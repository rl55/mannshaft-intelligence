"""
ADK MCP Tools for Google Sheets Integration
Wraps existing Google Sheets integration as ADK FunctionTools.

These tools can be used by ADK agents to fetch data from Google Sheets.
"""

from typing import Dict, Any, Optional, List
from google.adk.tools.function_tool import FunctionTool
from utils.logger import logger

# Import existing Google Sheets integration
from integrations.google_sheets import GoogleSheetsIntegration, RevenueData, ProductData, SupportData
from cache.cache_manager import CacheManager


# Initialize Google Sheets client (shared instance)
_sheets_client: Optional[GoogleSheetsIntegration] = None


def _get_sheets_client() -> GoogleSheetsIntegration:
    """Get or create Google Sheets client instance."""
    global _sheets_client
    if _sheets_client is None:
        _sheets_client = GoogleSheetsIntegration()
    return _sheets_client


async def fetch_revenue_data_from_sheets(
    week_number: int,
    spreadsheet_id: Optional[str] = None,
    revenue_ranges: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch revenue data from Google Sheets.
    
    This ADK tool wraps the existing Google Sheets integration to fetch revenue metrics.
    Supports reading from multiple tabs (e.g., "Weekly Revenue", "Customer Cohorts", "Revenue by Segment").
    
    Args:
        week_number: Week number for analysis (1-52)
        spreadsheet_id: Optional Google Sheets spreadsheet ID (uses config default if not provided)
        revenue_ranges: Optional list of sheet ranges to read (e.g., ["Weekly Revenue!A1:M100", "Customer Cohorts!A1:K50"])
        
    Returns:
        Dictionary containing:
        - week_number: Week number
        - data_points: List of revenue data points
        - metadata: Metadata about the data (spreadsheet_id, sheet_names, etc.)
        - freshness: Data freshness information (hours since update, status)
    """
    try:
        client = _get_sheets_client()
        
        # GoogleSheetsIntegration.read_revenue_data only accepts week_number
        # spreadsheet_id and revenue_ranges are configured in the client instance
        revenue_data: RevenueData = await client.read_revenue_data(
            week_number=week_number
        )
        
        # Convert to dictionary format
        result = {
            "week_number": revenue_data.week_number,
            "data_points": revenue_data.data_points,
            "metadata": revenue_data.metadata,
            "freshness": {
                "sheet_id": revenue_data.freshness.sheet_id if revenue_data.freshness else None,
                "last_updated": revenue_data.freshness.last_updated.isoformat() if revenue_data.freshness else None,
                "freshness_hours": revenue_data.freshness.freshness_hours if revenue_data.freshness else None,
                "status": revenue_data.freshness.status.value if revenue_data.freshness else None,
                "checksum": revenue_data.freshness.checksum if revenue_data.freshness else None
            } if revenue_data.freshness else None
        }
        
        logger.info(f"ADK Tool: Fetched revenue data for week {week_number}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching revenue data: {e}", exc_info=True)
        raise


async def fetch_product_data_from_sheets(
    week_number: int,
    spreadsheet_id: Optional[str] = None,
    product_ranges: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch product metrics data from Google Sheets.
    
    This ADK tool wraps the existing Google Sheets integration to fetch product metrics.
    Supports reading from multiple tabs (e.g., "Engagement Metrics", "Feature Adoption", "User Journey Metrics").
    
    Args:
        week_number: Week number for analysis (1-52)
        spreadsheet_id: Optional Google Sheets spreadsheet ID (uses config default if not provided)
        product_ranges: Optional list of sheet ranges to read
        
    Returns:
        Dictionary containing:
        - week_number: Week number
        - data_points: List of product data points
        - metadata: Metadata about the data
        - freshness: Data freshness information
    """
    try:
        client = _get_sheets_client()
        
        # GoogleSheetsIntegration.read_product_data only accepts week_number
        # spreadsheet_id and product_ranges are configured in the client instance
        product_data: ProductData = await client.read_product_data(
            week_number=week_number
        )
        
        # Convert to dictionary format
        result = {
            "week_number": product_data.week_number,
            "data_points": product_data.data_points,
            "metadata": product_data.metadata,
            "freshness": {
                "sheet_id": product_data.freshness.sheet_id if product_data.freshness else None,
                "last_updated": product_data.freshness.last_updated.isoformat() if product_data.freshness else None,
                "freshness_hours": product_data.freshness.freshness_hours if product_data.freshness else None,
                "status": product_data.freshness.status.value if product_data.freshness else None,
                "checksum": product_data.freshness.checksum if product_data.freshness else None
            } if product_data.freshness else None
        }
        
        logger.info(f"ADK Tool: Fetched product data for week {week_number}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching product data: {e}", exc_info=True)
        raise


async def fetch_support_data_from_sheets(
    week_number: int,
    spreadsheet_id: Optional[str] = None,
    support_ranges: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch support metrics data from Google Sheets.
    
    This ADK tool wraps the existing Google Sheets integration to fetch support metrics.
    Supports reading from multiple tabs (e.g., "Ticket Volume", "CSAT & Satisfaction", "Support Categories").
    
    Args:
        week_number: Week number for analysis (1-52)
        spreadsheet_id: Optional Google Sheets spreadsheet ID (uses config default if not provided)
        support_ranges: Optional list of sheet ranges to read
        
    Returns:
        Dictionary containing:
        - week_number: Week number
        - data_points: List of support data points
        - metadata: Metadata about the data
        - freshness: Data freshness information
    """
    try:
        client = _get_sheets_client()
        
        # GoogleSheetsIntegration.read_support_data only accepts week_number
        # spreadsheet_id and support_ranges are configured in the client instance
        support_data: SupportData = await client.read_support_data(
            week_number=week_number
        )
        
        # Convert to dictionary format
        result = {
            "week_number": support_data.week_number,
            "data_points": support_data.data_points,
            "metadata": support_data.metadata,
            "freshness": {
                "sheet_id": support_data.freshness.sheet_id if support_data.freshness else None,
                "last_updated": support_data.freshness.last_updated.isoformat() if support_data.freshness else None,
                "freshness_hours": support_data.freshness.freshness_hours if support_data.freshness else None,
                "status": support_data.freshness.status.value if support_data.freshness else None,
                "checksum": support_data.freshness.checksum if support_data.freshness else None
            } if support_data.freshness else None
        }
        
        logger.info(f"ADK Tool: Fetched support data for week {week_number}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching support data: {e}", exc_info=True)
        raise


def create_google_sheets_tools() -> List[FunctionTool]:
    """
    Create ADK FunctionTools for Google Sheets operations.
    
    Returns:
        List of FunctionTool instances for revenue, product, and support data fetching
    """
    revenue_tool = FunctionTool(
        fetch_revenue_data_from_sheets,
        require_confirmation=False
    )
    
    product_tool = FunctionTool(
        fetch_product_data_from_sheets,
        require_confirmation=False
    )
    
    support_tool = FunctionTool(
        fetch_support_data_from_sheets,
        require_confirmation=False
    )
    
    logger.info("ADK Google Sheets tools created")
    return [revenue_tool, product_tool, support_tool]

