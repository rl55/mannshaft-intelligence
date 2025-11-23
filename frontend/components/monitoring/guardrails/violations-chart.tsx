"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"

const data = Array.from({ length: 14 }, (_, i) => ({
  day: `Day ${i + 1}`,
  violations: Math.floor(Math.random() * 5) + 1, // Random small number
}))

const chartConfig = {
  violations: {
    label: "Violations",
    color: "hsl(var(--destructive))",
  },
}

export function ViolationsChart() {
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
            <span className="text-green-500 font-medium">↓ Decreasing</span>
          </div>
        </div>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" vertical={false} />
              <XAxis
                dataKey="day"
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                interval={2}
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
