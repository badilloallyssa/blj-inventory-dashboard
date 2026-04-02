# Demand Planning

## Objective
Generate monthly or quarterly replenishment recommendations for all 8 SKUs across all 10 warehouses. Output lands in Google Sheets: Dashboard (owner summary), Demand_Plan, Replenishment_Routing, Inventory_Health, and Calculation_Log.

---

## Google Setup (One-Time)
Before any tool can run, the Google Service Account must be configured:

1. Go to https://console.cloud.google.com
2. Create or select a project → search "Google Sheets API" → Enable it. Do the same for "Google Drive API".
3. IAM & Admin → Service Accounts → Create Service Account
   - Name: `inventory-planner` (or anything)
   - Role: Editor
4. Click the service account → Keys tab → Add Key → JSON → Download
5. Save the file as `service_account.json` in the project root (`/Users/allyssa/Desktop/Claude/`)
6. Open the JSON file — find `client_email` — copy that email address
7. Open the Google Sheet → Share → paste the service account email → give Editor access
8. Test: `python tools/auth_google.py` — should print "Connected to: [sheet name]"

---

## Inputs Required
- Google Sheet updated with fresh data in these tabs:
  - `Sales_Data` — weekly sales per SKU per warehouse (Date, SKU_ID, SKU_Name, Warehouse, Units_Sold)
  - `Current_Stock` — current on-hand inventory per SKU per warehouse
  - `Supplier_Stock` — stock at China supplier and Canada supplier
  - `PO_Tracker` — active POs and transfers in progress
- If first run: `python tools/setup_sheet.py` to create all tabs

---

## Default: Run Everything (say "run demand plan")

When triggered, run all of the following in order, then show both links:

```bash
python tools/run_demand_plan.py --plan-type monthly
python tools/export_static_dashboard.py
```

After both complete, always output:
- **Google Sheet (Dashboard):** https://docs.google.com/spreadsheets/d/17WfI1Uv8kAf2UIzd6QaOTcb5xQl4s4uryoW2mYFPHZk/edit#gid=0
- **HTML Dashboard:** https://badilloallyssa.github.io/blj-inventory-dashboard/

Then summarize: CRITICAL count, LOW count, OVERSTOCK count.

## Running a Quarterly Plan

```bash
python tools/run_demand_plan.py --plan-type quarterly
python tools/export_static_dashboard.py
```

## Other Options

```bash
# For a specific future month
python tools/run_demand_plan.py --plan-type monthly --plan-month 2025-06

# Reuse cached data (skip re-pulling from sheet)
python tools/run_demand_plan.py --plan-type monthly --skip-pull
```

---

## Pipeline Steps (what happens when you run it)

1. **pull_data.py** — reads Sales_Data, Current_Stock, Supplier_Stock, PO_Tracker, Config, Seasonality_Index from Google Sheet → `.tmp/data.json`
2. **calculate_velocity.py** — computes 30d, 60d, 90d average daily sales per SKU × Warehouse → `.tmp/velocity.json`
3. **calculate_seasonality.py** — derives monthly demand indices from 2-year history → `.tmp/seasonality.json`
4. **demand_plan.py** — core logic: velocity × seasonality → days of stock → units needed → `.tmp/demand_plan.json`
5. **recommend_routing.py** — for each replenishment need, picks best source (transfer vs new PO) → `.tmp/routing.json`
6. **inventory_health.py** — assigns CRITICAL / LOW / OK / OVERSTOCK status per SKU × Warehouse → `.tmp/health.json`
7. **write_plan.py** — writes all outputs back to Google Sheet

---

## The Math (how each number is calculated)

For each SKU × Warehouse:

```
Adjusted Velocity = 90-day velocity (units/day) × Seasonality Factor

Days of Stock = (Current Stock + In Transit) ÷ Adjusted Velocity

Gap = Target Days (90) − Days of Stock
Units Needed = Gap × Adjusted Velocity  (if Gap > 0)

Order Deadline = Today + (Days of Stock − Lead Time)
```

**Seasonality Factor** example:
- Overall average: 100 units/month across all months
- December average: 150 units/month
- December index: 150 / 100 = 1.50 (demand is 50% above average in December)

**Trend Signal:**
- 30d velocity ÷ 90d velocity > 1.2 = ACCELERATING (demand increasing)
- < 0.8 = SLOWING
- Otherwise: STABLE

---

## Status Codes
| Status | Meaning | Action |
|--------|---------|--------|
| CRITICAL | < 30 days of stock | Order immediately |
| LOW | 30–90 days | Plan replenishment now |
| OK | 90–365 days | Monitor |
| OVERSTOCK | > 365 days | Consider sale / transfer |
| NO_DATA | No sales history | Verify manually |

---

## Replenishment Routing Logic

| Destination | Primary | Secondary | Last Resort |
|-------------|---------|-----------|-------------|
| Amazon US FBA | Highest stock US warehouse | China direct to AWD (bulk ≥200 units) | New PO |
| Amazon CA FBA | CA warehouse | China | — |
| UK | EU | AU | China/US transfer (expensive — needs freight forwarder) |
| EU | UK | China | AU |
| AU | UK | China | — |
| US warehouses | China supplier | — | — |
| CA warehouse | US warehouse | Canada supplier | China |

**AWD note:** For Amazon FBA, quantities ≥ 200 units can go China → AWD directly (AWD auto-replenishes FBA). Better for bulk.

**Transfer rule:** A source warehouse is never stripped below a 25% stock buffer (to preserve its own supply).

---

## Edge Cases & Notes
- **Insufficient history:** If a SKU has <30 days of sales data, velocity will be low and unreliable. Check data quality field in Calculation_Log.
- **New SKU:** Add it to Config tab (SKU Master section). It will be included automatically next run.
- **Override seasonality:** Add a manual override in Seasonality_Index tab — the system respects manually set values.
- **Rate limits:** Google Sheets API allows ~300 requests/min. If hitting limits, add `time.sleep(0.2)` between batch writes in write_plan.py.
- **FBA fee differences:** For Amazon US FBA routing, the system picks highest-stock US warehouse. If you know a specific warehouse has lower FBA fees, override the recommendation manually.

---

## Asking Questions
You can ask Claude directly:
- "What's our current inventory state?" → runs inventory_health.py and summarizes
- "What do we need to order this month?" → runs demand_plan pipeline and reports urgent items
- "How did we get to 450 units for Kids Journal at SLI?" → reads Calculation_Log tab and explains
- "Plan for BFCM" → see seasonal_event_planning.md
