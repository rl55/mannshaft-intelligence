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
    
    # Create SequentialAgent orchestrator with all agents
    orchestrator = SequentialAgent(
        name="main_orchestrator",
        description="End-to-end SaaS BI analysis orchestrator coordinating analytical agents, synthesis, governance, and evaluation",
        sub_agents=[
            analytical_coordinator,  # ParallelAgent (Revenue, Product, Support)
            synthesizer_agent,        # LlmAgent (Cross-functional synthesis)
            governance_agent,         # BaseAgent (Guardrail validation)
            evaluation_agent,         # LlmAgent (Quality evaluation)
        ]
    )
    
    logger.info("ADK Main Orchestrator (SequentialAgent) created with all agents")
    
    return orchestrator

