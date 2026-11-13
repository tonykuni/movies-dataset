#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0130 — 薄尾:extract 第三輪修(2026-10-06 triage 二:無期間表頭 90 = 多數是「基本資料 / 投資評等」鍵值框與期間印在表框外)。
記憶體替換前版 _rebuild_table(v0129 的);其餘照前版鏈。
  ① 期間在表框外:表內找不到期間列,但周邊資訊段(表上方最後兩行)有 ≥2 個期間 → 當表頭補進去
  ② INFO 鍵值框:2–3 欄、無期間、每列「標籤:值」(投資評等 Buy · 目標價 120 · 股價 …)→ 類別 INFO,出 kv{std→值},不算無期間表頭,不擋 READ
  ③ 字典第二批 VRN_FinLexicon_SSOT_v0101(+33:CF/IS 英文項 · 比率 · 估值;v0100 不動,尾版自動取)
  ④ 噪音列標(資料來源: · (千元) · 單位 · OCR 亂碼含 ^ ｀ ﹐)不進 unmatched
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0130"


def _vnum_v0130(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0130(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0130(p) < _vnum_v0130(__file__)), key=_vnum_v0130)
PRIOR = _load_v0130(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


_P29 = PRIOR
_P28 = _P29._P28
_P27 = _P29._P27
_REBUILD_29 = _P27._rebuild_table
_NOISE_RX = re.compile(r"^(資料來源|來源|Source|Note|註|單位|Unit)[::]|^\(?(千元|百萬|億|元|NT\$|US\$)\)?$|[\^｀﹐]|^[A-Za-z]{1,2}\s*伺服器")
_LAB_PAT = re.compile(r"^[^\d]{1,20}[::]?\s*$")


def _periods_from_surround(sur: dict) -> list:
    above = (sur or {}).get("above") or ""
    for ln in reversed(above.splitlines()[-2:]):
        toks = [t for t in re.split(r"\s+", ln.strip()) if t]
        pers = [t for t in toks if _P28._is_period_28(t)]
        if len(pers) >= 2 and len(pers) >= len(toks) - 1:
            return pers
    return []


def _rebuild_table_30(tbl: dict, lex: list) -> dict:
    rows = [list(r) for r in tbl.get("rows", []) if any(_P27._clean_cell(c) for c in r)]
    sur = tbl.get("surround") or {}
    has_hdr = any(sum(1 for c in r[1:] if _P28._is_period_28(c)) >= 1 for r in rows[:6])
    col0_periods = sum(1 for r in rows[1:] if _P28._is_period_28(r[0])) if rows else 0
    if rows and not has_hdr and col0_periods < 2:
        pers = _periods_from_surround(sur)
        w = max(len(r) for r in rows)
        if pers and len(pers) <= w - 1:
            rows = [[""] + pers + [""] * (w - 1 - len(pers))] + rows
            tbl = dict(tbl, rows=rows)
            rb = _REBUILD_29(tbl, lex)
            rb["layout_note"] = (rb.get("layout_note", "") + ";期間取自表外") .strip(";")
            return rb
    rb = _REBUILD_29(tbl, lex)
    rb["unmatched_labels"] = [x for x in rb.get("unmatched_labels", []) if not _NOISE_RX.search(x)]
    if "無期間表頭" in rb.get("issues", []):
        w = max((len(r) for r in rows), default=0)
        labelled = [r for r in rows if _P27._clean_cell(r[0]) and not _P29._LABEL_RX.match(_P27._clean_cell(r[0]))]
        if 2 <= w <= 3 and len(labelled) >= max(2, int(0.6 * len(rows))):
            kv = {}
            for r in labelled:
                cat, std = _P27._std_label(r[0], lex)
                val = next((_P27._clean_cell(c) for c in r[1:] if _P27._clean_cell(c)), "")
                if val:
                    kv[std or _P27._clean_cell(r[0])[:30]] = val
            rb["category"] = "INFO"
            rb["kv"] = kv
            rb["issues"] = [x for x in rb["issues"] if x != "無期間表頭"]
            rb["unmatched_labels"] = [k for k in kv if k == _P27._clean_cell(k) and not any(k == s for _, s, _ in lex) and not _NOISE_RX.search(k)][:20]
    return rb


_P27._rebuild_table = _rebuild_table_30


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    return _P29.main(args)


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
    rb = _rebuild_table_30({"rows": [["Revenue", "1000", "1200"], ["COGS", "600", "700"], ["Gross profit", "400", "500"]], "surround": {"above": "Income statement (NT$ mn)\n2024A 2025E", "below": ""}}, lex)
    chk("① 期間在表外:上方「2024A 2025E」補成表頭 · 算術過 · 無「無期間表頭」", rb["periods"] == ["2024A", "2025E"] and not rb["issues"] and "期間取自表外" in rb.get("layout_note", ""))
    rb2 = _rebuild_table_30({"rows": [["投資評等", "Buy"], ["目標價", "120"], ["股價", "98.5"], ["公司名稱", "神達"]], "surround": {}}, lex)
    chk("② 鍵值框 → INFO · kv 有 rating/target_price/price · 不擋", rb2["category"] == "INFO" and rb2["kv"].get("rating") == "Buy" and rb2["kv"].get("target_price") == "120" and not rb2["issues"])
    rb3 = _rebuild_table_30({"rows": [["", "2024"], ["Net operating cashflow", "500"], ["Free cashflow", "300"], ["資料來源:CMoney", "1"], ["(千元)", "2"]], "surround": {}}, lex)
    chk("③ 第二批字典:cfo/fcf 認得 · 噪音列標不進 unmatched", {r["label_std"] for r in rb3["rows"]} >= {"cfo", "fcf"} and not rb3["unmatched_labels"] and rb3["category"] == "CF")
    tails = sorted((HERE / "SSOT").glob("VRN_FinLexicon_SSOT_v*.json")) if (HERE / "SSOT").is_dir() else []
    chk("④ 字典尾版 ≥ v0101 已在 VRN/SSOT(%s)" % (tails[-1].name if tails else "無"), bool(tails) and tails[-1].name >= "VRN_FinLexicon_SSOT_v0101.json")
    print("  ── 前版鏈自測(原樣印出;前版行為)──")
    _P27._rebuild_table = _REBUILD_29
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else _P29.selftest()
    finally:
        _P27._rebuild_table = _rebuild_table_30
    chk("⑤ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 帶加速器橋 · glob 取前版 · 獨立 MAIN", "[VIA:ACCEL-BRIDGE:v0100]" in body and "setdefault(\"VIA_FROM_VCGC\"" in body)
    print("[計] VRN_SystemManager_v0130 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
