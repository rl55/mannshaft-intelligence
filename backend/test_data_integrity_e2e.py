"""
Comprehensive End-to-End Data Integrity Test

This test verifies:
1. Raw data is fetched correctly from Google Sheets
2. Calculations are done correctly (especially churn rate)
3. Agents analyze data correctly
4. Report generation uses correct information
5. Data integrity throughout the pipeline
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, '.')

from agents.revenue_agent import RevenueAgent
from agents.product_agent import ProductAgent
from agents.support_agent import SupportAgent
from agents.synthesizer_agent import SynthesizerAgent
from agents.orchestrator import OrchestratorAgent
from cache.cache_manager import CacheManager
from integrations.google_sheets import GoogleSheetsClient
from utils.config import config
from utils.logger import logger


class DataIntegrityTester:
    """Comprehensive data integrity tester."""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.sheets_client = GoogleSheetsClient()
        self.errors = []
        self.warnings = []
        self.test_results = {}
        
    def log_error(self, test_name: str, error: str):
        """Log an error."""
        self.errors.append(f"[{test_name}] {error}")
        print(f"❌ ERROR [{test_name}]: {error}")
        
    def log_warning(self, test_name: str, warning: str):
        """Log a warning."""
        self.warnings.append(f"[{test_name}] {warning}")
        print(f"⚠️  WARNING [{test_name}]: {warning}")
        
    def log_success(self, test_name: str, message: str):
        """Log a success."""
        print(f"✅ SUCCESS [{test_name}]: {message}")
        
    async def test_raw_data_fetching(self, week_number: int = 10):
        """Test 1: Verify raw data is fetched correctly from Google Sheets."""
        print("\n" + "="*80)
        print("TEST 1: Raw Data Fetching from Google Sheets")
        print("="*80)
        
        test_name = "Raw Data Fetching"
        results = {}
        
        try:
            # Fetch revenue data
            revenue_spreadsheet_id = config.get('sheets.revenue.spreadsheet_id')
            # Get sheet name from config (same logic as orchestrator)
            revenue_ranges = config.get('sheets.revenue.ranges', ['Weekly Revenue!A1:N100'])
            revenue_sheet_name = revenue_ranges[0].split('!')[0] if revenue_ranges else 'Weekly Revenue'
            
            print(f"\nFetching revenue data from sheet: {revenue_spreadsheet_id}")
            revenue_rows = self.sheets_client.get_sheet_data(
                spreadsheet_id=revenue_spreadsheet_id,
                sheet_name=revenue_sheet_name,
                range_name='A1:Z100'
            )
            
            if not revenue_rows or len(revenue_rows) < 2:
                self.log_error(test_name, "No revenue data found in sheet")
                return results
                
            # Parse headers
            headers = [str(h).strip().lower() for h in revenue_rows[0]]
            print(f"Found headers: {headers[:10]}...")  # Show first 10
            
            # Find Week 10 data
            week_col_idx = None
            churn_rate_col_idx = None
            churned_col_idx = None
            customer_count_col_idx = None
            new_customers_col_idx = None
            
            for i, header in enumerate(headers):
                if 'week' in header:
                    week_col_idx = i
                elif 'churn rate' in header or 'churn_rate' in header:
                    churn_rate_col_idx = i
                elif 'churned' in header and 'customer' in header:
                    churned_col_idx = i
                elif 'customer count' in header or 'customer_count' in header:
                    customer_count_col_idx = i
                elif 'new customer' in header or 'new_customer' in header:
                    new_customers_col_idx = i
            
            print(f"\nColumn indices:")
            print(f"  Week: {week_col_idx}")
            print(f"  Churn Rate: {churn_rate_col_idx}")
            print(f"  Churned Customers: {churned_col_idx}")
            print(f"  Customer Count: {customer_count_col_idx}")
            print(f"  New Customers: {new_customers_col_idx}")
            
            # Find Week 10 row
            week_10_row = None
            week_10_idx = None
            for idx, row in enumerate(revenue_rows[1:], start=1):
                if week_col_idx is not None and idx < len(row):
                    try:
                        week_val = int(float(str(row[week_col_idx])))
                        if week_val == week_number:
                            week_10_row = row
                            week_10_idx = idx
                            break
                    except (ValueError, TypeError):
                        continue
            
            if not week_10_row:
                self.log_error(test_name, f"Week {week_number} not found in sheet")
                return results
            
            print(f"\nFound Week {week_number} at row {week_10_idx + 1}")
            
            # Extract values
            raw_data = {}
            if churn_rate_col_idx is not None and churn_rate_col_idx < len(week_10_row):
                try:
                    raw_data['churn_rate'] = float(week_10_row[churn_rate_col_idx])
                except (ValueError, TypeError):
                    raw_data['churn_rate'] = None
            else:
                raw_data['churn_rate'] = None
                
            if churned_col_idx is not None and churned_col_idx < len(week_10_row):
                try:
                    raw_data['churned'] = int(float(str(week_10_row[churned_col_idx])))
                except (ValueError, TypeError):
                    raw_data['churned'] = None
            else:
                raw_data['churned'] = None
                
            if customer_count_col_idx is not None and customer_count_col_idx < len(week_10_row):
                try:
                    raw_data['customer_count'] = int(float(str(week_10_row[customer_count_col_idx])))
                except (ValueError, TypeError):
                    raw_data['customer_count'] = None
            else:
                raw_data['customer_count'] = None
                
            if new_customers_col_idx is not None and new_customers_col_idx < len(week_10_row):
                try:
                    raw_data['new_customers'] = int(float(str(week_10_row[new_customers_col_idx])))
                except (ValueError, TypeError):
                    raw_data['new_customers'] = None
            else:
                raw_data['new_customers'] = None
            
            print(f"\nRaw data from sheet for Week {week_number}:")
            print(f"  Churn Rate (%): {raw_data['churn_rate']}")
            print(f"  Churned Customers: {raw_data['churned']}")
            print(f"  Customer Count: {raw_data['customer_count']}")
            print(f"  New Customers: {raw_data['new_customers']}")
            
            results['raw_data'] = raw_data
            results['week_found'] = True
            
            # Validate raw data
            if raw_data['churn_rate'] is None:
                self.log_warning(test_name, "Churn rate not found in sheet")
            else:
                self.log_success(test_name, f"Churn rate from sheet: {raw_data['churn_rate']}%")
                
            if raw_data['churned'] is None:
                self.log_warning(test_name, "Churned customers not found in sheet")
            else:
                self.log_success(test_name, f"Churned customers: {raw_data['churned']}")
                
            if raw_data['customer_count'] is None:
                self.log_warning(test_name, "Customer count not found in sheet")
            else:
                self.log_success(test_name, f"Customer count: {raw_data['customer_count']}")
            
            self.test_results['raw_data'] = results
            return results
            
        except Exception as e:
            self.log_error(test_name, f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return results
    
    async def test_churn_calculation(self, week_number: int = 10):
        """Test 2: Verify churn rate calculation is correct."""
        print("\n" + "="*80)
        print("TEST 2: Churn Rate Calculation")
        print("="*80)
        
        test_name = "Churn Calculation"
        results = {}
        
        try:
            # Get raw data first
            raw_data_result = await self.test_raw_data_fetching(week_number)
            raw_data = raw_data_result.get('raw_data', {})
            
            if not raw_data:
                self.log_error(test_name, "Cannot test calculation without raw data")
                return results
            
            # Initialize revenue agent
            revenue_agent = RevenueAgent(self.cache_manager)
            
            # Create test data structure matching what agent receives
            test_records = []
            
            # We need to fetch multiple weeks to test properly
            revenue_spreadsheet_id = config.get('sheets.revenue.spreadsheet_id')
            # Extract sheet name from ranges (same logic as orchestrator)
            revenue_ranges = config.get('sheets.revenue.ranges', ['Weekly Revenue!A1:N100'])
            revenue_sheet_name = revenue_ranges[0].split('!')[0] if revenue_ranges else 'Weekly Revenue'
            
            revenue_rows = self.sheets_client.get_sheet_data(
                spreadsheet_id=revenue_spreadsheet_id,
                sheet_name=revenue_sheet_name,
                range_name='A1:Z100'
            )
            
            if not revenue_rows or len(revenue_rows) < 2:
                self.log_error(test_name, "Cannot fetch data for calculation test")
                return results
            
            # Parse data using agent's parser
            parsed_data = revenue_agent._parse_sheet_data(revenue_rows, [])
            records = parsed_data.get('records', [])
            
            # Debug: Print first record to see what's parsed
            if records:
                print(f"\nDEBUG: First parsed record keys: {list(records[0].keys())}")
                print(f"DEBUG: First parsed record: {records[0]}")
            
            # Find Week 10 and Week 9 records
            week_10_record = next((r for r in records if r.get('week') == week_number), None)
            week_9_record = next((r for r in records if r.get('week') == week_number - 1), None)
            
            if not week_10_record:
                self.log_error(test_name, f"Week {week_number} record not found in parsed data")
                print(f"DEBUG: Available weeks in parsed data: {[r.get('week') for r in records]}")
                return results
            
            print(f"\nParsed Week {week_number} record:")
            print(f"  Week: {week_10_record.get('week')}")
            print(f"  Churn Rate: {week_10_record.get('churn_rate')}")
            print(f"  Churned: {week_10_record.get('churned')}")
            print(f"  Customer Count: {week_10_record.get('customer_count')}")
            print(f"  New Customers: {week_10_record.get('new_customers')}")
            print(f"  All keys: {list(week_10_record.keys())}")
            
            # Test statistical analysis
            test_data = {'records': records, 'total_records': len(records)}
            statistical_result = revenue_agent._perform_statistical_analysis(
                test_data, 
                target_week=week_number
            )
            
            calculated_churn_rate = statistical_result.get('churn_rate', 0)
            churn_change = statistical_result.get('churn_change_from_previous', 0)
            
            print(f"\nStatistical Analysis Results:")
            print(f"  Calculated Churn Rate: {calculated_churn_rate} ({calculated_churn_rate * 100:.2f}%)")
            print(f"  Churn Change: {churn_change} ({churn_change * 100:.2f}pp)")
            
            # Verify calculation
            expected_churn_rate = None
            if week_10_record.get('churn_rate') is not None:
                # Use churn_rate from sheet (convert % to decimal if needed)
                churn_rate_raw = week_10_record.get('churn_rate')
                expected_churn_rate = churn_rate_raw / 100.0 if churn_rate_raw > 1 else churn_rate_raw
            elif week_10_record.get('customer_count') and week_10_record.get('customer_count') > 0:
                # Calculate from churned / customer_count
                expected_churn_rate = week_10_record.get('churned', 0) / week_10_record.get('customer_count')
            
            if expected_churn_rate is not None:
                tolerance = 0.0001
                if abs(calculated_churn_rate - expected_churn_rate) < tolerance:
                    self.log_success(
                        test_name, 
                        f"Churn rate calculation correct: {calculated_churn_rate:.4f} = {expected_churn_rate:.4f}"
                    )
                    results['calculation_correct'] = True
                else:
                    self.log_error(
                        test_name,
                        f"Churn rate mismatch! Calculated: {calculated_churn_rate:.4f}, Expected: {expected_churn_rate:.4f}"
                    )
                    results['calculation_correct'] = False
            else:
                self.log_warning(test_name, "Cannot verify calculation - missing expected value")
            
            # Verify it's not the wrong calculation (churned / new_customers)
            if week_10_record.get('churned') and week_10_record.get('new_customers'):
                wrong_calculation = week_10_record.get('churned') / week_10_record.get('new_customers')
                if abs(calculated_churn_rate - wrong_calculation) < 0.01:
                    self.log_error(
                        test_name,
                        f"CRITICAL: Using wrong calculation! churned/new_customers = {wrong_calculation:.4f}"
                    )
                    results['wrong_calculation_detected'] = True
                else:
                    self.log_success(
                        test_name,
                        f"Not using wrong calculation (churned/new_customers = {wrong_calculation:.4f})"
                    )
                    results['wrong_calculation_detected'] = False
            
            results['calculated_churn_rate'] = calculated_churn_rate
            results['churn_change'] = churn_change
            results['week_10_record'] = week_10_record
            
            self.test_results['churn_calculation'] = results
            return results
            
        except Exception as e:
            self.log_error(test_name, f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return results
    
    async def test_agent_analysis(self, week_number: int = 10):
        """Test 3: Verify agents analyze data correctly."""
        print("\n" + "="*80)
        print("TEST 3: Agent Analysis")
        print("="*80)
        
        test_name = "Agent Analysis"
        results = {}
        
        try:
            # Test Revenue Agent
            print("\n--- Testing Revenue Agent ---")
            revenue_agent = RevenueAgent(self.cache_manager)
            
            # Extract sheet name from ranges (same logic as orchestrator)
            revenue_ranges = config.get('sheets.revenue.ranges', ['Weekly Revenue!A1:N100'])
            revenue_sheet_name = revenue_ranges[0].split('!')[0] if revenue_ranges else 'Weekly Revenue'
            
            context = {
                'spreadsheet_id': config.get('sheets.revenue.spreadsheet_id'),
                'revenue_sheet': revenue_sheet_name,
                'week_number': week_number,
                'analysis_type': 'comprehensive'
            }
            
            session_id = f"test_session_{datetime.now().timestamp()}"
            revenue_result = await revenue_agent.execute(context, session_id)
            
            if revenue_result.get('cached'):
                print("⚠️  Revenue agent result was cached - clearing cache for accurate test")
                # Clear cache and retry
                if hasattr(self.cache_manager, 'clear_cache'):
                    self.cache_manager.clear_cache()
                else:
                    # Fallback: manually clear cache tables
                    conn = self.cache_manager.connect()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM prompt_cache")
                    cursor.execute("DELETE FROM agent_responses")
                    conn.commit()
                revenue_result = await revenue_agent.execute(context, session_id)
            
            revenue_response = revenue_result.get('response', '{}')
            if isinstance(revenue_response, str):
                revenue_analysis = json.loads(revenue_response)
            else:
                revenue_analysis = revenue_response
            
            revenue_churn = revenue_analysis.get('analysis', {}).get('churn_analysis', {})
            revenue_churn_rate = revenue_churn.get('current_rate', 0)
            
            print(f"Revenue Agent Churn Rate: {revenue_churn_rate} ({revenue_churn_rate * 100:.2f}%)")
            print(f"Revenue Agent Churn Change: {revenue_churn.get('change_from_previous', 0)}")
            
            # Verify churn rate matches expected
            churn_calc_result = self.test_results.get('churn_calculation', {})
            expected_churn = churn_calc_result.get('calculated_churn_rate')
            
            if expected_churn is not None:
                tolerance = 0.0001
                if abs(revenue_churn_rate - expected_churn) < tolerance:
                    self.log_success(
                        test_name,
                        f"Revenue agent churn rate matches calculation: {revenue_churn_rate:.4f}"
                    )
                    results['revenue_churn_correct'] = True
                else:
                    self.log_error(
                        test_name,
                        f"Revenue agent churn rate mismatch! Agent: {revenue_churn_rate:.4f}, Expected: {expected_churn:.4f}"
                    )
                    results['revenue_churn_correct'] = False
            else:
                self.log_warning(test_name, "Cannot verify revenue agent churn rate - missing expected value")
            
            # Check if churn rate is reasonable (not 29.7%)
            if revenue_churn_rate > 0.05:  # More than 5%
                self.log_error(
                    test_name,
                    f"CRITICAL: Revenue agent churn rate seems too high: {revenue_churn_rate * 100:.1f}%"
                )
                results['revenue_churn_reasonable'] = False
            else:
                self.log_success(
                    test_name,
                    f"Revenue agent churn rate is reasonable: {revenue_churn_rate * 100:.2f}%"
                )
                results['revenue_churn_reasonable'] = True
            
            results['revenue_analysis'] = revenue_analysis
            results['revenue_churn_rate'] = revenue_churn_rate
            
            self.test_results['agent_analysis'] = results
            return results
            
        except Exception as e:
            self.log_error(test_name, f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return results
    
    async def test_full_analysis(self, week_number: int = 10):
        """Test 4: Run full analysis and verify report generation."""
        print("\n" + "="*80)
        print("TEST 4: Full Analysis and Report Generation")
        print("="*80)
        
        test_name = "Full Analysis"
        results = {}
        
        try:
            # Clear cache to ensure fresh analysis
            # Delete all cache entries for this test
            conn = self.cache_manager.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM prompt_cache")
            cursor.execute("DELETE FROM agent_responses")
            conn.commit()
            
            # Initialize orchestrator
            orchestrator = OrchestratorAgent(self.cache_manager)
            
            session_id = f"test_full_{datetime.now().timestamp()}"
            
            print(f"\nRunning full analysis for Week {week_number}...")
            print(f"Session ID: {session_id}")
            
            # Run analysis
            analysis_result = await orchestrator.analyze_week(
                week_number=week_number,
                user_id='test_user',
                session_id=session_id,
                analysis_type='comprehensive'
            )
            
            print("\nAnalysis completed!")
            
            # Extract results (AnalysisResult is a Pydantic model)
            if hasattr(analysis_result, 'dict'):
                result_dict = analysis_result.dict()
            elif hasattr(analysis_result, '__dict__'):
                result_dict = analysis_result.__dict__
            else:
                result_dict = analysis_result
            
            metadata = result_dict.get('metadata', {})
            analytical_results = metadata.get('analytical_results', {})
            
            # Check revenue agent result
            revenue_result = analytical_results.get('revenue', {})
            revenue_response = revenue_result.get('response', '{}')
            if isinstance(revenue_response, str):
                revenue_analysis = json.loads(revenue_response)
            else:
                revenue_analysis = revenue_response
            
            revenue_churn = revenue_analysis.get('analysis', {}).get('churn_analysis', {})
            final_churn_rate = revenue_churn.get('current_rate', 0)
            
            print(f"\nFinal Report Churn Rate: {final_churn_rate} ({final_churn_rate * 100:.2f}%)")
            
            # Verify against expected
            churn_calc_result = self.test_results.get('churn_calculation', {})
            expected_churn = churn_calc_result.get('calculated_churn_rate')
            
            if expected_churn is not None:
                tolerance = 0.0001
                if abs(final_churn_rate - expected_churn) < tolerance:
                    self.log_success(
                        test_name,
                        f"Final report churn rate matches expected: {final_churn_rate:.4f}"
                    )
                    results['final_churn_correct'] = True
                else:
                    self.log_error(
                        test_name,
                        f"Final report churn rate mismatch! Report: {final_churn_rate:.4f}, Expected: {expected_churn:.4f}"
                    )
                    results['final_churn_correct'] = False
            
            # Check synthesizer report
            synthesizer_result = analytical_results.get('synthesizer', {})
            synthesizer_response = synthesizer_result.get('response', '{}')
            if isinstance(synthesizer_response, str):
                synthesizer_report = json.loads(synthesizer_response)
            else:
                synthesizer_report = synthesizer_response
            
            executive_summary = synthesizer_report.get('executive_summary', '')
            print(f"\nExecutive Summary (first 200 chars):")
            print(executive_summary[:200] + "...")
            
            # Check if executive summary mentions incorrect churn
            if '29.7' in executive_summary or '29.7%' in executive_summary:
                self.log_error(
                    test_name,
                    "CRITICAL: Executive summary mentions incorrect churn rate (29.7%)"
                )
                results['executive_summary_correct'] = False
            elif 'elevated churn' in executive_summary.lower() and final_churn_rate < 0.03:
                self.log_warning(
                    test_name,
                    f"Executive summary mentions 'elevated churn' but churn rate is only {final_churn_rate * 100:.2f}%"
                )
                results['executive_summary_correct'] = True  # Not an error, just a warning
            else:
                self.log_success(
                    test_name,
                    "Executive summary does not contain incorrect churn references"
                )
                results['executive_summary_correct'] = True
            
            results['analysis_result'] = analysis_result
            results['final_churn_rate'] = final_churn_rate
            results['executive_summary'] = executive_summary
            
            self.test_results['full_analysis'] = results
            return results
            
        except Exception as e:
            self.log_error(test_name, f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return results
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        print(f"\nTotal Errors: {len(self.errors)}")
        print(f"Total Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All tests passed! Data integrity is verified.")
        elif not self.errors:
            print("\n✅ No critical errors! Some warnings present.")
        else:
            print("\n❌ Critical errors found! Data integrity issues detected.")
        
        print("\n" + "="*80)


async def main():
    """Run comprehensive data integrity tests."""
    print("\n" + "="*80)
    print("COMPREHENSIVE DATA INTEGRITY TEST")
    print("="*80)
    print(f"Started at: {datetime.now().isoformat()}")
    
    tester = DataIntegrityTester()
    
    week_number = 10
    
    # Run all tests
    await tester.test_raw_data_fetching(week_number)
    await tester.test_churn_calculation(week_number)
    await tester.test_agent_analysis(week_number)
    await tester.test_full_analysis(week_number)
    
    # Print summary
    tester.print_summary()
    
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    
    # Return exit code based on errors
    return 0 if not tester.errors else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

