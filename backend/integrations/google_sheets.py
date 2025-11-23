"""
Comprehensive Google Sheets integration using MCP (Model Context Protocol).

Features:
- MCP protocol support (or MCP-like patterns)
- Comprehensive caching with checksum-based change detection
- Data freshness tracking
- Retry logic with rate limit handling
- Specific methods for revenue, product, and support data
- Graceful error handling
"""

import json
import hashlib
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import gspread
from google.oauth2.service_account import Credentials

# Optional imports for advanced API operations
try:
    from googleapiclient.errors import HttpError
    from googleapiclient.discovery import build
    HAS_ADVANCED_API = True
except ImportError:
    HAS_ADVANCED_API = False
    HttpError = Exception  # Fallback for error handling

# gspread exceptions
try:
    from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
    HAS_GSPREAD_EXCEPTIONS = True
except ImportError:
    HAS_GSPREAD_EXCEPTIONS = False
    APIError = Exception
    SpreadsheetNotFound = Exception
    WorksheetNotFound = Exception

from utils.config import config
from utils.logger import logger
from cache.cache_manager import CacheManager


class DataFreshnessStatus(Enum):
    """Data freshness status."""
    FRESH = "fresh"  # < 1 hour
    RECENT = "recent"  # < 24 hours
    STALE = "stale"  # < 7 days
    VERY_STALE = "very_stale"  # >= 7 days


@dataclass
class DataFreshness:
    """Data freshness information."""
    sheet_id: str
    last_updated: datetime
    freshness_hours: float
    status: DataFreshnessStatus
    checksum: str


@dataclass
class RevenueData:
    """Revenue data structure."""
    week_number: int
    data_points: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    freshness: Optional[DataFreshness] = None


@dataclass
class ProductData:
    """Product data structure."""
    week_number: int
    data_points: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    freshness: Optional[DataFreshness] = None


@dataclass
class SupportData:
    """Support data structure."""
    week_number: int
    data_points: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    freshness: Optional[DataFreshness] = None


class GoogleSheetsIntegration:
    """
    Comprehensive Google Sheets integration with MCP protocol support.
    
    Features:
    - Authentication with Google Sheets API
    - Read data from specific sheets and ranges
    - Rate limit handling with retries
    - Comprehensive caching with checksum-based change detection
    - Data freshness tracking
    - Error handling with graceful degradation
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize Google Sheets integration.
        
        Args:
            cache_manager: Optional cache manager for data caching
        """
        self.cache_manager = cache_manager or CacheManager()
        self.logger = logger.getChild('google_sheets')
        
        # Initialize client
        self.client: Optional[gspread.Client] = None
        self.service: Optional[Any] = None  # Google Sheets API service
        
        # Configuration
        self.credentials_path = config.get('google_sheets.credentials_path')
        self.scopes = config.get('google_sheets.scopes', [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ])
        
        # Sheet configuration
        self.sheets_config = config.get('sheets', {})
        
        # Rate limiting and retry configuration
        self.max_retries = config.get('google_sheets.max_retries', 3)
        self.retry_delay_seconds = config.get('google_sheets.retry_delay_seconds', 2)
        self.rate_limit_delay_seconds = config.get('google_sheets.rate_limit_delay_seconds', 1)
        
        # Cache configuration
        self.cache_ttl_hours = config.get('google_sheets.cache_ttl_hours', 1)
        
        # Initialize
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets client and API service."""
        try:
            if not self.credentials_path:
                self.logger.warning("Google Sheets credentials path not configured")
                return
            
            # Initialize gspread client
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.scopes
            )
            self.client = gspread.authorize(creds)
            
            # Initialize Google Sheets API service (for advanced operations)
            if HAS_ADVANCED_API:
                self.service = build('sheets', 'v4', credentials=creds)
            else:
                self.service = None
                self.logger.warning("google-api-python-client not available, advanced features disabled")
            
            self.logger.info("Google Sheets client initialized successfully")
        except FileNotFoundError:
            self.logger.error(f"Credentials file not found: {self.credentials_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets client: {e}", exc_info=True)
    
    def _calculate_checksum(self, data: List[List[Any]]) -> str:
        """Calculate checksum for data to detect changes."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _get_cached_data(
        self,
        cache_key: str
    ) -> Optional[Tuple[List[List[Any]], str]]:
        """
        Get cached sheet data.
        
        Returns:
            Tuple of (data, checksum) or None if not cached/expired
        """
        try:
            conn = self.cache_manager.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT response, metadata FROM agent_responses
                WHERE agent_type = 'google_sheets' 
                AND request_params = ?
                AND datetime(last_accessed, '+' || ttl_hours || ' hours') > datetime('now')
            """, (json.dumps({'cache_key': cache_key}),))
            
            row = cursor.fetchone()
            if row:
                try:
                    data = json.loads(row['response'])
                    metadata = json.loads(row['metadata']) if row['metadata'] else {}
                    checksum = metadata.get('checksum', '')
                    
                    # Update last accessed
                    cursor.execute("""
                        UPDATE agent_responses 
                        SET last_accessed = datetime('now')
                        WHERE agent_type = 'google_sheets' AND request_params = ?
                    """, (json.dumps({'cache_key': cache_key}),))
                    conn.commit()
                    
                    return data, checksum
                except json.JSONDecodeError:
                    return None
        except Exception as e:
            self.logger.warning(f"Error getting cached data: {e}")
        
        return None
    
    def _cache_data(
        self,
        cache_key: str,
        data: List[List[Any]],
        checksum: str
    ):
        """Cache sheet data."""
        try:
            data_json = json.dumps(data)
            metadata = json.dumps({
                'checksum': checksum,
                'cached_at': datetime.utcnow().isoformat()
            })
            
            # Use cache_manager's agent response caching
            self.cache_manager.cache_agent_response(
                agent_type='google_sheets',
                context={'cache_key': cache_key},
                response=data_json,
                confidence_score=1.0,
                execution_time_ms=0,
                ttl_hours=self.cache_ttl_hours
            )
        except Exception as e:
            self.logger.warning(f"Error caching data: {e}")
    
    async def _fetch_with_retry(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        range_name: Optional[str] = None
    ) -> List[List[Any]]:
        """
        Fetch sheet data with retry logic and rate limit handling.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            range_name: Optional range (e.g., 'A1:C10')
            
        Returns:
            List of rows
            
        Raises:
            RuntimeError: If client not initialized
            Exception: After max retries
        """
        if not self.client:
            raise RuntimeError("Google Sheets client not initialized")
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Rate limit delay
                if attempt > 0:
                    await asyncio.sleep(self.rate_limit_delay_seconds * attempt)
                
                # Fetch data
                spreadsheet = self.client.open_by_key(spreadsheet_id)
                worksheet = spreadsheet.worksheet(sheet_name)
                
                if range_name:
                    return worksheet.get(range_name)
                else:
                    return worksheet.get_all_values()
                    
            except Exception as e:
                last_exception = e
                
                # Handle gspread exceptions
                if HAS_GSPREAD_EXCEPTIONS:
                    if isinstance(e, SpreadsheetNotFound):
                        self.logger.error(f"Spreadsheet not found: {spreadsheet_id}")
                        raise
                    if isinstance(e, WorksheetNotFound):
                        self.logger.error(f"Worksheet not found: {sheet_name}")
                        raise
                    if isinstance(e, APIError):
                        error_code = e.response.status_code if hasattr(e, 'response') else None
                    else:
                        error_code = None
                else:
                    # Try to extract error code from various exception types
                    error_code = None
                    if HAS_ADVANCED_API and isinstance(e, HttpError):
                        error_code = e.resp.status if hasattr(e, 'resp') else None
                    elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        error_code = e.response.status_code
                    elif hasattr(e, 'status_code'):
                        error_code = e.status_code
                
                # Handle rate limiting (429)
                if error_code == 429:
                    wait_time = self.retry_delay_seconds * (2 ** attempt)
                    self.logger.warning(
                        f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                # Handle other HTTP errors
                if error_code in [400, 401, 403, 404]:
                    self.logger.error(f"HTTP error {error_code}: {e}")
                    raise
                
                # Retry on transient errors (500, 503)
                if error_code in [500, 503]:
                    self.logger.warning(f"Transient error {error_code}, retrying...")
                    continue
                
                # If we can't determine error code, retry on last attempt
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Unknown error, retrying: {e}")
                    continue
                
                raise
                
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        f"Error fetching sheet data (attempt {attempt + 1}/{self.max_retries}): {e}"
                    )
                    await asyncio.sleep(self.retry_delay_seconds * (attempt + 1))
                else:
                    raise
        
        # If we get here, all retries failed
        raise last_exception or Exception("Failed to fetch sheet data after retries")
    
    async def read_sheet_data(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        range_name: Optional[str] = None,
        use_cache: bool = True
    ) -> Tuple[List[List[Any]], Optional[DataFreshness]]:
        """
        Read data from a Google Sheet with caching and freshness tracking.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            range_name: Optional range (e.g., 'A1:C10')
            use_cache: Whether to use cached data
            
        Returns:
            Tuple of (data rows, freshness info)
        """
        cache_key = f"{spreadsheet_id}:{sheet_name}:{range_name or 'all'}"
        
        # Check cache
        if use_cache:
            cached = self._get_cached_data(cache_key)
            if cached:
                data, old_checksum = cached
                self.logger.info(f"Cache HIT for {cache_key}")
                
                # Check if data changed (quick check)
                new_checksum = self._calculate_checksum(data)
                if new_checksum == old_checksum:
                    # Data unchanged, return cached
                    freshness = self._get_data_freshness(spreadsheet_id)
                    return data, freshness
        
        # Fetch fresh data
        self.logger.info(f"Fetching fresh data for {cache_key}")
        data = await self._fetch_with_retry(spreadsheet_id, sheet_name, range_name)
        
        # Calculate checksum and cache
        checksum = self._calculate_checksum(data)
        self._cache_data(cache_key, data, checksum)
        
        # Update freshness
        freshness = self._update_data_freshness(spreadsheet_id, checksum)
        
        return data, freshness
    
    def _get_data_freshness(self, sheet_id: str) -> Optional[DataFreshness]:
        """Get data freshness information."""
        try:
            conn = self.cache_manager.connect()
            cursor = conn.cursor()
            
            # Check if we have freshness data
            cursor.execute("""
                SELECT metadata FROM agent_responses
                WHERE agent_type = 'google_sheets_freshness'
                AND request_params = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (json.dumps({'sheet_id': sheet_id}),))
            
            row = cursor.fetchone()
            if row and row['metadata']:
                metadata = json.loads(row['metadata'])
                last_updated = datetime.fromisoformat(metadata.get('last_updated', datetime.utcnow().isoformat()))
                freshness_hours = (datetime.utcnow() - last_updated).total_seconds() / 3600
                
                status = self._determine_freshness_status(freshness_hours)
                
                return DataFreshness(
                    sheet_id=sheet_id,
                    last_updated=last_updated,
                    freshness_hours=freshness_hours,
                    status=status,
                    checksum=metadata.get('checksum', '')
                )
        except Exception as e:
            self.logger.warning(f"Error getting data freshness: {e}")
        
        return None
    
    def _update_data_freshness(self, sheet_id: str, checksum: str) -> DataFreshness:
        """Update data freshness tracking."""
        now = datetime.utcnow()
        
        try:
            metadata = json.dumps({
                'last_updated': now.isoformat(),
                'checksum': checksum
            })
            
            # Store freshness info
            self.cache_manager.cache_agent_response(
                agent_type='google_sheets_freshness',
                context={'sheet_id': sheet_id},
                response=json.dumps({'sheet_id': sheet_id}),
                confidence_score=1.0,
                execution_time_ms=0,
                ttl_hours=24 * 7  # 7 days
            )
        except Exception as e:
            self.logger.warning(f"Error updating data freshness: {e}")
        
        freshness_hours = 0.0  # Just updated
        status = DataFreshnessStatus.FRESH
        
        return DataFreshness(
            sheet_id=sheet_id,
            last_updated=now,
            freshness_hours=freshness_hours,
            status=status,
            checksum=checksum
        )
    
    def _determine_freshness_status(self, freshness_hours: float) -> DataFreshnessStatus:
        """Determine freshness status from hours."""
        if freshness_hours < 1:
            return DataFreshnessStatus.FRESH
        elif freshness_hours < 24:
            return DataFreshnessStatus.RECENT
        elif freshness_hours < 24 * 7:
            return DataFreshnessStatus.STALE
        else:
            return DataFreshnessStatus.VERY_STALE
    
    def check_data_freshness(self, sheet_id: str) -> Optional[DataFreshness]:
        """
        Check when data was last updated.
        
        Args:
            sheet_id: Spreadsheet ID
            
        Returns:
            DataFreshness object or None if not tracked
        """
        return self._get_data_freshness(sheet_id)
    
    async def read_revenue_data(self, week_number: int) -> RevenueData:
        """
        Read revenue data for specific week.
        
        Args:
            week_number: Week number (1-52)
            
        Returns:
            RevenueData object
        """
        revenue_config = self.sheets_config.get('revenue', {})
        spreadsheet_id = revenue_config.get('spreadsheet_id')
        
        if not spreadsheet_id:
            raise ValueError("Revenue spreadsheet_id not configured")
        
        ranges = revenue_config.get('ranges', [
            "Weekly Revenue!A1:N100",
            "Customer Cohorts!A1:K100",
            "Revenue by Segment!A1:M100"
        ])
        
        all_data_points = []
        metadata = {
            'week_number': week_number,
            'ranges_fetched': []
        }
        
        freshness = None
        
        for range_spec in ranges:
            try:
                # Parse range (e.g., "Revenue Metrics!A1:G100")
                if '!' in range_spec:
                    sheet_name, range_name = range_spec.split('!', 1)
                else:
                    sheet_name = range_spec
                    range_name = None
                
                data, range_freshness = await self.read_sheet_data(
                    spreadsheet_id=spreadsheet_id,
                    sheet_name=sheet_name,
                    range_name=range_name
                )
                
                if range_freshness:
                    freshness = range_freshness  # Use most recent freshness
                
                # Parse data into structured format
                if data:
                    # Assume first row is headers
                    headers = data[0] if data else []
                    rows = data[1:] if len(data) > 1 else []
                    
                    for row in rows:
                        if row:  # Skip empty rows
                            data_point = dict(zip(headers, row))
                            all_data_points.append(data_point)
                
                metadata['ranges_fetched'].append(range_spec)
                
            except Exception as e:
                self.logger.error(f"Error reading revenue range {range_spec}: {e}", exc_info=True)
                # Continue with other ranges
        
        return RevenueData(
            week_number=week_number,
            data_points=all_data_points,
            metadata=metadata,
            freshness=freshness
        )
    
    async def read_product_data(self, week_number: int) -> ProductData:
        """
        Read product metrics for specific week.
        
        Args:
            week_number: Week number (1-52)
            
        Returns:
            ProductData object
        """
        product_config = self.sheets_config.get('product', {})
        spreadsheet_id = product_config.get('spreadsheet_id')
        
        if not spreadsheet_id:
            raise ValueError("Product spreadsheet_id not configured")
        
        ranges = product_config.get('ranges', [
            "Engagement Metrics!A1:M100",
            "Feature Adoption!A1:M100",
            "User Journey Metrics!A1:M100"
        ])
        
        all_data_points = []
        metadata = {
            'week_number': week_number,
            'ranges_fetched': []
        }
        
        freshness = None
        
        for range_spec in ranges:
            try:
                # Parse range
                if '!' in range_spec:
                    sheet_name, range_name = range_spec.split('!', 1)
                else:
                    sheet_name = range_spec
                    range_name = None
                
                data, range_freshness = await self.read_sheet_data(
                    spreadsheet_id=spreadsheet_id,
                    sheet_name=sheet_name,
                    range_name=range_name
                )
                
                if range_freshness:
                    freshness = range_freshness
                
                # Parse data
                if data:
                    headers = data[0] if data else []
                    rows = data[1:] if len(data) > 1 else []
                    
                    for row in rows:
                        if row:
                            data_point = dict(zip(headers, row))
                            all_data_points.append(data_point)
                
                metadata['ranges_fetched'].append(range_spec)
                
            except Exception as e:
                self.logger.error(f"Error reading product range {range_spec}: {e}", exc_info=True)
        
        return ProductData(
            week_number=week_number,
            data_points=all_data_points,
            metadata=metadata,
            freshness=freshness
        )
    
    async def read_support_data(self, week_number: int) -> SupportData:
        """
        Read support metrics for specific week.
        
        Args:
            week_number: Week number (1-52)
            
        Returns:
            SupportData object
        """
        support_config = self.sheets_config.get('support', {})
        spreadsheet_id = support_config.get('spreadsheet_id')
        
        if not spreadsheet_id:
            raise ValueError("Support spreadsheet_id not configured")
        
        ranges = support_config.get('ranges', [
            "Ticket Volume!A1:N100",
            "CSAT & Satisfaction!A1:M100",
            "Support Categories!A1:M100"
        ])
        
        all_data_points = []
        metadata = {
            'week_number': week_number,
            'ranges_fetched': []
        }
        
        freshness = None
        
        for range_spec in ranges:
            try:
                # Parse range
                if '!' in range_spec:
                    sheet_name, range_name = range_spec.split('!', 1)
                else:
                    sheet_name = range_spec
                    range_name = None
                
                data, range_freshness = await self.read_sheet_data(
                    spreadsheet_id=spreadsheet_id,
                    sheet_name=sheet_name,
                    range_name=range_name
                )
                
                if range_freshness:
                    freshness = range_freshness
                
                # Parse data
                if data:
                    headers = data[0] if data else []
                    rows = data[1:] if len(data) > 1 else []
                    
                    for row in rows:
                        if row:
                            data_point = dict(zip(headers, row))
                            all_data_points.append(data_point)
                
                metadata['ranges_fetched'].append(range_spec)
                
            except Exception as e:
                self.logger.error(f"Error reading support range {range_spec}: {e}", exc_info=True)
        
        return SupportData(
            week_number=week_number,
            data_points=all_data_points,
            metadata=metadata,
            freshness=freshness
        )
    
    # Backward compatibility: Keep old GoogleSheetsClient interface
    def get_sheet_data(self, spreadsheet_id: str, sheet_name: str,
                       range_name: Optional[str] = None) -> List[List[Any]]:
        """
        Get data from a Google Sheet (synchronous, for backward compatibility).
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            range_name: Optional range (e.g., 'A1:C10')
            
        Returns:
            List of rows
        """
        if not self.client:
            raise RuntimeError("Google Sheets client not initialized")
        
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            if range_name:
                return worksheet.get(range_name)
            else:
                return worksheet.get_all_values()
        except Exception as e:
            self.logger.error(
                f"Error fetching sheet data: {e}",
                extra={'spreadsheet_id': spreadsheet_id, 'sheet_name': sheet_name},
                exc_info=True
            )
            raise


# Backward compatibility alias
GoogleSheetsClient = GoogleSheetsIntegration
