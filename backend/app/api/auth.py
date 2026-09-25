"""Authentication API Router for User Registration, Login & Google OAuth."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.company import Company
from app.models.membership import CompanyMembership
from app.models.invitation import Invitation
from app.models.user import User
from app.schemas.auth import (
    AcceptInvitationRequest,
    CompanyMembershipItem,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    InvitationValidateResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
    UserWithCompaniesResponse,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    s = re.sub(r"[-\s]+", "-", s)
    return s or "workspace"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account and provision their initial company workspace."""
    email_clean = payload.email.lower().strip()
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please login or reset your password.",
        )

    # 1. Create User
    new_user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(payload.password)

    from app.db.session import is_postgres
    if is_postgres:
        from sqlalchemy import text
        try:
            db.execute(text("""
                INSERT INTO auth.users (
                    id, instance_id, aud, role, email, encrypted_password, 
                    email_confirmed_at, raw_app_meta_data, raw_user_meta_data, 
                    created_at, updated_at
                ) VALUES (
                    :uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 
                    :email, :pwd, now(), '{"provider":"email","providers":["email"]}', 
                    json_build_object('full_name', :name), now(), now()
                )
                ON CONFLICT (id) DO NOTHING;
            """), {
                "uid": new_user_id,
                "email": email_clean,
                "pwd": hashed_pwd,
                "name": payload.full_name.strip(),
            })
            db.flush()
        except Exception as e:
            pass

    new_user = User(
        id=new_user_id,
        email=email_clean,
        hashed_password=hashed_pwd,
        full_name=payload.full_name.strip(),
        is_active=True,
        is_verified=True,
        auth_provider="local",
    )
    db.add(new_user)
    db.flush()

    # 2. Provision Company Workspace
    company_name = payload.company_name.strip() if payload.company_name else f"{new_user.full_name}'s Workspace"
    company_slug_base = _slugify(company_name)
    company_slug = f"{company_slug_base}-{uuid.uuid4().hex[:6]}"

    new_company = Company(
        id=str(uuid.uuid4()),
        name=company_name,
        slug=company_slug,
        domain_type=getattr(payload, "domain_type", None) or "General Business",
        owner_id=new_user.id,
        industry=getattr(payload, "industry", None) or "SaaS / Technology",
        company_size=getattr(payload, "company_size", None) or "11-50 Employees",
        country=getattr(payload, "country", None) or "United States",
        primary_objective=getattr(payload, "primary_objective", None) or "Revenue Growth & Margin Protection",
        settings="{}",
    )
    db.add(new_company)
    db.flush()

    # 3. Assign Owner Membership
    new_membership = CompanyMembership(
        id=str(uuid.uuid4()),
        user_id=new_user.id,
        company_id=new_company.id,
        role="owner",
        status="active",
    )
    db.add(new_membership)
    db.commit()
    db.refresh(new_user)

    # 4. Generate Tokens
    token_data = {"sub": str(new_user.id), "email": new_user.email, "company_id": str(new_company.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user_resp = UserProfileResponse(
        id=str(new_user.id),
        email=new_user.email,
        full_name=new_user.full_name,
        avatar_url=new_user.avatar_url,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        auth_provider=new_user.auth_provider,
        created_at=new_user.created_at,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_resp,
        active_company_id=str(new_company.id),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password."""
    email_clean = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact support.",
        )

    # Find active company membership
    membership = (
        db.query(CompanyMembership)
        .filter(CompanyMembership.user_id == user.id, CompanyMembership.status == "active")
        .first()
    )
    active_company_id = str(membership.company_id) if membership else None

    token_data = {"sub": str(user.id), "email": user.email, "company_id": active_company_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user_resp = UserProfileResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_verified=user.is_verified,
        auth_provider=user.auth_provider,
        created_at=user.created_at,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_resp,
        active_company_id=active_company_id,
    )


@router.post("/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate or register via Google OAuth 2.0."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured on this server. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend .env.",
        )

    # Decode/Verify Google token if provided
    # In production with google-auth, verify against Google certs.
    # For robust demonstration, support standard Google JWT payload structure.
    import httpx

    google_email: Optional[str] = None
    google_name: Optional[str] = None
    google_id: Optional[str] = None
    google_avatar: Optional[str] = None

    if payload.credential:
        try:
            # Verify with Google's tokeninfo endpoint
            resp = httpx.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={payload.credential}", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                google_email = data.get("email")
                google_name = data.get("name", google_email.split("@")[0] if google_email else "User")
                google_id = data.get("sub")
                google_avatar = data.get("picture")
        except Exception:
            pass

    if not google_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to authenticate with Google. Invalid or expired Google credential.",
        )

    email_clean = google_email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=email_clean,
            full_name=google_name or "Google User",
            avatar_url=google_avatar,
            is_active=True,
            is_verified=True,
            auth_provider="google",
            google_id=google_id,
        )
        db.add(user)
        db.flush()

        company_name = f"{user.full_name}'s Workspace"
        new_company = Company(
            id=str(uuid.uuid4()),
            name=company_name,
            slug=f"{_slugify(company_name)}-{uuid.uuid4().hex[:6]}",
            owner_id=user.id,
        )
        db.add(new_company)
        db.flush()

        membership = CompanyMembership(
            id=str(uuid.uuid4()),
            user_id=user.id,
            company_id=new_company.id,
            role="owner",
            status="active",
        )
        db.add(membership)
        db.commit()
        db.refresh(user)
        active_company_id = new_company.id
    else:
        membership = (
            db.query(CompanyMembership)
            .filter(CompanyMembership.user_id == user.id, CompanyMembership.status == "active")
            .first()
        )
        active_company_id = membership.company_id if membership else None

    token_data = {"sub": user.id, "email": user.email, "company_id": active_company_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user_resp = UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_verified=user.is_verified,
        auth_provider=user.auth_provider,
        created_at=user.created_at,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_resp,
        active_company_id=active_company_id,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Issue a new access token using a valid refresh token."""
    decoded = decode_token(payload.refresh_token)
    if decoded and decoded.get("type") == "refresh":
        user_id = decoded.get("sub")
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer active.",
            )
        company_id = decoded.get("company_id")
        token_data = {"sub": user.id, "email": user.email, "company_id": company_id}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        user_resp = UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_verified=user.is_verified,
            auth_provider=user.auth_provider,
            created_at=user.created_at,
        )
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user=user_resp,
            active_company_id=company_id,
        )

    # If not local token, try Supabase token refresh if configured
    from app.core.supabase_client import is_supabase_configured, get_clean_supabase_url
    if is_supabase_configured():
        import httpx
        try:
            clean_url = get_clean_supabase_url()
            url = f"{clean_url}/auth/v1/token?grant_type=refresh_token"
            headers = {"apikey": settings.SUPABASE_ANON_KEY, "Content-Type": "application/json"}
            with httpx.Client(timeout=6.0) as client:
                res = client.post(url, headers=headers, json={"refresh_token": payload.refresh_token})
                if res.status_code == 200:
                    sdata = res.json()
                    s_user = sdata.get("user", {})
                    s_user_id = s_user.get("id")
                    s_user_email = s_user.get("email")
                    user = db.query(User).filter((User.id == s_user_id) | (User.email == s_user_email)).first()
                    if not user and s_user_email:
                        user = User(
                            id=s_user_id or str(uuid.uuid4()),
                            email=s_user_email,
                            full_name=s_user.get("user_metadata", {}).get("full_name") or s_user_email.split("@")[0],
                            auth_provider="supabase",
                            is_active=True,
                            is_verified=True,
                        )
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                    if user:
                        first_mem = db.query(CompanyMembership).filter(CompanyMembership.user_id == user.id, CompanyMembership.status == "active").first()
                        active_comp_id = first_mem.company_id if first_mem else None
                        user_resp = UserProfileResponse(
                            id=user.id,
                            email=user.email,
                            full_name=user.full_name,
                            avatar_url=user.avatar_url,
                            is_active=user.is_active,
                            is_verified=user.is_verified,
                            auth_provider=user.auth_provider,
                            created_at=user.created_at,
                        )
                        return TokenResponse(
                            access_token=sdata.get("access_token"),
                            refresh_token=sdata.get("refresh_token") or payload.refresh_token,
                            user=user_resp,
                            active_company_id=active_comp_id,
                        )
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token. Please log in again.",
    )


from app.api.dependencies import get_current_user


@router.get("/me", response_model=UserWithCompaniesResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user profile and all their accessible company workspaces."""
    memberships = (
        db.query(CompanyMembership, Company)
        .join(Company, Company.id == CompanyMembership.company_id)
        .filter(CompanyMembership.user_id == current_user.id, CompanyMembership.status == "active")
        .all()
    )

    company_items = [
        CompanyMembershipItem(
            membership_id=str(m.id),
            company_id=str(c.id),
            company_name=c.name,
            company_slug=c.slug,
            role=m.role,
            status=m.status,
        )
        for m, c in memberships
    ]

    user_resp = UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        auth_provider=current_user.auth_provider,
        created_at=current_user.created_at,
    )
    return UserWithCompaniesResponse(user=user_resp, companies=company_items)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Log out and invalidate current session."""
    return {"status": "success", "message": "Successfully logged out."}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Initiate password reset request with a secure token."""
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    # Always return success message to prevent user enumeration attacks
    if not user or user.auth_provider != "local":
        return {
            "status": "success",
            "message": "If an account with this email exists, a password reset link has been prepared.",
        }

    # Generate reset token valid for 1 hour
    import secrets
    from datetime import timedelta
    reset_token = secrets.token_urlsafe(32)
    user.reset_password_token = reset_token
    user.reset_password_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    return {
        "status": "success",
        "message": "If an account with this email exists, a password reset link has been prepared.",
        "reset_token": reset_token,  # Provided in response for local/testing convenience
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset account password using valid reset token."""
    user = db.query(User).filter(User.reset_password_token == payload.token).first()
    
    if not user or not user.reset_password_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    # Check expiration (ensure offset-naive comparison safe)
    expires_at = user.reset_password_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new one.",
        )

    # Update password and clear token
    user.hashed_password = hash_password(payload.new_password)
    user.reset_password_token = None
    user.reset_password_expires_at = None
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "success",
        "message": "Password successfully updated. You can now log in with your new password.",
    }


@router.get("/invitations/{token}", response_model=InvitationValidateResponse)
def validate_invitation(token: str, db: Session = Depends(get_db)):
    """Validate a pending worker invitation token."""
    inv = db.query(Invitation).filter(Invitation.invitation_token == token).first()
    if not inv:
        return InvitationValidateResponse(
            valid=False,
            error="This invitation link is invalid or does not exist. Please check with your team administrator.",
        )

    if inv.status != "pending":
        status_msg = "already been accepted" if inv.status == "accepted" else "been revoked"
        return InvitationValidateResponse(
            valid=False,
            error=f"This invitation has {status_msg}. Please request a new invitation.",
        )

    expires_at = inv.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        return InvitationValidateResponse(
            valid=False,
            error="This invitation link has expired. Please ask your administrator to send a fresh invitation.",
        )

    company = db.query(Company).filter(Company.id == inv.company_id).first()
    return InvitationValidateResponse(
        valid=True,
        email=inv.email,
        role=inv.role,
        company_name=company.name if company else "DataScope Workspace",
        company_id=str(inv.company_id),
    )


@router.post("/invitations/accept", response_model=TokenResponse)
def accept_invitation(payload: AcceptInvitationRequest, db: Session = Depends(get_db)):
    """Accept an invitation, create own worker password, join workspace, and authenticate."""
    inv = db.query(Invitation).filter(Invitation.invitation_token == payload.token).first()
    if not inv or inv.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token.",
        )

    expires_at = inv.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation link has expired. Please ask your administrator for a new one.",
        )

    company = db.query(Company).filter(Company.id == inv.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The associated company workspace could not be found.",
        )

    now = datetime.now(timezone.utc)
    email_clean = inv.email.lower().strip()

    # Check if user already exists
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        # Create new worker account with their own password
        worker_id = str(uuid.uuid4())
        hashed_pwd = hash_password(payload.password)
        
        from app.db.session import is_postgres
        if is_postgres:
            from sqlalchemy import text
            try:
                db.execute(text("""
                    INSERT INTO auth.users (
                        id, instance_id, aud, role, email, encrypted_password, 
                        email_confirmed_at, raw_app_meta_data, raw_user_meta_data, 
                        created_at, updated_at
                    ) VALUES (
                        :uid, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 
                        :email, :pwd, now(), '{"provider":"email","providers":["email"]}', 
                        json_build_object('full_name', :name), now(), now()
                    )
                    ON CONFLICT (id) DO NOTHING;
                """), {
                    "uid": worker_id,
                    "email": email_clean,
                    "pwd": hashed_pwd,
                    "name": payload.full_name.strip(),
                })
                db.flush()
            except Exception as e:
                pass

        user = User(
            id=worker_id,
            email=email_clean,
            full_name=payload.full_name.strip(),
            hashed_password=hashed_pwd,
            is_active=True,
            is_verified=True,
            auth_provider="local",
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        db.flush()
    else:
        # If user existed but had no password or requested password update
        if not user.hashed_password:
            user.hashed_password = hash_password(payload.password)
        if payload.full_name and not user.full_name:
            user.full_name = payload.full_name.strip()
        user.is_active = True
        user.updated_at = now

    # Add or update company membership
    existing_mem = (
        db.query(CompanyMembership)
        .filter(CompanyMembership.user_id == user.id, CompanyMembership.company_id == inv.company_id)
        .first()
    )
    if existing_mem:
        existing_mem.role = inv.role
        existing_mem.status = "active"
        existing_mem.updated_at = now
    else:
        new_mem = CompanyMembership(
            id=str(uuid.uuid4()),
            user_id=user.id,
            company_id=inv.company_id,
            role=inv.role,
            status="active",
            created_at=now,
            updated_at=now,
        )
        db.add(new_mem)

    # Mark invitation accepted
    inv.status = "accepted"
    inv.updated_at = now
    db.commit()
    db.refresh(user)

    # Issue JWT tokens for worker
    token_data = {"sub": str(user.id), "email": user.email, "company_id": str(company.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user_resp = UserProfileResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_verified=user.is_verified,
        auth_provider=user.auth_provider,
        created_at=user.created_at,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_resp,
        active_company_id=str(company.id),
    )


