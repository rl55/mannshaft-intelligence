"use client"

import * as React from "react"
import { useEffect, useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Trash2, Search, Filter } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { apiClient } from "@/lib/api"

interface CacheEntry {
  id: string
  type: string
  hits: number
  last_accessed: string
  ttl: string
  created_at: string
}

export function CacheEntriesTable() {
  const [entries, setEntries] = useState<CacheEntry[]>([])
  const [filteredEntries, setFilteredEntries] = useState<CacheEntry[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [typeFilter, setTypeFilter] = useState("all")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const pageSize = 20

  useEffect(() => {
    const fetchEntries = async () => {
      try {
        setLoading(true)
        const cacheType = typeFilter === "all" ? undefined : typeFilter
        const response = await apiClient.getCacheEntries(page, pageSize, cacheType, true)
        setEntries(response.entries)
        setTotal(response.total)
      } catch (error) {
        console.error("Error fetching cache entries:", error)
        setEntries([])
      } finally {
        setLoading(false)
      }
    }

    fetchEntries()
  }, [page, typeFilter])

  useEffect(() => {
    const filtered = entries.filter((item) => {
      const matchesSearch = item.id.toLowerCase().includes(searchTerm.toLowerCase())
      return matchesSearch
    })
    setFilteredEntries(filtered)
  }, [entries, searchTerm])

  const handleClearEntry = async (entryId: string) => {
    // TODO: Implement individual cache entry clearing
    console.log("Clear entry:", entryId)
  }

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
          <Select value={typeFilter} onValueChange={(value) => { setTypeFilter(value); setPage(1); }}>
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

        {loading ? (
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            Loading...
          </div>
        ) : (
          <>
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
                  {filteredEntries.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                        {entries.length === 0 ? "No cache entries found" : "No entries match your search"}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredEntries.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="text-xs">{entry.id}</TableCell>
                        <TableCell>
                          <Badge
                            variant={entry.type === "Prompt" ? "default" : entry.type === "Agent" ? "secondary" : "outline"}
                          >
                            {entry.type}
                          </Badge>
                        </TableCell>
                        <TableCell>{entry.hits}</TableCell>
                        <TableCell>{entry.last_accessed}</TableCell>
                        <TableCell>{entry.ttl}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                            onClick={() => handleClearEntry(entry.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Clear</span>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="flex items-center justify-end space-x-2 py-4">
              <div className="text-xs text-muted-foreground">
                Showing {filteredEntries.length} of {total} entries
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  disabled={page * pageSize >= total}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
