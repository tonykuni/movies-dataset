"""Word (.docx) text + table extraction.

Engines
-------
rawxml (default, stdlib-only)
    Parses word/document.xml directly with zipfile + ElementTree.
    * gridSpan  -> horizontal merges recorded in Grid.merge_map
    * vMerge    -> vertical merges resolved to their anchor cell
    * nested tables -> flattened into the cell text AND collected separately
    * track changes -> deleted text (w:delText) is naturally excluded,
      insertions (w:ins) included; their presence is reported
    * mc:Fallback subtrees skipped so textbox content is not duplicated
python-docx / docx2python
    Optional engines used for cross-checking (多引擎交叉驗證).

Legacy .doc (OLE2) and encrypted files are detected by signature and
reported with actionable remedies instead of a cryptic BadZipFile.
"""
from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from .availability import has, load
from .tableops import Grid

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


_SKIP_SUBTREES = {
    f"{{{MC_NS}}}Fallback",   # duplicate of mc:Choice content
    _w("instrText"),          # field codes (e.g. ' PAGE ')
    _w("delInstrText"),
    _w("pPr"), _w("rPr"), _w("tblPr"), _w("trPr"), _w("tcPr"), _w("sectPr"),
}

OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ZIP_MAGIC = b"PK\x03\x04"


class ExtractionError(RuntimeError):
    """Raised with a human-actionable message (what happened + what to do)."""


@dataclass
class WordDocument:
    text: str = ""                      # body text, tables excluded
    paragraphs: list = field(default_factory=list)
    tables: list = field(default_factory=list)       # list[Grid]
    header_footer_text: str = ""
    notes: list = field(default_factory=list)
    engine: str = "rawxml"

    def all_text(self) -> str:
        parts = [self.text]
        if self.header_footer_text:
            parts.append(self.header_footer_text)
        return "\n".join(p for p in parts if p)


# ------------------------------------------------------------------ signature

def sniff_container(path_or_bytes) -> str:
    """'zip' | 'ole2' | 'unknown' — what the file *really* is."""
    if isinstance(path_or_bytes, (bytes, bytearray)):
        head = bytes(path_or_bytes[:8])
    else:
        with open(path_or_bytes, "rb") as fh:
            head = fh.read(8)
    if head.startswith(ZIP_MAGIC):
        return "zip"
    if head.startswith(OLE2_MAGIC):
        return "ole2"
    return "unknown"


def open_office_zip(path, password: str | None = None) -> zipfile.ZipFile:
    """Open an OOXML container, decrypting OLE-wrapped files when possible."""
    kind = sniff_container(path)
    if kind == "zip":
        return zipfile.ZipFile(path)
    if kind == "ole2":
        if password and has("msoffcrypto-tool"):
            msoffcrypto = load("msoffcrypto-tool")
            decrypted = io.BytesIO()
            with open(path, "rb") as fh:
                office = msoffcrypto.OfficeFile(fh)
                office.load_key(password=password)
                office.decrypt(decrypted)
            decrypted.seek(0)
            if decrypted.read(4) == ZIP_MAGIC:
                decrypted.seek(0)
                return zipfile.ZipFile(decrypted)
            raise ExtractionError("decryption succeeded but the payload is not OOXML — "
                                  "this is probably a legacy binary file")
        raise ExtractionError(
            "This file is an OLE2 container, not a modern OOXML zip. It is either "
            "a legacy .doc/.xls (convert with: soffice --headless --convert-to docx FILE) "
            "or password-protected OOXML (pass password=... with msoffcrypto-tool installed)."
        )
    raise ExtractionError("Unrecognized file signature — not OOXML (.docx/.xlsx) and not OLE2. "
                          "The extension may be lying about the real format.")


# ------------------------------------------------------------------ raw XML engine

def _iter_block_items(parent):
    """Yield w:p / w:tbl children in document order, descending into w:sdt."""
    for child in parent:
        if child.tag in (_w("p"), _w("tbl")):
            yield child
        elif child.tag in (_w("sdt"), _w("sdtContent"), _w("smartTag")):
            content = child.find(_w("sdtContent")) if child.tag == _w("sdt") else child
            if content is not None:
                yield from _iter_block_items(content)


def _para_text(p) -> str:
    """Text of one paragraph. Skips deleted text (w:delText has a different
    tag than w:t, so track-changes deletions are excluded automatically),
    field instructions, and duplicated mc:Fallback content."""
    parts: list[str] = []

    def walk(el):
        for child in el:
            tag = child.tag
            if tag in _SKIP_SUBTREES:
                continue
            if tag == _w("t"):
                parts.append(child.text or "")
            elif tag == _w("tab"):
                parts.append("\t")
            elif tag in (_w("br"), _w("cr")):
                parts.append("\n")
            elif tag == _w("noBreakHyphen"):
                parts.append("-")
            elif tag == _w("tbl"):
                continue  # nested tables are handled by the table walker
            else:
                walk(child)

    walk(p)
    return "".join(parts)


def _parse_table(tbl, source: str, index_path: str) -> Grid:
    """Parse one w:tbl into a Grid with full merge provenance.

    merge_map stores an anchor for *every* cell (self for normal cells);
    continuation cells point at the top-left cell of their merged region.
    """
    grid_rows: list[list] = []
    merge_map: dict = {}
    nested: list[Grid] = []

    rows = [el for el in _iter_table_rows(tbl)]
    for r, tr in enumerate(rows):
        row_vals: list = []
        col = 0
        tr_pr = tr.find(_w("trPr"))
        if tr_pr is not None:
            before = tr_pr.find(_w("gridBefore"))
            if before is not None:
                skip = int(before.get(_w("val"), "0") or 0)
                for k in range(skip):
                    row_vals.append("")
                    merge_map[(r, col + k)] = (r, col + k)
                col += skip

        for tc in _iter_row_cells(tr):
            tc_pr = tc.find(_w("tcPr"))
            span = 1
            vmerge_state = None  # None | 'restart' | 'continue'
            if tc_pr is not None:
                gs = tc_pr.find(_w("gridSpan"))
                if gs is not None:
                    span = max(1, int(gs.get(_w("val"), "1") or 1))
                vm = tc_pr.find(_w("vMerge"))
                if vm is not None:
                    vmerge_state = vm.get(_w("val")) or "continue"

            # cell content: paragraphs + nested tables
            cell_parts: list[str] = []
            for block in _iter_block_items(tc):
                if block.tag == _w("p"):
                    cell_parts.append(_para_text(block))
                else:  # nested w:tbl
                    sub = _parse_table(block, source, f"{index_path}>cell({r + 1},{col + 1})")
                    nested.append(sub)
                    nested.extend(sub.nested)
                    cell_parts.append(sub.to_text())
            cell_text = "\n".join(part for part in cell_parts if part).strip()

            # Anchor resolution. Real-world files often omit w:val="restart"
            # on the first cell of a vertical merge, so a continuation cell
            # simply inherits the anchor of the cell directly above it.
            if vmerge_state == "continue" and r > 0 and not cell_text:
                anchor = merge_map.get((r - 1, col), (r - 1, col))
            else:
                anchor = (r, col)   # normal / restart / stray text in continuation

            row_vals.append(cell_text if anchor == (r, col) else "")
            merge_map[(r, col)] = anchor
            for k in range(1, span):        # horizontal continuation columns
                row_vals.append("")
                merge_map[(r, col + k)] = anchor
            col += span

        grid_rows.append(row_vals)

    grid = Grid(rows=grid_rows, merge_map=merge_map,
                source=f"{source} : {index_path}", name=index_path, nested=nested)
    return grid.finalize()


def _iter_table_rows(tbl):
    for child in tbl:
        if child.tag == _w("tr"):
            yield child
        elif child.tag == _w("sdt"):
            content = child.find(_w("sdtContent"))
            if content is not None:
                for sub in content:
                    if sub.tag == _w("tr"):
                        yield sub


def _iter_row_cells(tr):
    for child in tr:
        if child.tag == _w("tc"):
            yield child
        elif child.tag == _w("sdt"):
            content = child.find(_w("sdtContent"))
            if content is not None:
                for sub in content:
                    if sub.tag == _w("tc"):
                        yield sub


def extract_docx_rawxml(path, password: str | None = None,
                        include_headers_footers: bool = True) -> WordDocument:
    doc = WordDocument(engine="rawxml")
    src_label = getattr(path, "name", str(path))

    with open_office_zip(path, password=password) as zf:
        names = set(zf.namelist())
        if "word/document.xml" not in names:
            raise ExtractionError("zip container has no word/document.xml — not a .docx "
                                  "(is it actually .xlsx/.pptx/.zip?)")
        xml_bytes = zf.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        body = root.find(_w("body"))
        if body is None:
            raise ExtractionError("document.xml has no w:body element")

        # track-changes presence -> note (deleted text is excluded from output)
        if any(True for _ in root.iter(_w("ins"))):
            doc.notes.append("document contains tracked INSERTIONS (w:ins) — their text is included")
        if any(True for _ in root.iter(_w("del"))):
            doc.notes.append("document contains tracked DELETIONS (w:del) — their text is EXCLUDED")

        table_no = 0
        for block in _iter_block_items(body):
            if block.tag == _w("p"):
                text = _para_text(block)
                if text.strip():
                    doc.paragraphs.append(text)
            else:
                table_no += 1
                doc.tables.append(_parse_table(block, src_label, f"table {table_no}"))

        if include_headers_footers:
            hf_parts = []
            for name in sorted(n for n in names
                               if re.match(r"word/(header|footer)\d*\.xml$", n)):
                hf_root = ET.fromstring(zf.read(name))
                for p in hf_root.iter(_w("p")):
                    text = _para_text(p)
                    if text.strip():
                        hf_parts.append(text)
            doc.header_footer_text = "\n".join(hf_parts)

    doc.text = "\n".join(doc.paragraphs)
    return doc


# ------------------------------------------------------------------ optional engines

def extract_docx_python_docx(path) -> WordDocument:
    if not has("python-docx"):
        raise ExtractionError("python-docx is not installed")
    docx = load("python-docx")
    d = docx.Document(path)
    doc = WordDocument(engine="python-docx")
    doc.paragraphs = [p.text for p in d.paragraphs if p.text.strip()]
    doc.text = "\n".join(doc.paragraphs)
    for i, table in enumerate(d.tables, 1):
        rows = []
        merge_map: dict = {}
        for r, row in enumerate(table.rows):
            vals = []
            seen_tc: dict[int, tuple] = {}
            for c, cell in enumerate(row.cells):
                # python-docx repeats the same _tc element across a merge
                key = id(cell._tc)
                if key in seen_tc:
                    merge_map[(r, c)] = seen_tc[key]
                    vals.append(cell.text)
                else:
                    seen_tc[key] = (r, c)
                    merge_map[(r, c)] = (r, c)
                    vals.append(cell.text)
            rows.append(vals)
        grid = Grid(rows=rows, merge_map=merge_map,
                    source=f"{path} : table {i}", name=f"table {i}")
        doc.tables.append(grid.finalize())
        doc.notes.append("python-docx repeats merged-cell text across the span "
                         "(no distinction between anchor and continuation)")
    return doc


def extract_docx_docx2python(path) -> WordDocument:
    if not has("docx2python"):
        raise ExtractionError("docx2python is not installed")
    d2p = load("docx2python")
    doc = WordDocument(engine="docx2python")
    with d2p.docx2python(path) as result:
        body = result.body
        table_no = 0
        for tbl in body:
            n_rows = len(tbl)
            n_cells = max((len(r) for r in tbl), default=0)
            if n_rows <= 1 and n_cells <= 1:
                # plain paragraphs are wrapped as 1x1 "tables"
                for row in tbl:
                    for cell in row:
                        for para in cell:
                            text = re.sub(r"----media/.*?----", "", str(para)).strip()
                            if text:
                                doc.paragraphs.append(text)
                continue
            table_no += 1
            rows = []
            for row in tbl:
                vals = []
                for cell in row:
                    text = "\n".join(str(p) for p in cell)
                    vals.append(re.sub(r"----media/.*?----", "", text).strip())
                rows.append(vals)
            grid = Grid(rows=rows, source=f"{path} : table {table_no}",
                        name=f"table {table_no}")
            doc.tables.append(grid.finalize())
    doc.text = "\n".join(doc.paragraphs)
    return doc


ENGINES = {
    "rawxml": extract_docx_rawxml,
    "python-docx": lambda path, **kw: extract_docx_python_docx(path),
    "docx2python": lambda path, **kw: extract_docx_docx2python(path),
}


def extract_docx(path, engine: str = "auto", password: str | None = None,
                 include_headers_footers: bool = True) -> WordDocument:
    """Extract text + tables from a .docx file.

    engine='auto' uses the stdlib rawxml engine (most precise merge
    handling); name an engine explicitly to force it.
    """
    if engine in ("auto", "rawxml"):
        return extract_docx_rawxml(path, password=password,
                                   include_headers_footers=include_headers_footers)
    if engine not in ENGINES:
        raise ExtractionError(f"unknown docx engine {engine!r}; choose from {sorted(ENGINES)}")
    return ENGINES[engine](path)


def available_docx_engines() -> list:
    engines = ["rawxml"]
    if has("python-docx"):
        engines.append("python-docx")
    if has("docx2python"):
        engines.append("docx2python")
    return engines
