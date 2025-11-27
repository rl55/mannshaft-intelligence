"""
ADK Main Orchestrator (SequentialAgent)
Coordinates the end-to-end analysis workflow.

Architecture:
SequentialAgent (Main Orchestrator)
├── ParallelAgent (Analytical Coordinator)
│   ├── RevenueAgent (LlmAgent)
│   ├── ProductAgent (LlmAgent)
│   └── SupportAgent (LlmAgent)
├── LoopAgent (Regeneration Loop)
│   ├── SynthesizerAgent (LlmAgent with tools)
│   └── EvaluationAgent (LlmAgent)
└── GovernanceAgent (Custom Agent Wrapper)
"""

from google.adk.agents import SequentialAgent
from adk_agents.analytical_coordinator import create_analytical_coordinator
from adk_agents.regeneration_loop import create_regeneration_loop
from adk_agents.governance_agent import create_governance_agent
from utils.logger import logger


def create_main_orchestrator() -> SequentialAgent:
    """
    Create ADK SequentialAgent orchestrator for end-to-end analysis workflow.
    
    This orchestrator coordinates the complete analysis lifecycle:
    1. ParallelAgent: Runs Revenue, Product, Support agents concurrently
    2. LoopAgent: Synthesizes report and evaluates quality, regenerates if needed
    3. GovernanceAgent: Validates against guardrails and escalates if needed
    
    Architecture Flow:
    ```
    SequentialAgent (Main Orchestrator)
    │
    ├── ParallelAgent (Analytical Coordinator)
    │   ├── RevenueAgent (LlmAgent)
    │   ├── ProductAgent (LlmAgent)
    │   └── SupportAgent (LlmAgent)
    │
    ├── LoopAgent (Regeneration Loop)
    │   ├── SynthesizerAgent (LlmAgent with tools)
    │   └── EvaluationAgent (LlmAgent)
    │
    └── GovernanceAgent (Custom Agent Wrapper)
    ```
    
    The LoopAgent automatically regenerates the synthesized report if evaluation
    fails quality threshold, up to max_iterations (default: 3).
    
    Returns:
        Configured SequentialAgent instance ready for execution
    """
    # Create all sub-agents
    analytical_coordinator = create_analytical_coordinator()
    regeneration_loop = create_regeneration_loop()  # LoopAgent wrapping Synthesizer + Evaluation
    governance_agent = create_governance_agent()
    
    # Create SequentialAgent orchestrator with all agents
    orchestrator = SequentialAgent(
        name="main_orchestrator",
        description="End-to-end SaaS BI analysis orchestrator coordinating analytical agents, synthesis with regeneration, and governance",
        sub_agents=[
            analytical_coordinator,  # ParallelAgent (Revenue, Product, Support)
            regeneration_loop,       # LoopAgent (Synthesizer + Evaluation with regeneration)
            governance_agent,         # BaseAgent (Guardrail validation)
        ]
    )
    
    logger.info("ADK Main Orchestrator (SequentialAgent) created with all agents")
    
    return orchestrator

