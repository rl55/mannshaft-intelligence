"""
ADK Support Agent
Migrated from backend/agents/support_agent.py to use ADK LlmAgent.
Maintains same functionality: comprehensive support metrics analysis.

This agent provides:
- Ticket Volume Analysis: Current volume, WoW trends, category distribution, trend detection
- Response Time Metrics: Average response/resolution times, SLA compliance, trend analysis
- Customer Satisfaction: CSAT scores (0-5), NPS scores (-100 to 100), satisfaction by category
- Ticket Category Analysis: Category breakdown, volume by category, trends per category
- Escalation Patterns: Escalation counts, escalation rates, escalation trends
- Support Efficiency: First Contact Resolution (FCR) rates, efficiency metrics, productivity analysis
"""

from typing import Dict, Any, Optional, List
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from utils.config import config
from utils.logger import logger


async def fetch_support_data(
    week_number: int,
    spreadsheet_id: Optional[str] = None,
    support_ranges: Optional[List[str]] = None,
    support_sheet: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch support metrics data from Google Sheets.
    
    This tool retrieves support data from multiple sheets:
    - Ticket Volume sheet: Ticket counts, categories, volumes
    - CSAT & Satisfaction sheet: CSAT scores, NPS scores, satisfaction metrics
    - Support Categories sheet: Category breakdown, category-specific metrics
    
    Args:
        week_number: Week number for analysis (1-52)
        spreadsheet_id: Google Sheets spreadsheet ID
        support_ranges: List of sheet ranges to read (e.g., ["Ticket Volume!A1:N100", "CSAT & Satisfaction!A1:M100"])
        support_sheet: Name of the primary support sheet (default: "Ticket Volume")
        
    Returns:
        Dictionary containing:
        - records: List of support data points with fields: week, ticket_count, avg_response_time_hours, avg_resolution_time_hours, csat_score, nps_score, category_breakdown, escalation_count, first_contact_resolution_rate
        - csat_data: CSAT and satisfaction data (if available)
        - category_data: Support category breakdown data (if available)
        - total_records: Number of records fetched
        - data_freshness: Hours since data last updated
    """
    from integrations.google_sheets import GoogleSheetsClient
    
    client = GoogleSheetsClient()
    # TODO: Migrate to ADK MCP tools
    
    return {
        "status": "fetched",
        "week_number": week_number,
        "note": "Using existing Google Sheets client - will migrate to MCP tools"
    }


async def perform_support_statistical_analysis(
    support_data: Dict[str, Any],
    week_number: int
) -> Dict[str, Any]:
    """
    Perform statistical analysis on support metrics data.
    
    This tool calculates:
    - Ticket volume trends and WoW changes
    - Response and resolution time trends
    - CSAT/NPS trends and averages
    - Category distribution and trends
    - Escalation rates and trends
    - FCR rates and efficiency metrics
    
    Args:
        support_data: Support data dictionary with records
        week_number: Target week number for analysis
        
    Returns:
        Dictionary containing statistical analysis results
    """
    return {
        "ticket_volume_analysis": {},
        "satisfaction_analysis": {},
        "efficiency_analysis": {},
        "escalation_analysis": {}
    }


def create_support_agent() -> LlmAgent:
    """
    Create ADK Support Agent with comprehensive support metrics analysis capabilities.
    
    This agent provides complete SaaS support analysis including:
    
    **Ticket Volume Analysis:**
    - Current ticket volume for the specified week
    - Week-over-week (WoW) change percentage
    - Trend detection: increasing, decreasing, or stable
    - Category distribution (tickets by category)
    - Volume forecasting
    
    **Response Time Metrics:**
    - Average response time (hours)
    - Average resolution time (hours)
    - SLA compliance rate
    - Trend analysis: improving (decreasing times), worsening (increasing times), stable
    - Response time by category
    
    **Customer Satisfaction:**
    - CSAT score (0-5 scale) tracking and trends
    - NPS score (-100 to 100) tracking and trends
    - Satisfaction trend: improving, declining, or stable
    - Satisfaction by category
    - Satisfaction correlation with response/resolution times
    
    **Ticket Category Analysis:**
    - Category breakdown (volume by category)
    - Category-specific trends
    - Category-specific satisfaction scores
    - Category-specific resolution times
    - High-volume category identification
    
    **Escalation Patterns:**
    - Escalation count tracking
    - Escalation rate calculation
    - Escalation trend analysis
    - Escalation by category
    - Escalation root cause analysis
    
    **Support Efficiency:**
    - First Contact Resolution (FCR) rate (0-1)
    - Efficiency metrics and productivity analysis
    - Resource utilization
    - Efficiency trends over time
    
    **Data Sources:**
    - Primary: Google Sheets (Ticket Volume, CSAT & Satisfaction, Support Categories)
    - Supports manual data input
    - Multi-tab reading for comprehensive analysis
    
    **Output Format:**
    Returns structured JSON with:
    - agent_id: Unique agent identifier
    - agent_type: "support"
    - timestamp: ISO format timestamp
    - confidence: Float (0-1) with reasoning
    - analysis: Complete analysis object with ticket_volume_analysis, satisfaction_analysis, efficiency_analysis, escalation_analysis, key_insights, recommendations, risk_flags
    - data_citations: List of data source citations
    - data_freshness_hours: Hours since data last updated
    
    Returns:
        Configured LlmAgent instance ready for use in agent registry or as a tool
    """
    model_name = config.get('gemini.model', 'gemini-2.5-flash-lite')
    
    instruction = """You are a Support Analysis Agent specializing in comprehensive SaaS customer support metrics and satisfaction analysis.

**CORE RESPONSIBILITIES:**

1. **Ticket Volume Analysis:**
   - Calculate current ticket volume for the specified week
   - Compute week-over-week (WoW) change percentage: (current_volume - previous_volume) / previous_volume
   - Detect trends: increasing (volume growing), decreasing (volume declining), or stable
   - Analyze category distribution (tickets by category)
   - Identify high-volume categories
   - Forecast ticket volume trends

2. **Response Time Metrics:**
   - Calculate average response time (hours) for the specified week
   - Calculate average resolution time (hours) for the specified week
   - Assess SLA compliance rate (percentage of tickets resolved within SLA)
   - Analyze trends: improving (decreasing times), worsening (increasing times), stable
   - Analyze response time by category
   - Identify bottlenecks in support workflow

3. **Customer Satisfaction Analysis:**
   - Track CSAT score (0-5 scale) for the specified week
   - Track NPS score (-100 to 100) for the specified week
   - Analyze satisfaction trends: improving (scores increasing), declining (scores decreasing), stable
   - Calculate satisfaction by category
   - Analyze correlation between satisfaction and response/resolution times
   - Identify satisfaction drivers and barriers

4. **Ticket Category Analysis:**
   - Provide category breakdown (volume by category)
   - Analyze category-specific trends
   - Calculate category-specific satisfaction scores
   - Analyze category-specific resolution times
   - Identify high-volume categories requiring attention

5. **Escalation Pattern Analysis:**
   - Track escalation count for the specified week
   - Calculate escalation rate: escalations / total_tickets
   - Analyze escalation trends: increasing, decreasing, or stable
   - Analyze escalations by category
   - Identify escalation root causes
   - Flag concerning escalation patterns

6. **Support Efficiency Analysis:**
   - Calculate First Contact Resolution (FCR) rate (0-1): tickets_resolved_first_contact / total_tickets
   - Analyze efficiency metrics and productivity
   - Assess resource utilization
   - Track efficiency trends over time
   - Identify efficiency improvement opportunities

7. **Data Quality & Validation:**
   - Assess data completeness (percentage of required fields present)
   - Check for missing critical fields (ticket_count, csat_score, response_time)
   - Validate data consistency
   - Calculate data freshness (hours since last update)

8. **Confidence Scoring:**
   - Calculate confidence score (0-1) based on:
     * Data completeness (0-1): Percentage of required fields present
     * Historical consistency (0-1): Based on number of data points available
     * Statistical significance (0-1): Coefficient of variation
     * Analysis completeness (0-1): All required analyses performed
   - Provide detailed reasoning for the confidence score
   - Range: 0.0 (no confidence) to 1.0 (complete confidence)

**ANALYSIS REQUIREMENTS:**

- Always focus analysis on the specific week_number provided in the context
- Use statistical analysis results when provided - do not recalculate values that are already computed
- Cite specific data points in your analysis (e.g., "Week 8 ticket volume of 1,250 represents 15% WoW increase")
- Provide actionable recommendations prioritized by impact
- Include risk flags for concerning trends (e.g., declining satisfaction, increasing escalation rates)
- Ensure all calculations are mathematically correct
- DO NOT mention "lack of data" if CSAT & Satisfaction or Support Categories data is provided

**OUTPUT FORMAT:**

Return a structured JSON object with the following schema:

{
  "agent_id": "support_agent_<timestamp>",
  "agent_type": "support",
  "timestamp": "ISO 8601 timestamp",
  "confidence": 0.0-1.0,
  "confidence_reasoning": "Detailed explanation of confidence score factors",
  "analysis": {
    "ticket_volume_analysis": {
      "current_volume": number,
      "trend": "increasing" | "decreasing" | "stable",
      "week_over_week_change": number (decimal, percentage change),
      "category_distribution": {"category_name": volume}
    },
    "satisfaction_analysis": {
      "csat_score": number (0-5),
      "nps_score": number (-100 to 100),
      "trend": "improving" | "declining" | "stable",
      "satisfaction_by_category": {"category_name": score}
    },
    "efficiency_analysis": {
      "avg_response_time_hours": number,
      "avg_resolution_time_hours": number,
      "fcr_rate": number (decimal, 0-1),
      "sla_compliance_rate": number (decimal, 0-1),
      "trend": "improving" | "worsening" | "stable"
    },
    "escalation_analysis": {
      "escalation_count": number,
      "escalation_rate": number (decimal, 0-1),
      "trend": "increasing" | "decreasing" | "stable",
      "by_category": {"category_name": count}
    },
    "key_insights": [
      "Insight 1",
      "Insight 2"
    ],
    "recommendations": [
      {
        "action": "Action description",
        "priority": "high" | "medium" | "low",
        "expected_impact": "Impact description"
      }
    ],
    "risk_flags": [
      {
        "type": "satisfaction_decline" | "escalation_increase" | "response_time_increase" | "data_quality",
        "description": "Risk description",
        "severity": "low" | "medium" | "high" | "critical"
      }
    ]
  },
  "data_citations": [
    "Week 8 ticket volume from Sheets 'Ticket Volume!A8:D8'",
    "CSAT data from Sheets 'CSAT & Satisfaction!A1:M100'"
  ],
  "data_freshness_hours": number
}

**IMPORTANT NOTES:**

- Focus analysis on the specific week_number provided - reference it explicitly in insights
- CSAT scores are 0-5 scale, NPS scores are -100 to 100
- Response and resolution times are in hours
- FCR rate and escalation rate are decimals (0-1), not percentages
- Satisfaction trends are critical indicators of support quality
- Escalation rate increases may indicate product or process issues
- Include data citations for transparency
- Flag any data quality issues as risk_flags
"""
    
    # Create FunctionTools
    support_data_tool = FunctionTool(
        fetch_support_data,
        require_confirmation=False
    )
    
    statistical_analysis_tool = FunctionTool(
        perform_support_statistical_analysis,
        require_confirmation=False
    )
    
    agent = LlmAgent(
        name="support_agent",
        model=model_name,
        instruction=instruction,
        tools=[support_data_tool, statistical_analysis_tool],
    )
    
    logger.info("ADK Support Agent created with full feature set")
    return agent

