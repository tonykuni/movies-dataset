#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG017 · VRN_TickerRecord_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 3 · 函式 38；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_TickerRecord v0100 -- the 4-digit code as the key: one record of 15 fields per stock report, and the one merged book
behind them.

Operator 2026-10-12:
  「用四碼代號去資料庫找到 YFINANCE TICKER / BLOOMBERG TICKER / NAME / ENGLISH NAME / BROKER / ANALYST / TITLE / EMAIL / TEL /
    RATING / TARGET PRICE(ADJ.) / TARGET PRICE(ORIGINAL) / ADJ CLOSE / ADJ CLOSE BEFORE REPORT DATE / UPSIDE %
    相關邏輯及 SSOT 同義字 REGEX 在一次跨不同專案整合去重不衝突整合一次完善一次」

Two things, nothing else:
  1. the book   ssot/VRN_TickerRecord_SSOT_v0100.json, built from every alias / label / regex book this repository holds
                (the VRN dictionaries, the mother-repo copies, the synonym union, the operator's labels, the S05 field registry,
                the field rules, the contact regexes, the TitleTrim book, the REGEX book): one entry per alias with the books it
                came from, duplicates folded (case-folded), a conflict listed whenever two books send the same alias to different
                canonicals -- shown, never resolved here (the operator rules; only_add).  `build-book` writes it; the selftest
                fails when the file on disk is older than what the books would give.
  2. the record one row per stock report: the 15 fields with value, state and source.  Nothing is read again from the report:
                the TitleTrim parts (two independent readers agree = VERIFIED), the first-page engine (platform codes, company
                name), the database engine's row with the local-DB columns (NAME, ADJ CLOSE, adjusted target, upside), and the
                local DB's listing for the code (yfinance ticker, market).  Bloomberg is `<code> TT` when the page does not
                print it (marked derived).  `lookup CODE` answers the DB part for a bare code.

The engines' judgement is unchanged.  No network, LIVE off, no consent variable read or set, nothing installed.
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
import csv
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import time
from collections import Counter, OrderedDict
from pathlib import Path

RECORD_VERSION = "v0100"
HERE = Path(__file__).resolve().parent
VRN_ROOT = HERE.parent
BOOK_PATH = VRN_ROOT / "ssot" / "VRN_TickerRecord_SSOT_v0100.json"
TABLE_NAME = "vrn_ticker_record"

# the 15 fields, in the operator's order; (key, zh, where the value comes from, in order of trust)
FIELDS = [
    ("ticker", "代號", "標題＋檔名＋首頁三平台碼（G17 title.ticker）"),
    ("yfinance_ticker", "YF 代號", "本機資料庫 tw_listings 的 yf_ticker → 首頁印的 .TW/.TWO 碼 → 市場推（上市 .TW、上櫃 .TWO）"),
    ("bloomberg_ticker", "Bloomberg 代號", "首頁印的「<代號> TT」→ 推（<代號> TT）"),
    ("name", "公司名", "本機資料庫 NAME（NameDB）→ 標題／首頁的中文公司名 → 檔名"),
    ("english_name", "英文名", "本機資料庫的英文名欄（有就取）→ 標題／首頁印的英文公司名（都沒有就 NOT_PRINTED）"),
    ("broker", "券商", "G17 cover.broker（首頁＋檔名＋首頁引擎＋e-mail 網域）"),
    ("analyst", "分析師", "G17 cover.analyst（首頁全部，分析師區先）"),
    ("title", "標題", "G17 title.text（TRIM 後；首頁引擎最大字作第二讀法）"),
    ("email", "E-mail", "G17 cover.email"),
    ("tel", "電話", "G17 cover.tel（主號碼；比後 8 碼）"),
    ("rating", "評等", "G17 cover.rating（照原文；同義字只用來比對同級，不分類）"),
    ("target_price_original", "目標價（原）", "G17 cover.target_price（首頁＋首頁引擎＋ENG396＋現價×(1+上漲空間)）"),
    ("target_price_adj", "目標價（調整）", "本機資料庫：目標價 × 報告日調整係數 ÷ 最新調整係數（TargetPriceAdj）"),
    ("adj_close", "ADJ CLOSE", "本機資料庫最新一日 adj_close（AdjCloseLatest · AdjCloseLatestDate）"),
    ("adj_close_before_report", "ADJ CLOSE（報告日前）", "本機資料庫報告日之前最後一個交易日（AdjCloseReport · AdjCloseReportDate）"),
    ("upside_pct", "上漲空間 %", "首頁印的（cover.upside）；另列 VRN 重算 (目標價−現價)/現價 與資料庫調整後（UpsideAdjPct）"),
]
RATING_COARSE = {"strong_buy": "BUY", "buy": "BUY", "hold": "HOLD", "neutral": "HOLD", "sell": "SELL", "strong_sell": "SELL",
                 "reduce": "SELL", "not_rated": "NOT_RATED", "nr": "NOT_RATED"}
PRIOR_CORE_WORDS = ["from", "previous", "prior", "old", "前次", "原先", "前一次", "上次", "upside to", "downside to"]   # VRN_Evidence_Core._TP_EXCLUDE_BEFORE


# [VRN-ID] VRN-ENG017-FNC001 · IO
def read_json_file(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


# [VRN-ID] VRN-ENG017-FNC002 · LOGIC
def file_sha256(path):
    """CRLF is normalised first (round 5: a Windows checkout gave every source book another hash and called the book stale)."""
    try:
        return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    except Exception:  # noqa: BLE001
        return ""


# [VRN-ID] VRN-ENG017-FNC003 · LOGIC
def fold_text(text):
    return re.sub(r"\s+", " ", str(text or "").strip()).casefold()


# =====================================================================
# 1 . THE MERGED BOOK
# =====================================================================
SOURCE_BOOKS = OrderedDict([
    ("broker_v0100", "ssot/VRN_Broker_Dict_v0100.json"),
    ("broker_v0103", "ssot/VRN_Broker_Dict_v0103.json"),
    ("broker_list", "registry/VRN_BROKER_LIST_v01.json"),
    ("synonym_union", "ssot/VIA_SSOT_SynonymUnion_v0107.json"),
    ("synonym_library_v4", "knowledge/SYNONYM_LIBRARY_v4.json"),
    ("synonym_ssot", "ssot/VRN_SYNONYM_SSOT_v0100.json"),
    ("operator_labels", "ssot/VRN_OperatorLabels_SSOT_v0100.json"),
    ("rating_dict", "ssot/VRN_Rating_Dict_v0100.json"),
    ("s05", "ssot/VRN_S05_FieldRegistry_v0103.json"),
    ("field_rules", "ssot/VRN_FieldRules_SSOT_v0101.json"),
    ("report_field_rules", "ssot/VIA_VRN_ReportFieldRules_SSOT_v0101.json"),
    ("contact_regex", "ssot/VRN_Contact_Regex_v0100.json"),
    ("titletrim", "ssot/VRN_TitleTrim_SSOT_v0100.json"),
    ("regex_ssot", "ssot/VRN_REGEX_SSOT_v0100.json"),
    ("ticker_master", "engine/VIA_TW_Ticker_Master_v0210.py"),
])


# [VRN-ID] VRN-ENG017-CLS001 · CLASS
class AliasTable:
    """alias -> canonical, with every book that said so; the same alias sent to two canonicals is a conflict (kept, shown)."""

    # [VRN-ID] VRN-ENG017-FNC004 · INIT
    def __init__(self, name):
        self.name = name
        self.items = OrderedDict()
        self.n_in = 0

    # [VRN-ID] VRN-ENG017-FNC005 · LOGIC
    def add(self, alias, canonical, book, note=""):
        alias = str(alias or "").strip()
        canonical = str(canonical or "").strip()
        if not alias or not canonical:
            return
        self.n_in += 1
        key = fold_text(alias)
        it = self.items.setdefault(key, {"alias": alias, "canonicals": OrderedDict()})
        c = it["canonicals"].setdefault(canonical, [])
        src = book + (f"#{note}" if note else "")
        if src not in c:
            c.append(src)

    # [VRN-ID] VRN-ENG017-FNC006 · LOGIC
    def result(self):
        entries, conflicts = OrderedDict(), []
        for key, it in sorted(self.items.items()):
            canon = list(it["canonicals"].keys())
            entries[it["alias"]] = {"canonical": canon[0] if len(canon) == 1 else canon,
                                    "from": sorted({s for lst in it["canonicals"].values() for s in lst})}
            if len(canon) > 1:
                conflicts.append({"alias": it["alias"], "canonicals": {c: srcs for c, srcs in it["canonicals"].items()},
                                  "rule": "兩本冊給不同正典：照列，不裁定（操作員裁；only_add）"})
        return {"count": len(entries), "aliases_in": self.n_in, "duplicates_folded": self.n_in - len(entries), "entries": entries,
                "conflicts": conflicts}


# [VRN-ID] VRN-ENG017-CLS002 · CLASS
class TermTable:
    """A flat list of label words with provenance (no canonical): labels, prior words, titles."""

    # [VRN-ID] VRN-ENG017-FNC007 · INIT
    def __init__(self):
        self.items = OrderedDict()
        self.n_in = 0

    # [VRN-ID] VRN-ENG017-FNC008 · LOGIC
    def add(self, term, book):
        term = str(term or "").strip()
        if not term:
            return
        self.n_in += 1
        it = self.items.setdefault(fold_text(term), {"term": term, "from": []})
        if book not in it["from"]:
            it["from"].append(book)

    # [VRN-ID] VRN-ENG017-FNC009 · LOGIC
    def result(self):
        return {"count": len(self.items), "terms_in": self.n_in, "duplicates_folded": self.n_in - len(self.items),
                "terms": OrderedDict((v["term"], v["from"]) for _k, v in sorted(self.items.items()))}


# [VRN-ID] VRN-ENG017-CLS003 · CLASS
class RegexTable:
    """Patterns with provenance, folded on the exact pattern string; every one compiles or is listed as broken."""

    # [VRN-ID] VRN-ENG017-FNC010 · INIT
    def __init__(self):
        self.items = OrderedDict()
        self.n_in = 0

    # [VRN-ID] VRN-ENG017-FNC011 · LOGIC
    def add(self, pattern, book, name=""):
        pattern = str(pattern or "")
        if not pattern:
            return
        self.n_in += 1
        it = self.items.setdefault(pattern, {"pattern": pattern, "from": [], "compiles": True})
        src = book + (f"#{name}" if name else "")
        if src not in it["from"]:
            it["from"].append(src)
        try:
            re.compile(pattern)
        except re.error:
            it["compiles"] = False

    # [VRN-ID] VRN-ENG017-FNC012 · LOGIC
    def result(self):
        return {"count": len(self.items), "patterns_in": self.n_in, "duplicates_folded": self.n_in - len(self.items),
                "broken": [p for p, v in self.items.items() if not v["compiles"]], "patterns": list(self.items.values())}


# [VRN-ID] VRN-ENG017-FNC013 · LOGIC
def broker_canon_map(books):
    """Canonical broker keys = Broker_Dict v0103 keys (what the first-page engine answers).  -> {fold_text(name): KEY}."""
    out = {}
    v3 = (books.get("broker_v0103") or {}).get("brokers") or {}
    for key, b in v3.items():
        out[fold_text(key)] = key
        for a in [b.get("abbr"), b.get("chinese_name"), b.get("english_name"), *(b.get("aliases") or [])]:
            if a:
                out.setdefault(fold_text(a), key)
    return out


# [VRN-ID] VRN-ENG017-FNC014 · LOGIC
def merge_broker(books, canon):
    """Every broker alias in every book -> the v0103 canonical key where the book's own key can be mapped, else the book's key."""
    m = AliasTable("broker")
    dom = AliasTable("email_domain")
    su = books.get("synonym_union") or {}
    key_alias = {fold_text(k): v.get("canonical") for k, v in (su.get("key_alias") or {}).items() if isinstance(v, dict) and v.get("canonical")}

    # [VRN-ID] VRN-ENG017-FNC015 · LOGIC
    def to_key(name):
        """A book's own key -> the canonical key: the v0103 key when the name is one of its aliases, else the synonym union's
        key ruling (MEGABANK -> MEGA, DAIWA SECURITIES -> DAIWA: a ruling in a source book, not one made here), else as given."""
        f = fold_text(name)
        if f in canon:
            return canon[f]
        if f in key_alias and fold_text(key_alias[f]) != f:
            return to_key(key_alias[f])
        return str(name).strip().upper()
    v0 = books.get("broker_v0100") or {}
    for zh, b in (v0.get("brokers") or {}).items():
        key = canon.get(fold_text(zh)) or canon.get(fold_text(b.get("abbr"))) or str(b.get("abbr") or zh).upper()
        for a in [zh, b.get("abbr"), *(b.get("aliases") or [])]:
            m.add(a, key, "VRN_Broker_Dict_v0100.json", "brokers")
        if b.get("abbr") and canon.get(fold_text(zh)) and fold_text(b["abbr"]) != fold_text(canon[fold_text(zh)]):
            m.add(b["abbr"], key, "VRN_Broker_Dict_v0100.json", f"abbr {b['abbr']} ≠ v0103 鍵 {key}（別名，不是正典）")
    for b in v0.get("brokers_extended") or []:
        for a in [b.get("code"), b.get("en"), b.get("zh"), *(b.get("aliases") or [])]:
            m.add(a, to_key(b.get("code")), "VRN_Broker_Dict_v0100.json", "brokers_extended")
    for key, b in ((books.get("broker_v0103") or {}).get("brokers") or {}).items():
        for a in [key, b.get("abbr"), b.get("chinese_name"), b.get("english_name"), *(b.get("aliases") or [])]:
            if a and "." in str(a) and " " not in str(a):
                dom.add(a, key, "VRN_Broker_Dict_v0103.json", "aliases(網域)")
            else:
                m.add(a, key, "VRN_Broker_Dict_v0103.json")
    for b in ((books.get("broker_list") or {}).get("brokers") or []):
        key = to_key(b.get("canonical_en") or b.get("canonical"))
        for a in [b.get("canonical"), b.get("canonical_en"), *(b.get("aliases") or [])]:
            m.add(a, key, "registry/VRN_BROKER_LIST_v01.json")
    for alias, it in (su.get("key_alias") or {}).items():
        if isinstance(it, dict) and it.get("canonical"):
            m.add(alias, to_key(it["canonical"]), "VIA_SSOT_SynonymUnion_v0107.json", "key_alias")
    for raw, lst in (((books.get("synonym_library_v4") or {}).get("scopes") or {}).get("broker") or {}).items():
        for it in lst if isinstance(lst, list) else []:
            if isinstance(it, dict) and it.get("canonical"):
                m.add(it.get("raw") or raw, to_key(it["canonical"]), "knowledge/SYNONYM_LIBRARY_v4.json", str(it.get("source", ""))[:40])
    for owner, d in (((books.get("synonym_ssot") or {}).get("scopes") or {}).get("broker") or {}).items():
        if not isinstance(d, dict):                        # a bare word list (no canonical) says nothing about the key
            continue
        for key, aliases in d.items():
            for a in (aliases if isinstance(aliases, list) else []):
                m.add(a, to_key(key), "VRN_SYNONYM_SSOT_v0100.json", f"runtime.{owner}")
    for b in ((books.get("operator_labels") or {}).get("broker_candidates") or []):
        for a in [b.get("code"), b.get("zh"), b.get("en"), *(b.get("names") or [])]:
            m.add(a, to_key(b.get("code")), "VRN_OperatorLabels_SSOT_v0100.json", "broker_candidates（候選）")
    s05 = books.get("s05") or {}
    for d, it in (s05.get("email_domain_to_broker") or {}).items():
        key = to_key(it.get("broker_en") or it.get("broker")) if isinstance(it, dict) else to_key(it)
        dom.add(d, key, "VRN_S05_FieldRegistry_v0103.json", "email_domain_to_broker")
    for d, key in (((books.get("report_field_rules") or {}).get("broker_domains_addendum") or {}).get("map") or {}).items():
        dom.add(d, to_key(key), "VIA_VRN_ReportFieldRules_SSOT_v0101.json", "broker_domains_addendum")
    bo = (((books.get("synonym_ssot") or {}).get("conflicts") or {}).get("book_broker_vs_runtime") or {}).get("book_only") or {}
    for key, frags in bo.items():
        for f in frags or []:
            dom.add(f, to_key(key), "VRN_SYNONYM_SSOT_v0100.json", "book_broker_vs_runtime.book_only（網域片段）")
    return m.result(), dom.result()


# [VRN-ID] VRN-ENG017-FNC016 · LOGIC
def merge_rating(books):
    """Rating words -> the coarse level they compare at (BUY / HOLD / SELL / NOT_RATED); the fine key is kept in the note.
    The record shows the rating as printed; this map is only for 'same level' comparisons."""
    m = AliasTable("rating")

    # [VRN-ID] VRN-ENG017-FNC017 · LOGIC
    def coarse(key):
        k = fold_text(key).replace(" ", "_").replace("-", "_")
        for fine, c in RATING_COARSE.items():
            if k == fine or k.endswith("_" + fine) or k.startswith(fine):
                return c
        return str(key).upper()
    rd = books.get("rating_dict") or {}
    for level, it in (rd.get("levels") or {}).items():
        for w in [*(it.get("zh") or []), *(it.get("en") or [])]:
            m.add(w, level, "VRN_Rating_Dict_v0100.json", "levels")
    for fine, words in (rd.get("keyword_sets") or {}).items():
        for w in words or []:
            m.add(w, coarse(fine), "VRN_Rating_Dict_v0100.json", f"keyword_sets.{fine}")
    s05 = books.get("s05") or {}
    for fine, it in (((s05.get("rating_list") or {}).get("canonical_v22_2")) or {}).items():
        for w in [*(it.get("chinese") or []), *(it.get("english") or [])] if isinstance(it, dict) else []:
            m.add(w, coarse(fine), "VRN_S05_FieldRegistry_v0103.json", f"rating_list.{fine}")
    for raw, lst in (((books.get("synonym_library_v4") or {}).get("scopes") or {}).get("rating") or {}).items():
        for it in lst if isinstance(lst, list) else []:
            if isinstance(it, dict) and it.get("canonical"):
                m.add(it.get("raw") or raw, coarse(it["canonical"]), "knowledge/SYNONYM_LIBRARY_v4.json", str(it.get("source", ""))[:40])
    su = books.get("synonym_union") or {}
    for w, c in (su.get("coarse_of") or {}).items():
        if isinstance(c, str):
            m.add(w, coarse(c), "VIA_SSOT_SynonymUnion_v0107.json", "coarse_of")
    return m.result()


# [VRN-ID] VRN-ENG017-FNC018 · LOGIC
def merge_term_table(books):
    """Label words per field (no canonical): target price, prior words, current price, upside, analyst, date."""
    tt = ((books.get("titletrim") or {}).get("cover") or {})
    labels = tt.get("labels") or {}
    s05 = books.get("s05") or {}
    syn = ((books.get("synonym_ssot") or {}).get("scopes") or {})
    bt = syn.get("book_terms") or {}
    out = {}
    t = TermTable()
    for w in labels.get("target_price") or []:
        t.add(w, "VRN_TitleTrim_SSOT_v0100.json#cover.labels.target_price")
    for w in ((s05.get("target_price_dict") or {}).get("synonyms") or []):
        t.add(w, "VRN_S05_FieldRegistry_v0103.json#target_price_dict.synonyms")
    for owner, lst in (syn.get("target_price_terms") or {}).items():
        for w in lst or []:
            t.add(w, f"VRN_SYNONYM_SSOT_v0100.json#target_price_terms.{owner}")
    for raw in (((books.get("synonym_library_v4") or {}).get("scopes") or {}).get("target_price") or {}):
        t.add(raw, "knowledge/SYNONYM_LIBRARY_v4.json#scopes.target_price")
    for w in ((bt.get("TARGET_PRICE") or {}).get("terms") or {}).get("target_price", []) if isinstance((bt.get("TARGET_PRICE") or {}).get("terms"), dict) else []:
        t.add(w, "VRN_SYNONYM_SSOT_v0100.json#book_terms.TARGET_PRICE")
    out["target_price_labels"] = t.result()
    t = TermTable()
    for w in tt.get("prior_words") or []:
        t.add(w, "VRN_TitleTrim_SSOT_v0100.json#cover.prior_words")
    for w in ((s05.get("target_price_dict") or {}).get("stopwords_previous") or []):
        t.add(w, "VRN_S05_FieldRegistry_v0103.json#target_price_dict.stopwords_previous")
    for w in PRIOR_CORE_WORDS:
        t.add(w, "engine/VRN_Evidence_Core.py#_TP_EXCLUDE_BEFORE")
    out["prior_words"] = t.result()
    t = TermTable()
    for w in labels.get("current_price") or []:
        t.add(w, "VRN_TitleTrim_SSOT_v0100.json#cover.labels.current_price")
    for w in (((bt.get("ADJ_CLOSE") or {}).get("terms") or {}).get("adj_close") or []):
        t.add(w, "VRN_SYNONYM_SSOT_v0100.json#book_terms.ADJ_CLOSE")
    out["current_price_labels"] = t.result()
    t = TermTable()
    for w in labels.get("upside") or []:
        t.add(w, "VRN_TitleTrim_SSOT_v0100.json#cover.labels.upside")
    out["upside_labels"] = t.result()
    t = TermTable()
    for w in labels.get("analyst") or []:
        t.add(w, "VRN_TitleTrim_SSOT_v0100.json#cover.labels.analyst")
    for k, lst in (((bt.get("ANALYST") or {}).get("terms") or {})).items():
        for w in lst or []:
            t.add(w, f"VRN_SYNONYM_SSOT_v0100.json#book_terms.ANALYST.{k}")
    rf = books.get("report_field_rules") or {}
    for k in ("zh", "en"):
        for w in ((rf.get("analyst_titles") or {}).get(k) or []):
            t.add(w, f"VIA_VRN_ReportFieldRules_SSOT_v0101.json#analyst_titles.{k}")
    out["analyst_labels"] = t.result()
    t = TermTable()
    for w in labels.get("rating") or []:
        t.add(w, "VRN_TitleTrim_SSOT_v0100.json#cover.labels.rating")
    out["rating_labels"] = t.result()
    t = TermTable()
    for w in labels.get("date") or []:
        t.add(w, "VRN_TitleTrim_SSOT_v0100.json#cover.labels.date")
    out["date_labels"] = t.result()
    return out


FIELD_REGEX_HINTS = {
    "ticker": ("ticker", "tricode", "tri_code", "platform", "yahoo", "bloomberg", "code"),
    "email": ("email", "mail"),
    "tel": ("tel", "phone"),
    "target_price": ("target", "tp_", "_tp", "price_target"),
    "rating": ("rating",),
    "broker": ("broker",),
    "upside": ("upside",),
    "date": ("date",),
    "analyst": ("analyst", "name_rx"),
    "title": ("title",),
}
S05_REGEX_FIELD = {"TW_TICKER_4DIGIT": "ticker", "TW_YFINANCE": "ticker", "TW_BLOOMBERG": "ticker", "EMAIL_FULL": "email",
                   "EMAIL_LOCAL_NUMERIC": "email", "EMAIL_LOCAL_NAME": "email", "TEL_TW_FULL": "tel", "TEL_EXTENSION": "tel",
                   "BROKER_RATING": "rating", "TARGET_PRICE_LABEL": "target_price", "TARGET_PRICE_VERB": "target_price",
                   "TARGET_PRICE_TAIL": "target_price", "UPSIDE_PCT": "upside"}
CONTACT_REGEX_FIELD = {"target_price": "target_price", "rating_en": "rating", "rating_zh": "rating", "broker_span": "broker", "email": "email",
                       "phone_tw_mobile": "tel", "phone_tw_fixed": "tel", "phone_hk_with_cc": "tel"}
TITLETRIM_REGEX_FIELD = {"tel_rx": "tel", "email_rx": "email", "name_rx": "analyst", "date_like_rx": "date", "prior_line_rx": "target_price",
                         "prior_before_rx": "target_price", "not_price_after_rx": "target_price", "current_price_not_near_rx": "target_price",
                         "date_exclude_before_rx": "date", "broker_context_rx": "broker"}


# [VRN-ID] VRN-ENG017-FNC019 · LOGIC
def merge_regexes(books):
    """The regexes behind the fields, from the REGEX book (by the site's function name), S05, the contact book, the TitleTrim
    book and the ticker master; folded on the pattern string."""
    per = {f: RegexTable() for f in FIELD_REGEX_HINTS}
    rx = books.get("regex_ssot") or {}
    for p in rx.get("patterns") or []:
        sites = p.get("sites") or []
        names = " ".join(f"{s.get('file', '')} {s.get('qualname', '')}".casefold() for s in sites)
        for field, hints in FIELD_REGEX_HINTS.items():
            if any(h in names for h in hints):
                per[field].add(p.get("pattern"), "VRN_REGEX_SSOT_v0100.json", p.get("id", ""))
    for name, it in (((books.get("s05") or {}).get("all_regex")) or {}).items():
        f = S05_REGEX_FIELD.get(name)
        if f and isinstance(it, dict):
            per[f].add(it.get("pattern"), "VRN_S05_FieldRegistry_v0103.json", name)
    for name, pat in (((books.get("contact_regex") or {}).get("patterns")) or {}).items():
        f = CONTACT_REGEX_FIELD.get(name)
        if f:
            per[f].add(pat, "VRN_Contact_Regex_v0100.json", name)
    cv = ((books.get("titletrim") or {}).get("cover") or {})
    for name, f in TITLETRIM_REGEX_FIELD.items():
        if cv.get(name):
            per[f].add(cv[name], "VRN_TitleTrim_SSOT_v0100.json", f"cover.{name}")
    for pat in cv.get("date_rx") or []:
        per["date"].add(pat, "VRN_TitleTrim_SSOT_v0100.json", "cover.date_rx")
    for pat in cv.get("tp_from_to_rx") or []:
        per["target_price"].add(pat, "VRN_TitleTrim_SSOT_v0100.json", "cover.tp_from_to_rx")
    tm = books.get("ticker_master_text") or ""
    m = re.search(r"PLATFORM_SUFFIX\s*=\s*(\{.*?\})", tm, re.S)
    if m:
        for plat, pat in re.findall(r'"([A-Z]+)":\s*r?"([^"]*)"', m.group(1)):
            if pat:
                per["ticker"].add(pat, "engine/VIA_TW_Ticker_Master_v0210.py", f"PLATFORM_SUFFIX.{plat}")
    return {f: r.result() for f, r in per.items()}


# [VRN-ID] VRN-ENG017-FNC020 · IO
def load_books(root=None):
    root = Path(root or VRN_ROOT)
    books, prov = {}, []
    for key, rel in SOURCE_BOOKS.items():
        path = root / rel
        if not path.is_file():
            prov.append({"book": rel, "present": False})
            continue
        if rel.endswith(".py"):
            books[key + "_text"] = path.read_text(encoding="utf-8", errors="replace")
        else:
            books[key] = read_json_file(path)
        prov.append({"book": rel, "present": True, "sha256": file_sha256(path)})
    return books, prov


# [VRN-ID] VRN-ENG017-FNC021 · BUILD
def build_book(root=None, generated=None):
    """The merged book from the books on disk (deterministic apart from `generated`)."""
    books, prov = load_books(root)
    canon = broker_canon_map(books)
    broker, domains = merge_broker(books, canon)
    rating = merge_rating(books)
    terms = merge_term_table(books)
    regexes = merge_regexes(books)
    conflicts = [dict(c, scope="broker") for c in broker["conflicts"]] + [dict(c, scope="email_domain") for c in domains["conflicts"]] \
        + [dict(c, scope="rating") for c in rating["conflicts"]]
    fields = OrderedDict()
    for key, zh, src in FIELDS:
        fields[key] = {"zh": zh, "source": src}
    fields["broker"]["synonyms"] = "broker"
    fields["email"]["domains"] = "email_domain"
    fields["rating"]["synonyms"] = "rating"
    fields["target_price_original"]["labels"] = ["target_price_labels", "prior_words"]
    fields["adj_close"]["labels"] = ["current_price_labels"]
    fields["upside_pct"]["labels"] = ["upside_labels"]
    fields["analyst"]["labels"] = ["analyst_labels"]
    book = OrderedDict([
        ("schema", "VRN_TickerRecord_SSOT_v0100"), ("version", RECORD_VERSION),
        ("generated", generated or time.strftime("%Y-%m-%dT%H:%M:%S")),
        ("operator", "2026-10-12「用四碼代號去資料庫找到 YFINANCE TICKER … UPSIDE %；相關邏輯及 SSOT 同義字 REGEX 跨專案整合去重不衝突，一次完善」"),
        ("policy", {"only_add": True, "built_by": "engine/VRN_TickerRecord_v0100.py build-book（從倉內每一本來源冊合併；冊舊了 selftest 就紅）",
                    "canonical": "券商正典鍵 = VRN_Broker_Dict_v0103 的鍵（首頁引擎答的那一套）；評等照原文輸出，同義字只用來比對同級（BUY／HOLD／SELL／NOT_RATED）",
                    "conflicts": "同一別名兩本冊給不同正典 → 列在 conflicts，兩邊都留，不自動裁定（操作員裁）",
                    "dedupe": "別名 casefold 相同就折成一條，來源全部列出", "no_network": True}),
        ("key", {"field": "ticker", "rule": "四碼台股代號（含代號+字母）：標題、檔名、首頁三平台碼兩條讀法一致才 VERIFIED；yfinance = 代號.TW／.TWO，Bloomberg = 代號 TT"}),
        ("fields", fields),
        ("broker", broker), ("email_domain", domains), ("rating", rating), ("terms", terms), ("regex", regexes),
        ("conflicts", conflicts),
        ("merge", {"books": prov, "counts": {"broker_aliases": broker["count"], "broker_folded": broker["duplicates_folded"],
                                              "email_domains": domains["count"], "rating_words": rating["count"],
                                              "regex": sum(v["count"] for v in regexes.values()),
                                              "regex_folded": sum(v["duplicates_folded"] for v in regexes.values()),
                                              "conflicts": len(conflicts)}}),
    ])
    return book


# [VRN-ID] VRN-ENG017-FNC022 · IO
def write_book(path=None, root=None):
    """內容沒變就不重寫冊,連 `generated` 時間戳也沿用舊的。

    build 只是「把來源冊合併成這一本」,重跑不等於內容變了。以前每跑一次 build
    就蓋一個新時間戳,於是同一個 v0100 檔名在 GitHub 與本機之間內容不同,
    治理閘會判成「版本號衝突(同名不同內容)」,但實質內容一模一樣。
    現在只有合併結果真的變了才換時間戳並落地。
    """
    path = Path(path or BOOK_PATH)
    on_disk = read_json_file(path)
    kept = build_book(root, generated=(on_disk or {}).get("generated"))
    if on_disk and json.dumps(kept, ensure_ascii=False, sort_keys=True) == json.dumps(on_disk, ensure_ascii=False, sort_keys=True):
        return path, kept
    book = build_book(root)
    path.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path, book


# [VRN-ID] VRN-ENG017-FNC023 · VALIDATE
def check_record_book(path=None, root=None):
    """True when the book on disk equals what the source books give now (the timestamp aside)."""
    path = Path(path or BOOK_PATH)
    on_disk = read_json_file(path)
    if not on_disk:
        return False, "冊不在"
    fresh = build_book(root, generated=on_disk.get("generated"))
    same = json.dumps(fresh, ensure_ascii=False, sort_keys=True) == json.dumps(on_disk, ensure_ascii=False, sort_keys=True)
    return same, "" if same else "來源冊變了：跑 VRN_TickerRecord_v0100.py build-book"


# =====================================================================
# 2 . THE RECORD
# =====================================================================
# [VRN-ID] VRN-ENG017-FNC024 · LOGIC
def _part(parts, name):
    return parts.get(name) or {}


# [VRN-ID] VRN-ENG017-FNC025 · LOGIC
def _cjk(text):
    return bool(re.search(r"[一-鿿]", str(text or "")))


# [VRN-ID] VRN-ENG017-FNC026 · LOGIC
def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


# [VRN-ID] VRN-ENG017-FNC027 · IO
def load_localdb_module():
    spec = importlib.util.spec_from_file_location("VRN_TickerRecord_localdb", HERE / "VRN_LocalDB_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# [VRN-ID] VRN-ENG017-FNC028 · LOGIC
def lookup_code_record(code, db_path=None, db=None):
    """The DB part for a bare 4-digit code: NAME, market, yfinance ticker, Bloomberg ticker, the latest adj close.
    -> {code, name, name_en, market, yfinance_ticker, bloomberg_ticker, adj_close, adj_close_date, status}."""
    code = str(code or "").strip()
    out = {"code": code, "name": "", "name_en": "", "market": "", "yfinance_ticker": "", "bloomberg_ticker": f"{code} TT" if code else "",
           "yf_source": "derived", "bbg_source": "derived", "adj_close": None, "adj_close_date": "", "status": "NO_DB"}
    if not code:
        out["status"] = "NO_CODE"
        return out
    close = False
    if db is None and db_path:
        try:
            db = load_localdb_module().LocalDB(db_path)
            close = True
        except Exception as error:  # noqa: BLE001
            out["status"] = f"DB_ERROR {error.__class__.__name__}"
            return out
    if db is None or getattr(db, "status", "") != "OK":
        out["status"] = getattr(db, "status", "NO_DB") or "NO_DB"
        return out
    try:
        row = db.names().get(code)
        if row:
            out["name"], out["market"], yf = row[0] or "", row[1] or "", row[2] or ""
            if yf:
                out["yfinance_ticker"], out["yf_source"] = str(yf), "localdb.yf_ticker"
        if callable(getattr(db, "name_en", None)):          # 2026-10-13 公司名稱一律從資料庫取：英文名欄有就帶出來
            out["name_en"] = str(db.name_en(code) or "").strip()
        if not out["yfinance_ticker"]:
            mk = fold_text(out["market"])
            if mk:
                out["yfinance_ticker"] = f"{code}." + ("TWO" if any(w in mk for w in ("tpex", "otc", "上櫃", "櫃")) else "TW")
        ticker, _basis, latest = db.quote(code, None)
        if latest:
            out["adj_close"], out["adj_close_date"] = _num(latest[2]), str(latest[0])[:10]
            if ticker and not out["yfinance_ticker"]:
                out["yfinance_ticker"], out["yf_source"] = str(ticker), "localdb.prices"
        out["status"] = "OK" if (row or latest) else "NOT_IN_DB"
    finally:
        if close:
            try:
                db.close()
            except Exception:  # noqa: BLE001
                pass
    return out


# [VRN-ID] VRN-ENG017-FNC029 · LOGIC
def record_of(result, basic=None, fpe=None, listing=None):
    """One stock report -> the 15 fields {value, state, source} from what the readers already produced (nothing re-read)."""
    basic, fpe, listing = basic or {}, fpe or {}, listing or {}
    parts = {p["part"]: p for p in result.get("parts") or [] if "@" not in str(p.get("part", ""))}
    rec = OrderedDict()

    # [VRN-ID] VRN-ENG017-FNC030 · LOGIC
    def put(key, value, state, source):
        rec[key] = {"value": "" if value is None else value, "state": state, "source": source}

    # [VRN-ID] VRN-ENG017-FNC031 · LOGIC
    def from_part(key, name, source):
        p = _part(parts, name)
        put(key, p.get("value", ""), p.get("state") or "MISSING", source)
    from_part("ticker", "title.ticker", "G17 title.ticker")
    code = str(rec["ticker"]["value"] or basic.get("TW_TICKER") or "").strip()
    if not rec["ticker"]["value"] and code:
        put("ticker", code, "SINGLE", "資料庫引擎 TW_TICKER")
    readers = (("首頁引擎", fpe.get("page_codes") or []),
               ("TRIM", (((result.get("cover") or {}).get("fields") or {}).get("page_codes") or {}).get("codes") or []))

    # [VRN-ID] VRN-ENG017-FNC037 · LOGIC
    def printed(platform):
        """首頁印的那個碼，兩條讀法各讀各的 —— 首頁引擎的 page_codes、TitleTrim 的 page_codes。

        實測 2026-10-20：TRIM 本來就讀到了（`title.market` 用的就是同一批 hits），只是沒交出來，
        所以這兩欄在 59 份報告裡 58 筆 SINGLE、永遠鎖不住；沒有首頁引擎結果的 .txt 更把紙上
        印著的 `Yahoo 3653.TW` 記成 MISSING、把印著的 `3653 TT` 記成「推」。
        """
        out = []
        for who, src in readers:
            raw = next((c.get("raw") for c in src if isinstance(c, dict)
                        and c.get("platform") == platform and c.get("core") == code), "")
            if raw:
                out.append((who, str(raw).strip()))
        return out

    # [VRN-ID] VRN-ENG017-FNC038 · IO
    def put_code(key, reads, derived, derived_source):
        """兩條讀法一致 = VERIFIED、不一致 = CONFLICT、只有一條 = SINGLE；紙上沒印才輪到推算。"""
        if len({fold_text(v) for _w, v in reads}) > 1:
            put(key, reads[0][1], "CONFLICT", "首頁兩條讀法不一致：" + "、".join(f"{w} {v}" for w, v in reads))
        elif len(reads) > 1:
            put(key, reads[0][1], "VERIFIED", "首頁印的碼：" + "＋".join(w for w, _v in reads) + " 一致")
        elif reads:
            put(key, reads[0][1], "SINGLE", f"首頁印的碼（只有{reads[0][0]}讀到）")
        elif derived:
            put(key, derived, "DERIVED", derived_source)
        else:
            put(key, "", "MISSING", "資料庫沒有這個代號，首頁也沒印" if code else "沒有代號")
    yf_reads, bbg_reads = printed("yfinance"), printed("bloomberg")
    # Codex PR #76 P2：資料庫對上其中一條，不能把**兩條讀法互相不一致**蓋掉 —— 那正是 G20 要喊的那一種。
    yf_clash = len({fold_text(v) for _w, v in yf_reads}) > 1
    if listing.get("yfinance_ticker") and listing.get("yf_source", "").startswith("localdb") and not yf_clash:
        agree = any(fold_text(v) == fold_text(listing["yfinance_ticker"]) for _w, v in yf_reads)
        put("yfinance_ticker", listing["yfinance_ticker"], "VERIFIED" if agree else "DB", "本機資料庫 yf_ticker" + ("＋首頁印的碼一致" if agree else ""))
    else:
        put_code("yfinance_ticker", yf_reads, listing.get("yfinance_ticker"), "市場推（上市 .TW／上櫃 .TWO）")
    put_code("bloomberg_ticker", bbg_reads, f"{code} TT" if code else "", "推：<代號> TT")
    name_db = basic.get("NameDB") or listing.get("name") or ""
    comp = _part(parts, "title.company")
    page_company = fpe.get("company_name_page")
    if isinstance(page_company, dict):
        page_company = page_company.get("value") or page_company.get("name") or ""
    comp_read = comp.get("printed") if comp.get("source") == "db" else comp.get("value")   # 2026-10-13: the report's own reading
    zh_candidates = [v for v in (comp_read, page_company, basic.get("CompanyNamePage"), basic.get("CompanyName")) if v and _cjk(v)]
    if name_db:
        agree = any(fold_text(name_db) in fold_text(v) or fold_text(v) in fold_text(name_db) for v in zh_candidates)
        put("name", name_db, "VERIFIED" if agree else "DB", "本機資料庫 NAME" + ("＋報告的中文名一致" if agree else ""))
    elif zh_candidates:
        put("name", zh_candidates[0], comp.get("state") if comp_read == zh_candidates[0] else "SINGLE", "報告印的中文名")
    else:
        put("name", "", "MISSING", "資料庫沒有、報告也沒印中文名")
    en_candidates = [v for v in (comp_read, page_company) if v and not _cjk(v) and re.search(r"[A-Za-z]{2,}", str(v))]
    en_db = str(listing.get("name_en") or "").strip()
    if en_db:                                               # 2026-10-13 公司名稱一律從資料庫取：資料庫有英文名就用它，報告印的拿來核對
        agree = any(fold_text(en_db) in fold_text(v) or fold_text(v) in fold_text(en_db) for v in en_candidates)
        put("english_name", en_db, "VERIFIED" if agree else "DB", "本機資料庫英文名" + ("＋報告印的英文名一致" if agree else ""))
    elif en_candidates:
        put("english_name", en_candidates[0], comp.get("state") if comp_read == en_candidates[0] and comp.get("source") != "db" else "SINGLE",
            "報告印的英文名")
    else:
        put("english_name", "", "NOT_PRINTED", "報告沒印英文名（資料庫也沒有英文名）")
    from_part("broker", "cover.broker", "G17 cover.broker")
    from_part("analyst", "cover.analyst", "G17 cover.analyst")
    from_part("title", "title.text", "G17 title.text")
    from_part("email", "cover.email", "G17 cover.email")
    from_part("tel", "cover.tel", "G17 cover.tel")
    from_part("rating", "cover.rating", "G17 cover.rating（照原文）")
    from_part("target_price_original", "cover.target_price", "G17 cover.target_price")
    tp_adj = _num(basic.get("TargetPriceAdj"))
    db_status = str(basic.get("LocalDBStatus") or listing.get("status") or "NO_DB")
    put("target_price_adj", tp_adj if tp_adj is not None else "", "DB" if tp_adj is not None else ("NOT_APPLICABLE" if db_status.startswith("OK") else db_status),
        "本機資料庫 TargetPriceAdj（目標價 × 報告日係數 ÷ 最新係數）")
    latest, latest_d = _num(basic.get("AdjCloseLatest")), str(basic.get("AdjCloseLatestDate") or "")[:10]
    if latest is None and listing.get("adj_close") is not None:
        latest, latest_d = listing["adj_close"], listing.get("adj_close_date", "")
    put("adj_close", latest if latest is not None else "", "DB" if latest is not None else db_status, "本機資料庫最新 adj_close")
    rec["adj_close"]["date"] = latest_d
    before, before_d = _num(basic.get("AdjCloseReport")), str(basic.get("AdjCloseReportDate") or "")[:10]
    put("adj_close_before_report", before if before is not None else "", "DB" if before is not None else db_status, "本機資料庫報告日前最後交易日 adj_close")
    rec["adj_close_before_report"]["date"] = before_d
    up = _part(parts, "cover.upside")
    # calc 是「拿報告印的原始價重算」的上漲%，所以用 cover.current_price 帶的原始收盤價（close），
    # 不是它的 value —— value 自 2026-10-16 起是 adj close 為基準（操作員裁決）。拿 adj 去算，
    # 除權息過的股票這一欄會悄悄算錯。還原後的上漲% 另有 rec["upside_pct"]["adj"]。
    cpp = _part(parts, "cover.current_price")
    tp = _num(_part(parts, "cover.target_price").get("value"))
    cp = _num(cpp.get("close") if cpp.get("close") not in ("", None) else cpp.get("value"))
    calc = round((tp - cp) / cp * 100.0, 2) if tp is not None and cp else None
    # 2026-10-20：這一欄 59/59 都是 NOT_PRINTED（「報告沒印」），而同一輪的另外兩張表把同一個數字
    # 當成 DERIVED 印出來：四重點第 1 點「上漲空間 29.99% (DERIVED)」、basic_info.UpsideDownsidePct
    # 29.99（與這裡的 calc 59/59 相符）。連 cover.upside 這個部位自己的 why 都寫著
    # 「沒印；VRN 重算 29.99%（def03）」—— 數字算出來了，只活在那句中文裡，欄位是空的。
    # 這不是新規則：代號那幾欄（put_code）早就有 DERIVED 這一格，推算得出來就不該記成沒讀到。
    # 印了的照舊優先，一個字都不改；沒印、而且真的算得出來，才用 DERIVED。
    if up.get("value") not in ("", None):
        # 2026-10-21 第二十三輪：部位自己現在也會交出 DERIVED（首頁沒印、但目標價與現價都在），
        # 這一支照收 —— 但 why 要跟著狀態走，沒印的值不可以寫成「首頁印的」。引用部位自己那一句，
        # 不在這裡另寫一次（同一句話兩個地方寫，下次只會改到一邊）。
        put("upside_pct", up["value"], up.get("state") or "NOT_PRINTED",
            (up.get("why") or "") if up.get("state") == "DERIVED" else "首頁印的（cover.upside）")
    elif calc is not None:
        put("upside_pct", calc, "DERIVED", "首頁沒印；VRN 重算 (目標價−現價)÷現價（現價用報告印的原始收盤價，不是 adj）")
    else:
        put("upside_pct", "", up.get("state") or "NOT_PRINTED", "首頁印的（cover.upside）")
    rec["upside_pct"]["calc"] = calc
    rec["upside_pct"]["adj"] = _num(basic.get("UpsideAdjPct"))
    return rec


# [VRN-ID] VRN-ENG017-FNC032 · LOGIC
def records_for_run(results, basics=None, fpes=None, db_path=None):
    """Every stock report of one run -> rows (file + the 15 fields + states + extras).  The DB is opened once."""
    basics, fpes = basics or {}, fpes or {}
    db = None
    if db_path:
        try:
            db = load_localdb_module().LocalDB(db_path)
        except Exception:  # noqa: BLE001
            db = None
    rows = []
    try:
        for res in sorted(results, key=lambda r: str(r.get("file", ""))):
            if res.get("status") != "OK":
                continue
            name = res.get("file", "")
            basic = basics.get(name) or basics.get(Path(name).name) or {}
            fpe = fpes.get(name) or fpes.get(Path(name).name) or {}
            code = str(((_part({p["part"]: p for p in res.get("parts") or [] if "@" not in str(p.get("part", ""))}, "title.ticker")).get("value"))
                       or basic.get("TW_TICKER") or "").strip()
            listing = lookup_code_record(code, db=db) if (db is not None and code) else {}
            rec = record_of(res, basic, fpe, listing)
            row = OrderedDict([("file", name)])
            for key, _zh, _src in FIELDS:
                row[key] = rec[key]["value"]
            for key, _zh, _src in FIELDS:
                row[key + "_state"] = rec[key]["state"]
            row["adj_close_date"] = rec["adj_close"].get("date", "")
            row["adj_close_before_report_date"] = rec["adj_close_before_report"].get("date", "")
            row["upside_pct_calc"] = rec["upside_pct"].get("calc")
            row["upside_pct_adj"] = rec["upside_pct"].get("adj")
            row["sources"] = json.dumps({k: rec[k]["source"] for k, _z, _s in FIELDS}, ensure_ascii=False)
            rows.append(row)
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:  # noqa: BLE001
                pass
    return rows


# [VRN-ID] VRN-ENG017-FNC033 · IO
def write_table(out_dir, rows):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    jp, cp = out / f"{TABLE_NAME}.json", out / f"{TABLE_NAME}.csv"
    jp.write_text(json.dumps(rows, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    cols = list(rows[0].keys()) if rows else ["file", *[k for k, _z, _s in FIELDS]]
    with open(cp, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return {"json": str(jp), "csv": str(cp), "rows": len(rows)}


# [VRN-ID] VRN-ENG017-FNC034 · LOGIC
def summarize_record_states(rows):
    """Per field: how many VERIFIED / SINGLE / DB / DERIVED / MISSING / NOT_PRINTED."""
    out = OrderedDict()
    for key, zh, _src in FIELDS:
        out[key] = {"zh": zh, **Counter(str(r.get(key + "_state", "")) for r in rows)}
    return out


# =====================================================================
# SELFTEST / CLI
# =====================================================================
# [VRN-ID] VRN-ENG017-FNC035 · ENTRY
def selftest(verbose=True):
    checks = []
    books = {"broker_v0103": {"brokers": {"KGI": {"abbr": "KGI", "chinese_name": "凱基證券", "english_name": "KGI Securities",
                                                  "aliases": ["KGI", "凱基", "kgi.com"]},
                                          "MEGA": {"abbr": "MEGA", "chinese_name": "兆豐證券", "english_name": "Mega Securities", "aliases": ["兆豐", "Mega"]}}},
             "broker_v0100": {"brokers": {"凱基": {"abbr": "KGI", "aliases": ["凱基投顧", "kgi"]}, "兆豐": {"abbr": "MEGA", "aliases": ["兆豐證券"]}},
                              "brokers_extended": [{"code": "MS", "en": "Morgan Stanley", "zh": "摩根士丹利", "aliases": ["大摩"]}]},
             "broker_list": {"brokers": [{"canonical": "凱基", "canonical_en": "KGI", "aliases": ["KGI Securities", "凱基"]},
                                         {"canonical": "大摩", "canonical_en": "MS", "aliases": ["大摩"]}]},
             "synonym_union": {"key_alias": {"MEGABANK": {"canonical": "MEGA"}}, "coarse_of": {"Outperform": "BUY"}},
             "s05": {"email_domain_to_broker": {"kgi.com": {"broker": "凱基", "broker_en": "KGI"}, "megabank.com.tw": {"broker": "兆豐"}},
                     "rating_list": {"canonical_v22_2": {"strong_buy": {"english": ["Outperform"]}, "buy": {"chinese": ["買進"], "english": ["Buy"]}}},
                     "target_price_dict": {"synonyms": ["目標價", "Target Price", "TP"], "stopwords_previous": ["previous", "前次"]},
                     "all_regex": {"TW_BLOOMBERG": {"pattern": r"\d{4}\s+TT"}, "EMAIL_FULL": {"pattern": r"[^@\s]+@[^@\s]+"}}},
             "report_field_rules": {"broker_domains_addendum": {"map": {"kgi.com": "KGI", "megabank.com.tw": "MS"}}},
             "rating_dict": {"levels": {"BUY": {"zh": ["買進"], "en": ["Buy", "Outperform"]}, "HOLD": {"zh": ["中立"], "en": ["Hold"]}},
                             "keyword_sets": {"strong_buy": ["Outperform"], "buy": ["買進"]}},
             "titletrim": {"cover": {"labels": {"target_price": ["目標價", "TP"], "current_price": ["收盤價"], "upside": ["上漲空間"],
                                                "analyst": ["分析師"], "rating": ["評等"], "date": ["報告日期"]},
                                     "prior_words": ["前次", "Previous"], "tel_rx": r"\d{2}-\d{4}-\d{4}", "email_rx": r"[^@\s]+@[^@\s]+"}},
             "contact_regex": {"patterns": {"email": r"[^@\s]+@[^@\s]+", "phone_tw_fixed": r"0\d{1,2}[- ]?\d{3,4}[- ]?\d{3,4}"}},
             "regex_ssot": {"patterns": [{"id": "RX-1", "pattern": r"\d{4}\s+TT", "sites": [{"file": "engine/VIA_VRN_FirstPageEngine.py", "qualname": "tri_code"}]}]}}
    canon = broker_canon_map(books)
    broker, domains = merge_broker(books, canon)
    rating = merge_rating(books)
    terms = merge_term_table(books)
    regexes = merge_regexes(books)
    e = broker["entries"]
    checks.append(("券商別名折疊、正典統一到 v0103 鍵（凱基／kgi／KGI → KGI；大摩 → MS）", e["凱基"]["canonical"] == "KGI" and e["KGI"]["canonical"] == "KGI"
                   and e["大摩"]["canonical"] == "MS" and len([a for a in e if fold_text(a) == "kgi"]) == 1, {k: v["canonical"] for k, v in list(e.items())[:6]}))
    checks.append(("每條別名列出來源冊", "VRN_Broker_Dict_v0100.json#brokers" in e["凱基投顧"]["from"] and len(e["凱基"]["from"]) >= 3, e["凱基"]["from"]))
    checks.append(("網域衝突照列不裁（megabank.com.tw：S05 兆豐 vs 規則冊 MS）", any(c["alias"] == "megabank.com.tw" and set(c["canonicals"]) == {"MEGA", "MS"} for c in domains["conflicts"])
                   and domains["entries"]["kgi.com"]["canonical"] == "KGI", domains["conflicts"]))
    checks.append(("評等詞只比粗級：Outperform = BUY（三本冊一致，沒有衝突）", rating["entries"]["Outperform"]["canonical"] == "BUY" and not rating["conflicts"], rating["conflicts"]))
    checks.append(("標籤去重、前次字合併三處", terms["target_price_labels"]["count"] == 3 and terms["prior_words"]["count"] >= 10
                   and "engine/VRN_Evidence_Core.py#_TP_EXCLUDE_BEFORE" in terms["prior_words"]["terms"]["from"], (terms["target_price_labels"]["count"], terms["prior_words"]["count"])))
    checks.append(("regex 同式折一條、來源全列、都可編譯", regexes["email"]["count"] == 1 and len(regexes["email"]["patterns"][0]["from"]) == 3
                   and regexes["ticker"]["count"] == 1 and not any(v["broken"] for v in regexes.values()), {k: v["count"] for k, v in regexes.items()}))
    cur, why = check_record_book()
    checks.append(("倉內的冊和來源冊一致（舊了就紅：build-book）", cur, why))
    result = {"file": "凱基投顧_2330 台積電_王小明_20260901.pdf", "status": "OK",
              "parts": [{"part": "title.ticker", "value": "2330", "state": "VERIFIED"}, {"part": "title.company", "value": "台積電", "state": "VERIFIED"},
                        {"part": "title.text", "value": "台積電(2330 TT) 先進製程", "state": "VERIFIED"}, {"part": "cover.broker", "value": "KGI", "state": "VERIFIED"},
                        {"part": "cover.analyst", "value": "王小明", "state": "SINGLE"}, {"part": "cover.email", "value": "a@kgi.com", "state": "VERIFIED"},
                        {"part": "cover.tel", "value": "0221818888", "state": "VERIFIED"}, {"part": "cover.rating", "value": "買進", "state": "VERIFIED"},
                        {"part": "cover.target_price", "value": 1200.0, "state": "VERIFIED"}, {"part": "cover.current_price", "value": 1000.0, "state": "SINGLE"},
                        {"part": "cover.upside", "value": 20.0, "state": "VERIFIED"}]}
    basic = {"TW_TICKER": "2330", "NameDB": "台積電", "TargetPriceAdj": 1188.0, "AdjCloseLatest": 1010.0, "AdjCloseLatestDate": "2026-10-09",
             "AdjCloseReport": 990.0, "AdjCloseReportDate": "2026-08-29", "UpsideAdjPct": 17.62, "LocalDBStatus": "OK"}
    fpe = {"page_codes": [{"raw": "2330.TW", "core": "2330", "platform": "yfinance"}, {"raw": "2330 TT", "core": "2330", "platform": "bloomberg"}],
           "company_name_page": "TSMC"}
    listing = {"name": "台積電", "market": "TWSE", "yfinance_ticker": "2330.TW", "yf_source": "localdb.yf_ticker", "status": "OK"}
    rec = record_of(result, basic, fpe, listing)
    checks.append(("15 欄都有值、狀態、來源", list(rec.keys()) == [k for k, _z, _s in FIELDS] and all("state" in v and "source" in v for v in rec.values()), list(rec.keys())))
    checks.append(("YF 代號：資料庫＋首頁一致 = VERIFIED；Bloomberg 首頁印的；英文名從首頁", rec["yfinance_ticker"]["state"] == "VERIFIED" and rec["bloomberg_ticker"]["value"] == "2330 TT"
                   and rec["english_name"]["value"] == "TSMC" and rec["name"]["state"] == "VERIFIED", (rec["yfinance_ticker"], rec["english_name"])))
    checks.append(("資料庫欄：調整目標價、ADJ CLOSE、報告日前、上漲（印／算／調整）", rec["target_price_adj"]["value"] == 1188.0 and rec["adj_close"]["date"] == "2026-10-09"
                   and rec["adj_close_before_report"]["value"] == 990.0 and rec["upside_pct"]["calc"] == 20.0 and rec["upside_pct"]["adj"] == 17.62, rec["upside_pct"]))
    en_db = record_of(result, basic, {"company_name_page": "TSMC"}, dict(listing, name_en="TSMC"))
    zh_only = record_of({"file": "y.pdf", "status": "OK", "parts": [{"part": "title.ticker", "value": "2330", "state": "VERIFIED"},
                                                                   {"part": "title.company", "value": "台積電", "state": "VERIFIED"}]},
                        {}, {}, dict(listing, name_en="Taiwan Semiconductor Manufacturing"))
    checks.append(("英文名：資料庫有就取資料庫的；報告也印且一致 = VERIFIED，報告只印中文 = DB（不是 NOT_PRINTED）",
                   en_db["english_name"]["value"] == "TSMC" and en_db["english_name"]["state"] == "VERIFIED"
                   and zh_only["english_name"]["value"] == "Taiwan Semiconductor Manufacturing" and zh_only["english_name"]["state"] == "DB",
                   (en_db["english_name"], zh_only["english_name"])))
    bare = record_of({"file": "x.pdf", "status": "OK", "parts": [{"part": "title.ticker", "value": "6873", "state": "VERIFIED"}]}, {}, {}, {})
    checks.append(("沒有資料庫、首頁沒印：Bloomberg 推 TT、YF MISSING、英文名 NOT_PRINTED", bare["bloomberg_ticker"]["state"] == "DERIVED" and bare["yfinance_ticker"]["state"] == "MISSING"
                   and bare["english_name"]["state"] == "NOT_PRINTED", bare["yfinance_ticker"]))
    # 2026-10-20 實測：沒有本機資料庫時，首頁印的碼有**兩條**讀法（首頁引擎、TRIM），對上就該鎖得住。
    cover_codes = {"cover": {"fields": {"page_codes": {"codes": [{"raw": "2330.TW", "core": "2330", "platform": "yfinance", "market": "TWSE"},
                                                                 {"raw": "2330 TT", "core": "2330", "platform": "bloomberg", "market": ""}]}}}}
    two = record_of(dict(result, **cover_codes), {}, fpe, {})
    one = record_of(dict(result, **cover_codes), {}, {}, {})          # .txt 沒有首頁引擎結果：只有 TRIM 讀到
    clash = record_of(dict(result, cover={"fields": {"page_codes": {"codes": [{"raw": "2330.TWO", "core": "2330", "platform": "yfinance",
                                                                              "market": "TPEX"}]}}}), {}, fpe, {})
    checks.append(("沒有資料庫也鎖得住：首頁引擎＋TRIM 兩條讀法一致 = VERIFIED",
                   two["yfinance_ticker"]["state"] == "VERIFIED" and two["bloomberg_ticker"]["state"] == "VERIFIED"
                   and two["yfinance_ticker"]["value"] == "2330.TW", (two["yfinance_ticker"], two["bloomberg_ticker"])))
    checks.append(("只有 TRIM 讀到（.txt 沒有首頁引擎結果）：照實記 SINGLE「首頁印的」，不是 MISSING、也不是推算",
                   one["yfinance_ticker"]["state"] == "SINGLE" and one["bloomberg_ticker"]["state"] == "SINGLE"
                   and one["bloomberg_ticker"]["value"] == "2330 TT" and "印" in one["bloomberg_ticker"]["source"],
                   (one["yfinance_ticker"], one["bloomberg_ticker"])))
    checks.append(("兩條讀法讀出不同的碼 = CONFLICT（不挑一個當答案）",
                   clash["yfinance_ticker"]["state"] == "CONFLICT", clash["yfinance_ticker"]))
    db_clash = record_of(dict(result, cover={"fields": {"page_codes": {"codes": [{"raw": "2330.TWO", "core": "2330",
                                                                                  "platform": "yfinance", "market": "TPEX"}]}}}),
                         {}, fpe, listing)
    checks.append(("資料庫對上其中一條，也不能把兩條讀法互相不一致蓋掉（Codex PR #76 P2）",
                   db_clash["yfinance_ticker"]["state"] == "CONFLICT", db_clash["yfinance_ticker"]))
    with tempfile.TemporaryDirectory(prefix="vrn_record_") as td:
        rows = records_for_run([result], {result["file"]: basic}, {result["file"]: fpe})
        got = write_table(td, rows)
        back = json.loads(Path(got["json"]).read_text(encoding="utf-8"))
        checks.append(("表：一列一檔，15 欄 + 狀態欄 + 日期與重算欄；CSV 同列", got["rows"] == 1 and back[0]["ticker"] == "2330" and back[0]["adj_close_before_report_date"] == "2026-08-29"
                       and Path(got["csv"]).read_text(encoding="utf-8-sig").count("\n") == 2, got))
        try:
            import duckdb  # noqa: F401
            L = load_localdb_module()
            dbp = Path(td) / "vdf.duckdb"
            if hasattr(L, "build_fixture_db"):
                L.build_fixture_db(dbp)
                got_l = lookup_code_record("2330", db_path=str(dbp))
                checks.append(("lookup 四碼 → 資料庫 NAME／YF／Bloomberg／最新 ADJ CLOSE", got_l["status"] in ("OK", "NOT_IN_DB"), got_l))
            else:
                checks.append(("lookup（本機資料庫自測冊沒有固定資料；略過不算證明）", True, "no fixture"))
        except Exception as error:  # noqa: BLE001
            checks.append(("lookup（要 duckdb；略過不算證明）", True, f"{error.__class__.__name__}"))
    dividend = {"parts": [{"part": "cover.target_price", "value": 104.0, "state": "VERIFIED"},
                          {"part": "cover.current_price", "value": 90.0, "close": 96.9, "state": "VERIFIED", "source": "db"},
                          {"part": "cover.upside", "value": 7.3, "state": "SINGLE"}]}
    got_u = record_of(dividend)
    checks.append(("上漲% 的 calc 用原始收盤價，不用 adj（除權息過的股票 adj 90.0 vs close 96.9："
                   "用 close 算 7.33% 對得上報告印的 7.3%，用 adj 會算成 15.56%）",
                   got_u["upside_pct"]["calc"] == 7.33, got_u["upside_pct"]))
    bad = [c for c in checks if not c[1]]
    if verbose:
        for name, ok, detail in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f" · {str(detail)[:300]}"))
        print(f"[RECORD] {RECORD_VERSION} · {len(checks) - len(bad)}/{len(checks)}")
    return 0 if not bad else 1


# [VRN-ID] VRN-ENG017-FNC036 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(prog="VRN_TickerRecord_v0100.py", description="四碼代號 → 15 欄紀錄；合併冊")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("build-book", help="從倉內來源冊合併出 ssot/VRN_TickerRecord_SSOT_v0100.json")
    p_l = sub.add_parser("lookup", help="四碼代號查本機資料庫")
    p_l.add_argument("code")
    p_l.add_argument("--db", default="", help="vdf_tw_market.duckdb 路徑")
    p_r = sub.add_parser("record", help="把一次實測的 G17 結果做成紀錄表")
    p_r.add_argument("--out", required=True)
    p_r.add_argument("--db", default="")
    sub.add_parser("selftest")
    args = parser.parse_args(argv)
    if args.command == "build-book":
        path, book = write_book()
        c = book["merge"]["counts"]
        print(f"[RECORD-BOOK] {path} · 券商別名 {c['broker_aliases']}（折 {c['broker_folded']}）· 網域 {c['email_domains']} · 評等詞 {c['rating_words']} · "
              f"regex {c['regex']}（折 {c['regex_folded']}）· 衝突 {c['conflicts']}")
        return 0
    if args.command == "lookup":
        print(json.dumps(lookup_code_record(args.code, db_path=args.db or None), ensure_ascii=False, indent=1))
        return 0
    if args.command == "record":
        run = Path(args.out)
        rp = sorted(run.glob("autotest/round*/titletrim/VRN_TitleTrim_Results_v0100.json"))
        if not rp:
            print("[RECORD] 沒有 G17 結果")
            return 1
        results = json.loads(rp[-1].read_text(encoding="utf-8"))
        rows = records_for_run(results, {}, {}, args.db or None)
        got = write_table(rp[-1].parent, rows)
        print(f"[RECORD] {got['rows']} 檔 · {got['json']}")
        return 0
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
