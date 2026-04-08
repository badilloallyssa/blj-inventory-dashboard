#!/usr/bin/env python3
"""
Quick comparison: Kids Journal print run destinations at 2024 vs 2025 pace.
"""
import json, calendar, os
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONTH_ABBR = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
US_WH = ['SLI','HBG','SAV','KCM']
SALES_WH_MAP = {
    'US':            ['SLI','HBG','SAV','KCM'],
    'Amazon_US_FBA': ['Amazon_US_FBA'],
    'CA':            ['CA'],
    'Amazon_CA_FBA': ['Amazon_CA_FBA'],
    'UK':            ['UK'],
    'EU':            ['EU'],
    'AU':            ['AU'],
}

GEO_WHS = {
    'SLI': ['SLI'], 'HBG': ['HBG'], 'SAV': ['SAV'], 'KCM': ['KCM'],
    'Amazon_US_FBA': ['Amazon_US_FBA'],
    'CA': ['CA'],
    'UK': ['UK'], 'EU': ['EU'], 'AU': ['AU'],
}
ALL_GEOS   = list(GEO_WHS.keys())
US_WH_GEOS = ['SLI','HBG','SAV','KCM']
APR_FACTOR = 27.0 / 30.0   # Apr 3 start

KIDS_JOURNAL_SKU = 'EIDJB5001'  # update if different

def load_data():
    with open(os.path.join(PROJECT_ROOT, '.tmp/data.json')) as f:
        return json.load(f)

def build_actuals(data, year):
    sales = data.get('sales', [])
    raw   = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for row in sales:
        if str(row.get('year', '')) != str(year): continue
        sid = row.get('sku_id', '').strip()
        wh  = row.get('warehouse', '').strip()
        d   = row.get('date', '')
        try:
            mo = int(d.split('-')[1]) if '-' in d else int(d.split('/')[0])
        except Exception:
            continue
        raw[sid][wh][mo] += float(row.get('units_sold', 0) or 0)

    out = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for sid, wh_data in raw.items():
        for sales_wh, month_data in wh_data.items():
            phys_whs = SALES_WH_MAP.get(sales_wh)
            if not phys_whs: continue
            n = len(phys_whs)
            for mo, units in month_data.items():
                for pwh in phys_whs:
                    out[sid][pwh][mo] += units / n
    return out

def get_starting_stock(data):
    stk = {e['sku_id']: {k: float(v) for k, v in e['stock'].items()}
           for e in data['current_stock']}
    for po in data.get('pos', []):
        sid, dst = po['sku_id'], po['destination']
        status = po.get('status', '').lower()
        if not any(s in status for s in ('ordered','in production','shipped','in transit','in-transit','pending')):
            continue
        stk.setdefault(sid, {})[dst] = stk.get(sid, {}).get(dst, 0) + float(po.get('qty_ordered', 0))
    return stk

def run_scenario(sid, actuals, stk_all, label):
    def actual_dem(wh, m):
        return actuals.get(sid, {}).get(wh, {}).get(m, 0.0)

    geo_stock  = {}
    geo_demand = {}
    geo_dem_sell = {}
    geo_dem_co   = {}

    for geo, whs in GEO_WHS.items():
        stock = sum(stk_all.get(sid, {}).get(w, 0) for w in whs)
        sell  = actual_dem(whs[0], 4) * APR_FACTOR
        for m in range(5, 13):
            sell += actual_dem(whs[0], m)
        co = actual_dem(whs[0], 1) + actual_dem(whs[0], 2)
        geo_stock[geo]    = stock
        geo_dem_sell[geo] = sell
        geo_dem_co[geo]   = co
        geo_demand[geo]   = sell + co

    geo_gap = {geo: geo_stock[geo] - geo_demand[geo] for geo in ALL_GEOS}

    transfer_log = []
    def do_transfer(src, dst):
        surplus = geo_gap.get(src, 0)
        deficit = -geo_gap.get(dst, 0)
        if surplus <= 0 or deficit <= 0: return
        usable = min(surplus, geo_stock[src] * 0.75)
        moved  = min(usable, deficit)
        if moved <= 0: return
        geo_gap[src] -= moved
        geo_gap[dst] += moved
        transfer_log.append((src, dst, int(moved)))

    for src in US_WH_GEOS:
        for dst in US_WH_GEOS:
            if src != dst: do_transfer(src, dst)
    for dst in ['Amazon_US_FBA', 'CA']:
        for src in sorted(US_WH_GEOS, key=lambda g: geo_gap.get(g, 0), reverse=True):
            do_transfer(src, dst)
    for route in [('UK','AU'),('EU','AU'),('UK','EU'),('EU','UK')]:
        do_transfer(*route)

    geo_print = {geo: int(round(max(0, -geo_gap[geo]))) for geo in ALL_GEOS}
    total_print = sum(geo_print.values())

    print(f"\n{'='*55}")
    print(f"  Kids Journal — {label}")
    print(f"{'='*55}")
    print(f"  {'Destination':<20} {'Stock':>8} {'Demand':>8} {'Print':>8}")
    print(f"  {'-'*44}")
    for geo in ALL_GEOS:
        s = int(geo_stock[geo])
        d = int(geo_demand[geo])
        p = geo_print[geo]
        flag = " ← PRINT" if p > 0 else ""
        print(f"  {geo:<20} {s:>8,} {d:>8,} {p:>8,}{flag}")
    print(f"  {'-'*44}")
    print(f"  {'TOTAL PRINT RUN':<20} {'':>8} {'':>8} {total_print:>8,}")

    if transfer_log:
        print(f"\n  Transfers applied:")
        for src, dst, qty in transfer_log:
            print(f"    {src} → {dst}: {qty:,}")

    return total_print, geo_print

def main():
    data    = load_data()
    stk_all = get_starting_stock(data)

    # Find Kids Journal SKU
    sku_names = {s['sku_id']: s['sku_name'] for s in data['config']['skus']}
    sid = None
    for s in data['config']['skus']:
        if 'kids' in s['sku_name'].lower() and 'journal' in s['sku_name'].lower():
            sid = s['sku_id']
            break
    if not sid:
        print("Could not find Kids Journal SKU. Available:")
        for s in data['config']['skus']:
            print(f"  {s['sku_id']}: {s['sku_name']}")
        return

    print(f"\nSKU: {sid} — {sku_names[sid]}")
    print("Demand = Apr 3 – Dec 31, 2026 + Jan/Feb 2027 carry-over")

    actuals_2025 = build_actuals(data, 2025)
    actuals_2024 = build_actuals(data, 2024)

    total_2025, geo_2025 = run_scenario(sid, actuals_2025, stk_all, "2025 Trend")
    total_2024, geo_2024 = run_scenario(sid, actuals_2024, stk_all, "2024 Trend")

    print(f"\n{'='*55}")
    print("  SUMMARY COMPARISON")
    print(f"{'='*55}")
    print(f"  {'Destination':<20} {'2025 trend':>12} {'2024 trend':>12} {'Diff':>10}")
    print(f"  {'-'*54}")
    for geo in ALL_GEOS:
        p25 = geo_2025[geo]
        p24 = geo_2024[geo]
        diff = p24 - p25
        if p25 > 0 or p24 > 0:
            sign = f"+{diff:,}" if diff > 0 else f"{diff:,}"
            print(f"  {geo:<20} {p25:>12,} {p24:>12,} {sign:>10}")
    print(f"  {'-'*54}")
    diff_total = total_2024 - total_2025
    sign_total = f"+{diff_total:,}" if diff_total > 0 else f"{diff_total:,}"
    print(f"  {'TOTAL':<20} {total_2025:>12,} {total_2024:>12,} {sign_total:>10}")

if __name__ == '__main__':
    main()
