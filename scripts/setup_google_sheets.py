#!/usr/bin/env python3
"""
Google Sheets Setup Script
Creates and populates synthetic SaaS data sheets
"""

import sys
import json
from pathlib import Path
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# Revenue data
REVENUE_DATA = [
    ["Week", "Start Date", "End Date", "MRR", "New MRR", "Churned MRR", "Expansion MRR", "Contraction MRR",
        "Customer Count", "New Customers", "Churned Customers", "ARPU", "Churn Rate %", "MRR Growth %"],
    [1, "2025-09-01", "2025-09-07", 980000, 45000, 28000,
        12000, 8000, 4900, 225, 140, 200.00, 2.86, 2.97],
    [2, "2025-09-08", "2025-09-14", 1009200, 52000, 22800,
        15000, 5000, 5037, 260, 114, 200.32, 2.26, 2.98],
    [3, "2025-09-15", "2025-09-21", 1048600, 58000, 18600,
        22000, 6000, 5183, 290, 95, 202.35, 1.77, 3.90],
    [4, "2025-09-22", "2025-09-28", 1089400, 62000, 21200,
        25000, 7000, 5330, 310, 106, 204.39, 1.99, 3.89],
    [5, "2025-09-29", "2025-10-05", 1128200, 65000, 26200,
        28000, 8000, 5489, 325, 119, 205.56, 2.17, 3.56],
    [6, "2025-10-06", "2025-10-12", 1165800, 68000, 30400,
        32000, 9000, 5635, 340, 128, 206.92, 2.27, 3.34],
    [7, "2025-10-13", "2025-10-19", 1198600, 71000, 38200,
        35000, 11000, 5706, 355, 142, 210.01, 2.49, 2.81],
    [8, "2025-10-20", "2025-10-26", 1250000, 75000, 23600,
        40000, 7000, 5811, 375, 118, 215.09, 2.07, 4.29],
    [9, "2025-10-27", "2025-11-02", 1312500, 82000, 19500,
        45000, 6000, 5968, 410, 98, 219.91, 1.64, 5.00],
    [10, "2025-11-03", "2025-11-09", 1378125, 88000, 22375,
        48000, 7000, 6156, 440, 112, 223.85, 1.82, 5.00],
    [11, "2025-11-10", "2025-11-16", 1447031, 95000, 26094,
        52000, 8000, 6344, 475, 131, 228.14, 2.07, 5.00],
    [12, "2025-11-17", "2025-11-23", 1519383, 102000, 29648,
        55000, 9000, 6536, 510, 148, 232.48, 2.26, 5.00],
]

# Product engagement data
PRODUCT_DATA = [
    ["Week", "Start Date", "DAU", "WAU", "MAU", "DAU/MAU Ratio %", "WAU/MAU Ratio %",
        "Avg Session Duration (min)", "Sessions per User", "Weekly Active Rate %", "Power Users", "Casual Users", "At-Risk Users"],
    [1, "2025-09-01", 12250, 28420, 45800, 26.7,
        62.1, 18.5, 4.2, 58.3, 3680, 20140, 4560],
    [2, "2025-09-08", 12586, 29192, 47036, 26.8,
        62.1, 18.8, 4.3, 58.5, 3778, 20694, 4728],
    [3, "2025-09-15", 12930, 29985, 48311, 26.8,
        62.1, 19.1, 4.4, 58.7, 3879, 21265, 4901],
    [4, "2025-09-22", 13282, 30798, 49626, 26.8,
        62.1, 19.4, 4.5, 58.9, 3983, 21853, 5078],
    [5, "2025-09-29", 13643, 31632, 50983, 26.8,
        62.0, 19.7, 4.6, 59.1, 4090, 22458, 5261],
    [6, "2025-10-06", 14013, 32488, 52382, 26.7,
        62.0, 20.0, 4.7, 59.3, 4200, 23081, 5449],
    [7, "2025-10-13", 14393, 33366, 53825, 26.7,
        62.0, 20.3, 4.8, 59.5, 4313, 23721, 5642],
    [8, "2025-10-20", 14783, 34268, 55314, 26.7,
        61.9, 20.6, 4.9, 59.7, 4429, 24379, 5841],
    [9, "2025-10-27", 15183, 35193, 56848, 26.7,
        61.9, 20.9, 5.0, 59.9, 4549, 25055, 6045],
    [10, "2025-11-03", 15594, 36142, 58430, 26.7,
        61.9, 21.2, 5.1, 60.1, 4672, 25750, 6254],
    [11, "2025-11-10", 16016, 37116, 60062, 26.7,
        61.8, 21.5, 5.2, 60.3, 4798, 26463, 6469],
    [12, "2025-11-17", 16449, 38116, 61744, 26.6,
        61.7, 21.8, 5.3, 60.5, 4928, 27196, 6690],
]

# Support ticket data
SUPPORT_DATA = [
    ["Week", "Start Date", "Total Tickets", "New Tickets", "Resolved Tickets", "Pending Tickets", "Bug Reports", "Feature Requests",
        "How-To Questions", "Account Issues", "First Response Time (hours)", "Resolution Time (hours)", "Tickets per Customer", "CSAT Score"],
    [1, "2025-09-01", 1225, 980, 892, 333, 196,
        147, 441, 196, 4.2, 18.5, 0.25, 4.2],
    [2, "2025-09-08", 1189, 950, 925, 314, 190,
        142, 428, 190, 3.9, 17.8, 0.24, 4.3],
    [3, "2025-09-15", 1155, 922, 895, 296, 184,
        138, 415, 184, 3.7, 17.2, 0.22, 4.3],
    [4, "2025-09-22", 1122, 896, 870, 278, 179,
        134, 403, 179, 3.5, 16.6, 0.21, 4.4],
    [5, "2025-09-29", 1090, 871, 845, 261, 174,
        131, 392, 174, 3.3, 16.1, 0.20, 4.4],
    [6, "2025-10-06", 1059, 847, 822, 244, 169,
        127, 381, 169, 3.2, 15.6, 0.19, 4.5],
    [7, "2025-10-13", 1029, 823, 799, 228, 164,
        123, 370, 164, 3.1, 15.1, 0.18, 4.5],
    [8, "2025-10-20", 1000, 800, 776, 212, 160,
        120, 360, 160, 2.9, 14.6, 0.17, 4.6],
    [9, "2025-10-27", 972, 780, 755, 197, 156,
        117, 351, 156, 2.8, 14.2, 0.16, 4.6],
    [10, "2025-11-03", 945, 761, 735, 183, 152,
        114, 342, 152, 2.7, 13.8, 0.15, 4.7],
    [11, "2025-11-10", 919, 743, 715, 169, 149,
        111, 334, 149, 2.6, 13.4, 0.14, 4.7],
    [12, "2025-11-17", 894, 725, 696, 155, 145,
        109, 326, 145, 2.5, 13.1, 0.14, 4.8],
]


def create_sheet_with_data(gc, title, data):
    """Create a Google Sheet and populate it with data"""

    print(f"   Creating sheet: {title}...")

    try:
        # Create new spreadsheet
        spreadsheet = gc.create(title)

        # Get the first worksheet
        worksheet = spreadsheet.sheet1
        worksheet.update_title("Weekly Metrics")

        # Update with data
        worksheet.update('A1', data)

        # Format header row
        worksheet.format('A1:Z1', {
            "backgroundColor": {
                "red": 0.2,
                "green": 0.2,
                "blue": 0.3
            },
            "textFormat": {
                "bold": True,
                "foregroundColor": {
                    "red": 1.0,
                    "green": 1.0,
                    "blue": 1.0
                }
            }
        })

        # Auto-resize columns
        worksheet.columns_auto_resize(0, len(data[0]))

        print(f"   ✅ Created: {title}")
        print(
            f"      URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")

        return spreadsheet.id

    except Exception as e:
        print(f"   ❌ Error creating {title}: {e}")
        raise


def main():
    if len(sys.argv) < 2:
        print("❌ Error: Credentials path not provided")
        print("Usage: python setup_google_sheets.py <credentials_path>")
        sys.exit(1)

    creds_path = sys.argv[1]

    if not Path(creds_path).exists():
        print(f"❌ Error: Credentials file not found: {creds_path}")
        sys.exit(1)

    print("🔐 Authenticating with Google...")

    try:
        # Setup credentials
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            creds_path, scope)
        gc = gspread.authorize(creds)

        print("✅ Authenticated successfully")
        print()

        # Get service account email for sharing info
        with open(creds_path) as f:
            creds_data = json.load(f)
            service_email = creds_data.get('client_email', 'Unknown')

        print(f"📧 Service Account: {service_email}")
        print()

        # Create sheets
        print("📊 Creating Google Sheets...")
        print()

        revenue_id = create_sheet_with_data(
            gc,
            "SaaS BI Agent - Revenue Data",
            REVENUE_DATA
        )

        product_id = create_sheet_with_data(
            gc,
            "SaaS BI Agent - Product Data",
            PRODUCT_DATA
        )

        support_id = create_sheet_with_data(
            gc,
            "SaaS BI Agent - Support Data",
            SUPPORT_DATA
        )

        print()
        print("✅ All sheets created successfully!")
        print()

        # Write sheet IDs to temporary file for setup.sh to read
        with open('../.sheet_ids.tmp', 'w') as f:
            f.write(f'REVENUE_SHEET_ID={revenue_id}\n')
            f.write(f'PRODUCT_SHEET_ID={product_id}\n')
            f.write(f'SUPPORT_SHEET_ID={support_id}\n')

        print("📝 Sheet IDs saved for configuration")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
