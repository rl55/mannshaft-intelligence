"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Check, X, Edit, Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface DecisionPanelProps {
  onDecide: (action: "approve" | "reject" | "modify", feedback: string) => void
}

export function DecisionPanel({ onDecide }: DecisionPanelProps) {
  const [feedback, setFeedback] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAction = async (action: "approve" | "reject" | "modify") => {
    // Validate required fields
    if (action === "reject" && !feedback.trim()) {
      setError("Feedback is required when rejecting an escalation.")
      return
    }
    
    if (action === "modify" && !feedback.trim()) {
      setError("Please provide modifications or feedback when modifying an escalation.")
      return
    }

    setError(null)
    setIsSubmitting(true)
    
    try {
      // Small delay for better UX
      await new Promise((resolve) => setTimeout(resolve, 300))
      onDecide(action, feedback.trim() || "")
      setFeedback("")
    } catch (err) {
      setError("Failed to process decision. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="border-t p-4 bg-muted/10">
      <div className="grid gap-4">
        {error && (
          <Alert variant="destructive" className="py-2">
            <AlertDescription className="text-sm">{error}</AlertDescription>
          </Alert>
        )}
        
        <div className="space-y-1.5">
          <Label htmlFor="feedback" className="text-sm">
            Feedback & Notes {<span className="text-muted-foreground">(Required for Reject)</span>}
          </Label>
          <Textarea
            id="feedback"
            placeholder="Provide context for this decision to improve future agent performance..."
            value={feedback}
            onChange={(e) => {
              setFeedback(e.target.value)
              setError(null) // Clear error when user types
            }}
            className="min-h-[80px] text-sm"
          />
        </div>

        <div className="flex items-center gap-2 justify-end">
          <Button 
            variant="outline" 
            onClick={() => handleAction("modify")} 
            disabled={isSubmitting} 
            className="gap-2"
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Edit className="h-4 w-4" />}
            Modify & Approve
          </Button>

          <Button
            variant="destructive"
            onClick={() => handleAction("reject")}
            disabled={isSubmitting || !feedback.trim()}
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
