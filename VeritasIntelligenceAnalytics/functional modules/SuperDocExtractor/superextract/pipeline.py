"""High-level pipeline: extract -> repair -> validate -> report, for any of
.docx / .xlsx / .xls / .csv / .tsv / .txt, dispatched by extension + file
signature (so a mis-named file gets a helpful message, not a stack trace).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .compare import compare_grids, compare_texts, pair_tables
from .csv_extract import extract_csv
from .excel_extract import extract_excel
from .encoding import read_text_auto
from .textclean import clean_text
from .validate import validate_grid, validate_text
from .word_extract import ExtractionError, extract_docx, sniff_container


@dataclass
class ExtractionResult:
    path: str
    format: str                      # docx / xlsx / xls / csv / text
    engine: str
    text: str = ""
    text_fixes: list = field(default_factory=list)
    tables: list = field(default_factory=list)     # list[Grid], repaired
    encoding: dict = None
    notes: list = field(default_factory=list)
    issues: list = field(default_factory=list)     # list[Issue]

    def report(self) -> dict:
        return {
            "file": self.path,
            "format": self.format,
            "engine": self.engine,
            "encoding": self.encoding,
            "text": {"chars": len(self.text), "fixes": self.text_fixes},
            "paragraphs": self.text.count("\n") + 1 if self.text else 0,
            "tables": [{
                "name": g.name or f"table {i + 1}",
                "rows": g.n_rows, "cols": g.n_cols,
                "merged_filled": sum(1 for k, v in g.merge_map.items() if k != v),
                "layout_suspect": g.is_layout_table(),
                "repairs": list(g.repairs),
                "source": g.source,
            } for i, g in enumerate(self.tables)],
            "notes": self.notes,
            "validation": [i.as_dict() for i in self.issues],
        }


def detect_format(path: str) -> str:
    ext = os.path.splitext(str(path))[1].lower()
    container = sniff_container(path)
    if ext in (".docx", ".docm", ".dotx"):
        return "docx"
    if ext in (".xlsx", ".xlsm", ".xltx"):
        return "xlsx"
    if ext == ".xls":
        return "xls" if container == "ole2" else "xlsx"
    if ext == ".doc":
        return "docx" if container == "zip" else "doc-legacy"
    if ext in (".csv", ".tsv"):
        return "csv"
    if ext in (".txt", ".md", ".log"):
        return "text"
    # extension unhelpful — trust the signature
    if container == "zip":
        try:
            import zipfile
            names = set(zipfile.ZipFile(path).namelist())
            if "word/document.xml" in names:
                return "docx"
            if "xl/workbook.xml" in names:
                return "xlsx"
        except Exception:
            pass
    if container == "ole2":
        return "doc-legacy"
    return "csv" if ext == "" else "text"


def extract_any(path, *, engine: str = "auto", encoding: str | None = None,
                password: str | None = None, values: str = "cached",
                delimiter: str | None = None, row_policy: str = "repair",
                repair: bool = True, keep_layout_tables: bool = True) -> ExtractionResult:
    """One call: extract + repair + validate any supported file."""
    fmt = detect_format(path)
    path_str = str(path)

    if fmt == "doc-legacy":
        raise ExtractionError(
            f"{path_str} is a legacy binary Office file (OLE2). Convert it first, e.g. "
            f"soffice --headless --convert-to docx '{path_str}' — or install xlrd for .xls.")

    if fmt == "docx":
        doc = extract_docx(path, engine=engine if engine != "auto" else "auto",
                           password=password)
        result = ExtractionResult(path_str, "docx", doc.engine,
                                  text=doc.all_text(), notes=list(doc.notes))
        result.tables = list(doc.tables)
        for grid in doc.tables:
            result.tables.extend(grid.nested)

    elif fmt in ("xlsx", "xls"):
        wb = extract_excel(path, engine=engine if engine != "auto" else "auto",
                           password=password, values=values)
        result = ExtractionResult(path_str, fmt, wb.engine, notes=list(wb.notes))
        result.tables = list(wb.sheets.values())

    elif fmt == "csv":
        if delimiter is None and path_str.lower().endswith(".tsv"):
            delimiter = "\t"
        res = extract_csv(path, encoding=encoding, delimiter=delimiter,
                          row_policy=row_policy)
        result = ExtractionResult(path_str, "csv", "csv",
                                  encoding=res.encoding.as_dict(), notes=list(res.notes))
        result.tables = [res.grid]

    else:  # plain text
        text, det = read_text_auto(path, encoding=encoding)
        result = ExtractionResult(path_str, "text", "text",
                                  text=text, encoding=det.as_dict())

    # ---- repair (修復) --------------------------------------------------
    if repair:
        if result.text:
            cleaned = clean_text(result.text)
            result.text = cleaned.text
            result.text_fixes = cleaned.fixes
        for grid in result.tables:
            grid.fill_merged()
            grid.clean_cells()

    if not keep_layout_tables:
        kept = [g for g in result.tables if not g.is_layout_table()]
        dropped = len(result.tables) - len(kept)
        if dropped:
            result.notes.append(f"dropped {dropped} layout-suspect table(s) "
                                "(pass keep_layout_tables=True to keep them)")
            result.tables = kept

    # ---- validate (驗證) -------------------------------------------------
    if result.text:
        result.issues.extend(validate_text(result.text, location=os.path.basename(path_str)))
    for grid in result.tables:
        result.issues.extend(validate_grid(grid))
    return result


def compare_files(old_path, new_path, *, key: str | None = None,
                  with_datacompy: bool = True, max_diff_lines: int = 400,
                  **extract_kwargs) -> dict:
    """Extract both files (with repair) and produce the full comparison report."""
    old = extract_any(old_path, **extract_kwargs)
    new = extract_any(new_path, **extract_kwargs)

    report: dict = {"old": str(old_path), "new": str(new_path),
                    "old_report": old.report(), "new_report": new.report()}

    if old.text or new.text:
        tdiff = compare_texts(old.text, new.text,
                              label_old=str(old_path), label_new=str(new_path))
        unified_lines = tdiff.unified.splitlines()
        report["text_diff"] = tdiff.as_dict()
        report["unified"] = "\n".join(unified_lines[:max_diff_lines]) + (
            f"\n... ({len(unified_lines) - max_diff_lines} more diff lines, see JSON)"
            if len(unified_lines) > max_diff_lines else "")

    pairs, only_old, only_new = pair_tables(old.tables, new.tables)
    label = lambda g, i: g.name or f"table {i + 1}"
    report["table_pairing"] = {
        "old_count": len(old.tables), "new_count": len(new.tables),
        "pairs": [{"old": label(old.tables[i], i), "new": label(new.tables[j], j),
                   "score": round(score, 3)} for i, j, score in pairs],
        "only_old": [label(old.tables[i], i) for i in only_old],
        "only_new": [label(new.tables[j], j) for j in only_new],
    }

    report["table_diffs"] = []
    for i, j, _score in pairs:
        diff = compare_grids(old.tables[i], new.tables[j], key=key,
                             with_datacompy=with_datacompy)
        entry = diff.as_dict()
        entry["label"] = f"{label(old.tables[i], i)} ↔ {label(new.tables[j], j)}"
        entry["datacompy"] = diff.datacompy_report
        report["table_diffs"].append(entry)
    return report
