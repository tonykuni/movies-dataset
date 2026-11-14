#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent verifier v0106: exact source excerpts; v0105 financial checks intact.

For SOURCE_VERBATIM books, complete PDFium source matches replace the old
synthetic-sentence coverage heuristic. OCR stays pending; mismatches stay FAIL.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import types


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VIA:ACCEL-BRIDGE:v0100] Every verifier shard applies the active locked tool.
BRIDGE = load("independent_v0106_execution", "VIA_ExecutionBridge_v0100.py")
BRIDGE.activate(Path(__file__).resolve().parents[2])
PRIOR = load("independent_v0105_financial_core", "VRN2_IndependentVerifier_v0105.py")
QUOTES = load("independent_v0106_source_reader", "VRN2_VerbatimVerifier_v0100.py")
for _name, _value in list(vars(PRIOR).items()):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value
VERSION = "VRN2_IndependentVerifier_v0106"
QUOTE_RESULT = None
QUOTE_DOCUMENTS = {}


def __getattr__(name):
    return getattr(PRIOR, name)


def rebind(function):
    result = types.FunctionType(function.__code__, globals(), function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def verify_summary(rows, pdfdir, basic=None, fin=None):
    result = PRIOR.verify_summary(rows, pdfdir, basic, fin)
    if QUOTE_RESULT is None:
        return result
    index = {(row.get("file"), row.get("point")): row for row in QUOTE_RESULT["rows"]}
    global_failure = any(row["state"] == "FAIL" and not row.get("point") for row in QUOTE_RESULT["rows"])
    for item in result:
        name = item["FILENAME"]
        if (QUOTE_DOCUMENTS.get(name) or {}).get("mode") != "SOURCE_VERBATIM":
            continue
        for point in range(1, 5):
            proof = index.get((name, point), {})
            state = proof.get("state")
            if global_failure:
                state = "FAIL"
            verdict = {"PASS": "PASS", "OCR_PENDING": "OCR"}.get(state, "FAIL")
            note = "完整原文與來源 PDF 雜湊相符 · p.%s · pypdfium2" % proof.get("page") if state == "PASS" else ("影像頁 · OCR 原文需核對原圖" if state == "OCR_PENDING" else proof.get("reason", "原文來源證據未齊"))
            item["checks"][f"POINT_{point}"] = verdict + " · " + note
    return result


_run_files = rebind(PRIOR.run_files)


def run_files(od, pdfdir, files):
    global QUOTE_RESULT, QUOTE_DOCUMENTS
    source = Path(od) / "VRN2_SummarySource_latest.json"
    QUOTE_RESULT, QUOTE_DOCUMENTS = None, {}
    if source.is_file():
        document = json.loads(source.read_text(encoding="utf-8-sig"))
        QUOTE_DOCUMENTS = {row["file"]: row for row in document["documents"]}
        QUOTE_RESULT = QUOTES.verify(od, pdfdir)
    return _run_files(od, pdfdir, files)


run_parallel = rebind(PRIOR.run_parallel)
write_digest = rebind(PRIOR.write_digest)
ui_payload = rebind(PRIOR.ui_payload)
main = rebind(PRIOR.main)
def selftest():
    global QUOTE_RESULT, QUOTE_DOCUMENTS
    result = PRIOR.selftest()
    original = PRIOR.verify_summary
    saved = QUOTE_RESULT, QUOTE_DOCUMENTS
    try:
        PRIOR.verify_summary = lambda *args: [{"FILENAME": "a.pdf", "checks": {"POINT_1": "PASS"}}]
        QUOTE_DOCUMENTS = {"a.pdf": {"mode": "SOURCE_VERBATIM"}}
        QUOTE_RESULT = {"rows": [{"file": "a.pdf", "point": 1, "state": "FAIL", "reason": "tampered source"}]}
        assert verify_summary([], ".")[0]["checks"]["POINT_1"].startswith("FAIL")
        QUOTE_RESULT["rows"][0]["state"] = "OCR_PENDING"
        assert verify_summary([], ".")[0]["checks"]["POINT_1"].startswith("OCR")
        assert ui_payload([], [], [], "fp", 0, 1, True, "test")["ver"] == VERSION
    finally:
        PRIOR.verify_summary = original
        QUOTE_RESULT, QUOTE_DOCUMENTS = saved
    print("[PASS] v0106: source mismatch remains FAIL; OCR remains pending; payload carries actual verifier version")
    return result


if __name__ == "__main__":
    if sys.argv[1:2] == ["--shard"]:
        od, pdfdir, selection, target = sys.argv[2:6]
        vb, vf, vs = run_files(od, pdfdir, json.loads(Path(selection).read_text(encoding="utf-8")))
        Path(target).write_text(json.dumps({"basic": vb, "fin": vf, "summary": vs}, ensure_ascii=False), encoding="utf-8")
        raise SystemExit(0)
    if sys.argv[1:2] == ["--selftest"]:
        raise SystemExit(selftest())
    arguments = sys.argv[1:]
    ui = arguments[arguments.index("--ui") + 1] if "--ui" in arguments else None
    positional = [item for i, item in enumerate(arguments) if item != "--ui" and not (i > 0 and arguments[i-1] == "--ui")]
    raise SystemExit(main(*positional[:3], ui=ui))
