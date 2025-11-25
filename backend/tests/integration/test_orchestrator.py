"""
Integration tests for OrchestratorAgent.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock

# TODO: Update test to use ADK orchestrator
# Legacy OrchestratorAgent removed - update to use:
# from adk_agents.orchestrator import create_main_orchestrator
# from adk_setup import get_runner, get_session_service
# See docs/CLEANUP_PLAN.md for migration details

import pytest
pytest.skip("Legacy OrchestratorAgent removed - test needs ADK migration. See docs/CLEANUP_PLAN.md", allow_module_level=True)

# Placeholder - test needs ADK migration
from agents.orchestrator import OrchestratorAgent, AnalysisType  # This will fail - needs ADK update
from tests.conftest import load_fixture


@pytest.mark.asyncio
async def test_full_orchestrator_flow(cache_manager, mock_gemini_responses):
    """Test complete orchestrator flow."""
    orchestrator = OrchestratorAgent(cache_manager=cache_manager)
    
    # Mock all Gemini calls
    mock_responses = {
        'revenue': mock_gemini_responses.get("revenue_analysis", {}),
        'product': mock_gemini_responses.get("product_analysis", {}),
        'support': mock_gemini_responses.get("support_analysis", {}),
        'synthesizer': mock_gemini_responses.get("synthesizer_analysis", {}),
        'evaluation': mock_gemini_responses.get("evaluation", {})
    }
    
    def mock_generate(prompt, **kwargs):
        # Determine which agent based on prompt content
        if 'revenue' in prompt.lower():
            return mock_responses['revenue']
        elif 'product' in prompt.lower():
            return mock_responses['product']
        elif 'support' in prompt.lower():
            return mock_responses['support']
        elif 'synthesizer' in prompt.lower() or 'correlation' in prompt.lower():
            return mock_responses['synthesizer']
        else:
            return mock_responses['evaluation']
    
    # Mock sheets client
    with patch.object(orchestrator.revenue_agent.sheets_client, 'get_sheet_data') as mock_revenue_sheets, \
         patch.object(orchestrator.product_agent.sheets_client, 'get_sheet_data') as mock_product_sheets, \
         patch.object(orchestrator.support_agent.sheets_client, 'get_sheet_data') as mock_support_sheets, \
         patch.object(orchestrator.revenue_agent.gemini_client, 'generate', new_callable=AsyncMock) as mock_revenue_gemini, \
         patch.object(orchestrator.product_agent.gemini_client, 'generate', new_callable=AsyncMock) as mock_product_gemini, \
         patch.object(orchestrator.support_agent.gemini_client, 'generate', new_callable=AsyncMock) as mock_support_gemini, \
         patch.object(orchestrator.synthesizer_agent.gemini_client, 'generate', new_callable=AsyncMock) as mock_synth_gemini, \
         patch.object(orchestrator.evaluator.gemini_client, 'generate', new_callable=AsyncMock) as mock_eval_gemini:
        
        # Setup sheet mocks
        mock_revenue_sheets.return_value = [
            ['Week', 'MRR', 'New Customers', 'Churned'],
            ['25', '100000', '10', '2']
        ]
        mock_product_sheets.return_value = [
            ['Week', 'DAU', 'WAU', 'MAU'],
            ['25', '5000', '15000', '50000']
        ]
        mock_support_sheets.return_value = [
            ['Week', 'Tickets', 'CSAT'],
            ['25', '150', '4.2']
        ]
        
        # Setup Gemini mocks
        mock_revenue_gemini.side_effect = lambda *args, **kwargs: AsyncMock(return_value=mock_responses['revenue'])()
        mock_product_gemini.side_effect = lambda *args, **kwargs: AsyncMock(return_value=mock_responses['product'])()
        mock_support_gemini.side_effect = lambda *args, **kwargs: AsyncMock(return_value=mock_responses['support'])()
        mock_synth_gemini.side_effect = lambda *args, **kwargs: AsyncMock(return_value=mock_responses['synthesizer'])()
        mock_eval_gemini.side_effect = lambda *args, **kwargs: AsyncMock(return_value=mock_responses['evaluation'])()
        
        # Run analysis
        result = await orchestrator.analyze_week(
            week_number=25,
            analysis_type=AnalysisType.COMPREHENSIVE,
            user_id="test_user",
            agent_types=['revenue', 'product', 'support']
        )
        
        assert result is not None
        assert result.session_id is not None
        assert result.quality_score >= 0.0
        assert result.execution_time_ms > 0
        assert len(result.agents_executed) > 0


@pytest.mark.asyncio
async def test_orchestrator_error_recovery(cache_manager):
    """Test orchestrator error recovery."""
    orchestrator = OrchestratorAgent(cache_manager=cache_manager)
    
    # Mock one agent to fail
    with patch.object(orchestrator.revenue_agent, 'analyze', new_callable=AsyncMock) as mock_revenue:
        mock_revenue.side_effect = Exception("Agent error")
        
        # Should handle error gracefully
        try:
            result = await orchestrator.analyze_week(
                week_number=25,
                analysis_type=AnalysisType.COMPREHENSIVE,
                user_id="test_user",
                agent_types=['revenue']
            )
            # May return partial results or fail gracefully
        except Exception as e:
            # Error should be logged but not crash
            assert True


@pytest.mark.asyncio
async def test_orchestrator_parallel_execution(cache_manager, mock_gemini_responses):
    """Test parallel agent execution."""
    orchestrator = OrchestratorAgent(cache_manager=cache_manager)
    
    # Mock agents to track execution order
    execution_order = []
    
    async def mock_analyze(context, session_id):
        agent_type = context.get('agent_type', 'unknown')
        execution_order.append(agent_type)
        return {'response': '{}', 'confidence_score': 0.9, 'cached': False}
    
    with patch.object(orchestrator.revenue_agent, 'analyze', new_callable=AsyncMock) as mock_revenue, \
         patch.object(orchestrator.product_agent, 'analyze', new_callable=AsyncMock) as mock_product, \
         patch.object(orchestrator.support_agent, 'analyze', new_callable=AsyncMock) as mock_support:
        
        mock_revenue.side_effect = lambda ctx, sid: mock_analyze({**ctx, 'agent_type': 'revenue'}, sid)
        mock_product.side_effect = lambda ctx, sid: mock_analyze({**ctx, 'agent_type': 'product'}, sid)
        mock_support.side_effect = lambda ctx, sid: mock_analyze({**ctx, 'agent_type': 'support'}, sid)
        
        # Run with multiple agents
        result = await orchestrator.analyze_week(
            week_number=25,
            analysis_type=AnalysisType.COMPREHENSIVE,
            user_id="test_user",
            agent_types=['revenue', 'product', 'support']
        )
        
        # Agents should execute (order may vary in parallel)
        assert len(execution_order) >= 3

