"""
One-time utility to rename the Google Sheet.

Usage:
    python tools/rename_sheet.py --title "Inventory Planner - Big Life Journal"
"""
import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sheets_client import get_sheets_service, get_sheet_id, rename_spreadsheet


def main():
    parser = argparse.ArgumentParser(description='Rename the Google Sheet')
    parser.add_argument('--title', required=True, help='New title for the spreadsheet')
    args = parser.parse_args()

    service = get_sheets_service()
    sheet_id = get_sheet_id()

    rename_spreadsheet(service, sheet_id, args.title)
    print(f"Sheet renamed to: {args.title}")


if __name__ == '__main__':
    main()
