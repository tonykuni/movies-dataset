# -*- coding: utf-8 -*-
"""
def VDF_Engine_aaii_sentiment
AAII Sentiment Survey engine.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests

from VDF_Engine_sentiment_strength import def_normalize_percent_column, def_calc_aaii_strength


def def_find_column(columns: list[str], keywords: list[str]) -> str | None:
    lowered = {str(c).strip().lower(): c for c in columns}

    for key in keywords:
        key_l = key.lower()
        for c_l, original in lowered.items():
            if key_l in c_l:
                return original

    return None


def def_clean_aaii_dataframe(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    date_col = def_find_column(
        list(df.columns),
        ["date", "reported", "week", "ending", "survey"]
    )

    bullish_col = def_find_column(list(df.columns), ["bullish", "bull"])
    neutral_col = def_find_column(list(df.columns), ["neutral"])
    bearish_col = def_find_column(list(df.columns), ["bearish", "bear"])

    if bullish_col is None or neutral_col is None or bearish_col is None:
        if len(df.columns) >= 4:
            date_col = date_col or df.columns[0]
            bullish_col = bullish_col or df.columns[1]
            neutral_col = neutral_col or df.columns[2]
            bearish_col = bearish_col or df.columns[3]
        else:
            raise ValueError(f"Cannot detect AAII sentiment columns. columns={list(df.columns)}")

    if date_col is None:
        raise ValueError(f"Cannot detect AAII date column. columns={list(df.columns)}")

    out = pd.DataFrame()
    out["def_date"] = pd.to_datetime(df[date_col], errors="coerce")
    out["def_bullish"] = def_normalize_percent_column(df[bullish_col])
    out["def_neutral"] = def_normalize_percent_column(df[neutral_col])
    out["def_bearish"] = def_normalize_percent_column(df[bearish_col])

    out = out.dropna(subset=["def_date"])
    out = out.sort_values("def_date").drop_duplicates(subset=["def_date"], keep="last")
    out["def_provider"] = "aaii"
    out["def_indicator_id"] = "AAII_SENTIMENT"
    out["def_indicator_name_zh"] = "AAII 投資人情緒調查"
    out["def_category_lv1"] = "Sentiment"
    out["def_category_lv2"] = "AAII"
    out["def_frequency"] = "W"
    out["def_unit"] = "percent"

    return out


def def_fetch_aaii_from_local_csv(local_csv: str) -> pd.DataFrame:
    path = Path(local_csv)
    if not path.exists():
        raise FileNotFoundError(f"AAII local CSV not found: {local_csv}")

    raw = pd.read_csv(path, encoding="utf-8-sig")
    return def_clean_aaii_dataframe(raw)


def def_fetch_aaii_from_html(url: str, timeout: int = 30) -> pd.DataFrame:
    headers = {
        "User-Agent": "Mozilla/5.0 VDF-SentimentStrength/1.0"
    }

    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    tables = pd.read_html(io.StringIO(resp.text))

    errors = []
    for table in tables:
        try:
            cleaned = def_clean_aaii_dataframe(table)
            if not cleaned.empty and len(cleaned) >= 10:
                return cleaned
        except Exception as exc:
            errors.append(str(exc))

    raise ValueError(f"No usable AAII table found. errors={errors[:5]}")


def def_fetch_aaii_sentiment(task: dict) -> pd.DataFrame:
    local_csv = task.get("local_csv", "")
    url = task.get("url", "https://www.aaii.com/sentimentsurvey/sent_results")
    timeout = int(task.get("timeout", 30))

    errors = []

    if local_csv:
        try:
            df = def_fetch_aaii_from_local_csv(local_csv)
            return def_calc_aaii_strength(df)
        except Exception as exc:
            errors.append(f"local_csv failed: {exc}")

    try:
        df = def_fetch_aaii_from_html(url=url, timeout=timeout)
        return def_calc_aaii_strength(df)
    except Exception as exc:
        errors.append(f"html failed: {exc}")

    raise ValueError("AAII fetch failed. " + " | ".join(errors))
