"""
Guardrails for agent responses and behavior.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

from utils.logger import logger


class RuleType(Enum):
    """Types of guardrail rules."""
    HARD = "hard"
    ADAPTIVE = "adaptive"


class ViolationSeverity(Enum):
    """Severity levels for violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionTaken(Enum):
    """Actions taken when violations occur."""
    BLOCKED = "blocked"
    ESCALATED = "escalated"
    MODIFIED = "modified"
    ALLOWED = "allowed"


class Guardrails:
    """
    Guardrails system for validating and controlling agent behavior.
    """
    
    def __init__(self):
        self.logger = logger.getChild('guardrails')
        self.rules: Dict[str, Dict[str, Any]] = {}
    
    def register_rule(self, rule_name: str, rule_type: RuleType, 
                      validator: callable, severity: ViolationSeverity = ViolationSeverity.MEDIUM):
        """
        Register a guardrail rule.
        
        Args:
            rule_name: Name of the rule
            rule_type: Type of rule (hard or adaptive)
            validator: Function that validates and returns (is_violation, details)
            severity: Severity level if violated
        """
        self.rules[rule_name] = {
            'rule_type': rule_type,
            'validator': validator,
            'severity': severity
        }
        self.logger.info(f"Registered guardrail rule: {rule_name}")
    
    def validate(self, agent_type: str, response: Dict[str, Any], 
                trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Validate agent response against all registered rules.
        
        Args:
            agent_type: Type of agent
            response: Agent response to validate
            trace_id: Optional trace ID
            
        Returns:
            List of violations found
        """
        violations = []
        
        for rule_name, rule_config in self.rules.items():
            try:
                is_violation, details = rule_config['validator'](response)
                
                if is_violation:
                    violation = {
                        'rule_name': rule_name,
                        'rule_type': rule_config['rule_type'].value,
                        'severity': rule_config['severity'].value,
                        'details': details,
                        'agent_type': agent_type,
                        'trace_id': trace_id
                    }
                    violations.append(violation)
                    
                    self.logger.warning(
                        f"Guardrail violation: {rule_name}",
                        extra=violation
                    )
            except Exception as e:
                self.logger.error(
                    f"Error validating rule {rule_name}",
                    extra={'error': str(e), 'rule_name': rule_name},
                    exc_info=True
                )
        
        return violations

