// components/analysis/enhanced-analysis-view.tsx
"use client"

import { useState, useEffect, useCallback } from "react"
import { AgentCard } from "@/components/analysis/agent-card"
import { ProgressDisplay } from "@/components/analysis/progress-display"
import type { AgentData, SessionStatus } from "@/components/analysis/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { BarChart3, RefreshCw, DollarSign, Users, HeadphonesIcon, X, Shield, AlertCircle } from "lucide-react"
import { useAnalysisProgress } from "@/hooks/use-analysis-progress"
import { useAnalysisStore } from "@/store/analysis-store"
import { useToast } from "@/hooks/use-toast"

const INITIAL_AGENTS: AgentData[] = [
  {
    id: "revenue",
    name: "Revenue Agent",
    role: "Financial Analysis",
    status: "idle",
    logs: [],
    confidence: 0,
  },
  {
    id: "product",
    name: "Product Agent",
    role: "Product Strategy",
    status: "idle",
    logs: [],
    confidence: 0,
  },
  {
    id: "support",
    name: "Support Agent",
    role: "Customer Success",
    status: "idle",
    logs: [],
    confidence: 0,
  },
  {
    id: "governance",
    name: "Governance Agent",
    role: "Safety & Compliance",
    status: "idle",
    logs: [],
    confidence: 0,
  },
]

const AGENT_ICONS = {
  revenue: <DollarSign className="size-5 text-primary" />,
  product: <Users className="size-5 text-primary" />,
  support: <HeadphonesIcon className="size-5 text-primary" />,
  governance: <Shield className="size-5 text-primary" />,
}

interface EnhancedAnalysisViewProps {
  sessionId: string
  weekId: string
  onClose: () => void
}

export function EnhancedAnalysisView({ sessionId, weekId, onClose }: EnhancedAnalysisViewProps) {
  const [agents, setAgents] = useState<AgentData[]>(INITIAL_AGENTS)
  const { toast } = useToast()
  const { getAnalysisStatus, getAnalysisResult } = useAnalysisStore()
  
  // Use WebSocket hook for real-time updates
  const { events, progress, isConnected, isReconnecting } = useAnalysisProgress(
    sessionId,
    {
      onComplete: async () => {
        // Fetch final result when analysis completes
        try {
          await getAnalysisResult(sessionId)
          toast({
            title: "Analysis Complete",
            description: "Your analysis has been completed successfully",
          })
        } catch (error) {
          console.error("Failed to fetch analysis result:", error)
        }
      },
      onError: (error) => {
        toast({
          title: "Connection Error",
          description: error.message,
          variant: "destructive",
        })
      },
    }
  )

  // Initialize session status
  const [session, setSession] = useState<SessionStatus>({
    id: sessionId,
    week: weekId,
    progress: 0,
    timeRemaining: 12,
    status: "initializing",
  })

  // Update session from WebSocket events and progress
  useEffect(() => {
    // Update progress from hook's progress value (most up-to-date)
    setSession((prev) => ({
      ...prev,
      progress: progress,
      status: progress >= 100 ? "completed" : prev.status === "initializing" ? "initializing" : "processing",
    }))
  }, [progress])

  // Update session from WebSocket events for agent-specific updates
  useEffect(() => {
    if (events.length > 0) {
      // Process all events, not just the latest one
      // This ensures we catch all agent_completed events even if they arrive together
      const processedAgents = new Set<string>()
      
      events.forEach((event) => {
        // Update status based on event type (use latest event for status)
        if (event === events[events.length - 1]) {
          if (event.type === "completed" || event.progress >= 100) {
            setSession((prev) => ({
              ...prev,
              status: "completed",
            }))
          } else if (event.type === "error") {
            setSession((prev) => ({
              ...prev,
              status: "failed",
            }))
          } else if (event.type === "agent_started" || event.type === "progress_update") {
            setSession((prev) => ({
              ...prev,
              status: prev.status === "initializing" ? "processing" : prev.status,
            }))
          }
        }

        // Handle agent-specific events - process ALL events, not just latest
        if (event.agent) {
          const agentId = event.agent.toLowerCase()
          const eventKey = `${event.type}-${agentId}`
          
          // Skip if we've already processed this exact event
          if (processedAgents.has(eventKey)) return
          processedAgents.add(eventKey)

          // Use functional updates to avoid dependency on agents array
          if (event.type === "agent_started") {
            setAgents((prev) =>
              prev.map((a) =>
                a.id === agentId ? { ...a, status: "running" } : a
              )
            )
          } else if (event.type === "agent_completed") {
            setAgents((prev) =>
              prev.map((a) =>
                a.id === agentId
                  ? {
                      ...a,
                      status: "completed",
                      confidence: event.data?.confidence || a.confidence,
                    }
                  : a
              )
            )
          }

          // Add log entry
          if (event.message) {
            setAgents((prev) => {
              const agent = prev.find((a) => a.id === agentId)
              if (!agent) return prev
              
              // Check if this log entry already exists to prevent duplicates
              const logEntry = `> ${event.message}`
              if (agent.logs.includes(logEntry)) return prev
              
              return prev.map((a) =>
                a.id === agentId
                  ? { ...a, logs: [...a.logs, logEntry] }
                  : a
              )
            })
          }
        }
      })
    }
  }, [events]) // Removed 'agents' from dependencies to prevent infinite loop

  // Poll for status updates as fallback (only when WebSocket is not connected)
  useEffect(() => {
    if (!isConnected && !isReconnecting && sessionId) {
      let pollCount = 0
      const maxPollAttempts = 3 // Stop polling after 3 consecutive 404s
      let consecutive404s = 0
      
      const interval = setInterval(async () => {
        try {
          const status = await getAnalysisStatus(sessionId)
          consecutive404s = 0 // Reset counter on success
          // Update session status, but progress comes from WebSocket hook
          setSession((prev) => ({
            ...prev,
            status: status.status as SessionStatus["status"],
            // Only update progress if WebSocket hasn't provided a more recent value
            // (WebSocket progress takes precedence)
          }))
          
          // Stop polling if analysis is completed or failed
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(interval)
          }
        } catch (error: any) {
          // Handle 404s gracefully - session might not exist yet or was cleared
          if (error?.statusCode === 404) {
            consecutive404s++
            pollCount++
            
            // Only log warning after multiple attempts
            if (consecutive404s >= maxPollAttempts) {
              console.warn(`Session ${sessionId} not found after ${pollCount} attempts. Stopping polling.`)
              clearInterval(interval)
              return
            }
            
            // Silently retry for first few 404s (session might be initializing)
            return
          }
          
          // Log other errors
          console.error("Failed to fetch status:", error)
        }
      }, 5000) // Poll every 5 seconds

      return () => clearInterval(interval)
    }
  }, [isConnected, isReconnecting, sessionId, getAnalysisStatus])

  const handleRerun = useCallback(() => {
    setAgents(INITIAL_AGENTS)
    setSession({
      id: sessionId,
      week: weekId,
      progress: 0,
      timeRemaining: 12,
      status: "initializing",
    })
  }, [sessionId, weekId])

  return (
    <Card className="border-primary/20 shadow-lg">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Week {weekId} Analysis
            </CardTitle>
            <CardDescription>
              Multi-agent intelligence grid processing data
              {session.status === "completed" ? (
                <span className="ml-2 text-green-600 flex items-center gap-1">
                  ✓ Completed
                </span>
              ) : isReconnecting ? (
                <span className="ml-2 text-yellow-600">Reconnecting...</span>
              ) : !isConnected && !isReconnecting ? (
                <span className="ml-2 text-red-600 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Disconnected
                </span>
              ) : null}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {session.status === "completed" && (
              <Button variant="outline" size="sm" onClick={handleRerun}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Rerun
              </Button>
            )}
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <ProgressDisplay session={session} />

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              icon={AGENT_ICONS[agent.id as keyof typeof AGENT_ICONS]}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

