import { useEffect, useState } from "react"
import { AlertCircle, ArrowRight, Database, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"

interface InitializationScreenProps {
  onRetry?: () => void
}

export function InitializationScreen({ onRetry }: InitializationScreenProps) {
  const { initError, retryInit, logout } = useAuth()
  const [stageIndex, setStageIndex] = useState(0)
  const [hasDelayed, setHasDelayed] = useState(false)

  const stages = [
    "Verifying authentication session...",
    "Connecting to DataScope platform...",
    "Loading workspace environment...",
    "Synchronizing analytics engines...",
  ]

  useEffect(() => {
    const stageTimer = setInterval(() => {
      setStageIndex((prev) => (prev < stages.length - 1 ? prev + 1 : prev))
    }, 1000)

    const delayTimer = setTimeout(() => {
      setHasDelayed(true)
    }, 3200)

    return () => {
      clearInterval(stageTimer)
      clearTimeout(delayTimer)
    }
  }, [])

  const handleRetry = async () => {
    setHasDelayed(false)
    setStageIndex(0)
    if (onRetry) {
      onRetry()
    } else {
      await retryInit()
    }
  }

  const handleResetSession = () => {
    logout()
    window.location.href = "/login"
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background p-4 text-foreground">
      <div className="relative w-full max-w-md p-8 rounded-2xl border border-border bg-card shadow-lg flex flex-col items-center text-center">
        {/* Brand Icon */}
        <div className="relative mb-6">
          <div className="w-12 h-12 rounded-xl bg-neutral-900 border border-neutral-700/80 flex items-center justify-center text-white shadow-sm">
            <Database className="w-6 h-6 text-foreground" />
          </div>
        </div>

        {/* Brand Title */}
        <h2 className="text-lg font-bold tracking-tight text-foreground mb-1">
          DataScope Platform
        </h2>

        {/* Dynamic Stage Message or Error */}
        {initError ? (
          <div className="my-4 p-3.5 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs flex items-start gap-2.5 text-left w-full">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
            <div>
              <p className="font-semibold text-red-200">Initialization Notice</p>
              <p className="mt-0.5 opacity-90">{initError}</p>
            </div>
          </div>
        ) : (
          <div className="my-5 w-full flex flex-col items-center">
            <div className="flex items-center gap-2.5 text-xs text-muted-foreground">
              <div className="w-3.5 h-3.5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="font-medium tracking-wide transition-all duration-300">
                {stages[stageIndex]}
              </span>
            </div>

            {/* Progress line */}
            <div className="w-full max-w-[220px] h-1 bg-muted rounded-full mt-4 overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-500 rounded-full"
                style={{ width: `${Math.min(100, (stageIndex + 1) * 25)}%` }}
              />
            </div>
          </div>
        )}

        {/* Delayed Assistance / Retry Controls */}
        {(hasDelayed || initError) && (
          <div className="mt-4 pt-4 border-t border-border w-full flex flex-col gap-2.5">
            <p className="text-xs text-muted-foreground mb-1">
              {hasDelayed && !initError
                ? "Initialization is taking longer than expected. You can retry connection or log in again."
                : "Unable to complete workspace initialization."}
            </p>

            <div className="grid grid-cols-2 gap-2 w-full">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetry}
                className="gap-1.5 text-xs cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retry
              </Button>

              <Button
                variant="default"
                size="sm"
                onClick={handleResetSession}
                className="gap-1.5 text-xs font-medium cursor-pointer"
              >
                Go to Login
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        )}

        <div className="mt-6 text-[11px] text-muted-foreground">
          Enterprise Business Intelligence Platform
        </div>
      </div>
    </div>
  )
}
