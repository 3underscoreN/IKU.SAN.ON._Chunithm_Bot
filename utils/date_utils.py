from datetime import date


def next_month(ref: date) -> date:
    """Return the first day of the next month."""
    if ref.month == 12:
        return date(ref.year + 1, 1, 1)
    return date(ref.year, ref.month + 1, 1)


def parse_iso_date(date_str: str) -> date | None:
    """Parse ISO format date string (YYYY-MM-DD). Return None if invalid."""
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None

def is_month_key_format(input: str) -> bool:
    """Check if the input string is in 'YYYY-MM' format."""
    try:
        year, month = map(int, input.split('-'))
        if (1000 <= year and year <= 9999) and (1 <= month and month <= 12):
            return True
        return False
    except ValueError:
        return False