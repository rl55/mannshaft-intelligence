import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Correlation } from "@/lib/report-types"
import { BrainCircuit, ArrowRight } from "lucide-react"

interface CorrelationMatrixProps {
  correlations: Correlation[]
}

export function CorrelationMatrix({ correlations }: CorrelationMatrixProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5 text-primary" />
          Cross-Functional Correlations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {correlations.map((correlation) => (
            <div
              key={correlation.id}
              className="flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between bg-muted/20"
            >
              <div className="flex items-start gap-3 sm:items-center">
                <div className="mt-0.5 sm:mt-0">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    {correlation.description.split("→").map((part, i, arr) => (
                      <span key={i} className="flex items-center">
                        {part.trim()}
                        {i < arr.length - 1 && <ArrowRight className="mx-2 h-3 w-3 text-muted-foreground" />}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{correlation.impact}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-xs font-medium text-muted-foreground whitespace-nowrap">
                  Correlation: {correlation.strength}
                </div>
                <div className="h-2 w-24 overflow-hidden rounded-full bg-secondary">
                  <div className="h-full bg-primary" style={{ width: `${Math.abs(correlation.strength) * 100}%` }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
