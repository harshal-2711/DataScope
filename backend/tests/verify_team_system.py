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
from app.core.security import create_access_token, hash_password, verify_password

client = TestClient(app)

def test_full_system():
    db = SessionLocal()
    try:
        print("=== 1. Checking Real Production Account ===")
        owner_user = db.query(User).filter(User.email == "om2711sharma@gmail.com").first()
        assert owner_user is not None, "Owner user om2711sharma@gmail.com must exist!"
        print(f"Owner verified: {owner_user.email} (id: {owner_user.id})")
        
        owner_membership = db.query(CompanyMembership).filter(
            CompanyMembership.user_id == owner_user.id,
            CompanyMembership.role == "owner"
        ).first()
        assert owner_membership is not None, "Owner membership must exist!"
        company_id = str(owner_membership.company_id)
        print(f"Owner company verified: {company_id}")

        owner_token = create_access_token({"sub": owner_user.id})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        print("\n=== 2. Owner Inviting Test Worker ===")
        test_worker_email = f"test_worker_{uuid.uuid4().hex[:8]}@example.com"
        invite_resp = client.post(
            f"/api/companies/{company_id}/invitations",
            headers=owner_headers,
            json={"email": test_worker_email, "role": "analyst"}
        )
        print(f"Invite Response Status: {invite_resp.status_code}")
        assert invite_resp.status_code in (200, 201), f"Expected 200/201, got {invite_resp.text}"
        invite_data = invite_resp.json()
        token = invite_data.get("invitation_token")
        assert token, "Invitation token must be returned"
        print(f"Invitation created successfully! Token generated: {token[:8]}...")

        print("\n=== 3. Worker Validates Invitation Token ===")
        validate_resp = client.get(f"/api/auth/invitations/{token}")
        assert validate_resp.status_code == 200, f"Validation failed: {validate_resp.text}"
        val_data = validate_resp.json()
        assert val_data["email"] == test_worker_email
        assert val_data["role"] == "analyst"
        assert val_data["valid"] is True
        print(f"Token validated successfully for {val_data['email']} with role {val_data['role']}")

        print("\n=== 4. Worker Sets Own Password and Accepts Invitation ===")
        worker_password = "WorkerSecurePassword!2026"
        accept_resp = client.post(
            "/api/auth/invitations/accept",
            json={
                "token": token,
                "full_name": "Test Analyst Worker",
                "password": worker_password
            }
        )
        assert accept_resp.status_code == 200, f"Accept failed: {accept_resp.text}"
        accept_data = accept_resp.json()
        worker_access_token = accept_data["access_token"]
        worker_user_id = accept_data["user"]["id"]
        print(f"Worker account created and activated! Worker user ID: {worker_user_id}")

        print("\n=== 5. Worker Logs In With Own Password ===")
        login_resp = client.post(
            "/api/auth/login",
            json={"email": test_worker_email, "password": worker_password}
        )
        assert login_resp.status_code == 200, f"Worker login failed: {login_resp.text}"
        worker_login_data = login_resp.json()
        assert worker_login_data["active_company_id"] == company_id
        worker_headers = {"Authorization": f"Bearer {worker_login_data['access_token']}"}
        print(f"Worker login verified! Correct company resolved server-side: {worker_login_data['active_company_id']}")

        print("\n=== 6. Worker Access Control & Role Enforcement ===")
        # Worker cannot update workspace settings (Owner/Admin only)
        settings_attempt = client.put(
            f"/api/companies/{company_id}/settings",
            headers=worker_headers,
            json={"name": "Hacked Company Name"}
        )
        print(f"Worker settings update status: {settings_attempt.status_code} (Expected: 403)")
        assert settings_attempt.status_code == 403, f"Expected 403, got {settings_attempt.status_code}"

        # Worker cannot invite other members
        invite_attempt = client.post(
            f"/api/companies/{company_id}/invitations",
            headers=worker_headers,
            json={"email": "another@example.com", "role": "analyst"}
        )
        print(f"Worker invite attempt status: {invite_attempt.status_code} (Expected: 403)")
        assert invite_attempt.status_code == 403, f"Expected 403, got {invite_attempt.status_code}"

        # Cross-company IDOR prevention
        fake_company_id = str(uuid.uuid4())
        idor_attempt = client.get(
            f"/api/companies/{fake_company_id}/members",
            headers=worker_headers
        )
        print(f"Cross-company IDOR attempt status: {idor_attempt.status_code} (Expected: 403)")
        assert idor_attempt.status_code == 403, f"Expected 403, got {idor_attempt.status_code}"

        print("\n=== 7. Owner Member Management & Cleanup ===")
        # Owner fetches members list
        members_resp = client.get(f"/api/companies/{company_id}/members", headers=owner_headers)
        assert members_resp.status_code == 200
        members_list = members_resp.json()
        worker_membership = next((m for m in members_list if m.get("user_email") == test_worker_email), None)
        assert worker_membership is not None, "Worker should be present in members list"
        print(f"Worker found in members list with role: {worker_membership['role']}")

        # Owner removes worker
        remove_resp = client.delete(
            f"/api/companies/{company_id}/members/{worker_membership['membership_id']}",
            headers=owner_headers
        )
        assert remove_resp.status_code == 200, f"Remove failed: {remove_resp.text}"
        print("Worker removed by Owner successfully")

        # Clean up test worker user and invitation from DB
        db.query(Invitation).filter(Invitation.email == test_worker_email).delete()
        db.query(User).filter(User.id == worker_user_id).delete()
        try:
            from sqlalchemy import text
            db.execute(text("DELETE FROM auth.users WHERE id = :uid"), {"uid": worker_user_id})
        except Exception:
            pass
        db.commit()
        print("Test worker records cleaned up from DB cleanly.")

        print("\nALL VERIFICATION CHECKS PASSED PERFECTLY!")

    finally:
        db.close()

if __name__ == "__main__":
    test_full_system()
