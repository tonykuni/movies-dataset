# -*- coding: utf-8 -*-
"""WorkOps 共用詞彙模組 v0100 — SSOT/REGEX/同義字/LIST 彙整去重(操作員 2026/08/09 令)。

正本原則:凡跨引擎共用之 regex/正規化函數/清單載入器,一律以本模組為唯一定義;
消費者(workops_wop_identifier / workops_namer / …)import 之,不得各自複本。
跨語言複本(指揮板 JS 之 CODE_RE、板 PS 之 SheetAlias)無法共享 runtime —
以 VIA_SSOT/VIA_Shared_Lexicon_Registry 目錄冊登記正本歸屬防漂移。
資料詞庫(org_lexicon.json / bulk_senders.txt / domain_dict.txt / product_code_map.json)
維持各自檔案,本模組提供統一載入器。只增不減;行為與原分散定義完全一致。
"""
import io, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent          # engines/

# ---- 共用 REGEX 正本(原 identifier/namer/board 各自定義 → 收斂於此)----
CODE_RE   = re.compile(r"\b[A-Z]{2,6}[-_ ]?\d{2,6}\b")
PREFIX_RE = re.compile(r"^\s*((re|fw|fwd|回覆|轉寄|答復)\s*[::]\s*)+", re.IGNORECASE)
TAG_RE    = re.compile(r"\[(?:THR|WOP)-\d+\]")
WOPID_RE  = re.compile(r"WOP-\d{4}")
URL_RE    = re.compile(r"https?://([A-Za-z0-9.\-]+)")


def norm_subj(s):
    """正規化主旨:剝 Re/Fw/回覆/轉寄 + [THR-#][WOP-#] 標籤,壓空白,lower,80 字。"""
    s = PREFIX_RE.sub("", (s or "").strip())
    s = TAG_RE.sub("", s)
    return re.sub(r"\s+", "", s).lower()[:80]


def clean_subject(s):
    """展示用清理主旨(命名提議同式):剝前綴,單一空白,40 字。"""
    s = PREFIX_RE.sub("", (s or "").strip())
    s = re.sub(r"\s+", " ", s)
    return s[:40]


def subj_code(s):
    """主旨/文字中之案號代號(ABC-123 型);無則空字串。"""
    m = CODE_RE.search((s or "").upper())
    return m.group(0).replace("_", "-").replace(" ", "-") if m else ""


def load_bulk_patterns(path=None):
    """bulk_senders.txt 樣式清單(# 註解;lower)。"""
    p = Path(path) if path else HERE / "bulk_senders.txt"
    pats = []
    if p.exists():
        for ln in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            ln = ln.strip().lower()
            if ln and not ln.startswith("#"):
                pats.append(ln)
    return pats


def is_bulk(sender, pats):
    s = (sender or "").lower()
    return any(p in s for p in pats)


def load_org_lexicon(path=None):
    """org_lexicon.json:機構/公司名(SSOT 附件萃取)。回 (names_desc_len, meta)。"""
    p = Path(path) if path else HERE / "org_lexicon.json"
    if not p.exists():
        return [], {}
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return [], {}
    names = set()
    for c in d.get("companies", []):
        nm = (c.get("name") or "").strip()
        if len(nm) >= 2:
            names.add(nm)
    for nm in d.get("orgs", []):
        nm = (nm or "").strip()
        if len(nm) >= 2:
            names.add(nm)
    return sorted(names, key=len, reverse=True), d


def extract_url_domains(text):
    """內文中 URL 網域(lower;去 www.)。"""
    out = []
    for d in URL_RE.findall(text or ""):
        d = d.lower().lstrip(".")
        if d.startswith("www."):
            d = d[4:]
        if "." in d:
            out.append(d)
    return out
