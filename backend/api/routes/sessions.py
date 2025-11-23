"""
Session management API routes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from api.models.requests import SessionCreateRequest
from api.models.responses import SessionResponse, SessionListResponse
from database.db_manager import get_db_manager, DatabaseManager
from utils.logger import logger

router = APIRouter()


def get_db() -> DatabaseManager:
    """Get database manager instance."""
    return get_db_manager()


@router.get("/", response_model=SessionListResponse)
async def get_sessions(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of sessions"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db_manager: DatabaseManager = Depends(get_db)
):
    """
    Get list of sessions from database.
    
    Args:
        limit: Maximum number of sessions to return
        offset: Offset for pagination
        user_id: Optional filter by user ID
        status: Optional filter by status
        
    Returns:
        List of sessions
    """
    try:
        sessions_data = db_manager.list_sessions(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        sessions = [
            SessionResponse(
                session_id=session['session_id'],
                session_type=session['session_type'],
                user_id=session.get('user_id'),
                status=session.get('current_status') or session.get('status', 'unknown'),
                created_at=session['created_at'] if isinstance(session['created_at'], datetime) else datetime.fromisoformat(session['created_at']),
                ended_at=session.get('completed_at') or session.get('failed_at') or session.get('ended_at')
            )
            for session in sessions_data
        ]
        
        # Get total count (would need separate query for accurate count with filters)
        # For now, return the length as total (not ideal but works)
        total = len(sessions_data)
        
        return SessionListResponse(sessions=sessions, total=total)
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db_manager: DatabaseManager = Depends(get_db)
):
    """
    Get session by ID from database.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session details
    """
    try:
        session = db_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session['session_id'],
            session_type=session['session_type'],
            user_id=session.get('user_id'),
            status=session.get('current_status') or session.get('status', 'unknown'),
            created_at=session['created_at'] if isinstance(session['created_at'], datetime) else datetime.fromisoformat(session['created_at']),
            ended_at=session.get('completed_at') or session.get('failed_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    db_manager: DatabaseManager = Depends(get_db)
):
    """
    Create a new analysis session in database.
    
    Args:
        request: Session creation request
        
    Returns:
        Session response
    """
    try:
        import uuid
        session_id = str(uuid.uuid4())
        
        # Create session in database
        db_manager.create_session(
            session_id=session_id,
            session_type=request.session_type,
            user_id=request.user_id
        )
        
        # Get created session
        session = db_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        return SessionResponse(
            session_id=session['session_id'],
            session_type=session['session_type'],
            user_id=session.get('user_id'),
            status=session.get('current_status') or session.get('status', 'queued'),
            created_at=session['created_at'] if isinstance(session['created_at'], datetime) else datetime.fromisoformat(session['created_at']),
            ended_at=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db_manager: DatabaseManager = Depends(get_db)
):
    """
    Delete a session from database.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
    """
    try:
        # Delete session from database
        deleted = db_manager.delete_session(session_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": f"Session {session_id} deleted", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
