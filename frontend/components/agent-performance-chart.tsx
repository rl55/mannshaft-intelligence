"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { Zap } from "lucide-react"

const data = [
  { name: "Mon", revenue: 2.1, product: 1.8, support: 2.5 },
  { name: "Tue", revenue: 1.9, product: 2.2, support: 2.1 },
  { name: "Wed", revenue: 2.3, product: 1.9, support: 2.4 },
  { name: "Thu", revenue: 2.0, product: 2.1, support: 1.9 },
  { name: "Fri", revenue: 1.8, product: 2.3, support: 2.2 },
  { name: "Sat", revenue: 2.2, product: 1.7, support: 2.0 },
  { name: "Sun", revenue: 2.1, product: 2.0, support: 2.3 },
]

const chartConfig = {
  revenue: {
    label: "Revenue Agent",
    color: "#3b82f6", // Blue
  },
  product: {
    label: "Product Agent",
    color: "#22c55e", // Green
  },
  support: {
    label: "Support Agent",
    color: "#eab308", // Warning/Yellow
  },
}

export function AgentPerformanceChart() {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="p-6">
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-primary" />
          Agent Performance
        </CardTitle>
        <CardDescription>Response times over the last 7 days</CardDescription>
      </CardHeader>
      <CardContent className="p-6 pt-0">
        <ChartContainer config={chartConfig} className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted/50" vertical={false} />
              <XAxis
                dataKey="name"
                className="text-xs"
                tickLine={false}
                axisLine={false}
                tick={{ fill: "hsl(var(--muted-foreground))" }}
              />
              <YAxis
                className="text-xs"
                tickLine={false}
                axisLine={false}
                tick={{ fill: "hsl(var(--muted-foreground))" }}
              />
              <ChartTooltip
                cursor={{ fill: "hsl(var(--muted)/0.2)" }}
                content={<ChartTooltipContent indicator="dashed" />}
              />
              <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="product" fill="#22c55e" radius={[4, 4, 0, 0]} />
              <Bar dataKey="support" fill="#eab308" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-6 text-sm border-t pt-4">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Avg Time:</span>
            <span className="font-bold text-foreground">2.1s</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Cache Hit:</span>
            <span className="font-bold text-[#22c55e]">78%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Success:</span>
            <span className="font-bold text-[#3b82f6]">98%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
