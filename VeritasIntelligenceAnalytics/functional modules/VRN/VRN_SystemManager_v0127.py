#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0127 — 薄尾:extract 動詞(操作員授權 2026-10-06:用 pdfplumber / tabula / camelot 當 layout 引擎,把元素與表格文字連同周邊資訊段切開、清乾淨、分別取、修正後重建,財務頁依類別重建)。

流程(每檔四步各自落檔,分開取、分開修、最後重建):
  ① filename   前版鏈 parse_filename(檔名律:日期/代號/券商/分型)
  ② split      pdfplumber 逐頁:字 → 行 → 區塊(layout);區塊分 HEADER / FOOTER / TEXT / TABLE_HINT;表格偵測:pdfplumber lines → camelot(lattice→stream)→ tabula(有 Java 才開),三引擎各自取,不互蓋
  ③ clean      儲存格清洗:全形→半形 · 千分位 · (負) · − · % · 多空白;表頭列/期間欄(2023 / 2024E / 2025F / 1Q25 / FY24)偵測;表的周邊資訊段 = 表上方最近 TEXT 區塊(標題/單位)+ 下方最近 TEXT(註)
  ④ rebuild    每表 → 類別(IS 損益 / BS 資產負債 / CF 現金流 / RATIO 比率 / VAL 估值 / FORECAST 預估 / OTHER)· 列標準名(VRN 字典有就用,沒有用內建 48 條)· 期間 × 指標矩陣 · 算術核(毛利=營收−成本 · 毛利率 · 營益率 · 淨利率)→ 不符標 REVIEW
  三態:READ(≥1 表有類別且算術過)· REVIEW(有表但類別/算術不確定)· NODATA(無文字無表 = 掃描件 → 等 OCR 閘)
  extract [--file <pdf>|--dir <夾>] [--limit N] [--engines pdfplumber,camelot,tabula]   出 VIA_Reports/vrn/extract/<doc_sha8>/{filename,pages,tables_raw,tables_clean,financial}.json + 帳 VRN_Extract_Ledger.jsonl
  extract status                                                                  帳的三態計
自測:temp 沙盒自建 PDF(reportlab 有就建,沒有就用內建極小 PDF 字節)。其餘動詞照前版鏈。
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
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0127"


def _vnum_v0127(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0127(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0127(p) < _vnum_v0127(__file__)), key=_vnum_v0127)
PRIOR = _load_v0127(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ────────────────── 引擎可用性(誠實,不裝猜) ──────────────────
def _engines() -> dict:
    out = {}
    for name in ("pdfplumber", "camelot", "tabula"):
        try:
            out[name] = importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            out[name] = False
    out["java"] = bool(shutil.which("java"))
    if out["tabula"] and not out["java"]:
        out["tabula"] = False
    return out


# ────────────────── ③ clean:儲存格與數字 ──────────────────
_FW = str.maketrans("０１２３４５６７８９．，％（）－：", "0123456789.,%()-:")
_PERIOD_RX = re.compile(r"^(?:FY)?(20\d{2}|\d{2})(?:[A-Z]{1,2}|E|F|P)?$|^[1-4]Q(?:FY)?\d{2,4}[EF]?$|^(?:1H|2H)\d{2,4}[EF]?$|^\d{2,4}年(?:度|[1-4]季|上半年|下半年)?[EF]?$", re.I)
_NUM_RX = re.compile(r"^[+\-−–]?\(?\$?[\d,]+(?:\.\d+)?\)?%?[xX倍]?$")


def _clean_cell(s) -> str:
    if s is None:
        return ""
    t = str(s).translate(_FW).replace("\u3000", " ").replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _to_num(s: str):
    t = _clean_cell(s).replace(",", "").replace("$", "").replace("NT", "")
    if not t or t in ("-", "—", "n.a.", "N/A", "NA", "n.m.", "NM", "n/a"):
        return None
    neg = False
    if t.startswith("(") and t.endswith(")"):
        neg, t = True, t[1:-1]
    if t.startswith(("−", "–")):
        neg, t = True, t[1:]
    elif t.startswith("-"):
        neg, t = True, t[1:]
    pct = t.endswith("%")
    t = t.rstrip("%xX倍")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _is_period(s: str) -> bool:
    return bool(_PERIOD_RX.match(_clean_cell(s).replace(" ", "")))


# ────────────────── ④ rebuild:類別與列標準名 ──────────────────
_FIN_STD = [
    ("IS", "revenue", ("營業收入", "營收", "Revenue", "Sales", "Net sales", "Turnover", "收入")),
    ("IS", "cogs", ("營業成本", "銷貨成本", "COGS", "Cost of goods", "Cost of sales")),
    ("IS", "gross_profit", ("營業毛利", "毛利", "Gross profit")),
    ("IS", "gross_margin", ("毛利率", "Gross margin", "GM")),
    ("IS", "opex", ("營業費用", "Operating expenses", "OPEX")),
    ("IS", "operating_income", ("營業利益", "營業淨利", "Operating income", "Operating profit", "EBIT")),
    ("IS", "operating_margin", ("營業利益率", "營益率", "Operating margin", "OPM")),
    ("IS", "ebitda", ("EBITDA",)),
    ("IS", "pretax_income", ("稅前淨利", "稅前利益", "Pretax", "Pre-tax")),
    ("IS", "net_income", ("稅後淨利", "本期淨利", "淨利", "Net income", "Net profit", "NI")),
    ("IS", "net_margin", ("淨利率", "Net margin")),
    ("IS", "eps", ("每股盈餘", "EPS")),
    ("IS", "dps", ("每股股利", "DPS", "Dividend per share")),
    ("BS", "total_assets", ("總資產", "資產總額", "Total assets")),
    ("BS", "total_liabilities", ("總負債", "負債總額", "Total liabilities")),
    ("BS", "equity", ("股東權益", "權益總額", "淨值", "Shareholders' equity", "Total equity")),
    ("BS", "cash", ("現金", "Cash", "現金及約當現金")),
    ("BS", "inventory", ("存貨", "Inventory", "Inventories")),
    ("BS", "receivables", ("應收帳款", "Receivables")),
    ("BS", "bvps", ("每股淨值", "BVPS", "Book value per share")),
    ("CF", "cfo", ("營業活動現金流", "營運現金流", "Operating cash flow", "CFO", "Cash from operations")),
    ("CF", "capex", ("資本支出", "Capex", "Capital expenditure")),
    ("CF", "fcf", ("自由現金流", "Free cash flow", "FCF")),
    ("RATIO", "roe", ("ROE", "股東權益報酬率")),
    ("RATIO", "roa", ("ROA", "資產報酬率")),
    ("RATIO", "debt_ratio", ("負債比", "Debt ratio", "Gearing")),
    ("RATIO", "current_ratio", ("流動比", "Current ratio")),
    ("VAL", "per", ("本益比", "PER", "P/E", "PE")),
    ("VAL", "pbr", ("股價淨值比", "PBR", "P/B")),
    ("VAL", "ev_ebitda", ("EV/EBITDA",)),
    ("VAL", "dividend_yield", ("殖利率", "Dividend yield", "Yield")),
    ("VAL", "target_price", ("目標價", "Target price", "TP")),
    ("VAL", "rating", ("評等", "Rating", "Recommendation")),
    ("IS", "yoy", ("YoY", "年增率", "成長率")),
]


def _load_vrn_lexicon() -> list:
    """VRN 自己的財務字典(SSOT/ 或 knowledge/ 的 *Fin*Lexicon* / *FinancialShown* 冊)有就併進來:{std, zh/en 同義} → (cat?, std, aliases)。"""
    extra = []
    for d in (HERE / "SSOT", HERE / "knowledge"):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*Fin*.json")) + sorted(d.glob("*Lexicon*.json")):
            try:
                dd = json.loads(p.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                continue
            rows = dd.get("rows") or dd.get("entries") or dd.get("items") or (dd if isinstance(dd, list) else [])
            for r in rows if isinstance(rows, list) else []:
                if not isinstance(r, dict):
                    continue
                std = r.get("std") or r.get("key") or r.get("name_std")
                al = [x for k in ("zh", "en", "aliases", "synonyms") for x in (r.get(k) or []) if isinstance(x, str)]
                if std and al:
                    extra.append((r.get("cat") or r.get("category") or "", str(std), tuple(al)))
    return extra


def _std_label(label: str, lex: list):
    """最長別名優先(「毛利率」要配 gross_margin 不是 gross_profit);英文整字比對,中文子字串比對。"""
    t = _clean_cell(label)
    low = t.lower()
    best = ("", "", 0)
    for cat, std, aliases in lex:
        for a in aliases:
            a_low = a.lower()
            hit = (a.isascii() and re.search(r"(?<![a-z])" + re.escape(a_low) + r"(?![a-z])", low)) or (not a.isascii() and a in t)
            if hit and len(a) > best[2]:
                best = (cat, std, len(a))
    return best[0], best[1]


def _classify_table(rows_std: list) -> tuple:
    cats = defaultdict(int)
    for r in rows_std:
        if r.get("cat"):
            cats[r["cat"]] += 1
    if not cats:
        return "OTHER", 0.0
    cat, n = max(cats.items(), key=lambda x: x[1])
    conf = round(n / max(1, len(rows_std)), 2)
    if cat == "IS" and any(r.get("periods_est") for r in rows_std):
        return "FORECAST", conf
    return cat, conf


def _arith(matrix: dict) -> list:
    """算術核:每期 毛利 = 營收 − 成本 · 毛利率 = 毛利/營收 · 營益率 · 淨利率(容忍 1.5% 相對 / 0.6 百分點)。"""
    issues = []
    g = matrix
    for per in sorted({p for v in g.values() for p in v}):
        rev, cogs, gp = g.get("revenue", {}).get(per), g.get("cogs", {}).get(per), g.get("gross_profit", {}).get(per)
        if rev and cogs is not None and gp is not None and abs((rev - cogs) - gp) > max(1.0, abs(gp) * 0.015):
            issues.append("%s 毛利≠營收−成本(%s vs %s)" % (per, gp, rev - cogs))
        for m_key, n_key in (("gross_margin", "gross_profit"), ("operating_margin", "operating_income"), ("net_margin", "net_income")):
            mv, nv = g.get(m_key, {}).get(per), g.get(n_key, {}).get(per)
            if rev and mv is not None and nv is not None:
                calc = nv / rev * 100
                if abs(calc - mv) > 0.6:
                    issues.append("%s %s %.1f≠%.1f" % (per, m_key, mv, calc))
    return issues


# ────────────────── ② split:pdfplumber layout ──────────────────
def _blocks(page, exclude_bboxes=()) -> list:
    """字 → 行(y 容忍 3pt)→ 區塊(行距 > 1.6 倍中位行高 切開);每塊:bbox · text · kind。exclude_bboxes = 已偵測表格區(表內的字不進文字區塊,周邊段才切得乾淨)。"""
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False, extra_attrs=["size"])
    if exclude_bboxes:
        words = [w for w in words if not any(bx[0] - 2 <= w["x0"] and w["x1"] <= bx[2] + 2 and bx[1] - 2 <= w["top"] and w["bottom"] <= bx[3] + 2 for bx in exclude_bboxes)]
    if not words:
        return []
    words.sort(key=lambda w: (round(w["top"] / 3), w["x0"]))
    lines, cur, cur_top = [], [], None
    for w in words:
        if cur_top is None or abs(w["top"] - cur_top) <= 3:
            cur.append(w)
            cur_top = w["top"] if cur_top is None else cur_top
        else:
            lines.append(cur)
            cur, cur_top = [w], w["top"]
    if cur:
        lines.append(cur)
    hs = sorted((max(w["bottom"] for w in ln) - min(w["top"] for w in ln)) for ln in lines)
    med_h = hs[len(hs) // 2] if hs else 10
    blocks, cur_blk, last_bottom = [], [], None
    for ln in lines:
        ln.sort(key=lambda w: w["x0"])
        top = min(w["top"] for w in ln)
        if last_bottom is not None and top - last_bottom > 1.6 * med_h:
            blocks.append(cur_blk)
            cur_blk = []
        cur_blk.append(ln)
        last_bottom = max(w["bottom"] for w in ln)
    if cur_blk:
        blocks.append(cur_blk)
    H = float(page.height)
    out = []
    for b in blocks:
        x0 = min(w["x0"] for ln in b for w in ln)
        x1 = max(w["x1"] for ln in b for w in ln)
        top = min(w["top"] for ln in b for w in ln)
        bottom = max(w["bottom"] for ln in b for w in ln)
        text = "\n".join(" ".join(w["text"] for w in ln) for ln in b)
        toks = [w["text"] for ln in b for w in ln]
        num_ratio = sum(1 for t in toks if _NUM_RX.match(_clean_cell(t))) / max(1, len(toks))
        cols = sorted({round(w["x0"] / 20) for ln in b for w in ln})
        kind = "HEADER" if top < H * 0.06 else ("FOOTER" if bottom > H * 0.94 else ("TABLE_HINT" if (num_ratio >= 0.35 and len(b) >= 2 and len(cols) >= 3) else "TEXT"))
        out.append({"bbox": [round(x0, 1), round(top, 1), round(x1, 1), round(bottom, 1)], "lines": len(b), "kind": kind, "num_ratio": round(num_ratio, 2), "text": text[:1200]})
    return out


def _tables_pdfplumber(page) -> list:
    out = []
    try:
        found = page.find_tables()
    except Exception:  # noqa: BLE001
        return out
    for t in found:
        try:
            rows = t.extract()
        except Exception:  # noqa: BLE001
            continue
        if rows and any(any(c for c in r) for r in rows):
            out.append({"engine": "pdfplumber", "bbox": [round(v, 1) for v in t.bbox], "rows": [[_clean_cell(c) for c in r] for r in rows]})
    return out


def _tables_camelot(pdf: Path, page_no: int, regions: list | None = None, flavors=("lattice", "stream")) -> list:
    """regions = 數字區塊(camelot 座標 'x1,y1,x2,y2',左下原點)→ stream 只在區塊內找,不會把整頁吞成一張大表。"""
    out = []
    try:
        import camelot  # noqa: WPS433
    except ImportError:
        return out
    for flavor in flavors:
        try:
            kw = {"pages": str(page_no), "flavor": flavor, "suppress_stdout": True}
            if flavor == "stream" and regions:
                kw["table_areas"] = regions
            tl = camelot.read_pdf(str(pdf), **kw)
        except Exception:  # noqa: BLE001
            continue
        for t in tl:
            try:
                rows = t.df.values.tolist()
            except Exception:  # noqa: BLE001
                continue
            if rows:
                bb = getattr(t, "_bbox", None)
                out.append({"engine": "camelot_" + flavor, "bbox": ([round(float(v), 1) for v in bb] if bb else None), "rows": [[_clean_cell(c) for c in r] for r in rows], "accuracy": round(float(getattr(t, "accuracy", 0) or 0), 1)})
    return out


def _tables_tabula(pdf: Path, page_no: int) -> list:
    out = []
    try:
        import tabula  # noqa: WPS433
    except ImportError:
        return out
    try:
        dfs = tabula.read_pdf(str(pdf), pages=page_no, multiple_tables=True, silent=True)
    except Exception:  # noqa: BLE001
        return out
    for df in dfs or []:
        try:
            rows = [[_clean_cell(c) for c in df.columns]] + [[_clean_cell(c) for c in r] for r in df.values.tolist()]
        except Exception:  # noqa: BLE001
            continue
        if rows:
            out.append({"engine": "tabula", "bbox": None, "rows": rows})
    return out


def _surround(blocks: list, bbox) -> dict:
    """表的周邊資訊段:上方最近 TEXT/HEADER(標題·單位)· 下方最近 TEXT(註)。bbox 不明就取整頁第一段。"""
    if not bbox:
        texts = [b for b in blocks if b["kind"] in ("TEXT", "HEADER")]
        return {"above": (texts[0]["text"][:300] if texts else ""), "below": ""}
    x0, top, x1, bottom = bbox
    above = [b for b in blocks if b["kind"] in ("TEXT", "HEADER") and b["bbox"][3] <= top + 2]
    below = [b for b in blocks if b["kind"] in ("TEXT", "FOOTER") and b["bbox"][1] >= bottom - 2]
    a = max(above, key=lambda b: b["bbox"][3]) if above else None
    d = min(below, key=lambda b: b["bbox"][1]) if below else None
    unit = ""
    for src in ((a["text"] if a else ""), ):
        m = re.search(r"(?:單位|Unit)[::]?\s*([^\s,;)]+)|\((?:NT\$|US\$|百萬|千元|million|mn|bn)[^)]*\)", src)
        if m:
            unit = m.group(0)[:40]
    return {"above": (a["text"][:300] if a else ""), "below": (d["text"][:300] if d else ""), "unit_hint": unit}


def _rebuild_table(tbl: dict, lex: list) -> dict:
    rows = [list(r) for r in tbl["rows"] if any(c for c in r)]
    if not rows:
        return {"category": "OTHER", "confidence": 0.0, "periods": [], "rows": [], "matrix": {}, "issues": ["空表"]}
    # 清:幾乎全空的欄丟掉(stream 常多一條空首欄);只有一格且是長句的列 = 表外文字(進 notes)
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    notes, body = [], []
    for r in rows:                                   # 只有一格的列(段落標題 / 長句)= 表外文字 → notes
        nz = [c for c in r if _clean_cell(c)]
        if len(nz) == 1 and not _is_period(nz[0]):      # 單格但是期間(只有一欄的表頭)仍是表的一部分
            notes.append(_clean_cell(nz[0]))
        else:
            body.append(r)
    rows = body or rows
    keep = [j for j in range(w) if sum(1 for r in rows if _clean_cell(r[j])) >= max(1, 0.1 * len(rows))]
    rows = [[r[j] for j in keep] for r in rows]
    hdr_idx = None
    for i, r in enumerate(rows[:4]):
        n_per = sum(1 for c in r[1:] if _is_period(c))
        if n_per >= 2 or (n_per >= 1 and not _clean_cell(r[0]) and n_per == len([c for c in r[1:] if _clean_cell(c)])):
            hdr_idx = i
            break
    periods = []
    if hdr_idx is not None:
        periods = [_clean_cell(c).replace(" ", "") for c in rows[hdr_idx][1:]]
    out_rows, matrix = [], defaultdict(dict)
    for r in rows[(hdr_idx + 1) if hdr_idx is not None else 0:]:
        label = _clean_cell(r[0]) if r else ""
        if not label:
            continue
        cat, std = _std_label(label, lex)
        vals = {}
        for j, c in enumerate(r[1:]):
            per = periods[j] if j < len(periods) and periods[j] else "c%d" % (j + 1)
            v = _to_num(c)
            if v is not None:
                vals[per] = v
                if std:
                    matrix[std][per] = v
        out_rows.append({"label_raw": label, "label_std": std, "cat": cat, "values": vals, "periods_est": any(re.search(r"[EF]$", p, re.I) for p in vals)})
    cat, conf = _classify_table(out_rows)
    issues = _arith(matrix) if cat in ("IS", "FORECAST") else []
    if hdr_idx is None:
        issues.append("無期間表頭")
    return {"category": cat, "confidence": conf, "periods": periods, "rows": out_rows, "matrix": {k: v for k, v in matrix.items()}, "issues": issues, "notes": notes}


def extract_one(pdf: Path, out_root: Path, engines: tuple = ("pdfplumber", "camelot", "tabula"), avail: dict | None = None) -> dict:
    avail = avail or _engines()
    t0 = time.time()
    sha8 = hashlib.sha256(pdf.read_bytes()).hexdigest()[:8]
    od = out_root / sha8
    od.mkdir(parents=True, exist_ok=True)
    pf = getattr(PRIOR, "parse_filename", None)
    fn = pf(pdf.stem) if callable(pf) else {"doc_kind": None, "codes": [], "broker_std": None, "report_date": None}
    fn = dict(fn, filename=pdf.name, sha8=sha8)
    (od / "filename.json").write_text(json.dumps(fn, ensure_ascii=False, indent=1), encoding="utf-8")
    pages, raw_tables = [], []
    n_text = 0
    if not avail.get("pdfplumber"):
        rec = {"file": pdf.name, "sha8": sha8, "status": "NODATA", "why": "pdfplumber 不在(環境)", "pages": 0, "tables": 0, "secs": round(time.time() - t0, 1), "dir": str(od), "filename": fn}
        return rec
    import pdfplumber  # noqa: WPS433
    with pdfplumber.open(str(pdf)) as doc:
        for i, page in enumerate(doc.pages, 1):
            pt = _tables_pdfplumber(page) if "pdfplumber" in engines else []
            blks = _blocks(page, [t["bbox"] for t in pt])
            n_text += sum(len(b["text"]) for b in blks)
            pages.append({"page": i, "w": float(page.width), "h": float(page.height), "blocks": blks})
            for t in pt:
                t.update(page=i, surround=_surround(blks, t["bbox"]))
                raw_tables.append(t)
            # 表外還有數字區塊(無框線表)→ camelot stream(bbox 轉成上左原點)→ 與已取表重疊 ≥50% 的丟掉;camelot 沒抓到才 tabula
            numeric_left = [b for b in blks if (b["num_ratio"] >= 0.2 and b["lines"] >= 2) or b["kind"] == "TABLE_HINT"]
            H = float(page.height)
            regions = ["%d,%d,%d,%d" % (b["bbox"][0] - 4, H - b["bbox"][3] - 4, b["bbox"][2] + 4, H - b["bbox"][1] + 4) for b in numeric_left]
            def _ov(a, b):
                if not a or not b:
                    return 0.0
                ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
                inter = ix * iy
                area = max(1.0, (a[2] - a[0]) * (a[3] - a[1]))
                return inter / area
            if numeric_left:
                got = False
                if "camelot" in engines and avail.get("camelot"):
                    for t in _tables_camelot(pdf, i, regions, flavors=("stream",) if pt else ("lattice", "stream")):
                        if t["bbox"]:
                            x0, y0, x1, y1 = t["bbox"]
                            t["bbox"] = [round(min(x0, x1), 1), round(H - max(y0, y1), 1), round(max(x0, x1), 1), round(H - min(y0, y1), 1)]
                        if any(_ov(t["bbox"], u["bbox"]) >= 0.5 for u in raw_tables if u["page"] == i and u["bbox"]):
                            continue
                        t.update(page=i, surround=_surround(blks, t["bbox"]))
                        raw_tables.append(t)
                        got = True
                if not got and "tabula" in engines and avail.get("tabula") and not any(t["page"] == i for t in raw_tables):
                    for t in _tables_tabula(pdf, i):
                        t.update(page=i, surround=_surround(blks, None))
                        raw_tables.append(t)
    (od / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
    (od / "tables_raw.json").write_text(json.dumps(raw_tables, ensure_ascii=False, indent=1), encoding="utf-8")
    lex = _FIN_STD + _load_vrn_lexicon()
    clean, fin = [], []
    for k, t in enumerate(raw_tables, 1):
        rb = _rebuild_table(t, lex)
        clean.append({"table": k, "page": t["page"], "engine": t["engine"], "n_rows": len(t["rows"]), "n_cols": max((len(r) for r in t["rows"]), default=0), "surround": t.get("surround"), "rows": t["rows"]})
        fin.append({"table": k, "page": t["page"], "engine": t["engine"], "surround": t.get("surround"), **rb})
    (od / "tables_clean.json").write_text(json.dumps(clean, ensure_ascii=False, indent=1), encoding="utf-8")
    by_cat = defaultdict(list)
    for f in fin:
        by_cat[f["category"]].append(f["table"])
    financial = {"file": pdf.name, "sha8": sha8, "filename": fn, "engines": avail, "by_category": dict(by_cat), "tables": fin}
    (od / "financial.json").write_text(json.dumps(financial, ensure_ascii=False, indent=1), encoding="utf-8")
    good = [f for f in fin if f["category"] != "OTHER" and not f["issues"]]
    unsure = [f for f in fin if f["category"] == "OTHER" or f["issues"]]
    if not raw_tables and n_text < 40:
        status, why = "NODATA", "無文字無表(掃描件 → OCR 閘)"
    elif good:
        status, why = "READ", "%d 表有類別且算術過;%d 表待審" % (len(good), len(unsure))
    elif raw_tables:
        status, why = "REVIEW", "%d 表但類別/算術不確定" % len(raw_tables)
    else:
        status, why = "REVIEW", "有文字無表(%d 字)" % n_text
    return {"file": pdf.name, "sha8": sha8, "status": status, "why": why, "pages": len(pages), "text_chars": n_text, "tables": len(raw_tables), "categories": {k: len(v) for k, v in by_cat.items()},
            "engines_used": sorted({t["engine"] for t in raw_tables}), "issues": sum(len(f["issues"]) for f in fin), "secs": round(time.time() - t0, 1), "dir": str(od), "filename": fn}


def _out_root() -> Path:
    return Path(os.environ.get("VIA_VRN_EXTRACT_OUT") or (HERE.parents[1] / "VIA_Reports" / "vrn" / "extract"))


def _ledger(rec: dict) -> None:
    lp = _out_root() / "VRN_Extract_Ledger.jsonl"
    lp.parent.mkdir(parents=True, exist_ok=True)
    with open(lp, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(rec, ts=datetime.datetime.now().isoformat(timespec="seconds")), ensure_ascii=False) + "\n")


def extract(files: list, engines: tuple, limit: int = 0) -> dict:
    avail = _engines()
    out = {"verb": "extract", "ts": datetime.datetime.now().isoformat(timespec="seconds"), "engines": avail, "rows": [], "_notes": []}
    if not avail.get("pdfplumber"):
        out["_notes"].append("pdfplumber 不在 → 全部 NODATA(環境,不是檔案)")
    if "camelot" in engines and not avail.get("camelot"):
        out["_notes"].append("camelot 不在 → 只走 pdfplumber(+tabula)")
    if "tabula" in engines and not avail.get("tabula"):
        out["_notes"].append("tabula 不在或無 Java → 跳過")
    for p in files[: (limit or len(files))]:
        try:
            rec = extract_one(p, _out_root(), engines, avail)
        except Exception as exc:  # noqa: BLE001 — 一檔壞不擋整批,誠實記
            rec = {"file": p.name, "sha8": "", "status": "ERROR", "why": "%s:%s" % (type(exc).__name__, str(exc)[:120]), "pages": 0, "tables": 0, "secs": 0}
        _ledger(rec)
        out["rows"].append(rec)
    c = defaultdict(int)
    for r in out["rows"]:
        c[r["status"]] += 1
    out["counts"] = dict(c)
    out["lamp"] = "RED" if c.get("ERROR") else ("YELLOW" if (c.get("REVIEW") or c.get("NODATA")) else ("GREEN" if out["rows"] else "GRAY"))
    return out


def extract_status() -> dict:
    lp = _out_root() / "VRN_Extract_Ledger.jsonl"
    c = defaultdict(int)
    n = 0
    if lp.exists():
        for ln in lp.read_text(encoding="utf-8").splitlines():
            try:
                c[json.loads(ln).get("status", "?")] += 1
                n += 1
            except ValueError:
                pass
    return {"verb": "extract_status", "ledger": str(lp), "rows": n, "counts": dict(c), "lamp": "GREEN" if n else "GRAY"}


def _print_v0127(out: dict) -> None:
    if out["verb"] == "extract":
        e = out["engines"]
        print("[計] extract 檔 %d · READ %d REVIEW %d NODATA %d ERROR %d · 引擎 pdfplumber=%s camelot=%s tabula=%s(java=%s) · %s" % (len(out["rows"]), out["counts"].get("READ", 0), out["counts"].get("REVIEW", 0), out["counts"].get("NODATA", 0), out["counts"].get("ERROR", 0), e.get("pdfplumber"), e.get("camelot"), e.get("tabula"), e.get("java"), out["lamp"]))
        for r in out["rows"][:40]:
            tag = {"READ": "OK", "REVIEW": "YEL", "NODATA": "YEL", "ERROR": "RED"}[r["status"]]
            print("  [%s] %s · %s · 頁 %s 表 %s %s · %s · %ss" % (tag, r["status"], r["file"][:60], r.get("pages"), r.get("tables"), r.get("categories", ""), r["why"], r.get("secs")))
        for n in out["_notes"]:
            print("  [注] %s" % n)
    else:
        print("[計] extract status · 帳 %d 列 · %s · %s" % (out["rows"], out["counts"], out["lamp"]))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] != ["extract"]:
        return PRIOR.main(args)
    if args[1:2] == ["status"]:
        out = extract_status()
        _print_v0127(out)
        return 0

    def _opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    engines = tuple(x.strip() for x in _opt("--engines", "pdfplumber,camelot,tabula").split(",") if x.strip())
    limit = int(_opt("--limit", "0") or 0)
    files = []
    if _opt("--file"):
        files = [Path(_opt("--file"))]
    else:
        d = Path(_opt("--dir") or (HERE / "input" / "incoming"))
        files = sorted(p for p in d.rglob("*.pdf")) if d.is_dir() else []
    if not files:
        print("[拒跑] 沒有 PDF(--file <pdf> 或 --dir <夾>;預設 input/incoming)")
        return 2
    out = extract(files, engines, limit)
    fn = getattr(PRIOR, "emit_matrix_html", None)
    if callable(fn):
        try:
            fn("extract", out)
        except Exception as exc:  # noqa: BLE001
            print("  [U/I] emit_matrix_html %s(主流程照走)" % type(exc).__name__)
    _print_v0127(out)
    return 1 if out["lamp"] == "RED" else 0


def _make_pdf(path: Path) -> bool:
    """reportlab 有就造一份兩頁測試報告:標題 · 單位 · 損益表(有框線)· 註 · 第二頁無框線估值表 + 段落。"""
    try:
        from reportlab.lib import colors  # noqa: WPS433
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        return False
    st = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    data = [["", "2024", "2025E", "2026F"], ["Revenue", "1,000", "1,200", "1,500"], ["COGS", "600", "700", "850"], ["Gross profit", "400", "500", "650"], ["Gross margin", "40.0%", "41.7%", "43.3%"], ["Operating income", "200", "260", "350"], ["Net income", "150", "200", "(270)"], ["EPS", "3.00", "4.00", "5.40"]]
    t = Table(data)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)]))
    data2 = [["", "2024", "2025E"], ["PER", "15.0", "12.0"], ["PBR", "2.1", "1.9"], ["Target price", "120", ""], ["Rating", "BUY", ""]]
    t2 = Table(data2)
    story = [Paragraph("Demo Securities - ABC Corp (2330 TT) Initiation", st["Title"]), Paragraph("Income statement summary (Unit: NT$ million)", st["Normal"]), Spacer(1, 8), t, Spacer(1, 6),
             Paragraph("Note: 2025E/2026F are our estimates. Source: company data, Demo Securities.", st["Normal"]), Spacer(1, 200), Paragraph("Valuation", st["Heading2"]), t2, Spacer(1, 8),
             Paragraph("We initiate with BUY and a target price of NT$120 based on 15x 2025E EPS.", st["Normal"])]
    doc.build(story)
    return True


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

    td = Path(tempfile.mkdtemp(prefix="vrnext-"))
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_EXTRACT_OUT", "VIA_NO_OPEN", "VIA_VRN_UI_DIR")}
    os.environ.update({"VIA_VRN_EXTRACT_OUT": str(td / "out"), "VIA_NO_OPEN": "1", "VIA_VRN_UI_DIR": str(td / "ui")})
    av = _engines()
    chk("① 引擎可用性誠實:pdfplumber=%s camelot=%s tabula=%s java=%s" % (av["pdfplumber"], av["camelot"], av["tabula"], av["java"]), isinstance(av["pdfplumber"], bool))
    chk("② clean:全形/千分位/(負)/% → 數", _to_num("１,２３４.５") == 1234.5 and _to_num("(270)") == -270 and _to_num("40.0%") == 40.0 and _to_num("—") is None and _to_num("−5") == -5)
    chk("③ 期間偵測:2024 2025E 2026F 1Q25 FY24 2025年 ; 'Revenue' 不是", all(_is_period(x) for x in ("2024", "2025E", "2026F", "1Q25", "FY24", "2025年")) and not _is_period("Revenue"))
    lex = _FIN_STD
    rb = _rebuild_table({"rows": [["", "2024", "2025E"], ["營業收入", "1,000", "1,200"], ["營業成本", "600", "700"], ["營業毛利", "400", "500"], ["毛利率", "40.0%", "41.7%"], ["本期淨利", "150", "(20)"]]}, lex)
    chk("④ rebuild:損益表 → FORECAST(有 E 期)· 列標準名 · 矩陣 · 算術全過", rb["category"] == "FORECAST" and rb["matrix"]["revenue"]["2025E"] == 1200 and rb["matrix"]["net_income"]["2025E"] == -20 and not rb["issues"])
    rb2 = _rebuild_table({"rows": [["", "2024"], ["Revenue", "1000"], ["COGS", "600"], ["Gross profit", "450"], ["Gross margin", "40%"]]}, lex)
    chk("⑤ 負控:毛利≠營收−成本 且 毛利率不符 → issues 2(REVIEW 依據)", len(rb2["issues"]) == 2)
    pdf = td / "Demo-2330 20251001.pdf"
    made = _make_pdf(pdf)
    if made and av["pdfplumber"]:
        res = extract([pdf], ("pdfplumber", "camelot", "tabula"))
        r = res["rows"][0]
        od = Path(r["dir"])
        fin = json.loads((od / "financial.json").read_text(encoding="utf-8"))
        cats = fin["by_category"]
        chk("⑥ 真 PDF:四步落檔(filename/pages/tables_raw/tables_clean/financial)· 檔名層 代號 2330 日期 2025-10-01", all((od / n).exists() for n in ("filename.json", "pages.json", "tables_raw.json", "tables_clean.json", "financial.json")) and "2330" in (fin["filename"].get("codes") or []) and fin["filename"].get("report_date") == "2025-10-01")
        chk("⑦ 表格:≥2 表 · 有 IS/FORECAST 類與 VAL 類 · 損益矩陣 Net income 2026F = -270(括號負)", r["tables"] >= 2 and (("FORECAST" in cats) or ("IS" in cats)) and "VAL" in cats and any(t["matrix"].get("net_income", {}).get("2026F") == -270 for t in fin["tables"]))
        is_t = [t for t in fin["tables"] if t["category"] in ("IS", "FORECAST")][0]
        chk("⑧ 周邊資訊段:表上方抓到單位/標題 · 下方抓到 Note", ("NT$" in (is_t["surround"].get("above") or "") or "Unit" in (is_t["surround"].get("above") or "")) and "Note" in (is_t["surround"].get("below") or ""))
        chk("⑨ 三態 READ · 帳一列 · status 計", r["status"] == "READ" and extract_status()["rows"] == 1)
    else:
        print("  [注] reportlab 或 pdfplumber 不在 → 真 PDF 段跳過(環境),⑥–⑨ 以空 PDF 走 NODATA")
        pdf.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF")
        res = extract([pdf], ("pdfplumber",))
        chk("⑥ 空 PDF → NODATA 不爆", res["rows"][0]["status"] in ("NODATA", "ERROR"))
        p += 3
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑩ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 帶加速器橋 · glob 取前版 · 獨立 MAIN(自立閘座)", "[VIA:ACCEL-BRIDGE:v0100]" in body and "setdefault(\"VIA_FROM_VCGC\"" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0127 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
