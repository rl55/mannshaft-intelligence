"""
Session management API routes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from api.models.requests import SessionCreateRequest
from api.models.responses import SessionResponse, SessionListResponse
from cache.cache_manager import CacheManager
from utils.logger import logger

router = APIRouter()


def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager()


@router.get("/", response_model=SessionListResponse)
async def get_sessions(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sessions"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get list of sessions.
    
    Args:
        limit: Maximum number of sessions to return
        offset: Offset for pagination
        
    Returns:
        List of sessions
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM sessions")
        total = cursor.fetchone()['total']
        
        # Get sessions
        cursor.execute("""
            SELECT session_id, session_type, user_id, status, 
                   timestamp as created_at, end_time as ended_at
            FROM sessions
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        
        sessions = [
            SessionResponse(
                session_id=row['session_id'],
                session_type=row['session_type'],
                user_id=row['user_id'],
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
                ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] and isinstance(row['ended_at'], str) else row['ended_at']
            )
            for row in rows
        ]
        
        return SessionListResponse(sessions=sessions, total=total)
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get session by ID.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session details
    """
    try:
        conn = cache_manager.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, session_type, user_id, status,
                   timestamp as created_at, end_time as ended_at
            FROM sessions
            WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=row['session_id'],
            session_type=row['session_type'],
            user_id=row['user_id'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
            ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] and isinstance(row['ended_at'], str) else row['ended_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Create a new analysis session.
    
    Args:
        request: Session creation request
        
    Returns:
        Session response
    """
    try:
        session_id = cache_manager.create_session(
            session_type=request.session_type,
            user_id=request.user_id
        )
        
        # Get created session
        conn = cache_manager.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, session_type, user_id, status,
                   timestamp as created_at, end_time as ended_at
            FROM sessions
            WHERE session_id = ?
        """, (session_id,))
        row = cursor.fetchone()
        
        return SessionResponse(
            session_id=row['session_id'],
            session_type=row['session_type'],
            user_id=row['user_id'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
            ended_at=None
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Delete a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
    """
    try:
        # End session first
        cache_manager.end_session(session_id, "deleted")
        
        return {"message": f"Session {session_id} deleted", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
