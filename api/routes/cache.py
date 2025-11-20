"""
Cache management API routes.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from api.models.responses import CacheStatsResponse
from cache.cache_manager import CacheManager
from utils.logger import logger

router = APIRouter()


def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager()


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(days: int = 7):
    """
    Get cache performance statistics.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Cache statistics
    """
    try:
        cache_manager = get_cache_manager()
        stats = cache_manager.get_cache_stats(days=days)
        
        return CacheStatsResponse(stats=stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_cache():
    """
    Clean up expired cache entries.
    
    Returns:
        Cleanup results
    """
    try:
        cache_manager = get_cache_manager()
        result = cache_manager.cleanup_expired_cache()
        
        return {
            "message": "Cache cleanup completed",
            "results": result
        }
    except Exception as e:
        logger.error(f"Error cleaning up cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

