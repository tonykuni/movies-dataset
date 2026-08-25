#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
proxy_session_driver — 批136 再擷取驅動器(2026-08-25)
====================================================================
批136 操作員再擷取令:「fetch vdf data again」。前次資料擷取=
RUN_20260617_001157(VDF_ManifestFetchAdapter 同件);本次於受管遠端
容器重跑同一轉接器、同一正典清單(VIA_data_manifest.json,
supportive modules/registry 正本 md5 同一)。
轉接器零改寫(byte-identical 快照);環境差異僅以本驅動器補橋:
  ① 代理 TLS 自適應 — 容器出網經 TLS 再終結代理,curl_cffi 瀏覽
     器擬真握手遭重置致 yfinance 預設道回空;本驅動器向統包網路
     工具(SUP_MDL740 glob 最新,v0104 起)取無擬真 session(瀏覽
     器 UA+代理 CA bundle),以 yfinance.download keyword 注入。
  ② 同意閘先行 — VIA_NET_CONSENT≠YES 即 rc2 fail-closed 零外呼
     (鐵律:閘永不代設;本次由操作員再擷取令開閘)。
  ③ FRED — 無 FRED_API_KEY 時轉接器自身 fredgraph.csv 後備道
     (直達 200 已探明);零改寫。
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _net_tool():
    """統包網路工具(supportive modules/network glob 最新 SUP_MDL740)"""
    p = HERE
    while p.parent != p:
        nd = p / "supportive modules" / "network"
        if nd.exists():
            hits = sorted(nd.glob("SUP_MDL740_NetUnified_v*.py"))
            if hits:
                return _load("SUP_MDL740_NetUnified_DRV", hits[-1])
            break
        p = p.parent
    return None


def main() -> int:
    if os.environ.get("VIA_NET_CONSENT", "") != "YES":
        print("[FAIL-CLOSED] VIA_NET_CONSENT≠YES:同意閘未開,零外呼(絕不代設)")
        return 2

    net = _net_tool()
    sess = net._proxy_safe_session() if net and hasattr(net, "_proxy_safe_session") else None
    if sess is not None:
        import yfinance as yf
        _orig_download = yf.download

        def _download_with_session(*args, **kwargs):
            kwargs.setdefault("session", sess)
            return _orig_download(*args, **kwargs)

        yf.download = _download_with_session
        print(f"[OK] yfinance session 注入(統包 {Path(net.__file__).name};無擬真+瀏覽器 UA)")
    else:
        print("[WARN] 統包 _proxy_safe_session 缺席:yfinance 走預設道(誠實)")

    adapter = _load("VDF_ManifestFetchAdapter_DRV", HERE / "VDF_ManifestFetchAdapter.py")
    sys.argv = [
        "VDF_ManifestFetchAdapter.py",
        "--mode", "fetch",
        "--manifest", str(HERE / "VIA_data_manifest.json"),
        "--outdir", str(HERE / "outputs"),
        "--start-policy", "ALL",
    ]
    return adapter.def_main()


if __name__ == "__main__":
    sys.exit(main())
