"""
One-time utility: read the old sheet and print structure so we can understand
how to transform the data into the new Sales_Data format.

Usage:
    python tools/explore_old_sheet.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sheets_client import get_sheets_service, get_existing_tabs, read_tab_raw

OLD_SHEET_ID = '1SQu2Z_gAnxsxS3ODm0e2QT_Cgql__1gAsvbjPbeld5k'


def main():
    service = get_sheets_service()

    # Show full rows 27 and 28 (Nov & Dec 2025) across all SKU blocks
    print("=== SALES TRACKING — ROWS 27 & 28 (full width) ===")
    rows = read_tab_raw(service, OLD_SHEET_ID, 'Sales Tracking - Update Monthly')
    for i in [27, 28]:
        row = rows[i] if i < len(rows) else []
        print(f"\n  row {i} ({len(row)} cols):")
        # Print in blocks of 8 (one per SKU)
        labels = ['Teen', 'Kids', 'Teal', 'Green', 'Adults', 'Joy', 'Dream', 'KnowMe']
        print(f"    col 0-1 (Year/Month): {row[:2]}")
        for idx, label in enumerate(labels):
            base = 2 + idx * 8
            block = row[base:base+7] if base+7 <= len(row) else row[base:] if base < len(row) else []
            print(f"    {label:<8} (cols {base}-{base+6}): {block}")


if __name__ == '__main__':
    main()
