"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Lightbulb } from "lucide-react"
import { SessionFilters } from "@/components/sessions/session-filters"
import { SessionList } from "@/components/sessions/session-list"
import { SessionDetailSheet } from "@/components/sessions/session-detail-sheet"
import { useAnalysisStore } from "@/store/analysis-store"
import { transformSessionToHistoryItem, transformToSessionDetail } from "@/lib/session-transform"
import type { SessionHistoryItem, SessionDetail } from "@/components/sessions/types"
import { toast } from "sonner"

export default function SessionsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [weekFilter, setWeekFilter] = useState("all")
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [sessions, setSessions] = useState<SessionHistoryItem[]>([])
  const [selectedSession, setSelectedSession] = useState<SessionDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { fetchSessions, getAnalysisResult } = useAnalysisStore()

  // Fetch sessions on mount
  useEffect(() => {
    const loadSessions = async () => {
      try {
        setIsLoading(true)
        const response = await fetchSessions(true)
        
        // Handle response - it might be the sessions array directly or an object with sessions property
        const sessionsArray = Array.isArray(response) 
          ? response 
          : (response?.sessions || [])
        
        // Transform sessions and fetch analysis results for completed ones
        const transformedSessions = await Promise.all(
          sessionsArray.map(async (session: any) => {
            try {
              // Try to get analysis result for completed sessions
              let analysisResult = null
              if (session.status === "completed") {
                try {
                  analysisResult = await getAnalysisResult(session.session_id)
                } catch (e) {
                  // Analysis result might not exist yet, that's okay
                  console.debug(`No analysis result for session ${session.session_id}`)
                }
              }
              
              return transformSessionToHistoryItem(session, analysisResult)
            } catch (error) {
              console.error(`Error transforming session ${session.session_id}:`, error)
              // Return basic session info even if transformation fails
              return transformSessionToHistoryItem(session)
            }
          })
        )
        
        setSessions(transformedSessions)
      } catch (error: any) {
        console.error("Error loading sessions:", error)
        toast.error("Failed to load sessions", {
          description: error.message || "Please try again later.",
        })
      } finally {
        setIsLoading(false)
      }
    }

    loadSessions()
  }, [fetchSessions, getAnalysisResult])

  // Load selected session details
  useEffect(() => {
    const loadSelectedSession = async () => {
      if (!selectedSessionId) {
        setSelectedSession(null)
        return
      }

      try {
        const sessionData = sessions.find(s => s.id === selectedSessionId)
        if (!sessionData) {
          setSelectedSession(null)
          return
        }

        // Fetch full session and analysis result
        const response = await fetchSessions(true)
        const sessionsArray = Array.isArray(response) 
          ? response 
          : (response?.sessions || [])
        const backendSession = sessionsArray.find((s: any) => s.session_id === selectedSessionId)
        
        if (backendSession) {
          let analysisResult = null
          if (backendSession.status === "completed") {
            try {
              analysisResult = await getAnalysisResult(selectedSessionId)
            } catch (e) {
              console.debug(`No analysis result for session ${selectedSessionId}`)
            }
          }
          
          const detail = transformToSessionDetail(backendSession, analysisResult)
          setSelectedSession(detail)
        }
      } catch (error) {
        console.error("Error loading session details:", error)
        setSelectedSession(null)
      }
    }

    loadSelectedSession()
  }, [selectedSessionId, sessions, fetchSessions, getAnalysisResult])

  const filteredSessions = sessions.filter((session) => {
    const matchesSearch =
      session.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.user.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesStatus = statusFilter === "all" || session.status === statusFilter
    const matchesWeek = weekFilter === "all" || session.week === weekFilter

    return matchesSearch && matchesStatus && matchesWeek
  })

  return (
    <div className="flex flex-1 flex-col">
      <header className="sticky top-0 z-10 flex h-16 items-center border-b bg-background px-6">
        <h1 className="text-xl font-semibold">Session History</h1>
      </header>
      <main className="flex-1 p-6 overflow-auto">

        <div className="container mx-auto space-y-6 p-6">
          <div className="flex flex-col gap-2">
            <h1 className="text-3xl font-bold tracking-tight">Session History</h1>
            <p className="text-muted-foreground">
              View and analyze past execution sessions, performance metrics, and reports.
            </p>
          </div>

          {/* Insights Banner */}
          <Alert className="bg-blue-50/50 text-blue-900 dark:bg-blue-950/20 dark:text-blue-100">
            <Lightbulb className="h-4 w-4" />
            <AlertTitle>Performance Insight</AlertTitle>
            <AlertDescription>
              Your analyses are <span className="font-semibold">25% faster</span> than the workspace average this week. Week
              8 had the highest quality score (94%).
            </AlertDescription>
          </Alert>

          <Card>
            <CardHeader>
              <CardTitle>Analysis Sessions</CardTitle>
              <CardDescription>
                {isLoading ? "Loading sessions..." : `${filteredSessions.length} sessions found`}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <SessionFilters
                onSearchChange={setSearchQuery}
                onStatusChange={setStatusFilter}
                onWeekChange={setWeekFilter}
              />

              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : (
                <SessionList sessions={filteredSessions} onViewDetails={setSelectedSessionId} />
              )}
            </CardContent>
          </Card>

          <SessionDetailSheet
            session={selectedSession}
            isOpen={!!selectedSessionId}
            onClose={() => setSelectedSessionId(null)}
          />
        </div>
      </main>
    </div>        
  )
}
