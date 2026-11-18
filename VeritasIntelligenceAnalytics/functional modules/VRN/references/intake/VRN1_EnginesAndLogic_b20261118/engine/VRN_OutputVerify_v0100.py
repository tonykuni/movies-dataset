#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG021 · VRN_OutputVerify_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 60；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_OutputVerify v0100 -- 輸出驗證與自動修正：每一筆輸出回原檔逐欄證明，證得出來的才進「驗證過的輸出」。

Operator 2026-10-20: 「VRN-1 自動修正直到100%正確 輸出驗證後的OUTPUT及HTML U/I」.

  read     原檔用 pypdfium2（pdfplumber 的相依；VRN-1 的擷取走 pdfplumber / PyMuPDF，這裡換一條讀法）取字元座標，
           自己排成行與字（由上到下 · 由左到右 · 不靠內容流順序）；.docx 的表格一格一字、.txt 用字元位置當座標；影像檔沒有文字層 = 不驗。
  verify   年度數據（vrn_financial_data）· 年度財報格（vrn_annual_cells）：科目那一列 → 科目後面那一段數字（並排表遇到下一個科目字就停）
           → 值那一列正上方最近的表頭 → 用 x 座標把值對到表頭那一欄（分組表頭：期間底下 新 / 舊 / 差 子欄，要在本次預估那一欄）
           → 那一欄的期間 = 這一列寫的年 / 季 才算 VERIFIED；轉置表（一列一年）用科目字在表頭的 x 範圍對值。
           代號紀錄（vrn_ticker_record）：代號 / 券商 / 分析師 / 電郵 / 電話 / 評等 / 目標價 / 公司名 / 標題逐欄回首頁原文。
           一標題四重點（vrn_summary_points）：揭露的句子要在原文裡。
  correct  能從原檔確定的才改：值在別的期間欄 → 改期間 · 取到舊值 / 共識 / 差異子欄 → 改成本次預估 · 值被截斷 / 取到別列 → 改成那一欄的值
           · Value 和原值不一致 → 照原值。改完再驗一次，證得出來才收（CORRECTED · 前 → 後寫進修正冊）。
  reject   證不出來的（科目歸類和原文對不上 · 期間字不明 · 原文找不到 · 欄位不能逐欄證明 · 影像檔）不進輸出，連理由進剔除冊 —— 不猜。
  section  （2026-10-20 操作員「工具可相互取用」）呼叫端給了段落標題的讀法（section_of：VRN-1 自己沒有，G23 向 VRN-2 借 section.near）
           → 證實過的每一筆再問「科目上方同一欄最近的段落標題」：標題是成長率 / 比率（Growth (%) · Margins (%) · YoY …）而這一列歸成
           金額科目 → 值是成長率 / 比率不是金額 → 剔除（理由 + 借來的證據）。判準是本支自己的（section_semantic）；沒給讀法 = 不查、行為不變。
  write    <round>/verified/：vrn_verified_financial_data · vrn_verified_annual_cells · vrn_verified_ticker_record ·
           vrn_verified_summary_points · vrn_output_corrections · vrn_output_rejected（.parquet + .csv UTF-8 BOM）·
           VRN_Verified_Output_v0100.json · VRN_Verified_Output_v0100.html（可篩選 · 深色模式 · 手機寬度）。

Only reads the round's dataframes and the original files; writes only under <round>/verified/.  No network.
"""

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

import csv
import hashlib
import html
import json
import re
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

VERSION = "VRN_OutputVerify v0100"
OUT_DIRNAME = "verified"
HTML_NAME = "VRN_Verified_Output_v0100.html"
JSON_NAME = "VRN_Verified_Output_v0100.json"
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
TIME_OK_RX = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")

# =====================================================================
# 1 . 原檔讀法（字元座標 → 行與字）
# =====================================================================


# [VRN-ID] VRN-ENG021-FNC001 · LOGIC
def nf(s: Any) -> str:
    return unicodedata.normalize("NFKC", "" if s is None else str(s))


# [VRN-ID] VRN-ENG021-FNC002 · LOGIC
def squash(s: Any) -> str:
    """比對用：NFKC · 小寫 · 去空白與標點（留中英數字與 % . -）。"""
    return re.sub(r"[^\w%.\-]+", "", nf(s).lower())


# [VRN-ID] VRN-ENG021-FNC003 · LOGIC
def present(v: Any) -> bool:
    return v is not None and str(v).strip() not in ("", "nan", "None", "<NA>")


# [VRN-ID] VRN-ENG021-FNC004 · LOGIC
def _pdf_page_lines(page) -> List[Dict[str, Any]]:
    tp = page.get_textpage()
    chars = []
    for i in range(tp.count_chars()):
        c = tp.get_text_range(i, 1)
        if not c or not c.strip():
            continue
        l, b, r, t = tp.get_charbox(i, loose=True)
        chars.append((nf(c), l, b, r, t))
    tp.close()
    rows: List[Dict[str, Any]] = []
    for c in sorted(chars, key=lambda x: (-(x[2] + x[4]) / 2, x[1])):
        yc, h = (c[2] + c[4]) / 2, max(c[4] - c[2], 1.0)
        for row in rows:
            if abs(row["y"] - yc) <= 0.45 * max(h, row["h"]):
                row["c"].append(c)
                break
        else:
            rows.append({"y": yc, "h": h, "c": [c]})
    lines = []
    for row in sorted(rows, key=lambda r: -r["y"]):
        words, cur, last_r = [], None, None
        for ch, l, b, r, t in sorted(row["c"], key=lambda x: x[1]):
            if cur is not None and l - last_r > 0.22 * max(t - b, 1.0):
                words.append(cur)
                cur = None
            if cur is None:
                cur = {"text": ch, "x0": l, "x1": r}
            else:
                cur["text"] += ch
                cur["x1"] = max(cur["x1"], r)
            last_r = r
        if cur:
            words.append(cur)
        lines.append({"y": row["y"], "h": row["h"], "words": words, "text": " ".join(w["text"] for w in words)})
    return lines


# [VRN-ID] VRN-ENG021-FNC005 · IO
def read_stream_text(path: Path) -> List[str]:
    """第二種讀法：pypdfium2 的內容流文字（每頁一段）。字元座標排行時，相鄰格子的字可能插進電話中間
    （凱基 2637：「88)6 2 2181 8710」），電話 / 電郵也拿內容流再對一次。非 PDF 或讀不到 → []。"""
    if path.suffix.lower() != ".pdf":
        return []
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(path))
        out = []
        for i in range(len(doc)):
            tp = doc[i].get_textpage()
            out.append(nf(tp.get_text_range()))
            tp.close()
        doc.close()
        return out
    except Exception:  # noqa: BLE001 - 第二種讀法讀不到就只用第一種
        return []


# [VRN-ID] VRN-ENG021-FNC006 · LOGIC
def _text_line(text: str, y: float) -> Dict[str, Any]:
    words = [{"text": m.group(0), "x0": float(m.start()), "x1": float(m.end())} for m in re.finditer(r"\S+", nf(text))]
    return {"y": y, "h": 1.0, "words": words, "text": " ".join(w["text"] for w in words)}


# [VRN-ID] VRN-ENG021-FNC007 · IO
def read_document(path: Path) -> Tuple[List[List[Dict[str, Any]]], str]:
    """原檔 → (每頁的行, 讀法)。讀不到 → ([], 原因)。"""
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            import pypdfium2 as pdfium  # pdfplumber 的相依（requirements-dev.txt 已有 pdfplumber）
            doc = pdfium.PdfDocument(str(path))
            pages = [_pdf_page_lines(doc[i]) for i in range(len(doc))]
            doc.close()
            return pages, "pypdfium2 字元座標"
        if suffix == ".docx":
            import docx  # python-docx
            d = docx.Document(str(path))
            lines, y = [], 0.0
            for para in d.paragraphs:
                if para.text.strip():
                    lines.append(_text_line(para.text, y))
                    y -= 1
            for table in d.tables:
                for row in table.rows:
                    cells = [nf(c.text).strip() for c in row.cells]
                    words = [{"text": c, "x0": 100.0 * k, "x1": 100.0 * k + 60} for k, c in enumerate(cells) if c]
                    if words:
                        lines.append({"y": y, "h": 1.0, "words": words, "text": " ".join(w["text"] for w in words)})
                        y -= 1
            return [lines], "python-docx（表格一格一字）"
        if suffix == ".txt":
            text = path.read_text(encoding="utf-8", errors="replace")
            return [[_text_line(ln, -k) for k, ln in enumerate(text.splitlines()) if ln.strip()]], "純文字（字元位置當座標）"
        if suffix in IMAGE_SUFFIXES:
            return [], "影像檔沒有文字層（OCR 的字不進驗證）"
        return [], "不支援的副檔名 " + suffix
    except Exception as error:  # noqa: BLE001 - 一份原檔讀不出來不該讓整輪倒掉
        return [], "%s: %s" % (error.__class__.__name__, str(error)[:120])


# =====================================================================
# 2 . 數字 · 期間 · 子欄
# =====================================================================
NUM_RX = re.compile(r"^\(?[-–−]?\d[\d,]*(?:\.\d+)?\)?%?x?$|^(?:n\.?a\.?|nm|n/a|na|-|--|–|—)$", re.I)
WORD_RX = re.compile(r"[A-Za-z一-鿿]{2,}")
PER_RX = re.compile(r"^(?:[1-4]Q\d{2}[A-Za-z]{0,2}|(?:FY)?\d{4}(?:\([A-Za-z]\)|[A-Za-z]{0,2})|FY\d{2}[AEFaef]?|\d{1,2}/\d{2}[AEFaef]?|\d{2}[AEF]|"
                    r"[A-Z][a-z]{2}-\d{2}[AEFaef]?)$")
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
SUBCOL_RX = re.compile(r"^(?:%?Diff(?:\(%\))?|Change|Chg|New|Old|Previous|Prior|Current|Cons\.?|Consensus|GS|Daiwa|Ours|"
                       r"修正後|修正前|調幅(?:\(%\))?|QoQ(?:\(%\))?|YoY(?:\(%\))?|市場共識|差異(?:\(%\))?|本次|前次|"
                       r"實際數?|實績|Actual|凱基預估|預估|Estimates?|Est\.?)$", re.I)
# 一組子欄裡「這份報告現在的數字」：修正後 / 本次 > 實際數（已公布的季）> 自家預估（沒有修正欄的那一組）。共識、修正前、差異永遠不是。
CURRENT_SUBCOL_RANK = (re.compile(r"^(?:New|Current|修正後|本次)$", re.I), re.compile(r"^(?:實際數?|實績|Actual)$", re.I),
                       re.compile(r"^(?:GS|Daiwa|Ours|凱基預估|預估|Estimates?|Est\.?)$", re.I))


# [VRN-ID] VRN-ENG021-FNC008 · LOGIC
def is_num(tok: str) -> bool:
    return bool(NUM_RX.match(nf(tok).strip()))


# [VRN-ID] VRN-ENG021-FNC009 · EXTRACT
def parse_num(s: Any) -> Optional[float]:
    t = nf(s).strip().replace("−", "-").replace("–", "-")
    neg = t.startswith("(") and (t.endswith(")") or t.endswith(")%"))
    t = t.strip("()%xX ").replace(",", "")
    if neg:
        t = "-" + t.lstrip("-")
    try:
        return float(t)
    except ValueError:
        return None


# [VRN-ID] VRN-ENG021-FNC010 · LOGIC
def decimals(s: str) -> int:
    t = nf(s).strip().rstrip("%xX)")
    return len(t.split(".")[1]) if "." in t else 0


# [VRN-ID] VRN-ENG021-FNC011 · LOGIC
def same_token(a: str, b: str) -> bool:
    """原值字面相同，或解析值相同且小數位相同（1,200 = 1200 · 6.1 ≠ 6.10 · 4.5% ≠ 4.5）。"""
    sa, sb = nf(a).replace(" ", ""), nf(b).replace(" ", "")
    if sa == sb:
        return True
    va, vb = parse_num(sa), parse_num(sb)
    return va is not None and vb is not None and va == vb and decimals(sa) == decimals(sb) and sa.endswith("%") == sb.endswith("%")


# [VRN-ID] VRN-ENG021-FNC012 · LOGIC
def canon(tok: str) -> Optional[Tuple[int, int, int]]:
    """期間字 → (年, 季 0 = 全年, 月 0 = 不是月-年欄頭)· 認不得 → None。"""
    r = nf(tok).strip().replace("(", "").replace(")", "")
    m = re.fullmatch(r"([1-4])Q(\d{2})[A-Za-z]{0,2}", r)
    if m:
        return 2000 + int(m.group(2)), int(m.group(1)), 0
    m = re.fullmatch(r"(?:FY)?(\d{4})[A-Za-z]{0,2}", r)
    if m and 1990 <= int(m.group(1)) <= 2040:
        return int(m.group(1)), 0, 0
    m = re.fullmatch(r"FY(\d{2})[A-Za-z]?", r)
    if m:
        return 2000 + int(m.group(1)), 0, 0
    m = re.fullmatch(r"(\d{1,2})/(\d{2})[A-Za-z]?", r)
    if m and 1 <= int(m.group(1)) <= 12:
        return 2000 + int(m.group(2)), 0, int(m.group(1))
    m = re.fullmatch(r"([A-Za-z]{3})-(\d{2})[A-Za-z]?", r)
    if m and m.group(1).lower() in MONTHS:
        return 2000 + int(m.group(2)), 0, MONTHS.index(m.group(1).lower()) + 1
    m = re.fullmatch(r"(\d{2})[AEF]", r)
    if m:
        return 2000 + int(m.group(1)), 0, 0
    return None


# [VRN-ID] VRN-ENG021-FNC013 · LOGIC
def header_periods(tokens: Sequence[str]) -> List[Optional[Tuple[int, int]]]:
    """表頭一列 → 每欄 (年, 季)。月-年欄頭同一列有別的月份：尾端連續、年份遞增的 12 月欄 = 全年，其餘照月份算季。"""
    cs = [canon(t) for t in tokens]
    months = [c[2] if c else 0 for c in cs]
    tail = len(cs)
    if len({m for m in months if m}) >= 2:
        while tail > 0 and months[tail - 1] == 12 and cs[tail - 1] and (tail == len(cs) or not cs[tail] or cs[tail - 1][0] < cs[tail][0]):
            tail -= 1
    out: List[Optional[Tuple[int, int]]] = []
    for i, c in enumerate(cs):
        if not c:
            out.append(None)
        elif c[2] and len({m for m in months if m}) >= 2 and i < tail:
            out.append((c[0], (c[2] + 2) // 3) if c[2] % 3 == 0 else None)
        else:
            out.append((c[0], c[1]))
    return out


# [VRN-ID] VRN-ENG021-FNC014 · LOGIC
def periods_in(line: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [w for w in line["words"] if PER_RX.match(nf(w["text"])) and canon(w["text"])]


# [VRN-ID] VRN-ENG021-FNC015 · LOGIC
def want_of(fiscal_year: Any, fiscal_quarter: Any, period_type: Any, period_raw: str) -> Optional[Tuple[int, int]]:
    """這一列自己說的 (年, 季)：FiscalYear + FiscalQuarter（YYYY-MM 季末月）優先，其次期間原文。"""
    try:
        y = int(float(fiscal_year)) if present(fiscal_year) else None
    except (TypeError, ValueError):
        y = None
    fq = nf(fiscal_quarter).strip()
    if y and re.fullmatch(r"\d{4}-(03|06|09|12)", fq):
        return y, int(fq[5:]) // 3
    if y and nf(period_type).strip() == "FY":
        return y, 0
    c = canon(period_raw)
    if c and not c[2]:
        return c[0], c[1]
    hp = header_periods([period_raw])
    return hp[0] if hp and hp[0] else ((y, 0) if y else None)


# [VRN-ID] VRN-ENG021-FNC016 · LOGIC
def period_fields(token: str, header: Sequence[str]) -> Dict[str, Any]:
    """表頭那一格 → 年度數據的期間欄（修正期間時用；季別寫成季末月 YYYY-MM）。"""
    yq = header_periods(list(header))[list(header).index(token)] if token in header else None
    flag = re.search(r"\d\s*\(?([AEFaef])\)?$", nf(token).strip())
    est = {"A": "Actual", "E": "Estimate", "F": "Estimate"}.get(flag.group(1).upper(), "") if flag else ""
    if not yq:
        return {}
    y, q = yq
    return {"PeriodLabelRaw": token, "FiscalYear": y, "FiscalQuarter": ("%d-%02d" % (y, q * 3)) if q else "",
            "PeriodType": "FQ" if q else "FY", "EstimateFlag": est}


# =====================================================================
# 3 . 一筆值回原檔那一頁
# =====================================================================
# [VRN-ID] VRN-ENG021-FNC017 · LOGIC
def find_label(line: Dict[str, Any], label: str) -> Optional[Tuple[int, int]]:
    target = squash(label)
    if not target:
        return None
    joined, starts = "", []
    for w in line["words"]:
        starts.append(len(joined))
        joined += squash(w["text"])
    pos = joined.find(target)
    if pos < 0:
        return None
    end = pos + len(target)
    s = max(i for i, st in enumerate(starts) if st <= pos)
    e = next(i for i in range(len(starts)) if starts[i] + len(squash(line["words"][i]["text"])) >= end) + 1
    return s, e


# [VRN-ID] VRN-ENG021-FNC018 · LOGIC
def value_run(words: List[Dict[str, Any]], start: int) -> Tuple[List[Dict[str, Any]], float]:
    """科目後面第一段連續的數字（並排表：遇到下一個科目字就停）→ (數字字, 下一個科目字的 x0)。"""
    out: List[Dict[str, Any]] = []
    for w in words[start:]:
        t = nf(w["text"]).strip()
        if is_num(t):
            out.append(w)
            continue
        if re.fullmatch(r"(?i)ppts?|pp|x|bps?", t):
            continue
        if re.fullmatch(r"(?i)\(?[-–−]?\d[\d,]*(?:\.\d+)?\)?(?:ppts?|pp|bps?)", t):
            out.append(w)                         # 凱基「(1.4)ppts」：數字黏著單位，是這一列的一格，不是下一個科目
            continue
        if WORD_RX.search(t):
            if out:
                return out, w["x0"]
            continue
    return out, float("inf")


# [VRN-ID] VRN-ENG021-FNC019 · LOGIC
def current_sub(names: Sequence[str]) -> Optional[int]:
    for rx in CURRENT_SUBCOL_RANK:
        hit = next((k for k, nm in enumerate(names) if rx.match(nm)), None)
        if hit is not None:
            return hit
    return None


# [VRN-ID] VRN-ENG021-FNC020 · LOGIC
def group_subs(subs: List[Dict[str, Any]], centers: Sequence[float]) -> Optional[List[List[Dict[str, Any]]]]:
    """子欄名稱 → 每個期間一組。各組大小可以不同（凱基：1Q26 底下 7 個、2Q26F 底下 7 個但名稱不同；2028F 底下只有 4 個），
    所以不是平均切：從左到右切成連續的組（每組至少 2 個），每組左右兩端的中點要對準它上面的期間字，總偏差最小的切法。
    任何一組偏離它的期間字超過期間間距的一半 → 不算分組表（None）。"""
    subs = sorted(subs, key=lambda w: w["x0"])
    n, m = len(subs), len(centers)
    if m < 1 or n < 2 * m:
        return None
    memo: Dict[Tuple[int, int], Tuple[float, Tuple[int, ...]]] = {}

    # [VRN-ID] VRN-ENG021-FNC021 · LOGIC
    def go(i: int, g: int) -> Tuple[float, Tuple[int, ...]]:
        if g == m:
            return (0.0, ()) if i == n else (float("inf"), ())
        if (i, g) not in memo:
            best = (float("inf"), ())
            for e in range(i + 2, n - 2 * (m - g - 1) + 1):
                rest = go(e, g + 1)
                cost = abs((subs[i]["x0"] + subs[e - 1]["x1"]) / 2 - centers[g]) + rest[0]
                if cost < best[0]:
                    best = (cost, (e,) + rest[1])
            memo[(i, g)] = best
        return memo[(i, g)]
    cost, ends = go(0, 0)
    if cost == float("inf"):
        return None
    groups, start = [], 0
    for e in ends:
        groups.append(subs[start:e])
        start = e
    spacing = min(b - a for a, b in zip(centers, centers[1:])) if m > 1 else 80.0
    if any(abs((grp[0]["x0"] + grp[-1]["x1"]) / 2 - c) > spacing / 2 for grp, c in zip(groups, centers)):
        return None
    return groups


# [VRN-ID] VRN-ENG021-FNC022 · LOGIC
def column_of(lines: List[Dict[str, Any]], li: int, word: Dict[str, Any], x_from: float, x_to: float) -> Optional[Dict[str, Any]]:
    """值那一列正上方最近的表頭（只看 x 在 [x_from, x_to) 之間的期間字）→ 這個值落在哪一欄（含分組子欄）。"""
    for j in range(li - 1, max(-1, li - 40), -1):
        ps = [w for w in periods_in(lines[j]) if x_from - 2 <= (w["x0"] + w["x1"]) / 2 < x_to]
        if len(ps) < 2:
            continue
        toks = [p["text"] for p in ps]
        yq = header_periods(toks)
        centers = [(p["x0"] + p["x1"]) / 2 for p in ps]
        spacing = min(b - a for a, b in zip(centers, centers[1:])) if len(centers) > 1 else 40.0
        cx = (word["x0"] + word["x1"]) / 2
        left, right = centers[0] - spacing * 0.6, centers[-1] + spacing * 0.6
        groups = None
        for s in range(j + 1, li):
            subs = [w for w in lines[s]["words"] if SUBCOL_RX.match(nf(w["text"]).replace(" ", "")) and left <= (w["x0"] + w["x1"]) / 2 <= right]
            groups = group_subs(subs, centers) if len(subs) >= 2 * len(ps) else None
            if groups:
                break
        if groups:
            flat = [((w["x0"] + w["x1"]) / 2, gk, si) for gk, grp in enumerate(groups) for si, w in enumerate(grp)]
            sc = [f[0] for f in flat]
            ssp = min(b - a for a, b in zip(sc, sc[1:])) if len(sc) > 1 else 20.0
            n = min(range(len(sc)), key=lambda q: abs(sc[q] - cx))
            if abs(sc[n] - cx) > max(4.0, ssp * 0.6):
                return {"header": toks, "line": j, "col": None, "why": "值不在任何子欄底下"}
            _c, k, si = flat[n]
            names = [[nf(w["text"]).replace(" ", "") for w in grp] for grp in groups]
            curs = [current_sub(nm) for nm in names]
            cur_x = [((groups[g][c]["x0"] + groups[g][c]["x1"]) / 2) if c is not None else None for g, c in enumerate(curs)]
            return {"header": toks, "line": j, "col": k, "token": toks[k], "yq": yq[k], "sub": names[k][si], "current": curs[k] is not None and si == curs[k],
                    "cur_index": curs[k], "group": len(groups[k]), "cur_x": cur_x}
        k = min(range(len(centers)), key=lambda q: abs(centers[q] - cx))
        if abs(centers[k] - cx) > max(6.0, spacing * 0.6):
            return {"header": toks, "line": j, "col": None, "why": "值不在任何期間欄底下"}
        return {"header": toks, "line": j, "col": k, "token": toks[k], "yq": yq[k], "centers": centers, "spacing": spacing}
    return None


# [VRN-ID] VRN-ENG021-FNC023 · LOGIC
def token_at(run: List[Dict[str, Any]], col: Dict[str, Any], want_k: int) -> Optional[str]:
    """那一列在第 want_k 欄（分組表頭：本次預估子欄）的值。"""
    if col.get("group"):
        target = col["cur_x"][want_k] if want_k < len(col["cur_x"]) else None
        if target is None:
            return None
    else:
        target = col["centers"][want_k]
    best = min(run, key=lambda w: abs((w["x0"] + w["x1"]) / 2 - target)) if run else None
    tol = (col.get("spacing") or 40.0) * 0.6 if not col.get("group") else 8.0
    if best is None or abs((best["x0"] + best["x1"]) / 2 - target) > max(6.0, tol):
        return None
    return nf(best["text"]).strip()


# [VRN-ID] VRN-ENG021-FNC024 · LOGIC
def same_row(lines: List[Dict[str, Any]], li: int, k: int, x_label: float, x_number: float) -> bool:
    """科目在第 li 行、數字在第 k 行（凱基 3665：EV/EBITDA 比它的數字低 4.6 pt，數字那一行左邊是分析師欄的人名）：
    第 k 行在科目欄（科目左緣到第一個數字之間）沒有自己的字、兩行差不到 3/4 行高、而且離第 k 行最近的科目行就是第 li 行 → 同一列。"""
    # [VRN-ID] VRN-ENG021-FNC025 · LOGIC
    def has_label(j: int) -> bool:
        return any(WORD_RX.search(nf(w["text"])) and x_label - 5 <= w["x0"] < x_number for w in lines[j]["words"])
    if has_label(k):
        return False
    dy = abs(lines[k]["y"] - lines[li]["y"])
    if dy > 0.75 * max(lines[li]["h"], lines[k]["h"]):
        return False
    return all(abs(lines[j]["y"] - lines[k]["y"]) > dy for j in range(len(lines)) if j not in (li, k) and has_label(j))


# [VRN-ID] VRN-ENG021-FNC026 · VALIDATE
def check_on_page(lines: List[Dict[str, Any]], label: str, raw: str, want: Optional[Tuple[int, int]]) -> Dict[str, Any]:
    """一頁上：ALIGNED / TRANSPOSED（證明了）· MISALIGNED / SUBCOL / NOTONROW（錯，附修正線索）· ONLINE / NOLABEL（證不了）。"""
    best: Optional[Dict[str, Any]] = None
    rank = {"ALIGNED": 0, "TRANSPOSED": 1, "SUBCOL": 2, "MISALIGNED": 3, "NOTONROW": 4, "ONLINE": 5, "NOLABEL": 6}

    # [VRN-ID] VRN-ENG021-FNC027 · LOGIC
    def keep(res):
        nonlocal best
        if best is None or rank[res["st"]] < rank[best["st"]]:
            best = res
    for li, line in enumerate(lines):
        span = find_label(line, label)
        if not span:
            continue
        run, x_next = value_run(line["words"], span[1])
        near = half = False
        if not run:                                   # 科目一行、數字差半行（側欄同一高度的字）：證得出是同一列才逐欄對，否則降級
            for k in (li - 1, li + 1):
                if 0 <= k < len(lines):
                    r2, _x = value_run(lines[k]["words"], 0)
                    if any(same_token(w["text"], raw) for w in r2):
                        half = same_row(lines, li, k, line["words"][span[0]]["x0"], r2[0]["x0"])
                        run, near = r2, not half
                        break
        x_from = line["words"][span[1] - 1]["x1"]
        hits = [w for w in run if same_token(w["text"], raw)]
        if not hits:
            col_any = column_of(lines, li, run[0], x_from, x_next) if run and want else None
            fix = None
            if col_any and want:
                yq_list = header_periods(col_any["header"])
                if want in yq_list:
                    fix = token_at(run, col_any, yq_list.index(want))
            keep({"st": "NOTONROW", "line": li, "fix_value": fix, "header": (col_any or {}).get("header"), "grouped": bool((col_any or {}).get("group")),
                  "why": "科目「%s」那一列沒有 %s（那一列：%s）" % (label, raw, " ".join(nf(w["text"]) for w in run[:14]))})
            continue
        if not want:
            keep({"st": "ONLINE", "line": li, "why": "值在科目那一列 · 這一列沒有可比的期間"})
            continue
        for w in hits:
            col = column_of(lines, li, w, x_from, x_next)
            if not col:
                keep({"st": "ONLINE", "line": li, "why": "值在科目那一列 · 上方沒有期間表頭"})
                continue
            if col.get("col") is None:
                keep({"st": "ONLINE", "line": li, "why": "值在科目那一列 · " + col["why"]})
                continue
            if near:
                keep({"st": "ONLINE", "line": li, "why": "數字和科目差半行（同一高度有別欄的字）· 欄位未證實"})
                continue
            if col["yq"] == want:
                if col.get("group") and not col.get("current"):
                    yq_list = header_periods(col["header"])
                    keep({"st": "SUBCOL", "line": li, "fix_value": token_at(run, col, yq_list.index(want)) if want in yq_list else None,
                          "header": col["header"], "why": "取到 %s 那一組的「%s」子欄（不是本次預估）" % (col["token"], col["sub"])})
                else:
                    keep({"st": "ALIGNED", "line": li, "token": col["token"], "header": col["header"],
                          "why": "表頭 %s%s%s" % (col["token"], ("「%s」欄" % col["sub"]) if col.get("group") else "",
                                                 "（數字和科目差半行，證得出是同一列）" if half else "")})
            else:
                yq_list = header_periods(col["header"])
                keep({"st": "MISALIGNED", "line": li, "token": col["token"], "header": col["header"], "grouped": bool(col.get("group")),
                      "fix_period": period_fields(col["token"], col["header"]) if not col.get("group") or col.get("current") else None,
                      "fix_value": token_at(run, col, yq_list.index(want)) if want in yq_list else None,
                      "why": "值在表頭 %s 那一欄 · 這一列寫的是 %s" % (col["token"], "%d%s" % (want[0], ("Q%d" % want[1]) if want[1] else ""))})
    if best and best["st"] in ("ALIGNED", "TRANSPOSED"):
        return best
    tr = transposed(lines, label, raw, want)
    if tr:
        return tr
    return best or {"st": "NOLABEL", "why": "這一頁找不到科目「%s」" % label}


# [VRN-ID] VRN-ENG021-FNC028 · LOGIC
def transposed(lines: List[Dict[str, Any]], label: str, raw: str, want: Optional[Tuple[int, int]]) -> Optional[Dict[str, Any]]:
    """一列一年的表：某一列以期間字開頭（可以接在左欄文字後面）· 那一列有這個值 · 值正上方表頭（可折好幾行）的字拼起來 = 科目。"""
    if not want:
        return None
    lab = squash(label)
    for li, line in enumerate(lines):
        ws = line["words"]
        for pi, pw in enumerate(ws):
            if not PER_RX.match(nf(pw["text"])) or header_periods([pw["text"]])[0] != want:
                continue
            run, _x = value_run(ws, pi + 1)
            if len(run) < 2:
                continue
            for w in run:
                if not same_token(w["text"], raw):
                    continue
                cx = (w["x0"] + w["x1"]) / 2
                half = max(8.0, min([abs((o["x0"] + o["x1"]) / 2 - cx) for o in run if o is not w] or [40.0]) / 2)
                head = []
                for j in range(max(0, li - 10), li):
                    head += [nf(h["text"]) for h in lines[j]["words"] if abs((h["x0"] + h["x1"]) / 2 - cx) <= half and not is_num(h["text"])
                             and not PER_RX.match(nf(h["text"]))]
                got = squash("".join(head))
                if lab and got and (lab in got or (got in lab and len(got) >= max(2, len(lab) * 0.6))):
                    return {"st": "TRANSPOSED", "line": li, "token": pw["text"], "why": "轉置表：%s 那一列 · 表頭「%s」" % (pw["text"], "".join(head)[:30])}
    return None


# =====================================================================
# 4 . 科目歸類（本支自己的對照：只判明顯不合，不替引擎重新歸類）
# =====================================================================
AMOUNT_METRICS = {"Revenue", "COGS", "GrossProfit", "OperatingExpense", "OperatingProfit", "NetIncome", "EPS", "TotalAssets", "TotalLiabilities",
                  "Equity", "PretaxIncome", "TargetPrice", "BookValuePerShare", "Capex", "FreeCashFlow", "OperatingCashFlow", "SharesOutstanding"}
SEMANTIC = {
    "Revenue": (r"revenue|sales|turnover|營收|營業收入|收入", r"cost|percent|growth|yoy|qoq|margin|成本|率|ev/|/sales|/revenue|/營業收入|capex|days|資產|費用|資金|other|hpc|segment"),
    "COGS": (r"cost of (sales|revenue|goods)|cogs|營業成本|銷貨成本", r"percent|margin|率"),
    "GrossProfit": (r"gross[ -]?(profit|income)|毛利", r"margin|率|growth|yoy"),
    "GrossMargin": (r"gross[ -]?(profit[ -]?)?margin|毛利率|\bgpm\b", r"營利率|淨利率|營業利益率"),
    "OperatingExpense": (r"operating expense|opex|營業費用|營運費用|sg&a|selling|r&d|研發", r"margin|率"),
    "OperatingProfit": (r"operating[ -]?(profit|income)|op\. income|\bebit\b|營業利益|營業淨利", r"margin|率|growth|yoy|cash|non[- ]?op|leverage|expense"),
    "OperatingMargin": (r"operating[ -]?(profit[ -]?)?margin|營業利益率|營益率|ebit margin|\bopm\b|op margin", r"毛利率 .*營業"),
    "PretaxIncome": (r"pre[- ]?tax|before tax|稅前", r"margin|率|eps"),
    "NetIncome": (r"net (income|profit)|稅後淨利|淨利|net earnings|net income to parent", r"margin|率|growth|yoy|retained"),
    "NetMargin": (r"net (profit |income )?margin|淨利率|純益率", r""),
    "EPS": (r"\beps\b|每股盈餘|每股稅後盈餘|每股獲利|earnings per share", r"growth|yoy|成長|vs cons|bbg|modelware|稅前|pre[- ]?tax|before tax"),
    "TotalAssets": (r"total assets|資產總額|總資產", r"growth|yoy"),
    "TotalLiabilities": (r"total liabilit|負債總額|總負債", r"/equity|equity &"),
    "Equity": (r"equity|權益|淨值", r"cost of equity|debt|/equity|liabilities|liabs|raised|minorit"),
    "TargetPrice": (r"target|目標價|\btp\b|price target", r"net profit|淨利"),
    "PER": (r"p/e|\bper\b|本益比", r"cash|operat|expense|financial|margin"),
    "PBR": (r"p/b|\bpbr\b|\bpb\b|淨值比", r""),
    "ROE": (r"\broe\b|股東權益報酬率", r""),
    "ROA": (r"\broa\b|資產報酬率", r""),
    "EV_EBITDA": (r"ev/ebitda", r"ebitdar"),
    "DividendYield": (r"yield|殖利率", r"fcf"),
    "SharesOutstanding": (r"share|股數", r""),
    "BookValuePerShare": (r"bvps|book value|每股淨值", r""),
    "OperatingCashFlow": (r"operating cash ?flow|cash ?flow from operations|營業現金流|營運現金流|\bcfo\b", r"growth|payout|debt"),
    "Capex": (r"capex|capital expenditure|資本支出", r"growth|/sales|/depreciation|/op"),
    "FreeCashFlow": (r"free cash ?flow|\bfcf\b|自由現金流", r"yield|growth|payout|ps\b|ev/"),
}


# 段落標題的種類（section_semantic）：成長率 / 比率段落底下的列，值是 % 不是金額。
# 「NT$m, %」這種混合單位的大標題底下金額與比率都有 → 不判（只判純粹的 % 段落與成長率段落）。
SECTION_GROWTH_RX = re.compile(r"(?i)growth|\byoy\b|y-o-y|\bchg\b|% ?change|change ?\(%\)|成長|增長|年增|增減|變動率")
SECTION_PCT_RX = re.compile(r"(?i)\(\s*%\s*\)|^\s*%|margins?\b|ratios?\b|returns?\b|profitability|率\s*(?:\(%\))?\s*$")
SECTION_MIXED_RX = re.compile(r"(?i)nt\$|us\$|\$|\bmn\b|\bbn\b|\bm\b|百萬|千元|億|仟元|元")
SECTION_AMOUNT_METRICS = AMOUNT_METRICS - {"TargetPrice", "SharesOutstanding"} | {"CashBegin", "CashEnd"}


# [VRN-ID] VRN-ENG021-FNC055 · LOGIC
def section_semantic(metric: str, section: str) -> Tuple[Optional[bool], str]:
    """(None = 不判, False = 不合, True = 合)：段落標題是成長率 / 比率，而這一列歸成金額科目 → 不合。"""
    sec = nf(section).strip()
    if not sec or metric not in SECTION_AMOUNT_METRICS:
        return None, ""
    if SECTION_MIXED_RX.search(sec) and not SECTION_GROWTH_RX.search(sec):
        return None, "段落標題「%s」是混合單位（金額與比率都有）· 不判" % sec
    if SECTION_GROWTH_RX.search(sec):
        return False, "段落標題「%s」底下是成長率，不是 %s 的金額" % (sec, metric)
    if SECTION_PCT_RX.search(sec):
        return False, "段落標題「%s」底下是百分比 / 比率，不是 %s 的金額" % (sec, metric)
    return True, ""


# 列標自己的括號單位（Codex PR #79 P1：Turnover (X) 是週轉率，不是營收）
LABEL_UNIT_MULT_RX = re.compile(r"[(（\[]\s*(?:x|times|倍)\s*[)）\]]", re.I)
LABEL_UNIT_PCT_RX = re.compile(r"[(（\[][^)）\]]*%[^)）\]]*[)）\]]")


# [VRN-ID] VRN-ENG021-FNC029 · LOGIC
def semantic(metric: str, raw_label: str, value_raw: str) -> Tuple[Optional[bool], str]:
    lab = nf(raw_label).lower()
    if metric in AMOUNT_METRICS and nf(value_raw).strip().endswith("%"):
        return False, "金額科目 %s 的原值是百分比 %s（成長率 / 比率列）" % (metric, value_raw)
    if metric in AMOUNT_METRICS and (LABEL_UNIT_MULT_RX.search(lab) or LABEL_UNIT_PCT_RX.search(lab)):
        return False, "列標「%s」自己寫了倍數 / 百分比單位，不是金額科目 %s" % (raw_label, metric)
    if metric not in SEMANTIC:
        return None, ""
    need, ban = SEMANTIC[metric]
    if not re.search(need, lab):
        return False, "科目「%s」不是 %s" % (raw_label, metric)
    if ban and re.search(ban, lab):
        return False, "科目「%s」是比率 / 別的科目，不是 %s" % (raw_label, metric)
    return True, ""


# =====================================================================
# 5 . 原檔快取 · 頁碼
# =====================================================================
# [VRN-ID] VRN-ENG021-CLS001 · CLASS
class Sources:
    # [VRN-ID] VRN-ENG021-FNC030 · INIT
    def __init__(self, samples: Path, focus_rows: Optional[Sequence[Dict[str, Any]]] = None) -> None:
        self.samples = Path(samples)
        self.docs: Dict[str, Tuple[List[List[Dict[str, Any]]], str]] = {}
        self.streams: Dict[str, List[str]] = {}
        self.kept: Dict[str, List[int]] = {}
        for r in focus_rows or []:
            pages = [int(x) for x in str(r.get("pages_kept") or "").split() if x.isdigit()]
            if pages:
                self.kept[Path(str(r.get("file") or "")).name] = pages

    # [VRN-ID] VRN-ENG021-FNC031 · LOGIC
    def doc(self, name: str) -> Tuple[List[List[Dict[str, Any]]], str]:
        if name not in self.docs:
            p = self.samples / name
            self.docs[name] = read_document(p) if p.is_file() else ([], "原檔不在樣本夾")
        return self.docs[name]

    # [VRN-ID] VRN-ENG021-FNC032 · LOGIC
    def stream(self, name: str) -> str:
        if name not in self.streams:
            p = self.samples / name
            self.streams[name] = read_stream_text(p) if p.is_file() else []
        return "\n".join(self.streams[name])

    # [VRN-ID] VRN-ENG021-FNC033 · LOGIC
    def candidates(self, name: str, page: Any, original: bool = False) -> List[Tuple[int, str]]:
        pages, _how = self.doc(name)
        try:
            k = int(float(page))
        except (TypeError, ValueError):
            k = 0
        out: List[Tuple[int, str]] = []
        kept = self.kept.get(name)
        if not original and kept and 1 <= k <= len(kept) and kept[k - 1] <= len(pages):
            out.append((kept[k - 1], "聚焦副本第 %d 頁 = 原檔第 %d 頁" % (k, kept[k - 1])))
        if 1 <= k <= len(pages) and k not in [o[0] for o in out]:
            out.append((k, "原檔第 %d 頁" % k))
        return out


# [VRN-ID] VRN-ENG021-FNC034 · LOGIC
def locate(src: Sources, name: str, page: Any, label: str, raw: str, want: Optional[Tuple[int, int]], original: bool = False) -> Dict[str, Any]:
    pages, how = src.doc(name)
    if not pages:
        return {"st": "NOSOURCE", "why": "原檔讀不到：" + how}
    best: Optional[Dict[str, Any]] = None
    rank = {"ALIGNED": 0, "TRANSPOSED": 1, "SUBCOL": 2, "MISALIGNED": 3, "NOTONROW": 4, "ONLINE": 5, "NOLABEL": 6}
    tried = src.candidates(name, page, original)
    for pno, basis in tried:
        r = dict(check_on_page(pages[pno - 1], label, raw, want), page=pno, basis=basis)
        if best is None or rank[r["st"]] < rank[best["st"]]:
            best = r
    if best is None or best["st"] not in ("ALIGNED", "TRANSPOSED"):
        for pno in range(1, len(pages) + 1):            # 冊上那一頁證不出來 → 全份原檔找（值對、頁碼錯的照實寫）
            if pno in [t[0] for t in tried]:
                continue
            r = check_on_page(pages[pno - 1], label, raw, want)
            if r["st"] in ("ALIGNED", "TRANSPOSED"):
                return dict(r, page=pno, basis="原檔第 %d 頁（冊上 PageNumber %s 不是這一頁）" % (pno, page), page_moved=True)
    return best or {"st": "NOLABEL", "why": "頁碼 %s 不在原檔 %d 頁內" % (page, len(pages))}


# =====================================================================
# 6 . 各表驗證 · 修正
# =====================================================================
# [VRN-ID] VRN-ENG021-FNC035 · LOGIC
def _read_table(folder: Path, name: str):
    import pandas as pd
    pq, cs = folder / (name + ".parquet"), folder / (name + ".csv")
    if pq.is_file():
        try:
            return pd.read_parquet(pq)
        except Exception:  # noqa: BLE001 - 沒有 pyarrow 就讀 CSV
            pass
    if cs.is_file():
        return pd.read_csv(cs, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    return None


# [VRN-ID] VRN-ENG021-FNC036 · LOGIC
def row_key(v: Dict[str, Any]) -> Tuple:
    """同一份報告、同一張表、同一科目、同一期間 = 同一格（修正後的重複／衝突用這個鍵判）。"""
    return (v.get("FileID"), v.get("MetricName"), v.get("MetricNameRaw"), str(v.get("FiscalYear")), v.get("FiscalQuarter"), v.get("PeriodType"),
            v.get("TableID"))


# [VRN-ID] VRN-ENG021-FNC037 · VALIDATE
def verify_financial(df, src: Sources, files: Dict[str, str], section_of: Any = None,
                     stats: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    verified, corrections, rejected = [], [], []
    records = df.to_dict("records")
    claims: Dict[Tuple, int] = {}
    for r in records:
        claims[row_key(r)] = claims.get(row_key(r), 0) + 1
    for r in records:
        name = files.get(str(r.get("FileID")), "")
        label, period, raw = nf(r.get("MetricNameRaw")).strip(), nf(r.get("PeriodLabelRaw")).strip(), nf(r.get("ValueRaw")).strip()
        base = {"table": "vrn_financial_data", "file": name, "field": "%s · %s" % (r.get("MetricName"), period), "label": label, "value": raw,
                "row": r.get("FinancialRowID")}
        if not name:
            rejected.append(dict(base, reason="找不到原檔名（FileID 對不到基本資料）", evidence=""))
            continue
        want = want_of(r.get("FiscalYear"), r.get("FiscalQuarter"), r.get("PeriodType"), period)
        if not want:
            rejected.append(dict(base, reason="期間字不明（%s）· VRN-1 自己標 %s" % (period or "空白", r.get("ValidationStatus")), evidence=r.get("SourceText", "")))
            continue
        ok, why = semantic(str(r.get("MetricName") or ""), label, raw)
        if ok is False:
            rejected.append(dict(base, reason="科目歸類和原文對不上", evidence=why))
            continue
        pv = parse_num(raw)
        fixed: Dict[str, Any] = {}
        notes = []
        try:
            value_ok = pv is not None and present(r.get("Value")) and abs(pv - float(r["Value"])) <= 1e-9 * max(1.0, abs(pv))
        except (TypeError, ValueError):
            value_ok = False
        if pv is not None and not value_ok:
            fixed["Value"] = pv
            notes.append("Value %s → %s（照原值 %s）" % (r.get("Value"), pv, raw))
        res = locate(src, name, r.get("PageNumber"), label, raw, want)
        st = res["st"]
        if st in ("ALIGNED", "TRANSPOSED"):
            out = dict(r, **fixed)
            out.update(VerifyFile=name, VerifyStatus="CORRECTED" if fixed else "VERIFIED", VerifyPage=res.get("page"), VerifyColumn=res.get("token", ""),
                       VerifyNote=res["why"] + " · " + res.get("basis", ""))
            verified.append(out)
            for n in notes:
                corrections.append(dict(base, kind="VALUE", before=str(r.get("Value")), after=str(fixed.get("Value")), reason=n, evidence=res["why"]))
            continue
        # 能從原檔確定的才改，改完再驗一次
        cand = None
        kind, res2 = "", res

        # [VRN-ID] VRN-ENG021-FNC038 · LOGIC
        def by_value(nv):
            again = locate(src, name, r.get("PageNumber"), label, nv, want)
            if again["st"] != "ALIGNED":
                return None
            c = dict(r, ValueRaw=nv, Value=parse_num(nv))
            c["SourceText"] = "%s | %s | %s" % (label, period, nv)
            return c, ("SUBCOLUMN" if st == "SUBCOL" or res.get("grouped") else "VALUE"), again, "值 %s → %s（%s）" % (raw, nv, res["why"])

        # [VRN-ID] VRN-ENG021-FNC039 · LOGIC
        def by_period(fp):
            want2 = (fp["FiscalYear"], int(fp["FiscalQuarter"][5:]) // 3 if fp["FiscalQuarter"] else 0)
            again = locate(src, name, r.get("PageNumber"), label, raw, want2)
            if again["st"] != "ALIGNED":
                return None
            c = dict(r, **fixed, **fp)
            c["SourceText"] = "%s | %s | %s" % (label, fp["PeriodLabelRaw"], raw)
            return c, "PERIOD", again, "期間 %s → %s（值 %s 在表頭 %s 那一欄）" % (period, fp["PeriodLabelRaw"], raw, fp["PeriodLabelRaw"])
        fv = res.get("fix_value") if res.get("fix_value") and is_num(res["fix_value"]) and parse_num(res["fix_value"]) is not None else None
        tries = []
        if st == "MISALIGNED":
            # 值在別的期間欄：這一列的期間另有別列也在講 → 改期間（值是對的，只是掛錯欄）；沒有別列 → 先補這一列自己那一欄的值（凱基 1Q26）
            tries = [("p", res.get("fix_period")), ("v", fv)] if claims.get(row_key(r), 0) > 1 else [("v", fv), ("p", res.get("fix_period"))]
        elif st in ("SUBCOL", "NOTONROW"):
            tries = [("v", fv)]
        for how, arg in tries:
            got = (by_value(arg) if how == "v" else by_period(arg)) if arg else None
            if got:
                cand, kind, res2, note = got
                notes.append(note)
                break
        if cand is not None:
            cand.update(VerifyFile=name, VerifyStatus="CORRECTED", VerifyPage=res2.get("page"), VerifyColumn=res2.get("token", ""),
                        VerifyNote=res2["why"] + " · 自動修正：" + "；".join(notes))
            verified.append(cand)
            corrections.append(dict(base, kind=kind, before="%s @ %s" % (raw, period), after="%s @ %s" % (cand["ValueRaw"], cand["PeriodLabelRaw"]),
                                    reason="；".join(notes), evidence=res2["why"] + " · " + res2.get("basis", "")))
            continue
        reason = {"MISALIGNED": "對位不符（值在別的期間欄，改不回來）", "SUBCOL": "分組表取到舊值 / 共識 / 差異子欄（本次預估那一格讀不到）",
                  "NOTONROW": "科目那一列沒有這個值", "ONLINE": "值在原文那一列，但欄位不能逐欄證明", "NOLABEL": "原檔找不到這個科目",
                  "NOSOURCE": "原檔讀不到"}.get(st, st)
        rejected.append(dict(base, reason=reason, evidence="%s · %s" % (res.get("why", ""), res.get("basis", ""))))
    # 修正出來的列若和已證實的列同鍵同值 → 重複，不留；同鍵不同值 → 衝突，剔除修正那一筆
    seen: Dict[Tuple, str] = {}
    out_rows = []
    for v in sorted(verified, key=lambda x: 0 if x["VerifyStatus"] == "VERIFIED" else 1):
        key = row_key(v)
        if key in seen:
            if seen[key] != str(v.get("ValueRaw")) and v["VerifyStatus"] == "CORRECTED":
                rejected.append({"table": "vrn_financial_data", "file": files.get(str(v.get("FileID")), ""), "field": "%s · %s" % (v.get("MetricName"), v.get("PeriodLabelRaw")),
                                 "label": v.get("MetricNameRaw"), "value": v.get("ValueRaw"), "row": v.get("FinancialRowID"),
                                 "reason": "修正後和已證實的另一筆同期間不同值", "evidence": "已證實的值 %s" % seen[key]})
            continue
        seen[key] = str(v.get("ValueRaw"))
        out_rows.append(v)
    if section_of is not None:
        out_rows = section_pass(out_rows, rejected, src, section_of, stats if stats is not None else {})
    return out_rows, corrections, rejected


# [VRN-ID] VRN-ENG021-FNC056 · LOGIC
def section_pass(rows: List[Dict[str, Any]], rejected: List[Dict[str, Any]], src: Sources, section_of: Any,
                 stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """證實過的每一筆再問段落標題（section_of 是借來的讀法）· 判準 section_semantic 是本支的 · 讀法自己倒了 = 不判（不剔除、記錯誤數）。"""
    keep: List[Dict[str, Any]] = []
    stats.update({"checked": 0, "found": 0, "with_section": 0, "rejected": 0, "errors": 0, "error_example": "", "reader": ""})
    memo: Dict[Tuple, Dict[str, Any]] = {}
    for v in rows:
        name, label, raw = nf(v.get("VerifyFile")), nf(v.get("MetricNameRaw")).strip(), nf(v.get("ValueRaw")).strip()
        pdf = src.samples / name
        if not name or pdf.suffix.lower() != ".pdf" or not pdf.is_file():
            keep.append(v)
            continue
        k = (name, str(v.get("VerifyPage")), label, raw)
        if k not in memo:
            try:
                memo[k] = dict(section_of(pdf, int(float(v.get("VerifyPage"))), label, raw) or {})
            except Exception as error:  # noqa: BLE001 - 借來的讀法倒了不該讓證實過的列被剔除：沒讀到 = 不判
                memo[k] = {"error": "%s: %s" % (error.__class__.__name__, error)}
        got = memo[k]
        stats["checked"] += 1
        if got.get("error"):
            stats["errors"] += 1
            stats["error_example"] = stats["error_example"] or str(got["error"])[:160]
            keep.append(v)
            continue
        stats["reader"] = stats["reader"] or str(got.get("reader", ""))
        if not got.get("found"):
            keep.append(v)
            continue
        stats["found"] += 1
        sec = nf(got.get("section")).strip()
        if sec:
            stats["with_section"] += 1
        ok, why = section_semantic(str(v.get("MetricName") or ""), sec)
        if ok is False:
            stats["rejected"] += 1
            rejected.append({"table": "vrn_financial_data", "file": name, "field": "%s · %s" % (v.get("MetricName"), v.get("PeriodLabelRaw")),
                             "label": label, "value": raw, "row": v.get("FinancialRowID"),
                             "reason": "段落標題對不上（成長率 / 比率段落底下的值歸成金額科目）",
                             "evidence": "%s · 第 %s 頁 · %s · %s" % (why, v.get("VerifyPage"), got.get("how", ""), got.get("reader", ""))})
            continue
        if sec:
            v = dict(v, VerifyNote=nf(v.get("VerifyNote")) + " · 段落標題「%s」" % sec)
        keep.append(v)
    return keep


# [VRN-ID] VRN-ENG021-FNC040 · VALIDATE
def verify_annual(df, src: Sources) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    verified, rejected = [], []
    for r in df.to_dict("records"):
        name, label, period, raw = str(r.get("file") or ""), nf(r.get("label_raw")).strip(), nf(r.get("period_raw")).strip(), nf(r.get("printed_raw")).strip()
        base = {"table": "vrn_annual_cells", "file": name, "field": "%s · %s" % (label, period), "label": label, "value": raw, "row": r.get("seq")}
        want = want_of(None, None, None, period)
        res = locate(src, name, r.get("page"), label, raw, want, original=True)
        pv, cv = parse_num(r.get("printed_clean")), r.get("value")
        try:
            vok = pv is None or not present(cv) or abs(pv - float(cv)) <= 1e-9 * max(1.0, abs(pv))
        except (TypeError, ValueError):
            vok = False
        if res["st"] in ("ALIGNED", "TRANSPOSED") and vok:
            verified.append(dict(r, VerifyStatus="VERIFIED", VerifyPage=res.get("page"), VerifyColumn=res.get("token", ""), VerifyNote=res["why"]))
        else:
            rejected.append(dict(base, reason=("value 和原值不一致" if not vok else {"ONLINE": "值在原文那一列，但欄位不能逐欄證明", "NOLABEL": "原檔找不到這個科目",
                                                                                    "NOTONROW": "科目那一列沒有這個值", "MISALIGNED": "對位不符",
                                                                                    "NOSOURCE": "原檔讀不到"}.get(res["st"], res["st"])),
                                 evidence="%s · %s" % (res.get("why", ""), res.get("basis", ""))))
    return verified, rejected


BROKER_ALIAS = {"MEGA": "兆豐|mega", "KGI": "凱基|kgi", "CTBC": "中信|中國信託|ctbc", "HUANAN": "華南|huanan|entrust", "MS": "morgan stanley|摩根士丹利|^ms-",
                "GS": "goldman|高盛|^gs-", "JPM": "j\\.?p\\.? ?morgan|摩根大通|jpmorgan|^jp-", "UBS": "ubs|瑞銀", "CITI": "citi|花旗", "DAIWA": "daiwa|大和",
                "CLSA": "clsa|里昂|cl-sec|^clst", "MACQUARIE": "macquarie|麥格理|^mq-", "CATHAY": "國泰|cathay", "PRESIDENT": "統一|president",
                "TAISHIN": "台新|taishin", "CAPITAL": "群益|capital", "GF": "廣發|gf ", "YUANTA": "元大|yuanta", "FUBON": "富邦|fubon",
                "SINOPAC": "永豐|sinopac", "NOMURA": "nomura|野村", "BOFA": "bofa|美銀|merrill", "HSBC": "hsbc|匯豐"}
TP_LABEL_RX = re.compile(r"target|目標價|目標|\btp\b|\bpt\b|price objective|價格目標", re.I)
RECORD_FIELDS = ("ticker", "broker", "analyst", "email", "tel", "rating", "target_price_original", "name", "title")


# [VRN-ID] VRN-ENG021-FNC041 · LOGIC
def _phones(text: str) -> List[str]:
    out = []
    for m in re.finditer(r"(?<![\w.,])(?:\+?886[\s\-.]?\(?0?\d{1,2}\)?|\(?0\d{1,2}\)?)[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}(?:\s*(?:ext\.?|#|分機)\s*\d+)?", text, re.I):
        grp = re.findall(r"\d+", m.group(0))
        if sum(1 for g in grp if len(g) == 4 and 1990 <= int(g) <= 2040) >= 2:
            continue                                  # 表頭的連續年份（2022 2023 2024）不是電話
        out.append(re.sub(r"\D", "", m.group(0)))
    return out


# [VRN-ID] VRN-ENG021-FNC058 · LOGIC
def _ticker_rx(s: str) -> "re.Pattern[str]":
    """代號在「代號的位置」上（Codex PR #79 P2）：報告裡四位數到處都是 —— 年份、價格、表格值、電話。
    只認帶交易所 / 平台記號的（2330.TW · 2330 TT · 6669TT · 2330-TW）、括號裡的（奇鋐(3017)）、「代號 / 股號」後面的。"""
    t = re.escape(s)
    return re.compile(r"(?<![0-9A-Za-z])%s\s*[.\-]?\s*(?:TWO|TW|TT)(?![A-Za-z])|[(（]\s*%s\s*(?:[.\-\s]*(?:TWO|TW|TT))?\s*[)）]"
                      r"|(?:股票代號|代號|代碼|股號|stock code|ticker)\s*[:：]?\s*%s(?!\d)" % (t, t, t), re.I)


# [VRN-ID] VRN-ENG021-FNC042 · VALIDATE
def verify_record(df, src: Sources) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    verified, rejected = [], []
    for r in df.to_dict("records"):
        name = str(r.get("file") or "")
        pages, how = src.doc(name)
        out = dict(r)
        notes = {}
        first = "\n".join(ln["text"] for pg in pages[:2] for ln in pg)
        allt = "\n".join(ln["text"] for pg in pages for ln in pg)
        fn = nf(name)

        # [VRN-ID] VRN-ENG021-FNC043 · LOGIC
        def fail(field, why):
            rejected.append({"table": "vrn_ticker_record", "file": name, "field": field, "label": field, "value": r.get(field), "row": name,
                             "reason": "代號紀錄這一欄證不出來", "evidence": why})
            out[field] = None
            out[field + "_state"] = "REJECTED"
        for field in RECORD_FIELDS:
            v = r.get(field)
            if not present(v):
                continue
            if not pages:
                fail(field, "原檔讀不到：" + how)
                continue
            s = str(v)
            if field == "ticker":
                ok = bool(re.search(r"(?<!\d)%s(?!\d)" % re.escape(s), fn) or _ticker_rx(s).search(allt) or _ticker_rx(s).search(src.stream(name)))
                why = "代號 %s 不在檔名（獨立的一段）也不在原文的代號位置（%s.TW · %s TT · (%s) · 代號 %s）" % (s, s, s, s, s)
            elif field == "broker":
                al = BROKER_ALIAS.get(s.upper())
                ok = bool(al) and bool(re.search(al, fn.lower()) or re.search(al, allt.lower(), re.M))
                why = "檔名與原文都沒有 %s 的字樣" % s if al else "沒有 %s 的別名可對" % s
            elif field in ("analyst", "name"):
                bad = [x for x in re.split(r"\s*\|\s*", s) if x.strip() and squash(x) not in squash(allt) and squash(x) not in squash(fn)]
                ok, why = not bad, "原文 / 檔名找不到 " + "、".join(bad)
            elif field == "email":
                flat = (allt + "\n" + src.stream(name)).lower().replace(" ", "")
                flat2 = re.sub(r"[%­​]", "", flat)
                bad = [x for x in re.split(r"[\s|;,]+", s) if x and x.lower() not in flat and x.lower() not in flat2]
                ok, why = not bad, "原文找不到 " + "、".join(bad)
            elif field == "tel":
                want = re.sub(r"\D", "", s)
                norm = lambda d: d[3:].lstrip("0") if d.startswith("886") else d.lstrip("0")   # noqa: E731
                ph = _phones(allt) + _phones(src.stream(name))
                ok = any(norm(want) == norm(p) or (norm(p).startswith(norm(want)) and len(norm(want)) >= 8) for p in ph)
                why = "原文沒有 %s 這支電話（原文的電話：%s）" % (s, "、".join(sorted(set(ph))[:4]) or "無")
            elif field == "rating":
                ok = squash(s) in squash(first) or squash(s) in squash(fn) or squash(s) in squash(allt)
                why = "評等「%s」不在原文" % s
            elif field == "target_price_original":
                try:
                    x = float(s)
                except ValueError:
                    x = None
                ok = False
                lines = [ln["text"] for pg in pages[:3] for ln in pg]
                for i, ln in enumerate(lines):
                    win = " ".join(lines[max(0, i - 1): i + 2])
                    if x is not None and (TP_LABEL_RX.search(ln) or TP_LABEL_RX.search(win)):
                        if any(parse_num(tok) == x and not tok.endswith("%") for tok in re.findall(r"\(?[-–−]?\d[\d,]*(?:\.\d+)?\)?%?", nf(ln))):
                            ok = True
                            break
                why = "前 3 頁「目標價」字樣旁沒有 %s" % s
            else:                                     # title
                parts = [x.strip(" -–—:") for x in re.split(r"\s+[-–—]\s+", s) if x.strip(" -–—:")]
                junk = [x for x in parts if re.fullmatch(r"[+\d\s()\-.]{7,}", x) or squash(x) in (squash(r.get("analyst") or "@@"), squash(r.get("email") or "@@"))
                        or re.search(r"(?i)\bequity analyst\b|\bcfa\b|@", x)]
                miss = [x for x in parts if squash(x) not in squash(first)]
                ok = not junk and not miss
                why = ("標題放的是電話 / 分析師 / 電郵：" + "、".join(junk)) if junk else ("標題這幾段不在首兩頁原文：" + "、".join(miss))
            if ok:
                notes[field] = "原文"
            else:
                fail(field, why)
        out["VerifyStatus"] = "VERIFIED" if not any(x["file"] == name and x["table"] == "vrn_ticker_record" for x in rejected) else "VERIFIED_PARTIAL"
        out["VerifyNote"] = "逐欄回首頁原文：" + "、".join(sorted(notes)) if notes else ""
        verified.append(out)
    return verified, rejected


# 組合段落要拿得出「依序的原文證據」（Codex PR #79 P1）：本來只問每個字詞在原文某處 —— 集合丟了順序、遠近與次數，
# 拿頁上常見字重排的句子也會過。現在這一段要能從頭到尾切成**同一頁**原文裡的連續片段（每段在那一頁兩種讀法之一裡一字不差），
# 帶數字的片段至少 TILE_NUM_MIN 字（數字不能單獨從別處搬來），三段以上時短片段（< TILE_SHORT 字）合計不過全段的 TILE_SHORT_SHARE。
TILE_SHORT, TILE_SHORT_SHARE, TILE_NUM_MIN = 8, 0.25, 8


# [VRN-ID] VRN-ENG021-FNC059 · LOGIC
def _page_hays(pages: List[List[Dict[str, Any]]], streams: Sequence[str]) -> List[str]:
    """每頁一條比對字串：字元座標排行 + \\x00 + 內容流（各自 squash；\\x00 擋住片段跨讀法）。"""
    return [squash("".join(ln["text"] for ln in pg)) + "\x00" + (squash(streams[k]) if k < len(streams) else "") for k, pg in enumerate(pages)]


# [VRN-ID] VRN-ENG021-FNC060 · LOGIC
def _tiles(t: str, hay: str) -> Optional[List[str]]:
    """t 從頭切成 hay 裡的連續片段，每次取最長的（hay 的子字串封閉 → 片段數最少）。切不動 → None。"""
    out, i = [], 0
    while i < len(t):
        lo, hi = 0, len(t) - i
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if t[i:i + mid] in hay:
                lo = mid
            else:
                hi = mid - 1
        if lo == 0:
            return None
        out.append(t[i:i + lo])
        i += lo
    return out


# [VRN-ID] VRN-ENG021-FNC061 · LOGIC
def tile_summary_text(t: str, hays: Sequence[str]) -> Dict[str, Any]:
    """squash 過的段落 → 在哪一頁拼得出來：{"ok", "page", "pieces", "why"}。過得了的頁裡取片段最少的；都不過 → 片段最少那頁的理由。"""
    if not t:
        return {"ok": False, "page": 0, "pieces": [], "why": "這一段沒有可比對的字"}
    tried: List[Dict[str, Any]] = []
    for k, hay in enumerate(hays, start=1):
        pieces = _tiles(t, hay)
        if pieces is None:
            continue
        bare = [x for x in pieces if re.search(r"\d", x) and len(x) < TILE_NUM_MIN]
        short = sum(len(x) for x in pieces if len(x) < TILE_SHORT)
        why = ""
        if bare:
            why = "第 %d 頁：數字片段沒有上下文（%s）" % (k, "、".join(bare[:4]))
        elif len(pieces) > 2 and short > TILE_SHORT_SHARE * len(t):
            why = "第 %d 頁：%d 段裡短片段占 %d%%（字詞是從頁上各處湊的）" % (k, len(pieces), round(100 * short / max(1, len(t))))
        tried.append({"ok": not why, "page": k, "pieces": pieces, "why": why})
    if not tried:
        return {"ok": False, "page": 0, "pieces": [], "why": "沒有一頁拼得出這一段（片段散在不同頁 / 原文沒有）"}
    tried.sort(key=lambda x: (not x["ok"], len(x["pieces"])))
    return tried[0]


# [VRN-ID] VRN-ENG021-FNC045 · VALIDATE
def verify_summary(df, src: Sources, record: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    verified, rejected = [], []
    src_pages: Dict[str, List[str]] = {}
    for r in df.to_dict("records"):
        name, text = str(r.get("file") or ""), nf(r.get("text")).strip()
        pages, how = src.doc(name)
        stream = src.stream(name)                 # 第二種讀法（內容流）：投影片轉的 PDF 字元框重疊，排行會把字攪在一起（台新：「報報報 用」）
        allt = squash("".join(ln["text"] for pg in pages for ln in pg)) + "\x00" + squash(stream)
        base = {"table": "vrn_summary_points", "file": name, "field": "重點 %s" % r.get("point_no"), "label": "重點 %s" % r.get("point_no"), "value": text[:80], "row": r.get("point_no")}
        if str(r.get("disclosed") or "") != "Y" or not text or text == "未揭露":
            verified.append(dict(r, VerifyStatus="NOT_DISCLOSED", VerifyNote="報告沒揭露（照實留空）"))
            continue
        if not pages:
            rejected.append(dict(base, reason="原檔讀不到", evidence=how))
            continue
        if "(DERIVED)" in text:
            nums = [parse_num(x) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", text.split("上漲空間")[0])]
            have_n = {parse_num(x) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", "\n".join(ln["text"] for pg in pages for ln in pg))}
            ok = all(n in have_n for n in nums if n is not None)        # 評等 / 目標價的數字在原文（上漲空間是算的，不比）
            if ok:
                verified.append(dict(r, VerifyStatus="VERIFIED", VerifyNote="推算的那一句：評等 / 目標價在原文 · 上漲空間是算的"))
            else:
                rejected.append(dict(base, reason="推算句的數字不在原文", evidence=text[:120]))
            continue
        if squash(text) in allt:
            verified.append(dict(r, VerifyStatus="VERIFIED", VerifyNote="句子在原文"))
            continue
        # 首頁好幾欄拼起來的段落（欄序交錯，整句比不到）：要能切成同一頁原文的連續片段（見 tile_summary_text）
        tile = tile_summary_text(squash(text), src_pages.setdefault(name, _page_hays(pages, src.streams.get(name, []))))
        if tile["ok"]:
            verified.append(dict(r, VerifyStatus="VERIFIED", VerifyNote="組合段落：第 %d 頁 %d 段原文依序拼成（首頁多欄拼成，欄序不同）" % (tile["page"], len(tile["pieces"]))))
        else:
            rejected.append(dict(base, reason="這一段拼不出同一頁的原文片段", evidence="%s · %s" % (tile["why"], text[:80])))
    return verified, rejected


# =====================================================================
# 7 . 寫出 · HTML U/I
# =====================================================================
# [VRN-ID] VRN-ENG021-FNC046 · LOGIC
def _write_table(folder: Path, name: str, rows: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> Dict[str, Any]:
    import pandas as pd
    df = pd.DataFrame(rows, columns=columns) if columns else pd.DataFrame(rows)
    df.to_csv(folder / (name + ".csv"), index=False, encoding="utf-8-sig")
    parquet = ""
    try:
        df.astype({c: "string" for c in df.columns if df[c].dtype == object}).to_parquet(folder / (name + ".parquet"), index=False)
        parquet = str(folder / (name + ".parquet"))
    except Exception as error:  # noqa: BLE001 - 沒有 pyarrow：只寫 CSV（照實記下）
        (folder / (name + ".parquet")).unlink(missing_ok=True)   # 上一次的 Parquet 跟這一次的 CSV 對不上 → 不留
        parquet = "（沒寫 Parquet：%s）" % error.__class__.__name__
    return {"rows": len(df), "csv": str(folder / (name + ".csv")), "parquet": parquet}


# [VRN-ID] VRN-ENG021-FNC047 · LOGIC
def fingerprint(rows: List[Dict[str, Any]], keys: Sequence[str]) -> str:
    h = hashlib.sha256()
    for r in sorted("\x1f".join(str(r.get(k, "")) for k in keys) for r in rows):
        h.update((r + "\x1e").encode("utf-8"))
    return h.hexdigest()[:16]


# [VRN-ID] VRN-ENG021-FNC048 · VALIDATE
def verify_round(round_dir: Path, samples: Path, focus_rows: Optional[Sequence[Dict[str, Any]]] = None, title: str = "",
                 section_of: Any = None, section_tool: str = "") -> Dict[str, Any]:
    """一輪的 dataframes → 驗證 · 修正 · 剔除 → <round>/verified/。回摘要（寫給閘與 MAIN 報告）。
    section_of（可不給）：段落標題的讀法 section_of(pdf, page, label, value) → {section, found, how, reader}；section_tool 是它的來歷（寫進摘要）。"""
    round_dir, samples = Path(round_dir), Path(samples)
    dfdir = round_dir / "dataframes"
    folder = round_dir / OUT_DIRNAME
    folder.mkdir(parents=True, exist_ok=True)
    if focus_rows is None:
        fj = round_dir / "focus" / "vrn_focus_files.json"
        try:
            focus_rows = json.loads(fj.read_text(encoding="utf-8")) if fj.is_file() else []
        except (OSError, ValueError):
            focus_rows = []
    src = Sources(samples, focus_rows)
    basic = _read_table(dfdir, "vrn_basic_info")
    files = {str(r["FileID"]): str(r["SourceFileName"]) for r in basic.to_dict("records")} if basic is not None else {}
    out: Dict[str, Any] = {"version": VERSION, "round": str(round_dir), "samples": str(samples), "folder": str(folder), "tables": {}}
    fin = _read_table(dfdir, "vrn_financial_data")
    ann = _read_table(dfdir, "vrn_annual_cells")
    rec = _read_table(dfdir, "vrn_ticker_record")
    summ = _read_table(dfdir, "vrn_summary_points")
    sec_stats: Dict[str, Any] = {}
    v_fin, corr, rej = verify_financial(fin, src, files, section_of, sec_stats) if fin is not None else ([], [], [])
    v_ann, rej_a = verify_annual(ann, src) if ann is not None else ([], [])
    v_rec, rej_r = verify_record(rec, src) if rec is not None else ([], [])
    v_sum, rej_s = verify_summary(summ, src, {r["file"]: r for r in v_rec}) if summ is not None else ([], [])
    rejected = rej + rej_a + rej_r + rej_s
    # 時間欄位：驗證過的輸出也照操作員的三形（P23 同一條規則）
    for v in v_fin:
        fq = nf(v.get("FiscalQuarter")).strip()
        if fq and not TIME_OK_RX.match(fq):
            v["FiscalQuarter"] = ""
    written = {}
    written["vrn_verified_financial_data"] = _write_table(folder, "vrn_verified_financial_data", v_fin,
                                                         (list(fin.columns) + ["VerifyStatus", "VerifyPage", "VerifyColumn", "VerifyNote"]) if fin is not None else None)
    written["vrn_verified_annual_cells"] = _write_table(folder, "vrn_verified_annual_cells", v_ann,
                                                       (list(ann.columns) + ["VerifyStatus", "VerifyPage", "VerifyColumn", "VerifyNote"]) if ann is not None else None)
    written["vrn_verified_ticker_record"] = _write_table(folder, "vrn_verified_ticker_record", v_rec,
                                                        (list(rec.columns) + ["VerifyStatus", "VerifyNote"]) if rec is not None else None)
    written["vrn_verified_summary_points"] = _write_table(folder, "vrn_verified_summary_points", v_sum,
                                                         (list(summ.columns) + ["VerifyStatus", "VerifyNote"]) if summ is not None else None)
    written["vrn_output_corrections"] = _write_table(folder, "vrn_output_corrections", corr,
                                                    ["table", "file", "field", "label", "value", "row", "kind", "before", "after", "reason", "evidence"])
    written["vrn_output_rejected"] = _write_table(folder, "vrn_output_rejected", rejected, ["table", "file", "field", "label", "value", "row", "reason", "evidence"])
    total_in = {"vrn_financial_data": len(fin) if fin is not None else 0, "vrn_annual_cells": len(ann) if ann is not None else 0,
                "vrn_ticker_record": len(rec) if rec is not None else 0, "vrn_summary_points": len(summ) if summ is not None else 0}
    rec_fields = sum(1 for r in (rec.to_dict("records") if rec is not None else []) for f in RECORD_FIELDS if present(r.get(f)))
    out.update({
        "tables": written,
        "counts": {
            "financial": {"in": total_in["vrn_financial_data"], "verified": sum(1 for v in v_fin if v["VerifyStatus"] == "VERIFIED"),
                          "corrected": sum(1 for v in v_fin if v["VerifyStatus"] == "CORRECTED"), "rejected": len(rej)},
            "annual": {"in": total_in["vrn_annual_cells"], "verified": len(v_ann), "rejected": len(rej_a)},
            "record": {"in_fields": rec_fields, "verified_fields": rec_fields - len(rej_r), "rejected_fields": len(rej_r), "reports": len(v_rec)},
            "summary": {"in": total_in["vrn_summary_points"], "verified": sum(1 for v in v_sum if v["VerifyStatus"] == "VERIFIED"),
                        "not_disclosed": sum(1 for v in v_sum if v["VerifyStatus"] == "NOT_DISCLOSED"), "rejected": len(rej_s)},
        },
        "reasons": dict(Counter("%s · %s" % (x["table"], x["reason"]) for x in rejected).most_common()),
        "corrections_by_kind": dict(Counter(c["kind"] for c in corr)),
        "fingerprint": fingerprint(v_fin, ("FileID", "MetricName", "MetricNameRaw", "FiscalYear", "FiscalQuarter", "ValueRaw")),
        "section_check": dict(sec_stats, tool=section_tool) if section_of is not None else {"tool": "", "why": "沒有段落標題的讀法（沒借到 · 不查）"},
        "sources": {k: v[1] for k, v in src.docs.items()},
    })
    (folder / JSON_NAME).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    write_html(folder / HTML_NAME, out, v_fin, v_ann, v_rec, v_sum, corr, rejected, title)
    out["html"] = str(folder / HTML_NAME)
    out["json"] = str(folder / JSON_NAME)
    return out


# [VRN-ID] VRN-ENG021-FNC049 · LOGIC
def _slim(rows: List[Dict[str, Any]], keys: Sequence[str]) -> List[List[str]]:
    return [["" if not present(r.get(k)) else str(r.get(k)) for k in keys] for r in rows]


FIN_COLS = ("VerifyFile", "TW_TICKER", "Broker", "MetricName", "MetricNameRaw", "PeriodLabelRaw", "FiscalYear", "FiscalQuarter", "PeriodType", "EstimateFlag",
            "ValueRaw", "Value", "Unit", "VerifyStatus", "VerifyPage", "VerifyColumn", "VerifyNote")
ANN_COLS = ("file", "page", "label_raw", "metric", "period_raw", "printed_raw", "value", "unit", "VerifyStatus", "VerifyColumn", "VerifyNote")
REC_COLS = ("file", "ticker", "name", "broker", "analyst", "email", "tel", "rating", "target_price_original", "title", "VerifyStatus", "VerifyNote")
SUM_COLS = ("file", "point_no", "header", "text", "VerifyStatus", "VerifyNote")
COR_COLS = ("table", "file", "field", "kind", "before", "after", "reason", "evidence")
REJ_COLS = ("table", "file", "field", "value", "reason", "evidence")


# [VRN-ID] VRN-ENG021-FNC050 · IO
def write_html(path: Path, summary: Dict[str, Any], v_fin, v_ann, v_rec, v_sum, corr, rejected, title: str = "") -> None:
    c = summary["counts"]
    tabs = [("fin", "年度數據（驗證過）", FIN_COLS, _slim(v_fin, FIN_COLS)), ("ann", "年度財報格", ANN_COLS, _slim(v_ann, ANN_COLS)),
            ("rec", "代號紀錄", REC_COLS, _slim(v_rec, REC_COLS)), ("sum", "一標題四重點", SUM_COLS, _slim(v_sum, SUM_COLS)),
            ("cor", "自動修正（前 → 後）", COR_COLS, _slim(corr, COR_COLS)), ("rej", "剔除（不進輸出 · 附理由）", REJ_COLS, _slim(rejected, REJ_COLS))]
    data = json.dumps({k: {"name": n, "cols": list(cols), "rows": rows} for k, n, cols, rows in tabs}, ensure_ascii=False).replace("<", "\\u003c")
    e = html.escape
    fin_ok = c["financial"]["verified"] + c["financial"]["corrected"]
    reasons = "".join("<tr><td>%s</td><td class='num'>%d</td></tr>" % (e(k), v) for k, v in summary["reasons"].items())
    cards = (
        "<div class='card'><div class='mut'>年度數據 · 驗證過的輸出</div><div class='big ok'>%s</div><div>逐欄證實 %s · 自動修正 %s · 剔除 %s（原本 %s 筆）</div></div>"
        % ("{:,}".format(fin_ok), "{:,}".format(c["financial"]["verified"]), "{:,}".format(c["financial"]["corrected"]), "{:,}".format(c["financial"]["rejected"]),
           "{:,}".format(c["financial"]["in"]))
        + "<div class='card'><div class='mut'>年度財報格</div><div class='big ok'>%s</div><div>剔除 %s（原本 %s）</div></div>" % (
            "{:,}".format(c["annual"]["verified"]), c["annual"]["rejected"], "{:,}".format(c["annual"]["in"]))
        + "<div class='card'><div class='mut'>代號紀錄（欄）</div><div class='big ok'>%s</div><div>證不出來清空 %s 欄 · %s 份個股</div></div>" % (
            c["record"]["verified_fields"], c["record"]["rejected_fields"], c["record"]["reports"])
        + "<div class='card'><div class='mut'>一標題四重點</div><div class='big ok'>%s</div><div>未揭露 %s · 剔除 %s</div></div>" % (
            c["summary"]["verified"], c["summary"]["not_disclosed"], c["summary"]["rejected"]))
    page = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN-1 驗證過的輸出</title>
<style>
:root{--bg:#f7f7f5;--fg:#1d1d1f;--mut:#5f6368;--card:#fff;--line:#dedede;--ok:#1a7f37;--part:#9a6700;--bad:#cf222e;--acc:#0b57d0;--chip:#eef1f6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121314;--fg:#e8e8e8;--mut:#a0a4a8;--card:#1c1d1f;--line:#34363a;--ok:#4ac26b;--part:#d4a72c;--bad:#ff7b72;--acc:#8ab4f8;--chip:#26282c}}
:root[data-theme="dark"]{--bg:#121314;--fg:#e8e8e8;--mut:#a0a4a8;--card:#1c1d1f;--line:#34363a;--ok:#4ac26b;--part:#d4a72c;--bad:#ff7b72;--acc:#8ab4f8;--chip:#26282c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,"Segoe UI","Noto Sans TC","PingFang TC",sans-serif}
main{max-width:1200px;margin:0 auto;padding:20px 16px 60px}h1{font-size:24px;margin:4px 0}h2{font-size:18px;margin:24px 0 8px}.mut{color:var(--mut)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.big{font-size:28px;font-weight:650;font-variant-numeric:tabular-nums}.ok{color:var(--ok)}.bad{color:var(--bad)}.num{text-align:right;font-variant-numeric:tabular-nums}
.note{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:8px;padding:10px 14px;margin:12px 0}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0 8px}.tabs button{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:99px;padding:5px 12px;font:inherit;cursor:pointer}
.tabs button[aria-selected="true"]{background:var(--acc);color:#fff;border-color:var(--acc)}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.bar input,.bar select{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:6px 8px;font:inherit;min-width:0}
.bar input{flex:1 1 220px}.pager{display:flex;gap:8px;align-items:center;margin:8px 0}.pager button{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:4px 12px;font:inherit;cursor:pointer}
.wrap{overflow-x:auto;border-radius:10px;border:1px solid var(--line)}table{width:100%;border-collapse:collapse;background:var(--card)}
th,td{padding:6px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:13.5px}th{background:var(--chip);font-weight:600;white-space:nowrap}
td{max-width:420px;overflow-wrap:anywhere}#tb td:first-child{min-width:15em}#tb td.long{min-width:20em}code{background:var(--chip);padding:0 4px;border-radius:4px;overflow-wrap:anywhere}
</style></head><body><main>
<h1>VRN-1 驗證過的輸出</h1>
<div class="mut">@TITLE@ · @VERSION@ · 指紋 <code>@FP@</code> · 這一頁只列證得出來的輸出；證不出來的在「剔除」分頁，附理由</div>
<div class="cards">@CARDS@</div>
<div class="note"><b>怎麼證的</b>：原檔用 pypdfium2 取字元座標自己排行（VRN-1 的擷取走 pdfplumber / PyMuPDF，這裡換一條讀法）→ 科目那一列 → 科目後面那一段數字（並排表遇到下一個科目字就停）→ 值那一列正上方最近的表頭 → 用 x 座標把值對到表頭那一欄（分組表頭要在本次預估那一欄）→ 那一欄的期間 = 這一列寫的年 / 季才算證實。能從原檔確定的才自動修正，改完再證一次；證不出來就不進輸出（不猜）。</div>
<h2>剔除的理由</h2><div class="wrap"><table><thead><tr><th>理由</th><th class="num">筆數</th></tr></thead><tbody>@REASONS@</tbody></table></div>
<div class="tabs" role="tablist" id="tabs"></div>
<div class="bar"><select id="ff"><option value="">全部檔案</option></select><input id="fq" placeholder="搜尋：科目 / 值 / 理由"></div>
<div class="pager"><button id="prev">上一頁</button><span id="pg" class="mut"></span><button id="next">下一頁</button></div>
<div class="wrap"><table><thead id="th"></thead><tbody id="tb"></tbody></table></div>
<p class="mut">檔案（同一夾）：<code>vrn_verified_financial_data.csv</code> · <code>vrn_verified_annual_cells.csv</code> · <code>vrn_verified_ticker_record.csv</code> · <code>vrn_verified_summary_points.csv</code> · <code>vrn_output_corrections.csv</code> · <code>vrn_output_rejected.csv</code>（另有 .parquet）· <code>@JSON@</code></p>
</main>
<script id="data" type="application/json">@DATA@</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);const P=50;let tab='fin',page=0;const $=i=>document.getElementById(i);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
Object.entries(D).forEach(([k,v])=>{const b=document.createElement('button');b.textContent=v.name+' · '+v.rows.length;b.setAttribute('role','tab');b.dataset.k=k;b.onclick=()=>{tab=k;page=0;sync();draw()};$('tabs').appendChild(b)});
function sync(){[...$('tabs').children].forEach(b=>b.setAttribute('aria-selected',b.dataset.k===tab));const t=D[tab];const fi=t.cols.indexOf(t.cols.includes('file')?'file':'VerifyFile');
 const ff=$('ff');const keep=ff.value;ff.length=1;[...new Set(t.rows.map(r=>r[fi]))].sort().forEach(f=>ff.add(new Option(f,f)));ff.value=[...ff.options].some(o=>o.value===keep)?keep:'';}
function rows(){const t=D[tab],fi=t.cols.indexOf(t.cols.includes('file')?'file':'VerifyFile'),f=$('ff').value,q=$('fq').value.trim().toLowerCase();
 return t.rows.filter(r=>(!f||r[fi]===f)&&(!q||r.join(' ').toLowerCase().includes(q)));}
function draw(){const t=D[tab],x=rows(),n=Math.max(1,Math.ceil(x.length/P));page=Math.min(page,n-1);
 $('th').innerHTML='<tr>'+t.cols.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr>';
 $('tb').innerHTML=x.slice(page*P,page*P+P).map(r=>'<tr>'+r.map(v=>'<td'+(String(v).length>24?' class="long"':'')+'>'+esc(v)+'</td>').join('')+'</tr>').join('');
 $('pg').textContent='第 '+(page+1)+' / '+n+' 頁 · '+x.length+' 筆';}
$('ff').onchange=()=>{page=0;draw()};$('fq').oninput=()=>{page=0;draw()};$('prev').onclick=()=>{if(page>0){page--;draw()}};$('next').onclick=()=>{page++;draw()};sync();draw();
</script></body></html>
"""
    for k, v in (("@TITLE@", e(title or str(summary.get("round", "")))), ("@VERSION@", e(VERSION)), ("@FP@", e(summary["fingerprint"])), ("@CARDS@", cards),
                 ("@REASONS@", reasons or "<tr><td>沒有剔除</td><td class='num'>0</td></tr>"), ("@JSON@", e(JSON_NAME)), ("@DATA@", data)):
        page = page.replace(k, v)
    path.write_text(page, encoding="utf-8")


# =====================================================================
# 8 . 已知答案（引擎鎖的證明）
# =====================================================================
# [VRN-ID] VRN-ENG021-FNC051 · ENTRY
def selftest(verbose: bool = True) -> int:
    """畫一份已知答案的 PDF（PyMuPDF）→ 對、錯期間、截斷、分組取到舊值、並排表取到右表、科目歸錯、原文沒有的值，各一筆 → 逐項對答案。
    2026-10-20 加：各期間子欄數不同的分組表（凱基：1Q26 底下 Actual / Est. / Diff，2Q26F 底下 New / Old / Chg / Cons.）、數字黏單位（(4.1)ppts）。"""
    checks: List[Tuple[str, bool]] = []
    try:
        import fitz  # PyMuPDF：VRN-1 的相依（requirements-dev.txt）
        import pandas as pd
        import pypdfium2  # noqa: F401
    except Exception as error:  # noqa: BLE001
        print("[SKIP] %s 自測：%s" % (VERSION, error))
        return 0
    with tempfile.TemporaryDirectory(prefix="vrn_outputverify_") as td:
        t = Path(td)
        samples = t / "samples"
        samples.mkdir()
        doc = fitz.open()
        pg = doc.new_page(width=600, height=400)

        # [VRN-ID] VRN-ENG021-FNC052 · LOGIC
        def put(x, y, s):
            pg.insert_text((x, y), s, fontsize=9, fontname="helv")
        for x, s in ((150, "2024A"), (210, "2025E"), (270, "2026E"), (380, "2024A"), (440, "2025E"), (500, "2026E")):
            put(x, 60, s)
        for y, row in ((80, [(10, "Revenue"), (150, "1,000"), (210, "1,200"), (270, "1,400"), (330, "Capex"), (380, "(90)"), (440, "(95)"), (500, "(99)")]),
                       (95, [(10, "EPS"), (150, "5.20"), (210, "6.10"), (270, "7.00")]), (110, [(10, "Net profit"), (150, "300"), (210, "350"), (270, "410")])):
            for x, s in row:
                put(x, y, s)
        for x, s in ((180, "2026E"), (360, "2027E")):
            put(x, 160, s)
        for x, s in ((150, "Old"), (180, "New"), (210, "Diff"), (330, "Old"), (360, "New"), (390, "Diff")):
            put(x, 175, s)
        for y, row in ((190, [(10, "Gross profit"), (150, "11,976"), (180, "12,009"), (210, "0.3%"), (330, "15,205"), (360, "17,076"), (390, "12.3%")]),
                       (205, [(10, "Op. income"), (150, "3,500"), (180, "3,837"), (210, "9.6%"), (330, "7,900"), (360, "8,316"), (390, "5.3%")])):
            for x, s in row:
                put(x, y, s)
        for x, s in ((192, "1Q26"), (390, "2Q26F")):
            put(x, 260, s)
        for x, s in ((150, "Actual"), (195, "Est."), (240, "Diff"), (300, "New"), (360, "Old"), (420, "Chg"), (480, "Cons.")):
            put(x, 275, s)
        for y, row in ((290, [(10, "Revenue"), (150, "20,864"), (195, "20,857"), (240, "0.0"), (300, "23,224"), (360, "22,629"), (420, "2.6"), (480, "22,630")]),
                       (305, [(10, "Gross margin"), (150, "28.8"), (195, "32.8"), (240, "(4.1)ppts"), (300, "30.6"), (360, "33.2"), (420, "(2.7)ppts"),
                              (480, "33.1")])):
            for x, s in row:
                put(x, y, s)
        doc.save(str(samples / "KNOWN.pdf"))
        doc.close()
        rnd = t / "round1"
        (rnd / "dataframes").mkdir(parents=True)

        # [VRN-ID] VRN-ENG021-FNC053 · LOGIC
        def fin(i, metric, label, period, fy, raw, ptype="FY", fq=""):
            return {"FinancialRowID": "r%d" % i, "FileID": "F", "TW_TICKER": "1234", "Broker": "KNOWN", "MetricName": metric, "MetricNameRaw": label,
                    "PeriodLabelRaw": period, "FiscalYear": fy, "FiscalQuarter": fq, "PeriodType": ptype, "EstimateFlag": "Estimate", "ValueRaw": raw,
                    "Value": parse_num(raw), "Unit": "raw", "PageNumber": 1, "TableID": "T", "SourceText": "%s | %s | %s" % (label, period, raw)}
        rows = [fin(1, "Revenue", "Revenue", "2025E", 2025, "1,200"),          # 對
                fin(2, "Revenue", "Revenue", "2024A", 2024, "1,400"),          # 值在 2026E 那一欄 → 改期間
                fin(3, "EPS", "EPS", "2025E", 2025, "6.1"),                    # 截斷 → 6.10
                fin(4, "GrossProfit", "Gross profit", "2026E", 2026, "11,976"),  # 分組取到 Old → New 12,009
                fin(5, "Revenue", "Revenue", "2024A", 2024, "(90)"),           # 並排表右表的值 → 改成 1,000
                fin(6, "TargetPrice", "Net profit", "2025E", 2025, "350"),     # 科目歸錯 → 剔除
                fin(7, "Revenue", "Revenue", "2025E", 2025, "9,999"),          # 原文沒有 → 改成那一欄的值 1,200（和第 1 筆重複 → 不留）
                fin(8, "OperatingProfit", "Op. income", "2027E", 2027, "8,316"),  # 分組 New 對
                fin(9, "EPS", "EPS", "T", None, "7"),                            # 期間不明 → 剔除
                fin(10, "Revenue", "Revenue", "1Q26", 2026, "23,224", "FQ", "2026-03"),     # 取到 2Q26F 的 New → 補 1Q26 的 Actual 20,864
                fin(11, "Revenue", "Revenue", "2Q26F", 2026, "2.6", "FQ", "2026-06"),       # 取到 2Q26F 的 Chg → 改成 New 23,224
                fin(12, "GrossMargin", "Gross margin", "1Q26", 2026, "30.6", "FQ", "2026-03")]  # 黏單位的格之後 · 取到 2Q26F → 1Q26 Actual 28.8
        pd.DataFrame(rows).to_parquet(rnd / "dataframes" / "vrn_financial_data.parquet", index=False)
        pd.DataFrame([{"FileID": "F", "SourceFileName": "KNOWN.pdf"}]).to_parquet(rnd / "dataframes" / "vrn_basic_info.parquet", index=False)
        got = verify_round(rnd, samples, [], title="已知答案")
        v = pd.read_csv(rnd / OUT_DIRNAME / "vrn_verified_financial_data.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
        rj = pd.read_csv(rnd / OUT_DIRNAME / "vrn_output_rejected.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
        by = {r["FinancialRowID"]: r for r in v.to_dict("records")}
        checks.append(("對的那一筆 → VERIFIED", by.get("r1", {}).get("VerifyStatus") == "VERIFIED"))
        checks.append(("值在別欄 → 期間改成那一欄（2026E · CORRECTED）", by.get("r2", {}).get("PeriodLabelRaw") == "2026E" and by["r2"]["VerifyStatus"] == "CORRECTED"))
        checks.append(("截斷 6.1 → 6.10", by.get("r3", {}).get("ValueRaw") == "6.10"))
        checks.append(("分組表取到 Old → 改成 New 12,009", by.get("r4", {}).get("ValueRaw") == "12,009"))
        checks.append(("並排表右表的值 → 改成左表那一欄 1,000", by.get("r5", {}).get("ValueRaw") == "1,000"))
        checks.append(("科目歸錯（Net profit → TargetPrice）→ 剔除", "r6" not in by and "r6" in set(rj["row"])))
        checks.append(("改出來和已證實的同鍵同值 → 不重複留", "r7" not in by))
        checks.append(("分組表 New 那一欄 → VERIFIED", by.get("r8", {}).get("VerifyStatus") == "VERIFIED"))
        checks.append(("期間不明 → 剔除", "r9" not in by and "r9" in set(rj["row"])))
        page = (rnd / OUT_DIRNAME / HTML_NAME).read_text(encoding="utf-8")
        checks.append(("子欄數不同的分組表：1Q26 取到 2Q26F 的 New → 補成 1Q26 Actual 20,864", by.get("r10", {}).get("ValueRaw") == "20,864"))
        checks.append(("子欄數不同的分組表：2Q26F 取到 Chg → 改成 New 23,224", by.get("r11", {}).get("ValueRaw") == "23,224"))
        checks.append(("數字黏單位（(4.1)ppts）不擋住這一列 · 1Q26 毛利率 → 28.8", by.get("r12", {}).get("ValueRaw") == "28.8"))
        checks.append(("HTML U/I：分頁 · 篩選 · 資料嵌入安全（沒有提早結束的 </script>）", page.count("</script>") == 2 and 'id="ff"' in page and 'id="tabs"' in page))
        checks.append(("計數對得上：證實 + 修正 + 剔除 = 輸入", got["counts"]["financial"]["verified"] + got["counts"]["financial"]["corrected"] + got["counts"]["financial"]["rejected"] + 1 == 12))
        checks.append(("沒給段落標題的讀法 → 不查（行為不變）", got["section_check"]["tool"] == "" and "r3" in by))
        checks.append(("段落判準：Growth(%) 底下的 NetIncome · YoY 底下的 Revenue → 不合；Margins (%) 底下的 GrossMargin → 不判",
                       section_semantic("NetIncome", "Growth(%)")[0] is False and section_semantic("Revenue", "YoY")[0] is False
                       and section_semantic("GrossMargin", "Margins (%)")[0] is None))
        checks.append(("段落判準：混合單位「Profit & Loss (NT$m, %)」→ 不判 · 一般標題「Key financials」→ 合 · 沒有標題 → 不判",
                       section_semantic("NetIncome", "Profit & Loss (NT$m, %)")[0] is None and section_semantic("NetIncome", "Key financials")[0] is True
                       and section_semantic("NetIncome", "")[0] is None))

        # [VRN-ID] VRN-ENG021-FNC057 · LOGIC
        def fake_section_of(pdf, page, label, value):
            if label == "Op. income":
                raise RuntimeError("借來的讀法倒了")
            return {"EPS": {"section": "Growth (%)", "found": True}, "Gross margin": {"section": "Margins (%)", "found": True},
                    "Revenue": {"section": "Income statement (NT$m, %)", "found": True}}.get(label, {"section": "", "found": False}) | {"how": "已知答案", "reader": "假讀法"}
        rnd2 = t / "round2"
        (rnd2 / "dataframes").mkdir(parents=True)
        for f in (rnd / "dataframes").iterdir():
            (rnd2 / "dataframes" / f.name).write_bytes(f.read_bytes())
        got2 = verify_round(rnd2, samples, [], title="已知答案 · 段落標題", section_of=fake_section_of, section_tool="假的 section.near")
        v2 = pd.read_csv(rnd2 / OUT_DIRNAME / "vrn_verified_financial_data.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
        rj2 = pd.read_csv(rnd2 / OUT_DIRNAME / "vrn_output_rejected.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
        by2 = {r["FinancialRowID"]: r for r in v2.to_dict("records")}
        sc = got2["section_check"]
        checks.append(("借來的段落標題：Growth (%) 底下的 EPS → 剔除（附理由）· Margins (%) 的毛利率留著並記下段落 · 混合單位的營收留著",
                       "r3" not in by2 and any(r["row"] == "r3" and "段落標題" in r["reason"] for r in rj2.to_dict("records"))
                       and "Margins (%)" in by2.get("r12", {}).get("VerifyNote", "") and "r1" in by2))
        checks.append(("借來的讀法倒了 → 不剔除（記錯誤數）· 摘要寫出讀法來歷",
                       "r8" in by2 and sc["errors"] == 1 and sc["rejected"] == 1 and sc["tool"] == "假的 section.near"))

        # Codex PR #79：科目列標自己的單位 · 代號要在代號的位置 · 組合段落要有同一頁依序的原文片段
        doc = fitz.open()
        pg = doc.new_page(width=600, height=400)
        put(10, 30, "TSMC (2330.TW) Overweight")
        for y, a, b in ((60, "Demand trends for AI are strong with broader", "Analyst Jane Doe"),
                        (75, "demand pickup and capacity likely to remain", "Price NT$1130.0"),
                        (90, "tight into 2026 on CoWoS orders.", "Revenue grew 31% in 2025")):
            put(10, y, a)
            put(380, y, b)
        pg = doc.new_page(width=600, height=400)
        put(10, 60, "Margin outlook improves next year")
        cover = "TSMC-2330 20250718.pdf"
        doc.save(str(samples / cover))
        doc.close()
        src3 = Sources(samples)
        recs = pd.DataFrame([{"file": cover, "ticker": tk} for tk in ("2330", "2025", "1130")])
        v_r, rj_r = verify_record(recs, src3)
        bad = {r["value"] for r in rj_r if r["field"] == "ticker"}
        checks.append(("代號：檔名獨立一段 / 原文 2330.TW → 證實 · 2025（檔名日期的一截、原文的年份）· 1130（價格）→ 剔除",
                       "2330" not in bad and bad == {"2025", "1130"}))
        summ = pd.DataFrame([{"file": cover, "point_no": i, "disclosed": "Y", "text": tx} for i, tx in enumerate((
            "Demand trends for AI are strong with broader Analyst Jane Doe demand pickup and capacity likely to remain",   # 兩欄交錯 → 證實
            "strong demand AI trends are with broader for pickup demand remain",                                         # 頁上的字重排 → 剔除
            "Demand trends for AI are strong with broader Margin outlook improves next year",                             # 跨頁拼 → 剔除
            "Demand trends for AI are strong with broader 1130 demand pickup",                                           # 數字從別處搬來 → 剔除
        ), start=1)])
        v_s, rj_s = verify_summary(summ, src3, {})
        st = {str(r["point_no"]): r.get("VerifyStatus") for r in v_s}
        rs = {str(r["row"]): r["evidence"] for r in rj_s}
        checks.append(("組合段落：兩欄交錯 → 同一頁依序片段證實 · 重排 / 跨頁 / 搬來的數字 → 剔除（附理由）",
                       st.get("1") == "VERIFIED" and "短片段" in rs.get("2", "") and "不同頁" in rs.get("3", "") and "數字片段" in rs.get("4", "")))
        checks.append(("科目列標自己寫了倍數 / 百分比 → 不是金額科目：Turnover (X) ≠ Revenue · Revenue (%) ≠ Revenue · P/E (x) 照舊",
                       semantic("Revenue", "Turnover (X)", "0.4")[0] is False and semantic("Revenue", "Revenue (%)", "12")[0] is False
                       and semantic("PER", "P/E (x)", "20.1")[0] is True and semantic("EPS", "EPS (pre-tax)", "5.2")[0] is False))
    for name, ok in checks:
        if verbose:
            print("  [%s] %s" % ("PASS" if ok else "FAIL", name))
    passed = sum(1 for _n, ok in checks if ok)
    print("[計] %s 自測 %d/%d · %s" % (VERSION, passed, len(checks), "PASS" if passed == len(checks) else "FAIL"))
    return 0 if passed == len(checks) else 1


# [VRN-ID] VRN-ENG021-FNC054 · ENTRY
def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest()
    if len(args) < 2:
        print("用法：python VRN_OutputVerify_v0100.py <round 夾（含 dataframes/）> <樣本夾> · 或 --selftest")
        return 2
    got = verify_round(Path(args[0]), Path(args[1]))
    print(json.dumps({k: got[k] for k in ("counts", "reasons", "corrections_by_kind", "fingerprint", "html")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
