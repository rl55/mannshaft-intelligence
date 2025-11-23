"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"

const data = Array.from({ length: 30 }, (_, i) => ({
  day: `Day ${i + 1}`,
  hitRate: Math.floor(Math.random() * (85 - 65 + 1)) + 65, // Random between 65 and 85
}))

const chartConfig = {
  hitRate: {
    label: "Hit Rate %",
    color: "hsl(var(--chart-1))",
  },
}

export function CacheHitRateChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Cache Hit Rate Over Time</CardTitle>
        <CardDescription>Daily hit rate % for last 30 days</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Trend:</span>
            <span className="text-green-500 font-medium">↑ Improving</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Avg:</span>
            <span className="font-medium">75%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Target:</span>
            <span className="font-medium">80%</span>
          </div>
        </div>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" vertical={false} />
              <XAxis
                dataKey="day"
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                interval={4}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={false}
                domain={[0, 100]}
                unit="%"
              />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Line type="monotone" dataKey="hitRate" stroke="var(--color-hitRate)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
