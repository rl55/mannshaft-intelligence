"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, LabelList } from "recharts"
import { apiClient } from "@/lib/api"

const chartConfig = {
  hits: {
    label: "Cache Hits",
    color: "hsl(var(--chart-4))",
  },
}

export function TopCachedAgentsChart() {
  const [data, setData] = useState<Array<{ agent: string; hits: number }>>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.getTopCachedAgents(5, true)
        const chartData = response.agents.map((agent) => ({
          agent: agent.agent_type,
          hits: agent.cache_hits,
        }))
        setData(chartData)
      } catch (error) {
        console.error("Error fetching top cached agents:", error)
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
          <CardTitle>Top Cached Agents</CardTitle>
          <CardDescription>Agents with most cache hits</CardDescription>
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
          <CardTitle>Top Cached Agents</CardTitle>
          <CardDescription>Agents with most cache hits</CardDescription>
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
