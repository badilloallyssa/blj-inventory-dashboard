"""
Orchestrator — runs the full demand planning pipeline end to end.

Steps:
  1. pull_data        → .tmp/data.json
  2. calculate_velocity → .tmp/velocity.json
  3. calculate_seasonality → .tmp/seasonality.json
  4. demand_plan      → .tmp/demand_plan.json
  5. recommend_routing → .tmp/routing.json
  6. inventory_health → .tmp/health.json
  7. write_plan       → Google Sheet (Dashboard, Demand_Plan, Routing, Health, Calc_Log)

Usage:
    python tools/run_demand_plan.py
    python tools/run_demand_plan.py --plan-type quarterly
    python tools/run_demand_plan.py --plan-type monthly --plan-month 2025-06
    python tools/run_demand_plan.py --skip-pull    # reuse existing .tmp/data.json
    python tools/run_demand_plan.py --skip-write   # run calculations only, don't write to sheet
"""
import sys
import os
import argparse
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tools'))


def step(label, fn, *args, **kwargs):
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    result = fn(*args, **kwargs)
    return result


def main():
    parser = argparse.ArgumentParser(description='Run full demand planning pipeline')
    parser.add_argument('--plan-type', choices=['monthly', 'quarterly'], default='monthly')
    parser.add_argument('--plan-month', help='YYYY-MM (monthly only)')
    parser.add_argument('--plan-quarter', help='YYYY-QN (quarterly only)')
    parser.add_argument('--skip-pull', action='store_true',
                        help='Skip data pull step — reuse existing .tmp/data.json')
    parser.add_argument('--skip-write', action='store_true',
                        help='Skip writing back to Google Sheet')
    args = parser.parse_args()

    start = datetime.now()
    print(f"\n{'='*60}")
    print(f"  DEMAND PLANNING PIPELINE")
    print(f"  Plan type: {args.plan_type.upper()}")
    if args.plan_month:
        print(f"  Plan month: {args.plan_month}")
    print(f"  Started:   {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # ── Step 1: Pull data ─────────────────────────────────────
    if args.skip_pull:
        print("\n  Skipping data pull (--skip-pull flag)")
        data_path = os.path.join(PROJECT_ROOT, '.tmp/data.json')
        if not os.path.exists(data_path):
            print("ERROR: .tmp/data.json not found. Cannot skip pull on first run.")
            sys.exit(1)
        with open(data_path) as f:
            data = json.load(f)
        print(f"  Loaded existing data from .tmp/data.json")
    else:
        from pull_data import main as pull_main
        import sys as _sys
        _sys.argv = ['pull_data.py']
        data = step("Step 1/7: Pulling data from Google Sheets", pull_main)

    # ── Step 2: Velocity ──────────────────────────────────────
    from calculate_velocity import calculate_velocity
    print(f"\n{'─'*60}")
    print(f"  Step 2/7: Calculating sales velocity")
    print(f"{'─'*60}")
    velocity_output = calculate_velocity(data)
    velocity_data = {'velocity': velocity_output, 'calculated_at': datetime.now().isoformat()}

    import json as _json
    os.makedirs(os.path.join(PROJECT_ROOT, '.tmp'), exist_ok=True)
    with open(os.path.join(PROJECT_ROOT, '.tmp/velocity.json'), 'w') as f:
        _json.dump(velocity_data, f, indent=2, default=str)
    print(f"  Velocity calculated for {len(velocity_output)} SKUs")

    # ── Step 3: Seasonality ───────────────────────────────────
    from calculate_seasonality import calculate_seasonality
    print(f"\n{'─'*60}")
    print(f"  Step 3/7: Calculating seasonality indices")
    print(f"{'─'*60}")
    indices, explanation = calculate_seasonality(data)
    seasonality_output = {'indices': indices, 'explanation': explanation, 'calculated_at': datetime.now().isoformat()}

    with open(os.path.join(PROJECT_ROOT, '.tmp/seasonality.json'), 'w') as f:
        _json.dump(seasonality_output, f, indent=2, default=str)
    print(f"  Seasonality calculated for {len(indices)} SKUs")

    # Merge seasonality into data for downstream use
    for sku_id, month_indices in indices.items():
        found = False
        for entry in data.setdefault('seasonality', []):
            if entry['sku_id'] == sku_id:
                entry['indices'] = month_indices
                found = True
        if not found:
            data['seasonality'].append({'sku_id': sku_id, 'sku_name': '', 'indices': month_indices})

    # ── Step 4: Demand plan ───────────────────────────────────
    from demand_plan import run_demand_plan
    print(f"\n{'─'*60}")
    print(f"  Step 4/7: Running demand plan ({args.plan_type})")
    print(f"{'─'*60}")
    plan_rows, calc_log_rows = run_demand_plan(
        data, velocity_data, data.get('seasonality', []),
        plan_type=args.plan_type,
        plan_month=args.plan_month,
        plan_quarter=args.plan_quarter
    )
    plan_data = {
        'generated_at': datetime.now().isoformat(),
        'plan_type': args.plan_type,
        'plan_rows': plan_rows,
        'calc_log_rows': calc_log_rows,
    }
    with open(os.path.join(PROJECT_ROOT, '.tmp/demand_plan.json'), 'w') as f:
        _json.dump(plan_data, f, indent=2, default=str)
    print(f"  Demand plan: {len(plan_rows)} SKU×Warehouse combinations")

    # ── Step 5: Routing ───────────────────────────────────────
    from recommend_routing import calculate_routing
    print(f"\n{'─'*60}")
    print(f"  Step 5/7: Calculating replenishment routing")
    print(f"{'─'*60}")
    routing_rows = calculate_routing(data, plan_data)
    routing_data = {'generated_at': datetime.now().isoformat(), 'routing_rows': routing_rows}
    with open(os.path.join(PROJECT_ROOT, '.tmp/routing.json'), 'w') as f:
        _json.dump(routing_data, f, indent=2, default=str)
    print(f"  Routing: {len(routing_rows)} recommendations")

    # ── Step 6: Health ────────────────────────────────────────
    from inventory_health import calculate_health
    print(f"\n{'─'*60}")
    print(f"  Step 6/7: Calculating inventory health")
    print(f"{'─'*60}")
    health_rows = calculate_health(data, plan_data)
    health_data = {
        'generated_at': datetime.now().isoformat(),
        'health_rows': health_rows,
        'summary': {}
    }
    from collections import defaultdict
    counts = defaultdict(int)
    for r in health_rows:
        counts[r['status']] += 1
    health_data['summary'] = dict(counts)
    with open(os.path.join(PROJECT_ROOT, '.tmp/health.json'), 'w') as f:
        _json.dump(health_data, f, indent=2, default=str)
    print(f"  Health: {dict(counts)}")

    # ── Step 7: Write to sheet ────────────────────────────────
    if args.skip_write:
        print(f"\n  Skipping sheet write (--skip-write flag)")
    else:
        from write_plan import (write_demand_plan_tab, write_routing_tab,
                                write_health_tab, write_calc_log_tab, write_dashboard)
        from sheets_client import get_sheets_service, get_sheet_id
        print(f"\n{'─'*60}")
        print(f"  Step 7/7: Writing results to Google Sheet")
        print(f"{'─'*60}")
        service = get_sheets_service()
        sheet_id = get_sheet_id()
        write_demand_plan_tab(service, sheet_id, plan_rows)
        write_routing_tab(service, sheet_id, routing_rows)
        write_health_tab(service, sheet_id, health_rows)
        write_calc_log_tab(service, sheet_id, calc_log_rows)
        write_dashboard(service, sheet_id, plan_rows, routing_rows, health_rows, data, plan_data)

    # ── Summary ───────────────────────────────────────────────
    elapsed = (datetime.now() - start).seconds
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE ({elapsed}s)")
    print(f"{'='*60}")

    critical_count = sum(1 for r in plan_rows if r['status'] == 'CRITICAL')
    low_count = sum(1 for r in plan_rows if r['status'] == 'LOW')
    overstock_count = sum(1 for r in plan_rows if r['status'] == 'OVERSTOCK')

    print(f"\n  CRITICAL (order now):    {critical_count}")
    print(f"  LOW (plan replenishment):{low_count}")
    print(f"  OVERSTOCK:               {overstock_count}")
    print(f"  Active POs tracked:      {len(data.get('pos', []))}")
    if not args.skip_write:
        print(f"\n  → Open your Google Sheet to view the Dashboard")


if __name__ == '__main__':
    main()
