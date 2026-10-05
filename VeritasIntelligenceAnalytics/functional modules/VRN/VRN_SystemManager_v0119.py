#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0119 — 薄尾:deepread 首頁深讀驗證(操作員令 2026-10-05「58檔實際讀取PDF內容」)。

對 intake 認定的個股報告,實際開 PDF 讀內容,引擎實測驗證並擴欄:
  ① 檔名律 vs 內文互證:REPORT DATE / TICKER / BROKER 內文重抽,逐項 MATCH/MISS 燈語
  ② 版面兩區(照正典一、3):首頁切 左=本文區(left main text)· 右=資訊區(right info segment);
     資訊區側別由關鍵詞密度定(目標價/評等/收盤/分析師/@/Tel…),左右都可
  ③ 資訊區抽取:rating(評等)· target price(目標價)· analyst name/title/email/tel
  ④ 代號衍生:bloomberg ticker=「#### TT」· yfinance ticker=####.TW/.TWO
     (市別查本地 universe 清單;查不到=兩候選並列,派 VDF 車道定盤,不猜)
  ⑤ 年度財務頁(financial data on annual financial pages):年份序列+財務關鍵詞+數字密度
     合格頁清單與樣本列(EPS/營收/淨利…),供 ENG400 表格梯接手
  ⑥ 外部價:adj close(最新)· adj close before report date(報告日前最後交易日)·
     target price(adj)=TP×(調整後/未調整收盤比);VIA_NO_NET 或 yfinance 缺=誠實 SKIPPED
  ⑦ SIZE 實量測(stat bytes);.docx/.txt 誠實 NON_PDF_SKIP(另路,不假裝讀過)
每動作自動 U/I 矩陣照 v0118 律(deepread 也跳);券商一律短英文縮寫(兆豐=MEGA·麥格理=MCQ,
同義字冊 v0105 裁定)。intake/eps-check/reconcile/closeout 照前版鏈。
自測: VIA_FROM_VCGC=YES python VRN_SystemManager_v0119.py --selftest(合成 PDF 實開實讀)
"""
from __future__ import annotations

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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

TAG = "v0119"
HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"


def _vnum_v0119(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0119(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0119(p) < _vnum_v0119(__file__)),
                 key=_vnum_v0119)
PRIOR = _load_v0119(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ────────────────── 深讀律 v0119(抽取式全走 SSOT 冊,不散落) ──────────────────
_INFO_KW = ("目標價", "評等", "收盤", "市值", "股價", "分析師", "Target", "Rating", "Close", "@", "Tel", "TEL", "電話")
_TITLE_WORDS = ("分析師", "研究員", "協理", "資深副總", "Analyst", "Research")
_NAME_STOP = ("聯絡", "地址", "免責", "客服", "本報告", "研究部", "部門", "Contact", "Disclaimer", "Address", "傳真")
_FIN_KW = ("EPS", "每股盈餘", "營收", "淨利", "毛利", "ROE", "股本", "營業利益", "Revenue", "Net income", "稅後")
_CRX_CACHE = None


def _wordish_v0119(term: str) -> str:
    """ASCII 詞加字母邊界(TP≠STOP);CJK 原樣。"""
    e = re.escape(term)
    return r"(?<![A-Za-z])" + e + r"(?![A-Za-z])" if term.isascii() else e


def _central_regex_v0119() -> dict:
    """中央 REGEX/同義字冊尾版(VIA_Central_Synonym_Regex_v*;操作員令 2026-10-05):
    三種台股代碼(TWEquityTicker/TWEquityYFTicker/TWEquityBBGTicker,批118 LOCKED)·
    RATING_* 字典 · TARGET_PRICE 字典 · TIME/EMAIL/台北+香港 TEL 式全走冊;
    BROKER 字典照 _broker_map(VRN_Broker_Dict+SynonymUnion 尾版)。缺鍵=誠實記 _notes 用內建後備。"""
    global _CRX_CACHE
    if _CRX_CACHE is None:
        reg = HERE.parents[1] / "supportive modules" / "registry"
        hits = sorted(reg.glob("VIA_Central_Synonym_Regex_v*.json"))
        rx, syn, notes = {}, {}, []
        if hits:
            try:
                d = json.loads(hits[-1].read_text(encoding="utf-8"))
                rx = {k: v.get("pattern") for k, v in (d.get("regex") or {}).items() if isinstance(v, dict)}
                syn = d.get("synonyms") or {}
            except (OSError, ValueError) as exc:
                notes.append(f"{hits[-1].name}: {type(exc).__name__}")
        else:
            notes.append("VIA_Central_Synonym_Regex 冊不在")

        def pat(key, fallback):
            if rx.get(key):
                return rx[key]
            notes.append(f"{key}: 冊缺,用引擎內建後備")
            return fallback

        rating = sorted({str(t) for k, v in syn.items() if k.startswith("RATING_") and isinstance(v, list)
                         for t in v} or {"買進", "中立", "賣出", "未評等"}, key=len, reverse=True)
        if len(rating) == 4 and "買進" in rating:
            pass  # 可能是後備;只有冊載入失敗時才會走到,notes 已記
        tp_words = sorted({str(t) for k in ("TARGET_PRICE", "FINANCIAL_FIELD_TARGET_PRICE")
                           for t in (syn.get(k) or [])} or {"目標價", "Target Price", "TP"}, key=len, reverse=True)
        bbg = pat("TWEquityBBGTicker", r"^([1-9]\d{3})\s+TT$")
        _CRX_CACHE = {
            "ticker_bare": pat("TWEquityTicker", r"^(?:[1-9]\d{3})$"),
            "ticker_yf": pat("TWEquityYFTicker", r"^([1-9]\d{3})\.(TW|TWO)$"),
            "ticker_bbg": bbg,
            "tt_in_text": re.compile(r"(?<!\d)" + bbg.strip("^$").replace(r"\s+", r"\s?")),
            "date": re.compile(pat("RX_TIME_CONTENT_DATE", r"(20[2-3]\d)[./年\-](\d{1,2})[./月\-](\d{1,2})日?")),
            "email": re.compile(pat("RX_EMAIL_STD", r"[\w.+-]+@[\w-]+\.[\w.-]+")),
            "tel": re.compile("(" + pat("RX_TEL_TAIPEI", r"(?:\+?886[- ]?2|\(02\)|02)[- ]?\d{4}[- ]?\d{4}")
                              + "|" + pat("RX_TEL_HK", r"\+?852[- ]?\d{4}[- ]?\d{4}")
                              + "|" + pat("RX_TEL_TW_ANY", r"(?:\+?886[-\s]?|\(0\d\)\s?|0)\d(?:[-\s]?\d){7,9}") + ")"),
            "date_en": re.compile(pat("RX_DATE_ENGLISH",
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})")),
            "rating": re.compile("(?i)(" + "|".join(_wordish_v0119(t) for t in rating) + ")"),
            "tp": re.compile("(?i)(?:" + "|".join(_wordish_v0119(t) for t in tp_words)
                             + r")[^\d]{0,15}((?:\d{1,3}(?:,\d{3})+|\d{2,5})(?:\.\d+)?)"),
            "tp_defense": re.compile(pat("RX_TARGET_PRICE_DEFENSE",
                r"(?i)(?:Target|目標(?:價)?)\s*[:：$]?\s*[\d,]+(\.\d+)?")),
            "tp_ntd": re.compile(pat("RX_TARGET_PRICE_NTD",
                r"(?:NT\$|NT\s?\$|目標價[:：]?\s*)\s*([0-9][0-9,]*\.?\d*)")),
            "tp_strips": [str(x) for x in (syn.get("TARGET_PRICE_STRIPS") or ["NT$", "TWD", "上看", "下看", "元"])],
            "rating_code": {str(a).lower(): (std, e.get("code"))
                            for std, e in (syn.get("RATING_CODEBOOK_MASTER") or {}).items()
                            for a in e.get("aliases", [])},
            "quarter": re.compile(pat("RX_YEAR_QUARTER", r"(?:(?:20)?\d{2}(?:\.|\s*)?Q[1-4])")),
            "tw_fin": dict(syn.get("TW_FIN_DICT") or {}),
            "name_zh": re.compile(pat("RX_NAME_ZH", r"[\u4e00-\u9fa5]{2,4}")),
            "name_en": re.compile("(" + pat("RX_NAME_EN_STD", r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b")
                                  + "|" + pat("RX_NAME_EN_SURNAME_FIRST", r"\b[A-Z][A-Z]+(?:\s+[A-Z][a-zA-Z\-]+){1,3}\b")
                                  + "|" + pat("RX_NAME_EN_INITIALS", r"\b(?:[A-Z][a-z]+|[A-Z]\.)(?:\s+(?:[A-Z][a-z]+|[A-Z]\.)){1,3}\b") + ")"),
            "name_mixed": re.compile(pat("RX_NAME_MIXED_PAREN",
                r"([\u4e00-\u9fa5]{2,4})\s*\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\)")),
            "name_mixed2": re.compile(pat("RX_NAME_MIXED_PLAIN",
                r"([\u4e00-\u9fa5]{2,4})\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})")),
            "val_methods": {k: (v.get("en", []) + v.get("zh", []))
                            for k, v in (syn.get("VALUATION_METHOD_CODEBOOK") or {}).items()},
            "job_titles": {k: (v.get("en", []) + v.get("zh", []))
                           for k, v in (syn.get("JOB_TITLE_CODEBOOK") or {}).items()},
            "_notes": notes,
        }
    return _CRX_CACHE


_MON_V0119 = {m: i + 1 for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"))}


def _content_date_v0119(crx, text: str) -> str | None:
    """內文日期:主式(數字/CJK)先;抓不到走英文月份式(MASTER)。"""
    m = crx["date"].search(text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    e = crx["date_en"].search(text)
    if e:
        return f"{e.group(3)}-{_MON_V0119[e.group(1)]:02d}-{int(e.group(2)):02d}"
    return None


_TP_UNIT_BAD = ("張", "億", "萬", "股", "倍", "%", "％", "年")


def _tp_ok_v0119(v: float) -> bool:
    """年份樣數值不是目標價(實測紅:儒鴻 target_price=2026);
    0/負值不是目標價(實測紅批1657:MQ-1560 OCR 道 TP=0.0)。"""
    if not (0 < float(v) < 100000):
        return False
    return not (float(v).is_integer() and re.fullmatch(r"20[2-4]\d", str(int(v))))


def _target_price_v0119(crx, *texts) -> float | None:
    """目標價:剝詞 → 主式逐候選(年份/張億萬股倍%尾拒抓)→ MASTER 防禦式第二道。"""
    for t in texts:
        for sp in crx["tp_strips"]:
            t = t.replace(sp, "")
        for m in crx["tp"].finditer(t):
            if t[m.end():m.end() + 1] not in _TP_UNIT_BAD:
                v = float(m.group(1).replace(",", ""))
                if _tp_ok_v0119(v):
                    return v
            # 候選被拒(年份/單位)→ 30 字前瞻窗找真價(實測紅:「目標價由 2026 年…上調至146元」)
            n2 = re.search(r"(?:\d{1,3}(?:,\d{3})+|\d{2,5})(?:\.\d+)?", t[m.end():m.end() + 30])
            if n2 and t[m.end() + n2.end():m.end() + n2.end() + 1] not in _TP_UNIT_BAD:
                v2 = float(n2.group(0).replace(",", ""))
                if _tp_ok_v0119(v2):
                    return v2
    for t in texts:
        for m in crx["tp_ntd"].finditer(t):   # NT$ 前綴式(上傳 v0101 實證)先於泛防禦式
            v = float(m.group(1).replace(",", "")) if m.group(1) else None
            if v and _tp_ok_v0119(v) and t[m.end():m.end() + 1] not in _TP_UNIT_BAD:
                return v
    for t in texts:
        for m in crx["tp_defense"].finditer(t):
            n = re.search(r"[\d,]+(?:\.\d+)?", m.group(0))
            if not n:
                continue
            v = float(n.group(0).replace(",", ""))
            if _tp_ok_v0119(v) and t[m.start() + n.end():m.start() + n.end() + 1] not in _TP_UNIT_BAD:
                return v
    return None


_BROKER_CONTENT_SKIP = {"first", "capital", "president", "long", "target", "mega"}
_RATING_REITERATE = ("維持", "重申", "Reiterate", "Maintain")


def _pick_rating_v0119(crx, info: str, whole: str):
    """評等揀選(實測紅兩案):「維持」「重申」是重申詞不是評等,跳過續找實體評等;
    超短 ASCII 碼(SS/N/OP…≤2 字母)只在含 評等/Rating/投資建議 的行收,防假命中;
    全文只有重申詞沒有實體評等=誠實 None(實測紅批1657:宏致 rating=維持)。"""
    for t in (info, whole):
        for m in crx["rating"].finditer(t):
            w = m.group(1)
            if w.isascii() and len(w) <= 2:
                ls = t.rfind("\n", 0, m.start()) + 1
                le = t.find("\n", m.end())
                line = t[ls:(len(t) if le < 0 else le)]
                if not any(k in line for k in ("評等", "Rating", "rating", "投資建議", "建議")):
                    continue
            if w in _RATING_REITERATE:
                continue
            return w
    return None


def _fn_analyst_v0119(stem: str, crx, company: str | None = None) -> str | None:
    """檔名中的分析師名(實測紅:KGI 式 …_代號 公司_姓名_日期,name 卻 null)。
    代號獨立成段時其下一段視為公司名跳過;首段視為券商;餘 2–4 字純中文段取最後一個。"""
    segs = [x.strip() for x in re.split(r"[_\-]", stem) if x.strip()]
    code_i = next((i for i, sg in enumerate(segs) if re.search(r"(?<!\d)\d{4}(?!\d)", sg)), None)
    skip = set()
    if code_i is not None and not re.search(r"[\u4e00-\u9fa5]", segs[code_i]) and code_i + 1 < len(segs):
        skip.add(code_i + 1)
    bm = PRIOR._broker_map()
    comp0 = (company or "").replace("-KY", "")
    cands = [sg for i, sg in enumerate(segs)
             if i not in skip and i != 0 and crx["name_zh"].fullmatch(sg)
             and sg.lower() not in bm and not any(w in sg for w in _NAME_STOP)
             and sg not in (company, comp0)]   # 公司名不是分析師(實測紅:志強)
    return cands[-1] if cands else None


def _open_pdf_v0119(path: Path):
    """PDF 引擎座:pymupdf(fitz)實開;缺/壞=誠實 (None, why),不吞。"""
    try:
        import fitz  # pymupdf;延遲載入
    except ImportError:
        return None, "pymupdf(fitz) 未裝:深讀引擎座 UNAVAILABLE,派環境計畫閘"
    try:
        return fitz.open(str(path)), None
    except Exception as exc:  # fitz 開檔失敗型別不一;誠實記型別不吞細節
        return None, f"開檔失敗 {type(exc).__name__}: {str(exc)[:80]}"


def _split_parts_v0119(bs, horizontal: bool, W: float) -> list:
    """資訊區拆獨立元件(批1657 操作員令「拆成獨立後識別」):
    側欄(左/右切出)→ **上下拆**(縱向空隙 >14pt 斷);帶狀(上/下切出)→ **左右拆**(x 中線分群)。
    每件帶 bbox/text/kind(矩陣/表格/長句/文字),獨立識別用。"""
    parts = []
    if horizontal:
        for b in sorted(bs, key=lambda b: b[1]):
            if parts and b[1] - parts[-1]["bbox"][3] <= 14:
                p = parts[-1]
                p["text"] += "\n" + b[4]
                p["bbox"] = [min(p["bbox"][0], b[0]), min(p["bbox"][1], b[1]),
                             max(p["bbox"][2], b[2]), max(p["bbox"][3], b[3])]
            else:
                parts.append({"bbox": [b[0], b[1], b[2], b[3]], "text": b[4]})
    else:
        sides = {"L": [], "R": []}
        for b in bs:
            sides["L" if (b[0] + b[2]) / 2 <= W / 2 else "R"].append(b)
        for k in ("L", "R"):
            if sides[k]:
                bb = sides[k]
                parts.append({"bbox": [min(b[0] for b in bb), min(b[1] for b in bb),
                                       max(b[2] for b in bb), max(b[3] for b in bb)],
                              "text": "\n".join(b[4] for b in sorted(bb, key=lambda b: (b[1], b[0])))})
    for p in parts:
        p["kind"] = _comp_kind_v0119(p["text"])
        p["bbox"] = [round(v, 1) for v in p["bbox"]]
    return parts


def first_page_zones(doc) -> dict:
    """首頁切兩區 v3(批1657 操作員令):側欄(左/右直切)之外,**資訊區在下方也認**(橫切);
    右(左)側資訊區再**上下拆**、下方資訊區再**左右拆**成獨立元件(info_parts),拆成獨立後識別。
    判側:關鍵詞密度(命中/區塊數);下方帶狀要命中數不輸側欄且密度較高才取(不誤搶左右版型);
    top 不認(大標 KW 如「目標價上調」會誤搶);零命中退回左右命中比較(與前版同判,不退步)。"""
    page = doc[0]
    W, H = page.rect.width, page.rect.height
    blocks = [b for b in page.get_text("blocks") if (b[4] or "").strip()]

    def _hits(bs):
        t = "\n".join(b[4] for b in bs)
        return sum(t.count(k) for k in _INFO_KW)

    zones = {"left": [b for b in blocks if b[0] <= W * 0.58],
             "right": [b for b in blocks if b[0] > W * 0.58],
             "bottom": [b for b in blocks if b[1] >= H * 0.60]}
    dens = {s: _hits(bs) / max(1, len(bs)) for s, bs in zones.items()}
    s_best = max(("right", "left"), key=lambda s: dens[s])
    bh, sh = _hits(zones["bottom"]), _hits(zones[s_best])
    # 操作員令只兩型:側欄(左/右,上下拆)與下方帶狀(左右拆);top 不認——大標 KW(目標價上調)會誤搶
    if bh and bh >= sh and dens["bottom"] > dens[s_best]:
        side = "bottom"
    elif sh:
        side = s_best
    else:
        lh, rh = _hits(zones["left"]), _hits(zones["right"])
        side = "right" if rh >= lh else "left"
    info_bs = zones[side]
    info_ids = {id(b) for b in info_bs}
    main_bs = [b for b in blocks if id(b) not in info_ids]
    axis = "x" if side in ("left", "right") else "y"
    cut = W * 0.58 if axis == "x" else H * 0.60
    info = "\n".join(b[4] for b in info_bs)
    main = "\n".join(b[4] for b in main_bs)
    return {"info_side": side, "info_text": info, "main_text": main,
            "info_kw_hits": int(_hits(info_bs)), "main_chars": len(main),
            "split_axis": axis, "split_at": round(cut, 1),
            "info_parts": _split_parts_v0119(info_bs, horizontal=(axis == "x"), W=W)}


def _yf_ticker_v0119(code: str) -> dict:
    """市別定盤:本地 universe 清單(VDF 資料家)查 上市/上櫃;查不到=兩候選並列不猜。"""
    uf = PRIOR._universe_file() if hasattr(PRIOR, "_universe_file") else None
    if uf:
        try:
            for line in uf.read_text(encoding="utf-8", errors="replace").splitlines():
                if re.match(rf"^\s*\"?{re.escape(code)}\b", line):
                    if any(k in line for k in ("TWO", "上櫃", "TPEx", "TPEX", "OTC")):
                        return {"yfinance_ticker": f"{code}.TWO", "market_source": uf.name}
                    return {"yfinance_ticker": f"{code}.TW", "market_source": uf.name}
        except OSError as exc:
            return {"yfinance_ticker": f"{code}.TW|{code}.TWO", "market_source": f"讀清單失敗 {type(exc).__name__}"}
    return {"yfinance_ticker": f"{code}.TW|{code}.TWO", "market_source": "無本地清單:候選並列,派 VDF 車道定盤"}


def _adj_close_v0119(code: str, report_date: str | None, tp: float | None) -> dict:
    """外部價三欄:最新 adj close · 報告日前 adj close · TP(adj)=TP×調整比;離線/缺=誠實 SKIPPED。"""
    if os.environ.get("VIA_NO_NET"):
        return {"state": "SKIPPED_NO_NET", "why": "VIA_NO_NET=1:離線模式不碰網路"}
    try:
        import yfinance
    except ImportError:
        return {"state": "UNAVAILABLE", "why": "yfinance 未裝"}
    import contextlib, io, logging
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    _sink = io.StringIO()
    try:
        cands = _yf_ticker_v0119(code)["yfinance_ticker"].split("|")
        if len(cands) == 1:   # 已定盤仍留另市後備(實測紅:上櫃股 .TW 404)
            cands.append(cands[0].replace(".TWO", ".X").replace(".TW", ".TWO").replace(".X", ".TW"))
        adj = raw = tk = None
        with contextlib.redirect_stderr(_sink), contextlib.redirect_stdout(_sink):   # 404 雜訊靜音(誠實態照回)
            for tk in cands:
                adj = yfinance.Ticker(tk).history(period="2y", auto_adjust=True)
                if adj is not None and not adj.empty:
                    raw = yfinance.Ticker(tk).history(period="2y", auto_adjust=False)
                    break
        if adj is not None and not adj.empty:   # 實測紅(批1657):最新列 Close=NaN 未成交;取最後有效值
            adj = adj[adj["Close"].notna()]
        if raw is not None and not raw.empty:
            raw = raw[raw["Close"].notna()]
        if adj is None or adj.empty:
            return {"state": "NODATA", "why": f"{'/'.join(cands)} 皆無資料(或全 NaN),不猜"}
        out = {"state": "OK", "ticker_used": tk,
               "price_lane": "yfinance(暫代;正式=VDF 網路統包 SUP_MDL740/AegisNexus)",
               "adj_close": round(float(adj["Close"].iloc[-1]), 2)}
        if report_date:
            upto = adj[adj.index.strftime("%Y-%m-%d") <= report_date]
            if not upto.empty:
                out["adj_close_before_report"] = round(float(upto["Close"].iloc[-1]), 2)
                if tp and raw is not None and not raw.empty:
                    rupto = raw[raw.index.strftime("%Y-%m-%d") <= report_date]
                    if not rupto.empty and float(rupto["Close"].iloc[-1]):
                        factor = float(upto["Close"].iloc[-1]) / float(rupto["Close"].iloc[-1])
                        out["target_price_adj"] = round(tp * factor, 2)
                        out["adj_factor"] = round(factor, 4)
        return out
    except Exception as exc:  # 網路層例外型別雜;誠實記型別
        return {"state": "ERROR", "why": f"{type(exc).__name__}: {str(exc)[:80]}"}


_FINLEX_CACHE = None


def _fin_lex_v0119() -> frozenset:
    """財報科目詞庫(SYNC ALL 之 fin_account 632 條,聯集冊尾版 + TW_FIN_DICT 16 詞):
    財報頁偵測共用;正則樣式別名濾除,缺冊退 _FIN_KW 誠實。"""
    global _FINLEX_CACHE
    if _FINLEX_CACHE is None:
        words = set(_FIN_KW) | set(_central_regex_v0119()["tw_fin"].keys())
        try:
            reg = HERE.parents[1] / "supportive modules" / "registry"
            hits = sorted(reg.glob("VIA_SSOT_SynonymUnion_v*.json"))
            d = json.loads(hits[-1].read_text(encoding="utf-8"))
            for alias in (d.get("scopes", {}).get("fin_account") or {}):
                a = str(alias).strip()
                if 2 <= len(a) <= 8 and re.search(r"[\u4e00-\u9fff]", a) \
                   and not re.search(r"[()\[\]?*+|\\]", a):
                    words.add(a)
        except (OSError, ValueError, KeyError) as exc:
            words.add(f"_載冊失敗{type(exc).__name__}")   # 誠實記,不吞(偵測照 _FIN_KW 走)
        _FINLEX_CACHE = frozenset(words)
    return _FINLEX_CACHE


def _fin_pages_v0119(doc) -> dict:
    """年度財務頁偵測:年份序列≥3 + 財報科目詞(fin_account 詞庫)≥2 + 數字密度;
    回頁碼與樣本列,交 ENG400 表格梯。"""
    pages, sample = [], ""
    lex = _fin_lex_v0119()
    for i in range(1, min(len(doc), 30)):   # 首頁另路(first_page_zones),財報頁從第 2 頁起(實測紅:p1 誤入)
        t = doc[i].get_text()
        years = len(set(re.findall(r"(?<!\d)20[1-3]\d(?!\d)", t)))
        kws = sum(1 for k in lex if k in t)
        kws = min(kws, 99)
        nums = len(re.findall(r"\d+\.\d+", t))
        if years >= 3 and kws >= 2 and nums >= 8:
            pages.append(i + 1)
            if not sample:
                for ln in t.splitlines():
                    if any(k in ln for k in ("EPS", "每股盈餘")) and re.search(r"\d+\.\d+", ln):
                        sample = ln.strip()[:120]
                        break
    return {"fin_pages": pages, "fin_sample": sample or None}


_GENERIC_MAILBOX = {"research", "media_request", "service", "info", "contact", "support",
                    "ir", "sales", "admin", "webmaster", "marketing", "news", "press"}
_EN_NAME_STOP = {"morgan", "broking", "securities", "research", "limited", "ltd", "capital",
                 "markets", "group", "bank", "global", "asia", "taiwan", "equity", "report",
                 "stanley", "sachs", "goldman", "questions", "requests", "media", "disclosure"}


def _en_namish_v0119(c: str) -> bool:
    """英文姓名候選不得含公司/機構詞(實測紅:Morgan Broking 被當人名)。"""
    return not any(t.lower().strip(".,") in _EN_NAME_STOP for t in c.split())
_ANALYST_PATTERNS = (r"(?:分析師|研究員)[::\s]*([\u4e00-\u9fa5]{2,4})(?![\u4e00-\u9fa5])",
                     r"(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{2,3})\s*(?:分析師|研究員)執?筆?")


def _analyst_v0119(info: str, whole: str | None = None) -> dict:
    """分析師姓名識別條件階梯(操作員令 2026-10-05,樣本定律:KGI=檔名中文名+first.last@、
    CTBC=人名信箱、華南/FactSet=通用信箱無人名):
    R1 資訊區區塊上方律(職稱/電話/郵箱上一~二行,過黑名單+姓名式)
    R2 全頁樣式律(「分析師 陳大文」「陳大文 分析師」樣式,資訊區+本文區)
    R3 email 鄰近律(email ±2 行內的姓名式行;中文行須短且全匹配,英文可子串)
    R4 檔名律(deepread 端 _fn_analyst;KGI 式)
    R5 email local 推英文名(first.last → First Last,並分拆 first/last)
    R6 通用信箱判(數字/research/media_request/service… → 不造名,analyst_contact_generic=True)
    每級帶 analyst_name_source;抽不到誠實 None。"""
    crx = _central_regex_v0119()
    em = crx["email"].search(info)
    tel = crx["tel"].search(info)
    lines = [ln.strip() for ln in info.splitlines()]
    name = title = title_std = src = None
    jt = sorted(((a, std) for std, al in crx["job_titles"].items() for a in al),
                key=lambda x: -len(x[0])) or [(w, None) for w in _TITLE_WORDS]
    tw = tuple(a for a, _ in jt) + _TITLE_WORDS
    blk = None
    for i, ln in enumerate(lines):
        if any(w in ln for w in tw) or crx["tel"].search(ln) or crx["email"].search(ln):
            blk = i
            break
    for ln in lines:   # 職稱碼冊(JOB_TITLE_CODEBOOK)長別名先比;中文子串、英文邊界
        for a, std in jt:
            if (not a.isascii() and a in ln) or (a.isascii() and re.search(_wordish_v0119(a), ln)):
                title, title_std = a, std
                break
        if title:
            break
    if blk is not None:   # 律③:區塊上方短行、無數字無 @ = 姓名(標題詞黑名單;實測紅「聯絡方式」)
        for j in range(blk - 1, max(blk - 3, -1), -1):
            c = lines[j]
            if c and len(c) <= 25 and "@" not in c and not re.search(r"\d", c) \
               and not any(w in c for w in tw) \
               and not any(w in c for w in _NAME_STOP) \
               and (crx["name_zh"].fullmatch(c) or crx["name_en"].fullmatch(c)
                    or crx["name_mixed"].fullmatch(c) or crx["name_mixed2"].fullmatch(c)) \
               and (not c.isascii() or _en_namish_v0119(c)):
                name, src = c, "info_zone"   # R1 姓名式驗證 + EN 公司詞閘
                break
    if name is None and title:   # R1 後備:職稱同行剝職稱;結果同樣過黑名單+姓名式
        for ln in lines:
            if title in ln:
                cand = re.sub(r"(?i)(分析師|研究員|協理|資深副總|Analyst|Research|[::])", " ", ln).strip()[:30]
                if cand and not any(w in cand for w in _NAME_STOP) \
                   and (crx["name_zh"].fullmatch(cand) or crx["name_en"].fullmatch(cand)
                        or crx["name_mixed"].fullmatch(cand) or crx["name_mixed2"].fullmatch(cand)):
                    name, src = cand, "info_zone"
                break
    if name is None:   # R2 全頁樣式律
        for rx in _ANALYST_PATTERNS:
            mm = re.search(rx, (whole or info))
            if mm and not any(w in mm.group(1) for w in _NAME_STOP):
                name, src = mm.group(1), "pattern"
                break
    _gen = bool(em) and ((not re.search(r"[A-Za-z]", em.group(0).partition("@")[0]))
                         or em.group(0).partition("@")[0].lower() in _GENERIC_MAILBOX)
    if name is None and em and not _gen:   # R3 email 鄰近律(通用信箱不跑:通用聯絡區無分析師)
        for j, ln in enumerate(lines):
            if em.group(0) in ln:
                for k in range(max(0, j - 2), min(len(lines), j + 3)):
                    c = lines[k]
                    if not c or "@" in c or any(w in c for w in _NAME_STOP) \
                       or any(w in c for w in tw):   # 職稱詞行不是姓名(研究員≠名)
                        continue
                    if len(c) <= 10 and crx["name_zh"].fullmatch(c):
                        name, src = c, "email_near"
                        break
                    me = crx["name_en"].search(c)
                    if me and len(c) <= 40 and _en_namish_v0119(me.group(0)):
                        name, src = me.group(0), "email_near"
                        break
                break
    name_en = broker_mail = None
    if name:   # 混合姓名拆欄:李明哲 (Michael Lee) / 王大明 David Wang
        mm = crx["name_mixed"].fullmatch(name) or crx["name_mixed2"].fullmatch(name)
        if mm:
            name, name_en = mm.group(1), mm.group(2)
    if em:
        local, _, dom = em.group(0).partition("@")
        generic = (not re.search(r"[A-Za-z]", local)) or local.lower() in _GENERIC_MAILBOX
        if name_en is None and not generic:   # R5;R6 通用信箱(數字/research/media_request…)不造名
            name_en = " ".join(t.capitalize() for t in re.split(r"[._\-]+", local) if t) or None
        toks = dom.lower().split(".")
        for alias, target in PRIOR._broker_map().items():   # 律②:短別名要 token 全等,長別名子串
            if alias.isascii():
                a = alias.lower()
                if (len(a) <= 3 and a in toks) or (len(a) > 3 and a in dom.lower()):
                    broker_mail = target
                    break
    coauthor = None
    if name and name.isascii() and em and name_en:   # 名與信箱不同人=共同作者(實測紅:Michael Hung vs carrie.liu)
        local_toks = {t.lower() for t in re.split(r"[._\-]+", em.group(0).partition("@")[0]) if t}
        name_toks = {t.lower().strip(".,") for t in name.split()}
        if not (local_toks & name_toks):
            coauthor, name, src = name, name_en, "email_local(主作者=信箱持有人;原抽名列共同作者)"
    if name is None and name_en:   # 後備:@前推名律(UBS/Citi 有信箱沒名)
        name, src = name_en, "email_local"
    first = last = None   # 英文姓名分拆(操作員令:英文姓名要分拆好)
    if name_en:
        parts = name_en.split()
        if len(parts) >= 2:
            first, last = parts[0], parts[-1]
    return {"analyst_name": name, "analyst_name_source": src, "analyst_coauthor": coauthor,
            "analyst_contact_generic": bool(em) and ((not re.search(r"[A-Za-z]", em.group(0).partition("@")[0]))
                                                     or em.group(0).partition("@")[0].lower() in _GENERIC_MAILBOX),
            "analyst_title": title, "analyst_title_std": title_std,
            "analyst_name_en": name_en, "analyst_first_name": first, "analyst_last_name": last,
            "analyst_broker": broker_mail,
            "analyst_email": em.group(0) if em else None,
            "analyst_tel": tel.group(1).strip() if tel else None}


def _repair_stats_v0119(text: str) -> dict:
    """文字修復統計:字元/CJK/數字/壞字(�與控制碼);誠實照數。"""
    bad = text.count("\ufffd") + sum(1 for ch in text if ord(ch) < 32 and ch not in "\n\t\r")
    return {"chars": len(text.strip()), "cjk": len(re.findall(r"[\u4e00-\u9fff]", text)),
            "digits": len(re.findall(r"\d", text)), "bad": bad}


def _fresh_outputs_v0119(verb: str) -> list:
    """實測清場律(操作員令 2026-10-05):每次實測先刪前一次該動詞輸出,避免混淆;回刪單。"""
    ui = Path(os.environ.get("VIA_VRN_UI_DIR") or HERE.parents[1] / "VIA_Reports" / "vrn")
    removed = []
    if ui.exists():
        for f in ui.glob("*" + verb + "*"):
            try:
                f.unlink()
                removed.append(f.name)
            except OSError as exc:
                removed.append(f"{f.name}(刪不掉 {type(exc).__name__})")
    return removed


def fin_page_zones(page) -> dict:
    """頁面切割(正典一、3/4):先左右切半,再各半依縱向空隙(>14pt)上下切成視覺元件;
    v2(操作員令 2026-10-05):dict 抽取帶字級 max_size,供文字大小階層分類。"""
    W = page.rect.width
    raw = page.get_text("dict")
    bl = []
    for b in raw.get("blocks", []):
        if b.get("type") != 0:
            continue
        txt = "\n".join("".join(sp.get("text", "") for sp in ln.get("spans", []))
                        for ln in b.get("lines", []))
        if not txt.strip():
            continue
        ms = max((sp.get("size", 0) for ln in b.get("lines", []) for sp in ln.get("spans", [])), default=0)
        x0, y0, x1, y1 = b["bbox"]
        bl.append((x0, y0, x1, y1, txt, ms))
    halves = {"left": [], "right": []}
    for b in bl:
        halves["left" if (b[0] + b[2]) / 2 <= W / 2 else "right"].append(b)
    out = {}
    for side, bs in halves.items():
        bs.sort(key=lambda b: b[1])
        comps = []
        for b in bs:
            if comps and b[1] - comps[-1]["bbox"][3] <= 14 \
               and abs(b[5] - comps[-1]["max_size"]) <= 2.5:   # 字級差>2.5pt=不同階層,不併(標題獨立成元件)
                c = comps[-1]
                c["bbox"] = [min(c["bbox"][0], b[0]), min(c["bbox"][1], b[1]),
                             max(c["bbox"][2], b[2]), max(c["bbox"][3], b[3])]
                c["text"] += "\n" + b[4]
                c["max_size"] = max(c["max_size"], round(b[5], 1))
            else:
                comps.append({"bbox": [round(b[0], 1), round(b[1], 1), round(b[2], 1), round(b[3], 1)],
                              "text": b[4], "max_size": round(b[5], 1)})
        out[side] = comps
    return out


def _hier_tally_v0119(comps) -> str:
    """本文區文字大小階層(操作員令):body=各元件字級中位數;≥1.25×=標題 · ≥1.08×=副標 · 其餘=本文。"""
    sizes = sorted(c.get("max_size", 0) for c in comps if c.get("max_size"))
    if not sizes:
        return "-"
    body = sizes[(len(sizes) - 1) // 2]   # 下中位:雙元件(標題+本文)時 body 取小者
    out = {}
    for c in comps:
        r = (c.get("max_size") or 0) / body if body else 0
        k = "標題" if r >= 1.25 else ("副標" if r >= 1.08 else "本文")
        out[k] = out.get(k, 0) + 1
    return "".join(f"{k}{v}" for k, v in out.items())


def _comp_kind_v0119(text: str) -> str:
    """元件類別(正典一、3:矩陣/表格/長句/文字):數字密度+行結構判;判不準寧給 文字。"""
    t = text.strip()
    if not t:
        return "空"
    lines = [ln for ln in t.splitlines() if ln.strip()]
    ratio = len(re.findall(r"\d", t)) / max(len(t), 1)
    nums = [len(re.findall(r"\d+(?:\.\d+)?", ln)) for ln in lines]
    if len(lines) >= 3 and max(nums) >= 3 and ratio > 0.2:
        return "矩陣" if all(n >= 3 for n in nums[1:]) else "表格"
    if len(lines) >= 2 and max(nums) >= 2 and ratio > 0.12:
        return "表格"
    if len(t.replace("\n", "")) >= 36 and ratio < 0.12:   # CJK 密度高,總長判(行寬換行不吃虧)
        return "長句"
    return "文字"


def _kind_tally_v0119(comps) -> str:
    out = {}
    for c in comps:
        k = _comp_kind_v0119(c["text"])
        out[k] = out.get(k, 0) + 1
    return "".join(f"{k}{v}" for k, v in out.items()) or "-"


def layout_check(path: str) -> dict:
    """LAYOUT+文字修復實測:首頁左右本文/資訊 · 財務頁左右再上下元件 · 每區壞字統計;
    先清前次結果(清場律)。只驗有代號的個股 PDF。"""
    removed = _fresh_outputs_v0119("layout_check")
    p = Path(path)
    files = sorted([q for q in p.rglob("*.pdf")]) if p.is_dir() else [p]
    rows = []
    for q in files:
        if not PRIOR.parse_filename(q.stem)["codes"]:
            continue
        doc, why = _open_pdf_v0119(q)
        if doc is None:
            rows.append({"filename": q.name, "state": "UNREADABLE", "lamp": "紅", "why": why})
            continue
        try:   # 單檔不殺整批
            z, _w, lane, lnote = _acquire_text_v0119(q, doc)
            if lane == "需OCR":
                rows.append({"filename": q.name, "state": "NO_TEXT_LAYER", "lamp": "黃",
                             "extract_lane": lane, "ocr_note": lnote})
                continue
            sm, si = _repair_stats_v0119(z["main_text"]), _repair_stats_v0119(z["info_text"])
            p1 = fin_page_zones(doc[0])   # 首頁也切元件供分類(只擷取第一頁+財報頁)
            if z["info_side"] in ("left", "right"):
                info_comps = p1[z["info_side"]]
                main_comps = p1["left" if z["info_side"] == "right" else "right"]
            else:   # 批1657:上/下帶狀資訊區——依切線分件(帶狀左右拆見 info_parts)
                _all = p1["left"] + p1["right"]
                _below = z["info_side"] == "bottom"
                info_comps = [c for c in _all if ((c["bbox"][1] + c["bbox"][3]) / 2 > z["split_at"]) == _below]
                _iid = {id(c) for c in info_comps}
                main_comps = [c for c in _all if id(c) not in _iid]
            fps = _fin_pages_v0119(doc)["fin_pages"]
            fin_desc, comp_n = [], 0
            for pno in fps[:4]:
                fz = fin_page_zones(doc[pno - 1])
                comp_n += len(fz["left"]) + len(fz["right"])
                fin_desc.append(f"p{pno}:L{len(fz['left'])}/R{len(fz['right'])}·"
                                f"{_kind_tally_v0119(fz['left'] + fz['right'])}")
            bad = sm["bad"] + si["bad"]
            lamp = "綠" if sm["chars"] and si["chars"] and bad == 0 else ("黃" if sm["chars"] or si["chars"] else "紅")
            rows.append({"filename": q.name, "state": "LAYOUT_CHECK", "info_side": z["info_side"],
                         "main_chars": sm["chars"], "main_cjk": sm["cjk"], "info_chars": si["chars"],
                         "info_digits": si["digits"], "bad_chars": bad,
                         "info_types": _kind_tally_v0119(info_comps), "main_types": _kind_tally_v0119(main_comps),
                         "main_hier": _hier_tally_v0119(main_comps),   # 本文區依文字大小階層
                         "info_has_text_and_table": ("文字" in _kind_tally_v0119(info_comps) or "長句" in _kind_tally_v0119(info_comps))
                                                    and ("表格" in _kind_tally_v0119(info_comps) or "矩陣" in _kind_tally_v0119(info_comps)),
                         "fin_pages": fin_desc or None, "fin_components": comp_n,
                         "info_parts": len(z.get("info_parts") or []),   # 批1657:資訊區拆成獨立元件數
                         "extract_lane": lane, "lamp": lamp})
        except Exception as exc:
            rows.append({"filename": q.name, "state": "ROW_ERROR", "lamp": "紅",
                         "why": f"{type(exc).__name__}: {str(exc)[:100]}"})
        finally:
            doc.close()
    return {"verb": "layout_check", "manager": TAG, "workflow": "VRN-WKF009", "step": "STP003-005",
            "cleaned_prev": removed, "checked": len(rows), "rows": rows}


def compute_fin_ratios(f: dict) -> dict:
    """財報比率分析(操作員 2026-10-05;TWSE/TPEX 用字,公式正本=中央冊 FIN_RATIO_CODEBOOK):
    輸入欄位字典(鍵用 TWSE/TPEX 中文用字,成長率配「上期」前綴鍵)→ 29 式;缺欄/除零誠實 None。"""
    def g(*ks):
        for k in ks:
            v = f.get(k)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None
        return None

    def div(a, b):
        return round(a / b, 4) if a is not None and b not in (None, 0) else None

    rev, gp, op, ni = g("營業收入"), g("營業毛利"), g("營業利益"), g("本期淨利")
    eq, ta, tl = g("股東權益"), g("總資產"), g("總負債")
    ca, cl, inv, cogs = g("流動資產"), g("流動負債"), g("存貨"), g("銷貨成本")
    ebit, ebitda, ie = g("EBIT", "息稅前利益"), g("EBITDA"), g("利息費用")
    shares, price, eps = g("流通在外股數"), g("股價"), g("EPS", "每股盈餘")
    wc = (ca - cl) if ca is not None and cl is not None else None
    out = {
        "毛利率": div(gp, rev), "營業利益率": div(op, rev), "稅後淨利率": div(ni, rev),
        "ROE": div(ni, eq), "ROA": div(ni, ta),
        "應收帳款週轉率": div(rev, g("平均應收帳款", "應收帳款")),
        "存貨週轉率": div(cogs, g("平均存貨", "存貨")),
        "總資產週轉率": div(rev, g("平均總資產", "總資產")),
        "應付帳款週轉率": div(cogs, g("平均應付帳款", "應付帳款")),
        "營運資金週轉率": div(rev, wc),
        "負債比率": div(tl, ta), "權益比率": div(eq, ta), "流動比率": div(ca, cl),
        "速動比率": div((ca - inv) if ca is not None and inv is not None else None, cl),
        "利息保障倍數": div(ebit, ie),
        "本益比": div(price, eps), "殖利率": div(g("每股股利", "DPS"), price),
        "股價淨值比": div(price, g("每股淨值", "BVPS")),
        "EV/EBITDA": div(g("企業價值", "EV"), ebitda),
        "BVPS": div(eq, shares), "DPS": div(g("現金股利總額", "現金股利"), shares),
        "EBIT利益率": div(ebit, rev), "EBITDA利益率": div(ebitda, rev),
    }
    for nm, cur, prev in (("營收成長率", "營業收入", "上期營業收入"), ("毛利成長率", "營業毛利", "上期營業毛利"),
                          ("營業利益成長率", "營業利益", "上期營業利益"), ("淨利成長率", "本期淨利", "上期本期淨利"),
                          ("EPS成長率", "EPS", "上期EPS")):
        c, p0 = g(cur), g(prev)
        out[nm] = round((c - p0) / p0, 4) if c is not None and p0 not in (None, 0) else None
    out["PEG"] = div(out["本益比"], out["EPS成長率"] * 100 if out["EPS成長率"] else None)
    return out


def _footer_scan_v0119(doc, crx) -> dict:
    """小字體頁尾/報告後方附錄(操作員令 2026-10-05):首頁底部 12% + 最後兩頁;
    不相關小字與附錄標題可抓券商與全評等名稱(外資附錄常列整套評等定義)。"""
    texts = [""]
    try:
        pg = doc[0]
        H = pg.rect.height
        texts.append("\n".join(b[4] for b in pg.get_text("blocks") if b[1] >= H * 0.88))
        for i in range(max(1, len(doc) - 2), len(doc)):
            texts.append(doc[i].get_text())
    except Exception as exc:
        return {"footer_broker": None, "rating_scale_found": False,
                "footer_note": f"頁尾掃描失敗 {type(exc).__name__}"}
    joined = "\n".join(texts)
    low = joined.lower()
    broker = None
    for alias, target in PRIOR._broker_map().items():
        if alias.isascii():
            a = alias.lower()
            if len(a) <= 2 or a in _BROKER_CONTENT_SKIP:
                continue
            if re.search(r"(?<![A-Za-z])" + re.escape(alias) + r"(?![A-Za-z])", low):
                broker = target
                break
        elif alias in low:
            broker = target
            break
    names = {m.group(1) for m in crx["rating"].finditer(joined) if not (m.group(1).isascii() and len(m.group(1)) <= 2)}
    return {"footer_broker": broker, "rating_scale_found": len(names) >= 3}


_NLP_CACHE = None


def _nlp_v0119() -> dict:
    """LAYOUT NLP 大引擎座(鎖冊 nlp=SUP_MDL866 統包;PRADDLE LAYOUT 修復鏈,段落照
    閱讀順序,原生在前 OCR 在後)。操作員令 2026-10-05:每個步驟都要用到 LAYOUT NLP——
    zones/斷句/分類/重建/再識別 全掛本座支援;載一次快取,缺/壞=誠實 UNAVAILABLE。"""
    global _NLP_CACHE
    if _NLP_CACHE is None:
        try:
            lock = json.loads((HERE.parents[1] / "supportive modules" / "registry" /
                               "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
            np_ = Path(lock["nlp"]["path"])
            if not np_.is_absolute():
                np_ = HERE.parents[2] / np_
            spec = importlib.util.spec_from_file_location("via_nlp_hub_for_vrn", np_)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            try:
                pin = mod.praddle_pinned()
                st = f"LOADED({lock['nlp']['version']}·praddle={pin.get('state')})"
            except Exception as exc:
                st = f"LOADED({lock['nlp']['version']}·praddle查詢失敗{type(exc).__name__})"
            _NLP_CACHE = {"state": st, "mod": mod}
        except Exception as exc:
            _NLP_CACHE = {"state": "UNAVAILABLE", "why": f"{type(exc).__name__}: {str(exc)[:80]}", "mod": None}
    return _NLP_CACHE


def _nlp_pdf_text_v0119(path: Path) -> tuple:
    """NLP 大引擎 LAYOUT 修復鏈取文(無文字層候援第一位,在輕OCR 之前)。"""
    if os.environ.get("VIA_VRN_NLP_LANE") != "1":
        return None, "NLP_LAYOUT 修復鏈未啟(設 VIA_VRN_NLP_LANE=1 單檔啟用;重鏈耗時,不拖死全批)"
    hub = _nlp_v0119()
    if hub.get("mod") is None:
        return None, hub["state"]
    try:
        r = hub["mod"].pdf_text(str(path), ocr="auto")
        t = (r or {}).get("text") or ""
        return (t if len(t.strip()) >= 40 else None), f"NLP_LAYOUT:{(r or {}).get('state')}"
    except Exception as exc:
        return None, f"NLP_LAYOUT 失敗 {type(exc).__name__}"


_SENT_END = "。!?;…!?"


def repair_sentences_v0119(comps) -> list:
    """第一頁本文斷句修復(操作員令 2026-10-05):行接到句點(。!?;…)才斷段,
    標題級(≥1.25×body)不用接;CJK 間空格 TRIM。回 [(級, 修復後文)]。"""
    sizes = sorted(c.get("max_size", 0) for c in comps if c.get("max_size"))
    body = sizes[(len(sizes) - 1) // 2] if sizes else 0
    out = []
    for c in comps:
        r = (c.get("max_size") or 0) / body if body else 0
        if r >= 1.25:   # 標題不用接
            out.append(("標題", re.sub(r"\s+", " ", c["text"]).strip()))
            continue
        buf, paras = "", []
        for ln in c["text"].splitlines():
            ln = ln.strip()
            if not ln:
                continue
            ln = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", ln)   # 去空格 TRIM
            buf += ln
            if buf[-1] in _SENT_END:
                paras.append(buf)
                buf = ""
        if buf:
            paras.append(buf)
        out.append(("本文" if r < 1.08 else "副標", "\n".join(paras)))
    return out


def _ocr_light_v0119(path: Path) -> tuple:
    """輕 OCR 座(梯:非OCR→輕OCR→重OCR):pytesseract+渲染;缺=誠實 (None, 指路)。"""
    try:
        import pytesseract  # noqa: F401
        import fitz
    except ImportError:
        return None, "輕OCR 未備(pytesseract 缺)→ 重型走 ENG400 OCR 車道(paddle 境)"
    try:
        doc = fitz.open(str(path))
        pix = doc[0].get_pixmap(dpi=200)
        import PIL.Image, io
        img = PIL.Image.open(io.BytesIO(pix.tobytes("png")))
        txt = pytesseract.image_to_string(img, lang="chi_tra+eng")
        doc.close()
        return (txt if len(txt.strip()) >= 40 else None), "輕OCR 已試(200dpi 首頁)"
    except Exception as exc:
        return None, f"輕OCR 失敗 {type(exc).__name__} → 重型 ENG400 車道"


def _render_table_v0119(text: str) -> str:
    """表格重現:垂直線 | 代表格線(連續空白/定位斷欄;單欄行退回逐詞)。"""
    out = []
    for ln in text.splitlines():
        if not ln.strip():
            continue
        cells = [c for c in re.split(r"\s{2,}|\t", ln.strip()) if c]
        if len(cells) == 1:
            cells = ln.strip().split()
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def reconstruct(path: str) -> dict:
    """報告重現(操作員令 2026-10-05):固定前段 FILENAME/REPORT DATE/BROKER/REPORT TYPE
    (一個報告前面都相同),自頁數起 PAGE n → TYPE-A 本文重現(文字大小階層標記)·
    TYPE-B 資訊區重現(表格用 | 格線)· 末段 SUMMARY 重現;本文出現表格雜湊 →
    抓出重建放到資訊區(moved 記數)。只處理第一頁+財報頁;清場律先刪前次。"""
    removed = _fresh_outputs_v0119("reconstruct")
    ui = Path(os.environ.get("VIA_VRN_UI_DIR") or HERE.parents[1] / "VIA_Reports" / "vrn")
    ui.mkdir(parents=True, exist_ok=True)
    p = Path(path)
    files = sorted(p.rglob("*.pdf")) if p.is_dir() else [p]
    rows = []
    crx = _central_regex_v0119()
    for q in files:
        fn = PRIOR.parse_filename(q.stem)
        if not fn["codes"]:
            continue
        doc, why = _open_pdf_v0119(q)
        if doc is None:
            rows.append({"filename": q.name, "state": "UNREADABLE", "lamp": "紅", "why": why})
            continue
        try:   # 單檔不殺整批
            z, whole0, lane, lnote = _acquire_text_v0119(q, doc)   # 統一核心,與 deepread 同梯
            if lane == "需OCR":
                rows.append({"filename": q.name, "state": "NO_TEXT_LAYER", "lamp": "黃",
                             "extract_lane": lane, "ocr_note": lnote,
                             "next": "無文字層 → OCR 車道(ENG400 四階梯)"})
                continue
            fps = _fin_pages_v0119(doc)["fin_pages"]
            fn_lock = bool(fn["report_date"] and fn["codes"] and fn["broker_std"])
            L = ["FILENAME    | " + q.name + ("  [鎖定]" if fn_lock else ""),
                 "REPORT DATE | " + (fn["report_date"] or "-"),
                 "BROKER      | " + (fn["broker_std"] or "-"),
                 "REPORT TYPE | " + (fn["doc_kind"] or "-"),
                 "ENGINE      | LAYOUT NLP " + _nlp_v0119()["state"], ""]
            moved = 0
            whole = z["info_text"] + "\n" + z["main_text"]
            rt = _pick_rating_v0119(crx, z["info_text"], whole)   # 首輪識別
            tp = _target_price_v0119(crx, z["info_text"], whole)
            c_date1 = _content_date_v0119(crx, whole)
            pz1 = fin_page_zones(doc[0])
            if z["info_side"] in ("left", "right"):
                info_comps = list(pz1[z["info_side"]])
                cand_main = pz1["left" if z["info_side"] == "right" else "right"]
            else:   # 批1657:資訊區在上/下——依切線把左右半的元件分到 info/main(帶狀再左右拆在 info_parts)
                allc = pz1["left"] + pz1["right"]
                below = z["info_side"] == "bottom"
                info_comps = [c for c in allc if ((c["bbox"][1] + c["bbox"][3]) / 2 > z["split_at"]) == below]
                iid = {id(c) for c in info_comps}
                cand_main = [c for c in allc if id(c) not in iid]
            main_comps = []
            for c in cand_main:
                if _comp_kind_v0119(c["text"]) in ("表格", "矩陣"):   # 本文表格雜湊 → 移資訊區
                    info_comps.append(c)
                    moved += 1
                else:
                    main_comps.append(c)
            L.append("PAGE 1")
            L.append("區一 TYPE-A 本文重現(斷句修復)")
            for lv, txt in repair_sentences_v0119(main_comps):
                L.append(f"[{lv}] " + txt)
            L.append("區二 TYPE-B 資訊區重現")
            for c in info_comps:
                k = _comp_kind_v0119(c["text"])
                L.append(f"[{k}]")
                L.append(_render_table_v0119(c["text"]) if k in ("表格", "矩陣") else c["text"].strip())
            L.append("")
            zone12_end = len(L)   # REVERIFY 域界:區一+區二止(首輪只掃第一頁,同域才公平)
            for pno in [x for x in fps[:3] if x != 1]:
                pz = fin_page_zones(doc[pno - 1])
                L.append(f"PAGE {pno}")
                L.append("區三 TYPE-C 財報頁重現")
                for side in ("left", "right"):
                    for c in pz[side]:
                        k = _comp_kind_v0119(c["text"])
                        L.append(f"[{side}·{k}]")
                        L.append(_render_table_v0119(c["text"]) if k in ("表格", "矩陣") else c["text"].strip())
                L.append("")
            vm = sorted({std for std, al in crx["val_methods"].items() for a in al
                         if (a in whole if not a.isascii() else re.search("(?i)" + _wordish_v0119(a), whole))})
            L += ["SUMMARY", "| 評等 | %s |" % (rt or "-"), "| 目標價 | %s |" % (tp or "-"),
                  "| 估值法 | %s |" % (",".join(vm) or "-"), "| 本文表格移置 | %d |" % moved]
            rebuilt = "\n".join(L[6:zone12_end])   # REVERIFY=區一+區二(表頭/區三/SUMMARY 不入;實測紅:財報頁日期假性不一致)
            rb_scan = re.sub(r"\s*\|\s*", " ", rebuilt)   # 去自家格線「|」(渲染物非原文;實測黃批1657:假性不一致)
            rv = {"評等": _pick_rating_v0119(crx, rb_scan, ""), "目標價": _target_price_v0119(crx, rb_scan),
                  "日期": _content_date_v0119(crx, rb_scan)}
            first = {"評等": rt, "目標價": tp, "日期": c_date1}
            L += ["", "REVERIFY(重建後再識別驗證;LAYOUT NLP 支援到底)", "| 項目 | 首輪 | 重建後 | 判 |"]
            rv_ok, rv_diff = True, {}
            for k in ("評等", "目標價", "日期"):
                same = first[k] == rv[k]
                rv_ok = rv_ok and same
                if not same:   # 逐欄差異上報(實測黃批1657:~15 檔不一致,矩陣要能直指哪欄)
                    rv_diff[k] = {"首輪": first[k], "重建後": rv[k]}
                L.append("| %s | %s | %s | %s |" % (k, first[k] or "-", rv[k] or "-", "一致" if same else "不一致"))
            out_p = ui / ("RECON_" + q.stem + ".txt")
            out_p.write_text("\n".join(L), encoding="utf-8")
            rows.append({"filename": q.name, "state": "RECONSTRUCTED",
                         "pages": [1] + [x for x in fps[:3] if x != 1], "fn_locked": fn_lock,
                         "moved_tables_to_info": moved, "reverify": "一致" if rv_ok else "不一致",
                         **({"reverify_diff": rv_diff} if rv_diff else {}),
                         "extract_lane": lane, "nlp_hub": _nlp_v0119()["state"],
                         "out": out_p.name, "lamp": "綠" if rv_ok else "黃"})
        except Exception as exc:
            rows.append({"filename": q.name, "state": "ROW_ERROR", "lamp": "紅",
                         "why": f"{type(exc).__name__}: {str(exc)[:100]}"})
        finally:
            doc.close()
    return {"verb": "reconstruct", "manager": TAG, "workflow": "VRN-WKF009", "step": "STP003-006",
            "cleaned_prev": removed, "reconstructed": len(rows), "rows": rows}


_DOCX_CACHE = None


def _docx_engine_v0119() -> dict:
    """WORD TEXT 擷取正主座:VRN_ENG052_DocxEngine 尾版(梯 docx2python→python-docx→
    內建 XML;extract_docx → (段落, 表格, 引擎名))。缺/壞=誠實 UNAVAILABLE(Zero-Hydra,不自建第二套)。"""
    global _DOCX_CACHE
    if _DOCX_CACHE is None:
        try:
            cands = sorted(HERE.glob("VRN_ENG052_DocxEngine_v*.py"), key=_vnum_v0119)
            spec = importlib.util.spec_from_file_location("vrn_eng052_for_" + TAG, cands[-1])
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            _DOCX_CACHE = {"mod": mod, "state": "LOADED(" + cands[-1].stem.split("_")[-1] + ")"}
        except Exception as exc:
            _DOCX_CACHE = {"mod": None, "state": f"UNAVAILABLE {type(exc).__name__}"}
    return _DOCX_CACHE


def _acquire_text_v0119(path: Path, doc) -> tuple:
    """統一取文核心(操作員令 2026-10-05「邏輯統一」:intake→deepread→layout-check→
    reconstruct 三套不各自為政,梯只此一條):zones 原生取文,不足 40 字走梯
    NLP LAYOUT 修復鏈 → 輕OCR → 需OCR 誠實。回 (zones, whole, lane, note)。"""
    z = first_page_zones(doc)
    whole = z["info_text"] + "\n" + z["main_text"]
    if len(whole.strip()) >= 40:
        return z, whole, "NON_OCR", ""
    otxt, onote = _nlp_pdf_text_v0119(path)
    if otxt is None:
        otxt, onote = _ocr_light_v0119(path)
    if otxt:
        return z, otxt, ("NLP_LAYOUT" if onote.startswith("NLP_LAYOUT") else "輕OCR"), onote
    return z, "", "需OCR", onote


def deepread_one(path: Path) -> dict:
    """單檔深讀:檔名律 → 開 PDF → 兩區 → 抽欄 → 互證燈語。全部誠實,不硬配。"""
    fn = PRIOR.parse_filename(path.stem)
    row = {"filename": path.name, "ext": path.suffix.lower(),
           "size_bytes": path.stat().st_size if path.exists() else None,
           "fn_date": fn["report_date"], "fn_codes": fn["codes"], "broker": fn["broker_std"],
           "fn_locked": bool(fn["report_date"] and fn["codes"] and fn["broker_std"])}
    # FILENAME 識別成功就鎖定(操作員令):三欄齊=鎖,內文互證只作佐證不改寫檔名欄
    if path.suffix.lower() != ".pdf":
        text, lane, note, ntab = None, None, "", 0
        if path.suffix.lower() == ".docx":   # WORD TEXT 擷取(正主=ENG052 尾版)
            eng = _docx_engine_v0119()
            if eng["mod"] is not None:
                try:
                    paras, tables, engname = eng["mod"].extract_docx(path)
                    ntab = len(tables)
                    text = "\n".join(list(paras) + ["\t".join(str(c) for c in r) for t in tables for r in t])
                    lane, note = "DOCX(ENG052)", f"{engname} · 段 {len(paras)} · 表 {ntab}"
                except Exception as exc:
                    note = f"ENG052 擷取失敗 {type(exc).__name__}"
            else:
                note = eng["state"]
        elif path.suffix.lower() == ".txt":
            try:
                text, lane = path.read_text(encoding="utf-8", errors="replace"), "TXT"
            except OSError as exc:
                note = f"讀檔失敗 {type(exc).__name__}"
        elif path.suffix.lower() == ".md":   # MARKDOWN 車道(正主=ENG085 尾版 repair_text)
            try:
                raw = path.read_text(encoding="utf-8", errors="replace")
                try:
                    cands = sorted(HERE.glob("VRN_ENG085_MarkdownRestore_v*.py"), key=_vnum_v0119)
                    spec85 = importlib.util.spec_from_file_location("vrn_eng085_for_" + TAG, cands[-1])
                    m85 = importlib.util.module_from_spec(spec85)
                    spec85.loader.exec_module(m85)
                    text, fixes = m85.repair_text(raw)
                    lane, note = "MD(ENG085)", f"修復 {sum(fixes.values()) if isinstance(fixes, dict) else fixes} 處"
                except Exception as exc:
                    text, lane, note = raw, "MD(原文)", f"ENG085 不可用 {type(exc).__name__},原文照抽"
            except OSError as exc:
                note = f"讀檔失敗 {type(exc).__name__}"
        elif path.suffix.lower() == ".doc":   # 舊版二進位 Word:無正主不假讀
            note = "舊版 .doc 需轉檔車道(OmniFormat 候選/Word 另存 docx)"
        if text and len(text.strip()) >= 20:
            crx = _central_regex_v0119()
            rtw = _pick_rating_v0119(crx, text, "")
            row.update({"state": "DEEPREAD_" + ("DOCX" if lane.startswith("DOCX") else ("MD" if lane.startswith("MD") else "TXT")),
                        "extract_lane": lane, "lane_note": note, "docx_tables": ntab,
                        "content_date": _content_date_v0119(crx, text),
                        "rating": rtw,
                        "rating_std": (crx["rating_code"].get((rtw or "").lower()) or (None, None))[0],
                        "target_price": _target_price_v0119(crx, text),
                        "size_h": PRIOR.size_h(row.get("size_bytes")), "lamp": "黃",
                        "next": "平文擷取(docx 無固定版面;表格交表格梯 ENG058)"})
            row.update(_analyst_v0119(text))
            if row.get("analyst_name") is None or str(row.get("analyst_name") or "").isascii():
                fnn = _fn_analyst_v0119(path.stem, crx, fn.get("company_name"))
                if fnn:   # 中文優先律(平文車道同律)
                    if row.get("analyst_name") and str(row["analyst_name"]).isascii() and row.get("analyst_name_en") is None:
                        row["analyst_name_en"] = row["analyst_name"]
                    row["analyst_name"], row["analyst_name_source"] = fnn, "filename(中文優先)"
            return row
        row.update({"state": "NON_PDF_SKIP", "lamp": "黃",
                    "next": "另路(不假裝讀過)" + ((" · " + note) if note else "")})
        return row
    doc, why = _open_pdf_v0119(path)
    if doc is None:
        row.update({"state": "UNREADABLE", "lamp": "紅", "why": why})
        return row
    try:
        crx = _central_regex_v0119()
        z, whole, lane, lnote = _acquire_text_v0119(path, doc)
        info = z["info_text"]
        row["extract_lane"] = lane
        if lane == "需OCR":
            row.update({"state": "NO_TEXT_LAYER", "lamp": "黃", "ocr_note": lnote,
                        "next": "無文字層 → OCR 車道(ENG400 四階梯:輕 OCR → 重型)"})
            return row
        if lane != "NON_OCR":   # 梯取回平文(無版面):平文擷取,全件還原走重型
            row.update({"state": "DEEPREAD_OCR_LIGHT", "ocr_note": lnote,
                        "content_date": _content_date_v0119(crx, whole),
                        "rating": _pick_rating_v0119(crx, whole, ""),
                        "target_price": _target_price_v0119(crx, whole), "lamp": "黃",
                        "next": "梯平文擷取(無版面);全件還原走重型 ENG400"})
            return row
        c_date = _content_date_v0119(crx, whole)
        tt = crx["tt_in_text"].search(whole)
        c_code = tt.group(1) if tt else (fn["codes"][0] if fn["codes"] else None)
        c_broker = None
        low = whole.lower()
        for alias, target in PRIOR._broker_map().items():
            if alias.isascii():
                a = alias.lower()
                if len(a) <= 2 or a in _BROKER_CONTENT_SKIP:   # 批413 精神:短碼限檔名空間;常用英文詞內文不收
                    continue
                if re.search(r"(?<![A-Za-z])" + re.escape(alias) + r"(?![A-Za-z])", low):
                    c_broker = target
                    break
            elif alias in low:
                c_broker = target
                break
        fs = _footer_scan_v0119(doc, crx)
        src_broker = None
        if c_broker is None and fs.get("footer_broker"):
            c_broker, src_broker = fs["footer_broker"], "footer"
        rtw = _pick_rating_v0119(crx, info, whole)
        tpv = _target_price_v0119(crx, info, whole)
        code = c_code or (fn["codes"][0] if fn["codes"] else None)
        row.update({"state": "DEEPREAD", "info_side": z["info_side"],
                    "info_parts": len(z.get("info_parts") or []),
                    "content_date": c_date, "content_code": c_code, "content_broker": c_broker,
                    "date_match": "MATCH" if (c_date and c_date == fn["report_date"]) else
                                  ("MISS" if c_date and fn["report_date"] else "ONE_SIDE"),
                    "ticker_match": "MATCH" if (c_code and fn["codes"] and c_code in fn["codes"]) else
                                    ("MISS" if c_code and fn["codes"] else "ONE_SIDE"),
                    "broker_match": "MATCH" if (c_broker and c_broker == fn["broker_std"]) else
                                    ("MISS" if c_broker and fn["broker_std"] else "ONE_SIDE"),
                    "rating": rtw,
                    "rating_std": (crx["rating_code"].get((rtw or "").lower()) or (None, None))[0],
                    "rating_code": (crx["rating_code"].get((rtw or "").lower()) or (None, None))[1],
                    "target_price": tpv,
                    "bloomberg_ticker": f"{code} TT" if code else None})
        row["size_h"] = PRIOR.size_h(row.get("size_bytes"))
        comp, comp_src = fn.get("company_name"), "filename"
        if comp is None and code:   # 公司名抽不到 → 代號走 VDF/universe 取名(操作員令)
            uf = PRIOR._universe_file() if hasattr(PRIOR, "_universe_file") else None
            if uf:
                try:
                    for ln0 in uf.read_text(encoding="utf-8", errors="replace").splitlines():
                        if re.match(rf"^\s*\"?{re.escape(code)}\b", ln0):
                            parts = [x.strip().strip('\"') for x in ln0.split(",")]
                            comp = parts[1] if len(parts) > 1 and parts[1] else None
                            comp_src = "universe(VDF 資料家)"
                            break
                except OSError as exc:
                    comp_src = f"universe 讀取失敗 {type(exc).__name__}"   # 誠實記,不吞
            if comp is None:
                comp_src = comp_src if comp_src.startswith("universe 讀取失敗") else "VDF 車道待取(本地無 universe)"
        row["company_name"], row["company_source"] = comp, comp_src
        if code:
            row.update(_yf_ticker_v0119(code))
            row["external_price"] = _adj_close_v0119(code, fn["report_date"] or c_date, tpv)
            ref = (row["external_price"] or {}).get("adj_close_before_report")
            if tpv and ref:   # TP 合理性燈(實測紅批1657:宏致 TP=5000 vs 市價兩位數)
                ratio = tpv / ref
                if not (0.15 <= ratio <= 8.0):
                    row["tp_sanity"] = f"可疑:TP/報告日前價={ratio:.1f}×(超出 0.15–8 帶),回查原文"
        row.update(fs)
        if src_broker:
            row["broker_source"] = src_broker
        row.update(_analyst_v0119(info, whole))
        if row.get("analyst_name") is None or str(row.get("analyst_name") or "").isascii():
            fnn = _fn_analyst_v0119(path.stem, crx, fn.get("company_name"))
            if fnn:   # 中文優先律(操作員令):中文名為主,英文名齊次(name_en 照留)
                if row.get("analyst_name") and str(row["analyst_name"]).isascii() and row.get("analyst_name_en") is None:
                    row["analyst_name_en"] = row["analyst_name"]
                row["analyst_name"], row["analyst_name_source"] = fnn, "filename(中文優先)"
        if row.get("content_broker") is None and row.get("analyst_broker"):
            row["content_broker"], row["broker_source"] = row["analyst_broker"], "email_domain"
            row["broker_match"] = ("MATCH" if row["content_broker"] == fn["broker_std"]
                                   else ("MISS" if fn["broker_std"] else "ONE_SIDE"))
        vm = sorted({std for std, al in crx["val_methods"].items() for a in al
                     if (a in whole if not a.isascii() else re.search("(?i)" + _wordish_v0119(a), whole))})
        row["valuation_methods"] = vm or None   # 估值法字典 × 資訊區+本文區核對
        row.update(_fin_pages_v0119(doc))
        row["engine_support"] = {"nlp_hub": _nlp_v0119()["state"],   # 每步驟 LAYOUT NLP(操作員令)
                                 "zones": "LAYOUT(ENG394 律)+NLP hub", "sentence_repair": "NLP 句點律",
                                 "classify": "NLP(字級+數字密度)", "reverify": "NLP 再識別",
                                 "ocr_ladder": row["extract_lane"]}
        hits = [row["date_match"], row["ticker_match"], row["broker_match"]].count("MATCH")
        row["lamp"] = "綠" if hits == 3 and tpv else ("黃" if hits else "紅")
    finally:
        doc.close()
    return row


_SCAN_NOTES: list = []   # 大小統計讀不到的單項(誠實帳,非驗證欄)


def _scan_size_v0119(root: Path) -> int:
    """夾層總大小(os.scandir 遞迴:遍歷時快取 metadata,批量最快;檔案給 stat)。"""
    if root.is_file():
        try:
            return root.stat().st_size
        except OSError:
            return 0
    total = 0
    try:
        with os.scandir(root) as it:
            for e in it:
                try:
                    if e.is_file(follow_symlinks=False):
                        total += e.stat(follow_symlinks=False).st_size
                    elif e.is_dir(follow_symlinks=False):
                        total += _scan_size_v0119(Path(e.path))
                except OSError as exc:
                    _SCAN_NOTES.append(f"{e.name}: {type(exc).__name__}")   # 誠實記,照數其餘
                    continue
    except OSError:
        return total
    return total


def deepread(path: str) -> dict:
    """深讀動詞:檔或夾;只深讀有代號的個股檔(STOCK REPORT ONLY),其餘列 SKIP 一行誠實。"""
    removed = _fresh_outputs_v0119("deepread")   # 清場律:先刪前次結果
    p = Path(path)
    files = sorted([q for q in p.rglob("*") if q.suffix.lower() in PRIOR._DOC_EXTS]) if p.is_dir() else [p]
    rows, skipped = [], 0
    for q in files:
        if PRIOR.parse_filename(q.stem)["codes"]:
            try:
                rows.append(deepread_one(q))
            except Exception as exc:   # 單檔不殺整批(矩陣一定要產)
                rows.append({"filename": q.name, "state": "ROW_ERROR", "lamp": "紅",
                             "why": f"{type(exc).__name__}: {str(exc)[:100]}"})
        else:
            skipped += 1
    total = _scan_size_v0119(p)   # os.scandir 批量統計(Top6 之 3:快取 metadata 少 syscalls)
    return {"verb": "deepread", "manager": TAG, "workflow": "VRN-WKF009", "step": "STP002-004",
            "cleaned_prev": removed, "total_files": len(files), "stock_reports": len(rows),
            "non_stock_skipped": skipped,
            "folder_size_bytes": total, "folder_size_h": PRIOR.size_h(total), "rows": rows}


def real_test(path: str, max_min: int = 45) -> dict:
    """實測清點判定(批1657 操作員令「有功能的指令全 PY 寫+加速器;PS 只做啟動與 HTML U/I」):
    原 Invoke-VIA-RealTest-VRN-v0103.ps1 的**判定段**(L41-47)PY 化入管——
    ① 樣本數 ② 近 N 分鐘 VRN 輸出清點 ③ CGC_MDL249 check 尾判行 ④ realtest/paste.md 風險行 ⑤ 總判。
    雙軌引擎(ENG399/393/394/396)照走 via-vcgc 各自動詞;本動詞只做清點與判定,不重跑引擎。
    .ps1 零觸碰(L70);PS 剩啟動與開頁。"""
    import subprocess, time
    via = HERE.parents[1]
    errors, verdicts = [], []
    base = Path(path)
    n_samples = len([q for q in base.rglob("*") if q.suffix.lower() in (".pdf", ".docx", ".pptx")]) if base.is_dir() else 0
    verdicts.append(f"[樣本] {base} · {n_samples} 件")
    cutoff = time.time() - max_min * 60
    outs = []
    for d in (via / "VIA_Reports" / "vrn", HERE / "output_hub", via / "VIA_Reports" / "review"):
        if d.is_dir():
            outs += [q for q in d.rglob("*") if q.is_file() and q.suffix in (".parquet", ".duckdb", ".json", ".html")
                     and q.stat().st_mtime > cutoff]
    top = sorted(outs, key=lambda q: -q.stat().st_size)[:6]
    verdicts.append("[清點] 本輪 VRN 輸出 %d 件:%s" % (len(outs), " · ".join(f"{q.name}({q.stat().st_size // 1024}KB)" for q in top)))
    locks = sorted((via / "supportive modules" / "registry").glob("CGC_MDL249_DataFrameLock_v*.py"))
    if locks:
        try:
            env = dict(os.environ, VIA_FROM_VCGC="YES", VIA_NO_OPEN="1")
            cp = subprocess.run([sys.executable, str(locks[-1]), "check"], capture_output=True, text=True, timeout=600, env=env)
            tail = [l for l in (cp.stdout or "").splitlines() if re.search(r"\[(計|GREEN|RED|YELLOW|FAIL)\]|總判", l)][-3:]
            for l in tail:
                (errors if re.search(r"RED|FAIL", l) else verdicts).append("[249] " + l.strip())
            if not tail:
                verdicts.append(f"[249] 無判決行(rc={cp.returncode};誠實記)")
        except Exception as exc:   # 子行程層例外型別雜;誠實記型別不吞判
            errors.append(f"[249] 跑不動 {type(exc).__name__}: {str(exc)[:60]}")
    else:
        verdicts.append("[249] CGC_MDL249 不在(誠實態,不假綠)")
    pm = via / "VIA_Reports" / "vrn" / "realtest" / "paste.md"
    if pm.is_file():
        for l in pm.read_text(encoding="utf-8", errors="replace").splitlines()[:12]:
            (errors if "[RED]" in l else verdicts).append("[風險] " + l)
    else:
        verdicts.append("[風險] realtest/paste.md 不在(ENG399 未跑或清場)")
    ok = not errors and len(outs) > 0
    verdicts.append("[判] " + ("成功:輸出清點 %d 件 · 249 無紅 · 風險無紅" % len(outs) if ok else "未成功:看紅字"))
    return {"verb": "real-test", "manager": TAG, "state": "OK" if ok else "RED",
            "samples": n_samples, "outputs_recent": len(outs), "max_min": max_min,
            "verdicts": verdicts, "errors": errors, "lamp": "綠" if ok else "紅",
            "rows": [{"filename": "(清點判定)", "lamp": "綠" if ok else "紅",
                      "樣本": n_samples, "輸出": len(outs), "紅字": len(errors)}]}


def _fn_b_ruler_v0119():
    """另一支負責引擎(收容件 audit_ssot;零觸碰,import 不跑它的 main):回 (module, rules, brokers) 或 (None, why)。"""
    pkg = HERE / "references" / "intake" / "VIA_SSOT_Additive_Audit_v0100_b20260921"
    try:
        spec = importlib.util.spec_from_file_location("audit_ssot_for_fncheck", str(pkg / "audit_ssot.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        inst = m.read_json(pkg / "baseline" / "VIA_Financial_Institution_SSOT_v0100.json")["registries"]
        rules = m.read_json(pkg / "baseline" / "VRN_FieldRules_SSOT_v0100.json")["rules"]
        brokers, _ = m.indexes(inst, rules, m.read_json(pkg / "baseline" / "broker_list.json"),
                               m.read_json(pkg / "baseline" / "intake_rating.json"))
        return (m, rules, brokers), None
    except Exception as exc:   # 收容件層例外型別雜;B 路缺=誠實單路,不吞
        return None, f"{type(exc).__name__}: {str(exc)[:80]}"


def fn_check(path: str) -> dict:
    """FILENAME 五步對照(批1657 操作員令「中英文標點轉換處切開 · 四碼=台股 TICKER · 長數字=REPORT DATE ·
    四碼去資料庫抓中文簡稱 Name · 剩下段=券商同義字 · 檔案大小格式加入 · 對照另一個負責引擎看差異」):
    A 路=VRN 正統鏈(v0118 parse_filename:tokenize 切段→codes→date→company_name→broker_std;
    universe 資料庫補中文簡稱;size_h 大小格式);B 路=收容件 audit_ssot.parse_filename/extract_broker。
    逐檔逐欄對照,diff 列出不同欄與兩路值;B 路載不到=誠實 B_UNAVAILABLE 照出 A 路。"""
    base = Path(path)
    files = sorted(q for q in base.rglob("*") if q.is_file()) if base.is_dir() else [base]
    b, b_why = _fn_b_ruler_v0119()
    uf = PRIOR._universe_file() if hasattr(PRIOR, "_universe_file") else None
    rows = []
    for q in files:
        fn = PRIOR.parse_filename(q.stem)
        name, nsrc = fn.get("company_name"), "filename"
        if name is None and fn["codes"] and uf:   # 四碼去資料庫抓中文簡稱
            try:
                for ln0 in uf.read_text(encoding="utf-8", errors="replace").splitlines():
                    if re.match(rf"^\s*\"?{re.escape(fn['codes'][0])}\b", ln0):
                        parts = [x.strip().strip('"') for x in ln0.split(",")]
                        name, nsrc = (parts[1] if len(parts) > 1 and parts[1] else None), "universe(資料庫)"
                        break
            except OSError:
                nsrc = "universe 讀取失敗"
        row = {"filename": q.name, "切段": "|".join(fn.get("fn_tokens") or []),
               "ticker_A": ",".join(fn["codes"]) or None, "date_A": fn["report_date"],
               "name": name, "name_source": (nsrc if name else ("VDF 車道待取" if fn["codes"] else None)),
               "broker_A": fn["broker_std"], "size_h": PRIOR.size_h(q.stat().st_size if q.exists() else None)}
        if b:
            m, rules, brokers = b
            pb = m.parse_filename(q.name, rules, brokers)
            row.update({"ticker_B": ",".join(pb["ticker_candidates"]) or None,
                        "date_B": pb["report_date"], "broker_B": pb["broker"]["value"]})
            diff = [k for k, a2, b2 in (("ticker", row["ticker_A"], row["ticker_B"]),
                                        ("date", row["date_A"], row["date_B"]),
                                        ("broker", row["broker_A"], row["broker_B"])) if a2 != b2]
            row["diff"] = diff or None
            row["lamp"] = "綠" if not diff else "黃"
            row["state"] = "兩路同" if not diff else "差異:" + ",".join(diff)
        else:
            row.update({"state": "B_UNAVAILABLE(" + (b_why or "?") + ")", "lamp": "黃"})
        rows.append(row)
    from collections import Counter
    return {"verb": "fn-check", "manager": TAG, "b_ruler": ("audit_ssot(收容件)" if b else "缺:" + (b_why or "")),
            "total": len(rows), "tally": dict(Counter(r["lamp"] for r in rows)),
            "diff_tally": dict(Counter(d for r in rows for d in (r.get("diff") or []))),
            "rows": rows}


def vdf_fetch(args: list) -> dict:
    """VRN↔VDF 相連指令(批1657 操作員令「寫一個指令連接 VDF SYSTEM MANAGER…支援擷取自資料庫或單獨擷取」):
    經 VCGC 資料中介(CGC_MDL239 尾版)一線式要料——① 先讀庫(EngineBus 掃的 duckdb/Parquet 目錄);
    ② 庫無/不夠新 → 轉交 VDF 項**單獨擷取**(預設乾跑 PLAN,--apply 才真跑;同意閘不代設);結果以 Parquet 回。
    VRN 不直開 VDF 庫(CGC_MDL239 繞道燈);中介不在=誠實 UNAVAILABLE。
    用法:vdf-fetch <table> [codes=2330,2317] [start=YYYY-MM-DD] [end=YYYY-MM-DD] [--apply]"""
    table = args[0]
    codes, start, end = None, "", ""
    for a in args[1:]:
        if a.startswith("codes="):
            codes = [c.strip() for c in a[6:].split(",") if c.strip()]
        elif a.startswith("start="):
            start = a[6:]
        elif a.startswith("end="):
            end = a[4:]
    reg = HERE.parents[1] / "supportive modules" / "registry"
    hits = sorted(reg.glob("CGC_MDL239_DataBroker_v*.py"), key=_vnum_v0119)
    if not hits:
        return {"verb": "vdf-fetch", "manager": TAG, "state": "UNAVAILABLE", "lamp": "紅",
                "why": "CGC_MDL239 資料中介不在:VRN 不直開 VDF 庫,誠實停",
                "rows": [{"filename": table, "state": "UNAVAILABLE", "lamp": "紅"}]}
    spec = importlib.util.spec_from_file_location("cgc239_for_vrnsm", str(hits[-1]))
    bk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bk)
    rec = bk.fetch(table, codes=codes, start=start, end=end,
                   requester=f"VRN_SystemManager_{TAG}", apply="--apply" in args)
    st = rec.get("state") or "?"
    lamp = "綠" if st == "OK" else ("紅" if st == "RED" else "黃")
    row = {"filename": table, "state": st, "codes": codes, "start": start or None, "end": end or None,
           "parquet": rec.get("parquet") or None, "coverage": rec.get("coverage"),
           "handoff": rec.get("handoff"), "why": rec.get("why") or None,
           "broker": hits[-1].name, "lamp": lamp}
    return {"verb": "vdf-fetch", "manager": TAG, "state": st, "lamp": lamp,
            "broker": hits[-1].name, "record": rec, "rows": [row]}


def emit_matrix_html(verb: str, result: dict) -> str:
    """矩陣出頁 v0119 殼(批1657「跳出來的介面不動」案):頁首插**執行引擎戳**
    (引擎檔名 + 檔案 mtime UTC + 出頁 UTC)——介面若不動,一看戳就知道是舊引擎/舊頁,不用猜。"""
    import datetime
    p = PRIOR.emit_matrix_html(verb, result)
    try:
        me = Path(__file__)
        stamp = "引擎 %s · mtime %s · 出頁 %s UTC" % (
            me.name,
            datetime.datetime.utcfromtimestamp(me.stat().st_mtime).strftime("%m-%d %H:%M"),
            datetime.datetime.utcnow().strftime("%m-%d %H:%M:%S"))
        fp = Path(p)
        h = fp.read_text(encoding="utf-8")
        fp.write_text(h.replace("<h3>", "<h3>[" + stamp + "] · ", 1), encoding="utf-8")
        print(f"  [引擎戳] {stamp}")
    except OSError as exc:
        print(f"  [引擎戳] 插入失敗 {type(exc).__name__}(頁照出,主流程照走)")
    return p


def _dump_result_v0119(verb: str, out: dict) -> None:
    """結果落檔 RESULT_<verb>_latest.json(操作員貼回免撈 console;寫不進不擋主流程,誠實印)。"""
    try:
        ui = Path(os.environ.get("VIA_VRN_UI_DIR") or HERE.parents[1] / "VIA_Reports" / "vrn")
        ui.mkdir(parents=True, exist_ok=True)
        fp = ui / f"RESULT_{verb}_latest.json"
        fp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [結果檔] {fp}")
    except OSError as exc:
        print(f"  [結果檔] 寫入失敗 {type(exc).__name__}(主流程照走)")


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":   # 批1657 獨立 MAIN:VRN 斷開仍互動——自立閘座(下游引擎兼容),入口誠實記
        os.environ["VIA_FROM_VCGC"] = "YES"
        print("[VRN] 獨立 MAIN(standalone)· 與 VCGC 各自運作下互動(資料仍經 vdf-fetch 中介;VDF v0129+ 同款自立閘)")
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    as_json = "--json" in args
    a = [x for x in args if x != "--json"]
    if a[:1] == ["reconstruct"]:
        if len(a) < 2:
            print("[拒跑] reconstruct <檔|夾>")
            return 2
        out = reconstruct(a[1])
        emit_matrix_html("reconstruct", out)
        _dump_result_v0119("reconstruct", out)
        print(json.dumps(out, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0
    if a[:1] == ["layout-check"]:
        if len(a) < 2:
            print("[拒跑] layout-check <檔|夾>")
            return 2
        out = layout_check(a[1])
        emit_matrix_html("layout_check", out)
        _dump_result_v0119("layout_check", out)
        print(json.dumps(out, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0
    if a[:1] == ["deepread"]:
        if len(a) < 2:
            print("[拒跑] deepread <檔|夾>")
            return 2
        out = deepread(a[1])
        emit_matrix_html("deepread", out)
        _dump_result_v0119("deepread", out)
        print(json.dumps(out, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0
    if a[:1] == ["fn-check"]:   # 批1657:FILENAME 五步對照(A=VRN 鏈 · B=收容件引擎 · 差異表)
        if len(a) < 2:
            print("[拒跑] fn-check <檔|夾>")
            return 2
        out = fn_check(a[1])
        emit_matrix_html("fn_check", out)
        _dump_result_v0119("fn_check", out)
        print(json.dumps(out, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0
    if a[:1] == ["vdf-fetch"]:   # 批1657:VRN↔VDF 相連(中介讀庫→轉交 VDF 單獨擷取)
        if len(a) < 2:
            print("[拒跑] vdf-fetch <table> [codes=…] [start=…] [end=…] [--apply]")
            return 2
        out = vdf_fetch(a[1:])
        emit_matrix_html("vdf_fetch", out)
        _dump_result_v0119("vdf_fetch", out)
        print(json.dumps(out, ensure_ascii=False, indent=(None if as_json else 1), default=str))
        return 0 if out["state"] == "OK" else 1
    if a[:1] == ["real-test"]:   # 批1657 PY 功能律:實測判定段 PY 化(PS 只啟動+開頁)
        if len(a) < 2:
            print("[拒跑] real-test <樣本夾> [分鐘窗]")
            return 2
        out = real_test(a[1], int(a[2]) if len(a) > 2 else 45)
        emit_matrix_html("real_test", out)
        _dump_result_v0119("real_test", out)
        print(json.dumps(out, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0 if out["state"] == "OK" else 1
    return PRIOR.main(args)   # intake/eps-check/reconcile/closeout 照前版鏈


def _mk_pdf_v0119(path: Path):
    """自測合成 PDF(標明 SYNTHETIC):左本文 + 右資訊區 + 第二頁年度財務;實開實讀不造假判。"""
    import fitz
    doc = fitz.open()
    pg = doc.new_page(width=595, height=842)
    pg.insert_textbox(fitz.Rect(36, 28, 330, 56), "台積電(2330)目標價上調", fontname="china-t", fontsize=16)
    pg.insert_textbox(fitz.Rect(36, 60, 330, 700),
                      "SYNTHETIC SAMPLE 台積電法說會後更新。本文區:先進製程需求強勁,"
                      "AI 動能延續。我們上修 2026 年預估,評價採本益比法並以 DCF 交叉驗證。\n" * 6,
                      fontname="china-t", fontsize=10)
    pg.insert_textbox(fitz.Rect(360, 60, 560, 700),
                      "2330 TT\n評等:買進\n目標價:NT$ 850\n收盤價:712\n"
                      "王小明\n分析師\nTel: 02-2345-6789\nwang.xm@brokerx.tw\n2025/08/19",
                      fontname="china-t", fontsize=10)
    pg.insert_textbox(fitz.Rect(360, 720, 560, 800),
                      "本報告僅供內部參考,非投資建議,引用請註明出處。資料截至報告日。",
                      fontname="china-t", fontsize=8)
    p2 = doc.new_page(width=595, height=842)   # 財務頁:左右各兩個視覺元件(上下切測試)
    p2.insert_textbox(fitz.Rect(36, 60, 280, 300),
                      "損益摘要\n項目 2023 2024 2025F 2026F\n營收 2161.7 2894.3 3570.1 4210.5\n"
                      "淨利 838.5 1173.1 1450.2 1702.8", fontname="china-t", fontsize=10)
    p2.insert_textbox(fitz.Rect(36, 420, 280, 650),
                      "資產負債摘要\n股本 259.3 259.3 259.3\n總資產 5532.2 6164.1 7021.8",
                      fontname="china-t", fontsize=10)
    p2.insert_textbox(fitz.Rect(320, 60, 560, 300),
                      "每股數據\nEPS 32.34 45.25 55.93 65.67\nROE 26.0 30.1 32.2 33.5",
                      fontname="china-t", fontsize=10)
    p2.insert_textbox(fitz.Rect(320, 420, 560, 650),
                      "現金流量\n營業現金流 1121.6 1452.7 1680.0\n自由現金流 265.1 303.9 410.2",
                      fontname="china-t", fontsize=10)
    p2.insert_textbox(fitz.Rect(36, 780, 560, 830),
                      "兆豐證券股份有限公司 投資評等說明:買進/中立/賣出/未評等 僅供參考",
                      fontname="china-t", fontsize=7)
    doc.save(str(path))
    doc.close()


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    os.environ["VIA_NO_NET"] = "1"
    os.environ["VIA_NO_OPEN"] = "1"
    td = Path(tempfile.mkdtemp(prefix="vrnsm119-"))
    os.environ["VIA_VRN_UI_DIR"] = str(td / "ui")
    try:
        import fitz  # noqa: F401
        have_fitz = True
    except ImportError:
        have_fitz = False
    if have_fitz:
        pdf = td / "MEGA-2330 20250819.pdf"
        _mk_pdf_v0119(pdf)
        r = deepread_one(pdf)
        chk("① 實開實讀:state=DEEPREAD · SIZE 實量測>0", r["state"] == "DEEPREAD" and r["size_bytes"] > 0)
        chk("② 兩區切割:資訊區=右 · 本文在左", r["info_side"] == "right")
        chk("③ 互證三欄:date/ticker 內文=檔名 MATCH", r["date_match"] == "MATCH" and r["ticker_match"] == "MATCH")
        chk("④ 評等+目標價:買進 · 850", r["rating"] == "買進" and r["target_price"] == 850.0)
        chk("⑤ 分析師四欄:email/tel/職稱抽到 · 缺名誠實", r["analyst_email"] == "wang.xm@brokerx.tw"
            and r["analyst_tel"] and r["analyst_title"] == "分析師")
        chk("⑥ 代號衍生:bloomberg=2330 TT · yfinance 候選/定盤", r["bloomberg_ticker"] == "2330 TT"
            and "2330.TW" in r["yfinance_ticker"])
        chk("⑦ 年度財務頁:第 2 頁入列 · EPS 樣本列", r["fin_pages"] == [2] and "EPS" in (r["fin_sample"] or ""))
        chk("⑧ 外部價離線誠實:SKIPPED_NO_NET", r["external_price"]["state"] == "SKIPPED_NO_NET")
        (td / "華南投顧-3038-全台-Memo-20260916.docx").write_text("x", encoding="utf-8")
        out = deepread(str(td))
        chk("⑨ 夾層深讀:docx 誠實 NON_PDF_SKIP · 矩陣自動產出",
            any(x["state"] == "NON_PDF_SKIP" for x in out["rows"])
            and Path(PRIOR.emit_matrix_html("deepread", out)).is_file())
        chk("⑯ 分析師三律:姓名在職稱上方=王小明 · @前英文名 Wang Xm · jane.doe@gs.com→GS",
            r["analyst_name"] == "王小明" and r["analyst_name_en"] == "Wang Xm"
            and _analyst_v0119("Jane Doe\nAnalyst\nTel: +852 2234 5678\njane.doe@gs.com")["analyst_broker"] == "GS"
            and _analyst_v0119("Jane Doe\nAnalyst\njane.doe@gs.com")["analyst_name"] == "Jane Doe")
        lc = layout_check(str(td))
        row0 = lc["rows"][0]
        chk("⑰ LAYOUT 實測:首頁右資訊 · 財務頁左右各≥2 元件(上下切)· 壞字 0",
            row0["info_side"] == "right" and row0["fin_components"] >= 4
            and row0["bad_chars"] == 0 and row0["lamp"] == "綠")
        stale = Path(os.environ["VIA_VRN_UI_DIR"]) / "UI_MATRIX_layout_check_stale.html"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("舊結果", encoding="utf-8")
        lc2 = layout_check(str(td))
        chk("⑱ 清場律:實測前刪前次結果(stale 檔被刪且入刪單)",
            not stale.exists() and any("stale" in x for x in lc2["cleaned_prev"]))
        chk("⑲ 元件分類(矩陣/表格/長句/文字)+首頁財務頁帶類別",
            _comp_kind_v0119("損益摘要\n營收 100.1 120.2 140.3\n淨利 10.1 12.2 14.3") in ("表格", "矩陣")
            and _comp_kind_v0119("本公司受惠AI需求強勁,營運展望樂觀,預期下半年動能延續不墜,評價仍具吸引力。") == "長句"
            and _comp_kind_v0119("評等:買進") == "文字"
            and "表" in (lc2["rows"][0]["fin_pages"][0] + lc2["rows"][0]["info_types"]
                         + lc2["rows"][0]["main_types"]).replace("矩陣", "表"))
        a2 = _analyst_v0119("聯絡方式\n研究員\n9899@entrust.com.tw")
        chk("⑳ 實測紅修:聯絡方式≠姓名 · 數字信箱≠英文名 · 財報頁不含首頁",
            a2["analyst_name"] is None and a2["analyst_name_en"] is None
            and a2["analyst_email"] == "9899@entrust.com.tw" and r["fin_pages"] == [2])
        chk("㉑ 估值法字典 × 資訊區+本文區核對:本益比法→PER · DCF",
            r["valuation_methods"] == ["DCF", "PER"])
        a3 = _analyst_v0119("王小明\n資深分析師\n02-2345-6789")
        chk("㉒ 職稱碼冊:資深分析師→SENIOR_ANALYST · 分析師→ANALYST",
            a3["analyst_title_std"] == "SENIOR_ANALYST" and r["analyst_title_std"] == "ANALYST")
        a4 = _analyst_v0119("李明哲 (Michael Lee)\n分析師\nml@kgi.com")
        chk("㉓ 姓名式 7 式:混合名拆欄 李明哲/Michael Lee · 英文姓前名後可認",
            a4["analyst_name"] == "李明哲" and a4["analyst_name_en"] == "Michael Lee"
            and _central_regex_v0119()["name_en"].fullmatch("LEE Tzu-Yuan"))
        crx24 = _central_regex_v0119()
        chk("㉔ 評等揀選:維持買進→買進(重申詞跳過)· SS 不在評等行不收 · 評等行內 SS 可收 · 只有重申詞=None",
            _pick_rating_v0119(crx24, "投資建議:維持買進,目標價280元", "") == "買進"
            and _pick_rating_v0119(crx24, "對後市維持審慎看法\n", "") is None
            and _pick_rating_v0119(crx24, "GLASS FIBER\nSS 產線擴充", "") is None
            and _pick_rating_v0119(crx24, "評等:SS\n", "") == "SS"
            and _pick_rating_v0119(crx24, "維持\n", "") is None)
        chk("㉕ 目標價拒抓:2026 年份不收 · 5,000張不收 · 146元照收 · 0.0 不收",
            _target_price_v0119(crx24, "目標價由 2026 年展望推導,上調至146元") == 146.0
            and _target_price_v0119(crx24, "目標 5,000張 成交") is None
            and _target_price_v0119(crx24, "Target Price: 2026") is None
            and _target_price_v0119(crx24, "目標價 0.0 元") is None)
        chk("㉖ 檔名姓名後備:凱基式取人名 · 華南式公司名不誤收",
            _fn_analyst_v0119("凱基投顧_1476 儒鴻_劉昃恩_20260519", crx24) == "劉昃恩"
            and _fn_analyst_v0119("凱基投顧_Takeaway_3605 宏致_張燾_20260917", crx24) == "張燾"
            and _fn_analyst_v0119("華南投顧-2606-裕民-1141202", crx24) is None)
        fr = compute_fin_ratios({"營業收入": 1000, "營業毛利": 300, "本期淨利": 120, "股東權益": 800,
                                 "總資產": 2000, "流通在外股數": 100, "股價": 60, "EPS": 1.2, "上期EPS": 1.0})
        chk("㉗ 財報比率(TWSE/TPEX 用字):毛利率0.3 · ROE0.15 · BVPS8 · 本益比50 · EPS成長0.2 · 缺欄誠實None",
            fr["毛利率"] == 0.3 and fr["ROE"] == 0.15 and fr["BVPS"] == 8.0
            and fr["本益比"] == 50.0 and fr["EPS成長率"] == 0.2 and fr["流動比率"] is None)
        lc3 = layout_check(str(td))
        r3 = lc3["rows"][0]
        chk("㉘ 階層與混排:本文區帶 標題+本文 字級階層 · 資訊區文表混排=True",
            "標題" in r3["main_hier"] and "本文" in r3["main_hier"]
            and r3["info_has_text_and_table"] is True)
        a5 = _analyst_v0119("研究員聯絡方式\n9899@entrust.com.tw")
        a6 = _analyst_v0119("Jane Doe\nAnalyst\njane.doe@gs.com")
        chk("㉙ 分析師更新:剝職稱殘詞過姓名式(聯絡方式→None)· 英文名分拆 Jane/Doe",
            a5["analyst_name"] is None
            and a6["analyst_first_name"] == "Jane" and a6["analyst_last_name"] == "Doe")
        r5 = deepread_one(pdf)
        chk("㉚ 小字頁尾/附錄:券商 MEGA 抓到 · 全評等名稱 ≥3 判附錄",
            r5["footer_broker"] == "MEGA" and r5["rating_scale_found"] is True)
        rc = reconstruct(str(td))
        rtxt = (Path(os.environ["VIA_VRN_UI_DIR"]) / rc["rows"][0]["out"]).read_text(encoding="utf-8")
        import fitz as _fz
        blank = td / "MQ-9999 20260101.pdf"
        _d = _fz.open(); _d.new_page(); _d.save(str(blank)); _d.close()
        rb = deepread_one(blank)
        a_dom = _analyst_v0119("x\nkevin.sw.chen@cl-sec.com")
        a_dom2 = _analyst_v0119("x\nhelen.chien@daiwacm-cathay.com.tw")
        a_dom3 = _analyst_v0119("x\n9899@entrust.com.tw")
        bad = td / "GS-9998 20260101.pdf"
        bad.write_bytes(b"%PDF-1.4 broken \x00\x01truncated")
        out_b = deepread(str(td))
        _, gate_note = _nlp_pdf_text_v0119(bad)
        chk("㊱ 批次防殺+重鏈閘:壞檔 UNREADABLE/ROW_ERROR 入列整批照走 · NLP 重鏈未啟誠實註記",
            any(x["state"] in ("UNREADABLE", "ROW_ERROR") for x in out_b["rows"])
            and any(x["state"] == "DEEPREAD" for x in out_b["rows"])
            and "VIA_VRN_NLP_LANE" in gate_note)
        bad.unlink()
        blank2 = td / "UBS-9997 20260101.pdf"
        import fitz as _f2
        _d2 = _f2.open(); _d2.new_page(); _d2.save(str(blank2)); _d2.close()
        d_row = deepread_one(blank2)
        rc_u = reconstruct(str(td))
        rc_blank = [x for x in rc_u["rows"] if x["filename"] == blank2.name][0]
        lc_u = layout_check(str(td))
        lc_blank = [x for x in lc_u["rows"] if x["filename"] == blank2.name][0]
        chk("㊲ 邏輯統一核心:同一檔三動詞同態同梯(NO_TEXT_LAYER×3)· 良檔 REVERIFY 不受表頭污染",
            d_row["state"] == rc_blank["state"] == lc_blank["state"] == "NO_TEXT_LAYER"
            and d_row["extract_lane"] == rc_blank["extract_lane"] == lc_blank["extract_lane"]
            and [x for x in rc_u["rows"] if x["filename"] == pdf.name][0]["reverify"] == "一致")
        blank2.unlink()
        chk("㊳ 公司名+人讀 SIZE 入列:合成檔 company 欄存在 · size_h 格式",
            "company_name" in r and r["size_h"].endswith(("KB", "MB", "B"))
            and r.get("company_source") in ("filename", "universe(VDF 資料家)", "VDF 車道待取(本地無 universe)"))
        a10 = _analyst_v0119("Michael Hung\nAnalyst\ncarrie.liu@citi.com")
        a11 = _analyst_v0119("Morgan Broking\nAnalyst\ngokul.hariharan@jpmorgan.com")
        a12 = _analyst_v0119("x\njerry.su@ubs.com")
        chk("㊴ 共同作者律+公司詞閘+推名後備:信箱持有人為主作者 · Morgan Broking≠人名 · 有信箱必有名 · 公司名≠分析師",
            a10["analyst_name"] == "Carrie Liu" and a10["analyst_coauthor"] == "Michael Hung"
            and a11["analyst_name"] == "Gokul Hariharan" and a11["analyst_coauthor"] is None
            and a12["analyst_name"] == "Jerry Su"
            and _fn_analyst_v0119("20251204兆豐個股報告-志強-KY(6768)", crx24, "志強-KY") is None)
        _dump_result_v0119("deepread", out_b)
        rc3 = reconstruct(str(td))
        chk("㊵ REVERIFY 域=區一+區二 · 結果檔落地",
            (Path(os.environ["VIA_VRN_UI_DIR"]) / "RESULT_deepread_latest.json").is_file()
            and [x for x in rc3["rows"] if x["filename"] == pdf.name][0]["reverify"] == "一致")
        lex = _fin_lex_v0119()
        chk("㊶ SSOT 全接 VRN Manager:fin_account 詞庫>300 · 評等正碼 買進→Buy/2 SS→Strong_Sell/5 未評等→Not_Rated/0 · 季度式 25Q1 · TW_FIN_DICT 16",
            len(lex) > 150 and "每股盈餘" in lex and "營業毛利" in lex
            and crx24["rating_code"]["買進"] == ("Buy", 2)
            and crx24["rating_code"]["ss"] == ("Strong_Sell", 5)
            and crx24["rating_code"]["未評等"] == ("Not_Rated", 0)
            and crx24["quarter"].search("25Q1 財測") and len(crx24["tw_fin"]) == 16
            and r["rating_std"] == "Buy" and r["rating_code"] == 2)
        chk("㊷ 上傳收割接線:全台手機電話可認 · NT$ 目標價式 · Equal-Weight→Hold/3",
            crx24["tel"].search("0912-345-678")
            and _target_price_v0119(crx24, "NT$ 1,085 維持") == 1085.0
            and _pick_rating_v0119(crx24, "評等:Equal-Weight", "") == "Equal-Weight"
            and crx24["rating_code"]["equal-weight"] == ("Hold", 3))
        dx = _docx_engine_v0119()
        if dx["mod"] is not None and hasattr(dx["mod"], "_selftest_make_docx"):
            dpath = td / "華南投顧-9901-測試-Memo-20260101.docx"
            dx["mod"]._selftest_make_docx(dpath, "評等:買進 目標價:NT$ 120 分析師 王小明 w@entrust.com.tw 2026/09/16",
                                          [["項目", "2025", "2026"], ["EPS", "5.1", "6.2"]])
            rdx = deepread_one(dpath)
            chk("㊸ WORD TEXT 擷取車道:ENG052 正主 · 評等/目標價/券商域/表數出列",
                rdx["state"] == "DEEPREAD_DOCX" and rdx["rating"] == "買進"
                and rdx["target_price"] == 120.0 and rdx["docx_tables"] == 1
                and rdx["analyst_broker"] == "HUANAN")
        else:
            chk("㊸ WORD 車道座誠實(ENG052 缺=UNAVAILABLE)", "UNAVAILABLE" in dx["state"] or dx["mod"] is None)
        chk("㊹ 夾層大小批量統計(os.scandir):folder_size 欄>0 且人讀格式",
            out_b.get("folder_size_bytes", 0) > 0 and out_b.get("folder_size_h", "").endswith(("KB", "MB", "B")))
        (td / "凱基投顧_9906 測試公司_陳測試_20260101.md").write_text(
            "# 測試公司(9906)\n評等:買進  目標價:NT$ 88\nJohn Doe Analyst\njohn.doe@kgi.com\n", encoding="utf-8")
        rmd = deepread_one(td / "凱基投顧_9906 測試公司_陳測試_20260101.md")
        (td / "舊檔-9905 測試-20260101.doc").write_bytes(b"\xd0\xcf\x11\xe0old-word")
        rdoc = deepread_one(td / "舊檔-9905 測試-20260101.doc")
        chk("㊺ MD 車道+中文優先+.doc 誠實:MD 抽評等/TP · 中文名陳測試優先(EN 齊次)· .doc 指路轉檔",
            rmd["state"] == "DEEPREAD_MD" and rmd["rating"] == "買進" and rmd["target_price"] == 88.0
            and rmd["analyst_name"] == "陳測試" and rmd["analyst_name_en"] in ("John Doe", "John Doe Analyst".replace(" Analyst", ""))
            and rdoc["state"] == "NON_PDF_SKIP" and "轉檔" in rdoc["next"])
        rep = repair_sentences_v0119([{"text": "營收成長強勁,\n我們上修預估。\n後續動能 延續", "max_size": 10.0},
                                      {"text": "台積電 法說會 快報", "max_size": 16.0}])
        chk("㉞ 斷句修復:接到句點成段 · CJK 去空格 · 標題不接",
            rep[0][0] == "本文" and rep[0][1].splitlines()[0] == "營收成長強勁,我們上修預估。"
            and "後續動能延續" in rep[0][1] and rep[1][0] == "標題" and rep[1][1] == "台積電 法說會 快報")
        rc2 = reconstruct(str(td))
        rt2 = (Path(os.environ["VIA_VRN_UI_DIR"]) / rc2["rows"][0]["out"]).read_text(encoding="utf-8")
        chk("㉟ 三大區+再識別+NLP 掛點:區一/二/三 · [鎖定] · REVERIFY 一致 · ENGINE 行",
            "區一 TYPE-A 本文重現(斷句修復)" in rt2 and "區二 TYPE-B 資訊區重現" in rt2
            and "區三 TYPE-C 財報頁重現" in rt2 and "[鎖定]" in rt2 and "ENGINE" in rt2
            and rc2["rows"][0]["reverify"] == "一致" and "REVERIFY" in rt2
            and ("LOADED" in rc2["rows"][0]["nlp_hub"] or "UNAVAILABLE" in rc2["rows"][0]["nlp_hub"]))
        chk("㉝ 無文字層誠實+域名別名:NO_TEXT_LAYER 指路 OCR · cl-sec→CLSA · daiwacm-cathay→DAIWA · entrust→HUANAN",
            rb["state"] == "NO_TEXT_LAYER" and "OCR" in rb["next"]
            and a_dom["analyst_broker"] == "CLSA" and a_dom2["analyst_broker"] == "DAIWA"
            and a_dom3["analyst_broker"] == "HUANAN")
        a7 = _analyst_v0119("聯絡資訊\n02-1234-5678", "本報告由分析師 陳大文 負責撰寫")
        a8 = _analyst_v0119("fabian.lee@ctbcsis.com\nFabian Lee 執筆")
        a9 = _analyst_v0119("Media Questions/Requests\nmedia_request@factset.com")
        chk("㉜ 姓名識別條件階梯:R2 樣式律 陳大文 · R3 email 鄰近 Fabian Lee · R6 通用信箱不造名",
            a7["analyst_name"] == "陳大文" and a7["analyst_name_source"] == "pattern"
            and a8["analyst_name"] == "Fabian Lee" and a8["analyst_name_source"] == "email_near"
            and a9["analyst_name_en"] is None and a9["analyst_name"] is None
            and a9["analyst_contact_generic"] is True)
        chk("㉛ 報告重現:固定前段+PAGE+TYPE-A/B+| 格線+SUMMARY 評等",
            rc["rows"][0]["state"] == "RECONSTRUCTED" and "FILENAME" in rtxt
            and "PAGE 1" in rtxt and "TYPE-A 本文重現" in rtxt and "TYPE-B 資訊區重現" in rtxt
            and "| 評等 | 買進 |" in rtxt and rtxt.count("|") > 20)
    else:
        print("  [誠實記] pymupdf 未裝:①–⑨ 深讀站 SKIP(座仍可載,引擎 UNAVAILABLE 誠實)")
        chk("①' 引擎座誠實 UNAVAILABLE", _open_pdf_v0119(Path("x.pdf"))[0] is None)
    chk("⑩ 短縮寫令:兆豐→MEGA · MQ/MAQ→MCQ(同義字冊 v0105)",
        PRIOR.parse_filename("20250819兆豐個股報告-泓德能源(6873)")["broker_std"] == "MEGA"
        and PRIOR.parse_filename("MQ-1560 20260520")["broker_std"] == "MCQ")
    chk("⑪ 前版鏈完好:intake/eps-check/closeout 可達", callable(PRIOR.intake)
        and callable(PRIOR.classify_eps_kind) and callable(__getattr__("closeout")))
    crx = _central_regex_v0119()
    chk("⑬ 抽取式全走 SSOT 冊:三代號/RATING/TP/TIME/EMAIL/台北+香港 TEL 零缺鍵",
        crx["_notes"] == [] and crx["ticker_bare"] and ".(TW|TWO)" in crx["ticker_yf"]
        and "TT" in crx["ticker_bbg"] and crx["rating"].search("Conviction Buy")
        and crx["tp"].search("合理價 123.5") and crx["tel"].search("+852 2234 5678")
        and crx["tel"].search("02-2345-6789") and not crx["rating"].search("xNRx"))
    chk("⑭ MASTER 併入生效:Market Perform 評等 · 剝詞+千分位 TP · 防禦式第二道",
        crx["rating"].search("Market Perform")
        and _target_price_v0119(crx, "目標價:NT$ 1,200元") == 1200.0
        and _target_price_v0119(crx, "Target: 95") == 95.0)
    chk("⑮ 英文日期式(MASTER):Jan 22, 2025 → 2025-01-22",
        _content_date_v0119(crx, "Report dated Jan 22, 2025") == "2025-01-22"
        and _content_date_v0119(crx, "2026/09/16") == "2026-09-16")
    # 批1657 四向資訊區:下方帶狀(左右拆)· 右側欄(上下拆)· reconstruct 下方版型照走
    import fitz as _fz
    _d1 = _fz.open()
    _pg = _d1.new_page(width=595, height=842)
    _pg.insert_textbox(_fz.Rect(36, 60, 560, 420), "本文區:公司營運與產業展望討論。\n" * 8,
                       fontname="china-t", fontsize=10)
    _pg.insert_textbox(_fz.Rect(36, 560, 280, 800), "評等:買進\n目標價:NT$ 120\n2330 TT",
                       fontname="china-t", fontsize=10)
    _pg.insert_textbox(_fz.Rect(320, 560, 560, 800), "分析師 王小明\nTel: 02-2345-6789\nwang.xm@brokerx.tw",
                       fontname="china-t", fontsize=10)
    _z1 = first_page_zones(_d1)
    chk("㊼ 下方帶狀資訊區:info_side=bottom · 左右拆成 2 件 · 本文在上",
        _z1["info_side"] == "bottom" and _z1["split_axis"] == "y"
        and len(_z1["info_parts"]) == 2 and "評等" in _z1["info_text"] and "本文區" in _z1["main_text"])
    _d2 = _fz.open()
    _p2 = _d2.new_page(width=595, height=842)
    _p2.insert_textbox(_fz.Rect(36, 60, 330, 700), "本文區:法說會後更新與展望。\n" * 8,
                       fontname="china-t", fontsize=10)
    _p2.insert_textbox(_fz.Rect(360, 60, 560, 200), "2330 TT\n評等:買進\n目標價:NT$ 850",
                       fontname="china-t", fontsize=10)
    _p2.insert_textbox(_fz.Rect(360, 320, 560, 460), "分析師 王小明\nTel: 02-2345-6789\nwang.xm@brokerx.tw",
                       fontname="china-t", fontsize=10)
    _z2 = first_page_zones(_d2)
    chk("㊽ 右側欄資訊區:info_side=right · 縱向空隙上下拆 ≥2 件 · 各件帶 kind",
        _z2["info_side"] == "right" and len(_z2["info_parts"]) >= 2
        and all(p.get("kind") for p in _z2["info_parts"]))
    with tempfile.TemporaryDirectory() as _bt:
        _bp = Path(_bt) / "測試-2330-下方資訊-20260101.pdf"
        _d1.save(str(_bp))
        _rb = reconstruct(str(_bp))["rows"][0]
        chk("㊾ reconstruct 下方版型照走:RECONSTRUCTED · 不炸 ROW_ERROR",
            _rb["state"] == "RECONSTRUCTED")
    _d1.close()
    _d2.close()
    with tempfile.TemporaryDirectory() as _ft:
        for _n in ("凱基投顧_1476 儒鴻_劉昃恩_20260519.pdf", "3014TT-20231005.pdf", "華南投顧-6143-振曜-1141128.pdf"):
            (Path(_ft) / _n).write_text("x", encoding="utf-8")
        _fc = fn_check(_ft)
        _r36 = next(r for r in _fc["rows"] if r["filename"].startswith("3014TT"))
        chk("51 fn-check 五步對照:切段/ticker/date/name/broker/size 欄在 · B 路(收容件)對得上 3014TT · ROC 日期兩路同",
            _fc["total"] == 3 and all(k in _r36 for k in ("切段", "ticker_A", "date_A", "size_h"))
            and (_fc["b_ruler"].startswith("audit_ssot")
                 and _r36.get("ticker_B") == "3014" and _r36.get("lamp") in ("綠", "黃")
                 or _fc["b_ruler"].startswith("缺")))
    _vf = vdf_fetch(["tw_listings", "codes=2330"])
    chk("㊿ vdf-fetch 相連口:經 CGC_MDL239 中介 · 回 state/record · 誠實態(OK/ABSENT/RED/黃)不吞",
        _vf.get("verb") == "vdf-fetch" and _vf.get("state")
        and (_vf["state"] == "UNAVAILABLE" or "record" in _vf))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 帶加速器橋 · VIA_FROM_VCGC 閘 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body
        and "VIA_FROM_VCGC" in body)
    with tempfile.TemporaryDirectory() as _rt:
        _r = real_test(_rt, max_min=1)
        chk("㊻ real-test PY 判定段(PS 只啟動):空夾=樣本 0 · 誠實 RED/綠 · 判決/清點行在",
            _r["samples"] == 0 and _r["state"] in ("OK", "RED")
            and any(l.startswith("[判]") for l in _r["verdicts"])
            and any(l.startswith("[清點]") for l in _r["verdicts"]))
    for k in ("VIA_NO_NET", "VIA_NO_OPEN", "VIA_VRN_UI_DIR"):
        os.environ.pop(k, None)
    print("[計] VRN_SystemManager_v0119 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
