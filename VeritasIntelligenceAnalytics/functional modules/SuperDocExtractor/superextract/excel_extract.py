"""Excel (.xlsx / .xls) extraction into Grids.

Engines
-------
openpyxl (preferred when installed)
    values="cached" (default) reads the last-calculated result of formula
    cells instead of the formula string; merged ranges are resolved into
    Grid.merge_map so repair can fill exactly the merged cells.
rawxml (stdlib fallback)
    Minimal but correct SpreadsheetML reader: shared strings, inline
    strings, booleans, errors, numbers, date detection via styles
    (built-in + custom number formats, 1900/1904 date systems).
xlrd
    Legacy binary .xls, when xlrd is installed.

Leading zeros: text cells stay strings ('00123' survives). Numbers that
Excel itself stored as numeric never had leading zeros to preserve.
"""
from __future__ import annotations
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

import datetime as _dt
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from .availability import has, load
from .tableops import Grid
from .word_extract import ExtractionError, open_office_zip, sniff_container

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _m(tag: str) -> str:
    return f"{{{MAIN_NS}}}{tag}"


#: Built-in numFmtIds that render as dates/times.
_DATE_NUMFMT_IDS = set(range(14, 23)) | set(range(27, 37)) | {45, 46, 47} | set(range(50, 59))
_DATE_TOKEN_RE = re.compile(r"[dmhysDMHYS]")


@dataclass
class ExcelWorkbook:
    sheets: dict = field(default_factory=dict)   # {sheet_name: Grid}
    formulas: dict = field(default_factory=dict) # {sheet_name: {"A1": "=SUM(...)"}}
    notes: list = field(default_factory=list)
    engine: str = ""


# ------------------------------------------------------------------ helpers

def col_to_index(ref: str) -> int:
    """'A' -> 0, 'AB' -> 27. Accepts a full cell ref like 'AB12'."""
    idx = 0
    for ch in ref:
        if ch.isalpha():
            idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
        else:
            break
    return idx - 1


def split_ref(ref: str):
    """'B12' -> (11, 1)  (row_idx, col_idx), zero-based."""
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    if not m:
        raise ValueError(f"bad cell reference {ref!r}")
    return int(m.group(2)) - 1, col_to_index(m.group(1))


def serial_to_datetime(serial: float, date1904: bool = False):
    """Excel serial number -> datetime (handles the 1900 leap-year bug)."""
    if date1904:
        base = _dt.datetime(1904, 1, 1)
        return base + _dt.timedelta(days=serial)
    # 1899-12-30 base absorbs Excel's phantom 1900-02-29 for serial >= 61
    base = _dt.datetime(1899, 12, 30)
    if serial < 60:
        base = _dt.datetime(1899, 12, 31)
    return base + _dt.timedelta(days=serial)


def _format_is_date(fmt_code: str) -> bool:
    """Heuristic: does a custom number format render as a date/time?"""
    # strip quoted literals, [] sections (colors, locale ids), and escapes
    cleaned = re.sub(r'"[^"]*"|\[[^\]]*\]|\\.', "", fmt_code)
    return bool(_DATE_TOKEN_RE.search(cleaned))


# ------------------------------------------------------------------ rawxml engine

def _load_shared_strings(zf) -> list:
    names = set(zf.namelist())
    if "xl/sharedStrings.xml" not in names:
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings = []
    for si in root:
        strings.append("".join(t.text or "" for t in si.iter(_m("t"))))
    return strings


def _load_date_styles(zf) -> set:
    """Indices into cellXfs whose number format is a date/time format."""
    names = set(zf.namelist())
    if "xl/styles.xml" not in names:
        return set()
    root = ET.fromstring(zf.read("xl/styles.xml"))
    custom_date_ids = set()
    num_fmts = root.find(_m("numFmts"))
    if num_fmts is not None:
        for nf in num_fmts:
            fmt_id = int(nf.get("numFmtId", "-1"))
            if _format_is_date(nf.get("formatCode", "")):
                custom_date_ids.add(fmt_id)
    date_styles = set()
    cell_xfs = root.find(_m("cellXfs"))
    if cell_xfs is not None:
        for i, xf in enumerate(cell_xfs):
            fmt_id = int(xf.get("numFmtId", "0"))
            if fmt_id in _DATE_NUMFMT_IDS or fmt_id in custom_date_ids:
                date_styles.add(i)
    return date_styles


def _sheet_targets(zf) -> list:
    """[(sheet_name, zip_member_path)] in workbook order."""
    wb_root = ET.fromstring(zf.read("xl/workbook.xml"))
    rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rid_to_target = {}
    for rel in rels_root:
        rid_to_target[rel.get("Id")] = rel.get("Target", "")
    out = []
    sheets = wb_root.find(_m("sheets"))
    if sheets is None:
        return out
    for sheet in sheets:
        name = sheet.get("name", "Sheet")
        rid = sheet.get(f"{{{REL_NS}}}id")
        target = rid_to_target.get(rid, "")
        if target.startswith("/"):
            member = target.lstrip("/")
        elif target.startswith("../"):
            member = target[3:]
        else:
            member = "xl/" + target
        out.append((name, member))
    return out


def _workbook_is_1904(zf) -> bool:
    wb_root = ET.fromstring(zf.read("xl/workbook.xml"))
    pr = wb_root.find(_m("workbookPr"))
    return pr is not None and pr.get("date1904", "0").lower() in ("1", "true")


def extract_xlsx_rawxml(path, password: str | None = None,
                        values: str = "cached") -> ExcelWorkbook:
    wb = ExcelWorkbook(engine="rawxml")
    with open_office_zip(path, password=password) as zf:
        names = set(zf.namelist())
        if "xl/workbook.xml" not in names:
            raise ExtractionError("zip container has no xl/workbook.xml — not an .xlsx "
                                  "(is it actually .docx/.zip?)")
        sst = _load_shared_strings(zf)
        date_styles = _load_date_styles(zf)
        date1904 = _workbook_is_1904(zf)

        for sheet_name, member in _sheet_targets(zf):
            if member not in names:
                wb.notes.append(f"sheet {sheet_name!r}: zip member {member} missing, skipped")
                continue
            root = ET.fromstring(zf.read(member))
            cells: dict = {}
            formulas: dict = {}
            max_r = max_c = -1
            sheet_data = root.find(_m("sheetData"))
            if sheet_data is not None:
                implied_row = 0
                for row_el in sheet_data:
                    r_attr = row_el.get("r")
                    r = int(r_attr) - 1 if r_attr else implied_row
                    implied_row = r + 1
                    implied_col = 0
                    for c_el in row_el:
                        ref = c_el.get("r")
                        if ref:
                            _, c = split_ref(ref)
                        else:
                            c = implied_col
                        implied_col = c + 1
                        val = _cell_value(c_el, sst, date_styles, date1904)
                        f_el = c_el.find(_m("f"))
                        if f_el is not None:
                            formulas[ref or f"r{r + 1}c{c + 1}"] = "=" + (f_el.text or "")
                            if values == "formula":
                                val = "=" + (f_el.text or "")
                        if val is not None:
                            cells[(r, c)] = val
                            max_r, max_c = max(max_r, r), max(max_c, c)

            rows = [[cells.get((r, c), "") for c in range(max_c + 1)]
                    for r in range(max_r + 1)]

            merge_map: dict = {}
            merged_el = root.find(_m("mergeCells"))
            if merged_el is not None:
                for mc in merged_el:
                    ref = mc.get("ref", "")
                    if ":" not in ref:
                        continue
                    a, b = ref.split(":")
                    (r1, c1), (r2, c2) = split_ref(a), split_ref(b)
                    for r in range(r1, r2 + 1):
                        for c in range(c1, c2 + 1):
                            merge_map[(r, c)] = (r1, c1)

            grid = Grid(rows=rows, merge_map=merge_map,
                        source=f"{path} : {sheet_name}", name=sheet_name)
            wb.sheets[sheet_name] = grid.finalize()
            if formulas:
                wb.formulas[sheet_name] = formulas
                if values == "cached":
                    wb.notes.append(f"sheet {sheet_name!r}: {len(formulas)} formula cell(s) "
                                    "read as cached values (use values='formula' for the formulas)")
    return wb


def _cell_value(c_el, sst, date_styles, date1904):
    ctype = c_el.get("t", "n")
    v_el = c_el.find(_m("v"))
    if ctype == "inlineStr":
        is_el = c_el.find(_m("is"))
        if is_el is not None:
            return "".join(t.text or "" for t in is_el.iter(_m("t")))
        return ""
    if v_el is None or v_el.text is None:
        return None
    raw = v_el.text
    if ctype == "s":
        try:
            return sst[int(raw)]
        except (ValueError, IndexError):
            return raw
    if ctype == "str":
        return raw
    if ctype == "b":
        return raw.strip() in ("1", "true", "TRUE")
    if ctype == "e":
        return raw  # e.g. #DIV/0!
    # numeric
    try:
        num = float(raw)
    except ValueError:
        return raw
    style = int(c_el.get("s", "-1"))
    if style in date_styles:
        try:
            return serial_to_datetime(num, date1904)
        except (OverflowError, ValueError):
            return num
    if num.is_integer() and abs(num) < 1e15:
        return int(num)
    return num


# ------------------------------------------------------------------ openpyxl engine

def extract_xlsx_openpyxl(path, password: str | None = None,
                          values: str = "cached") -> ExcelWorkbook:
    if not has("openpyxl"):
        raise ExtractionError("openpyxl is not installed")
    openpyxl = load("openpyxl")

    src = path
    if sniff_container(path) == "ole2":
        # decrypt (or raise with remedies) via the shared helper
        zf = open_office_zip(path, password=password)
        src = zf.fp
        src.seek(0)

    wb = ExcelWorkbook(engine="openpyxl")
    book = openpyxl.load_workbook(src, data_only=(values == "cached"), read_only=False)
    try:
        for ws in book.worksheets:
            rows = [[cell.value if cell.value is not None else "" for cell in row]
                    for row in ws.iter_rows()]
            merge_map: dict = {}
            for rng in ws.merged_cells.ranges:
                r1, c1 = rng.min_row - 1, rng.min_col - 1
                for r in range(rng.min_row - 1, rng.max_row):
                    for c in range(rng.min_col - 1, rng.max_col):
                        merge_map[(r, c)] = (r1, c1)
            grid = Grid(rows=rows, merge_map=merge_map,
                        source=f"{path} : {ws.title}", name=ws.title)
            wb.sheets[ws.title] = grid.finalize()

        if values == "cached":
            # count formula cells so the report can flag "cached values" caveat
            if hasattr(src, "seek"):
                src.seek(0)
            book_f = openpyxl.load_workbook(src, data_only=False, read_only=True)
            try:
                for ws in book_f.worksheets:
                    fmap = {}
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value, str) and cell.value.startswith("="):
                                fmap[cell.coordinate] = cell.value
                    if fmap:
                        wb.formulas[ws.title] = fmap
                        wb.notes.append(f"sheet {ws.title!r}: {len(fmap)} formula cell(s) "
                                        "read as cached values")
            finally:
                book_f.close()
    finally:
        book.close()
    return wb


# ------------------------------------------------------------------ legacy .xls

def extract_xls_xlrd(path) -> ExcelWorkbook:
    if not has("xlrd"):
        raise ExtractionError(
            "This is a legacy binary .xls file. Install xlrd (pip install xlrd) or convert "
            "with: soffice --headless --convert-to xlsx FILE")
    xlrd = load("xlrd")
    book = xlrd.open_workbook(path, formatting_info=False)
    wb = ExcelWorkbook(engine="xlrd")
    for ws in book.sheets():
        rows = []
        for r in range(ws.nrows):
            vals = []
            for c in range(ws.ncols):
                cell = ws.cell(r, c)
                if cell.ctype == xlrd.XL_CELL_DATE:
                    vals.append(_dt.datetime(*xlrd.xldate_as_tuple(cell.value, book.datemode)))
                elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                    vals.append(bool(cell.value))
                elif cell.ctype == xlrd.XL_CELL_EMPTY:
                    vals.append("")
                elif cell.ctype == xlrd.XL_CELL_NUMBER and float(cell.value).is_integer():
                    vals.append(int(cell.value))
                else:
                    vals.append(cell.value)
            rows.append(vals)
        merge_map: dict = {}
        for r1, r2, c1, c2 in getattr(ws, "merged_cells", []):
            for r in range(r1, r2):
                for c in range(c1, c2):
                    merge_map[(r, c)] = (r1, c1)
        grid = Grid(rows=rows, merge_map=merge_map,
                    source=f"{path} : {ws.name}", name=ws.name)
        wb.sheets[ws.name] = grid.finalize()
    return wb


# ------------------------------------------------------------------ facade

def extract_excel(path, engine: str = "auto", password: str | None = None,
                  values: str = "cached") -> ExcelWorkbook:
    """Extract every sheet of an Excel workbook into Grids.

    engine: auto | openpyxl | rawxml | xlrd
    values: 'cached' (formula results) or 'formula' (formula strings)
    """
    kind = sniff_container(path)
    path_str = str(path).lower()

    if engine == "xlrd" or (engine == "auto" and kind == "ole2" and path_str.endswith(".xls")):
        return extract_xls_xlrd(path)  # raises a helpful message when xlrd is missing
    if engine == "openpyxl" or (engine == "auto" and has("openpyxl") and kind == "zip"):
        return extract_xlsx_openpyxl(path, password=password, values=values)
    if engine in ("auto", "rawxml"):
        return extract_xlsx_rawxml(path, password=password, values=values)
    raise ExtractionError(f"unknown excel engine {engine!r}; choose auto/openpyxl/rawxml/xlrd")
