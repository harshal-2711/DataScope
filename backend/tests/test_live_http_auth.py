import urllib.request
import urllib.error
import json

def test_live_auth():
    base_url = "http://127.0.0.1:8000/api"
    print("1. Testing /api/health...")
    with urllib.request.urlopen(f"{base_url}/health") as res:
        print(f"Health check: {res.getcode()} OK -> {res.read().decode()}")

    print("2. Testing /api/auth/register...")
    reg_data = json.dumps({
        "email": "datascope_admin_test@example.com",
        "password": "SecurePassword123!",
        "full_name": "DataScope Admin",
        "company_name": "DataScope Test Corp"
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/auth/register",
        data=reg_data,
        headers={"Content-Type": "application/json"}
    )
    token = None
    try:
        with urllib.request.urlopen(req) as res:
            resp_body = json.loads(res.read().decode())
            print(f"Register status: {res.getcode()} -> User: {resp_body['user']['email']}")
            token = resp_body["access_token"]
    except urllib.error.HTTPError as e:
        err_content = e.read().decode()
        if e.code == 400 and "already exists" in err_content:
            print("User already registered, attempting login...")
            login_data = json.dumps({
                "email": "datascope_admin_test@example.com",
                "password": "SecurePassword123!"
            }).encode("utf-8")
            l_req = urllib.request.Request(
                f"{base_url}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(l_req) as l_res:
                resp_body = json.loads(l_res.read().decode())
                print(f"Login status: {l_res.getcode()} -> User: {resp_body['user']['email']}")
                token = resp_body["access_token"]
        else:
            print(f"Register HTTP Error {e.code}: {err_content}")
            raise

    if token:
        print("3. Testing /api/auth/me with Bearer token...")
        me_req = urllib.request.Request(
            f"{base_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(me_req) as me_res:
            me_body = json.loads(me_res.read().decode())
            print(f"Auth /me Status: {me_res.getcode()} -> Email: {me_body['user']['email']}, Workspaces: {len(me_body['companies'])}")

    print("\n--- ALL BACKEND LIVE AUTH TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    test_live_auth()
