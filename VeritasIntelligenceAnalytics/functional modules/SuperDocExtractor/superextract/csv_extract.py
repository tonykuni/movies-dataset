"""CSV extraction with encoding detection, dialect sniffing and ragged-row
repair (欄位數量不一致 / ParserError territory).

Row-width policies
------------------
repair (default)
    short rows are padded with '', overlong rows have their overflow merged
    into the last column; every touched row is reported.
skip   : malformed rows are dropped (and reported)
strict : raise on the first malformed row
keep   : leave rows as-is (grid is padded rectangular at the end)
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

import csv
import io
from collections import Counter
from dataclasses import dataclass, field

from .encoding import DetectionResult, decode_bytes
from .tableops import Grid

_DELIMITER_CANDIDATES = [",", ";", "\t", "|", ":"]


@dataclass
class CsvResult:
    grid: Grid
    encoding: DetectionResult = None
    delimiter: str = ","
    notes: list = field(default_factory=list)


def sniff_dialect(sample: str):
    """Return (delimiter, quotechar). csv.Sniffer first, frequency fallback."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(_DELIMITER_CANDIDATES))
        return dialect.delimiter, dialect.quotechar or '"'
    except csv.Error:
        pass
    # frequency analysis over the first lines, outside quoted sections
    lines = [ln for ln in sample.splitlines() if ln.strip()][:20]
    best, best_score = ",", -1
    for cand in _DELIMITER_CANDIDATES:
        counts = []
        for ln in lines:
            in_quote = False
            n = 0
            for ch in ln:
                if ch == '"':
                    in_quote = not in_quote
                elif ch == cand and not in_quote:
                    n += 1
            counts.append(n)
        if not counts or max(counts) == 0:
            continue
        consistency = Counter(counts).most_common(1)[0][1] / len(counts)
        score = consistency * (sum(counts) / len(counts))
        if score > best_score:
            best, best_score = cand, score
    return best, '"'


def extract_csv(path, encoding: str | None = None, delimiter: str | None = None,
                row_policy: str = "repair") -> CsvResult:
    with open(path, "rb") as fh:
        data = fh.read()
    text, det = decode_bytes(data, encoding=encoding)

    if delimiter is None:
        delimiter, quotechar = sniff_dialect(text[:64 * 1024])
    else:
        quotechar = '"'

    reader = csv.reader(io.StringIO(text), delimiter=delimiter, quotechar=quotechar)
    raw_rows = [row for row in reader]
    # trailing fully-empty rows are file artifacts
    while raw_rows and not any(v.strip() for v in raw_rows[-1]):
        raw_rows.pop()

    notes: list[str] = []
    if det.method != "explicit":
        notes.append(f"encoding detected as {det.encoding} via {det.method} "
                     f"(confidence {det.confidence:.2f})")
    notes.extend(det.notes)
    if delimiter != ",":
        notes.append(f"delimiter sniffed as {delimiter!r}")

    rows, repair_notes = _apply_row_policy(raw_rows, row_policy)
    notes.extend(repair_notes)

    grid = Grid(rows=rows, source=str(path), name="csv", notes=list(notes))
    grid.finalize()
    return CsvResult(grid=grid, encoding=det, delimiter=delimiter, notes=notes)


def _apply_row_policy(rows: list, policy: str):
    if not rows or policy == "keep":
        return rows, []

    widths = Counter(len(r) for r in rows)
    target = widths.most_common(1)[0][0]
    bad = [i for i, r in enumerate(rows) if len(r) != target]
    if not bad:
        return rows, []

    notes = [f"{len(bad)} of {len(rows)} row(s) deviate from the dominant width of {target} column(s)"]
    if policy == "strict":
        i = bad[0]
        raise ValueError(f"row {i + 1} has {len(rows[i])} column(s), expected {target} "
                         f"(row_policy='strict')")
    if policy == "skip":
        keep = [r for i, r in enumerate(rows) if i not in set(bad)]
        notes.append(f"row_policy='skip': dropped row(s) {[i + 1 for i in bad][:20]}")
        return keep, notes

    # policy == "repair"
    fixed = []
    padded, merged = [], []
    for i, row in enumerate(rows):
        if len(row) < target:
            if any(v.strip() for v in row):
                padded.append(i + 1)
            fixed.append(row + [""] * (target - len(row)))
        elif len(row) > target:
            overflow = row[target - 1:]
            # pure trailing empties are trimmed silently; real data is merged
            if any(v.strip() for v in row[target:]):
                merged.append(i + 1)
                fixed.append(row[: target - 1] + [",".join(overflow).rstrip(",")])
            else:
                fixed.append(row[:target])
        else:
            fixed.append(row)
    if padded:
        notes.append(f"row_policy='repair': padded short row(s) {padded[:20]} with empty cells")
    if merged:
        notes.append(f"row_policy='repair': merged overflow columns into the last cell "
                     f"on row(s) {merged[:20]} — verify these rows manually")
    return fixed, notes
