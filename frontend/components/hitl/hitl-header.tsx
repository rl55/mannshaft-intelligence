import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"

export function HitlHeader() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <Card className="p-4 flex items-center justify-between border-l-4 border-l-yellow-500">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Pending Review</p>
          <h2 className="text-2xl font-bold">3</h2>
        </div>
        <Badge variant="outline" className="bg-yellow-50 text-yellow-700">
          Action Required
        </Badge>
      </Card>
      <Card className="p-4 flex items-center justify-between border-l-4 border-l-green-500">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Approved</p>
          <h2 className="text-2xl font-bold">12</h2>
        </div>
        <Badge variant="outline" className="bg-green-50 text-green-700">
          This Week
        </Badge>
      </Card>
      <Card className="p-4 flex items-center justify-between border-l-4 border-l-red-500">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Rejected</p>
          <h2 className="text-2xl font-bold">1</h2>
        </div>
        <Badge variant="outline" className="bg-red-50 text-red-700">
          Attention
        </Badge>
      </Card>
    </div>
  )
}
