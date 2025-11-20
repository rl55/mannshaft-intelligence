"""
Analysis API routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from api.models.requests import AnalysisRequest, MultiAgentAnalysisRequest
from api.models.responses import AgentResponse, MultiAgentResponse
from agents.orchestrator import Orchestrator
from agents.revenue_agent import RevenueAgent
from agents.product_agent import ProductAgent
from agents.support_agent import SupportAgent
from agents.synthesizer_agent import SynthesizerAgent
from cache.cache_manager import CacheManager
from utils.logger import logger

router = APIRouter()


# Global orchestrator instance (would be injected via dependency in production)
_orchestrator: Orchestrator = None
_cache_manager: CacheManager = None


def get_orchestrator() -> Orchestrator:
    """Get orchestrator instance."""
    global _orchestrator, _cache_manager
    
    if _orchestrator is None:
        _cache_manager = CacheManager()
        _orchestrator = Orchestrator()
        
        # Register agents
        _orchestrator.register_agent(RevenueAgent(_cache_manager))
        _orchestrator.register_agent(ProductAgent(_cache_manager))
        _orchestrator.register_agent(SupportAgent(_cache_manager))
        _orchestrator.register_agent(SynthesizerAgent(_cache_manager))
    
    return _orchestrator


@router.post("/", response_model=AgentResponse)
async def analyze(request: AnalysisRequest):
    """
    Execute a single agent analysis.
    
    Args:
        request: Analysis request
        
    Returns:
        Agent response
    """
    try:
        orchestrator = get_orchestrator()
        
        if request.agent_type not in orchestrator.agents:
            raise HTTPException(
                status_code=404,
                detail=f"Agent type '{request.agent_type}' not found"
            )
        
        agent = orchestrator.agents[request.agent_type]
        
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            global _cache_manager
            if _cache_manager is None:
                _cache_manager = CacheManager()
            session_id = _cache_manager.create_session(
                session_type="ad_hoc"
            )
        
        result = await agent.execute(
            context=request.context,
            session_id=session_id,
            use_cache=request.use_cache
        )
        
        return AgentResponse(**result)
    except Exception as e:
        logger.error(f"Error in analysis endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi", response_model=MultiAgentResponse)
async def analyze_multi(request: MultiAgentAnalysisRequest):
    """
    Execute multiple agents in parallel or sequential mode.
    
    Args:
        request: Multi-agent analysis request
        
    Returns:
        Multi-agent response
    """
    try:
        orchestrator = get_orchestrator()
        
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            global _cache_manager
            if _cache_manager is None:
                _cache_manager = CacheManager()
            session_id = _cache_manager.create_session(
                session_type="multi_agent"
            )
        
        import time
        start_time = time.time()
        
        if request.execution_mode == "parallel":
            results = await orchestrator.execute_parallel(
                agent_types=request.agent_types,
                context=request.context,
                session_id=session_id
            )
        else:
            results = await orchestrator.execute_sequential(
                agent_types=request.agent_types,
                context=request.context,
                session_id=session_id
            )
        
        total_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert results to AgentResponse objects
        agent_responses = {
            agent_type: AgentResponse(**result)
            for agent_type, result in results.items()
        }
        
        return MultiAgentResponse(
            results=agent_responses,
            total_execution_time_ms=total_time_ms
        )
    except Exception as e:
        logger.error(f"Error in multi-agent analysis endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

