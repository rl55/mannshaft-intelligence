export type AgentStatusType = "idle" | "running" | "completed" | "error"

export interface LogEntry {
  message: string
  timestamp: string // ISO timestamp string
}

export interface AgentData {
  id: string
  name: string
  role: string
  status: AgentStatusType
  logs: LogEntry[]
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
  error?: string // Error message if status is "failed"
}
