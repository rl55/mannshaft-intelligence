"""
HITL (Human-in-the-Loop) API routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

from api.models.requests import HITLResolutionRequest
from api.models.responses import HITLPendingResponse
from governance.hitl_manager import HITLManager, HITLStatus
from cache.cache_manager import CacheManager
from utils.logger import logger

router = APIRouter()


def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager()


def get_hitl_manager(cache_manager: CacheManager = Depends(get_cache_manager)) -> HITLManager:
    """Get HITL manager instance."""
    return HITLManager(cache_manager)


@router.get("/pending", response_model=List[HITLPendingResponse])
async def get_pending_hitl_requests(
    limit: int = 10,
    hitl_manager: HITLManager = Depends(get_hitl_manager)
):
    """
    Get pending HITL requests.
    
    Args:
        limit: Maximum number of requests to return
        
    Returns:
        List of pending HITL requests
    """
    try:
        requests = hitl_manager.get_pending_requests(limit=limit)
        
        pending_responses = []
        for req in requests:
            context = req.get('context', {})
            if isinstance(context, str):
                import json
                try:
                    context = json.loads(context)
                except json.JSONDecodeError:
                    context = {}
            
            pending_responses.append(
                HITLPendingResponse(
                    request_id=req.get('request_id', ''),
                    session_id=req.get('trace_id', ''),
                    escalation_reason=req.get('reason', ''),
                    risk_score=context.get('risk_score', 0.0) if isinstance(context, dict) else 0.0,
                    created_at=datetime.fromisoformat(req['timestamp']) if isinstance(req.get('timestamp'), str) else datetime.utcnow(),
                    review_url=context.get('review_url') if isinstance(context, dict) else None,
                    status=req.get('status', 'pending'),
                    human_decision=req.get('human_decision'),
                    human_feedback=req.get('human_feedback'),
                    resolved_at=datetime.fromisoformat(req['resolved_at']) if req.get('resolved_at') else None
                )
            )
        
        return pending_responses
        
    except Exception as e:
        logger.error(f"Error getting pending HITL requests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=List[HITLPendingResponse])
async def get_all_hitl_requests(
    limit: int = 50,
    include_resolved: bool = True,
    hitl_manager: HITLManager = Depends(get_hitl_manager)
):
    """
    Get all HITL requests (including resolved ones with decisions and feedback).
    
    Args:
        limit: Maximum number of requests to return
        include_resolved: Whether to include resolved requests
        
    Returns:
        List of all HITL requests with decisions and feedback
    """
    try:
        requests = hitl_manager.get_all_requests(limit=limit, include_resolved=include_resolved)
        
        all_responses = []
        for req in requests:
            context = req.get('context', {})
            if isinstance(context, str):
                import json
                try:
                    context = json.loads(context)
                except json.JSONDecodeError:
                    context = {}
            
            resolved_at = None
            if req.get('resolved_at'):
                try:
                    resolved_at = datetime.fromisoformat(req['resolved_at'])
                except (ValueError, TypeError):
                    pass
            
            all_responses.append(
                HITLPendingResponse(
                    request_id=req.get('request_id', ''),
                    session_id=req.get('trace_id', ''),
                    escalation_reason=req.get('reason', ''),
                    risk_score=context.get('risk_score', 0.0) if isinstance(context, dict) else 0.0,
                    created_at=datetime.fromisoformat(req['timestamp']) if isinstance(req.get('timestamp'), str) else datetime.utcnow(),
                    review_url=context.get('review_url') if isinstance(context, dict) else None,
                    status=req.get('status', 'pending'),
                    human_decision=req.get('human_decision'),
                    human_feedback=req.get('human_feedback'),
                    resolved_at=resolved_at
                )
            )
        
        return all_responses
        
    except Exception as e:
        logger.error(f"Error getting all HITL requests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{escalation_id}/details")
async def get_escalation_details(
    escalation_id: str,
    hitl_manager: HITLManager = Depends(get_hitl_manager)
):
    """
    Get full escalation details including context (agent_outputs, guardrail_violations, etc.).
    
    Args:
        escalation_id: Escalation/request ID
        
    Returns:
        Full escalation details with context
    """
    try:
        conn = hitl_manager.cache_manager.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM hitl_requests
            WHERE request_id = ?
        """, (escalation_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        req = dict(row)
        
        # Parse context JSON
        context = {}
        if req.get('context'):
            try:
                import json
                context = json.loads(req['context']) if isinstance(req['context'], str) else req['context']
            except (json.JSONDecodeError, TypeError):
                context = {}
        
        # Extract structured details from context
        escalation_details = {
            "request_id": req.get('request_id'),
            "session_id": req.get('trace_id'),
            "escalation_reason": req.get('reason'),
            "risk_score": context.get('risk_score', 0.0),
            "risk_rationale": context.get('risk_rationale', ''),
            "summary": context.get('summary', ''),
            "agent_outputs": context.get('agent_outputs', {}),
            "guardrail_violations": context.get('guardrail_violations', []),
            "recommended_actions": context.get('recommended_actions', []),
            "evaluation_details": context.get('evaluation_details'),
            "review_url": context.get('review_url'),
            "status": req.get('status', 'pending'),
            "human_decision": req.get('human_decision'),
            "human_feedback": req.get('human_feedback'),
            "created_at": req.get('timestamp'),
            "resolved_at": req.get('resolved_at'),
            "resolution_time_minutes": req.get('resolution_time_minutes')
        }
        
        return escalation_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting escalation details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{escalation_id}/resolve")
async def resolve_hitl_request(
    escalation_id: str,
    request: HITLResolutionRequest,
    hitl_manager: HITLManager = Depends(get_hitl_manager)
):
    """
    Resolve a HITL escalation.
    
    Args:
        escalation_id: Escalation/request ID
        request: Resolution request
        
    Returns:
        Success message
    """
    try:
        # Map decision to HITLStatus
        status_map = {
            'approved': HITLStatus.APPROVED,
            'rejected': HITLStatus.REJECTED,
            'modified': HITLStatus.MODIFIED
        }
        
        status = status_map.get(request.decision)
        if not status:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid decision: {request.decision}"
            )
        
        # Resolve request
        if request.decision == 'approved':
            success = hitl_manager.approve_request(
                request_id=escalation_id,
                human_feedback=request.feedback,
                human_reviewer=request.human_reviewer
            )
        elif request.decision == 'rejected':
            if not request.feedback or (isinstance(request.feedback, str) and not request.feedback.strip()):
                raise HTTPException(
                    status_code=400,
                    detail="Feedback is required for rejection"
                )
            success = hitl_manager.reject_request(
                request_id=escalation_id,
                human_feedback=request.feedback,
                human_reviewer=request.human_reviewer
            )
        else:  # modified
            if not request.modifications:
                raise HTTPException(
                    status_code=400,
                    detail="Modifications are required for modification decision"
                )
            success = hitl_manager.modify_request(
                request_id=escalation_id,
                modifications=request.modifications,
                human_feedback=request.feedback,
                human_reviewer=request.human_reviewer
            )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to resolve HITL request"
            )
        
        return {
            "message": f"HITL request {escalation_id} resolved",
            "decision": request.decision,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving HITL request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

