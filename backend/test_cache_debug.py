#!/usr/bin/env python3
"""
Debug script to check why agent cache isn't being hit.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cache.cache_manager import CacheManager
# TODO: Update test to use ADK RevenueAgent
# Legacy RevenueAgent removed - update to use ADK
# See docs/CLEANUP_PLAN.md for migration details

# Placeholder - test needs ADK migration
RevenueAgent = None  # Legacy agent removed

def test_cache_context():
    """Test if cache context is consistent."""
    cache_manager = CacheManager()
    revenue_agent = RevenueAgent(cache_manager=cache_manager)
    
    # Simulate two runs with same week
    context1 = {
        'week_number': 10,
        'analysis_type': 'comprehensive',
        'spreadsheet_id': '1PfDS7lMpiwKSl6cBozQITW3GdIDugwmj1x8krenp1Bk',
        'revenue_sheet': 'Weekly Revenue',
        'churn_sheet': None
    }
    
    context2 = {
        'week_number': 10,
        'analysis_type': 'comprehensive',
        'spreadsheet_id': '1PfDS7lMpiwKSl6cBozQITW3GdIDugwmj1x8krenp1Bk',
        'revenue_sheet': 'Weekly Revenue',
        'churn_sheet': None
    }
    
    # Check what BaseAgent would hash
    base_hash1 = cache_manager._hash_context('revenue', context1)
    base_hash2 = cache_manager._hash_context('revenue', context2)
    
    print("BaseAgent cache context hashes:")
    print(f"  Run 1: {base_hash1}")
    print(f"  Run 2: {base_hash2}")
    print(f"  Match: {base_hash1 == base_hash2}")
    
    # Check what's actually cached
    conn = cache_manager.connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT context_hash, request_params, agent_type, timestamp
        FROM agent_responses
        WHERE agent_type = 'revenue'
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    
    print("\nCached agent responses (revenue):")
    for row in cursor.fetchall():
        params = json.loads(row['request_params']) if row['request_params'] else {}
        print(f"  Hash: {row['context_hash'][:16]}...")
        print(f"    Week: {params.get('week_number', 'N/A')}")
        print(f"    Analysis Type: {params.get('analysis_type', 'N/A')}")
        print(f"    Data Hash: {params.get('data_hash', 'N/A')[:16] if params.get('data_hash') else 'N/A'}...")
        print(f"    Timestamp: {row['timestamp']}")
        print()
    
    cache_manager.close()

if __name__ == "__main__":
    test_cache_context()

