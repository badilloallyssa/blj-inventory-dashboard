#!/usr/bin/env python3
"""
Build transfer + print plan from month-by-month inventory simulation.

Key simulation rules:
- US demand split evenly across 4 US warehouses (SLI/HBG/SAV/KCM)
- CA replenished by transfer from US warehouses (not new print)
- Source warehouses never stripped below 25% buffer
- No UK→US transfers
- Seasonality from 2024-2025 actual data

Saves to .tmp/transfer_plan.json and writes to Google Sheet tab Transfer_Print_Plan.

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
NUM_US_WH  = len(US_WH)   # 4 — US velocity is a pool split evenly across all 4


def run_simulation():
    with open(os.path.join(PROJECT_ROOT, '.tmp/data.json')) as f: data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, '.tmp/velocity.json')) as f: vel_raw = json.load(f)['velocity']
    with open(os.path.join(PROJECT_ROOT, '.tmp/seasonality.json')) as f: sea_raw = json.load(f)['indices']

    sku_names = {s['sku_id']: s['sku_name'] for s in data['config']['skus']}
    pos       = data.get('pos', [])
    TODAY     = date.today()

    supplier_stock = {e['sku_id']: {'china': float(e.get('china_supplier',0)), 'canada': float(e.get('canada_supplier',0))}
                      for e in data.get('supplier_stock', [])}

    def v90_raw(sid, wh):
        """Raw v90 from velocity file."""
        v = vel_raw.get(sid,{}).get(wh,{}).get('v90',0.0)
        if v == 0 and wh == 'Amazon_CA_FBA':
            v = vel_raw.get(sid,{}).get('CA',{}).get('v90',0.0)
        return v

    def v90(sid, wh):
        """Per-warehouse daily velocity.
        US velocity in the data is the total US pool — split evenly across 4 US warehouses.
        """
        if wh in US_WH:
            return v90_raw(sid, 'US') / NUM_US_WH
        return v90_raw(sid, wh)

    def sea(sid, m): return float(sea_raw.get(sid,{}).get(MONTH_ABBR[m-1], 1.0))
    def mdem(sid, wh, y, m): return v90(sid, wh) * sea(sid, m) * calendar.monthrange(y, m)[1]

    # Initialize stock from current_stock + in-transit POs
    stk = {e['sku_id']: {k: float(v) for k,v in e['stock'].items()} for e in data['current_stock']}
    for po in pos:
        sid, dst = po['sku_id'], po['destination']
        status = po.get('status','').lower()
        if not any(s in status for s in ('ordered','in production','shipped','in transit','in-transit','pending')):
            continue
        stk.setdefault(sid, {})[dst] = stk.get(sid,{}).get(dst,0) + float(po.get('qty_ordered',0))

    def get_sources(wh, sid):
        """Return list of (source, lead_days, is_new_po) in priority order.
        Rules:
        - No UK→US transfers
        - CA gets from US warehouses first (transfer), then China (new PO) — no Canada supplier for CA
        - AU gets from UK or China
        - EU gets from UK or China
        """
        # US pool sorted by stock level descending
        us_sorted = sorted(US_WH, key=lambda w: stk.get(sid,{}).get(w,0), reverse=True)

        if wh == 'Amazon_US_FBA':
            return [(w, 7, False) for w in us_sorted] + [('China_AWD', 60, True)]
        if wh == 'Amazon_CA_FBA':
            return [('CA', 14, False), ('China_Supplier', 60, True)]
        if wh in US_WH:
            others = sorted([w for w in US_WH if w != wh], key=lambda w: stk.get(sid,{}).get(w,0), reverse=True)
            return [(w, 3, False) for w in others] + [('China_Supplier', 45, True)]
        if wh == 'CA':
            # User: transfer from US, no new Canada prints
            return [(w, 14, False) for w in us_sorted] + [('China_Supplier', 60, True)]
        if wh == 'EU':
            return [('UK', 21, False), ('China_Supplier', 75, True)]
        if wh == 'UK':
            return [('EU', 21, False), ('China_Supplier', 75, True)]
        if wh == 'AU':
            return [('UK', 60, False), ('EU', 60, False), ('China_Supplier', 60, True)]
        return [('China_Supplier', 60, True)]

    QUARTER_OF = {4:'Q2',5:'Q2',6:'Q2', 7:'Q3',8:'Q3',9:'Q3', 10:'Q4',11:'Q4',12:'Q4'}
    po_new = defaultdict(float)       # (sid, src_label) -> units
    transfers_raw = defaultdict(list) # quarter -> list of transfer dicts
    stockout_log = []                 # warnings about stockouts

    y, m = TODAY.year, TODAY.month

    for _ in range(12):
        if y > 2026 or (y == 2026 and m > 12): break
        q = QUARTER_OF.get(m, 'other')

        # 1. Deduct monthly demand from every warehouse
        for sid in stk:
            for wh in WAREHOUSES:
                demand = mdem(sid, wh, y, m)
                stk[sid][wh] = stk[sid].get(wh, 0) - demand

        # 2. Check if any warehouse needs replenishment; if so, transfer or order
        for sid in stk:
            for wh in WAREHOUSES:
                if v90(sid, wh) == 0:
                    continue

                # Safety stock target = 90 days × peak seasonality in next 3 months
                future_months = [(m + i - 1) % 12 + 1 for i in range(3)]
                peak_sea = max(sea(sid, mm) for mm in future_months)
                safety = 90 * v90(sid, wh) * peak_sea

                if stk[sid].get(wh, 0) >= safety:
                    continue

                shortfall = safety - stk[sid].get(wh, 0)

                for (src, lead, is_po) in get_sources(wh, sid):
                    if shortfall <= 0:
                        break
                    if is_po:
                        # New order from supplier
                        po_new[(sid, src)] += shortfall
                        stk[sid][wh] = stk[sid].get(wh, 0) + shortfall
                        if q in ('Q2','Q3','Q4'):
                            transfers_raw[q].append({
                                'sku': sku_names.get(sid, sid),
                                'sku_id': sid,
                                'wh': wh,
                                'src': src,
                                'qty': int(shortfall),
                                'month': f'{MONTH_ABBR[m-1]} {y}',
                                'type': 'NEW PO'
                            })
                        shortfall = 0
                    else:
                        # Internal transfer — respect 25% buffer at source
                        src_stock = stk[sid].get(src, 0)
                        # Buffer = 25% of source's current stock (don't strip below this)
                        buffer = 0.25 * max(src_stock, 0)
                        usable = max(0, src_stock - buffer)
                        if usable <= 0:
                            continue
                        moved = min(shortfall, usable)
                        stk[sid][src] = src_stock - moved
                        stk[sid][wh]  = stk[sid].get(wh, 0) + moved
                        if q in ('Q2','Q3','Q4'):
                            transfers_raw[q].append({
                                'sku': sku_names.get(sid, sid),
                                'sku_id': sid,
                                'wh': wh,
                                'src': src,
                                'qty': int(moved),
                                'month': f'{MONTH_ABBR[m-1]} {y}',
                                'type': 'Transfer'
                            })
                        shortfall -= moved

        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1

    # --- End-of-year stock snapshot ---
    print("\n=== END-OF-YEAR STOCK SNAPSHOT (after all transfers & sales) ===")
    for sid, wh_stk in sorted(stk.items()):
        name = sku_names.get(sid, sid)
        print(f"\n{name}:")
        for wh in WAREHOUSES:
            remaining = wh_stk.get(wh, 0)
            daily_vel = v90(sid, wh)
            dos = remaining / daily_vel if daily_vel > 0 else 9999
            flag = ' ⚠️ STOCKOUT RISK' if remaining < 0 else (' ⚠️ LOW' if dos < 30 else '')
            print(f"  {wh:20s}: {int(remaining):6d} units  ({int(dos)}d){flag}")

    # --- Roll up new POs, reconcile against supplier stock ---
    print_runs = []
    supplier_orders = []
    run_date = TODAY.strftime('%Y-%m-%d')

    for (sid, src), qty in po_new.items():
        qty = int(round(qty))
        name = sku_names.get(sid, sid)
        sup  = supplier_stock.get(sid, {})

        if 'China' in src or 'AWD' in src:
            china_avail = sup.get('china', 0)
            if china_avail >= qty:
                supplier_orders.append({
                    'sku_id': sid, 'sku_name': name, 'source': src,
                    'units_needed': qty, 'supplier_stock': int(china_avail),
                    'covered': True, 'order_by': '2026-08-02',
                    'type': 'Supplier Order', 'run_date': run_date,
                    'notes': f'China has {int(china_avail):,} — covered, place order'
                })
            else:
                gap = qty - int(china_avail)
                if int(china_avail) > 0:
                    supplier_orders.append({
                        'sku_id': sid, 'sku_name': name, 'source': src,
                        'units_needed': int(china_avail), 'supplier_stock': int(china_avail),
                        'covered': True, 'order_by': '2026-08-02',
                        'type': 'Supplier Order', 'run_date': run_date,
                        'notes': f'China has {int(china_avail):,} — order all available'
                    })
                print_runs.append({
                    'sku_id': sid, 'sku_name': name, 'source': 'China_Supplier',
                    'units_needed': gap, 'supplier_stock': int(china_avail),
                    'order_by': '2026-08-02', 'type': 'Print Run', 'run_date': run_date,
                    'notes': (
                        f'China has {int(china_avail):,}, need {gap:,} more units. '
                        f'New production run required. Order by Aug 2 → arrives mid-Sep → distribute by Oct 1.'
                    )
                })

    # Deduplicate transfers by (quarter, sku, wh, src, type) — sum qty
    transfers_deduped = {}
    for q, rows in transfers_raw.items():
        dedup = defaultdict(int)
        for r in rows:
            dedup[(r['sku'], r['wh'], r['src'], r['type'])] += r['qty']
        transfers_deduped[q] = [
            {'sku': k[0], 'wh': k[1], 'src': k[2], 'type': k[3], 'qty': v}
            for k, v in sorted(dedup.items())
        ]

    WH_ORDER = ['Amazon_US_FBA','Amazon_CA_FBA','SLI','HBG','SAV','KCM','CA','EU','UK','AU','GLOBAL']
    def by_wh(rows):
        groups = defaultdict(list)
        for r in rows:
            groups[r['wh']].append(r)
        return {wh: groups[wh] for wh in WH_ORDER if wh in groups}

    Q_LABELS = {
        'Q2': 'Q2 — Apr / May / Jun',
        'Q3': 'Q3 — Jul / Aug / Sep',
        'Q4': 'Q4 — Oct / Nov / Dec (BFCM)'
    }

    result = {
        'generated': run_date,
        'print_runs': print_runs,
        'supplier_orders': supplier_orders,
        'totals': {q: len(rows) for q, rows in transfers_deduped.items()},
    }
    for q in ('Q2','Q3','Q4'):
        rows = transfers_deduped.get(q, [])
        result[q] = {'label': Q_LABELS[q], 'by_warehouse': by_wh(rows), 'all_rows': rows}

    return result


def write_to_sheet(result):
    from sheets_client import get_sheets_service, get_sheet_id, write_tab, add_tab

    print("Connecting to Google Sheets...")
    service  = get_sheets_service()
    sheet_id = get_sheet_id()

    add_tab(service, sheet_id, 'Transfer_Print_Plan')

    rows = []

    # Section 1: Print runs + supplier orders
    rows.append(['Type', 'SKU_Name', 'Source', 'Units_Needed', 'Order_By', 'Supplier_Stock', 'Notes'])
    for r in result.get('print_runs', []):
        rows.append([
            r.get('type', 'Print Run'),
            r.get('sku_name', ''),
            r.get('source', ''),
            r.get('units_needed', ''),
            r.get('order_by', ''),
            r.get('supplier_stock', ''),
            r.get('notes', ''),
        ])
    for r in result.get('supplier_orders', []):
        rows.append([
            r.get('type', 'Supplier Order'),
            r.get('sku_name', ''),
            r.get('source', ''),
            r.get('units_needed', ''),
            r.get('order_by', ''),
            r.get('supplier_stock', ''),
            r.get('notes', ''),
        ])

    rows.append([])  # blank separator

    # Section 2: Transfers
    rows.append(['Quarter', 'SKU_Name', 'To_Warehouse', 'From_Warehouse', 'Units', 'Action_Type'])
    for q in ('Q2', 'Q3', 'Q4'):
        q_data = result.get(q, {})
        for wh, items in q_data.get('by_warehouse', {}).items():
            for item in items:
                rows.append([
                    q,
                    item.get('sku', ''),
                    wh,
                    item.get('src', ''),
                    item.get('qty', ''),
                    item.get('type', ''),
                ])

    print(f"Writing {len(rows)} rows to Transfer_Print_Plan tab...")
    write_tab(service, sheet_id, 'Transfer_Print_Plan', rows)
    print("Done writing to sheet.")


def main():
    print("Running month-by-month inventory simulation...")
    print("  - US demand split evenly across SLI/HBG/SAV/KCM")
    print("  - CA replenished by US→CA transfers (no Canada prints)")
    print("  - 25% buffer enforced on source warehouses")
    print("  - No UK→US transfers")

    result = run_simulation()

    print(f"\n  Print runs needed: {len(result['print_runs'])}")
    print(f"  Supplier orders:   {len(result['supplier_orders'])}")
    print(f"  Q2 transfer rows:  {result['totals'].get('Q2', 0)}")
    print(f"  Q3 transfer rows:  {result['totals'].get('Q3', 0)}")
    print(f"  Q4 transfer rows:  {result['totals'].get('Q4', 0)}")

    if result['print_runs']:
        print("\n  *** PRINT RUNS NEEDED ***")
        for r in result['print_runs']:
            print(f"    {r['sku_name']}: {r['units_needed']:,} units from {r['source']} — order by {r['order_by']}")
            print(f"    {r['notes']}")
    else:
        print("\n  No new print runs needed — all replenishment covered by transfers + supplier stock.")

    if result['supplier_orders']:
        print("\n  Supplier orders (existing stock):")
        for r in result['supplier_orders']:
            print(f"    {r['sku_name']}: {r['units_needed']:,} from {r['source']} (has {r['supplier_stock']:,}) — order by {r['order_by']}")

    # Save to .tmp/
    tmp_dir = os.path.join(PROJECT_ROOT, '.tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    out_path = os.path.join(tmp_dir, 'transfer_plan.json')
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nSaved to {out_path}")

    # Write to Google Sheet
    write_to_sheet(result)
    print("\nDone.")


if __name__ == '__main__':
    main()
