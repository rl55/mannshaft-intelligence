"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Check, X, Edit, Loader2 } from "lucide-react"

interface DecisionPanelProps {
  onDecide: (action: "approve" | "reject" | "modify", feedback: string) => void
}

export function DecisionPanel({ onDecide }: DecisionPanelProps) {
  const [feedback, setFeedback] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleAction = async (action: "approve" | "reject" | "modify") => {
    setIsSubmitting(true)
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 800))
    onDecide(action, feedback)
    setFeedback("")
    setIsSubmitting(false)
  }

  return (
    <div className="border-t p-6 bg-muted/10">
      <div className="grid gap-6">
        <div className="space-y-2">
          <Label htmlFor="feedback">Feedback & Notes (Optional)</Label>
          <Textarea
            id="feedback"
            placeholder="Provide context for this decision to improve future agent performance..."
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            className="min-h-[100px]"
          />
        </div>

        <div className="flex items-center gap-3 justify-end">
          <Button variant="outline" onClick={() => handleAction("modify")} disabled={isSubmitting} className="gap-2">
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Edit className="h-4 w-4" />}
            Modify & Approve
          </Button>

          <Button
            variant="destructive"
            onClick={() => handleAction("reject")}
            disabled={isSubmitting}
            className="gap-2"
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <X className="h-4 w-4" />}
            Reject
          </Button>

          <Button
            onClick={() => handleAction("approve")}
            disabled={isSubmitting}
            className="bg-green-600 hover:bg-green-700 gap-2"
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            Approve
          </Button>
        </div>
      </div>
    </div>
  )
}
