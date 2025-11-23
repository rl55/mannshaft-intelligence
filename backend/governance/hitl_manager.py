"""
Comprehensive Human-in-the-Loop (HITL) Management System.

Features:
- Escalation logic for high-risk scenarios
- Escalation package creation
- Review interface (stub for future frontend)
- Auto-approval for demo mode
- Learning loop integration
- Notification stubs
"""

import json
import os
import asyncio
import time
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from utils.logger import logger
from utils.config import config
from cache.cache_manager import CacheManager

if TYPE_CHECKING:
    from governance.guardrails import GuardrailAgent


class HITLStatus(Enum):
    """Status of HITL requests."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    TIMEOUT = "timeout"


class EscalationReason(Enum):
    """Reasons for escalation."""
    GUARDRAIL_VIOLATION = "guardrail_violation"
    LOW_CONFIDENCE = "low_confidence"
    CONTRADICTORY_SIGNALS = "contradictory_signals"
    EDGE_CASE = "edge_case"
    BUSINESS_CRITICAL = "business_critical"
    ANOMALY_DETECTED = "anomaly_detected"


@dataclass
class EscalationPackage:
    """Escalation package for human review."""
    request_id: str
    session_id: str
    summary: str  # 200-word summary
    escalation_reason: str
    risk_score: float
    risk_rationale: str
    agent_outputs: Dict[str, Any]  # Formatted agent outputs
    recommended_actions: List[Dict[str, Any]]  # With pros/cons
    guardrail_violations: List[Dict[str, Any]]
    evaluation_details: Optional[Dict[str, Any]] = None
    review_url: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class HITLDecision:
    """Human decision on HITL escalation."""
    decision: str  # "approved" | "rejected" | "modified"
    feedback: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None
    resolution_time_minutes: int = 0
    auto_approved: bool = False
    human_reviewer: Optional[str] = None


class HITLManager:
    """
    Comprehensive HITL Manager for human oversight.
    
    Features:
    - Escalation logic for high-risk scenarios
    - Escalation package creation
    - Review interface (stub)
    - Auto-approval for demo mode
    - Learning loop integration
    - Notification stubs
    """
    
    def __init__(self, cache_manager: CacheManager, guardrail_agent: Optional['GuardrailAgent'] = None):
        """
        Initialize HITL Manager.
        
        Args:
            cache_manager: Cache manager instance
            guardrail_agent: Optional guardrail agent for learning
        """
        self.cache_manager = cache_manager
        self.guardrail_agent = guardrail_agent
        self.logger = logger.getChild('hitl_manager')
        
        # Configuration
        self.hitl_mode = os.getenv('HITL_MODE', 'production')  # 'demo' or 'production'
        self.auto_approval_delay_seconds = config.get('hitl.auto_approval_delay_seconds', 2)
        self.notification_enabled = config.get('hitl.notification_enabled', False)
        
        self.logger.info(f"HITLManager initialized in {self.hitl_mode} mode")
    
    async def escalate(
        self,
        session_id: str,
        report: Dict[str, Any],
        escalation_reason: str,
        risk_score: float,
        trace_id: Optional[str] = None,
        guardrail_violations: Optional[List[Dict[str, Any]]] = None,
        evaluation_details: Optional[Dict[str, Any]] = None,
        analytical_results: Optional[Dict[str, Any]] = None
    ) -> HITLDecision:
        """
        Escalate to human for review.
        
        In production: Queue for human, wait for decision
        In demo mode: Auto-approve with simulated delay
        
        Args:
            session_id: Session identifier
            report: Synthesizer output dictionary
            escalation_reason: Reason for escalation
            risk_score: Risk score (0-1)
            trace_id: Optional trace ID
            guardrail_violations: Optional guardrail violations
            evaluation_details: Optional evaluation details
            analytical_results: Optional original agent results
            
        Returns:
            HITLDecision with decision, feedback, modifications, etc.
        """
        start_time = time.time()
        
        try:
            # Step 1: Create escalation package
            escalation_package = self._create_escalation_package(
                session_id=session_id,
                report=report,
                escalation_reason=escalation_reason,
                risk_score=risk_score,
                trace_id=trace_id,
                guardrail_violations=guardrail_violations or [],
                evaluation_details=evaluation_details,
                analytical_results=analytical_results
            )
            
            # Step 2: Create HITL request in database
            request_id = self.cache_manager.create_hitl_request(
                trace_id=trace_id or session_id,
                agent_type='synthesizer',
                reason=escalation_reason,
                context=escalation_package.__dict__,
                proposed_action=escalation_package.recommended_actions[0].get('action', '') if escalation_package.recommended_actions else None
            )
            
            escalation_package.request_id = request_id
            
            # Step 3: Send notification (stub)
            await self._send_notification(escalation_package)
            
            # Step 4: Handle based on mode
            if self.hitl_mode == 'demo':
                # Auto-approve with simulated delay
                decision = await self._auto_approve_demo(escalation_package, risk_score)
            else:
                # Production: Wait for human decision (stub - would integrate with review UI)
                decision = await self._wait_for_human_decision(escalation_package)
            
            # Step 5: Resolve request
            resolution_time_minutes = int((time.time() - start_time) / 60)
            decision.resolution_time_minutes = resolution_time_minutes
            
            self.resolve_request(
                request_id=request_id,
                status=HITLStatus(decision.decision.upper()),
                human_decision=decision.decision,
                human_feedback=decision.feedback
            )
            
            # Step 6: Learn from decision
            if self.guardrail_agent and decision.decision in ['approved', 'rejected']:
                self._learn_from_decision(escalation_package, decision)
            
            self.logger.info(
                f"HITL escalation resolved: {request_id}",
                extra={
                    'request_id': request_id,
                    'decision': decision.decision,
                    'auto_approved': decision.auto_approved,
                    'resolution_time_minutes': resolution_time_minutes
                }
            )
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error in HITL escalation: {e}", exc_info=True)
            # Return default approval in error case
            return HITLDecision(
                decision="approved",
                feedback=f"Error in escalation: {str(e)}",
                auto_approved=True
            )
    
    def _create_escalation_package(
        self,
        session_id: str,
        report: Dict[str, Any],
        escalation_reason: str,
        risk_score: float,
        trace_id: Optional[str],
        guardrail_violations: List[Dict[str, Any]],
        evaluation_details: Optional[Dict[str, Any]],
        analytical_results: Optional[Dict[str, Any]]
    ) -> EscalationPackage:
        """Create comprehensive escalation package."""
        
        # Parse report if it's a JSON string
        if isinstance(report, dict) and 'response' in report:
            try:
                report_data = json.loads(report['response']) if isinstance(report['response'], str) else report['response']
            except (json.JSONDecodeError, TypeError):
                report_data = report
        else:
            report_data = report
        
        # Generate 200-word summary
        summary = self._generate_summary(report_data, 200)
        
        # Generate risk rationale
        risk_rationale = self._generate_risk_rationale(
            escalation_reason, risk_score, guardrail_violations, evaluation_details
        )
        
        # Format agent outputs
        agent_outputs = self._format_agent_outputs(analytical_results or {})
        
        # Generate recommended actions with pros/cons
        recommended_actions = self._generate_recommended_actions(
            report_data, guardrail_violations, risk_score
        )
        
        # Generate review URL (stub)
        review_url = self._generate_review_url(session_id)
        
        return EscalationPackage(
            request_id="",  # Will be set after creation
            session_id=session_id,
            summary=summary,
            escalation_reason=escalation_reason,
            risk_score=risk_score,
            risk_rationale=risk_rationale,
            agent_outputs=agent_outputs,
            recommended_actions=recommended_actions,
            guardrail_violations=guardrail_violations,
            evaluation_details=evaluation_details,
            review_url=review_url
        )
    
    def _generate_summary(self, report_data: Dict[str, Any], max_words: int = 200) -> str:
        """Generate concise summary of analysis."""
        executive_summary = report_data.get('executive_summary', '')
        
        # Extract key metrics
        key_metrics = report_data.get('key_metrics_summary', {})
        metrics_text = ""
        if key_metrics:
            revenue = key_metrics.get('revenue', {})
            product = key_metrics.get('product', {})
            support = key_metrics.get('support', {})
            
            metrics_parts = []
            if revenue:
                metrics_parts.append(f"MRR: ${revenue.get('current_mrr', 0):,.0f}")
            if product:
                metrics_parts.append(f"DAU: {product.get('dau', 0):,}")
            if support:
                metrics_parts.append(f"Tickets: {support.get('ticket_volume', 0)}")
            
            if metrics_parts:
                metrics_text = f"Key metrics: {', '.join(metrics_parts)}. "
        
        # Extract top correlation
        correlations = report_data.get('correlations', [])
        correlation_text = ""
        if correlations:
            top_correlation = correlations[0]
            correlation_text = f"Key finding: {top_correlation.get('pattern', '')}. "
        
        # Extract top recommendation
        recommendations = report_data.get('strategic_recommendations', [])
        recommendation_text = ""
        if recommendations:
            top_rec = recommendations[0]
            recommendation_text = f"Top recommendation: {top_rec.get('action', '')}. "
        
        # Combine into summary
        summary = f"{executive_summary} {metrics_text}{correlation_text}{recommendation_text}"
        
        # Truncate to max_words
        words = summary.split()
        if len(words) > max_words:
            summary = ' '.join(words[:max_words]) + "..."
        
        return summary.strip()
    
    def _generate_risk_rationale(
        self,
        escalation_reason: str,
        risk_score: float,
        guardrail_violations: List[Dict[str, Any]],
        evaluation_details: Optional[Dict[str, Any]]
    ) -> str:
        """Generate risk rationale explanation."""
        rationale_parts = []
        
        # Base rationale
        rationale_parts.append(f"Escalation reason: {escalation_reason}")
        rationale_parts.append(f"Risk score: {risk_score:.2f} ({'High' if risk_score > 0.7 else 'Medium' if risk_score > 0.4 else 'Low'})")
        
        # Guardrail violations
        if guardrail_violations:
            critical_violations = [v for v in guardrail_violations if v.get('severity') == 'critical']
            if critical_violations:
                rationale_parts.append(f"Critical guardrail violations: {len(critical_violations)}")
            else:
                rationale_parts.append(f"Guardrail violations: {len(guardrail_violations)}")
        
        # Evaluation details
        if evaluation_details:
            overall_score = evaluation_details.get('evaluation_details', {}).get('overall_score', 0)
            if overall_score < 0.7:
                rationale_parts.append(f"Low evaluation score: {overall_score:.2f}")
        
        return ". ".join(rationale_parts)
    
    def _format_agent_outputs(self, analytical_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format agent outputs for human review."""
        formatted = {}
        
        for agent_type, result in analytical_results.items():
            if isinstance(result, dict):
                try:
                    if 'response' in result:
                        agent_data = json.loads(result['response']) if isinstance(result['response'], str) else result['response']
                    else:
                        agent_data = result
                    
                    formatted[agent_type] = {
                        'confidence': agent_data.get('confidence', 0),
                        'key_insights': agent_data.get('analysis', {}).get('key_insights', [])[:3],
                        'top_recommendation': agent_data.get('analysis', {}).get('recommendations', [{}])[0] if agent_data.get('analysis', {}).get('recommendations') else None,
                        'data_citations': agent_data.get('data_citations', [])[:3]
                    }
                except (json.JSONDecodeError, TypeError):
                    formatted[agent_type] = {'error': 'Could not parse agent output'}
        
        return formatted
    
    def _generate_recommended_actions(
        self,
        report_data: Dict[str, Any],
        guardrail_violations: List[Dict[str, Any]],
        risk_score: float
    ) -> List[Dict[str, Any]]:
        """Generate recommended actions with pros/cons."""
        actions = []
        
        # Extract recommendations from report
        recommendations = report_data.get('strategic_recommendations', [])
        
        for rec in recommendations[:3]:  # Top 3 recommendations
            action = {
                'action': rec.get('action', ''),
                'priority': rec.get('priority', 'medium'),
                'expected_impact': rec.get('expected_impact', ''),
                'pros': [
                    f"High priority: {rec.get('priority', 'medium')}",
                    f"Expected impact: {rec.get('expected_impact', 'N/A')}"
                ],
                'cons': [
                    "Requires cross-functional coordination",
                    "Resource allocation needed"
                ]
            }
            actions.append(action)
        
        # Add guardrail-specific actions
        if guardrail_violations:
            critical_violations = [v for v in guardrail_violations if v.get('severity') == 'critical']
            if critical_violations:
                actions.insert(0, {
                    'action': 'Review and address critical guardrail violations',
                    'priority': 'high',
                    'expected_impact': 'Ensure compliance and data quality',
                    'pros': ['Prevents data quality issues', 'Ensures compliance'],
                    'cons': ['May delay report delivery', 'Requires immediate attention']
                })
        
        return actions
    
    def _generate_review_url(self, session_id: str) -> str:
        """Generate review URL (stub for future frontend)."""
        base_url = config.get('hitl.review_base_url', 'https://app.example.com/review')
        return f"{base_url}/{session_id}"
    
    async def _auto_approve_demo(
        self,
        escalation_package: EscalationPackage,
        risk_score: float
    ) -> HITLDecision:
        """Auto-approve in demo mode with simulated delay."""
        # Simulate human review delay
        await asyncio.sleep(self.auto_approval_delay_seconds)
        
        # Simulate decision based on risk score
        if risk_score < 0.5:
            decision = "approved"
            feedback = "Auto-approved: Low risk score indicates acceptable quality"
        elif risk_score < 0.7:
            decision = "approved"
            feedback = "Auto-approved: Medium risk score, acceptable with minor concerns"
        else:
            decision = "modified"
            feedback = "Auto-modified: High risk score, applying conservative modifications"
            modifications = {
                'confidence_adjusted': True,
                'risk_flags_added': True
            }
            return HITLDecision(
                decision=decision,
                feedback=feedback,
                modifications=modifications,
                auto_approved=True,
                human_reviewer="demo_auto_approver"
            )
        
        return HITLDecision(
            decision=decision,
            feedback=feedback,
            auto_approved=True,
            human_reviewer="demo_auto_approver"
        )
    
    async def _wait_for_human_decision(
        self,
        escalation_package: EscalationPackage
    ) -> HITLDecision:
        """
        Wait for human decision (stub for production).
        
        In production, this would:
        - Poll review API endpoint
        - Wait for human response
        - Handle timeouts
        """
        # Stub: In production, this would integrate with review UI
        # For now, return pending status (would be handled by separate review endpoint)
        
        self.logger.info(
            f"HITL request {escalation_package.request_id} queued for human review",
            extra={
                'request_id': escalation_package.request_id,
                'review_url': escalation_package.review_url
            }
        )
        
        # Return default decision (in production, would wait for actual human input)
        return HITLDecision(
            decision="pending",
            feedback="Awaiting human review",
            auto_approved=False
        )
    
    async def _send_notification(self, escalation_package: EscalationPackage):
        """Send notification about escalation (stub)."""
        if not self.notification_enabled:
            return
        
        # Stub: In production, would send email/Slack notification
        self.logger.info(
            f"Notification sent for HITL request {escalation_package.request_id}",
            extra={
                'request_id': escalation_package.request_id,
                'review_url': escalation_package.review_url,
                'risk_score': escalation_package.risk_score
            }
        )
        
        # In production:
        # - Send email to reviewers
        # - Post to Slack channel
        # - Create ticket in issue tracker
    
    def _learn_from_decision(
        self,
        escalation_package: EscalationPackage,
        decision: HITLDecision
    ):
        """Learn from human decision to improve guardrails."""
        if not self.guardrail_agent:
            return
        
        # Determine if this was a false positive
        was_false_positive = False
        
        if decision.decision == 'approved':
            # If approved, violations may have been false positives
            for violation in escalation_package.guardrail_violations:
                if violation.get('rule_type') == 'adaptive':
                    rule_name = violation.get('rule_name')
                    # Check if violation was overly strict
                    if violation.get('severity') in ['low', 'medium']:
                        was_false_positive = True
                        self.guardrail_agent.learn_from_hitl_feedback(
                            rule_name=rule_name,
                            was_false_positive=was_false_positive
                        )
                        self.logger.info(
                            f"Learned from HITL decision: {rule_name} threshold adjusted",
                            extra={
                                'rule_name': rule_name,
                                'was_false_positive': was_false_positive,
                                'decision': decision.decision
                            }
                        )
        elif decision.decision == 'rejected':
            # If rejected, violations were likely true positives
            # Could tighten thresholds
            pass
    
    def create_request(self, trace_id: str, agent_type: str,
                      reason: str, context: Dict[str, Any],
                      proposed_action: Optional[str] = None) -> str:
        """
        Create a new HITL request.
        
        Args:
            trace_id: Associated trace ID
            agent_type: Type of agent
            reason: Reason for escalation
            context: Full context for human review
            proposed_action: Optional proposed action
            
        Returns:
            HITL request ID
        """
        request_id = self.cache_manager.create_hitl_request(
            trace_id=trace_id,
            agent_type=agent_type,
            reason=reason,
            context=context,
            proposed_action=proposed_action
        )
        
        self.logger.info(
            f"Created HITL request: {request_id}",
            extra={'request_id': request_id, 'trace_id': trace_id, 'reason': reason}
        )
        
        return request_id
    
    def resolve_request(self, request_id: str, status: HITLStatus,
                       human_decision: str, human_feedback: Optional[str] = None):
        """
        Resolve a HITL request.
        
        Args:
            request_id: HITL request ID
            status: Resolution status
            human_decision: Human's decision
            human_feedback: Optional feedback
        """
        self.cache_manager.resolve_hitl_request(
            request_id=request_id,
            status=status.value,
            human_decision=human_decision,
            human_feedback=human_feedback
        )
        
        self.logger.info(
            f"Resolved HITL request: {request_id}",
            extra={'request_id': request_id, 'status': status.value}
        )
    
    def get_pending_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending HITL requests (for review interface).
        
        Args:
            limit: Maximum number of requests to return
            
        Returns:
            List of pending request dictionaries
        """
        try:
            conn = self.cache_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM hitl_requests
                WHERE status = 'pending'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            requests = [dict(row) for row in cursor.fetchall()]
            
            # Parse context JSON
            for req in requests:
                if req.get('context'):
                    try:
                        req['context'] = json.loads(req['context'])
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            return requests
        except Exception as e:
            self.logger.error(f"Error getting pending requests: {e}", exc_info=True)
            return []
    
    def approve_request(
        self,
        request_id: str,
        human_feedback: Optional[str] = None,
        human_reviewer: Optional[str] = None
    ) -> bool:
        """
        Approve a HITL request (for review interface).
        
        Args:
            request_id: HITL request ID
            human_feedback: Optional feedback
            human_reviewer: Optional reviewer identifier
            
        Returns:
            True if successful
        """
        try:
            self.resolve_request(
                request_id=request_id,
                status=HITLStatus.APPROVED,
                human_decision="approved",
                human_feedback=human_feedback
            )
            
            # Learn from decision
            if self.guardrail_agent:
                # Get request details
                conn = self.cache_manager.connect()
                cursor = conn.cursor()
                cursor.execute("SELECT context FROM hitl_requests WHERE request_id = ?", (request_id,))
                row = cursor.fetchone()
                if row and row['context']:
                    try:
                        context = json.loads(row['context'])
                        violations = context.get('guardrail_violations', [])
                        for violation in violations:
                            if violation.get('rule_type') == 'adaptive':
                                self.guardrail_agent.learn_from_hitl_feedback(
                                    rule_name=violation.get('rule_name'),
                                    was_false_positive=True
                                )
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            return True
        except Exception as e:
            self.logger.error(f"Error approving request: {e}", exc_info=True)
            return False
    
    def reject_request(
        self,
        request_id: str,
        human_feedback: str,
        human_reviewer: Optional[str] = None
    ) -> bool:
        """
        Reject a HITL request (for review interface).
        
        Args:
            request_id: HITL request ID
            human_feedback: Required feedback explaining rejection
            human_reviewer: Optional reviewer identifier
            
        Returns:
            True if successful
        """
        try:
            self.resolve_request(
                request_id=request_id,
                status=HITLStatus.REJECTED,
                human_decision="rejected",
                human_feedback=human_feedback
            )
            return True
        except Exception as e:
            self.logger.error(f"Error rejecting request: {e}", exc_info=True)
            return False
    
    def modify_request(
        self,
        request_id: str,
        modifications: Dict[str, Any],
        human_feedback: Optional[str] = None,
        human_reviewer: Optional[str] = None
    ) -> bool:
        """
        Modify a HITL request (for review interface).
        
        Args:
            request_id: HITL request ID
            modifications: Dictionary of modifications made
            human_feedback: Optional feedback
            human_reviewer: Optional reviewer identifier
            
        Returns:
            True if successful
        """
        try:
            feedback = human_feedback or f"Modified: {json.dumps(modifications)}"
            self.resolve_request(
                request_id=request_id,
                status=HITLStatus.MODIFIED,
                human_decision=f"modified: {json.dumps(modifications)}",
                human_feedback=feedback
            )
            return True
        except Exception as e:
            self.logger.error(f"Error modifying request: {e}", exc_info=True)
            return False
