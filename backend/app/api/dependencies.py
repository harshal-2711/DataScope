"""FastAPI Dependencies for Authentication, Tenant Isolation & RBAC."""
from __future__ import annotations

from typing import Callable, Optional
from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.core.supabase_client import verify_supabase_jwt
from app.db.session import get_db
from app.models.company import Company
from app.models.membership import CompanyMembership
from app.models.user import User

security_bearer = HTTPBearer(auto_error=False)

ROLE_HIERARCHY = {
    "viewer": 1,
    "analyst": 2,
    "admin": 3,
    "owner": 4,
}


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT bearer token (Supabase Auth or application token) and return active User instance."""
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.credentials
    # 1. Try Supabase verification
    payload = verify_supabase_jwt(token)
    if not payload:
        # 2. Try standard local token decode
        payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(payload.get("sub", ""))
    user_email = payload.get("email") or payload.get("user_metadata", {}).get("email")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user and user_email:
        # Check by email
        user = db.query(User).filter(User.email == user_email).first()

    if not user and user_email:
        # Provision profile record for new Supabase user
        full_name = payload.get("user_metadata", {}).get("full_name") or user_email.split("@")[0]
        user = User(
            id=user_id,
            email=user_email,
            full_name=full_name,
            auth_provider=payload.get("app_metadata", {}).get("provider", "supabase"),
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.flush()

        # Check for any pending invitation for this user
        import uuid
        from datetime import datetime, timezone
        from app.models.invitation import Invitation
        pending_inv = (
            db.query(Invitation)
            .filter(
                Invitation.email == user_email.lower().strip(),
                Invitation.status == "pending",
                Invitation.expires_at > datetime.now(timezone.utc),
            )
            .order_by(Invitation.created_at.desc())
            .first()
        )
        if pending_inv:
            membership = CompanyMembership(
                id=str(uuid.uuid4()),
                company_id=pending_inv.company_id,
                user_id=user.id,
                role=pending_inv.role,
                status="active",
            )
            db.add(membership)
            pending_inv.status = "accepted"
            pending_inv.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is deactivated.",
        )
    return user


def get_optional_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return User instance if valid token present, else None."""
    if not auth_header or not auth_header.credentials:
        return None
    try:
        return get_current_user(auth_header, db)
    except Exception:
        return None


class TenantContext:
    def __init__(self, company: Company, membership: CompanyMembership, user: User):
        self.company = company
        self.membership = membership
        self.user = user
        self.user_id = user.id
        self.company_id = company.id
        self.role = membership.role


def get_current_company(
    x_company_id: Optional[str] = Header(None, alias="X-Company-Id"),
    company_id_query: Optional[str] = Query(None, alias="company_id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantContext:
    """Validate that the current user has access to the requested company workspace."""
    target_company_id = x_company_id or company_id_query

    membership = None
    if target_company_id:
        membership = (
            db.query(CompanyMembership)
            .filter(
                CompanyMembership.user_id == current_user.id,
                CompanyMembership.company_id == target_company_id,
                CompanyMembership.status == "active",
            )
            .first()
        )

    if target_company_id and not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You are not an active member of this company workspace.",
        )

    if not membership:
        # Fall back to user's first active company membership
        membership = (
            db.query(CompanyMembership)
            .filter(CompanyMembership.user_id == current_user.id, CompanyMembership.status == "active")
            .first()
        )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No company access. You need an invitation from a company administrator to access workspace resources.",
        )

    company = db.query(Company).filter(Company.id == membership.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company workspace not found.",
        )
    return TenantContext(company=company, membership=membership, user=current_user)


def get_optional_company(
    x_company_id: Optional[str] = Header(None, alias="X-Company-Id"),
    company_id_query: Optional[str] = Query(None, alias="company_id"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Optional[TenantContext]:
    """Return TenantContext if authenticated user is present, else None."""
    if not current_user:
        return None
    try:
        return get_current_company(
            x_company_id=x_company_id,
            company_id_query=company_id_query,
            current_user=current_user,
            db=db,
        )
    except Exception:
        return None


def require_role(min_role: str = "analyst") -> Callable:
    """Factory creating dependency to enforce minimum role permission."""
    min_level = ROLE_HIERARCHY.get(min_role.lower(), 2)

    def role_checker(tenant: TenantContext = Depends(get_current_company)) -> TenantContext:
        user_level = ROLE_HIERARCHY.get(tenant.role.lower(), 1)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {min_role.capitalize()} or higher (Your role: {tenant.role.capitalize()}).",
            )
        return tenant

    return role_checker
