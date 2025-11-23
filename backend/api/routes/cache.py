"""
Cache management API routes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta

from api.models.responses import CacheStatsResponse, CachePerformanceResponse
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
