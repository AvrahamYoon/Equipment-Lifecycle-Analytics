"""Business-day span (Mon–Fri, US federal holidays excluded)."""

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar


def _federal_holiday_norm_set():
    cal = USFederalHolidayCalendar()
    h = cal.holidays(start="2000-01-01", end="2035-12-31")
    return {pd.Timestamp(ts).normalize() for ts in h}


_FED_HOLIDAYS_NORM = _federal_holiday_norm_set()


def business_days_inclusive(start, end) -> float:
    """Count business days from *start* through *end* (Mon–Fri, US federal holidays out).

    Same calendar day (schedule = completion) counts as **1** even on a weekend or
    holiday, so same-day turnaround is never shown as 0.
    """
    if pd.isna(start) or pd.isna(end):
        return float("nan")
    a = pd.Timestamp(start).normalize()
    b = pd.Timestamp(end).normalize()
    if b < a:
        return float("nan")
    if a == b:
        return 1.0
    n = 0
    for d in pd.date_range(a, b, freq="D"):
        if d.weekday() >= 5:
            continue
        if d.normalize() in _FED_HOLIDAYS_NORM:
            continue
        n += 1
    return float(n)
