"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Zap, Eye, Trash2 } from "lucide-react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { useAnalysisStore } from "@/store/analysis-store"

interface QuickActionsCardProps {
  onTrigger?: (week: string) => void
}

export function QuickActionsCard({ onTrigger }: QuickActionsCardProps) {
  const [selectedWeek, setSelectedWeek] = useState("8")
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()
  const router = useRouter()
  const { triggerAnalysis, clearCache: clearCacheStore } = useAnalysisStore()

  const handleTriggerAnalysis = async () => {
    setIsLoading(true)
    try {
      const response = await triggerAnalysis(
        parseInt(selectedWeek),
        'comprehensive',
        'demo_user'
      )
      toast({ 
        title: "Analysis Started", 
        description: `Session ${response.session_id} is now running`,
      })
      onTrigger?.(selectedWeek)
    } catch (error) {
      // Error is already handled by the API client
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearCache = async () => {
    if (!confirm("Clear all cache?")) return
    
    try {
      await clearCacheStore()
      toast({
        title: "Cache Cleared",
        description: "All cache has been cleared successfully",
      })
    } catch (error) {
      // Error is already handled by the API client
    }
  }

  const handleViewSessions = () => {
    router.push("/sessions")
  }


  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Zap className="h-5 w-5 text-primary" />
          Quick Actions
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          <label className="text-sm text-muted-foreground">Select Week</label>
          <Select value={selectedWeek} onValueChange={setSelectedWeek}>
            <SelectTrigger>
              <SelectValue placeholder="Select week" />
            </SelectTrigger>
            <SelectContent>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((week) => (
                <SelectItem key={week} value={String(week)}>
                  Week {week}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button className="w-full" size="sm" onClick={() => onTrigger?.(selectedWeek)}>
          Trigger Week {selectedWeek} Analysis
        </Button>

        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            className="flex-1 bg-transparent"
            onClick={handleViewSessions}
          >
            <Eye className="mr-2 h-4 w-4" />
            View Sessions
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            className="flex-1 bg-transparent"
            onClick={handleClearCache}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Clear Cache
          </Button>
        </div>  
      </CardContent>
      {/* <Button 
        onClick={handleTriggerAnalysis} 
        disabled={isLoading}
      >
        {isLoading ? "Starting..." : `Trigger Week ${selectedWeek} Analysis`}
      </Button>
      
      <Button onClick={handleClearCache}>Clear Cache</Button>
      <Button onClick={() => router.push("/sessions")}>View Sessions</Button>
      */}
    </Card>
  )
}
