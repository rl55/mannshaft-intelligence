"""
ADK Analytical Coordinator (ParallelAgent)
Coordinates parallel execution of Revenue, Product, and Support agents.

This ParallelAgent runs the three analytical agents concurrently:
- Revenue Agent: MRR, churn, ARPU analysis
- Product Agent: DAU/WAU/MAU, feature adoption, engagement analysis
- Support Agent: Ticket volume, CSAT/NPS, efficiency analysis

All three agents execute in parallel for optimal performance.
"""

from google.adk.agents.workflow_agents import ParallelAgent
from adk_agents.revenue_agent import create_revenue_agent
from adk_agents.product_agent import create_product_agent
from adk_agents.support_agent import create_support_agent
from utils.logger import logger


def create_analytical_coordinator() -> ParallelAgent:
    """
    Create ADK ParallelAgent coordinator for analytical agents.
    
    This coordinator runs Revenue, Product, and Support agents in parallel.
    Each agent analyzes its respective domain independently, and results
    are aggregated for the Synthesizer Agent.
    
    Architecture:
    - Revenue Agent: Analyzes revenue metrics (MRR, churn, ARPU)
    - Product Agent: Analyzes product metrics (DAU/WAU/MAU, features, engagement)
    - Support Agent: Analyzes support metrics (tickets, CSAT/NPS, efficiency)
    
    All agents execute concurrently for optimal performance.
    
    Returns:
        Configured ParallelAgent instance
    """
    # Create individual analytical agents
    revenue_agent = create_revenue_agent()
    product_agent = create_product_agent()
    support_agent = create_support_agent()
    
    # Create ParallelAgent coordinator
    coordinator = ParallelAgent(
        name="analytical_coordinator",
        agents=[revenue_agent, product_agent, support_agent],
        # ParallelAgent will execute all agents concurrently
        # Results will be aggregated and passed to the next agent in the SequentialAgent workflow
    )
    
    logger.info("ADK Analytical Coordinator (ParallelAgent) created")
    return coordinator

