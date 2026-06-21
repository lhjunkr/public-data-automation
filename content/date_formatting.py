from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime


DISPLAY_DATE_FORMAT = "%Y.%m.%d"


def format_display_date(raw_date: str) -> str:
    normalized_date = raw_date.strip()

    if not normalized_date:
        return ""

    parsed_date = parse_raw_date(normalized_date)

    if parsed_date is None:
        return normalized_date

    return parsed_date.strftime(DISPLAY_DATE_FORMAT)


def parse_raw_date(raw_date: str) -> datetime | None:
    for date_format in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw_date, date_format)
        except ValueError:
            pass

    try:
        return parsedate_to_datetime(raw_date)
    except (TypeError, ValueError):
        return None
    
    