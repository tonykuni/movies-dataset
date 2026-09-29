"""SYSTEM MANAGER / 使用者：來源證據整合模組 v0100。
重用既有 Layout 修復結果，四來源分立編號，保留原文、空值、0、表格與座標；
同語意跨來源對照、來源幾何覆蓋及失敗區域升級規劃。升級規劃不等於 OCR 已執行。
規則沿用 VRN_Evidence_Core；編號沿用 VCGC NumberingSystem；不修改已成功鎖定引擎。
本模組的 REVIEW 不宣稱全文件驗收；更新 2026-09-29T15:38:10+00:00"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
VERSION = "v0100"
ENGINE = "VRN_ENG114_SourceProvenance"
CONTRACT = REG / "VRN_SourceProvenance_SSOT_v0100.json"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def owners():
    # Numbering owns IDs. Evidence Core owns field rules. Successful extraction remains frozen.
    numbering = load(max(REG.glob("CGC_MDL237_NumberingSystem_v*.py")), "_provenance_numbering")
    core = load(HERE / "engine" / "VRN_Evidence_Core.py", "_provenance_core")
    return numbering, core


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def observation(numbering, catalog, document, lane, field, value, locator, raw=None, context=None, glyphs=None):
    code = numbering.observation_id(catalog[lane], document, locator, field)
    row = {"id": code, "source_id": catalog[lane], "lane": lane, "document_sha256": document,
           "field": field, "value": value, "raw": raw, "locator": locator,
           "context": context or {}, "glyph_ids": sorted(set(glyphs or [])),
           "state": "NULL_ALLOWED" if value is None else "EXTRACTED", "version": VERSION}
    row["revision_sha256"] = digest(row)
    return row


def reconcile(observations):
    """Compare only identical semantic contexts; same glyphs or repeated engines are one source."""
    groups = defaultdict(list)
    for row in observations:
        if row["field"] in {"text", "table_cell", "filename"}:
            continue
        groups[(row["document_sha256"], row["field"], digest(row["context"]))].append(row)
    results = []
    for (document, field, _), rows in groups.items():
        present = [r for r in rows if r["value"] is not None]
        unique = {digest(r["value"]) for r in present}
        independent = []
        for row in sorted(present, key=lambda r: r["id"]):
            if not any(row["id"] == x["id"] or (row["glyph_ids"] and set(row["glyph_ids"]) & set(x["glyph_ids"])) for x in independent):
                independent.append(row)
        state = "CONFLICT" if len(unique) > 1 else "AGREE" if len(independent) >= 2 else "SINGLE_SOURCE" if present else "NULL_ALLOWED"
        results.append({"document_sha256": document, "field": field, "state": state,
                        "observations": [r["id"] for r in rows], "independent_count": len(independent),
                        "proves_complete": False})
    return results


def inside(word, box):
    if not word or not box:
        return False
    x, y = (word[0] + word[2]) / 2, (word[1] + word[3]) / 2
    return box[0] - 1 <= x <= box[2] + 1 and box[1] - 1 <= y <= box[3] + 1


def plan_escalation(failures, attempts, contract):
    """Only failed regions advance. Budget exhaustion stays REVIEW, never GREEN."""
    plan = []
    for region, reason in sorted(failures.items()):
        prior = attempts.get(region, [])
        elapsed = sum(x.get("seconds", 0) for x in prior)
        stages = contract["escalation"]
        n = len(prior)
        capped = n >= contract["parameters"]["max_attempts_per_region"] or elapsed >= contract["parameters"]["max_seconds_per_region"] or n >= len(stages)
        plan.append({"region": region, "reason": reason, "state": "REVIEW_BUDGET" if capped else "RETRY_REQUIRED",
                     "next": None if capped else stages[n], "seconds_used": elapsed,
                     "automatic_execution": False})
    return plan


def page_fields(core, lines):
    # No filename is passed: the source lane must not borrow a filename result.
    proof = core.analyze("", lines, text_layer=bool(lines))
    result = {}
    for name, key in (("ticker", "ticker"), ("report_date", "page_date"), ("broker", "broker"),
                      ("rating", "rating"), ("target_price", "target_price"), ("current_price", "current_price")):
        evidence = proof.get(key) or {}
        value_key = {"ticker": "ticker", "report_date": "iso", "broker": "broker"}.get(name, "value")
        result[name] = evidence.get(value_key) if isinstance(evidence, dict) else evidence
    return result


def filename_fields(name, core):
    parser = load(HERE / "engine" / "VRN_Integrated_ReportDatabase_Engine.py", "_provenance_filename_owner")
    tokens = parser.tokenize_filename(name)
    candidates = parser.extract_filename_ticker_candidates(tokens, {})
    tickers = {c["ticker"] for c in candidates if c.get("ticker")}
    dates = {c["date"] for c in parser.parse_date_candidates_from_number_tokens(tokens["number_tokens"])}
    return {"ticker": next(iter(tickers)) if len(tickers) == 1 else None,
            "report_date": next(iter(dates)) if len(dates) == 1 else None,
            "rating": core.extract_rating([], name).get("value")}


def from_layout(document, numbering, core, catalog, contract):
    """Preserve all repaired text/cells and all four source identities; do not alter the supplied report."""
    before = digest(document)
    docsha, name = document["input_sha256"], document["filename"]
    repair = document["repair"]
    rows = []
    emit = lambda lane, field, value, locator, **kw: rows.append(observation(numbering, catalog, docsha, lane, field, value, locator, **kw))
    emit("filename", "filename", name, {"filename": name}, raw=name)
    # The filename parser is the existing field engine; its evidence is deliberately isolated.
    for field, value in filename_fields(name, core).items():
        emit("filename", field, value, {"filename": name, "field": field}, raw=name)
    lines = repair["text"]["lines"]
    page1 = [x for x in lines if x["page"] == 1]
    info, body = [], []
    for line in page1:
        text = line.get("text", "")
        labeled = core.extract_target_price([text]).get("value") is not None or core.extract_current_price([text]).get("value") is not None
        # Metadata headings and explicit quote labels may occur in ANY corner.
        is_info = labeled or line.get("role") == "REPORT_TITLE" or bool(core.page_dates([text]))
        lane = "first_page_info" if is_info else "first_page_body"
        (info if is_info else body).append(line)
        emit(lane, "text", text or None, {"page": 1, "line": line["id"], "bbox": line.get("bbox")},
             raw=line.get("raw_text", text), glyphs=line.get("source_ids", []),
             context={"role": line.get("role"), "size": line.get("size"), "classification": "LABEL_AND_LAYOUT_CANDIDATE"})
    for lane, group in (("first_page_info", info), ("first_page_body", body)):
        fields = page_fields(core, [x["text"] for x in group])
        for field, value in fields.items():
            emit(lane, field, value, {"page": 1, "field": field},
                 glyphs=[s for x in group for s in x.get("source_ids", [])])
    annual = []
    tables = sorted(repair["tables"], key=lambda t: (t["page"], (t.get("bbox") or [0])[0], (t.get("bbox") or [0, 0])[1], t["id"]))
    for table in tables:
        lane = "first_page_info" if table["page"] == 1 else "annual_financial"
        if lane == "annual_financial":
            annual.append(table)
        for line in table["rows"]:
            for cell in line:
                locator = {"page": table["page"], "table": table["id"], "row": cell["row"], "column": cell["column"], "bbox": cell.get("bbox")}
                # Numeric zero is never treated as null. Blank cells remain explicit observations.
                value = cell.get("number") if cell.get("number") is not None else cell.get("text") or None
                emit(lane, "table_cell", value, locator, raw=cell.get("raw"), glyphs=cell.get("source_ids", []),
                     context={"caption": table.get("caption"), "header_paths": table.get("header_paths", []),
                              "covered_by": cell.get("covered_by"), "unit_period_state": "PRESERVED_UNNORMALIZED"})
    if not annual:
        emit("annual_financial", "table_cell", None, {"page": None, "table": None}, context={"reason": "NO_TABLE_IN_LAYOUT_EVIDENCE"})
    # Coverage uses source word positions against output line/cell positions, not a second expensive OCR.
    scoped_pages = {1} | {t["page"] for t in annual}
    words = [w for w in repair.get("source_words", []) if w["page"] in scoped_pages]
    boxes = defaultdict(list)
    for line in page1:
        boxes[1].append(line.get("bbox"))
    for table in tables:
        for line in table["rows"]:
            for cell in line:
                if cell.get("text"):
                    boxes[table["page"]].append(cell.get("bbox"))
    missing = [w for w in words if not any(inside(w.get("bbox"), box) for box in boxes[w["page"]])]
    failures = {}
    for word in missing:
        failures["page:" + str(word["page"])] = "source words outside restored text/cell regions"
    conflicts = [x for x in reconcile(rows) if x["state"] == "CONFLICT"]
    for clash in conflicts:
        failures["field:" + clash["field"]] = "different source values"
    checks = {"observations_unique": len({r["id"] for r in rows}) == len(rows),
              "all_four_lanes": {r["lane"] for r in rows} == {s["key"] for s in contract["sources"]},
              "source_unchanged": digest(document) == before,
              "cells_preserved": sum(r["field"] == "table_cell" and r["locator"].get("table") is not None for r in rows) == sum(len(row) for t in tables for row in t["rows"])}
    return {"filename": name, "document_sha256": docsha, "observations": rows, "checks": checks,
            "cross_checks": reconcile(rows), "table_order": [t["id"] for t in tables],
            "scope_pages": sorted(scoped_pages), "source_words": len(words), "unmapped_words": len(missing),
            "unmapped_word_ids": [w.get("id") for w in missing],
            "escalation": plan_escalation(failures, {}, contract),
            "state": "RED" if not all(checks.values()) else "YELLOW",
            "completeness": "REVIEW_REQUIRED", "agreement_is_not_completeness": True,
            "note": "Geometry coverage and source agreement are diagnostics; annual-page classification, unit/period normalization and unresolved regions still require validation."}


def run(report_path, source, output):
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    numbering, core = owners()
    catalog = numbering.source_catalog()
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    source = Path(source)
    inputs = [source] if source.is_file() else list(source.rglob("*.pdf"))
    available = {(p.name, hashlib.sha256(p.read_bytes()).hexdigest()): p for p in inputs}
    results = []
    for doc in sorted(report["documents"], key=lambda d: (d["filename"].casefold(), d["filename"])):
        if (doc["filename"], doc["input_sha256"]) not in available:
            raise ValueError("INPUT_EVIDENCE_MISMATCH: " + doc["filename"])
        results.append(from_layout(doc, numbering, core, catalog, contract))
    result = {"schema": "VRN.SourceProvenance.v1", "engine": ENGINE + "_" + VERSION,
              "documents": results, "state": "RED" if any(d["state"] == "RED" for d in results) else "YELLOW" if results else "NODATA",
              "source_report_sha256": hashlib.sha256(Path(report_path).read_bytes()).hexdigest(),
              "database_written": False, "ocr_invoked": False, "reused_extraction": True}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "PROVENANCE.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[來源驗證] " + result["state"] + " · documents=" + str(len(results)) + " · observations=" + str(sum(len(d["observations"]) for d in results)) + " · OCR=0")
    return result


def selftest():
    module = load(HERE / "tests" / "test_SourceProvenance_v0100.py", "_provenance_tests")
    return module.run(sys.modules[__name__])


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] VCGC entry required")
        return 2
    if args == ["--selftest"]:
        return selftest()
    parser = argparse.ArgumentParser(description="四來源獨立編號、交叉對照、還原完整性與升級待辦")
    parser.add_argument("--report", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    options = parser.parse_args(args)
    result = run(options.report, options.source, options.out)
    return 1 if result["state"] == "RED" else 2 if result["state"] in {"YELLOW", "NODATA"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
