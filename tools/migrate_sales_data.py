"""
Migrate sales data from old sheet into new Sales_Data tab.

Sources:
  - "Sales Tracking - Update Monthly"  → 2024 & 2025 monthly sales
  - "Sales Log"                         → 2026 weekly sales

Target:
  - New sheet's Sales_Data tab

Usage:
    cd /Users/allyssa/Desktop/Claude
    python3 tools/migrate_sales_data.py --dry-run   # preview only, no writes
    python3 tools/migrate_sales_data.py             # write to new sheet
"""
import sys
import os
import argparse
from datetime import date
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_client import get_sheets_service, get_sheet_id, read_tab_raw, write_tab

OLD_SHEET_ID = '1SQu2Z_gAnxsxS3ODm0e2QT_Cgql__1gAsvbjPbeld5k'

MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}

# SKU blocks in "Sales Tracking - Update Monthly"
# Each block is 8 cols wide (7 data + 1 blank separator)
# Order matches the sheet left→right
SKU_BLOCKS = [
    ('EIDJ2100', 'Teen Journal',            2),
    ('EIDJ4100', 'Kids Journal',            10),
    ('EIDJ5100', 'Daily Journal Teal',      18),
    ('EIDJ5200', 'Daily Journal Green',     26),
    ('EIDJ5000', 'Adult Journal',           34),
    ('EIDC2000', 'Sharing Joy Cards',       42),
    ('EIDC2101', 'Dream Affirmation Cards', 50),
    ('EIDJB5002', 'Know Me Cards',          58),
]

# Within each block: column offset → warehouse ID in new sheet
# base+0 = US (Shopify) → US warehouses
# base+1 = US (Amazon)  → Amazon US FBA
# base+2 = US Combined  → SKIP (it's Shopify + Amazon added together)
# base+3 = AU & NZ      → AU
# base+4 = CA           → CA
# base+5 = UK           → UK
# base+6 = EU           → EU
TRACKING_OFFSETS = [
    (0, 'US'),
    (1, 'Amazon_US_FBA'),
    (3, 'AU'),
    (4, 'CA'),
    (5, 'UK'),
    (6, 'EU'),
]

# Product name → SKU ID for "Sales Log" (2026 weekly)
PRODUCT_NAME_MAP = {
    'kids journal':              'EIDJ4100',
    'teen journal':              'EIDJ2100',
    'daily edition (teal)':      'EIDJ5100',
    'daily journal teal':        'EIDJ5100',
    'daily edition (green)':     'EIDJ5200',
    'daily journal green':       'EIDJ5200',
    'adult journal':             'EIDJ5000',
    'joy conversation cards':    'EIDC2000',
    'sharing joy':               'EIDC2000',
    'joy cards':                 'EIDC2000',
    'dream affirmation cards':   'EIDC2101',
    'dream cards':               'EIDC2101',
    'know me if you can':        'EIDJB5002',
    'know me':                   'EIDJB5002',
}

SKU_NAMES = {
    'EIDJ4100': 'Kids Journal',
    'EIDJ2100': 'Teen Journal',
    'EIDJ5100': 'Daily Journal Teal',
    'EIDJ5200': 'Daily Journal Green',
    'EIDJ5000': 'Adult Journal',
    'EIDC2000': 'Sharing Joy Cards',
    'EIDC2101': 'Dream Affirmation Cards',
    'EIDJB5002': 'Know Me Cards',
}

# "Sales Log" column positions (0-indexed from raw row)
# Row 1 header: Month(3), Week&Date(4), ProductName(5),
#               US(6), AU(7), UK(8), CA(9), EU(10), AmazonUS(11), AmazonCA(12)
SALES_LOG_COLS = [
    (6,  'US'),
    (7,  'AU'),
    (8,  'UK'),
    (9,  'CA'),
    (10, 'EU'),
    (11, 'Amazon_US_FBA'),
    (12, 'Amazon_CA_FBA'),
]


def cell(row, idx, default=''):
    return row[idx] if idx < len(row) else default


def safe_int(val):
    if val is None or str(val).strip() == '':
        return 0
    try:
        return int(str(val).replace(',', '').strip())
    except (ValueError, TypeError):
        return 0


def parse_monthly_sales(rows):
    """Parse 'Sales Tracking - Update Monthly' → list of sales dicts."""
    results = []
    current_year = None

    # Rows 0-3 are headers; data starts at row 4
    for row in rows[4:]:
        if not row:
            continue

        year_val = str(cell(row, 0)).strip()
        month_val = str(cell(row, 1)).strip().lower()

        # Carry forward year (sheet may only fill it in first month)
        if year_val and year_val.isdigit():
            current_year = int(year_val)
        if not current_year:
            continue

        month_num = MONTH_MAP.get(month_val)
        if not month_num:
            continue

        row_date = f"{current_year}-{month_num:02d}-01"

        for sku_id, sku_name, base_col in SKU_BLOCKS:
            for offset, warehouse in TRACKING_OFFSETS:
                units = safe_int(cell(row, base_col + offset))
                if units > 0:
                    results.append({
                        'date': row_date,
                        'sku_id': sku_id,
                        'sku_name': sku_name,
                        'warehouse': warehouse,
                        'units_sold': units,
                        'week_number': '',
                        'year': current_year,
                    })

    return results


def parse_weekly_sales(rows):
    """Parse 'Sales Log' (2026 weekly) → list of sales dicts."""
    results = []
    year = 2026
    current_month = ''
    current_week = ''
    unrecognized = set()

    # Row 0: '2026' label, Row 1: headers, data starts at row 2
    for row in rows[2:]:
        if not row:
            continue

        month_val = str(cell(row, 3)).strip()
        week_val  = str(cell(row, 4)).strip()
        prod_val  = str(cell(row, 5)).strip()

        if month_val:
            current_month = month_val
        if week_val:
            current_week = week_val

        if not prod_val or not current_month or not current_week:
            continue

        # Map product name to SKU ID
        prod_lower = prod_val.lower()
        sku_id = None
        for key, sid in PRODUCT_NAME_MAP.items():
            if key in prod_lower:
                sku_id = sid
                break

        if not sku_id:
            unrecognized.add(prod_val)
            continue

        sku_name = SKU_NAMES[sku_id]

        # Convert month + week start day → date
        month_num = MONTH_MAP.get(current_month.lower())
        if not month_num:
            continue

        try:
            start_day = int(current_week.split('-')[0])
            row_date = f"{year}-{month_num:02d}-{start_day:02d}"
            week_num = date(year, month_num, start_day).isocalendar()[1]
        except (ValueError, IndexError):
            row_date = f"{year}-{month_num:02d}-01"
            week_num = ''

        for col_idx, warehouse in SALES_LOG_COLS:
            units = safe_int(cell(row, col_idx))
            if units > 0:
                results.append({
                    'date': row_date,
                    'sku_id': sku_id,
                    'sku_name': sku_name,
                    'warehouse': warehouse,
                    'units_sold': units,
                    'week_number': week_num,
                    'year': year,
                })

    if unrecognized:
        print(f"  Warning: unrecognized product names (skipped): {unrecognized}")

    return results


def main():
    parser = argparse.ArgumentParser(description='Migrate sales data to new Sales_Data tab')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, do not write')
    args = parser.parse_args()

    service = get_sheets_service()

    print("Reading old sheet...")
    tracking_rows  = read_tab_raw(service, OLD_SHEET_ID, 'Sales Tracking - Update Monthly')
    sales_log_rows = read_tab_raw(service, OLD_SHEET_ID, 'Sales Log')
    print(f"  Sales Tracking: {len(tracking_rows)} rows")
    print(f"  Sales Log:      {len(sales_log_rows)} rows")

    print("\nParsing 2024/2025 monthly data...")
    monthly = parse_monthly_sales(tracking_rows)
    print(f"  → {len(monthly)} data rows extracted")

    print("\nParsing 2026 weekly data...")
    weekly = parse_weekly_sales(sales_log_rows)
    print(f"  → {len(weekly)} data rows extracted")

    all_sales = monthly + weekly
    print(f"\nTotal: {len(all_sales)} rows")

    # Print summary
    summary = defaultdict(lambda: defaultdict(int))
    for r in all_sales:
        summary[r['year']][r['warehouse']] += r['units_sold']

    print("\nUnits by year + warehouse:")
    for yr in sorted(summary):
        for wh, total in sorted(summary[yr].items()):
            print(f"  {yr}  {wh:<20}  {total:>8,} units")

    if args.dry_run:
        print("\n[dry-run] No changes written.")
        return

    # Write to new sheet
    headers = ['Date', 'SKU_ID', 'SKU_Name', 'Warehouse', 'Units_Sold', 'Week_Number', 'Year', 'Notes']
    sheet_rows = [headers] + [
        [r['date'], r['sku_id'], r['sku_name'], r['warehouse'],
         r['units_sold'], r.get('week_number', ''), r['year'], '']
        for r in sorted(all_sales, key=lambda x: (x['date'], x['sku_id'], x['warehouse']))
    ]

    new_sheet_id = get_sheet_id()
    print(f"\nWriting {len(sheet_rows) - 1} rows to Sales_Data tab...")
    write_tab(service, new_sheet_id, 'Sales_Data', sheet_rows)
    print("Done! Open your sheet to verify Sales_Data tab.")


if __name__ == '__main__':
    main()
