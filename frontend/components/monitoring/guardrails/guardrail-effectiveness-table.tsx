import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"

const data = [
  { rule: "PII Detection", triggers: 2, blocks: 2, accuracy: "100%" },
  { rule: "Low Confidence", triggers: 12, blocks: 0, accuracy: "100%" },
  { rule: "Data Completeness", triggers: 4, blocks: 1, accuracy: "75%" },
]

export function GuardrailEffectivenessTable() {
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
            {data.map((item) => (
              <TableRow key={item.rule}>
                <TableCell className="font-medium">{item.rule}</TableCell>
                <TableCell>{item.triggers}</TableCell>
                <TableCell>{item.blocks}</TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={
                      item.accuracy === "100%"
                        ? "bg-green-50 text-green-700 border-green-200"
                        : "bg-yellow-50 text-yellow-700 border-yellow-200"
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
