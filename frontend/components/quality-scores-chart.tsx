"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { Star } from "lucide-react"

const data = [
  { day: "Mon", score: 89 },
  { day: "Tue", score: 91 },
  { day: "Wed", score: 88 },
  { day: "Thu", score: 93 },
  { day: "Fri", score: 95 },
  { day: "Sat", score: 92 },
  { day: "Sun", score: 94 },
]

const chartConfig = {
  score: {
    label: "Quality Score",
    color: "#3b82f6",
  },
}

export function QualityScoresChart() {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="p-6">
        <CardTitle className="flex items-center gap-2">
          <Star className="h-5 w-5 text-primary" />
          Quality Scores
        </CardTitle>
        <CardDescription>Response quality trend over time</CardDescription>
      </CardHeader>
      <CardContent className="p-6 pt-0">
        <ChartContainer config={chartConfig} className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted/50" vertical={false} />
              <XAxis
                dataKey="day"
                className="text-xs"
                tickLine={false}
                axisLine={false}
                tick={{ fill: "hsl(var(--muted-foreground))" }}
              />
              <YAxis
                domain={[80, 100]}
                className="text-xs"
                tickLine={false}
                axisLine={false}
                tick={{ fill: "hsl(var(--muted-foreground))" }}
              />
              <ChartTooltip content={<ChartTooltipContent indicator="line" />} />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#3b82f6"
                strokeWidth={3}
                dot={{ fill: "#3b82f6", r: 4, strokeWidth: 2, stroke: "hsl(var(--background))" }}
                activeDot={{ r: 6, strokeWidth: 2, stroke: "hsl(var(--background))" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>

        <div className="mt-4 flex justify-center gap-8 text-sm border-t pt-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-[#3b82f6]">93.6%</p>
            <p className="text-muted-foreground">Avg Score</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-[#22c55e]">+2.3%</p>
            <p className="text-muted-foreground">vs Last Week</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
