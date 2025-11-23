"""
Monitoring and observability API routes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from datetime import datetime, timedelta

from api.models.responses import (
    AgentPerformanceResponse,
    GuardrailStatsResponse,
    HITLStatsResponse,
    GeminiUsageResponse
)
from cache.cache_manager import CacheManager
from utils.logger import logger

router = APIRouter()


def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager()


@router.get("/agents", response_model=List[AgentPerformanceResponse])
async def get_agent_performance(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get agent performance statistics.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Agent performance metrics
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get performance by agent type
        cursor.execute("""
            SELECT 
                agent_type,
                COUNT(*) as total_executions,
                AVG(execution_time_ms) as avg_execution_time,
                AVG(confidence_score) as avg_confidence,
                COUNT(*) FILTER (WHERE confidence_score >= 0.7) * 1.0 / COUNT(*) as success_rate
            FROM agent_responses
            WHERE timestamp >= ?
            GROUP BY agent_type
        """, (cutoff_date.isoformat(),))
        
        rows = cursor.fetchall()
        
        performance = [
            AgentPerformanceResponse(
                agent_type=row['agent_type'],
                total_executions=row['total_executions'],
                average_execution_time_ms=float(row['avg_execution_time'] or 0),
                success_rate=float(row['success_rate'] or 0),
                average_confidence=float(row['avg_confidence'] or 0)
            )
            for row in rows
        ]
        
        return performance
        
    except Exception as e:
        logger.error(f"Error getting agent performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails", response_model=GuardrailStatsResponse)
async def get_guardrail_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get guardrail effectiveness statistics.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Guardrail statistics
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get guardrail stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_checks,
                COUNT(*) FILTER (WHERE severity IN ('high', 'critical')) as violations,
                COUNT(*) FILTER (WHERE action_taken = 'blocked') as blocks,
                COUNT(*) FILTER (WHERE action_taken = 'escalated') as escalations
            FROM guardrail_events
            WHERE timestamp >= ?
        """, (cutoff_date.isoformat(),))
        
        row = cursor.fetchone()
        
        if not row:
            return GuardrailStatsResponse(
                total_checks=0,
                violations=0,
                blocks=0,
                escalations=0,
                violation_rate=0.0,
                period_days=days
            )
        
        total_checks = row['total_checks'] or 0
        violations = row['violations'] or 0
        blocks = row['blocks'] or 0
        escalations = row['escalations'] or 0
        
        violation_rate = violations / total_checks if total_checks > 0 else 0.0
        
        return GuardrailStatsResponse(
            total_checks=total_checks,
            violations=violations,
            blocks=blocks,
            escalations=escalations,
            violation_rate=violation_rate,
            period_days=days
        )
        
    except Exception as e:
        logger.error(f"Error getting guardrail stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hitl", response_model=HITLStatsResponse)
async def get_hitl_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get HITL performance statistics.
    
    Args:
        days: Number of days to look back
        
    Returns:
        HITL performance metrics
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get HITL stats
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'approved') as approved,
                COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
                COUNT(*) FILTER (WHERE status = 'modified') as modified,
                AVG(
                    (julianday(resolved_at) - julianday(timestamp)) * 24 * 60
                ) as avg_resolution_time
            FROM hitl_requests
            WHERE timestamp >= ?
        """, (cutoff_date.isoformat(),))
        
        row = cursor.fetchone()
        
        if not row:
            return HITLStatsResponse(
                pending=0,
                approved=0,
                rejected=0,
                modified=0,
                average_resolution_time_minutes=0.0,
                period_days=days
            )
        
        return HITLStatsResponse(
            pending=row['pending'] or 0,
            approved=row['approved'] or 0,
            rejected=row['rejected'] or 0,
            modified=row['modified'] or 0,
            average_resolution_time_minutes=float(row['avg_resolution_time'] or 0),
            period_days=days
        )
        
    except Exception as e:
        logger.error(f"Error getting HITL stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gemini-usage", response_model=GeminiUsageResponse)
async def get_gemini_usage(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get Gemini API usage statistics.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Gemini usage metrics
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get Gemini usage stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_requests,
                COALESCE(SUM(tokens_input), 0) as total_tokens_input,
                COALESCE(SUM(tokens_output), 0) as total_tokens_output,
                COUNT(*) FILTER (WHERE hit_count > 0) as cached_requests,
                COALESCE(SUM(tokens_saved), 0) as tokens_saved
            FROM prompt_cache
            WHERE timestamp >= ? AND model LIKE 'gemini%'
        """, (cutoff_date.isoformat(),))
        
        row = cursor.fetchone()
        
        if not row:
            return GeminiUsageResponse(
                total_requests=0,
                total_tokens_input=0,
                total_tokens_output=0,
                cached_requests=0,
                tokens_saved=0,
                average_tokens_per_request=0.0,
                period_days=days
            )
        
        total_requests = row['total_requests'] or 0
        total_input = row['total_tokens_input'] or 0
        total_output = row['total_tokens_output'] or 0
        cached = row['cached_requests'] or 0
        saved = row['tokens_saved'] or 0
        
        avg_tokens = (total_input + total_output) / total_requests if total_requests > 0 else 0.0
        
        return GeminiUsageResponse(
            total_requests=total_requests,
            total_tokens_input=int(total_input),
            total_tokens_output=int(total_output),
            cached_requests=cached,
            tokens_saved=int(saved),
            average_tokens_per_request=avg_tokens,
            period_days=days
        )
        
    except Exception as e:
        logger.error(f"Error getting Gemini usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
