"use client"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Download, Mail, Share2 } from "lucide-react"
import { toast } from "sonner" // Assuming sonner is installed as per components list

export function ExportActions() {
  const handleExport = (type: string) => {
    toast.success(`${type} export started`, {
      description: "Your report is being prepared for download.",
    })
  }

  return (
    <Card className="flex flex-col items-center justify-between gap-4 p-4 sm:flex-row bg-muted/30">
      <p className="text-sm font-medium text-muted-foreground">
        Analysis complete. Share these insights with stakeholders.
      </p>
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" size="sm" onClick={() => handleExport("PDF")}>
          <Download className="mr-2 h-4 w-4" />
          Export PDF
        </Button>
        <Button variant="outline" size="sm" onClick={() => handleExport("Email")}>
          <Mail className="mr-2 h-4 w-4" />
          Email Report
        </Button>
        <Button size="sm" onClick={() => handleExport("Link")}>
          <Share2 className="mr-2 h-4 w-4" />
          Share Link
        </Button>
      </div>
    </Card>
  )
}
