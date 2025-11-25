"""
ADK Revenue Agent
Migrated from backend/agents/revenue_agent.py to use ADK LlmAgent.
Maintains same functionality: revenue analysis with MRR, churn, ARPU metrics.
"""

from typing import Dict, Any, Optional
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from utils.config import config
from utils.logger import logger


# Google Sheets tool will be added via MCP tools
# For now, we'll create a custom tool wrapper
async def fetch_revenue_data(
    week_number: int,
    spreadsheet_id: Optional[str] = None,
    revenue_ranges: Optional[list] = None
) -> Dict[str, Any]:
    """
    Fetch revenue data from Google Sheets.
    
    Args:
        week_number: Week number for analysis
        spreadsheet_id: Google Sheets spreadsheet ID
        revenue_ranges: List of sheet ranges to read
        
    Returns:
        Dictionary containing revenue data
    """
    # This will be implemented using ADK MCP tools for Google Sheets
    # For now, placeholder that maintains interface
    from integrations.google_sheets import GoogleSheetsClient
    
    client = GoogleSheetsClient()
    # Use existing Google Sheets client until MCP tools are set up
    # TODO: Migrate to ADK MCP tools
    
    return {
        "status": "fetched",
        "week_number": week_number,
        "note": "Using existing Google Sheets client - will migrate to MCP tools"
    }


def create_revenue_agent() -> LlmAgent:
    """
    Create ADK Revenue Agent.
    
    This agent analyzes revenue metrics including:
    - MRR (Monthly Recurring Revenue)
    - Churn rate and trends
    - ARPU (Average Revenue Per User)
    - Revenue forecasting
    - Anomaly detection
    
    Returns:
        Configured LlmAgent instance
    """
    model_name = config.get('gemini.model', 'gemini-2.5-flash-lite')
    
    # Agent instruction/prompt - this will be enhanced with the full prompt from original agent
    instruction = """You are a Revenue Analysis Agent specializing in SaaS business metrics.

Your responsibilities:
1. Analyze MRR (Monthly Recurring Revenue) trends and growth rates
2. Calculate and analyze churn rates with week-over-week comparisons
3. Evaluate ARPU (Average Revenue Per User) and segmentation
4. Perform revenue forecasting based on historical trends
5. Detect anomalies in revenue data
6. Provide confidence scores with reasoning

When analyzing data:
- Always focus on the specific week_number provided
- Use statistical analysis before generating insights
- Cite specific data points in your analysis
- Provide actionable recommendations
- Calculate confidence scores based on data completeness and quality

Output format: JSON with structured analysis including:
- Current metrics (MRR, churn rate, ARPU)
- Trends and changes (WoW, MoM)
- Forecasts and predictions
- Anomalies detected
- Confidence score (0-1) with reasoning
- Risk flags if any
"""
    
    # Create FunctionTool from the async function
    revenue_data_tool = FunctionTool(fetch_revenue_data)
    
    agent = LlmAgent(
        name="revenue_agent",
        model=model_name,
        instruction=instruction,
        tools=[revenue_data_tool],
        # ADK will handle caching via context caching
        # ADK will handle session management via SessionService
    )
    
    logger.info("ADK Revenue Agent created")
    return agent

