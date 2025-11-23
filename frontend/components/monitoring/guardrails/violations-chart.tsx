"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { apiClient } from "@/lib/api"
import { useQuery } from "@tanstack/react-query"
import { format } from "date-fns"

const chartConfig = {
  violations: {
    label: "Violations",
    color: "hsl(var(--destructive))",
  },
}

export function ViolationsChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["guardrail-violations-over-time"],
    queryFn: () => apiClient.getGuardrailViolationsOverTime(14),
    refetchInterval: 60000, // Refetch every minute
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Violations Over Time</CardTitle>
          <CardDescription>Daily violation trend for the last 2 weeks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const chartData = (data?.data || []).map((point: any) => ({
    day: format(new Date(point.date), "MMM d"),
    violations: point.violations,
  }))

  // Calculate trend
  const violations = chartData.map((d: any) => d.violations)
  const firstHalf = violations.slice(0, Math.floor(violations.length / 2))
  const secondHalf = violations.slice(Math.floor(violations.length / 2))
  const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length || 0
  const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length || 0
  const trend = secondAvg < firstAvg ? "↓ Decreasing" : secondAvg > firstAvg ? "↑ Increasing" : "→ Stable"
  const trendColor = secondAvg < firstAvg ? "text-green-500" : secondAvg > firstAvg ? "text-red-500" : "text-muted-foreground"

  return (
    <Card>
      <CardHeader>
        <CardTitle>Violations Over Time</CardTitle>
        <CardDescription>Daily violation trend for the last 2 weeks</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Trend:</span>
            <span className={`font-medium ${trendColor}`}>{trend}</span>
          </div>
        </div>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" vertical={false} />
              <XAxis
                dataKey="day"
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                interval={Math.floor(chartData.length / 7)}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Area
                type="monotone"
                dataKey="violations"
                stroke="var(--color-violations)"
                fill="var(--color-violations)"
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
