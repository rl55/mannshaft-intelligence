"use client"

import { useState } from "react"
import { HitlHeader } from "@/components/hitl/hitl-header"
import { QueueList } from "@/components/hitl/queue-list"
import { EscalationCard } from "@/components/hitl/escalation-card"
import { mockEscalations } from "@/components/hitl/mock-data"
import type { EscalationItem } from "@/components/hitl/types"
import { toast } from "sonner"
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react"

export default function HitlPage() {
  const [items, setItems] = useState<EscalationItem[]>(mockEscalations)
  const [selectedId, setSelectedId] = useState<string>(mockEscalations.length > 0 ? mockEscalations[0].id : "")

  const selectedItem = items.find((i) => i.id === selectedId)

  const handleDecision = (id: string, action: "approve" | "reject" | "modify", feedback: string) => {
    // 1. Update the item status
    const updatedItems = items.map((item) => {
      if (item.id === id) {
        return {
          ...item,
          status: action === "reject" ? "rejected" : "approved",
          decision: {
            action,
            feedback,
            timestamp: new Date().toISOString(),
          },
        } as EscalationItem
      }
      return item
    })

    setItems(updatedItems)

    // 2. Show toast feedback
    if (action === "approve") {
      toast.success("Report Approved", {
        description: `Escalation #${id} has been processed successfully.`,
        icon: <CheckCircle2 className="h-4 w-4 text-green-600" />,
      })
    } else if (action === "reject") {
      toast.error("Report Rejected", {
        description: `Escalation #${id} has been sent back for regeneration.`,
        icon: <XCircle className="h-4 w-4 text-red-600" />,
      })
    } else {
      toast.info("Report Modified & Approved", {
        description: `Changes saved for Escalation #${id}.`,
        icon: <AlertCircle className="h-4 w-4 text-blue-600" />,
      })
    }

    // 3. Auto-advance to next pending item
    const pendingItems = updatedItems.filter((i) => i.status === "pending" && i.id !== id)
    if (pendingItems.length > 0) {
      setSelectedId(pendingItems[0].id)
    }
  }

  return (
    <div className="container mx-auto p-4 md:p-6 max-w-7xl h-[calc(100vh-4rem)] flex flex-col">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Human Review Queue</h1>
        <p className="text-muted-foreground">Review and resolve agent escalations, conflicts, and compliance flags.</p>
      </div>

      <HitlHeader />

      <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-[320px_1fr] border rounded-lg overflow-hidden bg-background shadow-sm">
        <QueueList items={items} selectedId={selectedId} onSelect={setSelectedId} />
        <div className="h-full overflow-hidden bg-muted/5">
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
    </div>
  )
}
