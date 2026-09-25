# -*- coding: utf-8 -*-
"""
def VDF_Engine_aaii_sentiment
AAII Sentiment Survey engine.
"""

from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

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
