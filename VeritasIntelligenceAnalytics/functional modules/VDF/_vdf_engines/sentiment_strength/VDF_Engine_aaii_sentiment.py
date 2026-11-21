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


AAII_XLS_URL = "https://www.aaii.com/files/surveys/sentiment.xls"   # 操作員 2026-11-21 指定的官方檔


def def_parse_aaii_xls(data: bytes) -> pd.DataFrame:
    """AAII sentiment.xls:前幾列是標題 / 說明,表頭那一列含 Bullish / Neutral / Bearish;找到那一列當表頭再清理。"""
    raw = pd.read_excel(io.BytesIO(data), header=None)
    hdr = None
    for i in range(min(len(raw), 30)):
        cells = [str(x).strip().lower() for x in raw.iloc[i].tolist()]
        if any("bullish" in c for c in cells) and any("bearish" in c for c in cells):
            hdr = i
            break
    if hdr is None:
        raise ValueError("AAII xls:前 30 列找不到含 Bullish / Bearish 的表頭")
    body = raw.iloc[hdr + 1:].copy()
    body.columns = [str(x).strip() for x in raw.iloc[hdr].tolist()]
    body = body.loc[:, [c for c in body.columns if c and c.lower() != "nan"]]
    return def_clean_aaii_dataframe(body)


def def_fetch_aaii_from_local_xls(local_xls: str) -> pd.DataFrame:
    path = Path(local_xls)
    if not path.is_file():
        raise FileNotFoundError(f"AAII local xls not found: {local_xls}")
    return def_parse_aaii_xls(path.read_bytes())


def def_fetch_aaii_from_xls_url(url: str = AAII_XLS_URL, timeout: int = 60) -> pd.DataFrame:
    """經統包網路工具抓位元組(雙閘在工具內;不偽裝、不換道直連);被拒就照實報。"""
    net = _via_net()
    if net is None or not callable(getattr(net, "http_bytes", None)):
        raise RuntimeError("VIA 網路工具載不到(via_net_unified_v*.py)· 不換道直連")
    r = net.http_bytes(url, timeout=timeout)
    if r.get("state") != "OK" or not r.get("data"):
        raise RuntimeError(f"VIA 網路工具 {r.get('state')}: {str(r.get('note') or r.get('why') or r.get('error') or '')[:160]}"
                           "(網站拒絕時:用瀏覽器下載到 下載\\sentiment.xls 或給 local_xls)")
    return def_parse_aaii_xls(bytes(r["data"]))


def def_fetch_aaii_from_html(url: str, timeout: int = 30) -> pd.DataFrame:
    headers = {
        "User-Agent": "Mozilla/5.0 VDF-SentimentStrength/1.0"
    }

    del headers  # 出網一律走統包網路工具(雙閘在工具內;不換道直連,批115 / 2026-11-21 晨檢 A)
    net = _via_net()
    if net is None or not callable(getattr(net, "http_text", None)):
        raise RuntimeError("VIA 網路工具載不到(via_net_unified_v*.py)· 不換道直連")
    r = net.http_text(url, timeout=timeout)
    if r.get("state") != "OK" or not r.get("data"):
        raise RuntimeError(f"VIA 網路工具 {r.get('state')}: {str(r.get('why') or r.get('error') or '')[:160]}")

    tables = pd.read_html(io.StringIO(r["data"]))

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

    local_xls = task.get("local_xls") or str(Path.home() / "Downloads" / "sentiment.xls")
    if Path(local_xls).is_file():
        try:
            df = def_fetch_aaii_from_local_xls(local_xls)
            return def_calc_aaii_strength(df)
        except Exception as exc:
            errors.append(f"local_xls failed: {exc}")

    try:
        df = def_fetch_aaii_from_xls_url(url=task.get("xls_url", AAII_XLS_URL), timeout=max(timeout, 60))
        return def_calc_aaii_strength(df)
    except Exception as exc:
        errors.append(f"xls failed: {exc}")

    try:
        df = def_fetch_aaii_from_html(url=url, timeout=timeout)
        return def_calc_aaii_strength(df)
    except Exception as exc:
        errors.append(f"html failed: {exc}")

    raise ValueError("AAII fetch failed. " + " | ".join(errors))
