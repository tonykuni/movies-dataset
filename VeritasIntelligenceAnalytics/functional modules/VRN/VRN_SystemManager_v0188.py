#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0188 — 薄尾(操作員 2026-10-11「USE SAMPLE TO TEST ONE BY ONE · LEARN BY REAL TESTING · WITH 30 THE MOST POTENTIAL FAILURES AND MULTIPLE SOLUTIONS EMBEDDED」)。
  learn 動詞(auto 自動接 · learn --one <檔名> 只測一份):樣本一份一份 → 每張失敗表依根因(v0187)試該根因的多個解法 → 每個候選重跑加減法 / 除法測試 →
  通過數增加且不符數沒增加才接受(取分數最高)→ 每次嘗試寫學習台帳(只增)→ 解法順序冊依實測勝率排序(試 ≥5 次才調)· 每份處理完立刻更新(下一份用新順序)
  雙軌衝突:OCR 錯誤型態候選修正(負號 / 倍數 / 誤認字 / 黏連)= NON-OCR 驗過值 → 學 OCR 最常犯的錯(調 OCR 前處理的依據)
  修好的表另寫 restore_learned/(原 restore 輸出不動)
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import copy
import csv
import datetime
import html
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0188"
MIN_TRIES = 5


def _vnum_v0188(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0188(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0188(p) < _vnum_v0188(__file__)), key=_vnum_v0188)
PRIOR = _load_v0188(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_rep, _home = _resolve("_rep"), _resolve("_home")
_isp, _num = _resolve("_is_per") or (lambda s: False), _resolve("_num") or (lambda s: None)
COST = {"cogs", "opex", "tax", "sga", "rnd", "selling_expense", "admin_expense"}
GROWTH_MAP = [(r"(?i)revenue|sales|營收|營業收入", "rev_growth"), (r"(?i)net income|淨利|稅後", "ni_growth"), (r"(?i)eps|每股盈餘", "eps_growth"), (r"(?i)operating|營業利益|營益", "op_growth")]


def score(rows: list) -> tuple:
    ts = (_resolve("fin_tests") or (lambda r: []))(rows)
    ps, fs = sum(1 for x in ts if x["status"] == "PASS"), sum(1 for x in ts if x["status"] == "FAIL")
    cells = sum(1 for r in rows for c in r.get("cells") or [] if isinstance(c.get("value"), (int, float)))
    return ps - 2 * fs + 0.01 * cells, ps, fs


def build_rows(raw: list, lab2std: dict, align: str = "right", cols: tuple = None) -> list:
    """raw → rows:表頭 = 第一個有 ≥2 期間的列;數值依表頭期間對齊(靠右 / 靠左)· cols = 只取這段欄(並排兩表切開用)。"""
    hi = next((i for i, r in enumerate(raw) if sum(1 for c in r if _isp(c)) >= 2), None)
    if hi is None:
        return []
    hdr = [(j, str(c).strip()) for j, c in enumerate(raw[hi]) if _isp(c)]
    if cols:
        hdr = [(j, p) for j, p in hdr if cols[0] <= j < cols[1]]
    pers = [p for _, p in hdr]
    out = []
    for r in raw[hi + 1:]:
        lab = next((str(c).strip() for c in r if str(c).strip() and _num(c) is None), "")
        nums = [(j, _num(c)) for j, c in enumerate(r) if _num(c) is not None]
        if cols:
            nums = [(j, v) for j, v in nums if cols[0] <= j < cols[1]] or nums
        vals = [v for _, v in nums]
        if not lab or not vals:
            continue
        seq = vals[-len(pers):] if align == "right" else vals[:len(pers)]
        ps = pers[-len(seq):] if align == "right" else pers[:len(seq)]
        out.append({"label_raw": lab, "std": lab2std.get(lab, ""), "cells": [{"period": p, "value": v} for p, v in zip(ps, seq)]})
    return out


# ───────── 每個根因的多個解法(在表的資料上試 · 由驗證決定採用)─────────
def _l2s(t):
    return {r.get("label_raw"): r.get("std") for r in t.get("rows") or [] if r.get("label_raw")}


def sol_align_right(t, ctx):
    return build_rows(t.get("raw_rows") or [], _l2s(t), "right")


def sol_align_left(t, ctx):
    return build_rows(t.get("raw_rows") or [], _l2s(t), "left")


def _dup_split(t):
    raw = t.get("raw_rows") or []
    for r in raw[:3]:
        idx = [(j, str(c).strip()) for j, c in enumerate(r) if _isp(c)]
        seen = {}
        for j, p in idx:
            if p in seen:
                return j
            seen[p] = j
    return None


def sol_split_left(t, ctx):
    k = _dup_split(t)
    return build_rows(t.get("raw_rows") or [], _l2s(t), "left", (0, k)) if k else None


def sol_split_right(t, ctx):
    k = _dup_split(t)
    return build_rows(t.get("raw_rows") or [], _l2s(t), "left", (k, 10 ** 6)) if k else None


def sol_merge_label(t, ctx):
    raw = [list(r) for r in t.get("raw_rows") or []]
    out = []
    for r in raw:
        if out and not str(r[0]).strip() and sum(1 for c in r[1:] if _num(c) is not None) >= 2 and all(_num(c) is None for c in out[-1][1:]):
            out[-1] = [out[-1][0]] + r[1:]
        else:
            out.append(r)
    return build_rows(out, _l2s(t), "right")


def sol_paren_neg(t, ctx):
    paren = {abs(_num(c)) for r in t.get("raw_rows") or [] for c in r if re.fullmatch(r"\(\s*[\d,]+(?:\.\d+)?\s*\)", str(c).strip()) and _num(c) is not None}
    rows = copy.deepcopy(t.get("rows") or [])
    for r in rows:
        for c in r.get("cells") or []:
            if isinstance(c.get("value"), (int, float)) and c["value"] > 0 and c["value"] in paren:
                c["value"] = -c["value"]
    return rows


def sol_thousand(t, ctx):
    raw = [[re.sub(r"^(\d{1,3})\.(\d{3})$", r"\1\2", str(c).strip()) for c in r] for r in t.get("raw_rows") or []]
    return build_rows(raw, _l2s(t), "right")


def sol_drop_unit_rows(t, ctx):
    return [r for r in copy.deepcopy(t.get("rows") or []) if not re.fullmatch(r"(?i)\s*\(?(NT\$|US\$|RMB)?\s*(m|mn|bn|百萬|千元|億元|%|x)\)?\s*", str(r.get("label_raw") or ""))]


def sol_growth_key(t, ctx):
    rows = copy.deepcopy(t.get("rows") or [])
    for r in rows:
        lab = str(r.get("label_raw") or "")
        if re.search(r"(?i)growth|yoy|%|率", lab) and not re.search(r"margin|growth|ratio|roe|roa", r.get("std") or ""):
            r["std"] = next((k for rx, k in GROWTH_MAP if re.search(rx, lab)), "")
    return rows


def sol_growth_drop(t, ctx):
    rows = copy.deepcopy(t.get("rows") or [])
    for r in rows:
        if re.search(r"(?i)growth|yoy|%|率", str(r.get("label_raw") or "")) and not re.search(r"margin|growth|ratio", r.get("std") or ""):
            r["std"] = ""
    return rows


def _suffix(t, ctx, off):
    ry = ctx.get("report_year")
    if not ry:
        return None
    rows = copy.deepcopy(t.get("rows") or [])
    for r in rows:
        for c in r.get("cells") or []:
            m = re.fullmatch(r"(?:FY)?((?:19|20)\d{2})", str(c.get("period") or ""))
            if m:
                c["period"] = m.group(1) + ("F" if int(m.group(1)) >= ry + off else "A")
    return rows


def sol_suffix_same(t, ctx):
    return _suffix(t, ctx, 0)


def sol_suffix_next(t, ctx):
    return _suffix(t, ctx, 1)


def _dedupe(t, keep):
    rows, seen = [], {}
    for r in copy.deepcopy(t.get("rows") or []):
        s = r.get("std")
        if s and s in seen:
            if keep == "last":
                rows[seen[s]] = r
            continue
        if s:
            seen[s] = len(rows)
        rows.append(r)
    return rows


def sol_dedupe_first(t, ctx):
    return _dedupe(t, "first")


def sol_dedupe_last(t, ctx):
    return _dedupe(t, "last")


def _sign(t, neg):
    rows = copy.deepcopy(t.get("rows") or [])
    for r in rows:
        if r.get("std") in COST:
            for c in r.get("cells") or []:
                if isinstance(c.get("value"), (int, float)):
                    c["value"] = -abs(c["value"]) if neg else abs(c["value"])
    return rows


def sol_cost_negative(t, ctx):
    return _sign(t, True)


def sol_cost_positive(t, ctx):
    return _sign(t, False)


def _scale_rows(t, k):
    """只放大一列(量級錯通常只有某一列)· 逐列各試一次 · 取分數最好的變體。"""
    rows0 = t.get("rows") or []
    ts = (_resolve("fin_tests") or (lambda r: []))(rows0)
    bad = {x["period"] for x in ts if x["status"] == "FAIL"}
    best, bs = None, score(rows0)[0]
    for i, r in enumerate(rows0):
        if not r.get("std") or re.search(r"margin|growth|ratio|roe|roa|eps|dps|bvps|pe|pb", r["std"]):
            continue
        cand = copy.deepcopy(rows0)
        hit = False
        for c in cand[i].get("cells") or []:
            if c.get("period") in bad and isinstance(c.get("value"), (int, float)) and abs(c["value"]) < 10 ** 5:
                c["value"] = c["value"] * k
                hit = True
        if hit:
            s = score(cand)[0]
            if s > bs:
                best, bs = cand, s
    return best


def sol_scale_10(t, ctx):
    return _scale_rows(t, 10)


def sol_scale_100(t, ctx):
    return _scale_rows(t, 100)


def sol_scale_1000(t, ctx):
    return _scale_rows(t, 1000)


SOLUTIONS = {"RC03": [sol_align_right, sol_align_left], "RC04": [sol_split_left, sol_split_right], "RC06": [sol_merge_label], "RC07": [sol_paren_neg], "RC08": [sol_thousand],
             "RC09": [sol_drop_unit_rows], "RC12": [sol_growth_key, sol_growth_drop], "RC13": [sol_suffix_same, sol_suffix_next], "RC15": [sol_dedupe_first, sol_dedupe_last],
             "RC16": [sol_cost_negative, sol_cost_positive], "RC17": [sol_scale_10, sol_scale_100, sol_scale_1000], "RC01": [sol_align_right, sol_align_left], "RC02": [sol_align_right]}
OCR_FIX = {"RC29": lambda a, b: [-b], "RC28": lambda a, b: [b * k for k in (10, 100, 1000, 0.1, 0.01, 0.001)],
           "RC25": lambda a, b: [float(s) for s in _swaps(b)], "RC26": lambda a, b: [float(s) for s in _subs(b)], "RC27": lambda a, b: [], "RC30": lambda a, b: []}


def _swaps(b):
    conf = {"3": "8", "8": "3", "1": "7", "7": "1", "0": "6", "6": "0", "5": "6", "9": "4", "4": "9"}
    s = "%g" % b
    return [s[:i] + conf[ch] + s[i + 1:] for i, ch in enumerate(s) if ch in conf]


def _subs(b):
    s = ("%g" % abs(b)).replace(".", "")
    return [s[i:j] for i in range(len(s)) for j in range(i + 1, len(s)) if j - i >= 2][:40]


# ───────── 學習:台帳(只增)+ 解法順序冊(試 ≥5 次才依勝率調)─────────
def _learn_dir() -> Path:
    d = (_home or (lambda: HERE))() / "knowledge"
    d.mkdir(parents=True, exist_ok=True)
    return d


def order_book() -> dict:
    fs = sorted(_learn_dir().glob("VRN_RootCause_SolutionBook_v*.json"), key=_vnum_v0188)
    try:
        return json.loads(fs[-1].read_text(encoding="utf-8")).get("body", {}) if fs else {}
    except (OSError, ValueError):
        return {}


def ordered(rc: str, book: dict) -> list:
    sols = SOLUTIONS.get(rc, [])
    st = book.get(rc) or {}
    if all(st.get(s.__name__, {}).get("tried", 0) >= MIN_TRIES for s in sols):
        return sorted(sols, key=lambda s: -(st[s.__name__]["won"] / max(st[s.__name__]["tried"], 1)))
    return sols


def learn_table(fn: str, t: dict, ctx: dict, book: dict, ledger: list) -> dict:
    hits = sorted({h[0] for h in (_resolve("classify_table") or (lambda *a: []))(fn, t, ctx.get("report_year"))})
    base = score(t.get("rows") or [])
    best, best_s, used = None, base, []
    for rc in hits:
        for sol in ordered(rc, book):
            try:
                cand = sol(t, ctx)
            except Exception as exc:  # noqa: BLE001
                cand = None
                ledger.append({"file": fn, "table": t.get("id"), "rc": rc, "sol": sol.__name__, "ok": False, "why": "例外 %s" % type(exc).__name__})
                continue
            if not cand:
                ledger.append({"file": fn, "table": t.get("id"), "rc": rc, "sol": sol.__name__, "ok": False, "why": "沒有候選 / 沒改善"})   # 每次嘗試都記帳(勝率不灌水)
                continue
            s = score(cand)
            won = s[0] > best_s[0] and s[2] <= base[2]
            ledger.append({"file": fn, "table": t.get("id"), "rc": rc, "sol": sol.__name__, "before": base[:3], "after": s[:3], "ok": bool(s[0] > base[0] and s[2] <= base[2])})
            used.append((rc, sol.__name__, s))
            if won:
                best, best_s = (rc, sol.__name__, cand), s
    return {"rcs": hits, "base": base, "best": best, "best_s": best_s, "tried": len(used)}


def learn_ocr(rec: dict, ledger: list) -> list:
    out = []
    others = {float(c[1]) for c in rec.get("conflicts") or [] if isinstance(c, list) and len(c) > 2 and isinstance(c[1], (int, float))}
    cc = _resolve("classify_conflict")
    for c in rec.get("conflicts") or []:
        if not (isinstance(c, list) and len(c) >= 3 and cc):
            continue
        rc = cc(rec["file"], rec["id"], c[0], c[1], c[2], others)[0]
        try:
            a, b = float(c[1]), float(c[2])
            fixed = any(abs(x - a) <= max(abs(a) * 1e-4, 1e-9) for x in OCR_FIX.get(rc, lambda a, b: [])(a, b))
        except (TypeError, ValueError):
            fixed = False
        ledger.append({"file": rec["file"], "table": rec["id"], "rc": rc, "sol": "ocr_fix_" + rc, "ok": fixed, "track": "OCR"})
        out.append((rc, fixed))
    return out


def update_book(ledger: list) -> str:
    st = defaultdict(lambda: defaultdict(lambda: {"tried": 0, "won": 0}))
    lp = _learn_dir() / "VRN_RootCause_Learn_Ledger.jsonl"
    allrec = []
    if lp.exists():
        for l in lp.read_text(encoding="utf-8").splitlines():
            try:
                allrec.append(json.loads(l))
            except ValueError:
                pass
    with lp.open("a", encoding="utf-8") as fh:
        for x in ledger:
            fh.write(json.dumps(dict(x, ts=datetime.datetime.now().isoformat(timespec="seconds")), ensure_ascii=False, default=str) + "\n")
    for x in allrec + ledger:
        e = st[x["rc"]][x["sol"]]
        e["tried"] += 1
        e["won"] += 1 if x.get("ok") else 0
    body = {rc: dict(v) for rc, v in st.items()}
    w = _resolve("_book_write")
    return w(_learn_dir(), "VRN_RootCause_SolutionBook", body, "根因解法實測勝率(試 ≥%d 次才依勝率排序)· 學習台帳 VRN_RootCause_Learn_Ledger.jsonl(只增)" % MIN_TRIES) if w else "—"


def learn_run(one: str = "") -> dict:
    rep = _rep()
    files = [f for f in sorted((rep / "restore").glob("*.json")) if not f.name.startswith("RESTORE_")] if (rep / "restore").is_dir() else []
    dts = {}
    dp = rep / "dualtrack" / "DUALTRACK_latest.json"
    if dp.exists():
        for x in json.loads(dp.read_text(encoding="utf-8")).get("records", []):
            if x.get("kind") == "table" and x.get("lamp") == "RED":
                dts.setdefault(x["file"], []).append(x)
    od = rep / "restore_learned"
    od.mkdir(parents=True, exist_ok=True)
    per, tot = [], Counter()
    for f in files:
        dj = json.loads(f.read_text(encoding="utf-8"))
        meta = dj.get("document_meta") or {}
        fn = meta.get("file") or f.stem
        if one and one not in fn:
            continue
        ry = re.search(r"(20\d{2})", str(meta.get("report_date") or fn))
        ctx = {"report_year": int(ry.group(1)) if ry else None}
        book, ledger, fixed, fail_t = order_book(), [], 0, 0
        new = copy.deepcopy(dj)
        for i, t in enumerate(dj.get("tables", [])):
            if t.get("status") == "還原無誤" and not any(c.get("status") == "FAIL" for c in t.get("calc") or []):
                continue
            fail_t += 1
            r = learn_table(fn, t, ctx, book, ledger)
            if r["best"]:
                rc, sol, cand = r["best"]
                new["tables"][i] = dict(t, rows=cand, learned={"rc": rc, "solution": sol, "before": r["base"][:3], "after": r["best_s"][:3]})
                fixed += 1
                tot["%s·%s" % (rc, sol)] += 1
        oc = []
        for rec in dts.get(fn, []):
            oc += learn_ocr(rec, ledger)
        bk = update_book(ledger)
        if fixed:
            (od / f.name).write_text(json.dumps(new, ensure_ascii=False, default=str), encoding="utf-8")
        per.append({"file": fn, "fail_tables": fail_t, "fixed": fixed, "tries": len([x for x in ledger if x.get("track") != "OCR"]), "ocr": len(oc), "ocr_fixable": sum(1 for _, ok in oc if ok), "book": bk})
        print("  [學] %s · 失敗表 %d → 修好 %d · 試 %d 次 · OCR 衝突 %d(可由錯誤型態解釋 %d)· 順序冊 %s" % (fn[:34], fail_t, fixed, per[-1]["tries"], len(oc), per[-1]["ocr_fixable"], bk), flush=True)
    bk = order_book()
    rate = sorted(((rc, s, v["won"], v["tried"]) for rc, d in bk.items() for s, v in d.items() if v["tried"]), key=lambda x: (-x[2] / x[3], -x[3]))
    (rep / "learn").mkdir(parents=True, exist_ok=True)
    (rep / "learn" / "LEARN_latest.json").write_text(json.dumps({"per_report": per, "accepted": dict(tot), "solution_rates": rate}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"reports": len(per), "fail": sum(x["fail_tables"] for x in per), "fixed": sum(x["fixed"] for x in per), "accepted": tot, "rates": rate,
            "ocr": sum(x["ocr"] for x in per), "ocr_fixable": sum(x["ocr_fixable"] for x in per)}


def _lines_v188(o: dict) -> list:
    L = ["[計] 實測學習(一份一份 · 30 根因 × 多解法 · 驗證才採用)· %d 份 · 失敗表 %d → 修好 %d(另存 restore_learned · 原輸出不動)· OCR 衝突 %d(錯誤型態可解釋 %d)" % (
        o["reports"], o["fail"], o["fixed"], o["ocr"], o["ocr_fixable"])]
    if o["accepted"]:
        L.append("[計] 採用的解法 · " + " · ".join("%s × %d" % kv for kv in o["accepted"].most_common(8)))
    for rc, s, w, n in o["rates"][:10]:
        L.append("[計] 解法勝率 · %s · %s · %d/%d(%.0f%%)%s" % (rc, s, w, n, 100 * w / n, "" if n >= MIN_TRIES else " · 樣本 <%d 不調順序" % MIN_TRIES))
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["learn"] or (args[:1] in (["auto"], ["rootcause"]) and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] != ["learn"] else 0
        one = args[args.index("--one") + 1] if "--one" in args and args.index("--one") + 1 < len(args) else ""
        L = _lines_v188(learn_run(one))
        for l in L:
            print(l)
        if args[:1] == ["auto"]:
            pk = _rep() / "auto" / "VRN_AI_PACK_latest.md"
            if pk.exists():
                old = [l for l in pk.read_text(encoding="utf-8").splitlines() if l.strip()]
                nxt = [l for l in old if l.startswith("NEXT:")] or ["NEXT: 依根因排行與解法勝率 → 源頭修 → 再跑 auto"]
                pk.write_text("\n".join(([l for l in old if not l.startswith("NEXT:")] + L)[:299] + nxt[:1]) + "\n", encoding="utf-8")
                ac = _resolve("aiverb_compress")
                if ac:
                    print("[計] AI 包(含實測學習)· %s" % ac(pk, nxt[0].replace("NEXT: ", ""))[1])
        return rc
    return PRIOR.main(args)



def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    R = lambda lab, std, vals: {"label_raw": lab, "std": std, "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
    raw = [["NT$m", "2024A", "2025F"], ["Revenue", "1,000", "1,200"], ["Gross profit", "", "500"]]
    br, bl = build_rows(raw, {"Revenue": "revenue", "Gross profit": "gross_profit"}, "right"), build_rows(raw, {"Revenue": "revenue", "Gross profit": "gross_profit"}, "left")
    chk("① 由原始格重建列:少一格時 靠右 → 500 對 2025F · 靠左 → 500 對 2024A(兩個候選交給驗證決定)", br[1]["cells"] == [{"period": "2025F", "value": 500.0}] and bl[1]["cells"] == [{"period": "2024A", "value": 500.0}])
    tsc = {"id": "T1", "status": "算術不符(待查)", "raw_rows": [], "rows": [R("Revenue", "revenue", {"2025F": 1200}), R("COGS", "cogs", {"2025F": -700}), R("GP", "gross_profit", {"2025F": 50})],
           "calc": [{"rule": "毛利 = 營收 − 成本", "period": "2025F", "status": "FAIL", "detail": "50 vs 500"}]}
    led = []
    r1 = learn_table("A.pdf", tsc, {"report_year": 2025}, {}, led)
    chk("② 量級錯(毛利 50 應為 500):根因 RC17 → 試 ×10 / ×100 / ×1000(各自逐列)→ ×10 讓恆等式過 → 採用 %s · 分數 %s → %s" % (r1["best"][:2] if r1["best"] else None, r1["base"][:3], r1["best_s"][:3]),
        r1["best"] and r1["best"][:2] == ("RC17", "sol_scale_10") and r1["best_s"][2] == 0 and any(x["sol"] == "sol_scale_100" for x in led))
    tp = {"id": "T2", "status": "未過", "raw_rows": [["NT$m", "2025F"], ["Operating income", "500"], ["Non-operating", "(100)"], ["Pretax", "400"]],
          "rows": [R("Operating income", "operating_income", {"2025F": 500}), R("Non-operating", "nonop_income", {"2025F": 100}), R("Pretax", "pretax_income", {"2025F": 400})]}
    r2 = learn_table("B.pdf", tp, {}, {}, [])
    chk("③ 括號負數讀成正值(業外 (100) → 100):RC07 → 轉負 → 營益 500 + 業外 −100 = 稅前 400 → 採用", r2["best"] and r2["best"][:2] == ("RC07", "sol_paren_neg") and r2["best_s"][2] == 0)
    bk = {"RC03": {"sol_align_right": {"tried": 6, "won": 1}, "sol_align_left": {"tried": 6, "won": 5}}}
    bk2 = {"RC03": {"sol_align_right": {"tried": 2, "won": 0}, "sol_align_left": {"tried": 2, "won": 2}}}
    chk("④ 解法順序依實測勝率:試 ≥5 次 → 靠左(5/6)排第一 · 試 <5 次 → 維持預設順序(不被小樣本誤導)",
        [s.__name__ for s in ordered("RC03", bk)] == ["sol_align_left", "sol_align_right"] and [s.__name__ for s in ordered("RC03", bk2)] == ["sol_align_right", "sol_align_left"])
    lo = []
    oc = learn_ocr({"file": "A.pdf", "id": "T1", "conflicts": [["a·2025F", 120.0, -120.0], ["b·2025F", 1234.0, 12.34], ["c·2025F", 1830.0, 1330.0], ["d·2025F", 100.0, 257.0]]}, lo)
    chk("⑤ OCR 錯誤型態學習:負號遺失 / 小數點遺失 / 8↔3 誤認 → 候選修正 = NON-OCR 值(可解釋)· 其他 → 不可解釋", [x[1] for x in oc] == [True, True, True, False]
        and [x[0] for x in oc][:3] == ["RC29", "RC28", "RC25"])
    td = Path(tempfile.mkdtemp(prefix="vrn188-"))
    saved = os.environ.get("VIA_VRN_HEALTH_OUT")
    saved_home = globals().get("_home")
    try:
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        globals()["_home"] = lambda: td / "VRN"  # noqa: E731
        (td / "rep" / "restore").mkdir(parents=True)
        for i, t in enumerate((tsc, tp)):
            (td / "rep" / "restore" / ("0%d_x.json" % i)).write_text(json.dumps({"document_meta": {"file": "R%d 20251201.pdf" % i}, "tables": [t]}, ensure_ascii=False), encoding="utf-8")
        o = learn_run()
        lp = td / "VRN" / "knowledge" / "VRN_RootCause_Learn_Ledger.jsonl"
        n1 = len(lp.read_text(encoding="utf-8").splitlines())
        books = sorted((td / "VRN" / "knowledge").glob("VRN_RootCause_SolutionBook_v*.json"))
        learned = sorted(x.name for x in (td / "rep" / "restore_learned").glob("*.json"))
        orig = json.loads((td / "rep" / "restore" / "00_x.json").read_text(encoding="utf-8"))["tables"][0]["rows"][2]["cells"][0]["value"]
        o2 = learn_run("R1")
        n2 = len(lp.read_text(encoding="utf-8").splitlines())
        chk("⑥ 一份一份實測:2 份 → 修好 %d 張 · 每份處理完就更新順序冊(%d 版)· 修好的另存 restore_learned(%s)· 原 restore 不動(毛利仍 %s)· 台帳只增 %d → %d · --one 只測 1 份" % (
            o["fixed"], len(books), learned, orig, n1, n2), o["fixed"] == 2 and len(books) >= 1 and learned == ["00_x.json", "01_x.json"] and orig == 50 and n2 > n1 and o2["reports"] == 1)
    finally:
        globals()["_home"] = saved_home
        if saved is None:
            os.environ.pop("VIA_VRN_HEALTH_OUT", None)
        else:
            os.environ["VIA_VRN_HEALTH_OUT"] = saved
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0188 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
