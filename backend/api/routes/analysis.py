"""
Analysis API routes with background task support and WebSocket.
"""

import uuid
import asyncio
import json
from typing import Dict, Any, Optional, List
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
from database.db_manager import get_db_manager, DatabaseManager
from utils.logger import logger
from utils.config import config

router = APIRouter()

# In-memory storage for WebSocket connections (session_id -> [websockets])
_websocket_connections: Dict[str, list] = {}

# Event buffer for sessions without active WebSocket connections
# Format: {session_id: [event1, event2, ...]}
_websocket_event_buffer: Dict[str, List[Dict[str, Any]]] = {}


def get_db() -> DatabaseManager:
    """Get database manager instance."""
    return get_db_manager()


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
    cache_manager: CacheManager,
    db_manager: DatabaseManager
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
        db_manager: Database manager instance
    """
    try:
        # Update status to running in database
        db_manager.update_session_status(
            session_id=session_id,
            status='running',
            progress=0,
            current_step='Initializing'
        )
        
        # Emit WebSocket event
        await emit_websocket_event(session_id, {
            'type': 'agent_started',
            'session_id': session_id,
            'progress': 0,
            'message': 'Analysis started',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Create event emitter function for orchestrator
        async def emit_event(event_dict: Dict[str, Any]):
            await emit_websocket_event(session_id, event_dict)
        
        # Get orchestrator with event emitter
        orchestrator = OrchestratorAgent(cache_manager=cache_manager, event_emitter=emit_event)
        
        # Map analysis type to string (orchestrator expects string, not enum)
        analysis_type_str = analysis_type  # Use the string directly
        
        # Update progress in database
        db_manager.update_session_status(
            session_id=session_id,
            status='running',
            progress=10,
            current_step='Executing analytical agents'
        )
        await emit_websocket_event(session_id, {
            'type': 'progress_update',
            'session_id': session_id,
            'progress': 10,
            'message': 'Executing analytical agents'
        })
        
        # Run analysis - orchestrator will emit real-time events as agents execute
        # No need to emit agent_started/completed here - orchestrator handles it
        result = await orchestrator.analyze_week(
            week_number=week_number,
            analysis_type=analysis_type_str,
            user_id=user_id,
            session_id=session_id  # Pass session_id so orchestrator uses the same session
        )
        
        # Update progress - analysis complete, processing results
        db_manager.update_session_status(
            session_id=session_id,
            status='running',
            progress=95,
            current_step='Finalizing results'
        )
        await emit_websocket_event(session_id, {
            'type': 'progress_update',
            'session_id': session_id,
            'progress': 95,
            'message': 'Finalizing results'
        })
        
        # Parse report if it's a string
        report_data = result.report
        if isinstance(report_data, str):
            try:
                import json
                report_data = json.loads(report_data)
            except (json.JSONDecodeError, TypeError):
                report_data = {'text': report_data}
        
        # Note: All agent events (started/completed) are now emitted in REAL-TIME
        # by the orchestrator during execution via the event_emitter callback.
        # No need to emit them again here - they've already been sent as agents executed.
        
        # Save analysis result to database
        db_manager.save_analysis_result(
            session_id=result.session_id,
            report=report_data,
            quality_score=result.quality_score,
            execution_time_ms=result.execution_time_ms,
            cache_efficiency=result.cache_efficiency,
            agents_executed=result.agents_executed,
            hitl_escalations=result.hitl_escalations,
            guardrail_violations=result.guardrail_violations,
            evaluation_passed=result.evaluation_passed,
            regeneration_count=result.regeneration_count,
            metadata=result.metadata
        )
        
        # Update status to completed
        db_manager.update_session_status(
            session_id=session_id,
            status='completed',
            progress=100,
            current_step='Completed'
        )
        
        # Get the saved result for WebSocket event
        saved_result = db_manager.get_analysis_result(session_id)
        result_data = {
            'session_id': result.session_id,
            'week_number': week_number,
            'report': saved_result['report'] if saved_result else report_data,
            'quality_score': result.quality_score,
            'execution_time_ms': result.execution_time_ms,
            'cache_efficiency': result.cache_efficiency,
            'agents_executed': result.agents_executed,
            'hitl_escalations': result.hitl_escalations,
            'guardrail_violations': result.guardrail_violations,
            'generated_at': datetime.utcnow().isoformat(),
            'metadata': result.metadata
        }
        
        # Emit completion event
        await emit_websocket_event(session_id, {
            'type': 'completed',
            'session_id': session_id,
            'progress': 100,
            'message': 'Analysis completed successfully',
            'result': result_data
        })
        
    except Exception as e:
        logger.error(f"Error in background analysis: {e}", exc_info=True)
        
        # Update status to failed in database
        db_manager.update_session_status(
            session_id=session_id,
            status='failed',
            progress=0,
            error_message=str(e)
        )
        
        # Emit error event
        await emit_websocket_event(session_id, {
            'type': 'error',
            'session_id': session_id,
            'progress': 0,
            'message': f'Analysis failed: {str(e)}',
            'error': str(e)
        })


async def emit_websocket_event(session_id: str, event: Dict[str, Any]):
    """Emit WebSocket event to all connected clients for a session.
    
    If no WebSocket connections exist, buffer the event for later delivery.
    """
    # Serialize event data to ensure datetime objects are converted
    serialized_event = serialize_for_json(event)
    
    if session_id in _websocket_connections and len(_websocket_connections[session_id]) > 0:
        disconnected = []
        logger.info(f"📤 Sending WebSocket event for session {session_id}: type={event.get('type')}, agent={event.get('agent')}, progress={event.get('progress')}")
        for websocket in _websocket_connections[session_id]:
            try:
                await websocket.send_json(serialized_event)
                logger.debug(f"✅ WebSocket event sent successfully: {event.get('type')}")
            except Exception as e:
                logger.warning(f"❌ Error sending WebSocket event: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            _websocket_connections[session_id].remove(ws)
    else:
        # Buffer event for later delivery when WebSocket connects
        # Limit buffer size to prevent memory issues (keep last 100 events)
        if session_id not in _websocket_event_buffer:
            _websocket_event_buffer[session_id] = []
        
        _websocket_event_buffer[session_id].append(serialized_event)
        
        # Limit buffer to last 100 events
        if len(_websocket_event_buffer[session_id]) > 100:
            _websocket_event_buffer[session_id] = _websocket_event_buffer[session_id][-100:]
            logger.warning(f"Event buffer for session {session_id} exceeded 100 events, keeping last 100")
        
        logger.warning(f"⚠️ NO WebSocket connection for session {session_id}! Event BUFFERED: type={event.get('type')}, agent={event.get('agent')}, progress={event.get('progress')}. Buffer size: {len(_websocket_event_buffer[session_id])}")


@router.post("/trigger", response_model=AnalysisResponse)
async def trigger_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    cache_manager: CacheManager = Depends(get_cache_manager),
    db_manager: DatabaseManager = Depends(get_db)
):
    """
    Trigger a new analysis.
    
    Creates a session and queues analysis in background.
    """
    try:
        # Create session in cache manager (for agent caching)
        session_id = cache_manager.create_session(
            session_type=f"weekly_analysis_{request.analysis_type}",
            user_id=request.user_id
        )
        
        # Create session in database
        db_manager.create_session(
            session_id=session_id,
            session_type=f"weekly_analysis_{request.analysis_type}",
            user_id=request.user_id,
            week_number=request.week_number,
            analysis_type=request.analysis_type
        )
        
        # Queue analysis in background with a small delay to allow WebSocket to connect
        # This ensures real-time updates are sent over WebSocket, not just buffered
        async def delayed_run_analysis():
            # Wait 200ms for WebSocket to connect before starting analysis
            await asyncio.sleep(0.2)
            await run_analysis(
                session_id=session_id,
                week_number=request.week_number,
                analysis_type=request.analysis_type,
                user_id=request.user_id,
                agent_types=request.agent_types,
                cache_manager=cache_manager,
                db_manager=db_manager
            )
        
        background_tasks.add_task(delayed_run_analysis)
        
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
    db_manager: DatabaseManager = Depends(get_db)
):
    """
    Get analysis result by session ID.
    
    Returns the complete analysis result if available.
    """
    try:
        session = db_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if session.get('current_status') != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Analysis not completed. Status: {session.get('current_status')}"
            )
        
        result_data = db_manager.get_analysis_result(session_id)
        if not result_data:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        
        # Convert to AnalysisResult format
        return AnalysisResult(
            session_id=session_id,
            week_number=session.get('week_number', 0),
            report=result_data['report'],
            quality_score=result_data['quality_score'],
            execution_time_ms=result_data['execution_time_ms'],
            cache_efficiency=result_data['cache_efficiency'],
            agents_executed=result_data['agents_executed'],
            hitl_escalations=result_data['hitl_escalations'],
            guardrail_violations=result_data['guardrail_violations'],
            generated_at=datetime.fromisoformat(result_data['generated_at']) if isinstance(result_data['generated_at'], str) else result_data['generated_at'],
            metadata=result_data.get('metadata')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis result: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    session_id: str,
    db_manager: DatabaseManager = Depends(get_db)
):
    """
    Get analysis status by session ID.
    
    Returns current status, progress, and estimated time remaining.
    """
    try:
        status_data = db_manager.get_session_status(session_id)
        if not status_data:
            logger.debug(f"Session status not found for {session_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"Analysis session '{session_id}' not found. Status may have been cleared or session expired."
            )
        
        # Build response
        response_data = {
            'session_id': session_id,
            'status': status_data['status'],
            'progress': status_data.get('progress', 0),
            'current_step': status_data.get('current_step'),
            'estimated_time_remaining_seconds': status_data.get('estimated_time_remaining_seconds')
        }
        
        # Include result if completed
        if status_data['status'] == 'completed' and status_data.get('result'):
            result = status_data['result']
            session = db_manager.get_session(session_id)
            response_data['result'] = AnalysisResult(
                session_id=session_id,
                week_number=session.get('week_number', 0) if session else 0,
                report=result['report'],
                quality_score=result['quality_score'],
                execution_time_ms=result['execution_time_ms'],
                cache_efficiency=result['cache_efficiency'],
                agents_executed=result['agents_executed'],
                hitl_escalations=result['hitl_escalations'],
                guardrail_violations=result['guardrail_violations'],
                generated_at=datetime.fromisoformat(result['generated_at']) if isinstance(result['generated_at'], str) else result['generated_at'],
                metadata=result.get('metadata')
            )
        elif status_data['status'] == 'failed':
            session = db_manager.get_session(session_id)
            if session and session.get('error_message'):
                response_data['error_message'] = session['error_message']
        
        return AnalysisStatusResponse(**response_data)
        
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
    logger.info(f"✅ WebSocket connection ACCEPTED for session {session_id}")
    
    # Add to connections IMMEDIATELY so events are sent in real-time
    if session_id not in _websocket_connections:
        _websocket_connections[session_id] = []
    _websocket_connections[session_id].append(websocket)
    logger.info(f"✅ WebSocket REGISTERED. Total connections for {session_id}: {len(_websocket_connections[session_id])}")
    
    # Check if there are buffered events and send them
    if session_id in _websocket_event_buffer and len(_websocket_event_buffer[session_id]) > 0:
        logger.warning(f"⚠️ Found {len(_websocket_event_buffer[session_id])} buffered events - WebSocket connected AFTER analysis started!")
    
    # Send any buffered events immediately
    if session_id in _websocket_event_buffer and len(_websocket_event_buffer[session_id]) > 0:
        buffered_events = _websocket_event_buffer[session_id]
        logger.info(f"Sending {len(buffered_events)} buffered events to WebSocket for session {session_id}")
        for idx, buffered_event in enumerate(buffered_events):
            try:
                logger.debug(f"Sending buffered event {idx+1}/{len(buffered_events)}: type={buffered_event.get('type')}, agent={buffered_event.get('agent')}, progress={buffered_event.get('progress')}")
                await websocket.send_json(buffered_event)
                # Small delay between events to ensure they're processed separately
                await asyncio.sleep(0.01)  # 10ms delay
            except Exception as e:
                logger.warning(f"Error sending buffered event {idx+1}: {e}")
        # Clear buffer after sending
        del _websocket_event_buffer[session_id]
    
    try:
        # Get database manager
        db_manager = get_db_manager()
        
        # Send initial status if available
        status_data = db_manager.get_session_status(session_id)
        if status_data:
            status = status_data
            # Send initial status in the format expected by frontend
            status_type = status.get('status', 'unknown')
            progress = status.get('progress', 0)
            
            # Map status to appropriate event type
            if status_type == 'completed':
                event_type = 'completed'
            elif status_type == 'failed':
                event_type = 'error'
            else:
                event_type = 'progress_update'
            
            initial_event = {
                'type': event_type,
                'session_id': session_id,
                'progress': progress,
                'message': status.get('current_step') or f"Status: {status_type}",
                'timestamp': datetime.utcnow().isoformat()
            }
            logger.info(f"Sending initial status to WebSocket for session {session_id}: {event_type} (progress: {progress})")
            await websocket.send_json(initial_event)
            
            # If analysis is completed, also send agent_completed events for all executed agents
            if status_type == 'completed' and status.get('result'):
                result = status['result']
                agents_executed = result.get('agents_executed', [])
                metadata = result.get('metadata', {})
                analytical_results = metadata.get('analytical_results', {}) if metadata else {}
                guardrail_violations = result.get('guardrail_violations', 0)
                
                logger.info(f"Sending agent_completed events for {len(agents_executed)} agents: {agents_executed}")
                for agent_type in agents_executed:
                    # Get confidence score from analytical_results (0-1 range)
                    agent_result = analytical_results.get(agent_type, {})
                    confidence_score = agent_result.get('confidence_score', 0.85)
                    
                    # Extract key insights from agent response
                    key_insights = []
                    try:
                        agent_response = agent_result.get('response', '{}')
                        if isinstance(agent_response, str):
                            response_data = json.loads(agent_response)
                        else:
                            response_data = agent_response
                        
                        # Extract insights from analysis (structure varies by agent)
                        analysis = response_data.get('analysis', {})
                        if isinstance(analysis, dict):
                            key_insights = analysis.get('key_insights', [])
                            if not key_insights:
                                # Try direct access if analysis is nested differently
                                key_insights = response_data.get('key_insights', [])
                    except (json.JSONDecodeError, TypeError, AttributeError) as e:
                        logger.debug(f"Could not extract insights for {agent_type}: {e}")
                        key_insights = []
                    
                    # Send agent_started event first
                    await websocket.send_json({
                        'type': 'agent_started',
                        'session_id': session_id,
                        'agent': agent_type,
                        'progress': 10,
                        'message': f'Analyzing {agent_type} data...',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    # Send key insights as progress updates
                    for insight in key_insights[:3]:  # Send top 3 insights
                        insight_text = insight if isinstance(insight, str) else insight.get('description', str(insight))
                        await websocket.send_json({
                            'type': 'progress_update',
                            'session_id': session_id,
                            'agent': agent_type,
                            'progress': 50,
                            'message': insight_text,
                            'timestamp': datetime.utcnow().isoformat()
                        })
                    
                    # Send completion event
                    await websocket.send_json({
                        'type': 'agent_completed',
                        'session_id': session_id,
                        'agent': agent_type,
                        'progress': 100,
                        'message': f'{agent_type.capitalize()} agent completed',
                        'data': {
                            'confidence': confidence_score  # Send as decimal (0-1)
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    logger.debug(f"Sent agent events for {agent_type} with confidence {confidence_score:.2f} ({int(confidence_score * 100)}%) and {len(key_insights)} insights")
                
                # Send events for synthesizer agent (always runs after analytical agents)
                synthesizer_result = metadata.get('synthesizer_result', {})
                synthesizer_confidence = synthesizer_result.get('confidence_score', 0.9) if synthesizer_result else 0.9
                await websocket.send_json({
                    'type': 'agent_started',
                    'session_id': session_id,
                    'agent': 'synthesizer',
                    'progress': 60,
                    'message': 'Synthesizing cross-functional insights...',
                    'timestamp': datetime.utcnow().isoformat()
                })
                await websocket.send_json({
                    'type': 'agent_completed',
                    'session_id': session_id,
                    'agent': 'synthesizer',
                    'progress': 70,
                    'message': 'Synthesizer agent completed',
                    'data': {
                        'confidence': synthesizer_confidence
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
                logger.debug(f"Sent synthesizer agent events with confidence {synthesizer_confidence:.2f} ({int(synthesizer_confidence * 100)}%)")
                
                # Send events for governance agent (always runs after synthesizer)
                governance_confidence = 1.0 if guardrail_violations == 0 else max(0.5, 1.0 - (guardrail_violations * 0.1))
                await websocket.send_json({
                    'type': 'agent_started',
                    'session_id': session_id,
                    'agent': 'governance',
                    'progress': 75,
                    'message': 'Applying safety guardrails...',
                    'timestamp': datetime.utcnow().isoformat()
                })
                await websocket.send_json({
                    'type': 'progress_update',
                    'session_id': session_id,
                    'agent': 'governance',
                    'progress': 80,
                    'message': 'PII Check: Passed' if guardrail_violations == 0 else f'Found {guardrail_violations} guardrail violation(s)',
                    'timestamp': datetime.utcnow().isoformat()
                })
                await websocket.send_json({
                    'type': 'agent_completed',
                    'session_id': session_id,
                    'agent': 'governance',
                    'progress': 85,
                    'message': 'Final report approved for distribution' if guardrail_violations == 0 else 'Report requires review',
                    'data': {
                        'confidence': governance_confidence  # Send as decimal (0-1)
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
                logger.debug(f"Sent governance agent events with confidence {governance_confidence:.2f} ({int(governance_confidence * 100)}%)")
                
                # Send events for evaluation agent (always runs after governance)
                evaluation_result = metadata.get('evaluation', {})
                evaluation_details = evaluation_result.get('evaluation_details', {}) if isinstance(evaluation_result, dict) else {}
                evaluation_confidence = evaluation_details.get('overall_score', result.get('quality_score', 0.9)) if evaluation_details else result.get('quality_score', 0.9)
                await websocket.send_json({
                    'type': 'agent_started',
                    'session_id': session_id,
                    'agent': 'evaluation',
                    'progress': 90,
                    'message': 'Evaluating report quality...',
                    'timestamp': datetime.utcnow().isoformat()
                })
                await websocket.send_json({
                    'type': 'agent_completed',
                    'session_id': session_id,
                    'agent': 'evaluation',
                    'progress': 95,
                    'message': 'Evaluation agent completed',
                    'data': {
                        'confidence': evaluation_confidence
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
                logger.debug(f"Sent evaluation agent events with confidence {evaluation_confidence:.2f} ({int(evaluation_confidence * 100)}%)")
        else:
            logger.debug(f"No status found for session {session_id} when WebSocket connected")
        
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
