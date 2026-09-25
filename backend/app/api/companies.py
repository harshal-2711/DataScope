"""Company & Workspace Management API Router."""
from __future__ import annotations

import re
import secrets
import uuid
from datetime import datetime, timezone, timedelta

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import TenantContext, get_current_company, get_current_user, require_role
from app.db.session import get_db
from app.models.company import Company
from app.models.dataset import Dataset
from app.models.membership import CompanyMembership
from app.models.invitation import Invitation
from app.models.user import User
from app.schemas.auth import (
    CompanyCreateRequest,
    CompanyDetailResponse,
    CompanyMembershipItem,
    CompanyOnboardingRequest,
    CompanySettingsUpdateRequest,
    MemberInviteRequest,
    MemberResponseItem,
)


router = APIRouter(prefix="/companies", tags=["Companies & Workspaces"])


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    s = re.sub(r"[-\s]+", "-", s)
    return s or "workspace"


@router.get("", response_model=List[CompanyMembershipItem])
def list_user_companies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all company workspaces accessible to the authenticated user."""
    memberships = (
        db.query(CompanyMembership, Company)
        .join(Company, Company.id == CompanyMembership.company_id)
        .filter(CompanyMembership.user_id == current_user.id, CompanyMembership.status == "active")
        .all()
    )
    return [
        CompanyMembershipItem(
            membership_id=m.id,
            company_id=c.id,
            company_name=c.name,
            company_slug=c.slug,
            role=m.role,
            status=m.status,
        )
        for m, c in memberships
    ]


@router.post("", response_model=CompanyMembershipItem, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new company workspace and assign the creator as Owner."""
    name_clean = payload.name.strip()
    slug_base = _slugify(name_clean)
    slug = f"{slug_base}-{uuid.uuid4().hex[:6]}"

    new_company = Company(
        id=str(uuid.uuid4()),
        name=name_clean,
        slug=slug,
        domain_type=payload.domain_type or "General Business",
        owner_id=current_user.id,
    )
    db.add(new_company)
    db.flush()

    membership = CompanyMembership(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        company_id=new_company.id,
        role="owner",
        status="active",
    )
    db.add(membership)
    db.commit()

    return CompanyMembershipItem(
        membership_id=membership.id,
        company_id=new_company.id,
        company_name=new_company.name,
        company_slug=new_company.slug,
        role=membership.role,
        status=membership.status,
    )


@router.get("/{company_id}", response_model=CompanyDetailResponse)
def get_company_details(
    company_id: str,
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Get metadata and statistics for the active company workspace."""
    if company_id != tenant.company_id:
        membership = (
            db.query(CompanyMembership)
            .filter(
                CompanyMembership.user_id == tenant.user.id,
                CompanyMembership.company_id == company_id,
                CompanyMembership.status == "active",
            )
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not an active member of this company workspace.",
            )
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company workspace not found.",
            )
        tenant = TenantContext(company=company, membership=membership, user=tenant.user)

    member_count = (
        db.query(CompanyMembership)
        .filter(CompanyMembership.company_id == tenant.company_id, CompanyMembership.status == "active")
        .count()
    )
    dataset_count = db.query(Dataset).filter(Dataset.company_id == tenant.company_id).count()

    return CompanyDetailResponse(
        id=tenant.company.id,
        name=tenant.company.name,
        slug=tenant.company.slug,
        domain_type=tenant.company.domain_type,
        owner_id=tenant.company.owner_id,
        user_role=tenant.role,
        industry=tenant.company.industry,
        company_size=tenant.company.company_size,
        country=tenant.company.country,
        primary_objective=tenant.company.primary_objective,
        created_at=tenant.company.created_at,
        member_count=member_count,
        dataset_count=dataset_count,
    )


@router.post("/onboarding")
def complete_company_onboarding(
    payload: CompanyOnboardingRequest,
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Update onboarding fields for the active company workspace."""
    company = tenant.company
    if payload.company_name:
        company.name = payload.company_name.strip()
    if payload.industry:
        company.industry = payload.industry.strip()
    if payload.company_size:
        company.company_size = payload.company_size.strip()
    if payload.country:
        company.country = payload.country.strip()
    if payload.primary_objective:
        company.primary_objective = payload.primary_objective.strip()

    company.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(company)

    return {
        "status": "success",
        "message": "Company onboarding profile updated.",
        "company": {
            "id": company.id,
            "name": company.name,
            "industry": company.industry,
            "company_size": company.company_size,
            "country": company.country,
            "primary_objective": company.primary_objective,
        }
    }


@router.put("/{company_id}/settings")
def update_company_settings(
    company_id: str,
    payload: CompanySettingsUpdateRequest,
    tenant: TenantContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Update company settings and profile (Admin/Owner only)."""
    company = tenant.company
    if payload.name:
        company.name = payload.name.strip()
    if payload.industry is not None:
        company.industry = payload.industry.strip()
    if payload.company_size is not None:
        company.company_size = payload.company_size.strip()
    if payload.country is not None:
        company.country = payload.country.strip()
    if payload.primary_objective is not None:
        company.primary_objective = payload.primary_objective.strip()
    if payload.settings_json is not None:
        company.settings = payload.settings_json

    company.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(company)

    return {
        "status": "success",
        "message": "Workspace settings saved successfully.",
        "company": {
            "id": company.id,
            "name": company.name,
            "industry": company.industry,
            "company_size": company.company_size,
            "country": company.country,
            "primary_objective": company.primary_objective,
        }
    }



@router.get("/{company_id}/members", response_model=List[MemberResponseItem])
def list_company_members(
    company_id: str,
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """List team members and pending invitations for the company."""
    if str(company_id) != str(tenant.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-company access denied. You can only view members of your active company workspace.",
        )

    # 1. Active company members
    memberships = (
        db.query(CompanyMembership)
        .filter(CompanyMembership.company_id == tenant.company_id)
        .all()
    )

    user_ids = [str(m.user_id) for m in memberships if m.user_id]
    user_map = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_map = {str(u.id): u for u in users}

    items = []
    for m in memberships:
        u = user_map.get(str(m.user_id)) if m.user_id else None
        items.append(
            MemberResponseItem(
                membership_id=str(m.id),
                user_id=str(u.id) if u else None,
                user_email=u.email if u else m.invited_email,
                user_full_name=u.full_name if u else "Invited Member",
                role=m.role,
                status=m.status,
                created_at=m.created_at,
            )
        )

    # 2. Pending invitations from Invitation table
    pending_invites = (
        db.query(Invitation)
        .filter(
            Invitation.company_id == tenant.company_id,
            Invitation.status == "pending",
            Invitation.expires_at > datetime.now(timezone.utc),
        )
        .order_by(Invitation.created_at.desc())
        .all()
    )
    for inv in pending_invites:
        items.append(
            MemberResponseItem(
                membership_id=str(inv.id),
                user_id=None,
                user_email=inv.email,
                user_full_name="Pending Invitation",
                role=inv.role,
                status="pending",
                created_at=inv.created_at,
                invitation_token=inv.invitation_token,
                invite_url=f"/invite/accept?token={inv.invitation_token}",
            )
        )

    return items


@router.post("/{company_id}/invitations", response_model=MemberResponseItem, status_code=status.HTTP_201_CREATED)
def invite_member(
    company_id: str,
    payload: MemberInviteRequest,
    tenant: TenantContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Invite a new team member to the company with a designated role (Admin, Analyst, Viewer)."""
    if str(company_id) != str(tenant.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-company access denied. You can only invite members to your active workspace.",
        )

    email_clean = payload.email.lower().strip()
    role_clean = payload.role.lower().strip()
    if role_clean not in ["admin", "analyst", "viewer"]:
        role_clean = "analyst"

    # Only OWNER can invite another Admin
    if role_clean == "admin" and tenant.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace Owner can invite or assign Administrator privileges.",
        )

    # Check if user is already an active member of this company workspace
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        existing_membership = (
            db.query(CompanyMembership)
            .filter(
                CompanyMembership.company_id == tenant.company_id,
                CompanyMembership.user_id == existing_user.id,
            )
            .first()
        )
        if existing_membership and existing_membership.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{email_clean}' is already an active member of this workspace.",
            )

    # Check if pending invitation already exists for this email
    now = datetime.now(timezone.utc)
    existing_inv = (
        db.query(Invitation)
        .filter(
            Invitation.company_id == tenant.company_id,
            Invitation.email == email_clean,
            Invitation.status == "pending",
            Invitation.expires_at > now,
        )
        .first()
    )
    if existing_inv:
        return MemberResponseItem(
            membership_id=str(existing_inv.id),
            user_id=None,
            user_email=existing_inv.email,
            user_full_name="Pending Invitation",
            role=existing_inv.role,
            status="pending",
            created_at=existing_inv.created_at,
            invitation_token=existing_inv.invitation_token,
            invite_url=f"/invite/accept?token={existing_inv.invitation_token}",
        )

    # Create new persistent secure invitation
    token = secrets.token_urlsafe(32)
    expires_at = now + timedelta(days=7)

    invitation = Invitation(
        id=str(uuid.uuid4()),
        company_id=str(tenant.company_id),
        email=email_clean,
        role=role_clean,
        invited_by_id=str(tenant.user_id),
        invitation_token=token,
        status="pending",
        expires_at=expires_at,
        created_at=now,
        updated_at=now,
    )
    db.add(invitation)
    db.commit()

    return MemberResponseItem(
        membership_id=str(invitation.id),
        user_id=None,
        user_email=email_clean,
        user_full_name="Pending Invitation",
        role=invitation.role,
        status="pending",
        created_at=invitation.created_at,
        invitation_token=invitation.invitation_token,
        invite_url=f"/invite/accept?token={invitation.invitation_token}",
    )


@router.delete("/{company_id}/members/{membership_id}")
def remove_member(
    company_id: str,
    membership_id: str,
    tenant: TenantContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Remove a member or cancel an invitation."""
    if str(company_id) != str(tenant.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-company access denied. You can only remove members from your active workspace.",
        )

    # 1. Check if it's an invitation in the invitations table
    invitation = (
        db.query(Invitation)
        .filter(Invitation.id == membership_id, Invitation.company_id == tenant.company_id)
        .first()
    )
    if invitation:
        invitation.status = "revoked"
        invitation.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "success", "message": "Invitation successfully revoked."}

    # 2. Check if it's an active membership
    membership = (
        db.query(CompanyMembership)
        .filter(CompanyMembership.id == membership_id, CompanyMembership.company_id == tenant.company_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member or invitation record not found.")

    if membership.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The workspace Owner cannot be removed from the company.",
        )

    # Only Owner can remove an Admin
    if membership.role == "admin" and tenant.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace Owner can remove an Administrator.",
        )

    # Users cannot remove themselves through this endpoint
    if str(membership.user_id) == str(tenant.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the workspace.",
        )

    db.delete(membership)
    db.commit()
    return {"status": "success", "message": "Member successfully removed from workspace."}


@router.put("/{company_id}/members/{membership_id}/role")
def update_member_role(
    company_id: str,
    membership_id: str,
    payload: dict,
    tenant: TenantContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Update a team member's role (Admin/Owner only)."""
    if str(company_id) != str(tenant.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-company access denied.",
        )

    target_role = str(payload.get("role", "")).lower().strip()
    if target_role not in ["admin", "analyst", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'admin', 'analyst', or 'viewer'.",
        )

    # Only OWNER can promote someone to Admin or change an Admin's role
    if (target_role == "admin" or tenant.role != "owner") and tenant.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace Owner can modify Administrator privileges.",
        )

    membership = (
        db.query(CompanyMembership)
        .filter(CompanyMembership.id == membership_id, CompanyMembership.company_id == tenant.company_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    if membership.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot alter the workspace Owner's role.",
        )

    if str(membership.user_id) == str(tenant.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )

    membership.role = target_role
    membership.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "success", "message": f"Member role updated to {target_role}."}
