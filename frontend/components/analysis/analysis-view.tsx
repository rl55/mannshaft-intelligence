"use client"

import { useState, useEffect, useCallback } from "react"
import { AgentCard } from "@/components/analysis/agent-card"
import { ProgressDisplay } from "@/components/analysis/progress-display"
import type { AgentData, SessionStatus } from "@/components/analysis/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { BarChart3, RefreshCw, DollarSign, Users, HeadphonesIcon, X, Shield } from "lucide-react"

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

interface AnalysisViewProps {
  weekId: string
  onClose: () => void
}

export function AnalysisView({ weekId, onClose }: AnalysisViewProps) {
  const [agents, setAgents] = useState<AgentData[]>(INITIAL_AGENTS)
  const [session, setSession] = useState<SessionStatus>({
    id: Math.random().toString(36).substring(7),
    week: weekId,
    progress: 0,
    timeRemaining: 12,
    status: "initializing",
  })

  const addLog = useCallback((agentId: string, message: string) => {
    setAgents((prev) =>
      prev.map((agent) => (agent.id === agentId ? { ...agent, logs: [...agent.logs, `> ${message}`] } : agent)),
    )
  }, [])

  const updateAgentStatus = useCallback((agentId: string, status: AgentData["status"], confidence?: number) => {
    setAgents((prev) =>
      prev.map((agent) =>
        agent.id === agentId ? { ...agent, status, ...(confidence !== undefined && { confidence }) } : agent,
      ),
    )
  }, [])

  // Simulation Effect
  useEffect(() => {
    let timeoutId: NodeJS.Timeout
    let progressInterval: NodeJS.Timeout

    const runSimulation = async () => {
      // Start
      setSession((prev) => ({ ...prev, status: "processing" }))

      // Revenue Agent starts
      updateAgentStatus("revenue", "running")
      addLog("revenue", `Fetching financial data for Week ${weekId}...`)
      await new Promise((r) => setTimeout(r, 1500))
      addLog("revenue", "Analyzing recurring revenue patterns...")
      await new Promise((r) => setTimeout(r, 1500))
      addLog("revenue", "Detected 12% increase in enterprise upgrades")
      updateAgentStatus("revenue", "completed", 0.94)

      // Product Agent starts
      updateAgentStatus("product", "running")
      addLog("product", "Correlating revenue with feature usage...")
      await new Promise((r) => setTimeout(r, 1200))
      addLog("product", "High engagement detected in new Analytics dashboard")
      await new Promise((r) => setTimeout(r, 1500))
      addLog("product", "Recommending resource allocation to Analytics team")
      updateAgentStatus("product", "completed", 0.88)

      // Support Agent starts
      updateAgentStatus("support", "running")
      addLog("support", `Scanning support tickets for Week ${weekId}...`)
      await new Promise((r) => setTimeout(r, 1000))
      addLog("support", "No critical issues found in enterprise segment")
      await new Promise((r) => setTimeout(r, 1000))
      addLog("support", "Customer sentiment analysis: Positive")
      updateAgentStatus("support", "completed", 0.92)

      // Governance Agent starts
      updateAgentStatus("governance", "running")
      addLog("governance", "Verifying compliance with safety guardrails...")
      await new Promise((r) => setTimeout(r, 800))
      addLog("governance", "PII Check: Passed")
      await new Promise((r) => setTimeout(r, 800))
      addLog("governance", "Final report approved for distribution")
      updateAgentStatus("governance", "completed", 1.0)

      // Complete
      setSession((prev) => ({ ...prev, status: "completed", progress: 100, timeRemaining: 0 }))
    }

    // Progress Timer
    progressInterval = setInterval(() => {
      setSession((prev) => {
        if (prev.progress >= 100) return prev
        return {
          ...prev,
          progress: Math.min(prev.progress + 2, 99),
          timeRemaining: Math.max(prev.timeRemaining - 0.2, 0),
        }
      })
    }, 200)

    timeoutId = setTimeout(runSimulation, 500)

    return () => {
      clearTimeout(timeoutId)
      clearInterval(progressInterval)
    }
  }, [weekId, addLog, updateAgentStatus])

  return (
    <Card className="border-primary/20 shadow-lg">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Week {weekId} Analysis
            </CardTitle>
            <CardDescription>Multi-agent intelligence grid processing data</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {session.status === "completed" && (
              <Button variant="outline" size="sm" onClick={() => setAgents(INITIAL_AGENTS)}>
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
            <AgentCard key={agent.id} agent={agent} icon={AGENT_ICONS[agent.id as keyof typeof AGENT_ICONS]} />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
