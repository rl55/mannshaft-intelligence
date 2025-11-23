"""
Cache management API routes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
from typing import Optional, List

from api.models.responses import (
    CacheStatsResponse, 
    CachePerformanceResponse,
    CacheHitRateOverTimeResponse,
    CacheHitRateDataPoint,
    CacheEntriesResponse,
    CacheEntryResponse,
    CacheTypeDistributionResponse,
    TopCachedAgentsResponse,
    TopCachedAgentResponse
)
from cache.cache_manager import CacheManager
from utils.logger import logger

router = APIRouter()


def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager()


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get cache performance statistics.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Cache statistics
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Prompt cache stats
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE hit_count > 0) as hits,
                COUNT(*) FILTER (WHERE hit_count = 0) as misses,
                COALESCE(SUM(tokens_saved), 0) as tokens_saved
            FROM prompt_cache
            WHERE timestamp >= ?
        """, (cutoff_date.isoformat(),))
        
        prompt_row = cursor.fetchone()
        prompt_hits = prompt_row['hits'] if prompt_row else 0
        prompt_misses = prompt_row['misses'] if prompt_row else 0
        prompt_tokens_saved = prompt_row['tokens_saved'] if prompt_row else 0
        
        # Agent cache stats
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE cache_hit = 1) as hits,
                COUNT(*) FILTER (WHERE cache_hit = 0) as misses
            FROM agent_responses
            WHERE timestamp >= ?
        """, (cutoff_date.isoformat(),))
        
        agent_row = cursor.fetchone()
        agent_hits = agent_row['hits'] if agent_row else 0
        agent_misses = agent_row['misses'] if agent_row else 0
        
        # Calculate hit rate
        total_hits = prompt_hits + agent_hits
        total_misses = prompt_misses + agent_misses
        total_requests = total_hits + total_misses
        hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
        
        return CacheStatsResponse(
            prompt_cache_hits=prompt_hits,
            prompt_cache_misses=prompt_misses,
            agent_cache_hits=agent_hits,
            agent_cache_misses=agent_misses,
            total_tokens_saved=int(prompt_tokens_saved),
            cache_hit_rate=hit_rate,
            period_days=days
        )
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=CachePerformanceResponse)
async def get_cache_performance(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get cache performance metrics.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Cache performance metrics
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get average execution times for cache hits vs misses
        # This is a simplified version - in production, you'd track this more precisely
        cursor.execute("""
            SELECT 
                AVG(execution_time_ms) as avg_time,
                COUNT(*) as count
            FROM agent_responses
            WHERE timestamp >= ? AND cache_hit = 1
        """, (cutoff_date.isoformat(),))
        
        hit_row = cursor.fetchone()
        avg_hit_time = hit_row['avg_time'] if hit_row and hit_row['avg_time'] else 50.0
        hit_count = hit_row['count'] if hit_row else 0
        
        cursor.execute("""
            SELECT 
                AVG(execution_time_ms) as avg_time,
                COUNT(*) as count
            FROM agent_responses
            WHERE timestamp >= ? AND cache_hit = 0
        """, (cutoff_date.isoformat(),))
        
        miss_row = cursor.fetchone()
        avg_miss_time = miss_row['avg_time'] if miss_row and miss_row['avg_time'] else 2000.0
        miss_count = miss_row['count'] if miss_row else 0
        
        total_requests = hit_count + miss_count
        efficiency = hit_count / total_requests if total_requests > 0 else 0.0
        
        return CachePerformanceResponse(
            average_cache_hit_time_ms=float(avg_hit_time),
            average_cache_miss_time_ms=float(avg_miss_time),
            cache_efficiency=efficiency,
            total_requests=total_requests,
            period_days=days
        )
        
    except Exception as e:
        logger.error(f"Error getting cache performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hit-rate-over-time", response_model=CacheHitRateOverTimeResponse)
async def get_cache_hit_rate_over_time(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get cache hit rate over time (daily data for chart).
    
    Args:
        days: Number of days to look back
        
    Returns:
        Daily cache hit rate data
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily hit rate data
        cursor.execute("""
            SELECT 
                date(timestamp) as date,
                SUM(CASE WHEN hit_count > 0 THEN 1 ELSE 0 END) as hits,
                SUM(CASE WHEN hit_count = 0 THEN 1 ELSE 0 END) as misses
            FROM prompt_cache
            WHERE timestamp >= ?
            GROUP BY date(timestamp)
            ORDER BY date ASC
        """, (cutoff_date.isoformat(),))
        
        prompt_data = {row['date']: {'hits': row['hits'], 'misses': row['misses']} for row in cursor.fetchall()}
        
        # Get agent cache daily data
        cursor.execute("""
            SELECT 
                date(timestamp) as date,
                SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as hits,
                SUM(CASE WHEN cache_hit = 0 THEN 1 ELSE 0 END) as misses
            FROM agent_responses
            WHERE timestamp >= ?
            GROUP BY date(timestamp)
            ORDER BY date ASC
        """, (cutoff_date.isoformat(),))
        
        agent_data = {row['date']: {'hits': row['hits'], 'misses': row['misses']} for row in cursor.fetchall()}
        
        # Combine and calculate hit rates
        all_dates = set(prompt_data.keys()) | set(agent_data.keys())
        data_points = []
        
        for date in sorted(all_dates):
            prompt_hits = prompt_data.get(date, {}).get('hits', 0)
            prompt_misses = prompt_data.get(date, {}).get('misses', 0)
            agent_hits = agent_data.get(date, {}).get('hits', 0)
            agent_misses = agent_data.get(date, {}).get('misses', 0)
            
            total_hits = prompt_hits + agent_hits
            total_misses = prompt_misses + agent_misses
            total_requests = total_hits + total_misses
            
            hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
            
            data_points.append(CacheHitRateDataPoint(
                date=date,
                hit_rate=hit_rate
            ))
        
        # Fill in missing days with 0 hit rate if needed
        if len(data_points) < days:
            start_date = datetime.utcnow() - timedelta(days=days)
            existing_dates = {dp.date for dp in data_points}
            for i in range(days):
                current_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                if current_date not in existing_dates:
                    data_points.append(CacheHitRateDataPoint(
                        date=current_date,
                        hit_rate=0.0
                    ))
        
        data_points.sort(key=lambda x: x.date)
        
        return CacheHitRateOverTimeResponse(
            data=data_points,
            period_days=days
        )
        
    except Exception as e:
        logger.error(f"Error getting cache hit rate over time: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries", response_model=CacheEntriesResponse)
async def get_cache_entries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    cache_type: Optional[str] = Query(None, description="Filter by cache type: prompt, agent, eval"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get list of cache entries.
    
    Args:
        page: Page number
        page_size: Number of entries per page
        cache_type: Optional filter by cache type
        
    Returns:
        List of cache entries
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        offset = (page - 1) * page_size
        
        entries = []
        
        # Get prompt cache entries
        if cache_type is None or cache_type.lower() == "prompt":
            cursor.execute("""
                SELECT 
                    prompt_hash as id,
                    'prompt' as type,
                    hit_count as hits,
                    last_accessed,
                    ttl_hours,
                    timestamp as created_at
                FROM prompt_cache
                ORDER BY last_accessed DESC NULLS LAST, timestamp DESC
                LIMIT ? OFFSET ?
            """, (page_size, offset))
            
            for row in cursor.fetchall():
                last_accessed = row['last_accessed'] or row['created_at']
                if last_accessed:
                    last_accessed_dt = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                    last_accessed_str = _format_time_ago(last_accessed_dt)
                else:
                    last_accessed_str = "Never"
                
                ttl_hours = row['ttl_hours'] or 168
                ttl_str = _format_ttl(ttl_hours)
                
                entries.append(CacheEntryResponse(
                    id=f"p_{row['id'][:8]}",
                    type="Prompt",
                    hits=row['hits'] or 0,
                    last_accessed=last_accessed_str,
                    ttl=ttl_str,
                    created_at=row['created_at']
                ))
        
        # Get agent cache entries
        if cache_type is None or cache_type.lower() == "agent":
            cursor.execute("""
                SELECT 
                    context_hash as id,
                    agent_type,
                    COUNT(*) as hits,
                    MAX(last_accessed) as last_accessed,
                    MAX(ttl_hours) as ttl_hours,
                    MIN(timestamp) as created_at
                FROM agent_responses
                WHERE cache_hit = 1
                GROUP BY context_hash, agent_type
                ORDER BY last_accessed DESC NULLS LAST, created_at DESC
                LIMIT ? OFFSET ?
            """, (page_size, offset))
            
            for row in cursor.fetchall():
                last_accessed = row['last_accessed'] or row['created_at']
                if last_accessed:
                    last_accessed_dt = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                    last_accessed_str = _format_time_ago(last_accessed_dt)
                else:
                    last_accessed_str = "Never"
                
                ttl_hours = row['ttl_hours'] or 24
                ttl_str = _format_ttl(ttl_hours)
                
                entries.append(CacheEntryResponse(
                    id=f"a_{row['id'][:8]}",
                    type=row['agent_type'].capitalize(),
                    hits=row['hits'] or 0,
                    last_accessed=last_accessed_str,
                    ttl=ttl_str,
                    created_at=row['created_at']
                ))
        
        # Get total count
        if cache_type is None:
            cursor.execute("SELECT COUNT(*) as total FROM prompt_cache")
            prompt_count = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(DISTINCT context_hash) as total FROM agent_responses WHERE cache_hit = 1")
            agent_count = cursor.fetchone()['total']
            total = prompt_count + agent_count
        elif cache_type.lower() == "prompt":
            cursor.execute("SELECT COUNT(*) as total FROM prompt_cache")
            total = cursor.fetchone()['total']
        else:  # agent
            cursor.execute("SELECT COUNT(DISTINCT context_hash) as total FROM agent_responses WHERE cache_hit = 1")
            total = cursor.fetchone()['total']
        
        return CacheEntriesResponse(
            entries=entries[:page_size],  # Ensure we don't exceed page_size
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting cache entries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/type-distribution", response_model=CacheTypeDistributionResponse)
async def get_cache_type_distribution(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get cache type distribution.
    
    Returns:
        Distribution of cache entries by type
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        # Count prompt cache entries
        cursor.execute("SELECT COUNT(*) as total FROM prompt_cache")
        prompt_count = cursor.fetchone()['total'] or 0
        
        # Count agent cache entries
        cursor.execute("SELECT COUNT(DISTINCT context_hash) as total FROM agent_responses WHERE cache_hit = 1")
        agent_count = cursor.fetchone()['total'] or 0
        
        # Count eval cache entries (if any - currently not tracked separately)
        eval_count = 0
        
        return CacheTypeDistributionResponse(
            prompt=prompt_count,
            agent=agent_count,
            eval=eval_count
        )
        
    except Exception as e:
        logger.error(f"Error getting cache type distribution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-agents", response_model=TopCachedAgentsResponse)
async def get_top_cached_agents(
    limit: int = Query(5, ge=1, le=20, description="Number of top agents to return"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get top cached agents by cache hits.
    
    Args:
        limit: Number of top agents to return
        
    Returns:
        List of top cached agents
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                agent_type,
                COUNT(*) as cache_hits
            FROM agent_responses
            WHERE cache_hit = 1
            GROUP BY agent_type
            ORDER BY cache_hits DESC
            LIMIT ?
        """, (limit,))
        
        agents = []
        for row in cursor.fetchall():
            agents.append(TopCachedAgentResponse(
                agent_type=row['agent_type'].capitalize(),
                cache_hits=row['cache_hits'] or 0
            ))
        
        return TopCachedAgentsResponse(agents=agents)
        
    except Exception as e:
        logger.error(f"Error getting top cached agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _format_time_ago(dt: datetime) -> str:
    """Format datetime as relative time (e.g., '2 min ago')."""
    now = datetime.utcnow()
    diff = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt
    
    if diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())} sec ago"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() / 60)} min ago"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() / 3600)} hour{'s' if int(diff.total_seconds() / 3600) > 1 else ''} ago"
    else:
        days = int(diff.total_seconds() / 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"


def _format_ttl(hours: int) -> str:
    """Format TTL hours as readable string."""
    if hours < 24:
        return f"{hours}h"
    elif hours < 168:  # 7 days
        days = hours // 24
        return f"{days}d"
    else:
        weeks = hours // 168
        return f"{weeks}w"


@router.delete("/clear")
async def clear_cache(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Clear all cache entries.
    
    Returns:
        Success message
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        # Clear prompt cache
        cursor.execute("DELETE FROM prompt_cache")
        
        # Clear agent cache
        cursor.execute("DELETE FROM agent_responses")
        
        conn.commit()
        
        return {
            "message": "Cache cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
