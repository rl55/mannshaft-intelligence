"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Lightbulb } from "lucide-react"
import { SessionFilters } from "@/components/sessions/session-filters"
import { SessionList } from "@/components/sessions/session-list"
import { SessionDetailSheet } from "@/components/sessions/session-detail-sheet"
import { mockSessions } from "@/components/sessions/mock-data"

export default function SessionsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [weekFilter, setWeekFilter] = useState("all")
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)

  const filteredSessions = mockSessions.filter((session) => {
    const matchesSearch =
      session.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.user.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesStatus = statusFilter === "all" || session.status === statusFilter
    const matchesWeek = weekFilter === "all" || session.week === weekFilter

    return matchesSearch && matchesStatus && matchesWeek
  })

  const selectedSession = mockSessions.find((s) => s.id === selectedSessionId) || null

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
              <CardDescription>{filteredSessions.length} sessions found</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <SessionFilters
                onSearchChange={setSearchQuery}
                onStatusChange={setStatusFilter}
                onWeekChange={setWeekFilter}
              />

              <SessionList sessions={filteredSessions} onViewDetails={setSelectedSessionId} />
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
