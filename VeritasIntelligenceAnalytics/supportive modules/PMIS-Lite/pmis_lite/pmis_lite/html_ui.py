"""HTML UI / JavaScript 參數讀取（純 stdlib，離線）。

很多 ERP（含 SAP GUI for HTML、Web Dynpro）與網頁表單，資料藏在：
  - <table> 表格（報表匯出）
  - <input>/<select>/<textarea> 表單欄位（name/value/options）
  - hidden inputs 與 data-* 屬性（UI 參數）
  - <script> 內的 JS 物件 / JSON（前端組態與資料）

本模組把這些全部抽出成結構化 dict，供 preset 對照或直接進 SSOT。
用標準庫 html.parser + json + re，不裝任何外部套件。
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

import json
import re
from html.parser import HTMLParser


class _TableFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._cur_table = None
        self._cur_row = None
        self._cell = None
        self._in_cell = False
        self.form_fields = []
        self.data_attrs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._cur_table = []
        elif tag == "tr" and self._cur_table is not None:
            self._cur_row = []
        elif tag in ("td", "th") and self._cur_row is not None:
            self._in_cell = True
            self._cell = ""
        elif tag == "input":
            self.form_fields.append({"type": a.get("type", "text"), "name": a.get("name", ""),
                                     "value": a.get("value", ""), "tag": "input"})
        elif tag == "select":
            self.form_fields.append({"type": "select", "name": a.get("name", ""),
                                     "value": a.get("value", ""), "tag": "select", "options": []})
        elif tag == "option":
            if self.form_fields and self.form_fields[-1].get("tag") == "select":
                self.form_fields[-1]["options"].append(a.get("value", ""))
        elif tag == "textarea":
            self.form_fields.append({"type": "textarea", "name": a.get("name", ""),
                                     "value": "", "tag": "textarea"})
        # data-* 屬性（UI 參數）
        for k, v in a.items():
            if k.startswith("data-"):
                self.data_attrs.append({"attr": k, "value": v})

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._in_cell:
            self._cur_row.append((self._cell or "").strip())
            self._in_cell = False
        elif tag == "tr" and self._cur_row is not None:
            if self._cur_row:
                self._cur_table.append(self._cur_row)
            self._cur_row = None
        elif tag == "table" and self._cur_table is not None:
            if self._cur_table:
                self.tables.append(self._cur_table)
            self._cur_table = None

    def handle_data(self, data):
        if self._in_cell:
            self._cell += data


def extract_tables(html: str) -> list:
    """回傳所有 <table>，每個為 list[list[cell]]（首列常為表頭）。"""
    p = _TableFormParser()
    p.feed(html)
    return p.tables


def tables_as_dicts(html: str) -> list:
    """把每個表格首列當表頭 → list[dict]，方便直接餵 apply_preset。"""
    out = []
    for tbl in extract_tables(html):
        if len(tbl) < 2:
            continue
        header = tbl[0]
        for row in tbl[1:]:
            out.append({header[i]: row[i] for i in range(min(len(header), len(row)))})
    return out


def extract_form_fields(html: str) -> list:
    """回傳所有表單控件：input/select/textarea 的 name/value/options。"""
    p = _TableFormParser()
    p.feed(html)
    return p.form_fields


def extract_data_attributes(html: str) -> list:
    """回傳所有 data-* 屬性（UI 參數，如 data-material-id）。"""
    p = _TableFormParser()
    p.feed(html)
    return p.data_attrs


def extract_js_data(html: str) -> list:
    """抽 <script> 內的 JS 物件 / JSON 賦值（前端組態與資料）。

    支援：var x = {...} / let/const x = {...} / window.x = {...} / "key": {...}
    以括號配對安全擷取，逐個嘗試 json.loads。
    """
    results = []
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL | re.IGNORECASE)
    assign = re.compile(r"(?:var|let|const|window\.[\w.]+|[\w.]+)\s*=\s*([\[{])")
    for s in scripts:
        for m in assign.finditer(s):
            start = m.start(1)
            frag = _balanced(s, start)
            if not frag:
                continue
            obj = _try_json(frag)
            if obj is not None:
                results.append(obj)
    return results


def _balanced(text: str, start: int) -> str:
    """從 start 的 { 或 [ 起，回傳配對平衡的子字串（略過字串內括號）。"""
    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    in_str = None
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == in_str:
                in_str = None
            continue
        if c in ("'", '"'):
            in_str = c
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return ""


def _try_json(frag: str):
    try:
        return json.loads(frag)
    except Exception:
        # 寬鬆修：單引號→雙引號、去尾逗號、無引號 key 補引號
        f = re.sub(r"'", '"', frag)
        f = re.sub(r",\s*([}\]])", r"\1", f)
        f = re.sub(r"([{,]\s*)([A-Za-z_]\w*)(\s*:)", r'\1"\2"\3', f)
        try:
            return json.loads(f)
        except Exception:
            return None


def read_html_ui(html: str) -> dict:
    """一次抽完 HTML UI 的所有參數面向。"""
    return {
        "tables": extract_tables(html),
        "table_rows": tables_as_dicts(html),
        "form_fields": extract_form_fields(html),
        "data_attributes": extract_data_attributes(html),
        "js_data": extract_js_data(html),
    }
