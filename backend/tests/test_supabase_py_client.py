try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project-id.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "your-anon-key")

def test_client():
    client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase Python client initialized successfully.")
    
    # Test auth methods
    try:
        settings = client.auth.get_session()
        print("Session check:", settings)
    except Exception as e:
        print("Auth session test:", e)

if __name__ == "__main__":
    test_client()
