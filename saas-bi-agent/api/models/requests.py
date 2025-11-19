"""
Request models for SaaS BI Agent API.
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field, validator


class AnalysisRequest(BaseModel):
    """Request model for analysis endpoint."""

    session_id: Optional[str] = Field(
        None,
        description="Session ID. If not provided, a new session will be created."
    )

    agent_type: str = Field(
        ...,
        description="Type of agent to invoke (revenue, product, support, orchestrator)"
    )

    data: Dict[str, Any] = Field(
        ...,
        description="Input data for analysis"
    )

    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for the analysis"
    )

    skip_cache: bool = Field(
        False,
        description="If True, bypass cache and force new generation"
    )

    user_id: Optional[str] = Field(
        None,
        description="Optional user identifier for tracking"
    )

    @validator('agent_type')
    def validate_agent_type(cls, v):
        """Validate agent type."""
        allowed_types = ['revenue', 'product', 'support', 'orchestrator', 'synthesizer']
        if v not in allowed_types:
            raise ValueError(
                f"Invalid agent_type. Must be one of: {', '.join(allowed_types)}"
            )
        return v

    class Config:
        schema_extra = {
            "example": {
                "agent_type": "revenue",
                "data": {
                    "period": "2025-Q4",
                    "mrr": 1250000,
                    "churn_rate": 3.2,
                    "arpu": 127
                },
                "context": {
                    "analysis_type": "comprehensive"
                },
                "skip_cache": False
            }
        }


class SessionCreateRequest(BaseModel):
    """Request model for creating a new session."""

    session_type: str = Field(
        "ad_hoc",
        description="Type of session (weekly_review, ad_hoc, investigation)"
    )

    user_id: Optional[str] = Field(
        None,
        description="Optional user identifier"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata for the session"
    )

    @validator('session_type')
    def validate_session_type(cls, v):
        """Validate session type."""
        allowed_types = ['weekly_review', 'ad_hoc', 'investigation', 'monitoring']
        if v not in allowed_types:
            raise ValueError(
                f"Invalid session_type. Must be one of: {', '.join(allowed_types)}"
            )
        return v

    class Config:
        schema_extra = {
            "example": {
                "session_type": "weekly_review",
                "user_id": "user-123",
                "metadata": {
                    "department": "finance",
                    "priority": "high"
                }
            }
        }


class CacheCleanupRequest(BaseModel):
    """Request model for cache cleanup."""

    force: bool = Field(
        False,
        description="If True, force cleanup even if not scheduled"
    )


class EvaluationRequest(BaseModel):
    """Request model for manual evaluation."""

    trace_id: str = Field(
        ...,
        description="Trace ID to evaluate"
    )

    override_scores: Optional[Dict[str, float]] = Field(
        None,
        description="Optional score overrides"
    )
