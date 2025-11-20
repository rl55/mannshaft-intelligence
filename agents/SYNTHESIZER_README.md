# Synthesizer Agent Implementation

## Overview

The Synthesizer Agent is the intelligence layer that cross-correlates insights from Revenue, Product, and Support agents to provide strategic business intelligence.

## Key Responsibilities

### ✅ Cross-Functional Correlation Detection
- Identifies relationships between revenue, product, and support metrics
- Detects temporal correlations (lagging/leading indicators)
- Identifies segment-specific patterns
- Recognizes seasonal trends

### ✅ Root Cause Analysis
- Uses 5 Whys methodology
- Distinguishes correlation vs causation
- Provides confidence-weighted hypotheses
- Includes supporting evidence

### ✅ Strategic Recommendations
- Prioritized by business impact and feasibility
- Cross-functional action items
- Resource allocation suggestions
- Timeline estimates

### ✅ External Validation
- Validates hypotheses via web search (Google Search API or DuckDuckGo)
- Benchmarks against industry standards
- Verifies market trends
- All searches logged and cached

### ✅ Executive Summary
- 2-3 sentence summary for leadership
- Highlights critical findings
- States primary root cause
- Mentions top recommendation

## Architecture

```
Analytical Agents (Revenue, Product, Support)
    ↓
Synthesizer Agent
    ├── Correlation Detection
    ├── Root Cause Analysis
    ├── Strategic Recommendations
    ├── External Validation
    └── Executive Summary
    ↓
Final Synthesis Output
```

## Input Format

The synthesizer expects `analytical_results` dictionary:

```python
{
    'revenue': {
        'response': '{"analysis": {...}}',  # JSON string
        'confidence_score': 0.92,
        ...
    },
    'product': {
        'response': '{"analysis": {...}}',
        'confidence_score': 0.88,
        ...
    },
    'support': {
        'response': '{"analysis": {...}}',
        'confidence_score': 0.85,
        ...
    }
}
```

## Output Format

```json
{
  "agent_id": "synthesizer_agent_001",
  "agent_type": "synthesizer",
  "timestamp": "2025-11-19T...",
  "confidence": 0.90,
  "executive_summary": "2-3 sentence summary",
  "correlations": [
    {
      "pattern": "Product engagement drop correlates with increased support tickets",
      "agents_involved": ["product", "support"],
      "confidence": 0.85,
      "business_impact": "high",
      "temporal_relationship": "leading",
      "evidence": ["DAU/MAU ratio dropped 15%", "Support tickets increased 30%"]
    }
  ],
  "root_causes": [
    {
      "hypothesis": "New feature rollout caused usability issues",
      "confidence": 0.80,
      "reasoning": "5 Whys analysis...",
      "correlation_vs_causation": "Likely causation based on timing",
      "supporting_evidence": ["Feature launched week 40", "Tickets spiked week 41"]
    }
  ],
  "strategic_recommendations": [
    {
      "action": "Implement feature onboarding flow",
      "priority": "high",
      "expected_impact": "Reduce support tickets by 25%, improve engagement by 10%",
      "feasibility": "high",
      "cross_functional_teams": ["product", "support", "engineering"],
      "resource_requirements": "1 designer, 2 engineers, 2 weeks",
      "timeline": "4 weeks"
    }
  ],
  "key_metrics_summary": {
    "revenue": {
      "current_mrr": 1250000,
      "mom_growth": 0.12,
      "churn_rate": 0.032
    },
    "product": {
      "dau": 45000,
      "mau": 120000,
      "dau_mau_ratio": 0.375
    },
    "support": {
      "ticket_volume": 450,
      "csat_score": 4.2,
      "avg_response_time": 2.5
    }
  },
  "external_validations": [
    {
      "type": "correlation",
      "hypothesis": "...",
      "search_results": {...},
      "validated": true
    }
  ]
}
```

## Advanced Features

### Pattern Recognition

1. **Temporal Correlations**
   - Identifies lagging indicators (e.g., low engagement → churn 4 weeks later)
   - Detects leading indicators (e.g., support ticket spike → churn increase)
   - Recognizes concurrent trends

2. **Segment-Specific Patterns**
   - Analyzes patterns by customer segment
   - Identifies segment-specific correlations
   - Provides segment-level insights

3. **Seasonal Trends**
   - Recognizes seasonal patterns
   - Adjusts for seasonality in analysis
   - Provides context-aware recommendations

### Root Cause Analysis

Uses 5 Whys methodology:
1. Why is this happening?
2. Why is that?
3. Why is that?
4. Why is that?
5. Why is that?

Each root cause includes:
- Hypothesis statement
- Confidence score
- 5 Whys reasoning
- Correlation vs causation assessment
- Supporting evidence

### Strategic Recommendations

Recommendations are prioritized by:
1. **Business Impact**: High/Medium/Low
2. **Feasibility**: High/Medium/Low

Priority order:
1. High impact + High feasibility
2. High impact + Medium feasibility
3. Medium impact + High feasibility

Each recommendation includes:
- Specific actionable item
- Expected quantified impact
- Cross-functional teams involved
- Resource requirements
- Timeline estimate

### External Validation

Validates top correlations and root causes via web search:
- Uses Google Custom Search API (if configured)
- Falls back to DuckDuckGo
- Searches for industry benchmarks
- Validates hypotheses with external data
- All searches cached for 24 hours

## Usage Example

```python
from agents.synthesizer_agent import SynthesizerAgent
from cache.cache_manager import CacheManager

# Initialize synthesizer
cache_manager = CacheManager()
synthesizer = SynthesizerAgent(cache_manager)

# Synthesize results from analytical agents
result = await synthesizer.analyze(
    context={
        'analytical_results': {
            'revenue': revenue_result,
            'product': product_result,
            'support': support_result
        },
        'week_number': 42
    },
    session_id='session-123'
)

# Parse result
import json
synthesis = json.loads(result['response'])
print(f"Executive Summary: {synthesis['executive_summary']}")
print(f"Correlations: {len(synthesis['correlations'])}")
print(f"Recommendations: {len(synthesis['strategic_recommendations'])}")
```

## Configuration

The synthesizer respects:

- `synthesizer.enable_external_validation`: Enable/disable web search validation (default: true)
- `google_search.api_key`: Google Custom Search API key (optional)
- `google_search.cx`: Custom Search Engine ID (optional)

## Caching

- **Prompt Cache**: 24-hour TTL for Gemini prompts
- **Agent Cache**: 1-hour TTL for complete synthesis
- **Web Search Cache**: 24-hour TTL for search results

## Error Handling

- **Missing Agent Results**: Gracefully handles missing agents, reduces confidence
- **Gemini Failures**: Falls back to statistical correlation detection
- **Web Search Failures**: Continues without external validation
- **JSON Parse Errors**: Returns empty results with warning

## Integration with Orchestrator

The orchestrator automatically:
1. Executes Revenue, Product, Support agents in parallel
2. Collects their results
3. Passes results to Synthesizer
4. Returns final synthesis

```python
from agents.orchestrator import OrchestratorAgent

orchestrator = OrchestratorAgent()
result = await orchestrator.analyze_week(
    week_number=42,
    user_id="user-123",
    analysis_type="comprehensive"
)

# Result includes synthesized insights
```

## Dependencies

- `google-generativeai`: Gemini API for analysis
- `aiohttp`: Web search HTTP requests
- `duckduckgo-search`: Fallback search (optional)
- `cache.cache_manager`: Caching and observability

## Performance

- **Target**: <5s for complete synthesis (cache miss)
- **Cache Hit**: <1s response time
- **External Validation**: Adds ~2-3s per validation (cached)

## Testing

```python
import pytest
from agents.synthesizer_agent import SynthesizerAgent

@pytest.mark.asyncio
async def test_synthesis():
    synthesizer = SynthesizerAgent()
    
    result = await synthesizer.analyze(
        context={
            'analytical_results': {
                'revenue': {'response': '{"analysis": {...}}'},
                'product': {'response': '{"analysis": {...}}'},
                'support': {'response': '{"analysis": {...}}'}
            },
            'week_number': 42
        },
        session_id='test-session'
    )
    
    assert result['confidence_score'] > 0
    synthesis = json.loads(result['response'])
    assert 'executive_summary' in synthesis
    assert 'correlations' in synthesis
    assert 'strategic_recommendations' in synthesis
```

