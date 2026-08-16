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
} from "lucide-react"
import { navItems } from "@/config/navigation"
import { cn } from "@/lib/utils"

const icons: Record<string, React.ComponentType<{ className?: string }>> = {
  "/": LayoutDashboard,
  "/dataset": Database,
  "/explore": Search,
  "/trends": TrendingUp,
  "/forecast": LineChart,
  "/risks": ShieldAlert,
  "/competition": Target,
  "/recommendations": Lightbulb,
  "/reports": FileText,
}

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1 px-3">
      {navItems.map((item) => {
        const Icon = icons[item.path]
        return (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
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
      <div className="flex h-16 items-center px-6">
        <span className="text-lg font-semibold tracking-tight">
          DataScope
        </span>
      </div>
      <SidebarNav />
    </aside>
  )
}
