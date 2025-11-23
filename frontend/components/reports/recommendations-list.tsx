import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Recommendation, PriorityLevel } from "@/lib/report-types"
import { Target, Calendar, TrendingUp } from "lucide-react"

interface RecommendationsListProps {
  recommendations: Recommendation[]
}

export function RecommendationsList({ recommendations }: RecommendationsListProps) {
  const getPriorityColor = (priority: PriorityLevel) => {
    switch (priority) {
      case "HIGH":
        return "destructive"
      case "MEDIUM":
        return "secondary" // Using secondary as closest to yellow/orange in standard shadcn or default
      case "LOW":
        return "outline"
      default:
        return "default"
    }
  }

  // Map MEDIUM to a custom style if needed, but secondary is safe.
  // Actually, let's use custom classes for better matching the requirements:
  // HIGH (red), MEDIUM (yellow), LOW (blue)

  const getPriorityBadgeClass = (priority: PriorityLevel) => {
    switch (priority) {
      case "HIGH":
        return "bg-red-500/15 text-red-700 dark:text-red-400 hover:bg-red-500/25 border-red-500/20 border"
      case "MEDIUM":
        return "bg-amber-500/15 text-amber-700 dark:text-amber-400 hover:bg-amber-500/25 border-amber-500/20 border"
      case "LOW":
        return "bg-blue-500/15 text-blue-700 dark:text-blue-400 hover:bg-blue-500/25 border-blue-500/20 border"
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" />
          Strategic Recommendations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <div key={rec.id} className="flex flex-col gap-3 rounded-lg border p-4 transition-colors hover:bg-muted/50">
              <div className="flex items-start justify-between gap-4">
                <h3 className="font-medium leading-none">{rec.title}</h3>
                <Badge variant="outline" className={getPriorityBadgeClass(rec.priority)}>
                  {rec.priority}
                </Badge>
              </div>

              <div className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>
                    Impact: <span className="text-foreground">{rec.impact}</span>
                  </span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-3.5 w-3.5" />
                  <span>
                    Timeline: <span className="text-foreground">{rec.timeline}</span>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
