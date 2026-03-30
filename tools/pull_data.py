"""
Pull all data from the Inventory & Demand Planner Google Sheet.
Saves to .tmp/data.json for use by downstream tools.

Usage:
    python tools/pull_data.py
    python tools/pull_data.py --output .tmp/data.json
"""
import sys
import os
import json
import argparse
from datetime import datetime, date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sheets_client import get_sheets_service, get_sheet_id, read_tab

TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.tmp')


def pull_sales_data(service, sheet_id):
    rows = read_tab(service, sheet_id, 'Sales_Data')
    result = []
    for r in rows:
        try:
            result.append({
                'date': r.get('Date', ''),
                'sku_id': r.get('SKU_ID', '').strip(),
                'sku_name': r.get('SKU_Name', '').strip(),
                'warehouse': r.get('Warehouse', '').strip(),
                'units_sold': float(r.get('Units_Sold', 0) or 0),
                'week_number': r.get('Week_Number', ''),
                'year': r.get('Year', ''),
            })
        except (ValueError, TypeError):
            continue  # skip malformed rows
    return result


def pull_current_stock(service, sheet_id):
    rows = read_tab(service, sheet_id, 'Current_Stock')
    warehouses = ['SLI', 'HBG', 'SAV', 'KCM', 'EU', 'CA', 'AU', 'UK', 'Amazon_US_FBA', 'Amazon_CA_FBA']
    result = []
    for r in rows:
        if not r.get('SKU_ID'):
            continue
        entry = {
            'last_updated': r.get('Last_Updated', ''),
            'sku_id': r.get('SKU_ID', '').strip(),
            'sku_name': r.get('SKU_Name', '').strip(),
            'stock': {}
        }
        for wh in warehouses:
            entry['stock'][wh] = float(r.get(wh, 0) or 0)
        result.append(entry)
    return result


def pull_supplier_stock(service, sheet_id):
    rows = read_tab(service, sheet_id, 'Supplier_Stock')
    result = []
    for r in rows:
        if not r.get('SKU_ID'):
            continue
        result.append({
            'last_updated': r.get('Last_Updated', ''),
            'sku_id': r.get('SKU_ID', '').strip(),
            'sku_name': r.get('SKU_Name', '').strip(),
            'china_supplier': float(r.get('China_Supplier', 0) or 0),
            'canada_supplier': float(r.get('Canada_Supplier', 0) or 0),
            'notes': r.get('Notes', ''),
        })
    return result


def pull_po_tracker(service, sheet_id):
    rows = read_tab(service, sheet_id, 'PO_Tracker')
    result = []
    for r in rows:
        if not r.get('PO_ID'):
            continue
        status = r.get('Status', '').strip().lower()
        if status in ('received', 'cancelled', 'canceled'):
            continue  # exclude completed/cancelled POs
        result.append({
            'po_id': r.get('PO_ID', '').strip(),
            'type': r.get('Type', '').strip(),
            'sku_id': r.get('SKU_ID', '').strip(),
            'sku_name': r.get('SKU_Name', '').strip(),
            'qty_ordered': float(r.get('Qty_Ordered', 0) or 0),
            'origin': r.get('Origin', '').strip(),
            'destination': r.get('Destination', '').strip(),
            'order_date': r.get('Order_Date', ''),
            'expected_arrival': r.get('Expected_Arrival', ''),
            'status': r.get('Status', '').strip(),
            'notes': r.get('Notes', ''),
        })
    return result


def pull_config(service, sheet_id):
    """Parse the structured Config tab into a usable dict."""
    from sheets_client import read_tab_raw
    rows = read_tab_raw(service, sheet_id, 'Config')

    config = {
        'skus': [],
        'warehouses': [],
        'lead_times': {},
        'proximity_map': {},
        'thresholds': {}
    }

    section = None
    for row in rows:
        if not row:
            continue
        first = row[0].strip() if row[0] else ''

        # Detect section headers
        if 'SKU MASTER' in str(row):
            section = 'sku_header'
            continue
        elif 'WAREHOUSE MASTER' in str(row):
            section = 'wh_header'
            continue
        elif 'LEAD TIMES' in str(row):
            section = 'lt_header'
            continue
        elif 'PROXIMITY MAP' in str(row):
            section = 'prox_header'
            continue
        elif 'PLANNING THRESHOLDS' in str(row):
            section = 'thresh_header'
            continue

        # Skip header rows (column labels)
        if first in ('SKU_ID', 'Warehouse_ID', 'From → To', 'Destination', 'Parameter', ''):
            if first == 'From → To':
                section = 'lead_times'
                config['lead_times']['_headers'] = [c.strip() for c in row[1:] if c]
            elif first == 'Destination':
                section = 'proximity'
            elif first == 'Parameter':
                section = 'thresholds'
            elif first == 'SKU_ID':
                section = 'skus'
            elif first == 'Warehouse_ID':
                section = 'warehouses'
            continue

        # Parse data rows by section
        if section == 'skus' and first:
            config['skus'].append({
                'sku_id': first,
                'sku_name': row[1].strip() if len(row) > 1 else '',
                'short_name': row[2].strip() if len(row) > 2 else '',
                'active': (row[3].strip().upper() == 'TRUE') if len(row) > 3 else True
            })

        elif section == 'warehouses' and first:
            config['warehouses'].append({
                'id': first,
                'name': row[1].strip() if len(row) > 1 else '',
                'region': row[2].strip() if len(row) > 2 else '',
                'type': row[3].strip() if len(row) > 3 else '',
                'location': row[4].strip() if len(row) > 4 else '',
            })

        elif section == 'lead_times' and first:
            headers = config['lead_times'].get('_headers', [])
            config['lead_times'][first] = {}
            for i, h in enumerate(headers):
                val = row[i + 1] if i + 1 < len(row) else ''
                config['lead_times'][first][h] = int(val) if str(val).isdigit() else None

        elif section == 'proximity' and first:
            config['proximity_map'][first] = {
                'source_1': row[1].strip() if len(row) > 1 else '',
                'source_2': row[2].strip() if len(row) > 2 else '',
                'source_3': row[3].strip() if len(row) > 3 else '',
                'notes': row[4].strip() if len(row) > 4 else '',
            }

        elif section == 'thresholds' and first:
            val = row[1] if len(row) > 1 else ''
            try:
                config['thresholds'][first] = float(val)
            except (ValueError, TypeError):
                config['thresholds'][first] = val

    return config


def pull_seasonality(service, sheet_id):
    rows = read_tab(service, sheet_id, 'Seasonality_Index')
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    result = []
    for r in rows:
        if not r.get('SKU_ID'):
            continue
        entry = {
            'sku_id': r.get('SKU_ID', '').strip(),
            'sku_name': r.get('SKU_Name', '').strip(),
            'indices': {}
        }
        for m in months:
            val = r.get(m, '')
            try:
                entry['indices'][m] = float(val) if val else None
            except (ValueError, TypeError):
                entry['indices'][m] = None
        result.append(entry)
    return result


def main():
    parser = argparse.ArgumentParser(description='Pull all data from Inventory Planner Sheet')
    parser.add_argument('--output', default='.tmp/data.json', help='Output file path')
    args = parser.parse_args()

    service = get_sheets_service()
    sheet_id = get_sheet_id()

    print("Pulling data from Google Sheets...")

    data = {}

    print("  Reading Sales_Data...")
    data['sales'] = pull_sales_data(service, sheet_id)

    print("  Reading Current_Stock...")
    data['current_stock'] = pull_current_stock(service, sheet_id)

    print("  Reading Supplier_Stock...")
    data['supplier_stock'] = pull_supplier_stock(service, sheet_id)

    print("  Reading PO_Tracker...")
    data['pos'] = pull_po_tracker(service, sheet_id)

    print("  Reading Config...")
    data['config'] = pull_config(service, sheet_id)

    print("  Reading Seasonality_Index...")
    data['seasonality'] = pull_seasonality(service, sheet_id)

    data['pulled_at'] = datetime.now().isoformat()

    # Summary
    print(f"\n  Sales rows:       {len(data['sales'])}")
    print(f"  Stock entries:    {len(data['current_stock'])}")
    print(f"  Supplier entries: {len(data['supplier_stock'])}")
    print(f"  Active POs:       {len(data['pos'])}")
    print(f"  SKUs in config:   {len(data['config']['skus'])}")

    # Save
    os.makedirs(TMP_DIR, exist_ok=True)
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), args.output)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"\nSaved to {args.output}")
    return data


if __name__ == '__main__':
    main()
