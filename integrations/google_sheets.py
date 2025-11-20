"""
Google Sheets integration using MCP (Model Context Protocol).
"""

from typing import Dict, Any, List, Optional
import gspread
from google.oauth2.service_account import Credentials

from utils.config import config
from utils.logger import logger


class GoogleSheetsClient:
    """
    Client for interacting with Google Sheets via MCP.
    """
    
    def __init__(self):
        self.logger = logger.getChild('google_sheets')
        self.client: Optional[gspread.Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets client."""
        try:
            credentials_path = config.get('google_sheets.credentials_path')
            if not credentials_path:
                self.logger.warning("Google Sheets credentials path not configured")
                return
            
            scopes = config.get('google_sheets.scopes', [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ])
            
            creds = Credentials.from_service_account_file(
                credentials_path,
                scopes=scopes
            )
            
            self.client = gspread.authorize(creds)
            self.logger.info("Google Sheets client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets client: {e}", exc_info=True)
    
    def get_sheet_data(self, spreadsheet_id: str, sheet_name: str,
                       range_name: Optional[str] = None) -> List[List[Any]]:
        """
        Get data from a Google Sheet.
        
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

