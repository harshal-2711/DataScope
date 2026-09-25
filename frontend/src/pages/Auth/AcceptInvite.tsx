import { useEffect, useState } from "react"
import { useNavigate, useSearchParams, Link } from "react-router-dom"
import { ArrowRight, Lock, User, CheckCircle2, AlertCircle, Eye, EyeOff, Building2 } from "lucide-react"
import { AuthLayout } from "@/components/layout/AuthLayout"
import { acceptInvitation, validateInvitation } from "@/lib/authApi"
import { useAuth } from "@/context/AuthContext"

export default function AcceptInvite() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token") || searchParams.get("invitation_token") || ""
  const navigate = useNavigate()
  const { refreshProfile } = useAuth()

  const [isValidating, setIsValidating] = useState(true)
  const [invitationData, setInvitationData] = useState<{
    valid: boolean
    email?: string
    role?: string
    company_name?: string
    company_id?: string
    error?: string
  } | null>(null)

  const [fullName, setFullName] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSuccess, setIsSuccess] = useState(false)

  useEffect(() => {
    if (!token) {
      setIsValidating(false)
      setInvitationData({
        valid: false,
        error: "No invitation token was detected in the link. Please ask your administrator to share the complete setup link.",
      })
      return
    }

    validateInvitation(token)
      .then((data) => {
        setInvitationData(data)
        if (data.email) {
          // Prepopulate full name default from email prefix
          const defaultName = data.email.split("@")[0].replace(/[._-]/g, " ")
          setFullName(defaultName.charAt(0).toUpperCase() + defaultName.slice(1))
        }
      })
      .catch(() => {
        setInvitationData({
          valid: false,
          error: "Unable to verify invitation details. Please check your network connection.",
        })
      })
      .finally(() => {
        setIsValidating(false)
      })
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!fullName.trim() || !password) {
      setError("Please complete all required fields.")
      return
    }
    if (password.length < 6) {
      setError("Password must contain at least 6 characters.")
      return
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match. Please re-enter.")
      return
    }

    setError(null)
    setIsSubmitting(true)

    try {
      await acceptInvitation(token, fullName.trim(), password)
      await refreshProfile()
      setIsSuccess(true)
      setTimeout(() => {
        navigate("/overview", { replace: true })
      }, 1200)
    } catch (err: any) {
      setError(err.message || "Failed to activate your account. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isValidating) {
    return (
      <AuthLayout
        title="Validating Invitation"
        subtitle="Verifying your workspace access credentials..."
        badgeText="Team Access"
      >
        <div className="text-center py-8 text-xs text-neutral-400">Verifying secure token...</div>
      </AuthLayout>
    )
  }

  if (!invitationData?.valid) {
    return (
      <AuthLayout
        title="Invalid Invitation"
        subtitle="This invitation could not be verified."
        badgeText="Access Issue"
      >
        <div className="text-center py-4 space-y-4">
          <div className="w-12 h-12 rounded-full bg-destructive/10 border border-destructive/20 text-destructive flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <p className="text-xs text-neutral-400 leading-relaxed max-w-sm mx-auto">
            {invitationData?.error || "This invitation link is expired or has already been redeemed."}
          </p>
          <div className="pt-2">
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-white hover:bg-neutral-200 text-black text-xs font-semibold rounded-xl transition-colors"
            >
              <span>Go to Sign In</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </AuthLayout>
    )
  }

  if (isSuccess) {
    return (
      <AuthLayout
        title="Welcome to DataScope"
        subtitle={`Successfully joined ${invitationData.company_name}`}
        badgeText="Account Activated"
      >
        <div className="text-center py-6 space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-white">Setup Complete</h3>
          <p className="text-xs text-neutral-400">Redirecting to your company workspace analytics...</p>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      title={`Join ${invitationData.company_name}`}
      subtitle={`You've been invited as a ${invitationData.role?.toUpperCase()} to collaborate on shared data.`}
      badgeText="Worker Setup"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="p-3 rounded-xl bg-[#0A0A0A] border border-neutral-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Building2 className="w-4 h-4 text-neutral-400" />
            <div>
              <div className="text-xs font-semibold text-white">{invitationData.company_name}</div>
              <div className="text-[11px] text-neutral-400">{invitationData.email}</div>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-neutral-800 text-neutral-200 border border-neutral-700">
            {invitationData.role}
          </span>
        </div>

        <div>
          <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="worker-full-name">
            Your Full Name
          </label>
          <div className="relative">
            <User className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              id="worker-full-name"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Alex Smith"
              className="w-full pl-10 pr-3.5 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="worker-password">
            Create Your Password
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              id="worker-password"
              type={showPassword ? "text" : "password"}
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full pl-10 pr-10 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 p-1"
            >
              {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="worker-confirm-password">
            Confirm Password
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              id="worker-confirm-password"
              type={showPassword ? "text" : "password"}
              required
              minLength={6}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full pl-10 pr-3.5 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 transition-colors"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-2.5 px-4 bg-white hover:bg-neutral-200 text-black font-semibold text-xs rounded-xl transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 mt-2"
        >
          <span>{isSubmitting ? "Activating..." : "Create Account & Join"}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>

        <div className="text-center pt-2">
          <Link to="/login" className="text-xs text-neutral-400 hover:text-white transition-colors">
            Already have an account? Sign in
          </Link>
        </div>
      </form>
    </AuthLayout>
  )
}
