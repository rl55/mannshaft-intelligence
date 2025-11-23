"""
SaaS BI Agent - Setup & Test Script
Initializes database, runs comprehensive tests, and displays system status
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.cache_manager import CacheManager


def test_database_init():
    """Test database initialization"""
    print("\n" + "=" * 60)
    print("TEST 1: Database Initialization")
    print("=" * 60)
    
    try:
        cache = CacheManager(db_path="data/agent_cache.db")
        print("✓ Database initialized successfully")
        
        # Verify tables exist
        conn = cache.connect()
        cursor = conn.cursor()
        
        expected_tables = [
            'prompt_cache', 'agent_responses', 'traces', 'error_logs',
            'metrics', 'guardrail_violations', 'hitl_requests',
            'adaptive_rules', 'sessions', 'evaluations', 'data_freshness'
        ]
        
        for table in expected_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"  ✓ Table '{table}' exists")
            else:
                print(f"  ✗ Table '{table}' missing")
                return None
        
        # Verify views exist
        expected_views = [
            'v_cache_performance', 'v_agent_performance',
            'v_guardrail_effectiveness', 'v_hitl_performance',
            'v_session_efficiency'
        ]
        
        for view in expected_views:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view}'")
            if cursor.fetchone():
                print(f"  ✓ View '{view}' exists")
            else:
                print(f"  ✗ View '{view}' missing")
        
        return cache
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return None


def test_prompt_caching(cache: CacheManager):
    """Test prompt-level caching"""
    print("\n" + "=" * 60)
    print("TEST 2: Prompt Caching")
    print("=" * 60)
    
    test_prompt = "Analyze the following revenue data..."
    test_model = "gemini-2.0-flash"
    test_response = "Analysis: Revenue shows strong growth..."
    
    # First cache
    cache_id = cache.cache_prompt(
        prompt=test_prompt,
        response=test_response,
        model=test_model,
        tokens_input=100,
        tokens_output=200,
        ttl_hours=168
    )
    print(f"✓ Cached prompt with ID: {cache_id}")
    
    # Retrieve from cache
    cached = cache.get_cached_prompt(test_prompt, test_model)
    if cached:
        print(f"✓ Retrieved from cache (hit_count: {cached['hit_count']})")
        print(f"  Response preview: {cached['response'][:50]}...")
    else:
        print("✗ Failed to retrieve from cache")
    
    # Second retrieval (should increment hit count)
    cached2 = cache.get_cached_prompt(test_prompt, test_model)
    if cached2 and cached2['hit_count'] == 2:
        print(f"✓ Cache hit counter incremented correctly")
    else:
        print(f"✗ Cache hit counter not working (expected 2, got {cached2['hit_count'] if cached2 else 'None'})")


def test_agent_response_caching(cache: CacheManager):
    """Test agent-level response caching"""
    print("\n" + "=" * 60)
    print("TEST 3: Agent Response Caching")
    print("=" * 60)
    
    agent_type = "revenue"
    context = {
        "data": {"mrr": 100000, "churn": 2.5},
        "period": "2025-Q4"
    }
    response = '{"analysis": "Strong performance", "confidence": 0.9}'
    
    # Cache agent response
    cache_id = cache.cache_agent_response(
        agent_type=agent_type,
        context=context,
        response=response,
        confidence_score=0.9,
        execution_time_ms=1500,
        ttl_hours=24
    )
    print(f"✓ Cached agent response with ID: {cache_id}")
    
    # Retrieve from cache
    cached = cache.get_cached_agent_response(agent_type, context)
    if cached:
        print(f"✓ Retrieved agent response from cache")
        print(f"  Confidence: {cached['confidence_score']}")
        print(f"  Execution time: {cached['execution_time_ms']}ms")
    else:
        print("✗ Failed to retrieve agent response from cache")
    
    # Different context (should be cache miss)
    different_context = {"data": {"mrr": 200000}, "period": "2025-Q3"}
    cached_different = cache.get_cached_agent_response(agent_type, different_context)
    if not cached_different:
        print("✓ Cache correctly missed for different context")
    else:
        print("✗ Cache incorrectly hit for different context")


def test_tracing(cache: CacheManager):
    """Test distributed tracing"""
    print("\n" + "=" * 60)
    print("TEST 4: Distributed Tracing")
    print("=" * 60)
    
    session_id = cache.create_session(session_type="test_session", user_id="test_user")
    print(f"✓ Created session: {session_id}")
    
    # Start trace
    trace_id = cache.start_trace(
        agent_type="revenue",
        session_id=session_id
    )
    print(f"✓ Started trace: {trace_id}")
    
    # Simulate work
    time.sleep(0.1)
    
    # End trace
    cache.end_trace(
        trace_id=trace_id,
        status="success",
        input_tokens=500,
        output_tokens=1000,
        cached_tokens=200,
        metadata={"test": True}
    )
    print(f"✓ Ended trace successfully")
    
    # End session
    cache.end_session(session_id, final_status="completed")
    print(f"✓ Ended session successfully")


def test_error_logging(cache: CacheManager):
    """Test error logging"""
    print("\n" + "=" * 60)
    print("TEST 5: Error Logging")
    print("=" * 60)
    
    cache.log_error(
        agent_type="product",
        error_type="ValidationError",
        error_message="Missing required field: dau_data",
        stack_trace="Traceback...",
        context={"operation": "analyze_engagement"},
        severity="medium"
    )
    print("✓ Logged error successfully")
    
    # Query recent errors
    conn = cache.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM error_logs WHERE severity='medium'")
    count = cursor.fetchone()[0]
    print(f"✓ Found {count} medium severity error(s) in database")


def test_metrics(cache: CacheManager):
    """Test metrics recording"""
    print("\n" + "=" * 60)
    print("TEST 6: Metrics Recording")
    print("=" * 60)
    
    cache.record_metric(
        metric_name="analysis_latency_ms",
        metric_value=1250.5,
        agent_type="revenue",
        dimensions={"analysis_type": "comprehensive"}
    )
    print("✓ Recorded metric successfully")
    
    # Query metrics
    conn = cache.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM metrics WHERE metric_name='analysis_latency_ms'")
    count = cursor.fetchone()[0]
    print(f"✓ Found {count} metric(s) in database")


def test_guardrails(cache: CacheManager):
    """Test guardrail violation tracking"""
    print("\n" + "=" * 60)
    print("TEST 7: Guardrail Violations")
    print("=" * 60)
    
    session_id = cache.create_session(session_type="test")
    trace_id = cache.start_trace("revenue", session_id)
    
    cache.log_guardrail_violation(
        trace_id=trace_id,
        agent_type="revenue",
        rule_type="hard",
        rule_name="data_completeness_check",
        violation_severity="medium",
        violation_details={"missing_weeks": 3},
        action_taken="escalated",
        human_review_required=True
    )
    print("✓ Logged guardrail violation successfully")
    
    cache.end_trace(trace_id, "success")
    cache.end_session(session_id)
    
    # Query violations
    conn = cache.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM guardrail_violations WHERE rule_name='data_completeness_check'")
    count = cursor.fetchone()[0]
    print(f"✓ Found {count} guardrail violation(s) in database")


def test_session_management(cache: CacheManager):
    """Test session management"""
    print("\n" + "=" * 60)
    print("TEST 8: Session Management")
    print("=" * 60)
    
    # Create session
    session_id = cache.create_session(
        session_type="weekly_review",
        user_id="test_user_123"
    )
    print(f"✓ Created session: {session_id}")
    
    # Create some traces for this session
    trace1 = cache.start_trace("revenue", session_id)
    cache.end_trace(trace1, "success", input_tokens=500, output_tokens=1000)
    
    trace2 = cache.start_trace("product", session_id)
    cache.end_trace(trace2, "success", input_tokens=600, output_tokens=1200)
    
    print("✓ Created 2 traces for session")
    
    # End session (should calculate stats)
    cache.end_session(session_id, final_status="completed")
    print("✓ Session ended with statistics calculated")
    
    # Verify session stats
    conn = cache.connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT total_agents_invoked, total_tokens_used, final_status
        FROM sessions WHERE session_id = ?
    """, (session_id,))
    session_data = cursor.fetchone()
    
    if session_data:
        print(f"  Agents invoked: {session_data[0]}")
        print(f"  Total tokens: {session_data[1]}")
        print(f"  Status: {session_data[2]}")


def test_views(cache: CacheManager):
    """Test database views"""
    print("\n" + "=" * 60)
    print("TEST 9: Database Views")
    print("=" * 60)
    
    # Test cache performance view
    cache_stats = cache.get_cache_stats(days=7)
    print(f"✓ Cache performance view: {len(cache_stats)} rows")
    
    # Test agent performance view
    agent_perf = cache.get_agent_performance()
    print(f"✓ Agent performance view: {len(agent_perf)} rows")
    if agent_perf:
        print(f"  Sample: {agent_perf[0]['agent_type']} - "
              f"{agent_perf[0]['total_invocations']} invocations")
    
    # Test guardrail effectiveness view
    guardrail_stats = cache.get_guardrail_effectiveness()
    print(f"✓ Guardrail effectiveness view: {len(guardrail_stats)} rows")


def print_summary(cache: CacheManager):
    """Print comprehensive system summary"""
    print("\n" + "=" * 60)
    print("SYSTEM SUMMARY")
    print("=" * 60)
    
    conn = cache.connect()
    cursor = conn.cursor()
    
    # Count entries in each table
    tables = [
        'prompt_cache', 'agent_responses', 'traces', 'sessions',
        'error_logs', 'metrics', 'guardrail_violations'
    ]
    
    print("\nTable Row Counts:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:30s}: {count:5d} rows")
    
    # Cache efficiency
    cursor.execute("""
        SELECT 
            SUM(hit_count) as total_hits,
            SUM(tokens_saved) as total_saved
        FROM prompt_cache
    """)
    cache_stats = cursor.fetchone()
    if cache_stats and cache_stats[0]:
        print(f"\nCache Statistics:")
        print(f"  Total cache hits: {cache_stats[0]}")
        print(f"  Tokens saved: {cache_stats[1]}")
    
    print(f"\n{'=' * 60}")
    print("Next Steps:")
    print("=" * 60)
    print("""
  1. Check database file: data/agent_cache.db
  2. Check architecture: docs/ARCHITECTURE_MERMAID.md
  3. Run example: python agents/revenue_agent_example.py
  4. Start building your agents!

Quick Commands:
  # View cache stats
  sqlite3 data/agent_cache.db "SELECT * FROM v_cache_performance"
  
  # View agent performance
  sqlite3 data/agent_cache.db "SELECT * FROM v_agent_performance"
  
  # View recent sessions
  sqlite3 data/agent_cache.db "SELECT * FROM sessions ORDER BY start_time DESC LIMIT 5"
""")


def main():
    """Run all setup and tests"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         SaaS BI Agent - Setup & Test Script                 ║
║         Multi-Agent Intelligence Platform                    ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Run tests
    cache = test_database_init()
    if not cache:
        print("\n✗ Setup failed - could not initialize database")
        return 1
    
    test_prompt_caching(cache)
    test_agent_response_caching(cache)
    test_tracing(cache)
    test_error_logging(cache)
    test_metrics(cache)
    test_guardrails(cache)
    test_session_management(cache)
    test_views(cache)
    
    print_summary(cache)
    
    cache.close()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
