import React, { useEffect, useState } from 'react';
import { 
  Building2, 
  User, 
  Shield, 
  Users, 
  Save, 
  Plus, 
  Trash2
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { fetchCompanyDetails, fetchCompanyMembers, inviteCompanyMember, removeCompanyMember, updateCompanySettings } from '@/lib/authApi';
import type { MemberResponseItem } from '@/types/auth';

export const SettingsPage: React.FC = () => {
  const { user, activeCompany, refreshProfile } = useAuth();
  const [activeTab, setActiveTab] = useState<'company' | 'profile' | 'team' | 'security'>('company');

  // Company Profile form
  const [companyName, setCompanyName] = useState('');
  const [industry, setIndustry] = useState('');
  const [companySize, setCompanySize] = useState('');
  const [country, setCountry] = useState('');
  const [primaryObjective, setPrimaryObjective] = useState('');
  const [savingCompany, setSavingCompany] = useState(false);

  // Team
  const [members, setMembers] = useState<MemberResponseItem[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('analyst');
  const [inviting, setInviting] = useState(false);

  // Feedback
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const loadData = async () => {
    if (!activeCompany?.company_id) return;
    try {
      const details = await fetchCompanyDetails(activeCompany.company_id);
      setCompanyName(details.name);
      setIndustry(details.industry || 'SaaS / Technology');
      setCompanySize(details.company_size || '11-50 Employees');
      setCountry(details.country || 'United States');
      setPrimaryObjective(details.primary_objective || 'Revenue Growth & Margin Protection');
    } catch (err: any) {
      console.error('Failed to load company details:', err);
    }

    try {
      setLoadingMembers(true);
      const mems = await fetchCompanyMembers(activeCompany.company_id);
      setMembers(mems);
    } catch (err: any) {
      console.error('Failed to load members:', err);
    } finally {
      setLoadingMembers(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeCompany?.company_id]);

  const handleSaveCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany?.company_id) return;
    setSavingCompany(true);
    setStatusMessage(null);
    try {
      await updateCompanySettings(activeCompany.company_id, {
        name: companyName,
        industry,
        company_size: companySize,
        country,
        primary_objective: primaryObjective,
      });
      await refreshProfile();
      setStatusMessage({ text: 'Workspace profile settings updated successfully!', type: 'success' });
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Failed to save settings.', type: 'error' });
    } finally {
      setSavingCompany(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany?.company_id || !inviteEmail.trim()) return;
    setInviting(true);
    setStatusMessage(null);
    try {
      await inviteCompanyMember(activeCompany.company_id, inviteEmail.trim(), inviteRole);
      setInviteEmail('');
      setStatusMessage({ text: `Invitation sent to ${inviteEmail}!`, type: 'success' });
      const mems = await fetchCompanyMembers(activeCompany.company_id);
      setMembers(mems);
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Failed to invite member.', type: 'error' });
    } finally {
      setInviting(false);
    }
  };

  const handleRemoveMember = async (membershipId: string) => {
    if (!activeCompany?.company_id || !confirm('Are you sure you want to remove this member from the workspace?')) return;
    try {
      await removeCompanyMember(activeCompany.company_id, membershipId);
      setStatusMessage({ text: 'Member removed from workspace.', type: 'success' });
      const mems = await fetchCompanyMembers(activeCompany.company_id);
      setMembers(mems);
    } catch (err: any) {
      setStatusMessage({ text: err.message || 'Failed to remove member.', type: 'error' });
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-white tracking-tight sm:text-3xl">
          Workspace & Account Settings
        </h1>
        <p className="text-neutral-400 text-xs sm:text-sm">
          Manage your organization profile, team permissions, security configurations, and personal account.
        </p>
      </div>

      {statusMessage && (
        <div className={`p-4 rounded-xl flex items-center justify-between text-xs font-medium ${
          statusMessage.type === 'success' 
            ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300' 
            : 'bg-red-500/10 border border-red-500/20 text-red-300'
        }`}>
          <span>{statusMessage.text}</span>
          <button onClick={() => setStatusMessage(null)} className="text-neutral-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-neutral-800 gap-2">
        {[
          { id: 'company', label: 'Company Workspace', icon: Building2 },
          { id: 'team', label: 'Team & Roles', icon: Users },
          { id: 'profile', label: 'User Profile', icon: User },
          { id: 'security', label: 'Security & OAuth', icon: Shield },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`inline-flex items-center gap-2 px-4 py-3 text-xs sm:text-sm font-medium border-b-2 transition -mb-px cursor-pointer ${
                active
                  ? 'border-white text-white font-semibold'
                  : 'border-transparent text-neutral-400 hover:text-neutral-200 hover:border-neutral-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="bg-[#141414] border border-neutral-800 rounded-2xl p-6 sm:p-8 shadow-sm">
        {activeTab === 'company' && (
          <form onSubmit={handleSaveCompany} className="space-y-5 max-w-2xl">
            <div>
              <h3 className="text-base font-semibold text-white mb-1">Company Workspace Profile</h3>
              <p className="text-xs text-neutral-400">
                Organization parameters used to customize domain blueprints, risk thresholds, and executive summaries.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="settings-company-name">
                  Company Name
                </label>
                <input
                  id="settings-company-name"
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                  className="w-full px-3.5 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="settings-industry">
                    Industry Domain
                  </label>
                  <select
                    id="settings-industry"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
                  >
                    <option value="SaaS / Technology">SaaS / Technology</option>
                    <option value="E-Commerce & Retail">E-Commerce & Retail</option>
                    <option value="Healthcare & Life Sciences">Healthcare & Life Sciences</option>
                    <option value="Financial Services & Banking">Financial Services & Banking</option>
                    <option value="Manufacturing & Logistics">Manufacturing & Logistics</option>
                    <option value="Government & Public Sector">Government & Public Sector</option>
                    <option value="Education & Academics">Education & Academics</option>
                    <option value="Hospitality & Services">Hospitality & Services</option>
                    <option value="General Commercial">General Commercial</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="settings-size">
                    Organization Size
                  </label>
                  <select
                    id="settings-size"
                    value={companySize}
                    onChange={(e) => setCompanySize(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
                  >
                    <option value="1-10 Employees">1-10 Employees</option>
                    <option value="11-50 Employees">11-50 Employees</option>
                    <option value="51-200 Employees">51-200 Employees</option>
                    <option value="201-1000 Employees">201-1000 Employees</option>
                    <option value="1000+ Enterprise">1000+ Enterprise</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="settings-country">
                  Operating Country
                </label>
                <input
                  id="settings-country"
                  type="text"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="settings-objective">
                  Primary Strategic Objective
                </label>
                <select
                  id="settings-objective"
                  value={primaryObjective}
                  onChange={(e) => setPrimaryObjective(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
                >
                  <option value="Revenue Growth & Margin Protection">Revenue Growth & Margin Protection</option>
                  <option value="Profit Maximization & Cost Reduction">Profit Maximization & Cost Reduction</option>
                  <option value="Risk & Anomaly Mitigation">Risk & Anomaly Mitigation</option>
                  <option value="Operational Efficiency & Forecasting">Operational Efficiency & Forecasting</option>
                  <option value="Customer Retention & Segment Analytics">Customer Retention & Segment Analytics</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={savingCompany}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-neutral-200 text-black text-xs font-semibold shadow-sm transition disabled:opacity-50 cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              {savingCompany ? 'Saving...' : 'Save Workspace Settings'}
            </button>
          </form>
        )}

        {activeTab === 'team' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
              <div>
                <h3 className="text-base font-semibold text-white">Team Members & Access Control</h3>
                <p className="text-xs text-neutral-400">
                  Invite teammates to collaborate with Role-Based Access Control (RBAC).
                </p>
              </div>
            </div>

            {/* Invite Form */}
            <form onSubmit={handleInvite} className="p-4 rounded-xl bg-[#0A0A0A] border border-neutral-800 flex flex-col sm:flex-row items-center gap-3">
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                required
                className="w-full sm:flex-1 px-3.5 py-2 bg-[#141414] border border-neutral-800 rounded-xl text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 transition-colors"
              />
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="w-full sm:w-36 px-3 py-2 bg-[#141414] border border-neutral-800 rounded-xl text-xs text-white focus:outline-none focus:border-neutral-500 transition-colors"
              >
                <option value="admin">Admin</option>
                <option value="analyst">Analyst</option>
                <option value="viewer">Viewer</option>
              </select>
              <button
                type="submit"
                disabled={inviting}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-white hover:bg-neutral-200 text-black rounded-xl text-xs font-semibold transition disabled:opacity-50 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                {inviting ? 'Inviting...' : 'Invite'}
              </button>
            </form>

            {/* Members List */}
            <div className="divide-y divide-neutral-800 border border-neutral-800 rounded-xl overflow-hidden">
              {loadingMembers ? (
                <div className="p-6 text-center text-xs text-neutral-400">Loading team members...</div>
              ) : members.length === 0 ? (
                <div className="p-6 text-center text-xs text-neutral-500">No members found.</div>
              ) : (
                members.map((m) => (
                  <div key={m.membership_id} className="p-4 flex items-center justify-between bg-[#0A0A0A]">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-neutral-800 border border-neutral-700 flex items-center justify-center font-bold text-xs text-neutral-200">
                        {m.user_full_name ? m.user_full_name.charAt(0).toUpperCase() : 'U'}
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-white">{m.user_full_name}</div>
                        <div className="text-[11px] text-neutral-400">{m.user_email}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        m.role === 'owner'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : m.role === 'admin'
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          : m.role === 'analyst'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-neutral-800 text-neutral-300 border border-neutral-700'
                      }`}>
                        {m.role}
                      </span>

                      {m.role !== 'owner' && (
                        <button
                          onClick={() => handleRemoveMember(m.membership_id)}
                          className="p-1.5 text-neutral-500 hover:text-red-400 transition cursor-pointer"
                          title="Remove Member"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'profile' && (
          <div className="space-y-4 max-w-xl">
            <h3 className="text-base font-semibold text-white">Your Personal Account</h3>
            <div className="space-y-3 text-xs">
              <div className="p-3.5 rounded-xl bg-[#0A0A0A] border border-neutral-800">
                <span className="text-neutral-400 block mb-0.5">Full Name</span>
                <span className="text-white font-medium text-sm">{user?.full_name}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-[#0A0A0A] border border-neutral-800">
                <span className="text-neutral-400 block mb-0.5">Email Address</span>
                <span className="text-white font-medium text-sm">{user?.email}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-[#0A0A0A] border border-neutral-800">
                <span className="text-neutral-400 block mb-0.5">Authentication Provider</span>
                <span className="text-neutral-200 font-medium uppercase text-xs">{user?.auth_provider || 'local'}</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'security' && (
          <div className="space-y-4 max-w-xl">
            <h3 className="text-base font-semibold text-white">Security & Environment Configuration</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Google OAuth 2.0 PKCE and database encryption parameters are configured via server environment variables.
            </p>
            <div className="p-4 rounded-xl bg-[#0A0A0A] border border-neutral-800 font-mono text-xs space-y-2">
              <div className="text-neutral-400">Password Hashing: <span className="text-emerald-400 font-sans">PBKDF2-HMAC-SHA256 (Enforced)</span></div>
              <div className="text-neutral-400">JWT Token Security: <span className="text-emerald-400 font-sans">HS256 (24h Access / 7d Refresh)</span></div>
              <div className="text-neutral-400">Multi-Tenant Isolation: <span className="text-emerald-400 font-sans">SQL Foreign-Key Scoped</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
export default SettingsPage;
