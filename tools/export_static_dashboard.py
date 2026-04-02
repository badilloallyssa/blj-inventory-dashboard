#!/usr/bin/env python3
"""
Export a self-contained static HTML dashboard to docs/index.html for GitHub Pages.

Usage:
    python3 tools/export_static_dashboard.py

Output:
    docs/index.html  — single file, no server required
    docs/.nojekyll   — prevents Jekyll processing on GitHub Pages
"""

import os
import sys
import json
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

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


def build_static_data():
    from sheets_client import get_sheets_service, get_sheet_id, read_tab
    from pull_data import pull_config

    print("Connecting to Google Sheets...")
    service  = get_sheets_service()
    sheet_id = get_sheet_id()

    print("Pulling all tabs...")
    health_rows   = read_tab(service, sheet_id, 'Inventory_Health')
    routing_rows  = read_tab(service, sheet_id, 'Replenishment_Routing')
    po_rows       = read_tab(service, sheet_id, 'PO_Tracker')
    plan_rows     = read_tab(service, sheet_id, 'Demand_Plan')
    supplier_rows = read_tab(service, sheet_id, 'Supplier_Stock')
    sales_rows    = read_tab(service, sheet_id, 'Sales_Data')
    stock_rows    = read_tab(service, sheet_id, 'Current_Stock')
    seas_rows     = read_tab(service, sheet_id, 'Seasonality_Index')
    calc_rows     = read_tab(service, sheet_id, 'Calculation_Log')
    annual_rows   = read_tab(service, sheet_id, 'Annual_Plan')
    config        = pull_config(service, sheet_id)

    skus = [s for s in config.get('skus', []) if s.get('active', True)]

    # ── Overview ─────────────────────────────────────────────────────────────
    active_pos = [r for r in po_rows if r.get('PO_ID') and
                  r.get('Status', '').lower() not in ('received', 'cancelled', 'canceled')]

    health_counts = defaultdict(int)
    for r in health_rows:
        health_counts[r.get('Status', 'NO_DATA')] += 1

    health_index = {(r.get('SKU_ID', ''), r.get('Warehouse', '')): r for r in health_rows}

    matrix = []
    for sku in skus:
        row = {'id': sku['sku_id'], 'name': sku['sku_name'], 'cells': []}
        for wh in WAREHOUSES:
            h = health_index.get((sku['sku_id'], wh), {})
            try:
                d = float(h.get('Days_of_Stock', 0) or 0)
                if d >= 9999 or d == 0:
                    row['cells'].append({'label': '—', 'cls': 'nd'})
                elif d < 30:
                    row['cells'].append({'label': f'{d:.0f}d', 'cls': 'cr'})
                elif d < 90:
                    row['cells'].append({'label': f'{d:.0f}d', 'cls': 'lw'})
                elif d > 365:
                    row['cells'].append({'label': f'{d:.0f}d', 'cls': 'ov'})
                else:
                    row['cells'].append({'label': f'{d:.0f}d', 'cls': 'ok'})
            except Exception:
                row['cells'].append({'label': '—', 'cls': 'nd'})
        matrix.append(row)

    overview = {
        'generated': datetime.now().strftime('%b %d, %Y  %I:%M %p') + ' (snapshot)',
        'plan_date': plan_rows[0].get('Run_Date', 'Never') if plan_rows else 'Never',
        'has_data': len(plan_rows) > 0,
        'counts': dict(health_counts),
        'active_pos_count': len(active_pos),
        'urgent': [r for r in routing_rows if r.get('Priority') == 'URGENT'][:15],
        'normal': [r for r in routing_rows if r.get('Priority') == 'NORMAL'][:25],
        'active_pos': active_pos,
        'matrix': matrix,
        'wh_labels': list(WH_LABELS.values()),
        'supplier': supplier_rows,
    }

    # ── Seasonality ──────────────────────────────────────────────────────────
    colors = ['#2563eb', '#16a34a', '#d97706', '#dc2626', '#7c3aed', '#0891b2', '#db2777', '#65a30d']
    seas_datasets = []
    for i, r in enumerate(seas_rows):
        if not r.get('SKU_ID'):
            continue
        seas_datasets.append({
            'name': r.get('SKU_Name', r.get('SKU_ID', '')),
            'data': [safe_float(r.get(m, 1.0)) for m in MONTHS],
            'color': colors[i % len(colors)],
        })
    seasonality = {'labels': MONTHS, 'datasets': seas_datasets}

    # ── Action Plan ──────────────────────────────────────────────────────────
    calc_index = {}
    for r in calc_rows:
        key = (r.get('SKU_ID', ''), r.get('Warehouse', ''))
        calc_index[key] = r

    enriched = []
    for r in routing_rows:
        key = (r.get('SKU_ID', ''), r.get('Destination', ''))
        calc = calc_index.get(key, {})
        enriched.append({
            **r,
            'math': {
                'current_stock': safe_int(calc.get('Current_Stock', 0)),
                'in_transit':    safe_int(calc.get('In_Transit', 0)),
                'velocity_90d':  safe_float(calc.get('Velocity_90d', 0)),
                'seasonality':   safe_float(calc.get('Seasonality_Factor', 1)),
                'adj_velocity':  safe_float(calc.get('Adjusted_Velocity', 0)),
                'days_of_stock': safe_float(calc.get('Days_of_Stock', 0)),
                'target_days':   safe_int(calc.get('Target_Days', 90)),
                'gap_days':      safe_float(calc.get('Gap_Days', 0)),
                'units_needed':  safe_int(calc.get('Units_Needed', 0)),
                'lead_time':     safe_int(calc.get('Lead_Time_Days', 0)),
                'notes':         calc.get('Calculation_Notes', ''),
            }
        })

    action_plan = {
        'urgent':       [r for r in enriched if r.get('Priority') == 'URGENT'],
        'normal':       [r for r in enriched if r.get('Priority') == 'NORMAL'],
        'active_pos':   active_pos,
        'total_actions': len(enriched),
    }

    # ── Annual Plan ──────────────────────────────────────────────────────────
    STATUS_ORDER = {'OVERDUE': 0, 'URGENT': 1, 'PLAN NOW': 2, 'UPCOMING': 3}
    print_runs   = [r for r in annual_rows if r.get('Action_Type', '') == 'New PO (Print Run)']
    distribution = [r for r in annual_rows if r.get('Action_Type', '') != 'New PO (Print Run)']
    distribution.sort(key=lambda r: (STATUS_ORDER.get(r.get('Status', ''), 9), r.get('Action_Deadline', '')))
    print_runs.sort(  key=lambda r: (STATUS_ORDER.get(r.get('Status', ''), 9), r.get('Action_Deadline', '')))
    annual_counts = defaultdict(int)
    for r in distribution:
        annual_counts[r.get('Status', 'UNKNOWN')] += 1

    annual_plan = {
        'generated':   annual_rows[0].get('Run_Date', '') if annual_rows else '',
        'print_runs':  print_runs,
        'distribution': distribution,
        'counts':      dict(annual_counts),
        'total':       len(annual_rows),
    }

    # ── Transfer Plan — seasonality-aware quarterly simulation ───────────────
    import calendar as _cal
    from datetime import date as _date, timedelta as _td

    _MONTH_ABBR = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    _US_WH = ['SLI', 'HBG', 'SAV', 'KCM']
    _TODAY = _date.today()

    # Read velocity + seasonality + data from .tmp/ files (fresh, not from sheet)
    import json as _json
    _vel_raw  = _json.load(open(os.path.join(PROJECT_ROOT, '.tmp/velocity.json')))
    _sea_raw  = _json.load(open(os.path.join(PROJECT_ROOT, '.tmp/seasonality.json')))
    _data_raw = _json.load(open(os.path.join(PROJECT_ROOT, '.tmp/data.json')))
    _vel      = _vel_raw.get('velocity', {})
    _sea_idx  = _sea_raw.get('indices', {})

    _stock_idx = {e['sku_id']: {k: float(v) for k, v in e['stock'].items()}
                  for e in _data_raw.get('current_stock', [])}
    _sku_names = {s['sku_id']: s['sku_name'] for s in _data_raw.get('config', {}).get('skus', [])}
    _pos       = _data_raw.get('pos', [])

    def _sea(sku_id, month_num):
        return float(_sea_idx.get(sku_id, {}).get(_MONTH_ABBR[month_num - 1], 1.0))

    def _q_demand(sku_id, wh, months, year):
        v90 = _vel.get(sku_id, {}).get(wh, {}).get('v90', 0.0)
        if wh == 'Amazon_CA_FBA' and v90 == 0:
            v90 = _vel.get(sku_id, {}).get('CA', {}).get('v90', 0.0)
        if v90 == 0:
            return 0.0, 0.0
        total = sum(v90 * _sea(sku_id, m) * _cal.monthrange(year, m)[1] for m in months)
        return total, v90

    def _source_and_lead(wh, sku_id, cur_stocks):
        stk = cur_stocks.get(sku_id, {})
        if wh == 'Amazon_US_FBA':
            best = max(_US_WH, key=lambda w: stk.get(w, 0))
            if stk.get(best, 0) > 50:
                return best, 21, 'Transfer'
            return 'China_Supplier', 45, 'New PO'
        if wh == 'Amazon_CA_FBA':
            if stk.get('CA', 0) > 50:
                return 'CA', 21, 'Transfer'
            return 'Canada_Supplier', 21, 'New PO'
        if wh in _US_WH:
            best = max([w for w in _US_WH if w != wh], key=lambda w: stk.get(w, 0))
            if stk.get(best, 0) > 100:
                return best, 7, 'Transfer'
            return 'China_Supplier', 45, 'New PO'
        if wh == 'EU':
            return ('UK', 21, 'Transfer') if stk.get('UK', 0) > 200 else ('China_Supplier', 75, 'New PO')
        if wh == 'UK':
            return ('EU', 21, 'Transfer') if stk.get('EU', 0) > 200 else ('China_Supplier', 75, 'New PO')
        if wh == 'AU':
            if stk.get('UK', 0) > 200: return 'UK', 60, 'Transfer'
            if stk.get('EU', 0) > 200: return 'EU', 60, 'Transfer'
            return 'China_Supplier', 45, 'New PO'
        if wh == 'CA':
            return 'Canada_Supplier', 14, 'New PO'
        return 'China_Supplier', 60, 'New PO'

    # Running stock — starts at current stock + in-transit POs
    _run_stk = {sid: dict(whs) for sid, whs in _stock_idx.items()}
    for _po in _pos:
        _sid, _dst = _po['sku_id'], _po['destination']
        if not any(s in _po.get('status', '').lower()
                   for s in ('ordered', 'in production', 'shipped', 'in transit',
                              'in-transit', 'pending')):
            continue
        if _sid in _run_stk and _dst in _run_stk[_sid]:
            _run_stk[_sid][_dst] = _run_stk[_sid].get(_dst, 0) + float(_po.get('qty_ordered', 0))

    _QUARTERS = [
        {'name': 'Q2', 'months': [4, 5, 6],   'year': 2026, 'label': 'Q2 — Apr / May / Jun'},
        {'name': 'Q3', 'months': [7, 8, 9],   'year': 2026, 'label': 'Q3 — Jul / Aug / Sep'},
        {'name': 'Q4', 'months': [10, 11, 12],'year': 2026, 'label': 'Q4 — Oct / Nov / Dec (BFCM)'},
    ]
    _STATUS_O = {'OVERDUE': 0, 'URGENT': 1, 'PLAN NOW': 2, 'UPCOMING': 3}

    _tp_results = {q['name']: defaultdict(list) for q in _QUARTERS}
    _tp_totals  = {}

    for _sku_id, _wh_stk in _stock_idx.items():
        _sku_name = _sku_names.get(_sku_id, _sku_id)
        for _wh in WAREHOUSES:
            for _q in _QUARTERS:
                _qname   = _q['name']
                _months  = _q['months']
                _year    = _q['year']

                _qdem, _v90 = _q_demand(_sku_id, _wh, _months, _year)
                if _v90 == 0:
                    continue

                _cur = _run_stk.get(_sku_id, {}).get(_wh, 0.0)

                # Safety stock = 90 days × PEAK-month velocity in this quarter
                # (ensures we're ready for the busiest month, not just average)
                _peak_sea     = max(_sea(_sku_id, m) for m in _months)
                _safety_stock = 90 * _v90 * _peak_sea

                _needed = _qdem + _safety_stock
                _units  = max(0, int(round(_needed - _cur)))

                if _units > 0:
                    _src, _lt, _atype = _source_and_lead(_wh, _sku_id, _run_stk)
                    _q_start   = _date(_year, _months[0], 1)
                    _deadline  = _q_start - _td(days=_lt)
                    _days_till = (_deadline - _TODAY).days
                    _status    = ('OVERDUE'   if _days_till < 0  else
                                  'URGENT'    if _days_till <= 30 else
                                  'PLAN NOW'  if _days_till <= 90 else 'UPCOMING')

                    _tp_results[_qname][_wh].append({
                        'sku_name':        _sku_name,
                        'sku_id':          _sku_id,
                        'warehouse':       _wh,
                        'action_type':     _atype,
                        'source':          _src,
                        'units_needed':    _units,
                        'q_demand':        int(round(_qdem)),
                        'safety_stock':    int(round(_safety_stock)),
                        'current_stock':   int(_cur),
                        'peak_sea':        round(_peak_sea, 2),
                        'action_deadline': _deadline.strftime('%Y-%m-%d'),
                        'days_until':      _days_till,
                        'status':          _status,
                        'lead_time':       _lt,
                    })

                # Carry forward: deduct quarter demand, add transfer
                _run_stk.setdefault(_sku_id, {})[_wh] = max(0.0, _cur - _qdem) + _units

    for _q in _QUARTERS:
        _qname = _q['name']
        for _wh in _tp_results[_qname]:
            _tp_results[_qname][_wh].sort(
                key=lambda x: (_STATUS_O.get(x['status'], 9), x['action_deadline']))
        _tp_totals[_qname] = sum(len(v) for v in _tp_results[_qname].values())

    transfer_plan = {
        'generated':         _TODAY.strftime('%Y-%m-%d'),
        'print_runs_needed': len(print_runs) > 0,
        'print_runs':        print_runs,
        'totals':            _tp_totals,
        'Q2': {'label': _QUARTERS[0]['label'], 'by_warehouse': {wh: items for wh, items in _tp_results['Q2'].items()}},
        'Q3': {'label': _QUARTERS[1]['label'], 'by_warehouse': {wh: items for wh, items in _tp_results['Q3'].items()}},
        'Q4': {'label': _QUARTERS[2]['label'], 'by_warehouse': {wh: items for wh, items in _tp_results['Q4'].items()}},
    }

    # ── SKUs ─────────────────────────────────────────────────────────────────
    skus_data = {
        'skus':       [{'id': s['sku_id'], 'name': s['sku_name']} for s in skus],
        'warehouses': [{'id': wh, 'label': WH_LABELS[wh]} for wh in WAREHOUSES],
    }

    return {
        'overview':    overview,
        'seasonality': seasonality,
        'action_plan': action_plan,
        'annual_plan': annual_plan,
        'skus':        skus_data,
        # Raw rows — used by JS-side computed endpoints
        'sales_raw':  sales_rows,
        'health_raw': health_rows,
        'stock_raw':  stock_rows,
        'skus_list':  [{'id': s['sku_id'], 'name': s['sku_name']} for s in skus],
        'transfer_plan': transfer_plan,
    }


# ── Client-side fetch() interceptor ──────────────────────────────────────────
INTERCEPTOR_JS = r"""
(function(){
  var SD = window.STATIC_DATA;
  var WAREHOUSES = ['SLI','HBG','SAV','KCM','EU','CA','AU','UK','Amazon_US_FBA','Amazon_CA_FBA'];
  var WH_LABELS  = {SLI:'SLI',HBG:'HBG',SAV:'SAV',KCM:'KCM',EU:'EU',CA:'CA',
                    AU:'AU',UK:'UK',Amazon_US_FBA:'FBA US',Amazon_CA_FBA:'FBA CA'};

  function sfloat(v){ return parseFloat(v||0)||0; }
  function sint(v){ return Math.round(sfloat(v)); }

  /* /api/sales — filter + weekly-aggregate raw sales rows */
  function computeSales(p){
    var skuF=p.get('sku')||'all', whF=p.get('warehouse')||'all';
    var startD=p.get('start')?new Date(p.get('start')):null;
    var endD  =p.get('end')  ?new Date(p.get('end'))  :null;
    var weekly={}, skusSeen=new Set();
    for(var i=0;i<SD.sales_raw.length;i++){
      var r=SD.sales_raw[i];
      var d=r.Date?new Date(r.Date):null;
      if(!d||isNaN(d)) continue;
      if(startD&&d<startD) continue;
      if(endD  &&d>endD)   continue;
      var sku=(r.SKU_ID||'').trim(), wh=(r.Warehouse||'').trim();
      var units=sfloat(r.Units_Sold);
      if(skuF!=='all'&&sku!==skuF) continue;
      if(whF !=='all'&&wh !==whF)  continue;
      var day=d.getDay(), diff=(day===0)?-6:1-day;
      var mon=new Date(d); mon.setDate(d.getDate()+diff);
      var wl=mon.toISOString().split('T')[0];
      if(!weekly[wl]) weekly[wl]={};
      weekly[wl][sku]=(weekly[wl][sku]||0)+units;
      skusSeen.add(sku);
    }
    var weeks=Object.keys(weekly).sort();
    var skusList=[...skusSeen].sort();
    var colors=['#2563eb','#16a34a','#d97706','#dc2626','#7c3aed','#0891b2','#db2777','#65a30d'];
    var datasets=skusList.map(function(s,i){
      return {sku:s,data:weeks.map(function(w){return Math.round(weekly[w][s]||0);}),color:colors[i%colors.length]};
    });
    var totals=weeks.map(function(w){return Object.values(weekly[w]).reduce(function(a,b){return a+b;},0);});
    return {labels:weeks,datasets:datasets,totals:totals,skus:skusList};
  }

  /* /api/velocity — aggregate from health_raw */
  function computeVelocity(p){
    var whF=p.get('warehouse')||'all', skuF=p.get('sku')||'all';
    var whs=whF!=='all'?[whF]:WAREHOUSES;
    var bySkuMap={};
    for(var i=0;i<SD.health_raw.length;i++){
      var r=SD.health_raw[i];
      if(whs.indexOf(r.Warehouse)<0) continue;
      bySkuMap[r.SKU_ID]=(bySkuMap[r.SKU_ID]||0)+sfloat(r.Velocity_Daily);
    }
    var bySkuArr=SD.skus_list.map(function(s){
      return {name:s.name,id:s.id,velocity:Math.round((bySkuMap[s.id]||0)*1000)/1000};
    });
    var perWH=[];
    if(skuF!=='all'){
      perWH=WAREHOUSES.map(function(wh){
        var row=null;
        for(var i=0;i<SD.health_raw.length;i++){
          if(SD.health_raw[i].SKU_ID===skuF&&SD.health_raw[i].Warehouse===wh){row=SD.health_raw[i];break;}
        }
        return {wh:WH_LABELS[wh]||wh,velocity:row?Math.round(sfloat(row.Velocity_Daily)*1000)/1000:0};
      });
    }
    return {by_sku:bySkuArr,by_warehouse:perWH};
  }

  /* /api/warehouse-comparison — from health_raw + stock_raw */
  function computeWHComp(p){
    var skuF=p.get('sku')||(SD.skus_list[0]?SD.skus_list[0].id:'');
    var whF =p.get('warehouse')||WAREHOUSES[0];
    var skuName=(SD.skus_list.filter(function(s){return s.id===skuF;})[0]||{}).name||skuF;

    var daysPerWH=WAREHOUSES.map(function(wh){
      var h=null;
      for(var i=0;i<SD.health_raw.length;i++){
        if(SD.health_raw[i].SKU_ID===skuF&&SD.health_raw[i].Warehouse===wh){h=SD.health_raw[i];break;}
      }
      var d=h?sfloat(h.Days_of_Stock):0;
      return {wh:WH_LABELS[wh]||wh,days:d<9999?Math.round(d*10)/10:0};
    });

    var stockRow=null;
    for(var i=0;i<SD.stock_raw.length;i++){if(SD.stock_raw[i].SKU_ID===skuF){stockRow=SD.stock_raw[i];break;}}
    var stockPerWH=WAREHOUSES.map(function(wh){
      return {wh:WH_LABELS[wh]||wh,units:sint(stockRow?stockRow[wh]||0:0)};
    });

    var daysPerSKU=SD.skus_list.map(function(s){
      var h=null;
      for(var i=0;i<SD.health_raw.length;i++){
        if(SD.health_raw[i].SKU_ID===s.id&&SD.health_raw[i].Warehouse===whF){h=SD.health_raw[i];break;}
      }
      var d=h?sfloat(h.Days_of_Stock):0;
      return {sku:s.name,days:d<9999?Math.round(d*10)/10:0};
    });

    return {
      sku:skuF,sku_name:skuName,
      days_per_wh:daysPerWH,stock_per_wh:stockPerWH,days_per_sku:daysPerSKU,
      wh_filter:WH_LABELS[whF]||whF,
      skus:SD.skus_list,
      warehouses:WAREHOUSES.map(function(wh){return {id:wh,label:WH_LABELS[wh]||wh};})
    };
  }

  function fakeResp(data){
    return Promise.resolve({ok:true,json:function(){return Promise.resolve(data);},text:function(){return Promise.resolve(JSON.stringify(data));}});
  }

  var _nativeFetch=window.fetch;
  window.fetch=function(url,opts){
    if(typeof url!=='string'||url.indexOf('/api/')!==0) return _nativeFetch(url,opts);
    var qi=url.indexOf('?');
    var path=qi>=0?url.slice(0,qi):url;
    var params=new URLSearchParams(qi>=0?url.slice(qi+1):'');
    if(path==='/api/overview')             return fakeResp(SD.overview);
    if(path==='/api/skus')                 return fakeResp(SD.skus);
    if(path==='/api/seasonality')          return fakeResp(SD.seasonality);
    if(path==='/api/action-plan')          return fakeResp(SD.action_plan);
    if(path==='/api/annual-plan')          return fakeResp(SD.annual_plan);
    if(path==='/api/transfer-plan')        return fakeResp(SD.transfer_plan);
    if(path==='/api/sales')                return fakeResp(computeSales(params));
    if(path==='/api/velocity')             return fakeResp(computeVelocity(params));
    if(path==='/api/warehouse-comparison') return fakeResp(computeWHComp(params));
    return _nativeFetch(url,opts);
  };
})();
"""


def inject_static_script(html, static_data_json):
    """Inject STATIC_DATA + interceptor just before </head>."""
    script_block = (
        f'<script>\n'
        f'// Static snapshot — generated {datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
        f'window.STATIC_DATA = {static_data_json};\n'
        f'{INTERCEPTOR_JS}\n'
        f'</script>\n'
    )
    if '</head>' in html:
        return html.replace('</head>', script_block + '</head>', 1)
    # Fallback: inject before first <script> in body
    return html.replace('<script>', script_block + '<script>', 1)


def main():
    print("Building static data from Google Sheets...")
    static_data = build_static_data()

    print("Serialising JSON...")
    static_data_json = json.dumps(static_data, ensure_ascii=False, default=str)

    template_path = os.path.join(PROJECT_ROOT, 'dashboard', 'templates', 'dashboard.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    html = inject_static_script(html, static_data_json)

    # Replace live indicator with static snapshot label
    html = html.replace(
        '<span><div class="dot-live"></div> Live</span>',
        '<span style="color:var(--muted)">Static snapshot</span>'
    )

    docs_dir = os.path.join(PROJECT_ROOT, 'docs')
    os.makedirs(docs_dir, exist_ok=True)

    out_path = os.path.join(docs_dir, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    nojekyll = os.path.join(docs_dir, '.nojekyll')
    if not os.path.exists(nojekyll):
        open(nojekyll, 'w').close()

    size_kb = os.path.getsize(out_path) / 1024
    print(f"\n✓ docs/index.html  ({size_kb:.0f} KB)")
    print(f"✓ docs/.nojekyll")
    print(f"\nNext steps:")
    print(f"  1. git add docs/ && git commit -m 'chore: export static dashboard'")
    print(f"  2. git push")
    print(f"  3. GitHub → Settings → Pages → Source: main / docs")


if __name__ == '__main__':
    main()
