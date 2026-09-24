import { useState, useRef, useEffect } from "react"
import { Building2, ChevronDown, Check, Plus, Users } from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import { WorkspaceMembersModal } from "./WorkspaceMembersModal"


export function CompanySwitcher() {
  const { companies, activeCompany, switchCompany, createCompany } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [newCompanyName, setNewCompanyName] = useState("")
  const [showMembersModal, setShowMembersModal] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setIsCreating(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newCompanyName.trim()) return
    await createCompany(newCompanyName.trim())
    setNewCompanyName("")
    setIsCreating(false)
    setIsOpen(false)
  }

  if (!activeCompany) return null

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-secondary hover:bg-secondary/80 border border-border text-xs font-medium text-foreground transition-colors shadow-xs cursor-pointer"
      >
        <Building2 className="w-3.5 h-3.5 text-muted-foreground" />
        <span className="max-w-[130px] truncate font-semibold">{activeCompany.company_name}</span>
        <span className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground text-[10px] uppercase font-bold tracking-wider">
          {activeCompany.role}
        </span>
        <ChevronDown className="w-3 h-3 text-muted-foreground" />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-64 rounded-xl bg-popover border border-border shadow-lg p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="px-2 py-1.5 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            Switch Workspace
          </div>

          <div className="space-y-1 my-1">
            {companies.map((c) => (
              <button
                key={c.company_id}
                type="button"
                onClick={() => {
                  switchCompany(c.company_id)
                  setIsOpen(false)
                }}
                className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  c.company_id === activeCompany.company_id
                    ? "bg-secondary text-foreground border border-border font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <Building2 className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{c.company_name}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] uppercase font-bold text-muted-foreground">{c.role}</span>
                  {c.company_id === activeCompany.company_id && <Check className="w-3.5 h-3.5 text-foreground" />}
                </div>
              </button>
            ))}
          </div>

          <div className="border-t border-border pt-1 mt-1 space-y-1">
            {/* Manage Members */}
            <button
              type="button"
              onClick={() => {
                setShowMembersModal(true)
                setIsOpen(false)
              }}
              className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors cursor-pointer"
            >
              <Users className="w-3.5 h-3.5 text-muted-foreground" />
              <span>Workspace Members & Roles</span>
            </button>

            {/* Create New Workspace */}
            {!isCreating ? (
              <button
                type="button"
                onClick={() => setIsCreating(true)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs text-foreground hover:bg-secondary/60 transition-colors cursor-pointer font-medium"
              >
                <Plus className="w-3.5 h-3.5 text-muted-foreground" />
                <span>Create New Workspace</span>
              </button>
            ) : (
              <form onSubmit={handleCreateSubmit} className="p-1 space-y-2">
                <input
                  type="text"
                  autoFocus
                  placeholder="New company name..."
                  value={newCompanyName}
                  onChange={(e) => setNewCompanyName(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-background border border-input rounded-lg text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                />
                <div className="flex gap-1.5">
                  <button
                    type="submit"
                    className="flex-1 py-1 bg-primary hover:bg-primary/90 text-primary-foreground text-[11px] font-semibold rounded-md transition-colors cursor-pointer"
                  >
                    Create
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsCreating(false)}
                    className="px-2 py-1 bg-secondary hover:bg-secondary/80 text-muted-foreground text-[11px] rounded-md transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {showMembersModal && (
        <WorkspaceMembersModal
          companyId={activeCompany.company_id}
          companyName={activeCompany.company_name}
          userRole={activeCompany.role}
          onClose={() => setShowMembersModal(false)}
        />
      )}
    </div>
  )
}
