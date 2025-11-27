// components/analysis/enhanced-analysis-view.tsx
"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { AgentCard } from "@/components/analysis/agent-card"
import { ProgressDisplay } from "@/components/analysis/progress-display"
import type { AgentData, SessionStatus, LogEntry } from "@/components/analysis/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { BarChart3, RefreshCw, DollarSign, Users, HeadphonesIcon, X, Shield, AlertCircle, Network, CheckCircle, Activity } from "lucide-react"
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
    id: "synthesizer",
    name: "Synthesizer Agent",
    role: "Cross-Functional Synthesis",
    status: "idle",
    logs: [],
    confidence: 0,
  },
  {
    id: "evaluation",
    name: "Evaluation Agent",
    role: "Quality Assurance",
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
  synthesizer: <Network className="size-5 text-primary" />,
  governance: <Shield className="size-5 text-primary" />,
  evaluation: <CheckCircle className="size-5 text-primary" />,
}

interface EnhancedAnalysisViewProps {
  sessionId: string
  weekId: string
  onClose: () => void
}

// Helper to create a log entry with the event timestamp or current time
function createLogEntry(message: string, eventTimestamp?: string): LogEntry {
  return {
    message,
    timestamp: eventTimestamp || new Date().toISOString(),
  }
}

export function EnhancedAnalysisView({ sessionId, weekId, onClose }: EnhancedAnalysisViewProps) {
  // Show loading state if sessionId is not yet available
  if (!sessionId) {
    return (
      <Card className="border-primary/20 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Week {weekId} Analysis
          </CardTitle>
          <CardDescription>Initializing analysis session...</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center p-12">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-muted-foreground">Starting analysis for Week {weekId}...</p>
          </div>
        </CardContent>
      </Card>
    )
  }
  const [agents, setAgents] = useState<AgentData[]>(INITIAL_AGENTS)
  const { toast } = useToast()
  const { getAnalysisStatus, getAnalysisResult } = useAnalysisStore()
  
  // Use WebSocket hook for real-time updates
  const { 
    events, 
    progress, 
    isConnected, 
    isConnecting, 
    isReconnecting,
    analysisError,
    canRetry,
    isRetrying,
    clearError 
  } = useAnalysisProgress(
    sessionId,
    {
      waitForSession: false, // Connect immediately
      initialDelay: 100, // Minimal delay
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
      onAnalysisFailed: (message, canRetryFlag) => {
        toast({
          title: "Analysis Failed",
          description: message,
          variant: "destructive",
        })
      },
    }
  )
  
  // Fetch initial status immediately when component mounts
  useEffect(() => {
    const fetchInitialStatus = async () => {
      try {
        const status = await getAnalysisStatus(sessionId)
        if (status.progress !== undefined) {
          // Update progress from initial status
          setSession((prev) => ({
            ...prev,
            progress: status.progress || 0,
            status: status.status || "initializing",
          }))
        }
      } catch (error) {
        // Ignore - WebSocket will provide updates
        console.log("Initial status fetch failed, will use WebSocket:", error)
      }
    }
    
    fetchInitialStatus()
  }, [sessionId, getAnalysisStatus])

  // Initialize session status with optimistic "connecting" state
  const [session, setSession] = useState<SessionStatus>({
    id: sessionId,
    week: weekId,
    progress: 0,
    timeRemaining: 12,
    status: "initializing", // Will update to "processing" when connected
  })

  // Update session from WebSocket events and progress
  useEffect(() => {
    // Check if all agents are completed
    const allAgentsCompleted = agents.every(agent => agent.status === "completed");
    
    // Update progress from hook's progress value (most up-to-date)
    // Ensure progress is 100% when all agents are completed or status is completed
    let finalProgress = progress;
    if (allAgentsCompleted && progress < 100) {
      // If all agents are completed but progress isn't 100, set it to 100
      finalProgress = 100;
    } else if (progress >= 100) {
      finalProgress = 100;
    }
    
    // Determine status based on error state, retry state, and progress
    let sessionStatus: SessionStatus["status"] = "processing";
    if (analysisError && !isRetrying) {
      sessionStatus = "failed";
    } else if (isRetrying) {
      sessionStatus = "processing"; // Still processing during retry
    } else if (finalProgress >= 100 || allAgentsCompleted) {
      sessionStatus = "completed";
    } else if (isConnecting) {
      sessionStatus = "initializing";
    } else if (isConnected) {
      sessionStatus = "processing";
    }
    
    setSession((prev) => ({
      ...prev,
      progress: analysisError && !isRetrying ? 0 : finalProgress,
      status: sessionStatus,
      error: analysisError || undefined,
    }))
  }, [progress, agents, isConnecting, isConnected])

  // Track which events have been processed to avoid reprocessing
  const processedEventsRef = useRef<Set<string>>(new Set())
  
  // Update session from WebSocket events for agent-specific updates
  // Process events IMMEDIATELY as they arrive - no fake delays!
  useEffect(() => {
    if (events.length === 0) return
    
    // Filter out already processed events
    const newEvents = events.filter((event, index) => {
      const eventKey = `${event.type}-${event.agent || 'none'}-${event.timestamp || index}`
      if (processedEventsRef.current.has(eventKey)) {
        return false
      }
      processedEventsRef.current.add(eventKey)
      return true
    })
    
    if (newEvents.length === 0) return
    
    console.log(`Processing ${newEvents.length} new WebSocket events (${events.length} total):`, 
      newEvents.map(e => ({ type: e.type, agent: e.agent, progress: e.progress, message: e.message, data: e.data })))
    
    // Log all events for debugging
    if (newEvents.length > 0) {
      console.log("Full event details:", newEvents)
    }
    
    // Sort events to ensure 'started' events are processed before 'completed' for the same agent
    const sortedEvents = [...newEvents].sort((a, b) => {
      if (a.agent === b.agent) {
        if (a.type === 'agent_started' && b.type === 'agent_completed') return -1
        if (a.type === 'agent_completed' && b.type === 'agent_started') return 1
      }
      return 0
    })
    
    // Process all events, batching state updates for better performance
    let sessionUpdates: Partial<SessionStatus> = {}
    const agentUpdates = new Map<string, Partial<AgentData>>()
    
    sortedEvents.forEach((event) => {
      // Update status based on event type (use latest event for status)
      // Only treat as session completion if type is explicitly 'completed' or 'progress_update' with 100%
      if (event.type === "completed" || (event.type === "progress_update" && event.progress >= 100)) {
        sessionUpdates.status = "completed"
        sessionUpdates.progress = 100
      } else if (event.type === "error") {
        sessionUpdates.status = "failed"
      } else if (event.type === "agent_started" || event.type === "progress_update") {
        if (!sessionUpdates.status || sessionUpdates.status === "initializing") {
          sessionUpdates.status = "processing"
        }
        // Only update session progress from progress_update events
        if (event.type === "progress_update" && event.progress !== undefined) {
          sessionUpdates.progress = event.progress
        }
      }

      // Handle agent-specific events
      if (event.agent) {
        const agentId = event.agent.toLowerCase()
        
        if (!agentUpdates.has(agentId)) {
          agentUpdates.set(agentId, {})
        }
        const agentUpdate = agentUpdates.get(agentId)!

        // Get event timestamp (from event or current time)
        const eventTimestamp = event.timestamp || new Date().toISOString()
        
        if (event.type === "agent_started") {
          console.log(`Setting agent ${agentId} to running`)
          agentUpdate.status = "running"
          // Add "Processing" log when agent starts
          if (!agentUpdate.logs) {
            agentUpdate.logs = []
          }
          agentUpdate.logs.push(createLogEntry("Processing", eventTimestamp))
        } else if (event.type === "agent_completed") {
          const confidence = event.data?.confidence || event.data?.confidence_score || 0
          console.log(`Setting agent ${agentId} to completed with confidence ${confidence}`)
          agentUpdate.status = "completed"
          agentUpdate.confidence = confidence
          
          // Build detailed completion logs with insights
          if (!agentUpdate.logs) {
            agentUpdate.logs = []
          }
          
          // Add main completion message
          if (event.message) {
            agentUpdate.logs.push(createLogEntry(event.message, eventTimestamp))
          }
          
          // Add metrics summary if available
          if (event.data?.metrics && Object.keys(event.data.metrics).length > 0) {
            const metricsStr = Object.entries(event.data.metrics)
              .map(([key, value]) => `${key}: ${value}`)
              .join(", ")
            agentUpdate.logs.push(createLogEntry(`Metrics: ${metricsStr}`, eventTimestamp))
          }
          
          // Add key insights if available
          if (event.data?.key_insights && Array.isArray(event.data.key_insights) && event.data.key_insights.length > 0) {
            agentUpdate.logs.push(createLogEntry("Key Insights:", eventTimestamp))
            event.data.key_insights.slice(0, 3).forEach((insight: string) => {
              agentUpdate.logs.push(createLogEntry(`  • ${insight}`, eventTimestamp))
            })
          }
          
          // Add cache status if available
          if (event.data?.cached !== undefined) {
            agentUpdate.logs.push(createLogEntry(`Cache: ${event.data.cached ? "Hit" : "Miss"}`, eventTimestamp))
          }
          
          // Add execution time if available
          if (event.data?.execution_time_ms) {
            agentUpdate.logs.push(createLogEntry(`Execution Time: ${(event.data.execution_time_ms / 1000).toFixed(2)}s`, eventTimestamp))
          }
        } else {
          // Add log entry for other event types (agent_progress, etc.)
          if (event.message) {
            if (!agentUpdate.logs) {
              agentUpdate.logs = []
            }
            const newLog = createLogEntry(event.message, eventTimestamp)
            // Avoid duplicate messages
            const isDuplicate = agentUpdate.logs.some(log => log.message === newLog.message)
            if (!isDuplicate) {
              agentUpdate.logs.push(newLog)
            }
          }
        }
      }
    })
    
    // Apply session updates
    if (Object.keys(sessionUpdates).length > 0) {
      setSession((prev) => ({
        ...prev,
        ...sessionUpdates,
      }))
    }
    
    // Apply agent updates - batch all updates in a single setState call
    if (agentUpdates.size > 0) {
      console.log(`Applying updates to ${agentUpdates.size} agents:`, 
        Array.from(agentUpdates.entries()).map(([id, update]) => ({ id, status: update.status, confidence: update.confidence, logsCount: update.logs?.length || 0 })))
      
      setAgents((prev) => {
        const updated = prev.map((agent) => {
          const update = agentUpdates.get(agent.id)
          if (!update) return agent
          
          // Merge logs correctly - combine existing logs with new logs, avoiding duplicates by message
          const existingMessages = new Set(agent.logs.map(log => log.message))
          const mergedLogs = update.logs 
            ? [...agent.logs, ...update.logs.filter(log => !existingMessages.has(log.message))]
            : agent.logs
          
          const updatedAgent = {
            ...agent,
            ...update,
            logs: mergedLogs,
          }
          
          console.log(`Agent ${agent.id} updated:`, {
            oldStatus: agent.status,
            newStatus: updatedAgent.status,
            oldConfidence: agent.confidence,
            newConfidence: updatedAgent.confidence,
            oldLogsCount: agent.logs.length,
            newLogsCount: updatedAgent.logs.length,
          })
          
          return updatedAgent
        })
        return updated
      })
    }
  }, [events]) // Removed 'agents' from dependencies to prevent infinite loop

  // Poll for status updates as fallback (only when WebSocket is not connected)
  useEffect(() => {
    if (!isConnected && !isConnecting && !isReconnecting && sessionId) {
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
  }, [isConnected, isConnecting, isReconnecting, sessionId, getAnalysisStatus])

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
              {session.status === "failed" ? (
                <span className="ml-2 text-red-600 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Failed
                </span>
              ) : session.status === "completed" ? (
                <span className="ml-2 text-green-600 flex items-center gap-1">
                  ✓ Completed
                </span>
              ) : isRetrying ? (
                <span className="ml-2 text-yellow-600 flex items-center gap-1">
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  Retrying...
                </span>
              ) : isConnecting ? (
                <span className="ml-2 text-primary flex items-center gap-1">
                  <Activity className="h-3 w-3 animate-pulse" />
                  Connecting...
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
            {(session.status === "completed" || (session.status === "failed" && canRetry)) && (
              <Button variant="outline" size="sm" onClick={handleRerun}>
                <RefreshCw className="mr-2 h-4 w-4" />
                {session.status === "failed" ? "Retry" : "Rerun"}
              </Button>
            )}
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Error Banner */}
        {analysisError && !isRetrying && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Analysis Failed
                </h4>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  {analysisError}
                </p>
                {canRetry && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="mt-3 border-red-300 text-red-700 hover:bg-red-100 dark:border-red-700 dark:text-red-300 dark:hover:bg-red-900"
                    onClick={handleRerun}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Try Again
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Retry Banner */}
        {isRetrying && analysisError && (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-800 dark:bg-yellow-950">
            <div className="flex items-center gap-3">
              <RefreshCw className="h-5 w-5 text-yellow-600 dark:text-yellow-400 animate-spin" />
              <div>
                <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Retrying...
                </h4>
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  {analysisError}
                </p>
              </div>
            </div>
          </div>
        )}

        <ProgressDisplay session={session} />

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
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

