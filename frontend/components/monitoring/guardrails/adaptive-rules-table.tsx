import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight, Settings2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"

const data = [
  { rule: "Low Confidence", threshold: "0.70", adjustments: 2, status: "Active" },
  { rule: "Anomaly Detector", threshold: "0.85", adjustments: 5, status: "Active" },
]

export function AdaptiveRulesTable() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg flex items-center gap-2">
          Adaptive Rules Status
          <Badge variant="secondary" className="text-xs font-normal">
            Auto-Tuning
          </Badge>
        </CardTitle>
        <Button variant="ghost" size="sm" className="text-xs">
          Manage Rules <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Rule</TableHead>
              <TableHead>Threshold</TableHead>
              <TableHead>Adjustments</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item) => (
              <TableRow key={item.rule}>
                <TableCell className="font-medium">{item.rule}</TableCell>
                <TableCell>{item.threshold}</TableCell>
                <TableCell>
                  <Badge variant="secondary" className="rounded-full px-2">
                    {item.adjustments}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-green-500" />
                    {item.status}
                  </div>
                </TableCell>
                <TableCell>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Settings2 className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
