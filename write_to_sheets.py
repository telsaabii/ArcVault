import gspread
import re
import os
import logging 
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SPREADSHEET_ID      = os.environ.get("SPREADSHEET_ID", "YOUR_SPREADSHEET_ID_HERE")
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

SHEET_NAMES = ["All", "Engineering", "Billing", "Product", "IT/Security", "Escalation"]

# Columns written to every sheet (order matters — matches _build_row)
HEADERS = [
    "intake_id", "received_at", "sender", "source",
    "raw_message",
    "category", "priority", "confidence_score",
    "core_issue", "account_id", "invoice_number", "error_code", "other_identifier",
    "urgency_signal",
    "queue", "routing_reason", "escalated", "escalation_reason","summary",
]

def _get_sheets_client() -> gspread.Spreadsheet:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)

def _ensure_sheets(spreadsheet: gspread.Spreadsheet) -> dict[str, gspread.Worksheet]:
    """
    Makes sure all six worksheets exist and have the correct header row.
    Returns a dict mapping sheet name → Worksheet object.
    """
    existing = {ws.title: ws for ws in spreadsheet.worksheets()}
    sheets: dict[str, gspread.Worksheet] = {}

    for name in SHEET_NAMES:
        if name not in existing:
            ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=len(HEADERS))
            ws.append_row(HEADERS)
            logger.info("Created worksheet '%s'", name)
        else:
            ws = existing[name]
            # Add headers if the sheet is brand-new/empty
            if ws.row_count == 0 or ws.cell(1, 1).value != HEADERS[0]:
                ws.insert_row(HEADERS, index=1)
        sheets[name] = ws

    return sheets

def _build_row(record: dict) -> list:
    """Converts the merged pipeline+routing record into an ordered list matching HEADERS."""
    ids = record.get("identifiers", {})
    return [
        record.get("intake_id", ""),
        record.get("received_at", ""),
        record.get("sender", ""),
        record.get("source", ""),
        record.get("raw_message", ""),
        record.get("category", ""),
        record.get("priority", ""),
        record.get("confidence_score", ""),
        record.get("core_issue", ""),
        ids.get("account_id", ""),
        ids.get("invoice_number", ""),
        ids.get("error_code", ""),
        ids.get("other", ""),
        record.get("urgency_signal", ""),
        record.get("queue", ""),
        record.get("routing_reason", ""),
        str(record.get("escalated", False)),
        record.get("escalation_reason", ""),
        record.get("summary", ""),
    ]

def _write_to_sheets(record: dict) -> None:
    """Appends the record to the 'All' sheet and the queue-specific sheet."""
    try:
        spreadsheet = _get_sheets_client()
        sheets      = _ensure_sheets(spreadsheet)
        row         = _build_row(record)
        queue_name  = record.get("queue", "Escalation")

        sheets["All"].append_row(row)
        sheets[queue_name].append_row(row)

        logger.info("Written to sheets: All + %s", queue_name)
    except Exception as e:
        # Log but don't crash the API — sheets write is best-effort in dev
        logger.error("Google Sheets write failed: %s", e)
