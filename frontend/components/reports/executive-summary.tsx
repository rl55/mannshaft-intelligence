import { Card, CardContent } from "@/components/ui/card"

interface ExecutiveSummaryProps {
  summary: string
}

export function ExecutiveSummary({ summary }: ExecutiveSummaryProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <h2 className="mb-4 text-lg font-semibold">Executive Summary</h2>
        <p className="leading-relaxed text-foreground">{summary}</p>
      </CardContent>
    </Card>
  )
}
