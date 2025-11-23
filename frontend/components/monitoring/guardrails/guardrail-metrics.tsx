"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ShieldCheck, AlertTriangle, UserCheck } from "lucide-react"
import { apiClient } from "@/lib/api"
import { useQuery } from "@tanstack/react-query"

export function GuardrailMetrics() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["guardrail-stats"],
    queryFn: () => apiClient.getGuardrailStats(7),
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const { data: hitlStats } = useQuery({
    queryKey: ["hitl-stats"],
    queryFn: () => apiClient.getHITLStats(7),
    refetchInterval: 30000,
  })

  if (isLoading) {
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

  const totalChecks = stats?.total_checks || 0
  const violations = stats?.violations || 0
  const violationRate = stats?.violation_rate || 0
  const hitlReviews = hitlStats?.pending || 0

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Checks</CardTitle>
          <ShieldCheck className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalChecks.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <span className="text-muted-foreground">Last 7 days</span>
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Violations</CardTitle>
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {violations} <span className="text-sm font-normal text-muted-foreground">
              ({violationRate > 0 ? (violationRate * 100).toFixed(1) : "0.0"}%)
            </span>
          </div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <span className="text-muted-foreground">Last 7 days</span>
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">HITL Reviews</CardTitle>
          <UserCheck className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{hitlReviews}</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <span className="text-muted-foreground">Pending reviews</span>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
