"use client"

import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip"
import { Info } from "lucide-react"

interface MetricTooltipProps {
  source?: string
  confidence?: number
}

export function MetricTooltip({ source, confidence }: MetricTooltipProps) {
  if (!source && confidence === undefined) return null

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button className="ml-1 inline-flex opacity-50 hover:opacity-100 transition-opacity">
            <Info className="h-3.5 w-3.5" />
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          {source && <p className="text-xs">Source: {source}</p>}
          {confidence !== undefined && <p className="text-xs">Confidence: {(confidence * 100).toFixed(0)}%</p>}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
