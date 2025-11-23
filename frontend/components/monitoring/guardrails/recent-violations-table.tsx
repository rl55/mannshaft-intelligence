import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"

const data = [
  { time: "2m ago", rule: "Low Confidence", severity: "Medium", action: "Escalated" },
  { time: "15m ago", rule: "Data Stale", severity: "Low", action: "Warning" },
  { time: "1h ago", rule: "Cost Limit", severity: "High", action: "Blocked" },
]

export function RecentViolationsTable() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Recent Violations</CardTitle>
        <Button variant="ghost" size="sm" className="text-xs">
          View All <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>Rule</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item, i) => (
              <TableRow key={i}>
                <TableCell className="text-muted-foreground">{item.time}</TableCell>
                <TableCell className="font-medium">{item.rule}</TableCell>
                <TableCell>
                  <Badge
                    variant={
                      item.severity === "High" || item.severity === "Critical"
                        ? "destructive"
                        : item.severity === "Medium"
                          ? "secondary"
                          : "outline"
                    }
                    className={
                      item.severity === "Medium"
                        ? "bg-yellow-100 text-yellow-800 hover:bg-yellow-100/80 dark:bg-yellow-900/30 dark:text-yellow-500"
                        : ""
                    }
                  >
                    {item.severity}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{item.action}</Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
