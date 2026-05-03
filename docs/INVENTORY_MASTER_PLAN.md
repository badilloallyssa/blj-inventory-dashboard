# Inventory Master Plan: May 2026 – January 2027

*Generated: May 3, 2026 · 8 SKUs · 7 channels · 9-month selling period + 30-day carry-over buffer*

---

## Executive Summary

We're entering the 9-month window from May through January — our most important selling period, with November and December accounting for the majority of annual volume. This plan models demand for all 7 channels (Amazon US FBA, Amazon CA FBA, US Shopify, CA Shopify, UK, EU, AU), sets a 30-day safety buffer for each, and determines exactly what stock needs to move and where — before peak season starts.

**The core rule:** US hubs (HBG/SLI/SAV/KCM) and the CA hub serve Shopify channels first. Only stock above Shopify needs can transfer to FBA. If total stock is still short after counting everything, we print — and new prints ship direct from the factory to the destination, never routed through a hub.

### Actions Required

#### 🖨️ Print Orders

**Kids Journal — 26,134 units**
All channels combined fall **11,304 units short** of covering May–January demand plus a 30-day buffer (75,813 available vs 87,117 needed). Peak month is Dec at 20,248 units globally. Printing:
  - **20,843 units** → Amazon US FBA *(direct from printer)*
  - **2,262 units** → Amazon CA FBA *(direct from printer)*
  - **3,029 units** → US Shopify *(direct from printer)*

**Know Me If You Can Cards — 5,409 units**
All channels combined fall **4,484 units short** of covering May–January demand plus a 30-day buffer (34,177 available vs 38,661 needed). Peak month is Nov at 14,995 units globally. Printing:
  - **1,321 units** → Amazon CA FBA *(direct from printer)*
  - **1,095 units** → CA Shopify *(direct from printer)*
  - **607 units** → UK *(direct from printer)*
  - **35 units** → EU *(direct from printer)*
  - **2,351 units** → AU *(direct from printer)*

#### 📦 Hub→FBA Transfers *(reposition surplus, no print needed)*

**Teen Journal** — globally covered (+27,723 units ahead), but FBA channels are light. Transferring hub surplus:
  - 1,038 units: US Hub → Amazon US FBA

**Sharing Joy Conversation Cards** — globally covered (+3,839 units ahead), but FBA channels are light. Transferring hub surplus:
  - 1,431 units: CA Hub → Amazon CA FBA

**Daily Journal (Teal)** — globally covered (+10,331 units ahead), but FBA channels are light. Transferring hub surplus:
  - 10,185 units: US Hub → Amazon US FBA

**Daily Journal (Green)** — globally covered (+39,503 units ahead), but FBA channels are light. Transferring hub surplus:
  - 6,078 units: US Hub → Amazon US FBA
  - 477 units: CA Hub → Amazon CA FBA

**Adult Journal** — globally covered (+35,631 units ahead), but FBA channels are light. Transferring hub surplus:
  - 5,302 units: US Hub → Amazon US FBA

**Dream Affirmation Cards** — globally covered (+12,764 units ahead), but FBA channels are light. Transferring hub surplus:
  - 3,514 units: US Hub → Amazon US FBA
  - 440 units: CA Hub → Amazon CA FBA

#### 🖨️ Top-Up Prints *(targeted fills where transfer routes are blocked)*

**Teen Journal:**
  - **7,032 units** → Amazon US FBA
  - **744 units** → Amazon CA FBA

**Sharing Joy Conversation Cards:**
  - **1,401 units** → Amazon US FBA
  - **2,514 units** → US Shopify
  - **430 units** → AU

**Daily Journal (Teal):**
  - **1,797 units** → AU

**Dream Affirmation Cards:**
  - **576 units** → Amazon CA FBA

#### ✈️ International Transfers *(UK surplus → AU/EU)*

**Kids Journal:**
  - 5,066 units: UK → AU

**Daily Journal (Teal):**
  - 1,221 units: UK → AU

**Dream Affirmation Cards:**
  - 523 units: UK → EU

### Summary Table

| SKU | Decision | Units | Notes |
| :--- | :--- | ---: | :--- |
| Kids Journal | 🖨️ Print run | 26,134 | Globally short 11,304 units · 5,066 UK→intl |
| Teen Journal | 📦 Transfer + 🖨️ top-up print | 8,814 | 1,038 transfer · 7,776 top-up print |
| Sharing Joy Conversation Cards | 📦 Transfer + 🖨️ top-up print | 5,776 | 1,431 transfer · 4,345 top-up print |
| Daily Journal (Teal) | 📦 Transfer + 🖨️ top-up print | 11,982 | 10,185 transfer · 1,797 top-up print · 1,221 UK→intl |
| Daily Journal (Green) | 📦 Hub→FBA transfer | 6,555 | Globally sufficient |
| Adult Journal | 📦 Hub→FBA transfer | 5,302 | Globally sufficient |
| Dream Affirmation Cards | 📦 Transfer + 🖨️ top-up print | 4,530 | 3,954 transfer · 576 top-up print · 523 UK→intl |
| Know Me If You Can Cards | 🖨️ Print run | 5,409 | Globally short 4,484 units |

---

## Section 1: How the Numbers Were Built

### Demand Forecast: Always Plan for the Worst Month We've Seen

For each channel and each month (May through January), we look at 2024 and 2025 actuals and take the **higher number**. If October 2024 was bigger than October 2025, we plan for October 2024. This means we're prepared for a strong Q4 — not just an average one.

*Example — Kids Journal Q4:*

| Month | 2024 | 2025 | Plan Uses |
| :--- | ---: | ---: | ---: |
| Oct | 3,247 | 2,770 | **3,247** ← 2024 |
| Nov | 8,953 | 17,726 | **17,726** ← 2025 |
| Dec | 19,957 | 20,248 | **20,248** ← 2025 |

### The 30-Day Safety Buffer

We don't plan to hit zero in January. The buffer is the average of what each channel sells in February, March, and April — one month's worth of stock that must still be sitting in the warehouse on February 1st, before the next replenishment arrives. This prevents stockouts in the gap between January and whenever the next order lands.

### The Print vs. Transfer Decision

For each SKU, we ask one question first: **does total stock across all channels cover total demand + buffers?**

- **Yes (globally sufficient):** No print run needed. We reposition hub surplus to FBA instead. Hubs reserve their Shopify demand + buffer; only the excess moves.
- **No (globally short):** A print run is ordered. New stock ships direct from the factory to each short channel — it never routes through a hub first.

This is a binary decision per SKU. We don't mix print runs with hub→FBA transfers for the same SKU. If we're printing, FBA gets stock from the printer. If we're not printing, FBA gets stock from hub surplus.

### Routing Rules

| Route | Allowed? | Why |
| :--- | :--- | :--- |
| UK → AU | ✅ Journals only | Cards can't use this route |
| UK → EU | ✅ All SKUs | |
| US Hub surplus → US FBA | ✅ If no print run | Shopify reserve must be maintained |
| CA Hub surplus → CA FBA | ✅ If no print run | Shopify reserve must be maintained |
| New print → hub → FBA | ❌ | Too slow; prints go direct |
| Canada supplier → US channels | ❌ | Restricted to CA channels only |

---

## Section 2: SKU-by-SKU Analysis

Each SKU section covers: the situation in plain language, the demand forecast, hub surplus math, the specific decision made, what would have happened without that decision, and the full rolling depletion forecast by channel.

---

### Kids Journal `EIDJ4100`

**🖨️ Print 26,134 units** — Short **11,304 units** globally — 75,813 available vs 87,117 needed

> ⚠️ **Globally short 11,304 units** (stock: 75,813 · need: 87,117)

**What needs to happen — and when:**

| Priority | Action | Units | Order / Ship By | Arrives / Done By | Without This Action |
| :---: | :--- | ---: | :--- | :--- | :--- |
| 🚨 | 🖨️ Print → Amazon US FBA | 20,843 | Order **NOW** (May 2026) | Arrive Jul–Aug · Send to FBA by Sep 1 · Checked in Oct | 🚨 Stockout Jun |
| 🚨 | 🖨️ Print → Amazon CA FBA | 2,262 | Order **NOW** (May 2026) | Arrive Jul–Aug · Send to FBA by Sep 1 · Checked in Oct | 🚨 Stockout May |
| 🚨 | 🖨️ Print → US Shopify | 3,029 | Order **NOW** (May 2026) | At destination warehouse by Aug 2026 | 🚨 Stockout Jan |
| 🚨 | 📦 Transfer UK → AU | 5,066 | Ship **now** (ASAP) | At AU ~Jul 2026 | 🚨 Stockout Nov |

*Starting = stock after all transfers / supplier / print runs arrive. Monthly columns = ending balance after cumulative demand is deducted. **Jan must end ≥ Buffer.***

| Channel | On Hand | Action | Starting | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Buffer | ✓ |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Amazon US FBA | 1,935 | +20,843 print | 22,778 | 20,946 | 19,602 | 18,020 | 16,564 | 15,044 | 13,699 | 11,523 | 4,661 | **1,934** | 1,934 | ✅ |
| Amazon CA FBA | 0 | +306 supplier; +2,262 print | 2,568 | 2,235 | 2,027 | 1,915 | 1,746 | 1,627 | 1,539 | 992 | 353 | **135** | 135 | ✅ |
| US Shopify (hubs) | 22,728 | +3,029 print | 25,757 | 23,583 | 22,369 | 21,558 | 20,504 | 19,482 | 18,585 | 11,886 | 3,892 | **1,197** | 1,197 | ✅ |
| CA Shopify (CA hub) | 3,184 | +1,953 supplier | 5,137 | 4,471 | 4,055 | 3,831 | 3,492 | 3,255 | 3,078 | 1,985 | 707 | **270** | 270 | ✅ |
| UK | 33,137 | −5,066→AU | 28,071 | 27,225 | 26,694 | 25,895 | 25,511 | 25,133 | 24,802 | 21,675 | 19,648 | **15,410** | 796 | ✅ |
| EU | 3,590 | — | 3,590 | 3,388 | 3,141 | 2,792 | 2,743 | 2,633 | 2,456 | 1,447 | 445 | **344** | 127 | ✅ |
| AU | 8,979 | +5,066 from UK | 14,045 | 12,956 | 12,164 | 11,402 | 10,738 | 9,907 | 9,228 | 5,048 | 1,479 | **763** | 763 | ✅ |

**Full justification:**

- **Why we're printing:** All 7 channels combined hold **75,813 units** against a total need of **87,117** (May–Jan demand + 30-day buffer per channel) — a **11,304 unit deficit**. There is no transfer fix: stock is short across channels, so new supply from the printer is the only solution. Peak demand hits **Dec** at 20,248 units globally.
- **Why print direct to each destination (not through a hub):** Routing through a hub adds 2–4 weeks of handling and delays FBA inbound. New prints are shipped directly from the factory — FBA shipments use Amazon's inbound address, AU/EU prints go straight to those warehouses. This is the fastest path from printer to sellable inventory.
- **Lead time math:** 4–8 weeks production + 4–6 weeks ocean transit = **8–14 weeks total** from order date to shelf. An order placed **May 2026** arrives **July–August 2026**. For FBA: add 2–4 weeks Amazon inbound processing → stock live in FBA **September–October**, just before November peak. Every week of delay pushes the arrival date further into peak season.
- **Per-channel gap breakdown (how each destination's print qty was calculated):**
  - **Amazon US FBA:** on hand 1,935 · needs 22,778 (demand 20,844 + 30-day buffer 1,934) → gap 20,843 → print **20,843** direct
  - **Amazon CA FBA:** on hand 0 · needs 2,568 (demand 2,433 + 30-day buffer 135) → gap 2,568 → print **2,262** direct
  - **US Shopify:** on hand 22,728 · needs 25,757 (demand 24,560 + 30-day buffer 1,197) → gap 3,029 → print **3,029** direct
- **Without this print run — what breaks and when:**
  - **Amazon US FBA** → 🚨 Stockout Jun — zero inventory, customers see out-of-stock listing
  - **US Shopify** → 🚨 Stockout Jan — zero inventory, customers see out-of-stock listing
  - **Amazon CA FBA** → 🚨 Stockout May — zero inventory, customers see out-of-stock listing

#### Monthly Demand Forecast

*Max of 2024 and 2025 actuals taken for each month — we plan for the strongest Q4 we've seen.*

| Month | 2024 Actual | 2025 Actual | Plan Uses | Cumulative |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 6,607 | 3,091 | **6,607** ← 2024 | 6,607 |
| Jun | 4,297 | 3,247 | **4,297** ← 2024 | 10,904 |
| Jul | 4,161 | 2,584 | **4,161** ← 2024 | 15,065 |
| Aug | 3,897 | 1,501 | **3,897** ← 2024 | 18,962 |
| Sep | 3,988 | 1,789 | **3,988** ← 2024 | 22,950 |
| Oct | 3,247 | 2,770 | **3,247** ← 2024 | 26,197 |
| Nov | 8,953 | 17,726 | **17,726** ← 2025 | 43,923 |
| Dec | 19,957 | 20,248 | **20,248** ← 2025 | 64,171 |
| Jan 2027 | 10,256 | 4,233 | **10,256** ← 2024 | 74,427 |
| **9-Month Total** | | | | **74,427** |

#### 30-Day Safety Buffer Calculation

*Average of Feb, Mar, Apr monthly sales — one month's worth of stock that must remain at end of January.*

| Month | 2024 | 2025 | Monthly Average |
| :--- | ---: | ---: | ---: |
| Feb | 8,761 | 3,682 | 5,074 |
| Mar | 8,221 | 3,184 | 5,107 |
| Apr | 5,733 | 4,147 | 4,940 |
| **30-day buffer (avg of 3 months)** | | | **5,040** |

---

### Teen Journal `EIDJ2100`

**📦 Hub Transfers + 🖨️ Top-Up Prints** — Surplus **+27,723** globally — 1,038 repositioned to FBA · 7,776 top-up printed

> ✅ **Globally sufficient · +27,723 surplus** (stock: 84,718 · need: 56,995)

**What needs to happen — and when:**

| Priority | Action | Units | Order / Ship By | Arrives / Done By | Without This Action |
| :---: | :--- | ---: | :--- | :--- | :--- |
| 🚨 | 🖨️ Top-up → Amazon US FBA | 7,032 | Order **NOW** (May 2026) | Arrive Jul–Aug · Send to FBA by Sep 1 · Checked in Oct | 🚨 Stockout Dec |
| 🚨 | 🖨️ Top-up → Amazon CA FBA | 744 | Order **NOW** (May 2026) | Arrive Jul–Aug · Send to FBA by Sep 1 · Checked in Oct | 🚨 Stockout Dec |
| ⚠️ | 📦 Transfer US Hub → Amazon US FBA | 1,038 | Ship by **Sep 1, 2026** | Checked into FBA by Oct 1 | ⚠️ Below buffer Jan |

*Starting = stock after all transfers / supplier / print runs arrive. Monthly columns = ending balance after cumulative demand is deducted. **Jan must end ≥ Buffer.***

| Channel | On Hand | Action | Starting | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Buffer | ✓ |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Amazon US FBA | 10,284 | +1,038 from US Hub; +7,032 top-up | 18,354 | 16,474 | 14,803 | 13,501 | 12,210 | 10,751 | 9,863 | 7,881 | 3,023 | **1,310** | 1,310 | ✅ |
| Amazon CA FBA | 0 | +1,261 supplier; +744 top-up | 2,006 | 1,895 | 1,608 | 1,481 | 1,391 | 1,266 | 1,182 | 814 | 438 | **87** | 87 | ✅ |
| US Shopify (hubs) | 14,693 | −1,038→US FBA | 13,654 | 12,600 | 11,601 | 10,576 | 9,928 | 9,224 | 8,371 | 6,603 | 1,861 | **623** | 623 | ✅ |
| CA Shopify (CA hub) | 1,723 | +2,289 supplier | 4,012 | 3,791 | 3,216 | 2,963 | 2,782 | 2,532 | 2,365 | 1,628 | 876 | **175** | 175 | ✅ |
| UK | 41,324 | — | 41,324 | 40,627 | 40,101 | 39,733 | 39,506 | 39,225 | 38,879 | 37,619 | 35,238 | **33,699** | 864 | ✅ |
| EU | 2,162 | — | 2,162 | 2,076 | 1,966 | 1,762 | 1,670 | 1,641 | 1,629 | 1,407 | 1,168 | **870** | 139 | ✅ |
| AU | 10,981 | — | 10,981 | 10,308 | 9,426 | 8,782 | 8,193 | 7,617 | 6,934 | 5,254 | 3,169 | **2,449** | 515 | ✅ |

**Full justification:**

- **Why no print run:** 84,718 units available vs 56,995 needed globally = **+27,723 surplus**. The stock exists — we just need to move it to where it sells. Peak demand is **Dec** at 14,818 units globally. Demand model uses the higher of 2024 vs 2025 actuals for every month, so we're planning for the strongest Q4 we've seen — not an average one.
- **US hub math (HBG/SLI/SAV/KCM):** hold 14,693 units total. US Shopify must keep 13,654 reserved (demand 13,031 + buffer 623). **Surplus above Shopify reserve: 1,039.** Transfer **1,038** → Amazon US FBA. Rationale: hub stock sitting in HBG/SLI doesn't appear on Amazon — it has to be in FBA to be sellable on that channel.
- **CA hub:** holds 1,723 — fully reserved for CA Shopify (needs 4,012). No surplus for CA FBA.
- **Why top-up print for Amazon US FBA (+7,032):** US hub surplus was **1,039** — transferred 1,038 to US FBA. US FBA still needs 7,032 more. UK→US warehouse routing is not a confirmed lane, so a direct print run fills the remaining gap. After top-up: 18,354 units vs need 18,354. Without it: Stockout Dec.
- **Why top-up print for Amazon CA FBA (+744):** CA hub surplus was only **0** — fully used up transferring to CA FBA. CA FBA still needs 744 more units that have no transfer source. Print direct to CA FBA is the only remaining option. After top-up: 2,006 units vs need 2,006. Without it: Stockout Dec.
- **Why September 1 is the transfer deadline:** Amazon FBA inbound processing takes 2–4 weeks after the shipment is received at an Amazon fulfillment center. Our peak month is November. For stock to be **available and sellable on November 1**, it must be **checked into FBA by October 1**. Working backwards: ship from the hub or warehouse by **September 1**. Stock that arrives after mid-October is at serious risk of missing peak entirely — Amazon may not process it before Black Friday.
- **Canada supplier stock (3,551 units):** Geography-restricted — these units can only ship to CA-region warehouses (CA hub and Amazon CA FBA). They cannot be rerouted to fill US or international gaps regardless of need.

#### Monthly Demand Forecast

*Max of 2024 and 2025 actuals taken for each month — we plan for the strongest Q4 we've seen.*

| Month | 2024 Actual | 2025 Actual | Plan Uses | Cumulative |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 4,405 | 3,289 | **4,405** ← 2024 | 4,405 |
| Jun | 2,871 | 4,591 | **4,591** ← 2025 | 8,996 |
| Jul | 2,683 | 3,629 | **3,629** ← 2025 | 12,625 |
| Aug | 2,613 | 2,390 | **2,613** ← 2024 | 15,238 |
| Sep | 2,977 | 2,177 | **2,977** ← 2024 | 18,215 |
| Oct | 2,210 | 1,832 | **2,210** ← 2024 | 20,425 |
| Nov | 6,608 | 7,079 | **7,079** ← 2025 | 27,504 |
| Dec | 14,818 | 7,914 | **14,818** ← 2024 | 42,322 |
| Jan 2027 | 5,538 | 5,167 | **5,538** ← 2024 | 47,860 |
| **9-Month Total** | | | | **47,860** |

#### 30-Day Safety Buffer Calculation

*Average of Feb, Mar, Apr monthly sales — one month's worth of stock that must remain at end of January.*

| Month | 2024 | 2025 | Monthly Average |
| :--- | ---: | ---: | ---: |
| Feb | 5,340 | 5,232 | 4,396 |
| Mar | 4,029 | 3,920 | 3,756 |
| Apr | 2,609 | 2,559 | 2,584 |
| **30-day buffer (avg of 3 months)** | | | **3,579** |

---

### Sharing Joy Conversation Cards `EIDC2000`

**📦 Hub Transfers + 🖨️ Top-Up Prints** — Surplus **+3,839** globally — 1,431 repositioned to FBA · 4,345 top-up printed

> ✅ **Globally sufficient · +3,839 surplus** (stock: 59,022 · need: 55,183)

**What needs to happen — and when:**

| Priority | Action | Units | Order / Ship By | Arrives / Done By | Without This Action |
| :---: | :--- | ---: | :--- | :--- | :--- |
| 🚨 | 📦 Transfer CA Hub → Amazon CA FBA | 1,431 | Ship by **Sep 1, 2026** | Checked into FBA by Oct 1 | 🚨 Stockout May |
| 🚨 | 🖨️ Top-up → Amazon US FBA | 1,401 | Order **NOW** (May 2026) | Arrive Jul–Aug · Send to FBA by Sep 1 · Checked in Oct | 🚨 Stockout Jan |
| 🚨 | 🖨️ Top-up → US Shopify | 2,514 | Order **NOW** (May 2026) | At destination warehouse by Aug 2026 | 🚨 Stockout Jan |
| 🚨 | 🖨️ Top-up → AU | 430 | Order **NOW** (May 2026) | At destination warehouse by Aug 2026 | 🚨 Stockout Jan |

*Starting = stock after all transfers / supplier / print runs arrive. Monthly columns = ending balance after cumulative demand is deducted. **Jan must end ≥ Buffer.***

| Channel | On Hand | Action | Starting | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Buffer | ✓ |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Amazon US FBA | 9,662 | +5,500 supplier; +1,401 top-up | 16,563 | 15,188 | 14,046 | 12,981 | 12,128 | 11,509 | 10,563 | 8,521 | 4,685 | **1,250** | 1,250 | ✅ |
| Amazon CA FBA | 0 | +1,431 from CA Hub | 1,431 | 1,320 | 1,213 | 1,113 | 1,075 | 935 | 832 | 581 | 296 | **82** | 82 | ✅ |
| US Shopify (hubs) | 18,064 | +2,514 top-up | 20,578 | 19,437 | 18,276 | 17,337 | 16,685 | 15,220 | 13,688 | 11,395 | 6,753 | **1,419** | 1,419 | ✅ |
| CA Shopify (CA hub) | 4,825 | −1,431→CA FBA | 3,393 | 3,171 | 2,957 | 2,756 | 2,681 | 2,400 | 2,195 | 1,692 | 1,122 | **695** | 165 | ✅ |
| UK | 10,071 | — | 10,071 | 10,063 | 10,044 | 10,031 | 10,023 | 9,747 | 9,543 | 7,197 | 5,440 | **4,714** | 203 | ✅ |
| EU | 4,523 | — | 4,523 | 4,514 | 4,504 | 4,481 | 4,474 | 4,467 | 4,455 | 3,886 | 3,261 | **3,187** | 43 | ✅ |
| AU | 6,377 | +430 top-up | 6,807 | 6,366 | 5,870 | 5,391 | 5,048 | 4,567 | 3,884 | 2,503 | 1,309 | **397** | 397 | ✅ |

**Full justification:**

- **Why no print run:** 59,022 units available vs 55,183 needed globally = **+3,839 surplus**. The stock exists — we just need to move it to where it sells. Peak demand is **Dec** at 11,695 units globally. Demand model uses the higher of 2024 vs 2025 actuals for every month, so we're planning for the strongest Q4 we've seen — not an average one.
- **US hubs:** hold 18,064 — fully reserved for US Shopify (needs 20,578). Zero surplus available for FBA.
- **CA hub math:** holds 4,825. CA Shopify must keep 2,863 reserved (demand 2,698 + buffer 165). **Surplus: 1,962.** Transfer **1,431** → Amazon CA FBA.
- **Why top-up print for Amazon US FBA (+1,401):** US hub surplus was **0** — transferred 0 to US FBA. US FBA still needs 1,401 more. UK→US warehouse routing is not a confirmed lane, so a direct print run fills the remaining gap. After top-up: 16,563 units vs need 16,563. Without it: Stockout Jan.
- **Why top-up print for US Shopify (+2,514):** US hubs are short on their own Shopify demand — the hub stock doesn't even cover Shopify, let alone FBA. Need 2,514 additional units printed direct to the US hub network. After top-up: 20,578 units vs need 20,578. Without it: Stockout Jan.
- **Why top-up print for AU (+430):** Cards **cannot use the UK→AU route** — only journal SKUs are approved for that shipping lane. No other transfer source covers AU for card SKUs. A direct print run to AU is the only available option. After top-up: 6,807 units vs need 6,807. Without it: Stockout Jan.
- **Why September 1 is the transfer deadline:** Amazon FBA inbound processing takes 2–4 weeks after the shipment is received at an Amazon fulfillment center. Our peak month is November. For stock to be **available and sellable on November 1**, it must be **checked into FBA by October 1**. Working backwards: ship from the hub or warehouse by **September 1**. Stock that arrives after mid-October is at serious risk of missing peak entirely — Amazon may not process it before Black Friday.
- **China supplier stock (5,500 units):** Allocated to Amazon US FBA first (highest-priority gap), then overflow to other deficit channels in priority order.

#### Monthly Demand Forecast

*Max of 2024 and 2025 actuals taken for each month — we plan for the strongest Q4 we've seen.*

| Month | 2024 Actual | 2025 Actual | Plan Uses | Cumulative |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | — | 3,196 | **3,196** ← 2025 | 3,196 |
| Jun | — | 3,042 | **3,042** ← 2025 | 6,238 |
| Jul | — | 2,720 | **2,720** ← 2025 | 8,958 |
| Aug | — | 1,938 | **1,938** ← 2025 | 10,896 |
| Sep | 2,503 | 1,509 | **2,503** ← 2024 | 13,399 |
| Oct | 2,350 | 2,668 | **2,668** ← 2025 | 16,067 |
| Nov | 4,363 | 9,134 | **9,134** ← 2025 | 25,201 |
| Dec | 10,462 | 11,695 | **11,695** ← 2025 | 36,896 |
| Jan 2027 | — | 10,908 | **10,908** ← 2025 | 47,804 |
| **9-Month Total** | | | | **47,804** |

#### 30-Day Safety Buffer Calculation

*Average of Feb, Mar, Apr monthly sales — one month's worth of stock that must remain at end of January.*

| Month | 2024 | 2025 | Monthly Average |
| :--- | ---: | ---: | ---: |
| Feb | — | 2,937 | 2,326 |
| Mar | — | 3,975 | 2,758 |
| Apr | — | 5,351 | 5,351 |
| **30-day buffer (avg of 3 months)** | | | **3,478** |

---

### Daily Journal (Teal) `EIDJ5100`

**📦 Hub Transfers + 🖨️ Top-Up Prints** — Surplus **+10,331** globally — 10,185 repositioned to FBA · 1,797 top-up printed

> ✅ **Globally sufficient · +10,331 surplus** (stock: 61,201 · need: 50,870)

**What needs to happen — and when:**

| Priority | Action | Units | Order / Ship By | Arrives / Done By | Without This Action |
| :---: | :--- | ---: | :--- | :--- | :--- |
| 🚨 | 📦 Transfer UK → AU | 1,221 | Ship **now** (ASAP) | At AU ~Jul 2026 | 🚨 Stockout Dec |
| 🚨 | 📦 Transfer US Hub → Amazon US FBA | 10,185 | Ship by **Sep 1, 2026** | Checked into FBA by Oct 1 | 🚨 Stockout Jun |
| 🚨 | 🖨️ Top-up → AU | 1,797 | Order **NOW** (May 2026) | At destination warehouse by Aug 2026 | 🚨 Stockout Dec |

*Starting = stock after all transfers / supplier / print runs arrive. Monthly columns = ending balance after cumulative demand is deducted. **Jan must end ≥ Buffer.***

| Channel | On Hand | Action | Starting | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Buffer | ✓ |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Amazon US FBA | 1,050 | +10,185 from US Hub | 11,235 | 10,499 | 9,763 | 8,716 | 7,809 | 6,940 | 6,144 | 4,741 | 1,921 | **839** | 839 | ✅ |
| Amazon CA FBA | 0 | +1,464 supplier | 1,464 | 1,228 | 1,111 | 993 | 891 | 727 | 635 | 449 | 231 | **103** | 103 | ✅ |
| US Shopify (hubs) | 34,801 | −10,185→US FBA | 24,615 | 23,256 | 22,511 | 21,175 | 19,790 | 18,601 | 17,763 | 16,161 | 12,268 | **11,031** | 688 | ✅ |
| CA Shopify (CA hub) | 4,526 | — | 4,526 | 4,053 | 3,819 | 3,583 | 3,379 | 3,052 | 2,868 | 2,496 | 2,060 | **1,804** | 207 | ✅ |
| UK | 12,161 | −1,221→AU | 10,939 | 10,661 | 10,424 | 9,852 | 8,419 | 7,005 | 5,923 | 4,380 | 2,007 | **682** | 682 | ✅ |
| EU | 958 | — | 958 | 934 | 915 | 835 | 798 | 764 | 730 | 557 | 368 | **251** | 61 | ✅ |
| AU | 6,241 | +1,221 from UK; +1,797 top-up | 9,260 | 8,428 | 7,599 | 6,527 | 5,752 | 4,995 | 4,353 | 2,575 | 918 | **451** | 451 | ✅ |

**Full justification:**

- **Why no print run:** 61,201 units available vs 50,870 needed globally = **+10,331 surplus**. The stock exists — we just need to move it to where it sells. Peak demand is **Dec** at 11,179 units globally. Demand model uses the higher of 2024 vs 2025 actuals for every month, so we're planning for the strongest Q4 we've seen — not an average one.
- **US hub math (HBG/SLI/SAV/KCM):** hold 34,801 units total. US Shopify must keep 14,272 reserved (demand 13,584 + buffer 688). **Surplus above Shopify reserve: 20,529.** Transfer **10,185** → Amazon US FBA. Rationale: hub stock sitting in HBG/SLI doesn't appear on Amazon — it has to be in FBA to be sellable on that channel.
- **CA hub math:** holds 4,526. CA Shopify must keep 2,929 reserved (demand 2,722 + buffer 207). **Surplus: 1,597.**
- **UK → AU transfer:** UK holds 12,161 with only 10,939 needed locally (demand 10,257 + buffer 682) — surplus 1,222 units sitting idle in UK. Transfer **1,221** to fill AU shortfall. Journals are approved for UK→AU ocean freight. Allow 3–4 weeks for ocean transit + customs clearance.
- **Why top-up print for AU (+1,797):** All transfer routes are exhausted — 1,797 unit gap has no transfer source After top-up: 9,260 units vs need 9,260. Without it: Stockout Dec.
- **Why September 1 is the transfer deadline:** Amazon FBA inbound processing takes 2–4 weeks after the shipment is received at an Amazon fulfillment center. Our peak month is November. For stock to be **available and sellable on November 1**, it must be **checked into FBA by October 1**. Working backwards: ship from the hub or warehouse by **September 1**. Stock that arrives after mid-October is at serious risk of missing peak entirely — Amazon may not process it before Black Friday.
- **Canada supplier stock (1,500 units):** Geography-restricted — these units can only ship to CA-region warehouses (CA hub and Amazon CA FBA). They cannot be rerouted to fill US or international gaps regardless of need.

#### Monthly Demand Forecast

*Max of 2024 and 2025 actuals taken for each month — we plan for the strongest Q4 we've seen.*

| Month | 2024 Actual | 2025 Actual | Plan Uses | Cumulative |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 3,567 | 1,806 | **3,567** ← 2024 | 3,567 |
| Jun | 2,655 | 1,323 | **2,655** ← 2024 | 6,222 |
| Jul | 4,263 | 1,174 | **4,263** ← 2024 | 10,485 |
| Aug | 4,704 | 906 | **4,704** ← 2024 | 15,189 |
| Sep | 4,556 | 993 | **4,556** ← 2024 | 19,745 |
| Oct | 3,542 | 1,404 | **3,542** ← 2024 | 23,287 |
| Nov | 6,698 | 3,774 | **6,698** ← 2024 | 29,985 |
| Dec | 11,179 | 5,495 | **11,179** ← 2024 | 41,164 |
| Jan 2027 | 3,580 | 4,193 | **4,193** ← 2025 | 45,357 |
| **9-Month Total** | | | | **45,357** |

#### 30-Day Safety Buffer Calculation

*Average of Feb, Mar, Apr monthly sales — one month's worth of stock that must remain at end of January.*

| Month | 2024 | 2025 | Monthly Average |
| :--- | ---: | ---: | ---: |
| Feb | 2,930 | 3,656 | 2,740 |
| Mar | 2,820 | 2,865 | 2,612 |
| Apr | 4,962 | 1,783 | 3,372 |
| **30-day buffer (avg of 3 months)** | | | **2,908** |

---

### Daily Journal (Green) `EIDJ5200`

**📦 Hub→FBA Repositioning** — Surplus **+39,503** globally — 6,555 units repositioned from hubs to FBA

> ✅ **Globally sufficient · +39,503 surplus** (stock: 62,275 · need: 22,772)

**What needs to happen — and when:**

| Priority | Action | Units | Order / Ship By | Arrives / Done By | Without This Action |
| :---: | :--- | ---: | :--- | :--- | :--- |
| 🚨 | 📦 Transfer US Hub → Amazon US FBA | 6,078 | Ship by **Sep 1, 2026** | Checked into FBA by Oct 1 | 🚨 Stockout Jun |
| 🚨 | 📦 Transfer CA Hub → Amazon CA FBA | 477 | Ship by **Sep 1, 2026** | Checked into FBA by Oct 1 | 🚨 Stockout May |

*Starting = stock after all transfers / supplier / print runs arrive. Monthly columns = ending balance after cumulative demand is deducted. **Jan must end ≥ Buffer.***

| Channel | On Hand | Action | Starting | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Buffer | ✓ |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Amazon US FBA | 1,118 | +6,078 from US Hub | 7,196 | 6,710 | 6,036 | 5,408 | 4,778 | 4,327 | 3,794 | 2,842 | 943 | **438** | 438 | ✅ |
| Amazon CA FBA | 0 | +477 from CA Hub | 477 | 410 | 374 | 337 | 304 | 266 | 237 | 161 | 86 | **36** | 36 | ✅ |
| US Shopify (hubs) | 19,209 | −6,078→US FBA | 13,131 | 12,449 | 12,169 | 11,724 | 11,278 | 10,928 | 10,563 | 9,560 | 8,273 | **7,821** | 358 | ✅ |
| CA Shopify (CA hub) | 4,274 | −477→CA FBA | 3,797 | 3,664 | 3,592 | 3,517 | 3,451 | 3,376 | 3,317 | 3,165 | 3,015 | **2,916** | 73 | ✅ |
| UK | 31,861 | — | 31,861 | 31,098 | 30,903 | 30,649 | 30,329 | 29,981 | 29,631 | 29,020 | 28,026 | **27,343** | 480 | ✅ |
| EU | 938 | — | 938 | 873 | 817 | 717 | 691 | 675 | 657 | 547 | 436 | **379** | 23 | ✅ |
| AU | 4,875 | — | 4,875 | 4,587 | 4,342 | 3,990 | 3,759 | 3,537 | 3,348 | 2,737 | 2,325 | **2,134** | 155 | ✅ |

**Full justification:**

- **Why no print run:** 62,275 units available vs 22,772 needed globally = **+39,503 surplus**. The stock exists — we just need to move it to where it sells. Peak demand is **Dec** at 4,700 units globally. Demand model uses the higher of 2024 vs 2025 actuals for every month, so we're planning for the strongest Q4 we've seen — not an average one.
- **US hub math (HBG/SLI/SAV/KCM):** hold 19,209 units total. US Shopify must keep 5,668 reserved (demand 5,310 + buffer 358). **Surplus above Shopify reserve: 13,541.** Transfer **6,078** → Amazon US FBA. Rationale: hub stock sitting in HBG/SLI doesn't appear on Amazon — it has to be in FBA to be sellable on that channel.
- **CA hub math:** holds 4,274. CA Shopify must keep 954 reserved (demand 881 + buffer 73). **Surplus: 3,320.** Transfer **477** → Amazon CA FBA.
- **Why September 1 is the transfer deadline:** Amazon FBA inbound processing takes 2–4 weeks after the shipment is received at an Amazon fulfillment center. Our peak month is November. For stock to be **available and sellable on November 1**, it must be **checked into FBA by October 1**. Working backwards: ship from the hub or warehouse by **September 1**. Stock that arrives after mid-October is at serious risk of missing peak entirely — Amazon may not process it before Black Friday.

#### Monthly Demand Forecast

*Max of 2024 and 2025 actuals taken for each month — we plan for the strongest Q4 we've seen.*

| Month | 2024 Actual | 2025 Actual | Plan Uses | Cumulative |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 2,352 | 839 | **2,352** ← 2024 | 2,352 |
| Jun | 1,466 | 772 | **1,466** ← 2024 | 3,818 |
| Jul | 1,754 | 657 | **1,754** ← 2024 | 5,572 |
| Aug | 1,693 | 449 | **1,693** ← 2024 | 7,265 |
| Sep | 1,446 | 485 | **1,446** ← 2024 | 8,711 |
| Oct | 1,496 | 504 | **1,496** ← 2024 | 10,207 |
| Nov | 3,020 | 2,443 | **3,020** ← 2024 | 13,227 |
| Dec | 4,700 | 2,800 | **4,700** ← 2024 | 17,927 |
| Jan 2027 | 1,322 | 1,987 | **1,987** ← 2025 | 19,914 |
| **9-Month Total** | | | | **19,914** |

#### 30-Day Safety Buffer Calculation

*Average of Feb, Mar, Apr monthly sales — one month's worth of stock that must remain at end of January.*

| Month | 2024 | 2025 | Monthly Average |
| :--- | ---: | ---: | ---: |
| Feb | 942 | 1,657 | 1,088 |
| Mar | 487 | 1,487 | 1,009 |
| Apr | 3,948 | 975 | 2,461 |
| **30-day buffer (avg of 3 months)** | | | **1,519** |

---

### Adult Journal `EIDJ5000`

**📦 Hub→FBA Repositioning** — Surplus **+35,631** globally — 5,302 units repositioned from hubs to FBA

> ✅ **Globally sufficient · +35,631 surplus** (stock: 62,873 · need: 27,242)

**What needs to happen — and when:**

| Priority | Action | Units | Order / Ship By | Arrives / Done By | Without This Action |
| :---: | :--- | ---: | :--- | :--- | :--- |
| 🚨 | 📦 Transfer US Hub → Amazon US FBA | 5,302 | Ship by **Sep 1, 2026** | Checked into FBA by Oct 1 | 🚨 Stockout May |

*Starting = stock after all transfers / supplier / print runs arrive. Monthly columns = ending balance after cumulative demand is deducted. **Jan must end ≥ Buffer.***

| Channel | On Hand | Action | Starting | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Buffer | ✓ |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Amazon US FBA | 415 | +5,302 from US Hub | 5,717 | 5,128 | 4,708 | 4,279 | 3,892 | 3,579 | 3,306 | 2,801 | 1,194 | **289** | 289 | ✅ |
| Amazon CA FBA | 0 | +831 supplier | 831 | 786 | 745 | 708 | 692 | 664 | 644 | 469 | 286 | **36** | 36 | ✅ |
| US Shopify (hubs) | 37,634 | −5,302→US FBA | 32,331 | 31,866 | 31,497 | 31,166 | 30,967 | 30,804 | 30,480 | 29,579 | 26,725 | **25,238** | 156 | ✅ |
| CA Shopify (CA hub) | 4,929 | — | 4,929 | 4,840 | 4,757 | 4,684 | 4,652 | 4,595 | 4,556 | 4,206 | 3,840 | **3,340** | 73 | ✅ |
| UK | 11,565 | — | 11,565 | 11,018 | 10,494 | 10,171 | 9,912 | 9,726 | 9,411 | 8,276 | 5,434 | **4,673** | 224 | ✅ |
| EU | 1,599 | — | 1,599 | 1,574 | 1,522 | 1,164 | 1,158 | 1,144 | 1,136 | 1,069 | 994 | **922** | 30 | ✅ |
| AU | 5,900 | — | 5,900 | 5,641 | 5,415 | 5,206 | 5,058 | 4,913 | 4,797 | 4,143 | 2,742 | **2,085** | 142 | ✅ |

**Full justification:**

- **Why no print run:** 62,873 units available vs 27,242 needed globally = **+35,631 surplus**. The stock exists — we just need to move it to where it sells. Peak demand is **Dec** at 9,070 units globally. Demand model uses the higher of 2024 vs 2025 actuals for every month, so we're planning for the strongest Q4 we've seen — not an average one.
- **US hub math (HBG/SLI/SAV/KCM):** hold 37,634 units total. US Shopify must keep 7,249 reserved (demand 7,093 + buffer 156). **Surplus above Shopify reserve: 30,385.** Transfer **5,302** → Amazon US FBA. Rationale: hub stock sitting in HBG/SLI doesn't appear on Amazon — it has to be in FBA to be sellable on that channel.
- **CA hub math:** holds 4,929. CA Shopify must keep 1,662 reserved (demand 1,589 + buffer 73). **Surplus: 3,267.**
- **Why September 1 is the transfer deadline:** Amazon FBA inbound processing takes 2–4 weeks after the shipment is received at an Amazon fulfillment center. Our peak month is November. For stock to be **available and sellable on November 1**, it must be **checked into FBA by October 1**. Working backwards: ship from the hub or warehouse by **September 1**. Stock that arrives after mid-October is at serious risk of missing peak entirely — Amazon may not process it before Black Friday.
- **Canada supplier stock (1,472 units):** Geography-restricted — these units can only ship to CA-region warehouses (CA hub and Amazon CA FBA). They cannot be rerouted to fill US or international gaps regardless of need.

#### Monthly Demand Forecast

*Max of 2024 and 2025 actuals taken for each month — we plan for the strongest Q4 we've seen.*

| Month | 2024 Actual | 2025 Actual | Plan Uses | Cumulative |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 1,949 | 537 | **1,949** ← 2024 | 1,949 |
| Jun | 1,622 | 627 | **1,622** ← 2024 | 3,571 |
| Jul | 1,365 | 688 | **1,365** ← 2024 | 4,936 |
| Aug | 1,016 | 496 | **1,016** ← 2024 | 5,952 |
| Sep | 864 | 312 | **864** ← 2024 | 6,816 |
| Oct | 806 | 670 | **806** ← 2024 | 7,622 |
| Nov | 3,545 | 1,718 | **3,545** ← 2024 | 11,167 |
| Dec | 9,070 | 1,975 | **9,070** ← 2024 | 20,237 |
| Jan 2027 | 3,663 | 2,418 | **3,663** ← 2024 | 23,900 |
| **9-Month Total** | | | | **23,900** |

#### 30-Day Safety Buffer Calculation

*Average of Feb, Mar, Apr monthly sales — one month's worth of stock that must remain at end of January.*

| Month | 2024 | 2025 | Monthly Average |
| :--- | ---: | ---: | ---: |
| Feb | 1,256 | 1,051 | 985 |
| Mar | 1,081 | 695 | 846 |
| Apr | 1,357 | 421 | 889 |
| **30-day buffer (avg of 3 months)** | | | **906** |

---

### Dream Affirmation Cards `EIDC2101`

**📦 Hub Transfers + 🖨️ Top-Up Prints** — Surplus **+12,764** globally — 3,954 repositioned to FBA · 576 top-up printed

> ✅ **Globally sufficient · +12,764 surplus** (stock: 43,091 · need: 30,327)

**What needs to happen — and when:**

| Priority | Action | Units | Order / Ship By | Arrives / Done By | Without This Action |
| :---: | :--- | ---: | :--- | :--- | :--- |
| 🚨 | 📦 Transfer UK → EU | 523 | Ship **now** (ASAP) | At EU ~Jul 2026 | 🚨 Stockout Dec |
| 🚨 | 📦 Transfer US Hub → Amazon US FBA | 3,514 | Ship by **Sep 1, 2026** | Checked into FBA by Oct 1 | 🚨 Stockout Sep |
| 🚨 | 📦 Transfer CA Hub → Amazon CA FBA | 440 | Ship by **Sep 1, 2026** | Checked into FBA by Oct 1 | 🚨 Stockout Nov |
| 🚨 | 🖨️ Top-up → Amazon CA FBA | 576 | Order **NOW** (May 2026) | Arrive Jul–Aug · Send to FBA by Sep 1 · Checked in Oct | 🚨 Stockout Oct |

*Starting = stock after all transfers / supplier / print runs arrive. Monthly columns = ending balance after cumulative demand is deducted. **Jan must end ≥ Buffer.***

| Channel | On Hand | Action | Starting | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Buffer | ✓ |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Amazon US FBA | 794 | +3,514 from US Hub | 4,308 | 4,012 | 3,850 | 3,699 | 3,516 | 3,340 | 3,094 | 2,003 | 797 | **351** | 351 | ✅ |
| Amazon CA FBA | 0 | +440 from CA Hub; +576 top-up | 1,016 | 957 | 943 | 931 | 915 | 727 | 554 | 302 | 132 | **68** | 68 | ✅ |
| US Shopify (hubs) | 25,105 | −3,514→US FBA | 21,590 | 21,314 | 21,205 | 20,940 | 20,780 | 18,677 | 16,520 | 14,921 | 12,067 | **11,221** | 582 | ✅ |
| CA Shopify (CA hub) | 2,474 | −440→CA FBA | 2,033 | 1,914 | 1,886 | 1,863 | 1,830 | 1,454 | 1,108 | 605 | 264 | **137** | 137 | ✅ |
| UK | 9,234 | −523→EU | 8,710 | 8,593 | 8,464 | 8,422 | 8,408 | 7,739 | 7,176 | 4,830 | 3,036 | **2,594** | 108 | ✅ |
| EU | 943 | +523 from UK | 1,466 | 1,380 | 1,356 | 1,318 | 1,311 | 1,310 | 1,293 | 724 | 165 | **58** | 58 | ✅ |
| AU | 4,541 | — | 4,541 | 4,356 | 4,276 | 4,181 | 4,115 | 3,502 | 2,786 | 1,405 | 659 | **409** | 194 | ✅ |

**Full justification:**

- **Why no print run:** 43,091 units available vs 30,327 needed globally = **+12,764 surplus**. The stock exists — we just need to move it to where it sells. Peak demand is **Nov** at 7,489 units globally. Demand model uses the higher of 2024 vs 2025 actuals for every month, so we're planning for the strongest Q4 we've seen — not an average one.
- **US hub math (HBG/SLI/SAV/KCM):** hold 25,105 units total. US Shopify must keep 10,951 reserved (demand 10,369 + buffer 582). **Surplus above Shopify reserve: 14,154.** Transfer **3,514** → Amazon US FBA. Rationale: hub stock sitting in HBG/SLI doesn't appear on Amazon — it has to be in FBA to be sellable on that channel.
- **CA hub math:** holds 2,474. CA Shopify must keep 2,033 reserved (demand 1,896 + buffer 137). **Surplus: 441.** Transfer **440** → Amazon CA FBA.
- **UK → EU transfer:** UK holds 9,234 with only 6,224 needed locally (demand 6,116 + buffer 108) — surplus 3,010 units sitting idle in UK. Transfer **523** to fill EU shortfall. All SKUs can use UK→EU routing. Allow 3–4 weeks for ocean transit + customs clearance.
- **Why top-up print for Amazon CA FBA (+576):** CA hub surplus was only **441** — fully used up transferring to CA FBA. CA FBA still needs 576 more units that have no transfer source. Print direct to CA FBA is the only remaining option. After top-up: 1,016 units vs need 1,016. Without it: Stockout Oct.
- **Why September 1 is the transfer deadline:** Amazon FBA inbound processing takes 2–4 weeks after the shipment is received at an Amazon fulfillment center. Our peak month is November. For stock to be **available and sellable on November 1**, it must be **checked into FBA by October 1**. Working backwards: ship from the hub or warehouse by **September 1**. Stock that arrives after mid-October is at serious risk of missing peak entirely — Amazon may not process it before Black Friday.

#### Monthly Demand Forecast

*Max of 2024 and 2025 actuals taken for each month — we plan for the strongest Q4 we've seen.*

| Month | 2024 Actual | 2025 Actual | Plan Uses | Cumulative |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | — | 1,079 | **1,079** ← 2025 | 1,079 |
| Jun | — | 532 | **532** ← 2025 | 1,611 |
| Jul | — | 614 | **614** ← 2025 | 2,225 |
| Aug | — | 463 | **463** ← 2025 | 2,688 |
| Sep | 3,761 | 326 | **3,761** ← 2024 | 6,449 |
| Oct | 3,943 | 584 | **3,943** ← 2024 | 10,392 |
| Nov | 3,884 | 7,489 | **7,489** ← 2025 | 17,881 |
| Dec | 6,648 | 5,140 | **6,648** ← 2024 | 24,529 |
| Jan 2027 | — | 2,056 | **2,056** ← 2025 | 26,585 |
| **9-Month Total** | | | | **26,585** |

#### 30-Day Safety Buffer Calculation

*Average of Feb, Mar, Apr monthly sales — one month's worth of stock that must remain at end of January.*

| Month | 2024 | 2025 | Monthly Average |
| :--- | ---: | ---: | ---: |
| Feb | — | 1,159 | 975 |
| Mar | — | 958 | 864 |
| Apr | — | 2,459 | 2,459 |
| **30-day buffer (avg of 3 months)** | | | **1,432** |

---

### Know Me If You Can Cards `EIDJB5002`

**🖨️ Print 5,409 units** — Short **4,484 units** globally — 34,177 available vs 38,661 needed

> ⚠️ **Globally short 4,484 units** (stock: 34,177 · need: 38,661)

**What needs to happen — and when:**

| Priority | Action | Units | Order / Ship By | Arrives / Done By | Without This Action |
| :---: | :--- | ---: | :--- | :--- | :--- |
| 🚨 | 🖨️ Print → Amazon CA FBA | 1,321 | Order **NOW** (May 2026) | Arrive Jul–Aug · Send to FBA by Sep 1 · Checked in Oct | 🚨 Stockout Jun |
| 🚨 | 🖨️ Print → CA Shopify | 1,095 | Order **NOW** (May 2026) | At destination warehouse by Aug 2026 | 🚨 Stockout Nov |
| 🚨 | 🖨️ Print → UK | 607 | Order **NOW** (May 2026) | At destination warehouse by Aug 2026 | 🚨 Stockout Dec |
| 🚨 | 🖨️ Print → AU | 2,351 | Order **NOW** (May 2026) | At destination warehouse by Aug 2026 | 🚨 Stockout Nov |
| ⚠️ | 🖨️ Print → EU | 35 | Order **NOW** (May 2026) | At destination warehouse by Aug 2026 | ⚠️ Below buffer Dec |

*Starting = stock after all transfers / supplier / print runs arrive. Monthly columns = ending balance after cumulative demand is deducted. **Jan must end ≥ Buffer.***

| Channel | On Hand | Action | Starting | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Buffer | ✓ |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Amazon US FBA | 7,426 | +2,077 supplier | 9,503 | 9,503 | 9,503 | 9,503 | 9,503 | 9,455 | 9,281 | 5,687 | 1,089 | **216** | 216 | ✅ |
| Amazon CA FBA | 0 | +1,321 print | 1,321 | 1,321 | 1,227 | 1,211 | 1,153 | 1,095 | 1,047 | 479 | 106 | **25** | 25 | ✅ |
| US Shopify (hubs) | 15,083 | — | 15,083 | 15,083 | 13,953 | 13,724 | 13,173 | 12,327 | 11,625 | 6,437 | 1,907 | **1,076** | 149 | ✅ |
| CA Shopify (CA hub) | 1,547 | +1,095 print | 2,642 | 2,642 | 2,455 | 2,423 | 2,307 | 2,190 | 2,095 | 959 | 212 | **51** | 51 | ✅ |
| UK | 3,368 | +607 print | 3,975 | 3,975 | 3,796 | 3,796 | 3,787 | 3,785 | 3,714 | 1,275 | 358 | **67** | 67 | ✅ |
| EU | 681 | +35 print | 716 | 716 | 650 | 637 | 588 | 551 | 447 | 299 | 78 | **44** | 44 | ✅ |
| AU | 3,128 | +866 supplier; +2,351 print | 6,345 | 6,345 | 5,981 | 5,824 | 5,315 | 4,940 | 4,512 | 2,022 | 517 | **78** | 78 | ✅ |

**Full justification:**

- **Why we're printing:** All 7 channels combined hold **34,177 units** against a total need of **38,661** (May–Jan demand + 30-day buffer per channel) — a **4,484 unit deficit**. There is no transfer fix: stock is short across channels, so new supply from the printer is the only solution. Peak demand hits **Nov** at 14,995 units globally.
- **Why print direct to each destination (not through a hub):** Routing through a hub adds 2–4 weeks of handling and delays FBA inbound. New prints are shipped directly from the factory — FBA shipments use Amazon's inbound address, AU/EU prints go straight to those warehouses. This is the fastest path from printer to sellable inventory.
- **Lead time math:** 4–8 weeks production + 4–6 weeks ocean transit = **8–14 weeks total** from order date to shelf. An order placed **May 2026** arrives **July–August 2026**. For FBA: add 2–4 weeks Amazon inbound processing → stock live in FBA **September–October**, just before November peak. Every week of delay pushes the arrival date further into peak season.
- **Per-channel gap breakdown (how each destination's print qty was calculated):**
  - **Amazon CA FBA:** on hand 0 · needs 1,321 (demand 1,295 + 30-day buffer 25) → gap 1,321 → print **1,321** direct
  - **CA Shopify:** on hand 1,547 · needs 2,642 (demand 2,591 + 30-day buffer 51) → gap 1,095 → print **1,095** direct
  - **UK:** on hand 3,368 · needs 3,975 (demand 3,908 + 30-day buffer 67) → gap 607 → print **607** direct
  - **EU:** on hand 681 · needs 716 (demand 672 + 30-day buffer 44) → gap 35 → print **35** direct
  - **AU:** on hand 3,128 · needs 6,345 (demand 6,267 + 30-day buffer 78) → gap 3,217 → print **2,351** direct
- **Without this print run — what breaks and when:**
  - **AU** → 🚨 Stockout Nov — zero inventory, customers see out-of-stock listing
  - **Amazon CA FBA** → 🚨 Stockout Jun — zero inventory, customers see out-of-stock listing
  - **CA Shopify** → 🚨 Stockout Nov — zero inventory, customers see out-of-stock listing
  - **UK** → 🚨 Stockout Dec — zero inventory, customers see out-of-stock listing
  - **EU** → ⚠️ Below buffer Dec — exposed if demand spikes even slightly

#### Monthly Demand Forecast

*Max of 2024 and 2025 actuals taken for each month — we plan for the strongest Q4 we've seen.*

| Month | 2024 Actual | 2025 Actual | Plan Uses | Cumulative |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | — | — | — | 0 |
| Jun | — | 1,926 | **1,926** ← 2025 | 1,926 |
| Jul | — | 431 | **431** ← 2025 | 2,357 |
| Aug | — | 1,234 | **1,234** ← 2025 | 3,591 |
| Sep | — | 1,425 | **1,425** ← 2025 | 5,016 |
| Oct | — | 1,574 | **1,574** ← 2025 | 6,590 |
| Nov | — | 14,995 | **14,995** ← 2025 | 21,585 |
| Dec | — | 12,518 | **12,518** ← 2025 | 34,103 |
| Jan 2027 | — | — | — | 34,103 |
| **9-Month Total** | | | | **34,103** |

#### 30-Day Safety Buffer Calculation

*Average of Feb, Mar, Apr monthly sales — one month's worth of stock that must remain at end of January.*

| Month | 2024 | 2025 | Monthly Average |
| :--- | ---: | ---: | ---: |
| Feb | — | — | 981 |
| Mar | — | — | 844 |
| Apr | — | — | 0 |
| **30-day buffer (avg of 3 months)** | | | **608** |

---

## Section 3: Print Order Instructions

New print runs ship **direct from the printer to the destination warehouse**. Do not route prints through a hub — prints going to FBA should be addressed directly to FBA; prints going to AU should go to the AU warehouse.

Place orders immediately. Standard lead times (4–8 weeks production + 4–6 weeks transit) mean orders placed in May arrive July–August, giving time for FBA inbound processing before peak season.

### 🖨️ Kids Journal — 26,134 Units

*Reason: globally short by 11,304 units.*

| Destination | Units to Print | Current Stock | Total Need | Gap Filled |
| :--- | ---: | ---: | ---: | :--- |
| Amazon US FBA | **20,843** | 1,935 | 22,778 | 20,843 of 20,843 deficit |
| Amazon CA FBA | **2,262** | 0 | 2,568 | 2,262 of 2,568 deficit |
| US Shopify | **3,029** | 22,728 | 25,757 | 3,029 of 3,029 deficit |

**Total: 26,134 units.** Ship all units direct from printer. No intermediate warehousing.

### 🖨️ Know Me If You Can Cards — 5,409 Units

*Reason: globally short by 4,484 units.*

| Destination | Units to Print | Current Stock | Total Need | Gap Filled |
| :--- | ---: | ---: | ---: | :--- |
| Amazon CA FBA | **1,321** | 0 | 1,321 | 1,321 of 1,321 deficit |
| CA Shopify | **1,095** | 1,547 | 2,642 | 1,095 of 1,095 deficit |
| UK | **607** | 3,368 | 3,975 | 607 of 607 deficit |
| EU | **35** | 681 | 716 | 35 of 35 deficit |
| AU | **2,351** | 3,128 | 6,345 | 2,351 of 3,217 deficit (UK→AU blocked) |

**Total: 5,409 units.** Ship all units direct from printer. No intermediate warehousing.

### 🖨️ Top-Up Prints

Top-up prints are small, targeted orders for channels where the transfer route is blocked or hub surplus wasn't enough. These happen **in parallel** with hub→FBA transfers — they don't replace each other.

| SKU | Destination | Units | Why Transfer Wasn't Enough |
| :--- | :--- | ---: | :--- |
| Teen Journal | Amazon US FBA | **7,032** | US hub surplus only covered 1,038 · FBA still needs 7,032 |
| Teen Journal | Amazon CA FBA | **744** | CA hub surplus exhausted after Shopify reserve · FBA still needs 744 |
| Sharing Joy Conversation Cards | Amazon US FBA | **1,401** | US hub surplus only covered 0 · FBA still needs 1,401 |
| Sharing Joy Conversation Cards | US Shopify | **2,514** | US hubs short on their own Shopify demand · need 2,514 more at hubs |
| Sharing Joy Conversation Cards | AU | **430** | Cards can't use UK→AU route · no transfer source available |
| Daily Journal (Teal) | AU | **1,797** | Transfer routes exhausted · 1,797 unit gap remains |
| Dream Affirmation Cards | Amazon CA FBA | **576** | CA hub surplus exhausted after Shopify reserve · FBA still needs 576 |

---

## Section 4: Transfer Plan

**Deadline: September 1, 2026.** FBA inbound processing takes 2–4 weeks — stock must be checked in to FBA by early October to be available for the November–December peak. Stock arriving after mid-October may miss the window.

Hub→FBA transfers only apply to SKUs **not** getting a print run. For printing SKUs, FBA is filled by the print run directly.

| SKU | Transfer | Units | Source Stock | Dest Need | Why |
| :--- | :--- | ---: | ---: | ---: | :--- |
| Kids Journal | UK → AU | **5,066** | 33,137 | 14,045 | AU needs 14,045 (demand + buffer); AU has 8,979; deficit 5,066; UK surplus 19,679 |
| Teen Journal | US Hub → Amazon US FBA | **1,038** | 14,693 | 18,354 | US hubs have 14,693; Shopify needs 13,654 (demand + buffer); surplus 1,038; US FBA gap 8,070 |
| Sharing Joy Conversation Cards | CA Hub → Amazon CA FBA | **1,431** | 4,825 | 1,431 | CA hub has 4,825; CA Shopify needs 2,863 (demand + buffer); surplus 1,961; CA FBA gap 1,431 |
| Daily Journal (Teal) | UK → AU | **1,221** | 12,161 | 9,260 | AU needs 9,260 (demand + buffer); AU has 6,241; deficit 3,019; UK surplus 1,221 |
| Daily Journal (Teal) | US Hub → Amazon US FBA | **10,185** | 34,801 | 11,235 | US hubs have 34,801; Shopify needs 14,272 (demand + buffer); surplus 20,528; US FBA gap 10,185 |
| Daily Journal (Green) | US Hub → Amazon US FBA | **6,078** | 19,209 | 7,196 | US hubs have 19,209; Shopify needs 5,668 (demand + buffer); surplus 13,540; US FBA gap 6,078 |
| Daily Journal (Green) | CA Hub → Amazon CA FBA | **477** | 4,274 | 477 | CA hub has 4,274; CA Shopify needs 954 (demand + buffer); surplus 3,320; CA FBA gap 477 |
| Adult Journal | US Hub → Amazon US FBA | **5,302** | 37,634 | 5,717 | US hubs have 37,634; Shopify needs 7,249 (demand + buffer); surplus 30,384; US FBA gap 5,302 |
| Dream Affirmation Cards | UK → EU | **523** | 9,234 | 1,466 | EU needs 1,466; EU has 943; deficit 523; UK surplus 3,009 |
| Dream Affirmation Cards | US Hub → Amazon US FBA | **3,514** | 25,105 | 4,308 | US hubs have 25,105; Shopify needs 10,951 (demand + buffer); surplus 14,153; US FBA gap 3,514 |
| Dream Affirmation Cards | CA Hub → Amazon CA FBA | **440** | 2,474 | 1,016 | CA hub has 2,474; CA Shopify needs 2,033 (demand + buffer); surplus 440; CA FBA gap 1,016 |

---

## Section 5: Action Checklist

### 🖨️ Print Orders — Place Now

- [ ] **Kids Journal** — order 26,134 units
  - [ ] 20,843 units → Amazon US FBA (direct from printer)
  - [ ] 2,262 units → Amazon CA FBA (direct from printer)
  - [ ] 3,029 units → US Shopify (direct from printer)
- [ ] **Know Me If You Can Cards** — order 5,409 units
  - [ ] 1,321 units → Amazon CA FBA (direct from printer)
  - [ ] 1,095 units → CA Shopify (direct from printer)
  - [ ] 607 units → UK (direct from printer)
  - [ ] 35 units → EU (direct from printer)
  - [ ] 2,351 units → AU (direct from printer)

### 🖨️ Top-Up Prints — Place Now

- [ ] **Teen Journal** top-up prints:
  - [ ] 7,032 units → Amazon US FBA
  - [ ] 744 units → Amazon CA FBA
- [ ] **Sharing Joy Conversation Cards** top-up prints:
  - [ ] 1,401 units → Amazon US FBA
  - [ ] 2,514 units → US Shopify
  - [ ] 430 units → AU
- [ ] **Daily Journal (Teal)** top-up prints:
  - [ ] 1,797 units → AU
- [ ] **Dream Affirmation Cards** top-up prints:
  - [ ] 576 units → Amazon CA FBA

### 📦 Transfers — Complete by September 1

**Kids Journal:**
- [ ] UK → AU: 5,066 units

**Teen Journal:**
- [ ] US Hub → Amazon US FBA: 1,038 units

**Sharing Joy Conversation Cards:**
- [ ] CA Hub → Amazon CA FBA: 1,431 units

**Daily Journal (Teal):**
- [ ] UK → AU: 1,221 units
- [ ] US Hub → Amazon US FBA: 10,185 units

**Daily Journal (Green):**
- [ ] US Hub → Amazon US FBA: 6,078 units
- [ ] CA Hub → Amazon CA FBA: 477 units

**Adult Journal:**
- [ ] US Hub → Amazon US FBA: 5,302 units

**Dream Affirmation Cards:**
- [ ] UK → EU: 523 units
- [ ] US Hub → Amazon US FBA: 3,514 units
- [ ] CA Hub → Amazon CA FBA: 440 units

### 📋 Verification Checkpoints

- [ ] Print order lead times confirmed — stock must arrive by August for FBA prep
- [ ] FBA inbound shipments created in Seller Central with estimated arrival dates
- [ ] UK→AU journal transfers cleared customs and confirmed in AU system
- [ ] US hub transfers: confirm Shopify buffer reserved before moving surplus to FBA
- [ ] **Re-run this plan in August** — adjust if Q3 demand tracks above or below forecast
- [ ] **Check again in November** — flag early if December is pacing above forecast

---

*Plan generated May 3, 2026 · Model: max(2024, 2025) per month per channel · Source: `.tmp/data.json`*
