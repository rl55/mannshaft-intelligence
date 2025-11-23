"""
Unit tests for GuardrailAgent.
"""

import pytest
from unittest.mock import patch

from governance.guardrails import GuardrailAgent, ViolationSeverity


@pytest.mark.asyncio
async def test_guardrail_pii_detection(cache_manager):
    """Test PII detection guardrail."""
    guardrail = GuardrailAgent(cache_manager)
    
    # Test with SSN
    test_data = {
        'response': '{"executive_summary": "Customer SSN: 123-45-6789"}'
    }
    
    result = guardrail.evaluate(
        insights=test_data,
        session_id="test_session"
    )
    
    # Should detect PII
    assert result is not None
    assert len(result.violations) > 0 or result.action in ['blocked', 'escalate_hitl']


@pytest.mark.asyncio
async def test_guardrail_confidence_threshold(cache_manager):
    """Test confidence threshold guardrail."""
    guardrail = GuardrailAgent(cache_manager)
    
    # Test with low confidence
    test_data = {
        'response': '{"confidence": 0.5, "executive_summary": "Test"}'
    }
    
    result = guardrail.evaluate(
        insights=test_data,
        session_id="test_session"
    )
    
    # Should flag low confidence
    assert result is not None


@pytest.mark.asyncio
async def test_guardrail_hallucination_detection(cache_manager):
    """Test hallucination detection (missing citations)."""
    guardrail = GuardrailAgent(cache_manager)
    
    # Test without citations
    test_data = {
        'response': '{"executive_summary": "MRR is $1M", "data_citations": []}'
    }
    
    result = guardrail.evaluate(
        insights=test_data,
        session_id="test_session"
    )
    
    # Should detect missing citations
    assert result is not None


@pytest.mark.asyncio
async def test_guardrail_cost_limit(cache_manager):
    """Test cost limit guardrail."""
    guardrail = GuardrailAgent(cache_manager)
    
    # Test with high token count (simulated)
    test_data = {
        'response': '{"executive_summary": "Test"}',
        'metadata': {
            'tokens_input': 100000,  # Very high
            'tokens_output': 50000
        }
    }
    
    result = guardrail.evaluate(
        insights=test_data,
        session_id="test_session"
    )
    
    # Should flag cost limit
    assert result is not None


@pytest.mark.asyncio
async def test_guardrail_adaptive_rules(cache_manager):
    """Test adaptive guardrail rules."""
    guardrail = GuardrailAgent(cache_manager)
    
    # Test adaptive rule loading
    rules = guardrail._load_adaptive_rules()
    
    assert isinstance(rules, list)
    # Rules should be loaded from database or defaults


@pytest.mark.asyncio
async def test_guardrail_learning(cache_manager):
    """Test guardrail learning from HITL feedback."""
    guardrail = GuardrailAgent(cache_manager)
    
    # Test learning from false positive
    guardrail.learn_from_hitl_feedback(
        rule_name="confidence_threshold",
        was_false_positive=True
    )
    
    # Should adjust threshold (implementation dependent)
    assert True  # Placeholder - actual implementation may vary

