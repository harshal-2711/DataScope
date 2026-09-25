import type { AuthTokenResponse, CompanyDetail, CompanyMembershipItem, MemberResponseItem, UserProfile } from "@/types/auth"

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "") + "/api"

import { supabase, isSupabaseConfigured } from "./supabase"

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null
  const direct = localStorage.getItem("datascope_access_token")
  if (direct) return direct

  // Check Supabase session in localStorage
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && (key.startsWith("sb-") && key.endsWith("-auth-token"))) {
        const item = localStorage.getItem(key)
        if (item) {
          const parsed = JSON.parse(item)
          if (parsed?.access_token) {
            localStorage.setItem("datascope_access_token", parsed.access_token)
            if (parsed.refresh_token) {
              localStorage.setItem("datascope_refresh_token", parsed.refresh_token)
            }
            return parsed.access_token
          }
        }
      }
    }
  } catch {}
  return null
}

export function getStoredActiveCompanyId(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("datascope_active_company_id")
}

export function setStoredAuth(token: string, refreshToken: string, companyId?: string | null) {
  if (typeof window === "undefined") return
  localStorage.setItem("datascope_access_token", token)
  localStorage.setItem("datascope_refresh_token", refreshToken)
  if (companyId) {
    localStorage.setItem("datascope_active_company_id", companyId)
  }
}

export function clearStoredAuth() {
  if (typeof window === "undefined") return
  localStorage.removeItem("datascope_access_token")
  localStorage.removeItem("datascope_refresh_token")
  localStorage.removeItem("datascope_active_company_id")
  sessionStorage.removeItem("datascope_active_dataset_summary")
}

function getAuthHeaders(companyId?: string | null): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  const token = getStoredToken()
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  const activeCompId = companyId || getStoredActiveCompanyId()
  if (activeCompId) {
    headers["X-Company-Id"] = activeCompId
  }
  return headers
}

export async function registerUser(email: string, password: string, fullName: string, companyName?: string): Promise<AuthTokenResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      full_name: fullName,
      company_name: companyName || undefined,
    }),
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || "Registration failed. Please check your information.")
  }
  const data: AuthTokenResponse = await res.json()
  setStoredAuth(data.access_token, data.refresh_token, data.active_company_id)
  return data
}

export async function loginUser(email: string, password: string): Promise<AuthTokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || "Invalid email or password.")
  }
  const data: AuthTokenResponse = await res.json()
  setStoredAuth(data.access_token, data.refresh_token, data.active_company_id)
  return data
}

export async function googleAuth(credential: string): Promise<AuthTokenResponse> {
  const res = await fetch(`${API_BASE}/auth/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ credential }),
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || "Google authentication failed.")
  }
  const data: AuthTokenResponse = await res.json()
  setStoredAuth(data.access_token, data.refresh_token, data.active_company_id)
  return data
}

export async function refreshTokenApi(): Promise<AuthTokenResponse | null> {
  if (typeof window === "undefined") return null

  // 1. Try Supabase Auth session refresh if configured
  if (isSupabaseConfigured) {
    try {
      const { data, error } = await supabase.auth.refreshSession()
      if (!error && data.session?.access_token) {
        setStoredAuth(data.session.access_token, data.session.refresh_token || "")
        return {
          access_token: data.session.access_token,
          refresh_token: data.session.refresh_token || "",
          token_type: "bearer",
          user: {} as any,
          active_company_id: getStoredActiveCompanyId() || undefined,
        }
      }
    } catch {}
  }

  // 2. Try Backend API session refresh
  const refreshToken = localStorage.getItem("datascope_refresh_token")
  if (!refreshToken) return null

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) {
      return null
    }
    const data: AuthTokenResponse = await res.json()
    setStoredAuth(data.access_token, data.refresh_token, data.active_company_id)
    return data
  } catch {
    return null
  }
}

export async function fetchCurrentUser(): Promise<{ user: UserProfile; companies: CompanyMembershipItem[] }> {
  const token = getStoredToken()
  if (!token) throw new Error("Not authenticated")

  let res = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders(),
  })

  // Attempt token refresh on 401 before giving up
  if (res.status === 401) {
    const refreshed = await refreshTokenApi()
    if (refreshed?.access_token) {
      res = await fetch(`${API_BASE}/auth/me`, {
        headers: getAuthHeaders(refreshed.active_company_id),
      })
    }
  }

  if (!res.ok) {
    if (res.status === 401) {
      clearStoredAuth()
    }
    throw new Error("Failed to fetch user session.")
  }
  return res.json()
}

export async function createCompany(name: string, domainType?: string): Promise<CompanyMembershipItem> {
  const res = await fetch(`${API_BASE}/companies`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ name, domain_type: domainType }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to create company workspace.")
  }
  return res.json()
}

export async function fetchCompanyDetails(companyId: string): Promise<CompanyDetail> {
  const res = await fetch(`${API_BASE}/companies/${companyId}`, {
    headers: getAuthHeaders(companyId),
  })
  if (!res.ok) {
    throw new Error("Failed to load company details.")
  }
  return res.json()
}

export async function fetchCompanyMembers(companyId: string): Promise<MemberResponseItem[]> {
  const res = await fetch(`${API_BASE}/companies/${companyId}/members`, {
    headers: getAuthHeaders(companyId),
  })
  if (!res.ok) {
    throw new Error("Failed to load company members.")
  }
  return res.json()
}

export async function inviteCompanyMember(companyId: string, email: string, role: string): Promise<MemberResponseItem> {
  const res = await fetch(`${API_BASE}/companies/${companyId}/invitations`, {
    method: "POST",
    headers: getAuthHeaders(companyId),
    body: JSON.stringify({ email, role }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to invite member.")
  }
  return res.json()
}

export async function removeCompanyMember(companyId: string, membershipId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/companies/${companyId}/members/${membershipId}`, {
    method: "DELETE",
    headers: getAuthHeaders(companyId),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to remove member.")
  }
}

export async function forgotPassword(email: string): Promise<{ status: string; message: string; reset_token?: string }> {
  const res = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to send password reset request.")
  }
  return res.json()
}

export async function resetPassword(token: string, newPassword: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to reset password.")
  }
  return res.json()
}

export async function completeOnboarding(data: {
  company_name?: string
  industry?: string
  company_size?: string
  country?: string
  primary_objective?: string
}): Promise<{ status: string; message: string; company: any }> {
  const res = await fetch(`${API_BASE}/companies/onboarding`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to save company profile.")
  }
  return res.json()
}

export async function updateCompanySettings(
  companyId: string,
  data: {
    name?: string
    industry?: string
    company_size?: string
    country?: string
    primary_objective?: string
    settings_json?: string
  }
): Promise<{ status: string; message: string; company: any }> {
  const res = await fetch(`${API_BASE}/companies/${companyId}/settings`, {
    method: "PUT",
    headers: getAuthHeaders(companyId),
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to update workspace settings.")
  }
  return res.json()
}

