"use client"

import { Suspense } from "react"
import { QuickActionsCard } from "@/components/quick-actions-card"
import { LatestAnalysisCard } from "@/components/latest-analysis-card"
import { AgentPerformanceChart } from "@/components/agent-performance-chart"
import { GuardrailActivityChart } from "@/components/guardrail-activity-chart"
import { QualityScoresChart } from "@/components/quality-scores-chart"
import { GeminiUsageCard } from "@/components/gemini-usage-card"
import { AnalysisView } from "@/components/analysis/analysis-view"
import { EnhancedAnalysisView } from "@/components/analysis/enhanced-analysis-view"
import { ThemeToggle } from "@/components/theme-toggle"
import { Bell } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useState, useEffect } from "react"
import { useAnalysisStore } from "@/store/analysis-store"

export default function DashboardPage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisWeek, setAnalysisWeek] = useState("8")
  const [sessionId, setSessionId] = useState<string | null>(null)
  const { currentSession, triggerAnalysis } = useAnalysisStore()

  const handleStartAnalysis = async (week: string) => {
    setAnalysisWeek(week)
    setIsAnalyzing(true)
    
    try {
      const response = await triggerAnalysis(
        parseInt(week),
        'comprehensive',
        'demo_user'
      )
      setSessionId(response.session_id)
    } catch (error) {
      setIsAnalyzing(false)
      // Error is handled by the store/API client
    }
  }

  // Update sessionId when currentSession changes
  useEffect(() => {
    if (currentSession?.session_id) {
      setSessionId(currentSession.session_id)
    }
  }, [currentSession])

  return (
    <div className="flex flex-1 flex-col">
      <header className="sticky top-0 z-10 flex h-16 items-center border-b bg-background px-6">
        <div className="flex items-center gap-4 flex-1">
          <h1 className="text-xl font-semibold">Dashboard</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="h-9 w-9">
            <Bell className="h-4 w-4" />
          </Button>
          <ThemeToggle />
          <Avatar className="h-8 w-8">
            <AvatarImage src="/placeholder-user.jpg" />
            <AvatarFallback>DU</AvatarFallback>
          </Avatar>
        </div>
      </header>

      <main className="flex-1 p-6 overflow-auto">
        <div className="space-y-6">
          {isAnalyzing && sessionId ? (
            <Suspense fallback={<div>Loading analysis...</div>}>
              <EnhancedAnalysisView
                sessionId={sessionId}
                weekId={analysisWeek}
                onClose={() => {
                  setIsAnalyzing(false)
                  setSessionId(null)
                }}
              />
            </Suspense>
          ) : (
            <>
              {/* Row 1: Quick Actions + Latest Analysis */}
              <div className="grid gap-6 md:grid-cols-2">
                <QuickActionsCard onTrigger={handleStartAnalysis} />
                <LatestAnalysisCard />
              </div>

              {/* Row 2: Agent Performance (Full Width) */}
              <Suspense fallback={<div>Loading chart...</div>}>
                <AgentPerformanceChart />
              </Suspense>

              {/* Row 3: Guardrails + Quality Scores */}
              <div className="grid gap-6 md:grid-cols-2">
                <Suspense fallback={<div>Loading chart...</div>}>
                  <GuardrailActivityChart />
                </Suspense>
                <Suspense fallback={<div>Loading chart...</div>}>
                  <QualityScoresChart />
                </Suspense>
              </div>

              {/* Row 4: Gemini Usage (Full Width) */}
              <Suspense fallback={<div>Loading chart...</div>}>
                <GeminiUsageCard />
              </Suspense>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
