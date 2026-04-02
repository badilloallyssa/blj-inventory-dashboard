#!/usr/bin/env python3
"""
Build transfer + print plan from month-by-month inventory simulation.

Saves results to .tmp/transfer_plan.json and writes to Google Sheet
tab Transfer_Print_Plan.

Usage:
    python3 tools/build_transfer_plan.py
"""

import json, calendar
from datetime import date, timedelta
from collections import defaultdict
import os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

MONTH_ABBR = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
WAREHOUSES = ['SLI','HBG','SAV','KCM','EU','CA','AU','UK','Amazon_US_FBA','Amazon_CA_FBA']
US_WH      = ['SLI','HBG','SAV','KCM']


def run_simulation():
    with open(os.path.join(PROJECT_ROOT, '.tmp/data.json')) as f: data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, '.tmp/velocity.json')) as f: vel_raw = json.load(f)['velocity']
    with open(os.path.join(PROJECT_ROOT, '.tmp/seasonality.json')) as f: sea_raw = json.load(f)['indices']

    sku_names = {s['sku_id']: s['sku_name'] for s in data['config']['skus']}
    pos       = data.get('pos', [])
    TODAY     = date.today()

    supplier_stock = {e['sku_id']: {'china': float(e.get('china_supplier',0)), 'canada': float(e.get('canada_supplier',0))}
                      for e in data.get('supplier_stock', [])}

    def v90(sid, wh):
        v = vel_raw.get(sid,{}).get(wh,{}).get('v90',0.0)
        if wh == 'Amazon_CA_FBA' and v == 0:
            v = vel_raw.get(sid,{}).get('CA',{}).get('v90',0.0)
        return v

    def sea(sid, m): return float(sea_raw.get(sid,{}).get(MONTH_ABBR[m-1],1.0))
    def mdem(sid, wh, y, m): return v90(sid,wh) * sea(sid,m) * calendar.monthrange(y,m)[1]

    stk = {e['sku_id']:{k:float(v) for k,v in e['stock'].items()} for e in data['current_stock']}
    for po in pos:
        sid,dst = po['sku_id'], po['destination']
        if not any(s in po.get('status','').lower() for s in
                   ('ordered','in production','shipped','in transit','in-transit','pending')): continue
        stk.setdefault(sid,{})[dst] = stk.get(sid,{}).get(dst,0) + float(po.get('qty_ordered',0))

    def get_sources(wh, sid):
        if wh == 'Amazon_US_FBA':
            return [(w, 21, False) for w in sorted(US_WH, key=lambda w: stk[sid].get(w,0), reverse=True)] + [('China_AWD', 60, True)]
        if wh == 'Amazon_CA_FBA':
            return [('CA', 21, False), ('Canada_Supplier', 21, True)]
        if wh in US_WH:
            others = sorted([w for w in US_WH if w!=wh], key=lambda w: stk[sid].get(w,0), reverse=True)
            return [(w, 7, False) for w in others] + [('China_Supplier', 45, True)]
        if wh == 'EU':  return [('UK', 21, False), ('China_Supplier', 75, True)]
        if wh == 'UK':  return [('EU', 21, False), ('China_Supplier', 75, True)]
        if wh == 'AU':  return [('UK', 60, False), ('EU', 60, False), ('China_Supplier', 45, True)]
        if wh == 'CA':  return [('Canada_Supplier', 14, True)]
        return [('China_Supplier', 60, True)]

    QUARTER_OF = {4:'Q2',5:'Q2',6:'Q2', 7:'Q3',8:'Q3',9:'Q3', 10:'Q4',11:'Q4',12:'Q4'}
    po_new = defaultdict(float)   # (sid, src_label) -> units
    transfers_raw = defaultdict(list)  # quarter -> list

    y, m = TODAY.year, TODAY.month
    for _ in range(12):
        if y > 2026 or (y == 2026 and m > 12): break
        q   = QUARTER_OF.get(m, 'other')
        days_in_month = calendar.monthrange(y, m)[1]

        for sid in stk:
            for wh in WAREHOUSES:
                stk[sid][wh] = stk[sid].get(wh,0) - mdem(sid, wh, y, m)

        for sid in stk:
            for wh in WAREHOUSES:
                if v90(sid,wh) == 0: continue
                future_months = [(m+i-1)%12+1 for i in range(3)]
                peak_sea = max(sea(sid, mm) for mm in future_months)
                safety   = 90 * v90(sid,wh) * peak_sea
                if stk[sid].get(wh,0) >= safety: continue

                shortfall = safety - stk[sid].get(wh,0)
                for (src, lead, is_po) in get_sources(wh, sid):
                    if shortfall <= 0: break
                    if is_po:
                        po_new[(sid, src)] += shortfall
                        stk[sid][wh] = stk[sid].get(wh,0) + shortfall
                        if q in ('Q2','Q3','Q4'):
                            transfers_raw[q].append({'sku':sku_names[sid],'sku_id':sid,'wh':wh,'src':src,'qty':int(shortfall),'month':f'{MONTH_ABBR[m-1]} {y}','type':'NEW PO'})
                        shortfall = 0
                    else:
                        avail = stk[sid].get(src,0)
                        if avail <= 0: continue
                        moved = min(shortfall, avail)
                        stk[sid][src] = stk[sid].get(src,0) - moved
                        stk[sid][wh]  = stk[sid].get(wh,0) + moved
                        if q in ('Q2','Q3','Q4'):
                            transfers_raw[q].append({'sku':sku_names[sid],'sku_id':sid,'wh':wh,'src':src,'qty':int(moved),'month':f'{MONTH_ABBR[m-1]} {y}','type':'Transfer'})
                        shortfall -= moved

        if m==12: y,m = y+1,1
        else: m+=1

    # Roll up new POs, reconcile against supplier stock
    print_runs = []
    supplier_orders = []
    run_date = TODAY.strftime('%Y-%m-%d')

    for (sid, src), qty in po_new.items():
        qty = int(round(qty))
        name = sku_names.get(sid, sid)
        sup  = supplier_stock.get(sid, {})

        if 'Canada' in src:
            canada_avail = sup.get('canada', 0)
            if canada_avail >= qty:
                supplier_orders.append({'sku_id':sid,'sku_name':name,'source':src,'units_needed':qty,
                    'supplier_stock':int(canada_avail),'covered':True,'order_by':'2026-09-10',
                    'type':'Supplier Order','run_date':run_date,
                    'notes':f'Canada supplier has {int(canada_avail):,} — fully covered'})
            else:
                gap = qty - int(canada_avail)
                supplier_orders.append({'sku_id':sid,'sku_name':name,'source':src,'units_needed':qty,
                    'supplier_stock':int(canada_avail),'covered':False,'order_by':'2026-09-10',
                    'type':'Supplier Order','run_date':run_date,
                    'notes':f'Canada has {int(canada_avail):,}, short {gap:,} — additional print run needed'})
                print_runs.append({'sku_id':sid,'sku_name':name,'source':'China_Supplier','units_needed':gap,
                    'supplier_stock':int(sup.get('china',0)),'order_by':'2026-08-02','type':'Print Run',
                    'run_date':run_date,'notes':f'Canada short by {gap:,} units — new production required'})
        elif 'China' in src or 'AWD' in src:
            china_avail = sup.get('china', 0)
            if china_avail >= qty:
                supplier_orders.append({'sku_id':sid,'sku_name':name,'source':src,'units_needed':qty,
                    'supplier_stock':int(china_avail),'covered':True,'order_by':'2026-08-02',
                    'type':'Supplier Order','run_date':run_date,
                    'notes':f'China supplier has {int(china_avail):,} — covered, place order'})
            else:
                gap = qty - int(china_avail)
                print_runs.append({'sku_id':sid,'sku_name':name,'source':'China_Supplier','units_needed':gap,
                    'supplier_stock':int(china_avail),'order_by':'2026-08-02','type':'Print Run',
                    'run_date':run_date,
                    'notes':f'China has {int(china_avail):,}, need {gap:,} more — new production run required. Order by Aug 2 → arrives mid-Sep → FBA by Oct 1'})

    # Deduplicate transfers by (quarter, sku, wh, src, type)
    transfers_deduped = {}
    for q, rows in transfers_raw.items():
        dedup = defaultdict(int)
        for r in rows:
            dedup[(r['sku'], r['wh'], r['src'], r['type'])] += r['qty']
        transfers_deduped[q] = [{'sku':k[0],'wh':k[1],'src':k[2],'type':k[3],'qty':v}
                                 for k,v in sorted(dedup.items())]

    # Structure for dashboard
    WH_ORDER = ['Amazon_US_FBA','Amazon_CA_FBA','SLI','HBG','SAV','KCM','CA','EU','UK','AU','GLOBAL']
    def by_wh(rows):
        groups = defaultdict(list)
        for r in rows:
            groups[r['wh']].append(r)
        return {wh: groups[wh] for wh in WH_ORDER if wh in groups}

    Q_LABELS = {'Q2':'Q2 — Apr / May / Jun','Q3':'Q3 — Jul / Aug / Sep','Q4':'Q4 — Oct / Nov / Dec (BFCM)'}

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

    # Build rows for the sheet
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

    # Blank separator row
    rows.append([])

    # Section 2: Transfers
    rows.append(['Quarter', 'SKU_Name', 'To_Warehouse', 'From_Warehouse', 'Units', 'Action_Type', 'Month'])
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
                    '',  # Month not tracked at this level after dedup
                ])

    print(f"Writing {len(rows)} rows to Transfer_Print_Plan tab...")
    write_tab(service, sheet_id, 'Transfer_Print_Plan', rows)
    print("Done writing to sheet.")


def main():
    print("Running month-by-month inventory simulation...")
    result = run_simulation()

    print(f"  Print runs needed: {len(result['print_runs'])}")
    print(f"  Supplier orders: {len(result['supplier_orders'])}")
    print(f"  Q2 transfer rows: {result['totals'].get('Q2', 0)}")
    print(f"  Q3 transfer rows: {result['totals'].get('Q3', 0)}")
    print(f"  Q4 transfer rows: {result['totals'].get('Q4', 0)}")

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
