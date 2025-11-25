"""
ADK Governance Agent (Custom BaseAgent)
Proper ADK agent extending BaseAgent for guardrail validation and HITL escalation.

This agent provides:
- Hard Guardrails: Cannot be overridden (PII detection, privacy, cost limits, hallucination detection)
- Adaptive Guardrails: Risk-scored policies that learn from feedback
- Rule Engine: Configurable rules with thresholds
- HITL Escalation: Escalates high-risk insights for human review
- Learning: Adapts thresholds based on HITL feedback
"""

from typing import Dict, Any, Optional, AsyncGenerator
from google.adk.agents.base_agent import BaseAgent
from google.adk.events import Event
from utils.logger import logger

# Import existing governance logic
from governance.guardrails import GuardrailAgent, GuardrailResult
from cache.cache_manager import CacheManager


class GovernanceAgent(BaseAgent):
    """
    ADK Custom Agent for governance and guardrail validation.
    
    This agent validates synthesized insights against:
    - Hard rules: PII detection, privacy, cost limits, hallucination detection
    - Adaptive rules: Risk-scored policies with learning capabilities
    
    Features:
    - Rule-based validation (not LLM-driven)
    - HITL escalation for high-risk violations
    - Adaptive rule learning from feedback
    - Comprehensive violation tracking
    """
    
    # Use Pydantic model config to allow extra fields
    model_config = {"extra": "allow"}
    
    def __init__(self, cache_manager: Optional[CacheManager] = None, **kwargs):
        """
        Initialize Governance Agent.
        
        Args:
            cache_manager: Cache manager instance
            **kwargs: Additional BaseAgent parameters
        """
        # Initialize BaseAgent with name and description
        super().__init__(
            name="governance_agent",
            description="Validates synthesized insights against hard and adaptive guardrails",
            **kwargs
        )
        
        # Store cache_manager and guardrail_agent as instance attributes
        # Using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'cache_manager', cache_manager or CacheManager())
        object.__setattr__(self, 'guardrail_agent', GuardrailAgent(self.cache_manager))
        object.__setattr__(self, 'logger', logger.getChild('governance_agent'))
        
        self.logger.info("ADK Governance Agent initialized")
    
    async def run_async(self, parent_context) -> AsyncGenerator[Event, None]:
        """
        ADK agent execution method.
        
        Validates synthesized response against guardrails and escalates if needed.
        
        Args:
            parent_context: ADK InvocationContext from parent agent
            
        Yields:
            Event objects with validation results
        """
        try:
            # Extract synthesized response from context
            # In ADK, previous agent's output is typically in the context messages
            synthesized_response = None
            session_id = None
            trace_id = None
            
            # Try to get synthesized response from context
            # ADK context typically has messages from previous agents
            if hasattr(parent_context, 'messages') and parent_context.messages:
                # Get the last message which should be from SynthesizerAgent
                last_message = parent_context.messages[-1]
                if hasattr(last_message, 'content'):
                    # Parse content - could be JSON string or dict
                    import json
                    content = last_message.content
                    if isinstance(content, str):
                        try:
                            synthesized_response = json.loads(content)
                        except json.JSONDecodeError:
                            synthesized_response = {"raw_content": content}
                    elif isinstance(content, dict):
                        synthesized_response = content
            
            # Fallback: try to get from context attributes
            if not synthesized_response:
                if hasattr(parent_context, 'session_id'):
                    session_id = parent_context.session_id
                if hasattr(parent_context, 'trace_id'):
                    trace_id = parent_context.trace_id
                # Try to extract from context state
                if hasattr(parent_context, 'state'):
                    state = parent_context.state
                    if isinstance(state, dict):
                        synthesized_response = state.get('synthesized_response')
            
            if not synthesized_response:
                self.logger.warning("No synthesized response found in context, using empty dict")
                synthesized_response = {}
            
            # Get session_id and trace_id
            if hasattr(parent_context, 'session_id'):
                session_id = parent_context.session_id or "unknown"
            if hasattr(parent_context, 'trace_id'):
                trace_id = parent_context.trace_id
            
            # Validate against guardrails using existing logic
            # Note: GuardrailAgent.evaluate is synchronous, but we're in async context
            # We'll call it directly (it's fast, rule-based)
            result: GuardrailResult = self.guardrail_agent.evaluate(
                insights=synthesized_response,
                session_id=session_id or "unknown",
                trace_id=trace_id
            )
            
            # Create event with validation results
            event_content = {
                "validation_passed": result.passed,
                "violations": [
                    {
                        "rule_name": v.rule_name,
                        "rule_type": v.rule_type,
                        "severity": v.severity,
                        "details": v.details,
                        "reasoning": v.reasoning
                    }
                    for v in result.violations
                ],
                "risk_score": result.risk_score,
                "action": result.action,
                "reasoning": result.reasoning,
                "hitl_request_id": result.hitl_request_id
            }
            
            # Yield event
            event = Event(
                author=self.name,
                content=event_content
            )
            
            yield event
            
        except Exception as e:
            self.logger.error(f"Error in Governance Agent: {e}", exc_info=True)
            # Yield error event
            error_event = Event(
                author=self.name,
                content={
                    "error": str(e),
                    "validation_passed": False,
                    "action": "error"
                }
            )
            yield error_event


def create_governance_agent(cache_manager: Optional[CacheManager] = None) -> GovernanceAgent:
    """
    Create ADK Governance Agent.
    
    Returns:
        Configured GovernanceAgent instance
    """
    return GovernanceAgent(cache_manager=cache_manager)

