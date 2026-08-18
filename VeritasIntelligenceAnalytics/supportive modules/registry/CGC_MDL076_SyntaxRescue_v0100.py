#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_syntax_rescue_v0100 — 語法敗三輪沙盒救援引擎(TOOL-064)
====================================================================
操作員令(批23 Mega-Prompt 再頒):對全景掃描識別之語法敗件,
在 Zero-Hydra 前提下三輪修復——并行可修一口氣修,順序依賴逐步修,
高風險只建議。

安全設計(紅線):
  · 原件零觸碰——修復產出為提案檔 <stem>_syntaxfix_v0100.py,
    與原件並排;採用與否走 via-intake 讓位裁決(操作員審)。
  · 每輪修復後 ast.parse 沙盒閘;三輪未過=誠實 FAIL+建議,不硬修。
  · 只做機械可證變換(圍欄剝離/引號正規化/f-string 反斜線吊升/
    Tab 縮排/BOM·NUL 清理);語意級破損不猜,出建議。

三輪協議(每檔,錯誤導向):
  R1 并行安全變換:BOM/NUL 清理+markdown 圍欄剝離+智慧引號/全形
     標點正規化(僅限錯誤行鄰域,不全檔盲改)。
  R2 順序錯誤導向:依 ast 回報錯類施修——
     · f-string backslash → 反斜線字面量吊升為前置變數
     · TabError/inconsistent tabs → Tab→4 空格
     · invalid character(全形)→ 錯誤行字元正規化
  R3 收尾:重驗+報告;仍敗=ADVICE(截斷/語意破損候人工)。

用法:
  --scan             全倉掃描語法敗清單(同治理台 SKIP 規則)
  --repair           對掃描所得全數生成修復提案(沙盒閘)
  --repair-one <檔>  單檔救援
  --selftest         七檢
"""
from __future__ import annotations

import ast
import json
import re
import sys
import warnings
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RUNS = VIA / "VIA_Reports" / "syntaxrescue_runs"
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")
SKIP_FRAGS = ("_sha", "_review_quarantine", "__pycache__", "/vendor/",
              "package_samples", "/docs/", "quarantine", "_syntaxfix_")

SMART_MAP = {"“": '"', "”": '"', "‘": "'", "’": "'",
             "，": ",", "：": ":", "（": "(", "）": ")",
             "、": ",", "　": " "}


def _parse_err(text: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            ast.parse(text)
            return None
        except SyntaxError as e:
            return e


def t_clean_binary(text: str) -> str:
    return text.replace("\ufeff", "").replace("\x00", "")


def t_strip_fences(text: str) -> str:
    lines = text.split("\n")
    out = [ln for ln in lines if not re.match(r"^\s*```", ln)]
    return "\n".join(out) if len(out) != len(lines) else text


def t_smart_quotes_line(text: str, lineno: int) -> str:
    """僅錯誤行±1 正規化智慧引號/全形標點(不全檔盲改)。"""
    lines = text.split("\n")
    for i in range(max(0, lineno - 2), min(len(lines), lineno + 1)):
        for k, v in SMART_MAP.items():
            lines[i] = lines[i].replace(k, v)
    return "\n".join(lines)


def t_tabs(text: str) -> str:
    return text.replace("\t", "    ")


def t_fstring_backslash(text: str, lineno: int) -> str:
    """f-string 內反斜線字面量吊升:錯誤行內 {…r"…\…"…} → 前置變數。"""
    lines = text.split("\n")
    if lineno - 1 >= len(lines):
        return text
    ln = lines[lineno - 1]
    lits = re.findall(r'r?"[^"]*\\[^"]*"|r?\'[^\']*\\[^\']*\'', ln)
    if not lits:
        return text
    indent = re.match(r"\s*", ln).group(0)
    pre = []
    for j, lit in enumerate(dict.fromkeys(lits)):
        var = f"_rxfix_{lineno}_{j}"
        pre.append(f"{indent}{var} = {lit}")
        ln = ln.replace(lit, var)
    lines[lineno - 1] = ln
    lines[lineno - 1:lineno] = pre + [lines[lineno - 1]]
    return "\n".join(lines)


def rescue_text(text: str, max_rounds: int = 3):
    """三輪錯誤導向救援。回 (fixed_text|None, rounds, applied, last_err)。"""
    applied = []
    cur = text
    for rnd in range(1, max_rounds + 1):
        err = _parse_err(cur)
        if err is None:
            return cur, rnd - 1, applied, None
        msg = (err.msg or "").lower()
        before = cur
        if rnd == 1:  # R1 并行安全
            cur = t_strip_fences(t_clean_binary(cur))
            if cur != before:
                applied.append("R1:fence/bom")
                continue
        if "backslash" in msg and "f-string" in msg:
            cur = t_fstring_backslash(cur, err.lineno or 1)
            tag = "R2:fstring-backslash"
        elif "tab" in msg or "inconsistent" in msg:
            cur = t_tabs(cur)
            tag = "R2:tabs"
        elif "invalid character" in msg or "invalid syntax" in msg:
            cur = t_smart_quotes_line(cur, err.lineno or 1)
            tag = "R2:smart-quotes"
        else:
            return None, rnd, applied, f"{err.msg} @L{err.lineno}(語意級,候人工)"
        if cur == before:
            return None, rnd, applied, f"{err.msg} @L{err.lineno}(變換無效,候人工)"
        applied.append(tag)
    err = _parse_err(cur)
    if err is None:
        return cur, max_rounds, applied, None
    return None, max_rounds, applied, f"{err.msg} @L{err.lineno}(三輪未收斂,誠實 FAIL)"


def iter_bad():
    for p in VIA.rglob("*.py"):
        rp = str(p.relative_to(VIA)).replace("\\", "/")
        if any(f in rp for f in SKIP_FRAGS):
            continue
        try:
            if _parse_err(p.read_text(encoding="utf-8", errors="ignore")):
                yield p, rp
        except Exception:
            continue


def cmd_scan() -> int:
    bad = list(iter_bad())
    print(f"  [掃] 語法敗 {len(bad)} 件(原件零觸碰;--repair 生成提案)")
    for _, rp in bad:
        print(f"    {rp}")
    return 0


def repair_one(p: Path, rp: str) -> dict:
    text = p.read_text(encoding="utf-8", errors="ignore")
    fixed, rounds, applied, last = rescue_text(text)
    rec = {"path": rp, "rounds": rounds, "applied": applied}
    if fixed is not None:
        prop = p.with_name(p.stem + "_syntaxfix_v0100.py")
        prop.write_text(fixed, encoding="utf-8")
        rec.update({"status": "PROPOSED", "proposal": prop.name})
        print(f"  [修] {rp} · {rounds} 輪 · {'+'.join(applied) or '零變換'} → 提案 {prop.name}(原件不動)")
    else:
        rec.update({"status": "ADVICE", "advice": last})
        print(f"  [議] {rp} · {last}")
    return rec


def cmd_repair(target: str | None = None) -> int:
    RUNS.mkdir(parents=True, exist_ok=True)
    recs = []
    if target:
        p = Path(target)
        if not p.is_absolute():
            p = VIA / target
        if not p.exists():
            print(f"  [FAIL] 檔不存在:{target}")
            return 2
        recs.append(repair_one(p, str(p)))
    else:
        for p, rp in iter_bad():
            recs.append(repair_one(p, rp))
    n_ok = sum(1 for r in recs if r["status"] == "PROPOSED")
    ev = RUNS / f"SYNTAXRESCUE_{NOW}.json"
    ev.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] 提案 {n_ok} · 候人工 {len(recs) - n_ok} · 存證 {ev.name}")
    print("  [紅線] 提案採用走 via-intake 讓位裁決;原件與提案並存零刪除")
    return 0


def selftest() -> int:
    ok, total = 0, 7
    # 1 圍欄剝離
    f1 = "```python\nx = 1\n```\n"
    r, _, a, _ = rescue_text(f1)
    if r is not None and "R1:fence/bom" in a and _parse_err(r) is None:
        ok += 1; print("  [PASS] R1 圍欄/BOM 剝離")
    else:
        print("  [FAIL] 圍欄")
    # 2 f-string 反斜線吊升
    f2 = 'v = source["T"].str.fullmatch(r"\\d{4}").all()\ns = f"bad {source[\'T\'].str.fullmatch(r\'\\d{4}\').sum()}"\n'
    r2, _, a2, _ = rescue_text(f2)
    if r2 is not None and any("fstring" in x for x in a2) and _parse_err(r2) is None:
        ok += 1; print("  [PASS] R2 f-string 反斜線吊升(前置變數)")
    else:
        print("  [FAIL] f-string")
    # 3 智慧引號(錯誤行鄰域)
    f3 = 'x = "ok"\ny = "bad"\n'.replace('"bad"', '“bad”')
    r3, _, a3, _ = rescue_text(f3)
    if r3 is not None and _parse_err(r3) is None:
        ok += 1; print("  [PASS] R2 智慧引號正規化(僅錯誤行鄰域)")
    else:
        print("  [FAIL] 引號")
    # 4 Tab 混縮排
    f4 = "def f():\n    x = 1\n\ty = 2\n\treturn x + y\n"
    r4, _, _, _ = rescue_text(f4)
    if r4 is not None and _parse_err(r4) is None:
        ok += 1; print("  [PASS] R2 Tab→空格")
    else:
        print("  [FAIL] Tab")
    # 5 不可救=誠實 ADVICE
    f5 = "def f(:\n    return ???\n"
    r5, _, _, last5 = rescue_text(f5)
    if r5 is None and last5:
        ok += 1; print("  [PASS] 語意級破損誠實 FAIL+建議(不硬修)")
    else:
        print("  [FAIL] 誠實閘")
    # 6 三輪上限
    if rescue_text(f5, max_rounds=3)[1] <= 3:
        ok += 1; print("  [PASS] 三輪上限(不無限修)")
    else:
        print("  [FAIL] 輪限")
    # 7 好檔零變換
    f7 = "a = 1\n"
    r7, rounds7, a7, _ = rescue_text(f7)
    if r7 == f7 and rounds7 == 0 and not a7:
        ok += 1; print("  [PASS] 健康檔零觸碰")
    else:
        print("  [FAIL] 零觸碰")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    if "--scan" in a:
        return cmd_scan()
    if "--repair-one" in a:
        i = a.index("--repair-one")
        return cmd_repair(a[i + 1] if len(a) > i + 1 else None)
    if "--repair" in a:
        return cmd_repair()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
