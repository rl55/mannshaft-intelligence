"""
Session management API routes.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from api.models.requests import SessionCreateRequest
from api.models.responses import SessionResponse
from cache.cache_manager import CacheManager
from utils.logger import logger

router = APIRouter()


def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager()


@router.post("/", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    """
    Create a new analysis session.
    
    Args:
        request: Session creation request
        
    Returns:
        Session response
    """
    try:
        cache_manager = get_cache_manager()
        session_id = cache_manager.create_session(
            session_type=request.session_type,
            user_id=request.user_id
        )
        
        return SessionResponse(
            session_id=session_id,
            session_type=request.session_type,
            user_id=request.user_id,
            status="active"
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/end")
async def end_session(session_id: str, final_status: str = "completed"):
    """
    End an analysis session.
    
    Args:
        session_id: Session identifier
        final_status: Final status ('completed', 'incomplete', 'error')
        
    Returns:
        Success message
    """
    try:
        cache_manager = get_cache_manager()
        cache_manager.end_session(session_id, final_status)
        
        return {"message": f"Session {session_id} ended", "status": final_status}
    except Exception as e:
        logger.error(f"Error ending session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

