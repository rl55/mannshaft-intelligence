"""
Production Synthesizer Agent - Cross-functional intelligence layer.

Features:
- Cross-correlates insights from Revenue, Product, and Support agents
- Pattern recognition (temporal, segment-specific, seasonal)
- Root cause analysis (5 Whys methodology)
- Strategic recommendations prioritized by impact
- External validation via web search
- Executive summary generation
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from pydantic import BaseModel, Field
import numpy as np

from agents.base_agent import BaseAgent
from cache.cache_manager import CacheManager
from integrations.gemini_client import GeminiClient
from integrations.web_search import WebSearchClient
from utils.config import config
from utils.logger import logger


# ============================================================================
# PYDANTIC MODELS FOR VALIDATION
# ============================================================================

class Correlation(BaseModel):
    """Cross-functional correlation."""
    pattern: str = Field(..., description="Description of the correlation pattern")
    agents_involved: List[str] = Field(..., description="Agents involved in correlation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in correlation")
    business_impact: str = Field(..., description="Impact level: high|medium|low")
    temporal_relationship: Optional[str] = Field(None, description="lagging|leading|concurrent")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")


class RootCause(BaseModel):
    """Root cause analysis result."""
    hypothesis: str = Field(..., description="Root cause hypothesis")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in hypothesis")
    reasoning: str = Field(..., description="5 Whys analysis")
    correlation_vs_causation: str = Field(..., description="Assessment of correlation vs causation")
    supporting_evidence: List[str] = Field(default_factory=list)
    external_validation: Optional[Dict[str, Any]] = Field(None, description="External validation results")


class StrategicRecommendation(BaseModel):
    """Strategic recommendation."""
    action: str = Field(..., description="Recommended action")
    priority: str = Field(..., description="Priority: high|medium|low")
    expected_impact: str = Field(..., description="Quantified expected impact")
    feasibility: str = Field(..., description="Feasibility: high|medium|low")
    cross_functional_teams: List[str] = Field(default_factory=list, description="Teams involved")
    resource_requirements: Optional[str] = Field(None, description="Resource needs")
    timeline: Optional[str] = Field(None, description="Estimated timeline")


class SynthesisOutput(BaseModel):
    """Complete synthesis output."""
    agent_id: str = Field(default_factory=lambda: f"synthesizer_agent_{uuid.uuid4().hex[:8]}")
    agent_type: str = "synthesizer"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = Field(..., ge=0, le=1)
    executive_summary: str = Field(..., description="2-3 sentence executive summary")
    correlations: List[Dict[str, Any]] = Field(default_factory=list)
    root_causes: List[Dict[str, Any]] = Field(default_factory=list)
    strategic_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    key_metrics_summary: Dict[str, Any] = Field(default_factory=dict)
    external_validations: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# SYNTHESIZER AGENT IMPLEMENTATION
# ============================================================================

class SynthesizerAgent(BaseAgent):
    """
    Production-grade Synthesizer Agent for cross-functional intelligence.
    
    Responsibilities:
    - Receive outputs from Revenue, Product, and Support agents
    - Identify cross-functional correlations
    - Perform root cause analysis
    - Generate strategic recommendations
    - Prioritize findings by business impact
    - Create executive summary
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Synthesizer Agent.
        
        Args:
            cache_manager: Cache manager instance
        """
        super().__init__("synthesizer", cache_manager)
        
        # Initialize integrations
        self.gemini_client = GeminiClient(cache_manager)
        self.web_search_client = WebSearchClient(cache_manager)
        
        # Configuration
        self.prompt_cache_ttl_hours = 24
        self.agent_cache_ttl_hours = 1
        self.enable_external_validation = config.get('synthesizer.enable_external_validation', True)
        
        self.logger.info("SynthesizerAgent initialized")
    
    async def analyze(self, context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Synthesize multiple agent results with cross-functional analysis.
        
        Args:
            context: Input context containing:
                - analytical_results: Dictionary with agent results
                - week_number: Week number for analysis
            session_id: Session identifier
            
        Returns:
            Synthesis result with:
            - response: JSON string of synthesis
            - confidence_score: Confidence level (0-1)
            - metadata: Additional metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Extract agent results
            analytical_results = context.get('analytical_results', {})
            week_number = context.get('week_number', 0)
            
            if not analytical_results:
                raise ValueError("No analytical results provided for synthesis")
            
            # Step 2: Parse agent results
            parsed_results = self._parse_agent_results(analytical_results)
            
            # Step 3: Check agent-level cache
            cache_context = {
                'week_number': week_number,
                'results_hash': self._hash_results(parsed_results)
            }
            
            cached_response = self.cache_manager.get_cached_agent_response(
                agent_type=self.agent_type,
                context=cache_context
            )
            
            if cached_response:
                self.logger.info("Agent cache HIT")
                return {
                    'response': cached_response['response'],
                    'confidence_score': cached_response['confidence_score'],
                    'cached': True,
                    'execution_time_ms': cached_response['execution_time_ms'],
                    'metadata': {'cache_hit': True}
                }
            
            self.logger.info("Agent cache MISS - generating new synthesis")
            
            # Step 4: Detect correlations
            correlations = await self._detect_correlations(parsed_results)
            
            # Step 5: Perform root cause analysis
            root_causes = await self._analyze_root_causes(parsed_results, correlations)
            
            # Step 6: Generate strategic recommendations
            recommendations = await self._generate_recommendations(
                parsed_results, correlations, root_causes
            )
            
            # Step 7: External validation (if enabled)
            external_validations = []
            if self.enable_external_validation:
                external_validations = await self._validate_externally(
                    correlations, root_causes, recommendations
                )
            
            # Step 8: Generate executive summary
            executive_summary = await self._generate_executive_summary(
                parsed_results, correlations, root_causes, recommendations
            )
            
            # Step 9: Create key metrics summary
            key_metrics = self._create_metrics_summary(parsed_results)
            
            # Step 10: Calculate confidence
            confidence = self._calculate_confidence(
                parsed_results, correlations, root_causes
            )
            
            # Step 11: Build final output
            output = SynthesisOutput(
                confidence=confidence,
                executive_summary=executive_summary,
                correlations=[c.dict() if isinstance(c, BaseModel) else c for c in correlations],
                root_causes=[rc.dict() if isinstance(rc, BaseModel) else rc for rc in root_causes],
                strategic_recommendations=[r.dict() if isinstance(r, BaseModel) else r for r in recommendations],
                key_metrics_summary=key_metrics,
                external_validations=external_validations
            )
            
            output_dict = output.dict()
            output_json = json.dumps(output_dict, indent=2)
            
            # Step 12: Cache the response
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.cache_manager.cache_agent_response(
                agent_type=self.agent_type,
                context=cache_context,
                response=output_json,
                confidence_score=confidence,
                execution_time_ms=execution_time_ms,
                ttl_hours=self.agent_cache_ttl_hours
            )
            
            self.logger.info(
                f"Synthesis completed",
                extra={
                    'week_number': week_number,
                    'confidence': confidence,
                    'execution_time_ms': execution_time_ms,
                    'correlations': len(correlations),
                    'recommendations': len(recommendations)
                }
            )
            
            return {
                'response': output_json,
                'confidence_score': confidence,
                'cached': False,
                'execution_time_ms': execution_time_ms,
                'metadata': {
                    'agent_id': output_dict['agent_id'],
                    'correlations_count': len(correlations),
                    'recommendations_count': len(recommendations)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in synthesis: {e}", exc_info=True)
            raise
    
    def _parse_agent_results(self, analytical_results: Dict[str, Any]) -> Dict[str, Any]:
        """Parse agent results into structured format."""
        parsed = {}
        
        for agent_type, result in analytical_results.items():
            if isinstance(result, dict) and 'response' in result:
                try:
                    parsed[agent_type] = json.loads(result['response'])
                except (json.JSONDecodeError, TypeError):
                    parsed[agent_type] = result
            else:
                parsed[agent_type] = result
        
        return parsed
    
    async def _detect_correlations(
        self,
        parsed_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect cross-functional correlations."""
        prompt = self._build_correlation_prompt(parsed_results)
        
        # Check prompt cache
        cached_prompt = self.cache_manager.get_cached_prompt(
            prompt=prompt,
            model=self.gemini_client.model_name
        )
        
        if cached_prompt:
            try:
                return json.loads(cached_prompt['response'])
            except json.JSONDecodeError:
                pass
        
        # Generate correlations with Gemini
        gemini_response = await self.gemini_client.generate(prompt, use_cache=True)
        response_text = gemini_response['text']
        
        # Extract JSON
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        
        try:
            correlations_data = json.loads(response_text)
            correlations = correlations_data.get('correlations', [])
            
            # Cache results
            self.cache_manager.cache_prompt(
                prompt=prompt,
                response=json.dumps(correlations),
                model=self.gemini_client.model_name,
                tokens_input=gemini_response.get('tokens_input', 0),
                tokens_output=gemini_response.get('tokens_output', 0),
                ttl_hours=self.prompt_cache_ttl_hours
            )
            
            return correlations
        except json.JSONDecodeError:
            # Fallback to statistical correlation detection
            return self._statistical_correlation_detection(parsed_results)
    
    def _build_correlation_prompt(self, parsed_results: Dict[str, Any]) -> str:
        """Build prompt for correlation detection."""
        return f"""You are a strategic business analyst identifying cross-functional correlations.

REVENUE INSIGHTS:
{json.dumps(parsed_results.get('revenue', {}), indent=2)}

PRODUCT INSIGHTS:
{json.dumps(parsed_results.get('product', {}), indent=2)}

SUPPORT INSIGHTS:
{json.dumps(parsed_results.get('support', {}), indent=2)}

TASK: Identify correlations between these three domains.

Look for:
- Temporal correlations (lagging/leading indicators)
- Segment-specific patterns
- Causal relationships
- Concurrent trends

Return JSON format:
{{
  "correlations": [
    {{
      "pattern": "Description of correlation",
      "agents_involved": ["revenue", "product"],
      "confidence": 0.85,
      "business_impact": "high|medium|low",
      "temporal_relationship": "lagging|leading|concurrent",
      "evidence": ["evidence 1", "evidence 2"]
    }}
  ]
}}

Return ONLY valid JSON, no markdown."""
    
    def _statistical_correlation_detection(
        self,
        parsed_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fallback statistical correlation detection."""
        correlations = []
        
        # Extract key metrics
        revenue_analysis = parsed_results.get('revenue', {}).get('analysis', {})
        product_analysis = parsed_results.get('product', {}).get('analysis', {})
        support_analysis = parsed_results.get('support', {}).get('analysis', {})
        
        # Check for obvious correlations
        revenue_churn = revenue_analysis.get('churn_analysis', {}).get('current_rate', 0)
        support_volume = support_analysis.get('ticket_volume_analysis', {}).get('current_volume', 0)
        
        if revenue_churn > 0.05 and support_volume > 100:
            correlations.append({
                'pattern': 'High churn rate correlates with increased support ticket volume',
                'agents_involved': ['revenue', 'support'],
                'confidence': 0.7,
                'business_impact': 'high',
                'temporal_relationship': 'concurrent',
                'evidence': [
                    f'Churn rate: {revenue_churn:.1%}',
                    f'Support tickets: {support_volume}'
                ]
            })
        
        product_engagement = product_analysis.get('engagement_analysis', {}).get('dau_mau_ratio', 0)
        if product_engagement < 0.2 and revenue_churn > 0.04:
            correlations.append({
                'pattern': 'Low product engagement correlates with higher churn',
                'agents_involved': ['product', 'revenue'],
                'confidence': 0.75,
                'business_impact': 'high',
                'temporal_relationship': 'leading',
                'evidence': [
                    f'DAU/MAU ratio: {product_engagement:.1%}',
                    f'Churn rate: {revenue_churn:.1%}'
                ]
            })
        
        return correlations
    
    async def _analyze_root_causes(
        self,
        parsed_results: Dict[str, Any],
        correlations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform root cause analysis using 5 Whys methodology."""
        prompt = self._build_root_cause_prompt(parsed_results, correlations)
        
        cached_prompt = self.cache_manager.get_cached_prompt(
            prompt=prompt,
            model=self.gemini_client.model_name
        )
        
        if cached_prompt:
            try:
                return json.loads(cached_prompt['response'])
            except json.JSONDecodeError:
                pass
        
        gemini_response = await self.gemini_client.generate(prompt, use_cache=True)
        response_text = gemini_response['text']
        
        # Extract JSON
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        
        try:
            root_causes_data = json.loads(response_text)
            root_causes = root_causes_data.get('root_causes', [])
            
            # Cache results
            self.cache_manager.cache_prompt(
                prompt=prompt,
                response=json.dumps(root_causes),
                model=self.gemini_client.model_name,
                tokens_input=gemini_response.get('tokens_input', 0),
                tokens_output=gemini_response.get('tokens_output', 0),
                ttl_hours=self.prompt_cache_ttl_hours
            )
            
            return root_causes
        except json.JSONDecodeError:
            return []
    
    def _build_root_cause_prompt(
        self,
        parsed_results: Dict[str, Any],
        correlations: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for root cause analysis."""
        return f"""You are a strategic analyst performing root cause analysis using the 5 Whys methodology.

AGENT RESULTS:
{json.dumps(parsed_results, indent=2)}

CORRELATIONS IDENTIFIED:
{json.dumps(correlations, indent=2)}

TASK: For each significant correlation, perform root cause analysis.

Use 5 Whys methodology:
1. Why is this happening?
2. Why is that?
3. Why is that?
4. Why is that?
5. Why is that?

Assess correlation vs causation for each hypothesis.

Return JSON format:
{{
  "root_causes": [
    {{
      "hypothesis": "Root cause hypothesis",
      "confidence": 0.8,
      "reasoning": "5 Whys analysis: Why 1... Why 2... Why 3... Why 4... Why 5...",
      "correlation_vs_causation": "Assessment of whether this is correlation or causation",
      "supporting_evidence": ["evidence 1", "evidence 2"]
    }}
  ]
}}

Return ONLY valid JSON, no markdown."""
    
    async def _generate_recommendations(
        self,
        parsed_results: Dict[str, Any],
        correlations: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate strategic recommendations."""
        prompt = self._build_recommendations_prompt(
            parsed_results, correlations, root_causes
        )
        
        cached_prompt = self.cache_manager.get_cached_prompt(
            prompt=prompt,
            model=self.gemini_client.model_name
        )
        
        if cached_prompt:
            try:
                return json.loads(cached_prompt['response'])
            except json.JSONDecodeError:
                pass
        
        gemini_response = await self.gemini_client.generate(prompt, use_cache=True)
        response_text = gemini_response['text']
        
        # Extract JSON
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        
        try:
            recommendations_data = json.loads(response_text)
            recommendations = recommendations_data.get('strategic_recommendations', [])
            
            # Sort by priority and impact
            recommendations = sorted(
                recommendations,
                key=lambda x: (
                    {'high': 3, 'medium': 2, 'low': 1}.get(x.get('priority', 'low'), 1),
                    {'high': 3, 'medium': 2, 'low': 1}.get(x.get('feasibility', 'low'), 1)
                ),
                reverse=True
            )
            
            # Cache results
            self.cache_manager.cache_prompt(
                prompt=prompt,
                response=json.dumps(recommendations),
                model=self.gemini_client.model_name,
                tokens_input=gemini_response.get('tokens_input', 0),
                tokens_output=gemini_response.get('tokens_output', 0),
                ttl_hours=self.prompt_cache_ttl_hours
            )
            
            return recommendations
        except json.JSONDecodeError:
            return []
    
    def _build_recommendations_prompt(
        self,
        parsed_results: Dict[str, Any],
        correlations: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for recommendations."""
        return f"""You are a strategic advisor generating actionable recommendations.

AGENT RESULTS:
{json.dumps(parsed_results, indent=2)}

CORRELATIONS:
{json.dumps(correlations, indent=2)}

ROOT CAUSES:
{json.dumps(root_causes, indent=2)}

TASK: Generate strategic recommendations prioritized by business impact and feasibility.

Consider:
- Cross-functional action items
- Resource allocation
- Timeline estimates
- Expected impact quantification

Return JSON format:
{{
  "strategic_recommendations": [
    {{
      "action": "Specific actionable recommendation",
      "priority": "high|medium|low",
      "expected_impact": "Quantified expected impact (e.g., '+$150K MRR in Q1')",
      "feasibility": "high|medium|low",
      "cross_functional_teams": ["team1", "team2"],
      "resource_requirements": "Resource needs",
      "timeline": "Estimated timeline"
    }}
  ]
}}

Prioritize by:
1. High impact + High feasibility
2. High impact + Medium feasibility
3. Medium impact + High feasibility

Return ONLY valid JSON, no markdown."""
    
    async def _validate_externally(
        self,
        correlations: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate hypotheses externally via web search."""
        validations = []
        
        # Validate top correlations
        for correlation in correlations[:3]:  # Top 3
            if correlation.get('confidence', 0) > 0.7:
                pattern = correlation.get('pattern', '')
                try:
                    search_results = await self.web_search_client.validate_hypothesis(pattern)
                    validations.append({
                        'type': 'correlation',
                        'hypothesis': pattern,
                        'search_results': search_results,
                        'validated': len(search_results.get('results', [])) > 0
                    })
                except Exception as e:
                    self.logger.warning(f"External validation failed: {e}")
        
        # Validate root causes
        for root_cause in root_causes[:2]:  # Top 2
            hypothesis = root_cause.get('hypothesis', '')
            try:
                search_results = await self.web_search_client.validate_hypothesis(hypothesis)
                validations.append({
                    'type': 'root_cause',
                    'hypothesis': hypothesis,
                    'search_results': search_results,
                    'validated': len(search_results.get('results', [])) > 0
                })
            except Exception as e:
                self.logger.warning(f"External validation failed: {e}")
        
        return validations
    
    async def _generate_executive_summary(
        self,
        parsed_results: Dict[str, Any],
        correlations: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate executive summary."""
        prompt = f"""Create a 2-3 sentence executive summary for business leadership.

KEY FINDINGS:
- Correlations: {len(correlations)} identified
- Root Causes: {len(root_causes)} analyzed
- Recommendations: {len(recommendations)} prioritized

TOP CORRELATION: {correlations[0].get('pattern', 'None') if correlations else 'None'}
TOP ROOT CAUSE: {root_causes[0].get('hypothesis', 'None') if root_causes else 'None'}
TOP RECOMMENDATION: {recommendations[0].get('action', 'None') if recommendations else 'None'}

Write a concise executive summary (2-3 sentences) that:
1. Highlights the most critical finding
2. States the primary root cause
3. Mentions the top strategic recommendation

Return ONLY the summary text, no JSON or markdown."""
        
        try:
            gemini_response = await self.gemini_client.generate(prompt, use_cache=True)
            return gemini_response['text'].strip()
        except Exception as e:
            self.logger.error(f"Failed to generate executive summary: {e}")
            return "Synthesis analysis completed with cross-functional insights identified."
    
    def _create_metrics_summary(self, parsed_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create key metrics summary."""
        summary = {}
        
        # Revenue metrics
        revenue_analysis = parsed_results.get('revenue', {}).get('analysis', {})
        if revenue_analysis:
            mrr_analysis = revenue_analysis.get('mrr_analysis', {})
            summary['revenue'] = {
                'current_mrr': mrr_analysis.get('current_mrr', 0),
                'mom_growth': mrr_analysis.get('mom_growth', 0),
                'churn_rate': revenue_analysis.get('churn_analysis', {}).get('current_rate', 0)
            }
        
        # Product metrics
        product_analysis = parsed_results.get('product', {}).get('analysis', {})
        if product_analysis:
            engagement = product_analysis.get('engagement_analysis', {})
            summary['product'] = {
                'dau': engagement.get('dau', 0),
                'mau': engagement.get('mau', 0),
                'dau_mau_ratio': engagement.get('dau_mau_ratio', 0)
            }
        
        # Support metrics
        support_analysis = parsed_results.get('support', {}).get('analysis', {})
        if support_analysis:
            volume = support_analysis.get('ticket_volume_analysis', {})
            satisfaction = support_analysis.get('satisfaction_analysis', {})
            summary['support'] = {
                'ticket_volume': volume.get('current_volume', 0),
                'csat_score': satisfaction.get('csat_score', 0),
                'avg_response_time': support_analysis.get('response_time_analysis', {}).get('avg_response_time_hours', 0)
            }
        
        return summary
    
    def _calculate_confidence(
        self,
        parsed_results: Dict[str, Any],
        correlations: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall confidence score."""
        confidence = 1.0
        
        # Reduce if missing agent results
        required_agents = ['revenue', 'product', 'support']
        missing_agents = [a for a in required_agents if a not in parsed_results]
        if missing_agents:
            confidence *= 0.8
        
        # Increase if strong correlations found
        high_confidence_correlations = [c for c in correlations if c.get('confidence', 0) > 0.8]
        if len(high_confidence_correlations) >= 2:
            confidence *= 1.0
        elif len(high_confidence_correlations) >= 1:
            confidence *= 0.95
        
        # Increase if root causes identified
        if len(root_causes) > 0:
            confidence *= 1.0
        else:
            confidence *= 0.9
        
        return max(0.0, min(1.0, round(confidence, 2)))
    
    def _hash_results(self, parsed_results: Dict[str, Any]) -> str:
        """Generate hash for results caching."""
        import hashlib
        data_str = json.dumps(parsed_results, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
