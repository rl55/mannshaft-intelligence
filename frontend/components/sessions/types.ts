import type { AgentStatusType } from "@/components/analysis/types"

export type SessionStatusType = "completed" | "running" | "partial" | "failed"

export interface SessionHistoryItem {
  id: string
  week: string
  status: SessionStatusType
  qualityScore?: number
  executionTime: string
  date: string
  user: string
  cacheHitRate: number
  cost: string
}

export interface AgentExecutionMetric {
  name: string
  status: AgentStatusType
  confidence: number
  executionTime: string
  cacheStatus: "HIT" | "MISS" | "N/A"
}

export interface SessionCostMetric {
  geminiCost: string
  inputTokens: number
  outputTokens: number
}

export interface SessionGovernanceMetric {
  passed: number
  violations: number
  escalations: number
}

export interface SessionDetail extends SessionHistoryItem {
  agents: AgentExecutionMetric[]
  governance: SessionGovernanceMetric
  costBreakdown: SessionCostMetric
  fullTimestamp: string
}
