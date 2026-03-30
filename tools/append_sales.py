"""
Append weekly sales data to Sales_Data tab without touching history.

Each week, I update WEEKLY_DATA with new numbers, then run:

    python3 tools/append_sales.py --dry-run   # preview rows
    python3 tools/append_sales.py             # write to sheet

WEEKLY_DATA is a list — can hold one week or multiple for catch-up.
Each entry: week_start (Monday date), week_number, year, sales {SKU: {warehouse: units}}
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_client import get_sheets_service, get_sheet_id, append_rows_to_tab

SKU_NAMES = {
    'EIDJ2100':  'Teen Journal',
    'EIDJ4100':  'Kids Journal',
    'EIDJ5100':  'Daily Journal Teal',
    'EIDJ5200':  'Daily Journal Green',
    'EIDJ5000':  'Adult Journal',
    'EIDC2000':  'Sharing Joy Cards',
    'EIDC2101':  'Dream Affirmation Cards',
    'EIDJB5002': 'Know Me Cards',
}

# ── Update this list each week (add new entry at the bottom) ─────────────────
WEEKLY_DATA = [
    {
        'week_start': '2026-03-02',  # March 1-7
        'week_number': 10,
        'year': 2026,
        'sales': {
            'EIDJ4100': {'US': 163, 'AU': 141, 'UK': 97,  'CA': 131, 'EU': 60,  'Amazon_US_FBA': 292},
            'EIDJ2100': {'US': 104, 'AU': 111, 'UK': 121, 'CA': 79,  'EU': 55,  'Amazon_US_FBA': 342},
            'EIDJ5100': {'US': 86,  'AU': 53,  'UK': 90,  'CA': 25,  'EU': 30,  'Amazon_US_FBA': 239},
            'EIDJ5200': {'US': 32,  'AU': 21,  'UK': 20,  'CA': 10,  'EU': 8,   'Amazon_US_FBA': 144},
            'EIDJ5000': {'US': 33,  'AU': 23,  'UK': 53,  'CA': 9,   'EU': 14,  'Amazon_US_FBA': 46},
            'EIDC2000': {'US': 53,  'AU': 58,  'UK': 70,  'CA': 18,  'EU': 14,  'Amazon_US_FBA': 170},
            'EIDC2101': {'US': 37,  'AU': 28,  'UK': 28,  'CA': 13,  'EU': 10,  'Amazon_US_FBA': 105},
            'EIDJB5002':{'US': 38,  'AU': 30,  'UK': 23,  'CA': 21,  'EU': 22,  'Amazon_US_FBA': 77},
        }
    },
    {
        'week_start': '2026-03-09',  # March 8-14
        'week_number': 11,
        'year': 2026,
        'sales': {
            'EIDJ4100': {'US': 163, 'AU': 152, 'UK': 140, 'CA': 56,  'EU': 73,  'Amazon_US_FBA': 163},
            'EIDJ2100': {'US': 82,  'AU': 103, 'UK': 153, 'CA': 28,  'EU': 57,  'Amazon_US_FBA': 169},
            'EIDJ5100': {'US': 69,  'AU': 55,  'UK': 88,  'CA': 30,  'EU': 37,  'Amazon_US_FBA': 109},
            'EIDJ5200': {'US': 22,  'AU': 14,  'UK': 32,  'CA': 10,  'EU': 17,  'Amazon_US_FBA': 64},
            'EIDJ5000': {'US': 22,  'AU': 20,  'UK': 42,  'CA': 15,  'EU': 22,  'Amazon_US_FBA': 46},
            'EIDC2000': {'US': 29,  'AU': 67,  'UK': 66,  'CA': 7,   'EU': 14,  'Amazon_US_FBA': 95},
            'EIDC2101': {'US': 14,  'AU': 11,  'UK': 15,  'CA': 8,   'EU': 10,  'Amazon_US_FBA': 43},
            'EIDJB5002':{'US': 28,  'AU': 20,  'UK': 29,  'CA': 11,  'EU': 27,  'Amazon_US_FBA': 37},
        }
    },
    {
        'week_start': '2026-03-16',  # March 15-21
        'week_number': 12,
        'year': 2026,
        'sales': {
            'EIDJ4100': {'US': 228, 'AU': 175, 'UK': 39,  'CA': 50,  'EU': 72,  'Amazon_US_FBA': 181},
            'EIDJ2100': {'US': 61,  'AU': 106, 'UK': 70,  'CA': 12,  'EU': 50,  'Amazon_US_FBA': 361},
            'EIDJ5100': {'US': 72,  'AU': 59,  'UK': 64,  'CA': 14,  'EU': 37,  'Amazon_US_FBA': 173},
            'EIDJ5200': {'US': 16,  'AU': 4,   'UK': 16,  'CA': 4,   'EU': 8,   'Amazon_US_FBA': 123},
            'EIDJ5000': {'US': 17,  'AU': 26,  'UK': 27,  'CA': 5,   'EU': 14,  'Amazon_US_FBA': 23},
            'EIDC2000': {'US': 20,  'AU': 55,  'UK': 65,  'CA': 2,   'EU': 12,  'Amazon_US_FBA': 112},
            'EIDC2101': {'US': 13,  'AU': 12,  'UK': 19,  'CA': 4,   'EU': 8,   'Amazon_US_FBA': 46},
            'EIDJB5002':{'US': 24,  'AU': 19,  'UK': 19,  'CA': 8,   'EU': 22,  'Amazon_US_FBA': 56},
        }
    },
    # ── Add next week below when ready ───────────────────────────────────────
    # {
    #     'week_start': '2026-03-23',  # March 22-28
    #     'week_number': 13,
    #     'year': 2026,
    #     'sales': {
    #         'EIDJ4100': {'US': 0, 'AU': 0, 'UK': 0, 'CA': 0, 'EU': 0, 'Amazon_US_FBA': 0},
    #         ...
    #     }
    # },
]
# ─────────────────────────────────────────────────────────────────────────────


def build_rows(data):
    rows = []
    for week in data:
        for sku_id, warehouses in week['sales'].items():
            sku_name = SKU_NAMES.get(sku_id, sku_id)
            for warehouse, units in warehouses.items():
                if units and units > 0:
                    rows.append([
                        week['week_start'], sku_id, sku_name, warehouse,
                        units, week['week_number'], week['year'], ''
                    ])
    rows.sort(key=lambda r: (r[0], r[1], r[3]))
    return rows


def main():
    parser = argparse.ArgumentParser(description='Append weekly sales to Sales_Data tab')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, no writes')
    args = parser.parse_args()

    rows = build_rows(WEEKLY_DATA)
    weeks = sorted(set(r[0] for r in rows))

    print(f"Weeks to append: {', '.join(weeks)}")
    print(f"Total rows: {len(rows)}\n")

    total = 0
    for week_start in weeks:
        week_rows = [r for r in rows if r[0] == week_start]
        week_total = sum(r[4] for r in week_rows)
        print(f"  {week_start} (wk {week_rows[0][5]}): {len(week_rows)} rows, {week_total:,} units")
        total += week_total
    print(f"\n  Grand total: {total:,} units")

    if args.dry_run:
        print("\n[dry-run] No changes written.")
        return

    service = get_sheets_service()
    sheet_id = get_sheet_id()
    append_rows_to_tab(service, sheet_id, 'Sales_Data', rows)
    print(f"\nAppended {len(rows)} rows to Sales_Data. Historical data untouched.")


if __name__ == '__main__':
    main()
