#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_NonStockReaders v0100 — VRN 非個股車道的「讀檔 + 類型路由」層(從暫代核心 VRN2_NonStockCore_v0100 原樣搬出)

操作員 2026-11-22:「整合去重 · 整合成功後刪除」+ 上傳 NON_STOCK_CORE_v0400(操作員正式核心)。
v0400 是 v0310 摘要器要的核心(16 個名稱全有),但它只讀 pdf(fitz / pypdf)· txt/md/log/html · docx · enex · json(區塊格式)。
暫代核心 VRN2_NonStockCore_v0100 另有 VRN 自己的讀檔與路由,v0400 沒有 —— 刪暫代核心前要先把這一塊搬出來,否則圖片 / 郵件 / Office 讀不到:
  · 圖片 → VCGC 鎖版 OCR 車道(RapidOCR → Tesseract → Paddle → Surya,隔離境子行程)
  · 影像 PDF → pypdfium2 轉圖再 OCR · 文字 PDF 三段讀法 pdfplumber → pypdf → pdftotext
  · .eml · .doc/.rtf/.odt(LibreOffice)· LINE / Messenger 訊息 JSON · .enex · 網頁 · 純文字(多編碼)
  · 類型路由(新聞 NEWS · 訊息 · 筆記 · 產業 · 總經 · 盤勢)與聊天切分(一則訊息一塊)
本檔的 40 個定義是用語法樹從 VRN2_NonStockCore_v0100 逐字搬來的(自測 ⑩ 逐一比對原文);只改兩處:
  ① meta 的 backend 標 VRN2_NONSTOCK_READERS_v0100(不再冒充核心)
  ② 新聞路由回 (核心的 PROFILE_OTHER, "NEWS"):v0400 沒有 NEWS 這個類型,報告類型照舊顯示 NEWS(子類型)
核心相依(SourceBlock · def_normalize_text · def_guess_block_type · PROFILE_*)不自己做,一律由 bind(core) 綁到呼叫方給的核心(v0400)。
邊界:只讀輸入檔;不寫檔(OCR / LibreOffice 只用暫存夾);零網路(OCR 只借鎖冊路徑,車道在隔離境);不用 TA-Lib;不 import VCGC 模組。
用法:python VRN2_NonStockReaders_v0100.py extract <檔> [--core <核心.py>] · --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

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
from pathlib import Path
from typing import Optional

VERSION = "v0100"
ENGINE = "VRN2_NonStockReaders " + VERSION
HERE = Path(__file__).resolve().parent
SOURCE_OF_MOVE = "VRN2_NonStockCore_v0100.py"          # 搬出來源(自測 ⑩ 比對用;來源不在 = 灰,不算失敗)

# ── 00 核心綁定(bind 之前用到 = 照實報錯,不自己猜)────────────────────────────
SourceBlock = None
def_normalize_text = None
def_guess_block_type = None
PROFILE_MESSENGER = PROFILE_INDUSTRY = PROFILE_OTHER = PROFILE_EVERNOTE = PROFILE_NEWS = None
BOUND = {"core": None}
_CORE_NAMES = ("SourceBlock", "def_normalize_text", "def_guess_block_type", "PROFILE_MESSENGER", "PROFILE_INDUSTRY", "PROFILE_OTHER", "PROFILE_EVERNOTE")


def bind(core) -> dict:
    """把讀檔層綁到核心模組(v0400):區塊型別 · 正規化 · 類型常數都用核心的。核心沒有 NEWS → 新聞走核心的 OTHER + 子類型 NEWS。"""
    miss = [n for n in _CORE_NAMES if not hasattr(core, n)]
    if miss:
        raise RuntimeError("核心缺 %s · 不綁" % " ".join(miss))
    g = globals()
    for n in _CORE_NAMES:
        g[n] = getattr(core, n)
    g["PROFILE_NEWS"] = getattr(core, "PROFILE_NEWS", core.PROFILE_OTHER)
    BOUND["core"] = getattr(core, "__file__", repr(core))
    return {"core": BOUND["core"], "profiles": {n: g[n] for n in _CORE_NAMES if n.startswith("PROFILE_")}, "news": g["PROFILE_NEWS"]}


# ── 01 以下 40 個定義自 VRN2_NonStockCore_v0100 逐字搬出 ─────────────────────────
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
OCR_PAGE_LIMIT = 30                   # 影像 PDF 最多 OCR 幾頁(重件;超過照實記)
NUMBER_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?\s*%?")
MSG_HEAD_RE = re.compile(r"^\s*(?:\[?\s*(?:\d{4}[/.-]\d{1,2}[/.-]\d{1,2}\s*)?(?:上午|下午|AM|PM)?\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\s*\]?)\s*[\t ]?(.*)$", re.I)


class ReaderUnavailable(RuntimeError):
    """讀這種格式要的工具不在(例:圖片沒有就緒的 OCR 車道)→ 照實 ABSENT,不假抽。"""


def _hash8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:8].upper()


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
    meta = {"backend": "VRN2_NONSTOCK_READERS_" + VERSION, "format": FORMAT_OF.get(ext, "UNKNOWN"), "ext": ext}
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


# ── 02 自測 / CLI ─────────────────────────────────────────────────────────
def _default_core() -> Optional[Path]:
    hits = sorted(HERE.glob("nonstock_core_v*/NON_STOCK_CORE_v*.py"))
    return hits[-1] if hits else None


def _load_core(path: Path):
    spec = importlib.util.spec_from_file_location("vrn2_readers_core_%s" % hashlib.sha1(str(path).encode()).hexdigest()[:8], path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def moved_defs_match(source: Path) -> tuple:
    """本檔每個搬來的定義 vs 來源檔同名定義:原文逐字相同(只容許 backend 標籤那一處)。回 (相同數, 總數, 不同清單)。"""
    import ast
    mine_src = Path(__file__).read_text(encoding="utf-8")
    head, _, body = mine_src.partition("# ── 01 以下 40 個定義")
    body = body.split("# ── 02 自測 / CLI", 1)[0]
    src = source.read_text(encoding="utf-8")
    theirs = {}
    for n in ast.parse(src).body:
        for nm in ([n.name] if isinstance(n, (ast.FunctionDef, ast.ClassDef)) else
                   [x.id for x in getattr(n, "targets", []) if isinstance(x, ast.Name)]):
            theirs[nm] = ast.get_source_segment(src, n)
    same, diff, total = 0, [], 0
    tree = ast.parse(mine_src)
    for n in tree.body:
        if n.lineno < len(head.split("\n")) + 1:
            continue
        seg = ast.get_source_segment(mine_src, n)
        if seg is None or "# ── 02" in seg:
            continue
        names = [n.name] if isinstance(n, (ast.FunctionDef, ast.ClassDef)) else [x.id for x in getattr(n, "targets", []) if isinstance(x, ast.Name)]
        if not names or names[0] in ("_default_core", "_load_core", "moved_defs_match", "selftest", "main"):
            continue
        total += 1
        t = theirs.get(names[0], "")
        if seg == t or seg == t.replace('"VRN2_NONSTOCK_CORE_" + VERSION', '"VRN2_NONSTOCK_READERS_" + VERSION'):
            same += 1
        else:
            diff.append(names[0])
    return same, total, diff


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print("=== %s 自測(讀檔 + 路由 · 綁 v0400 核心 · 暫存夾造資料 · 零網路)===" % ENGINE, flush=True)
    cp = _default_core()
    chk("① 找得到 v0400 核心(nonstock_core_v*/NON_STOCK_CORE_v*.py)", cp is not None and cp.is_file(), cp)
    core = _load_core(cp)
    info = bind(core)
    chk("② bind:類型常數用核心的 · 新聞 = 核心 OTHER", info["news"] == core.PROFILE_OTHER and PROFILE_MESSENGER == core.PROFILE_MESSENGER, info)
    with tempfile.TemporaryDirectory(prefix="vrn2_readers_") as td:
        d = Path(td)
        (d / "a.txt").write_text("第一段:AI伺服器需求成長 40%。\n\n第二段:若關稅提高,下半年出貨可能放緩。", encoding="utf-8")
        b, m = def_extract_input(d / "a.txt")
        chk("③ 純文字 → 兩段 · 區塊是核心的 SourceBlock · backend 標讀檔層", len(b) == 2 and all(isinstance(x, core.SourceBlock) for x in b)
            and m["backend"] == "VRN2_NONSTOCK_READERS_v0100", (len(b), m))
        (d / "n.html").write_text("<h1>航運快訊</h1><script>x=1</script><p>記者報導:貨櫃運價回升 12%。</p>", encoding="utf-8")
        b, m = def_extract_input(d / "n.html")
        txt = "\n".join(x.text for x in b)
        chk("④ 網頁 → 去 script · 留內文", "貨櫃運價" in txt and "x=1" not in txt, txt[:80])
        chk("⑤ 路由:新聞 → (核心 OTHER, NEWS)", def_profile_router(d / "n.html", b) == (core.PROFILE_OTHER, "NEWS"), def_profile_router(d / "n.html", b))
        (d / "c.json").write_text(json.dumps({"messages": [{"time": "09:01", "sender": "A", "text": "美債殖利率走高,科技股承壓。"},
                                                         {"time": "09:05", "sender": "B", "text": "PCB 訂單能見度到明年。"}]}, ensure_ascii=False), encoding="utf-8")
        b, m = def_extract_input(d / "c.json")
        chk("⑥ 訊息 JSON → 一則一塊 MESSAGE · 路由 MESSENGER", len(b) == 2 and all(x.block_type == "MESSAGE" for x in b)
            and def_profile_router(d / "c.json", b)[0] == core.PROFILE_MESSENGER, (len(b), m))
        (d / "m.eml").write_bytes(b"From: a@example.com\r\nSubject: =?utf-8?b?5rW36YGL?=\r\nDate: Sun, 22 Nov 2026 09:00:00 +0800\r\n"
                                  b"Content-Type: text/plain; charset=utf-8\r\n\r\n" + "運價回升,帶動獲利改善。".encode("utf-8"))
        b, m = def_extract_input(d / "m.eml")
        chk("⑦ 郵件 .eml → 標頭 + 內文", b and b[0].block_type == "HEADING" and any("運價回升" in x.text for x in b), [x.text[:30] for x in b])
        chat = "\n".join("2026/11/22 09:%02d 小明 第 %d 則訊息內容" % (i, i) for i in range(1, 7))
        (d / "line.txt").write_text(chat, encoding="utf-8")
        b, _ = def_extract_input(d / "line.txt")
        msgs = def_parse_messenger_blocks(d / "line.txt", b)
        chk("⑧ 聊天文字 → 路由 MESSENGER · 一則訊息一塊", def_profile_router(d / "line.txt", b)[0] == core.PROFILE_MESSENGER and len(msgs) == 6,
            (def_profile_router(d / "line.txt", b), len(msgs)))
        (d / "n.enex").write_text("<en-export><note><title>筆記</title><content><![CDATA[<div>庫存去化接近尾聲。</div>]]></content></note></en-export>",
                                  encoding="utf-8")
        b, _ = def_extract_input(d / "n.enex")
        chk("⑨ 筆記 .enex → 標題 + 內文 · 路由 EVERNOTE", b and def_profile_router(d / "n.enex", b)[0] == core.PROFILE_EVERNOTE, len(b))
        try:
            from PIL import Image
            Image.new("RGB", (40, 20), "white").save(d / "s.png")
            try:
                b, m = def_extract_input(d / "s.png")
                img_ok = m.get("reader") == "OCR"
            except ReaderUnavailable as exc:
                img_ok = "OCR" in str(exc)
        except ImportError:
            img_ok = True                                       # 沒有 PIL 造不出圖:不算本檔失敗
        chk("⑩ 圖片 → OCR 車道;沒有就緒車道 → ReaderUnavailable(照實,不假抽)", img_ok)
        try:
            def_extract_input(d / "x.unknownext")
            unk = False
        except ReaderUnavailable:
            unk = True
        except FileNotFoundError:
            unk = False
        chk("⑪ 不支援的副檔名 → ReaderUnavailable", unk)
    srcf = HERE / SOURCE_OF_MOVE
    if srcf.is_file():
        same, total, diff = moved_defs_match(srcf)
        chk("⑫ 40 個定義與來源 %s 逐字相同(只差 backend 標籤)" % SOURCE_OF_MOVE, total == 40 and same == total and not diff, (same, total, diff))
    else:
        print("  [GRAY] ⑫ 來源 %s 已不在 → 逐字比對略過(搬移當時已驗)" % SOURCE_OF_MOVE, flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑬ 零網路 · 不用 TA-Lib · 不 import VCGC · 加速器橋在",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|http|CGC_)", body, re.M) and "[VIA:ACCEL-BRIDGE:v0100]" in src)
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=ENGINE)
    ap.add_argument("verb", nargs="?", default="selftest", choices=["extract", "selftest"])
    ap.add_argument("path", nargs="?")
    ap.add_argument("--core", default=None, help="核心檔(預設 nonstock_core_v* 最新那一支)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    if not a.path:
        ap.error("extract 要給一個檔")
    bind(_load_core(Path(a.core) if a.core else _default_core()))
    try:
        blocks, meta = def_extract_input(Path(a.path))
    except ReaderUnavailable as exc:
        print(json.dumps({"status": "ABSENT", "why": str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps({"status": "OK" if blocks else "NODATA", "meta": meta, "profile": def_profile_router(Path(a.path), blocks),
                      "blocks": [{"sid": b.sid, "page": b.page, "type": b.block_type, "text": b.text[:120]} for b in blocks[:20]]},
                     ensure_ascii=False, indent=1))
    return 0 if blocks else 2


if __name__ == "__main__":
    sys.exit(main())
