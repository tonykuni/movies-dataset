from __future__ import annotations

"""Shared point-in-time timestamp normalization for VIA v0.5.

Availability timestamps are stored UTC-aware.  Trading and observation dates
are stored as timezone-naive Asia/Taipei calendar dates.  Naive timestamps are
explicitly interpreted as Asia/Taipei rather than silently treated as UTC.
"""

from typing import Any

import pandas as pd


LOCAL_TIMEZONE = "Asia/Taipei"
UTC_TIMEZONE = "UTC"


def def_available_at_utc(value: Any) -> pd.Timestamp | pd.NaT:
    if value is None or value is pd.NaT or value is pd.NA:
        return pd.NaT
    if pd.api.types.is_scalar(value) and bool(pd.isna(value)):
        return pd.NaT
    text = str(value).strip()
    if not text:
        return pd.NaT
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize(LOCAL_TIMEZONE)
    return stamp.tz_convert(UTC_TIMEZONE)


def def_local_calendar_date(value: Any) -> pd.Timestamp | pd.NaT:
    if value is None or value is pd.NaT or value is pd.NA:
        return pd.NaT
    if pd.api.types.is_scalar(value) and bool(pd.isna(value)):
        return pd.NaT
    text = str(value).strip()
    if not text:
        return pd.NaT
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert(LOCAL_TIMEZONE).tz_localize(None)
    return stamp.normalize()
