#!/usr/bin/env python3
"""
Build transfer + print plan with mixed demand basis:
  Q2 (Apr/May/Jun)  → current velocity (v90 × seasonality), since we're in Q2 now
  Q3 (Jul-Sep) and Q4 (Oct-Dec) → 2025 actual monthly sales (better BFCM signal)

Transfer routing rules:
  - No UK→US transfers
  - UK can transfer to AU only (not EU directly)
  - EU can transfer to UK
  - CA replenished from US warehouses (no new Canada prints)
  - Source warehouses never stripped below 25% buffer
  - China/Canada supplier used when warehouse transfers run out

Print run deduplication:
  - China_AWD and China_Supplier are the same factory → one print run per SKU

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

# Q2 months use velocity-based demand; Q3/Q4 use 2025 actuals
Q2_MONTHS = {4, 5, 6}


def load_data():
    with open(os.path.join(PROJECT_ROOT, '.tmp/data.json')) as f:
        return json.load(f)


def build_2025_monthly_demand(data):
    """2025 actual monthly sales → physical warehouse demand."""
    sales = data.get('sales', [])
    raw   = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    for row in sales:
        if str(row.get('year', '')) != '2025':
            continue
        sid = row.get('sku_id', '').strip()
        wh  = row.get('warehouse', '').strip()
        d   = row.get('date', '')
        try:
            mo = int(d.split('-')[1]) if '-' in d else int(d.split('/')[0])
        except Exception:
            continue
        raw[sid][wh][mo] += float(row.get('units_sold', 0) or 0)

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
    actual_2025    = build_2025_monthly_demand(data)

    with open(os.path.join(PROJECT_ROOT, '.tmp/velocity.json')) as f:
        vel_raw = json.load(f)['velocity']
    with open(os.path.join(PROJECT_ROOT, '.tmp/seasonality.json')) as f:
        sea_raw = json.load(f)['indices']

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

    # ── Velocity helpers (Q2 demand) ─────────────────────────────────────────
    def v90_raw(sid, wh):
        v = vel_raw.get(sid, {}).get(wh, {}).get('v90', 0.0)
        if v == 0 and wh in ('Amazon_CA_FBA', 'CA'):
            # CA FBA uses CA warehouse velocity
            v = vel_raw.get(sid, {}).get('CA', {}).get('v90', 0.0)
        return v

    def v90(sid, wh):
        """Per-warehouse daily velocity. US pool split evenly across 4 warehouses."""
        if wh in US_WH:
            return v90_raw(sid, 'US') / len(US_WH)
        return v90_raw(sid, wh)

    def sea(sid, m):
        return float(sea_raw.get(sid, {}).get(MONTH_ABBR[m - 1], 1.0))

    def velocity_demand(sid, wh, m):
        """v90 × seasonality × days — used for Q2."""
        return v90(sid, wh) * sea(sid, m) * calendar.monthrange(2026, m)[1]

    # ── Mixed demand function ─────────────────────────────────────────────────
    def demand_for(sid, wh, m):
        """Q2: velocity-based. Q3/Q4: 2025 actual. Falls back to velocity if no 2025 data."""
        if m in Q2_MONTHS:
            return velocity_demand(sid, wh, m)
        actual = actual_2025.get(sid, {}).get(wh, {}).get(m, 0.0)
        if actual > 0:
            return actual
        # Fallback for SKUs with no 2025 history in that warehouse
        return velocity_demand(sid, wh, m)

    def has_demand(sid, wh, m):
        """True if this warehouse has any expected demand this month."""
        return demand_for(sid, wh, m) > 0

    def safety_for(sid, wh, m):
        """Buffer = next 2 months of expected demand (forward-looking)."""
        total = 0.0
        for offset in range(1, 3):
            nm = (m - 1 + offset) % 12 + 1
            total += demand_for(sid, wh, nm)
        return total

    # ── Stock initialisation ──────────────────────────────────────────────────
    stk = {e['sku_id']: {k: float(v) for k, v in e['stock'].items()}
           for e in data['current_stock']}
    for po in pos:
        sid, dst = po['sku_id'], po['destination']
        status   = po.get('status', '').lower()
        if not any(s in status for s in
                   ('ordered','in production','shipped','in transit','in-transit','pending')):
            continue
        stk.setdefault(sid, {})[dst] = stk.get(sid, {}).get(dst, 0) + float(po.get('qty_ordered', 0))

    # ── Source routing ────────────────────────────────────────────────────────
    def get_sources(wh, sid):
        """
        Priority-ordered list of (source, lead_days, is_new_po).
        UK transfers: only to AU (not US, not EU directly).
        EU receives from China only (UK can't send to EU directly now).
        """
        us_sorted = sorted(US_WH, key=lambda w: stk.get(sid, {}).get(w, 0), reverse=True)

        if wh == 'Amazon_US_FBA':
            return [(w, 7, False) for w in us_sorted] + [('China_Supplier', 60, True)]
        if wh == 'Amazon_CA_FBA':
            return [('CA', 14, False), ('China_Supplier', 60, True)]
        if wh in US_WH:
            others = sorted([w for w in US_WH if w != wh],
                            key=lambda w: stk.get(sid, {}).get(w, 0), reverse=True)
            return [(w, 3, False) for w in others] + [('China_Supplier', 45, True)]
        if wh == 'CA':
            # Transfer from US warehouses first, then China
            return [(w, 14, False) for w in us_sorted] + [('China_Supplier', 60, True)]
        if wh == 'EU':
            return [('UK', 21, False), ('China_Supplier', 75, True)]
        if wh == 'UK':
            return [('EU', 21, False), ('China_Supplier', 75, True)]
        if wh == 'AU':
            return [('UK', 60, False), ('EU', 60, False), ('China_Supplier', 60, True)]
        return [('China_Supplier', 60, True)]

    QUARTER_OF    = {4:'Q2',5:'Q2',6:'Q2', 7:'Q3',8:'Q3',9:'Q3', 10:'Q4',11:'Q4',12:'Q4'}
    # sid → total units needed from China (all destinations combined)
    po_new_china  = defaultdict(float)
    # sid → {wh: units} — tracks which warehouses the China stock is going to and why
    po_china_dest = defaultdict(lambda: defaultdict(float))
    po_china_why  = defaultdict(list)   # sid → list of plain-English reasons
    po_new_canada = defaultdict(float)
    transfers_raw = defaultdict(list)
    action_log    = []
    monthly_forecast = {}

    y, m = TODAY.year, TODAY.month

    for _ in range(12):
        if y > 2026 or (y == 2026 and m > 12):
            break
        q           = QUARTER_OF.get(m, 'other')
        month_label = f'{MONTH_ABBR[m - 1]} {y}'
        basis       = 'velocity' if m in Q2_MONTHS else '2025 actuals'

        # ── Forecast snapshot ─────────────────────────────────────────────
        mfc = {}
        for sid in sku_list:
            mfc[sid] = defaultdict(float)
            for wh in WAREHOUSES:
                d      = demand_for(sid, wh, m)
                region = WH_REGION.get(wh, wh)
                mfc[sid][region] += d
        monthly_forecast[month_label] = {
            sid: {r: round(v) for r, v in regions.items()}
            for sid, regions in mfc.items()
        }

        # ── Deduct demand ─────────────────────────────────────────────────
        for sid in stk:
            for wh in WAREHOUSES:
                stk[sid][wh] = stk[sid].get(wh, 0) - demand_for(sid, wh, m)

        # ── Replenish ─────────────────────────────────────────────────────
        for sid in stk:
            for wh in WAREHOUSES:
                if not has_demand(sid, wh, m):
                    continue

                safety    = safety_for(sid, wh, m)
                current   = stk[sid].get(wh, 0)
                if current >= safety:
                    continue

                shortfall  = safety - current
                mo_demand  = demand_for(sid, wh, m)
                days_stock = max(0, current) / (mo_demand / calendar.monthrange(y, m)[1]) \
                             if mo_demand > 0 else 9999

                for (src, lead, is_po) in get_sources(wh, sid):
                    if shortfall <= 0:
                        break
                    if is_po:
                        # Consolidate all China sources under one key per SKU
                        if 'China' in src or 'AWD' in src:
                            po_new_china[sid] += shortfall
                            po_china_dest[sid][wh] += shortfall
                            # Build a plain-English reason for boss-level reporting
                            next2 = [demand_for(sid, wh, (m-1+i)%12+1) for i in range(1,3)]
                            po_china_why[sid].append(
                                f"{wh} runs short in {month_label} — "
                                f"needs {int(sum(next2)):,} units in the next 2 months "
                                f"(2025 pace) but has no transfer source available."
                            )
                        else:
                            po_new_canada[sid] += shortfall
                        stk[sid][wh] = stk[sid].get(wh, 0) + shortfall
                        reason = (
                            f"After {month_label} sales ({basis}), "
                            f"{sku_names.get(sid,sid)} at {wh} has ~{int(days_stock)}d of stock. "
                            f"No warehouse available — ordering {int(shortfall):,} units from {src}."
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

                        next_mo_d = demand_for(sid, src, (m % 12) + 1)
                        src_days  = int(max(0, src_stock) / (next_mo_d / 30)) \
                                    if next_mo_d > 0 else 9999
                        reason = (
                            f"After {month_label} sales ({basis}), "
                            f"{sku_names.get(sid,sid)} at {wh} drops to ~{int(days_stock)}d of stock "
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

    # ── End-of-year snapshot ──────────────────────────────────────────────────
    print("\n=== END-OF-YEAR STOCK SNAPSHOT ===")
    for sid in sku_list:
        if sid not in stk:
            continue
        name = sku_names.get(sid, sid)
        print(f"\n{name}:")
        for wh in WAREHOUSES:
            remaining = stk[sid].get(wh, 0)
            mo_d      = demand_for(sid, wh, 11)  # Nov as burn-rate proxy
            dos       = remaining / (mo_d / 30) if mo_d > 0 else 9999
            flag      = ' ⚠️  STOCKOUT' if remaining < 0 else \
                        (' ⚠️  LOW' if dos < 30 and mo_d > 0 else '')
            print(f"  {wh:20s}: {int(remaining):7,}  (~{int(dos)}d){flag}")

    # ── Roll up print runs (one entry per SKU per supplier) ───────────────────
    print_runs      = []
    supplier_orders = []
    run_date        = date.today().strftime('%Y-%m-%d')

    for sid, qty in po_new_china.items():
        qty  = int(round(qty))
        name = sku_names.get(sid, sid)
        sup  = supplier_stock.get(sid, {})
        china_avail = int(sup.get('china', 0))

        # Build destination breakdown string: "EU: 422, SLI: 300, ..."
        dest_map  = po_china_dest.get(sid, {})
        dest_str  = ', '.join(f'{wh}: {int(round(u)):,}' for wh, u in
                              sorted(dest_map.items(), key=lambda x: -x[1]))
        why_lines = po_china_why.get(sid, [])
        # Deduplicate why lines
        seen = set(); why_uniq = []
        for w in why_lines:
            if w not in seen: seen.add(w); why_uniq.append(w)

        if china_avail >= qty:
            supplier_orders.append({
                'sku_id':sid,'sku_name':name,'source':'China_Supplier',
                'units_needed':qty,'supplier_stock':china_avail,
                'covered':True,'order_by':'2026-08-02',
                'type':'Supplier Order','run_date':run_date,
                'destinations': dest_str,
                'why': why_uniq,
                'notes':f'China has {china_avail:,} in stock — fully covered. Place order now.',
            })
        else:
            gap = qty - china_avail
            if china_avail > 0:
                supplier_orders.append({
                    'sku_id':sid,'sku_name':name,'source':'China_Supplier',
                    'units_needed':china_avail,'supplier_stock':china_avail,
                    'covered':True,'order_by':'2026-08-02',
                    'type':'Supplier Order','run_date':run_date,
                    'destinations': dest_str,
                    'why': why_uniq,
                    'notes':f'China has {china_avail:,} available — order all of it now.',
                })
            print_runs.append({
                'sku_id':sid,'sku_name':name,'source':'China_Supplier',
                'units_needed':gap,'supplier_stock':china_avail,
                'order_by':'2026-08-02','type':'Print Run','run_date':run_date,
                'destinations': dest_str,
                'why': why_uniq,
                'notes':(
                    f'Need {qty:,} units total from China; only {china_avail:,} in existing stock. '
                    f'New production run of {gap:,} units required. '
                    f'Order by Aug 2 → production ~6 weeks → arrives Sep → in warehouses/FBA by Oct 1 for BFCM.'
                ),
            })

    for sid, qty in po_new_canada.items():
        qty  = int(round(qty))
        name = sku_names.get(sid, sid)
        sup  = supplier_stock.get(sid, {})
        canada_avail = int(sup.get('canada', 0))

        if canada_avail >= qty:
            supplier_orders.append({
                'sku_id':sid,'sku_name':name,'source':'Canada_Supplier',
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

    # ── Deduplicate transfers ──────────────────────────────────────────────────
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
        'Q2':'Q2 — Apr / May / Jun  (velocity-based forecast)',
        'Q3':'Q3 — Jul / Aug / Sep  (2025 actual sales)',
        'Q4':'Q4 — Oct / Nov / Dec  (2025 actual sales · BFCM)',
    }

    def by_wh(rows):
        groups = defaultdict(list)
        for r in rows: groups[r['wh']].append(r)
        return {wh: groups[wh] for wh in WH_ORDER if wh in groups}

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
        'forecast_basis':   'Q2: velocity × seasonality  |  Q3/Q4: 2025 actual monthly sales',
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
                rows.append([q,item['sku'],wh,item['src'],item['qty'],item['type']])
    rows.append([])

    rows.append(['Month','Forecast_Basis','SKU','US_Units','US_FBA_Units','CA_Units','EU_Units','UK_Units','AU_Units','Total'])
    for month_label, skus in result.get('monthly_forecast',{}).items():
        basis = 'velocity' if any(f' {mo} ' in month_label or month_label.startswith(mo)
                                  for mo in ('Apr','May','Jun')) else '2025 actuals'
        for sid, regions in skus.items():
            total = sum(regions.values())
            rows.append([
                month_label, basis, result['sku_names'].get(sid, sid),
                regions.get('US',0), regions.get('US FBA',0),
                regions.get('CA',0), regions.get('EU',0),
                regions.get('UK',0), regions.get('AU',0),
                round(total),
            ])

    print(f"Writing {len(rows)} rows to Transfer_Print_Plan...")
    write_tab(service, sheet_id, 'Transfer_Print_Plan', rows)
    print("Done.")


def main():
    print("Running simulation...")
    print("  Q2 demand: v90 × seasonality (current velocity)")
    print("  Q3/Q4 demand: 2025 actual monthly sales")
    print("  UK transfers: AU only (not US, not EU)")
    print("  CA replenishment: US warehouses → CA transfer")

    result = run_simulation()

    print(f"\n  Print runs needed:  {len(result['print_runs'])}")
    print(f"  Supplier orders:    {len(result['supplier_orders'])}")
    for q in ('Q2','Q3','Q4'):
        print(f"  {q} actions:        {result['totals'].get(q,0)}")

    if result['print_runs']:
        print("\n  *** PRINT RUNS NEEDED ***")
        for r in result['print_runs']:
            print(f"    {r['sku_name']}: {r['units_needed']:,} units from {r['source']} — order by {r['order_by']}")
            print(f"    → {r['notes']}")
    else:
        print("\n  No new print runs needed.")

    if result['supplier_orders']:
        print("\n  Supplier orders (existing stock, place order now):")
        for r in result['supplier_orders']:
            print(f"    {r['sku_name']}: {r['units_needed']:,} from {r['source']} (has {r['supplier_stock']:,}) — by {r['order_by']}")

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
