"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart3, CheckCircle2 } from "lucide-react"

export function LatestAnalysisCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <BarChart3 className="h-5 w-5 text-primary" />
          Latest Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Week 8 Analysis</span>
          <Badge variant="secondary" className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Completed
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Quality Score</p>
            <p className="text-2xl font-bold text-primary">94%</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Avg Time</p>
            <p className="text-2xl font-bold">3.2s</p>
          </div>
        </div>

        <div className="pt-2 text-xs text-muted-foreground">Completed 2 hours ago</div>
      </CardContent>
    </Card>
  )
}
