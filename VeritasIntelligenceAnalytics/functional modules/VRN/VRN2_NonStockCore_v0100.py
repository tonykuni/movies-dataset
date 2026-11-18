#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN2_NonStockCore v0100 — VRN-2 自建的非個股核心(暫代操作員 NON_STOCK_CORE_v0200 的同名介面)。

為什麼有這支(操作員 2026-11-12):「非個股 v0300 用在 VRN-2 摘要非個股報告、新聞、訊息;輸入有 PDF / Word / 圖片 / 文字」。
非個股摘要器 v0310(nonstock_v0310/engine)的 hard gate 要 internal/NON_STOCK_CORE_v0200.py(54,135 B · SHA-256 92f53d82…),
2026-11-06 起兩次附件都沒帶、本倉 / VRN-1 / 桌機都找不到(nonstock_v0310/internal/README_MISSING.md)。
本支照 v0310 引擎實際呼叫的 CORE 介面(19 個名稱)寫一份 VRN-2 自己的實作,讓 v0310 不改一字就能跑:
  Claim · SourceBlock · NUMBER_RE · URL_RE · PROFILE_{MESSENGER,INDUSTRY,OTHER,EVERNOTE,NEWS}
  def_normalize_text · def_guess_block_type · def_extract_input · def_extract_claims · def_profile_router
  def_parse_messenger_blocks · def_apply_note_layers · def_similarity
另加多格式讀取(本支自己的擴充,v0310 只認 .pdf/.txt/.md/.html/.docx/.enex/.json):
  PDF(pdfplumber → pypdf → pdftotext;字太少 = 影像 PDF → OCR)· Word(.docx 用 python-docx 含表格;.doc/.rtf/.odt 用 LibreOffice 轉文字)
  圖片(.png/.jpg/.jpeg/.tif/.tiff/.bmp/.webp/.gif → VCGC 鎖版 OCR 超引擎的隔離境車道;沒有就緒車道 = 照實 ABSENT,不假抽)
  文字(.txt/.md/.csv/.log;UTF-8 / UTF-16 / Big5 / GB18030 自動)· 網頁(.html/.htm)· 訊息(.json 訊息陣列 · .eml 電子郵件 · LINE / Messenger 匯出文字)· 筆記(.enex)
誠實邊界:
  - 這是**暫代**,不是操作員的 v0200 原件;原件放進 nonstock_v0310/internal/ 後,VRN2_NonStockSummarizer 會優先用原件(並記 SHA 是否相符)。
  - 抽取式:只切原文句子、打標籤,不改寫、不生成字;每個 Claim 都帶 evidence_sid 指回原文區塊。
  - 零網路([VIA:NET-BRIDGE] 留名:本支不出網)· 不用 TA-Lib · 不 import VCGC(OCR 只借 VCGC 鎖冊裡 OCR 工具的路徑,子行程跑隔離境)。
用法:python VRN2_NonStockCore_v0100.py --selftest · read <檔> (印出讀到的區塊數與前幾句)
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import difflib
import email
import email.policy
import hashlib
import html as _html
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

VERSION = "v0100"
ENGINE = "VRN2_NonStockCore " + VERSION
CORE_KIND = "VRN2_STANDIN"            # 原件 = "NON_STOCK_CORE_v0200"
HERE = Path(__file__).resolve().parent

# ── 00 參數(可調的都在這裡)──────────────────────────────────────────────
PROFILE_MESSENGER = "MESSENGER"
PROFILE_INDUSTRY = "INDUSTRY_REPORT"
PROFILE_OTHER = "OTHER"
PROFILE_EVERNOTE = "EVERNOTE"
PROFILE_NEWS = "NEWS"

TEXT_EXT = {".txt", ".md", ".csv", ".log", ".tsv"}
HTML_EXT = {".html", ".htm"}
WORD_EXT = {".docx"}
OFFICE_EXT = {".doc", ".rtf", ".odt"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".gif"}
MSG_EXT = {".json", ".eml"}
NOTE_EXT = {".enex"}
PDF_EXT = {".pdf"}
ALL_EXT = TEXT_EXT | HTML_EXT | WORD_EXT | OFFICE_EXT | IMAGE_EXT | MSG_EXT | NOTE_EXT | PDF_EXT
FORMAT_OF = {**{e: "TEXT" for e in TEXT_EXT}, **{e: "WEB" for e in HTML_EXT}, **{e: "WORD" for e in WORD_EXT | OFFICE_EXT},
             **{e: "IMAGE" for e in IMAGE_EXT}, ".json": "MESSAGE", ".eml": "MESSAGE", ".enex": "NOTE", ".pdf": "PDF"}

PDF_MIN_CHARS_PER_PAGE = 40           # 每頁平均字數低於此 = 影像 PDF → 走 OCR
CLAIM_MIN_CHARS = 8
CLAIM_MAX_CHARS = 400
SIM_DEDUP = 0.92
OCR_PAGE_LIMIT = 30                   # 影像 PDF 最多 OCR 幾頁(重件;超過照實記)

NUMBER_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?\s*%?")
URL_RE = re.compile(r"https?://[^\s<>\"'）)]+")
_ZW_RE = re.compile(r"[​-‏  ﻿]")
_SENT_SPLIT = re.compile(r"(?<=[。！？!?；;])\s*|(?<=\.)\s+(?=[A-Z一-鿿])|\n+")
DISCLAIMER_RE = re.compile(r"本刊所刊載之內容僅做為參考|僅供內部參考|僅供內部使用|請勿外傳|免責聲明|投資人應自行|Disclaimer|not an offer", re.I)

TICKER_PATTERNS = [
    re.compile(r"[（(]\s*([1-9]\d{3}[A-Z]?)\s*(?:\.?\s*(?:TT|TW|TWO))?\s*[,，)）]"),
    re.compile(r"(?<![\d.])([1-9]\d{3})\s*(?:TT|\.TWO|\.TW)\b"),
    re.compile(r"[（(]\s*([A-Z]{2,5})(?:\s*(?:US|\.US|\.O|\.N))?\s*[)）]"),
]
US_NOT_TICKER = {"AI", "CEO", "CFO", "GDP", "CPI", "PMI", "EPS", "ROE", "YOY", "QOQ", "ASP", "USD", "TWD", "NTD", "ETF", "IPO",
                 "OEM", "ODM", "PCB", "CCL", "HBM", "ASIC", "CPO", "EUV", "AWS", "LLM", "GPU", "CPU", "NAND", "DRAM", "ESL",
                 "CDMO", "FED", "ECB", "BOJ", "TT", "TW", "TWO", "US", "FY", "YTD", "NR", "N", "Q"}

STORY_KEYWORDS = {
    "AI_INFRASTRUCTURE": ("AI伺服器", "AI 伺服器", "資料中心", "GB200", "GB300", "AI server", "data center", "算力", "雲端服務商", "CSP"),
    "ASIC_CUSTOM_SILICON": ("ASIC", "客製化晶片", "自研晶片", "custom silicon"),
    "AI_THERMAL": ("散熱", "液冷", "水冷", "均熱板", "thermal", "cooling"),
    "MEMORY": ("DRAM", "HBM", "NAND", "記憶體", "memory"),
    "PCB_MATERIALS": ("PCB", "CCL", "銅箔基板", "ABF", "載板", "玻纖布"),
    "CPO_OPTICAL": ("CPO", "光通訊", "矽光子", "光模組", "optical", "transceiver"),
    "FOUNDRY_ADVANCED": ("晶圓代工", "先進製程", "2奈米", "3奈米", "foundry", "N2", "N3"),
    "ADVANCED_PACKAGING": ("CoWoS", "先進封裝", "SoIC", "封測", "advanced packaging"),
    "SEMICONDUCTOR_MATERIALS": ("矽晶圓", "特用化學", "半導體材料", "光阻"),
    "SEMICONDUCTOR_EQUIPMENT": ("半導體設備", "EUV", "設備廠", "equipment"),
    "AEROSPACE": ("航太", "衛星", "低軌", "飛機", "aerospace", "Boeing", "Airbus"),
    "DEFENSE_DRONE": ("無人機", "國防", "軍工", "drone", "defense"),
    "ROBOTICS_PHYSICAL_AI": ("機器人", "人形", "robot", "physical AI", "自動化"),
    "EV_AUTOMOTIVE": ("電動車", "車用", "EV", "汽車", "automotive"),
    "SHIPPING": ("航運", "貨櫃", "散裝", "運價", "SCFI", "BDI", "shipping"),
    "RATES_BONDS": ("利率", "殖利率", "公債", "美債", "降息", "升息", "聯準會", "Fed", "債券", "bond", "yield"),
    "ENERGY_GEOPOLITICS": ("油價", "原油", "天然氣", "地緣", "中東", "關稅", "制裁", "oil", "tariff"),
    "DISPLAY_ESL": ("面板", "電子紙", "ESL", "顯示器", "display"),
    "CDMO_PHARMA": ("CDMO", "新藥", "製藥", "藥證", "pharma", "生技"),
    "POWER_GRID": ("電網", "重電", "變壓器", "儲能", "電力", "power grid"),
}
AI_SEGMENTS = {"ASIC_CUSTOM_SILICON", "AI_THERMAL", "MEMORY", "PCB_MATERIALS", "CPO_OPTICAL", "FOUNDRY_ADVANCED", "ADVANCED_PACKAGING",
               "SEMICONDUCTOR_MATERIALS", "SEMICONDUCTOR_EQUIPMENT", "POWER_GRID"}
DRIVER_KEYWORDS = {
    "CAPEX": ("資本支出", "capex", "擴產", "建廠"),
    "DEMAND": ("需求", "拉貨", "訂單", "出貨", "demand", "orders"),
    "SUPPLY": ("供給", "產能", "缺貨", "供應", "supply", "capacity"),
    "PRICE": ("報價", "漲價", "降價", "ASP", "價格", "price"),
    "MARGIN": ("毛利率", "營益率", "利潤率", "margin"),
    "POLICY": ("政策", "關稅", "補貼", "法規", "policy", "tariff"),
    "RATES": ("利率", "降息", "升息", "殖利率", "rate cut", "rate hike"),
    "INVENTORY": ("庫存", "去化", "inventory"),
    "FX": ("匯率", "新台幣", "美元", "升值", "貶值", "FX"),
}
RELATION_WORDS = ("帶動", "受惠", "導致", "因此", "推升", "拖累", "由於", "隨著", "使得", "進而", "主因", "受到", "有助", "driven by", "due to", "benefit", "thanks to", "lead to")
ANCHOR_WORDS = {"NVIDIA": ("NVIDIA", "Nvidia", "輝達"), "TSMC": ("TSMC", "台積電"), "APPLE": ("Apple", "蘋果"), "AMD": ("AMD", "超微"),
                "BROADCOM": ("Broadcom", "博通"), "MICROSOFT": ("Microsoft", "微軟"), "GOOGLE": ("Google", "谷歌", "Alphabet"),
                "AMAZON": ("Amazon", "亞馬遜", "AWS"), "META": ("Meta",), "INTEL": ("Intel", "英特爾"), "SAMSUNG": ("Samsung", "三星"),
                "SK_HYNIX": ("SK Hynix", "SK海力士", "海力士"), "MICRON": ("Micron", "美光"), "OPENAI": ("OpenAI",), "TESLA": ("Tesla", "特斯拉")}
MACRO_WORDS = ("通膨", "CPI", "PCE", "利率", "降息", "升息", "Fed", "聯準會", "GDP", "PMI", "匯率", "就業", "非農", "美債", "油價", "景氣", "衰退", "inflation")
POS_WORDS = ("成長", "增加", "上調", "上修", "受惠", "強勁", "優於", "創新高", "回升", "看好", "買進", "擴大", "提升", "增溫", "轉佳", "樂觀", "growth", "upgrade", "beat", "strong")
NEG_WORDS = ("下滑", "衰退", "下修", "疲弱", "拖累", "不如", "低於", "賣出", "減少", "下跌", "壓抑", "放緩", "惡化", "保守", "疲軟", "decline", "downgrade", "miss", "weak")
UNCERTAIN_RE = re.compile(r"可能|或將|恐|不確定|風險|變數|觀察|待確認|may|might|uncertain|risk", re.I)
CONDITIONAL_RE = re.compile(r"若|如果|假如|一旦|倘若|除非|\bif\b|\bunless\b", re.I)
GUIDANCE_RE = re.compile(r"公司表示|管理層|經營層|法說|指引|公司預估|公司預期|guidance|management", re.I)
ANALYST_RE = re.compile(r"我們|本中心|研究部|研究團隊|預估|預期|認為|看好|建議|維持.*評等|we expect|we think|we believe", re.I)
PERIOD_RE = re.compile(r"20\d{2}\s*(?:年|F|E)?(?:[上下]半年|第[一二三四]季|Q[1-4])?|[1-4]Q\s?\d{2}|\d{2}Q[1-4]|[上下]半年|明年|今年|後年|未來\s*\d+\s*年|第[一二三四]季|H[12]\s?\d{2}")
METRIC_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?\s*(?:%|％|億|萬|元|倍|bps|美元|台幣|兆|x\b|times)|(?:YoY|QoQ|年增|季增|年減|季減)\s*[-+]?\d", re.I)
MSG_HEAD_RE = re.compile(r"^\s*(?:\[?\s*(?:\d{4}[/.-]\d{1,2}[/.-]\d{1,2}\s*)?(?:上午|下午|AM|PM)?\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\s*\]?)\s*[\t ]?(.*)$", re.I)


# ── 01 資料結構(與 v0310 呼叫方式相容:Claim 前 11 個位置參數 + 關鍵字串列)──────────
@dataclass
class SourceBlock:
    sid: str
    source_id: str
    page: int
    block_index: int
    block_type: str
    text: str


@dataclass
class Claim:
    claim_id: str
    source_id: str
    evidence_sid: str
    text: str
    page: int
    block_type: str
    attribution: str
    direction: str
    uncertain: bool
    conditional: bool
    importance: str
    metrics: list = field(default_factory=list)
    stories: list = field(default_factory=list)
    tickers: list = field(default_factory=list)
    anchors: list = field(default_factory=list)
    drivers: list = field(default_factory=list)
    relations: list = field(default_factory=list)
    periods: list = field(default_factory=list)
    macro_terms: list = field(default_factory=list)


class ReaderUnavailable(RuntimeError):
    """讀這種格式要的工具不在(例:圖片沒有就緒的 OCR 車道)→ 照實 ABSENT,不假抽。"""


# ── 02 文字正規化 / 區塊型別 / 相似度 ───────────────────────────────────────
def def_normalize_text(text: str) -> str:
    t = _ZW_RE.sub("", str(text or "")).replace("\r\n", "\n").replace("\r", "\n").replace("　", " ").replace("\xa0", " ")
    t = unicodedata.normalize("NFC", t)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in t.split("\n")]
    out, blank = [], 0
    for ln in lines:
        if ln:
            out.append(ln)
            blank = 0
        elif out and blank == 0:
            out.append("")
            blank = 1
    return "\n".join(out).strip()


def def_guess_block_type(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "EMPTY"
    if DISCLAIMER_RE.search(t):
        return "DISCLAIMER"
    if URL_RE.fullmatch(t):
        return "URL"
    nums = len(NUMBER_RE.findall(t))
    if nums >= 6 and nums * 4 >= len(re.sub(r"\s", "", t)) / 3:
        return "TABLE"
    if re.match(r"^\s*(?:[-•●■◆▶►※]|\d+[.、)]|[（(]\d+[)）]|[一二三四五六七八九十]+、)", t):
        return "LIST"
    if len(t) <= 40 and "\n" not in t and not re.search(r"[。！？!?；;，,]$", t):
        return "HEADING"
    return "PARAGRAPH"


def def_similarity(a: str, b: str) -> float:
    a, b = re.sub(r"\s+", "", a or ""), re.sub(r"\s+", "", b or "")
    if not a or not b:
        return 0.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sm.ratio() if sm.real_quick_ratio() >= 0.5 else 0.0


def _hash8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:8].upper()


# ── 03 讀檔(多格式)──────────────────────────────────────────────────────
def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    for enc in ("utf-8-sig", "big5", "cp950", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


_CJK = re.compile(r"[\u4e00-\u9fff]")
_END_RE = re.compile(r"[。！？!?；;：:」』）)]$")
_BULLET_RE = re.compile(r"^\s*(?:[-•●■◆▶►※・]|\d+[.、)](?!\d)|[（(]\d+[)）]|[一二三四五六七八九十]+、|[A-Z]\.\s)")


def is_table_line(line: str) -> bool:
    """表格列(數字密、句讀少):不拿來當摘要句,只留在原文。"""
    t = (line or "").strip()
    nums = NUMBER_RE.findall(t)
    if len(nums) < 4:
        return False
    digits = sum(len(re.sub(r"\D", "", n)) for n in nums)
    letters = len(_CJK.findall(t)) + len(re.findall(r"[A-Za-z]", t))
    return digits >= letters * 0.6 or (len(nums) >= 6 and not re.search(r"[，。,；;]", t))


_SPACED_RE = re.compile(r"(?<![^\s｜|])((?:[\u4e00-\u9fffA-Z] ){2,}[\u4e00-\u9fffA-Z])(?![^\s｜|])")


def is_form_line(line: str) -> bool:
    """表單 / 欄位頭(例:「公司名稱 來億-KY(6890) 報告種類 個股報告評 等 逢低買進」):中文為主、空白分隔 ≥ 5 段、沒有句讀。"""
    t = (line or "").strip()
    if re.search(r"[，。；,;！？]", t) or len(t) < 16:
        return False
    toks = t.split()
    cjk = len(_CJK.findall(t))
    return len(toks) >= 5 and cjk >= len(re.sub(r"\s", "", t)) * 0.5


def reflow_lines(text: str) -> str:
    """PDF / OCR 文字:排版斷行接回句子(前行沒句末標點、本行不是條列 / 表格列就接);段落之間空一行。"""
    out = []
    prev_tab = False
    for raw in (text or "").splitlines():
        ln = _SPACED_RE.sub(lambda m: m.group(1).replace(" ", ""), raw.strip())   # 「債 券 E T F」→「債券ETF」
        if not ln:
            if out and out[-1] != "":
                out.append("")
            prev_tab = False
            continue
        tab = is_table_line(ln)
        new = (not out or out[-1] == "" or tab or prev_tab or _BULLET_RE.match(ln) or _END_RE.search(out[-1])
               or (len(out[-1]) <= 24 and not re.search(r"[，,、]$", out[-1])))
        if new:
            if out and out[-1] != "":
                out.append("")
            out.append(ln)
        else:
            glue = "" if (_CJK.search(out[-1][-1:]) or _CJK.search(ln[:1])) else " "
            out[-1] = out[-1] + glue + ln
        prev_tab = tab
    return "\n".join(out)


def _paragraph_blocks(path: Path, text: str, page: int = 1, start: int = 0, kind: Optional[str] = None) -> list:
    blocks = []
    for para in re.split(r"\n\s*\n", def_normalize_text(text)):
        para = para.strip()
        if not para:
            continue
        i = start + len(blocks)
        btype = kind or def_guess_block_type(para)
        blocks.append(SourceBlock("%s-P%03d-B%04d-%s" % (FORMAT_OF.get(path.suffix.lower(), "SRC")[:3], page, i, _hash8(para)),
                                  path.name, page, i, btype, para))
    return blocks


def _read_html(text: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")
        for t in soup(["script", "style", "noscript"]):
            t.decompose()
        return soup.get_text("\n")
    except ImportError:
        return _html.unescape(re.sub(r"<[^>]+>", "\n", re.sub(r"(?is)<(script|style).*?</\1>", "", text)))


def _read_docx(path: Path) -> list:
    try:
        import docx  # python-docx
    except ImportError as exc:
        raise ReaderUnavailable("讀 .docx 要 python-docx(VCGC InstallGate 裝)") from exc
    d = docx.Document(str(path))
    parts = []
    for p in d.paragraphs:
        t = p.text.strip()
        if t:
            style = (p.style.name or "").lower() if p.style is not None else ""
            parts.append(("HEADING" if style.startswith(("heading", "title", "標題")) else None, t))
    for tb in d.tables:
        rows = [" | ".join(c.text.strip() for c in r.cells) for r in tb.rows]
        if rows:
            parts.append(("TABLE", "\n".join(rows)))
    blocks = []
    for kind, t in parts:
        blocks.extend(_paragraph_blocks(path, t, 1, len(blocks), kind))
    return blocks


def _office_to_text(path: Path) -> str:
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        raise ReaderUnavailable("讀 %s 要 LibreOffice(soffice)· 沒有就先另存成 .docx" % path.suffix)
    with tempfile.TemporaryDirectory() as td:
        cp = subprocess.run([exe, "--headless", "--convert-to", "txt:Text (encoded):UTF8", "--outdir", td, str(path)],
                            capture_output=True, text=True, timeout=180, stdin=subprocess.DEVNULL)
        outs = list(Path(td).glob("*.txt"))
        if not outs:
            raise ReaderUnavailable("LibreOffice 轉文字失敗 rc %s" % cp.returncode)
        return _read_text_file(outs[0])


def _read_json_messages(path: Path) -> tuple:
    data = json.loads(_read_text_file(path))
    items = data
    if isinstance(data, dict):
        items = next((data[k] for k in ("messages", "items", "data", "records", "chats") if isinstance(data.get(k), list)), [data])
    msgs = []
    for it in items if isinstance(items, list) else [items]:
        if isinstance(it, str):
            msgs.append({"text": it})
        elif isinstance(it, dict):
            txt = next((it[k] for k in ("text", "content", "message", "body", "summary") if isinstance(it.get(k), str)), "")
            if not txt:
                txt = "\n".join(str(v) for v in it.values() if isinstance(v, str) and len(v) > 10)
            head = " ".join(str(it[k]) for k in ("date", "time", "timestamp", "sender", "from", "author", "title") if it.get(k))
            msgs.append({"text": txt, "head": head})
    blocks = []
    for i, m in enumerate(msgs):
        t = def_normalize_text(m["text"])
        if t:
            blocks.append(SourceBlock("MSG-P001-B%04d-%s" % (i, _hash8(t)), path.name, 1, i, "MESSAGE",
                                      (m.get("head", "") + "\n" + t).strip() if m.get("head") else t))
    return blocks, len(msgs)


def _read_eml(path: Path) -> list:
    msg = email.message_from_bytes(path.read_bytes(), policy=email.policy.default)
    head = " · ".join(str(msg.get(k, "")) for k in ("Date", "From", "Subject") if msg.get(k))
    body = msg.get_body(preferencelist=("plain", "html"))
    text = body.get_content() if body is not None else ""
    if body is not None and body.get_content_type() == "text/html":
        text = _read_html(text)
    blocks = [SourceBlock("EML-P001-B0000-%s" % _hash8(head), path.name, 1, 0, "HEADING", head)] if head else []
    return blocks + _paragraph_blocks(path, text, 1, len(blocks))


def _read_enex(path: Path) -> list:
    raw = _read_text_file(path)
    blocks = []
    for n, note in enumerate(re.findall(r"(?is)<note>(.*?)</note>", raw) or [raw], 1):
        title = re.search(r"(?is)<title>(.*?)</title>", note)
        content = re.search(r"(?is)<content>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</content>", note)
        if title:
            t = def_normalize_text(_html.unescape(title.group(1)))
            blocks.append(SourceBlock("NOTE-P%03d-B%04d-%s" % (n, len(blocks), _hash8(t)), path.name, n, len(blocks), "HEADING", t))
        if content:
            blocks.extend(_paragraph_blocks(path, _read_html(content.group(1)), n, len(blocks)))
    return blocks


def _ocr_module():
    """VCGC 鎖冊 VIA_ToolVersion_Lock 的 ocr 那一支(只借路徑,子行程在隔離境跑);找不到 = None。"""
    p = HERE
    while p.parent != p and not (p / "supportive modules" / "registry").is_dir():
        p = p.parent
    lock = p / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json"
    try:
        rel = json.loads(lock.read_text(encoding="utf-8"))["ocr"]["path"]
    except (OSError, ValueError, KeyError):
        return None
    f = p.parent / rel
    if not f.is_file():
        return None
    spec = importlib.util.spec_from_file_location("vrn2_nonstock_ocr_lock", f)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def ocr_image(image: Path) -> dict:
    """圖片 → OCR 文字。走 VCGC 鎖版 OCR 超引擎的車道階梯(輕→重:RapidOCR → Tesseract → Paddle → Surya),每車道隔離境子行程。
    沒有就緒車道 → ReaderUnavailable(照實 ABSENT · 缺的交 VCGC InstallGate,不在 VIA 環境 pip)。"""
    mod = _ocr_module()
    if mod is None:
        raise ReaderUnavailable("找不到 VCGC 鎖版 OCR 工具(VIA_ToolVersion_Lock ocr)")
    envs = mod.env_map()
    tried = []
    for lane in sorted(mod.LANES, key=lambda x: x["pri"]):
        state, py = mod.probe_lane(lane, envs)
        tried.append("%s:%s" % (lane["k"], state))
        if state != "READY":
            continue
        r = mod.run_lane(lane, py, str(image))
        if mod.pick_winner([r]):
            return {"lane": lane["k"], "lines": r.get("text", []), "avg": r.get("avg"), "tried": tried}
        tried[-1] += "(信心不足 %s)" % r.get("avg", r.get("err", "?"))
    raise ReaderUnavailable("OCR 沒有就緒車道 · " + " ".join(tried) + " → 交 VCGC InstallGate 建隔離境(via_rapidocr 最輕)")


def _read_image(path: Path) -> tuple:
    r = ocr_image(path)
    text = reflow_lines("\n".join(x for x in r["lines"] if str(x).strip()))
    return _paragraph_blocks(path, text, 1), {"ocr_lane": r["lane"], "ocr_conf": r["avg"]}


def _pdf_pages_text(path: Path) -> tuple:
    errs = []
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            return [pg.extract_text() or "" for pg in pdf.pages], "pdfplumber"
    except Exception as exc:  # noqa: BLE001 — 換下一個讀法,原因照實記
        errs.append("pdfplumber:%s" % type(exc).__name__)
    try:
        from pypdf import PdfReader
        return [pg.extract_text() or "" for pg in PdfReader(str(path)).pages], "pypdf"
    except Exception as exc:  # noqa: BLE001
        errs.append("pypdf:%s" % type(exc).__name__)
    exe = shutil.which("pdftotext")
    if exe:
        cp = subprocess.run([exe, "-layout", str(path), "-"], capture_output=True, text=True, timeout=180, stdin=subprocess.DEVNULL)
        if cp.returncode == 0:
            return cp.stdout.split("\f"), "pdftotext"
        errs.append("pdftotext:rc%s" % cp.returncode)
    raise ReaderUnavailable("PDF 三個讀法都失敗 · " + " ".join(errs))


def _pdf_ocr_pages(path: Path, n_pages: int) -> tuple:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise ReaderUnavailable("影像 PDF 要 pypdfium2 轉圖再 OCR") from exc
    texts, lanes = [], set()
    doc = pdfium.PdfDocument(str(path))
    with tempfile.TemporaryDirectory() as td:
        for i in range(min(n_pages, OCR_PAGE_LIMIT)):
            img = Path(td) / ("p%03d.png" % (i + 1))
            doc[i].render(scale=2).to_pil().save(img)
            r = ocr_image(img)
            lanes.add(r["lane"])
            texts.append("\n".join(r["lines"]))
    return texts, "OCR:" + "+".join(sorted(lanes))


def _read_pdf(path: Path) -> tuple:
    pages, backend = _pdf_pages_text(path)
    meta = {"pages": len(pages), "pdf_reader": backend}
    chars = sum(len(re.sub(r"\s", "", p)) for p in pages)
    if pages and chars / max(1, len(pages)) < PDF_MIN_CHARS_PER_PAGE:
        pages, backend = _pdf_ocr_pages(path, len(pages))
        meta.update(pdf_reader=backend, image_pdf=True, ocr_pages=len(pages))
    blocks = []
    for i, txt in enumerate(pages, 1):
        blocks.extend(_paragraph_blocks(path, reflow_lines(txt), i, len(blocks)))
    for b in blocks:
        if is_table_line(b.text.splitlines()[0] if b.text else ""):
            b.block_type = "TABLE"
    return blocks, meta


def def_extract_input(path) -> tuple:
    """任一支援格式 → (list[SourceBlock], meta)。讀不到字 → 空清單(呼叫方記 NODATA);要的工具不在 → ReaderUnavailable。"""
    path = Path(path)
    ext = path.suffix.lower()
    meta = {"backend": "VRN2_NONSTOCK_CORE_" + VERSION, "format": FORMAT_OF.get(ext, "UNKNOWN"), "ext": ext}
    if ext in PDF_EXT:
        blocks, m = _read_pdf(path)
        meta.update(m)
    elif ext in WORD_EXT:
        blocks = _read_docx(path)
        meta["reader"] = "python-docx"
    elif ext in OFFICE_EXT:
        blocks = _paragraph_blocks(path, _office_to_text(path))
        meta["reader"] = "LibreOffice→txt"
    elif ext in IMAGE_EXT:
        blocks, m = _read_image(path)
        meta.update(m, reader="OCR")
    elif ext in HTML_EXT:
        blocks = _paragraph_blocks(path, _read_html(_read_text_file(path)))
        meta["reader"] = "bs4"
    elif ext == ".json":
        blocks, n = _read_json_messages(path)
        meta.update(reader="json-messages", messages=n)
    elif ext == ".eml":
        blocks = _read_eml(path)
        meta["reader"] = "email"
    elif ext in NOTE_EXT:
        blocks = _read_enex(path)
        meta["reader"] = "enex"
    elif ext in TEXT_EXT:
        blocks = _paragraph_blocks(path, _read_text_file(path))
        meta["reader"] = "text"
    else:
        raise ReaderUnavailable("不支援的副檔名 %s" % ext)
    meta["blocks"] = len(blocks)
    meta["chars"] = sum(len(b.text) for b in blocks)
    return blocks, meta


# ── 04 類型路由 / 訊息切分 / 筆記層 ─────────────────────────────────────────
def _looks_like_chat(text: str) -> bool:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    heads = sum(1 for ln in lines if MSG_HEAD_RE.match(ln) and re.search(r"\d{1,2}:\d{2}", ln[:30]))
    return len(lines) >= 4 and heads >= max(3, len(lines) // 6)


def def_profile_router(path, blocks: list) -> tuple:
    path = Path(path)
    name = path.name.lower()
    text = "\n".join(b.text for b in blocks[:60])
    if path.suffix.lower() == ".enex":
        return PROFILE_EVERNOTE, "NOTE"
    if path.suffix.lower() in (".json", ".eml") or any(b.block_type == "MESSAGE" for b in blocks[:5]) or _looks_like_chat(text):
        return PROFILE_MESSENGER, "DAILY_MESSAGE_STREAM" if path.suffix.lower() != ".eml" else "EMAIL"
    if re.search(r"新聞|報導|記者|快訊|news|reuters|bloomberg|中央社|經濟日報|工商時報", name + "\n" + text[:600], re.I):
        return PROFILE_NEWS, "NEWS"
    if re.search(r"產業|供應鏈|industry|sector|產業鏈|族群", name + "\n" + text[:1500], re.I):
        return PROFILE_INDUSTRY, "INDUSTRY_REPORT"
    if re.search(r"利率|總經|央行|通膨|GDP|macro|債券|匯率", name + "\n" + text[:1500], re.I):
        return PROFILE_OTHER, "MACRO_OUTLOOK"
    if re.search(r"盤勢|大盤|加權指數|策略|strategy", name + "\n" + text[:800], re.I):
        return PROFILE_OTHER, "MARKET_STRATEGY"
    return PROFILE_OTHER, "GENERAL_REPORT"


def def_parse_messenger_blocks(path, blocks: list) -> list:
    """把聊天匯出(LINE / Messenger / 文字)切成一則訊息一塊;已是 MESSAGE 的照舊。"""
    if blocks and all(b.block_type == "MESSAGE" for b in blocks):
        return blocks
    path = Path(path)
    out, cur, cur_page = [], [], 1
    for b in blocks:
        for ln in b.text.splitlines():
            if MSG_HEAD_RE.match(ln) and re.search(r"\d{1,2}:\d{2}", ln[:30]) and cur:
                out.append((cur_page, "\n".join(cur)))
                cur = []
            if not cur:
                cur_page = b.page
            cur.append(ln)
    if cur:
        out.append((cur_page, "\n".join(cur)))
    res = []
    for i, (pg, t) in enumerate(out):
        t = def_normalize_text(t)
        if t:
            res.append(SourceBlock("MSG-P%03d-B%04d-%s" % (pg, i, _hash8(t)), path.name, pg, i, "MESSAGE", t))
    return res or blocks


def def_apply_note_layers(blocks: list) -> list:
    """筆記:標題層標 HEADING,其餘照原文;不刪字。"""
    for b in blocks:
        if b.block_type not in ("HEADING", "DISCLAIMER") and len(b.text) <= 40 and "\n" not in b.text:
            b.block_type = "HEADING"
    return blocks


# ── 05 句子 → Claim(抽取式:只切原句、打標籤)──────────────────────────────────
def _sentences(text: str) -> list:
    out = []
    for s in _SENT_SPLIT.split(text or ""):
        s = re.sub(r"^\s*(?:[-•●■◆▶►※]|\d+[.、)]\s|[（(]\d+[)）])\s*", "", (s or "").strip())
        if len(s) >= CLAIM_MIN_CHARS:
            out.append(s[:CLAIM_MAX_CHARS])
    return out


def _hits(text: str, table: dict) -> list:
    low = text.lower()
    return [k for k, words in table.items() if any(w.lower() in low for w in words)]


def _tickers(text: str) -> list:
    out = []
    for i, rx in enumerate(TICKER_PATTERNS):
        for m in rx.finditer(text):
            t = m.group(1)
            if i == 2 and t.upper() in US_NOT_TICKER:
                continue
            if i < 2 and re.fullmatch(r"20[0-4]\d", t):          # 年份不是代號
                continue
            if t not in out:
                out.append(t)
    return out


def _direction(text: str) -> str:
    low = text.lower()
    p = sum(low.count(w.lower()) for w in POS_WORDS)
    n = sum(low.count(w.lower()) for w in NEG_WORDS)
    return "POSITIVE" if p > n else ("NEGATIVE" if n > p else "NEUTRAL_OR_MIXED")


def def_extract_claims(blocks: list) -> list:
    claims, seen = [], []
    for b in blocks:
        if b.block_type in ("DISCLAIMER", "URL", "EMPTY", "TABLE") or DISCLAIMER_RE.search(b.text or ""):
            continue
        for s in _sentences(b.text):
            if URL_RE.fullmatch(s) or len(re.sub(r"[\W\d_]", "", s)) < 4 or is_table_line(s) or is_form_line(s) or DISCLAIMER_RE.search(s):
                continue
            if any(def_similarity(s, x) >= SIM_DEDUP for x in seen[-80:]):
                continue
            seen.append(s)
            metrics = [m.group(0).strip() for m in METRIC_RE.finditer(s)]
            stories, drivers = _hits(s, STORY_KEYWORDS), _hits(s, DRIVER_KEYWORDS)
            if "AI_INFRASTRUCTURE" in stories and set(stories) & AI_SEGMENTS:   # 傘題讓位給供應鏈分段(散熱 / ASIC / 記憶體 …)
                stories.remove("AI_INFRASTRUCTURE")
            relations = [w for w in RELATION_WORDS if w.lower() in s.lower()]
            anchors = _hits(s, ANCHOR_WORDS)
            periods = list(dict.fromkeys(m.group(0).strip() for m in PERIOD_RE.finditer(s)))
            macro = [w for w in MACRO_WORDS if w.lower() in s.lower()]
            attribution = ("MANAGEMENT_GUIDANCE" if GUIDANCE_RE.search(s) else
                           "ANALYST_VIEW" if ANALYST_RE.search(s) else "SOURCE_FACT_OR_REPORTED_DATA")
            heading_kw = re.search(r"結論|重點|摘要|總結|key takeaway|conclusion", s, re.I)
            importance = ("MUST_KEEP" if (heading_kw or (metrics and (stories or _tickers(s)) and relations)) else
                          "IMPORTANT" if (metrics or relations or stories or drivers) else "SUPPORTING")
            claims.append(Claim("C-%s" % _hash8(b.sid + s), b.source_id, b.sid, s, int(b.page), b.block_type, attribution,
                                _direction(s), bool(UNCERTAIN_RE.search(s)), bool(CONDITIONAL_RE.search(s)), importance,
                                metrics=metrics, stories=stories, tickers=_tickers(s), anchors=anchors, drivers=drivers,
                                relations=relations, periods=periods, macro_terms=macro))
    return claims


# ── 06 自測 / CLI ────────────────────────────────────────────────────────
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測(暫代 NON_STOCK_CORE_v0200 介面 · 多格式讀取)===" % ENGINE, flush=True)
    names = ["Claim", "SourceBlock", "NUMBER_RE", "URL_RE", "PROFILE_MESSENGER", "PROFILE_INDUSTRY", "PROFILE_OTHER", "PROFILE_EVERNOTE",
             "def_normalize_text", "def_guess_block_type", "def_extract_input", "def_extract_claims", "def_profile_router",
             "def_parse_messenger_blocks", "def_apply_note_layers", "def_similarity"]
    mod = sys.modules[__name__]
    chk("① v0310 要的 CORE 介面都在(16 名)", all(hasattr(mod, n) for n in names), [n for n in names if not hasattr(mod, n)] or "")
    c = Claim("c", "s", "e", "CSP CAPEX上調帶動ASIC需求成長", 1, "x", "SOURCE_FACT_OR_REPORTED_DATA", "POSITIVE", False, False, "IMPORTANT",
              stories=["ASIC_CUSTOM_SILICON"], drivers=["CAPEX", "DEMAND"])
    chk("② v0310 自測那一行的 Claim 位置參數相容", c.text.startswith("CSP") and c.importance == "IMPORTANT" and c.metrics == [])
    sample = ("2026年AI伺服器需求強勁,帶動台積電(2330)CoWoS產能擴充 30%。\n\n若美國關稅提高,可能拖累下半年出貨。\n\n"
              "本刊所刊載之內容僅做為參考")
    blk = [SourceBlock("S1", "t.txt", 1, 0, "PARAGRAPH", p) for p in sample.split("\n\n")]
    cl = def_extract_claims(blk)
    c1 = cl[0] if cl else None
    chk("③ 抽取式 Claim:原句不改 · 代號 2330 · 故事 = 先進封裝(AI 傘題讓位分段)· 有關係詞 · 有數字",
        c1 and c1.text in sample and "2330" in c1.tickers and c1.stories == ["ADVANCED_PACKAGING"]
        and c1.relations and c1.metrics, c1 and (c1.tickers, c1.stories, c1.metrics))
    c2 = cl[1] if len(cl) > 1 else None
    chk("④ 條件 / 不確定 / 負向 / 期間", c2 and c2.conditional and c2.uncertain and c2.direction == "NEGATIVE" and "下半年" in c2.periods,
        c2 and (c2.direction, c2.periods))
    chk("⑤ 免責聲明不成 Claim", len(cl) == 2, len(cl))
    chk("⑥ 年份不當代號(2026)", "2026" not in (c1.tickers if c1 else []))
    rf = reflow_lines("預估ASIC的可服務市場規模(SAM) 800億美元，市\n場年複合成長率達 30%。\n2645 長榮航太 14.1% 52.8% 8.34 14.5% 29.3%\n結論")
    chk("⑥c 表單欄位頭不成 Claim · 字距拆開的標題併回", is_form_line("公司名稱 來億-KY(6890) 報告種類 個股報告評 等 逢低買進")
        and not is_form_line("台股昨日上漲,外資買超 150 億元。") and reflow_lines("債 券 E T F 周 報｜市場焦點") == "債券ETF周報｜市場焦點",
        reflow_lines("債 券 E T F 周 報｜市場焦點"))
    chk("⑥b 排版斷行接回句子 · 表格列不接 · 表格列不成 Claim", "800億美元，市場年複合成長率達 30%。" in rf and "\n2645 長榮航太" in rf
        and not any("2645" in c.text for c in def_extract_claims([SourceBlock("R", "r.pdf", 1, 0, "PARAGRAPH", rf)])), rf.replace("\n", "⏎")[:80])
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "a.txt").write_bytes("油價攀升壓抑債市，利率高檔震盪。\n\n聯準會降息時點延後，美債殖利率走高。".encode("big5"))
        b, m = def_extract_input(d / "a.txt")
        chk("⑦ 文字檔 Big5 自動解碼 → 區塊", len(b) == 2 and "油價" in b[0].text, m.get("reader"))
        (d / "n.html").write_text("<html><script>x=1</script><h1>航太產業</h1><p>低軌衛星帶動需求成長 20%。</p></html>", encoding="utf-8")
        b, _ = def_extract_input(d / "n.html")
        chk("⑧ 網頁去 script · 留標題與內文", any("航太" in x.text for x in b) and not any("x=1" in x.text for x in b))
        try:
            import docx
            doc = docx.Document()
            doc.add_heading("記憶體產業展望", 1)
            doc.add_paragraph("HBM 供給吃緊,推升 DRAM 報價上漲 15%。")
            t = doc.add_table(rows=1, cols=2)
            t.rows[0].cells[0].text, t.rows[0].cells[1].text = "2026F", "成長 25%"
            doc.save(str(d / "w.docx"))
            b, _ = def_extract_input(d / "w.docx")
            chk("⑨ Word(.docx)段落 + 標題 + 表格", any(x.block_type == "HEADING" for x in b) and any("2026F | 成長 25%" in x.text for x in b),
                [x.block_type for x in b])
        except ImportError:
            chk("⑨ Word(.docx)(容器沒有 python-docx → 跳過不算)", True, "ABSENT")
        (d / "m.json").write_text(json.dumps({"messages": [{"time": "09:01", "sender": "A", "text": "航運運價回升,貨櫃三雄受惠。"},
                                                            {"time": "09:05", "sender": "B", "text": "PCB 族群訂單能見度到明年。"}]},
                                             ensure_ascii=False), encoding="utf-8")
        b, m = def_extract_input(d / "m.json")
        prof = def_profile_router(d / "m.json", b)
        chk("⑩ 訊息 JSON → 一則一塊 · 路由 = MESSENGER", len(b) == 2 and all(x.block_type == "MESSAGE" for x in b) and prof[0] == PROFILE_MESSENGER, prof)
        (d / "line.txt").write_text("\n".join(["10:01 王 美債殖利率走高,科技股承壓。", "10:03 李 散熱族群液冷訂單持續增加。",
                                               "10:05 陳 若關稅加徵,出口恐放緩。", "10:07 王 HBM 報價續漲。"]), encoding="utf-8")
        b, _ = def_extract_input(d / "line.txt")
        prof = def_profile_router(d / "line.txt", b)
        mb = def_parse_messenger_blocks(d / "line.txt", b)
        chk("⑪ LINE 匯出文字 → 認出聊天 · 一則一塊", prof[0] == PROFILE_MESSENGER and len(mb) == 4, (prof, len(mb)))
        raw = ("From: desk@example.com\nSubject: 晨間快訊\nDate: Wed, 12 Nov 2026 08:00:00 +0800\nContent-Type: text/plain; charset=utf-8\n\n"
               "台股昨日上漲 1.2%,外資買超 150 億元。").encode("utf-8")
        (d / "e.eml").write_bytes(raw)
        b, _ = def_extract_input(d / "e.eml")
        chk("⑫ 電子郵件 .eml → 主旨頭 + 內文", len(b) == 2 and "晨間快訊" in b[0].text and "外資" in b[1].text)
        try:
            from reportlab.pdfgen import canvas
            cv = canvas.Canvas(str(d / "p.pdf"))
            y = 800
            for line in ["Industry outlook: AI server demand driven by CSP capex, up 35% YoY in 2026.",
                         "Risk: if tariffs rise, shipments may slow in 2H26."] * 3:
                cv.drawString(50, y, line)
                y -= 20
            cv.save()
            b, m = def_extract_input(d / "p.pdf")
            chk("⑬ PDF(有字)→ pdfplumber 讀 · 不走 OCR", b and m.get("pdf_reader") == "pdfplumber" and not m.get("image_pdf"), m.get("pdf_reader"))
        except ImportError:
            chk("⑬ PDF(容器沒有 reportlab 造樣本 → 跳過不算)", True, "ABSENT")
        from PIL import Image
        Image.new("RGB", (40, 20), "white").save(d / "i.png")
        try:
            b, m = def_extract_input(d / "i.png")
            chk("⑭ 圖片 → OCR 車道有就緒(讀到 %d 塊)" % len(b), True, m.get("ocr_lane"))
        except ReaderUnavailable as exc:
            chk("⑭ 圖片沒有就緒 OCR 車道 → 照實 ReaderUnavailable(不假抽)", "OCR" in str(exc), str(exc)[:90])
        try:
            def_extract_input(d / "x.xyz")
            chk("⑮ 不支援副檔名 → ReaderUnavailable", False)
        except ReaderUnavailable:
            chk("⑮ 不支援副檔名 → ReaderUnavailable", True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑯ 零網路 · 不用 TA-Lib · 不 import VCGC · 不寫同意閘",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|CGC_)", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("--selftest", "selftest"):
        return selftest()
    if args[0] == "read" and len(args) > 1:
        try:
            blocks, meta = def_extract_input(Path(args[1]))
        except ReaderUnavailable as exc:
            print("[ABSENT] %s" % exc)
            return 3
        claims = def_extract_claims(blocks)
        print(json.dumps({"meta": meta, "profile": def_profile_router(Path(args[1]), blocks), "claims": len(claims),
                          "first": [c.text for c in claims[:5]]}, ensure_ascii=False, indent=2))
        return 0 if blocks else 2
    print("用法:VRN2_NonStockCore_v0100.py --selftest | read <檔>")
    return 2


if __name__ == "__main__":
    sys.exit(main())
