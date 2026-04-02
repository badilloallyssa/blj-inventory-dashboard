#!/usr/bin/env python3
"""
Build transfer + print plan.

Print runs are calculated directly:
  For each SKU:  total demand Apr-Dec  vs  total available stock + supplier
  US region (SLI/HBG/SAV/KCM/FBA/CA) is isolated — UK cannot transfer to US.
  Intl region (UK/EU/AU) shares freely.
  Supplier stock covers US gap first, then any intl gap.
  Shortfall after all sources = new print run needed.

Transfers are planned via monthly simulation:
  Each month demand is deducted, then warehouses below their safety buffer
  are replenished from other warehouses (no supplier orders — those come from
  the print run calculation above).

Demand basis: 2025 actual monthly sales. Fallback: v90 x seasonality.

Transfer routing rules:
  UK → EU ok  |  UK → AU ok  |  UK → US blocked
  CA replenished from US warehouses
  Source warehouses never stripped below 25% buffer

Outputs:
  .tmp/transfer_plan.json
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

SALES_WH_MAP = {
    'US':            ['SLI','HBG','SAV','KCM'],
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
        return json.load(f)


def build_actuals(data):
    """2025 monthly actuals → {sid: {phys_wh: {month: units}}}"""
    sales = data.get('sales', [])
    raw   = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for row in sales:
        if str(row.get('year', '')) != '2025': continue
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
    """Current stock + in-transit POs per SKU per warehouse."""
    stk = {e['sku_id']: {k: float(v) for k, v in e['stock'].items()}
           for e in data['current_stock']}
    for po in data.get('pos', []):
        sid, dst = po['sku_id'], po['destination']
        status   = po.get('status', '').lower()
        if not any(s in status for s in
                   ('ordered','in production','shipped','in transit','in-transit','pending')):
            continue
        stk.setdefault(sid, {})[dst] = stk.get(sid, {}).get(dst, 0) + float(po.get('qty_ordered', 0))
    return stk


def get_supplier_stock(data):
    return {
        e['sku_id']: {'china': float(e.get('china_supplier', 0)),
                      'canada': float(e.get('canada_supplier', 0))}
        for e in data.get('supplier_stock', [])
    }


# ── STEP 1: Per-GEO print run calculation ────────────────────────────────────

def compute_print_runs(data, actuals, vel_raw, sea_raw, sku_names, sku_list, run_date):
    """
    Analyse each GEO independently (US_POOL, Amazon_US_FBA, CA, UK, EU, AU).

    Demand target = Apr 2–Dec 31 sales + Jan+Feb 2027 carry-over stock
    (using 2025 Jan/Feb actuals as the carry-over proxy so no GEO stocks out
    at the start of 2027).

    Step A: Apply inter-GEO transfers (surplus GEO → deficit GEO, routing rules).
    Step B: Apply available supplier stock to remaining deficits (US side first).
    Step C: Per-GEO breakdown of print run destinations.

    Transfer routing:
      US_POOL surplus → Amazon_US_FBA → CA
      UK surplus     → AU → EU
      EU surplus     → AU → UK
      UK/EU/AU → US is BLOCKED
    """
    stk          = get_starting_stock(data)
    supplier_stk = get_supplier_stock(data)

    APR_FACTOR = 28.0 / 30.0   # Apr 2 → Apr 30 (28 days remaining)

    def sea(sid, m): return float(sea_raw.get(sid, {}).get(MONTH_ABBR[m-1], 1.0))

    def v90(sid, wh):
        v = vel_raw.get(sid, {}).get(wh, {}).get('v90', 0.0)
        if v == 0 and wh in US_WH:
            return vel_raw.get(sid, {}).get('US', {}).get('v90', 0.0) / len(US_WH)
        return v

    def vel_demand(sid, wh, m):
        return v90(sid, wh) * sea(sid, m) * calendar.monthrange(2026, m)[1]

    def actual_dem(sid, wh, m):
        a = actuals.get(sid, {}).get(wh, {}).get(m, 0.0)
        return a if a > 0 else vel_demand(sid, wh, m)

    GEO_WHS = {
        'US_POOL':       US_WH,
        'Amazon_US_FBA': ['Amazon_US_FBA'],
        'CA':            ['CA'],
        'Amazon_CA_FBA': ['Amazon_CA_FBA'],
        'UK':            ['UK'],
        'EU':            ['EU'],
        'AU':            ['AU'],
    }
    ALL_GEOS  = list(GEO_WHS.keys())
    US_GEOS   = ['US_POOL', 'Amazon_US_FBA', 'CA', 'Amazon_CA_FBA']
    INTL_GEOS = ['UK', 'EU', 'AU']

    print_runs      = []
    supplier_orders = []

    for sid in sku_list:
        name  = sku_names.get(sid, sid)
        sup   = supplier_stk.get(sid, {})
        china_avail  = int(sup.get('china', 0))
        canada_avail = int(sup.get('canada', 0))
        total_supplier = china_avail + canada_avail

        # ── Per-GEO stock and demand ────────────────────────────────────────
        # demand = Apr 2–Dec 31  +  Jan+Feb 2027 carry-over (2025 actuals)
        geo_stock    = {}
        geo_dem_sell = {}   # Apr–Dec selling demand
        geo_dem_co   = {}   # Jan+Feb carry-over target
        geo_demand   = {}   # total = sell + carry-over

        for geo, whs in GEO_WHS.items():
            stock = sum(stk.get(sid, {}).get(w, 0) for w in whs)
            if geo == 'US_POOL':
                sell = sum(actual_dem(sid, w, 4) for w in whs) * APR_FACTOR
                for m in range(5, 13):
                    sell += sum(actual_dem(sid, w, m) for w in whs)
                co = sum(actual_dem(sid, w, 1) + actual_dem(sid, w, 2) for w in whs)
            else:
                sell = actual_dem(sid, whs[0], 4) * APR_FACTOR
                for m in range(5, 13):
                    sell += actual_dem(sid, whs[0], m)
                co = actual_dem(sid, whs[0], 1) + actual_dem(sid, whs[0], 2)
            geo_stock[geo]    = stock
            geo_dem_sell[geo] = sell
            geo_dem_co[geo]   = co
            geo_demand[geo]   = sell + co

        # gap > 0 = surplus, gap < 0 = deficit (must have enough for sell+carry-over)
        geo_gap = {geo: geo_stock[geo] - geo_demand[geo] for geo in ALL_GEOS}

        # ── Step A: Transfers (respect 25 % source buffer) ─────────────────
        transfer_log = []

        def do_transfer(src, dst):
            surplus = geo_gap.get(src, 0)
            deficit = -geo_gap.get(dst, 0)
            if surplus <= 0 or deficit <= 0:
                return
            usable = min(surplus, geo_stock[src] * 0.75)
            moved  = min(usable, deficit)
            if moved <= 0:
                return
            geo_gap[src] -= moved
            geo_gap[dst] += moved
            transfer_log.append((src, dst, int(moved)))

        do_transfer('US_POOL', 'Amazon_US_FBA')
        do_transfer('US_POOL', 'CA')
        do_transfer('UK', 'AU')
        do_transfer('EU', 'AU')
        do_transfer('UK', 'EU')
        do_transfer('EU', 'UK')

        # ── Step B: Supplier covers remaining deficits (US first) ──────────
        remaining_sup = total_supplier
        sup_used_by   = {}

        for geo in ['Amazon_US_FBA', 'CA', 'US_POOL', 'AU', 'EU', 'UK']:
            if remaining_sup <= 0:
                break
            deficit = max(0.0, -geo_gap[geo])
            if deficit <= 0:
                continue
            give = min(remaining_sup, deficit)
            geo_gap[geo]    += give
            remaining_sup   -= give
            sup_used_by[geo] = int(give)

        # ── Step C: Per-GEO print run destinations ─────────────────────────
        geo_print = {geo: int(round(max(0, -geo_gap[geo]))) for geo in ALL_GEOS}
        total_print   = sum(geo_print.values())
        supplier_used = total_supplier - remaining_sup

        # Summaries
        us_total_dem   = sum(geo_demand[g] for g in US_GEOS)
        us_total_stk   = sum(geo_stock[g]  for g in US_GEOS)
        intl_total_dem = sum(geo_demand[g] for g in INTL_GEOS)
        intl_total_stk = sum(geo_stock[g]  for g in INTL_GEOS)

        # Destinations: per-GEO breakdown
        dest_parts = []
        for geo in ALL_GEOS:
            if geo_print[geo] > 0:
                dest_parts.append(f'{geo}: {geo_print[geo]:,}')
        dest_str = ' | '.join(dest_parts) if dest_parts else ''

        # Why explanation
        why = []
        uk_stk = int(stk.get(sid, {}).get('UK', 0))
        for geo in ALL_GEOS:
            shortage = geo_print[geo]
            if shortage <= 0:
                continue
            sell   = int(geo_dem_sell[geo])
            co_tgt = int(geo_dem_co[geo])
            s_stk  = int(geo_stock[geo])
            xf_in  = sum(qty for src, dst, qty in transfer_log if dst == geo)
            s_sup  = sup_used_by.get(geo, 0)
            why.append(
                f'{geo}: needs {sell:,} units Apr–Dec + {co_tgt:,} carry-over (Jan/Feb 2027) '
                f'= {sell+co_tgt:,} total. Has {s_stk:,} stock'
                + (f' + {xf_in:,} transfer in' if xf_in else '')
                + (f' + {s_sup:,} supplier' if s_sup else '')
                + f'. Short {shortage:,} → print {shortage:,} units to {geo}.'
                + (f" (UK's {uk_stk:,} cannot go to US)" if geo in US_GEOS and uk_stk > 0 else '')
            )

        # Supplier orders
        if supplier_used > 0:
            dest_sup = [f'{g}: {q:,}' for g, q in sup_used_by.items()]
            supplier_orders.append({
                'sku_id': sid, 'sku_name': name, 'source': 'China_Supplier',
                'units_needed': int(supplier_used),
                'supplier_stock': total_supplier,
                'covered': True,
                'order_by': '2026-09-06',
                'type': 'Supplier Order',
                'run_date': run_date,
                'destinations': ' | '.join(dest_sup),
                'why': why,
                'notes': 'Existing supplier stock — dispatch now to cover GEO deficits.',
            })

        if total_print > 0:
            print_runs.append({
                'sku_id': sid, 'sku_name': name, 'source': 'China_Supplier',
                'units_needed': total_print,
                'supplier_stock': china_avail,
                'order_by': '2026-09-06',
                'type': 'Print Run',
                'run_date': run_date,
                'destinations': dest_str,
                'why': why,
                'notes': (
                    f'Covers Apr 2–Dec 31 selling demand + Jan/Feb 2027 carry-over so no GEO stocks out. '
                    f'Gap after all transfers + {total_supplier:,} supplier units: {total_print:,}. '
                    f'Order by Sep 6 (AU lead time) → arrives Nov → distribute before BFCM.'
                ),
            })

        # Debug
        status = f'PRINT RUN: {total_print:,} units' if total_print > 0 else 'OK - covered'
        print(f'  {name}: US gap {int(us_total_stk - us_total_dem):+,} | '
              f'Intl gap {int(intl_total_stk - intl_total_dem):+,} | '
              f'Supplier {total_supplier:,} | {status}')

    return print_runs, supplier_orders


# ── STEP 2: Monthly simulation for TRANSFER routing only ──────────────────────

def run_transfer_simulation(data, actuals, vel_raw, sea_raw, sku_names, sku_list):
    """
    Month-by-month: deduct demand, then replenish by warehouse transfers only.
    No new supplier orders here — print run quantities come from compute_print_runs().
    """
    stk = get_starting_stock(data)

    def v90_raw(sid, wh):
        v = vel_raw.get(sid, {}).get(wh, {}).get('v90', 0.0)
        if v == 0 and wh in ('Amazon_CA_FBA',):
            v = vel_raw.get(sid, {}).get('CA', {}).get('v90', 0.0)
        return v

    def v90(sid, wh):
        if wh in US_WH: return v90_raw(sid, 'US') / len(US_WH)
        return v90_raw(sid, wh)

    def sea(sid, m): return float(sea_raw.get(sid, {}).get(MONTH_ABBR[m-1], 1.0))

    def vel_demand(sid, wh, m):
        return v90(sid, wh) * sea(sid, m) * calendar.monthrange(2026, m)[1]

    def demand_for(sid, wh, m):
        a = actuals.get(sid, {}).get(wh, {}).get(m, 0.0)
        return a if a > 0 else vel_demand(sid, wh, m)

    def safety_for(sid, wh, m):
        return sum(demand_for(sid, wh, (m - 1 + i) % 12 + 1) for i in range(1, 3))

    def get_transfer_sources(wh, sid):
        us_sorted = sorted(US_WH, key=lambda w: stk.get(sid, {}).get(w, 0), reverse=True)
        if wh == 'Amazon_US_FBA':
            return [(w, 7) for w in us_sorted]
        if wh == 'Amazon_CA_FBA':
            return [('CA', 14)]
        if wh in US_WH:
            others = sorted([w for w in US_WH if w != wh],
                            key=lambda w: stk.get(sid, {}).get(w, 0), reverse=True)
            return [(w, 3) for w in others]
        if wh == 'CA':
            return [(w, 14) for w in us_sorted]
        if wh == 'EU':
            return [('UK', 21)]
        if wh == 'UK':
            return [('EU', 21)]
        if wh == 'AU':
            return [('UK', 60), ('EU', 60)]
        return []

    QUARTER_OF   = {4:'Q2',5:'Q2',6:'Q2', 7:'Q3',8:'Q3',9:'Q3', 10:'Q4',11:'Q4',12:'Q4'}
    transfers_raw = defaultdict(list)
    action_log    = []
    monthly_forecast = {}

    y, m = date.today().year, date.today().month

    for _ in range(12):
        if y > 2026 or (y == 2026 and m > 12): break
        q           = QUARTER_OF.get(m, 'other')
        month_label = f'{MONTH_ABBR[m-1]} {y}'

        # Forecast snapshot
        mfc = {}
        for sid in sku_list:
            mfc[sid] = defaultdict(float)
            for wh in WAREHOUSES:
                mfc[sid][WH_REGION.get(wh, wh)] += demand_for(sid, wh, m)
        monthly_forecast[month_label] = {
            sid: {r: round(v) for r, v in regs.items()} for sid, regs in mfc.items()
        }

        # Deduct demand
        for sid in stk:
            for wh in WAREHOUSES:
                stk[sid][wh] = stk[sid].get(wh, 0) - demand_for(sid, wh, m)

        # Transfer-only replenishment
        for sid in stk:
            for wh in WAREHOUSES:
                mo_dem = demand_for(sid, wh, m)
                if mo_dem == 0: continue
                safety  = safety_for(sid, wh, m)
                current = stk[sid].get(wh, 0)
                if current >= safety: continue
                shortfall = safety - current
                dos = max(0, current) / (mo_dem / calendar.monthrange(y, m)[1]) if mo_dem > 0 else 9999

                for (src, lead) in get_transfer_sources(wh, sid):
                    if shortfall <= 0: break
                    src_stock = stk[sid].get(src, 0)
                    buffer    = 0.25 * max(src_stock, 0)
                    usable    = max(0, src_stock - buffer)
                    if usable <= 0: continue
                    moved = min(shortfall, usable)
                    stk[sid][src] = src_stock - moved
                    stk[sid][wh]  = stk[sid].get(wh, 0) + moved

                    next_mo_d = demand_for(sid, src, (m % 12) + 1)
                    src_dos   = int(max(0, src_stock) / (next_mo_d / 30)) if next_mo_d > 0 else 9999
                    reason = (
                        f"After {month_label} sales, {sku_names.get(sid,sid)} at {wh} "
                        f"drops to ~{int(dos)}d of stock "
                        f"(next 2 months need {int(safety):,} units as buffer). "
                        f"Transfer {int(moved):,} units from {src} "
                        f"({src} has {int(src_stock):,} units / ~{src_dos}d to spare)."
                    )
                    if q in ('Q2','Q3','Q4'):
                        action_log.append({'month':month_label,'quarter':q,
                            'sku':sku_names.get(sid,sid),'wh':wh,'src':src,
                            'qty':int(moved),'type':'Transfer','reason':reason})
                        transfers_raw[q].append({'sku':sku_names.get(sid,sid),'sku_id':sid,
                            'wh':wh,'src':src,'qty':int(moved),
                            'month':month_label,'type':'Transfer'})
                    shortfall -= moved

        if m == 12: y, m = y+1, 1
        else: m += 1

    # Deduplicate
    transfers_deduped = {}
    for q, rows in transfers_raw.items():
        dedup = defaultdict(int)
        for r in rows: dedup[(r['sku'], r['wh'], r['src'], r['type'])] += r['qty']
        transfers_deduped[q] = [{'sku':k[0],'wh':k[1],'src':k[2],'type':k[3],'qty':v}
                                 for k,v in sorted(dedup.items())]

    return transfers_deduped, action_log, monthly_forecast


def main():
    print("Loading data...")
    data      = load_data()
    actuals   = build_actuals(data)

    with open(os.path.join(PROJECT_ROOT, '.tmp/velocity.json')) as f:
        vel_raw = json.load(f)['velocity']
    with open(os.path.join(PROJECT_ROOT, '.tmp/seasonality.json')) as f:
        sea_raw = json.load(f)['indices']

    sku_names = {s['sku_id']: s['sku_name'] for s in data['config']['skus']}
    sku_list  = [s['sku_id'] for s in data['config']['skus']]
    run_date  = date.today().strftime('%Y-%m-%d')

    print("\nStep 1 — Computing print runs (direct demand vs stock)...")
    print_runs, supplier_orders = compute_print_runs(
        data, actuals, vel_raw, sea_raw, sku_names, sku_list, run_date)

    print("\nStep 2 — Planning transfers (monthly simulation)...")
    transfers_deduped, action_log, monthly_forecast = run_transfer_simulation(
        data, actuals, vel_raw, sea_raw, sku_names, sku_list)

    # Assemble result
    WH_ORDER = ['Amazon_US_FBA','Amazon_CA_FBA','SLI','HBG','SAV','KCM','CA','EU','UK','AU']
    Q_LABELS = {'Q2':'Q2 — Apr / May / Jun','Q3':'Q3 — Jul / Aug / Sep','Q4':'Q4 — Oct / Nov / Dec (BFCM)'}

    def by_wh(rows):
        groups = defaultdict(list)
        for r in rows: groups[r['wh']].append(r)
        return {wh: groups[wh] for wh in WH_ORDER if wh in groups}

    annual_totals = defaultdict(lambda: defaultdict(float))
    for ml, skus in monthly_forecast.items():
        for sid, regs in skus.items():
            for reg, units in regs.items(): annual_totals[sid][reg] += units
    annual_totals = {sid: {r: round(v) for r, v in regs.items()} for sid, regs in annual_totals.items()}

    result = {
        'generated':        run_date,
        'print_runs':       print_runs,
        'supplier_orders':  supplier_orders,
        'totals':           {q: len(rows) for q, rows in transfers_deduped.items()},
        'monthly_forecast': monthly_forecast,
        'annual_totals':    annual_totals,
        'action_log':       action_log,
        'sku_names':        sku_names,
        'forecast_basis':   '2025 actual monthly sales (velocity fallback if no history)',
    }
    for q in ('Q2','Q3','Q4'):
        rows      = transfers_deduped.get(q, [])
        result[q] = {'label':Q_LABELS[q], 'by_warehouse':by_wh(rows), 'all_rows':rows}

    # Summary to console
    print(f"\n{'='*60}")
    print("PRINT RUNS NEEDED:")
    if print_runs:
        for p in print_runs:
            print(f"  {p['sku_name']}: {p['units_needed']:,} units → {p['destinations']}")
    else:
        print("  None — all products covered by existing stock + transfers.")

    if supplier_orders:
        print("\nSUPPLIER ORDERS (existing stock, order now):")
        for o in supplier_orders:
            print(f"  {o['sku_name']}: {o['units_needed']:,} from {o['source']} → {o.get('destinations','')}")

    print(f"\nTRANSFERS: Q2={result['totals'].get('Q2',0)} | Q3={result['totals'].get('Q3',0)} | Q4={result['totals'].get('Q4',0)}")
    print(f"{'='*60}")

    # Save
    tmp_dir  = os.path.join(PROJECT_ROOT, '.tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    out_path = os.path.join(tmp_dir, 'transfer_plan.json')
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nSaved to {out_path}")

    # Write to sheet
    from sheets_client import get_sheets_service, get_sheet_id, write_tab, add_tab
    print("Writing to Google Sheets...")
    service  = get_sheets_service()
    sheet_id = get_sheet_id()
    add_tab(service, sheet_id, 'Transfer_Print_Plan')

    rows = [['Type','SKU_Name','Source','Units_Needed','Order_By','Supplier_Stock','Destinations','Notes']]
    for r in print_runs:
        rows.append([r['type'],r['sku_name'],r['source'],r['units_needed'],r['order_by'],r['supplier_stock'],r.get('destinations',''),r['notes']])
    for r in supplier_orders:
        rows.append([r['type'],r['sku_name'],r['source'],r['units_needed'],r['order_by'],r['supplier_stock'],r.get('destinations',''),r['notes']])
    rows.append([])
    rows.append(['Quarter','SKU_Name','To_Warehouse','From_Warehouse','Units','Action_Type'])
    for q in ('Q2','Q3','Q4'):
        for wh, items in result.get(q,{}).get('by_warehouse',{}).items():
            for item in items:
                rows.append([q,item['sku'],wh,item['src'],item['qty'],item['type']])
    rows.append([])
    rows.append(['Month','SKU','US_Units','US_FBA_Units','CA_Units','EU_Units','UK_Units','AU_Units','Total'])
    for ml, skus in monthly_forecast.items():
        for sid, regs in skus.items():
            total = sum(regs.values())
            rows.append([ml, sku_names.get(sid,sid),
                         regs.get('US',0), regs.get('US FBA',0),
                         regs.get('CA',0), regs.get('EU',0),
                         regs.get('UK',0), regs.get('AU',0), round(total)])

    write_tab(service, sheet_id, 'Transfer_Print_Plan', rows)
    print(f"Wrote {len(rows)} rows to Transfer_Print_Plan tab.")
    print("\nDone.")


if __name__ == '__main__':
    main()
