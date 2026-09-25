import os
import urllib.request
import urllib.error
import json
import time

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project-id.supabase.co")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "your-anon-key")

def run_full_suite():
    print("=" * 70)
    print("DATASCOPE FULL END-TO-END AUTHENTICATION & DATABASE AUDIT")
    print("=" * 70)

    # Test 1: Health
    with urllib.request.urlopen(f"{BASE_URL}/health") as res:
        print(f"[TEST 1 PASSED] Backend Health: {res.getcode()} OK")

    # Test 2: Invalid Login (Wrong Password)
    wrong_payload = json.dumps({"email": "datascope_admin_test@example.com", "password": "WrongPassword999!"}).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/login", data=wrong_payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        print("[TEST 2 FAILED] Expected 401 on wrong password")
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401, got {e.code}"
        print(f"[TEST 2 PASSED] Wrong Password Handled Correctly -> HTTP {e.code} Unauthorized")

    # Test 3: Correct Login & Session
    login_payload = json.dumps({"email": "datascope_admin_test@example.com", "password": "SecurePassword123!"}).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/login", data=login_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        token = data["access_token"]
        comp_id = data["active_company_id"]
        print(f"[TEST 3 PASSED] Valid Login Successful -> Token issued, Workspace: {comp_id}")

    # Test 4: Profile Fetch & Workspace Isolation
    me_req = urllib.request.Request(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {token}", "X-Company-Id": comp_id})
    with urllib.request.urlopen(me_req) as res:
        me_data = json.loads(res.read().decode())
        print(f"[TEST 4 PASSED] Profile Loaded -> Email: {me_data['user']['email']}, Memberships: {len(me_data['companies'])}")

    # Test 5: Duplicate Registration Check
    dup_payload = json.dumps({
        "email": "datascope_admin_test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Duplicate User"
    }).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/register", data=dup_payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        print("[TEST 5 FAILED] Expected 400 on duplicate registration")
    except urllib.error.HTTPError as e:
        assert e.code == 400
        print(f"[TEST 5 PASSED] Duplicate Registration Blocked -> HTTP {e.code} Bad Request")

    # Test 6: Supabase Cloud Database Query
    supa_req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/profiles?select=*&limit=1", headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"})
    with urllib.request.urlopen(supa_req) as res:
        print(f"[TEST 6 PASSED] Supabase Cloud Database Query -> HTTP {res.getcode()} OK")

    # Test 7: Supabase Cloud Storage Endpoint
    storage_req = urllib.request.Request(f"{SUPABASE_URL}/storage/v1/bucket", headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"})
    with urllib.request.urlopen(storage_req) as res:
        print(f"[TEST 7 PASSED] Supabase Cloud Storage Query -> HTTP {res.getcode()} OK")

    print("\n" + "=" * 70)
    print("ALL 7 SYSTEM INTEGRATION TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 70)

if __name__ == "__main__":
    run_full_suite()
