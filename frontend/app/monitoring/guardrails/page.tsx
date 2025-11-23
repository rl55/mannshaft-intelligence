"use client"

import { GuardrailMetrics } from "@/components/monitoring/guardrails/guardrail-metrics"
import { ViolationsChart } from "@/components/monitoring/guardrails/violations-chart"
import { SeverityDistributionChart } from "@/components/monitoring/guardrails/severity-distribution-chart"
import { GuardrailEffectivenessTable } from "@/components/monitoring/guardrails/guardrail-effectiveness-table"
import { RecentViolationsTable } from "@/components/monitoring/guardrails/recent-violations-table"
import { AdaptiveRulesTable } from "@/components/monitoring/guardrails/adaptive-rules-table"
import { Button } from "@/components/ui/button"
import { CalendarIcon, Download, Shield } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export default function GuardrailMonitoringPage() {
  return (
    <div className="p-8 space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Guardrail Monitoring</h1>
          <p className="text-muted-foreground">Real-time supervision of agent behavior and compliance checks.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="gap-2 bg-transparent">
            <CalendarIcon className="h-4 w-4" />
            Last 30 Days
          </Button>
          <Button variant="outline" size="icon">
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        <Alert className="bg-blue-50/50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <Shield className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          <AlertTitle className="text-blue-800 dark:text-blue-300">Weekly Insight</AlertTitle>
          <AlertDescription className="text-blue-700 dark:text-blue-400">
            Guardrails blocked 2 potential PII leakages this week. False positive rate decreased by 10%.
          </AlertDescription>
        </Alert>
      </div>

      <GuardrailMetrics />

      <div className="grid gap-4 md:grid-cols-7">
        <div className="md:col-span-4">
          <GuardrailEffectivenessTable />
        </div>
        <div className="md:col-span-3">
          <SeverityDistributionChart />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-1">
        <ViolationsChart />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <RecentViolationsTable />
        <AdaptiveRulesTable />
      </div>
    </div>
  )
}
