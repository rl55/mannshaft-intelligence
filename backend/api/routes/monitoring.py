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
        
        # Get guardrail stats from guardrail_violations table
        cursor.execute("""
            SELECT 
                COUNT(*) as total_checks,
                COUNT(*) FILTER (WHERE violation_severity IN ('high', 'critical')) as violations,
                COUNT(*) FILTER (WHERE action_taken = 'blocked') as blocks,
                COUNT(*) FILTER (WHERE action_taken = 'escalated') as escalations
            FROM guardrail_violations
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


@router.get("/guardrails/violations-over-time")
async def get_guardrail_violations_over_time(
    days: int = Query(14, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get guardrail violations over time (daily data for chart).
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as violations
            FROM guardrail_violations
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        """, (cutoff_date.isoformat(),))
        
        data_points = []
        for row in cursor.fetchall():
            data_points.append({
                'date': row['date'],
                'violations': row['violations']
            })
        
        # Fill in missing days with 0 violations
        if len(data_points) < days:
            start_date = datetime.utcnow() - timedelta(days=days)
            existing_dates = {dp['date'] for dp in data_points}
            for i in range(days):
                current_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                if current_date not in existing_dates:
                    data_points.append({
                        'date': current_date,
                        'violations': 0
                    })
        
        data_points.sort(key=lambda x: x['date'])
        
        return {
            'data': data_points,
            'period_days': days
        }
        
    except Exception as e:
        logger.error(f"Error getting violations over time: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/recent-violations")
async def get_recent_guardrail_violations(
    limit: int = Query(10, ge=1, le=100, description="Number of violations to return"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get recent guardrail violations.
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                timestamp,
                rule_name,
                violation_severity,
                action_taken,
                agent_type
            FROM guardrail_violations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        violations = []
        for row in cursor.fetchall():
            # Calculate time ago
            timestamp = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            now = datetime.utcnow().replace(tzinfo=timestamp.tzinfo)
            diff = now - timestamp
            
            if diff.total_seconds() < 60:
                time_ago = f"{int(diff.total_seconds())}s ago"
            elif diff.total_seconds() < 3600:
                time_ago = f"{int(diff.total_seconds() / 60)}m ago"
            elif diff.total_seconds() < 86400:
                time_ago = f"{int(diff.total_seconds() / 3600)}h ago"
            else:
                time_ago = f"{int(diff.total_seconds() / 86400)}d ago"
            
            violations.append({
                'time': time_ago,
                'rule': row['rule_name'],
                'severity': row['violation_severity'].capitalize() if row['violation_severity'] else 'Unknown',
                'action': row['action_taken'].capitalize() if row['action_taken'] else 'Unknown',
                'agent_type': row['agent_type'],
                'timestamp': row['timestamp']
            })
        
        return {
            'violations': violations,
            'total': len(violations)
        }
        
    except Exception as e:
        logger.error(f"Error getting recent violations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/effectiveness")
async def get_guardrail_effectiveness(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get guardrail effectiveness statistics by rule.
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                rule_name,
                COUNT(*) as triggers,
                SUM(CASE WHEN action_taken = 'blocked' THEN 1 ELSE 0 END) as blocks,
                SUM(CASE WHEN action_taken = 'escalated' THEN 1 ELSE 0 END) as escalations
            FROM guardrail_violations
            WHERE timestamp >= ?
            GROUP BY rule_name
            ORDER BY triggers DESC
        """, (cutoff_date.isoformat(),))
        
        effectiveness = []
        for row in cursor.fetchall():
            triggers = row['triggers'] or 0
            blocks = row['blocks'] or 0
            
            # Calculate accuracy (blocks / triggers, or 100% if no triggers but also no false positives)
            if triggers > 0:
                accuracy = (blocks / triggers) * 100
            else:
                accuracy = 100.0
            
            effectiveness.append({
                'rule': row['rule_name'],
                'triggers': triggers,
                'blocks': blocks,
                'escalations': row['escalations'] or 0,
                'accuracy': f"{accuracy:.0f}%"
            })
        
        return {
            'effectiveness': effectiveness,
            'period_days': days
        }
        
    except Exception as e:
        logger.error(f"Error getting guardrail effectiveness: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/severity-distribution")
async def get_guardrail_severity_distribution(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get guardrail violations by severity distribution.
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                violation_severity,
                COUNT(*) as count
            FROM guardrail_violations
            WHERE timestamp >= ?
            GROUP BY violation_severity
        """, (cutoff_date.isoformat(),))
        
        distribution = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for row in cursor.fetchall():
            severity = (row['violation_severity'] or 'low').lower()
            count = row['count'] or 0
            if severity in distribution:
                distribution[severity] = count
        
        return {
            'distribution': [
                {'name': 'Critical', 'value': distribution['critical']},
                {'name': 'High', 'value': distribution['high']},
                {'name': 'Medium', 'value': distribution['medium']},
                {'name': 'Low', 'value': distribution['low']}
            ],
            'period_days': days
        }
        
    except Exception as e:
        logger.error(f"Error getting severity distribution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/adaptive-rules")
async def get_adaptive_rules(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get adaptive guardrail rules with their current thresholds and adjustment counts.
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        # Try to get adaptive rules from database
        try:
            cursor.execute("""
                SELECT 
                    rule_name,
                    confidence_threshold as threshold,
                    COALESCE(trigger_count, 0) as adjustments
                FROM adaptive_rules
                WHERE is_active = 1
                ORDER BY rule_name
            """)
            
            rules = []
            for row in cursor.fetchall():
                rule_name = row['rule_name']
                # Format rule name (replace underscores, capitalize words)
                formatted_name = ' '.join(word.capitalize() for word in rule_name.split('_'))
                
                rules.append({
                    'rule': formatted_name,
                    'threshold': f"{row['threshold']:.2f}",
                    'adjustments': row['adjustments'] or 0,
                    'status': 'Active'
                })
            
            if rules:
                return {
                    'rules': rules,
                    'total': len(rules)
                }
        except Exception as e:
            # If table doesn't exist or query fails, return empty
            logger.debug(f"Could not fetch adaptive rules: {e}")
        
        # Fallback: return default adaptive rules from config
        return {
            'rules': [
                {
                    'rule': 'Low Confidence',
                    'threshold': '0.70',
                    'adjustments': 0,
                    'status': 'Active'
                },
                {
                    'rule': 'Anomaly Detector',
                    'threshold': '3.00',
                    'adjustments': 0,
                    'status': 'Active'
                }
            ],
            'total': 2
        }
        
    except Exception as e:
        logger.error(f"Error getting adaptive rules: {e}", exc_info=True)
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
