# Seasonal Event Planning

## Objective
Plan inventory for high-demand events: BFCM (Black Friday / Cyber Monday), Q4 holiday season, Mother's Day, back-to-school, or any event where demand spikes above the historical seasonality baseline.

---

## Key Events Calendar (typical for journals/cards)
| Event | Month | Expected Pattern |
|-------|-------|-----------------|
| Mother's Day | May | Spike in gifting SKUs |
| Back to School | Aug–Sep | Spike in journal SKUs |
| BFCM | Nov (last week) | Highest sales week of year |
| Holiday / Christmas | Dec | Strong across all SKUs |
| New Year / Resolutions | Jan | Spike in journal SKUs |
| Valentine's Day | Feb | Spike in gifting/cards SKUs |

---

## How the System Already Handles Seasonality
The demand planning engine automatically applies monthly seasonality indices derived from 2 years of history. If November and December historically show 2x average sales, the system will already factor that into the replenishment quantity when running the plan for those months.

To check what the system has learned:
```bash
python tools/calculate_seasonality.py --data .tmp/data.json
```
This prints the full index table. Index > 1.0 = above-average demand that month.

---

## Planning for BFCM Specifically

BFCM is a single-week event, but the inventory impact spans 6–8 weeks:
- **Stock needs to be at Amazon FBA 4–6 weeks before** (FBA processing + buffer)
- **Stock needs to leave US warehouse 3–4 weeks before** that
- **Stock needs to leave China 8–12 weeks before** (sea freight)

### BFCM Planning Timeline (working backwards from Nov last week)

| Milestone | Timing |
|-----------|--------|
| BFCM week | Nov Week 4 |
| Stock must be at Amazon FBA | Oct Week 1 (6 weeks before) |
| Ship from US warehouse to FBA | Sep Week 2 (leave by) |
| New PO from China must arrive at US warehouse | Aug Week 3 |
| New PO from China must be placed | Jun–Jul (8–10 weeks before US arrival) |

### How to Run a BFCM Plan
```bash
# Step 1: Pull fresh data
python tools/pull_data.py

# Step 2: Run plan for November (captures peak seasonality)
python tools/run_demand_plan.py --plan-type monthly --plan-month YYYY-11

# Step 3: Also run quarterly to see the full Q4 picture
python tools/run_demand_plan.py --plan-type quarterly
```

Then ask Claude: "Summarize what we need to order for BFCM and what the deadlines are."

---

## Overriding Seasonality for a Specific Event

If you know a specific event will be bigger than historical patterns suggest (e.g., you're running a promo, launching a new product, or have a partnership), you can manually override the seasonality index:

1. Open the `Seasonality_Index` tab in the Google Sheet
2. Find the SKU and the relevant month
3. Update the index value (e.g., change November from 1.8 to 2.5)
4. Add a note in the `Override_Notes` column explaining why
5. Re-run the plan — it will use your overridden value

---

## Calculating How Much Extra Stock to Order for an Event

Example: BFCM for Kids Journal at Amazon US FBA
```
Normal November velocity:        15 units/day
BFCM week expected multiplier:  3x (based on last 2 years)
BFCM week extra demand:          15 × 3 × 7 days = 315 extra units
Lead time from US warehouse:     21 days
→ Extra units need to be at FBA 21 days before BFCM week starts
→ Need to leave US warehouse by: Nov 3 (roughly)
```

---

## Overstock After Events

After a major sales event, if you over-ordered:
1. Check Inventory_Health for OVERSTOCK flags
2. Options:
   - Run a post-event sale (Boxing Day, New Year promo)
   - Transfer excess to a warehouse with lower stock
   - Pause the next regular replenishment for that SKU at that location
3. Update PO_Tracker with a note if you're deferring a planned order

---

## Asking Claude for Event Planning

You can ask directly:
- "Plan for BFCM this year — what do we need to order and by when?"
- "What's our current state for Q4?"
- "If BFCM does 3x our normal November velocity, do we have enough at Amazon FBA?"
- "When is the last date we can place a China PO to have stock in time for Mother's Day?"

Claude will pull the latest data, run the relevant calculations, and give you a plain-language answer with the math shown.

---

## Edge Cases
- **New SKU launching before an event**: if the SKU doesn't have 12 months of history, seasonality will be 1.0 (neutral). Override it manually based on comparable SKU patterns.
- **Amazon FBA inventory limits**: FBA has storage limits, especially around Q4. Factor in whether you can send all the stock at once or need to stagger it via AWD.
- **Freight forwarder for UK/EU**: if you need to emergency-transfer from US to UK/EU for a holiday event, this is expensive and slow (30–90 days + freight forwarder cost). Plan early.
- **Currency/cost consideration**: when choosing between a transfer and a new China PO, factor in that China POs may be cheaper per unit but take longer. A transfer is faster but may create a shortage at the source warehouse.
