"""Report rendering: one markdown/JSON view over extraction + repair +
validation + comparison results, so the whole pipeline is auditable."""
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

import json


def write_json(payload: dict, path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)


def render_extraction_md(report: dict) -> str:
    lines = [f"# Extraction report — `{report['file']}`", ""]
    lines.append(f"- format: **{report['format']}** / engine: **{report['engine']}**")
    if report.get("encoding"):
        enc = report["encoding"]
        lines.append(f"- encoding: **{enc['encoding']}** "
                     f"(method: {enc['method']}, confidence {enc['confidence']})")
    if report.get("text") is not None:
        t = report["text"]
        lines.append(f"- text: {t['chars']} chars, {report.get('paragraphs', '?')} paragraph(s)")
        for fix in t.get("fixes", []):
            lines.append(f"  - repair: {fix}")
    lines.append(f"- tables: {len(report.get('tables', []))}")
    for tbl in report.get("tables", []):
        lines.append(f"  - **{tbl['name']}**: {tbl['rows']} x {tbl['cols']}"
                     + (f", {tbl['merged_filled']} merged cell(s) filled" if tbl.get("merged_filled") else "")
                     + (" (layout table?)" if tbl.get("layout_suspect") else ""))
        for r in tbl.get("repairs", []):
            lines.append(f"    - repair: {r}")
    for note in report.get("notes", []):
        lines.append(f"- note: {note}")

    issues = report.get("validation", [])
    lines += ["", f"## Validation — {len(issues)} finding(s)", ""]
    if not issues:
        lines.append("no findings — data looks clean")
    for issue in issues:
        lines.append(f"- `{issue['severity'].upper()}` **{issue['code']}**"
                     + (f" [{issue['location']}]" if issue.get("location") else "")
                     + f": {issue['message']}"
                     + (f" → {issue['suggestion']}" if issue.get("suggestion") else ""))
    return "\n".join(lines) + "\n"


def render_comparison_md(report: dict) -> str:
    lines = [f"# Comparison report", "",
             f"- old: `{report['old']}`", f"- new: `{report['new']}`", ""]

    text = report.get("text_diff")
    if text is not None:
        lines += ["## 1. Text diff (文字比對)", ""]
        if text["identical"]:
            lines.append("✅ text content is identical (after normalization)")
        else:
            lines.append(f"- similarity: **{text['similarity']:.2%}**  "
                         f"(+{text['added_lines']} / -{text['removed_lines']} lines)")
            lines += ["", "```diff", report.get("unified", "(diff too large, see JSON)"), "```"]
        lines.append("")

    pairing = report.get("table_pairing")
    if pairing is not None:
        lines += ["## 2. Table pairing (表格配對)", ""]
        lines.append(f"- old file tables: {pairing['old_count']} / new file tables: {pairing['new_count']}")
        for pair in pairing["pairs"]:
            lines.append(f"- paired: old **{pair['old']}** ↔ new **{pair['new']}** "
                         f"(similarity {pair['score']:.2f})")
        for name in pairing["only_old"]:
            lines.append(f"- ❌ removed table (only in old): **{name}**")
        for name in pairing["only_new"]:
            lines.append(f"- ➕ added table (only in new): **{name}**")
        lines.append("")

    for i, tdiff in enumerate(report.get("table_diffs", []), 1):
        lines += [f"## 3.{i} Table diff — {tdiff['label']}", ""]
        lines.append(f"- row alignment: `{tdiff['alignment']}`")
        for note in tdiff.get("notes", []):
            lines.append(f"- note: {note}")
        if tdiff["identical"]:
            lines.append("✅ tables are identical (after normalization)")
        else:
            if tdiff["added_columns"]:
                lines.append(f"- added column(s): {tdiff['added_columns']}")
            if tdiff["removed_columns"]:
                lines.append(f"- removed column(s): {tdiff['removed_columns']}")
            if tdiff["added_rows"]:
                lines.append(f"- added row(s): {tdiff['added_rows'][:20]}")
            if tdiff["removed_rows"]:
                lines.append(f"- removed row(s): {tdiff['removed_rows'][:20]}")
            if tdiff["changed_cells"]:
                lines += ["", "| row | column | old | new |", "| --- | --- | --- | --- |"]
                for ch in tdiff["changed_cells"][:200]:
                    lines.append(f"| {ch['row']} | {ch['column']} | {ch['old']} | {ch['new']} |")
                if len(tdiff["changed_cells"]) > 200:
                    lines.append(f"| ... | {len(tdiff['changed_cells']) - 200} more | | |")
        if tdiff.get("datacompy"):
            lines += ["", "<details><summary>datacompy report</summary>", "",
                      "```", tdiff["datacompy"], "```", "", "</details>"]
        lines.append("")
    return "\n".join(lines) + "\n"


def render_crosscheck_md(report: dict) -> str:
    lines = [f"# Engine cross-check — `{report['file']}`", "",
             f"engines: {', '.join(report['engines'])}", ""]
    for pair in report["pairs"]:
        if "error" in pair:
            lines.append(f"- ⚠️ {pair['engines'][0]}: failed with {pair['error']}")
            continue
        a, b = pair["engines"]
        tbl = pair["tables"]
        ok = pair["text_similarity"] > 0.98 and pair["cell_mismatches"] == 0 \
            and not tbl["only_first"] and not tbl["only_second"]
        mark = "✅" if ok else "⚠️"
        lines.append(f"- {mark} **{a} vs {b}**: text similarity {pair['text_similarity']:.2%}, "
                     f"{tbl['paired']} table pair(s), {pair['cell_mismatches']} cell mismatch(es)")
    lines += ["", "_High agreement across independent parsers = faithful extraction; "
                  "mismatches show exactly where to look._"]
    return "\n".join(lines) + "\n"


def dump_debug_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)
