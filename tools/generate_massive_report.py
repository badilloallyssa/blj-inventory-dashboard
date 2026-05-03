
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

    wh_ann    = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
    global_ann = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

    for row in sales:
        d = parse_date(row.get('date', ''))
        if d is None:
            continue
        sku   = row.get('sku_id', '').strip()
        wh    = row.get('warehouse', '').strip()
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

    skus      = [s for s in data['config']['skus'] if s.get('active', True)]
    stock_idx = {
        e['sku_id']: {k: float(v) for k, v in e.get('stock', {}).items()}
        for e in data.get('current_stock', [])
    }
    sup_detail = {
        e['sku_id']: {
            'canada': float(e.get('canada_supplier', 0)),
            'china':  float(e.get('china_supplier',  0)),
        }
        for e in data.get('supplier_stock', [])
    }

    # 7 modelled channels:
    #   US_Shopify  = HBG+SLI+SAV+KCM combined  (sales warehouse: 'US')
    #   CA_Shopify  = CA hub                     (sales warehouse: 'CA')
    #   Amazon_CA_FBA is new — proxy demand from 'CA' warehouse history
    all_channels = ['Amazon_US_FBA', 'Amazon_CA_FBA', 'US_Shopify', 'CA_Shopify', 'UK', 'EU', 'AU']

    source_wh = {
        'Amazon_US_FBA': 'Amazon_US_FBA',
        'Amazon_CA_FBA': 'CA',
        'US_Shopify':    'US',
        'CA_Shopify':    'CA',
        'UK':            'UK',
        'EU':            'EU',
        'AU':            'AU',
    }

    US_HUB_KEYS = ['HBG', 'SLI', 'SAV', 'KCM']

    def channel_stock(sid, region):
        if region == 'US_Shopify':
            return sum(stock_idx.get(sid, {}).get(h, 0) for h in US_HUB_KEYS)
        elif region == 'CA_Shopify':
            return stock_idx.get(sid, {}).get('CA', 0)
        else:
            return stock_idx.get(sid, {}).get(region, 0)

    def wh_demand(sku_id, wh):
        return sum(
            max_or_zero([wh_ann[sku_id][wh][yr][m]
                         for yr in wh_ann[sku_id][wh]
                         if wh_ann[sku_id][wh][yr][m] > 0])
            for m in forecast_months
        )

    def wh_monthly(sku_id, wh):
        return {
            m: max_or_zero([wh_ann[sku_id][wh][yr][m]
                            for yr in wh_ann[sku_id][wh]
                            if wh_ann[sku_id][wh][yr][m] > 0])
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
        return total / len(buffer_months), parts   # 30-day avg, not sum

    # ── PRE-COMPUTE ALL SKU DATA ─────────────────────────────────────────────

    sku_data = {}

    for sku in skus:
        sid  = sku['sku_id']
        name = sku['sku_name']
        is_j = is_journal(sid)

        g_monthly = {}
        for m in forecast_months + buffer_months:
            y24    = global_ann[sid].get(2024, {}).get(m, 0)
            y25    = global_ann[sid].get(2025, {}).get(m, 0)
            active = [v for v in [y24, y25] if v > 0]
            g_monthly[m] = {'2024': y24, '2025': y25,
                             'max': max_or_zero(active), 'avg': avg(active)}

        ch = {}
        for region in all_channels:
            swh             = source_wh[region]
            dem             = wh_demand(sid, swh)
            curr            = channel_stock(sid, region)
            buf_total, buf_parts = wh_buffer(sid, swh)
            ch[region] = {
                'source_wh': swh,
                'demand':    dem,
                'monthly':   wh_monthly(sid, swh),
                'current':   curr,
                'deficit':   max(0.0, dem + buf_total - curr),
                'buffer':    buf_total,
                'buf_parts': buf_parts,
            }

        g_buf_parts = {}
        g_buf_total = 0.0
        for m in buffer_months:
            vals = [global_ann[sid][yr][m]
                    for yr in global_ann[sid]
                    if global_ann[sid][yr][m] > 0]
            a = avg(vals)
            g_buf_parts[m] = {'vals': vals, 'avg': a}
            g_buf_total    += a
        g_buf_total /= len(buffer_months)
        g_demand     = sum(g_monthly[m]['max'] for m in forecast_months)

        canada_sup = sup_detail.get(sid, {}).get('canada', 0)
        china_sup  = sup_detail.get(sid, {}).get('china',  0)
        g_stock    = sum(stock_idx.get(sid, {}).values()) + canada_sup + china_sup

        # ── Step 1: UK transfers (UK→AU journals; UK→EU all) ──────────────────
        uk_stock   = stock_idx.get(sid, {}).get('UK', 0)
        uk_surplus = max(0.0, uk_stock - ch['UK']['demand'] - ch['UK']['buffer'])

        transfers   = []
        incoming    = defaultdict(float)
        outgoing_uk = 0.0

        if is_j:
            au_def = max(0.0, ch['AU']['demand'] + ch['AU']['buffer'] - ch['AU']['current'])
            if au_def > 0 and uk_surplus > 0:
                pull = min(au_def, uk_surplus)
                transfers.append({
                    'source': 'UK', 'dest': 'AU', 'qty': pull,
                    'reason': (f"AU needs {int(ch['AU']['demand'] + ch['AU']['buffer']):,} "
                               f"(demand + buffer); AU has {int(ch['AU']['current']):,}; "
                               f"deficit {int(au_def):,}; UK surplus {int(uk_surplus):,}")
                })
                incoming['AU'] += pull
                outgoing_uk    += pull
                uk_surplus     -= pull

        eu_def = max(0.0, ch['EU']['demand'] + ch['EU']['buffer'] - ch['EU']['current'])
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

        # ── Step 2: Start stock after UK transfers ─────────────────────────────
        start_stock = {}
        for region in all_channels:
            if region == 'UK':
                start_stock[region] = uk_stock - outgoing_uk
            else:
                start_stock[region] = ch[region]['current'] + incoming.get(region, 0)

        # ── Step 3: Supplier allocation ────────────────────────────────────────
        # Canada supplier → CA Shopify first (Shopify priority), then CA FBA
        # China supplier  → US FBA first, then other deficit channels
        supplier_alloc = defaultdict(float)

        if canada_sup > 0:
            pool = canada_sup
            for region in ['CA_Shopify', 'Amazon_CA_FBA']:
                if pool <= 0:
                    break
                need = max(0.0, ch[region]['demand'] + ch[region]['buffer'] - start_stock[region])
                if need > 0:
                    alloc = min(pool, need)
                    supplier_alloc[region] += alloc
                    start_stock[region]    += alloc
                    incoming[region]       += alloc
                    pool -= alloc

        if china_sup > 0:
            pool = china_sup
            for region in ['Amazon_US_FBA', 'AU', 'EU', 'Amazon_CA_FBA', 'US_Shopify']:
                if pool <= 0:
                    break
                need = max(0.0, ch[region]['demand'] + ch[region]['buffer'] - start_stock[region])
                if need > 0:
                    alloc = min(pool, need)
                    supplier_alloc[region] += alloc
                    start_stock[region]    += alloc
                    incoming[region]       += alloc
                    pool -= alloc

        # ── Step 4: Global gap check ────────────────────────────────────────────
        # All 7 channels are included: US_Shopify stock = HBG+SLI+SAV+KCM,
        # CA_Shopify stock = CA hub. No separate hub_total needed.
        total_need  = sum(ch[r]['demand'] + ch[r]['buffer'] for r in all_channels)
        total_avail = sum(start_stock[r] for r in all_channels)
        is_globally_short = total_avail < total_need

        # ── Step 4a: PRINT MODE ─────────────────────────────────────────────────
        # Not enough stock globally — print to cover each channel's specific deficit.
        # Prints ship direct from factory to destination; no hub→FBA transfers.
        print_alloc = {}
        if is_globally_short:
            for region in all_channels:
                residual = max(0.0, ch[region]['demand'] + ch[region]['buffer']
                               - start_stock[region])
                if residual > 0:
                    print_alloc[region] = int(residual)
                    start_stock[region] += residual
                    incoming[region]    += residual

        total_print = sum(print_alloc.values())
        is_printing  = total_print > 0

        # ── Step 4b: REPOSITION MODE ────────────────────────────────────────────
        # Globally sufficient — transfer hub SURPLUS (above Shopify demand+buffer) to FBA.
        # Hubs keep enough for all Shopify demand + 30-day buffer; only the excess moves.
        outgoing_us_hub = 0.0
        outgoing_ca_hub = 0.0

        if not is_globally_short:
            us_shopify_need = ch['US_Shopify']['demand'] + ch['US_Shopify']['buffer']
            us_hub_surplus  = max(0.0, start_stock['US_Shopify'] - us_shopify_need)

            ca_shopify_need = ch['CA_Shopify']['demand'] + ch['CA_Shopify']['buffer']
            ca_hub_surplus  = max(0.0, start_stock['CA_Shopify'] - ca_shopify_need)

            # US hub surplus → Amazon US FBA
            us_fba_gap = max(0.0, ch['Amazon_US_FBA']['demand'] + ch['Amazon_US_FBA']['buffer']
                             - start_stock['Amazon_US_FBA'])
            if us_fba_gap > 0 and us_hub_surplus > 0:
                pull = min(us_fba_gap, us_hub_surplus)
                transfers.append({
                    'source': 'US Hub', 'dest': 'Amazon_US_FBA', 'qty': pull,
                    'reason': (
                        f"US hubs (HBG/SLI/SAV/KCM) have {int(start_stock['US_Shopify']):,}; "
                        f"Shopify needs {int(us_shopify_need):,} (demand + buffer); "
                        f"surplus {int(us_hub_surplus):,}; US FBA gap {int(us_fba_gap):,}")
                })
                start_stock['Amazon_US_FBA'] += pull
                start_stock['US_Shopify']    -= pull
                incoming['Amazon_US_FBA']    += pull
                outgoing_us_hub              += pull
                us_hub_surplus               -= pull

            # CA hub surplus → Amazon CA FBA
            ca_fba_gap = max(0.0, ch['Amazon_CA_FBA']['demand'] + ch['Amazon_CA_FBA']['buffer']
                             - start_stock['Amazon_CA_FBA'])
            if ca_fba_gap > 0 and ca_hub_surplus > 0:
                pull = min(ca_fba_gap, ca_hub_surplus)
                transfers.append({
                    'source': 'CA Hub', 'dest': 'Amazon_CA_FBA', 'qty': pull,
                    'reason': (
                        f"CA hub has {int(start_stock['CA_Shopify']):,}; "
                        f"CA Shopify needs {int(ca_shopify_need):,} (demand + buffer); "
                        f"surplus {int(ca_hub_surplus):,}; CA FBA gap {int(ca_fba_gap):,}")
                })
                start_stock['Amazon_CA_FBA'] += pull
                start_stock['CA_Shopify']    -= pull
                incoming['Amazon_CA_FBA']    += pull
                outgoing_ca_hub              += pull

        # ── Step 5: Top-up prints ───────────────────────────────────────────────
        # Globally sufficient but a channel still has a gap (blocked route or no hub surplus).
        top_up_print = {}
        if not is_globally_short:
            for region in all_channels:
                residual = max(0.0, ch[region]['demand'] + ch[region]['buffer']
                               - start_stock[region])
                if residual > 0:
                    top_up_print[region] = int(residual)
                    start_stock[region] += residual
                    incoming[region]    += residual

        total_top_up = sum(top_up_print.values())

        sku_data[sid] = {
            'name': name, 'is_journal': is_j,
            'g_monthly': g_monthly, 'g_buf_parts': g_buf_parts,
            'g_demand': g_demand, 'g_buf_total': g_buf_total, 'g_stock': g_stock,
            'canada_sup': canada_sup, 'china_sup': china_sup,
            'ch': ch,
            'transfers': transfers, 'incoming': dict(incoming),
            'supplier_alloc': dict(supplier_alloc),
            'outgoing_uk': outgoing_uk,
            'outgoing_us_hub': outgoing_us_hub,
            'outgoing_ca_hub': outgoing_ca_hub,
            'print_alloc': print_alloc, 'total_print': total_print,
            'is_printing': is_printing,
            'top_up_print': top_up_print, 'total_top_up': total_top_up,
            'start_stock': start_stock,
            'total_need': total_need, 'total_avail': total_avail,
        }

    # ── REPORT STATS ────────────────────────────────────────────────────────
    printing_skus     = [s for s in skus if sku_data[s['sku_id']]['is_printing']]
    total_print_units = sum(sku_data[s['sku_id']]['total_print'] for s in printing_skus)
    top_up_skus       = [s for s in skus if sku_data[s['sku_id']]['total_top_up'] > 0]
    total_top_up_all  = sum(sku_data[s['sku_id']]['total_top_up'] for s in top_up_skus)
    total_transfers   = sum(len(sku_data[s['sku_id']]['transfers']) for s in skus)

    # ── BUILD MARKDOWN ───────────────────────────────────────────────────────

    md  = "# Inventory Master Plan: May 2026 – January 2027\n\n"
    md += "*Generated: May 3, 2026 · 9-month active period + 30-day carry-over buffer · 8 SKUs · 10 warehouses*\n\n"
    md += "---\n\n"

    # ── EXECUTIVE SUMMARY ───────────────────────────────────────────────────
    md += "## Executive Summary\n\n"
    md += ("This plan covers every SKU from **May 2026 through January 2027** across all channels — "
           "Amazon US FBA, Amazon CA FBA, US Shopify (HBG/SLI/SAV/KCM), CA Shopify, UK, EU, and AU. "
           "US hubs reserve stock for Shopify demand first; only the surplus above Shopify needs can "
           "transfer to FBA. Each channel ends January with 30 days of carry-over stock.\n\n")

    md += "### What Needs to Happen Now\n\n"

    if printing_skus:
        md += "**🖨️ New Print Orders:**\n\n"
        for s in printing_skus:
            sd = sku_data[s['sku_id']]
            alloc_str = ', '.join(
                f"{qty:,} → {dest.replace('_',' ')}"
                for dest, qty in sd['print_alloc'].items()
            )
            md += f"- **{sd['name']}**: print **{sd['total_print']:,} units** ({alloc_str}) — ship direct from printer\n"
        md += "\n"

    hub_transfer_skus = [s for s in skus if not sku_data[s['sku_id']]['is_printing']
                         and any(t['source'] in ('US Hub', 'CA Hub')
                                 for t in sku_data[s['sku_id']]['transfers'])]
    if hub_transfer_skus:
        md += "**📦 Hub→FBA Transfers** *(no print run needed — reposition hub surplus to FBA)*:\n\n"
        for s in hub_transfer_skus:
            sd = sku_data[s['sku_id']]
            t_str = ', '.join(
                f"{int(t['qty']):,} {t['source']}→{t['dest'].replace('_',' ')}"
                for t in sd['transfers'] if t['source'] in ('US Hub', 'CA Hub')
            )
            md += f"- **{sd['name']}**: {t_str}\n"
        md += "\n"

    intl_skus = [s for s in skus if any(t['source'] == 'UK' for t in sku_data[s['sku_id']]['transfers'])]
    if intl_skus:
        md += "**✈️ International Transfers** *(UK surplus → AU/EU)*:\n\n"
        for s in intl_skus:
            sd = sku_data[s['sku_id']]
            t_str = ', '.join(
                f"{int(t['qty']):,} UK→{t['dest'].replace('_',' ')}"
                for t in sd['transfers'] if t['source'] == 'UK'
            )
            md += f"- **{sd['name']}**: {t_str}\n"
        md += "\n"

    if top_up_skus:
        md += "**🖨️ Top-Up Prints** *(blocked routes or no hub surplus for specific channels)*:\n\n"
        for s in top_up_skus:
            sd = sku_data[s['sku_id']]
            tp_str = ', '.join(
                f"{qty:,} → {dest.replace('_',' ')}"
                for dest, qty in sd['top_up_print'].items()
            )
            md += f"- **{sd['name']}**: {tp_str}\n"
        md += "\n"

    md += "### Plan at a Glance\n\n"
    md += "| | |\n| :--- | :--- |\n"
    md += f"| Selling period | May 2026 – Jan 2027 (9 months) |\n"
    md += f"| Channels modelled | Amazon US FBA, Amazon CA FBA, US Shopify, CA Shopify, UK, EU, AU |\n"
    md += f"| Buffer carry-over | 30 days (Feb 2027 average) |\n"
    md += f"| Full print runs | {len(printing_skus)} SKUs · {int(total_print_units):,} units total |\n"
    md += f"| Top-up prints | {len(top_up_skus)} SKUs · {int(total_top_up_all):,} units |\n"
    md += f"| Transfer moves | {total_transfers} |\n"
    md += ("| Hub→FBA rule | Hubs reserve Shopify demand + 30-day buffer first · "
           "only surplus transfers to FBA |\n")
    md += ("| Print rule | If printing: ship direct from factory · "
           "No hub→FBA transfers for that SKU |\n\n")
    md += "---\n\n"

    # ── SECTION 1: METHODOLOGY ──────────────────────────────────────────────
    md += "## Section 1: How the Numbers Were Calculated\n\n"

    md += "### The Two Questions\n\n"
    md += ("1. **How much will we sell?** — per channel, per month, May 2026–Jan 2027\n"
           "2. **How much must be left over in January?** — 30-day buffer so we never hit zero\n\n")

    md += "### Demand: Use the Maximum, Not the Average\n\n"
    md += ("For each channel and each month, we compare 2024 and 2025 actual sales and take "
           "the **higher number**. Planning to the max means we're ready for a strong Q4.\n\n")

    ex    = skus[0]
    ex_sd = sku_data[ex['sku_id']]
    oct_d = ex_sd['g_monthly'][10]
    md += f"**Example — {ex_sd['name']}, October (global):**\n\n"
    md += "| | Units |\n| :--- | ---: |\n"
    md += f"| 2024 October | {int(oct_d['2024']):,} |\n"
    md += f"| 2025 October | {int(oct_d['2025']):,} |\n"
    md += f"| **We plan for** | **{int(oct_d['max']):,}** ← the higher of the two |\n\n"

    md += "### Safety Buffer: 30 Days of Stock After January\n\n"
    md += ("The buffer is the average monthly sales from February, March, and April — "
           "one month's worth of stock that must still be on hand February 1st.\n\n")

    md += "### How the Hub→FBA Decision Works\n\n"
    md += ("US hubs (HBG, SLI, SAV, KCM) serve US Shopify primarily. "
           "CA hub serves CA Shopify. The rule:\n\n"
           "1. Each hub reserves enough stock for its own **Shopify demand + 30-day buffer**.\n"
           "2. Any stock above that reserve is **surplus** — it can transfer to FBA.\n"
           "3. If the total stock across ALL channels (including hub surplus) is still not "
           "enough to cover all channel needs, a **print run** is triggered. "
           "In print mode, stock ships direct from the factory to FBA — no hub transfers.\n\n")

    md += "### Channels and Their Stock Sources\n\n"
    md += "| Channel | Stock Comes From | Demand Proxy |\n| :--- | :--- | :--- |\n"
    md += "| Amazon US FBA | Amazon_US_FBA warehouse | Amazon_US_FBA sales history |\n"
    md += "| Amazon CA FBA | Amazon_CA_FBA warehouse (new — 0 stock) | CA Shopify history (proxy) |\n"
    md += "| US Shopify | HBG + SLI + SAV + KCM combined | 'US' warehouse sales history |\n"
    md += "| CA Shopify | CA hub | 'CA' warehouse sales history |\n"
    md += "| UK | UK warehouse | UK sales history |\n"
    md += "| EU | EU warehouse | EU sales history |\n"
    md += "| AU | AU warehouse | AU sales history |\n\n"

    md += "### Routing Constraints\n\n"
    md += "| Route | Allowed? | Notes |\n| :--- | :--- | :--- |\n"
    md += "| UK → AU | ✅ Journals only | Cards blocked |\n"
    md += "| UK → EU | ✅ All SKUs | |\n"
    md += "| US Hub surplus → US FBA | ✅ If no print run | Shopify needs reserved first |\n"
    md += "| CA Hub surplus → CA FBA | ✅ If no print run | Shopify needs reserved first |\n"
    md += "| New print → hub → FBA | ❌ | Prints ship direct to destination |\n"
    md += "| Canada supplier → US channels | ❌ | Canada supplier: CA channels only |\n\n"
    md += "---\n\n"

    # ── SECTION 2: DEMAND BREAKDOWN ─────────────────────────────────────────
    md += "## Section 2: Full Demand Breakdown by SKU\n\n"

    for sku in skus:
        sid  = sku['sku_id']
        sd   = sku_data[sid]
        name = sd['name']

        md += f"### {name} `{sid}`\n\n"

        # Global monthly demand table
        md += "**Monthly Demand Forecast (Global — all channels combined)**\n\n"
        md += "| Month | 2024 | 2025 | ✅ Max Used | Running Total |\n"
        md += "| :--- | ---: | ---: | ---: | ---: |\n"
        running = 0
        for m in forecast_months:
            r       = sd['g_monthly'][m]
            running += r['max']
            y24 = f"{int(r['2024']):,}" if r['2024'] > 0 else "—"
            y25 = f"{int(r['2025']):,}" if r['2025'] > 0 else "—"
            chosen  = f"**{int(r['max']):,}**" if r['max'] > 0 else "—"
            if r['2024'] > r['2025'] and r['2024'] > 0:
                chosen += " ← 2024"
            elif r['2025'] > r['2024'] and r['2025'] > 0:
                chosen += " ← 2025"
            md += f"| {month_label[m]} | {y24} | {y25} | {chosen} | {int(running):,} |\n"
        md += f"| **9-Month Total** | | | | **{int(sd['g_demand']):,}** |\n\n"

        # Global buffer
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

        # Global gap summary
        shortfall = int(sd['total_need']) - int(sd['total_avail'])
        gap_label = (f"⚠️ **Globally short by {shortfall:,} units** → print run triggered"
                     if sd['is_printing']
                     else f"✅ **Globally sufficient** — total stock {int(sd['total_avail']):,} ≥ "
                          f"total need {int(sd['total_need']):,}")
        md += f"**Global Stock Check:** {gap_label}\n\n"

        # Per-channel stock check
        md += "**Per-Channel Stock Check**\n\n"
        md += "| Channel | 9-Mo Demand | Buffer | Need | Current Stock | How It's Filled |\n"
        md += "| :--- | ---: | ---: | ---: | ---: | :--- |\n"
        for region in all_channels:
            c = sd['ch'][region]
            if c['demand'] == 0 and c['current'] == 0:
                continue
            dem   = int(c['demand'])
            buf   = int(c['buffer'])
            need  = dem + buf
            curr  = int(c['current'])

            if region == 'US_Shopify':
                curr_label = f"{curr:,} (HBG+SLI+SAV+KCM)"
            elif region == 'CA_Shopify':
                curr_label = f"{curr:,} (CA hub)"
            else:
                curr_label = f"{curr:,}"

            sup_qty = int(sd['supplier_alloc'].get(region, 0))
            tp_qty  = sd['top_up_print'].get(region, 0)
            dest_transfers = [t for t in sd['transfers'] if t['dest'] == region]

            final_stock = int(sd['start_stock'].get(region, 0))

            if region in sd['print_alloc']:
                qty  = sd['print_alloc'][region]
                note = " (UK→AU blocked for cards)" if region == 'AU' and not sd['is_journal'] else ""
                parts = []
                if sup_qty:
                    parts.append(f"📦 {sup_qty:,} supplier")
                parts.append(f"🖨️ print {qty:,} direct")
                fill = f"{' + '.join(parts)}{note}"
            elif region == 'US_Shopify' and sd['outgoing_us_hub'] > 0:
                fill = (f"✅ Sufficient · {int(sd['outgoing_us_hub']):,} surplus → US FBA "
                        f"(Shopify keeps {int(sd['start_stock']['US_Shopify']):,})")
            elif region == 'CA_Shopify' and sd['outgoing_ca_hub'] > 0:
                fill = (f"✅ Sufficient · {int(sd['outgoing_ca_hub']):,} surplus → CA FBA "
                        f"(CA Shopify keeps {int(sd['start_stock']['CA_Shopify']):,})")
            elif final_stock >= need:
                fill = "✅ Sufficient stock"
                if sup_qty:
                    fill += f" (incl. {sup_qty:,} supplier)"
            else:
                parts = []
                if dest_transfers:
                    t_parts = [f"{t['source']} {int(t['qty']):,}" for t in dest_transfers]
                    icon    = "✈️" if any(t['source'] == 'UK' for t in dest_transfers) else "📦"
                    parts.append(f"{icon} Transfer: {' + '.join(t_parts)}")
                if sup_qty:
                    parts.append(f"📦 {sup_qty:,} supplier")
                if tp_qty:
                    note = " (UK→AU blocked for cards)" if region == 'AU' and not sd['is_journal'] else ""
                    parts.append(f"🖨️ top-up print {tp_qty:,}{note}")
                fill = " + ".join(parts) if parts else f"⚠️ Gap {need - final_stock:,} — unresolved"

            md += f"| {region.replace('_',' ')} | {dem:,} | {buf:,} | {need:,} | {curr_label} | {fill} |\n"

        if sd['outgoing_uk'] > 0:
            uk_end = int(stock_idx.get(sid, {}).get('UK', 0)) - int(sd['outgoing_uk'])
            uk_dem = int(sd['ch']['UK']['demand'])
            md += (f"\n> **UK stock:** {int(stock_idx.get(sid,{}).get('UK',0)):,} current "
                   f"− {int(sd['outgoing_uk']):,} transferred = **{uk_end:,} remaining** "
                   f"vs UK demand {uk_dem:,} → "
                   f"{'✅ covered' if uk_end >= uk_dem else '⚠️ short'}\n")

        if sd['is_printing']:
            alloc_detail = ' + '.join(
                f"{qty:,} to {dest.replace('_',' ')}" for dest, qty in sd['print_alloc'].items()
            )
            md += f"\n**→ PRINT ORDER: {sd['total_print']:,} units** ({alloc_detail})\n\n"
        elif sd['total_top_up'] > 0:
            tp_detail = ' + '.join(
                f"{qty:,} to {dest.replace('_',' ')}" for dest, qty in sd['top_up_print'].items()
            )
            md += (f"\n**→ No full print run** — hub surplus covers FBA · "
                   f"Top-up print: **{sd['total_top_up']:,} units** ({tp_detail})\n\n")
        else:
            md += f"\n**→ No print order needed** — transfers reposition existing stock\n\n"

        md += "---\n\n"

    # ── SECTION 3: PRINT ORDERS ──────────────────────────────────────────────
    md += "## Section 3: New Print Orders\n\n"

    if not printing_skus:
        md += ("✅ **No new print orders required.** All channels can be covered by "
               "repositioning existing hub surplus via transfers.\n\n")
    else:
        md += ("The following SKUs need new units printed and shipped **direct from the "
               "printer to the destination** — do not route through hubs.\n\n")
        for s in printing_skus:
            sid = s['sku_id']
            sd  = sku_data[sid]
            md += f"### 🖨️ {sd['name']} — Print {sd['total_print']:,} Units\n\n"
            md += "| Destination | Units | Current Stock | 9-Mo Need | Deficit | Math |\n"
            md += "| :--- | ---: | ---: | ---: | ---: | :--- |\n"
            for dest, qty in sd['print_alloc'].items():
                c       = sd['ch'][dest]
                curr    = int(c['current'])
                need    = int(c['demand'] + c['buffer'])
                deficit = int(c['deficit'])
                uk_note = " (UK→AU blocked for cards)" if dest == 'AU' and not sd['is_journal'] else ""
                md += (f"| {dest.replace('_',' ')} | **{qty:,}** | {curr:,} | "
                       f"{need:,} | {deficit:,} | "
                       f"{need:,} need − {curr:,} stock = {deficit:,}{uk_note} |\n")
            md += f"\n*Total: **{sd['total_print']:,} units** · ship direct from printer*\n\n"

    if top_up_skus:
        md += "### 🖨️ Top-Up Prints (Targeted Channel Fills)\n\n"
        md += ("Small supplemental prints where the transfer route is blocked or hub "
               "surplus is exhausted. Hub→FBA transfers still proceed in parallel.\n\n")
        md += "| SKU | Destination | Units | Reason |\n"
        md += "| :--- | :--- | ---: | :--- |\n"
        for s in top_up_skus:
            sid = s['sku_id']
            sd  = sku_data[sid]
            for dest, qty in sd['top_up_print'].items():
                c    = sd['ch'][dest]
                dem  = int(c['demand'])
                curr = int(c['current'])
                inc  = int(sd['incoming'].get(dest, 0))
                if dest == 'AU' and not sd['is_journal']:
                    reason = f"Cards blocked UK→AU · no transfer route · AU needs {dem+int(c['buffer']):,}, has {curr:,}"
                elif dest == 'Amazon_CA_FBA':
                    reason = f"CA hub surplus exhausted · CA FBA still short {qty:,}"
                elif dest == 'Amazon_US_FBA':
                    reason = f"US hub surplus insufficient · US FBA still short {qty:,}"
                else:
                    reason = f"Deficit {qty:,} after all transfers"
                md += f"| {sd['name']} | {dest.replace('_',' ')} | **{qty:,}** | {reason} |\n"
        md += "\n"

    md += "---\n\n"

    # ── SECTION 4: TRANSFER PLAN ─────────────────────────────────────────────
    md += "## Section 4: Transfer Plan\n\n"
    md += ("Complete all transfers by **September 1, 2026**. "
           "FBA inbound processing takes 2–4 weeks — stock not in FBA by early October "
           "will miss the November–December peak.\n\n")
    md += ("> **Rule:** Hub→FBA transfers only happen for SKUs with **no new print run**. "
           "Hub stock is split: Shopify demand + buffer stays at the hub; only the surplus moves to FBA.\n\n")

    has_transfers = any(sd['transfers'] for sd in sku_data.values())
    if has_transfers:
        md += "| SKU | From → To | Units | Source Stock | Dest Need | Justification |\n"
        md += "| :--- | :--- | ---: | ---: | ---: | :--- |\n"
        for sku in skus:
            sid = sku['sku_id']
            sd  = sku_data[sid]
            for t in sd['transfers']:
                src = t['source']
                if src == 'US Hub':
                    src_stock = int(sum(stock_idx.get(sid, {}).get(h, 0) for h in US_HUB_KEYS))
                elif src == 'CA Hub':
                    src_stock = int(stock_idx.get(sid, {}).get('CA', 0))
                else:
                    src_stock = int(stock_idx.get(sid, {}).get(src, 0))
                dest_need = int(sd['ch'].get(t['dest'], {}).get('demand', 0)
                                + sd['ch'].get(t['dest'], {}).get('buffer', 0))
                md += (f"| {sd['name']} | {src} → {t['dest'].replace('_',' ')} "
                       f"| **{int(t['qty']):,}** | {src_stock:,} | {dest_need:,} | "
                       f"{t['reason']} |\n")
    else:
        md += "No transfers required — all channels covered by existing stock or new print.\n"

    md += "\n---\n\n"

    # ── SECTION 5: ROLLING DEPLETION ─────────────────────────────────────────
    md += "## Section 5: Rolling Depletion Forecast by Channel\n\n"
    md += ("Starting stock = current inventory **after** all transfers and print runs arrive. "
           "Each month we subtract max projected sales. "
           "January 2027 ending balance = the 30-day carry-over buffer.\n\n")

    consumer_display = ['Amazon_US_FBA', 'Amazon_CA_FBA', 'US_Shopify', 'CA_Shopify', 'UK', 'AU']

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

            # Starting stock note
            curr = int(c['current'])
            inc  = int(sd['incoming'].get(region, 0))
            sup_in = int(sd['supplier_alloc'].get(region, 0))

            if region == 'UK':
                out = int(sd['outgoing_uk'])
                stock_note = (f"*Starting stock: **{int(starting):,}** "
                              f"({curr:,} current − {out:,} transferred out)*")
            elif region == 'US_Shopify':
                out = int(sd['outgoing_us_hub'])
                parts = [f"HBG+SLI+SAV+KCM: {curr:,}"]
                if out > 0:
                    parts.append(f"− {out:,} transferred to US FBA")
                stock_note = f"*Starting stock: **{int(starting):,}** ({', '.join(parts)})*"
            elif region == 'CA_Shopify':
                out = int(sd['outgoing_ca_hub'])
                parts = [f"CA hub: {curr:,}"]
                if out > 0:
                    parts.append(f"− {out:,} transferred to CA FBA")
                if sup_in > 0:
                    parts.append(f"+ {sup_in:,} supplier")
                stock_note = f"*Starting stock: **{int(starting):,}** ({', '.join(parts)})*"
            else:
                parts = [f"{curr:,} current"]
                if inc > 0:
                    if region in sd.get('print_alloc', {}):
                        src_label = 'print'
                    elif region in sd.get('top_up_print', {}):
                        src_label = 'top-up print'
                    else:
                        src_label = 'transfer + supplier' if sup_in > 0 and (inc - sup_in) > 0 else (
                            'supplier' if sup_in > 0 else 'transfer')
                    parts.append(f"{inc:,} {src_label}")
                if len(parts) > 1:
                    stock_note = f"*Starting stock: **{int(starting):,}** ({' + '.join(parts)})*"
                else:
                    stock_note = f"*Starting stock: **{int(starting):,}** (current stock only)*"

            buf_parts = []
            for m in buffer_months:
                bp = c['buf_parts'].get(m, {})
                if bp.get('avg', 0) > 0:
                    buf_parts.append(f"{month_short[m]} avg {int(bp['avg']):,}")
            buf_note = " + ".join(buf_parts) + f" = {int(reg_buffer):,}" if buf_parts else f"{int(reg_buffer):,}"

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

                next_i = i + 1
                if next_i < len(forecast_months):
                    next_rate = monthly[forecast_months[next_i]]
                else:
                    next_rate = reg_buffer / 3
                woc_str = f"{ending / (next_rate / (days_in.get(m, 30) / 7)):.1f}w" if next_rate > 0 else "—"

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
        md += "- ✅ No full production runs needed\n"
    md += "\n"

    if top_up_skus:
        md += "### 🖨️ Top-Up Prints (Small Targeted Orders)\n\n"
        for s in top_up_skus:
            sd = sku_data[s['sku_id']]
            md += f"- [ ] **{sd['name']}** — top-up prints:\n"
            for dest, qty in sd['top_up_print'].items():
                md += f"  - Ship **{qty:,} units** direct to **{dest.replace('_',' ')}**\n"
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
    md += "- [ ] Confirm print run lead times — stock must arrive before September for FBA prep\n"
    md += "- [ ] FBA inbound shipments created in Seller Central with tracking numbers\n"
    md += "- [ ] UK→AU journal shipments cleared customs and confirmed at AU warehouse\n"
    md += "- [ ] US hub transfers initiated — confirm Shopify buffer is reserved before moving surplus\n"
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
