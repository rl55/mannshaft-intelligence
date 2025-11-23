"use client"

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { InsightSection } from "@/lib/report-types"
import { MetricTooltip } from "./metric-tooltip"
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface InsightsGridProps {
  insights: InsightSection[]
}

export function InsightsGrid({ insights }: InsightsGridProps) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {insights.map((section) => (
        <Card key={section.id} className="overflow-hidden">
          <CardHeader className="bg-muted/50 pb-4">
            <CardTitle className="flex items-center gap-2 text-base font-medium">
              <span>{section.icon}</span>
              {section.title}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="border-b p-4">
              <div className="grid gap-4">
                {section.metrics.map((metric, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{metric.label}</span>
                    <div className="flex items-center gap-2 font-medium">
                      <span>{metric.value}</span>
                      {metric.change && (
                        <span
                          className={cn(
                            "flex items-center text-xs",
                            metric.trend === "up"
                              ? "text-green-600 dark:text-green-400"
                              : metric.trend === "down"
                                ? "text-red-600 dark:text-red-400"
                                : "text-muted-foreground",
                          )}
                        >
                          {metric.trend === "up" && <ArrowUpRight className="mr-0.5 h-3 w-3" />}
                          {metric.trend === "down" && <ArrowDownRight className="mr-0.5 h-3 w-3" />}
                          {metric.trend === "neutral" && <ArrowRight className="mr-0.5 h-3 w-3" />}
                          {metric.change}
                        </span>
                      )}
                      <MetricTooltip source={metric.source} confidence={metric.confidence} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="details" className="border-0">
                <AccordionTrigger className="px-4 py-3 text-xs text-muted-foreground hover:no-underline">
                  View Detailed Analysis
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <div className="bg-muted/50 rounded-md p-3 text-sm font-mono text-xs overflow-x-auto">
                    {section.details ? (
                      <pre className="whitespace-pre-wrap">{section.details}</pre>
                    ) : (
                      <p className="text-muted-foreground italic">No detailed logs available.</p>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
