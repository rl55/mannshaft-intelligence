"""
Pytest configuration and shared fixtures.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from cache.cache_manager import CacheManager
from agents.revenue_agent import RevenueAgent
from agents.product_agent import ProductAgent
from agents.support_agent import SupportAgent
from agents.synthesizer_agent import SynthesizerAgent
from governance.guardrails import GuardrailAgent
from governance.evaluation import Evaluator
from governance.hitl_manager import HITLManager


@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database path for tests."""
    db_path = tmp_path / "test_cache.db"
    schema_path = Path(__file__).parent.parent / "data" / "schema.sql"
    return str(db_path), str(schema_path)


@pytest.fixture
def cache_manager(test_db_path):
    """Create a cache manager instance for tests."""
    db_path, schema_path = test_db_path
    return CacheManager(db_path=db_path, schema_path=schema_path)


@pytest.fixture
def revenue_agent(cache_manager):
    """Create a revenue agent instance for tests."""
    return RevenueAgent(cache_manager=cache_manager)


@pytest.fixture
def product_agent(cache_manager):
    """Create a product agent instance for tests."""
    return ProductAgent(cache_manager=cache_manager)


@pytest.fixture
def support_agent(cache_manager):
    """Create a support agent instance for tests."""
    return SupportAgent(cache_manager=cache_manager)


@pytest.fixture
def synthesizer_agent(cache_manager):
    """Create a synthesizer agent instance for tests."""
    return SynthesizerAgent(cache_manager=cache_manager)


@pytest.fixture
def guardrail_agent(cache_manager):
    """Create a guardrail agent instance for tests."""
    return GuardrailAgent(cache_manager)


@pytest.fixture
def evaluator(cache_manager):
    """Create an evaluator instance for tests."""
    return Evaluator(cache_manager=cache_manager)


@pytest.fixture
def hitl_manager(cache_manager, guardrail_agent):
    """Create a HITL manager instance for tests."""
    return HITLManager(cache_manager=cache_manager, guardrail_agent=guardrail_agent)


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client for tests."""
    mock_client = AsyncMock()
    mock_client.generate = AsyncMock(return_value={
        'text': '{"analysis": {"key_insights": ["Test insight"]}, "confidence": 0.9}',
        'tokens_input': 100,
        'tokens_output': 50
    })
    return mock_client


@pytest.fixture
def mock_sheets_client():
    """Mock Google Sheets client for tests."""
    mock_client = Mock()
    mock_client.get_sheet_data = Mock(return_value=[
        ['Week', 'MRR', 'New Customers', 'Churned'],
        ['25', '100000', '10', '2'],
        ['26', '105000', '12', '1']
    ])
    mock_client.client = Mock()  # Simulate initialized client
    return mock_client


def load_fixture(filename):
    """Load a fixture file."""
    fixture_path = Path(__file__).parent / "fixtures" / filename
    if not fixture_path.exists():
        return None
    with open(fixture_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def sample_revenue_data():
    """Load sample revenue data fixture."""
    return load_fixture("sample_revenue_data.json") or {
        "week_number": 25,
        "revenue_data": [
            {"week": 25, "mrr": 100000, "new_customers": 10, "churned": 2},
            {"week": 26, "mrr": 105000, "new_customers": 12, "churned": 1}
        ]
    }


@pytest.fixture
def sample_product_data():
    """Load sample product data fixture."""
    return load_fixture("sample_product_data.json") or {
        "week_number": 25,
        "dau": 5000,
        "wau": 15000,
        "mau": 50000,
        "feature_adoption": {"feature_a": 0.75, "feature_b": 0.50}
    }


@pytest.fixture
def sample_support_data():
    """Load sample support data fixture."""
    return load_fixture("sample_support_data.json") or {
        "week_number": 25,
        "ticket_volume": 150,
        "average_response_time_hours": 2.5,
        "csat_score": 4.2
    }


@pytest.fixture
def mock_gemini_responses():
    """Load mock Gemini responses fixture."""
    return load_fixture("mock_gemini_responses.json") or {
        "revenue_analysis": {
            "text": '{"analysis": {"mrr_analysis": {"current_mrr": 100000}, "key_insights": ["MRR growing"]}, "confidence": 0.9}',
            "tokens_input": 200,
            "tokens_output": 100
        },
        "product_analysis": {
            "text": '{"analysis": {"dau": 5000, "key_insights": ["DAU stable"]}, "confidence": 0.85}',
            "tokens_input": 150,
            "tokens_output": 80
        },
        "support_analysis": {
            "text": '{"analysis": {"ticket_volume": 150, "key_insights": ["Volume normal"]}, "confidence": 0.88}',
            "tokens_input": 180,
            "tokens_output": 90
        }
    }

