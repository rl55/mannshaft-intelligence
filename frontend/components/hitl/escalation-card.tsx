import type { EscalationItem } from "./types"
import { Card, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, Calendar, User } from "lucide-react"
import { AgentOutputs } from "./agent-outputs"
import { DecisionPanel } from "./decision-panel"
import Link from "next/link"
import { formatDistanceToNow } from "date-fns"

interface EscalationCardProps {
  item: EscalationItem
  onDecision: (id: string, action: "approve" | "reject" | "modify", feedback: string) => void
}

export function EscalationCard({ item, onDecision }: EscalationCardProps) {
  return (
    <Card className="h-full flex flex-col border-0 shadow-none rounded-none md:rounded-lg md:border overflow-hidden">
      <CardHeader className="pb-3 px-4 pt-4 border-b flex-shrink-0">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold">{item.week || `Escalation #${item.id.substring(0, 8)}`}</h2>
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
                Risk Score: {(item.riskScore * 100).toFixed(0)}%
              </Badge>
              <span>•</span>
              <span className="font-medium text-foreground">{item.reason}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2 bg-transparent" asChild>
              <Link href={`/reports/${item.session}`}>
                <FileText className="h-4 w-4" />
                Preview Report
              </Link>
            </Button>
          </div>
        </div>
      </CardHeader>

      <div className="flex-1 overflow-y-auto min-h-0 px-4">
        <div className="py-3 space-y-3">
          {/* Metadata Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3 bg-muted/30 rounded-lg border">
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
          <div className="space-y-1.5">
            <h3 className="text-xs font-semibold uppercase text-muted-foreground">Executive Summary</h3>
            <div className="p-3 border rounded-md bg-background shadow-sm">
              <p className="text-sm leading-relaxed text-foreground/90">{item.summary}</p>
            </div>
          </div>

          {/* Agent Outputs */}
          <AgentOutputs outputs={item.agentOutputs} />

          {/* Decision & Feedback (if resolved) */}
          {item.status !== "pending" && (item.humanDecision || item.humanFeedback) && (
            <>
              <div className="space-y-1.5">
                <h3 className="text-xs font-semibold uppercase text-muted-foreground">Decision & Feedback</h3>
                <div className="p-3 border rounded-md bg-background shadow-sm space-y-2">
                  {item.humanDecision && (
                    <div>
                      <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Decision</p>
                      <Badge
                        className={
                          item.status === "approved"
                            ? "bg-green-100 text-green-700 hover:bg-green-100 border-green-200"
                            : item.status === "rejected"
                            ? "bg-red-100 text-red-700 hover:bg-red-100 border-red-200"
                            : "bg-blue-100 text-blue-700 hover:bg-blue-100 border-blue-200"
                        }
                      >
                        {item.status === "approved" ? "✓ Approved" : item.status === "rejected" ? "✗ Rejected" : "✎ Modified"}
                      </Badge>
                    </div>
                  )}
                  {item.humanFeedback && (
                    <div>
                      <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Feedback</p>
                      <p className="text-sm leading-relaxed text-foreground/90">{item.humanFeedback}</p>
                    </div>
                  )}
                  {item.resolvedAt && (
                    <div>
                      <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Resolved</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDistanceToNow(new Date(item.resolvedAt), { addSuffix: true })}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Decision Panel - Only show for pending escalations */}
      {item.status === "pending" && (
        <div className="flex-shrink-0 border-t bg-background">
          <DecisionPanel onDecide={(action, feedback) => onDecision(item.id, action, feedback)} />
        </div>
      )}
    </Card>
  )
}
