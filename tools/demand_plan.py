"""
Core demand planning engine.

For each SKU × Warehouse, calculates:
  - Total available stock (on-hand + in transit)
  - Adjusted daily velocity (90d base × seasonality factor)
  - Days of stock remaining
  - Units needed to reach 90-day target
  - Urgency (days until action needed, given lead time)
  - Full calculation trail (for Calculation_Log)

Usage:
    python tools/demand_plan.py --data .tmp/data.json --velocity .tmp/velocity.json --seasonality .tmp/seasonality.json
    python tools/demand_plan.py ... --plan-type monthly --plan-month 2025-04
    python tools/demand_plan.py ... --plan-type quarterly --plan-quarter 2025-Q2
"""
import sys
import os
import json
import argparse
from datetime import datetime, date
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

WAREHOUSES = ['SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA']


def get_lead_time(config, source, destination):
    """Look up lead time in days from config. Returns midpoint value or 45 as fallback."""
    lt = config.get('lead_times', {})
    # Try direct source → dest lookup
    for src_key, dests in lt.items():
        if src_key.startswith('_'):
            continue
        if source.lower() in src_key.lower():
            if isinstance(dests, dict):
                for dest_key, days in dests.items():
                    if destination.lower() in dest_key.lower() and days:
                        return int(days)
    return 45  # safe fallback


def get_in_transit(pos, sku_id, destination):
    """Sum up units in-transit for a given SKU headed to a destination warehouse."""
    total = 0.0
    active_statuses = ('ordered', 'in production', 'shipped', 'in transit', 'in-transit',
                       'pending', 'processing', 'confirmed')
    for po in pos:
        if po['sku_id'] != sku_id:
            continue
        if po['destination'].lower() != destination.lower():
            continue
        status = po.get('status', '').lower()
        if any(s in status for s in active_statuses):
            total += float(po.get('qty_ordered', 0))
    return total


def get_seasonality_factor(seasonality_data, sku_id, target_month_num):
    """Get seasonality index for a SKU and month number (1-12). Returns 1.0 if unknown."""
    month_name = MONTH_NAMES[target_month_num - 1]
    for entry in seasonality_data:
        if entry['sku_id'] == sku_id:
            idx = entry['indices'].get(month_name)
            if idx is not None:
                return float(idx)
    return 1.0  # neutral if no data


def get_primary_lead_time(config, destination):
    """Get the lead time from the primary source for a given destination."""
    prox = config.get('proximity_map', {})
    entry = prox.get(destination, {})
    source_1 = entry.get('source_1', '')

    # Map proximity source labels to lead time keys
    source_map = {
        'china_supplier': 'China_Supplier',
        'china': 'China_Supplier',
        'us_warehouse': 'SLI',  # representative US warehouse
        'eu': 'EU',
        'uk': 'UK',
        'au': 'AU',
        'ca': 'CA',
    }
    for key, lt_key in source_map.items():
        if key in source_1.lower():
            return get_lead_time(config, lt_key, destination)
    return 45


def run_demand_plan(data, velocity_data, seasonality_data_raw, plan_type='monthly',
                    plan_month=None, plan_quarter=None):
    """
    Main planning function. Returns (plan_rows, calc_log_rows).

    plan_rows: list of dicts, one per SKU × Warehouse
    calc_log_rows: list of dicts with full calculation trail
    """
    config = data.get('config', {})
    current_stock_list = data.get('current_stock', [])
    pos = data.get('pos', [])
    seasonality_list = data.get('seasonality', seasonality_data_raw)

    thresholds = config.get('thresholds', {})
    target_days = int(thresholds.get('Target_Days_of_Stock', 90))
    overstock_days = int(thresholds.get('Overstock_Threshold_Days', 365))
    critical_days = int(thresholds.get('Critical_Threshold_Days', 30))

    velocity = velocity_data.get('velocity', {})

    # Determine which months to plan for
    now = datetime.now()
    if plan_type == 'monthly':
        if plan_month:
            dt = datetime.strptime(plan_month, '%Y-%m')
        else:
            # Default: next month
            if now.month == 12:
                dt = datetime(now.year + 1, 1, 1)
            else:
                dt = datetime(now.year, now.month + 1, 1)
        plan_months = [dt.month]
        plan_label = dt.strftime('%B %Y')
    else:
        # Quarterly: next 3 months
        start_month = now.month + 1 if now.month < 12 else 1
        start_year = now.year if now.month < 12 else now.year + 1
        plan_months = [(start_month + i - 1) % 12 + 1 for i in range(3)]
        plan_label = f"Q{(start_month - 1) // 3 + 1} {start_year}"

    # Avg seasonality factor across plan months
    def avg_seasonality(sku_id):
        factors = [get_seasonality_factor(seasonality_list, sku_id, m) for m in plan_months]
        return round(sum(factors) / len(factors), 3)

    # Index current stock by sku_id
    stock_index = {}
    for entry in current_stock_list:
        stock_index[entry['sku_id']] = entry['stock']

    skus = [s for s in config.get('skus', []) if s.get('active', True)]

    plan_rows = []
    calc_log_rows = []
    run_date = now.strftime('%Y-%m-%d %H:%M')

    for sku in skus:
        sku_id = sku['sku_id']
        sku_name = sku['sku_name']
        short_name = sku.get('short_name', sku_name)

        sku_velocity = velocity.get(sku_id, {})
        sea_factor = avg_seasonality(sku_id)

        for wh in WAREHOUSES:
            current = stock_index.get(sku_id, {}).get(wh, 0.0)
            in_transit = get_in_transit(pos, sku_id, wh)
            total_available = current + in_transit

            v30 = sku_velocity.get(wh, {}).get('v30', 0.0)
            v90 = sku_velocity.get(wh, {}).get('v90', 0.0)
            trend = sku_velocity.get(wh, {}).get('trend', 1.0)
            trend_signal = sku_velocity.get(wh, {}).get('trend_signal', 'STABLE')
            data_quality = sku_velocity.get(wh, {}).get('data_quality', 'INSUFFICIENT')

            # Use 90d velocity as base (more stable), adjusted by seasonality
            adjusted_velocity = round(v90 * sea_factor, 4)

            # Days of stock
            if adjusted_velocity > 0:
                days_of_stock = round(total_available / adjusted_velocity, 1)
            else:
                days_of_stock = 9999  # no velocity = infinite stock (no data or zero sales)

            # Lead time for this warehouse (from primary source)
            lead_time = get_primary_lead_time(config, wh)

            # Gap analysis
            gap_days = round(target_days - days_of_stock, 1)
            units_needed = round(max(0, gap_days) * adjusted_velocity, 0) if adjusted_velocity > 0 else 0

            # Status
            # Amazon FBA uses a tighter overstock threshold — storage fees apply above target
            fba_warehouses = ('Amazon_US_FBA', 'Amazon_CA_FBA')
            effective_overstock_days = target_days if wh in fba_warehouses else overstock_days

            if days_of_stock == 9999:
                status = 'NO_DATA'
            elif days_of_stock < critical_days:
                status = 'CRITICAL'
            elif days_of_stock < target_days:
                status = 'LOW'
            elif days_of_stock > effective_overstock_days:
                status = 'OVERSTOCK'
            else:
                status = 'OK'

            # Urgency: how many days until we drop below lead time buffer?
            if adjusted_velocity > 0 and days_of_stock < 9999:
                days_until_action = round(days_of_stock - lead_time, 1)
                if days_until_action < 0:
                    urgency_note = f"ORDER NOW — stock runs out in {days_of_stock}d, lead time is {lead_time}d"
                elif days_until_action < 14:
                    urgency_note = f"Order within {int(days_until_action)} days"
                elif status == 'OVERSTOCK':
                    urgency_note = f"No action — {days_of_stock:.0f}d of stock (overstock threshold: {overstock_days}d)"
                elif status == 'OK':
                    urgency_note = f"OK — next review in {int(days_until_action - 14)} days"
                else:
                    urgency_note = f"Plan replenishment — {days_of_stock:.0f}d of stock remaining"
            else:
                urgency_note = 'No sales data — verify stock'

            plan_row = {
                'run_date': run_date,
                'plan_type': plan_type.capitalize(),
                'sku_id': sku_id,
                'sku_name': sku_name,
                'warehouse': wh,
                'current_stock': int(current),
                'in_transit': int(in_transit),
                'total_available': int(total_available),
                'velocity_30d': v30,
                'velocity_90d': v90,
                'trend': trend,
                'trend_signal': trend_signal,
                'plan_month': plan_label,
                'seasonality_factor': sea_factor,
                'adjusted_velocity': adjusted_velocity,
                'days_of_stock': days_of_stock,
                'lead_time_days': lead_time,
                'target_days': target_days,
                'gap_days': gap_days,
                'units_needed': int(units_needed),
                'status': status,
                'urgency_note': urgency_note,
                'data_quality': data_quality,
            }
            plan_rows.append(plan_row)

            # Calculation log (full transparency)
            calc_note = (
                f"Current stock: {int(current)} | In transit: {int(in_transit)} | "
                f"Total: {int(total_available)} | "
                f"90d velocity: {v90:.3f}/day | "
                f"Seasonality ({plan_label}): {sea_factor}x | "
                f"Adjusted velocity: {v90:.3f} × {sea_factor} = {adjusted_velocity:.3f}/day | "
                f"Days of stock: {int(total_available)} ÷ {adjusted_velocity:.3f} = {days_of_stock}d | "
                f"Target: {target_days}d | Gap: {gap_days}d | "
                f"Units needed: {int(units_needed)} | "
                f"Lead time from primary source: {lead_time}d | "
                f"Data quality: {data_quality}"
            )
            calc_log_rows.append({**plan_row, 'calculation_notes': calc_note})

    return plan_rows, calc_log_rows


def main():
    parser = argparse.ArgumentParser(description='Run demand planning calculations')
    parser.add_argument('--data', default='.tmp/data.json')
    parser.add_argument('--velocity', default='.tmp/velocity.json')
    parser.add_argument('--seasonality', default='.tmp/seasonality.json')
    parser.add_argument('--output', default='.tmp/demand_plan.json')
    parser.add_argument('--plan-type', choices=['monthly', 'quarterly'], default='monthly')
    parser.add_argument('--plan-month', help='YYYY-MM (monthly plan). Default: next month.')
    parser.add_argument('--plan-quarter', help='YYYY-QN (quarterly plan). Default: next quarter.')
    args = parser.parse_args()

    for path, label in [(args.data, 'data.json'), (args.velocity, 'velocity.json'),
                        (args.seasonality, 'seasonality.json')]:
        full = os.path.join(PROJECT_ROOT, path)
        if not os.path.exists(full):
            print(f"ERROR: {path} not found. Run the prerequisite tools first.")
            sys.exit(1)

    with open(os.path.join(PROJECT_ROOT, args.data)) as f:
        data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, args.velocity)) as f:
        velocity_data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, args.seasonality)) as f:
        seasonality_raw = json.load(f)
        # Merge calculated seasonality into data format
        for sku_id, indices in seasonality_raw.get('indices', {}).items():
            found = False
            for entry in data.get('seasonality', []):
                if entry['sku_id'] == sku_id:
                    entry['indices'] = indices
                    found = True
            if not found:
                data.setdefault('seasonality', []).append({'sku_id': sku_id, 'indices': indices})

    print(f"Running {args.plan_type} demand plan...")
    plan_rows, calc_log_rows = run_demand_plan(
        data, velocity_data, data.get('seasonality', []),
        plan_type=args.plan_type,
        plan_month=args.plan_month,
        plan_quarter=args.plan_quarter
    )

    # Print summary
    statuses = defaultdict(int)
    for r in plan_rows:
        statuses[r['status']] += 1
    print(f"\nResults: {len(plan_rows)} SKU×Warehouse combinations")
    for status, count in sorted(statuses.items()):
        print(f"  {status:<12} {count}")

    urgent = [r for r in plan_rows if r['status'] in ('CRITICAL', 'LOW') and r['units_needed'] > 0]
    if urgent:
        print(f"\nAction needed ({len(urgent)} items):")
        for r in sorted(urgent, key=lambda x: x['days_of_stock'])[:10]:
            print(f"  {r['sku_name']:<35} {r['warehouse']:<20} "
                  f"{r['days_of_stock']:>6.1f}d stock  need {r['units_needed']:>5} units")

    output = {
        'generated_at': datetime.now().isoformat(),
        'plan_type': args.plan_type,
        'plan_rows': plan_rows,
        'calc_log_rows': calc_log_rows,
    }

    output_path = os.path.join(PROJECT_ROOT, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nSaved to {args.output}")
    return output


if __name__ == '__main__':
    main()
