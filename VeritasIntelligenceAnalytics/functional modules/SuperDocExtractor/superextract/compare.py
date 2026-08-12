"""Comparison (對照): text diff, table pairing, cell-level diff.

Design notes
------------
* Tables are PAIRED before they are diffed. Pairing uses header + content
  similarity, so an inserted table in the new document shifts nothing
  (the classic "table 2 now compares against a brand-new table" bug).
* Row alignment uses a key column when one is given or can be auto-detected
  (unique, non-empty in both tables); otherwise row order. Index alignment
  after an inserted row would mark everything below as changed — the report
  says which alignment was used so that failure mode is visible.
* Cell equality goes through normalize_for_compare (NFKC, zero-width strip)
  plus numeric-aware comparison, so '1,000' == 1000 and '１２３' == '123',
  while genuinely different values still differ.
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from .availability import has, load
from .tableops import Grid, coerce_number
from .textclean import normalize_for_compare


# ------------------------------------------------------------------ text

@dataclass
class TextDiff:
    similarity: float
    added: list = field(default_factory=list)
    removed: list = field(default_factory=list)
    unified: str = ""

    @property
    def identical(self) -> bool:
        return not self.added and not self.removed

    def as_dict(self) -> dict:
        return {"similarity": round(self.similarity, 4),
                "added_lines": len(self.added), "removed_lines": len(self.removed),
                "identical": self.identical}


def compare_texts(old: str, new: str, label_old: str = "old", label_new: str = "new",
                  normalize: bool = True) -> TextDiff:
    if normalize:
        old_lines = [normalize_for_compare(ln) for ln in old.splitlines()]
        new_lines = [normalize_for_compare(ln) for ln in new.splitlines()]
    else:
        old_lines, new_lines = old.splitlines(), new.splitlines()

    sim = difflib.SequenceMatcher(None, "\n".join(old_lines), "\n".join(new_lines)).ratio()
    unified = "\n".join(difflib.unified_diff(old_lines, new_lines,
                                             fromfile=label_old, tofile=label_new, lineterm=""))
    added = [ln[1:] for ln in unified.splitlines()
             if ln.startswith("+") and not ln.startswith("+++")]
    removed = [ln[1:] for ln in unified.splitlines()
               if ln.startswith("-") and not ln.startswith("---")]
    return TextDiff(similarity=sim, added=added, removed=removed, unified=unified)


def html_side_by_side(old: str, new: str, label_old: str = "old", label_new: str = "new") -> str:
    return difflib.HtmlDiff(wrapcolumn=80).make_file(
        old.splitlines(), new.splitlines(), label_old, label_new, context=True, numlines=2)


# ------------------------------------------------------------------ pairing

def _similarity(g1: Grid, g2: Grid) -> float:
    h1 = {normalize_for_compare(h) for h in g1.header() if h}
    h2 = {normalize_for_compare(h) for h in g2.header() if h}
    header_j = len(h1 & h2) / len(h1 | h2) if (h1 | h2) else 0.0
    c1, c2 = g1.content_signature(), g2.content_signature()
    content_j = len(c1 & c2) / len(c1 | c2) if (c1 | c2) else 0.0
    shape = 1.0 - (abs(g1.n_cols - g2.n_cols) / max(g1.n_cols, g2.n_cols, 1)) * 0.5 \
                - (abs(g1.n_rows - g2.n_rows) / max(g1.n_rows, g2.n_rows, 1)) * 0.5
    return 0.5 * header_j + 0.3 * content_j + 0.2 * max(shape, 0.0)


def pair_tables(old_tables: list, new_tables: list, threshold: float = 0.3):
    """Greedy best-first pairing.

    Returns (pairs, unmatched_old, unmatched_new) where pairs is a list of
    (old_idx, new_idx, score) sorted by old_idx.
    """
    candidates = []
    for i, g1 in enumerate(old_tables):
        for j, g2 in enumerate(new_tables):
            score = _similarity(g1, g2)
            if score >= threshold:
                candidates.append((score, i, j))
    candidates.sort(reverse=True)

    pairs, used_old, used_new = [], set(), set()
    for score, i, j in candidates:
        if i in used_old or j in used_new:
            continue
        pairs.append((i, j, score))
        used_old.add(i)
        used_new.add(j)
    pairs.sort()
    unmatched_old = [i for i in range(len(old_tables)) if i not in used_old]
    unmatched_new = [j for j in range(len(new_tables)) if j not in used_new]
    return pairs, unmatched_old, unmatched_new


# ------------------------------------------------------------------ cell diff

@dataclass
class CellChange:
    row_label: str
    column: str
    old: object
    new: object

    def as_dict(self) -> dict:
        return {"row": self.row_label, "column": self.column,
                "old": str(self.old), "new": str(self.new)}


@dataclass
class TableDiff:
    alignment: str = "index"            # 'key:<col>' or 'index'
    changes: list = field(default_factory=list)     # list[CellChange]
    added_rows: list = field(default_factory=list)  # row labels
    removed_rows: list = field(default_factory=list)
    added_columns: list = field(default_factory=list)
    removed_columns: list = field(default_factory=list)
    datacompy_report: str = ""
    notes: list = field(default_factory=list)

    @property
    def identical(self) -> bool:
        return not (self.changes or self.added_rows or self.removed_rows
                    or self.added_columns or self.removed_columns)

    def as_dict(self) -> dict:
        return {"alignment": self.alignment, "identical": self.identical,
                "changed_cells": [c.as_dict() for c in self.changes],
                "added_rows": self.added_rows, "removed_rows": self.removed_rows,
                "added_columns": self.added_columns, "removed_columns": self.removed_columns,
                "notes": self.notes}


def cells_equal(a, b) -> bool:
    """Normalized equality: NFKC + whitespace + numeric-aware ('1,000'==1000)."""
    na, nb = normalize_for_compare(a), normalize_for_compare(b)
    if na == nb:
        return True
    ca, cb = coerce_number(na), coerce_number(nb)
    if isinstance(ca, (int, float)) and isinstance(cb, (int, float)):
        if ca == cb:
            return True
        largest = max(abs(ca), abs(cb))
        return largest > 0 and abs(ca - cb) / largest < 1e-9
    return False


def detect_key_column(g1: Grid, g2: Grid):
    """A column that uniquely identifies rows in BOTH tables, or None."""
    h1, h2 = g1.header(), g2.header()
    shared = [h for h in h1 if h in h2]
    hints = ("id", "編號", "項次", "代號", "代碼", "key", "no", "no.", "序號")

    def uniqueness(grid: Grid, col_name: str, header: list) -> bool:
        idx = header.index(col_name)
        vals = [normalize_for_compare(row[idx]) for row in grid.body() if idx < len(row)]
        vals = [v for v in vals if v]
        return len(vals) == len(grid.body()) and len(set(vals)) == len(vals) and bool(vals)

    ranked = sorted(shared, key=lambda h: (not any(k in h.lower() for k in hints),
                                           shared.index(h)))
    for col in ranked:
        if uniqueness(g1, col, h1) and uniqueness(g2, col, h2):
            return col
    return None


def compare_grids(g_old: Grid, g_new: Grid, key: str | None = None,
                  auto_key: bool = True, with_datacompy: bool = True) -> TableDiff:
    diff = TableDiff()
    h_old, h_new = g_old.header(), g_new.header()
    diff.added_columns = [h for h in h_new if h not in h_old]
    diff.removed_columns = [h for h in h_old if h not in h_new]
    shared_cols = [h for h in h_old if h in h_new]

    if key is None and auto_key:
        key = detect_key_column(g_old, g_new)
        if key:
            diff.notes.append(f"auto-detected key column {key!r} for row alignment")
    if key is not None and key not in shared_cols:
        diff.notes.append(f"requested key {key!r} missing from both tables; "
                          "falling back to row-order alignment")
        key = None

    rec_old, rec_new = g_old.to_records(), g_new.to_records()

    if key:
        diff.alignment = f"key:{key}"
        map_old = {normalize_for_compare(r[key]): r for r in rec_old}
        map_new = {normalize_for_compare(r[key]): r for r in rec_new}
        if len(map_old) < len(rec_old) or len(map_new) < len(rec_new):
            diff.notes.append("duplicate key values collapsed; counts may be off")
        diff.removed_rows = [k for k in map_old if k not in map_new]
        diff.added_rows = [k for k in map_new if k not in map_old]
        common = [k for k in map_old if k in map_new]
        for k in common:
            for col in shared_cols:
                if not cells_equal(map_old[k].get(col), map_new[k].get(col)):
                    diff.changes.append(CellChange(f"{key}={k}", col,
                                                   map_old[k].get(col), map_new[k].get(col)))
    else:
        diff.alignment = "index"
        diff.notes.append("row-order alignment: an inserted/deleted row makes every "
                          "row below it look changed — provide a key column when possible")
        n = min(len(rec_old), len(rec_new))
        for i in range(n):
            for col in shared_cols:
                if not cells_equal(rec_old[i].get(col), rec_new[i].get(col)):
                    diff.changes.append(CellChange(f"row {i + 2}", col,   # +2: 1-based + header
                                                   rec_old[i].get(col), rec_new[i].get(col)))
        diff.removed_rows = [f"row {i + 2}" for i in range(n, len(rec_old))]
        diff.added_rows = [f"row {i + 2}" for i in range(n, len(rec_new))]

    if with_datacompy and has("datacompy") and has("pandas"):
        diff.datacompy_report = _datacompy_report(g_old, g_new, key)
    return diff


def _datacompy_report(g_old: Grid, g_new: Grid, key: str | None) -> str:
    try:
        datacompy = load("datacompy")
        # datacompy <1.0 exposes Compare; 1.x renamed it to PandasCompare
        Compare = getattr(datacompy, "Compare", None) or datacompy.PandasCompare
        df_old = g_old.to_dataframe().astype(str)
        df_new = g_new.to_dataframe().astype(str)
        if key:
            join_cols = [key]
        else:
            df_old = df_old.copy()
            df_new = df_new.copy()
            df_old["_row_"] = range(len(df_old))
            df_new["_row_"] = range(len(df_new))
            join_cols = ["_row_"]
        comp = Compare(df_old, df_new, join_columns=join_cols,
                       df1_name="old", df2_name="new")
        return comp.report()
    except Exception as exc:  # datacompy report is a bonus, never a blocker
        return f"(datacompy report unavailable: {exc})"


# ------------------------------------------------------------------ engine cross-check

def crosscheck_docx(path) -> dict:
    """Run every available .docx engine and compare their outputs.

    Agreement across independent parsers is strong evidence the extraction
    is faithful (多引擎交叉驗證); disagreement pinpoints what to inspect.
    """
    from .word_extract import available_docx_engines, extract_docx

    engines = available_docx_engines()
    docs = {}
    for engine in engines:
        try:
            doc = extract_docx(path, engine=engine)
            for grid in doc.tables:
                grid.fill_merged()   # unify merged-cell semantics across engines
            docs[engine] = doc
        except Exception as exc:
            docs[engine] = exc

    report = {"file": str(path), "engines": engines, "pairs": []}
    names = [e for e in engines if not isinstance(docs[e], Exception)]
    for e, doc in docs.items():
        if isinstance(doc, Exception):
            report["pairs"].append({"engines": [e], "error": str(doc)})
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = docs[names[i]], docs[names[j]]
            text_sim = compare_texts(a.text, b.text).similarity
            table_pairs, only_a, only_b = pair_tables(a.tables, b.tables)
            cell_mismatches = 0
            for ti, tj, _score in table_pairs:
                d = compare_grids(a.tables[ti], b.tables[tj], auto_key=False,
                                  with_datacompy=False)
                cell_mismatches += len(d.changes) + len(d.added_rows) + len(d.removed_rows)
            report["pairs"].append({
                "engines": [names[i], names[j]],
                "text_similarity": round(text_sim, 4),
                "tables": {"old": len(a.tables), "new": len(b.tables),
                           "paired": len(table_pairs),
                           "only_first": only_a, "only_second": only_b},
                "cell_mismatches": cell_mismatches,
            })
    return report
