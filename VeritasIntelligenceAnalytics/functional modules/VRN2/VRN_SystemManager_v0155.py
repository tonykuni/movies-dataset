#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0155 — 薄尾:layout(操作員 2026-10-10:版面引擎只有一個最新最強的版本 → 抓首頁與年度財報頁)。
  layout [--dir 夾] [--max N] [--only 檔名片段] [--recursive]
     版面引擎 = VRN_ENG394_LayoutRestore 尾版(VRN 自家;子分類走它的 _subcat,規則冊 VRN_LayoutRestore_SSOT)——照紀錄(v0119 deepread 正典 · v0108 交接包 segment_firstpages)
     首頁:先抓股票名稱與代號(檔名 → 首頁內文互證)→ 左右切(欄間空白帶)→ 上下切(行距 · 樣式分段)
           本文區 BODY / 資訊區 INFO 由關鍵詞密度定(目標價 · 評等 · 收盤 · 分析師 · @ · Tel …),左右都可;頁首 H / 頁尾 B 另分
           主標題 = 首頁上半部字級最大(粗)、無句號的一句話
     年度財報頁:年份序列 + 財務關鍵詞 + 數字密度選頁(最多 6 頁)→ 先左右切再上下切 → 每張表一個相對位置編號 P頁·區·序號·T表號
     表格:pdfplumber 格線 → 文字分欄 → 座標分欄 → tabula(有 Java 才用)取最佳 → 修補(空列 · 空欄 · 換行列標)
     分類兩層:第一層 文字 / 表格 / 圖;第二層 文字 = 主標題 · H1–H4 標題 · 重點條列 · 內文 · 註 · 圖表標題 · 資訊 · 頁首 · 頁尾;表 = 財務表(損益 / 資產負債 / 現金流量)· 估值表 · 資訊表 · 數據表;再加 ENG394 _subcat
     字型階層:全報告依(字級, 粗細)字數統計 → 最多字的 = 內文;比它大或粗且少的 = H1–H4;比它小 = 註
     產出:每檔一頁 HTML(左 = 本文 · 右 = 資訊區 · 下 = 年度財報頁版面圖與表)+ LAYOUT_MATRIX_latest.html(跳出)
  另:fname / prep 預設只掃最上層(--recursive 才往下);券商短縮寫正本 = 鏈上 _broker_map(同義字冊裁定:兆豐 MEGA · 麥格理 MCQ)
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
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0155"


def _vnum_v0155(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0155(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0155(p) < _vnum_v0155(__file__)), key=_vnum_v0155)
PRIOR = _load_v0155(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _resolve(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return vars(mod)[name]
        mod = vars(mod).get("PRIOR")
    return None


_home, _rep = _resolve("_home"), _resolve("_rep")

# ───────── ① 只掃最上層(--recursive 才往下)· ② 券商短縮寫正本 = 鏈上 _broker_map(同義字冊裁定)─────────


class _TopPath(type(Path())):
    def rglob(self, pattern):
        import fnmatch
        return (p for p in self.iterdir() if fnmatch.fnmatch(p.name, pattern))


_ORIG_ABBR = _resolve("_abbr_of")


def _abbr_of_v155(book: dict, canon: str) -> tuple:
    bm = _resolve("_broker_map")
    if bm:
        try:
            m = {str(k).lower(): str(v) for k, v in (bm() or {}).items()}
            for key in [canon] + sorted((book.get(canon) or {}).get("aliases", {}), key=len, reverse=True):
                v = m.get(str(key).lower())
                if v and v.isascii():
                    return v, "冊"
        except Exception:  # noqa: BLE001
            pass
    return _ORIG_ABBR(book, canon) if _ORIG_ABBR else ("", "—")


if _ORIG_ABBR:
    PRIOR._abbr_of = _abbr_of_v155

# ───────── 版面引擎:ENG394 LayoutRestore(VRN 自家,唯一 · 取最新)─────────
_ENG = {}


def eng394() -> dict:
    if _ENG:
        return _ENG
    hits = sorted(_home().glob("VRN_ENG394_LayoutRestore_v*.py"), key=lambda q: _vnum_v0155(q.stem))
    _ENG.update(file=hits[-1].name if hits else "", mod=None, subcat=None, pattern="", err="", rulebook="", rule_keys=[])
    for rb in sorted(list((_home() / "SSOT").glob("VRN_LayoutRestore_SSOT_v*.json")) + list((_home().parents[1] / "supportive modules" / "registry").glob("VIA_VRN_LayoutRestore_SSOT_v*.json"))):
        try:
            d = json.loads(rb.read_text(encoding="utf-8-sig"))
            _ENG.update(rulebook=rb.name, rule_keys=list(d.keys())[:20] if isinstance(d, dict) else [])
        except (OSError, ValueError):
            pass
    if not hits:
        _ENG["err"] = "樹上沒有 VRN_ENG394_LayoutRestore"
        return _ENG
    try:
        mod = _load_v0155(hits[-1], "vrn_eng394_for_v0155")
        _ENG["mod"] = mod
        fn = getattr(mod, "_subcat", None)
        if callable(fn):
            for pat in ("text", "kind_text", "dict"):
                try:
                    r = fn("Revenue 2024A 2025F") if pat == "text" else (fn("table", "Revenue 2024A 2025F") if pat == "kind_text" else fn({"type": "table", "text": "Revenue 2024A 2025F"}))
                    if r is not None:
                        _ENG.update(subcat=fn, pattern=pat)
                        break
                except Exception:  # noqa: BLE001
                    continue
            if not _ENG["subcat"]:
                _ENG["err"] = "_subcat 介面對不上(%s)" % str(inspect.signature(fn))[:60]
        else:
            _ENG["err"] = "ENG394 沒有 _subcat"
    except Exception as exc:  # noqa: BLE001
        _ENG["err"] = "載入失敗 %s:%s" % (type(exc).__name__, str(exc)[:80])
    return _ENG


def _eng_subcat(kind: str, text: str) -> str:
    e = eng394()
    fn = e.get("subcat")
    if not fn:
        return ""
    try:
        r = fn(text) if e["pattern"] == "text" else (fn(kind, text) if e["pattern"] == "kind_text" else fn({"type": kind, "text": text}))
        if isinstance(r, (tuple, list)) and r:
            r = r[0]
        if isinstance(r, dict):
            r = r.get("subcat") or r.get("category") or r.get("cat") or json.dumps(r, ensure_ascii=False)[:30]
        return str(r)[:30] if r is not None else ""
    except Exception:  # noqa: BLE001
        return ""


# ───────── 版面分析(pdfplumber 為主 · tabula 為輔)─────────
_BOLD_RX = re.compile(r"(?i)bold|black|heavy|semibold|demi|W[6-9](?!\d)|-B(?:,|$)|Bd(?:$|,)")
_INFO_KW = ("目標價", "評等", "收盤", "市值", "股價", "分析師", "投資建議", "Target", "Rating", "Close", "Price", "Market cap", "Bloomberg", "Reuters", "Analyst", "@", "Tel", "TEL", "電話", "52")
_FIN_KW = ("EPS", "每股盈餘", "營收", "營業收入", "淨利", "稅後", "毛利", "營業利益", "ROE", "Revenue", "Net income", "Gross", "Operating", "Income statement", "Balance sheet", "Cash flow", "損益", "資產負債", "現金流量", "BVPS", "DPS", "Sales")
_VAL_KW = ("P/E", "PER", "P/B", "PBR", "本益比", "股價淨值比", "EV/EBITDA", "Valuation", "評價", "殖利率")
_YEAR_RX = re.compile(r"(?<![\d.])(?:20\d{2}[AEF]?|FY\d{2,4}[AEF]?|\d{2}[AEF])(?![\d])")
_NUM_RX = re.compile(r"^[\(\-–+]?[\d,]+(?:\.\d+)?%?\)?$")
_BULLET_RX = re.compile(r"^\s*(?:[●•■◆▪‧◎◼➢►\-–\*]|\d{1,2}[\.、\)])\s*")
_CAPTION_RX = re.compile(r"^\s*(?:圖|表|Figure|Fig\.|Exhibit|Table|Chart)\s*[\d一二三四五六七八九十]+")
_NOTE_RX = re.compile(r"^\s*(?:註|資料來源|來源|Source|Note)[:：\s]")


def _lines(page) -> list:
    words = page.extract_words(extra_attrs=["fontname", "size"], use_text_flow=False, keep_blank_chars=False, x_tolerance=1.5, y_tolerance=2.5)
    words.sort(key=lambda w: (round(w["top"], 1), w["x0"]))
    rows = []
    for w in words:
        if rows and abs(rows[-1][-1]["top"] - w["top"]) <= 2.5:
            rows[-1].append(w)
        else:
            rows.append([w])
    out = []
    for r in rows:
        r.sort(key=lambda w: w["x0"])
        seg = [r[0]]
        for w in r[1:]:
            gap = w["x0"] - seg[-1]["x1"]
            if gap > max(10.0, 1.6 * float(w.get("size") or 9)):
                out.append(seg)
                seg = [w]
            else:
                seg.append(w)
        out.append(seg)
    lines = []
    for seg in out:
        txt = ""
        for i, w in enumerate(seg):
            if i and (w["x0"] - seg[i - 1]["x1"]) > 0.25 * float(w.get("size") or 9):
                txt += " "
            txt += w["text"]
        sizes = [float(w.get("size") or 0) for w in seg]
        nb = sum(len(w["text"]) for w in seg if _BOLD_RX.search(str(w.get("fontname", ""))))
        nall = sum(len(w["text"]) for w in seg) or 1
        lines.append({"text": txt.strip(), "x0": min(w["x0"] for w in seg), "x1": max(w["x1"] for w in seg), "top": min(w["top"] for w in seg), "bottom": max(w["bottom"] for w in seg),
                      "size": round(max(sizes), 1), "bold": nb / nall >= 0.5, "font": str(seg[0].get("fontname", "")), "kind": "text"})
    return lines


def _figures(page, tables: list) -> list:
    W, H = float(page.width), float(page.height)
    out = []
    for im in page.images:
        bx = (float(im["x0"]), float(im["top"]), float(im["x1"]), float(im["bottom"]))
        if (bx[2] - bx[0]) * (bx[3] - bx[1]) >= 0.015 * W * H:
            out.append(bx)
    objs = [(float(o["x0"]), float(o["top"]), float(o["x1"]), float(o["bottom"])) for o in (page.curves + page.lines) if not any(t[0] - 2 <= o["x0"] and o["x1"] <= t[2] + 2 and t[1] - 2 <= o["top"] and o["bottom"] <= t[3] + 2 for t in tables)]
    objs.sort(key=lambda b: (b[1], b[0]))
    clusters = []
    for b in objs:
        for c in clusters:
            if b[0] <= c["box"][2] + 12 and b[2] >= c["box"][0] - 12 and b[1] <= c["box"][3] + 12 and b[3] >= c["box"][1] - 12:
                c["box"] = (min(c["box"][0], b[0]), min(c["box"][1], b[1]), max(c["box"][2], b[2]), max(c["box"][3], b[3]))
                c["n"] += 1
                break
        else:
            clusters.append({"box": b, "n": 1})
    for c in clusters:
        x0, t, x1, b = c["box"]
        if c["n"] >= 12 and (x1 - x0) * (b - t) >= 0.015 * W * H:
            out.append(c["box"])
    return out


def _table_boxes(page, annual: bool) -> list:
    boxes = []
    try:
        for t in page.find_tables():
            boxes.append(("lines", tuple(float(v) for v in t.bbox)))
    except Exception:  # noqa: BLE001
        pass
    if annual and not boxes:
        try:
            for t in page.find_tables({"vertical_strategy": "text", "horizontal_strategy": "text", "min_words_vertical": 3, "min_words_horizontal": 2}):
                rows = t.extract() or []
                cells = [c for r in rows for c in r if c and str(c).strip()]
                num = sum(1 for c in cells if _NUM_RX.match(str(c).replace(" ", "")))
                if len(rows) >= 3 and max((len(r) for r in rows), default=0) >= 3 and cells and num / len(cells) >= 0.35:
                    boxes.append(("text", tuple(float(v) for v in t.bbox)))
        except Exception:  # noqa: BLE001
            pass
    return boxes


def _repair_rows(rows: list) -> tuple:
    fixes = []
    rr = []
    for r in rows or []:
        r2 = [re.sub(r"\s+", " ", str(c if c is not None else "")).strip() for c in r]
        if any(r2):
            rr.append(r2)
        else:
            fixes.append("刪空列")
    if not rr:
        return [], fixes
    w = max(len(r) for r in rr)
    rr = [r + [""] * (w - len(r)) for r in rr]
    keep = [j for j in range(w) if any(r[j] for r in rr)]
    if len(keep) < w:
        fixes.append("刪空欄 %d" % (w - len(keep)))
    rr = [[r[j] for j in keep] for r in rr]
    merged = []
    for r in rr:
        is_label_only = r[0] and not any(r[1:])
        if merged and not r[0] and any(r[1:]) and merged[-1][0] and not any(merged[-1][1:]):
            merged[-1] = [merged[-1][0]] + r[1:]
            fixes.append("併換行列標")
            continue
        merged.append(r)
    return merged, fixes


def _cluster_table(page, bbox) -> list:
    """沒有格線的數字區:字詞依 top 成列、依 x 中心分欄(初階還原)。"""
    crop = page.crop(bbox)
    ws = crop.extract_words(x_tolerance=1.5, y_tolerance=2.5)
    if not ws:
        return []
    ws.sort(key=lambda w: (round(w["top"], 1), w["x0"]))
    rows = []
    for w in ws:
        if rows and abs(rows[-1][-1]["top"] - w["top"]) <= 2.5:
            rows[-1].append(w)
        else:
            rows.append([w])
    xs = sorted({round((w["x0"] + w["x1"]) / 2) for r in rows for w in r})
    cols = []
    for x in xs:
        if cols and x - cols[-1][-1] <= 14:
            cols[-1].append(x)
        else:
            cols.append([x])
    centers = [sum(c) / len(c) for c in cols]
    grid = []
    for r in rows:
        line = [""] * len(centers)
        for w in r:
            xc = (w["x0"] + w["x1"]) / 2
            j = min(range(len(centers)), key=lambda k: abs(centers[k] - xc))
            line[j] = (line[j] + " " + w["text"]).strip()
        grid.append(line)
    return grid


def _extract_table(page, bbox, how: str, pdf_path: str, pno: int, tabula_ok: bool) -> dict:
    cands = []
    try:
        rows = page.crop(bbox).extract_table() if how == "lines" else page.crop(bbox).extract_table({"vertical_strategy": "text", "horizontal_strategy": "text"})
        if rows:
            cands.append(("pdfplumber-" + how, rows))
    except Exception:  # noqa: BLE001
        pass
    try:
        g = _cluster_table(page, bbox)
        if g:
            cands.append(("座標分欄", g))
    except Exception:  # noqa: BLE001
        pass
    def score(rows):
        rr, _ = _repair_rows(rows)
        cells = [c for r in rr for c in r]
        filled = [c for c in cells if c]
        num = sum(1 for c in filled if _NUM_RX.match(c.replace(" ", "")))
        multi = sum(1 for c in filled if len(re.findall(r"[\d,]+\.?\d*", c)) >= 2 and " " in c)
        return num * 2 + len(filled) - multi * 3 - (len(cells) - len(filled)) * 0.3

    def weak(rows):
        rr, _ = _repair_rows(rows)
        cells = [c for r in rr for c in r]
        return len(rr) < 2 or not cells or sum(1 for c in cells if c) / len(cells) < 0.5 or any(len(re.findall(r"[\d,]+\.?\d*", c)) >= 2 and " " in c for c in cells)
    if tabula_ok and (not cands or weak(max(cands, key=lambda kv: score(kv[1]))[1])):      # tabula 只在 pdfplumber 抽得不好時補位(每次啟 Java 很慢)
        try:
            import tabula  # noqa: WPS433
            H = float(page.height)
            dfs = tabula.read_pdf(pdf_path, pages=pno, area=[bbox[1], bbox[0], bbox[3], bbox[2]], stream=True, guess=False, pandas_options={"header": None}, silent=True)
            if dfs:
                cands.append(("tabula", [[("" if str(v) == "nan" else str(v)) for v in row] for row in dfs[0].values.tolist()]))
        except Exception:  # noqa: BLE001
            pass

    if not cands:
        return {"engine": "", "rows": [], "fixes": ["抽不到"]}
    eng, best = max(cands, key=lambda kv: score(kv[1]))
    rr, fixes = _repair_rows(best)
    return {"engine": eng, "rows": rr, "fixes": fixes, "alts": [k for k, _ in cands]}


def _table_cat(rows: list, zone_role: str) -> str:
    txt = " ".join(" ".join(r) for r in rows[:40])
    yrs = len(_YEAR_RX.findall(" ".join(rows[0]) if rows else ""))
    if zone_role == "INFO":
        return "資訊表"
    if any(k.lower() in txt.lower() for k in _VAL_KW) and not any(k.lower() in txt.lower() for k in ("revenue", "營收", "net income", "淨利")):
        return "估值表"
    if yrs >= 2 or len(_YEAR_RX.findall(txt)) >= 3:
        if re.search(r"(?i)balance|資產負債|total assets|資產總", txt):
            return "財務表·資產負債"
        if re.search(r"(?i)cash ?flow|現金流", txt):
            return "財務表·現金流量"
        if re.search(r"(?i)revenue|sales|營收|營業收入|net income|淨利|EPS", txt):
            return "財務表·損益"
        return "財務表"
    return "數據表"


def _info_score(texts: list) -> float:
    t = " ".join(texts)
    n = max(len(t), 1)
    kw = sum(t.count(k) for k in _INFO_KW)
    digits = sum(ch.isdigit() for ch in t) / n
    short = sum(1 for x in texts if len(x) <= 18) / max(len(texts), 1)
    sent = t.count("。") + t.count(". ")
    return kw * 100.0 / n * 10 + digits * 3 + short * 2 - sent * 0.3


def _gutter(elems: list, W: float, min_n: int = 6) -> float | None:
    if len(elems) < min_n:
        return None
    cov = [0.0] * (int(W) + 2)
    for x0, x1, t, b in elems:
        for x in range(max(0, int(x0)), min(int(W), int(x1)) + 1):
            cov[x] += (b - t)
    lo, hi = int(0.2 * W), int(0.8 * W)
    thr = max(cov) * 0.02
    best, start = None, None
    for x in range(lo, hi + 2):
        if x <= hi and cov[x] <= thr:
            start = x if start is None else start
        elif start is not None:
            if x - start >= 8 and (best is None or x - start > best[1] - best[0]):
                best = (start, x)
            start = None
    if not best:
        return None
    g = (best[0] + best[1]) / 2
    left = sum(1 for e in elems if e[1] <= g)
    right = sum(1 for e in elems if e[0] >= g)
    return g if left >= 0.12 * len(elems) and right >= 0.12 * len(elems) else None


def analyze_page(pdf, pno: int, pdf_path: str, annual: bool, tabula_ok: bool) -> dict:
    page = pdf.pages[pno - 1]
    W, H = float(page.width), float(page.height)
    lines = _lines(page)
    tb = _table_boxes(page, annual)
    tboxes = [b for _, b in tb]
    figs = _figures(page, tboxes)

    def inside(l, boxes):
        return any(b[0] - 2 <= l["x0"] and l["x1"] <= b[2] + 2 and b[1] - 2 <= l["top"] and l["bottom"] <= b[3] + 2 for b in boxes)
    free = [l for l in lines if not inside(l, tboxes) and not inside(l, figs)]
    elems = [dict(l) for l in free]
    for (how, b) in tb:
        elems.append({"kind": "table", "how": how, "x0": b[0], "top": b[1], "x1": b[2], "bottom": b[3], "text": ""})
    for b in figs:
        inner = " ".join(l["text"] for l in lines if inside(l, [b]))[:200]
        elems.append({"kind": "figure", "x0": b[0], "top": b[1], "x1": b[2], "bottom": b[3], "text": inner})
    for e in elems:
        e["band"] = "H" if e["bottom"] <= 0.055 * H else ("B" if e["top"] >= 0.94 * H else "")
    top_cut = 0.12 * H if pno == 1 else 0.05 * H       # 首頁頂部常有跨欄大標題;年度頁表格可能緊貼頁頂
    core = [(e["x0"], e["x1"], e["top"], e["bottom"]) for e in elems if not e["band"] and (e["x1"] - e["x0"]) < 0.7 * W and e["top"] > top_cut]
    g = _gutter(core, W, min_n=2 if (annual and sum(1 for e in elems if e["kind"] == "table") >= 2) else 6)
    for e in elems:
        if e["band"]:
            e["zone"] = e["band"]
        elif g is None:
            e["zone"] = "F"
        elif e["x1"] <= g + 2:
            e["zone"] = "L"
        elif e["x0"] >= g - 2:
            e["zone"] = "R"
        else:
            e["zone"] = "F"
    blocks = []
    for z in ("H", "F", "L", "R", "B"):
        zs = sorted((e for e in elems if e["zone"] == z), key=lambda e: (e["top"], e["x0"]))
        cur = None
        for e in zs:
            if e["kind"] != "text":
                if cur:
                    blocks.append(cur)
                    cur = None
                blocks.append({"zone": z, "kind": e["kind"], "how": e.get("how", ""), "x0": e["x0"], "top": e["top"], "x1": e["x1"], "bottom": e["bottom"], "lines": [], "text": e.get("text", "")})
                continue
            same = cur and abs(cur["lines"][-1]["size"] - e["size"]) <= 0.6 and cur["lines"][-1]["bold"] == e["bold"] and (e["top"] - cur["lines"][-1]["bottom"]) <= 1.7 * max(e["size"], 6) and abs(cur["x0"] - e["x0"]) <= 40
            if same and not _BULLET_RX.match(e["text"]):
                cur["lines"].append(e)
                cur["x1"] = max(cur["x1"], e["x1"])
                cur["bottom"] = max(cur["bottom"], e["bottom"])
            else:
                if cur:
                    blocks.append(cur)
                cur = {"zone": z, "kind": "text", "x0": e["x0"], "top": e["top"], "x1": e["x1"], "bottom": e["bottom"], "lines": [e]}
        if cur:
            blocks.append(cur)
    for b in blocks:
        if b["kind"] == "text":
            b["text"] = "".join((("" if (i and re.search(r"[\u4e00-\u9fff]$", b["lines"][i - 1]["text"]) and re.match(r"[\u4e00-\u9fff]", l["text"])) else (" " if i else "")) + l["text"]) for i, l in enumerate(b["lines"]))
            b["size"] = max(l["size"] for l in b["lines"])
            b["bold"] = sum(1 for l in b["lines"] if l["bold"]) * 2 >= len(b["lines"])
    roles = {"H": "HEADER", "B": "FOOTER", "F": "BODY"}
    if g is not None:
        sl = _info_score([b.get("text", "") for b in blocks if b["zone"] == "L"])
        sr = _info_score([b.get("text", "") for b in blocks if b["zone"] == "R"])
        roles.update({"L": "INFO" if sl > sr + 0.5 else "BODY", "R": "INFO" if sr > sl + 0.5 else "BODY"})
        if roles["L"] == roles["R"] == "BODY" and pno == 1:
            nl = sum(len(b.get("text", "")) for b in blocks if b["zone"] == "L")
            nr = sum(len(b.get("text", "")) for b in blocks if b["zone"] == "R")
            roles["R" if nr < nl else "L"] = "INFO"
    else:
        roles.update({"L": "BODY", "R": "BODY"})
    counters = defaultdict(int)
    tno = 0
    for b in sorted(blocks, key=lambda b: ("HFLRB".index(b["zone"]), b["top"], b["x0"])):
        counters[b["zone"]] += 1
        b["role"] = roles.get(b["zone"], "BODY")
        b["id"] = "P%d·%s·%02d" % (pno, b["zone"], counters[b["zone"]])
        if b["kind"] == "table":
            tno += 1
            b["id"] += "·T%d" % tno
            t = _extract_table(page, (b["x0"], b["top"], b["x1"], b["bottom"]), b.get("how") or "lines", pdf_path, pno, tabula_ok)
            b.update(rows=t["rows"], engine=t["engine"], fixes=t["fixes"], alts=t.get("alts", []))
            b["sub"] = _table_cat(t["rows"], b["role"])
            b["text"] = " | ".join(" ".join(r) for r in t["rows"][:3])
        elif b["kind"] == "figure":
            b["sub"] = "圖"
        b["bbox_pct"] = [round(100 * b["x0"] / W, 1), round(100 * b["top"] / H, 1), round(100 * (b["x1"] - b["x0"]) / W, 1), round(100 * (b["bottom"] - b["top"]) / H, 1)]
    return {"page": pno, "W": W, "H": H, "gutter": round(g, 1) if g else None, "roles": roles, "blocks": sorted(blocks, key=lambda b: ("HFLRB".index(b["zone"]), b["top"], b["x0"])), "n_lines": len(lines)}


def _hierarchy(pages: list) -> dict:
    cnt = Counter()
    for pg in pages:
        for b in pg["blocks"]:
            if b["kind"] == "text" and b["role"] not in ("HEADER", "FOOTER"):
                for l in b["lines"]:
                    cnt[(round(l["size"] * 2) / 2, l["bold"])] += len(l["text"])
    if not cnt:
        return {"body": None, "levels": {}, "styles": []}
    body = max(cnt.items(), key=lambda kv: kv[1])[0]
    total = sum(cnt.values())
    heads = sorted([s for s, n in cnt.items() if (s[0] >= body[0] + 1.0 or (s[1] and not body[1] and s[0] >= body[0])) and n <= 0.35 * total], key=lambda s: (-s[0], not s[1]))
    levels = {s: "H%d" % (i + 1) for i, s in enumerate(heads[:4])}
    styles = [{"size": s[0], "bold": s[1], "chars": n, "level": levels.get(s, "內文" if s == body else ("註" if s[0] < body[0] - 0.4 else "內文"))} for s, n in sorted(cnt.items(), key=lambda kv: (-kv[0][0], not kv[0][1]))]
    return {"body": {"size": body[0], "bold": body[1]}, "levels": {"%s|%s" % k: v for k, v in levels.items()}, "styles": styles}


def _text_subcat(b: dict, hier: dict) -> str:
    t = b.get("text", "")
    if b["role"] == "INFO":
        return "資訊"
    if b["role"] in ("HEADER", "FOOTER"):
        return "頁首" if b["role"] == "HEADER" else "頁尾/免責"
    if _CAPTION_RX.match(t):
        return "圖表標題"
    if _NOTE_RX.match(t):
        return "註/來源"
    key = "%s|%s" % (round(b["size"] * 2) / 2, b["bold"])
    lv = hier["levels"].get(key)
    if lv and len(t) <= 120:
        return lv + " 標題"
    if _BULLET_RX.match(t):
        return "重點條列"
    body = hier.get("body") or {}
    if body and b["size"] < body.get("size", 0) - 0.4:
        return "註"
    return "內文"


def _main_title(p1: dict, hier: dict, f: dict, book: dict) -> dict:
    H = p1["H"]
    cands = []
    for b in p1["blocks"]:
        if b["kind"] != "text" or b["role"] in ("HEADER", "FOOTER", "INFO") or b["top"] > 0.55 * H:
            continue
        t = b["text"].strip()
        if not (4 <= len(t) <= 90) or re.search(r"[。．]$|\.\s*$", t) or "。" in t[:-1]:
            continue
        if f.get("code") and re.fullmatch(r"[\W\d]*%s[\W\d]*(TT)?" % re.escape(f["code"]), t):
            continue
        if re.fullmatch(r"[\d/\-\.\s年月日]+", t):
            continue
        cands.append((b["size"], b["bold"], -b["top"], t, b["id"]))
    if not cands:
        return {"text": "", "id": "", "why": "首頁上半部沒有大字無句號的單句"}
    s, bold, nt, t, bid = max(cands)
    body = (hier.get("body") or {}).get("size") or 0
    return {"text": t, "id": bid, "size": s, "bold": bold, "why": "字級 %.1f(內文 %.1f)%s" % (s, body, " · 粗體" if bold else "")}


def _annual_pages(pdf, max_scan: int = 40) -> list:
    sc = []
    for i, pg in enumerate(pdf.pages[:max_scan], 1):
        try:
            t = pg.extract_text() or ""
        except Exception:  # noqa: BLE001
            continue
        if not t:
            continue
        yrs = len(set(_YEAR_RX.findall(t)))
        fin = sum(1 for k in _FIN_KW if k.lower() in t.lower())
        dens = sum(ch.isdigit() for ch in t) / max(len(t), 1)
        s = yrs * 1.0 + fin * 1.5 + dens * 20
        if yrs >= 3 and fin >= 2 and dens >= 0.15:
            sc.append((s, i))
    return [i for _, i in sorted(sc, reverse=True)[:6]]


def layout_one(path: Path, master: dict, book: dict, tabula_ok: bool, deep=None) -> dict:
    import pdfplumber
    t0 = time.time()
    out = {"file": path.name, "path": str(path), "lamp": "GRAY", "notes": []}
    f = _resolve("fname_parse")(path.name, master, book, path.stat().st_mtime, None)
    out["id"] = {k: f.get(k, "") for k in ("code", "yf", "bbg", "name", "broker", "date", "date_src")}
    try:
        pdf = pdfplumber.open(str(path))
    except Exception as exc:  # noqa: BLE001
        out.update(lamp="RED", notes=["開不了:%s" % str(exc)[:80]])
        return out
    with pdf:
        n = len(pdf.pages)
        out["pages_total"] = n
        if not n:
            out["notes"].append("0 頁")
            return out
        p1t = pdf.pages[0].extract_text() or ""
        if len(p1t.strip()) < 40:
            out.update(lamp="GRAY", notes=["首頁無文字層(掃描件 → OCR 閘)"])
            return out
        conf = {}
        if f.get("code"):
            conf["代號"] = bool(re.search(r"(?<!\d)%s(?!\d)" % re.escape(f["code"]), p1t))
        if f.get("name"):
            conf["名稱"] = f["name"].replace("-KY", "") in p1t
        out["confirm"] = conf
        ann = [p for p in _annual_pages(pdf) if p != 1]
        pages = [analyze_page(pdf, 1, str(path), annual=False, tabula_ok=tabula_ok)] + [analyze_page(pdf, p, str(path), annual=True, tabula_ok=tabula_ok) for p in ann]
    hier = _hierarchy(pages)
    for pg in pages:
        for b in pg["blocks"]:
            if b["kind"] == "text":
                b["sub"] = _text_subcat(b, hier)
            b["eng394"] = _eng_subcat(b["kind"], b.get("text", "")[:300])
    title = _main_title(pages[0], hier, f, book)
    for b in pages[0]["blocks"]:
        if b["id"] == title.get("id"):
            b["sub"] = "主標題"
    info = {}
    if deep:
        try:
            os.environ["VIA_NO_NET"] = "1"
            r = deep(path)
            info = {k: v for k, v in (r or {}).items() if isinstance(v, (str, int, float)) and v not in ("", None) and re.search(r"(?i)rating|target|tp|analyst|email|tel|close|price|評等|目標", k)}
        except Exception as exc:  # noqa: BLE001
            info = {"_deepread": "沒跑:%s" % str(exc)[:60]}
    p1 = pages[0]
    n_tables = sum(1 for pg in pages for b in pg["blocks"] if b["kind"] == "table")
    n_fix = sum(len(b.get("fixes", [])) for pg in pages for b in pg["blocks"] if b["kind"] == "table")
    split = "INFO" in p1["roles"].values() and "BODY" in p1["roles"].values()
    is_stock = bool(f.get("code"))
    out.update(pages=pages, hier=hier, title=title, info=info, annual=ann, n_tables=n_tables, n_fixes=n_fix, split=split, secs=round(time.time() - t0, 1))
    y = []
    if is_stock and not all(conf.values()):
        y.append("首頁沒對到" + "/".join(k for k, v in conf.items() if not v))
    if not title["text"]:
        y.append("主標題沒找到")
    if not split:
        y.append("首頁本文/資訊區沒切開")
    if is_stock and not ann:
        y.append("年度財報頁沒找到")
    if is_stock and ann and not n_tables:
        y.append("年度財報頁沒抽到表")
    out["notes"] = y
    out["lamp"] = "YELLOW" if y else "GREEN"
    return out


# ───────── HTML ─────────
_ZC = {"H": "#e0f2fe", "F": "#f5f5f4", "L": "#dcfce7", "R": "#fef3c7", "B": "#ede9fe"}
_KC = {"text": "#93c5fd", "table": "#f59e0b", "figure": "#a78bfa"}
_L = {"GREEN": "var(--lamp-green,#16a34a)", "YELLOW": "var(--lamp-yellow,#eab308)", "RED": "var(--lamp-red,#dc2626)", "GRAY": "var(--lamp-gray,#9ca3af)"}
_CSS = ("body{font-family:'Microsoft JhengHei UI','Segoe UI',Arial;font-size:12.5px;color:#1f2937;background:var(--bg,#fafafa);margin:0;padding:12px}h1{font-size:15px;margin:0 0 4px}.meta{color:#6b7280;font-size:11px}"
        ".lp{display:inline-block;width:11px;height:11px;border-radius:50%;vertical-align:middle;margin-right:3px}.lp.RED{animation:bl 2.4s ease-in-out infinite}@keyframes bl{0%,100%{opacity:1}50%{opacity:.25}}"
        ".idbar{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;margin-bottom:8px}.idbar .tt{font-size:19px;font-weight:700;margin:4px 0}.chip{display:inline-block;background:#f3f4f6;border-radius:10px;padding:1px 8px;margin:0 4px 2px 0;font-size:11.5px}"
        ".two{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:10px}@media(max-width:900px){.two{grid-template-columns:1fr}}.pane{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px}.pane h2{font-size:13px;margin:0 0 6px;color:#374151}"
        ".blk{margin:4px 0;padding:3px 6px;border-left:3px solid #e5e7eb}.blk .bid{color:#9ca3af;font-size:10px;margin-right:6px;font-family:Consolas,monospace}.blk .sub{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:4px;padding:0 4px;font-size:10px;margin-right:4px}"
        ".h1{font-size:17px;font-weight:700}.h2{font-size:15px;font-weight:700}.h3{font-size:13.5px;font-weight:700}.h4{font-size:13px;font-weight:600}.note{color:#6b7280;font-size:11px}"
        "table.t{border-collapse:collapse;margin:4px 0;font-size:11.5px}table.t td{border:1px solid #e5e7eb;padding:1px 5px;text-align:right}table.t td:first-child{text-align:left}table.t tr:first-child td{background:#f9fafb;font-weight:600}"
        ".pg{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;margin-top:10px}.map{position:relative;border:1px solid #d1d5db;background:#fff;width:210px;flex:none}.map div{position:absolute;border:1px solid #6b7280;font-size:8px;overflow:hidden;opacity:.85}"
        ".row{display:flex;gap:10px;align-items:flex-start}.hier td,.hier th{border:1px solid #e5e7eb;padding:1px 6px}.hier{border-collapse:collapse;font-size:11px}.yel{color:#92400e}")


def _rows_html(rows: list) -> str:
    return "<table class='t'>" + "".join("<tr>" + "".join("<td>%s</td>" % html.escape(c) for c in r) + "</tr>" for r in rows[:60]) + "</table>"


def _block_html(b: dict) -> str:
    sub = b.get("sub", "")
    tag = "<span class='bid'>%s</span><span class='sub'>%s</span>%s" % (html.escape(b["id"]), html.escape(sub), ("<span class='sub' style='background:#fef3c7;color:#92400e'>ENG394:%s</span>" % html.escape(b["eng394"])) if b.get("eng394") else "")
    if b["kind"] == "table":
        return "<div class='blk' style='border-color:%s'>%s<span class='note'>%s · %d×%d · %s</span>%s</div>" % (_KC["table"], tag, html.escape(b.get("engine", "")), len(b.get("rows", [])), max((len(r) for r in b.get("rows", [])), default=0), html.escape(" ".join(b.get("fixes", [])) or "無修補"), _rows_html(b.get("rows", [])))
    if b["kind"] == "figure":
        return "<div class='blk' style='border-color:%s'>%s<span class='note'>[圖]</span> %s</div>" % (_KC["figure"], tag, html.escape(b.get("text", "")[:160]))
    cls = {"主標題": "h1", "H1 標題": "h1", "H2 標題": "h2", "H3 標題": "h3", "H4 標題": "h4", "註": "note", "註/來源": "note", "頁尾/免責": "note"}.get(sub, "")
    return "<div class='blk' style='border-color:%s'>%s<span class='%s'>%s</span></div>" % (_KC["text"], tag, cls, html.escape(b.get("text", "")))


def _map_html(pg: dict) -> str:
    h = round(210 * pg["H"] / pg["W"]) if pg["W"] else 297
    boxes = "".join("<div title='%s · %s' style='left:%s%%;top:%s%%;width:%s%%;height:%s%%;background:%s'>%s</div>" % (html.escape(b["id"]), html.escape(b.get("sub", "")), b["bbox_pct"][0], b["bbox_pct"][1], max(b["bbox_pct"][2], 0.8), max(b["bbox_pct"][3], 0.8), _KC.get(b["kind"], "#ddd") if b["kind"] != "text" else _ZC.get(b["zone"], "#eee"), html.escape(b["id"].split("·", 1)[1])) for b in pg["blocks"])
    gl = ("<div style='left:%s%%;top:0;width:0;height:100%%;border-left:1px dashed #dc2626;background:none'></div>" % round(100 * pg["gutter"] / pg["W"], 1)) if pg.get("gutter") else ""
    return "<div class='map' style='height:%dpx'>%s%s</div>" % (h, boxes, gl)


def _file_html(r: dict) -> str:
    e = html.escape
    idd, title = r.get("id", {}), r.get("title", {})
    conf = r.get("confirm", {})
    chips = "".join("<span class='chip'>%s</span>" % e(x) for x in [("代號 %s" % idd.get("code")) if idd.get("code") else "", idd.get("yf", ""), idd.get("bbg", ""), ("券商 %s" % idd.get("broker")) if idd.get("broker") else "", ("報告日 %s" % idd.get("date")) if idd.get("date") else ""] if x)
    chips += "".join("<span class='chip'>首頁%s %s</span>" % (e(k), "✓" if v else "✗") for k, v in conf.items())
    pages = r.get("pages", [])
    p1 = pages[0] if pages else {"blocks": [], "roles": {}}
    body = [b for b in p1["blocks"] if b["role"] == "BODY"]
    info = [b for b in p1["blocks"] if b["role"] in ("INFO", "HEADER", "FOOTER")]
    info_kv = "".join("<div class='blk'><span class='sub'>deepread</span>%s:%s</div>" % (e(k), e(str(v))) for k, v in r.get("info", {}).items())
    hier = r.get("hier", {})
    hrows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (s["size"], "粗" if s["bold"] else "", e(s["level"]), s["chars"]) for s in hier.get("styles", [])[:12])
    ann = ""
    for pg in pages[1:]:
        ann += "<div class='pg'><h2 style='font-size:13px;margin:0 0 6px'>年度財報頁 P%d · 左右切 %s · 角色 %s</h2><div class='row'>%s<div style='flex:1;min-width:0'>%s</div></div></div>" % (pg["page"], ("x=%s" % pg["gutter"]) if pg.get("gutter") else "無(單欄)", e(" ".join("%s=%s" % kv for kv in pg["roles"].items() if kv[0] in "LRF")), _map_html(pg), "".join(_block_html(b) for b in pg["blocks"] if b["role"] not in ("HEADER", "FOOTER")))
    head = "<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>%s</title><style>%s</style></head><body>" % (e(r["file"]), _CSS)
    return head + ("<div class='idbar'><div class='meta'><i class='lp %s' style='background:%s'></i>%s · %s 頁 · 年度財報頁 %s · 表 %d · 修補 %d · %ss · %s</div><div style='font-size:15px;font-weight:700'>%s</div><div class='tt'>%s</div>%s<div class='meta yel'>%s</div></div>"
                   "<div class='two'><div class='pane'><h2>本文(首頁 BODY · 依字級粗細分層)</h2>%s</div><div class='pane'><h2>資訊區(首頁 INFO · 頁首 · 頁尾)</h2>%s%s<h2 style='margin-top:10px'>字型階層</h2><table class='hier'><tr><th>字級</th><th>粗</th><th>層級</th><th>字數</th></tr>%s</table><div class='row' style='margin-top:8px'>%s</div></div></div>%s"
                   "<div class='meta' style='margin-top:8px'>編號 = P頁·區(H 頁首 · F 跨欄 · L 左 · R 右 · B 頁尾)·序號[·T表號];先左右切(找欄間空白帶)再上下切(行距與樣式分段);表格:pdfplumber 格線 → 文字分欄 → 座標分欄 → tabula(有 Java 才用)取最佳後修補。</div></body></html>") % (
        r.get("lamp", "GRAY"), _L.get(r.get("lamp", "GRAY")), e(r["file"]), r.get("pages_total", "?"), e(",".join("P%d" % p for p in r.get("annual", [])) or "無"), r.get("n_tables", 0), r.get("n_fixes", 0), r.get("secs", ""),
        e(title.get("why", "")), e("%s %s" % (idd.get("name", ""), ("(%s)" % idd["code"]) if idd.get("code") else "")), e(title.get("text", "") or "(主標題未找到)"), chips, e(";".join(r.get("notes", []))),
        "".join(_block_html(b) for b in body) or "<div class='note'>—</div>", info_kv, "".join(_block_html(b) for b in info), hrows, _map_html(p1) if pages else "", ann)


def layout_run(d: Path, max_files: int = 0, only: str = "", recursive: bool = False) -> dict:
    now = datetime.datetime.now()
    out_dir = _rep() / "layout"
    out_dir.mkdir(parents=True, exist_ok=True)
    master, _ = (_resolve("_load_roster_v154") or (lambda u=True: ({}, [])))(True)
    book, _ = (_resolve("load_brokers_v154") or (lambda: ({}, [])))()
    mf = _rep() / "prep" / "PREP_MANIFEST_latest.json"
    files = []
    if mf.exists():
        try:
            for r in json.loads(mf.read_text(encoding="utf-8")).get("rows", []):
                if r.get("read_pdf") and Path(r["read_pdf"]).exists() and str(Path(r.get("path", "")).parent).lower().startswith(str(d).lower()):
                    files.append((r["file"], Path(r["read_pdf"])))
        except ValueError:
            pass
    if not files:
        it = d.rglob("*.pdf") if recursive else d.glob("*.pdf")
        files = [(p.name, p) for p in sorted(it)]
    if only:
        files = [x for x in files if only.lower() in x[0].lower()]
    if max_files:
        files = files[:max_files]
    tabula_ok = bool(shutil.which("java")) and importlib.util.find_spec("tabula") is not None
    deep = _resolve("deepread_one")
    rows = []
    for i, (name, pth) in enumerate(files, 1):
        try:
            r = layout_one(pth, master, book, tabula_ok, deep)
        except Exception as exc:  # noqa: BLE001
            r = {"file": name, "path": str(pth), "lamp": "RED", "notes": ["%s:%s" % (type(exc).__name__, str(exc)[:100])]}
        r["file"] = name
        page = out_dir / ("%s_%s.html" % (hashlib.sha256(str(pth).encode("utf-8")).hexdigest()[:8], re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", Path(name).stem)[:60]))
        if r.get("pages"):
            page.write_text(_file_html(r), encoding="utf-8")
            r["html"] = str(page)
        (out_dir / (page.stem + ".json")).write_text(json.dumps(r, ensure_ascii=False, default=str), encoding="utf-8")
        rows.append({k: r.get(k) for k in ("file", "lamp", "notes", "html", "annual", "n_tables", "n_fixes", "split", "secs", "pages_total")} | {"id": r.get("id", {}), "title": (r.get("title") or {}).get("text", ""), "confirm": r.get("confirm", {}), "levels": len((r.get("hier") or {}).get("levels", {})), "eng394": sum(1 for pg in r.get("pages", []) for b in pg["blocks"] if b.get("eng394"))})
        print("  [進度] %d/%d · %s · %s" % (i, len(files), r.get("lamp"), name[:50]), flush=True)
    e = eng394()
    s = {"ts": now.isoformat(timespec="seconds"), "dir": str(d), "files": len(rows), "lamps": dict(Counter(r["lamp"] for r in rows)), "titles": sum(1 for r in rows if r["title"]), "split": sum(1 for r in rows if r.get("split")),
         "annual": sum(1 for r in rows if r.get("annual")), "tables": sum(r.get("n_tables") or 0 for r in rows), "fixes": sum(r.get("n_fixes") or 0 for r in rows), "eng394": e.get("file") or "無", "eng394_ok": bool(e.get("subcat")), "eng394_err": e.get("err", ""),
         "rulebook": e.get("rulebook", ""), "tabula": tabula_ok, "deepread": bool(deep)}
    idx = out_dir / "LAYOUT_MATRIX_latest.html"
    idx.write_text(_index_html(s, rows), encoding="utf-8")
    (out_dir / "LAYOUT_latest.json").write_text(json.dumps({"summary": s, "rows": rows}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    lamp = "RED" if s["lamps"].get("RED") and not s["lamps"].get("GREEN") else ("YELLOW" if s["lamps"].get("YELLOW") or s["lamps"].get("RED") else ("GREEN" if rows else "GRAY"))
    return {"verb": "layout", "summary": s, "rows": rows, "html": str(idx), "lamp": lamp}


def _index_html(s: dict, rows: list) -> str:
    e = html.escape
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2, "GRAY": 3}
    trs = "".join("<tr data-l='%s'><td><i class='lp %s' style='background:%s'></i></td><td class='f'>%s</td><td>%s<div class='meta'>%s</div></td><td>%s</td><td class='tt'>%s</td><td>%s</td><td>%s</td><td style='text-align:right'>%s</td><td style='text-align:right'>%s</td><td style='text-align:right'>%s</td><td style='text-align:right'>%s</td><td class='meta'>%s</td></tr>" % (
        r["lamp"], r["lamp"], _L.get(r["lamp"]), ("<a href='%s'>%s</a>" % (Path(r["html"]).name, e(r["file"]))) if r.get("html") else e(r["file"]),
        e("%s %s" % (r["id"].get("name", ""), r["id"].get("code", ""))), e(" ".join("%s%s" % (k, "✓" if v else "✗") for k, v in (r.get("confirm") or {}).items())), e(r["id"].get("broker", "")), e(r.get("title", "") or "—"),
        "左右切 ✓" if r.get("split") else "—", e(",".join("P%d" % p for p in (r.get("annual") or [])) or "—"), r.get("n_tables") or 0, r.get("n_fixes") or 0, r.get("levels") or 0, r.get("eng394") or 0, e(";".join(r.get("notes") or [])))
                  for r in sorted(rows, key=lambda x: (order.get(x["lamp"], 9), x["file"])))
    css = _CSS + "table.m{border-collapse:collapse;width:100%;background:#fff}table.m th,table.m td{border:1px solid #eceff3;padding:2px 5px;text-align:left;vertical-align:top}table.m th{background:#111827;color:#fff;position:sticky;top:0}td.f{max-width:240px;word-break:break-all}td.tt{max-width:280px}.bar button{font-size:11px;margin-right:4px;padding:2px 8px;border:1px solid #d1d5db;background:#fff;border-radius:6px;cursor:pointer}"
    js = "function f(l){document.querySelectorAll('tbody tr').forEach(function(t){t.style.display=(!l||t.dataset.l===l)?'':'none'})}"
    head = "<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VRN 版面矩陣</title><style>" + css + "</style><script>" + js + "</script></head><body>"
    return head + ("<h1>VRN 版面 · 首頁本文/資訊區 · 年度財報頁表格 · 字型階層</h1><div class='meta'>%s · %s · 檔 %d · 燈 %s · 主標題 %d · 首頁左右切 %d · 有年度財報頁 %d · 表 %d · 修補 %d</div>"
                   "<div class='meta'>版面引擎 ENG394:%s · 子分類 %s%s · 規則冊 %s · tabula %s · deepread(v0119 資訊區抽取)%s</div>"
                   "<div class='bar' style='margin:6px 0'><button onclick=\"f('')\">全部</button><button onclick=\"f('YELLOW')\">只看黃</button><button onclick=\"f('GREEN')\">只看綠</button><button onclick=\"f('RED')\">只看紅</button><button onclick=\"f('GRAY')\">只看灰</button></div>"
                   "<div style='overflow-x:auto'><table class='m'><thead><tr><th>燈</th><th>檔(點開看版面)</th><th>股票(首頁確認)</th><th>券商</th><th>主標題</th><th>首頁</th><th>年度財報頁</th><th>表</th><th>修補</th><th>標題層</th><th>ENG394</th><th>備註</th></tr></thead><tbody>%s</tbody></table></div></body></html>") % (
        e(s["ts"]), e(s["dir"]), s["files"], e(" ".join("%s=%d" % kv for kv in sorted(s["lamps"].items()))), s["titles"], s["split"], s["annual"], s["tables"], s["fixes"],
        e(s["eng394"]), "已接" if s["eng394_ok"] else "未接", (" · " + e(s["eng394_err"])) if s["eng394_err"] else "", e(s["rulebook"] or "無"), "有" if s["tabula"] else "無(缺 Java 或 tabula-py)", "有" if s["deepread"] else "無", trs)


def _print_layout(o: dict) -> None:
    s = o["summary"]
    print("[計] VRN layout · 檔 %d · 燈 %s · 主標題 %d · 首頁左右切 %d · 有年度財報頁 %d · 表 %d · 修補 %d · %s" % (s["files"], " ".join("%s=%d" % kv for kv in sorted(s["lamps"].items())), s["titles"], s["split"], s["annual"], s["tables"], s["fixes"], o["lamp"]))
    print("[計] 版面引擎 ENG394 %s · 子分類 %s%s · 規則冊 %s · tabula %s · deepread %s" % (s["eng394"], "已接" if s["eng394_ok"] else "未接", (" · " + s["eng394_err"]) if s["eng394_err"] else "", s["rulebook"] or "無", "有" if s["tabula"] else "無", "有" if s["deepread"] else "無"))
    for k, v in Counter(n for r in o["rows"] for n in (r.get("notes") or [])).most_common(10):
        print("  [%s] %s · %d 檔" % ("RED" if k.startswith(("開不了", "Error", "Type", "Value", "Key")) else "YEL", k, v))
    print("  [U/I] %s" % o["html"])
    print("NEXT: %s" % ("版面全綠 → 表格接 FinLexicon 標準列" if o["lamp"] == "GREEN" else "點開黃的檔看版面圖:主標題/左右切/年度頁/表 哪一層錯,貼檔名給 AI"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    rec = "--recursive" in args
    if args[:1] in (["fname"], ["prep"], ["layout"]) and len(args) >= 2 and "--dir" not in args and Path(args[-1]).is_dir():
        args = args[:-1] + ["--dir", args[-1]]
    if args[:1] in (["fname"], ["prep"]) and not rec:
        cfg = (_resolve("config_get") or (lambda: {}))()
        d = _TopPath(opt("--dir") or cfg.get("input_dir") or r"C:\測試樣本報告")
        if args[:1] == ["fname"]:
            o = _resolve("fname_run")(d, use_vdf=("--no-vdf" not in args))
            _resolve("_print_fname")(o)
            n_sub = sum(1 for p in Path(d).iterdir() if p.is_dir()) if Path(d).is_dir() else 0
            if n_sub:
                print("  [注] 只掃最上層;子資料夾 %d 個未掃(加 --recursive 才掃)" % n_sub)
            return 0
        args = [a for a in args if a != "--dir" and a != opt("--dir")]
        o = _resolve("prep")(d, use_vdf=("--no-vdf" not in args), max_pages=int(opt("--max-pages", "60") or 60), workers=int(opt("--workers", "4") or 4), raster_all=("--raster-all" in args))
        _resolve("_print_prep")(o)
        return 0
    if args[:1] == ["layout"]:
        cfg = (_resolve("config_get") or (lambda: {}))()
        o = layout_run(Path(opt("--dir") or cfg.get("input_dir") or r"C:\測試樣本報告"), int(opt("--max", "0") or 0), opt("--only", "") or "", rec)
        _print_layout(o)
        return 0
    if args[:1] == ["ui"]:
        rc = PRIOR.main(args)
        page = _rep() / "VRN_UI_latest.html"
        if page.exists():
            h = page.read_text(encoding="utf-8", errors="replace")
            if "via://VRN/layout" not in h:
                h = h.replace("只判檔名(秒級)</a></div>", "只判檔名(秒級)</a><a href='via://VRN/layout' style='display:inline-block;padding:4px 10px;border:1px solid var(--border,#e0e0e0);border-radius:6px;text-decoration:none;margin-left:6px'>② 版面(首頁 · 年度財報頁)</a></div>", 1)
                page.write_text(h, encoding="utf-8")
        return rc
    return PRIOR.main(args)


def _mk_report_pdf(path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    cjk = "MSung-Light"
    for fp in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", r"C:\Windows\Fonts\msjh.ttc", r"C:\Windows\Fonts\mingliu.ttc"):
        if Path(fp).exists():
            try:
                from reportlab.pdfbase.ttfonts import TTFont
                pdfmetrics.registerFont(TTFont("CJKT", fp, subfontIndex=0))
                cjk = "CJKT"
                break
            except Exception:  # noqa: BLE001
                continue
    if cjk == "MSung-Light":
        pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
    W, H = A4
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica", 7)
    c.drawString(40, H - 28, "KGI Research | Taiwan Equity | 2026-09-17")
    c.setFont(cjk, 20)
    c.drawString(40, H - 80, "健策 3653:液冷題材發酵 營運動能強勁")
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, H - 120, "Investment highlights")
    c.setFont("Helvetica", 9.5)
    y = H - 140
    for i in range(14):
        c.drawString(40, y, "Jentech (3653 TT) benefits from liquid cooling adoption across AI servers, line %d." % i)
        y -= 13
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, y - 10, "Risks")
    c.setFont("Helvetica", 9.5)
    y -= 30
    for i in range(6):
        c.drawString(40, y, "- Customer concentration and pricing pressure could weigh on margins %d." % i)
        y -= 13
    c.setFont("Helvetica", 8)
    yy = H - 120
    for k, v in (("Rating", "Buy"), ("Target price", "NT$1,200"), ("Close", "NT$980"), ("Market cap", "NT$120bn"), ("Bloomberg", "3653 TT"), ("Analyst", "Amy Wang"), ("Email", "amy.wang@kgi.com"), ("Tel", "02-2181-8888")):
        c.drawString(420, yy, "%s: %s" % (k, v))
        yy -= 12
    t = Table([["Key data", "2025A", "2026F"], ["EPS", "45.2", "58.1"], ["P/E", "21.7", "16.9"]], colWidths=[50, 40, 40])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("FONT", (0, 0), (-1, -1), "Helvetica", 7)]))
    t.wrapOn(c, W, H)
    t.drawOn(c, 420, yy - 70)
    c.setFont("Helvetica", 6)
    c.drawString(40, 30, "Disclaimer: this report is for information only. Please see the last page for important disclosures.")
    c.showPage()
    c.setFont("Helvetica", 10)
    for i in range(30):
        c.drawString(40, H - 60 - i * 14, "Company background and industry discussion paragraph %d without numbers." % i)
    c.showPage()
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, H - 70, "Financial summary")
    is_rows = [["Income statement", "2023A", "2024A", "2025F", "2026F"], ["Revenue", "12,345", "15,678", "19,012", "23,456"], ["Gross profit", "4,321", "5,678", "7,012", "8,765"], ["Operating income", "2,345", "3,210", "4,321", "5,432"], ["Net income", "1,876", "2,654", "3,456", "4,321"], ["EPS", "15.2", "21.5", "28.0", "35.1"]]
    bs_rows = [["Balance sheet", "2023A", "2024A", "2025F", "2026F"], ["Cash", "3,210", "4,321", "5,432", "6,543"], ["Receivables", "2,100", "2,500", "3,000", "3,600"], ["Total assets", "20,000", "24,000", "29,000", "35,000"], ["Total equity", "12,000", "14,500", "17,800", "21,900"]]
    for rows, x in ((is_rows, 40), (bs_rows, 310)):
        t = Table(rows, colWidths=[80, 42, 42, 42, 42])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("FONT", (0, 0), (-1, -1), "Helvetica", 7.5)]))
        t.wrapOn(c, W, H)
        t.drawOn(c, x, H - 200)
    v_rows = [["Valuation", "2023A", "2024A", "2025F", "2026F"], ["P/E (x)", "64.5", "45.6", "35.0", "27.9"], ["P/B (x)", "10.1", "8.4", "6.9", "5.6"], ["ROE (%)", "15.6", "18.3", "19.4", "19.7"]]
    t = Table(v_rows, colWidths=[120, 90, 90, 90, 90])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("FONT", (0, 0), (-1, -1), "Helvetica", 7.5)]))
    t.wrapOn(c, W, H)
    t.drawOn(c, 40, H - 340)
    c.showPage()
    c.save()


def selftest() -> int:
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

    td = Path(tempfile.mkdtemp(prefix="vrnlay-"))
    home = td / "functional modules" / "VRN"
    (home / "SSOT").mkdir(parents=True)
    (home / "knowledge").mkdir()
    rep = td / "VIA_Reports" / "vrn"
    inp = td / "inbox"
    (inp / "sub").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_VDF_HOME", "VIA_VRN_MASTER_LISTS")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(rep), "VIA_VDF_HOME": str(td / "nope")})
    (home / "VRN_TWRoster_Offline_v0100.json").write_text(json.dumps({"rows": [{"code": "3653", "name": "健策", "market": "上市"}]}, ensure_ascii=False), encoding="utf-8")
    (home / "knowledge" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": {"凱基": {"abbr": "KGI", "aliases": ["凱基", "凱基投顧", "KGI"]}}}, ensure_ascii=False), encoding="utf-8")
    (home / "VRN_ENG394_LayoutRestore_v0102.py").write_text("def _subcat(text):\n    return 'FIN' if any(y in str(text) for y in ('2024A', '2025F')) else 'TXT'\n", encoding="utf-8")
    pdfp = inp / "凱基投顧_3653 健策_向子慧_20260917.pdf"
    _mk_report_pdf(pdfp)
    (inp / "sub" / "hidden_9999.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    o = layout_run(inp)
    r = json.loads(Path(o["html"]).with_name("LAYOUT_latest.json").read_text(encoding="utf-8"))["rows"][0]
    full = json.loads((Path(r["html"]).with_suffix(".json")).read_text(encoding="utf-8"))
    p1 = full["pages"][0]
    chk("① 只掃最上層(子夾 hidden 不進)· 首頁確認代號 3653 / 名稱 健策 · 券商 KGI", o["summary"]["files"] == 1 and full["confirm"] == {"代號": True, "名稱": True} and full["id"]["broker"] == "KGI")
    chk("② 主標題 = 最大字級無句號的單句「健策 3653:液冷題材發酵 營運動能強勁」", full["title"]["text"].startswith("健策 3653") and "液冷" in full["title"]["text"])
    chk("③ 首頁先左右切(欄間空白帶)· 左 = BODY · 右 = INFO(關鍵詞密度)· 頁首 / 頁尾分出", p1["gutter"] and p1["roles"]["L"] == "BODY" and p1["roles"]["R"] == "INFO" and any(b["zone"] == "H" for b in p1["blocks"]) and any(b["zone"] == "B" for b in p1["blocks"]))
    heads = [b for b in p1["blocks"] if b.get("sub", "").endswith("標題") and b["role"] == "BODY"]
    chk("④ 字型階層:Investment highlights / Risks = 標題層 · 長段 = 內文 · 條列 = 重點條列", any("Investment highlights" in b["text"] for b in heads) and any(b.get("sub") == "內文" for b in p1["blocks"]) and any(b.get("sub") == "重點條列" for b in p1["blocks"]))
    chk("⑤ 資訊區有表(資訊表)· deepread 不在也不壞", any(b["kind"] == "table" and b["role"] == "INFO" and b["sub"] == "資訊表" for b in p1["blocks"]))
    ann = full["pages"][1:]
    tbs = [b for pg in ann for b in pg["blocks"] if b["kind"] == "table"]
    cats = sorted(b["sub"] for b in tbs)
    chk("⑥ 年度財報頁 = P3(P2 純文字不選)· 左右切 · 損益(左)· 資產負債(右)· 估值(跨欄下方)", full["annual"] == [3] and "財務表·損益" in cats and "財務表·資產負債" in cats and "估值表" in cats and any(b["zone"] == "L" and b["sub"] == "財務表·損益" for b in tbs) and any(b["zone"] == "R" and b["sub"] == "財務表·資產負債" for b in tbs))
    is_t = next(b for b in tbs if b["sub"] == "財務表·損益")
    chk("⑦ 表格還原:損益表 6×5 · 表頭年度 · 數字原樣 · 相對位置編號 P3·L·xx·T1", len(is_t["rows"]) == 6 and len(is_t["rows"][0]) == 5 and is_t["rows"][1][0] == "Revenue" and is_t["rows"][1][4] == "23,456" and re.match(r"P3·L·\d{2}·T\d", is_t["id"]))
    chk("⑧ ENG394 _subcat 已接(偵測到單參數介面)· 表 → FIN", any(b.get("eng394") == "FIN" for b in tbs) and o["summary"]["eng394_ok"])
    h = Path(r["html"]).read_text(encoding="utf-8")
    chk("⑨ HTML:左本文 · 右資訊區 · 年度頁版面圖 · 字型階層 · 矩陣頁", "本文(首頁 BODY" in h and "資訊區(首頁 INFO" in h and "年度財報頁 P3" in h and "字型階層" in h and Path(o["html"]).exists())
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑩ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    chk("⑪ 帶加速器橋", "[VIA:ACCEL-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8"))
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0155 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
