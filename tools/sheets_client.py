"""Shared Google Sheets API helper. Not a standalone tool — imported by other tools."""
import os
import sys
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# service_account.json lives in project root (parent of tools/)
SERVICE_ACCOUNT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'service_account.json'
)


def get_sheets_service():
    # Support credentials from env var (for Render/Railway hosting)
    # or from service_account.json file (local dev)
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        import json
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    elif os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    else:
        print("ERROR: No Google credentials found.")
        print("Local: add service_account.json to project root.")
        print("Hosted: set GOOGLE_CREDENTIALS_JSON environment variable.")
        sys.exit(1)
    return build('sheets', 'v4', credentials=creds)


def get_sheet_id():
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID not set in .env")
    return sheet_id


def get_existing_tabs(service, sheet_id):
    """Return list of existing tab names."""
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return [s['properties']['title'] for s in spreadsheet['sheets']]


def add_tab(service, sheet_id, tab_name, index=None):
    """Add a new tab. Skips silently if it already exists."""
    existing = get_existing_tabs(service, sheet_id)
    if tab_name in existing:
        return
    req = {'addSheet': {'properties': {'title': tab_name}}}
    if index is not None:
        req['addSheet']['properties']['index'] = index
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': [req]}
    ).execute()


def read_tab(service, sheet_id, tab_name):
    """Read a tab, return list of dicts (row per item, header row as keys)."""
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=tab_name
    ).execute()
    values = result.get('values', [])
    if len(values) < 2:
        return []
    headers = list(values[0])
    rows = []
    for row in values[1:]:
        # Pad short rows with empty strings
        padded = list(row) + [''] * (len(headers) - len(list(row)))
        if any(padded):  # skip completely empty rows
            rows.append(dict(zip(headers, padded)))
    return rows


def read_tab_raw(service, sheet_id, tab_name):
    """Read a tab, return raw list of lists (no header processing)."""
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=tab_name
    ).execute()
    return result.get('values', [])


def write_tab(service, sheet_id, tab_name, data, clear_first=True):
    """Write list-of-lists to a tab. First row should be headers."""
    if clear_first:
        service.spreadsheets().values().clear(
            spreadsheetId=sheet_id,
            range=tab_name
        ).execute()
    if not data:
        return
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        valueInputOption='USER_ENTERED',
        body={'values': data}
    ).execute()


def add_note(service, sheet_id, tab_name, row, col, note_text):
    """Add a note/comment to a specific cell (row/col are 0-indexed)."""
    # Get sheet ID (numeric) for this tab
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheet_gid = None
    for s in spreadsheet['sheets']:
        if s['properties']['title'] == tab_name:
            sheet_gid = s['properties']['sheetId']
            break
    if sheet_gid is None:
        return
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': [{
            'updateCells': {
                'range': {
                    'sheetId': sheet_gid,
                    'startRowIndex': row,
                    'endRowIndex': row + 1,
                    'startColumnIndex': col,
                    'endColumnIndex': col + 1
                },
                'rows': [{'values': [{'note': note_text}]}],
                'fields': 'note'
            }
        }]}
    ).execute()


def append_rows_to_tab(service, sheet_id, tab_name, rows):
    """Append rows to a tab without touching existing data."""
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': rows}
    ).execute()


def rename_spreadsheet(service, sheet_id, new_title):
    """Rename the spreadsheet itself (not a tab)."""
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': [{'updateSpreadsheetProperties': {
            'properties': {'title': new_title},
            'fields': 'title'
        }}]}
    ).execute()


def format_header_row(service, sheet_id, tab_name, bold=True, bg_color=None):
    """Format the first row of a tab as a header (bold, optional background color)."""
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheet_gid = None
    for s in spreadsheet['sheets']:
        if s['properties']['title'] == tab_name:
            sheet_gid = s['properties']['sheetId']
            break
    if sheet_gid is None:
        return

    fmt = {'textFormat': {'bold': bold}}
    if bg_color:
        fmt['backgroundColor'] = bg_color  # e.g. {'red': 0.9, 'green': 0.9, 'blue': 0.9}

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': [{
            'repeatCell': {
                'range': {
                    'sheetId': sheet_gid,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {'userEnteredFormat': fmt},
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        }]}
    ).execute()
