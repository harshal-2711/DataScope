import React from 'react';
import { ShieldAlert, LogOut, RefreshCw } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export const NoCompanyAccess: React.FC = () => {
  const { user, logout, refreshProfile } = useAuth();
  const [checking, setChecking] = React.useState(false);

  const handleRefresh = async () => {
    setChecking(true);
    try {
      await refreshProfile();
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#000000] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-[#0A0A0A] border border-neutral-800 rounded-2xl p-6 sm:p-8 text-center space-y-6 shadow-2xl">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
          <ShieldAlert className="w-7 h-7" />
        </div>

        <div className="space-y-2">
          <h2 className="text-xl font-bold text-white tracking-tight">No Company Access</h2>
          <p className="text-xs text-neutral-400 leading-relaxed">
            You are signed in as <span className="text-white font-medium">{user?.email}</span>, but your account is not currently associated with an active company workspace.
          </p>
        </div>

        <div className="p-3.5 rounded-xl bg-neutral-900/60 border border-neutral-800 text-left space-y-1.5 text-xs">
          <div className="font-semibold text-neutral-300">How to get access:</div>
          <div className="text-neutral-400 text-[11px] leading-relaxed">
            Ask a company Owner or Administrator to send an invitation to your email. Once invited, you will automatically gain access to their workspace upon your next login.
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={checking}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-neutral-200 text-black text-xs font-semibold transition disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${checking ? 'animate-spin' : ''}`} />
            {checking ? 'Checking...' : 'Check Status'}
          </button>

          <button
            type="button"
            onClick={logout}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white border border-neutral-800 text-xs font-semibold transition cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            Log Out
          </button>
        </div>
      </div>
    </div>
  );
};
