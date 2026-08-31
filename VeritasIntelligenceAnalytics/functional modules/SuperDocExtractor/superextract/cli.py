"""Command-line interface.

    python PLG_ENG001_SuperExtract.py doctor
    python PLG_ENG001_SuperExtract.py extract  FILE  [-o OUTDIR] [--engine E] [--encoding ENC] ...
    python PLG_ENG001_SuperExtract.py validate FILE
    python PLG_ENG001_SuperExtract.py compare  OLD NEW [--key COL] [-o OUTDIR] [--html]
    python PLG_ENG001_SuperExtract.py crosscheck FILE.docx
    python PLG_ENG001_SuperExtract.py selftest [--keep DIR]
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

import argparse
import os
import sys

from .availability import doctor_text
from .compare import crosscheck_docx, html_side_by_side
from .pipeline import compare_files, extract_any
from .report import (dump_debug_json, render_comparison_md, render_crosscheck_md,
                     render_extraction_md, write_json)
from .word_extract import ExtractionError


def _add_common_extract_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--engine", default="auto",
                   help="docx: auto|rawxml|python-docx|docx2python; "
                        "excel: auto|openpyxl|rawxml|xlrd (default: auto)")
    p.add_argument("--encoding", default=None,
                   help="explicit text encoding for CSV/TXT (skips auto-detection)")
    p.add_argument("--password", default=None, help="password for encrypted Office files")
    p.add_argument("--values", default="cached", choices=["cached", "formula"],
                   help="excel: read formula results (cached) or formula strings")
    p.add_argument("--delimiter", default=None, help="CSV delimiter (default: sniffed)")
    p.add_argument("--row-policy", default="repair",
                   choices=["repair", "skip", "strict", "keep"],
                   help="how to handle CSV rows with the wrong column count")
    p.add_argument("--no-repair", action="store_true",
                   help="skip the repair stage (raw extraction only)")
    p.add_argument("--drop-layout-tables", action="store_true",
                   help="exclude tables that look like layout/signature scaffolding")


def _extract_kwargs(args) -> dict:
    return dict(engine=args.engine, encoding=args.encoding, password=args.password,
                values=args.values, delimiter=args.delimiter, row_policy=args.row_policy,
                repair=not args.no_repair,
                keep_layout_tables=not args.drop_layout_tables)


def cmd_doctor(_args) -> int:
    print(doctor_text())
    return 0


def cmd_extract(args) -> int:
    result = extract_any(args.file, **_extract_kwargs(args))
    outdir = args.outdir or (os.path.splitext(str(args.file))[0] + "_extracted")
    os.makedirs(outdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(str(args.file)))[0]

    written = []
    if result.text:
        text_path = os.path.join(outdir, f"{stem}.txt")
        with open(text_path, "w", encoding="utf-8") as fh:
            fh.write(result.text + "\n")
        written.append(text_path)

    for i, grid in enumerate(result.tables, 1):
        safe = (grid.name or f"table_{i}").replace("/", "_").replace(" ", "_")
        csv_path = os.path.join(outdir, f"{stem}__{safe}.csv")
        # dump the grid verbatim (its own header row stays row 1)
        grid.to_csv(csv_path, header_row=None, encoding=args.output_encoding)
        written.append(csv_path)

    report = result.report()
    write_json(report, os.path.join(outdir, f"{stem}_report.json"))
    md_path = os.path.join(outdir, f"{stem}_report.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_extraction_md(report))
    written += [os.path.join(outdir, f"{stem}_report.json"), md_path]

    print(render_extraction_md(report))
    print("written:")
    for path in written:
        print(f"  {path}")
    return 0


def cmd_validate(args) -> int:
    result = extract_any(args.file, **_extract_kwargs(args))
    print(render_extraction_md(result.report()))
    errors = sum(1 for i in result.issues if i.severity == "error")
    return 1 if errors else 0


def cmd_compare(args) -> int:
    report = compare_files(args.old, args.new, key=args.key,
                           with_datacompy=not args.no_datacompy,
                           **_extract_kwargs(args))
    md = render_comparison_md(report)
    print(md)

    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
        write_json(report, os.path.join(args.outdir, "comparison.json"))
        with open(os.path.join(args.outdir, "comparison.md"), "w", encoding="utf-8") as fh:
            fh.write(md)
        if args.html:
            old = extract_any(args.old, **_extract_kwargs(args))
            new = extract_any(args.new, **_extract_kwargs(args))
            html = html_side_by_side(old.text, new.text, str(args.old), str(args.new))
            with open(os.path.join(args.outdir, "text_diff.html"), "w", encoding="utf-8") as fh:
                fh.write(html)
        print(f"reports written to {args.outdir}/")

    changed = any(not d["identical"] for d in report.get("table_diffs", []))
    text_changed = report.get("text_diff") and not report["text_diff"]["identical"]
    return 2 if (changed or text_changed) else 0


def cmd_crosscheck(args) -> int:
    report = crosscheck_docx(args.file)
    print(render_crosscheck_md(report))
    if args.json:
        print(dump_debug_json(report))
    return 0


def cmd_selftest(args) -> int:
    from .selftest import run_selftest
    return run_selftest(keep_dir=args.keep)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="super_extract",
        description="Word/Excel/CSV text & table extractor with encoding repair, "
                    "validation and comparison (擷取 → 修復 → 驗證 → 對照). "
                    "Works with the stdlib alone; optional libraries add power "
                    "(see: doctor).")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="show optional-library availability")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("extract", help="extract text + tables from one file")
    p.add_argument("file")
    p.add_argument("-o", "--outdir", default=None,
                   help="output directory (default: <file>_extracted/)")
    p.add_argument("--output-encoding", default="utf-8-sig",
                   help="encoding for written CSVs (default utf-8-sig so Excel "
                        "opens CJK correctly)")
    _add_common_extract_args(p)
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser("validate", help="extract + run validation checks, print findings")
    p.add_argument("file")
    _add_common_extract_args(p)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("compare", help="compare two files: text diff + table diff")
    p.add_argument("old")
    p.add_argument("new")
    p.add_argument("--key", default=None,
                   help="key column for row alignment (default: auto-detect)")
    p.add_argument("-o", "--outdir", default=None, help="write md/json reports here")
    p.add_argument("--html", action="store_true",
                   help="also write a side-by-side HTML text diff (needs --outdir)")
    p.add_argument("--no-datacompy", action="store_true",
                   help="skip the datacompy report even when installed")
    _add_common_extract_args(p)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("crosscheck",
                       help="parse a .docx with every available engine and compare them")
    p.add_argument("file")
    p.add_argument("--json", action="store_true", help="also dump the raw JSON")
    p.set_defaults(func=cmd_crosscheck)

    p = sub.add_parser("selftest",
                       help="generate tricky sample files and verify the whole pipeline")
    p.add_argument("--keep", default=None, metavar="DIR",
                   help="keep the generated samples/outputs in DIR")
    p.set_defaults(func=cmd_selftest)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"error: file not found — {exc.filename}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
