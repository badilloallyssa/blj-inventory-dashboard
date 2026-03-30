"""
Derive monthly seasonality indices from 2 years of sales history.

How it works (plain language):
  - For each SKU, calculate average monthly sales across all history
  - Then calculate the average for each specific month (Jan, Feb, ... Dec)
  - Index = that month's average / overall average
  - Example: December average = 150 units/week, overall average = 100 → index = 1.50
  - Index > 1.0 means above-average demand that month (stock up)
  - Index < 1.0 means below-average demand (less stock needed)

This is written back to the Seasonality_Index tab in the sheet.

Usage:
    python tools/calculate_seasonality.py --data .tmp/data.json
    python tools/calculate_seasonality.py --data .tmp/data.json --output .tmp/seasonality.json
    python tools/calculate_seasonality.py --data .tmp/data.json --write-to-sheet
"""
import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def parse_date(date_str):
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            continue
    return None


def calculate_seasonality(data):
    """
    Calculate monthly seasonality index per SKU (aggregated across all warehouses).

    Returns: {sku_id: {month_name: index, ...}}
    With full explanation dict for transparency.
    """
    sales = data.get('sales', [])

    # Aggregate sales by sku + year + month (summed across all warehouses)
    # {sku_id: {(year, month): total_units}}
    monthly_sales = defaultdict(lambda: defaultdict(float))

    for row in sales:
        d = parse_date(row.get('date', ''))
        if d is None:
            continue
        sku = row.get('sku_id', '').strip()
        units = float(row.get('units_sold', 0) or 0)
        if sku:
            monthly_sales[sku][(d.year, d.month)] += units

    result = {}
    explanation = {}  # for calculation log / transparency

    for sku, months_data in monthly_sales.items():
        if not months_data:
            continue

        # Step 1: Average units per month (across all data)
        all_monthly_totals = list(months_data.values())
        overall_avg = sum(all_monthly_totals) / len(all_monthly_totals)

        # Step 2: Average per calendar month (Jan=1 ... Dec=12)
        month_totals = defaultdict(list)
        for (year, month), total in months_data.items():
            month_totals[month].append(total)

        month_avgs = {}
        for m in range(1, 13):
            vals = month_totals.get(m, [])
            month_avgs[m] = sum(vals) / len(vals) if vals else overall_avg

        # Step 3: Index = month_avg / overall_avg
        indices = {}
        expl = {
            'overall_avg_per_month': round(overall_avg, 1),
            'data_points_used': len(all_monthly_totals),
            'months': {}
        }
        for m in range(1, 13):
            month_name = MONTH_NAMES[m - 1]
            avg = month_avgs[m]
            index = round(avg / overall_avg, 3) if overall_avg > 0 else 1.0
            indices[month_name] = index
            expl['months'][month_name] = {
                'avg_units': round(avg, 1),
                'observations': len(month_totals.get(m, [])),
                'index': index,
                'meaning': f"{'+' if index >= 1 else ''}{round((index - 1) * 100, 1)}% vs average month"
            }

        result[sku] = indices
        explanation[sku] = expl

    return result, explanation


def main():
    parser = argparse.ArgumentParser(description='Calculate monthly seasonality indices')
    parser.add_argument('--data', default='.tmp/data.json')
    parser.add_argument('--output', default='.tmp/seasonality.json')
    parser.add_argument('--write-to-sheet', action='store_true',
                        help='Write results directly to Seasonality_Index tab in Google Sheet')
    args = parser.parse_args()

    data_path = os.path.join(PROJECT_ROOT, args.data)
    if not os.path.exists(data_path):
        print(f"ERROR: {args.data} not found. Run pull_data.py first.")
        sys.exit(1)

    with open(data_path) as f:
        data = json.load(f)

    print(f"Calculating seasonality from {len(data.get('sales', []))} sales rows...")

    indices, explanation = calculate_seasonality(data)

    sku_names = {s['sku_id']: s['sku_name'] for s in data.get('config', {}).get('skus', [])}

    print(f"\n{'SKU':<35} {'Jan':>5} {'Feb':>5} {'Mar':>5} {'Apr':>5} {'May':>5} {'Jun':>5} "
          f"{'Jul':>5} {'Aug':>5} {'Sep':>5} {'Oct':>5} {'Nov':>5} {'Dec':>5}")
    print('-' * 95)
    for sku, month_indices in sorted(indices.items()):
        name = sku_names.get(sku, sku)[:34]
        row = f"{name:<35}"
        for m in MONTH_NAMES:
            idx = month_indices.get(m, 1.0)
            row += f" {idx:>5.2f}"
        print(row)

    print(f"\n(>1.0 = above average demand that month, <1.0 = below average)")

    output = {
        'calculated_at': datetime.now().isoformat(),
        'indices': indices,
        'explanation': explanation
    }

    output_path = os.path.join(PROJECT_ROOT, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved to {args.output}")

    if args.write_to_sheet:
        sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))
        from sheets_client import get_sheets_service, get_sheet_id, write_tab

        service = get_sheets_service()
        sheet_id = get_sheet_id()
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        rows = [['SKU_ID', 'SKU_Name'] + MONTH_NAMES + ['Last_Calculated', 'Override_Notes']]
        for sku, month_indices in sorted(indices.items()):
            name = sku_names.get(sku, sku)
            row = [sku, name] + [month_indices.get(m, '') for m in MONTH_NAMES] + [now, '']
            rows.append(row)

        write_tab(service, sheet_id, 'Seasonality_Index', rows)
        print(f"Written to Seasonality_Index tab in Google Sheet.")

    return output


if __name__ == '__main__':
    main()
