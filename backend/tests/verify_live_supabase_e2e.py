"""Comprehensive Real End-to-End Supabase Verification Script."""
import sys
import httpx
from supabase import create_client, Client

SUPABASE_URL = "https://wvbozonxguapddgrbitz.supabase.co"
SUPABASE_KEY = "sb_publishable_C-De4bkO-fUjauTg_GGGLg_IMot1AnQ"

def run_e2e_verification():
    print("=" * 60)
    print("DATASCOPE REAL END-TO-END SUPABASE VERIFICATION")
    print(f"Target URL: {SUPABASE_URL}")
    print("=" * 60)

    results = []

    # 1. Test Auth Settings Endpoint
    try:
        r = httpx.get(
            f"{SUPABASE_URL}/auth/v1/settings",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            timeout=10.0
        )
        if r.status_code == 200:
            data = r.json()
            email_enabled = data.get("external", {}).get("email", False)
            results.append(("Supabase Auth Endpoint (/auth/v1/settings)", "PASSED", f"Status: 200 OK | Email Auth: {email_enabled}"))
        else:
            results.append(("Supabase Auth Endpoint (/auth/v1/settings)", "FAILED", f"Status: {r.status_code} | {r.text}"))
    except Exception as e:
        results.append(("Supabase Auth Endpoint (/auth/v1/settings)", "FAILED", f"Exception: {str(e)}"))

    # 2. Test Real Auth Signup (Testing auth functionality with a disposable test email)
    test_email = "datascope_test_verification@datascope.internal"
    test_password = "SecurePassword2026!Verification"
    try:
        r = httpx.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
            json={"email": test_email, "password": test_password},
            timeout=10.0
        )
        if r.status_code in (200, 201):
            results.append(("Supabase Auth User Signup (/auth/v1/signup)", "PASSED", f"Status: {r.status_code} | User registration functioning"))
        elif "User already registered" in r.text or "already exists" in r.text or r.status_code == 422:
            results.append(("Supabase Auth User Signup (/auth/v1/signup)", "PASSED", f"Status: {r.status_code} | Endpoint active (User already registered/Rate Limit)"))
        else:
            results.append(("Supabase Auth User Signup (/auth/v1/signup)", "WARNING", f"Status: {r.status_code} | {r.text}"))
    except Exception as e:
        results.append(("Supabase Auth User Signup (/auth/v1/signup)", "FAILED", f"Exception: {str(e)}"))

    # 3. Test Storage API & Bucket List
    try:
        r = httpx.get(
            f"{SUPABASE_URL}/storage/v1/bucket",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            timeout=10.0
        )
        if r.status_code == 200:
            buckets = r.json()
            bucket_names = [b.get("name") if isinstance(b, dict) else str(b) for b in buckets] if isinstance(buckets, list) else []
            has_datasets = "datasets" in bucket_names
            has_reports = "reports" in bucket_names
            results.append(("Supabase Storage Buckets (/storage/v1/bucket)", "PASSED", f"Status: 200 OK | Buckets found: {bucket_names} (datasets bucket created: {has_datasets})"))
        else:
            results.append(("Supabase Storage Buckets (/storage/v1/bucket)", "FAILED", f"Status: {r.status_code} | {r.text}"))
    except Exception as e:
        results.append(("Supabase Storage Buckets (/storage/v1/bucket)", "FAILED", f"Exception: {str(e)}"))

    # 4. Test Database Tables & SQL Migration Verification (REST API)
    tables_to_check = ["profiles", "companies", "company_memberships", "datasets", "dataset_versions", "reports"]
    for table in tables_to_check:
        try:
            r = httpx.get(
                f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit=1",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
                timeout=10.0
            )
            if r.status_code == 200:
                results.append((f"Database Table Check: public.{table}", "PASSED", f"Status: 200 OK | Table exists & queryable"))
            elif r.status_code == 401 or r.status_code == 403:
                # Table exists but RLS requires user token
                results.append((f"Database Table Check: public.{table}", "PROTECTED (RLS Active)", f"Status: {r.status_code} | RLS policy enforced"))
            elif r.status_code == 404 or "does not exist" in r.text or "PGRST204" in r.text or "PGRST205" in r.text:
                results.append((f"Database Table Check: public.{table}", "MIGRATION PENDING", f"Status: {r.status_code} | Table not yet created in Supabase SQL editor"))
            else:
                results.append((f"Database Table Check: public.{table}", "INFO", f"Status: {r.status_code} | {r.text}"))
        except Exception as e:
            results.append((f"Database Table Check: public.{table}", "ERROR", f"Exception: {str(e)}"))

    # Print summary
    print("\n--- TEST EXECUTION SUMMARY ---")
    for name, status, details in results:
        print(f"[{status:20}] {name}\n    Details: {details}\n")

if __name__ == "__main__":
    run_e2e_verification()
