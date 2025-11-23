"""
Production Revenue Agent with comprehensive analysis capabilities.

Features:
- Data validation with Pydantic models
- Google Sheets integration via MCP
- Enhanced analysis (MRR, churn, ARPU, forecasting, anomalies)
- Confidence scoring with reasoning
- Gemini prompt engineering with structured JSON responses
- Aggressive caching (prompt: 24h, agent: 1h)
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field

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

class RevenueDataPoint(BaseModel):
    """Individual revenue data point."""
    week: int = Field(..., ge=1, le=52, description="Week number (1-52)")
    mrr: float = Field(..., ge=0, description="Monthly Recurring Revenue")
    new_customers: int = Field(..., ge=0, description="New customers acquired")
    churned: int = Field(..., ge=0, description="Customers churned")
    arpu: Optional[float] = Field(None, ge=0, description="Average Revenue Per User")
    customer_tier: Optional[str] = Field(None, description="Customer tier (enterprise/smb)")
    
    @validator('churned')
    def validate_churned(cls, v, values):
        """Ensure churned doesn't exceed reasonable limits."""
        if 'new_customers' in values and v > values['new_customers'] * 2:
            raise ValueError("Churned customers exceeds reasonable threshold")
        return v


class RevenueInput(BaseModel):
    """Input model for revenue analysis."""
    week_number: int = Field(..., ge=1, le=52, description="Week number for analysis")
    spreadsheet_id: Optional[str] = Field(None, description="Google Sheets spreadsheet ID")
    revenue_sheet: Optional[str] = Field("Revenue", description="Sheet name for revenue data")
    churn_sheet: Optional[str] = Field("Churn", description="Sheet name for churn data")
    manual_data: Optional[Dict[str, Any]] = Field(None, description="Manual data override")
    analysis_type: str = Field("comprehensive", description="Type of analysis")
    
    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        """Validate analysis type."""
        allowed = ['comprehensive', 'mrr_only', 'churn_only', 'arpu_only']
        if v not in allowed:
            raise ValueError(f"analysis_type must be one of {allowed}")
        return v


class MRRAnalysis(BaseModel):
    """MRR analysis results."""
    current_mrr: float = Field(..., ge=0)
    wow_growth: float = Field(..., description="Week-over-week growth rate")
    mom_growth: float = Field(..., description="Month-over-month growth rate")
    trend: str = Field(..., description="Trend direction: accelerating/decelerating/stable")
    forecast_next_month: float = Field(..., ge=0)


class ChurnAnalysis(BaseModel):
    """Churn analysis results."""
    current_rate: float = Field(..., ge=0, le=1, description="Current churn rate (0-1)")
    change_from_previous: float = Field(..., description="Change from previous period")
    severity: str = Field(..., description="Severity: low/medium/high/critical")
    cohort_breakdown: Dict[str, Any] = Field(default_factory=dict)


class RevenueAnalysisOutput(BaseModel):
    """Complete revenue analysis output."""
    agent_id: str = Field(default_factory=lambda: f"revenue_agent_{uuid.uuid4().hex[:8]}")
    agent_type: str = "revenue"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = Field(..., ge=0, le=1)
    confidence_reasoning: str = Field(..., description="Explanation of confidence score")
    analysis: Dict[str, Any] = Field(..., description="Analysis results")
    data_citations: List[str] = Field(default_factory=list, description="Data source citations")
    data_freshness_hours: Optional[float] = Field(None, description="Hours since data last updated")


# ============================================================================
# REVENUE AGENT IMPLEMENTATION
# ============================================================================

class RevenueAgent(BaseAgent):
    """
    Production-grade Revenue Agent with comprehensive analysis capabilities.
    
    Features:
    - Data validation with Pydantic
    - Google Sheets integration
    - MRR growth and trend analysis
    - Cohort-based churn analysis
    - ARPU segmentation
    - Revenue forecasting
    - Anomaly detection
    - Confidence scoring with reasoning
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Revenue Agent.
        
        Args:
            cache_manager: Cache manager instance
        """
        super().__init__("revenue", cache_manager)
        
        # Initialize integrations
        self.sheets_client = GoogleSheetsClient()
        self.gemini_client = GeminiClient(cache_manager)
        
        # Configuration
        self.prompt_cache_ttl_hours = 24  # Aggressive prompt caching
        self.agent_cache_ttl_hours = 1   # 1 hour agent cache
        self.min_data_points = 4  # Minimum weeks for reliable analysis
        
        self.logger.info("RevenueAgent initialized")
    
    async def analyze(self, context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Analyze revenue data with comprehensive metrics.
        
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
                revenue_input = RevenueInput(**context)
            except Exception as e:
                self.logger.error(f"Input validation failed: {e}")
                raise ValueError(f"Invalid input: {e}")
            
            # Step 2: Fetch data from Google Sheets or use manual data
            revenue_data = await self._fetch_revenue_data(revenue_input)
            
            # Step 3: Validate data quality and freshness
            data_quality = self._validate_data_quality(revenue_data)
            
            # Step 4: Check agent-level cache
            cache_context = {
                'week_number': revenue_input.week_number,
                'analysis_type': revenue_input.analysis_type,
                'data_hash': self._hash_data(revenue_data)
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
            statistical_analysis = self._perform_statistical_analysis(revenue_data)
            
            # Step 6: Generate Gemini analysis with structured prompt
            gemini_analysis = await self._generate_gemini_analysis(
                revenue_data=revenue_data,
                statistical_analysis=statistical_analysis,
                week_number=revenue_input.week_number,
                analysis_type=revenue_input.analysis_type
            )
            
            # Step 7: Combine analyses and format output
            combined_analysis = self._combine_analyses(
                statistical_analysis=statistical_analysis,
                gemini_analysis=gemini_analysis,
                revenue_data=revenue_data,
                week_number=revenue_input.week_number
            )
            
            # Step 8: Calculate confidence with reasoning
            confidence_result = self._calculate_confidence(
                revenue_data=revenue_data,
                data_quality=data_quality,
                analysis=combined_analysis
            )
            
            # Step 9: Build final output
            output = RevenueAnalysisOutput(
                confidence=confidence_result['score'],
                confidence_reasoning=confidence_result['reasoning'],
                analysis=combined_analysis,
                data_citations=self._generate_citations(revenue_input, revenue_data),
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
            
            # Step 11: Log Gemini call metrics
            if gemini_analysis.get('tokens_input'):
                self.cache_manager.record_metric(
                    metric_name='gemini_tokens_input',
                    metric_value=gemini_analysis['tokens_input'],
                    agent_type=self.agent_type,
                    session_id=session_id
                )
            
            self.logger.info(
                f"Revenue analysis completed",
                extra={
                    'week_number': revenue_input.week_number,
                    'confidence': confidence_result['score'],
                    'execution_time_ms': execution_time_ms,
                    'cached': False
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
            self.logger.error(
                f"Error in revenue analysis: {e}",
                exc_info=True
            )
            raise
    
    async def _fetch_revenue_data(self, revenue_input: RevenueInput) -> Dict[str, Any]:
        """
        Fetch revenue data from Google Sheets or use manual data.
        
        Args:
            revenue_input: Validated input
            
        Returns:
            Revenue data dictionary
        """
        # Use manual data if provided
        if revenue_input.manual_data:
            self.logger.info("Using manual data")
            return revenue_input.manual_data
        
        # Fetch from Google Sheets
        if not revenue_input.spreadsheet_id:
            raise ValueError("Either spreadsheet_id or manual_data must be provided")
        
        if not self.sheets_client.client:
            raise RuntimeError("Google Sheets client not initialized")
        
        try:
            self.logger.info(f"Fetching data from Google Sheets: {revenue_input.spreadsheet_id}")
            
            # Fetch revenue data
            revenue_rows = self.sheets_client.get_sheet_data(
                spreadsheet_id=revenue_input.spreadsheet_id,
                sheet_name=revenue_input.revenue_sheet
            )
            
            # Fetch churn data if available
            churn_rows = []
            try:
                churn_rows = self.sheets_client.get_sheet_data(
                    spreadsheet_id=revenue_input.spreadsheet_id,
                    sheet_name=revenue_input.churn_sheet
                )
            except Exception as e:
                self.logger.warning(f"Could not fetch churn data: {e}")
            
            # Parse rows into structured data
            revenue_data = self._parse_sheet_data(revenue_rows, churn_rows)
            
            return revenue_data
            
        except Exception as e:
            self.logger.error(f"Error fetching from Google Sheets: {e}", exc_info=True)
            raise
    
    def _parse_sheet_data(self, revenue_rows: List[List[Any]], 
                         churn_rows: List[List[Any]]) -> Dict[str, Any]:
        """
        Parse Google Sheets rows into structured data.
        
        Args:
            revenue_rows: Revenue sheet rows
            churn_rows: Churn sheet rows
            
        Returns:
            Structured revenue data
        """
        if not revenue_rows or len(revenue_rows) < 2:
            raise ValueError("Insufficient revenue data in sheet")
        
        # Assume first row is header
        headers = [str(h).lower().strip() for h in revenue_rows[0]]
        
        records = []
        for row in revenue_rows[1:]:
            if len(row) < len(headers):
                continue
            
            record = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else None
                
                # Try to parse numeric values
                if header in ['week', 'mrr', 'arpu']:
                    try:
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                elif header in ['new_customers', 'churned']:
                    try:
                        value = int(value) if value else 0
                    except (ValueError, TypeError):
                        value = 0
                else:
                    value = str(value) if value else None
                
                record[header] = value
            
            # Validate record
            try:
                validated = RevenueDataPoint(**record)
                records.append(validated.dict())
            except Exception as e:
                self.logger.warning(f"Skipping invalid record: {e}")
                continue
        
        return {
            'records': records,
            'total_records': len(records)
        }
    
    def _validate_data_quality(self, revenue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data quality and freshness.
        
        Args:
            revenue_data: Revenue data
            
        Returns:
            Data quality metrics
        """
        records = revenue_data.get('records', [])
        
        quality = {
            'completeness_score': 1.0,
            'freshness_hours': None,
            'anomalies_detected': [],
            'missing_fields': []
        }
        
        # Check completeness
        if len(records) < self.min_data_points:
            quality['completeness_score'] *= 0.7
            quality['missing_fields'].append(f"Insufficient data points: {len(records)} < {self.min_data_points}")
        
        # Check for required fields
        required_fields = ['week', 'mrr', 'new_customers', 'churned']
        for record in records:
            for field in required_fields:
                if field not in record or record[field] is None:
                    quality['missing_fields'].append(f"Missing {field} in record")
                    quality['completeness_score'] *= 0.9
        
        # Detect anomalies
        if len(records) >= 2:
            mrr_values = [r['mrr'] for r in records if r.get('mrr')]
            if mrr_values:
                mean_mrr = np.mean(mrr_values)
                std_mrr = np.std(mrr_values)
                
                for i, record in enumerate(records):
                    if record.get('mrr'):
                        z_score = abs((record['mrr'] - mean_mrr) / std_mrr) if std_mrr > 0 else 0
                        if z_score > 2.5:  # Significant outlier
                            quality['anomalies_detected'].append({
                                'type': 'mrr_outlier',
                                'week': record.get('week'),
                                'value': record['mrr'],
                                'z_score': z_score
                            })
        
        quality['completeness_score'] = max(0.0, min(1.0, quality['completeness_score']))
        
        return quality
    
    def _perform_statistical_analysis(self, revenue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform statistical analysis on revenue data.
        
        Args:
            revenue_data: Revenue data
            
        Returns:
            Statistical analysis results
        """
        records = revenue_data.get('records', [])
        
        if len(records) < 2:
            return {
                'mrr_trend': 'insufficient_data',
                'churn_rate': None,
                'arpu_trend': None
            }
        
        # Sort by week
        sorted_records = sorted(records, key=lambda x: x.get('week', 0))
        
        # MRR Analysis
        mrr_values = [r['mrr'] for r in sorted_records if r.get('mrr')]
        current_mrr = mrr_values[-1] if mrr_values else 0
        
        wow_growth = 0.0
        if len(mrr_values) >= 2:
            wow_growth = (mrr_values[-1] - mrr_values[-2]) / mrr_values[-2] if mrr_values[-2] > 0 else 0
        
        mom_growth = 0.0
        if len(mrr_values) >= 5:  # Approximate month (4-5 weeks)
            mom_growth = (mrr_values[-1] - mrr_values[-5]) / mrr_values[-5] if mrr_values[-5] > 0 else 0
        
        # Churn Analysis
        total_churned = sum(r.get('churned', 0) for r in sorted_records[-4:])  # Last 4 weeks
        total_new = sum(r.get('new_customers', 0) for r in sorted_records[-4:])
        churn_rate = total_churned / total_new if total_new > 0 else 0
        
        # ARPU Analysis
        arpu_values = [r['arpu'] for r in sorted_records if r.get('arpu')]
        avg_arpu = np.mean(arpu_values) if arpu_values else None
        
        return {
            'current_mrr': current_mrr,
            'wow_growth': wow_growth,
            'mom_growth': mom_growth,
            'churn_rate': churn_rate,
            'avg_arpu': avg_arpu,
            'data_points': len(records)
        }
    
    async def _generate_gemini_analysis(
        self,
        revenue_data: Dict[str, Any],
        statistical_analysis: Dict[str, Any],
        week_number: int,
        analysis_type: str
    ) -> Dict[str, Any]:
        """
        Generate analysis using Gemini with structured prompts.
        
        Args:
            revenue_data: Revenue data
            statistical_analysis: Statistical analysis results
            week_number: Week number
            analysis_type: Type of analysis
            
        Returns:
            Gemini analysis results
        """
        # Build structured prompt with few-shot examples
        prompt = self._build_structured_prompt(
            revenue_data=revenue_data,
            statistical_analysis=statistical_analysis,
            week_number=week_number,
            analysis_type=analysis_type
        )
        
        # Check prompt cache
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
        
        # Call Gemini API
        gemini_response = None
        try:
            gemini_response = await self.gemini_client.generate(prompt, use_cache=True)
            
            # Parse JSON response
            response_text = gemini_response['text']
            
            # Extract JSON from response (handle markdown code blocks)
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
            # Return fallback analysis
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
        revenue_data: Dict[str, Any],
        statistical_analysis: Dict[str, Any],
        week_number: int,
        analysis_type: str
    ) -> str:
        """
        Build structured prompt with few-shot examples for Gemini.
        
        Args:
            revenue_data: Revenue data
            statistical_analysis: Statistical analysis
            week_number: Week number
            analysis_type: Type of analysis
            
        Returns:
            Structured prompt string
        """
        prompt = f"""You are a SaaS revenue analyst. Analyze the following revenue data for Week {week_number} and provide a comprehensive analysis in JSON format.

REVENUE DATA:
{json.dumps(revenue_data, indent=2)}

STATISTICAL ANALYSIS:
{json.dumps(statistical_analysis, indent=2)}

REQUIRED OUTPUT FORMAT (JSON):
{{
  "mrr_analysis": {{
    "current_mrr": <number>,
    "wow_growth": <decimal 0-1>,
    "mom_growth": <decimal 0-1>,
    "trend": "<accelerating|decelerating|stable>",
    "forecast_next_month": <number>
  }},
  "churn_analysis": {{
    "current_rate": <decimal 0-1>,
    "change_from_previous": <decimal>,
    "severity": "<low|medium|high|critical>",
    "cohort_breakdown": {{
      "enterprise": {{"rate": <decimal>, "trend": "<string>"}},
      "smb": {{"rate": <decimal>, "trend": "<string>"}}
    }}
  }},
  "arpu_analysis": {{
    "current_arpu": <number>,
    "segmentation": {{
      "by_tier": {{
        "enterprise": <number>,
        "smb": <number>
      }}
    }},
    "trend": "<increasing|decreasing|stable>"
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
  "risk_flags": [
    "<risk flag if any>"
  ],
  "anomalies": [
    {{
      "type": "<outlier type>",
      "description": "<description>",
      "severity": "<low|medium|high>"
    }}
  ]
}}

FEW-SHOT EXAMPLE:
Input: MRR growing 15% WoW, churn at 3.2%
Output: {{
  "mrr_analysis": {{
    "current_mrr": 1250000,
    "wow_growth": 0.015,
    "mom_growth": 0.12,
    "trend": "accelerating",
    "forecast_next_month": 1400000
  }},
  "churn_analysis": {{
    "current_rate": 0.032,
    "change_from_previous": -0.009,
    "severity": "low",
    "cohort_breakdown": {{}}
  }},
  "key_insights": [
    "Enterprise segment driving 60% of growth",
    "Annual contracts showing 2.1% churn vs 4.5% monthly"
  ],
  "recommendations": [
    {{
      "action": "Increase enterprise sales capacity",
      "priority": "high",
      "expected_impact": "+$150K MRR in Q1"
    }}
  ],
  "risk_flags": []
}}

INSTRUCTIONS:
1. Use the statistical analysis provided to inform your insights
2. Ensure all numbers are grounded in the data
3. Provide specific, actionable recommendations
4. Flag any anomalies or risks
5. Return ONLY valid JSON, no markdown or explanations
6. Include data citations in your insights where relevant

ANALYSIS TYPE: {analysis_type}

Now provide the analysis for Week {week_number}:"""
        
        return prompt
    
    def _combine_analyses(
        self,
        statistical_analysis: Dict[str, Any],
        gemini_analysis: Dict[str, Any],
        revenue_data: Dict[str, Any],
        week_number: int
    ) -> Dict[str, Any]:
        """
        Combine statistical and Gemini analyses into final output.
        
        Args:
            statistical_analysis: Statistical analysis
            gemini_analysis: Gemini analysis
            revenue_data: Revenue data
            week_number: Week number
            
        Returns:
            Combined analysis dictionary
        """
        gemini_result = gemini_analysis.get('analysis', {})
        
        # Merge analyses, preferring Gemini insights but validating with statistics
        combined = {
            'mrr_analysis': gemini_result.get('mrr_analysis', {
                'current_mrr': statistical_analysis.get('current_mrr', 0),
                'wow_growth': statistical_analysis.get('wow_growth', 0),
                'mom_growth': statistical_analysis.get('mom_growth', 0),
                'trend': 'stable',
                'forecast_next_month': statistical_analysis.get('current_mrr', 0) * 1.1
            }),
            'churn_analysis': gemini_result.get('churn_analysis', {
                'current_rate': statistical_analysis.get('churn_rate', 0),
                'change_from_previous': 0,
                'severity': 'low',
                'cohort_breakdown': {}
            }),
            'arpu_analysis': gemini_result.get('arpu_analysis', {
                'current_arpu': statistical_analysis.get('avg_arpu'),
                'segmentation': {},
                'trend': 'stable'
            }),
            'key_insights': gemini_result.get('key_insights', []),
            'recommendations': gemini_result.get('recommendations', []),
            'risk_flags': gemini_result.get('risk_flags', []),
            'anomalies': gemini_result.get('anomalies', [])
        }
        
        return combined
    
    def _calculate_confidence(
        self,
        revenue_data: Dict[str, Any],
        data_quality: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate confidence score with reasoning.
        
        Args:
            revenue_data: Revenue data
            data_quality: Data quality metrics
            analysis: Analysis results
            
        Returns:
            Dictionary with 'score' and 'reasoning'
        """
        confidence = 1.0
        reasons = []
        
        # Data completeness
        completeness = data_quality.get('completeness_score', 1.0)
        confidence *= completeness
        if completeness < 0.9:
            reasons.append(f"Data completeness: {completeness:.0%}")
        
        # Historical consistency
        records = revenue_data.get('records', [])
        if len(records) >= 8:
            confidence *= 1.0
            reasons.append("Sufficient historical data (8+ weeks)")
        elif len(records) >= 4:
            confidence *= 0.9
            reasons.append("Limited historical data (4-7 weeks)")
        else:
            confidence *= 0.7
            reasons.append("Insufficient historical data (<4 weeks)")
        
        # Statistical significance
        mrr_values = [r.get('mrr') for r in records if r.get('mrr')]
        if len(mrr_values) >= 4:
            std_dev = np.std(mrr_values)
            mean_val = np.mean(mrr_values)
            cv = std_dev / mean_val if mean_val > 0 else 1.0
            if cv < 0.2:  # Low coefficient of variation
                confidence *= 1.0
                reasons.append("High data consistency")
            elif cv < 0.4:
                confidence *= 0.95
                reasons.append("Moderate data consistency")
            else:
                confidence *= 0.85
                reasons.append("High data variability")
        
        # Analysis completeness
        required_sections = ['mrr_analysis', 'churn_analysis', 'key_insights']
        missing_sections = [s for s in required_sections if s not in analysis or not analysis[s]]
        if missing_sections:
            confidence *= 0.8
            reasons.append(f"Missing analysis sections: {', '.join(missing_sections)}")
        
        # Anomalies
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
        revenue_input: RevenueInput,
        revenue_data: Dict[str, Any]
    ) -> List[str]:
        """
        Generate data citations for transparency.
        
        Args:
            revenue_input: Input parameters
            revenue_data: Revenue data
            
        Returns:
            List of citation strings
        """
        citations = []
        
        if revenue_input.spreadsheet_id:
            citations.append(
                f"Week {revenue_input.week_number} MRR from Sheets '{revenue_input.revenue_sheet}'"
            )
            citations.append(
                f"Churn data from Sheets '{revenue_input.churn_sheet}'"
            )
        else:
            citations.append("Data from manual input")
        
        records = revenue_data.get('records', [])
        if records:
            citations.append(f"Analysis based on {len(records)} data points")
        
        return citations
    
    def _hash_data(self, revenue_data: Dict[str, Any]) -> str:
        """Generate hash for data caching."""
        import hashlib
        data_str = json.dumps(revenue_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _create_fallback_analysis(self, statistical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis when Gemini fails."""
        return {
            'mrr_analysis': {
                'current_mrr': statistical_analysis.get('current_mrr', 0),
                'wow_growth': statistical_analysis.get('wow_growth', 0),
                'mom_growth': statistical_analysis.get('mom_growth', 0),
                'trend': 'stable',
                'forecast_next_month': statistical_analysis.get('current_mrr', 0) * 1.05
            },
            'churn_analysis': {
                'current_rate': statistical_analysis.get('churn_rate', 0),
                'change_from_previous': 0,
                'severity': 'low',
                'cohort_breakdown': {}
            },
            'key_insights': [
                'Analysis generated from statistical data only',
                'Gemini analysis unavailable'
            ],
            'recommendations': [],
            'risk_flags': ['Gemini analysis failed - using statistical fallback']
        }
