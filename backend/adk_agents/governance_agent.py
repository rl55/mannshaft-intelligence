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
import json
from google.adk.agents.base_agent import BaseAgent
from google.adk.events import Event
from google.genai import types as genai_types
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
            # With LoopAgent (Synthesizer + Evaluation), we need to search for synthesizer output
            if hasattr(parent_context, 'messages') and parent_context.messages:
                # Search through messages for synthesizer output
                # Start from the end (most recent) and look backwards
                for message in reversed(parent_context.messages):
                    if not hasattr(message, 'content'):
                        continue
                    
                    content = message.content
                    content_str = None
                    
                    # Extract string content
                    if isinstance(content, str):
                        content_str = content
                    elif hasattr(content, 'parts') and content.parts:
                        text_parts = [p.text for p in content.parts if hasattr(p, 'text') and p.text]
                        if text_parts:
                            content_str = text_parts[0]
                    elif isinstance(content, dict):
                        synthesized_response = content
                        self.logger.info("Found synthesized response as dict in context")
                        break
                    
                    if content_str:
                        # Check if this looks like a synthesizer output (has executive_summary or report)
                        try:
                            parsed = json.loads(content_str)
                            if isinstance(parsed, dict):
                                # Check for synthesizer output markers
                                if any(key in parsed for key in ['executive_summary', 'report', 'summary', 'cross_functional_insights']):
                                    synthesized_response = parsed
                                    self.logger.info("Found synthesized response in context messages")
                                    break
                                # Also accept raw text that looks like a report
                                elif 'Executive Summary' in content_str:
                                    synthesized_response = {"raw_content": content_str, "executive_summary": content_str}
                                    self.logger.info("Found synthesized response as text in context")
                                    break
                        except json.JSONDecodeError:
                            # Not JSON - check if it's a text report
                            if 'Executive Summary' in content_str or 'Analysis Results' in content_str:
                                synthesized_response = {"raw_content": content_str, "executive_summary": content_str}
                                self.logger.info("Found synthesized response as raw text in context")
                                break
            
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
            
            # ADK Event.content must be a google.genai.types.Content object
            # Convert dict to JSON string and wrap in Content
            content_obj = genai_types.Content(
                parts=[genai_types.Part(text=json.dumps(event_content))],
                role="assistant"
            )
            
            # Yield event
            event = Event(
                author=self.name,
                content=content_obj
            )
            
            yield event
            
        except Exception as e:
            self.logger.error(f"Error in Governance Agent: {e}", exc_info=True)
            # Yield error event
            # ADK Event.content must be a google.genai.types.Content object
            error_content = {
                "error": str(e),
                "validation_passed": False,
                "action": "error"
            }
            content_obj = genai_types.Content(
                parts=[genai_types.Part(text=json.dumps(error_content))],
                role="assistant"
            )
            error_event = Event(
                author=self.name,
                content=content_obj
            )
            yield error_event


def create_governance_agent(cache_manager: Optional[CacheManager] = None) -> GovernanceAgent:
    """
    Create ADK Governance Agent.
    
    Returns:
        Configured GovernanceAgent instance
    """
    return GovernanceAgent(cache_manager=cache_manager)

