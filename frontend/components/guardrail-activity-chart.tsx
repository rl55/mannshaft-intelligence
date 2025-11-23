"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import { Shield } from "lucide-react"

const data = [
  { name: "Pass", value: 1185, color: "#22c55e" }, // Success
  { name: "Warn", value: 50, color: "#eab308" }, // Warning
  { name: "Block", value: 12, color: "#ef4444" }, // Danger
]

const chartConfig = {
  pass: {
    label: "Pass",
    color: "#22c55e",
  },
  warning: {
    label: "Warning",
    color: "#eab308",
  },
  block: {
    label: "Block",
    color: "#ef4444",
  },
}

export function GuardrailActivityChart() {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="p-6">
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          Guardrail Activity
        </CardTitle>
        <CardDescription>Security checks in the last 7 days</CardDescription>
      </CardHeader>
      <CardContent className="p-6 pt-0">
        <ChartContainer config={chartConfig} className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={2} dataKey="value">
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={0} />
                ))}
              </Pie>
              <ChartTooltip cursor={false} content={<ChartTooltipContent hideLabel />} />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>

        <div className="mt-4 grid grid-cols-3 gap-4 text-center text-sm">
          <div>
            <p className="text-2xl font-bold text-[#22c55e]">{data[0].value}</p>
            <p className="text-muted-foreground">Passed</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-[#eab308]">{data[1].value}</p>
            <p className="text-muted-foreground">Warnings</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-[#ef4444]">{data[2].value}</p>
            <p className="text-muted-foreground">Blocked</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
