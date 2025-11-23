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
  { name: "Critical", value: 0 },
  { name: "High", value: 2 },
  { name: "Medium", value: 10 },
  { name: "Low", value: 6 },
]

// Filter out zero values for better visualization if needed, or keep to show empty
const activeData = data.filter((d) => d.value > 0)

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
                {activeData.map((entry, index) => (
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
