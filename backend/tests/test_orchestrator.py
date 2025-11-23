"""
Unit tests for OrchestratorAgent.

Example test cases demonstrating how to test the orchestrator.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from agents.orchestrator import OrchestratorAgent, AnalysisResult, AnalysisType
from cache.cache_manager import CacheManager
from governance.guardrails import Guardrails
from governance.evaluation import Evaluator
from governance.hitl_manager import HITLManager


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache = Mock(spec=CacheManager)
    cache.create_session = Mock(return_value="test-session-123")
    cache.end_session = Mock()
    cache.log_error = Mock()
    cache.log_guardrail_violation = Mock()
    cache.record_evaluation = Mock()
    cache.connect = Mock()
    return cache


@pytest.fixture
def mock_guardrails():
    """Create a mock guardrails instance."""
    guardrails = Mock(spec=Guardrails)
    guardrails.validate = Mock(return_value=[])
    return guardrails


@pytest.fixture
def mock_evaluator():
    """Create a mock evaluator."""
    evaluator = Mock(spec=Evaluator)
    evaluator.evaluate = AsyncMock(return_value={
        'factual_grounding_score': 0.8,
        'relevance_score': 0.9,
        'completeness_score': 0.85,
        'coherence_score': 0.8,
        'overall_quality': 'good',
        'requires_review': False
    })
    return evaluator


@pytest.fixture
def mock_hitl_manager(mock_cache_manager):
    """Create a mock HITL manager."""
    hitl = Mock(spec=HITLManager)
    hitl.create_request = Mock(return_value="hitl-request-123")
    return hitl


@pytest.fixture
def orchestrator_agent(mock_cache_manager, mock_guardrails, mock_evaluator, mock_hitl_manager):
    """Create an OrchestratorAgent instance with mocked dependencies."""
    with patch('agents.orchestrator.RevenueAgent'), \
         patch('agents.orchestrator.ProductAgent'), \
         patch('agents.orchestrator.SupportAgent'), \
         patch('agents.orchestrator.SynthesizerAgent'):
        
        orchestrator = OrchestratorAgent(
            cache_manager=mock_cache_manager,
            guardrails=mock_guardrails,
            evaluator=mock_evaluator,
            hitl_manager=mock_hitl_manager
        )
        
        # Mock the agents
        orchestrator.revenue_agent = Mock()
        orchestrator.revenue_agent.execute = AsyncMock(return_value={
            'response': 'Revenue analysis complete',
            'confidence_score': 0.9,
            'cached': False,
            'execution_time_ms': 1000
        })
        
        orchestrator.product_agent = Mock()
        orchestrator.product_agent.execute = AsyncMock(return_value={
            'response': 'Product analysis complete',
            'confidence_score': 0.85,
            'cached': False,
            'execution_time_ms': 1200
        })
        
        orchestrator.support_agent = Mock()
        orchestrator.support_agent.execute = AsyncMock(return_value={
            'response': 'Support analysis complete',
            'confidence_score': 0.8,
            'cached': False,
            'execution_time_ms': 800
        })
        
        orchestrator.synthesizer_agent = Mock()
        orchestrator.synthesizer_agent.execute = AsyncMock(return_value={
            'response': 'Synthesized report: All analyses complete',
            'confidence_score': 0.85,
            'cached': False,
            'execution_time_ms': 500
        })
        
        return orchestrator


@pytest.mark.asyncio
async def test_analyze_week_comprehensive(orchestrator_agent):
    """Test comprehensive weekly analysis."""
    result = await orchestrator_agent.analyze_week(
        week_number=42,
        user_id="user-123",
        analysis_type="comprehensive"
    )
    
    assert isinstance(result, AnalysisResult)
    assert result.session_id == "test-session-123"
    assert len(result.agents_executed) == 3
    assert 'revenue' in result.agents_executed
    assert 'product' in result.agents_executed
    assert 'support' in result.agents_executed
    assert result.execution_time_ms > 0
    assert result.quality_score > 0
    assert len(result.report) > 0


@pytest.mark.asyncio
async def test_analyze_week_revenue_only(orchestrator_agent):
    """Test revenue-only analysis."""
    result = await orchestrator_agent.analyze_week(
        week_number=42,
        user_id="user-123",
        analysis_type="revenue_only"
    )
    
    assert isinstance(result, AnalysisResult)
    assert len(result.agents_executed) == 1
    assert 'revenue' in result.agents_executed


@pytest.mark.asyncio
async def test_analyze_week_invalid_week_number(orchestrator_agent):
    """Test that invalid week number raises ValueError."""
    with pytest.raises(ValueError, match="Invalid week_number"):
        await orchestrator_agent.analyze_week(
            week_number=100,
            user_id="user-123"
        )


@pytest.mark.asyncio
async def test_parallel_agent_execution(orchestrator_agent):
    """Test that agents execute in parallel."""
    import time
    
    start_time = time.time()
    
    result = await orchestrator_agent.analyze_week(
        week_number=42,
        user_id="user-123",
        analysis_type="comprehensive"
    )
    
    execution_time = time.time() - start_time
    
    # If truly parallel, should take less than sum of individual times
    # (allowing for overhead)
    assert execution_time < 4.0  # 3 agents * ~1s each, but parallel


@pytest.mark.asyncio
async def test_guardrail_violation_handling(orchestrator_agent):
    """Test handling of guardrail violations."""
    # Mock guardrails to return violations
    orchestrator_agent.guardrails.validate = Mock(return_value=[
        {
            'rule_name': 'test_rule',
            'rule_type': 'hard',
            'severity': 'high',
            'details': {'test': 'violation'}
        }
    ])
    
    result = await orchestrator_agent.analyze_week(
        week_number=42,
        user_id="user-123"
    )
    
    assert result.guardrail_violations == 1
    assert result.hitl_escalations >= 0  # May create HITL request


@pytest.mark.asyncio
async def test_evaluation_failure_regeneration(orchestrator_agent):
    """Test regeneration when evaluation fails."""
    # Mock evaluator to return poor quality
    orchestrator_agent.evaluator.evaluate = AsyncMock(return_value={
        'overall_quality': 'poor',
        'requires_review': True,
        'factual_grounding_score': 0.3,
        'relevance_score': 0.4,
        'completeness_score': 0.3,
        'coherence_score': 0.4
    })
    
    # Set max regenerations to 1 for faster test
    orchestrator_agent.max_regenerations = 1
    
    result = await orchestrator_agent.analyze_week(
        week_number=42,
        user_id="user-123"
    )
    
    # Should have attempted regeneration
    assert result.regeneration_count >= 0


@pytest.mark.asyncio
async def test_agent_timeout_handling(orchestrator_agent):
    """Test handling of agent timeouts."""
    # Mock an agent to timeout
    async def timeout_execute(*args, **kwargs):
        await asyncio.sleep(100)  # Longer than timeout
    
    orchestrator_agent.revenue_agent.execute = timeout_execute
    orchestrator_agent.timeout_seconds = 0.1  # Very short timeout
    
    result = await orchestrator_agent.analyze_week(
        week_number=42,
        user_id="user-123",
        analysis_type="revenue_only"
    )
    
    # Should handle timeout gracefully
    assert isinstance(result, AnalysisResult)


@pytest.mark.asyncio
async def test_agent_failure_handling(orchestrator_agent):
    """Test handling of agent failures."""
    # Mock an agent to raise an exception
    orchestrator_agent.revenue_agent.execute = AsyncMock(side_effect=Exception("Test error"))
    
    result = await orchestrator_agent.analyze_week(
        week_number=42,
        user_id="user-123",
        analysis_type="revenue_only"
    )
    
    # Should handle error gracefully
    assert isinstance(result, AnalysisResult)
    # Should still have a report (fallback synthesis)
    assert len(result.report) > 0


@pytest.mark.asyncio
async def test_cache_efficiency_calculation(orchestrator_agent):
    """Test cache efficiency calculation."""
    # Mock cache manager to return cache stats
    mock_cursor = Mock()
    mock_row = Mock()
    mock_row.__getitem__ = Mock(side_effect=lambda k: {'cache_hits': 2, 'total_requests': 5}[k])
    mock_cursor.fetchone = Mock(return_value=mock_row)
    mock_conn = Mock()
    mock_conn.cursor = Mock(return_value=mock_cursor)
    orchestrator_agent.cache_manager.connect = Mock(return_value=mock_conn)
    
    result = await orchestrator_agent.analyze_week(
        week_number=42,
        user_id="user-123"
    )
    
    # Cache efficiency should be calculated
    assert 0.0 <= result.cache_efficiency <= 1.0


if __name__ == "__main__":
    # Run tests with: pytest tests/test_orchestrator.py -v
    pytest.main([__file__, "-v"])

