import { useState } from "react"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { SidebarNav } from "@/components/layout/Sidebar"
import { ThemeToggle } from "@/components/theme/ThemeToggle"

export function TopBar() {
  const [open, setOpen] = useState(false)

  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-4 md:px-6">
      <div className="flex items-center gap-2 md:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <div className="flex h-16 items-center px-6">
              <span className="text-lg font-semibold tracking-tight">
                DataScope
              </span>
            </div>
            <SidebarNav onNavigate={() => setOpen(false)} />
          </SheetContent>
        </Sheet>
        <span className="font-semibold">DataScope</span>
      </div>
      <div className="hidden md:block" />
      <ThemeToggle />
    </header>
  )
}
