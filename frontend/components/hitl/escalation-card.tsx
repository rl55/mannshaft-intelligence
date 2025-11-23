import type { EscalationItem } from "./types"
import { Card, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { FileText, Calendar, User } from "lucide-react"
import { AgentOutputs } from "./agent-outputs"
import { DecisionPanel } from "./decision-panel"

interface EscalationCardProps {
  item: EscalationItem
  onDecision: (id: string, action: "approve" | "reject" | "modify", feedback: string) => void
}

export function EscalationCard({ item, onDecision }: EscalationCardProps) {
  return (
    <Card className="h-full flex flex-col border-0 shadow-none rounded-none md:rounded-lg md:border">
      <CardHeader className="pb-4 border-b">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold">Escalation #{item.id}</h2>
              <Badge variant="outline" className="font-normal text-muted-foreground">
                {item.timestamp}
              </Badge>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Badge
                className={
                  item.riskScore > 0.7
                    ? "bg-red-100 text-red-700 hover:bg-red-100 border-red-200"
                    : "bg-yellow-100 text-yellow-700 hover:bg-yellow-100 border-yellow-200"
                }
              >
                Risk Score: {item.riskScore}
              </Badge>
              <span>•</span>
              <span className="font-medium text-foreground">{item.reason}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2 bg-transparent">
              <FileText className="h-4 w-4" />
              Preview Report
            </Button>
          </div>
        </div>
      </CardHeader>

      <div className="flex-1 overflow-auto">
        <div className="p-6 space-y-6">
          {/* Metadata Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted/30 rounded-lg border">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                <FileText className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase">Session</p>
                <p className="text-sm font-medium">{item.session}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
                <Calendar className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase">Period</p>
                <p className="text-sm font-medium">{item.week}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-orange-100 flex items-center justify-center text-orange-600">
                <User className="h-4 w-4" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase">Flagged By</p>
                <p className="text-sm font-medium">{item.primaryAgent}</p>
              </div>
            </div>
          </div>

          {/* Summary Section */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold uppercase text-muted-foreground">Executive Summary</h3>
            <div className="p-4 border rounded-md bg-background shadow-sm">
              <p className="text-sm leading-relaxed text-foreground/90">{item.summary}</p>
            </div>
          </div>

          <Separator />

          {/* Agent Outputs */}
          <AgentOutputs outputs={item.agentOutputs} />
        </div>
      </div>

      {/* Decision Panel (Fixed at bottom or scrollable?) -> Let's keep it at bottom of flow */}
      <DecisionPanel onDecide={(action, feedback) => onDecision(item.id, action, feedback)} />
    </Card>
  )
}
