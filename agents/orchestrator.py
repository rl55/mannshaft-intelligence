"""
Core orchestrator for coordinating multiple agents.
"""

from typing import Dict, Any, List, Optional
import asyncio

from agents.base_agent import BaseAgent
from utils.logger import logger


class Orchestrator:
    """
    Orchestrates execution of multiple agents in parallel or sequence.
    """
    
    def __init__(self):
        self.logger = logger.getChild('orchestrator')
        self.agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent.agent_type] = agent
        self.logger.info(f"Registered agent: {agent.agent_type}")
    
    async def execute_parallel(self, agent_types: List[str], 
                              context: Dict[str, Any], 
                              session_id: str) -> Dict[str, Any]:
        """
        Execute multiple agents in parallel.
        
        Args:
            agent_types: List of agent types to execute
            context: Shared context for all agents
            session_id: Session identifier
            
        Returns:
            Dictionary mapping agent types to their results
        """
        tasks = []
        for agent_type in agent_types:
            if agent_type not in self.agents:
                self.logger.warning(f"Agent {agent_type} not registered")
                continue
            
            agent = self.agents[agent_type]
            tasks.append(agent.execute(context, session_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            agent_type: result if not isinstance(result, Exception) else {'error': str(result)}
            for agent_type, result in zip(agent_types, results)
        }
    
    async def execute_sequential(self, agent_types: List[str],
                                 context: Dict[str, Any],
                                 session_id: str,
                                 pass_results: bool = False) -> Dict[str, Any]:
        """
        Execute multiple agents sequentially, optionally passing results.
        
        Args:
            agent_types: List of agent types to execute in order
            context: Initial context
            session_id: Session identifier
            pass_results: Whether to pass previous results to next agent
            
        Returns:
            Dictionary mapping agent types to their results
        """
        results = {}
        current_context = context.copy()
        
        for agent_type in agent_types:
            if agent_type not in self.agents:
                self.logger.warning(f"Agent {agent_type} not registered")
                continue
            
            agent = self.agents[agent_type]
            result = await agent.execute(current_context, session_id)
            results[agent_type] = result
            
            if pass_results:
                current_context['previous_results'] = results
        
        return results

