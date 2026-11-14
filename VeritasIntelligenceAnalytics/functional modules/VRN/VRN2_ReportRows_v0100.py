#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN2_ReportRows v0100 — VRN-2 報告擷取 · 還原 · 重點摘要 · 一行一單位輸出(個股 / 產業 / 主題)。

操作員 2026-11-10:「VRN-2 為主,缺乏的功能 VRN-1 整併進來 · 使股票報告及多種非股票報告皆能擷取還原資料抓重要資料摘要 ·
個股報告是一行一報告 · 產業報告是一行一產業 · 其他一行一主題 · 多行一報告 · 輸出調整優化」。

輸出律(一行 = 一個單位;一份報告可多行):
  個股報告  一行一報告    代號 · 名稱 · 評等 · 目標價 · 收盤價 · 四點摘要(評價與目標 / 核心驅動 / 營運與財務 / 風險與展望)
  產業報告  一行一產業    產業名(封面 / 檔名 / 章節標題命中產業詞)· 該產業的重點句 · 關鍵數字 · 提到的個股
  其他報告  一行一主題    主題 = 投影片每頁標題(連續同標題合併;目錄 / 封面 / 分隔頁 / 免責不算)或晨會「公司名稱」段 ·
                          該主題的重點句 · 關鍵數字 · 提到的個股
擷取還原:pdfplumber 逐頁抽字 + 去疊字(粗體假字「誠誠信信」)+ 收合字距(「債 券 E T F」)+ 去每頁重複的頁首字;沒字的掃描頁照實標
  NEEDS_OCR(容器沒有 OCR;桌機走 VRN-2 自己的 OCR 橋)。
摘要律:**只抽原句、不改寫**(extractive);每句都回原文比對,對得到才算 verified —— 不憑空生字。
分類律沿用 VRN-2 自己的車道判準(VRN_ReportLaneCheck v0100 → VRN_SystemManager v0231 的 _SK_EXCL 與檔名代號律),不另造一套。
VRN-1 整併(只讀來源,邏輯照搬不 import):tonykuni/VIA-VDF-VRN `attachments/VIA_Financial_Document_Summarizer_Engine_1.py`
  的 normalize_text · split_sentences · dedupe_sentences · sentence_score · RATING / TARGET / CURRENT / FINANCIAL / CATALYST / RISK
  規則與「四點」分類;VRN-1 倉一字不動(L123)。
邊界:只讀 PDF;只寫輸出夾(預設 VIA_Reports/vrn2/report_rows · 不進倉);零網路;不用 TA-Lib;不碰 VCGC。
用法:python VRN2_ReportRows_v0100.py run [--pdf-dir D] [--out O] · --selftest
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VRN2_ReportRows " + VERSION
HERE = Path(__file__).resolve().parent                  # functional modules/VRN(VRN-2 底座)
VIA = HERE.parent.parent
FIXTURE_REL = "functional modules/VRN/intake/VRN_v0108_Annual/VRN_v0108_Complete_Handover/pack/engine/fixtures/REAL_TEST_INPUT"
KIND_ZH = {"stock": "個股", "industry": "產業", "topic": "主題"}

# ---- VRN-1 整併(attachments/VIA_Financial_Document_Summarizer_Engine_1.py · 邏輯照搬)----
MAX_SENT = 320
RATING_RE = re.compile(r"(?:評等|Rating|投資評等)?\s*[：:]?\s*(買進|增加持股|增持|中立|持有|減持|賣出|區間操作|逢低買進|未評等|"
                       r"\bBuy\b|\bOutperform\b|\bOverweight\b|\bNeutral\b|\bHold\b|\bUnderperform\b|\bUnderweight\b|\bSell\b)", re.I)
TARGET_RE = re.compile(r"(?:目標價|合理價|推估價|Price\s*Target|Target\s*Price|TP)\s*(?:\([^)]{0,12}\))?\s*(?:為|上看|調升至|調降至|：|:)?\s*"
                       r"(?:\(NT\$\)|NT\$|TWD|新台幣|US\$)?\s*(?P<value>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?![\d,])", re.I)
CURRENT_RE = re.compile(r"(?:目前股價|現價|收盤價|前日收盤價|Shr\s*price,\s*close\s*\([^)]*\)|(?<!\w)Price\s*\([^)]*\))\s*(?:[A-Za-z]+\s*\d{1,2})?\s*[：:]?\s*(?:\(NT\$\)|NT\$|TWD)?\s*[：:]?\s*"
                        r"(?P<value>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?![\d,])", re.I)
FINANCIAL_RE = re.compile(r"營收|毛利率|營益率|淨利|EPS|每股盈餘|資本支出|CAPEX|revenue|margin|earnings", re.I)
CATALYST_RE = re.compile(r"催化劑|法說會|量產|出貨|漲價|調升|上修|下修|新產品|訂單|產能|市佔|成長|受惠|需求|demand|growth|ramp", re.I)
RISK_RE = re.compile(r"風險|下行|不確定|庫存|匯率|地緣政治|疲弱|遞延|競爭|承壓|Risk|downside", re.I)
VALUE_RE = re.compile(r"目標價|評等|本益比|股價淨值比|P/?E|PBR|DCF|上漲空間|潛在漲幅|維持|調升|調降|Target|valuation", re.I)
DISCLAIMER_RE = re.compile(r"免責|Disclaimer|重要聲明|請詳閱|copyright|版權所有|本報告僅供|本刊所刊載|分析師聲明|Analyst Certification|"
                           r"Important disclosures|投資人應|不得轉載|僅供參考|恕不負擔|法律責任|自行考量投資", re.I)


def normalize_text(text) -> str:
    v = "" if text is None else str(text)
    v = unicodedata.normalize("NFKC", v).replace("­", "").replace("​", "")
    v = v.replace("\r\n", "\n").replace("\r", "\n")
    v = re.sub(r"(?<=\w)-\n(?=\w)", "", v)
    v = re.sub(r"[ \t\f\v]+", " ", v)
    v = re.sub(r" *\n *", "\n", v)
    return re.sub(r"\n{3,}", "\n\n", v).strip()


def split_sentences(text: str) -> list:
    parts = re.split(r"(?<=[。！？!?；;])\s*|(?<=[a-z0-9%)][.])\s+(?=[A-Z])|\n+", normalize_text(text))
    return [p.strip(" *•-\t➢⚫●▪■◆") for p in parts if len(p.strip()) >= 2]


def dedupe_sentences(sentences) -> list:
    seen, out = set(), []
    for s in sentences:
        k = re.sub(r"\W+", "", s).lower()
        if k and k not in seen:
            seen.add(k)
            out.append(s)
    return out


def sentence_score(s: str, keywords, pattern=None) -> float:
    score = 2.5 if (pattern is not None and pattern.search(s)) else 0.0
    score += sum(0.35 for k in keywords if k and k.lower() in s.lower())
    score += min(len(re.findall(r"\d+(?:\.\d+)?%?", s)), 4) * 0.45
    score += 0.5 if 18 <= len(s) <= MAX_SENT else 0
    return score
# ---- VRN-1 整併 END ----


INDUSTRY_VOCAB = ("航太", "國防", "無人機", "半導體設備", "半導體", "晶圓代工", "ASIC", "IC設計", "AI伺服器", "伺服器", "AI", "散熱", "記憶體",
                  "PCB", "ABF", "CPO", "矽光子", "網通", "光通訊", "被動元件", "面板", "光學", "手機", "PC", "電動車", "汽車", "機器人",
                  "航運", "貨櫃", "散裝", "金融", "銀行", "壽險", "證券", "生技", "醫療", "製藥", "食品", "零售", "觀光", "營建", "鋼鐵",
                  "塑化", "紡織", "水泥", "電信", "綠能", "太陽能", "風電", "儲能", "重電", "衛星", "低軌衛星", "電池", "能源", "原物料")
SKIP_TITLE_RE = re.compile(r"簡報大綱|^大綱$|目\s*錄|目次|免責|Disclaimer|重要聲明|附錄|Appendix|分析師聲明|Analyst Certification|"
                           r"報告單位|報\s*告\s*人|聯絡資訊|^\d+$", re.I)
NOISE_LINE_RE = re.compile(r"^\d{1,2}號字$|【AI魔法小咒語】|根據以上內容幫我|^XX$|^[\W_]{1,3}$")   # 投影片模板殘字(字級 / 提示詞)
PROMPT_RESIDUE_RE = re.compile(r"\d{1,2}號字|【AI魔法小咒語】|根據以上內容幫我|歸納「『台股』的|近期概要、類股表現?|現、重點事件、未|重點事件未來展望|來一周展望」|"
                               r"改表達方式,讓他|看起來更直觀")         # 投影片模板留下的提示詞(中信周報模板實錄)
SOURCE_LINE_RE = re.compile(r"^\s*(?:資料來源|Source|註\s*[:：]|\*?註\d?[:：]|研究員[:：])", re.I)
COMPANY_SEG_RE = re.compile(r"公司名稱\s*([^\s()（）]{1,12}[（(][A-Z0-9 ]{2,8}[)）])")
TICKER_MENTION_RE = re.compile(r"([一-鿿A-Za-z\-]{2,10})\s*[（(](\d{4}[A-Z]?)(?:\s*(?:TT|TW|\.TW|\.TWO))?[)）]|(?<!\d)(\d{4})\s?([一-鿿]{2,4})(?=[，、：:\s])")
KEYNUM_RE = re.compile(r"[^\s，。；;：:、|]{0,14}?[-+]?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|％|億元|億|兆|萬張|萬|元|美元|bps|ppts?|倍|YoY|QoQ)"
                       r"[^\s，。；;|]{0,6}")
KEYFIG_RE = re.compile(r"(?P<lab>[一-鿿]{2,8}|[A-Za-z][A-Za-z/&-]{1,12}(?: [A-Za-z/&-]{2,12}){0,2})?\s*[:：]?\s*(?:為|達|至|約)?\s*"
                       r"(?P<v>[-+]?\d+(?:,\d{3})*(?:\.\d+)?)\s*(?P<u>%|％|億美元|億元|億|兆|萬張|萬|元|美元|bps|ppts?|倍|bn|mn)(?![A-Za-z])")
BROKERS = (("兆豐", "兆豐投顧"), ("台新", "台新投顧"), ("CTBC", "中信投顧"), ("中信", "中信投顧"), ("凱基", "凱基投顧"), ("JP-", "J.P. Morgan"),
           ("MS-", "Morgan Stanley"), ("CLST-", "CLSA"), ("MQ-", "Macquarie"), ("元大", "元大投顧"), ("富邦", "富邦投顧"), ("國泰", "國泰投顧"))


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lane_module():
    p = HERE / "VRN_ReportLaneCheck_v0100.py"
    spec = importlib.util.spec_from_file_location("vrn2_lane_for_rows", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def clean_line(s: str) -> str:
    s = normalize_text(s).replace("\n", " ").strip()
    toks = s.split(" ")
    if re.fullmatch(r"(?:\S ){2,}\S", s) or (len(toks) >= 6 and sum(len(t) == 1 for t in toks) >= 0.6 * len(toks)
                                               and sum(1 for t in toks if re.fullmatch(r"[一-鿿]", t)) >= 3):
        s = s.replace(" ", "")                                # 「債 券 E T F 周 報」·「目標價 3 00 . 0 0 元」字距 → 收合
    s = re.sub(r"(?<=[一-鿿]) (?=[一-鿿])", "", s)
    s = re.sub(r"(?<![\d.,])\d{1,2}(?: (?:\.?\d{1,2}|\.)){2,}(?![\d.,])",
               lambda m: m.group(0).replace(" ", "") if "." in m.group(0) else m.group(0), s)   # 價格字距「1 9 .2 0」→「19.20」
    s = re.sub(r"^([一-鿿])\1([一-鿿])\2", r"\1\2", s)   # 粗體疊字殘留(去疊字後仍有的話)
    s = re.sub(r"^\d{1,2}號字\s*", "", s)                     # 模板字級提示「7號字 …」
    return s.strip(" ➢•⚫●▪■◆*-")


def page_lines(text: str) -> list:
    out = []
    for x in (text or "").split("\n"):
        c = clean_line(PROMPT_RESIDUE_RE.sub("", x))
        if c and not NOISE_LINE_RE.search(c):
            out.append(("• " + c) if re.match(r"\s*[➢•⚫●▪■◆]", x) else c)   # 條列記號留成「• 」,還原段落時當新項開頭
    return out


def _proseish(ln: str) -> bool:
    t = re.sub(r"\s+", "", ln)
    if not t:
        return False
    dig = len(re.findall(r"\d", t))
    return dig / len(t) < 0.4 and (len(re.findall(r"[一-鿿]", t)) >= 4 or len(re.findall(r"[A-Za-z]", t)) >= 15)


ITEM_START_RE = re.compile(r"^(?:• |\(\d+\)|（\d+）|\d+[.、](?!\d)|[一二三四五六七八九十]+、|[A-Z][.、)] )")


def restore_lines(lines: list, stop=frozenset()) -> list:
    """還原段落:PDF 換行切斷的句子接回(前行沒句尾 · 兩行都是文字行 · 下一行不是條列開頭)。只動空白,不動字。"""
    out = []
    for ln in lines:
        prev = out[-1] if out else ""
        heading = (len(prev) <= 14 and prev[-1:] not in ",，、(（-") or prev in stop or ln in stop   # 短行 / 多頁重複的章節標 = 標題,不接
        tail = len(ln) <= 16 and bool(re.search(r"[。！？]$", ln))       # 「空間 59%。」這種句尾殘行
        if (out and not heading and _proseish(prev) and (_proseish(ln) or tail) and prev[-1] not in "。！？!?；;:：" and not ITEM_START_RE.match(ln)
                and not SOURCE_LINE_RE.match(ln) and "⚫" not in prev and "⚫" not in ln):
            sep = " " if re.search(r"[A-Za-z0-9,.)%]$", out[-1]) and re.match(r"[A-Za-z0-9(]", ln) else ""
            out[-1] = out[-1] + sep + ln
        else:
            out.append(ln)
    return out


def is_prose(s: str) -> bool:
    """可當摘要的句子:有足夠文字 · 數字不過多 · 不是資料來源 / 註 / 電話。表格列另放 data_rows。"""
    t = re.sub(r"\s+", "", s)
    if len(t) < 10 or SOURCE_LINE_RE.match(s) or re.search(r"\(\d{3}\)\s?\d{4}-\d{4}|\+886|@\w", s):
        return False
    if len(re.findall(r"\d", t)) / len(t) > 0.35:
        return False
    punct = bool(re.search(r"[,，。;；:：、]", s))
    cjk, lat = len(re.findall(r"[一-鿿]", t)), len(re.findall(r"[A-Za-z]", t))
    if cjk >= 6:
        return punct or cjk >= 30                                # 表頭(無標點的詞串)不當句子
    toks = s.split()
    low = sum(1 for w in toks if re.fullmatch(r"[a-z][a-z'’-]+[,.;:]?", w))
    return lat >= 20 and len(toks) >= (6 if punct else 10) and low >= 0.5 * len(toks)


def data_rows(lines: list, k=3) -> list:
    """表格頁的前 k 列資料(有標籤 + 至少兩個數字;不是散文、不是來源)。"""
    out = []
    for ln in lines:
        if is_prose(ln) or SOURCE_LINE_RE.match(ln) or DISCLAIMER_RE.search(ln):
            continue
        if len(re.findall(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?", ln)) >= 2 and re.search(r"[一-鿿]{2,}|[A-Za-z]{3,}", ln) and len(ln) >= 8:
            out.append(ln)
        if len(out) >= k:
            break
    return out


def _gutter(pg):
    """兩欄版面(側欄 + 內文)找垂直空白縫:縫寬 ≥ 8pt · 兩邊各 ≥ 15 字詞 · 兩邊都有三成以上文字詞(數字表不切)。找到回 x。"""
    try:
        words = pg.extract_words()
    except Exception:  # noqa: BLE001
        return None
    if len(words) < 40 or float(pg.width) > float(pg.height):    # 橫式 = 投影片,不切欄
        return None
    H = float(pg.height)
    words = [w for w in words if w["top"] > 0.1 * H and w["bottom"] < 0.92 * H] or words   # 頁首 / 頁尾橫跨不算
    step, bins = 2.0, int(float(pg.width) // 2.0) + 1
    cov = [0] * bins
    for w in words:
        for b in range(int(w["x0"] // step), min(bins - 1, int(w["x1"] // step)) + 1):
            cov[b] += 1
    lo, hi, best, i = int(bins * 0.15), int(bins * 0.8), None, int(bins * 0.15)
    while i < hi:
        if cov[i] == 0:
            j = i
            while j < hi and cov[j] == 0:
                j += 1
            if (j - i) * step >= 8:
                L = [w["text"] for w in words if w["x1"] <= i * step]
                R = [w["text"] for w in words if w["x0"] >= j * step]
                wordy = lambda ws: sum(1 for t in ws if re.search(r"[一-鿿]|[A-Za-z]{2,}", t)) / max(1, len(ws))  # noqa: E731
                if len(L) >= 15 and len(R) >= 15 and wordy(L) >= 0.3 and wordy(R) >= 0.3 and (best is None or j - i > best[1] - best[0]):
                    best = (i, j)
            i = j
        i += 1
    return None if best is None else (best[0] + best[1]) * step / 2


def read_pdf(path: Path) -> list:
    """逐頁 → [{page, lines, text}];pdfplumber 去疊字;失敗退 pypdf。"""
    pages = []
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            for i, pg in enumerate(pdf.pages):
                try:
                    pg = pg.dedupe_chars()
                except Exception:  # noqa: BLE001 — 舊版沒有 dedupe_chars
                    pass
                x = _gutter(pg)
                if x:                                           # 兩欄:左欄、右欄分開抽,不讓側欄插進內文句子
                    t = "\n".join((pg.crop((0, 0, x, pg.height)).extract_text() or "", pg.crop((x, 0, pg.width, pg.height)).extract_text() or ""))
                else:
                    t = pg.extract_text() or ""
                pages.append({"page": i + 1, "text": t, "columns": 2 if x else 1, "flat": (pg.extract_text() or "") if x else ""})
    except Exception:  # noqa: BLE001
        try:
            from pypdf import PdfReader
            for i, pg in enumerate(PdfReader(str(path)).pages):
                pages.append({"page": i + 1, "text": pg.extract_text() or ""})
        except Exception:  # noqa: BLE001
            return []
    for p in pages:
        p["lines"] = page_lines(p["text"])
    return pages


def strip_repeating_headers(pages: list) -> list:
    """每頁都出現的頁首字(過半頁)不當主題。"""
    cnt, anywhere = Counter(), Counter()
    for p in pages:
        for ln in set(p["lines"][:3]):
            cnt[ln] += 1
        for ln in set(p["lines"]):
            if len(ln) <= 20:
                anywhere[ln] += 1
    n = max(1, sum(1 for p in pages if p["lines"]))
    rep = {k for k, v in cnt.items() if v >= max(3, n * 0.5)} | {k for k, v in anywhere.items() if n >= 8 and v >= max(4, n * 0.6)}
    for p in pages:
        p["body_lines"] = [ln for ln in p["lines"] if ln not in rep]
    return pages


def meta_from_name(name: str, cover: str) -> dict:
    broker = next((b for k, b in BROKERS if k in name), "")
    d = re.search(r"(20\d{2})[./-]?(\d{2})[./-]?(\d{2})", name) or re.search(r"(20\d{2})[./年]\s?(\d{1,2})[./月]\s?(\d{1,2})", cover)
    if not d:
        m6 = re.search(r"CTBC(\d{2})(\d{2})(\d{2})", name)
        date = "20%s-%s-%s" % m6.groups() if m6 else ""
    else:
        date = "%s-%02d-%02d" % (d.group(1), int(d.group(2)), int(d.group(3)))
    return {"broker": broker, "date": date}


def report_kind(name: str, cover: str, lane: dict) -> str:
    if lane.get("lane") == "stock":
        return "stock"
    if re.search(r"產業|Industry|Sector", name + " " + cover, re.I) and not re.search(r"晨會|早報|盤勢|周報|週報", name):
        return "industry"
    return "topic"


def pick(sentences, pattern, keywords, used=()) -> str:
    best, bs = "", 0.0
    for s in sentences:
        if s in used or not is_prose(s):
            continue
        if pattern.search(s) and not DISCLAIMER_RE.search(s):
            sc = sentence_score(s, keywords, pattern)
            if sc > bs:
                best, bs = s, sc
    return best


def top_sentences(text: str, keywords, k=3, must=None) -> list:
    sents = [s for s in dedupe_sentences(split_sentences(text)) if 12 <= len(s) <= MAX_SENT and not DISCLAIMER_RE.search(s) and is_prose(s)]
    if must:
        sents = [s for s in sents if must.lower() in s.lower()] or sents
    near, uniq = set(), []
    for x in sents:                                              # 同一句換個空白 / 斷點再出現一次 → 只留一句
        nk = re.sub(r"\W+", "", x)[:28]
        if nk not in near:
            near.add(nk)
            uniq.append(x)
    sents = uniq
    order = {s: i for i, s in enumerate(sents)}
    ranked = sorted(sents, key=lambda s: (-sentence_score(s, keywords, CATALYST_RE), order[s]))[:k]
    return sorted(ranked, key=lambda s: order[s])                # 依原文順序呈現


def key_numbers(text: str, k=6) -> list:
    """關鍵數字 = 「標籤 數值單位」(例:營收 22.58億元 · 毛利率 23.3% · EPS 6.07元);沒有標籤的裸數字不列。"""
    out = []
    for m in KEYFIG_RE.finditer(normalize_text(text).replace("\n", " ")):
        lab = re.sub(r"^[為及之在將約已至由與和對較並但而的月]+", "", (m.group("lab") or "").strip())
        if len(lab) < 2 or (re.match(r"[A-Za-z]", lab) and not re.search(
                r"(?i)revenue|sales|margin|\bGM\b|\bOPM\b|EPS|profit|growth|upside|downside|target|ROE|P/?E|capex|dividend|yield|share", lab)):
            continue                                             # 英文標籤只收財務詞(避免「which is 17%」)
        v = "%s %s%s" % (lab, m.group("v"), m.group("u"))
        if v not in out:
            out.append(v)
        if len(out) >= k:
            break
    return out


def tickers_in(text: str) -> list:
    out = []
    for m in TICKER_MENTION_RE.finditer(normalize_text(text)):
        v = ("%s(%s)" % (m.group(1), m.group(2))) if m.group(2) else ("%s(%s)" % (m.group(4), m.group(3)))
        v = re.sub(r"^(?:公司名稱|股名|個股|推薦|續推|新增|多單|空單)", "", v)
        if v not in out and not re.match(r"20\d\d", v.split("(")[-1]):
            out.append(v)
    return out[:12]


def _section_label(body: list) -> str:
    parts = [ln for ln in body if not re.fullmatch(r"[\d\W]+", ln) and not SKIP_TITLE_RE.search(ln)]
    lab = " ".join(parts).strip(" |")
    return lab.split("|")[-1].strip() if "|" in lab else lab


def topic_segments(pages: list, stop=frozenset()) -> list:
    """主題段:晨會「公司名稱」段優先;否則投影片每頁標題(連續同標題合併 · 分隔頁當章節 · 同標題多處出現 → 加子標 / 章節)。"""
    texts = ["\n".join(restore_lines(p.get("lines") or [], stop)) for p in pages]
    whole = "\n".join(texts)
    comps = list(COMPANY_SEG_RE.finditer(whole))
    if len(comps) >= 2:
        segs = []
        for i, m in enumerate(comps):
            end = comps[i + 1].start() if i + 1 < len(comps) else len(whole)
            seg = whole[m.start():end]
            key = re.sub(r"\s+", "", m.group(1))
            pg = [p["page"] for p, t in zip(pages, texts) if key in re.sub(r"\s+", "", t)]
            pg = [x for x in pg if x != pages[0]["page"]] or pg      # 封面目錄提到不算
            segs.append({"topic": m.group(1), "text": seg, "lines": seg.split("\n"), "pages": pg, "company": True})
        return segs
    raw, section = [], ""
    for p in pages[1:] if len(pages) > 1 else pages:            # 第 1 頁是封面
        body = p.get("body_lines") or []
        if not body:
            continue
        if not any(is_prose(x) for x in restore_lines(body)) and sum(map(len, body)) < 40:
            section = _section_label(body) or section            # 分隔頁 → 章節名
            continue
        if len(body) < 2 or sum(map(len, body[1:])) < 12 or sum(len(x) <= 2 for x in body) > 0.6 * len(body):
            continue                                            # 只有標題、沒有內文 / 圖表軸字散落頁
        title = next((ln for ln in body if 2 <= len(ln) <= 40 and not re.fullmatch(r"[\d\W]+", ln) and not SOURCE_LINE_RE.match(ln)
                      and (len(re.findall(r"[一-鿿]", ln)) >= 2 or len(re.findall(r"[A-Za-z]", ln)) >= 3)), "")
        if not title or SKIP_TITLE_RE.search(title) or DISCLAIMER_RE.search(title):
            continue
        title = re.sub(r"\s*\d+\s*$", "", title)
        i = body.index(title) if title in body else 0
        rest = body[i + 1:]
        sub = rest[0] if rest and 2 <= len(rest[0]) <= 10 and not re.search(r"[\d()（）]", rest[0]) else ""
        raw.append({"title": title, "sub": sub, "section": section, "body": rest, "page": p["page"]})
    cnt = Counter(r["title"] for r in raw)
    segs = []
    for r in raw:
        topic = r["title"]
        if cnt[topic] > 1 and (r["sub"] or r["section"]):
            topic = "%s · %s" % (topic, r["sub"] or r["section"])
        if segs and segs[-1]["topic"] == topic:
            segs[-1]["lines"] += r["body"]
            segs[-1]["pages"].append(r["page"])
        else:
            segs.append({"topic": topic, "lines": list(r["body"]), "pages": [r["page"]], "section": r["section"]})
    for sg in segs:
        sg["text"] = "\n".join(restore_lines(sg["lines"], stop))
    return segs


def industries_of(name: str, cover: str, pages: list) -> list:
    hay = name + " " + cover
    found = []
    for w in INDUSTRY_VOCAB:
        if w in hay and not any(w in f and w != f for f in found):
            found.append(w)
    found = [w for w in found if not any(w != o and w in o for o in found)]
    if not found:
        t = next((ln for ln in cover.split(" | ") if 2 <= len(ln) <= 20 and not re.search(r"\d{4}|產業專題", ln)), "")
        found = [t or "產業"]
    return found


def build_rows(name: str, pages: list, lane: dict) -> list:
    pages = strip_repeating_headers(pages)
    seen_on = Counter(ln for p in pages for ln in set(p.get("lines") or []) if len(ln) >= 6)
    stop = frozenset(ln for ln, c in seen_on.items() if c >= 3)                 # 多頁重複的章節標(投影片每頁的段標)
    for p in pages:
        p["rtext"] = "\n".join(restore_lines(p.get("lines") or [], stop))   # 還原文字(去字距 / 疊字 / 模板殘字 · 段落接行)
    cover = " | ".join((pages[0]["lines"] if pages else [])[:8])
    whole = "\n".join(p["rtext"] for p in pages)
    meta = meta_from_name(name, cover)
    rid = hashlib.sha256(name.encode("utf-8")).hexdigest()[:8]
    base = {"report_id": rid, "file": name, "broker": meta["broker"], "date": meta["date"], "pages_total": len(pages)}
    if not "".join(p["text"] for p in pages).strip():
        return [dict(base, kind="unknown", kind_zh="—", row_no=1, row_key="", title="", summary=[], data_rows=[], key_numbers=[], tickers=[], pages=[],
                     status="NEEDS_OCR", note="PDF 沒有可抽的文字層(掃描檔);容器沒有 OCR → 桌機走 VRN-2 OCR 橋")]
    kind = report_kind(name, cover, lane)
    rows = []
    if kind == "stock":
        sents = [s for s in dedupe_sentences(split_sentences(whole)) if 8 <= len(s) <= MAX_SENT]
        head = "\n".join("\n".join(restore_lines(page_lines(p.get("flat") or p["text"]))) for p in pages[:2])   # 側欄標籤 / 值同列:用整頁原排
        rating = (RATING_RE.search(head) or RATING_RE.search(whole))
        tp = TARGET_RE.search(head) or TARGET_RE.search(whole)
        cp = CURRENT_RE.search(head)
        kw = [lane.get("ticker", "")]
        four, used = [], set()
        for lb, pat in (("評價與目標", VALUE_RE), ("核心驅動", CATALYST_RE), ("營運與財務", FINANCIAL_RE), ("風險與展望", RISK_RE)):
            x = pick(sents, pat, kw, used)
            used.add(x)
            four.append((lb, x))
        rows.append(dict(base, kind="stock", row_no=1, row_key=lane.get("ticker", ""), title=_title(pages),
                         ticker=lane.get("ticker", ""), rating=rating.group(1) if rating else "", target_price=(tp.group("value").replace(",", "") if tp else ""),
                         close_price=(cp.group("value").replace(",", "") if cp else ""),
                         summary=[x for _, x in four if x], summary_labels=[lb for lb, x in four if x], data_rows=[],
                         key_numbers=key_numbers(head), tickers=tickers_in(head), pages=[p["page"] for p in pages if p["text"].strip()]))
    elif kind == "industry":
        inds = industries_of(name, cover, pages)
        txt = "\n".join(p["rtext"] for p in pages[1:]) or whole
        taken = set()
        for i, ind in enumerate(inds, 1):
            summ = top_sentences(txt, [ind], k=6, must=ind if len(inds) > 1 else None)
            summ = ([x for x in summ if x not in taken] or summ)[:3]       # 別的產業行用過的句子不重複
            taken.update(summ)
            rel = [p["page"] for p in pages if ind in p["rtext"]]
            rows.append(dict(base, kind="industry", row_no=i, row_key=ind, title=_title(pages), summary=summ, data_rows=[],
                             key_numbers=key_numbers("\n".join(summ) or txt), tickers=tickers_in(txt), pages=rel))
    else:
        segs = topic_segments(pages, stop)
        if not segs:
            segs = [{"topic": _title(pages) or "全文", "text": whole, "lines": whole.split("\n"), "pages": [p["page"] for p in pages]}]
        for i, sg in enumerate(segs, 1):
            summ = top_sentences(sg["text"], re.findall(r"[一-鿿A-Za-z0-9]{2,}", sg["topic"])[:4], k=3)
            row = dict(base, kind="topic", row_no=i, row_key=sg["topic"], title=_title(pages), summary=summ,
                       data_rows=data_rows(sg["lines"]) if len(summ) < 2 else [],
                       key_numbers=key_numbers(sg["text"]), tickers=tickers_in(sg["text"]), pages=sg["pages"])
            if sg.get("company"):                                # 晨會一家公司一行:評等 / 目標價也抓
                rt, tp = RATING_RE.search(sg["text"]), TARGET_RE.search(sg["text"])
                row.update(ticker=(re.search(r"[（(]([A-Z0-9 ]{2,8})[)）]", sg["topic"]) or [None, ""])[1].strip(),
                           rating=rt.group(1) if rt else "", target_price=tp.group("value").replace(",", "") if tp else "")
            rows.append(row)
    for r in rows:
        r.setdefault("kind_zh", KIND_ZH.get(r["kind"], r["kind"]))
        r["lane_why"] = lane.get("why", "")
        verify_row(r, whole)
    return rows


def _title(pages: list) -> str:
    ln = [x for x in (pages[0]["lines"] if pages else []) if 4 <= len(x) <= 60 and not DISCLAIMER_RE.search(x)]
    return " · ".join(ln[:3])


def verify_row(r: dict, source_text: str) -> None:
    """抽取式摘要必須回得到原文:每句 / 每列去空白後是還原原文(去空白)的子字串才算。"""
    src = re.sub(r"\s+", "", normalize_text(source_text))
    items = list(r.get("summary", [])) + list(r.get("data_rows", []))
    ok = [bool(s) and re.sub(r"\s+", "", normalize_text(s)) in src for s in items]
    r["verified_sentences"] = sum(ok)
    r["summary_sentences"] = len(ok)
    r.setdefault("status", "VERIFIED" if ok and all(ok) else ("EMPTY" if not ok else "MISMATCH"))


def run(pdf_dir: Path, out: Path) -> dict:
    lane_m = lane_module()
    excl, excl_src = lane_m.load_excl(HERE)
    rows, files = [], sorted(p for p in Path(pdf_dir).glob("*.pdf"))
    for f in files:
        pages = read_pdf(f)
        cover = " ".join((pages[0]["text"] if pages else "")[:400].split())
        lane = lane_m.classify(f.name, excl, cover)
        rows.extend(build_rows(f.name, pages, lane))
    summary = {"engine": ENGINE, "at": _now(), "pdf_dir": str(pdf_dir), "classifier": excl_src, "reports": len(files), "rows": len(rows),
               "by_kind": dict(Counter(r["kind"] for r in rows)), "reports_by_kind": dict(Counter(k for k in {r["file"]: r["kind"] for r in rows}.values())),
               "status": dict(Counter(r["status"] for r in rows)),
               "sentences": {"verified": sum(r.get("verified_sentences", 0) for r in rows), "total": sum(r.get("summary_sentences", 0) for r in rows)}}
    v, t = summary["sentences"]["verified"], summary["sentences"]["total"]
    summary["lamp"] = "GREEN" if t and v == t and not summary["status"].get("MISMATCH") and not summary["status"].get("NEEDS_OCR") else ("YELLOW" if t and v == t else "RED")
    write_outputs(rows, summary, out)
    return summary


def write_outputs(rows: list, summary: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "VRN2_ReportRows_latest.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    cols = ["report_id", "file", "broker", "date", "kind_zh", "row_no", "row_key", "ticker", "rating", "target_price", "close_price",
            "summary", "data_rows", "key_numbers", "tickers", "pages", "status", "verified_sentences", "summary_sentences"]
    with (out / "VRN2_ReportRows_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([" ｜ ".join(r.get(c) or []) if isinstance(r.get(c), list) and c != "pages" else
                        (",".join(map(str, r.get(c) or [])) if c == "pages" else r.get(c, "")) for c in cols])
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        tbl = pa.table({c: [json.dumps(r.get(c), ensure_ascii=False) if isinstance(r.get(c), list) else ("" if r.get(c) is None else str(r.get(c)))
                            for r in rows] for c in cols})
        pq.write_table(tbl, out / "VRN2_ReportRows_latest.parquet")
        summary["parquet"] = True
    except Exception:  # noqa: BLE001 — 沒 pyarrow 就只出 json / csv / html
        summary["parquet"] = False
    (out / "VRN2_ReportRows_latest.html").write_text(render_html(rows, summary), encoding="utf-8")


def _pages_str(pg: list) -> str:
    """[1,2,3,5,6] → 1–3, 5–6"""
    out, run = [], []
    for x in sorted(set(int(v) for v in pg)):
        if run and x == run[-1] + 1:
            run.append(x)
        else:
            if run:
                out.append(str(run[0]) if len(run) == 1 else "%d–%d" % (run[0], run[-1]))
            run = [x]
    if run:
        out.append(str(run[0]) if len(run) == 1 else "%d–%d" % (run[0], run[-1]))
    return ", ".join(out)


def render_html(rows: list, s: dict) -> str:
    e = html.escape
    lamp = {"GREEN": "#1f8a4c", "YELLOW": "#a87400", "RED": "#c62828"}.get(s["lamp"], "#777")
    body = []
    for f in sorted({r["file"] for r in rows}):
        rs = [r for r in rows if r["file"] == f]
        r0 = rs[0]
        trs = "".join("<tr><td class=n>%d</td><td><b>%s</b>%s</td><td><ul>%s</ul></td><td>%s</td><td>%s</td><td class=n>%s</td><td>%s</td></tr>" % (
            r["row_no"], e(r.get("row_key") or "—"),
            ("<div class=m>%s %s · TP %s%s</div>" % (e(r.get("ticker", "")), e(r.get("rating", "")), e(r.get("target_price", "") or "—"),
                                                    (" · 收 " + e(r.get("close_price") or "—")) if r["kind"] == "stock" else "")) if (r["kind"] == "stock" or r.get("rating") or r.get("target_price")) else "",
            ("".join("<li>%s%s</li>" % (("<span class=lb>%s</span>" % e(lb)) if lb else "", e(x)) for x, lb in zip(r.get("summary", []), (r.get("summary_labels") or [""] * 9)))
             + "".join("<li class=dr><span class=lb>表</span>%s</li>" % e(x) for x in r.get("data_rows", []))) or "<li class=m>%s</li>" % e(r.get("note", "—")),
            e(" · ".join(r.get("key_numbers", [])[:6])), e(" · ".join(r.get("tickers", [])[:8])), e(_pages_str(r.get("pages", []))),
            e("%s %s/%s" % (r["status"], r.get("verified_sentences", 0), r.get("summary_sentences", 0)))) for r in rs)
        body.append("<section><h2>%s <span class=k>%s · %d 行</span></h2><p class=m>%s · %s · %s</p><div class=w><table><colgroup><col style='width:3%%'><col style='width:13%%'><col style='width:46%%'><col style='width:16%%'><col style='width:10%%'><col style='width:5%%'><col style='width:7%%'></colgroup><thead><tr><th>#</th><th>單位</th><th>重點(原句)</th><th>關鍵數字</th><th>提到的個股</th><th>頁</th><th>驗證</th></tr></thead><tbody>%s</tbody></table></div></section>" % (
            e(f), e(r0.get("kind_zh", "")), len(rs), e(r0.get("broker") or "—"), e(r0.get("date") or "—"), e(r0.get("lane_why", "")), trs))
    return ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>VRN-2 報告一行一單位</title>"
            "<style>body{font:14px/1.55 system-ui,'Noto Sans TC',sans-serif;margin:0;background:#f5f6f4;color:#1b2420}main{max-width:1200px;margin:0 auto;padding:16px}"
            "section{background:#fff;border:1px solid #d9dfdb;border-radius:10px;padding:12px 14px;margin:12px 0}h1{font-size:1.3rem}h2{font-size:1rem;margin:0}"
            ".k{color:#3b5f8a;font-weight:600}.m{color:#5d6862;font-size:.85rem}.w{overflow-x:auto}table{border-collapse:collapse;width:100%%;min-width:900px}"
            "th,td{text-align:left;vertical-align:top;padding:6px;border-bottom:1px solid #e3e8e5}th{font-size:.75rem;color:#5d6862;white-space:nowrap}table{table-layout:fixed}ul{margin:0;padding-left:1.1em}"
            ".n{font-variant-numeric:tabular-nums}.lb{display:inline-block;background:#eef3f1;border-radius:4px;padding:0 4px;margin-right:4px;font-size:.75rem}"
            ".dr{font:12px/1.5 ui-monospace,monospace;color:#33403a}"
            ".lp{color:#fff;border-radius:999px;padding:1px 10px;background:%s}</style><main><h1>VRN-2 報告擷取 · 一行一單位 <span class=lp>%s</span></h1>"
            "<p class=m>%s · 報告 %d · 行 %d · %s · 摘要原句驗證 %d/%d · 個股一行一報告 · 產業一行一產業 · 其他一行一主題</p>%s</main>") % (
        lamp, e(s["lamp"]), e(s["at"]), s["reports"], s["rows"], e(json.dumps(s["by_kind"], ensure_ascii=False)), s["sentences"]["verified"], s["sentences"]["total"], "".join(body))


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)
    print("[%s selftest]" % ENGINE, flush=True)

    def pg(i, t):
        return {"page": i, "text": t, "lines": page_lines(t)}
    stock = [pg(1, "個股報告\n2025/12/06\n晶心科 (6533 TT) 中立(Neutral)\n前日收盤價 270.00 元\n目 標 價 3 00 . 0 0 元\n受部分案件遞延影響,3Q25 營收略低於預期。"),
             pg(2, "3Q25 營收為 4.7 億元(YoY+8.8%),毛利率維持高檔。\n公司仍維持每年營收成長 30%的長期目標,歐美市場出貨可望上修。\n主要風險為案件遞延與競爭加劇。")]
    r = build_rows("晶心科(6533,N,中立)-CTBC251208.pdf", stock, {"lane": "stock", "ticker": "6533", "why": "代號 6533"})
    chk("① 個股報告 = 一行一報告:代號 · 評等 · TP · 收盤 · 四點全由原句", len(r) == 1 and r[0]["ticker"] == "6533" and r[0]["target_price"] == "300.00"
        and r[0]["close_price"] == "270.00" and r[0]["rating"] in ("中立", "Neutral") and r[0]["status"] == "VERIFIED" and len(r[0]["summary"]) >= 3, r[0].get("summary_labels"))
    ind = [pg(1, "產業專題\n半導體與散熱\n2026年9月16日"),
           pg(2, "半導體\n半導體設備需求於 2026 年成長 15%,晶圓代工產能利用率提升。\n先進封裝帶動半導體設備訂單上修。"),
           pg(3, "散熱\n散熱水冷滲透率將由 10% 提升至 35%,奇鋐(3017)受惠。\n散熱模組報價上漲 5%。")]
    r = build_rows("兆豐產業專題-半導體與散熱.pdf", ind, {"lane": "non_stock", "why": "排除字"})
    chk("② 產業報告 = 一行一產業(兩個產業 → 兩行 · 句子各自含該產業)", [x["row_key"] for x in r] == ["半導體", "散熱"] and all(x["kind"] == "industry" for x in r)
        and all(x["row_key"] in " ".join(x["summary"]) for x in r) and any("奇鋐(3017)" in x["tickers"] for x in r), [x["row_key"] for x in r])
    topic = [pg(1, "誠信 承諾\n台股盤勢分析"), pg(2, "誠信 承諾\n簡報大綱\n一、國際股市 二、台股盤勢"),
             pg(3, "誠信 承諾\n國際股市\n本週關注聯準會12月例會,美股四大指數上漲 1.2%。\n費半指數創新高,AI 需求延續。"),
             pg(4, "誠信 承諾\n國際股市\n美債殖利率回落至 4.1%,資金回流科技股。"),
             pg(5, "誠信 承諾\n焦點族群\n散熱:水冷成為標配,長期成長可期,3017奇鋐 營收年增 35%。"),
             pg(6, "誠信 承諾\n免責聲明\n本報告僅供參考")]
    r = build_rows("20251208_台新台股盤勢分析.pdf", topic, {"lane": "non_stock", "why": "排除字"})
    chk("③ 其他報告 = 一行一主題:重複頁首不算 · 大綱 / 免責跳過 · 連續同標題合併", [x["row_key"] for x in r] == ["國際股市", "焦點族群"] and r[0]["pages"] == [3, 4]
        and all(x["status"] == "VERIFIED" for x in r), [(x["row_key"], x["pages"]) for x in r])
    morn = [pg(1, "晨會報告\n目錄"), pg(2, "晨會報告\n公司名稱 振大環球(4441)\n振大環球營收年增 12%,新產能下半年開出。\n公司名稱 美時(1795)\n美時新藥授權收入成長 20%,維持區間操作。")]
    r = build_rows("20251205兆豐晨會報告(二)-公司訪談摘要.pdf", morn, {"lane": "non_stock", "why": "排除字「晨會」"})
    chk("④ 晨會:一家公司一主題 → 多行一報告 · 每行帶頁碼 / 評等 / 目標價", [x["row_key"] for x in r] == ["振大環球(4441)", "美時(1795)"]
        and r[0]["pages"] == [2] and r[0]["ticker"] == "4441", [(x["row_key"], x["pages"], x.get("rating"), x.get("target_price")) for x in r])
    r = build_rows("MQ-1560 20260520.pdf", [pg(1, ""), pg(2, "")], {"lane": "stock", "ticker": "1560"})
    chk("⑤ 掃描檔沒文字層 → NEEDS_OCR 照實(不假摘要)", r[0]["status"] == "NEEDS_OCR" and not r[0]["summary"])
    row = {"summary": ["這句不在原文裡,營收成長 99%。"]}
    verify_row(row, "原文只有這一句:營收成長 10%。")
    m1, m2 = TARGET_RE.search("Price Target (Dec-25):NT$1275.0"), CURRENT_RE.search("Price (17 Jul 25):NT$1130.0 · Shr price, close (Dec 3, 2025) NT$3,190.00")
    chk("⑤b 數字不截斷:「NT$1275.0」= 1275.0(不是 127)· 英文收盤價「Price (17 Jul 25):NT$1130.0」", m1 and m1.group("value") == "1275.0" and m2 and m2.group("value") == "1130.0",
        (m1 and m1.group("value"), m2 and m2.group("value")))
    chk("⑥ 驗證:摘要句不在原文 = MISMATCH(抽取式 · 不生字)", row["status"] == "MISMATCH" and row["verified_sentences"] == 0)
    chk("⑦ 還原:去字距「債 券 E T F 周 報」· 數字字距「目 標 價 3 00 . 0 0 元」· 模板殘字「7號字」· 斷行接回", clean_line("債 券 E T F 周 報") == "債券ETF周報"
        and clean_line("目 標 價 3 00 . 0 0 元") == "目標價300.00元" and page_lines("7號字 【AI魔法小咒語】\n8號字\n市場焦點") == ["市場焦點"]
        and restore_lines(["受部分案件遞延影響,3Q25 營收略低於", "預期,前三季累計營收 10.2 億元。", "(2) 預估 4Q25 營收持平。"]) ==
        ["受部分案件遞延影響,3Q25 營收略低於預期,前三季累計營收 10.2 億元。", "(2) 預估 4Q25 營收持平。"])
    bond = [pg(1, "債券ETF周報\n2026/9/11"),
            pg(2, "1\n債券 ETF 市場概況\n6"),
            pg(3, "債券ETF|報酬排名\n不含槓反 (單周前20名)\n1 00710B 復華彭博非投等債 1.22 2.3 3.4 8.0\n2 00953B 群益優選非投等債 1.06 2.8 3.5 8.8\n資料來源:CMoney,2026/9/11。"),
            pg(4, "附錄\n依組別分類 | 公債\n22"),
            pg(5, "債券ETF|報酬排名\n美國公債\n1 00864B 中信美國公債0-1 0.88 1.5 3.1 8.0\n2 00865B 國泰US短期公債 0.87 1.6 3.1 8.2")]
    r = build_rows("【中信｜債券ETF周報】測試_CTBC260915.pdf", bond, {"lane": "non_stock", "why": "排除字"})
    chk("⑦b 同標題多處出現 → 加子標 / 章節區分 · 表格頁抓前幾列資料(不當摘要句)· 資料來源不算",
        [x["row_key"] for x in r] == ["債券ETF|報酬排名 · 債券 ETF 市場概況", "債券ETF|報酬排名 · 美國公債"]
        and r[1]["data_rows"][0].startswith("1 00864B") and not any("資料來源" in d for x in r for d in x["data_rows"]) and all(x["status"] == "VERIFIED" for x in r),
        [(x["row_key"], x["data_rows"][:1]) for x in r])
    with tempfile.TemporaryDirectory() as td:
        rows = build_rows("晶心科(6533,N,中立)-CTBC251208.pdf", stock, {"lane": "stock", "ticker": "6533"})
        s = {"engine": ENGINE, "at": _now(), "reports": 1, "rows": 1, "by_kind": {"stock": 1}, "lamp": "GREEN", "sentences": {"verified": 1, "total": 1}}
        write_outputs(rows, s, Path(td))
        chk("⑧ 輸出 json / csv / html(有 pyarrow 再加 parquet)", all((Path(td) / ("VRN2_ReportRows_latest." + x)).is_file() for x in ("json", "csv", "html")))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 不用 TA-Lib · 不 import VCGC · 零網路", not re.search(r"^\s*(?:import|from)\s+(talib|CGC_|requests|urllib)", src, re.M | re.I))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=ENGINE)
    ap.add_argument("verb", nargs="?", default="run", choices=["run", "selftest"])
    ap.add_argument("--pdf-dir", default=str(VIA / FIXTURE_REL))
    ap.add_argument("--out", default=str(VIA / "VIA_Reports" / "vrn2" / "report_rows"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    s = run(Path(a.pdf_dir), Path(a.out))
    print("[%s] %s · 報告 %d · 行 %d · %s · 摘要原句驗證 %d/%d · 狀態 %s → %s" % (
        s["lamp"], ENGINE, s["reports"], s["rows"], json.dumps(s["by_kind"], ensure_ascii=False), s["sentences"]["verified"], s["sentences"]["total"],
        json.dumps(s["status"], ensure_ascii=False), Path(a.out) / "VRN2_ReportRows_latest.html"), flush=True)
    return 0 if s["lamp"] != "RED" else 2


if __name__ == "__main__":
    sys.exit(main())
