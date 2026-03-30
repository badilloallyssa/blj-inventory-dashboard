"""Test Google Sheets API connection. Run this first to verify setup."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sheets_client import get_sheets_service, get_sheet_id, get_existing_tabs


def main():
    print("Testing Google Sheets connection...\n")
    try:
        service = get_sheets_service()
        sheet_id = get_sheet_id()
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        title = spreadsheet['properties']['title']
        tabs = get_existing_tabs(service, sheet_id)

        print(f"  Connected to: {title}")
        print(f"  Sheet ID:     {sheet_id}")
        print(f"  Existing tabs ({len(tabs)}): {', '.join(tabs) if tabs else 'none'}")
        print("\nConnection successful. Run setup_sheet.py next to create the required tabs.")
    except FileNotFoundError:
        print("ERROR: service_account.json not found.")
        print("\nQuick setup:")
        print("  1. Go to https://console.cloud.google.com")
        print("  2. Create/select a project → Enable 'Google Sheets API' and 'Google Drive API'")
        print("  3. IAM & Admin → Service Accounts → Create Service Account")
        print("  4. Give it a name (e.g. 'inventory-planner'), click Create")
        print("  5. Keys tab → Add Key → JSON → download the file")
        print("  6. Save it as service_account.json in your project root")
        print("  7. Share your Google Sheet with the service account email")
        print("     (found in the JSON under 'client_email')")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
