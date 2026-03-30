# Inventory Health Check

## Objective
Quick snapshot of current inventory state across all SKUs and warehouses. Answers: "Where are we healthy? Where are we at risk? What's in transit?"

---

## When to Use
- Weekly monitoring check
- After a sudden sales spike (to spot warehouses going critical)
- Before a sales event (verify you have enough buffer)
- Anytime someone asks "what's our current state?"

---

## How to Run

### Quick check (reuses last pull, no sheet write)
```bash
python tools/run_demand_plan.py --skip-write
```

### Full check with fresh data
```bash
python tools/run_demand_plan.py --plan-type monthly
```

### Health only (no routing or demand plan needed)
```bash
python tools/pull_data.py
python tools/calculate_velocity.py --data .tmp/data.json
python tools/calculate_seasonality.py --data .tmp/data.json
python tools/demand_plan.py --data .tmp/data.json --velocity .tmp/velocity.json --seasonality .tmp/seasonality.json
python tools/inventory_health.py --plan .tmp/demand_plan.json --data .tmp/data.json
```

---

## What to Look For

### CRITICAL (< 30 days)
- Immediate action required
- Check if there's already a PO in transit (PO_Tracker tab)
- If not → escalate to routing recommendation and place order today
- Calculate: is there time to transfer from another warehouse, or does a new PO need to be placed?

### LOW (30–90 days)
- Replenishment needed within this planning cycle
- Check lead time: if lead time from source = 45 days and you have 60 days of stock → order within 15 days
- Run demand_plan.py to get specific quantities

### OVERSTOCK (> 365 days)
- Flag for owner review
- Options: run a sale, transfer to lower-stock warehouse, pause next PO for this SKU at this location

### NO_DATA
- No sales recorded for this SKU at this warehouse
- Could be: new warehouse, SKU not sold there, data entry gap
- Verify manually — do not treat as "zero demand"

---

## Reading the Health Matrix
The Dashboard tab shows a matrix: SKU rows × Warehouse columns, each cell = days of stock + status.

Example:
```
                          SLI     HBG     SAV     KCM     EU      CA      AU      UK
Kids Journal (EIDJ4100)   120d OK  45d LOW  88d LOW  200d OK  55d LOW  310d OK  N/A  75d LOW
```
→ HBG, SAV, EU, and UK need replenishment for Kids Journal.

---

## Checking What's In Transit
Active POs and transfers are in the `PO_Tracker` tab. Also surfaced on the Dashboard.

Key fields:
- **Origin** → **Destination**: where stock is coming from/going to
- **Expected_Arrival**: when it lands
- **Qty_Ordered**: units on the way
- **Status**: Ordered / In Production / Shipped / In Transit

When a PO is received, update Status to "Received" — the tool will automatically exclude it from in-transit calculations.

---

## Checking Supplier Stock
`Supplier_Stock` tab shows current stock at China and Canada suppliers. This is the pool available for new POs before a production run is needed.

If supplier stock is low for a SKU → a new production run needs to be initiated, not just a PO.

---

## Week-to-Week Monitoring
If there's a sudden spike in sales at a warehouse:
1. Re-run `python tools/pull_data.py` (get fresh numbers)
2. Re-run `python tools/run_demand_plan.py --skip-pull` skips re-pull if you just did it
3. Look at the CRITICAL section of the Dashboard
4. Check if the spike is reflected in the 30d velocity vs 90d velocity (trend = ACCELERATING)
5. If yes, the adjusted velocity will account for it in the replenishment quantity

---

## Edge Cases
- **Amazon FBA stock** is updated manually in Current_Stock — Amazon doesn't auto-sync. Update this weekly from Seller Central.
- **Stock discrepancies**: if physical count doesn't match sheet, update Current_Stock before running plan
- **Seasonal spikes**: if health check shows LOW but it's expected seasonality, check Seasonality_Index to confirm the factor is applied
