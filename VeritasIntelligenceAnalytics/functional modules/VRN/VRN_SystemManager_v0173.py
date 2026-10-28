#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0173 — 薄尾(操作員 2026-10-11「NON-OCR FIXING VALIDATING · OCR FIXING VALIDATING · REPORT DATE / FILENAME / TICKER / YFINANCE TICKER /
   BLOOMBERG TICKER / NAME / BROKER / ANALYST / TEL / EMAIL / TITLE / RATING / TARGET PRICE(ORIGINAL) / TARGET PRICE(ADJ) / ADJ CLOSE BEFORE REPORT DATE / UPSIDE POTENTIAL%」)。
  basicinfo 動詞(讀上一輪 layout 的逐檔結果 + 名冊 + 價格庫;每份報告一筆 · 16 欄 · 每欄 值 / 燈 / 來源 / 驗證)
  第一關 NON-OCR 修復驗證:報告日 檔名↔首頁 · 代號 碼型↔名冊↔首頁 · 名稱 名冊(全名 → 簡稱)· 券商 檔名↔頁尾↔電郵網域 · 分析師 / 電話 / EMAIL / 職稱 ·
         評等(+ 檔名評等槽 · 主字典 0~5 碼)· 目標價 合理範圍(資料庫收盤 0.3~5 倍)· TP(adj) = TP × 報告日前 adj / close · 報告日前 adj close(價格庫過期 → 灰 · 不硬算)
  第二關 OCR 修復驗證(第一關缺 評等 / 目標價 / 首頁日期 / 分析師 才做):第一頁資訊區 → OCR → 只補缺的欄位 → 同樣交叉驗證(過 = 綠 · 沒法驗 = 黃候選)
  上漲空間 = TP(adj) ÷ 報告日前 adj close − 1;另附 依最新 adj close(操作員 09-24「上漲空間都要用最新的 ADJ CLOSE」)
  輸出 VIA_Reports\\vrn\\basicinfo\\BASIC_INFO_latest.json / .jsonl / .csv / .parquet + BASIC_INFO_latest.html(每欄一顆燈)
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

import csv
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
TAG = "v0173"


def _vnum_v0173(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0173(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0173(p) < _vnum_v0173(__file__)), key=_vnum_v0173)
PRIOR = _load_v0173(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
FIELDS = ["REPORT_DATE", "FILENAME", "TICKER", "YF_TICKER", "BBG_TICKER", "NAME", "BROKER", "ANALYST", "TEL", "EMAIL", "TITLE", "RATING", "TP_ORIGINAL", "TP_ADJ", "ADJ_CLOSE_BEFORE", "UPSIDE_PCT"]
ZH = {"REPORT_DATE": "報告日", "FILENAME": "檔名", "TICKER": "代號", "YF_TICKER": "yfinance", "BBG_TICKER": "Bloomberg", "NAME": "名稱", "BROKER": "券商", "ANALYST": "分析師", "TEL": "電話",
      "EMAIL": "EMAIL", "TITLE": "職稱", "RATING": "評等", "TP_ORIGINAL": "目標價(原)", "TP_ADJ": "目標價(adj)", "ADJ_CLOSE_BEFORE": "報告日前 adj close", "UPSIDE_PCT": "上漲空間%"}
_RANK = {"RED": 3, "YELLOW": 2, "GRAY": 1, "GREEN": 0}


def F(value, status, source, check=""):
    return {"value": value, "status": status, "source": source, "check": check}


def _iso(s: str) -> str:
    """各種日期寫法 → YYYY-MM-DD(8 碼 · 民國 7 碼 · 6 碼 · YYYY/MM/DD · 英文月份)。"""
    s = str(s or "").strip()
    m = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", s)
    if m:
        y, mo, d = map(int, m.groups())
    else:
        m = re.search(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)", s) or re.search(r"(?<!\d)(1[01]\d)(\d{2})(\d{2})(?!\d)", s)
        if m:
            y, mo, d = map(int, m.groups())
            y = y + 1911 if y < 1000 else y
        else:
            m = re.search(r"(?i)(?:(\d{1,2})\s+)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(?:(\d{1,2}),?\s+)?(20\d{2})", s)
            if not m:
                return ""
            mon = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].index(m.group(2).lower()[:3]) + 1
            y, mo, d = int(m.group(4)), mon, int(m.group(1) or m.group(3) or 0)
    try:
        return datetime.date(y, mo, d).isoformat()
    except ValueError:
        return ""


def _market_suffix(code: str, ent: dict, row: dict) -> tuple:
    mk = str((ent or {}).get("market") or "")
    if re.search(r"TWO|上櫃|櫃|OTC|TPEx|TPEX", mk, re.I):
        return ".TWO", True
    if re.search(r"TW|上市|TWSE|TSE", mk, re.I):
        return ".TW", True
    yf = str(row.get("yf") or "")
    if yf.upper().endswith(".TWO"):
        return ".TWO", True
    if yf.upper().endswith(".TW"):
        return ".TW", True
    return ".TW", False


def _short_name(n: str) -> str:
    nv = _resolve("name_variants")
    if not n or not nv or "公司" not in n:
        return n or ""
    vs = sorted((v for v in nv(n) if len(v) >= 2 and "-KY" not in v), key=len)
    return vs[0] if vs else n


_MEMO = re.compile(r"(?i)memo|訪談速報|,\s*note\)|\(\d{4},\s*note|_note|晨會|\.docx?$|\.txt$|\.md$")


def _rating_code(raw: str, canon: str):
    md = _resolve("_MASTER") or {}
    for key in (raw, canon):
        k = str(key or "").strip().lower()
        if not k:
            continue
        for name, e in (md.get("RATING_LIST") or {}).items():
            if any(k == str(a).lower() for a in e.get("aliases", [])):
                return e.get("code"), name
    return None, ""


def _fname_rating(fn: str) -> str:
    m = re.search(r"\(\d{4},\s*([A-Za-z]{1,3})_([^)]+)\)", fn)
    return m.group(2) if m else ""


def fields_native(row: dict, info: dict, summ: dict, x: dict, master: dict, book: dict) -> dict:
    to_code = _resolve("to_code") or (lambda c, b: c)
    fn, code = row.get("file", ""), row.get("code", "")
    ent = master.get(code) or {}
    memo = bool(_MEMO.search(fn))
    out = {}
    d_fn, d_p1 = _iso(row.get("date")), _iso(info.get("date_p1"))
    if d_fn and d_p1:
        out["REPORT_DATE"] = F(d_fn, "GREEN" if d_fn == d_p1 else "RED", "檔名 + 首頁", "一致" if d_fn == d_p1 else "檔名 %s ≠ 首頁 %s" % (d_fn, d_p1))
    else:
        out["REPORT_DATE"] = F(d_fn or d_p1, "YELLOW" if (d_fn or d_p1) else "RED", "檔名" if d_fn else ("首頁" if d_p1 else "—"), "只有%s" % ("檔名" if d_fn else "首頁") if (d_fn or d_p1) else "沒找到")
    out["FILENAME"] = F(fn, "GREEN", "檔名")
    conf = (summ.get("confirm") or {})
    ok_code = bool(re.fullmatch(r"[1-9]\d{3}|00\d{3,4}[A-Z]?", code or ""))
    out["TICKER"] = F(code, "GREEN" if ok_code and ent else ("YELLOW" if ok_code else "RED"), "檔名 + 名冊", ("名冊有" if ent else "名冊沒有") + (" · 首頁有" if conf.get("代號") else ""))
    suf, known = _market_suffix(code, ent, row)
    out["YF_TICKER"] = F(code + suf if code else "", "GREEN" if known and ok_code else "YELLOW", "名冊市場別" if known else "預設 .TW", "上櫃 .TWO / 上市 .TW")
    out["BBG_TICKER"] = F(code + " TT" if code else "", out["TICKER"]["status"], "代號", "Bloomberg 台股 = 代號 + TT")
    nm = row.get("name") or ent.get("name", "")
    out["NAME"] = F(_short_name(nm), "GREEN" if x.get("name_ok") else "YELLOW", "名冊" if ent else "檔名", "全名 %s" % nm if _short_name(nm) != nm else ("名冊一致" if x.get("name_ok") else "名冊沒對到"))
    bk = row.get("broker", "")
    foot = to_code(summ.get("footer_broker") or "", book) if summ.get("footer_broker") else ""
    doms = sorted({to_code((a.get("domain_broker") or ""), book) for a in info.get("analysts", []) if isinstance(a, dict) and a.get("domain_broker")} - {""})
    conflict = (foot and bk and foot != bk) or (doms and bk and bk not in doms)
    agree = (foot and foot == bk) or (bk in doms)
    out["BROKER"] = F(bk or foot or (doms[0] if doms else ""), "RED" if conflict else ("GREEN" if agree else ("YELLOW" if bk else "RED")), "檔名" + (" + 頁尾" if foot else "") + (" + 電郵網域" if doms else ""),
                      "頁尾 %s · 網域 %s" % (foot or "—", ",".join(doms) or "—"))
    an = [a for a in info.get("analysts", []) if isinstance(a, dict)]
    names = [a.get("name") or a.get("name_from_email") or "" for a in an]
    names = [n for n in names if n]
    out["ANALYST"] = F("; ".join(names), "GREEN" if any(a.get("name_check") == "✓" for a in an) or (names and any(a.get("email") for a in an)) else ("YELLOW" if names else ("GRAY" if memo else "YELLOW")),
                       "首頁資訊區", "姓名對 EMAIL" if any(a.get("name_check") == "✓" for a in an) else ("無 EMAIL 可對" if names else "沒找到"))
    tel_rx = [r for r in (_resolve("TEL_TW_RX"), _resolve("TEL_HK_RX")) if r is not None]
    tels = [a.get("tel") for a in an if a.get("tel")] or list(info.get("tel_tw") or []) + list(info.get("tel_hk") or [])
    out["TEL"] = F("; ".join(dict.fromkeys(tels)), "GREEN" if tels and all(any(rx.search(t) for rx in tel_rx) for t in tels) else ("YELLOW" if tels else "GRAY" if memo else "YELLOW"), "首頁資訊區", "台 / 港電話格式" if tels else "沒找到")
    ems = [a.get("email") for a in an if a.get("email")]
    em_ok = ems and all(to_code(a.get("domain_broker") or "", book) == bk for a in an if a.get("email"))
    out["EMAIL"] = F("; ".join(ems), "GREEN" if em_ok else ("YELLOW" if ems else ("GRAY" if memo else "YELLOW")), "首頁資訊區", "網域 = 券商" if em_ok else ("網域對不上券商" if ems else "沒找到"))
    tts = [a.get("title") for a in an if a.get("title")]
    out["TITLE"] = F("; ".join(dict.fromkeys(tts)), "GREEN" if tts else ("GRAY" if memo else "YELLOW"), "首頁資訊區", "" if tts else "沒找到")
    rc, rname = _rating_code(info.get("rating_raw"), info.get("rating"))
    fr = _fname_rating(fn)
    rt = info.get("rating") or ""
    if rt:
        frc = _rating_code(fr, "")[0] if fr else None
        st = "GREEN" if (fr and frc is not None and frc == rc) or info.get("rating_src") else "YELLOW"
        if fr and frc is not None and rc is not None and frc != rc:
            st = "RED"
        out["RATING"] = F(rt, st, "首頁資訊區" + (" + 檔名" if fr else ""), "原文 %s · 主字典碼 %s%s" % (info.get("rating_raw") or rt, rc if rc is not None else "?", (" · 檔名 %s" % fr) if fr else ""))
    else:
        out["RATING"] = F("", "GRAY" if memo else "YELLOW", "—", "Memo / Note 無評等" if memo else "沒找到")
    tp, cb, ab = info.get("tp"), x.get("close_before"), x.get("adj_before")
    stale = bool(x.get("stale"))
    ref = cb or info.get("close")
    if tp:
        plaus = ref and 0.3 <= tp / ref <= 5
        if cb:                                                       # 綠 = 跟資料庫收盤交叉驗證過;只跟報告自述收盤比 = 同一份報告內部自洽 → 黃
            out["TP_ORIGINAL"] = F(tp, "GREEN" if plaus else "RED", "首頁資訊區", "資料庫收盤 %s 的 %.2f 倍%s" % (cb, tp / cb, "" if plaus else " → 不合理"))
        else:
            out["TP_ORIGINAL"] = F(tp, "YELLOW" if (not ref or plaus) else "RED", "首頁資訊區", ("只跟報告自述收盤 %s 比(%.2f 倍)· 資料庫不能比" % (ref, tp / ref)) if ref else "沒有收盤可比")
    else:
        out["TP_ORIGINAL"] = F(None, "GRAY" if memo or rc == 0 else "YELLOW", "—", "Memo / 未評等 無目標價" if (memo or rc == 0) else "沒找到(或不合理已剔除)")
    if x.get("tp_adj"):
        out["TP_ADJ"] = F(x["tp_adj"], "GREEN", "TP × adj ÷ close", "報告日前 %s:close %s · adj %s" % (x.get("date_before"), cb, ab))
    else:
        out["TP_ADJ"] = F(None, "GRAY", "—", x.get("note") or ("價格庫過期" if stale else ("無目標價" if not tp else "缺 adj close")))
    if ab and not stale:
        out["ADJ_CLOSE_BEFORE"] = F(ab, "GREEN", "價格庫(唯讀)", "報告日前最後交易日 %s" % x.get("date_before"))
    else:
        out["ADJ_CLOSE_BEFORE"] = F(ab if ab else None, "GRAY", "價格庫(唯讀)", x.get("note") or "價格表沒有")
    if out["TP_ADJ"]["value"] and ab and not stale:
        out["UPSIDE_PCT"] = F(round((out["TP_ADJ"]["value"] / ab - 1) * 100, 2), "GREEN", "TP(adj) ÷ 報告日前 adj − 1", "")
    elif tp and info.get("close"):
        out["UPSIDE_PCT"] = F(round((tp / info["close"] - 1) * 100, 2), "YELLOW", "依報告自述收盤", "價格庫不能比(過期 / 沒有)→ 用報告收盤 %s" % info["close"])
    else:
        out["UPSIDE_PCT"] = F(None, "GRAY", "—", "無目標價或收盤")
    return out


# ───────── 第二關:OCR 修復驗證(只補第一關缺的)─────────
_TP_RX = re.compile(r"(?i)(?:target\s*price|price\s*target|12m\s*tp|\btp\b|\bpt\b|目標價|目標股價|合理價)\s*[:：]?\s*(?:\(?[A-Z]{0,3}\$?\)?\s*)?(?:NT\$|TWD|NTD|\$)?\s*([\d,]+(?:\.\d+)?)")
_CLOSE_RX = re.compile(r"(?i)(?:closing\s*price|close|share\s*price|price\s*\(|收盤價|股價)\s*[^\d\n]{0,18}?([\d,]+(?:\.\d+)?)")
_EMAIL_RX = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")


def _rating_from_text(t: str) -> str:
    md = _resolve("_MASTER") or {}
    best = (None, "")
    for name, e in (md.get("RATING_LIST") or {}).items():
        for a in e.get("aliases", []):
            if len(a) < 3 and not re.search(r"[\u4e00-\u9fff]", a):
                continue
            m = re.search(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", t, re.I)
            if m and (best[0] is None or m.start() < best[0]):
                best = (m.start(), a)
    return best[1]


def ocr_fill(fields: dict, row: dict, j: dict, x: dict, book: dict, th, dpi: int = 200) -> dict:
    need = [k for k in ("REPORT_DATE", "RATING", "TP_ORIGINAL", "ANALYST", "EMAIL") if fields[k]["status"] in ("YELLOW", "RED") and not fields[k]["value"]]
    if fields["REPORT_DATE"]["status"] == "YELLOW" and fields["REPORT_DATE"]["source"] == "檔名":
        need.append("REPORT_DATE_P1")
    if not need or th is None or not row.get("mini") or not Path(row["mini"]).exists():
        return {"used": False, "need": need}
    import fitz  # noqa: WPS433
    from PIL import Image  # noqa: WPS433
    pg = (j.get("pages") or [{}])[0]
    roles = pg.get("roles") or {}
    info_b = [b for b in pg.get("blocks", []) if (b.get("role") or roles.get(b.get("zone"))) == "INFO" and all(k in b for k in ("x0", "top", "x1", "bottom"))]
    with fitz.open(row["mini"]) as d:
        p = d[0]
        if info_b:
            clip = fitz.Rect(max(0, min(b["x0"] for b in info_b) - 6), max(0, min(b["top"] for b in info_b) - 6), min(p.rect.width, max(b["x1"] for b in info_b) + 6), min(p.rect.height, max(b["bottom"] for b in info_b) + 6))
        else:
            clip = fitz.Rect(0, 0, p.rect.width, p.rect.height * 0.45)
        pix = p.get_pixmap(clip=clip, dpi=dpi, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    t0 = time.time()
    o = th.ocr_image(img, "rapidocr")
    if o.get("status") != "ok":
        return {"used": True, "need": need, "status": o.get("status"), "why": o.get("why", "")}
    txt = " ".join(l["text"] for l in o["lines"])
    got = {}
    if "RATING" in need:
        r = _rating_from_text(txt)
        if r:
            code = _rating_code(r, "")[0]
            fields["RATING"] = F(r, "YELLOW", "OCR(候選)", "OCR 讀到 · 主字典碼 %s" % code)
            got["RATING"] = r
    if "TP_ORIGINAL" in need:
        m = _TP_RX.search(txt)
        if m:
            tp = float(m.group(1).replace(",", ""))
            ref = x.get("close_before")
            ok = bool(ref) and 0.3 <= tp / ref <= 5
            fields["TP_ORIGINAL"] = F(tp, "GREEN" if ok else "YELLOW", "OCR" + ("(資料庫收盤驗過)" if ok else "(候選)"), ("資料庫收盤 %s 的 %.2f 倍" % (ref, tp / ref)) if ref else "沒有收盤可驗")
            got["TP_ORIGINAL"] = tp
    if "REPORT_DATE" in need or "REPORT_DATE_P1" in need:
        dd = ""
        for m in re.finditer(r"(?:20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2})|(?:(?:\d{1,2}\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(?:\d{1,2},?\s+)?20\d{2})", txt, re.I):
            dd = _iso(m.group(0))
            if dd:
                break
        if dd:
            fn_d = _iso(row.get("date"))
            fields["REPORT_DATE"] = F(fn_d or dd, "GREEN" if fn_d and fn_d == dd else ("RED" if fn_d else "YELLOW"), ("檔名 + " if fn_d else "") + "OCR 首頁", "一致" if fn_d == dd else ("檔名 %s ≠ OCR %s" % (fn_d, dd) if fn_d else "只有 OCR"))
            got["REPORT_DATE"] = dd
    if "EMAIL" in need or "ANALYST" in need:
        ems = sorted(set(_EMAIL_RX.findall(txt)))
        if ems:
            dom_ok = all((_resolve("domain_broker") or (lambda a, b: ""))(e.split("@")[1], book) == row.get("broker") for e in ems)
            fields["EMAIL"] = F("; ".join(ems), "GREEN" if dom_ok else "YELLOW", "OCR" + ("(網域 = 券商)" if dom_ok else "(候選)"), "")
            if "ANALYST" in need:
                nf = _resolve("email_name") or (lambda s: s)
                fields["ANALYST"] = F("; ".join(nf(e.split("@")[0]) for e in ems), "YELLOW", "OCR(由 EMAIL 推)", "候選")
            got["EMAIL"] = ems
    return {"used": True, "need": need, "got": got, "conf": o.get("conf"), "lines": o.get("n"), "ms": int((time.time() - t0) * 1000)}


def basicinfo_run(ocr: bool = True, budget: int = 180, px=None, master=None) -> dict:
    d = _resolve("_latest_l2_dir")("")
    if not d:
        return {"err": "找不到上一輪 layout 的逐檔結果(先跑 -Verb layout)"}
    docs = []
    for p in sorted(d.glob("*.json")):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if j.get("row") and j["row"].get("code"):
            docs.append(j)
    docs.sort(key=lambda j: j["row"].get("file", ""))
    if master is None:
        try:
            master = (_resolve("_load_roster_v154") or (lambda u: ({}, [])))(True)[0]
        except Exception:  # noqa: BLE001
            master = {}
    if px is None:
        try:
            px = (_resolve("prices_for") or (lambda c: {}))({j["row"]["code"] for j in docs})
        except Exception:  # noqa: BLE001
            px = {}
    book = (_resolve("load_brokers_v154") or (lambda: ({}, [])))()[0]
    dbc = _resolve("db_check")
    th = (_resolve("toolhub") or (lambda: None))() if ocr else None
    recs, t_ocr, S = [], 0.0, Counter()
    for nn, j in enumerate(docs, 1):
        row, info, summ = j["row"], j.get("info") or {}, j.get("summary") or {}
        try:
            x = dbc(dict(row, path=row.get("path", "")), info, px, master) or {}
        except Exception as exc:  # noqa: BLE001
            x = {"note": "資料庫對照失敗 %s" % type(exc).__name__}
        flds = fields_native(row, info, summ, x, master, book)
        stage = "NON-OCR"
        oc = {"used": False}
        if ocr and t_ocr < budget:
            t0 = time.time()
            try:
                oc = ocr_fill(flds, row, j, x, book, th)
            except Exception as exc:  # noqa: BLE001
                oc = {"used": True, "status": "error", "why": "%s: %s" % (type(exc).__name__, str(exc)[:80])}
            if oc.get("used"):
                t_ocr += time.time() - t0
                stage = "NON-OCR + OCR"
                S["ocr_docs"] += 1
                S["ocr_got"] += len(oc.get("got") or {})
        if flds["TP_ADJ"]["value"] is None and flds["TP_ORIGINAL"]["value"] and x.get("adj_before") and x.get("close_before") and not x.get("stale"):     # OCR 補到 TP → 補算 TP(adj) / 上漲空間
            tpa = round(flds["TP_ORIGINAL"]["value"] * x["adj_before"] / x["close_before"], 2)
            flds["TP_ADJ"] = F(tpa, flds["TP_ORIGINAL"]["status"], "TP × adj ÷ close", "TP 來自 %s" % flds["TP_ORIGINAL"]["source"])
            flds["UPSIDE_PCT"] = F(round((tpa / x["adj_before"] - 1) * 100, 2), flds["TP_ORIGINAL"]["status"], "TP(adj) ÷ 報告日前 adj − 1", "")
        lamp = max((f["status"] for f in flds.values()), key=lambda s: _RANK[s])
        for k, f in flds.items():
            S["%s_%s" % (k, f["status"])] += 1
        up_latest = round((flds["TP_ADJ"]["value"] / x["adj_latest"] - 1) * 100, 2) if flds["TP_ADJ"]["value"] and x.get("adj_latest") else None
        rc = _rating_code(info.get("rating_raw"), info.get("rating"))
        recs.append({"report_id": "%02d_%s" % (nn, row.get("code")), "lamp": lamp, "stage": stage, "fields": flds,
                     "analysts": [{k: a.get(k) for k in ("name", "name_from_email", "title", "tel", "email", "domain_broker", "name_check")} for a in info.get("analysts", []) if isinstance(a, dict)],
                     "extra": {"name_full": row.get("name"), "rating_raw": info.get("rating_raw"), "rating_code": rc[0], "rating_class": rc[1], "close_report": info.get("close"), "close_before": x.get("close_before"),
                               "date_before": x.get("date_before"), "adj_latest": x.get("adj_latest"), "date_latest": x.get("date_latest"), "upside_latest_pct": up_latest,
                               "upside_latest_rule": "操作員 09-24「上漲空間都要用最新的 ADJ CLOSE」", "price_stale": bool(x.get("stale")), "db_note": x.get("note", "")},
                     "ocr": oc})
        print("  [進度] %d/%d · 還原 · %s · %s" % (nn, len(docs), lamp, row.get("file", "")[:44]), flush=True)
    out = _rep() / "basicinfo"
    out.mkdir(parents=True, exist_ok=True)
    (out / "BASIC_INFO_latest.json").write_text(json.dumps({"schema": "VIA.VRN.BasicInfo.v1", "generated": datetime.datetime.now().isoformat(timespec="seconds"), "layout_run": d.parent.name,
                                                             "fields": FIELDS, "rule": "NON-OCR 修復驗證 → 缺才 OCR 修復驗證;每欄 值 / 燈 / 來源 / 驗證;OCR 沒法交叉驗證 = 黃(候選)", "records": recs},
                                                            ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with (out / "BASIC_INFO_latest.jsonl").open("w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    cols = ["report_id", "lamp", "stage"] + FIELDS + ["UPSIDE_LATEST_PCT", "RATING_CODE"]
    p = out / "BASIC_INFO_latest.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in recs:
            w.writerow([r["report_id"], r["lamp"], r["stage"]] + [r["fields"][k]["value"] if r["fields"][k]["value"] is not None else "" for k in FIELDS] + [r["extra"]["upside_latest_pct"] or "", r["extra"]["rating_code"] if r["extra"]["rating_code"] is not None else ""])
    try:
        import duckdb  # noqa: WPS433
        duckdb.connect().execute("copy (select * from read_csv_auto('%s', header=true, all_varchar=true)) to '%s' (format parquet)" % (str(p).replace("'", "''"), str(p.with_suffix(".parquet")).replace("'", "''")))
    except Exception:  # noqa: BLE001
        pass
    page, L = _resolve("_page"), (_resolve("_L") or {})
    if page:
        cell = lambda f: "<span title='%s · %s'><i class='lp %s' style='background:%s;display:inline-block;width:8px;height:8px;border-radius:50%%;margin-right:3px'></i>%s</span>" % (  # noqa: E731
            html.escape(f["source"]), html.escape(f["check"]), f["status"], L.get(f["status"], "#9ca3af"), html.escape("" if f["value"] is None else str(f["value"]))[:60])
        rows = [(r["lamp"], [r["report_id"], r["stage"]] + [cell(r["fields"][k]) for k in FIELDS]) for r in recs]
        (out / "BASIC_INFO_latest.html").write_text(page("BASIC INFO · 16 欄 · NON-OCR 修復驗證 → 缺才 OCR 修復驗證(每欄一顆燈 · 滑鼠停在值上看來源 / 驗證)",
                                                         "讀 %s · 報告 %d · 動用 OCR %d 份(補到 %d 欄)· 綠 = 交叉驗證過 · 黃 = 單一來源 / OCR 候選 · 紅 = 互相矛盾 · 灰 = 不適用 / 價格庫過期" % (
                                                             html.escape(d.parent.name), len(recs), S["ocr_docs"], S["ocr_got"]), ["報告", "階段"] + [ZH[k] for k in FIELDS], rows), encoding="utf-8")
    return {"dir": str(out), "layout_run": d.parent.name, "docs": len(recs), "S": dict(S), "lamps": dict(Counter(r["lamp"] for r in recs)), "ocr_secs": int(t_ocr),
            "html": str(out / "BASIC_INFO_latest.html"), "records": recs}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["basicinfo"]:
        inst = _resolve("install_v166")
        if inst:
            inst()
        opt = lambda k, dv="": args[args.index(k) + 1] if k in args and args.index(k) + 1 < len(args) else dv  # noqa: E731
        o = basicinfo_run("--no-ocr" not in args, int(opt("--ocr-budget", "180") or 180))
        if o.get("err"):
            print("[計] BASIC INFO · %s · RED" % o["err"])
            return 1
        S = o["S"]
        print("[計] BASIC INFO · 讀上一輪 layout(%s)· 報告 %d · 整列燈 %s · 動用 OCR %d 份(補到 %d 欄 · %d 秒)" % (
            o["layout_run"], o["docs"], " · ".join("%s %d" % kv for kv in sorted(o["lamps"].items(), key=lambda kv: -_RANK[kv[0]])), S.get("ocr_docs", 0), S.get("ocr_got", 0), o["ocr_secs"]))
        for k in FIELDS:
            print("[計] %s · 綠 %d · 黃 %d · 紅 %d · 灰 %d" % (ZH[k], S.get(k + "_GREEN", 0), S.get(k + "_YELLOW", 0), S.get(k + "_RED", 0), S.get(k + "_GRAY", 0)))
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
    td = Path(tempfile.mkdtemp(prefix="vrn173-"))
    saved = {k: os.environ.get(k) for k in ("VIA_SPILL_DIR", "VIA_VRN_HEALTH_OUT")}
    try:
        from reportlab.pdfgen import canvas
        import fitz
        stage = td / "VIA_progress" / "ps_x" / "spill" / "vrn_stage_r1"
        (stage / "layout_l2").mkdir(parents=True)
        src = td / "src.pdf"
        c = canvas.Canvas(str(src), pagesize=(595, 842))
        c.setFont("Helvetica", 12)
        for i, t in enumerate(["21 May 2026", "Rating: Buy", "Target price: TWD 260", "kevin.lin@daiwa.com.hk"]):
            c.drawString(50, 842 - 80 - 22 * i, t)
        c.save()
        with fitz.open(str(src)) as dd:
            dd[0].get_pixmap(dpi=200, clip=fitz.Rect(40, 60, 320, 160)).save(str(td / "info.png"))
        mini = stage / "c_mini.pdf"
        c = canvas.Canvas(str(mini), pagesize=(595, 842))
        c.drawImage(str(td / "info.png"), 40, 842 - 160, width=280, height=100)
        c.showPage()
        c.save()
        an = {"name": "Sharon Shih", "name_from_email": "sharon shih", "email": "Sharon.Shih@morganstanley.com", "domain_broker": "MS", "title": "Equity Analyst", "tel": "+886 2 2730 2869", "name_check": "✓"}
        docs = [{"row": {"file": "MS-2308 20251128.pdf", "code": "2308", "name": "台達電", "broker": "MS", "date": "2025-11-28", "path": "a"},
                 "info": {"rating": "Buy", "rating_raw": "Overweight", "tp": 1288.0, "close": 932.0, "date_p1": "2025-11-28", "analysts": [an], "rating_src": "資訊區"},
                 "summary": {"footer_broker": "MS", "confirm": {"代號": True}}, "pages": []},
                {"row": {"file": "欣銓(3264,B_買進)-CTBC260918.pdf", "code": "3264", "name": "欣銓科技股份有限公司", "broker": "CTBC", "date": "2026-09-18", "path": "b"},
                 "info": {"rating": "Buy", "rating_raw": "買進", "tp": 400.0, "close": None, "date_p1": "2026-09-18", "analysts": [{"name": "李柏賢", "name_check": "中英名(無法直比)"}]},
                 "summary": {"confirm": {"代號": True}}, "pages": []},
                {"row": {"file": "Daiwa-6278 20260521.pdf", "code": "6278", "name": "台表科", "broker": "DAIWA", "date": "2026-05-21", "path": "c", "mini": str(mini)},
                 "info": {}, "summary": {}, "pages": [{"page": 1, "W": 595, "H": 842, "roles": {"L": "INFO"}, "blocks": [{"id": "P1·L·01", "kind": "text", "zone": "L", "role": "INFO", "x0": 40, "top": 60, "x1": 320, "bottom": 160}]}]}]
        for k, dj in enumerate(docs):
            (stage / "layout_l2" / ("%d.json" % k)).write_text(json.dumps(dj, ensure_ascii=False), encoding="utf-8")
        px = {"2308": [("2025-11-27", 942.0, 937.1), ("2026-08-25", 1710.0, 1710.0)], "3264": [("2026-08-25", 213.0, 213.0)], "6278": [("2026-05-20", 203.0, 197.35), ("2026-08-25", 181.5, 181.5)]}
        master = {"2308": {"name": "台達電", "market": "上市"}, "3264": {"name": "欣銓科技股份有限公司", "market": "上櫃"}, "6278": {"name": "台表科", "market": "上市"}}
        os.environ["VIA_SPILL_DIR"] = str(td / "VIA_progress" / "ps_new" / "spill")
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        o = basicinfo_run(ocr=True, budget=120, px=px, master=master)
        R = {r["fields"]["TICKER"]["value"]: r for r in o["records"]}
        a = R["2308"]["fields"]
        chk("① 完整報告 16 欄 NON-OCR 第一關就驗過(沒動 OCR)· TP(adj) 1288 × 937.1 ÷ 942 = %s · 上漲空間 %s%% · 2308.TW · 2308 TT" % (a["TP_ADJ"]["value"], a["UPSIDE_PCT"]["value"]),
            all(a[k]["status"] == "GREEN" for k in FIELDS) and a["TP_ADJ"]["value"] == 1281.3 and a["UPSIDE_PCT"]["value"] == 36.73 and a["YF_TICKER"]["value"] == "2308.TW" and a["BBG_TICKER"]["value"] == "2308 TT"
            and R["2308"]["stage"] == "NON-OCR")
        b = R["3264"]["fields"]
        chk("② 全名 → 簡稱 欣銓 · 上櫃 3264.TWO · 評等 檔名槽「買進」= 首頁 Buy(主字典碼 2)→ 綠 · 價格庫只到 8/25(報告日前缺 24 天)→ TP(adj) / adj close / 上漲空間 灰(不硬算)",
            b["NAME"]["value"] == "欣銓" and b["YF_TICKER"]["value"] == "3264.TWO" and b["RATING"]["status"] == "GREEN" and b["TP_ADJ"]["status"] == "GRAY" and b["ADJ_CLOSE_BEFORE"]["status"] == "GRAY"
            and b["UPSIDE_PCT"]["status"] == "GRAY" and R["3264"]["extra"]["price_stale"])
        cc = R["6278"]["fields"]
        if importlib.util.find_spec("rapidocr_onnxruntime"):
            chk("③ 資訊區是圖(原生讀不到)→ 第二關 OCR 才補:目標價 260(資料庫收盤 203 驗過 → 綠)· 報告日 OCR 2026-05-21 = 檔名(綠)· 評等 Buy(候選 黃)· EMAIL 網域 = DAIWA",
                R["6278"]["stage"] == "NON-OCR + OCR" and cc["TP_ORIGINAL"]["value"] == 260.0 and cc["TP_ORIGINAL"]["status"] == "GREEN" and cc["REPORT_DATE"]["status"] == "GREEN"
                and cc["RATING"]["value"] == "Buy" and cc["RATING"]["status"] == "YELLOW" and "daiwa" in (cc["EMAIL"]["value"] or ""))
            chk("④ OCR 補到目標價 → 自動補算 TP(adj) = 260 × 197.35 ÷ 203 = %s · 上漲空間 %s%%" % (cc["TP_ADJ"]["value"], cc["UPSIDE_PCT"]["value"]),
                cc["TP_ADJ"]["value"] == round(260 * 197.35 / 203, 2) and cc["UPSIDE_PCT"]["value"] == round((round(260 * 197.35 / 203, 2) / 197.35 - 1) * 100, 2))
        else:
            chk("③ 這台沒有 rapidocr → 第二關略過(不崩)· 缺的欄位維持黃", cc["RATING"]["status"] == "YELLOW")
            chk("④ (略)", True)
        out = Path(o["dir"])
        js = json.loads((out / "BASIC_INFO_latest.json").read_text(encoding="utf-8"))
        hdr = (out / "BASIC_INFO_latest.csv").read_text(encoding="utf-8-sig").splitlines()[0].split(",")
        chk("⑤ 全程 JSON(.json / .jsonl)+ CSV 欄序 = 操作員 16 欄 + 每欄 值 / 燈 / 來源 / 驗證 + 每欄一顆燈 HTML",
            js["fields"] == FIELDS and hdr[3:19] == FIELDS and all(set(r["fields"][k]) == {"value", "status", "source", "check"} for r in js["records"] for k in FIELDS) and (out / "BASIC_INFO_latest.jsonl").exists()
            and (out / "BASIC_INFO_latest.html").exists())
        chk("⑥ 依最新 adj close 的上漲空間另附(操作員 09-24 規則):2308 = 1281.3 ÷ 1710 − 1 = %s%%" % R["2308"]["extra"]["upside_latest_pct"], R["2308"]["extra"]["upside_latest_pct"] == round((1281.3 / 1710 - 1) * 100, 2))
        f_tp = fields_native({"file": "x.pdf", "code": "3653", "date": "2026-09-17"}, {"tp": 1200.0, "close": 980.0}, {}, {}, {}, {})["TP_ORIGINAL"]
        chk("⑩ 目標價只跟報告自述收盤比(資料庫不能比)→ 黃(同一份報告內部自洽 ≠ 交叉驗證)", f_tp["status"] == "YELLOW" and "資料庫不能比" in f_tp["check"])
        chk("⑦ 日期寫法全認:20250122 · 1140122(民國)· 2025/1/22 · 22 Jan 2025 · January 22, 2025 → 2025-01-22",
            {_iso(s) for s in ("20250122", "1140122", "2025/1/22", "22 Jan 2025", "January 22, 2025")} == {"2025-01-22"})
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑨ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0173 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
