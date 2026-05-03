
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

    wh_annual_monthly = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
    global_annual_monthly = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    for row in sales:
        d = parse_date(row.get('date', ''))
        if d is None:
            continue
        sku = row.get('sku_id', '').strip()
        wh = row.get('warehouse', '').strip()
        units = float(row.get('units_sold', 0) or 0)
        if sku:
            global_annual_monthly[sku][d.year][d.month] += units
            if wh:
                wh_annual_monthly[sku][wh][d.year][d.month] += units

    forecast_months = [5, 6, 7, 8, 9, 10, 11, 12, 1]
    buffer_months = [2, 3, 4]
    month_names = {
        1: 'Jan 2027', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May 2026', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    month_short = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                   7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
    days_in_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
                     7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

    skus = [s for s in data['config']['skus'] if s.get('active', True)]
    stock_index = {
        entry['sku_id']: {k: float(v) for k, v in entry.get('stock', {}).items()}
        for entry in data.get('current_stock', [])
    }
    supplier_stock_index = {
        entry['sku_id']: {
            'china': float(entry.get('china_supplier', 0)),
            'canada': float(entry.get('canada_supplier', 0))
        }
        for entry in data.get('supplier_stock', [])
    }

    consumer_regions = ['Amazon_US_FBA', 'Amazon_CA_FBA', 'UK', 'AU']

    # ── PRE-COMPUTE ALL NUMBERS ──────────────────────────────────────────────

    sku_data = {}

    for sku in skus:
        sku_id = sku['sku_id']
        sku_name = sku['sku_name']
        is_j = is_journal(sku_id)

        # Global monthly: 2024, 2025, max (forecast + buffer months)
        monthly = {}
        for m in forecast_months + buffer_months:
            y2024 = global_annual_monthly[sku_id].get(2024, {}).get(m, 0)
            y2025 = global_annual_monthly[sku_id].get(2025, {}).get(m, 0)
            active = [v for v in [y2024, y2025] if v > 0]
            monthly[m] = {
                '2024': y2024,
                '2025': y2025,
                'max': max_or_zero(active),
                'avg': avg(active),
            }

        total_demand = sum(monthly[m]['max'] for m in forecast_months)

        # Buffer: avg of Feb-Apr globally
        buf_monthly = {}
        total_buffer = 0
        for m in buffer_months:
            active = [
                global_annual_monthly[sku_id][yr][m]
                for yr in global_annual_monthly[sku_id]
                if global_annual_monthly[sku_id][yr][m] > 0
            ]
            b_avg = avg(active)
            buf_monthly[m] = {'values': active, 'avg': b_avg}
            total_buffer += b_avg

        current_global = (
            sum(stock_index.get(sku_id, {}).values())
            + supplier_stock_index.get(sku_id, {}).get('china', 0)
            + supplier_stock_index.get(sku_id, {}).get('canada', 0)
        )
        total_needed = total_demand + total_buffer
        global_gap = max(0, total_needed - current_global)

        # Per-region data
        reg_data = {}
        for region in consumer_regions:
            source_wh = 'CA' if region == 'Amazon_CA_FBA' else region
            reg_monthly = {}
            for m in forecast_months:
                active = [
                    wh_annual_monthly[sku_id][source_wh][yr][m]
                    for yr in wh_annual_monthly[sku_id][source_wh]
                    if wh_annual_monthly[sku_id][source_wh][yr][m] > 0
                ]
                reg_monthly[m] = max_or_zero(active)
            reg_demand = sum(reg_monthly[m] for m in forecast_months)
            reg_buf = 0
            for m in buffer_months:
                active = [
                    wh_annual_monthly[sku_id][source_wh][yr][m]
                    for yr in wh_annual_monthly[sku_id][source_wh]
                    if wh_annual_monthly[sku_id][source_wh][yr][m] > 0
                ]
                reg_buf += avg(active)
            reg_data[region] = {
                'source_wh': source_wh,
                'monthly': reg_monthly,
                'demand': reg_demand,
                'buffer': reg_buf,
                'current_stock': stock_index.get(sku_id, {}).get(region, 0),
            }

        # Transfers: track how much flows INTO each destination
        transfers = []
        transfer_in = defaultdict(float)

        for dest_wh in ['Amazon_US_FBA', 'Amazon_CA_FBA', 'AU', 'EU']:
            source_wh = 'CA' if dest_wh == 'Amazon_CA_FBA' else dest_wh
            if dest_wh in consumer_regions:
                reg_demand = reg_data[dest_wh]['demand']
            else:
                reg_demand = sum(
                    max_or_zero([
                        wh_annual_monthly[sku_id][source_wh][yr][m]
                        for yr in wh_annual_monthly[sku_id][source_wh]
                        if wh_annual_monthly[sku_id][source_wh][yr][m] > 0
                    ])
                    for m in forecast_months
                )
            curr = stock_index.get(sku_id, {}).get(dest_wh, 0)

            if reg_demand > curr:
                gap = reg_demand - curr
                if dest_wh == 'Amazon_US_FBA':
                    hbg = stock_index.get(sku_id, {}).get('HBG', 0)
                    sli = stock_index.get(sku_id, {}).get('SLI', 0)
                    if hbg > 0:
                        pull = min(gap, hbg)
                        transfers.append({
                            'source': 'HBG', 'dest': 'Amazon_US_FBA', 'qty': pull,
                            'reason': f'US FBA needs {int(reg_demand):,}; has {int(curr):,}; HBG has {int(hbg):,} available'
                        })
                        transfer_in['Amazon_US_FBA'] += pull
                        gap -= pull
                    if gap > 0 and sli > 0:
                        pull = min(gap, sli)
                        transfers.append({
                            'source': 'SLI', 'dest': 'Amazon_US_FBA', 'qty': pull,
                            'reason': f'After HBG still short {int(gap):,}; SLI has {int(sli):,} available'
                        })
                        transfer_in['Amazon_US_FBA'] += pull

                elif dest_wh == 'Amazon_CA_FBA':
                    ca = stock_index.get(sku_id, {}).get('CA', 0)
                    if ca > 0:
                        pull = min(gap, ca)
                        transfers.append({
                            'source': 'CA Hub', 'dest': 'Amazon_CA_FBA', 'qty': pull,
                            'reason': f'CA FBA needs {int(reg_demand):,}; has {int(curr):,}; CA Hub has {int(ca):,} available'
                        })
                        transfer_in['Amazon_CA_FBA'] += pull

                elif dest_wh == 'AU':
                    if is_j:
                        uk = stock_index.get(sku_id, {}).get('UK', 0)
                        if uk > 0:
                            pull = min(gap, uk)
                            transfers.append({
                                'source': 'UK', 'dest': 'AU', 'qty': pull,
                                'reason': f'AU needs {int(reg_demand):,}; has {int(curr):,}; UK→AU permitted for journals; UK has {int(uk):,}'
                            })
                            transfer_in['AU'] += pull
                    # Cards: no UK→AU transfer; must print direct

                elif dest_wh == 'EU':
                    uk = stock_index.get(sku_id, {}).get('UK', 0)
                    if uk > 0:
                        pull = min(gap, uk)
                        transfers.append({
                            'source': 'UK', 'dest': 'EU', 'qty': pull,
                            'reason': f'EU needs {int(reg_demand):,}; UK has {int(uk):,} available'
                        })
                        transfer_in['EU'] += pull

        # Print distribution: fill post-transfer deficits in each region
        print_alloc = {}
        if global_gap > 0:
            remaining = global_gap
            for dest in ['Amazon_US_FBA', 'Amazon_CA_FBA', 'AU']:
                if dest not in consumer_regions:
                    continue
                rd = reg_data[dest]
                curr = stock_index.get(sku_id, {}).get(dest, 0)
                post_transfer = curr + transfer_in[dest]
                deficit = max(0, rd['demand'] - post_transfer)
                if deficit > 0 and remaining > 0:
                    alloc = min(deficit, remaining)
                    print_alloc[dest] = int(alloc)
                    remaining -= alloc

        sku_data[sku_id] = {
            'name': sku_name,
            'is_journal': is_j,
            'monthly': monthly,
            'buf_monthly': buf_monthly,
            'total_demand': total_demand,
            'total_buffer': total_buffer,
            'current_global': current_global,
            'total_needed': total_needed,
            'global_gap': global_gap,
            'reg_data': reg_data,
            'transfers': transfers,
            'transfer_in': dict(transfer_in),
            'print_alloc': print_alloc,
        }

    # ── SUMMARY STATS ───────────────────────────────────────────────────────

    skus_needing_print = [s for s in skus if sku_data[s['sku_id']]['global_gap'] > 0]
    total_print_units = sum(sku_data[s['sku_id']]['global_gap'] for s in skus_needing_print)
    total_transfer_moves = sum(len(sku_data[s['sku_id']]['transfers']) for s in skus)

    # ── BUILD REPORT ────────────────────────────────────────────────────────

    md = "# Inventory Master Plan: May 2026 – January 2027\n\n"
    md += "*Generated: May 3, 2026 · 9-month active period + 90-day carry-over buffer · 8 SKUs · 10 warehouses*\n\n"
    md += "---\n\n"

    # ── EXECUTIVE SUMMARY ───────────────────────────────────────────────────
    md += "## Executive Summary\n\n"
    md += (
        "This plan ensures we have the right stock, in the right place, "
        "from **May 2026 through April 2027**. It covers the full Q4 peak season "
        "and carries enough buffer into Q1 2027 that we won't touch zero before the "
        "next order cycle.\n\n"
    )

    md += "### Actions Required\n\n"
    if skus_needing_print:
        md += "**Print Orders (place now):**\n\n"
        for sku in skus_needing_print:
            sd = sku_data[sku['sku_id']]
            md += f"- **{sd['name']}** — order **{int(sd['global_gap']):,} units**\n"
        md += "\n"

    md += f"**Warehouse Transfers ({total_transfer_moves} moves — execute before September):**\n"
    md += "Stock must move from regional hubs into FBA now. FBA processing takes 2–4 weeks; "
    md += "if transfers happen in October the stock won't be live for November peak.\n\n"

    md += "### Plan at a Glance\n\n"
    md += "| | |\n| :--- | :--- |\n"
    md += f"| Active selling period | May 2026 – Jan 2027 (9 months) |\n"
    md += f"| Buffer carry-over | Feb – Apr 2027 (90 days) |\n"
    md += f"| SKUs in plan | {len(skus)} |\n"
    md += f"| New print orders | {len(skus_needing_print)} SKUs · {int(total_print_units):,} units total |\n"
    md += f"| Warehouse transfers | {total_transfer_moves} moves |\n"
    md += f"| Demand model | Historical max per month (stress-test) |\n"
    md += f"| Buffer model | Historical average of Feb + Mar + Apr |\n\n"
    md += "---\n\n"

    # ── SECTION 1: METHODOLOGY ──────────────────────────────────────────────
    md += "## Section 1: How the Numbers Were Calculated\n\n"

    md += "### The Question We're Answering\n\n"
    md += (
        "How much inventory do we need, globally and per region, to get through Q4 "
        "without stockouts — and still have 90 days of stock left in January before "
        "we place our next order?\n\n"
    )

    md += "### Step 1 — Demand Forecast: Always Use the Maximum\n\n"
    md += (
        "For each SKU and each month, we look at 2024 sales and 2025 sales and take "
        "the **higher number**. We never average them. The logic: if we've ever sold "
        "that many in a given month, we need to be ready to sell that many again. "
        "This is especially important for Q4 where one strong November can define the year.\n\n"
    )

    # Worked example: first SKU, October
    ex = skus[0]
    ex_id = ex['sku_id']
    ex_sd = sku_data[ex_id]
    oct = ex_sd['monthly'][10]
    md += f"**Example — {ex_sd['name']}, October:**\n\n"
    md += f"| | Units |\n| :--- | ---: |\n"
    md += f"| 2024 October actual | {int(oct['2024']):,} |\n"
    md += f"| 2025 October actual | {int(oct['2025']):,} |\n"
    md += f"| **We plan for** | **{int(oct['max']):,}** ← the higher of the two |\n\n"
    md += "We do this for every month May through January, then sum the 9 months. That total is the demand forecast.\n\n"

    md += "### Step 2 — Safety Buffer: 90 Days Left After January\n\n"
    md += (
        "We don't want to start February with zero stock. The buffer is the average "
        "of what we historically sell in February, March, and April — the slow months "
        "right after peak season. That amount must still be sitting in the warehouse "
        "on February 1st.\n\n"
    )
    md += f"**Example — {ex_sd['name']} buffer:**\n\n"
    md += "| Buffer Month | Historical Sales | Average |\n"
    md += "| :--- | :--- | ---: |\n"
    for m in buffer_months:
        bd = ex_sd['buf_monthly'][m]
        vals = ', '.join(f"{int(v):,}" for v in bd['values']) if bd['values'] else 'no data'
        n = len(bd['values'])
        avg_str = f"**{int(bd['avg']):,}**" if n > 0 else "0"
        md += f"| {month_short[m]} | {vals} | {avg_str} |\n"
    md += f"| **Total 90-day buffer** | | **{int(ex_sd['total_buffer']):,}** |\n\n"

    md += "### Step 3 — The Gap: How Much to Print\n\n"
    md += "```\nTotal Needed  =  9-Month Demand  +  90-Day Buffer\nPrint Order   =  Total Needed  −  (Current Stock + Supplier Stock)\n```\n\n"
    md += f"**Example — {ex_sd['name']}:**\n\n"
    md += f"| | Units |\n| :--- | ---: |\n"
    md += f"| 9-Month Demand | {int(ex_sd['total_demand']):,} |\n"
    md += f"| 90-Day Buffer | {int(ex_sd['total_buffer']):,} |\n"
    md += f"| **Total Needed** | **{int(ex_sd['total_needed']):,}** |\n"
    md += f"| Current Stock + Supplier | {int(ex_sd['current_global']):,} |\n"
    gap_ex = ex_sd['global_gap']
    result_str = f"**ORDER {int(gap_ex):,} units**" if gap_ex > 0 else f"**Surplus — no print needed**"
    md += f"| **Gap → Decision** | {result_str} |\n\n"

    md += "### Step 4 — Regional Routing Rules\n\n"
    md += "Having enough stock globally isn't enough — it has to be positioned where sales happen.\n\n"
    md += "| Channel | Source | Rule |\n"
    md += "| :--- | :--- | :--- |\n"
    md += "| Amazon US FBA | HBG → FBA, then SLI → FBA | Pull from hubs; print fills remaining gap |\n"
    md += "| Amazon CA FBA | CA Hub → CA FBA | Pull from CA hub; print fills remaining gap |\n"
    md += "| AU (Journals) | UK → AU | UK→AU transfer permitted for journals |\n"
    md += "| AU (Cards) | China printer → AU direct | UK→AU blocked for cards; must print new |\n"
    md += "| EU | UK surplus → EU | Topped up from UK only if surplus exists |\n\n"
    md += "---\n\n"

    # ── SECTION 2: FULL DEMAND BREAKDOWN ────────────────────────────────────
    md += "## Section 2: Demand Breakdown by SKU\n\n"
    md += (
        "For every SKU: the month-by-month comparison of 2024 vs 2025 actual sales, "
        "which year's number was used in the forecast, and the buffer calculation. "
        "This is the full math behind every number in this plan.\n\n"
    )

    for sku in skus:
        sku_id = sku['sku_id']
        sd = sku_data[sku_id]

        md += f"### {sd['name']} `{sku_id}`\n\n"

        # Monthly demand table
        md += "**Monthly Demand Forecast (Global — all warehouses combined)**\n\n"
        md += "| Month | 2024 Actual | 2025 Actual | Max Used | Running Total |\n"
        md += "| :--- | ---: | ---: | ---: | ---: |\n"
        running = 0
        for m in forecast_months:
            md_row = sd['monthly'][m]
            running += md_row['max']
            y24 = f"{int(md_row['2024']):,}" if md_row['2024'] > 0 else "—"
            y25 = f"{int(md_row['2025']):,}" if md_row['2025'] > 0 else "—"
            chosen = f"**{int(md_row['max']):,}**" if md_row['max'] > 0 else "—"
            winner = " ← 2024 peak" if md_row['2024'] > md_row['2025'] and md_row['2024'] > 0 else (" ← 2025 peak" if md_row['2025'] > md_row['2024'] and md_row['2025'] > 0 else "")
            md += f"| {month_names[m]} | {y24} | {y25} | {chosen}{winner} | {int(running):,} |\n"
        md += f"| **9-Month Total** | | | | **{int(sd['total_demand']):,}** |\n\n"

        # Buffer table
        md += "**90-Day Safety Buffer (Feb – Apr historical average)**\n\n"
        md += "| Month | 2024 | 2025 | Average Used |\n"
        md += "| :--- | ---: | ---: | ---: |\n"
        for m in buffer_months:
            bd = sd['buf_monthly'][m]
            y24_b = int(global_annual_monthly[sku_id].get(2024, {}).get(m, 0))
            y25_b = int(global_annual_monthly[sku_id].get(2025, {}).get(m, 0))
            y24_str = f"{y24_b:,}" if y24_b > 0 else "—"
            y25_str = f"{y25_b:,}" if y25_b > 0 else "—"
            md += f"| {month_short[m]} | {y24_str} | {y25_str} | **{int(bd['avg']):,}** |\n"
        md += f"| **Total Buffer** | | | **{int(sd['total_buffer']):,}** |\n\n"

        # Global check
        surplus = sd['current_global'] - sd['total_needed']
        if sd['global_gap'] > 0:
            verdict = f"🖨️ **PRINT {int(sd['global_gap']):,} UNITS** — supply falls short by {int(sd['global_gap']):,}"
        else:
            verdict = f"✅ **No print needed** — surplus of {int(-surplus):,} units"
        md += f"**Stock Check:** {int(sd['total_demand']):,} demand + {int(sd['total_buffer']):,} buffer "
        md += f"= **{int(sd['total_needed']):,} needed** vs **{int(sd['current_global']):,} available** → {verdict}\n\n"
        md += "---\n\n"

    # ── SECTION 3: PRINT ORDERS ──────────────────────────────────────────────
    md += "## Section 3: New Print Orders\n\n"

    if not skus_needing_print:
        md += "✅ **No new print orders required.** Global supply covers all demand plus the 90-day buffer for every SKU.\n\n"
    else:
        md += "The following SKUs have a global supply shortfall. Print runs should be placed immediately.\n\n"
        for sku in skus_needing_print:
            sku_id = sku['sku_id']
            sd = sku_data[sku_id]

            md += f"### 🖨️ {sd['name']} — Print {int(sd['global_gap']):,} Units\n\n"
            md += "**Why this is needed:**\n\n"
            md += f"| | Units |\n| :--- | ---: |\n"
            md += f"| Total requirement (demand + buffer) | {int(sd['total_needed']):,} |\n"
            md += f"| Available supply (stock + supplier) | {int(sd['current_global']):,} |\n"
            md += f"| **Shortfall → Print order** | **{int(sd['global_gap']):,}** |\n\n"

            md += "**Where to ship (direct from printer — do not route through hubs):**\n\n"
            md += "| Destination | Units | How we got this number |\n"
            md += "| :--- | ---: | :--- |\n"
            total_alloc = 0
            for dest, qty in sd['print_alloc'].items():
                rd = sd['reg_data'].get(dest, {})
                curr = stock_index.get(sku_id, {}).get(dest, 0)
                t_in = sd['transfer_in'].get(dest, 0)
                post = curr + t_in
                deficit = rd.get('demand', 0) - post
                note = ""
                if dest == 'AU' and not is_journal(sku_id):
                    note = " — UK→AU blocked for cards; must print direct to AU"
                md += f"| {dest.replace('_', ' ')} | **{qty:,}** | Region demand: {int(rd.get('demand',0)):,} · stock after transfers: {int(post):,} · deficit: {int(deficit):,}{note} |\n"
                total_alloc += qty
            remainder = int(sd['global_gap']) - total_alloc
            if remainder > 0:
                md += f"| Supplier reserve | **{remainder:,}** | Hold at supplier pending final regional allocation |\n"
            md += "\n"
    md += "---\n\n"

    # ── SECTION 4: TRANSFER PLAN ─────────────────────────────────────────────
    md += "## Section 4: Warehouse Transfer Plan\n\n"
    md += (
        "These transfers move existing inventory from holding warehouses into active "
        "selling channels. **Execute all transfers before September 1st** — FBA inbound "
        "processing takes 2–4 weeks, and November is when velocity spikes.\n\n"
    )
    md += "> **Routing rule reminder:** UK → AU is permitted for Journals only. "
    md += "Cards cannot transfer UK → AU and must receive new print stock direct from supplier.\n\n"

    md += "| SKU | From → To | Units to Move | Stock at Source | Demand at Dest | Why |\n"
    md += "| :--- | :--- | ---: | ---: | ---: | :--- |\n"
    for sku in skus:
        sku_id = sku['sku_id']
        sd = sku_data[sku_id]
        for t in sd['transfers']:
            src_stock = int(stock_index.get(sku_id, {}).get(
                t['source'].replace(' Hub', ''), 0
            ))
            dest_region = t['dest']
            dest_demand = int(sd['reg_data'].get(dest_region, {}).get('demand', 0))
            md += (
                f"| {sd['name']} | {t['source']} → {t['dest'].replace('_', ' ')} "
                f"| **{int(t['qty']):,}** | {src_stock:,} | {dest_demand:,} | {t['reason']} |\n"
            )
    md += "\n---\n\n"

    # ── SECTION 5: ROLLING DEPLETION ─────────────────────────────────────────
    md += "## Section 5: Rolling Depletion Forecast by Region\n\n"
    md += (
        "Month-by-month stock burn for each key selling region, assuming all transfers "
        "and print runs above are executed. Every region should end January 2027 with "
        "a positive buffer balance — that carry-over stock is what keeps us live through "
        "April 2027 while the next order cycle completes.\n\n"
    )
    md += (
        "> **How to read this:** Starting stock = demand + buffer (what the region "
        "needs to have after all transfers land). Each month we subtract max projected "
        "sales. January ending balance = the 90-day buffer. It should never be zero.\n\n"
    )

    for sku in skus:
        sku_id = sku['sku_id']
        sd = sku_data[sku_id]

        if not any(sd['reg_data'][r]['demand'] > 0 for r in consumer_regions):
            continue

        md += f"### {sd['name']}\n\n"

        for region in consumer_regions:
            rd = sd['reg_data'][region]
            if rd['demand'] == 0:
                continue

            source_wh = rd['source_wh']
            reg_buffer = rd['buffer']
            total_reg_demand = rd['demand']
            starting_stock = total_reg_demand + reg_buffer

            # Buffer breakdown string
            buf_parts = []
            for m in buffer_months:
                active = [
                    wh_annual_monthly[sku_id][source_wh][yr][m]
                    for yr in wh_annual_monthly[sku_id][source_wh]
                    if wh_annual_monthly[sku_id][source_wh][yr][m] > 0
                ]
                if active:
                    buf_parts.append(f"{month_short[m]} avg {int(avg(active)):,}")
            buf_note = " + ".join(buf_parts) + f" = **{int(reg_buffer):,} units**" if buf_parts else f"**{int(reg_buffer):,} units**"

            md += f"#### {region.replace('_', ' ')}\n\n"
            md += (
                f"*Required starting stock: **{int(starting_stock):,} units** "
                f"({int(total_reg_demand):,} demand + {int(reg_buffer):,} buffer — {buf_note})*\n\n"
            )
            md += "| Month | Max Projected Sales | Ending Stock | Weeks of Cover |\n"
            md += "| :--- | ---: | ---: | ---: |\n"

            cumulative = 0
            for i, m in enumerate(forecast_months):
                m_max = rd['monthly'][m]
                cumulative += m_max
                ending = starting_stock - cumulative

                # Weeks of cover = ending stock / weekly run rate of next month
                next_i = i + 1
                if next_i < len(forecast_months):
                    next_m = forecast_months[next_i]
                    next_rate = rd['monthly'][next_m]
                else:
                    next_rate = reg_buffer / 3  # avg monthly during buffer period

                if next_rate > 0:
                    weekly_rate = next_rate / (days_in_month.get(m, 30) / 7)
                    woc = ending / weekly_rate if weekly_rate > 0 else 999
                    woc_str = f"{woc:.1f}w"
                else:
                    woc_str = "—"

                low_flag = " ⚠️" if (ending < reg_buffer * 0.5 and m != 1) else ""
                md += f"| {month_names[m]} | {int(m_max):,} | **{int(ending):,}**{low_flag} | {woc_str} |\n"

            md += f"\n> **Jan 2027 buffer: {int(reg_buffer):,} units** — carry-over stock covering Feb–Apr 2027\n\n"

    md += "---\n\n"

    # ── SECTION 6: MASTER ACTION CHECKLIST ──────────────────────────────────
    md += "## Section 6: Master Action Checklist\n\n"
    md += "Everything that needs to happen, in priority order.\n\n"

    md += "### 🖨️ Print Orders (Place Now)\n\n"
    if skus_needing_print:
        for sku in skus_needing_print:
            sku_id = sku['sku_id']
            sd = sku_data[sku_id]
            md += f"- [ ] **{sd['name']}** — order **{int(sd['global_gap']):,} units** from supplier\n"
            for dest, qty in sd['print_alloc'].items():
                md += f"  - Ship **{qty:,}** direct to **{dest.replace('_', ' ')}**\n"
            remainder = int(sd['global_gap']) - sum(sd['print_alloc'].values())
            if remainder > 0:
                md += f"  - Hold **{remainder:,}** at supplier pending allocation confirmation\n"
    else:
        md += "- ✅ No print orders required\n"
    md += "\n"

    md += "### 📦 Warehouse Transfers (Complete Before September 1st)\n\n"
    for sku in skus:
        sku_id = sku['sku_id']
        sd = sku_data[sku_id]
        if sd['transfers']:
            md += f"**{sd['name']}:**\n"
            for t in sd['transfers']:
                md += f"- [ ] {t['source']} → {t['dest'].replace('_', ' ')}: **{int(t['qty']):,} units**\n"
            md += "\n"

    md += "### 📋 Verification Checkpoints\n\n"
    md += "- [ ] Confirm print order lead times — Kids Journal and Know Me Cards must arrive before September\n"
    md += "- [ ] Create FBA inbound shipments in Seller Central and confirm tracking\n"
    md += "- [ ] Verify UK → AU journal shipments cleared customs and landed at AU warehouse\n"
    md += "- [ ] Re-run this plan in August to catch any demand surprises before Q4 locks in\n"
    md += "- [ ] Check this plan again in November — if Dec sales are running above forecast, flag early\n\n"

    md += "---\n\n"
    md += "*Plan generated May 3, 2026. Re-run monthly to stay current. Source: `.tmp/data.json`*\n"

    # Write to both .tmp (working copy) and docs/ (git-tracked, boss-visible)
    tmp_path = os.path.join(PROJECT_ROOT, '.tmp/massive_report.md')
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
