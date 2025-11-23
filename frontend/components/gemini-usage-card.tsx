"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { DollarSign } from "lucide-react"

const data = [
  { day: "Mon", cost: 0.18 },
  { day: "Tue", cost: 0.22 },
  { day: "Wed", cost: 0.19 },
  { day: "Thu", cost: 0.25 },
  { day: "Fri", cost: 0.21 },
  { day: "Sat", cost: 0.15 },
  { day: "Sun", cost: 0.12 },
]

const chartConfig = {
  cost: {
    label: "Daily Cost",
    color: "#3b82f6", // Blue
  },
}

export function GeminiUsageCard() {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="p-6">
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-primary" />
          Gemini API Usage
        </CardTitle>
        <CardDescription>Cost tracking and token usage</CardDescription>
      </CardHeader>
      <CardContent className="p-6 pt-0">
        <div className="mb-6 grid grid-cols-3 gap-4">
          <div className="bg-muted/30 p-3 rounded-lg border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">Today</p>
            <p className="text-2xl font-bold text-[#3b82f6]">$0.12</p>
          </div>
          <div className="bg-muted/30 p-3 rounded-lg border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">This Week</p>
            <p className="text-2xl font-bold text-foreground">$1.45</p>
          </div>
          <div className="bg-muted/30 p-3 rounded-lg border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">Tokens</p>
            <p className="text-2xl font-bold text-foreground">125K</p>
          </div>
        </div>

        <ChartContainer config={chartConfig} className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted/50" vertical={false} />
              <XAxis
                dataKey="day"
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
                tickFormatter={(value) => `$${value}`}
              />
              <ChartTooltip content={<ChartTooltipContent formatter={(value) => `$${value}`} />} />
              <Area type="monotone" dataKey="cost" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartContainer>

        <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground border-t pt-4">
          <span>Usage vs Limit</span>
          <span className="font-medium text-foreground">12% used</span>
        </div>
      </CardContent>
    </Card>
  )
}
