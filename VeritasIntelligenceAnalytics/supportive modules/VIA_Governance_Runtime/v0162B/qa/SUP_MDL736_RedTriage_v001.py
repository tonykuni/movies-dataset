#!/usr/bin/env python3
"""VIA RED triage · distill a System Manager run into a paste-sized report.

The panoramic matrix HTML is complete but far too large to share in a chat or
a ticket. This tool reads an existing run directory (any v0162B run, including
crashed ones) and writes a compact Markdown triage of exactly what blocks the
GREEN gate: every RED file with its parser message, the round-trend, the top
Hydra risks and the multi-version SSOT groups. Read-only: it never touches
canonical trees and writes only <run>/reports/VIA_RED_Triage.md (or --out).

Usage:
  python via_red_triage_v001.py --base <Base>          # newest run under runtime/
  python via_red_triage_v001.py --run <run_dir>        # a specific run
  python via_red_triage_v001.py --base <Base> --out report.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

RUNTIME_RELATIVE = Path("supportive modules") / "VIA_Governance_Runtime" / "v0162B" / "runtime"
MAX_MESSAGE = 300
MAX_HYDRA = 12
MAX_SSOT = 12
MAX_PATHS_PER_GROUP = 4


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def newest_run(base: Path) -> Path | None:
    runtime = base / RUNTIME_RELATIVE
    if not runtime.is_dir():
        return None
    runs = sorted((d for d in runtime.iterdir() if d.is_dir() and d.name.startswith("run_")),
                  key=lambda d: d.name, reverse=True)
    return runs[0] if runs else None


def latest_matrix(run_dir: Path) -> tuple[list[dict[str, Any]], str]:
    for round_number in (3, 2, 1):
        for name in ("post_matrix.json", "pre_matrix.json"):
            path = run_dir / "rounds" / f"round_{round_number}" / name
            value = load_json(path)
            if isinstance(value, list):
                return value, f"round_{round_number}/{name}"
    return [], "none"


def relative_display(path_text: str, bases: list[Path]) -> str:
    display = path_text.replace("\\", "/")
    for base in bases:
        prefix = str(base).replace("\\", "/").rstrip("/") + "/"
        if display.lower().startswith(prefix.lower()):
            return display[len(prefix):]
    return display


def clip(text: str, limit: int = MAX_MESSAGE) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_report(run_dir: Path, base: Path | None) -> str:
    final = load_json(run_dir / "final_summary.v0162B.json") or {}
    failure = load_json(run_dir / "failure.v0162B.json")
    rounds = load_json(run_dir / "evidence" / "round_summaries.json") or []
    hydra = load_json(run_dir / "evidence" / "hydra_matrix.json") or []
    ssot = load_json(run_dir / "evidence" / "ssot_matrix.json") or []
    matrix, matrix_source = latest_matrix(run_dir)
    bases = [b for b in (base, Path(str(final["base"])) if final.get("base") else None) if b is not None]

    lines: list[str] = []
    lines.append("# VIA RED Triage · " + run_dir.name)
    summary = final.get("summary") or {}
    if final:
        lines.append("")
        lines.append("- Gate: `" + str(final.get("gate", "UNKNOWN")) + "`")
        lines.append("- Files {0} · GREEN {1} · YELLOW {2} · RED {3} · Hydra {4} · SSOT groups {5} · repair candidates {6}".format(
            summary.get("files", "?"), summary.get("green", "?"), summary.get("yellow", "?"),
            summary.get("red", "?"), final.get("hydra_count", "?"),
            final.get("ssot_group_count", "?"), final.get("repair_candidate_count", "?")))
    if failure:
        lines.append("")
        lines.append("**RUN FAILED**: `{0}: {1}`".format(
            failure.get("error_type", "?"), clip(failure.get("error_message", "?"))))

    if rounds:
        lines.append("")
        lines.append("## Round trend (RED before → after repair)")
        lines.append("")
        lines.append("| Round | Strategy | Pre RED | Post RED | Repairs | Gate |")
        lines.append("|---|---|---|---|---|---|")
        for row in rounds:
            lines.append("| {0} | {1} | {2} | {3} | {4} | {5} |".format(
                row.get("round", "?"), row.get("strategy", "?"),
                (row.get("pre") or {}).get("red", "?"), (row.get("post") or {}).get("red", "?"),
                row.get("repair_count", "?"), row.get("gate", "?")))

    red_rows = [row for row in matrix if row.get("state") == "RED"]
    lines.append("")
    lines.append("## RED files · {0} (from {1})".format(len(red_rows), matrix_source))
    for row in sorted(red_rows, key=lambda r: str(r.get("path", ""))):
        lines.append("")
        lines.append("### `" + relative_display(str(row.get("path", "?")), bases) + "`")
        lines.append("subsystem {0} · {1} bytes".format(row.get("subsystem", "?"), row.get("bytes", "?")))
        for issue in row.get("issues") or []:
            if issue.get("severity") != "RED":
                continue
            where = ""
            if issue.get("line") is not None:
                where = " line {0}".format(issue["line"])
                if issue.get("column") is not None:
                    where += ":{0}".format(issue["column"])
            lines.append("- **{0}**{1}: {2}".format(issue.get("kind", "?"), where, clip(issue.get("message", ""))))

    red_hydra = sorted((h for h in hydra if h.get("state") == "RED"),
                       key=lambda h: -int(h.get("score") or 0))
    lines.append("")
    lines.append("## Top Hydra risks (RED {0} of {1} total; showing up to {2})".format(
        len(red_hydra), len(hydra), MAX_HYDRA))
    for row in red_hydra[:MAX_HYDRA]:
        paths = [relative_display(p, bases) for p in (row.get("paths") or [])[:MAX_PATHS_PER_GROUP]]
        more = max(0, len(row.get("paths") or []) - MAX_PATHS_PER_GROUP)
        lines.append("- `{0}` · {1} · score {2}{3}".format(
            row.get("name", "?"), row.get("risk", "?"), row.get("score", "?"),
            (" · " + "; ".join(paths) + (" (+{0} more)".format(more) if more else "")) if paths else ""))

    multi = [g for g in ssot if g.get("alignment") == "MULTI_VERSION_REVIEW_REQUIRED"]
    multi.sort(key=lambda g: (-int(g.get("distinct_hashes") or 0), str(g.get("group", ""))))
    lines.append("")
    lines.append("## SSOT multi-version groups ({0} of {1} total; showing up to {2})".format(
        len(multi), len(ssot), MAX_SSOT))
    for group in multi[:MAX_SSOT]:
        paths = [relative_display(p, bases) for p in (group.get("paths") or [])[:MAX_PATHS_PER_GROUP]]
        more = max(0, len(group.get("paths") or []) - MAX_PATHS_PER_GROUP)
        lines.append("- `{0}` · {1} files · {2} hashes · {3}{4}".format(
            group.get("group", "?"), group.get("file_count", "?"), group.get("distinct_hashes", "?"),
            "; ".join(paths), " (+{0} more)".format(more) if more else ""))

    lines.append("")
    lines.append("_Read-only triage over existing run evidence; canonical trees untouched._")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="VIA Base directory (newest run is picked)")
    parser.add_argument("--run", help="specific run directory")
    parser.add_argument("--out", help="output Markdown path (default <run>/reports/VIA_RED_Triage.md)")
    args = parser.parse_args()

    base = Path(args.base).resolve() if args.base else None
    if args.run:
        run_dir = Path(args.run).resolve()
    elif base is not None:
        found = newest_run(base)
        if found is None:
            print("No run_* directory under " + str(base / RUNTIME_RELATIVE), file=sys.stderr)
            return 2
        run_dir = found
    else:
        parser.error("provide --base or --run")
        return 2
    if not run_dir.is_dir():
        print("Run directory not found: " + str(run_dir), file=sys.stderr)
        return 2

    report = build_report(run_dir, base)
    out = Path(args.out).resolve() if args.out else run_dir / "reports" / "VIA_RED_Triage.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8", newline="\n")
    print(report)
    print("Saved: " + str(out), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
