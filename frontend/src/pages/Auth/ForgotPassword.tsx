import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowRight, CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react';
import { forgotPassword } from '@/lib/authApi';
import { AuthLayout } from '@/components/layout/AuthLayout';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Please enter your work email address.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await forgotPassword(email.trim());
      setSubmitted(true);
      if (res.reset_token) {
        setResetToken(res.reset_token);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to send password reset link. Please verify your email.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="Enter your work email address to receive password recovery instructions."
      badgeText="Account Recovery"
    >
      {error && (
        <div className="mb-5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}

      {submitted ? (
        <div className="text-center py-2">
          <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-3">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-white mb-1.5">Check Your Email</h3>
          <p className="text-neutral-400 text-xs leading-relaxed mb-5">
            If an account with <strong className="text-white">{email}</strong> exists, password reset instructions have been generated.
          </p>

          {resetToken && (
            <div className="p-3.5 rounded-xl bg-[#0A0A0A] border border-neutral-800 text-left mb-5">
              <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider block mb-1">
                Development Environment Link:
              </span>
              <Link
                to={`/reset-password?token=${resetToken}`}
                className="text-xs text-blue-400 hover:text-blue-300 break-all underline"
              >
                Proceed to Reset Password Form &rarr;
              </Link>
            </div>
          )}

          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-neutral-300 hover:text-white transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Sign in
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="recovery-email">
              Work Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                id="recovery-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full pl-10 pr-4 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 bg-white hover:bg-neutral-200 text-black font-semibold text-sm rounded-xl transition-colors duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>Send instructions</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          <div className="text-center mt-5 pt-3 border-t border-neutral-800/80">
            <Link
              to="/login"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-neutral-400 hover:text-white transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Sign in
            </Link>
          </div>
        </form>
      )}
    </AuthLayout>
  );
};

export default ForgotPasswordPage;
