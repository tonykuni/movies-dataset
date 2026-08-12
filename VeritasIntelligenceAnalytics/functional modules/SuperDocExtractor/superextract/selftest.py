"""End-to-end selftest: generate pathological samples, run the full
extract -> repair -> validate -> compare pipeline, assert the outcomes.

    python super_extract.py selftest [--keep DIR]

Every check maps to a documented real-world failure mode (merged cells,
tracked changes, nested tables, encodings, ragged CSVs, fake extensions...).
"""
from __future__ import annotations

import datetime as _dt
import shutil
import tempfile
import traceback

from .availability import has
from .compare import crosscheck_docx
from .excel_extract import extract_excel
from .pipeline import compare_files, extract_any
from .samples import build_all
from .word_extract import ExtractionError


# ------------------------------------------------------------------ checks

def check_docx_text_and_track_changes(paths):
    """Word: tracked deletions excluded, insertions included, header captured."""
    res = extract_any(paths["docx_v1"])
    assert "舊條款已刪除" not in res.text, "tracked DELETION leaked into the text"
    assert "並新增保密條款" in res.text, "tracked INSERTION missing from the text"
    assert "機密文件頁首" in res.text, "header text missing"
    assert any("DELETIONS" in n for n in res.notes), "track-changes note missing"


def check_docx_invisible_char_repair(paths):
    """Word: zero-width space and NBSP repaired in text."""
    res = extract_any(paths["docx_v1"])
    assert "範例科技" in res.text, "zero-width space not removed (範例\\u200b科技)"
    assert "\u200b" not in res.text and "\xa0" not in res.text
    assert any("zero-width" in f for f in res.text_fixes), "repair not recorded in audit"


def check_docx_merges(paths):
    """Word: vMerge/gridSpan filled precisely; true empty cell untouched."""
    res = extract_any(paths["docx_v1"])
    main = res.tables[0]
    assert main.rows[0] == ["類別", "品名", "數量", "單價"], f"header wrong: {main.rows[0]}"
    assert main.rows[1][0] == "3C設備"
    assert main.rows[2][0] == "3C設備", "vMerge continuation not filled from anchor"
    assert main.rows[3][0] == "備註" and main.rows[3][1] == "備註", "gridSpan not filled"
    assert main.rows[3][2] == "", "truly-empty cell was wrongly filled (ffill 誤殺)"
    assert main.rows[1][2] == "10", f"full-width １０ not normalized: {main.rows[1][2]!r}"


def check_docx_nested_and_layout(paths):
    """Word: nested table flattened + lifted; layout table flagged."""
    res = extract_any(paths["docx_v1"])
    outer = res.tables[1]
    assert "內層A" in outer.rows[0][1], "nested table not flattened into outer cell"
    nested = [g for g in res.tables if "cell(" in (g.name or "")]
    assert nested and nested[0].rows[0] == ["內層A", "內層B"], "nested table not lifted"
    layout = [g for g in res.tables if g.is_layout_table()]
    assert layout, "signature layout table not flagged"


def check_docx_crosscheck(paths):
    """Word: independent engines agree (多引擎交叉驗證)."""
    report = crosscheck_docx(paths["docx_v1"])
    assert "rawxml" in report["engines"]
    pairs = {tuple(p["engines"]): p for p in report["pairs"] if "error" not in p}
    for combo, pair in pairs.items():
        if "rawxml" in combo and "python-docx" in combo:
            # Known engine difference: python-docx drops text inside w:ins
            # (tracked insertions), so similarity is high but not 1.0 —
            # exactly the kind of gap cross-checking exists to surface.
            assert pair["text_similarity"] > 0.9, \
                f"rawxml vs python-docx text similarity too low: {pair}"
            assert pair["cell_mismatches"] == 0, f"table cells disagree: {pair}"


def check_xlsx_both_engines(paths):
    """Excel: leading zeros, dates, cached formulas, merges — on BOTH engines."""
    engines = ["rawxml"] + (["openpyxl"] if has("openpyxl") else [])
    for engine in engines:
        wb = extract_excel(paths["xlsx"], engine=engine)
        grid = wb.sheets["訂單"]
        label = f"[engine={engine}]"
        assert grid.rows[1][0] == "00123", f"{label} leading zeros lost: {grid.rows[1][0]!r}"
        date_val = grid.rows[1][2]
        assert isinstance(date_val, _dt.datetime) and date_val.date() == _dt.date(2023, 7, 1), \
            f"{label} date serial not converted: {date_val!r}"
        assert grid.rows[1][3] == 52000, f"{label} cached formula value wrong: {grid.rows[1][3]!r}"
        assert wb.formulas.get("訂單"), f"{label} formula map missing"

        grid.fill_merged()
        assert grid.rows[2][4] == "研發部", f"{label} merged E2:E3 not filled"
        assert grid.rows[2][3] == "", f"{label} truly-empty D3 was wrongly filled"

    # values='formula' returns the formula string instead of the cache
    wb_f = extract_excel(paths["xlsx"], engine="rawxml", values="formula")
    assert str(wb_f.sheets["訂單"].rows[1][3]).startswith("=50000"), "formula mode broken"


def check_xlsx_validation(paths):
    """Excel: pipeline flags leading-zero identifiers and trims padding."""
    res = extract_any(paths["xlsx"])
    codes = {i.code for i in res.issues}
    assert "leading-zeros" in codes, f"leading-zero warning missing; got {codes}"
    grid = res.tables[0]
    assert grid.rows[3][4] == "業務部", f"whitespace padding not trimmed: {grid.rows[3][4]!r}"


def check_csv_big5(paths):
    """CSV: Big5/cp950 auto-detected; quoted comma kept in one field."""
    res = extract_any(paths["big5"])
    grid = res.tables[0]
    assert grid.rows[0][0] == "產品編號", f"Big5 decode failed: {grid.rows[0]}"
    assert grid.rows[1][2] == "台北市, 台灣", f"quoted comma split: {grid.rows[1]}"
    assert res.encoding["encoding"].lower() in ("cp950", "big5", "big5hkscs"), res.encoding


def check_csv_bom(paths):
    """CSV: UTF-8 BOM stripped from the first header cell."""
    res = extract_any(paths["bom"])
    grid = res.tables[0]
    assert grid.rows[0][0] == "id", f"BOM leaked into header: {grid.rows[0][0]!r}"
    assert grid.rows[1][1] == "測試"


def check_csv_mojibake(paths):
    """CSV: double-encoded mojibake repaired cell by cell."""
    res = extract_any(paths["mojibake"])
    grid = res.tables[0]
    assert grid.rows[0][0] == "編號", f"mojibake header not repaired: {grid.rows[0][0]!r}"
    assert grid.rows[1][1] == "台北", f"mojibake cell not repaired: {grid.rows[1][1]!r}"


def check_csv_ragged(paths):
    """CSV: short rows padded, overflow merged, trailing empties dropped."""
    res = extract_any(paths["ragged"])
    grid = res.tables[0]
    assert grid.n_cols == 3, f"width should stay 3, got {grid.n_cols}"
    assert grid.rows[2] == ["4", "5", ""], f"short row not padded: {grid.rows[2]}"
    assert grid.rows[3] == ["6", "7", "8,9"], f"overflow not merged: {grid.rows[3]}"
    assert grid.n_rows == 4, f"trailing empty row kept: {grid.n_rows} rows"


def check_csv_semicolon(paths):
    """CSV: non-comma delimiter sniffed automatically."""
    res = extract_any(paths["semicolon"])
    assert res.tables[0].rows[0] == ["id", "name", "total"], res.tables[0].rows[0]


def check_fake_docx_rejected(paths):
    """A .docx that is really OLE2 gets a helpful error, not BadZipFile."""
    try:
        extract_any(paths["fake_docx"])
    except ExtractionError as exc:
        msg = str(exc)
        assert "OLE2" in msg or "legacy" in msg, f"unhelpful message: {msg}"
        return
    raise AssertionError("fake .docx (OLE2 bytes) was not rejected")


def check_compare_docx_versions(paths):
    """Compare v1 vs v2: exact changed cell + added row + text diff."""
    report = compare_files(paths["docx_v1"], paths["docx_v2"])

    assert not report["text_diff"]["identical"], "text edit not detected"
    assert any("3月1日" in ln for ln in report["unified"].splitlines()
               if ln.startswith("+")), "edited paragraph not in diff"

    pairing = report["table_pairing"]
    assert pairing["pairs"], "main tables were not paired"
    main_diff = report["table_diffs"][0]
    assert main_diff["alignment"].startswith("key:"), \
        f"key column not auto-detected: {main_diff['alignment']}"

    changes = main_diff["changed_cells"]
    assert len(changes) == 1, f"expected exactly 1 changed cell, got {changes}"
    change = changes[0]
    assert change["column"] == "單價" and "筆記型電腦" in change["row"], change
    assert "30,000" in change["old"] and "32,000" in change["new"], change

    assert any("鍵盤" in r for r in main_diff["added_rows"]), \
        f"added row 鍵盤 missed: {main_diff['added_rows']}"
    assert not main_diff["removed_rows"]

    if has("datacompy") and has("pandas"):
        assert main_diff.get("datacompy"), "datacompy report missing"


def check_numeric_equivalence(paths):
    """'1,000' == 1000, '１０' == '10', but '00123' stays a string identifier."""
    from .compare import cells_equal
    assert cells_equal("1,000", 1000)
    assert cells_equal("１０", "10")
    assert cells_equal(" 100 ", "100")
    assert not cells_equal("00123", 123), "leading-zero id must NOT equal the number"
    assert not cells_equal("100", "101")


CHECKS = [
    check_docx_text_and_track_changes,
    check_docx_invisible_char_repair,
    check_docx_merges,
    check_docx_nested_and_layout,
    check_docx_crosscheck,
    check_xlsx_both_engines,
    check_xlsx_validation,
    check_csv_big5,
    check_csv_bom,
    check_csv_mojibake,
    check_csv_ragged,
    check_csv_semicolon,
    check_fake_docx_rejected,
    check_compare_docx_versions,
    check_numeric_equivalence,
]


def run_selftest(keep_dir: str | None = None) -> int:
    outdir = keep_dir or tempfile.mkdtemp(prefix="superextract_selftest_")
    paths = build_all(outdir)
    print(f"samples generated in {outdir}\n")

    failures = 0
    for check in CHECKS:
        name = check.__name__.replace("check_", "")
        desc = (check.__doc__ or "").strip().splitlines()[0]
        try:
            check(paths)
            print(f"  PASS  {name:<32} {desc}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {name:<32} {exc}")
        except Exception:
            failures += 1
            print(f"  ERROR {name:<32}")
            traceback.print_exc()

    total = len(CHECKS)
    print(f"\n{total - failures}/{total} checks passed"
          + ("" if failures else " — pipeline verified ✔"))
    if keep_dir is None:
        shutil.rmtree(outdir, ignore_errors=True)
    else:
        print(f"samples kept in {outdir}")
    return 1 if failures else 0
