"""
Small shared helpers used across multiple route modules.

Consolidated here to avoid near-identical copies of the same date/amount
parsing logic living separately in capital.py, expenses.py and vehicles.py.
"""

from datetime import datetime


def parse_date(value):
    """Parse a 'YYYY-MM-DD' string into a date object, or return None."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError, TypeError):
        return None


def parse_amount(value):
    """Parse a money string (commas allowed) into a float. Returns 0.0 if invalid."""
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0
