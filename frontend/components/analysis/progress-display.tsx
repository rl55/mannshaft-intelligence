"use client"

import { Progress } from "@/components/ui/progress"
import type { SessionStatus } from "@/components/analysis/types"
import { Clock, Activity } from "lucide-react"

interface ProgressDisplayProps {
  session: SessionStatus
}

export function ProgressDisplay({ session }: ProgressDisplayProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <Activity className="size-4 text-primary animate-pulse" />
          <span className="font-medium">Overall Progress</span>
        </div>
        <div className="flex items-center gap-4 text-muted-foreground">
          {session.status !== "completed" && (
            <div className="flex items-center gap-1.5">
              <Clock className="size-3.5" />
              <span>Est. Time: {session.timeRemaining}s remaining</span>
            </div>
          )}
          <span className="font-medium text-foreground">{Math.round(session.progress)}%</span>
        </div>
      </div>
      <Progress value={session.progress} className="h-2" />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span className={session.progress >= 25 ? "text-primary" : ""}>Initialization</span>
        <span className={session.progress >= 50 ? "text-primary" : ""}>Data Collection</span>
        <span className={session.progress >= 75 ? "text-primary" : ""}>Synthesis</span>
        <span className={session.progress >= 100 ? "text-primary" : ""}>Validation</span>
      </div>
    </div>
  )
}
