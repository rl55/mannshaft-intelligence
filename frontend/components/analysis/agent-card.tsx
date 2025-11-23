"use client"

import type React from "react"

import { useEffect, useRef } from "react"
import type { AgentData } from "@/components/analysis/types"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { CheckCircle2, Circle, AlertCircle, Loader2, Clock, Database, Bot } from "lucide-react"
import { Progress } from "@/components/ui/progress"

interface AgentCardProps {
  agent: AgentData
  icon?: React.ReactNode
}

export function AgentCard({ agent, icon }: AgentCardProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll logs
  useEffect(() => {
    if (scrollRef.current) {
      const scrollContainer = scrollRef.current.querySelector("[data-radix-scroll-area-viewport]")
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [agent.logs])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-green-500 border-green-500/20 bg-green-500/10"
      case "running":
        return "text-blue-500 border-blue-500/20 bg-blue-500/10"
      case "error":
        return "text-red-500 border-red-500/20 bg-red-500/10"
      default:
        return "text-muted-foreground border-muted bg-muted/30"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="size-4" />
      case "running":
        return <Loader2 className="size-4 animate-spin" />
      case "error":
        return <AlertCircle className="size-4" />
      default:
        return <Circle className="size-4" />
    }
  }

  return (
    <Card
      className={cn(
        "transition-all duration-300 border-l-4",
        agent.status === "running" && "border-l-blue-500 shadow-md ring-1 ring-blue-500/20",
        agent.status === "completed" && "border-l-green-500",
        agent.status === "error" && "border-l-red-500",
        agent.status === "idle" && "border-l-transparent opacity-70",
      )}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={cn("p-2 rounded-md bg-primary/10", agent.status === "running" && "animate-pulse")}>
              {icon || <Bot className="size-5 text-primary" />}
            </div>
            <div>
              <CardTitle className="text-base">{agent.name}</CardTitle>
              <div className="text-xs text-muted-foreground">{agent.role}</div>
            </div>
          </div>
          <Badge variant="outline" className={cn("gap-1.5", getStatusColor(agent.status))}>
            {getStatusIcon(agent.status)}
            <span className="capitalize">{agent.status}</span>
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <div className="space-y-3">
          {/* Stats Row */}
          {agent.status !== "idle" && (
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              {agent.executionTime && (
                <div className="flex items-center gap-1">
                  <Clock className="size-3" />
                  <span>{(agent.executionTime / 1000).toFixed(1)}s</span>
                </div>
              )}
              {agent.status === "running" && (
                <div className="flex items-center gap-1">
                  <Database className="size-3" />
                  <span>Fetching data...</span>
                </div>
              )}
            </div>
          )}

          {/* Logs Area */}
          <div className="rounded-md border bg-muted/30 font-mono text-xs">
            <ScrollArea className="h-[120px] p-3" ref={scrollRef}>
              {agent.logs.length === 0 ? (
                <span className="text-muted-foreground italic">Waiting to start...</span>
              ) : (
                <div className="space-y-1.5">
                  {agent.logs.map((log, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="text-muted-foreground">
                        [
                        {new Date().toLocaleTimeString([], {
                          hour12: false,
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                        ]
                      </span>
                      <span
                        className={cn(
                          i === agent.logs.length - 1 && agent.status === "running" && "animate-pulse text-primary",
                        )}
                      >
                        {log.replace(/^> /, "")}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-0">
        <div className="w-full flex items-center justify-between text-xs">
          {agent.confidence !== undefined ? (
            <div className="flex items-center gap-2 w-full">
              <span className="text-muted-foreground">Confidence:</span>
              <div className="flex-1 flex items-center gap-2">
                <Progress value={agent.confidence * 100} className="h-1.5 w-20" />
                <span className={cn("font-medium", agent.confidence > 0.8 ? "text-green-500" : "text-amber-500")}>
                  {(agent.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ) : (
            <div className="h-4" /> /* Spacer */
          )}
        </div>
      </CardFooter>
    </Card>
  )
}
