"""Authentication, User & Company Pydantic Schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# User Schemas
class UserRegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2)
    company_name: Optional[str] = None  # If provided, auto-creates company


class UserLoginRequest(BaseModel):
    email: str
    password: str



class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None  # Google ID token (JWT) or access token
    code: Optional[str] = None  # Authorization code
    redirect_uri: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    auth_provider: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfileResponse
    active_company_id: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Company Schemas
class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=2)
    domain_type: Optional[str] = "General Business"


class CompanyMembershipItem(BaseModel):
    membership_id: str
    company_id: str
    company_name: str
    company_slug: str
    role: str  # "owner", "admin", "analyst", "viewer"
    status: str


class UserWithCompaniesResponse(BaseModel):
    user: UserProfileResponse
    companies: List[CompanyMembershipItem]


class MemberInviteRequest(BaseModel):
    email: str
    role: str = "analyst"  # "admin", "analyst", "viewer"



class MemberResponseItem(BaseModel):
    membership_id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    role: str
    status: str
    created_at: datetime
    invitation_token: Optional[str] = None
    invite_url: Optional[str] = None


class InvitationValidateResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    role: Optional[str] = None
    company_name: Optional[str] = None
    company_id: Optional[str] = None
    error: Optional[str] = None


class AcceptInvitationRequest(BaseModel):
    token: str
    full_name: str = Field(min_length=2)
    password: str = Field(min_length=6)


class CompanyDetailResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain_type: str
    owner_id: str
    user_role: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    country: Optional[str] = None
    primary_objective: Optional[str] = None
    created_at: datetime
    member_count: int = 1
    dataset_count: int = 0


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


class CompanyOnboardingRequest(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    country: Optional[str] = None
    primary_objective: Optional[str] = None


class CompanySettingsUpdateRequest(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    country: Optional[str] = None
    primary_objective: Optional[str] = None
    settings_json: Optional[str] = None

