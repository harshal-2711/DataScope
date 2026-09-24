import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app

client = TestClient(app)

def test_auth_endpoints():
    print("Testing backend auth endpoints...")
    # 1. Test registration
    reg_payload = {
        "email": "test_e2e_user@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "company_name": "E2E Testing Corp"
    }
    # Reset existing if any or register new
    res = client.post("/api/auth/register", json=reg_payload)
    if res.status_code == 400 and "already exists" in res.text:
        # User already exists, try login
        login_res = client.post("/api/auth/login", json={"email": reg_payload["email"], "password": reg_payload["password"]})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
    else:
        assert res.status_code == 201, f"Register failed: {res.text}"
        token = res.json()["access_token"]

    # 2. Test /api/auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200, f"Me endpoint failed: {me_res.text}"
    user_data = me_res.json()
    print("Logged in user:", user_data["user"]["email"])
    print("Assigned companies:", len(user_data["companies"]))
    assert user_data["user"]["email"] == "test_e2e_user@example.com"
    print("ALL BACKEND AUTH TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_auth_endpoints()
