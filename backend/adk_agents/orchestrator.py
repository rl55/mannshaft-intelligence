"""
ADK Main Orchestrator (SequentialAgent)
Coordinates the end-to-end analysis workflow.

Architecture:
SequentialAgent (Main Orchestrator)
├── ParallelAgent (Analytical Coordinator)
│   ├── RevenueAgent (LlmAgent)
│   ├── ProductAgent (LlmAgent)
│   └── SupportAgent (LlmAgent)
├── SynthesizerAgent (LlmAgent with tools)
├── GovernanceAgent (Custom Agent Wrapper)
└── EvaluationAgent (LlmAgent)
"""

from google.adk.agents import SequentialAgent
from adk_agents.analytical_coordinator import create_analytical_coordinator
from adk_agents.synthesizer_agent import create_synthesizer_agent
from adk_agents.governance_agent import create_governance_agent
from adk_agents.evaluation_agent import create_evaluation_agent
from utils.logger import logger


def create_main_orchestrator() -> SequentialAgent:
    """
    Create ADK SequentialAgent orchestrator for end-to-end analysis workflow.
    
    This orchestrator coordinates the complete analysis lifecycle:
    1. ParallelAgent: Runs Revenue, Product, Support agents concurrently
    2. SynthesizerAgent: Cross-correlates insights and generates strategic recommendations
    3. GovernanceAgent: Validates against guardrails and escalates if needed
    4. EvaluationAgent: Evaluates quality and determines if regeneration is needed
    
    Architecture Flow:
    ```
    SequentialAgent (Main Orchestrator)
    │
    ├── ParallelAgent (Analytical Coordinator)
    │   ├── RevenueAgent (LlmAgent)
    │   ├── ProductAgent (LlmAgent)
    │   └── SupportAgent (LlmAgent)
    │
    ├── SynthesizerAgent (LlmAgent with tools)
    │
    ├── GovernanceAgent (Custom Agent Wrapper)
    │
    └── EvaluationAgent (LlmAgent)
    ```
    
    Returns:
        Configured SequentialAgent instance ready for execution
    """
    # Create all sub-agents
    analytical_coordinator = create_analytical_coordinator()
    synthesizer_agent = create_synthesizer_agent()
    governance_agent = create_governance_agent()
    evaluation_agent = create_evaluation_agent()
    
    # Create SequentialAgent orchestrator
    # Note: Governance and Evaluation are wrappers, not ADK agents
    # We'll need to integrate them properly - for now, creating SequentialAgent with
    # the agents that are ADK-compatible
    orchestrator = SequentialAgent(
        name="main_orchestrator",
        description="End-to-end SaaS BI analysis orchestrator coordinating analytical agents, synthesis, governance, and evaluation",
        sub_agents=[
            analytical_coordinator,  # ParallelAgent
            synthesizer_agent,        # LlmAgent
            # governance_agent and evaluation_agent need to be integrated differently
            # as they're wrappers around existing logic
            # TODO: Integrate governance and evaluation properly
        ]
    )
    
    logger.info("ADK Main Orchestrator (SequentialAgent) created")
    logger.warning("Governance and Evaluation agents need proper ADK integration - currently SequentialAgent only includes ParallelAgent and Synthesizer")
    
    return orchestrator

