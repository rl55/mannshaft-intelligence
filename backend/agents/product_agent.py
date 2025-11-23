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
                - product_ranges: Optional list of sheet ranges to read (e.g., ["Engagement Metrics!A1:M100", "Feature Adoption!A1:M100"])
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
            # Pass product_ranges from context if available
            product_ranges = context.get('product_ranges', [])
            product_data = await self._fetch_product_data(product_input, product_ranges)
            
            # Step 2.5: Filter data to include target week and previous weeks for context
            filtered_data_for_analysis = self._filter_data_for_analysis(product_data, product_input.week_number)
            
            # Step 2.6: Filter data by week_number for cache key (to ensure unique cache per week)
            filtered_data_for_cache = self._filter_data_by_week(product_data, product_input.week_number)
            
            # Step 3: Validate data quality (using filtered data)
            data_quality = self._validate_data_quality(filtered_data_for_analysis)
            
            # Step 4: Check agent-level cache (using filtered data hash to ensure week-specific caching)
            cache_context = {
                'week_number': product_input.week_number,
                'analysis_type': product_input.analysis_type,
                'data_hash': self._hash_data(filtered_data_for_cache)
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
            
            # Step 5: Perform statistical analysis (using filtered data with target week as current)
            # Include additional tab data if available
            statistical_analysis = self._perform_statistical_analysis(
                filtered_data_for_analysis, 
                product_input.week_number,
                feature_adoption_data=product_data.get('feature_adoption_data'),
                user_journey_data=product_data.get('user_journey_data')
            )
            
            # Step 6: Generate Gemini analysis (using filtered data)
            gemini_analysis = await self._generate_gemini_analysis(
                product_data=filtered_data_for_analysis,
                statistical_analysis=statistical_analysis,
                week_number=product_input.week_number,
                analysis_type=product_input.analysis_type,
                feature_adoption_data=product_data.get('feature_adoption_data'),
                user_journey_data=product_data.get('user_journey_data')
            )
            
            # Step 7: Combine analyses
            # Pass full product_data (including additional tabs) for risk flag filtering
            combined_analysis = self._combine_analyses(
                statistical_analysis=statistical_analysis,
                gemini_analysis=gemini_analysis,
                product_data=product_data,  # Use full product_data to check for additional tabs
                week_number=product_input.week_number
            )
            
            # Step 8: Calculate confidence
            confidence_result = self._calculate_confidence(
                product_data=filtered_data_for_analysis,
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
    
    async def _fetch_product_data(self, product_input: ProductInput, product_ranges: List[str] = None) -> Dict[str, Any]:
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
            
            # Fetch from primary sheet
            product_rows = self.sheets_client.get_sheet_data(
                spreadsheet_id=product_input.spreadsheet_id,
                sheet_name=product_input.product_sheet
            )
            
            # Parse primary sheet data
            product_data = self._parse_sheet_data(product_rows)
            
            # If multiple ranges are configured, fetch and merge data from additional tabs
            if product_ranges and len(product_ranges) > 1:
                self.logger.info(f"Fetching data from {len(product_ranges)} product sheets")
                for range_spec in product_ranges[1:]:  # Skip first (already fetched)
                    try:
                        # Extract sheet name and range from "SheetName!A1:M100"
                        if '!' in range_spec:
                            sheet_name, range_name = range_spec.split('!', 1)
                        else:
                            sheet_name = range_spec
                            range_name = None
                        
                        self.logger.info(f"Fetching data from sheet: {sheet_name}")
                        additional_rows = self.sheets_client.get_sheet_data(
                            spreadsheet_id=product_input.spreadsheet_id,
                            sheet_name=sheet_name,
                            range_name=range_name
                        )
                        
                        # Merge additional data based on sheet name
                        if 'Feature Adoption' in sheet_name or 'feature' in sheet_name.lower():
                            feature_data = self._parse_feature_adoption_data(additional_rows)
                            product_data['feature_adoption_data'] = feature_data
                            self.logger.info(f"Merged feature adoption data from {sheet_name}")
                        elif 'User Journey' in sheet_name or 'Journey' in sheet_name or 'Activation' in sheet_name:
                            journey_data = self._parse_user_journey_data(additional_rows)
                            product_data['user_journey_data'] = journey_data
                            self.logger.info(f"Merged user journey data from {sheet_name}")
                        else:
                            # Generic merge - try to parse as additional product data
                            additional_data = self._parse_sheet_data(additional_rows)
                            # Merge records if they have week numbers
                            if 'records' in additional_data and 'records' in product_data:
                                # Merge records by week
                                existing_weeks = {r.get('week') for r in product_data.get('records', [])}
                                for record in additional_data.get('records', []):
                                    if record.get('week') not in existing_weeks:
                                        product_data['records'].append(record)
                            self.logger.info(f"Merged generic data from {sheet_name}")
                    except Exception as e:
                        self.logger.warning(f"Could not fetch data from {range_spec}: {e}")
                        continue
            
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
    
    def _parse_feature_adoption_data(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Parse feature adoption sheet data."""
        if not rows or len(rows) < 2:
            return {'records': [], 'total_records': 0}
        
        headers = [str(h).lower().strip() for h in rows[0]]
        records = []
        
        for row in rows[1:]:
            if len(row) < len(headers):
                continue
            
            record = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else None
                if header in ['week']:
                    try:
                        value = int(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                elif 'adoption' in header or 'usage' in header or 'rate' in header:
                    try:
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                record[header] = value
            
            if record.get('week'):
                records.append(record)
        
        return {'records': records, 'total_records': len(records)}
    
    def _parse_user_journey_data(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Parse user journey/activation sheet data."""
        if not rows or len(rows) < 2:
            return {'records': [], 'total_records': 0}
        
        headers = [str(h).lower().strip() for h in rows[0]]
        records = []
        
        for row in rows[1:]:
            if len(row) < len(headers):
                continue
            
            record = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else None
                if header in ['week']:
                    try:
                        value = int(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                elif 'activation' in header or 'time' in header or 'journey' in header:
                    try:
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                record[header] = value
            
            if record.get('week'):
                records.append(record)
        
        return {'records': records, 'total_records': len(records)}
    
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
    
    def _perform_statistical_analysis(
        self, 
        product_data: Dict[str, Any], 
        target_week: Optional[int] = None,
        feature_adoption_data: Optional[Dict[str, Any]] = None,
        user_journey_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform statistical analysis on product data."""
        records = product_data.get('records', [])
        
        if len(records) < 2:
            return {
                'engagement_trend': 'insufficient_data',
                'adoption_rate': None
            }
        
        sorted_records = sorted(records, key=lambda x: x.get('week', 0))
        
        # Engagement Analysis - use target week if specified, otherwise use last week
        if target_week is not None:
            target_record = next((r for r in sorted_records if r.get('week') == target_week), None)
            if target_record:
                latest = target_record
            else:
                latest = sorted_records[-1] if sorted_records else {}
        else:
            latest = sorted_records[-1] if sorted_records else {}
        
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
        
        # Feature Adoption - check additional tab data if available
        all_adoptions = []
        for record in sorted_records:
            if record.get('feature_adoptions'):
                all_adoptions.extend(record['feature_adoptions'].values())
        
        # Also check feature_adoption_data from additional tab
        if feature_adoption_data:
            feature_records = feature_adoption_data.get('records', [])
            for record in feature_records:
                if record.get('week') == target_week or (target_week is None and record == feature_records[-1]):
                    # Extract adoption rates from feature adoption sheet
                    for key, value in record.items():
                        if 'adoption' in key.lower() or 'usage' in key.lower() or 'rate' in key.lower():
                            if isinstance(value, (int, float)) and value > 0:
                                all_adoptions.append(float(value))
        
        avg_adoption_rate = np.mean(all_adoptions) if all_adoptions else 0
        
        # Activation Metrics - check additional tab data if available
        activation_times = [r.get('activation_time_days') for r in sorted_records if r.get('activation_time_days')]
        
        # Also check user_journey_data from additional tab
        if user_journey_data:
            journey_records = user_journey_data.get('records', [])
            for record in journey_records:
                if record.get('week') == target_week or (target_week is None and record == journey_records[-1]):
                    # Extract activation times from user journey sheet
                    for key, value in record.items():
                        if 'activation' in key.lower() or 'time' in key.lower():
                            if isinstance(value, (int, float)) and value > 0:
                                activation_times.append(float(value))
        
        avg_activation_time = np.mean(activation_times) if activation_times else None
        
        # PQLs
        pql_values = [r.get('pqls') or 0 for r in sorted_records if r.get('pqls') is not None]
        current_pqls = pql_values[-1] if pql_values else 0
        pql_trend = 'stable'
        if len(pql_values) >= 2 and pql_values[-1] is not None and pql_values[-2] is not None:
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
        analysis_type: str,
        feature_adoption_data: Optional[Dict[str, Any]] = None,
        user_journey_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate analysis using Gemini."""
        prompt = self._build_structured_prompt(
            product_data=product_data,
            statistical_analysis=statistical_analysis,
            week_number=week_number,
            analysis_type=analysis_type,
            feature_adoption_data=feature_adoption_data,
            user_journey_data=user_journey_data
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
        analysis_type: str,
        feature_adoption_data: Optional[Dict[str, Any]] = None,
        user_journey_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build structured prompt for Gemini."""
        prompt = f"""You are a SaaS product analyst. Analyze the following product metrics data for Week {week_number} and provide a comprehensive analysis in JSON format.

IMPORTANT: Focus your analysis specifically on Week {week_number}. The data includes historical weeks for context, but your analysis should be centered on Week {week_number} metrics and trends.

PRODUCT DATA:
{json.dumps(product_data, indent=2)}
"""
        
        # Add feature adoption data if available
        if feature_adoption_data:
            prompt += f"""
FEATURE ADOPTION DATA (from Feature Adoption sheet):
{json.dumps(feature_adoption_data, indent=2)}
"""
        
        # Add user journey data if available
        if user_journey_data:
            prompt += f"""
USER JOURNEY DATA (from User Journey Metrics sheet):
{json.dumps(user_journey_data, indent=2)}
"""
        
        prompt += f"""
STATISTICAL ANALYSIS:
{json.dumps(statistical_analysis, indent=2)}

NOTE: The statistical analysis above uses Week {week_number} as the current week. Ensure your insights and metrics reflect Week {week_number} specifically.

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

CRITICAL INSTRUCTIONS:
1. Your analysis MUST focus on Week {week_number} specifically
2. When mentioning weeks in your insights, always reference Week {week_number}
3. The "current" metrics in your analysis should reflect Week {week_number} data
4. Do NOT analyze other weeks - only Week {week_number}
5. Format your insights as: "Week {week_number} [your insight here]"
6. Use the statistical analysis provided to inform your insights
7. Focus on engagement trends, feature adoption, and activation metrics
8. If FEATURE ADOPTION DATA is provided above, use it to analyze feature adoption rates and trends
9. If USER JOURNEY DATA is provided above, use it to analyze activation metrics and time-to-value
10. Provide specific, actionable recommendations
11. Flag any anomalies or risks
12. Return ONLY valid JSON, no markdown or explanations
13. DO NOT mention "lack of data" if Feature Adoption or User Journey data is provided above

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
        
        # Check if we have feature adoption or user journey data
        has_feature_adoption_data = bool(
            product_data.get('feature_adoption_data', {}).get('records')
        )
        has_user_journey_data = bool(
            product_data.get('user_journey_data', {}).get('records')
        )
        
        # Filter risk flags - remove "lack of data" flags if we actually have the data
        raw_risk_flags = gemini_result.get('risk_flags', [])
        filtered_risk_flags = []
        
        for risk_flag in raw_risk_flags:
            if isinstance(risk_flag, str):
                risk_text = risk_flag.lower()
            elif isinstance(risk_flag, dict):
                risk_text = risk_flag.get('description', risk_flag.get('flag', '')).lower()
            else:
                risk_text = str(risk_flag).lower()
            
            # Skip risk flags about "lack of data" if we have the data
            if has_feature_adoption_data and (
                'lack of data' in risk_text and 'feature adoption' in risk_text
            ):
                self.logger.info(f"Filtering out risk flag about lack of feature adoption data: {risk_flag}")
                continue
            
            if has_user_journey_data and (
                'lack of data' in risk_text and ('activation' in risk_text or 'user journey' in risk_text)
            ):
                self.logger.info(f"Filtering out risk flag about lack of activation/user journey data: {risk_flag}")
                continue
            
            # Keep all other risk flags
            filtered_risk_flags.append(risk_flag)
        
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
            'risk_flags': filtered_risk_flags,  # Use filtered risk flags
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
    
    def _filter_data_by_week(self, product_data: Dict[str, Any], week_number: int) -> Dict[str, Any]:
        """
        Filter product data to include only records for the specified week.
        This ensures each week has a unique cache key.
        
        Args:
            product_data: Full product data dictionary
            week_number: Week number to filter by
            
        Returns:
            Filtered product data dictionary
        """
        records = product_data.get('records', [])
        filtered_records = [
            record for record in records
            if record.get('week') == week_number
        ]
        
        return {
            'records': filtered_records,
            'total_records': len(filtered_records),
            'week_number': week_number
        }
    
    def _filter_data_for_analysis(self, product_data: Dict[str, Any], target_week: int) -> Dict[str, Any]:
        """
        Filter product data to include target week and previous weeks for context.
        This ensures we analyze the correct week while maintaining historical context for trends.
        
        Args:
            product_data: Full product data dictionary
            target_week: Target week number to analyze
            
        Returns:
            Filtered product data dictionary with target week and historical context
        """
        records = product_data.get('records', [])
        # Include target week and all previous weeks (up to 12 weeks back for trends)
        filtered_records = [
            record for record in records
            if record.get('week') is not None and record.get('week') <= target_week
        ]
        
        # Sort by week to ensure proper ordering
        filtered_records.sort(key=lambda x: x.get('week', 0))
        
        return {
            'records': filtered_records,
            'total_records': len(filtered_records),
            'target_week': target_week
        }
    
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
