#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0157 — 薄尾(操作員 2026-10-10):第二步 = LAYOUT NON-OCR 識別。
  layout [--dir 夾] [--workers N] [--tabula] [--max N] [--only 片段]
   第一步  四類分類器(上傳的 VRN_ReportClassifier v0100,放 VRN\\intake\\VRN_ReportClassifier;讀取改用 pdfplumber,不另需 PyMuPDF)
           + 檔名判讀 → 只取個股報告的第一頁 + 年度財報頁 → 小 PDF 進 TEMP;分類器確定非個股的也不碰
   第二步  LAYOUT NON-OCR 識別(多程序 spawn;每檔識別結果全存 TEMP JSON,主程序只留摘要 = 用 TEMP 補記憶體)
           文字還原:斷句連接(英文斷字接回 · 中文不加空白 · 句號後換句)但不錯接(疑錯接計數)→ 一句 / 一標題 / 一資料 / 一條列 / 一表列
                     100% 證明 = 每個非空白字元都落在已分類區塊(位置覆蓋 ≥ 99.5% 才算過;漏的片段列出)
           表格還原:修復(拆合併數字格 · 數字欄少於年度欄時座標重分欄 · 刪空列空欄 · 併換行列標)→ 驗證(表頭 · 列長齊 · 無合併數字格 · 可解析 ≥90% · 表內字還原 ≥98% · 前版 _rebuild_table 算術)
           成功收尾 = 文字還原過 且 表格還原過
           資訊區:EMAIL(@ 前 = 英文姓名還原;@ 後網域 = 券商再核對)· 台灣 / 香港電話 · 職稱(中英)· 分析師(電郵上方 · 職稱上方 · 電話上方)· 評等字典 · 目標價 · 收盤 · 首頁日期
           ENG394 _subcat:照它真正的簽名(size, bold, body, nchar, text)依參數名綁定
   交互驗證 檔名 ↔ 首頁 ↔ 頁尾 / 電郵網域 ↔ 資料庫(VDF 資料庫唯讀:總清單 · 收盤 · 報告日前最後交易日 adj close · 最新 adj close · TP(adj)= TP × adj/close)
   產出三頁:STEP1_latest.html · STEP2_latest.html · XCHECK_latest.html(+ 每檔版面頁加還原面板)
   速度:tabula 預設關(每表起 Java 很慢;--tabula 才開)· deepread 不再呼叫 · 多程序
  engines [--register]  VRN 引擎稽核:版本 · 是否註冊於 VRN SSOT · 是否加入加速器(PY 與 PS 都查;含 Downloads 現行啟動器)· --register 寫 registry\\VRN_Engine_Register_v####(內容變才出新版)
其餘動詞照前版鏈。
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

import datetime
import hashlib
import html
import importlib.util
import inspect
import json
import os
import re
import shutil
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0157"


def _vnum_v0157(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0157(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0157(p) < _vnum_v0157(__file__)), key=_vnum_v0157)
PRIOR = _load_v0157(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


_home, _rep = _resolve("_home"), _resolve("_rep")

# ───────── ENG394 _subcat:照它真正的簽名(size, bold, body, nchar, text)依參數名綁定 ─────────
_E394 = {}


def eng394_bind() -> dict:
    if _E394:
        return _E394
    e = (_resolve("eng394") or (lambda: {}))()
    _E394.update(file=e.get("file", ""), ok=False, sig="", err=e.get("err", ""), rulebook=e.get("rulebook", ""))
    mod = e.get("mod")
    fn = getattr(mod, "_subcat", None) if mod else None
    if not callable(fn):
        return _E394
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        _E394["err"] = "_subcat 讀不到簽名"
        return _E394
    _E394["sig"] = str(sig)[:120]

    def call(size, bold, body, nchar, text):
        kw = {}
        for name, prm in sig.parameters.items():
            n = name.lower()
            if prm.kind in (prm.VAR_POSITIONAL, prm.VAR_KEYWORD):
                continue
            if n.startswith("size") or n in ("fs", "font_size", "fontsize"):
                kw[name] = size
            elif n.startswith("bold") or n in ("is_bold", "b"):
                kw[name] = bold
            elif n.startswith("body") or n in ("base", "body_size"):
                kw[name] = body
            elif n.startswith(("nchar", "n_char", "chars", "length", "ln")):
                kw[name] = nchar
            elif n.startswith(("t", "s")):
                kw[name] = text
            elif prm.default is inspect.Parameter.empty:
                kw[name] = None
        return fn(**kw)
    try:
        probe = call(13.0, True, 9.5, 21, "Investment highlights")
        _E394.update(ok=True, call=call, probe=str(probe)[:30], err="")
    except Exception as exc:  # noqa: BLE001
        _E394["err"] = "依名綁定仍失敗 %s:%s" % (type(exc).__name__, str(exc)[:60])
    return _E394


def _e394_text(b: dict, body: float) -> str:
    e = eng394_bind()
    if not e.get("ok"):
        return ""
    try:
        r = e["call"](float(b.get("size") or 0), bool(b.get("bold")), float(body or 0), len(b.get("text", "")), b.get("text", ""))
        if isinstance(r, (tuple, list)) and r:
            r = r[0]
        if isinstance(r, dict):
            r = r.get("subcat") or r.get("category") or r.get("cat") or ""
        return str(r)[:30] if r is not None else ""
    except Exception:  # noqa: BLE001
        return ""


# ───────── 文字還原:斷句連接(不錯接)· 一句 / 一標題 / 一資料 · 位置覆蓋率證明 100% ─────────
_TERM = re.compile(r"[。！？!?；;:：]\s*$|\.\s*$")
_CJK_END = re.compile(r"[\u4e00-\u9fff，、（(「]$")
_CJK_START = re.compile(r"^[\u4e00-\u9fff，、。）)」]")


def rejoin(lines: list) -> tuple:
    """依行重組:CJK 接 CJK 不加空白 · 英文斷字(-)接回 · 其餘一個空白;回傳(文字, 連接斷句數, 疑錯接數)。"""
    if not lines:
        return "", 0, 0
    width = max(l["x1"] for l in lines) - min(l["x0"] for l in lines) or 1
    txt, joins, sus = lines[0]["text"], 0, 0
    for prev, l in zip(lines, lines[1:]):
        t = l["text"]
        if not _TERM.search(prev["text"]):
            joins += 1
            if (prev["x1"] - prev["x0"]) < 0.55 * width and re.match(r"[A-Z]", t) and not re.search(r"[,a-z]$", prev["text"]):
                sus += 1
        if txt.endswith("-") and re.match(r"[a-z]", t):
            txt = txt[:-1] + t
        elif _CJK_END.search(txt) and _CJK_START.search(t):
            txt += t
        else:
            txt += " " + t
    return txt, joins, sus


def units_of(b: dict) -> list:
    sub, t = b.get("sub", ""), b.get("text", "")
    if b["kind"] == "table":
        return [("表列", " | ".join(r)) for r in b.get("rows", [])]
    if b["kind"] == "figure":
        return [("圖", t[:80])] if t else [("圖", "")]
    if sub == "主標題" or sub.endswith("標題") or sub == "圖表標題":
        return [("標題", t)]
    if b["role"] in ("INFO", "HEADER") or sub == "資訊":
        return [("資料", l["text"]) for l in b.get("lines", [])] or [("資料", t)]
    if sub == "重點條列":
        return [("條列", t)]
    parts = [p.strip() for p in re.split(r"(?<=[。！？!?；;])|(?<=[.!?])\s+(?=[A-Z0-9\u4e00-\u9fff])", t) if p and p.strip()]
    return [("句", p) for p in parts] or [("句", t)]


def coverage(page, blocks: list) -> dict:
    """每個非空白字元都要落在某個已分類區塊(文字 · 表 · 圖 · 頁首 · 頁尾)裡 = 100% 還原(位置證明)。"""
    boxes = []
    for b in blocks:
        if b["kind"] == "text" and b.get("lines"):
            for l in b["lines"]:
                boxes.append((l["x0"] - 1, l["top"] - 1, l["x1"] + 1, l["bottom"] + 1))
        else:
            boxes.append((b["x0"] - 1, b["top"] - 1, b["x1"] + 1, b["bottom"] + 1))
    total, miss = 0, []
    for c in page.chars:
        ch = c.get("text", "")
        if not ch.strip():
            continue
        total += 1
        x, y = (c["x0"] + c["x1"]) / 2, (c["top"] + c["bottom"]) / 2
        if not any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in boxes):
            miss.append((round(c["top"]), c["x0"], ch))
    miss.sort()
    snippets, cur, last = [], "", None
    for top, x, ch in miss:
        if last is not None and top != last:
            snippets.append(cur)
            cur = ""
        cur += ch
        last = top
    if cur:
        snippets.append(cur)
    return {"chars": total, "missing": len(miss), "pct": round(100.0 * (total - len(miss)) / total, 2) if total else 100.0, "miss_snippets": snippets[:12]}


# ───────── 表格還原:驗證 + 修復(過去紀錄的還原修正法)─────────
_NUMTOK = re.compile(r"^[\(\-–−+]?[\d,]*\.?\d+%?\)?$|^(?:n\.?a\.?|N/?A|-|–|—|nm|NM)$")
_YR = re.compile(r"(?<![\d.])(?:20\d{2}[AEFP]?|FY\d{2,4}[AEFP]?|\d{2}[AEFP]|[1-4]Q\d{2}[AEF]?|\d[HQ]\d{2})(?![\d])")
_UNIT_RX = re.compile(r"(?i)(NT\$\s*(?:m|mn|bn|k)|US\$\s*(?:m|mn|bn)|\(?(?:百萬|千元|億元|仟元|元)\)?|%|x\b)")


def parse_number(s: str):
    t = str(s).strip().replace(",", "").replace("−", "-").replace("–", "-")
    if t in ("", "-", "—", "n.a.", "na", "N/A", "NA", "nm", "NM"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").rstrip("%").lstrip("+")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def repair_table(b: dict, page=None) -> dict:
    rows = [list(r) for r in b.get("rows", [])]
    fixes = list(b.get("fixes", []))
    if not rows:
        return {"rows": rows, "fixes": fixes}
    hdr = rows[0]
    nyears = sum(1 for c in hdr if _YR.search(c or ""))
    width = max(len(r) for r in rows)
    out = [hdr]
    split = 0
    for r in rows[1:]:
        cells = list(r)
        multi = [i for i, c in enumerate(cells) if c and len(re.findall(r"[\(\-]?[\d,]*\.?\d+%?\)?", c)) >= 2 and " " in c.strip() and all(_NUMTOK.match(tk) for tk in c.split())]
        if multi:
            new = []
            for i, c in enumerate(cells):
                new.extend(c.split() if i in multi else [c])
            if len(new) <= max(width, nyears + 1) + 1:
                cells = new
                split += 1
        out.append(cells + [""] * (max(width, len(cells)) - len(cells)))
    if split:
        fixes.append("拆合併數字格 %d 列" % split)
    w = max(len(r) for r in out)
    out = [r + [""] * (w - len(r)) for r in out]
    keep = [j for j in range(w) if any(r[j] for r in out)]
    if len(keep) < w:
        fixes.append("刪空欄 %d" % (w - len(keep)))
        out = [[r[j] for j in keep] for r in out]
    data = out[1:] if len(out) > 1 else []
    ncols = len(out[0]) if out else 0
    numeric_cols = [j for j in range(1, ncols) if sum(1 for r in data if r[j]) and sum(1 for r in data if r[j] and parse_number(r[j]) is not None) / max(1, sum(1 for r in data if r[j])) >= 0.6]
    if page is not None and nyears >= 2 and numeric_cols and len(numeric_cols) < nyears:
        try:
            g = _resolve("_cluster_table")(page, (b["x0"], b["top"], b["x1"], b["bottom"]))
            rr, _f = _resolve("_repair_rows")(g)
            if rr and sum(1 for c in rr[0] if _YR.search(c or "")) >= nyears and len(rr) >= len(out) - 1:
                out = rr
                fixes.append("座標重分欄(數字欄少於年度欄)")
        except Exception:  # noqa: BLE001
            pass
    return {"rows": out, "fixes": fixes}


def verify_table(b: dict, page=None) -> dict:
    rows = b.get("rows", [])
    v = {"ok": False, "header": False, "rect": False, "parse_rate": 0.0, "multi_left": 0, "text_cov": None, "arith": "未驗", "issues": [], "unit": ""}
    if len(rows) < 2 or max((len(r) for r in rows), default=0) < 2:
        v["issues"].append("列或欄少於 2")
        return v
    hdr = rows[0]
    v["header"] = sum(1 for c in hdr if _YR.search(c or "")) >= 2 or (bool(hdr[0]) and sum(1 for c in hdr[1:] if c and parse_number(c) is None) >= 1)
    v["rect"] = len({len(r) for r in rows}) == 1
    cells = [c for r in rows[1:] for c in r[1:] if c]
    nums = [c for c in cells if parse_number(c) is not None or c.strip() in ("-", "—", "–", "n.a.", "NA", "N/A", "nm", "NM")]
    v["parse_rate"] = round(len(nums) / len(cells), 3) if cells else 0.0
    v["multi_left"] = sum(1 for c in cells if len(c.split()) >= 2 and all(_NUMTOK.match(tk) for tk in c.split()))
    um = _UNIT_RX.search(" ".join(hdr) + " " + b.get("caption", ""))
    v["unit"] = um.group(1) if um else ""
    if page is not None:
        try:
            crop = page.crop((b["x0"], b["top"], b["x1"], b["bottom"]))
            raw = Counter(ch for ch in "".join(c.get("text", "") for c in crop.chars) if ch.strip())
            got = Counter(ch for ch in "".join("".join(r) for r in rows) if ch.strip())
            tot = sum(raw.values())
            v["text_cov"] = round(100.0 * sum(min(raw[k], got[k]) for k in raw) / tot, 1) if tot else 100.0
        except Exception:  # noqa: BLE001
            pass
    rb = _resolve("_rebuild_table")
    if rb:
        try:
            lex = list(_resolve("_FIN_STD") or []) + list((_resolve("_load_vrn_lexicon") or (lambda: []))())
            r2 = rb({"rows": rows, "page": b.get("page", 0), "engine": b.get("engine", ""), "surround": ""}, lex)
            iss = r2.get("issues") or []
            v["arith"] = "過" if not iss else "有問題"
            v["issues"] += [str(x)[:60] for x in iss[:5]]
            v["std_cat"] = r2.get("category", "")
        except Exception as exc:  # noqa: BLE001
            v["arith"] = "未驗(%s)" % type(exc).__name__
    numeric_table = b.get("sub", "").startswith(("財務表", "估值表"))
    v["ok"] = v["header"] and v["rect"] and v["multi_left"] == 0 and (v["parse_rate"] >= 0.9 or not numeric_table) and (v["text_cov"] is None or v["text_cov"] >= 98.0) and v["arith"] != "有問題"
    if not v["ok"]:
        for k, msg in (("header", "無表頭"), ("rect", "列長不齊")):
            if not v[k]:
                v["issues"].append(msg)
        if v["multi_left"]:
            v["issues"].append("仍有合併數字格 %d" % v["multi_left"])
        if numeric_table and v["parse_rate"] < 0.9:
            v["issues"].append("數字可解析率 %.0f%%" % (v["parse_rate"] * 100))
        if v["text_cov"] is not None and v["text_cov"] < 98.0:
            v["issues"].append("表內字還原 %.1f%%" % v["text_cov"])
    return v


# ───────── 資訊區抽取:EMAIL · 電話(台灣 / 香港)· 職稱 · 分析師(位置)· 評等 · 目標價 · 收盤 · 首頁日期 ─────────
EMAIL_RX = re.compile(r"([A-Za-z0-9][A-Za-z0-9._%+\-]{0,63})@([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+)")
TEL_TW_RX = re.compile(r"(?:\+?886[\s\-]?\(?0?\)?\s?\d{1,2}[\s\-]?\d{3,4}[\s\-]?\d{4}|\(0\d{1,2}\)\s?\d{3,4}[\s\-]?\d{4}|(?<!\d)0\d{1,2}[\s\-]\d{3,4}[\s\-]?\d{4}|(?<!\d)09\d{2}[\s\-]?\d{3}[\s\-]?\d{3})(?:\s?(?:#|ext\.?|分機)\s?\d{1,5})?")
TEL_HK_RX = re.compile(r"(?:\+?852[\s\-]?)\d{4}[\s\-]?\d{4}")
TITLES_ZH = ("資深分析師", "首席分析師", "研究部主管", "研究主管", "資深副總", "副總經理", "研究員", "分析師", "協理", "副理", "經理", "副總")
TITLES_EN = ("Head of Research", "Senior Analyst", "Research Analyst", "Equity Analyst", "Lead Analyst", "Managing Director", "Executive Director", "Vice President", "Associate", "Analyst", "Director", "VP", "MD")
RATING_NORM = {"強力買進": "Strong Buy", "買進": "Buy", "增加持股": "Overweight", "優於大盤": "Outperform", "中立": "Neutral", "持有": "Hold", "區間操作": "Trading Range", "降低持股": "Underweight", "劣於大盤": "Underperform", "賣出": "Sell", "未評等": "Not Rated",
               "Strong Buy": "Strong Buy", "Buy": "Buy", "Add": "Add", "Outperform": "Outperform", "Overweight": "Overweight", "OW": "Overweight", "Equal-weight": "Equal-weight", "Equal weight": "Equal-weight", "Neutral": "Neutral", "Hold": "Hold",
               "Market Perform": "Neutral", "Reduce": "Reduce", "Underperform": "Underperform", "Underweight": "Underweight", "UW": "Underweight", "Sell": "Sell", "Not Rated": "Not Rated", "NR": "Not Rated", "Trading Buy": "Trading Buy"}
TP_RX = re.compile(r"(?i)(?:目標價|目標股價|Target\s*Price|Price\s*Target|12[- ]?M(?:onth)?\s*TP|\bTP\b)\s*(?:\([^)]{0,20}\))?\s*[:：]?\s*(?:NT\$|TWD|NTD|NT|US\$|HK\$|\$|新台幣|元)?\s*([\d,]+(?:\.\d+)?)")
CLOSE_RX = re.compile(r"(?i)(?:收盤價|收盤|前日收盤|股價|Close(?:\s*price)?|Last\s*(?:close|price)|Share\s*price|Price\s*\((?:[^)]{0,20})\))\s*(?:\([^)]{0,20}\))?\s*[:：]?\s*(?:NT\$|TWD|NTD|US\$|HK\$|\$|元)?\s*([\d,]+(?:\.\d+)?)")
_MON = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
DATE_RXS = [(re.compile(r"(?<!\d)(20\d{2})\s*[/\-.年]\s*(\d{1,2})\s*[/\-.月]\s*(\d{1,2})"), "ymd"), (re.compile(r"(?<!\d)(1[01]\d)\s*[/\-.年]\s*(\d{1,2})\s*[/\-.月]\s*(\d{1,2})"), "roc"),
            (re.compile(r"(?i)(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+(20\d{2})"), "dmy"), (re.compile(r"(?i)(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(20\d{2})"), "mdy")]
DOMAIN_BROKER = {"kgi": "KGI", "kgieworld": "KGI", "morganstanley": "MS", "ms": "MS", "ubs": "UBS", "gs": "GS", "goldmansachs": "GS", "citi": "Citi", "citigroup": "Citi", "daiwa": "Daiwa", "daiwacm": "Daiwa", "jpmorgan": "JPM", "jpmchase": "JPM",
                 "clsa": "CLSA", "macquarie": "MCQ", "ctbcsec": "CTBC", "ctbc": "CTBC", "megasec": "MEGA", "emega": "MEGA", "capital": "CSC", "taishin": "TSC", "tsc": "TSC", "yuanta": "YT", "fubon": "FB", "sinopac": "SJP", "cathaysec": "CT", "cathay": "CT",
                 "hnsec": "HNSC", "entrust": "HNSC", "pscnet": "PSC", "gfgroup": "GF", "gf": "GF", "nomura": "Nomura", "bofa": "BofA", "baml": "BofA", "hsbc": "HSBC", "jefferies": "Jefferies", "bernstein": "Bernstein", "barclays": "Barclays", "dbs": "DBS", "mizuho": "Mizuho"}


def email_name(local: str) -> str:
    parts = [p for p in re.split(r"[._\-]+", local) if p and not p.isdigit()]
    return " ".join(p.capitalize() for p in parts) if len(parts) >= 2 else (parts[0].capitalize() if parts else "")


def domain_broker(domain: str, book: dict) -> str:
    toks = [t for t in domain.lower().split(".") if t not in ("com", "tw", "hk", "net", "org", "co", "www", "jp", "sg")]
    for t in toks:
        if t in DOMAIN_BROKER:
            return DOMAIN_BROKER[t]
    abbr = _resolve("_abbr_of")
    for canon, e in (book or {}).items():
        for a in e.get("aliases", {}):
            k = re.sub(r"[^a-z]", "", a.lower())
            if len(k) >= 3 and any(k == t or (len(k) >= 4 and k in t) for t in toks):
                return abbr(book, canon)[0] if abbr else canon
    return ""


def _is_name_line(t: str) -> bool:
    t = t.strip()
    if not t or any(ch.isdigit() for ch in t) or "@" in t or len(t) > 40:
        return False
    if any(w in t for w in TITLES_ZH) or any(re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(w), t) for w in TITLES_EN):
        return False
    if any(k in t for k in ("目標", "評等", "收盤", "股價", "市值", "Rating", "Target", "Price", "Close", "Tel", "電話", "Bloomberg", "Reuters", "Research", "研究")):
        return False
    return bool(re.fullmatch(r"[\u4e00-\u9fff]{2,4}", t) or re.fullmatch(r"[A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+){1,2}", t) or re.fullmatch(r"[\u4e00-\u9fff]{2,4}\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?", t))


def extract_info(p1: dict, book: dict, rating_words: list) -> dict:
    lines = []
    for b in p1["blocks"]:
        if b["kind"] == "text" and b["role"] in ("INFO", "HEADER", "BODY"):
            for l in b.get("lines", []):
                lines.append(dict(l, role=b["role"]))
    lines.sort(key=lambda l: (l["role"] != "INFO", round(l["x0"] / 30), l["top"]))
    info_txt = " ".join(l["text"] for l in lines if l["role"] in ("INFO", "HEADER"))
    all_txt = " ".join(l["text"] for l in lines)
    out = {"analysts": [], "tel_tw": [], "tel_hk": [], "rating": "", "rating_raw": "", "tp": None, "close": None, "date_p1": "", "notes": []}
    for i, l in enumerate(lines):
        for m in EMAIL_RX.finditer(l["text"]):
            local, dom = m.group(1), m.group(2)
            a = {"email": "%s@%s" % (local, dom), "name_from_email": email_name(local), "domain_broker": domain_broker(dom, book), "name": "", "title": "", "tel": ""}
            before = l["text"][:m.start()].strip(" ,;|:：")
            if _is_name_line(before):
                a["name"] = before
            col = [x for x in lines if abs(x["x0"] - l["x0"]) <= 40 and x["top"] < l["top"] and l["top"] - x["top"] <= 60]
            col.sort(key=lambda x: -x["top"])
            for x in col:
                t = x["text"].strip()
                if not a["title"]:
                    tz = next((w for w in TITLES_ZH if w in t), "") or next((w for w in TITLES_EN if re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(w), t)), "")
                    if tz:
                        a["title"] = tz
                        continue
                if not a["tel"]:
                    tm = TEL_TW_RX.search(t) or TEL_HK_RX.search(t)
                    if tm:
                        a["tel"] = tm.group(0)
                        continue
                if not a["name"] and _is_name_line(t):
                    a["name"] = t
                    break
            if not a["tel"]:
                below = [x for x in lines if abs(x["x0"] - l["x0"]) <= 40 and 0 < x["top"] - l["top"] <= 30]
                for x in below:
                    tm = TEL_TW_RX.search(x["text"]) or TEL_HK_RX.search(x["text"])
                    if tm:
                        a["tel"] = tm.group(0)
                        break
            en = a["name_from_email"].lower()
            a["name_check"] = ("✓" if a["name"] and en and (en.replace(" ", "") in a["name"].lower().replace(" ", "") or a["name"].lower().replace(" ", "") in en.replace(" ", "")) else ("中英名(無法直比)" if a["name"] and re.search(r"[\u4e00-\u9fff]", a["name"]) else ("≠" if a["name"] else "只有電郵名")))
            out["analysts"].append(a)
    out["tel_tw"] = sorted({m.group(0) for m in TEL_TW_RX.finditer(all_txt)})[:6]
    out["tel_hk"] = sorted({m.group(0) for m in TEL_HK_RX.finditer(all_txt)})[:6]
    words = sorted(set(list(RATING_NORM) + [w for w in (rating_words or []) if len(w) >= 2]), key=len, reverse=True)
    lab = re.search(r"(?i)(?:評等|投資建議|Rating|Recommendation)\s*[:：]?\s*([^\s|,;]{1,20}(?:\s[A-Za-z\-]+)?)", info_txt or all_txt)
    cand = lab.group(1) if lab else ""
    for w in words:
        rx = (r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(w)) if w.isascii() else re.escape(w)
        if (cand and re.search(rx, cand)) or (not cand and re.search(rx, info_txt)):
            out["rating_raw"], out["rating"] = w, RATING_NORM.get(w, w)
            break
    m = TP_RX.search(info_txt) or TP_RX.search(all_txt)
    if m:
        out["tp"] = parse_number(m.group(1))
    m = CLOSE_RX.search(info_txt) or CLOSE_RX.search(all_txt)
    if m:
        out["close"] = parse_number(m.group(1))
    price_lab = re.compile(r"(?i)close|收盤|股價|price|價")
    tiers = [[l for l in lines if l["role"] == "HEADER"], [l for l in lines if l["role"] == "BODY" and l["top"] < 0.25 * p1["H"]], [l for l in lines if l["role"] == "INFO" and not price_lab.search(l["text"])]]
    found = None
    for tier in tiers:                       # 報告日:頁首優先 → 首頁上緣 → 資訊區(跳過收盤價旁的日期)
        txt = " ".join(l["text"] for l in tier)
        for rx, kind in DATE_RXS:
            mm = rx.search(txt)
            if mm:
                found = (mm, kind)
                break
        if found:
            break
    for mm, kind in ([found] if found else []):
        try:
            if kind == "ymd":
                d = datetime.date(int(mm.group(1)), int(mm.group(2)), int(mm.group(3)))
            elif kind == "roc":
                d = datetime.date(int(mm.group(1)) + 1911, int(mm.group(2)), int(mm.group(3)))
            elif kind == "dmy":
                d = datetime.date(int(mm.group(3)), _MON[mm.group(2)[:3].lower()], int(mm.group(1)))
            else:
                d = datetime.date(int(mm.group(3)), _MON[mm.group(1)[:3].lower()], int(mm.group(2)))
            out["date_p1"] = d.isoformat()
            break
        except ValueError:
            continue
    return out


# ───────── 資料庫對照(VDF 資料庫唯讀):收盤 · 報告日前最後交易日 adj close · 最新 adj close · TP(adj)─────────
_PX = {}


def _price_source() -> dict:
    if _PX:
        return _PX
    _PX.update(kind="", path="", table="", cols={}, note="")
    roots = []
    vr = _resolve("via_roots")
    if vr:
        roots.append(vr()["vdf_database"])
    for x in ((_resolve("config_get") or (lambda: {}))().get("price_db") or []):
        roots.append(Path(x))
    cands = []
    for r in roots:
        if r.is_file():
            cands.append(r)
        elif r.is_dir():
            cands += [q for q in r.rglob("*") if q.is_file() and q.suffix.lower() in (".duckdb", ".db", ".csv", ".parquet") and "_superseded" not in q.parts]
    best = None

    def pick_cols(cols):
        low = {c.lower().replace(" ", "_"): c for c in cols}
        code = next((low[k] for k in ("ticker", "stock_id", "code", "symbol", "stock_code", "證券代號", "代號") if k in low), None)
        date = next((low[k] for k in ("date", "trade_date", "日期", "dt") if k in low), None)
        close = next((low[k] for k in ("close", "收盤價", "收盤", "close_price") if k in low), None)
        adj = next((low[k] for k in ("adj_close", "adjclose", "adj_close_price", "還原收盤", "adjusted_close") if k in low), None)
        return {"code": code, "date": date, "close": close, "adj": adj} if code and date and (close or adj) else None
    for q in sorted(cands, key=lambda q: q.stat().st_mtime, reverse=True)[:120]:
        try:
            if q.suffix.lower() in (".duckdb", ".db"):
                import duckdb  # noqa: WPS433
                con = duckdb.connect(str(q), read_only=True)
                for sch, tb in con.execute("select table_schema, table_name from information_schema.tables").fetchall():
                    cols = [r[0] for r in con.execute("select column_name from information_schema.columns where table_schema=? and table_name=?", [sch, tb]).fetchall()]
                    pc = pick_cols(cols)
                    if pc:
                        score = (1 if pc["adj"] else 0, q.stat().st_mtime)
                        if not best or score > best[0]:
                            best = (score, {"kind": "duckdb", "path": str(q), "table": '"%s"."%s"' % (sch, tb), "cols": pc})
                con.close()
            elif q.suffix.lower() == ".csv":
                with q.open(encoding="utf-8-sig", errors="replace") as fh:
                    hdr = fh.readline().strip().split(",")
                pc = pick_cols(hdr)
                if pc:
                    score = (1 if pc["adj"] else 0, q.stat().st_mtime)
                    if not best or score > best[0]:
                        best = (score, {"kind": "csv", "path": str(q), "table": "", "cols": pc})
            elif q.suffix.lower() == ".parquet":
                import duckdb  # noqa: WPS433
                cols = duckdb.sql("select * from read_parquet('%s') limit 0" % str(q).replace("'", "''")).columns
                pc = pick_cols(cols)
                if pc:
                    score = (1 if pc["adj"] else 0, q.stat().st_mtime)
                    if not best or score > best[0]:
                        best = (score, {"kind": "parquet", "path": str(q), "table": "", "cols": pc})
        except Exception:  # noqa: BLE001
            continue
    if best:
        _PX.update(best[1])
    else:
        _PX["note"] = "VDF 資料庫裡找不到含 代號/日期/收盤(或 adj close)的價格表"
    return _PX


def prices_for(codes: set) -> dict:
    src = _price_source()
    out = defaultdict(list)
    if not src.get("kind") or not codes:
        return out
    c = src["cols"]
    norm = lambda v: re.sub(r"\.TWO?$", "", str(v).strip().upper())  # noqa: E731
    try:
        if src["kind"] == "csv":
            import csv as _csv
            with open(src["path"], encoding="utf-8-sig", errors="replace") as fh:
                for r in _csv.DictReader(fh):
                    k = norm(r.get(c["code"], ""))
                    if k in codes:
                        out[k].append((str(r.get(c["date"], ""))[:10], parse_number(r.get(c["close"], "")) if c["close"] else None, parse_number(r.get(c["adj"], "")) if c["adj"] else None))
        else:
            import duckdb  # noqa: WPS433
            sel = ", ".join('"%s"' % x for x in (c["code"], c["date"], c["close"] or c["adj"], c["adj"] or c["close"]))
            frm = src["table"] if src["kind"] == "duckdb" else "read_parquet('%s')" % src["path"].replace("'", "''")
            con = duckdb.connect(src["path"], read_only=True) if src["kind"] == "duckdb" else duckdb.connect()
            keys = sorted(codes | {k + ".TW" for k in codes} | {k + ".TWO" for k in codes})
            q = "select %s from %s where cast(\"%s\" as varchar) in (%s)" % (sel, frm, c["code"], ",".join("'%s'" % k for k in keys))
            for code, d, cl, adj in con.execute(q).fetchall():
                out[norm(code)].append((str(d)[:10], float(cl) if cl is not None and c["close"] else None, float(adj) if adj is not None and c["adj"] else None))
            con.close()
    except Exception as exc:  # noqa: BLE001
        src["note"] = "讀價格失敗 %s:%s" % (type(exc).__name__, str(exc)[:60])
    for k in out:
        out[k].sort()
    return out


def db_check(row: dict, info: dict, px: dict, master: dict) -> dict:
    code, rd = row.get("code", ""), row.get("date", "")
    ent = master.get(code) or {}
    r = {"in_master": bool(ent), "master_name": ent.get("name", ""), "name_ok": bool(ent) and (row.get("name", "").replace("-KY", "") in ent.get("name", "") or ent.get("name", "").replace("-KY", "") in row.get("name", "")),
         "close_before": None, "adj_before": None, "date_before": "", "adj_latest": None, "date_latest": "", "tp_adj": None, "close_ok": None, "note": ""}
    series = px.get(code) or []
    if not series:
        r["note"] = "價格表沒有 %s" % code if _PX.get("kind") else (_PX.get("note") or "無價格表")
        return r
    before = [s for s in series if s[0] < rd] if rd else []
    if before:
        r["date_before"], r["close_before"], r["adj_before"] = before[-1]
    r["date_latest"], _c, r["adj_latest"] = series[-1]
    if r["adj_latest"] is None:
        r["adj_latest"] = _c
    tp = info.get("tp")
    if tp and r["close_before"] and r["adj_before"]:
        r["tp_adj"] = round(tp * r["adj_before"] / r["close_before"], 2)
    elif tp and r["adj_before"] is None:
        r["note"] = "價格表無 adj close → TP(adj) 不算(誠實 SKIPPED)"
    cl = info.get("close")
    if cl and r["close_before"]:
        r["close_ok"] = abs(cl - r["close_before"]) / r["close_before"] <= 0.03
    return r


# ───────── 第一步:四類分類器(上傳的 VRN_ReportClassifier;讀取用 pdfplumber,不另需 PyMuPDF)─────────
_CLS = {}


def classifier() -> dict:
    if _CLS:
        return _CLS
    cfg = (_resolve("config_get") or (lambda: {}))()
    cands = [Path(cfg["classifier_path"])] if cfg.get("classifier_path") else []
    cands += sorted(_home().glob("VRN_ReportClassifier_v*.py")) + sorted((_home() / "intake").rglob("VRN_ReportClassifier_v*.py"))
    _CLS.update(file="", mod=None, err="")
    for p in reversed(cands):
        if p.is_file():
            try:
                _CLS["mod"] = _load_v0157(p, "vrn_report_classifier_for_v0157")
                _CLS["file"] = str(p)
                break
            except Exception as exc:  # noqa: BLE001
                _CLS["err"] = "%s:%s" % (type(exc).__name__, str(exc)[:60])
    if not _CLS["mod"] and not _CLS["err"]:
        _CLS["err"] = "找不到 VRN_ReportClassifier(放 VRN\\intake\\VRN_ReportClassifier\\)"
    return _CLS


def classify_file(path: str) -> dict:
    c = classifier()
    if not c.get("mod"):
        return {"category": None, "status": "NO_ENGINE", "why": c.get("err", "")}
    p = Path(path)
    try:
        if p.suffix.lower() == ".pdf":
            import pdfplumber
            with pdfplumber.open(str(p)) as pdf:
                pages = pdf.pages[:3]
                texts = [(pg.extract_text() or "") for pg in pages]
                header = ""
                if pages:
                    pg = pages[0]
                    header = pg.crop((0, 0, float(pg.width), float(pg.height) * 0.42)).extract_text() or ""
                n = len(pdf.pages)
            doc = {"filename": p.name, "title": "", "header": header, "front": texts[0] if texts else "", "text": "\n".join(texts), "metadata": {}, "blocks": [], "reader": ["pdfplumber(VRN v0157)"], "warnings": [], "page_count": n, "pages_read": len(texts)}
        elif p.suffix.lower() in (".txt", ".md", ".json"):
            doc = c["mod"].def_read_document(str(p))
        else:
            return {"category": None, "status": "SKIP", "why": "檔型 %s 不送分類器" % p.suffix}
        r = c["mod"].def_classify(doc)
        return {"category": r.get("category"), "candidate": r.get("candidate_category"), "status": r.get("status"), "confidence": r.get("confidence"), "why": str(r.get("reason", ""))[:80], "subtype": r.get("subtype")}
    except Exception as exc:  # noqa: BLE001
        return {"category": None, "status": "ERROR", "why": "%s:%s" % (type(exc).__name__, str(exc)[:60])}


# ───────── 第二步:LAYOUT NON-OCR 識別(多程序 · 結果落 TEMP)─────────
_CTX = {}


def _init_worker(book, master, ratings, opts):
    _CTX.update(book=book, master=master, ratings=ratings, opts=opts)


def _job(kind: str, item):
    if kind == "cls":
        return dict(classify_file(item), path=item)
    return l2_one(item)


def _pool_map(kind: str, items: list, workers: int, initargs: tuple) -> tuple:
    out = []
    if workers > 1 and len(items) > 1:
        try:
            import multiprocessing as _mp
            from concurrent.futures import ProcessPoolExecutor, as_completed
            with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=initargs, mp_context=_mp.get_context("spawn")) as ex:   # Windows 只有 spawn;各平台一致
                futs = {ex.submit(_job, kind, it): it for it in items}
                for i, fu in enumerate(as_completed(futs), 1):
                    it = futs[fu]
                    try:
                        out.append(fu.result())
                    except Exception as exc:  # noqa: BLE001
                        out.append({"file": Path(it if isinstance(it, str) else it.get("path", "?")).name, "path": it if isinstance(it, str) else it.get("path"), "lamp": "RED", "status": "ERROR", "notes": ["%s:%s" % (type(exc).__name__, str(exc)[:80])]})
                    if kind == "l2":
                        print("  [進度] %d/%d · %s · %s" % (i, len(items), out[-1].get("lamp"), str(out[-1].get("file", ""))[:50]), flush=True)
            return out, "多程序 ×%d" % workers
        except Exception as exc:  # noqa: BLE001
            out = []
            note = "多程序失敗(%s)→ 單程序" % type(exc).__name__
    else:
        note = "單程序"
    _init_worker(*initargs)
    for i, it in enumerate(items, 1):
        try:
            out.append(_job(kind, it))
        except Exception as exc:  # noqa: BLE001
            out.append({"file": Path(it if isinstance(it, str) else it.get("path", "?")).name, "lamp": "RED", "notes": ["%s:%s" % (type(exc).__name__, str(exc)[:80])]})
        if kind == "l2":
            print("  [進度] %d/%d · %s · %s" % (i, len(items), out[-1].get("lamp"), str(out[-1].get("file", ""))[:50]), flush=True)
    return out, note


def l2_one(row: dict) -> dict:
    import pdfplumber
    t0 = time.time()
    book, master, opts = _CTX.get("book", {}), _CTX.get("master", {}), _CTX.get("opts", {})
    src = Path(row.get("mini") or row.get("src_pdf") or row["path"])
    pick = row.get("picked") or [1]
    an, ff = _resolve("analyze_page"), _resolve("_footer_fix")
    pages = []
    with pdfplumber.open(str(src)) as pdf:
        local = list(range(1, len(pdf.pages) + 1)) if row.get("mini") else pick
        p1t = pdf.pages[local[0] - 1].extract_text() or ""
        for i, lp in enumerate(local):
            page = pdf.pages[lp - 1]
            pg = an(pdf, lp, str(src), annual=(i > 0), tabula_ok=bool(opts.get("tabula")))
            orig = pick[i] if i < len(pick) else lp
            if orig != pg["page"]:
                for b in pg["blocks"]:
                    b["id"] = re.sub(r"^P\d+·", "P%d·" % orig, b["id"])
                pg["page"] = orig
            ff(pg)
            for b in pg["blocks"]:
                if b["kind"] == "text":
                    b["text"], b["joins"], b["sus"] = rejoin(b.get("lines", []))
            pg["coverage"] = coverage(page, pg["blocks"])
            for b in pg["blocks"]:
                if b["kind"] == "table":
                    b["page"] = orig
                    rr = repair_table(b, page)
                    b["rows"], b["fixes"] = rr["rows"], rr["fixes"]
                    b["sub"] = _resolve("_table_cat")(b["rows"], b["role"])
                    b["verify"] = verify_table(b, page)
            pages.append(pg)
    hier = _resolve("_hierarchy")(pages)
    body = (hier.get("body") or {}).get("size") or 0
    ts = _resolve("_text_subcat")
    for pg in pages:
        for b in pg["blocks"]:
            if b["kind"] == "text":
                b["sub"] = "頁尾/免責" if b["role"] == "FOOTER" else ts(b, hier)
                b["eng394"] = _e394_text(b, body)
            b["units"] = units_of(b)
    f = {"code": row.get("code"), "broker": row.get("broker")}
    title = _resolve("_main_title")(pages[0], hier, f, book)
    for b in pages[0]["blocks"]:
        if b["id"] == title.get("id"):
            b["sub"] = "主標題"
            b["units"] = [("標題", b["text"])]
    ftxt = " ".join(b.get("text", "") for pg in pages for b in pg["blocks"] if b["role"] == "FOOTER")
    mb, abf = _resolve("match_broker"), _resolve("_abbr_of")
    canon = mb(ftxt, book)[0] if ftxt else ""
    fab = abf(book, canon)[0] if canon else ""
    info = extract_info(pages[0], book, _CTX.get("ratings", []))
    conf = {}
    if row.get("code"):
        conf["代號"] = bool(re.search(r"(?<!\d)%s(?!\d)" % re.escape(row["code"]), p1t))
    if row.get("name"):
        conf["名稱"] = row["name"].replace("-KY", "") in p1t
    covs = [pg["coverage"]["pct"] for pg in pages]
    tblocks = [b for pg in pages for b in pg["blocks"] if b["kind"] == "table"]
    txt_blocks = [b for pg in pages for b in pg["blocks"] if b["kind"] == "text"]
    classified = sum(1 for b in txt_blocks if b.get("sub")) / max(1, len(txt_blocks))
    text_ok = min(covs) >= 99.5 and classified >= 0.999
    annual = [pg["page"] for pg in pages[1:]]
    table_ok = bool(tblocks) and all(b["verify"]["ok"] for b in tblocks) if annual else all(b["verify"]["ok"] for b in tblocks)
    units = Counter(u[0] for pg in pages for b in pg["blocks"] if b["role"] != "FOOTER" for u in b.get("units", []))
    res = {"file": row["file"], "path": row["path"], "code": row.get("code", ""), "name": row.get("name", ""), "broker": row.get("broker", ""), "date": row.get("date", ""), "yf": row.get("yf", ""), "bbg": row.get("bbg", ""),
           "picked": pick, "pages_total": row.get("pages_total"), "title": title.get("text", ""), "confirm": conf, "cov_min": min(covs), "cov_pages": dict(zip([pg["page"] for pg in pages], covs)), "missing": sum(pg["coverage"]["missing"] for pg in pages),
           "units": dict(units), "joins": sum(b.get("joins", 0) for b in txt_blocks), "sus": sum(b.get("sus", 0) for b in txt_blocks), "classified": round(classified * 100, 1), "tables": len(tblocks), "tables_ok": sum(1 for b in tblocks if b["verify"]["ok"]),
           "repairs": sum(len(b.get("fixes", [])) for b in tblocks), "e394": sum(1 for b in txt_blocks if b.get("eng394")), "split": "INFO" in pages[0]["roles"].values() and "BODY" in pages[0]["roles"].values(), "annual": annual,
           "footer_broker": fab, "info": info, "text_ok": text_ok, "table_ok": table_ok, "secs": round(time.time() - t0, 1)}
    res["step2_ok"] = text_ok and table_ok
    notes = []
    if not text_ok:
        notes.append("文字還原 %.1f%%%s" % (min(covs), "" if classified >= 0.999 else " · 有未分類段"))
    if not table_ok:
        notes.append("表格 %d/%d 過" % (res["tables_ok"], res["tables"]) if tblocks else "年度頁沒抽到表")
    if res["sus"]:
        notes.append("疑錯接 %d" % res["sus"])
    if conf and not all(conf.values()):
        notes.append("首頁沒對到 " + "/".join(k for k, v in conf.items() if not v))
    res["notes"] = notes
    res["lamp"] = "GREEN" if res["step2_ok"] and not res["sus"] and all(conf.values()) else ("YELLOW" if text_ok or table_ok else "RED")
    tmpd = Path(row.get("temp") or tempfile.gettempdir()) / "layout_l2"
    tmpd.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(row["path"].encode("utf-8")).hexdigest()[:8]
    full = {"row": row, "pages": pages, "hier": hier, "title": title, "info": info, "summary": res}
    (tmpd / (key + ".json")).write_text(json.dumps(full, ensure_ascii=False, default=str), encoding="utf-8")
    res["temp_json"] = str(tmpd / (key + ".json"))
    out_dir = _rep() / "layout"
    out_dir.mkdir(parents=True, exist_ok=True)
    view = {"file": row["file"], "pages": [dict(pg, blocks=[b for b in pg["blocks"] if b["role"] != "FOOTER"]) for pg in pages], "hier": hier, "title": title, "info": {}, "annual": annual, "n_tables": len(tblocks), "n_fixes": res["repairs"],
            "secs": res["secs"], "confirm": conf, "pages_total": row.get("pages_total"), "notes": notes, "lamp": res["lamp"], "id": {k: row.get(k, "") for k in ("code", "yf", "bbg", "name", "broker", "date")}}
    h = _resolve("_file_html")(view)
    h = h.replace("<div class='two'>", _restore_panel(res, pages, info) + "<div class='two'>", 1)
    page_html = out_dir / ("%s_%s.html" % (key, re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", Path(row["file"]).stem)[:60]))
    page_html.write_text(h, encoding="utf-8")
    res["html"] = str(page_html)
    return res


def _restore_panel(res: dict, pages: list, info: dict) -> str:
    e = html.escape
    ok = lambda b: "<b style='color:#15803d'>✓</b>" if b else "<b style='color:#b91c1c'>✗</b>"  # noqa: E731
    cov = "".join("<tr><td>P%d</td><td style='text-align:right'>%.2f%%</td><td style='text-align:right'>%d</td><td class='note'>%s</td></tr>" % (pg["page"], pg["coverage"]["pct"], pg["coverage"]["missing"], e(" / ".join(pg["coverage"]["miss_snippets"][:4]))) for pg in pages)
    tbl = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td style='text-align:right'>%.0f%%</td><td style='text-align:right'>%s</td><td>%s</td><td>%s</td><td class='note'>%s</td></tr>" % (e(b["id"]), e(b.get("sub", "")), ok(b["verify"]["ok"]), b["verify"]["parse_rate"] * 100, ("%.1f%%" % b["verify"]["text_cov"]) if b["verify"]["text_cov"] is not None else "—", e(b["verify"]["arith"]), e(b["verify"]["unit"]), e("; ".join(b.get("fixes", []) + b["verify"]["issues"])[:160])) for pg in pages for b in pg["blocks"] if b["kind"] == "table")
    an = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (e(a.get("name") or "—"), e(a.get("name_from_email", "")), e(a.get("name_check", "")), e(a.get("title") or "—"), e(a.get("email", "")), e(a.get("tel") or "—")) for a in info.get("analysts", []))
    un = " · ".join("%s %d" % kv for kv in sorted(res["units"].items()))
    return ("<div class='pg' style='margin:0 0 8px'><h2 style='font-size:13px;margin:0 0 6px'>第二步 LAYOUT NON-OCR 識別 · 文字還原 %s · 表格還原 %s · %s</h2>"
            "<div class='row' style='flex-wrap:wrap'><div style='flex:1;min-width:260px'><div class='note'>位置覆蓋(每個字都落在已分類區塊)</div><table class='hier'><tr><th>頁</th><th>覆蓋</th><th>漏字</th><th>漏的片段</th></tr>%s</table>"
            "<div class='note' style='margin-top:4px'>單位:%s · 連接斷句 %d · 疑錯接 %d · 分類完成 %.1f%%</div></div>"
            "<div style='flex:1;min-width:300px'><div class='note'>資訊區抽取 · 評等 %s(%s)· 目標價 %s · 收盤 %s · 首頁日期 %s · 台灣電話 %s · 香港電話 %s</div><table class='hier'><tr><th>分析師</th><th>電郵名</th><th>比對</th><th>職稱</th><th>電郵</th><th>電話</th></tr>%s</table></div></div>"
            "<div class='note' style='margin-top:6px'>表格驗證(表頭 · 列長齊 · 無合併數字格 · 數字可解析 ≥90%% · 表內字還原 ≥98%% · 算術)</div><table class='hier'><tr><th>編號</th><th>分類</th><th>過</th><th>可解析</th><th>表內字</th><th>算術</th><th>單位</th><th>修補 / 問題</th></tr>%s</table></div>") % (
        ok(res["text_ok"]), ok(res["table_ok"]), "第二步成功" if res["step2_ok"] else "第二步未過", cov, e(un), res["joins"], res["sus"], res["classified"],
        e(info.get("rating") or "—"), e(info.get("rating_raw") or ""), info.get("tp") or "—", info.get("close") or "—", e(info.get("date_p1") or "—"), e(", ".join(info.get("tel_tw", [])) or "—"), e(", ".join(info.get("tel_hk", [])) or "—"), an or "<tr><td colspan='6' class='note'>沒找到電郵</td></tr>", tbl or "<tr><td colspan='8' class='note'>無表</td></tr>")


# ───────── 三頁:第一步 · 第二步 · 交互驗證 ─────────
_L = {"GREEN": "var(--lamp-green,#16a34a)", "YELLOW": "var(--lamp-yellow,#eab308)", "RED": "var(--lamp-red,#dc2626)", "GRAY": "var(--lamp-gray,#9ca3af)"}
_ORD = {"RED": 0, "YELLOW": 1, "GREEN": 2, "GRAY": 3}


def _page(title: str, meta: str, head: list, rows: list) -> str:
    css = (_resolve("_CSS") or "") + "table.m{border-collapse:collapse;width:100%;background:#fff;font-size:11.5px}table.m th,table.m td{border:1px solid #eceff3;padding:2px 5px;text-align:left;vertical-align:top}table.m th{background:#111827;color:#fff;position:sticky;top:0}.bar button{font-size:11px;margin-right:4px;padding:2px 8px;border:1px solid #d1d5db;background:#fff;border-radius:6px;cursor:pointer}td.n{text-align:right}"
    js = "function f(l){document.querySelectorAll('tbody tr').forEach(function(t){t.style.display=(!l||t.dataset.l===l)?'':'none'})}"
    trs = "".join("<tr data-l='%s'><td><i class='lp %s' style='background:%s'></i></td>%s</tr>" % (l, l, _L.get(l, "#9ca3af"), "".join("<td%s>%s</td>" % (" class='n'" if isinstance(c, (int, float)) else "", c if isinstance(c, str) and c.startswith("<") else html.escape(str(c))) for c in cells)) for l, cells in rows)
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>" + html.escape(title) + "</title><style>" + css + "</style><script>" + js + "</script></head><body><h1>" + html.escape(title) + "</h1><div class='meta'>" + meta +
            "</div><div class='bar' style='margin:6px 0'><button onclick=\"f('')\">全部</button><button onclick=\"f('RED')\">紅</button><button onclick=\"f('YELLOW')\">黃</button><button onclick=\"f('GREEN')\">綠</button><button onclick=\"f('GRAY')\">灰</button></div><div style='overflow-x:auto'><table class='m'><thead><tr><th>燈</th>" +
            "".join("<th>%s</th>" % html.escape(h) for h in head) + "</tr></thead><tbody>" + trs + "</tbody></table></div></body></html>")


def _link(r):
    return ("<a href='%s'>%s</a>" % (Path(r["html"]).name, html.escape(r["file"]))) if r.get("html") else html.escape(r["file"])


def write_pages(stage_rows: list, cls: dict, l2: list, xc: dict, s: dict) -> dict:
    out = _rep() / "layout"
    out.mkdir(parents=True, exist_ok=True)
    r1 = []
    for r in sorted(stage_rows, key=lambda x: x["file"]):
        c = cls.get(r["path"], {})
        lamp = "RED" if r.get("lamp") == "RED" else ("GRAY" if not r.get("picked") else ("YELLOW" if (not r.get("annual")) or (c.get("status") == "ACCEPTED" and c.get("category") != "SINGLE_STOCK") else "GREEN"))
        r1.append((lamp, [r["file"], "%s · %s" % (c.get("category") or c.get("candidate") or "—", c.get("status") or "—"), c.get("confidence") if c.get("confidence") is not None else "", r.get("date", ""), r.get("code", ""), r.get("name", ""), r.get("broker", ""), r.get("status", ""), ",".join("P%d" % x for x in r.get("picked") or []) or "—", r.get("pages_total") or "", r.get("convert", "")]))
    r1.sort(key=lambda x: (_ORD.get(x[0], 9), x[1][0]))
    p1 = out / "STEP1_latest.html"
    p1.write_text(_page("第一步 · 輸入判讀 / 四類分類 / 只取個股第一頁 + 年度財報頁 → TEMP", "%s · 檔 %d · 處理 %d · 不碰 %d · 分類器 %s · TEMP %s" % (s["ts"], len(stage_rows), s["staged"], len(stage_rows) - s["staged"], html.escape(s["classifier"]), html.escape(s["temp"])),
                        ["檔", "分類器(類別 · 狀態)", "信心", "報告日", "代號", "名稱", "券商", "第一步狀態", "取頁", "總頁", "轉換"], r1), encoding="utf-8")
    r2 = []
    for r in sorted(l2, key=lambda x: (_ORD.get(x.get("lamp"), 9), x.get("file", ""))):
        if "cov_min" not in r:
            r2.append(("RED", [r.get("file", ""), "—", "—", "—", "—", "—", "—", "—", "—", "—", "; ".join(r.get("notes", []))]))
            continue
        inf = r["info"]
        ana = "; ".join("%s%s" % (a.get("name") or a.get("name_from_email"), ("(%s)" % a["title"]) if a.get("title") else "") for a in inf.get("analysts", [])) or "—"
        r2.append((r["lamp"], [_link(r), "%.2f%%" % r["cov_min"], r["missing"], " ".join("%s%d" % kv for kv in sorted(r["units"].items())), "%d / %d" % (r["joins"], r["sus"]), "%s%%" % r["classified"], "%d/%d" % (r["tables_ok"], r["tables"]), r["repairs"],
                                   "✓" if r["text_ok"] else "✗", "✓" if r["table_ok"] else "✗", "%s · %s · TP %s · 收 %s" % (ana, inf.get("rating") or "—", inf.get("tp") or "—", inf.get("close") or "—")]))
    p2 = out / "STEP2_latest.html"
    p2.write_text(_page("第二步 · LAYOUT NON-OCR 識別 · 文字還原 / 表格還原 / 修復與驗證", "%s · 處理 %d · 第二步成功 %d(文字 %d · 表格 %d)· 表 %d(過 %d)· 修補 %d · %s · %.0f 秒 · 結果 JSON 在 TEMP" % (s["ts"], s["staged"], s["ok"], s["text_ok"], s["table_ok"], s["tables"], s["tables_ok"], s["repairs"], html.escape(s["mode"]), s["secs"]),
                        ["檔(點開看版面)", "文字覆蓋(最低頁)", "漏字", "單位(句 · 標題 · 資料 · 條列 · 表列)", "連接斷句 / 疑錯接", "分類完成", "表過", "修補", "文字", "表格", "資訊區(分析師 · 評等 · TP · 收盤)"], r2), encoding="utf-8")
    r3 = []
    for r in sorted(l2, key=lambda x: x.get("file", "")):
        if "cov_min" not in r:
            continue
        x = xc.get(r["path"], {})
        inf = r["info"]
        doms = sorted({a.get("domain_broker") for a in inf.get("analysts", []) if a.get("domain_broker")})
        checks = {"代號首頁": r["confirm"].get("代號"), "代號在清單": x.get("in_master"), "名稱": x.get("name_ok") if x.get("in_master") else r["confirm"].get("名稱"), "頁尾券商": (r["footer_broker"] == r["broker"]) if r["footer_broker"] else None,
                  "電郵網域券商": (r["broker"] in doms) if doms else None, "首頁日期": (inf.get("date_p1") == r["date"]) if inf.get("date_p1") else None, "收盤 vs DB": x.get("close_ok")}
        bad = [k for k, v in checks.items() if v is False]
        lamp = "YELLOW" if bad else ("GREEN" if any(v for v in checks.values()) else "GRAY")
        mark = lambda v: "✓" if v else ("✗" if v is False else "—")  # noqa: E731
        r3.append((lamp, [_link(r), "%s %s · 首頁%s · 清單%s" % (r["code"], r["yf"], mark(checks["代號首頁"]), mark(checks["代號在清單"])), "%s · %s%s" % (r["name"], x.get("master_name") or "—", mark(checks["名稱"])),
                          "檔名 %s · 頁尾 %s%s · 網域 %s%s" % (r["broker"] or "—", r["footer_broker"] or "—", mark(checks["頁尾券商"]), ",".join(doms) or "—", mark(checks["電郵網域券商"])), "%s · 首頁 %s%s" % (r["date"], inf.get("date_p1") or "—", mark(checks["首頁日期"])),
                          inf.get("rating") or "—", inf.get("tp") or "—", x.get("tp_adj") or "—", "%s · DB %s(%s)%s" % (inf.get("close") or "—", x.get("close_before") or "—", x.get("date_before") or "—", mark(checks["收盤 vs DB"])),
                          "%s(%s)" % (x.get("adj_before") or "—", x.get("date_before") or "—"), "%s(%s)" % (x.get("adj_latest") or "—", x.get("date_latest") or "—"), "; ".join(bad) or x.get("note", "")]))
    r3.sort(key=lambda x: (_ORD.get(x[0], 9), x[1][0]))
    p3 = out / "XCHECK_latest.html"
    p3.write_text(_page("交互驗證 · 檔名 ↔ 首頁 ↔ 頁尾/電郵 ↔ 資料庫", "%s · 價格表 %s · 總清單 %d 碼" % (s["ts"], html.escape(s["price_src"]), s["master_n"]),
                        ["檔", "代號(yfinance)", "名稱(清單)", "券商(檔名 · 頁尾 · 電郵網域)", "報告日", "評等", "目標價", "TP(adj)", "收盤 vs DB 報告日前", "adj close 報告日前", "最新 adj close", "不符"], r3), encoding="utf-8")
    return {"step1": str(p1), "step2": str(p2), "xcheck": str(p3)}


def layout_run_v157(d: Path, opts: dict) -> dict:
    t0 = time.time()
    now = datetime.datetime.now()
    cfg = (_resolve("config_get") or (lambda: {}))()
    files = sorted(str(p) for p in d.iterdir() if p.is_file() and not p.name.startswith("~$") and p.suffix.lower() in (".pdf", ".txt", ".md")) if d.is_dir() else []
    master, _ = _resolve("_load_roster_v154")(True)
    book, _ = _resolve("load_brokers_v154")()
    ratings = (_resolve("_ratings") or (lambda: []))()
    initargs = (book, master, ratings, opts)
    cls_rows, _m = _pool_map("cls", files, opts["workers"], initargs)
    cls = {r["path"]: r for r in cls_rows}
    man = _resolve("stage_run")(d, False, opts.get("only", ""))
    for r in man["rows"]:
        c = cls.get(r["path"], {})
        if r.get("picked") and c.get("status") == "ACCEPTED" and c.get("category") not in (None, "SINGLE_STOCK"):
            r.update(status="分類器 %s(%s)→ 這次不碰" % (c.get("category"), c.get("confidence")), picked=None)
        elif not r.get("picked") and c.get("status") == "ACCEPTED" and c.get("category") == "SINGLE_STOCK" and not r.get("code"):
            r["status"] = "分類器說個股但檔名無代號 → 人看"
        r["temp"] = man["temp"]
    todo = [r for r in man["rows"] if r.get("picked")]
    if opts.get("max"):
        todo = todo[:opts["max"]]
    l2, mode = _pool_map("l2", todo, opts["workers"], initargs)
    px = prices_for({r["code"] for r in l2 if r.get("code")})
    xc = {r["path"]: db_check(r, r.get("info", {}), px, master) for r in l2 if "cov_min" in r}
    src = _price_source()
    s = {"ts": now.isoformat(timespec="seconds"), "staged": len(todo), "ok": sum(1 for r in l2 if r.get("step2_ok")), "text_ok": sum(1 for r in l2 if r.get("text_ok")), "table_ok": sum(1 for r in l2 if r.get("table_ok")),
         "tables": sum(r.get("tables", 0) for r in l2), "tables_ok": sum(r.get("tables_ok", 0) for r in l2), "repairs": sum(r.get("repairs", 0) for r in l2), "mode": mode, "secs": time.time() - t0,
         "classifier": classifier().get("file") or classifier().get("err", ""), "temp": man["temp"], "price_src": ("%s %s" % (src.get("kind"), src.get("path"))) if src.get("kind") else (src.get("note") or "無"), "master_n": len(master),
         "lamps": dict(Counter(r.get("lamp") for r in l2)), "e394": eng394_bind(), "sus": sum(r.get("sus", 0) for r in l2), "cov_full": sum(1 for r in l2 if r.get("cov_min", 0) >= 99.5)}
    pages = write_pages(man["rows"], cls, l2, xc, s)
    (_rep() / "layout" / "L2_latest.json").write_text(json.dumps({"summary": {k: v for k, v in s.items() if k != "e394"}, "rows": l2, "xcheck": xc}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return {"summary": s, "pages": pages, "rows": l2, "cls": cls, "xc": xc, "stage": man}


# ───────── 引擎稽核:版本 · 註冊於 VRN SSOT · 加速器(PY 與 PS 一樣)─────────
_SKIP = {"_superseded", "intake", "references", "__pycache__", "output", "output_hub", "staging", "generations", "_quarantine", "input", "bridges", "node_modules", "target", "evidence_uploads", "_runs"}
_PIPE = {"VRN_SystemManager": "第一步 / 第二步主控", "VRN_ENG394_LayoutRestore": "第二步子分類(_subcat)", "VRN_ReportClassifier": "第一步四類分類"}


def engines_audit(register: bool = False) -> dict:
    home = _home()
    files = []
    for p in home.rglob("*"):
        try:
            rel = p.relative_to(home)
        except ValueError:
            continue
        if p.is_file() and p.suffix.lower() in (".py", ".ps1") and not (set(rel.parts[:-1]) & _SKIP) and not any(x.startswith("_superseded") for x in rel.parts[:-1]):
            files.append(p)
    for p in (home / "intake").rglob("VRN_ReportClassifier_v*.py") if (home / "intake").is_dir() else []:
        files.append(p)
    corpus = []
    for d in (home / "registry", home / "SSOT"):
        if d.is_dir():
            for q in d.glob("*.json*"):
                try:
                    if q.stat().st_size < 40 * 1024 * 1024:
                        corpus.append(q.read_text(encoding="utf-8", errors="replace").lower())
                except OSError:
                    pass
    corpus = "\n".join(corpus)
    fams = defaultdict(list)
    for p in files:
        fam = re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", p.stem)
        fam = re.sub(r"_sha[0-9a-f]{6,}$", "", fam)
        fams[(fam, p.suffix.lower())].append(p)
    py_ok = re.compile(r"\[VIA:ACCEL-BRIDGE|import\s+VeritasCeleritas_v\d+|from\s+VeritasCeleritas_v\d+|VIA_SuperAccel_Module|SUP_MDL737_SuperAccelModule")
    ps_ok = re.compile(r"Initialize-VCAccel|VeritasCeleritas\.PS7|CELERITAS-TEMPLATE-JOIN|Invoke-VIACeleritasScoped")
    rows = []
    for (fam, ext), ps in sorted(fams.items()):
        ps.sort(key=lambda q: (_vnum_v0157(q.stem), q.name))
        tail = ps[-1]
        try:
            txt = tail.read_text(encoding="utf-8", errors="replace")
        except OSError:
            txt = ""
        has_v = bool(re.search(r"_v\d{4}$", tail.stem))
        reg = fam.lower() in corpus or tail.name.lower() in corpus
        acc = bool((py_ok if ext == ".py" else ps_ok).search(txt))
        rows.append({"family": fam, "ext": ext, "tail": str(tail.relative_to(home)) if home in tail.parents else str(tail), "n": len(ps), "version": has_v, "registered": reg, "accel": acc, "pipeline": _PIPE.get(fam, ""), "sha8": hashlib.sha256(tail.read_bytes()).hexdigest()[:8]})
    dl = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads"
    lau = sorted((q for q in dl.glob("Invoke-VIA-Launch-v0*.ps1") if not re.search(r"\(\d+\)", q.name)), key=lambda q: q.name)
    if lau:
        t = lau[-1].read_text(encoding="utf-8", errors="replace")
        rows.append({"family": "Invoke-VIA-Launch(Downloads 現行啟動器)", "ext": ".ps1", "tail": str(lau[-1]), "n": len(lau), "version": True, "registered": True, "accel": bool(ps_ok.search(t)), "pipeline": "啟動器(落地 · 開頁)", "sha8": hashlib.sha256(lau[-1].read_bytes()).hexdigest()[:8]})
    reg_file = ""
    if register:
        rd = home / "registry"
        rd.mkdir(exist_ok=True)
        hits = sorted(rd.glob("VRN_Engine_Register_v*.json"), key=lambda q: _vnum_v0157(q.stem))
        body = {r["family"] + r["ext"]: {"tail": r["tail"], "sha8": r["sha8"], "versions": r["n"], "accel": r["accel"], "pipeline": r["pipeline"]} for r in rows}
        prev = json.loads(hits[-1].read_text(encoding="utf-8")).get("engines") if hits else None
        if prev != body:
            nv = "v%04d" % ((_vnum_v0157(hits[-1].stem) + 1) if hits else 100)
            fp = rd / ("VRN_Engine_Register_%s.json" % nv)
            fp.write_text(json.dumps({"schema": "VIA.VRN.EngineRegister.v1", "version": nv, "prior": hits[-1].name if hits else None, "ts": datetime.datetime.now().isoformat(timespec="seconds"), "rule": "VRN SystemManager 自家引擎登記(只增;內容變才出新版)", "engines": body}, ensure_ascii=False, indent=1), encoding="utf-8")
            reg_file = fp.name
            for r in rows:
                r["registered"] = True
        else:
            reg_file = hits[-1].name + "(無變更)"
    for r in rows:
        r["lamp"] = "GREEN" if r["version"] and r["registered"] and r["accel"] else ("YELLOW" if r["accel"] else "RED")
    py = [r for r in rows if r["ext"] == ".py"]
    psr = [r for r in rows if r["ext"] == ".ps1"]
    s = {"families": len(rows), "py": len(py), "ps1": len(psr), "no_version": sum(1 for r in rows if not r["version"]), "not_registered": sum(1 for r in rows if not r["registered"]), "no_accel_py": sum(1 for r in py if not r["accel"]), "no_accel_ps": sum(1 for r in psr if not r["accel"]), "register": reg_file}
    page = _rep() / "ENGINES_latest.html"
    mark = lambda v: "✓" if v else "✗"  # noqa: E731
    page.write_text(_page("VRN 引擎稽核 · 版本 · 註冊(VRN SSOT)· 加速器(PY / PS)", "族 %d(py %d · ps1 %d)· 無版號 %d · 未註冊 %d · py 無加速器 %d · ps1 無加速器 %d · 註冊冊 %s" % (s["families"], s["py"], s["ps1"], s["no_version"], s["not_registered"], s["no_accel_py"], s["no_accel_ps"], html.escape(reg_file or "未寫(加 --register)")),
                          ["族", "類", "尾版", "版數", "版號", "註冊", "加速器", "管線用途"], [(r["lamp"], [r["family"], r["ext"], r["tail"], r["n"], mark(r["version"]), mark(r["registered"]), mark(r["accel"]), r["pipeline"]]) for r in sorted(rows, key=lambda r: (_ORD[r["lamp"]], r["family"]))]), encoding="utf-8")
    return {"summary": s, "rows": rows, "html": str(page)}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    if args[:1] == ["layout"] and len(args) >= 2 and "--dir" not in args and Path(args[-1]).is_dir():
        args = args[:-1] + ["--dir", args[-1]]
    cfg = (_resolve("config_get") or (lambda: {}))()
    if args[:1] == ["layout"]:
        w = int(opt("--workers", "0") or 0) or max(1, min(3, (os.cpu_count() or 2) - 1))
        o = layout_run_v157(Path(opt("--dir") or cfg.get("input_dir") or r"C:\測試樣本報告"), {"workers": w, "tabula": "--tabula" in args, "max": int(opt("--max", "0") or 0), "only": opt("--only", "") or ""})
        s = o["summary"]
        e = s["e394"]
        print("[計] 第一步 · 檔 %d · 個股報告處理 %d · 分類器 %s" % (len(o["stage"]["rows"]), s["staged"], Path(s["classifier"]).name if os.sep in s["classifier"] or "/" in s["classifier"] else s["classifier"]))
        print("[計] 第二步 LAYOUT NON-OCR · 成功 %d/%d(文字 %d · 表格 %d)· 文字覆蓋≥99.5%% %d · 表 %d 過 %d · 修補 %d · 疑錯接 %d · %s · %.0f 秒 · %s" % (s["ok"], s["staged"], s["text_ok"], s["table_ok"], s["cov_full"], s["tables"], s["tables_ok"], s["repairs"], s["sus"], s["mode"], s["secs"], "GREEN" if s["ok"] == s["staged"] and s["staged"] else "YELLOW"))
        print("[計] ENG394 %s · _subcat %s%s · 價格表 %s · 總清單 %d 碼" % (e.get("file") or "無", "已接(依名綁定)" if e.get("ok") else "未接", (" · " + e["err"]) if e.get("err") else "", s["price_src"], s["master_n"]))
        c = Counter(n.split(" ")[0] for r in o["rows"] for n in r.get("notes", []))
        for k, v in c.most_common(8):
            print("  [YEL] %s · %d 檔" % (k, v))
        for k in ("step1", "step2", "xcheck"):
            print("  [U/I] %s" % o["pages"][k])
        if "--no-audit" not in args:
            ea = engines_audit(register="--register" in args)
            es = ea["summary"]
            print("[計] VRN 引擎稽核 · 族 %d(py %d · ps1 %d)· 無版號 %d · 未註冊 %d · py 無加速器 %d · ps1 無加速器 %d · 註冊冊 %s" % (es["families"], es["py"], es["ps1"], es["no_version"], es["not_registered"], es["no_accel_py"], es["no_accel_ps"], es["register"] or "未寫(加 --register)"))
            for r in [r for r in ea["rows"] if r["pipeline"]]:
                print("  [%s] 管線 %s · %s · 版號%s 註冊%s 加速器%s" % ("OK" if r["lamp"] == "GREEN" else "YEL", r["family"], r["pipeline"], "✓" if r["version"] else "✗", "✓" if r["registered"] else "✗", "✓" if r["accel"] else "✗"))
            print("  [U/I] %s" % ea["html"])
        print("NEXT: %s" % ("第二步全過 → 表格接 FinLexicon 標準列" if s["ok"] == s["staged"] else "看第二步頁:文字覆蓋 <99.5% 的點開看漏的片段;表格 ✗ 看驗證欄;交互驗證頁的 ✗ 貼 AI"))
        return 0
    if args[:1] == ["engines"]:
        o = engines_audit(register="--register" in args)
        s = o["summary"]
        print("[計] VRN 引擎稽核 · 族 %d(py %d · ps1 %d)· 無版號 %d · 未註冊 %d · py 無加速器 %d · ps1 無加速器 %d · 註冊冊 %s" % (s["families"], s["py"], s["ps1"], s["no_version"], s["not_registered"], s["no_accel_py"], s["no_accel_ps"], s["register"] or "未寫(加 --register)"))
        for r in [r for r in o["rows"] if r["pipeline"]]:
            print("  [%s] 管線 %s · %s · 版號%s 註冊%s 加速器%s" % ("OK" if r["lamp"] == "GREEN" else "YEL", r["family"], r["pipeline"], "✓" if r["version"] else "✗", "✓" if r["registered"] else "✗", "✓" if r["accel"] else "✗"))
        for r in [r for r in o["rows"] if r["lamp"] != "GREEN" and not r["pipeline"]][:20]:
            print("  [YEL] %s%s · 版號%s 註冊%s 加速器%s" % (r["family"], r["ext"], "✓" if r["version"] else "✗", "✓" if r["registered"] else "✗", "✓" if r["accel"] else "✗"))
        print("  [U/I] %s" % o["html"])
        return 0
    return PRIOR.main(args)


def _mk_pdf_v157(path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    cjk = "MSung-Light"
    for fp in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", r"C:\Windows\Fonts\msjh.ttc", r"C:\Windows\Fonts\mingliu.ttc"):
        if Path(fp).exists():
            try:
                from reportlab.pdfbase.ttfonts import TTFont
                pdfmetrics.registerFont(TTFont("CJKT7", fp, subfontIndex=0))
                cjk = "CJKT7"
                break
            except Exception:  # noqa: BLE001
                continue
    if cjk == "MSung-Light":
        pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
    W, H = A4
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica", 7)
    c.drawString(40, H - 28, "KGI Research | Taiwan Equity | 2026/09/17")
    c.setFont(cjk, 20)
    c.drawString(40, H - 80, "健策 3653:液冷題材發酵 營運動能強勁")
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, H - 120, "Investment highlights")
    c.setFont("Helvetica", 9.5)
    para = ("Jentech (3653 TT) benefits from liquid cooling adoption across AI servers and we expect revenue to grow strongly in 2026. "
            "Margins should expand as the product mix shifts toward vapor chambers. We reiterate our positive view on the stock.")
    words, line, y = para.split(), "", H - 140
    for w in words:
        if len(line) + len(w) > 70:
            c.drawString(40, y, line)
            y -= 13
            line = w
        else:
            line = (line + " " + w).strip()
    c.drawString(40, y, line)
    y -= 26
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, y, "Risks")
    c.setFont("Helvetica", 9.5)
    for i in range(3):
        y -= 14
        c.drawString(40, y, "- Customer concentration risk number %d could weigh on margins." % (i + 1))
    c.setFont("Helvetica", 8)
    yy = H - 120
    for t in ("Rating: Buy", "Target price: NT$1,200", "Close (2026/09/16): NT$980", "Bloomberg: 3653 TT", "", "Amy Wang", "Senior Analyst", "+886-2-2181-8888", "amy.wang@kgi.com"):
        if t:
            c.drawString(420, yy, t)
        yy -= 12
    c.setFont("Helvetica", 6)
    c.drawString(40, 30, "KGI Securities Investment Advisory Co., Ltd. | Disclaimer: for information only.")
    c.showPage()
    c.setFont("Helvetica", 10)
    for i in range(25):
        c.drawString(40, H - 60 - i * 14, "Industry discussion paragraph %d without financial numbers." % i)
    c.setFont("Helvetica", 6)
    c.drawString(40, 30, "KGI Securities Investment Advisory Co., Ltd.")
    c.showPage()
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, H - 70, "Financial summary (NT$m)")
    rows = [["Income statement", "2023A", "2024A", "2025F", "2026F"], ["Revenue", "12,345", "15,678", "19,012", "23,456"], ["Gross profit", "4,321", "5,678", "7,012", "8,765"], ["Net income", "1,876", "2,654", "3,456", "4,321"], ["EPS (NT$)", "15.2", "21.5", "28.0", "35.1"]]
    t = Table(rows, colWidths=[90, 50, 50, 50, 50])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("FONT", (0, 0), (-1, -1), "Helvetica", 7.5)]))
    t.wrapOn(c, W, H)
    t.drawOn(c, 40, H - 200)
    rows2 = [["Balance sheet", "2023A", "2024A", "2025F", "2026F"], ["Cash", "3,210", "4,321", "5,432", "6,543"], ["Total assets", "20,000", "24,000", "29,000", "35,000"]]
    t2 = Table(rows2, colWidths=[80, 42, 42, 42, 42])
    t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("FONT", (0, 0), (-1, -1), "Helvetica", 7.5)]))
    t2.wrapOn(c, W, H)
    t2.drawOn(c, 340, H - 200)
    c.setFont("Helvetica", 6)
    c.drawString(40, 30, "KGI Securities Investment Advisory Co., Ltd.")
    c.showPage()
    c.save()


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

    td = Path(tempfile.mkdtemp(prefix="vrnl2-"))
    home = td / "functional modules" / "VRN"
    for x in ("SSOT", "knowledge", "registry", "intake/VRN_ReportClassifier"):
        (home / x).mkdir(parents=True, exist_ok=True)
    rep = td / "VIA_Reports" / "vrn"
    base = td / "VIA"
    vdb = base / "via_database" / "vdf_database"
    vdb.mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_VDF_HOME", "VIA_ROOTS_BASE", "VIA_SPILL_DIR", "VIA_VRN_MASTER_LISTS", "USERPROFILE")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(rep), "VIA_VDF_HOME": str(td / "nope"), "VIA_ROOTS_BASE": str(base), "VIA_SPILL_DIR": str(td / "TEMP"), "USERPROFILE": str(td)})
    with (vdb / "vdf_tw_all_stocks.csv").open("w", encoding="utf-8") as fh:
        fh.write("stock_id,name,market\n3653,健策,上市\n")
        for i in range(1100, 1950):
            fh.write("%d,測%d,上市\n" % (i, i))
    with (vdb / "vdf_daily_prices.csv").open("w", encoding="utf-8") as fh:
        fh.write("ticker,date,close,adj_close\n")
        for d, cl, adj in (("2026-09-15", 975, 965.25), ("2026-09-16", 980, 970.2), ("2026-09-17", 990, 980.1), ("2026-10-08", 1010, 1010)):
            fh.write("3653.TW,%s,%s,%s\n" % (d, cl, adj))
    (home / "knowledge" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": {"凱基": {"abbr": "KGI", "aliases": ["凱基", "凱基投顧", "KGI", "KGI Securities"]}}}, ensure_ascii=False), encoding="utf-8")
    (home / "VRN_ENG394_LayoutRestore_v0102.py").write_text("def _subcat(size: float, bold: bool, body: float, nchar: int, text: str):\n    return 'HEAD' if (size > body + 1 or bold) and nchar < 80 else 'BODY'\n", encoding="utf-8")
    upl = sorted(Path("/mnt/user-data/uploads").glob("*VRN_ReportClassifier_v0100.py")) if Path("/mnt/user-data/uploads").is_dir() else []
    cls_src = upl[0] if upl else next(iter(sorted(HERE.rglob("VRN_ReportClassifier_v0100.py"))), None)
    if cls_src:
        shutil.copy(cls_src, home / "intake" / "VRN_ReportClassifier" / "VRN_ReportClassifier_v0100.py")
    inp = td / "inbox"
    inp.mkdir()
    rpt = inp / "凱基投顧_3653 健策_向子慧_20260917.pdf"
    _mk_pdf_v157(rpt)
    e = eng394_bind()
    chk("① ENG394 _subcat 依參數名綁定(size, bold, body, nchar, text)→ 已接", e.get("ok") and "nchar" in e.get("sig", ""))
    b = {"rows": [["Item", "2024A", "2025F"], ["Revenue", "1,234 1,456", ""], ["EPS", "12.1", "13.5"]], "fixes": [], "x0": 0, "top": 0, "x1": 1, "bottom": 1, "sub": "財務表·損益"}
    rr = repair_table(b)
    v = verify_table(dict(b, rows=rr["rows"]))
    chk("② 表格修復:合併數字格「1,234 1,456」拆成兩欄 → 驗證過(表頭 · 列長齊 · 可解析 100%)", rr["rows"][1][:3] == ["Revenue", "1,234", "1,456"] and v["ok"] and v["parse_rate"] == 1.0)
    txt, joins, sus = rejoin([{"text": "Margins should ex-", "x0": 0, "x1": 300}, {"text": "pand strongly in", "x0": 0, "x1": 280}, {"text": "2026.", "x0": 0, "x1": 40}, {"text": "液冷題材發酵", "x0": 0, "x1": 300}, {"text": "營運動能強勁。", "x0": 0, "x1": 200}])
    chk("③ 連接斷句:英文斷字接回 · 中文接中文不加空白 · 句號後換句", txt == "Margins should expand strongly in 2026. 液冷題材發酵營運動能強勁。" and joins == 3)
    o = layout_run_v157(inp, {"workers": 1, "tabula": False, "max": 0, "only": ""})
    r = o["rows"][0]
    chk("④ 第一步:分類器已接(四類)· 只取 P1 + 年度財報頁 P3(P2 不碰)", o["summary"]["classifier"].endswith("VRN_ReportClassifier_v0100.py") and o["cls"][str(rpt)]["status"] in ("ACCEPTED", "REVIEW") and r["picked"] == [1, 3])
    chk("⑤ 第二步文字還原:每頁位置覆蓋 ≥ 99.5%%(實 %s)· 分類完成 100%% · 單位有句 / 標題 / 資料 / 條列 / 表列" % r["cov_pages"], r["text_ok"] and r["classified"] == 100.0 and all(k in r["units"] for k in ("句", "標題", "資料", "條列", "表列")))
    chk("⑥ 第二步表格還原:年度頁表全驗證過 · 單位 NT$m 抓到 · 第二步成功", r["table_ok"] and r["tables"] >= 2 and r["step2_ok"])
    a = (r["info"]["analysts"] or [{}])[0]
    chk("⑦ 資訊區:電郵 amy.wang@kgi.com → 英文名 Amy Wang · 網域 → KGI · 分析師在電郵/職稱/電話上方 · 職稱 Senior Analyst · 台灣電話 · 評等 Buy · TP 1200 · 收盤 980 · 首頁日期",
        a.get("name") == "Amy Wang" and a.get("name_from_email") == "Amy Wang" and a.get("name_check") == "✓" and a.get("domain_broker") == "KGI" and a.get("title") == "Senior Analyst" and "2181" in (a.get("tel") or "") and r["info"]["rating"] == "Buy" and r["info"]["tp"] == 1200 and r["info"]["close"] == 980 and r["info"]["date_p1"] == "2026-09-17")
    x = o["xc"][str(rpt)]
    chk("⑧ 資料庫對照:報告日前最後交易日 2026-09-16 收 980 / adj 970.2 · 最新 adj 1010(10-08)· TP(adj)= 1200×970.2/980 = 1188.0 · 收盤 ✓", x["date_before"] == "2026-09-16" and x["adj_before"] == 970.2 and x["adj_latest"] == 1010 and x["tp_adj"] == round(1200 * 970.2 / 980, 2) and x["close_ok"] is True and x["in_master"])
    full = json.loads(Path(r["temp_json"]).read_text(encoding="utf-8"))
    chk("⑨ 識別結果全存 TEMP(含頁尾段 · 單位 · 表驗證)· 三頁 第一步 / 第二步 / 交互驗證 · 每檔頁有還原面板", str(td / "TEMP") in r["temp_json"] and any(b["role"] == "FOOTER" for pg in full["pages"] for b in pg["blocks"]) and all(Path(o["pages"][k]).exists() for k in ("step1", "step2", "xcheck")) and "LAYOUT NON-OCR" in Path(r["html"]).read_text(encoding="utf-8") and r["footer_broker"] == "KGI")
    os.environ["VRN_SPAWN_TEST"] = "1"
    rpt2 = inp / "凱基投顧_3653 健策_copy_20260917.pdf"
    shutil.copy(rpt, rpt2)
    o2 = layout_run_v157(inp, {"workers": 2, "tabula": False, "max": 0, "only": ""})
    chk("⑩ 多程序(spawn,跟 Windows 一樣)跑 2 檔 · 結果與單程序一致", o2["summary"]["mode"].startswith("多程序") and len(o2["rows"]) == 2 and all(x.get("step2_ok") for x in o2["rows"]))
    ea = engines_audit(register=True)
    pipe = {x["family"]: x for x in ea["rows"] if x["pipeline"]}
    chk("⑪ 引擎稽核:版本 · 註冊(寫 VRN_Engine_Register_v0100)· 加速器 · 管線三引擎都在列", ea["summary"]["register"] == "VRN_Engine_Register_v0100.json" and {"VRN_ENG394_LayoutRestore", "VRN_ReportClassifier"} <= set(pipe) and Path(ea["html"]).exists())
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑫ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    chk("⑬ 帶加速器橋", "[VIA:ACCEL-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8"))
    for k, val in saved.items():
        if val is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = val
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0157 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
