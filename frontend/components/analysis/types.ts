export type AgentStatusType = "idle" | "running" | "completed" | "error"

export interface AgentData {
  id: string
  name: string
  role: string
  status: AgentStatusType
  logs: string[]
  confidence?: number
  stats?: { label: string; value: string }[]
  executionTime?: number
}

export interface SessionStatus {
  id: string
  week: string
  progress: number
  timeRemaining: number
  status: "initializing" | "processing" | "evaluating" | "completed" | "failed"
}
