export interface AgentOutput {
  id: string
  name: string
  confidence: number
  content: string
  flagged?: boolean
  warnings?: string[]
}

export interface EscalationItem {
  id: string
  riskScore: number
  timestamp: string
  reason: string
  session: string
  week: string
  primaryAgent: string
  summary: string
  agentOutputs: AgentOutput[]
  status: "pending" | "approved" | "rejected" | "modified"
  humanDecision?: string
  humanFeedback?: string
  resolvedAt?: string
  decision?: {
    action: "approve" | "reject" | "modify"
    feedback?: string
    tags?: string[]
    timestamp: string
  }
}
