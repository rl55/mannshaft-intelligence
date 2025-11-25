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

          {/* Summary Section - Expanded to avoid scrolling */}
          <div className="space-y-1.5">
            <h3 className="text-xs font-semibold uppercase text-muted-foreground">Executive Summary</h3>
            <div className="p-4 border rounded-md bg-background shadow-sm max-h-[300px] overflow-y-auto">
              <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">{item.summary}</p>
            </div>
          </div>

          {/* Risk Rationale */}
          {item.riskRationale && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold uppercase text-muted-foreground">Risk Rationale</h3>
              <div className="p-3 border rounded-md bg-amber-50/50 dark:bg-amber-950/20 shadow-sm">
                <p className="text-sm leading-relaxed text-foreground/90">{item.riskRationale}</p>
              </div>
            </div>
          )}

          {/* Guardrail Violations */}
          {item.guardrailViolations && item.guardrailViolations.length > 0 && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold uppercase text-muted-foreground">Guardrail Violations</h3>
              <div className="space-y-2">
                {item.guardrailViolations.map((violation, idx) => (
                  <div key={idx} className="p-3 border rounded-md bg-red-50/50 dark:bg-red-950/20 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            violation.severity === "critical" || violation.severity === "high"
                              ? "destructive"
                              : violation.severity === "medium"
                              ? "secondary"
                              : "outline"
                          }
                        >
                          {violation.severity.toUpperCase()}
                        </Badge>
                        <span className="text-sm font-medium">{violation.rule_name}</span>
                        <Badge variant="outline" className="text-xs">
                          {violation.rule_type}
                        </Badge>
                      </div>
                    </div>
                    {violation.reasoning && (
                      <p className="text-sm text-muted-foreground mb-2">{violation.reasoning}</p>
                    )}
                    {violation.details && (
                      <details className="text-xs text-muted-foreground">
                        <summary className="cursor-pointer hover:text-foreground">View Details</summary>
                        <pre className="mt-2 p-2 bg-background rounded text-xs overflow-x-auto">
                          {JSON.stringify(violation.details, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Actions */}
          {item.recommendedActions && item.recommendedActions.length > 0 && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold uppercase text-muted-foreground">Recommended Actions</h3>
              <div className="space-y-2">
                {item.recommendedActions.map((action, idx) => (
                  <div key={idx} className="p-3 border rounded-md bg-blue-50/50 dark:bg-blue-950/20 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">{action.action}</span>
                      <Badge
                        variant={
                          action.priority === "high"
                            ? "destructive"
                            : action.priority === "medium"
                            ? "secondary"
                            : "outline"
                        }
                      >
                        {action.priority.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{action.expected_impact}</p>
                    {(action.pros || action.cons) && (
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        {action.pros && action.pros.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-green-700 dark:text-green-400 mb-1">Pros:</p>
                            <ul className="text-xs text-muted-foreground list-disc list-inside space-y-0.5">
                              {action.pros.map((pro, i) => (
                                <li key={i}>{pro}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {action.cons && action.cons.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-red-700 dark:text-red-400 mb-1">Cons:</p>
                            <ul className="text-xs text-muted-foreground list-disc list-inside space-y-0.5">
                              {action.cons.map((con, i) => (
                                <li key={i}>{con}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

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
