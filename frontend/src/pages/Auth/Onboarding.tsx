import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, ArrowRight, Target, Globe, Users, Briefcase, AlertCircle } from 'lucide-react';
import { completeOnboarding } from '@/lib/authApi';
import { useAuth } from '@/context/AuthContext';

export const OnboardingPage: React.FC = () => {
  const { currentCompany, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [companyName, setCompanyName] = useState(currentCompany?.name || '');
  const [industry, setIndustry] = useState('SaaS / Technology');
  const [companySize, setCompanySize] = useState('11-50 Employees');
  const [country, setCountry] = useState('United States');
  const [primaryObjective, setPrimaryObjective] = useState('Revenue Growth & Margin Protection');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await completeOnboarding({
        company_name: companyName.trim() || undefined,
        industry,
        company_size: companySize,
        country,
        primary_objective: primaryObjective,
      });
      await refreshUser();
      navigate('/overview');
    } catch (err: any) {
      setError(err.message || 'Failed to complete workspace onboarding.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0B0B] text-neutral-100 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 selection:bg-neutral-800 selection:text-white">
      <div className="sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-neutral-900 border border-neutral-700/80 flex items-center justify-center text-white font-bold text-xs shadow-sm">
            DS
          </div>
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
            Workspace Configuration
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
          Configure your company workspace
        </h1>
        <p className="mt-1.5 text-xs sm:text-sm text-neutral-400">
          DataScope tailors analytical domain blueprints and risk thresholds to your operating model.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-[#141414] border border-neutral-800 rounded-2xl p-6 sm:p-8 shadow-xl">
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Company Name */}
            <div>
              <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="onboarding-company">
                Company / Organization Name
              </label>
              <div className="relative">
                <Building2 className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  id="onboarding-company"
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g. Acme Corporation"
                  className="w-full pl-10 pr-4 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
                />
              </div>
            </div>

            {/* Industry & Size Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="onboarding-industry">
                  Industry / Domain
                </label>
                <div className="relative">
                  <Briefcase className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <select
                    id="onboarding-industry"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
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
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="onboarding-size">
                  Organization Size
                </label>
                <div className="relative">
                  <Users className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <select
                    id="onboarding-size"
                    value={companySize}
                    onChange={(e) => setCompanySize(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
                  >
                    <option value="1-10 Employees">1-10 Employees</option>
                    <option value="11-50 Employees">11-50 Employees</option>
                    <option value="51-200 Employees">51-200 Employees</option>
                    <option value="201-1000 Employees">201-1000 Employees</option>
                    <option value="1000+ Enterprise">1000+ Enterprise</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Country */}
            <div>
              <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="onboarding-country">
                Primary Operating Country
              </label>
              <div className="relative">
                <Globe className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <select
                  id="onboarding-country"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
                >
                  <option value="United States">United States</option>
                  <option value="United Kingdom">United Kingdom</option>
                  <option value="Canada">Canada</option>
                  <option value="Germany">Germany</option>
                  <option value="France">France</option>
                  <option value="India">India</option>
                  <option value="Singapore">Singapore</option>
                  <option value="Australia">Australia</option>
                  <option value="Global / International">Global / International</option>
                </select>
              </div>
            </div>

            {/* Primary Objective */}
            <div>
              <label className="block text-xs font-medium text-neutral-300 mb-1.5" htmlFor="onboarding-objective">
                Primary Analytical Objective
              </label>
              <div className="relative">
                <Target className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <select
                  id="onboarding-objective"
                  value={primaryObjective}
                  onChange={(e) => setPrimaryObjective(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-[#0A0A0A] border border-neutral-800 rounded-xl text-sm text-white focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500 transition-colors"
                >
                  <option value="Revenue Growth & Margin Protection">Revenue Growth & Margin Protection</option>
                  <option value="Operational Anomaly & Risk Detection">Operational Anomaly & Risk Detection</option>
                  <option value="Customer Retention & Cohort Analytics">Customer Retention & Cohort Analytics</option>
                  <option value="Competitive Benchmarking & Pricing Strategy">Competitive Benchmarking & Pricing Strategy</option>
                  <option value="Executive Dossiers & Audit-Ready Reporting">Executive Dossiers & Audit-Ready Reporting</option>
                </select>
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
                  <span>Save workspace profile</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default OnboardingPage;
