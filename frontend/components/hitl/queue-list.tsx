"use client"

import type { EscalationItem } from "./types"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"

interface QueueListProps {
  items: EscalationItem[]
  selectedId: string
  onSelect: (id: string) => void
}

export function QueueList({ items, selectedId, onSelect }: QueueListProps) {
  const pendingItems = items.filter((i) => i.status === "pending")
  const resolvedItems = items.filter((i) => i.status !== "pending")

  return (
    <div className="h-full flex flex-col border-r bg-background/50 overflow-hidden">
      <div className="p-4 border-b flex-shrink-0">
        <h3 className="font-semibold mb-1">Escalation Queue</h3>
        <p className="text-xs text-muted-foreground">
          {pendingItems.length} pending • {resolvedItems.length} resolved
        </p>
      </div>
      <ScrollArea className="flex-1 min-h-0">
        <div className="flex flex-col gap-1 p-2">
          {/* Pending Items */}
          {pendingItems.length > 0 && (
            <>
              <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase">Pending</div>
              {pendingItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onSelect(item.id)}
                  className={cn(
                    "flex flex-col items-start gap-2 p-3 rounded-lg text-left transition-colors border",
                    selectedId === item.id
                      ? "bg-accent text-accent-foreground border-primary/20"
                      : "bg-background hover:bg-muted border-transparent",
                  )}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="font-medium text-sm">
                      {item.week !== "Unknown" ? item.week : `Session ${item.session.substring(0, 8)}`}
                    </span>
                    <span className="text-xs text-muted-foreground">{item.timestamp}</span>
                  </div>
                  <div className="flex items-center gap-2 w-full">
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-[10px] px-1 py-0 h-5",
                        item.riskScore > 0.7 ? "border-red-500 text-red-500" : "border-yellow-500 text-yellow-500",
                      )}
                    >
                      Risk: {(item.riskScore * 100).toFixed(0)}%
                    </Badge>
                    <span className="text-xs truncate text-muted-foreground flex-1">{item.primaryAgent}</span>
                  </div>
                </button>
              ))}
            </>
          )}
          
          {/* Resolved Items */}
          {resolvedItems.length > 0 && (
            <>
              <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase mt-2">Resolved</div>
              {resolvedItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onSelect(item.id)}
                  className={cn(
                    "flex flex-col items-start gap-2 p-3 rounded-lg text-left transition-colors border",
                    selectedId === item.id
                      ? "bg-accent text-accent-foreground border-primary/20"
                      : "bg-background hover:bg-muted border-transparent opacity-75",
                  )}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="font-medium text-sm">
                      {item.week !== "Unknown" ? item.week : `Session ${item.session.substring(0, 8)}`}
                    </span>
                    <span className="text-xs text-muted-foreground">{item.timestamp}</span>
                  </div>
                  <div className="flex items-center gap-2 w-full">
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-[10px] px-1 py-0 h-5",
                        item.status === "approved"
                          ? "border-green-500 text-green-500"
                          : item.status === "rejected"
                          ? "border-red-500 text-red-500"
                          : "border-blue-500 text-blue-500",
                      )}
                    >
                      {item.status === "approved" ? "✓ Approved" : item.status === "rejected" ? "✗ Rejected" : "✎ Modified"}
                    </Badge>
                    <span className="text-xs truncate text-muted-foreground flex-1">{item.primaryAgent}</span>
                  </div>
                </button>
              ))}
            </>
          )}
          
          {items.length === 0 && (
            <div className="p-4 text-center text-sm text-muted-foreground">No escalations found</div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
