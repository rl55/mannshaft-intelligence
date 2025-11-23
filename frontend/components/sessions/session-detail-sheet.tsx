import { CheckCircle2, AlertTriangle, Clock, RefreshCw, Download, FileText, Zap } from "lucide-react"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/components/ui/sheet"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { SessionDetail, AgentExecutionMetric } from "./types"

interface SessionDetailSheetProps {
  session: SessionDetail | null
  isOpen: boolean
  onClose: () => void
}

export function SessionDetailSheet({ session, isOpen, onClose }: SessionDetailSheetProps) {
  if (!session) return null

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <div className="flex items-center justify-between">
            <SheetTitle>Session {session.id}</SheetTitle>
            <Badge variant="outline" className="mr-6">
              Week {session.week}
            </Badge>
          </div>
          <SheetDescription>
            {session.fullTimestamp} by {session.user}
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-200px)] pr-4">
          <div className="mt-6 space-y-6">
            {/* High Level Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-muted-foreground text-xs">Quality Score</div>
                <div className="text-2xl font-bold text-green-600">{session.qualityScore || 0}%</div>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-muted-foreground text-xs">Execution Time</div>
                <div className="text-2xl font-bold">{session.executionTime}</div>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-muted-foreground text-xs">Cache Hit Rate</div>
                <div className="text-2xl font-bold text-blue-600">{session.cacheHitRate}%</div>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-muted-foreground text-xs">Cost</div>
                <div className="text-2xl font-bold">{session.cost}</div>
              </div>
            </div>

            <Separator />

            {/* Agents Executed */}
            <div>
              <h3 className="mb-3 text-sm font-medium">Agents Executed</h3>
              <div className="space-y-3">
                {session.agents.map((agent, index) => (
                  <AgentRow key={index} agent={agent} />
                ))}
              </div>
            </div>

            <Separator />

            {/* Governance */}
            <div>
              <h3 className="mb-3 text-sm font-medium">Governance</h3>
              <div className="bg-muted/30 rounded-lg border p-4">
                <div className="flex justify-between text-sm">
                  <span>Guardrail Checks:</span>
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    {session.governance.passed} passed, {session.governance.violations} violations
                  </span>
                </div>
                <div className="mt-2 flex justify-between text-sm">
                  <span>HITL Escalations:</span>
                  <span>{session.governance.escalations}</span>
                </div>
              </div>
            </div>

            <Separator />

            {/* Cost Breakdown */}
            <div>
              <h3 className="mb-3 text-sm font-medium">Cost Analysis</h3>
              <div className="bg-muted/30 rounded-lg border p-4 text-sm">
                <div className="flex justify-between">
                  <span>Gemini API:</span>
                  <span>{session.costBreakdown.geminiCost}</span>
                </div>
                <div className="text-muted-foreground mt-2 flex justify-between text-xs">
                  <span>Input Tokens:</span>
                  <span>{session.costBreakdown.inputTokens.toLocaleString()}</span>
                </div>
                <div className="text-muted-foreground flex justify-between text-xs">
                  <span>Output Tokens:</span>
                  <span>{session.costBreakdown.outputTokens.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>

        <SheetFooter className="absolute bottom-0 left-0 right-0 border-t bg-background p-4">
          <div className="flex w-full justify-between gap-2 sm:justify-end">
            <Button variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export Logs
            </Button>
            <Button variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Re-run
            </Button>
            <Button size="sm">
              <FileText className="mr-2 h-4 w-4" />
              View Report
            </Button>
          </div>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

function AgentRow({ agent }: { agent: AgentExecutionMetric }) {
  return (
    <div className="flex items-center justify-between rounded-md border p-3">
      <div className="flex items-center gap-3">
        {agent.status === "completed" ? (
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        ) : agent.status === "error" ? (
          <AlertTriangle className="h-4 w-4 text-red-500" />
        ) : (
          <Clock className="h-4 w-4 text-blue-500" />
        )}
        <div>
          <div className="text-sm font-medium">{agent.name}</div>
          <div className="text-muted-foreground text-xs">Confidence: {(agent.confidence * 100).toFixed(0)}%</div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-sm">{agent.executionTime}</div>
        <div className="flex items-center justify-end gap-1">
          {agent.cacheStatus === "HIT" && (
            <Badge variant="secondary" className="h-5 px-1 text-[10px]">
              <Zap className="mr-1 h-3 w-3 fill-yellow-400 text-yellow-400" />
              CACHE
            </Badge>
          )}
          {agent.cacheStatus === "MISS" && <span className="text-muted-foreground text-[10px]">MISS</span>}
        </div>
      </div>
    </div>
  )
}
