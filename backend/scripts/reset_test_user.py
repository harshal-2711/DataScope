"""Safe Test User Reset CLI for DataScope Development."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal, init_db, engine
from app.db.session import Base
from app.models.user import User
from app.models.company import Company
from app.models.membership import CompanyMembership
from app.models.dataset import Dataset
from app.models.audit_log import AuditLog

def reset_user(email: str):
    email_clean = email.lower().strip()
    if not email_clean:
        print("Error: Email is required.")
        return

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email_clean).first()
        if not user:
            print(f"Notice: User '{email_clean}' not found in local database.")
            return

        print(f"Found user '{user.email}' (ID: {user.id})")

        # 1. Find owned companies
        memberships = db.query(CompanyMembership).filter(CompanyMembership.user_id == user.id).all()
        for m in memberships:
            comp = db.query(Company).filter(Company.id == m.company_id).first()
            if comp and comp.owner_id == user.id:
                print(f"Deleting owned company: {comp.name} ({comp.id})")
                db.delete(comp)

        # 2. Delete user
        print(f"Deleting user: {user.email}")
        db.delete(user)

        db.commit()
        print(f"SUCCESS: Test user '{email_clean}' deleted from local database.")
    except Exception as e:
        db.rollback()
        print(f"Error during reset: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/reset_test_user.py <test_user_email>")
        sys.exit(1)
    reset_user(sys.argv[1])
