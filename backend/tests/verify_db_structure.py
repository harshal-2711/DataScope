import os
import sys

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

from app.db.session import engine
from sqlalchemy import text

def verify_production_db():
    print("=== Direct Production Database Structure Verification ===")
    with engine.connect() as conn:
        # 1. Company exists
        comp = conn.execute(text("SELECT id, name, owner_id FROM public.companies WHERE name = 'Harshal ojha''s Workspace'")).first()
        assert comp is not None, "Production company must exist!"
        company_id, company_name, owner_id = comp[0], comp[1], comp[2]
        print(f"[OK] Company exists: '{company_name}' (ID: {company_id})")

        # 2. Owner exists
        owner_user = conn.execute(text("SELECT id, email, full_name FROM public.users WHERE email = 'om2711sharma@gmail.com'")).first()
        assert owner_user is not None, "Owner user must exist!"
        assert str(owner_id) == str(owner_user[0]), f"Company owner_id ({owner_id}) must match owner user ID ({owner_user[0]})"
        print(f"[OK] Owner user exists: '{owner_user[2]}' ({owner_user[1]}) with matching owner_id relationship")

        # 3. Owner has OWNER membership
        owner_mem = conn.execute(text("""
            SELECT id, role, status 
            FROM public.company_memberships 
            WHERE company_id = :cid AND user_id = :uid
        """), {"cid": company_id, "uid": owner_id}).first()
        assert owner_mem is not None, "Owner membership record must exist!"
        assert owner_mem[1] == "owner", f"Owner membership role must be 'owner', got {owner_mem[1]}"
        assert owner_mem[2] == "active", f"Owner membership status must be 'active', got {owner_mem[2]}"
        print(f"[OK] Owner membership verified: Role={owner_mem[1]}, Status={owner_mem[2]}")

        # 4. Check memberships & roles via canonical view
        overview_rows = conn.execute(text("""
            SELECT "Company", "User", "Email", "Role", "Status", is_owner
            FROM public.company_members_overview
            WHERE company_id = :cid
            ORDER BY CASE WHEN "Role" = 'OWNER' THEN 1 ELSE 2 END, "User"
        """), {"cid": company_id}).fetchall()
        assert len(overview_rows) >= 1, "At least Owner must be listed in company_members_overview"
        print(f"[OK] Canonical view company_members_overview returns {len(overview_rows)} member(s):")
        for r in overview_rows:
            print(f"     * {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} (is_owner={r[5]})")

        # 5. Existing datasets remain associated with the company
        datasets = conn.execute(text("""
            SELECT id, name, company_id 
            FROM public.datasets 
            WHERE company_id = :cid
        """), {"cid": company_id}).fetchall()
        assert len(datasets) > 0, "Production datasets must remain associated with the company!"
        for ds in datasets:
            print(f"[OK] Production dataset intact: '{ds[1]}' (ID: {ds[0]}) -> Company: {ds[2]}")

        # 6. Check role constraint
        valid_roles = ["owner", "admin", "analyst", "viewer"]
        mems = conn.execute(text("SELECT DISTINCT role FROM public.company_memberships WHERE company_id = :cid"), {"cid": company_id}).fetchall()
        for m in mems:
            assert m[0] in valid_roles, f"Role {m[0]} not in valid roles {valid_roles}"
        print(f"[OK] All stored membership roles are strictly valid: {[m[0] for m in mems]}")

    print("\nALL PRODUCTION DATABASE CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    verify_production_db()
