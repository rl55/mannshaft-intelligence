import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ShieldCheck, AlertTriangle, UserCheck, ArrowUp, ArrowDown } from "lucide-react"

export function GuardrailMetrics() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Checks</CardTitle>
          <ShieldCheck className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">1,247</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <ArrowUp className="mr-1 h-4 w-4 text-green-500" />
            <span className="text-green-500 font-medium">+120</span>
            <span className="ml-1">vs last week</span>
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Violations</CardTitle>
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            18 <span className="text-sm font-normal text-muted-foreground">(1.4%)</span>
          </div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <ArrowDown className="mr-1 h-4 w-4 text-green-500" />
            <span className="text-green-500 font-medium">-2</span>
            <span className="ml-1">vs last week</span>
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">HITL Reviews</CardTitle>
          <UserCheck className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">3</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <ArrowDown className="mr-1 h-4 w-4 text-green-500" />
            <span className="text-green-500 font-medium">-1</span>
            <span className="ml-1">vs last week</span>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
