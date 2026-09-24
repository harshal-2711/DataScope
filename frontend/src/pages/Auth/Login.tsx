import { useState, useEffect } from "react"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { ArrowRight, Lock, Mail, AlertCircle, Eye, EyeOff, Building2, CheckCircle2 } from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import { AuthLayout } from "@/components/layout/AuthLayout"

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showGoogleModal, setShowGoogleModal] = useState(false)

  useEffect(() => {
    if (location.state?.successMessage) {
      setSuccessMessage(location.state.successMessage)
    }
    if (location.state?.registeredEmail) {
      setEmail(location.state.registeredEmail)
    }
  }, [location.state])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password) {
      setError("Please enter both work email and password.")
      return
    }
    setError(null)
    setSuccessMessage(null)
    setIsSubmitting(true)
    try {
      await login(email.trim(), password)
      navigate("/overview", { replace: true })
    } catch (err: any) {
      const msg = err.message || ""
      if (msg.toLowerCase().includes("invalid") || msg.toLowerCase().includes("credentials")) {
        setError("Invalid login credentials. If you haven't created an account with this email yet, please click 'Create workspace' below.")
      } else {
        setError(msg || "Unable to sign in. Please check your credentials.")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleGoogleClick = () => {
    setShowGoogleModal(true)
  }

  return (
    <AuthLayout
      title="Sign in to your workspace"
      subtitle="Access your business intelligence, operational insights, and decision reports."
      badgeText="Enterprise Decision Intelligence"
    >
      {successMessage && (
        <div className="mb-5 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
          <span className="leading-relaxed font-medium">{successMessage}</span>
        </div>
      )}

      {error && (
        <div className="mb-5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="work-email">
            Work Email
          </label>
          <div className="relative">
            <Mail className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              id="work-email"
              type="email"
              autoComplete="email"
              required
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium text-neutral-300" htmlFor="account-password">
              Password
            </label>
            <Link
              to="/forgot-password"
              className="text-xs text-neutral-400 hover:text-white transition-colors underline-offset-2 hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Lock className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              id="account-password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-10 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 p-1 rounded transition-colors"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full mt-2 py-2.5 px-4 bg-white hover:bg-neutral-200 text-black font-semibold text-sm rounded-xl transition-colors duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
        >
          {isSubmitting ? (
            <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <span>Sign in</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      <div className="relative my-5">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-neutral-800" />
        </div>
        <div className="relative flex justify-center text-[11px] uppercase">
          <span className="bg-[#141414] px-3 text-neutral-500 font-medium">Or continue with</span>
        </div>
      </div>

      {/* Google OAuth Button */}
      <button
        type="button"
        onClick={handleGoogleClick}
        className="w-full py-2.5 px-4 bg-[#0A0A0A] hover:bg-neutral-900 border border-neutral-800 hover:border-neutral-700 rounded-xl text-sm font-medium text-neutral-200 transition-colors flex items-center justify-center gap-2.5 cursor-pointer shadow-sm"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
          />
        </svg>
        <span>Continue with Google</span>
      </button>

      {/* Footer Link */}
      <div className="text-center mt-6 pt-4 border-t border-neutral-800/80">
        <p className="text-xs text-neutral-400">
          Need a company workspace?{" "}
          <Link to="/register" className="text-white hover:text-neutral-200 font-semibold underline underline-offset-4">
            Create workspace
          </Link>
        </p>
      </div>

      {/* Google OAuth Modal / Setup Notice */}
      {showGoogleModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#141414] border border-neutral-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center gap-3 mb-3 text-neutral-200">
              <div className="p-2 rounded-lg bg-neutral-900 border border-neutral-800 text-blue-400">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Google OAuth 2.0 Configuration</h3>
                <p className="text-[11px] text-neutral-400">Single Sign-On for Enterprise Teams</p>
              </div>
            </div>
            <p className="text-xs text-neutral-300 leading-relaxed mb-4">
              Google Single Sign-On is supported via PKCE OAuth. To activate Google SSO for your organization, configure the environment variables in your server:
            </p>
            <div className="bg-[#0B0B0B] p-3.5 rounded-xl border border-neutral-800 font-mono text-[11px] text-neutral-300 space-y-1 mb-5">
              <div>GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com</div>
              <div>GOOGLE_CLIENT_SECRET=your-client-secret</div>
              <div>GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback</div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowGoogleModal(false)}
                className="px-4 py-2 bg-white hover:bg-neutral-200 text-black text-xs font-semibold rounded-xl transition-colors cursor-pointer"
              >
                Close & Use Email Login
              </button>
            </div>
          </div>
        </div>
      )}
    </AuthLayout>
  )
}
