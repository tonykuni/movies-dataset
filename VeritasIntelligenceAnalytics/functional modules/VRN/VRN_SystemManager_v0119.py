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
                              + "|" + pat("RX_TEL_HK", r"\+?852[- ]?\d{4}[- ]?\d{4}") + ")"),
            "date_en": re.compile(pat("RX_DATE_ENGLISH",
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})")),
            "rating": re.compile("(?i)(" + "|".join(_wordish_v0119(t) for t in rating) + ")"),
            "tp": re.compile("(?i)(?:" + "|".join(_wordish_v0119(t) for t in tp_words)
                             + r")[^\d]{0,15}((?:\d{1,3}(?:,\d{3})+|\d{2,5})(?:\.\d+)?)"),
            "tp_defense": re.compile(pat("RX_TARGET_PRICE_DEFENSE",
                r"(?i)(?:Target|目標(?:價)?)\s*[:：$]?\s*[\d,]+(\.\d+)?")),
            "tp_strips": [str(x) for x in (syn.get("TARGET_PRICE_STRIPS") or ["NT$", "TWD", "上看", "下看", "元"])],
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


def _target_price_v0119(crx, *texts) -> float | None:
    """目標價:剝詞(NT$/TWD/上看/元)→ 主式(同義字冊關鍵詞)→ MASTER 防禦式第二道。"""
    for t in texts:
        for s in crx["tp_strips"]:
            t = t.replace(s, "")
        m = crx["tp"].search(t)
        if m:
            return float(m.group(1).replace(",", ""))
    for t in texts:
        m = crx["tp_defense"].search(t)
        if m:
            n = re.search(r"[\d,]+(?:\.\d+)?", m.group(0))
            if n:
                return float(n.group(0).replace(",", ""))
    return None


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


def first_page_zones(doc) -> dict:
    """首頁切兩區:本文區 vs 資訊區(左右皆可,關鍵詞密度定側;正典一、3)。"""
    page = doc[0]
    W = page.rect.width
    blocks = page.get_text("blocks")
    left = "\n".join(b[4] for b in blocks if b[0] <= W * 0.58)
    right = "\n".join(b[4] for b in blocks if b[0] > W * 0.58)
    lh = sum(left.count(k) for k in _INFO_KW)
    rh = sum(right.count(k) for k in _INFO_KW)
    side = "right" if rh >= lh else "left"
    info = right if side == "right" else left
    main = left if side == "right" else right
    return {"info_side": side, "info_text": info, "main_text": main,
            "info_kw_hits": max(rh, lh), "main_chars": len(main)}


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
    try:
        cands = _yf_ticker_v0119(code)["yfinance_ticker"].split("|")
        if len(cands) == 1:   # 已定盤仍留另市後備(實測紅:上櫃股 .TW 404)
            cands.append(cands[0].replace(".TWO", ".X").replace(".TW", ".TWO").replace(".X", ".TW"))
        adj = raw = tk = None
        for tk in cands:
            adj = yfinance.Ticker(tk).history(period="2y", auto_adjust=True)
            if adj is not None and not adj.empty:
                raw = yfinance.Ticker(tk).history(period="2y", auto_adjust=False)
                break
        if adj is None or adj.empty:
            return {"state": "NODATA", "why": f"{'/'.join(cands)} 皆無資料,不猜"}
        out = {"state": "OK", "ticker_used": tk,
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


def _fin_pages_v0119(doc) -> dict:
    """年度財務頁偵測:年份序列≥3 + 財務關鍵詞≥2 + 數字密度;回頁碼與樣本列,交 ENG400 表格梯。"""
    pages, sample = [], ""
    for i in range(1, min(len(doc), 30)):   # 首頁另路(first_page_zones),財報頁從第 2 頁起(實測紅:p1 誤入)
        t = doc[i].get_text()
        years = len(set(re.findall(r"(?<!\d)20[1-3]\d(?!\d)", t)))
        kws = sum(1 for k in _FIN_KW if k in t)
        nums = len(re.findall(r"\d+\.\d+", t))
        if years >= 3 and kws >= 2 and nums >= 8:
            pages.append(i + 1)
            if not sample:
                for ln in t.splitlines():
                    if any(k in ln for k in ("EPS", "每股盈餘")) and re.search(r"\d+\.\d+", ln):
                        sample = ln.strip()[:120]
                        break
    return {"fin_pages": pages, "fin_sample": sample or None}


def _analyst_v0119(info: str) -> dict:
    """資訊區抽分析師(操作員三律 2026-10-05):① @ 前通常是 ANALYST 英文姓名 →
    analyst_name_en;② @ 後 domain 是 BROKER → analyst_broker(交互證);
    ③ ANALYST 姓名通常在 職稱/電話/郵箱 區塊上方 → 上一~二行優先。抽不到誠實 None。"""
    crx = _central_regex_v0119()
    em = crx["email"].search(info)
    tel = crx["tel"].search(info)
    lines = [ln.strip() for ln in info.splitlines()]
    name = title = title_std = None
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
                    or crx["name_mixed"].fullmatch(c) or crx["name_mixed2"].fullmatch(c)):
                name = c   # 姓名式驗證(中央冊 7 式):非姓名樣式不收
                break
    if name is None and title:   # 後備:職稱同行剝職稱
        for ln in lines:
            if title in ln:
                cand = re.sub(r"(?i)(分析師|研究員|協理|資深副總|Analyst|Research|[::])", " ", ln).strip()
                name = cand[:30] or None
                break
    name_en = broker_mail = None
    if name:   # 混合姓名拆欄:李明哲 (Michael Lee) / 王大明 David Wang
        mm = crx["name_mixed"].fullmatch(name) or crx["name_mixed2"].fullmatch(name)
        if mm:
            name, name_en = mm.group(1), mm.group(2)
    if em:
        local, _, dom = em.group(0).partition("@")
        if name_en is None and re.search(r"[A-Za-z]", local):   # 律①;數字信箱不是姓名;混合姓名已拆者優先
            name_en = " ".join(t.capitalize() for t in re.split(r"[._\-]+", local) if t) or None
        toks = dom.lower().split(".")
        for alias, target in PRIOR._broker_map().items():   # 律②:短別名要 token 全等,長別名子串
            if alias.isascii():
                a = alias.lower()
                if (len(a) <= 3 and a in toks) or (len(a) > 3 and a in dom.lower()):
                    broker_mail = target
                    break
    return {"analyst_name": name, "analyst_title": title, "analyst_title_std": title_std,
            "analyst_name_en": name_en, "analyst_broker": broker_mail,
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
    """財務頁切割(正典一、4):先左右切半,再各半依縱向空隙(>14pt)上下切成視覺元件。"""
    W = page.rect.width
    halves = {"left": [], "right": []}
    for b in page.get_text("blocks"):
        halves["left" if (b[0] + b[2]) / 2 <= W / 2 else "right"].append(b)
    out = {}
    for side, bs in halves.items():
        bs.sort(key=lambda b: b[1])
        comps = []
        for b in bs:
            if comps and b[1] - comps[-1]["bbox"][3] <= 14:
                c = comps[-1]
                c["bbox"] = [min(c["bbox"][0], b[0]), min(c["bbox"][1], b[1]),
                             max(c["bbox"][2], b[2]), max(c["bbox"][3], b[3])]
                c["text"] += "\n" + b[4]
            else:
                comps.append({"bbox": [round(b[0], 1), round(b[1], 1), round(b[2], 1), round(b[3], 1)],
                              "text": b[4]})
        out[side] = comps
    return out


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
        try:
            z = first_page_zones(doc)
            sm, si = _repair_stats_v0119(z["main_text"]), _repair_stats_v0119(z["info_text"])
            p1 = fin_page_zones(doc[0])   # 首頁也切元件供分類(只擷取第一頁+財報頁)
            info_comps = p1["right" if z["info_side"] == "right" else "left"]
            main_comps = p1["left" if z["info_side"] == "right" else "right"]
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
                         "fin_pages": fin_desc or None, "fin_components": comp_n, "lamp": lamp})
        finally:
            doc.close()
    return {"verb": "layout_check", "manager": TAG, "workflow": "VRN-WKF009", "step": "STP003-005",
            "cleaned_prev": removed, "checked": len(rows), "rows": rows}


def deepread_one(path: Path) -> dict:
    """單檔深讀:檔名律 → 開 PDF → 兩區 → 抽欄 → 互證燈語。全部誠實,不硬配。"""
    fn = PRIOR.parse_filename(path.stem)
    row = {"filename": path.name, "ext": path.suffix.lower(),
           "size_bytes": path.stat().st_size if path.exists() else None,
           "fn_date": fn["report_date"], "fn_codes": fn["codes"], "broker": fn["broker_std"]}
    if path.suffix.lower() != ".pdf":
        row.update({"state": "NON_PDF_SKIP", "lamp": "黃", "next": "docx/txt 另路(不假裝讀過)"})
        return row
    doc, why = _open_pdf_v0119(path)
    if doc is None:
        row.update({"state": "UNREADABLE", "lamp": "紅", "why": why})
        return row
    try:
        z = first_page_zones(doc)
        crx = _central_regex_v0119()
        info, whole = z["info_text"], z["info_text"] + "\n" + z["main_text"]
        c_date = _content_date_v0119(crx, whole)
        tt = crx["tt_in_text"].search(whole)
        c_code = tt.group(1) if tt else (fn["codes"][0] if fn["codes"] else None)
        c_broker = None
        low = whole.lower()
        for alias, target in PRIOR._broker_map().items():
            if (alias.isascii() and re.search(r"(?<![A-Za-z])" + re.escape(alias) + r"(?![A-Za-z])", low)) \
               or (not alias.isascii() and alias in low):
                c_broker = target
                break
        rt = crx["rating"].search(info) or crx["rating"].search(whole)
        tpv = _target_price_v0119(crx, info, whole)
        code = c_code or (fn["codes"][0] if fn["codes"] else None)
        row.update({"state": "DEEPREAD", "info_side": z["info_side"],
                    "content_date": c_date, "content_code": c_code, "content_broker": c_broker,
                    "date_match": "MATCH" if (c_date and c_date == fn["report_date"]) else
                                  ("MISS" if c_date and fn["report_date"] else "ONE_SIDE"),
                    "ticker_match": "MATCH" if (c_code and fn["codes"] and c_code in fn["codes"]) else
                                    ("MISS" if c_code and fn["codes"] else "ONE_SIDE"),
                    "broker_match": "MATCH" if (c_broker and c_broker == fn["broker_std"]) else
                                    ("MISS" if c_broker and fn["broker_std"] else "ONE_SIDE"),
                    "rating": rt.group(1) if rt else None, "target_price": tpv,
                    "bloomberg_ticker": f"{code} TT" if code else None})
        if code:
            row.update(_yf_ticker_v0119(code))
            row["external_price"] = _adj_close_v0119(code, fn["report_date"] or c_date, tpv)
        row.update(_analyst_v0119(info))
        vm = sorted({std for std, al in crx["val_methods"].items() for a in al
                     if (a in whole if not a.isascii() else re.search("(?i)" + _wordish_v0119(a), whole))})
        row["valuation_methods"] = vm or None   # 估值法字典 × 資訊區+本文區核對
        row.update(_fin_pages_v0119(doc))
        hits = [row["date_match"], row["ticker_match"], row["broker_match"]].count("MATCH")
        row["lamp"] = "綠" if hits == 3 and tpv else ("黃" if hits else "紅")
    finally:
        doc.close()
    return row


def deepread(path: str) -> dict:
    """深讀動詞:檔或夾;只深讀有代號的個股檔(STOCK REPORT ONLY),其餘列 SKIP 一行誠實。"""
    removed = _fresh_outputs_v0119("deepread")   # 清場律:先刪前次結果
    p = Path(path)
    files = sorted([q for q in p.rglob("*") if q.suffix.lower() in PRIOR._DOC_EXTS]) if p.is_dir() else [p]
    rows, skipped = [], 0
    for q in files:
        if PRIOR.parse_filename(q.stem)["codes"]:
            rows.append(deepread_one(q))
        else:
            skipped += 1
    return {"verb": "deepread", "manager": TAG, "workflow": "VRN-WKF009", "step": "STP002-004",
            "cleaned_prev": removed, "total_files": len(files), "stock_reports": len(rows),
            "non_stock_skipped": skipped, "rows": rows}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    as_json = "--json" in args
    a = [x for x in args if x != "--json"]
    if a[:1] == ["layout-check"]:
        if len(a) < 2:
            print("[拒跑] layout-check <檔|夾>")
            return 2
        out = layout_check(a[1])
        PRIOR.emit_matrix_html("layout_check", out)
        print(json.dumps(out, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0
    if a[:1] == ["deepread"]:
        if len(a) < 2:
            print("[拒跑] deepread <檔|夾>")
            return 2
        out = deepread(a[1])
        PRIOR.emit_matrix_html("deepread", out)
        print(json.dumps(out, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0
    return PRIOR.main(args)   # intake/eps-check/reconcile/closeout 照前版鏈


def _mk_pdf_v0119(path: Path):
    """自測合成 PDF(標明 SYNTHETIC):左本文 + 右資訊區 + 第二頁年度財務;實開實讀不造假判。"""
    import fitz
    doc = fitz.open()
    pg = doc.new_page(width=595, height=842)
    pg.insert_textbox(fitz.Rect(36, 60, 330, 700),
                      "SYNTHETIC SAMPLE 台積電法說會後更新。本文區:先進製程需求強勁,"
                      "AI 動能延續。我們上修 2026 年預估,評價採本益比法並以 DCF 交叉驗證。\n" * 6,
                      fontname="china-t", fontsize=10)
    pg.insert_textbox(fitz.Rect(360, 60, 560, 700),
                      "2330 TT\n評等:買進\n目標價:NT$ 850\n收盤價:712\n"
                      "王小明\n分析師\nTel: 02-2345-6789\nwang.xm@brokerx.tw\n2025/08/19",
                      fontname="china-t", fontsize=10)
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
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 帶加速器橋 · VIA_FROM_VCGC 閘 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body
        and "VIA_FROM_VCGC" in body)
    for k in ("VIA_NO_NET", "VIA_NO_OPEN", "VIA_VRN_UI_DIR"):
        os.environ.pop(k, None)
    print("[計] VRN_SystemManager_v0119 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
