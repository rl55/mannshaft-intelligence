#!/usr/bin/env python3
"""
End-to-end cache test script.
Tests that caching is working correctly for Week 10 analysis.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from cache.cache_manager import CacheManager
from agents.orchestrator import OrchestratorAgent
from utils.logger import logger

async def test_cache_e2e():
    """Test end-to-end caching functionality."""
    print("=" * 80)
    print("CACHE END-TO-END TEST")
    print("=" * 80)
    
    cache_manager = CacheManager()
    
    # Step 1: Check initial cache state
    print("\n[STEP 1] Checking initial cache state...")
    conn = cache_manager.connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM prompt_cache")
    prompt_count = cursor.fetchone()['count']
    print(f"  Prompt cache entries: {prompt_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM agent_responses")
    agent_count = cursor.fetchone()['count']
    print(f"  Agent cache entries: {agent_count}")
    
    cursor.execute("""
        SELECT SUM(hit_count) as total_hits 
        FROM prompt_cache
    """)
    total_hits = cursor.fetchone()['total_hits'] or 0
    print(f"  Total prompt cache hits: {total_hits}")
    
    # Step 2: Run Week 10 analysis (first run - should create cache)
    print("\n[STEP 2] Running Week 10 analysis (FIRST RUN - should create cache)...")
    orchestrator = OrchestratorAgent(cache_manager=cache_manager)
    
    try:
        result = await orchestrator.analyze_week(
            week_number=10,
            analysis_type="comprehensive",
            user_id="test_user",
            session_id=None  # Let orchestrator create session
        )
        
        print(f"  ✓ Analysis completed")
        print(f"  Session ID: {result.session_id}")
        print(f"  Cache efficiency: {result.cache_efficiency:.2%}")
        print(f"  Execution time: {result.execution_time_ms}ms")
        print(f"  Agents executed: {result.agents_executed}")
        print(f"  HITL escalations: {result.hitl_escalations}")
        
        # Check cache after first run
        cursor.execute("SELECT COUNT(*) as count FROM prompt_cache")
        prompt_count_after = cursor.fetchone()['count']
        print(f"\n  Prompt cache entries after first run: {prompt_count_after} (was {prompt_count})")
        
        cursor.execute("SELECT COUNT(*) as count FROM agent_responses")
        agent_count_after = cursor.fetchone()['count']
        print(f"  Agent cache entries after first run: {agent_count_after} (was {agent_count})")
        
        # Step 3: Run Week 10 analysis again (second run - should hit cache)
        print("\n[STEP 3] Running Week 10 analysis (SECOND RUN - should hit cache)...")
        
        result2 = await orchestrator.analyze_week(
            week_number=10,
            analysis_type="comprehensive",
            user_id="test_user",
            session_id=None
        )
        
        print(f"  ✓ Analysis completed")
        print(f"  Session ID: {result2.session_id}")
        print(f"  Cache efficiency: {result2.cache_efficiency:.2%}")
        print(f"  Execution time: {result2.execution_time_ms}ms")
        print(f"  Agents executed: {result2.agents_executed}")
        
        # Check cache hits
        cursor.execute("""
            SELECT SUM(hit_count) as total_hits 
            FROM prompt_cache
        """)
        total_hits_after = cursor.fetchone()['total_hits'] or 0
        print(f"\n  Total prompt cache hits after second run: {total_hits_after} (was {total_hits})")
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM agent_responses 
            WHERE cache_hit = 1
        """)
        agent_hits = cursor.fetchone()['count']
        print(f"  Agent cache hits: {agent_hits}")
        
        # Step 4: Verify Week 10 results
        print("\n[STEP 4] Verifying Week 10 results...")
        # Check if results mention Week 10
        if "Week 10" in result.report or "week 10" in result.report.lower():
            print("  ✓ Results contain Week 10 references")
        else:
            print("  ✗ WARNING: Results may not be for Week 10")
            print(f"  Report preview: {result.report[:200]}...")
        
        # Step 5: Check HITL
        print("\n[STEP 5] Checking HITL escalations...")
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM hitl_requests 
            WHERE trace_id IN (
                SELECT trace_id FROM traces WHERE session_id = ?
            )
        """, (result.session_id,))
        hitl_count = cursor.fetchone()['count']
        print(f"  HITL requests for session: {hitl_count}")
        
        if result.hitl_escalations > 0:
            cursor.execute("""
                SELECT request_id, status, reason 
                FROM hitl_requests 
                WHERE trace_id IN (
                    SELECT trace_id FROM traces WHERE session_id = ?
                )
                LIMIT 5
            """, (result.session_id,))
            hitl_requests = cursor.fetchall()
            for req in hitl_requests:
                reason = req.get('reason', 'N/A')
                print(f"    - Request {req['request_id'][:8]}: {req['status']} - {reason[:50] if reason else 'N/A'}")
        else:
            print("  No HITL escalations found")
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"✓ Cache entries created: {prompt_count_after - prompt_count} prompts, {agent_count_after - agent_count} agents")
        print(f"✓ Cache hits: {total_hits_after - total_hits} prompt hits, {agent_hits} agent hits")
        print(f"✓ Cache efficiency: {result2.cache_efficiency:.2%}")
        print(f"✓ Week 10 analysis: {'PASS' if 'Week 10' in result.report or 'week 10' in result.report.lower() else 'CHECK MANUALLY'}")
        print(f"✓ HITL escalations: {result.hitl_escalations}")
        
        if result2.cache_efficiency > 0:
            print("\n✓ CACHING IS WORKING!")
        else:
            print("\n✗ WARNING: Cache efficiency is 0% - caching may not be working correctly")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        cache_manager.close()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_cache_e2e())
    sys.exit(0 if success else 1)

