import type { EscalationItem } from "./types"

export const mockEscalations: EscalationItem[] = [
  {
    id: "45",
    riskScore: 0.75,
    timestamp: "5 min ago",
    reason: "Low confidence analysis (0.68)",
    session: "abc-123",
    week: "Week 8",
    primaryAgent: "Synthesizer",
    summary:
      "Revenue grew 15% but Product and Support agents show conflicting signals. Synthesizer flagged data quality concerns due to incomplete Support data (missing 3 weeks). Recommend manual review before sending to stakeholders.",
    status: "pending",
    agentOutputs: [
      {
        id: "revenue",
        name: "Revenue Agent",
        confidence: 0.92,
        content:
          "Revenue metrics show a strong upward trend with a 15% WoW increase. Key drivers include the Enterprise plan adoption and expansion in the EMEA region.",
      },
      {
        id: "product",
        name: "Product Agent",
        confidence: 0.85,
        content:
          "User engagement metrics are stable. However, the new 'Export' feature has a high error rate (5%) which might be impacting customer satisfaction scores.",
      },
      {
        id: "support",
        name: "Support Agent",
        confidence: 0.45,
        flagged: true,
        warnings: ["Missing data for dates: 2023-11-10 to 2023-11-30"],
        content:
          "Support ticket volume analysis is inconclusive due to missing data logs. Partial data suggests an uptick in billing-related inquiries.",
      },
      {
        id: "synthesizer",
        name: "Synthesizer",
        confidence: 0.68,
        content:
          "Synthesized View: While revenue is growing, the stability of the platform is in question due to Product errors and Support data gaps. The correlation between the Export feature errors and billing tickets requires investigation.",
      },
    ],
  },
  {
    id: "46",
    riskScore: 0.82,
    timestamp: "12 min ago",
    reason: "Compliance violation detected",
    session: "def-456",
    week: "Week 8",
    primaryAgent: "Governance",
    summary:
      "Governance agent flagged potential PII leakage in the customer feedback analysis. Specific user emails were found in the sentiment analysis logs.",
    status: "pending",
    agentOutputs: [
      {
        id: "governance",
        name: "Governance Agent",
        confidence: 0.99,
        flagged: true,
        warnings: ["PII Pattern Detected: Email Address"],
        content:
          "Found 3 instances of email addresses in the unstructured text analysis. Recommended Action: Redact and re-run.",
      },
    ],
  },
  {
    id: "44",
    riskScore: 0.3,
    timestamp: "25 min ago",
    reason: "Routine check",
    session: "xyz-789",
    week: "Week 7",
    primaryAgent: "Synthesizer",
    summary: "Standard weekly report generation. No anomalies detected. Confidence scores are high across all agents.",
    status: "approved",
    decision: {
      action: "approve",
      timestamp: "2023-11-22T10:00:00Z",
    },
    agentOutputs: [],
  },
]
