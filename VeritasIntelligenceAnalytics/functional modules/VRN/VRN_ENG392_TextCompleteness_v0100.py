#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG392_TextCompleteness v0100 — 個股報告全文擷取無遺漏驗證 · 文字修復還原狀態分類 · 修復品質迭代 · 完整內容才摘要

操作員 R30(2026-09-28):「我比較擔心擷取文字不遺漏 文字修復還原狀態分類 修正後的個股報告第一頁 你要如何驗證全部擷取無遺漏
生成修復文字你自己看得懂品質 依品質再修正優化檢查 修完的完整內容再進行 SUMMARY 依規定」「留意輸出原始文字如何驗證所有文字都有取到」。
量過(R30):VRN 樹內沒有任何一支拿「來源每一個字」去對「擷取結果」——ENG072 只比兩法相似度(前 3000 字)、ENG056 只數來源字數、
ENG049 只找目標價/代號。本支補上這一把尺,不改任何既有引擎:

① 來源盤點(逐頁,真值 = PDF 文字層每一個字物件):fitz rawdict 每個 char · 每行數字 token(金額/百分比/日期/代號)·
   亂碼(U+FFFD / 私用區 / 控制字 / (cid:))· 影像區面積(圖內文字不在文字層 → 要 OCR 才核得到)。
   docx:word/document.xml 的每一個 <w:t>(不需第三方套件)。影像檔:只有 OCR 才有真值。
② 還原全文(每頁分區:【標題帶】【本文】【右資訊區】【頁尾】,順序照版面)→ 修復迭代:
   R0 原樣 → R1 去零寬/控制字 + 全形英數轉半形 → R2 中文字間空白 + 數字斷開接回 → R3 斷行接回(中文直接接,英數補空白)· 多空白。
   每一輪量「覆蓋率」(來源字的多重集合有多少出現在修復文)與「品質分」;**覆蓋率只要比上一輪低,這一輪整輪退回**(修復不能吃字)。
③ 核對:字元覆蓋率 · 數字逐一(少一個就列出)· 缺字片段(對齊法找出在哪一頁、前後文;只是順序換了的標「移位」不算缺)·
   多出來的字(疑似幻覺/雜訊)。第二讀法(pdfplumber)在就互核兩法字集;缺件照實寫,不冒充。
   另核 VRN 正線產出:VIA_Reports/first_page_text/<檔名>.txt(ENG072 首頁四節)對第 1 頁來源的覆蓋率與缺字。
④ 修復還原狀態分類(逐頁 → 文件取最差):
   INTACT 原生完整(綠)· REPAIRED 修復還原完整(綠)· OCR_RESTORED OCR 還原(黃:單法)· IMAGE_NO_OCR 影像頁本機無 OCR(黃)·
   IMAGE_TEXT_UNVERIFIED 頁內圖的文字未核(黃)· GARBLED 文字層亂碼(紅)· PARTIAL 有遺漏(紅,列出缺什麼)。
⑤ 品質分 0–100(A≥90 · B≥75 · C≥60 · D):亂碼比 · 中文字間空白 · 斷行 · 數字斷開 · 全形英數 · 碎行。
⑥ 摘要只給「完整」的文件(綠):修好的第 1 頁 + 其餘頁 → VRN_ENG062 尾版 summarize_report(一標題五點規定);
   還原收盤價要網路 → 只在操作員自己開了 VIA_NET_CONSENT=YES 時才抓(本支不代設)。
⑦ 範圍與版面(操作員 R30 追加令「個股報告只取第一頁」「年度財報可能分左右 · 右上下表堆疊 · 先拆左右再拆上下」;
   規則冊 VIA_Policy_VRNTextScope_v0100.json,本支照冊讀、不另寫第二份):
   文件類 = 個股報告(首頁有 評等 / 目標價 / Rating / Target …)→ **只取第 1 頁**(核對 · 修復 · 摘要都只用第 1 頁,其餘頁不進);
            年度財報(檔名或首頁有 年報 / 年度報告 / 財務報告 / 財務報表 / Annual Report …)→ 全部頁;其他 → 全部頁。
   版面切割 = 遞迴 XY 切:每一區**先找直切縫(左右)**,切得開就左→右各自再遞迴;切不開才找橫切縫(上下),上→下;
            都切不開 = 葉區。讀序 = 左子樹全部 → 右子樹全部;每個葉區標【區 L/R/T/B 路徑】,個股報告首頁另標標題帶 / 本文 / 右資訊區 / 頁尾。
輸出:VIA_Reports/vrn/text_completeness/ <檔>.restored.txt(全文,分頁分區)· <檔>.page1.txt(修正後首頁)· <檔>.audit.json ·
      <檔>.summary.md · TEXTCOMP_latest.json / .html(紅黃綠矩陣在最前)。只讀來源,不改來源。
結束碼:0 全綠 · 1 有紅(遺漏/亂碼)· 2 沒有輸入 · 3 只剩缺件(OCR / 樣本夾不在本機)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
CLI:run [--in <檔或夾> …] [--dir <夾>] [--fixtures] [--no-summary] [--json] · fixtures --out <夾> · --selftest
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import difflib
import html as _html
import importlib.util
import json
import os
import re
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
OUT = VIA / "VIA_Reports" / "vrn" / "text_completeness"
ENG072_OUT = VIA / "VIA_Reports" / "first_page_text"
ENGINE = Path(__file__).stem
PDF_EXT, DOCX_EXT, IMG_EXT = {".pdf"}, {".docx"}, {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
COVER_MIN = 0.999                      # 字元覆蓋率門檻(千分之一以內;數字另外逐一核,少一個就紅)
GARBLE_MAX = 0.01                      # 文字層亂碼比超過 1% = 字型對映壞
IMAGE_PAGE_CHARS, IMAGE_PAGE_AREA, IMAGE_NOTE_AREA = 30, 0.30, 0.15
LAMP = {"INTACT": "GREEN", "REPAIRED": "GREEN", "OCR_RESTORED": "AMBER", "IMAGE_NO_OCR": "AMBER", "IMAGE_TEXT_UNVERIFIED": "AMBER",
        "GARBLED": "RED", "PARTIAL": "RED", "EMPTY": "AMBER"}
STATE_ZH = {"INTACT": "原生完整", "REPAIRED": "修復還原完整", "OCR_RESTORED": "OCR 還原(單法)", "IMAGE_NO_OCR": "影像頁 · 本機無 OCR",
            "IMAGE_TEXT_UNVERIFIED": "頁內圖文字未核", "GARBLED": "文字層亂碼", "PARTIAL": "有遺漏", "EMPTY": "無文字"}
ORDER = {"RED": 0, "AMBER": 1, "NODATA": 2, "GREEN": 3}
ZW_RX = re.compile(r"[​-‏⁠﻿­]")
CTRL_RX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
GARBAGE_RX = re.compile(r"[�-]|\(cid:\d+\)")
CJK = r"㐀-鿿豈-﫿"
FW_RX = re.compile(r"[０-９Ａ-Ｚａ-ｚ．，％＋－／]")
NUM_RX = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?%?")
TERMINAL = "。!?;:.!?;:)」』》%…"
SEC = ("【標題帶】", "【本文】", "【右資訊區】", "【頁尾】")
SCOPE_BOOK_GLOB = "VIA_Policy_VRNTextScope_v*.json"
SCOPE_DEFAULT = {"stock_report": {"pages": "first", "keys": ["評等", "目標價", "投資評等", "Rating", "Target Price", "買進", "中立", "持有", "減碼", "Buy", "Hold", "Sell"]},
                 "annual_report": {"pages": "all", "keys": ["年報", "年度報告", "財務報告", "財務報表", "合併財務", "Annual Report", "Financial Statements"]},
                 "layout": {"order": "vertical_first", "min_gap_pt": 8.0}}


# ---------------------------------------------------------------- text primitives

def norm(s: str) -> str:
    """Comparison form: NFKC (full-width = half-width), no whitespace / zero-width / control characters."""
    s = unicodedata.normalize("NFKC", ZW_RX.sub("", s or ""))
    return re.sub(r"\s+", "", CTRL_RX.sub("", s))


def num_canon(line: str) -> str:
    s = unicodedata.normalize("NFKC", ZW_RX.sub("", line or ""))
    s = re.sub(r"(\d)\s*,\s*(\d{3})(?!\d)", r"\1,\2", s)            # split thousands: 1, 650 → 1,650 (not 78, 2009)
    s = re.sub(r"(\d)\s*\.\s*(\d)(?!\d*\s*[.,]\s*\d{4})", r"\1.\2", s) if re.search(r"\d\s+\.|\.\s+\d", s) else s
    return re.sub(r"(\d)\s+%", r"\1%", s)


def numbers(text: str) -> Counter:
    c = Counter()
    for line in (text or "").splitlines():
        for t in NUM_RX.findall(num_canon(line)):
            t = t.strip(",").lstrip("+")
            if any(ch.isdigit() for ch in t):
                c[t] += 1
    return c


def garbage_count(text: str) -> int:
    return len(GARBAGE_RX.findall(text or "")) + len(CTRL_RX.findall(text or ""))


def coverage(src: str, ext: str) -> tuple:
    """(ratio, missing Counter, extra Counter) over the normalized character multisets."""
    a, b = Counter(norm(src)), Counter(norm(ext))
    total = sum(a.values())
    missing = a - b
    extra = b - a
    return (1.0 if total == 0 else 1 - sum(missing.values()) / total), missing, extra


def missing_segments(src: str, ext: str, limit: int = 20) -> list:
    """Where the omissions are: aligned on the normalized strings; a segment still present elsewhere is 'moved', not missing."""
    a, b = norm(src), norm(ext)
    if not a:
        return []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=len(a) > 20000)
    out = []
    for op, i1, i2, _j1, _j2 in sm.get_opcodes():
        if op not in ("delete", "replace"):
            continue
        seg = a[i1:i2]
        moved = len(seg) >= 2 and seg in b
        out.append({"text": seg[:80], "len": i2 - i1, "before": a[max(0, i1 - 12):i1], "after": a[i2:i2 + 12], "moved": moved})
    real = [x for x in out if not x["moved"]]
    return (real + [x for x in out if x["moved"]])[:limit]


# ---------------------------------------------------------------- repair passes (never delete a visible character)

def p1_clean(t: str) -> str:
    t = CTRL_RX.sub("", ZW_RX.sub("", t))
    return FW_RX.sub(lambda m: unicodedata.normalize("NFKC", m.group(0)), t)


def p2_spacing(t: str) -> str:
    t = re.sub(rf"(?<=[{CJK}])[ 　]+(?=[{CJK}])", "", t)
    t = re.sub(r"(\d)[ 　]+([,.])[ 　]*(\d)", r"\1\2\3", t)
    t = re.sub(r"(\d{1,3})\.[ 　]+(\d{1,2})(?=[ 　]*%)", r"\1.\2", t)        # 49. 5% → 49.5%
    return re.sub(r"(\d)([,.])[ 　]+(\d{3})(?!\d)", r"\1\2\3", t)


CJK_RX = re.compile(rf"[{CJK}\u3000-\u303f\uff01-\uff0f\uff1a-\uff20]")
LABEL_RX = re.compile(r"^[^\s::]{1,12}[::]")


def should_join(prev: str, nxt: str) -> bool:
    """One rule for repair and for the quality score: a wrapped line of prose, not a label, a table row or a heading."""
    if not prev or not nxt or prev.startswith(("【", "=== 第")) or nxt.startswith(("【", "=== 第")):
        return False
    if prev[-1] in TERMINAL or re.match(r"^([•\-*]\s|\d{1,2}[、)]|\d{1,2}\.\s|\[\d+\])", nxt):
        return False
    if LABEL_RX.match(nxt) or LABEL_RX.match(prev):                 # 評等:買進 / 目標價:1,250元 …
        return False
    if re.search(r"[\d%]$", prev) and CJK_RX.match(nxt[0]):          # table row: 營業收入 1,234,607 ↵ 營業毛利 …
        return False
    if re.search(r"\d[,.]?$", prev) and nxt[0].isdigit():            # never glue two numbers: 65–78, ↵ 2009.
        return False
    return len(prev) >= 10                                           # short lines are headings / cells


def join_pair(prev: str, nxt: str) -> str:
    tight = (CJK_RX.match(prev[-1]) or CJK_RX.match(nxt[0])          # Chinese joins directly; everything else keeps a space
             or (len(prev) > 1 and prev[-1] in ",.;:" and CJK_RX.match(prev[-2])))
    return prev + ("" if tight else " ") + nxt


def p3_lines(t: str) -> str:
    out, buf = [], ""
    for ln in t.split("\n"):
        s = ln.strip()
        if not s:
            continue
        if buf and should_join(buf, s):
            buf = join_pair(buf, s)
            continue
        if buf:
            out.append(buf)
        buf = s
    if buf:
        out.append(buf)
    text = "\n".join(out)
    text = re.sub(r"\n(?=【|=== 第)", "\n\n", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip() + "\n"


PASSES = (("R1 去零寬 · 全形英數轉半形", p1_clean), ("R2 中文字間空白 · 數字接回", p2_spacing), ("R3 斷行接回 · 多空白", p3_lines))


def quality(text: str) -> dict:
    body = [ln for ln in (text or "").splitlines() if ln.strip() and not ln.startswith(("【", "=== 第"))]
    chars = max(1, sum(len(ln) for ln in body))
    g = garbage_count(text) / chars
    spaced = len(re.findall(rf"[{CJK}][ 　][{CJK}]", text or "")) * 1000 / chars
    every = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]                 # zone headers stay in: no join across zones
    broken = sum(1 for a, b in zip(every, every[1:]) if should_join(a, b)) / max(1, len(body))
    splitnum = len(re.findall(r"\d[ 　]+[,.][ 　]*\d|\d[,.][ 　]+\d{3}(?!\d)", text or ""))
    fw = len(FW_RX.findall(text or ""))
    frag = sum(1 for ln in body if len(ln.strip()) <= 2) / max(1, len(body))
    pen = {"亂碼": min(40, g * 400), "字間空白": min(20, spaced * 2), "斷行": min(20, broken * 40), "數字斷開": min(10, splitnum * 2),
           "全形英數": min(10, fw * 0.5), "碎行": min(10, frag * 30)}
    score = round(max(0.0, 100 - sum(pen.values())), 1)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"
    return {"score": score, "grade": grade, "penalty": {k: round(v, 1) for k, v in pen.items() if v}}


def repair_loop(raw: str, src: str) -> tuple:
    """R0 → R3; a round that lowers coverage is rolled back whole. Returns (final text, rounds)."""
    cur = raw
    cov0 = coverage(src, cur)[0]
    rounds = [{"round": "R0 原樣", **quality(cur), "coverage": round(cov0, 5), "kept": True}]
    for name, fn in PASSES:
        nxt = fn(cur)
        cov = coverage(src, nxt)[0]
        q = quality(nxt)
        kept = cov >= rounds[-1]["coverage"] - 1e-9 if rounds[-1]["kept"] else cov >= cov0 - 1e-9
        rounds.append({"round": name, **q, "coverage": round(cov, 5), "kept": kept, "changed": nxt != cur})
        if kept:
            cur = nxt
    return cur, rounds


# ---------------------------------------------------------------- source readers

def _ocr_backend():
    try:
        import pytesseract  # noqa: F401
        import shutil
        if shutil.which("tesseract") is None:
            return None
        return pytesseract
    except Exception:
        return None


def _plumber():
    try:
        import pdfplumber
        return pdfplumber
    except Exception:
        return None


def scope_book() -> dict:
    hits = sorted(REG.glob(SCOPE_BOOK_GLOB))
    try:
        book = json.loads(hits[-1].read_text(encoding="utf-8")) if hits else {}
    except (OSError, ValueError):
        book = {}
    out = {k: dict(v) for k, v in SCOPE_DEFAULT.items()}
    for k in out:
        out[k].update(book.get(k) or {})
    out["_book"] = hits[-1].name if hits else "(規則冊不在,用內建預設)"
    return out


def doc_type(name: str, page1: str) -> str:
    sb = scope_book()
    hay = name + "\n" + (page1 or "")[:3000]
    if any(k in hay for k in sb["annual_report"]["keys"]):
        return "annual_report"
    if any(k in (page1 or "") for k in sb["stock_report"]["keys"]):
        return "stock_report"
    return "general"


def _gaps(spans: list, lo: float, hi: float, min_gap: float) -> list:
    """Empty bands along one axis: (start, end) intervals inside [lo, hi] that no span covers, at least min_gap wide."""
    spans = sorted(spans)
    out, cur = [], lo
    for a, b in spans:
        if a - cur >= min_gap and cur > lo:
            out.append((cur, a))
        cur = max(cur, b)
    return out


def xy_cut(blocks: list, box: tuple, min_gap: float = 8.0, path: str = "") -> list:
    """Recursive XY cut, **vertical (left/right) first**, then horizontal (top/bottom). Returns [(path, box, blocks)] in reading order."""
    if len(blocks) <= 1:
        return [(path or "0", box, blocks)]
    x0, y0, x1, y1 = box
    v = _gaps([(b[0], b[2]) for b in blocks], x0, x1, min_gap)
    if v:
        a, b = max(v, key=lambda g: g[1] - g[0])
        cut = (a + b) / 2
        left = [bl for bl in blocks if bl[2] <= cut]
        right = [bl for bl in blocks if bl[0] >= cut]
        if left and right and len(left) + len(right) == len(blocks):
            return (xy_cut(left, (x0, y0, cut, y1), min_gap, path + "L") + xy_cut(right, (cut, y0, x1, y1), min_gap, path + "R"))
    best = None                                              # gutter with the fewest crossing blocks (those are full-width bands)
    step = max(1.0, (x1 - x0) / 200)
    xs = [x0 + (x1 - x0) * 0.15 + i * step for i in range(int((x1 - x0) * 0.7 / step))]
    for x in xs:
        cross = sum(1 for bl in blocks if bl[0] < x < bl[2])
        left = sum(1 for bl in blocks if bl[2] <= x)
        right = sum(1 for bl in blocks if bl[0] >= x)
        if left and right:
            clear = min([abs(x - bl[2]) for bl in blocks if bl[2] <= x] + [abs(bl[0] - x) for bl in blocks if bl[0] >= x])
            key = (cross, -clear)
            if best is None or key < best[0]:
                best = (key, x)
    if best is not None and 0 < best[0][0] <= max(1, len(blocks) // 3) and -best[0][1] >= min_gap / 2:
        cut = best[1]
        spanning = [bl for bl in blocks if bl[0] < cut < bl[2]]
        if spanning and len(spanning) < len(blocks):
            bands, cur = [], []
            for bl in sorted(blocks, key=lambda bl: (bl[1], bl[0])):
                if bl in spanning:
                    if cur:
                        bands.append(cur)
                    bands.append([bl])
                    cur = []
                else:
                    cur.append(bl)
            if cur:
                bands.append(cur)
            if len(bands) > 1:
                out = []
                for i, band in enumerate(bands, 1):
                    bb = (x0, min(b[1] for b in band), x1, max(b[3] for b in band))
                    out += xy_cut(band, bb, min_gap, path + f"H{i}")
                return out
    heights = sorted(bl[3] - bl[1] for bl in blocks)
    hz = _gaps([(b[1], b[3]) for b in blocks], y0, y1, max(min_gap, heights[len(heights) // 2]))   # a row gap is not a section gap
    if hz:
        a, b = max(hz, key=lambda g: g[1] - g[0])
        cut = (a + b) / 2
        top = [bl for bl in blocks if bl[3] <= cut]
        bot = [bl for bl in blocks if bl[1] >= cut]
        if top and bot and len(top) + len(bot) == len(blocks):
            return (xy_cut(top, (x0, y0, x1, cut), min_gap, path + "T") + xy_cut(bot, (x0, cut, x1, y1), min_gap, path + "B"))
    return [(path or "0", box, sorted(blocks, key=lambda bl: (round(bl[1], 1), bl[0])))]


def _bbox(bl: list, box: tuple) -> tuple:
    return (min(b[0] for b in bl), min(b[1] for b in bl), max(b[2] for b in bl), max(b[3] for b in bl)) if bl else box


def label_leaf(path: str, box: tuple, w: float, h: float) -> str:
    x0, y0, x1, y1 = box
    ys = [y0, y1]
    if y1 <= h * 0.14:
        zone = SEC[0]
    elif y0 >= h * 0.88:
        zone = SEC[3]
    elif "R" in path and x0 >= w * 0.5:
        zone = SEC[2]
    else:
        zone = SEC[1]
    return f"{zone}〔區 {path or '0'}〕" if ys else zone


def pdf_pages(path: Path) -> list:
    import fitz
    pages = []
    with fitz.open(str(path)) as doc:
        for pno, page in enumerate(doc, 1):
            w, h = page.rect.width or 1, page.rect.height or 1
            chars, lines = [], []
            for b in page.get_text("rawdict").get("blocks", []):
                if b.get("type") != 0:
                    continue
                for ln in b.get("lines", []):
                    s = "".join(ch.get("c", "") for sp in ln.get("spans", []) for ch in sp.get("chars", []))
                    chars.append(s)
                    lines.append(s)
            src = "\n".join(lines)
            area = 0.0
            for info in page.get_image_info():
                x0, y0, x1, y1 = info.get("bbox", (0, 0, 0, 0))
                area += max(0, min(x1, w) - max(x0, 0)) * max(0, min(y1, h) - max(y0, 0))
            blocks = [(x0, y0, x1, y1, str(t).rstrip("\n")) for x0, y0, x1, y1, t, _bn, bt in page.get_text("blocks")
                      if bt == 0 and str(t).strip()]
            leaves = xy_cut(blocks, (0, 0, w, h), scope_book()["layout"].get("min_gap_pt", 8.0))
            raw = "\n\n".join(f"{label_leaf(path_, _bbox(bl, box), w, h)}\n" + "\n\n".join(b[4] for b in bl) for path_, box, bl in leaves)
            pages.append({"page": pno, "src": src, "raw": raw, "image_area": round(min(1.0, area / (w * h)), 3),
                          "images": len(page.get_image_info()), "_fitz_page": pno})
    return pages


def plumber_chars(path: Path) -> list | None:
    pl = _plumber()
    if pl is None:
        return None
    try:
        with pl.open(str(path)) as pdf:
            return ["".join(c.get("text", "") for c in p.chars) for p in pdf.pages]
    except Exception:
        return None


def ocr_page(path: Path, pno: int) -> str | None:
    ocr = _ocr_backend()
    if ocr is None:
        return None
    try:
        import fitz
        from PIL import Image
        import io
        with fitz.open(str(path)) as doc:
            pix = doc[pno - 1].get_pixmap(dpi=300)
            return ocr.image_to_string(Image.open(io.BytesIO(pix.tobytes("png"))), lang="chi_tra+eng")
    except Exception:
        return None


def docx_pages(path: Path) -> list:
    with zipfile.ZipFile(str(path)) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    paras = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        t = "".join(_html.unescape(x) for x in re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", p, flags=re.S))
        if t:
            paras.append(t)
    src = "\n".join(paras)
    return [{"page": 1, "src": src, "raw": f"{SEC[1]}\n" + "\n".join(paras), "image_area": 0.0, "images": 0}]


# ---------------------------------------------------------------- one document

def audit_doc(path: Path) -> dict:
    ext = path.suffix.lower()
    doc = {"file": str(path), "name": path.name, "kind": ext.lstrip("."), "pages": []}
    try:
        pages = pdf_pages(path) if ext in PDF_EXT else docx_pages(path) if ext in DOCX_EXT else \
            [{"page": 1, "src": "", "raw": "", "image_area": 1.0, "images": 1}]
    except Exception as exc:
        doc.update(state="PARTIAL", lamp="RED", why=f"讀不開:{type(exc).__name__}: {str(exc)[:120]}")
        return doc
    doc["doc_type"] = doc_type(path.name, pages[0]["src"] if pages else "")
    sb = scope_book()
    doc["scope_book"] = sb["_book"]
    if doc["doc_type"] == "stock_report" and sb["stock_report"].get("pages") == "first":
        doc["pages_total"], pages = len(pages), pages[:1]          # 個股報告只取第一頁(規則冊)
        doc["scope"] = f"個股報告 · 只取第 1 頁(共 {doc['pages_total']} 頁)"
    else:
        doc["pages_total"] = len(pages)
        doc["scope"] = ("年度財報" if doc["doc_type"] == "annual_report" else "一般文件") + f" · 全部 {len(pages)} 頁 · 版面先拆左右再拆上下"
    if doc["doc_type"] != "stock_report":                     # zone names are a stock-report first-page notion; others keep the cut path only
        for pg in pages:
            pg["raw"] = re.sub(r"【(?:標題帶|本文|右資訊區|頁尾)】〔區 (\w+)〕", r"【區 \1】", pg["raw"])
    second = plumber_chars(path) if ext in PDF_EXT else None
    restored_pages = []
    for pg in pages:
        src, raw = pg["src"], pg["raw"]
        rec = {"page": pg["page"], "src_chars": len(norm(src)), "images": pg["images"], "image_area": pg["image_area"]}
        g = garbage_count(src)
        rec["garbage"] = g
        is_image_page = rec["src_chars"] < IMAGE_PAGE_CHARS and (pg["image_area"] >= IMAGE_PAGE_AREA or ext in IMG_EXT)
        if is_image_page:
            ocr = ocr_page(path, pg["page"]) if ext in PDF_EXT else None
            if ocr is None:
                rec.update(state="IMAGE_NO_OCR", coverage=None, note="影像頁:文字層沒有字,真值只能靠 OCR;本機沒有 OCR 後端(pytesseract + tesseract)")
                restored_pages.append((pg["page"], f"{SEC[1]}\n(影像頁,未 OCR)"))
                doc["pages"].append(rec)
                continue
            src, raw = ocr, f"{SEC[1]}\n{ocr}"
            rec["ocr"] = True
        fixed, rounds = repair_loop(raw, src)
        cov, miss, extra = coverage(src, fixed)
        n_src, n_fix = numbers(src), numbers(fixed)
        num_missing = n_src - n_fix
        rec.update(coverage=round(cov, 5), missing_chars=sum(miss.values()), extra_chars=sum(extra.values()),
                   numbers=sum(n_src.values()), numbers_missing=sorted(num_missing.elements())[:20],
                   segments=missing_segments(src, fixed), rounds=rounds, quality=rounds[-1] if rounds[-1]["kept"] else
                   next(r for r in reversed(rounds) if r["kept"]))
        if second is not None and pg["page"] <= len(second):
            c2 = coverage(second[pg["page"] - 1], src)[0]
            rec["second_reader"] = {"reader": "pdfplumber", "agree": round(c2, 5)}
        else:
            rec["second_reader"] = {"reader": "pdfplumber", "agree": None, "note": "本境沒有 pdfplumber(第二讀法缺件;真值仍是文字層每個字)"}
        if rec.get("ocr"):
            state = "OCR_RESTORED"
        elif rec["src_chars"] == 0:
            state = "EMPTY"
        elif g / max(1, len(src)) > GARBLE_MAX:
            state = "GARBLED"
        elif cov < COVER_MIN or num_missing:
            state = "PARTIAL"
        elif pg["image_area"] >= IMAGE_NOTE_AREA and _ocr_backend() is None:
            state = "IMAGE_TEXT_UNVERIFIED"
        elif any(r.get("changed") and r.get("kept") for r in rounds[1:]):
            state = "REPAIRED"
        else:
            state = "INTACT"
        rec["state"] = state
        doc["pages"].append(rec)
        restored_pages.append((pg["page"], fixed))
    states = [p["state"] for p in doc["pages"]]
    worst = min(states, key=lambda s: ORDER[LAMP[s]]) if states else "EMPTY"
    doc["state"], doc["lamp"] = worst, LAMP[worst]
    doc["restored"] = "\n".join(f"=== 第 {n} 頁 ===\n{t.strip()}\n" for n, t in restored_pages)
    doc["page1"] = restored_pages[0][1] if restored_pages else ""
    covs = [p["coverage"] for p in doc["pages"] if p.get("coverage") is not None]
    doc["coverage"] = round(min(covs), 5) if covs else None
    doc["numbers"] = sum(p.get("numbers", 0) for p in doc["pages"])
    doc["numbers_missing"] = sum(len(p.get("numbers_missing") or []) for p in doc["pages"])
    doc["quality"] = quality(doc["restored"])
    doc["eng072"] = eng072_check(path, pages[0]["src"] if pages else "")
    return doc


def eng072_check(path: Path, page1_src: str) -> dict:
    """The VRN first-page output (ENG072 four sections) against page 1 of the source."""
    txt = ENG072_OUT / (path.stem + ".txt")
    if not txt.exists():
        return {"state": "NODATA", "note": f"ENG072 首頁輸出不在({txt.name};先跑 VRN 首頁擷取)"}
    got = txt.read_text(encoding="utf-8", errors="replace")
    cov, miss, _ = coverage(page1_src, got)
    nmiss = numbers(page1_src) - numbers(got)
    state = "GREEN" if cov >= COVER_MIN and not nmiss else "RED"
    q = quality(got)
    return {"state": state, "coverage": round(cov, 5), "missing_chars": sum(miss.values()), "numbers_missing": sorted(nmiss.elements())[:20],
            "segments": missing_segments(page1_src, got, 10), "file": str(txt), "quality": q,
            "note": "完整但品質低於 ENG392 修正版(看 <檔>.page1.txt)" if state == "GREEN" and q["grade"] not in ("A",) else ""}


# ---------------------------------------------------------------- summary (only complete documents)

def _num(v: str):
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", v or "")
    return float(m.group(0).replace(",", "")) if m else None


def fields(page1: str) -> dict:
    """Label: value lines of the first page (右資訊區) → the summarizer's own keyword arguments."""
    out, eps = {}, []
    for ln in page1.splitlines():
        m = re.match(r"^\s*([^\s::]{1,14})[::]\s*(.+)$", ln)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if "目標價" in k:
            out["target_price"] = _num(v)
        elif k in ("評等", "投資評等") or "Rating" in k:
            out["rating"] = re.split(r"[((]", v)[0].strip()
        elif "分析師" in k:
            out["analyst"] = v
        elif "日期" in k:
            d = re.sub(r"\D", "", v)
            out["report_date"] = d[:8] if len(d) >= 8 else v
        elif "券商" in k:
            out["broker"] = v
        elif k.upper().startswith("EPS"):
            eps.append(_num(v))
        elif k.upper().startswith("ROE"):
            out["roe_current"] = _num(v)
        elif k.upper().startswith(("BVPS", "每股淨值")):
            out["bvps_current"] = _num(v)
        elif k.upper().startswith(("DPS", "股利")):
            out["dps_current"] = _num(v)
    if eps:
        out["eps_current"] = eps[0]
        if len(eps) > 1:
            out["eps_next"] = eps[1]
    return {k: v for k, v in out.items() if v not in (None, "")}


def _summarizer():
    hits = sorted(HERE.glob("VRN_ENG062_SummarizerV1_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("vrn_eng062_for_" + ENGINE, hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def summarize(doc: dict) -> dict:
    if doc.get("lamp") != "GREEN":
        return {"state": "SKIP", "why": f"內容未確認完整({STATE_ZH.get(doc.get('state'), doc.get('state'))});依規定完整內容才摘要"}
    if doc.get("doc_type") != "stock_report":
        return {"state": "N/A", "why": "個股報告摘要規定(一標題五點)只用在個股報告;年度財報 / 一般文件只驗全文,不套個股摘要"}
    page1 = doc["page1"]
    rest = "" if doc.get("doc_type") == "stock_report" else (
        doc["restored"].split("=== 第 2 頁 ===", 1)[1] if "=== 第 2 頁 ===" in doc["restored"] else "")
    page1 = "\n".join(ln for ln in page1.splitlines() if not ln.startswith(("【", "=== 第")))    # labels are ours, not the report's
    rest = "\n".join(ln for ln in rest.splitlines() if not ln.startswith(("【", "=== 第")))
    m = re.search(r"[((](\d{4})[))]|(\d{4})\s*(?:TT|\.TW|TW)", page1)
    ticker = (m.group(1) or m.group(2)) if m else ""
    kv = fields(page1)
    try:
        mod = _summarizer()
        if mod is None:
            return {"state": "ABSENT", "why": "VRN_ENG062 尾版不在"}
        body = mod._load_body() if hasattr(mod, "_load_body") else mod
        fn = getattr(body, "summarize_report", None) or getattr(mod, "summarize_report")
        if os.environ.get("VIA_NET_CONSENT") != "YES":            # no network without the operator's own consent (L07)
            fetcher = getattr(body, "AdjCloseFetcher", None)
            if fetcher is not None:
                fetcher.fetch = lambda self, *a, **k: {"error": "未開同意閘 VIA_NET_CONSENT(本支不代設)"}
        s = fn(ticker, page1, rest, filename=doc["name"], **kv)
        md = s.to_markdown() if hasattr(s, "to_markdown") else str(s)
        points = [getattr(s, f"point_{i}_{k}", "") for i, k in ((1, "conclusion"), (2, "growth"), (3, "valuation"), (4, "peers"), (5, "risk"))]
        basis = norm(page1 + "\n" + rest)
        ungrounded = [p for p in points if p and norm(re.sub(r"[。.]$", "", p)) not in basis]    # every point must be quotable from the source
        headline = getattr(s, "headline", "")
        titles = ("核心結論", "成長動能", "財務與估值", "同業比較", "潛在風險")
        kept = [p if p and p not in ungrounded else "原文未提及" for p in points]      # filler the summarizer made up is not the report's
        facts = " · ".join(f"{k} {v}" for k, v in (("評等", kv.get("rating")), ("目標價", kv.get("target_price")), ("EPS", kv.get("eps_current")),
                                                   ("次年 EPS", kv.get("eps_next")), ("分析師", kv.get("analyst")), ("日期", kv.get("report_date"))) if v)
        md = (f"{headline}\n\n" + "\n".join(f"{i}. {t}:{p}" for i, (t, p) in enumerate(zip(titles, kept), 1))
              + f"\n\n---\n首頁欄位:{facts or '—'}\n出處核對:五點每一點都在修正後首頁找得到原句;摘要引擎的補句 {len(ungrounded)} 句已改成「原文未提及」"
              + ("\n(" + " / ".join(ungrounded) + ")" if ungrounded else "") + "\n")
        state = "GREEN" if headline and any(p != "原文未提及" for p in kept) else "AMBER"
        return {"state": state, "ticker": ticker, "markdown": md, "headline": headline, "points": kept, "engine_points": points,
                "ungrounded": ungrounded, "why": ("摘要引擎補句已拿掉:" + " / ".join(ungrounded)) if ungrounded else ""}
    except Exception as exc:
        return {"state": "ABSENT", "why": f"摘要引擎載不起來:{type(exc).__name__}: {str(exc)[:120]}"}


# ---------------------------------------------------------------- inputs · fixtures

def _spec_dirs() -> list:
    books = sorted(REG.glob("VIA_InputConsole_Spec_v*.json"))
    if not books:
        return []
    try:
        spec = json.loads(books[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    user = spec.get("user") or {}
    fam = ((spec.get("families") or {}).get("vrn") or {}).get("input") or {}
    out = []
    for d in (user.get("vrn_dir"), fam.get("dir_default"), fam.get("incoming")):
        if d:
            p = Path(d) if Path(d).is_absolute() or ":" in str(d) else VIA / d
            out.append(p)
    return out


def collect_inputs(given: list, fixtures_dir: Path | None = None) -> tuple:
    notes, files = [], []
    targets = [Path(g) for g in given] if given else _spec_dirs()
    if fixtures_dir is not None:
        targets.append(fixtures_dir)
    for t in targets:
        if not t.exists():
            notes.append(f"不在本機:{t}(操作員樣本夾在工作站;容器照實 ABSENT)")
            continue
        cand = [t] if t.is_file() else sorted(p for p in t.rglob("*") if p.is_file())
        files += [p for p in cand if p.suffix.lower() in PDF_EXT | DOCX_EXT | IMG_EXT]
    seen, uniq = set(), []
    for f in files:
        k = f.resolve()
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    return uniq, notes


def make_fixtures(out: Path) -> list:
    """Synthetic broker-report samples (text-layer truth known): clean · needs repair · scanned image page."""
    import fitz
    out.mkdir(parents=True, exist_ok=True)
    made = []

    def page(doc, lines_left, lines_right, header, footer, spaced=False):
        pg = doc.new_page(width=595, height=842)
        pg.insert_text((40, 60), header, fontname="china-t", fontsize=14)
        y = 120
        for ln in lines_left:
            pg.insert_text((40, y), ln, fontname="china-t", fontsize=10.5)
            y += 16
        y = 120
        for ln in lines_right:
            pg.insert_text((400, y), ln, fontname="china-t", fontsize=9)
            y += 14
        pg.insert_text((40, 810), footer, fontname="china-t", fontsize=7)
        return pg

    left = ["台積電(2330)第三季營收優於預期,先進製程",
            "需求強勁,我們維持買進評等,目標價由1,180元",
            "上調至1,250元,相當於2027年預估EPS 62.5元",
            "的20倍本益比。受惠AI加速器與高效能運算訂單,",
            "3奈米產能利用率維持在95%以上,毛利率預估",
            "達58.3%,較上季提升1.2個百分點。",
            "風險:匯率波動、地緣政治、終端需求放緩。"]
    right = ["評等:買進(維持)", "目標價:1,250元", "收盤價:1,035元", "潛在漲幅:20.8%", "分析師:王小明", "報告日期:2026/09/28",
             "EPS(2026F):48.7", "EPS(2027F):62.5", "ROE(2026F):28.4%"]
    d = fitz.open()
    page(d, left, right, "台積電 TSMC (2330 TT) 個股報告", "本報告僅供參考,投資人應審慎評估風險。第 1 頁")
    page(d, ["營收預估(百萬元):2025 2,894,307;2026F 3,512,880;2027F 4,210,455。",
             "資本支出維持420億美元,先進封裝CoWoS產能2026年底倍增。"], [], "財務預估", "第 2 頁")
    p1 = out / "fixture_broker_clean.pdf"
    d.save(str(p1))
    made.append(p1)
    d = fitz.open()
    pg = d.new_page(width=595, height=842)
    pg.insert_text((40, 60), "聯 發 科(２４５４) 個股報告", fontname="china-t", fontsize=14)
    y = 120
    for ln in ["聯發科第三季營收４８２．５億元,年增１８．３%,天璣旗艦晶片出貨暢旺,",
               "我們維持買進,目標價 1, 650元。​毛利率預估 49. 5%,",
               "AI 邊緣運算需求帶動下半年成長。"]:
        pg.insert_text((40, y), ln, fontname="china-t", fontsize=10.5)
        y += 16
    pg.insert_text((40, 810), "第 1 頁", fontname="china-t", fontsize=7)
    p2 = out / "fixture_broker_needs_repair.pdf"
    d.save(str(p2))
    made.append(p2)
    d = fitz.open()
    for pno in (1, 2):
        pg = d.new_page(width=595, height=842)
        pg.insert_text((40, 50), f"XX股份有限公司 2025 年度報告 財務報表 第 {pno} 頁", fontname="china-t", fontsize=12)
        for (x, y, tag) in ((40, 110, "左上表"), (40, 470, "左下表"), (320, 110, "右上表"), (320, 470, "右下表")):
            pg.insert_text((x, y), f"{tag}(單位:千元)", fontname="china-t", fontsize=10)
            for i, (k, v) in enumerate((("營業收入", f"{1234567 * pno + x:,}"), ("營業毛利", f"{456789 + y:,}"), ("本期淨利", f"{98765 + x + y:,}"),
                                        ("每股盈餘", f"{12.34 + pno:.2f}"))):
                pg.insert_text((x, y + 20 + i * 16), f"{k}  {v}", fontname="china-t", fontsize=9)
    p4 = out / "fixture_annual_report.pdf"
    d.save(str(p4))
    made.append(p4)
    src = fitz.open(str(p1))
    pix = src[0].get_pixmap(dpi=72)
    d = fitz.open()
    pg = d.new_page(width=595, height=842)
    pg.insert_image(pg.rect, stream=pix.tobytes("png"))
    p3 = out / "fixture_broker_scanned.pdf"
    d.save(str(p3))
    made.append(p3)
    return made


# ---------------------------------------------------------------- run · page

def _kit():
    hits = sorted((REG).glob("CGC_MDL241_TemplateAdapter_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("mdl241_for_" + ENGINE, hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    try:
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def page_html(rep: dict) -> str:
    e = _html.escape
    kit = _kit()
    lamp = (kit.lamp if kit else (lambda s, t: f"<b>{e(t)}</b>"))
    rows = "".join(
        f"<tr><td>{lamp(d['lamp'], d['lamp'])}</td><td>{e(d['name'])}</td><td>{e(STATE_ZH.get(d['state'], d['state']))}</td>"
        f"<td>{'—' if d.get('coverage') is None else f'{d[chr(99) + chr(111) + chr(118) + chr(101) + chr(114) + chr(97) + chr(103) + chr(101)] * 100:.2f}%'}</td>"
        f"<td>{d.get('numbers', 0)} · 缺 {d.get('numbers_missing', 0)}</td><td>{e(d['quality']['grade'])} {d['quality']['score']}</td>"
        f"<td>{e((d.get('eng072') or {}).get('state', '—'))}</td><td>{e((d.get('summary') or {}).get('state', '—'))}</td></tr>"
        for d in rep["docs"])
    detail = []
    for d in rep["docs"]:
        segs = [s for p in d.get("pages", []) for s in (p.get("segments") or []) if not s.get("moved")]
        pg = "".join(f"<tr><td>{p['page']}</td><td>{lamp(LAMP[p['state']], STATE_ZH.get(p['state'], p['state']))}</td>"
                     f"<td>{'—' if p.get('coverage') is None else round(p['coverage'] * 100, 2)}</td><td>{p.get('src_chars', 0)}</td>"
                     f"<td>{e(', '.join(p.get('numbers_missing') or []) or '—')}</td>"
                     f"<td>{e(' → '.join(r['round'].split()[0] + ' ' + str(r['score']) for r in p.get('rounds') or []))}</td>"
                     f"<td>{e(p.get('note', ''))}</td></tr>" for p in d.get("pages", []))
        detail.append(f"<h3>{e(d['name'])} · {e(STATE_ZH.get(d['state'], d['state']))}</h3>"
                      f"<table class='via'><tr><th>頁</th><th>狀態</th><th>覆蓋%</th><th>來源字</th><th>缺的數字</th><th>修復迭代(品質分)</th><th>備註</th></tr>{pg}</table>"
                      + ("<div class='via-note'>缺字片段:" + e(" · ".join(f"「{s['before']}【{s['text']}】{s['after']}」" for s in segs[:8])) + "</div>" if segs else "")
                      + f"<pre style='white-space:pre-wrap;max-height:18em;overflow:auto'>{e(d.get('page1', '')[:1600])}</pre>")
    body = (f"<h3>紅黃綠矩陣 · 全文擷取無遺漏驗證</h3><table class='via'><tr><th>燈</th><th>文件</th><th>修復還原狀態</th><th>字元覆蓋</th>"
            f"<th>數字</th><th>品質</th><th>ENG072 首頁</th><th>摘要</th></tr>{rows}</table>"
            + "".join(detail)
            + "<div class='via-note'>真值 = 來源文字層每一個字物件(影像只能靠 OCR);覆蓋率 = 來源字多重集合出現在修復文的比例;數字逐一核;"
              "修復每一輪覆蓋率下降就整輪退回。</div>")
    side = (f"<div class='via-card'>{lamp(rep['verdict'], '總判 ' + rep['verdict'])}</div><div class='via-note'>{e(rep['ts'])}</div>"
            f"<div class='via-note'>{len(rep['docs'])} 件 · " + " · ".join(f"{k} {v}" for k, v in sorted(rep["tally"].items())) + "</div>"
            + "".join(f"<div class='via-note'>{e(n)}</div>" for n in rep.get("notes", [])))
    if kit:
        return kit.page("VRN 全文擷取無遺漏驗證", body, side, module={"id": "vrn-text-completeness", "name": "全文無遺漏"})
    return f"<!doctype html><meta charset='utf-8'><title>VRN 全文擷取無遺漏驗證</title>{side}{body}"


def run(given: list | None = None, fixtures: bool = False, do_summary: bool = True, write: bool = True) -> dict:
    fx = OUT / "fixtures" if fixtures else None
    if fx is not None:
        make_fixtures(fx)
    files, notes = collect_inputs(given or [], fx)
    docs = []
    for f in files:
        d = audit_doc(f)
        if do_summary:
            d["summary"] = summarize(d)
        docs.append(d)
    tally = Counter(d["lamp"] for d in docs)
    verdict = "NODATA" if not docs else ("RED" if tally.get("RED") else "AMBER" if tally.get("AMBER") else "GREEN")
    rep = {"engine": ENGINE, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "verdict": verdict, "tally": dict(tally),
           "notes": notes, "docs": docs, "ocr_backend": _ocr_backend() is not None, "second_reader": _plumber() is not None}
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        for d in docs:
            stem = Path(d["name"]).stem
            (OUT / f"{stem}.restored.txt").write_text(d.get("restored", ""), encoding="utf-8")
            (OUT / f"{stem}.page1.txt").write_text(d.get("page1", ""), encoding="utf-8")
            if (d.get("summary") or {}).get("markdown"):
                (OUT / f"{stem}.summary.md").write_text(d["summary"]["markdown"], encoding="utf-8")
            (OUT / f"{stem}.audit.json").write_text(json.dumps({k: v for k, v in d.items() if k not in ("restored", "page1")},
                                                               ensure_ascii=False, indent=1), encoding="utf-8")
        slim = {**rep, "docs": [{k: v for k, v in d.items() if k not in ("restored", "page1", "pages")} for d in docs]}
        (OUT / "TEXTCOMP_latest.json").write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")
        (OUT / "TEXTCOMP_latest.html").write_text(page_html(rep), encoding="utf-8")
    return rep


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if args[:1] == ["fixtures"]:
        out = Path(args[args.index("--out") + 1]) if "--out" in args else OUT / "fixtures"
        for p in make_fixtures(out):
            print(f"  [樣本] {p}")
        return 0
    given = [args[i + 1] for i, a in enumerate(args) if a in ("--in", "--dir") and i + 1 < len(args)]
    rep = run(given, fixtures="--fixtures" in args, do_summary="--no-summary" not in args)
    if "--json" in args:
        print(json.dumps({**rep, "docs": [{k: v for k, v in d.items() if k not in ("restored", "page1")} for d in rep["docs"]]},
                         ensure_ascii=False, indent=1))
    for n in rep["notes"]:
        print(f"  [輸入] {n}")
    for d in rep["docs"]:
        cov = "—" if d.get("coverage") is None else f"{d['coverage'] * 100:.2f}%"
        print(f"  {d['lamp']:<6} {d['name']} · {STATE_ZH.get(d['state'], d['state'])} · 覆蓋 {cov} · 數字 {d.get('numbers', 0)} 缺 "
              f"{d.get('numbers_missing', 0)} · 品質 {d['quality']['grade']} {d['quality']['score']} · ENG072 首頁 "
              f"{(d.get('eng072') or {}).get('state', '—')} · 摘要 {(d.get('summary') or {}).get('state', '—')}")
    print(f"[全文無遺漏] 總判 {rep['verdict']} · {len(rep['docs'])} 件 · OCR 後端 {'在' if rep['ocr_backend'] else '缺'} · "
          f"第二讀法 {'在' if rep['second_reader'] else '缺'} · 頁 {OUT / 'TEXTCOMP_latest.html'}")
    if rep["verdict"] == "NODATA":
        return 2
    if rep["verdict"] == "RED":
        return 1
    only_absent = all(d["lamp"] == "GREEN" or d["state"] in ("IMAGE_NO_OCR", "IMAGE_TEXT_UNVERIFIED") for d in rep["docs"])
    return 0 if rep["verdict"] == "GREEN" else (3 if only_absent else 2)


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    src = "目標價 1,250 元\n毛利率 58.3%\n風險:匯率"
    cov, miss, _ = coverage(src, "目標價 1,250 元\n風險:匯率")
    segs = missing_segments(src, "目標價 1,250 元\n風險:匯率")
    chk("缺一行 → 覆蓋率掉、缺字片段指出是哪一段", cov < COVER_MIN and any("毛利率58.3%" in s["text"] for s in segs), f"{cov:.3f} · {segs[:1]}")
    chk("數字逐一核:少了 58.3% 就列出", list((numbers(src) - numbers("目標價 1,250 元")).elements()) == ["58.3%"])
    chk("順序換了不算缺(移位)", coverage("甲乙丙\n丁戊己", "丁戊己\n甲乙丙")[0] == 1.0)
    chk("全形 = 半形(NFKC)· 字間空白不算缺", coverage("１，２５０ 台積電", "1,250台 積 電")[0] == 1.0)
    chk("數字斷開接回後仍是同一個數", numbers("目標價 1, 650元") == numbers("目標價 1,650元"), dict(numbers("目標價 1, 650元")))
    fixed, rounds = repair_loop("【本文】\n聯 發 科營收４８２．５億元,年增\n１８．３%​。", "聯發科營收４８２．５億元,年增１８．３%。")
    chk("修復迭代:品質分上升、覆蓋率不降、全形轉半形、字間空白與斷行接回", rounds[-1]["score"] > rounds[0]["score"]
        and all(r["coverage"] == 1.0 for r in rounds) and "482.5" in fixed and "聯發科" in fixed and "年增18.3%" in fixed,
        " → ".join(f"{r['round'].split()[0]} {r['score']}" for r in rounds))
    bad = lambda t: t.replace("營收", "")                       # a pass that eats characters must be rolled back
    keep = PASSES
    try:
        globals()["PASSES"] = (("壞修復", bad),)
        _f, r2 = repair_loop("營收成長", "營收成長")
    finally:
        globals()["PASSES"] = keep
    chk("吃字的修復輪整輪退回", r2[-1]["kept"] is False and _f == "營收成長")
    chk("亂碼偵測(私用區 / U+FFFD / (cid:))", garbage_count("正常�(cid:12)") == 3)
    with tempfile.TemporaryDirectory() as td:
        made = make_fixtures(Path(td))
        docs = {p.name: audit_doc(p) for p in made}
        c = docs["fixture_broker_clean.pdf"]
        chk("個股報告只取第 1 頁:全覆蓋、數字零缺、綠", c["lamp"] == "GREEN" and c["coverage"] == 1.0 and c["numbers_missing"] == 0
            and len(c["pages"]) == 1 and c["pages_total"] == 2 and c["doc_type"] == "stock_report", f"{c['state']} · {c['scope']} · 數字 {c['numbers']}")
        a = docs["fixture_annual_report.pdf"]
        body = a["restored"]
        order_ok = body.index("左上表") < body.index("左下表") < body.index("右上表") < body.index("右下表")
        chk("年度財報:全部頁 · 先拆左右再拆上下(左上→左下→右上→右下)· 全覆蓋", a["doc_type"] == "annual_report" and a["lamp"] == "GREEN"
            and a["coverage"] == 1.0 and order_ok and len(a["pages"]) == 2, a["scope"])
        chk("修正後首頁分區(標題帶 · 本文 · 右資訊區 · 頁尾)", all(s in c["page1"] for s in SEC) and "目標價:1,250元" in c["page1"],
            " · ".join(ln for ln in c["page1"].splitlines() if ln.startswith("【")))
        r = docs["fixture_broker_needs_repair.pdf"]
        chk("待修樣本:REPAIRED、覆蓋 100%、品質 A/B", r["state"] == "REPAIRED" and r["coverage"] == 1.0 and r["quality"]["grade"] in ("A", "B")
            and "1,650" in r["page1"] and "482.5" in r["page1"], f"{r['quality']} · {r['pages'][0]['rounds'][-1]['round']}")
        s = docs["fixture_broker_scanned.pdf"]
        chk("掃描樣本:影像頁;沒有 OCR 就照實 IMAGE_NO_OCR(黃),有 OCR 就 OCR_RESTORED", s["state"] in ("IMAGE_NO_OCR", "OCR_RESTORED")
            and s["lamp"] == "AMBER", s["state"])
        chk("摘要閘:不完整的不摘要", summarize(s)["state"] == "SKIP")
        kv = fields(c["page1"])
        chk("首頁右資訊區 → 摘要欄位(目標價 · 評等 · 分析師 · 日期 · EPS)", kv.get("target_price") == 1250.0 and kv.get("rating") == "買進"
            and kv.get("report_date") == "20260928" and kv.get("eps_current") == 48.7 and kv.get("eps_next") == 62.5, kv)
        chk("修復:百分比小數斷開接回(49. 5% → 49.5%)", "49.5%" in r["page1"])
        fake = {"lamp": "GREEN", "state": "INTACT", "doc_type": "stock_report", "name": "x.pdf", "restored": "", "page1": "【本文】\n營收成長。"}
        sm = summarize(fake)
        chk("摘要出處核對:原文沒有的補句改成「原文未提及」(不冒充)", sm["state"] == "ABSENT" or (sm["ungrounded"] and all(
            p == "原文未提及" or norm(re.sub(r"[。.]$", "", p)) in norm("營收成長。") for p in sm["points"])), sm.get("why") or sm.get("state"))
        chk("年度財報不套個股摘要規定", summarize({**a, "lamp": "GREEN"})["state"] == "N/A")
        ENG = ENG072_OUT
        try:
            globals()["ENG072_OUT"] = Path(td)
            (Path(td) / "fixture_broker_clean.txt").write_text("【標題帶】\n" + c["page1"], encoding="utf-8")
            ok72 = eng072_check(made[0], pdf_pages(made[0])[0]["src"])["state"] == "GREEN"
            (Path(td) / "fixture_broker_clean.txt").write_text(c["page1"].replace("1,250", ""), encoding="utf-8")
            bad72 = eng072_check(made[0], pdf_pages(made[0])[0]["src"])
        finally:
            globals()["ENG072_OUT"] = ENG
        chk("ENG072 首頁輸出核對:完整 = 綠;少了目標價數字 = 紅並列出", ok72 and bad72["state"] == "RED" and "1,250" in bad72["numbers_missing"],
            bad72.get("numbers_missing"))
        dx = Path(td) / "t.docx"
        with zipfile.ZipFile(str(dx), "w") as z:
            z.writestr("word/document.xml", "<w:document><w:body><w:p><w:r><w:t>第一段 EPS 12.5</w:t></w:r></w:p>"
                                            "<w:p><w:r><w:t>第二段</w:t></w:r></w:p></w:body></w:document>")
        dd = audit_doc(dx)
        chk("docx:每個 <w:t> 都核到", dd["lamp"] == "GREEN" and dd["coverage"] == 1.0 and dd["numbers"] == 1)
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
