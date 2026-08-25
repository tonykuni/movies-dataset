#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUP_MDL740_NetUnified_v0104 — 統包唯一網路工具 · 代理環境 TLS 自適應版
====================================================================
批136 操作員再擷取令(2026-08-25:「fetch vdf data again」)。
  ① 正典基底 — 動態載入 v0103 全能力(AegisNexus 後端/六車道/
     法遵雙閘 fail-closed)原樣再輸出;只增不減,零改寫基底。
  ② yf_download 車道 TLS 自適應 — 受管代理環境(TLS 再終結)會
     重置 curl_cffi 瀏覽器擬真握手(curl 35 Recv failure),致
     yfinance 預設道回空。本版:先走 v0103 原道;回空/敗時改用
     無擬真 curl_cffi Session(瀏覽器 UA 標頭+代理 CA bundle)
     重試一次;原道有資料=零行為變更(非代理環境不受影響)。
  ③ 雙閘不動 — VIA_NET_CONSENT/VIA_SCRAPE_CONSENT fail-closed
     紅線原樣:閘閉=DENY 零外呼恆真;自適應道同樣過雙閘。
誠實探明存證(2026-08-25 遠端容器):TWSE/TPEX/FRED 直達 200;
Yahoo 對預設 UA 回 429、對瀏覽器 UA 回 200;擬真握手遭代理重置
(全主機皆然=代理端行為,非 Yahoo 端封鎖)。
用法:與 v0103 相同(via-net --status/--check/--fetch/--selftest)。
"""
from __future__ import annotations

import importlib.util as _ilu
import os as _os
import sys as _sys
from pathlib import Path as _Path

_HERE = _Path(__file__).resolve().parent
_BASE_HITS = [p for p in sorted(_HERE.glob("SUP_MDL740_NetUnified_v*.py"))
              if p.name < "SUP_MDL740_NetUnified_v0104.py"]
if not _BASE_HITS:
    raise ImportError("SUP_MDL740_NetUnified 正典基底缺(誠實 fail)")
_spec = _ilu.spec_from_file_location("SUP_MDL740_NetUnified_BASE", _BASE_HITS[-1])
_BASE = _ilu.module_from_spec(_spec)
_sys.modules["SUP_MDL740_NetUnified_BASE"] = _BASE
_spec.loader.exec_module(_BASE)
globals().update({_k: _v for _k, _v in vars(_BASE).items()
                  if not _k.startswith("__")})
BASE_CANONICAL = _BASE_HITS[-1].name

_BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _proxy_safe_session():
    """無擬真 curl_cffi Session(瀏覽器 UA+CA bundle);缺件回 None(誠實)"""
    try:
        from curl_cffi import requests as _cr
    except ImportError:
        return None
    ca = None
    for c in (_os.environ.get("REQUESTS_CA_BUNDLE"),
              _os.environ.get("CURL_CA_BUNDLE"),
              _os.environ.get("SSL_CERT_FILE"),
              "/root/.ccr/ca-bundle.crt"):
        if c and _Path(c).exists():
            ca = c
            break
    try:
        s = _cr.Session(verify=ca if ca else True)
        s.headers.update(_BROWSER_HEADERS)
        return s
    except Exception:
        return None


def _df_has_rows(df) -> bool:
    try:
        return df is not None and not df.dropna(how="all").empty
    except Exception:
        return False


def yf_download(tickers: list[str], period: str = "5d") -> dict:
    """車道④覆版:v0103 原道優先;空/敗→無擬真 session 自適應重試(雙閘先行)"""
    r = _BASE.yf_download(tickers, period=period)
    if r.get("state") == "OK" and _df_has_rows(r.get("data")):
        return r
    if r.get("state") in ("DENY", "SKIP"):
        return r  # 閘閉/套件缺=原判原樣(fail-closed 紅線)
    d = _BASE._deny_if_closed()
    if d:
        return d
    sess = _proxy_safe_session()
    if sess is None:
        return r
    try:
        import yfinance as yf
        df = yf.download(tickers, period=period, interval="1d", auto_adjust=False,
                         progress=False, threads=True, group_by="ticker",
                         session=sess)
        if _df_has_rows(df):
            return {"state": "OK", "data": df,
                    "note": "TLS 自適應道(無擬真 session;原道空/敗後重試)"}
        return r  # 自適應仍空=回傳原道誠實結果
    except Exception as exc:
        return {"state": "FAIL", "note": f"自適應道敗:{str(exc)[:120]}"}


if __name__ == "__main__":
    _sys.exit(_BASE.main())
