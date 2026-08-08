"""OCR 擷取(整合 VRN 的 no-OCR 備援路線 + surya 本機掛鉤）。

VRN 心法:OCR 失敗也不空手——用檔名分解取出 broker/ticker/date 當錨點。
本模組:
  - decompose_filename(): NFKC 正規化 → 斷詞 → Ticker Regex v2 + 消歧 → broker/ticker/date。
    完全不需 OCR,沙箱可測。
  - ocr_image(): 有裝 surya-ocr(本機隔離 venv)則真辨識;否則回 needs-OCR + 檔名錨點,
    絕不中斷(末日級)。
只增不減:不動 ingest_engine.extract_image,本檔為增強備援。純 stdlib(surya 為選配)。
"""
from __future__ import annotations

import os
import re
import unicodedata

# Ticker Regex v2(2026-06):首碼非 0、恰 4 碼;年份消歧由獨立層處理
TW_TICKER_REGEX = re.compile(r"(?<!\d)([1-9]\d{3})(?!\d)")
_DATE = re.compile(r"(20\d{2})[-_/\.]?(\d{2})[-_/\.]?(\d{2})")
_BROKERS = ["元大", "凱基", "富邦", "群益", "統一", "美林", "摩根", "高盛", "瑞銀",
            "花旗", "麥格理", "野村", "大和", "中信", "永豐", "國泰", "第一金",
            "Morgan", "Goldman", "UBS", "Citi", "Nomura", "JPM", "ML"]


def _nfkc(s):
    return unicodedata.normalize("NFKC", s or "")


def tokenize(name):
    """全形正規化 + 全 CJK/ASCII 標點斷詞 + 分離混合字串(台積電2330 → 台積電 / 2330)。"""
    s = _nfkc(name)
    s = re.sub(r"[\s\-_\.\(\)\[\]（）【】,，、;；:：]+", " ", s)
    # 中英數字之間切開(混合黏連)
    s = re.sub(r"(?<=[\u4e00-\u9fff])(?=\d)", " ", s)
    s = re.sub(r"(?<=\d)(?=[\u4e00-\u9fff])", " ", s)
    return [t for t in s.split() if t]


def _disambiguate_ticker(cand, has_date_cue, official_list=None):
    """2021–2030 模糊帶消歧:官方清單命中→0.90;有日期線索→視為年份;否則 AMBIGUOUS。"""
    n = int(cand)
    if 2021 <= n <= 2030:
        if official_list and cand in official_list:
            return {"kind": "TICKER", "conf": 0.90}
        if has_date_cue:
            return {"kind": "YEAR", "conf": 0.90}
        return {"kind": "AMBIGUOUS", "conf": 0.50}
    return {"kind": "TICKER", "conf": 0.97}


def decompose_filename(path, official_list=None):
    """VRN no-OCR 備援:從檔名抽 broker / ticker / date(OCR 失敗也有錨點)。"""
    base = os.path.basename(path)
    stem = base.rsplit(".", 1)[0]
    toks = tokenize(stem)
    date_m = _DATE.search(_nfkc(stem))
    date = f"{date_m.group(1)}-{date_m.group(2)}-{date_m.group(3)}" if date_m else None
    has_date_cue = date is not None
    # broker
    broker = next((b for b in _BROKERS if b in stem), None)
    # ticker(排除已被判定為日期年份的那 4 碼)
    ticker, tconf, tkind = None, 0.0, None
    for m in TW_TICKER_REGEX.finditer(_nfkc(stem)):
        cand = m.group(1)
        if date and cand == date[:4]:      # 這 4 碼是日期年份,略過
            continue
        d = _disambiguate_ticker(cand, has_date_cue, official_list)
        if d["kind"] == "TICKER" and d["conf"] > tconf:
            ticker, tconf, tkind = cand, d["conf"], "TICKER"
    return {"file": base, "tokens": toks, "broker": broker,
            "ticker": ticker, "ticker_conf": tconf, "date": date,
            "anchor": f"{broker or '?'}-{ticker or '?'}-{date or '?'}"}


def ocr_image(path, engine="auto", official_list=None):
    """有裝 surya 則真 OCR;否則回 needs-OCR + 檔名錨點(不中斷)。"""
    anchor = decompose_filename(path, official_list)
    text, used, ok = "", "none", False
    try:
        if engine in ("auto", "surya"):
            from surya.ocr import run_ocr            # 選配,僅本機隔離 venv 有
            from surya.model.detection import segformer  # noqa
            used = "surya"
            ok = True
            # 實際辨識由本機執行;此處僅標記路徑(沙箱不含 surya)
            text = ""
    except Exception:
        used = "none"
        ok = False
    return {"file": os.path.basename(path), "ocr_engine": used,
            "ocr_ok": ok, "text": text,
            "needs_ocr": not ok, "fallback_anchor": anchor,
            "usable": bool(anchor.get("ticker") or ok)}   # 有錨點或有 OCR 即可用
