"""
Write demand plan results back to the Google Sheet.

Updates tabs: Dashboard, Demand_Plan, Replenishment_Routing, Inventory_Health, Calculation_Log.

Usage:
    python tools/write_plan.py --plan .tmp/demand_plan.json --routing .tmp/routing.json --health .tmp/health.json --data .tmp/data.json
"""
import sys
import os
import json
import argparse
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))

from sheets_client import (
    get_sheets_service, get_sheet_id, write_tab,
    add_note, format_header_row
)


# ── Tab writers ───────────────────────────────────────────────────────────────

def write_demand_plan_tab(service, sheet_id, plan_rows):
    headers = [
        'Run_Date', 'Plan_Type', 'SKU_ID', 'SKU_Name', 'Warehouse',
        'Current_Stock', 'In_Transit', 'Total_Available',
        'Velocity_30d', 'Velocity_90d', 'Trend',
        'Plan_Month', 'Seasonality_Factor', 'Adjusted_Velocity',
        'Days_of_Stock', 'Lead_Time_Days', 'Target_Days',
        'Gap_Days', 'Units_Needed', 'Status', 'Urgency_Note'
    ]
    rows = [headers]
    for r in plan_rows:
        rows.append([
            r['run_date'], r['plan_type'], r['sku_id'], r['sku_name'], r['warehouse'],
            r['current_stock'], r['in_transit'], r['total_available'],
            r['velocity_30d'], r['velocity_90d'], r['trend'],
            r['plan_month'], r['seasonality_factor'], r['adjusted_velocity'],
            r['days_of_stock'], r['lead_time_days'], r['target_days'],
            r['gap_days'], r['units_needed'], r['status'], r['urgency_note']
        ])
    write_tab(service, sheet_id, 'Demand_Plan', rows)
    format_header_row(service, sheet_id, 'Demand_Plan',
                      bg_color={'red': 0.85, 'green': 0.92, 'blue': 0.83})
    print(f"  Wrote {len(rows)-1} rows to Demand_Plan")


def write_routing_tab(service, sheet_id, routing_rows):
    headers = [
        'Run_Date', 'SKU_ID', 'SKU_Name', 'Destination',
        'Units_Needed', 'Recommended_Source', 'Source_Available',
        'Lead_Time_Days', 'Action_Type', 'Order_Deadline',
        'Estimated_Arrival', 'Priority', 'Days_of_Stock', 'Notes'
    ]
    rows = [headers]
    for r in routing_rows:
        rows.append([
            r['run_date'], r['sku_id'], r['sku_name'], r['destination'],
            r['units_needed'], r['recommended_source'], r['source_available'],
            r['lead_time_days'], r['action_type'], r['order_deadline'],
            r['estimated_arrival'], r['priority'], r['days_of_stock'], r['notes']
        ])
    write_tab(service, sheet_id, 'Replenishment_Routing', rows)
    format_header_row(service, sheet_id, 'Replenishment_Routing',
                      bg_color={'red': 0.85, 'green': 0.92, 'blue': 0.83})
    print(f"  Wrote {len(rows)-1} rows to Replenishment_Routing")


def write_health_tab(service, sheet_id, health_rows):
    headers = [
        'Run_Date', 'SKU_ID', 'SKU_Name', 'Warehouse',
        'Current_Stock', 'In_Transit', 'Total_Available',
        'Velocity_Daily', 'Days_of_Stock', 'Status', 'Alert'
    ]
    rows = [headers]
    for r in health_rows:
        rows.append([
            r['run_date'], r['sku_id'], r['sku_name'], r['warehouse'],
            r['current_stock'], r['in_transit'], r['total_available'],
            r['velocity_daily'], r['days_of_stock'], r['status'], r['alert']
        ])
    write_tab(service, sheet_id, 'Inventory_Health', rows)
    format_header_row(service, sheet_id, 'Inventory_Health',
                      bg_color={'red': 0.85, 'green': 0.92, 'blue': 0.83})
    print(f"  Wrote {len(rows)-1} rows to Inventory_Health")


def write_calc_log_tab(service, sheet_id, calc_log_rows):
    headers = [
        'Run_Date', 'Plan_Type', 'SKU_ID', 'SKU_Name', 'Warehouse',
        'Current_Stock', 'In_Transit', 'Total_Available',
        'Velocity_30d', 'Velocity_90d', 'Trend_Signal',
        'Plan_Month', 'Seasonality_Factor',
        'Adjusted_Velocity', 'Days_of_Stock',
        'Lead_Time_Days', 'Target_Days', 'Gap_Days', 'Units_Needed',
        'Status', 'Calculation_Notes'
    ]
    rows = [headers]
    for r in calc_log_rows:
        rows.append([
            r['run_date'], r['plan_type'], r['sku_id'], r['sku_name'], r['warehouse'],
            r['current_stock'], r['in_transit'], r['total_available'],
            r['velocity_30d'], r['velocity_90d'], r.get('trend_signal', ''),
            r['plan_month'], r['seasonality_factor'],
            r['adjusted_velocity'], r['days_of_stock'],
            r['lead_time_days'], r['target_days'], r['gap_days'], r['units_needed'],
            r['status'], r.get('calculation_notes', '')
        ])
    write_tab(service, sheet_id, 'Calculation_Log', rows)
    format_header_row(service, sheet_id, 'Calculation_Log',
                      bg_color={'red': 0.85, 'green': 0.92, 'blue': 0.83})
    print(f"  Wrote {len(rows)-1} rows to Calculation_Log")


def write_dashboard(service, sheet_id, plan_rows, routing_rows, health_rows, data, plan_data):
    """Build and write the Dashboard tab."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    config = data.get('config', {})
    pos = data.get('pos', [])
    plan_type = plan_data.get('plan_type', 'monthly').capitalize()

    # Separate by status
    critical = [r for r in plan_rows if r['status'] == 'CRITICAL' and r['units_needed'] > 0]
    low = [r for r in plan_rows if r['status'] == 'LOW' and r['units_needed'] > 0]
    overstock = [r for r in plan_rows if r['status'] == 'OVERSTOCK']

    # Get routing for urgent items
    routing_index = {(r['sku_id'], r['destination']): r for r in routing_rows}

    rows = []

    # Header
    rows.append(['INVENTORY & DEMAND PLANNER', '', '', '', '', '', '', '', '', '', ''])
    rows.append([f'Last Updated: {now}  |  Plan Type: {plan_type}', '', '', '', '', '', '', '', '', '', ''])
    rows.append(['', '', '', '', '', '', '', '', '', '', ''])

    # Urgent Actions
    rows.append(['── URGENT ACTIONS (CRITICAL — Order Now) ──────────────────────────────────', '', '', '', '', '', '', '', '', '', ''])
    rows.append(['SKU', 'Warehouse', 'Current Stock', 'Days of Stock', 'Units Needed',
                 'Action', 'Source', 'Order Deadline', 'ETA', 'Note', ''])
    if critical:
        for r in sorted(critical, key=lambda x: x['days_of_stock']):
            rt = routing_index.get((r['sku_id'], r['warehouse']), {})
            rows.append([
                f"{r['sku_name']} ({r['sku_id']})", r['warehouse'],
                r['current_stock'], f"{r['days_of_stock']:.0f}d", r['units_needed'],
                rt.get('action_type', ''), rt.get('recommended_source', ''),
                rt.get('order_deadline', ''), rt.get('estimated_arrival', ''),
                r['urgency_note'], ''
            ])
    else:
        rows.append(['No critical items', '', '', '', '', '', '', '', '', '', ''])

    rows.append(['', '', '', '', '', '', '', '', '', '', ''])

    # Replenishment Needed
    rows.append(['── REPLENISHMENT NEEDED (LOW — Plan Now) ──────────────────────────────────', '', '', '', '', '', '', '', '', '', ''])
    rows.append(['SKU', 'Warehouse', 'Current Stock', 'Days of Stock', 'Units Needed',
                 'Action', 'Source', 'Order By', 'ETA', 'Note', ''])
    if low:
        for r in sorted(low, key=lambda x: x['days_of_stock']):
            rt = routing_index.get((r['sku_id'], r['warehouse']), {})
            rows.append([
                f"{r['sku_name']} ({r['sku_id']})", r['warehouse'],
                r['current_stock'], f"{r['days_of_stock']:.0f}d", r['units_needed'],
                rt.get('action_type', ''), rt.get('recommended_source', ''),
                rt.get('order_deadline', ''), rt.get('estimated_arrival', ''),
                r['urgency_note'], ''
            ])
    else:
        rows.append(['No low-stock items', '', '', '', '', '', '', '', '', '', ''])

    rows.append(['', '', '', '', '', '', '', '', '', '', ''])

    # Overstock Alerts
    rows.append(['── OVERSTOCK ALERTS (>365 days) ────────────────────────────────────────────', '', '', '', '', '', '', '', '', '', ''])
    rows.append(['SKU', 'Warehouse', 'Current Stock', 'Days of Stock', 'Recommended Action', '', '', '', '', '', ''])
    if overstock:
        for r in sorted(overstock, key=lambda x: -x['days_of_stock']):
            action = 'Run promotion / transfer excess to lower-stock warehouse'
            rows.append([
                f"{r['sku_name']} ({r['sku_id']})", r['warehouse'],
                r['current_stock'], f"{r['days_of_stock']:.0f}d", action,
                '', '', '', '', '', ''
            ])
    else:
        rows.append(['No overstock alerts', '', '', '', '', '', '', '', '', '', ''])

    rows.append(['', '', '', '', '', '', '', '', '', '', ''])

    # Active POs & Transfers
    rows.append(['── ACTIVE POs & TRANSFERS ──────────────────────────────────────────────────', '', '', '', '', '', '', '', '', '', ''])
    rows.append(['PO_ID', 'Type', 'SKU', 'Qty', 'From', 'To', 'Order Date', 'ETA', 'Status', 'Notes', ''])
    if pos:
        for po in pos:
            sku_name = next((s['sku_name'] for s in config.get('skus', [])
                             if s['sku_id'] == po['sku_id']), po['sku_id'])
            rows.append([
                po['po_id'], po['type'],
                f"{sku_name} ({po['sku_id']})",
                int(po['qty_ordered']), po['origin'], po['destination'],
                po['order_date'], po['expected_arrival'], po['status'], po['notes'], ''
            ])
    else:
        rows.append(['No active POs or transfers', '', '', '', '', '', '', '', '', '', ''])

    rows.append(['', '', '', '', '', '', '', '', '', '', ''])

    # Health Matrix
    wh_order = ['SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA']
    rows.append(['── OVERALL HEALTH MATRIX (days of stock) ───────────────────────────────────', '', '', '', '', '', '', '', '', '', ''])
    rows.append(['SKU \\ Warehouse'] + wh_order)

    # Index health
    health_index = {(r['sku_id'], r['warehouse']): r for r in health_rows}
    skus = [s for s in config.get('skus', []) if s.get('active', True)]

    for sku in skus:
        row = [f"{sku['sku_name']} ({sku['sku_id']})"]
        for wh in wh_order:
            h = health_index.get((sku['sku_id'], wh))
            if h:
                d = h['days_of_stock']
                if d == 9999:
                    cell = 'N/A'
                else:
                    cell = f"{d:.0f}d [{h['status']}]"
            else:
                cell = '---'
            row.append(cell)
        rows.append(row)

    write_tab(service, sheet_id, 'Dashboard', rows)
    print(f"  Wrote Dashboard ({len(critical)} critical, {len(low)} low, {len(overstock)} overstock, {len(pos)} active POs)")


def main():
    parser = argparse.ArgumentParser(description='Write demand plan results to Google Sheet')
    parser.add_argument('--plan', default='.tmp/demand_plan.json')
    parser.add_argument('--routing', default='.tmp/routing.json')
    parser.add_argument('--health', default='.tmp/health.json')
    parser.add_argument('--data', default='.tmp/data.json')
    args = parser.parse_args()

    for path in [args.plan, args.routing, args.health, args.data]:
        if not os.path.exists(os.path.join(PROJECT_ROOT, path)):
            print(f"ERROR: {path} not found.")
            sys.exit(1)

    with open(os.path.join(PROJECT_ROOT, args.plan)) as f:
        plan_data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, args.routing)) as f:
        routing_data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, args.health)) as f:
        health_data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, args.data)) as f:
        data = json.load(f)

    service = get_sheets_service()
    sheet_id = get_sheet_id()

    print("Writing to Google Sheet...")
    write_demand_plan_tab(service, sheet_id, plan_data['plan_rows'])
    write_routing_tab(service, sheet_id, routing_data['routing_rows'])
    write_health_tab(service, sheet_id, health_data['health_rows'])
    write_calc_log_tab(service, sheet_id, plan_data['calc_log_rows'])
    write_dashboard(service, sheet_id,
                    plan_data['plan_rows'],
                    routing_data['routing_rows'],
                    health_data['health_rows'],
                    data, plan_data)

    print("\nDone. Open the Google Sheet to view results.")
    print(f"  → Dashboard tab has the action summary for the owner")
    print(f"  → Calculation_Log tab has the full math behind every number")


if __name__ == '__main__':
    main()
