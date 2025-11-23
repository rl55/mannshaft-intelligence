"""
Request models for API endpoints.
"""

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request model for triggering analysis."""
    week_number: int = Field(..., ge=1, le=52, description="Week number (1-52)")
    analysis_type: Literal["comprehensive", "quick", "deep_dive"] = Field(
        "comprehensive",
        description="Type of analysis to perform"
    )
    user_id: str = Field(..., description="User identifier")
    agent_types: Optional[List[str]] = Field(
        None,
        description="Optional list of specific agent types to execute"
    )


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
    decision: Literal["approved", "rejected", "modified"] = Field(
        ...,
        description="Human decision"
    )
    feedback: Optional[str] = Field(None, description="Optional human feedback")
    modifications: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional modifications made"
    )
    human_reviewer: Optional[str] = Field(None, description="Optional reviewer identifier")
