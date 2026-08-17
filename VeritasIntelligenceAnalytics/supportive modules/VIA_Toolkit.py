#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_Toolkit — Top-10 本機免費工具統一導入層(TOOL-040;操作員令 2026-08-17)
============================================================================
令:Top-10 工具整合強化 VIA Integration & System Manager;透過支援工具
導入 libs,於 via_core/via_* 環境導入。本模組=統一 graceful 出入口:
  ① 零硬依賴 — 每件工具缺席回 None,引擎行為零改變(graceful 鐵則)
  ② 統一探測 — availability()/report() 供 sysman/plan/hub 一源共用
  ③ 安裝一律經 via-install 閘(儲存規定);本模組永不代裝
十件與用途(對應 SPEC-015 Pipeline/加速器):
  libcst(P1/A01/A06 保格式重構)· pydantic(P2/T2 契約驗證)·
  networkx(P3/A03/A04/A15 依賴 DAG)· pytest(P5/A14 測試基座)·
  hypothesis(T2/T4/T5 邊界生成)· ruff(P1/P4 高速 lint)·
  bandit(A03/S04 安全 AST)· psutil(P4/A11/A18 資源監控)·
  duckdb(T3/T4/R06 資料品質查核)· polars(VDF/P4 高速資料管線)
介面:
  get(name)          → module|None(快取;缺席 None)
  availability()     → {name: version|None}(importlib.metadata,零 import)
  report()           → 印四批次矩陣+經閘安裝令(誠實)
"""
from __future__ import annotations

import importlib
import importlib.util

TOOLS = {  # name → (批次, 用途)
    "libcst":     ("靜態治理", "保留格式的精準 Python 重構(P1/A01/A06)"),
    "networkx":   ("靜態治理", "依賴 DAG/循環偵測/拓撲排序(P3/A03/A04/A15)"),
    "ruff":       ("靜態治理", "高速 lint/import/死碼(P1/P4)"),
    "bandit":     ("靜態治理", "AST 安全掃描(A03/S04)"),
    "pydantic":   ("契約測試", "Manifest/Evidence/參數契約驗證(P2/T2)"),
    "pytest":     ("契約測試", "單元/整合/回歸測試基座(P5/A14)"),
    "hypothesis": ("契約測試", "Null/Empty/Boolean/OHLC 邊界案例生成(T2/T4/T5)"),
    "duckdb":     ("真實資料", "Parquet/CSV 查核/重複鍵/Row Context(T3/T4/R06)"),
    "polars":     ("真實資料", "LazyFrame 增量管線/低記憶體(VDF/P4)"),
    "psutil":     ("Runtime 監控", "CPU/Memory/Process/Heartbeat/洩漏(P4/A11/A18)"),
}
BATCH_ORDER = ["靜態治理", "契約測試", "真實資料", "Runtime 監控"]
_cache: dict[str, object | None] = {}


def get(name: str):
    """統一 graceful 取件:缺席 None(引擎零硬依賴)。"""
    if name not in _cache:
        try:
            _cache[name] = importlib.import_module(name)
        except Exception:
            _cache[name] = None
    return _cache[name]


def availability() -> dict[str, str | None]:
    out = {}
    for name in TOOLS:
        if importlib.util.find_spec(name) is None:
            out[name] = None
        else:
            try:
                from importlib.metadata import version
                out[name] = version(name)
            except Exception:
                out[name] = "?"
    return out


def report() -> int:
    av = availability()
    n_in = sum(1 for v in av.values() if v)
    print(f"=== VIA_Toolkit · Top-10 統一導入層 · 可用 {n_in}/10 ===")
    for batch in BATCH_ORDER:
        names = [n for n, (b, _u) in TOOLS.items() if b == batch]
        missing = [n for n in names if not av[n]]
        print(f"  ── {batch} ──")
        for n in names:
            mark = f"OK {av[n]}" if av[n] else "缺"
            print(f"     [{mark:12s}] {n:11s} · {TOOLS[n][1]}")
        if missing:
            print(f"     [裝令] via-install {' '.join(missing)}(經閘;先 via-plan 實測)")
    print("  [鐵則] graceful 全退化;安裝一律 via-install 閘;先計畫先實測(via-plan)")
    return 0 if n_in == 10 else 1


if __name__ == "__main__":
    import sys
    sys.exit(report())
