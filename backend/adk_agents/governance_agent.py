"""
ADK Governance Agent (Custom Agent Wrapper)
Wraps existing backend/governance/guardrails.py logic for ADK integration.
Maintains same functionality: guardrail validation and HITL escalation.

This agent provides:
- Hard Guardrails: Cannot be overridden (PII detection, privacy, cost limits, hallucination detection)
- Adaptive Guardrails: Risk-scored policies that learn from feedback
- Rule Engine: Configurable rules with thresholds
- HITL Escalation: Escalates high-risk insights for human review
- Learning: Adapts thresholds based on HITL feedback

Note: This is a wrapper around the existing GuardrailAgent logic.
The actual validation logic remains in backend/governance/guardrails.py.
"""

from typing import Dict, Any, Optional
from utils.logger import logger

# Import existing governance logic
from governance.guardrails import GuardrailAgent, GuardrailResult
from governance.hitl_manager import HITLManager
from cache.cache_manager import CacheManager


class GovernanceAgentWrapper:
    """
    Wrapper for Governance Agent to integrate with ADK.
    
    This wraps the existing GuardrailAgent logic for use in ADK workflows.
    The actual validation logic remains in backend/governance/guardrails.py.
    
    This agent validates synthesized insights against:
    - Hard rules: PII detection, privacy, cost limits, hallucination detection
    - Adaptive rules: Risk-scored policies with learning capabilities
    
    Features:
    - Rule-based validation
    - HITL escalation for high-risk violations
    - Adaptive rule learning from feedback
    - Comprehensive violation tracking
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Governance Agent Wrapper.
        
        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager or CacheManager()
        self.guardrail_agent = GuardrailAgent(self.cache_manager)
        self.hitl_manager = HITLManager(self.cache_manager)
        self.logger = logger.getChild('governance_agent')
        self.name = "governance_agent"
        
        self.logger.info("ADK Governance Agent Wrapper initialized")
    
    async def validate(
        self,
        synthesized_response: Dict[str, Any],
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> GuardrailResult:
        """
        Validate synthesized response against guardrails.
        
        Args:
            synthesized_response: Synthesized insights to validate
            session_id: Session identifier
            trace_id: Optional trace identifier
            
        Returns:
            GuardrailResult with validation results
        """
        # Use existing GuardrailAgent logic
        result = await self.guardrail_agent.validate(
            agent_type='synthesizer',
            response=synthesized_response,
            session_id=session_id or "unknown",
            trace_id=trace_id
        )
        
        return result


def create_governance_agent(cache_manager: Optional[CacheManager] = None) -> GovernanceAgentWrapper:
    """
    Create ADK Governance Agent Wrapper.
    
    Returns:
        Configured GovernanceAgentWrapper instance
    """
    return GovernanceAgentWrapper(cache_manager=cache_manager)

