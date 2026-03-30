"""
Inventory Dashboard — Flask web app.
Serves an interactive dashboard with live data from Google Sheets.

Local:  PORT=5001 python3 dashboard/app.py
Render: auto-detected via render.yaml
"""
import os
import sys
import json
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))

app = Flask(__name__)

WAREHOUSES = ['SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA']
WH_LABELS  = {'SLI':'SLI','HBG':'HBG','SAV':'SAV','KCM':'KCM','EU':'EU','CA':'CA',
               'AU':'AU','UK':'UK','Amazon_US_FBA':'FBA US','Amazon_CA_FBA':'FBA CA'}
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']


def safe_float(v):
    try: return float(v or 0)
    except: return 0.0

def safe_int(v):
    try: return int(float(v or 0))
    except: return 0

def parse_date(s):
    for fmt in ('%Y-%m-%d','%m/%d/%Y','%d/%m/%Y','%Y/%m/%d'):
        try:
            from datetime import datetime as dt
            return dt.strptime(str(s).strip(), fmt).date()
        except: pass
    return None


def get_service_and_sheet():
    from sheets_client import get_sheets_service, get_sheet_id
    return get_sheets_service(), get_sheet_id()


# ── API: Overview ─────────────────────────────────────────────────────────────

@app.route('/api/overview')
def api_overview():
    from sheets_client import read_tab
    from pull_data import pull_config

    service, sheet_id = get_service_and_sheet()

    health_rows  = read_tab(service, sheet_id, 'Inventory_Health')
    routing_rows = read_tab(service, sheet_id, 'Replenishment_Routing')
    po_rows      = read_tab(service, sheet_id, 'PO_Tracker')
    plan_rows    = read_tab(service, sheet_id, 'Demand_Plan')
    supplier_rows= read_tab(service, sheet_id, 'Supplier_Stock')
    config       = pull_config(service, sheet_id)
    skus         = [s for s in config.get('skus',[]) if s.get('active', True)]

    active_pos = [r for r in po_rows if r.get('PO_ID') and
                  r.get('Status','').lower() not in ('received','cancelled','canceled')]

    counts = defaultdict(int)
    for r in health_rows:
        counts[r.get('Status','NO_DATA')] += 1

    health_index = {(r.get('SKU_ID',''), r.get('Warehouse','')): r for r in health_rows}

    matrix = []
    for sku in skus:
        row = {'id': sku['sku_id'], 'name': sku['sku_name'], 'cells': []}
        for wh in WAREHOUSES:
            h = health_index.get((sku['sku_id'], wh), {})
            try:
                d = float(h.get('Days_of_Stock', 0) or 0)
                if d >= 9999 or d == 0:
                    row['cells'].append({'label':'—','cls':'nd'})
                elif d < 30:
                    row['cells'].append({'label':f'{d:.0f}d','cls':'cr'})
                elif d < 90:
                    row['cells'].append({'label':f'{d:.0f}d','cls':'lw'})
                elif d > 365:
                    row['cells'].append({'label':f'{d:.0f}d','cls':'ov'})
                else:
                    row['cells'].append({'label':f'{d:.0f}d','cls':'ok'})
            except:
                row['cells'].append({'label':'—','cls':'nd'})
        matrix.append(row)

    urgent = [r for r in routing_rows if r.get('Priority') == 'URGENT']
    normal = [r for r in routing_rows if r.get('Priority') == 'NORMAL']

    return jsonify({
        'generated': datetime.now().strftime('%b %d, %Y  %I:%M %p'),
        'plan_date': plan_rows[0].get('Run_Date','Never') if plan_rows else 'Never',
        'has_data': len(plan_rows) > 0,
        'counts': dict(counts),
        'active_pos_count': len(active_pos),
        'urgent': urgent[:15],
        'normal': normal[:25],
        'active_pos': active_pos,
        'matrix': matrix,
        'wh_labels': list(WH_LABELS.values()),
        'supplier': supplier_rows,
    })


# ── API: Sales trend ──────────────────────────────────────────────────────────

@app.route('/api/sales')
def api_sales():
    from sheets_client import read_tab

    sku_filter = request.args.get('sku', 'all')
    wh_filter  = request.args.get('warehouse', 'all')
    start_str  = request.args.get('start', '')
    end_str    = request.args.get('end', '')

    service, sheet_id = get_service_and_sheet()
    sales_rows = read_tab(service, sheet_id, 'Sales_Data')

    # Parse date bounds
    start_date = parse_date(start_str) if start_str else None
    end_date   = parse_date(end_str)   if end_str   else None

    # Weekly aggregation: {week_label: {sku_id: units}}
    weekly = defaultdict(lambda: defaultdict(float))
    skus_seen = set()

    for r in sales_rows:
        d = parse_date(r.get('Date',''))
        if d is None: continue
        if start_date and d < start_date: continue
        if end_date   and d > end_date:   continue

        sku = r.get('SKU_ID','').strip()
        wh  = r.get('Warehouse','').strip()
        units = safe_float(r.get('Units_Sold', 0))

        if sku_filter != 'all' and sku != sku_filter: continue
        if wh_filter  != 'all' and wh != wh_filter:  continue

        # Week label: Monday of that week
        week_start = d - timedelta(days=d.weekday())
        week_label = week_start.strftime('%Y-%m-%d')
        weekly[week_label][sku] += units
        skus_seen.add(sku)

    # Sort weeks
    sorted_weeks = sorted(weekly.keys())
    skus_list = sorted(skus_seen)

    datasets = []
    colors = ['#2563eb','#16a34a','#d97706','#dc2626','#7c3aed','#0891b2','#db2777','#65a30d']
    for i, sku in enumerate(skus_list):
        datasets.append({
            'sku': sku,
            'data': [round(weekly[w].get(sku, 0)) for w in sorted_weeks],
            'color': colors[i % len(colors)],
        })

    # Total per week (across all SKUs)
    totals = [sum(weekly[w].values()) for w in sorted_weeks]

    return jsonify({
        'labels': sorted_weeks,
        'datasets': datasets,
        'totals': totals,
        'skus': skus_list,
    })


# ── API: Velocity comparison ──────────────────────────────────────────────────

@app.route('/api/velocity')
def api_velocity():
    from sheets_client import read_tab
    from pull_data import pull_config

    service, sheet_id = get_service_and_sheet()
    health_rows = read_tab(service, sheet_id, 'Inventory_Health')
    config      = pull_config(service, sheet_id)
    skus        = [s for s in config.get('skus',[]) if s.get('active', True)]

    wh_filter = request.args.get('warehouse', 'all')
    whs = [wh_filter] if wh_filter != 'all' else WAREHOUSES

    data = []
    for sku in skus:
        total_v = sum(
            safe_float(next(
                (r.get('Velocity_Daily',0) for r in health_rows
                 if r.get('SKU_ID')==sku['sku_id'] and r.get('Warehouse')==wh),
                0))
            for wh in whs
        )
        data.append({'name': sku['sku_name'], 'id': sku['sku_id'], 'velocity': round(total_v, 3)})

    # Also per-warehouse breakdown for the selected SKU
    sku_filter = request.args.get('sku', 'all')
    per_wh = []
    if sku_filter != 'all':
        for wh in WAREHOUSES:
            v = safe_float(next(
                (r.get('Velocity_Daily',0) for r in health_rows
                 if r.get('SKU_ID')==sku_filter and r.get('Warehouse')==wh),
                0))
            per_wh.append({'wh': WH_LABELS.get(wh, wh), 'velocity': round(v, 3)})

    return jsonify({'by_sku': data, 'by_warehouse': per_wh})


# ── API: Seasonality ──────────────────────────────────────────────────────────

@app.route('/api/seasonality')
def api_seasonality():
    from sheets_client import read_tab

    service, sheet_id = get_service_and_sheet()
    rows = read_tab(service, sheet_id, 'Seasonality_Index')

    datasets = []
    colors = ['#2563eb','#16a34a','#d97706','#dc2626','#7c3aed','#0891b2','#db2777','#65a30d']
    for i, r in enumerate(rows):
        if not r.get('SKU_ID'): continue
        datasets.append({
            'name': r.get('SKU_Name', r.get('SKU_ID','')),
            'data': [safe_float(r.get(m, 1.0)) for m in MONTHS],
            'color': colors[i % len(colors)],
        })

    return jsonify({'labels': MONTHS, 'datasets': datasets})


# ── API: Warehouse comparison ─────────────────────────────────────────────────

@app.route('/api/warehouse-comparison')
def api_warehouse_comparison():
    from sheets_client import read_tab
    from pull_data import pull_config

    service, sheet_id = get_service_and_sheet()
    health_rows = read_tab(service, sheet_id, 'Inventory_Health')
    stock_rows  = read_tab(service, sheet_id, 'Current_Stock')
    config      = pull_config(service, sheet_id)
    skus        = [s for s in config.get('skus',[]) if s.get('active', True)]

    sku_filter = request.args.get('sku', skus[0]['sku_id'] if skus else 'all')

    # Days of stock per warehouse for selected SKU
    days_per_wh = []
    stock_per_wh = []
    health_index = {(r.get('SKU_ID',''), r.get('Warehouse','')): r for r in health_rows}
    stock_index  = {}
    for r in stock_rows:
        if r.get('SKU_ID') == sku_filter:
            stock_index = r
            break

    for wh in WAREHOUSES:
        h = health_index.get((sku_filter, wh), {})
        d = safe_float(h.get('Days_of_Stock', 0))
        days_per_wh.append({'wh': WH_LABELS.get(wh,wh), 'days': round(d, 1) if d < 9999 else 0})
        stock_per_wh.append({'wh': WH_LABELS.get(wh,wh), 'units': safe_int(stock_index.get(wh, 0))})

    # All SKUs at a specific warehouse
    wh_filter = request.args.get('warehouse', WAREHOUSES[0])
    days_per_sku = []
    for sku in skus:
        h = health_index.get((sku['sku_id'], wh_filter), {})
        d = safe_float(h.get('Days_of_Stock', 0))
        days_per_sku.append({'sku': sku['sku_name'], 'days': round(d,1) if d < 9999 else 0})

    return jsonify({
        'sku': sku_filter,
        'sku_name': next((s['sku_name'] for s in skus if s['sku_id']==sku_filter), sku_filter),
        'days_per_wh': days_per_wh,
        'stock_per_wh': stock_per_wh,
        'days_per_sku': days_per_sku,
        'wh_filter': WH_LABELS.get(wh_filter, wh_filter),
        'skus': [{'id':s['sku_id'],'name':s['sku_name']} for s in skus],
        'warehouses': [{'id':wh,'label':WH_LABELS[wh]} for wh in WAREHOUSES],
    })


# ── API: Action plan ──────────────────────────────────────────────────────────

@app.route('/api/action-plan')
def api_action_plan():
    from sheets_client import read_tab

    service, sheet_id = get_service_and_sheet()
    routing_rows = read_tab(service, sheet_id, 'Replenishment_Routing')
    calc_rows    = read_tab(service, sheet_id, 'Calculation_Log')
    po_rows      = read_tab(service, sheet_id, 'PO_Tracker')

    active_pos = [r for r in po_rows if r.get('PO_ID') and
                  r.get('Status','').lower() not in ('received','cancelled','canceled')]

    # Index calc log for math lookup
    calc_index = {}
    for r in calc_rows:
        key = (r.get('SKU_ID',''), r.get('Warehouse',''))
        calc_index[key] = r

    # Enrich routing with calc details
    enriched = []
    for r in routing_rows:
        key = (r.get('SKU_ID',''), r.get('Destination',''))
        calc = calc_index.get(key, {})
        enriched.append({
            **r,
            'math': {
                'current_stock': safe_int(calc.get('Current_Stock', 0)),
                'in_transit': safe_int(calc.get('In_Transit', 0)),
                'velocity_90d': safe_float(calc.get('Velocity_90d', 0)),
                'seasonality': safe_float(calc.get('Seasonality_Factor', 1)),
                'adj_velocity': safe_float(calc.get('Adjusted_Velocity', 0)),
                'days_of_stock': safe_float(calc.get('Days_of_Stock', 0)),
                'target_days': safe_int(calc.get('Target_Days', 90)),
                'gap_days': safe_float(calc.get('Gap_Days', 0)),
                'units_needed': safe_int(calc.get('Units_Needed', 0)),
                'lead_time': safe_int(calc.get('Lead_Time_Days', 0)),
                'notes': calc.get('Calculation_Notes', ''),
            }
        })

    urgent = [r for r in enriched if r.get('Priority') == 'URGENT']
    normal = [r for r in enriched if r.get('Priority') == 'NORMAL']

    return jsonify({
        'urgent': urgent,
        'normal': normal,
        'active_pos': active_pos,
        'total_actions': len(enriched),
    })


# ── API: Year-ahead plan ──────────────────────────────────────────────────────

@app.route('/api/annual-plan')
def api_annual_plan():
    from sheets_client import read_tab

    service, sheet_id = get_service_and_sheet()
    rows = read_tab(service, sheet_id, 'Annual_Plan')

    print_runs = [r for r in rows if r.get('Action_Type', '') == 'New PO (Print Run)']
    distribution = [r for r in rows if r.get('Action_Type', '') != 'New PO (Print Run)']

    STATUS_ORDER = {'OVERDUE': 0, 'URGENT': 1, 'PLAN NOW': 2, 'UPCOMING': 3}
    distribution.sort(key=lambda r: (STATUS_ORDER.get(r.get('Status', ''), 9), r.get('Action_Deadline', '')))
    print_runs.sort(key=lambda r: (STATUS_ORDER.get(r.get('Status', ''), 9), r.get('Action_Deadline', '')))

    counts = defaultdict(int)
    for r in distribution:
        counts[r.get('Status', 'UNKNOWN')] += 1

    generated = rows[0].get('Run_Date', '') if rows else ''

    return jsonify({
        'generated': generated,
        'print_runs': print_runs,
        'distribution': distribution,
        'counts': dict(counts),
        'total': len(rows),
    })


# ── API: SKU list helper ──────────────────────────────────────────────────────

@app.route('/api/skus')
def api_skus():
    from pull_data import pull_config
    from sheets_client import get_sheet_id
    service, sheet_id = get_service_and_sheet()
    config = pull_config(service, sheet_id)
    skus = [s for s in config.get('skus',[]) if s.get('active', True)]
    return jsonify({
        'skus': [{'id':s['sku_id'],'name':s['sku_name']} for s in skus],
        'warehouses': [{'id':wh,'label':WH_LABELS[wh]} for wh in WAREHOUSES],
    })


# ── Main routes ───────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
