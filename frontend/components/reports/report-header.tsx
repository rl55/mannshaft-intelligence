import { Badge } from "@/components/ui/badge"
import type { ConfidenceLevel } from "@/lib/report-types"
import { CheckCircle2, AlertCircle, Clock } from "lucide-react"

interface ReportHeaderProps {
  week: string
  date: string
  qualityScore: number
  confidence: ConfidenceLevel
  executionTime: string
}

export function ReportHeader({ week, date, qualityScore, confidence, executionTime }: ReportHeaderProps) {
  const getConfidenceColor = (level: ConfidenceLevel) => {
    switch (level) {
      case "high":
        return "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20"
      case "medium":
        return "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20"
      case "low":
        return "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20"
    }
  }

  const getQualityColor = (score: number) => {
    if (score >= 90) return "text-green-600 dark:text-green-400"
    if (score >= 70) return "text-yellow-600 dark:text-yellow-400"
    return "text-red-600 dark:text-red-400"
  }

  return (
    <div className="border-b bg-card">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">SaaS BI Intelligence Report</h1>
            <p className="text-muted-foreground text-sm">
              {week} | {date}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-sm font-medium">Quality Score:</span>
              <span className={`text-lg font-bold ${getQualityColor(qualityScore)}`}>{qualityScore}%</span>
            </div>

            <Badge variant="outline" className={getConfidenceColor(confidence)}>
              <AlertCircle className="h-3 w-3" />
              Confidence: {confidence.charAt(0).toUpperCase() + confidence.slice(1)}
            </Badge>

            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              {executionTime}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
