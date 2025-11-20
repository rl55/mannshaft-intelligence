"""
Monitoring and observability API routes.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from cache.cache_manager import CacheManager
from utils.logger import logger

router = APIRouter()


def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager()


@router.get("/agent-performance")
async def get_agent_performance():
    """
    Get agent performance statistics.
    
    Returns:
        Agent performance metrics
    """
    try:
        cache_manager = get_cache_manager()
        performance = cache_manager.get_agent_performance()
        
        return {"performance": performance}
    except Exception as e:
        logger.error(f"Error getting agent performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrail-effectiveness")
async def get_guardrail_effectiveness():
    """
    Get guardrail effectiveness statistics.
    
    Returns:
        Guardrail effectiveness metrics
    """
    try:
        cache_manager = get_cache_manager()
        effectiveness = cache_manager.get_guardrail_effectiveness()
        
        return {"effectiveness": effectiveness}
    except Exception as e:
        logger.error(f"Error getting guardrail effectiveness: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hitl-performance")
async def get_hitl_performance(days: int = 7):
    """
    Get HITL performance statistics.
    
    Args:
        days: Number of days to look back
        
    Returns:
        HITL performance metrics
    """
    try:
        cache_manager = get_cache_manager()
        performance = cache_manager.get_hitl_performance(days=days)
        
        return {"performance": performance}
    except Exception as e:
        logger.error(f"Error getting HITL performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

