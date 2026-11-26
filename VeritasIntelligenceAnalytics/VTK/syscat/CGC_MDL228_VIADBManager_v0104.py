#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL228_VIADBManager v0104 — 薄尾:庫表冊讀最新一版(VIA_DB_Table_SSOT_v*.json)

v0102 把冊釘在 VIA_DB_Table_SSOT_v0100.json(PINVER);v0100 又被 VIA_ShutdownRecord 釘住 blob、不能改。
R17-3 補冊(aaii_sentiment · vdf_hub 兩表 · vrn_report_* 兩表)只能落在新的一版 v0101 —— 本尾版讓面板的「冊上期望」讀最新一版。
其餘全照 v0103 / v0102(L04 舊版一字不動;L05 冊就是那一本,只是版號跟尾)。
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

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL228_VIADBManager"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl228_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def newest_book() -> Path:
    hits = [p for p in HERE.glob("VIA_DB_Table_SSOT_v*.json") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else BASE.TABLE_BOOK


_BASE_BOOK = BASE._book


def _book(path: Path | None = None) -> list:
    return _BASE_BOOK(path or newest_book())


BASE._book = _book               # v0102 的核對 / 面板一律讀最新冊
BASE.TABLE_BOOK = newest_book()


def __getattr__(name):
    return getattr(PRIOR, name)


def selftest() -> int:
    rc = PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    print("=== CGC_MDL228 v0104 薄尾加檢(庫表冊跟尾)===")
    nb = newest_book()
    chk("⓪ 冊取最新一版", nb.name == max((p.name for p in HERE.glob("VIA_DB_Table_SSOT_v*.json"))), nb.name)
    rows = {(t.get("db"), t.get("table")) for t in _book()}
    want = {("aaii_sentiment.duckdb", "aaii_sentiment"), ("vdf_hub.duckdb", "digest_vdf_rows"), ("vdf_hub.duckdb", "vdf_sample_rows"),
            ("vdf_tw_market.duckdb", "vrn_report_arith_check"), ("vdf_tw_market.duckdb", "vrn_report_official_check")}
    chk("⓪ R17-3 五張表在冊上", want <= rows, str(sorted(want - rows)) if not want <= rows else "5/5")
    old = json.loads((HERE / "VIA_DB_Table_SSOT_v0100.json").read_text(encoding="utf-8"))
    chk("⓪ v0100 冊原樣(ShutdownRecord 釘它的 blob)", not ({(t['db'], t['table']) for t in old['tables']} & want))
    ok = rc == 0 and all(results)
    print(f"  [計] v0104 薄尾 {sum(results)}/{len(results)} · v0103 本體 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
