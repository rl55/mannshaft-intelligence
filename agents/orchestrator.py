"""
Core Orchestrator Agent for coordinating weekly SaaS analysis.

Coordinates multiple analytical agents, synthesizes results, applies governance,
and manages the complete analysis lifecycle from session creation to final report delivery.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.revenue_agent import RevenueAgent
from agents.product_agent import ProductAgent
from agents.support_agent import SupportAgent
from agents.synthesizer_agent import SynthesizerAgent
from cache.cache_manager import CacheManager
from governance.guardrails import Guardrails, GuardrailAgent, ViolationSeverity
from governance.evaluation import Evaluator
from governance.hitl_manager import HITLManager, HITLStatus
from utils.config import config
from utils.logger import logger


class AnalysisType(Enum):
    """Types of analysis that can be performed."""
    COMPREHENSIVE = "comprehensive"
    REVENUE_ONLY = "revenue_only"
    PRODUCT_ONLY = "product_only"
    SUPPORT_ONLY = "support_only"
    CUSTOM = "custom"


@dataclass
class AnalysisResult:
    """
    Result of a complete analysis orchestration.
    
    Attributes:
        report: Final synthesized report text
        session_id: Session identifier
        quality_score: Overall quality score (0-1)
        cache_efficiency: Cache hit rate (0-1)
        execution_time_ms: Total execution time in milliseconds
        agents_executed: List of agent types that were executed
        hitl_escalations: Number of HITL escalations during analysis
        guardrail_violations: Number of guardrail violations
        evaluation_passed: Whether evaluation passed
        regeneration_count: Number of regeneration attempts
        metadata: Additional metadata dictionary
    """
    report: str
    session_id: str
    quality_score: float = 0.0
    cache_efficiency: float = 0.0
    execution_time_ms: int = 0
    agents_executed: List[str] = field(default_factory=list)
    hitl_escalations: int = 0
    guardrail_violations: int = 0
    evaluation_passed: bool = False
    regeneration_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class OrchestratorAgent:
    """
    Core orchestrator agent for coordinating weekly SaaS analysis.
    
    Responsibilities:
    - Session management and lifecycle
    - Agent-to-Agent (A2A) coordination
    - Parallel agent execution (Revenue, Product, Support)
    - Data aggregation from analytical agents
    - Routing to Synthesizer
    - Integration with governance layer
    - HITL escalation handling
    
    Architecture Flow:
    1. Initialize session in CacheManager
    2. Spawn 3 analytical agents concurrently (asyncio.gather)
    3. Collect results and pass to Synthesizer
    4. Route synthesized insights through Guardrails
    5. Handle HITL escalations if needed
    6. Send to Evaluation Agent
    7. Handle regeneration loop if evaluation fails
    8. Deliver final report
    """
    
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        guardrails: Optional[Guardrails] = None,
        evaluator: Optional[Evaluator] = None,
        hitl_manager: Optional[HITLManager] = None
    ):
        """
        Initialize the orchestrator agent.
        
        Args:
            cache_manager: Cache manager instance (creates new if None)
            guardrails: Guardrails instance (creates new if None)
            evaluator: Evaluator instance (creates new if None)
            hitl_manager: HITL manager instance (creates new if None)
        """
        self.cache_manager = cache_manager or CacheManager(
            db_path=config.get('database.path', 'data/agent_cache.db'),
            schema_path=config.get('database.schema_path', 'data/schema.sql')
        )
        self.guardrails = guardrails or Guardrails()
        self.guardrail_agent = GuardrailAgent(self.cache_manager)  # Comprehensive guardrail agent
        self.evaluator = evaluator or Evaluator()
        self.hitl_manager = hitl_manager or HITLManager(self.cache_manager)
        
        self.logger = logger.getChild('orchestrator')
        
        # Initialize analytical agents
        self.revenue_agent = RevenueAgent(self.cache_manager)
        self.product_agent = ProductAgent(self.cache_manager)
        self.support_agent = SupportAgent(self.cache_manager)
        self.synthesizer_agent = SynthesizerAgent(self.cache_manager)
        
        # Agent registry
        self.agents: Dict[str, BaseAgent] = {
            'revenue': self.revenue_agent,
            'product': self.product_agent,
            'support': self.support_agent,
            'synthesizer': self.synthesizer_agent
        }
        
        # Configuration
        self.timeout_seconds = config.get('agents.timeout_seconds', 60)
        self.max_retries = config.get('agents.max_retries', 3)
        self.min_quality_score = config.get('agents.min_quality_score', 0.7)
        self.max_regenerations = config.get('agents.max_regenerations', 2)
        
        self.logger.info("OrchestratorAgent initialized")
    
    async def analyze_week(
        self,
        week_number: int,
        user_id: str,
        analysis_type: str = "comprehensive"
    ) -> AnalysisResult:
        """
        Coordinate weekly SaaS analysis across all agents.
        
        This is the main entry point for weekly analysis. It:
        1. Creates a session
        2. Executes analytical agents in parallel
        3. Synthesizes results
        4. Applies guardrails
        5. Evaluates quality
        6. Handles HITL escalations if needed
        7. Returns final report
        
        Args:
            week_number: Week number for analysis (e.g., 1-52)
            user_id: User identifier
            analysis_type: Type of analysis ("comprehensive", "revenue_only", etc.)
            
        Returns:
            AnalysisResult with:
            - report: Final synthesized report
            - session_id: Session identifier
            - quality_score: Overall quality (0-1)
            - cache_efficiency: Cache hit rate (0-1)
            - execution_time_ms: Total time
            - agents_executed: List of agents run
            - hitl_escalations: Number of escalations
            - guardrail_violations: Number of violations
            - evaluation_passed: Whether evaluation passed
            - regeneration_count: Number of regeneration attempts
            
        Raises:
            ValueError: If week_number is invalid
            RuntimeError: If analysis fails after all retries
        """
        start_time = time.time()
        session_id = None
        regeneration_count = 0
        
        try:
            # Validate inputs
            if not (1 <= week_number <= 52):
                raise ValueError(f"Invalid week_number: {week_number}. Must be between 1 and 52.")
            
            # Determine which agents to execute
            agent_types = self._get_agent_types_for_analysis(analysis_type)
            
            self.logger.info(
                f"Starting weekly analysis",
                extra={
                    'week_number': week_number,
                    'user_id': user_id,
                    'analysis_type': analysis_type,
                    'agent_types': agent_types
                }
            )
            
            # Step 1: Initialize session
            session_id = self.cache_manager.create_session(
                session_type=f"weekly_analysis_{analysis_type}",
                user_id=user_id
            )
            
            self.logger.info(f"Created session: {session_id}")
            
            # Main analysis loop with regeneration support
            while regeneration_count <= self.max_regenerations:
                try:
                    # Step 2: Execute analytical agents in parallel
                    analytical_results = await self._execute_analytical_agents(
                        agent_types=agent_types,
                        week_number=week_number,
                        session_id=session_id
                    )
                    
                    # Step 3: Synthesize results
                    synthesized_result = await self._synthesize_results(
                        analytical_results=analytical_results,
                        week_number=week_number,
                        session_id=session_id
                    )
                    
                    # Step 4: Apply guardrails
                    guardrail_violations = self._apply_guardrails(
                        response=synthesized_result,
                        session_id=session_id
                    )
                    
                    # Step 5: Handle HITL escalations if needed
                    hitl_escalations = await self._handle_hitl_escalations(
                        violations=guardrail_violations,
                        response=synthesized_result,
                        session_id=session_id
                    )
                    
                    # Step 6: Evaluate quality
                    evaluation_result = await self._evaluate_quality(
                        response=synthesized_result,
                        session_id=session_id
                    )
                    
                    # Step 7: Check if regeneration is needed
                    if evaluation_result.get('requires_review', False) or \
                       evaluation_result.get('overall_quality') == 'poor':
                        if regeneration_count < self.max_regenerations:
                            regeneration_count += 1
                            self.logger.warning(
                                f"Quality check failed, regenerating (attempt {regeneration_count})",
                                extra={'evaluation': evaluation_result}
                            )
                            continue
                    
                    # Step 8: Calculate metrics
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    cache_efficiency = self._calculate_cache_efficiency(session_id)
                    quality_score = self._calculate_quality_score(evaluation_result)
                    
                    # Step 9: End session
                    self.cache_manager.end_session(session_id, final_status='completed')
                    
                    # Step 10: Return final result
                    return AnalysisResult(
                        report=synthesized_result.get('response', ''),
                        session_id=session_id,
                        quality_score=quality_score,
                        cache_efficiency=cache_efficiency,
                        execution_time_ms=execution_time_ms,
                        agents_executed=agent_types,
                        hitl_escalations=hitl_escalations,
                        guardrail_violations=len(guardrail_violations),
                        evaluation_passed=evaluation_result.get('overall_quality') != 'poor',
                        regeneration_count=regeneration_count,
                        metadata={
                            'week_number': week_number,
                            'analysis_type': analysis_type,
                            'evaluation': evaluation_result,
                            'analytical_results': {
                                k: {
                                    'cached': v.get('cached', False),
                                    'execution_time_ms': v.get('execution_time_ms', 0),
                                    'confidence_score': v.get('confidence_score', 0.0)
                                }
                                for k, v in analytical_results.items()
                            }
                        }
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"Error in analysis loop (attempt {regeneration_count})",
                        extra={'error': str(e), 'session_id': session_id},
                        exc_info=True
                    )
                    
                    if regeneration_count < self.max_regenerations:
                        regeneration_count += 1
                        self.logger.info(f"Retrying analysis (attempt {regeneration_count})")
                        await asyncio.sleep(1)  # Brief delay before retry
                        continue
                    else:
                        raise
            
            # If we get here, all regeneration attempts failed
            raise RuntimeError(
                f"Analysis failed after {self.max_regenerations} regeneration attempts"
            )
            
        except Exception as e:
            self.logger.error(
                f"Fatal error in analyze_week",
                extra={'week_number': week_number, 'user_id': user_id, 'error': str(e)},
                exc_info=True
            )
            
            # Log error to cache manager
            if session_id:
                self.cache_manager.log_error(
                    agent_type='orchestrator',
                    error_type=type(e).__name__,
                    error_message=str(e),
                    trace_id=None,
                    context={'week_number': week_number, 'user_id': user_id},
                    severity='critical'
                )
                self.cache_manager.end_session(session_id, final_status='error')
            
            raise
    
    def _get_agent_types_for_analysis(self, analysis_type: str) -> List[str]:
        """
        Determine which agents to execute based on analysis type.
        
        Args:
            analysis_type: Type of analysis requested
            
        Returns:
            List of agent type strings to execute
        """
        analysis_type_enum = AnalysisType(analysis_type.lower())
        
        if analysis_type_enum == AnalysisType.COMPREHENSIVE:
            return ['revenue', 'product', 'support']
        elif analysis_type_enum == AnalysisType.REVENUE_ONLY:
            return ['revenue']
        elif analysis_type_enum == AnalysisType.PRODUCT_ONLY:
            return ['product']
        elif analysis_type_enum == AnalysisType.SUPPORT_ONLY:
            return ['support']
        else:
            # Default to comprehensive
            return ['revenue', 'product', 'support']
    
    async def _execute_analytical_agents(
        self,
        agent_types: List[str],
        week_number: int,
        session_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute analytical agents in parallel with error handling.
        
        Args:
            agent_types: List of agent types to execute
            week_number: Week number for context
            session_id: Session identifier
            
        Returns:
            Dictionary mapping agent types to their results
        """
        context = {
            'week_number': week_number,
            'analysis_type': 'weekly_review'
        }
        
        self.logger.info(
            f"Executing {len(agent_types)} analytical agents in parallel",
            extra={'agent_types': agent_types, 'session_id': session_id}
        )
        
        # Create tasks for parallel execution
        tasks = []
        for agent_type in agent_types:
            if agent_type not in self.agents:
                self.logger.warning(f"Agent {agent_type} not found, skipping")
                continue
            
            agent = self.agents[agent_type]
            task = self._execute_agent_with_timeout(
                agent=agent,
                context=context,
                session_id=session_id,
                agent_type=agent_type
            )
            tasks.append((agent_type, task))
        
        # Execute all agents concurrently
        results = {}
        for agent_type, task in tasks:
            try:
                result = await task
                results[agent_type] = result
                self.logger.info(
                    f"Agent {agent_type} completed",
                    extra={
                        'cached': result.get('cached', False),
                        'execution_time_ms': result.get('execution_time_ms', 0)
                    }
                )
            except asyncio.TimeoutError:
                self.logger.error(f"Agent {agent_type} timed out after {self.timeout_seconds}s")
                results[agent_type] = {
                    'response': f'Agent {agent_type} timed out',
                    'confidence_score': 0.0,
                    'cached': False,
                    'execution_time_ms': self.timeout_seconds * 1000,
                    'error': 'timeout'
                }
            except Exception as e:
                self.logger.error(
                    f"Agent {agent_type} failed",
                    extra={'error': str(e)},
                    exc_info=True
                )
                results[agent_type] = {
                    'response': f'Agent {agent_type} encountered an error: {str(e)}',
                    'confidence_score': 0.0,
                    'cached': False,
                    'execution_time_ms': 0,
                    'error': str(e)
                }
        
        return results
    
    async def _execute_agent_with_timeout(
        self,
        agent: BaseAgent,
        context: Dict[str, Any],
        session_id: str,
        agent_type: str
    ) -> Dict[str, Any]:
        """
        Execute an agent with timeout protection.
        
        Args:
            agent: Agent instance to execute
            context: Context dictionary
            session_id: Session identifier
            agent_type: Type of agent (for logging)
            
        Returns:
            Agent execution result
        """
        try:
            return await asyncio.wait_for(
                agent.execute(context, session_id),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            self.logger.error(
                f"Agent {agent_type} execution timed out",
                extra={'timeout_seconds': self.timeout_seconds}
            )
            raise
    
    async def _synthesize_results(
        self,
        analytical_results: Dict[str, Dict[str, Any]],
        week_number: int,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Synthesize results from analytical agents.
        
        Args:
            analytical_results: Results from analytical agents
            week_number: Week number
            session_id: Session identifier
            
        Returns:
            Synthesized result dictionary
        """
        self.logger.info("Synthesizing analytical results")
        
        # Prepare context for synthesizer
        synthesis_context = {
            'analytical_results': analytical_results,
            'week_number': week_number,
            'timestamp': datetime.now().isoformat()
        }
        
        # Execute synthesizer agent
        try:
            synthesized = await self.synthesizer_agent.execute(
                context=synthesis_context,
                session_id=session_id
            )
            
            self.logger.info("Synthesis completed successfully")
            return synthesized
            
        except Exception as e:
            self.logger.error(
                f"Synthesis failed: {e}",
                exc_info=True
            )
            # Fallback: create basic synthesis
            return {
                'response': self._create_fallback_synthesis(analytical_results, week_number),
                'confidence_score': 0.5,
                'cached': False,
                'execution_time_ms': 0
            }
    
    def _create_fallback_synthesis(
        self,
        analytical_results: Dict[str, Dict[str, Any]],
        week_number: int
    ) -> str:
        """
        Create a fallback synthesis when synthesizer fails.
        
        Args:
            analytical_results: Results from analytical agents
            week_number: Week number
            
        Returns:
            Fallback synthesis text
        """
        parts = [f"Week {week_number} Analysis Summary:\n"]
        
        for agent_type, result in analytical_results.items():
            if 'error' not in result:
                parts.append(f"\n{agent_type.capitalize()} Analysis:")
                parts.append(result.get('response', 'No response available'))
        
        return "\n".join(parts)
    
    def _apply_guardrails(
        self,
        response: Dict[str, Any],
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Apply guardrails to synthesized response using comprehensive GuardrailAgent.
        
        Args:
            response: Synthesized response
            session_id: Session identifier
            
        Returns:
            List of guardrail violations
        """
        if not config.get('governance.guardrails_enabled', True):
            return []
        
        self.logger.info("Applying guardrails")
        
        # Use comprehensive GuardrailAgent for synthesizer output
        try:
            guardrail_result = self.guardrail_agent.evaluate(
                insights=response,
                session_id=session_id,
                trace_id=None  # Could extract from response if available
            )
            
            # Convert violations to dict format for compatibility
            violations = [
                {
                    'rule_name': v.rule_name,
                    'rule_type': v.rule_type,
                    'severity': v.severity,
                    'details': v.details,
                    'reasoning': v.reasoning
                }
                for v in guardrail_result.violations
            ]
            
            # Log action taken
            if guardrail_result.action == 'block':
                self.logger.error(
                    f"Guardrails BLOCKED response: {guardrail_result.reasoning}",
                    extra={'violations': violations, 'risk_score': guardrail_result.risk_score}
                )
            elif guardrail_result.action == 'escalate_hitl':
                self.logger.warning(
                    f"Guardrails ESCALATED to HITL: {guardrail_result.reasoning}",
                    extra={'hitl_request_id': guardrail_result.hitl_request_id}
                )
            elif guardrail_result.action == 'warn':
                self.logger.warning(
                    f"Guardrails WARNING: {guardrail_result.reasoning}",
                    extra={'violations': violations}
                )
            
            return violations
            
        except Exception as e:
            self.logger.error(
                f"Error applying guardrails: {e}",
                exc_info=True
            )
            # Fallback to simple guardrails
            violations = self.guardrails.validate(
                agent_type='synthesizer',
                response=response,
                trace_id=None
            )
            return violations
    
    async def _handle_hitl_escalations(
        self,
        violations: List[Dict[str, Any]],
        response: Dict[str, Any],
        session_id: str
    ) -> int:
        """
        Handle HITL escalations if needed.
        
        Args:
            violations: List of guardrail violations
            response: Synthesized response
            session_id: Session identifier
            
        Returns:
            Number of HITL escalations created
        """
        if not config.get('governance.hitl_enabled', True):
            return 0
        
        hitl_count = 0
        
        # Check for critical violations that require HITL
        critical_violations = [
            v for v in violations
            if v.get('severity') in ['high', 'critical']
        ]
        
        for violation in critical_violations:
            try:
                request_id = self.hitl_manager.create_request(
                    trace_id=None,  # Could extract from response
                    agent_type='synthesizer',
                    reason=f"Guardrail violation: {violation['rule_name']}",
                    context={
                        'violation': violation,
                        'response': response,
                        'session_id': session_id
                    },
                    proposed_action=response.get('response', '')
                )
                hitl_count += 1
                self.logger.info(
                    f"Created HITL request: {request_id}",
                    extra={'request_id': request_id, 'violation': violation['rule_name']}
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to create HITL request: {e}",
                    exc_info=True
                )
        
        return hitl_count
    
    async def _evaluate_quality(
        self,
        response: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate the quality of the synthesized response.
        
        Args:
            response: Synthesized response
            session_id: Session identifier
            
        Returns:
            Evaluation result dictionary
        """
        if not config.get('governance.evaluation_enabled', True):
            return {
                'overall_quality': 'acceptable',
                'requires_review': False
            }
        
        self.logger.info("Evaluating response quality")
        
        try:
            evaluation_result = await self.evaluator.evaluate(
                agent_type='synthesizer',
                response=response,
                trace_id=None  # Could extract from response
            )
            
            # Record evaluation in cache manager
            if evaluation_result:
                self.cache_manager.record_evaluation(
                    trace_id=None,  # Could extract from response
                    agent_type='synthesizer',
                    factual_grounding_score=evaluation_result.get('factual_grounding_score', 0.0),
                    relevance_score=evaluation_result.get('relevance_score', 0.0),
                    completeness_score=evaluation_result.get('completeness_score', 0.0),
                    coherence_score=evaluation_result.get('coherence_score', 0.0),
                    data_citations_present=evaluation_result.get('data_citations_present', False),
                    confidence_calibrated=evaluation_result.get('confidence_calibrated', False),
                    anomalies_flagged=evaluation_result.get('anomalies_flagged', False),
                    overall_quality=evaluation_result.get('overall_quality', 'acceptable'),
                    evaluator_agent='evaluator',
                    evaluation_time_ms=0,  # Could track this
                    requires_review=evaluation_result.get('requires_review', False),
                    review_reason=evaluation_result.get('review_reason')
                )
            
            return evaluation_result
            
        except Exception as e:
            self.logger.error(
                f"Evaluation failed: {e}",
                exc_info=True
            )
            # Return default evaluation
            return {
                'overall_quality': 'acceptable',
                'requires_review': False
            }
    
    def _calculate_cache_efficiency(self, session_id: str) -> float:
        """
        Calculate cache efficiency for the session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Cache efficiency ratio (0-1)
        """
        try:
            # Query cache stats from database using traces
            conn = self.cache_manager.connect()
            cursor = conn.cursor()
            
            # Count total tokens and cached tokens from traces
            cursor.execute("""
                SELECT 
                    SUM(input_tokens + output_tokens) as total_tokens,
                    SUM(cached_tokens) as cached_tokens
                FROM traces
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row and row['total_tokens'] and row['total_tokens'] > 0:
                efficiency = row['cached_tokens'] / row['total_tokens']
                return min(max(efficiency, 0.0), 1.0)  # Clamp between 0 and 1
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating cache efficiency: {e}", exc_info=True)
            return 0.0
    
    def _calculate_quality_score(self, evaluation_result: Dict[str, Any]) -> float:
        """
        Calculate overall quality score from evaluation result.
        
        Args:
            evaluation_result: Evaluation result dictionary
            
        Returns:
            Quality score (0-1)
        """
        if not evaluation_result:
            return 0.5  # Default score
        
        # Calculate weighted average of scores
        scores = [
            evaluation_result.get('factual_grounding_score', 0.0),
            evaluation_result.get('relevance_score', 0.0),
            evaluation_result.get('completeness_score', 0.0),
            evaluation_result.get('coherence_score', 0.0)
        ]
        
        # Filter out None values
        valid_scores = [s for s in scores if s is not None]
        
        if not valid_scores:
            return 0.5
        
        return sum(valid_scores) / len(valid_scores)


# Backward compatibility: Keep the simple Orchestrator class for existing code
class Orchestrator:
    """
    Simple orchestrator for basic agent coordination.
    Kept for backward compatibility.
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
        """Execute multiple agents in parallel."""
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
        """Execute multiple agents sequentially."""
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
