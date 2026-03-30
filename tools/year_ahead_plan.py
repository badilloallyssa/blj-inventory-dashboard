"""
Year-ahead supply chain plan.

Projects inventory depletion month by month through Dec 2026, identifies WHEN
each SKU × warehouse needs a transfer or new print run to START so stock is
ready in time. Sorted by action deadline — most urgent first.

Usage:
    python3 tools/year_ahead_plan.py --dry-run     # print only, no sheet write
    python3 tools/year_ahead_plan.py               # print + write Annual_Plan tab
    python3 tools/year_ahead_plan.py --horizon 12  # months ahead (default: 9)
"""
import sys
import os
import json
import argparse
import calendar
from datetime import datetime, date, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_client import get_sheets_service, get_sheet_id, write_tab, add_tab

MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

WAREHOUSES = ['SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA']
US_WAREHOUSES = ['SLI', 'HBG', 'SAV', 'KCM']
FBA_WAREHOUSES = ('Amazon_US_FBA', 'Amazon_CA_FBA')

# Lead times (days) from primary source to each destination
# Source → Destination
LEAD_TIME_TABLE = {
    ('US_Warehouse', 'SLI'):          7,
    ('US_Warehouse', 'HBG'):          7,
    ('US_Warehouse', 'SAV'):          7,
    ('US_Warehouse', 'KCM'):          7,
    ('US_Warehouse', 'Amazon_US_FBA'): 21,
    ('China_Supplier', 'SLI'):        45,
    ('China_Supplier', 'HBG'):        45,
    ('China_Supplier', 'SAV'):        45,
    ('China_Supplier', 'KCM'):        45,
    ('China_Supplier', 'EU'):         75,
    ('China_Supplier', 'AU'):         45,
    ('China_Supplier', 'UK'):         75,
    ('China_Supplier', 'CA'):         45,
    ('UK', 'EU'):                     21,
    ('UK', 'AU'):                     60,
    ('EU', 'UK'):                     21,
    ('EU', 'AU'):                     60,
    ('Canada_Supplier', 'CA'):        14,
    ('Canada_Supplier', 'Amazon_CA_FBA'): 21,
    ('CA', 'Amazon_CA_FBA'):          21,
}


def get_lead_time(source, destination):
    key = (source, destination)
    if key in LEAD_TIME_TABLE:
        return LEAD_TIME_TABLE[key]
    if source == 'China_Supplier':
        return 60  # safe fallback
    return 21


def get_primary_source_and_lead(destination, stock_index, sku_id):
    """
    Return (source, lead_time_days, action_type) for a destination.
    Prefers transfers over new POs wherever possible.
    action_type: 'Transfer' or 'New PO'
    """
    # Amazon FBA: replenish from US warehouse
    if destination == 'Amazon_US_FBA':
        best = max(US_WAREHOUSES, key=lambda w: stock_index.get(sku_id, {}).get(w, 0))
        if stock_index.get(sku_id, {}).get(best, 0) > 50:
            return (best, get_lead_time('US_Warehouse', destination), 'Transfer')
        return ('China_Supplier', get_lead_time('China_Supplier', 'SLI'), 'New PO')

    if destination == 'Amazon_CA_FBA':
        ca_stock = stock_index.get(sku_id, {}).get('CA', 0)
        if ca_stock > 50:
            return ('CA', get_lead_time('CA', 'Amazon_CA_FBA'), 'Transfer')
        return ('Canada_Supplier', get_lead_time('Canada_Supplier', 'Amazon_CA_FBA'), 'New PO')

    # US warehouses: try US-to-US transfer first
    if destination in US_WAREHOUSES:
        other_us = [w for w in US_WAREHOUSES if w != destination]
        best = max(other_us, key=lambda w: stock_index.get(sku_id, {}).get(w, 0))
        if stock_index.get(sku_id, {}).get(best, 0) > 100:
            return (best, get_lead_time('US_Warehouse', destination), 'Transfer')
        return ('China_Supplier', get_lead_time('China_Supplier', destination), 'New PO')

    if destination == 'AU':
        uk_stock = stock_index.get(sku_id, {}).get('UK', 0)
        if uk_stock > 200:
            return ('UK', get_lead_time('UK', 'AU'), 'Transfer')
        return ('China_Supplier', get_lead_time('China_Supplier', 'AU'), 'New PO')

    if destination == 'UK':
        eu_stock = stock_index.get(sku_id, {}).get('EU', 0)
        if eu_stock > 200:
            return ('EU', get_lead_time('EU', 'UK'), 'Transfer')
        return ('China_Supplier', get_lead_time('China_Supplier', 'UK'), 'New PO')

    if destination == 'EU':
        uk_stock = stock_index.get(sku_id, {}).get('UK', 0)
        if uk_stock > 200:
            return ('UK', get_lead_time('UK', 'EU'), 'Transfer')
        return ('China_Supplier', get_lead_time('China_Supplier', 'EU'), 'New PO')

    if destination == 'CA':
        return ('Canada_Supplier', get_lead_time('Canada_Supplier', 'CA'), 'New PO')

    return ('China_Supplier', 60, 'New PO')


def get_seasonality(seasonality_indices, sku_id, month_num):
    sku_idx = seasonality_indices.get(sku_id, {})
    return float(sku_idx.get(MONTH_ABBR[month_num - 1], 1.0))


def get_po_arrivals(pos, sku_id, destination, year, month):
    """Units arriving at destination for this SKU in year/month."""
    total = 0.0
    active = ('ordered', 'in production', 'shipped', 'in transit', 'in-transit',
              'pending', 'processing', 'confirmed')
    for po in pos:
        if po['sku_id'] != sku_id:
            continue
        if po['destination'].lower() != destination.lower():
            continue
        if not any(s in po.get('status', '').lower() for s in active):
            continue
        arrival_str = po.get('expected_arrival', '')
        if not arrival_str:
            continue
        for fmt in ('%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d'):
            try:
                arr = datetime.strptime(str(arrival_str).strip(), fmt)
                if arr.year == year and arr.month == month:
                    total += float(po.get('qty_ordered', 0))
                break
            except ValueError:
                continue
    return total


def simulate_and_flag(sku_id, sku_name, warehouse, start_stock, velocity_90d,
                      seasonality_indices, pos, stock_index, target_days,
                      horizon_months, today):
    """
    Simulate inventory month by month. Return ALL actions needed through the horizon.
    After each flagged event, assumes the fix is applied (stock restored to reorder_stock)
    and continues simulating — so Q4 build-up events are caught even when the warehouse
    is currently depleted.
    """
    if velocity_90d <= 0:
        return []

    source, lead_time, action_type = get_primary_source_and_lead(
        warehouse, stock_index, sku_id
    )

    reorder_stock = (target_days + lead_time) * velocity_90d  # stock level to trigger order

    stock = float(start_stock)
    year = today.year
    month = today.month
    actions = []

    for _ in range(horizon_months):
        num_days = calendar.monthrange(year, month)[1]
        sea = get_seasonality(seasonality_indices, sku_id, month)
        monthly_demand = velocity_90d * sea * num_days

        arrivals = get_po_arrivals(pos, sku_id, warehouse, year, month)
        stock = stock + arrivals - monthly_demand

        if stock < reorder_stock:
            target_month_start = date(year, month, 1)
            action_deadline = target_month_start - timedelta(days=lead_time)

            days_until = (action_deadline - today).days
            if days_until < 0:
                status = 'OVERDUE'
            elif days_until <= 30:
                status = 'URGENT'
            elif days_until <= 90:
                status = 'PLAN NOW'
            else:
                status = 'UPCOMING'

            units_needed = max(0, int(reorder_stock - stock + monthly_demand))
            month_label = f"{MONTH_ABBR[month-1]} {year}"

            actions.append({
                'sku_id': sku_id,
                'sku_name': sku_name,
                'warehouse': warehouse,
                'action_type': action_type,
                'source': source,
                'units_needed': units_needed,
                'action_deadline': action_deadline.strftime('%Y-%m-%d'),
                'stock_runs_low': month_label,
                'lead_time_days': lead_time,
                'status': status,
                'days_until_action': days_until,
                'velocity_daily': round(velocity_90d, 2),
                'note': (
                    f"Stock projects to {max(0,int(stock)):,} units by {month_label} "
                    f"(seasonality: {sea:.2f}x). "
                    f"Reorder point: {int(reorder_stock):,} units. "
                    f"{'Start transfer from ' + source if action_type == 'Transfer' else 'Place new PO with ' + source} "
                    f"by {action_deadline.strftime('%b %d, %Y')} (lead time: {lead_time}d)."
                )
            })

            # Assume the fix is applied: restore stock to reorder_stock and continue
            # This lets us find all subsequent events (e.g., Q4 build-up) in the same pass
            stock = reorder_stock

        # Advance month
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1

    return actions


def check_global_supply(sku_id, sku_name, global_stock, global_velocity,
                        seasonality_indices, pos, target_days,
                        horizon_months, today):
    """
    Check if total global inventory (all warehouses combined) is sufficient
    for total global demand through the horizon. Returns a New PO (Print Run)
    recommendation if global stock will run low, or None.
    """
    if global_velocity <= 0:
        return None

    CHINA_LEAD_DAYS = 60  # conservative China→US lead time for print run planning
    buffer = target_days * global_velocity  # units needed on hand at any time globally

    stock = float(global_stock)
    year = today.year
    month = today.month

    active_statuses = ('ordered', 'in production', 'shipped', 'in transit', 'in-transit',
                       'pending', 'processing', 'confirmed')

    for _ in range(horizon_months):
        num_days = calendar.monthrange(year, month)[1]
        sea = get_seasonality(seasonality_indices, sku_id, month)
        monthly_demand = global_velocity * sea * num_days

        # Add all active PO arrivals for this SKU (any destination) this month
        for po in pos:
            if po['sku_id'] != sku_id:
                continue
            if not any(s in po.get('status', '').lower() for s in active_statuses):
                continue
            arrival_str = po.get('expected_arrival', '')
            if not arrival_str:
                continue
            for fmt in ('%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d'):
                try:
                    arr = datetime.strptime(str(arrival_str).strip(), fmt)
                    if arr.year == year and arr.month == month:
                        stock += float(po.get('qty_ordered', 0))
                    break
                except ValueError:
                    continue

        stock -= monthly_demand

        if stock < buffer:
            target_month_start = date(year, month, 1)
            action_deadline = target_month_start - timedelta(days=CHINA_LEAD_DAYS)

            days_until = (action_deadline - today).days
            if days_until < 0:
                status = 'OVERDUE'
            elif days_until <= 30:
                status = 'URGENT'
            elif days_until <= 90:
                status = 'PLAN NOW'
            else:
                status = 'UPCOMING'

            units_needed = max(0, int(buffer - stock + monthly_demand))
            month_label = f"{MONTH_ABBR[month-1]} {year}"

            return {
                'sku_id': sku_id,
                'sku_name': sku_name,
                'warehouse': 'GLOBAL',
                'action_type': 'New PO (Print Run)',
                'source': 'China_Supplier',
                'units_needed': units_needed,
                'action_deadline': action_deadline.strftime('%Y-%m-%d'),
                'stock_runs_low': month_label,
                'lead_time_days': CHINA_LEAD_DAYS,
                'status': status,
                'days_until_action': days_until,
                'velocity_daily': round(global_velocity, 2),
                'note': (
                    f"Global stock projects to {max(0, int(stock)):,} units by {month_label} "
                    f"(seasonality index: {sea:.2f}x). "
                    f"Global reorder point: {int(buffer):,} units. "
                    f"Place new print run with China_Supplier "
                    f"by {action_deadline.strftime('%b %d, %Y')} (lead time: {CHINA_LEAD_DAYS}d)."
                )
            }

        if month == 12:
            month = 1
            year += 1
        else:
            month += 1

    return None  # global supply is fine through the horizon


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--horizon', type=int, default=12, help='Months ahead to simulate')
    parser.add_argument('--data', default='.tmp/data.json')
    parser.add_argument('--velocity', default='.tmp/velocity.json')
    parser.add_argument('--seasonality', default='.tmp/seasonality.json')
    args = parser.parse_args()

    for path in [args.data, args.velocity, args.seasonality]:
        full = os.path.join(PROJECT_ROOT, path)
        if not os.path.exists(full):
            print(f"ERROR: {path} not found. Run pull_data.py and velocity/seasonality scripts first.")
            sys.exit(1)

    with open(os.path.join(PROJECT_ROOT, args.data)) as f:
        data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, args.velocity)) as f:
        vel_data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, args.seasonality)) as f:
        sea_data = json.load(f)

    velocity = vel_data.get('velocity', {})
    seasonality_indices = sea_data.get('indices', {})
    config = data.get('config', {})
    thresholds = config.get('thresholds', {})
    target_days = int(thresholds.get('Target_Days_of_Stock', 90))
    pos = data.get('pos', [])

    # Build stock index
    stock_index = {}
    for entry in data.get('current_stock', []):
        stock_index[entry['sku_id']] = {k: float(v) for k, v in entry.get('stock', {}).items()}

    today = date.today()
    skus = [s for s in config.get('skus', []) if s.get('active', True)]

    print(f"\nYear-ahead plan — as of {today}  |  Horizon: {args.horizon} months\n")
    print("=" * 70)

    actions = []
    print_runs = []

    for sku in skus:
        sku_id = sku['sku_id']
        sku_name = sku['sku_name']
        sku_velocity = velocity.get(sku_id, {})

        # --- Per-warehouse distribution checks ---
        for wh in WAREHOUSES:
            v90 = sku_velocity.get(wh, {}).get('v90', 0.0)
            # Amazon_CA_FBA has no sales history before launch — proxy from CA velocity
            if wh == 'Amazon_CA_FBA' and v90 == 0.0:
                v90 = sku_velocity.get('CA', {}).get('v90', 0.0)
            current = stock_index.get(sku_id, {}).get(wh, 0.0)

            results = simulate_and_flag(
                sku_id, sku_name, wh, current, v90,
                seasonality_indices, pos, stock_index,
                target_days, args.horizon, today
            )
            actions.extend(results)

        # --- Global supply check: do we need a new print run? ---
        global_stock = sum(stock_index.get(sku_id, {}).values())
        global_vel = sum(
            sku_velocity.get(wh, {}).get('v90', 0.0)
            for wh in WAREHOUSES
        )
        pr = check_global_supply(
            sku_id, sku_name, global_stock, global_vel,
            seasonality_indices, pos, target_days,
            args.horizon, today
        )
        if pr:
            print_runs.append(pr)

    # Sort by status priority then action_deadline
    STATUS_ORDER = {'OVERDUE': 0, 'URGENT': 1, 'PLAN NOW': 2, 'UPCOMING': 3}
    actions.sort(key=lambda r: (STATUS_ORDER.get(r['status'], 9), r['action_deadline']))
    print_runs.sort(key=lambda r: (STATUS_ORDER.get(r['status'], 9), r['action_deadline']))

    # --- Print runs section ---
    icons = {'OVERDUE': '🔴', 'URGENT': '🟠', 'PLAN NOW': '🟡', 'UPCOMING': '🟢'}
    if print_runs:
        print("\n🖨️  NEW PRINT RUNS NEEDED (Global supply insufficient for demand horizon)")
        print("=" * 70)
        for a in print_runs:
            days_str = f"OVERDUE by {-a['days_until_action']}d" if a['days_until_action'] < 0 else f"in {a['days_until_action']}d"
            print(f"  {icons.get(a['status'], '')} {a['status']:<10} {a['sku_name']:<30}")
            print(f"    Qty: {a['units_needed']:>6,}  Deadline: {a['action_deadline']} ({days_str})")
            print(f"    Global stock runs low: {a['stock_runs_low']}  |  {a['note']}")
    else:
        print("\n✅  No new print runs needed — global supply sufficient through horizon.")

    # --- Per-warehouse distribution actions ---
    print(f"\n{'='*70}")
    print("DISTRIBUTION ACTIONS (transfers & warehouse restocks)")
    for status_label in ['OVERDUE', 'URGENT', 'PLAN NOW', 'UPCOMING']:
        group = [a for a in actions if a['status'] == status_label]
        if not group:
            continue
        print(f"\n{icons[status_label]} {status_label} ({len(group)})")
        print("-" * 70)
        for a in group:
            days_str = f"OVERDUE by {-a['days_until_action']}d" if a['days_until_action'] < 0 else f"in {a['days_until_action']}d"
            print(f"  {a['sku_name']:<30} → {a['warehouse']:<18} {a['action_type']:<10}")
            print(f"    Source: {a['source']:<20} Qty: {a['units_needed']:>5,}  "
                  f"Deadline: {a['action_deadline']} ({days_str})")
            print(f"    Runs low: {a['stock_runs_low']}")

    total_all = len(actions) + len(print_runs)
    print(f"\n{'='*70}")
    print(f"Total actions: {total_all}  |  Print Runs: {len(print_runs)}  |  "
          f"Distribution: {len(actions)}  "
          f"(Overdue: {sum(1 for a in actions if a['status']=='OVERDUE')}  "
          f"Urgent: {sum(1 for a in actions if a['status']=='URGENT')}  "
          f"Plan Now: {sum(1 for a in actions if a['status']=='PLAN NOW')}  "
          f"Upcoming: {sum(1 for a in actions if a['status']=='UPCOMING')})")

    if args.dry_run:
        print("\n[dry-run] No sheet changes written.")
        return

    # Write to Annual_Plan tab (print runs first, then distribution actions)
    run_date = today.strftime('%Y-%m-%d')
    headers = [
        'Status', 'Action_Deadline', 'Days_Until_Action',
        'SKU_ID', 'SKU_Name', 'Warehouse',
        'Action_Type', 'Source', 'Units_Needed',
        'Stock_Runs_Low', 'Lead_Time_Days', 'Velocity_Daily', 'Notes', 'Run_Date'
    ]

    def to_row(a):
        return [
            a['status'], a['action_deadline'], a['days_until_action'],
            a['sku_id'], a['sku_name'], a['warehouse'],
            a['action_type'], a['source'], a['units_needed'],
            a['stock_runs_low'], a['lead_time_days'], a['velocity_daily'],
            a['note'], run_date
        ]

    rows = [headers] + [to_row(a) for a in print_runs] + [to_row(a) for a in actions]

    service = get_sheets_service()
    sheet_id = get_sheet_id()
    add_tab(service, sheet_id, 'Annual_Plan')
    write_tab(service, sheet_id, 'Annual_Plan', rows)
    print(f"\nWrote {len(rows)-1} rows to Annual_Plan tab ({len(print_runs)} print runs + {len(actions)} distribution).")


if __name__ == '__main__':
    main()
