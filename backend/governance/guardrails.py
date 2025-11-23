"""
Comprehensive Guardrails System for SaaS BI Agent.

Implements both Hard Guardrails (cannot be overridden) and Adaptive Guardrails
(risk-scored, may escalate to HITL) with learning capabilities.
"""

import re
import json
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from utils.logger import logger
from cache.cache_manager import CacheManager
from governance.hitl_manager import HITLManager


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
    PASS = "pass"
    WARN = "warn"


@dataclass
class Violation:
    """Guardrail violation details."""
    rule_name: str
    rule_type: str
    category: str
    severity: str
    details: Dict[str, Any]
    threshold: Optional[float] = None
    actual_value: Optional[float] = None
    reasoning: str = ""


@dataclass
class GuardrailResult:
    """Result of guardrail evaluation."""
    passed: bool
    violations: List[Violation] = field(default_factory=list)
    risk_score: float = 0.0
    action: str = "pass"  # pass, block, warn, escalate_hitl
    reasoning: str = ""
    hitl_request_id: Optional[str] = None


class GuardrailAgent:
    """
    Comprehensive Guardrails Agent for evaluating synthesized insights.
    
    Features:
    - Hard Guardrails: Cannot be overridden (PII, privacy, cost, hallucination)
    - Adaptive Guardrails: Risk-scored, may escalate to HITL
    - Rule Engine: Configurable rules with thresholds
    - Learning: Adapts thresholds based on HITL feedback
    - Comprehensive Logging: All evaluations logged to CacheManager
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Guardrail Agent.
        
        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager or CacheManager()
        self.hitl_manager = HITLManager(self.cache_manager)
        self.logger = logger.getChild('guardrail_agent')
        
        # Initialize rules
        self.hard_rules: Dict[str, Dict[str, Any]] = {}
        self.adaptive_rules: Dict[str, Dict[str, Any]] = {}
        
        # Load default rules
        self._initialize_default_rules()
        
        # Load adaptive rules from database
        self._load_adaptive_rules()
        
        self.logger.info("GuardrailAgent initialized")
    
    def _initialize_default_rules(self):
        """Initialize default hard and adaptive rules."""
        
        # HARD RULES (Cannot be overridden)
        self.hard_rules = {
            "pii_detection": {
                "name": "pii_detection",
                "category": "privacy",
                "detector": self._detect_pii,
                "action": "block",
                "severity": ViolationSeverity.CRITICAL
            },
            "data_privacy": {
                "name": "data_privacy",
                "category": "privacy",
                "detector": self._detect_customer_identifiers,
                "action": "block",
                "severity": ViolationSeverity.CRITICAL
            },
            "cost_limit": {
                "name": "cost_limit",
                "category": "cost",
                "threshold": 0.50,  # $0.50 per analysis
                "detector": self._check_cost_limit,
                "action": "block",
                "severity": ViolationSeverity.HIGH
            },
            "hallucination_detection": {
                "name": "hallucination_detection",
                "category": "quality",
                "detector": self._detect_hallucinations,
                "action": "block",
                "severity": ViolationSeverity.HIGH
            }
        }
        
        # ADAPTIVE RULES (Risk-scored, may escalate)
        self.adaptive_rules = {
            "data_quality": {
                "name": "data_quality",
                "category": "quality",
                "threshold": 0.70,  # Minimum data quality score
                "detector": self._check_data_quality,
                "action": "escalate_hitl",
                "severity": ViolationSeverity.MEDIUM,
                "adjustable": True
            },
            "confidence_threshold": {
                "name": "confidence_threshold",
                "category": "quality",
                "threshold": 0.70,  # Minimum confidence score
                "detector": self._check_confidence,
                "action": "warn",
                "severity": ViolationSeverity.MEDIUM,
                "adjustable": True
            },
            "anomaly_magnitude": {
                "name": "anomaly_magnitude",
                "category": "anomaly",
                "threshold": 3.0,  # Z-score threshold
                "detector": self._check_anomaly_magnitude,
                "action": "escalate_hitl",
                "severity": ViolationSeverity.HIGH,
                "adjustable": True
            },
            "contradiction_detection": {
                "name": "contradiction_detection",
                "category": "consistency",
                "threshold": 0.50,  # Contradiction score threshold
                "detector": self._detect_contradictions,
                "action": "escalate_hitl",
                "severity": ViolationSeverity.MEDIUM,
                "adjustable": True
            }
        }
        
        self.logger.info(f"Initialized {len(self.hard_rules)} hard rules and {len(self.adaptive_rules)} adaptive rules")
    
    def evaluate(
        self,
        insights: Dict[str, Any],
        session_id: str,
        trace_id: Optional[str] = None
    ) -> GuardrailResult:
        """
        Evaluate synthesized insights against all guardrail rules.
        
        Args:
            insights: Synthesizer output dictionary
            session_id: Session identifier
            trace_id: Optional trace ID
            
        Returns:
            GuardrailResult with evaluation results
        """
        violations: List[Violation] = []
        risk_score = 0.0
        action = "pass"
        reasoning_parts = []
        hitl_request_id = None
        
        # Step 1: Evaluate Hard Rules (must pass all)
        hard_violations = self._evaluate_hard_rules(insights, trace_id)
        violations.extend(hard_violations)
        
        if hard_violations:
            # Hard violations always block
            action = "block"
            reasoning_parts.append(f"Hard guardrail violations detected: {len(hard_violations)}")
            risk_score = 1.0
        
        # Step 2: Evaluate Adaptive Rules (if hard rules passed)
        if action != "block":
            adaptive_violations, adaptive_risk = self._evaluate_adaptive_rules(
                insights, trace_id
            )
            violations.extend(adaptive_violations)
            risk_score = max(risk_score, adaptive_risk)
            
            if adaptive_violations:
                # Determine action based on violations
                critical_violations = [v for v in adaptive_violations if v.severity == "critical"]
                high_violations = [v for v in adaptive_violations if v.severity == "high"]
                
                if critical_violations or len(high_violations) >= 2:
                    action = "escalate_hitl"
                    reasoning_parts.append(f"Critical violations require HITL escalation")
                elif high_violations:
                    action = "warn"
                    reasoning_parts.append(f"High severity violations detected: {len(high_violations)}")
                else:
                    action = "warn"
                    reasoning_parts.append(f"Adaptive rule violations detected: {len(adaptive_violations)}")
        
        # Step 3: Create HITL request if needed
        if action == "escalate_hitl":
            try:
                hitl_request_id = self.hitl_manager.create_request(
                    trace_id=trace_id or session_id,
                    agent_type="synthesizer",
                    reason=f"Guardrail violations require human review: {len(violations)} violations",
                    context={
                        "insights": insights,
                        "violations": [v.__dict__ for v in violations],
                        "risk_score": risk_score
                    },
                    proposed_action="Review and approve/modify insights"
                )
                reasoning_parts.append(f"HITL request created: {hitl_request_id}")
            except Exception as e:
                self.logger.error(f"Failed to create HITL request: {e}", exc_info=True)
                # Fallback to warn if HITL creation fails
                action = "warn"
                reasoning_parts.append("HITL escalation failed, downgrading to warning")
        
        # Step 4: Log all violations
        for violation in violations:
            self.cache_manager.log_guardrail_violation(
                trace_id=trace_id or session_id,
                agent_type="synthesizer",
                rule_type=violation.rule_type,
                rule_name=violation.rule_name,
                violation_severity=violation.severity,
                violation_details=violation.details,
                action_taken=action,
                human_review_required=(action == "escalate_hitl")
            )
        
        # Step 5: Build result
        passed = (action == "pass")
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "All guardrails passed"
        
        result = GuardrailResult(
            passed=passed,
            violations=violations,
            risk_score=risk_score,
            action=action,
            reasoning=reasoning,
            hitl_request_id=hitl_request_id
        )
        
        self.logger.info(
            f"Guardrail evaluation completed",
            extra={
                'session_id': session_id,
                'passed': passed,
                'action': action,
                'violations_count': len(violations),
                'risk_score': risk_score
            }
        )
        
        return result
    
    def _evaluate_hard_rules(
        self,
        insights: Dict[str, Any],
        trace_id: Optional[str]
    ) -> List[Violation]:
        """Evaluate hard rules (cannot be overridden)."""
        violations = []
        
        for rule_name, rule_config in self.hard_rules.items():
            try:
                detector = rule_config['detector']
                is_violation, details = detector(insights)
                
                if is_violation:
                    violation = Violation(
                        rule_name=rule_name,
                        rule_type="hard",
                        category=rule_config['category'],
                        severity=rule_config['severity'].value,
                        details=details,
                        reasoning=details.get('reasoning', f"Hard rule violation: {rule_name}")
                    )
                    violations.append(violation)
                    
                    self.logger.warning(
                        f"Hard guardrail violation: {rule_name}",
                        extra={'violation': violation.__dict__, 'trace_id': trace_id}
                    )
            except Exception as e:
                self.logger.error(
                    f"Error evaluating hard rule {rule_name}: {e}",
                    exc_info=True
                )
        
        return violations
    
    def _evaluate_adaptive_rules(
        self,
        insights: Dict[str, Any],
        trace_id: Optional[str]
    ) -> Tuple[List[Violation], float]:
        """Evaluate adaptive rules (risk-scored)."""
        violations = []
        max_risk = 0.0
        
        for rule_name, rule_config in self.adaptive_rules.items():
            try:
                # Get current threshold (may be adjusted from database)
                threshold = self._get_rule_threshold(rule_name, rule_config.get('threshold', 0.7))
                
                detector = rule_config['detector']
                is_violation, details = detector(insights, threshold)
                
                if is_violation:
                    actual_value = details.get('actual_value', 0)
                    risk = self._calculate_risk_score(
                        threshold=threshold,
                        actual_value=actual_value,
                        severity=rule_config['severity']
                    )
                    max_risk = max(max_risk, risk)
                    
                    violation = Violation(
                        rule_name=rule_name,
                        rule_type="adaptive",
                        category=rule_config['category'],
                        severity=rule_config['severity'].value,
                        details=details,
                        threshold=threshold,
                        actual_value=actual_value,
                        reasoning=details.get('reasoning', f"Adaptive rule violation: {rule_name}")
                    )
                    violations.append(violation)
                    
                    self.logger.warning(
                        f"Adaptive guardrail violation: {rule_name}",
                        extra={
                            'violation': violation.__dict__,
                            'risk_score': risk,
                            'trace_id': trace_id
                        }
                    )
            except Exception as e:
                self.logger.error(
                    f"Error evaluating adaptive rule {rule_name}: {e}",
                    exc_info=True
                )
        
        return violations, max_risk
    
    # =========================================================================
    # HARD RULE DETECTORS
    # =========================================================================
    
    def _detect_pii(self, insights: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Detect PII (SSN, credit cards, etc.) in insights."""
        text = json.dumps(insights)
        
        # SSN pattern (XXX-XX-XXXX)
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        # Credit card pattern (basic)
        cc_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        detected = []
        if re.search(ssn_pattern, text):
            detected.append("SSN")
        if re.search(cc_pattern, text):
            detected.append("Credit Card")
        if re.search(email_pattern, text):
            # Check if emails look like customer emails (not just generic domains)
            emails = re.findall(email_pattern, text)
            customer_emails = [e for e in emails if not any(
                domain in e.lower() for domain in ['example.com', 'test.com', 'company.com']
            )]
            if customer_emails:
                detected.append(f"Customer Email ({len(customer_emails)} found)")
        
        is_violation = len(detected) > 0
        
        return is_violation, {
            'detected_pii': detected,
            'reasoning': f"PII detected: {', '.join(detected)}" if detected else ""
        }
    
    def _detect_customer_identifiers(self, insights: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Detect customer-identifiable information."""
        text = json.dumps(insights).lower()
        
        # Common customer identifier patterns
        customer_patterns = [
            r'\bcustomer\s+id\s*:?\s*\d+',
            r'\buser\s+id\s*:?\s*\d+',
            r'\baccount\s+number\s*:?\s*\d+',
            r'\bphone\s*:?\s*[\d\s\-\(\)]+',
        ]
        
        detected = []
        for pattern in customer_patterns:
            if re.search(pattern, text):
                detected.append(pattern)
        
        is_violation = len(detected) > 0
        
        return is_violation, {
            'detected_identifiers': detected,
            'reasoning': f"Customer identifiers detected: {len(detected)} patterns found" if detected else ""
        }
    
    def _check_cost_limit(self, insights: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Check if projected Gemini cost exceeds threshold."""
        # Estimate cost based on token usage
        # Gemini pricing: ~$0.00025 per 1K input tokens, ~$0.0005 per 1K output tokens
        
        # Extract token counts from metadata if available
        metadata = insights.get('metadata', {})
        input_tokens = metadata.get('input_tokens', 0)
        output_tokens = metadata.get('output_tokens', 0)
        
        # Calculate estimated cost
        input_cost = (input_tokens / 1000) * 0.00025
        output_cost = (output_tokens / 1000) * 0.0005
        total_cost = input_cost + output_cost
        
        threshold = self.hard_rules['cost_limit']['threshold']
        is_violation = total_cost > threshold
        
        return is_violation, {
            'estimated_cost': total_cost,
            'threshold': threshold,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'reasoning': f"Estimated cost ${total_cost:.4f} exceeds threshold ${threshold:.2f}" if is_violation else ""
        }
    
    def _detect_hallucinations(self, insights: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Detect hallucinations by checking for data citations."""
        # Check if insights have data citations
        data_citations = insights.get('data_citations', [])
        analysis = insights.get('analysis', {})
        
        # Check key insights for citations
        key_insights = analysis.get('key_insights', [])
        correlations = analysis.get('correlations', [])
        recommendations = analysis.get('strategic_recommendations', [])
        
        # Count claims without citations
        uncited_claims = []
        
        # Check if insights reference data sources
        if len(key_insights) > 0 and len(data_citations) == 0:
            uncited_claims.append("Key insights lack data citations")
        
        # Check if correlations reference evidence
        for correlation in correlations:
            evidence = correlation.get('evidence', [])
            if len(evidence) == 0:
                uncited_claims.append(f"Correlation '{correlation.get('pattern', '')}' lacks evidence")
        
        # Check if recommendations are grounded
        for rec in recommendations:
            impact = rec.get('expected_impact', '')
            if 'data' not in impact.lower() and 'metric' not in impact.lower():
                uncited_claims.append(f"Recommendation '{rec.get('action', '')}' lacks data grounding")
        
        is_violation = len(uncited_claims) > len(key_insights) * 0.5  # More than 50% uncited
        
        return is_violation, {
            'uncited_claims': uncited_claims,
            'total_claims': len(key_insights) + len(correlations) + len(recommendations),
            'data_citations_count': len(data_citations),
            'reasoning': f"{len(uncited_claims)} claims lack data citations" if is_violation else ""
        }
    
    # =========================================================================
    # ADAPTIVE RULE DETECTORS
    # =========================================================================
    
    def _check_data_quality(
        self,
        insights: Dict[str, Any],
        threshold: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check data quality score."""
        # Extract data quality from agent results if available
        metadata = insights.get('metadata', {})
        analytical_results = metadata.get('analytical_results', {})
        
        quality_scores = []
        for agent_type, result in analytical_results.items():
            if isinstance(result, dict):
                try:
                    agent_data = json.loads(result.get('response', '{}'))
                    data_quality = agent_data.get('metadata', {}).get('data_quality', {})
                    completeness = data_quality.get('completeness_score', 1.0)
                    quality_scores.append(completeness)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 1.0
        is_violation = avg_quality < threshold
        
        return is_violation, {
            'data_quality_score': avg_quality,
            'threshold': threshold,
            'actual_value': avg_quality,
            'reasoning': f"Data quality score {avg_quality:.2f} below threshold {threshold:.2f}" if is_violation else ""
        }
    
    def _check_confidence(
        self,
        insights: Dict[str, Any],
        threshold: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check confidence score."""
        confidence = insights.get('confidence', 1.0)
        is_violation = confidence < threshold
        
        return is_violation, {
            'confidence_score': confidence,
            'threshold': threshold,
            'actual_value': confidence,
            'reasoning': f"Confidence score {confidence:.2f} below threshold {threshold:.2f}" if is_violation else ""
        }
    
    def _check_anomaly_magnitude(
        self,
        insights: Dict[str, Any],
        threshold: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if anomalies exceed expected variance."""
        analysis = insights.get('analysis', {})
        anomalies = analysis.get('anomalies', [])
        
        # Check for high-severity anomalies
        high_severity_anomalies = [
            a for a in anomalies
            if a.get('severity') == 'high' or a.get('z_score', 0) > threshold
        ]
        
        is_violation = len(high_severity_anomalies) > 0
        
        max_z_score = max([a.get('z_score', 0) for a in anomalies], default=0)
        
        return is_violation, {
            'anomaly_count': len(anomalies),
            'high_severity_count': len(high_severity_anomalies),
            'max_z_score': max_z_score,
            'threshold': threshold,
            'actual_value': max_z_score,
            'reasoning': f"{len(high_severity_anomalies)} high-severity anomalies detected" if is_violation else ""
        }
    
    def _detect_contradictions(
        self,
        insights: Dict[str, Any],
        threshold: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """Detect contradictions between agent signals."""
        analysis = insights.get('analysis', {})
        correlations = analysis.get('correlations', [])
        
        # Look for contradictory patterns
        contradictions = []
        
        # Check for conflicting trends
        revenue_analysis = insights.get('metadata', {}).get('analytical_results', {}).get('revenue', {})
        product_analysis = insights.get('metadata', {}).get('analytical_results', {}).get('product', {})
        
        if revenue_analysis and product_analysis:
            try:
                revenue_data = json.loads(revenue_analysis.get('response', '{}'))
                product_data = json.loads(product_analysis.get('response', '{}'))
                
                revenue_trend = revenue_data.get('analysis', {}).get('mrr_analysis', {}).get('trend', '')
                product_trend = product_data.get('analysis', {}).get('engagement_analysis', {}).get('trend', '')
                
                # Contradiction: Revenue growing but engagement declining
                if revenue_trend == 'accelerating' and product_trend == 'declining':
                    contradictions.append("Revenue accelerating but product engagement declining")
            except (json.JSONDecodeError, TypeError):
                pass
        
        contradiction_score = len(contradictions) / max(len(correlations), 1)
        is_violation = contradiction_score > threshold
        
        return is_violation, {
            'contradictions': contradictions,
            'contradiction_score': contradiction_score,
            'threshold': threshold,
            'actual_value': contradiction_score,
            'reasoning': f"{len(contradictions)} contradictions detected" if is_violation else ""
        }
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _calculate_risk_score(
        self,
        threshold: float,
        actual_value: float,
        severity: ViolationSeverity
    ) -> float:
        """Calculate risk score based on violation."""
        # Base risk from deviation
        deviation = abs(threshold - actual_value) / threshold if threshold > 0 else 0
        
        # Severity multiplier
        severity_multiplier = {
            ViolationSeverity.LOW: 0.3,
            ViolationSeverity.MEDIUM: 0.6,
            ViolationSeverity.HIGH: 0.9,
            ViolationSeverity.CRITICAL: 1.0
        }.get(severity, 0.5)
        
        risk = min(1.0, deviation * severity_multiplier)
        return risk
    
    def _get_rule_threshold(self, rule_name: str, default_threshold: float) -> float:
        """Get rule threshold, potentially adjusted from database."""
        # Check if rule exists in adaptive_rules table
        try:
            conn = self.cache_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT confidence_threshold 
                FROM adaptive_rules 
                WHERE rule_name = ? AND is_active = 1
            """, (rule_name,))
            
            row = cursor.fetchone()
            if row:
                return row['confidence_threshold']
        except Exception as e:
            self.logger.warning(f"Could not load threshold for {rule_name}: {e}")
        
        return default_threshold
    
    def _load_adaptive_rules(self):
        """Load adaptive rules from database."""
        try:
            conn = self.cache_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT rule_name, rule_definition, confidence_threshold
                FROM adaptive_rules
                WHERE is_active = 1
            """)
            
            for row in cursor.fetchall():
                rule_name = row['rule_name']
                if rule_name in self.adaptive_rules:
                    # Update threshold from database
                    self.adaptive_rules[rule_name]['threshold'] = row['confidence_threshold']
                    self.logger.info(f"Loaded adaptive rule threshold for {rule_name}: {row['confidence_threshold']}")
        except Exception as e:
            self.logger.warning(f"Could not load adaptive rules from database: {e}")
    
    def learn_from_hitl_feedback(self, rule_name: str, was_false_positive: bool):
        """
        Learn from HITL feedback to adjust adaptive rule thresholds.
        
        Args:
            rule_name: Name of the rule
            was_false_positive: Whether the violation was a false positive
        """
        if rule_name not in self.adaptive_rules:
            self.logger.warning(f"Rule {rule_name} not found for learning")
            return
        
        if not self.adaptive_rules[rule_name].get('adjustable', False):
            self.logger.info(f"Rule {rule_name} is not adjustable")
            return
        
        try:
            conn = self.cache_manager.connect()
            cursor = conn.cursor()
            
            # Get current threshold
            cursor.execute("""
                SELECT confidence_threshold, false_positive_count
                FROM adaptive_rules
                WHERE rule_name = ?
            """, (rule_name,))
            
            row = cursor.fetchone()
            if not row:
                return
            
            current_threshold = row['confidence_threshold']
            false_positive_count = row['false_positive_count'] + (1 if was_false_positive else 0)
            
            # Adjust threshold based on feedback
            if was_false_positive:
                # Increase threshold (make rule less strict)
                new_threshold = min(1.0, current_threshold + 0.05)
            else:
                # Decrease threshold (make rule more strict)
                new_threshold = max(0.0, current_threshold - 0.02)
            
            # Update database
            cursor.execute("""
                UPDATE adaptive_rules
                SET confidence_threshold = ?,
                    false_positive_count = ?,
                    updated_at = datetime('now')
                WHERE rule_name = ?
            """, (new_threshold, false_positive_count, rule_name))
            
            conn.commit()
            
            # Update in-memory rule
            self.adaptive_rules[rule_name]['threshold'] = new_threshold
            
            self.logger.info(
                f"Adjusted threshold for {rule_name}: {current_threshold:.2f} -> {new_threshold:.2f} "
                f"(false positive: {was_false_positive})"
            )
        except Exception as e:
            self.logger.error(f"Error learning from HITL feedback: {e}", exc_info=True)


# Backward compatibility: Keep simple Guardrails class
class Guardrails:
    """
    Simple guardrails system for backward compatibility.
    """
    
    def __init__(self):
        self.logger = logger.getChild('guardrails')
        self.rules: Dict[str, Dict[str, Any]] = {}
    
    def register_rule(self, rule_name: str, rule_type: RuleType, 
                      validator: callable, severity: ViolationSeverity = ViolationSeverity.MEDIUM):
        """Register a guardrail rule."""
        self.rules[rule_name] = {
            'rule_type': rule_type,
            'validator': validator,
            'severity': severity
        }
        self.logger.info(f"Registered guardrail rule: {rule_name}")
    
    def validate(self, agent_type: str, response: Dict[str, Any], 
                trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Validate agent response against all registered rules."""
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
