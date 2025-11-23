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
  return (
    <div className="h-full flex flex-col border-r bg-background/50">
      <div className="p-4 border-b">
        <h3 className="font-semibold mb-1">Escalation Queue</h3>
        <p className="text-xs text-muted-foreground">
          {items.filter((i) => i.status === "pending").length} items pending review
        </p>
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-1 p-2">
          {items.map((item) => (
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
                <span className="font-medium text-sm">#{item.id}</span>
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
                  Risk: {item.riskScore}
                </Badge>
                <span className="text-xs truncate text-muted-foreground flex-1">{item.primaryAgent}</span>
              </div>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
