"""
Comprehensive Evaluation Agent for quality control.

Evaluates synthesized reports using Gemini meta-evaluation with multiple criteria:
- Requirement Fulfillment
- Factual Grounding
- Quality & Coherence
- Consistency Check
- Constraint Compliance
"""

import json
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from cache.cache_manager import CacheManager
from integrations.gemini_client import GeminiClient
from utils.config import config
from utils.logger import logger


@dataclass
class EvaluationResult:
    """Result of evaluation."""
    requirement_score: float = 0.0
    requirement_reasoning: str = ""
    grounding_score: float = 0.0
    grounding_reasoning: str = ""
    quality_score: float = 0.0
    quality_reasoning: str = ""
    consistency_score: float = 0.0
    consistency_reasoning: str = ""
    constraint_score: float = 0.0
    constraint_reasoning: str = ""
    overall_score: float = 0.0
    pass_threshold: bool = False
    issues: List[str] = field(default_factory=list)
    regeneration_needed: bool = False
    regeneration_feedback: str = ""
    evaluation_time_ms: int = 0


class Evaluator:
    """
    Comprehensive Evaluator Agent for quality control.
    
    Uses Gemini meta-evaluation to assess:
    - Requirement Fulfillment
    - Factual Grounding
    - Quality & Coherence
    - Consistency Check
    - Constraint Compliance
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Evaluator Agent.
        
        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager or CacheManager()
        self.gemini_client = GeminiClient(cache_manager)
        self.logger = logger.getChild('evaluator')
        
        # Configuration
        self.pass_threshold = config.get('evaluation.pass_threshold', 0.75)
        self.regeneration_threshold = config.get('evaluation.regeneration_threshold', 0.75)
        self.max_regenerations = config.get('evaluation.max_regenerations', 2)
        self.evaluation_cache_ttl_hours = 168  # 7 days
        
        self.logger.info("Evaluator initialized")
    
    async def evaluate(
        self,
        agent_type: str,
        response: Dict[str, Any],
        trace_id: Optional[str] = None,
        original_data_summary: Optional[Dict[str, Any]] = None,
        requested_analysis_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate an agent response comprehensively.
        
        Args:
            agent_type: Type of agent (typically 'synthesizer')
            response: Agent response to evaluate
            trace_id: Optional trace ID
            original_data_summary: Summary of source data for grounding check
            requested_analysis_areas: List of requested analysis areas
            
        Returns:
            Evaluation results with scores and flags
        """
        start_time = time.time()
        
        try:
            # Extract report content
            if isinstance(response, dict) and 'response' in response:
                # Response is a dict with 'response' key containing JSON string
                report_data = json.loads(response['response']) if isinstance(response['response'], str) else response['response']
            else:
                report_data = response
            
            # Generate report hash for caching
            report_hash = self._hash_report(report_data)
            
            # Check evaluation cache
            cached_evaluation = self._get_cached_evaluation(report_hash)
            if cached_evaluation:
                self.logger.info("Evaluation cache HIT")
                return cached_evaluation
            
            self.logger.info("Evaluation cache MISS - performing new evaluation")
            
            # Build evaluation prompt
            evaluation_prompt = self._build_evaluation_prompt(
                report_data=report_data,
                original_data_summary=original_data_summary,
                requested_analysis_areas=requested_analysis_areas
            )
            
            # Perform Gemini evaluation
            gemini_response = await self.gemini_client.generate(
                evaluation_prompt,
                use_cache=True
            )
            
            # Parse evaluation results
            evaluation_result = self._parse_evaluation_response(
                gemini_response['text'],
                report_data
            )
            
            # Calculate overall score
            evaluation_result.overall_score = self._calculate_overall_score(evaluation_result)
            evaluation_result.pass_threshold = evaluation_result.overall_score >= self.pass_threshold
            evaluation_result.regeneration_needed = (
                evaluation_result.overall_score < self.regeneration_threshold
            )
            evaluation_result.evaluation_time_ms = int((time.time() - start_time) * 1000)
            
            # Generate regeneration feedback if needed
            if evaluation_result.regeneration_needed:
                evaluation_result.regeneration_feedback = self._generate_regeneration_feedback(
                    evaluation_result
                )
            
            # Cache evaluation result
            self._cache_evaluation(report_hash, evaluation_result)
            
            # Record evaluation in database
            self._record_evaluation(
                trace_id=trace_id or "unknown",
                agent_type=agent_type,
                evaluation_result=evaluation_result
            )
            
            # Convert to dict format
            result_dict = {
                'factual_grounding_score': evaluation_result.grounding_score,
                'relevance_score': evaluation_result.requirement_score,
                'completeness_score': evaluation_result.requirement_score,
                'coherence_score': evaluation_result.quality_score,
                'data_citations_present': evaluation_result.grounding_score > 0.7,
                'confidence_calibrated': evaluation_result.consistency_score > 0.7,
                'anomalies_flagged': len(evaluation_result.issues) > 0,
                'overall_quality': self._score_to_quality(evaluation_result.overall_score),
                'requires_review': evaluation_result.regeneration_needed,
                'review_reason': evaluation_result.regeneration_feedback if evaluation_result.regeneration_needed else None,
                'evaluation_details': {
                    'requirement_score': evaluation_result.requirement_score,
                    'grounding_score': evaluation_result.grounding_score,
                    'quality_score': evaluation_result.quality_score,
                    'consistency_score': evaluation_result.consistency_score,
                    'constraint_score': evaluation_result.constraint_score,
                    'overall_score': evaluation_result.overall_score,
                    'issues': evaluation_result.issues
                }
            }
            
            self.logger.info(
                f"Evaluation completed",
                extra={
                    'agent_type': agent_type,
                    'overall_score': evaluation_result.overall_score,
                    'pass_threshold': evaluation_result.pass_threshold,
                    'regeneration_needed': evaluation_result.regeneration_needed
                }
            )
            
            return result_dict
            
        except Exception as e:
            self.logger.error(f"Error in evaluation: {e}", exc_info=True)
            # Return default evaluation on error
            return {
                'factual_grounding_score': 0.5,
                'relevance_score': 0.5,
                'completeness_score': 0.5,
                'coherence_score': 0.5,
                'data_citations_present': False,
                'confidence_calibrated': False,
                'anomalies_flagged': False,
                'overall_quality': 'acceptable',
                'requires_review': True,
                'review_reason': f'Evaluation error: {str(e)}'
            }
    
    def _build_evaluation_prompt(
        self,
        report_data: Dict[str, Any],
        original_data_summary: Optional[Dict[str, Any]],
        requested_analysis_areas: Optional[List[str]]
    ) -> str:
        """Build comprehensive evaluation prompt for Gemini."""
        
        # Extract key sections from report
        executive_summary = report_data.get('executive_summary', '')
        correlations = report_data.get('correlations', [])
        root_causes = report_data.get('root_causes', [])
        recommendations = report_data.get('strategic_recommendations', [])
        key_metrics = report_data.get('key_metrics_summary', {})
        data_citations = report_data.get('data_citations', [])
        
        synthesized_report = f"""
EXECUTIVE SUMMARY:
{executive_summary}

KEY METRICS:
{json.dumps(key_metrics, indent=2)}

CORRELATIONS ({len(correlations)}):
{json.dumps(correlations[:5], indent=2) if correlations else "None"}

ROOT CAUSES ({len(root_causes)}):
{json.dumps(root_causes[:3], indent=2) if root_causes else "None"}

RECOMMENDATIONS ({len(recommendations)}):
{json.dumps(recommendations[:5], indent=2) if recommendations else "None"}

DATA CITATIONS ({len(data_citations)}):
{chr(10).join(data_citations[:10]) if data_citations else "None"}
"""
        
        # Build data summary
        if original_data_summary:
            data_summary = json.dumps(original_data_summary, indent=2)
        else:
            data_summary = "Source data summary not provided"
        
        # Build requested areas
        if requested_analysis_areas:
            requested_areas = ", ".join(requested_analysis_areas)
        else:
            requested_areas = "Comprehensive analysis (revenue, product, support)"
        
        prompt = f"""You are a quality assurance analyst evaluating a SaaS business intelligence report.

REPORT TO EVALUATE:
{synthesized_report}

SOURCE DATA SUMMARY:
{data_summary}

REQUESTED ANALYSIS AREAS:
{requested_areas}

EVALUATION CRITERIA:

1. REQUIREMENT FULFILLMENT (0-1 score):
   - Does the report address all requested analysis areas ({requested_areas})?
   - Are key metrics included (MRR, churn, engagement, support metrics)?
   - Is executive summary present and clear (2-3 sentences)?
   - Are correlations, root causes, and recommendations provided?

2. FACTUAL GROUNDING (0-1 score):
   - Are all claims backed by data citations?
   - Do numbers match source data (if provided)?
   - Are calculations correct?
   - Are data sources clearly cited?

3. QUALITY & COHERENCE (0-1 score):
   - Is the narrative logical and coherent?
   - Are recommendations actionable and specific?
   - Is language clear and professional?
   - Are insights well-structured and easy to follow?

4. CONSISTENCY CHECK (0-1 score):
   - Do different sections contradict each other?
   - Are agent outputs aligned (revenue/product/support)?
   - Do recommendations match findings?
   - Are correlations consistent with root causes?

5. CONSTRAINT COMPLIANCE (0-1 score):
   - No PII or sensitive data present?
   - Report structure follows expected format?
   - All required fields present?
   - Guardrails passed (assume yes if report exists)?

For each criterion, provide:
- Score (0-1, be strict but fair)
- Reasoning (1-2 sentences explaining the score)
- Specific issues if score < 0.8

OUTPUT FORMAT: JSON only, no markdown or explanations
{{
  "requirement_score": 0.95,
  "requirement_reasoning": "Report addresses all requested areas with comprehensive metrics and clear executive summary.",
  "grounding_score": 0.88,
  "grounding_reasoning": "Most claims are cited, but some recommendations lack specific data references.",
  "quality_score": 0.92,
  "quality_reasoning": "Well-structured narrative with actionable recommendations and professional language.",
  "consistency_score": 0.90,
  "consistency_reasoning": "Sections are aligned and recommendations match findings consistently.",
  "constraint_score": 1.0,
  "constraint_reasoning": "No PII detected, format compliant, all required fields present.",
  "overall_score": 0.93,
  "pass": true,
  "issues": [
    "Minor: Some recommendations could cite more specific data cells"
  ],
  "regeneration_needed": false
}}

Now evaluate the report:"""
        
        return prompt
    
    def _parse_evaluation_response(
        self,
        response_text: str,
        report_data: Dict[str, Any]
    ) -> EvaluationResult:
        """Parse Gemini evaluation response."""
        # Extract JSON from response
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        
        try:
            eval_data = json.loads(response_text)
            
            return EvaluationResult(
                requirement_score=eval_data.get('requirement_score', 0.0),
                requirement_reasoning=eval_data.get('requirement_reasoning', ''),
                grounding_score=eval_data.get('grounding_score', 0.0),
                grounding_reasoning=eval_data.get('grounding_reasoning', ''),
                quality_score=eval_data.get('quality_score', 0.0),
                quality_reasoning=eval_data.get('quality_reasoning', ''),
                consistency_score=eval_data.get('consistency_score', 0.0),
                consistency_reasoning=eval_data.get('consistency_reasoning', ''),
                constraint_score=eval_data.get('constraint_score', 0.0),
                constraint_reasoning=eval_data.get('constraint_reasoning', ''),
                overall_score=eval_data.get('overall_score', 0.0),
                pass_threshold=eval_data.get('pass', False),
                issues=eval_data.get('issues', []),
                regeneration_needed=eval_data.get('regeneration_needed', False)
            )
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse evaluation JSON: {e}")
            # Fallback to heuristic evaluation
            return self._heuristic_evaluation(report_data)
    
    def _heuristic_evaluation(self, report_data: Dict[str, Any]) -> EvaluationResult:
        """Fallback heuristic evaluation when Gemini fails."""
        scores = {
            'requirement': 0.7,
            'grounding': 0.6,
            'quality': 0.7,
            'consistency': 0.7,
            'constraint': 0.9
        }
        
        # Check for required sections
        if report_data.get('executive_summary'):
            scores['requirement'] += 0.1
        if report_data.get('correlations'):
            scores['requirement'] += 0.1
        if report_data.get('strategic_recommendations'):
            scores['requirement'] += 0.1
        
        # Check for data citations
        citations = report_data.get('data_citations', [])
        if len(citations) > 0:
            scores['grounding'] += 0.2
        
        # Normalize scores
        for key in scores:
            scores[key] = min(1.0, scores[key])
        
        overall = sum(scores.values()) / len(scores)
        
        return EvaluationResult(
            requirement_score=scores['requirement'],
            requirement_reasoning="Heuristic evaluation: Basic structure present",
            grounding_score=scores['grounding'],
            grounding_reasoning=f"Heuristic evaluation: {len(citations)} citations found",
            quality_score=scores['quality'],
            quality_reasoning="Heuristic evaluation: Structure appears coherent",
            consistency_score=scores['consistency'],
            consistency_reasoning="Heuristic evaluation: Unable to verify consistency",
            constraint_score=scores['constraint'],
            constraint_reasoning="Heuristic evaluation: Format appears compliant",
            overall_score=overall,
            pass_threshold=overall >= self.pass_threshold,
            issues=["Heuristic evaluation used - Gemini evaluation unavailable"],
            regeneration_needed=overall < self.regeneration_threshold
        )
    
    def _calculate_overall_score(self, result: EvaluationResult) -> float:
        """Calculate weighted overall score."""
        # Weighted average (all criteria equally important)
        weights = {
            'requirement': 0.2,
            'grounding': 0.25,
            'quality': 0.2,
            'consistency': 0.2,
            'constraint': 0.15
        }
        
        overall = (
            result.requirement_score * weights['requirement'] +
            result.grounding_score * weights['grounding'] +
            result.quality_score * weights['quality'] +
            result.consistency_score * weights['consistency'] +
            result.constraint_score * weights['constraint']
        )
        
        return round(overall, 3)
    
    def _generate_regeneration_feedback(self, result: EvaluationResult) -> str:
        """Generate specific feedback for regeneration."""
        feedback_parts = []
        
        if result.requirement_score < 0.8:
            feedback_parts.append(f"Requirement fulfillment ({result.requirement_score:.2f}): {result.requirement_reasoning}")
        
        if result.grounding_score < 0.8:
            feedback_parts.append(f"Factual grounding ({result.grounding_score:.2f}): {result.grounding_reasoning}")
        
        if result.quality_score < 0.8:
            feedback_parts.append(f"Quality & coherence ({result.quality_score:.2f}): {result.quality_reasoning}")
        
        if result.consistency_score < 0.8:
            feedback_parts.append(f"Consistency ({result.consistency_score:.2f}): {result.consistency_reasoning}")
        
        if result.constraint_score < 0.8:
            feedback_parts.append(f"Constraint compliance ({result.constraint_score:.2f}): {result.constraint_reasoning}")
        
        if result.issues:
            feedback_parts.append(f"Issues to address: {', '.join(result.issues)}")
        
        return "; ".join(feedback_parts) if feedback_parts else "Overall score below threshold"
    
    def _score_to_quality(self, score: float) -> str:
        """Convert numeric score to quality label."""
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.8:
            return 'good'
        elif score >= 0.7:
            return 'acceptable'
        else:
            return 'poor'
    
    def _hash_report(self, report_data: Dict[str, Any]) -> str:
        """Generate hash for report caching."""
        # Create deterministic hash from report content
        report_str = json.dumps({
            'executive_summary': report_data.get('executive_summary', ''),
            'correlations_count': len(report_data.get('correlations', [])),
            'recommendations_count': len(report_data.get('strategic_recommendations', [])),
            'key_metrics': report_data.get('key_metrics_summary', {})
        }, sort_keys=True)
        
        return hashlib.sha256(report_str.encode()).hexdigest()[:16]
    
    def _get_cached_evaluation(self, report_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached evaluation result."""
        try:
            conn = self.cache_manager.connect()
            cursor = conn.cursor()
            
            # Use prompt_cache table for evaluation caching
            cache_key = f"evaluation:{report_hash}"
            cached = self.cache_manager.get_cached_prompt(
                prompt=cache_key,
                model="evaluator"
            )
            
            if cached:
                try:
                    return json.loads(cached['response'])
                except json.JSONDecodeError:
                    return None
        except Exception as e:
            self.logger.warning(f"Error getting cached evaluation: {e}")
        
        return None
    
    def _cache_evaluation(self, report_hash: str, result: EvaluationResult):
        """Cache evaluation result."""
        try:
            cache_key = f"evaluation:{report_hash}"
            result_json = json.dumps({
                'factual_grounding_score': result.grounding_score,
                'relevance_score': result.requirement_score,
                'completeness_score': result.requirement_score,
                'coherence_score': result.quality_score,
                'data_citations_present': result.grounding_score > 0.7,
                'confidence_calibrated': result.consistency_score > 0.7,
                'anomalies_flagged': len(result.issues) > 0,
                'overall_quality': self._score_to_quality(result.overall_score),
                'requires_review': result.regeneration_needed,
                'review_reason': result.regeneration_feedback if result.regeneration_needed else None,
                'evaluation_details': {
                    'requirement_score': result.requirement_score,
                    'grounding_score': result.grounding_score,
                    'quality_score': result.quality_score,
                    'consistency_score': result.consistency_score,
                    'constraint_score': result.constraint_score,
                    'overall_score': result.overall_score,
                    'issues': result.issues
                }
            })
            
            self.cache_manager.cache_prompt(
                prompt=cache_key,
                response=result_json,
                model="evaluator",
                tokens_input=0,  # Evaluation prompts are cached separately
                tokens_output=0,
                ttl_hours=self.evaluation_cache_ttl_hours
            )
        except Exception as e:
            self.logger.warning(f"Error caching evaluation: {e}")
    
    def _record_evaluation(
        self,
        trace_id: str,
        agent_type: str,
        evaluation_result: EvaluationResult
    ):
        """Record evaluation in database."""
        try:
            self.cache_manager.record_evaluation(
                trace_id=trace_id,
                agent_type=agent_type,
                factual_grounding_score=evaluation_result.grounding_score,
                relevance_score=evaluation_result.requirement_score,
                completeness_score=evaluation_result.requirement_score,
                coherence_score=evaluation_result.quality_score,
                data_citations_present=evaluation_result.grounding_score > 0.7,
                confidence_calibrated=evaluation_result.consistency_score > 0.7,
                anomalies_flagged=len(evaluation_result.issues) > 0,
                overall_quality=self._score_to_quality(evaluation_result.overall_score),
                evaluator_agent="evaluator",
                evaluation_time_ms=evaluation_result.evaluation_time_ms,
                requires_review=evaluation_result.regeneration_needed,
                review_reason=evaluation_result.regeneration_feedback if evaluation_result.regeneration_needed else None
            )
        except Exception as e:
            self.logger.error(f"Error recording evaluation: {e}", exc_info=True)
    
    async def evaluate_with_regeneration(
        self,
        agent_type: str,
        response: Dict[str, Any],
        trace_id: Optional[str] = None,
        original_data_summary: Optional[Dict[str, Any]] = None,
        requested_analysis_areas: Optional[List[str]] = None,
        regeneration_callback: Optional[callable] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Evaluate with automatic regeneration if score is low.
        
        Args:
            agent_type: Type of agent
            response: Agent response to evaluate
            trace_id: Optional trace ID
            original_data_summary: Summary of source data
            requested_analysis_areas: List of requested areas
            regeneration_callback: Optional callback to regenerate report
            
        Returns:
            Tuple of (evaluation_result, regeneration_count)
        """
        regeneration_count = 0
        
        while regeneration_count <= self.max_regenerations:
            # Evaluate
            evaluation_result = await self.evaluate(
                agent_type=agent_type,
                response=response,
                trace_id=trace_id,
                original_data_summary=original_data_summary,
                requested_analysis_areas=requested_analysis_areas
            )
            
            # Check if regeneration needed
            if not evaluation_result.get('requires_review', False):
                return evaluation_result, regeneration_count
            
            if regeneration_count >= self.max_regenerations:
                self.logger.warning(
                    f"Max regenerations ({self.max_regenerations}) reached",
                    extra={'trace_id': trace_id}
                )
                return evaluation_result, regeneration_count
            
            # Regenerate with feedback
            if regeneration_callback:
                feedback = evaluation_result.get('review_reason', '')
                self.logger.info(
                    f"Regenerating report (attempt {regeneration_count + 1})",
                    extra={'feedback': feedback, 'trace_id': trace_id}
                )
                
                try:
                    response = await regeneration_callback(feedback)
                    regeneration_count += 1
                except Exception as e:
                    self.logger.error(f"Regeneration failed: {e}", exc_info=True)
                    return evaluation_result, regeneration_count
            else:
                # No callback provided, return current result
                return evaluation_result, regeneration_count
        
        return evaluation_result, regeneration_count
