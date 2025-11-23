"""
Unit tests for Evaluator.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock

from governance.evaluation import Evaluator


@pytest.mark.asyncio
async def test_evaluation_criteria(cache_manager, mock_gemini_responses):
    """Test evaluation criteria scoring."""
    evaluator = Evaluator(cache_manager)
    
    mock_eval_response = mock_gemini_responses.get("evaluation", {})
    
    with patch.object(evaluator.gemini_client, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_eval_response
        
        test_report = {
            'executive_summary': 'Test summary',
            'correlations': [],
            'strategic_recommendations': []
        }
        
        result = await evaluator.evaluate(
            agent_type='synthesizer',
            response={'response': json.dumps(test_report)},
            trace_id='test_trace'
        )
        
        assert 'overall_quality' in result
        assert 'factual_grounding_score' in result
        assert 'relevance_score' in result
        assert 'completeness_score' in result
        assert 'coherence_score' in result


@pytest.mark.asyncio
async def test_evaluation_caching(cache_manager, mock_gemini_responses):
    """Test evaluation result caching."""
    evaluator = Evaluator(cache_manager)
    
    mock_eval_response = mock_gemini_responses.get("evaluation", {})
    
    test_report = {
        'executive_summary': 'Test summary',
        'correlations': [],
        'strategic_recommendations': []
    }
    
    with patch.object(evaluator.gemini_client, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_eval_response
        
        # First evaluation
        result1 = await evaluator.evaluate(
            agent_type='synthesizer',
            response={'response': json.dumps(test_report)},
            trace_id='test_trace'
        )
        
        # Second evaluation (should use cache)
        result2 = await evaluator.evaluate(
            agent_type='synthesizer',
            response={'response': json.dumps(test_report)},
            trace_id='test_trace'
        )
        
        # Results should be similar (cached or same)
        assert result1['overall_quality'] == result2['overall_quality']


@pytest.mark.asyncio
async def test_evaluation_regeneration_logic(cache_manager, mock_gemini_responses):
    """Test evaluation regeneration logic."""
    evaluator = Evaluator(cache_manager)
    
    # Mock low score evaluation
    low_score_response = {
        'text': '{"overall_score": 0.5, "regeneration_needed": true}',
        'tokens_input': 100,
        'tokens_output': 50
    }
    
    with patch.object(evaluator.gemini_client, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = low_score_response
        
        test_report = {
            'executive_summary': 'Test',
            'correlations': [],
            'strategic_recommendations': []
        }
        
        result = await evaluator.evaluate(
            agent_type='synthesizer',
            response={'response': json.dumps(test_report)},
            trace_id='test_trace'
        )
        
        # Should indicate regeneration needed
        assert result.get('requires_review', False) == True


@pytest.mark.asyncio
async def test_evaluation_heuristic_fallback(cache_manager):
    """Test heuristic evaluation fallback."""
    evaluator = Evaluator(cache_manager)
    
    # Mock Gemini failure
    with patch.object(evaluator.gemini_client, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.side_effect = Exception("Gemini API error")
        
        test_report = {
            'executive_summary': 'Test summary',
            'correlations': [{'pattern': 'Test'}],
            'strategic_recommendations': [{'action': 'Test'}],
            'data_citations': ['Sheet1!A1']
        }
        
        result = await evaluator.evaluate(
            agent_type='synthesizer',
            response={'response': json.dumps(test_report)},
            trace_id='test_trace'
        )
        
        # Should fallback to heuristic
        assert 'overall_quality' in result
        assert result['overall_quality'] in ['excellent', 'good', 'acceptable', 'poor']

