#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG014 · VRN_TitleTrim_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 103；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_TitleTrim v0100 -- stock reports only: the title taken apart, the first page and the annual financial pages cleaned
(TRIM) before they are taken apart, and every value read twice so that only what two readings agree on is called right.

Operator 2026-10-11:
  「"C:\\測試樣本報告" 只擷取個股報告的標題分拆識別 首頁及年度財報頁來進行基本資料清理TRIM後分拆識別 實測實修正
    正確鎖功能鎖成功部分及引擎 位成功的持續實測實際修正直到輸出正確可驗證無誤」

Rules come from the books, never from here:
  ssot/VRN_Method_SSOT_v0100.json   def02_title (where a title is found, no first-line assumption, the eight TRIM steps,
                                    the segment order, the Taiwan ticker rules), def02_report_types, def03 (first-page zones,
                                    rating layers, upside formula), def05 (an unmappable label is REVIEW_REQUIRED), def16 (nulls)
  ssot/VRN_TitleTrim_SSOT_v0100.json the characters TRIM touches, the title / cover / annual words and patterns, the states,
                                    what may be locked

Per stock report:
  1. title      candidates from the PDF metadata title, the top 25 % of page 1, the two largest font sizes and the first
                three lines that carry company + code + type; the best one (lines next to it of nearly the same size joined)
                is TRIMmed and split into company, ticker, market, report type, core view, rating action, target-price change
  2. cover      page 1 line by line, TRIMmed, put in the def03 zones; broker, date, rating (as printed), target price,
                current price, upside, analyst, e-mail, telephone read from the clean lines
  3. annual     the G15 restored tables TRIMmed cell by cell and read again with the same G15 functions; a page with enough
                fiscal-year cells under mapped labels is an annual financial page; the add / subtract / divide checks run
                before and after TRIM (TRIM may only help)
  4. verify     each value set beside the answers the other readers already gave for the same file (file name, the first-page
                engine, the database engine, ENG396 on the full text, the checks): two independent readers that agree =
                VERIFIED, the only state that is locked (VRN_Lock_v0100); everything else goes on the fix list with the reason

Measured only: no answer of an existing engine is changed.  No network, LIVE off, no consent variable read or set.
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

import argparse
import copy
import importlib.util
import json
import re
import sys
import tempfile
import time
import unicodedata
from collections import Counter
from pathlib import Path

TITLE_TRIM_VERSION = "v0100"
VRN_ROOT = Path(__file__).resolve().parents[1]
SSOT_DIR = VRN_ROOT / "ssot"
BOOK_FILE = SSOT_DIR / "VRN_TitleTrim_SSOT_v0100.json"
METHOD_FILE = SSOT_DIR / "VRN_Method_SSOT_v0100.json"
REGIONS_FILE = VRN_ROOT / "engine" / "VRN_PageRegions_v0100.py"
FPE_FILE = VRN_ROOT / "engine" / "VIA_VRN_FirstPageEngine.py"
EVIDENCE_FILE = VRN_ROOT / "engine" / "VRN_Evidence_Core.py"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
TEXT_EXT = {".txt", ".docx"}
EXPECTED_TITLE = ("title.ticker", "title.company")
# 2026-10-21 第二十三輪：首頁沒印上漲%、但目標價與現價都在，就算得出來。這句話只寫這一次 ——
# 代號紀錄那一支（VRN_TickerRecord）直接引用部位自己的 why，兩邊不會各寫各的。
UPSIDE_DERIVED_WHY = "首頁沒印；VRN 重算 (目標價−現價)÷現價（現價用報告印的原始收盤價，不是 adj）"
STATE_ORDER = ("VERIFIED", "SINGLE", "NOT_PRINTED", "CONFLICT", "MISSING", "REVIEW", "UNMAPPED", "REPORT_CHECK", "TRIM_LOSS",
               "TRIM_REGRESSION")


# =====================================================================
# 0 . BOOKS AND THE ENGINES THIS ONE READS FROM (loaded by path, never changed)
# =====================================================================
# [VRN-ID] VRN-ENG014-FNC001 · IO
def load_module(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-ENG014-FNC093 · LOGIC
def _is_analyst(name, ctx):
    """標題代號前面那一段是不是這份報告的分析師 —— **判斷不在這裡**，向 VRN_Evidence_Core 借。

    2026-10-19 操作員：「多數讀到分析師是錯的 修那個 不要放寬門檻」。
    「代號前面那一段就是公司」在凱基的標題上會取到人（`賴偉中(2637 TT)`，實測 4 檔）。
    分析師是誰本來就是 VRN_Evidence_Core 算的（extract_analysts + filename_analysts），
    名單由首頁引擎往上帶（ctx["analysts"]），比法也用它的 is_analyst_name ——
    這裡再寫一份姓氏表就是第二顆頭。

    借不到（檔不見、載入失敗）時回 False：維持現狀的 CONFLICT 讓它現形，
    不另外用一條猜的規則頂上。
    """
    names = (ctx or {}).get("analysts") or []
    if not name or not names:
        return False
    try:
        return bool(load_module("vrn_titletrim_evidence", EVIDENCE_FILE).is_analyst_name(name, names))
    except Exception:                                 # noqa: BLE001
        return False


# [VRN-ID] VRN-ENG014-FNC094 · LOGIC
def _analyst_names(name, fpe, ticker=""):
    """這份報告的分析師名單：首頁引擎帶上來的（頁上＋檔名）∪ 檔名自己算的。

    判斷還是只有一份（VRN_Evidence_Core.filename_analysts）—— 同一支函式兩個呼叫端，
    不是兩顆頭。非 PDF 沒有首頁引擎結果時檔名那一半照樣算得出來：2026-10-19 實測
    `3653健策凱基投顧 向子慧 (3).txt` 就是因為名單空著而漏掉（PDF 的三檔都修好了，它沒有）。

    **ticker 一定要傳**：貼著代號的那一段是公司不是分析師，少傳這個參數
    `國光生(4142,Note)` 會被當成人名，正確答案反而被擋掉（實測踩過）。
    """
    out = [n for n in (fpe or {}).get("analyst_names") or [] if n]
    try:
        for a in load_module("vrn_titletrim_evidence", EVIDENCE_FILE).filename_analysts(name, None, ticker) or []:
            if a.get("name") and a["name"] not in out:
                out.append(a["name"])
    except Exception:                                 # noqa: BLE001
        pass
    return out


# [VRN-ID] VRN-ENG014-FNC096 · LOGIC
def _broker_slot_has_text(title, cover, ctx, B):
    """券商名**該在的四個位置**裡，有沒有我們沒讀出來的字？有 → 維持 MISSING。

    操作員 2026-10-20：「券商名收穫縮寫同義字等一定位在 FILENAME 首頁
    各頁下方小字體頁尾 或是報告後方小字體附錄等」。所以「沒印」要照這四個位置判，
    不是只看首頁有沒有機構字 —— Codex PR #74 P1 指的就是這一點：
    報告印了不認得的券商名（`Jefferies`，後面沒接 Securities）而三條讀法都空，
    只看機構字會把**字典缺口**當成合法缺席，把完成度灌水。

    四個位置分兩種判法：
      跨頁重複帶（各頁頁眉／頁尾）—— **結構判準，不靠詞表**：這一帶裡只要有「不是本報告標題」
          的文字，就表示發行機構帶存在而我們沒讀到。實測對照組這一帶是
          `兆豐證券投資顧問MEGA Securities Research`、`大華證券投資顧問GS Securities Research`；
          那兩檔的重複帶**只有標題行本身**。印 `Jefferies` 的報告會落在這一格 → 維持 MISSING。
      檔名／首頁／後方小字附錄 —— 散文或複合詞，用冊上的 `cover.broker_context_rx` 判機構字
          （e-mail 與網址裡的字不算，冊 broker_alias_rule_r6）。

    讀不到資料就回 True（保守：維持 MISSING，寧可留紅字也不默默放過）。
    """
    try:
        rx = re.compile(B.book["cover"]["broker_context_rx"], re.I)
    except (KeyError, re.error):
        return True
    fn = (ctx or {}).get("filename") or {}
    page = "\n".join(str(z.get("clean") or "") for z in ((cover or {}).get("zones") or []))
    if not page.strip():
        return True
    bands = [b for b in ((ctx or {}).get("bands") or []) if (b.get("reason") or "").startswith("跨頁重複")]
    own = _bare_text((title or {}).get("text") or "")
    for b in bands:
        head = _bare_text(b.get("head") or "")
        if head and own and (head in own or own in head):
            continue                                  # 這一帶就是標題行本身，不是發行機構帶
        if head:
            return True                               # 發行機構帶有字，而三條讀法都沒讀出來 → 讀漏
    prose = [str(fn.get("stem") or ""), page]
    prose += [str(b.get("head") or "") for b in ((ctx or {}).get("bands") or [])
              if not (b.get("reason") or "").startswith("跨頁重複")]
    for text in prose:
        cleaned = B.email_rx.sub(" ", text)
        try:
            cleaned = load_module("vrn_titletrim_evidence", EVIDENCE_FILE).URL_RX.sub(" ", cleaned)
        except Exception:                             # noqa: BLE001
            pass                                      # 清不掉網址就少清一層：方向保守（更容易留 MISSING）
        if rx.search(cleaned):
            return True
    return False


# [VRN-ID] VRN-ENG014-FNC097 · LOGIC
def _bare_text(text):
    """只留字母、數字與漢字 —— 比「這一帶是不是標題行」用的同一把尺。"""
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", str(text or ""))


# [VRN-ID] VRN-ENG014-CLS001 · CLASS
class Books:
    """The TitleTrim book and the Method book, compiled once."""

    # [VRN-ID] VRN-ENG014-FNC002 · INIT
    def __init__(self, book=None, method=None):
        self.book = book if book is not None else json.loads(BOOK_FILE.read_text(encoding="utf-8"))
        self.method = method if method is not None else json.loads(METHOD_FILE.read_text(encoding="utf-8"))
        t = self.book["trim"]
        table = {}
        for ch in t["invisible"]:
            table[ord(ch)] = None
        for ch in t["spaces"]:
            table[ord(ch)] = " "
        self.space_table = table
        punct = {ord(ch): t["dash_to"] for ch in t["dashes"]}
        punct.update({ord(ch): t["colon_to"] for ch in t["colons"]})
        punct.update({ord(k): v for k, v in t["brackets"].items()})
        self.punct_table = punct
        self.variant_table = {ord(k): v for k, v in t["variants"].items()}
        self.keep = t["keep"]
        lo, hi = (int(x, 16) for x in t["unreadable"]["pua"])
        self.pua = (lo, hi)
        self.number_rx = re.compile(t["number_rx"])
        ti = self.book["title"]
        self.meta_junk_rx = re.compile(ti["metadata_junk_rx"], re.I)
        self.noise_rx = re.compile(ti["noise_rx"], re.I)
        self.sep_rx = re.compile(ti["separators_rx"])
        tk = self.book["ticker"]
        self.paren_rx = re.compile(tk["paren_rx"], re.I)
        self.bbg_rx = re.compile(tk["bloomberg_rx"], re.I)
        self.yahoo_rx = re.compile(tk["yahoo_rx"], re.I)
        self.bare_rx = re.compile(tk["bare_rx"])
        self.report_types = {}
        for code, words in (self.method.get("def02_report_types") or {}).items():
            if isinstance(words, list):
                self.report_types.setdefault(code, []).extend(words)
        for code, words in (self.book.get("report_types_extra") or {}).items():
            self.report_types.setdefault(code, []).extend(w for w in words if w not in self.report_types.get(code, []))
        ra = self.book["rating_action"]
        self.actions = {k: v for k, v in ra.items() if isinstance(v, list)}
        self.action_window = int(ra.get("window", 8))
        tp = self.book["tp_change"]
        self.tp_word = tp["words_rx"]
        self.money = tp["money_rx"]
        self.tp_dirs = {"up": tp["up"], "down": tp["down"], "same": tp["same"]}
        dirs = "|".join(re.escape(w) for w in sorted(tp["up"] + tp["down"] + tp["same"], key=len, reverse=True))
        self.tp_from_to = re.compile(rf"{self.tp_word}[^0-9]{{0,16}}?{tp['from_rx']}\s*{self.money}[^0-9]{{0,16}}?{tp['to_rx']}\s*{self.money}",
                                     re.I)
        self.tp_to_from = re.compile(rf"{self.tp_word}[^0-9]{{0,24}}?{tp['to_rx']}\s*{self.money}\s*\(?\s*{tp['from_rx']}\s*{self.money}",
                                     re.I)
        self.tp_dir_to = re.compile(rf"(?:{self.tp_word}\s*(?P<d1>{dirs})|(?P<d2>{dirs})\s*{self.tp_word})[^0-9]{{0,8}}?"
                                    rf"(?:{tp['to_rx']})?\s*{self.money}", re.I)
        self.tp_plain = re.compile(rf"{self.tp_word}\s*:?\s*{self.money}", re.I)
        self.tp_dir_words = re.compile(rf"(?:{dirs})", re.I)
        cv = self.book["cover"]
        self.labels = cv["labels"]
        self.date_rx = [re.compile(p, re.I) for p in cv["date_rx"]]
        self.email_rx = re.compile(cv["email_rx"])
        self.tel_rx = re.compile(cv["tel_rx"], re.I)
        self.name_rx = re.compile(cv["name_rx"])
        self.value_stop_rx = re.compile(cv["value_stop_rx"], re.I)
        self.date_like_rx = re.compile(cv["date_like_rx"])
        self.broker_context_rx = cv["broker_context_rx"]
        self.broker_generic = {a.casefold() for a in cv["broker_generic_aliases"]}
        self.date_skip = [w.casefold() for w in cv["date_skip_words"]]
        self.prior_words = [w.casefold() for w in cv["prior_words"]]
        self.prior_line_rx = re.compile(cv["prior_line_rx"])
        self.prior_before_rx = re.compile(cv["prior_before_rx"], re.I)
        self.prior_before_chars = int(cv["prior_before_chars"])
        self.not_price_after_rx = re.compile(cv["not_price_after_rx"])
        self.label_row = dict(cv["label_row"], value=re.compile(cv["label_row"]["value_rx"]),
                              label=re.compile(cv["label_row"]["label_rx"]))
        self.date_exclude_before_rx = re.compile(cv["date_exclude_before_rx"], re.I)
        self.prior_gap = float(cv["prior_geometry"]["max_gap_lines"])
        self.tp_from_to_cover = [re.compile(p, re.I) for p in cv["tp_from_to_rx"]]
        self.cp_not_near_rx = re.compile(cv["current_price_not_near_rx"], re.I)
        self.tp_declared_none_rx = re.compile(cv.get("tp_declared_none_rx") or r"(?!x)x", re.I)
        self.upside_max_gap = int(cv.get("upside_max_gap") or 0)
        self.rating_not_after_rx = re.compile(cv.get("rating_not_after_rx") or r"(?!x)x", re.I)
        self.rating_tails = tuple(cv.get("rating_word_tails") or ())
        self.rating_heads = tuple(cv.get("rating_word_heads") or ())
        self.fn_date_send_days = int(cv.get("filename_date_send_days") or 0)
        self.short_words = [str(w) for w in (self.book.get("focus") or {}).get("short_report_words") or []]
        self.title_junk_min = int(cv["title_engine_junk"]["min_chars"])
        self.contact_rank = cv["contact_zone_rank"]
        self.nr_words = {w.casefold() for w in cv["nr_words"]}
        an = self.book["annual"]
        self.null_tokens = {tok.casefold(): kind for kind, toks in an["null_tokens"].items() for tok in toks}
        self.triangle = tuple(an["triangle"])
        self.verify = self.book["verify"]


_BOOKS = None
_FPE = None
_REGIONS = None


# [VRN-ID] VRN-ENG014-FNC003 · LOGIC
def books():
    global _BOOKS
    if _BOOKS is None:
        _BOOKS = Books()
    return _BOOKS


# [VRN-ID] VRN-ENG014-FNC004 · LOGIC
def regions():
    """VRN_PageRegions (G15) and its mother engines: decompose, table_rows, check_rows are reused, never copied."""
    global _REGIONS
    if _REGIONS is None:
        R = load_module("VRN_PageRegions_v0100", REGIONS_FILE)
        _REGIONS = (R, R.mother())
    return _REGIONS


# [VRN-ID] VRN-ENG014-FNC005 · LOGIC
def share(regions_module=None, fpe=None):
    """The caller's already loaded G15 module and first-page engine are used instead of loading second copies."""
    global _REGIONS, _FPE
    if regions_module is not None:
        _REGIONS = (regions_module, regions_module.mother())
    if fpe is not None:
        _FPE = fpe


# [VRN-ID] VRN-ENG014-FNC006 · LOGIC
def first_page_engine():
    """The first-page engine is read as a library (broker and rating dictionaries, file-name fields); its logic is not touched."""
    global _FPE
    if _FPE is None:
        F = load_module("VIA_VRN_FirstPageEngine", FPE_FILE)
        _FPE = F.FirstPageEngine()
    return _FPE


# =====================================================================
# 1 . TRIM (Method def02 normalize_steps; raw kept, clean built, numbers never lost)
# =====================================================================
# [VRN-ID] VRN-ENG014-FNC007 · LOGIC
def _fullwidth_to_halfwidth(s):
    out = []
    for ch in s:
        o = ord(ch)
        if 0xFF01 <= o <= 0xFF5E:
            out.append(chr(o - 0xFEE0))
        elif o == 0x3000:
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


# [VRN-ID] VRN-ENG014-FNC008 · LOGIC
def _count_digits(s):
    return sum(1 for ch in s if unicodedata.digit(ch, None) is not None)


# [VRN-ID] VRN-ENG014-FNC009 · LOGIC
def _count(s, chars):
    return sum(s.count(c) for c in chars)


# [VRN-ID] VRN-ENG014-FNC010 · LOGIC
def trim(text, B=None):
    """-> {raw, clean, fold, steps (the ones that changed something), loss, pua, numbers}."""
    B = B or books()
    raw = "" if text is None else str(text)
    steps = []
    s1 = _fullwidth_to_halfwidth(raw)
    if s1 != raw:
        steps.append("全形轉半形")
    s2 = unicodedata.normalize("NFKC", s1)
    if s2 != s1:
        steps.append("Unicode NFKC")
    s3 = s2.translate(B.variant_table)
    if s3 != s2:
        steps.append("異體字修正")
    s4 = re.sub(r" {2,}", " ", s3.translate(B.space_table)).strip()
    if s4 != s3:
        steps.append("移除重複空格與不可見字元")
    s5 = s4.translate(B.punct_table)
    if s5 != s4:
        steps.append("統一破折號/冒號/括號")
    clean = s5
    loss = []
    if _count_digits(clean) < _count_digits(raw):
        loss.append("數字")
    if clean.count("%") < _count(raw, B.keep["percent"]):
        loss.append("百分比")
    if _count(clean, "-(") < _count(raw, B.keep["minus"]):
        loss.append("負號")
    if clean.count("$") < _count(raw, B.keep["currency"]):
        loss.append("幣別")
    pua = sum(1 for ch in raw if B.pua[0] <= ord(ch) <= B.pua[1])
    return {"raw": raw, "clean": clean, "fold": clean.casefold(), "steps": steps, "loss": loss, "pua": pua,
            "numbers": numbers(clean, B)}


# [VRN-ID] VRN-ENG014-FNC011 · LOGIC
def numbers(clean, B=None):
    """Numeric version beside the text (def02 數值版另建原文保留; def16 parentheses, multiples, percent)."""
    B = B or books()
    out = []
    for m in B.number_rx.finditer(clean):
        num = m.group("num")
        try:
            value = float(num.replace(",", ""))
        except ValueError:
            continue
        neg = bool(m.group("sign") == "-" or (m.group("open") and m.group("close")))
        unit = m.group("unit") or ""
        kind = "pct" if unit == "%" else ("multiple" if unit in ("x", "X", "倍") else "amount")
        v = -value if neg else value
        item = {"text": m.group(0).strip(), "value": v, "kind": kind, "currency": m.group("cur") or "", "end": m.end()}
        if kind == "pct":
            item["internal"] = round(v / 100.0, 10)
        out.append(item)
    return out


# [VRN-ID] VRN-ENG014-FNC012 · LOGIC
def fold_key(text, B=None):
    """Comparable form: TRIMmed, case-folded, no blanks."""
    return re.sub(r"\s+", "", trim(text, B)["fold"]) if text not in (None, "") else ""


# =====================================================================
# 2 . PAGE 1 LINES (PyMuPDF dict: spans with size, bold, box) / text files
# =====================================================================
# [VRN-ID] VRN-ENG014-FNC013 · EXTRACT
def page_lines(path, page_no=0):
    """-> {width, height, meta_title, lines: [{text, size, bold, bbox, top, x0}]} (same-row spans of similar size merged)."""
    import fitz  # type: ignore
    with fitz.open(str(path)) as doc:
        meta_title = (doc.metadata or {}).get("title") or ""
        if page_no >= len(doc):
            return {"width": 0, "height": 0, "meta_title": meta_title, "lines": [], "pages": len(doc)}
        page = doc[page_no]
        width, height = float(page.rect.width), float(page.rect.height)
        raw_lines = []
        flags = fitz.TEXTFLAGS_DICT & ~getattr(fitz, "TEXT_MEDIABOX_CLIP", 0)   # text past the page edge is still text (TRIM loses none)
        for block in page.get_text("dict", flags=flags).get("blocks", []):
            for line in block.get("lines", []):
                spans = [sp for sp in line.get("spans", []) if (sp.get("text") or "").strip()]
                if not spans:
                    continue
                text = "".join(sp["text"] for sp in spans)
                size = max(float(sp.get("size") or 0) for sp in spans)
                bold = any((int(sp.get("flags") or 0) & 16) or "bold" in str(sp.get("font") or "").lower() for sp in spans)
                x0, y0, x1, y1 = (float(v) for v in line["bbox"])
                raw_lines.append({"text": text, "size": round(size, 2), "bold": bold, "bbox": [x0, y0, x1, y1], "top": y0, "x0": x0})
        pages = len(doc)
    merged = []
    for ln in sorted(raw_lines, key=lambda l: (round(l["bbox"][3]), l["x0"])):
        prev = merged[-1] if merged else None
        left = bool(prev) and ln["bbox"][2] <= prev["bbox"][0] + 0.25 * ln["size"]   # 2026-10-20: rounding the bottom put a span left of prev after it
        dist = (prev["bbox"][0] - ln["bbox"][2]) if left else (ln["x0"] - prev["bbox"][2]) if prev else 0.0
        if (prev and abs(prev["bbox"][3] - ln["bbox"][3]) <= 2.0 and abs(prev["size"] - ln["size"]) <= 0.15 * max(prev["size"], ln["size"])
                and dist < 3 * ln["size"]):
            gap = " " if dist > 0.25 * ln["size"] else ""
            prev["text"] = (ln["text"] + gap + prev["text"]) if left else (prev["text"] + gap + ln["text"])
            prev["bbox"] = [min(prev["bbox"][0], ln["bbox"][0]), min(prev["bbox"][1], ln["bbox"][1]),
                            max(prev["bbox"][2], ln["bbox"][2]), max(prev["bbox"][3], ln["bbox"][3])]
            prev["bold"] = prev["bold"] or ln["bold"]
            continue
        merged.append(dict(ln))
    merged.sort(key=lambda l: (l["top"], l["x0"]))
    return {"width": width, "height": height, "meta_title": meta_title, "lines": merged, "pages": pages}


# [VRN-ID] VRN-ENG014-FNC014 · LOGIC
def text_lines(path):
    """DOCX / TXT: no coordinates, no font sizes -- lines in order (the title is then found by content only)."""
    suffix = Path(path).suffix.lower()
    if suffix == ".docx":
        R, _M = regions()
        text = R._docx_text(path)
    else:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    lines = [{"text": t, "size": 0.0, "bold": False, "bbox": [], "top": float(i), "x0": 0.0}
             for i, t in enumerate(x for x in text.splitlines() if x.strip())]
    return {"width": 0.0, "height": 0.0, "meta_title": "", "lines": lines, "pages": 1}


# =====================================================================
# 3 . TITLE (def02: candidates, no first-line assumption, segments in order)
# =====================================================================
# [VRN-ID] VRN-ENG014-FNC015 · LOGIC
def _ticker_hits(clean, B, filename_ticker=""):
    """Every code in the clean title: (code, form, span).  Year-band codes count only when the file name has the same code."""
    hits, taken = [], []
    lo, hi = B.book["ticker"]["year_band"]
    phones = [m.span() for m in B.tel_rx.finditer(clean) if not (m.start() and (clean[m.start() - 1].isdigit() or clean[m.start() - 1] == "."))]
    phones += [m.span() for m in INTL_TEL_RX.finditer(clean)]

    # [VRN-ID] VRN-ENG014-FNC016 · LOGIC
    def add(code, form, span, how):
        if any(s[0] <= span[0] < s[1] for s in taken) or any(p[0] <= span[0] < p[1] for p in phones):
            return                                   # 2026-10-20: '+886 2 2326 8179' scored as a title with a code (2326)
        in_band = lo <= int(code) <= hi
        if in_band and code != str(filename_ticker or "") and how == "bare":
            return
        taken.append(span)
        hits.append({"code": code, "form": form, "span": list(span), "how": how, "year_band": in_band})
    for m in B.paren_rx.finditer(clean):
        form = (m.group(2) or "").strip().upper()
        add(m.group(1), form if form else "()", m.span(), "paren")
    for m in B.yahoo_rx.finditer(clean):
        add(m.group(1), "." + m.group(2).upper(), m.span(), "yahoo")
    for m in B.bbg_rx.finditer(clean):
        add(m.group(1), re.sub(r"\s+", " ", m.group(2).upper()), m.span(), "bloomberg")
    if not hits:
        for m in B.bare_rx.finditer(clean):
            add(m.group(1), "", m.span(), "bare")
    return hits


# [VRN-ID] VRN-ENG014-FNC017 · LOGIC
def _report_types(clean, B):
    low = clean.casefold()
    found = {}
    for code, words in B.report_types.items():
        for w in sorted(words, key=len, reverse=True):
            wl = w.casefold()
            if re.search(r"[A-Za-z]", w):
                m = re.search(r"(?<![A-Za-z])" + re.escape(wl) + r"(?![A-Za-z])", low)
                at = m.start() if m else -1
            else:
                at = low.find(wl)
            if at >= 0:
                found[code] = {"code": code, "word": clean[at:at + len(w)], "span": [at, at + len(w)]}
                break
    return list(found.values())


# [VRN-ID] VRN-ENG014-FNC018 · LOGIC
def _rating_action(clean, B, brd):
    """Action verb next to a rating word (or a whole phrase such as 首次評等); the rating word is kept as printed."""
    low = clean.casefold()
    rating_hits = []
    if brd is not None:
        for h in brd.rating_matches(clean, in_rating_field=False):
            a = h["alias"].casefold()
            at = low.find(a)
            if at >= 0:
                rating_hits.append((at, at + len(a), clean[at:at + len(a)]))
    rating_hits += [(m.start(), m.end(), m.group(0)) for m in re.finditer(r"評等|評級|rating", clean, re.I)]
    best = None
    for code, words in B.actions.items():
        for w in sorted(words, key=len, reverse=True):
            wl = w.casefold()
            for m in re.finditer(re.escape(wl), low):
                if re.search(r"[A-Za-z]", w) and ((m.start() and low[m.start() - 1].isalpha()) or (m.end() < len(low) and low[m.end()].isalpha())):
                    continue
                whole = ("評等" in w) or w in ("首評", "初評", "Initiating Coverage", "Not Rated", "Suspended")
                near = [r for r in rating_hits if 0 <= r[0] - m.end() <= B.action_window or 0 <= m.start() - r[1] <= 2]
                if not whole and not near:
                    continue
                printed = next((r[2] for r in near if r[2] not in ("評等", "評級") and r[2].casefold() != "rating"), "")
                cand = {"action": code, "verb": clean[m.start():m.end()], "rating_printed": printed,
                        "span": [m.start(), max([m.end()] + [r[1] for r in near])]}
                if best is None or (cand["span"][1] - cand["span"][0]) > (best["span"][1] - best["span"][0]):
                    best = cand
    return best


# [VRN-ID] VRN-ENG014-FNC019 · LOGIC
def _num(text):
    try:
        return float(str(text).replace(",", ""))
    except (TypeError, ValueError):
        return None


# [VRN-ID] VRN-ENG014-FNC020 · LOGIC
def _direction(word, B):
    w = (word or "").casefold()
    for d, words in B.tp_dirs.items():
        if any(w == x.casefold() for x in words):
            return d
    return ""


# [VRN-ID] VRN-ENG014-FNC021 · LOGIC
def _with_verb(clean, span, B):
    """'Raising TP to ...' / '調升目標價至 ...': a direction word right before the target-price phrase belongs to it."""
    head = clean[:span[0]]
    m = re.search(r"(" + B.tp_dir_words.pattern + r")\s*$", head, re.I)
    return [m.start(1), span[1]] if m else list(span)


# [VRN-ID] VRN-ENG014-FNC022 · LOGIC
def tp_change(clean, B):
    """Target price in the title: prior -> current and the direction word (as printed)."""
    got = _tp_change(clean, B)
    if got:
        got["span"] = _with_verb(clean, got["span"], B)
        got["text"] = clean[got["span"][0]:got["span"][1]]
        if not got.get("direction"):
            dw = B.tp_dir_words.match(got["text"])
            got["direction"] = _direction(dw.group(0), B) if dw else ""
    return got


# [VRN-ID] VRN-ENG014-FNC023 · LOGIC
def _tp_change(clean, B):
    m = B.tp_from_to.search(clean)
    if m:
        prior, cur = _num(m.group(1)), _num(m.group(2))
        dw = B.tp_dir_words.search(clean[m.start():m.end() + 6])
        d = _direction(dw.group(0), B) if dw else ""
        if not d and prior is not None and cur is not None:
            d = "up" if cur > prior else ("down" if cur < prior else "same")
        return {"prior": prior, "current": cur, "direction": d, "text": m.group(0), "span": list(m.span())}
    m = B.tp_to_from.search(clean)
    if m:
        cur, prior = _num(m.group(1)), _num(m.group(2))
        dw = B.tp_dir_words.search(clean[max(0, m.start() - 12):m.end()])
        d = _direction(dw.group(0), B) if dw else ("up" if (cur or 0) > (prior or 0) else "down" if (cur or 0) < (prior or 0) else "same")
        return {"prior": prior, "current": cur, "direction": d, "text": m.group(0), "span": list(m.span())}
    m = B.tp_dir_to.search(clean)
    if m:
        word = m.group("d1") or m.group("d2") or ""
        return {"prior": None, "current": _num(m.group(m.lastindex)), "direction": _direction(word, B), "text": m.group(0),
                "span": list(m.span())}
    m = B.tp_plain.search(clean)
    if m:
        return {"prior": None, "current": _num(m.group(1)), "direction": "", "text": m.group(0), "span": list(m.span())}
    return None


# [VRN-ID] VRN-ENG014-FNC024 · LOGIC
def _company_before(clean, span):
    """Company = the run of letters right before the code (台積電(2330 TT) / TSMC (2330 TT))."""
    head = clean[:span[0]].rstrip(" -:|/")
    m = re.search(r"([一-鿿A-Za-z0-9&.\-]+(?:[ ][A-Za-z][A-Za-z0-9&.\-]*){0,3})\s*$", head)
    if not m:
        return "", None
    name = m.group(1).strip(" -.")
    name = re.split(r"[:|/]", name)[-1].strip()
    if not name or re.fullmatch(r"[\d.]+", name):
        return "", None
    return name, [head.rfind(name), head.rfind(name) + len(name)]


# [VRN-ID] VRN-ENG014-FNC025 · LOGIC
def decompose_title(text, ctx=None, B=None, brd=None):
    """def02 segment order: company, ticker, market, report type, core view, rating action, target-price change."""
    B = B or books()
    ctx = ctx or {}
    t = trim(text, B)
    clean = t["clean"]
    fn = ctx.get("filename") or {}
    seg = {}
    used = []
    hits = _ticker_hits(clean, B, fn.get("ticker"))
    codes = sorted({h["code"] for h in hits})
    subject = None
    if len(codes) == 1:
        subject = next(h for h in hits if h["code"] == codes[0])
    elif len(codes) > 1:
        subject = next((h for h in hits if h["code"] == str(fn.get("ticker") or "")), None)
    if subject:
        used.append(subject["span"])
        state = "REVIEW" if subject["year_band"] and subject["code"] != str(fn.get("ticker") or "") else "READ"
        seg["ticker"] = {"value": subject["code"], "text": clean[subject["span"][0]:subject["span"][1]], "form": subject["form"],
                         "state": state, "candidates": codes if len(codes) > 1 else []}
        market = B.book["ticker"]["market_of_form"].get(subject["form"], "") if subject["form"] else ""
        seg["market"] = {"value": market, "text": subject["form"],
                         "state": "READ" if market else ("UNKNOWN_NO_GENERATE" if subject["form"] else "NOT_PRINTED"),
                         "why": "" if market else B.book["ticker"]["market_rule"]}
    else:
        seg["ticker"] = {"value": "", "text": "", "state": "REVIEW" if len(codes) > 1 else "NOT_PRINTED", "candidates": codes,
                         "why": "多個代號，第一個不當主體（def02 multi_ticker_first_not_assumed_subject）" if len(codes) > 1 else ""}
        seg["market"] = {"value": "", "text": "", "state": "NOT_PRINTED"}
    company, cspan = ("", None)
    person, pspan = "", None
    if subject:
        company, cspan = _company_before(clean, subject["span"])
        if company and _is_analyst(company, ctx):
            person, pspan, company, cspan = company, cspan, "", None
    # 擋掉人名之後**不拿檔名頂上**。頂上去的話「標題」這一票的值其實來自檔名，
    # _vote 數的是群組數,標題＋檔名就會變成「兩個來源一致」—— 一個來源假裝成兩個。
    # 標題沒印公司就是沒印：照實 NOT_PRINTED,讓檔名那一票單獨成立（SINGLE，優先 3）。
    if not company and not person:
        for name in fn.get("company_names") or []:
            at = t["fold"].find(trim(name, B)["fold"])
            if name and at >= 0:
                company, cspan = clean[at:at + len(trim(name, B)["clean"])], [at, at + len(trim(name, B)["clean"])]
                break
    for w in sorted(B.nr_words, key=len, reverse=True):     # round 6: '未評等瑞基(4171 TT)' -> 瑞基
        if company and company.casefold().startswith(w) and len(company) > len(w) + 1 and re.search(r"[一-鿿]", w):
            company = company[len(w):].lstrip(" -_:")
            if cspan:
                cspan = [cspan[0] + len(w), cspan[1]]
            break
    if not company and not person:                       # 2026-10-20: 'Wiwynn - Smoother transition' -> core view 'Smoother transition'
        for name in ((ctx.get("engine") or {}).get("company"), (ctx.get("basic") or {}).get("NameDB")):
            key = trim(name, B)["fold"] if name else ""
            at = t["fold"].find(key) if key else -1
            if at >= 0 and len(key) >= 2:
                used.append([at, at + len(trim(name, B)["clean"])])   # used up only: the title's company vote stays NOT_PRINTED
                break
    if cspan:
        used.append(cspan)
    if pspan:
        # 認出它是人名之後,那一段**還是「用掉了」**：標題確實印了這幾個字,也知道它是什麼。
        # 不標的話核心觀點會把它收進去 —— 2026-10-19 G18 鎖正是這樣擋下我這一改的連帶退步
        # （`營運動能延續,評價仍具吸引力` → `賴偉中, 營運動能延續,評價仍具吸引力`）。
        used.append(pspan)
    seg["company"] = {"value": company, "text": company, "state": "READ" if company else "NOT_PRINTED"}
    if person:
        seg["company"]["why"] = f"標題代號前面那一段是這份報告的分析師（{person}），不是公司名"
        seg["company"]["rejected"] = person
    types = _report_types(clean, B)
    for ty in types:
        used.append(ty["span"])
    if len(types) == 1:
        seg["report_type"] = {"value": types[0]["code"], "text": types[0]["word"], "state": "READ", "candidates": []}
    elif types:
        seg["report_type"] = {"value": "", "text": " / ".join(x["word"] for x in types), "state": "REVIEW",
                              "candidates": [{"code": x["code"], "word": x["word"], "confidence": round(1 / len(types), 3)} for x in types],
                              "why": "def02 ambiguous_rule：無法唯一分類 = 保留候選 + 信心分數，不強制選一"}
    else:
        seg["report_type"] = {"value": "", "text": "", "state": "NOT_PRINTED", "candidates": []}
    act = _rating_action(clean, B, brd)
    if act:
        used.append(act["span"])
        seg["rating_action"] = {"value": act["action"], "text": clean[act["span"][0]:act["span"][1]], "verb": act["verb"],
                                "rating_printed": act["rating_printed"], "state": "READ"}
    else:
        seg["rating_action"] = {"value": "", "text": "", "state": "NOT_PRINTED"}
    tp = tp_change(clean, B)
    if tp:
        used.append(tp["span"])
        seg["tp_change"] = {"value": _tp_value(tp), "text": tp["text"], "prior": tp["prior"], "current": tp["current"],
                            "direction": tp["direction"], "state": "READ"}
    else:
        seg["tp_change"] = {"value": "", "text": "", "state": "NOT_PRINTED"}
    rest = list(clean)
    for a, b in used:
        for i in range(max(0, a), min(len(rest), b)):
            rest[i] = "\x00"
    pieces = [B.sep_rx.sub("", p).strip() for p in re.split(r"\x00+", "".join(rest))]
    # 2026-10-20: '慧洋-KY - 獲利將創四年新高' leaves '-KY' in front of the view once 慧洋 is used up; the listing marker is not a view
    pieces = [B.sep_rx.sub("", re.sub(r"^-?\s*KY(?![A-Za-z])", "", p, flags=re.I)).strip() for p in pieces]
    pieces = [p for p in pieces if len(p) >= 2 and not re.fullmatch(r"[\W\d_]+", p)]
    core = ", ".join(pieces)
    seg["core_view"] = {"value": core, "text": core, "state": "READ" if core else "NOT_PRINTED"}
    order = B.method.get("def02_title", {}).get("segment_order") or []
    return {"raw": t["raw"], "clean": clean, "steps": t["steps"], "loss": t["loss"], "pua": t["pua"], "segments": seg,
            "segment_order": order}


# [VRN-ID] VRN-ENG014-FNC026 · LOGIC
def _tp_value(tp):
    # [VRN-ID] VRN-ENG014-FNC027 · LOGIC
    def f(v):
        return "" if v is None else (f"{v:,.2f}".rstrip("0").rstrip("."))
    arrow = f"{f(tp.get('prior'))}→{f(tp.get('current'))}" if tp.get("prior") is not None else f(tp.get("current"))
    return arrow + (f" {tp['direction']}" if tp.get("direction") else "")


# [VRN-ID] VRN-ENG014-FNC028 · LOGIC
def title_candidates(page, ctx=None, B=None, brd=None):
    """def02 zone_priority -> scored candidates (source, text, size, top, score, why)."""
    B = B or books()
    ctx = ctx or {}
    ti = B.book["title"]
    sc = ti["score"]
    lines = page["lines"]
    height = page.get("height") or 0.0
    body = [l for l in lines if not height or l["top"] < height * ti["footer_fraction"]]
    sizes = sorted({l["size"] for l in body if l["size"]}, reverse=True)
    font1 = sizes[0] if sizes else None
    font2 = sizes[1] if len(sizes) > 1 else None
    fn = ctx.get("filename") or {}
    names = [trim(n, B)["fold"] for n in fn.get("company_names") or [] if n]
    out = []

    # [VRN-ID] VRN-ENG014-FNC029 · LOGIC
    def score(text, extra, why):
        t = trim(text, B)
        clean = t["clean"]
        s, reasons = 0, list(why)
        if len(clean) < ti["min_chars"] or B.noise_rx.match(clean):
            return sc["noise"], reasons + ["雜訊（頁碼／日期／網址／電郵）"], t
        if _contact_line(clean, B):
            return sc["noise"], reasons + ["聯絡資訊（電話／電郵），不是標題"], t
        hits = _ticker_hits(clean, B, fn.get("ticker"))
        rest = clean
        for h in sorted(hits, key=lambda h: -h["span"][0]):
            rest = rest[:h["span"][0]] + " " + rest[h["span"][1]:]
        if hits and re.search(r"[A-Za-z\u4e00-\u9fff]{2,}", rest):
            s += sc["ticker"]
            reasons.append("有代號")
        elif hits:
            reasons.append("只有代號（代號欄，不是標題）")   # 2026-10-20 (JPM): the code box '2330.TW, 2330 TT' outscored 'TSMC'
        if any(n and n in t["fold"] for n in names):
            s += sc["company"]
            reasons.append("有公司名")
        if _report_types(clean, B):
            s += sc["report_type"]
            reasons.append("有報告類型")
        if tp_change(clean, B) or (brd is not None and brd.rating_matches(clean)):
            s += sc["rating_or_tp"]
            reasons.append("有評等或目標價")
        header = any(w.casefold() in t["fold"] for w in ti["header_words"]) or (brd is not None and brd.broker_matches(clean)
                                                                                 and not _ticker_hits(clean, B, fn.get("ticker")))
        if header and s < sc["ticker"]:
            s += sc["header_only"]
            reasons.append("券商頁首")
        return s + extra, reasons, t
    meta = (page.get("meta_title") or "").strip()
    if meta and not B.meta_junk_rx.match(meta):
        s, why, t = score(meta, sc["meta"], ["PDF metadata Title"])
        out.append({"source": "META", "text": t["clean"], "raw": meta, "size": None, "top": None, "index": -1, "score": s, "why": why})
    for i, l in enumerate(body):
        tags, extra = [], 0
        if height and l["top"] < height * ti["top_fraction"]:
            tags.append("TOP25")
            extra += sc["top25"]
        if font1 and l["size"] == font1:
            tags.append("FONT1")
            extra += sc["font1"]
        elif font2 and l["size"] == font2:
            tags.append("FONT2")
            extra += sc["font2"]
        if i < ti["first_lines"]:
            tags.append("FIRST3")
        if not tags:
            continue
        s, why, t = score(l["text"], extra, tags)
        if "FIRST3" in tags and tags == ["FIRST3"] and s < sc["ticker"]:
            continue                                   # def02: the first lines count only when they carry company + code + type
        out.append({"source": "+".join(tags), "text": t["clean"], "raw": l["text"], "size": l["size"], "top": l["top"], "index": i,
                    "score": s, "why": why})
    out.sort(key=lambda c: (-c["score"], c["top"] if c["top"] is not None else -1))
    return out, body


INTL_TEL_RX = re.compile(r"(?<![\d.])\+\d{1,3}[ \-]?(?:\(?\d{1,4}\)?[ \-]?)?\d{3,4}[ \-]?\d{4}(?!\d)")   # +852 2848-7310 (the book's tel_rx is Taiwan's)


# [VRN-ID] VRN-ENG014-FNC100 · LOGIC
def _headline_below(body, best, ti, B):
    """2026-10-20 (CLSA 'Wiwynn' over 'Smoother transition', JPM 'TSMC' over 'Margin test passed; …'): the largest line is the
    company name alone and the headline is the next line in the same column that is larger than the body text.  A rating /
    price line between them ('NT$3,300.00 - OUTPERFORM') is the rating box and is passed over; the headline's own next line
    of the same size joins it.  Nothing larger than the body text below the name -> no headline (nothing is borrowed)."""
    sizes = sorted(ln["size"] for ln in body if ln["size"])
    body_size = sizes[len(sizes) // 2] if sizes else 0.0
    rb = body[best["index"]].get("bbox") or []

    # [VRN-ID] VRN-ENG014-FNC101 · LOGIC
    def same_column(ln):
        lb = ln.get("bbox") or []
        return not (len(rb) == 4 and len(lb) == 4 and (lb[2] < rb[0] or lb[0] > rb[2]))

    # [VRN-ID] VRN-ENG014-FNC102 · LOGIC
    def skip(clean):
        digits = sum(ch.isdigit() for ch in clean)
        return (B.noise_rx.match(clean) or _contact_line(clean, B) or _label_led(clean, B)
                or digits >= 0.25 * max(1, len(clean.replace(" ", ""))))
    out = []
    for j in range(best["index"] + 1, min(len(body), best["index"] + 8)):
        ln = body[j]
        if not same_column(ln):
            continue
        t = trim(ln["text"], B)
        if not out:
            if skip(t["clean"]) or not ln["size"] or ln["size"] <= body_size:
                if ln["size"] and ln["size"] > body_size:
                    continue                                # the rating box between the name and the headline
                break
            out.append({"source": "JOIN", "text": t["clean"], "raw": ln["text"], "size": ln["size"], "top": ln["top"], "index": j})
            continue
        prev = out[-1]
        if (abs(ln["size"] - prev["size"]) > 0.15 * prev["size"] or not 0 < ln["top"] - prev["top"] <= ti["join_gap_ratio"] * prev["size"] * 1.6
                or skip(t["clean"]) or len(out) >= ti["max_join_lines"] - 1):
            break
        out.append({"source": "JOIN", "text": t["clean"], "raw": ln["text"], "size": ln["size"], "top": ln["top"], "index": j})
    return out


# [VRN-ID] VRN-ENG014-FNC103 · LOGIC
def _label_led(clean, B):
    """2026-10-20 (華南 '投資建議', JPM 'Price (17 Jul 25):NT$1130.0'): a line that starts with a cover label followed by its value
    (or by nothing) is the rating box, not the next line of the title.  'TP raised to …' is prose and stays joinable."""
    low = clean.casefold().strip()
    for field in ("rating", "target_price", "current_price", "upside"):
        for lab in B.labels[field]:
            lab_f = lab.casefold()
            if low.startswith(lab_f) and re.match(r"^\s*(?:$|[:：(（]|[\d$]|nt\$)", low[len(lab_f):]):
                return True
    return False


# [VRN-ID] VRN-ENG014-FNC104 · LOGIC
def _contact_line(clean, B):
    """2026-10-20 (operator: VRN-1 auto-fix until 100% correct): the MS / CLSA analyst box ('+886 2 2730-2865', 'Samantha Chen') was
    the title; a line with a phone number or an e-mail address is the analyst box, not a title, and a title does not join it."""
    if B.email_rx.search(clean) or INTL_TEL_RX.search(clean):
        return True
    return any(not (m.start() and (clean[m.start() - 1].isdigit() or clean[m.start() - 1] == ".")) for m in B.tel_rx.finditer(clean))


# [VRN-ID] VRN-ENG014-FNC030 · LOGIC
def pick_title(page, ctx=None, B=None, brd=None):
    """Best candidate; lines right above / below of nearly the same size joined (a title set on two lines)."""
    B = B or books()
    ti = B.book["title"]
    cands, body = title_candidates(page, ctx, B, brd)
    good = [c for c in cands if c["score"] > 0]
    if not good:
        return {"text": "", "raw": "", "source": "", "candidates": cands[:8], "joined": []}
    best = good[0]
    joined = [best]
    used = set()
    if best["index"] >= 0 and best["size"]:
        i = best["index"]
        # 2026-10-20 (瑞基): the same row in the same type size, left to right ('瑞基(4171 TT)' ... '未評等'), is one title line
        row = [k for k, ln in enumerate(body) if k != i and ln["size"] and abs(ln["top"] - best["top"]) <= 0.3 * best["size"]
               and abs(ln["size"] - best["size"]) <= 0.15 * best["size"] and not _contact_line(trim(ln["text"], B)["clean"], B)
               and not B.noise_rx.match(trim(ln["text"], B)["clean"])]
        if row:
            used = set(row) | {i}
            raw_row = " ".join(body[k]["text"].strip() for k in sorted(used, key=lambda k: body[k]["x0"]))
            joined = [dict(best, raw=raw_row, text=trim(raw_row, B)["clean"])]
        for step in (-1, 1):
            j = i + step
            while 0 <= j < len(body) and len(joined) < ti["max_join_lines"]:
                if j in used:
                    j += step
                    continue
                ln = body[j]
                ref = joined[0] if step < 0 else joined[-1]
                gap = (ref["top"] - ln["top"]) if step < 0 else (ln["top"] - ref["top"])
                rb, lb = body[ref["index"]].get("bbox") or [], ln.get("bbox") or []
                if len(rb) == 4 and len(lb) == 4 and (lb[2] < rb[0] or lb[0] > rb[2]):   # 2026-10-20 (MS): the analyst column prints between the two title lines
                    if gap <= ti["join_gap_ratio"] * best["size"] * 1.6:
                        j += step
                        continue
                    break
                if not (ln["size"] and ln["size"] >= ti["join_size_ratio"] * best["size"] and 0 < gap <= ti["join_gap_ratio"] * best["size"] * 1.6):
                    break
                t = trim(ln["text"], B)
                if (B.noise_rx.match(t["clean"]) or _contact_line(t["clean"], B) or _label_led(t["clean"], B)
                        or any(w.casefold() in t["fold"] for w in ti["header_words"])):
                    break
                item = {"source": "JOIN", "text": t["clean"], "raw": ln["text"], "size": ln["size"], "top": ln["top"], "index": j}
                joined = [item] + joined if step < 0 else joined + [item]
                j += step
    if best["index"] >= 0 and best["size"] and len(joined) == 1 and len(_bare_text(joined[0]["text"])) <= 12 \
            and not _ticker_hits(joined[0]["text"], B):
        joined += _headline_below(body, best, ti, B)
    raw = " - ".join(x["raw"] for x in joined)
    return {"text": trim(raw, B)["clean"], "raw": raw, "source": best["source"] + ("+JOIN" if len(joined) > 1 else ""),
            "candidates": cands[:8], "joined": [x["text"] for x in joined]}


# =====================================================================
# 4 . COVER (def03 zones; every field read from the TRIMmed lines)
# =====================================================================
# [VRN-ID] VRN-ENG014-FNC031 · LOGIC
def _zone(line, clean, height, B, title_tops):
    cv = B.book["cover"]
    low = clean.casefold()
    if height and line["top"] >= height * B.book["title"]["footer_fraction"] or any(w.casefold() in low for w in cv["footer_words"]):
        return "Footer"
    if line["top"] in title_tops:
        return "TitleZone"
    for field in ("rating", "target_price", "current_price", "upside"):
        if any(lab.casefold() in low for lab in B.labels[field]):
            return "RatingBox"
    if B.email_rx.search(clean) or B.tel_rx.search(clean) or any(lab.casefold() in low for lab in B.labels["analyst"]):
        return "AnalystBox"
    if height and line["top"] < height * cv["header_fraction"]:
        return "TopHeader"
    if any(w.casefold() in low for w in cv["key_metric_words"]):
        return "KeyMetrics"
    return "SummaryBox"


# [VRN-ID] VRN-ENG014-FNC062 · LOGIC
def _label_hits(clean, labels, B):
    """Every label occurrence, leftmost first (longest label at the same place): (label, value after it, position).
    A label inside an e-mail address or a URL (analyst@...) is not a label."""
    low = clean.casefold()
    hits = []
    for lab in labels:
        ll = lab.casefold()
        for m in re.finditer(re.escape(ll), low):
            before = low[m.start() - 1] if m.start() else " "
            after = low[m.end()] if m.end() < len(low) else " "
            if re.search(r"[A-Za-z]", lab) and (before.isalpha() or after.isalpha()):
                continue
            if after in "@." or before in "@./" or re.match(r"\S*@", low[m.end():]):
                continue
            if any(low[:m.start()].rstrip(" (").endswith(w) for w in B.prior_words):
                continue                                  # 前次目標價 / Prior TP: not the current one
            if B.prior_before_rx.search(low[max(0, m.start() - B.prior_before_chars):m.start()]):
                continue                                  # 'upside to TP', '前次評等 目標價' (Evidence core _TP_EXCLUDE_BEFORE)
            tail = clean[m.end():]
            tail = re.sub(r"^\s*(?:\([^)]{0,28}\))?\s*[:=]?\s*", "", tail)   # round 5: '(as of 4 Jun 2025)' is a date, not the value
            stop = B.value_stop_rx.search(tail[1:]) if tail else None
            value = tail[:stop.start() + 1] if stop else tail
            hits.append((m.start(), -len(lab), lab, value.strip()))
    hits.sort()
    return [(lab, value, at) for at, _n, lab, value in hits]


# [VRN-ID] VRN-ENG014-FNC032 · LOGIC
def _after_label(clean, labels, B):
    """The leftmost label and the text right after it (':' optional), up to the next label."""
    hits = _label_hits(clean, labels, B)
    return hits[0] if hits else (None, "", -1)


# [VRN-ID] VRN-ENG014-FNC033 · LOGIC
def _date_of(clean, B):
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11,
              "dec": 12}
    for i, rx in enumerate(B.date_rx):
        m = rx.search(clean)
        if not m:
            continue
        g = m.groups()
        try:
            if i in (0, 1):
                y, mo, d = int(g[0]), int(g[1]), int(g[2])
            elif i == 2:
                y, mo, d = int(g[0]) + 1911, int(g[1]), int(g[2])
            elif i == 3:
                d, mo, y = int(g[0]), months[g[1][:4].lower().rstrip(".")] if g[1][:4].lower() in months else months[g[1][:3].lower()], int(g[2])
            else:
                mo, d, y = months[g[0][:4].lower()] if g[0][:4].lower() in months else months[g[0][:3].lower()], int(g[1]), int(g[2])
            time.strptime(f"{y:04d}-{mo:02d}-{d:02d}", "%Y-%m-%d")
        except (ValueError, KeyError):
            continue
        if i in (0, 2) and not _date_shape_ok(m.group(0), clean[m.end():]):
            continue                                      # round 6: '150.8 / 4,777' is a number pair, not ROC 150-08-04
        if y > time.localtime().tm_year + 1:
            continue
        return f"{y:04d}-{mo:02d}-{d:02d}", m.group(0)
    return None, ""


# [VRN-ID] VRN-ENG014-FNC080 · LOGIC
def _date_shape_ok(text, after):
    """Round 6 (2026-10-12): both separators the same, no space beside a dot, and no ',ddd' right after (4,777)."""
    seps = re.findall(r"\D+", text.strip().rstrip("日"))
    if len(seps) >= 2:
        a, b = seps[0].strip(), seps[1].strip()
        if not ((a == b) or (a == "年" and b == "月")):
            return False
        if "." in a and seps[0] != a:
            return False
    return not re.match(r",\d{3}", after)


# [VRN-ID] VRN-ENG014-FNC065 · LOGIC
def _broker_of(zones, brd, B, fragments=()):
    """Broker from the page: header, title and analyst lines first, then the body, the disclaimer last.  An alias that is a
    plain word (first, capital, mega, ms, gs …, 第一, 統一 …) counts only when 證券 / Securities / Research … follows it.
    `fragments`: the covered company's names (中信金, 國泰金): an alias at their start is the company, not the broker."""
    for group in B.book["cover"]["broker_zone_order"]:
        lines = [z for z in zones if z["zone"] in group]
        for z in lines:
            low = z["clean"].casefold()
            for h in brd.broker_matches(z["clean"], exclude_prefix_fragments=tuple(f for f in fragments if f)):
                alias = h["alias"].casefold()
                if not _broker_alias_ok(low, alias, B):
                    continue
                return {"value": h["broker"], "text": h["alias"], "line": z["line"], "zone": z["zone"]}
    return None


# [VRN-ID] VRN-ENG014-FNC081 · LOGIC
def _broker_alias_ok(low, alias, B):
    """Round 6 (2026-10-12): one occurrence of the alias has to stand as a broker name: not inside an e-mail address or a URL
    (daiwacm-cathay.com.tw is read through the merged book's domains), a Chinese alias not right after a digit (3.37元大致),
    a plain-word alias (台新, 元大, first, mega …) only with 證券 / 投顧 / Securities … after it."""
    generic = alias in B.broker_generic
    cjk = bool(re.search(r"[一-鿿]", alias))
    for m in re.finditer(re.escape(alias), low):
        a, b = m.start(), m.end()
        left = low[:a].rsplit(None, 1)[-1] if low[:a] and not low[:a][-1].isspace() else ""
        right = low[b:].split(None, 1)[0] if low[b:] and not low[b:][0].isspace() else ""
        token = left + alias + right
        if "@" in token or token.startswith(("http", "www.")) or re.search(r"\.(?:com|net|org)(?:\.[a-z]{2})?\b", token):
            continue
        if cjk and a and (low[a - 1].isdigit() or low[a - 1] == "."):
            continue
        if not cjk and ((a and low[a - 1].isalnum()) or (b < len(low) and low[b].isalnum())):
            continue
        if generic and not re.match(B.broker_context_rx, low[b:]):
            continue
        return True
    return False


# [VRN-ID] VRN-ENG014-FNC071 · LOGIC
def _prior_lines(lines, clean, B):
    """Real run 2026-10-12 (round 3): in the 兆豐 layout the right-hand box ('前次投資建議：日期' over '「買進」,目標價: 78') is
    interleaved with body lines of the left column once lines are sorted by y, so 'the next line' is found by geometry: the
    nearest line below the 前次 line (gap <= max_gap_lines line heights) that overlaps it horizontally.  Lines without a box
    (TXT / DOCX) fall back to reading order.  -> [bool] per line."""
    n = len(lines)
    flags = [False] * n
    for h in range(n):
        if not B.prior_line_rx.search(clean[h]):
            continue
        hb = lines[h].get("bbox") or []
        if len(hb) < 4:
            if h + 1 < n:
                flags[h + 1] = True
            continue
        size = float(lines[h].get("size") or 0) or 10.0
        best = None
        for i in range(n):
            b = lines[i].get("bbox") or []
            if i == h or len(b) < 4 or b[1] < hb[3] - 1.0 or b[1] - hb[3] > B.prior_gap * size:
                continue
            if b[2] <= hb[0] or b[0] >= hb[2]:
                continue
            if best is None or b[1] < (lines[best]["bbox"][1]):
                best = i
        if best is not None:
            flags[best] = True
    return flags


_DOMAIN_BOOK = None
_LOCALDB = None


# [VRN-ID] VRN-ENG014-FNC085 · LOGIC
def _db_module_open():
    """The operator's database (VRN_LocalDB: the vdf_database parquet folder first, the duckdb files after), opened once."""
    global _LOCALDB
    if _LOCALDB is None:
        try:
            path = Path(__file__).resolve().parent / "VRN_LocalDB_v0100.py"
            spec = importlib.util.spec_from_file_location("vrn_titletrim_localdb", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["vrn_titletrim_localdb"] = mod
            spec.loader.exec_module(mod)
            _LOCALDB = mod.LocalDB()
        except Exception:  # noqa: BLE001
            _LOCALDB = False
    return _LOCALDB if (_LOCALDB and getattr(_LOCALDB, "status", "") == "OK") else None


# [VRN-ID] VRN-ENG014-FNC086 · LOGIC
def db_lookup(code, report_date=None):
    """{name, name_source, closes, path} for a 4-digit code from the database, or {} (no database / no such code)."""
    ldb = _db_module_open()
    if ldb is None or not code:
        return {}
    name = ldb.names().get(str(code))
    out = {"path": str(ldb.path), "source": getattr(ldb, "source", "")}
    if name:
        out.update(name=name[0], name_source=name[3])
    if report_date:
        out["closes"] = ldb.closes(str(code), str(report_date)[:10])
    return out


# [VRN-ID] VRN-ENG014-FNC087 · LOGIC
def _db_name(ctx, code):
    """The database's company name: the run's lookup (ctx["db"]) first, else the database engine's NameDB."""
    look = (ctx or {}).get("db")
    if callable(look) and code:
        try:
            got = look(code, None) or {}
        except Exception:  # noqa: BLE001
            got = {}
        if got.get("name"):
            return got["name"]
    return ((ctx or {}).get("basic") or {}).get("NameDB") or ""


# [VRN-ID] VRN-ENG014-FNC088 · LOGIC
def _db_closes(ctx, code, report_date):
    look = (ctx or {}).get("db")
    if not (callable(look) and code and report_date):
        return {}
    try:
        return (look(code, report_date) or {}).get("closes") or {}
    except Exception:  # noqa: BLE001
        return {}


# [VRN-ID] VRN-ENG014-FNC089 · LOGIC
def _db_company_part(db_name, readings, B):
    """The company is the database's name.  VERIFIED: a reading in the same script is the same company; CONFLICT: the same-script
    readings all name another; SINGLE: no reading to compare (the report prints the English name, or none)."""
    script = _script(db_name)
    same_script = [r for r in readings if _script(r[2]) == script]
    agree = [r for r in same_script if _company_same(r[2], db_name, B)]
    sources = {"資料庫": db_name}
    for _g, n, v in readings:
        sources[n if _script(v) == script else f"{n}（不同文字，不比）"] = v
    if agree:
        state, why = "VERIFIED", "公司名取資料庫；" + "＋".join(dict.fromkeys(r[1] for r in agree)) + " 讀到的是同一家"
    elif same_script:
        state, why = "CONFLICT", "公司名取資料庫；報告讀到的（" + "、".join(dict.fromkeys(str(r[2]) for r in same_script)) + "）不是同一家，要人看"
    else:
        state, why = "SINGLE", "公司名取資料庫；" + ("報告印的是另一種文字的名稱，不比" if readings else "報告沒讀到公司名")
    # 2026-10-20：手工組 part 的四條路都少了 `agree`。資料庫自己是一組，讀到同一家的那些讀法
    # 各算自己那一組 ——「是不是同一家」是上面 `_company_same` 判的，這裡只數它判出來的結果。
    return {"part": "title.company", "value": db_name, "state": state, "sources": sources, "why": why, "source": "db",
            "agree": 1 + len({r[0] for r in agree}), "printed": readings[0][2] if readings else ""}


# [VRN-ID] VRN-ENG014-FNC090 · LOGIC
def _db_price_part(quote, cp_votes, same):
    """現價：**值以 adj close 為基準**，**狀態仍然比原始收盤價**。

    操作員 2026-10-16：「全部使用最新的 adj close 或報告前一日的 adj close 為基準動態更新」。

    為什麼狀態不跟著改用 adj：報告印在紙上的是原始收盤價，不是還原價（handover L99／L104，
    本引擎 closes() 的註解也這麼寫）。拿 adj 去比對印出來的數字，只要那檔除過權息就一律
    判成 CONFLICT —— 那不是讀錯，是拿兩種不同的量去比。所以比對用 close，帶走的值用 adj。

    基準日取報告日前最後一個交易日（與這份報告對應的那一天）；庫裡沒有那天的 adj 就退到最新
    一天的 adj。adj_close 缺就是缺，不拿 close 頂替（L99）—— 那種情況值照實是原始收盤價，why 會說。

    dynamic=True：這個值庫一更新就會變，是設計如此。輸出鎖不把它的變動當退步（否則同一份
    報告隔天再跑必紅 —— 2026-10-16 實測 534 檔，12 個 BROKEN 全部是這個部位）。
    """
    readings = [(g, n, v) for g, n, v in cp_votes if v not in (None, "")]
    cands = [c for c in (quote.get("basis"), quote.get("same")) if c]
    adj_on = dict(x for x in (quote.get("basis_adj"), quote.get("same_adj"), quote.get("latest_adj")) if x)
    latest_adj = quote.get("latest_adj")
    sources = {n: v for _g, n, v in readings}
    for d, c in cands:
        sources[f"資料庫收盤價 {d}"] = c
    for d, a in sorted(adj_on.items()):
        sources[f"資料庫 ADJ CLOSE {d}"] = a

    # [VRN-ID] VRN-ENG014-FNC092 · LOGIC
    def basis(d, c):
        """(值, 基準日, why 用的說法) —— 基準日**與「印的價對到哪一天」無關**。

        裁決只點名兩種基準：報告前一日的 adj close、最新的 adj close。報告當日的 adj
        不在其中，所以不能因為印的價剛好對到當日收盤價就改用當日的 adj —— 那會讓同一個
        欄位的基準隨報告印什麼而跳動。對到哪一天只決定狀態（VERIFIED／CONFLICT）。
        缺 adj 才照實回原始收盤價（L99：不拿 close 當 adj）。
        """
        for tag, got in (("報告日前", quote.get("basis_adj")), ("最新", quote.get("latest_adj"))):
            if got:
                return got[1], got[0], f"{tag} ADJ CLOSE {got[0]}"
        return c, d, f"收盤價 {d}（庫裡沒有 ADJ CLOSE，不拿 close 當 adj）"

    match = next(((d, c, [r for r in readings if same(r[2], c)]) for d, c in cands if any(same(r[2], c) for r in readings)), None)
    if match:
        d, c, agree = match
        value, on, how = basis(d, c)
        # 2026-10-20：同上 —— 資料庫一組，印的價與它相同的那些讀法各算一組（`same` 已經判過）。
        return {"part": "cover.current_price", "value": value, "state": "VERIFIED", "sources": sources, "source": "db", "date": on,
                "agree": 1 + len({r[0] for r in agree}),
                "dynamic": True, "close": c, "printed": agree[0][2],
                "why": f"現價取資料庫 {how}（動態更新）；" + "＋".join(dict.fromkeys(r[1] for r in agree)) + f" 印的 {c} 與 {d} 收盤價相同"}
    d, c = cands[0]
    value, on, how = basis(d, c)
    if readings:
        return {"part": "cover.current_price", "value": value, "state": "CONFLICT", "sources": sources, "source": "db", "date": on,
                "agree": 1, "dynamic": True, "close": c, "printed": readings[0][2],
                "why": f"現價取資料庫 {how}（動態更新）；報告印的（" + "、".join(str(r[2]) for r in readings) +
                "）和資料庫報告日前後的收盤價都不同，要人看"}
    return {"part": "cover.current_price", "value": value, "state": "SINGLE", "sources": sources, "source": "db", "date": on,
            "agree": 1, "dynamic": True, "close": c, "printed": "",
            "why": f"現價取資料庫 {how}（動態更新，報告日前最後一個交易日為基準）；報告沒印現價"}


# [VRN-ID] VRN-ENG014-FNC076 · LOGIC
def _domain_broker(domain, known=None):
    """Round 5 (2026-10-12): the e-mail domain through the merged book (ssot/VRN_TickerRecord_SSOT_v0100.json email_domain):
    daiwacm-cathay.com is DAIWA there, where a word match would say CATHAY.  Longest key first; a key two books dispute
    (a list) is skipped; no book -> None."""
    global _DOMAIN_BOOK
    if _DOMAIN_BOOK is None:
        try:
            book = json.loads((Path(__file__).resolve().parents[1] / "ssot" / "VRN_TickerRecord_SSOT_v0100.json").read_text(encoding="utf-8"))
            _DOMAIN_BOOK = {k.casefold(): v["canonical"] for k, v in ((book.get("email_domain") or {}).get("entries") or {}).items()
                            if isinstance(v, dict) and isinstance(v.get("canonical"), str)}
        except Exception:  # noqa: BLE001
            _DOMAIN_BOOK = {}
    d = str(domain or "").casefold().strip()
    if not d:
        return None
    first = d.split(".")[0]
    for key in sorted(_DOMAIN_BOOK, key=len, reverse=True):
        if d == key or d.endswith("." + key) or first == key or d.startswith(key + "."):
            if known and _DOMAIN_BOOK[key] not in known:
                continue                                  # round 6: daiwacm-cathay.com.tw -> 'DAIWA-CATHAY' is no engine key; the next key says DAIWA
            return _DOMAIN_BOOK[key]
    return None


# [VRN-ID] VRN-ENG014-FNC098 · LOGIC
def _cp_qualified(low_line, lab, at, B):
    """現價標籤旁邊有沒有把它改掉意思的字？——「12M price target」是目標價、「52 週股價 (低 \\ 高)」是一年區間。

    實測 2026-10-20：那個字得**緊鄰**標籤。標籤後面本來就是錨定的（re.match），標籤前面卻是 14 字內
    到處找（re.search）。TRIM 會把連續空白收成一個空白，「投資評等:賣出 目標價:NT$182.5 收盤價:NT$140.4」
    收完之後，**前一欄自己的「目標價」**就落進「收盤價」前面那 14 字裡——59 份個股報告的收盤價
    一份也沒讀到。兩側改成同一把尺：那個字與標籤之間**只容得下分隔符號**。

    Codex PR #75 P2：分隔符號不准列舉（`Target-Price`、`Target (Price):`、`52週-股價` 的 `-`、`(`
    都不在列舉裡，就漏成現價）。間隔「是不是只有分隔符號」借 `_bare_text` 那把尺問——
    留下字母、數字、漢字以後是空的就是相鄰，不必數標點。
    """
    end = at + len(lab)
    before, after = low_line[max(0, at - 14):at], low_line[end:end + 14]
    return (any(not _bare_text(before[m.end():]) for m in B.cp_not_near_rx.finditer(before))
            or any(not _bare_text(after[:m.start()]) for m in B.cp_not_near_rx.finditer(after)))


# [VRN-ID] VRN-ENG014-FNC034 · LOGIC
def cover_fields(page, title, B=None, brd=None, fragments=()):
    """-> {zones: [...], fields: {name: {value, text, line, zone}}} from the TRIMmed page-1 lines.
    Real run 2026-10-12 (round 2): the line after '前次投資建議：日期' / '前次評等：' holds the previous rating and target (兆豐),
    a header line that is only labels takes its values from the next line, and a number followed by %, 倍, x, (F) or '-11x' is
    not a price (the same knowledge as VRN_Evidence_Core, written in the book)."""
    B = B or books()
    height = page.get("height") or 0.0
    title_tops = {l["top"] for l in page["lines"] if trim(l["text"], B)["clean"] in (title.get("joined") or [])}
    zones, fields = [], {}
    full = []
    date_cands = []
    prior_tp = []
    declared_na = {}
    contacts = {"analyst": [], "email": [], "tel": []}
    row = B.label_row
    lines_clean = [trim(l["text"], B)["clean"] for l in page["lines"]]
    prior_flags = _prior_lines(page["lines"], lines_clean, B)
    for i, l in enumerate(page["lines"]):
        t = trim(l["text"], B)
        z = _zone(l, t["clean"], height, B, title_tops)
        bbox = l.get("bbox") or []
        zones.append({"line": i + 1, "zone": z, "raw": t["raw"], "clean": t["clean"], "steps": t["steps"], "loss": t["loss"],
                      "pua": t["pua"], "top": l["top"], "size": l["size"], "x0": round(bbox[0], 1) if bbox else None,
                      "x1": round(bbox[2], 1) if bbox else None})
        full.append(t["clean"])
        if prior_flags[i]:
            zones[-1]["prior"] = True                     # the line under 前次投資建議 / 前次評等 (same column): previous values, not read
            for lab, val, _at in _label_hits(t["clean"], B.labels["target_price"], B):
                plain = B.date_like_rx.sub(" ", val)
                prior_tp.extend(abs(n["value"]) for n in numbers(plain, B)
                                if n["kind"] == "amount" and n["value"] and not B.not_price_after_rx.match(plain[n["end"]:]))
            continue

        # [VRN-ID] VRN-ENG014-FNC035 · LOGIC
        def put(name, value, text):
            if value in (None, "") or name in fields:
                return
            fields[name] = {"value": value, "text": text, "line": i + 1, "zone": z}
        low_line = t["clean"].casefold()
        for name in ("target_price", "current_price", "upside"):
            hits = _label_hits(t["clean"], B.labels[name], B)
            if name == "current_price":                   # round 4: '12M price target NT$4,200' is the target, not the price
                hits = [h for h in hits if not _cp_qualified(low_line, h[0], h[2], B)]
            lab, val, _at = hits[0] if hits else (None, "", -1)
            if lab and name == "target_price" and B.tp_declared_none_rx.match(val or "") and "target_price" not in declared_na:
                declared_na["target_price"] = {"text": f"{lab} {val}"[:80], "line": i + 1}   # round 5b: 'Target price: n.a.'
            if lab and name == "target_price":            # round 4: 'TP from NT$3,600 to NT$4,200' -> 4,200; 3,600 is the previous one
                ft = next((m for m in (rx.search(val) for rx in B.tp_from_to_cover) if m), None)
                if ft:
                    try:
                        cur, prior = float(ft.group("cur").replace(",", "")), float(ft.group("prior").replace(",", ""))
                    except ValueError:
                        cur, prior = None, None
                    if cur:
                        put(name, cur, f"{lab} {ft.group(0)}")
                        prior_tp.append(prior)
                        continue
            if lab:
                plain = B.date_like_rx.sub(" ", val)
                nums = numbers(plain, B)     # real run 2026-10-12: '股價 2025/11/27 90.2' is 90.2, not 2025
                if name == "upside":
                    pct = next((n for n in nums if n["kind"] == "pct"
                                and (not B.upside_max_gap or plain.rfind(n["text"], 0, n["end"]) <= B.upside_max_gap)), None)   # round 6
                    if pct:
                        put(name, pct["value"], f"{lab} {pct['text']}")
                else:
                    amt = next((n for n in nums if n["kind"] == "amount" and not B.not_price_after_rx.match(plain[n["end"]:])), None)
                    if amt and abs(amt["value"]) > 0:
                        put(name, abs(amt["value"]), f"{lab} {amt['text']}")
        if (i < int(row["header_lines"]) and i + 1 < len(lines_clean) and row["label"].search(t["clean"])
                and not re.search(r"\d", t["clean"]) and "target_price" not in fields):
            m = row["value"].search(lines_clean[i + 1])    # '投資評等 目標價' / '逢低買進 $208' (兆豐 header box)
            if m:
                try:
                    put("target_price", float((m.group("num") or m.group("n2")).replace(",", "")), f"{t['clean']} / {m.group(0)}")
                except ValueError:
                    pass
        rhits = [h for h in _label_hits(t["clean"], B.labels["rating"], B)
                 if not B.rating_not_after_rx.search(low_line[max(0, h[2] - 8):h[2]])]   # round 6: 'ESG 評等社會(S)' is not the rating
        lab, val, _at = rhits[0] if rhits else (None, "", -1)
        if lab and val and brd is not None:
            hits = brd.rating_matches(val, in_rating_field=True)
            if hits:
                lowv = val.casefold()                     # round 6: the word printed first, not the dictionary's order (ties vary per run)
                pos = lambda h: lowv.find(str(h["alias"]).casefold()) if lowv.find(str(h["alias"]).casefold()) >= 0 else len(lowv)  # noqa: E731
                best = min(hits, key=lambda h: (pos(h), -len(str(h["alias"]))))
                word = brd.printed(val, best["alias"])
                at = val.find(word)
                if at >= 0 and re.search(r"[一-鿿]", word):
                    tail = val[at + len(word):at + len(word) + 2]
                    head = val[max(0, at - 2):at]
                    if tail in B.rating_tails and word not in B.rating_tails:
                        word += tail                      # round 6: 區間 -> 區間持有, as printed
                    elif word in B.rating_tails and head in B.rating_heads:
                        word = head + word                # 持有 -> 區間持有
                put("rating", word, f"{lab} {val}")
        crank = B.contact_rank.get(z, 2)
        for lab, val, _at in _label_hits(t["clean"], B.labels["analyst"], B):
            m = B.name_rx.match(val) if val else None
            if m:
                contacts["analyst"].append((crank, i, m.group(1), f"{lab} {val}", z))
                break
        for m in B.email_rx.finditer(t["clean"]):
            em = re.sub(r"^\d+(?:\.\d+)+(?=[a-z])", "", m.group(0).lower())   # round 6: '13.7terry.lee@kgi.com' = a table cell + the address
            contacts["email"].append((crank, i, em, m.group(0), z))
        for m in B.tel_rx.finditer(t["clean"]):
            if m.start() and (t["clean"][m.start() - 1].isdigit() or t["clean"][m.start() - 1] == "."):
                continue                                  # round 6: '7.6886 2 2181 8710' - a number glued to a decimal is a table cell
            main = re.split(r"\s*(?:#|ext\.?|分機)", m.group(0), maxsplit=1, flags=re.I)[0]   # round 4: the extension stays out of the number
            contacts["tel"].append((crank, i, re.sub(r"\D", "", main), m.group(0), z))
        iso, text = _date_of(t["clean"], B)
        at = t["clean"].find(text) if iso else -1
        if iso and at >= 0 and B.date_exclude_before_rx.search(t["clean"][max(0, at - 24):at]):
            iso = None                                    # '前次投資建議：2024/12/09' is the previous report's date
        if iso and z != "Footer" and not any(w in t["fold"] for w in B.date_skip):
            labelled = any(lab.casefold() in t["fold"] for lab in B.labels["date"])
            rank = 0 if labelled else B.book["cover"]["date_rank"].get(z, 6)
            date_cands.append((rank, i, iso, text, z))
    if date_cands:
        rank, i, iso, text, z = min(date_cands, key=lambda c: (c[0], c[1]))
        fields["date"] = {"value": iso, "text": text, "line": i + 1, "zone": z}
    for name, cands in contacts.items():                  # round 3: every contact on the page, the analyst box first, the footer last
        if cands:
            cands.sort(key=lambda c: (c[0], c[1]))
            seen = list(dict.fromkeys(c[2] for c in cands))
            crank, i, v, text, z = cands[0]
            fields[name] = {"value": v, "text": text, "line": i + 1, "zone": z, "all": seen}
    joined = "\n".join(full)
    if brd is not None:
        got = _broker_of(zones, brd, B, fragments)
        if got:
            fields["broker"] = got
        elif fields.get("email"):                          # round 3: no alias in the text -> the e-mail domain (kgi.com -> KGI)
            for em in fields["email"]["all"]:
                dom = em.split("@", 1)[1] if "@" in em else ""
                known = set(getattr(brd, "b", {}) or {})
                hit = (_domain_broker(dom, known) or brd.broker_normalize(dom.replace(".", " "))) if dom else None   # round 5: the merged book first
                if hit:
                    fields["broker"] = {"value": hit, "text": dom, "line": fields["email"]["line"], "zone": fields["email"]["zone"],
                                        "how": "email_domain"}
                    break
    page_hits = _ticker_hits(joined, B)
    codes = sorted({h["code"] for h in page_hits if h["how"] in ("yahoo", "bloomberg", "paren")})
    yahoo = [h for h in page_hits if h["how"] == "yahoo"]
    if yahoo:
        market = B.book["ticker"]["market_of_form"].get(yahoo[0]["form"], "")
        if market:
            fields["market"] = {"value": market, "text": joined[yahoo[0]["span"][0]:yahoo[0]["span"][1]], "line": None, "zone": "TitleZone",
                                "code": yahoo[0]["code"]}
    if codes:
        fields["ticker_codes"] = {"value": ",".join(codes), "text": ",".join(codes), "line": None, "zone": "TitleZone"}
    # 實測 2026-10-20：首頁印的 `Bloomberg 6873 TT  Yahoo 6873.TW`，TRIM 這一側本來就讀到了（`title.market` 用的就是它），
    # 但只留下市場別。代號紀錄（G20）於是只剩首頁引擎一條讀法，YF／Bloomberg 兩欄 58/59 永遠 SINGLE。
    # 這裡把讀到的碼照**首頁引擎同一個形狀**交出去（raw / core / platform / market），讓兩條讀法能互相對照。
    # [VRN-ID] VRN-ENG014-FNC099 · LOGIC
    def _page_code(h):
        """這個代號 hit 對到哪個平台。

        Codex PR #76 P2：括號裡的也算 —— `鴻海 (2317.TW)`、`TSMC (2330 TT)` 常常是整頁唯一印的碼，
        而 `_ticker_hits` 先用 paren_rx 吃掉它、壓住後面重疊的 yahoo／bloomberg 比對，`how` 就停在 "paren"。
        認不認得用**冊上同一組式子**（`yahoo_rx` / `bbg_rx`）再問一次，不另列一張形狀表
        （所以 `國光生(4142,Note)`、`(1234-KY)` 這種照樣不算平台碼）。
        """
        raw = joined[h["span"][0]:h["span"][1]].strip("()[]（）［］ ").strip()
        if h["how"] == "yahoo" or (h["how"] == "paren" and B.yahoo_rx.fullmatch(raw)):
            return {"raw": raw, "core": h["code"], "platform": "yfinance",
                    "market": B.book["ticker"]["market_of_form"].get(h["form"], "")}
        if h["how"] == "bloomberg" or (h["how"] == "paren" and B.bbg_rx.fullmatch(raw)):
            return {"raw": raw, "core": h["code"], "platform": "bloomberg", "market": ""}
        return None
    page_codes = list({(c["platform"], c["raw"]): c for c in (_page_code(h) for h in page_hits) if c}.values())
    if page_codes:
        fields["page_codes"] = {"value": ",".join(c["raw"] for c in page_codes), "text": ",".join(c["raw"] for c in page_codes),
                                "line": None, "zone": "TitleZone", "codes": page_codes}
    return {"zones": zones, "fields": fields, "prior_target_prices": sorted(set(prior_tp)), "declared_na": declared_na}


# =====================================================================
# 5 . ANNUAL FINANCIAL PAGES (G15 tables TRIMmed; the same G15 functions read them again)
# =====================================================================
# [VRN-ID] VRN-ENG014-FNC036 · LOGIC
def _trim_table(t, B):
    t2 = copy.deepcopy(t)
    t2["columns"] = [trim(c, B)["clean"] for c in t.get("columns") or []]
    t2["rows"] = [[trim(x, B)["clean"] for x in r] for r in t.get("rows") or []]
    return t2


# [VRN-ID] VRN-ENG014-FNC037 · LOGIC
def _cell_key(r, B):
    return (r.get("anchor"), trim(r.get("period_raw"), B)["clean"], fold_key(r.get("metric_raw"), B))


# [VRN-ID] VRN-ENG014-FNC063 · LOGIC
def _db_index(financial, B):
    """The database engine's FinancialData rows (its own table reader) by (printed label, printed period)."""
    idx = {}
    for row in financial or []:
        key = (fold_key(row.get("MetricNameRaw"), B), fold_key(row.get("PeriodLabelRaw"), B))
        try:
            idx.setdefault(key, []).append(float(row.get("Value")))
        except (TypeError, ValueError):
            continue
    return idx


# [VRN-ID] VRN-ENG014-FNC064 · LOGIC
def _decimals(text):
    m = re.search(r"\.(\d+)", str(text or ""))
    return len(m.group(1)) if m else 0


# [VRN-ID] VRN-ENG014-FNC038 · LOGIC
def annual(result, B=None, financial=None):
    """The G15 result of one file -> annual pages, cells (before / after TRIM), checks before / after, null and triangle cells.
    `financial`: the database engine's FinancialData rows of the same file -- a second reader of the same tables."""
    B = B or books()
    db_idx = _db_index(financial, B)
    R, M = regions()
    an = B.book["annual"]
    name = result.get("file", "")
    tables = [t for t in result.get("tables") or [] if t.get("subcategory") not in ("KV", "TOC") and t.get("rows")]
    trimmed = [_trim_table(t, B) for t in tables]
    rows_before = result.get("rows") or []
    rows_after = R.table_rows(M, name, trimmed)
    checks_before = result.get("checks") or []
    checks_after, conflicts_after = R.check_rows(M, rows_after)
    loss = []
    for t in tables:
        for cell in [*(t.get("columns") or []), *(x for r in t.get("rows") or [] for x in r)]:
            tt = trim(cell, B)
            if tt["loss"]:
                loss.append({"anchor": t.get("anchor"), "raw": tt["raw"], "clean": tt["clean"], "loss": tt["loss"]})
    pages = {}
    for r in rows_after:
        p = pages.setdefault(r.get("page"), {"page": r.get("page"), "fy": 0, "mapped": set(), "blocks": Counter(), "anchors": set()})
        if r.get("period") and len(str(r["period"])) == 4:
            p["fy"] += 1
        if r.get("metric"):
            p["mapped"].add(r["metric"])
            p["blocks"][r.get("block") or "?"] += 1
        p["anchors"].add(r.get("anchor"))
    words = an["statement_words"]
    page_text = {}
    for s in result.get("sentences") or []:
        page_text.setdefault(s.get("page"), []).append(s.get("text") or "")
    for t in tables:
        page_text.setdefault(R._page_of(t.get("anchor")), []).append(" ".join([t.get("title") or ""] + [str(c) for c in t.get("columns") or []]))
    annual_pages = []
    for pno, p in sorted(pages.items(), key=lambda kv: kv[0] or 0):
        if p["fy"] < an["min_fy_cells"] or len(p["mapped"]) < an["min_mapped"]:
            continue
        txt = trim(" ".join(page_text.get(pno, [])), B)["fold"]
        named = [k for k, ws in words.items() if any(w.casefold() in txt for w in ws)]
        annual_pages.append({"page": pno, "fy_cells": p["fy"], "mapped": len(p["mapped"]),
                             "statements": sorted({b for b in p["blocks"] if b in ("IS", "BS", "CF", "RATIO", "PERSHARE", "VALUATION")}),
                             "named": named, "tables": len(p["anchors"])})
    annual_set = {p["page"] for p in annual_pages}
    before = {}
    for r in rows_before:
        before.setdefault(_cell_key(r, B), []).append(r)
    verified, flagged = {}, {}
    for c in checks_after:
        for metric in (c.get("used") or {}):
            slot = f"{metric}@{c.get('period')}"
            if c.get("state") == "PASS":
                verified.setdefault(slot, []).append(c["id"])
            elif c.get("state") in ("FAIL", "WARN", "UNIT_SCALE"):
                flagged.setdefault(slot, []).append(f"{c['id']} {c['state']}")
    cells = []
    for r in rows_after:
        if r.get("page") not in annual_set:
            continue
        b = (before.get(_cell_key(r, B)) or [None])[0]
        effect = "SAME"
        if b is None:
            effect = "TRIM_GAIN"
        elif (b.get("metric") or "") != (r.get("metric") or "") and b.get("metric") and r.get("metric"):
            effect = "TRIM_CONFLICT"
        elif not b.get("metric") and r.get("metric"):
            effect = "TRIM_GAIN"
        elif b.get("value") is not None and r.get("value") is not None and abs(float(b["value"]) - float(r["value"])) > 1e-9:
            effect = "TRIM_CONFLICT"
        slot = f"{r.get('metric')}@{r.get('period')}"
        label_raw = (b or {}).get("metric_raw", r.get("metric_raw"))
        db_vals = db_idx.get((fold_key(label_raw, B), fold_key(r.get("period_raw"), B))) or []
        db_state, db_value = "", None
        if db_vals and r.get("value") is not None:
            tol = max(0.5 * 10 ** -_decimals(r.get("printed")), 1e-9)
            near = [v for v in db_vals if abs(v - float(r["value"])) <= tol]
            db_state, db_value = ("AGREE", near[0]) if near else ("DISAGREE", db_vals[0])
        if not r.get("metric"):
            state = "UNMAPPED"
        elif effect == "TRIM_CONFLICT" or db_state == "DISAGREE":
            state = "CONFLICT"
        elif slot in flagged and slot not in verified:
            state = "REPORT_CHECK"
        elif slot in verified or db_state == "AGREE":
            state = "VERIFIED"
        else:
            state = "SINGLE"
        cells.append({"page": r.get("page"), "anchor": r.get("anchor"), "label_raw": (b or {}).get("metric_raw", r.get("metric_raw")),
                      "label_clean": r.get("metric_raw"), "metric_before": (b or {}).get("metric", ""), "metric": r.get("metric") or "",
                      "block": r.get("block") or "", "period_raw": r.get("period_raw"), "period": r.get("period"), "kind": r.get("kind", ""),
                      "printed_raw": (b or {}).get("printed", ""), "printed_clean": r.get("printed"),
                      "value_before": (b or {}).get("value"), "value": r.get("value"), "unit": r.get("unit", ""), "effect": effect,
                      "db_value": db_value, "db_state": db_state, "state": state,
                      "verified_by": verified.get(slot, []) + (["資料庫引擎同值"] if db_state == "AGREE" else []),
                      "flagged_by": flagged.get(slot, []) + ([f"資料庫引擎讀成 {db_value:g}"] if db_state == "DISAGREE" else [])})
    specials = []
    for t, t2 in zip(tables, trimmed):
        pno = R._page_of(t.get("anchor"))
        if pno not in annual_set:
            continue
        for ri, row in enumerate(t2.get("rows") or []):
            for ci, cell in enumerate(row[1:], 1):
                c = cell.strip()
                kind = B.null_tokens.get(c.casefold()) if c else None
                if c.startswith(B.triangle):
                    kind = "TRIANGLE"
                if kind and kind != "BLANK":
                    cols = t2.get("columns") or []
                    specials.append({"page": pno, "anchor": t.get("anchor"), "row": ri, "col": ci, "label": row[0] if row else "",
                                     "column": cols[ci] if ci < len(cols) else "", "raw": (t.get("rows") or [[]])[ri][ci], "kind": kind,
                                     "state": "REVIEW" if kind == "TRIANGLE" else "NULL_PRINTED"})
    delta = []
    bstate = {(c.get("id"), c.get("period")): c.get("state") for c in checks_before}
    for c in checks_after:
        k = (c.get("id"), c.get("period"))
        old = bstate.get(k)
        if old == "PASS" and c.get("state") != "PASS":
            delta.append({"id": k[0], "period": k[1], "before": old, "after": c.get("state"), "effect": "TRIM_REGRESSION"})
        elif old != "PASS" and c.get("state") == "PASS":
            delta.append({"id": k[0], "period": k[1], "before": old or "（TRIM 前沒有這條）", "after": "PASS", "effect": "TRIM_FIX"})
    for k, old in bstate.items():
        if old == "PASS" and not any((c.get("id"), c.get("period")) == k for c in checks_after):
            delta.append({"id": k[0], "period": k[1], "before": "PASS", "after": "（TRIM 後不見了）", "effect": "TRIM_REGRESSION"})
    return {"pages": annual_pages, "cells": cells, "specials": specials, "loss": loss, "delta": delta,
            "checks_before": dict(Counter(c.get("state") for c in checks_before)),
            "checks_after": dict(Counter(c.get("state") for c in checks_after)), "conflicts_after": conflicts_after,
            "rows_before": len(rows_before), "rows_after": len(rows_after)}


# =====================================================================
# 6 . VERIFY: two independent readers that agree = VERIFIED
# =====================================================================
# [VRN-ID] VRN-ENG014-FNC039 · LOGIC
def _same_text(a, b, B):
    ka, kb = fold_key(a, B), fold_key(b, B)
    return bool(ka) and ka == kb


_COMPANY_SUFFIX_RX = re.compile(r"(?:股份有限公司|有限公司|股份公司|公司|corporation|corp|incorporated|inc|limited|ltd|holdings|holding|company|co)$")


# [VRN-ID] VRN-ENG014-FNC077 · LOGIC
def _company_key(s, B):
    """A company name as it compares: letters / digits / CJK only, the -KY listing marker and company-form words dropped."""
    k = _bare(s, B)
    k = re.sub(r"[\-*＊]*ky$", "", k)
    for _ in range(3):
        k2 = _COMPANY_SUFFIX_RX.sub("", k)
        if k2 == k or len(k2) < 2:
            break
        k = k2
    return k


# [VRN-ID] VRN-ENG014-FNC078 · LOGIC
def _company_same(a, b, B):
    """Round 5 (2026-10-12): 慧洋 = 慧洋-KY, 頎邦 = 頎邦科技股份有限公司 (the local DB's official name), Wiwynn = Wiwynn Corp:
    equal keys, or one is the other's start / inside it (CJK from 2 characters, Latin from 4)."""
    ka, kb = _company_key(a, B), _company_key(b, B)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    need = 2 if _script(ka) == "cjk" else 4
    return min(len(ka), len(kb)) >= need and (ka in kb or kb in ka)


# [VRN-ID] VRN-ENG014-FNC082 · LOGIC
def _year_like(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    return f.is_integer() and 1990 <= f <= time.localtime().tm_year + 2


# [VRN-ID] VRN-ENG014-FNC083 · LOGIC
def _days_after(a, b):
    """Days from ISO date b to ISO date a (a later -> positive); None when either is not a date."""
    try:
        ta, tb = time.strptime(str(a), "%Y-%m-%d"), time.strptime(str(b), "%Y-%m-%d")
    except (TypeError, ValueError):
        return None
    return int(round((time.mktime(ta) - time.mktime(tb)) / 86400.0))


# [VRN-ID] VRN-ENG014-FNC084 · LOGIC
def _is_short_report(text, B):
    """Note / Memo / Takeaway / 訪談 … in the file name or the title (the TitleTrim book's focus.short_report_words)."""
    low = str(text or "").casefold()
    for w in B.short_words:
        wl = w.casefold()
        if re.search(r"[一-鿿]", wl):
            if wl in low:
                return True
        elif re.search(r"(?<![a-z])" + re.escape(wl) + r"(?![a-z])", low):
            return True
    return False


# [VRN-ID] VRN-ENG014-FNC040 · LOGIC
def _script(s):
    return "cjk" if re.search(r"[一-鿿]", s or "") else ("latin" if re.search(r"[A-Za-z]", s or "") else "")


# [VRN-ID] VRN-ENG014-FNC066 · LOGIC
def _bare(text, B=None):
    """Letters, digits and CJK only: separators and punctuation do not make two readings different."""
    return re.sub(r"[^0-9a-z一-鿿]", "", trim(text, B)["fold"]) if text not in (None, "") else ""


# [VRN-ID] VRN-ENG014-FNC041 · LOGIC
def _vote(part, sources, same, expected=False, note=""):
    """sources: [(group, name, value)] -> one part.  VERIFIED: >= 2 groups agree and no voter disagrees."""
    voters = [(g, n, v) for g, n, v in sources if v not in (None, "", [])]
    if not voters:
        return {"part": part, "value": "", "state": "MISSING" if expected else "NOT_PRINTED", "sources": {}, "why": note}
    clusters = []
    for g, n, v in voters:
        for cl in clusters:
            if same(cl["value"], v):
                cl["groups"].add(g)
                cl["names"].append(n)
                break
        else:
            clusters.append({"value": v, "groups": {g}, "names": [n]})
    clusters.sort(key=lambda c: (-len(c["groups"]), "arith" not in c["groups"], -len(c["names"])))   # a tie goes to arithmetic
    top = clusters[0]
    shown = {n: v for _g, n, v in voters}
    # 2026-10-19 操作員「兩個以上相同即算對照成功」：那條規則本來就是這裡的 `>= 2`，
    # 但它只活在 why 那句中文裡 —— 下游要驗只能去解析散文。改成一併記下**支持採用值的群組數**，
    # 閘讀數字不猜文字（而且沒走這支的部位會因為沒有這個鍵而現形,那正是要看見的）。
    agree = len(top["groups"])
    if len(clusters) > 1:
        return {"part": part, "value": top["value"], "state": "CONFLICT", "sources": shown, "agree": agree,
                "why": "讀法不一致：" + " vs ".join(f"{'+'.join(c['names'])}={c['value']}" for c in clusters[:3]) + (f" · {note}" if note else "")}
    if agree >= 2:
        return {"part": part, "value": top["value"], "state": "VERIFIED", "sources": shown, "agree": agree,
                "why": "+".join(top["names"]) + " 一致"}
    return {"part": part, "value": top["value"], "state": "SINGLE", "sources": shown, "agree": agree,
            "why": f"只有 {top['names'][0]} 讀到，沒有第二來源" + (f" · {note}" if note else "")}


# [VRN-ID] VRN-ENG014-FNC068 · LOGIC
def _arith_pair(tp_votes, cp_votes, upside, tol):
    """Real run 2026-10-12 (round 2): target, current price and upside all printed -> every (target, current) pair the readers
    gave is tried against the printed upside.  Only one target and one current price that add up (within tol) get a vote each;
    a pair that adds up to nothing anyone read gives no vote.  -> (target or None, current or None)."""
    try:
        u = float(upside) / 100.0 if upside not in (None, "") else None
    except (TypeError, ValueError):
        u = None
    if u is None or u <= -1:
        return None, None
    tps = sorted({float(v) for _g, _n, v in tp_votes if v not in (None, "") and _is_num(v) and float(v) > 0})
    cps = sorted({float(v) for _g, _n, v in cp_votes if v not in (None, "") and _is_num(v) and float(v) > 0})
    pairs = [(t, c) for t in tps for c in cps if abs(t - c * (1 + u)) <= tol * c * (1 + u)]
    tp_hit = {t for t, _c in pairs}
    cp_hit = {c for _t, c in pairs}
    return (next(iter(tp_hit)) if len(tp_hit) == 1 else None), (next(iter(cp_hit)) if len(cp_hit) == 1 else None)


# [VRN-ID] VRN-ENG014-FNC075 · LOGIC
def _title_junk(eng_title, trim_title, ticker, B, company=""):
    """Round 4 (2026-10-12): the engine's largest-font line was 'I' and a header '國泰證券子公司 2023/10/05'.  Fewer than
    min_chars, or a date with the title's ticker missing: it is not a title and does not vote (shown)."""
    if not eng_title:
        return False
    bare = _bare(eng_title, B)
    if len(bare) < B.title_junk_min:
        return True
    tk = str(ticker or "")
    if tk and tk in _bare(trim_title, B) and tk not in bare and B.date_like_rx.search(eng_title):
        return True
    ck = _company_key(company, B) if company else ""
    return bool(tk and tk in _bare(trim_title, B) and tk not in bare and ck and ck not in bare)   # round 6: '個股報告' / '投資 顧問' banners


# [VRN-ID] VRN-ENG014-FNC072 · LOGIC
def _is_nr(value, B):
    low = str(value or "").strip().casefold()
    return bool(low) and (low in B.nr_words or any(w in low for w in ("未評等", "無評等", "not rated", "unrated", "nr_")))


# [VRN-ID] VRN-ENG014-FNC073 · LOGIC
def _contact_vote(part, fields, name, eng_value, norm):
    """Real run 2026-10-12 (round 3): a report with two analysts prints two e-mails; the engine reads one of them.  The page
    voter carries every contact it found (first by zone, the analyst box first); the engine agrees when its value is any of
    them, and the part's value is the one both have."""
    page = fields.get(name) or {}
    allv = [norm(x) for x in (page.get("all") or [])]
    first = norm(page.get("value"))

    # [VRN-ID] VRN-ENG014-FNC074 · LOGIC
    def same(a, b):
        na, nb = norm(a), norm(b)
        if not na or not nb:
            return False
        return na == nb or (na == first and nb in allv) or (nb == first and na in allv)   # the other reader's value is one of the page's
    p = _vote(part, [("page", "首頁（TRIM）", page.get("value")), ("engine", "首頁引擎", eng_value)], same)
    if p["state"] == "VERIFIED" and eng_value not in (None, "") and norm(eng_value) != norm(page.get("value")):
        p["value"] = eng_value
    if len(page.get("all") or []) > 1:
        p.setdefault("sources", {})["首頁全部"] = "；".join(map(str, page["all"]))[:200]
    return p


# [VRN-ID] VRN-ENG014-FNC069 · LOGIC
def _not_prior(value, prior_values, same):
    """Real run 2026-10-12 (round 2): ENG396 read 345 from the 兆豐 line under '前次投資建議' (the previous target).  A reading
    equal to a target printed on a 前次 line is set aside: shown, not counted.  -> (value or None, note)."""
    if value in (None, "") or not prior_values:
        return value, {}
    if any(same(value, pv) for pv in prior_values):
        return None, {"ENG396 全文（讀到前次那一行，不計）": value}
    return value, {}


# [VRN-ID] VRN-ENG014-FNC070 · LOGIC
def _is_num(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


# [VRN-ID] VRN-ENG014-FNC042 · LOGIC
def _title_only(seg, key, part):
    """An optional title segment the title does not print is NOT_PRINTED -- another reader's value is noted, never borrowed."""
    if (seg.get(key) or {}).get("state") == "NOT_PRINTED":
        others = "; ".join(f"{k}={v}" for k, v in (part.get("sources") or {}).items() if k != "標題")
        # 2026-10-20：重建 dict 的時候原本把 `_vote` 算好的 `agree` 丟掉了。標題沒印、值沒有採用，
        # 但「各來源讀到什麼」既然留著，「幾組讀成同一個」就要一起留著 —— 不然跨來源對照看不到它。
        return {"part": part["part"], "value": "", "state": "NOT_PRINTED", "sources": part.get("sources") or {},
                "agree": part.get("agree"),
                "why": "標題沒印" + (f"（別處讀到：{others}）" if others else "")}
    return part


# [VRN-ID] VRN-ENG014-FNC043 · LOGIC
def verify(title, cover, ctx, B=None, brd=None):
    """-> parts (title.* and cover.*) with state, value, sources, why."""
    B = B or books()
    fn, eng, basic, ent = (ctx.get(k) or {} for k in ("filename", "engine", "basic", "entities"))
    seg = (title or {}).get("segments") or {}
    f = (cover or {}).get("fields") or {}
    tol_tp = float(B.verify["tp_tol_rel"])
    tol_p = float(B.verify["price_tol_rel"])

    # [VRN-ID] VRN-ENG014-FNC044 · LOGIC
    def num_same(tol):
        # [VRN-ID] VRN-ENG014-FNC045 · LOGIC
        def same(a, b):
            try:
                a, b = float(a), float(b)
            except (TypeError, ValueError):
                return False
            return abs(a - b) <= tol * max(abs(a), abs(b), 1e-9)
        return same

    # [VRN-ID] VRN-ENG014-FNC046 · LOGIC
    def text_same(a, b):
        return _same_text(a, b, B)

    # [VRN-ID] VRN-ENG014-FNC047 · LOGIC
    def rating_same(a, b):
        if _same_text(a, b, B):
            return True
        if brd is None:
            return False
        ra, rb = brd.rating_normalize(a, True), brd.rating_normalize(b, True)
        return bool(ra) and ra == rb

    # [VRN-ID] VRN-ENG014-FNC048 · LOGIC
    def contains(a, b):
        ka, kb = _bare(a, B), _bare(b, B)
        return bool(ka and kb) and (ka in kb or kb in ka)
    parts = []
    tseg = lambda k: (seg.get(k) or {}).get("value") or ""   # noqa: E731
    code_sources = [("title", "標題", tseg("ticker")), ("filename", "檔名", fn.get("ticker")), ("engine", "首頁引擎", eng.get("ticker"))]
    p = _vote("title.ticker", code_sources, lambda a, b: str(a) == str(b), expected=True)
    if (seg.get("ticker") or {}).get("state") == "REVIEW" and p["state"] != "VERIFIED":
        p.update(state="REVIEW", why=((seg["ticker"].get("why") or B.book["ticker"]["year_band_rule"]) + " · " + p["why"]).strip(" ·"))
    parts.append(p)
    company = tseg("company")
    names = [("filename", "檔名", n) for n in fn.get("company_names") or []]
    names += [("engine", "首頁引擎", eng.get("company")), ("localdb", "本機資料庫", basic.get("NameDB") or basic.get("Name"))]
    present = [s for s in names if s[2]]
    ref = company or (present[0][2] if present else "")       # round 5: with no title company the engine's script leads
    ref_script = _script(ref)
    comparable = [s for s in present if not ref_script or _script(s[2]) == ref_script]
    aside = [s for s in present if s not in comparable]
    p = _vote("title.company", [("title", "標題", company)] + comparable, lambda a, b: _company_same(a, b, B), expected=True,
              note="不同文字（中文／英文）的名稱不互比" if aside else "")
    for _g, n, v in aside:
        p.setdefault("sources", {})[f"{n}（不同文字，不比）"] = v
    db_name = _db_name(ctx, parts[0].get("value"))
    if db_name:                                           # 2026-10-13 operator: 公司名稱一律至 DATABASE 去取
        readings = [r for r in [("title", "標題", company)] + [s for s in names if s[0] != "localdb"] if r[2]]
        p = _db_company_part(db_name, readings, B)
    parts.append(p)
    market_sources = [("title", "標題", tseg("market")), ("page", "首頁 Yahoo 代碼（TRIM）", (f.get("market") or {}).get("value")),
                      ("engine", "首頁引擎", eng.get("market")), ("localdb", "代碼主檔", basic.get("Market"))]
    p = _vote("title.market", market_sources, text_same)
    if p["state"] == "NOT_PRINTED" and (seg.get("market") or {}).get("state") == "UNKNOWN_NO_GENERATE":
        p.update(state="NOT_PRINTED", why=B.book["ticker"]["market_rule"])
    parts.append(p)
    rt = seg.get("report_type") or {}
    fn_types = _report_types(trim(fn.get("stem") or "", B)["clean"], B)
    p = _vote("title.report_type", [("title", "標題", rt.get("value")), ("filename", "檔名", fn_types[0]["code"] if len(fn_types) == 1 else "")],
              text_same)
    p = _title_only(seg, "report_type", p)
    if rt.get("state") == "REVIEW":
        p.update(state="REVIEW", value="", why=rt.get("why", "") + "：" + ", ".join(f"{c['code']}({c['word']})" for c in rt.get("candidates", [])))
    parts.append(p)
    fv = lambda k: (f.get(k) or {}).get("value")   # noqa: E731
    not_rated = _is_nr(tseg("rating_action"), B) or any(_is_nr(v, B) for v in (fn.get("rating"), eng.get("rating"), fv("rating")))
    act_votes = [("title", "標題", tseg("rating_action")), ("engine", "首頁引擎", eng.get("rating_action")),
                 ("filename", "檔名", "NOT_RATED" if _is_nr(fn.get("rating"), B) else "")]
    act_note = {}
    if not_rated and eng.get("rating_action") == "MAINTAIN":        # round 3: MAINTAIN is the default of a 維持 word; NR is explicit
        act_votes[1] = ("engine", "首頁引擎", "")
        act_note = {"首頁引擎（MAINTAIN 是維持字的預設，報告未評等，不計）": "MAINTAIN"}
    p = _title_only(seg, "rating_action", _vote("title.rating_action", act_votes, text_same))
    if act_note:
        p.setdefault("sources", {}).update(act_note)
    parts.append(p)
    tpc = seg.get("tp_change") or {}
    ent_tp, ent_note = _not_prior((ent.get("target_price") or {}).get("current"), (cover or {}).get("prior_target_prices") or [], num_same(tol_tp))
    if _year_like(ent_tp):                                 # round 6: ENG396 read 2026 as UBS 6409's target price
        ent_note = dict(ent_note or {}, **{"ENG396 全文（像年份，不計）": ent_tp})
        ent_tp = None
    tp_votes = [("title", "標題", tpc.get("current")), ("entities", "ENG396 全文", ent_tp)]
    p = _title_only(seg, "tp_change", _vote("title.tp_change", tp_votes, num_same(tol_tp)))
    if ent_note:
        p.setdefault("sources", {}).update(ent_note)
    if p["value"] not in ("", None):
        p["value"] = tpc.get("value") or p["value"]
    parts.append(p)
    eng_title = eng.get("title") or ""
    junk = _title_junk(eng_title, (title or {}).get("text") or "", fn.get("ticker"), B, company)
    meta = (title or {}).get("source") == "META"          # round 6: the PDF's metadata Title is not printed on the page
    # 2026-10-20 (JPM): the engine's largest-font reading is one line ('TSMC Overweight', two columns of one row); the TRIM title can
    # be several joined lines ('TSMC - Margin test passed; …').  They agree when the engine's line and one of the title's lines agree.
    # [VRN-ID] VRN-ENG014-FNC105 · LOGIC
    def line_same(a, b):
        return contains(a, b) or any(contains(x, b) for x in str(a or "").split(" - ")) or any(contains(a, y) for y in str(b or "").split(" - "))
    p = _vote("title.text", [("title", "標題（TRIM）", "" if meta else (title or {}).get("text")),
                             ("engine", "首頁引擎最大字", "" if junk else eng_title)], line_same)
    p["value"] = (title or {}).get("text") or p["value"]
    if junk:
        p.setdefault("sources", {})["首頁引擎最大字（像頁首、版頭或太短，不計）"] = eng_title
    if meta:
        p.setdefault("sources", {})["標題（PDF 屬性 Title，不是首頁印的，不比）"] = (title or {}).get("text")
    parts.append(p)
    core = tseg("core_view")
    only_company = bool(core) and not tseg("ticker") and any(_company_same(core, k, B) for k in [company] + [n[2] for n in names] if k)
    if only_company:
        core = ""                                         # 2026-10-20 (CLSA 'Wiwynn', JPM 'TSMC'): the title line is the company name alone
    if core:
        state = "VERIFIED" if p["state"] == "VERIFIED" else "SINGLE"
        parts.append({"part": "title.core_view", "value": core, "state": state, "sources": {"標題": core},
                      "why": "標題兩條讀法一致，核心觀點從同一行拆出" if state == "VERIFIED" else "標題只有一條讀法"})
    else:
        parts.append({"part": "title.core_view", "value": "", "state": "NOT_PRINTED", "sources": {},
                      "why": "標題只印了公司名，沒有核心觀點" if only_company else ""})
    expected = set(B.book["cover"]["expected_on_stock"])
    short = _is_short_report(" ".join(str(x or "") for x in (fn.get("stem"), (title or {}).get("text"))), B)
    if short:
        expected.discard("rating")
        expected.discard("target_price")
    if not_rated:
        expected.discard("target_price")
    tp_na = ((cover or {}).get("declared_na") or {}).get("target_price")
    if tp_na:
        expected.discard("target_price")
    # 第四條同形的例外：三條讀法都沒讀到券商，而首頁上連「券商名該有的字」都沒有一個
    # —— 這份報告沒印發行機構，記 NOT_PRINTED 不是 MISSING（operator 2026-10-20）。
    if "broker" in expected and not any((fv("broker"), fn.get("broker"), eng.get("broker"))) \
            and not _broker_slot_has_text(title, cover, ctx, B):
        expected.discard("broker")
    parts.append(_vote("cover.broker", [("page", "首頁（TRIM）", fv("broker")), ("filename", "檔名", fn.get("broker")),
                                        ("engine", "首頁引擎", eng.get("broker"))], text_same, expected="broker" in expected))
    fn_date, fn_note = fn.get("date"), {}
    late = _days_after(fn_date, fv("date")) if fv("date") and fv("date") == eng.get("date") else None
    if late is not None and 0 < late <= B.fn_date_send_days:   # round 6: the file is named on the send date, the page prints the report date
        fn_note = {f"檔名（晚 {late} 天，常是發送日，不比）": fn_date}
        fn_date = ""
    parts.append(_vote("cover.date", [("page", "首頁（TRIM）", fv("date")), ("filename", "檔名", fn_date),
                                      ("engine", "首頁引擎", eng.get("date"))], text_same, expected="date" in expected))
    if fn_note:
        parts[-1].setdefault("sources", {}).update(fn_note)
    parts.append(_vote("cover.rating", [("page", "首頁（TRIM）", fv("rating")), ("engine", "首頁引擎", eng.get("rating")),
                                        ("filename", "檔名", fn.get("rating"))], rating_same, expected="rating" in expected,
                       note="評等照原文；比對時才用詞表對同級（輸出不帶等級）"))
    tp_votes = [("page", "首頁（TRIM）", fv("target_price")), ("engine", "首頁引擎", eng.get("target_price")),
                ("entities", "ENG396 全文", ent_tp)]
    cp_votes = [("page", "首頁（TRIM）", fv("current_price")), ("engine", "首頁引擎", eng.get("current_price"))]
    tp_arith, cp_arith = _arith_pair(tp_votes, cp_votes, fv("upside"), float(B.verify.get("upside_implied_tol_rel", 0.01)))
    if tp_arith is not None:
        tp_votes.append(("arith", "現價×(1+上漲空間) 反推", tp_arith))
    if cp_arith is not None:
        cp_votes.append(("arith", "目標價÷(1+上漲空間) 反推", cp_arith))
    parts.append(_vote("cover.target_price", tp_votes, num_same(tol_tp), expected="target_price" in expected))
    if ent_note:
        parts[-1].setdefault("sources", {}).update(ent_note)
    if not_rated and parts[-1]["state"] == "NOT_PRINTED":
        parts[-1]["why"] = "未評等（NR）報告：沒有目標價是正常"
    elif short and parts[-1]["state"] == "NOT_PRINTED":
        parts[-1]["why"] = "短評（Note／Memo／Takeaway／訪談）不一定印目標價"
    elif tp_na and parts[-1]["state"] == "NOT_PRINTED":
        parts[-1]["why"] = f"報告寫明沒有目標價（第 {tp_na['line']} 行「{tp_na['text']}」）"
    date_part = next((x for x in parts if x["part"] == "cover.date"), {})
    quote = _db_closes(ctx, parts[0].get("value"), date_part.get("value") or fn.get("date"))
    if quote.get("basis") or quote.get("same"):           # 2026-10-13 operator: 價格一律至 DATABASE 去取
        parts.append(_db_price_part(quote, cp_votes, num_same(tol_p)))
    else:
        parts.append(_vote("cover.current_price", cp_votes, num_same(tol_p)))
    tp = next((x for x in parts if x["part"] == "cover.target_price"), {})
    cp = next((x for x in parts if x["part"] == "cover.current_price"), {})
    up_printed = fv("upside")
    calc = None
    try:
        # 重算用原始收盤價，不用 adj：報告印的上漲% 是拿它自己印的原始價算的。
        # 現價的值已經改成 adj close 為基準（操作員 2026-10-16），拿 adj 去比印出來的百分比，
        # 只要那檔除過權息就會差一截 —— 和現價的狀態同一個紀律：比對要拿同一種量比。
        base = cp.get("close") if cp.get("close") not in ("", None) else cp.get("value")
        if tp.get("value") not in ("", None) and base not in ("", None) and float(base):
            calc = (float(tp["value"]) - float(base)) / float(base) * 100.0
    except (TypeError, ValueError):
        calc = None
    if up_printed is None and calc is not None:
        # 2026-10-21 第二十三輪：算出來了，卻記成「報告沒印」—— 數字只活在 why 那句中文裡，欄位是空的。
        # 第十七輪已經在代號紀錄那一欄修過同一格（put_code 早就有 DERIVED），**部位這一層沒跟上**，
        # 所以操作員每一輪在終端看到的部位矩陣印「上漲% –59」＝報告沒印。
        # 三條自我約束照第十七輪：不發明新狀態（DERIVED 這一格早就在）、不另算一次（交出去的就是 calc）、
        # 印了的優先（下面兩支一個字都不改）。四捨五入到小數兩位 —— 代號紀錄與 basic_info.UpsideDownsidePct
        # 本來就是兩位，同一個事實在幾張表上要印同一個數字。
        parts.append({"part": "cover.upside", "value": round(calc, 2), "state": "DERIVED",
                      "sources": {"VRN 重算": round(calc, 2)}, "why": UPSIDE_DERIVED_WHY + "（def03）"})
    elif up_printed is None:
        parts.append({"part": "cover.upside", "value": "", "state": "NOT_PRINTED", "sources": {}, "why": ""})
    elif calc is None:
        parts.append({"part": "cover.upside", "value": up_printed, "state": "SINGLE", "sources": {"首頁（TRIM）": up_printed},
                      "why": "目標價或現價缺，不能重算"})
    else:
        ok = abs(float(up_printed) - calc) <= float(B.verify["upside_tol_pp"])
        both = tp.get("state") == "VERIFIED" and cp.get("state") == "VERIFIED"
        parts.append({"part": "cover.upside", "value": up_printed, "state": ("VERIFIED" if both else "SINGLE") if ok else "CONFLICT",
                      "sources": {"首頁（TRIM）": up_printed, "VRN 重算": round(calc, 4)},
                      "why": (f"印 {up_printed}% vs 重算 {calc:.2f}%：" + ("合理四捨五入" if ok else "標記差異（def03）"))
                      + ("" if both or not ok else "（目標價或現價還沒驗證，不鎖）")})
    parts.append(_contact_vote("cover.analyst", f, "analyst", eng.get("analyst"), lambda v: fold_key(v, B)))
    parts.append(_contact_vote("cover.email", f, "email", eng.get("email"), lambda v: str(v or "").strip().casefold()))
    parts.append(_contact_vote("cover.tel", f, "tel", eng.get("tel"), lambda v: re.sub(r"\D", "", str(v or ""))[-8:]))
    zones = (cover or {}).get("zones") or []
    for p in parts:                                   # real run 2026-10-12: every page reading carries the line it came from
        name = p["part"].split(".", 1)[1] if p["part"].startswith("cover.") else ""
        line = (f.get(name) or {}).get("line")
        if line and 0 < line <= len(zones) and p["state"] not in ("VERIFIED", "NOT_PRINTED"):
            p.setdefault("sources", {})["首頁那一行"] = f"L{line} {zones[line - 1]['clean'][:110]}"
            p["sources"]["區塊"] = zones[line - 1]["zone"]
            if line > 1:
                p["sources"]["首頁上一行"] = f"L{line - 1} {zones[line - 2]['clean'][:110]}"
    return parts


# [VRN-ID] VRN-ENG014-FNC049 · LOGIC
def annual_parts(an):
    """annual.<metric>@<period>: VERIFIED when a passing identity used it; one value per slot (two different = CONFLICT)."""
    by = {}
    for c in an.get("cells") or []:
        if not c.get("metric"):
            continue
        by.setdefault(f"annual.{c['metric']}@{c['period']}", []).append(c)
    parts = []
    for part, cs in sorted(by.items()):
        values = sorted({round(float(c["value"]), 9) for c in cs if c.get("value") is not None})
        states = {c["state"] for c in cs}
        if len(values) > 1:
            state, why = "CONFLICT", "同一科目同一期有不同數字：" + " / ".join(f"p{c['page']} {c['printed_clean']}" for c in cs[:4])
        elif "CONFLICT" in states:
            state, why = "CONFLICT", "讀法不一致：" + "; ".join(sorted({x for c in cs for x in c["flagged_by"]} | (
                {"TRIM 前後讀到的科目或數字不同"} if any(c["effect"] == "TRIM_CONFLICT" for c in cs) else set())))
        elif "VERIFIED" in states:
            state, why = "VERIFIED", "驗算 PASS：" + ", ".join(sorted({x for c in cs for x in c["verified_by"]}))
        elif "REPORT_CHECK" in states:
            state, why = "REPORT_CHECK", "驗算不過：" + ", ".join(sorted({x for c in cs for x in c["flagged_by"]}))
        else:
            state, why = "SINGLE", "沒有任何驗算式用到它（表上沒印對應的數字）"
        c0 = cs[0]
        # 2026-10-20：`agree`（支持採用值的來源群組數）以前只有 `_vote` 那條路會寫，這一條沒有。
        # 實測 612 個部位 state=VERIFIED、三個來源同值，agree 卻是空的 —— 操作員 2026-10-19 要的跨來源
        # 對照（「相互對照兩個以上相同即算對照成功」）讀的就是這個數字，讀不到就把它們全歸進「別條路徑」：
        # 對上印 699，實際上 1311。這裡**不另立第二把尺重判數字**：「資料庫引擎讀到的算不算同值」
        # 上面那一圈 cell 已經判過（db_state），這裡只把判過的結果數起來。
        # 表格（TRIM）與原印是同一個讀法的前後兩面，算一組；資料庫引擎是第二組。
        groups = (int(bool(c0.get("printed_clean") or c0.get("printed_raw")))
                  + int(any(c.get("db_state") == "AGREE" for c in cs)))
        parts.append({"part": part, "value": values[0] if values else "", "state": state, "agree": groups,
                      "sources": {"表格（TRIM）": c0.get("printed_clean"), "原印": c0.get("printed_raw") or c0.get("printed_clean"),
                                  "資料庫引擎": c0.get("db_value")},
                      "why": why, "page": c0.get("page"), "effect": ",".join(sorted({c["effect"] for c in cs}))})
    for c in an.get("cells") or []:
        if not c.get("metric"):
            parts.append({"part": f"annual.unmapped:{c['label_clean']}@{c['period']}", "value": c.get("value"), "state": "UNMAPPED",
                          "sources": {"列標": c.get("label_raw")}, "why": "列標對不到科目（def05 unmappable_rule：REVIEW_REQUIRED，不猜）",
                          "page": c.get("page"), "effect": c.get("effect")})
    for s in an.get("specials") or []:
        if s["kind"] == "TRIANGLE":
            parts.append({"part": f"annual.triangle:{s['label']}@{s['column']}", "value": s["raw"], "state": "REVIEW",
                          "sources": {"原印": s["raw"]}, "why": books().book["annual"]["triangle_rule"], "page": s["page"], "effect": ""})
    for x in an.get("loss") or []:
        parts.append({"part": f"annual.trim_loss:{x['raw']}", "value": x["clean"], "state": "TRIM_LOSS", "sources": {"原印": x["raw"]},
                      "why": "TRIM 少了：" + "、".join(x["loss"]), "page": None, "effect": ""})
    for d in an.get("delta") or []:
        if d["effect"] == "TRIM_REGRESSION":
            parts.append({"part": f"annual.check:{d['id']}@{d['period']}", "value": d["after"], "state": "TRIM_REGRESSION",
                          "sources": {"TRIM 前": d["before"], "TRIM 後": d["after"]}, "why": "TRIM 後驗算反而變差", "page": None, "effect": ""})
    return parts


# =====================================================================
# 7 . ONE FILE / MANY FILES
# =====================================================================
# [VRN-ID] VRN-ENG014-FNC067 · REPORT
def report_context(name, fpe=None, basic=None, regions_result=None, brd_engine=None):
    """The other readers' answers for the same file, as plain values (nothing of theirs is changed)."""
    fpe = fpe or {}
    basic = basic or {}
    dec = (regions_result or {}).get("decomposition") or {}
    ffields = fpe.get("filename_fields") or {}
    if not ffields and brd_engine is not None:
        try:
            ff = brd_engine._filename_fields(name)
            ffields = {k: ff.get(k) for k in ("ticker", "broker", "date", "rating")}
        except Exception:  # noqa: BLE001
            ffields = {}
    rating = fpe.get("rating") or {}
    tps = fpe.get("target_prices") or {}
    emails = fpe.get("emails") or []
    tel = fpe.get("tel") or []
    analysts = fpe.get("analysts") or []
    company_page = fpe.get("company_name_page")
    if isinstance(company_page, dict):
        company_page = company_page.get("value") or company_page.get("name") or ""
    tri = fpe.get("tri_code") or {}
    page_codes = fpe.get("page_codes") or []
    yf = next((c for c in page_codes if c.get("platform") == "yfinance"), None)
    ticker_page = fpe.get("ticker_page") or {}
    eng_ticker = (ticker_page.get("ticker") if isinstance(ticker_page, dict) else "") or (fpe.get("ticker") or {}).get("ticker") or ""
    eng = {"title": (fpe.get("layout") or {}).get("company_name", ""), "ticker": eng_ticker, "company": company_page or "",
           "market": (yf or {}).get("market", "") if yf else "",
           "broker": fpe.get("broker_page") or fpe.get("broker") or basic.get("Broker") or "",
           "date": fpe.get("page_date") or basic.get("PageDate") or "",
           "rating": rating.get("text") or basic.get("Rating") or "", "rating_action": rating.get("action") or basic.get("RatingAction") or "",
           "target_price": tps.get("primary") if tps.get("primary") is not None else (basic.get("TargetPrice") or None),
           "current_price": fpe.get("current_price") if fpe.get("current_price") is not None else (basic.get("CurrentPrice") or None),
           "email": (f"{emails[0].get('analyst_id')}@{emails[0].get('broker_domain')}".lower() if emails and isinstance(emails[0], dict)
                     else (basic.get("AnalystEmail") or "")),
           "tel": (re.sub(r"\D", "", str(tel[0].get("number") or tel[0].get("raw") or tel[0])) if tel and isinstance(tel[0], dict)
                   else (re.sub(r"\D", "", str(tel[0])) if tel else "")),
           "analyst": (analysts[0].get("name") if analysts and isinstance(analysts[0], dict) else (analysts[0] if analysts else ""))
           or basic.get("Analyst") or "",
           "tri_code": tri.get("verdict", "")}
    ent = (regions_result or {}).get("entities") or {}
    return {"filename": {"ticker": dec.get("ticker") or ffields.get("ticker") or "", "company_names": dec.get("company_names") or [],
                         "broker": ffields.get("broker") or "", "date": ffields.get("date") or "", "rating": ffields.get("rating") or "",
                         "doc_class": dec.get("doc_class") or "", "stem": Path(name).stem},
            # 分析師名單（頁上 + 檔名）由 VRN_Evidence_Core 算，首頁引擎往上帶；
            # 非 PDF 沒有首頁引擎結果時，檔名那一半照樣算得出來（operator 2026-10-19）。
            # 標題那一路用它擋掉「代號前面那一段其實是人」，不自己再算一次。
            "analysts": _analyst_names(name, fpe, dec.get("ticker") or ffields.get("ticker") or ""),
            # 券商名「該在的位置」除了檔名與首頁，還有各頁頁尾小字與後方小字附錄
            # （operator 2026-10-20）。G15 已經把它們抽出來當 excluded，這裡只是帶過去讀。
            "bands": (regions_result or {}).get("excluded") or [],
            "engine": eng, "basic": basic, "entities": ent}


# [VRN-ID] VRN-ENG014-FNC051 · LOGIC
def analyze(path, name=None, regions_result=None, fpe=None, basic=None, brd_engine=None, financial=None):
    """One file -> {status, title, cover, annual, parts}.  Only STOCK reports (ENG393 DocClass) are taken further."""
    B = books()
    R, M = regions()
    path = Path(path)
    name = name or path.name
    suffix = Path(name).suffix.lower()
    started = time.perf_counter()
    out = {"file": name, "engine": "VRN_TitleTrim " + TITLE_TRIM_VERSION, "status": "", "why": "", "title": {}, "cover": {}, "annual": {},
           "parts": []}
    dec = (regions_result or {}).get("decomposition") or R.decompose(M, name)
    out["doc_class"] = dec.get("doc_class") or ""
    if dec.get("doc_class") != "STOCK":
        out.update(status="NOT_STOCK", why=f"只擷取個股報告：DocClass 冊判 {dec.get('doc_class') or '?'}（{dec.get('class_rule') or ''}）")
        return out
    if suffix in IMAGE_EXT:
        out.update(status="OCR_REQUIRED", why="影像檔：文字不在文字層，要 OCR 才拆得到（操作員決定是否裝 OCR）")
        out["parts"] = [{"part": "file.ocr", "value": "", "state": "REVIEW", "sources": {}, "why": out["why"]}]
        return out
    brd_engine = brd_engine if brd_engine is not None else first_page_engine()
    brd = getattr(brd_engine, "brd", None)
    try:
        page = page_lines(path) if suffix == ".pdf" else (text_lines(path) if suffix in TEXT_EXT else None)
    except Exception as error:  # noqa: BLE001
        out.update(status="ERROR", why=f"讀首頁 {error.__class__.__name__}: {error}"[:300])
        out["parts"] = [{"part": "file.read", "value": "", "state": "REVIEW", "sources": {}, "why": out["why"]}]
        return out
    if page is None:
        out.update(status="UNSUPPORTED", why=f"{suffix} 不在 PDF / DOCX / TXT")
        return out
    if regions_result is None:
        regions_result = R.analyze(path, name)
    ctx = report_context(name, fpe, basic, regions_result, brd_engine)
    ctx["db"] = db_lookup                                 # 2026-10-13: names and prices from the database
    title = pick_title(page, ctx, B, brd)
    title.update(decompose_title(title.get("raw") or "", ctx, B, brd) if title.get("raw") else
                 {"segments": {}, "clean": "", "steps": [], "loss": [], "pua": 0})
    names = [*((ctx.get("filename") or {}).get("company_names") or []), ((title.get("segments") or {}).get("company") or {}).get("value"),
             (ctx.get("engine") or {}).get("company")]
    cover = cover_fields(page, title, B, brd, tuple(dict.fromkeys(n for n in names if n and len(str(n)) >= 2)))
    an = annual(regions_result or {}, B, financial) if (regions_result or {}).get("status") == "OK" else {"pages": [], "cells": [], "specials": [],
                                                                                              "loss": [], "delta": []}
    parts = verify(title, cover, ctx, B, brd) + annual_parts(an)
    page_loss = [z for z in cover["zones"] if z["loss"]]
    for z in page_loss:
        parts.append({"part": f"cover.trim_loss:L{z['line']}", "value": z["clean"], "state": "TRIM_LOSS", "sources": {"原印": z["raw"]},
                      "why": "TRIM 少了：" + "、".join(z["loss"])})
    pua = sum(z["pua"] for z in cover["zones"])
    if pua:
        parts.append({"part": "cover.unreadable_glyphs", "value": pua, "state": "REVIEW", "sources": {},
                      "why": f"首頁有 {pua} 個私用區字元：{B.book['trim']['unreadable']['note']}"})
    out.update(status="OK", title=title, cover=cover, annual=an, parts=parts, pages=page.get("pages"),
               seconds=round(time.perf_counter() - started, 3))
    return out


# [VRN-ID] VRN-ENG014-FNC052 · LOGIC
def analyze_many(items, regions_by_file=None, fpe_by_file=None, basic_by_file=None, financial_by_file=None):
    """[(path, name)] -> results in input order.  One file at a time, in this process.

    2026-10-18：原本還收 `mapper` 與 `action` 兩個參數，但函式體從頭到尾沒有用過它們 ——
    永遠回 `lane: "sequential"`，也沒有任何呼叫端傳過。一個**宣稱有、實際沒接**的參數比沒有更糟：
    下一個人接上它會靜靜地沒有效果，而且不會有任何地方報錯。拿掉，讓介面說實話。

    這一關本來就不拆：`VRN_Main.ACCEL_BY_DESIGN` 記著「首頁引擎實例與快取共用，不拆執行緒
    （判讀邏輯不可動）」，G06／G07／G08 同列 —— 所以這裡不是少做了平行化，是裁定如此。
    """
    regions_by_file, fpe_by_file, basic_by_file = regions_by_file or {}, fpe_by_file or {}, basic_by_file or {}
    financial_by_file = financial_by_file or {}
    brd_engine = first_page_engine()
    started = time.perf_counter()
    results = []
    for p, n in items:
        n = n or Path(p).name
        try:
            results.append(analyze(p, n, regions_by_file.get(n), fpe_by_file.get(n), basic_by_file.get(n), brd_engine,
                                   financial_by_file.get(n) or financial_by_file.get(Path(n).name)))
        except Exception as error:  # noqa: BLE001
            results.append({"file": n, "status": "ERROR", "why": f"{error.__class__.__name__}: {error}"[:300], "parts": [
                {"part": "file.error", "value": "", "state": "REVIEW", "sources": {}, "why": f"{error.__class__.__name__}: {error}"[:300]}]})
    return results, {"lane": "sequential", "items": len(items), "seconds": round(time.perf_counter() - started, 3),
                     "why": "PyMuPDF 不能多執行緒共用；每檔只開首頁，表格用 G15 已還原的結果"}


# =====================================================================
# 8 . FLAT TABLES (DataFrame / CSV) AND THE FIX LIST
# =====================================================================
# [VRN-ID] VRN-ENG014-FNC053 · LOGIC
def title_rows(results):
    out = []
    order = ("company", "ticker", "market", "report_type", "core_view", "rating_action", "tp_change")
    for r in results:
        if r.get("status") != "OK":
            continue
        t = r.get("title") or {}
        seg = t.get("segments") or {}
        row = {"file": r["file"], "title_raw": t.get("raw", ""), "title_clean": t.get("clean", ""), "title_source": t.get("source", ""),
               "trim_steps": " · ".join(t.get("steps") or []), "trim_loss": " · ".join(t.get("loss") or []),
               "engine_title": t.get("engine_title", ""), "db_title": t.get("db_title", "")}
        for k in order:
            s = seg.get(k) or {}
            row[k] = "" if s.get("value") in (None,) else str(s.get("value", ""))
            row[k + "_state"] = s.get("state") or ("NO_TITLE" if not t.get("text") else "NOT_PRINTED")
        out.append(row)
    return out


# [VRN-ID] VRN-ENG014-FNC054 · LOGIC
def part_rows(results):
    out = []
    for r in results:
        for i, p in enumerate(r.get("parts") or [], 1):
            out.append({"file": r["file"], "seq": i, "part": p["part"], "value": "" if p.get("value") is None else str(p.get("value")),
                        "state": p["state"], "why": p.get("why", ""),
                        "sources": json.dumps(p.get("sources") or {}, ensure_ascii=False, default=str), "page": p.get("page"),
                        "effect": p.get("effect", ""),
                        # 支持採用值的來源群組數；空字串代表這個部位不是走 _vote 判的（例如從別的部位繼承狀態）。
                        # **型別要一致**：整數與空字串混在同一欄，G16 寫 parquet 時 Arrow 推不出型別
                        # （ArrowInvalid: Could not convert '' with type str: tried to convert to int64）——
                        # 我第一版就是這樣紅的。一律字串，讀的那一側自己 int()。
                        "agree": "" if p.get("agree") is None else str(p.get("agree"))})
    return out


# [VRN-ID] VRN-ENG014-FNC055 · LOGIC
def cell_rows(results):
    out = []
    for r in results:
        for i, c in enumerate((r.get("annual") or {}).get("cells") or [], 1):
            out.append({"file": r["file"], "seq": i, **{k: c.get(k) for k in (
                "page", "anchor", "label_raw", "label_clean", "metric_before", "metric", "block", "period_raw", "period", "kind",
                "printed_raw", "printed_clean", "value_before", "value", "unit", "effect", "db_value", "db_state", "state")},
                "verified_by": ",".join(c.get("verified_by") or []), "flagged_by": ",".join(c.get("flagged_by") or [])})
    return out


# [VRN-ID] VRN-ENG014-FNC056 · LOGIC
def fix_rows(results, lock_states=None):
    """Everything not yet right, worst first, with what to look at; `lock_states` (part key -> lock state) adds BROKEN locks.
    Round 5b (2026-10-12): every row carries the page line behind it (`evidence`), and conflicts come before missing parts,
    so the head of the list printed on the console is what a fix needs."""
    B = books()
    pri = B.verify["fix_priority"]
    out = []
    for r in results:
        if r.get("status") not in ("OK", "OCR_REQUIRED", "ERROR"):
            continue
        for p in r.get("parts") or []:
            lock = (lock_states or {}).get((r["file"], p["part"]), "")
            if p["state"] in pri or lock == "BROKEN":
                out.append({"file": r["file"], "part": p["part"], "state": p["state"], "lock": lock,
                            "priority": 0 if lock == "BROKEN" else pri.get(p["state"], 3),
                            "value": "" if p.get("value") is None else str(p.get("value")), "why": p.get("why", ""),
                            "sources": json.dumps(p.get("sources") or {}, ensure_ascii=False, default=str),
                            "evidence": report_evidence_line(r, p["part"], B)})
    rank = {"CONFLICT": 0, "MISSING": 1}
    out.sort(key=lambda x: (x["priority"], rank.get(x["state"], 2), x["file"], x["part"]))
    return out


# [VRN-ID] VRN-ENG014-FNC079 · REPORT
def report_evidence_line(result, part, B=None):
    """The page line a part was read from (cover.*: the TRIM field's line; a part TRIM did not read: the first line carrying
    one of its labels; title.*: the title) -> '行 N: text', or ''."""
    B = B or books()
    try:
        group, name = part.split(".", 1)
    except ValueError:
        return ""
    if group == "title":
        text = (result.get("title") or {}).get("text") or ""
        return f"標題: {text[:110]}" if text else ""
    if group != "cover":
        return ""
    cover = result.get("cover") or {}
    zones = cover.get("zones") or []
    field = (cover.get("fields") or {}).get(name) or (cover.get("declared_na") or {}).get(name) or {}
    line = field.get("line")
    if line and 0 < line <= len(zones):
        return f"行 {line}: {zones[line - 1].get('clean', '')[:110]}"
    labels = B.labels.get(name) or []
    for z in zones:
        if labels and _label_hits(z.get("clean") or "", labels, B):     # round 6: 'FTPS' is not the label TP
            return f"行 {z.get('line')}（有標籤，TRIM 沒讀到值）: {z.get('clean', '')[:100]}"
    return ""


# =====================================================================
# 9 . KNOWN ANSWERS (strings + three PDFs with messy text)
# =====================================================================
TITLE_CASES = [
    {"text": "台積電（２３３０ ＴＴ）－先進製程需求強勁，維持「買進」，目標價上調至ＮＴ＄１，２００",
     "ticker": "2330", "company": "台積電", "market": "", "rating_action": "MAINTAIN", "tp_current": 1200.0, "tp_direction": "up",
     "core_has": "先進製程需求強勁"},
    {"text": "TSMC (2330 TT): Raising TP to NT$1,200 (from NT$1,000); Maintain Outperform",
     "ticker": "2330", "company": "TSMC", "rating_action": "MAINTAIN", "tp_current": 1200.0, "tp_prior": 1000.0, "tp_direction": "up"},
    {"text": "聯發科(2454.TW) 首次評等：買進 AI 需求延續", "ticker": "2454", "company": "聯發科", "market": "TWSE",
     "rating_action": "INITIATE", "report_type": "INITIATION", "core_has": "AI 需求延續"},
    {"text": "【公司更新】鴻海 2317 TT\u3000目標價由 NT$200 下修至 NT$180", "ticker": "2317", "company": "鴻海",
     "report_type": "COMPANY_UPDATE", "tp_current": 180.0, "tp_prior": 200.0, "tp_direction": "down"},
    {"text": "元太(8069.TWO) 調降評等至中立，目標價 NT$250", "ticker": "8069", "market": "TPEX", "company": "元太",
     "rating_action": "DOWNGRADE", "tp_current": 250.0},
    {"text": "2025 年展望：燁輝 (2023) 營運回溫", "ticker": "2023", "filename_ticker": "2023", "company": "燁輝"},
    {"text": "2025 年展望：營運回溫", "ticker": ""},
    {"text": "臺積電(2330\u200b TT)\u00a0 3Q26 財報快評 — 毛利率優於預期", "ticker": "2330", "company": "台積電",
     "report_type": "EARNINGS_REVIEW", "core_has": "毛利率優於預期"},
]


# [VRN-ID] VRN-ENG014-FNC057 · VALIDATE
def check_title_case(case, B=None, brd=None):
    B = B or books()
    ctx = {"filename": {"ticker": case.get("filename_ticker", ""), "company_names": []}}
    d = decompose_title(case["text"], ctx, B, brd)
    s = d["segments"]
    got = {"ticker": s["ticker"]["value"], "company": s["company"]["value"], "market": s["market"]["value"],
           "rating_action": s["rating_action"]["value"], "report_type": s["report_type"]["value"],
           "tp_current": (s["tp_change"].get("current") if s["tp_change"].get("state") == "READ" else None),
           "tp_prior": s["tp_change"].get("prior"), "tp_direction": s["tp_change"].get("direction")}
    bad = []
    for k, v in case.items():
        if k in ("text", "filename_ticker", "core_has"):
            continue
        if got.get(k) != v:
            bad.append(f"{k}: 要 {v!r} 得 {got.get(k)!r}")
    if case.get("core_has") and case["core_has"] not in s["core_view"]["value"]:
        bad.append(f"core_view 要含 {case['core_has']!r} 得 {s['core_view']['value']!r}")
    if d["loss"]:
        bad.append("TRIM_LOSS " + "、".join(d["loss"]))
    return bad


# [VRN-ID] VRN-ENG014-FNC058 · BUILD
def build_fixtures(folder):
    """Eight stock reports with messy text (full-width digits and brackets, odd minus signs, two-line title, English title) and the
    layouts the real runs (2026-10-12) got wrong: prior TP before the TP, a dated price, an event date, 'first half' (round 1);
    the 兆豐 header box, the line under '前次投資建議', '第一階段', '股價10-11x', '12X 26(F) PER' (round 2); the 前次 box
    interleaved with body lines, two analysts, '+886 2', an NR report without a target, the broker in the e-mail domain (round 3)."""
    try:
        import fitz  # type: ignore
    except Exception:  # noqa: BLE001
        return []
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    truths = []
    name = "凱基_2330台積電_20260901_公司更新.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "凱基證券投資顧問 KGI Securities Research  ２０２６／０９／０１", fontname="china-t", fontsize=8)
    page.insert_text((40, 80), "台積電（２３３０ ＴＴ）－先進製程需求強勁", fontname="china-t", fontsize=18)
    page.insert_text((40, 104), "維持「買進」，目標價上調至ＮＴ＄１，２００", fontname="china-t", fontsize=16)
    for i, line in enumerate(["我們將目標價由 NT$1,000 上調至 NT$1,200，以 20x 2026E EPS 60 元評價。",
                              "先進製程與先進封裝需求延續，2026 年營收成長動能明確。"]):
        page.insert_text((40, 140 + 22 * i), line, fontname="china-t", fontsize=10)
    for i, line in enumerate(["投資評等：買進", "目標價：ＮＴ＄１，２００", "收盤價：NT$1,000", "潛在上漲空間：20.0%", "分析師：王小明",
                              "xiaoming.wang@kgi.com", "Tel: (02)2181-8888"]):
        page.insert_text((420, 140 + 16 * i), line, fontname="china-t", fontsize=8)
    head = ["損益表（NT$百萬元）", "2024A", "2025E", "2026E"]
    rows = [["營業收入", "１，０００", "1,200", "1,500"], ["營業成本", "600", "696", "840"], ["營業毛利", "400", "504", "660"],
            ["營業費用", "150", "180", "210"], ["營業利益", "250", "324", "450"], ["業外損益", "（10）", "－12", "(15)"],
            ["毛利率(%)", "40.0", "42.0", "44.0"], ["每股盈餘(元)", "8.00", "10.40", "14.40"], ["股利", "n.a.", "—", "△1"]]
    top = 300.0
    for r_i, row in enumerate([head] + rows):
        x = 40.0
        for c_i, cell in enumerate(row):
            w = (150, 80, 80, 80)[c_i]
            page.draw_rect(fitz.Rect(x, top + r_i * 18, x + w, top + (r_i + 1) * 18), color=(0, 0, 0), width=0.6)
            page.insert_text((x + 3, top + r_i * 18 + 13), cell, fontname="china-t", fontsize=8.5)
            x += w
    page.insert_text((40, 815), "本報告僅供參考，不構成投資建議。免責聲明：請參閱報告末頁。", fontname="china-t", fontsize=6)
    doc.set_metadata({"title": "Microsoft Word - 2330_update.docx"})
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "title_has": "台積電(2330 TT)-先進製程需求強勁 - 維持「買進」", "ticker": "2330", "company": "台積電", "market": "",
                   "rating_action": "MAINTAIN", "tp_change": "1,200 up", "cover": {"rating": "買進", "target_price": 1200.0,
                                                                                  "current_price": 1000.0, "upside": 20.0,
                                                                                  "analyst": "王小明", "email": "xiaoming.wang@kgi.com",
                                                                                  "broker": "KGI", "date": "2026-09-01"},
                   "verified": ["title.ticker", "title.company", "cover.target_price", "cover.date"],
                   "annual_pages": [1], "gain": {"revenue@2024": 1000.0, "nonop@2024": -10.0, "nonop@2025": -12.0}, "same": {"nonop@2026": -15.0},
                   "verified_cells": ["gross_profit@2025", "revenue@2025", "cogs@2025"], "null": 2, "triangle": 1})
    name = "KGI_2330_TSMC_20260905_Company Update.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "KGI Securities Research    5 Sep 2026", fontname="helv", fontsize=8)
    page.insert_text((40, 80), "TSMC (2330 TT): Raising TP to NT$1,200 (from NT$1,000);", fontname="helv", fontsize=16)
    page.insert_text((40, 100), "Maintain Outperform", fontname="helv", fontsize=16)
    for i, line in enumerate(["Rating: Outperform", "Target Price: NT$1,200", "Close: NT$1,000", "Analyst: Mary Chen",
                              "mary.chen@kgi.com"]):
        page.insert_text((400, 140 + 16 * i), line, fontname="helv", fontsize=8)
    page.insert_text((40, 140), "We raise our target price from NT$1,000 to NT$1,200 on 20x 2026E EPS.", fontname="helv", fontsize=10)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "title_has": "Maintain Outperform", "ticker": "2330", "company": "TSMC", "rating_action": "MAINTAIN",
                   "tp_change": "1,000→1,200 up", "cover": {"rating": "Outperform", "target_price": 1200.0, "current_price": 1000.0,
                                                           "analyst": "Mary Chen", "date": "2026-09-05", "broker": "KGI"},
                   "verified": ["title.ticker", "cover.date"]})
    name = "元大_2454聯發科_20260910_首次評等.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "元大證券投資顧問  Yuanta Research  2026/09/10", fontname="china-t", fontsize=8)
    page.insert_text((40, 80), "AI 需求延續 營運動能強勁", fontname="china-t", fontsize=20)
    page.insert_text((40, 106), "聯發科（2454.TW）首次評等：買進", fontname="china-t", fontsize=16)
    for i, line in enumerate(["評等：買進", "目標價：NT$1,500", "股價：NT$1,250"]):
        page.insert_text((420, 150 + 16 * i), line, fontname="china-t", fontsize=8)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "title_has": "AI 需求延續 營運動能強勁 - 聯發科(2454.TW)", "ticker": "2454", "company": "聯發科",
                   "market": "TWSE", "rating_action": "INITIATE", "report_type": "INITIATION",
                   "cover": {"rating": "買進", "target_price": 1500.0, "current_price": 1250.0, "date": "2026-09-10"},
                   "verified": ["title.ticker", "title.company", "title.report_type"]})
    name = "20250819兆豐個股報告-泓德能源(6873).pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "兆豐證券投資顧問 Mega Securities 研究部    報告日期：2025/08/19", fontname="china-t", fontsize=8)
    page.insert_text((40, 80), "泓德能源(6873)", fontname="china-t", fontsize=18)
    page.insert_text((40, 104), "逢低買進 $208", fontname="china-t", fontsize=16)
    for i, line in enumerate(["first half 營收年增 35%，下半年動能延續。", "法說會 2026/06/03 將說明新案場進度。"]):
        page.insert_text((40, 150 + 22 * i), line, fontname="china-t", fontsize=10)
    for i, line in enumerate(["投資評等：逢低買進", "前次目標價：345", "目標價：208", "股價(2025/08/18)：169.5", "潛在上漲空間：22.7%"]):
        page.insert_text((420, 150 + 16 * i), line, fontname="china-t", fontsize=8)
    page.insert_text((40, 815), "免責聲明：本報告由兆豐證券提供，第一金證券等其他機構之意見不代表本公司。", fontname="china-t", fontsize=6)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "title_has": "泓德能源(6873) - 逢低買進 $208", "ticker": "6873", "company": "泓德能源",
                   "cover": {"broker": "MEGA", "date": "2025-08-19", "current_price": 169.5, "target_price": 208.0, "upside": 22.7,
                             "rating": "逢低買進"},
                   "verified": ["title.ticker", "title.company", "cover.target_price", "cover.date", "cover.broker"]})
    # real run 2026-10-12 round 2: the 兆豐 header box ('投資評等 目標價' with the values one line down), the line under
    # '前次投資建議：日期' holding the previous rating and target, '第一階段', '股價10-11x', '12X 26(F) PER'
    name = "20251128兆豐訪談速報-神達(3706).pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "兆豐證券投資顧問 研究部    報告日期：2025/11/28", fontname="china-t", fontsize=8)
    page.insert_text((40, 80), "神達(3706)", fontname="china-t", fontsize=18)
    page.insert_text((40, 104), "訪談速報 買進 $128", fontname="china-t", fontsize=16)
    for i, line in enumerate(["投資評等  目標價", "買進  $128", "收盤價(11/27)：90.2", "前次投資建議：2025/06/03", "「買進」，目標價：78",
                              "潛在上漲空間：41.9%"]):
        page.insert_text((420, 150 + 16 * i), line, fontname="china-t", fontsize=8)
    for i, line in enumerate(["伺服器第一階段 300MW 將開始認列，2026 年營收成長。",
                              "目前股價對應約 12X 26(F) PER，評價位於股價10-11x 區間下緣。"]):
        page.insert_text((40, 300 + 22 * i), line, fontname="china-t", fontsize=10)
    page.insert_text((40, 815), "免責聲明：本報告由兆豐證券提供。", fontname="china-t", fontsize=6)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "title_has": "神達(3706)", "ticker": "3706", "company": "神達",
                   "cover": {"broker": "MEGA", "date": "2025-11-28", "current_price": 90.2, "target_price": 128.0, "upside": 41.9},
                   "prior_target_prices": [78.0], "not_read": ["2025-06-03"],
                   "verified": ["title.ticker", "cover.target_price", "cover.date", "cover.broker"]})
    # real run 2026-10-12 round 3: the 前次 box interleaved with body lines (sorted by y), two analysts, '+886 2' phone,
    # an NR report with no target, the broker only in the e-mail domain
    name = "凱基投顧_4171 瑞基_王小明_20251208.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "研究部 Research Department    報告日期：2025/12/08", fontname="china-t", fontsize=8)
    page.insert_text((40, 80), "瑞基(4171 TT) 個股介紹", fontname="china-t", fontsize=18)
    page.insert_text((40, 104), "未評等 (NR)", fontname="china-t", fontsize=16)
    page.insert_text((420, 150), "前次投資建議：2025/06/03", fontname="china-t", fontsize=8)
    page.insert_text((40, 158), "本公司未對本股票評等,僅作個股介紹。", fontname="china-t", fontsize=10)   # the left column, between the two
    page.insert_text((420, 166), "「買進」,目標價: 78", fontname="china-t", fontsize=8)
    page.insert_text((40, 176), "2026 年營收成長動能來自新產品。", fontname="china-t", fontsize=10)
    for i, line in enumerate(["收盤價(12/05)：45.5", "分析師：王小明", "xiaoming.wang@kgi.com", "李小華 lihua.lee@kgi.com",
                              "Tel: +886 2 2326 9812"]):
        page.insert_text((420, 186 + 16 * i), line, fontname="china-t", fontsize=8)
    page.insert_text((40, 815), "免責聲明：本報告僅供參考。電話:(02) 2181-8888", fontname="china-t", fontsize=6)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "title_has": "瑞基(4171 TT)", "ticker": "4171", "company": "瑞基", "rating_action": "NOT_RATED",
                   "cover": {"broker": "KGI", "date": "2025-12-08", "current_price": 45.5, "analyst": "王小明",
                             "email": "xiaoming.wang@kgi.com", "tel": "886223269812"},
                   "prior_target_prices": [78.0], "not_printed": ["cover.target_price"],
                   "all": {"email": ["xiaoming.wang@kgi.com", "lihua.lee@kgi.com"], "tel": ["886223269812", "0221818888"]},
                   "verified": ["title.ticker", "cover.date", "cover.broker"]})
    # real run 2026-10-12 round 4: the 兆豐 full report writes '前次投資建議 2025.08.06:' (the colon after the date) with the
    # previous target one line down, the header box one line below its labels, '股價10-11x' in the body
    name = "20251204兆豐個股報告-志強-KY(6768).pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "兆豐證券投資顧問 研究部    報告日期：2025/12/04", fontname="china-t", fontsize=8)
    page.insert_text((40, 80), "志強-KY(6768)", fontname="china-t", fontsize=18)
    page.insert_text((40, 104), "逢低買進 $145", fontname="china-t", fontsize=16)
    for i, line in enumerate(["投資評等  目標價", "逢低買進  $145", "股價(12/03)：118", "潛在上漲空間：23%", "前次投資建議 2025.08.06:"]):
        page.insert_text((420, 140 + 16 * i), line, fontname="china-t", fontsize=8)
    page.insert_text((40, 212), "2025/26 年EPS 預估7.7/11.19 元,目前評價位於股價10-11x,低於過往區間", fontname="china-t", fontsize=10)
    page.insert_text((420, 220), "目標價125 元「逢低買進」", fontname="china-t", fontsize=8)
    page.insert_text((40, 815), "免責聲明：本報告由兆豐證券提供。", fontname="china-t", fontsize=6)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "title_has": "志強-KY(6768)", "ticker": "6768",
                   "cover": {"broker": "MEGA", "date": "2025-12-04", "current_price": 118.0, "target_price": 145.0, "upside": 23.0},
                   "prior_target_prices": [125.0],
                   "verified": ["title.ticker", "cover.target_price", "cover.date", "cover.broker"]})
    # real run 2026-10-12 round 4: an English report: 'raise our TP from NT$3,600 to NT$4,200', '12M price target' (not the
    # share price), a phone with an extension
    name = "CLST-6669 20251001.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "CLSA Securities Taiwan Ltd    1 October 2025", fontname="helv", fontsize=8)
    page.insert_text((40, 80), "Wiwynn (6669 TT) Raising target", fontname="helv", fontsize=18)
    page.insert_text((40, 140), "We raise our 25-27CL EPS by 6-18% and raise our TP from NT$3,600 to NT$4,200. Maintain BUY.", fontname="helv", fontsize=9)
    for i, line in enumerate(["12M price target NT$4,200.00", "Share price (30 Sep 2025) NT$3,300.00", "Upside 27.3%", "Rating BUY",
                              "analyst@clsa.com", "Tel: +886 2 2326 9899 ext. 7960"]):
        page.insert_text((380, 180 + 16 * i), line, fontname="helv", fontsize=8)
    page.insert_text((40, 815), "Disclaimer: for information only.", fontname="helv", fontsize=6)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "title_has": "Wiwynn (6669 TT)", "ticker": "6669",
                   "cover": {"date": "2025-10-01", "current_price": 3300.0, "target_price": 4200.0, "upside": 27.3, "tel": "886223269899",
                             "email": "analyst@clsa.com"},
                   "prior_target_prices": [3600.0],
                   "verified": ["title.ticker", "cover.date", "cover.target_price"]})
    # real run 2026-10-20 round 7: the layout 59 of the 59 stock reports actually use -- rating, target and close all on ONE
    # line.  Every known answer so far put them on separate lines, so 'the close next to a target' was a path lock never walked.
    name = "20260518兆豐個股報告-聯詠(3034).pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "兆豐證券投資顧問 MEGA Securities Research", fontname="china-t", fontsize=8)
    page.insert_text((40, 80), "聯詠(3034 TT) 營運動能延續，評價仍具吸引", fontname="china-t", fontsize=18)
    page.insert_text((40, 110), "報告日期：2026/05/18    Bloomberg 3034 TT    Yahoo 3034.TW", fontname="china-t", fontsize=8)
    page.insert_text((40, 130), "投資評等：賣出    目標價：NT$182.5    收盤價：NT$140.4", fontname="china-t", fontsize=9)
    page.insert_text((40, 150), "分析師 王小明  analyst@example-research.com  (02)2181-8888", fontname="china-t", fontsize=8)
    for i, line in enumerate(["我們預估聯詠 2026 年稀釋 EPS 5.43 元，2027 年 6.87 元。",
                              "主要動能來自 AI 伺服器需求、產品組合改善與新產能開出。"]):
        page.insert_text((40, 190 + 22 * i), line, fontname="china-t", fontsize=10)
    page.insert_text((40, 815), "免責聲明：本報告由兆豐證券提供。", fontname="china-t", fontsize=6)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "title_has": "聯詠(3034 TT)", "ticker": "3034",
                   "cover": {"broker": "MEGA", "date": "2026-05-18", "rating": "賣出", "target_price": 182.5,
                             "current_price": 140.4},
                   "verified": ["title.ticker", "cover.date", "cover.broker"]})
    return truths


# [VRN-ID] VRN-ENG014-FNC059 · VALIDATE
def check_fixture(result, truth):
    """[(item, ok, detail)] for one fixture."""
    out = []
    t = result.get("title") or {}
    seg = t.get("segments") or {}
    parts = {p["part"]: p for p in result.get("parts") or []}
    out.append(("status", result.get("status") == "OK", result.get("why", "")))
    out.append(("title", truth["title_has"] in (t.get("clean") or ""), f"{t.get('clean')!r} 要含 {truth['title_has']!r}"))
    for k in ("ticker", "company", "market", "rating_action", "report_type", "tp_change"):
        if k in truth:
            got = (seg.get(k) or {}).get("value")
            out.append((f"title.{k}", got == truth[k], f"要 {truth[k]!r} 得 {got!r}"))
    fields = (result.get("cover") or {}).get("fields") or {}
    for k, v in (truth.get("cover") or {}).items():
        got = (fields.get(k) or {}).get("value")
        ok = (abs(float(got) - v) < 1e-6) if isinstance(v, float) and got not in (None, "") else got == v
        out.append((f"cover.{k}", ok, f"要 {v!r} 得 {got!r}"))
    for k in truth.get("verified") or []:
        out.append((f"{k} VERIFIED", (parts.get(k) or {}).get("state") == "VERIFIED", json.dumps(parts.get(k) or {}, ensure_ascii=False)[:200]))
    an = result.get("annual") or {}
    if "annual_pages" in truth:
        got = [p["page"] for p in an.get("pages") or []]
        out.append(("annual.pages", got == truth["annual_pages"], f"要 {truth['annual_pages']} 得 {got}"))
    cells = {f"{c['metric']}@{c['period']}": c for c in an.get("cells") or [] if c.get("metric")}
    for k, v in (truth.get("gain") or {}).items():
        c = cells.get(k) or {}
        out.append((f"TRIM 救回 {k}", c.get("effect") == "TRIM_GAIN" and c.get("value") == v, f"{c.get('effect')} {c.get('value')}"))
    for k, v in (truth.get("same") or {}).items():
        c = cells.get(k) or {}
        out.append((f"TRIM 前後一致 {k}", c.get("effect") == "SAME" and c.get("value") == v, f"{c.get('effect')} {c.get('value')}"))
    for k in truth.get("verified_cells") or []:
        out.append((f"annual.{k} VERIFIED", (parts.get(f"annual.{k}") or {}).get("state") == "VERIFIED",
                    (parts.get(f"annual.{k}") or {}).get("why", "")))
    if "null" in truth:
        n = sum(1 for s in an.get("specials") or [] if s["kind"] != "TRIANGLE")
        out.append(("NULL 照印", n == truth["null"], f"要 {truth['null']} 得 {n}"))
    if "triangle" in truth:
        n = sum(1 for s in an.get("specials") or [] if s["kind"] == "TRIANGLE")
        out.append(("三角形 REVIEW", n == truth["triangle"], f"要 {truth['triangle']} 得 {n}"))
    if "prior_target_prices" in truth:
        got = (result.get("cover") or {}).get("prior_target_prices")
        out.append(("前次那一行的目標價（不讀）", got == truth["prior_target_prices"], f"要 {truth['prior_target_prices']} 得 {got}"))
    for k, want in (truth.get("all") or {}).items():
        got = (fields.get(k) or {}).get("all")
        out.append((f"cover.{k} 首頁全部（分析師區先、頁尾最後）", got == want, f"要 {want} 得 {got}"))
    for k in truth.get("not_printed") or []:
        out.append((f"{k} NOT_PRINTED", (parts.get(k) or {}).get("state") == "NOT_PRINTED", json.dumps(parts.get(k) or {}, ensure_ascii=False)[:200]))
    loss = [p for p in result.get("parts") or [] if p["state"] in ("TRIM_LOSS", "TRIM_REGRESSION")]
    out.append(("TRIM 不掉數字、不讓驗算變差", not loss, "; ".join(p["part"] for p in loss)))
    return out


# [VRN-ID] VRN-ENG014-FNC060 · ENTRY
def selftest(verbose=True):
    """Title strings + three messy PDFs, every known answer.  The operator's database is kept out: the known answers are made-up
    reports (2330 at NT$1,000), so a real close would change them (the proof must give the same answer on every machine)."""
    global _LOCALDB
    saved, _LOCALDB = _LOCALDB, False
    try:
        return selftest_body(verbose)
    finally:
        _LOCALDB = saved


# [VRN-ID] VRN-ENG014-FNC091 · LOGIC
def selftest_body(verbose=True):
    B = books()
    brd = getattr(first_page_engine(), "brd", None)
    rows = []
    for case in TITLE_CASES:
        bad = check_title_case(case, B, brd)
        rows.append((f"標題 {case['text'][:24]}", not bad, "; ".join(bad)))
    t = trim("（１２３）　－４５％\u200b ＮＴ＄１，２００ 臺積電⽑利")
    rows.append(("TRIM 八步", t["clean"] == "(123) -45% NT$1,200 台積電毛利" and not t["loss"], repr(t["clean"]) + " " + str(t["loss"])))
    # 首頁印的平台碼要交給代號紀錄當第二條讀法；括號裡的也算，但只認冊上那兩組式子（Codex PR #76 P2）
    _codes = lambda text: {(c["platform"], c["raw"]) for c in ((cover_fields(
        {"height": 842.0, "lines": [{"text": text, "top": 80.0, "size": 12.0, "bbox": [40.0, 80.0, 500.0, 92.0]}]},
        {"joined": []}, B, brd)["fields"].get("page_codes") or {}).get("codes") or [])}
    _plain = _codes("報告日期：2025/08/19  Bloomberg 6873 TT  Yahoo 6873.TW")
    _paren = _codes("鴻海 (2317.TW) 法說會摘要") | _codes("TSMC (2330 TT) 先進製程")
    _nope = _codes("國光生(4142,Note)-CTBC260917") | _codes("慧洋-KY(2637-KY) 速報")
    rows.append(("首頁平台碼交給代號紀錄：直接印的、括號裡的都算；不是平台碼的不收",
                 _plain == {("bloomberg", "6873 TT"), ("yfinance", "6873.TW")}
                 and _paren == {("yfinance", "2317.TW"), ("bloomberg", "2330 TT")} and not _nope,
                 (sorted(_plain), sorted(_paren), sorted(_nope))))
    try:
        import fitz  # type: ignore  # noqa: F401
        have_fitz = True
    except Exception:  # noqa: BLE001
        have_fitz = False
    if have_fitz:
        R, M = regions()
        with tempfile.TemporaryDirectory(prefix="vrn_titletrim_") as tmp:
            truths = build_fixtures(Path(tmp) / "fx")
            for tr in truths:
                path = Path(tmp) / "fx" / tr["file"]
                res = analyze(path, tr["file"], R.analyze(path, tr["file"]))
                rows += [(f"{tr['file'][:18]} · {i}", ok, d) for i, ok, d in check_fixture(res, tr)]
    # 現價：基準日只能是「報告前一日的 adj」或「最新的 adj」（操作員 2026-10-16），
    # 不隨「印的價對到哪一天」跳動；缺 adj 才照實回原始收盤價（L99）。
    _near = lambda a, b: abs(float(a) - float(b)) < 0.005
    _q = {"basis": ("2026-09-14", 95.1), "same": ("2026-09-15", 96.9), "latest": "2026-09-18",
          "basis_adj": ("2026-09-14", 90.0), "same_adj": ("2026-09-15", 91.7), "latest_adj": ("2026-09-18", 93.4)}
    _on_same = _db_price_part(_q, [("g", "首頁", 96.9)], _near)          # 印的對到報告當日
    _on_prev = _db_price_part(_q, [("g", "首頁", 95.1)], _near)          # 印的對到前一日
    _no_prev = _db_price_part(dict(_q, basis_adj=None), [("g", "首頁", 96.9)], _near)
    _no_adj = _db_price_part(dict(_q, basis_adj=None, same_adj=None, latest_adj=None), [("g", "首頁", 96.9)], _near)
    rows += [("現價 · 基準是報告前一日的 adj，且不隨印的價對到哪一天跳動",
              (_on_same["value"], _on_same["date"]) == (90.0, "2026-09-14")
              and (_on_prev["value"], _on_prev["date"]) == (90.0, "2026-09-14"), (_on_same["value"], _on_prev["value"])),
             ("現價 · 狀態照原始收盤價比對，close 帶著走（上漲%重算與 record 要用）",
              _on_same["state"] == "VERIFIED" and _on_same["close"] == 96.9 and _on_same["dynamic"] is True, _on_same["close"]),
             ("現價 · 庫裡沒有報告前一日的 adj 就退到最新的 adj",
              (_no_prev["value"], _no_prev["date"]) == (93.4, "2026-09-18"), _no_prev["date"]),
             ("現價 · 完全沒有 adj 就照實回原始收盤價，不拿 close 當 adj（L99）",
              _no_adj["value"] == 96.9 and "不拿 close 當 adj" in _no_adj["why"], _no_adj["why"][:60])]
    bad = [r for r in rows if not r[1]]
    if verbose:
        for item, ok, detail in rows:
            print(f"  [{'PASS' if ok else 'FAIL'}] {item}" + ("" if ok else f" · {detail}"))
        print(f"[TITLETRIM] {len(rows) - len(bad)}/{len(rows)}")
    return 0 if not bad else 1, rows


# [VRN-ID] VRN-ENG014-FNC061 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(description="VRN TitleTrim: stock reports -> title segments, TRIMmed cover and annual pages, parts")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("selftest")
    run = sub.add_parser("run")
    run.add_argument("paths", nargs="+")
    run.add_argument("--json", default="")
    args = parser.parse_args(argv)
    if args.command == "run":
        files = []
        for p in args.paths:
            p = Path(p)
            files += sorted(q for q in p.rglob("*") if q.is_file()) if p.is_dir() else [p]
        results, lane = analyze_many([(f, f.name) for f in files])
        payload = {"lane": lane, "results": results}
        if args.json:
            Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        for r in results:
            states = Counter(p["state"] for p in r.get("parts") or [])
            print(f"{r['file']}: {r.get('status')} · " + " · ".join(f"{k} {v}" for k, v in states.most_common()))
        return 0
    return selftest()[0]


if __name__ == "__main__":
    sys.exit(main())
