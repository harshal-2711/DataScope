import uuid
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.db.session import engine

test_uid = str(uuid.uuid4())
test_email = f"test_auth_{uuid.uuid4().hex[:6]}@datascope.test"

with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO auth.users (
            id, instance_id, aud, role, email, encrypted_password, 
            email_confirmed_at, raw_app_meta_data, raw_user_meta_data, 
            created_at, updated_at
        ) VALUES (
            :uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 
            :email, 'hashed_test_password', now(), '{"provider":"email","providers":["email"]}', 
            json_build_object('full_name', 'Test User Auth'), now(), now()
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"uid": test_uid, "email": test_email})
    conn.commit()

    u_row = conn.execute(text("SELECT id, email FROM auth.users WHERE id = :uid"), {"uid": test_uid}).fetchone()
    p_row = conn.execute(text("SELECT id, email, full_name FROM public.profiles WHERE id = :uid"), {"uid": test_uid}).fetchone()
    print("Inserted auth.users row   :", u_row)
    print("Auto-created profile row  :", p_row)
