"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import { apiClient } from "@/lib/api"
import { useQuery } from "@tanstack/react-query"

const chartConfig = {
  Critical: {
    label: "Critical",
    color: "hsl(var(--destructive))",
  },
  High: {
    label: "High",
    color: "hsl(30 100% 50%)", // Orange
  },
  Medium: {
    label: "Medium",
    color: "hsl(48 100% 50%)", // Yellow
  },
  Low: {
    label: "Low",
    color: "hsl(var(--chart-2))", // Blue/Green
  },
}

export function SeverityDistributionChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["guardrail-severity-distribution"],
    queryFn: () => apiClient.getGuardrailSeverityDistribution(30),
    refetchInterval: 60000, // Refetch every minute
  })

  if (isLoading) {
    return (
      <Card className="flex flex-col">
        <CardHeader>
          <CardTitle>Violations by Severity</CardTitle>
          <CardDescription>Distribution by risk level</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 pb-0">
          <div className="h-[300px] flex items-center justify-center">
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const distribution = data?.distribution || []
  const activeData = distribution.filter((d: any) => d.value > 0)

  if (activeData.length === 0) {
    return (
      <Card className="flex flex-col">
        <CardHeader>
          <CardTitle>Violations by Severity</CardTitle>
          <CardDescription>Distribution by risk level</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 pb-0">
          <div className="h-[300px] flex items-center justify-center">
            <p className="text-muted-foreground">No violations found</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Violations by Severity</CardTitle>
        <CardDescription>Distribution by risk level</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 pb-0">
        <ChartContainer config={chartConfig} className="mx-auto aspect-square max-h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={activeData} dataKey="value" nameKey="name" innerRadius={60} strokeWidth={5}>
                {activeData.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={`var(--color-${entry.name})`} />
                ))}
              </Pie>
              <ChartTooltip content={<ChartTooltipContent hideLabel />} />
              <ChartLegend
                content={<ChartLegendContent nameKey="name" />}
                className="-translate-y-2 flex-wrap gap-2 [&>*]:basis-1/4 [&>*]:justify-center"
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
