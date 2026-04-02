#!/usr/bin/env python3
"""
Build transfer + print plan using 2025 actual monthly sales as demand forecast.

Why 2025 actuals instead of v90 x seasonality:
  The v90 is calculated over Jan-Mar 2026 (slowest months), which runs 60-87%
  below 2025 actual sales. Using v90 x seasonality dramatically understates
  real demand — especially for BFCM (Nov/Dec). We instead use each month's
  2025 actual sales as the demand proxy for the same month in 2026.

Key rules:
  - No UK→US transfers
  - CA replenished from US warehouses (no new Canada prints)
  - Source warehouses never stripped below 25% buffer
  - China/Canada supplier stock used when warehouse transfers insufficient

Outputs:
  .tmp/transfer_plan.json   — dashboard data
  Google Sheet: Transfer_Print_Plan tab

Usage:
    python3 tools/build_transfer_plan.py
"""

import json, calendar
from datetime import date
from collections import defaultdict
import os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

MONTH_ABBR = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
WAREHOUSES = ['SLI','HBG','SAV','KCM','EU','CA','AU','UK','Amazon_US_FBA','Amazon_CA_FBA']
US_WH      = ['SLI','HBG','SAV','KCM']

# Sales data uses these warehouse labels; map to physical stock locations
SALES_WH_MAP = {
    'US':            ['SLI','HBG','SAV','KCM'],  # US pool split evenly across 4 warehouses
    'Amazon_US_FBA': ['Amazon_US_FBA'],
    'CA':            ['CA'],
    'Amazon_CA_FBA': ['Amazon_CA_FBA'],
    'UK':            ['UK'],
    'EU':            ['EU'],
    'AU':            ['AU'],
}

WH_REGION = {
    'SLI':'US','HBG':'US','SAV':'US','KCM':'US',
    'Amazon_US_FBA':'US FBA',
    'CA':'CA','Amazon_CA_FBA':'CA FBA',
    'EU':'EU','UK':'UK','AU':'AU',
}


def load_data():
    with open(os.path.join(PROJECT_ROOT, '.tmp/data.json')) as f:
        data = json.load(f)
    return data


def build_2025_monthly_demand(data):
    """
    Build actual 2025 monthly sales per SKU per physical warehouse.
    Sales data uses: US, Amazon_US_FBA, CA, UK, EU, AU
    US sales are split evenly across SLI/HBG/SAV/KCM (4 warehouses).
    Amazon_CA_FBA has no separate sales data; treat as 0 (CA warehouse covers CA demand).
    """
    sales = data.get('sales', [])
    # raw: sku -> sales_wh -> month -> units
    raw = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    for row in sales:
        if str(row.get('year', '')) != '2025':
            continue
        sid  = row.get('sku_id', '').strip()
        wh   = row.get('warehouse', '').strip()
        d    = row.get('date', '')
        try:
            mo = int(d.split('-')[1]) if '-' in d else int(d.split('/')[0])
        except Exception:
            continue
        raw[sid][wh][mo] += float(row.get('units_sold', 0) or 0)

    # Expand to physical warehouse demand
    # monthly_demand[sid][wh][month] = units
    monthly_demand = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    for sid, wh_data in raw.items():
        for sales_wh, month_data in wh_data.items():
            phys_whs = SALES_WH_MAP.get(sales_wh)
            if not phys_whs:
                continue
            n = len(phys_whs)
            for mo, units in month_data.items():
                for pwh in phys_whs:
                    monthly_demand[sid][pwh][mo] += units / n

    return monthly_demand


def run_simulation():
    data           = load_data()
    monthly_demand = build_2025_monthly_demand(data)

    sku_names = {s['sku_id']: s['sku_name'] for s in data['config']['skus']}
    sku_list  = [s['sku_id'] for s in data['config']['skus']]
    pos       = data.get('pos', [])
    TODAY     = date.today()

    supplier_stock = {
        e['sku_id']: {
            'china':  float(e.get('china_supplier', 0)),
            'canada': float(e.get('canada_supplier', 0)),
        }
        for e in data.get('supplier_stock', [])
    }

    # Initialize stock from current snapshot + in-transit POs
    stk = {e['sku_id']: {k: float(v) for k, v in e['stock'].items()}
           for e in data['current_stock']}
    for po in pos:
        sid, dst = po['sku_id'], po['destination']
        status = po.get('status', '').lower()
        if not any(s in status for s in
                   ('ordered','in production','shipped','in transit','in-transit','pending')):
            continue
        stk.setdefault(sid, {})[dst] = stk.get(sid, {}).get(dst, 0) + float(po.get('qty_ordered', 0))

    def demand_for(sid, wh, m):
        """2025 actual units sold in month m, at physical warehouse wh."""
        return monthly_demand.get(sid, {}).get(wh, {}).get(m, 0.0)

    def safety_for(sid, wh, m):
        """
        Safety stock = sum of demand for the next 2 months after m.
        This gives us a forward-looking buffer so we order before we run out.
        """
        total = 0.0
        for offset in range(1, 3):
            nm = (m - 1 + offset) % 12 + 1
            total += demand_for(sid, wh, nm)
        return total

    def get_sources(wh, sid):
        us_sorted = sorted(US_WH, key=lambda w: stk.get(sid, {}).get(w, 0), reverse=True)
        if wh == 'Amazon_US_FBA':
            return [(w, 7, False) for w in us_sorted] + [('China_AWD', 60, True)]
        if wh == 'Amazon_CA_FBA':
            return [('CA', 14, False), ('China_Supplier', 60, True)]
        if wh in US_WH:
            others = sorted([w for w in US_WH if w != wh],
                            key=lambda w: stk.get(sid, {}).get(w, 0), reverse=True)
            return [(w, 3, False) for w in others] + [('China_Supplier', 45, True)]
        if wh == 'CA':
            # Transfer from US warehouses; no new Canada prints
            return [(w, 14, False) for w in us_sorted] + [('China_Supplier', 60, True)]
        if wh == 'EU':
            return [('UK', 21, False), ('China_Supplier', 75, True)]
        if wh == 'UK':
            return [('EU', 21, False), ('China_Supplier', 75, True)]
        if wh == 'AU':
            return [('UK', 60, False), ('EU', 60, False), ('China_Supplier', 60, True)]
        return [('China_Supplier', 60, True)]

    QUARTER_OF   = {4:'Q2',5:'Q2',6:'Q2', 7:'Q3',8:'Q3',9:'Q3', 10:'Q4',11:'Q4',12:'Q4'}
    po_new        = defaultdict(float)
    transfers_raw = defaultdict(list)
    action_log    = []
    monthly_forecast = {}  # for dashboard

    y, m = TODAY.year, TODAY.month

    for _ in range(12):
        if y > 2026 or (y == 2026 and m > 12):
            break
        q           = QUARTER_OF.get(m, 'other')
        month_label = f'{MONTH_ABBR[m - 1]} {y}'

        # --- Build forecast snapshot (2025 actuals for this month) ---

        mfc = {}
        for sid in sku_list:
            mfc[sid] = defaultdict(float)
            for wh in WAREHOUSES:
                d = demand_for(sid, wh, m)
                region = WH_REGION.get(wh, wh)
                mfc[sid][region] += d
        monthly_forecast[month_label] = {
            sid: {r: round(v) for r, v in regions.items()}
            for sid, regions in mfc.items()
        }

        # --- Deduct this month's demand ---
        for sid in stk:
            for wh in WAREHOUSES:
                stk[sid][wh] = stk[sid].get(wh, 0) - demand_for(sid, wh, m)

        # --- Check & replenish ---
        for sid in stk:
            for wh in WAREHOUSES:
                this_demand = demand_for(sid, wh, m)
                if this_demand == 0:
                    continue  # no sales at this warehouse, skip

                safety    = safety_for(sid, wh, m)
                current   = stk[sid].get(wh, 0)

                if current >= safety:
                    continue

                shortfall = safety - current
                days_stock = max(0, current) / (this_demand / calendar.monthrange(y, m)[1]) \
                             if this_demand > 0 else 9999

                for (src, lead, is_po) in get_sources(wh, sid):
                    if shortfall <= 0:
                        break
                    if is_po:
                        po_new[(sid, src)] += shortfall
                        stk[sid][wh] = stk[sid].get(wh, 0) + shortfall
                        reason = (
                            f"After {month_label} sales, {sku_names.get(sid,sid)} at {wh} "
                            f"has only ~{int(days_stock)}d of stock remaining. "
                            f"No warehouse stock available to transfer — ordering {int(shortfall):,} units from {src}."
                        )
                        if q in ('Q2','Q3','Q4'):
                            action_log.append({'month':month_label,'quarter':q,
                                'sku':sku_names.get(sid,sid),'wh':wh,'src':src,
                                'qty':int(shortfall),'type':'NEW PO','reason':reason})
                            transfers_raw[q].append({'sku':sku_names.get(sid,sid),'sku_id':sid,
                                'wh':wh,'src':src,'qty':int(shortfall),
                                'month':month_label,'type':'NEW PO'})
                        shortfall = 0
                    else:
                        src_stock = stk[sid].get(src, 0)
                        buffer    = 0.25 * max(src_stock, 0)
                        usable    = max(0, src_stock - buffer)
                        if usable <= 0:
                            continue
                        moved = min(shortfall, usable)
                        stk[sid][src] = src_stock - moved
                        stk[sid][wh]  = stk[sid].get(wh, 0) + moved

                        next_mo_demand = demand_for(sid, src, (m % 12) + 1)
                        src_days = int(max(0, src_stock) / (next_mo_demand / 30)) \
                                   if next_mo_demand > 0 else 9999
                        reason = (
                            f"After {month_label} sales, {sku_names.get(sid,sid)} at {wh} "
                            f"drops to ~{int(days_stock)}d of stock "
                            f"(next 2 months need {int(safety):,} units as buffer). "
                            f"Transfer {int(moved):,} units from {src} "
                            f"({src} has {int(src_stock):,} units / ~{src_days}d to spare)."
                        )
                        if q in ('Q2','Q3','Q4'):
                            action_log.append({'month':month_label,'quarter':q,
                                'sku':sku_names.get(sid,sid),'wh':wh,'src':src,
                                'qty':int(moved),'type':'Transfer','reason':reason})
                            transfers_raw[q].append({'sku':sku_names.get(sid,sid),'sku_id':sid,
                                'wh':wh,'src':src,'qty':int(moved),
                                'month':month_label,'type':'Transfer'})
                        shortfall -= moved

        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1

    # --- End-of-year snapshot ---
    print("\n=== END-OF-YEAR STOCK SNAPSHOT (after all 2025-pace sales + transfers) ===")
    for sid in sku_list:
        if sid not in stk:
            continue
        name = sku_names.get(sid, sid)
        print(f"\n{name}:")
        for wh in WAREHOUSES:
            remaining = stk[sid].get(wh, 0)
            monthly_d = demand_for(sid, wh, 11)  # use Nov as proxy for burn rate
            dos = remaining / (monthly_d / 30) if monthly_d > 0 else 9999
            flag = ' ⚠️  STOCKOUT' if remaining < 0 else (' ⚠️  LOW (<30d)' if dos < 30 and monthly_d > 0 else '')
            print(f"  {wh:20s}: {int(remaining):7,} units  (~{int(dos)}d){flag}")

    # --- Roll up print runs ---
    print_runs     = []
    supplier_orders = []
    run_date        = date.today().strftime('%Y-%m-%d')

    for (sid, src), qty in po_new.items():
        qty  = int(round(qty))
        name = sku_names.get(sid, sid)
        sup  = supplier_stock.get(sid, {})

        if 'China' in src or 'AWD' in src:
            china_avail = int(sup.get('china', 0))
            if china_avail >= qty:
                supplier_orders.append({
                    'sku_id':sid,'sku_name':name,'source':src,
                    'units_needed':qty,'supplier_stock':china_avail,
                    'covered':True,'order_by':'2026-08-02',
                    'type':'Supplier Order','run_date':run_date,
                    'notes':f'China has {china_avail:,} in stock — covered, place order now.',
                })
            else:
                gap = qty - china_avail
                if china_avail > 0:
                    supplier_orders.append({
                        'sku_id':sid,'sku_name':name,'source':src,
                        'units_needed':china_avail,'supplier_stock':china_avail,
                        'covered':True,'order_by':'2026-08-02',
                        'type':'Supplier Order','run_date':run_date,
                        'notes':f'China has {china_avail:,} — order all available stock now.',
                    })
                print_runs.append({
                    'sku_id':sid,'sku_name':name,'source':'China_Supplier',
                    'units_needed':gap,'supplier_stock':china_avail,
                    'order_by':'2026-08-02','type':'Print Run','run_date':run_date,
                    'notes':(
                        f'China has {china_avail:,} available but {qty:,} needed total — '
                        f'short {gap:,} units. New production run required. '
                        f'Order by Aug 2 → arrives mid-Sep → in FBA/warehouses by Oct 1 for BFCM.'
                    ),
                })
        elif 'Canada' in src:
            canada_avail = int(sup.get('canada', 0))
            if canada_avail >= qty:
                supplier_orders.append({
                    'sku_id':sid,'sku_name':name,'source':src,
                    'units_needed':qty,'supplier_stock':canada_avail,
                    'covered':True,'order_by':'2026-09-01',
                    'type':'Supplier Order','run_date':run_date,
                    'notes':f'Canada has {canada_avail:,} — covered.',
                })
            else:
                gap = qty - canada_avail
                print_runs.append({
                    'sku_id':sid,'sku_name':name,'source':'Canada_Supplier',
                    'units_needed':gap,'supplier_stock':canada_avail,
                    'order_by':'2026-09-01','type':'Print Run','run_date':run_date,
                    'notes':f'Canada has {canada_avail:,}, short {gap:,} — new production needed.',
                })

    # --- Deduplicate transfers ---
    transfers_deduped = {}
    for q, rows in transfers_raw.items():
        dedup = defaultdict(int)
        for r in rows:
            dedup[(r['sku'], r['wh'], r['src'], r['type'])] += r['qty']
        transfers_deduped[q] = [
            {'sku':k[0],'wh':k[1],'src':k[2],'type':k[3],'qty':v}
            for k, v in sorted(dedup.items())
        ]

    WH_ORDER = ['Amazon_US_FBA','Amazon_CA_FBA','SLI','HBG','SAV','KCM','CA','EU','UK','AU']
    Q_LABELS = {
        'Q2':'Q2 — Apr / May / Jun',
        'Q3':'Q3 — Jul / Aug / Sep',
        'Q4':'Q4 — Oct / Nov / Dec (BFCM)',
    }

    def by_wh(rows):
        groups = defaultdict(list)
        for r in rows: groups[r['wh']].append(r)
        return {wh: groups[wh] for wh in WH_ORDER if wh in groups}

    # Annual totals per SKU per region
    annual_totals = defaultdict(lambda: defaultdict(float))
    for month_label, skus in monthly_forecast.items():
        for sid, regions in skus.items():
            for region, units in regions.items():
                annual_totals[sid][region] += units
    annual_totals = {sid: {r: round(v) for r, v in reg.items()}
                     for sid, reg in annual_totals.items()}

    result = {
        'generated':        run_date,
        'print_runs':       print_runs,
        'supplier_orders':  supplier_orders,
        'totals':           {q: len(rows) for q, rows in transfers_deduped.items()},
        'monthly_forecast': monthly_forecast,
        'annual_totals':    annual_totals,
        'action_log':       action_log,
        'sku_names':        sku_names,
        'forecast_basis':   '2025 actual monthly sales',
    }
    for q in ('Q2','Q3','Q4'):
        rows      = transfers_deduped.get(q, [])
        result[q] = {'label':Q_LABELS[q], 'by_warehouse':by_wh(rows), 'all_rows':rows}

    return result


def write_to_sheet(result):
    from sheets_client import get_sheets_service, get_sheet_id, write_tab, add_tab
    print("Connecting to Google Sheets...")
    service  = get_sheets_service()
    sheet_id = get_sheet_id()
    add_tab(service, sheet_id, 'Transfer_Print_Plan')

    rows = []
    rows.append(['Type','SKU_Name','Source','Units_Needed','Order_By','Supplier_Stock','Notes'])
    for r in result.get('print_runs', []):
        rows.append([r['type'],r['sku_name'],r['source'],r['units_needed'],r['order_by'],r['supplier_stock'],r['notes']])
    for r in result.get('supplier_orders', []):
        rows.append([r['type'],r['sku_name'],r['source'],r['units_needed'],r['order_by'],r['supplier_stock'],r['notes']])
    rows.append([])

    rows.append(['Quarter','SKU_Name','To_Warehouse','From_Warehouse','Units','Action_Type'])
    for q in ('Q2','Q3','Q4'):
        for wh, items in result.get(q,{}).get('by_warehouse',{}).items():
            for item in items:
                rows.append([q, item['sku'], wh, item['src'], item['qty'], item['type']])
    rows.append([])

    rows.append(['Month','SKU','US_Units','US_FBA_Units','CA_Units','EU_Units','UK_Units','AU_Units','Total'])
    for month_label, skus in result.get('monthly_forecast',{}).items():
        for sid, regions in skus.items():
            total = sum(regions.values())
            rows.append([
                month_label, result['sku_names'].get(sid, sid),
                regions.get('US',0), regions.get('US FBA',0),
                regions.get('CA',0), regions.get('EU',0),
                regions.get('UK',0), regions.get('AU',0),
                round(total),
            ])

    print(f"Writing {len(rows)} rows to Transfer_Print_Plan...")
    write_tab(service, sheet_id, 'Transfer_Print_Plan', rows)
    print("Done.")


def main():
    print("Running month-by-month simulation (demand basis: 2025 actual monthly sales)...")
    result = run_simulation()

    print(f"\n  Print runs needed:  {len(result['print_runs'])}")
    print(f"  Supplier orders:    {len(result['supplier_orders'])}")
    for q in ('Q2','Q3','Q4'):
        print(f"  {q} actions:        {result['totals'].get(q,0)}")

    if result['print_runs']:
        print("\n  *** PRINT RUNS NEEDED ***")
        for r in result['print_runs']:
            print(f"    {r['sku_name']}: {r['units_needed']:,} units — order by {r['order_by']}")
            print(f"    → {r['notes']}")
    else:
        print("\n  No new print runs needed — all replenishment covered by transfers + existing supplier stock.")

    if result['supplier_orders']:
        print("\n  Supplier orders (use existing stock):")
        for r in result['supplier_orders']:
            print(f"    {r['sku_name']}: {r['units_needed']:,} from {r['source']} (has {r['supplier_stock']:,}) — order by {r['order_by']}")

    tmp_dir  = os.path.join(PROJECT_ROOT, '.tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    out_path = os.path.join(tmp_dir, 'transfer_plan.json')
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nSaved to {out_path}")

    write_to_sheet(result)
    print("\nDone.")


if __name__ == '__main__':
    main()
