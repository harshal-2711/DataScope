import { NavLink } from "react-router-dom"
import {
  LayoutDashboard,
  Database,
  Search,
  TrendingUp,
  LineChart,
  ShieldAlert,
  Target,
  Lightbulb,
  FileText,
  TableProperties,
  Server,
  Settings,
} from "lucide-react"
import { navItems } from "@/config/navigation"
import { cn } from "@/lib/utils"

const icons: Record<string, React.ComponentType<{ className?: string }>> = {
  "/": LayoutDashboard,
  "/overview": LayoutDashboard,
  "/dataset": Database,
  "/connect-data": Server,
  "/live-data": Server,
  "/data-management": TableProperties,
  "/explore": Search,
  "/trends": TrendingUp,
  "/forecast": LineChart,
  "/risks": ShieldAlert,
  "/competition": Target,
  "/recommendations": Lightbulb,
  "/reports": FileText,
  "/settings": Settings,
}

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1 px-3">
      {navItems.map((item) => {
        const Icon = icons[item.path] || LayoutDashboard
        return (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-semibold transition-colors",
                isActive
                  ? "bg-neutral-800 text-white shadow-sm"
                  : "text-muted-foreground hover:bg-neutral-900 hover:text-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        )
      })}
    </nav>
  )
}

export function Sidebar() {
  return (
    <aside className="hidden md:flex md:w-64 md:flex-col md:border-r md:bg-card">
      <div className="flex h-16 items-center px-6 gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-neutral-900 border border-neutral-700/80 flex items-center justify-center text-white font-bold text-xs shadow-sm">
          DS
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-tight text-foreground leading-none">
            DataScope
          </span>
          <span className="text-[10px] text-muted-foreground font-medium mt-0.5">
            Enterprise BI
          </span>
        </div>
      </div>
      <SidebarNav />
    </aside>
  )
}
