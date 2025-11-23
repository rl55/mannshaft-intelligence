"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { apiClient } from "@/lib/api"

const chartConfig = {
  hitRate: {
    label: "Hit Rate %",
    color: "hsl(var(--chart-1))",
  },
}

export function CacheHitRateChart() {
  const [data, setData] = useState<Array<{ day: string; hitRate: number }>>([])
  const [avgHitRate, setAvgHitRate] = useState<number>(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.getCacheHitRateOverTime(30, true)
        const chartData = response.data.map((point, index) => ({
          day: `Day ${index + 1}`,
          hitRate: Math.round(point.hit_rate * 100),
          date: point.date,
        }))
        setData(chartData)
        
        // Calculate average hit rate
        const avg = chartData.reduce((sum, d) => sum + d.hitRate, 0) / chartData.length
        setAvgHitRate(Math.round(avg))
      } catch (error) {
        console.error("Error fetching cache hit rate data:", error)
        // Fallback to empty data
        setData([])
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cache Hit Rate Over Time</CardTitle>
          <CardDescription>Daily hit rate % for last 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            Loading...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cache Hit Rate Over Time</CardTitle>
          <CardDescription>Daily hit rate % for last 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            No data available
          </div>
        </CardContent>
      </Card>
    )
  }

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
            <span className="font-medium">{avgHitRate}%</span>
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
                interval={Math.max(0, Math.floor(data.length / 6) - 1)}
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
              <Line 
                type="monotone" 
                dataKey="hitRate" 
                stroke="var(--color-hitRate)" 
                strokeWidth={2} 
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
