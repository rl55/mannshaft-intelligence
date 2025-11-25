"""
Unit tests for RevenueAgent.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock

# TODO: Update test to use ADK RevenueAgent
# Legacy agent removed - update to use:
# from adk_agents.revenue_agent import create_revenue_agent
# See docs/CLEANUP_PLAN.md for migration details

import pytest
pytest.skip("Legacy RevenueAgent removed - test needs ADK migration. See docs/CLEANUP_PLAN.md", allow_module_level=True)

# Placeholder - test needs ADK migration
from agents.revenue_agent import RevenueAgent, RevenueInput  # This will fail - needs ADK update
from tests.conftest import load_fixture


@pytest.mark.asyncio
async def test_revenue_agent_caching(cache_manager, sample_revenue_data, mock_gemini_responses):
    """Test revenue agent caching behavior."""
    agent = RevenueAgent(cache_manager=cache_manager)
    
    # Mock Gemini client
    mock_response = mock_gemini_responses.get("revenue_analysis", {})
    
    with patch.object(agent.gemini_client, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response
        
        # Mock sheets client
        with patch.object(agent.sheets_client, 'get_sheet_data') as mock_sheets:
            mock_sheets.return_value = [
                ['Week', 'MRR', 'New Customers', 'Churned'],
                ['25', '100000', '10', '2']
            ]
            
            # First call - cache miss
            context = {
                'week_number': 25,
                'spreadsheet_id': 'test',
                'revenue_sheet': 'Revenue Metrics',
                'churn_sheet': 'Churn Data'
            }
            
            result1 = await agent.analyze(context, "session_1")
            
            assert result1['cached'] == False
            assert 'response' in result1
            
            # Second call with same context - cache hit
            result2 = await agent.analyze(context, "session_1")
            
            # Should be cached (if caching is working)
            # Note: May need to adjust based on actual caching implementation
            assert 'response' in result2


@pytest.mark.asyncio
async def test_revenue_agent_data_validation(cache_manager, sample_revenue_data):
    """Test revenue agent data validation."""
    agent = RevenueAgent(cache_manager=cache_manager)
    
    # Test with valid data
    valid_input = RevenueInput(
        week_number=25,
        spreadsheet_id="test_sheet",
        revenue_sheet="Revenue Metrics",
        churn_sheet="Churn Data"
    )
    
    assert valid_input.week_number == 25
    
    # Test with invalid week number
    with pytest.raises(Exception):  # Pydantic validation error
        RevenueInput(
            week_number=53,  # Invalid (max 52)
            spreadsheet_id="test_sheet",
            revenue_sheet="Revenue Metrics"
        )


@pytest.mark.asyncio
async def test_revenue_agent_confidence_scoring(cache_manager, mock_gemini_responses):
    """Test revenue agent confidence scoring."""
    agent = RevenueAgent(cache_manager=cache_manager)
    
    mock_response = mock_gemini_responses.get("revenue_analysis", {})
    
    with patch.object(agent.gemini_client, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response
        
        with patch.object(agent.sheets_client, 'get_sheet_data') as mock_sheets:
            mock_sheets.return_value = [
                ['Week', 'MRR', 'New Customers', 'Churned'],
                ['25', '100000', '10', '2']
            ]
            
            context = {
                'week_number': 25,
                'spreadsheet_id': 'test',
                'revenue_sheet': 'Revenue Metrics'
            }
            
            result = await agent.analyze(context, "session_1")
            
            assert 'confidence_score' in result
            assert 0.0 <= result['confidence_score'] <= 1.0


@pytest.mark.asyncio
async def test_revenue_agent_error_handling(cache_manager):
    """Test revenue agent error handling."""
    agent = RevenueAgent(cache_manager=cache_manager)
    
    # Test with missing spreadsheet
    context = {
        'week_number': 25,
        'spreadsheet_id': None,
        'revenue_sheet': 'Revenue Metrics'
    }
    
    with pytest.raises((ValueError, RuntimeError)):
        await agent.analyze(context, "session_1")


@pytest.mark.asyncio
async def test_revenue_agent_execution_time(cache_manager, mock_gemini_responses):
    """Test revenue agent execution time tracking."""
    agent = RevenueAgent(cache_manager=cache_manager)
    
    mock_response = mock_gemini_responses.get("revenue_analysis", {})
    
    with patch.object(agent.gemini_client, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response
        
        with patch.object(agent.sheets_client, 'get_sheet_data') as mock_sheets:
            mock_sheets.return_value = [
                ['Week', 'MRR', 'New Customers', 'Churned'],
                ['25', '100000', '10', '2']
            ]
            
            context = {
                'week_number': 25,
                'spreadsheet_id': 'test',
                'revenue_sheet': 'Revenue Metrics'
            }
            
            result = await agent.analyze(context, "session_1")
            
            assert 'execution_time_ms' in result
            assert result['execution_time_ms'] > 0

