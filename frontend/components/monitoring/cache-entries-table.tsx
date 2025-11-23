"use client"

import * as React from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Trash2, Search, Filter } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const mockData = [
  { id: "c_78912", type: "Prompt", hits: 45, lastAccessed: "2 min ago", ttl: "6d" },
  { id: "c_78913", type: "Agent", hits: 23, lastAccessed: "5 min ago", ttl: "23h" },
  { id: "c_78914", type: "Eval", hits: 12, lastAccessed: "12 min ago", ttl: "2d" },
  { id: "c_78915", type: "Prompt", hits: 89, lastAccessed: "15 min ago", ttl: "5d" },
  { id: "c_78916", type: "Agent", hits: 34, lastAccessed: "23 min ago", ttl: "12h" },
  { id: "c_78917", type: "Prompt", hits: 156, lastAccessed: "1 hour ago", ttl: "7d" },
  { id: "c_78918", type: "Eval", hits: 8, lastAccessed: "2 hours ago", ttl: "1d" },
]

export function CacheEntriesTable() {
  const [searchTerm, setSearchTerm] = React.useState("")
  const [typeFilter, setTypeFilter] = React.useState("all")

  const filteredData = mockData.filter((item) => {
    const matchesSearch = item.id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = typeFilter === "all" || item.type.toLowerCase() === typeFilter.toLowerCase()
    return matchesSearch && matchesType
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cache Entries</CardTitle>
        <CardDescription>Manage and monitor individual cache entries</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by Entry ID..."
              className="pl-8"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[180px]">
              <Filter className="mr-2 h-4 w-4" />
              <SelectValue placeholder="Filter by Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="prompt">Prompt</SelectItem>
              <SelectItem value="agent">Agent</SelectItem>
              <SelectItem value="eval">Eval</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Entry ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Hits</TableHead>
                <TableHead>Last Accessed</TableHead>
                <TableHead>TTL</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell className="font-mono text-xs">{entry.id}</TableCell>
                  <TableCell>
                    <Badge
                      variant={entry.type === "Prompt" ? "default" : entry.type === "Agent" ? "secondary" : "outline"}
                    >
                      {entry.type}
                    </Badge>
                  </TableCell>
                  <TableCell>{entry.hits}</TableCell>
                  <TableCell>{entry.lastAccessed}</TableCell>
                  <TableCell>{entry.ttl}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span className="sr-only">Clear</span>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="flex items-center justify-end space-x-2 py-4">
          <div className="text-xs text-muted-foreground">
            Showing {filteredData.length} of {mockData.length} entries
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled>
              Next
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
