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
import hashlib
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
    churn_rate: Optional[float] = Field(None, ge=0, description="Churn rate (0-1 decimal or percentage if > 1)")
    customer_count: Optional[int] = Field(None, ge=0, description="Total customer count")
    
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
                - revenue_ranges: Optional list of sheet ranges to read (e.g., ["Weekly Revenue!A1:N100", "Customer Cohorts!A1:K100"])
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
            # Pass revenue_ranges from context if available
            revenue_ranges = context.get('revenue_ranges', [])
            revenue_data = await self._fetch_revenue_data(revenue_input, revenue_ranges)
            
            # Step 2.5: Filter data to include target week and previous weeks for context (for trends)
            # This ensures we analyze the correct week while still having historical context
            filtered_data_for_analysis = self._filter_data_for_analysis(revenue_data, revenue_input.week_number)
            
            # Step 2.6: Filter data by week_number for cache key (to ensure unique cache per week)
            filtered_data_for_cache = self._filter_data_by_week(revenue_data, revenue_input.week_number)
            
            # Step 3: Validate data quality and freshness (using filtered data)
            data_quality = self._validate_data_quality(filtered_data_for_analysis)
            
            # Step 4: Check agent-level cache (using filtered data hash to ensure week-specific caching)
            cache_context = {
                'week_number': revenue_input.week_number,
                'analysis_type': revenue_input.analysis_type,
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
                revenue_input.week_number,
                cohort_data=revenue_data.get('cohort_data'),
                segment_data=revenue_data.get('segment_data')
            )
            
            # Step 6: Generate Gemini analysis with structured prompt (using filtered data)
            # Include additional tab data if available
            gemini_analysis = await self._generate_gemini_analysis(
                revenue_data=filtered_data_for_analysis,
                statistical_analysis=statistical_analysis,
                week_number=revenue_input.week_number,
                analysis_type=revenue_input.analysis_type,
                cohort_data=revenue_data.get('cohort_data'),
                segment_data=revenue_data.get('segment_data')
            )
            
            # Step 7: Combine analyses and format output
            combined_analysis = self._combine_analyses(
                statistical_analysis=statistical_analysis,
                gemini_analysis=gemini_analysis,
                revenue_data=filtered_data_for_analysis,
                week_number=revenue_input.week_number
            )
            
            # Step 8: Calculate confidence with reasoning
            confidence_result = self._calculate_confidence(
                revenue_data=filtered_data_for_analysis,
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
    
    async def _fetch_revenue_data(self, revenue_input: RevenueInput, revenue_ranges: List[str] = None) -> Dict[str, Any]:
        """
        Fetch revenue data from Google Sheets or use manual data.
        
        Args:
            revenue_input: Validated input
            revenue_ranges: Optional list of sheet ranges to read
            
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
            
            # Fetch revenue data from primary sheet
            revenue_rows = self.sheets_client.get_sheet_data(
                spreadsheet_id=revenue_input.spreadsheet_id,
                sheet_name=revenue_input.revenue_sheet
            )
            
            # Fetch churn data if available (churn data is typically in the main revenue sheet)
            churn_rows = []
            if revenue_input.churn_sheet and revenue_input.churn_sheet != revenue_input.revenue_sheet:
                try:
                    churn_rows = self.sheets_client.get_sheet_data(
                        spreadsheet_id=revenue_input.spreadsheet_id,
                        sheet_name=revenue_input.churn_sheet
                    )
                except Exception as e:
                    self.logger.debug(f"Churn data not in separate sheet (likely in main sheet): {e}")
            
            # Parse rows into structured data
            revenue_data = self._parse_sheet_data(revenue_rows, churn_rows)
            
            # If multiple ranges are configured, fetch and merge data from additional tabs
            if revenue_ranges and len(revenue_ranges) > 1:
                self.logger.info(f"Fetching data from {len(revenue_ranges)} revenue sheets")
                for range_spec in revenue_ranges[1:]:  # Skip first (already fetched)
                    try:
                        # Extract sheet name and range from "SheetName!A1:N100"
                        if '!' in range_spec:
                            sheet_name, range_name = range_spec.split('!', 1)
                        else:
                            sheet_name = range_spec
                            range_name = None
                        
                        self.logger.info(f"Fetching data from sheet: {sheet_name}")
                        additional_rows = self.sheets_client.get_sheet_data(
                            spreadsheet_id=revenue_input.spreadsheet_id,
                            sheet_name=sheet_name,
                            range_name=range_name
                        )
                        
                        # Merge additional data based on sheet name
                        if 'Cohort' in sheet_name or 'cohort' in sheet_name.lower():
                            cohort_data = self._parse_cohort_data(additional_rows)
                            revenue_data['cohort_data'] = cohort_data
                            self.logger.info(f"Merged cohort data from {sheet_name}")
                        elif 'Segment' in sheet_name or 'segment' in sheet_name.lower():
                            segment_data = self._parse_segment_data(additional_rows)
                            revenue_data['segment_data'] = segment_data
                            self.logger.info(f"Merged segment data from {sheet_name}")
                        else:
                            # Generic merge - try to parse as additional revenue data
                            additional_data = self._parse_sheet_data(additional_rows, [])
                            # Merge records if they have week numbers
                            if 'records' in additional_data and 'records' in revenue_data:
                                # Merge records by week
                                existing_weeks = {r.get('week') for r in revenue_data.get('records', [])}
                                for record in additional_data.get('records', []):
                                    if record.get('week') not in existing_weeks:
                                        revenue_data['records'].append(record)
                            self.logger.info(f"Merged generic data from {sheet_name}")
                    except Exception as e:
                        self.logger.warning(f"Could not fetch data from {range_spec}: {e}")
                        continue
            
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
        
        # Map Google Sheets column names to expected field names
        column_mapping = {
            'new customers': 'new_customers',
            'churned customers': 'churned',
            'new mrr': 'new_mrr',
            'churned mrr': 'churned_mrr',
            'expansion mrr': 'expansion_mrr',
            'contraction mrr': 'contraction_mrr',
            'customer count': 'customer_count',
            'churn rate %': 'churn_rate',
            'churn rate': 'churn_rate',  # Handle both with and without %
            'mrr growth %': 'mrr_growth',
            'mrr growth': 'mrr_growth',  # Handle both with and without %
            'start date': 'start_date',
            'end date': 'end_date',
        }
        
        # Normalize headers: lowercase, strip, and map to expected field names
        raw_headers = [str(h).strip() for h in revenue_rows[0]]
        headers = [column_mapping.get(h.lower(), h.lower().replace(' ', '_').replace('%', '').replace('$', '')) for h in raw_headers]
        
        records = []
        for row in revenue_rows[1:]:
            if len(row) < len(headers):
                continue
            
            record = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else None
                
                # Try to parse numeric values
                if header in ['week', 'mrr', 'arpu', 'new_mrr', 'churned_mrr', 'expansion_mrr', 'contraction_mrr', 'customer_count', 'churn_rate', 'mrr_growth']:
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
    
    def _parse_cohort_data(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Parse Customer Cohorts sheet data."""
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
                if header in ['week', 'cohort']:
                    try:
                        value = int(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                elif 'retention' in header or 'rate' in header or 'revenue' in header or 'mrr' in header:
                    try:
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                else:
                    value = str(value) if value else None
                record[header] = value
            
            if record.get('week') or record.get('cohort'):
                records.append(record)
        
        return {'records': records, 'total_records': len(records)}
    
    def _parse_segment_data(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Parse Revenue by Segment sheet data."""
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
                elif 'segment' in header.lower():
                    value = str(value) if value else None
                elif 'revenue' in header or 'mrr' in header or 'arpu' in header or 'customer' in header:
                    try:
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                else:
                    value = str(value) if value else None
                record[header] = value
            
            if record.get('week'):
                records.append(record)
        
        return {'records': records, 'total_records': len(records)}
    
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
    
    def _perform_statistical_analysis(
        self, 
        revenue_data: Dict[str, Any], 
        target_week: Optional[int] = None,
        cohort_data: Optional[Dict[str, Any]] = None,
        segment_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform statistical analysis on revenue data.
        
        Args:
            revenue_data: Revenue data (should be filtered to include target week and previous weeks)
            target_week: Target week number (if None, uses last week in data)
            cohort_data: Optional cohort retention data from Customer Cohorts sheet
            segment_data: Optional segment breakdown data from Revenue by Segment sheet
            
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
        
        # Extract MRR values for all records (needed for fallback calculations)
        mrr_values = [r['mrr'] for r in sorted_records if r.get('mrr') is not None]
        
        # Find target week record (or use last week if target_week not specified)
        if target_week is not None:
            target_record = next((r for r in sorted_records if r.get('week') == target_week), None)
            if target_record:
                current_mrr = target_record.get('mrr', 0)
            else:
                # Fallback to last week if target week not found
                current_mrr = mrr_values[-1] if mrr_values else 0
        else:
            # Use last week if no target specified
            current_mrr = mrr_values[-1] if mrr_values else 0
        
        # Calculate WoW growth using target week and previous week
        wow_growth = 0.0
        if target_week is not None and target_week > 1:
            prev_week_record = next((r for r in sorted_records if r.get('week') == target_week - 1), None)
            if prev_week_record and prev_week_record.get('mrr', 0) > 0:
                prev_mrr = prev_week_record.get('mrr', 0)
                wow_growth = (current_mrr - prev_mrr) / prev_mrr if prev_mrr > 0 else 0
        elif len(mrr_values) >= 2:
            # Fallback: use last two weeks
            wow_growth = (mrr_values[-1] - mrr_values[-2]) / mrr_values[-2] if mrr_values[-2] > 0 else 0
        
        # Calculate MoM growth using target week and 4-5 weeks ago
        mom_growth = 0.0
        if target_week is not None and target_week >= 5:
            month_ago_week = target_week - 4  # Approximate month (4 weeks)
            month_ago_record = next((r for r in sorted_records if r.get('week') == month_ago_week), None)
            if month_ago_record and month_ago_record.get('mrr', 0) > 0:
                month_ago_mrr = month_ago_record.get('mrr', 0)
                mom_growth = (current_mrr - month_ago_mrr) / month_ago_mrr if month_ago_mrr > 0 else 0
        elif len(mrr_values) >= 5:  # Fallback: use last 5 weeks
            mom_growth = (mrr_values[-1] - mrr_values[-5]) / mrr_values[-5] if mrr_values[-5] > 0 else 0
        
        # Churn Analysis - use churn_rate from sheet for target week if available
        # Otherwise calculate from churned customers and customer count
        churn_rate = None
        prev_churn_rate = None
        
        if target_week is not None:
            # First, try to use churn_rate directly from the sheet for the target week
            target_record = next((r for r in sorted_records if r.get('week') == target_week), None)
            if target_record and target_record.get('churn_rate') is not None:
                # Use churn_rate from sheet (already a percentage, convert to decimal if > 1)
                churn_rate_raw = target_record.get('churn_rate')
                churn_rate = churn_rate_raw / 100.0 if churn_rate_raw > 1 else churn_rate_raw
                self.logger.info(f"Using churn_rate from sheet for Week {target_week}: {churn_rate} (raw: {churn_rate_raw})")
            elif target_record:
                # Calculate churn rate for target week using customer_count if available
                churned = target_record.get('churned', 0)
                customer_count = target_record.get('customer_count')
                
                if customer_count and customer_count > 0:
                    churn_rate = churned / customer_count
                    self.logger.info(f"Calculated churn_rate for Week {target_week}: {churn_rate} (churned={churned}, customer_count={customer_count})")
                else:
                    # Fallback: use previous week's customer count + new customers - churned
                    prev_week_record = next((r for r in sorted_records if r.get('week') == target_week - 1), None)
                    if prev_week_record:
                        prev_customer_count = prev_week_record.get('customer_count')
                        new_customers = target_record.get('new_customers', 0)
                        if prev_customer_count and prev_customer_count > 0:
                            total_customers = prev_customer_count + new_customers
                            churn_rate = churned / total_customers if total_customers > 0 else 0
                            self.logger.info(f"Calculated churn_rate using previous week's count: {churn_rate}")
            
            # Get previous week's churn rate for change calculation
            if target_week > 1:
                prev_week_record = next((r for r in sorted_records if r.get('week') == target_week - 1), None)
                if prev_week_record:
                    if prev_week_record.get('churn_rate') is not None:
                        prev_churn_rate_raw = prev_week_record.get('churn_rate')
                        prev_churn_rate = prev_churn_rate_raw / 100.0 if prev_churn_rate_raw > 1 else prev_churn_rate_raw
                    elif prev_week_record.get('customer_count') and prev_week_record.get('customer_count') > 0:
                        prev_churned = prev_week_record.get('churned', 0)
                        prev_churn_rate = prev_churned / prev_week_record.get('customer_count')
        
        # If still no churn_rate, use average of last 4 weeks
        if churn_rate is None:
            churn_records = sorted_records[-4:] if len(sorted_records) >= 4 else sorted_records
            total_churned = sum(r.get('churned', 0) for r in churn_records)
            
            # Try to use churn_rate from records if available
            churn_rates = [r.get('churn_rate') for r in churn_records if r.get('churn_rate') is not None]
            if churn_rates:
                # Convert percentages to decimals if needed
                churn_rates_decimal = [r / 100.0 if r > 1 else r for r in churn_rates]
                churn_rate = np.mean(churn_rates_decimal)
            else:
                # Try to use customer_count from records
                customer_counts = [r.get('customer_count') for r in churn_records if r.get('customer_count')]
                if customer_counts:
                    avg_customer_count = np.mean(customer_counts)
                    churn_rate = total_churned / (avg_customer_count * len(churn_records)) if avg_customer_count > 0 else 0
                else:
                    # This should not happen, but set to 0 as fallback
                    churn_rate = 0
                    self.logger.warning("Could not calculate churn_rate - using 0 as fallback")
        
        # Calculate change_from_previous for churn rate
        churn_change = 0.0
        if prev_churn_rate is not None and prev_churn_rate > 0:
            churn_change = churn_rate - prev_churn_rate
        
        # ARPU Analysis
        arpu_values = [r['arpu'] for r in sorted_records if r.get('arpu')]
        avg_arpu = np.mean(arpu_values) if arpu_values else None
        
        # Calculate change_from_previous for churn rate
        churn_change = 0.0
        if prev_churn_rate is not None and prev_churn_rate > 0:
            churn_change = churn_rate - prev_churn_rate
        
        return {
            'current_mrr': current_mrr,
            'wow_growth': wow_growth,
            'mom_growth': mom_growth,
            'churn_rate': churn_rate,
            'churn_change_from_previous': churn_change,
            'avg_arpu': avg_arpu,
            'data_points': len(records)
        }
    
    async def _generate_gemini_analysis(
        self,
        revenue_data: Dict[str, Any],
        statistical_analysis: Dict[str, Any],
        week_number: int,
        analysis_type: str,
        cohort_data: Optional[Dict[str, Any]] = None,
        segment_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate analysis using Gemini with structured prompts.
        
        Args:
            revenue_data: Revenue data
            statistical_analysis: Statistical analysis results
            week_number: Week number
            analysis_type: Type of analysis
            cohort_data: Optional cohort retention data from Customer Cohorts sheet
            segment_data: Optional segment breakdown data from Revenue by Segment sheet
            
        Returns:
            Gemini analysis results
        """
        # Build structured prompt with few-shot examples
        prompt = self._build_structured_prompt(
            revenue_data=revenue_data,
            statistical_analysis=statistical_analysis,
            week_number=week_number,
            analysis_type=analysis_type,
            cohort_data=cohort_data,
            segment_data=segment_data
        )
        
        # Check prompt cache
        # Note: The prompt already includes week_number, so the cache key should be unique per week
        # But we'll add explicit logging to verify
        cached_prompt = self.cache_manager.get_cached_prompt(
            prompt=prompt,
            model=self.gemini_client.model_name
        )
        
        if cached_prompt:
            self.logger.info(f"Prompt cache HIT for Week {week_number} analysis")
        else:
            self.logger.info(f"Prompt cache MISS for Week {week_number} analysis - generating new response")
        
        if cached_prompt:
            self.logger.info("Prompt cache HIT")
            try:
                cached_analysis = json.loads(cached_prompt['response'])
                # Verify cached analysis is for the correct week
                # Check if key insights mention the correct week
                key_insights = cached_analysis.get('key_insights', [])
                if key_insights:
                    insights_text = ' '.join(key_insights).lower()
                    if f'week {week_number}' not in insights_text and f'week {week_number}' not in str(cached_analysis).lower():
                        self.logger.warning(
                            f"Cached prompt response may be for wrong week. "
                            f"Expected Week {week_number}, but insights mention: {insights_text[:200]}"
                        )
                        # Don't use cached response if it seems wrong
                        cached_prompt = None
                    else:
                        self.logger.info(f"Using cached prompt response for Week {week_number}")
                        return {
                            'analysis': cached_analysis,
                            'tokens_input': cached_prompt.get('tokens_input', 0),
                            'tokens_output': cached_prompt.get('tokens_output', 0),
                            'cached': True
                        }
                else:
                    # No insights to check, use cached response
                    return {
                        'analysis': cached_analysis,
                        'tokens_input': cached_prompt.get('tokens_input', 0),
                        'tokens_output': cached_prompt.get('tokens_output', 0),
                        'cached': True
                    }
            except json.JSONDecodeError:
                self.logger.warning("Cached response is not valid JSON, regenerating")
                cached_prompt = None
        
        if not cached_prompt:
            self.logger.info(f"Prompt cache MISS for Week {week_number} - calling Gemini API")
        
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
        analysis_type: str,
        cohort_data: Optional[Dict[str, Any]] = None,
        segment_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build structured prompt with few-shot examples for Gemini.
        
        Args:
            revenue_data: Revenue data
            statistical_analysis: Statistical analysis
            week_number: Week number
            analysis_type: Type of analysis
            cohort_data: Optional cohort retention data from Customer Cohorts sheet
            segment_data: Optional segment breakdown data from Revenue by Segment sheet
            
        Returns:
            Structured prompt string
        """
        # Get churn values from statistical analysis to include in prompt
        churn_rate = statistical_analysis.get('churn_rate', 0)
        churn_change = statistical_analysis.get('churn_change_from_previous', 0)
        
        prompt = f"""You are a SaaS revenue analyst. Analyze the following revenue data for Week {week_number} and provide a comprehensive analysis in JSON format.

IMPORTANT: Focus your analysis specifically on Week {week_number}. The data includes historical weeks for context, but your analysis should be centered on Week {week_number} metrics and trends.

REVENUE DATA:
{json.dumps(revenue_data, indent=2)}
"""
        
        # Add cohort data if available
        if cohort_data:
            prompt += f"""
CUSTOMER COHORTS DATA (from Customer Cohorts sheet):
{json.dumps(cohort_data, indent=2)}
"""
        
        # Add segment data if available
        if segment_data:
            prompt += f"""
REVENUE BY SEGMENT DATA (from Revenue by Segment sheet):
{json.dumps(segment_data, indent=2)}
"""
        
        prompt += f"""
STATISTICAL ANALYSIS:
{json.dumps(statistical_analysis, indent=2)}

NOTE: The statistical analysis above uses Week {week_number} as the current week. Ensure your insights and metrics reflect Week {week_number} specifically.

CRITICAL INSTRUCTION FOR CHURN RATE:
The churn_rate in the statistical analysis is {churn_rate:.4f} ({churn_rate * 100:.2f}%). This value is calculated correctly from the sheet data.
You MUST use this exact value for "current_rate" in your churn_analysis. Do NOT recalculate churn_rate.
The change_from_previous is {churn_change:.4f} ({churn_change * 100:.2f} percentage points).

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
    "current_rate": {churn_rate:.4f},  # MUST USE THIS EXACT VALUE - DO NOT RECALCULATE
    "change_from_previous": {churn_change:.4f},  # MUST USE THIS EXACT VALUE - DO NOT RECALCULATE
    "severity": "<low|medium|high|critical>",  # Based on current_rate value ({churn_rate * 100:.2f}%)
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

CRITICAL INSTRUCTIONS:
1. Your analysis MUST use the 'churn_rate' and 'churn_change_from_previous' values provided in the STATISTICAL ANALYSIS section for the 'churn_analysis' output. Do NOT recalculate or infer these values.
2. Your analysis MUST focus on Week {week_number} specifically
3. When mentioning weeks in your insights, always reference Week {week_number}
4. The "current" metrics in your analysis should reflect Week {week_number} data
5. Do NOT analyze other weeks - only Week {week_number}
6. Format your insights as: "Week {week_number} [your insight here]"
7. If CUSTOMER COHORTS DATA is provided above, use it to analyze cohort retention rates and trends
8. If REVENUE BY SEGMENT DATA is provided above, use it to analyze segment breakdown and ARPU by segment
9. Use cohort and segment data to provide more detailed insights in the 'churn_analysis.cohort_breakdown' and 'arpu_analysis.segmentation' fields

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
            'churn_analysis': {
                # Always use statistical analysis churn_rate (calculated correctly from sheet)
                'current_rate': statistical_analysis.get('churn_rate', 0),
                'change_from_previous': statistical_analysis.get('churn_change_from_previous', 0),
                # Use Gemini's severity and cohort breakdown if available, otherwise defaults
                'severity': gemini_result.get('churn_analysis', {}).get('severity', 'low'),
                'cohort_breakdown': gemini_result.get('churn_analysis', {}).get('cohort_breakdown', {})
            },
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
    
    def _filter_data_by_week(self, revenue_data: Dict[str, Any], week_number: int) -> Dict[str, Any]:
        """
        Filter revenue data to include only records for the specified week.
        This ensures each week has a unique cache key.
        
        Args:
            revenue_data: Full revenue data dictionary
            week_number: Week number to filter by
            
        Returns:
            Filtered revenue data dictionary
        """
        records = revenue_data.get('records', [])
        filtered_records = [
            record for record in records
            if record.get('week') == week_number
        ]
        
        return {
            'records': filtered_records,
            'total_records': len(filtered_records),
            'week_number': week_number
        }
    
    def _filter_data_for_analysis(self, revenue_data: Dict[str, Any], target_week: int) -> Dict[str, Any]:
        """
        Filter revenue data to include target week and previous weeks for context.
        This ensures we analyze the correct week while maintaining historical context for trends.
        
        Args:
            revenue_data: Full revenue data dictionary
            target_week: Target week number to analyze
            
        Returns:
            Filtered revenue data dictionary with target week and historical context
        """
        records = revenue_data.get('records', [])
        # Include target week and all previous weeks (up to 12 weeks back for MoM calculations)
        # STRICT filtering: only include weeks <= target_week
        filtered_records = [
            record for record in records
            if record.get('week') is not None and isinstance(record.get('week'), (int, float)) and int(record.get('week')) <= target_week
        ]
        
        # Sort by week to ensure proper ordering
        filtered_records.sort(key=lambda x: int(x.get('week', 0)))
        
        # Log filtering for debugging
        weeks_in_data = [int(r.get('week', 0)) for r in filtered_records if r.get('week')]
        self.logger.info(
            f"Filtered revenue data for Week {target_week} analysis. "
            f"Weeks in filtered data: {weeks_in_data}. "
            f"Total records: {len(filtered_records)}"
        )
        
        # Verify target week is in the data
        target_week_records = [r for r in filtered_records if int(r.get('week', 0)) == target_week]
        if not target_week_records:
            self.logger.warning(
                f"WARNING: Week {target_week} not found in filtered data. "
                f"Available weeks: {weeks_in_data}"
            )
        
        return {
            'records': filtered_records,
            'total_records': len(filtered_records),
            'target_week': target_week,
            'weeks_included': weeks_in_data
        }
    
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
                'change_from_previous': statistical_analysis.get('churn_change_from_previous', 0),
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
