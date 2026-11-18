#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG011 · VRN_PageRegions_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 2 · 函式 61；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_PageRegions v0100 -- individual-stock reports taken apart and put back together as a database, every number checked.

Operator 2026-10-11:
  「inputs示那些個股報告的檔案名稱拆解 首頁的資訊區 本文區切割資訊區 年度財報告面左頁對切 不同圖在上下切 output確定
    有辦法還原資料轉為資料庫並擷取到對的輸出值並驗算通過 use all sample document 只擷取個股報告 … 所有動作都要加入加速器 …
    評價方法 完整無後自其他vrn vdf抓來 financial data加減法及除法驗算法自其他抓完備」

What runs, per file (nothing here is a second copy of logic that exists elsewhere):
  1. file name   -> mother ENG393 DocClassVerify v0100 (DocClass book): class, ticker, rule, evidence.  Only STOCK goes on
                    (只擷取個股報告); the others are listed with the reason, never guessed.
  2. layout      -> mother ENG394 LayoutRestore v0100 + its v0101 tail (ported below) on ENG392's XY cut (LayoutRestore book):
                    every page is cut left / right
                    first, then top / bottom; each leaf is INFO (first-page card, header / footer bands, key-value blocks,
                    tables), BODY (one numbered sentence per row under its heading), FIGURE or EXCLUDED (disclaimers,
                    repeated page headers).  Tables: merged cells filled, a table with an empty column is split left / right,
                    an empty row or a new header splits it top / bottom.  Completeness: every character of the text layer must
                    be captured (>= 99.9 %).
  3. restore     -> each restored table becomes rows (metric x period x value, the printed text kept beside the number);
                    the metric names are the AnnualExtract book's keys (79 line items, zh / en).
  4. check       -> ssot/VRN_FinIdentity_SSOT_v0100.json: add / subtract / divide identities harvested from FieldRules v0101,
                    Method SSOT def07-def18, AnnualExtract formulas and the first-page engine; tolerance Method def15.
                    Measured, never corrected.
  5. entities    -> mother ENG396 ReportEntities (company name forms, target price prior -> current, valuation multiple x
                    metric = target price) with ENG395's valuation-method lexicon (16 methods, about 279 terms).
  6. database    -> one SQLite file: reports / regions / tables / rows / checks / sentences / entities / excluded.

Mother engines are byte copies in engine/mother/ (provenance: ssot/VRN_ENGINES_PROVENANCE_v0100.json); they are loaded by
path and handed VRN's own copies of their books, so they never look outside VRN and never write anywhere.

Accelerator: PyMuPDF cannot share a process between threads, so files are split into chunks, each chunk runs in its own
worker process, and the chunks are dispatched through the caller's accelerator lane (accel_map when mounted); results come
back through the TEMP run.  No network; LIVE off; no consent variable is read or set.
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
import importlib.util
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PAGE_REGIONS_VERSION = "v0100"
VRN_ROOT = Path(__file__).resolve().parents[1]
MOTHER_DIR = VRN_ROOT / "engine" / "mother"
SSOT_DIR = VRN_ROOT / "ssot"
TITLETRIM_SSOT = SSOT_DIR / "VRN_TitleTrim_SSOT_v0100.json"
_FOCUS_BOOK: dict = {}


# [VRN-ID] VRN-ENG011-FNC053 · LOGIC
def focus_book():
    """TitleTrim 冊的 focus 區塊（doc_class_policy 住在那裡）。讀不到就回空的，呼叫端退回舊範圍。

    這裡直接讀 JSON 而不是 import VRN_TitleTrim —— TitleTrim 會載入本模組，反過來 import 會成環。
    讀的是同一個檔，政策仍然只有一份。
    """
    if not _FOCUS_BOOK:
        try:
            _FOCUS_BOOK.update(json.loads(TITLETRIM_SSOT.read_text(encoding="utf-8")).get("focus") or {})
        except (OSError, ValueError):
            _FOCUS_BOOK["_absent"] = True
    return _FOCUS_BOOK


# [VRN-ID] VRN-ENG011-FNC054 · LOGIC
def class_policy(focus, doc_class):
    """ENG393 的 doc_class → 這一類怎麼處理。**全系統唯一一份這個判斷**：

    VRN_Focus 走 `R.class_policy(...)` 呼叫到這裡，不自己再寫一份；
    兩個地方各判一次，遲早會各說各話（這個倉已經被那種事咬過）。
    冊裡沒有 doc_class_policy 就退回 2026-10-11 G19 的舊範圍（只處理個股）。
    """
    table = (focus or {}).get("doc_class_policy") or {}
    if not table:
        return {"process": "FULL" if doc_class == "STOCK" else "SKIP", "rows": "ONE_PER_REPORT",
                "why": "冊裡沒有 doc_class_policy：退回 2026-10-11 G19 的舊範圍"}
    return table.get(doc_class) or table.get("_default") or {"process": "SKIP", "rows": "ONE_PER_REPORT",
                                                             "why": "政策表沒有這一類"}
MOTHER_FILES = {
    "eng392": "VRN_ENG392_TextCompleteness_v0100.py",
    "eng394": "VRN_ENG394_LayoutRestore_v0100.py",
    "eng395": "VRN_ENG395_ValuationMethodLexicon_v0100.py",
    "eng396": "VRN_ENG396_ReportEntities_v0100.py",
    "eng393": "VRN_ENG393_DocClassVerify_v0100.py",
}
BOOK_FILES = {
    "layout": SSOT_DIR / "VRN_LayoutRestore_SSOT_v0100.json",
    "docclass": SSOT_DIR / "03_ssot" / "VRN_DocClass_SSOT_v0100.json",
    "valuation": SSOT_DIR / "03_ssot" / "VRN_ValuationMethod_SSOT_v0100.json",
    "entities": SSOT_DIR / "03_ssot" / "VRN_ReportEntities_SSOT_v0100.json",
    "identity": SSOT_DIR / "VRN_FinIdentity_SSOT_v0100.json",
    "annual": SSOT_DIR / "VRN_AnnualExtract_SSOT_v0100.json",
    "method": SSOT_DIR / "VRN_Method_SSOT_v0100.json",
    "operator_labels": SSOT_DIR / "VRN_OperatorLabels_SSOT_v0100.json",
}
DB_NAME = "VRN_ReportRegions_v0100.sqlite"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
TEXT_EXT = {".txt", ".docx"}


# [VRN-ID] VRN-ENG011-FNC001 · IO
def read_book(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    if isinstance(data, dict):
        data["_path"] = Path(path).name
    return data


# =====================================================================
# 1 . THE MOTHER ENGINES, LOADED BY PATH AND GIVEN VRN'S BOOKS
# =====================================================================
# [VRN-ID] VRN-ENG011-CLS001 · CLASS
class Mother:
    """ENG392 / 393 / 394 / 395 / 396 from engine/mother/, each pointed at VRN's copy of its book."""

    # [VRN-ID] VRN-ENG011-FNC002 · INIT
    def __init__(self):
        self.errors = {}
        self.books = {key: read_book(path) for key, path in BOOK_FILES.items()}
        for key, data in self.books.items():
            if data is None:
                self.errors["book:" + key] = f"{BOOK_FILES[key].name} 不在或讀不了"
        self.e392 = self._load("eng392")
        self.e394 = self._load("eng394")
        self.e395 = self._load("eng395")
        self.e396 = self._load("eng396")
        self.e393 = self._load("eng393")
        self.degraded = self._helpers_absent()
        self._wire()
        self._matcher = None
        self._broker_aliases = None
        self.ledger = Ledger(self.books.get("identity") or {}, self.books.get("annual") or {}, self.books.get("method") or {},
                             self.books.get("operator_labels") or {})

    # [VRN-ID] VRN-ENG011-FNC056 · LOGIC
    def broker_aliases(self):
        """中文券商別名，長的先排 —— 只給 _split_glued_broker 切 token 用，不做券商判定。

        取的是**首頁引擎真正在用的那一張組好的表**（`BrokerRatingDict.b`），不是生冊。
        Codex PR #74 P2 指的就是這一點：生冊 v0100 有 10 筆記錄（華南、日盛、統一、大華、合庫、
        康和、宏遠、麥格理、里昂、摩根士丹利）的 canonical key 本身就是中文名、底下卻沒有
        `aliases` 陣列 —— 只讀 `aliases` 會把它們整批漏掉，`3653健策華南投顧.txt` 照樣切不開。
        真正解決問題的是**換表**：組好的表裡 `華南投顧` 是 `HUANAN` 這一筆的 alias
        （實測 60 → 128 個中文名，華南／華南投顧／華南永昌／日盛／摩根士丹利 都在）。
        Codex 建議的「把 canonical key 也算進去」單獨做**救不了他自己舉的例子** ——
        生冊的 key 是 `華南`，而 `3653健策華南投顧` 的尾巴是 `華南投顧`。
        `+ [canon]` 還是留著：組好的表今天的 key 全是英文（HUANAN／JIHSUN／MS），
        所以這一段目前一個名字都沒多加，純粹是防著哪天表改成以中文當 key ——
        **它沒有測試蓋得到，就照實說它沒有**。

        **延後載入**：只有真的找到「代號後面黏中文」的 token 才會問到這裡
        （`_glued_token` 先擋，實測 106 檔裡只有 4 檔問得到），所以 G15 的子行程平常不為它載首頁引擎。
        載不到就回空 —— 不切，維持現狀。
        """
        if self._broker_aliases is None:
            names = set()
            try:
                spec = importlib.util.spec_from_file_location("vrn_regions_fpe", VRN_ROOT / "engine" / "VIA_VRN_FirstPageEngine.py")
                fpe = importlib.util.module_from_spec(spec)
                sys.modules.setdefault("vrn_regions_fpe", fpe)
                spec.loader.exec_module(fpe)
                table = getattr(fpe.FirstPageEngine().brd, "b", {}) or {}
                for canon, alias_set in table.items():
                    for one in list(alias_set or []) + [canon]:
                        if re.search(r"[\u4e00-\u9fff]", str(one or "")):
                            names.add(str(one))
            except Exception as error:  # noqa: BLE001
                self.errors["broker_aliases"] = f"{error.__class__.__name__}: {error}"[:200]
            self._broker_aliases = sorted(names, key=len, reverse=True)
        return self._broker_aliases

    # [VRN-ID] VRN-ENG011-FNC003 · LOGIC
    def _load(self, key):
        path = MOTHER_DIR / MOTHER_FILES[key]
        name = "vrn_regions_" + key
        if name in sys.modules:
            return sys.modules[name]
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            return module
        except Exception as error:  # noqa: BLE001
            sys.modules.pop(name, None)
            self.errors[key] = f"{path.name}: {error.__class__.__name__}: {error}"[:300]
            return None

    # [VRN-ID] VRN-ENG011-FNC059 · LOGIC
    def _helpers_absent(self):
        """母引擎自己還要叫的**助手引擎**，哪些不在這個倉裡。

        實測 2026-10-20：ENG393 DocClassVerify 要 eng072／eng073／eng114 三個助手，`engine/mother/` 只鏡了五支，
        三個都不在。ENG393 於是整路靜默降級 —— 107 檔實測 `broker_raw` 0/107、`report_date` 0/107、
        `fine_kind_eng073` 與 `fine_type_eng114` 全 None，連「這四位數是不是年份」的代號守衛
        （ENG073 的 `_date_spans` / `_is_year_like`，那支函式的說明寫著三道守衛）都沒跑。
        而 `self.errors` 是空的：沒有閘、沒有 WARN，什麼都沒說。

        本機 VDF 資料庫缺席會在三個地方報出來，缺一支**引擎**卻一聲不響 —— 不知道不等於沒事。
        助手缺席不致命（讀出來的值實測仍然對），所以不混進 `errors`（那會讓 G15 直接 FAIL 收攤），
        自己一欄，讓閘喊 WARN。
        """
        out = {}
        for key in MOTHER_FILES:
            module = getattr(self, "e" + key[3:], None)
            for name in dir(module or ()):
                if not re.fullmatch(r"eng\d{3}", name):
                    continue
                try:
                    got = getattr(module, name)()
                except Exception:                         # 要參數的、會爆的都不算助手探測
                    continue
                mod, why = got if isinstance(got, tuple) else (got, "")
                if mod is None:
                    out[f"{key}:{name}"] = str(why or "不在")
        return out

    # [VRN-ID] VRN-ENG011-FNC004 · LOGIC
    def _wire(self):
        books = self.books
        if self.e394 is not None and books.get("layout"):
            self.e394._SSOT_CACHE = books["layout"]
            if self.e392 is not None:
                self.e394._eng392 = lambda: self.e392        # one ENG392 instead of a fresh copy per file
            tail_v0101(self.e394)
        if self.e395 is not None and books.get("valuation"):
            original = self.e395.load_ssot
            self.e395.load_ssot = lambda path=None: original(path or BOOK_FILES["valuation"])
        if self.e396 is not None and books.get("entities"):
            self.e396._BOOK = books["entities"]
            self.e396._MODS["VRN_ENG395_ValuationMethodLexicon"] = self.e395
            self.e396._MODS["VRN_ENG394_LayoutRestore"] = self.e394
        if self.e393 is not None and books.get("docclass"):
            self.e393._BOOK[""] = books["docclass"]

    # [VRN-ID] VRN-ENG011-FNC005 · LOGIC
    @property
    def matcher(self):
        if self._matcher is None and self.e395 is not None:
            self._matcher = self.e395.Matcher()
        return self._matcher

    # [VRN-ID] VRN-ENG011-FNC006 · LOGIC
    def describe(self):
        return {"engines": {k: MOTHER_FILES[k] for k in MOTHER_FILES if getattr(self, "e" + k[3:], None) is not None},
                "books": {k: BOOK_FILES[k].name for k, v in self.books.items() if v is not None}, "errors": dict(self.errors),
                "degraded": dict(getattr(self, "degraded", {}) or {})}


# ---------------------------------------------------------------------------------------------------------------------
# ENG394 v0101's thin tail (mother c88acc4f, functional modules/VRN/VRN_ENG394_LayoutRestore_v0101.py), ported unchanged
# in behaviour: a second file numbered ENG394 next to v0100 collides in central governance G32 (one number, one file),
# so the tail is applied here to the v0100 body exactly as v0101 applies itself to its PRIOR:
#   table-of-contents fix · cross-page / same-page de-duplication · two numberings (S0001 / section.sentence) ·
#   completeness = every character of the text layer captured (ENG392's coverage), >= 99.9 % GREEN.
# ---------------------------------------------------------------------------------------------------------------------
COVER_MIN = 0.999
SAME_PAGE_MIN = 12
SUB_ZH = {"KV": "鍵值", "TOC": "目錄"}


# [VRN-ID] VRN-ENG011-FNC042 · LOGIC
def tail_v0101(e394):
    """Apply v0101 to a loaded v0100 module (idempotent)."""
    if getattr(e394, "_vrn_tail_v0101", False):
        return
    tidy = e394.tidy

    # [VRN-ID] VRN-ENG011-FNC043 · LOGIC
    def _lines_toc(lns):
        heads = [h.lower() for h in e394.ssot().get("toc_heads", [])]
        rows, used, i = [], 0, 0
        while i < len(lns):
            t = tidy(lns[i]["text"])
            m = re.match(r"^(.*?[A-Za-z一-鿿].*?)\s*(?:\.{3,}|…+)?\s+(\d{1,3})$", t)
            nxt_pg = i + 1 < len(lns) and re.fullmatch(r"\d{1,3}", tidy(lns[i + 1]["text"]))
            if t.lower() in heads and not nxt_pg:
                used += 1
            elif m:
                rows.append([tidy(m.group(1)), m.group(2)])
                used += 1
            elif nxt_pg and re.search(r"[A-Za-z一-鿿]", t):
                rows.append([t, tidy(lns[i + 1]["text"])])
                used += 2
                i += 1
            i += 1
        pg = [int(r[1]) for r in rows]
        if len(rows) >= 3 and used >= 0.6 * len(lns) and sum(1 for a, b in zip(pg, pg[1:]) if b >= a) >= 0.8 * (len(pg) - 1):
            return rows
        return None

    # [VRN-ID] VRN-ENG011-FNC044 · LOGIC
    def _key(s):
        return re.sub(r"\s+", "", str(s or "")).lower()

    # [VRN-ID] VRN-ENG011-FNC060 · LOGIC
    def _span(anchor):
        """文字檔的定位是來源字元區間 `c<起>-<迄>` —— 解得出來就回 (起, 迄)，否則 None（PDF 的定位不是這個形狀）。"""
        m = re.fullmatch(r"c(\d+)-(\d+)", str(anchor or ""))
        return (int(m.group(1)), int(m.group(2))) if m else None

    # [VRN-ID] VRN-ENG011-FNC045 · LOGIC
    def dedup(res):
        pages = res.get("pages") or [res]
        n = len(pages)
        seen_on = {}
        for p in pages:
            for k in {_key(b["text"]) for b in p.get("body", []) if len(_key(b["text"])) >= 2}:
                seen_on[k] = seen_on.get(k, 0) + 1
        cross = {k for k, c in seen_on.items() if c >= 2 and c * 2 >= n}
        first_kept, removed = set(), 0
        for p in pages:
            keep, here = [], set()
            for b in p.get("body", []):
                k = _key(b["text"])
                why = ""
                if k in cross and k in first_kept:
                    why = f"跨頁重複(出現在 {seen_on[k]}/{n} 頁:頁眉 / 頁尾 / 浮水印)"
                elif k in here and len(k) >= SAME_PAGE_MIN:
                    why = "同頁重複句"
                if why:
                    p.setdefault("excluded", []).append({"anchor": b["anchor"], "bbox": b.get("bbox"), "reason": why, "size": b.get("size"),
                                                         "head": b["text"][:40], "lines": 1, "text": b["text"], "dedup": True})
                    removed += 1
                    continue
                here.add(k)
                if k in cross:
                    first_kept.add(k)
                keep.append(b)
            p["body"] = keep
        res["dedup"] = {"removed": removed, "cross_page_keys": len(cross)}
        return res

    # [VRN-ID] VRN-ENG011-FNC046 · LOGIC
    def number(res):
        pages = res.get("pages") or [res]
        sid, sec, idx, title, tn, fn = 0, 0, 0, "", 0, 0
        for p in pages:
            for b in p.get("body", []):
                sid += 1
                b["no"] = f"S{sid:04d}"
                if b.get("subcategory") in ("H1", "H2", "H3"):
                    sec, idx, title = sec + 1, 0, b["text"]
                    b["sec_no"], b["title"] = f"{sec}.0", b["text"]
                else:
                    idx += 1
                    b["sec_no"], b["title"] = f"{max(sec, 0)}.{idx}", title or "(首段 · 無標題)"
                b["cat"] = e394.CAT_ZH.get(b.get("category", "text"), "文")
            for t in p.get("info", []):
                tn += 1
                t["no"] = f"T{tn:02d}"
                t["sub2"] = SUB_ZH.get(t.get("subcategory"), t.get("subcategory")) or {
                    "pdf_grid": "格線表", "pdf_text": "扁平表", "text": "扁平表", "pdf_info": "鍵值", "pdf_toc": "目錄"}.get(t.get("origin", ""), "表")
            for f in p.get("figures", []):
                fn += 1
                f["no"] = f"F{fn:02d}"
                f["sub2"] = "影像" if f.get("origin") == "pdf_image" else "座標軸圖"
        return res

    # [VRN-ID] VRN-ENG011-FNC047 · LOGIC
    def _captured_text(p):
        body = [b["text"] for b in p.get("body", [])]
        info = []
        for t in p.get("info", []):
            info += [str(c) for c in t.get("columns", [])]
            if t.get("subcategory") == "KV":
                info += [f"{r[0]}：{r[1]}" if r[0] else str(r[1]) for r in t.get("rows", [])]
            else:
                info += [str(x) for r in t.get("rows", []) for x in r]
            info += [t.get("source") or "", t.get("caption") or "", t.get("title") or ""] + list(t.get("notes") or [])
        figs = []
        for f in p.get("figures", []):
            figs += [f.get("table_no") or "", f.get("title") or "", " ".join(f.get("x_labels") or []), " ".join(f.get("data_labels") or []),
                     f.get("legend") or "", f.get("source") or "", " ".join(str(v) for v in (f.get("axis") or {}).get("ticks", []))]
        excl = [e.get("text") or e.get("head") or "" for e in p.get("excluded", [])]
        return " ".join(body + info + figs), " ".join(excl)

    # [VRN-ID] VRN-ENG011-FNC048 · LOGIC
    def completeness(res, src_pages):
        e392 = e394._eng392()
        rows, worst = [], "GREEN"
        for p, src in zip(res.get("pages") or [res], src_pages):
            kept, excl = _captured_text(p)
            if e392 is None:
                rows.append({"page": p.get("page", 1), "state": "NODATA", "why": "ENG392 不在"})
                worst = "NODATA" if worst == "GREEN" else worst
                continue
            cap, miss, _x = e392.coverage(src, kept + " " + excl)
            ext, _m2, _x2 = e392.coverage(src, kept)
            segs = [s for s in e392.missing_segments(src, kept + " " + excl) if not s.get("moved")][:8] if miss else []
            lamp = "GREEN" if cap >= COVER_MIN else "RED"
            if lamp == "RED":
                worst = "RED"
            rows.append({"page": p.get("page", 1), "src_chars": len(re.sub(r"\s", "", src)), "captured": round(cap * 100, 2),
                         "extracted": round(ext * 100, 2), "missing_chars": sum(miss.values()), "segments": segs, "state": lamp})
        return {"verdict": worst, "pages": rows, "rule": "截取 = 本文 + 資訊區 + 圖 + 排除區原文;≥ 99.9% GREEN(ENG392 同一把尺)"}

    # [VRN-ID] VRN-ENG011-FNC049 · LOGIC
    def _src_pages(path, sel):
        import fitz  # type: ignore
        out = []
        with fitz.open(str(path)) as doc:
            for pno in sel:
                chars = []
                for b in doc[pno - 1].get_text("rawdict").get("blocks", []):
                    if b.get("type") != 0:
                        continue
                    for ln in b.get("lines", []):
                        chars.append("".join(ch.get("c", "") for sp in ln.get("spans", []) for ch in sp.get("chars", [])))
                out.append("\n".join(chars))
        return out

    # [VRN-ID] VRN-ENG011-FNC050 · LOGIC
    def _fill_excluded_text(path, res):
        import fitz  # type: ignore
        with fitz.open(str(path)) as doc:
            for p in res.get("pages", []):
                page = doc[p["page"] - 1]
                for e in p.get("excluded", []):
                    if not e.get("text") and e.get("bbox"):
                        try:
                            e["text"] = tidy(page.get_text("text", clip=fitz.Rect(*e["bbox"])))
                        except (ValueError, TypeError, RuntimeError) as exc:
                            e["text_error"] = f"{type(exc).__name__}"

    prior_restore, prior_text = e394.restore_pdf, e394.text_restore

    # [VRN-ID] VRN-ENG011-FNC051 · LOGIC
    def restore_pdf(path, pages="1"):
        res = prior_restore(path, pages)
        _fill_excluded_text(Path(path), res)
        dedup(res)
        number(res)
        res["completeness"] = completeness(res, _src_pages(Path(path), [p["page"] for p in res["pages"]]))
        if res["completeness"]["verdict"] == "RED" and res["verdict"] != "RED":
            res["verdict"] = "RED"
        return res

    # [VRN-ID] VRN-ENG011-FNC061 · LOGIC
    def _recover_text_lines(text, res):
        """母引擎吞掉的內文行，照原文補回 body；回傳補了幾行。

        實測 2026-10-20：文字檔沒有版面座標，ENG394 的扁平表解析會把內文一起吃掉 ——
        8 個 .docx／.txt **每一檔**都只收到八成（`3653健策…txt` 387 字收 312 字，
        漏的正是「主要動能…毛利率可望維持在高檔」與「催化因素…風險…」那兩句，
        也就是四重點第 3、4 點的料）；合成語料上 12 行內文甚至一行都收不到。
        母引擎在 `engine/mother/` 是鏡像、不能改，所以在 VRN 這一側補。

        判準只有一條、不靠量表反推（靠量表補就等於讓量表自己證明自己）：
        **來源裡整行的字沒被任何區塊收走的，照原順序把原文補回去**，
        比對用的是這支引擎自己的 `_key`（去空白、轉小寫），不另立一把尺。
        """
        kept, excl = _captured_text(res)
        have, back, pos = _key(kept + " " + excl), 0, 0
        for raw in str(text or "").split("\n"):
            line = raw.strip()
            if _key(line) and _key(line) not in have:
                at = pos + len(raw) - len(raw.lstrip())           # 定位照母引擎自己的寫法：來源字元區間 c<起>-<迄>
                to = at + len(line)
                # Codex PR #78 P2：母引擎只收到半行時（本文尾段被扁平表切斷），整行補回去會和原塊重疊、
                # 同一句在 sentences 出現兩次，而且 `_key` 完全相同才會被 dedup 清掉，前綴對整行清不掉。
                # 用**來源字元區間**判重疊（不是模糊比字）：疊到了就把原塊的尾巴接長，不另開一塊。
                host = next((b for b in res.get("body") or [] if _span(b.get("anchor")) and _span(b["anchor"])[0] <= at < _span(b["anchor"])[1]), None)
                if host is not None:
                    a0, a1 = _span(host["anchor"])
                    host["text"] = str(host.get("text") or "") + str(text)[a1:to]
                    host["anchor"] = f"c{a0}-{to}"
                    host["recovered"], host["why"] = True, "母引擎 ENG394 只收到這一行的前半，尾段照原文接回"
                else:
                    res.setdefault("body", []).append({"text": line, "category": "text", "subcategory": "BODY",
                                                       "anchor": f"c{at}-{to}", "size": None, "bold": None,
                                                       "recovered": True,
                                                       "why": "母引擎 ENG394 的扁平表解析沒收走這一行，照原文補回"})
                back += 1
            pos += len(raw) + 1
        if back:
            # Codex PR #78 P2：補回的塊接在最後面，遇到「表在前、內文在後」時句號會倒著發
            # （後面那句拿 S0001、前面那句拿 S0002）。編號之前照來源位置排回去。
            body = res.get("body") or []
            if all(_span(b.get("anchor")) for b in body):
                body.sort(key=lambda b: _span(b["anchor"]))
        return back

    # [VRN-ID] VRN-ENG011-FNC052 · LOGIC
    def text_restore(text):
        res = prior_text(text)
        res.setdefault("page", 1)
        recovered = _recover_text_lines(text, res)
        dedup(res)
        number(res)
        res["completeness"] = completeness(res, [text])
        for row in (res["completeness"].get("pages") or []):
            row["recovered_lines"] = recovered      # 補回來不等於沒事：補了幾行要看得見
        return res

    e394._lines_toc = _lines_toc
    e394.restore_pdf = restore_pdf
    e394.text_restore = text_restore
    e394._vrn_tail_v0101 = True


_MOTHER = None


# [VRN-ID] VRN-ENG011-FNC007 · LOGIC
def mother():
    global _MOTHER
    if _MOTHER is None:
        _MOTHER = Mother()
    return _MOTHER


# =====================================================================
# 2 . METRIC NAMES AND PERIODS (the AnnualExtract book's keys)
# =====================================================================
_PAREN_RX = re.compile(r"[（(]([^()（）]{0,24})[）)]")
_UNIT_RX = re.compile(r"%|％|元|倍|x|X|NT\$|US\$|HK\$|RMB|百萬|千|億|萬|天|日|次|days?|times|mn|bn|m\b", re.I)
_MARK_RX = re.compile(r"[*＊※†‡]+|註\s*\d*$|\(\s*註\s*\d*\s*\)$")


# [VRN-ID] VRN-ENG011-FNC008 · LOGIC
def norm_label(text):
    """'營業毛利(利益)' / '毛利率 (%)' / 'Gross Profit*' -> the comparable form (NFKC, no blanks, no trailing brackets)."""
    s = unicodedata.normalize("NFKC", str(text or "")).strip()
    s = _MARK_RX.sub("", s).strip()
    while True:
        m = re.search(r"[（(][^()（）]{0,24}[）)]\s*$", s)
        if not m:
            break
        s = s[:m.start()].rstrip()
    return re.sub(r"\s+", "", s).lower().replace("－", "-")


# [VRN-ID] VRN-ENG011-FNC009 · LOGIC
def unit_of(text):
    for m in _PAREN_RX.finditer(unicodedata.normalize("NFKC", str(text or ""))):
        if _UNIT_RX.search(m.group(1)):
            return m.group(1).strip()
    return "%" if str(text or "").strip().endswith(("%", "％")) else ""


# [VRN-ID] VRN-ENG011-CLS002 · CLASS
class Ledger:
    """Row label -> operand key.  Labels: AnnualExtract items (zh / en), the identity book's extra operands, Method def05.
    A label claimed by two keys keeps the first owner and is listed (shown, never merged)."""

    # [VRN-ID] VRN-ENG011-FNC010 · INIT
    def __init__(self, identity_book, annual_book, method_book, operator_book=None):
        self.book = identity_book or {}
        self.key_of, self.block_of, self.conflicts, self.growth_of = {}, {}, [], {}
        self.patterns = []                               # (compiled, key, source): whole-label fallback, operator upload 2026-10-11
        for item in (annual_book or {}).get("items", []):
            self._add(item.get("key"), item.get("zh", []) + item.get("en", []) + [item.get("key", "")], item.get("block", ""))
        for key, spec in (self.book.get("extra_operands") or {}).items():
            self._add(key, spec.get("labels_zh", []) + spec.get("labels_en", []) + [key], spec.get("block", ""))
            if spec.get("growth_of"):
                self.growth_of[key] = spec["growth_of"]
        mapping = ((self.book.get("method_labels") or {}).get("map")) or {}
        for field, labels in ((method_book or {}).get("def05_canonical_fields") or {}).items():
            if field in mapping and isinstance(labels, list):
                self._add(mapping[field], labels, self.block_of.get(mapping[field], ""))
        for key, labels in ((operator_book or {}).get("operand_labels") or {}).items():
            self._add(key, labels, self.block_of.get(key, ""))
        for key, spec in ((operator_book or {}).get("operand_patterns") or {}).items():
            for text in spec.get("regex") or []:
                try:
                    self.patterns.append((re.compile(text, re.I), key, "; ".join(spec.get("from") or [])))
                except re.error:
                    self.conflicts.append({"label": text, "kept": "", "also": key, "why": "regex 不能編譯"})

    # [VRN-ID] VRN-ENG011-FNC011 · LOGIC
    def _add(self, key, labels, block):
        if not key:
            return
        self.block_of.setdefault(key, block)
        for label in labels:
            n = norm_label(label)
            if not n:
                continue
            owner = self.key_of.get(n)
            if owner is None:
                self.key_of[n] = key
            elif owner != key:
                self.conflicts.append({"label": label, "kept": owner, "also": key})

    # [VRN-ID] VRN-ENG011-FNC012 · LOGIC
    def lookup(self, label):
        """Exact label first (the books); then the operator's whole-label patterns (fullmatch, never a substring)."""
        n = norm_label(label)
        if n in self.key_of:
            return self.key_of[n]
        for rx, key, _src in self.patterns:
            if rx.fullmatch(n):
                return key
        return ""


_ROC_DIGITS = {"一": "1", "二": "2", "三": "3", "四": "4"}


# [VRN-ID] VRN-ENG011-FNC013 · LOGIC
def period_of(text):
    """A column / row label that names a period -> {'key': '2025' | '2025Q1' | '2025H1', 'year', 'part', 'kind', 'raw'}."""
    raw = str(text or "")
    s = unicodedata.normalize("NFKC", raw).strip().upper().replace(" ", "")
    s = re.sub(r"[*※]+$", "", s)
    year = part = kind = ""
    m = re.fullmatch(r"(?:FY)?((?:19|20)\d{2})([AEFP])?", s) or re.fullmatch(r"FY(\d{2})([AEFP])?", s)
    if m:
        year, kind = m.group(1), m.group(2) or ""
    elif re.fullmatch(r"'?(\d{2})([AEF])", s):
        m = re.fullmatch(r"'?(\d{2})([AEF])", s)
        year, kind = m.group(1), m.group(2)
    elif re.fullmatch(r"([1-4])Q(\d{2}|\d{4})([AEF])?", s):
        m = re.fullmatch(r"([1-4])Q(\d{2}|\d{4})([AEF])?", s)
        part, year, kind = "Q" + m.group(1), m.group(2), m.group(3) or ""
    elif re.fullmatch(r"((?:19|20)\d{2})[-/]?Q([1-4])([AEF])?", s):
        m = re.fullmatch(r"((?:19|20)\d{2})[-/]?Q([1-4])([AEF])?", s)
        year, part, kind = m.group(1), "Q" + m.group(2), m.group(3) or ""
    elif re.fullmatch(r"([12])H(\d{2}|\d{4})([AEF])?", s):
        m = re.fullmatch(r"([12])H(\d{2}|\d{4})([AEF])?", s)
        part, year, kind = "H" + m.group(1), m.group(2), m.group(3) or ""
    elif re.fullmatch(r"(\d{3,4})年(?:度)?(?:第?([1-4一二三四])季)?([AEF]|\(預估\)|\(實際\))?", s):
        m = re.fullmatch(r"(\d{3,4})年(?:度)?(?:第?([1-4一二三四])季)?([AEF]|\(預估\)|\(實際\))?", s)
        y = int(m.group(1))
        year = str(y + 1911) if y < 1000 else str(y)              # 民國 113 年 = 2024
        part = ("Q" + _ROC_DIGITS.get(m.group(2), m.group(2))) if m.group(2) else ""
        kind = {"(預估)": "E", "(實際)": "A"}.get(m.group(3) or "", m.group(3) or "")
    elif re.fullmatch(r"Q([1-4])", s):
        return {"key": "", "year": None, "part": "Q" + s[1], "kind": "", "raw": raw}
    elif re.fullmatch(r"(?:FY)?(\d{1,2})/(\d{2}|\d{4})([AEFP])?", s):           # 2026-10-12 real run: '12/25E' (fiscal year ending 12/2025)
        m = re.fullmatch(r"(?:FY)?(\d{1,2})/(\d{2}|\d{4})([AEFP])?", s)
        if not 1 <= int(m.group(1)) <= 12 or (not m.group(3) and int(m.group(1)) != 12):
            return None                                   # '11/27' is a date; a fiscal year needs A/E/F/P or a December end
        year, kind = m.group(2), m.group(3) or ""
    elif re.fullmatch(r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[-'’]?(\d{2}|\d{4})([AEFP])?", s):   # 'Dec-25E'
        m = re.fullmatch(r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[-'’]?(\d{2}|\d{4})([AEFP])?", s)
        if not m.group(3) and m.group(1) != "DEC":
            return None                                   # 'Jan-25 Feb-25 …' is a monthly table, not fiscal years
        year, kind = m.group(2), m.group(3) or ""
    else:
        return None
    y = int(year)
    if y < 100:
        y += 2000
    if not 1990 <= y <= 2100:
        return None
    return {"key": f"{y}{part}", "year": y, "part": part, "kind": kind, "raw": raw}


# =====================================================================
# 3 . RESTORED TABLES -> ROWS
# =====================================================================
# [VRN-ID] VRN-ENG011-FNC014 · EXTRACT
def parse_num(M, text):
    if M.e394 is not None:
        try:
            return M.e394.parse_num(text)
        except Exception:  # noqa: BLE001
            return None
    try:
        return float(str(text).replace(",", "").replace("%", ""))
    except ValueError:
        return None


# [VRN-ID] VRN-ENG011-FNC015 · LOGIC
def _decimals(text):
    m = re.search(r"\.(\d+)", str(text or ""))
    return len(m.group(1)) if m else 0


# [VRN-ID] VRN-ENG011-FNC016 · LOGIC
def table_rows(M, file_name, tables):
    """Every numeric cell of a restored table -> {metric, period, value, printed}; the orientation is read from the labels."""
    out = []
    for t in tables:
        if t.get("subcategory") in ("KV", "TOC") or not t.get("rows"):
            continue
        cols = [str(c) for c in t.get("columns") or []]
        rows = [list(r) for r in t.get("rows") or []]
        generic = all(not c or re.fullmatch(r"欄\d+", c) for c in cols)
        first = [period_of(str(c)) for c in (rows[0][1:] if rows else [])]
        if generic and rows and first and sum(1 for p in first if p and p["key"]) * 2 >= len(first):
            cols, rows = [str(c) for c in rows[0]], rows[1:]     # a header of plain years ('2026') reads as numbers upstream
        table_unit = unit_of(cols[0]) if cols else ""
        col_periods = [period_of(c.split("/")[-1]) for c in cols[1:]]
        row_periods = [period_of(r[0]) for r in rows if r]
        n_col = sum(1 for p in col_periods if p and p["key"])
        n_row = sum(1 for p in row_periods if p and p["key"])
        cells = []
        if n_col and n_col >= n_row:
            for r in rows:
                label = str(r[0]) if r else ""
                for ci, p in enumerate(col_periods, 1):
                    if p and p["key"] and ci < len(r):
                        cells.append((label, p, r[ci], cols[ci]))
        elif n_row:
            for r, p in zip(rows, row_periods):
                for ci in range(1, min(len(r), len(cols))):
                    head = cols[ci]
                    label, q = head, None
                    if "/" in head:                                  # '營收/Q1' with the year in the row
                        label, tail = head.rsplit("/", 1)
                        q = period_of(tail)
                    if p and p["key"]:
                        pp = dict(p)
                        if q and q.get("part") and not p.get("part"):
                            pp["part"], pp["key"] = q["part"], f"{p['year']}{q['part']}"
                        cells.append((label, pp, r[ci], head))
        for label, p, printed, head in cells:
            value = parse_num(M, printed)
            if value is None:
                continue
            key = M.ledger.lookup(label)
            out.append({"file": file_name, "anchor": t.get("anchor", ""), "page": _page_of(t.get("anchor", "")),
                        "metric_raw": str(label), "metric": key, "block": M.ledger.block_of.get(key, ""),
                        "period_raw": p["raw"], "period": p["key"], "kind": p.get("kind", ""), "value": value,
                        "printed": str(printed), "unit": unit_of(label) or unit_of(head) or table_unit})
    return out


# [VRN-ID] VRN-ENG011-FNC017 · LOGIC
def _page_of(anchor):
    m = re.match(r"p(\d+)", str(anchor or ""))
    return int(m.group(1)) if m else None


# =====================================================================
# 4 . ADD / SUBTRACT / DIVIDE (ssot/VRN_FinIdentity_SSOT_v0100.json)
# =====================================================================
# [VRN-ID] VRN-ENG011-FNC018 · LOGIC
def _judge(diff, tol):
    if diff <= tol:
        return "PASS"
    return "WARN" if diff <= 3 * tol else "FAIL"


# [VRN-ID] VRN-ENG011-FNC019 · LOGIC
def _operand(values, name):
    """'a|b' = the first one the table has; '|capex|' = its size; '1' = the number one."""
    if name == "1":
        return 1.0, "1", "1"
    absolute = name.startswith("|") and name.endswith("|")
    for alt in name.strip("|").split("|"):
        if alt in values:
            v, printed = values[alt]
            return (abs(v) if absolute else v), printed, alt
    return None, "", name


# [VRN-ID] VRN-ENG011-FNC020 · LOGIC
def _sum(values, terms):
    total, printed, used, missing = 0.0, [], {}, []
    for coef, name in terms:
        v, p, alt = _operand(values, name)
        if v is None:
            missing.append(name.strip("|"))
            continue
        total += coef * v
        printed.append(p)
        used[alt] = v
    return total, printed, used, missing


# [VRN-ID] VRN-ENG011-FNC021 · LOGIC
def _tol(ident, kind_tol, lhs, rhs, printed):
    rounding = sum(0.5 * 10 ** -_decimals(p) for p in printed)
    tol_abs = max(float(ident.get("tol_abs", kind_tol.get("abs", 0.0))), rounding)
    tol_rel = float(ident.get("tol_rel", kind_tol.get("rel", 0.0)))
    return max(tol_abs, tol_rel * max(abs(lhs), abs(rhs)))


# [VRN-ID] VRN-ENG011-FNC022 · LOGIC
def identity_state(ident, values, tolerance_book):
    """One identity on one period -> {state, lhs, rhs, diff, tol, detail, used}."""
    kind_tol = ((tolerance_book or {}).get("by_kind") or {}).get(ident.get("kind", "amount"), {})
    op = ident.get("op")
    target = ident.get("target")
    tgt_terms = target if isinstance(target, list) else [[1, target]]
    lhs, lp, lused, lmiss = _sum(values, tgt_terms)
    if op == "lin":
        rhs, rp, rused, rmiss = _sum(values, ident["terms"])
        scale_note = ""
    elif op == "le":                                   # reasonableness: target <= the terms (Method def12), never FAIL
        rhs, rp, rused, rmiss = _sum(values, ident["terms"])
        if not lmiss and not rmiss:
            tol = _tol(ident, kind_tol, lhs, rhs, lp + rp)
            if rhs < 0:
                return {"state": "PASS", "lhs": lhs, "rhs": rhs, "diff": None, "tol": tol, "detail": "虧損：反稀釋不計入，不比",
                        "used": dict(lused, **rused)}
            state = "PASS" if lhs <= rhs + tol else ident.get("fail_state", "WARN")
            return {"state": state, "lhs": lhs, "rhs": rhs, "diff": max(0.0, lhs - rhs), "tol": tol,
                    "detail": "" if state == "PASS" else "稀釋 EPS 大於基本 EPS（照列，不改）", "used": dict(lused, **rused)}
        scale_note = ""
    elif op == "ratio":
        num, npr, nused, nmiss = _sum(values, ident.get("num") or [])
        if ident.get("den"):
            den, dpr, dused, dmiss = _sum(values, ident["den"])
        else:
            den, dpr, dused, dmiss = 1.0, [], {}, []
        rp, rused, rmiss = npr + dpr, dict(nused, **dused), nmiss + dmiss
        if not rmiss and not lmiss and den == 0:
            return {"state": "DIV_ZERO", "lhs": lhs, "rhs": None, "diff": None, "tol": None, "detail": "分母為 0：不可計算",
                    "used": dict(lused, **rused)}
        rhs = (num / den) * float(ident.get("scale", 1)) if not rmiss else 0.0
        scale_note = ""
    else:
        return {"state": "INSUFFICIENT", "detail": f"op {op} 由專屬函式驗", "used": {}}
    missing = lmiss + rmiss
    if rmiss and not (set(rused) - {"1"}):
        return {"state": "SKIP", "detail": "算式右邊的數字一個都不在表上", "used": dict(lused)}
    if missing:
        notes = ident.get("required_note") or {}
        hit = [notes[m] for m in missing if m in notes]
        state = "INCOMPLETE_COMPONENTS" if hit and len(missing) == len([m for m in missing if m in notes]) and len(missing) < len(
            tgt_terms) + len(ident.get("terms") or ident.get("num") or []) else "INSUFFICIENT"
        return {"state": state, "lhs": None, "rhs": None, "diff": None, "tol": None, "missing": missing,
                "detail": ("缺 " + "、".join(missing)) + ((" · " + hit[0]) if hit else ""), "used": dict(lused, **rused)}
    used = dict(lused, **rused)
    tol = _tol(ident, kind_tol, lhs, rhs, lp + rp)
    diff = abs(lhs - rhs)
    state = _judge(diff, tol)
    if state != "PASS" and op == "ratio":
        scale = float(ident.get("scale", 1)) or 1.0
        rounding = max([0.5 * 10 ** -_decimals(p) for p in lp] or [0.0])
        rel = float(ident.get("tol_rel", kind_tol.get("rel", 0.03)) or 0.03)
        for alt in ident.get("alt_scales_ok") or []:                # 流動比率印成倍數（1.8x）也是對的寫法
            r2 = rhs / scale * float(alt)
            if abs(lhs - r2) <= max(rel * abs(r2), rounding):
                return {"state": "PASS", "lhs": lhs, "rhs": r2, "diff": abs(lhs - r2), "tol": max(rel * abs(r2), rounding),
                        "detail": f"以 ×{alt:g} 表示（冊上允許）", "used": used}
        probes = []
        if ident.get("kind") == "pct":
            probes = [(0.01, "比率印成小數（40 vs 0.40）"), (100.0, "比率差 100 倍")]
        if ident.get("scale_probe"):
            probes += [(10.0 ** k, f"差 ×{10.0 ** k:g}") for k in (-3, -2, -1, 1, 2, 3)]
        for k, why in probes:
            r2 = rhs * k
            if r2 and abs(lhs - r2) <= max(rel * abs(r2), rounding):
                return {"state": "UNIT_SCALE", "lhs": lhs, "rhs": rhs, "diff": diff, "tol": tol, "detail": why + "（照列，不改）",
                        "used": used}
    if state == "FAIL" and ident.get("approx"):
        state = "WARN"
        scale_note = "冊上的式子用平均數，表上只有期末數：最多 WARN"
    return {"state": state, "lhs": lhs, "rhs": rhs, "diff": diff, "tol": tol, "detail": scale_note, "used": used}


# [VRN-ID] VRN-ENG011-FNC023 · LOGIC
def growth_state(cur, prev, printed_pct, tol_abs):
    """Method def11: (cur - prev) / |prev| x 100 with the six states."""
    if prev is None:
        return "INSUFFICIENT", None
    if prev == 0:
        return "NOT_COMPUTABLE_ZERO_BASE", None
    calc = (cur - prev) / abs(prev) * 100
    if prev < 0 < cur:
        return "TURNAROUND_TO_PROFIT", calc
    if cur < 0 < prev:
        return "TURNAROUND_TO_LOSS", calc
    if prev < 0 and cur < 0:
        return "NEG_TO_NEG_ANNOTATED", calc
    tol = max(tol_abs, 0.5 * 10 ** -_decimals(printed_pct))
    return _judge(abs(calc - float(printed_pct.replace(",", "").rstrip("%％")) if isinstance(printed_pct, str) else abs(calc)), tol), calc


# [VRN-ID] VRN-ENG011-FNC024 · VALIDATE
def check_rows(M, rows):
    """Every identity of the book on every period the restored tables give."""
    book = M.ledger.book
    tol_book = book.get("tolerance") or {}
    by_period, conflicts = {}, []
    for r in rows:
        if not r["metric"] or not r["period"]:
            continue
        slot = by_period.setdefault(r["period"], {})
        if r["metric"] in slot:
            if abs(slot[r["metric"]][0] - r["value"]) > 1e-9:
                conflicts.append({"period": r["period"], "metric": r["metric"], "kept": slot[r["metric"]][1], "also": r["printed"],
                                  "anchor": r["anchor"]})
            continue
        slot[r["metric"]] = (r["value"], r["printed"])
    out = []
    for period in sorted(by_period, key=lambda k: (k[:4], k[4:])):
        values = by_period[period]
        for ident in book.get("identities") or []:
            op = ident.get("op")
            if op in ("lin", "ratio", "le"):
                target = ident.get("target")
                printed = [name for _c, name in (target if isinstance(target, list) else [[1, target]])]
                if any(_operand(values, name)[0] is None for name in printed):
                    continue                                          # the result is not printed: nothing to verify
                res = identity_state(ident, values, tol_book)
                if res["state"] == "SKIP":
                    continue
                out.append(dict(res, period=period, id=ident["id"], zh=ident.get("zh", ""), source=ident.get("source", "")))
            elif op == "growth":
                for tgt in ident.get("targets") or []:
                    base = M.ledger.growth_of.get(tgt)
                    if tgt not in values or not base or base not in values:
                        continue
                    year = int(period[:4])
                    prev_key = f"{year - 1}{period[4:]}"
                    prev = (by_period.get(prev_key) or {}).get(base)
                    state, calc = growth_state(values[base][0], prev[0] if prev else None, values[tgt][1], float(ident.get("tol_abs", 0.6)))
                    out.append({"period": period, "id": f"YOY:{tgt}", "zh": ident.get("zh", ""), "source": ident.get("source", ""),
                                "state": state, "lhs": values[tgt][0], "rhs": calc, "diff": None if calc is None else abs(values[tgt][0] - calc),
                                "tol": ident.get("tol_abs"), "detail": "" if prev else f"缺 {prev_key} 的 {base}",
                                "used": {base: values[base][0], tgt: values[tgt][0]}})
    for ident in book.get("identities") or []:
        if ident.get("op") != "annual_sum":
            continue
        blocks = set(ident.get("blocks") or [])
        years = sorted({p[:4] for p in by_period if len(p) == 4 and p + "Q1" in by_period})
        for y in years:
            for metric, (v, printed) in by_period[y].items():
                if M.ledger.block_of.get(metric) not in blocks:
                    continue
                qs = [(by_period.get(f"{y}Q{i}") or {}).get(metric) for i in range(1, 5)]
                if any(q is None for q in qs):
                    continue
                total = sum(q[0] for q in qs)
                tol = max(float(ident.get("tol_rel", 0.01)) * max(abs(v), abs(total)), sum(0.5 * 10 ** -_decimals(q[1]) for q in qs))
                out.append({"period": y, "id": f"ANNUAL_SUM:{metric}", "zh": ident.get("zh", ""), "source": ident.get("source", ""),
                            "state": _judge(abs(v - total), tol), "lhs": v, "rhs": total, "diff": abs(v - total), "tol": tol, "detail": "",
                            "used": {metric: v}})
    return out, conflicts


# =====================================================================
# 5 . ONE FILE
# =====================================================================
# [VRN-ID] VRN-ENG011-FNC025 · LOGIC
def decompose(M, name):
    """File name -> ENG393 DocClass row (class, ticker, rule, confidence, evidence) + ENG396 name forms."""
    row = {"file": name}
    if M.e393 is None:
        row.update(doc_class="", why=M.errors.get("eng393", "ENG393 不在"))
        return row
    try:
        c = M.e393.classify(name)
    except Exception as error:  # noqa: BLE001
        row.update(doc_class="", why=f"classify {error.__class__.__name__}: {error}"[:200])
        return row
    for key in ("doc_class", "doc_class_zh", "class_confidence", "class_rule", "class_evidence", "ticker", "broker_raw", "report_date",
                "needs_review", "route"):
        row[key] = c.get(key)
    if M.e396 is not None:
        try:
            stem = Path(name).stem
            ident = M.e396.company_identity(stem, "")
            if not ident.get("names") and row.get("ticker"):     # '2330台積電': ENG396 wants the code set apart; ENG393 found it
                ident = M.e396.company_identity(stem.replace(str(row["ticker"]), f"_{row['ticker']}_", 1), "")
            if not ident.get("names") and _glued_token(stem, row.get("ticker")):   # '3653健策凱基投顧': 券商也黏在一起
                spaced = _split_glued_broker(stem, row["ticker"], M.broker_aliases())
                if spaced:
                    ident = M.e396.company_identity(spaced, "")
            row["company_names"] = [n.get("name") for n in ident.get("names", []) if n.get("name")]
        except Exception:  # noqa: BLE001
            row["company_names"] = []
    return row


# [VRN-ID] VRN-ENG011-FNC058 · LOGIC
def _glued_token(stem, ticker):
    """檔名裡有沒有「代號後面直接黏著中文」的 token —— 便宜的形狀檢查，不用載任何冊。

    `_split_glued_broker` 要的券商別名表得載首頁引擎才拿得到，所以先用這一支擋在前面：
    沒有這種 token 就連問都不問（實測 106 檔裡只有 4 檔問得到）。
    """
    code = str(ticker or "")
    if not code:
        return ""
    for tok in re.split(r"[_\-\s()（）]+", stem):
        if tok.startswith(code) and len(tok) > len(code) and re.search(r"[\u4e00-\u9fff]", tok[len(code):]):
            return tok
    return ""


# [VRN-ID] VRN-ENG011-FNC057 · LOGIC
def _split_glued_broker(stem, ticker, aliases):
    """`3653健策凱基投顧 向子慧` → `_3653_健策_凱基投顧 向子慧`：代號與券商別名都切開，公司名才站得出來。

    2026-10-20 操作員：「把那 3 筆缺的補到 100% 過關」。實測 `3653健策凱基投顧 向子慧 (3).txt`
    的公司（健策）在正文出現 0 次，只黏在檔名裡，而且三段（代號＋公司＋券商）之間一個分隔符都沒有。
    ENG396 是 MIRROR_MOTHER（逐位元組，不能改），它要看得到邊界才認得公司名 ——
    上面那條 `_<ticker>_` 的 workaround 已經是同一招，這裡只是把券商那一邊也切開。

    **公司名由 ENG396 認，不是這裡剝字串當答案**：這支只回一個「補了分隔符的檔名」，
    認不認得、認成什麼，還是 ENG396 說。邊界在哪則由 VRN 自己的券商別名冊說（只讀不猜）。

    守得很窄：token 要以**這一份報告的代號**開頭，剩下那段要以冊上的中文別名結尾，
    切完兩邊都不能是空的。實測語料裡只有 1 檔符合（另外 3 個像的 token —— `6533,N,中立`、
    `2026年投資大趨勢`、`2026海外投資展望` —— 都在這三道守門前就被擋掉）。
    """
    code = str(ticker or "")
    if not code or not aliases:
        return ""
    for tok in re.split(r"[_\-\s()（）]+", stem):
        if not tok.startswith(code) or len(tok) <= len(code):
            continue
        rest = tok[len(code):]
        if not re.search(r"[一-鿿]", rest):
            continue
        for alias in aliases:
            if rest.endswith(alias) and len(rest) > len(alias):
                return stem.replace(tok, f"_{code}_{rest[:-len(alias)]}_{alias}", 1)
    return ""


# [VRN-ID] VRN-ENG011-FNC026 · LOGIC
def _clean(obj):
    """JSON-safe copy (tuples -> lists, sets -> sorted lists, floats kept)."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, set):
        return sorted(_clean(v) for v in obj)
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


# [VRN-ID] VRN-ENG011-FNC027 · LOGIC
def _page_texts(path):
    import fitz  # type: ignore
    with fitz.open(str(path)) as doc:
        return [page.get_text("text") for page in doc]


# [VRN-ID] VRN-ENG011-FNC028 · LOGIC
def _docx_text(path):
    """Word 的文字：表格一列一行、欄與欄之間用 tab；表外段落各自一行。

    2026-10-19 實測：本來是把整份 document.xml 的每一個 `<w:p>` 抓出來用換行接起來。
    但 Word 的表格**每一個儲存格裡都有自己的 `<w:p>`** —— 一張 15 列 4 欄的表於是變成
    60 行一欄，行列結構整個沒了，ENG394 的扁平表解析拼不回來。量到的後果：

        .pdf   98 檔 → 51 檔有財務列 → 2142 列
        .docx   7 檔 →  0 檔         →    0 列
        .txt    1 檔 →  0 檔         →    0 列

    非 PDF 的財務表是**整張不見**，不是掉幾個字。改成照文件順序走：`<w:tbl>` 裡
    每個 `<w:tr>` 的儲存格用 tab 接成一行（和 .txt 的扁平表同一個形狀），表外的
    `<w:p>` 仍是一行。`<w:tbl>` 放在交替的前面，finditer 掃到表就整塊吃掉，
    裡面的 `<w:p>` 不會再被當成獨立段落。

    不引 python-docx：這支只要文字，而且 G06 的 extract_docx_text_and_zones 已經
    用 python-docx 讀表讀得好好的 —— 兩邊要的東西不一樣（這裡要「一段文字」、
    那裡要「結構化的表」），所以各自留著，但形狀要對得上，不能一邊有表一邊沒有。
    已知限制：`.*?</w:tbl>` 碰到巢狀表會停在內層那個；巢狀表很罕見，而改之前這支
    連一張表都拼不出來。
    """
    import zipfile
    with zipfile.ZipFile(str(path)) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")

    # [VRN-ID] VRN-ENG011-FNC055 · LOGIC
    def _runs(chunk):
        return "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", chunk, flags=re.S))

    out = []
    for block in re.finditer(r"<w:tbl[ >].*?</w:tbl>|<w:p[ >].*?</w:p>", xml, flags=re.S):
        chunk = block.group(0)
        if chunk.startswith("<w:tbl"):
            for row in re.findall(r"<w:tr[ >].*?</w:tr>", chunk, flags=re.S):
                cells = [" ".join(_runs(c).split()) for c in re.findall(r"<w:tc[ >].*?</w:tc>", row, flags=re.S)]
                if any(cells):
                    out.append("\t".join(cells))
        else:
            t = _runs(chunk)
            if t:
                out.append(t)
    return "\n".join(out)


# [VRN-ID] VRN-ENG011-FNC029 · LOGIC
def analyze(path, name=None, pages="all"):
    """One file -> decomposition, regions, tables, rows, checks, sentences, entities (only STOCK reports past step 1)."""
    M = mother()
    path = Path(path)
    name = name or path.name
    suffix = Path(name).suffix.lower()
    started = time.perf_counter()
    out = {"file": name, "suffix": suffix, "engine": "VRN_PageRegions " + PAGE_REGIONS_VERSION, "status": "", "why": "",
           "decomposition": decompose(M, name), "regions": [], "tables": [], "rows": [], "checks": [], "conflicts": [],
           "sentences": [], "figures": [], "excluded": [], "entities": {}, "completeness": {}, "pages": 0}
    cls = out["decomposition"].get("doc_class") or ""
    rule = class_policy(focus_book(), cls)
    out["process"] = rule.get("process") or "SKIP"
    out["rows_shape"] = rule.get("rows") or "ONE_PER_REPORT"
    if out["process"] != "FULL":
        # 2026-10-15：非個股不再一律 NOT_STOCK。SKIP 照舊不拆；COVERAGE／REGISTER 拆到報告層就停
        # （券商、報告日、標題、型別都在檔名與首頁，不需要個股那一整套）。
        status = {"SKIP": "NOT_STOCK", "COVERAGE": "COVERAGE", "REGISTER": "REGISTERED"}.get(out["process"], "NOT_STOCK")
        out.update(status=status,
                   why=f"DocClass {cls or '?'}（{out['decomposition'].get('class_rule') or ''}）→ {out['process']}："
                       f"{rule.get('why') or ''}")
        return _clean(out)
    if suffix in IMAGE_EXT:
        out.update(status="OCR_REQUIRED", why="影像檔：文字不在文字層，要 OCR 才拆得到")
        return _clean(out)
    if M.e394 is None:
        out.update(status="ENGINE_MISSING", why=M.errors.get("eng394", "ENG394 不在"))
        return _clean(out)
    try:
        if suffix == ".pdf":
            res = M.e394.restore_pdf(path, pages)
            texts = _page_texts(path)
        elif suffix in TEXT_EXT:
            text = _docx_text(path) if suffix == ".docx" else path.read_text(encoding="utf-8", errors="replace")
            res = M.e394.text_restore(text)
            res = {"pages": [dict(res, page=1, leaves=[])], "completeness": res.get("completeness"), "dedup": res.get("dedup")}
            texts = [text]
            out["why"] = "文字檔沒有版面座標：只有句子、扁平表與排除區，沒有左右上下切"
        else:
            out.update(status="UNSUPPORTED", why=f"{suffix} 不在 PDF / DOCX / TXT")
            return _clean(out)
    except Exception as error:  # noqa: BLE001
        out.update(status="ERROR", why=f"{error.__class__.__name__}: {error}"[:300])
        return _clean(out)
    out["pages"] = len(res.get("pages") or [])
    out["completeness"] = res.get("completeness") or {}
    for p in res.get("pages") or []:
        pno = p.get("page", 1)
        for leaf in p.get("leaves") or []:
            path_ = str(leaf.get("path") or "0")
            out["regions"].append({"page": pno, "path": path_, "zone": leaf.get("zone"), "where": leaf.get("where", ""),
                                   "category": leaf.get("category"), "bbox": list(leaf.get("bbox") or []),
                                   "left_right": "L" if "L" in path_ else ("R" if "R" in path_ else ""),
                                   "top_bottom": "T" if "T" in path_ else ("B" if "B" in path_ else ""),
                                   "band": (re.search(r"H(\d+)", path_) or [None, ""])[1]})
        for t in p.get("info") or []:
            out["tables"].append({"page": pno, "anchor": t.get("anchor"), "origin": t.get("origin"), "subcategory": t.get("subcategory", ""),
                                  "zone": t.get("zone"), "title": t.get("title", ""), "verdict": t.get("verdict"),
                                  "bbox": list(t.get("bbox") or []), "columns": t.get("columns"), "rows": t.get("rows"),
                                  "checks": t.get("checks", []), "issues": t.get("issues", []), "merged": t.get("merged", [])})
        for b in p.get("body") or []:
            out["sentences"].append({"page": pno, "no": b.get("no", ""), "sec_no": b.get("sec_no", ""), "title": b.get("title", ""),
                                     "subcategory": b.get("subcategory", ""), "anchor": b.get("anchor", ""), "text": b.get("text", ""),
                                     "recovered": 1 if b.get("recovered") else 0, "why": b.get("why", "")})
        for f in p.get("figures") or []:
            out["figures"].append({"page": pno, "anchor": f.get("anchor"), "bbox": list(f.get("bbox") or []), "verdict": f.get("verdict"),
                                   "note": f.get("note", "")})
        for e in p.get("excluded") or []:
            out["excluded"].append({"page": pno, "anchor": e.get("anchor"), "reason": e.get("reason", ""), "head": e.get("head", "")})
    out["rows"] = table_rows(M, name, out["tables"])
    out["checks"], out["conflicts"] = check_rows(M, out["rows"])
    out["entities"] = entities(M, texts, name)
    out["status"] = "OK"
    out["seconds"] = round(time.perf_counter() - started, 3)
    return _clean(out)


# [VRN-ID] VRN-ENG011-FNC030 · LOGIC
def entities(M, texts, name):
    full = "\n".join(texts)
    out = {}
    if M.e396 is not None:
        try:
            e = M.e396.analyze_text(full, Path(name).stem, texts)
            tp = dict(e.get("target_price") or {})
            tp["hits"] = [{k: h.get(k) for k in ("pattern", "prior", "current", "snippet")} for h in tp.get("hits") or []]
            out.update(company=e.get("identity"), mentions=e.get("mentions"), target_price=tp, valuation=e.get("valuation"),
                       notes=e.get("notes"))
        except Exception as error:  # noqa: BLE001
            out["error"] = f"ENG396 {error.__class__.__name__}: {error}"[:200]
    if M.matcher is not None:
        try:
            out["valuation_methods"] = sorted({h["id"] for h in M.matcher.match(full) if not h.get("context_required")})
        except Exception as error:  # noqa: BLE001
            out["valuation_methods_error"] = f"{error.__class__.__name__}: {error}"[:200]
    return out


# =====================================================================
# 6 . MANY FILES: WORKER PROCESSES DISPATCHED ON THE ACCELERATOR LANE
# =====================================================================
# [VRN-ID] VRN-ENG011-FNC031 · LOGIC
def _default_mapper(fn, items, action):
    with ThreadPoolExecutor(max_workers=max(1, min(8, len(items)))) as pool:
        return list(pool.map(fn, items))


# [VRN-ID] VRN-ENG011-FNC032 · LOGIC
def analyze_many(items, temp_dir=None, workers=None, mapper=None, timeout=1800, action="版面還原：子行程逐塊"):
    """[(path, name)] -> (results in input order, lane info).  Chunks run in worker processes (PyMuPDF is not thread-safe);
    the chunk dispatch goes through `mapper(fn, chunks, action)` -- the caller's accelerator lane."""
    items = [(str(p), n or Path(p).name) for p, n in items]
    started = time.perf_counter()
    if not items:
        return [], {"lane": "none", "items": 0, "seconds": 0.0}
    workers = workers or min(8, max(1, (os.cpu_count() or 2)))
    if len(items) < 3 or workers < 2 or os.environ.get("VRN_REGIONS_INPROC") == "1":
        results = [analyze(p, n) for p, n in items]
        return results, {"lane": "sequential", "items": len(items), "workers": 1, "seconds": round(time.perf_counter() - started, 3)}
    folder = Path(temp_dir or tempfile.mkdtemp(prefix="vrn_regions_"))
    folder.mkdir(parents=True, exist_ok=True)
    chunks = [list(range(i, len(items), workers)) for i in range(min(workers, len(items)))]

    # [VRN-ID] VRN-ENG011-FNC033 · LOGIC
    def run_chunk(index):
        idx = chunks[index]
        src = folder / f"regions_in_{index:02d}.json"
        dst = folder / f"regions_out_{index:02d}.jsonl"
        src.write_text(json.dumps([[i, items[i][0], items[i][1]] for i in idx], ensure_ascii=False), encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        try:
            done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "worker", "--input", str(src), "--output", str(dst)],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
            ok = done.returncode == 0 and dst.is_file()
            return {"index": index, "ok": ok, "out": str(dst), "err": (done.stderr or "")[-400:]}
        except Exception as error:  # noqa: BLE001
            return {"index": index, "ok": False, "out": str(dst), "err": f"{error.__class__.__name__}: {error}"}

    status = (mapper or _default_mapper)(run_chunk, list(range(len(chunks))), action)
    results = [None] * len(items)
    failed = []
    for st in status:
        if st.get("ok"):
            for line in Path(st["out"]).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    results[rec["index"]] = rec["result"]
        else:
            failed.append(st)
    for i, r in enumerate(results):                       # a chunk that failed is redone here, never dropped
        if r is None:
            results[i] = analyze(items[i][0], items[i][1])
    return results, {"lane": "worker_process", "items": len(items), "workers": len(chunks), "failed_chunks": len(failed),
                     "seconds": round(time.perf_counter() - started, 3), "temp": str(folder),
                     "why": "PyMuPDF 不能多執行緒共用：每塊一個子行程，逐塊由加速器派工"}


# [VRN-ID] VRN-ENG011-FNC034 · LOGIC
def _worker(args):
    jobs = json.loads(Path(args.input).read_text(encoding="utf-8"))
    with open(args.output, "w", encoding="utf-8") as handle:
        for index, path, name in jobs:
            try:
                result = analyze(path, name)
            except Exception as error:  # noqa: BLE001
                result = {"file": name, "status": "ERROR", "why": f"{error.__class__.__name__}: {error}"[:300]}
            handle.write(json.dumps({"index": index, "result": result}, ensure_ascii=False) + "\n")
    return 0


# =====================================================================
# 7 . THE DATABASE
# =====================================================================
SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (file TEXT PRIMARY KEY, status TEXT, why TEXT, doc_class TEXT, doc_class_zh TEXT, class_rule TEXT,
  class_confidence REAL, ticker TEXT, broker_raw TEXT, report_date TEXT, company_names TEXT, pages INTEGER, regions INTEGER,
  tables INTEGER, rows INTEGER, checks_pass INTEGER, checks_fail INTEGER, checks_warn INTEGER, captured_min REAL,
  tp_current REAL, tp_prior REAL, tp_direction TEXT, valuation_methods TEXT, valuation_checks TEXT);
CREATE TABLE IF NOT EXISTS regions (file TEXT, seq INTEGER, page INTEGER, path TEXT, zone TEXT, where_ TEXT, category TEXT, left_right TEXT,
  top_bottom TEXT, band TEXT, x0 REAL, y0 REAL, x1 REAL, y1 REAL);
CREATE TABLE IF NOT EXISTS tables_ (file TEXT, seq INTEGER, page INTEGER, anchor TEXT, origin TEXT, subcategory TEXT, zone TEXT, title TEXT,
  verdict TEXT, n_rows INTEGER, n_cols INTEGER, columns TEXT, cells TEXT, checks TEXT, issues TEXT);
CREATE TABLE IF NOT EXISTS rows_ (file TEXT, seq INTEGER, page INTEGER, anchor TEXT, metric_raw TEXT, metric TEXT, block TEXT, period_raw TEXT,
  period TEXT, kind TEXT, value REAL, printed TEXT, unit TEXT);
CREATE TABLE IF NOT EXISTS checks (file TEXT, period TEXT, id TEXT, zh TEXT, state TEXT, lhs REAL, rhs REAL, diff REAL, tol REAL,
  detail TEXT, used TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS sentences (file TEXT, page INTEGER, no TEXT, sec_no TEXT, title TEXT, subcategory TEXT, anchor TEXT, text TEXT,
  recovered INTEGER);
CREATE TABLE IF NOT EXISTS entities (file TEXT, seq INTEGER, kind TEXT, key TEXT, value TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS excluded (file TEXT, seq INTEGER, page INTEGER, anchor TEXT, reason TEXT, head TEXT);
CREATE TABLE IF NOT EXISTS completeness (file TEXT, page INTEGER, src_chars INTEGER, captured REAL, extracted REAL, missing_chars INTEGER,
  state TEXT, missing_text TEXT, recovered_lines INTEGER);
"""


# [VRN-ID] VRN-ENG011-FNC035 · IO
def write_db(results, db_path):
    """All results into one SQLite file (rebuilt each run); returns the row counts per table."""
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(str(db_path))
    try:
        con.executescript(SCHEMA)
        for r in results:
            d = r.get("decomposition") or {}
            states = [c.get("state") for c in r.get("checks") or []]
            tp = (r.get("entities") or {}).get("target_price") or {}
            caps = [p.get("captured") for p in (r.get("completeness") or {}).get("pages") or [] if p.get("captured") is not None]
            vals = (r.get("entities") or {}).get("valuation") or []
            con.execute("INSERT OR REPLACE INTO reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                r.get("file"), r.get("status"), r.get("why"), d.get("doc_class"), d.get("doc_class_zh"), d.get("class_rule"),
                d.get("class_confidence"), d.get("ticker"), d.get("broker_raw"), d.get("report_date"),
                "、".join(d.get("company_names") or []), r.get("pages"), len(r.get("regions") or []), len(r.get("tables") or []),
                len(r.get("rows") or []), states.count("PASS"), states.count("FAIL"), states.count("WARN"), min(caps) if caps else None,
                tp.get("current"), tp.get("prior"), tp.get("direction"),
                ",".join((r.get("entities") or {}).get("valuation_methods") or []),
                "; ".join(f"{v.get('method')} {v.get('multiple')}x {v.get('metric')} {v.get('metric_value')} -> {v.get('implied_tp')} {v.get('check')}"
                          for v in vals if isinstance(v, dict) and v.get("method"))))
            f = r.get("file")
            con.executemany("INSERT INTO regions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                (f, i, g.get("page"), g.get("path"), g.get("zone"), g.get("where"), g.get("category"), g.get("left_right"), g.get("top_bottom"),
                 g.get("band"), *((list(g.get("bbox") or []) + [None] * 4)[:4])) for i, g in enumerate(r.get("regions") or [], 1)])
            con.executemany("INSERT INTO tables_ VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                (f, i, t.get("page"), t.get("anchor"), t.get("origin"), t.get("subcategory"), t.get("zone"), t.get("title"), t.get("verdict"),
                 len(t.get("rows") or []), len(t.get("columns") or []), json.dumps(t.get("columns"), ensure_ascii=False),
                 json.dumps(t.get("rows"), ensure_ascii=False), json.dumps(t.get("checks"), ensure_ascii=False),
                 json.dumps(t.get("issues"), ensure_ascii=False)) for i, t in enumerate(r.get("tables") or [], 1)])
            con.executemany("INSERT INTO rows_ VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                (f, i, w.get("page"), w.get("anchor"), w.get("metric_raw"), w.get("metric"), w.get("block"), w.get("period_raw"), w.get("period"),
                 w.get("kind"), w.get("value"), w.get("printed"), w.get("unit")) for i, w in enumerate(r.get("rows") or [], 1)])
            con.executemany("INSERT INTO checks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
                (f, c.get("period"), c.get("id"), c.get("zh"), c.get("state"), c.get("lhs"), c.get("rhs"), c.get("diff"), c.get("tol"),
                 c.get("detail"), json.dumps(c.get("used"), ensure_ascii=False), c.get("source")) for c in r.get("checks") or []])
            con.executemany("INSERT INTO sentences VALUES (?,?,?,?,?,?,?,?,?)", [
                (f, s.get("page"), s.get("no"), s.get("sec_no"), s.get("title"), s.get("subcategory"), s.get("anchor"), s.get("text"),
                 int(s.get("recovered") or 0)) for s in r.get("sentences") or []])
            ent = r.get("entities") or {}
            erows = [(f, "company_name", n.get("lang", ""), n.get("name"), " / ".join(n.get("forms") or []))
                     for n in ((ent.get("company") or {}).get("names") or []) if isinstance(n, dict)]
            erows += [(f, "target_price", k, None if tp.get(k) is None else str(tp.get(k)), "") for k in ("current", "prior", "direction", "change_pct")
                      if tp.get(k) is not None]
            erows += [(f, "valuation", v.get("method"), None if v.get("implied_tp") is None else str(v.get("implied_tp")),
                       f"{v.get('check')} · {v.get('sentence', '')[:120]}") for v in vals if isinstance(v, dict) and v.get("method")]
            erows += [(f, "valuation_method", m, m, "") for m in ent.get("valuation_methods") or []]
            con.executemany("INSERT INTO entities VALUES (?,?,?,?,?,?)", [(e[0], i, *e[1:]) for i, e in enumerate(erows, 1)])
            con.executemany("INSERT INTO excluded VALUES (?,?,?,?,?,?)", [
                (f, i, e.get("page"), e.get("anchor"), e.get("reason"), e.get("head")) for i, e in enumerate(r.get("excluded") or [], 1)])
            con.executemany("INSERT INTO completeness VALUES (?,?,?,?,?,?,?,?,?)", [
                (f, c.get("page"), c.get("src_chars"), c.get("captured"), c.get("extracted"), c.get("missing_chars"), c.get("state"),
                 " ‖ ".join(str(s.get("text", "")) for s in c.get("segments") or []), int(c.get("recovered_lines") or 0))
                for c in (r.get("completeness") or {}).get("pages") or []])
        con.commit()
        counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ("reports", "regions", "tables_", "rows_", "checks", "sentences", "entities", "excluded", "completeness")}
    finally:
        con.close()
    return counts


# =====================================================================
# 8 . FIXTURES WITH KNOWN ANSWERS (used by the self-test, G15 and the tests)
# =====================================================================
FIX_IS = {"營業收入": (1000.0, 1200.0, 1500.0), "營業成本": (600.0, 696.0, 840.0), "營業毛利": (400.0, 504.0, 660.0),
          "營業費用": (150.0, 180.0, 210.0), "營業利益": (250.0, 324.0, 450.0), "稅後淨利": (200.0, 260.0, 360.0),
          "毛利率(%)": (40.0, 42.0, 44.0), "營業利益率(%)": (25.0, 27.0, 30.0), "每股盈餘(元)": (8.0, 10.4, 14.4)}
FIX_BS = {"流動資產": (900.0, 1000.0, 1200.0), "非流動資產": (1100.0, 1300.0, 1500.0), "資產總額": (2000.0, 2300.0, 2700.0),
          "流動負債": (500.0, 550.0, 600.0), "非流動負債": (300.0, 350.0, 400.0), "負債總額": (800.0, 900.0, 1000.0),
          "權益總額": (1200.0, 1400.0, 1700.0), "流通在外股數(百萬股)": (25.0, 25.0, 25.0)}
FIX_CF = {"營業活動之淨現金流入": (300.0, 360.0, 450.0), "資本支出": (-120.0, -150.0, -170.0), "自由現金流量": (180.0, 210.0, 280.0)}
FIX_YEARS = ("2024A", "2025E", "2026E")
FIX_KEYS = {"營業收入": "revenue", "營業成本": "cogs", "營業毛利": "gross_profit", "營業費用": "opex", "營業利益": "operating_income",
            "稅後淨利": "net_income", "毛利率(%)": "gross_margin", "營業利益率(%)": "op_margin", "每股盈餘(元)": "basic_eps",
            "流動資產": "current_assets", "非流動資產": "noncurrent_assets", "資產總額": "assets", "流動負債": "current_liab",
            "非流動負債": "noncurrent_liab", "負債總額": "liabilities", "權益總額": "equity_total", "流通在外股數(百萬股)": "shares",
            "營業活動之淨現金流入": "cfo", "資本支出": "capex", "自由現金流量": "fcf"}
FIX_PASS = ("GP_SUB", "OP_SUB", "GM_DIV", "OPM_DIV", "BS_ADD", "BS_ASSETS", "BS_LIAB", "EPS_DIV", "FCF_ADD")


# [VRN-ID] VRN-ENG011-FNC036 · LOGIC
def _fmt(v):
    return f"{v:,.1f}" if abs(v - round(v)) > 1e-9 else f"{v:,.0f}"


# [VRN-ID] VRN-ENG011-FNC037 · LOGIC
def _grid(page, fitz, x0, top, widths, rows, size=8.5, row_h=17.0):
    for r_i, row in enumerate(rows):
        x = x0
        for c_i, cell in enumerate(row):
            rect = fitz.Rect(x, top + r_i * row_h, x + widths[c_i], top + (r_i + 1) * row_h)
            page.draw_rect(rect, color=(0, 0, 0), width=0.6)
            page.insert_text((x + 3, top + r_i * row_h + 12), str(cell), fontname="china-t", fontsize=size)
            x += widths[c_i]
    return top + len(rows) * row_h


# [VRN-ID] VRN-ENG011-FNC038 · BUILD
def build_fixtures(folder):
    """Four reports with known answers -> [truth].  Needs PyMuPDF (fitz); returns [] without it."""
    try:
        import fitz  # type: ignore
    except Exception:  # noqa: BLE001
        return []
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    truths = []
    # F1 first page: header band, body on the left, the info card on the right, small disclaimer at the bottom
    name = "凱基_2330台積電_20260901_公司更新.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 40), "凱基證券投資顧問 KGI Securities Research    2026/09/01    Taiwan Equity Research", fontname="china-t", fontsize=8)
    page.insert_text((40, 80), "台積電(2330 TT)  先進製程需求強勁", fontname="china-t", fontsize=18)
    body = ["我們將目標價由 NT$1,000 上調至 NT$1,200，以 20x 2026E EPS 60 元評價。",
            "先進製程與先進封裝需求延續，2026 年營收成長動能明確。",
            "毛利率可望維持在高檔，主要受惠產品組合改善與產能利用率提升。",
            "風險：匯率波動、終端需求不如預期與地緣政治。"]
    y = 120.0
    for line in body:
        page.insert_text((40, y), line, fontname="china-t", fontsize=10)
        y += 22
    card = ["評等：買進", "目標價：NT$1,200", "收盤價：NT$1,000", "分析師：王小明", "Tel: (02)2181-8888", "xiaoming.wang@kgi.com"]
    y = 120.0
    for line in card:
        page.insert_text((440, y), line, fontname="china-t", fontsize=8)
        y += 16
    page.insert_text((40, 815), "本報告僅供參考，不構成投資建議。免責聲明：請參閱報告末頁之重要聲明與分析師聲明。", fontname="china-t", fontsize=6)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "kind": "first_page", "doc_class": "STOCK", "ticker": "2330", "info_right": True,
                   "tp_current": 1200.0, "tp_prior": 1000.0, "valuation": "VAL_PE", "valuation_check": "VERIFIED"})
    # F2 annual financial page: income statement left, balance sheet right, cash flow below across the page
    name = "凱基_2330台積電_20260902_財務預估.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 50), "台積電(2330 TT)  財務預估", fontname="china-t", fontsize=14)
    head = ["項目", *FIX_YEARS]
    left = [["損益表(NT$百萬元)", *FIX_YEARS]] + [[k, *(_fmt(v) for v in vs)] for k, vs in FIX_IS.items()]
    right = [["資產負債表(百萬元)", *FIX_YEARS]] + [[k, *(_fmt(v) for v in vs)] for k, vs in FIX_BS.items()]
    bottom_left = _grid(page, fitz, 40, 80, [100, 50, 50, 50], left)
    bottom_right = _grid(page, fitz, 315, 80, [110, 45, 45, 45], right)
    cf = [["現金流量表(NT$百萬元)", *FIX_YEARS]] + [[k, *(_fmt(v) for v in vs)] for k, vs in FIX_CF.items()]
    _grid(page, fitz, 40, max(bottom_left, bottom_right) + 40, [250, 80, 80, 80], cf)
    doc.save(str(folder / name))
    doc.close()
    values = {}
    for table in (FIX_IS, FIX_BS, FIX_CF):
        for label, vs in table.items():
            for year, v in zip(FIX_YEARS, vs):
                values[f"{FIX_KEYS[label]}@{year[:4]}"] = v
    truths.append({"file": name, "kind": "annual", "doc_class": "STOCK", "ticker": "2330", "values": values, "pass": list(FIX_PASS),
                   "split_lr": True, "split_tb": True, "head": head})
    # F3 a chart on top, a table under it
    name = "凱基_2330台積電_20260903_營收趨勢.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 50), "圖一：台積電季營收趨勢（NT$十億元）", fontname="china-t", fontsize=10)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 240, 120), False)
    pix.clear_with(235)
    for i, h in enumerate((40, 60, 75, 95, 110)):
        pix.set_rect(fitz.IRect(15 + i * 45, 120 - h, 45 + i * 45, 120), (40, 90, 160))
    page.insert_image(fitz.Rect(40, 60, 520, 300), pixmap=pix)
    rows = [["季營收(NT$十億元)", "1Q26", "2Q26", "3Q26", "4Q26", "2026"], ["營業收入", "800", "900", "950", "1,050", "3,700"]]
    _grid(page, fitz, 40, 340, [150, 70, 70, 70, 70, 70], rows)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "kind": "chart", "doc_class": "STOCK", "ticker": "2330", "figure_above_table": True,
                   "values": {"revenue@2026Q1": 800.0, "revenue@2026Q4": 1050.0, "revenue@2026": 3700.0}, "pass": ["ANNUAL_SUM:revenue"]})
    # F4 an industry report: listed with the reason, not taken apart
    name = "元大_半導體產業_20260901_產業報告.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 60), "半導體產業：先進製程需求延續", fontname="china-t", fontsize=16)
    doc.save(str(folder / name))
    doc.close()
    truths.append({"file": name, "kind": "not_stock", "doc_class": "INDUSTRY_OUTLOOK"})
    return truths


# [VRN-ID] VRN-ENG011-FNC039 · VALIDATE
def check_fixture(result, truth):
    """[(item, ok, detail)] for one fixture."""
    out = []
    d = result.get("decomposition") or {}
    out.append((f"{truth['file']} 類別", d.get("doc_class") == truth["doc_class"], f"{d.get('doc_class')} vs {truth['doc_class']}"))
    if truth["kind"] == "not_stock":
        # 2026-10-15：非個股不再一律 NOT_STOCK，改成依 doc_class_policy 走 COVERAGE／REGISTER。
        # 這一案要守的是「不照個股那一套拆」，所以判準是「狀態不是 FULL 的那條路」。
        expect = {"COVERAGE", "REGISTERED", "NOT_STOCK"}
        out.append((f"{truth['file']} 不照個股拆", result.get("status") in expect, result.get("status", "")))
        return out
    out.append((f"{truth['file']} 代號", d.get("ticker") == truth.get("ticker"), str(d.get("ticker"))))
    out.append((f"{truth['file']} 還原", result.get("status") == "OK", result.get("why", "") or result.get("status", "")))
    caps = [p.get("captured") for p in (result.get("completeness") or {}).get("pages") or []]
    out.append((f"{truth['file']} 截取完整 ≥ 99.9%", bool(caps) and min(caps) >= 99.9, str(caps)))
    regions = result.get("regions") or []
    if truth.get("info_right"):
        hit = [g for g in regions if g.get("zone") == "INFO" and g.get("where") == "右"]
        out.append((f"{truth['file']} 首頁右側資訊區", bool(hit), f"{len(hit)} 區"))
    if truth.get("split_lr"):
        lr = {g.get("left_right") for g in regions if g.get("category") == "table"}
        out.append((f"{truth['file']} 表格左右對切", {"L", "R"} <= lr, str(sorted(x for x in lr if x))))
    if truth.get("split_tb"):
        tops = sorted({round(g["bbox"][1]) for g in regions if g.get("category") == "table" and g.get("bbox")})
        out.append((f"{truth['file']} 表格上下切", len(tops) >= 2, str(tops)))
    if truth.get("figure_above_table"):
        figs = [g for g in regions if g.get("zone") == "FIGURE" and g.get("bbox")]
        tabs = [g for g in regions if g.get("category") == "table" and g.get("bbox")]
        ok = bool(figs and tabs and max(f["bbox"][3] for f in figs) <= min(t["bbox"][1] for t in tabs) + 1)
        out.append((f"{truth['file']} 圖在上、表在下", ok, f"圖 {len(figs)} · 表 {len(tabs)}"))
    got = {f"{w.get('metric')}@{w.get('period')}": w.get("value") for w in result.get("rows") or [] if w.get("metric")}
    for key, want in (truth.get("values") or {}).items():
        out.append((f"{truth['file']} {key}", got.get(key) is not None and abs(got[key] - want) < 1e-6, f"{got.get(key)} vs {want}"))
    states = {}
    for c in result.get("checks") or []:
        states.setdefault(c.get("id"), []).append(c.get("state"))
    for ident in truth.get("pass") or []:
        st = states.get(ident) or []
        out.append((f"{truth['file']} 驗算 {ident}", bool(st) and all(s == "PASS" for s in st), "/".join(st) or "沒有算到"))
    if truth.get("tp_current") is not None:
        tp = (result.get("entities") or {}).get("target_price") or {}
        out.append((f"{truth['file']} 目標價 前 → 今", (tp.get("prior"), tp.get("current")) == (truth["tp_prior"], truth["tp_current"]),
                    f"{tp.get('prior')} → {tp.get('current')}"))
    if truth.get("valuation"):
        vals = (result.get("entities") or {}).get("valuation") or []
        hit = [v for v in vals if v.get("method") == truth["valuation"] and v.get("check") == truth["valuation_check"]]
        out.append((f"{truth['file']} 評價法 {truth['valuation']} 倍數×指標=目標價", bool(hit), "; ".join(f"{v.get('method')} {v.get('check')}" for v in vals)))
    return out


# =====================================================================
# 9 . SELF-TEST AND CLI
# =====================================================================
# [VRN-ID] VRN-ENG011-FNC040 · ENTRY
def selftest(workers=None):
    M = mother()
    print(f"[REGIONS] VRN_PageRegions {PAGE_REGIONS_VERSION} · 母倉引擎 {len(M.describe()['engines'])}/{len(MOTHER_FILES)} · 冊 "
          f"{len(M.describe()['books'])}/{len(BOOK_FILES)}")
    for key, why in M.errors.items():
        print(f"  [FAIL] {key}: {why}")
    if M.errors:
        return 1
    with tempfile.TemporaryDirectory(prefix="vrn_regions_selftest_") as tmp:
        truths = build_fixtures(Path(tmp) / "fixtures")
        if not truths:
            print("  [SKIP] PyMuPDF 沒有安裝：pip install pymupdf（安裝是操作員的手）")
            return 0
        results, lane = analyze_many([(Path(tmp) / "fixtures" / t["file"], t["file"]) for t in truths], temp_dir=Path(tmp) / "work",
                                     workers=workers)
        checks = [c for r, t in zip(results, truths) for c in check_fixture(r, t)]
        counts = write_db(results, Path(tmp) / DB_NAME)
    for item, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {item}" + ("" if ok else f" · {detail}"))
    failed = sum(1 for _i, ok, _d in checks if not ok)
    print(f"[REGIONS] {len(checks) - failed}/{len(checks)} · 道 {lane['lane']} · 資料庫 " + " · ".join(f"{k} {v}" for k, v in counts.items()))
    return 1 if failed else 0


# [VRN-ID] VRN-ENG011-FNC041 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(description="VRN PageRegions: stock reports -> regions, tables, rows, checks, entities, SQLite")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("selftest")
    run = sub.add_parser("run")
    run.add_argument("paths", nargs="+")
    run.add_argument("--out", required=True)
    work = sub.add_parser("worker")
    work.add_argument("--input", required=True)
    work.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.command == "worker":
        return _worker(args)
    if args.command == "run":
        files = []
        for p in args.paths:
            p = Path(p)
            files += sorted(q for q in p.rglob("*") if q.is_file()) if p.is_dir() else [p]
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        results, lane = analyze_many([(f, f.name) for f in files], temp_dir=out / "work")
        counts = write_db(results, out / DB_NAME)
        print(json.dumps({"lane": lane, "db": str(out / DB_NAME), "counts": counts}, ensure_ascii=False, indent=1))
        return 0
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
