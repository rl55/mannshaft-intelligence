import { ReportHeader } from "@/components/reports/report-header"
import { ExecutiveSummary } from "@/components/reports/executive-summary"
import { InsightsGrid } from "@/components/reports/insights-grid"
import { CorrelationMatrix } from "@/components/reports/correlation-matrix"
import { RecommendationsList } from "@/components/reports/recommendations-list"
import { RiskFlags } from "@/components/reports/risk-flags"
import { ExportActions } from "@/components/reports/export-actions"
import type { ReportData } from "@/lib/report-types"
import { DashboardHeader } from "@/components/dashboard-header"

// Mock data function to simulate fetching a report
const getReportData = (sessionId: string): ReportData => {
  return {
    sessionId,
    week: "Week 8",
    date: "Nov 19, 2025",
    qualityScore: 94,
    confidence: "high",
    executionTime: "3.2s",
    executiveSummary:
      "MRR grew 15% to $1.25M driven by enterprise segment. Product engagement remains strong. Support tickets decreased 12%, indicating improved product quality. Cross-analysis suggests a strong correlation between the new feature rollout and reduced churn in the SMB segment.",
    insights: [
      {
        id: "revenue",
        title: "Revenue Insights",
        icon: "💰",
        summary: "Strong growth in enterprise MRR.",
        metrics: [
          { label: "MRR", value: "$1.25M", change: "+15%", trend: "up", confidence: 0.95, source: "Stripe API" },
          { label: "Churn", value: "3.2%", change: "-0.9pp", trend: "up", confidence: 0.92, source: "ChartMogul" }, // 'up' means positive movement (improvement) even if number is lower? Context dependent. Assuming 'trend' is visual direction. So for churn down is good. Let's stick to visual arrows. Change is negative, so arrow down. If 'trend' is 'up' it renders up arrow.
          { label: "ARPU", value: "$127", change: "+8%", trend: "up", confidence: 0.89 },
        ],
        details: JSON.stringify(
          {
            segment_breakdown: { enterprise: "+22%", smb: "+4%" },
            top_plans: ["Enterprise Plus", "Pro Annual"],
            churn_analysis: "Involuntary churn reduced by payment retry logic update.",
          },
          null,
          2,
        ),
      },
      {
        id: "product",
        title: "Product Insights",
        icon: "📊",
        summary: "Adoption of new dashboard feature driving engagement.",
        metrics: [
          { label: "DAU", value: "12.5K", change: "+8%", trend: "up", confidence: 0.94, source: "Mixpanel" },
          { label: "Adoption", value: "78%", change: "+5%", trend: "up", confidence: 0.88 },
          { label: "NPS", value: "52", change: "Excellent", trend: "neutral", confidence: 0.91, source: "Delighted" },
        ],
        details: JSON.stringify(
          {
            feature_usage: { dashboard: "85%", reports: "42%", settings: "15%" },
            session_length: "Avg 14m (+2m vs prev week)",
            drop_off_points: ["Onboarding step 3", "Export modal"],
          },
          null,
          2,
        ),
      },
    ],
    correlations: [
      {
        id: "c1",
        description: "Enterprise product usage → lower churn",
        strength: 0.82,
        impact: "High retention in engaged accounts",
      },
      { id: "c2", description: "Feature X adoption → 15% higher ARPU", strength: 0.65, impact: "Upsell driver" },
      {
        id: "c3",
        description: "Support ticket reduction → NPS improvement",
        strength: 0.78,
        impact: "Customer sentiment",
      },
    ],
    recommendations: [
      {
        id: "r1",
        priority: "HIGH",
        title: "Double enterprise sales capacity",
        impact: "+$150K MRR",
        timeline: "Q1 2026",
      },
      {
        id: "r2",
        priority: "MEDIUM",
        title: "Incentivize annual contract conversions",
        impact: "-1.5pp churn",
        timeline: "Ongoing",
      },
      { id: "r3", priority: "LOW", title: "Investigate SMB churn drivers", impact: "TBD", timeline: "Q2 2026" },
    ],
    risks: [
      { id: "rk1", description: "SMB churn elevated at 5.8% (vs 3.2% overall)", severity: "warning" },
      { id: "rk2", description: "Q1 renewals compressed - capacity risk", severity: "warning" },
    ],
  }
}

interface ReportPageProps {
  params: {
    sessionId: string
  }
}

export default function ReportPage({ params }: ReportPageProps) {
  // In a real app, this would be an async data fetch
  const reportData = getReportData(params.sessionId)

  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      {/* Reusing the Dashboard Header for consistency, or could be a simpler nav */}
      <DashboardHeader />

      <main className="flex flex-col">
        <ReportHeader
          week={reportData.week}
          date={reportData.date}
          qualityScore={reportData.qualityScore}
          confidence={reportData.confidence}
          executionTime={reportData.executionTime}
        />

        <div className="container mx-auto space-y-8 px-4 py-8">
          {/* Top Section: Summary & Risks */}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ExecutiveSummary summary={reportData.executiveSummary} />
            </div>
            <div className="lg:col-span-1">
              <RiskFlags risks={reportData.risks} />
            </div>
          </div>

          {/* Detailed Analysis Grid */}
          <InsightsGrid insights={reportData.insights} />

          {/* Cross-Functional & Strategic Section */}
          <div className="grid gap-6 lg:grid-cols-2">
            <CorrelationMatrix correlations={reportData.correlations} />
            <RecommendationsList recommendations={reportData.recommendations} />
          </div>

          {/* Footer Actions */}
          <ExportActions />
        </div>
      </main>
    </div>
  )
}
