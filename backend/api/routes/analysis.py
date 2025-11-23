"""
Analysis API routes with background task support and WebSocket.
"""

import uuid
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from api.models.requests import AnalysisRequest
from api.models.responses import (
    AnalysisResponse,
    AnalysisResult,
    AnalysisStatusResponse
)
from agents.orchestrator import OrchestratorAgent, AnalysisType
from cache.cache_manager import CacheManager
from utils.logger import logger
from utils.config import config

router = APIRouter()

# In-memory storage for analysis status (in production, use Redis or database)
_analysis_status: Dict[str, Dict[str, Any]] = {}
_websocket_connections: Dict[str, list] = {}  # session_id -> [websockets]


def serialize_for_json(obj: Any) -> Any:
    """
    Recursively serialize objects for JSON, converting datetime to ISO format strings.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Try to convert to string for other types
        try:
            return str(obj)
        except Exception:
            return None


def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager()


def get_orchestrator(cache_manager: CacheManager = Depends(get_cache_manager)) -> OrchestratorAgent:
    """Get orchestrator instance."""
    return OrchestratorAgent(cache_manager=cache_manager)


async def run_analysis(
    session_id: str,
    week_number: int,
    analysis_type: str,
    user_id: str,
    agent_types: Optional[list],
    cache_manager: CacheManager
):
    """
    Run analysis in background task.
    
    Args:
        session_id: Session identifier
        week_number: Week number
        analysis_type: Type of analysis
        user_id: User identifier
        agent_types: Optional list of agent types
        cache_manager: Cache manager instance
    """
    try:
        # Update status to running
        _analysis_status[session_id] = {
            'status': 'running',
            'progress': 0,
            'current_step': 'Initializing',
            'started_at': datetime.utcnow()
        }
        
        # Emit WebSocket event
        await emit_websocket_event(session_id, {
            'type': 'agent_started',
            'session_id': session_id,
            'progress': 0,
            'message': 'Analysis started',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Get orchestrator
        orchestrator = OrchestratorAgent(cache_manager=cache_manager)
        
        # Map analysis type to string (orchestrator expects string, not enum)
        analysis_type_str = analysis_type  # Use the string directly
        
        # Update progress
        _analysis_status[session_id]['progress'] = 10
        _analysis_status[session_id]['current_step'] = 'Executing analytical agents'
        await emit_websocket_event(session_id, {
            'type': 'progress_update',
            'session_id': session_id,
            'progress': 10,
            'message': 'Executing analytical agents'
        })
        
        # Run analysis (orchestrator determines agent types internally based on analysis_type)
        # Note: Progress updates during analysis would require modifying orchestrator to emit events
        # For now, we emit updates at key milestones
        result = await orchestrator.analyze_week(
            week_number=week_number,
            analysis_type=analysis_type_str,
            user_id=user_id
        )
        
        # Update progress - analysis complete, processing results
        _analysis_status[session_id]['progress'] = 90
        _analysis_status[session_id]['current_step'] = 'Processing results'
        await emit_websocket_event(session_id, {
            'type': 'progress_update',
            'session_id': session_id,
            'progress': 90,
            'message': 'Processing results'
        })
        
        # Parse report if it's a string
        report_data = result.report
        if isinstance(report_data, str):
            try:
                import json
                report_data = json.loads(report_data)
            except (json.JSONDecodeError, TypeError):
                report_data = {'text': report_data}
        
        # Update status to completed
        _analysis_status[session_id] = {
            'status': 'completed',
            'progress': 100,
            'current_step': 'Completed',
            'result': {
                'session_id': result.session_id,
                'week_number': week_number,
                'report': report_data,
                'quality_score': result.quality_score,
                'execution_time_ms': result.execution_time_ms,
                'cache_efficiency': result.cache_efficiency,
                'agents_executed': result.agents_executed,
                'hitl_escalations': result.hitl_escalations,
                'guardrail_violations': result.guardrail_violations,
                'generated_at': datetime.utcnow().isoformat(),
                'metadata': result.metadata
            },
            'completed_at': datetime.utcnow()
        }
        
        # Emit completion event
        await emit_websocket_event(session_id, {
            'type': 'completed',
            'session_id': session_id,
            'progress': 100,
            'message': 'Analysis completed successfully',
            'result': _analysis_status[session_id]['result']
        })
        
    except Exception as e:
        logger.error(f"Error in background analysis: {e}", exc_info=True)
        
        # Update status to failed
        _analysis_status[session_id] = {
            'status': 'failed',
            'progress': 0,
            'error_message': str(e),
            'failed_at': datetime.utcnow()
        }
        
        # Emit error event
        await emit_websocket_event(session_id, {
            'type': 'error',
            'session_id': session_id,
            'progress': 0,
            'message': f'Analysis failed: {str(e)}',
            'error': str(e)
        })


async def emit_websocket_event(session_id: str, event: Dict[str, Any]):
    """Emit WebSocket event to all connected clients for a session."""
    if session_id in _websocket_connections:
        disconnected = []
        # Serialize event data to ensure datetime objects are converted
        serialized_event = serialize_for_json(event)
        for websocket in _websocket_connections[session_id]:
            try:
                await websocket.send_json(serialized_event)
            except Exception as e:
                logger.warning(f"Error sending WebSocket event: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            _websocket_connections[session_id].remove(ws)


@router.post("/trigger", response_model=AnalysisResponse)
async def trigger_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Trigger a new analysis.
    
    Creates a session and queues analysis in background.
    """
    try:
        # Create session
        session_id = cache_manager.create_session(
            session_type=f"weekly_analysis_{request.analysis_type}",
            user_id=request.user_id
        )
        
        # Initialize status
        _analysis_status[session_id] = {
            'status': 'queued',
            'progress': 0,
            'created_at': datetime.utcnow()
        }
        
        # Queue analysis in background
        background_tasks.add_task(
            run_analysis,
            session_id=session_id,
            week_number=request.week_number,
            analysis_type=request.analysis_type,
            user_id=request.user_id,
            agent_types=request.agent_types,
            cache_manager=cache_manager
        )
        
        return AnalysisResponse(
            session_id=session_id,
            status="queued",
            progress=0,
            estimated_time_remaining_seconds=None
        )
        
    except Exception as e:
        logger.error(f"Error triggering analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=AnalysisResult)
async def get_analysis_result(
    session_id: str,
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    Get analysis result by session ID.
    
    Returns the complete analysis result if available.
    """
    try:
        if session_id not in _analysis_status:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        status = _analysis_status[session_id]
        
        if status['status'] != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Analysis not completed. Status: {status['status']}"
            )
        
        result_data = status['result']
        
        return AnalysisResult(**result_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis result: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(session_id: str):
    """
    Get analysis status by session ID.
    
    Returns current status, progress, and estimated time remaining.
    """
    try:
        if session_id not in _analysis_status:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        status = _analysis_status[session_id]
        
        # Calculate estimated time remaining
        estimated_time = None
        if status['status'] == 'running' and 'started_at' in status:
            elapsed = (datetime.utcnow() - status['started_at']).total_seconds()
            progress = status.get('progress', 0)
            if progress > 0:
                total_estimated = elapsed / (progress / 100)
                estimated_time = int(total_estimated - elapsed)
        
        return AnalysisStatusResponse(
            session_id=session_id,
            status=status['status'],
            progress=status.get('progress', 0),
            current_step=status.get('current_step'),
            estimated_time_remaining_seconds=estimated_time,
            error_message=status.get('error_message'),
            result=AnalysisResult(**status['result']) if status.get('result') else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time analysis updates.
    
    Clients can subscribe to session-specific updates.
    """
    await websocket.accept()
    
    # Add to connections
    if session_id not in _websocket_connections:
        _websocket_connections[session_id] = []
    _websocket_connections[session_id].append(websocket)
    
    try:
        # Send initial status if available
        if session_id in _analysis_status:
            status_data = serialize_for_json(_analysis_status[session_id])
            await websocket.send_json({
                'event': 'status_update',
                'session_id': session_id,
                'status': status_data
            })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages (client can send ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping
                if data == "ping":
                    await websocket.send_json({"event": "pong"})
                    
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"event": "keepalive"})
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        # Remove from connections
        if session_id in _websocket_connections:
            if websocket in _websocket_connections[session_id]:
                _websocket_connections[session_id].remove(websocket)
