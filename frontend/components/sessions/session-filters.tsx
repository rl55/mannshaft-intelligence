"use client"

import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface SessionFiltersProps {
  onSearchChange: (value: string) => void
  onStatusChange: (value: string) => void
  onWeekChange: (value: string) => void
}

export function SessionFilters({ onSearchChange, onStatusChange, onWeekChange }: SessionFiltersProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-1 items-center space-x-2">
        <div className="relative flex-1 md:max-w-xs">
          <Search className="text-muted-foreground absolute left-2 top-2.5 h-4 w-4" />
          <Input
            placeholder="Search by ID or User..."
            className="pl-8"
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>
        <Select onValueChange={onStatusChange}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="partial">Partial</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
        <Select onValueChange={onWeekChange}>
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder="Week" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Weeks</SelectItem>
            <SelectItem value="8">Week 8</SelectItem>
            <SelectItem value="7">Week 7</SelectItem>
            <SelectItem value="6">Week 6</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="text-muted-foreground text-sm">Showing recent sessions</div>
    </div>
  )
}
