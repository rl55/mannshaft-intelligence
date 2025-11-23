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

const data = [
  { name: "Prompt", value: 45 },
  { name: "Agent", value: 35 },
  { name: "Eval", value: 20 },
]

const chartConfig = {
  Prompt: {
    label: "Prompt",
    color: "hsl(var(--chart-1))",
  },
  Agent: {
    label: "Agent",
    color: "hsl(var(--chart-2))",
  },
  Eval: {
    label: "Eval",
    color: "hsl(var(--chart-3))",
  },
}

export function CacheTypeChart() {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Cache by Type</CardTitle>
        <CardDescription>Distribution of cache entries</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 pb-0">
        <ChartContainer config={chartConfig} className="mx-auto aspect-square max-h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" innerRadius={60} strokeWidth={5}>
                {data.map((entry, index) => (
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
