"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api"
import { useQuery } from "@tanstack/react-query"

export function GuardrailEffectivenessTable() {
  const { data, isLoading } = useQuery({
    queryKey: ["guardrail-effectiveness"],
    queryFn: () => apiClient.getGuardrailEffectiveness(30),
    refetchInterval: 60000, // Refetch every minute
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Guardrail Effectiveness</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center">
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const effectiveness = data?.effectiveness || []

  if (effectiveness.length === 0) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Guardrail Effectiveness</CardTitle>
          <Button variant="ghost" size="sm" className="text-xs">
            View Details <ArrowRight className="ml-1 h-3 w-3" />
          </Button>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center">
            <p className="text-muted-foreground">No effectiveness data available</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Guardrail Effectiveness</CardTitle>
        <Button variant="ghost" size="sm" className="text-xs">
          View Details <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Rule Name</TableHead>
              <TableHead>Triggers</TableHead>
              <TableHead>Blocks</TableHead>
              <TableHead>Accuracy</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {effectiveness.map((item: any) => (
              <TableRow key={item.rule}>
                <TableCell className="font-medium">{item.rule}</TableCell>
                <TableCell>{item.triggers}</TableCell>
                <TableCell>{item.blocks}</TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={
                      item.accuracy === "100%"
                        ? "bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400"
                        : parseFloat(item.accuracy) >= 75
                          ? "bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-400"
                          : "bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400"
                    }
                  >
                    {item.accuracy}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
