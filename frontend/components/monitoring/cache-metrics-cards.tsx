import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowUp, Zap, Database, DollarSign } from "lucide-react"

export function CacheMetricsCards() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Hit Rate</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">78%</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <ArrowUp className="mr-1 h-4 w-4 text-green-500" />
            <span className="text-green-500 font-medium">+5%</span>
            <span className="ml-1">vs last week</span>
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Tokens Saved</CardTitle>
          <Database className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">125K</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <ArrowUp className="mr-1 h-4 w-4 text-green-500" />
            <span className="text-green-500 font-medium">+18K</span>
            <span className="ml-1">vs last week</span>
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Cost Saved</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">$2.34</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <ArrowUp className="mr-1 h-4 w-4 text-green-500" />
            <span className="text-green-500 font-medium">+$0.42</span>
            <span className="ml-1">vs last week</span>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
