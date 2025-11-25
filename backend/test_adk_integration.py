#!/usr/bin/env python3
"""
Test script for ADK integration.
Verifies that ADK agents can be executed through the integration wrapper.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from adk_integration import run_adk_analysis
from utils.logger import logger


async def test_adk_integration():
    """Test ADK integration wrapper."""
    print("=" * 80)
    print("Testing ADK Integration")
    print("=" * 80)
    
    try:
        # Test with a simple week number
        session_id = "test-session-adk-integration"
        week_number = 1
        analysis_type = "comprehensive"
        user_id = "test-user"
        
        print(f"\n📊 Running ADK analysis:")
        print(f"   Session ID: {session_id}")
        print(f"   Week Number: {week_number}")
        print(f"   Analysis Type: {analysis_type}")
        print(f"   User ID: {user_id}")
        print()
        
        # Simple event emitter for testing
        async def test_event_emitter(event):
            print(f"   📡 Event: {event.get('type')} - {event.get('message', '')}")
        
        # Run analysis
        result = await run_adk_analysis(
            week_number=week_number,
            session_id=session_id,
            analysis_type=analysis_type,
            user_id=user_id,
            event_emitter=test_event_emitter
        )
        
        print("\n" + "=" * 80)
        print("✅ ADK Integration Test Results")
        print("=" * 80)
        print(f"Session ID: {result.session_id}")
        print(f"Quality Score: {result.quality_score}")
        print(f"Execution Time: {result.execution_time_ms}ms")
        print(f"Agents Executed: {result.agents_executed}")
        print(f"Report Keys: {list(result.report.keys()) if isinstance(result.report, dict) else 'N/A'}")
        print(f"Metadata: {result.metadata}")
        print("=" * 80)
        
        if result.report and not result.report.get('error'):
            print("✅ ADK integration test PASSED")
            return 0
        else:
            print("⚠️  ADK integration test completed with warnings")
            if result.report.get('error'):
                print(f"   Error: {result.report.get('error')}")
            return 1
            
    except Exception as e:
        logger.error(f"ADK integration test failed: {e}", exc_info=True)
        print(f"\n❌ ADK integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_adk_integration())
    sys.exit(exit_code)

