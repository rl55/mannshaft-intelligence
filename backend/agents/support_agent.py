"""
Production Support Agent with comprehensive support metrics analysis.

Features:
- Ticket volume and trends
- Response time metrics
- Customer satisfaction (CSAT/NPS)
- Ticket category analysis
- Escalation patterns
- Support efficiency metrics
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

class SupportDataPoint(BaseModel):
    """Individual support ticket data point."""
    week: int = Field(..., ge=1, le=52, description="Week number (1-52)")
    ticket_count: int = Field(..., ge=0, description="Number of tickets")
    avg_response_time_hours: Optional[float] = Field(None, ge=0, description="Average response time in hours")
    avg_resolution_time_hours: Optional[float] = Field(None, ge=0, description="Average resolution time in hours")
    csat_score: Optional[float] = Field(None, ge=0, le=5, description="CSAT score (0-5)")
    nps_score: Optional[int] = Field(None, ge=-100, le=100, description="NPS score (-100 to 100)")
    category_breakdown: Optional[Dict[str, int]] = Field(None, description="Tickets by category")
    escalation_count: Optional[int] = Field(None, ge=0, description="Number of escalated tickets")
    first_contact_resolution_rate: Optional[float] = Field(None, ge=0, le=1, description="FCR rate (0-1)")


class SupportInput(BaseModel):
    """Input model for support analysis."""
    week_number: int = Field(..., ge=1, le=52, description="Week number for analysis")
    spreadsheet_id: Optional[str] = Field(None, description="Google Sheets spreadsheet ID")
    support_sheet: Optional[str] = Field("Support Tickets", description="Sheet name for support data")
    manual_data: Optional[Dict[str, Any]] = Field(None, description="Manual data override")
    analysis_type: str = Field("comprehensive", description="Type of analysis")
    
    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        """Validate analysis type."""
        allowed = ['comprehensive', 'volume_only', 'satisfaction_only', 'efficiency_only']
        if v not in allowed:
            raise ValueError(f"analysis_type must be one of {allowed}")
        return v


class TicketVolumeAnalysis(BaseModel):
    """Ticket volume analysis."""
    current_volume: int = Field(..., ge=0)
    trend: str = Field(..., description="Trend: increasing/decreasing/stable")
    week_over_week_change: float = Field(..., description="WoW change percentage")
    category_distribution: Dict[str, int] = Field(default_factory=dict)


class SatisfactionAnalysis(BaseModel):
    """Customer satisfaction analysis."""
    csat_score: float = Field(..., ge=0, le=5)
    nps_score: int = Field(..., ge=-100, le=100)
    trend: str = Field(..., description="Trend: improving/declining/stable")
    satisfaction_by_category: Dict[str, float] = Field(default_factory=dict)


class SupportAnalysisOutput(BaseModel):
    """Complete support analysis output."""
    agent_id: str = Field(default_factory=lambda: f"support_agent_{uuid.uuid4().hex[:8]}")
    agent_type: str = "support"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = Field(..., ge=0, le=1)
    confidence_reasoning: str = Field(..., description="Explanation of confidence score")
    analysis: Dict[str, Any] = Field(..., description="Analysis results")
    data_citations: List[str] = Field(default_factory=list, description="Data source citations")
    data_freshness_hours: Optional[float] = Field(None, description="Hours since data last updated")


# ============================================================================
# SUPPORT AGENT IMPLEMENTATION
# ============================================================================

class SupportAgent(BaseAgent):
    """
    Production-grade Support Agent with comprehensive support metrics analysis.
    
    Features:
    - Ticket volume and trend analysis
    - Response and resolution time metrics
    - Customer satisfaction (CSAT/NPS) tracking
    - Ticket category analysis
    - Escalation pattern detection
    - Support efficiency metrics
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Support Agent.
        
        Args:
            cache_manager: Cache manager instance
        """
        super().__init__("support", cache_manager)
        
        # Initialize integrations
        self.sheets_client = GoogleSheetsClient()
        self.gemini_client = GeminiClient(cache_manager)
        
        # Configuration
        self.prompt_cache_ttl_hours = 24
        self.agent_cache_ttl_hours = 1
        self.min_data_points = 4
        
        self.logger.info("SupportAgent initialized")
    
    async def analyze(self, context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Analyze support metrics with comprehensive analysis.
        
        Args:
            context: Input context containing:
                - week_number: Week number for analysis
                - spreadsheet_id: Optional Google Sheets ID
                - manual_data: Optional manual data override
                - analysis_type: Type of analysis
                - support_ranges: Optional list of sheet ranges to read (e.g., ["Ticket Volume!A1:N100", "CSAT & Satisfaction!A1:M100"])
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
                support_input = SupportInput(**context)
            except Exception as e:
                self.logger.error(f"Input validation failed: {e}")
                raise ValueError(f"Invalid input: {e}")
            
            # Step 2: Fetch data from Google Sheets or use manual data
            # Pass support_ranges from context if available
            support_ranges = context.get('support_ranges', [])
            support_data = await self._fetch_support_data(support_input, support_ranges)
            
            # Step 2.5: Filter data to include target week and previous weeks for context
            filtered_data_for_analysis = self._filter_data_for_analysis(support_data, support_input.week_number)
            
            # Step 2.6: Filter data by week_number for cache key (to ensure unique cache per week)
            filtered_data_for_cache = self._filter_data_by_week(support_data, support_input.week_number)
            
            # Step 3: Validate data quality (using filtered data)
            data_quality = self._validate_data_quality(filtered_data_for_analysis)
            
            # Step 4: Check agent-level cache (using filtered data hash to ensure week-specific caching)
            cache_context = {
                'week_number': support_input.week_number,
                'analysis_type': support_input.analysis_type,
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
                support_input.week_number,
                csat_data=support_data.get('csat_data'),
                category_data=support_data.get('category_data')
            )
            
            # Step 6: Generate Gemini analysis (using filtered data)
            gemini_analysis = await self._generate_gemini_analysis(
                support_data=filtered_data_for_analysis,
                statistical_analysis=statistical_analysis,
                week_number=support_input.week_number,
                analysis_type=support_input.analysis_type,
                csat_data=support_data.get('csat_data'),
                category_data=support_data.get('category_data')
            )
            
            # Step 7: Combine analyses
            # Pass full support_data (including additional tabs) for risk flag filtering
            combined_analysis = self._combine_analyses(
                statistical_analysis=statistical_analysis,
                gemini_analysis=gemini_analysis,
                support_data=support_data,  # Use full support_data to check for additional tabs
                week_number=support_input.week_number
            )
            
            # Step 8: Calculate confidence
            confidence_result = self._calculate_confidence(
                support_data=filtered_data_for_analysis,
                data_quality=data_quality,
                analysis=combined_analysis
            )
            
            # Step 9: Build final output
            output = SupportAnalysisOutput(
                confidence=confidence_result['score'],
                confidence_reasoning=confidence_result['reasoning'],
                analysis=combined_analysis,
                data_citations=self._generate_citations(support_input, support_data),
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
                f"Support analysis completed",
                extra={
                    'week_number': support_input.week_number,
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
            self.logger.error(f"Error in support analysis: {e}", exc_info=True)
            raise
    
    async def _fetch_support_data(self, support_input: SupportInput, support_ranges: List[str] = None) -> Dict[str, Any]:
        """Fetch support data from Google Sheets or use manual data."""
        if support_input.manual_data:
            self.logger.info("Using manual data")
            return support_input.manual_data
        
        if not support_input.spreadsheet_id:
            raise ValueError("Either spreadsheet_id or manual_data must be provided")
        
        if not self.sheets_client.client:
            raise RuntimeError("Google Sheets client not initialized")
        
        try:
            self.logger.info(f"Fetching support data from Google Sheets")
            
            # Fetch from primary sheet
            support_rows = self.sheets_client.get_sheet_data(
                spreadsheet_id=support_input.spreadsheet_id,
                sheet_name=support_input.support_sheet
            )
            
            # Parse primary sheet data
            support_data = self._parse_sheet_data(support_rows)
            
            # If multiple ranges are configured, fetch and merge data from additional tabs
            if support_ranges and len(support_ranges) > 1:
                self.logger.info(f"Fetching data from {len(support_ranges)} support sheets")
                for range_spec in support_ranges[1:]:  # Skip first (already fetched)
                    try:
                        # Extract sheet name and range from "SheetName!A1:M100"
                        if '!' in range_spec:
                            sheet_name, range_name = range_spec.split('!', 1)
                        else:
                            sheet_name = range_spec
                            range_name = None
                        
                        self.logger.info(f"Fetching data from sheet: {sheet_name}")
                        additional_rows = self.sheets_client.get_sheet_data(
                            spreadsheet_id=support_input.spreadsheet_id,
                            sheet_name=sheet_name,
                            range_name=range_name
                        )
                        
                        # Merge additional data based on sheet name
                        if 'CSAT' in sheet_name or 'Satisfaction' in sheet_name or 'NPS' in sheet_name:
                            csat_data = self._parse_csat_data(additional_rows)
                            support_data['csat_data'] = csat_data
                            self.logger.info(f"Merged CSAT data from {sheet_name}")
                        elif 'Category' in sheet_name or 'Categories' in sheet_name:
                            category_data = self._parse_category_data(additional_rows)
                            support_data['category_data'] = category_data
                            self.logger.info(f"Merged category data from {sheet_name}")
                        else:
                            # Generic merge - try to parse as additional support data
                            additional_data = self._parse_sheet_data(additional_rows)
                            # Merge records if they have week numbers
                            if 'records' in additional_data and 'records' in support_data:
                                # Merge records by week
                                existing_weeks = {r.get('week') for r in support_data.get('records', [])}
                                for record in additional_data.get('records', []):
                                    if record.get('week') not in existing_weeks:
                                        support_data['records'].append(record)
                            self.logger.info(f"Merged generic data from {sheet_name}")
                    except Exception as e:
                        self.logger.warning(f"Could not fetch data from {range_spec}: {e}")
                        continue
            
            return support_data
            
        except Exception as e:
            self.logger.error(f"Error fetching from Google Sheets: {e}", exc_info=True)
            raise
    
    def _parse_sheet_data(self, support_rows: List[List[Any]]) -> Dict[str, Any]:
        """Parse Google Sheets rows into structured data."""
        if not support_rows or len(support_rows) < 2:
            raise ValueError("Insufficient support data in sheet")
        
        # Map Google Sheets column names (lowercased) to expected field names
        column_mapping = {
            'total tickets': 'ticket_count',
            'week': 'week',
            'start date': 'start_date',
            'new tickets': 'new_tickets',
            'resolved tickets': 'resolved_tickets',
            'pending tickets': 'pending_tickets',
            'first response time (hours)': 'avg_response_time_hours',
            'resolution time (hours)': 'avg_resolution_time_hours',
            'csat score': 'csat_score',
            'tickets per customer': 'tickets_per_customer',
        }
        
        # Normalize headers: lowercase, strip, and map to expected field names
        raw_headers = [str(h).strip() for h in support_rows[0]]
        headers = [column_mapping.get(h.lower(), h.lower().replace(' ', '_')) for h in raw_headers]
        
        records = []
        
        for row in support_rows[1:]:
            if len(row) < len(headers):
                continue
            
            record = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else None
                
                # Parse numeric values
                if header in ['week', 'ticket_count', 'escalation_count']:
                    try:
                        value = int(value) if value else 0
                    except (ValueError, TypeError):
                        value = 0
                elif header in ['avg_response_time_hours', 'avg_resolution_time_hours', 
                               'csat_score', 'first_contact_resolution_rate']:
                    try:
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                elif header == 'nps_score':
                    try:
                        value = int(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                elif header == 'category_breakdown':
                    try:
                        value = json.loads(value) if value else {}
                    except (json.JSONDecodeError, TypeError):
                        value = {}
                else:
                    value = str(value) if value else None
                
                record[header] = value
            
            try:
                validated = SupportDataPoint(**record)
                records.append(validated.dict())
            except Exception as e:
                self.logger.warning(f"Skipping invalid record: {e}")
                continue
        
        return {
            'records': records,
            'total_records': len(records)
        }
    
    def _parse_csat_data(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Parse CSAT & Satisfaction sheet data."""
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
                elif 'csat' in header or 'nps' in header or 'satisfaction' in header or 'score' in header:
                    try:
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                record[header] = value
            
            if record.get('week'):
                records.append(record)
        
        return {'records': records, 'total_records': len(records)}
    
    def _parse_category_data(self, rows: List[List[Any]]) -> Dict[str, Any]:
        """Parse Support Categories sheet data."""
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
                elif 'category' in header or 'count' in header or 'ticket' in header:
                    try:
                        value = int(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                else:
                    value = str(value) if value else None
                record[header] = value
            
            if record.get('week'):
                records.append(record)
        
        return {'records': records, 'total_records': len(records)}
    
    def _validate_data_quality(self, support_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data quality and freshness."""
        records = support_data.get('records', [])
        
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
        required_fields = ['week', 'ticket_count']
        for record in records:
            for field in required_fields:
                if field not in record or record[field] is None:
                    quality['missing_fields'].append(f"Missing {field} in record")
                    quality['completeness_score'] *= 0.9
        
        # Detect anomalies in ticket volume
        if len(records) >= 2:
            ticket_counts = [r['ticket_count'] for r in records if r.get('ticket_count')]
            if ticket_counts:
                mean_count = np.mean(ticket_counts)
                std_count = np.std(ticket_counts)
                
                for record in records:
                    if record.get('ticket_count'):
                        z_score = abs((record['ticket_count'] - mean_count) / std_count) if std_count > 0 else 0
                        if z_score > 2.5:
                            quality['anomalies_detected'].append({
                                'type': 'ticket_volume_outlier',
                                'week': record.get('week'),
                                'value': record['ticket_count'],
                                'z_score': z_score
                            })
        
        quality['completeness_score'] = max(0.0, min(1.0, quality['completeness_score']))
        return quality
    
    def _perform_statistical_analysis(
        self, 
        support_data: Dict[str, Any], 
        target_week: Optional[int] = None,
        csat_data: Optional[Dict[str, Any]] = None,
        category_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform statistical analysis on support data."""
        records = support_data.get('records', [])
        
        if len(records) < 2:
            return {
                'volume_trend': 'insufficient_data',
                'avg_response_time': None
            }
        
        sorted_records = sorted(records, key=lambda x: x.get('week', 0))
        
        # Ticket Volume Analysis - use target week if specified, otherwise use last week
        if target_week is not None:
            target_record = next((r for r in sorted_records if r.get('week') == target_week), None)
            if target_record:
                latest = target_record
            else:
                latest = sorted_records[-1] if sorted_records else {}
        else:
            latest = sorted_records[-1] if sorted_records else {}
        
        current_volume = latest.get('ticket_count', 0)
        
        # Calculate WoW change using target week and previous week
        volume_values = [r.get('ticket_count', 0) for r in sorted_records]
        wow_change = 0.0
        if target_week is not None and target_week > 1:
            prev_week_record = next((r for r in sorted_records if r.get('week') == target_week - 1), None)
            if prev_week_record and prev_week_record.get('ticket_count', 0) > 0:
                prev_volume = prev_week_record.get('ticket_count', 0)
                wow_change = (current_volume - prev_volume) / prev_volume if prev_volume > 0 else 0
        elif len(volume_values) >= 2:
            # Fallback: use last two weeks
            wow_change = (volume_values[-1] - volume_values[-2]) / volume_values[-2] if volume_values[-2] > 0 else 0
        
        volume_trend = 'stable'
        if len(volume_values) >= 4:
            recent_avg = np.mean(volume_values[-2:])
            previous_avg = np.mean(volume_values[-4:-2])
            if recent_avg > previous_avg * 1.1:
                volume_trend = 'increasing'
            elif recent_avg < previous_avg * 0.9:
                volume_trend = 'decreasing'
        
        # Response Time Analysis
        response_times = [r.get('avg_response_time_hours') for r in sorted_records if r.get('avg_response_time_hours')]
        avg_response_time = np.mean(response_times) if response_times else None
        
        resolution_times = [r.get('avg_resolution_time_hours') for r in sorted_records if r.get('avg_resolution_time_hours')]
        avg_resolution_time = np.mean(resolution_times) if resolution_times else None
        
        # Satisfaction Analysis - check additional CSAT tab data if available
        csat_scores = [r.get('csat_score') for r in sorted_records if r.get('csat_score')]
        nps_scores = [r.get('nps_score') for r in sorted_records if r.get('nps_score')]
        
        # Also check csat_data from additional tab
        if csat_data:
            csat_records = csat_data.get('records', [])
            for record in csat_records:
                if record.get('week') == target_week or (target_week is None and record == csat_records[-1]):
                    # Extract CSAT and NPS from CSAT sheet
                    for key, value in record.items():
                        if 'csat' in key.lower() and isinstance(value, (int, float)) and value > 0:
                            csat_scores.append(float(value))
                        elif 'nps' in key.lower() and isinstance(value, (int, float)):
                            nps_scores.append(int(value))
        
        current_csat = np.mean(csat_scores[-4:]) if len(csat_scores) >= 4 else (csat_scores[-1] if csat_scores else None)
        current_nps = np.mean(nps_scores[-4:]) if len(nps_scores) >= 4 else (nps_scores[-1] if nps_scores else None)
        
        satisfaction_trend = 'stable'
        if len(csat_scores) >= 4:
            recent_csat = np.mean(csat_scores[-2:])
            previous_csat = np.mean(csat_scores[-4:-2])
            if recent_csat > previous_csat + 0.2:
                satisfaction_trend = 'improving'
            elif recent_csat < previous_csat - 0.2:
                satisfaction_trend = 'declining'
        
        # Escalation Analysis
        escalation_counts = [r.get('escalation_count') or 0 for r in sorted_records if r.get('escalation_count') is not None]
        current_escalations = escalation_counts[-1] if escalation_counts else 0
        escalation_rate = (current_escalations / current_volume) if current_volume > 0 and current_escalations is not None else 0
        
        # Efficiency Metrics
        fcr_rates = [r.get('first_contact_resolution_rate') for r in sorted_records if r.get('first_contact_resolution_rate')]
        avg_fcr = np.mean(fcr_rates) if fcr_rates else None
        
        # Category Breakdown - check additional category tab data if available
        all_categories = {}
        for record in sorted_records:
            if record.get('category_breakdown'):
                for category, count in record['category_breakdown'].items():
                    all_categories[category] = all_categories.get(category, 0) + count
        
        # Also check category_data from additional tab
        if category_data:
            category_records = category_data.get('records', [])
            for record in category_records:
                if record.get('week') == target_week or (target_week is None and record == category_records[-1]):
                    # Extract category breakdown from Support Categories sheet
                    for key, value in record.items():
                        if 'category' not in key.lower() and 'week' not in key.lower() and isinstance(value, (int, float)) and value > 0:
                            # Assume column name is category name
                            category_name = key.replace('_', ' ').title()
                            all_categories[category_name] = all_categories.get(category_name, 0) + int(value)
        
        return {
            'current_volume': current_volume,
            'wow_change': wow_change,
            'volume_trend': volume_trend,
            'avg_response_time': avg_response_time,
            'avg_resolution_time': avg_resolution_time,
            'current_csat': current_csat,
            'current_nps': current_nps,
            'satisfaction_trend': satisfaction_trend,
            'current_escalations': current_escalations,
            'escalation_rate': escalation_rate,
            'avg_fcr': avg_fcr,
            'category_distribution': all_categories,
            'data_points': len(records)
        }
    
    async def _generate_gemini_analysis(
        self,
        support_data: Dict[str, Any],
        statistical_analysis: Dict[str, Any],
        week_number: int,
        analysis_type: str,
        csat_data: Optional[Dict[str, Any]] = None,
        category_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate analysis using Gemini."""
        prompt = self._build_structured_prompt(
            support_data=support_data,
            statistical_analysis=statistical_analysis,
            week_number=week_number,
            analysis_type=analysis_type,
            csat_data=csat_data,
            category_data=category_data
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
        support_data: Dict[str, Any],
        statistical_analysis: Dict[str, Any],
        week_number: int,
        analysis_type: str,
        csat_data: Optional[Dict[str, Any]] = None,
        category_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build structured prompt for Gemini."""
        prompt = f"""You are a SaaS support analyst. Analyze the following support metrics data for Week {week_number} and provide a comprehensive analysis in JSON format.

IMPORTANT: Focus your analysis specifically on Week {week_number}. The data includes historical weeks for context, but your analysis should be centered on Week {week_number} metrics and trends.

SUPPORT DATA:
{json.dumps(support_data, indent=2)}
"""
        
        # Add CSAT data if available
        if csat_data:
            prompt += f"""
CSAT & SATISFACTION DATA (from CSAT & Satisfaction sheet):
{json.dumps(csat_data, indent=2)}
"""
        
        # Add category data if available
        if category_data:
            prompt += f"""
SUPPORT CATEGORIES DATA (from Support Categories sheet):
{json.dumps(category_data, indent=2)}
"""
        
        prompt += f"""
STATISTICAL ANALYSIS:
{json.dumps(statistical_analysis, indent=2)}

NOTE: The statistical analysis above uses Week {week_number} as the current week. Ensure your insights and metrics reflect Week {week_number} specifically.

REQUIRED OUTPUT FORMAT (JSON):
{{
  "ticket_volume_analysis": {{
    "current_volume": <number>,
    "trend": "<increasing|decreasing|stable>",
    "week_over_week_change": <decimal>,
    "category_distribution": {{
      "<category>": <count>
    }}
  }},
  "response_time_analysis": {{
    "avg_response_time_hours": <number>,
    "avg_resolution_time_hours": <number>,
    "trend": "<improving|worsening|stable>",
    "sla_compliance_rate": <decimal 0-1>
  }},
  "satisfaction_analysis": {{
    "csat_score": <decimal 0-5>,
    "nps_score": <integer -100 to 100>,
    "trend": "<improving|declining|stable>",
    "satisfaction_by_category": {{
      "<category>": <csat_score>
    }}
  }},
  "escalation_analysis": {{
    "escalation_rate": <decimal 0-1>,
    "trend": "<increasing|decreasing|stable>",
    "escalation_reasons": [
      "<reason>"
    ]
  }},
  "efficiency_metrics": {{
    "first_contact_resolution_rate": <decimal 0-1>,
    "tickets_per_agent": <number>,
    "efficiency_trend": "<improving|worsening|stable>"
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
7. Focus on ticket volume trends, response times, and customer satisfaction
8. If CSAT & SATISFACTION DATA is provided above, use it to analyze CSAT and NPS scores
9. If SUPPORT CATEGORIES DATA is provided above, use it to analyze category distribution and trends
10. Identify escalation patterns and efficiency opportunities
11. Provide specific, actionable recommendations
12. Flag any anomalies or risks
13. Return ONLY valid JSON, no markdown or explanations
14. DO NOT mention "lack of data" if CSAT & Satisfaction or Support Categories data is provided above

ANALYSIS TYPE: {analysis_type}

Now provide the analysis for Week {week_number}:"""
        
        return prompt
    
    def _combine_analyses(
        self,
        statistical_analysis: Dict[str, Any],
        gemini_analysis: Dict[str, Any],
        support_data: Dict[str, Any],
        week_number: int
    ) -> Dict[str, Any]:
        """Combine statistical and Gemini analyses."""
        gemini_result = gemini_analysis.get('analysis', {})
        
        # Check if we have CSAT or category data
        has_csat_data = bool(
            support_data.get('csat_data', {}).get('records')
        )
        has_category_data = bool(
            support_data.get('category_data', {}).get('records')
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
            if has_csat_data and (
                'lack of data' in risk_text and ('csat' in risk_text or 'satisfaction' in risk_text or 'nps' in risk_text)
            ):
                self.logger.info(f"Filtering out risk flag about lack of CSAT/satisfaction data: {risk_flag}")
                continue
            
            if has_category_data and (
                'lack of data' in risk_text and 'category' in risk_text
            ):
                self.logger.info(f"Filtering out risk flag about lack of category data: {risk_flag}")
                continue
            
            # Keep all other risk flags
            filtered_risk_flags.append(risk_flag)
        
        combined = {
            'ticket_volume_analysis': gemini_result.get('ticket_volume_analysis', {
                'current_volume': statistical_analysis.get('current_volume', 0),
                'trend': statistical_analysis.get('volume_trend', 'stable'),
                'week_over_week_change': statistical_analysis.get('wow_change', 0),
                'category_distribution': statistical_analysis.get('category_distribution', {})
            }),
            'response_time_analysis': gemini_result.get('response_time_analysis', {
                'avg_response_time_hours': statistical_analysis.get('avg_response_time', 0),
                'avg_resolution_time_hours': statistical_analysis.get('avg_resolution_time', 0),
                'trend': 'stable',
                'sla_compliance_rate': 0.85
            }),
            'satisfaction_analysis': gemini_result.get('satisfaction_analysis', {
                'csat_score': statistical_analysis.get('current_csat', 0),
                'nps_score': statistical_analysis.get('current_nps', 0),
                'trend': statistical_analysis.get('satisfaction_trend', 'stable'),
                'satisfaction_by_category': {}
            }),
            'escalation_analysis': gemini_result.get('escalation_analysis', {
                'escalation_rate': statistical_analysis.get('escalation_rate', 0),
                'trend': 'stable',
                'escalation_reasons': []
            }),
            'efficiency_metrics': gemini_result.get('efficiency_metrics', {
                'first_contact_resolution_rate': statistical_analysis.get('avg_fcr', 0),
                'tickets_per_agent': 0,
                'efficiency_trend': 'stable'
            }),
            'key_insights': gemini_result.get('key_insights', []),
            'recommendations': gemini_result.get('recommendations', []),
            'risk_flags': filtered_risk_flags,  # Use filtered risk flags
            'anomalies': gemini_result.get('anomalies', [])
        }
        
        return combined
    
    def _calculate_confidence(
        self,
        support_data: Dict[str, Any],
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
        
        records = support_data.get('records', [])
        if len(records) >= 8:
            confidence *= 1.0
            reasons.append("Sufficient historical data (8+ weeks)")
        elif len(records) >= 4:
            confidence *= 0.9
            reasons.append("Limited historical data (4-7 weeks)")
        else:
            confidence *= 0.7
            reasons.append("Insufficient historical data (<4 weeks)")
        
        # Check for satisfaction data availability
        csat_scores = [r.get('csat_score') for r in records if r.get('csat_score')]
        if len(csat_scores) >= 4:
            confidence *= 1.0
            reasons.append("Sufficient satisfaction data")
        elif len(csat_scores) >= 2:
            confidence *= 0.9
            reasons.append("Limited satisfaction data")
        else:
            confidence *= 0.85
            reasons.append("Missing satisfaction data")
        
        required_sections = ['ticket_volume_analysis', 'satisfaction_analysis', 'key_insights']
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
        support_input: SupportInput,
        support_data: Dict[str, Any]
    ) -> List[str]:
        """Generate data citations."""
        citations = []
        
        if support_input.spreadsheet_id:
            citations.append(
                f"Week {support_input.week_number} support metrics from Sheets '{support_input.support_sheet}'"
            )
        else:
            citations.append("Data from manual input")
        
        records = support_data.get('records', [])
        if records:
            citations.append(f"Analysis based on {len(records)} data points")
        
        return citations
    
    def _filter_data_by_week(self, support_data: Dict[str, Any], week_number: int) -> Dict[str, Any]:
        """
        Filter support data to include only records for the specified week.
        This ensures each week has a unique cache key.
        
        Args:
            support_data: Full support data dictionary
            week_number: Week number to filter by
            
        Returns:
            Filtered support data dictionary
        """
        records = support_data.get('records', [])
        filtered_records = [
            record for record in records
            if record.get('week') == week_number
        ]
        
        return {
            'records': filtered_records,
            'total_records': len(filtered_records),
            'week_number': week_number
        }
    
    def _filter_data_for_analysis(self, support_data: Dict[str, Any], target_week: int) -> Dict[str, Any]:
        """
        Filter support data to include target week and previous weeks for context.
        This ensures we analyze the correct week while maintaining historical context for trends.
        
        Args:
            support_data: Full support data dictionary
            target_week: Target week number to analyze
            
        Returns:
            Filtered support data dictionary with target week and historical context
        """
        records = support_data.get('records', [])
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
    
    def _hash_data(self, support_data: Dict[str, Any]) -> str:
        """Generate hash for data caching."""
        import hashlib
        data_str = json.dumps(support_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _create_fallback_analysis(self, statistical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis when Gemini fails."""
        return {
            'ticket_volume_analysis': {
                'current_volume': statistical_analysis.get('current_volume', 0),
                'trend': statistical_analysis.get('volume_trend', 'stable'),
                'week_over_week_change': statistical_analysis.get('wow_change', 0),
                'category_distribution': statistical_analysis.get('category_distribution', {})
            },
            'satisfaction_analysis': {
                'csat_score': statistical_analysis.get('current_csat', 0),
                'nps_score': statistical_analysis.get('current_nps', 0),
                'trend': statistical_analysis.get('satisfaction_trend', 'stable'),
                'satisfaction_by_category': {}
            },
            'key_insights': [
                'Analysis generated from statistical data only',
                'Gemini analysis unavailable'
            ],
            'recommendations': [],
            'risk_flags': ['Gemini analysis failed - using statistical fallback']
        }
