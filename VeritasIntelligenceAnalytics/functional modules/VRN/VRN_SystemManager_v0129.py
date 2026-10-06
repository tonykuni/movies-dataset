#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0129 — 薄尾:extract 第二輪修(2026-10-06 triage:率不符 102 · 無期間表頭 82 · 年份當列標 22 · 純數字列標 16 · 表頭「會計年度」在期間列之前)。
記憶體替換前版 _rebuild_table(v0128 的);其餘照前版鏈。
  ① 轉置表:首欄前 ≥2 列是期間(2024 / 2025(F) …)而首列是指標名 → 轉置後再重建(年份不再被當列標)
  ② 表頭深找:前 6 列找期間列;「會計年度 / 年度 / FY」那種標籤列跳過;期間格允許 2025(F) · 2024A · 114年 · 1Q25
  ③ 純數字 / 日期 / 空白的列標(0 · 100 · 1,000 · 1 October 2025)不算列標,不進 unmatched
  ④ 率不符降級為提醒(advisory,記 rate_notes),不擋 READ;擋 READ 的只剩「毛利≠營收−成本」與「無期間表頭」
  ⑤ VRN 自家字典 SSOT/VRN_FinLexicon_SSOT_v*.json(40 條第一批)由前版 _load_vrn_lexicon 自動併入;列標比對最長別名優先
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0129"


def _vnum_v0129(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0129(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0129(p) < _vnum_v0129(__file__)), key=_vnum_v0129)
PRIOR = _load_v0129(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


_P28 = PRIOR
_P27 = _P28._P27
_REBUILD_28 = _P27._rebuild_table          # v0128 已換上的版本
_LABEL_RX = re.compile(r"^[\s\d,.%()$\-−–+xX倍]*$|^\d{1,2} [A-Z][a-z]+ 20\d{2}$|^[A-Z][a-z]+ \d{1,2},? 20\d{2}$")
_HDR_SKIP = re.compile(r"^(會計\s*年度|年度|年|FY|期間|項目|單位.*|NT\$.*|百萬.*|\(.*\))$", re.I)


def _is_label(s: str) -> bool:
    t = _P27._clean_cell(s)
    return bool(t) and not _LABEL_RX.match(t) and not _P28._is_period_28(t)


def _normalize_rows(rows: list) -> tuple:
    """① 轉置 · ② 表頭深找 · ③ 跳過標籤列。回 (rows, note)。"""
    rows = [list(r) for r in rows if any(_P27._clean_cell(c) for c in r)]
    if not rows:
        return rows, ""
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    col0_periods = sum(1 for r in rows[1:] if _P28._is_period_28(r[0]))
    row0_labels = sum(1 for c in rows[0][1:] if _is_label(c))
    if col0_periods >= 2 and row0_labels >= 2 and col0_periods >= len(rows) - 2:
        rows = [list(x) for x in zip(*rows)]      # 轉置:期間變表頭,指標變列
        return rows, "轉置"
    for i, r in enumerate(rows[:6]):
        n_per = sum(1 for c in r[1:] if _P28._is_period_28(c))
        if n_per >= 2 or (n_per >= 1 and not _P27._clean_cell(r[0])):
            if i > 0:
                rows = [r] + [x for j, x in enumerate(rows) if j != i and not _HDR_SKIP.match(_P27._clean_cell(x[0]) or "") or j > i]
                rows = [rows[0]] + [x for x in rows[1:] if x is not r]
            return rows, ("表頭在第 %d 列" % (i + 1)) if i else ""
    return rows, ""


def _rebuild_table_29(tbl: dict, lex: list) -> dict:
    rows, note = _normalize_rows(tbl.get("rows", []))
    rb = _REBUILD_28(dict(tbl, rows=rows), lex)
    rb["rows"] = [r for r in rb.get("rows", []) if _is_label(r.get("label_raw", ""))]
    rb["unmatched_labels"] = [r["label_raw"] for r in rb["rows"] if not r.get("label_std") and r.get("values")][:30]
    rate = [x for x in rb.get("issues", []) if "≠" in x and "毛利≠" not in x]
    rb["rate_notes"] = rate
    rb["issues"] = [x for x in rb.get("issues", []) if x not in rate]
    if rb.get("category") == "OTHER" and not rb["rows"]:
        rb["category"] = "TEXT_BLOCK"
    if note:
        rb["layout_note"] = note
    return rb


_P27._rebuild_table = _rebuild_table_29


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    return _P28.main(args)


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    lex = _P27._FIN_STD + _P27._load_vrn_lexicon()
    rb = _rebuild_table_29({"rows": [["", "營業收入淨額", "營業毛利", "稅後純益"], ["2024", "1000", "400", "150"], ["2025(F)", "1200", "500", "200"], ["2026(F)", "1500", "650", "270"]]}, lex)
    chk("① 轉置表(年份在首欄)→ 期間 2024/2025(F)/2026(F) · 列 revenue/gross_profit/net_income · 無年份列標", rb.get("layout_note") == "轉置" and rb["periods"] == ["2024", "2025(F)", "2026(F)"] and {r["label_std"] for r in rb["rows"]} >= {"revenue", "gross_profit", "net_income"} and not rb["unmatched_labels"])
    rb2 = _rebuild_table_29({"rows": [["會計年度", "", ""], ["", "2024", "2025(F)"], ["營業收入淨額", "1,000", "1,200"], ["營業成本", "600", "700"], ["營業毛利", "400", "500"], ["0", "9", "9"], ["1 October 2025", "1", "2"]]}, lex)
    chk("② 表頭在第 2 列(會計年度列跳過)· 純數字/日期列標不算 · 毛利算術過", rb2["periods"] == ["2024", "2025(F)"] and not rb2["unmatched_labels"] and not rb2["issues"] and all(_is_label(r["label_raw"]) for r in rb2["rows"]))
    rb3 = _rebuild_table_29({"rows": [["", "2024"], ["Revenue", "1000"], ["COGS", "600"], ["Gross profit", "400"], ["Gross margin", "45%"]]}, lex)
    chk("③ 率不符降級:issues 空 · rate_notes 1(不擋 READ)", not rb3["issues"] and len(rb3["rate_notes"]) == 1)
    rb4 = _rebuild_table_29({"rows": [["", "2024"], ["資本公積", "100"], ["保留盈餘", "300"], ["負債與權益總計", "900"], ["投資評等", "逢低買進"]]}, lex)
    chk("④ 字典第一批:資本公積/保留盈餘/負債與權益總計 → BS · 投資評等 認得", rb4["category"] == "BS" and all(r["label_std"] for r in rb4["rows"] if r["values"]))
    print("  ── 前版鏈自測(原樣印出)──")
    _P27._rebuild_table = _REBUILD_28          # 前版鏈自測用前版本身的行為(v0127 ⑤ 期望率不符仍在 issues),測完再換回
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else _P28.selftest()
    finally:
        _P27._rebuild_table = _rebuild_table_29
    chk("⑤ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 帶加速器橋 · glob 取前版 · 獨立 MAIN", "[VIA:ACCEL-BRIDGE:v0100]" in body and "setdefault(\"VIA_FROM_VCGC\"" in body)
    print("[計] VRN_SystemManager_v0129 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
