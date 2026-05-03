
import json
import os
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

def is_journal(sku_id):
    return sku_id.startswith('EIDJ') and not sku_id.startswith('EIDJB')

def avg(lst):
    return sum(lst) / len(lst) if lst else 0

def max_or_zero(lst):
    return max(lst) if lst else 0


def generate_report():
    with open(os.path.join(PROJECT_ROOT, '.tmp/data.json')) as f:
        data = json.load(f)
    sales = data.get('sales', [])

    wh_ann = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
    global_ann = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    for row in sales:
        d = parse_date(row.get('date', ''))
        if d is None:
            continue
        sku = row.get('sku_id', '').strip()
        wh  = row.get('warehouse', '').strip()
        units = float(row.get('units_sold', 0) or 0)
        if sku:
            global_ann[sku][d.year][d.month] += units
            if wh:
                wh_ann[sku][wh][d.year][d.month] += units

    forecast_months = [5, 6, 7, 8, 9, 10, 11, 12, 1]
    buffer_months   = [2, 3, 4]

    month_label = {
        1: 'Jan 2027', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May 2026', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    month_short = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                   7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    days_in = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}

    skus = [s for s in data['config']['skus'] if s.get('active', True)]
    stock_idx = {
        e['sku_id']: {k: float(v) for k, v in e.get('stock', {}).items()}
        for e in data.get('current_stock', [])
    }
    sup_idx = {
        e['sku_id']: float(e.get('china_supplier', 0)) + float(e.get('canada_supplier', 0))
        for e in data.get('supplier_stock', [])
    }

    # All modelled channels — EU included for transfer planning
    all_channels = ['Amazon_US_FBA', 'Amazon_CA_FBA', 'UK', 'EU', 'AU']

    def wh_demand(sku_id, wh):
        """Max monthly demand for a warehouse over the forecast window."""
        return sum(
            max_or_zero([
                wh_ann[sku_id][wh][yr][m]
                for yr in wh_ann[sku_id][wh]
                if wh_ann[sku_id][wh][yr][m] > 0
            ])
            for m in forecast_months
        )

    def wh_monthly(sku_id, wh):
        return {
            m: max_or_zero([
                wh_ann[sku_id][wh][yr][m]
                for yr in wh_ann[sku_id][wh]
                if wh_ann[sku_id][wh][yr][m] > 0
            ])
            for m in forecast_months
        }

    def wh_buffer(sku_id, wh):
        total = 0
        parts = {}
        for m in buffer_months:
            vals = [wh_ann[sku_id][wh][yr][m]
                    for yr in wh_ann[sku_id][wh]
                    if wh_ann[sku_id][wh][yr][m] > 0]
            a = avg(vals)
            total += a
            parts[m] = {'vals': vals, 'avg': a}
        # 30-day buffer = average of the 3 post-peak months (not their sum)
        return total / len(buffer_months), parts

    # ── PRE-COMPUTE ALL SKU DATA ─────────────────────────────────────────────

    sku_data = {}

    for sku in skus:
        sid  = sku['sku_id']
        name = sku['sku_name']
        is_j = is_journal(sid)

        # --- Global monthly (for demand-breakdown table) ---
        g_monthly = {}
        for m in forecast_months + buffer_months:
            y24 = global_ann[sid].get(2024, {}).get(m, 0)
            y25 = global_ann[sid].get(2025, {}).get(m, 0)
            active = [v for v in [y24, y25] if v > 0]
            g_monthly[m] = {'2024': y24, '2025': y25,
                             'max': max_or_zero(active), 'avg': avg(active)}

        # --- Per-channel demand, current stock, deficit ---
        # CA FBA uses 'CA' warehouse sales as proxy for demand
        source_wh = {'Amazon_US_FBA': 'Amazon_US_FBA',
                     'Amazon_CA_FBA': 'CA',
                     'UK':            'UK',
                     'EU':            'EU',
                     'AU':            'AU'}

        ch = {}
        for region in all_channels:
            swh   = source_wh[region]
            dem   = wh_demand(sid, swh)
            curr  = stock_idx.get(sid, {}).get(region, 0)
            buf_total, buf_parts = wh_buffer(sid, swh)
            ch[region] = {
                'source_wh':  swh,
                'demand':     dem,
                'monthly':    wh_monthly(sid, swh),
                'current':    curr,
                'deficit':    max(0.0, dem + buf_total - curr),  # must cover demand + buffer
                'buffer':     buf_total,
                'buf_parts':  buf_parts,
            }

        # --- Global buffer (for global summary table) ---
        g_buf_parts = {}
        g_buf_total = 0.0
        for m in buffer_months:
            vals = [global_ann[sid][yr][m]
                    for yr in global_ann[sid]
                    if global_ann[sid][yr][m] > 0]
            a = avg(vals)
            g_buf_parts[m] = {'vals': vals, 'avg': a}
            g_buf_total += a
        g_buf_total = g_buf_total / len(buffer_months)  # 30-day = 1-month average
        g_demand = sum(g_monthly[m]['max'] for m in forecast_months)
        g_stock  = sum(stock_idx.get(sid, {}).values()) + sup_idx.get(sid, 0)

        # ── TRANSFERS & PRINT LOGIC ──────────────────────────────────────────
        #
        # Step 1  UK transfers — only send what UK can spare above its own needs.
        # Step 2  Compute start_stock for all regions.
        # Step 3  Calculate per-channel shortfalls (demand + buffer − start_stock).
        # Step 4a If ANY shortfall exists → print for ALL short channels (no hub transfers).
        # Step 4b If no shortfall anywhere → hub→FBA transfers reposition existing stock.

        uk_stock   = stock_idx.get(sid, {}).get('UK', 0)
        uk_surplus = max(0.0,
                         uk_stock - ch['UK']['demand'] - ch['UK']['buffer'])

        transfers   = []
        incoming    = defaultdict(float)
        outgoing_uk = 0.0

        # Step 1a: UK → AU (journals only, limited to UK surplus above own needs)
        if is_j:
            au_def = max(0.0,
                         ch['AU']['demand'] + ch['AU']['buffer'] - ch['AU']['current'])
            if au_def > 0 and uk_surplus > 0:
                pull = min(au_def, uk_surplus)
                transfers.append({
                    'source': 'UK', 'dest': 'AU', 'qty': pull,
                    'reason': (f"AU needs {int(ch['AU']['demand'] + ch['AU']['buffer']):,} "
                               f"(demand + buffer); AU has {int(ch['AU']['current']):,}; "
                               f"deficit {int(au_def):,}; UK can spare {int(uk_surplus):,} "
                               f"above its own needs")
                })
                incoming['AU'] += pull
                outgoing_uk    += pull
                uk_surplus     -= pull

        # Step 1b: UK → EU (limited to remaining UK surplus)
        eu_def = max(0.0,
                     ch['EU']['demand'] + ch['EU']['buffer'] - ch['EU']['current'])
        if eu_def > 0 and uk_surplus > 0:
            pull = min(eu_def, uk_surplus)
            transfers.append({
                'source': 'UK', 'dest': 'EU', 'qty': pull,
                'reason': (f"EU needs {int(ch['EU']['demand'] + ch['EU']['buffer']):,}; "
                           f"EU has {int(ch['EU']['current']):,}; "
                           f"deficit {int(eu_def):,}; UK surplus {int(uk_surplus):,}")
            })
            incoming['EU'] += pull
            outgoing_uk    += pull
            uk_surplus     -= pull

        # Step 2: Start stock after UK transfers (before any print or hub moves)
        start_stock = {}
        for region in all_channels:
            if region == 'UK':
                start_stock[region] = uk_stock - outgoing_uk
            else:
                start_stock[region] = ch[region]['current'] + incoming.get(region, 0)

        # Step 3: Per-channel shortfalls (demand + buffer − start_stock)
        shortfalls = {
            r: max(0.0, ch[r]['demand'] + ch[r]['buffer'] - start_stock[r])
            for r in all_channels
        }
        any_short = any(v > 0 for v in shortfalls.values())

        # Step 4a: Print mode — triggered by ANY channel being short.
        # Rule: if printing anything, print for ALL short channels; no hub→FBA transfers.
        print_alloc = {}
        if any_short:
            for region, shortfall in shortfalls.items():
                if shortfall > 0:
                    # EU: only print if UK truly can't cover (already handled in Step 1b)
                    # We skip EU here — the transfer in Step 1b covers what it can;
                    # remaining EU gap is a real shortfall that needs print.
                    print_alloc[region] = int(shortfall)
                    incoming[region]    += shortfall
                    start_stock[region] += shortfall

        total_print = sum(print_alloc.values())
        is_printing = total_print > 0

        # Step 4b: Reposition mode — no print needed, use hub→FBA transfers.
        if not is_printing:
            for region, src_list in [
                ('Amazon_US_FBA', [('HBG', 'HBG'), ('SLI', 'SLI'), ('SAV', 'SAV')]),
                ('Amazon_CA_FBA', [('CA',  'CA Hub')]),
            ]:
                gap = max(0.0, ch[region]['demand'] + ch[region]['buffer']
                          - start_stock[region])
                for src_key, src_label in src_list:
                    if gap <= 0:
                        break
                    src_stock = stock_idx.get(sid, {}).get(src_key, 0)
                    if src_stock > 0:
                        pull = min(gap, src_stock)
                        transfers.append({
                            'source': src_label, 'dest': region, 'qty': pull,
                            'reason': (
                                f"{region.replace('_',' ')} needs "
                                f"{int(ch[region]['demand'] + ch[region]['buffer']):,}; "
                                f"has {int(ch[region]['current']):,}; "
                                f"{src_label} has {int(src_stock):,}")
                        })
                        incoming[region]    += pull
                        start_stock[region] += pull
                        gap -= pull

        sku_data[sid] = {
            'name': name, 'is_journal': is_j,
            'g_monthly': g_monthly, 'g_buf_parts': g_buf_parts,
            'g_demand': g_demand, 'g_buf_total': g_buf_total, 'g_stock': g_stock,
            'ch': ch,
            'transfers': transfers, 'incoming': dict(incoming),
            'outgoing_uk': outgoing_uk,
            'print_alloc': print_alloc, 'total_print': total_print,
            'is_printing': is_printing,
            'start_stock': start_stock,
        }

    # ── REPORT STATS ────────────────────────────────────────────────────────
    printing_skus     = [s for s in skus if sku_data[s['sku_id']]['is_printing']]
    total_print_units = sum(sku_data[s['sku_id']]['total_print'] for s in printing_skus)
    total_transfers   = sum(len(sku_data[s['sku_id']]['transfers']) for s in skus)

    # ── BUILD MARKDOWN ───────────────────────────────────────────────────────

    md  = "# Inventory Master Plan: May 2026 – January 2027\n\n"
    md += "*Generated: May 3, 2026 · 9-month active period + 30-day carry-over buffer · 8 SKUs · 10 warehouses*\n\n"
    md += "---\n\n"

    # ── EXECUTIVE SUMMARY ───────────────────────────────────────────────────
    md += "## Executive Summary\n\n"
    md += ("This plan covers every SKU from **May 2026 through January 2027** and "
           "ensures each channel ends January with 30 days of carry-over stock — "
           "enough to bridge to the next order cycle without touching zero.\n\n")

    md += "### What Needs to Happen Now\n\n"

    if printing_skus:
        md += "**🖨️ New Print Orders:**\n\n"
        for s in printing_skus:
            sd = sku_data[s['sku_id']]
            alloc_str = ', '.join(
                f"{qty:,} → {dest.replace('_',' ')}"
                for dest, qty in sd['print_alloc'].items()
            )
            md += f"- **{sd['name']}**: print **{sd['total_print']:,} units** ({alloc_str}) — ship direct from printer, do not route through hubs\n"
        md += "\n"

    non_print_skus = [s for s in skus if not sku_data[s['sku_id']]['is_printing']
                      and sku_data[s['sku_id']]['transfers']]
    if non_print_skus:
        md += "**📦 Hub→FBA Transfers** *(no print run needed — reposition existing stock)*:\n\n"
        for s in non_print_skus:
            sd = sku_data[s['sku_id']]
            t_str = ', '.join(
                f"{int(t['qty']):,} {t['source']}→{t['dest'].replace('_',' ')}"
                for t in sd['transfers'] if t['source'] in ('HBG','SLI','CA Hub')
            )
            if t_str:
                md += f"- **{sd['name']}**: {t_str}\n"
        md += "\n"

    intl_skus = [s for s in skus if any(
        t['source'] == 'UK' for t in sku_data[s['sku_id']]['transfers']
    )]
    if intl_skus:
        md += "**✈️ International Transfers** *(all SKUs — happens regardless of print)*:\n\n"
        for s in intl_skus:
            sd = sku_data[s['sku_id']]
            t_str = ', '.join(
                f"{int(t['qty']):,} UK→{t['dest'].replace('_',' ')}"
                for t in sd['transfers'] if t['source'] == 'UK'
            )
            md += f"- **{sd['name']}**: {t_str}\n"
        md += "\n"

    md += "### Plan at a Glance\n\n"
    md += "| | |\n| :--- | :--- |\n"
    md += f"| Selling period | May 2026 – Jan 2027 (9 months) |\n"
    md += f"| Buffer carry-over | Feb 2027 (30 days) |\n"
    md += f"| SKUs needing new print | {len(printing_skus)} SKUs · {int(total_print_units):,} units total |\n"
    md += f"| Transfer moves | {total_transfers} |\n"
    md += ("| Print → FBA rule | If printing: ship direct to FBA from printer · "
           "No hub→FBA transfers |\n")
    md += ("| Transfer → FBA rule | If NOT printing: reposition hub stock into FBA · "
           "No new print |\n\n")
    md += "---\n\n"

    # ── SECTION 1: METHODOLOGY ──────────────────────────────────────────────
    md += "## Section 1: How the Numbers Were Calculated\n\n"

    md += "### The Two Questions\n\n"
    md += ("1. **How much will we sell?** — per channel, per month, May 2026–Jan 2027\n"
           "2. **How much must be left over in January?** — 30-day buffer so we never hit zero "
           "before the next order arrives\n\n")

    md += "### Demand: Use the Maximum, Not the Average\n\n"
    md += ("For each channel and each month, we compare 2024 and 2025 actual sales and take "
           "the **higher number**. Planning to the max means we're ready for a strong Q4 — "
           "if we've ever sold that many in a given month, we need to be ready to do it again.\n\n")

    ex = skus[0]
    ex_sd = sku_data[ex['sku_id']]
    oct = ex_sd['g_monthly'][10]
    md += f"**Example — {ex_sd['name']}, October (global):**\n\n"
    md += "| | Units |\n| :--- | ---: |\n"
    md += f"| 2024 October | {int(oct['2024']):,} |\n"
    md += f"| 2025 October | {int(oct['2025']):,} |\n"
    md += f"| **We plan for** | **{int(oct['max']):,}** ← the higher of the two |\n\n"

    md += "### Safety Buffer: 90 Days of Stock After January\n\n"
    md += ("The buffer is the average of what each channel historically sells in "
           "February, March, and April — then average them. That single monthly "
           "average is the 30-day buffer: it must still be sitting in the warehouse "
           "on February 1st before the next order cycle completes.\n\n")

    md += f"**Example — {ex_sd['name']} global buffer:**\n\n"
    md += "| Month | Historical Sales | Average |\n| :--- | :--- | ---: |\n"
    for m in buffer_months:
        bd = ex_sd['g_buf_parts'][m]
        vals = ', '.join(f"{int(v):,}" for v in bd['vals']) if bd['vals'] else 'no data'
        md += f"| {month_short[m]} | {vals} | **{int(bd['avg']):,}** |\n"
    md += f"| **30-day buffer (avg)** | | **{int(ex_sd['g_buf_total']):,}** |\n\n"

    md += "### Print vs Transfer Decision\n\n"
    md += ("**If a channel is short and we need a new print run:** "
           "the print ships direct from the printer to that channel — US FBA, CA FBA, or AU. "
           "We do not route through hubs. Hub stock stays in hubs to serve domestic and "
           "wholesale orders.\n\n"
           "**If global stock is sufficient (no print run):** "
           "we reposition hub stock (HBG/SLI → US FBA, CA Hub → CA FBA) to fill "
           "channel deficits. No new units are ordered.\n\n"
           "**UK transfers (UK → AU for journals, UK → EU) always happen** "
           "when those markets have a deficit — regardless of whether we're printing.\n\n")

    md += "### Routing Constraints\n\n"
    md += "| Route | Allowed? | Notes |\n| :--- | :--- | :--- |\n"
    md += "| UK → AU | ✅ Journals only | Cards blocked; must print direct to AU |\n"
    md += "| UK → EU | ✅ All SKUs | |\n"
    md += "| HBG / SLI → US FBA | ✅ If not printing | Skipped when a print run is active |\n"
    md += "| CA Hub → CA FBA | ✅ If not printing | Same rule |\n"
    md += "| UK → US / CA | ❌ | Not a valid route |\n\n"
    md += "---\n\n"

    # ── SECTION 2: DEMAND BREAKDOWN ─────────────────────────────────────────
    md += "## Section 2: Full Demand Breakdown by SKU\n\n"
    md += ("For every SKU: month-by-month global demand (2024 vs 2025, max chosen), "
           "buffer calculation, and per-channel stock check.\n\n")

    for sku in skus:
        sid  = sku['sku_id']
        sd   = sku_data[sid]
        name = sd['name']

        md += f"### {name} `{sid}`\n\n"

        # Global monthly demand table
        md += "**Monthly Demand Forecast (Global)**\n\n"
        md += "| Month | 2024 | 2025 | ✅ Max Used | Running Total |\n"
        md += "| :--- | ---: | ---: | ---: | ---: |\n"
        running = 0
        for m in forecast_months:
            r = sd['g_monthly'][m]
            running += r['max']
            y24 = f"{int(r['2024']):,}" if r['2024'] > 0 else "—"
            y25 = f"{int(r['2025']):,}" if r['2025'] > 0 else "—"
            chosen = f"**{int(r['max']):,}**" if r['max'] > 0 else "—"
            if r['2024'] > r['2025'] and r['2024'] > 0:
                chosen += " ← 2024"
            elif r['2025'] > r['2024'] and r['2025'] > 0:
                chosen += " ← 2025"
            md += f"| {month_label[m]} | {y24} | {y25} | {chosen} | {int(running):,} |\n"
        md += f"| **9-Month Total** | | | | **{int(sd['g_demand']):,}** |\n\n"

        # Buffer
        md += "**30-Day Buffer (Feb–Apr average)**\n\n"
        md += "| Month | 2024 | 2025 | Average |\n| :--- | ---: | ---: | ---: |\n"
        for m in buffer_months:
            bd   = sd['g_buf_parts'][m]
            y24b = int(global_ann[sid].get(2024, {}).get(m, 0))
            y25b = int(global_ann[sid].get(2025, {}).get(m, 0))
            y24s = f"{y24b:,}" if y24b > 0 else "—"
            y25s = f"{y25b:,}" if y25b > 0 else "—"
            md += f"| {month_short[m]} | {y24s} | {y25s} | **{int(bd['avg']):,}** |\n"
        md += f"| **30-day buffer (avg)** | | | **{int(sd['g_buf_total']):,}** |\n\n"

        # Per-channel stock check
        md += "**Per-Channel Stock Check**\n\n"
        md += "| Channel | 9-Mo Demand | Current Stock | Deficit | How It's Filled |\n"
        md += "| :--- | ---: | ---: | ---: | :--- |\n"
        for region in all_channels:
            c = sd['ch'][region]
            if c['demand'] == 0 and c['current'] == 0:
                continue
            deficit = int(c['deficit'])
            curr    = int(c['current'])
            dem     = int(c['demand'])
            # Determine fill method — check print_alloc first, then transfers
            if deficit == 0:
                fill = "✅ Sufficient stock"
            elif region in sd['print_alloc']:
                qty  = sd['print_alloc'][region]
                note = " (UK→AU blocked for cards)" if region == 'AU' and not sd['is_journal'] else ""
                fill = f"🖨️ Print {qty:,} direct to {region.replace('_',' ')}{note}"
            else:
                dest_transfers = [t for t in sd['transfers'] if t['dest'] == region]
                if dest_transfers:
                    parts = [f"{t['source']} {int(t['qty']):,}" for t in dest_transfers]
                    icon  = "✈️" if any(t['source'] == 'UK' for t in dest_transfers) else "📦"
                    fill  = f"{icon} Transfer: {' + '.join(parts)}"
                else:
                    fill = f"⚠️ Deficit {deficit:,} — unresolved (no transfer or print allocated)"
            md += f"| {region.replace('_',' ')} | {dem:,} | {curr:,} | {deficit:,} | {fill} |\n"

        # UK outgoing note
        uk_curr = int(sd['ch']['UK']['current'])
        uk_out  = int(sd['outgoing_uk'])
        uk_dem  = int(sd['ch']['UK']['demand'])
        uk_end  = uk_curr - uk_out
        if uk_out > 0:
            md += (f"\n> **UK stock:** {uk_curr:,} current − {uk_out:,} transferred out = "
                   f"**{uk_end:,} remaining** vs UK demand {uk_dem:,} → "
                   f"{'✅ covered' if uk_end >= uk_dem else '⚠️ short'}\n")

        # Print decision summary
        if sd['is_printing']:
            alloc_detail = ' + '.join(
                f"{qty:,} to {dest.replace('_',' ')}"
                for dest, qty in sd['print_alloc'].items()
            )
            md += f"\n**→ PRINT ORDER: {sd['total_print']:,} units** ({alloc_detail})\n\n"
        else:
            md += f"\n**→ No print order needed** — transfers reposition existing stock\n\n"

        md += "---\n\n"

    # ── SECTION 3: PRINT ORDERS ──────────────────────────────────────────────
    md += "## Section 3: New Print Orders\n\n"

    if not printing_skus:
        md += ("✅ **No new print orders required.** All channels can be covered by "
               "repositioning existing hub stock via transfers.\n\n")
    else:
        md += ("The following SKUs need new units printed and shipped **direct from the "
               "printer to the destination** — do not route through hubs.\n\n")
        for s in printing_skus:
            sid = s['sku_id']
            sd  = sku_data[sid]

            md += f"### 🖨️ {sd['name']} — Print {sd['total_print']:,} Units\n\n"

            md += "| Destination | Units | Current Stock | 9-Mo Demand | Deficit | Math |\n"
            md += "| :--- | ---: | ---: | ---: | ---: | :--- |\n"
            for dest, qty in sd['print_alloc'].items():
                c       = sd['ch'][dest]
                curr    = int(c['current'])
                dem     = int(c['demand'])
                deficit = int(c['deficit'])
                uk_note = ""
                if dest == 'AU' and not sd['is_journal']:
                    uk_note = " (UK→AU blocked for cards)"
                md += (f"| {dest.replace('_',' ')} | **{qty:,}** | {curr:,} | "
                       f"{dem:,} | {deficit:,} | "
                       f"{dem:,} demand − {curr:,} stock = {deficit:,} needed{uk_note} |\n")

            md += f"\n*Total print run: **{sd['total_print']:,} units** · ship direct from printer*\n\n"

    md += "---\n\n"

    # ── SECTION 4: TRANSFER PLAN ─────────────────────────────────────────────
    md += "## Section 4: Transfer Plan\n\n"
    md += ("All transfers should be executed by **September 1, 2026**. "
           "FBA inbound processing takes 2–4 weeks — stock not in FBA by "
           "early October will miss the November–December peak.\n\n")

    md += ("> **Routing rule:** UK → AU for Journals only. "
           "Hub → FBA transfers only happen for SKUs with **no new print run**. "
           "For printing SKUs, FBA is filled directly from the print run.\n\n")

    has_transfers = any(sd['transfers'] for sd in sku_data.values())
    if has_transfers:
        md += "| SKU | From → To | Units | Source Stock | Dest Demand | Justification |\n"
        md += "| :--- | :--- | ---: | ---: | ---: | :--- |\n"
        for sku in skus:
            sid = sku['sku_id']
            sd  = sku_data[sid]
            for t in sd['transfers']:
                src_key = t['source'].replace(' Hub', '')
                src_stock = int(stock_idx.get(sid, {}).get(src_key, 0))
                dest_dem  = int(sd['ch'].get(t['dest'], {}).get('demand', 0))
                md += (f"| {sd['name']} | {t['source']} → {t['dest'].replace('_',' ')} "
                       f"| **{int(t['qty']):,}** | {src_stock:,} | {dest_dem:,} | "
                       f"{t['reason']} |\n")
    else:
        md += "No transfers required — all channels covered by existing stock at destination or new print.\n"

    md += "\n---\n\n"

    # ── SECTION 5: ROLLING DEPLETION ─────────────────────────────────────────
    md += "## Section 5: Rolling Depletion Forecast by Channel\n\n"
    md += ("Starting stock = current inventory **after** all transfers land and print runs arrive. "
           "Each month we subtract max projected sales. "
           "January 2027 ending balance = the 30-day carry-over buffer.\n\n")
    md += ("> **How to read:** Starting stock is real — it reflects actual current inventory "
           "plus confirmed inbound (transfers or print). "
           "January ending balance should always be positive — that's the buffer.\n\n")

    consumer_display = ['Amazon_US_FBA', 'Amazon_CA_FBA', 'UK', 'AU']

    for sku in skus:
        sid = sku['sku_id']
        sd  = sku_data[sid]

        if not any(sd['ch'][r]['demand'] > 0 for r in consumer_display):
            continue

        md += f"### {sd['name']}\n\n"

        for region in consumer_display:
            c = sd['ch'][region]
            if c['demand'] == 0 and sd['start_stock'].get(region, 0) == 0:
                continue

            starting   = sd['start_stock'].get(region, 0)
            reg_buffer = c['buffer']
            monthly    = c['monthly']

            # Build buffer note
            buf_parts = []
            for m in buffer_months:
                bp = c['buf_parts'].get(m, {})
                if bp.get('avg', 0) > 0:
                    buf_parts.append(f"{month_short[m]} avg {int(bp['avg']):,}")
            buf_note = " + ".join(buf_parts) + f" = {int(reg_buffer):,}" if buf_parts else f"{int(reg_buffer):,}"

            # Incoming explanation
            inc = sd['incoming'].get(region, 0)
            curr = int(c['current'])
            if region == 'UK':
                out = int(sd['outgoing_uk'])
                stock_note = (f"*Starting stock: **{int(starting):,}** "
                              f"({curr:,} current − {out:,} transferred out)*")
            elif inc > 0:
                src = 'print run' if sd['is_printing'] and region in sd['print_alloc'] else 'transfer in'
                stock_note = (f"*Starting stock: **{int(starting):,}** "
                              f"({curr:,} current + {int(inc):,} {src})*")
            else:
                stock_note = f"*Starting stock: **{int(starting):,}** (current stock only)*"

            md += f"#### {region.replace('_', ' ')}\n\n"
            md += stock_note + "\n\n"
            md += f"*30-day buffer target: **{int(reg_buffer):,} units** ({buf_note})*\n\n"

            md += "| Month | Max Projected Sales | Ending Stock | vs Buffer | Weeks of Cover |\n"
            md += "| :--- | ---: | ---: | ---: | ---: |\n"

            cumulative = 0
            for i, m in enumerate(forecast_months):
                m_max = monthly[m]
                cumulative += m_max
                ending = starting - cumulative

                # Weeks of cover (based on next month's rate)
                next_i = i + 1
                if next_i < len(forecast_months):
                    next_rate = monthly[forecast_months[next_i]]
                else:
                    next_rate = reg_buffer / 3
                if next_rate > 0:
                    woc = ending / (next_rate / (days_in.get(m, 30) / 7))
                    woc_str = f"{woc:.1f}w"
                else:
                    woc_str = "—"

                vs_buf = int(round(ending)) - int(round(reg_buffer))
                vs_str = f"+{vs_buf:,}" if vs_buf >= 0 else f"**{vs_buf:,} ⚠️**"
                flag   = " ⚠️" if ending < 0 else ""
                md += (f"| {month_label[m]} | {int(m_max):,} | "
                       f"**{int(ending):,}**{flag} | {vs_str} | {woc_str} |\n")

            jan_end = starting - sum(monthly[m] for m in forecast_months)
            status  = "✅" if jan_end >= reg_buffer * 0.9 else "⚠️ below target"
            md += (f"\n> Jan 2027 ending: **{int(jan_end):,} units** | "
                   f"Buffer target: {int(reg_buffer):,} | {status}\n\n")

    md += "---\n\n"

    # ── SECTION 6: MASTER CHECKLIST ──────────────────────────────────────────
    md += "## Section 6: Master Action Checklist\n\n"

    md += "### 🖨️ Print Orders (Place Immediately)\n\n"
    if printing_skus:
        for s in printing_skus:
            sd = sku_data[s['sku_id']]
            md += f"- [ ] **{sd['name']}** — order **{sd['total_print']:,} units** from supplier\n"
            for dest, qty in sd['print_alloc'].items():
                md += f"  - Ship **{qty:,} units** direct to **{dest.replace('_',' ')}**\n"
    else:
        md += "- ✅ No print orders needed\n"
    md += "\n"

    md += "### 📦 Transfers (Complete Before September 1st)\n\n"
    for s in skus:
        sid = s['sku_id']
        sd  = sku_data[sid]
        if sd['transfers']:
            md += f"**{sd['name']}:**\n"
            for t in sd['transfers']:
                md += f"- [ ] {t['source']} → {t['dest'].replace('_',' ')}: **{int(t['qty']):,} units**\n"
            md += "\n"

    md += "### 📋 Verification Checkpoints\n\n"
    md += "- [ ] Print order lead times confirmed — Kids Journal & Know Me Cards must arrive before September\n"
    md += "- [ ] FBA inbound shipments created in Seller Central with tracking numbers\n"
    md += "- [ ] UK→AU journal shipments cleared customs and confirmed at AU warehouse\n"
    md += "- [ ] Re-run this plan in August — adjust if Q3 demand runs above or below forecast\n"
    md += "- [ ] Check again in November — flag early if December is tracking above forecast\n\n"

    md += "---\n\n"
    md += "*Plan generated May 3, 2026. Re-run monthly. Source: `.tmp/data.json`*\n"

    tmp_path  = os.path.join(PROJECT_ROOT, '.tmp/massive_report.md')
    docs_path = os.path.join(PROJECT_ROOT, 'docs/INVENTORY_MASTER_PLAN.md')
    for path in [tmp_path, docs_path]:
        with open(path, 'w') as f:
            f.write(md)

    lines = len(md.splitlines())
    print(f"Report generated: {lines} lines")
    print(f"  .tmp/massive_report.md")
    print(f"  docs/INVENTORY_MASTER_PLAN.md")


if __name__ == '__main__':
    generate_report()
