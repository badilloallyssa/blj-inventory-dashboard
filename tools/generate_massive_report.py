
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


# ── MARKDOWN HELPERS ────────────────────────────────────────────────────────

def depletion_region_md(region, sd, forecast_months, buffer_months,
                        month_label, month_short, days_in):
    """Rolling depletion table for one channel of one SKU."""
    c          = sd['ch'][region]
    starting   = sd['start_stock'].get(region, 0)
    reg_buffer = c['buffer']
    monthly    = c['monthly']
    curr       = int(c['current'])

    # ── starting stock note ──
    inc    = int(sd['incoming'].get(region, 0))
    sup_in = int(sd['supplier_alloc'].get(region, 0))

    if region == 'UK':
        out = int(sd['outgoing_uk'])
        note = (f"{curr:,} current"
                + (f" − {out:,} transferred out" if out > 0 else ""))
    elif region == 'US_Shopify':
        out = int(sd['outgoing_us_hub'])
        note = ("HBG+SLI+SAV+KCM: " + f"{curr:,}"
                + (f" − {out:,} transferred to US FBA" if out > 0 else "")
                + (f" + {int(sd['print_alloc'].get(region,0)):,} print" if region in sd['print_alloc'] else "")
                + (f" + {int(sd['top_up_print'].get(region,0)):,} top-up print" if region in sd['top_up_print'] else ""))
    elif region == 'CA_Shopify':
        out = int(sd['outgoing_ca_hub'])
        parts = [f"CA hub: {curr:,}"]
        if out > 0:
            parts.append(f"− {out:,} to CA FBA")
        if sup_in > 0:
            parts.append(f"+ {sup_in:,} supplier")
        if region in sd['print_alloc']:
            parts.append(f"+ {int(sd['print_alloc'][region]):,} print")
        if region in sd['top_up_print']:
            parts.append(f"+ {int(sd['top_up_print'][region]):,} top-up print")
        note = " ".join(parts)
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
            parts.append(f"+ {inc:,} {src_label}")
        note = " + ".join(parts) if len(parts) > 1 else parts[0]

    buf_parts = []
    for m in buffer_months:
        bp = c['buf_parts'].get(m, {})
        if bp.get('avg', 0) > 0:
            buf_parts.append(f"{month_short[m]} avg {int(bp['avg']):,}")
    buf_note = " + ".join(buf_parts) + f" = {int(reg_buffer):,}" if buf_parts else f"{int(reg_buffer):,}"

    md  = f"#### {region.replace('_', ' ')}\n\n"
    md += f"*Starting stock: **{int(starting):,}** ({note})*\n\n"
    md += f"*30-day buffer target: **{int(reg_buffer):,} units** ({buf_note})*\n\n"
    md += "| Month | Projected Sales | Ending Stock | vs Buffer | Weeks of Cover |\n"
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
    md += (f"\n> **Jan 2027 ending: {int(jan_end):,} units** · "
           f"Buffer target: {int(reg_buffer):,} · {status}\n\n")
    return md


def stockout_md(sd, forecast_months, month_label):
    """Shows what breaks for print-SKU channels if no print run happens."""
    lines = []
    for region, qty in sorted(sd['print_alloc'].items(), key=lambda x: -x[1]):
        # no-print start = start_stock minus the print allocation
        no_print_start = sd['start_stock'].get(region, 0) - qty
        monthly = sd['ch'][region]['monthly']
        buf     = sd['ch'][region]['buffer']
        cumul   = 0
        breach_m = stockout_m = None
        for m in forecast_months:
            cumul += monthly[m]
            ending = no_print_start - cumul
            if ending < buf and breach_m is None:
                breach_m = m
            if ending < 0 and stockout_m is None:
                stockout_m = m
                break
        if stockout_m:
            risk = f"🚨 Runs out of stock in **{month_label[stockout_m]}**"
        elif breach_m:
            risk = f"⚠️ Falls below 30-day safety buffer in **{month_label[breach_m]}**"
        else:
            risk = "Would survive through Jan (just barely — no buffer)"
        lines.append(f"| {region.replace('_',' ')} | {int(no_print_start):,} | {int(qty):,} | {risk} |")

    md  = "**Without this print run — what would break:**\n\n"
    md += "| Channel | Stock Without Print | Print Adds | Consequence |\n"
    md += "| :--- | ---: | ---: | :--- |\n"
    md += "\n".join(lines) + "\n\n"
    return md


def hub_math_md(sd, forecast_months):
    """Hub surplus table + FBA gap analysis + monthly hub depletion — boss-level transparency."""
    ch = sd['ch']

    us_curr    = int(ch['US_Shopify']['current'])
    us_dem     = int(ch['US_Shopify']['demand'])
    us_buf     = int(ch['US_Shopify']['buffer'])
    us_need    = us_dem + us_buf
    us_sup     = int(sd['supplier_alloc'].get('US_Shopify', 0))
    us_avail   = us_curr + us_sup
    us_surplus = max(0, us_avail - us_need)
    us_short   = max(0, us_need - us_avail)
    us_xfr     = int(sd['outgoing_us_hub'])

    ca_curr    = int(ch['CA_Shopify']['current'])
    ca_dem     = int(ch['CA_Shopify']['demand'])
    ca_buf     = int(ch['CA_Shopify']['buffer'])
    ca_need    = ca_dem + ca_buf
    ca_sup     = int(sd['supplier_alloc'].get('CA_Shopify', 0))
    ca_avail   = ca_curr + ca_sup
    ca_surplus = max(0, ca_avail - ca_need)
    ca_short   = max(0, ca_need - ca_avail)
    ca_xfr     = int(sd['outgoing_ca_hub'])

    fba_us_curr = int(ch['Amazon_US_FBA']['current'])
    fba_us_dem  = int(ch['Amazon_US_FBA']['demand'])
    fba_us_buf  = int(ch['Amazon_US_FBA']['buffer'])
    fba_us_need = fba_us_dem + fba_us_buf
    fba_ca_curr = int(ch['Amazon_CA_FBA']['current'])
    fba_ca_dem  = int(ch['Amazon_CA_FBA']['demand'])
    fba_ca_buf  = int(ch['Amazon_CA_FBA']['buffer'])
    fba_ca_need = fba_ca_dem + fba_ca_buf

    md  = "#### US & CA Channel Analysis\n\n"

    # ── Hub vs Shopify table ──
    md += "**Step 1 — How much hub stock is reserved for Shopify vs available for FBA?**\n\n"
    md += "| | US Hubs (HBG / SLI / SAV / KCM) | CA Hub |\n"
    md += "| :--- | ---: | ---: |\n"
    md += f"| Current stock at hub | {us_curr:,} | {ca_curr:,} |\n"
    if us_sup > 0 or ca_sup > 0:
        md += f"| Incoming supplier stock | +{us_sup:,} | +{ca_sup:,} |\n"
        md += f"| **Total available** | **{us_avail:,}** | **{ca_avail:,}** |\n"
    md += f"| Shopify demand May–Jan | {us_dem:,} | {ca_dem:,} |\n"
    md += f"| 30-day Shopify buffer | {us_buf:,} | {ca_buf:,} |\n"
    md += f"| **Shopify reserve (must keep)** | **{us_need:,}** | **{ca_need:,}** |\n"

    if us_surplus > 0:
        us_res = f"**+{us_surplus:,} surplus → transfer {us_xfr:,} to US FBA**"
    else:
        us_res = f"**−{us_short:,} shortfall — hub itself needs {us_short:,} more units**"
    if ca_surplus > 0:
        ca_res = f"**+{ca_surplus:,} surplus → transfer {ca_xfr:,} to CA FBA**"
    else:
        ca_res = f"**−{ca_short:,} shortfall — hub needs {ca_short:,} more**"
    md += f"| **Hub result** | {us_res} | {ca_res} |\n\n"

    # ── FBA gap table ──
    md += "**Step 2 — After hub transfer, is FBA covered?**\n\n"
    md += "| | Amazon US FBA | Amazon CA FBA |\n"
    md += "| :--- | ---: | ---: |\n"
    md += f"| Current FBA stock | {fba_us_curr:,} | {fba_ca_curr:,} |\n"
    if us_xfr > 0 or ca_xfr > 0:
        md += f"| Transfer in from hub | +{us_xfr:,} | +{ca_xfr:,} |\n"
    sup_us_fba = int(sd['supplier_alloc'].get('Amazon_US_FBA', 0))
    sup_ca_fba = int(sd['supplier_alloc'].get('Amazon_CA_FBA', 0))
    if sup_us_fba > 0 or sup_ca_fba > 0:
        md += f"| Supplier stock | +{sup_us_fba:,} | +{sup_ca_fba:,} |\n"
    fba_us_have = fba_us_curr + us_xfr + sup_us_fba
    fba_ca_have = fba_ca_curr + ca_xfr + sup_ca_fba
    md += f"| **Total FBA stock** | **{fba_us_have:,}** | **{fba_ca_have:,}** |\n"
    md += f"| FBA demand May–Jan | {fba_us_dem:,} | {fba_ca_dem:,} |\n"
    md += f"| 30-day FBA buffer | {fba_us_buf:,} | {fba_ca_buf:,} |\n"
    md += f"| **FBA total need** | **{fba_us_need:,}** | **{fba_ca_need:,}** |\n"
    fba_us_gap = fba_us_need - fba_us_have
    fba_ca_gap = fba_ca_need - fba_ca_have
    us_fba_res = f"**−{fba_us_gap:,} still short**" if fba_us_gap > 0 else f"**✅ Covered (+{-fba_us_gap:,})**"
    ca_fba_res = f"**−{fba_ca_gap:,} still short**" if fba_ca_gap > 0 else f"**✅ Covered (+{-fba_ca_gap:,})**"
    md += f"| **FBA result** | {us_fba_res} | {ca_fba_res} |\n\n"

    # ── Monthly US hub depletion (only show if interesting — hub has meaningful volume) ──
    if us_dem > 0:
        mlabels = {5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec',1:'Jan'}
        us_start = us_avail - us_xfr  # hub start after transferring surplus to FBA
        us_print = int(sd['print_alloc'].get('US_Shopify', 0) + sd['top_up_print'].get('US_Shopify', 0))
        us_start += us_print
        monthly = ch['US_Shopify']['monthly']
        md += "**US Hub monthly sell-through (US Shopify channel):**\n\n"
        md += "| Month | Projected Sales | Hub Balance | vs Buffer |\n"
        md += "| :--- | ---: | ---: | ---: |\n"
        cumul = 0
        for m in forecast_months:
            cumul += monthly[m]
            bal = us_start - cumul
            vs  = int(bal) - int(us_buf)
            vs_str = f"+{vs:,}" if vs >= 0 else f"**{vs:,} ⚠️**"
            flag = " ⚠️" if bal < 0 else ""
            md += f"| {mlabels[m]} | {int(monthly[m]):,} | **{int(bal):,}**{flag} | {vs_str} |\n"
        jan_bal = us_start - sum(monthly[m] for m in forecast_months)
        status  = "✅ Hub ends above buffer" if jan_bal >= us_buf * 0.9 else "⚠️ Hub ends below buffer"
        md += f"\n> Jan 2027 hub balance: **{int(jan_bal):,}** · Buffer target: {int(us_buf):,} · {status}\n\n"

    return md


def master_sku_table_md(sd, forecast_months, month_label):
    """
    Consolidated per-SKU section:
      - decision label + one-liner
      - global stock check callout
      - master channel depletion table (all 9 months as columns)
      - why-this-plan bullets (quantitative + qualitative)
    """
    ch = sd['ch']

    # ── Decision label + one-liner ──────────────────────────────────────────────
    if sd['is_printing']:
        gap = int(sd['total_need']) - int(sd['total_avail'])
        decision_label = f"🖨️ Print {sd['total_print']:,} units"
        one_liner = (f"Short **{gap:,} units** globally — "
                     f"{int(sd['total_avail']):,} available vs {int(sd['total_need']):,} needed")
    else:
        surplus = int(sd['total_avail']) - int(sd['total_need'])
        hub_xfr = int(sd['outgoing_us_hub']) + int(sd['outgoing_ca_hub'])
        top_up  = sd['total_top_up']
        if hub_xfr > 0 and top_up > 0:
            decision_label = "📦 Hub Transfers + 🖨️ Top-Up Prints"
            one_liner = (f"Surplus **+{surplus:,}** globally — "
                         f"{hub_xfr:,} repositioned to FBA · {top_up:,} top-up printed")
        elif hub_xfr > 0:
            decision_label = "📦 Hub→FBA Repositioning"
            one_liner = (f"Surplus **+{surplus:,}** globally — "
                         f"{hub_xfr:,} units repositioned from hubs to FBA")
        elif top_up > 0:
            decision_label = "🖨️ Top-Up Prints"
            one_liner = (f"Surplus **+{surplus:,}** globally but transfer routes blocked — "
                         f"{top_up:,} units top-up printed")
        else:
            decision_label = "✅ No Action Required"
            one_liner = f"Surplus **+{surplus:,}** globally — all channels covered by current stock"

    md  = f"**{decision_label}** — {one_liner}\n\n"

    # ── Global check callout ────────────────────────────────────────────────────
    if sd['is_printing']:
        gap = int(sd['total_need']) - int(sd['total_avail'])
        md += (f"> ⚠️ **Globally short {gap:,} units** "
               f"(stock: {int(sd['total_avail']):,} · need: {int(sd['total_need']):,})\n\n")
    else:
        surplus = int(sd['total_avail']) - int(sd['total_need'])
        md += (f"> ✅ **Globally sufficient · +{surplus:,} surplus** "
               f"(stock: {int(sd['total_avail']):,} · need: {int(sd['total_need']):,})\n\n")

    # ── Master channel depletion table ──────────────────────────────────────────
    md += ("*Starting = stock after all transfers / supplier / print runs arrive. "
           "Monthly columns = ending balance after cumulative demand is deducted. "
           "**Jan must end ≥ Buffer.***\n\n")

    hdr = ("| Channel | On Hand | Action | Starting "
           "| May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Buffer | ✓ |")
    sep = ("| :--- | ---: | :--- | ---: "
           "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |")
    md += hdr + "\n" + sep + "\n"

    ch_display = {
        'Amazon_US_FBA': 'Amazon US FBA',
        'Amazon_CA_FBA': 'Amazon CA FBA',
        'US_Shopify':    'US Shopify (hubs)',
        'CA_Shopify':    'CA Shopify (CA hub)',
        'UK':            'UK',
        'EU':            'EU',
        'AU':            'AU',
    }

    for region in ['Amazon_US_FBA', 'Amazon_CA_FBA', 'US_Shopify', 'CA_Shopify', 'UK', 'EU', 'AU']:
        c = ch[region]
        if c['demand'] == 0 and c['current'] == 0 and sd['start_stock'].get(region, 0) == 0:
            continue

        curr     = int(c['current'])
        starting = sd['start_stock'].get(region, 0)
        buf      = c['buffer']
        monthly  = c['monthly']

        # Decompose incoming into its sources
        print_in = int(sd['print_alloc'].get(region, 0))
        topup_in = int(sd['top_up_print'].get(region, 0))
        sup_in   = int(sd['supplier_alloc'].get(region, 0))
        xfr_in   = int(sum(t['qty'] for t in sd['transfers'] if t['dest'] == region))

        if region == 'UK':
            out = int(sd['outgoing_uk'])
        elif region == 'US_Shopify':
            out = int(sd['outgoing_us_hub'])
        elif region == 'CA_Shopify':
            out = int(sd['outgoing_ca_hub'])
        else:
            out = 0

        action_parts = []
        if xfr_in > 0:
            t_srcs = list(dict.fromkeys(t['source'] for t in sd['transfers'] if t['dest'] == region))
            action_parts.append(f"+{xfr_in:,} from {'/'.join(t_srcs)}")
        if sup_in > 0:
            action_parts.append(f"+{sup_in:,} supplier")
        if print_in > 0:
            action_parts.append(f"+{print_in:,} print")
        if topup_in > 0:
            action_parts.append(f"+{topup_in:,} top-up")
        if out > 0:
            if region == 'UK':
                dests = list(dict.fromkeys(
                    t['dest'].replace('_', ' ') for t in sd['transfers'] if t['source'] == 'UK'))
                action_parts.append(f"−{out:,}→{'/'.join(dests)}")
            elif region == 'US_Shopify':
                action_parts.append(f"−{out:,}→US FBA")
            elif region == 'CA_Shopify':
                action_parts.append(f"−{out:,}→CA FBA")

        action_str = "; ".join(action_parts) if action_parts else "—"

        row = f"| {ch_display[region]} | {curr:,} | {action_str} | {int(starting):,} |"
        cumul = 0
        for m in forecast_months:
            cumul  += monthly[m]
            ending  = starting - cumul
            row    += f" **{int(ending):,}** |" if m == 1 else f" {int(ending):,} |"

        jan_end = starting - sum(monthly[m] for m in forecast_months)
        status  = "✅" if jan_end >= buf * 0.9 else "⚠️"
        row    += f" {int(buf):,} | {status} |"
        md     += row + "\n"

    md += "\n"

    # ── Why this plan ───────────────────────────────────────────────────────────
    md += "**Why this plan:**\n\n"

    peak_m     = max(forecast_months, key=lambda m: sd['g_monthly'][m]['max'])
    peak_units = int(sd['g_monthly'][peak_m]['max'])

    if sd['is_printing']:
        gap = int(sd['total_need']) - int(sd['total_avail'])
        md += (f"- **Global shortfall:** All 7 channels combined hold **{int(sd['total_avail']):,} units** "
               f"against a total need of **{int(sd['total_need']):,}** (May–Jan demand + 30-day buffer "
               f"per channel) = **{gap:,} unit deficit**. Peak demand hits **{month_label[peak_m]}** "
               f"at {peak_units:,} units globally.\n")
        md += (f"- **Print decision:** Order **{sd['total_print']:,} units** and ship direct from factory "
               f"to each short channel — never routed through a hub, as that adds weeks of lead time.\n")
        for region, qty in sd['print_alloc'].items():
            c = ch[region]
            need = int(c['demand'] + c['buffer'])
            curr = int(c['current'])
            md  += (f"  - **{region.replace('_', ' ')}:** has {curr:,} · needs {need:,} "
                    f"(demand {int(c['demand']):,} + buffer {int(c['buffer']):,}) "
                    f"→ gap {need - curr:,} → print **{qty:,}** direct\n")
        md += "- **Without this print run:**\n"
        for region, qty in sorted(sd['print_alloc'].items(), key=lambda x: -x[1]):
            no_start = sd['start_stock'].get(region, 0) - qty
            monthly  = ch[region]['monthly']
            buf      = ch[region]['buffer']
            cumul = 0
            breach_m = stockout_m = None
            for m in forecast_months:
                cumul  += monthly[m]
                ending  = no_start - cumul
                if ending < buf and breach_m is None:
                    breach_m = m
                if ending < 0 and stockout_m is None:
                    stockout_m = m
                    break
            if stockout_m:
                md += f"  - **{region.replace('_', ' ')}** runs out of stock in **{month_label[stockout_m]}** 🚨\n"
            elif breach_m:
                md += f"  - **{region.replace('_', ' ')}** falls below safety buffer in **{month_label[breach_m]}** ⚠️\n"
            else:
                md += f"  - **{region.replace('_', ' ')}** would survive through Jan but with zero buffer margin\n"

    else:
        surplus    = int(sd['total_avail']) - int(sd['total_need'])
        us_hub_c   = int(ch['US_Shopify']['current'])
        us_need_sh = int(ch['US_Shopify']['demand'] + ch['US_Shopify']['buffer'])
        us_surplus = max(0, us_hub_c - us_need_sh)
        us_xfr     = int(sd['outgoing_us_hub'])
        ca_hub_c   = int(ch['CA_Shopify']['current'])
        ca_need_sh = int(ch['CA_Shopify']['demand'] + ch['CA_Shopify']['buffer'])
        ca_surplus = max(0, ca_hub_c - ca_need_sh)
        ca_xfr     = int(sd['outgoing_ca_hub'])

        md += (f"- **No print needed:** {int(sd['total_avail']):,} units available vs "
               f"{int(sd['total_need']):,} needed = **+{surplus:,} surplus** across all channels. "
               f"Peak demand is **{month_label[peak_m]}** at {peak_units:,} units.\n")

        if us_hub_c > 0:
            if us_surplus > 0:
                md += (f"- **US hubs (HBG/SLI/SAV/KCM):** hold {us_hub_c:,} units total. "
                       f"US Shopify must keep {us_need_sh:,} "
                       f"(demand {int(ch['US_Shopify']['demand']):,} + buffer {int(ch['US_Shopify']['buffer']):,}). "
                       f"**Surplus above Shopify reserve: {us_surplus:,}.**")
                if us_xfr > 0:
                    md += f" Transfer **{us_xfr:,}** → Amazon US FBA.\n"
                else:
                    md += " Amazon US FBA already covered — no transfer needed.\n"
            else:
                md += (f"- **US hubs:** hold {us_hub_c:,} — all reserved for US Shopify "
                       f"(needs {us_need_sh:,}), zero surplus for FBA.\n")

        if ca_hub_c > 0 or ch['CA_Shopify']['demand'] > 0:
            if ca_surplus > 0:
                md += (f"- **CA hub:** holds {ca_hub_c:,}. "
                       f"CA Shopify must keep {ca_need_sh:,} "
                       f"(demand {int(ch['CA_Shopify']['demand']):,} + buffer {int(ch['CA_Shopify']['buffer']):,}). "
                       f"**Surplus: {ca_surplus:,}.**")
                if ca_xfr > 0:
                    md += f" Transfer **{ca_xfr:,}** → Amazon CA FBA.\n"
                else:
                    md += "\n"
            elif ca_hub_c > 0:
                md += (f"- **CA hub:** holds {ca_hub_c:,} — all reserved for CA Shopify "
                       f"(needs {ca_need_sh:,}), no surplus for CA FBA.\n")

        for t in sd['transfers']:
            if t['source'] == 'UK':
                uk_c = int(ch['UK']['current'])
                uk_n = int(ch['UK']['demand'] + ch['UK']['buffer'])
                dest = t['dest'].replace('_', ' ')
                md  += (f"- **UK → {dest}:** UK holds {uk_c:,} with only {uk_n:,} needed locally "
                        f"(surplus {max(0, uk_c - uk_n):,}). "
                        f"Transfer **{int(t['qty']):,}** to fill {dest} gap.\n")

        for region, qty in sd['top_up_print'].items():
            c     = ch[region]
            need  = int(c['demand'] + c['buffer'])
            final = int(sd['start_stock'].get(region, 0))
            if region == 'AU' and not sd['is_journal']:
                reason = "Cards cannot use the UK→AU route — no valid transfer source"
            elif region == 'Amazon_CA_FBA':
                reason = (f"CA hub surplus ({ca_surplus:,}) exhausted after reserving "
                          f"CA Shopify — FBA still needs {qty:,} more")
            elif region == 'Amazon_US_FBA':
                reason = (f"US hub surplus ({us_surplus:,}) only covered {us_xfr:,} "
                          f"— FBA still short {qty:,}")
            elif region == 'US_Shopify':
                reason = f"US hubs are short on their own Shopify demand — need {qty:,} additional"
            else:
                reason = f"No transfer route covers this gap — {qty:,} units short"
            md += (f"- **Top-up print {region.replace('_', ' ')} (+{qty:,}):** {reason}. "
                   f"After top-up: {final:,} vs need {need:,}.\n")

        if sd['canada_sup'] > 0:
            md += (f"- **Canada supplier ({int(sd['canada_sup']):,} units):** "
                   f"allocated to CA channels only — geography-restricted, cannot ship to US.\n")
        if sd['china_sup'] > 0:
            md += (f"- **China supplier ({int(sd['china_sup']):,} units):** "
                   f"allocated to Amazon US FBA first, then overflow to other deficit channels.\n")

    md += "\n"
    return md


# ── MAIN REPORT FUNCTION ─────────────────────────────────────────────────────

def generate_report():
    with open(os.path.join(PROJECT_ROOT, '.tmp/data.json')) as f:
        data = json.load(f)
    sales = data.get('sales', [])

    wh_ann     = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
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
        return total / len(buffer_months), parts

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
            swh              = source_wh[region]
            dem              = wh_demand(sid, swh)
            curr             = channel_stock(sid, region)
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

        # ── Step 1: UK transfers ───────────────────────────────────────────────
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

        # ── Step 2: Start stock ────────────────────────────────────────────────
        start_stock = {}
        for region in all_channels:
            if region == 'UK':
                start_stock[region] = uk_stock - outgoing_uk
            else:
                start_stock[region] = ch[region]['current'] + incoming.get(region, 0)

        # ── Step 3: Supplier allocation ────────────────────────────────────────
        supplier_alloc = defaultdict(float)

        if canada_sup > 0:
            pool = canada_sup
            for region in ['CA_Shopify', 'Amazon_CA_FBA']:
                if pool <= 0: break
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
                if pool <= 0: break
                need = max(0.0, ch[region]['demand'] + ch[region]['buffer'] - start_stock[region])
                if need > 0:
                    alloc = min(pool, need)
                    supplier_alloc[region] += alloc
                    start_stock[region]    += alloc
                    incoming[region]       += alloc
                    pool -= alloc

        # ── Step 4: Global gap check ───────────────────────────────────────────
        total_need  = sum(ch[r]['demand'] + ch[r]['buffer'] for r in all_channels)
        total_avail = sum(start_stock[r] for r in all_channels)
        is_globally_short = total_avail < total_need

        # ── Step 4a: Print mode ────────────────────────────────────────────────
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

        # ── Step 4b: Reposition mode ───────────────────────────────────────────
        outgoing_us_hub = 0.0
        outgoing_ca_hub = 0.0

        if not is_globally_short:
            us_shopify_need = ch['US_Shopify']['demand'] + ch['US_Shopify']['buffer']
            us_hub_surplus  = max(0.0, start_stock['US_Shopify'] - us_shopify_need)

            ca_shopify_need = ch['CA_Shopify']['demand'] + ch['CA_Shopify']['buffer']
            ca_hub_surplus  = max(0.0, start_stock['CA_Shopify'] - ca_shopify_need)

            us_fba_gap = max(0.0, ch['Amazon_US_FBA']['demand'] + ch['Amazon_US_FBA']['buffer']
                             - start_stock['Amazon_US_FBA'])
            if us_fba_gap > 0 and us_hub_surplus > 0:
                pull = min(us_fba_gap, us_hub_surplus)
                transfers.append({
                    'source': 'US Hub', 'dest': 'Amazon_US_FBA', 'qty': pull,
                    'reason': (
                        f"US hubs have {int(start_stock['US_Shopify']):,}; "
                        f"Shopify needs {int(us_shopify_need):,} (demand + buffer); "
                        f"surplus {int(us_hub_surplus):,}; US FBA gap {int(us_fba_gap):,}")
                })
                start_stock['Amazon_US_FBA'] += pull
                start_stock['US_Shopify']    -= pull
                incoming['Amazon_US_FBA']    += pull
                outgoing_us_hub              += pull
                us_hub_surplus               -= pull

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

        # ── Step 5: Top-up prints ──────────────────────────────────────────────
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
    printing_skus = [s for s in skus if sku_data[s['sku_id']]['is_printing']]
    top_up_skus   = [s for s in skus if sku_data[s['sku_id']]['total_top_up'] > 0]

    # ── BUILD MARKDOWN ───────────────────────────────────────────────────────

    md  = "# Inventory Master Plan: May 2026 – January 2027\n\n"
    md += "*Generated: May 3, 2026 · 8 SKUs · 7 channels · 9-month selling period + 30-day carry-over buffer*\n\n"
    md += "---\n\n"

    # ── EXECUTIVE SUMMARY ───────────────────────────────────────────────────
    md += "## Executive Summary\n\n"

    md += ("We're entering the 9-month window from May through January — our most important "
           "selling period, with November and December accounting for the majority of annual volume. "
           "This plan models demand for all 7 channels (Amazon US FBA, Amazon CA FBA, US Shopify, "
           "CA Shopify, UK, EU, AU), sets a 30-day safety buffer for each, and determines exactly "
           "what stock needs to move and where — before peak season starts.\n\n"
           "**The core rule:** US hubs (HBG/SLI/SAV/KCM) and the CA hub serve Shopify channels "
           "first. Only stock above Shopify needs can transfer to FBA. If total stock is still "
           "short after counting everything, we print — and new prints ship direct from the "
           "factory to the destination, never routed through a hub.\n\n")

    md += "### Actions Required\n\n"

    # Print narratives
    if printing_skus:
        md += "#### 🖨️ Print Orders\n\n"
        for s in printing_skus:
            sd  = sku_data[s['sku_id']]
            gap = int(sd['total_need']) - int(sd['total_avail'])
            peak_m = max(forecast_months, key=lambda m: sd['g_monthly'][m]['max'])

            dest_lines = '\n'.join(
                f"  - **{qty:,} units** → {dest.replace('_',' ')} *(direct from printer)*"
                for dest, qty in sd['print_alloc'].items()
            )
            md += (f"**{sd['name']} — {sd['total_print']:,} units**\n"
                   f"All channels combined fall **{gap:,} units short** of covering "
                   f"May–January demand plus a 30-day buffer "
                   f"({int(sd['total_avail']):,} available vs {int(sd['total_need']):,} needed). "
                   f"Peak month is {month_label[peak_m]} at "
                   f"{int(sd['g_monthly'][peak_m]['max']):,} units globally. Printing:\n"
                   f"{dest_lines}\n\n")

    # Transfer narratives
    hub_transfer_skus = [s for s in skus if not sku_data[s['sku_id']]['is_printing']
                         and any(t['source'] in ('US Hub', 'CA Hub')
                                 for t in sku_data[s['sku_id']]['transfers'])]
    if hub_transfer_skus:
        md += "#### 📦 Hub→FBA Transfers *(reposition surplus, no print needed)*\n\n"
        for s in hub_transfer_skus:
            sd = sku_data[s['sku_id']]
            surplus = int(sd['total_avail']) - int(sd['total_need'])
            t_lines = '\n'.join(
                f"  - {int(t['qty']):,} units: {t['source']} → {t['dest'].replace('_',' ')}"
                for t in sd['transfers'] if t['source'] in ('US Hub', 'CA Hub')
            )
            md += (f"**{sd['name']}** — globally covered (+{surplus:,} units ahead), "
                   f"but FBA channels are light. Transferring hub surplus:\n{t_lines}\n\n")

    # Top-up narratives
    if top_up_skus:
        md += "#### 🖨️ Top-Up Prints *(targeted fills where transfer routes are blocked)*\n\n"
        for s in top_up_skus:
            sd = sku_data[s['sku_id']]
            tp_lines = '\n'.join(
                f"  - **{qty:,} units** → {dest.replace('_',' ')}"
                for dest, qty in sd['top_up_print'].items()
            )
            md += f"**{sd['name']}:**\n{tp_lines}\n\n"

    # International transfers
    intl_skus = [s for s in skus if any(t['source'] == 'UK' for t in sku_data[s['sku_id']]['transfers'])]
    if intl_skus:
        md += "#### ✈️ International Transfers *(UK surplus → AU/EU)*\n\n"
        for s in intl_skus:
            sd = sku_data[s['sku_id']]
            t_lines = '\n'.join(
                f"  - {int(t['qty']):,} units: UK → {t['dest'].replace('_',' ')}"
                for t in sd['transfers'] if t['source'] == 'UK'
            )
            md += f"**{sd['name']}:**\n{t_lines}\n\n"

    # Summary table
    md += "### Summary Table\n\n"
    md += "| SKU | Decision | Units | Notes |\n"
    md += "| :--- | :--- | ---: | :--- |\n"
    for s in skus:
        sid = s['sku_id']
        sd  = sku_data[sid]
        if sd['is_printing']:
            decision = "🖨️ Print run"
            units    = sd['total_print']
            gap      = int(sd['total_need']) - int(sd['total_avail'])
            notes    = f"Globally short {gap:,} units"
        elif sd['total_top_up'] > 0 and any(t['source'] in ('US Hub','CA Hub') for t in sd['transfers']):
            decision = "📦 Transfer + 🖨️ top-up print"
            units    = sd['total_top_up'] + int(sum(t['qty'] for t in sd['transfers'] if t['source'] in ('US Hub','CA Hub')))
            notes    = f"{int(sum(t['qty'] for t in sd['transfers'] if t['source'] in ('US Hub','CA Hub'))):,} transfer · {sd['total_top_up']:,} top-up print"
        elif sd['total_top_up'] > 0:
            decision = "🖨️ Top-up print"
            units    = sd['total_top_up']
            notes    = "Blocked routes"
        elif any(t['source'] in ('US Hub','CA Hub') for t in sd['transfers']):
            decision = "📦 Hub→FBA transfer"
            units    = int(sum(t['qty'] for t in sd['transfers'] if t['source'] in ('US Hub','CA Hub')))
            notes    = "Globally sufficient"
        else:
            decision = "✅ No action needed"
            units    = 0
            notes    = "All channels covered by current stock"
        uk_t = int(sum(t['qty'] for t in sd['transfers'] if t['source'] == 'UK'))
        if uk_t > 0:
            notes += f" · {uk_t:,} UK→intl"
        md += f"| {sd['name']} | {decision} | {units:,} | {notes} |\n"

    md += "\n---\n\n"

    # ── SECTION 1: METHODOLOGY ──────────────────────────────────────────────
    md += "## Section 1: How the Numbers Were Built\n\n"

    md += ("### Demand Forecast: Always Plan for the Worst Month We've Seen\n\n"
           "For each channel and each month (May through January), we look at 2024 and 2025 "
           "actuals and take the **higher number**. If October 2024 was bigger than October 2025, "
           "we plan for October 2024. This means we're prepared for a strong Q4 — "
           "not just an average one.\n\n")

    ex    = skus[0]
    ex_sd = sku_data[ex['sku_id']]
    oct_d = ex_sd['g_monthly'][10]
    nov_d = ex_sd['g_monthly'][11]
    dec_d = ex_sd['g_monthly'][12]
    md += f"*Example — {ex_sd['name']} Q4:*\n\n"
    md += "| Month | 2024 | 2025 | Plan Uses |\n| :--- | ---: | ---: | ---: |\n"
    md += (f"| Oct | {int(oct_d['2024']):,} | {int(oct_d['2025']):,} | "
           f"**{int(oct_d['max']):,}** ← {'2024' if oct_d['2024'] >= oct_d['2025'] else '2025'} |\n")
    md += (f"| Nov | {int(nov_d['2024']):,} | {int(nov_d['2025']):,} | "
           f"**{int(nov_d['max']):,}** ← {'2024' if nov_d['2024'] >= nov_d['2025'] else '2025'} |\n")
    md += (f"| Dec | {int(dec_d['2024']):,} | {int(dec_d['2025']):,} | "
           f"**{int(dec_d['max']):,}** ← {'2024' if dec_d['2024'] >= dec_d['2025'] else '2025'} |\n\n")

    md += ("### The 30-Day Safety Buffer\n\n"
           "We don't plan to hit zero in January. The buffer is the average of what each "
           "channel sells in February, March, and April — one month's worth of stock that "
           "must still be sitting in the warehouse on February 1st, before the next "
           "replenishment arrives. This prevents stockouts in the gap between January and "
           "whenever the next order lands.\n\n")

    md += ("### The Print vs. Transfer Decision\n\n"
           "For each SKU, we ask one question first: **does total stock across all channels "
           "cover total demand + buffers?**\n\n"
           "- **Yes (globally sufficient):** No print run needed. We reposition hub surplus "
           "to FBA instead. Hubs reserve their Shopify demand + buffer; only the excess moves.\n"
           "- **No (globally short):** A print run is ordered. New stock ships direct from "
           "the factory to each short channel — it never routes through a hub first.\n\n"
           "This is a binary decision per SKU. We don't mix print runs with hub→FBA transfers "
           "for the same SKU. If we're printing, FBA gets stock from the printer. "
           "If we're not printing, FBA gets stock from hub surplus.\n\n")

    md += ("### Routing Rules\n\n"
           "| Route | Allowed? | Why |\n| :--- | :--- | :--- |\n"
           "| UK → AU | ✅ Journals only | Cards can't use this route |\n"
           "| UK → EU | ✅ All SKUs | |\n"
           "| US Hub surplus → US FBA | ✅ If no print run | Shopify reserve must be maintained |\n"
           "| CA Hub surplus → CA FBA | ✅ If no print run | Shopify reserve must be maintained |\n"
           "| New print → hub → FBA | ❌ | Too slow; prints go direct |\n"
           "| Canada supplier → US channels | ❌ | Restricted to CA channels only |\n\n")

    md += "---\n\n"

    # ── SECTION 2: SKU-BY-SKU ANALYSIS ──────────────────────────────────────
    md += "## Section 2: SKU-by-SKU Analysis\n\n"
    md += ("Each SKU section covers: the situation in plain language, the demand forecast, "
           "hub surplus math, the specific decision made, what would have happened without "
           "that decision, and the full rolling depletion forecast by channel.\n\n")

    for sku in skus:
        sid  = sku['sku_id']
        sd   = sku_data[sid]
        name = sd['name']

        md += f"---\n\n### {name} `{sid}`\n\n"

        # Master table: decision + global check + channel depletion + why bullets
        md += master_sku_table_md(sd, forecast_months, month_label)

        # Monthly demand forecast (supporting data)
        md += "#### Monthly Demand Forecast\n\n"
        md += ("*Max of 2024 and 2025 actuals taken for each month — "
               "we plan for the strongest Q4 we've seen.*\n\n")
        md += "| Month | 2024 Actual | 2025 Actual | Plan Uses | Cumulative |\n"
        md += "| :--- | ---: | ---: | ---: | ---: |\n"
        running = 0
        for m in forecast_months:
            r       = sd['g_monthly'][m]
            running += r['max']
            y24 = f"{int(r['2024']):,}" if r['2024'] > 0 else "—"
            y25 = f"{int(r['2025']):,}" if r['2025'] > 0 else "—"
            yr_tag = ""
            if r['2024'] > r['2025'] and r['2024'] > 0:
                yr_tag = " ← 2024"
            elif r['2025'] > r['2024'] and r['2025'] > 0:
                yr_tag = " ← 2025"
            chosen = f"**{int(r['max']):,}**{yr_tag}" if r['max'] > 0 else "—"
            md += f"| {month_label[m]} | {y24} | {y25} | {chosen} | {int(running):,} |\n"
        md += f"| **9-Month Total** | | | | **{int(sd['g_demand']):,}** |\n\n"

        # 30-day buffer calc (supporting data)
        md += "#### 30-Day Safety Buffer Calculation\n\n"
        md += ("*Average of Feb, Mar, Apr monthly sales — one month's worth of stock "
               "that must remain at end of January.*\n\n")
        md += "| Month | 2024 | 2025 | Monthly Average |\n| :--- | ---: | ---: | ---: |\n"
        for m in buffer_months:
            bd   = sd['g_buf_parts'][m]
            y24b = int(global_ann[sid].get(2024, {}).get(m, 0))
            y25b = int(global_ann[sid].get(2025, {}).get(m, 0))
            y24s = f"{y24b:,}" if y24b > 0 else "—"
            y25s = f"{y25b:,}" if y25b > 0 else "—"
            md += f"| {month_short[m]} | {y24s} | {y25s} | {int(bd['avg']):,} |\n"
        md += f"| **30-day buffer (avg of 3 months)** | | | **{int(sd['g_buf_total']):,}** |\n\n"

    md += "---\n\n"

    # ── SECTION 3: PRINT ORDER INSTRUCTIONS ─────────────────────────────────
    md += "## Section 3: Print Order Instructions\n\n"
    md += ("New print runs ship **direct from the printer to the destination warehouse**. "
           "Do not route prints through a hub — prints going to FBA should be addressed "
           "directly to FBA; prints going to AU should go to the AU warehouse.\n\n"
           "Place orders immediately. Standard lead times (4–8 weeks production + 4–6 weeks "
           "transit) mean orders placed in May arrive July–August, giving time for FBA "
           "inbound processing before peak season.\n\n")

    if not printing_skus:
        md += "✅ **No full print runs required** for this planning period.\n\n"
    else:
        for s in printing_skus:
            sid = s['sku_id']
            sd  = sku_data[sid]
            gap = int(sd['total_need']) - int(sd['total_avail'])

            md += f"### 🖨️ {sd['name']} — {sd['total_print']:,} Units\n\n"
            md += f"*Reason: globally short by {gap:,} units.*\n\n"
            md += "| Destination | Units to Print | Current Stock | Total Need | Gap Filled |\n"
            md += "| :--- | ---: | ---: | ---: | :--- |\n"
            for dest, qty in sd['print_alloc'].items():
                c    = sd['ch'][dest]
                curr = int(c['current'])
                need = int(c['demand'] + c['buffer'])
                gap_filled = f"{qty:,} of {int(c['deficit']):,} deficit"
                uk_note = " (UK→AU blocked)" if dest == 'AU' and not sd['is_journal'] else ""
                md += (f"| {dest.replace('_',' ')} | **{qty:,}** | {curr:,} | "
                       f"{need:,} | {gap_filled}{uk_note} |\n")
            md += (f"\n**Total: {sd['total_print']:,} units.** "
                   f"Ship all units direct from printer. No intermediate warehousing.\n\n")

    if top_up_skus:
        md += "### 🖨️ Top-Up Prints\n\n"
        md += ("Top-up prints are small, targeted orders for channels where the transfer "
               "route is blocked or hub surplus wasn't enough. These happen **in parallel** "
               "with hub→FBA transfers — they don't replace each other.\n\n")
        md += "| SKU | Destination | Units | Why Transfer Wasn't Enough |\n"
        md += "| :--- | :--- | ---: | :--- |\n"
        for s in top_up_skus:
            sid = s['sku_id']
            sd  = sku_data[sid]
            for dest, qty in sd['top_up_print'].items():
                c = sd['ch'][dest]
                if dest == 'AU' and not sd['is_journal']:
                    why = "Cards can't use UK→AU route · no transfer source available"
                elif dest == 'Amazon_CA_FBA':
                    why = f"CA hub surplus exhausted after Shopify reserve · FBA still needs {qty:,}"
                elif dest == 'Amazon_US_FBA':
                    why = f"US hub surplus only covered {int(sd['outgoing_us_hub']):,} · FBA still needs {qty:,}"
                elif dest == 'US_Shopify':
                    why = f"US hubs short on their own Shopify demand · need {qty:,} more at hubs"
                else:
                    why = f"Transfer routes exhausted · {qty:,} unit gap remains"
                md += f"| {sd['name']} | {dest.replace('_',' ')} | **{qty:,}** | {why} |\n"
        md += "\n"

    md += "---\n\n"

    # ── SECTION 4: TRANSFER PLAN ─────────────────────────────────────────────
    md += "## Section 4: Transfer Plan\n\n"
    md += ("**Deadline: September 1, 2026.** FBA inbound processing takes 2–4 weeks — "
           "stock must be checked in to FBA by early October to be available for the "
           "November–December peak. Stock arriving after mid-October may miss the window.\n\n"
           "Hub→FBA transfers only apply to SKUs **not** getting a print run. "
           "For printing SKUs, FBA is filled by the print run directly.\n\n")

    has_transfers = any(sd['transfers'] for sd in sku_data.values())
    if has_transfers:
        md += "| SKU | Transfer | Units | Source Stock | Dest Need | Why |\n"
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

    # ── SECTION 5: CHECKLIST ─────────────────────────────────────────────────
    md += "## Section 5: Action Checklist\n\n"

    md += "### 🖨️ Print Orders — Place Now\n\n"
    if printing_skus:
        for s in printing_skus:
            sd = sku_data[s['sku_id']]
            md += f"- [ ] **{sd['name']}** — order {sd['total_print']:,} units\n"
            for dest, qty in sd['print_alloc'].items():
                md += f"  - [ ] {qty:,} units → {dest.replace('_',' ')} (direct from printer)\n"
        md += "\n"
    else:
        md += "- ✅ No full production runs needed\n\n"

    if top_up_skus:
        md += "### 🖨️ Top-Up Prints — Place Now\n\n"
        for s in top_up_skus:
            sd = sku_data[s['sku_id']]
            md += f"- [ ] **{sd['name']}** top-up prints:\n"
            for dest, qty in sd['top_up_print'].items():
                md += f"  - [ ] {qty:,} units → {dest.replace('_',' ')}\n"
        md += "\n"

    md += "### 📦 Transfers — Complete by September 1\n\n"
    for s in skus:
        sid = s['sku_id']
        sd  = sku_data[sid]
        if sd['transfers']:
            md += f"**{sd['name']}:**\n"
            for t in sd['transfers']:
                md += f"- [ ] {t['source']} → {t['dest'].replace('_',' ')}: {int(t['qty']):,} units\n"
            md += "\n"

    md += "### 📋 Verification Checkpoints\n\n"
    md += "- [ ] Print order lead times confirmed — stock must arrive by August for FBA prep\n"
    md += "- [ ] FBA inbound shipments created in Seller Central with estimated arrival dates\n"
    md += "- [ ] UK→AU journal transfers cleared customs and confirmed in AU system\n"
    md += "- [ ] US hub transfers: confirm Shopify buffer reserved before moving surplus to FBA\n"
    md += "- [ ] **Re-run this plan in August** — adjust if Q3 demand tracks above or below forecast\n"
    md += "- [ ] **Check again in November** — flag early if December is pacing above forecast\n\n"

    md += "---\n\n"
    md += f"*Plan generated May 3, 2026 · Model: max(2024, 2025) per month per channel · Source: `.tmp/data.json`*\n"

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
