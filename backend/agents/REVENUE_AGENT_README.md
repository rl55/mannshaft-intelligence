# Revenue Agent Implementation

## Overview

Production-grade Revenue Agent with comprehensive SaaS revenue analysis capabilities, following the pattern from `revenue_agent_example.py` with significant enhancements.

## Key Features

### ✅ Data Validation
- **Pydantic Models**: Comprehensive input/output validation
  - `RevenueInput`: Validates week number, spreadsheet IDs, analysis types
  - `RevenueDataPoint`: Validates individual data points
  - `RevenueAnalysisOutput`: Ensures structured output format
- **Data Quality Checks**: 
  - Completeness scoring
  - Missing field detection
  - Anomaly detection using statistical methods (Z-scores)

### ✅ Enhanced Analysis
- **MRR Analysis**:
  - Current MRR calculation
  - Week-over-week (WoW) growth rate
  - Month-over-month (MoM) growth rate
  - Trend detection (accelerating/decelerating/stable)
  - 4-week revenue forecasting
- **Churn Analysis**:
  - Current churn rate calculation
  - Change from previous period
  - Severity classification (low/medium/high/critical)
  - Cohort breakdown (enterprise/SMB)
- **ARPU Segmentation**:
  - Current ARPU calculation
  - Segmentation by customer tier
  - Trend analysis
- **Anomaly Detection**:
  - Statistical outlier detection (Z-score > 2.5)
  - MRR anomaly flagging
  - Data consistency checks

### ✅ Confidence Scoring
- **Multi-factor Scoring**:
  - Data completeness (0-1)
  - Historical consistency (based on data points)
  - Statistical significance (coefficient of variation)
  - Analysis completeness
  - Anomaly impact
- **Reasoning**: Detailed explanation of confidence score
- **Range**: 0.0 to 1.0 with clear thresholds

### ✅ Google Sheets Integration
- **MCP Protocol**: Reads data via Google Sheets API
- **Error Handling**: Graceful fallback when sheets unavailable
- **Data Parsing**: Intelligent parsing of sheet rows
- **Multiple Sheets**: Supports revenue and churn sheets
- **Data Citations**: Tracks data sources for transparency

### ✅ Gemini Prompt Engineering
- **Structured Prompts**: Well-defined JSON schema requirements
- **Few-shot Examples**: Includes example input/output pairs
- **Data Citations**: Requests citations in responses
- **JSON Extraction**: Handles markdown code blocks
- **Fallback**: Statistical analysis when Gemini fails

### ✅ Performance Optimization
- **Prompt Caching**: 24-hour TTL for prompt-level cache
- **Agent Caching**: 1-hour TTL for agent-level cache
- **Target Performance**:
  - Cache hit: <2s response time
  - Cache miss: <5s response time
- **Token Tracking**: Logs all Gemini API calls to CacheManager

## Output Format

The agent returns a structured JSON response matching the specification:

```json
{
  "agent_id": "revenue_agent_001",
  "agent_type": "revenue",
  "timestamp": "2025-11-19T...",
  "confidence": 0.92,
  "confidence_reasoning": "High confidence: All quality checks passed",
  "analysis": {
    "mrr_analysis": {
      "current_mrr": 1250000,
      "wow_growth": 0.015,
      "mom_growth": 0.12,
      "trend": "accelerating",
      "forecast_next_month": 1400000
    },
    "churn_analysis": {
      "current_rate": 0.032,
      "change_from_previous": -0.009,
      "severity": "low",
      "cohort_breakdown": {
        "enterprise": {"rate": 0.021, "trend": "improving"},
        "smb": {"rate": 0.045, "trend": "stable"}
      }
    },
    "arpu_analysis": {
      "current_arpu": 127,
      "segmentation": {
        "by_tier": {
          "enterprise": 450,
          "smb": 89
        }
      },
      "trend": "increasing"
    },
    "key_insights": [
      "Enterprise segment driving 60% of growth",
      "Annual contracts showing 2.1% churn vs 4.5% monthly"
    ],
    "recommendations": [
      {
        "action": "Increase enterprise sales capacity",
        "priority": "high",
        "expected_impact": "+$150K MRR in Q1"
      }
    ],
    "risk_flags": [],
    "anomalies": [
      {
        "type": "mrr_outlier",
        "description": "Week 5 MRR spike detected",
        "severity": "medium"
      }
    ]
  },
  "data_citations": [
    "Week 8 MRR from Sheets 'Revenue!A8:D8'",
    "Churn data from Sheets 'Churn!A1:E50'"
  ],
  "data_freshness_hours": 2.5
}
```

## Usage Example

```python
from agents.revenue_agent import RevenueAgent
from cache.cache_manager import CacheManager

# Initialize agent
cache_manager = CacheManager()
agent = RevenueAgent(cache_manager=cache_manager)

# Analyze with Google Sheets
result = await agent.analyze(
    context={
        'week_number': 42,
        'spreadsheet_id': 'your-spreadsheet-id',
        'revenue_sheet': 'Revenue',
        'churn_sheet': 'Churn',
        'analysis_type': 'comprehensive'
    },
    session_id='session-123'
)

# Or with manual data
result = await agent.analyze(
    context={
        'week_number': 42,
        'manual_data': {
            'records': [
                {'week': 38, 'mrr': 1150000, 'new_customers': 45, 'churned': 12},
                {'week': 39, 'mrr': 1180000, 'new_customers': 52, 'churned': 10},
                # ... more records
            ]
        },
        'analysis_type': 'comprehensive'
    },
    session_id='session-123'
)

# Parse result
import json
analysis = json.loads(result['response'])
print(f"Confidence: {analysis['confidence']}")
print(f"Current MRR: ${analysis['analysis']['mrr_analysis']['current_mrr']:,.0f}")
print(f"WoW Growth: {analysis['analysis']['mrr_analysis']['wow_growth']:.1%}")
```

## Configuration

The agent respects the following configuration:

- `cache.prompt_ttl_hours`: Prompt cache TTL (default: 24h)
- `cache.agent_response_ttl_hours`: Agent cache TTL (default: 1h)
- `gemini.model`: Gemini model name (default: 'gemini-pro')
- `gemini.temperature`: Generation temperature (default: 0.7)
- `google_sheets.credentials_path`: Path to service account JSON

## Error Handling

- **Input Validation**: Pydantic models catch invalid inputs early
- **Sheet Access Errors**: Graceful fallback with error logging
- **Gemini API Failures**: Falls back to statistical analysis
- **JSON Parse Errors**: Returns fallback analysis with warning
- **Data Quality Issues**: Confidence score reflects data problems

## Performance Metrics

The agent tracks:
- Execution time (ms)
- Cache hit/miss rates
- Token usage (input/output)
- Data quality scores
- Confidence scores

All metrics are logged to CacheManager for observability.

## Testing

Example test cases:

```python
import pytest
from agents.revenue_agent import RevenueAgent, RevenueInput

@pytest.mark.asyncio
async def test_revenue_analysis():
    agent = RevenueAgent()
    result = await agent.analyze(
        context={
            'week_number': 42,
            'manual_data': {
                'records': [
                    {'week': 38, 'mrr': 1150000, 'new_customers': 45, 'churned': 12},
                    {'week': 39, 'mrr': 1180000, 'new_customers': 52, 'churned': 10},
                ]
            }
        },
        session_id='test-session'
    )
    
    assert result['confidence_score'] > 0
    assert 'response' in result
```

## Dependencies

- `pydantic`: Data validation
- `numpy`: Statistical calculations
- `google-generativeai`: Gemini API
- `gspread`: Google Sheets integration
- `cache.cache_manager`: Caching and observability

