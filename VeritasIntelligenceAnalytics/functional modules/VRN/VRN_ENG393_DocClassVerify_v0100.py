#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG393_DocClassVerify v0100 — VRN 文件五類分類與路由 + 首頁文字 · 表格 · 分類 還原修復驗證(多法數字格三格亂數乘積互核)

操作員(2026-09-30):「啟動實測並驗證真實輸出結果  修正後的首頁內容持續調整到最佳化 文字表格分類還原修復驗證
  格子若有數字則可用亂數選三格相乘 若多方法結果並存 可檢驗數值乘積  再亂選三個直到選完  檢視政策都有符合
  VRN目前這條路徑只擷取個股報告  為 產業/展望  新聞摘要 / 其他投資報告(無關個股)  其他分類好就好」

為什麼是新引擎而不是某支的薄尾(量過 R35):
  · 細型別尺已有三把(ENG073 classify_kind · 首頁全能引擎 TickerFilename.classify_kind · ENG086 doc_type)加 webscraping 型冊 39 型,
    都寫死在各自的碼裡、互不相認;沒有一支擁有「五大類 + 路由 + 非個股欄留 NULL」,也沒有一支做「多法數字格互核」。
    改其中任一支的尾版都會讓那一支多管一件不屬於它的事(ENG073 是入庫正主、ENG072 是擷取正主、ENG392 是全文無遺漏正主)。
  · 本支**不重寫**任何一把尺:代號/年份守衛/券商/日期/細型別 讀 ENG073 尾版;首頁分區與法B(pdfplumber,含表格)讀 ENG072 尾版;
    首頁文字覆蓋率 · 數字逐一 · 修復迭代 · 品質分 讀 ENG392 尾版;標題細型讀 webscraping 型冊分類器。本支只加:
      ① 五類粗分類(規則冊 VIA_VRN_DocClass_SSOT_v*.json;次序即判準;證據 = 檔名 · 首頁標題帶 · 代號 · 券商)
      ② 路由:STOCK 走既有路徑(一個位元不變);產業/展望 · 新聞摘要 · 其他投資 各自車道記錄;OTHER → 複核佇列,絕不靜默丟棄;
         個股專屬欄在非個股列一律 NULL(NOT_STOCK_CLASS),不猜。
      ③ 首頁表格數字格多法互核:fitz find_tables · pdfplumber(ENG072 法B)· fitz 字詞自行分格 · 外部擷取器留存的格子 jsonl;
         ≥2 法都有數字的格 → 種子洗牌(種子寫進輸出)→ 三格一組相乘、各法乘積比對(Fraction 精確;相對容差 1e-9)→ 直到選完
         (最後一組可能不足三格,照實寫);含 0 的組一律逐格下鑽;乘積不符 → 逐格下鑽指出哪一格哪一法不同;
         只有一法的格 = SINGLE_SOURCE(不能互核,不算過);另一法看得到這張表、這格卻不是數字 = PRESENCE_DIFF(紅)。
         第二輪用 seed+1 重洗再分組:相乘可交換,單輪看不到同組兩格互換。
      ④ 逐件總判 GREEN / YELLOW / RED 與計數,寫成提案表頭 vrn_doc_class · vrn_firstpage_xcheck 的列
         (vrn_firstpage_matrix 七欄全是個股單值必填,非個股列放進去 = 必填空 = 紅;故另立兩表,表頭提案在規則冊 proposed_headers,
         定案由 VIA_Output_Header_SSOT 出新版;本支用 CGC_MDL249 check_table 自核列是否合提案表頭)。

CLI(只收經 VCGC 呼叫:VIA_FROM_VCGC=YES;via-vcgc run --family vrn VRN_ENG393_DocClassVerify <動詞> …):
  classify [--samples <夾>]… [--names <檔名> …] [--basicinfo [<json>]] [--no-text] [--json] [--no-write] [--out <夾>]
           未給來源 = 讀 StockReportBasicInfo.json(操作員 76 份真檔名)
  verify   --samples <夾>… [--seed N] [--recorded 名=<cells.jsonl>]… [--limit N] [--json] [--no-write] [--out <夾>]
  --selftest
結束碼:0 全綠(classify:全數分完)· 1 有紅 · 2 NODATA(樣本夾不在 / 沒有檔)· 3 只剩黃(不能互核 / 缺件 / 待複核)· 4 規則冊不在。
輸出:VIA_Reports/vrn/doc_class/(再生件,不入 git):DOCCLASS_latest.json · XCHECK_latest.json · lanes/<route>.jsonl。
VRN 不直接對外:只帶加速器橋,不帶網路橋(零網路)。不用 TA-Lib。L04:新家族 v0100,其他引擎一字不動。
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

import hashlib
import importlib.util
import json
import os
import random
import re
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
OUT = VIA / "VIA_Reports" / "vrn" / "doc_class"
ENGINE = Path(__file__).stem
FAMILY = "VRN_ENG393_DocClassVerify"
VER = "v0100"
BOOK_GLOB = "VIA_VRN_DocClass_SSOT_v*.json"
BASICINFO = HERE / "StockReportBasicInfo.json"
ENG114_PATH = HERE / "webscraping_dualengine_v20260819" / "VIA_Investment_Report_Classifier.py"
SAMPLE_EXT = {".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".txt", ".md"}
VERIFY_EXT = {".pdf", ".docx"}
ZW_RX = re.compile(r"[​-‏⁠﻿­]")


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _tail(folder: Path, stem: str):
    hits = [p for p in folder.glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


_MODS: dict = {}


def _load(path, key: str):
    """Load a module by path once; (module | None, why)."""
    if key in _MODS:
        return _MODS[key]
    if path is None or not Path(path).exists():
        _MODS[key] = (None, f"{key} 不在")
        return _MODS[key]
    try:
        spec = importlib.util.spec_from_file_location(f"eng393_{key}_{Path(path).stem}", str(path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _MODS[key] = (mod, Path(path).name)
    except Exception as exc:                       # an absent canon is reported, never faked
        _MODS[key] = (None, f"{Path(path).name} 載入失敗 {type(exc).__name__}: {str(exc)[:80]}")
    return _MODS[key]


def eng073():
    return _load(_tail(HERE, "VRN_ENG073_ReportStructuredDB"), "eng073")


def eng072():
    return _load(_tail(HERE, "VRN_ENG072_FirstPageText"), "eng072")


def eng392():
    return _load(_tail(HERE, "VRN_ENG392_TextCompleteness"), "eng392")


def eng114():
    return _load(ENG114_PATH, "eng114")


_BOOK: dict = {}


def book(path=None) -> dict:
    """The class book (newest VIA_VRN_DocClass_SSOT_v*.json). Absent → {} (callers report rc 4)."""
    key = str(path or "")
    if key in _BOOK:
        return _BOOK[key]
    hits = [Path(path)] if path else sorted(REG.glob(BOOK_GLOB), key=_vnum)
    try:
        bk = json.loads(hits[-1].read_text(encoding="utf-8")) if hits else {}
        bk["_book"] = hits[-1].name if hits else ""
    except (OSError, ValueError, IndexError):
        bk = {}
    _BOOK[key] = bk
    return bk


# ---------------------------------------------------------------- evidence

def _norm(s) -> str:
    return unicodedata.normalize("NFKC", ZW_RX.sub("", str(s or ""))).casefold()


_RX_CACHE: dict = {}


def _en_rx(word: str):
    rx = _RX_CACHE.get(word)
    if rx is None:
        parts = [re.escape(x) for x in word.split()]
        rx = re.compile(r"(?<![a-z0-9])" + r"[\s_\-]+".join(parts) + r"(?![a-z0-9])")
        _RX_CACHE[word] = rx
    return rx


def lex_hit(text: str, key: str, bk: dict):
    """First word of lexicon[key] found in text (zh = substring · en = word boundary). None when nothing hits."""
    t = _norm(text)
    for w in (bk.get("lexicon") or {}).get(key) or []:
        wn = _norm(w)
        if re.fullmatch(r"[a-z0-9 .&/\-]+", wn):
            if _en_rx(wn).search(t):
                return w
        elif wn and wn in t:
            return w
    return None


def _first_hit(text: str, keys: list, bk: dict):
    for k in keys:
        h = lex_hit(text, k, bk)
        if h:
            return k, h
    return None, None


def _has_mark(s: str, a: int, b: int) -> bool:
    """A four-digit token carries a ticker mark: (….) · TT/TW suffix · ',' ')' after · 'GS-' / '投顧_' before."""
    prev = s[a - 1] if a > 0 else ""
    nxt = s[b:b + 3]
    if (prev and prev in "(（") or (nxt[:1] and nxt[:1] in ")）,，") or nxt.upper().startswith(("TT", "TW")):
        return True
    if re.search(r"(?:^|[^A-Za-z])[A-Za-z]{2,8}\s*-\s*$", s[:a]):
        return True
    return bool(re.search(r"(?:投顧|證券|投信|代號|股號)\s*[_\-:：]?\s*$", s[:a]))


_FALLBACK_TICK_RX = re.compile(r"(?<![A-Za-z0-9])(\d{4})(?:TWO|TT|TW|T)?(?![A-Za-z0-9])")


def ticker_of(text: str, bk: dict, require_mark: bool = False) -> tuple:
    """(ticker | '', rejects). Canon = ENG073 TICK_RX + _is_year_like (three guards); then the book's YG-2 / YG-3 guards.
    require_mark (first-page title): a bare four-digit number is not a ticker there — it needs (….) / TT / TW / 'GS-' (book: title_ticker_requires_mark)."""
    m73, _why = eng073()
    s = unicodedata.normalize("NFKC", str(text or ""))
    rx = getattr(m73, "TICK_RX", None) if m73 else None
    rx = rx or _FALLBACK_TICK_RX
    spans = m73._date_spans(s) if m73 else []
    yg = ((bk.get("ticker") or {}).get("year_context_guard") or {})
    lo, hi = (yg.get("range") or [1990, 2099])
    rejects = []
    for cand in rx.finditer(s):
        code = cand.group(1)
        why = m73._is_year_like(s, cand, spans) if m73 else ""
        if why:
            rejects.append(f"{code}(ENG073:{why})")
            continue
        a, b = cand.span(1)
        if code.startswith("0") and yg.get("leading_zero_not_stock", True):
            rejects.append(f"{code}(YG-3:0 開頭 = ETF/基金代號,非個股)")
            continue
        if lo <= int(code) <= hi and not _has_mark(s, a, b):
            k, h = _first_hit(s, yg.get("reject_when_any_lex") or [], bk)
            if h:
                rejects.append(f"{code}(YG-2:{k}「{h}」)")
                continue
        if require_mark and not _has_mark(s, a, b):
            rejects.append(f"{code}(YG-4:首頁標題裸四碼無代號記號)")
            continue
        return code, rejects
    return "", rejects


def acronyms(text: str, bk: dict) -> list:
    stop = set((bk.get("lexicon") or {}).get("acronym_stop") or [])
    seen = []
    for t in re.findall(r"(?<![A-Za-z0-9])([A-Z]{2,5})(?![A-Za-z0-9])", unicodedata.normalize("NFKC", text or "")):
        if t not in stop and t not in seen:
            seen.append(t)
    return sorted(seen)


def ladder(text: str, ticker: str, bk: dict):
    """Walk the book's rules in order (order = the ruling). Returns (rule, hits) or (None, []) when only R10/R99 are left."""
    for rule in bk.get("rules") or []:
        w = rule.get("when") or {}
        if not w or w.get("fine_type_vote"):
            continue
        if "ticker" in w and bool(ticker) != bool(w["ticker"]):
            continue
        hits = []
        if w.get("ticker"):
            hits.append(f"代號 {ticker}")
        if w.get("any_lex"):
            k, h = _first_hit(text, w["any_lex"], bk)
            if not h:
                continue
            hits.append(f"{k}「{h}」")
        if w.get("also_any_lex"):
            k, h = _first_hit(text, w["also_any_lex"], bk)
            if not h:
                continue
            hits.append(f"{k}「{h}」")
        if w.get("min_acronyms"):
            acr = acronyms(text, bk)
            if len(acr) < int(w["min_acronyms"]):
                continue
            hits.append(f"科技縮寫 {acr}")
        return rule, hits
    return None, []


def _rule(bk: dict, rid: str) -> dict:
    return next((r for r in bk.get("rules") or [] if r.get("id") == rid), {"id": rid, "class": "OTHER", "base": 0.2})


def fine_type(text: str) -> tuple:
    """webscraping 型冊分類器(39 型)→ (code, scope) or ('', '') when absent."""
    m, _why = eng114()
    if m is None or not text:
        return "", ""
    try:
        ss = _MODS.get("eng114_ssot")
        if ss is None:
            ss = m.def_load_report_type_ssot()
            _MODS["eng114_ssot"] = ss
        r = m.def_classify_investment_report(text, "", ss)
        return r.report_type_code, r.report_scope
    except Exception:
        return "", ""


def _fine_type_class(code: str, scope: str, bk: dict):
    fm = bk.get("fine_kind_map") or {}
    over = fm.get("ENG114_type_override") or {}
    if code in over:
        return over[code]
    return (fm.get("ENG114_scope") or {}).get(scope)


def classify(name: str, title: str = "", broker_hint: str = "", bk: dict | None = None) -> dict:
    """One document → class row (vrn_doc_class shape) + evidence."""
    bk = bk or book()
    classes = bk.get("classes") or {}
    cf = bk.get("confidence") or {}
    p = Path(str(name))
    stem = p.stem if p.suffix.lower() in SAMPLE_EXT else str(name)
    stem = unicodedata.normalize("NFKC", stem)
    tk, rej = ticker_of(stem, bk)
    f_rule, f_hits = ladder(stem, tk, bk)
    t_rule, t_hits, ttk = None, [], ""
    if title:
        ttk, _trej = ticker_of(title, bk, bool((bk.get("ticker") or {}).get("title_ticker_requires_mark", True)))
        t_rule, t_hits = ladder(title, ttk, bk)
    m73, _w73 = eng073()
    fine73 = m73.classify_kind(stem, tk) if m73 else ("", "")
    ft_code, ft_scope = fine_type((stem + " " + (title or "")).strip())
    ft_cls = _fine_type_class(ft_code, ft_scope, bk) if ft_code else None
    src, adj, notes = "filename", 0.0, []
    if f_rule:
        rule, hits, cls = f_rule, f_hits, f_rule["class"]
    elif t_rule:
        rule, hits, cls, src = t_rule, t_hits, t_rule["class"], "title"
        adj += cf.get("title_only", -0.05)
        tk = ttk if cls == "STOCK" else tk
    elif ft_cls:
        rule, hits, cls, src = _rule(bk, "DC-R10"), [f"細型 {ft_code}({ft_scope})"], ft_cls, "fine_type"
    else:
        rule, cls = _rule(bk, "DC-R99"), "OTHER"
        hits = ["無代號 · 無型別詞 · 無細型投票"]
    conflict = bool(f_rule and t_rule and t_rule["class"] != f_rule["class"])
    if conflict:
        adj += cf.get("title_conflict", -0.10)
        notes.append(f"首頁標題判 {t_rule['class']}({t_rule['id']})≠ 檔名")
    map73 = ((bk.get("fine_kind_map") or {}).get("ENG073") or {}).get(fine73[0]) if fine73[0] else None
    if map73:
        adj += cf.get("agree_eng073", 0.03) if map73 == cls else cf.get("disagree_eng073", -0.15)
        if map73 != cls:
            notes.append(f"ENG073 細型「{fine73[0]}」→ {map73}")
    if ft_cls and src != "fine_type":
        adj += cf.get("agree_fine_type", 0.02) if ft_cls == cls else 0.0
    m73b = m73.parse_broker(stem) if m73 else ""
    broker = m73b or (broker_hint or "")
    if cls == "STOCK" and broker:
        adj += cf.get("broker_present_stock", 0.02)
    conf = max(cf.get("floor", 0.05), min(cf.get("cap", 0.99), float(rule.get("base", 0.2)) + adj))
    needs_review = bool(cls == "OTHER" or conf < cf.get("review_below", 0.6) or conflict or (classes.get(cls) or {}).get("review"))
    date = ""
    if m73:
        try:
            date = m73.parse_date(stem) or ""
        except Exception:
            date = ""
    ev = [f"{src}:{h}" for h in hits] + ([f"代號守衛擋 {', '.join(rej)}"] if rej else []) + ([f"券商 {broker}"] if broker else []) + notes
    return {
        "report_file": str(name), "doc_class": cls, "doc_class_zh": (classes.get(cls) or {}).get("zh", cls),
        "class_confidence": round(conf, 3), "class_rule": rule.get("id", ""), "class_evidence": " · ".join(ev) or "(none)",
        "route": (classes.get(cls) or {}).get("route", "review"), "needs_review": needs_review,
        "fine_kind_eng073": fine73[0] or None, "fine_type_eng114": ft_code or None,
        "ticker": (tk or None) if cls == "STOCK" else None, "broker_raw": broker or None, "report_date": date or None,
        "stock_fields_state": "STOCK_LANE" if cls == "STOCK" else "NULL:NOT_STOCK_CLASS",
        "title_class": t_rule["class"] if t_rule else None, "conflict": conflict,
    }


def stock_fields_null(row: dict, bk: dict | None = None) -> dict:
    """Stock-only fields on a non-stock row are NULL — never guessed (the book's stock_only_fields)."""
    bk = bk or book()
    if row.get("doc_class") != "STOCK":
        for f in bk.get("stock_only_fields") or []:
            row[f] = None
    return row


# ---------------------------------------------------------------- numeric cells

def parse_num(text, bk: dict | None = None) -> tuple:
    """Whole cell is one number → (Fraction, unit); otherwise (None, '')."""
    spec = ((bk or book()).get("xcheck") or {}).get("numeric_cell") or {}
    s = unicodedata.normalize("NFKC", ZW_RX.sub("", str(text or ""))).strip()
    s = re.sub(r"\s+", "", s)
    if not s:
        return None, ""
    for ch in spec.get("minus_chars", "−–—－"):
        s = s.replace(ch, "-")
    neg = False
    if spec.get("neg_paren", True) and len(s) > 2 and s[0] in "(（" and s[-1] in ")）":
        neg, s = True, s[1:-1]
    sign = ""
    if s[:1] in "+-":
        sign, s = s[0], s[1:]
    for pre in sorted(spec.get("strip_prefix") or [], key=len, reverse=True):
        if s.upper().startswith(pre.upper()):
            s = s[len(pre):]
            break
    if not sign and s[:1] in "+-":
        sign, s = s[0], s[1:]
    unit = ""
    for suf in sorted(spec.get("strip_suffix") or [], key=len, reverse=True):
        if s.endswith(suf):
            unit, s = suf, s[:-len(suf)]
            break
    rx = spec.get("rx") or r"^[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$"
    if not re.fullmatch(rx, s):
        return None, ""
    try:
        v = Fraction(Decimal(s.replace(",", "")))
    except (InvalidOperation, ValueError):
        return None, ""
    if sign == "-":
        v = -v
    return (-v if neg else v), unit


def _fmt(v) -> str:
    try:
        return f"{float(v):.10g}"
    except (OverflowError, ValueError, TypeError):
        return str(v)


def reldiff(a: Fraction, b: Fraction) -> float:
    if a == b:
        return 0.0
    den = max(abs(a), abs(b))
    try:
        return float(abs(a - b) / den)
    except (OverflowError, ZeroDivisionError):
        return float("inf")


def triple_check(cells: dict, seed: int, prio: list, group: int = 3, tol: float = 1e-9, passes: int = 2) -> dict:
    """cells: {cell_id: {method: (Fraction, unit, raw)}} — only MULTI cells (≥2 methods numeric).
    Shuffle with seed (pass k uses seed+k), take `group` at a time until all are used, compare each method's product."""
    ids = sorted(cells)

    def drill(g):
        out = []
        for cid in g:
            vals = cells[cid]
            ms = [m for m in prio if m in vals] + [m for m in vals if m not in prio]
            ref = vals[ms[0]]
            if any((vals[m][0] != ref[0]) or (vals[m][1] != ref[1]) for m in ms[1:]):
                out.append({"cell": cid, "values": {m: vals[m][2] for m in ms}})
        return out

    res = []
    for k in range(max(1, passes)):
        order = ids[:]
        random.Random(seed + k).shuffle(order)
        groups = [order[i:i + group] for i in range(0, len(order), group)]
        trip = []
        for gi, g in enumerate(groups, 1):
            rec = {"g": gi, "cells": g, "size": len(g)}
            common = [m for m in prio if all(m in cells[c] for c in g)]
            common += [m for m in sorted({m for c in g for m in cells[c]}) if m not in common and all(m in cells[c] for c in g)]
            if len(common) >= 2:
                prods = {}
                for m in common:
                    p = Fraction(1)
                    for c in g:
                        p *= cells[c][m][0]
                    prods[m] = p
                ref = prods[common[0]]
                rel = max(reldiff(ref, prods[m]) for m in common[1:])
                zero = any(cells[c][m][0] == 0 for c in g for m in common)
                rec.update(methods=common, products={m: _fmt(v) for m, v in prods.items()}, rel_diff=rel)
                state = "MISMATCH" if rel > tol else "ZERO_DRILL" if zero else "MATCH"
            else:
                state = "UNDER_COVERED"
            rec["state"] = state
            if state != "MATCH":
                rec["drill"] = drill(g)
            trip.append(rec)
        res.append({"pass": k + 1, "seed": seed + k, "groups": len(groups),
                    "last_group_size": len(groups[-1]) if groups else 0, "triples": trip})
    diff_cells = sorted({d["cell"] for p in res for t in p["triples"] for d in t.get("drill") or []})
    return {
        "seed": seed, "group_size": group, "passes": res, "rel_tol": tol,
        "triples": res[0]["groups"] if res else 0,
        "last_group_size": res[0]["last_group_size"] if res else 0,
        "last_group_short": bool(res and res[0]["groups"] and res[0]["last_group_size"] < group),
        "triples_mismatch": sum(1 for p in res for t in p["triples"] if t["state"] == "MISMATCH"),
        "zero_drills": sum(1 for p in res for t in p["triples"] if t["state"] == "ZERO_DRILL"),
        "under_covered": sum(1 for p in res for t in p["triples"] if t["state"] == "UNDER_COVERED"),
        "cell_diffs": diff_cells,
    }


# ---------------------------------------------------------------- table methods (page 1)

def _fitz():
    try:
        import pymupdf as fz            # the maintained name (fitz alias is deprecated upstream)
        return fz
    except Exception:
        try:
            import fitz as fz
            return fz
        except Exception:
            return None


def page1_fitz(path: Path) -> dict:
    """fitz page 1: tables (grid + cell boxes) and words. {'tables': [...], 'words': [...], 'why': ''}."""
    fz = _fitz()
    if fz is None:
        return {"tables": [], "words": [], "why": "ABSENT(No module named 'fitz')"}
    try:
        with fz.open(str(path)) as doc:
            if not doc.page_count:
                return {"tables": [], "words": [], "why": "0 頁"}
            page = doc[0]
            tabs = []
            try:
                found = page.find_tables().tables
            except Exception as exc:
                found = []
                why = f"find_tables {type(exc).__name__}"
            else:
                why = ""
            for t in found:
                grid = [[(c or "").strip() for c in row] for row in t.extract()]
                boxes = [list(r.cells) for r in t.rows]
                tabs.append({"bbox": tuple(t.bbox), "grid": grid, "boxes": boxes})
            words = [(w[0], w[1], w[2], w[3], w[4]) for w in page.get_text("words")]
            return {"tables": tabs, "words": words, "why": why}
    except Exception as exc:
        return {"tables": [], "words": [], "why": f"讀不開 {type(exc).__name__}: {str(exc)[:80]}"}


def _inside(w, box, pad=1.0) -> bool:
    if not box:
        return False
    xc, yc = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
    return box[0] - pad <= xc <= box[2] + pad and box[1] - pad <= yc <= box[3] + pad


def words_grid(tab: dict, words: list) -> tuple:
    """Independent geometry: words inside the table frame → rows by line gaps, columns by x-projection gaps.
    Shape differs from fitz_tables → fall back to fitz cell boxes (grid='borrowed'). Returns (grid, mode)."""
    ws = [w for w in words if _inside(w, tab["bbox"])]
    shape = (len(tab["grid"]), max((len(r) for r in tab["grid"]), default=0))
    if ws:
        hs = sorted(w[3] - w[1] for w in ws)
        h = hs[len(hs) // 2] or 8.0
        rows = []
        for w in sorted(ws, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
            yc = (w[1] + w[3]) / 2
            if rows and abs(yc - rows[-1]["yc"]) <= 0.6 * h:
                rows[-1]["w"].append(w)
            else:
                rows.append({"yc": yc, "w": [w]})
        spans = []
        gap = max(3.0, 0.5 * h)
        for w in sorted(ws, key=lambda w: w[0]):
            if spans and w[0] <= spans[-1][1] + gap:
                spans[-1][1] = max(spans[-1][1], w[2])
            else:
                spans.append([w[0], w[2]])
        if (len(rows), len(spans)) == shape:
            grid = []
            for r in rows:
                cells = [[] for _ in spans]
                for w in sorted(r["w"], key=lambda w: w[0]):
                    xc = (w[0] + w[2]) / 2
                    ci = next((i for i, s in enumerate(spans) if s[0] - 0.5 <= xc <= s[1] + 0.5), None)
                    if ci is not None:
                        cells[ci].append(w[4])
                grid.append([" ".join(c) for c in cells])
            return grid, "own"
    grid = []
    for row in tab.get("boxes") or []:
        grid.append([" ".join(w[4] for w in sorted((w for w in words if _inside(w, box, 0.5)), key=lambda w: (w[1], w[0])))
                     if box else "" for box in row])
    return grid, "borrowed"


def plumber_tables(path: Path) -> tuple:
    """ENG072 法B tables (pdfplumber). (tables | None, why)."""
    m72, why = eng072()
    if m72 is None:
        return None, f"ENG072 缺({why})"
    ok = getattr(m72, "_plumber_ok", None)
    if ok is not None and not ok():
        return None, "ABSENT(No module named 'pdfplumber')"
    try:
        r = m72.extract_page1_plumber(path)
    except Exception as exc:
        return None, f"法B {type(exc).__name__}"
    if r is None:
        return None, "法B 無結果"
    return [[[str(c or "").strip() for c in row] for row in t] for t in (r.get("tables") or [])], ""


def recorded_tables(jsonl: Path) -> tuple:
    """External extractor cells jsonl (table_id,row,column,text; 1-based; page 1 only when a page field exists)."""
    try:
        rows = [json.loads(ln) for ln in Path(jsonl).read_text(encoding="utf-8").splitlines() if ln.strip()]
    except (OSError, ValueError) as exc:
        return None, f"讀不開 {type(exc).__name__}"
    order, cells = [], {}
    for r in rows:
        if r.get("page") not in (None, 1, "1"):
            continue
        tid = r.get("table_id")
        if tid not in cells:
            order.append(tid)
            cells[tid] = {}
        cells[tid][(int(r["row"]) - 1, int(r["column"]) - 1)] = str(r.get("text") or "").strip()
    out = []
    for tid in order:
        nr = max(k[0] for k in cells[tid]) + 1
        nc = max(k[1] for k in cells[tid]) + 1
        out.append([[cells[tid].get((i, j), "") for j in range(nc)] for i in range(nr)])
    return out, ""


def align(primary: list, other: list) -> dict:
    """primary table index → other table index (same column count; same row count, or other truncated at 30 rows)."""
    used, out = set(), {}
    for ti, P in enumerate(primary):
        pc = max((len(r) for r in P), default=0)
        best = None
        for oj, O in enumerate(other):
            if oj in used or max((len(r) for r in O), default=0) != pc:
                continue
            if len(O) != len(P) and not (len(O) == 30 and len(P) > 30):
                continue
            score = sum(1 for i in range(min(len(P), len(O))) for j in range(min(len(P[i]), len(O[i])))
                        if _norm(P[i][j]).replace(" ", "") == _norm(O[i][j]).replace(" ", ""))
            if best is None or score > best[0]:
                best = (score, oj)
        if best and best[0] > 0:
            out[ti] = best[1]
            used.add(best[1])
    return out


def build_cells(methods: dict, prio: list, bk: dict) -> dict:
    """methods: {name: [grid, …]}. Primary = first method (priority order) with a table.
    Returns {'primary', 'aligned', 'cells': {cid: {m: (v, unit, raw)}}, 'states': {cid: state}}."""
    order = [m for m in prio if m in methods and methods[m]] + \
            [m for m in methods if m not in prio and methods[m] and not any(m.startswith(p.rstrip("*")) for p in prio if p.endswith("*"))] + \
            [m for p in prio if p.endswith("*") for m in methods if m.startswith(p.rstrip("*")) and methods[m] and m not in prio]
    seen = []
    for m in order:
        if m not in seen:
            seen.append(m)
    order = seen
    if not order:
        return {"primary": None, "aligned": {}, "cells": {}, "states": {}, "order": []}
    primary = order[0]
    P = methods[primary]
    aligned = {primary: {i: i for i in range(len(P))}}
    for m in order[1:]:
        aligned[m] = align(P, methods[m])
    cells, states = {}, {}
    for ti, grid in enumerate(P):
        for r, row in enumerate(grid):
            for c, _txt in enumerate(row):
                cid = f"T{ti + 1}R{r + 1}C{c + 1}"
                seen_m, vals = [], {}
                for m in order:
                    oj = aligned[m].get(ti)
                    if oj is None:
                        continue
                    G = methods[m][oj]
                    if r >= len(G) or c >= len(G[r]):
                        continue
                    seen_m.append(m)
                    v, unit = parse_num(G[r][c], bk)
                    if v is not None:
                        vals[m] = (v, unit, G[r][c])
                if not vals:
                    continue
                cells[cid] = vals
                states[cid] = "MULTI" if len(vals) >= 2 else ("PRESENCE_DIFF" if len(seen_m) >= 2 else "SINGLE_SOURCE")
    return {"primary": primary, "aligned": {m: {f"T{k + 1}": f"T{v + 1}" for k, v in a.items()} for m, a in aligned.items()},
            "cells": cells, "states": states, "order": order}


def default_seed(path: Path) -> int:
    try:
        size = Path(path).stat().st_size
    except OSError:
        size = 0
    return int(hashlib.sha256(f"{Path(path).name}|{size}".encode("utf-8")).hexdigest()[:8], 16)


# ---------------------------------------------------------------- first-page text (ENG392 + ENG072)

def text_verify(path: Path) -> dict:
    out = {"text_state": "NODATA", "text_lamp": "NODATA", "text_coverage": None, "text_numbers_missing": None,
           "text_quality": None, "zones_xcheck": "NODATA", "title": "", "page1_restored": "", "notes": []}
    m392, w392 = eng392()
    if m392 is None:
        out["notes"].append(f"ENG392 缺({w392})")
    else:
        try:
            doc = m392.audit_doc(path)
            pg = (doc.get("pages") or [{}])[0]
            st = pg.get("state") or doc.get("state") or "NODATA"
            q = pg.get("quality") or {}
            out.update(text_state=st, text_lamp=m392.LAMP.get(st, "NODATA"), text_coverage=pg.get("coverage"),
                       text_numbers_missing=len(pg.get("numbers_missing") or []) if "numbers_missing" in pg else None,
                       text_quality=(f"{q.get('grade')} {q.get('score')}" if q else None), page1_restored=doc.get("page1") or "",
                       numbers_missing_list=pg.get("numbers_missing") or [], eng072_file=(doc.get("eng072") or {}).get("state"))
            if doc.get("why"):
                out["notes"].append(doc["why"])
        except Exception as exc:
            out["notes"].append(f"ENG392 audit_doc {type(exc).__name__}: {str(exc)[:80]}")
    if Path(path).suffix.lower() != ".pdf":
        out["zones_xcheck"] = "N/A(非 PDF)"
        return out
    m72, w72 = eng072()
    if m72 is None:
        out["zones_xcheck"] = f"NODATA(ENG072 缺:{w72})"
        return out
    try:
        a = m72.extract_page1_zones(path)
    except Exception:
        a = None
    try:
        b = m72.extract_page1_plumber(path)
    except Exception:
        b = None
    out["_plumber"] = b
    if a:
        heads = [h.get("text", "") for h in (a.get("heads") or [])][:3]
        out["title"] = (" ".join(heads) + " " + str(a.get("header") or ""))[:300].strip()
    if a and b:
        cz = m72.compare_zones(a, b)
        worst = min((v.get("verdict") for v in cz.values()), key=lambda v: {"DIVERGE": 0, "PARTIAL": 1, "AGREE": 2, "BOTH_EMPTY": 3}.get(v, 3))
        out["zones_xcheck"] = f"{worst}(" + " · ".join(f"{k} {v['ratio']}" for k, v in cz.items()) + ")"
    elif a:
        absent = getattr(m72, "_plumber_ok", lambda: True)() is False
        out["zones_xcheck"] = "SINGLE(法B 缺件:本境沒有 pdfplumber)" if absent else "SINGLE(法B 無字)"
    else:
        out["zones_xcheck"] = "NODATA(法A 無文字層)"
    return out


# ---------------------------------------------------------------- one document

def verify_doc(path: Path, seed: int | None = None, recorded: dict | None = None, bk: dict | None = None,
               broker_hint: str = "") -> dict:
    bk = bk or book()
    xc = bk.get("xcheck") or {}
    prio = xc.get("methods_priority") or ["fitz_tables", "pdfplumber_tables", "fitz_words_grid", "recorded:*"]
    path = Path(path)
    tv = text_verify(path)
    cls = stock_fields_null(classify(path.name, tv.get("title") or "", broker_hint, bk), bk)
    methods, avail, modes = {}, {}, {}
    if path.suffix.lower() == ".pdf":
        fz = page1_fitz(path)
        if fz["tables"]:
            methods["fitz_tables"] = [t["grid"] for t in fz["tables"]]
            wg = [words_grid(t, fz["words"]) for t in fz["tables"]]
            methods["fitz_words_grid"] = [g for g, _m in wg]
            modes = {f"T{i + 1}": m for i, (_g, m) in enumerate(wg)}
        avail["fitz_tables"] = f"{len(fz['tables'])}" if not fz["why"] else fz["why"]
        avail["fitz_words_grid"] = (f"{len(fz['tables'])}(" + ",".join(f"{k}:{v}" for k, v in modes.items()) + ")") if modes else "0(沒有表框)"
        pl = tv.pop("_plumber", None)
        if pl is not None:
            plt = [[[str(c or "").strip() for c in row] for row in t] for t in (pl.get("tables") or [])]
            why = ""
        else:
            plt, why = plumber_tables(path)
        if plt:
            methods["pdfplumber_tables"] = plt
        avail["pdfplumber_tables"] = why or f"{len(plt or [])}"
    else:
        tv.pop("_plumber", None)
        avail["tables"] = "N/A(非 PDF:本支只核 PDF 首頁表格)"
    for name, jp in (recorded or {}).items():
        rt, why = recorded_tables(Path(jp))
        key = f"recorded:{name}"
        if rt:
            methods[key] = rt
        avail[key] = why or f"{len(rt or [])}"
    bc = build_cells(methods, prio, bk)
    states = bc["states"]
    multi = {cid: v for cid, v in bc["cells"].items() if states[cid] == "MULTI"}
    seed = default_seed(path) if seed is None else int(seed)
    tc = triple_check(multi, seed, prio, int(xc.get("group_size", 3)), float(xc.get("rel_tol", 1e-9)), int(xc.get("passes", 2)))
    n_single = sum(1 for s in states.values() if s == "SINGLE_SOURCE")
    n_pres = sum(1 for s in states.values() if s == "PRESENCE_DIFF")
    n_tab_methods = sum(1 for m in methods if methods[m])
    reds, yellows = [], []
    if tv["text_lamp"] == "RED":
        reds.append(f"首頁文字 {tv['text_state']}(覆蓋 {tv['text_coverage']} · 數字缺 {tv['text_numbers_missing']})")
    if tc["cell_diffs"]:
        reds.append(f"乘積互核下鑽:{len(tc['cell_diffs'])} 格各法不同 {tc['cell_diffs'][:6]}")
    if n_pres:
        reds.append(f"PRESENCE_DIFF {n_pres} 格(另一法讀不到這個數)")
    if n_single:
        yellows.append(f"SINGLE_SOURCE {n_single} 格無法互核")
    if bc["cells"] and n_tab_methods < 2:
        yellows.append(f"表格可用方法 {n_tab_methods} 種(<2)")
    if tv["text_lamp"] in ("AMBER", "NODATA"):
        yellows.append(f"首頁文字 {tv['text_state']}")
    if str(tv["zones_xcheck"]).startswith("DIVERGE"):
        yellows.append("ENG072 兩法分區 DIVERGE")
    if cls["needs_review"]:
        yellows.append(f"分類待複核({cls['doc_class']} · 信心 {cls['class_confidence']})")
    verdict = "RED" if reds else "YELLOW" if yellows else "GREEN"
    why = " ; ".join(reds or yellows) or ("NO_NUMERIC_CELLS · 首頁文字完整" if not bc["cells"] else
                                          f"{len(multi)} 格全經 ≥2 法互核、{tc['triples']} 組 × {len(tc['passes'])} 輪乘積全符")
    row = {
        "report_file": path.name, "doc_class": cls["doc_class"], "text_state": tv["text_state"],
        "text_coverage": tv["text_coverage"], "text_numbers_missing": tv["text_numbers_missing"], "text_quality": tv["text_quality"],
        "zones_xcheck": tv["zones_xcheck"], "table_methods": " · ".join(f"{k}:{v}" for k, v in avail.items()) or "(none)",
        "tables": len(methods.get(bc["primary"]) or []) if bc["primary"] else 0,
        "numeric_cells": len(bc["cells"]), "multi_cells": len(multi), "single_source_cells": n_single,
        "presence_diffs": n_pres, "seed": seed, "triples": tc["triples"], "triples_mismatch": tc["triples_mismatch"],
        "zero_drills": tc["zero_drills"], "last_group_size": tc["last_group_size"], "cell_diffs": len(tc["cell_diffs"]),
        "verdict": verdict, "verdict_why": why,
    }
    restored = {}
    if bc["primary"]:
        for ti, grid in enumerate(methods[bc["primary"]]):
            restored[f"T{ti + 1}"] = grid
    return {"row": row, "class": cls, "text": {k: v for k, v in tv.items() if k != "page1_restored"},
            "page1_restored": tv.get("page1_restored", ""), "tables_restored": restored, "primary": bc["primary"],
            "aligned": bc["aligned"], "cell_states": states,
            "cells": {cid: {m: {"raw": v[2], "value": _fmt(v[0]), "unit": v[1]} for m, v in vals.items()} for cid, vals in bc["cells"].items()},
            "xcheck": tc}


# ---------------------------------------------------------------- inputs / outputs

def list_samples(dirs: list, exts: set) -> tuple:
    files, notes = [], []
    for d in dirs:
        p = Path(d)
        if not p.exists():
            notes.append(f"NODATA:樣本夾不在 {d}")
            continue
        if p.is_file():
            files.append(p)
            continue
        got = sorted(q for q in p.rglob("*") if q.is_file() and q.suffix.lower() in exts and not q.name.startswith(("~$", ".")))
        if not got:
            notes.append(f"NODATA:夾裡沒有可讀檔 {d}")
        files += got
    return files, notes


def load_basicinfo(path: Path) -> list:
    rows = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    rows = rows if isinstance(rows, list) else (rows.get("rows") or rows.get("records") or [])
    return [{"name": r.get("SourceFile") or r.get("file") or "", "broker": r.get("Broker") or "", "ticker_given": r.get("Ticker") or ""}
            for r in rows if (r.get("SourceFile") or r.get("file"))]


def header_check(rows: list, table: str, bk: dict) -> dict:
    """CGC_MDL249 check_table against this book's proposed header (pandas absent → SKIP)."""
    spec = ((bk.get("proposed_headers") or {}).get(table)) or {}
    lock_p = _tail(REG, "CGC_MDL249_DataFrameLock")
    m, why = _load(lock_p, "mdl249")
    if m is None or not spec:
        return {"lamp": "SKIP", "problems": [why if m is None else "提案表頭不在"]}
    try:
        import pandas as pd
    except Exception:
        return {"lamp": "SKIP", "problems": ["No module named 'pandas'"]}
    names = [c["name"] for c in spec.get("columns") or []]
    frame = pd.DataFrame([{k: r.get(k) for k in names} for r in rows], columns=names)
    return m.check_table(table, spec, frame=frame)


def write_out(out: Path, kind: str, payload: dict, lanes: dict | None = None) -> list:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    p = out / f"{kind}_latest.json"
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    written.append(p)
    if lanes is not None:
        ld = out / "lanes"
        ld.mkdir(exist_ok=True)
        for route, rows in lanes.items():
            q = ld / f"{route}.jsonl"
            q.write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows), encoding="utf-8")
            written.append(q)
    return written


def _opt(args: list, key: str, default=None):
    return args[args.index(key) + 1] if key in args and args.index(key) + 1 < len(args) else default


def _multi(args: list, key: str) -> list:
    return [args[i + 1] for i, a in enumerate(args) if a == key and i + 1 < len(args)]


def _names(args: list) -> list:
    if "--names" not in args:
        return []
    out = []
    for a in args[args.index("--names") + 1:]:
        if a.startswith("--"):
            break
        out.append(a)
    return out


def run_classify(args: list) -> int:
    bk = book()
    if not bk:
        print(json.dumps({"engine": ENGINE, "state": "ABSENT", "why": f"規則冊 {BOOK_GLOB} 不在"}, ensure_ascii=False))
        return 4
    samples = _multi(args, "--samples")
    items, src = [], ""
    if samples:
        files, notes = list_samples(samples, SAMPLE_EXT)
        for n in notes:
            print(f"  [輸入] {n}")
        if not files:
            print(json.dumps({"engine": ENGINE, "verb": "classify", "state": "NODATA", "samples": samples, "notes": notes}, ensure_ascii=False))
            return 2
        m72, _w = eng072()
        for f in files:
            title = ""
            if f.suffix.lower() == ".pdf" and m72 is not None and "--no-text" not in args:
                try:
                    z = m72.extract_page1_zones(f) or {}
                    title = (" ".join(h.get("text", "") for h in (z.get("heads") or [])[:3]) + " " + str(z.get("header") or ""))[:300]
                except Exception:
                    title = ""
            items.append({"name": f.name, "title": title, "broker": ""})
        src = " · ".join(samples)
    elif _names(args):
        items = [{"name": n, "title": "", "broker": ""} for n in _names(args)]
        src = "--names"
    else:
        bi_arg = _opt(args, "--basicinfo")
        bi = Path(bi_arg) if bi_arg and not bi_arg.startswith("--") else BASICINFO
        if not bi.exists():
            print(json.dumps({"engine": ENGINE, "verb": "classify", "state": "NODATA", "why": f"{bi} 不在"}, ensure_ascii=False))
            return 2
        items = [{"name": r["name"], "title": "", "broker": r["broker"]} for r in load_basicinfo(bi)]
        src = str(bi.name)
    rows = [stock_fields_null(classify(it["name"], it["title"], it["broker"], bk), bk) for it in items]
    counts = {c: sum(1 for r in rows if r["doc_class"] == c) for c in (bk.get("classes") or {})}
    uniq = {c: len({r["report_file"] for r in rows if r["doc_class"] == c}) for c in counts}
    seen, table_rows = set(), []
    for r in rows:                                   # the table is keyed by report_file: an input listed twice is one row
        if r["report_file"] not in seen:
            seen.add(r["report_file"])
            table_rows.append(r)
    lanes: dict = {c.get("route"): [] for c in (bk.get("classes") or {}).values()}
    for r in table_rows:
        lanes.setdefault(r["route"], []).append(r)
    hc = header_check(table_rows, "vrn_doc_class", bk)
    payload = {"engine": ENGINE, "verb": "classify", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "book": bk.get("_book"), "source": src, "n": len(rows), "counts": counts, "unique_counts": uniq,
               "review": sum(1 for r in rows if r["needs_review"]), "duplicates_in_input": len(rows) - len(table_rows),
               "header_check": {k: hc.get(k) for k in ("lamp", "problems", "rows")}, "rows": table_rows}
    if "--no-write" not in args:
        for p in write_out(Path(_opt(args, "--out") or OUT), "DOCCLASS", payload, lanes):
            print(f"  [寫出] {p}")
    if "--json" in args:
        print(json.dumps(payload, ensure_ascii=False, indent=1, default=str))
    for r in rows:
        print(f"  {r['doc_class']:<16} {r['class_confidence']:.2f} {r['class_rule']:<6} {'複核 ' if r['needs_review'] else ''}"
              f"{r['report_file']}  ← {r['class_evidence'][:110]}")
    dropped = len(table_rows) - sum(len(v) for v in lanes.values())
    print(f"[文件分類] 來源 {src} · {len(rows)} 件(去重 {len({r['report_file'] for r in rows})})· "
          + " · ".join(f"{c} {counts[c]}(去重 {uniq[c]})" for c in counts)
          + f" · 待複核 {payload['review']} · 丟棄 {dropped} · 表頭自核 {hc.get('lamp')} · 冊 {bk.get('_book')}")
    return 0 if dropped == 0 else 1


def run_verify(args: list) -> int:
    bk = book()
    if not bk:
        print(json.dumps({"engine": ENGINE, "state": "ABSENT", "why": f"規則冊 {BOOK_GLOB} 不在"}, ensure_ascii=False))
        return 4
    samples = _multi(args, "--samples")
    files, notes = list_samples(samples, VERIFY_EXT) if samples else ([], ["NODATA:沒給 --samples <夾>"])
    for n in notes:
        print(f"  [輸入] {n}")
    lim = _opt(args, "--limit")
    if lim:
        files = files[:int(lim)]
    if not files:
        print(json.dumps({"engine": ENGINE, "verb": "verify", "state": "NODATA", "samples": samples, "notes": notes}, ensure_ascii=False))
        return 2
    rec = {}
    for spec in _multi(args, "--recorded"):
        name, _, p = spec.partition("=")
        rec[name or Path(p).stem] = p
    seed = _opt(args, "--seed")
    docs = [verify_doc(f, None if seed is None else int(seed), rec, bk) for f in files]
    rows = [d["row"] for d in docs]
    hc = header_check(rows, "vrn_firstpage_xcheck", bk)
    hc2 = header_check([d["class"] for d in docs], "vrn_doc_class", bk)
    lanes: dict = {}
    for d in docs:
        lanes.setdefault(d["class"]["route"], []).append({**d["class"], "xcheck_verdict": d["row"]["verdict"]})
    tally = {v: sum(1 for r in rows if r["verdict"] == v) for v in ("GREEN", "YELLOW", "RED")}
    payload = {"engine": ENGINE, "verb": "verify", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "book": bk.get("_book"), "samples": samples, "n": len(rows), "tally": tally,
               "header_check": {"vrn_firstpage_xcheck": {k: hc.get(k) for k in ("lamp", "problems", "rows")},
                                "vrn_doc_class": {k: hc2.get(k) for k in ("lamp", "problems", "rows")}},
               "rows": rows,            # 平面列 = 表頭冊 vrn_firstpage_xcheck(CGC_MDL249 json 來源 table=rows)
               "class_rows": [d["class"] for d in docs],   # 平面列 = 表頭冊 vrn_doc_class(本批樣本)
               "docs": docs}
    if "--no-write" not in args:
        for p in write_out(Path(_opt(args, "--out") or OUT), "XCHECK", payload, lanes):
            print(f"  [寫出] {p}")
    if "--json" in args:
        print(json.dumps(payload, ensure_ascii=False, indent=1, default=str))
    for d in docs:
        r = d["row"]
        print(f"  {r['verdict']:<6} {r['report_file']} · {r['doc_class']} · 文字 {r['text_state']} 覆蓋 {r['text_coverage']} 品質 {r['text_quality']}"
              f" · 分區 {r['zones_xcheck'][:40]} · 表 {r['tables']} · 數字格 {r['numeric_cells']}(多法 {r['multi_cells']} · 單法 {r['single_source_cells']}"
              f" · 漏 {r['presence_diffs']})· 種子 {r['seed']} · {r['triples']} 組(末組 {r['last_group_size']} 格)× {len(d['xcheck']['passes'])} 輪"
              f" · 不符 {r['triples_mismatch']} · 含0下鑽 {r['zero_drills']} · 差異格 {r['cell_diffs']}")
        print(f"         方法 {r['table_methods']} · {r['verdict_why'][:160]}")
    print(f"[首頁互核] {len(rows)} 件 · GREEN {tally['GREEN']} · YELLOW {tally['YELLOW']} · RED {tally['RED']} · "
          f"表頭自核 xcheck {hc.get('lamp')} / doc_class {hc2.get('lamp')} · 冊 {bk.get('_book')}")
    if tally["RED"]:
        return 1
    return 0 if tally["YELLOW"] == 0 else 3


# ---------------------------------------------------------------- selftest

def _fixture_pdf(path: Path, rows: list, title: str = "Sector Outlook 2026") -> bool:
    fz = _fitz()
    if fz is None:
        return False
    doc = fz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((42, 70), title, fontsize=18)
    page.insert_text((42, 110), "This page body explains the quarterly figures in the table below.", fontsize=10)
    xs, y0, rh = [42, 180, 300, 420, 540], 300, 30
    ys = [y0 + i * rh for i in range(len(rows) + 1)]
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y))
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))
    for i, row in enumerate(rows):
        for j, txt in enumerate(row):
            page.insert_text((xs[j] + 6, ys[i] + 20), txt, fontsize=10)
    page.insert_text((42, ys[-1] + 30), "Source: selftest fixture", fontsize=8)
    doc.save(str(path))
    doc.close()
    return True


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:200]) if note else ''}")

    bk = book()
    classes = bk.get("classes") or {}
    chk("規則冊在 · 五類齊 · 每條規則的類在冊上 · OTHER 路由 = review(不丟棄)",
        bk and set(classes) == {"STOCK", "INDUSTRY_OUTLOOK", "NEWS_DIGEST", "OTHER_INVEST", "OTHER"}
        and all(r["class"] in classes or r["class"] == "@fine_type" for r in bk.get("rules") or [])
        and classes["OTHER"]["route"] == "review" and classes["OTHER"].get("never_drop"), bk.get("_book"))
    m73, w73 = eng073()
    m72, w72 = eng072()
    m392, w392 = eng392()
    m114, w114 = eng114()
    chk("正主尾版可讀(ENG073 代號/年份守衛 · ENG072 首頁分區 · ENG392 全文無遺漏;型冊分類器缺席照實寫)",
        m73 is not None and m72 is not None and m392 is not None, f"{w73} · {w72} · {w392} · 型冊 {w114}")
    real = {
        "【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822.pdf": ("STOCK", "3706"),
        "3014TT-20231005.pdf": ("STOCK", "3014"),
        "20251128兆豐訪談速報-神達(3706).pdf": ("STOCK", "3706"),
        "6933_AMAX-KY_個股介紹報告.pdf": ("STOCK", "6933"),
        "晶心科(6533,N,中立)-CTBC251208.pdf": ("STOCK", "6533"),
        "20251205兆豐晨會報告(一)-當日新聞與重要訊息評論.pdf": ("NEWS_DIGEST", None),
        "20251205兆豐晨會報告(二)-公司訪談摘要.pdf": ("NEWS_DIGEST", None),
        "20251208_台新台股盤勢分析.pdf": ("NEWS_DIGEST", None),
        "凱基期貨晨間解盤20251205.pdf": ("NEWS_DIGEST", None),
        "凱基美股分析20251205-Meta大砍元宇宙預算，標普、那指續漲.pdf": ("NEWS_DIGEST", None),
        "投資早報251209.pdf": ("NEWS_DIGEST", None),
        "Daiwa-PCB 20251204.pdf": ("INDUSTRY_OUTLOOK", None),
        "GS-AI PCB CCL 20251204.pdf": ("INDUSTRY_OUTLOOK", None),
        "GF-Thoughts on TPU Competition with GPU 20251126.pdf": ("INDUSTRY_OUTLOOK", None),
        "UBS-Asia Hardware Insights 20251205.pdf": ("INDUSTRY_OUTLOOK", None),
        "凱基投顧_鋼鐵產業_劉昃恩_20260518.pdf": ("INDUSTRY_OUTLOOK", None),
        "第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf": ("INDUSTRY_OUTLOOK", None),
        "第二場 2026海外投資展望 - 華南永昌海外商品部.pdf": ("INDUSTRY_OUTLOOK", None),
    }
    got = {n: classify(n, bk=bk) for n in real}
    bad = [f"{n}→{g['doc_class']}/{g['ticker']}" for n, g in got.items() if (g["doc_class"], g["ticker"]) != real[n]]
    chk("操作員真檔名 18 例:個股 / 新聞摘要 / 產業展望 判得對(代號只在個股列)", not bad, bad[:4])
    g = classify("2026_macro_investment_engine_v10.pdf", bk=bk)
    chk("年份守衛 YG-2:2026_macro… 的 2026 不是代號(聚亨)→ 其他投資", g["doc_class"] == "OTHER_INVEST" and g["ticker"] is None
        and "YG-2" in g["class_evidence"], g["class_evidence"])
    g = classify("凱基投顧_2002 中鋼_某某_20260519.pdf", bk=bk)
    chk("有代號記號(投顧_)的 2002 照舊是個股(守衛不誤殺)", g["doc_class"] == "STOCK" and g["ticker"] == "2002", g["class_evidence"])
    g = classify("兆豐晨會-2330台積電-2317鴻海.pdf", bk=bk)
    chk("強標記:晨會列一串代號仍是新聞摘要(代號不越過強標記)", g["doc_class"] == "NEWS_DIGEST" and g["ticker"] is None, g["class_rule"])
    g = classify("2330法人說明會.pdf", bk=bk)
    chk("法說是弱標記:有代號 = 個股", g["doc_class"] == "STOCK" and g["ticker"] == "2330")
    for n, want in (("元大台灣50 ETF 月報.pdf", "OTHER_INVEST"), ("全球債券基金策略.pdf", "OTHER_INVEST"), ("美元指數DXY分析模型.pdf", "OTHER_INVEST")):
        g = classify(n, bk=bk)
        chk(f"其他投資(無關個股):{n}", g["doc_class"] == want, f"{g['doc_class']} · {g['class_evidence']}")
    g = stock_fields_null(classify("隨手筆記.pdf", bk=bk), bk)
    chk("分不出來 = OTHER → review 車道 · 待複核 · 個股欄 NULL(不丟、不猜)", g["doc_class"] == "OTHER" and g["route"] == "review"
        and g["needs_review"] and all(g.get(f) is None for f in bk.get("stock_only_fields") or []), g["stock_fields_state"])
    g = classify("scan_0001.pdf", title="半導體產業展望 2026", bk=bk)
    chk("檔名沒證據 → 用首頁標題帶判(source=title,信心降)", g["doc_class"] == "INDUSTRY_OUTLOOK" and g["class_evidence"].startswith("title:"),
        f"{g['class_confidence']} · {g['class_evidence']}")
    g = classify("p766.pdf", title="Service Mining: Using Process Mining to Discover IEEE 2011", bk=bk)
    chk("首頁標題的裸四碼(2011)不是代號(YG-4:標題要有代號記號)→ 不判個股", g["doc_class"] != "STOCK", f"{g['doc_class']} · {g['class_evidence']}")
    g = classify("scan_0002.pdf", title="台積電 TSMC (2330 TT) 個股報告", bk=bk)
    chk("首頁標題帶記號的代號(2330 TT)→ 個股(source=title)", g["doc_class"] == "STOCK" and g["ticker"] == "2330", g["class_evidence"])
    g = classify("Daiwa-PCB 20251204.pdf", title="台積電(2330) 目標價 1,250", bk=bk)
    chk("檔名/標題互斥 → 照檔名判、標衝突、進複核", g["doc_class"] == "INDUSTRY_OUTLOOK" and g["conflict"] and g["needs_review"], g["class_evidence"])
    g = stock_fields_null(classify("Daiwa-PCB 20251204.pdf", bk=bk), bk)
    chk("非個股列:ticker / 評等 / 目標價 / 升幅 = NULL,狀態 NOT_STOCK_CLASS", all(g.get(f) is None for f in ("ticker", "rating_ssot_key", "target_price", "upside_calc"))
        and g["stock_fields_state"] == "NULL:NOT_STOCK_CLASS")
    pn = {"1,234": Fraction(1234), "(1,234)": Fraction(-1234), "12.5%": Fraction(25, 2), "NT$1,250": Fraction(1250), "－3.2": Fraction(-16, 5),
          "１２３": Fraction(123), "n.a.": None, "Q1": None, "2Q25": None, "-": None, "": None, "3.5x": Fraction(7, 2)}
    badp = {k: parse_num(k, bk)[0] for k in pn if parse_num(k, bk)[0] != pn[k]}
    chk("數字格解析:千分位 · 括號負數 · % · NT$ · 全形 · 倍數;Q1 / 2Q25 / n.a. / - 不算數字", not badp, badp)
    prio = ["A", "B"]
    cells7 = {f"c{i}": {"A": (Fraction(i + 2), "", str(i + 2)), "B": (Fraction(i + 2), "", str(i + 2))} for i in range(7)}
    t1 = triple_check(cells7, 12345, prio, 3, 1e-9, 2)
    t2 = triple_check(cells7, 12345, prio, 3, 1e-9, 2)
    t3 = triple_check(cells7, 999, prio, 3, 1e-9, 2)
    order = lambda t: [c for tr in t["passes"][0]["triples"] for c in tr["cells"]]
    chk("7 格兩法相同:3+3+1 組(末組 1 格照實寫)· 全符 · 同種子可重現、換種子換順序",
        t1["triples"] == 3 and t1["last_group_size"] == 1 and t1["last_group_short"] and not t1["cell_diffs"] and t1["triples_mismatch"] == 0
        and order(t1) == order(t2) and order(t1) != order(t3) and sorted(order(t1)) == sorted(cells7), order(t1))
    bad7 = json.loads(json.dumps({k: {m: [str(v[0]), v[1], v[2]] for m, v in d.items()} for k, d in cells7.items()}))
    bad7 = {k: {m: (Fraction(v[0]), v[1], v[2]) for m, v in d.items()} for k, d in bad7.items()}
    bad7["c3"]["B"] = (Fraction(99), "", "99")
    tb = triple_check(bad7, 12345, prio, 3, 1e-9, 1)
    mis = [tr for tr in tb["passes"][0]["triples"] if tr["state"] == "MISMATCH"]
    chk("改一格:那一組乘積不符 → 下鑽只指出那一格(c3:A=5 / B=99)", len(mis) == 1 and tb["cell_diffs"] == ["c3"] and mis[0]["rel_diff"] > 1e-9,
        mis[0]["drill"] if mis else tb)
    z = {"z0": {"A": (Fraction(0), "", "0"), "B": (Fraction(0), "", "0")}, "z1": {"A": (Fraction(5), "", "5"), "B": (Fraction(7), "", "7")},
         "z2": {"A": (Fraction(2), "", "2"), "B": (Fraction(2), "", "2")}}
    tz = triple_check(z, 1, prio, 3, 1e-9, 1)
    chk("含 0 的組:乘積都是 0(被遮蔽)→ 一律逐格下鑽,仍抓到 z1", tz["zero_drills"] == 1 and tz["cell_diffs"] == ["z1"] and tz["triples_mismatch"] == 0, tz["cell_diffs"])
    base12 = {f"s{i:02d}": {"A": (Fraction(i + 3), "", str(i + 3)), "B": (Fraction(i + 3), "", str(i + 3))} for i in range(12)}
    sw = {k: dict(v) for k, v in base12.items()}
    sw["s01"]["B"], sw["s02"]["B"] = (Fraction(5), "", "5"), (Fraction(4), "", "4")
    pick = None
    for s in range(500):
        tt = triple_check(sw, s, prio, 3, 1e-9, 2)
        g1 = next(tr for tr in tt["passes"][0]["triples"] if "s01" in tr["cells"])
        g2 = next(tr for tr in tt["passes"][1]["triples"] if "s01" in tr["cells"])
        if "s02" in g1["cells"] and "s02" not in g2["cells"]:
            pick = (s, g1, tt)
            break
    chk("同組兩格互換:第一輪乘積相同(遮蔽)· 第二輪 seed+1 重洗分開 → 抓到兩格", pick and pick[1]["state"] == "MATCH"
        and pick[2]["cell_diffs"] == ["s01", "s02"], f"seed {pick[0] if pick else None}")
    sc = build_cells({"fitz_tables": [[["Metric", "Q1"], ["Rev", "10"], ["GM", "5"]]]}, ["fitz_tables", "pdfplumber_tables"], bk)
    chk("只有一法 = SINGLE_SOURCE(不能互核,不算過)", set(sc["states"].values()) == {"SINGLE_SOURCE"} and len(sc["states"]) == 2, sc["states"])
    pc = build_cells({"fitz_tables": [[["Metric", "Q1"], ["Rev", "10"], ["GM", "5"]]],
                      "pdfplumber_tables": [[["Metric", "Q1"], ["Rev", "10"], ["GM", ""]]]}, ["fitz_tables", "pdfplumber_tables"], bk)
    chk("另一法對得上這張表、這格卻空白 = PRESENCE_DIFF", pc["states"].get("T1R3C2") == "PRESENCE_DIFF" and pc["states"].get("T1R2C2") == "MULTI", pc["states"])
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        rows = [["Metric", "Q1", "Q2", "Q3"], ["Revenue", "1,200", "1,350", "(80)"], ["Margin", "12.5%", "0", "13.1%"], ["EPS", "3.2", "3.4", "3.9"]]
        fx = tdp / "fixture_sector_outlook.pdf"
        made = _fixture_pdf(fx, rows)
        chk("自造首頁 PDF(格線表 4×4,9 個數字格,含 0 與括號負數)", made and fx.exists())
        if made:
            d = verify_doc(fx, None, None, bk)
            r = d["row"]
            plumber_absent = "ABSENT" in r["table_methods"]
            chk("fitz_tables × fitz_words_grid(自行分格)還原同一張表 · 9 格全多法 · 3 組 × 2 輪全符 · 含 0 組下鑽過",
                r["tables"] == 1 and r["numeric_cells"] == 9 and r["multi_cells"] == 9 and r["single_source_cells"] == 0
                and r["triples"] == 3 and r["last_group_size"] == 3 and r["triples_mismatch"] == 0 and r["cell_diffs"] == 0
                and "own" in r["table_methods"], r["table_methods"])
            chk("逐件總判:分類 產業/展望 · 文字完整 · 互核全符 → GREEN(pdfplumber 在就三法;缺件照實寫)",
                r["verdict"] == "GREEN" and r["doc_class"] == "INDUSTRY_OUTLOOK", f"{r['verdict']} · {r['verdict_why']} · 法B {'缺件' if plumber_absent else '在'}")
            chk("種子寫進輸出 · 預設種子可重現(檔名|位元組數)", r["seed"] == default_seed(fx) and verify_doc(fx, None, None, bk)["row"]["seed"] == r["seed"])
            rec = tdp / "cells.jsonl"
            lines = []
            for i, row in enumerate(rows, 1):
                for j, txt in enumerate(row, 1):
                    txt = "1,305" if txt == "1,350" else txt
                    lines.append(json.dumps({"table_id": "TBL-X", "page": 1, "row": i, "column": j, "text": txt}))
            rec.write_text("\n".join(lines) + "\n", encoding="utf-8")
            d2 = verify_doc(fx, 7, {"tamper": str(rec)}, bk)
            r2 = d2["row"]
            chk("外部擷取器格子改一個數(1,350→1,305):乘積不符 → 下鑽指出 T1R2C3 · RED", r2["verdict"] == "RED"
                and d2["xcheck"]["cell_diffs"] == ["T1R2C3"] and r2["triples_mismatch"] >= 1, r2["verdict_why"])
            hc = header_check([d["row"]], "vrn_firstpage_xcheck", bk)
            hc2 = header_check([d["class"]], "vrn_doc_class", bk)
            hcd = header_check([d["row"], d2["row"]], "vrn_firstpage_xcheck", bk)
            chk("表頭自核會抓主鍵重複(同一檔兩列 = RED;pandas 缺 = SKIP)", hcd["lamp"] in ("RED", "SKIP"), hcd.get("problems"))
            chk("列合提案表頭(CGC_MDL249 check_table;pandas 缺 = SKIP)", hc["lamp"] in ("GREEN", "SKIP") and hc2["lamp"] in ("GREEN", "SKIP")
                and hc2["problems"] != ["提案表頭不在"], f"xcheck {hc['lamp']} {hc.get('problems')} · doc_class {hc2['lamp']} {hc2.get('problems')}")
        syn = HERE / "references" / "intake" / "PDFRegressionEvidence_v1.0.0_b245" / "PDFRegressionEvidence_v1.0.0"
        if (syn / "synthetic_financial_report.pdf").exists():
            d3 = verify_doc(syn / "synthetic_financial_report.pdf", None, {"table_cells": str(syn / "04_table" / "table_cells.jsonl")}, bk)
            r3 = d3["row"]
            chk("正典合成樣本(唯讀):fitz × 字詞分格 × 外部擷取器 三法 · 6 格 · 2 組全符", r3["multi_cells"] == 6 and r3["triples"] == 2
                and r3["cell_diffs"] == 0 and r3["presence_diffs"] == 0 and "recorded:table_cells:1" in r3["table_methods"],
                f"{r3['verdict']} · {r3['table_methods']} · {r3['verdict_why'][:80]}")
        else:
            chk("正典合成樣本不在 → 照實略過(不冒充)", True, "SKIP")
        old = dict(os.environ)
        try:
            os.environ["VIA_FROM_VCGC"] = "YES"
            rc_nd = run_verify(["verify", "--samples", str(tdp / "不存在的夾"), "--no-write"])
            rc_nc = run_classify(["classify", "--samples", str(tdp / "不存在的夾"), "--no-write"])
        finally:
            os.environ.clear()
            os.environ.update(old)
        chk("樣本夾不在 → NODATA rc=2(verify 與 classify 都照實)", rc_nd == 2 and rc_nc == 2)
    if BASICINFO.exists():
        rows = [stock_fields_null(classify(r["name"], "", r["broker"], bk), bk) for r in load_basicinfo(BASICINFO)]
        cnt = {c: sum(1 for r in rows if r["doc_class"] == c) for c in classes}
        chk("操作員 76 份真檔名:全數分完、零丟棄、非個股列無代號", len(rows) == 76 and sum(cnt.values()) == 76
            and all(r["ticker"] is None for r in rows if r["doc_class"] != "STOCK"), cnt)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("政策:加速器橋 · VIA_FROM_VCGC 閘 · 不匯入 TA-Lib · 零網路(不讀同意閘)", "[VIA:ACCEL-BRIDGE:v0100]" in body and 'os.environ.get("VIA_FROM_VCGC")' in body
        and not re.search(r"^\s*(import|from)\s+ta" + "lib", body, re.M) and ("VIA_NET_" + "CONSENT") not in body)
    old = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        rc_deny = main(["classify", "--no-write"])
    finally:
        if old is not None:
            os.environ["VIA_FROM_VCGC"] = old
    chk("不經 VCGC 直呼 = DENY(自測例外)", rc_deny == 2)
    n_ok = sum(ok)
    print(f"[{FAMILY} {VER}] 自測 {n_ok}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "engine": ENGINE, "state": "DENY", "why": "only via-vcgc(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = args[0] if args and not args[0].startswith("-") else "classify"
    if verb == "classify":
        return run_classify(args)
    if verb == "verify":
        return run_verify(args)
    print(f"  用法:{ENGINE} classify|verify [--samples <夾>] … | --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
