"""
Request models for API endpoints.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request model for analysis endpoint."""
    agent_type: str = Field(..., description="Type of agent to use")
    context: Dict[str, Any] = Field(..., description="Input context for analysis")
    use_cache: bool = Field(True, description="Whether to use cached responses")
    session_id: Optional[str] = Field(None, description="Optional session ID")


class MultiAgentAnalysisRequest(BaseModel):
    """Request model for multi-agent analysis."""
    agent_types: List[str] = Field(..., description="List of agent types to execute")
    context: Dict[str, Any] = Field(..., description="Input context for analysis")
    execution_mode: str = Field("parallel", description="Execution mode: 'parallel' or 'sequential'")
    use_cache: bool = Field(True, description="Whether to use cached responses")
    session_id: Optional[str] = Field(None, description="Optional session ID")


class SessionCreateRequest(BaseModel):
    """Request model for creating a session."""
    session_type: str = Field(..., description="Type of session")
    user_id: Optional[str] = Field(None, description="Optional user identifier")


class HITLResolutionRequest(BaseModel):
    """Request model for resolving HITL requests."""
    request_id: str = Field(..., description="HITL request ID")
    status: str = Field(..., description="Resolution status")
    human_decision: str = Field(..., description="Human's decision")
    human_feedback: Optional[str] = Field(None, description="Optional feedback")

