
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_date(date_str):
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            continue
    return None

def main():
    with open(os.path.join(PROJECT_ROOT, '.tmp/data.json')) as f: data = json.load(f)
    sales = data.get('sales', [])
    
    # {sku_id: {year: {month: total_units}}}
    global_annual_monthly = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for row in sales:
        d = parse_date(row.get('date', ''))
        if d is None: continue
        sku, units = row.get('sku_id', '').strip(), float(row.get('units_sold', 0) or 0)
        if sku:
            global_annual_monthly[sku][d.year][d.month] += units

    # Target Months: May-Jan (9 months of depletion)
    forecast_months = [5, 6, 7, 8, 9, 10, 11, 12, 1]
    # Buffer Months: Feb-Apr (to have 90 days left over in Jan)
    buffer_months = [2, 3, 4]

    config = data.get('config', {})
    skus = [s for s in config.get('skus', []) if s.get('active', True)]
    stock_index = {entry['sku_id']: sum(float(v) for v in entry.get('stock', {}).values()) for entry in data.get('current_stock', [])}
    # Supplier stock also counts as "on hand" (not needing a print)
    supplier_stock = {entry['sku_id']: float(entry.get('china_supplier', 0)) + float(entry.get('canada_supplier', 0)) for entry in data.get('supplier_stock', [])}
    
    print("\n" + "="*130)
    print("STRESS-TEST INVENTORY ORDERING PLAN (STOCKED THROUGH JAN 2027 + 90 DAY BUFFER)")
    print("Formula: [Max Historical Demand May-Jan] + [90-Day Post-Jan Buffer] - [Current Stock + Supplier Stock]")
    print("="*130)
    header = f"{'SKU Name':<30} | {'Current+Sup Stock':>18} | {'Forecast Demand':>18} | {'90D Buffer':>12} | {'TOTAL NEEDED':>15}"
    print(header)
    print("-" * 130)

    for sku in skus:
        sku_id, sku_name = sku['sku_id'], sku['sku_name']
        
        # 1. Aggressive Forecast (Max of 2024/2025 per month)
        total_demand = 0
        for m in forecast_months:
            active_totals = [global_annual_monthly[sku_id][yr][m] for yr in global_annual_monthly[sku_id] if global_annual_monthly[sku_id][yr][m] > 0]
            total_demand += max(active_totals) if active_totals else 0
            
        # 2. Buffer (Avg of Feb-Apr)
        total_buffer = 0
        for m in buffer_months:
            active_totals = [global_annual_monthly[sku_id][yr][m] for yr in global_annual_monthly[sku_id] if global_annual_monthly[sku_id][yr][m] > 0]
            total_buffer += (sum(active_totals) / len(active_totals)) if active_totals else 0
            
        current_total = stock_index.get(sku_id, 0) + supplier_stock.get(sku_id, 0)
        
        needed = (total_demand + total_buffer) - current_total
        order_qty = max(0, int(needed))
        
        print(f"{sku_name:<30} | {int(current_total):>18,} | {int(total_demand):>18,} | {int(total_buffer):>12,} | {order_qty:>15,}")

    print("-" * 130)

if __name__ == '__main__':
    main()
