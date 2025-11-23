import type { SystemSettings } from "./types"

export const defaultSettings: SystemSettings = {
  general: {
    analysisType: "comprehensive",
    cacheTtl: {
      prompts: 168,
      agents: 24,
      evaluations: 168,
    },
    hitlMode: "production",
    notifications: {
      email: true,
      slack: true,
      desktop: false,
    },
  },
  agents: {
    model: "gemini-2.0-flash-exp",
    confidenceThreshold: 0.7,
    parallelExecution: true,
  },
  guardrails: {
    hardRules: {
      piiDetection: true,
      costLimit: 0.5,
    },
    adaptiveRules: {
      lowConfidence: {
        enabled: true,
        threshold: 0.7,
      },
      dataCompleteness: {
        enabled: true,
        minWeeks: 6,
      },
      anomalyDetection: {
        enabled: false,
      },
    },
  },
  integrations: {
    googleSheets: {
      connected: true,
      account: "demo@mannshaft.ai",
      sheets: {
        revenue: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74DgvE",
        product: "1dI-8_5jFe5nFMdKvBdBZjgmUUqptlbs74DgvE",
        support: "19-72jFe5nFMdKvBdBZjgmUUqptlbs74DgvE",
      },
      refreshInterval: 60, // minutes
    },
  },
  api: {
    webhookUrl: "https://api.example.com/webhooks/v1/analysis",
    apiKey: "sk_live_51M...",
  },
}
