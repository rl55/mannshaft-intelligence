"""
Unit tests for CacheManager.
"""

import pytest
import json
import time
from datetime import datetime, timedelta

from cache.cache_manager import CacheManager


@pytest.mark.asyncio
async def test_cache_manager_initialization(test_db_path):
    """Test cache manager initialization."""
    db_path, schema_path = test_db_path
    cache = CacheManager(db_path=db_path, schema_path=schema_path)
    
    assert cache is not None
    assert cache.db_path == db_path


def test_cache_prompt(cache_manager):
    """Test caching a prompt."""
    prompt = "Test prompt"
    response = "Test response"
    
    cache_manager.cache_prompt(
        prompt=prompt,
        response=response,
        model="test-model",
        tokens_input=100,
        tokens_output=50,
        ttl_hours=24
    )
    
    # Retrieve cached prompt
    cached = cache_manager.get_cached_prompt(prompt=prompt, model="test-model")
    
    assert cached is not None
    assert cached['response'] == response
    assert cached['tokens_input'] == 100
    assert cached['tokens_output'] == 50


def test_cache_agent_response(cache_manager):
    """Test caching an agent response."""
    agent_type = "test_agent"
    context = {"week_number": 25, "analysis_type": "comprehensive"}
    response = "Test agent response"
    
    cache_manager.cache_agent_response(
        agent_type=agent_type,
        context=context,
        response=response,
        confidence_score=0.9,
        execution_time_ms=1000,
        ttl_hours=24
    )
    
    # Retrieve cached response
    cached = cache_manager.get_cached_agent_response(
        agent_type=agent_type,
        context=context
    )
    
    assert cached is not None
    assert cached['response'] == response
    assert cached['confidence_score'] == 0.9


def test_cache_expiration(cache_manager):
    """Test that cache entries expire correctly."""
    prompt = "Expiring prompt"
    response = "Expired response"
    
    # Cache with very short TTL
    cache_manager.cache_prompt(
        prompt=prompt,
        response=response,
        model="test-model",
        tokens_input=0,
        tokens_output=0,
        ttl_hours=0.0001  # Very short TTL (0.36 seconds)
    )
    
    # Should be cached immediately
    cached = cache_manager.get_cached_prompt(prompt=prompt, model="test-model")
    assert cached is not None
    
    # Wait for expiration
    time.sleep(0.5)
    
    # Should be expired
    cached = cache_manager.get_cached_prompt(prompt=prompt, model="test-model")
    assert cached is None


def test_session_management(cache_manager):
    """Test session creation and management."""
    session_id = cache_manager.create_session(
        session_type="test_session",
        user_id="test_user"
    )
    
    assert session_id is not None
    
    # End session
    cache_manager.end_session(session_id, final_status="completed")
    
    # Verify session exists
    conn = cache_manager.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    
    assert row is not None
    assert row['status'] == "completed"


def test_trace_creation(cache_manager):
    """Test trace creation."""
    session_id = cache_manager.create_session("test", "user")
    
    trace_id = cache_manager.start_trace(
        session_id=session_id,
        agent_type="test_agent"
    )
    
    assert trace_id is not None
    
    # End trace
    cache_manager.end_trace(
        trace_id=trace_id,
        status="success",
        duration_ms=1000
    )
    
    # Verify trace exists
    conn = cache_manager.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM traces WHERE trace_id = ?", (trace_id,))
    row = cursor.fetchone()
    
    assert row is not None
    assert row['status'] == "success"


def test_cache_stats(cache_manager):
    """Test cache statistics retrieval."""
    # Create some cache entries
    for i in range(5):
        cache_manager.cache_prompt(
            prompt=f"prompt_{i}",
            response=f"response_{i}",
            model="test-model",
            tokens_input=100,
            tokens_output=50,
            ttl_hours=24
        )
    
    # Get stats (simplified - actual implementation may vary)
    conn = cache_manager.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM prompt_cache")
    count = cursor.fetchone()['count']
    
    assert count == 5

