"use client"

import { useState, useEffect } from "react"
import { HitlHeader } from "@/components/hitl/hitl-header"
import { QueueList } from "@/components/hitl/queue-list"
import { EscalationCard } from "@/components/hitl/escalation-card"
import type { EscalationItem } from "@/components/hitl/types"
import { toast } from "sonner"
import { CheckCircle2, XCircle, AlertCircle, Loader2 } from "lucide-react"
import { apiClient } from "@/lib/api"
import { formatDistanceToNow } from "date-fns"

interface BackendEscalation {
  request_id: string
  session_id: string
  escalation_reason: string
  risk_score: number
  created_at: string
  review_url?: string | null
  status?: string
  human_decision?: string | null
  human_feedback?: string | null
  resolved_at?: string | null
}

export default function HitlPage() {
  const [items, setItems] = useState<EscalationItem[]>([])
  const [selectedId, setSelectedId] = useState<string>("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch escalations from backend
  useEffect(() => {
    const fetchEscalations = async () => {
      try {
        setIsLoading(true)
        setError(null)
        // Fetch all escalations including resolved ones
        const backendEscalations: BackendEscalation[] = await apiClient.getAllEscalations(true, true)
        
        // Transform backend response to frontend format
        const transformedEscalations: EscalationItem[] = await Promise.all(
          backendEscalations.map(async (esc) => {
            // Try to fetch session details to get week number
            let week = "Unknown"
            let sessionDetails = null
            try {
              sessionDetails = await apiClient.getSession(esc.session_id, true)
              if (sessionDetails?.week_number) {
                week = `Week ${sessionDetails.week_number}`
              }
            } catch (e) {
              console.debug(`Could not fetch session details for ${esc.session_id}:`, e)
            }

            // Format timestamp
            const createdAt = new Date(esc.created_at)
            const timestamp = formatDistanceToNow(createdAt, { addSuffix: true })
            
            // Determine status
            const status = (esc.status || "pending") as "pending" | "approved" | "rejected" | "modified"

            return {
              id: esc.request_id,
              riskScore: esc.risk_score,
              timestamp,
              reason: esc.escalation_reason,
              session: esc.session_id, // Full session ID for linking
              week,
              primaryAgent: "Governance", // Default, could be enhanced with more data
              summary: esc.escalation_reason || "Escalation requires human review",
              agentOutputs: [], // Could be populated from session analysis result if needed
              status,
              humanDecision: esc.human_decision || undefined,
              humanFeedback: esc.human_feedback || undefined,
              resolvedAt: esc.resolved_at || undefined,
            }
          })
        )

        setItems(transformedEscalations)
        if (transformedEscalations.length > 0) {
          // Select first pending escalation, or first item if none pending
          const firstPending = transformedEscalations.find(item => item.status === "pending")
          setSelectedId(firstPending?.id || transformedEscalations[0].id)
        } else {
          setSelectedId("")
        }
      } catch (err: any) {
        console.error("Error fetching HITL escalations:", err)
        setError(err.message || "Failed to load escalations")
        toast.error("Failed to load escalations", {
          description: err.message || "Please try again later.",
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchEscalations()
    // No auto-refresh - escalations only change when manually resolved
  }, [])

  const selectedItem = items.find((i) => i.id === selectedId)

  const handleDecision = async (id: string, action: "approve" | "reject" | "modify", feedback: string) => {
    try {
      // Call backend API to resolve escalation
      await apiClient.resolveEscalation(id, action, feedback)

      // Refresh escalations to get updated data with decisions/feedback
      const backendEscalations: BackendEscalation[] = await apiClient.getAllEscalations(true, true)
      
      const transformedEscalations: EscalationItem[] = await Promise.all(
        backendEscalations.map(async (esc) => {
          let week = "Unknown"
          try {
            const sessionDetails = await apiClient.getSession(esc.session_id, true)
            if (sessionDetails?.week_number) {
              week = `Week ${sessionDetails.week_number}`
            }
          } catch (e) {
            console.debug(`Could not fetch session details for ${esc.session_id}:`, e)
          }

          const createdAt = new Date(esc.created_at)
          const timestamp = formatDistanceToNow(createdAt, { addSuffix: true })
          const status = (esc.status || "pending") as "pending" | "approved" | "rejected" | "modified"

          return {
            id: esc.request_id,
            riskScore: esc.risk_score,
            timestamp,
            reason: esc.escalation_reason,
            session: esc.session_id,
            week,
            primaryAgent: "Governance",
            summary: esc.escalation_reason || "Escalation requires human review",
            agentOutputs: [],
            status,
            humanDecision: esc.human_decision || undefined,
            humanFeedback: esc.human_feedback || undefined,
            resolvedAt: esc.resolved_at || undefined,
          }
        })
      )

      setItems(transformedEscalations)
      
      // Select next pending escalation, or first item if none pending
      const nextPending = transformedEscalations.find(item => item.status === "pending")
      setSelectedId(nextPending?.id || transformedEscalations[0]?.id || "")

      // Show toast feedback
      if (action === "approve") {
        toast.success("Report Approved", {
          description: feedback || `Escalation #${id.substring(0, 8)} has been processed successfully.`,
          icon: <CheckCircle2 className="h-4 w-4 text-green-600" />,
        })
      } else if (action === "reject") {
        toast.error("Report Rejected", {
          description: feedback || `Escalation #${id.substring(0, 8)} has been sent back for regeneration.`,
          icon: <XCircle className="h-4 w-4 text-red-600" />,
        })
      } else {
        toast.info("Report Modified & Approved", {
          description: feedback || `Changes saved for Escalation #${id.substring(0, 8)}.`,
          icon: <AlertCircle className="h-4 w-4 text-blue-600" />,
        })
      }
    } catch (err: any) {
      console.error("Error resolving escalation:", err)
      toast.error("Failed to resolve escalation", {
        description: err.message || "Please try again.",
      })
    }
  }

  return (
    <div className="container mx-auto p-4 md:p-6 max-w-7xl h-[calc(100vh-4rem)] flex flex-col">
      <div className="mb-4 flex-shrink-0">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Human Review Queue</h1>
        <p className="text-muted-foreground">Review and resolve agent escalations, conflicts, and compliance flags.</p>
      </div>

      <div className="mb-4 flex-shrink-0">
        <HitlHeader items={items} />
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-muted-foreground">Loading escalations...</p>
          </div>
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <div>
              <h3 className="text-lg font-semibold mb-2">Error Loading Escalations</h3>
              <p className="text-muted-foreground">{error}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-[300px_1fr] border rounded-lg overflow-hidden bg-background shadow-sm">
          <QueueList items={items} selectedId={selectedId} onSelect={setSelectedId} />
          <div className="h-full overflow-hidden bg-muted/5 flex flex-col">
            {selectedItem ? (
              <EscalationCard item={selectedItem} onDecision={handleDecision} />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-muted-foreground p-8 text-center">
                <CheckCircle2 className="h-12 w-12 mb-4 opacity-20" />
                <h3 className="text-lg font-semibold">All Caught Up!</h3>
                <p className="max-w-xs">There are no pending escalations in the queue. Great work!</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
