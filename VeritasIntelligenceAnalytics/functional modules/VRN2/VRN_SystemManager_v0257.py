#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 v0257: one row, one item — side-by-side tables no longer lend their values to the left table's item (thin tail over v0255).

Desktop run 2026-10-30 18:34 (Handle-All v0100 → RoundAll v0108 verify · package v0152): the independent verifier still counts
DUPKEY 45 in the annual book — 37 of them are 6933_AMAX-KY_個股介紹報告.pdf page 8, where two tables stand side by side
(balance sheet on the left, income statement on the right). One extracted row carries both tables' cells, so the right table's
values were written under the LEFT item: 流動資產 2020 = 1,331,956 (balance sheet) AND 3,411,492 (income statement) ·
權益總額分配後 2020 = 699,650 AND -0.54 (EPS). The verifier: "同鍵對位的值是 1,331,956 · 這筆 3,411,492 不對位 → 錯值".
The other 8 are 凱基投顧_2891 中信金 page 5 (no row number · "分不出").

v0257 checks the annual book once more after v0255's books are written: rows with the same file · page · table · row number ·
item · period · section · sub-column but DIFFERENT values cannot all belong to that item.
  · row number known → find each value's cell in that extracted row (the zone row of the table, left to right); the value in the
    leftmost cell stays with the row's own item. A later value takes the item written in its own row between the two groups
    (a label cell, or a label cell fused with its first value: 「繼續營業單位本期淨利 -19,614」) → renamed to that item, verify note
    says so (the independent verifier checks it again). No label in that row → the later values move to the Rejected book
    with a reason (not under the left item any more).
  · no row number → which value is the item's cannot be told → all of them move to the Rejected book with a reason.
  · same item on different rows (MS-3661 "Percent of Revenues" under every line · MS-2308 "Other adjustments" in each cash-flow
    block) is NOT touched: the row number already tells them apart and every value is on its own row.
Nothing else changes: extraction, acceptance, the other books, verifiers and the U/I stay v0255 / v0243 code (reached through PRIOR).
Selftest also re-runs v0255's idempotence-gate selftest with one counter file per report: v0255's fake engine shares ONE counter file
between its 3 parallel lanes without a lock — a lane that truncates it while another reads gets an empty file, the count restarts, R1
equals R2 for that report and the check reports 2 nondeterministic files instead of 3 (seen on 1 of 6 concurrent runs). v0255 stays as is.
Version number: v0256 is the desktop line's in functional modules/VRN; this private runtime line continues at v0257 (PRIOR v0255).
"""
from __future__ import annotations

# ===== 1. Parameters =====
TAG = "v0257"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0255.py"

from collections import defaultdict
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import contextlib
import io
import tempfile
import types

# [VIA:ACCEL-BRIDGE:v0111] The original manager executes its accelerator bridge.
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0257", Path(__file__).with_name(PRIOR_NAME))
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in list(vars(PRIOR).items()):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


def _rebind(function):
    result = types.FunctionType(function.__code__, globals(), function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__, result.__doc__ = function.__kwdefaults__, function.__doc__
    return result


# ===== 2. One row, one item =====
_RF_NUM = re.compile(r"^[(\[]?[-+−–]?\s?[\d,]*\.?\d+\s?[)\]]?\s?%?x?$|^[-–—]+$|^n\.?\s?[am]\.?$|^nm$", re.I)
_RF_PER = re.compile(r"^(?:fy)?(?:19|20)?\d{2}[aefp]?$|^\d{1,2}/\d{2}[aefp]?$|^(?:[a-z]{3}-)\d{2}[aefp]?$|^\d{4}\s?\((?:a|e|f|p)\)$", re.I)
_RF_TAIL = re.compile(r"^(?P<lab>.*?[A-Za-z㐀-鿿\)）%].*?)\s+(?P<val>[(\[]?[-+−–]?[\d,]*\.?\d+[)\]]?%?|[-–—])$")


def _rf_sq(text) -> str:
    return re.sub(r"\s+", "", str(text or "")).replace("−", "-").replace("–", "-")


def _rf_label(cell):
    """A cell that names an item → the item text; a label fused with its first value (「繼續營業單位本期淨利 -19,614」) → the label part;
    numbers / dashes / periods / empty → None."""
    text = str(cell or "").strip()
    if not text or _RF_NUM.match(text) or _RF_PER.match(text):
        return None
    m = _RF_TAIL.match(text)
    lab = (m.group("lab") if m else text).strip()
    if not re.search(r"[A-Za-z㐀-鿿]", lab) or _RF_PER.match(lab):
        return None
    return lab


def _rf_zone_rows(res) -> dict:
    """(file, table id) → the table's extracted rows (cells left to right), as the extraction stored them."""
    out = {}
    for entry in res or []:
        for page in entry.get("pages") or []:
            for zone in page.get("zones") or []:
                if zone.get("id") and zone.get("rows"):
                    out[(entry.get("file"), zone.get("id"))] = zone["rows"]
    return out


def _rf_cell(cells: list, value, used: set):
    """Index of the cell that holds this value (whole cell, or the value part of a label+value cell) · not one already used · None."""
    want = _rf_sq(value)
    if not want:
        return None
    for j, cell in enumerate(cells):
        if j == 0 or j in used:
            continue
        text = str(cell or "")
        m = _RF_TAIL.match(text.strip())
        if _rf_sq(text) == want or (m and _rf_sq(m.group("val")) == want):
            return j
    return None


def _rowfix(fin: list, res) -> tuple:
    """Same file · page · table · row · item · period · section · sub-column with different values → keep / rename / reject (see the module doc).
    Returns (kept rows, rejected rows with REASON, renamed count, examples)."""
    zones = _rf_zone_rows(res)
    groups = defaultdict(list)
    for i, x in enumerate(fin):
        groups[(x.get("FILENAME"), str(x.get("PAGE", "")), x.get("TABLE"), str(x.get("ROW") or ""), x.get("ITEM"), x.get("PERIOD"), x.get("SECTION", "") or "", x.get("SUBCOL", "") or "")].append(i)
    clash = {k: ix for k, ix in groups.items() if len({_rf_sq(fin[i].get("VALUE")) for i in ix}) > 1}
    drop, rename, ex = {}, {}, []
    rowwise = defaultdict(list)
    for k, ix in clash.items():
        if not k[3]:
            for i in ix:
                drop[i] = "同科目同期間 %d 個不同的值(%s)· 這幾筆沒有列號 · 分不出哪個是「%s」的 → 都不進主冊" % (len(ix), " / ".join(str(fin[j].get("VALUE")) for j in ix)[:80], k[4])
            if len(ex) < 6:
                ex.append("%s p%s 「%s」%s 沒有列號 → 剔除 %d 筆" % (str(k[0])[:16], k[1], str(k[4])[:14], k[5], len(ix)))
        else:
            rowwise[k[:5]].append(k)
    for rk, keys in rowwise.items():
        cells = zones.get((rk[0], rk[2]))
        try:
            cells = list(cells[int(rk[3]) - 1]) if cells else None
        except (ValueError, IndexError, TypeError):
            cells = None
        members = [i for i, x in enumerate(fin) if (x.get("FILENAME"), str(x.get("PAGE", "")), x.get("TABLE"), str(x.get("ROW") or ""), x.get("ITEM")) == rk]
        pos, used = {}, set()
        if cells:
            for i in members:
                j = _rf_cell(cells, fin[i].get("VALUE"), used)
                if j is not None:
                    pos[i] = j
                    used.add(j)
        for k in keys:
            ix = groups[k]
            order = sorted(ix, key=lambda i: (pos.get(i, 10 ** 6), i))
            keep = order[0]
            for i in order[1:]:
                label, at = None, None
                if cells and i in pos and keep in pos:
                    for j in range(pos[i], pos[keep], -1):
                        lab = _rf_label(cells[j])
                        if lab and _rf_sq(lab) != _rf_sq(rk[4]):
                            label, at = lab, j
                            break
                if label:
                    rename[i] = (label, at)
                else:
                    drop[i] = "並排的另一張表:同一列「%s」%s 有 %d 個不同的值 · 留最左邊的 %s · 這個值在這一列找不到它自己的科目名 → 不掛在「%s」名下" % (
                        rk[4], fin[i].get("PERIOD"), len(ix), fin[keep].get("VALUE"), rk[4])
        # the rest of that row right of a found label belongs to the label too (a period the left table does not have)
        for i, (label, at) in list(rename.items()):
            if i not in members:
                continue
            for m_ in members:
                if m_ not in rename and m_ not in drop and pos.get(m_, -1) > at and not any(at < j < pos[m_] and _rf_label(cells[j]) for j in range(at + 1, pos[m_])):
                    rename[m_] = (label, at)
        if len(ex) < 6 and any(i in rename or i in drop for i in members):
            ex.append("%s p%s %s 第 %s 列「%s」→ 改名 %d · 剔除 %d" % (str(rk[0])[:16], rk[1], rk[2], rk[3], str(rk[4])[:14], sum(1 for i in members if i in rename), sum(1 for i in members if i in drop)))
    keep_rows, rej = [], []
    for i, x in enumerate(fin):
        if i in drop:
            rej.append(dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData", REASON=drop[i]))
        elif i in rename:
            label = _tidy(rename[i][0]) if "_tidy" in globals() else rename[i][0]
            keep_rows.append(dict(x, ITEM=label, VERIFY=(str(x.get("VERIFY") or "") + " · v0257 並排第二張表(科目取同一列的「%s」· 原掛在「%s」)" % (label, x.get("ITEM"))).strip(" ·")))
        else:
            keep_rows.append(x)
    return keep_rows, rej, len(rename), ex


def _out_books_v0257(res, acc, st, v2):
    """v0257 = v0255 / v0243 books + one row, one item (annual book rewritten only when something moved)."""
    basic, fin, summ, gaps, made = _PRIOR_OUT(res, acc, st, v2)
    fin2, rej_add, renamed, ex = _rowfix(fin, res)
    if rej_add or renamed:
        od = Path(v2) / "output"
        rej = _XV_LAST.get("rej")
        if rej is None:
            try:
                rej = json.loads((od / "VRN2_Rejected_latest.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                rej = []
        rej = list(rej) + rej_add
        made = [m_ for m_ in made if not m_.startswith(("FinancialData(", "Rejected("))]
        made = [_write_book(od, "FinancialData", fin2)] + made + [_write_book(od, "Rejected", rej)]
        _XV_LAST["rej"] = rej
        fin = fin2
    it = _XV_LAST.get("item")
    if it:
        _XV_LAST["item"] = (it[0], it[1], it[2] + " · v0257 同一列同科目同期間兩個值:改名 %d · 剔除 %d%s" % (renamed, len(rej_add), (":" + " | ".join(ex[:3])) if ex else ""))
    if ex:
        _say("[計] v0257 一列一科目 · 改名 %d · 剔除 %d · %s" % (renamed, len(rej_add), " | ".join(ex[:4])))
    return basic, fin, summ, gaps, made


_PRIOR_OUT = getattr(PRIOR._out_books, "__wrapped__", PRIOR._out_books)    # v0255 wraps v0243's books in a phase timer
_out_books = _timed("輸出冊", _out_books_v0257)


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    result["manager"] = f"{DISPLAY_NAME} {TAG}"
    return result


# ===== 3. Native flow with v0257 globals (books · completion · register) =====
_native_vrn2 = _rebind(PRIOR._native_vrn2)
_success_register = _rebind(PRIOR._success_register)
vrn2 = _rebind(PRIOR.vrn2)


# ===== 4. Self-test =====
def selftest():
    bad = []

    def chk(name, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", name), flush=True)
        if not cond:
            bad.append(name)

    hdr = ["", "2020", "2021", "2022", "2020", "2021", "2022"]
    rows = [["資產負債表 ∥ 損益表"], hdr,
            ["流動資產", "1,331,956", "2,155,768", "2,112,693", "營業收入", "3,411,492", "5,212,499", "6,748,900"],
            ["流動負債分配後", "692,377", "1,334,171", "1,029,690", "繼續營業單位本期淨利 -19,614", "249,706", "184,523"],
            ["權益總額分配後", "699,650", "939,626", "1,205,604", "-0.54", "1.64", "2.85"],
            ["Percent of Revenues", "76.8%", "79.4%", "72.3%"], ["Gross Profit", "2,429", "1,887", "1,844"], ["Percent of Revenues", "23.2%", "20.6%", "27.7%"]]
    res = [{"file": "a.pdf", "pages": [{"pno": 8, "zones": [{"id": "P8·F·02·TB", "rows": rows}]}]}]

    def r(item, per, val, row, table="P8·F·02·TB", f="a.pdf"):
        return {"FILENAME": f, "PAGE": 8, "TABLE": table, "ITEM": item, "PERIOD": per, "VALUE": val, "ROW": row, "SECTION": "", "SUBCOL": "", "VERIFY": "對欄(pypdfium2)"}
    fin = [r("流動資產", p, v, 3) for p, v in zip(("2020", "2021", "2022"), ("1,331,956", "2,155,768", "2,112,693"))]
    fin += [r("流動資產", p, v, 3) for p, v in zip(("2020", "2021", "2022"), ("3,411,492", "5,212,499", "6,748,900"))]
    fin += [r("流動負債分配後", p, v, 4) for p, v in zip(("2020", "2021", "2022"), ("692,377", "1,334,171", "1,029,690"))]
    fin += [r("流動負債分配後", p, v, 4) for p, v in zip(("2021", "2022"), ("249,706", "184,523"))]
    fin += [r("權益總額分配後", p, v, 5) for p, v in zip(("2020", "2021", "2022"), ("699,650", "939,626", "1,205,604"))]
    fin += [r("權益總額分配後", p, v, 5) for p, v in zip(("2020", "2021", "2022"), ("-0.54", "1.64", "2.85"))]
    fin += [r("Percent of Revenues", "2020", "76.8%", 6), r("Percent of Revenues", "2020", "23.2%", 8)]
    fin += [{**r("現金及約當現金", "FY25", "4.3", ""), "TABLE": "P5·F·01·TB"}, {**r("現金及約當現金", "FY25", "1.33", ""), "TABLE": "P5·F·01·TB"}, r("股本", "2020", "499,298", "")]
    keep, rej, renamed, ex = _rowfix(fin, res)
    items = {(x["ITEM"], x["PERIOD"], x["VALUE"]) for x in keep}
    chk("① 並排兩張表 · 右表科目在同一列 → 右邊三個值改掛「營業收入」(左邊「流動資產」三個值不動)",
        {("流動資產", "2020", "1,331,956"), ("營業收入", "2020", "3,411,492"), ("營業收入", "2022", "6,748,900")} <= items and ("流動資產", "2020", "3,411,492") not in items)
    chk("② 右表科目跟第一個值黏在同一格(「繼續營業單位本期淨利 -19,614」)→ 同列右邊的值改掛「繼續營業單位本期淨利」",
        ("繼續營業單位本期淨利", "2021", "249,706") in items and ("繼續營業單位本期淨利", "2022", "184,523") in items and ("流動負債分配後", "2021", "1,334,171") in items)
    chk("③ 右表在這一列找不到科目名(權益總額 ∥ EPS -0.54)→ 右邊的值移剔除冊(帶理由)· 左邊的留著",
        ("權益總額分配後", "2020", "699,650") in items and not any(x[2] in ("-0.54", "1.64", "2.85") for x in items)
        and sum(1 for x in rej if x["VALUE"] in ("-0.54", "1.64", "2.85") and "並排的另一張表" in x["REASON"]) == 3)
    chk("④ 沒有列號的同鍵兩值(凱基 2891 現金及約當現金 FY25 4.3 / 1.33)→ 兩筆都移剔除冊 · 分不出",
        not any(x[0] == "現金及約當現金" for x in items) and sum(1 for x in rej if x["ITEM"] == "現金及約當現金" and "沒有列號" in x["REASON"]) == 2)
    chk("⑤ 同一個科目字在不同列(Percent of Revenues 第 6 / 8 列)· 沒撞鍵的列(股本)→ 不動",
        ("Percent of Revenues", "2020", "76.8%") in items and ("Percent of Revenues", "2020", "23.2%") in items and ("股本", "2020", "499,298") in items)
    chk("⑥ 改名的列註明來源(驗證器會再驗)· 剔除列不帶 VERIFY · 筆數守恆 · 改名 %d" % renamed,
        renamed == 5 and len(keep) + len(rej) == len(fin) and all("v0257 並排第二張表" in x["VERIFY"] for x in keep if x["ITEM"] in ("營業收入", "繼續營業單位本期淨利"))
        and all("VERIFY" not in x and x["BOOK"] == "FinancialData" for x in rej) and len(ex) >= 2)
    k2, r2, n2, e2 = _rowfix(fin[:3] + fin[12:14], res)
    chk("⑦ 沒有撞鍵 → 原樣(不改名 · 不剔除)", k2 == fin[:3] + fin[12:14] and not r2 and n2 == 0 and not e2)
    k3, r3, _n3, _e3 = _rowfix(fin[:6], [])
    chk("⑧ 沒有這張表的列(擷取結果不在)→ 依冊裡的順序留第一個 · 其他移剔除冊(不猜科目)",
        [x["VALUE"] for x in k3] == ["1,331,956", "2,155,768", "2,112,693"] and len(r3) == 3)
    with tempfile.TemporaryDirectory() as td:
        v2 = Path(td)
        (v2 / "output").mkdir()
        saved = dict(_XV_LAST)
        try:
            _XV_LAST.clear()
            _XV_LAST.update(rej=[{"BOOK": "FinancialData", "VALUE": "x", "REASON": "前版的剔除"}], item=("輸出值驗證", "GREEN", "基本資料 欄 1"))
            fake = lambda *a, **k: ([], list(fin), [], [], ["BasicInfo(0 列)", "FinancialData(%d 列)" % len(fin), "Rejected(1 列)"])   # noqa: E731
            globals()["_PRIOR_OUT"] = fake
            out = _out_books(res, [], [], v2)
            book = json.loads((v2 / "output" / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))
            rbook = json.loads((v2 / "output" / "VRN2_Rejected_latest.json").read_text(encoding="utf-8"))
            chk("⑨ 輸出冊:年度數據重寫 · 剔除冊 = 前版的剔除 + 本版的(不漏)· 輸出值驗證那一項註明 v0257 · 輸出冊階段照樣計時",
                len(book) == len(keep) and rbook[0]["REASON"] == "前版的剔除" and len(rbook) == 1 + len(rej) and "v0257 同一列同科目同期間兩個值" in _XV_LAST["item"][2]
                and out[1] == book and any(p["phase"] == "輸出冊" for p in PHASES) and sum(1 for m_ in out[4] if m_.startswith("FinancialData(")) == 1)
        finally:
            globals()["_PRIOR_OUT"] = getattr(PRIOR._out_books, "__wrapped__", PRIOR._out_books)
            _XV_LAST.clear()
            _XV_LAST.update(saved)
    chk("⑩ 原生流程綁本版名稱空間(輸出冊 / 完成判定 / 成功登記 → v0257)· 前版程式碼不動",
        _native_vrn2.__globals__ is globals() and vrn2.__globals__ is globals() and _native_vrn2.__code__ is PRIOR._native_vrn2.__code__
        and _success_register.__globals__ is globals() and _out_books.__wrapped__ is _out_books_v0257 and completion.__module__ == __name__)
    fixed = PRIOR.FAKE_ENGINE.replace('counter = os.environ.get("FAKE_COUNTER")\n', 'counter = os.environ.get("FAKE_COUNTER")\nif counter:\n    counter = counter + "." + shard["jobs"][0][1]\n', 1)
    saved_engine, why = PRIOR.FAKE_ENGINE, ""
    try:
        PRIOR.FAKE_ENGINE = fixed
        with contextlib.redirect_stdout(io.StringIO()):
            gate_rc = PRIOR.selftest()
    except AssertionError as error:
        gate_rc, why = 1, str(error)[:160]
    finally:
        PRIOR.FAKE_ENGINE = saved_engine
    chk("⑪ v0255 的冪等閘自測(GREEN · NONDETERMINISTIC 3 份 · 單路)用每份一個計數檔重跑 → 過(v0255 的假引擎 3 路共用一個計數檔 · 會互蓋)%s" % (" · " + why if why else ""),
        fixed != saved_engine and gate_rc == 0)
    print("[%s] v0257: one row, one item — side-by-side right-table values renamed to their own row label or moved to Rejected · row-less duplicates rejected · repeated item names on different rows untouched · v0255 gate selftest race-free · %d checks · failed %d"
          % ("PASS" if not bad else "FAIL", 11, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--selftest"]:
        return selftest()
    if arguments[:1] == ["vrn2"]:
        code, lines = vrn2(arguments[1:])
        for line in lines:
            print(line, flush=True)
        return code
    return PRIOR.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
