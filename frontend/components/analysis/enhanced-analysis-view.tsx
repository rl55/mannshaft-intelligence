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

  // Update session from WebSocket events
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1]
      
      // Update progress
      setSession((prev) => ({
        ...prev,
        progress: latestEvent.progress || prev.progress,
        status: latestEvent.progress >= 100 ? "completed" : "processing",
      }))

      // Handle agent-specific events
      if (latestEvent.agent) {
        const agentId = latestEvent.agent.toLowerCase()
        const agent = agents.find((a) => a.id === agentId)

        if (agent) {
          if (latestEvent.type === "agent_started") {
            setAgents((prev) =>
              prev.map((a) =>
                a.id === agentId ? { ...a, status: "running" } : a
              )
            )
          } else if (latestEvent.type === "agent_completed") {
            setAgents((prev) =>
              prev.map((a) =>
                a.id === agentId
                  ? {
                      ...a,
                      status: "completed",
                      confidence: latestEvent.data?.confidence || a.confidence,
                    }
                  : a
              )
            )
          }

          // Add log entry
          if (latestEvent.message) {
            setAgents((prev) =>
              prev.map((a) =>
                a.id === agentId
                  ? { ...a, logs: [...a.logs, `> ${latestEvent.message}`] }
                  : a
              )
            )
          }
        }
      }
    }
  }, [events, agents])

  // Poll for status updates as fallback
  useEffect(() => {
    if (!isConnected && !isReconnecting) {
      const interval = setInterval(async () => {
        try {
          const status = await getAnalysisStatus(sessionId)
          setSession((prev) => ({
            ...prev,
            progress: status.progress,
            status: status.status as SessionStatus["status"],
          }))
        } catch (error) {
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
              {isReconnecting && (
                <span className="ml-2 text-yellow-600">Reconnecting...</span>
              )}
              {!isConnected && !isReconnecting && (
                <span className="ml-2 text-red-600 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Disconnected
                </span>
              )}
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

