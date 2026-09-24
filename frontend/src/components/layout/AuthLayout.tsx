import React from "react"
import { ShieldCheck, BarChart3, ShieldAlert, FileText, CheckCircle2 } from "lucide-react"

interface AuthLayoutProps {
  children: React.ReactNode
  title: string
  subtitle: string
  badgeText?: string
}

export function AuthLayout({ children, title, subtitle, badgeText = "Enterprise Decision Intelligence" }: AuthLayoutProps) {
  return (
    <div className="min-h-screen w-full bg-[#0B0B0B] text-neutral-100 flex flex-col lg:flex-row selection:bg-neutral-800 selection:text-white">
      {/* Left Column: Brand Identity & Enterprise Value Proposition */}
      <div className="lg:w-1/2 flex flex-col justify-between p-8 sm:p-12 lg:p-16 border-b lg:border-b-0 lg:border-r border-neutral-800/80 bg-[#0E0E0E] relative overflow-hidden">
        {/* Subtle grid pattern background */}
        <div 
          className="absolute inset-0 opacity-[0.03] pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(#ffffff 1px, transparent 1px)`,
            backgroundSize: "24px 24px"
          }}
        />

        {/* Top: Brand Header */}
        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-neutral-700/80 flex items-center justify-center text-white font-bold text-base shadow-sm">
              <span className="bg-gradient-to-br from-white to-neutral-400 bg-clip-text text-transparent">DS</span>
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white block">DataScope</span>
              <span className="text-[11px] text-neutral-400 font-medium tracking-wide">Enterprise Intelligence Platform</span>
            </div>
          </div>

          <div className="mt-4 inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-neutral-900/90 border border-neutral-800 text-[11px] font-medium text-neutral-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>{badgeText}</span>
          </div>
        </div>

        {/* Middle: Business Intelligence Highlights & Metrics */}
        <div className="my-10 lg:my-0 relative z-10 max-w-lg">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white leading-snug mb-4">
            Deterministic business analytics and real-time decision intelligence.
          </h2>
          <p className="text-sm text-neutral-400 leading-relaxed mb-8">
            DataScope unifies multi-source company datasets, analyzes real-time revenue and margin trajectories, detects operational anomalies, and compiles audit-ready decision reports for leadership teams.
          </p>

          {/* Value Proposition Cards */}
          <div className="space-y-3">
            <div className="p-3.5 rounded-xl bg-neutral-900/80 border border-neutral-800/80 flex items-start gap-3.5">
              <div className="p-2 rounded-lg bg-neutral-800 text-blue-400 shrink-0 mt-0.5">
                <BarChart3 className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Universal Performance Modeling</div>
                <div className="text-[11px] text-neutral-400 mt-0.5">
                  Instant revenue, margin, cohort, and segment decomposition across any dataset.
                </div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-neutral-900/80 border border-neutral-800/80 flex items-start gap-3.5">
              <div className="p-2 rounded-lg bg-neutral-800 text-amber-400 shrink-0 mt-0.5">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Continuous Risk & Anomaly Surveillance</div>
                <div className="text-[11px] text-neutral-400 mt-0.5">
                  Automated statistical anomaly detection, concentration risks, and margin erosion triggers.
                </div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-neutral-900/80 border border-neutral-800/80 flex items-start gap-3.5">
              <div className="p-2 rounded-lg bg-neutral-800 text-emerald-400 shrink-0 mt-0.5">
                <FileText className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Board-Ready Decision Dossiers</div>
                <div className="text-[11px] text-neutral-400 mt-0.5">
                  6-question evidence-backed executive reports exportable to PDF and DOCX.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom: Enterprise Compliance Badges */}
        <div className="relative z-10 pt-6 border-t border-neutral-800/60 flex flex-wrap items-center gap-6 text-[11px] text-neutral-400">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-neutral-300" />
            <span>Multi-Tenant Data Isolation</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-neutral-300" />
            <span>Role-Based Access Control</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-neutral-300" />
            <span>Encrypted Data Stores</span>
          </div>
        </div>
      </div>

      {/* Right Column: Authentication Form Container */}
      <div className="lg:w-1/2 flex items-center justify-center p-6 sm:p-12 lg:p-16 bg-[#0B0B0B] relative z-10">
        <div className="w-full max-w-md">
          {/* Form Header */}
          <div className="mb-6 text-left">
            <h1 className="text-2xl font-bold tracking-tight text-white">{title}</h1>
            <p className="text-xs sm:text-sm text-neutral-400 mt-1.5 leading-relaxed">{subtitle}</p>
          </div>

          {/* Form Content */}
          <div className="bg-[#141414] border border-neutral-800/90 rounded-2xl p-6 sm:p-8 shadow-xl">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
