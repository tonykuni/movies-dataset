#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL183_CeleritasPolicyGate v0102 — 薄尾:讀「已還債帳」,棘輪只緊不鬆

R16-9(操作員 2026-09-28「加速器導入所有 py 檔 ps 檔 · 覆蓋率要達 100% · 授權進行一切」)以剖析器替既有債 .ps1
接上模板章(790 支;BACKUP 3 支後來還原)。v0101 的自測 ④ 把「既有債 = 基線清單長度」當不變量 —— 設計時假設 L70 下債永遠不會還,債一還就假紅。
基線資料檔 VIA_CeleritasPolicy_Baseline_v0100.json **不改**;另立一本只增的帳 VIA_CeleritasPolicy_PaidDebt_v0100.json
(已還的 790 支)。本尾版只換一件事:v0101 的 baseline() 回「基線 − 已還」作為有效既有債。結果:

  · 有效既有債 = 53(每支都有具名理由:雜湊被冊登錄 / 凍結鎖 / intake 正本 / 原檔本身剖析不過 / 封存備份副本)
  · 已還的任何一支掉章 → 不在有效既有債裡 → v0101 scan() 自然把它算成「基線外新缺」= RED(比單純放寬 ④ 更緊)
  · 其餘判準、排除清單、PS 稽核委派引擎、唯讀零網路 —— 全照 v0101(L05 不立第二把尺,L04 舊版一字不動)
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

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL183_CeleritasPolicyGate"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl183_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

PAID = HERE / "VIA_CeleritasPolicy_PaidDebt_v0100.json"
VERSION = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
_BASE_BASELINE = PRIOR.baseline
_paid_override: list | None = None       # 只給自測沙盒用


def __getattr__(name):
    return getattr(PRIOR, name)


def paid() -> list:
    """已還債帳(只增的另一本);讀不到 = 空(照 v0101 行為,不假裝已還)。"""
    if _paid_override is not None:
        return list(_paid_override)
    try:
        return list(json.loads(PAID.read_text(encoding="utf-8")).get("files") or [])
    except Exception:
        return []


def baseline() -> dict:
    """基線 − 已還 = 有效既有債。基線資料檔本身一個字都不改。"""
    b = copy.deepcopy(_BASE_BASELINE())
    done = set(paid())
    debt = b.get("ps1_debt") or {}
    if done and debt.get("files"):
        debt["files_in_book"] = len(debt["files"])
        debt["files"] = [f for f in debt["files"] if f not in done]
        debt["paid"] = len(done)
    return b


PRIOR.baseline = baseline        # v0101 的 scan / report / selftest 都改讀有效既有債
scan = PRIOR.scan
report = PRIOR.report
PS_MARK = PRIOR.PS_MARK


def selftest() -> int:
    global _paid_override
    rc = PRIOR.selftest()        # v0101 八檢原樣跑(④ 此時比對的是有效既有債)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")

    print(f"=== {_STEM} {VERSION} 薄尾加檢(已還債帳)===")
    book = _BASE_BASELINE()
    in_book = set((book.get("ps1_debt") or {}).get("files") or [])
    done = paid()
    chk("⑨ 已還債帳 ⊆ 基線(帳上每一支都是真的既有債,不能拿新檔來充數)", set(done) <= in_book and len(done) > 0, f"已還 {len(done)} · 基線 {len(in_book)}")
    unmarked = [p for p in done if (PRIOR.VIA / p).is_file() and PS_MARK not in (PRIOR.VIA / p).read_text(encoding="utf-8", errors="ignore")]
    chk("⑩ 已還的每一支現在都帶模板章", not unmarked, f"掉章 {unmarked[:3] or '無'}")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "x").mkdir()
        (root / "x" / "paid.ps1").write_text("Write-Host 1\n", encoding="utf-8")
        (root / "x" / "debt.ps1").write_text("Write-Host 2\n", encoding="utf-8")
        real = _BASE_BASELINE
        try:
            PRIOR_base = {"ps1_debt": {"files": ["x/paid.ps1", "x/debt.ps1"]}}
            globals()["_BASE_BASELINE"] = lambda: copy.deepcopy(PRIOR_base)
            _paid_override = ["x/paid.ps1"]
            s = PRIOR.scan(root)
        finally:
            globals()["_BASE_BASELINE"] = real
            _paid_override = None
        ps = s.get("ps") or {}
        chk("⑪ 棘輪只緊:已還的一支掉章 = 基線外新缺 RED;沒還的照算既有債",
            s.get("state") != "NODATA" and "x/paid.ps1" in (ps.get("new_missing") or []) and ps.get("debt") == 1,
            f"新缺 {ps.get('new_missing')} · 既有債 {ps.get('debt')}")
    b2 = json.loads(PRIOR.BASELINE.read_text(encoding="utf-8"))
    chk("⑫ 基線資料檔沒被改(另一本帳只增)", len((b2.get("ps1_debt") or {}).get("files") or []) == len(in_book))
    ok = rc == 0 and all(results)
    print(f"  [計] {VERSION} 薄尾 {sum(results)}/{len(results)} · v0101 八檢 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    print(f"=== Celeritas 產出契約閘 {VERSION}(薄尾 · 已還債帳 {len(paid())} 支 · 執法 L102)===")
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
