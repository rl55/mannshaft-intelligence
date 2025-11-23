"use client"

import { CacheMetricsCards } from "@/components/monitoring/cache-metrics-cards"
import { CacheHitRateChart } from "@/components/monitoring/cache-hit-rate-chart"
import { CacheTypeChart } from "@/components/monitoring/cache-type-chart"
import { TopCachedAgentsChart } from "@/components/monitoring/top-cached-agents-chart"
import { CacheEntriesTable } from "@/components/monitoring/cache-entries-table"
import { Button } from "@/components/ui/button"
import { RefreshCw, Trash2 } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertTriangle } from "lucide-react"

export default function CacheMonitoringPage() {
  return (
    <div className="flex flex-1 flex-col">
      <header className="sticky top-0 z-10 flex h-16 items-center border-b bg-background px-6">
        <h1 className="text-xl font-semibold">Session History</h1>
      </header>
      <main className="flex-1 p-6 overflow-auto">

        <div className="p-8 space-y-8">
          <div className="flex flex-col space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">Cache Performance Dashboard</h1>
            <p className="text-muted-foreground">Monitor cache efficiency, hit rates, and storage optimization.</p>
          </div>

          {/* Alerts Section */}
          <div className="space-y-4">
            {/* Mock Alert: Hit Rate Warning (Hidden by default unless condition met, showing generic insight here) */}
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Optimization Insight</AlertTitle>
              <AlertDescription>
                Consider increasing TTL for stable prompts. Agent cache hit rate dropped 5% in the last hour.
              </AlertDescription>
            </Alert>
          </div>

          <CacheMetricsCards />

          <div className="grid gap-4 md:grid-cols-7">
            <div className="md:col-span-4">
              <CacheHitRateChart />
            </div>
            <div className="md:col-span-3 space-y-4">
              <CacheTypeChart />
              <TopCachedAgentsChart />
            </div>
          </div>

          <CacheEntriesTable />

          <div className="flex items-center justify-between border-t pt-4">
            <p className="text-sm text-muted-foreground">Last updated: Just now</p>
            <div className="flex gap-4">
              <Button variant="outline" className="gap-2 bg-transparent">
                <RefreshCw className="h-4 w-4" />
                Refresh Stats
              </Button>
              <Button variant="destructive" className="gap-2">
                <Trash2 className="h-4 w-4" />
                Clear All Cache
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>        
  )
}
