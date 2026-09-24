export interface UserProfile {
  id: string
  email: string
  full_name: string
  avatar_url?: string | null
  is_active: boolean
  is_verified: boolean
  auth_provider: string
  created_at: string
}

export interface CompanyMembershipItem {
  membership_id: string
  company_id: string
  company_name: string
  company_slug: string
  role: "owner" | "admin" | "analyst" | "viewer"
  status: string
  id?: string
  name?: string
}

export interface AuthTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserProfile
  active_company_id?: string | null
}

export interface MemberResponseItem {
  membership_id: string
  user_id?: string | null
  user_email?: string | null
  user_full_name?: string | null
  role: "owner" | "admin" | "analyst" | "viewer"
  status: string
  created_at: string
}

export interface CompanyDetail {
  id: string
  name: string
  slug: string
  domain_type: string
  owner_id: string
  user_role: "owner" | "admin" | "analyst" | "viewer"
  created_at: string
  member_count: number
  dataset_count: number
  industry?: string
  company_size?: string
  country?: string
  primary_objective?: string
}
