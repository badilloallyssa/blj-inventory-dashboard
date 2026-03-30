"""
Calculate sales velocity per SKU per warehouse.

Velocity = average daily units sold over a rolling window (30d, 60d, 90d).
Also calculates a trend signal: 30d velocity vs 90d velocity.

Usage:
    python tools/calculate_velocity.py --data .tmp/data.json
    python tools/calculate_velocity.py --data .tmp/data.json --output .tmp/velocity.json
"""
import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_date(date_str):
    """Try common date formats."""
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            continue
    return None


def calculate_velocity(data, as_of_date=None):
    """
    Calculate velocity for each SKU × Warehouse combination.

    Returns dict: {sku_id: {warehouse: {v30: float, v60: float, v90: float, trend: float, ...}}}
    """
    if as_of_date is None:
        as_of_date = datetime.today().date()
    elif isinstance(as_of_date, str):
        as_of_date = parse_date(as_of_date)

    sales = data.get('sales', [])

    # Build sales index: {sku_id: {warehouse: [(date, units)]}}
    sales_by_sku_wh = defaultdict(lambda: defaultdict(list))
    skipped = 0
    for row in sales:
        d = parse_date(row.get('date', ''))
        if d is None:
            skipped += 1
            continue
        sku = row.get('sku_id', '').strip()
        wh = row.get('warehouse', '').strip()
        units = float(row.get('units_sold', 0) or 0)
        if sku and wh:
            sales_by_sku_wh[sku][wh].append((d, units))

    windows = {'v30': 30, 'v60': 60, 'v90': 90}
    result = {}

    for sku, warehouses in sales_by_sku_wh.items():
        result[sku] = {}
        for wh, entries in warehouses.items():
            wh_result = {}
            for key, days in windows.items():
                cutoff = as_of_date - timedelta(days=days)
                window_entries = [(d, u) for d, u in entries if d > cutoff]
                total_units = sum(u for _, u in window_entries)
                # Velocity = total sold / window days (not just days with sales)
                wh_result[key] = round(total_units / days, 4)

            # Trend: ratio of 30d vs 90d velocity (>1.2 = accelerating, <0.8 = slowing)
            if wh_result['v90'] > 0:
                wh_result['trend'] = round(wh_result['v30'] / wh_result['v90'], 3)
            else:
                wh_result['trend'] = 1.0

            trend_val = wh_result['trend']
            if trend_val > 1.2:
                wh_result['trend_signal'] = 'ACCELERATING'
            elif trend_val < 0.8:
                wh_result['trend_signal'] = 'SLOWING'
            else:
                wh_result['trend_signal'] = 'STABLE'

            # Data quality: how many days of actual sales data do we have?
            if entries:
                earliest = min(d for d, _ in entries)
                days_of_data = (as_of_date - earliest).days
            else:
                days_of_data = 0
            wh_result['days_of_data'] = days_of_data
            wh_result['data_quality'] = 'GOOD' if days_of_data >= 90 else ('PARTIAL' if days_of_data >= 30 else 'INSUFFICIENT')

            result[sku][wh] = wh_result

    if skipped > 0:
        print(f"  Warning: skipped {skipped} sales rows with unparseable dates")

    # Expand US aggregate velocity to individual US warehouses
    # If Sales_Data uses 'US' instead of individual warehouse codes,
    # apply that velocity to SLI, HBG, SAV, KCM (unless warehouse-specific data exists)
    US_WAREHOUSES = ['SLI', 'HBG', 'SAV', 'KCM']
    for sku in result:
        if 'US' in result[sku]:
            us_velocity = result[sku]['US']
            for us_wh in US_WAREHOUSES:
                if us_wh not in result[sku]:
                    result[sku][us_wh] = us_velocity

    return result


def main():
    parser = argparse.ArgumentParser(description='Calculate sales velocity per SKU per warehouse')
    parser.add_argument('--data', default='.tmp/data.json', help='Input data.json from pull_data.py')
    parser.add_argument('--output', default='.tmp/velocity.json', help='Output file path')
    parser.add_argument('--as-of', default=None, help='Calculate as of this date (YYYY-MM-DD). Default: today.')
    args = parser.parse_args()

    data_path = os.path.join(PROJECT_ROOT, args.data)
    if not os.path.exists(data_path):
        print(f"ERROR: {args.data} not found. Run pull_data.py first.")
        sys.exit(1)

    with open(data_path) as f:
        data = json.load(f)

    print(f"Calculating velocity from {len(data.get('sales', []))} sales rows...")
    as_of = args.as_of or datetime.today().strftime('%Y-%m-%d')
    print(f"As of: {as_of}\n")

    velocity = calculate_velocity(data, as_of_date=as_of)

    # Print summary
    sku_names = {s['sku_id']: s['sku_name'] for s in data.get('config', {}).get('skus', [])}
    for sku, warehouses in sorted(velocity.items()):
        name = sku_names.get(sku, sku)
        print(f"  {name} ({sku})")
        for wh, v in sorted(warehouses.items()):
            print(f"    {wh:<20} 30d: {v['v30']:.2f}/day  90d: {v['v90']:.2f}/day  "
                  f"Trend: {v['trend_signal']}  Data: {v['data_quality']} ({v['days_of_data']}d)")

    output = {
        'calculated_at': datetime.now().isoformat(),
        'as_of_date': as_of,
        'velocity': velocity
    }

    output_path = os.path.join(PROJECT_ROOT, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nSaved to {args.output}")
    return output


if __name__ == '__main__':
    main()
