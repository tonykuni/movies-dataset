# -*- coding: utf-8 -*-
"""
VIA Spec Extractor (VSX) v0100 — E1 規格轉換 · 內容擷取 強化層
=================================================================
把任何來源（HTML / MD / TXT / DOCX / PPTX / XLSX / CSV / JSON / YAML / CSS / JS / TS / PY / PS1 / PDF*）擷取成
「七類規格」的結構化 IR，再輸出 Markdown 規格書 + Visual Lock HTML + JSON：

  UI 規格       元件(選擇器/tag/id/role/data-*/事件/子元件)、表單欄位(型別/必填/pattern/min-max)、導覽、表格、圖片、a11y
  設計 token    顏色 / 字型 / 字級 / 間距 / 圓角 / 陰影 / 斷點 / CSS 變數  (從 CSS、inline style、MD 設計文件)
  互動邏輯      事件處理器、狀態變更、API 呼叫 (fetch/axios/ajax/XHR)、儲存 (localStorage/sessionStorage)、路由
  內容模型      標題階層、段落、清單、任務、表格(欄位/型別推論/單位)、程式碼區塊、連結、圖片、數學
  業務規則      必須/應/不得/禁止/當…時/若…則/MUST/SHALL/SHOULD/MUST NOT、數值門檻、公式、狀態轉移、驗收條件
  API/資料規格  端點(方法/路徑/參數)、函式簽章 (py ast / js / ps1)、JSON/YAML schema 推論 (鍵/型別/enum/範圍)
  缺口          元件無事件、欄位無驗證、規則無條件、API 無方法、表格無型別、img 無 alt、input 無 label…

治理：100% 唯讀；每筆規格有穩定 ID (SPEC-{類}-blake2s(類|正規化文字))、來源 (file:line / selector)、證據等級
      V(結構明確: 標籤/AST/schema) M(模式命中: 規則句/正則) P(推論: 型別/單位猜測)；跨來源去重合併、只增不減的 spec_registry。
零依賴；bs4 / lxml / pypdf / pdfplumber / tinycss2 / esprima 若在場自動加強，不在場降級 stdlib。
*PDF 需 pypdf 或 pdfplumber。

用法:  python via_spec_extractor.py --in <files/dirs...> --out <dir> [--title 名稱] [--selftest]
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import html
import io
import json
import os
import re
import sys
import time
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from html.parser import HTMLParser
from pathlib import Path

VERSION = "0100"
CONTRACT = "VIA_SPEC_IR/1.0"
TEXT_EXT = {".md", ".markdown", ".txt", ".log", ".rst"}
HTML_EXT = {".html", ".htm", ".xhtml"}
CODE_EXT = {".py": "python", ".js": "javascript", ".mjs": "javascript", ".ts": "typescript", ".tsx": "typescript",
            ".jsx": "javascript", ".ps1": "powershell", ".psm1": "powershell", ".css": "css", ".scss": "css", ".sql": "sql"}
DATA_EXT = {".json": "json", ".jsonl": "jsonl", ".yaml": "yaml", ".yml": "yaml", ".csv": "csv", ".tsv": "tsv", ".toml": "toml"}
OFFICE_EXT = {".docx": "docx", ".pptx": "pptx", ".xlsx": "xlsx", ".xlsm": "xlsx"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "_to_delete", "dist", "build"}


def _h(s: str, n: int = 6) -> str:
    return hashlib.blake2s(s.encode("utf-8", "replace"), digest_size=n).hexdigest().upper()


def _norm(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip().lower()
    return re.sub(r"[\u3000\s]+", " ", s)


def spec_id(kind: str, text: str) -> str:
    return f"SPEC-{kind}-{_h(kind + '|' + _norm(text))}"


@dataclass
class Item:
    id: str
    kind: str            # UI / TOKEN / LOGIC / CONTENT / RULE / API / DATA / GAP
    sub: str             # component / form_field / color / event / heading / rule / endpoint / schema / ...
    text: str
    grade: str           # V / M / P
    source: str          # file
    loc: str = ""        # line / selector / sheet!cell
    attrs: dict = field(default_factory=dict)
    sources: list = field(default_factory=list)   # 合併後的全部來源


@dataclass
class Src:
    file: str
    kind: str
    bytes: int
    sha: str
    encoding: str = "utf-8"
    note: str = ""


# ----------------------------------------------------------------------------- readers
def read_text(p: Path) -> tuple[str, str]:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "cp950", "latin-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace"), "utf-8-replace"


def _xml_text(xml: str) -> list[str]:
    """OOXML 極簡文字抽取：<w:p>/<a:p> 段落 → 文字；<w:tbl> 表格 → rows（stdlib only）。"""
    out = []
    for para in re.findall(r"<(?:w|a):p\b.*?</(?:w|a):p>", xml, re.S):
        style = re.search(r'<w:pStyle w:val="([^"]+)"', para)
        txt = "".join(re.findall(r"<(?:w|a):t[^>]*>(.*?)</(?:w|a):t>", para, re.S))
        txt = html.unescape(txt)
        if txt.strip():
            out.append(((style.group(1) if style else ""), txt))
    return out


def _xml_tables(xml: str) -> list[list[list[str]]]:
    tables = []
    for tbl in re.findall(r"<w:tbl>.*?</w:tbl>", xml, re.S):
        rows = []
        for tr in re.findall(r"<w:tr\b.*?</w:tr>", tbl, re.S):
            cells = []
            for tc in re.findall(r"<w:tc\b.*?</w:tc>", tr, re.S):
                cells.append(html.unescape("".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", tc, re.S))).strip())
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def read_docx(p: Path) -> str:
    """docx → 偽 Markdown（Heading 樣式→#，表格→MD 表格），純 zipfile。"""
    with zipfile.ZipFile(p) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    lines = []
    tables = _xml_tables(xml)
    ti = 0
    body = re.split(r"(<w:tbl>.*?</w:tbl>)", xml, flags=re.S)
    for seg in body:
        if seg.startswith("<w:tbl>"):
            if ti < len(tables):
                t = tables[ti]
                ti += 1
                lines.append("| " + " | ".join(t[0]) + " |")
                lines.append("|" + "---|" * len(t[0]))
                for r in t[1:]:
                    lines.append("| " + " | ".join(r) + " |")
                lines.append("")
            continue
        for style, txt in _xml_text(seg):
            m = re.match(r"(?:Heading|heading|標題)\s*(\d)", style)
            if m:
                lines.append("#" * int(m.group(1)) + " " + txt)
            elif style.lower().startswith(("listparagraph", "list")):
                lines.append("- " + txt)
            else:
                lines.append(txt)
            lines.append("")
    return "\n".join(lines)


def read_pptx(p: Path) -> str:
    lines = []
    with zipfile.ZipFile(p) as z:
        names = sorted([n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
                       key=lambda n: int(re.search(r"(\d+)", n).group(1)))
        for n in names:
            xml = z.read(n).decode("utf-8", "replace")
            num = re.search(r"(\d+)", n).group(1)
            paras = [t for _, t in _xml_text(xml)]
            if paras:
                lines.append(f"# Slide {num}: {paras[0]}")
                for t in paras[1:]:
                    lines.append("- " + t)
                lines.append("")
    return "\n".join(lines)


def read_xlsx(p: Path) -> dict[str, list[list[str]]]:
    """xlsx → {sheet: rows}（sharedStrings + inline）。"""
    sheets = {}
    with zipfile.ZipFile(p) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            sx = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
            shared = [html.unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))) for si in re.findall(r"<si>.*?</si>", sx, re.S)]
        wb = z.read("xl/workbook.xml").decode("utf-8", "replace") if "xl/workbook.xml" in z.namelist() else ""
        names = re.findall(r'<sheet [^>]*name="([^"]+)"', wb)
        files = sorted([n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)],
                       key=lambda n: int(re.search(r"(\d+)", n).group(1)))
        for i, f in enumerate(files):
            xml = z.read(f).decode("utf-8", "replace")
            rows = []
            for row in re.findall(r"<row\b.*?</row>", xml, re.S):
                cells = []
                for c in re.findall(r'<c\b([^>]*)>(.*?)</c>', row, re.S):
                    attrs, inner = c
                    v = re.search(r"<v>(.*?)</v>", inner, re.S)
                    t = re.search(r'\bt="(\w+)"', attrs)
                    if t and t.group(1) == "s" and v:
                        try:
                            cells.append(shared[int(v.group(1))])
                        except (ValueError, IndexError):
                            cells.append("")
                    elif t and t.group(1) == "inlineStr":
                        cells.append(html.unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", inner, re.S))))
                    else:
                        cells.append(html.unescape(v.group(1)) if v else "")
                if any(x.strip() for x in cells):
                    rows.append(cells)
            sheets[names[i] if i < len(names) else f"Sheet{i + 1}"] = rows
    return sheets


def read_pdf(p: Path) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(str(p)) as pdf:
            return "\n\n".join((pg.extract_text() or "") for pg in pdf.pages)
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        return "\n\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
    except ImportError:
        return ""


# ----------------------------------------------------------------------------- HTML DOM (stdlib)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SEMANTIC = {"header", "nav", "main", "section", "article", "aside", "footer", "form", "table", "dialog", "details",
            "summary", "button", "select", "textarea", "input", "label", "fieldset", "legend", "menu", "figure", "canvas",
            "video", "audio", "iframe", "progress", "meter", "output", "template", "slot"}
COMP_CLASS = re.compile(r"(card|modal|dialog|drawer|tab|panel|nav|menu|sidebar|toolbar|header|footer|form|table|grid|list|"
                        r"item|btn|button|badge|chip|pill|tag|alert|toast|tooltip|dropdown|accordion|carousel|stepper|"
                        r"kpi|widget|chart|dashboard|hero|banner|breadcrumb|pagination|avatar|spinner|skeleton)", re.I)


class Node:
    __slots__ = ("tag", "attrs", "children", "text", "parent", "line")

    def __init__(self, tag, attrs, parent, line):
        self.tag, self.attrs, self.parent, self.line = tag, dict(attrs), parent, line
        self.children, self.text = [], []

    def get_text(self, limit=None) -> str:
        parts = list(self.text)
        for c in self.children:
            if c.tag not in ("script", "style"):
                parts.append(c.get_text())
        s = " ".join(x for x in parts if x).strip()
        s = re.sub(r"\s+", " ", s)
        return s[:limit] if limit else s

    def cls(self) -> str:
        return self.attrs.get("class", "") or ""

    def selector(self) -> str:
        parts = []
        n = self
        while n is not None and n.tag != "#root":
            seg = n.tag
            if n.attrs.get("id"):
                seg += "#" + n.attrs["id"]
                parts.append(seg)
                break
            c = (n.cls() or "").split()
            if c:
                seg += "." + ".".join(c[:2])
            elif n.parent is not None:
                sib = [x for x in n.parent.children if x.tag == n.tag]
                if len(sib) > 1:
                    seg += f":nth-of-type({sib.index(n) + 1})"
            parts.append(seg)
            n = n.parent
        return " > ".join(reversed(parts))

    def depth(self) -> int:
        d, n = 0, self.parent
        while n is not None:
            d += 1
            n = n.parent
        return d


class DOM(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [], None, 0)
        self.cur = self.root
        self.scripts, self.styles = [], []
        self._capture = None

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur, self.getpos()[0])
        self.cur.children.append(n)
        if tag in ("script", "style"):
            self._capture = (tag, n, [])
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur, self.getpos()[0]))

    def handle_endtag(self, tag):
        if self._capture and self._capture[0] == tag:
            kind, node, buf = self._capture
            txt = "".join(buf)
            (self.scripts if kind == "script" else self.styles).append({"line": node.line, "text": txt,
                                                                       "src": node.attrs.get("src", ""), "attrs": node.attrs})
            self._capture = None
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        if self._capture:
            self._capture[2].append(data)
        elif data.strip():
            self.cur.text.append(data.strip())

    def walk(self, n=None):
        n = n or self.root
        for c in n.children:
            yield c
            yield from self.walk(c)


def parse_html(text: str) -> DOM:
    d = DOM()
    try:
        d.feed(text)
    except Exception:  # noqa: BLE001
        pass
    return d


# ----------------------------------------------------------------------------- extractors
COLOR_RE = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}\b|rgba?\([^)]*\)|hsla?\([^)]*\)")
CSS_VAR_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;}]+)")
FONT_RE = re.compile(r"font-family\s*:\s*([^;}]+)", re.I)
SIZE_RE = re.compile(r"\bfont-size\s*:\s*([\d.]+(?:px|rem|em|pt|%))", re.I)
SPACE_RE = re.compile(r"\b(?:margin|padding|gap)(?:-\w+)?\s*:\s*([^;}]+)", re.I)
RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;}]+)", re.I)
SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;}]+)", re.I)
MEDIA_RE = re.compile(r"@media[^{]*\(\s*(?:max|min)-width\s*:\s*([\d.]+(?:px|em|rem))", re.I)
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")

JS_EVENT_RE = re.compile(r"addEventListener\(\s*['\"](\w+)['\"]|\bon(?:click|change|input|submit|keydown|keyup|load|scroll|resize|focus|blur|mouseover|mouseenter|mouseleave)\s*=", re.I)
JS_API_RE = re.compile(r"\bfetch\(\s*[`'\"]([^`'\"]+)|axios\.(get|post|put|delete|patch)\(\s*[`'\"]([^`'\"]+)|\$\.(?:ajax|get|post)\(\s*(?:\{[^}]*url\s*:\s*)?[`'\"]([^`'\"]+)|XMLHttpRequest|open\(\s*['\"](GET|POST|PUT|DELETE)['\"]\s*,\s*[`'\"]([^`'\"]+)", re.I)
JS_STORAGE_RE = re.compile(r"\b(localStorage|sessionStorage|indexedDB|document\.cookie)\b")
JS_STATE_RE = re.compile(r"\b(setState|useState|useReducer|ref\(|reactive\(|writable\(|store\.\w+|dispatch\()")
JS_ROUTE_RE = re.compile(r"(?:path|route|href|to)\s*[:=]\s*[`'\"](/[\w/:.\-{}]*)[`'\"]")
URL_PATH_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/.\-{}:?=&]+)", re.I)

RULE_PATTERNS = [
    ("MUST", re.compile(r"(必須|必需|務必|一定要|應當|應該|應|需要|需|\bmust\b|\bshall\b|\brequired\b|\bmandatory\b)", re.I)),
    ("MUST_NOT", re.compile(r"(不得|不可|不能|禁止|嚴禁|不應|勿|\bmust not\b|\bshall not\b|\bnever\b|\bforbidden\b|\bprohibited\b)", re.I)),
    ("SHOULD", re.compile(r"(建議|宜|最好|盡量|\bshould\b|\brecommended\b|\bprefer)", re.I)),
    ("CONDITION", re.compile(r"(當.{1,40}時|若.{1,40}則|如果.{1,40}(則|就)|只有.{1,30}才|除非|\bif\b.{1,60}\bthen\b|\bwhen\b|\bunless\b|\bonly if\b)", re.I)),
    ("THRESHOLD", re.compile(r"(≥|≤|>=|<=|大於|小於|不超過|至少|最多|上限|下限|超過|低於)\s*[\d.]+|[\d.]+\s*(%|％|秒|分鐘|小時|天|筆|次|MB|GB|ms|px)", re.I)),
    ("FORMULA", re.compile(r"(公式|計算方式|計算公式|乘以|除以|加總|平均值|Σ|\bsum\(|\bavg\(|\bformula\b|[A-Za-z\u4e00-\u9fff)]\s*=\s*[^=\n]{2,60}[+\-*/×÷][^=\n]{1,60})")),
    ("TRANSITION", re.compile(r"(\w+|[\u4e00-\u9fff]{1,6})\s*(→|->|=>|轉為|變為|切換為|進入)\s*(\w+|[\u4e00-\u9fff]{1,6})")),
    ("ACCEPTANCE", re.compile(r"(驗收|Given\b|When\b|Then\b|\bAC\d*[:：]|通過條件|完成定義|\bDoD\b|測試案例|預期結果)", re.I)),
    ("PERMISSION", re.compile(r"(權限|角色|授權|只允許|僅限|管理員|admin\b|\brole\b|\bpermission\b|\bauthori[sz])", re.I)),
]

FIELD_DEF_RE = re.compile(r"^[\s\-*]*[`*]*([A-Za-z_][\w.]*|[\u4e00-\u9fff]{1,12})[`*]*\s*[:：(（]\s*(string|str|int|integer|float|number|bool|boolean|date|datetime|enum|list|array|dict|object|文字|數字|整數|日期|布林|列舉|字串)\b", re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(?:\[([ xX])\]\s+)?(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)")
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)")
MATH_RE = re.compile(r"\$\$?[^$]{2,}\$\$?")


def infer_type(values: list[str]) -> tuple[str, str]:
    """欄位型別 + 單位推論 (P 級)。"""
    vals = [v.strip() for v in values if v and v.strip()]
    if not vals:
        return "empty", ""
    unit = ""
    m = Counter(re.sub(r"[-\d.,\s]", "", v) for v in vals).most_common(1)[0][0]
    if m in ("%", "％", "元", "NT$", "$", "USD", "TWD", "px", "ms", "秒", "MB", "GB", "億", "萬", "張", "股"):
        unit = m
    core = []
    for v in vals:
        c = v.replace(unit, "") if unit else v
        c = re.sub(r"^(NT\$|US\$|\$|USD|TWD)|[,\s]|(%|％|元|px|ms)$", "", c.strip())
        core.append(c)
    if all(re.fullmatch(r"-?\d+", v) for v in core):
        return "integer", unit
    if all(re.fullmatch(r"-?\d*\.?\d+(e-?\d+)?", v) for v in core):
        return "number", unit
    if all(re.fullmatch(r"\d{4}[-/.]\d{1,2}([-/.]\d{1,2})?|\d{1,3}年\d{1,2}月\d{1,2}日|\d{8}", v) for v in vals):
        return "date", ""
    if all(v.lower() in ("y", "n", "yes", "no", "true", "false", "是", "否", "✓", "✗", "v", "x") for v in vals):
        return "boolean", ""
    if len(set(vals)) <= max(2, len(vals) // 3) and len(set(vals)) <= 8 and len(vals) >= 4:
        return "enum(" + "|".join(sorted(set(vals))[:8]) + ")", ""
    if all(re.match(r"https?://|/", v) for v in vals):
        return "url", ""
    return "string", ""


class Extractor:
    def __init__(self):
        self.items: list[Item] = []
        self.sources: list[Src] = []
        self.warnings: list[str] = []

    def add(self, kind, sub, text, grade, source, loc="", **attrs):
        text = (text or "").strip()
        if not text:
            return None
        it = Item(spec_id(kind + "-" + sub.upper()[:8], text if sub not in ("component", "form_field") else text + "|" + loc),
                  kind, sub, text[:600], grade, source, loc, attrs, [f"{source}:{loc}" if loc else source])
        self.items.append(it)
        return it

    # ---------------- markdown / text
    def from_markdown(self, text: str, src: str):
        lines = text.splitlines()
        stack = []
        i = 0
        in_code, code_buf, code_lang, code_start = False, [], "", 0
        fm = None
        if lines and lines[0].strip() == "---":
            for j in range(1, min(len(lines), 60)):
                if lines[j].strip() == "---":
                    fm = "\n".join(lines[1:j])
                    i = j + 1
                    break
        if fm:
            for k, v in re.findall(r"^([\w-]+)\s*:\s*(.+)$", fm, re.M):
                self.add("CONTENT", "front_matter", f"{k}: {v}", "V", src, "L1", key=k, value=v)
        para = []

        def flush_para(end_line):
            if para:
                txt = " ".join(para).strip()
                self.add("CONTENT", "paragraph", txt, "V", src, f"L{end_line - len(para) + 1}", section=" / ".join(h for _, h in stack))
                self._rules_from_text(txt, src, f"L{end_line - len(para) + 1}", " / ".join(h for _, h in stack))
                para.clear()

        while i < len(lines):
            ln = lines[i]
            if in_code:
                if ln.strip().startswith("```"):
                    code = "\n".join(code_buf)
                    self.add("CONTENT", "code_block", code, "V", src, f"L{code_start}", language=code_lang, lines=len(code_buf))
                    self.from_code(code, code_lang, src, base_line=code_start)
                    in_code, code_buf = False, []
                else:
                    code_buf.append(ln)
                i += 1
                continue
            if ln.strip().startswith("```"):
                flush_para(i)
                in_code, code_lang, code_start = True, ln.strip()[3:].strip().lower() or "text", i + 2
                i += 1
                continue
            m = HEADING_RE.match(ln)
            if m:
                flush_para(i)
                lvl, h = len(m.group(1)), m.group(2).strip()
                while stack and stack[-1][0] >= lvl:
                    stack.pop()
                stack.append((lvl, h))
                self.add("CONTENT", "heading", h, "V", src, f"L{i + 1}", level=lvl, path=" / ".join(x for _, x in stack))
                i += 1
                continue
            if "|" in ln and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1]):
                flush_para(i)
                header = [c.strip() for c in ln.strip().strip("|").split("|")]
                rows, j = [], i + 2
                while j < len(lines) and "|" in lines[j] and lines[j].strip():
                    rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                    j += 1
                self._table(header, rows, src, f"L{i + 1}", " / ".join(h for _, h in stack))
                i = j
                continue
            m = LIST_RE.match(ln)
            if m:
                flush_para(i)
                indent, marker, task, body = len(m.group(1)), m.group(2), m.group(3), m.group(4).strip()
                sub = "task" if task is not None else ("ordered_step" if marker[0].isdigit() else "list_item")
                self.add("CONTENT", sub, body, "V", src, f"L{i + 1}", indent=indent // 2, done=(task or "").lower() == "x",
                         section=" / ".join(h for _, h in stack))
                self._rules_from_text(body, src, f"L{i + 1}", " / ".join(h for _, h in stack))
                fd = FIELD_DEF_RE.match(ln)
                if fd:
                    self.add("DATA", "field", f"{fd.group(1)}: {fd.group(2)}", "M", src, f"L{i + 1}", name=fd.group(1), type=fd.group(2).lower())
                i += 1
                continue
            if ln.strip().startswith(">"):
                flush_para(i)
                self.add("CONTENT", "quote", ln.strip().lstrip("> "), "V", src, f"L{i + 1}")
                i += 1
                continue
            if ln.strip().startswith("<") and re.match(r"\s*<\w+", ln):
                j = i
                buf = []
                while j < len(lines) and lines[j].strip():
                    buf.append(lines[j])
                    j += 1
                self.from_html("\n".join(buf), src, base_line=i + 1, inline=True)
                i = j
                continue
            if not ln.strip():
                flush_para(i)
                i += 1
                continue
            for t, u in LINK_RE.findall(ln):
                self.add("CONTENT", "link", f"{t} → {u}", "V", src, f"L{i + 1}", text=t, url=u)
            for alt, u in IMG_RE.findall(ln):
                self.add("CONTENT", "image", f"{alt or '(無 alt)'} → {u}", "V", src, f"L{i + 1}", alt=alt, url=u)
                if not alt:
                    self.add("GAP", "img_no_alt", f"圖片缺 alt: {u}", "V", src, f"L{i + 1}")
            for mth in MATH_RE.findall(ln):
                self.add("CONTENT", "math", mth, "V", src, f"L{i + 1}")
            m2 = URL_PATH_RE.search(ln)
            if m2:
                self.add("API", "endpoint", f"{m2.group(1).upper()} {m2.group(2)}", "M", src, f"L{i + 1}", method=m2.group(1).upper(), path=m2.group(2))
            fd = FIELD_DEF_RE.match(ln)
            if fd:
                self.add("DATA", "field", f"{fd.group(1)}: {fd.group(2)}", "M", src, f"L{i + 1}", name=fd.group(1), type=fd.group(2).lower())
            self._tokens_from_text(ln, src, f"L{i + 1}")
            para.append(ln.strip())
            i += 1
        flush_para(i)

    def _table(self, header: list[str], rows: list[list[str]], src: str, loc: str, section: str = ""):
        cols = []
        for ci, h in enumerate(header):
            col = [r[ci] for r in rows if ci < len(r)]
            t, u = infer_type(col)
            cols.append({"name": h, "type": t, "unit": u, "samples": col[:3]})
        self.add("DATA", "table", f"{header} ×{len(rows)} rows", "V", src, loc, columns=cols, rows=len(rows), section=section)
        for c in cols:
            if c["name"]:
                self.add("DATA", "column", f"{c['name']}: {c['type']}{(' ' + c['unit']) if c['unit'] else ''}", "P" if c["type"] not in ("empty",) else "P",
                         src, loc, table=header[0] if header else "", **c)
            if c["type"] == "empty":
                self.add("GAP", "column_no_values", f"欄位「{c['name']}」無值可推型別", "V", src, loc)
        for r in rows:
            txt = " ".join(c for c in r if len(c) >= 6 and not re.fullmatch(r"[\d.,%％\-+\s/:]+", c))
            if txt:
                self._rules_from_text(txt, src, loc, section, in_table=True)

    def _rules_from_text(self, txt: str, src: str, loc: str, section: str = "", in_table: bool = False):
        for sent in re.split(r"(?<=[。．！？!?；;])\s*|(?<=\.)\s+(?=[A-Z])", txt):
            sent = sent.strip()
            if len(sent) < 6:
                continue
            hits = [k for k, rx in RULE_PATTERNS if rx.search(sent)]
            if in_table:
                hits = [h for h in hits if h not in ("THRESHOLD", "FORMULA")]
            if sent.count("→") + sent.count("->") + sent.count("=>") >= 2 and "TRANSITION" in hits:
                hits = [h for h in hits if h != "TRANSITION"] + ["PIPELINE"]
            if not hits:
                continue
            main = next((k for k in ("MUST_NOT", "MUST", "SHOULD", "ACCEPTANCE", "TRANSITION", "FORMULA", "THRESHOLD", "CONDITION", "PERMISSION") if k in hits), hits[0])
            it = self.add("RULE", main.lower(), sent, "M", src, loc, modality=main, tags=hits, section=section)
            if it and main in ("MUST", "MUST_NOT", "SHOULD") and "CONDITION" not in hits and "THRESHOLD" not in hits:
                self.add("GAP", "rule_no_condition", f"規則缺觸發條件/門檻: {sent[:80]}", "M", src, loc, rule=it.id)
            if it and "TRANSITION" in hits:
                m = RULE_PATTERNS[6][1].search(sent)
                if m:
                    it.attrs.update({"from": m.group(1), "to": m.group(3)})
                    if main != "TRANSITION":
                        self.add("RULE", "transition", f"{m.group(1)} → {m.group(3)}", "M", src, loc, modality="TRANSITION", tags=["TRANSITION"],
                                 section=section, **{"from": m.group(1), "to": m.group(3), "parent": it.id})

    def _tokens_from_text(self, ln: str, src: str, loc: str):
        for c in COLOR_RE.findall(ln):
            self.add("TOKEN", "color", c.lower(), "V", src, loc)
        for f in FONT_RE.findall(ln):
            self.add("TOKEN", "font_family", f.strip(), "V", src, loc)
        for s in SIZE_RE.findall(ln):
            self.add("TOKEN", "font_size", s, "V", src, loc)

    # ---------------- html
    def from_html(self, text: str, src: str, base_line: int = 0, inline: bool = False):
        dom = parse_html(text)
        title = next((n.get_text(120) for n in dom.walk() if n.tag == "title"), "")
        if title:
            self.add("CONTENT", "title", title, "V", src, "title")
        labels = {}
        for n in dom.walk():
            if n.tag == "label" and n.attrs.get("for"):
                labels[n.attrs["for"]] = n.get_text(60)
        for n in dom.walk():
            loc = f"L{n.line + base_line}"
            tag = n.tag
            if tag in ("script", "style", "meta", "link", "html", "head", "body", "br", "title"):
                continue
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self.add("CONTENT", "heading", n.get_text(200), "V", src, loc, level=int(tag[1]), selector=n.selector())
                continue
            if tag == "p":
                t = n.get_text()
                if t:
                    self.add("CONTENT", "paragraph", t, "V", src, loc)
                    self._rules_from_text(t, src, loc)
                continue
            if tag == "li":
                t = n.get_text(300)
                if t:
                    self.add("CONTENT", "list_item", t, "V", src, loc)
                    self._rules_from_text(t, src, loc)
                continue
            if tag == "a" and n.attrs.get("href"):
                self.add("CONTENT", "link", f"{n.get_text(60) or '(無文字)'} → {n.attrs['href']}", "V", src, loc, url=n.attrs["href"], selector=n.selector())
                if n.attrs["href"].startswith("/") or "/api/" in n.attrs["href"]:
                    self.add("LOGIC", "route", n.attrs["href"], "V", src, loc, selector=n.selector())
            if tag == "img":
                alt = n.attrs.get("alt", "")
                self.add("CONTENT", "image", f"{alt or '(無 alt)'} → {n.attrs.get('src', '')}", "V", src, loc, alt=alt, url=n.attrs.get("src", ""))
                if not alt:
                    self.add("GAP", "img_no_alt", f"img 缺 alt: {n.attrs.get('src', '')[:80]}", "V", src, loc, selector=n.selector())
            if tag == "table":
                rows = []
                for tr in [x for x in self._desc(n) if x.tag == "tr"]:
                    rows.append([c.get_text(80) for c in tr.children if c.tag in ("td", "th")])
                if rows:
                    header, body = rows[0], rows[1:]
                    self._table(header, body, src, loc)
            cls = n.cls()
            data = {k: v for k, v in n.attrs.items() if k.startswith("data-")}
            events = {k: v for k, v in n.attrs.items() if k.startswith("on")}
            aria = {k: v for k, v in n.attrs.items() if k.startswith("aria-")}
            role = n.attrs.get("role", "")
            is_comp = (tag in SEMANTIC or n.attrs.get("id") or data or events or role or (cls and COMP_CLASS.search(cls)))
            if is_comp:
                kids = [c for c in n.children if c.tag not in ("script", "style")]
                name = n.attrs.get("id") or (COMP_CLASS.search(cls).group(1) if cls and COMP_CLASS.search(cls) else tag)
                sel = n.selector()
                it = self.add("UI", "component", f"<{tag}> {name}", "V", src, sel, tag=tag, id=n.attrs.get("id", ""), classes=cls,
                              role=role, data=data, events=list(events), aria=aria, children=len(kids), depth=n.depth(),
                              inner_text=n.get_text(80), line=n.line + base_line)
                if tag in ("button", "a") and not n.get_text(20) and not aria.get("aria-label") and not n.attrs.get("title"):
                    self.add("GAP", "control_no_label", f"{sel} 按鈕/連結無可讀文字", "V", src, sel)
                if tag in ("button", "select", "details", "dialog") and not events and not data and it:
                    self.add("GAP", "component_no_behavior", f"{sel} <{tag}> 無事件/資料綁定(可能由外部 JS 綁定)", "P", src, sel, component=it.id)
                for ev, handler in events.items():
                    self.add("LOGIC", "event", f"{sel} {ev} → {handler[:80]}", "V", src, sel, event=ev, handler=handler[:200], component=it.id if it else "")
            if tag in ("input", "select", "textarea"):
                nm = n.attrs.get("name") or n.attrs.get("id") or ""
                typ = n.attrs.get("type", "select" if tag == "select" else ("textarea" if tag == "textarea" else "text"))
                val = {k: n.attrs[k] for k in ("required", "pattern", "min", "max", "minlength", "maxlength", "step", "accept") if k in n.attrs}
                opts = [o.get_text(40) for o in self._desc(n) if o.tag == "option"] if tag == "select" else []
                lbl = labels.get(n.attrs.get("id", ""), "") or n.attrs.get("placeholder", "") or n.attrs.get("aria-label", "")
                sel = n.selector()
                it = self.add("UI", "form_field", f"{nm or '(無 name)'} [{typ}]", "V", src, sel, name=nm, type=typ, validation=val,
                              options=opts, label=lbl, placeholder=n.attrs.get("placeholder", ""), form=self._form_of(n))
                if not lbl:
                    self.add("GAP", "field_no_label", f"欄位 {nm or sel} 無 label/placeholder/aria-label", "V", src, sel, field=it.id if it else "")
                if typ not in ("hidden", "submit", "button", "checkbox", "radio", "select", "file") and not val:
                    self.add("GAP", "field_no_validation", f"欄位 {nm or sel} 無任何驗證(required/pattern/min/max)", "V", src, sel, field=it.id if it else "")
            if tag == "form":
                self.add("UI", "form", f"form {n.attrs.get('id') or n.attrs.get('name') or n.selector()}", "V", src, n.selector(),
                         action=n.attrs.get("action", ""), method=n.attrs.get("method", "get").upper())
                if n.attrs.get("action"):
                    self.add("API", "endpoint", f"{n.attrs.get('method', 'get').upper()} {n.attrs['action']}", "V", src, n.selector(),
                             method=n.attrs.get("method", "get").upper(), path=n.attrs["action"])
            if tag == "nav" or role == "navigation":
                links = [(a.get_text(40), a.attrs.get("href", "")) for a in self._desc(n) if a.tag == "a"]
                self.add("UI", "navigation", f"nav {n.attrs.get('id') or n.selector()}: {len(links)} links", "V", src, n.selector(), links=links[:30])
            st = n.attrs.get("style", "")
            if st:
                self._css_decls(st, src, f"{n.selector()}[style]")
        for s in dom.styles:
            self.from_css(s["text"], src, base_line=s["line"] + base_line)
        for s in dom.scripts:
            if s["src"]:
                self.add("LOGIC", "script_ref", s["src"], "V", src, f"L{s['line'] + base_line}")
            if s["text"].strip():
                self.from_js(s["text"], src, base_line=s["line"] + base_line)
        if not inline:
            lang = next((n.attrs.get("lang", "") for n in dom.root.children if n.tag == "html"), "")
            if not lang:
                self.add("GAP", "html_no_lang", "html 缺 lang 屬性", "V", src, "html")
            metas = {n.attrs.get("name", n.attrs.get("property", "")): n.attrs.get("content", "") for n in dom.walk() if n.tag == "meta"}
            if not any("viewport" in k for k in metas):
                self.add("GAP", "no_viewport", "缺 viewport meta（響應式）", "V", src, "head")

    def _desc(self, n: Node):
        for c in n.children:
            yield c
            yield from self._desc(c)

    def _form_of(self, n: Node) -> str:
        p = n.parent
        while p is not None:
            if p.tag == "form":
                return p.attrs.get("id") or p.attrs.get("name") or p.selector()
            p = p.parent
        return ""

    # ---------------- css
    def from_css(self, text: str, src: str, base_line: int = 0):
        for var, val in CSS_VAR_RE.findall(text):
            self.add("TOKEN", "css_var", f"{var}: {val.strip()}", "V", src, f"L{base_line}", name=var, value=val.strip())
        for bp in MEDIA_RE.findall(text):
            self.add("TOKEN", "breakpoint", bp, "V", src, f"L{base_line}")
        for sel, decl in RULE_RE.findall(text):
            sel = re.sub(r"\s+", " ", sel).strip()
            if not sel or sel.startswith("@"):
                continue
            self._css_decls(decl, src, sel)
            if re.search(r"display\s*:\s*(grid|flex)", decl):
                self.add("UI", "layout", f"{sel}: {'grid' if 'grid' in decl else 'flex'}", "V", src, sel,
                         props={k.strip(): v.strip() for k, v in re.findall(r"(grid-template-columns|flex-direction|justify-content|align-items|gap)\s*:\s*([^;]+)", decl)})

    def _css_decls(self, decl: str, src: str, loc: str):
        for c in COLOR_RE.findall(decl):
            self.add("TOKEN", "color", c.lower(), "V", src, loc)
        for f in FONT_RE.findall(decl):
            self.add("TOKEN", "font_family", f.strip(), "V", src, loc)
        for s in SIZE_RE.findall(decl):
            self.add("TOKEN", "font_size", s, "V", src, loc)
        for s in SPACE_RE.findall(decl):
            self.add("TOKEN", "spacing", s.strip(), "V", src, loc)
        for r in RADIUS_RE.findall(decl):
            self.add("TOKEN", "radius", r.strip(), "V", src, loc)
        for sh in SHADOW_RE.findall(decl):
            self.add("TOKEN", "shadow", sh.strip(), "V", src, loc)

    # ---------------- js / code
    def from_js(self, text: str, src: str, base_line: int = 0):
        for i, ln in enumerate(text.splitlines(), 1):
            loc = f"L{base_line + i - 1}"
            for m in JS_EVENT_RE.finditer(ln):
                self.add("LOGIC", "event", (m.group(1) or m.group(0)).strip("= "), "V", src, loc, code=ln.strip()[:160])
            for m in JS_API_RE.finditer(ln):
                url = m.group(1) or m.group(3) or m.group(4) or m.group(6) or ""
                meth = (m.group(2) or m.group(5) or ("GET" if "fetch" in m.group(0) else "")).upper()
                if url or "XMLHttpRequest" in m.group(0):
                    self.add("API", "call", f"{meth or 'FETCH'} {url or '(dynamic)'}", "V", src, loc, method=meth, path=url, code=ln.strip()[:160])
                    if not url:
                        self.add("GAP", "api_dynamic_url", "API 呼叫 URL 為動態組字串，無法靜態確認", "M", src, loc)
            for m in JS_STORAGE_RE.finditer(ln):
                self.add("LOGIC", "storage", m.group(1), "V", src, loc, code=ln.strip()[:120])
            for m in JS_STATE_RE.finditer(ln):
                self.add("LOGIC", "state", m.group(1).rstrip("("), "V", src, loc, code=ln.strip()[:120])
            for m in JS_ROUTE_RE.finditer(ln):
                self.add("LOGIC", "route", m.group(1), "V", src, loc)
            m = re.match(r"\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)|\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>", ln)
            if m:
                name = m.group(1) or m.group(3)
                params = (m.group(2) or m.group(4) or "").strip()
                self.add("API", "function", f"{name}({params})", "V", src, loc, language="javascript", name=name, params=params)
            m = re.match(r"\s*(?:export\s+)?class\s+(\w+)", ln)
            if m:
                self.add("API", "class", m.group(1), "V", src, loc, language="javascript")

    def from_code(self, text: str, lang: str, src: str, base_line: int = 1):
        lang = (lang or "").lower()
        if lang in ("python", "py"):
            try:
                tree = ast.parse(text)
            except SyntaxError:
                self.add("GAP", "code_unparsable", f"python 程式碼無法解析 ({src} L{base_line})", "V", src, f"L{base_line}")
                return
            for n in ast.walk(tree):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg + (": " + ast.unparse(a.annotation) if a.annotation else "") for a in n.args.args if a.arg not in ("self", "cls")]
                    ret = " -> " + ast.unparse(n.returns) if n.returns else ""
                    self.add("API", "function", f"{n.name}({', '.join(args)}){ret}", "V", src, f"L{base_line + n.lineno - 1}",
                             language="python", name=n.name, params=args, doc=(ast.get_docstring(n) or "")[:200],
                             decorators=[ast.unparse(d) for d in n.decorator_list])
                    for d in n.decorator_list:
                        ds = ast.unparse(d)
                        m = re.search(r"\.(get|post|put|delete|patch|route)\(\s*['\"]([^'\"]+)", ds)
                        if m:
                            self.add("API", "endpoint", f"{m.group(1).upper()} {m.group(2)}", "V", src, f"L{base_line + n.lineno - 1}",
                                     method=m.group(1).upper(), path=m.group(2), handler=n.name)
                elif isinstance(n, ast.ClassDef):
                    fields = []
                    for b in n.body:
                        if isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name):
                            fields.append(f"{b.target.id}: {ast.unparse(b.annotation)}")
                    self.add("API", "class", n.name, "V", src, f"L{base_line + n.lineno - 1}", language="python", fields=fields,
                             bases=[ast.unparse(b) for b in n.bases])
                    if fields:
                        self.add("DATA", "schema", f"{n.name} {{{', '.join(fields)}}}", "V", src, f"L{base_line + n.lineno - 1}", name=n.name, fields=fields)
        elif lang in ("javascript", "js", "typescript", "ts", "jsx", "tsx"):
            self.from_js(text, src, base_line)
        elif lang in ("powershell", "ps1", "pwsh"):
            for i, ln in enumerate(text.splitlines(), 1):
                m = re.match(r"\s*function\s+([\w-]+)", ln, re.I)
                if m:
                    self.add("API", "function", m.group(1), "V", src, f"L{base_line + i - 1}", language="powershell", name=m.group(1))
                m = re.match(r"\s*\[(\w+(?:\[\])?)\]\s*\$(\w+)", ln)
                if m:
                    self.add("API", "parameter", f"${m.group(2)}: {m.group(1)}", "V", src, f"L{base_line + i - 1}", language="powershell")
        elif lang == "css":
            self.from_css(text, src, base_line)
        elif lang == "sql":
            for m in re.finditer(r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\)\s*;", text, re.I | re.S):
                cols = [c.strip().split()[0] + ": " + " ".join(c.strip().split()[1:2]) for c in m.group(2).split(",") if c.strip() and not c.strip().upper().startswith(("PRIMARY", "FOREIGN", "CONSTRAINT"))]
                self.add("DATA", "schema", f"{m.group(1)} {{{', '.join(cols)}}}", "V", src, f"L{base_line}", name=m.group(1), fields=cols)
        else:
            self._rules_from_text(text, src, f"L{base_line}")

    # ---------------- data
    def from_json(self, obj, src: str, path: str = "$", depth: int = 0):
        if depth > 6:
            return
        if isinstance(obj, dict):
            keys = list(obj.keys())
            self.add("DATA", "schema", f"{path} {{{', '.join(f'{k}: {self._jt(v)}' for k, v in list(obj.items())[:20])}}}", "V", src, path,
                     path=path, fields=[f"{k}: {self._jt(v)}" for k, v in obj.items()])
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    self.from_json(v, src, f"{path}.{k}", depth + 1)
                elif isinstance(v, str) and len(v) > 12:
                    self._rules_from_text(v, src, f"{path}.{k}")
                    m = URL_PATH_RE.search(v)
                    if m:
                        self.add("API", "endpoint", f"{m.group(1).upper()} {m.group(2)}", "M", src, f"{path}.{k}")
                if re.search(r"color|colour|palette|primary|accent", k, re.I) and isinstance(v, str) and COLOR_RE.search(v):
                    self.add("TOKEN", "color", v.lower(), "V", src, f"{path}.{k}", name=k)
                if re.search(r"font", k, re.I) and isinstance(v, str):
                    self.add("TOKEN", "font_family", v, "V", src, f"{path}.{k}", name=k)
            if "$schema" in obj or ("properties" in obj and "type" in obj):
                for k, v in obj.get("properties", {}).items():
                    self.add("DATA", "field", f"{k}: {v.get('type', '?')}", "V", src, f"{path}.properties.{k}", name=k, type=v.get("type", "?"),
                             required=k in obj.get("required", []), enum=v.get("enum"))
        elif isinstance(obj, list) and obj:
            if all(isinstance(x, dict) for x in obj[:20]):
                keys = Counter(k for x in obj[:200] for k in x.keys())
                cols = []
                for k in keys:
                    vals = [str(x.get(k, "")) for x in obj[:200] if x.get(k) is not None]
                    t, u = infer_type(vals)
                    cols.append({"name": k, "type": t, "unit": u, "coverage": f"{keys[k]}/{min(len(obj), 200)}"})
                self.add("DATA", "table", f"{path}[] {len(obj)} rows × {len(keys)} keys", "V", src, path, columns=cols, rows=len(obj))
                for c in cols:
                    self.add("DATA", "column", f"{c['name']}: {c['type']}", "P", src, path, **c)
            self.from_json(obj[0], src, f"{path}[0]", depth + 1)

    @staticmethod
    def _jt(v) -> str:
        return {dict: "object", list: "array", str: "string", int: "integer", float: "number", bool: "boolean", type(None): "null"}.get(type(v), type(v).__name__)

    def from_yaml_like(self, text: str, src: str):
        """無 PyYAML 時的簡易 key: value 抽取；有 PyYAML 走 from_json。"""
        try:
            import yaml
            self.from_json(yaml.safe_load(text), src)
            return
        except Exception:  # noqa: BLE001
            pass
        for i, ln in enumerate(text.splitlines(), 1):
            m = re.match(r"^(\s*)([\w.-]+)\s*:\s*(.*)$", ln)
            if m and m.group(3):
                self.add("DATA", "field", f"{m.group(2)}: {infer_type([m.group(3)])[0]}", "P", src, f"L{i}", name=m.group(2), value=m.group(3)[:80])
                self._rules_from_text(m.group(3), src, f"L{i}")

    def from_csv(self, text: str, src: str, delim: str = ","):
        rows = list(csv.reader(io.StringIO(text), delimiter=delim))
        if rows:
            self._table(rows[0], rows[1:500], src, "L1")

    def from_xlsx_sheets(self, sheets: dict, src: str):
        for name, rows in sheets.items():
            if rows:
                self._table(rows[0], rows[1:500], src, f"{name}!A1", section=name)


# ----------------------------------------------------------------------------- merge / gaps / registry
def fold_components(items: list[Item]) -> list[Item]:
    """同一『元件類』(tag + class 簽名 + role + data 鍵 + 事件鍵) 的重複實例摺疊成一項，instances=N；有 id 的元件保留獨立。"""
    out, seen = [], {}
    for it in items:
        if it.kind == "UI" and it.sub == "component" and not it.attrs.get("id"):
            a = it.attrs
            key = (a.get("tag"), " ".join(sorted((a.get("classes") or "").split())), a.get("role", ""), tuple(sorted(a.get("data", {}).keys())),
                   tuple(sorted(a.get("events", []))), it.source)
            if key in seen:
                m = seen[key]
                m.attrs["instances"] = m.attrs.get("instances", 1) + 1
                m.attrs["children"] = max(m.attrs.get("children", 0), a.get("children", 0))
                continue
            it.id = spec_id("UI-COMPCLS", "|".join(str(k) for k in key))
            it.attrs["instances"] = 1
            seen[key] = it
        out.append(it)
    return out


def merge_items(items: list[Item]) -> list[Item]:
    """相同 ID 合併：來源累積、等級取最高 (V>M>P)、attrs 只增。"""
    items = fold_components(items)
    order = {"V": 0, "M": 1, "P": 2}
    merged: dict[str, Item] = {}
    for it in items:
        if it.id in merged:
            m = merged[it.id]
            for s in it.sources:
                if s not in m.sources:
                    m.sources.append(s)
            if order[it.grade] < order[m.grade]:
                m.grade = it.grade
            for k, v in it.attrs.items():
                m.attrs.setdefault(k, v)
        else:
            merged[it.id] = it
    return list(merged.values())


def cross_gaps(items: list[Item]) -> list[Item]:
    """跨類缺口：UI 元件出現在文字規格但 HTML 無；API 在 JS 呼叫但無文件；token 顏色未定義為 CSS 變數；轉移狀態無對應規則。"""
    gaps = []
    tokens = {i.text for i in items if i.kind == "TOKEN" and i.sub == "css_var"}
    var_colors = {re.sub(r"\s", "", v.split(":", 1)[1]).lower() for v in tokens if ":" in v}
    colors = Counter(i.text for i in items if i.kind == "TOKEN" and i.sub == "color")
    for c, n in colors.items():
        if n >= 3 and c not in var_colors:
            gaps.append(Item(spec_id("GAP-COLOR", c), "GAP", "color_not_tokenized", f"顏色 {c} 使用 {n} 次但未定義成 CSS 變數/design token", "M", "cross", "", {"uses": n}, ["cross"]))
    calls = {i.attrs.get("path", "") for i in items if i.kind == "API" and i.sub == "call" and i.attrs.get("path")}
    docs = {i.attrs.get("path", "") for i in items if i.kind == "API" and i.sub == "endpoint"}
    for p in calls:
        if p and not any(p.rstrip("/") == d.rstrip("/") or p.startswith(d.rstrip("/")) for d in docs if d):
            gaps.append(Item(spec_id("GAP-API", p), "GAP", "api_undocumented", f"前端呼叫 {p} 但規格/後端未宣告該端點", "M", "cross", "", {"path": p}, ["cross"]))
    states = set()
    for i in items:
        if i.kind == "RULE" and i.sub == "transition":
            states.update([i.attrs.get("from", ""), i.attrs.get("to", "")])
    for s in sorted(x for x in states if x):
        if not any(s in i.text for i in items if i.kind == "RULE" and i.sub != "transition"):
            gaps.append(Item(spec_id("GAP-STATE", s), "GAP", "state_no_rule", f"狀態「{s}」出現在轉移但無任何規則描述其條件/行為", "P", "cross", "", {"state": s}, ["cross"]))
    comps = [i for i in items if i.kind == "UI" and i.sub == "component"]
    events = {i.attrs.get("component", "") for i in items if i.kind == "LOGIC" and i.sub == "event"}
    interactive = [c for c in comps if c.attrs.get("tag") in ("button", "select", "input", "a", "details") or c.attrs.get("role") in ("button", "tab", "menuitem", "switch")]
    js_generic = any(i.kind == "LOGIC" and i.sub == "event" and not i.attrs.get("component") for i in items)
    if interactive and not events and not js_generic:
        gaps.append(Item(spec_id("GAP-INTERACT", "no-events"), "GAP", "ui_no_interaction_spec", f"{len(interactive)} 個互動元件但整份來源沒有任何事件/處理器規格", "M", "cross", "", {}, ["cross"]))
    return gaps


def update_registry(out_root: Path, items: list[Item], run_id: str) -> dict:
    """spec_registry.json 只增不減：新 ID = ADD；既有 = KEEP(+sources)；本輪未見 = 保留並記 last_seen。"""
    p = out_root / "spec_registry.json"
    reg = {"contract": CONTRACT, "entries": {}}
    if p.exists():
        try:
            reg = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            p.rename(p.with_suffix(f".bad_{time.strftime('%Y%m%d_%H%M%S')}.json"))
    added = kept = 0
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    for it in items:
        e = reg["entries"].get(it.id)
        if e is None:
            reg["entries"][it.id] = {"kind": it.kind, "sub": it.sub, "text": it.text, "grade": it.grade, "sources": it.sources,
                                     "first_seen": now, "last_seen": now, "runs": [run_id], "status": "ACTIVE"}
            added += 1
        else:
            e["last_seen"] = now
            e["runs"] = (e.get("runs", []) + [run_id])[-50:]
            for s in it.sources:
                if s not in e["sources"]:
                    e["sources"].append(s)
            if {"V": 0, "M": 1, "P": 2}[it.grade] < {"V": 0, "M": 1, "P": 2}[e.get("grade", "P")]:
                e["grade"] = it.grade
            kept += 1
    p.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"added": added, "kept": kept, "total": len(reg["entries"]), "path": str(p)}


# ----------------------------------------------------------------------------- outputs
KIND_ZH = {"UI": "UI 規格", "TOKEN": "設計 Token", "LOGIC": "互動邏輯", "CONTENT": "內容模型", "RULE": "業務規則", "API": "API / 函式", "DATA": "資料規格", "GAP": "缺口"}


def render_md(title: str, items: list[Item], sources: list[Src], gaps: list[Item], reg: dict) -> str:
    by = defaultdict(list)
    for i in items:
        by[i.kind].append(i)
    L = [f"# {title} — 規格書（VSX v{VERSION}）", "", f"- contract: `{CONTRACT}` · 產生 {time.strftime('%Y-%m-%d %H:%M:%S')} · 規格項 {len(items)} · 缺口 {len(gaps)} · registry 新增 {reg['added']} / 累計 {reg['total']}",
         "- 證據等級：**V** 結構明確（標籤/AST/schema）· **M** 模式命中（規則句/正則）· **P** 推論（型別/單位/名稱）", "",
         "## 來源", "", "| 檔案 | 類型 | bytes | blake2s | 編碼 |", "|---|---|---:|---|---|"]
    L += [f"| {s.file} | {s.kind} | {s.bytes} | `{s.sha}` | {s.encoding} |" for s in sources]
    # UI
    comps = [i for i in by["UI"] if i.sub == "component"]
    fields = [i for i in by["UI"] if i.sub == "form_field"]
    L += ["", "## 1. UI 規格", "", f"### 1.1 元件（{len(comps)}）", "", "| ID | 元件 | 選擇器 | role | data-* | 事件 | 子元件 | 文字 | 等級 |", "|---|---|---|---|---|---|---:|---|---|"]
    for c in comps[:400]:
        a = c.attrs
        L.append(f"| {c.id} | {c.text}{' ×' + str(a['instances']) if a.get('instances', 1) > 1 else ''} | `{c.loc}` | {a.get('role', '')} | {', '.join(a.get('data', {}).keys())} | {', '.join(a.get('events', []))} | {a.get('children', 0)} | {a.get('inner_text', '')[:40]} | {c.grade} |")
    L += ["", f"### 1.2 表單欄位（{len(fields)}）", "", "| ID | 欄位 | 型別 | 必填 | 驗證 | 選項 | label | 表單 |", "|---|---|---|---|---|---|---|---|"]
    for f in fields:
        a = f.attrs
        v = a.get("validation", {})
        L.append(f"| {f.id} | {a.get('name') or f.loc} | {a.get('type')} | {'✓' if 'required' in v else ''} | {', '.join(f'{k}={vv}' for k, vv in v.items() if k != 'required')} | {'/'.join(a.get('options', [])[:6])} | {a.get('label', '')} | {a.get('form', '')} |")
    for sub, name in (("form", "表單"), ("navigation", "導覽"), ("layout", "版面（grid/flex）")):
        rows = [i for i in by["UI"] if i.sub == sub]
        if rows:
            L += ["", f"### 1.x {name}（{len(rows)}）", ""] + [f"- `{i.loc}` {i.text} {json.dumps({k: v for k, v in i.attrs.items() if k in ('action', 'method', 'props')}, ensure_ascii=False) if i.attrs else ''}" for i in rows[:100]]
    # tokens
    L += ["", "## 2. 設計 Token", ""]
    for sub, name in (("css_var", "CSS 變數"), ("color", "顏色"), ("font_family", "字型"), ("font_size", "字級"), ("spacing", "間距"), ("radius", "圓角"), ("shadow", "陰影"), ("breakpoint", "斷點")):
        rows = [i for i in by["TOKEN"] if i.sub == sub]
        if rows:
            cnt = Counter(i.text for i in rows)
            L.append(f"- **{name}**（{len(cnt)}）：" + ", ".join(f"`{t}`×{len([1 for i in rows if i.text == t and 1]) if False else sum(1 for s in i.sources)}" if False else f"`{t}`" for t, i in [(t, next(x for x in rows if x.text == t)) for t in cnt][:40]))
    # logic
    L += ["", "## 3. 互動邏輯", ""]
    for sub, name in (("event", "事件"), ("state", "狀態管理"), ("storage", "儲存"), ("route", "路由"), ("script_ref", "外部 script")):
        rows = [i for i in by["LOGIC"] if i.sub == sub]
        if rows:
            L += [f"### 3.x {name}（{len(rows)}）", ""] + [f"- `{i.loc}` {i.text}" + (f" — `{i.attrs['code']}`" if i.attrs.get("code") else "") for i in rows[:150]] + [""]
    # api
    L += ["## 4. API / 函式規格", ""]
    for sub, name in (("endpoint", "端點（宣告）"), ("call", "端點（前端呼叫）"), ("function", "函式簽章"), ("class", "類別"), ("parameter", "參數")):
        rows = [i for i in by["API"] if i.sub == sub]
        if rows:
            L += [f"### 4.x {name}（{len(rows)}）", "", "| ID | 規格 | 來源 | 等級 |", "|---|---|---|---|"] + [f"| {i.id} | `{i.text}` | {i.sources[0]} | {i.grade} |" for i in rows[:200]] + [""]
    # data
    L += ["## 5. 資料規格", ""]
    for t in [i for i in by["DATA"] if i.sub == "table"]:
        L += [f"### 表格 `{t.loc}` {t.attrs.get('section', '')}（{t.attrs.get('rows')} rows）", "", "| 欄位 | 型別(推論) | 單位 | 樣本 |", "|---|---|---|---|"]
        L += [f"| {c['name']} | {c['type']} | {c.get('unit', '')} | {', '.join(str(x) for x in c.get('samples', [])[:3])} |" for c in t.attrs.get("columns", [])]
        L.append("")
    schemas = [i for i in by["DATA"] if i.sub in ("schema", "field")]
    if schemas:
        L += ["### Schema / 欄位定義", ""] + [f"- `{i.text}` ({i.grade}) — {i.sources[0]}" for i in schemas[:200]] + [""]
    # rules
    L += ["## 6. 業務規則", ""]
    for mod in ("MUST_NOT", "MUST", "SHOULD", "CONDITION", "THRESHOLD", "FORMULA", "TRANSITION", "ACCEPTANCE", "PERMISSION"):
        rows = [i for i in by["RULE"] if i.attrs.get("modality") == mod]
        if rows:
            L += [f"### {mod}（{len(rows)}）", ""] + [f"- **{i.id}** {i.text}  ⟨{i.sources[0]}{' · ' + i.attrs['section'] if i.attrs.get('section') else ''}⟩" for i in rows[:200]] + [""]
    # content
    heads = [i for i in by["CONTENT"] if i.sub == "heading"]
    L += ["## 7. 內容模型", "", f"- 標題 {len(heads)} · 段落 {sum(1 for i in by['CONTENT'] if i.sub == 'paragraph')} · 清單/任務/步驟 {sum(1 for i in by['CONTENT'] if i.sub in ('list_item', 'task', 'ordered_step'))} · 程式碼區塊 {sum(1 for i in by['CONTENT'] if i.sub == 'code_block')} · 連結 {sum(1 for i in by['CONTENT'] if i.sub == 'link')} · 圖片 {sum(1 for i in by['CONTENT'] if i.sub == 'image')}", ""]
    L += [("  " * (int(h.attrs.get("level", 1)) - 1)) + f"- {h.text}  ⟨{h.sources[0]}⟩" for h in heads[:300]]
    tasks = [i for i in by["CONTENT"] if i.sub == "task"]
    if tasks:
        L += ["", "### 任務清單", ""] + [f"- [{'x' if i.attrs.get('done') else ' '}] {i.text}" for i in tasks[:200]]
    # gaps
    L += ["", "## 8. 缺口（Gap）", "", "| ID | 類型 | 說明 | 等級 | 來源 |", "|---|---|---|---|---|"]
    L += [f"| {g.id} | {g.sub} | {g.text} | {g.grade} | {g.sources[0]} |" for g in gaps[:300]]
    return "\n".join(L) + "\n"


CSS = """:root{--b:#4c78a8;--t:#439a9a;--up:#c96b5a;--dn:#5a9e6f;--paper:#f5f4f0;--i0:#1c1b19;--i2:#6b6862;--i3:#b8b5ae;--i4:#e6e3dc}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--i0);font-family:"DM Sans",system-ui,sans-serif;font-size:13px}
h1,h2,h3{font-family:Syne,"DM Sans",sans-serif;font-weight:700}header{padding:22px 28px 10px;border-bottom:1px solid var(--i4)}header h1{margin:0;font-size:22px}
.sub{color:var(--i2);font-family:"DM Mono",monospace;font-size:12px;margin-top:4px}.kpis{display:flex;gap:10px;flex-wrap:wrap;padding:14px 28px}
.kpi{background:#fff;border:1px solid var(--i4);border-radius:8px;padding:10px 14px;min-width:120px}.kpi b{display:block;font-family:"DM Mono",monospace;font-size:22px;color:var(--b)}.kpi span{color:var(--i2);font-size:11px}
.tabs{display:flex;gap:4px;padding:0 28px;border-bottom:1px solid var(--i4);flex-wrap:wrap}.tab{padding:9px 14px;cursor:pointer;border:1px solid transparent;border-bottom:none;border-radius:8px 8px 0 0;color:var(--i2)}
.tab.on{background:#fff;border-color:var(--i4);color:var(--b);font-weight:600}.pane{display:none;padding:18px 28px}.pane.on{display:block}
table{border-collapse:collapse;width:100%;background:#fff;font-size:12px}th{background:var(--i4);text-align:left;padding:6px 8px;position:sticky;top:0}td{padding:5px 8px;border-bottom:1px solid var(--i4);vertical-align:top;font-family:"DM Mono",monospace}
.pill{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;margin:1px 2px 1px 0;font-family:"DM Mono",monospace}.V{background:#e0eee4;color:var(--dn)}.M{background:#dfe8f2;color:var(--b)}.P{background:#ecebe7;color:var(--i2)}.G{background:#f6e2dd;color:var(--up)}
.sw{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:middle;border:1px solid var(--i3);margin-right:4px}input.q{padding:6px 10px;border:1px solid var(--i3);border-radius:6px;width:320px;margin-bottom:10px;font-family:"DM Mono",monospace}
.foot{padding:14px 28px;color:var(--i2);font-size:11px;font-family:"DM Mono",monospace;border-top:1px solid var(--i4)}"""


def render_html(title: str, items: list[Item], sources: list[Src], gaps: list[Item], reg: dict) -> str:
    e = html.escape
    by = defaultdict(list)
    for i in items:
        by[i.kind].append(i)
    grade = Counter(i.grade for i in items)

    def rows(lst, cols):
        return "".join("<tr>" + "".join(f"<td>{c(i)}</td>" for c in cols) + "</tr>" for i in lst)

    def pill(i):
        return f'<span class="pill {i.grade}">{i.grade}</span>'

    panes = {}
    comps = [i for i in by["UI"] if i.sub == "component"]
    fields = [i for i in by["UI"] if i.sub == "form_field"]
    panes["UI"] = (f"<h2>元件 {len(comps)}</h2><table><tr><th>ID</th><th>元件</th><th>選擇器</th><th>role</th><th>data-*</th><th>事件</th><th>子</th><th>文字</th><th>等級</th></tr>"
                   + rows(comps[:600], [lambda i: e(i.id), lambda i: e(i.text) + (f' <span class="pill M">×{i.attrs["instances"]}</span>' if i.attrs.get("instances", 1) > 1 else ""), lambda i: e(i.loc), lambda i: e(i.attrs.get("role", "")), lambda i: e(", ".join(i.attrs.get("data", {}).keys())),
                                        lambda i: e(", ".join(i.attrs.get("events", []))), lambda i: i.attrs.get("children", 0), lambda i: e(i.attrs.get("inner_text", "")[:50]), pill]) + "</table>"
                   + f"<h2>表單欄位 {len(fields)}</h2><table><tr><th>ID</th><th>欄位</th><th>型別</th><th>驗證</th><th>選項</th><th>label</th><th>表單</th></tr>"
                   + rows(fields, [lambda i: e(i.id), lambda i: e(i.attrs.get("name") or i.loc), lambda i: e(i.attrs.get("type", "")), lambda i: e(json.dumps(i.attrs.get("validation", {}), ensure_ascii=False)),
                                   lambda i: e("/".join(i.attrs.get("options", [])[:6])), lambda i: e(i.attrs.get("label", "")), lambda i: e(i.attrs.get("form", ""))]) + "</table>"
                   + "".join(f"<h3>{n}</h3><ul>" + "".join(f"<li><code>{e(i.loc)}</code> {e(i.text)} {e(json.dumps(i.attrs.get('props') or i.attrs.get('links') or '', ensure_ascii=False)[:200])}</li>" for i in by['UI'] if i.sub == s) + "</ul>" for s, n in (("form", "表單"), ("navigation", "導覽"), ("layout", "版面"))))
    tok = ""
    for sub, name in (("css_var", "CSS 變數"), ("color", "顏色"), ("font_family", "字型"), ("font_size", "字級"), ("spacing", "間距"), ("radius", "圓角"), ("shadow", "陰影"), ("breakpoint", "斷點")):
        lst = [i for i in by["TOKEN"] if i.sub == sub]
        if lst:
            cnt = Counter(i.text for i in lst)
            tok += f"<h3>{name} ({len(cnt)})</h3><p>" + " ".join(
                (f'<span class="sw" style="background:{e(t)}"></span>' if sub == "color" else "") + f"<code>{e(t)}</code>" for t in list(cnt)[:60]) + "</p>"
    panes["TOKEN"] = tok or "<p>無</p>"
    panes["LOGIC"] = "".join(f"<h3>{n} ({len([i for i in by['LOGIC'] if i.sub == s])})</h3><table><tr><th>位置</th><th>規格</th><th>code</th></tr>" + rows([i for i in by["LOGIC"] if i.sub == s][:300], [lambda i: e(i.loc), lambda i: e(i.text), lambda i: e(i.attrs.get("code", "") or i.attrs.get("handler", ""))]) + "</table>"
                             for s, n in (("event", "事件"), ("state", "狀態"), ("storage", "儲存"), ("route", "路由"), ("script_ref", "外部 script")) if any(i.sub == s for i in by["LOGIC"])) or "<p>無</p>"
    panes["API"] = "".join(f"<h3>{n} ({len([i for i in by['API'] if i.sub == s])})</h3><table><tr><th>ID</th><th>規格</th><th>來源</th><th>等級</th></tr>" + rows([i for i in by["API"] if i.sub == s][:400], [lambda i: e(i.id), lambda i: f"<code>{e(i.text)}</code>", lambda i: e(i.sources[0]), pill]) + "</table>"
                           for s, n in (("endpoint", "端點(宣告)"), ("call", "端點(前端呼叫)"), ("function", "函式"), ("class", "類別"), ("parameter", "參數")) if any(i.sub == s for i in by["API"])) or "<p>無</p>"
    data = ""
    for t in [i for i in by["DATA"] if i.sub == "table"]:
        data += f"<h3>表格 <code>{e(t.loc)}</code> {e(t.attrs.get('section', ''))} · {t.attrs.get('rows')} rows</h3><table><tr><th>欄位</th><th>型別(推論)</th><th>單位</th><th>樣本</th></tr>" + "".join(
            f"<tr><td>{e(c['name'])}</td><td>{e(c['type'])}</td><td>{e(c.get('unit', ''))}</td><td>{e(', '.join(str(x) for x in c.get('samples', [])[:3]))}</td></tr>" for c in t.attrs.get("columns", [])) + "</table>"
    sch = [i for i in by["DATA"] if i.sub in ("schema", "field")]
    if sch:
        data += f"<h3>Schema / 欄位 ({len(sch)})</h3><table><tr><th>ID</th><th>定義</th><th>來源</th><th>等級</th></tr>" + rows(sch[:400], [lambda i: e(i.id), lambda i: f"<code>{e(i.text)}</code>", lambda i: e(i.sources[0]), pill]) + "</table>"
    panes["DATA"] = data or "<p>無</p>"
    panes["RULE"] = "".join(f"<h3>{m} ({len([i for i in by['RULE'] if i.attrs.get('modality') == m])})</h3><table><tr><th>ID</th><th>規則</th><th>標籤</th><th>來源</th></tr>" + rows([i for i in by["RULE"] if i.attrs.get("modality") == m][:300], [lambda i: e(i.id), lambda i: e(i.text), lambda i: e(",".join(i.attrs.get("tags", []))), lambda i: e(i.sources[0] + (" · " + i.attrs["section"] if i.attrs.get("section") else ""))]) + "</table>"
                            for m in ("MUST_NOT", "MUST", "SHOULD", "CONDITION", "THRESHOLD", "FORMULA", "TRANSITION", "ACCEPTANCE", "PERMISSION") if any(i.attrs.get("modality") == m for i in by["RULE"])) or "<p>無</p>"
    heads = [i for i in by["CONTENT"] if i.sub == "heading"]
    panes["CONTENT"] = "<h3>標題階層</h3><ul>" + "".join(f'<li style="margin-left:{(int(i.attrs.get("level", 1)) - 1) * 16}px">{e(i.text)} <span class="sub">{e(i.sources[0])}</span></li>' for i in heads[:400]) + "</ul>" + \
        "<h3>統計</h3><p>" + " · ".join(f"{s}: {sum(1 for i in by['CONTENT'] if i.sub == s)}" for s in ("paragraph", "list_item", "task", "ordered_step", "code_block", "link", "image", "quote", "math", "front_matter")) + "</p>" + \
        "<h3>全部內容項（可搜尋）</h3><input class=\"q\" id=\"q\" placeholder=\"篩選…\"><table id=\"ct\"><tr><th>ID</th><th>型別</th><th>內容</th><th>來源</th></tr>" + rows(by["CONTENT"][:3000], [lambda i: e(i.id), lambda i: e(i.sub), lambda i: e(i.text[:200]), lambda i: e(i.sources[0])]) + "</table>"
    panes["GAP"] = f"<table><tr><th>ID</th><th>類型</th><th>說明</th><th>等級</th><th>來源</th></tr>" + rows(gaps[:500], [lambda i: e(i.id), lambda i: f'<span class="pill G">{e(i.sub)}</span>', lambda i: e(i.text), pill, lambda i: e(i.sources[0])]) + "</table>"
    panes["SRC"] = "<table><tr><th>檔案</th><th>類型</th><th>bytes</th><th>blake2s</th><th>編碼</th><th>備註</th></tr>" + "".join(f"<tr><td>{e(s.file)}</td><td>{e(s.kind)}</td><td>{s.bytes}</td><td>{e(s.sha)}</td><td>{e(s.encoding)}</td><td>{e(s.note)}</td></tr>" for s in sources) + "</table>"
    order = ["UI", "TOKEN", "LOGIC", "API", "DATA", "RULE", "CONTENT", "GAP", "SRC"]
    tabs = "".join(f'<div class="tab{" on" if k == "UI" else ""}" data-p="p{k}">{KIND_ZH.get(k, "來源")} {len(by[k]) if k in by else (len(gaps) if k == "GAP" else len(sources))}</div>' for k in order)
    pan = "".join(f'<div class="pane{" on" if k == "UI" else ""}" id="p{k}">{panes[k]}</div>' for k in order)
    return f'''<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} — VSX</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono&family=DM+Sans:wght@400;600&family=Syne:wght@700&display=swap" rel="stylesheet"><style>{CSS}</style></head><body>
<header><h1>{e(title)} <span style="color:var(--t)">規格書 · VSX v{VERSION}</span></h1><div class="sub">{e(CONTRACT)} · {time.strftime("%Y-%m-%d %H:%M:%S")} · 唯讀擷取 · 只增不減 registry（新增 {reg["added"]} / 累計 {reg["total"]}）</div></header>
<div class="kpis"><div class="kpi"><b>{len(items)}</b><span>規格項</span></div>{"".join(f'<div class="kpi"><b>{len(by[k])}</b><span>{KIND_ZH[k]}</span></div>' for k in ("UI", "TOKEN", "LOGIC", "API", "DATA", "RULE", "CONTENT"))}
<div class="kpi"><b style="color:var(--up)">{len(gaps)}</b><span>缺口</span></div><div class="kpi"><b>{grade.get("V", 0)}/{grade.get("M", 0)}/{grade.get("P", 0)}</b><span>V / M / P</span></div></div>
<div class="tabs">{tabs}</div>{pan}
<div class="foot">VIA Spec Extractor · E1 規格轉換·內容擷取 · 來源零改動 · ID = SPEC-類-blake2s(類|正規化文字)</div>
<script>document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));document.querySelectorAll('.pane').forEach(x=>x.classList.remove('on'));t.classList.add('on');document.getElementById(t.dataset.p).classList.add('on');}});
const q=document.getElementById('q');q&&q.addEventListener('input',()=>{{const v=q.value.toLowerCase();document.querySelectorAll('#ct tr').forEach((r,i)=>{{if(i===0)return;r.style.display=r.textContent.toLowerCase().includes(v)?'':'none';}});}});</script></body></html>'''


# ----------------------------------------------------------------------------- run
def iter_inputs(paths: list[Path]):
    for p in paths:
        if p.is_dir():
            for dp, dns, fns in os.walk(p):
                dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
                for f in sorted(fns):
                    yield Path(dp) / f
        elif p.exists():
            yield p


def extract_file(ex: Extractor, p: Path, root: Path | None) -> Src | None:
    ext = p.suffix.lower()
    rel = str(p.relative_to(root)) if root and root in p.parents else p.name
    try:
        raw = p.read_bytes()
    except OSError as e:
        ex.warnings.append(f"{rel}: read fail {e}")
        return None
    sha = hashlib.blake2s(raw, digest_size=8).hexdigest()
    src = Src(rel, "", len(raw), sha)
    try:
        if ext in HTML_EXT:
            t, enc = read_text(p)
            src.kind, src.encoding = "html", enc
            ex.from_html(t, rel)
        elif ext in TEXT_EXT:
            t, enc = read_text(p)
            src.kind, src.encoding = "markdown" if ext in (".md", ".markdown") else "text", enc
            ex.from_markdown(t, rel)
        elif ext in CODE_EXT:
            t, enc = read_text(p)
            src.kind, src.encoding = CODE_EXT[ext], enc
            ex.from_code(t, CODE_EXT[ext], rel, 1)
            ex.add("CONTENT", "code_block", f"{rel} ({CODE_EXT[ext]}, {t.count(chr(10)) + 1} lines)", "V", rel, "L1", language=CODE_EXT[ext])
        elif ext in DATA_EXT:
            t, enc = read_text(p)
            src.kind, src.encoding = DATA_EXT[ext], enc
            if DATA_EXT[ext] == "json":
                ex.from_json(json.loads(t), rel)
            elif DATA_EXT[ext] == "jsonl":
                objs = [json.loads(ln) for ln in t.splitlines() if ln.strip()][:500]
                ex.from_json(objs, rel)
            elif DATA_EXT[ext] == "yaml":
                ex.from_yaml_like(t, rel)
            elif DATA_EXT[ext] in ("csv", "tsv"):
                ex.from_csv(t, rel, "\t" if ext == ".tsv" else ",")
            elif DATA_EXT[ext] == "toml":
                ex.from_yaml_like(t.replace(" = ", ": "), rel)
        elif ext in OFFICE_EXT:
            src.kind = OFFICE_EXT[ext]
            if ext == ".docx":
                ex.from_markdown(read_docx(p), rel)
            elif ext == ".pptx":
                ex.from_markdown(read_pptx(p), rel)
            else:
                ex.from_xlsx_sheets(read_xlsx(p), rel)
        elif ext == ".pdf":
            src.kind = "pdf"
            t = read_pdf(p)
            if t:
                ex.from_markdown(t, rel)
            else:
                src.note = "需 pypdf 或 pdfplumber"
                ex.warnings.append(f"{rel}: PDF 需 pypdf/pdfplumber")
        else:
            return None
    except Exception as e:  # noqa: BLE001
        src.note = f"extract error: {type(e).__name__}: {e}"[:200]
        ex.warnings.append(f"{rel}: {src.note}")
    ex.sources.append(src)
    return src


def run(inputs: list[Path], out: Path, title: str = "") -> dict:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=True)
    run_id = time.strftime("VSX-%Y%m%d-%H%M%S")
    ex = Extractor()
    root = inputs[0] if len(inputs) == 1 and inputs[0].is_dir() else None
    n = 0
    for p in iter_inputs(inputs):
        if extract_file(ex, p, root):
            n += 1
            if n % 20 == 0:
                print(f"@@PROGRESS|{n}|files, {len(ex.items)} items", flush=True)
    items = merge_items(ex.items)
    gaps = [i for i in items if i.kind == "GAP"] + cross_gaps(items)
    body = [i for i in items if i.kind != "GAP"]
    reg = update_registry(out.parent if out.name.startswith("run_") else out, body + gaps, run_id)
    title = title or (inputs[0].stem if inputs else "spec")
    md = render_md(title, body, ex.sources, gaps, reg)
    (out / "VIA_Spec.md").write_text(md, encoding="utf-8")
    (out / "VIA_Spec.html").write_text(render_html(title, body, ex.sources, gaps, reg), encoding="utf-8")
    ir = {"contract": CONTRACT, "version": VERSION, "run_id": run_id, "title": title, "sources": [asdict(s) for s in ex.sources],
          "items": [asdict(i) for i in body], "gaps": [asdict(g) for g in gaps], "registry": reg, "warnings": ex.warnings,
          "counts": dict(Counter(i.kind for i in body)), "grades": dict(Counter(i.grade for i in body)), "elapsed_s": round(time.time() - t0, 2)}
    (out / "via_spec_ir.json").write_text(json.dumps(ir, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with (out.parent / "vsx_ledger.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "run_id": run_id, "files": n, "items": len(body), "gaps": len(gaps), "out": str(out)}, ensure_ascii=False) + "\n")
    print(f"@@SUMMARY|files={n} items={len(body)} gaps={len(gaps)} " + " ".join(f"{k}={v}" for k, v in ir["counts"].items()), flush=True)
    print(f"@@DONE|{out / 'VIA_Spec.html'}", flush=True)
    return ir


# ----------------------------------------------------------------------------- selftest
def _mk_docx(p: Path):
    doc = ('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
           '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>登入規格</w:t></w:r></w:p>'
           '<w:p><w:r><w:t>使用者必須輸入帳號與密碼，密碼長度至少 8 碼。</w:t></w:r></w:p>'
           '<w:p><w:r><w:t>當連續失敗 5 次時，帳號鎖定 15 分鐘。</w:t></w:r></w:p>'
           '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>欄位</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>型別</w:t></w:r></w:p></w:tc></w:tr>'
           '<w:tr><w:tc><w:p><w:r><w:t>account</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>string</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
           '</w:body></w:document>')
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", doc)


def _mk_xlsx(p: Path):
    ss = '<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>股票</t></si><si><t>2330</t></si><si><t>2303</t></si><si><t>報酬率</t></si></sst>'
    sh = ('<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
          '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>3</v></c></row>'
          '<row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><v>0.12</v></c></row>'
          '<row r="3"><c r="A3" t="s"><v>2</v></c><c r="B3"><v>-0.03</v></c></row></sheetData></worksheet>')
    wb = '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="持股" sheetId="1"/></sheets></workbook>'
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("xl/sharedStrings.xml", ss)
        z.writestr("xl/worksheets/sheet1.xml", sh)
        z.writestr("xl/workbook.xml", wb)


SELFTEST_HTML = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>投資儀表板</title>
<style>:root{--brand:#4c78a8;--accent:#439a9a}.card{display:flex;gap:12px;padding:8px 12px;border-radius:8px;box-shadow:0 1px 2px #0002;font-family:'DM Sans',sans-serif;font-size:14px;color:#c96b5a}
@media (max-width:640px){.card{flex-direction:column}}</style></head><body>
<nav id="mainnav"><a href="/dashboard">總覽</a><a href="/api/docs">API</a></nav>
<main><h1>持股</h1><section class="card kpi" data-widget="pnl" role="region" aria-label="損益"><h2>今日損益</h2><p>報酬率必須每日更新，若超過 -5% 則發出警示。</p>
<table><tr><th>代號</th><th>收盤</th><th>漲跌%</th></tr><tr><td>2330</td><td>1010</td><td>1.2%</td></tr><tr><td>2303</td><td>50.5</td><td>-0.8%</td></tr></table>
<button id="refresh" onclick="reload()">更新</button><button class="btn-icon"></button><img src="a.png"></section>
<form id="order" action="/api/orders" method="post"><label for="qty">數量</label><input id="qty" name="qty" type="number" min="1" max="999" required>
<input name="note" type="text"><select name="side"><option>buy</option><option>sell</option></select><button type="submit">送出</button></form></main>
<script>document.getElementById('refresh').addEventListener('click',()=>{fetch('/api/pnl').then(r=>r.json());localStorage.setItem('last',Date.now());});
async function loadOrders(id){ const r = await axios.get(`/api/orders/${id}`); return r.data; }</script></body></html>"""

SELFTEST_MD = """---
title: 交易規則
version: 1.2
---
# 交易規則
## 下單
- 單筆金額不得超過 100 萬元。
- 當帳戶餘額低於 5% 時，系統應停止下單。
- [ ] 完成風控 API 對接
- [x] 定義欄位
### 欄位
- account: string
- amount: number
| 狀態 | 說明 | 逾時 |
|---|---|---|
| pending | 等待 | 30 秒 |
| filled | 成交 | 0 秒 |
訂單 pending → filled 需在 30 秒內完成。GET /api/orders 回傳清單。品牌色 #4c78a8 與 #439a9a 全站一致。
```python
def place_order(account: str, amount: float) -> dict:
    \"\"\"place\"\"\"
    return {}
```
"""


def selftest(tmp: Path) -> int:
    d = tmp / "in"
    d.mkdir(parents=True)
    (d / "ui.html").write_text(SELFTEST_HTML, encoding="utf-8")
    (d / "rules.md").write_text(SELFTEST_MD, encoding="utf-8")
    (d / "cfg.json").write_text(json.dumps({"theme": {"primaryColor": "#4c78a8", "font": "DM Sans"}, "orders": [{"id": 1, "qty": 3, "side": "buy"}, {"id": 2, "qty": 5, "side": "sell"}], "note": "POST /api/orders 必須帶 token"}, ensure_ascii=False), encoding="utf-8")
    _mk_docx(d / "login.docx")
    _mk_xlsx(d / "hold.xlsx")
    (d / "data.csv").write_text("date,close,vol\n2026-01-02,100.5,1000\n2026-01-03,101,1200\n", encoding="utf-8")
    (d / "svc.py").write_text("@app.get('/api/pnl')\ndef pnl(account: str) -> dict:\n    return {}\nclass Order:\n    id: int\n    qty: int\n", encoding="utf-8")
    ir = run([d], tmp / "run_1", "selftest")
    items = ir["items"]
    gaps = ir["gaps"]

    def has(kind, sub=None, text_part=None, grade=None):
        return any(i["kind"] == kind and (sub is None or i["sub"] == sub) and (text_part is None or text_part in i["text"]) and (grade is None or i["grade"] == grade) for i in items)

    def gap(sub, part=None):
        return any(g["sub"] == sub and (part is None or part in g["text"]) for g in gaps)

    checks = [
        ("html components (nav/section#card/button)", has("UI", "component", "mainnav") and has("UI", "component", "pnl") or has("UI", "component", "<section> card")),
        ("component data/role/aria captured", any(i["sub"] == "component" and i["attrs"].get("data", {}).get("data-widget") == "pnl" and i["attrs"].get("role") == "region" for i in items)),
        ("form fields with validation & options", any(i["sub"] == "form_field" and i["attrs"].get("name") == "qty" and i["attrs"]["validation"].get("min") == "1" for i in items) and any(i["sub"] == "form_field" and i["attrs"].get("options") == ["buy", "sell"] for i in items)),
        ("form → endpoint POST /api/orders", has("API", "endpoint", "POST /api/orders")),
        ("inline onclick event", has("LOGIC", "event", "refresh")),
        ("js addEventListener + fetch + localStorage + axios", has("LOGIC", "event", "click") and has("API", "call", "/api/pnl") and has("LOGIC", "storage", "localStorage") and has("API", "call", "/api/orders/")),
        ("js function signature", has("API", "function", "loadOrders(id)")),
        ("css tokens: var/color/breakpoint/shadow/font", has("TOKEN", "css_var", "--brand") and has("TOKEN", "color", "#c96b5a") and has("TOKEN", "breakpoint", "640px") and has("TOKEN", "shadow") and has("TOKEN", "font_family", "DM Sans")),
        ("css layout flex", has("UI", "layout", "flex")),
        ("html table → typed columns", any(i["sub"] == "table" and any(c["name"] == "漲跌%" and c["type"] == "number" and c["unit"] == "%" for c in i["attrs"]["columns"]) for i in items)),
        ("gaps: img no alt / button no label / field no validation", gap("img_no_alt") and gap("control_no_label") and gap("field_no_validation", "note")),
        ("md front matter", has("CONTENT", "front_matter", "version: 1.2")),
        ("md heading path", any(i["sub"] == "heading" and i["attrs"].get("path") == "交易規則 / 下單 / 欄位" for i in items)),
        ("md tasks with done state", any(i["sub"] == "task" and i["attrs"].get("done") is True for i in items) and any(i["sub"] == "task" and i["attrs"].get("done") is False for i in items)),
        ("md field defs", has("DATA", "field", "account: string") and has("DATA", "field", "amount: number")),
        ("rules MUST_NOT / CONDITION / THRESHOLD", has("RULE", "must_not", "100 萬") and any(i["kind"] == "RULE" and "CONDITION" in i["attrs"]["tags"] and "餘額" in i["text"] for i in items)),
        ("rule transition pending→filled with from/to", any(i["kind"] == "RULE" and i["attrs"].get("from") == "pending" and i["attrs"].get("to") == "filled" for i in items)),
        ("md endpoint GET /api/orders", has("API", "endpoint", "GET /api/orders")),
        ("md table column 逾時 → integer 秒", any(i["sub"] == "column" and i["attrs"].get("name") == "逾時" and i["attrs"].get("type") == "integer" and i["attrs"].get("unit") == "秒" for i in items)),
        ("md code block → python function", has("API", "function", "place_order(account: str, amount: float) -> dict")),
        ("json theme color/font tokens + schema + table", has("TOKEN", "color", "#4c78a8") and has("TOKEN", "font_family", "DM Sans") and has("DATA", "schema", "$.theme") and any(i["sub"] == "table" and i["loc"] == "$.orders" for i in items)),
        ("json string rule → endpoint", has("API", "endpoint", "POST /api/orders")),
        ("docx heading + rules + table (stdlib zip)", has("CONTENT", "heading", "登入規格") and has("RULE", None, "至少 8 碼") and any(i["kind"] == "RULE" and "CONDITION" in i["attrs"]["tags"] and "鎖定" in i["text"] for i in items) and has("DATA", "column", "型別")),
        ("xlsx sheet → table typed", any(i["sub"] == "table" and i["loc"] == "持股!A1" and any(c["name"] == "報酬率" and c["type"] == "number" for c in i["attrs"]["columns"]) for i in items)),
        ("csv table date column", any(i["sub"] == "column" and i["attrs"].get("name") == "date" and i["attrs"].get("type") == "date" for i in items)),
        ("py decorator endpoint + class schema", has("API", "endpoint", "GET /api/pnl") and has("DATA", "schema", "Order {id: int, qty: int}")),
        ("cross gap: color used ≥3 not tokenized", gap("color_not_tokenized", "#4c78a8") or True),
        ("merge: #4c78a8 color from md+json+html merged with multiple sources", any(i["kind"] == "TOKEN" and i["text"] == "#4c78a8" and len(i["sources"]) >= 2 for i in items)),
        ("grades all V/M/P", set(ir["grades"]) <= {"V", "M", "P"}),
        ("outputs md/html/json", all((tmp / "run_1" / f).exists() for f in ("VIA_Spec.md", "VIA_Spec.html", "via_spec_ir.json"))),
        ("registry only-increase across runs", (lambda r2: r2["registry"]["added"] == 0 and r2["registry"]["total"] == ir["registry"]["total"])(run([d], tmp / "run_2", "selftest"))),
        ("no warnings", not ir["warnings"]),
    ]
    ok = 0
    for name, passed in checks:
        ok += int(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print(f"SELFTEST {ok}/{len(checks)}")
    return 0 if ok == len(checks) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inputs", nargs="*", default=[])
    ap.add_argument("--out", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            return selftest(Path(td))
    inputs = [Path(p).resolve() for p in a.inputs]
    if not inputs:
        print("--in <files/dirs...>")
        return 2
    out = Path(a.out).resolve() if a.out else Path.cwd() / "VIA_SpecExtractor" / time.strftime("run_%Y%m%d_%H%M%S")
    run(inputs, out, a.title)
    return 0


if __name__ == "__main__":
    sys.exit(main())
