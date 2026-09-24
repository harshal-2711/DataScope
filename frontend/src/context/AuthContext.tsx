import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react"
import {
  clearStoredAuth,
  createCompany as apiCreateCompany,
  fetchCurrentUser,
  getStoredActiveCompanyId,
  getStoredToken,
  loginUser,
  registerUser,
  setStoredAuth,
} from "@/lib/authApi"
import { supabase, isSupabaseConfigured } from "@/lib/supabase"
import type { CompanyMembershipItem, UserProfile } from "@/types/auth"

export interface RealtimeEvent {
  type: string
  company_id: string
  data: any
}

export interface AuthContextValue {
  user: UserProfile | null
  companies: CompanyMembershipItem[]
  activeCompany: CompanyMembershipItem | null
  currentCompany: CompanyMembershipItem | null
  isLoading: boolean
  isAuthenticated: boolean
  isWsConnected: boolean
  initError: string | null
  lastRealtimeEvent: RealtimeEvent | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string, companyName?: string) => Promise<{ requiresEmailConfirmation?: boolean; user?: any } | void>
  logout: () => void
  switchCompany: (companyId: string) => void
  createCompany: (name: string, domainType?: string) => Promise<void>
  refreshProfile: () => Promise<void>
  refreshUser: () => Promise<void>
  retryInit: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [companies, setCompanies] = useState<CompanyMembershipItem[]>([])
  const [activeCompanyId, setActiveCompanyId] = useState<string | null>(() => getStoredActiveCompanyId())
  const [isLoading, setIsLoading] = useState(true)
  const [initError, setInitError] = useState<string | null>(null)
  const [isWsConnected, setIsWsConnected] = useState(false)
  const [lastRealtimeEvent, setLastRealtimeEvent] = useState<RealtimeEvent | null>(null)

  const activeCompany = useMemo(() => {
    if (!companies.length) return null
    if (activeCompanyId) {
      const match = companies.find((c) => c.company_id === activeCompanyId)
      if (match) return match
    }
    return companies[0]
  }, [companies, activeCompanyId])

  const isRefreshingRef = useRef(false)

  const refreshProfile = useCallback(async () => {
    if (isRefreshingRef.current) return
    isRefreshingRef.current = true
    setInitError(null)

    const token = getStoredToken()
    if (!token && !isSupabaseConfigured) {
      setUser(null)
      setCompanies([])
      setIsLoading(false)
      isRefreshingRef.current = false
      return
    }

    // Wrap backend profile fetch with a 4-second timeout guard
    const fetchWithTimeout = async () => {
      if (!token) return null
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 4000)
      try {
        const data = await fetchCurrentUser()
        clearTimeout(timer)
        return data
      } catch (err) {
        clearTimeout(timer)
        throw err
      }
    }

    try {
      if (token) {
        const data = await fetchWithTimeout()
        if (data) {
          setUser(data.user)
          setCompanies(data.companies)
          if (data.companies.length > 0) {
            const storedId = getStoredActiveCompanyId()
            const validStored = data.companies.find((c) => c.company_id === storedId)
            if (validStored) {
              setActiveCompanyId(validStored.company_id)
            } else {
              setActiveCompanyId(data.companies[0].company_id)
              localStorage.setItem("datascope_active_company_id", data.companies[0].company_id)
            }
          }
          setIsLoading(false)
          isRefreshingRef.current = false
          return
        }
      }
    } catch (err: any) {
      console.warn("Backend auth fetch failed:", err?.message || err)
    }

    // Supabase fallback verification
    if (isSupabaseConfigured) {
      try {
        const supaSessionPromise = supabase.auth.getSession()
        const timeoutPromise = new Promise<{ data: { session: null } }>((resolve) =>
          setTimeout(() => resolve({ data: { session: null } }), 3500)
        )
        const { data: supaSession } = await Promise.race([supaSessionPromise, timeoutPromise])

        if (supaSession?.session?.user) {
          const supaUser = supaSession.session.user
          const sToken = supaSession.session.access_token
          setStoredAuth(sToken, supaSession.session.refresh_token || "")

          const fallbackUser: UserProfile = {
            id: supaUser.id,
            email: supaUser.email || "",
            full_name: supaUser.user_metadata?.full_name || supaUser.email?.split("@")[0] || "Team Member",
            avatar_url: supaUser.user_metadata?.avatar_url || null,
            is_active: true,
            is_verified: true,
            auth_provider: "supabase",
            created_at: supaUser.created_at,
          }
          setUser(fallbackUser)

          const defaultComp: CompanyMembershipItem = {
            membership_id: `mem-${supaUser.id.slice(0, 8)}`,
            company_id: `workspace-${supaUser.id.slice(0, 8)}`,
            company_name: supaUser.user_metadata?.company_name || `${fallbackUser.full_name}'s Workspace`,
            company_slug: `workspace-${supaUser.id.slice(0, 8)}`,
            role: "owner",
            status: "active",
          }
          setCompanies([defaultComp])
          setActiveCompanyId(defaultComp.company_id)
          setIsLoading(false)
          isRefreshingRef.current = false
          return
        }
      } catch (supaErr) {
        console.warn("Supabase session check notice:", supaErr)
      }
    }

    // If no valid session or token could be verified, complete loading safely
    clearStoredAuth()
    setUser(null)
    setCompanies([])
    setIsLoading(false)
    isRefreshingRef.current = false
  }, [])

  const retryInit = useCallback(async () => {
    setIsLoading(true)
    setInitError(null)
    await refreshProfile()
  }, [refreshProfile])

  // Supabase Auth State Change Listener
  useEffect(() => {
    let isMounted = true

    if (!isSupabaseConfigured) {
      refreshProfile()
      return
    }

    const { data: authListener } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (!isMounted) return
      if (session?.access_token) {
        setStoredAuth(session.access_token, session.refresh_token || "")
        await refreshProfile()
      } else if (event === "SIGNED_OUT") {
        clearStoredAuth()
        setUser(null)
        setCompanies([])
        setIsLoading(false)
      }
    })

    refreshProfile()

    // Safety timeout to ensure loading screen NEVER hangs indefinitely
    const safetyTimer = setTimeout(() => {
      if (isMounted) {
        setIsLoading((prev) => {
          if (prev) {
            console.warn("Safety initialization timeout triggered.")
            return false
          }
          return false
        })
      }
    }, 4500)

    return () => {
      isMounted = false
      clearTimeout(safetyTimer)
      authListener?.subscription.unsubscribe()
    }
  }, [refreshProfile])

  // Real-Time WebSocket Channel Listener
  useEffect(() => {
    if (!activeCompany?.company_id) {
      setIsWsConnected(false)
      return
    }
    const token = getStoredToken()
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const wsUrl = `${protocol}//${window.location.host}/api/ws/${activeCompany.company_id}?token=${token || ""}`

    let socket: WebSocket | null = null
    let reconnectTimeout: any = null

    function connectWs() {
      try {
        socket = new WebSocket(wsUrl)
        socket.onopen = () => {
          setIsWsConnected(true)
        }
        socket.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data)
            setLastRealtimeEvent(parsed)
          } catch (e) {}
        }
        socket.onclose = () => {
          setIsWsConnected(false)
          reconnectTimeout = setTimeout(connectWs, 4000)
        }
        socket.onerror = () => {
          setIsWsConnected(false)
        }
      } catch (err) {
        setIsWsConnected(false)
      }
    }

    connectWs()

    return () => {
      if (socket) socket.close()
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
    }
  }, [activeCompany?.company_id])

  const login = useCallback(async (email: string, password: string) => {
    let authSuccess = false
    let lastError: any = null

    // 1. Try Supabase Auth first
    if (isSupabaseConfigured) {
      try {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) {
          lastError = error
        } else if (data.session?.access_token) {
          setStoredAuth(data.session.access_token, data.session.refresh_token || "")
          authSuccess = true
        }
      } catch (err: any) {
        lastError = err
      }
    }

    // 2. If Supabase auth failed or user is not in Supabase yet, fallback to backend login
    if (!authSuccess) {
      try {
        await loginUser(email, password)
        authSuccess = true
      } catch (apiErr: any) {
        const message = apiErr?.message || lastError?.message || "Invalid email or password."
        throw new Error(message)
      }
    }

    await refreshProfile()
  }, [refreshProfile])

  const register = useCallback(async (email: string, password: string, fullName: string, companyName?: string) => {
    let requiresEmailConfirmation = false

    // 1. Register with Supabase Auth
    if (isSupabaseConfigured) {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            company_name: companyName || `${fullName}'s Workspace`,
          },
        },
      })
      if (error) {
        throw new Error(error.message)
      }
      if (data.user) {
        if (!data.session?.access_token) {
          requiresEmailConfirmation = true
        }
      }
    }

    // 2. Synchronize with Backend Database
    try {
      await registerUser(email, password, fullName, companyName)
    } catch (apiErr: any) {
      console.warn("Backend registration sync notice:", apiErr?.message)
    }

    // Clear stored auth and active session so user explicitly logs in on Login page
    if (isSupabaseConfigured) {
      await supabase.auth.signOut().catch(() => {})
    }
    clearStoredAuth()
    setUser(null)
    setCompanies([])

    return { requiresEmailConfirmation }
  }, [])

  const logout = useCallback(async () => {
    if (isSupabaseConfigured) {
      await supabase.auth.signOut().catch(() => {})
    }
    clearStoredAuth()
    setUser(null)
    setCompanies([])
    setActiveCompanyId(null)
  }, [])

  const switchCompany = useCallback((companyId: string) => {
    setActiveCompanyId(companyId)
    localStorage.setItem("datascope_active_company_id", companyId)
  }, [])

  const createCompany = useCallback(async (name: string, domainType?: string) => {
    const newComp = await apiCreateCompany(name, domainType)
    await refreshProfile()
    switchCompany(newComp.company_id)
  }, [refreshProfile, switchCompany])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      companies,
      activeCompany,
      currentCompany: activeCompany,
      isLoading,
      isAuthenticated: !!user,
      isWsConnected,
      initError,
      lastRealtimeEvent,
      login,
      register,
      logout,
      switchCompany,
      createCompany,
      refreshProfile,
      refreshUser: refreshProfile,
      retryInit,
    }),
    [
      user,
      companies,
      activeCompany,
      isLoading,
      initError,
      isWsConnected,
      lastRealtimeEvent,
      login,
      register,
      logout,
      switchCompany,
      createCompany,
      refreshProfile,
      retryInit,
    ]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return ctx
}
