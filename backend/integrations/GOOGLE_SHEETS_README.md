# Google Sheets MCP Integration

## Overview

Comprehensive Google Sheets integration using MCP (Model Context Protocol) patterns. Provides robust data fetching, caching, freshness tracking, and error handling for SaaS BI Agent system.

## Key Features

### ✅ MCP Protocol Support
- MCP-like patterns for structured data access
- Standardized interface for sheet operations
- Protocol-compliant error handling

### ✅ Authentication
- Service account authentication
- Configurable scopes (readonly by default)
- Credential path from environment/config

### ✅ Data Reading
- Read from specific sheets and ranges
- Support for multiple ranges per spreadsheet
- Automatic header detection and parsing
- Structured data output (RevenueData, ProductData, SupportData)

### ✅ Caching Strategy
- **TTL**: 1 hour default (configurable)
- **Checksum-based**: Detects data changes
- **Cache invalidation**: Automatic on data change
- **Performance**: <100ms cache hits vs ~500ms-2s API calls

### ✅ Data Freshness Tracking
- Tracks last update time per sheet
- Freshness status: FRESH, RECENT, STALE, VERY_STALE
- Hours since last update
- Checksum for change detection

### ✅ Rate Limit Handling
- Automatic retry on rate limits (429)
- Exponential backoff
- Configurable retry attempts (default: 3)
- Rate limit delay between requests

### ✅ Error Handling
- Retry on transient errors (500, 503)
- Clear error messages for auth issues (401, 403)
- Graceful degradation if sheets unavailable
- Comprehensive error logging

## Configuration

### config.yaml

```yaml
google_sheets:
  credentials_path: "${GOOGLE_CREDENTIALS_PATH}"
  scopes:
    - "https://www.googleapis.com/auth/spreadsheets.readonly"
    - "https://www.googleapis.com/auth/drive.readonly"
  max_retries: 3
  retry_delay_seconds: 2
  rate_limit_delay_seconds: 1
  cache_ttl_hours: 1

sheets:
  revenue:
    spreadsheet_id: "${REVENUE_SPREADSHEET_ID}"
    ranges:
      - "Revenue Metrics!A1:G100"
      - "Churn Data!A1:E100"
  
  product:
    spreadsheet_id: "${PRODUCT_SPREADSHEET_ID}"
    ranges:
      - "DAU/WAU!A1:F100"
      - "Feature Adoption!A1:H100"
  
  support:
    spreadsheet_id: "${SUPPORT_SPREADSHEET_ID}"
    ranges:
      - "Ticket Volume!A1:E100"
      - "CSAT Scores!A1:D50"
```

### Environment Variables

```bash
GOOGLE_CREDENTIALS_PATH=/path/to/service-account.json
REVENUE_SPREADSHEET_ID=1abc...
PRODUCT_SPREADSHEET_ID=1def...
SUPPORT_SPREADSHEET_ID=1ghi...
```

## Interface

### GoogleSheetsIntegration Class

```python
from integrations.google_sheets import GoogleSheetsIntegration
from cache.cache_manager import CacheManager

# Initialize
cache_manager = CacheManager()
sheets = GoogleSheetsIntegration(cache_manager)
```

### Read Revenue Data

```python
revenue_data = await sheets.read_revenue_data(week_number=25)

# Returns RevenueData:
# - week_number: int
# - data_points: List[Dict[str, Any]]
# - metadata: Dict[str, Any]
# - freshness: Optional[DataFreshness]
```

### Read Product Data

```python
product_data = await sheets.read_product_data(week_number=25)

# Returns ProductData:
# - week_number: int
# - data_points: List[Dict[str, Any]]
# - metadata: Dict[str, Any]
# - freshness: Optional[DataFreshness]
```

### Read Support Data

```python
support_data = await sheets.read_support_data(week_number=25)

# Returns SupportData:
# - week_number: int
# - data_points: List[Dict[str, Any]]
# - metadata: Dict[str, Any]
# - freshness: Optional[DataFreshness]
```

### Check Data Freshness

```python
freshness = sheets.check_data_freshness(sheet_id="1abc...")

# Returns DataFreshness:
# - sheet_id: str
# - last_updated: datetime
# - freshness_hours: float
# - status: DataFreshnessStatus (FRESH/RECENT/STALE/VERY_STALE)
# - checksum: str
```

### Read Sheet Data (Generic)

```python
data, freshness = await sheets.read_sheet_data(
    spreadsheet_id="1abc...",
    sheet_name="Revenue Metrics",
    range_name="A1:G100",
    use_cache=True
)
```

## Data Structures

### RevenueData

```python
@dataclass
class RevenueData:
    week_number: int
    data_points: List[Dict[str, Any]]  # Parsed rows as dictionaries
    metadata: Dict[str, Any]  # Ranges fetched, etc.
    freshness: Optional[DataFreshness] = None
```

### ProductData

```python
@dataclass
class ProductData:
    week_number: int
    data_points: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    freshness: Optional[DataFreshness] = None
```

### SupportData

```python
@dataclass
class SupportData:
    week_number: int
    data_points: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    freshness: Optional[DataFreshness] = None
```

### DataFreshness

```python
@dataclass
class DataFreshness:
    sheet_id: str
    last_updated: datetime
    freshness_hours: float
    status: DataFreshnessStatus  # FRESH/RECENT/STALE/VERY_STALE
    checksum: str
```

## Caching Strategy

### Cache Key Format

```
{spreadsheet_id}:{sheet_name}:{range_name or 'all'}
```

### Cache Invalidation

- **TTL-based**: Expires after configured hours (default: 1 hour)
- **Checksum-based**: Detects data changes
- **Automatic**: Re-fetches if checksum differs

### Cache Storage

Uses `agent_responses` table:
- `agent_type`: 'google_sheets'
- `request_params`: JSON with cache_key
- `response`: JSON array of rows
- `metadata`: JSON with checksum and cached_at

## Rate Limiting

### Handling 429 (Too Many Requests)

1. Detect rate limit error
2. Calculate exponential backoff: `delay * (2 ** attempt)`
3. Wait before retry
4. Retry up to `max_retries` times

### Rate Limit Prevention

- Configurable delay between requests (`rate_limit_delay_seconds`)
- Automatic throttling
- Request queuing (future enhancement)

## Error Handling

### Retry Logic

- **Transient errors** (500, 503): Retry with exponential backoff
- **Rate limits** (429): Retry with exponential backoff
- **Auth errors** (401, 403): Fail immediately with clear error
- **Not found** (404): Fail immediately with clear error
- **Max retries**: 3 attempts (configurable)

### Error Types

```python
# Rate limit
HttpError with status 429 → Retry with backoff

# Transient server error
HttpError with status 500/503 → Retry

# Auth error
HttpError with status 401/403 → Fail immediately

# Not found
HttpError with status 404 → Fail immediately

# Other errors
Exception → Log and raise
```

## Usage Examples

### Basic Usage

```python
from integrations.google_sheets import GoogleSheetsIntegration
from cache.cache_manager import CacheManager

cache_manager = CacheManager()
sheets = GoogleSheetsIntegration(cache_manager)

# Read revenue data
revenue = await sheets.read_revenue_data(week_number=25)
print(f"Data points: {len(revenue.data_points)}")
print(f"Freshness: {revenue.freshness.freshness_hours:.1f} hours")
print(f"Status: {revenue.freshness.status.value}")
```

### Check Freshness

```python
freshness = sheets.check_data_freshness("1abc...")

if freshness:
    if freshness.status == DataFreshnessStatus.VERY_STALE:
        print("Warning: Data is very stale!")
    print(f"Last updated: {freshness.last_updated}")
    print(f"Hours old: {freshness.freshness_hours:.1f}")
```

### Custom Range Reading

```python
data, freshness = await sheets.read_sheet_data(
    spreadsheet_id="1abc...",
    sheet_name="Revenue Metrics",
    range_name="A1:G100",
    use_cache=True
)

# data is List[List[Any]] (rows)
# freshness is Optional[DataFreshness]
```

### Error Handling

```python
try:
    revenue = await sheets.read_revenue_data(week_number=25)
except RuntimeError as e:
    print(f"Client not initialized: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Backward Compatibility

The old `GoogleSheetsClient` interface is maintained:

```python
# Old interface (still works)
client = GoogleSheetsClient()
data = client.get_sheet_data(
    spreadsheet_id="1abc...",
    sheet_name="Sheet1",
    range_name="A1:C10"
)

# New interface (recommended)
integration = GoogleSheetsIntegration(cache_manager)
data, freshness = await integration.read_sheet_data(
    spreadsheet_id="1abc...",
    sheet_name="Sheet1",
    range_name="A1:C10"
)
```

## Performance

- **Cache Hit**: <100ms
- **Cache Miss**: 500ms-2s (depends on sheet size)
- **Rate Limited**: Adds exponential backoff delay
- **Concurrent Requests**: Supported (async)

## Dependencies

- `gspread`: Google Sheets API client
- `google-auth`: Authentication
- `google-api-python-client`: Advanced API operations
- `cache.cache_manager`: Caching and storage

## Testing

```python
import pytest
from integrations.google_sheets import GoogleSheetsIntegration

@pytest.mark.asyncio
async def test_read_revenue_data():
    sheets = GoogleSheetsIntegration()
    
    revenue = await sheets.read_revenue_data(week_number=25)
    
    assert revenue.week_number == 25
    assert len(revenue.data_points) > 0
    assert revenue.freshness is not None
```

## Troubleshooting

### Credentials Not Found

```
Error: Credentials file not found
```

**Solution**: Set `GOOGLE_CREDENTIALS_PATH` environment variable or configure in `config.yaml`.

### Rate Limited

```
Warning: Rate limited, waiting 4s before retry
```

**Solution**: Increase `rate_limit_delay_seconds` or reduce request frequency.

### Sheet Not Found

```
Error: HTTP error 404
```

**Solution**: Verify spreadsheet ID and ensure service account has access.

### Stale Data

```
Status: VERY_STALE
```

**Solution**: Data hasn't been updated in 7+ days. Check data source or refresh manually.

