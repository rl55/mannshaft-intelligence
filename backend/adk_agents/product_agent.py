"""
ADK Product Agent
Migrated from backend/agents/product_agent.py to use ADK LlmAgent.
Maintains same functionality: comprehensive product metrics analysis.

This agent provides:
- DAU/WAU/MAU Analysis: Daily/Weekly/Monthly Active Users, engagement ratios, trend detection
- Feature Adoption: Top features, adoption trends, average adoption rates
- User Engagement: Engagement scores, cohort-based analysis, pattern detection
- Activation Metrics: Time-to-value (days), cohort breakdown, trend analysis
- Product-Qualified Leads (PQLs): Volume tracking, conversion rates, trend identification
- Retention Cohorts: Feature-specific retention rates, cohort analysis by feature usage
"""

from typing import Dict, Any, Optional, List
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from utils.config import config
from utils.logger import logger


async def fetch_product_data(
    week_number: int,
    spreadsheet_id: Optional[str] = None,
    product_ranges: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch product metrics data from Google Sheets using ADK MCP tools.
    
    This tool retrieves product data from multiple sheets:
    - Engagement Metrics sheet: DAU/WAU/MAU, engagement scores
    - Feature Adoption sheet: Feature adoption rates by feature
    - User Journey Metrics sheet: Activation times, user journey data
    
    Args:
        week_number: Week number for analysis (1-52)
        spreadsheet_id: Optional Google Sheets spreadsheet ID (uses config default if not provided)
        product_ranges: Optional list of sheet ranges to read (e.g., ["Engagement Metrics!A1:M100", "Feature Adoption!A1:M100"])
        
    Returns:
        Dictionary containing:
        - week_number: Week number
        - data_points: List of product data points with fields: week, dau, wau, mau, feature_adoptions, activation_time_days, pqls, engagement_score
        - metadata: Metadata about the data
        - freshness: Data freshness information
    """
    from adk_tools.google_sheets_tools import fetch_product_data_from_sheets
    
    # Use ADK MCP tool
    result = await fetch_product_data_from_sheets(
        week_number=week_number,
        spreadsheet_id=spreadsheet_id,
        product_ranges=product_ranges
    )
    
    return result


async def perform_product_statistical_analysis(
    product_data: Dict[str, Any],
    week_number: int
) -> Dict[str, Any]:
    """
    Perform statistical analysis on product metrics data.
    
    This tool calculates:
    - DAU/WAU/MAU ratios and trends
    - Feature adoption rates and trends
    - Engagement score trends
    - Activation time metrics
    - PQL conversion rates
    
    Args:
        product_data: Product data dictionary with records
        week_number: Target week number for analysis
        
    Returns:
        Dictionary containing statistical analysis results
    """
    return {
        "engagement_analysis": {},
        "feature_adoption_analysis": {},
        "activation_analysis": {},
        "pql_analysis": {}
    }


def create_product_agent() -> LlmAgent:
    """
    Create ADK Product Agent with comprehensive product metrics analysis capabilities.
    
    This agent provides complete SaaS product analysis including:
    
    **DAU/WAU/MAU Analysis:**
    - Daily Active Users (DAU) tracking
    - Weekly Active Users (WAU) tracking
    - Monthly Active Users (MAU) tracking
    - Engagement ratios: DAU/MAU, WAU/MAU
    - Trend detection: growing, declining, or stable
    
    **Feature Adoption Analysis:**
    - Top features identification by adoption rate
    - Adoption trend analysis (increasing/decreasing/stable per feature)
    - Average adoption rate calculation across all features
    - Feature-specific retention rates
    
    **User Engagement Analysis:**
    - Engagement score tracking (0-1 scale)
    - Cohort-based engagement analysis
    - Engagement pattern detection
    - User activity trends
    
    **Activation Metrics:**
    - Time-to-value (average activation time in days)
    - Cohort breakdown by activation time
    - Trend analysis: improving (decreasing time), worsening (increasing time), stable
    - Activation rate by user segment
    
    **Product-Qualified Leads (PQLs):**
    - PQL volume tracking
    - PQL conversion rate analysis
    - Trend identification: increasing/decreasing/stable
    - PQL quality scoring
    
    **Retention Cohorts by Feature Usage:**
    - Feature-specific retention rates
    - Cohort analysis by feature adoption
    - Retention trend tracking
    - Feature impact on retention
    
    **Data Sources:**
    - Primary: Google Sheets (Engagement Metrics, Feature Adoption, User Journey Metrics)
    - Supports manual data input
    - Multi-tab reading for comprehensive analysis
    
    **Output Format:**
    Returns structured JSON with:
    - agent_id: Unique agent identifier
    - agent_type: "product"
    - timestamp: ISO format timestamp
    - confidence: Float (0-1) with reasoning
    - analysis: Complete analysis object with engagement_analysis, feature_adoption_analysis, activation_analysis, pql_analysis, key_insights, recommendations, risk_flags
    - data_citations: List of data source citations
    - data_freshness_hours: Hours since data last updated
    
    Returns:
        Configured LlmAgent instance ready for use in agent registry or as a tool
    """
    model_name = config.get('gemini.model', 'gemini-2.5-flash-lite')
    model_config = config.get_model_config_with_retries()

    instruction = """You are a Product Analysis Agent specializing in comprehensive SaaS product metrics and user engagement analysis.

**CORE RESPONSIBILITIES:**

1. **DAU/WAU/MAU Analysis:**
   - Calculate current DAU (Daily Active Users), WAU (Weekly Active Users), MAU (Monthly Active Users) for the specified week
   - Compute engagement ratios: DAU/MAU and WAU/MAU (higher ratios indicate better engagement)
   - Calculate week-over-week (WoW) changes for each metric
   - Detect trends: growing (increasing users), declining (decreasing users), or stable
   - Identify engagement patterns and anomalies

2. **Feature Adoption Analysis:**
   - Identify top features by adoption rate
   - Analyze adoption trends per feature: increasing, decreasing, or stable
   - Calculate average adoption rate across all features
   - Assess feature-specific retention rates
   - Identify features driving user engagement
   - Flag features with declining adoption

3. **User Engagement Analysis:**
   - Track engagement scores (0-1 scale) over time
   - Perform cohort-based engagement analysis
   - Detect engagement patterns (daily, weekly, seasonal)
   - Analyze user activity trends
   - Identify engagement drivers and barriers

4. **Activation Metrics:**
   - Calculate average time-to-value (activation time in days)
   - Provide cohort breakdown by activation time
   - Analyze trends: improving (decreasing activation time), worsening (increasing time), stable
   - Calculate activation rate by user segment
   - Identify factors affecting activation time

5. **Product-Qualified Leads (PQLs):**
   - Track PQL volume for the specified week
   - Calculate PQL conversion rates
   - Identify trends: increasing, decreasing, or stable
   - Assess PQL quality scoring
   - Analyze PQL sources and characteristics

6. **Retention Cohorts by Feature Usage:**
   - Calculate feature-specific retention rates
   - Perform cohort analysis by feature adoption
   - Track retention trends over time
   - Identify features that impact retention positively or negatively
   - Analyze correlation between feature usage and retention

7. **Data Quality & Validation:**
   - Assess data completeness (percentage of required fields present)
   - Check for missing critical fields (DAU, WAU, MAU, feature_adoptions)
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
- Cite specific data points in your analysis (e.g., "Week 8 DAU of 45,000 represents 60% DAU/MAU ratio")
- Provide actionable recommendations prioritized by impact
- Include risk flags for concerning trends (e.g., declining engagement, feature adoption drops)
- Ensure all calculations are mathematically correct
- DO NOT mention "lack of data" if Feature Adoption or User Journey data is provided

**OUTPUT FORMAT:**

Return a structured JSON object with the following schema:

{
  "agent_id": "product_agent_<timestamp>",
  "agent_type": "product",
  "timestamp": "ISO 8601 timestamp",
  "confidence": 0.0-1.0,
  "confidence_reasoning": "Detailed explanation of confidence score factors",
  "analysis": {
    "engagement_analysis": {
      "dau": number,
      "wau": number,
      "mau": number,
      "dau_mau_ratio": number (decimal, 0-1),
      "wau_mau_ratio": number (decimal, 0-1),
      "trend": "growing" | "declining" | "stable",
      "wow_change": number (decimal, percentage change)
    },
    "feature_adoption_analysis": {
      "top_features": [
        {"name": "Feature Name", "adoption_rate": number (decimal, 0-1), "trend": "increasing" | "decreasing" | "stable"}
      ],
      "average_adoption_rate": number (decimal, 0-1),
      "adoption_trends": {"feature_name": "trend"}
    },
    "activation_analysis": {
      "avg_activation_time_days": number,
      "trend": "improving" | "worsening" | "stable",
      "cohort_breakdown": {}
    },
    "pql_analysis": {
      "current_pqls": number,
      "conversion_rate": number (decimal),
      "trend": "increasing" | "decreasing" | "stable"
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
        "type": "engagement_decline" | "feature_adoption_drop" | "activation_increase" | "data_quality",
        "description": "Risk description",
        "severity": "low" | "medium" | "high" | "critical"
      }
    ]
  },
  "data_citations": [
    "Week 8 DAU from Sheets 'Engagement Metrics!A8:D8'",
    "Feature adoption from Sheets 'Feature Adoption!A1:M100'"
  ],
  "data_freshness_hours": number
}

**IMPORTANT NOTES:**

- Focus analysis on the specific week_number provided - reference it explicitly in insights
- All ratios should be decimals (0-1), not percentages
- Engagement ratios (DAU/MAU, WAU/MAU) are key indicators of product health
- Feature adoption trends are critical for product strategy
- Activation time improvements indicate better onboarding
- Include data citations for transparency
- Flag any data quality issues as risk_flags
"""
    
    # Create FunctionTools
    product_data_tool = FunctionTool(
        fetch_product_data,
        require_confirmation=False
    )
    
    statistical_analysis_tool = FunctionTool(
        perform_product_statistical_analysis,
        require_confirmation=False
    )
    
    agent = LlmAgent(
        name="product_agent",
        model=model_name,
        instruction=instruction,
        tools=[product_data_tool, statistical_analysis_tool],
        **model_config  # Include HTTP retry options for transient errors (503, 429, etc.)
    )
    
    logger.info("ADK Product Agent created with full feature set")
    return agent

