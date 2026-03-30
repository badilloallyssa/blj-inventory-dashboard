"""
Create and initialize all required tabs in the Inventory & Demand Planner Google Sheet.
Safe to re-run — skips tabs that already exist, never overwrites existing data.

Usage:
    python tools/setup_sheet.py
    python tools/setup_sheet.py --reset-config   # overwrites Config tab with fresh defaults
"""
import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sheets_client import (
    get_sheets_service, get_sheet_id, get_existing_tabs,
    add_tab, write_tab, read_tab_raw, format_header_row
)

# ── Tab definitions: name → [header row] ────────────────────────────────────

TABS = {
    'Dashboard': None,  # special — formatted manually
    'Sales_Data': [
        ['Date', 'SKU_ID', 'SKU_Name', 'Warehouse', 'Units_Sold', 'Week_Number', 'Year', 'Notes']
    ],
    'Current_Stock': [
        ['Last_Updated', 'SKU_ID', 'SKU_Name',
         'SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK',
         'Amazon_US_FBA', 'Amazon_CA_FBA', 'Total']
    ],
    'Supplier_Stock': [
        ['Last_Updated', 'SKU_ID', 'SKU_Name', 'China_Supplier', 'Canada_Supplier', 'Notes']
    ],
    'PO_Tracker': [
        ['PO_ID', 'Type', 'SKU_ID', 'SKU_Name', 'Qty_Ordered', 'Origin', 'Destination',
         'Order_Date', 'Expected_Arrival', 'Days_Until_Arrival', 'Status', 'Notes']
    ],
    'Config': None,  # special — written with full structured data
    'Seasonality_Index': [
        ['SKU_ID', 'SKU_Name',
         'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
         'Last_Calculated', 'Override_Notes']
    ],
    'Demand_Plan': [
        ['Run_Date', 'Plan_Type', 'SKU_ID', 'SKU_Name', 'Warehouse',
         'Current_Stock', 'In_Transit', 'Total_Available',
         'Velocity_30d', 'Velocity_90d', 'Trend',
         'Plan_Month', 'Seasonality_Factor', 'Adjusted_Velocity',
         'Days_of_Stock', 'Lead_Time_Days', 'Target_Days',
         'Gap_Days', 'Units_Needed', 'Status', 'Urgency_Note']
    ],
    'Replenishment_Routing': [
        ['Run_Date', 'SKU_ID', 'SKU_Name', 'Destination',
         'Units_Needed', 'Recommended_Source', 'Source_Available',
         'Lead_Time_Days', 'Action_Type', 'Order_Deadline',
         'Estimated_Arrival', 'Priority', 'Notes']
    ],
    'Inventory_Health': [
        ['Run_Date', 'SKU_ID', 'SKU_Name', 'Warehouse',
         'Current_Stock', 'In_Transit', 'Total_Available',
         'Velocity_Daily', 'Days_of_Stock', 'Status', 'Alert']
    ],
    'Calculation_Log': [
        ['Run_Date', 'Plan_Type', 'SKU_ID', 'SKU_Name', 'Warehouse',
         'Current_Stock', 'In_Transit', 'Total_Available',
         'Velocity_30d', 'Velocity_90d', 'Trend_Signal',
         'Plan_Month', 'Seasonality_Factor', 'Seasonality_Source',
         'Adjusted_Velocity', 'Days_of_Stock',
         'Lead_Time_Days', 'Lead_Time_Source',
         'Target_Days', 'Gap_Days', 'Gap_Units',
         'Primary_Source', 'Primary_Source_Stock', 'Primary_Sufficient',
         'Secondary_Source', 'Secondary_Source_Stock', 'Secondary_Sufficient',
         'Final_Action', 'Final_Source', 'Final_Qty', 'Calculation_Notes']
    ],
}

TAB_ORDER = [
    'Dashboard', 'Sales_Data', 'Current_Stock', 'Supplier_Stock',
    'PO_Tracker', 'Config', 'Seasonality_Index',
    'Demand_Plan', 'Replenishment_Routing', 'Inventory_Health', 'Calculation_Log'
]

# ── Config tab content ───────────────────────────────────────────────────────

SKU_MASTER = [
    ['', 'SKU MASTER', '', ''],
    ['SKU_ID', 'SKU_Name', 'Short_Name', 'Active'],
    ['EIDJ4100', 'Kids Journal', 'Kids Journal', 'TRUE'],
    ['EIDJ2100', 'Teen Journal', 'Teen Journal', 'TRUE'],
    ['EIDC2000', 'Sharing Joy Conversation Cards', 'Sharing Joy Cards', 'TRUE'],
    ['EIDJ5100', 'Daily Journal (Teal)', 'Daily Journal Teal', 'TRUE'],
    ['EIDJ5200', 'Daily Journal (Green)', 'Daily Journal Green', 'TRUE'],
    ['EIDJ5000', 'Adult Journal', 'Adult Journal', 'TRUE'],
    ['EIDC2101', 'Dream Affirmation Cards', 'Dream Affirmation Cards', 'TRUE'],
    ['EIDJB5002', 'Know Me If You Can Cards', 'Know Me Cards', 'TRUE'],
]

WAREHOUSE_MASTER = [
    ['', '', '', '', ''],
    ['', 'WAREHOUSE MASTER', '', '', ''],
    ['Warehouse_ID', 'Name', 'Region', 'Type', 'Location'],
    ['SLI', 'Salt Lake City', 'US', '3PL', 'Salt Lake City, UT'],
    ['HBG', 'Harrisburg', 'US', '3PL', 'Harrisburg, PA'],
    ['SAV', 'Savannah', 'US', '3PL', 'Savannah, GA'],
    ['KCM', 'Kansas City', 'US', '3PL', 'Kansas City, MO'],
    ['EU', 'EU Warehouse', 'EU', '3PL', ''],
    ['CA', 'Canada Warehouse', 'CA', '3PL', ''],
    ['AU', 'Australia Warehouse', 'AU', '3PL', ''],
    ['UK', 'UK Warehouse', 'UK', '3PL', ''],
    ['Amazon_US_FBA', 'Amazon US FBA', 'US', 'FBA', 'US'],
    ['Amazon_CA_FBA', 'Amazon CA FBA', 'CA', 'FBA', 'CA'],
    ['China_Supplier', 'China Supplier', 'CN', 'Supplier', 'China'],
    ['Canada_Supplier', 'Canada Supplier', 'CA', 'Supplier', 'Canada'],
]

# Lead times in days (midpoint of stated ranges)
LEAD_TIMES = [
    ['', '', '', '', ''],
    ['', 'LEAD TIMES (days — midpoint of range)', '', '', ''],
    ['From → To', 'SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA'],
    ['China_Supplier', 45, 45, 45, 45, 75, 45, 45, 75, '', ''],
    ['Canada_Supplier', '', '', '', '', '', 14, '', '', '', 21],
    ['SLI (→ Amazon US FBA)', '', '', '', '', '', '', '', '', 21, ''],
    ['HBG (→ Amazon US FBA)', '', '', '', '', '', '', '', '', 21, ''],
    ['SAV (→ Amazon US FBA)', '', '', '', '', '', '', '', '', 21, ''],
    ['KCM (→ Amazon US FBA)', '', '', '', '', '', '', '', '', 21, ''],
    ['US_Warehouse (→ CA)', '', '', '', '', '', 21, '', '', '', ''],
    ['EU (→ UK)', '', '', '', '', '', '', '', 21, '', ''],
    ['EU (→ AU)', '', '', '', '', '', '', 60, '', '', ''],
    ['UK (→ EU)', '', '', '', '', 21, '', '', '', '', ''],
    ['UK (→ AU)', '', '', '', '', '', '', 60, '', '', ''],
    ['AU (→ UK)', '', '', '', '', '', '', '', 60, '', ''],
    ['CA (→ Amazon CA FBA)', '', '', '', '', '', '', '', '', '', 21],
]

PROXIMITY_MAP = [
    ['', '', '', '', '', ''],
    ['', 'REPLENISHMENT PROXIMITY MAP (ordered preference)', '', '', '', ''],
    ['Destination', 'Source_1', 'Source_2', 'Source_3', 'Notes'],
    ['Amazon_US_FBA', 'US_Warehouse (highest stock)', 'China_AWD (bulk direct)', '', 'AWD auto-replenishes FBA. Flag FBA fee differences per warehouse.'],
    ['Amazon_CA_FBA', 'CA', 'China', '', 'China can ship direct to AWD CA'],
    ['UK', 'EU', 'AU', 'China / US (expensive — needs freight forwarder)', ''],
    ['EU', 'UK', 'China', 'AU (if excess)', ''],
    ['AU', 'UK', 'China', '', ''],
    ['SLI', 'China_Supplier', '', '', ''],
    ['HBG', 'China_Supplier', '', '', ''],
    ['SAV', 'China_Supplier', '', '', ''],
    ['KCM', 'China_Supplier', '', '', ''],
    ['CA', 'US_Warehouse', 'Canada_Supplier', 'China', ''],
]

THRESHOLDS = [
    ['', '', '', ''],
    ['', 'PLANNING THRESHOLDS', '', ''],
    ['Parameter', 'Value', 'Notes'],
    ['Target_Days_of_Stock', 90, 'Minimum stock coverage target for all warehouses'],
    ['Overstock_Threshold_Days', 365, 'Flag if stock coverage exceeds this'],
    ['Critical_Threshold_Days', 30, 'Immediate action required below this'],
    ['AWD_Minimum_Qty', 200, 'Minimum units to justify sending to Amazon AWD (adjust as needed)'],
    ['Velocity_Window_Primary', 90, 'Days of sales history used for base velocity'],
    ['Velocity_Window_Trend', 30, 'Days of sales history used for trend detection'],
    ['Seasonality_Years', 2, 'Years of history used for seasonality calculation'],
]


def build_config_data():
    data = []
    data.extend(SKU_MASTER)
    data.extend(WAREHOUSE_MASTER)
    data.extend(LEAD_TIMES)
    data.extend(PROXIMITY_MAP)
    data.extend(THRESHOLDS)
    return data


def build_dashboard_placeholder():
    return [
        ['INVENTORY & DEMAND PLANNER', '', '', '', '', '', '', '', '', '', ''],
        ['Last Updated:', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', ''],
        ['Run python tools/run_demand_plan.py to generate the full plan.', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', ''],
        ['── URGENT ACTIONS ─────────────────────────────', '', '', '', '', '', '', '', '', '', ''],
        ['SKU', 'Warehouse', 'Current Stock', 'Days of Stock', 'Units Needed', 'Action', 'Source', 'Deadline', '', '', ''],
        ['(run plan to populate)', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', ''],
        ['── REPLENISHMENT NEEDED ────────────────────────', '', '', '', '', '', '', '', '', '', ''],
        ['SKU', 'Warehouse', 'Current Stock', 'Days of Stock', 'Units Needed', 'Action', 'Source', 'Order By', '', '', ''],
        ['(run plan to populate)', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', ''],
        ['── OVERSTOCK ALERTS ────────────────────────────', '', '', '', '', '', '', '', '', '', ''],
        ['SKU', 'Warehouse', 'Current Stock', 'Days of Stock', 'Recommended Action', '', '', '', '', '', ''],
        ['(run plan to populate)', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', ''],
        ['── ACTIVE POs & TRANSFERS ──────────────────────', '', '', '', '', '', '', '', '', '', ''],
        ['PO_ID', 'SKU', 'Qty', 'From', 'To', 'Order Date', 'ETA', 'Status', '', '', ''],
        ['(pulled from PO_Tracker tab)', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', ''],
        ['── OVERALL HEALTH MATRIX ───────────────────────', '', '', '', '', '', '', '', '', '', ''],
        ['SKU \\ Warehouse', 'SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA'],
        ['Kids Journal (EIDJ4100)', '', '', '', '', '', '', '', '', '', ''],
        ['Teen Journal (EIDJ2100)', '', '', '', '', '', '', '', '', '', ''],
        ['Sharing Joy Cards (EIDC2000)', '', '', '', '', '', '', '', '', '', ''],
        ['Daily Journal Teal (EIDJ5100)', '', '', '', '', '', '', '', '', '', ''],
        ['Daily Journal Green (EIDJ5200)', '', '', '', '', '', '', '', '', '', ''],
        ['Adult Journal (EIDJ5000)', '', '', '', '', '', '', '', '', '', ''],
        ['Dream Affirmation Cards (EIDC2101)', '', '', '', '', '', '', '', '', '', ''],
        ['Know Me Cards (EIDJB5002)', '', '', '', '', '', '', '', '', '', ''],
    ]


def main():
    parser = argparse.ArgumentParser(description='Set up Inventory Planner Google Sheet tabs')
    parser.add_argument('--reset-config', action='store_true',
                        help='Overwrite Config tab with fresh defaults')
    args = parser.parse_args()

    service = get_sheets_service()
    sheet_id = get_sheet_id()
    existing = get_existing_tabs(service, sheet_id)

    print(f"Sheet: {sheet_id}")
    print(f"Existing tabs: {existing}\n")

    for i, tab_name in enumerate(TAB_ORDER):
        if tab_name in existing:
            print(f"  SKIP  {tab_name} (already exists)")
            # Special case: Config reset
            if tab_name == 'Config' and args.reset_config:
                print(f"  RESET {tab_name} (--reset-config flag)")
                write_tab(service, sheet_id, tab_name, build_config_data())
                format_header_row(service, sheet_id, tab_name,
                                  bg_color={'red': 0.85, 'green': 0.92, 'blue': 0.83})
        else:
            add_tab(service, sheet_id, tab_name, index=i)
            print(f"  CREATE {tab_name}")

            if tab_name == 'Dashboard':
                write_tab(service, sheet_id, tab_name, build_dashboard_placeholder())
            elif tab_name == 'Config':
                write_tab(service, sheet_id, tab_name, build_config_data())
                format_header_row(service, sheet_id, tab_name,
                                  bg_color={'red': 0.85, 'green': 0.92, 'blue': 0.83})
            elif TABS.get(tab_name):
                write_tab(service, sheet_id, tab_name, TABS[tab_name])
                format_header_row(service, sheet_id, tab_name,
                                  bg_color={'red': 0.85, 'green': 0.92, 'blue': 0.83})

    print("\nDone. Open your Google Sheet to verify.")
    print("Next step: add your historical sales data to the Sales_Data tab,")
    print("then run: python tools/run_demand_plan.py")


if __name__ == '__main__':
    main()
