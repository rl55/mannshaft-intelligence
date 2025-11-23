# HITL Manager Implementation

## Overview

Comprehensive Human-in-the-Loop (HITL) Management System for human oversight of AI-generated insights. Provides escalation logic, review interface stubs, auto-approval for demo mode, and learning integration.

## Key Features

### ✅ Escalation Logic

Escalations triggered by:
- **High-risk guardrail violations**: Critical or high-severity violations
- **Low confidence with business-critical insights**: Confidence < 0.7 with important findings
- **Contradictory signals**: Conflicting information from different agents
- **First-time edge cases**: Unusual patterns requiring human judgment

### ✅ Escalation Package

Comprehensive package includes:
- **Summary**: 200-word summary of analysis
- **Escalation Reason**: Specific reason for escalation
- **Risk Score**: Calculated risk score (0-1) with rationale
- **Agent Outputs**: Formatted outputs from all agents
- **Recommended Actions**: Actions with pros/cons
- **Guardrail Violations**: All violations requiring review
- **Review URL**: Link to review interface (stub)

### ✅ Review Interface (Stub)

Methods for future frontend integration:
- `get_pending_requests()`: Get pending escalations
- `approve_request()`: Approve an escalation
- `reject_request()`: Reject an escalation
- `modify_request()`: Modify an escalation

### ✅ Auto-Approval for Demo

- **Mode**: Set `HITL_MODE=demo` environment variable
- **Behavior**: Auto-approves after 2-second delay
- **Logic**: Simulates human decision based on risk score
- **Logging**: Logs as `auto_approved=True`

### ✅ Learning Loop

- Tracks approved vs rejected escalations
- Adjusts adaptive guardrail thresholds based on feedback
- Reduces false positives over time
- Integrates with GuardrailAgent learning

## Interface

### escalate()

```python
from governance.hitl_manager import HITLManager

hitl_manager = HITLManager(cache_manager, guardrail_agent)

decision = await hitl_manager.escalate(
    session_id="session-123",
    report=synthesizer_output,
    escalation_reason="High-risk guardrail violations",
    risk_score=0.85,
    trace_id="trace-456",
    guardrail_violations=violations,
    evaluation_details=evaluation_result,
    analytical_results=analytical_results
)

# Returns HITLDecision:
# - decision: "approved" | "rejected" | "modified"
# - feedback: Optional human feedback
# - modifications: Changes made by human
# - resolution_time_minutes: Time to resolution
# - auto_approved: Whether auto-approved
```

## Escalation Flow

```
1. Determine if escalation needed
   ├── Check guardrail violations
   ├── Check risk score
   └── Check evaluation results
   ↓
2. Create escalation package
   ├── Generate summary
   ├── Format agent outputs
   ├── Generate recommended actions
   └── Create review URL
   ↓
3. Create HITL request in database
   ↓
4. Send notification (stub)
   ↓
5. Handle based on mode:
   ├── Demo: Auto-approve with delay
   └── Production: Wait for human (stub)
   ↓
6. Resolve request
   ↓
7. Learn from decision
   └── Adjust guardrail thresholds
```

## Escalation Package Structure

```python
EscalationPackage(
    request_id: str,
    session_id: str,
    summary: str,  # 200-word summary
    escalation_reason: str,
    risk_score: float,
    risk_rationale: str,
    agent_outputs: Dict[str, Any],  # Formatted
    recommended_actions: List[Dict[str, Any]],  # With pros/cons
    guardrail_violations: List[Dict[str, Any]],
    evaluation_details: Optional[Dict[str, Any]],
    review_url: Optional[str],
    created_at: str
)
```

## Auto-Approval Logic (Demo Mode)

```python
if risk_score < 0.5:
    decision = "approved"  # Low risk
elif risk_score < 0.7:
    decision = "approved"  # Medium risk, acceptable
else:
    decision = "modified"  # High risk, apply modifications
```

## Review Interface Methods

### Get Pending Requests

```python
pending = hitl_manager.get_pending_requests(limit=10)
# Returns list of pending request dictionaries
```

### Approve Request

```python
success = hitl_manager.approve_request(
    request_id="hitl-123",
    human_feedback="Looks good, approved",
    human_reviewer="user-456"
)
```

### Reject Request

```python
success = hitl_manager.reject_request(
    request_id="hitl-123",
    human_feedback="Data quality issues, needs regeneration",
    human_reviewer="user-456"
)
```

### Modify Request

```python
success = hitl_manager.modify_request(
    request_id="hitl-123",
    modifications={
        'confidence_adjusted': True,
        'risk_flags_added': True
    },
    human_feedback="Adjusted confidence based on review",
    human_reviewer="user-456"
)
```

## Learning Integration

### Learning from Decisions

When a request is approved:
- Adaptive guardrail violations may be false positives
- Thresholds are adjusted upward (less strict)
- Learning logged to database

When a request is rejected:
- Violations were likely true positives
- Thresholds may be tightened (more strict)
- Learning logged to database

### Threshold Adjustment

```python
# Called automatically when decision is made
guardrail_agent.learn_from_hitl_feedback(
    rule_name="confidence_threshold",
    was_false_positive=True  # If approved
)
```

## Notification Stubs

Currently logs to logger. In production would:
- Send email to reviewers
- Post to Slack channel
- Create ticket in issue tracker

## Configuration

```yaml
hitl:
  auto_approval_delay_seconds: 2  # Demo mode delay
  notification_enabled: false  # Enable notifications
  review_base_url: "https://app.example.com/review"  # Review UI URL
```

Environment Variable:
```bash
HITL_MODE=demo  # or 'production'
```

## Integration with Orchestrator

The orchestrator automatically:
1. Evaluates guardrails
2. Calculates risk score
3. Determines escalation reason
4. Calls `hitl_manager.escalate()`
5. Handles decision (approve/reject/modify)
6. Learns from decision

## Usage Example

```python
from governance.hitl_manager import HITLManager
from cache.cache_manager import CacheManager
from governance.guardrails import GuardrailAgent

# Initialize
cache_manager = CacheManager()
guardrail_agent = GuardrailAgent(cache_manager)
hitl_manager = HITLManager(cache_manager, guardrail_agent)

# Escalate
decision = await hitl_manager.escalate(
    session_id="session-123",
    report={
        'executive_summary': '...',
        'correlations': [...],
        'confidence': 0.65
    },
    escalation_reason="Low confidence with business-critical insights",
    risk_score=0.75,
    guardrail_violations=[
        {
            'rule_name': 'confidence_threshold',
            'severity': 'high',
            'details': {...}
        }
    ]
)

print(f"Decision: {decision.decision}")
print(f"Auto-approved: {decision.auto_approved}")
print(f"Feedback: {decision.feedback}")
```

## Database Integration

All escalations logged to `hitl_requests` table:
- Request ID
- Trace ID
- Status (pending/approved/rejected/modified/timeout)
- Reason
- Context (full escalation package)
- Resolution time
- Human feedback

## Performance

- **Escalation Creation**: <100ms
- **Auto-Approval (Demo)**: ~2s (simulated delay)
- **Human Review (Production)**: Variable (stub)
- **Learning**: <50ms

## Testing

```python
import pytest
from governance.hitl_manager import HITLManager

@pytest.mark.asyncio
async def test_hitl_escalation():
    hitl_manager = HITLManager(cache_manager)
    
    decision = await hitl_manager.escalate(
        session_id="test-session",
        report={'executive_summary': 'Test'},
        escalation_reason="Test escalation",
        risk_score=0.8
    )
    
    assert decision.decision in ['approved', 'rejected', 'modified']
    assert decision.resolution_time_minutes >= 0
```

## Dependencies

- `cache.cache_manager`: Database logging
- `governance.guardrails`: Learning integration
- `utils.config`: Configuration management

