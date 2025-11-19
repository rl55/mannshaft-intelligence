"""
Response models for SaaS BI Agent API.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    """Response model for analysis endpoint."""

    success: bool = Field(..., description="Whether the analysis was successful")

    trace_id: str = Field(..., description="Unique trace ID for this request")

    session_id: str = Field(..., description="Session ID for this analysis")

    data: Optional[Any] = Field(None, description="Analysis results")

    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")

    cached: bool = Field(..., description="Whether result was from cache")

    execution_time_ms: int = Field(..., description="Execution time in milliseconds")

    error: Optional[str] = Field(None, description="Error message if failed")

    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "660e8400-e29b-41d4-a716-446655440000",
                "data": {
                    "mrr_trend": "Growing at 15% MoM",
                    "key_findings": ["Enterprise growth accelerating"],
                    "recommendations": ["Focus on annual contracts"]
                },
                "confidence": 0.92,
                "cached": False,
                "execution_time_ms": 1250,
                "metadata": {
                    "from_cache": False,
                    "input_tokens": 500,
                    "output_tokens": 1500
                }
            }
        }


class SessionResponse(BaseModel):
    """Response model for session operations."""

    session_id: str = Field(..., description="Unique session identifier")

    user_id: Optional[str] = Field(None, description="User ID if provided")

    session_type: str = Field(..., description="Type of session")

    start_time: datetime = Field(..., description="Session start timestamp")

    end_time: Optional[datetime] = Field(None, description="Session end timestamp")

    status: str = Field(
        ...,
        description="Session status (active, completed, error)"
    )

    total_agents_invoked: int = Field(
        0,
        description="Number of agents invoked in this session"
    )

    total_tokens_used: int = Field(
        0,
        description="Total tokens used in this session"
    )

    class Config:
        schema_extra = {
            "example": {
                "session_id": "660e8400-e29b-41d4-a716-446655440000",
                "user_id": "user-123",
                "session_type": "weekly_review",
                "start_time": "2025-01-15T10:30:00Z",
                "end_time": None,
                "status": "active",
                "total_agents_invoked": 0,
                "total_tokens_used": 0
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")

    version: str = Field(..., description="Application version")

    timestamp: datetime = Field(..., description="Current server timestamp")

    components: Dict[str, str] = Field(
        ...,
        description="Status of individual components"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-01-15T10:30:00Z",
                "components": {
                    "database": "healthy",
                    "cache": "healthy",
                    "gemini_api": "healthy"
                }
            }
        }


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    prompt_cache: Dict[str, Any] = Field(
        ...,
        description="Prompt cache statistics"
    )

    agent_cache: Dict[str, Any] = Field(
        ...,
        description="Agent response cache statistics"
    )

    performance: List[Dict[str, Any]] = Field(
        ...,
        description="Performance metrics over time"
    )

    class Config:
        schema_extra = {
            "example": {
                "prompt_cache": {
                    "total_entries": 150,
                    "total_hits": 450,
                    "hit_rate": 75.0,
                    "tokens_saved": 125000
                },
                "agent_cache": {
                    "total_entries": 45,
                    "total_hits": 120,
                    "hit_rate": 72.7
                },
                "performance": [
                    {
                        "date": "2025-01-15",
                        "total_entries": 150,
                        "total_hits": 450,
                        "hit_rate_percent": 75.0
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error message")

    error_type: str = Field(..., description="Error type/category")

    trace_id: Optional[str] = Field(None, description="Trace ID if available")

    timestamp: datetime = Field(..., description="Error timestamp")

    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )

    class Config:
        schema_extra = {
            "example": {
                "error": "Invalid input data format",
                "error_type": "ValidationError",
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-15T10:30:00Z",
                "details": {
                    "field": "data.records",
                    "issue": "Expected list, got string"
                }
            }
        }


class MetricsResponse(BaseModel):
    """Response model for metrics."""

    agent_performance: List[Dict[str, Any]] = Field(
        ...,
        description="Performance metrics by agent"
    )

    guardrail_stats: List[Dict[str, Any]] = Field(
        ...,
        description="Guardrail effectiveness statistics"
    )

    hitl_stats: List[Dict[str, Any]] = Field(
        ...,
        description="Human-in-the-loop statistics"
    )

    class Config:
        schema_extra = {
            "example": {
                "agent_performance": [
                    {
                        "agent_type": "revenue",
                        "total_invocations": 150,
                        "avg_duration_ms": 1250,
                        "success_rate": 98.5,
                        "cache_efficiency_percent": 65.0
                    }
                ],
                "guardrail_stats": [],
                "hitl_stats": []
            }
        }
