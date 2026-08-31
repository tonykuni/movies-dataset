# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# -*- coding: utf-8 -*-
# VRN D8B Filename Parser  (append-only standalone module)
# Spec (Tony, 2026-05-31):
#   - normalize full-width <-> half-width punctuation
#   - split at punctuation + spaces; trim runs of consecutive ZH / EN / digits
#   - 4-digit group = TICKER, via LOCKED TW_TICKER_REGEX (excludes years 2021-2030, leading zero)
#   - date = (YY)YYMMDD : 8-digit Gregorian / 6-digit Gregorian / 7-digit ROC (民國)
#   - BASIC EPS vs DILUTED EPS distinguished (helper for D8B financial validator)
import re, unicodedata, datetime

# ---- LOCKED regexes (immutable) ----
TW_TICKER_REGEX = r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})"
_TICKER_FULL = re.compile(r"^[1-9]\d{3}$")

BROKERS = {
    "GS":"GS","MS":"MS","Daiwa":"Daiwa","JP":"JPMorgan","Citi":"Citi","UBS":"UBS",
    "CLST":"CLSA","MQ":"Macquarie","CTBC":"CTBC","GF":"GF",
    "凱基":"凱基","凱基投顧":"凱基","華南":"華南","華南投顧":"華南","兆豐":"兆豐",
    "國泰":"國泰","統一":"統一","統一投顧":"統一","台新":"台新","日盛":"日盛",
}

_FW = {ord('（'):'(',ord('）'):')',ord('，'):',',ord('、'):',',ord('：'):':',
       ord('；'):';',ord('・'):' ',ord('·'):' ',ord('～'):'~',ord('　'):' ',
       ord('【'):'(',ord('】'):')',ord('〔'):'(',ord('〕'):')'}

def _norm(s):
    s = unicodedata.normalize("NFKC", s)
    return s.translate(_FW)

def _split_tokens(stem):
    # split at any punctuation/space, then split letter<->digit<->han boundaries
    parts = re.split(r"[ \-_()\[\],;:~.+]+", stem)
    out = []
    for p in parts:
        if not p: continue
        # break at script boundaries: digits | ascii letters | CJK
        out += re.findall(r"[0-9]+|[A-Za-z]+|[\u4e00-\u9fff]+|[^0-9A-Za-z\u4e00-\u9fff]+", p)
    return [t for t in (x.strip() for x in out) if t]

def _try_date(tok):
    if not tok.isdigit(): return None
    n = len(tok)
    try:
        if n == 8:   # YYYYMMDD
            y,m,d = int(tok[:4]),int(tok[4:6]),int(tok[6:8])
        elif n == 7: # ROC YYYMMDD  (114 -> 2025)
            y,m,d = int(tok[:3])+1911,int(tok[3:5]),int(tok[5:7])
        elif n == 6: # YYMMDD -> 20YY
            y,m,d = 2000+int(tok[:2]),int(tok[2:4]),int(tok[4:6])
        else: return None
        if 2018 <= y <= 2031 and 1 <= m <= 12 and 1 <= d <= 31:
            return datetime.date(y,m,d).isoformat(), {8:"G8",7:"ROC7",6:"G6"}[n]
    except ValueError:
        return None
    return None

def _is_ticker(tok):
    return bool(_TICKER_FULL.match(tok)) and not (2021 <= int(tok) <= 2030)

def parse_filename(fn):
    stem = re.sub(r"\.(pdf|docx|xlsx|txt)$","",fn,flags=re.I)
    toks = _split_tokens(_norm(stem))
    date_iso=date_kind=None; date_tok=None
    for t in toks:
        r=_try_date(t)
        if r: date_iso,date_kind=r; date_tok=t; break
    ticker=None
    for t in toks:
        if t==date_tok: continue
        if t.isdigit() and _is_ticker(t):
            ticker=t; break
    broker=None
    for t in toks:
        if t in BROKERS: broker=BROKERS[t]; break
    # name: prefer the Chinese token nearest the ticker (company sits beside its code);
    # blank for ticker-less thematic/strategy reports (no single company)
    NAME_SKIP = ("投顧","投資","報告","個股","訪談","速報","晨會","晨間","解盤","期貨",
                 "日股","美股","港股","分析","早報","評論","摘要","趨勢","展望","海外",
                 "商品","研究","證期","盤勢","產業","半導體","概念","預算","場")
    def _name_ok(t):
        return (re.fullmatch(r"[\u4e00-\u9fff]{2,5}",t) and t not in BROKERS
                and not any(k in t for k in NAME_SKIP))
    name=""
    if ticker:
        try: ti=toks.index(ticker)
        except ValueError: ti=None
        if ti is not None:
            best=None;bd=99
            for j,t in enumerate(toks):
                if _name_ok(t) and abs(j-ti)<bd:
                    best=t;bd=abs(j-ti)
            name=best or ""
        if not name:
            for t in toks:
                if _name_ok(t): name=t; break
    return {"filename":fn,"ticker":ticker or "","date":date_iso or "",
            "date_kind":date_kind or "","broker":broker or "","name":name or "",
            "tokens":toks}

# ---- BASIC vs DILUTED EPS classifier (D8B financial validator helper) ----
def classify_eps(text):
    t=text.lower()
    if re.search(r"稀釋(後)?(每股)?(盈餘|eps)|diluted\s*eps|fully[- ]diluted",t): return "eps_diluted"
    if re.search(r"基本(每股)?(盈餘|eps)|basic\s*eps",t): return "eps_basic"
    if re.search(r"每股盈餘|\beps\b",t): return "eps"     # unqualified
    return None


# ---- EPS invariant: BASIC EPS >= DILUTED EPS  (Tony 2026-05-31) ----
# Dilution raises share count -> lowers per-share earnings, so basic >= diluted
# always holds for profits. For losses, standards exclude anti-dilutive shares,
# so diluted == basic; a material gap is flagged.
def _to_eps_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"-?\d+(?:\.\d+)?", str(v).replace(",", ""))
    return float(m.group(0)) if m else None

def validate_eps_pair(basic, diluted, tol=0.01):
    """Return (status, note). status in {PASS, WARN, FLAG, NA}."""
    b = _to_eps_float(basic)
    d = _to_eps_float(diluted)
    if b is None or d is None:
        return ("NA", "one side missing; cannot cross-check")
    if b + tol >= d:
        if b < 0 and d < 0 and abs(b - d) > tol:
            return ("WARN", "loss period: diluted should equal basic (gap=%.4g)" % abs(b - d))
        return ("PASS", "basic>=diluted ok")
    return ("FLAG", "diluted(%.4g) > basic(%.4g): invariant violated / labels may be swapped" % (d, b))
