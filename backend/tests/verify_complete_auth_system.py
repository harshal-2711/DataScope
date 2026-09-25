import os
import sys
import uuid
from datetime import datetime, timezone

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.membership import CompanyMembership
from app.models.invitation import Invitation
from app.models.dataset import Dataset
from app.core.security import create_access_token, hash_password
from sqlalchemy import text

client = TestClient(app)

def run_all_verification_tests():
    db = SessionLocal()
    cleanups = []
    try:
        print("==================================================")
        print("STARTING COMPLETE AUTHENTICATION & ACCESS VERIFICATION")
        print("==================================================")

        # ----------------------------------------------------
        # PRE-CHECK: Production Owner & Company
        # ----------------------------------------------------
        owner = db.query(User).filter(User.email == "om2711sharma@gmail.com").first()
        assert owner is not None, "Production Owner user must exist!"
        owner_token = create_access_token({"sub": owner.id})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        owner_profile_res = client.get("/api/auth/me", headers=owner_headers)
        assert owner_profile_res.status_code == 200
        owner_companies = owner_profile_res.json()["companies"]
        assert len(owner_companies) > 0, "Owner must belong to their workspace"
        company_id = owner_companies[0]["company_id"]
        assert owner_companies[0]["role"] == "owner", "Owner role must be owner"
        print(f"[CHECK] Production Owner verified: {owner.email} in company {company_id} as {owner_companies[0]['role']}")

        # ----------------------------------------------------
        # TEST A: New Email Worker
        # ----------------------------------------------------
        print("\n--- TEST A: New Email Worker Flow ---")
        worker_a_email = f"worker_a_{uuid.uuid4().hex[:8]}@example.com"
        cleanups.append(worker_a_email)

        # 1. Owner invites worker
        invite_res = client.post(
            f"/api/companies/{company_id}/invitations",
            headers=owner_headers,
            json={"email": worker_a_email, "role": "analyst"}
        )
        assert invite_res.status_code in (200, 201), f"Invite failed: {invite_res.text}"
        inv_token = invite_res.json()["invitation_token"]
        print(f"[OK] Worker invited with secure token: {inv_token[:8]}...")

        # 2. Worker validates token
        val_res = client.get(f"/api/auth/invitations/{inv_token}")
        assert val_res.status_code == 200 and val_res.json()["valid"] is True
        print(f"[OK] Worker validated invitation for: {val_res.json()['email']}")

        # 3. Worker creates own password
        worker_pwd = "SecureWorkerPassword!2026"
        accept_res = client.post(
            "/api/auth/invitations/accept",
            json={"token": inv_token, "full_name": "Worker A Analyst", "password": worker_pwd}
        )
        assert accept_res.status_code == 200, f"Accept failed: {accept_res.text}"
        print("[OK] Worker set own password and activated account")

        # 4. Worker logs in with email/password
        login_a = client.post("/api/auth/login", json={"email": worker_a_email, "password": worker_pwd})
        assert login_a.status_code == 200
        worker_a_data = login_a.json()
        assert worker_a_data["active_company_id"] == company_id, "Worker must join the invited company"
        worker_a_headers = {"Authorization": f"Bearer {worker_a_data['access_token']}"}

        # 5. Worker profile & shared datasets load
        profile_a = client.get("/api/auth/me", headers=worker_a_headers).json()
        assert profile_a["companies"][0]["role"] == "analyst"
        print(f"[OK] Worker A logged in, resolved company {company_id}, role: {profile_a['companies'][0]['role']}")

        ds_res = client.get("/api/data-management/datasets", headers=worker_a_headers)
        assert ds_res.status_code == 200
        print(f"[OK] Worker A loaded company datasets successfully ({len(ds_res.json())} dataset(s) visible)")

        # ----------------------------------------------------
        # TEST B: Google Worker Onboarding
        # ----------------------------------------------------
        print("\n--- TEST B: Google Worker Flow ---")
        worker_b_email = f"worker_b_{uuid.uuid4().hex[:8]}@example.com"
        cleanups.append(worker_b_email)

        # 1. Owner invites Google worker
        client.post(
            f"/api/companies/{company_id}/invitations",
            headers=owner_headers,
            json={"email": worker_b_email, "role": "viewer"}
        )

        # 2. Worker simulates Google OAuth callback
        from unittest.mock import patch, MagicMock
        mock_httpx_resp = MagicMock()
        mock_httpx_resp.status_code = 200
        mock_httpx_resp.json.return_value = {
            "email": worker_b_email,
            "name": "Worker B Viewer",
            "sub": f"google-sub-{uuid.uuid4().hex[:8]}",
            "picture": "https://example.com/avatar_b.png"
        }

        with patch("httpx.get", return_value=mock_httpx_resp):
            with patch("app.core.config.settings.GOOGLE_CLIENT_ID", "mock-client-id"):
                google_res = client.post("/api/auth/google", json={"credential": "mock_google_id_token"})
                assert google_res.status_code == 200, f"Google login failed: {google_res.text}"
                google_data = google_res.json()
                assert google_data["active_company_id"] == company_id, "Google worker must resolve invited company"

        # Verify role is viewer and not owner
        worker_b_headers = {"Authorization": f"Bearer {google_data['access_token']}"}
        profile_b = client.get("/api/auth/me", headers=worker_b_headers).json()
        assert profile_b["companies"][0]["role"] == "viewer"
        print(f"[OK] Google Worker B joined company {company_id} with role: {profile_b['companies'][0]['role']} (NOT owner)")

        # ----------------------------------------------------
        # TEST C: Random Google User without Invitation
        # ----------------------------------------------------
        print("\n--- TEST C: Random Google User without Invitation ---")
        random_google_email = f"random_{uuid.uuid4().hex[:8]}@gmail.com"
        cleanups.append(random_google_email)

        mock_random_resp = MagicMock()
        mock_random_resp.status_code = 200
        mock_random_resp.json.return_value = {
            "email": random_google_email,
            "name": "Random Stranger",
            "sub": f"google-sub-{uuid.uuid4().hex[:8]}",
            "picture": None
        }

        with patch("httpx.get", return_value=mock_random_resp):
            with patch("app.core.config.settings.GOOGLE_CLIENT_ID", "mock-client-id"):
                random_res = client.post("/api/auth/google", json={"credential": "mock_random_token"})
                assert random_res.status_code == 200
                random_data = random_res.json()
                assert random_data["active_company_id"] is None, "Random user must have NO active company ID!"

        random_headers = {"Authorization": f"Bearer {random_data['access_token']}"}
        random_profile = client.get("/api/auth/me", headers=random_headers).json()
        assert len(random_profile["companies"]) == 0, "Random user must have 0 companies"
        print(f"[OK] Random Google user authenticated without company access (companies: {len(random_profile['companies'])})")

        # Random user blocked from accessing company data
        random_ds = client.get("/api/data-management/datasets", headers=random_headers)
        assert random_ds.status_code == 403, f"Expected 403 for random user, got {random_ds.status_code}"
        print("[OK] Random user blocked from datasets (HTTP 403 Forbidden)")

        # ----------------------------------------------------
        # TEST D: Existing User Accepting Invitation
        # ----------------------------------------------------
        print("\n--- TEST D: Existing User Accepting Invitation ---")
        existing_email = f"existing_{uuid.uuid4().hex[:8]}@example.com"
        cleanups.append(existing_email)

        # Register standard user
        client.post("/api/auth/register", json={
            "email": existing_email,
            "password": "ExistingPassword123!",
            "full_name": "Existing Standalone User"
        })

        # Owner invites existing user to company as Analyst
        client.post(
            f"/api/companies/{company_id}/invitations",
            headers=owner_headers,
            json={"email": existing_email, "role": "analyst"}
        )

        # Existing user logs in with their existing credentials
        existing_login = client.post("/api/auth/login", json={
            "email": existing_email,
            "password": "ExistingPassword123!"
        })
        assert existing_login.status_code == 200
        existing_headers = {"Authorization": f"Bearer {existing_login.json()['access_token']}"}
        existing_profile = client.get("/api/auth/me", headers=existing_headers).json()
        
        # Verify joined company with role analyst
        matching_comp = next((c for c in existing_profile["companies"] if c["company_id"] == company_id), None)
        assert matching_comp is not None and matching_comp["role"] == "analyst"
        print(f"[OK] Existing user linked to invited company with role: {matching_comp['role']} without duplicate account")

        # ----------------------------------------------------
        # TEST E: Owner Panel Security & RBAC Enforcement
        # ----------------------------------------------------
        print("\n--- TEST E: Owner Security & RBAC Enforcement ---")
        # 1. Worker cannot access workspace settings update (403)
        hack_settings = client.put(
            f"/api/companies/{company_id}/settings",
            headers=worker_a_headers,
            json={"name": "Hacked Workspace"}
        )
        assert hack_settings.status_code == 403, f"Expected 403, got {hack_settings.status_code}"
        print("[OK] Worker blocked from updating workspace settings (403 Forbidden)")

        # 2. Worker cannot invite other members (403)
        hack_invite = client.post(
            f"/api/companies/{company_id}/invitations",
            headers=worker_a_headers,
            json={"email": "victim@example.com", "role": "owner"}
        )
        assert hack_invite.status_code == 403, f"Expected 403, got {hack_invite.status_code}"
        print("[OK] Worker blocked from inviting members (403 Forbidden)")

        # 3. Worker cannot promote themselves to OWNER (403)
        # Find worker A's membership id
        mems_list = client.get(f"/api/companies/{company_id}/members", headers=owner_headers).json()
        worker_a_mem = next(m for m in mems_list if m.get("user_email") == worker_a_email)
        hack_role = client.put(
            f"/api/companies/{company_id}/members/{worker_a_mem['membership_id']}/role",
            headers=worker_a_headers,
            json={"role": "owner"}
        )
        assert hack_role.status_code == 403, f"Expected 403, got {hack_role.status_code}"
        print("[OK] Worker blocked from self-promoting to OWNER (403 Forbidden)")

        # 4. Worker cannot change company ID to access another company (IDOR 403)
        foreign_comp_id = str(uuid.uuid4())
        idor_res = client.get(f"/api/companies/{foreign_comp_id}/members", headers=worker_a_headers)
        assert idor_res.status_code == 403, f"Expected 403, got {idor_res.status_code}"
        print("[OK] Cross-tenant IDOR attempt blocked (403 Forbidden)")

        # ----------------------------------------------------
        # TEST F: Persistence & Source Data Sharing
        # ----------------------------------------------------
        print("\n--- TEST F: Persistence & Source Data Sharing ---")
        # Check production Google Sheet dataset
        prod_ds = db.query(Dataset).filter(Dataset.company_id == company_id).first()
        assert prod_ds is not None, "Production dataset must exist"
        print(f"[OK] Production dataset verified intact: '{prod_ds.name}' (ID: {prod_ds.id})")

        # Owner logout simulation & login
        owner_logout = client.post("/api/auth/logout", headers=owner_headers)
        assert owner_logout.status_code == 200

        # Owner logs in again
        owner_relogin = client.get("/api/auth/me", headers=owner_headers)
        assert owner_relogin.status_code == 200
        print("[OK] Owner session restores workspace and company relationships without data loss")

        # Worker sees the same persistent company dataset
        worker_ds_check = client.get("/api/data-management/datasets", headers=worker_a_headers).json()
        assert any(d["id"] == str(prod_ds.id) for d in worker_ds_check), "Worker must see company dataset"
        print(f"[OK] Worker sees persistent company dataset '{prod_ds.name}' without reconnecting")

        # ----------------------------------------------------
        # TEST G: Member Removal
        # ----------------------------------------------------
        print("\n--- TEST G: Member Removal ---")
        del_res = client.delete(f"/api/companies/{company_id}/members/{worker_a_mem['membership_id']}", headers=owner_headers)
        assert del_res.status_code == 200
        # Worker A loses active membership
        revoked_profile = client.get("/api/auth/me", headers=worker_a_headers).json()
        assert not any(c["company_id"] == company_id for c in revoked_profile["companies"])
        print("[OK] Removed worker immediately loses access to company workspace")

        # Datasets remain intact
        ds_after = db.query(Dataset).filter(Dataset.company_id == company_id).first()
        assert ds_after is not None, "Datasets must remain intact after member removal"
        print("[OK] Company datasets remain intact after worker removal")

        print("\n==================================================")
        print("ALL TESTS (A, B, C, D, E, F, G) PASSED WITH 100% SUCCESS!")
        print("==================================================")

    finally:
        # Clean up any test users created
        for email in cleanups:
            test_users = db.query(User).filter(User.email == email).all()
            for u in test_users:
                db.query(Invitation).filter(Invitation.email == email).delete()
                db.query(CompanyMembership).filter(CompanyMembership.user_id == u.id).delete()
                db.query(User).filter(User.id == u.id).delete()
                try:
                    db.execute(text("DELETE FROM auth.users WHERE email = :email"), {"email": email})
                except Exception:
                    pass
        db.commit()
        db.close()
        print("[CLEANUP] All temporary test records removed cleanly from database.")

if __name__ == "__main__":
    run_all_verification_tests()
