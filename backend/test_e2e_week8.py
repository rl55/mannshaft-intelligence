#!/usr/bin/env python3
"""
End-to-end test for Week 8 analysis using ADK integration.
"""

import asyncio
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from adk_integration import run_adk_analysis
from database.db_manager import get_db_manager
from cache.cache_manager import CacheManager
from utils.logger import logger


async def emit_test_event(event_dict):
    """Test event emitter for WebSocket events."""
    event_type = event_dict.get('type', 'unknown')
    agent = event_dict.get('agent', 'unknown')
    progress = event_dict.get('progress', 0)
    message = event_dict.get('message', '')
    print(f"  📡 [{progress}%] {event_type} - {agent}: {message}")


async def test_week8_analysis():
    """Run end-to-end test for Week 8 analysis."""
    print("=" * 80)
    print("End-to-End Test: Week 8 Analysis")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Initialize components
    try:
        db_manager = get_db_manager()
        cache_manager = CacheManager()
        
        # Test parameters
        week_number = 8
        analysis_type = "comprehensive"
        user_id = "e2e-test-user"
        session_id = f"e2e-test-week{week_number}-{int(time.time())}"
        
        print(f"📊 Test Configuration:")
        print(f"   Week Number: {week_number}")
        print(f"   Analysis Type: {analysis_type}")
        print(f"   User ID: {user_id}")
        print(f"   Session ID: {session_id}")
        print()
        
        # Create session in database
        print("🔧 Setting up session...")
        db_manager.create_session(
            session_id=session_id,
            session_type=f"weekly_analysis_{analysis_type}",
            user_id=user_id,
            week_number=week_number,
            analysis_type=analysis_type
        )
        print("   ✅ Session created in database")
        
        # Create session in cache manager
        cache_manager.create_session(
            session_type=f"weekly_analysis_{analysis_type}",
            user_id=user_id
        )
        print("   ✅ Session created in cache")
        print()
        
        # Run analysis
        print("🚀 Starting ADK analysis...")
        print()
        
        start_time = time.time()
        result = await run_adk_analysis(
            week_number=week_number,
            session_id=session_id,
            analysis_type=analysis_type,
            user_id=user_id,
            event_emitter=emit_test_event
        )
        execution_time = time.time() - start_time
        
        print()
        print("=" * 80)
        print("📋 Test Results")
        print("=" * 80)
        
        # Check for errors
        if result.report.get('error'):
            print(f"❌ Analysis failed with error:")
            print(f"   {result.report.get('error')}")
            return False
        
        # Verify result structure
        print(f"✅ Analysis completed successfully")
        print(f"   Session ID: {result.session_id}")
        print(f"   Execution Time: {execution_time:.2f}s ({result.execution_time_ms}ms)")
        print(f"   Quality Score: {result.quality_score:.2f}")
        print(f"   Agents Executed: {len(result.agents_executed)}")
        print(f"   Agents: {', '.join(result.agents_executed) if result.agents_executed else 'N/A'}")
        print(f"   Cache Efficiency: {result.cache_efficiency:.2%}")
        print(f"   HITL Escalations: {result.hitl_escalations}")
        print(f"   Guardrail Violations: {result.guardrail_violations}")
        print(f"   Evaluation Passed: {result.evaluation_passed}")
        print()
        
        # Verify report structure
        print("📄 Report Structure:")
        if isinstance(result.report, dict):
            print(f"   Report Keys: {list(result.report.keys())[:10]}...")
            if 'summary' in result.report or 'executive_summary' in result.report:
                print("   ✅ Report contains summary")
            if 'agents' in result.report:
                print(f"   ✅ Report contains agent results: {len(result.report.get('agents', {}))}")
        else:
            print(f"   Report Type: {type(result.report)}")
        print()
        
        # Verify database persistence
        print("💾 Verifying database persistence...")
        saved_result = db_manager.get_analysis_result(session_id)
        if saved_result:
            print("   ✅ Result saved to database")
            print(f"   Quality Score: {saved_result.get('quality_score', 'N/A')}")
            print(f"   Execution Time: {saved_result.get('execution_time_ms', 'N/A')}ms")
        else:
            print("   ⚠️  Result not found in database (may need to be saved)")
        print()
        
        # Verify session status
        session = db_manager.get_session(session_id)
        if session:
            print("📊 Session Status:")
            print(f"   Status: {session.get('current_status', 'N/A')}")
            print(f"   Progress: {session.get('progress', 'N/A')}%")
            print(f"   Week Number: {session.get('week_number', 'N/A')}")
        print()
        
        # Final verification
        success_criteria = [
            result.session_id == session_id,
            result.execution_time_ms > 0,
            result.quality_score >= 0.0,
            isinstance(result.report, dict),
            not result.report.get('error'),
        ]
        
        all_passed = all(success_criteria)
        
        print("=" * 80)
        if all_passed:
            print("✅ END-TO-END TEST PASSED")
            print("=" * 80)
            print("\nAll success criteria met:")
            print("  ✅ Session ID matches")
            print("  ✅ Execution time recorded")
            print("  ✅ Quality score valid")
            print("  ✅ Report structure valid")
            print("  ✅ No errors in report")
            return True
        else:
            print("❌ END-TO-END TEST FAILED")
            print("=" * 80)
            print("\nFailed criteria:")
            if not success_criteria[0]:
                print("  ❌ Session ID mismatch")
            if not success_criteria[1]:
                print("  ❌ Execution time not recorded")
            if not success_criteria[2]:
                print("  ❌ Quality score invalid")
            if not success_criteria[3]:
                print("  ❌ Report structure invalid")
            if not success_criteria[4]:
                print("  ❌ Error in report")
            return False
            
    except Exception as e:
        logger.error(f"End-to-end test failed: {e}", exc_info=True)
        print(f"\n❌ END-TO-END TEST FAILED WITH EXCEPTION:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(test_week8_analysis())
    print()
    sys.exit(0 if success else 1)

