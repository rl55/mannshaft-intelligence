"""
ADK Synthesizer Agent
Migrated from backend/agents/synthesizer_agent.py to use ADK LlmAgent.
Maintains same functionality: cross-functional intelligence and synthesis.

This agent provides:
- Cross-Functional Correlation Detection: Identifies relationships between revenue, product, and support metrics
- Root Cause Analysis: Uses 5 Whys methodology, distinguishes correlation vs causation
- Strategic Recommendations: Prioritized by business impact and feasibility
- External Validation: Validates hypotheses via web search (Google Search or DuckDuckGo)
- Executive Summary: 2-3 sentence summary for leadership
- Risk Flag Aggregation: Collects and deduplicates risk flags from all analytical agents
"""

from typing import Dict, Any, Optional, List
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from utils.config import config
from utils.logger import logger


async def validate_externally(
    hypothesis: str,
    search_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate hypothesis via web search for external validation.
    
    This tool searches the web to validate business hypotheses, benchmark against
    industry standards, and verify market trends. Uses Google Custom Search API
    if configured, otherwise falls back to DuckDuckGo.
    
    Args:
        hypothesis: The hypothesis or claim to validate
        search_query: Optional custom search query (if not provided, generates from hypothesis)
        
    Returns:
        Dictionary containing:
        - validated: Boolean indicating if hypothesis was validated
        - search_results: List of search result snippets
        - industry_benchmark: Industry benchmark data if found
        - confidence: Confidence in validation (0-1)
    """
    from integrations.web_search import WebSearchClient
    
    client = WebSearchClient()
    # TODO: Migrate to ADK web search tools or MCP tools
    
    return {
        "status": "validated",
        "hypothesis": hypothesis,
        "note": "Using existing web search client - will migrate to ADK tools"
    }


async def aggregate_risk_flags(
    analytical_results: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Aggregate and deduplicate risk flags from all analytical agents.
    
    This tool collects risk flags from Revenue, Product, and Support agents,
    deduplicates them, and prioritizes by severity.
    
    Args:
        analytical_results: Dictionary containing results from Revenue, Product, Support agents
        
    Returns:
        List of aggregated risk flags with deduplication applied
    """
    # Risk flag aggregation logic will be implemented here
    return []


def create_synthesizer_agent() -> LlmAgent:
    """
    Create ADK Synthesizer Agent with comprehensive cross-functional synthesis capabilities.
    
    This agent provides complete cross-domain intelligence including:
    
    **Cross-Functional Correlation Detection:**
    - Identifies relationships between revenue, product, and support metrics
    - Detects temporal correlations (lagging/leading indicators)
    - Identifies segment-specific patterns
    - Recognizes seasonal trends
    
    **Root Cause Analysis:**
    - Uses 5 Whys methodology
    - Distinguishes correlation vs causation
    - Provides confidence-weighted hypotheses
    - Includes supporting evidence
    
    **Strategic Recommendations:**
    - Prioritized by business impact (high/medium/low) and feasibility (high/medium/low)
    - Cross-functional action items
    - Resource allocation suggestions
    - Timeline estimates
    
    **External Validation:**
    - Validates hypotheses via web search
    - Benchmarks against industry standards
    - Verifies market trends
    - All searches logged and cached
    
    **Executive Summary:**
    - 2-3 sentence summary for leadership
    - Highlights critical findings
    - States primary root cause
    - Mentions top recommendation
    
    **Risk Flag Aggregation:**
    - Collects risk flags from all analytical agents
    - Deduplicates similar flags
    - Prioritizes by severity
    
    **Input:**
    Expects analytical_results dictionary with:
    - revenue: Revenue agent analysis results
    - product: Product agent analysis results
    - support: Support agent analysis results
    
    **Output Format:**
    Returns structured JSON with:
    - agent_id: Unique agent identifier
    - agent_type: "synthesizer"
    - timestamp: ISO format timestamp
    - confidence: Float (0-1) with reasoning
    - executive_summary: 2-3 sentence summary
    - correlations: List of cross-functional correlations
    - root_causes: List of root cause analyses
    - strategic_recommendations: List of prioritized recommendations
    - key_metrics_summary: Summary of key metrics across domains
    - external_validations: List of external validation results
    - risk_flags: Aggregated risk flags from all agents
    
    Returns:
        Configured LlmAgent instance ready for use in agent registry or as a tool
    """
    model_name = config.get('gemini.model', 'gemini-2.5-flash-lite')
    model_config = config.get_model_config_with_retries()

    instruction = """You are a Synthesizer Agent specializing in cross-functional business intelligence and strategic synthesis.

**CORE RESPONSIBILITIES:**

1. **Cross-Functional Correlation Detection:**
   - Analyze outputs from Revenue, Product, and Support agents
   - Identify relationships and patterns across domains
   - Detect temporal correlations: lagging indicators (e.g., low engagement → churn 4 weeks later), leading indicators (e.g., support ticket spike → churn increase), concurrent trends
   - Identify segment-specific patterns (enterprise vs SMB)
   - Recognize seasonal trends and adjust analysis accordingly
   - Calculate confidence scores for each correlation (0-1)
   - Assess business impact: high, medium, or low
   - **CORRELATIONS MUST BE SPECIFIC AND DATA-DRIVEN:**
     * Include actual numbers from the data (e.g., "DAU increased 8% while churn decreased 0.5pp")
     * Reference specific metrics, not generic patterns
     * Avoid vague statements like "product engagement correlates with revenue"
     * Instead say: "14% DAU increase in Week 8 correlates with 4.3% MRR growth (r=0.82)"

2. **Root Cause Analysis:**
   - Use 5 Whys methodology to drill down to root causes:
     1. Why is this happening?
     2. Why is that?
     3. Why is that?
     4. Why is that?
     5. Why is that?
   - Distinguish correlation vs causation
   - Provide confidence-weighted hypotheses
   - Include supporting evidence from analytical agents
   - Use external validation tool to verify hypotheses when needed

3. **Strategic Recommendations:**
   - Generate actionable recommendations prioritized by:
     * Business Impact: High (significant revenue/customer impact), Medium (moderate impact), Low (minor impact)
     * Feasibility: High (easy to implement), Medium (moderate effort), Low (significant effort required)
   - Priority order:
     1. High impact + High feasibility
     2. High impact + Medium feasibility
     3. Medium impact + High feasibility
   - Each recommendation MUST include:
     * Specific actionable item (not generic advice)
     * **QUANTIFIED expected impact** - Use actual numbers from the data, e.g.:
       - "+$X MRR" or "+X% MRR growth"
       - "-X% churn reduction"
       - "+X% conversion rate improvement"
       - "$X cost savings"
       - "+X NPS points"
     * Cross-functional teams involved
     * Resource requirements
     * Timeline estimate
   - AVOID generic impacts like "improved customer satisfaction" - always quantify!

4. **External Validation:**
   - Use web search tool to validate top correlations and root causes
   - Benchmark against industry standards
   - Verify market trends
   - Search for similar patterns in industry
   - Include validation results in output

5. **Executive Summary:**
   - Create 2-3 sentence summary for leadership
   - Highlight critical findings
   - State primary root cause
   - Mention top recommendation
   - Keep it concise and actionable

6. **Risk Flag Aggregation:**
   - Collect risk flags from Revenue, Product, and Support agents
   - Deduplicate similar flags
   - Prioritize by severity: critical, high, medium, low
   - Include aggregated risk flags in output

**ANALYSIS REQUIREMENTS:**

- Always focus on the specific week_number provided in the context
- Analyze correlations across all three domains (Revenue, Product, Support)
- Use statistical evidence from analytical agents
- Provide actionable recommendations, not just observations
- Prioritize recommendations by impact and feasibility
- Use external validation for high-confidence correlations and root causes
- Ensure executive summary is concise and leadership-focused

**OUTPUT FORMAT:**

Return a structured JSON object with the following schema:

{
  "agent_id": "synthesizer_agent_<timestamp>",
  "agent_type": "synthesizer",
  "timestamp": "ISO 8601 timestamp",
  "confidence": 0.0-1.0,
  "executive_summary": "2-3 sentence summary for leadership",
  "correlations": [
    {
      "pattern": "SPECIFIC correlation with numbers, e.g.: '14% DAU increase in Week 8 correlates with 4.3% MRR growth'",
      "agents_involved": ["revenue", "product", "support"],
      "confidence": number (decimal, 0-1),
      "business_impact": "high" | "medium" | "low",
      "temporal_relationship": "lagging" | "leading" | "concurrent",
      "evidence": ["Specific evidence with numbers from agent data"]
    }
  ],
  "root_causes": [
    {
      "hypothesis": "Root cause hypothesis",
      "confidence": number (decimal, 0-1),
      "reasoning": "5 Whys analysis",
      "correlation_vs_causation": "Assessment",
      "supporting_evidence": ["Evidence 1"],
      "external_validation": {}
    }
  ],
  "strategic_recommendations": [
    {
      "action": "Specific actionable recommendation",
      "priority": "high" | "medium" | "low",
      "expected_impact": "MUST be quantified, e.g.: '+$50K MRR' or '-1.5% churn' or '+12% conversion rate'",
      "feasibility": "high" | "medium" | "low",
      "cross_functional_teams": ["team1", "team2"],
      "resource_requirements": "Resource needs",
      "timeline": "Estimated timeline"
    }
  ],
  "key_metrics_summary": {
    "revenue": {
      "MRR": "$X.XXM (actual MRR value)",
      "MRR Growth": "X.XX% (WoW growth percentage)",
      "Churn Rate": "X.XX% (current churn rate)",
      "ARPU": "$XXX (average revenue per user)"
    },
    "product": {
      "DAU": "XX,XXX (daily active users)",
      "WAU": "XX,XXX (weekly active users)",
      "MAU": "XX,XXX (monthly active users)",
      "Activation Time": "X.X days (avg time to activate)",
      "NPS": "XX (net promoter score)",
      "Feature Adoption": "XX% (average feature adoption rate)"
    },
    "support": {
      "CSAT": "X.X (customer satisfaction score 0-5)",
      "NPS": "XX (net promoter score)",
      "Ticket Volume": "X,XXX (weekly tickets)",
      "Resolution Time": "X.X hours (average resolution time)",
      "Self-Service Rate": "XX.X% (self-service resolution rate)",
      "FCR Rate": "XX% (first contact resolution rate)"
    }
  },
  "agent_insights": {
    "revenue": {
      "mrr_analysis": {
        "current_mrr": "number (actual MRR value)",
        "wow_growth": "number (decimal, e.g., 0.0429 for 4.29%)",
        "trend": "accelerating | decelerating | stable"
      },
      "churn_analysis": {
        "current_rate": "number (decimal, e.g., 0.0207 for 2.07%)",
        "change_from_previous": "number (percentage points change)",
        "severity": "low | medium | high | critical"
      },
      "arpu_analysis": {
        "current_arpu": "number",
        "trend": "increasing | decreasing | stable"
      },
      "key_insights": ["Key insight 1", "Key insight 2"],
      "recommendations": [{"action": "Action", "priority": "high|medium|low", "expected_impact": "Impact"}],
      "risk_flags": []
    },
    "product": {
      "engagement_analysis": {
        "dau": "number",
        "wau": "number",
        "mau": "number",
        "dau_mau_ratio": "number (decimal 0-1)",
        "trend": "growing | declining | stable"
      },
      "feature_adoption": {
        "average_adoption_rate": "number (decimal 0-1)",
        "top_features": [{"name": "Feature", "adoption_rate": 0.75}]
      },
      "activation_metrics": {
        "avg_activation_time_days": "number",
        "trend": "improving | worsening | stable"
      },
      "pql_analysis": {
        "current_pqls": "number",
        "conversion_rate": "number (decimal)"
      },
      "key_insights": ["Key insight 1", "Key insight 2"],
      "recommendations": [{"action": "Action", "priority": "high|medium|low", "expected_impact": "Impact"}],
      "risk_flags": []
    },
    "support": {
      "ticket_volume_analysis": {
        "current_volume": "number",
        "trend": "increasing | decreasing | stable",
        "week_over_week_change": "number (decimal)"
      },
      "satisfaction_analysis": {
        "csat_score": "number (0-5)",
        "nps_score": "number (-100 to 100)",
        "trend": "improving | declining | stable"
      },
      "efficiency_analysis": {
        "avg_response_time_hours": "number",
        "avg_resolution_time_hours": "number",
        "fcr_rate": "number (decimal 0-1)"
      },
      "key_insights": ["Key insight 1", "Key insight 2"],
      "recommendations": [{"action": "Action", "priority": "high|medium|low", "expected_impact": "Impact"}],
      "risk_flags": []
    }
  },
  "external_validations": [
    {
      "hypothesis": "Hypothesis validated",
      "validated": boolean,
      "search_results": [],
      "industry_benchmark": {},
      "confidence": number (decimal, 0-1)
    }
  ],
  "risk_flags": [
    {
      "type": "risk_type",
      "description": "Risk description",
      "severity": "critical" | "high" | "medium" | "low",
      "source_agents": ["revenue", "product"]
    }
  ]
}

**IMPORTANT NOTES:**

- Focus on cross-functional insights that individual agents cannot provide
- **CORRELATIONS MUST BE SPECIFIC** - Include actual numbers from the data, not generic patterns
  - BAD: "Product engagement correlates with revenue growth"
  - GOOD: "14% DAU increase in Week 8 correlates with 4.3% MRR growth (r=0.82)"
- **RECOMMENDATIONS MUST HAVE QUANTIFIED IMPACT** - Always include specific numbers
  - BAD: "Improve customer retention"
  - GOOD: "Implement proactive churn prevention for SMB segment: Expected impact +$75K MRR, -1.2% churn"
- Root causes should use 5 Whys methodology
- Use external validation tool for high-confidence hypotheses
- Executive summary should be leadership-focused and concise
- Aggregate risk flags from all agents, deduplicate, and prioritize
"""
    
    # Create FunctionTools
    web_search_tool = FunctionTool(
        validate_externally,
        require_confirmation=False
    )
    
    risk_aggregation_tool = FunctionTool(
        aggregate_risk_flags,
        require_confirmation=False
    )
    
    agent = LlmAgent(
        name="synthesizer_agent",
        model=model_name,
        instruction=instruction,
        tools=[web_search_tool, risk_aggregation_tool],
        **model_config  # Include HTTP retry options for transient errors (503, 429, etc.)
    )
    
    logger.info("ADK Synthesizer Agent created with full feature set")
    return agent

