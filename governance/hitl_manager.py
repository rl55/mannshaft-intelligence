"""
Human-in-the-loop (HITL) management system.
"""

from typing import Dict, Any, Optional
from enum import Enum

from utils.logger import logger
from cache.cache_manager import CacheManager


class HITLStatus(Enum):
    """Status of HITL requests."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    TIMEOUT = "timeout"


class HITLManager:
    """
    Manages human-in-the-loop escalations and approvals.
    """
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.logger = logger.getChild('hitl_manager')
    
    def create_request(self, trace_id: str, agent_type: str,
                      reason: str, context: Dict[str, Any],
                      proposed_action: Optional[str] = None) -> str:
        """
        Create a new HITL request.
        
        Args:
            trace_id: Associated trace ID
            agent_type: Type of agent
            reason: Reason for escalation
            context: Full context for human review
            proposed_action: Optional proposed action
            
        Returns:
            HITL request ID
        """
        request_id = self.cache_manager.create_hitl_request(
            trace_id=trace_id,
            agent_type=agent_type,
            reason=reason,
            context=context,
            proposed_action=proposed_action
        )
        
        self.logger.info(
            f"Created HITL request: {request_id}",
            extra={'request_id': request_id, 'trace_id': trace_id, 'reason': reason}
        )
        
        return request_id
    
    def resolve_request(self, request_id: str, status: HITLStatus,
                       human_decision: str, human_feedback: Optional[str] = None):
        """
        Resolve a HITL request.
        
        Args:
            request_id: HITL request ID
            status: Resolution status
            human_decision: Human's decision
            human_feedback: Optional feedback
        """
        self.cache_manager.resolve_hitl_request(
            request_id=request_id,
            status=status.value,
            human_decision=human_decision,
            human_feedback=human_feedback
        )
        
        self.logger.info(
            f"Resolved HITL request: {request_id}",
            extra={'request_id': request_id, 'status': status.value}
        )

