#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG007 · VRN_BookCheck_v0100 v0100 · MEASURE 收來的冊當量尺 =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 24；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_BookCheck v0100 -- the books harvested from the other sessions, used as test instruments.

Operator 2026-10-10: 「擷取其他對話中的 BROKER DICT RATING LIST TARGET PRICE DICT EMAIL TEL 所有 FINANCIAL ACCOUNT
AND VALIDATION METHOD 快整合進入實測階段」.

The books are VRN-owned byte copies in ssot/ (where each came from: ssot/VRN_BOOKS_PROVENANCE_v0100.json):

  VRN_S05_FieldRegistry_v0103.json        rating list, target-price dict, e-mail domain -> broker, 40 regexes with
                                          their own pass/fail examples, 30 basic + 76 financial fields, each with
                                          regex / synonyms / validation method / tolerance
  VRN_Broker_Dict_v0103.json              28 canonical brokers with Chinese / English names, aliases, domain aliases
  VIA_VRN_ReportFieldRules_SSOT_v0101.json  phone order TPE -> HK -> HK mobile (weak) -> TW mobile -> INTL + guard
  VRN_FieldRules_SSOT_v0101.json          financial identities (GP_SUB, GM_DIV, OP_SUB, OPM_DIV, NM_DIV, BS_ADD, EPS_DIV)
  VIA_VRN_ExtractRules_SSOT_v0100.json    R-CMP-01 tolerances (target price 0.5 %, revenue 1 %, EPS 1 %)
  VRN_FinLexicon_SSOT_v0109.json          76 financial accounts (zh / en), noise rules
  VIA_SSOT_SynonymUnion_v0107.json        fin_account scope (632 synonyms) and rating scope
  VIA_VRN_FieldSpec_SSOT_v0100.json       the 15 columns and their states (GREEN needs 95 %)

This module never changes an engine answer.  It reads each answer back against the books and names the
state: AGREE / DISAGREE / BOOK_ONLY / ENGINE_ONLY / NOT_IN_BOOK / NONE.  Ratings are compared as printed
words (operator 2026-10-10: no classification); mainland brokers are VRN's own as-printed list, which the
mother books deny, so they are VRN_OWN here, never a disagreement.

Stdlib only.  LIVE off, no network, never sets VIA_NET_CONSENT / VIA_SCRAPE_CONSENT.
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
import json
import os
import re
import sys
from collections import Counter, defaultdict

BOOKCHECK_VERSION = "v0100"
SSOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ssot")
BOOK_FILES = {
    "s05": "VRN_S05_FieldRegistry_v0103.json",
    "broker": "VRN_Broker_Dict_v0103.json",
    "contact": "VIA_VRN_ReportFieldRules_SSOT_v0101.json",
    "field_rules": "VRN_FieldRules_SSOT_v0101.json",
    "extract": "VIA_VRN_ExtractRules_SSOT_v0100.json",
    "lexicon": "VRN_FinLexicon_SSOT_v0109.json",
    "union": "VIA_SSOT_SynonymUnion_v0107.json",
    "field_spec": "VIA_VRN_FieldSpec_SSOT_v0100.json",
}
GREEN_AT = 0.95                      # VIA_VRN_FieldSpec_SSOT: GREEN needs 95 % (94 % is PARTIAL)
YEAR_PAIR_RX = re.compile(r"(?:19|20)\d{2}(?:19|20)\d{2}")   # operator run 2026-10-11: '20252026' read as a phone
TP_TOL_DEFAULT = 0.005               # ExtractRules R-CMP-01 target_price, used when the book is absent
# engine MetricName -> FieldRules identity operand
IDENTITY_OPERANDS = {"Revenue": "revenue", "COGS": "cogs", "GrossProfit": "gross_profit",
                     "GrossMargin": "gross_margin", "OperatingExpense": "opex",
                     "OperatingProfit": "op_profit", "OperatingMargin": "op_margin",
                     "NetIncome": "net_income", "NetMargin": "net_margin", "EPS": "eps",
                     "SharesOutstanding": "shares", "TotalAssets": "total_assets",
                     "TotalLiabilities": "total_liabilities", "Equity": "equity"}
_REGEX_HINT = re.compile(r"\\[sdwbS]|\(\?|\[[^\]]+\]|[*+?]\)?|\|")


# [VRN-ID] VRN-ENG007-FNC001 · IO
def read_json(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return None


# [VRN-ID] VRN-ENG007-FNC022 · LOGIC
def local_ssot_dir():
    """The operator's local VRN SSOT folder (via_02_vrn\\03_ssot), read-only; VRN_LOCAL_SSOT overrides, "" turns it off."""
    env = os.environ.get("VRN_LOCAL_SSOT")
    if env is not None:
        return env if env and os.path.isdir(env) else None
    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    path = os.path.join(home, "OneDrive", "Documents", "VeritasIntelligenceAnalytics", "via_02_vrn", "03_ssot")
    return path if os.path.isdir(path) else None


# [VRN-ID] VRN-ENG007-FNC023 · LOGIC
def _version(name):
    m = re.search(r"_v(\d+)\.json$", name)
    return int(m.group(1)) if m else -1


# [VRN-ID] VRN-ENG007-FNC024 · LOGIC
def newest(name, folders):
    """(path, folder label) of the newest version of the book family `name` belongs to ("...X_v0109.json" -> "...X_v*.json"),
    over the folders in order; a tie keeps the earlier folder.  `.integration.json` reports are not books."""
    family = re.sub(r"_v\d+\.json$", "", name)
    best = None
    for label, folder in folders:
        if not folder or not os.path.isdir(folder):
            continue
        for entry in os.listdir(folder):
            if entry.startswith(family + "_v") and entry.endswith(".json") and ".integration." not in entry and _version(entry) >= 0:
                if best is None or _version(entry) > _version(os.path.basename(best[0])):
                    best = (os.path.join(folder, entry), label)
    return best


# [VRN-ID] VRN-ENG007-FNC002 · IO
def load_books(ssot_dir=None, local=True):
    """Every book, newest version of each family (2026-10-11: VRN ssot/, ssot/03_ssot/, and the operator's local
    03_ssot when present and `local`): {"books", "paths", "sources", "missing"}."""
    folder = ssot_dir or SSOT_DIR
    folders = [("VRN ssot", folder), ("VRN ssot/03_ssot", os.path.join(folder, "03_ssot"))]
    if local and ssot_dir is None and local_ssot_dir():
        folders.append(("本機 03_ssot", local_ssot_dir()))
    books, paths, sources, missing = {}, {}, {}, []
    for key, name in BOOK_FILES.items():
        hit = newest(name, folders)
        data = read_json(hit[0]) if hit else None
        if data is None:
            missing.append(name)
        else:
            books[key], paths[key], sources[key] = data, hit[0], hit[1]
    return {"books": books, "paths": paths, "sources": sources, "missing": missing}


# [VRN-ID] VRN-ENG007-FNC003 · LOGIC
def _get(node, *path, default=None):
    for part in path:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node


# [VRN-ID] VRN-ENG007-FNC004 · LOGIC
def _dotted(book, dotted):
    """'contact_block.corrected.tpe_phone' -> the string at that path, or None."""
    return _get(book, *dotted.split("."))


# [VRN-ID] VRN-ENG007-FNC005 · LOGIC
def _compile(pattern, flags=0):
    try:
        return re.compile(pattern, flags)
    except (re.error, TypeError):
        return None


# =====================================================================
# 1 . THE BOOKS CHECK THEMSELVES
# =====================================================================
# [VRN-ID] VRN-ENG007-FNC006 · LOGIC
def book_selftest(loaded):
    """S05: every regex against its own pass / fail examples; the contact book: every phone pattern compiles in
    Python.  A book that contradicts itself is the book's defect, so the caller shows it, it does not fix it."""
    books = loaded["books"]
    out = []
    regs = _get(books.get("s05") or {}, "all_regex", default={}) or {}
    n_ex, bad = 0, []
    for name, spec in regs.items():
        rx = _compile(spec.get("pattern"))
        if rx is None:
            bad.append(name + ": does not compile")
            continue
        for ex in spec.get("examples_pass", []) or []:
            n_ex += 1
            if not rx.search(ex):
                bad.append(f"{name}: misses its own pass example {ex!r}")
        for ex in spec.get("examples_fail", []) or []:
            n_ex += 1
            if rx.search(ex):
                bad.append(f"{name}: hits its own fail example {ex!r}")
    out.append({"book": BOOK_FILES["s05"], "name": f"{len(regs)} regexes x {n_ex} own examples", "ok": not bad and bool(regs),
                "detail": "; ".join(bad[:8]) if bad else ("" if regs else "book absent")})
    contact = books.get("contact") or {}
    uses = _get(contact, "phone", "use", default=[]) or []
    broken = []
    for use in uses:
        src = str(use.get("from") or "")
        pattern = _get(books.get("field_rules") or {}, *src.split("#", 1)[1].split(".")) if "#" in src else _dotted(contact, src)
        if not isinstance(pattern, str) or _compile(pattern) is None:
            broken.append(str(use.get("id")))
    out.append({"book": BOOK_FILES["contact"], "name": f"{len(uses)} phone patterns (order {' > '.join(str(u.get('id')) for u in uses)}) compile",
                "ok": bool(uses) and not broken, "detail": ", ".join(broken) if broken else ("" if uses else "book absent")})
    return out


# =====================================================================
# 2 . BROKER / E-MAIL / PHONE / RATING / TARGET PRICE ON ONE FIRST PAGE
# =====================================================================
# [VRN-ID] VRN-ENG007-CLS001 · CLASS
class Books:
    """The loaded books with the lookups built once."""

    # [VRN-ID] VRN-ENG007-FNC007 · INIT
    def __init__(self, loaded=None, vrn_own_brokers=None):
        self.loaded = loaded or load_books()
        b = self.loaded["books"]
        self.vrn_own = {str(k).upper() for k in (vrn_own_brokers or ())}
        # broker canon <- every alias / name / abbr (lower case)
        self.broker_keys = set()
        self.broker_alias = {}
        for key, entry in (_get(b.get("broker") or {}, "brokers", default={}) or {}).items():
            k = str(key).upper()
            self.broker_keys.add(k)
            names = [key, entry.get("abbr"), entry.get("chinese_name"), entry.get("english_name")] + list(entry.get("aliases") or [])
            for n in names:
                if n:
                    self.broker_alias.setdefault(str(n).strip().lower(), k)
        s05 = b.get("s05") or {}
        self.domain_map = {}
        for dom, spec in (_get(s05, "email_domain_to_broker", default={}) or {}).items():
            self.domain_map[dom.lower()] = (spec or {}).get("broker") or (spec or {}).get("broker_en")
        for dom, name in (_get(b.get("contact") or {}, "broker_domains_addendum", "map", default={}) or {}).items():
            self.domain_map.setdefault(dom.lower(), name)
        rx = _get(s05, "all_regex", default={}) or {}
        self.rx_email = _compile(_get(rx, "EMAIL_FULL", "pattern", default=r"[A-Za-z][A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"))
        self.rx_email_any = _compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
        self.rx_tp = [r for r in (_compile(_get(rx, n, "pattern", default="")) for n in
                                  ("TARGET_PRICE_LABEL", "TARGET_PRICE_VERB", "TARGET_PRICE_TAIL")) if r is not None and r.pattern]
        prev = _get(s05, "target_price_dict", "stopwords_previous", default=[]) or []
        self.rx_prev = _compile("(?:" + "|".join(re.escape(w) for w in sorted(prev, key=len, reverse=True)) + r")\W{0,3}$", re.I) if prev else None
        self.tp_tol = float(next((r.get("tolerance", {}).get("target_price") for r in _get(b.get("extract") or {}, "rules", default=[]) or []
                                  if r.get("id") == "R-CMP-01"), None) or TP_TOL_DEFAULT)
        # phones: the contact book's order and guard; Taiwan masked before Hong Kong
        contact = b.get("contact") or {}
        field_rules = b.get("field_rules") or {}
        self.phone_rx = []
        for use in _get(contact, "phone", "use", default=[]) or []:
            src = str(use.get("from") or "")
            pattern = _get(field_rules, *src.split("#", 1)[1].split(".")) if "#" in src else _dotted(contact, src)
            rx_one = _compile(pattern) if isinstance(pattern, str) else None
            if rx_one is not None:
                self.phone_rx.append((use.get("id"), use.get("grade"), rx_one))
        self.phone_cue = _compile(_get(contact, "phone", "guard", "cue_rx", default=r"電\s*話|Tel\.?|TEL|Phone|分機|ext\.?|Fax"))
        # rating words: every list the books carry (detection only; nothing is classified)
        words = set(w.lower() for w in _get(s05, "rating_list", "flat_list_for_matching", default=[]) or [])
        for vals in (_get(field_rules, "rules", "rating", "canon_map", default={}) or {}).values():
            words.update(str(w).lower() for w in vals or [])
        for word, rows in (_get(b.get("union") or {}, "scopes", "rating", default={}) or {}).items():
            if not any((r or {}).get("namespace") == "field_code" for r in rows or []):
                words.add(str(word).lower())
        self.rating_words = {w for w in words if w}
        # financial accounts: FinLexicon rows, S05 financial fields, union fin_account scope
        self.account_terms = []          # (term_lower, std, is_regex)
        for row in _get(b.get("lexicon") or {}, "rows", default=[]) or []:
            for t in list(row.get("zh") or []) + list(row.get("en") or []):
                self.account_terms.append((str(t).lower(), row.get("std"), False))
        for f in _get(s05, "financialdata_fields", default=[]) or []:
            for t in _get(f, "validation_layers", "synonyms", default=[]) or []:
                self.account_terms.append((str(t).lower(), f.get("data_official_en"), False))
        for term, rows in (_get(b.get("union") or {}, "scopes", "fin_account", default={}) or {}).items():
            canon = (rows or [{}])[0].get("canonical")
            if _REGEX_HINT.search(term):
                rx_term = _compile(term, re.I)
                if rx_term is not None:
                    self.account_terms.append((rx_term, canon, True))
            else:
                self.account_terms.append((term.lower(), canon, False))
        self.account_terms.sort(key=lambda x: -len(x[0].pattern if x[2] else x[0]))
        self.noise = [r for r in (_compile(p) for p in (_get(b.get("lexicon") or {}, "noise_rules", default={}) or {}).values()) if r]
        self.identities = _get(field_rules, "rules", "financial", "verify", "identities", default=[]) or []

    # ---- broker ------------------------------------------------------
    # [VRN-ID] VRN-ENG007-FNC008 · LOGIC
    def broker_of(self, name):
        """A broker key, name or alias -> the book's canonical key (None when the book does not know it)."""
        if not name:
            return None
        n = str(name).strip()
        if n.upper() in self.broker_keys:
            return n.upper()
        return self.broker_alias.get(n.lower())

    # [VRN-ID] VRN-ENG007-FNC009 · LOGIC
    def broker_of_domain(self, domain):
        """2026-10-11: a domain the e-mail books name with a key the broker book does not have (daiwacm-cathay.com.tw ->
        'DAIWA-CATHAY') is first looked up in the broker book's own domain aliases (daiwacm-cathay -> DAIWA): the broker book
        is the canon for brokers.  Only when neither knows it is the e-mail book's name returned as it is."""
        dom = (domain or "").lower().strip(".")
        parts = dom.split(".")
        named = None
        for i in range(len(parts) - 1):
            hit = self.domain_map.get(".".join(parts[i:]))
            if hit:
                known = self.broker_of(hit)
                if known:
                    return known
                named = str(hit).upper()
                break
        for label in parts[:-1]:                       # Broker_Dict domain aliases: kgieworld, entrust, cl-sec ...
            hit = self.broker_alias.get(label)
            if hit:
                return hit
        return named

    # ---- page readers --------------------------------------------------
    # [VRN-ID] VRN-ENG007-FNC010 · LOGIC
    def emails(self, lines):
        out = []
        for i, line in enumerate(lines or []):
            for m in self.rx_email_any.finditer(line or ""):
                addr = m.group(0)
                local, _, dom = addr.partition("@")
                named = bool(self.rx_email and self.rx_email.fullmatch(addr))
                out.append({"email": addr, "line": i, "named": named, "domain": dom.lower(),
                            "broker": self.broker_of_domain(dom)})
        return out

    # [VRN-ID] VRN-ENG007-FNC011 · LOGIC
    def phones(self, lines):
        """The contact book's order; each later pattern only reads what the earlier ones left (no conflict)."""
        out = []
        for i, line in enumerate(lines or []):
            text = line or ""
            cue = bool(self.phone_cue and self.phone_cue.search(text))
            for pid, grade, rx in self.phone_rx:
                for m in rx.finditer(text):
                    raw = m.group(0)
                    digits = re.sub(r"\D", "", raw)
                    if not 8 <= len(digits) <= 15:
                        continue
                    if YEAR_PAIR_RX.fullmatch(digits):     # 2026-10-11: '2025-2026' is a span of years, not a phone
                        continue
                    strong = grade != "WEAK_ONLY" and (cue or bool(re.search(r"[+(\-]", raw)))
                    out.append({"id": pid, "raw": raw.strip(), "digits": digits, "line": i, "grade": "HIT" if strong else "WEAK"})
                    text = text[:m.start()] + " " * (m.end() - m.start()) + text[m.end():]
        return out

    # [VRN-ID] VRN-ENG007-FNC012 · LOGIC
    def target_prices(self, lines):
        out = []
        for i, line in enumerate(lines or []):
            for rx in self.rx_tp:
                for m in rx.finditer(line or ""):
                    if self.rx_prev and self.rx_prev.search((line or "")[max(0, m.start() - 16):m.start()]):
                        continue
                    num = next((g for g in m.groups() if g and re.search(r"\d", g)), None) if m.groups() else None
                    try:
                        value = float(str(num).replace(",", "")) if num else None
                    except ValueError:
                        value = None
                    if value is not None and value > 0:
                        out.append({"value": value, "line": i, "text": m.group(0)[:60]})
        return out

    # [VRN-ID] VRN-ENG007-FNC013 · LOGIC
    def rating_in_book(self, text):
        if not text:
            return "NONE"
        t = str(text).strip().lower()
        if t in self.rating_words:
            return "IN_BOOK"
        return "IN_BOOK_PART" if any(w in t for w in self.rating_words if len(w) >= 2) else "NOT_IN_BOOK"

    # ---- one first page ------------------------------------------------
    # [VRN-ID] VRN-ENG007-FNC014 · VALIDATE
    def check_first_page(self, fp):
        """fp: {"broker", "rating", "target_price", "emails", "tel", "lines"} -> {field: {"state", "detail"}}."""
        lines = fp.get("lines") or []
        res = {}
        broker = fp.get("broker")
        book_key = self.broker_of(broker)
        if not broker:
            res["broker"] = {"state": "NONE", "detail": ""}
        elif str(broker).upper() in self.vrn_own:
            res["broker"] = {"state": "VRN_OWN", "detail": f"{broker}: VRN's as-printed mainland list (the mother book denies it)"}
        else:
            res["broker"] = {"state": "IN_BOOK" if book_key else "NOT_IN_BOOK", "detail": str(broker) if not book_key else ""}
        mails = self.emails(lines)
        mapped = [m for m in mails if m["broker"]]
        if not mails:
            res["email"] = {"state": "NO_EMAIL", "detail": ""}
        else:
            numeric = [m["email"] for m in mails if not m["named"]]
            res["email"] = {"state": "NAMED" if len(numeric) < len(mails) else "UNVERIFIABLE",
                            "detail": (f"{len(mails)} e-mail(s); staff-id / role mailbox: " + ", ".join(numeric[:3])) if numeric else f"{len(mails)} e-mail(s)"}
        if not mapped or not broker:
            res["email_broker"] = {"state": "UNMAPPED" if mails else "NO_EMAIL", "detail": ", ".join(m["domain"] for m in mails[:3])}
        else:
            doms = {m["broker"] for m in mapped}
            own = book_key or str(broker).upper()
            res["email_broker"] = {"state": "AGREE" if own in doms else "DISAGREE",
                                   "detail": "" if own in doms else f"page {broker} vs domain " + ", ".join(sorted(doms))}
        book_tel = {p["digits"] for p in self.phones(lines) if p["grade"] == "HIT"}
        eng_tel = {re.sub(r"\D", "", str(t)) for t in (fp.get("tel") or [])}
        only_book = sorted(book_tel - eng_tel)
        if not book_tel and not eng_tel:
            res["tel"] = {"state": "NONE", "detail": ""}
        elif only_book:
            res["tel"] = {"state": "BOOK_ONLY", "detail": "book reads " + ", ".join(only_book[:3]) + " the engine did not"}
        elif not book_tel:
            res["tel"] = {"state": "ENGINE_ONLY", "detail": ", ".join(sorted(eng_tel)[:3])}
        else:
            res["tel"] = {"state": "AGREE", "detail": f"{len(book_tel)} phone(s)"}
        res["rating"] = {"state": self.rating_in_book(fp.get("rating")), "detail": str(fp.get("rating") or "")}
        tps = [t["value"] for t in self.target_prices(lines)]
        tp = fp.get("target_price")
        if tp in (None, "") and not tps:
            res["target_price"] = {"state": "NONE", "detail": ""}
        elif tp in (None, ""):
            res["target_price"] = {"state": "BOOK_ONLY", "detail": "book reads " + ", ".join(f"{v:g}" for v in tps[:3])}
        elif not tps:
            res["target_price"] = {"state": "ENGINE_ONLY", "detail": f"{float(tp):g}"}
        else:
            ok = any(abs(v - float(tp)) <= self.tp_tol * max(abs(float(tp)), 1e-9) for v in tps)
            res["target_price"] = {"state": "AGREE" if ok else "DISAGREE",
                                   "detail": "" if ok else f"engine {float(tp):g} vs book " + ", ".join(f"{v:g}" for v in tps[:3])}
        return res

    # ---- financial tables ------------------------------------------------
    # [VRN-ID] VRN-ENG007-FNC015 · LOGIC
    def account_of(self, label):
        """A row label -> the books' account (None = no book names it; 'NOISE' = not a row label)."""
        raw = re.sub(r"\s+", " ", str(label or "")).strip()
        if not raw or re.fullmatch(r"[\d\W_]+", raw):
            return "NOISE"
        if any(rx.search(raw) for rx in self.noise):
            return "NOISE"
        low = raw.lower()
        for term, canon, is_rx in self.account_terms:
            if (is_rx and term.search(raw)) or (not is_rx and term and term in low):
                return canon or "?"
        return None

    # [VRN-ID] VRN-ENG007-FNC016 · VALIDATE
    def check_accounts(self, fin_rows):
        labels = {}
        for r in fin_rows or []:
            raw = str(r.get("MetricNameRaw") or "").strip()
            if raw:
                labels.setdefault(raw, bool(r.get("MetricName")))
        tally = Counter()
        extra, unknown = [], []
        for raw, engine_named in labels.items():
            acct = self.account_of(raw)
            if acct == "NOISE":
                tally["noise"] += 1
            elif engine_named:
                tally["engine_named"] += 1
            elif acct:
                tally["book_only"] += 1
                extra.append(f"{raw} -> {acct}")
            else:
                tally["unknown"] += 1
                unknown.append(raw)
        return {"labels": len(labels), "tally": dict(tally), "book_only": extra, "unknown": unknown}

    # [VRN-ID] VRN-ENG007-FNC017 · VALIDATE
    def check_identities(self, fin_rows):
        """FieldRules v0101 identities on every (report, period) bucket; INSUFFICIENT when an operand is missing."""
        buckets = defaultdict(dict)
        for r in fin_rows or []:
            op = IDENTITY_OPERANDS.get(r.get("MetricName"))
            if not op or r.get("Value") in (None, ""):
                continue
            key = (r.get("ReportID"), r.get("TableID"), r.get("PeriodLabelRaw") or r.get("FiscalYear"))
            try:
                buckets[key].setdefault(op, float(r["Value"]))
            except (TypeError, ValueError):
                continue
        tally = defaultdict(Counter)
        fails = []
        for key, vals in buckets.items():
            for ident in self.identities:
                state = identity_state(ident, vals)
                tally[ident["id"]][state] += 1
                if state == "FAIL" and len(fails) < 12:
                    fails.append(f"{key[0]}/{key[2]} {ident['id']}")
        return {"buckets": len(buckets), "tally": {k: dict(v) for k, v in tally.items()}, "fails": fails}


# [VRN-ID] VRN-ENG007-FNC018 · LOGIC
def identity_state(ident, vals):
    """PASS / FAIL / UNIT_SCALE / INSUFFICIENT / DIV_ZERO, as the FieldRules v0101 identity_states define them."""
    a, b, target = vals.get(ident.get("a")), vals.get(ident.get("b")), vals.get(ident.get("target"))
    if a is None or b is None or target is None:
        return "INSUFFICIENT"
    op = ident.get("op")
    if op in ("div", "div_pct") and b == 0:
        return "DIV_ZERO"
    expect = {"sub": a - b, "add": a + b, "div": (a / b) if b else None, "div_pct": (a / b * 100.0) if b else None}.get(op)
    if expect is None:
        return "INSUFFICIENT"
    if "tol_abs_pp" in ident:
        if abs(target - expect) <= float(ident["tol_abs_pp"]):
            return "PASS"
        return "UNIT_SCALE" if abs(target * 100.0 - expect) <= float(ident["tol_abs_pp"]) else "FAIL"
    tol = float(ident.get("tol_rel", 0.01))
    return "PASS" if abs(target - expect) <= tol * max(abs(expect), 1e-9) else "FAIL"


# [VRN-ID] VRN-ENG007-FNC019 · LOGIC
def field_state(have, total, wired=True, pending=False, gated=False):
    """The six states as VIA_VRN_FieldSpec_SSOT writes them (same order as CGC_MDL181 v0100), for runs where the
    VCGC tool is not mirrored: not wired > source pending > needs network > no data > enough."""
    if not wired:
        return "NOT_WIRED"
    if pending:
        return "SOURCE_PENDING"
    if total <= 0:
        return "NODATA"
    if have <= 0:
        return "GATED" if gated else "NODATA"
    if have >= total * GREEN_AT:
        return "GREEN"
    return "GATED" if gated else "PARTIAL"


# =====================================================================
# 3 . SELF-TEST AND CLI
# =====================================================================
# [VRN-ID] VRN-ENG007-FNC020 · ENTRY
def selftest():
    loaded = load_books()
    if loaded["missing"]:
        print("[BOOKCHECK] books missing: " + ", ".join(loaded["missing"]))
        return 1
    bk = Books(loaded, vrn_own_brokers=("GF",))
    checks = [(row["name"], row["ok"]) for row in book_selftest(loaded)]
    page = ["凱基證券 研究部", "分析師 王小明 Tel: (02) 2181-8888", "xiaoming.wang@kgi.com", "目標價: NT$1,100",
            "評等: 買進"]
    res = bk.check_first_page({"broker": "KGI", "rating": "買進", "target_price": 1100.0, "tel": ["(02) 2181-8888"], "lines": page})
    checks += [("broker KGI in book", res["broker"]["state"] == "IN_BOOK"),
               ("kgi.com agrees with KGI", res["email_broker"]["state"] == "AGREE"),
               ("TP NT$1,100 read whole", res["target_price"]["state"] == "AGREE"),
               ("phone read", res["tel"]["state"] == "AGREE"),
               ("買進 in the rating book", res["rating"]["state"] == "IN_BOOK"),
               ("GF is VRN's own", bk.check_first_page({"broker": "GF"})["broker"]["state"] == "VRN_OWN"),
               ("營業收入 is an account", bk.account_of("營業收入淨額") not in (None, "NOISE")),
               ("GP = Rev - COGS", identity_state({"op": "sub", "a": "revenue", "b": "cogs", "target": "gross_profit", "tol_rel": 0.02},
                                                  {"revenue": 100.0, "cogs": 60.0, "gross_profit": 40.0}) == "PASS"),
               ("40 vs 0.40 is UNIT_SCALE", identity_state({"op": "div_pct", "a": "gross_profit", "b": "revenue", "target": "gross_margin",
                                                            "tol_abs_pp": 0.5}, {"gross_profit": 40.0, "revenue": 100.0, "gross_margin": 0.40}) == "UNIT_SCALE"),
               ("95 % is GREEN, 94 % PARTIAL", field_state(95, 100) == "GREEN" and field_state(94, 100) == "PARTIAL")]
    unwired = sorted({o for ident in bk.identities for o in (ident.get("target"), ident.get("a"), ident.get("b"))
                      if o and o not in set(IDENTITY_OPERANDS.values())})
    checks.append((f"冊上每個恆等式運算元都接得到 MetricName（沒接到的：{unwired or '無'}）", not unwired))
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    failed = sum(1 for _, ok in checks if not ok)
    print(f"[BOOKCHECK] {BOOKCHECK_VERSION} · {len(checks) - failed}/{len(checks)}")
    return 1 if failed else 0


# [VRN-ID] VRN-ENG007-FNC021 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(description="VRN BookCheck: the harvested books as test instruments")
    parser.add_argument("command", nargs="?", default="selftest", choices=("selftest", "books"))
    args = parser.parse_args(argv)
    if args.command == "books":
        loaded = load_books()
        for key, name in BOOK_FILES.items():
            print(f"  {'OK ' if key in loaded['books'] else 'MISSING'} {key:12s} {name}")
        return 1 if loaded["missing"] else 0
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
