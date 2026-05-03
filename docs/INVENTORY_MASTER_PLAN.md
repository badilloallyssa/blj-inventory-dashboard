# Inventory Master Plan: May 2026 – January 2027

*Generated: May 3, 2026 · 9-month active period + 90-day carry-over buffer · 8 SKUs · 10 warehouses*

---

## Executive Summary

This plan ensures we have the right stock, in the right place, from **May 2026 through April 2027**. It covers the full Q4 peak season and carries enough buffer into Q1 2027 that we won't touch zero before the next order cycle.

### Actions Required

**Print Orders (place now):**

- **Kids Journal** — order **13,735 units**
- **Know Me If You Can Cards** — order **1,751 units**

**Warehouse Transfers (21 moves — execute before September):**
Stock must move from regional hubs into FBA now. FBA processing takes 2–4 weeks; if transfers happen in October the stock won't be live for November peak.

### Plan at a Glance

| | |
| :--- | :--- |
| Active selling period | May 2026 – Jan 2027 (9 months) |
| Buffer carry-over | Feb – Apr 2027 (90 days) |
| SKUs in plan | 8 |
| New print orders | 2 SKUs · 15,486 units total |
| Warehouse transfers | 21 moves |
| Demand model | Historical max per month (stress-test) |
| Buffer model | Historical average of Feb + Mar + Apr |

---

## Section 1: How the Numbers Were Calculated

### The Question We're Answering

How much inventory do we need, globally and per region, to get through Q4 without stockouts — and still have 90 days of stock left in January before we place our next order?

### Step 1 — Demand Forecast: Always Use the Maximum

For each SKU and each month, we look at 2024 sales and 2025 sales and take the **higher number**. We never average them. The logic: if we've ever sold that many in a given month, we need to be ready to sell that many again. This is especially important for Q4 where one strong November can define the year.

**Example — Kids Journal, October:**

| | Units |
| :--- | ---: |
| 2024 October actual | 3,247 |
| 2025 October actual | 2,770 |
| **We plan for** | **3,247** ← the higher of the two |

We do this for every month May through January, then sum the 9 months. That total is the demand forecast.

### Step 2 — Safety Buffer: 90 Days Left After January

We don't want to start February with zero stock. The buffer is the average of what we historically sell in February, March, and April — the slow months right after peak season. That amount must still be sitting in the warehouse on February 1st.

**Example — Kids Journal buffer:**

| Buffer Month | Historical Sales | Average |
| :--- | :--- | ---: |
| Feb | 8,761, 3,682, 2,779 | **5,074** |
| Mar | 8,221, 3,184, 3,916 | **5,107** |
| Apr | 5,733, 4,147 | **4,940** |
| **Total 90-day buffer** | | **15,121** |

### Step 3 — The Gap: How Much to Print

```
Total Needed  =  9-Month Demand  +  90-Day Buffer
Print Order   =  Total Needed  −  (Current Stock + Supplier Stock)
```

**Example — Kids Journal:**

| | Units |
| :--- | ---: |
| 9-Month Demand | 74,427 |
| 90-Day Buffer | 15,121 |
| **Total Needed** | **89,548** |
| Current Stock + Supplier | 75,813 |
| **Gap → Decision** | **ORDER 13,735 units** |

### Step 4 — Regional Routing Rules

Having enough stock globally isn't enough — it has to be positioned where sales happen.

| Channel | Source | Rule |
| :--- | :--- | :--- |
| Amazon US FBA | HBG → FBA, then SLI → FBA | Pull from hubs; print fills remaining gap |
| Amazon CA FBA | CA Hub → CA FBA | Pull from CA hub; print fills remaining gap |
| AU (Journals) | UK → AU | UK→AU transfer permitted for journals |
| AU (Cards) | China printer → AU direct | UK→AU blocked for cards; must print new |
| EU | UK surplus → EU | Topped up from UK only if surplus exists |

---

## Section 2: Demand Breakdown by SKU

For every SKU: the month-by-month comparison of 2024 vs 2025 actual sales, which year's number was used in the forecast, and the buffer calculation. This is the full math behind every number in this plan.

### Kids Journal `EIDJ4100`

**Monthly Demand Forecast (Global — all warehouses combined)**

| Month | 2024 Actual | 2025 Actual | Max Used | Running Total |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 6,607 | 3,091 | **6,607** ← 2024 peak | 6,607 |
| Jun | 4,297 | 3,247 | **4,297** ← 2024 peak | 10,904 |
| Jul | 4,161 | 2,584 | **4,161** ← 2024 peak | 15,065 |
| Aug | 3,897 | 1,501 | **3,897** ← 2024 peak | 18,962 |
| Sep | 3,988 | 1,789 | **3,988** ← 2024 peak | 22,950 |
| Oct | 3,247 | 2,770 | **3,247** ← 2024 peak | 26,197 |
| Nov | 8,953 | 17,726 | **17,726** ← 2025 peak | 43,923 |
| Dec | 19,957 | 20,248 | **20,248** ← 2025 peak | 64,171 |
| Jan 2027 | 10,256 | 4,233 | **10,256** ← 2024 peak | 74,427 |
| **9-Month Total** | | | | **74,427** |

**90-Day Safety Buffer (Feb – Apr historical average)**

| Month | 2024 | 2025 | Average Used |
| :--- | ---: | ---: | ---: |
| Feb | 8,761 | 3,682 | **5,074** |
| Mar | 8,221 | 3,184 | **5,107** |
| Apr | 5,733 | 4,147 | **4,940** |
| **Total Buffer** | | | **15,121** |

**Stock Check:** 74,427 demand + 15,121 buffer = **89,548 needed** vs **75,813 available** → 🖨️ **PRINT 13,735 UNITS** — supply falls short by 13,735

---

### Teen Journal `EIDJ2100`

**Monthly Demand Forecast (Global — all warehouses combined)**

| Month | 2024 Actual | 2025 Actual | Max Used | Running Total |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 4,405 | 3,289 | **4,405** ← 2024 peak | 4,405 |
| Jun | 2,871 | 4,591 | **4,591** ← 2025 peak | 8,996 |
| Jul | 2,683 | 3,629 | **3,629** ← 2025 peak | 12,625 |
| Aug | 2,613 | 2,390 | **2,613** ← 2024 peak | 15,238 |
| Sep | 2,977 | 2,177 | **2,977** ← 2024 peak | 18,215 |
| Oct | 2,210 | 1,832 | **2,210** ← 2024 peak | 20,425 |
| Nov | 6,608 | 7,079 | **7,079** ← 2025 peak | 27,504 |
| Dec | 14,818 | 7,914 | **14,818** ← 2024 peak | 42,322 |
| Jan 2027 | 5,538 | 5,167 | **5,538** ← 2024 peak | 47,860 |
| **9-Month Total** | | | | **47,860** |

**90-Day Safety Buffer (Feb – Apr historical average)**

| Month | 2024 | 2025 | Average Used |
| :--- | ---: | ---: | ---: |
| Feb | 5,340 | 5,232 | **4,396** |
| Mar | 4,029 | 3,920 | **3,756** |
| Apr | 2,609 | 2,559 | **2,584** |
| **Total Buffer** | | | **10,737** |

**Stock Check:** 47,860 demand + 10,737 buffer = **58,597 needed** vs **84,718 available** → ✅ **No print needed** — surplus of -26,121 units

---

### Sharing Joy Conversation Cards `EIDC2000`

**Monthly Demand Forecast (Global — all warehouses combined)**

| Month | 2024 Actual | 2025 Actual | Max Used | Running Total |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | — | 3,196 | **3,196** ← 2025 peak | 3,196 |
| Jun | — | 3,042 | **3,042** ← 2025 peak | 6,238 |
| Jul | — | 2,720 | **2,720** ← 2025 peak | 8,958 |
| Aug | — | 1,938 | **1,938** ← 2025 peak | 10,896 |
| Sep | 2,503 | 1,509 | **2,503** ← 2024 peak | 13,399 |
| Oct | 2,350 | 2,668 | **2,668** ← 2025 peak | 16,067 |
| Nov | 4,363 | 9,134 | **9,134** ← 2025 peak | 25,201 |
| Dec | 10,462 | 11,695 | **11,695** ← 2025 peak | 36,896 |
| Jan 2027 | — | 10,908 | **10,908** ← 2025 peak | 47,804 |
| **9-Month Total** | | | | **47,804** |

**90-Day Safety Buffer (Feb – Apr historical average)**

| Month | 2024 | 2025 | Average Used |
| :--- | ---: | ---: | ---: |
| Feb | — | 2,937 | **2,326** |
| Mar | — | 3,975 | **2,758** |
| Apr | — | 5,351 | **5,351** |
| **Total Buffer** | | | **10,435** |

**Stock Check:** 47,804 demand + 10,435 buffer = **58,239 needed** vs **59,022 available** → ✅ **No print needed** — surplus of -782 units

---

### Daily Journal (Teal) `EIDJ5100`

**Monthly Demand Forecast (Global — all warehouses combined)**

| Month | 2024 Actual | 2025 Actual | Max Used | Running Total |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 3,567 | 1,806 | **3,567** ← 2024 peak | 3,567 |
| Jun | 2,655 | 1,323 | **2,655** ← 2024 peak | 6,222 |
| Jul | 4,263 | 1,174 | **4,263** ← 2024 peak | 10,485 |
| Aug | 4,704 | 906 | **4,704** ← 2024 peak | 15,189 |
| Sep | 4,556 | 993 | **4,556** ← 2024 peak | 19,745 |
| Oct | 3,542 | 1,404 | **3,542** ← 2024 peak | 23,287 |
| Nov | 6,698 | 3,774 | **6,698** ← 2024 peak | 29,985 |
| Dec | 11,179 | 5,495 | **11,179** ← 2024 peak | 41,164 |
| Jan 2027 | 3,580 | 4,193 | **4,193** ← 2025 peak | 45,357 |
| **9-Month Total** | | | | **45,357** |

**90-Day Safety Buffer (Feb – Apr historical average)**

| Month | 2024 | 2025 | Average Used |
| :--- | ---: | ---: | ---: |
| Feb | 2,930 | 3,656 | **2,740** |
| Mar | 2,820 | 2,865 | **2,612** |
| Apr | 4,962 | 1,783 | **3,372** |
| **Total Buffer** | | | **8,725** |

**Stock Check:** 45,357 demand + 8,725 buffer = **54,082 needed** vs **61,237 available** → ✅ **No print needed** — surplus of -7,154 units

---

### Daily Journal (Green) `EIDJ5200`

**Monthly Demand Forecast (Global — all warehouses combined)**

| Month | 2024 Actual | 2025 Actual | Max Used | Running Total |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 2,352 | 839 | **2,352** ← 2024 peak | 2,352 |
| Jun | 1,466 | 772 | **1,466** ← 2024 peak | 3,818 |
| Jul | 1,754 | 657 | **1,754** ← 2024 peak | 5,572 |
| Aug | 1,693 | 449 | **1,693** ← 2024 peak | 7,265 |
| Sep | 1,446 | 485 | **1,446** ← 2024 peak | 8,711 |
| Oct | 1,496 | 504 | **1,496** ← 2024 peak | 10,207 |
| Nov | 3,020 | 2,443 | **3,020** ← 2024 peak | 13,227 |
| Dec | 4,700 | 2,800 | **4,700** ← 2024 peak | 17,927 |
| Jan 2027 | 1,322 | 1,987 | **1,987** ← 2025 peak | 19,914 |
| **9-Month Total** | | | | **19,914** |

**90-Day Safety Buffer (Feb – Apr historical average)**

| Month | 2024 | 2025 | Average Used |
| :--- | ---: | ---: | ---: |
| Feb | 942 | 1,657 | **1,088** |
| Mar | 487 | 1,487 | **1,009** |
| Apr | 3,948 | 975 | **2,461** |
| **Total Buffer** | | | **4,559** |

**Stock Check:** 19,914 demand + 4,559 buffer = **24,473 needed** vs **62,275 available** → ✅ **No print needed** — surplus of -37,801 units

---

### Adult Journal `EIDJ5000`

**Monthly Demand Forecast (Global — all warehouses combined)**

| Month | 2024 Actual | 2025 Actual | Max Used | Running Total |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | 1,949 | 537 | **1,949** ← 2024 peak | 1,949 |
| Jun | 1,622 | 627 | **1,622** ← 2024 peak | 3,571 |
| Jul | 1,365 | 688 | **1,365** ← 2024 peak | 4,936 |
| Aug | 1,016 | 496 | **1,016** ← 2024 peak | 5,952 |
| Sep | 864 | 312 | **864** ← 2024 peak | 6,816 |
| Oct | 806 | 670 | **806** ← 2024 peak | 7,622 |
| Nov | 3,545 | 1,718 | **3,545** ← 2024 peak | 11,167 |
| Dec | 9,070 | 1,975 | **9,070** ← 2024 peak | 20,237 |
| Jan 2027 | 3,663 | 2,418 | **3,663** ← 2024 peak | 23,900 |
| **9-Month Total** | | | | **23,900** |

**90-Day Safety Buffer (Feb – Apr historical average)**

| Month | 2024 | 2025 | Average Used |
| :--- | ---: | ---: | ---: |
| Feb | 1,256 | 1,051 | **985** |
| Mar | 1,081 | 695 | **846** |
| Apr | 1,357 | 421 | **889** |
| **Total Buffer** | | | **2,720** |

**Stock Check:** 23,900 demand + 2,720 buffer = **26,620 needed** vs **63,514 available** → ✅ **No print needed** — surplus of -36,893 units

---

### Dream Affirmation Cards `EIDC2101`

**Monthly Demand Forecast (Global — all warehouses combined)**

| Month | 2024 Actual | 2025 Actual | Max Used | Running Total |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | — | 1,079 | **1,079** ← 2025 peak | 1,079 |
| Jun | — | 532 | **532** ← 2025 peak | 1,611 |
| Jul | — | 614 | **614** ← 2025 peak | 2,225 |
| Aug | — | 463 | **463** ← 2025 peak | 2,688 |
| Sep | 3,761 | 326 | **3,761** ← 2024 peak | 6,449 |
| Oct | 3,943 | 584 | **3,943** ← 2024 peak | 10,392 |
| Nov | 3,884 | 7,489 | **7,489** ← 2025 peak | 17,881 |
| Dec | 6,648 | 5,140 | **6,648** ← 2024 peak | 24,529 |
| Jan 2027 | — | 2,056 | **2,056** ← 2025 peak | 26,585 |
| **9-Month Total** | | | | **26,585** |

**90-Day Safety Buffer (Feb – Apr historical average)**

| Month | 2024 | 2025 | Average Used |
| :--- | ---: | ---: | ---: |
| Feb | — | 1,159 | **975** |
| Mar | — | 958 | **864** |
| Apr | — | 2,459 | **2,459** |
| **Total Buffer** | | | **4,298** |

**Stock Check:** 26,585 demand + 4,298 buffer = **30,883 needed** vs **43,091 available** → ✅ **No print needed** — surplus of -12,207 units

---

### Know Me If You Can Cards `EIDJB5002`

**Monthly Demand Forecast (Global — all warehouses combined)**

| Month | 2024 Actual | 2025 Actual | Max Used | Running Total |
| :--- | ---: | ---: | ---: | ---: |
| May 2026 | — | — | — | 0 |
| Jun | — | 1,926 | **1,926** ← 2025 peak | 1,926 |
| Jul | — | 431 | **431** ← 2025 peak | 2,357 |
| Aug | — | 1,234 | **1,234** ← 2025 peak | 3,591 |
| Sep | — | 1,425 | **1,425** ← 2025 peak | 5,016 |
| Oct | — | 1,574 | **1,574** ← 2025 peak | 6,590 |
| Nov | — | 14,995 | **14,995** ← 2025 peak | 21,585 |
| Dec | — | 12,518 | **12,518** ← 2025 peak | 34,103 |
| Jan 2027 | — | — | — | 34,103 |
| **9-Month Total** | | | | **34,103** |

**90-Day Safety Buffer (Feb – Apr historical average)**

| Month | 2024 | 2025 | Average Used |
| :--- | ---: | ---: | ---: |
| Feb | — | — | **981** |
| Mar | — | — | **844** |
| Apr | — | — | **0** |
| **Total Buffer** | | | **1,825** |

**Stock Check:** 34,103 demand + 1,825 buffer = **35,928 needed** vs **34,177 available** → 🖨️ **PRINT 1,751 UNITS** — supply falls short by 1,751

---

## Section 3: New Print Orders

The following SKUs have a global supply shortfall. Print runs should be placed immediately.

### 🖨️ Kids Journal — Print 13,735 Units

**Why this is needed:**

| | Units |
| :--- | ---: |
| Total requirement (demand + buffer) | 89,548 |
| Available supply (stock + supplier) | 75,813 |
| **Shortfall → Print order** | **13,735** |

**Where to ship (direct from printer — do not route through hubs):**

| Destination | Units | How we got this number |
| :--- | ---: | :--- |
| Amazon US FBA | **7,758** | Region demand: 20,844 · stock after transfers: 13,086 · deficit: 7,758 |
| Amazon CA FBA | **1,683** | Region demand: 4,867 · stock after transfers: 3,184 · deficit: 1,683 |
| Supplier reserve | **4,294** | Hold at supplier pending final regional allocation |

### 🖨️ Know Me If You Can Cards — Print 1,751 Units

**Why this is needed:**

| | Units |
| :--- | ---: |
| Total requirement (demand + buffer) | 35,928 |
| Available supply (stock + supplier) | 34,177 |
| **Shortfall → Print order** | **1,751** |

**Where to ship (direct from printer — do not route through hubs):**

| Destination | Units | How we got this number |
| :--- | ---: | :--- |
| Amazon CA FBA | **1,044** | Region demand: 2,591 · stock after transfers: 1,547 · deficit: 1,044 |
| AU | **707** | Region demand: 6,267 · stock after transfers: 3,128 · deficit: 3,139 — UK→AU blocked for cards; must print direct to AU |

---

## Section 4: Warehouse Transfer Plan

These transfers move existing inventory from holding warehouses into active selling channels. **Execute all transfers before September 1st** — FBA inbound processing takes 2–4 weeks, and November is when velocity spikes.

> **Routing rule reminder:** UK → AU is permitted for Journals only. Cards cannot transfer UK → AU and must receive new print stock direct from supplier.

| SKU | From → To | Units to Move | Stock at Source | Demand at Dest | Why |
| :--- | :--- | ---: | ---: | ---: | :--- |
| Kids Journal | HBG → Amazon US FBA | **6,607** | 6,607 | 20,844 | US FBA needs 20,844; has 1,935; HBG has 6,607 available |
| Kids Journal | SLI → Amazon US FBA | **4,544** | 4,544 | 20,844 | After HBG still short 12,302; SLI has 4,544 available |
| Kids Journal | CA Hub → Amazon CA FBA | **3,184** | 3,184 | 4,867 | CA FBA needs 4,867; has 0; CA Hub has 3,184 available |
| Kids Journal | UK → AU | **4,303** | 33,137 | 13,282 | AU needs 13,282; has 8,979; UK→AU permitted for journals; UK has 33,137 |
| Teen Journal | HBG → Amazon US FBA | **3,537** | 3,537 | 17,044 | US FBA needs 17,044; has 10,284; HBG has 3,537 available |
| Teen Journal | SLI → Amazon US FBA | **2,251** | 2,251 | 17,044 | After HBG still short 3,223; SLI has 2,251 available |
| Teen Journal | CA Hub → Amazon CA FBA | **1,723** | 1,723 | 3,837 | CA FBA needs 3,837; has 0; CA Hub has 1,723 available |
| Sharing Joy Conversation Cards | HBG → Amazon US FBA | **5,651** | 6,810 | 15,313 | US FBA needs 15,313; has 9,662; HBG has 6,810 available |
| Sharing Joy Conversation Cards | CA Hub → Amazon CA FBA | **2,698** | 4,825 | 2,698 | CA FBA needs 2,698; has 0; CA Hub has 4,825 available |
| Daily Journal (Teal) | HBG → Amazon US FBA | **9,346** | 9,737 | 10,396 | US FBA needs 10,396; has 1,050; HBG has 9,737 available |
| Daily Journal (Teal) | CA Hub → Amazon CA FBA | **2,722** | 4,526 | 2,722 | CA FBA needs 2,722; has 0; CA Hub has 4,526 available |
| Daily Journal (Teal) | UK → AU | **2,568** | 12,161 | 8,809 | AU needs 8,809; has 6,241; UK→AU permitted for journals; UK has 12,161 |
| Daily Journal (Green) | HBG → Amazon US FBA | **5,640** | 6,138 | 6,758 | US FBA needs 6,758; has 1,118; HBG has 6,138 available |
| Daily Journal (Green) | CA Hub → Amazon CA FBA | **881** | 4,274 | 881 | CA FBA needs 881; has 0; CA Hub has 4,274 available |
| Adult Journal | HBG → Amazon US FBA | **5,013** | 14,159 | 5,428 | US FBA needs 5,428; has 415; HBG has 14,159 available |
| Adult Journal | CA Hub → Amazon CA FBA | **1,589** | 4,929 | 1,589 | CA FBA needs 1,589; has 0; CA Hub has 4,929 available |
| Dream Affirmation Cards | HBG → Amazon US FBA | **3,163** | 13,138 | 3,957 | US FBA needs 3,957; has 794; HBG has 13,138 available |
| Dream Affirmation Cards | CA Hub → Amazon CA FBA | **1,896** | 2,474 | 1,896 | CA FBA needs 1,896; has 0; CA Hub has 2,474 available |
| Dream Affirmation Cards | UK → EU | **465** | 9,234 | 0 | EU needs 1,408; UK has 9,234 available |
| Know Me If You Can Cards | HBG → Amazon US FBA | **1,861** | 2,603 | 9,287 | US FBA needs 9,287; has 7,426; HBG has 2,603 available |
| Know Me If You Can Cards | CA Hub → Amazon CA FBA | **1,547** | 1,547 | 2,591 | CA FBA needs 2,591; has 0; CA Hub has 1,547 available |

---

## Section 5: Rolling Depletion Forecast by Region

Month-by-month stock burn for each key selling region, assuming all transfers and print runs above are executed. Every region should end January 2027 with a positive buffer balance — that carry-over stock is what keeps us live through April 2027 while the next order cycle completes.

> **How to read this:** Starting stock = demand + buffer (what the region needs to have after all transfers land). Each month we subtract max projected sales. January ending balance = the 90-day buffer. It should never be zero.

### Kids Journal

#### Amazon US FBA

*Required starting stock: **26,646 units** (20,844 demand + 5,802 buffer — Feb avg 1,747 + Mar avg 1,897 + Apr avg 2,158 = **5,802 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 1,832 | **24,814** | 81.8w |
| Jun | 1,344 | **23,470** | 63.6w |
| Jul | 1,582 | **21,888** | 66.6w |
| Aug | 1,456 | **20,432** | 59.5w |
| Sep | 1,520 | **18,912** | 60.3w |
| Oct | 1,345 | **17,567** | 35.8w |
| Nov | 2,176 | **15,391** | 9.6w |
| Dec | 6,862 | **8,529** | 13.9w |
| Jan 2027 | 2,727 | **5,802** | 13.3w |

> **Jan 2027 buffer: 5,802 units** — carry-over stock covering Feb–Apr 2027

#### Amazon CA FBA

*Required starting stock: **5,678 units** (4,867 demand + 811 buffer — Feb avg 292 + Mar avg 300 + Apr avg 218 = **811 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 666 | **5,012** | 53.4w |
| Jun | 416 | **4,596** | 87.9w |
| Jul | 224 | **4,372** | 57.1w |
| Aug | 339 | **4,033** | 75.4w |
| Sep | 237 | **3,796** | 91.9w |
| Oct | 177 | **3,619** | 14.7w |
| Nov | 1,093 | **2,526** | 8.5w |
| Dec | 1,278 | **1,248** | 12.6w |
| Jan 2027 | 437 | **811** | 13.3w |

> **Jan 2027 buffer: 811 units** — carry-over stock covering Feb–Apr 2027

#### UK

*Required starting stock: **15,050 units** (12,661 demand + 2,389 buffer — Feb avg 1,148 + Mar avg 760 + Apr avg 480 = **2,389 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 846 | **14,204** | 118.5w |
| Jun | 531 | **13,673** | 73.3w |
| Jul | 799 | **12,874** | 148.5w |
| Aug | 384 | **12,490** | 146.3w |
| Sep | 378 | **12,112** | 156.8w |
| Oct | 331 | **11,781** | 16.7w |
| Nov | 3,127 | **8,654** | 18.3w |
| Dec | 2,027 | **6,627** | 6.9w |
| Jan 2027 | 4,238 | **2,389** | 13.3w |

> **Jan 2027 buffer: 2,389 units** — carry-over stock covering Feb–Apr 2027

#### AU

*Required starting stock: **15,571 units** (13,282 demand + 2,289 buffer — Feb avg 651 + Mar avg 841 + Apr avg 796 = **2,289 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 1,089 | **14,482** | 81.0w |
| Jun | 792 | **13,690** | 77.0w |
| Jul | 762 | **12,928** | 86.2w |
| Aug | 664 | **12,264** | 65.4w |
| Sep | 831 | **11,433** | 72.2w |
| Oct | 679 | **10,754** | 11.4w |
| Nov | 4,180 | **6,574** | 7.9w |
| Dec | 3,569 | **3,005** | 18.6w |
| Jan 2027 | 716 | **2,289** | 13.3w |

> **Jan 2027 buffer: 2,289 units** — carry-over stock covering Feb–Apr 2027

### Teen Journal

#### Amazon US FBA

*Required starting stock: **20,974 units** (17,044 demand + 3,930 buffer — Feb avg 1,237 + Mar avg 1,444 + Apr avg 1,249 = **3,930 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 1,880 | **19,094** | 50.6w |
| Jun | 1,671 | **17,423** | 57.4w |
| Jul | 1,302 | **16,121** | 55.3w |
| Aug | 1,291 | **14,830** | 45.0w |
| Sep | 1,459 | **13,371** | 64.5w |
| Oct | 888 | **12,483** | 27.9w |
| Nov | 1,982 | **10,501** | 9.3w |
| Dec | 4,858 | **5,643** | 14.6w |
| Jan 2027 | 1,713 | **3,930** | 13.3w |

> **Jan 2027 buffer: 3,930 units** — carry-over stock covering Feb–Apr 2027

#### Amazon CA FBA

*Required starting stock: **4,362 units** (3,837 demand + 525 buffer — Feb avg 258 + Mar avg 191 + Apr avg 75 = **525 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 221 | **4,141** | 31.9w |
| Jun | 575 | **3,566** | 60.4w |
| Jul | 253 | **3,313** | 81.1w |
| Aug | 181 | **3,132** | 55.5w |
| Sep | 250 | **2,882** | 74.0w |
| Oct | 167 | **2,715** | 16.3w |
| Nov | 737 | **1,978** | 11.3w |
| Dec | 752 | **1,226** | 7.7w |
| Jan 2027 | 701 | **525** | 13.3w |

> **Jan 2027 buffer: 525 units** — carry-over stock covering Feb–Apr 2027

#### UK

*Required starting stock: **10,217 units** (7,625 demand + 2,592 buffer — Feb avg 1,437 + Mar avg 753 + Apr avg 402 = **2,592 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 697 | **9,520** | 80.2w |
| Jun | 526 | **8,994** | 104.7w |
| Jul | 368 | **8,626** | 168.3w |
| Aug | 227 | **8,399** | 132.4w |
| Sep | 281 | **8,118** | 100.6w |
| Oct | 346 | **7,772** | 27.3w |
| Nov | 1,260 | **6,512** | 11.7w |
| Dec | 2,381 | **4,131** | 11.9w |
| Jan 2027 | 1,539 | **2,592** | 13.3w |

> **Jan 2027 buffer: 2,592 units** — carry-over stock covering Feb–Apr 2027

#### AU

*Required starting stock: **10,078 units** (8,532 demand + 1,546 buffer — Feb avg 619 + Mar avg 655 + Apr avg 271 = **1,546 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 673 | **9,405** | 47.2w |
| Jun | 882 | **8,523** | 56.7w |
| Jul | 644 | **7,879** | 59.2w |
| Aug | 589 | **7,290** | 56.0w |
| Sep | 576 | **6,714** | 42.1w |
| Oct | 683 | **6,031** | 15.9w |
| Nov | 1,680 | **4,351** | 8.9w |
| Dec | 2,085 | **2,266** | 13.9w |
| Jan 2027 | 720 | **1,546** | 13.3w |

> **Jan 2027 buffer: 1,546 units** — carry-over stock covering Feb–Apr 2027

### Sharing Joy Conversation Cards

#### Amazon US FBA

*Required starting stock: **19,063 units** (15,313 demand + 3,750 buffer — Feb avg 860 + Mar avg 1,155 + Apr avg 1,735 = **3,750 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 1,375 | **17,688** | 68.6w |
| Jun | 1,142 | **16,546** | 66.6w |
| Jul | 1,065 | **15,481** | 80.4w |
| Aug | 853 | **14,628** | 104.7w |
| Sep | 619 | **14,009** | 63.5w |
| Oct | 946 | **13,063** | 28.3w |
| Nov | 2,042 | **11,021** | 12.3w |
| Dec | 3,836 | **7,185** | 9.3w |
| Jan 2027 | 3,435 | **3,750** | 13.3w |

> **Jan 2027 buffer: 3,750 units** — carry-over stock covering Feb–Apr 2027

#### Amazon CA FBA

*Required starting stock: **3,193 units** (2,698 demand + 495 buffer — Feb avg 127 + Mar avg 92 + Apr avg 276 = **495 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 222 | **2,971** | 61.5w |
| Jun | 214 | **2,757** | 58.8w |
| Jul | 201 | **2,556** | 151.0w |
| Aug | 75 | **2,481** | 39.1w |
| Sep | 281 | **2,200** | 46.0w |
| Oct | 205 | **1,995** | 17.6w |
| Nov | 503 | **1,492** | 11.2w |
| Dec | 570 | **922** | 9.6w |
| Jan 2027 | 427 | **495** | 13.3w |

> **Jan 2027 buffer: 495 units** — carry-over stock covering Feb–Apr 2027

#### UK

*Required starting stock: **5,968 units** (5,357 demand + 611 buffer — Feb avg 226 + Mar avg 171 + Apr avg 214 = **611 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 8 | **5,960** | 1389.3w |
| Jun | 19 | **5,941** | 1958.7w |
| Jul | 13 | **5,928** | 3281.8w |
| Aug | 8 | **5,920** | 95.0w |
| Sep | 276 | **5,644** | 118.6w |
| Oct | 204 | **5,440** | 10.3w |
| Nov | 2,346 | **3,094** | 7.5w |
| Dec | 1,757 | **1,337** | 8.2w |
| Jan 2027 | 726 | **611** | 13.3w |

> **Jan 2027 buffer: 611 units** — carry-over stock covering Feb–Apr 2027

#### AU

*Required starting stock: **7,602 units** (6,410 demand + 1,192 buffer — Feb avg 337 + Mar avg 369 + Apr avg 486 = **1,192 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 441 | **7,161** | 63.9w |
| Jun | 496 | **6,665** | 59.6w |
| Jul | 479 | **6,186** | 79.9w |
| Aug | 343 | **5,843** | 53.8w |
| Sep | 481 | **5,362** | 33.6w |
| Oct | 683 | **4,679** | 15.0w |
| Nov | 1,381 | **3,298** | 11.8w |
| Dec | 1,194 | **2,104** | 10.2w |
| Jan 2027 | 912 | **1,192** | 13.3w |

> **Jan 2027 buffer: 1,192 units** — carry-over stock covering Feb–Apr 2027

### Daily Journal (Teal)

#### Amazon US FBA

*Required starting stock: **12,915 units** (10,396 demand + 2,519 buffer — Feb avg 748 + Mar avg 905 + Apr avg 865 = **2,519 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 736 | **12,179** | 73.3w |
| Jun | 736 | **11,443** | 46.8w |
| Jul | 1,047 | **10,396** | 50.8w |
| Aug | 907 | **9,489** | 48.4w |
| Sep | 869 | **8,620** | 46.4w |
| Oct | 796 | **7,824** | 24.7w |
| Nov | 1,403 | **6,421** | 9.8w |
| Dec | 2,820 | **3,601** | 14.7w |
| Jan 2027 | 1,082 | **2,519** | 13.3w |

> **Jan 2027 buffer: 2,519 units** — carry-over stock covering Feb–Apr 2027

#### Amazon CA FBA

*Required starting stock: **3,345 units** (2,722 demand + 623 buffer — Feb avg 186 + Mar avg 148 + Apr avg 289 = **623 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 473 | **2,872** | 54.4w |
| Jun | 234 | **2,638** | 47.9w |
| Jul | 236 | **2,402** | 52.1w |
| Aug | 204 | **2,198** | 29.8w |
| Sep | 327 | **1,871** | 43.6w |
| Oct | 184 | **1,687** | 20.1w |
| Nov | 372 | **1,315** | 12.9w |
| Dec | 436 | **879** | 15.2w |
| Jan 2027 | 256 | **623** | 13.3w |

> **Jan 2027 buffer: 623 units** — carry-over stock covering Feb–Apr 2027

#### UK

*Required starting stock: **12,303 units** (10,257 demand + 2,046 buffer — Feb avg 606 + Mar avg 554 + Apr avg 885 = **2,046 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 278 | **12,025** | 224.7w |
| Jun | 237 | **11,788** | 88.3w |
| Jul | 572 | **11,216** | 34.7w |
| Aug | 1,433 | **9,783** | 30.6w |
| Sep | 1,414 | **8,369** | 33.1w |
| Oct | 1,082 | **7,287** | 20.9w |
| Nov | 1,543 | **5,744** | 10.4w |
| Dec | 2,373 | **3,371** | 11.3w |
| Jan 2027 | 1,325 | **2,046** | 13.3w |

> **Jan 2027 buffer: 2,046 units** — carry-over stock covering Feb–Apr 2027

#### AU

*Required starting stock: **10,162 units** (8,809 demand + 1,353 buffer — Feb avg 425 + Mar avg 396 + Apr avg 531 = **1,353 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 832 | **9,330** | 49.8w |
| Jun | 829 | **8,501** | 34.0w |
| Jul | 1,072 | **7,429** | 42.5w |
| Aug | 775 | **6,654** | 38.9w |
| Sep | 757 | **5,897** | 39.4w |
| Oct | 642 | **5,255** | 13.1w |
| Nov | 1,778 | **3,477** | 9.0w |
| Dec | 1,657 | **1,820** | 17.3w |
| Jan 2027 | 467 | **1,353** | 13.3w |

> **Jan 2027 buffer: 1,353 units** — carry-over stock covering Feb–Apr 2027

### Daily Journal (Green)

#### Amazon US FBA

*Required starting stock: **8,072 units** (6,758 demand + 1,314 buffer — Feb avg 378 + Mar avg 470 + Apr avg 465 = **1,314 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 486 | **7,586** | 49.8w |
| Jun | 674 | **6,912** | 47.2w |
| Jul | 628 | **6,284** | 44.2w |
| Aug | 630 | **5,654** | 55.5w |
| Sep | 451 | **5,203** | 41.8w |
| Oct | 533 | **4,670** | 21.7w |
| Nov | 952 | **3,718** | 8.4w |
| Dec | 1,899 | **1,819** | 16.0w |
| Jan 2027 | 505 | **1,314** | 13.3w |

> **Jan 2027 buffer: 1,314 units** — carry-over stock covering Feb–Apr 2027

#### Amazon CA FBA

*Required starting stock: **1,100 units** (881 demand + 219 buffer — Feb avg 58 + Mar avg 43 + Apr avg 117 = **219 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 133 | **967** | 59.5w |
| Jun | 72 | **895** | 51.1w |
| Jul | 75 | **820** | 55.0w |
| Aug | 66 | **754** | 44.5w |
| Sep | 75 | **679** | 49.3w |
| Oct | 59 | **620** | 18.1w |
| Nov | 152 | **468** | 13.4w |
| Dec | 150 | **318** | 14.2w |
| Jan 2027 | 99 | **219** | 13.3w |

> **Jan 2027 buffer: 219 units** — carry-over stock covering Feb–Apr 2027

#### UK

*Required starting stock: **5,959 units** (4,518 demand + 1,441 buffer — Feb avg 225 + Mar avg 153 + Apr avg 1,063 = **1,441 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 763 | **5,196** | 118.0w |
| Jun | 195 | **5,001** | 84.4w |
| Jul | 254 | **4,747** | 65.7w |
| Aug | 320 | **4,427** | 56.3w |
| Sep | 348 | **4,079** | 50.0w |
| Oct | 350 | **3,729** | 27.0w |
| Nov | 611 | **3,118** | 13.4w |
| Dec | 994 | **2,124** | 13.8w |
| Jan 2027 | 683 | **1,441** | 13.3w |

> **Jan 2027 buffer: 1,441 units** — carry-over stock covering Feb–Apr 2027

#### AU

*Required starting stock: **3,206 units** (2,741 demand + 465 buffer — Feb avg 126 + Mar avg 128 + Apr avg 210 = **465 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 288 | **2,918** | 52.7w |
| Jun | 245 | **2,673** | 32.5w |
| Jul | 352 | **2,321** | 44.5w |
| Aug | 231 | **2,090** | 41.7w |
| Sep | 222 | **1,868** | 42.4w |
| Oct | 189 | **1,679** | 12.2w |
| Nov | 611 | **1,068** | 11.1w |
| Dec | 412 | **656** | 15.2w |
| Jan 2027 | 191 | **465** | 13.3w |

> **Jan 2027 buffer: 465 units** — carry-over stock covering Feb–Apr 2027

### Adult Journal

#### Amazon US FBA

*Required starting stock: **6,297 units** (5,428 demand + 869 buffer — Feb avg 277 + Mar avg 257 + Apr avg 334 = **869 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 589 | **5,708** | 60.2w |
| Jun | 420 | **5,288** | 52.8w |
| Jul | 429 | **4,859** | 55.6w |
| Aug | 387 | **4,472** | 63.3w |
| Sep | 313 | **4,159** | 65.3w |
| Oct | 273 | **3,886** | 34.1w |
| Nov | 505 | **3,381** | 9.0w |
| Dec | 1,607 | **1,774** | 8.7w |
| Jan 2027 | 905 | **869** | 13.3w |

> **Jan 2027 buffer: 869 units** — carry-over stock covering Feb–Apr 2027

#### Amazon CA FBA

*Required starting stock: **1,810 units** (1,589 demand + 221 buffer — Feb avg 103 + Mar avg 80 + Apr avg 38 = **221 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 89 | **1,721** | 91.9w |
| Jun | 83 | **1,638** | 96.2w |
| Jul | 73 | **1,565** | 216.7w |
| Aug | 32 | **1,533** | 119.2w |
| Sep | 57 | **1,476** | 162.3w |
| Oct | 39 | **1,437** | 18.2w |
| Nov | 350 | **1,087** | 12.7w |
| Dec | 366 | **721** | 6.4w |
| Jan 2027 | 500 | **221** | 13.3w |

> **Jan 2027 buffer: 221 units** — carry-over stock covering Feb–Apr 2027

#### UK

*Required starting stock: **7,566 units** (6,892 demand + 674 buffer — Feb avg 217 + Mar avg 204 + Apr avg 252 = **674 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 547 | **7,019** | 59.3w |
| Jun | 524 | **6,495** | 86.2w |
| Jul | 323 | **6,172** | 105.5w |
| Aug | 259 | **5,913** | 140.8w |
| Sep | 186 | **5,727** | 77.9w |
| Oct | 315 | **5,412** | 21.1w |
| Nov | 1,135 | **4,277** | 6.5w |
| Dec | 2,842 | **1,435** | 8.4w |
| Jan 2027 | 761 | **674** | 13.3w |

> **Jan 2027 buffer: 674 units** — carry-over stock covering Feb–Apr 2027

#### AU

*Required starting stock: **4,242 units** (3,815 demand + 427 buffer — Feb avg 157 + Mar avg 144 + Apr avg 125 = **427 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 259 | **3,983** | 78.0w |
| Jun | 226 | **3,757** | 77.0w |
| Jul | 209 | **3,548** | 106.2w |
| Aug | 148 | **3,400** | 103.8w |
| Sep | 145 | **3,255** | 120.3w |
| Oct | 116 | **3,139** | 21.3w |
| Nov | 654 | **2,485** | 7.6w |
| Dec | 1,401 | **1,084** | 7.3w |
| Jan 2027 | 657 | **427** | 13.3w |

> **Jan 2027 buffer: 427 units** — carry-over stock covering Feb–Apr 2027

### Dream Affirmation Cards

#### Amazon US FBA

*Required starting stock: **5,011 units** (3,957 demand + 1,054 buffer — Feb avg 263 + Mar avg 306 + Apr avg 485 = **1,054 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 296 | **4,715** | 128.9w |
| Jun | 162 | **4,553** | 129.2w |
| Jul | 151 | **4,402** | 106.5w |
| Aug | 183 | **4,219** | 106.2w |
| Sep | 176 | **4,043** | 70.4w |
| Oct | 246 | **3,797** | 15.4w |
| Nov | 1,091 | **2,706** | 9.6w |
| Dec | 1,206 | **1,500** | 14.9w |
| Jan 2027 | 446 | **1,054** | 13.3w |

> **Jan 2027 buffer: 1,054 units** — carry-over stock covering Feb–Apr 2027

#### Amazon CA FBA

*Required starting stock: **2,308 units** (1,896 demand + 412 buffer — Feb avg 83 + Mar avg 59 + Apr avg 270 = **412 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 119 | **2,189** | 346.3w |
| Jun | 28 | **2,161** | 402.8w |
| Jul | 23 | **2,138** | 287.0w |
| Aug | 33 | **2,105** | 24.8w |
| Sep | 376 | **1,729** | 21.4w |
| Oct | 346 | **1,383** | 12.2w |
| Nov | 503 | **880** | 11.1w |
| Dec | 341 | **539** | 18.8w |
| Jan 2027 | 127 | **412** | 13.3w |

> **Jan 2027 buffer: 412 units** — carry-over stock covering Feb–Apr 2027

#### UK

*Required starting stock: **6,440 units** (6,116 demand + 324 buffer — Feb avg 114 + Mar avg 70 + Apr avg 140 = **324 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 117 | **6,323** | 217.1w |
| Jun | 129 | **6,194** | 632.1w |
| Jul | 42 | **6,152** | 1946.2w |
| Aug | 14 | **6,138** | 40.6w |
| Sep | 669 | **5,469** | 41.6w |
| Oct | 563 | **4,906** | 9.3w |
| Nov | 2,346 | **2,560** | 6.1w |
| Dec | 1,794 | **766** | 7.7w |
| Jan 2027 | 442 | **324** | 13.3w |

> **Jan 2027 buffer: 324 units** — carry-over stock covering Feb–Apr 2027

#### AU

*Required starting stock: **4,716 units** (4,132 demand + 584 buffer — Feb avg 169 + Mar avg 140 + Apr avg 275 = **584 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 185 | **4,531** | 250.9w |
| Jun | 80 | **4,451** | 200.8w |
| Jul | 95 | **4,356** | 292.3w |
| Aug | 66 | **4,290** | 31.0w |
| Sep | 613 | **3,677** | 22.0w |
| Oct | 716 | **2,961** | 9.5w |
| Nov | 1,381 | **1,580** | 9.1w |
| Dec | 746 | **834** | 14.8w |
| Jan 2027 | 250 | **584** | 13.3w |

> **Jan 2027 buffer: 584 units** — carry-over stock covering Feb–Apr 2027

### Know Me If You Can Cards

#### Amazon US FBA

*Required starting stock: **9,937 units** (9,287 demand + 650 buffer — Feb avg 333 + Mar avg 317 = **650 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 0 | **9,937** | — |
| Jun | 0 | **9,937** | — |
| Jul | 0 | **9,937** | — |
| Aug | 0 | **9,937** | 916.8w |
| Sep | 48 | **9,889** | 243.6w |
| Oct | 174 | **9,715** | 12.0w |
| Nov | 3,594 | **6,121** | 5.7w |
| Dec | 4,598 | **1,523** | 7.7w |
| Jan 2027 | 873 | **650** | 13.3w |

> **Jan 2027 buffer: 650 units** — carry-over stock covering Feb–Apr 2027

#### Amazon CA FBA

*Required starting stock: **2,745 units** (2,591 demand + 154 buffer — Feb avg 97 + Mar avg 57 = **154 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 0 | **2,745** | 65.0w |
| Jun | 187 | **2,558** | 342.6w |
| Jul | 32 | **2,526** | 96.4w |
| Aug | 116 | **2,410** | 91.2w |
| Sep | 117 | **2,293** | 103.4w |
| Oct | 95 | **2,198** | 8.6w |
| Nov | 1,136 | **1,062** | 6.1w |
| Dec | 747 | **315** | 8.7w |
| Jan 2027 | 161 | **154** | 13.3w |

> **Jan 2027 buffer: 154 units** — carry-over stock covering Feb–Apr 2027

#### UK

*Required starting stock: **4,111 units** (3,908 demand + 203 buffer — Feb avg 98 + Mar avg 105 = **203 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 0 | **4,111** | 101.7w |
| Jun | 179 | **3,932** | — |
| Jul | 0 | **3,932** | 1934.8w |
| Aug | 9 | **3,923** | 8686.6w |
| Sep | 2 | **3,921** | 236.7w |
| Oct | 71 | **3,850** | 7.0w |
| Nov | 2,439 | **1,411** | 6.6w |
| Dec | 917 | **494** | 7.5w |
| Jan 2027 | 291 | **203** | 13.3w |

> **Jan 2027 buffer: 203 units** — carry-over stock covering Feb–Apr 2027

#### AU

*Required starting stock: **6,503 units** (6,267 demand + 236 buffer — Feb avg 115 + Mar avg 121 = **236 units**)*

| Month | Max Projected Sales | Ending Stock | Weeks of Cover |
| :--- | ---: | ---: | ---: |
| May 2026 | 0 | **6,503** | 79.1w |
| Jun | 364 | **6,139** | 167.6w |
| Jul | 157 | **5,982** | 52.0w |
| Aug | 509 | **5,473** | 64.6w |
| Sep | 375 | **5,098** | 51.0w |
| Oct | 428 | **4,670** | 8.3w |
| Nov | 2,490 | **2,180** | 6.2w |
| Dec | 1,505 | **675** | 6.8w |
| Jan 2027 | 439 | **236** | 13.3w |

> **Jan 2027 buffer: 236 units** — carry-over stock covering Feb–Apr 2027

---

## Section 6: Master Action Checklist

Everything that needs to happen, in priority order.

### 🖨️ Print Orders (Place Now)

- [ ] **Kids Journal** — order **13,735 units** from supplier
  - Ship **7,758** direct to **Amazon US FBA**
  - Ship **1,683** direct to **Amazon CA FBA**
  - Hold **4,294** at supplier pending allocation confirmation
- [ ] **Know Me If You Can Cards** — order **1,751 units** from supplier
  - Ship **1,044** direct to **Amazon CA FBA**
  - Ship **707** direct to **AU**

### 📦 Warehouse Transfers (Complete Before September 1st)

**Kids Journal:**
- [ ] HBG → Amazon US FBA: **6,607 units**
- [ ] SLI → Amazon US FBA: **4,544 units**
- [ ] CA Hub → Amazon CA FBA: **3,184 units**
- [ ] UK → AU: **4,303 units**

**Teen Journal:**
- [ ] HBG → Amazon US FBA: **3,537 units**
- [ ] SLI → Amazon US FBA: **2,251 units**
- [ ] CA Hub → Amazon CA FBA: **1,723 units**

**Sharing Joy Conversation Cards:**
- [ ] HBG → Amazon US FBA: **5,651 units**
- [ ] CA Hub → Amazon CA FBA: **2,698 units**

**Daily Journal (Teal):**
- [ ] HBG → Amazon US FBA: **9,346 units**
- [ ] CA Hub → Amazon CA FBA: **2,722 units**
- [ ] UK → AU: **2,568 units**

**Daily Journal (Green):**
- [ ] HBG → Amazon US FBA: **5,640 units**
- [ ] CA Hub → Amazon CA FBA: **881 units**

**Adult Journal:**
- [ ] HBG → Amazon US FBA: **5,013 units**
- [ ] CA Hub → Amazon CA FBA: **1,589 units**

**Dream Affirmation Cards:**
- [ ] HBG → Amazon US FBA: **3,163 units**
- [ ] CA Hub → Amazon CA FBA: **1,896 units**
- [ ] UK → EU: **465 units**

**Know Me If You Can Cards:**
- [ ] HBG → Amazon US FBA: **1,861 units**
- [ ] CA Hub → Amazon CA FBA: **1,547 units**

### 📋 Verification Checkpoints

- [ ] Confirm print order lead times — Kids Journal and Know Me Cards must arrive before September
- [ ] Create FBA inbound shipments in Seller Central and confirm tracking
- [ ] Verify UK → AU journal shipments cleared customs and landed at AU warehouse
- [ ] Re-run this plan in August to catch any demand surprises before Q4 locks in
- [ ] Check this plan again in November — if Dec sales are running above forecast, flag early

---

*Plan generated May 3, 2026. Re-run monthly to stay current. Source: `.tmp/data.json`*
