"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, LabelList } from "recharts"

const data = [
  { agent: "Revenue", hits: 1200 },
  { agent: "Product", hits: 980 },
  { agent: "Synthesizer", hits: 650 },
]

const chartConfig = {
  hits: {
    label: "Cache Hits",
    color: "hsl(var(--chart-4))",
  },
}

export function TopCachedAgentsChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Cached Agents</CardTitle>
        <CardDescription>Agents with most cache hits</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 0, right: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} className="stroke-muted" />
              <XAxis type="number" hide />
              <YAxis
                dataKey="agent"
                type="category"
                tickLine={false}
                axisLine={false}
                className="text-sm font-medium"
                width={80}
              />
              <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: "transparent" }} />
              <Bar dataKey="hits" fill="var(--color-hits)" radius={[0, 4, 4, 0]} barSize={32}>
                <LabelList
                  dataKey="hits"
                  position="right"
                  className="fill-foreground text-xs"
                  formatter={(value: number) => value.toLocaleString()}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
