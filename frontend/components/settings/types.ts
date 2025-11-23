export interface SystemSettings {
  general: {
    analysisType: "comprehensive" | "fast" | "deep"
    cacheTtl: {
      prompts: number
      agents: number
      evaluations: number
    }
    hitlMode: "production" | "demo"
    notifications: {
      email: boolean
      slack: boolean
      desktop: boolean
    }
  }
  agents: {
    model: string
    confidenceThreshold: number
    parallelExecution: boolean
  }
  guardrails: {
    hardRules: {
      piiDetection: boolean
      costLimit: number
    }
    adaptiveRules: {
      lowConfidence: {
        enabled: boolean
        threshold: number
      }
      dataCompleteness: {
        enabled: boolean
        minWeeks: number
      }
      anomalyDetection: {
        enabled: boolean
      }
    }
  }
  integrations: {
    googleSheets: {
      connected: boolean
      account: string
      sheets: {
        revenue: string
        product: string
        support: string
      }
      refreshInterval: number
    }
  }
  api: {
    webhookUrl: string
    apiKey: string
  }
}
