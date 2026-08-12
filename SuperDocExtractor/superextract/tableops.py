"""Grid: the common table structure every extractor produces.

A Grid is a rectangular list-of-lists plus *merge provenance*: for every
cell that was part of a merged region we remember the anchor cell it came
from. That lets the repair step fill ONLY genuinely merged cells — a
truly-empty cell is never overwritten by `ffill`-style guessing
(the classic「向下填補誤殺真實空值」bug).
"""
from __future__ import annotations

import csv
import datetime as _dt
import io
import re
from dataclasses import dataclass, field

from .availability import has, load
from .textclean import clean_text, normalize_for_compare


@dataclass
class Grid:
    rows: list                      # list[list[Any]] — rectangular after finalize()
    merge_map: dict = field(default_factory=dict)   # {(r, c): (anchor_r, anchor_c)}
    source: str = ""                # e.g. "report.docx : table 2" / "book.xlsx : Sheet1"
    name: str = ""                  # sheet name / table label
    notes: list = field(default_factory=list)
    nested: list = field(default_factory=list)      # nested Grids found inside cells
    repairs: list = field(default_factory=list)     # audit log of repair actions

    # ---------------------------------------------------------- shape
    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def n_cols(self) -> int:
        return max((len(r) for r in self.rows), default=0)

    def finalize(self) -> "Grid":
        """Pad ragged rows with '' so the grid is rectangular."""
        width = self.n_cols
        for r in self.rows:
            if len(r) < width:
                r.extend([""] * (width - len(r)))
        return self

    # ---------------------------------------------------------- repair
    def fill_merged(self) -> int:
        """Copy each merge anchor's value into its continuation cells.

        Only cells listed in merge_map are touched, so genuinely empty
        cells stay empty. Returns the number of cells filled.
        """
        filled = 0
        for (r, c), (ar, ac) in sorted(self.merge_map.items()):
            if (r, c) == (ar, ac):
                continue
            try:
                anchor_val = self.rows[ar][ac]
            except IndexError:
                continue
            if r < len(self.rows) and c < len(self.rows[r]):
                if self.rows[r][c] in ("", None):
                    self.rows[r][c] = anchor_val
                    filled += 1
        if filled:
            self.repairs.append(f"filled {filled} merged-continuation cell(s) from their anchors")
        return filled

    def clean_cells(self, **clean_kwargs) -> int:
        """Run textclean.clean_text on every string cell. Returns cells changed."""
        changed = 0
        for r, row in enumerate(self.rows):
            for c, val in enumerate(row):
                if isinstance(val, str) and val:
                    res = clean_text(val, collapse_blank_lines=False, **clean_kwargs)
                    new_val = res.text.strip()   # cell values are always trimmed
                    if new_val != val:
                        row[c] = new_val
                        changed += 1
        if changed:
            self.repairs.append(f"cleaned {changed} cell(s) (invisible chars / whitespace / normalization)")
        return changed

    def drop_empty_rows(self) -> int:
        keep = [r for r in self.rows if any(str(v).strip() for v in r)]
        dropped = len(self.rows) - len(keep)
        if dropped:
            self.rows = keep
            self.repairs.append(f"dropped {dropped} fully-empty row(s)")
        return dropped

    # ---------------------------------------------------------- headers
    def header(self, header_row: int = 0) -> list:
        """Deduplicated, non-empty column names taken from *header_row*."""
        if not self.rows:
            return []
        raw = [str(v).strip() if v is not None else "" for v in self.rows[header_row]]
        return dedupe_headers(raw)

    def body(self, header_row: int = 0) -> list:
        return [row for i, row in enumerate(self.rows) if i > header_row]

    def to_records(self, header_row: int = 0) -> list:
        """list[dict] keyed by the deduplicated header."""
        cols = self.header(header_row)
        out = []
        for row in self.body(header_row):
            rec = {}
            for i, col in enumerate(cols):
                rec[col] = row[i] if i < len(row) else ""
            out.append(rec)
        return out

    # ---------------------------------------------------------- exports
    def to_dataframe(self, header_row: int | None = 0):
        """pandas.DataFrame (raises RuntimeError when pandas is missing)."""
        if not has("pandas"):
            raise RuntimeError("pandas is not installed — use to_records()/to_csv() instead")
        pd = load("pandas")
        if header_row is None:
            return pd.DataFrame(self.rows)
        return pd.DataFrame(self.body(header_row), columns=self.header(header_row))

    def to_csv(self, path=None, header_row: int | None = None, encoding: str = "utf-8-sig") -> str:
        """Write CSV (utf-8-sig by default so Excel opens CJK correctly).

        With header_row=None the grid is dumped verbatim; otherwise the
        deduplicated header is emitted first.
        """
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        if header_row is None:
            for row in self.rows:
                writer.writerow([_stringify(v) for v in row])
        else:
            writer.writerow(self.header(header_row))
            for row in self.body(header_row):
                writer.writerow([_stringify(v) for v in row])
        data = buf.getvalue()
        if path is not None:
            with open(path, "w", encoding=encoding, newline="") as fh:
                fh.write(data)
        return data

    def to_markdown(self, header_row: int | None = 0, max_col_width: int = 40) -> str:
        if not self.rows:
            return "(empty table)"
        if header_row is None:
            head = [f"c{i+1}" for i in range(self.n_cols)]
            body = self.rows
        else:
            head, body = self.header(header_row), self.body(header_row)

        def cell(v):
            s = _stringify(v).replace("\n", " ").replace("|", "\\|")
            return s if len(s) <= max_col_width else s[: max_col_width - 1] + "…"

        lines = ["| " + " | ".join(cell(h) for h in head) + " |",
                 "| " + " | ".join("---" for _ in head) + " |"]
        for row in body:
            padded = list(row) + [""] * (len(head) - len(row))
            lines.append("| " + " | ".join(cell(v) for v in padded[: len(head)]) + " |")
        return "\n".join(lines)

    def to_text(self) -> str:
        """Plain-text rendering (used when flattening nested tables)."""
        return "\n".join(" | ".join(_stringify(v) for v in row) for row in self.rows)

    # ---------------------------------------------------------- heuristics
    def is_layout_table(self, empty_threshold: float = 0.75) -> bool:
        """True for signature blocks / layout scaffolding rather than data:
        tiny grids or grids that are mostly empty."""
        if self.n_rows == 0 or self.n_cols == 0:
            return True
        if self.n_rows < 2 or self.n_cols < 2:
            return True
        total = self.n_rows * self.n_cols
        empty = sum(1 for row in self.rows for v in row if not str(v).strip())
        return (empty / total) > empty_threshold

    def content_signature(self, sample: int = 30) -> set:
        """Normalized sample of cell values, used for table pairing."""
        sig = set()
        for row in self.rows:
            for v in row:
                s = normalize_for_compare(v)
                if s:
                    sig.add(s)
                    if len(sig) >= sample:
                        return sig
        return sig


# ------------------------------------------------------------------ helpers

def _stringify(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, (_dt.datetime, _dt.date)):
        iso = v.isoformat()
        return iso[:-9] if iso.endswith("T00:00:00") else iso
    return str(v)


def dedupe_headers(names: list) -> list:
    """Make header names non-empty and unique: '' -> col_N, dup -> dup_2..."""
    seen: dict[str, int] = {}
    out = []
    for i, raw in enumerate(names):
        name = str(raw).strip() if raw is not None else ""
        if not name or name.lower() in ("nan", "none"):
            name = f"col_{i + 1}"
        base = name
        if base in seen:
            seen[base] += 1
            name = f"{base}_{seen[base]}"
        else:
            seen[base] = 1
        out.append(name)
    return out


_NUM_RE = re.compile(r"^[+-]?\d{1,3}(,\d{3})*(\.\d+)?$|^[+-]?\d+(\.\d+)?$")


def coerce_number(value):
    """'1,000' -> 1000.0 / '42' -> 42 — or the original value untouched.

    Values with leading zeros ('00123') are deliberately kept as strings:
    they are identifiers, not numbers (員工編號/電話 leading-zero problem).
    """
    if not isinstance(value, str):
        return value
    s = normalize_for_compare(value)
    if not s or not _NUM_RE.match(s):
        return value
    bare = s.lstrip("+-")
    if bare.startswith("0") and not bare.startswith("0.") and bare != "0":
        return value  # leading-zero identifier
    s = s.replace(",", "")
    try:
        return int(s) if "." not in s else float(s)
    except ValueError:
        return value
