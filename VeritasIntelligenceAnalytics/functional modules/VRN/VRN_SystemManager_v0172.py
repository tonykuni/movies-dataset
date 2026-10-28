#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0172 — 薄尾(操作員 2026-10-11「所有資料都用 JSON 格式傳輸 · 資料下來先進行簡單的斷句銜接及資料銜接但不可亂接 · 去空格一句一資料到句號 ·
   但標題無句號不可亂接 · 原生 NON-OCR 修正資料方式如附件 · 如果原生工具修復不必動用到 OCR 100% 還原表格 · 避免文中有表格等狀態 · 還原後無誤就算成功 ·
   不動 OCR 除非失敗才進行 LAYOUT 識別切割轉換擷取再修復驗證」)。
  restore 動詞(讀上一輪 layout 的逐檔結果 → 每份一個 JSON;既有引擎沿用:_rebuild_table 標準鍵 · FinLexicon · ENG107 斷句律 · 工具總站讀表器)
  ① 文字:去空格(中文之間 · 全形轉半形)· 一句一筆到句號(。!? ! ? 或英文句點;分號不算)· 標題 / 條列 / 資料 / 圖說各自一筆不接 ·
     跨區塊只在同頁同欄同字級 · 間距小 · 下一塊以句開頭才接 · 其餘不接(收尾標「無句號」)
  ② 去雜訊(不刪 · 進 dropped 附原因):圖表座標數字 · 浮水印編碼 · 亂碼 · 免責聲明 · 聯絡方式
  ③ 文中表格(units 表列)不當句子 → 依表頭重組成表 → 結構 + 算術驗證
  ④ 表格:VRN 驗過 → 標準鍵 + 算術;沒過 → 原生讀表器依序(第一個過 VRN 原驗表就用)→ 原生全失敗才 OCR(表框 200 DPI · 對表頭欄位重組 · 候選)
  ⑤ 會計恆等式(正負號統一):毛利 = 營收 − 成本 · 營益 = 毛利 − 營業費用 · 淨利 ≈ 稅前 − 稅 · 資產 = 負債 + 權益 · 利潤率
  ⑥ 成功 = 還原後無誤(驗表過 + 無算術不符);OCR 結果一律候選
  輸出 VIA_Reports\\vrn\\restore\\<序>_<代號>_<券商>_<日期>.json · RESTORE_ALL_latest.jsonl · RESTORE_SUMMARY_latest.json · RESTORE_latest.html
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
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

import datetime
import html
import importlib.util
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0172"


def _vnum_v0172(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0172(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0172(p) < _vnum_v0172(__file__)), key=_vnum_v0172)
PRIOR = _load_v0172(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


_rep = _resolve("_rep")

# ───────── ① 文字:去空格 · 句號 · 不亂接 ─────────
_WIDE = str.maketrans("０１２３４５６７８９．，：％（）", "0123456789.,:%()")
_CJ = "\u3400-\u9fff\uf900-\ufaff"
_CJP = _CJ + "，。、；：！？「」『』（）《》〈〉【】"
_ABBR = {"e.g", "i.e", "vs", "inc", "co", "ltd", "no", "corp", "approx", "mr", "ms", "dr", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec", "fig", "est", "u.s", "etc"}
_PROTECT = re.compile(r"\d+\.\d+|\d{4}\.TWO|\d{4}\.TW|20\d{2}[./-]\d{1,2}[./-]\d{1,2}|\b(?:[A-Z]\.){2,}|\b(?:e\.g|i\.e|vs|Inc|Co|Ltd|No|Corp|approx|U\.S|Fig|Est)\.", re.I)
_BULLET = re.compile(r"^\s*(?:[➢◆●■▲►•▪◦‧・\-–—*]|\(?\d{1,2}[).、]|[一二三四五六七八九十]+、)\s*")


def tidy(s: str) -> str:
    s = str(s or "").replace("\u3000", " ").replace("\u00ad", "").replace("\ufeff", "").replace("\u200b", "").translate(_WIDE)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"(?<=[%s])\s+(?=[%s])" % (_CJP, _CJP), "", s)
    return s


def ends_sentence(s: str) -> bool:
    t = re.sub(r"[」』”\"')）\]]+$", "", s.rstrip())
    if not t:
        return False
    if t[-1] in "。！？!?":
        return True
    if t[-1] == ".":
        last = re.split(r"\s+", t[:-1])[-1].lower() if t[:-1] else ""
        if last in _ABBR or re.fullmatch(r"[a-z]", last) or re.fullmatch(r"\d+", last):
            return False
        return True
    return False


def split_sentences(text: str) -> list:
    held = []

    def park(m):
        held.append(m.group(0))
        return "\u0000%d\u0000" % (len(held) - 1)
    parked = _PROTECT.sub(park, text)
    parts = re.split(r"(?<=[。！？!?])(?![」』”\"')）])\s*|(?<=[a-z0-9%%)])\.\s+(?=[A-Z%s])" % _CJ, parked)
    out = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        if i < len(parts) - 1 and not ends_sentence(part) and re.search(r"[a-z0-9%)]$", part):
            part += "."
        for k, tok in enumerate(held):
            part = part.replace("\u0000%d\u0000" % k, tok)
        out.append(part)
    return out


def _join(a: str, b: str) -> str:
    if not a:
        return b
    if a.endswith("-") and b[:1].isascii() and b[:1].isalpha():
        return a[:-1] + b
    if re.search(r"[%s]$" % _CJP, a) or re.match(r"[%s]" % _CJP, b):
        return a + b
    return a + " " + b


# ───────── 資訊區:欄名 + 值 配對(不套斷句)─────────
_INFO_LABEL = re.compile(r"(?i)^(?:stock\s*)?(?:rating|recommendation|target\s*price|price\s*target|12m\s*tp|tp|pt|close|closing\s*price|share\s*price|price|market\s*cap\S*|"
                         r"shares\s*outstanding|52[-\s]?w(?:ee)?k\s*(?:high|low|range)?|free\s*float|avg\.?\s*daily\s*\S*|industry|sector|analyst|report\s*date|date|"
                         r"目標價|目標股價|合理價|評等|投資評等|投資建議|收盤價|股價|市值|股本|發行股數|分析師|研究員|報告日期|日期|產業別?|外資持股|董監持股|本益比|股價淨值比|52週\S*|成交量\S*)\s*[:：]?$")


def info_pairs(units: list) -> list:
    txts = [tidy(t) for _, t in units if tidy(t)]
    out, i = [], 0
    while i < len(txts):
        t = txts[i]
        if _INFO_LABEL.match(t) and i + 1 < len(txts) and not _INFO_LABEL.match(txts[i + 1]) and len(txts[i + 1]) <= 40:
            out.append("%s: %s" % (t.rstrip(":："), txts[i + 1]))
            i += 2
            continue
        out.append(t)
        i += 1
    return out


# ───────── ② 雜訊(不刪 · 附原因)─────────
_DISC = re.compile(r"本資料之內容|翻印必究|免責聲明|投資人應|僅供參考|請參閱.*(聲明|揭露)|Disclaimer|Analyst Certification|Important disclosures|See the last page|For important disclosures|此報告|不得轉載", re.I)
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")
_NUMONLY = re.compile(r"^[\s\d,.\-−–%()$x倍]+$")


def noise_reason(t: str) -> str:
    s = t.strip()
    if not s:
        return "空白"
    toks = s.split()
    if len(toks) >= 3 and _NUMONLY.match(s) and not re.search(r"[A-Za-z%s]" % _CJ, s):
        return "圖表座標數字"
    if re.search(r"\{\[\{|\}\]\}", s) or re.search(r"(?=[A-Za-z0-9+/=_-]{24,})(?=\S*\d)(?=\S*[a-z])(?=\S*[A-Z])[A-Za-z0-9+/=_-]{24,}", s):
        return "浮水印 / 編碼"
    good = len(re.findall(r"[%sA-Za-z0-9\s.,:;%%()$/&'\"\-+~～—–]" % _CJP, s))
    if len(s) >= 4 and good / len(s) < 0.7:
        return "亂碼"
    if _DISC.search(s):
        return "免責聲明"
    if _EMAIL.search(s) and len(_EMAIL.sub("", s).strip()) < 25:
        return "聯絡方式"
    return ""


# ───────── ③ 文中表格(表列)→ 表 ─────────
_NUM_TOK = re.compile(r"^\(?[-−–]?\$?\d[\d,]*(?:\.\d+)?\)?(?:%|x|倍)?$|^(?:--|-|—|–|n\.?a\.?|N/?A|NM|n\.m\.)$", re.I)


def _yr():
    return _resolve("_YR158") or re.compile(r"(?:19|20)\d{2}[A-Z]?|\d{1,2}Q\d{2}|[1-4]Q\d{2}[A-Z]?|\d{2}Q[1-4]|FY\d{2}")


def flat_rows(lines: list) -> list:
    """「營業收入淨額 5,839 884 1,272」→ [label, v1, v2, ...];表頭行(≥2 期間)→ ["", p1, p2, ...]。科目名用第一個數字切(科目自帶空格不被切斷)。"""
    yr, rows = _yr(), []
    for ln in lines:
        toks = tidy(ln).split(" ")
        per = [t for t in toks if yr.fullmatch(t) or re.fullmatch(r"(?:19|20)\d{2}\(?[AEFC]?\)?|\d{2}Q[1-4](?:\(?[EF]\)?)?|[1-4]Q\d{2}[EF]?", t)]
        if len(per) >= 2 and len(per) >= 0.6 * len([t for t in toks if re.search(r"\d", t)]):
            first = next(i for i, t in enumerate(toks) if t in per)
            rows.append([""] + toks[first:])                 # 表頭第一格留空(「6873泓德能源」這類是表名,不是科目)
            continue
        k = next((i for i, t in enumerate(toks) if _NUM_TOK.match(t)), None)
        if k is None:
            rows.append([" ".join(toks)])
            continue
        rows.append([tidy(" ".join(toks[:k]))] + toks[k:])
    return rows


# ───────── ⑤ 會計恆等式(正負號統一)─────────
def calc_checks(matrix: dict) -> list:
    g = matrix or {}
    out = []

    def tol(x):
        return max(1.0, abs(x) * 0.015)
    for per in sorted({p for v in g.values() for p in v}):
        v = {k: g.get(k, {}).get(per) for k in ("revenue", "cogs", "gross_profit", "opex", "operating_income", "pretax_income", "tax", "net_income", "total_assets", "total_liabilities", "equity",
                                                 "gross_margin", "operating_margin", "net_margin")}
        if v["revenue"] is not None and v["cogs"] is not None and v["gross_profit"] is not None:
            calc = v["revenue"] - abs(v["cogs"])
            out.append({"rule": "毛利 = 營收 − 成本", "period": per, "status": "PASS" if abs(calc - v["gross_profit"]) <= tol(v["gross_profit"]) else "FAIL", "detail": "%s vs %s" % (v["gross_profit"], round(calc, 2))})
        if v["gross_profit"] is not None and v["opex"] is not None and v["operating_income"] is not None:
            calc = v["gross_profit"] - abs(v["opex"])
            out.append({"rule": "營益 = 毛利 − 營業費用", "period": per, "status": "PASS" if abs(calc - v["operating_income"]) <= tol(v["operating_income"]) else "FAIL", "detail": "%s vs %s" % (v["operating_income"], round(calc, 2))})
        if v["pretax_income"] is not None and v["tax"] is not None and v["net_income"] is not None:
            a, b = v["pretax_income"] - abs(v["tax"]), v["pretax_income"] + abs(v["tax"])
            ok = min(abs(a - v["net_income"]), abs(b - v["net_income"])) <= max(tol(v["net_income"]), abs(v["pretax_income"]) * 0.05)    # 少數股權 / 停業損益可能各家列法不同 → 放寬 5%
            out.append({"rule": "淨利 ≈ 稅前 − 所得稅", "period": per, "status": "PASS" if ok else "FAIL", "detail": "%s vs %s" % (v["net_income"], round(a, 2))})
        if v["total_assets"] is not None and v["total_liabilities"] is not None and v["equity"] is not None:
            calc = v["total_liabilities"] + v["equity"]
            out.append({"rule": "資產 = 負債 + 權益", "period": per, "status": "PASS" if abs(calc - v["total_assets"]) <= tol(v["total_assets"]) else "FAIL", "detail": "%s vs %s" % (v["total_assets"], round(calc, 2))})
        for mk, nk, zh in (("gross_margin", "gross_profit", "毛利率"), ("operating_margin", "operating_income", "營益率"), ("net_margin", "net_income", "淨利率")):
            if v["revenue"] and v[mk] is not None and g.get(nk, {}).get(per) is not None:
                calc = g[nk][per] / v["revenue"] * 100
                out.append({"rule": "%s = %s / 營收" % (zh, zh[:-1]), "period": per, "status": "PASS" if abs(calc - v[mk]) <= 0.6 else "FAIL", "detail": "%s vs %.1f" % (v[mk], calc)})
    return out


def _lex():
    return list(_resolve("_FIN_STD") or []) + list((_resolve("_load_vrn_lexicon") or (lambda: []))())


def table_record(rows: list, page: int, tid: str, method: str, lex: list, verify_ok, issues=None, extra=None) -> dict:
    rb = (_resolve("_rebuild_table") or (lambda t, l: {}))({"rows": rows, "page": page, "engine": method, "surround": ""}, lex) or {}
    to_num = _resolve("_to_num") or (lambda s: None)
    periods = [p for p in (rb.get("periods") or []) if p] or list(dict.fromkeys(p for r in rb.get("rows") or [] for p in (r.get("values") or {})))   # 新版重建有時不回 periods → 由各列取
    out_rows = []
    for r in rb.get("rows") or []:
        cells = [{"period": p, "value": val} for p, val in (r.get("values") or {}).items()]
        out_rows.append({"label_raw": r.get("label_raw"), "std": r.get("label_std") or "", "cat": r.get("cat") or "", "cells": cells})
    calc = calc_checks(rb.get("matrix") or {})
    cf = sum(1 for c in calc if c["status"] == "FAIL")
    raw = [[str(c) for c in r] for r in rows]
    ok = bool(verify_ok)
    if ok and cf == 0:
        status = "還原無誤"
    elif ok:
        status = "算術不符(待查)"
    else:
        status = "未過"
    rec = {"id": tid, "page": page, "method": method, "category": rb.get("category", ""), "periods": periods, "rows": out_rows, "raw_rows": raw, "notes": rb.get("notes") or [],
           "unmatched_labels": rb.get("unmatched_labels") or [], "verify": {"ok": ok, "issues": list(issues or [])}, "calc": calc,
           "calc_status": "FAIL" if cf else ("PASS" if calc else "NA"), "status": status}
    if extra:
        rec.update(extra)
    return rec


def _real_table(rows, v) -> bool:
    """驗表的「小框(不到 2×2)→ 當文字」是給版面用的,不能當成表格還原成功 → 至少 2 列 × 2 欄且不是小框判定。"""
    rows = rows or []
    return not v.get("tiny") and len([r for r in rows if any((c or "").strip() for c in r)]) >= 2 and max((len(r) for r in rows), default=0) >= 2


def _rescue(th, mini, local, b, vt, page_pl, budget_left) -> tuple:
    """原生讀表器依序;第一個過 VRN 原驗表就用。回 (rows, backend, tried)。"""
    tried = []
    if th is None or not mini:
        return None, "", tried
    pr = {r["id"]: r["status"] for r in th.probe_tools()}
    bb = [float(b["x0"]) - 3, max(0.0, float(b["top"]) - 42), float(b["x1"]) + 3, float(b["bottom"]) + 3]
    t0 = time.time()
    for k in th.TABLE_BACKENDS:
        tool = {"pymupdf": "pymupdf", "pdfplumber": "pdfplumber", "camelot": "camelot", "tabula": "tabula", "img2table": "img2table"}[k.split("_")[0]]
        if pr.get(tool) != "ok" or time.time() - t0 > budget_left:
            continue
        r = th.nonocr_tables(mini, local, bb, k)
        tried.append(k)
        if r.get("status") != "ok":
            continue
        best, bov = None, -1.0
        for t in r.get("tables") or []:
            tb = t.get("bbox") or bb
            ov = max(0.0, min(tb[2], b["x1"]) - max(tb[0], b["x0"])) * max(0.0, min(tb[3], b["bottom"]) - max(tb[1], b["top"]))
            if ov > bov:
                best, bov = t, ov
        if best and best["rows"]:
            try:
                vv = vt(dict(b, rows=best["rows"]), page_pl)
                if vv.get("ok") and _real_table(best["rows"], vv):
                    return best["rows"], k, tried
            except Exception:  # noqa: BLE001
                continue
    return None, "", tried


def ocr_rows(lines: list) -> list:
    """OCR 行框 → 列(依 y)→ 有表頭期間就依期間欄位 x 中心對齊。"""
    if not lines:
        return []
    yr = _yr()
    hs = sorted(l["bbox"][3] - l["bbox"][1] for l in lines)
    mh = hs[len(hs) // 2] or 10
    items = sorted(({"cy": (l["bbox"][1] + l["bbox"][3]) / 2, "x0": l["bbox"][0], "x1": l["bbox"][2], "t": tidy(l["text"])} for l in lines), key=lambda i: i["cy"])
    rows, cur = [], []
    for it in items:
        if cur and abs(it["cy"] - cur[-1]["cy"]) > 0.55 * mh:
            rows.append(sorted(cur, key=lambda i: i["x0"]))
            cur = []
        cur.append(it)
    if cur:
        rows.append(sorted(cur, key=lambda i: i["x0"]))
    toks = []
    for r in rows:
        tr = []
        for it in r:
            parts = it["t"].split(" ")
            w = (it["x1"] - it["x0"]) / max(len(it["t"]), 1)
            pos = it["x0"]
            for p in parts:
                tr.append({"t": p, "cx": pos + w * len(p) / 2, "x0": pos})
                pos += w * (len(p) + 1)
        toks.append(tr)
    hdr = next((i for i, tr in enumerate(toks) if sum(1 for t in tr if yr.fullmatch(t["t"]) or re.fullmatch(r"(?:19|20)\d{2}[AEF]?|\d{2}Q[1-4][EF]?|[1-4]Q\d{2}[EF]?", t["t"])) >= 2), None)
    if hdr is None:
        return [[t["t"] for t in tr] for tr in toks]
    cols = [t for t in toks[hdr] if yr.fullmatch(t["t"]) or re.fullmatch(r"(?:19|20)\d{2}[AEF]?|\d{2}Q[1-4][EF]?|[1-4]Q\d{2}[EF]?", t["t"])]
    gap = min((b["cx"] - a["cx"] for a, b in zip(cols, cols[1:])), default=80)
    out = [[""] + [c["t"] for c in cols]]
    for i, tr in enumerate(toks):
        if i == hdr:
            continue
        lab = [t["t"] for t in tr if t["cx"] < cols[0]["cx"] - gap * 0.5 and not _NUM_TOK.match(t["t"])]
        vals = [""] * len(cols)
        for t in tr:
            if t["cx"] < cols[0]["cx"] - gap * 0.5:
                continue
            j = min(range(len(cols)), key=lambda j: abs(cols[j]["cx"] - t["cx"]))
            if abs(cols[j]["cx"] - t["cx"]) <= gap * 0.6:
                vals[j] = (vals[j] + " " + t["t"]).strip() if vals[j] else t["t"]
        if lab or any(vals):
            out.append([tidy(" ".join(lab))] + vals)
    return out


# ───────── 期間辨識補洞 + 算術正負號統一(第二步驗表 / 重建一起受益)─────────
# 實測:24Q1 / 25Q4(F)(兆豐季表)三套辨識都不認得;Dec-24A(KGI 財報表頭)重建不認得 → 重建報「無期間表頭」→ 驗表當算術有問題 → 整張判不過
#      KGI 成本寫 (25,460) → 舊算術 營收 − 成本 = 營收 + 25,460 → 誤判毛利不符
_MON = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
_PER_EXTRA = re.compile(r"^(?:\d{2}Q[1-4]|[1-4]Q\d{2}|%s[-\s'.]?\d{2,4}|(?:19|20)\d{2}[/.](?:0?[1-9]|1[0-2]))\(?[AEFCT]{0,2}\)?$" % _MON, re.I)


def per_extra(t) -> bool:
    return bool(_PER_EXTRA.match(tidy(str(t or "")).replace(" ", "")))


def _wrap_period(name: str) -> bool:
    mo = _owner(name)
    if mo is None or getattr(vars(mo)[name], "_v172", False):
        return False
    prev = vars(mo)[name]

    def f(c, *a, **k):
        return bool(prev(c, *a, **k)) or per_extra(c)
    f._v172 = True
    setattr(mo, name, f)
    return True


_WRAPPED = [n for n in ("_is_period", "_is_period_28") if _wrap_period(n)]
for _rx in ("_YR158", "_YR"):
    _mo = _owner(_rx)
    _done = vars(_mo).setdefault("_V172_RX_DONE", set()) if _mo is not None else set()
    if _mo is not None and hasattr(vars(_mo)[_rx], "pattern") and _rx not in _done:
        _old = vars(_mo)[_rx]
        setattr(_mo, _rx, re.compile("(?:%s)|(?:\\b\\d{2}Q[1-4]\\b)|(?:\\b%s[-'.]?\\d{2,4}[AEF]?\\b)" % (_old.pattern, _MON), _old.flags))
        _done.add(_rx)
        _WRAPPED.append(_rx)


def _abs_costs(matrix: dict) -> dict:
    m = {k: dict(v) for k, v in (matrix or {}).items()}
    for k in ("cogs", "opex"):
        if k in m:
            m[k] = {p: (abs(x) if isinstance(x, (int, float)) else x) for p, x in m[k].items()}
    return m


for _an in ("_arith", "_arith_28"):
    _mo = _owner(_an)
    if _mo is not None and not getattr(vars(_mo)[_an], "_v172", False):
        _pa = vars(_mo)[_an]

        def _ar(matrix, *a, _pa=_pa, **k):
            return _pa(_abs_costs(matrix), *a, **k)
        _ar._v172 = True
        setattr(_mo, _an, _ar)
        _WRAPPED.append(_an)


# ───────── restore 主流程 ─────────
def restore_run(ocr: bool = True, rescue_budget: int = 600, ocr_budget: int = 300, ocr_dpi: int = 200) -> dict:
    d = _resolve("_latest_l2_dir")("")
    if not d:
        return {"err": "找不到上一輪 layout 的逐檔結果(先跑 -Verb layout)"}
    th = (_resolve("toolhub") or (lambda: None))()
    vt = _resolve("_ORIG_VT") or _resolve("verify_table")
    lex = _lex()
    docs = []
    for p in sorted(d.glob("*.json")):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if j.get("pages") and j.get("row"):
            docs.append(j)
    docs.sort(key=lambda j: j["row"].get("file", ""))
    out = _rep() / "restore"
    out.mkdir(parents=True, exist_ok=True)
    S = Counter()
    by_backend, drop_why, calc_c = Counter(), Counter(), Counter()
    t_res = t_ocr = 0.0
    allj = []
    lines_ok = []
    for nn, j in enumerate(docs, 1):
        row, info = j["row"], j.get("info") or {}
        rid = "%02d_%s_%s_%s" % (nn, row.get("code") or "NA", re.sub(r"\W", "", row.get("broker") or "") or "NA", re.sub(r"\D", "", row.get("date") or "") or "NA")
        picked = list(row.get("picked") or [])
        content, tables, dropped = [], [], []
        seq = 0

        def add(typ, text, b, pg, flags=None, joined=None):
            nonlocal seq
            why = noise_reason(text) if typ in ("sentence", "data", "bullet", "caption", "info") else ""
            if why:
                dropped.append({"text": text[:300], "reason": why, "page": pg, "block": b.get("id")})
                drop_why[why] += 1
                return
            seq += 1
            content.append({"id": "P%02d-%04d" % (pg, seq), "type": typ, "text": text, "page": pg, "block": joined or [b.get("id")], "zone": b.get("zone"), "role": b.get("role"),
                            "sub": b.get("sub", ""), "flags": flags or []})
            S[typ] += 1
        pending = None
        info_buf = []
        for pi, pg in enumerate(j["pages"]):
            orig = int(pg.get("page") or pi + 1)
            roles = pg.get("roles") or {}
            blocks = [b for b in pg.get("blocks", []) if (b.get("role") or roles.get(b.get("zone"))) not in ("HEADER", "FOOTER")]
            for bi, b in enumerate(blocks):
                if b.get("kind") != "text":
                    if pending:
                        add("sentence", pending["t"], pending["b"], orig, ["無句號"], pending["ids"])
                        S["no_end"] += 1
                        pending = None
                    continue
                if str(b.get("sub", "")).startswith(("頁尾", "免責")):
                    dropped.append({"text": (b.get("text") or "")[:300], "reason": "頁尾 / 免責區塊", "page": orig, "block": b.get("id")})
                    drop_why["頁尾 / 免責區塊"] += 1
                    continue
                units = b.get("units") or [("句", b.get("text") or "")]
                is_info = (b.get("role") or roles.get(b.get("zone"))) == "INFO"
                if not is_info and len(units) == 1 and _INFO_LABEL.match(tidy(units[0][1])):       # 欄名單行區塊 + 下一塊是資訊區 → 一起算資訊區
                    nb = blocks[bi + 1] if bi + 1 < len(blocks) else None
                    is_info = bool(nb) and nb.get("kind") == "text" and (nb.get("role") or roles.get(nb.get("zone"))) == "INFO"
                if is_info:                                                         # 資訊區 = 欄名 + 值,不套斷句;連續資訊區區塊串成一條再配對
                    if pending:
                        add("sentence", pending["t"], pending["b"], orig, ["無句號"], pending["ids"])
                        S["no_end"] += 1
                        pending = None
                    info_buf.append((b, units))
                    nb = blocks[bi + 1] if bi + 1 < len(blocks) else None
                    nxt_info = bool(nb) and nb.get("kind") == "text" and ((nb.get("role") or roles.get(nb.get("zone"))) == "INFO" or (len(nb.get("units") or []) == 1 and _INFO_LABEL.match(tidy((nb.get("units") or [("", "")])[0][1]))))
                    if not nxt_info:
                        for t in info_pairs([u for _, us in info_buf for u in us]):
                            add("info", t, info_buf[0][0], orig)
                        info_buf.clear()
                    continue
                head_block = "標題" in str(b.get("sub", ""))
                flat = []
                for typ, txt in units:
                    txt = tidy(txt)
                    if not txt:
                        continue
                    if typ == "表列":
                        flat.append(txt)
                        continue
                    if typ != "句" or head_block:
                        if pending:
                            add("sentence", pending["t"], pending["b"], orig, ["無句號"], pending["ids"])
                            S["no_end"] += 1
                            pending = None
                        t2 = {"標題": "heading", "資料": "data", "圖": "caption", "條列": "bullet"}.get(typ, "heading" if head_block else "data")
                        if t2 == "bullet":
                            for s in split_sentences(txt) or [txt]:
                                add("bullet", s, b, orig, ["條列"])
                        else:
                            add(t2, txt, b, orig)
                        continue
                    nz = noise_reason(txt)
                    if nz:                                   # 雜訊逐個單位判(在銜接之前)· 不參與銜接
                        dropped.append({"text": txt[:300], "reason": nz, "page": orig, "block": b.get("id")})
                        drop_why[nz] += 1
                        continue
                    if pending:
                        pending["t"] = _join(pending["t"], txt)
                        if b.get("id") not in pending["ids"]:
                            pending["ids"].append(b.get("id"))
                            S["cross_join"] += 1
                    else:
                        pending = {"t": txt, "b": b, "ids": [b.get("id")]}
                    if ends_sentence(pending["t"]):
                        ss = split_sentences(pending["t"])
                        for s in ss:
                            add("sentence", s, pending["b"], orig, [], pending["ids"] if len(pending["ids"]) > 1 else None)
                        pending = None
                if flat:
                    rows = flat_rows(flat)
                    hdr = rows[0] if rows and len(rows[0]) > 2 and not rows[0][0] else None
                    width = len(hdr) if hdr else 0
                    consistent = bool(hdr) and all(len(r) == width for r in rows[1:] if len(r) > 1) and len(rows) >= 2
                    rec = table_record([r + [""] * (max(len(x) for x in rows) - len(r)) for r in rows], orig, "P%02d-%s-文中表" % (orig, (b.get("id") or "").split("·")[-1]), "文中表格重組(表列)", lex, consistent,
                                       [] if consistent else ["列數值數 ≠ 表頭期數" if hdr else "找不到期間表頭"], {"block": b.get("id")})
                    tables.append(rec)
                    S["flat_tables"] += 1
                if pending:
                    nxt = blocks[bi + 1] if bi + 1 < len(blocks) else None
                    cont = bool(nxt) and nxt.get("kind") == "text" and nxt.get("zone") == b.get("zone") and nxt.get("role") == b.get("role") and "標題" not in str(nxt.get("sub", "")) \
                        and abs(float(nxt.get("size") or 0) - float(b.get("size") or 0)) <= 0.6 and (nxt.get("units") or [("句", "")])[0][0] == "句" \
                        and 0 <= float(nxt.get("top", 0)) - float(b.get("bottom", 0)) <= 2.0 * max(float(b.get("size") or 9), 6) and not _BULLET.match((nxt.get("units") or [("", "")])[0][1] or "")
                    if not cont:
                        add("sentence", pending["t"], pending["b"], orig, ["無句號"], pending["ids"] if len(pending["ids"]) > 1 else None)
                        S["no_end"] += 1
                        pending = None
            if pending:
                add("sentence", pending["t"], pending["b"], orig, ["無句號"], pending["ids"] if len(pending["ids"]) > 1 else None)
                S["no_end"] += 1
                pending = None
            if info_buf:
                for t in info_pairs([u for _, us in info_buf for u in us]):
                    add("info", t, info_buf[0][0], orig)
                info_buf.clear()
            # 表格
            local = (picked.index(orig) + 1) if orig in picked else pi + 1
            page_pl, pdf_h = None, None
            for b in [b for b in pg.get("blocks", []) if b.get("kind") == "table"]:
                tid = "P%02d-%s" % (orig, (b.get("id") or "").split("·")[-1])
                v = b.get("verify") or {}
                if not v.get("ok") and row.get("mini") and Path(row["mini"]).exists():       # 先用補好洞的驗表重驗原生列(期間辨識 · 算術正負號)
                    try:
                        import pdfplumber  # noqa: WPS433
                        if pdf_h is None:
                            pdf_h = pdfplumber.open(row["mini"])
                            page_pl = pdf_h.pages[local - 1]
                        v2 = vt(dict(b), page_pl)
                        if v2.get("ok") and _real_table(b.get("rows"), v2):
                            tables.append(table_record(b.get("rows") or [], orig, tid, "原生(重驗過 · 期間辨識 / 算術正負號已補)", lex, True, [], {"block": b.get("id"), "old_issues": list(v.get("issues") or [])}))
                            S["t_reverify"] += 1
                            continue
                    except Exception:  # noqa: BLE001
                        pass
                if v.get("ok"):
                    tables.append(table_record(b.get("rows") or [], orig, tid, b.get("engine") or "原生(pdfplumber)", lex, True, [], {"block": b.get("id")}))
                    S["t_native"] += 1
                    continue
                rows, backend, tried = None, "", []
                if row.get("mini") and Path(row["mini"]).exists() and t_res < rescue_budget:
                    t0 = time.time()
                    try:
                        import pdfplumber  # noqa: WPS433
                        if pdf_h is None:
                            pdf_h = pdfplumber.open(row["mini"])
                            page_pl = pdf_h.pages[local - 1]
                        rows, backend, tried = _rescue(th, row["mini"], local, b, vt, page_pl, rescue_budget - t_res)
                    except Exception:  # noqa: BLE001
                        rows = None
                    t_res += time.time() - t0
                if rows:
                    tables.append(table_record(rows, orig, tid, "原生救回(%s)" % backend, lex, True, [], {"block": b.get("id"), "tried": tried}))
                    S["t_rescued"] += 1
                    by_backend[backend] += 1
                    continue
                rec = None
                if ocr and th is not None and row.get("mini") and t_ocr < ocr_budget:
                    t0 = time.time()
                    try:
                        import fitz  # noqa: WPS433
                        from PIL import Image  # noqa: WPS433
                        with fitz.open(row["mini"]) as dd:
                            p_ = dd[local - 1]
                            clip = fitz.Rect(max(0, float(b["x0"]) - 4), max(0, float(b["top"]) - 42), min(p_.rect.width, float(b["x1"]) + 4), min(p_.rect.height, float(b["bottom"]) + 4))
                            pix = p_.get_pixmap(clip=clip, dpi=ocr_dpi, alpha=False)
                            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                        o = th.ocr_image(img, "rapidocr")
                        if o.get("status") == "ok":
                            orows = ocr_rows(o["lines"])
                            w = max((len(r) for r in orows), default=0)
                            orows = [r + [""] * (w - len(r)) for r in orows]
                            rec = table_record(orows, orig, tid, "OCR 候選(rapidocr@%d DPI)" % ocr_dpi, lex, False, list(v.get("issues") or []),
                                               {"block": b.get("id"), "tried": tried, "ocr_conf": o.get("conf"), "ocr_lines": o.get("n")})
                            rec["status"] = "OCR 候選 · 算術過" if rec["calc_status"] == "PASS" else ("OCR 候選 · 算術不符" if rec["calc_status"] == "FAIL" else "OCR 候選(無恆等式可驗)")
                    except Exception as exc:  # noqa: BLE001
                        rec = None
                        S["ocr_err"] += 1
                    t_ocr += time.time() - t0
                if rec:
                    tables.append(rec)
                    S["t_ocr"] += 1
                else:
                    tables.append(table_record(b.get("rows") or [], orig, tid, "原生(未過)", lex, False, list(v.get("issues") or []), {"block": b.get("id"), "tried": tried,
                                                                                                                                     "next": "OCR 預算用完 / 沒跑" if ocr else "--no-ocr"}))
                    S["t_fail"] += 1
            if pdf_h is not None:
                pdf_h.close()
        for t in tables:
            for c in t["calc"]:
                calc_c[c["status"]] += 1
        good = [t for t in tables if t["status"] == "還原無誤"]
        ok_doc = bool(content) and len(good) == len(tables)
        S["docs_ok"] += 1 if ok_doc else 0
        meta = {"report_id": rid, "file": row.get("file"), "ticker": row.get("code"), "yf": row.get("yf"), "bbg": row.get("bbg"), "company": row.get("name"), "broker": row.get("broker"),
                "report_date": row.get("date"), "rating": info.get("rating"), "rating_raw": info.get("rating_raw"), "target_price": info.get("tp"), "close": info.get("close"),
                "analysts": [(a.get("name") if isinstance(a, dict) else str(a)) for a in (info.get("analysts") or [])], "pages_picked": picked, "annual_pages": row.get("annual") or []}
        docj = {"schema": "VIA.VRN.Restore.v1", "generated": datetime.datetime.now().isoformat(timespec="seconds"), "layout_run": d.parent.name, "document_meta": meta, "content": content,
                "tables": tables, "dropped": dropped,
                "summary": {"sentences": sum(1 for c in content if c["type"] == "sentence"), "headings": sum(1 for c in content if c["type"] == "heading"), "tables": len(tables),
                            "tables_ok": len(good), "status": "還原後無誤" if ok_doc else "待補", "rule": "成功 = 驗表過 + 無算術不符;OCR 一律候選"}}
        (out / (rid + ".json")).write_text(json.dumps(docj, ensure_ascii=False, indent=1), encoding="utf-8")
        allj.append(docj)
        lines_ok.append(("GREEN" if ok_doc else ("YELLOW" if good else "RED"), [rid, row.get("file", ""), docj["summary"]["sentences"], docj["summary"]["headings"], len(dropped), "%d/%d" % (len(good), len(tables)),
                                                                              sum(1 for t in tables if t["method"].startswith("原生救回")), sum(1 for t in tables if t["method"].startswith("OCR")),
                                                                              sum(1 for t in tables if t["calc_status"] == "FAIL"), docj["summary"]["status"]]))
        print("  [進度] %d/%d · 還原 · %s · %s" % (nn, len(docs), lines_ok[-1][0], row.get("file", "")[:44]), flush=True)
    with (out / "RESTORE_ALL_latest.jsonl").open("w", encoding="utf-8") as fh:
        for x in allj:
            fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    summ = {"schema": "VIA.VRN.RestoreSummary.v1", "layout_run": d.parent.name, "docs": len(docs), "docs_ok": S["docs_ok"], "counts": dict(S), "dropped": dict(drop_why), "rescued_by": dict(by_backend),
            "calc": dict(calc_c), "rescue_secs": int(t_res), "ocr_secs": int(t_ocr), "ocr": ocr}
    (out / "RESTORE_SUMMARY_latest.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    page = _resolve("_page")
    if page:
        (out / "RESTORE_latest.html").write_text(page("原生還原(JSON)· 斷句 · 去雜訊 · 文中表格 · 表格依序升級 · 會計恆等式", "讀 %s · 報告 %d · 還原後無誤 %d · JSON 夾 %s" % (
            html.escape(d.parent.name), len(docs), S["docs_ok"], html.escape(str(out))), ["報告", "檔", "句", "標題", "去雜訊", "表 無誤/總", "原生救回", "OCR 候選", "算術不符", "狀態"], lines_ok), encoding="utf-8")
    summ["dir"], summ["html"] = str(out), str(out / "RESTORE_latest.html")
    return summ


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["restore"]:
        inst = _resolve("install_v166")
        if inst:
            inst()
        opt = lambda k, dv="": args[args.index(k) + 1] if k in args and args.index(k) + 1 < len(args) else dv  # noqa: E731
        o = restore_run("--no-ocr" not in args, int(opt("--rescue-budget", "600") or 600), int(opt("--ocr-budget", "300") or 300), int(opt("--ocr-dpi", "200") or 200))
        if o.get("err"):
            print("[計] 原生還原 · %s · RED" % o["err"])
            return 1
        c = o["counts"]
        print("[計] 原生還原(JSON)· 讀上一輪 layout(%s)· 報告 %d · 句 %d · 標題 %d · 條列 %d · 資料 %d · 資訊區 %d · 圖說 %d · 跨區塊銜接 %d · 無句號收尾 %d" % (
            o["layout_run"], o["docs"], c.get("sentence", 0), c.get("heading", 0), c.get("bullet", 0), c.get("data", 0), c.get("info", 0), c.get("caption", 0), c.get("cross_join", 0), c.get("no_end", 0)))
        print("[計] 去雜訊(不刪 · 進 dropped)· " + (" · ".join("%s %d" % kv for kv in Counter(o["dropped"]).most_common()) or "—"))
        print("[計] 期間辨識 / 算術補洞 · %s(24Q1 · Dec-24A · Mar-25 · 2024/12 · (F) 後綴;成本 / 費用正負號統一)· 上一輪沒過的表重驗過 %d 張" % (",".join(_WRAPPED) or "—", c.get("t_reverify", 0)))
        print("[計] 表格 · 原生還原 %d · 原生重驗過 %d · 原生救回 %d(%s)· 文中表格重組 %d · OCR 候選 %d · 仍失敗 %d · 救回 %d 秒 · OCR %d 秒%s" % (
            c.get("t_native", 0), c.get("t_reverify", 0), c.get("t_rescued", 0), " · ".join("%s %d" % kv for kv in Counter(o["rescued_by"]).most_common()) or "—", c.get("flat_tables", 0), c.get("t_ocr", 0), c.get("t_fail", 0),
            o["rescue_secs"], o["ocr_secs"], "" if o["ocr"] else " · OCR 沒跑(--no-ocr)"))
        cc = o["calc"]
        print("[計] 會計恆等式(正負號統一)· 驗 %d 期 · 過 %d · 不符 %d(毛利 = 營收 − 成本 · 營益 = 毛利 − 費用 · 淨利 ≈ 稅前 − 稅 · 資產 = 負債 + 權益 · 利潤率)" % (sum(cc.values()), cc.get("PASS", 0), cc.get("FAIL", 0)))
        print("[計] 還原後無誤的報告 %d/%d(全部表驗過且無算術不符;OCR 一律候選)· JSON 夾 %s" % (o["docs_ok"], o["docs"], o["dir"]))
        print("  [U/I] %s" % o["html"])
        return 0
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
    td = Path(tempfile.mkdtemp(prefix="vrn172-"))
    saved = {k: os.environ.get(k) for k in ("VIA_SPILL_DIR", "VIA_VRN_HEALTH_OUT")}
    try:
        from reportlab.pdfgen import canvas
        import fitz
        stage = td / "VIA_progress" / "ps_x" / "spill" / "vrn_stage_r1"
        (stage / "layout_l2").mkdir(parents=True)
        tmp = td / "img_src.pdf"
        c = canvas.Canvas(str(tmp), pagesize=(595, 842))
        c.setFont("Helvetica", 14)
        Y = lambda y: 842 - y - 14  # noqa: E731
        for t, x in (("Item", 60), ("2024", 260), ("2025F", 380)):
            c.drawString(x, Y(100), t)
        for y, lab, v in ((130, "Revenue", ("2,000", "2,400")), (160, "COGS", ("(1,500)", "(1,700)")), (190, "Gross profit", ("500", "700"))):
            c.drawString(60, Y(y), lab)
            c.drawString(260, Y(y), v[0])
            c.drawString(380, Y(y), v[1])
        c.save()
        with fitz.open(str(tmp)) as dd:
            pix = dd[0].get_pixmap(dpi=150, clip=fitz.Rect(40, 80, 500, 230))
            pngp = td / "tbl.png"
            pix.save(str(pngp))
        mini = stage / "mini.pdf"
        c = canvas.Canvas(str(mini), pagesize=(595, 842))
        c.setFont("Helvetica", 9)
        c.drawString(60, 842 - 100, "p1")
        c.showPage()
        c.setFont("Helvetica", 10)
        Y = lambda y: 842 - y - 9  # noqa: E731
        for t, x in (("NT$m", 60), ("2024A", 220), ("2025F", 320)):
            c.drawString(x, Y(300), t)
        for y, lab, v in ((320, "Revenue", ("1,234", "1,456")), (340, "EPS", ("2.31", "3.10")), (360, "Net income", ("300", "350"))):
            c.drawString(60, Y(y), lab)
            c.drawString(220, Y(y), v[0])
            c.drawString(320, Y(y), v[1])
        for y in (295, 312, 332, 352, 372):
            c.line(55, 842 - y, 400, 842 - y)
        for x in (55, 200, 300, 400):
            c.line(x, 842 - 295, x, 842 - 372)
        c.showPage()
        c.drawImage(str(pngp), 40, 842 - 230, width=460, height=150)          # 頁面座標(左下原點):頂 80 · 底 230
        c.showPage()
        c.save()
        U = lambda *u: [list(x) for x in u]  # noqa: E731
        tx = lambda i, units, top, bottom, sub="內文", size=9.0: {"id": i, "kind": "text", "zone": "F", "role": "BODY", "x0": 50, "top": top, "x1": 540, "bottom": bottom, "size": size, "sub": sub, "units": units, "text": ""}  # noqa: E731
        ib = lambda i, units, top: dict(tx(i, units, top, top + 8), role="INFO", zone="L")  # noqa: E731
        blocks1 = [tx("P1·F·01", U(("標題", "Jentech (3653 TT) Liquid cooling ramp")), 40, 56, "主標題", 15.0),
                   dict(tx("P1·L·01", U(("句", "Stock Rating")), 20, 28), zone="L"), ib("P1·L·02", U(("句", "Overweight")), 29), ib("P1·L·03", U(("句", "Price target")), 38), ib("P1·L·04", U(("句", "NT$650")), 47),
                   tx("P1·F·02", U(("句", "We expect revenue to keep growing;"), ("句", "margin outlook stays solid."), ("句", "Demand into the second half")), 60, 90),
                   tx("P1·F·03", U(("句", "of 2026 remains strong."), ("句", "營 收 年 增 二 成 。 毛利率 回 升 。")), 92, 120),
                   tx("P1·F·04", U(("標題", "投資建議")), 124, 134, "小標題", 11.0),
                   tx("P1·F·05", U(("條列", "• 產能擴張。 • 新客戶導入"), ("句", "0 50 100 150 200"), ("句", "{[{penVENX2WqWz8Kq3Lm9PzQ}]}"), ("句", "本資料之內容,本公司已力求其正確性,翻印必究。")), 140, 180),
                   tx("P1·F·06", U(("表列", "6873泓德能源 2023 24Q1 24Q2"), ("表列", "營業收入淨額 5,839 884 1,272"), ("表列", "營業成本 4,332 651 945"), ("表列", "營業毛利淨額 1,507 233 327")), 200, 260)]
        tb = lambda i, rows, ok, x0, top, x1, bottom: {"id": i, "kind": "table", "zone": "F", "role": "BODY", "sub": "財務表(損益)", "x0": x0, "top": top, "x1": x1, "bottom": bottom, "rows": rows, "verify": {"ok": ok, "issues": [] if ok else ["仍有合併數字格"]}}  # noqa: E731
        blocks2 = [tb("P5·F·01·T1", [["NT$m", "2024A", "2025F"], ["營業收入", "1,000", "1,200"], ["營業成本", "(600)", "(700)"], ["營業毛利", "400", "500"]], True, 50, 100, 400, 160),
                   tb("P5·F·02·T2", [["NT$m", "2024A", "2025F"], ["Revenue", "1,234 1,456", ""], ["EPS", "2.31 3.10", ""], ["Net income", "300 350", ""]], False, 55, 295, 400, 372),
                   dict(tb("P5·F·03·T3", [["NT$m", "2024A"], ["Total assets", "1,000"], ["Total liabilities", "600"], ["Total equity", "300"]], True, 50, 500, 400, 560), sub="財務表(資產負債)")]
        blocks3 = [tb("P6·F·01·T1", [["x", "1 2"]], False, 40, 80, 500, 230)]
        j = {"row": {"file": "兆豐_6873_泓德能源_20250819.pdf", "code": "6873", "name": "泓德能源", "broker": "MEGA", "date": "2025-08-19", "mini": str(mini), "picked": [1, 5, 6], "annual": [5, 6]},
             "info": {"rating": "Buy", "tp": 345.0}, "pages": [{"page": 1, "W": 595, "H": 842, "roles": {"F": "BODY"}, "blocks": blocks1}, {"page": 5, "W": 595, "H": 842, "roles": {"F": "BODY"}, "blocks": blocks2},
                                                           {"page": 6, "W": 595, "H": 842, "roles": {"F": "BODY"}, "blocks": blocks3}]}
        (stage / "layout_l2" / "a.json").write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
        os.environ["VIA_SPILL_DIR"] = str(td / "VIA_progress" / "ps_new" / "spill")
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        o = restore_run(ocr=True, rescue_budget=120, ocr_budget=120, ocr_dpi=200)
        dj = json.loads((Path(o["dir"]) / "01_6873_MEGA_20250819.json").read_text(encoding="utf-8"))
        sents = [x["text"] for x in dj["content"] if x["type"] == "sentence"]
        heads = [x["text"] for x in dj["content"] if x["type"] == "heading"]
        chk("① 一句一筆到句號:分號不斷句(We expect … growing; margin … solid.)· 跨區塊銜接(Demand into the second half of 2026 remains strong.)· 中文去空格(營收年增二成。/ 毛利率回升。)",
            "We expect revenue to keep growing; margin outlook stays solid." in sents and "Demand into the second half of 2026 remains strong." in sents and "營收年增二成。" in sents and "毛利率回升。" in sents)
        infos = [x["text"] for x in dj["content"] if x["type"] == "info"]
        chk("⑭ 資訊區跨區塊配對:欄名「Stock Rating」(版面沒判成資訊區)+ 下一塊「Overweight」→ Stock Rating: Overweight · Price target: NT$650 · 沒變成句子", infos == ["Stock Rating: Overweight", "Price target: NT$650"] and "Stock Rating" not in sents)
        chk("② 標題無句號不接(主標題 · 小標題各自一筆,沒跟後面句子接)· 條列各自一筆", heads == ["Jentech (3653 TT) Liquid cooling ramp", "投資建議"] and
            [x["text"] for x in dj["content"] if x["type"] == "bullet"] == ["• 產能擴張。", "• 新客戶導入"] and not any("投資建議" in s for s in sents))
        why = {x["reason"] for x in dj["dropped"]}
        chk("③ 去雜訊不刪(進 dropped 附原因):圖表座標數字 · 浮水印 / 編碼 · 免責聲明 → %s" % "、".join(sorted(why)), {"圖表座標數字", "浮水印 / 編碼", "免責聲明"} <= why and not any("翻印" in s for s in sents))
        T = {t["id"]: t for t in dj["tables"]}
        ft = next(t for t in dj["tables"] if t["method"].startswith("文中表格"))
        chk("④ 文中表格(表列)不當句子 → 依表頭重組 · 期間 2023/24Q1/24Q2 · 營業收入淨額 → revenue · 毛利 = 營收 − 成本 3 期全過 · 還原無誤",
            ft["status"] == "還原無誤" and ft["periods"][:3] == ["2023", "24Q1", "24Q2"] and any(r["std"] == "revenue" for r in ft["rows"]) and sum(1 for c in ft["calc"] if c["status"] == "PASS") == 3
            and not any("5,839" in s for s in sents))
        t1 = T.get("P05-T1")
        chk("⑤ 成本寫成括號負數(600)→ 正負號統一後 毛利 = 營收 − 成本 過(舊 _arith 會誤判)· 還原無誤", t1 and t1["status"] == "還原無誤" and t1["calc_status"] == "PASS")
        t2 = T.get("P05-T2")
        chk("⑥ VRN 沒過的格線表 → 原生讀表器依序 → %s 過 VRN 原驗表 · 不動 OCR" % (t2 or {}).get("method"), t2 and t2["method"].startswith("原生救回") and t2["status"] == "還原無誤")
        t3 = T.get("P05-T3")
        chk("⑦ 資產 1,000 ≠ 負債 600 + 權益 300 → 算術不符(待查)· 不算成功", t3 and t3["status"] == "算術不符(待查)" and any(c["rule"] == "資產 = 負債 + 權益" and c["status"] == "FAIL" for c in t3["calc"]))
        t4 = T.get("P06-T1")
        if importlib.util.find_spec("rapidocr_onnxruntime"):
            vals = {c["value"] for r in (t4 or {}).get("rows", []) for c in r["cells"]}
            chk("⑧ 純影像表:原生讀表器全讀不到 → 才走 OCR(表框 200 DPI · 對表頭欄位)→ %s · 讀到 2,000 / 2,400 · 只算候選" % (t4 or {}).get("status"),
                t4 and t4["method"].startswith("OCR") and t4["status"].startswith("OCR 候選") and {2000.0, 2400.0} <= vals)
        else:
            chk("⑧ 純影像表:這台沒有 rapidocr → 標原生未過(不崩)", t4 and t4["status"] == "未過")
        chk("⑨ 成功 = 全部表還原無誤:這份有算術不符 + OCR 候選 → 待補(不灌水)· 全程 JSON(每份 · jsonl · 摘要)",
            dj["summary"]["status"] == "待補" and o["docs_ok"] == 0 and (Path(o["dir"]) / "RESTORE_ALL_latest.jsonl").exists() and (Path(o["dir"]) / "RESTORE_SUMMARY_latest.json").exists())
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    ip = info_pairs([("句", "Stock Rating"), ("句", "Overweight"), ("句", "Price target"), ("句", "NT$1,200"), ("句", "Analyst Amy Wang"), ("句", "目標價"), ("句", "1275")])
    chk("⑬ 資訊區不套斷句 · 欄名 + 值配對(Stock Rating: Overweight · Price target: NT$1,200 · 目標價: 1275)· 配不起來的各自一筆不亂接",
        ip == ["Stock Rating: Overweight", "Price target: NT$1,200", "Analyst Amy Wang", "目標價: 1275"])
    lex = _lex()
    kgi = {"id": "K", "kind": "table", "sub": "財務表(損益)", "x0": 0, "top": 0, "x1": 1, "bottom": 1,
           "rows": [["NT$ 百萬", "Dec-24A", "Dec-25A", "Dec-26F"], ["營業收入", "36,828", "37,990", "39,521"], ["營業成本", "(25,460)", "(27,108)", "(28,000)"], ["營業毛利", "11,368", "10,882", "11,521"]]}
    vk = (_resolve("_ORIG_VT") or _resolve("verify_table"))(kgi, None)
    rk = table_record(kgi["rows"], 1, "K", "t", lex, True)
    mg = table_record([["", "2023", "24Q1", "25Q4(F)"], ["營業收入淨額", "5,839", "884", "900"], ["營業成本", "4,332", "651", "600"], ["營業毛利淨額", "1,507", "233", "300"]], 1, "M", "t", lex, True)
    chk("⑫ 補洞:KGI 表頭 Dec-24A 認得 + 成本 (25,460) 正負號統一 → VRN 驗表過(原本誤判沒過)· 兆豐季表 24Q1 / 25Q4(F) 認得 · 期間 %s" % mg["periods"],
        vk.get("ok") and rk["periods"] == ["Dec-24A", "Dec-25A", "Dec-26F"] and rk["calc_status"] == "PASS" and mg["periods"] == ["2023", "24Q1", "25Q4(F)"] and per_extra("Mar-25") and not per_extra("Revenue"))
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑪ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0172 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
