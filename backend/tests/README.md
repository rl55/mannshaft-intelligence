# Test Suite Documentation

## Overview

Comprehensive test suite for the SaaS BI Agent system covering unit tests, integration tests, and performance tests.

## Test Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for full flows
├── performance/       # Performance and load tests
└── fixtures/          # Test data and mock responses
```

## Running Tests

### All Tests

```bash
pytest tests/
```

### With Coverage

```bash
pytest --cov=agents --cov=governance --cov=api --cov=cache --cov=integrations tests/
```

### Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Performance tests only
pytest tests/performance/ -v
```

### With Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only performance tests
pytest -m performance

# Skip slow tests
pytest -m "not slow"
```

## Test Categories

### Unit Tests

- **test_cache_manager.py**: Cache operations, expiration, session management
- **test_revenue_agent.py**: Revenue agent caching, validation, confidence scoring
- **test_guardrails.py**: PII detection, confidence thresholds, hallucination detection
- **test_evaluation.py**: Evaluation criteria, caching, regeneration logic

### Integration Tests

- **test_orchestrator.py**: Full orchestrator flow, error recovery, parallel execution
- **test_full_analysis.py**: Complete analysis pipeline, regeneration, HITL escalation
- **test_api_endpoints.py**: API endpoint testing with TestClient

### Performance Tests

- **test_cache_performance.py**: Cache hit rates, response times, concurrent requests, memory usage

## Fixtures

### Sample Data

- **sample_revenue_data.json**: Sample revenue data for testing
- **sample_product_data.json**: Sample product metrics
- **sample_support_data.json**: Sample support metrics

### Mock Responses

- **mock_gemini_responses.json**: Mock Gemini API responses to avoid hitting real API

## Test Targets

### Cache Performance

- **Hit Rate**: >70% cache hit rate
- **Response Time**: <100ms for cache hits
- **Cache Miss**: <5s for cache misses

### Response Times

- **Agent Execution**: <5s per agent
- **Full Analysis**: <30s for comprehensive analysis
- **API Endpoints**: <500ms for most endpoints

### Concurrent Handling

- Support 10+ concurrent requests
- No race conditions in caching
- Proper session isolation

## Mocking Strategy

### External Services

- **Gemini API**: Mocked using `mock_gemini_responses.json`
- **Google Sheets**: Mocked with sample data
- **Web Search**: Mocked for external validation

### Benefits

- Fast test execution
- No API costs
- Deterministic results
- Offline testing

## Example Test

```python
@pytest.mark.asyncio
async def test_revenue_agent_caching(cache_manager, sample_revenue_data, mock_gemini_responses):
    """Test revenue agent caching behavior."""
    agent = RevenueAgent(cache_manager=cache_manager)
    
    mock_response = mock_gemini_responses.get("revenue_analysis", {})
    
    with patch.object(agent.gemini_client, 'generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response
        
        # First call - cache miss
        result1 = await agent.analyze(context, "session_1")
        assert result1['cached'] == False
        
        # Second call - cache hit
        result2 = await agent.analyze(context, "session_1")
        assert result2['cached'] == True
```

## Continuous Integration

Tests should be run in CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pytest tests/ --cov --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Coverage Goals

- **Overall**: >80% code coverage
- **Critical Paths**: >90% coverage
- **Agents**: >85% coverage
- **Governance**: >90% coverage

## Troubleshooting

### Tests Failing

1. Check fixture files exist
2. Verify database schema is initialized
3. Check mock responses are valid JSON
4. Ensure async/await is used correctly

### Slow Tests

- Use `pytest -m "not slow"` to skip slow tests
- Use `pytest --durations=10` to find slowest tests
- Consider using `pytest-xdist` for parallel execution

### Import Errors

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check `PYTHONPATH` includes project root
- Verify `__init__.py` files exist in test directories

