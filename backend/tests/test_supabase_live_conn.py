import os
import httpx
import json

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project-id.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "your-anon-key")

def test_supabase():
    print(f"Testing Supabase connection to: {SUPABASE_URL}")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    # 1. Test Auth API
    try:
        r = httpx.get(f"{SUPABASE_URL}/auth/v1/settings", headers=headers, timeout=10.0)
        print(f"Auth /settings status: {r.status_code}")
        if r.status_code == 200:
            print("Auth endpoint response:", r.json())
        else:
            print("Auth response text:", r.text)
    except Exception as e:
        print(f"Auth test error: {e}")

    # 2. Test REST API root
    try:
        r = httpx.get(f"{SUPABASE_URL}/rest/v1/", headers=headers, timeout=10.0)
        print(f"REST / status: {r.status_code}")
        if r.status_code == 200:
            print("OpenAPI schema detected on REST endpoint.")
    except Exception as e:
        print(f"REST test error: {e}")

    # 3. Test Storage buckets
    try:
        r = httpx.get(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers, timeout=10.0)
        print(f"Storage /bucket status: {r.status_code}")
        print("Storage response:", r.text)
    except Exception as e:
        print(f"Storage test error: {e}")

if __name__ == "__main__":
    test_supabase()
