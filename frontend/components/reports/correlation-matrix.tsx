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
          {correlations.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No correlations identified for this period.</p>
          ) : (
            correlations.map((correlation) => {
              // Ensure we have a description, fallback to impact if description is empty
              const description = correlation.description || correlation.impact || "Correlation identified"
              const hasArrow = description.includes("→") || description.includes("->")
              
              return (
                <div
                  key={correlation.id}
                  className="rounded-lg border p-4 bg-muted/20 hover:bg-muted/30 transition-colors"
                >
                  <div className="flex flex-col gap-3">
                    {/* Correlation Description */}
                    <div className="flex items-start gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                          {hasArrow ? (
                            description.split(/→|->/).map((part, i, arr) => (
                              <span key={i} className="flex items-center">
                                {part.trim()}
                                {i < arr.length - 1 && <ArrowRight className="mx-2 h-4 w-4 text-muted-foreground" />}
                              </span>
                            ))
                          ) : (
                            <span>{description}</span>
                          )}
                        </div>
                        {/* Impact Description - only show if different from description */}
                        {correlation.impact && correlation.impact !== description && (
                          <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                            {correlation.impact}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    {/* Correlation Strength */}
                    <div className="flex items-center justify-between gap-4 pt-2 border-t">
                      <div className="flex items-center gap-3 flex-1">
                        <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
                          Correlation:
                        </span>
                        <div className="flex-1 max-w-[200px]">
                          <div className="h-2 overflow-hidden rounded-full bg-secondary">
                            <div 
                              className="h-full bg-primary transition-all" 
                              style={{ width: `${Math.abs(typeof correlation.strength === 'number' ? correlation.strength : 0) * 100}%` }} 
                            />
                          </div>
                        </div>
                        <span className="text-xs font-semibold text-foreground min-w-[3rem]">
                          {typeof correlation.strength === 'number' ? correlation.strength.toFixed(2) : correlation.strength}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </CardContent>
    </Card>
  )
}
