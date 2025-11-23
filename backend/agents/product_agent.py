"""
Production Product Agent with comprehensive product metrics analysis.

Features:
- DAU/WAU/MAU metrics
- Feature adoption rates
- User engagement trends
- Activation metrics (time-to-value)
- Product-qualified leads (PQLs)
- Retention cohorts by feature usage
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, validator
import numpy as np

from agents.base_agent import BaseAgent
from cache.cache_manager import CacheManager
from integrations.google_sheets import GoogleSheetsClient
from integrations.gemini_client import GeminiClient
from utils.config import config
from utils.logger import logger


# ============================================================================
# PYDANTIC MODELS FOR VALIDATION
# ============================================================================

class ProductDataPoint(BaseModel):
    """Individual product metrics data point."""
    week: int = Field(..., ge=1, le=52, description="Week number (1-52)")
    dau: Optional[int] = Field(None, ge=0, description="Daily Active Users")
    wau: Optional[int] = Field(None, ge=0, description="Weekly Active Users")
    mau: Optional[int] = Field(None, ge=0, description="Monthly Active Users")
    feature_adoptions: Optional[Dict[str, float]] = Field(None, description="Feature adoption rates")
    activation_time_days: Optional[float] = Field(None, ge=0, description="Average time to activation")
    pqls: Optional[int] = Field(None, ge=0, description="Product-Qualified Leads")
    engagement_score: Optional[float] = Field(None, ge=0, le=1, description="Engagement score (0-1)")


class ProductInput(BaseModel):
    """Input model for product analysis."""
    week_number: int = Field(..., ge=1, le=52, description="Week number for analysis")
    spreadsheet_id: Optional[str] = Field(None, description="Google Sheets spreadsheet ID")
    product_sheet: Optional[str] = Field("Product Metrics", description="Sheet name for product data")
    manual_data: Optional[Dict[str, Any]] = Field(None, description="Manual data override")
    analysis_type: str = Field("comprehensive", description="Type of analysis")
    
    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        """Validate analysis type."""
        allowed = ['comprehensive', 'engagement_only', 'adoption_only', 'activation_only']
        if v not in allowed:
            raise ValueError(f"analysis_type must be one of {allowed}")
        return v


class EngagementAnalysis(BaseModel):
    """Engagement metrics analysis."""
    dau: int = Field(..., ge=0)
    wau: int = Field(..., ge=0)
    mau: int = Field(..., ge=0)
    dau_mau_ratio: float = Field(..., ge=0, le=1, description="DAU/MAU ratio")
    wau_mau_ratio: float = Field(..., ge=0, le=1, description="WAU/MAU ratio")
    trend: str = Field(..., description="Trend: growing/declining/stable")


class FeatureAdoptionAnalysis(BaseModel):
    """Feature adoption analysis."""
    top_features: List[Dict[str, Any]] = Field(default_factory=list)
    adoption_trends: Dict[str, str] = Field(default_factory=dict)
    average_adoption_rate: float = Field(..., ge=0, le=1)


class ProductAnalysisOutput(BaseModel):
    """Complete product analysis output."""
    agent_id: str = Field(default_factory=lambda: f"product_agent_{uuid.uuid4().hex[:8]}")
    agent_type: str = "product"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = Field(..., ge=0, le=1)
    confidence_reasoning: str = Field(..., description="Explanation of confidence score")
    analysis: Dict[str, Any] = Field(..., description="Analysis results")
    data_citations: List[str] = Field(default_factory=list, description="Data source citations")
    data_freshness_hours: Optional[float] = Field(None, description="Hours since data last updated")


# ============================================================================
# PRODUCT AGENT IMPLEMENTATION
# ============================================================================

class ProductAgent(BaseAgent):
    """
    Production-grade Product Agent with comprehensive product metrics analysis.
    
    Features:
    - DAU/WAU/MAU metrics and ratios
    - Feature adoption tracking
    - User engagement trends
    - Activation metrics (time-to-value)
    - Product-qualified leads (PQLs)
    - Retention cohorts by feature usage
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Product Agent.
        
        Args:
            cache_manager: Cache manager instance
        """
        super().__init__("product", cache_manager)
        
        # Initialize integrations
        self.sheets_client = GoogleSheetsClient()
        self.gemini_client = GeminiClient(cache_manager)
        
        # Configuration
        self.prompt_cache_ttl_hours = 24
        self.agent_cache_ttl_hours = 1
        self.min_data_points = 4
        
        self.logger.info("ProductAgent initialized")
    
    async def analyze(self, context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Analyze product metrics with comprehensive analysis.
        
        Args:
            context: Input context containing:
                - week_number: Week number for analysis
                - spreadsheet_id: Optional Google Sheets ID
                - manual_data: Optional manual data override
                - analysis_type: Type of analysis
            session_id: Session identifier
            
        Returns:
            Analysis result with:
            - response: JSON string of analysis
            - confidence_score: Confidence level (0-1)
            - metadata: Additional metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Validate and parse input
            try:
                product_input = ProductInput(**context)
            except Exception as e:
                self.logger.error(f"Input validation failed: {e}")
                raise ValueError(f"Invalid input: {e}")
            
            # Step 2: Fetch data from Google Sheets or use manual data
            product_data = await self._fetch_product_data(product_input)
            
            # Step 3: Validate data quality
            data_quality = self._validate_data_quality(product_data)
            
            # Step 4: Check agent-level cache
            cache_context = {
                'week_number': product_input.week_number,
                'analysis_type': product_input.analysis_type,
                'data_hash': self._hash_data(product_data)
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
                    'metadata': {
                        'cache_hit': True,
                        'data_quality': data_quality
                    }
                }
            
            self.logger.info("Agent cache MISS - generating new analysis")
            
            # Step 5: Perform statistical analysis
            statistical_analysis = self._perform_statistical_analysis(product_data)
            
            # Step 6: Generate Gemini analysis
            gemini_analysis = await self._generate_gemini_analysis(
                product_data=product_data,
                statistical_analysis=statistical_analysis,
                week_number=product_input.week_number,
                analysis_type=product_input.analysis_type
            )
            
            # Step 7: Combine analyses
            combined_analysis = self._combine_analyses(
                statistical_analysis=statistical_analysis,
                gemini_analysis=gemini_analysis,
                product_data=product_data,
                week_number=product_input.week_number
            )
            
            # Step 8: Calculate confidence
            confidence_result = self._calculate_confidence(
                product_data=product_data,
                data_quality=data_quality,
                analysis=combined_analysis
            )
            
            # Step 9: Build final output
            output = ProductAnalysisOutput(
                confidence=confidence_result['score'],
                confidence_reasoning=confidence_result['reasoning'],
                analysis=combined_analysis,
                data_citations=self._generate_citations(product_input, product_data),
                data_freshness_hours=data_quality.get('freshness_hours')
            )
            
            output_dict = output.dict()
            output_json = json.dumps(output_dict, indent=2)
            
            # Step 10: Cache the response
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.cache_manager.cache_agent_response(
                agent_type=self.agent_type,
                context=cache_context,
                response=output_json,
                confidence_score=confidence_result['score'],
                execution_time_ms=execution_time_ms,
                ttl_hours=self.agent_cache_ttl_hours
            )
            
            # Step 11: Log metrics
            if gemini_analysis.get('tokens_input'):
                self.cache_manager.record_metric(
                    metric_name='gemini_tokens_input',
                    metric_value=gemini_analysis['tokens_input'],
                    agent_type=self.agent_type,
                    session_id=session_id
                )
            
            self.logger.info(
                f"Product analysis completed",
                extra={
                    'week_number': product_input.week_number,
                    'confidence': confidence_result['score'],
                    'execution_time_ms': execution_time_ms
                }
            )
            
            return {
                'response': output_json,
                'confidence_score': confidence_result['score'],
                'cached': False,
                'execution_time_ms': execution_time_ms,
                'input_tokens': gemini_analysis.get('tokens_input', 0),
                'output_tokens': gemini_analysis.get('tokens_output', 0),
                'cached_tokens': 0,
                'metadata': {
                    'data_quality': data_quality,
                    'agent_id': output_dict['agent_id']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in product analysis: {e}", exc_info=True)
            raise
    
    async def _fetch_product_data(self, product_input: ProductInput) -> Dict[str, Any]:
        """Fetch product data from Google Sheets or use manual data."""
        if product_input.manual_data:
            self.logger.info("Using manual data")
            return product_input.manual_data
        
        if not product_input.spreadsheet_id:
            raise ValueError("Either spreadsheet_id or manual_data must be provided")
        
        if not self.sheets_client.client:
            raise RuntimeError("Google Sheets client not initialized")
        
        try:
            self.logger.info(f"Fetching product data from Google Sheets")
            
            product_rows = self.sheets_client.get_sheet_data(
                spreadsheet_id=product_input.spreadsheet_id,
                sheet_name=product_input.product_sheet
            )
            
            product_data = self._parse_sheet_data(product_rows)
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error fetching from Google Sheets: {e}", exc_info=True)
            raise
    
    def _parse_sheet_data(self, product_rows: List[List[Any]]) -> Dict[str, Any]:
        """Parse Google Sheets rows into structured data."""
        if not product_rows or len(product_rows) < 2:
            raise ValueError("Insufficient product data in sheet")
        
        headers = [str(h).lower().strip() for h in product_rows[0]]
        
        records = []
        for row in product_rows[1:]:
            if len(row) < len(headers):
                continue
            
            record = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else None
                
                # Parse numeric values
                if header in ['week', 'dau', 'wau', 'mau', 'pqls']:
                    try:
                        value = int(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                elif header in ['activation_time_days', 'engagement_score']:
                    try:
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                elif header == 'feature_adoptions':
                    try:
                        value = json.loads(value) if value else {}
                    except (json.JSONDecodeError, TypeError):
                        value = {}
                else:
                    value = str(value) if value else None
                
                record[header] = value
            
            try:
                validated = ProductDataPoint(**record)
                records.append(validated.dict())
            except Exception as e:
                self.logger.warning(f"Skipping invalid record: {e}")
                continue
        
        return {
            'records': records,
            'total_records': len(records)
        }
    
    def _validate_data_quality(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data quality and freshness."""
        records = product_data.get('records', [])
        
        quality = {
            'completeness_score': 1.0,
            'freshness_hours': None,
            'anomalies_detected': [],
            'missing_fields': []
        }
        
        if len(records) < self.min_data_points:
            quality['completeness_score'] *= 0.7
            quality['missing_fields'].append(f"Insufficient data points: {len(records)} < {self.min_data_points}")
        
        # Check for required fields
        required_fields = ['week', 'dau', 'wau', 'mau']
        for record in records:
            for field in required_fields:
                if field not in record or record[field] is None:
                    quality['missing_fields'].append(f"Missing {field} in record")
                    quality['completeness_score'] *= 0.9
        
        # Detect anomalies in engagement metrics
        if len(records) >= 2:
            dau_values = [r['dau'] for r in records if r.get('dau')]
            if dau_values:
                mean_dau = np.mean(dau_values)
                std_dau = np.std(dau_values)
                
                for record in records:
                    if record.get('dau'):
                        z_score = abs((record['dau'] - mean_dau) / std_dau) if std_dau > 0 else 0
                        if z_score > 2.5:
                            quality['anomalies_detected'].append({
                                'type': 'dau_outlier',
                                'week': record.get('week'),
                                'value': record['dau'],
                                'z_score': z_score
                            })
        
        quality['completeness_score'] = max(0.0, min(1.0, quality['completeness_score']))
        return quality
    
    def _perform_statistical_analysis(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis on product data."""
        records = product_data.get('records', [])
        
        if len(records) < 2:
            return {
                'engagement_trend': 'insufficient_data',
                'adoption_rate': None
            }
        
        sorted_records = sorted(records, key=lambda x: x.get('week', 0))
        
        # Engagement Analysis
        latest = sorted_records[-1]
        dau = latest.get('dau', 0)
        wau = latest.get('wau', 0)
        mau = latest.get('mau', 0)
        
        dau_mau_ratio = dau / mau if mau > 0 else 0
        wau_mau_ratio = wau / mau if mau > 0 else 0
        
        # Calculate trends
        dau_values = [r.get('dau', 0) for r in sorted_records]
        dau_trend = 'stable'
        if len(dau_values) >= 2:
            recent_avg = np.mean(dau_values[-2:])
            previous_avg = np.mean(dau_values[-4:-2]) if len(dau_values) >= 4 else dau_values[0]
            if recent_avg > previous_avg * 1.05:
                dau_trend = 'growing'
            elif recent_avg < previous_avg * 0.95:
                dau_trend = 'declining'
        
        # Feature Adoption
        all_adoptions = []
        for record in sorted_records:
            if record.get('feature_adoptions'):
                all_adoptions.extend(record['feature_adoptions'].values())
        
        avg_adoption_rate = np.mean(all_adoptions) if all_adoptions else 0
        
        # Activation Metrics
        activation_times = [r.get('activation_time_days') for r in sorted_records if r.get('activation_time_days')]
        avg_activation_time = np.mean(activation_times) if activation_times else None
        
        # PQLs
        pql_values = [r.get('pqls', 0) for r in sorted_records]
        current_pqls = pql_values[-1] if pql_values else 0
        pql_trend = 'stable'
        if len(pql_values) >= 2:
            if pql_values[-1] > pql_values[-2] * 1.1:
                pql_trend = 'growing'
            elif pql_values[-1] < pql_values[-2] * 0.9:
                pql_trend = 'declining'
        
        return {
            'current_dau': dau,
            'current_wau': wau,
            'current_mau': mau,
            'dau_mau_ratio': dau_mau_ratio,
            'wau_mau_ratio': wau_mau_ratio,
            'engagement_trend': dau_trend,
            'avg_adoption_rate': avg_adoption_rate,
            'avg_activation_time': avg_activation_time,
            'current_pqls': current_pqls,
            'pql_trend': pql_trend,
            'data_points': len(records)
        }
    
    async def _generate_gemini_analysis(
        self,
        product_data: Dict[str, Any],
        statistical_analysis: Dict[str, Any],
        week_number: int,
        analysis_type: str
    ) -> Dict[str, Any]:
        """Generate analysis using Gemini."""
        prompt = self._build_structured_prompt(
            product_data=product_data,
            statistical_analysis=statistical_analysis,
            week_number=week_number,
            analysis_type=analysis_type
        )
        
        cached_prompt = self.cache_manager.get_cached_prompt(
            prompt=prompt,
            model=self.gemini_client.model_name
        )
        
        if cached_prompt:
            self.logger.info("Prompt cache HIT")
            try:
                return {
                    'analysis': json.loads(cached_prompt['response']),
                    'tokens_input': cached_prompt.get('tokens_input', 0),
                    'tokens_output': cached_prompt.get('tokens_output', 0),
                    'cached': True
                }
            except json.JSONDecodeError:
                self.logger.warning("Cached response is not valid JSON, regenerating")
        
        self.logger.info("Prompt cache MISS - calling Gemini API")
        
        gemini_response = None
        try:
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
            
            analysis = json.loads(response_text)
            
            # Cache with custom TTL
            self.cache_manager.cache_prompt(
                prompt=prompt,
                response=gemini_response['text'],
                model=self.gemini_client.model_name,
                tokens_input=gemini_response.get('tokens_input', 0),
                tokens_output=gemini_response.get('tokens_output', 0),
                ttl_hours=self.prompt_cache_ttl_hours
            )
            
            return {
                'analysis': analysis,
                'tokens_input': gemini_response.get('tokens_input', 0),
                'tokens_output': gemini_response.get('tokens_output', 0),
                'cached': False
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gemini JSON response: {e}")
            return {
                'analysis': self._create_fallback_analysis(statistical_analysis),
                'tokens_input': gemini_response.get('tokens_input', 0) if gemini_response else 0,
                'tokens_output': gemini_response.get('tokens_output', 0) if gemini_response else 0,
                'cached': False
            }
        except Exception as e:
            self.logger.error(f"Gemini API call failed: {e}", exc_info=True)
            raise
    
    def _build_structured_prompt(
        self,
        product_data: Dict[str, Any],
        statistical_analysis: Dict[str, Any],
        week_number: int,
        analysis_type: str
    ) -> str:
        """Build structured prompt for Gemini."""
        prompt = f"""You are a SaaS product analyst. Analyze the following product metrics data for Week {week_number} and provide a comprehensive analysis in JSON format.

PRODUCT DATA:
{json.dumps(product_data, indent=2)}

STATISTICAL ANALYSIS:
{json.dumps(statistical_analysis, indent=2)}

REQUIRED OUTPUT FORMAT (JSON):
{{
  "engagement_analysis": {{
    "dau": <number>,
    "wau": <number>,
    "mau": <number>,
    "dau_mau_ratio": <decimal 0-1>,
    "wau_mau_ratio": <decimal 0-1>,
    "trend": "<growing|declining|stable>"
  }},
  "feature_adoption": {{
    "top_features": [
      {{"feature": "<name>", "adoption_rate": <decimal>, "trend": "<string>"}}
    ],
    "average_adoption_rate": <decimal 0-1>,
    "adoption_trends": {{
      "<feature_name>": "<growing|declining|stable>"
    }}
  }},
  "activation_metrics": {{
    "avg_time_to_value_days": <number>,
    "trend": "<improving|worsening|stable>",
    "cohort_breakdown": {{
      "<cohort>": {{"avg_days": <number>, "users": <number>}}
    }}
  }},
  "pql_analysis": {{
    "current_pqls": <number>,
    "trend": "<growing|declining|stable>",
    "conversion_rate": <decimal 0-1>
  }},
  "retention_cohorts": {{
    "<feature>": {{
      "retention_rate": <decimal 0-1>,
      "users": <number>
    }}
  }},
  "key_insights": [
    "<insight 1>",
    "<insight 2>"
  ],
  "recommendations": [
    {{
      "action": "<actionable recommendation>",
      "priority": "<high|medium|low>",
      "expected_impact": "<quantified impact>"
    }}
  ],
  "risk_flags": [],
  "anomalies": []
}}

INSTRUCTIONS:
1. Use the statistical analysis provided to inform your insights
2. Focus on engagement trends, feature adoption, and activation metrics
3. Provide specific, actionable recommendations
4. Flag any anomalies or risks
5. Return ONLY valid JSON, no markdown or explanations

ANALYSIS TYPE: {analysis_type}

Now provide the analysis for Week {week_number}:"""
        
        return prompt
    
    def _combine_analyses(
        self,
        statistical_analysis: Dict[str, Any],
        gemini_analysis: Dict[str, Any],
        product_data: Dict[str, Any],
        week_number: int
    ) -> Dict[str, Any]:
        """Combine statistical and Gemini analyses."""
        gemini_result = gemini_analysis.get('analysis', {})
        
        combined = {
            'engagement_analysis': gemini_result.get('engagement_analysis', {
                'dau': statistical_analysis.get('current_dau', 0),
                'wau': statistical_analysis.get('current_wau', 0),
                'mau': statistical_analysis.get('current_mau', 0),
                'dau_mau_ratio': statistical_analysis.get('dau_mau_ratio', 0),
                'wau_mau_ratio': statistical_analysis.get('wau_mau_ratio', 0),
                'trend': statistical_analysis.get('engagement_trend', 'stable')
            }),
            'feature_adoption': gemini_result.get('feature_adoption', {
                'top_features': [],
                'average_adoption_rate': statistical_analysis.get('avg_adoption_rate', 0),
                'adoption_trends': {}
            }),
            'activation_metrics': gemini_result.get('activation_metrics', {
                'avg_time_to_value_days': statistical_analysis.get('avg_activation_time'),
                'trend': 'stable',
                'cohort_breakdown': {}
            }),
            'pql_analysis': gemini_result.get('pql_analysis', {
                'current_pqls': statistical_analysis.get('current_pqls', 0),
                'trend': statistical_analysis.get('pql_trend', 'stable'),
                'conversion_rate': 0
            }),
            'retention_cohorts': gemini_result.get('retention_cohorts', {}),
            'key_insights': gemini_result.get('key_insights', []),
            'recommendations': gemini_result.get('recommendations', []),
            'risk_flags': gemini_result.get('risk_flags', []),
            'anomalies': gemini_result.get('anomalies', [])
        }
        
        return combined
    
    def _calculate_confidence(
        self,
        product_data: Dict[str, Any],
        data_quality: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate confidence score with reasoning."""
        confidence = 1.0
        reasons = []
        
        completeness = data_quality.get('completeness_score', 1.0)
        confidence *= completeness
        if completeness < 0.9:
            reasons.append(f"Data completeness: {completeness:.0%}")
        
        records = product_data.get('records', [])
        if len(records) >= 8:
            confidence *= 1.0
            reasons.append("Sufficient historical data (8+ weeks)")
        elif len(records) >= 4:
            confidence *= 0.9
            reasons.append("Limited historical data (4-7 weeks)")
        else:
            confidence *= 0.7
            reasons.append("Insufficient historical data (<4 weeks)")
        
        # Check for engagement metrics consistency
        dau_values = [r.get('dau') for r in records if r.get('dau')]
        if len(dau_values) >= 4:
            std_dev = np.std(dau_values)
            mean_val = np.mean(dau_values)
            cv = std_dev / mean_val if mean_val > 0 else 1.0
            if cv < 0.2:
                confidence *= 1.0
                reasons.append("High engagement data consistency")
            elif cv < 0.4:
                confidence *= 0.95
            else:
                confidence *= 0.85
                reasons.append("High engagement data variability")
        
        required_sections = ['engagement_analysis', 'feature_adoption', 'key_insights']
        missing_sections = [s for s in required_sections if s not in analysis or not analysis[s]]
        if missing_sections:
            confidence *= 0.8
            reasons.append(f"Missing analysis sections: {', '.join(missing_sections)}")
        
        anomalies = data_quality.get('anomalies_detected', [])
        if len(anomalies) > 2:
            confidence *= 0.85
            reasons.append(f"Multiple data anomalies detected ({len(anomalies)})")
        
        confidence = max(0.0, min(1.0, confidence))
        reasoning = "; ".join(reasons) if reasons else "High confidence: All quality checks passed"
        
        return {
            'score': round(confidence, 2),
            'reasoning': reasoning
        }
    
    def _generate_citations(
        self,
        product_input: ProductInput,
        product_data: Dict[str, Any]
    ) -> List[str]:
        """Generate data citations."""
        citations = []
        
        if product_input.spreadsheet_id:
            citations.append(
                f"Week {product_input.week_number} product metrics from Sheets '{product_input.product_sheet}'"
            )
        else:
            citations.append("Data from manual input")
        
        records = product_data.get('records', [])
        if records:
            citations.append(f"Analysis based on {len(records)} data points")
        
        return citations
    
    def _hash_data(self, product_data: Dict[str, Any]) -> str:
        """Generate hash for data caching."""
        import hashlib
        data_str = json.dumps(product_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _create_fallback_analysis(self, statistical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis when Gemini fails."""
        return {
            'engagement_analysis': {
                'dau': statistical_analysis.get('current_dau', 0),
                'wau': statistical_analysis.get('current_wau', 0),
                'mau': statistical_analysis.get('current_mau', 0),
                'dau_mau_ratio': statistical_analysis.get('dau_mau_ratio', 0),
                'wau_mau_ratio': statistical_analysis.get('wau_mau_ratio', 0),
                'trend': statistical_analysis.get('engagement_trend', 'stable')
            },
            'feature_adoption': {
                'top_features': [],
                'average_adoption_rate': statistical_analysis.get('avg_adoption_rate', 0),
                'adoption_trends': {}
            },
            'key_insights': [
                'Analysis generated from statistical data only',
                'Gemini analysis unavailable'
            ],
            'recommendations': [],
            'risk_flags': ['Gemini analysis failed - using statistical fallback']
        }
