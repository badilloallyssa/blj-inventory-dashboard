"""
Inventory health check — quick snapshot of current state per SKU per warehouse.

Status codes:
  CRITICAL  — < 30 days of stock (action required now)
  LOW       — 30–90 days of stock (replenishment needed)
  OK        — 90–365 days of stock (healthy)
  OVERSTOCK — > 365 days of stock (consider sale or transfer)
  NO_DATA   — no velocity data (zero sales or missing history)

Usage:
    python tools/inventory_health.py --plan .tmp/demand_plan.json --data .tmp/data.json
    python tools/inventory_health.py ... --output .tmp/health.json
"""
import sys
import os
import json
import argparse
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUS_ORDER = {'CRITICAL': 0, 'LOW': 1, 'OK': 2, 'OVERSTOCK': 3, 'NO_DATA': 4}


def calculate_health(data, plan_data):
    """Derive health rows from the demand plan (avoids recalculating everything)."""
    plan_rows = plan_data.get('plan_rows', [])
    run_date = datetime.now().strftime('%Y-%m-%d %H:%M')

    health_rows = []
    for r in plan_rows:
        days = r['days_of_stock']
        status = r['status']

        alert = ''
        fba_warehouses = ('Amazon_US_FBA', 'Amazon_CA_FBA')
        if status == 'CRITICAL':
            alert = f"CRITICAL: Only {days:.0f}d of stock — order deadline approaching"
        elif status == 'LOW':
            alert = f"LOW: {days:.0f}d of stock — replenishment needed (target: {r['target_days']}d)"
        elif status == 'OVERSTOCK' and r['warehouse'] in fba_warehouses:
            velocity = r['velocity_90d']
            excess_units = int((days - r['target_days']) * velocity) if velocity > 0 and days < 9999 else 0
            alert = (f"FBA OVERSTOCK: {days:.0f}d of stock — send ~{excess_units:,} units to AWD "
                     f"to avoid storage fee penalties")
        elif status == 'OVERSTOCK':
            alert = f"OVERSTOCK: {days:.0f}d of stock — consider transfer to another region"
        elif status == 'NO_DATA':
            alert = "NO SALES DATA — verify stock and check Sales_Data tab"

        health_rows.append({
            'run_date': run_date,
            'sku_id': r['sku_id'],
            'sku_name': r['sku_name'],
            'warehouse': r['warehouse'],
            'current_stock': r['current_stock'],
            'in_transit': r['in_transit'],
            'total_available': r['total_available'],
            'velocity_daily': r['velocity_90d'],
            'days_of_stock': days,
            'status': status,
            'alert': alert,
        })

    return health_rows


def print_health_matrix(health_rows, sku_names):
    """Print a compact ASCII health matrix."""
    STATUS_ICONS = {
        'CRITICAL': '🔴 CRIT',
        'LOW': '🟡 LOW ',
        'OK': '🟢 OK  ',
        'OVERSTOCK': '🟠 OVER',
        'NO_DATA': '⚪ N/A ',
    }
    warehouses = ['SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA']

    # Index health by sku×warehouse
    health_index = {}
    for r in health_rows:
        health_index[(r['sku_id'], r['warehouse'])] = r

    print(f"\n{'SKU':<35}", end='')
    for wh in warehouses:
        short = wh[:6]
        print(f" {short:>8}", end='')
    print()
    print('-' * (35 + 9 * len(warehouses)))

    for sku_id, sku_name in sorted(sku_names.items()):
        name = sku_name[:34]
        print(f"{name:<35}", end='')
        for wh in warehouses:
            row = health_index.get((sku_id, wh))
            if row:
                status = row['status']
                days = row['days_of_stock']
                if days == 9999:
                    cell = '   N/A  '
                else:
                    cell = f"{days:>6.0f}d"
                print(f" {cell:>8}", end='')
            else:
                print(f" {'---':>8}", end='')
        print()

    print(f"\nLegend: <30d = CRITICAL | 30-90d = LOW | 90-365d = OK | >365d = OVERSTOCK")


def main():
    parser = argparse.ArgumentParser(description='Inventory health check')
    parser.add_argument('--plan', default='.tmp/demand_plan.json')
    parser.add_argument('--data', default='.tmp/data.json')
    parser.add_argument('--output', default='.tmp/health.json')
    args = parser.parse_args()

    for path in [args.plan, args.data]:
        full = os.path.join(PROJECT_ROOT, path)
        if not os.path.exists(full):
            print(f"ERROR: {path} not found.")
            sys.exit(1)

    with open(os.path.join(PROJECT_ROOT, args.plan)) as f:
        plan_data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, args.data)) as f:
        data = json.load(f)

    print("Calculating inventory health...")
    health_rows = calculate_health(data, plan_data)

    sku_names = {s['sku_id']: s['sku_name'] for s in data.get('config', {}).get('skus', [])}
    print_health_matrix(health_rows, sku_names)

    # Summary by status
    status_counts = defaultdict(int)
    for r in health_rows:
        status_counts[r['status']] += 1
    print(f"\nSummary:")
    for status in ['CRITICAL', 'LOW', 'OK', 'OVERSTOCK', 'NO_DATA']:
        count = status_counts.get(status, 0)
        if count > 0:
            print(f"  {status:<12} {count} SKU×Warehouse combinations")

    output = {
        'generated_at': datetime.now().isoformat(),
        'health_rows': health_rows,
        'summary': dict(status_counts),
    }

    output_path = os.path.join(PROJECT_ROOT, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nSaved to {args.output}")
    return output


if __name__ == '__main__':
    main()
