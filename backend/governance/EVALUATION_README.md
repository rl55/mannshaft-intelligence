# Evaluation Agent Implementation

## Overview

Comprehensive Evaluation Agent for quality control using Gemini meta-evaluation. Evaluates synthesized reports against multiple criteria and supports automatic regeneration if quality is below threshold.

## Evaluation Criteria

### 1. Requirement Fulfillment (0-1 score)
- **Checks**:
  - Does report address all requested analysis areas?
  - Are key metrics included (MRR, churn, engagement, support)?
  - Is executive summary present and clear (2-3 sentences)?
  - Are correlations, root causes, and recommendations provided?

### 2. Factual Grounding (0-1 score)
- **Checks**:
  - Are all claims backed by data citations?
  - Do numbers match source data?
  - Are calculations correct?
  - Are data sources clearly cited?

### 3. Quality & Coherence (0-1 score)
- **Checks**:
  - Is narrative logical and coherent?
  - Are recommendations actionable and specific?
  - Is language clear and professional?
  - Are insights well-structured and easy to follow?

### 4. Consistency Check (0-1 score)
- **Checks**:
  - Do different sections contradict each other?
  - Are agent outputs aligned (revenue/product/support)?
  - Do recommendations match findings?
  - Are correlations consistent with root causes?

### 5. Constraint Compliance (0-1 score)
- **Checks**:
  - No PII or sensitive data present?
  - Report structure follows expected format?
  - All required fields present?
  - Guardrails passed (assumed yes if report exists)?

## Evaluation Method

Uses Gemini as meta-evaluator with structured prompt:

```python
evaluation_prompt = f"""
You are a quality assurance analyst evaluating a SaaS business report.

REPORT TO EVALUATE:
{synthesized_report}

SOURCE DATA SUMMARY:
{original_data_summary}

EVALUATION CRITERIA:
1. Requirement Fulfillment: ...
2. Factual Grounding: ...
3. Quality & Coherence: ...
4. Consistency: ...
5. Constraint Compliance: ...

For each criterion, provide:
- Score (0-1)
- Reasoning (1-2 sentences)
- Specific issues if score < 0.8

OUTPUT FORMAT: JSON
{{
  "requirement_score": 0.95,
  "requirement_reasoning": "...",
  "grounding_score": 0.88,
  ...
  "overall_score": 0.91,
  "pass": true,
  "issues": [...],
  "regeneration_needed": false
}}
"""
```

## Regeneration Logic

### Automatic Regeneration

- **Trigger**: Overall score < regeneration_threshold (default: 0.75)
- **Max Attempts**: 2 regenerations (configurable)
- **Feedback**: Specific feedback on what to improve
- **Tracking**: Regeneration count tracked in evaluation cache

### Regeneration Flow

```
1. Evaluate report
   ↓
2. Check if score < threshold
   ↓
3. If yes and attempts < max:
   ├── Generate feedback
   ├── Call regeneration callback
   ├── Increment count
   └── Re-evaluate
   ↓
4. Return final result
```

### Feedback Generation

Feedback includes:
- Low-scoring criteria with reasoning
- Specific issues to address
- Actionable improvement suggestions

## Caching

### Evaluation Cache

- **Key**: Report hash (deterministic from content)
- **TTL**: 7 days (evaluations are deterministic)
- **Storage**: Uses `prompt_cache` table with model="evaluator"
- **Benefits**: Avoids re-evaluating identical reports

### Cache Key Generation

```python
report_hash = hash({
    'executive_summary': ...,
    'correlations_count': ...,
    'recommendations_count': ...,
    'key_metrics': ...
})
```

## Interface

### Basic Evaluation

```python
from governance.evaluation import Evaluator

evaluator = Evaluator(cache_manager)

result = await evaluator.evaluate(
    agent_type='synthesizer',
    response=synthesizer_output,
    trace_id='trace-123',
    original_data_summary=data_summary,
    requested_analysis_areas=['revenue', 'product', 'support']
)
```

### Evaluation with Regeneration

```python
async def regenerate_callback(feedback: str) -> Dict[str, Any]:
    """Regenerate report with feedback."""
    # Use feedback to improve synthesis
    return new_synthesizer_output

result, regeneration_count = await evaluator.evaluate_with_regeneration(
    agent_type='synthesizer',
    response=synthesizer_output,
    trace_id='trace-123',
    original_data_summary=data_summary,
    requested_analysis_areas=['revenue', 'product', 'support'],
    regeneration_callback=regenerate_callback
)
```

## Output Format

```python
{
    'factual_grounding_score': 0.88,
    'relevance_score': 0.95,
    'completeness_score': 0.95,
    'coherence_score': 0.92,
    'data_citations_present': True,
    'confidence_calibrated': True,
    'anomalies_flagged': False,
    'overall_quality': 'excellent',  # excellent|good|acceptable|poor
    'requires_review': False,
    'review_reason': None,
    'evaluation_details': {
        'requirement_score': 0.95,
        'grounding_score': 0.88,
        'quality_score': 0.92,
        'consistency_score': 0.90,
        'constraint_score': 1.0,
        'overall_score': 0.93,
        'issues': []
    }
}
```

## Overall Score Calculation

Weighted average of all criteria:

```python
overall_score = (
    requirement_score * 0.20 +
    grounding_score * 0.25 +
    quality_score * 0.20 +
    consistency_score * 0.20 +
    constraint_score * 0.15
)
```

## Quality Labels

- **excellent**: score >= 0.9
- **good**: score >= 0.8
- **acceptable**: score >= 0.7
- **poor**: score < 0.7

## Integration with Orchestrator

The orchestrator automatically:
1. Evaluates synthesized output
2. Checks if regeneration needed
3. Regenerates if score < threshold
4. Re-evaluates regenerated output
5. Returns final result with evaluation details

## Configuration

```yaml
evaluation:
  pass_threshold: 0.75  # Minimum score to pass
  regeneration_threshold: 0.75  # Score below which regeneration triggered
  max_regenerations: 2  # Maximum regeneration attempts
  cache_ttl_hours: 168  # 7 days evaluation cache TTL
```

## Error Handling

- **Gemini Failures**: Falls back to heuristic evaluation
- **JSON Parse Errors**: Uses heuristic evaluation
- **Missing Data**: Gracefully handles missing context
- **All Errors**: Logged with full context

## Heuristic Fallback

When Gemini evaluation fails, uses heuristic evaluation:
- Checks for required sections
- Counts data citations
- Validates structure
- Provides basic scores

## Database Integration

All evaluations recorded in `evaluations` table:
- Trace ID
- Agent type
- All scores (factual_grounding, relevance, completeness, coherence)
- Flags (citations, confidence, anomalies)
- Overall quality
- Review requirements

## Performance

- **Evaluation Time**: ~2-3s (Gemini API call)
- **Cache Hit**: <100ms
- **Regeneration**: Adds ~2-3s per attempt
- **Target**: Complete evaluation <5s (cache miss)

## Testing

```python
import pytest
from governance.evaluation import Evaluator

@pytest.mark.asyncio
async def test_evaluation():
    evaluator = Evaluator()
    
    result = await evaluator.evaluate(
        agent_type='synthesizer',
        response={
            'executive_summary': 'Test summary',
            'correlations': [],
            'strategic_recommendations': []
        },
        trace_id='test-trace'
    )
    
    assert 'overall_quality' in result
    assert result['factual_grounding_score'] >= 0
    assert result['factual_grounding_score'] <= 1
```

## Dependencies

- `google-generativeai`: Gemini API for meta-evaluation
- `cache.cache_manager`: Caching and database logging
- `utils.config`: Configuration management

