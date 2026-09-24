import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Database, 
  TrendingUp, 
  ShieldAlert, 
  Target, 
  FileText, 
  CheckCircle2, 
  ArrowRight, 
  Building2, 
  LineChart,
  Lock
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export const LandingPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-[#0B0B0B] text-neutral-100 flex flex-col selection:bg-neutral-800 selection:text-white">
      {/* Navigation */}
      <header className="border-b border-neutral-800/80 bg-[#0E0E0E]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-neutral-900 border border-neutral-700/80 flex items-center justify-center text-white font-bold text-xs shadow-sm">
              DS
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-white">
                DataScope
              </span>
              <span className="ml-2 text-[10px] font-medium px-2 py-0.5 rounded bg-neutral-900 text-neutral-400 border border-neutral-800">
                Enterprise BI
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {user ? (
              <Link
                to="/overview"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white hover:bg-neutral-200 text-black text-xs font-semibold transition shadow-sm"
              >
                Go to Workspace <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-3.5 py-1.5 rounded-xl text-xs font-medium text-neutral-300 hover:text-white hover:bg-neutral-900 transition"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white hover:bg-neutral-200 text-black text-xs font-semibold transition shadow-sm"
                >
                  Create workspace <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="relative overflow-hidden pt-16 pb-20 lg:pt-24 lg:pb-28 border-b border-neutral-800/80">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-neutral-900 border border-neutral-800 text-xs font-medium text-neutral-300 mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>Multi-Tenant Business Intelligence & Decision Support</span>
            </div>

            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight">
              Deterministic Business Analytics & Executive Decision Intelligence
            </h1>

            <p className="mt-5 text-sm sm:text-base text-neutral-400 max-w-2xl mx-auto font-normal leading-relaxed">
              Connect SQL databases, REST endpoints, Google Sheets, or CSV files. Automatically evaluate revenue trajectories, detect margin erosion, calculate statistical anomalies, and generate audit-ready boardroom dossiers.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                to="/register"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-white hover:bg-neutral-200 text-black font-semibold text-sm transition shadow-sm"
              >
                Create company workspace <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[#141414] hover:bg-neutral-800 border border-neutral-800 text-neutral-200 font-medium text-sm transition"
              >
                Sign in to workspace
              </Link>
            </div>

            {/* Compliance Badges */}
            <div className="mt-10 flex flex-wrap items-center justify-center gap-6 text-[11px] text-neutral-400 font-medium">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Tenant Isolation</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Live Data Sync & Rollback</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>PKCE OAuth Support</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Executive PDF & DOCX Reports</span>
              </div>
            </div>
          </div>
        </section>

        {/* Feature Grid */}
        <section className="py-16 bg-[#0E0E0E] border-b border-neutral-800/80">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-left max-w-3xl mb-12">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-1">Architecture & Capabilities</h2>
              <p className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Complete Decision-Support Platform
              </p>
              <p className="mt-2 text-neutral-400 text-xs sm:text-sm">
                From live data ingestion to actionable prescriptive playbooks and boardroom dossiers.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {/* Card 1 */}
              <div className="p-5 rounded-xl bg-[#141414] border border-neutral-800 hover:border-neutral-700 transition">
                <div className="w-9 h-9 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center text-blue-400 mb-4">
                  <Database className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white mb-1.5">Live Data Connectors</h3>
                <p className="text-neutral-400 text-xs leading-relaxed">
                  Connect PostgreSQL, MySQL, REST APIs, and Google Sheets. Sync continuously with automated validation and rollback checkpoints.
                </p>
              </div>

              {/* Card 2 */}
              <div className="p-5 rounded-xl bg-[#141414] border border-neutral-800 hover:border-neutral-700 transition">
                <div className="w-9 h-9 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center text-emerald-400 mb-4">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white mb-1.5">Domain-Aware Trends</h3>
                <p className="text-neutral-400 text-xs leading-relaxed">
                  Dynamic multi-granularity time series, period-over-period variance, moving averages, and growth volatility analysis.
                </p>
              </div>

              {/* Card 3 */}
              <div className="p-5 rounded-xl bg-[#141414] border border-neutral-800 hover:border-neutral-700 transition">
                <div className="w-9 h-9 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center text-white mb-4">
                  <LineChart className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white mb-1.5">Predictive Forecasting</h3>
                <p className="text-neutral-400 text-xs leading-relaxed">
                  Baseline forecasting with 80% and 95% confidence intervals, seasonal decomposition, and scenario horizons.
                </p>
              </div>

              {/* Card 4 */}
              <div className="p-5 rounded-xl bg-[#141414] border border-neutral-800 hover:border-neutral-700 transition">
                <div className="w-9 h-9 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center text-amber-400 mb-4">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white mb-1.5">Risk & Anomaly Register</h3>
                <p className="text-neutral-400 text-xs leading-relaxed">
                  Identify margin compression, statistical outlier events, and customer/product concentration vulnerabilities.
                </p>
              </div>

              {/* Card 5 */}
              <div className="p-5 rounded-xl bg-[#141414] border border-neutral-800 hover:border-neutral-700 transition">
                <div className="w-9 h-9 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center text-white mb-4">
                  <Target className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white mb-1.5">Actionable Recommendations</h3>
                <p className="text-neutral-400 text-xs leading-relaxed">
                  Evidence-based playbooks complete with root causes, quantified financial impacts, and phased execution roadmaps.
                </p>
              </div>

              {/* Card 6 */}
              <div className="p-5 rounded-xl bg-[#141414] border border-neutral-800 hover:border-neutral-700 transition">
                <div className="w-9 h-9 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center text-rose-400 mb-4">
                  <FileText className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white mb-1.5">Executive Boardroom Reports</h3>
                <p className="text-neutral-400 text-xs leading-relaxed">
                  Generate comprehensive 8-page executive PDF dossiers and editable DOCX summaries with 6-question analytical frameworks.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Multi-Tenant Security Section */}
        <section className="py-16 bg-[#0B0B0B]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-[#141414] border border-neutral-800 rounded-2xl p-6 sm:p-10">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
                <div>
                  <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-neutral-900 border border-neutral-800 text-[11px] font-semibold text-neutral-300 mb-3">
                    <Building2 className="w-3.5 h-3.5" />
                    <span>Multi-Tenancy & Governance</span>
                  </div>
                  <h2 className="text-xl sm:text-3xl font-bold text-white tracking-tight">
                    Strict Workspace Isolation & Role-Based Access
                  </h2>
                  <p className="mt-3 text-neutral-400 text-xs sm:text-sm leading-relaxed">
                    DataScope enforces database-level and API-level tenant isolation. Team members can be provisioned with granular roles (Owner, Admin, Analyst, Viewer).
                  </p>
                  <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-[#0A0A0A] border border-neutral-800 text-xs text-neutral-300">
                      <span className="text-white font-semibold block mb-0.5">Owner / Admin</span>
                      Workspace management & dataset governance
                    </div>
                    <div className="p-3 rounded-lg bg-[#0A0A0A] border border-neutral-800 text-xs text-neutral-300">
                      <span className="text-white font-semibold block mb-0.5">Analyst / Viewer</span>
                      Live data inspection & executive reporting
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-xl bg-[#0A0A0A] border border-neutral-800 flex flex-col gap-3 font-mono text-[11px]">
                  <div className="flex items-center justify-between pb-2 border-b border-neutral-800 text-neutral-400">
                    <span className="text-white font-semibold flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5 text-blue-400" /> Security Check
                    </span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Enforced
                    </span>
                  </div>
                  <div className="text-neutral-400">
                    <span className="text-blue-400">GET</span> /api/datasets
                    <div className="text-[10px] text-neutral-500 mt-0.5">Auth: Bearer JWT | Scope: X-Company-Id</div>
                  </div>
                  <div className="text-neutral-400">
                    <span className="text-emerald-400">WS</span> /api/ws/:company_id
                    <div className="text-[10px] text-neutral-500 mt-0.5">Real-time update stream for active tenant</div>
                  </div>
                  <div className="p-2 rounded bg-neutral-900 border border-neutral-800 text-neutral-300 text-[10px]">
                    SQL Policy: <code className="text-emerald-400">WHERE company_id = :active_company_id</code>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-800/80 py-6 bg-[#0A0A0A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-neutral-500">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-neutral-800 border border-neutral-700 flex items-center justify-center text-white text-[10px] font-bold">
              DS
            </div>
            <span className="font-semibold text-neutral-300">DataScope</span>
            <span>— Enterprise Decision Intelligence</span>
          </div>
          <div>© {new Date().getFullYear()} DataScope Platform. All rights reserved.</div>
        </div>
      </footer>
    </div>
  );
};
export default LandingPage;
