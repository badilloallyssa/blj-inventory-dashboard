"""
Generate a self-contained HTML dashboard from live Google Sheets data.
Opens automatically in your default browser when done.

Usage:
    python tools/generate_dashboard.py
    python tools/generate_dashboard.py --output dashboard.html  # custom output path
    python tools/generate_dashboard.py --no-open               # don't auto-open browser
"""
import sys
import os
import json
import argparse
import webbrowser
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))


def get_dashboard_data():
    from sheets_client import get_sheets_service, get_sheet_id, read_tab
    from pull_data import pull_config

    service = get_sheets_service()
    sheet_id = get_sheet_id()

    WAREHOUSES = ['SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA']
    WH_LABELS  = ['SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'FBA US', 'FBA CA']

    def safe_float(v):
        try: return float(v or 0)
        except: return 0.0

    def safe_int(v):
        try: return int(float(v or 0))
        except: return 0

    print("  Pulling health data...")
    health_rows = read_tab(service, sheet_id, 'Inventory_Health')
    health_index = {(r.get('SKU_ID',''), r.get('Warehouse','')): r for r in health_rows}

    print("  Pulling demand plan...")
    plan_rows = read_tab(service, sheet_id, 'Demand_Plan')

    print("  Pulling routing...")
    routing_rows = read_tab(service, sheet_id, 'Replenishment_Routing')

    print("  Pulling PO tracker...")
    po_rows = read_tab(service, sheet_id, 'PO_Tracker')
    active_pos = [r for r in po_rows if r.get('PO_ID') and
                  r.get('Status','').lower() not in ('received','cancelled','canceled')]

    print("  Pulling supplier stock...")
    supplier_rows = read_tab(service, sheet_id, 'Supplier_Stock')

    print("  Pulling config...")
    config = pull_config(service, sheet_id)
    skus = [s for s in config.get('skus', []) if s.get('active', True)]

    # Summary counts
    counts = defaultdict(int)
    for r in health_rows:
        counts[r.get('Status', 'NO_DATA')] += 1

    # Action points
    urgent  = [r for r in routing_rows if r.get('Priority') == 'URGENT']
    normal  = [r for r in routing_rows if r.get('Priority') == 'NORMAL']

    # Health matrix
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
            except:
                row['cells'].append({'label': '—', 'cls': 'nd'})
        matrix.append(row)

    # Velocity chart
    velocity = []
    for sku in skus:
        total = sum(
            safe_float(health_index.get((sku['sku_id'], wh), {}).get('Velocity_Daily', 0))
            for wh in WAREHOUSES
        )
        velocity.append({'name': sku['sku_name'], 'v': round(total, 2)})

    return {
        'generated': datetime.now().strftime('%B %d, %Y  %I:%M %p'),
        'plan_date': plan_rows[0].get('Run_Date', 'Not yet run') if plan_rows else 'Not yet run',
        'has_data': len(plan_rows) > 0,
        'counts': dict(counts),
        'active_pos_count': len(active_pos),
        'urgent': urgent[:15],
        'normal': normal[:25],
        'active_pos': active_pos,
        'matrix': matrix,
        'wh_labels': WH_LABELS,
        'velocity': velocity,
        'supplier': supplier_rows,
    }


def render_html(d):
    # Serialize data for JS
    js_velocity_labels = json.dumps([v['name'] for v in d['velocity']])
    js_velocity_values = json.dumps([v['v'] for v in d['velocity']])

    def action_badge(action_type):
        t = (action_type or '').lower()
        if 'transfer' in t: return '<span class="badge b-tr">Transfer</span>'
        if 'awd' in t:      return '<span class="badge b-aw">AWD</span>'
        return '<span class="badge b-po">New PO</span>'

    def status_pill(status):
        s = (status or '').lower()
        if 'ship' in s:       return f'<span class="pill p-sh">{status}</span>'
        if 'transit' in s:    return f'<span class="pill p-tr">{status}</span>'
        if 'production' in s: return f'<span class="pill p-pr">{status}</span>'
        return f'<span class="pill p-or">{status}</span>'

    def urgent_rows():
        if not d['urgent']:
            return '<div class="empty">No urgent actions — all critical items are covered.</div>'
        rows = ''
        for r in d['urgent']:
            rows += f"""
            <div class="arow">
              <div class="adot cr-dot"></div>
              <div class="amain">
                <div class="asku">{r.get('SKU_Name','')} → {r.get('Destination','')}</div>
                <div class="adet">{action_badge(r.get('Action_Type',''))} from {r.get('Recommended_Source','')} &middot; {r.get('Lead_Time_Days','')}d lead time</div>
              </div>
              <div class="ameta">
                <div class="adeadline">By {r.get('Order_Deadline','')}</div>
                <div class="aqty">{r.get('Units_Needed','')} units</div>
              </div>
            </div>"""
        return rows

    def normal_rows():
        if not d['normal']:
            return '<div class="empty">No replenishment needed right now.</div>'
        rows = ''
        for r in d['normal']:
            rows += f"""
            <div class="arow">
              <div class="adot lw-dot"></div>
              <div class="amain">
                <div class="asku">{r.get('SKU_Name','')} → {r.get('Destination','')}</div>
                <div class="adet">{action_badge(r.get('Action_Type',''))} from {r.get('Recommended_Source','')} &middot; {r.get('Days_of_Stock','')} days left</div>
              </div>
              <div class="ameta">
                <div class="adeadline" style="color:#d97706">By {r.get('Order_Deadline','')}</div>
                <div class="aqty">{r.get('Units_Needed','')} units</div>
              </div>
            </div>"""
        return rows

    def po_rows():
        if not d['active_pos']:
            return '<tr><td colspan="6" style="text-align:center;color:#9ca3af;padding:24px">No active POs or transfers.</td></tr>'
        rows = ''
        for r in d['active_pos']:
            rows += f"""
            <tr>
              <td><strong>{r.get('PO_ID','')}</strong></td>
              <td>{r.get('SKU_Name','')}</td>
              <td>{r.get('Qty_Ordered','')}</td>
              <td style="color:#6b7280">{r.get('Origin','')} → {r.get('Destination','')}</td>
              <td>{r.get('Expected_Arrival','')}</td>
              <td>{status_pill(r.get('Status',''))}</td>
            </tr>"""
        return rows

    def matrix_rows():
        rows = ''
        for row in d['matrix']:
            cells = ''.join(
                f'<td><span class="mc {c["cls"]}">{c["label"]}</span></td>'
                for c in row['cells']
            )
            rows += f'<tr><td class="sku-col">{row["name"]}</td>{cells}</tr>'
        return rows

    def supplier_cards():
        if not d['supplier']:
            return '<p style="color:#9ca3af;padding:16px">No supplier stock data.</p>'
        cards = ''
        for r in d['supplier']:
            cards += f"""
            <div class="sc">
              <div class="sc-name">{r.get('SKU_Name','')}</div>
              <div class="sc-row"><span>China</span><span>{int(float(r.get('China_Supplier',0) or 0))}</span></div>
              <div class="sc-row"><span>Canada</span><span>{int(float(r.get('Canada_Supplier',0) or 0))}</span></div>
            </div>"""
        return cards

    c = d['counts']
    no_data_msg = ''
    if not d['has_data']:
        no_data_msg = '''
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:28px;text-align:center;margin-bottom:24px">
          <p style="font-size:16px;font-weight:600;margin-bottom:6px">No plan data yet</p>
          <p style="color:#6b7280;font-size:14px">Add data to Sales_Data and Current_Stock tabs, then ask Claude to run the demand plan.</p>
        </div>'''

    wh_headers = ''.join(f'<th>{wh}</th>' for wh in d['wh_labels'])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Inventory Dashboard — Big Life Journal</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#f8f7f4;--card:#fff;--border:#e8e3db;--muted:#6b6560;--cr:#dc2626;--cr-bg:#fef2f2;--lw:#d97706;--lw-bg:#fffbeb;--ok:#16a34a;--ok-bg:#f0fdf4;--ov:#7c3aed;--ov-bg:#faf5ff;--blue:#2563eb;--r:12px;--sh:0 1px 3px rgba(0,0,0,.07),0 2px 8px rgba(0,0,0,.04)}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:#1a1a1a;min-height:100vh}}
.hdr{{background:var(--card);border-bottom:1px solid var(--border);padding:18px 32px;display:flex;align-items:center;justify-content:space-between}}
.hdr h1{{font-size:19px;font-weight:700;letter-spacing:-.3px}}
.hdr p{{font-size:12px;color:var(--muted);margin-top:2px}}
.badge-plan{{font-size:11px;background:#f1f5f9;color:var(--muted);padding:4px 10px;border-radius:20px}}
.main{{max-width:1380px;margin:0 auto;padding:26px 32px}}
.sg{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:24px}}
.sc-sum{{background:var(--card);border-radius:var(--r);border:1px solid var(--border);padding:18px;box-shadow:var(--sh)}}
.sc-sum .lbl{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:6px}}
.sc-sum .val{{font-size:30px;font-weight:700;line-height:1}}
.sc-sum .sub{{font-size:11px;color:var(--muted);margin-top:3px}}
.v-cr .val{{color:var(--cr)}} .v-lw .val{{color:var(--lw)}} .v-ok .val{{color:var(--ok)}} .v-ov .val{{color:var(--ov)}} .v-tr .val{{color:var(--blue)}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}}
.full{{margin-bottom:18px}}
.card{{background:var(--card);border-radius:var(--r);border:1px solid var(--border);box-shadow:var(--sh);overflow:hidden}}
.ch{{padding:14px 18px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}}
.ch h2{{font-size:13px;font-weight:600}}
.cnt{{font-size:11px;background:#f1f5f9;color:var(--muted);padding:2px 8px;border-radius:20px}}
.arow{{padding:12px 18px;border-bottom:1px solid var(--border);display:grid;grid-template-columns:8px 1fr auto;gap:10px;align-items:start}}
.arow:last-child{{border-bottom:none}}
.adot{{width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0}}
.cr-dot{{background:var(--cr)}} .lw-dot{{background:var(--lw)}}
.asku{{font-size:13px;font-weight:600}}
.adet{{font-size:12px;color:var(--muted);margin-top:3px}}
.adeadline{{font-size:12px;font-weight:600;color:var(--cr);text-align:right}}
.aqty{{font-size:11px;color:var(--muted);margin-top:2px;text-align:right}}
.badge{{display:inline-block;font-size:11px;font-weight:500;padding:2px 7px;border-radius:4px;margin-right:4px}}
.b-tr{{background:#dbeafe;color:#1d4ed8}} .b-po{{background:#fce7f3;color:#be185d}} .b-aw{{background:#d1fae5;color:#065f46}}
.pt{{width:100%;border-collapse:collapse}}
.pt th{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);padding:10px 14px;text-align:left;background:#fafaf9;border-bottom:1px solid var(--border)}}
.pt td{{font-size:13px;padding:11px 14px;border-bottom:1px solid var(--border);vertical-align:middle}}
.pt tr:last-child td{{border-bottom:none}}
.pt tr:hover td{{background:#fafaf9}}
.pill{{display:inline-block;font-size:11px;font-weight:500;padding:3px 9px;border-radius:20px}}
.p-sh{{background:#dbeafe;color:#1e40af}} .p-tr{{background:#d1fae5;color:#065f46}} .p-pr{{background:#ede9fe;color:#5b21b6}} .p-or{{background:#fef3c7;color:#92400e}}
.mx{{overflow-x:auto}}
.mt{{width:100%;border-collapse:collapse;min-width:860px}}
.mt th{{font-size:11px;font-weight:600;color:var(--muted);padding:9px 7px;text-align:center;background:#fafaf9;border-bottom:1px solid var(--border);white-space:nowrap}}
.mt th:first-child{{text-align:left;padding-left:16px;min-width:190px}}
.mt td{{padding:7px;text-align:center;border-bottom:1px solid var(--border);font-size:12px}}
.mt td:first-child{{text-align:left;padding-left:16px;font-size:13px;font-weight:500}}
.mt tr:last-child td{{border-bottom:none}}
.mc{{display:inline-block;padding:3px 7px;border-radius:5px;font-weight:500;min-width:36px;text-align:center}}
.mc.cr{{background:var(--cr-bg);color:var(--cr)}} .mc.lw{{background:var(--lw-bg);color:var(--lw)}}
.mc.ok{{background:var(--ok-bg);color:var(--ok)}} .mc.ov{{background:var(--ov-bg);color:var(--ov)}} .mc.nd{{color:#d1d5db}}
.leg{{display:flex;gap:14px;padding:10px 18px;border-top:1px solid var(--border);background:#fafaf9;flex-wrap:wrap}}
.li{{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--muted)}}
.ld{{width:10px;height:10px;border-radius:3px}}
.sku-col{{white-space:nowrap}}
.sup-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;padding:14px 18px}}
.sc{{background:#fafaf9;border:1px solid var(--border);border-radius:8px;padding:12px}}
.sc-name{{font-size:13px;font-weight:600;margin-bottom:7px}}
.sc-row{{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-top:3px}}
.sc-row span:last-child{{font-weight:600;color:#1a1a1a}}
.chart-wrap{{padding:18px;height:210px}}
.empty{{padding:28px 18px;text-align:center;color:var(--muted);font-size:13px}}
@media(max-width:900px){{.sg{{grid-template-columns:repeat(3,1fr)}}.two{{grid-template-columns:1fr}}.main{{padding:14px}}.hdr{{padding:14px}}}}
</style>
</head>
<body>
<div class="hdr">
  <div>
    <h1>Inventory Dashboard</h1>
    <p>Big Life Journal &nbsp;&middot;&nbsp; Generated: {d['generated']}</p>
  </div>
  <span class="badge-plan">Plan: {d['plan_date']}</span>
</div>
<div class="main">
{no_data_msg}

<!-- Summary -->
<div class="sg">
  <div class="sc-sum v-cr"><div class="lbl">Critical</div><div class="val">{c.get('CRITICAL',0)}</div><div class="sub">Need immediate action</div></div>
  <div class="sc-sum v-lw"><div class="lbl">Low Stock</div><div class="val">{c.get('LOW',0)}</div><div class="sub">Need replenishment</div></div>
  <div class="sc-sum v-ok"><div class="lbl">Healthy</div><div class="val">{c.get('OK',0)}</div><div class="sub">90–365 days of stock</div></div>
  <div class="sc-sum v-ov"><div class="lbl">Overstock</div><div class="val">{c.get('OVERSTOCK',0)}</div><div class="sub">Over 365 days</div></div>
  <div class="sc-sum v-tr"><div class="lbl">In Transit</div><div class="val">{d['active_pos_count']}</div><div class="sub">Active POs &amp; transfers</div></div>
</div>

<!-- Actions + Velocity -->
<div class="two">
  <div class="card">
    <div class="ch"><h2>🔴 Urgent Actions</h2><span class="cnt">{len(d['urgent'])}</span></div>
    {urgent_rows()}
  </div>
  <div class="card">
    <div class="ch"><h2>Sales Velocity (units/day, 90d avg)</h2></div>
    <div class="chart-wrap"><canvas id="vc"></canvas></div>
  </div>
</div>

<!-- Replenishment + POs -->
<div class="two">
  <div class="card">
    <div class="ch"><h2>🟡 Replenishment Needed</h2><span class="cnt">{len(d['normal'])}</span></div>
    {normal_rows()}
  </div>
  <div class="card">
    <div class="ch"><h2>📦 Active POs &amp; Transfers</h2><span class="cnt">{d['active_pos_count']}</span></div>
    <table class="pt"><thead><tr><th>PO / ID</th><th>SKU</th><th>Qty</th><th>Route</th><th>ETA</th><th>Status</th></tr></thead>
    <tbody>{po_rows()}</tbody></table>
  </div>
</div>

<!-- Health Matrix -->
<div class="card full">
  <div class="ch"><h2>Inventory Health Matrix</h2></div>
  <div class="mx">
    <table class="mt">
      <thead><tr><th>SKU</th>{wh_headers}</tr></thead>
      <tbody>{matrix_rows()}</tbody>
    </table>
  </div>
  <div class="leg">
    <div class="li"><div class="ld" style="background:var(--cr-bg);border:1px solid var(--cr)"></div>Critical &lt;30d</div>
    <div class="li"><div class="ld" style="background:var(--lw-bg);border:1px solid var(--lw)"></div>Low 30–90d</div>
    <div class="li"><div class="ld" style="background:var(--ok-bg);border:1px solid var(--ok)"></div>Healthy 90–365d</div>
    <div class="li"><div class="ld" style="background:var(--ov-bg);border:1px solid var(--ov)"></div>Overstock &gt;365d</div>
  </div>
</div>

<!-- Supplier Stock -->
<div class="card full">
  <div class="ch"><h2>Supplier Stock</h2></div>
  <div class="sup-grid">{supplier_cards()}</div>
</div>

</div>
<script>
new Chart(document.getElementById('vc').getContext('2d'),{{
  type:'bar',
  data:{{
    labels:{js_velocity_labels},
    datasets:[{{
      label:'Units/day',
      data:{js_velocity_values},
      backgroundColor:'#dbeafe',borderColor:'#2563eb',borderWidth:1.5,borderRadius:6
    }}]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{
      x:{{grid:{{display:false}},ticks:{{font:{{size:10}}}}}},
      y:{{grid:{{color:'#f1f5f9'}},ticks:{{font:{{size:10}}}}}}
    }}
  }}
}});
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description='Generate HTML inventory dashboard')
    parser.add_argument('--output', default='.tmp/dashboard.html')
    parser.add_argument('--no-open', action='store_true', help='Do not open in browser')
    args = parser.parse_args()

    print("Generating dashboard...")
    data = get_dashboard_data()

    html = render_html(data)

    output_path = os.path.join(PROJECT_ROOT, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"\nDashboard saved to {args.output}")

    if not args.no_open:
        webbrowser.open(f'file://{os.path.abspath(output_path)}')
        print("Opened in browser.")

    return output_path


if __name__ == '__main__':
    main()
