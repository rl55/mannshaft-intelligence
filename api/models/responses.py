"""
Response models for API endpoints.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """Response model for agent execution."""
    response: str = Field(..., description="Agent's response text")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    cached: bool = Field(False, description="Whether response was cached")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    trace_id: Optional[str] = Field(None, description="Trace ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class MultiAgentResponse(BaseModel):
    """Response model for multi-agent execution."""
    results: Dict[str, AgentResponse] = Field(..., description="Results by agent type")
    total_execution_time_ms: int = Field(..., description="Total execution time")


class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str = Field(..., description="Session ID")
    session_type: str = Field(..., description="Type of session")
    user_id: Optional[str] = Field(None, description="User identifier")
    status: str = Field(..., description="Session status")


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    stats: List[Dict[str, Any]] = Field(..., description="Cache statistics")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")
    cache: str = Field(..., description="Cache connection status")

