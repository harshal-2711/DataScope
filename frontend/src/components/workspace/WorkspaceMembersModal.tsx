import { useState, useEffect } from "react"
import { Users, X, UserPlus, Trash2, Mail, AlertCircle, CheckCircle } from "lucide-react"
import { fetchCompanyMembers, inviteCompanyMember, removeCompanyMember } from "@/lib/authApi"

import type { MemberResponseItem } from "@/types/auth"

interface WorkspaceMembersModalProps {
  companyId: string
  companyName: string
  userRole: string
  onClose: () => void
}

export function WorkspaceMembersModal({ companyId, companyName, userRole, onClose }: WorkspaceMembersModalProps) {
  const [members, setMembers] = useState<MemberResponseItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole] = useState("analyst")
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [createdInviteUrl, setCreatedInviteUrl] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const canManage = userRole === "owner" || userRole === "admin"

  const loadMembers = async () => {
    setIsLoading(true)
    try {
      const data = await fetchCompanyMembers(companyId)
      setMembers(data)
    } catch (err: any) {
      setError(err.message || "Failed to load workspace members.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadMembers()
  }, [companyId])

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inviteEmail.trim()) return
    setError(null)
    setSuccess(null)
    setIsSubmitting(true)
    try {
      const res = await inviteCompanyMember(companyId, inviteEmail.trim(), inviteRole)
      setSuccess(`Invitation created for ${inviteEmail}.`)
      if (res.invitation_token) {
        const fullUrl = `${window.location.origin}/invite/accept?token=${res.invitation_token}`
        setCreatedInviteUrl(fullUrl)
      } else {
        setCreatedInviteUrl(null)
      }
      setInviteEmail("")
      await loadMembers()
    } catch (err: any) {
      setError(err.message || "Failed to invite member.")
      setCreatedInviteUrl(null)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRemove = async (membershipId: string) => {
    if (!confirm("Are you sure you want to remove this member or cancel this invitation?")) return
    try {
      await removeCompanyMember(companyId, membershipId)
      await loadMembers()
    } catch (err: any) {
      setError(err.message || "Failed to remove member.")
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl max-w-xl w-full p-6 shadow-xl relative animate-in fade-in zoom-in-95 duration-150">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-secondary transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="p-2.5 rounded-lg bg-secondary text-foreground">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-foreground">Workspace Members & Permissions</h2>
            <p className="text-xs text-muted-foreground">Managing team access for {companyName}</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {createdInviteUrl && (
          <div className="mb-4 p-3.5 rounded-lg bg-secondary/50 border border-border space-y-2">
            <div className="text-[11px] font-semibold text-foreground flex items-center justify-between">
              <span>Secure Setup Link (for invited worker):</span>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(createdInviteUrl)
                  setCopied(true)
                  setTimeout(() => setCopied(false), 2500)
                }}
                className="px-2 py-0.5 bg-primary text-primary-foreground rounded text-[10px] font-medium hover:bg-primary/90 transition-colors cursor-pointer"
              >
                {copied ? "Copied!" : "Copy Link"}
              </button>
            </div>
            <div className="text-[11px] text-muted-foreground font-mono truncate select-all bg-background/60 p-2 rounded border border-border">
              {createdInviteUrl}
            </div>
            <div className="text-[10px] text-muted-foreground leading-relaxed">
              Share this single-use link with the worker. They will create their own private password to join this workspace.
            </div>
          </div>
        )}

        {/* Invite Form (Admins/Owners only) */}
        {canManage && (
          <form onSubmit={handleInvite} className="mb-6 p-4 rounded-lg bg-secondary/30 border border-border space-y-3">
            <div className="text-xs font-semibold text-foreground">Invite New Team Member</div>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Mail className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  placeholder="colleague@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-background border border-input rounded-lg text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>

              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="px-3 py-2 bg-background border border-input rounded-lg text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="analyst">Analyst (Upload & Edit)</option>
                {userRole === "owner" && <option value="admin">Admin (Manage Workspace)</option>}
                <option value="viewer">Viewer (Read-Only)</option>
              </select>

              <button
                type="submit"
                disabled={isSubmitting}
                className="px-3.5 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Invite</span>
              </button>
            </div>
          </form>
        )}

        {/* Members List */}
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {isLoading ? (
            <div className="text-center py-8 text-xs text-muted-foreground">Loading workspace members...</div>
          ) : members.length === 0 ? (
            <div className="text-center py-8 text-xs text-muted-foreground">No members found.</div>
          ) : (
            members.map((m) => (
              <div
                key={m.membership_id}
                className="flex items-center justify-between p-3 rounded-lg bg-secondary/20 border border-border hover:border-border/80 transition-colors"
              >
                <div>
                  <div className="text-xs font-medium text-foreground flex items-center gap-2">
                    <span>{m.user_full_name || m.user_email}</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-secondary text-secondary-foreground border border-border">
                      {m.role}
                    </span>
                    {m.status === "pending" && (
                      <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-semibold">
                        Pending
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-muted-foreground mt-0.5">{m.user_email}</div>
                </div>

                <div className="flex items-center gap-2">
                  {m.status === "pending" && m.invitation_token && (
                    <button
                      type="button"
                      onClick={() => {
                        const url = `${window.location.origin}/invite/accept?token=${m.invitation_token}`
                        navigator.clipboard.writeText(url)
                        alert("Setup link copied to clipboard!")
                      }}
                      className="px-2 py-1 text-[10px] text-primary hover:underline font-medium cursor-pointer"
                      title="Copy setup link"
                    >
                      Copy Link
                    </button>
                  )}
                  {canManage && m.role !== "owner" && (
                    <button
                      type="button"
                      onClick={() => handleRemove(m.membership_id)}
                      className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors cursor-pointer"
                      title={m.status === "pending" ? "Revoke invitation" : "Remove member"}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="flex justify-end mt-6">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
