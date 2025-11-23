"use client"

import { Eye } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import type { SessionHistoryItem, SessionStatusType } from "./types"
import { cn } from "@/lib/utils"

interface SessionListProps {
  sessions: SessionHistoryItem[]
  onViewDetails: (sessionId: string) => void
}

const statusColorMap: Record<SessionStatusType, "default" | "success" | "warning" | "destructive" | "secondary"> = {
  completed: "success",
  running: "secondary",
  partial: "warning",
  failed: "destructive",
}

const statusLabelMap: Record<SessionStatusType, string> = {
  completed: "Completed",
  running: "Running",
  partial: "Partial",
  failed: "Failed",
}

export function SessionList({ sessions, onViewDetails }: SessionListProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Session ID</TableHead>
            <TableHead>Week</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Quality</TableHead>
            <TableHead>Time</TableHead>
            <TableHead>Date</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="h-24 text-center">
                No sessions found.
              </TableCell>
            </TableRow>
          ) : (
            sessions.map((session) => (
              <TableRow
                key={session.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => onViewDetails(session.id)}
              >
                <TableCell className="font-medium">{session.id}</TableCell>
                <TableCell>Week {session.week}</TableCell>
                <TableCell>
                  <Badge variant={statusColorMap[session.status]} className="capitalize">
                    {statusLabelMap[session.status]}
                  </Badge>
                </TableCell>
                <TableCell>
                  {session.qualityScore ? (
                    <span
                      className={cn(
                        "font-medium",
                        session.qualityScore >= 90
                          ? "text-green-600"
                          : session.qualityScore >= 70
                            ? "text-yellow-600"
                            : "text-red-600",
                      )}
                    >
                      {session.qualityScore}%
                    </span>
                  ) : (
                    <span className="text-muted-foreground">-</span>
                  )}
                </TableCell>
                <TableCell>{session.executionTime}</TableCell>
                <TableCell>{session.date}</TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation()
                      onViewDetails(session.id)
                    }}
                  >
                    <Eye className="h-4 w-4" />
                    <span className="sr-only">View Details</span>
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}
