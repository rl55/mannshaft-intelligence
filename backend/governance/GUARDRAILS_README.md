# Guardrails System Implementation

## Overview

Comprehensive Guardrails System implementing both Hard Guardrails (cannot be overridden) and Adaptive Guardrails (risk-scored, may escalate to HITL) with learning capabilities.

## Architecture

```
GuardrailAgent
├── Hard Rules (Block)
│   ├── PII Detection
│   ├── Data Privacy
│   ├── Cost Limits
│   └── Hallucination Detection
└── Adaptive Rules (Risk-Scored)
    ├── Data Quality
    ├── Confidence Threshold
    ├── Anomaly Magnitude
    └── Contradiction Detection
```

## Hard Guardrails

### 1. PII Detection
- **Purpose**: Block any output containing PII
- **Detection**: Regex patterns for SSN, credit cards, emails
- **Action**: Block
- **Severity**: Critical

**Patterns Detected**:
- SSN: `XXX-XX-XXXX`
- Credit Cards: `XXXX XXXX XXXX XXXX`
- Customer Emails: Excludes generic domains

### 2. Data Privacy
- **Purpose**: Ensure no customer-identifiable information
- **Detection**: Customer ID, User ID, Account Number, Phone patterns
- **Action**: Block
- **Severity**: Critical

### 3. Cost Limits
- **Purpose**: Reject if projected Gemini cost exceeds threshold
- **Threshold**: $0.50 per analysis (configurable)
- **Calculation**: Based on input/output token counts
- **Action**: Block
- **Severity**: High

**Cost Calculation**:
- Input: ~$0.00025 per 1K tokens
- Output: ~$0.0005 per 1K tokens

### 4. Hallucination Detection
- **Purpose**: Verify all claims cite source data
- **Detection**: Checks for data citations in insights
- **Action**: Block if >50% claims lack citations
- **Severity**: High

**Checks**:
- Key insights have data citations
- Correlations have evidence
- Recommendations are data-grounded

## Adaptive Guardrails

### 1. Data Quality
- **Purpose**: Flag if input data is incomplete/stale
- **Threshold**: 0.70 minimum data quality score
- **Action**: Escalate to HITL
- **Severity**: Medium
- **Adjustable**: Yes

### 2. Confidence Threshold
- **Purpose**: Warn if agent confidence < threshold
- **Threshold**: 0.70 minimum confidence
- **Action**: Warn
- **Severity**: Medium
- **Adjustable**: Yes

### 3. Anomaly Magnitude
- **Purpose**: Escalate if changes exceed expected variance
- **Threshold**: Z-score > 3.0
- **Action**: Escalate to HITL
- **Severity**: High
- **Adjustable**: Yes

### 4. Contradiction Detection
- **Purpose**: Flag if agents give conflicting signals
- **Threshold**: Contradiction score > 0.50
- **Action**: Escalate to HITL
- **Severity**: Medium
- **Adjustable**: Yes

**Detects**:
- Revenue growing but engagement declining
- Conflicting trends between agents
- Inconsistent recommendations

## Interface

### GuardrailAgent.evaluate()

```python
from governance.guardrails import GuardrailAgent

guardrail_agent = GuardrailAgent(cache_manager)

result = guardrail_agent.evaluate(
    insights=synthesizer_output,
    session_id="session-123",
    trace_id="trace-456"
)

# Result contains:
# - passed: bool
# - violations: List[Violation]
# - risk_score: float (0-1)
# - action: "pass" | "block" | "warn" | "escalate_hitl"
# - reasoning: str
# - hitl_request_id: Optional[str]
```

### GuardrailResult

```python
@dataclass
class GuardrailResult:
    passed: bool
    violations: List[Violation]
    risk_score: float  # 0-1
    action: str  # pass, block, warn, escalate_hitl
    reasoning: str
    hitl_request_id: Optional[str]
```

### Violation

```python
@dataclass
class Violation:
    rule_name: str
    rule_type: str  # hard or adaptive
    category: str
    severity: str  # low, medium, high, critical
    details: Dict[str, Any]
    threshold: Optional[float]
    actual_value: Optional[float]
    reasoning: str
```

## Rule Engine

### Rule Structure

```python
{
    "name": "rule_name",
    "category": "privacy|quality|cost|anomaly|consistency",
    "threshold": 0.70,  # For adaptive rules
    "detector": callable,  # Function that returns (is_violation, details)
    "action": "block|warn|escalate_hitl",
    "severity": ViolationSeverity,
    "adjustable": True  # For adaptive rules
}
```

### Rule Storage

- **Hard Rules**: Defined in code (cannot be overridden)
- **Adaptive Rules**: Stored in `adaptive_rules` table
- **Thresholds**: Can be adjusted based on HITL feedback
- **Learning**: Tracks false positives for threshold adjustment

## Adaptive Learning

### Learning from HITL Feedback

```python
guardrail_agent.learn_from_hitl_feedback(
    rule_name="confidence_threshold",
    was_false_positive=True
)
```

**Learning Logic**:
- **False Positive**: Increase threshold (make rule less strict) by +0.05
- **True Positive**: Decrease threshold (make rule more strict) by -0.02
- **Threshold Bounds**: 0.0 to 1.0

### Database Integration

Rules stored in `adaptive_rules` table:
- `rule_name`: Unique identifier
- `rule_definition`: JSON rule specification
- `confidence_threshold`: Current threshold (adjustable)
- `trigger_count`: Number of times rule triggered
- `false_positive_count`: Number of false positives
- `is_active`: Whether rule is active

## Evaluation Flow

```
1. Evaluate Hard Rules
   ├── If violation → BLOCK (risk_score = 1.0)
   └── If pass → Continue
   
2. Evaluate Adaptive Rules
   ├── Calculate risk scores
   ├── Collect violations
   └── Determine action:
       ├── Critical/High violations → ESCALATE_HITL
       ├── Medium violations → WARN
       └── Low violations → WARN
       
3. Create HITL Request (if needed)
   └── Log request ID
   
4. Log All Violations
   └── Store in guardrail_violations table
   
5. Return GuardrailResult
```

## Action Determination

| Violations | Action |
|------------|--------|
| Hard rule violation | `block` |
| Critical adaptive violation | `escalate_hitl` |
| 2+ High adaptive violations | `escalate_hitl` |
| 1 High adaptive violation | `warn` |
| Medium/Low violations | `warn` |
| No violations | `pass` |

## Risk Score Calculation

```python
risk_score = min(1.0, deviation * severity_multiplier)

where:
- deviation = abs(threshold - actual_value) / threshold
- severity_multiplier:
  - LOW: 0.3
  - MEDIUM: 0.6
  - HIGH: 0.9
  - CRITICAL: 1.0
```

## Integration with Orchestrator

The orchestrator automatically applies guardrails:

```python
from agents.orchestrator import OrchestratorAgent
from governance.guardrails import GuardrailAgent

orchestrator = OrchestratorAgent()
result = await orchestrator.analyze_week(...)

# Guardrails are applied in orchestrator._apply_guardrails()
```

## Logging

All guardrail evaluations are logged to:
- **guardrail_violations** table: All violations
- **hitl_requests** table: HITL escalations
- **adaptive_rules** table: Threshold adjustments

## Usage Example

```python
from governance.guardrails import GuardrailAgent
from cache.cache_manager import CacheManager

# Initialize
cache_manager = CacheManager()
guardrail_agent = GuardrailAgent(cache_manager)

# Evaluate synthesized insights
result = guardrail_agent.evaluate(
    insights={
        'executive_summary': '...',
        'correlations': [...],
        'confidence': 0.85,
        ...
    },
    session_id='session-123',
    trace_id='trace-456'
)

# Check result
if not result.passed:
    if result.action == 'block':
        print(f"BLOCKED: {result.reasoning}")
    elif result.action == 'escalate_hitl':
        print(f"ESCALATED: HITL request {result.hitl_request_id}")
    elif result.action == 'warn':
        print(f"WARNING: {result.reasoning}")
    
    for violation in result.violations:
        print(f"  - {violation.rule_name}: {violation.reasoning}")
```

## Configuration

Rules can be configured via:
1. **Code**: Hard rules defined in `_initialize_default_rules()`
2. **Database**: Adaptive rules stored in `adaptive_rules` table
3. **Learning**: Thresholds adjusted based on HITL feedback

## Testing

```python
import pytest
from governance.guardrails import GuardrailAgent

@pytest.fixture
def guardrail_agent():
    return GuardrailAgent()

def test_pii_detection(guardrail_agent):
    insights = {
        'executive_summary': 'Customer SSN: 123-45-6789',
        'confidence': 0.9
    }
    
    result = guardrail_agent.evaluate(insights, 'test-session')
    assert not result.passed
    assert result.action == 'block'
    assert any(v.rule_name == 'pii_detection' for v in result.violations)

def test_confidence_threshold(guardrail_agent):
    insights = {
        'confidence': 0.5,  # Below threshold
        'executive_summary': '...'
    }
    
    result = guardrail_agent.evaluate(insights, 'test-session')
    assert result.action == 'warn'
    assert any(v.rule_name == 'confidence_threshold' for v in result.violations)
```

## Dependencies

- `cache.cache_manager`: Logging violations and HITL requests
- `governance.hitl_manager`: Creating HITL escalations
- `re`: Regex pattern matching for PII detection

## Performance

- **Evaluation Time**: <100ms for typical insights
- **Hard Rules**: Evaluated first (fastest)
- **Adaptive Rules**: Evaluated only if hard rules pass
- **Database Queries**: Cached where possible

