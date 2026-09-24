try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

SUPABASE_URL = "https://wvbozonxguapddgrbitz.supabase.co"
SUPABASE_KEY = "sb_publishable_C-De4bkO-fUjauTg_GGGLg_IMot1AnQ"

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
