"use client"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Download, Mail, Share2 } from "lucide-react"
import { toast } from "sonner"
import { exportToPDF, exportReportToPDF } from "@/lib/pdf-export"
import { useState } from "react"
import type { ReportData } from "@/lib/report-types"

interface ExportActionsProps {
  reportData?: ReportData
  reportElementId?: string
}

export function ExportActions({ reportData, reportElementId = "report-content" }: ExportActionsProps) {
  const [isExporting, setIsExporting] = useState(false)

  const handlePDFExport = async () => {
    try {
      setIsExporting(true)
      
      if (reportData) {
        // Use report data to generate PDF
        exportReportToPDF(reportData, `analysis-report-${reportData.sessionId}.pdf`)
      } else {
        // Use element ID to capture current page
        await exportToPDF(reportElementId, "analysis-report.pdf")
      }
      
      toast.success("PDF export started", {
        description: "Your report is being prepared for download.",
      })
    } catch (error) {
      console.error("PDF export error:", error)
      toast.error("Export failed", {
        description: "Failed to generate PDF. Please try again.",
      })
    } finally {
      setIsExporting(false)
    }
  }

  const handleEmailExport = () => {
    toast.info("Email export", {
      description: "Email functionality will be available soon.",
    })
  }

  const handleShareLink = () => {
    if (reportData?.sessionId) {
      const url = `${window.location.origin}/reports/${reportData.sessionId}`
      navigator.clipboard.writeText(url)
      toast.success("Link copied", {
        description: "Report link has been copied to clipboard.",
      })
    } else {
      toast.info("Share link", {
        description: "Share link functionality will be available soon.",
      })
    }
  }

  return (
    <Card className="flex flex-col items-center justify-between gap-4 p-4 sm:flex-row bg-muted/30">
      <p className="text-sm font-medium text-muted-foreground">
        Analysis complete. Share these insights with stakeholders.
      </p>
      <div className="flex flex-wrap gap-2">
        <Button 
          variant="outline" 
          size="sm" 
          onClick={handlePDFExport}
          disabled={isExporting}
        >
          <Download className="mr-2 h-4 w-4" />
          {isExporting ? "Exporting..." : "Export PDF"}
        </Button>
        <Button variant="outline" size="sm" onClick={handleEmailExport}>
          <Mail className="mr-2 h-4 w-4" />
          Email Report
        </Button>
        <Button size="sm" onClick={handleShareLink}>
          <Share2 className="mr-2 h-4 w-4" />
          Share Link
        </Button>
      </div>
    </Card>
  )
}
