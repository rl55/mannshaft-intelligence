"""
Response models for API endpoints.
"""

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    """Response model for analysis trigger."""
    session_id: str = Field(..., description="Session identifier")
    status: Literal["queued", "running", "completed", "failed"] = Field(
        ...,
        description="Analysis status"
    )
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    estimated_time_remaining_seconds: Optional[int] = Field(
        None,
        description="Estimated time remaining in seconds"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class AnalysisResult(BaseModel):
    """Response model for analysis result."""
    session_id: str = Field(..., description="Session identifier")
    week_number: int = Field(..., ge=1, le=52, description="Week number")
    report: Dict[str, Any] = Field(..., description="Analysis report")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    cache_efficiency: float = Field(..., ge=0.0, le=1.0, description="Cache efficiency")
    agents_executed: List[str] = Field(..., description="List of agents executed")
    hitl_escalations: int = Field(..., ge=0, description="Number of HITL escalations")
    guardrail_violations: int = Field(..., ge=0, description="Number of guardrail violations")
    generated_at: datetime = Field(..., description="Generation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status."""
    session_id: str = Field(..., description="Session identifier")
    status: Literal["queued", "running", "completed", "failed"] = Field(
        ...,
        description="Analysis status"
    )
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current step in analysis")
    estimated_time_remaining_seconds: Optional[int] = Field(
        None,
        description="Estimated time remaining"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    result: Optional[AnalysisResult] = Field(None, description="Result if completed")


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
    created_at: datetime = Field(..., description="Creation timestamp")
    ended_at: Optional[datetime] = Field(None, description="End timestamp")


class SessionListResponse(BaseModel):
    """Response model for session list."""
    sessions: List[SessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    prompt_cache_hits: int = Field(..., description="Prompt cache hits")
    prompt_cache_misses: int = Field(..., description="Prompt cache misses")
    agent_cache_hits: int = Field(..., description="Agent cache hits")
    agent_cache_misses: int = Field(..., description="Agent cache misses")
    total_tokens_saved: int = Field(..., description="Total tokens saved")
    cache_hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate")
    period_days: int = Field(..., description="Period in days")


class CachePerformanceResponse(BaseModel):
    """Response model for cache performance."""
    average_cache_hit_time_ms: float = Field(..., description="Average cache hit time")
    average_cache_miss_time_ms: float = Field(..., description="Average cache miss time")
    cache_efficiency: float = Field(..., ge=0.0, le=1.0, description="Cache efficiency")
    total_requests: int = Field(..., description="Total requests")
    period_days: int = Field(..., description="Period in days")


class AgentPerformanceResponse(BaseModel):
    """Response model for agent performance."""
    agent_type: str = Field(..., description="Agent type")
    total_executions: int = Field(..., description="Total executions")
    average_execution_time_ms: float = Field(..., description="Average execution time")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate")
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence")


class GuardrailStatsResponse(BaseModel):
    """Response model for guardrail statistics."""
    total_checks: int = Field(..., description="Total guardrail checks")
    violations: int = Field(..., description="Number of violations")
    blocks: int = Field(..., description="Number of blocks")
    escalations: int = Field(..., description="Number of escalations")
    violation_rate: float = Field(..., ge=0.0, le=1.0, description="Violation rate")
    period_days: int = Field(..., description="Period in days")


class HITLStatsResponse(BaseModel):
    """Response model for HITL statistics."""
    pending: int = Field(..., description="Pending requests")
    approved: int = Field(..., description="Approved requests")
    rejected: int = Field(..., description="Rejected requests")
    modified: int = Field(..., description="Modified requests")
    average_resolution_time_minutes: float = Field(
        ...,
        description="Average resolution time"
    )
    period_days: int = Field(..., description="Period in days")


class GeminiUsageResponse(BaseModel):
    """Response model for Gemini usage statistics."""
    total_requests: int = Field(..., description="Total requests")
    total_tokens_input: int = Field(..., description="Total input tokens")
    total_tokens_output: int = Field(..., description="Total output tokens")
    cached_requests: int = Field(..., description="Cached requests")
    tokens_saved: int = Field(..., description="Tokens saved via caching")
    average_tokens_per_request: float = Field(..., description="Average tokens per request")
    period_days: int = Field(..., description="Period in days")


class HITLPendingResponse(BaseModel):
    """Response model for pending HITL requests."""
    request_id: str = Field(..., description="Request ID")
    session_id: str = Field(..., description="Session ID")
    escalation_reason: str = Field(..., description="Reason for escalation")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score")
    created_at: datetime = Field(..., description="Creation timestamp")
    review_url: Optional[str] = Field(None, description="Review URL")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")
    cache: str = Field(..., description="Cache connection status")
