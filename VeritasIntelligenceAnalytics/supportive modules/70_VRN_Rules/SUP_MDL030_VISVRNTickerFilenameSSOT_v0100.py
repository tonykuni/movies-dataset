# -*- coding: utf-8 -*-
"""
VIS_VRN_TickerFilenameSSOT  (reference build for review)
- Corrected TW ticker regex trio
- Filename tokenizer (CJK/EN punctuation + space -> runs of CJK / Latin / digits)
- Tri-code cross-check (filename ticker <-> first-page info-zone ticker)
- 2021-2030 year false-positive disambiguation
Append-only: this is a NEW module, it does not modify existing SSOT files.
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
import re, unicodedata

# ---------------------------------------------------------------
# 1. CORRECTED TICKER REGEX TRIO
#    Rule: 4 digits, first digit != 0.  Year-exclusion is NO LONGER
#    baked into the regex (that wrongly killed real tickers like 2027).
#    Instead a separate disambiguation layer handles 2021-2030.
# ---------------------------------------------------------------
TW_TICKER_REGEX          = re.compile(r"(?<!\d)([1-9]\d{3})(?!\d)")
TW_YFINANCE_TICKER_REGEX = re.compile(r"(?<!\d)([1-9]\d{3})\.(TW|TWO)\b", re.IGNORECASE)
TW_BLOOMBERG_TICKER_REGEX= re.compile(r"(?<!\d)([1-9]\d{3})\s+TT\b", re.IGNORECASE)

# year ambiguity band per spec
YEAR_BAND = range(2021, 2031)  # 2021..2030 inclusive

# Known REAL TWSE/TPEX tickers that fall inside 2021-2030 (the trap set).
# This is the proof that the OLD (?!202[1-9])(?!2030) exclusion was WRONG.
KNOWN_REAL_TICKERS_IN_BAND = {
    "2023": "燁輝", "2024": "志聯", "2027": "大成鋼", "2029": "盛餘",
    "2025": "千興", "2028": "威致", "2030": "彰源", "2022": "聚亨",
    "2021": "中鋼構",
}

# date-context cues around a 4-digit token => likely a YEAR not a ticker
_DATE_CUE_AFTER  = re.compile(r"^\s*[年/\-\._]?\s*(0?[1-9]|1[0-2])?")  # 2024年, 2024/03
_DATE_CUE_TOKENS = ("年", "Q1", "Q2", "Q3", "Q4", "H1", "H2", "FY", "上半年", "下半年", "第一季", "第二季", "第三季", "第四季")

def is_year_band(tok: str) -> bool:
    return tok.isdigit() and len(tok) == 4 and int(tok) in YEAR_BAND

# ---------------------------------------------------------------
# 2. FILENAME TOKENIZER
#    Convert CJK + ASCII punctuation and whitespace into separators,
#    then emit independent runs of: CJK / Latin / Digit.
# ---------------------------------------------------------------
# punctuation we normalize to a single space separator
_PUNct = "　 \t\r\n" + \
    "．。，、；：（）()【】〔〕「」『』《》〈〉［］{}<>" + \
    "·•‧／/\\|—–-_~＿﹣－＝=＋+＊*＆&％%＃#＠@！!？?＂\"＇'｀`^＄$" + \
    ".,;:!?\"'()[]{}<>"
_SEP_RE = re.compile("[" + re.escape(_PUNct) + "]+")

def _char_class(ch: str) -> str:
    o = ord(ch)
    if ch.isdigit():
        return "DIGIT"
    # CJK unified + ext-A + compatibility + fullwidth forms that are CJK
    if (0x4E00 <= o <= 0x9FFF) or (0x3400 <= o <= 0x4DBF) or (0xF900 <= o <= 0xFAFF):
        return "CJK"
    if ("A" <= ch.upper() <= "Z"):
        return "LATIN"
    return "OTHER"

def tokenize_filename(name: str):
    """Return list of (token, kind) where kind in {CJK, LATIN, DIGIT}."""
    # strip extension
    stem = re.sub(r"\.(pdf|docx?|pptx?|png|jpe?g|tiff?|webp|heic)$", "", name, flags=re.IGNORECASE)
    # normalize fullwidth ascii digits/letters to halfwidth so 2330 == ２３３０
    stem = unicodedata.normalize("NFKC", stem)
    # punctuation -> space
    stem = _SEP_RE.sub(" ", stem)
    out = []
    for chunk in stem.split():
        chunk = chunk.strip()
        if not chunk:
            continue
        # split a mixed chunk (e.g. 台積電2330) into homogeneous runs
        cur, cur_kind = "", None
        for ch in chunk:
            k = _char_class(ch)
            if k == "OTHER":
                if cur:
                    out.append((cur, cur_kind)); cur, cur_kind = "", None
                continue
            if cur_kind is None or k == cur_kind:
                cur += ch; cur_kind = k
            else:
                out.append((cur, cur_kind)); cur, cur_kind = ch, k
        if cur:
            out.append((cur, cur_kind))
    return out

def extract_filename_ticker_candidates(name: str):
    """4-digit DIGIT tokens that satisfy TW_TICKER_REGEX."""
    toks = tokenize_filename(name)
    cands = []
    for tok, kind in toks:
        if kind == "DIGIT" and len(tok) == 4 and TW_TICKER_REGEX.fullmatch(tok):
            cands.append(tok)
    return cands, toks

# ---------------------------------------------------------------
# 3. YEAR DISAMBIGUATION
# ---------------------------------------------------------------
def disambiguate_year_vs_ticker(tok, *, firstpage_ticker=None, official_set=None, neighbor_text=""):
    """
    Returns (verdict, confidence, reason).
    verdict in {TICKER, YEAR, AMBIGUOUS}
    """
    if not is_year_band(tok):
        return ("TICKER", 1.0, "outside 2021-2030 band; plain ticker")
    # in band -> must adjudicate
    if firstpage_ticker and tok == str(firstpage_ticker):
        return ("TICKER", 0.97, "matches first-page info-zone ticker")
    if official_set is not None and tok in official_set:
        return ("TICKER", 0.9, "present in TWSE/TPEX official list")
    if any(c in neighbor_text for c in _DATE_CUE_TOKENS):
        return ("YEAR", 0.9, "date cue (年/Q/FY/季) adjacent")
    if tok in KNOWN_REAL_TICKERS_IN_BAND and not neighbor_text:
        return ("AMBIGUOUS", 0.5, f"real ticker {tok}={KNOWN_REAL_TICKERS_IN_BAND[tok]} but no corroboration")
    return ("AMBIGUOUS", 0.4, "in year band, no corroborating signal -> hold for review")

# ---------------------------------------------------------------
# 4. TRI-CODE CROSS-CHECK
# ---------------------------------------------------------------
def core4(code: str):
    m = TW_TICKER_REGEX.search(code or "")
    return m.group(1) if m else None

def cross_check_tricode(filename_ticker, raw_code=None, yf_code=None, bbg_code=None):
    """
    All three code forms' leading 4 digits must agree with filename ticker,
    and each must satisfy its own regex. Returns dict matrix.
    """
    result = {"filename_ticker": filename_ticker, "checks": [], "verdict": "PASS"}
    def add(label, value, ok, msg):
        result["checks"].append({"code": label, "value": value, "ok": ok, "msg": msg})
        if not ok: result["verdict"] = "FAIL"
    fc = filename_ticker
    if raw_code is not None:
        ok = bool(TW_TICKER_REGEX.fullmatch(raw_code)) and core4(raw_code) == fc
        add("TW_TICKER", raw_code, ok, "raw 4-digit matches & valid" if ok else "raw mismatch/invalid")
    if yf_code is not None:
        ok = bool(TW_YFINANCE_TICKER_REGEX.fullmatch(yf_code)) and core4(yf_code) == fc
        add("TW_YFINANCE", yf_code, ok, ".TW/.TWO suffix valid & core4 matches" if ok else "yfinance mismatch/invalid")
    if bbg_code is not None:
        ok = bool(TW_BLOOMBERG_TICKER_REGEX.fullmatch(bbg_code)) and core4(bbg_code) == fc
        add("TW_BLOOMBERG", bbg_code, ok, "'NNNN TT' valid & core4 matches" if ok else "bloomberg mismatch/invalid")
    return result

if __name__ == "__main__":
    print("module self-import OK")
