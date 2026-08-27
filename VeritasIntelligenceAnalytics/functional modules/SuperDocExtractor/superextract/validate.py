"""Validation (驗證): structural and content checks on extracted data.

Each check emits Issues instead of failing, so one report shows everything
that deserves a human look: duplicate headers, layout tables, leading-zero
identifiers, ambiguous dates, invisible characters, mixed types, ...
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

import re
from dataclasses import dataclass, field

from .tableops import Grid, _NUM_RE
from .textclean import find_invisible_chars, mojibake_score

SEVERITIES = ("info", "warning", "error")


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    location: str = ""
    suggestion: str = ""

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v}

    def __str__(self) -> str:
        loc = f" [{self.location}]" if self.location else ""
        tip = f" -> {self.suggestion}" if self.suggestion else ""
        return f"{self.severity.upper():7} {self.code}{loc}: {self.message}{tip}"


_LEADING_ZERO_RE = re.compile(r"^0\d+$")
_DATE_SLASH_RE = re.compile(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$")


def validate_text(text: str, location: str = "text") -> list:
    issues: list[Issue] = []
    invisibles = find_invisible_chars(text)
    if invisibles:
        top = ", ".join(f"{k} x{v}" for k, v in list(invisibles.items())[:5])
        issues.append(Issue("warning", "invisible-chars",
                            f"invisible/suspicious characters present: {top}",
                            location, "clean_text() removes them before comparison"))
    score = mojibake_score(text)
    if score:
        issues.append(Issue("warning", "mojibake",
                            f"possible mojibake detected (score {score})",
                            location, "run the repair step (ftfy / recode) and re-check"))
    if "\r" in text:
        issues.append(Issue("info", "mixed-newlines",
                            "carriage returns present (CRLF/CR)", location,
                            "normalized to LF by clean_text()"))
    return issues


def validate_grid(grid: Grid, header_row: int = 0) -> list:
    issues: list[Issue] = []
    where = grid.source or grid.name or "table"

    if grid.n_rows == 0 or grid.n_cols == 0:
        issues.append(Issue("warning", "empty-table", "table has no content", where))
        return issues

    if grid.is_layout_table():
        issues.append(Issue("info", "layout-table",
                            f"looks like a layout/signature table "
                            f"({grid.n_rows}x{grid.n_cols}), probably not data",
                            where, "consider excluding it from data comparison"))

    # header checks (on the raw header row, before dedupe_headers fixes it)
    raw_header = [str(v).strip() for v in grid.rows[header_row]] if grid.n_rows > header_row else []
    empties = sum(1 for h in raw_header if not h)
    if empties:
        issues.append(Issue("warning", "empty-header-cells",
                            f"{empties} empty header cell(s)", where,
                            "auto-named col_N by dedupe_headers()"))
    dupes = {h for h in raw_header if h and raw_header.count(h) > 1}
    if dupes:
        issues.append(Issue("warning", "duplicate-headers",
                            f"duplicate header name(s): {sorted(dupes)}", where,
                            "suffixed _2, _3... by dedupe_headers()"))

    merged = sum(1 for k, v in grid.merge_map.items() if k != v)
    if merged:
        issues.append(Issue("info", "merged-cells",
                            f"{merged} cell(s) belong to merged regions", where,
                            "fill_merged() copies anchor values into them"))

    body = grid.body(header_row)
    if body:
        _validate_columns(grid, body, where, issues)

    invisible_cells = 0
    for row in grid.rows:
        for v in row:
            if isinstance(v, str) and find_invisible_chars(v):
                invisible_cells += 1
    if invisible_cells:
        issues.append(Issue("warning", "invisible-chars",
                            f"{invisible_cells} cell(s) contain invisible characters", where,
                            "clean_cells() removes them"))
    return issues


def _validate_columns(grid: Grid, body: list, where: str, issues: list):
    n_cols = grid.n_cols
    headers = grid.header()
    for c in range(n_cols):
        col_name = headers[c] if c < len(headers) else f"col_{c + 1}"
        values = [row[c] for row in body if c < len(row)]
        strings = [str(v).strip() for v in values if str(v).strip()]
        if not strings:
            continue

        leading_zero = sum(1 for s in strings if _LEADING_ZERO_RE.match(s))
        if leading_zero:
            issues.append(Issue("warning", "leading-zeros",
                                f"column {col_name!r}: {leading_zero} value(s) with leading zeros "
                                "(identifiers, not numbers)", where,
                                "keep this column as text; numeric coercion would drop the zeros"))

        numeric = sum(1 for s in strings if _NUM_RE.match(s.replace(",", "")))
        if 0 < numeric < len(strings) and numeric / len(strings) >= 0.5:
            examples = [s for s in strings if not _NUM_RE.match(s.replace(",", ""))][:3]
            issues.append(Issue("warning", "mixed-types",
                                f"column {col_name!r}: {numeric}/{len(strings)} numeric but "
                                f"also non-numeric values e.g. {examples}", where,
                                "decide a single type before comparing"))

        ambiguous = 0
        for s in strings:
            m = _DATE_SLASH_RE.match(s)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                if a <= 12 and b <= 12 and a != b:
                    ambiguous += 1
        if ambiguous:
            issues.append(Issue("warning", "ambiguous-dates",
                                f"column {col_name!r}: {ambiguous} date(s) like '10/11/2026' where "
                                "day/month order cannot be inferred", where,
                                "parse with an explicit format (%d/%m/%Y vs %m/%d/%Y)"))

        padded = sum(1 for v in values if isinstance(v, str) and v != v.strip() and v.strip())
        if padded:
            issues.append(Issue("info", "whitespace-padding",
                                f"column {col_name!r}: {padded} value(s) wrapped in whitespace",
                                where, "clean_cells() trims them"))


def summarize_issues(issues: list) -> dict:
    counts = {s: 0 for s in SEVERITIES}
    for issue in issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1
    return counts
