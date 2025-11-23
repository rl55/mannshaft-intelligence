import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { RiskFlag } from "@/lib/report-types"
import { AlertTriangle, ShieldAlert } from "lucide-react"

interface RiskFlagsProps {
  risks: RiskFlag[]
}

export function RiskFlags({ risks }: RiskFlagsProps) {
  if (!risks.length) return null

  return (
    <Card className="border-orange-200 bg-orange-50/50 dark:border-orange-900/50 dark:bg-orange-950/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-orange-800 dark:text-orange-400">
          <ShieldAlert className="h-5 w-5" />
          Risk Flags
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {risks.map((risk) => (
            <li key={risk.id} className="flex items-start gap-2.5">
              <AlertTriangle className="mt-0.5 h-4 w-4 text-orange-600 dark:text-orange-500 shrink-0" />
              <span className="text-sm text-orange-900 dark:text-orange-300">{risk.description}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
