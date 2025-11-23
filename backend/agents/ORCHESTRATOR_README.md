# Orchestrator Agent Implementation

## Overview

The `OrchestratorAgent` is the core coordination component for weekly SaaS analysis. It manages the complete analysis lifecycle from session creation to final report delivery.

## Key Features

### ✅ Session Management
- Creates and manages analysis sessions via CacheManager
- Tracks session lifecycle and statistics
- Handles session cleanup on completion or error

### ✅ Parallel Agent Execution
- Executes Revenue, Product, and Support agents concurrently using `asyncio.gather`
- Configurable timeout handling per agent
- Graceful error handling - agent failures don't crash orchestrator

### ✅ Data Aggregation
- Collects results from all analytical agents
- Passes aggregated data to Synthesizer agent
- Handles partial results when some agents fail

### ✅ Governance Integration
- **Guardrails**: Validates synthesized responses against rules
- **Evaluation**: Assesses response quality (factual grounding, relevance, completeness, coherence)
- **HITL**: Escalates critical violations for human review
- **Regeneration**: Automatically regenerates if quality is poor

### ✅ Error Handling & Recovery
- Individual agent failures are caught and logged
- Partial results are synthesized when possible
- Retry logic for transient failures
- Comprehensive error logging to CacheManager

### ✅ Progress Tracking
- Tracks execution time for each agent
- Calculates cache efficiency
- Records quality scores
- Monitors HITL escalations and guardrail violations

## Architecture Flow

```
1. Initialize Session
   ↓
2. Execute Analytical Agents (Parallel)
   ├── Revenue Agent
   ├── Product Agent
   └── Support Agent
   ↓
3. Synthesize Results
   └── Synthesizer Agent
   ↓
4. Apply Guardrails
   └── Validate Response
   ↓
5. Handle HITL Escalations (if needed)
   └── Create HITL Requests
   ↓
6. Evaluate Quality
   └── Evaluator Agent
   ↓
7. Regeneration Loop (if quality poor)
   └── Retry from Step 2
   ↓
8. Deliver Final Report
   └── AnalysisResult
```

## Usage Example

```python
from agents.orchestrator import OrchestratorAgent
from cache.cache_manager import CacheManager

# Initialize orchestrator
cache_manager = CacheManager()
orchestrator = OrchestratorAgent(cache_manager=cache_manager)

# Run weekly analysis
result = await orchestrator.analyze_week(
    week_number=42,
    user_id="user-123",
    analysis_type="comprehensive"
)

# Access results
print(f"Report: {result.report}")
print(f"Quality Score: {result.quality_score}")
print(f"Cache Efficiency: {result.cache_efficiency}")
print(f"Execution Time: {result.execution_time_ms}ms")
print(f"Agents Executed: {result.agents_executed}")
print(f"HITL Escalations: {result.hitl_escalations}")
```

## Analysis Types

- `comprehensive`: Execute all agents (Revenue, Product, Support)
- `revenue_only`: Execute only Revenue agent
- `product_only`: Execute only Product agent
- `support_only`: Execute only Support agent

## Configuration

The orchestrator respects the following configuration values:

- `agents.timeout_seconds`: Timeout for agent execution (default: 60s)
- `agents.max_retries`: Maximum retry attempts (default: 3)
- `agents.min_quality_score`: Minimum acceptable quality (default: 0.7)
- `agents.max_regenerations`: Maximum regeneration attempts (default: 2)
- `governance.guardrails_enabled`: Enable/disable guardrails (default: true)
- `governance.hitl_enabled`: Enable/disable HITL (default: true)
- `governance.evaluation_enabled`: Enable/disable evaluation (default: true)

## Error Handling

### Agent Failures
- Individual agent failures are caught and logged
- Error information is included in the result
- Orchestrator continues with remaining agents

### Timeouts
- Each agent has a configurable timeout
- Timed-out agents return error responses
- Orchestrator continues with successful agents

### Quality Failures
- If evaluation fails or quality is poor, regeneration is attempted
- Maximum regeneration attempts are configurable
- Final result includes regeneration count

## Testing

Unit tests are provided in `tests/test_orchestrator.py`. Run with:

```bash
pytest tests/test_orchestrator.py -v
```

Test coverage includes:
- Comprehensive analysis flow
- Analysis type variations
- Error handling
- Timeout handling
- Guardrail violations
- HITL escalations
- Cache efficiency calculation

## Return Value: AnalysisResult

The `analyze_week` method returns an `AnalysisResult` dataclass with:

- `report`: Final synthesized report text
- `session_id`: Session identifier
- `quality_score`: Overall quality score (0-1)
- `cache_efficiency`: Cache hit rate (0-1)
- `execution_time_ms`: Total execution time
- `agents_executed`: List of agent types executed
- `hitl_escalations`: Number of HITL escalations
- `guardrail_violations`: Number of guardrail violations
- `evaluation_passed`: Whether evaluation passed
- `regeneration_count`: Number of regeneration attempts
- `metadata`: Additional metadata dictionary

## Backward Compatibility

The simple `Orchestrator` class is still available for basic agent coordination:

```python
from agents.orchestrator import Orchestrator

orchestrator = Orchestrator()
orchestrator.register_agent(revenue_agent)
results = await orchestrator.execute_parallel(['revenue'], context, session_id)
```

