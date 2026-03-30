"""
Recommend replenishment routing for each SKU × Warehouse that needs stock.

Logic:
  1. Check proximity map for ordered source preference
  2. For each source candidate: verify available stock (minus that source's own needs)
  3. If source has enough → recommend transfer
  4. If internal sources all insufficient → recommend new PO from China supplier
  5. Flag Amazon AWD option for Amazon FBA when qty is above AWD threshold
  6. Never strip a source warehouse below its own 30-day buffer

Usage:
    python tools/recommend_routing.py --plan .tmp/demand_plan.json --data .tmp/data.json
    python tools/recommend_routing.py --plan .tmp/demand_plan.json --data .tmp/data.json --output .tmp/routing.json
"""
import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WAREHOUSES = ['SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA']
US_WAREHOUSES = ['SLI', 'HBG', 'SAV', 'KCM']

# Hard-coded lead times (days, midpoint) — mirrors Config tab
LEAD_TIME_TABLE = {
    ('China_Supplier', 'SLI'): 45, ('China_Supplier', 'HBG'): 45,
    ('China_Supplier', 'SAV'): 45, ('China_Supplier', 'KCM'): 45,
    ('China_Supplier', 'EU'): 75, ('China_Supplier', 'CA'): 45,
    ('China_Supplier', 'AU'): 45, ('China_Supplier', 'UK'): 75,
    ('Canada_Supplier', 'CA'): 14, ('Canada_Supplier', 'Amazon_CA_FBA'): 21,
    ('SLI', 'Amazon_US_FBA'): 21, ('HBG', 'Amazon_US_FBA'): 21,
    ('SAV', 'Amazon_US_FBA'): 21, ('KCM', 'Amazon_US_FBA'): 21,
    ('US_Warehouse', 'CA'): 21, ('US_Warehouse', 'Amazon_US_FBA'): 21,
    ('EU', 'UK'): 21, ('EU', 'AU'): 60,
    ('UK', 'EU'): 21, ('UK', 'AU'): 60,
    ('AU', 'UK'): 60, ('AU', 'EU'): 60,
    ('CA', 'Amazon_CA_FBA'): 21,
}


def get_lead_time(origin, destination):
    key = (origin, destination)
    if key in LEAD_TIME_TABLE:
        return LEAD_TIME_TABLE[key]
    # Try US_Warehouse as proxy for any US warehouse
    us_key = ('US_Warehouse', destination)
    if us_key in LEAD_TIME_TABLE:
        return LEAD_TIME_TABLE[us_key]
    return 45  # fallback


def get_proximity_sources(destination, config):
    """Return ordered list of source options for a destination."""
    prox = config.get('proximity_map', {})
    entry = prox.get(destination, {})
    sources = []
    for key in ['source_1', 'source_2', 'source_3']:
        s = entry.get(key, '').strip()
        if s:
            sources.append(s)
    return sources


def resolve_source_label(source_label, stock_index, sku_id, exclude_dest=None):
    """
    Resolve a proximity map label like 'US_Warehouse (highest stock)' to an actual warehouse ID.
    Returns (warehouse_id, available_qty) or None.
    """
    label_lower = source_label.lower()

    if 'china' in label_lower and 'awd' not in label_lower:
        return ('China_Supplier', None)  # unlimited new PO

    if 'awd' in label_lower or 'china_awd' in label_lower:
        return ('China_AWD', None)  # direct to AWD

    if 'canada_supplier' in label_lower or 'canada supplier' in label_lower:
        return ('Canada_Supplier', None)

    if 'us_warehouse' in label_lower or 'us warehouse' in label_lower:
        # Pick the US warehouse with the most available stock for this SKU
        best_wh = None
        best_qty = -1
        for wh in US_WAREHOUSES:
            if wh == exclude_dest:
                continue
            qty = stock_index.get(sku_id, {}).get(wh, 0.0)
            if qty > best_qty:
                best_qty = qty
                best_wh = wh
        if best_wh and best_qty > 0:
            return (best_wh, best_qty)
        return None

    # Direct warehouse match
    for wh in WAREHOUSES:
        if wh.lower() in label_lower or label_lower in wh.lower():
            if wh == exclude_dest:
                continue
            qty = stock_index.get(sku_id, {}).get(wh, 0.0)
            return (wh, qty)

    return None


def build_stock_index(data):
    """Build {sku_id: {warehouse: qty}} from current_stock list."""
    index = defaultdict(lambda: defaultdict(float))
    for entry in data.get('current_stock', []):
        sku = entry['sku_id']
        for wh, qty in entry.get('stock', {}).items():
            index[sku][wh] = float(qty)
    return index


def build_needs_index(plan_rows):
    """Build {sku_id: {warehouse: units_needed}} from demand plan."""
    needs = defaultdict(lambda: defaultdict(float))
    for row in plan_rows:
        if row['units_needed'] > 0:
            needs[row['sku_id']][row['warehouse']] = float(row['units_needed'])
    return needs


def calculate_routing(data, plan_data):
    config = data.get('config', {})
    thresholds = config.get('thresholds', {})
    awd_min_qty = int(thresholds.get('AWD_Minimum_Qty', 200))

    plan_rows = plan_data.get('plan_rows', [])
    stock_index = build_stock_index(data)
    needs_index = build_needs_index(plan_rows)

    # Track how much stock has been "allocated" from each warehouse
    # so we don't over-commit a source warehouse
    allocated = defaultdict(lambda: defaultdict(float))

    routing_rows = []
    run_date = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Process by urgency: CRITICAL first, then LOW
    prioritized = sorted(
        [r for r in plan_rows if r['units_needed'] > 0],
        key=lambda r: r['days_of_stock']
    )

    for plan_row in prioritized:
        sku_id = plan_row['sku_id']
        sku_name = plan_row['sku_name']
        destination = plan_row['warehouse']
        units_needed = int(plan_row['units_needed'])
        status = plan_row['status']

        if units_needed <= 0:
            continue

        priority = 'URGENT' if status == 'CRITICAL' else 'NORMAL'
        sources = get_proximity_sources(destination, config)

        # For US warehouses: always try US-to-US transfer first, before any China PO
        # Inject US_Warehouse as the first source candidate if not already listed
        if destination in US_WAREHOUSES:
            us_transfer_label = 'US_Warehouse (highest stock)'
            if not any('us_warehouse' in s.lower() or 'us warehouse' in s.lower() for s in sources):
                sources = [us_transfer_label] + sources

        chosen_source = None
        chosen_source_id = None
        source_available = None
        action_type = None
        lead_time = None
        notes = []

        # Try each source in order
        for source_label in sources:
            resolved = resolve_source_label(source_label, stock_index, sku_id, exclude_dest=destination)
            if resolved is None:
                notes.append(f"{source_label}: no stock found")
                continue

            src_id, available = resolved

            # Supplier = unlimited (new PO)
            if src_id in ('China_Supplier', 'Canada_Supplier', 'China_AWD'):
                chosen_source = source_label
                chosen_source_id = src_id
                source_available = 'New PO'
                action_type = 'China_AWD' if src_id == 'China_AWD' else 'New PO'
                lead_time = get_lead_time(src_id.replace('_AWD', '_Supplier'), destination)
                notes.append(f"New production order from {src_id}")
                break

            # Internal warehouse transfer
            if available is None:
                available = stock_index.get(sku_id, {}).get(src_id, 0.0)

            already_allocated = allocated[sku_id][src_id]
            # Keep a 30-day buffer at source (use source's own velocity if available)
            # Simple approximation: reserve 25% of source stock as buffer
            source_buffer = available * 0.25
            transferable = max(0, available - already_allocated - source_buffer)

            if transferable >= units_needed:
                chosen_source = src_id
                chosen_source_id = src_id
                source_available = int(available)
                action_type = 'Transfer'
                lead_time = get_lead_time(src_id, destination)
                allocated[sku_id][src_id] += units_needed
                notes.append(f"Transfer from {src_id} (available: {int(available)}, "
                              f"allocated: {int(already_allocated)}, transferable: {int(transferable)})")
                break
            elif transferable > 0:
                notes.append(f"{src_id}: only {int(transferable)} available (need {units_needed})")
            else:
                notes.append(f"{src_id}: insufficient stock ({int(available)} on hand, {int(already_allocated)} already allocated)")

        # If no source found, default to China new PO
        if chosen_source is None:
            chosen_source = 'China_Supplier'
            chosen_source_id = 'China_Supplier'
            source_available = 'New PO'
            action_type = 'New PO'
            lead_time = get_lead_time('China_Supplier', destination)
            notes.append("No internal source sufficient — new PO from China required")

        # Check AWD option for Amazon FBA
        awd_note = ''
        if destination in ('Amazon_US_FBA', 'Amazon_CA_FBA') and units_needed >= awd_min_qty:
            awd_note = f" (Consider AWD for bulk qty ≥ {awd_min_qty} — auto-replenishes FBA)"

        # Order deadline: when to place the order so stock arrives by target date
        order_deadline = (datetime.now() + timedelta(days=max(0, plan_row['days_of_stock'] - lead_time)))
        estimated_arrival = (datetime.now() + timedelta(days=plan_row['days_of_stock'] + lead_time))

        routing_rows.append({
            'run_date': run_date,
            'sku_id': sku_id,
            'sku_name': sku_name,
            'destination': destination,
            'units_needed': units_needed,
            'recommended_source': chosen_source_id,
            'source_available': source_available,
            'lead_time_days': lead_time,
            'action_type': action_type,
            'order_deadline': order_deadline.strftime('%Y-%m-%d'),
            'estimated_arrival': estimated_arrival.strftime('%Y-%m-%d'),
            'priority': priority,
            'days_of_stock': plan_row['days_of_stock'],
            'notes': (' | '.join(notes) + awd_note).strip(' |'),
        })

    return routing_rows


def main():
    parser = argparse.ArgumentParser(description='Generate replenishment routing recommendations')
    parser.add_argument('--plan', default='.tmp/demand_plan.json')
    parser.add_argument('--data', default='.tmp/data.json')
    parser.add_argument('--output', default='.tmp/routing.json')
    args = parser.parse_args()

    for path in [args.plan, args.data]:
        full = os.path.join(PROJECT_ROOT, path)
        if not os.path.exists(full):
            print(f"ERROR: {path} not found.")
            sys.exit(1)

    with open(os.path.join(PROJECT_ROOT, args.plan)) as f:
        plan_data = json.load(f)
    with open(os.path.join(PROJECT_ROOT, args.data)) as f:
        data = json.load(f)

    print("Calculating replenishment routing...")
    routing = calculate_routing(data, plan_data)

    # Summary
    action_counts = defaultdict(int)
    for r in routing:
        action_counts[r['action_type']] += 1
    print(f"\n{len(routing)} replenishment recommendations:")
    for action, count in sorted(action_counts.items()):
        print(f"  {action:<20} {count}")

    urgent = [r for r in routing if r['priority'] == 'URGENT']
    if urgent:
        print(f"\nURGENT ({len(urgent)}):")
        for r in urgent:
            print(f"  {r['sku_name']:<35} {r['destination']:<20} "
                  f"→ {r['recommended_source']:<20} {r['units_needed']:>5} units  "
                  f"by {r['order_deadline']}")

    output = {
        'generated_at': datetime.now().isoformat(),
        'routing_rows': routing,
    }

    output_path = os.path.join(PROJECT_ROOT, args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nSaved to {args.output}")
    return output


if __name__ == '__main__':
    main()
