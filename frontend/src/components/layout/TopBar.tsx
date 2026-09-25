import { useCallback, useEffect, useState } from "react"
import { Menu, LogOut, User, Wifi, WifiOff, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { SidebarNav } from "@/components/layout/Sidebar"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { ActiveDatasetBadge } from "@/components/dataset/ActiveDatasetBadge"
import { CompanySwitcher } from "@/components/workspace/CompanySwitcher"
import { useAuth } from "@/context/AuthContext"
import { checkBackendHealth } from "@/lib/api"

export function TopBar() {
  const [open, setOpen] = useState(false)
  const { user, logout, isWsConnected } = useAuth()
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking")

  const verifyBackendStatus = useCallback(async () => {
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      setBackendStatus("offline")
      return
    }
    try {
      await checkBackendHealth()
      setBackendStatus("online")
    } catch {
      setBackendStatus("offline")
    }
  }, [])

  useEffect(() => {
    verifyBackendStatus()

    const handleOnline = () => {
      setBackendStatus("checking")
      verifyBackendStatus()
    }
    const handleOffline = () => setBackendStatus("offline")
    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        verifyBackendStatus()
      }
    }

    window.addEventListener("online", handleOnline)
    window.addEventListener("offline", handleOffline)
    document.addEventListener("visibilitychange", handleVisibility)

    const interval = setInterval(verifyBackendStatus, 30000)

    return () => {
      window.removeEventListener("online", handleOnline)
      window.removeEventListener("offline", handleOffline)
      document.removeEventListener("visibilitychange", handleVisibility)
      clearInterval(interval)
    }
  }, [verifyBackendStatus])

  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-4 md:px-6 z-20">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 md:hidden">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0">
              <div className="flex h-16 items-center px-6 gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-neutral-900 border border-neutral-700/80 flex items-center justify-center text-white font-bold text-xs shadow-sm">
                  DS
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-bold tracking-tight text-foreground leading-none">DataScope</span>
                  <span className="text-[10px] text-muted-foreground font-medium mt-0.5">Enterprise BI</span>
                </div>
              </div>
              <SidebarNav onNavigate={() => setOpen(false)} />
            </SheetContent>
          </Sheet>
        </div>

        {/* Multi-Tenant Workspace Selector */}
        <CompanySwitcher />

        <div className="hidden lg:block">
          <ActiveDatasetBadge />
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend & Real-time Connectivity indicator */}
        <div
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium transition-colors"
          style={{
            borderColor:
              backendStatus === "online"
                ? "rgba(16, 185, 129, 0.3)"
                : backendStatus === "checking"
                ? "rgba(245, 158, 11, 0.3)"
                : "rgba(239, 68, 68, 0.3)",
            backgroundColor:
              backendStatus === "online"
                ? "rgba(16, 185, 129, 0.08)"
                : backendStatus === "checking"
                ? "rgba(245, 158, 11, 0.08)"
                : "rgba(239, 68, 68, 0.08)",
            color:
              backendStatus === "online"
                ? "#10B981"
                : backendStatus === "checking"
                ? "#F59E0B"
                : "#EF4444",
          }}
          title={
            backendStatus === "online"
              ? isWsConnected
                ? "Connected to backend API (Real-time active)"
                : "Connected to backend API"
              : backendStatus === "checking"
              ? "Checking backend connectivity..."
              : "Backend unreachable"
          }
        >
          {backendStatus === "checking" && <Loader2 className="w-3 h-3 animate-spin" />}
          {backendStatus === "online" && <Wifi className="w-3 h-3" />}
          {backendStatus === "offline" && <WifiOff className="w-3 h-3" />}
          <span>
            {backendStatus === "checking" ? "Checking" : backendStatus === "online" ? "Online" : "Offline"}
          </span>
        </div>

        <ThemeToggle />

        {/* User Profile / Logout */}
        {user ? (
          <div className="flex items-center gap-2 pl-2 border-l border-border">
            <div className="w-8 h-8 rounded-full bg-secondary border border-border flex items-center justify-center text-foreground font-bold text-xs">
              {user.full_name ? user.full_name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
            </div>
            <div className="hidden xl:block text-left">
              <div className="text-xs font-semibold text-foreground truncate max-w-[120px]">{user.full_name}</div>
              <div className="text-[10px] text-muted-foreground truncate max-w-[120px]">{user.email}</div>
            </div>
            <button
              type="button"
              onClick={logout}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-destructive/10 transition-colors cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : null}
      </div>
    </header>
  )
}
