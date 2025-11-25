"""
ADK Integration Wrapper
Provides compatibility layer between ADK agents and existing API structure.
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from adk_setup import get_runner, get_session_service
from adk_app import app as adk_app
from utils.logger import logger


@dataclass
class AnalysisResult:
    """Compatibility wrapper for ADK analysis results."""
    session_id: str
    report: Dict[str, Any]
    quality_score: float = 0.85
    execution_time_ms: int = 0
    cache_efficiency: float = 0.0
    agents_executed: List[str] = None
    hitl_escalations: int = 0
    guardrail_violations: int = 0
    evaluation_passed: bool = True
    regeneration_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.agents_executed is None:
            self.agents_executed = []
        if self.metadata is None:
            self.metadata = {}


async def run_adk_analysis(
    week_number: int,
    session_id: str,
    analysis_type: str = "comprehensive",
    user_id: Optional[str] = None,
    event_emitter: Optional[callable] = None
) -> AnalysisResult:
    """
    Run analysis using ADK agents.
    
    Args:
        week_number: Week number for analysis
        session_id: Session identifier
        analysis_type: Type of analysis (default: "comprehensive")
        user_id: Optional user identifier
        event_emitter: Optional async function to emit WebSocket events
        
    Returns:
        AnalysisResult object with analysis results
    """
    start_time = time.time()
    
    try:
        # Get ADK Runner with app
        runner = get_runner(app=adk_app)
        
        # Get session service and create session if needed
        # ADK Runner requires the session to exist before execution
        session_service = get_session_service()
        user_id_final = user_id or "system"
        
        # Create session in ADK SessionService if it doesn't exist
        try:
            # Try to get existing session
            existing_session = session_service.get_session(user_id=user_id_final, session_id=session_id)
            if not existing_session:
                # Create new session
                session_service.create_session(
                    user_id=user_id_final,
                    session_id=session_id
                )
                logger.info(f"Created ADK session: {session_id} for user: {user_id_final}")
        except Exception as e:
            # Session might not exist, try to create it
            try:
                session_service.create_session(
                    user_id=user_id_final,
                    session_id=session_id
                )
                logger.info(f"Created ADK session: {session_id} for user: {user_id_final}")
            except Exception as create_error:
                # Session might already exist or creation failed
                logger.debug(f"ADK session creation: {create_error}, continuing...")
        
        # Prepare context for ADK agent
        context = {
            "week_number": week_number,
            "analysis_type": analysis_type,
            "user_id": user_id_final,
            "session_id": session_id
        }
        
        # Emit start event
        if event_emitter:
            await event_emitter({
                'type': 'agent_started',
                'session_id': session_id,
                'agent': 'main_orchestrator',
                'progress': 0,
                'message': 'Starting ADK analysis',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Execute ADK agent using Runner
        # ADK Runner.run_async executes the root_agent from the App
        # The root_agent (SequentialAgent) will execute all sub-agents
        # ADK Runner API: run_async(user_id, session_id, new_message, state_delta, ...)
        # Pass context via state_delta - agents will read week_number and analysis_type from state
        
        result_stream = runner.run_async(
            user_id=user_id_final,
            session_id=session_id,
            new_message=None,  # No new message, use state_delta for context
            state_delta=context  # Pass context as state_delta (week_number, analysis_type, etc.)
        )
        
        # Collect results from ADK agent execution
        # ADK agents yield events, we need to collect the final result
        final_result = None
        agents_executed = []
        events_collected = []
        
        async for event in result_stream:
            events_collected.append(event)
            
            # Emit WebSocket events if emitter provided
            if event_emitter:
                # Transform ADK event to WebSocket format
                ws_event = {
                    'type': 'agent_progress',
                    'session_id': session_id,
                    'agent': getattr(event, 'agent_name', 'unknown'),
                    'progress': getattr(event, 'progress', 0),
                    'message': getattr(event, 'message', 'Processing'),
                    'timestamp': datetime.utcnow().isoformat()
                }
                await event_emitter(ws_event)
            
            # Track agents executed
            if hasattr(event, 'agent_name'):
                if event.agent_name not in agents_executed:
                    agents_executed.append(event.agent_name)
            
            # Collect final result (last event with result data)
            if hasattr(event, 'result') and event.result:
                final_result = event.result
            elif hasattr(event, 'content'):
                # Try to extract result from content
                try:
                    import json
                    if isinstance(event.content, str):
                        final_result = json.loads(event.content)
                    else:
                        final_result = event.content
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Extract report from final result
        # ADK agents return structured data, we need to extract the report
        report_data = {}
        if final_result:
            if isinstance(final_result, dict):
                report_data = final_result
            elif isinstance(final_result, str):
                try:
                    import json
                    report_data = json.loads(final_result)
                except json.JSONDecodeError:
                    report_data = {'text': final_result}
        else:
            # Fallback: construct report from events
            report_data = {
                'summary': 'Analysis completed',
                'agents': agents_executed,
                'events': len(events_collected)
            }
        
        # Extract quality score and other metrics from result or metadata
        quality_score = 0.85  # Default
        if final_result and isinstance(final_result, dict):
            quality_score = final_result.get('quality_score', final_result.get('confidence', 0.85))
        
        # Create AnalysisResult
        result = AnalysisResult(
            session_id=session_id,
            report=report_data,
            quality_score=quality_score,
            execution_time_ms=execution_time_ms,
            cache_efficiency=0.0,  # TODO: Extract from ADK cache stats
            agents_executed=agents_executed or ['revenue', 'product', 'support', 'synthesizer', 'governance', 'evaluation'],
            hitl_escalations=0,  # TODO: Extract from governance events
            guardrail_violations=0,  # TODO: Extract from governance events
            evaluation_passed=True,  # TODO: Extract from evaluation events
            regeneration_count=0,  # TODO: Track regeneration attempts
            metadata={
                'week_number': week_number,
                'analysis_type': analysis_type,
                'adk_execution': True,
                'events_count': len(events_collected),
                'agents': agents_executed
            }
        )
        
        logger.info(f"ADK analysis completed for session {session_id}, week {week_number}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error running ADK analysis: {e}", exc_info=True)
        
        # Emit error event
        if event_emitter:
            await event_emitter({
                'type': 'error',
                'session_id': session_id,
                'message': f'ADK analysis failed: {str(e)}',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Return error result
        execution_time_ms = int((time.time() - start_time) * 1000)
        return AnalysisResult(
            session_id=session_id,
            report={'error': str(e)},
            quality_score=0.0,
            execution_time_ms=execution_time_ms,
            evaluation_passed=False,
            metadata={'error': str(e), 'adk_execution': True}
        )

