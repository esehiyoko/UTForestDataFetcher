"""Months in a range of dates."""

import datetime
import re

MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def to_date(value, name="date"):
    """A date from a date, a datetime, ``YYYY-MM-DD``, ``YYYY/MM/DD`` or ``YYYY-MM`` (first day)."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    text = str(value).strip().replace("/", "-")
    m = re.match(r"^(\d{4})-(\d{1,2})(?:-(\d{1,2}))?$", text)
    if not m:
        raise ValueError(f"{name} must be a date or YYYY-MM-DD: {value!r}")
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))
    except ValueError:
        raise ValueError(f"{name} is not a valid date: {value!r}") from None


def month_of(value):
    d = to_date(value)
    return f"{d.year:04d}-{d.month:02d}"


def months(range_):
    """``YYYY-MM`` for every month from the first date's month to the second's, both included."""
    try:
        start, end = range_
    except (TypeError, ValueError):
        raise ValueError("range must be (FROM, TO)") from None
    start, end = to_date(start, "FROM"), to_date(end, "TO")
    if start > end:
        raise ValueError("FROM is after TO")
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def check_month(value):
    text = str(value)
    if not MONTH.match(text):
        raise ValueError(f"month must be YYYY-MM: {value!r}")
    return text
