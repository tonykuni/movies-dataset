# -*- coding: utf-8 -*-
"""
VIA_VRN_FirstPageEngine  v0101
ALL-IN-ONE engine consolidating the VRN first-page extraction & cross-validation logic.

Modules (single file, one entry point `FirstPageEngine.run`):
  1 SSOT loader          - load _RAW_REGEX/_RAW_SYNONYMS from SSOT .py, else locked fallback
  2 TickerFilename       - tokenize, 4-digit ticker / 6-8 digit date, disambiguation ladder,
                           year-band reclaim, tri-code cross-check, email->analyst/broker
  3 Layout               - font-hierarchy (MAIN_TITLE..FOOTER), element_type, boilerplate,
                           company-name (largest+bold), sentence linking (break at period)
  4 TableGeometry        - reconstruct hidden-gridline tables via x/y clustering, period headers
  5 NLPRepair            - local heuristic sentence repair (hook to swap in via_nlp v1.5)
  6 FinancialValidation  - Add/Sub tolerance layering, Division two-stage, Historical YoY
  7 PriceAdjustment      - adjusted-price consistency
  8 CrossValidation      - filename <-> text <-> table <-> financials
Governance: append-only; raw + repaired coexist; TABLE/FIGURE never enter NLP.
"""
import re, os, json, unicodedata, statistics
from collections import defaultdict

# =====================================================================
# 1 · SSOT LOADER
# =====================================================================
_LOCK = {
    "TW_STOCK_CODE_4DIGIT": r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
    "TW_YFINANCE_TICKER":   r"([1-9]\d{3})\.(TW|TWO)",
    "TW_BLOOMBERG_TICKER":  r"([1-9]\d{3})\s+TT",
}

def load_ssot_blocks(ssot_path):
    blocks = {}
    if not (ssot_path and os.path.exists(ssot_path)):
        return blocks
    txt = open(ssot_path, encoding="utf-8", errors="replace").read()
    for var in ("_RAW_REGEX", "_RAW_LISTS", "_RAW_SYNONYMS"):
        m = re.search(var + r"\s*[:=][^=]*=?\s*json\.loads\(r'''(.*?)'''\)", txt, re.S)
        if m:
            try: blocks[var] = json.loads(m.group(1))
            except Exception: blocks[var] = []
    return blocks

# =====================================================================
# 2 · TICKER / FILENAME
# =====================================================================
class TickerFilename:
    _PUN = ("　 \t\r\n．。，、；：（）()【】〔〕「」『』《》〈〉［］{}<>"
            "·•‧／/\\|—–-_~＿＝=＋+＊*＆&％%＃#＠@！!？?＂\"＇'｀`^＄$.,;:!?\"'()[]{}<>")
    _SEP = re.compile("[" + re.escape(_PUN) + "]+")
    _SECTOR_KW = ("產業", "類股", "族群", "策略", "展望", "sector", "industry")

    def __init__(self, ssot_path=None, official_set=None):
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
            cn = next((a for a in names if re.search(r"[\u4e00-\u9fff]", a)), (names[0] if names else ""))
            self.tk2name[tk] = cn
            for a in s.get("aliases", []) + [canon]:
                self.alias2tk[a] = tk
        self.official_set = set(official_set) if official_set else None

    @staticmethod
    def is_valid_bare(t): return bool(re.fullmatch(r"[1-9]\d{3}", t or ""))

    @staticmethod
    def numtoken_to_date(tok):
        if not (tok and tok.isdigit()): return None
        if len(tok) == 8: y, mo, d = tok[:4], tok[4:6], tok[6:8]
        elif len(tok) == 6: y, mo, d = "20"+tok[:2], tok[2:4], tok[4:6]
        else: return None
        try: iy, im, idd = int(y), int(mo), int(d)
        except ValueError: return None
        if 1990 <= iy <= 2099 and 1 <= im <= 12 and 1 <= idd <= 31:
            return "%04d-%02d-%02d" % (iy, im, idd)
        return None

    @staticmethod
    def _cls(ch):
        if ch.isdigit(): return "DIGIT"
        o = ord(ch)
        if (0x4E00<=o<=0x9FFF) or (0x3400<=o<=0x4DBF) or (0xF900<=o<=0xFAFF): return "CJK"
        if "A" <= ch.upper() <= "Z": return "LATIN"
        return "OTHER"

    def tokenize(self, name):
        stem = re.sub(r"\.(pdf|docx?|pptx?|png|jpe?g|tiff?|webp|heic)$", "", name or "", flags=re.I)
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
        res = {"tickers": [], "dates": [], "cjk": [], "latin": []}
        for tok, kind in self.tokenize(name):
            if kind == "DIGIT":
                if len(tok) == 4 and self.is_valid_bare(tok): res["tickers"].append(tok)
                else:
                    d = self.numtoken_to_date(tok)
                    if d: res["dates"].append(d)
            elif kind == "CJK": res["cjk"].append(tok)
            elif kind == "LATIN": res["latin"].append(tok)
        return res

    @staticmethod
    def parse_email(text):
        return [{"analyst_id": m.group(1), "broker_domain": m.group(2)}
                for m in re.finditer(r"([A-Za-z][A-Za-z.\-_]*)@([A-Za-z0-9.\-]+)", text or "")]

    def resolve(self, filename, title="", body=""):
        fn, title, body = filename or "", title or "", body or ""
        def suf(src):
            m = self.rx_yf.search(src) or self.rx_bb.search(src)
            return m.group(1) if m else None
        tk = suf(fn)
        if tk: return self._ok(tk, "FILE_SUFFIX")
        m = self.rx_bare_strict.search(fn)
        if m: return self._ok(m.group(1), "FILE_BARE")
        if any(k in fn for k in self._SECTOR_KW): return self._sec("SECTOR_FILE")
        tk = suf(title)
        if tk: return self._ok(tk, "TITLE_SUFFIX")
        for a, t in self.alias2tk.items():
            if a and len(a) >= 2 and re.search(r"[\u4e00-\u9fffA-Za-z]", a) and a in title:
                return self._ok(t, "TITLE_SYNONYM")
        tk = suf(body)
        if tk: return self._ok(tk, "BODY_SUFFIX")
        if any(k in title for k in self._SECTOR_KW): return self._sec("SECTOR_TITLE")
        for src, why in ((fn, "FILE"), (title, "TITLE")):
            m = self.rx_bare_any.search(src)
            if m:
                cand = m.group(1)
                if 2021 <= int(cand) <= 2030:
                    if (self.official_set and cand in self.official_set) or (cand == suf(fn+" "+title+" "+body)):
                        return self._ok(cand, "RECLAIM_"+why)
                else:
                    return self._ok(cand, why+"_BARE_ANY")
        m = self.rx_bare_strict.search(body[:600])
        if m: return self._ok(m.group(1), "BODY_BARE")
        return self._sec("NONE")

    def _ok(self, tk, method): return {"ticker": tk, "name": self.tk2name.get(tk, ""), "method": method, "is_sector": False}
    def _sec(self, method): return {"ticker": "", "name": "", "method": method, "is_sector": True}

    def cross_check(self, filename_ticker, raw=None, yf=None, bbg=None):
        res = {"filename_ticker": filename_ticker, "checks": [], "verdict": "PASS"}
        core = lambda c: (re.match(r"([1-9]\d{3})", c or "") or [None, None])[1] if re.match(r"([1-9]\d{3})", c or "") else None
        def core4(c):
            m = re.match(r"([1-9]\d{3})", c or ""); return m.group(1) if m else None
        def add(l, v, ok, msg):
            res["checks"].append({"code": l, "value": v, "ok": ok, "msg": msg})
            if not ok: res["verdict"] = "FAIL"
        if raw is not None: add("TW_TICKER", raw, self.is_valid_bare(raw) and core4(raw)==filename_ticker, "raw core4")
        if yf is not None: add("TW_YFINANCE", yf, bool(re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", yf, re.I)) and core4(yf)==filename_ticker, "yf")
        if bbg is not None: add("TW_BLOOMBERG", bbg, bool(re.fullmatch(r"[1-9]\d{3}\s+TT", bbg, re.I)) and core4(bbg)==filename_ticker, "bbg")
        return res

# =====================================================================
# 3 · LAYOUT  (font hierarchy + element_type + sentence linking)
# =====================================================================
class Layout:
    _BOILER = ("投顧", "研究部", "免責", "disclosure", "bloomberg", "reuters", "not investment advice", "for information only")

    def __init__(self, page_height=842.0):
        self.H = page_height

    @staticmethod
    def _lines_from_chars(chars):
        """group chars into text lines by rounded 'top', ordered top->bottom, left->right."""
        rows = defaultdict(list)
        for c in chars:
            rows[round(c["top"] / 3.0)].append(c)
        lines = []
        for key in sorted(rows):
            cs = sorted(rows[key], key=lambda c: c["x0"])
            text = "".join(c["text"] for c in cs)
            size = statistics.median([c["size"] for c in cs]) if cs else 0
            bold = sum(1 for c in cs if "bold" in (c.get("fontname") or "").lower()) > len(cs)/2
            top = min(c["top"] for c in cs); x0 = min(c["x0"] for c in cs)
            lines.append({"text": text, "size": round(size, 2), "bold": bold, "top": top, "x0": x0, "chars": cs})
        return lines

    def classify(self, chars):
        lines = self._lines_from_chars(chars)
        if not lines: return {"lines": [], "body_size": 0, "company_name": "", "main_text": "", "footer": ""}
        sizes = [l["size"] for l in lines]
        body_size = statistics.median(sizes)
        for l in lines:
            r = l["size"] / body_size if body_size else 1
            low = l["text"].lower()
            if l["top"] >= self.H * 0.88 or any(b in low for b in self._BOILER):
                l["level"] = "FOOTER"
            elif r >= 1.8: l["level"] = "MAIN_TITLE"
            elif r >= 1.4: l["level"] = "HEADLINE"
            elif r >= 1.15: l["level"] = "H2"
            elif r <= 0.8: l["level"] = "FOOTER"
            else: l["level"] = "BODY"
        # company name = largest + bold among non-footer; prefer top region
        cands = [l for l in lines if l["level"] in ("MAIN_TITLE", "HEADLINE")]
        company = ""
        if cands:
            cands.sort(key=lambda l: (-l["size"], not l["bold"], l["top"]))
            company = cands[0]["text"].strip()
        # main text = BODY lines not footer, joined + sentence-linked
        body_lines = [l["text"] for l in lines if l["level"] == "BODY"]
        main_text = self._link_sentences(body_lines)
        footer = " ".join(l["text"] for l in lines if l["level"] == "FOOTER")
        return {"lines": lines, "body_size": body_size, "company_name": company,
                "main_text": main_text, "footer": footer}

    @staticmethod
    def _link_sentences(body_lines):
        """rightward+downward link; break only at sentence-final punctuation."""
        buf, out = "", []
        for ln in body_lines:
            ln = ln.strip()
            if not ln: continue
            buf = (buf + " " + ln).strip() if buf else ln
            while True:
                m = re.search(r"[。.!?！？]", buf)
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
        # rows by top
        row_centers = self._cluster([c["top"] for c in chars], row_gap)
        # columns by x0 of word starts: detect column anchors via left edges
        col_centers = self._cluster([c["x0"] for c in chars], col_gap)
        grid = [["" for _ in col_centers] for _ in row_centers]
        def nearest(centers, v):
            return min(range(len(centers)), key=lambda i: abs(centers[i]-v))
        # assemble words: group chars by (row, then contiguous x within same col cluster)
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
        """normalize period tokens like 12/24A, 12/25E, 2024, 1Q25 -> canonical."""
        out = []
        for c in cells:
            c = c.strip()
            m = re.match(r"(\d{1,2})/(\d{2})([AEF]?)", c)
            if m:
                out.append({"raw": c, "period": "20%s-%s" % (m.group(2), m.group(1).zfill(2)),
                            "kind": {"A": "actual", "E": "estimate", "F": "forecast"}.get(m.group(3), "actual")})
            elif re.fullmatch(r"20\d{2}", c):
                out.append({"raw": c, "period": c, "kind": "actual"})
            else:
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
        # heuristic fallback: de-hyphenate line breaks, collapse spaces
        t = re.sub(r"(\w)-\s+(\w)", r"\1\2", raw)      # join hyphen line-wrap
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def split_sentences(self, text):
        if self.ext is not None:
            try: return self.ext.split_sentences(text)
            except Exception: pass
        parts = re.split(r"(?<=[。.!?！？])\s+", text)
        return [p.strip() for p in parts if p.strip()]

# =====================================================================
# 6 · FINANCIAL VALIDATION
# =====================================================================
class FinancialValidation:
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
                out.append({"year": y1, "yoy": None}); continue
            out.append({"year": y1, "yoy": round((v1 - v0) / abs(v0), 4)})
        return out

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
        if not current_price_adj: return None
        return round((target_price - current_price_adj) / current_price_adj, 4)

# =====================================================================
# 8 · CROSS VALIDATION
# =====================================================================
# ---------------------------------------------------------------------
# BROKER DICT / RATING DICT
# ---------------------------------------------------------------------
class BrokerRatingDict:
    BROKER = {
        "KGI": ["凱基", "kgi", "kgieworld"], "YUANTA": ["元大", "yuanta"],
        "FUBON": ["富邦", "fubon"], "CAPITAL": ["群益", "capital"],
        "PRESIDENT": ["統一", "pscnet"], "CTBC": ["中信", "中國信託", "ctbc"],
        "JPMORGAN": ["摩根", "jp morgan", "j.p. morgan", "jpm", "jpmorgan"],
        "GOLDMAN": ["高盛", "goldman", "gs"], "BOFA": ["美銀", "美林", "bofa", "merrill"],
        "MACQUARIE": ["麥格理", "macquarie", "mq"], "CITI": ["花旗", "citi"],
        "UBS": ["瑞銀", "ubs"], "DAIWA": ["大和", "daiwa"], "NOMURA": ["野村", "nomura"],
        "MORGANSTANLEY": ["摩根士丹利", "morgan stanley", "ms"], "CLSA": ["里昂", "clsa"],
    }
    RATING = {
        "BUY": ["買進", "強力買進", "加碼", "buy", "outperform", "overweight", "strong buy"],
        "HOLD": ["中立", "持有", "區間", "neutral", "hold", "market perform", "equal-weight", "equalweight"],
        "SELL": ["賣出", "減碼", "sell", "underperform", "underweight", "reduce"],
        "ADD": ["逢低", "accumulate", "add"],
    }

    def __init__(self, extra_broker=None, extra_rating=None):
        self.b = {k: set(x.lower() for x in v) for k, v in self.BROKER.items()}
        self.r = {k: set(x.lower() for x in v) for k, v in self.RATING.items()}
        for k, v in (extra_broker or {}).items(): self.b.setdefault(k, set()).update(x.lower() for x in v)
        for k, v in (extra_rating or {}).items(): self.r.setdefault(k, set()).update(x.lower() for x in v)

    def broker_normalize(self, s):
        if not s: return None
        low = s.lower()
        for canon, al in self.b.items():
            if any(a in low for a in al): return canon
        return None

    def rating_normalize(self, s):
        if not s: return None
        low = s.lower()
        for canon, al in self.r.items():
            if any(re.search(r"\b" + re.escape(a) + r"\b", low) or a in low for a in al): return canon
        return None

    def validate_rating(self, s):
        c = self.rating_normalize(s)
        return {"raw": s, "canonical": c, "in_dict": c is not None}

# ---------------------------------------------------------------------
# FIELD VALIDATION  (email / tel / target price)
# ---------------------------------------------------------------------
class FieldValidation:
    _TEL = re.compile(r"(?:\+?886[-\s]?|\(0\d\)\s?|0)\d(?:[-\s]?\d){7,9}")
    _TP = re.compile(r"(?:NT\$|NT\s?\$|目標價[:：]?\s*)\s*([0-9][0-9,]*\.?\d*)", re.I)

    def __init__(self, brd=None):
        self.brd = brd or BrokerRatingDict()

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
        dom_broker = self.brd.broker_normalize(domain)
        return {"email": email, "valid": True, "domain": domain,
                "domain_broker": dom_broker,
                "broker_match": (broker_canon is None) or (dom_broker == broker_canon)}

    def extract_target_price(self, text):
        m = self._TP.search(text or "")
        if not m: return None
        try: return float(m.group(1).replace(",", ""))
        except ValueError: return None

    def validate_target_price(self, tp, per=None, eps=None, current=None, fin=None):
        res = {"target_price": tp, "checks": []}
        if tp is None or tp <= 0:
            res["checks"].append({"name": "positive", "ok": False}); res["verdict"] = "FAIL"; return res
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
            out["years"][y] = {"report": rv, "source": sv, "rel_err": round(err, 4), "match": ok}
            if not ok: out["verdict"] = "FAIL"
        return out

# =====================================================================
# ORCHESTRATOR
# =====================================================================
class FirstPageEngine:
    def __init__(self, ssot_path=None, official_set=None, nlp_engine=None):
        self.tf = TickerFilename(ssot_path, official_set)
        self.layout = Layout()
        self.tg = TableGeometry()
        self.nlp = NLPRepair(nlp_engine)
        self.fin = FinancialValidation()
        self.price = PriceAdjustment()
        self.brd = BrokerRatingDict()
        self.fv = FieldValidation(self.brd)
        self.xv = CrossValidation()

    def _filename_fields(self, filename):
        p = self.tf.parse_filename(filename)
        ticker = p["tickers"][0] if p["tickers"] else None
        date = p["dates"][0] if p["dates"] else None
        broker = None
        for tok in p["cjk"] + p["latin"]:
            b = self.brd.broker_normalize(tok)
            if b: broker = b; break
        return {"ticker": ticker, "broker": broker, "date": date, "parse": p}

    def run(self, filename, chars=None, title_codes=None, table_chars=None,
            per=None, eps=None, current_price=None, source_historical=None, report_historical=None):
        out = {"filename": filename, "governance": "append-only; raw+repaired coexist"}
        fnf = self._filename_fields(filename)
        out["filename_parse"] = fnf["parse"]
        out["filename_fields"] = {k: fnf[k] for k in ("ticker", "broker", "date")}
        lay = self.layout.classify(chars) if chars else {"company_name": "", "main_text": "", "footer": "", "lines": []}
        out["layout"] = {"company_name": lay["company_name"], "footer_excluded": bool(lay["footer"])}
        title = lay["company_name"]; body = lay["main_text"]
        full_text = " ".join(l["text"] for l in lay.get("lines", [])) or (lay["footer"] + " " + body)
        res = self.tf.resolve(filename, title, body)
        out["ticker"] = res
        out["main_text_raw"] = body
        out["main_text_repaired"] = self.nlp.repair_text(body)

        # analyst email / tel / rating / target price
        emails = self.tf.parse_email(full_text)
        out["emails"] = emails
        out["tel"] = self.fv.extract_tel(full_text)
        page_broker = self.brd.broker_normalize(full_text)
        out["broker"] = page_broker
        out["rating"] = self.brd.validate_rating(full_text)
        tp = self.fv.extract_target_price(full_text)
        out["target_price"] = self.fv.validate_target_price(tp, per=per, eps=eps, current=current_price, fin=self.fin)
        if emails:
            e0 = emails[0]["analyst_id"] + "@" + emails[0]["broker_domain"]
            out["email_validation"] = self.fv.validate_email(e0, page_broker)

        # cross validations
        page_date = fnf["date"]  # (report date extracted upstream; use filename date as page proxy here)
        out["xv_filename_vs_page"] = self.xv.filename_vs_page(
            fnf, {"ticker": res["ticker"] or None, "broker": page_broker, "date": page_date})
        info_zone = [x for x in [tp, out["rating"]["canonical"], page_broker] if x]
        body_zone = self.nlp.split_sentences(body)
        out["xv_zone_presence"] = self.xv.zone_presence(info_zone, body_zone)
        if title_codes:
            out["cross_check"] = self.tf.cross_check(res["ticker"], **title_codes)
        if table_chars:
            out["table"] = self.tg.reconstruct(table_chars)
        if source_historical and report_historical:
            out["xv_historical"] = self.xv.historical_vs_source(report_historical, source_historical)
        return out

if __name__ == "__main__":
    print("VIA_VRN_FirstPageEngine v0101 import OK")
