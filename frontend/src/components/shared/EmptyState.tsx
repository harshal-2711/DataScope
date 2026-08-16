import type { LucideIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
}

export function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <div className="rounded-full bg-muted p-3">
          <Icon className="h-6 w-6 text-muted-foreground" />
        </div>
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="max-w-sm text-sm text-muted-foreground">
          {description}
        </p>
      </CardContent>
    </Card>
  )
}
