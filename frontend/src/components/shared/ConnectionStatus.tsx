import { useEffect, useState } from "react"
import { CheckCircle2, XCircle, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { checkBackendHealth } from "@/lib/api"

type Status = "loading" | "online" | "offline"

export function ConnectionStatus() {
  const [status, setStatus] = useState<Status>("loading")

  useEffect(() => {
    let active = true
    checkBackendHealth()
      .then(() => active && setStatus("online"))
      .catch(() => active && setStatus("offline"))
    return () => {
      active = false
    }
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Backend Connection
        </CardTitle>
      </CardHeader>
      <CardContent className="flex items-center gap-2 text-sm">
        {status === "loading" && (
          <>
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            <span className="text-muted-foreground">
              Checking backend status…
            </span>
          </>
        )}
        {status === "online" && (
          <>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <span>Connected to backend API</span>
          </>
        )}
        {status === "offline" && (
          <>
            <XCircle className="h-4 w-4 text-destructive" />
            <span>Backend unreachable. Is Uvicorn running on port 8000?</span>
          </>
        )}
      </CardContent>
    </Card>
  )
}
