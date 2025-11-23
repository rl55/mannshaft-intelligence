"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowUp, Zap, Database, DollarSign } from "lucide-react"
import { apiClient } from "@/lib/api"

export function CacheMetricsCards() {
  const [hitRate, setHitRate] = useState<number>(0)
  const [tokensSaved, setTokensSaved] = useState<number>(0)
  const [costSaved, setCostSaved] = useState<number>(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const stats = await apiClient.getCacheStats(true)
        setHitRate(Math.round(stats.cache_hit_rate * 100))
        setTokensSaved(stats.total_tokens_saved)
        // Estimate cost saved: $0.00025 per 1K tokens (approximate Gemini pricing)
        setCostSaved((stats.total_tokens_saved / 1000) * 0.00025)
      } catch (error) {
        console.error("Error fetching cache stats:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Hit Rate</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{hitRate}%</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <ArrowUp className="mr-1 h-4 w-4 text-green-500" />
            <span className="text-green-500 font-medium">Real-time</span>
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Tokens Saved</CardTitle>
          <Database className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {tokensSaved >= 1000 ? `${(tokensSaved / 1000).toFixed(0)}K` : tokensSaved.toLocaleString()}
          </div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <ArrowUp className="mr-1 h-4 w-4 text-green-500" />
            <span className="text-green-500 font-medium">Real-time</span>
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Cost Saved</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">${costSaved.toFixed(2)}</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <ArrowUp className="mr-1 h-4 w-4 text-green-500" />
            <span className="text-green-500 font-medium">Real-time</span>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
