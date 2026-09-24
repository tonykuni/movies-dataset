# -*- coding: utf-8 -*-
"""
VIA_VRN_FirstPageEngine  v0102
ALL-IN-ONE engine consolidating the VRN first-page extraction & cross-validation logic.

Modules (single file, one entry point `FirstPageEngine.run`):
  1 SSOT loader          - load _RAW_REGEX/_RAW_SYNONYMS from SSOT .py, else locked fallback;
                           v0102: broker dict / rating dict / SYNONYM_LIBRARY / ticker master (graceful)
  2 TickerFilename       - protect date / tri-code / ETF / quarter / KY fragments first, then
                           tokenize by CJK|LATIN|DIGIT boundaries; 4-digit ticker vs 2021-2030
                           year band; ROC 7-digit, (20)yymmdd, yymmdd, CTBC0915 (YEAR_MISSING);
                           tri-code cross-check with PASS / MISMATCH / MARKET_MISMATCH /
                           INSUFFICIENT_EVIDENCE verdicts; email->analyst/broker
  3 Layout               - font-hierarchy (MAIN_TITLE..FOOTER), element_type, boilerplate,
                           company-name (largest+bold), sentence linking (break at period)
  4 TableGeometry        - reconstruct hidden-gridline tables via x/y clustering, period headers
  5 NLPRepair            - local heuristic sentence repair (hook to swap in via_nlp v1.5);
                           v0102: never touches digits / decimals / signs / percentages
  6 FinancialValidation  - Add/Sub tolerance layering, Division two-stage, Historical YoY;
                           v0102: spec identities (assets, gross profit, margins, diluted EPS,
                           annual = quarters) with abs 0.01 / rel 0.5% tolerances
  7 PriceAdjustment      - adjusted-price consistency, upside on a comparable basis
  8 CrossValidation      - filename <-> text <-> table <-> financials
  9 FourPointSummary     - spec section 5 data contract (header + four points, DERIVED upside)
Governance: append-only; raw + repaired coexist; TABLE/FIGURE never enter NLP; LIVE off;
no network; nothing here ever sets VIA_NET_CONSENT / VIA_SCRAPE_CONSENT.

v0102 changes (auto-test loop, 2026-09-21):
  - ROC 7-digit dates (1141202 -> 2025-12-02), (20)260131 prefix join, calendar validation
    (20250230 rejected), CTBC0915 -> month/day + YEAR_MISSING, 926708 stays an unclassified number,
    006208 is an ETF format candidate and never a date.
  - 2021..2030 four-digit tokens are a year band, not a ticker, unless the official set says so.
  - Broker matching: ASCII aliases need letter boundaries (MS never matches "systems"), CJK aliases
    are substrings, longest alias wins, company fragments right after the ticker are excluded
    (凱基投顧_2891 中信金 -> KGI), GFHK is not GF.
  - Rating: single/double letter codes only inside a rating structure, actions (維持/調升/調降/重申)
    are separate from the rating value, "Note" is not NOT_RATED, strong/soft variants keep both
    candidates (SOURCE_REQUIRED) with a coarse canonical for compatibility.
  - Target price: synonym scope + price context, percentages and multiples excluded, Base/Bull/Bear
    scenarios kept in separate fields; current price never reads "Target Price".
  - Knowledge wiring: attachments/VRN_Broker_Dict_v0100.json, attachments/VRN_Rating_Dict_v0100.json,
    knowledge/SYNONYM_LIBRARY_v4.json, VIA_TW_Ticker_Master_v0210.py (all optional, all graceful).
  - CLI: --filename / --pdf / --docx / --json.

v0104 (mother 批729; operator 2026-09-24 "報告後小字體不相關附錄可抓到局部識別券商"):
  run(..., source_path=) reads the appendix small print of the last pages through VRN_Evidence_Core.appendix_evidence
  (same deny gate).  It fills the broker ONLY when page 1 has no strong evidence (EMAIL / DISCLOSURE / ISSUER);
  broker_tier then reads APPENDIX_<tier>.  An appendix issuer that disagrees with the filename broker is kept as
  broker_conflict (REVIEW), never a silent win.  out["appendix"]["rating_scale"] carries the harvested rating
  definitions (candidates only; no book is written).  --pdf passes its path.
  Operator 2026-09-24 "所有目標價及各前一日的價格都要換成ADJ CLOSE 上漲空間都要用最新的ADJ CLOSE":
  out["upside"] is now the mother's L99 answer through VRN_Evidence_Core.adj_basis (ENG073 adj_quote): target x
  adj factor over the LATEST adj close, basis ADJ_LATEST, status DERIVED_ADJ or NO_ADJ with the reason; it also
  carries the target and the day-before prices in ADJ CLOSE terms (target_price_adj, price_prev_adj, page_price_adj).
  The page arithmetic (target / printed price) is kept as out["upside_page"], labelled as what it is (v0103 said
  "latest adjusted close" but divided by the printed price).  A non-TWD target is never put on the TW adj close.
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

import re, os, sys, json, unicodedata, statistics, datetime
from collections import defaultdict

ENGINE_VERSION = "v0104"


_CORE_MODNAME = "vrn_engine_evidence_core"


def _load_evidence_core():
    """VRN_Evidence_Core (same folder): one rule set for both engines; None keeps the v0102 behaviour.
    Mother 批728: cached under a unique module name and reused only when it IS the sibling file -- the mother
    also keeps an older intake VRN_Evidence_Core.py (audit package v0.2.0) that a plain `import
    VRN_Evidence_Core` elsewhere in the same process would bind; the engine must never pick that one up."""
    try:
        import importlib.util
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VRN_Evidence_Core.py")
        cached = sys.modules.get(_CORE_MODNAME)
        if cached is not None and os.path.abspath(getattr(cached, "__file__", "") or "") == os.path.abspath(path):
            return cached
        if not os.path.isfile(path):
            return None
        spec = importlib.util.spec_from_file_location(_CORE_MODNAME, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[_CORE_MODNAME] = mod
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


EVIDENCE_CORE = _load_evidence_core()

# =====================================================================
# 1 · SSOT LOADER
# =====================================================================
_LOCK = {
    "TW_STOCK_CODE_4DIGIT": r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
    "TW_YFINANCE_TICKER":   r"([1-9]\d{3})\.(TW|TWO)",
    "TW_BLOOMBERG_TICKER":  r"([1-9]\d{3})\s+TT",
}

YEAR_BAND = (2021, 2030)
ETF_CODE_RE = re.compile(r"^(?:00\d{2,4}|00\d{3}[A-Z]|00\d[A-Z]\d{2})$")
SHORT_RATING_CODES = {"B", "H", "S", "N", "OW", "EW", "UW", "MP", "OP", "NR", "SB", "SS", "CD", "UP"}
RATING_ACTIONS = {
    "UPGRADE": ("調升", "升評", "上調", "upgrade", "upgraded"),
    "DOWNGRADE": ("調降", "降評", "下調", "downgrade", "downgraded"),
    "MAINTAIN": ("維持", "重申", "maintain", "maintained", "reiterate", "reiterated"),
    "INITIATE": ("初次評等", "初評", "初次", "initiate", "initiating", "initiation"),
}


def load_ssot_blocks(ssot_path):
    blocks = {}
    if not (ssot_path and os.path.exists(ssot_path)):
        return blocks
    with open(ssot_path, encoding="utf-8", errors="replace") as handle:
        txt = handle.read()
    for var in ("_RAW_REGEX", "_RAW_LISTS", "_RAW_SYNONYMS"):
        m = re.search(var + r"\s*[:=][^=]*=?\s*json\.loads\(r'''(.*?)'''\)", txt, re.S)
        if m:
            try: blocks[var] = json.loads(m.group(1))
            except Exception: blocks[var] = []
    return blocks


def _read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return None


def find_knowledge_paths(start=None):
    """Walk upward from this file (or `start`) and collect optional knowledge files.

    Nothing is required: every consumer degrades to its built-in tables.
    """
    found = {"broker_dict": None, "rating_dict": None, "synonym_library": None,
             "ticker_master": None, "ticker_ssot": None}
    here = os.path.dirname(os.path.abspath(start or __file__))
    probe = here
    for _ in range(8):
        cands = {
            "broker_dict": [os.path.join(probe, "attachments", "VRN_Broker_Dict_v0100.json")],
            "rating_dict": [os.path.join(probe, "attachments", "VRN_Rating_Dict_v0100.json")],
            "synonym_library": [
                os.path.join(probe, "knowledge", "SYNONYM_LIBRARY_v4.json"),
                os.path.join(probe, "functional modules", "VRN", "knowledge", "SYNONYM_LIBRARY_v4.json"),
            ],
            "ticker_master": [os.path.join(probe, "VIA_TW_Ticker_Master_v0210.py"),
                              os.path.join(probe, "engine", "VIA_TW_Ticker_Master_v0210.py")],
            "ticker_ssot": [os.path.join(probe, "attachments", "VIS_VRN_TickerFilenameSSOT_v0100.py")],
        }
        for key, paths in cands.items():
            if found[key]:
                continue
            for path in paths:
                if os.path.isfile(path):
                    found[key] = path
                    break
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    return found


def load_broker_dict(path):
    """attachments/VRN_Broker_Dict_v0100.json -> {CANONICAL_UPPER: {"aliases": [...], "display": zh}}"""
    payload = _read_json(path) if path else None
    out = {}
    if not isinstance(payload, dict):
        return out
    for canon_zh, spec in (payload.get("brokers") or {}).items():
        abbr = str(spec.get("abbr") or canon_zh).upper()
        canonical = BROKER_CANONICAL_BRIDGE.get(abbr, abbr)
        aliases = [str(a) for a in (spec.get("aliases") or [])] + [str(canon_zh)]
        entry = out.setdefault(canonical, {"aliases": [], "display": str(canon_zh)})
        for alias in aliases:
            if alias not in entry["aliases"]:
                entry["aliases"].append(alias)
    return out


def load_rating_dict(path):
    """attachments/VRN_Rating_Dict_v0100.json -> {LEVEL: [words]}"""
    payload = _read_json(path) if path else None
    out = {}
    if not isinstance(payload, dict):
        return out
    for level, spec in (payload.get("levels") or {}).items():
        words = list(spec.get("zh") or []) + list(spec.get("en") or [])
        out[str(level).upper()] = [str(w) for w in words]
    return out


def load_synonym_library(path):
    """SYNONYM_LIBRARY_v4.json -> {scope: {term_casefold: [canonical, ...]}} (differences kept)."""
    payload = _read_json(path) if path else None
    out = {}
    if not isinstance(payload, dict):
        return out
    for scope, terms in (payload.get("scopes") or {}).items():
        table = {}
        for term, records in (terms or {}).items():
            canon = []
            for rec in records or []:
                c = rec.get("canonical")
                if c and c not in canon:
                    canon.append(str(c))
            if canon:
                table[unicodedata.normalize("NFKC", str(term)).casefold().strip()] = canon
        out[scope] = table
    return out


def load_ticker_master(path):
    """Import VIA_TW_Ticker_Master_v0210.py by path; None when absent or broken."""
    if not path or not os.path.isfile(path):
        return None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("via_tw_ticker_master", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


# canonical bridge: abbreviations used by the attachments dict / older engines -> SYNONYM_LIBRARY keys
BROKER_CANONICAL_BRIDGE = {
    "YT": "YUANTA", "FB": "FUBON", "CT": "CATHAY", "TSC": "TAISHIN", "TS": "TAISHIN",
    "SP": "SINOPAC", "SINOPAC": "SINOPAC", "CS": "CS", "JPMORGAN": "JPM", "JP": "JPM",
    "MORGANSTANLEY": "MS", "GOLDMAN": "GS", "GOLDMANSACHS": "GS", "BOA": "BOFA",
    "MQ": "MACQUARIE", "MCQ": "MACQUARIE", "CLST": "CLSA", "MEGABANK": "MEGA",
    "HUANAN": "HUANAN", "HN": "HUANAN", "PSC": "PRESIDENT", "UNI": "PRESIDENT",
    "CAP": "CAPITAL", "KGI": "KGI", "CTBC": "CTBC", "MEGA": "MEGA", "DAIWA": "DAIWA",
    "NOMURA": "NOMURA", "UBS": "UBS", "CITI": "CITI", "HSBC": "HSBC", "CLSA": "CLSA",
    "MACQUARIE": "MACQUARIE", "JPM": "JPM", "MS": "MS", "GS": "GS", "BOFA": "BOFA",
    "YUANTA": "YUANTA", "FUBON": "FUBON", "CATHAY": "CATHAY", "TAISHIN": "TAISHIN",
    "PRESIDENT": "PRESIDENT", "CAPITAL": "CAPITAL", "MASTERLINK": "MASTERLINK",
    "JIHSUN": "JIHSUN", "ESUN": "ESUN", "FIRST": "FIRST",  "GFHK": "GF",
}

# =====================================================================
# 2 · TICKER / FILENAME
# =====================================================================
class TickerFilename:
    _PUN = ("　 \t\r\n．。，、；：（）()【】〔〕「」『』《》〈〉［］{}<>"
            "·•‧／/\\|—–-_~＿＝=＋+＊*＆&％%＃#＠@！!？?＂\"＇'｀`^＄$.,;:!?\"'()[]{}<>")
    _SEP = re.compile("[" + re.escape(_PUN) + "]+")
    _SECTOR_KW = ("產業", "類股", "族群", "策略", "展望", "sector", "industry")
    # spec section 2: protected fragments are cut out before the CJK/LATIN/DIGIT split
    _PROTECT = [
        ("tricode", re.compile(r"(?<![0-9A-Za-z])([1-9]\d{3})(?:\.(TWO|TW)|\s?TT)(?![0-9A-Za-z])", re.I)),
        ("date_split", re.compile(r"(?<!\d)((?:19|20)\d{2}|1\d{2})[./\-年](0?[1-9]|1[0-2])[./\-月](0?[1-9]|[12]\d|3[01])日?(?!\d)")),
        ("date_prefixed", re.compile(r"\((19|20)\)(\d{6})(?!\d)")),
        ("date8", re.compile(r"(?<!\d)((?:19|20)\d{6})(?!\d)")),
        ("date7", re.compile(r"(?<!\d)(1\d{6})(?!\d)")),
        ("etf", re.compile(r"(?<![0-9A-Za-z])(00\d{3}[A-Z]|00\d[A-Z]\d{2}|00\d{2,4})(?![0-9A-Za-z])")),
        ("quarter", re.compile(r"(?<![0-9A-Za-z])(?:([1-4])Q(\d{2}|\d{4})|Q([1-4])[ ]?(\d{2}|\d{4})|(\d{4})[.\s]?Q([1-4])|(\d{4})年?第?([1-4])季)(?![0-9A-Za-z])", re.I)),
        ("date6", re.compile(r"(?<!\d)(\d{6})(?!\d)")),
        ("ky", re.compile(r"([一-鿿A-Za-z]{1,8})[-‑]KY(?![A-Za-z])")),
    ]

    def __init__(self, ssot_path=None, official_set=None, knowledge=None):
        b = load_ssot_blocks(ssot_path)
        rules = {r.get("rule_name") or r.get("name"): r for r in b.get("_RAW_REGEX", [])}
        def pat(name):
            r = rules.get(name)
            return r["pattern"] if (r and r.get("pattern")) else _LOCK[name]
        self.rx_bare_strict = re.compile(r"(?<!\d)" + pat("TW_STOCK_CODE_4DIGIT") + r"(?!\d)")
        self.rx_bare_any = re.compile(r"(?<!\d)([1-9]\d{3})(?!\d)")
        self.rx_yf = re.compile(r"(?<!\d)" + pat("TW_YFINANCE_TICKER") + r"\b", re.I)
        self.rx_bb = re.compile(r"(?<!\d)" + pat("TW_BLOOMBERG_TICKER") + r"\b", re.I)
        self.alias2tk, self.tk2name = {}, {}
        for s in b.get("_RAW_SYNONYMS", []):
            canon = s.get("canonical", "")
            mt = re.match(r"(\d{4})", canon)
            if not mt: continue
            tk = mt.group(1)
            names = [a for a in s.get("aliases", []) if not re.match(r"^\d{4}(\s+TT|\.TW[O]?)?$", a)]
            cn = next((a for a in names if re.search(r"[一-鿿]", a)), (names[0] if names else ""))
            self.tk2name[tk] = cn
            for a in s.get("aliases", []) + [canon]:
                self.alias2tk[a] = tk
        self.official_set = set(official_set) if official_set else None
        self.ticker_master = (knowledge or {}).get("ticker_master") if isinstance(knowledge, dict) else None

    @staticmethod
    def is_valid_bare(t): return bool(re.fullmatch(r"[1-9]\d{3}", t or ""))

    @staticmethod
    def is_year_band(t):
        return bool(re.fullmatch(r"\d{4}", t or "")) and YEAR_BAND[0] <= int(t) <= YEAR_BAND[1]

    @staticmethod
    def is_etf_code(t):
        return bool(ETF_CODE_RE.match(t or ""))

    @staticmethod
    def _calendar(y, mo, d):
        try:
            iy, im, idd = int(y), int(mo), int(d)
            datetime.date(iy, im, idd)
        except (ValueError, TypeError):
            return None
        if not (1990 <= iy <= 2099):
            return None
        return "%04d-%02d-%02d" % (iy, im, idd)

    @classmethod
    def numtoken_to_date(cls, tok):
        """8 digits -> yyyymmdd; 7 digits -> ROC 1yymmdd (+1911); 6 digits -> 20yymmdd.
        Calendar-validated: 20250230 -> None, 926708 -> None."""
        if not (tok and tok.isdigit()): return None
        if len(tok) == 8: y, mo, d = tok[:4], tok[4:6], tok[6:8]
        elif len(tok) == 7:
            roc = int(tok[:3])
            if not (80 <= roc <= 150): return None
            y, mo, d = str(roc + 1911), tok[3:5], tok[5:7]
        elif len(tok) == 6: y, mo, d = "20"+tok[:2], tok[2:4], tok[4:6]
        else: return None
        return cls._calendar(y, mo, d)

    @staticmethod
    def to_display(iso):
        return iso.replace("-", "/") if iso else ""

    @staticmethod
    def _cls(ch):
        if ch.isdigit(): return "DIGIT"
        o = ord(ch)
        if (0x4E00<=o<=0x9FFF) or (0x3400<=o<=0x4DBF) or (0xF900<=o<=0xFAFF): return "CJK"
        if "A" <= ch.upper() <= "Z": return "LATIN"
        return "OTHER"

    @staticmethod
    def strip_ext(name):
        return re.sub(r"\.(pdf|docx?|pptx?|xlsx?|csv|txt|png|jpe?g|tiff?|webp|heic)$", "", name or "", flags=re.I)

    def protect(self, stem):
        """Cut protected fragments (spec section 2 order) out of the stem.

        Returns (rest_text, fragments) where fragments is a list of dicts with kind/raw/value.
        """
        text = unicodedata.normalize("NFKC", stem)
        fragments = []
        taken = [False] * len(text)
        def free(a, b): return not any(taken[a:b])
        def take(a, b):
            for i in range(a, b): taken[i] = True
        for kind, rx in self._PROTECT:
            for m in rx.finditer(text):
                a, b = m.span()
                if not free(a, b):
                    continue
                raw = m.group(0)
                frag = {"kind": kind, "raw": raw, "span": [a, b], "value": None}
                if kind == "tricode":
                    frag["value"] = m.group(1)
                    frag["platform"] = "yfinance" if "." in raw else "bloomberg"
                    frag["market"] = ("TPEX" if raw.upper().endswith(".TWO") else "TWSE") if "." in raw else ""
                elif kind == "date_split":
                    y = int(m.group(1)); y = y + 1911 if y < 1000 else y
                    frag["value"] = self._calendar(y, m.group(2), m.group(3))
                elif kind == "date_prefixed":
                    frag["value"] = self.numtoken_to_date(m.group(1) + m.group(2))
                elif kind in ("date8", "date7", "date6"):
                    frag["value"] = self.numtoken_to_date(m.group(1))
                    if frag["value"] is None and kind == "date6":
                        frag["kind"] = "number"      # e.g. 926708: stays an unclassified number
                elif kind == "etf":
                    frag["value"] = m.group(1)
                elif kind == "quarter":
                    g = m.groups()
                    if g[0]: q, y = g[0], g[1]
                    elif g[2]: q, y = g[2], g[3]
                    elif g[4]: y, q = g[4], g[5]
                    else: y, q = g[6], g[7]
                    y = int(y); y = y + 2000 if y < 100 else y
                    frag["value"] = "%04d-Q%s" % (y, q)
                elif kind == "ky":
                    frag["value"] = m.group(0)
                if frag["value"] is None and frag["kind"] != "number":
                    continue          # invalid protected candidate: leave the text to the tokenizer
                take(a, b)
                fragments.append(frag)
        rest = "".join(" " if taken[i] else ch for i, ch in enumerate(text))
        fragments.sort(key=lambda f: f["span"][0])
        return rest, fragments

    def tokenize(self, name):
        stem = self.strip_ext(name)
        stem = unicodedata.normalize("NFKC", stem)
        stem = self._SEP.sub(" ", stem)
        out = []
        for chunk in stem.split():
            cur, ck = "", None
            for ch in chunk:
                k = self._cls(ch)
                if k == "OTHER":
                    if cur: out.append((cur, ck)); cur, ck = "", None
                    continue
                if ck is None or k == ck: cur += ch; ck = k
                else: out.append((cur, ck)); cur, ck = ch, k
            if cur: out.append((cur, ck))
        return out

    def parse_filename(self, name):
        """Filename ladder: keep name -> protect fragments -> split -> trim -> candidates.

        Result keys (append-only): tickers, dates, cjk, latin, plus v0102 fields
        year_band, etf, tricodes, quarters, partial_dates, unclassified_numbers,
        dates_display, ky_names, company_fragments, tokens.
        """
        res = {"tickers": [], "dates": [], "cjk": [], "latin": [], "year_band": [], "etf": [],
               "tricodes": [], "quarters": [], "partial_dates": [], "unclassified_numbers": [],
               "dates_display": [], "ky_names": [], "company_fragments": [], "tokens": []}
        stem = self.strip_ext(name)
        rest, fragments = self.protect(stem)
        for frag in fragments:
            kind, val = frag["kind"], frag["value"]
            if kind == "tricode":
                res["tricodes"].append({"raw": frag["raw"], "core": val, "platform": frag.get("platform"), "market": frag.get("market", "")})
                if val not in res["tickers"]:
                    res["tickers"].append(val)
            elif kind.startswith("date") and val:
                if val not in res["dates"]:
                    res["dates"].append(val)
            elif kind == "etf":
                res["etf"].append(val)
            elif kind == "quarter":
                res["quarters"].append({"raw": frag["raw"], "period": val})
            elif kind == "ky":
                res["ky_names"].append(val)
                res["cjk"].append(re.sub(r"[-‑]KY$", "", val))
            elif kind == "number":
                res["unclassified_numbers"].append(frag["raw"])
        tokens = self.tokenize(rest)
        res["tokens"] = tokens
        prev = None
        after_ticker = 0
        for idx, (tok, kind) in enumerate(tokens):
            if kind == "DIGIT":
                after_ticker = 0
                if len(tok) == 4 and self.is_valid_bare(tok):
                    if self.is_year_band(tok) and not (self.official_set and tok in self.official_set):
                        res["year_band"].append(tok)
                    else:
                        if tok not in res["tickers"]:
                            res["tickers"].append(tok)
                        after_ticker = 1
                elif len(tok) == 4 and tok[0] == "0" and prev and prev[1] == "LATIN" and not res["dates"]:
                    # CTBC0915: month/day only, never invent the year (spec section 2)
                    mm, dd = int(tok[:2]), int(tok[2:])
                    if 1 <= mm <= 12 and 1 <= dd <= 31:
                        res["partial_dates"].append({"raw": prev[0] + tok, "month": mm, "day": dd, "status": "YEAR_MISSING"})
                    else:
                        res["unclassified_numbers"].append(tok)
                elif self.is_etf_code(tok):
                    res["etf"].append(tok)
                else:
                    d = self.numtoken_to_date(tok)
                    if d:
                        if d not in res["dates"]: res["dates"].append(d)
                    elif len(tok) >= 5:
                        res["unclassified_numbers"].append(tok)
            elif kind == "CJK":
                res["cjk"].append(tok)
                if after_ticker and after_ticker <= 2:
                    res["company_fragments"].append(tok)   # 凱基投顧_2891 中信金: 中信金 is the company
                    after_ticker += 1
                else:
                    after_ticker = 0
            elif kind == "LATIN":
                res["latin"].append(tok)
                after_ticker = 0
            prev = (tok, kind)
        # spec: filename before page; keep every candidate, first valid wins downstream
        res["dates_display"] = [self.to_display(d) for d in res["dates"]]
        res["unclassified_numbers"] = list(dict.fromkeys(res["unclassified_numbers"]))
        return res

    @staticmethod
    def parse_email(text):
        return [{"analyst_id": m.group(1), "broker_domain": m.group(2)}
                for m in re.finditer(r"([A-Za-z][A-Za-z.\-_]*)@([A-Za-z0-9.\-]+)", text or "")]

    def resolve(self, filename, title="", body=""):
        fn, title, body = filename or "", title or "", body or ""
        def suf(src):
            m = self.rx_yf.search(src) or self.rx_bb.search(src) or re.search(r"(?<!\d)([1-9]\d{3})TT\b", src, re.I)
            return m.group(1) if m else None
        tk = suf(fn)
        if tk: return self._ok(tk, "FILE_SUFFIX")
        m = self.rx_bare_strict.search(self.strip_ext(fn))
        if m: return self._ok(m.group(1), "FILE_BARE")
        parsed = self.parse_filename(fn)
        if parsed["etf"] and not parsed["tickers"]:
            out = self._ok(parsed["etf"][0], "FILE_ETF"); out["is_etf"] = True; return out
        if any(k in fn for k in self._SECTOR_KW): return self._sec("SECTOR_FILE")
        tk = suf(title)
        if tk: return self._ok(tk, "TITLE_SUFFIX")
        for a, t in self.alias2tk.items():
            if a and len(a) >= 2 and re.search(r"[一-鿿A-Za-z]", a) and a in title:
                return self._ok(t, "TITLE_SYNONYM")
        tk = suf(body)
        if tk: return self._ok(tk, "BODY_SUFFIX")
        if any(k in title for k in self._SECTOR_KW): return self._sec("SECTOR_TITLE")
        for src, why in ((fn, "FILE"), (title, "TITLE")):
            # a bare number glued to letters (CTBC2609, Q4 2026x) is not a ticker candidate
            m = re.search(r"(?<![0-9A-Za-z])([1-9]\d{3})(?![0-9A-Za-z])", src)
            if m:
                cand = m.group(1)
                if YEAR_BAND[0] <= int(cand) <= YEAR_BAND[1]:
                    if (self.official_set and cand in self.official_set) or (cand == suf(fn+" "+title+" "+body)):
                        return self._ok(cand, "RECLAIM_"+why)
                else:
                    return self._ok(cand, why+"_BARE_ANY")
        # body evidence must be structured: 公司(1234) / 代號：1234 — a bare number (phone, amount) is never a ticker
        m = (re.search(r"[一-鿿]{1,12}(?:-KY)?\s*[（(]\s*([1-9]\d{3})(?:\s*TT|\.TWO?)?\s*[,，)）]", body[:1200])
             or re.search(r"(?:股票代號|證券代號|代號|Ticker|Stock\s*Code|Code)\s*[:：]?\s*(?<![0-9A-Za-z])([1-9]\d{3})(?![0-9A-Za-z])", body[:1200], re.I))
        if m and not (self.is_year_band(m.group(1)) and not (self.official_set and m.group(1) in self.official_set)):
            return self._ok(m.group(1), "BODY_STRUCTURED")
        return self._sec("NONE")

    def _ok(self, tk, method): return {"ticker": tk, "name": self.tk2name.get(tk, ""), "method": method, "is_sector": False}
    def _sec(self, method): return {"ticker": "", "name": "", "method": method, "is_sector": True}

    def cross_check(self, filename_ticker, raw=None, yf=None, bbg=None, official_market=None):
        """Tri-code cross check (spec section 2).

        verdict: PASS (every present code agrees on the 4-digit core),
                 MISMATCH (a present code disagrees),
                 MARKET_MISMATCH (cores agree but .TW/.TWO contradicts the official market),
                 INSUFFICIENT_EVIDENCE (only one side is available).
        """
        res = {"filename_ticker": filename_ticker, "checks": [], "verdict": "PASS"}
        def core4(c):
            m = re.match(r"([1-9]\d{3})", (c or "").strip()); return m.group(1) if m else None
        def add(l, v, ok, msg):
            res["checks"].append({"code": l, "value": v, "ok": ok, "msg": msg})
            if not ok: res["verdict"] = "MISMATCH"
        present = [c for c in (raw, yf, bbg) if c]
        if raw is not None: add("TW_TICKER", raw, self.is_valid_bare(raw) and core4(raw)==filename_ticker, "raw core4")
        if yf is not None: add("TW_YFINANCE", yf, bool(re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", yf.strip(), re.I)) and core4(yf)==filename_ticker, "yf")
        if bbg is not None: add("TW_BLOOMBERG", bbg, bool(re.fullmatch(r"[1-9]\d{3}\s+TT", bbg.strip(), re.I)) and core4(bbg)==filename_ticker, "bbg")
        if res["verdict"] == "PASS":
            if yf and official_market:
                market = "TPEX" if yf.strip().upper().endswith(".TWO") else "TWSE"
                if market != str(official_market).upper():
                    res["verdict"] = "MARKET_MISMATCH"
                    res["checks"].append({"code": "MARKET", "value": market, "ok": False, "msg": "official=" + str(official_market)})
            if not filename_ticker or not present:
                res["verdict"] = "INSUFFICIENT_EVIDENCE"
        res["fail"] = res["verdict"] != "PASS"
        return res

# =====================================================================
# 3 · LAYOUT  (font hierarchy + element_type + sentence linking)
# =====================================================================
class Layout:
    _BOILER = ("投顧", "研究部", "免責", "disclosure", "bloomberg", "reuters", "not investment advice", "for information only")
    _KEEP_FOOTER = ("目標價", "評等", "target price", "rating", "eps", "稀釋", "diluted", "nt$", "twd", "元")

    def __init__(self, page_height=842.0, page_width=595.0):
        self.H = page_height
        self.W = page_width

    @staticmethod
    def _lines_from_chars(chars):
        """Rows of glyphs -> lines.  v0103: VRN_Evidence_Core groups by baseline and writes spaces from the
        glyph geometry (CTBC filler spaces, English words, chart overlays); v0102 grouping is the fallback."""
        if EVIDENCE_CORE is not None:
            try:
                return EVIDENCE_CORE.lines_from_chars(chars)
            except Exception:
                pass
        rows = defaultdict(list)
        for c in chars:
            rows[round(c["top"] / 3.0)].append(c)
        lines = []
        for key in sorted(rows):
            cs = sorted(rows[key], key=lambda c: c["x0"])
            # overprinted (faux-bold) glyphs: the same char within 1pt of the previous one is a duplicate
            deduped = []
            for c in cs:
                if deduped and c["text"] == deduped[-1]["text"] and abs(c["x0"] - deduped[-1]["x0"]) < 1.0:
                    continue
                deduped.append(c)
            cs = deduped
            text = "".join(c["text"] for c in cs)
            size = statistics.median([c["size"] for c in cs]) if cs else 0
            bold = sum(1 for c in cs if "bold" in (c.get("fontname") or "").lower()) > len(cs)/2
            top = min(c["top"] for c in cs); x0 = min(c["x0"] for c in cs)
            lines.append({"text": text, "size": round(size, 2), "bold": bold, "top": top, "x0": x0, "chars": cs})
        return lines

    def classify(self, chars):
        lines = self._lines_from_chars(chars)
        if not lines: return {"lines": [], "body_size": 0, "company_name": "", "main_text": "", "footer": "", "footer_kept": ""}
        sizes = [l["size"] for l in lines]
        body_size = statistics.median(sizes)
        for idx, l in enumerate(lines):
            r = l["size"] / body_size if body_size else 1
            low = l["text"].lower()
            l["source_id"] = "L%03d" % (idx + 1)
            l["zone"] = "left" if l["x0"] < self.W * 0.45 else "right"
            if l["top"] >= self.H * 0.88 or any(b in low for b in self._BOILER):
                l["level"] = "FOOTER"
            elif r >= 1.8: l["level"] = "MAIN_TITLE"
            elif r >= 1.4: l["level"] = "HEADLINE"
            elif r >= 1.15: l["level"] = "H2"
            elif r <= 0.8: l["level"] = "FOOTER"
            else: l["level"] = "BODY"
            # spec section 3: small print that carries research data is kept, not dropped
            l["keep_data"] = l["level"] == "FOOTER" and any(k in low for k in self._KEEP_FOOTER)
        cands = [l for l in lines if l["level"] in ("MAIN_TITLE", "HEADLINE")]
        company = ""
        if cands:
            cands.sort(key=lambda l: (-l["size"], not l["bold"], l["top"]))
            company = cands[0]["text"].strip()
        body_lines = [l["text"] for l in lines if l["level"] == "BODY"]
        main_text = self._link_sentences(body_lines)
        footer = " ".join(l["text"] for l in lines if l["level"] == "FOOTER")
        footer_kept = " ".join(l["text"] for l in lines if l.get("keep_data"))
        return {"lines": lines, "body_size": body_size, "company_name": company,
                "main_text": main_text, "footer": footer, "footer_kept": footer_kept}

    @staticmethod
    def _link_sentences(body_lines):
        """rightward+downward link; break only at sentence-final punctuation."""
        buf, out = "", []
        for ln in body_lines:
            ln = ln.strip()
            if not ln: continue
            buf = (buf + " " + ln).strip() if buf else ln
            while True:
                m = re.search(r"[。!?！？]|\.(?=\s|$)", buf)
                if not m: break
                cut = m.end()
                out.append(buf[:cut].strip()); buf = buf[cut:].strip()
        if buf: out.append(buf)
        return " ".join(out)

# =====================================================================
# 4 · TABLE GEOMETRY (hidden gridline reconstruction)
# =====================================================================
class TableGeometry:
    @staticmethod
    def _cluster(vals, gap):
        vals = sorted(vals)
        if not vals: return []
        groups = [[vals[0]]]
        for v in vals[1:]:
            if v - groups[-1][-1] <= gap: groups[-1].append(v)
            else: groups.append([v])
        return [statistics.mean(g) for g in groups]

    def reconstruct(self, chars, col_gap=18.0, row_gap=6.0):
        """cluster chars by x (columns) and y (rows) -> 2D grid of cell text."""
        if not chars: return {"rows": [], "n_cols": 0}
        row_centers = self._cluster([c["top"] for c in chars], row_gap)
        col_centers = self._cluster([c["x0"] for c in chars], col_gap)
        grid = [["" for _ in col_centers] for _ in row_centers]
        def nearest(centers, v):
            return min(range(len(centers)), key=lambda i: abs(centers[i]-v))
        by_row = defaultdict(list)
        for c in chars:
            ri = nearest(row_centers, c["top"])
            by_row[ri].append(c)
        for ri, cs in by_row.items():
            cs.sort(key=lambda c: c["x0"])
            for c in cs:
                ci = nearest(col_centers, c["x0"])
                grid[ri][ci] += c["text"]
        rows = ["|".join(cell.strip() for cell in r) for r in grid]
        return {"rows": [r.split("|") for r in rows], "n_cols": len(col_centers),
                "col_centers": col_centers, "row_centers": row_centers}

    @staticmethod
    def restore_period_header(cells):
        """normalize period tokens like 12/24A, 12/25E, 2024, 2025E, 1Q25, 2025.Q1 -> canonical."""
        out = []
        kinds = {"A": "actual", "E": "estimate", "F": "forecast"}
        for c in cells:
            c = c.strip()
            m = re.match(r"(\d{1,2})/(\d{2})([AEF]?)$", c)
            if m:
                out.append({"raw": c, "period": "20%s-%s" % (m.group(2), m.group(1).zfill(2)),
                            "kind": kinds.get(m.group(3), "actual")}); continue
            m = re.match(r"(?:FY)?(20\d{2})([AEF]?)$", c, re.I)
            if m:
                out.append({"raw": c, "period": m.group(1), "kind": kinds.get(m.group(2).upper(), "actual")}); continue
            m = re.match(r"(\d{2})([AEF])$", c, re.I)
            if m:
                out.append({"raw": c, "period": "20" + m.group(1), "kind": kinds.get(m.group(2).upper(), "actual")}); continue
            m = re.match(r"(?:([1-4])Q(\d{2,4})|Q([1-4])\s?(\d{2,4})|(\d{4})[.\s]?Q([1-4]))([AEF]?)$", c, re.I)
            if m:
                g = m.groups()
                if g[0]: q, y = g[0], g[1]
                elif g[2]: q, y = g[2], g[3]
                else: y, q = g[4], g[5]
                y = int(y); y = y + 2000 if y < 100 else y
                out.append({"raw": c, "period": "%04d-Q%s" % (y, q), "kind": kinds.get((g[6] or "").upper(), "actual")}); continue
            out.append({"raw": c, "period": None, "kind": None})
        return out

# =====================================================================
# 5 · NLP REPAIR  (local heuristic; hook to swap in via_nlp v1.5)
# =====================================================================
class NLPRepair:
    def __init__(self, external_engine=None):
        self.ext = external_engine  # e.g. via_nlp_engine.text_ops.TextProcessor()

    def repair_text(self, raw):
        if self.ext is not None:
            try: return self.ext.repaired(raw)  # delegate to real engine
            except Exception: pass
        # heuristic fallback: join English hyphen line-wraps only (never digits, signs or decimals),
        # join CJK line breaks without a space, collapse whitespace
        t = raw or ""
        t = re.sub(r"([A-Za-z])-\s+([a-z])", r"\1\2", t)
        t = re.sub(r"([一-鿿])\s+([一-鿿])", r"\1\2", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def split_sentences(self, text):
        if self.ext is not None:
            try: return self.ext.split_sentences(text)
            except Exception: pass
        # Chinese sentence-final punctuation always splits; ASCII .!? only before whitespace + capital/CJK
        parts = re.split(r"(?<=[。！？])|(?<=[.!?])\s+(?=[A-Z一-鿿])", text or "")
        return [p.strip() for p in parts if p and p.strip()]

# =====================================================================
# 6 · FINANCIAL VALIDATION
# =====================================================================
class FinancialValidation:
    ABS_TOL = 0.01      # spec section 6 defaults
    REL_TOL = 0.005

    @staticmethod
    def _band(err):
        a = abs(err)
        if a <= 0.01: return ("PASS", 1.0)
        if a <= 0.05: return ("PASS-SOFT", 0.85)
        if a <= 0.10: return ("WARN", 0.65)
        return ("FAIL", 0.45)

    def add_sub(self, total, parts):
        """total ?= sum(parts). returns verdict + confidence + rel err."""
        s = sum(parts)
        if total == 0: return {"verdict": "N/A", "conf": 0.0, "rel_err": None}
        err = (s - total) / total
        v, c = self._band(err)
        return {"verdict": v, "conf": c, "rel_err": round(err, 4), "computed": s, "reported": total}

    def multiply(self, actual, a, b, scale_percent=False):
        """actual ?= a * b  (e.g. TargetPrice = PER * EPS ; NetIncome = EPS * Shares)."""
        expected = a * b
        if scale_percent: expected /= 100.0
        if actual in (None, 0) and expected == 0:
            return {"verdict": "N/A", "conf": 0.0}
        if expected == 0:
            return {"verdict": "N/A", "conf": 0.0}
        err = (actual - expected) / expected
        v, c = self._band(err)
        return {"verdict": v, "conf": c, "expected": round(expected, 4), "actual": actual, "rel_err": round(err, 4)}

    def division(self, actual, numer, denom, scale_percent=False):
        """two-stage: A magnitude 0.5x-3.0x, B tolerance bands. handles ROE %/decimal."""
        if denom == 0 or actual in (None, 0):
            return {"verdict": "N/A", "conf": 0.0}
        expected = numer / denom
        if scale_percent: expected *= 100.0
        ratio = actual / expected if expected else 0
        stageA = 0.5 <= ratio <= 3.0
        err = (actual - expected) / expected if expected else 1
        v, c = self._band(err)
        if v == "FAIL" and stageA:
            v, c = "PASS-RANGE", 0.6   # magnitude ok even if exact tol fails (avg vs ending equity etc.)
        return {"verdict": v, "conf": c, "expected": round(expected, 4), "actual": actual,
                "ratio": round(ratio, 3), "stageA_magnitude_ok": stageA}

    def historical_yoy(self, series):
        """series: list[(year, value)] ascending. returns YoY growth, derived-skip aware."""
        series = sorted(series)
        out = []
        for i in range(1, len(series)):
            (y0, v0), (y1, v1) = series[i-1], series[i]
            if v0 in (None, 0) or v1 is None:
                out.append({"year": y1, "yoy": None, "note": "BASE_ZERO_OR_MISSING"}); continue
            item = {"year": y1, "yoy": round((v1 - v0) / abs(v0), 4)}
            if v0 < 0:
                item["note"] = "NEGATIVE_BASE"      # spec: growth on a negative base needs a reading note
            out.append(item)
        return out

    def check_identity(self, lhs, rhs, abs_tol=None, rel_tol=None, name="identity"):
        """lhs ?= rhs with absolute OR relative tolerance (defaults abs 0.01 / rel 0.5%)."""
        abs_tol = self.ABS_TOL if abs_tol is None else abs_tol
        rel_tol = self.REL_TOL if rel_tol is None else rel_tol
        if lhs is None or rhs is None:
            return {"name": name, "verdict": "N/A", "reason": "MISSING_INPUT"}
        diff = lhs - rhs
        base = max(abs(lhs), abs(rhs))
        ok = abs(diff) <= abs_tol or (base > 0 and abs(diff) / base <= rel_tol)
        return {"name": name, "verdict": "PASS" if ok else "FAIL", "lhs": lhs, "rhs": rhs,
                "diff": round(diff, 6), "rel": (round(abs(diff) / base, 6) if base else None)}

    def balance_sheet(self, assets, liabilities, equity_total):
        """assets = liabilities + total equity (same date, same consolidation, NCI included)."""
        return self.check_identity(assets, (liabilities or 0) + (equity_total or 0), name="assets=liabilities+equity")

    def gross_profit(self, revenue, cost, gross):
        return self.check_identity((revenue or 0) - (cost or 0), gross, name="revenue-cost=gross")

    def margin(self, profit, revenue, margin_pct):
        if not revenue:
            return {"name": "margin", "verdict": "N/A", "reason": "REVENUE_ZERO"}
        return self.check_identity(profit / revenue * 100.0, margin_pct, abs_tol=0.05, name="profit/revenue=margin%")

    def diluted_eps(self, diluted_numerator, weighted_diluted_shares, eps):
        if not weighted_diluted_shares:
            return {"name": "diluted_eps", "verdict": "N/A", "reason": "SHARES_MISSING"}
        return self.check_identity(diluted_numerator / weighted_diluted_shares, eps, name="diluted_eps")

    def annual_equals_quarters(self, annual, quarters, flow_item=True):
        if not flow_item:
            return {"name": "annual=quarters", "verdict": "N/A", "reason": "NOT_A_FLOW_ITEM"}
        if annual is None or len(quarters or []) != 4 or any(q is None for q in quarters):
            return {"name": "annual=quarters", "verdict": "N/A", "reason": "QUARTERS_INCOMPLETE"}
        return self.check_identity(sum(quarters), annual, name="annual=quarters")

# =====================================================================
# 7 · PRICE ADJUSTMENT (consistency)
# =====================================================================
class PriceAdjustment:
    @staticmethod
    def to_adjusted(raw_price, cum_adjust_factor):
        """If price passed ex-div/ex-rights, apply cumulative factor so series is comparable."""
        if raw_price is None or cum_adjust_factor in (None, 0): return raw_price
        return round(raw_price * cum_adjust_factor, 4)

    def normalize_series(self, prices, factors):
        """prices/factors aligned by index; returns adjusted series on a comparable basis."""
        return [self.to_adjusted(p, f) for p, f in zip(prices, factors)]

    def upside(self, target_price, current_price_adj):
        if not current_price_adj or target_price is None: return None
        return round((target_price - current_price_adj) / current_price_adj, 4)

    def upside_checked(self, target_price, current_price, target_basis="raw", price_basis="raw",
                       target_currency="TWD", price_currency="TWD", price_date=""):
        """Spec section 5: same currency, same per-share basis, comparable adjustment basis,
        otherwise keep both values and answer BASIS_MISMATCH."""
        if target_price is None or current_price in (None, 0):
            return {"status": "UNDISCLOSED", "upside_pct": None, "target_price": target_price, "current_price": current_price}
        if target_currency != price_currency or target_basis != price_basis:
            return {"status": "BASIS_MISMATCH", "upside_pct": None, "target_price": target_price,
                    "current_price": current_price, "target_basis": target_basis, "price_basis": price_basis}
        # v0104: the label says what was divided (run() passes the printed page price; the ADJ upside is separate)
        return {"status": "DERIVED", "upside_pct": round((target_price / current_price - 1.0) * 100.0, 2),
                "target_price": target_price, "current_price": current_price, "price_date": price_date,
                "price_basis": price_basis, "formula": "(target / current price given - 1) * 100%"}

# =====================================================================
# 8 · CROSS VALIDATION
# =====================================================================
# ---------------------------------------------------------------------
# BROKER DICT / RATING DICT
# ---------------------------------------------------------------------
class BrokerRatingDict:
    BROKER = {
        "KGI": ["凱基", "kgi", "kgieworld", "凱基證券", "凱基投顧"], "YUANTA": ["元大", "yuanta"],
        "FUBON": ["富邦", "fubon"], "CAPITAL": ["群益", "capital securities", "capital"],
        "PRESIDENT": ["統一", "統一投顧", "pscnet", "president"], "CTBC": ["中信", "中國信託", "ctbc", "中信投顧", ],
        "JPM": ["摩根大通", "jp morgan", "j.p. morgan", "jpm", "jpmorgan", "jp"],
        "GS": ["高盛", "goldman", "goldman sachs", "gs"], "BOFA": ["美銀", "美林", "bofa", "merrill", "boa"],
        "MACQUARIE": ["麥格理", "macquarie", "mq", "mcq"], "CITI": ["花旗", "citi", "citigroup"],
        "UBS": ["瑞銀", "ubs"], "DAIWA": ["大和", "daiwa"], "NOMURA": ["野村", "nomura"],
        "MS": ["摩根士丹利", "morgan stanley", "ms"], "CLSA": ["里昂", "clsa", "clst"],
        "HUANAN": ["華南", "華南永昌", "華南投顧", "hua nan", "huanan"], "MEGA": ["兆豐", "兆豐證券", "兆豐投顧", "mega"],
        "TAISHIN": ["台新", "台新投顧", "taishin"], "CATHAY": ["國泰", "國泰證期", "國泰投顧", "國泰證券", "cathay"],
        "SINOPAC": ["永豐", "永豐金", "sinopac"], "MASTERLINK": ["元富", "masterlink"], "JIHSUN": ["日盛", "jih sun"],
        "HSBC": ["匯豐", "hsbc"],  "ESUN": ["玉山", "esun"], "FIRST": ["第一金", "第一金投顧"],
    }
    RATING = {
        "BUY": ["買進", "強力買進", "加碼", "buy", "outperform", "overweight", "strong buy", "增加持股", "增持", "推薦買進", "買進評等", "超配"],
        "HOLD": ["中立", "持有", "區間", "neutral", "hold", "market perform", "equal-weight", "equalweight", "equal weight", "market weight", "持平", "標準配置"],
        "SELL": ["賣出", "減碼", "sell", "underperform", "underweight", "reduce", "低配", "建議減碼"],
        "ADD": ["逢低", "accumulate", "add"],
        "NOT_RATED": ["未評等", "not rated", "unrated", "not covered", "no recommendation", "不予評等", "尚未評級", "未覆蓋", "停止覆蓋"],
    }
    FINE = {  # spec section 4: differences are kept, not overwritten
        "strong buy": ("BUY", "STRONG_BUY"), "強力買進": ("BUY", "STRONG_BUY"), "積極買進": ("BUY", "STRONG_BUY"),
        "conviction buy": ("BUY", "STRONG_BUY"), "top pick": ("BUY", "STRONG_BUY"),
        "strong sell": ("SELL", "STRONG_SELL"), "強力賣出": ("SELL", "STRONG_SELL"), "強烈賣出": ("SELL", "STRONG_SELL"),
        "accumulate": ("ADD", "BUY"), "add": ("ADD", "BUY"),
    }
    SHORT = {"B": "BUY", "OW": "BUY", "OP": "BUY", "SB": "BUY", "H": "HOLD", "N": "HOLD", "EW": "HOLD", "MP": "HOLD",
             "S": "SELL", "UW": "SELL", "UP": "SELL", "SS": "SELL", "NR": "NOT_RATED", "CD": "NOT_RATED"}
    TARGET_PRICE_TERMS = ["target price", "price target", "12m target price", "12-month target price",
                          "12-month price target", "fair value estimate", "fair value", "tp", "pt",
                          "目標價格", "十二個月目標價", "12個月目標價", "目標價", "目標股價", "股價目標", "合理價值", "合理價", "合理股價"]

    def __init__(self, extra_broker=None, extra_rating=None, knowledge=None):
        self.b = {k: set(x.lower() for x in v) for k, v in self.BROKER.items()}
        self.r = {k: set(x.lower() for x in v) for k, v in self.RATING.items()}
        self.display = {}
        self.fine = dict(self.FINE)
        self.target_terms = list(self.TARGET_PRICE_TERMS)
        self.sources = []
        for k, v in (extra_broker or {}).items(): self.b.setdefault(k.upper(), set()).update(x.lower() for x in v)
        for k, v in (extra_rating or {}).items(): self.r.setdefault(k.upper(), set()).update(x.lower() for x in v)
        if knowledge:
            self.absorb(knowledge)

    def _owner(self):
        owner = {}
        for canon, aliases in self.b.items():
            for a in aliases:
                owner.setdefault(a, canon)
        return owner

    def _add_broker_alias(self, canonical, alias, owner):
        """One owner per alias: the first source (built-in, then SYNONYM_LIBRARY, then attachments) wins."""
        alias = (alias or "").lower().strip()
        if not alias:
            return
        if alias in owner and owner[alias] != canonical:
            return
        self.b.setdefault(canonical, set()).add(alias)
        owner[alias] = canonical

    def absorb(self, knowledge):
        """Merge SYNONYM_LIBRARY scopes + attachments dicts (append-only, differences kept, one owner per alias)."""
        owner = self._owner()
        action_words = {w.lower() for words in RATING_ACTIONS.values() for w in words}
        syn = knowledge.get("synonyms") or {}
        for term, canon in (syn.get("broker") or {}).items():
            c = BROKER_CANONICAL_BRIDGE.get(canon[0].upper(), canon[0].upper())
            self._add_broker_alias(c, term, owner)
        for canonical, spec in (knowledge.get("broker_dict") or {}).items():
            aliases = [a.lower() for a in spec.get("aliases", []) if a]
            owners = {owner[a] for a in aliases if a in owner}
            if len(owners) == 1:
                target = owners.pop()          # 大和/DAI -> DAIWA, 華南/FCB -> HUANAN: merge into the known canonical
            elif len(owners) > 1:
                continue                       # mixed entry (MS/JPM lumped together): never rewrites an identity
            else:
                target = canonical
            for a in aliases:
                self._add_broker_alias(target, a, owner)
            self.display.setdefault(target, spec.get("display", ""))
        if knowledge.get("broker_dict"):
            self.sources.append("broker_dict")
        for level, words in (knowledge.get("rating_dict") or {}).items():
            level = level.upper()
            if level in ("BUY", "HOLD", "SELL", "NOT_RATED", "ADD"):
                self.r.setdefault(level, set()).update(w.lower() for w in words if w.lower() not in action_words)
                self.sources.append("rating_dict")
        for term, canon in (syn.get("rating") or {}).items():
            coarse = {"STRONG_BUY": "BUY", "STRONG_SELL": "SELL"}
            if term in action_words:
                continue        # 維持 / 調升 / 調降 / 重申 are actions, never a rating value (spec section 4)
            if len(canon) > 1:
                fine = next((c for c in canon if c.startswith("STRONG_")), canon[-1])
                base = next((c for c in canon if not c.startswith("STRONG_")), canon[0])
                self.fine[term] = (base, fine)
                self.r.setdefault(base, set()).add(term)
            else:
                level = coarse.get(canon[0], canon[0])
                if canon[0].startswith("STRONG_"):
                    self.fine[term] = (level, canon[0])
                self.r.setdefault(level, set()).add(term)
        for term in (syn.get("target_price") or {}):
            if term not in self.target_terms and term not in ("target", "tgt", "valuation", "目標", "預期價", "目標區間",
                                                                "base case", "bull case", "bear case", "fv"):
                self.target_terms.append(term)
        if syn:
            self.sources.append("synonym_library")
        self.target_terms.sort(key=len, reverse=True)

    @staticmethod
    def _alias_hits(alias, low):
        """CJK alias: substring. ASCII alias: letter/digit boundaries on both sides."""
        if re.search(r"[一-鿿]", alias):
            return alias in low
        return re.search(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", low) is not None

    def broker_matches(self, s, exclude_prefix_fragments=()):
        """All broker hits, longest alias first. `exclude_prefix_fragments`: company fragments whose
        leading alias must not count (凱基投顧_2891 中信金 -> 中信 at the start of 中信金 is ignored)."""
        if not s: return []
        low = s.lower()
        frag_low = [f.lower() for f in exclude_prefix_fragments]
        hits = []
        for canon, aliases in self.b.items():
            for a in sorted(aliases, key=len, reverse=True):
                if not a or not self._alias_hits(a, low):
                    continue
                if any(f.startswith(a) for f in frag_low) and not any(self._alias_hits(a, low.replace(f, " ")) for f in frag_low):
                    continue
                # mother 批728: the mother's deny list (overlay deny_keys + CGC_MDL177) through the evidence core;
                # a hit inside a longer-or-equal denied name is not a broker (中信 inside 中信證券), and a denied
                # alias (摩通) never resolves.  Longest wins, the mother's 批681 rule.
                if EVIDENCE_CORE is not None and EVIDENCE_CORE.deny_shadowed(a, s):
                    continue
                hits.append({"broker": canon, "alias": a, "display": self.display.get(canon, "")})
                break
        hits.sort(key=lambda h: (-len(h["alias"]), h["broker"]))
        return hits

    def broker_normalize(self, s, exclude_prefix_fragments=()):
        hits = self.broker_matches(s, exclude_prefix_fragments)
        return hits[0]["broker"] if hits else None

    def rating_matches(self, s, in_rating_field=False):
        if not s: return []
        low = s.lower()
        out = []
        for canon, aliases in self.r.items():
            for a in sorted(aliases, key=len, reverse=True):
                if not a: continue
                if a.upper() in SHORT_RATING_CODES and not in_rating_field:
                    continue        # single/double letters only inside a rating structure
                if self._alias_hits(a, low):
                    base, fine = self.fine.get(a, (canon, None))
                    out.append({"rating": base, "fine": fine, "alias": a,
                                "candidates": [base] if not fine else [base, fine],
                                "scope": "SOURCE_REQUIRED" if fine and fine != base else "SINGLE"})
                    break
        out.sort(key=lambda h: (-len(h["alias"]), h["rating"]))
        return out

    def rating_normalize(self, s, in_rating_field=False):
        hits = self.rating_matches(s, in_rating_field)
        return hits[0]["rating"] if hits else None

    def rating_structures(self, s):
        """Structured rating cells: (4171,NR_未評等), (6533,N,中立), 評等: B, Rating: OW ..."""
        found = []
        for m in re.finditer(r"\(\s*([1-9]\d{3})\s*,\s*([A-Za-z]{1,2})\s*[_,]\s*([^)]{1,12})\)", s or ""):
            code = m.group(2).upper()
            label = m.group(3)
            found.append({"ticker": m.group(1), "code": code, "label": label,
                          "rating": self.SHORT.get(code) or self.rating_normalize(label) or "",
                          "source": "FILENAME_STRUCTURE"})
        for m in re.finditer(r"(?:投資評等|投資評級|投資建議|評等|評級|rating|recommendation)\s*[:：]\s*([A-Za-z]{1,2}|[^\s,，;；)]{2,12})", s or "", re.I):
            token = m.group(1)
            if re.fullmatch(r"[A-Za-z]{1,2}", token):
                rating = self.SHORT.get(token.upper())
            else:
                rating = self.rating_normalize(token, True)
            if rating:
                found.append({"code": token, "rating": rating, "source": "RATING_FIELD"})
        return found

    def rating_action(self, s):
        low = (s or "").lower()
        for action, words in RATING_ACTIONS.items():
            if any(w.lower() in low for w in words):
                return action
        return ""

    def validate_rating(self, s, in_rating_field=False):
        structures = self.rating_structures(s)
        hits = self.rating_matches(s, in_rating_field)
        if structures and structures[0].get("rating"):
            c = structures[0]["rating"]
            return {"raw": s, "canonical": c, "in_dict": True, "fine": None, "candidates": [c],
                    "scope": "STRUCTURE", "action": self.rating_action(s), "structure": structures[0]}
        if hits:
            h = hits[0]
            return {"raw": s, "canonical": h["rating"], "in_dict": True, "fine": h["fine"],
                    "candidates": h["candidates"], "scope": h["scope"], "alias": h["alias"],
                    "action": self.rating_action(s)}
        return {"raw": s, "canonical": None, "in_dict": False, "fine": None, "candidates": [],
                "scope": "NONE", "action": self.rating_action(s)}

# ---------------------------------------------------------------------
# FIELD VALIDATION  (email / tel / target price)
# ---------------------------------------------------------------------
class FieldValidation:
    _TEL = re.compile(r"(?:\+?886[-\s]?|\(0\d\)\s?|0)\d(?:[-\s]?\d){7,9}")
    _PRICE = r"(?:NT\$|NT\s?\$|新台幣|TWD|NTD|US\$|USD|HK\$)?\s*([0-9][0-9,]*\.?\d*)\s*(?:元|美元|港元)?(?!\s*[%倍xX])"
    _SCENARIO = re.compile(r"\b(base|bull|bear)\s*case\b[^0-9]{0,40}([0-9][0-9,]*\.?\d*)", re.I)

    def __init__(self, brd=None):
        self.brd = brd or BrokerRatingDict()
        self._tp = None

    def _tp_regex(self):
        if self._tp is None:
            terms = sorted(self.brd.target_terms, key=len, reverse=True)
            alts = []
            for t in terms:
                esc = re.escape(t)
                if re.search(r"[一-鿿]", t):
                    alts.append(esc)
                else:
                    alts.append(r"(?<![A-Za-z])" + esc + r"(?![A-Za-z])")
            self._tp = re.compile(r"(?:" + "|".join(alts) + r")\s*[:：]?\s*(?:\((?:NT\$|TWD)\))?\s*" + self._PRICE, re.I)
        return self._tp

    def extract_tel(self, text):
        out = []
        for m in self._TEL.finditer(text or ""):
            t = m.group(0).strip()
            digits = re.sub(r"\D", "", t)
            if 8 <= len(digits) <= 12: out.append(t)
        return out

    def validate_email(self, email, broker_canon=None):
        m = re.match(r"([A-Za-z][A-Za-z.\-_]*)@([A-Za-z0-9.\-]+)$", email or "")
        if not m: return {"email": email, "valid": False, "broker_match": None}
        domain = m.group(2)
        dom_broker = self.brd.broker_normalize(domain.replace(".", " "))
        return {"email": email, "valid": True, "domain": domain,
                "domain_broker": dom_broker,
                "broker_match": (broker_canon is None) or (dom_broker is None) or (dom_broker == broker_canon)}

    def extract_target_price(self, text):
        m = self._tp_regex().search(text or "")
        if not m: return None
        try: return float(m.group(1).replace(",", ""))
        except ValueError: return None

    def extract_target_prices(self, text):
        """Every target-price mention plus Base/Bull/Bear scenarios; never picks the maximum."""
        out = {"values": [], "scenarios": {}}
        for m in self._tp_regex().finditer(text or ""):
            try: out["values"].append(float(m.group(1).replace(",", "")))
            except ValueError: continue
        for m in self._SCENARIO.finditer(text or ""):
            try: out["scenarios"][m.group(1).upper()] = float(m.group(2).replace(",", ""))
            except ValueError: continue
        out["primary"] = out["values"][0] if out["values"] else None
        out["ambiguous"] = len(set(out["values"])) > 1
        return out

    def extract_current_price(self, text):
        rx = re.compile(r"(?<!目標)(?<!Target )(?<!target )(?:最新收盤價|收盤價|現價|股價|最新股價|current\s*price|share\s*price|close|last\s*price)"
                        r"\s*[:：]?\s*(?:\((?:NT\$|TWD)\))?\s*(?:NT\$|NT\s?\$|新台幣|TWD|NTD)?\s*([0-9][0-9,]*\.?\d*)\s*(?:元)?(?!\s*[%倍xX])", re.I)
        m = rx.search(text or "")
        if not m: return None
        try: return float(m.group(1).replace(",", ""))
        except ValueError: return None

    def validate_target_price(self, tp, per=None, eps=None, current=None, fin=None):
        res = {"target_price": tp, "checks": []}
        if tp is None or tp <= 0:
            res["checks"].append({"name": "positive", "ok": False}); res["verdict"] = "FAIL" if tp is not None else "UNDISCLOSED"; return res
        res["checks"].append({"name": "positive", "ok": True})
        if per and eps and fin:
            mul = fin.multiply(tp, per, eps)
            res["checks"].append({"name": "TP=PER*EPS", "ok": mul["verdict"] in ("PASS", "PASS-SOFT"), "detail": mul})
        if current:
            up = (tp - current) / current
            res["checks"].append({"name": "upside_sane", "ok": abs(up) <= 2.0, "upside": round(up, 4)})
        res["verdict"] = "PASS" if all(c["ok"] for c in res["checks"]) else "WARN"
        return res

# ---------------------------------------------------------------------
# CROSS VALIDATION
# ---------------------------------------------------------------------
class CrossValidation:
    @staticmethod
    def four_way(filename_ticker, title_ticker, table_ticker=None, financials_ticker=None):
        vals = [("filename", filename_ticker), ("title", title_ticker),
                ("table", table_ticker), ("financials", financials_ticker)]
        present = [(k, v) for k, v in vals if v]
        agree = len({v for _, v in present}) <= 1
        return {"verdict": "PASS" if agree and present else ("FAIL" if present else "N/A"),
                "sources": dict(present)}

    @staticmethod
    def filename_vs_page(fn, page):
        """fn/page dicts with keys ticker/broker/date. GREEN if all present agree."""
        out = {"fields": {}, "verdict": "PASS"}
        for key in ("ticker", "broker", "date"):
            a, b = fn.get(key), page.get(key)
            if a and b:
                ok = (a == b)
                out["fields"][key] = {"filename": a, "page": b, "match": ok}
                if not ok: out["verdict"] = "FAIL"
            else:
                out["fields"][key] = {"filename": a, "page": b, "match": None}
        return out

    @staticmethod
    def filename_vs_page_core(fnf, core):
        """v0103 contract: FAIL only when the page contradicts the filename on the ticker (the page's own
        primary code differs and the filename code is absent) or when strong page evidence names another
        broker.  A differing date is CONFLICT (kept, never picked silently): reports are often filed later."""
        out = {"fields": {}, "verdict": "PASS"}
        tri = core.get("tri_code") or {}
        page_primary = (core.get("ticker") or {}).get("ticker")
        t_state = {"PASS": True, "MISMATCH": False}.get(tri.get("verdict"))
        out["fields"]["ticker"] = {"filename": fnf.get("ticker"), "page": page_primary, "match": t_state,
                                   "verdict": tri.get("verdict")}
        b_verdict = core.get("broker_vs_filename")
        out["fields"]["broker"] = {"filename": fnf.get("broker"), "page": (core.get("broker") or {}).get("broker"),
                                   "match": {"PASS": True, "MISMATCH": False}.get(b_verdict), "verdict": b_verdict,
                                   "tier": (core.get("broker") or {}).get("tier")}
        pd, fd = (core.get("page_date") or {}).get("iso"), fnf.get("date")
        out["fields"]["date"] = {"filename": fd, "page": pd, "match": (pd == fd) if (pd and fd) else None,
                                 "verdict": ("PASS" if pd == fd else "CONFLICT") if (pd and fd) else "INSUFFICIENT_EVIDENCE"}
        if tri.get("verdict") == "MISMATCH" or b_verdict == "MISMATCH":
            out["verdict"] = "FAIL"
        elif out["fields"]["date"]["verdict"] == "CONFLICT" or b_verdict in ("AMBIGUOUS",):
            out["verdict"] = "WARN"
        return out

    @staticmethod
    def tri_code(filename_ticker, page_codes):
        """Spec section 2 verdict from filename core vs page platform codes (list of tricode dicts)."""
        cores = {c.get("core") for c in (page_codes or []) if c.get("core")}
        if not filename_ticker and not cores:
            return {"verdict": "N/A", "cores": sorted(cores)}
        if not filename_ticker or not cores:
            return {"verdict": "INSUFFICIENT_EVIDENCE", "cores": sorted(cores), "filename": filename_ticker or ""}
        if cores == {filename_ticker}:
            return {"verdict": "PASS", "cores": sorted(cores), "filename": filename_ticker}
        return {"verdict": "MISMATCH", "cores": sorted(cores), "filename": filename_ticker}

    @staticmethod
    def zone_presence(info_zone_fields, body_zone_fields):
        """each expected zone must yield data; append-only categorization."""
        return {"info_zone": {"has_data": bool(info_zone_fields), "n": len(info_zone_fields or [])},
                "body_zone": {"has_data": bool(body_zone_fields), "n": len(body_zone_fields or [])},
                "verdict": "PASS" if (info_zone_fields and body_zone_fields) else "WARN"}

    @staticmethod
    def historical_vs_source(report_vals, source_vals, tol=0.05):
        """report_vals/source_vals: dict{year: value}. TWSE/TPEx as authority for actuals."""
        out = {"years": {}, "verdict": "PASS"}
        for y in sorted(set(report_vals) & set(source_vals)):
            rv, sv = report_vals[y], source_vals[y]
            if sv in (None, 0): out["years"][y] = {"report": rv, "source": sv, "match": None}; continue
            err = abs((rv - sv) / sv)
            ok = err <= tol
            out["years"][y] = {"report": rv, "source": sv, "rel_err": round(err, 4), "match": ok,
                               "canonical": sv, "report_value_kept": rv}
            if not ok: out["verdict"] = "FAIL"
        return out

# =====================================================================
# 9 · FOUR-POINT SUMMARY (spec section 5 data contract)
# =====================================================================
class FourPointSummary:
    @staticmethod
    def build(official_name, yahoo_code, title, rating, target, upside, eps, momentum, catalysts, sources):
        header = "%s(%s)-%s" % (official_name or "官方名稱待查", yahoo_code or "代碼待核對", title or "首頁主標題未揭露")
        def point(text, fields):
            return {"text": text or "未揭露", "disclosed": bool(text), "fields": fields, "source_ids": list(sources or [])}
        return {
            "header": header,
            "points": [
                point(" / ".join(x for x in [rating and ("評等 " + rating), target and ("目標價 " + str(target)),
                                            upside and upside.get("status") == "DERIVED" and ("上漲空間 %.2f%% (DERIVED)" % upside["upside_pct"]),
                                            upside and upside.get("status") == "DERIVED_ADJ" and
                                            ("上漲空間 %.1f%% (ADJ;最新 adj close %s)" % (upside["upside_pct"], upside.get("price_date") or ""))] if x),
                      {"rating": rating, "target_price": target, "upside": upside}),
                point(eps and ("稀釋 EPS " + str(eps)), {"eps_diluted": eps}),
                point(momentum, {"momentum": momentum}),
                point(catalysts, {"catalysts": catalysts}),
            ],
            "rule": "first page only; every sentence links back to a source_id; nothing invented",
        }

# =====================================================================
# ORCHESTRATOR
# =====================================================================
class FirstPageEngine:
    def __init__(self, ssot_path=None, official_set=None, nlp_engine=None, knowledge_root=None, load_knowledge=True):
        paths = find_knowledge_paths(knowledge_root) if load_knowledge else {}
        self.knowledge_paths = paths
        knowledge = {
            "broker_dict": load_broker_dict(paths.get("broker_dict")) if paths else {},
            "rating_dict": load_rating_dict(paths.get("rating_dict")) if paths else {},
            "synonyms": load_synonym_library(paths.get("synonym_library")) if paths else {},
            "ticker_master": load_ticker_master(paths.get("ticker_master")) if paths else None,
        }
        self.knowledge = knowledge
        self.tf = TickerFilename(ssot_path or (paths.get("ticker_ssot") if paths else None), official_set, knowledge)
        self.layout = Layout()
        self.tg = TableGeometry()
        self.nlp = NLPRepair(nlp_engine)
        self.fin = FinancialValidation()
        self.price = PriceAdjustment()
        self.brd = BrokerRatingDict(knowledge=knowledge)
        self.fv = FieldValidation(self.brd)
        self.xv = CrossValidation()
        self.summary = FourPointSummary()

    def _filename_fields(self, filename):
        p = self.tf.parse_filename(filename)
        ticker = p["tickers"][0] if p["tickers"] else None
        date = p["dates"][0] if p["dates"] else None
        broker = None
        broker_hit = None
        # spec: brokers may be identified from filename fragments, longest alias first,
        # company fragments after the code are excluded, first tokens are preferred
        ordered = [t for t, k in p["tokens"] if k in ("CJK", "LATIN")]
        scored = []
        for idx, tok in enumerate(ordered):
            for hit in self.brd.broker_matches(tok, exclude_prefix_fragments=p["company_fragments"]):
                scored.append((-len(hit["alias"]), idx, hit))      # longest alias first, then earliest token
        if scored:
            scored.sort(key=lambda s: (s[0], s[1], s[2]["broker"]))
            broker, broker_hit = scored[0][2]["broker"], scored[0][2]
        if not broker:
            stem = self.tf.strip_ext(filename)
            hits = self.brd.broker_matches(stem, exclude_prefix_fragments=p["company_fragments"])
            if hits:
                broker, broker_hit = hits[0]["broker"], hits[0]
        rating = self.brd.validate_rating(self.tf.strip_ext(filename))
        return {"ticker": ticker, "broker": broker, "broker_hit": broker_hit, "date": date,
                "date_display": self.tf.to_display(date) if date else "", "parse": p,
                "rating": rating["canonical"], "rating_detail": rating,
                "date_status": "FILENAME_CANDIDATE" if date else ("YEAR_MISSING" if p["partial_dates"] else "NO_COMPLETE_DATE"),
                "ticker_status": "FILENAME_CANDIDATE" if ticker else ("ETF_CANDIDATE" if p["etf"] else "NO_TICKER")}

    def classification(self, code):
        master = self.knowledge.get("ticker_master")
        if master is None or not code:
            return None
        try:
            return master.classify_ticker(code)
        except Exception:
            return None

    def adj_upside(self, ticker, report_date, target_price, currency=None, page_price=None):
        """v0104 (operator 2026-09-24): the upside over the LATEST adj close, with the target and the day-before
        prices in ADJ CLOSE terms -- VRN_Evidence_Core.adj_basis (ENG073 adj_quote, the mother's one L99 formula).
        status DERIVED_ADJ when the engine answers a number, else NO_ADJ with its state and reason.
        self.adj_db names a market database explicitly (tests); self.use_adj = False switches the lookup off."""
        up = {"status": "NO_ADJ", "basis": "ADJ_LATEST", "upside_pct": None, "target_price": target_price,
              "formula": "(target x adj factor / latest adj close - 1) * 100%  [L99, ENG073 adj_quote]"}
        cur = str(currency or "").upper()
        if EVIDENCE_CORE is None or not hasattr(EVIDENCE_CORE, "adj_basis") or not getattr(self, "use_adj", True):
            up.update(state="ADJ_OFF", why="the evidence core has no adj_basis (or use_adj is off)")
            return up
        if cur and cur not in ("TWD", "TWD?"):
            up.update(state="ADJ_CURRENCY(%s)" % cur, why="a %s target is not put on the TW adj close" % cur)
            return up
        try:
            q = EVIDENCE_CORE.adj_basis(ticker, report_date, target_price, db=getattr(self, "adj_db", None))
        except Exception as exc:          # graceful: the page answer stays in upside_page
            q = {"state": "ADJ_ERROR", "why": "%s: %s" % (type(exc).__name__, exc)}
        fac = q.get("adj_factor")
        up.update({
            "status": "DERIVED_ADJ" if q.get("upside_adj") is not None else "NO_ADJ",
            "upside_pct": q.get("upside_adj"), "target_price_adj": q.get("target_price_adj"),
            "current_price": q.get("price_latest_adj"), "price_date": q.get("price_latest_date"),
            "adj_factor": fac, "adj_factor_date": q.get("adj_factor_date"),
            "price_prev_close": q.get("price_prev_close"), "price_prev_adj": q.get("price_prev_adj"),
            "price_prev_date": q.get("price_prev_date"), "page_price": page_price,
            "page_price_adj": round(page_price * fac, 4) if (page_price and fac) else None,
            "report_age_days": q.get("report_age_days"), "target_freshness": q.get("target_freshness"),
            "state": q.get("state"), "why": q.get("why") or "", "ticker": q.get("ticker"), "engine": q.get("engine")})
        return up

    def run(self, filename, chars=None, title_codes=None, table_chars=None,
            per=None, eps=None, current_price=None, source_historical=None, report_historical=None,
            official_name="", official_market=None, page_width=None, page_height=None, source_path=None):
        out = {"filename": filename, "engine": "VIA_VRN_FirstPageEngine " + ENGINE_VERSION,
               "governance": "append-only; raw+repaired coexist; LIVE off; no network"}
        if page_width or page_height:
            self.layout = Layout(page_height or 842.0, page_width or 595.0)
        fnf = self._filename_fields(filename)
        out["filename_parse"] = fnf["parse"]
        out["filename_fields"] = {k: fnf[k] for k in ("ticker", "broker", "date", "date_display", "rating", "date_status", "ticker_status")}
        lay = self.layout.classify(chars) if chars else {"company_name": "", "main_text": "", "footer": "", "footer_kept": "", "lines": []}
        out["layout"] = {"company_name": lay["company_name"], "footer_excluded": bool(lay["footer"]),
                         "footer_kept": lay.get("footer_kept", ""), "line_count": len(lay.get("lines", []))}
        title = lay["company_name"]; body = lay["main_text"]
        full_text = "\n".join(l["text"] for l in lay.get("lines", [])) or (lay["footer"] + " " + body)
        res = self.tf.resolve(filename, title, body)
        core = None
        if EVIDENCE_CORE is not None and getattr(self, "use_core", True):
            try:
                core = EVIDENCE_CORE.analyze(filename, [l["text"] for l in lay.get("lines", [])],
                                             alias_table=self.brd.b, filename_ticker=fnf["ticker"],
                                             filename_date=fnf["date"], filename_broker=fnf["broker"],
                                             official_market=official_market, text_layer=bool(chars))
            except Exception as exc:          # graceful: the v0102 path still answers
                core = {"error": "%s: %s" % (type(exc).__name__, exc)}
        out["ticker"] = res
        out["ticker_classification"] = self.classification(res.get("ticker"))
        out["main_text_raw"] = body
        out["main_text_repaired"] = self.nlp.repair_text(body)

        # analyst email / tel / rating / target price
        emails = self.tf.parse_email(full_text)
        out["emails"] = emails
        out["tel"] = self.fv.extract_tel(full_text)
        page_hits = self.brd.broker_matches(full_text)
        page_broker = page_hits[0]["broker"] if page_hits else None
        out["broker"] = page_broker or fnf["broker"]
        out["broker_page"] = page_broker
        out["broker_filename"] = fnf["broker"]
        if core and not core.get("error"):
            ev = core["broker"]
            out["broker_page_legacy"] = page_broker
            page_broker = ev["broker"] if ev.get("strong") else None
            denied = core.get("broker_vs_filename") == "DENIED"
            out["broker"] = ev["broker"] or (None if denied else fnf["broker"])
            out["broker_page"] = page_broker
            out["broker_tier"] = ev.get("tier")
            out["broker_vs_filename"] = core.get("broker_vs_filename")
            out["broker_denied"] = ev.get("denied") or ({fnf["broker"]: 1} if denied else {})
        # v0104 (mother 批729; operator 2026-09-24): the appendix small print on the last pages names the issuer.
        # It fills the broker only when page 1 has no strong evidence; a strong page 1 is never overruled, and an
        # appendix issuer that disagrees with the filename is flagged for review instead of silently winning.
        if source_path and EVIDENCE_CORE is not None and hasattr(EVIDENCE_CORE, "appendix_evidence"):
            try:
                app = EVIDENCE_CORE.appendix_evidence(source_path, alias_table=self.brd.b, filename_broker=fnf["broker"])
            except Exception as exc:          # graceful: the page-1 answer stands
                app = {"state": "ERROR", "error": "%s: %s" % (type(exc).__name__, exc), "broker": {}, "rating_scale": []}
            out["appendix"] = {"state": app.get("state"), "error": app.get("error"), "info": app.get("info"),
                               "broker": (app.get("broker") or {}).get("broker"), "tier": (app.get("broker") or {}).get("tier"),
                               "strong": bool((app.get("broker") or {}).get("strong")), "vs_filename": app.get("vs_filename"),
                               "evidence": ((app.get("broker") or {}).get("evidence") or [])[:8],
                               "denied": (app.get("broker") or {}).get("denied") or {},
                               "rating_scale": app.get("rating_scale") or [], "n_lines": app.get("n_lines", 0)}
            page_strong = out.get("broker_tier") in ("EMAIL", "DISCLOSURE", "ISSUER")
            ab = out["appendix"]
            if ab["strong"] and ab["broker"] and not page_strong:
                if not fnf["broker"] or ab["broker"] == fnf["broker"]:
                    out["broker_page"] = ab["broker"]
                    out["broker"] = ab["broker"]
                    out["broker_tier"] = "APPENDIX_" + str(ab["tier"])
                else:
                    out["broker_conflict"] = {"filename": fnf["broker"], "appendix": ab["broker"], "state": "REVIEW"}
        # spec section 4: a rating needs a structure, a rating label or the info zone; body prose alone is only a hint
        label_rx = re.compile(r"投資評等|投資評級|投資建議|評等|評級|rating|recommendation|目標價|target\s*price", re.I)
        evidence_lines = [l["text"] for l in lay.get("lines", [])
                          if l.get("level") in ("MAIN_TITLE", "HEADLINE", "H2") or label_rx.search(l["text"]) or l.get("keep_data")]
        rating_text = "\n".join(evidence_lines + [self.tf.strip_ext(filename)])
        out["rating"] = self.brd.validate_rating(rating_text, in_rating_field=False)
        body_hint = self.brd.rating_matches(body)
        out["rating"]["body_hint"] = body_hint[0]["rating"] if body_hint else None
        tps = self.fv.extract_target_prices(full_text)
        tp = tps["primary"]
        out["target_prices"] = tps
        cp = current_price if current_price is not None else self.fv.extract_current_price(full_text)
        if core and not core.get("error"):
            r = core["rating"]
            out["rating_legacy"] = out["rating"]
            out["rating"] = {"raw": r.get("raw"), "canonical": r.get("value"), "fine": r.get("fine"),
                             "canonical_key": r.get("canonical_key"), "in_dict": r.get("value") is not None,
                             "scope": "EVIDENCE_CORE:" + str(r.get("source") or ""), "state": r.get("state"),
                             "action": r.get("action", ""), "candidates": [c.get("value") for c in r.get("candidates", [])][:8],
                             "body_hint": out["rating_legacy"].get("body_hint"), "kept_value": r.get("kept_value")}
            t = core["target_price"]
            out["target_prices_legacy"] = tps
            tp = t.get("value")
            out["target_prices"] = {"values": t.get("distinct_values", []), "primary": tp, "scenarios": tps.get("scenarios", {}),
                                    "ambiguous": len(t.get("distinct_values", [])) > 1, "raw": t.get("raw"),
                                    "source": t.get("source"), "state": t.get("state"), "currency": t.get("currency")}
            if current_price is None:
                out["current_price_legacy"] = cp
                cp = core["current_price"].get("value")
        out["current_price"] = cp
        out["target_price"] = self.fv.validate_target_price(tp, per=per, eps=eps, current=cp, fin=self.fin)
        out["upside"] = self.price.upside_checked(tp, cp)
        if emails:
            e0 = emails[0]["analyst_id"] + "@" + emails[0]["broker_domain"]
            out["email_validation"] = self.fv.validate_email(e0, page_broker)

        # page platform codes (tri-code cross check, spec section 2)
        page_codes = []
        for m in self.tf.rx_yf.finditer(full_text):
            page_codes.append({"raw": m.group(0), "core": m.group(1), "platform": "yfinance",
                               "market": "TPEX" if m.group(0).upper().endswith(".TWO") else "TWSE"})
        for m in self.tf.rx_bb.finditer(full_text):
            page_codes.append({"raw": m.group(0), "core": m.group(1), "platform": "bloomberg", "market": ""})
        out["page_codes"] = page_codes
        out["tri_code"] = self.xv.tri_code(fnf["ticker"] or res.get("ticker") or "", page_codes)
        if core and not core.get("error"):
            out["tri_code_legacy"] = out["tri_code"]
            out["tri_code"] = dict(core["tri_code"])
            out["page_codes_core"] = core.get("page_codes", [])
        if out["tri_code"]["verdict"] == "PASS" and official_market:
            yf = next((c for c in page_codes if c["platform"] == "yfinance"), None)
            if yf and yf["market"] != str(official_market).upper():
                out["tri_code"]["verdict"] = "MARKET_MISMATCH"

        # dates: filename first, page as fallback (ISO inside, YYYY/MM/DD for display)
        page_date = None
        m = re.search(r"(?<!\d)((?:19|20)\d{2}|1\d{2})[./\-年](0?[1-9]|1[0-2])[./\-月](0?[1-9]|[12]\d|3[01])日?(?!\d)", full_text)
        if m:
            y = int(m.group(1)); y = y + 1911 if y < 1000 else y
            page_date = TickerFilename._calendar(y, m.group(2), m.group(3))
        if not page_date:
            m = re.search(r"(?<!\d)((?:19|20)\d{6})(?!\d)", full_text)
            page_date = TickerFilename.numtoken_to_date(m.group(1)) if m else None
        if core and not core.get("error"):
            out["page_date_legacy"] = page_date
            page_date = core["page_date"].get("iso")
        # mother source priority (本文 > 首頁周邊 > 檔名): the page date leads, the filename date is kept
        out["report_date"] = page_date or fnf["date"] or ""
        out["report_date_display"] = TickerFilename.to_display(out["report_date"])
        out["report_date_source"] = "PAGE" if page_date else ("FILENAME" if fnf["date"] else "")
        out["page_date"] = page_date
        out["date_conflict"] = bool(page_date and fnf["date"] and page_date != fnf["date"])
        # v0104 (operator 2026-09-24): the upside is on the latest ADJ close; the page arithmetic stays as evidence
        core_ok = bool(core and not core.get("error"))
        adj_ticker = ((core.get("ticker") or {}).get("ticker") if core_ok else None) or res.get("ticker") or fnf["ticker"]
        if core_ok and (core.get("report_type") or {}).get("type") not in (None, "", "STOCK"):
            adj_ticker = None                 # industry / market / macro report: no covered company to price
        out["upside_page"] = out["upside"]
        out["upside"] = self.adj_upside(adj_ticker, out["report_date"], tp,
                                        currency=out["target_prices"].get("currency"), page_price=cp)

        # cross validations
        out["xv_filename_vs_page"] = self.xv.filename_vs_page(
            {"ticker": fnf["ticker"], "broker": fnf["broker"], "date": fnf["date"]},
            {"ticker": (page_codes[0]["core"] if page_codes else (res["ticker"] or None)), "broker": page_broker, "date": page_date})
        if core and not core.get("error"):
            out["xv_filename_vs_page_legacy"] = out["xv_filename_vs_page"]
            out["xv_filename_vs_page"] = self.xv.filename_vs_page_core(fnf, core)
            out["report_type"] = core["report_type"]
            out["ticker_page"] = core["ticker"]
            out["analysts"] = core.get("analysts", [])
            out["company_name_page"] = core.get("company_name")
            out["evidence_core"] = {"core": core.get("core"), "vcgc": core.get("vcgc"), "text_layer": core.get("text_layer"),
                                    "broker_evidence": core["broker"].get("evidence", [])[:12],
                                    "rating_state": core["rating"].get("state"), "tp_state": core["target_price"].get("state"),
                                    "cp_state": core["current_price"].get("state"), "date_state": core["page_date"].get("state")}
        elif core:
            out["evidence_core"] = {"error": core.get("error")}
        info_zone = [x for x in [tp, out["rating"]["canonical"], page_broker] if x]
        body_zone = self.nlp.split_sentences(body)
        out["xv_zone_presence"] = self.xv.zone_presence(info_zone, body_zone)
        if title_codes:
            out["cross_check"] = self.tf.cross_check(res["ticker"], official_market=official_market, **title_codes)
        if table_chars:
            out["table"] = self.tg.reconstruct(table_chars)
        if source_historical and report_historical:
            out["xv_historical"] = self.xv.historical_vs_source(report_historical, source_historical)
        yahoo = ""
        if res.get("ticker") and official_market:
            yahoo = res["ticker"] + (".TWO" if str(official_market).upper() == "TPEX" else ".TW")
        elif page_codes and page_codes[0]["platform"] == "yfinance":
            yahoo = page_codes[0]["raw"]
        sentences = body_zone
        out["summary_four_points"] = self.summary.build(
            official_name or res.get("name") or "", yahoo, title, out["rating"]["canonical"], tp, out["upside"],
            eps, sentences[0] if sentences else "", sentences[1] if len(sentences) > 1 else "",
            [l["source_id"] for l in lay.get("lines", []) if l.get("level") == "BODY"][:8])
        return out


# =====================================================================
# CLI
# =====================================================================
def _chars_from_pdf(path):
    """First-page chars via pdfplumber (preferred) or PyMuPDF; None when neither is installed.
    v0103: through VRN_Evidence_Core.pdf_page_chars (x1/bottom kept, rotated chart labels left out)."""
    if EVIDENCE_CORE is not None:
        try:
            got = EVIDENCE_CORE.pdf_page_chars(path, 0)
            if got is not None:
                return got
        except Exception:
            pass
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                return [], (595.0, 842.0)
            page = pdf.pages[0]
            chars = [{"text": c.get("text", ""), "x0": float(c.get("x0", 0)), "top": float(c.get("top", 0)),
                      "size": float(c.get("size", 0)), "fontname": str(c.get("fontname", ""))} for c in page.chars]
            return chars, (float(page.width), float(page.height))
    except ImportError:
        pass
    except Exception:
        return None
    try:
        import fitz
        doc = fitz.open(path)
        if len(doc) == 0:
            return [], (595.0, 842.0)
        page = doc[0]
        chars = []
        for block in page.get_text("rawdict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    for ch in span.get("chars", []):
                        chars.append({"text": ch.get("c", ""), "x0": float(ch["bbox"][0]), "top": float(ch["bbox"][1]),
                                      "size": float(span.get("size", 0)), "fontname": str(span.get("font", ""))})
        size = (float(page.rect.width), float(page.rect.height))
        doc.close()
        return chars, size
    except Exception:
        return None


def _chars_from_docx(path):
    """Synthesize chars from DOCX paragraphs (one line per paragraph, heading size by style).
    v0103: header, text boxes, body, tables and footer through VRN_Evidence_Core.docx_lines (華南 memos
    print the date in a header text box and the issuer only in the footer)."""
    if EVIDENCE_CORE is not None:
        try:
            got = EVIDENCE_CORE.docx_lines(path)
        except Exception:
            got = None
        if got:
            lines, sizes = got
            chars, top = [], 60.0
            for text, size in zip(lines, sizes):
                size = float(size or 10.0)
                x = 60.0
                for ch in text:
                    width = size * (1.0 if ord(ch) > 255 else 0.55)
                    chars.append({"text": ch, "x0": x, "x1": x + width, "top": top, "bottom": top + size,
                                  "size": size, "fontname": "Regular"})
                    x += width
                top += size * 1.6
            return chars, (595.0, max(842.0, top + 40.0))
    try:
        import docx
    except ImportError:
        return None
    try:
        document = docx.Document(path)
    except Exception:
        return None
    chars = []
    top = 60.0
    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name if para.style is not None else "") or ""
        size = 18.0 if "Title" in style else 14.0 if "Heading" in style else 10.0
        run_sizes = [run.font.size.pt for run in para.runs if run.font is not None and run.font.size is not None]
        if run_sizes:
            size = float(max(run_sizes))
        bold = any(run.bold for run in para.runs if run.bold)
        x = 60.0
        for ch in text:
            chars.append({"text": ch, "x0": x, "top": top, "size": size, "fontname": "Bold" if bold else "Regular"})
            x += size * (1.0 if ord(ch) > 255 else 0.55)
        top += size * 1.6
    for table in document.tables:
        for row in table.rows:
            x = 60.0
            for cell in row.cells:
                for ch in cell.text.strip():
                    chars.append({"text": ch, "x0": x, "top": top, "size": 10.0, "fontname": "Regular"})
                    x += 10.0 * (1.0 if ord(ch) > 255 else 0.55)
                x += 40.0
            top += 16.0
    return chars, (595.0, max(842.0, top + 40.0))


def main(argv=None):
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)   # 'Could not get FontBBox …' is noise, not an error
    import argparse
    parser = argparse.ArgumentParser(description="VIA_VRN_FirstPageEngine " + ENGINE_VERSION + " (LIVE off, no network)")
    parser.add_argument("--filename", help="filename-only contract: ticker / date / broker / rating")
    parser.add_argument("--pdf", help="PDF path: first-page chars through pdfplumber or PyMuPDF")
    parser.add_argument("--docx", help="DOCX path: paragraphs and tables as synthetic lines")
    parser.add_argument("--json", help="write the result to this path (UTF-8)")
    parser.add_argument("--no-knowledge", action="store_true", help="built-in tables only")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    engine = FirstPageEngine(load_knowledge=not args.no_knowledge)
    if not (args.filename or args.pdf or args.docx):
        print("VIA_VRN_FirstPageEngine " + ENGINE_VERSION + " import OK")
        return 0
    chars, size = None, (None, None)
    name = args.filename or os.path.basename(args.pdf or args.docx)
    if args.pdf:
        got = _chars_from_pdf(args.pdf)
        if got is not None:
            chars, size = got
    elif args.docx:
        got = _chars_from_docx(args.docx)
        if got is not None:
            chars, size = got
    result = engine.run(name, chars=chars, page_width=size[0], page_height=size[1], source_path=args.pdf)
    payload = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
