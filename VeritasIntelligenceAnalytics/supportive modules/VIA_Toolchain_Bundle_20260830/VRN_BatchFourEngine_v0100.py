# ---------------------------------------------------------------------
# VRN_BatchFourEngine_v0100
#
# Closes the gap between VRNFourEngineSuite (one file per run, no .docx)
# and a real broker-attachment folder (64 mixed pdf/docx documents).
#
#   1. discovery      pdf/image go straight in; docx/pptx/xlsx/msg/html are
#                     bridged to .md by markitdown, which the suite accepts
#                     as a prefetched-text input
#   2. per-file run   four_engine_orchestrator.run_all_engines
#   3. aggregation    one batch manifest + audit csv over every stage
#   4. reconciliation new PDF-derived financial_data vs the baseline
#                     text-corpus extraction, matched on filename/metric/period
#
# Governance: append-only. Every invocation writes a fresh timestamped run
# directory; nothing existing is touched.
# ---------------------------------------------------------------------

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

DRIVER_NAME = "VRN_BatchFourEngine"
DRIVER_VERSION = "v0100"

# accepted natively by four_engine_orchestrator
NATIVE_DOCUMENT = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
NATIVE_TEXT = {".txt", ".md"}
# rejected by the suite, recoverable through markitdown
BRIDGE_SOURCE = {".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".msg", ".html", ".htm", ".epub", ".csv"}

STAGE_ORDER = ["repair", "layout", "text", "table"]


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chars: int = 16) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 256), b""):
            h.update(chunk)
    return h.hexdigest()[:chars]


def norm_period(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def norm_metric(value) -> str:
    return str(value or "").strip().upper()


# ---------------------------------------------------------------------
# markitdown bridge
# ---------------------------------------------------------------------

class Bridge:
    """Converts formats the four-engine suite rejects into .md it accepts."""

    def __init__(self, bridge_dir: Path):
        self.bridge_dir = bridge_dir
        self.bridge_dir.mkdir(parents=True, exist_ok=True)
        self.available = False
        self.error = ""
        self.md = None
        try:
            from markitdown import MarkItDown
            self.md = MarkItDown(enable_plugins=False)
            self.available = True
        except Exception as exc:
            self.error = "{0}: {1}".format(type(exc).__name__, exc)

    # VRNTextRepairEngine only parses a corpus whose records carry the marker
    #   <filename>.(pdf|docx)(DUAL_ZONES|DOCX_HEAD|NEEDS_OCR) · <detail>
    # followed by the 本文區(修復) zone. Raw markdown is rejected outright, so
    # the bridge has to emit a single well-formed one-record corpus.
    @staticmethod
    def wrap_as_corpus(src: Path, body: str) -> str:
        ext = src.suffix.lower()
        record_name = src.name if ext == ".docx" else src.name + ".docx"
        head = "{0}DOCX_HEAD · markitdown bridge from {1}".format(record_name, ext or "unknown")
        return "\n".join([head, "本文區(修復)", body.strip(), ""])

    def convert(self, src: Path) -> dict:
        rec = {"source": str(src), "bridged": "", "status": "FAIL", "error": "", "chars": 0,
               "record_name": ""}
        if not self.available:
            rec["error"] = "markitdown unavailable: " + self.error
            return rec
        try:
            if hasattr(self.md, "convert_local"):
                result = self.md.convert_local(str(src))
            else:
                result = self.md.convert(str(src))
            body = getattr(result, "markdown", None) or getattr(result, "text_content", "") or ""
            if not body.strip():
                rec["error"] = "empty conversion"
                return rec
            corpus = self.wrap_as_corpus(src, body)
            rec["record_name"] = corpus.split("\n", 1)[0]
            body = corpus
            target = self.bridge_dir / (src.stem + ".md")
            n = 2
            while target.exists():
                target = self.bridge_dir / "{0}__b{1}.md".format(src.stem, n)
                n += 1
            target.write_text(body, encoding="utf-8", newline="\n")
            rec.update({"bridged": str(target), "status": "OK", "chars": len(body)})
        except Exception as exc:
            rec["error"] = "{0}: {1}".format(type(exc).__name__, exc)
        return rec


# ---------------------------------------------------------------------
# suite loading
# ---------------------------------------------------------------------

def load_suite(suite_dir: Path):
    suite_dir = suite_dir.resolve()
    if str(suite_dir) not in sys.path:
        sys.path.insert(0, str(suite_dir))
    import four_engine_orchestrator as feo
    return feo


# ---------------------------------------------------------------------
# per-document execution
# ---------------------------------------------------------------------

def run_document(feo, config, item: dict, runs_root: Path, index: int) -> dict:
    started = time.perf_counter()
    src = Path(item["fed_path"])
    out_dir = runs_root / "{0:04d}_{1}".format(index, src.stem[:60])
    rec = {
        "index": index,
        "original": item["original"],
        "fed_path": item["fed_path"],
        "route": item["route"],
        "output_dir": str(out_dir),
        "status": "FAIL",
        "run_id": "",
        "stages": {},
        "warnings": [],
        "error": "",
        "ms": 0,
    }
    try:
        manifest = feo.run_all_engines(src, out_dir, config)
        rec["run_id"] = manifest.run_id
        rec["status"] = manifest.status
        for stage in manifest.stages:
            rec["stages"][stage.name] = {
                "status": stage.status,
                "counts": dict(stage.counts or {}),
                "duration_ms": stage.duration_ms,
                "warnings": list(stage.warnings or []),
            }
            for w in (stage.warnings or []):
                rec["warnings"].append("{0}: {1}".format(stage.name, w))
    except Exception as exc:
        rec["error"] = "{0}: {1}".format(type(exc).__name__, exc)
    rec["ms"] = int((time.perf_counter() - started) * 1000)
    return rec


# ---------------------------------------------------------------------
# reconciliation against the baseline text-corpus extraction
# ---------------------------------------------------------------------

def load_financial(path: Path) -> list:
    out = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def collect_new_financial(runs_root: Path) -> list:
    out = []
    for fin in runs_root.rglob("01_repair/financial_data.jsonl"):
        out.extend(load_financial(fin))
    return out


def reconcile(baseline: list, fresh: list) -> dict:
    def key(rec):
        return (
            str(rec.get("filename") or "").strip(),
            norm_metric(rec.get("metric")),
            norm_period(rec.get("period")),
        )

    b_map = {}
    for r in baseline:
        b_map.setdefault(key(r), []).append(r)
    f_map = {}
    for r in fresh:
        f_map.setdefault(key(r), []).append(r)

    rows = []
    for k in sorted(set(b_map) | set(f_map)):
        b_vals = sorted({round(float(r["value"]), 6) for r in b_map.get(k, []) if r.get("value") is not None})
        f_vals = sorted({round(float(r["value"]), 6) for r in f_map.get(k, []) if r.get("value") is not None})
        if b_vals and f_vals:
            verdict = "MATCH" if b_vals == f_vals else "MISMATCH"
        elif b_vals:
            verdict = "BASELINE_ONLY"
        else:
            verdict = "NEW_ONLY"
        rows.append({
            "filename": k[0],
            "metric": k[1],
            "period": k[2],
            "baseline_values": ";".join(str(v) for v in b_vals),
            "new_values": ";".join(str(v) for v in f_vals),
            "verdict": verdict,
        })

    tally = {"MATCH": 0, "MISMATCH": 0, "BASELINE_ONLY": 0, "NEW_ONLY": 0}
    for r in rows:
        tally[r["verdict"]] += 1
    return {"rows": rows, "tally": tally}


# ---------------------------------------------------------------------
# discovery
# ---------------------------------------------------------------------

def discover(input_dir: Path, bridge: Bridge) -> tuple:
    items = []
    skipped = []
    bridge_log = []
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        ext = path.suffix.lower()
        if ext in NATIVE_DOCUMENT:
            items.append({"original": str(path), "fed_path": str(path), "route": "NATIVE_DOC"})
        elif ext in NATIVE_TEXT:
            items.append({"original": str(path), "fed_path": str(path), "route": "NATIVE_TEXT"})
        elif ext in BRIDGE_SOURCE:
            res = bridge.convert(path)
            bridge_log.append(res)
            if res["status"] == "OK":
                items.append({"original": str(path), "fed_path": res["bridged"], "route": "MARKITDOWN_BRIDGE"})
            else:
                skipped.append({"path": str(path), "reason": "bridge failed: " + res["error"]})
        else:
            skipped.append({"path": str(path), "reason": "unsupported extension " + ext})
    return items, skipped, bridge_log


# ---------------------------------------------------------------------
# main
# ---------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Batch driver for VRNFourEngineSuite")
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output-root", required=True)
    ap.add_argument("--suite-dir", required=True)
    ap.add_argument("--baseline", default="", help="AttachmentFixedOutput root for reconciliation")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--config", default="")
    ap.add_argument("--emit", default="")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    started = time.perf_counter()
    input_dir = Path(args.input_dir).resolve()
    suite_dir = Path(args.suite_dir).resolve()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_root = Path(args.output_root).resolve() / ("BATCH_" + stamp)
    runs_root = run_root / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    payload = {
        "driver": {"name": DRIVER_NAME, "version": DRIVER_VERSION},
        "at": utcnow(),
        "input_dir": str(input_dir),
        "run_root": str(run_root),
        "suite_dir": str(suite_dir),
        "bridge": {"available": False, "error": "", "converted": 0, "failed": 0},
        "discovery": {"total": 0, "native_doc": 0, "native_text": 0, "bridged": 0, "skipped": 0},
        "documents": [],
        "skipped": [],
        "stage_tally": {},
        "reconciliation": {"enabled": False, "tally": {}, "sample": []},
        "fatal": "",
        "elapsed_s": 0,
    }

    if not input_dir.is_dir():
        payload["fatal"] = "input dir not found: " + str(input_dir)
        emit(payload, args.emit)
        return 2

    try:
        feo = load_suite(suite_dir)
    except Exception as exc:
        payload["fatal"] = "cannot load suite from {0}: {1}".format(suite_dir, exc)
        emit(payload, args.emit)
        return 2

    bridge = Bridge(run_root / "_bridge")
    payload["bridge"]["available"] = bridge.available
    payload["bridge"]["error"] = bridge.error

    items, skipped, bridge_log = discover(input_dir, bridge)
    if args.limit:
        items = items[: args.limit]
    payload["skipped"] = skipped
    payload["bridge"]["converted"] = sum(1 for b in bridge_log if b["status"] == "OK")
    payload["bridge"]["failed"] = sum(1 for b in bridge_log if b["status"] != "OK")
    payload["discovery"] = {
        "total": len(items),
        "native_doc": sum(1 for i in items if i["route"] == "NATIVE_DOC"),
        "native_text": sum(1 for i in items if i["route"] == "NATIVE_TEXT"),
        "bridged": sum(1 for i in items if i["route"] == "MARKITDOWN_BRIDGE"),
        "skipped": len(skipped),
    }

    if args.config:
        config = feo.load_four_engine_config(Path(args.config))
    else:
        config = feo.FourEngineConfig()
    if args.dpi:
        config.dpi = args.dpi

    results = []
    if items:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = {
                pool.submit(run_document, feo, config, item, runs_root, idx): idx
                for idx, item in enumerate(items, start=1)
            }
            done = 0
            for fut in as_completed(futures):
                done += 1
                try:
                    results.append(fut.result())
                except Exception as exc:
                    results.append({
                        "index": futures[fut], "original": "", "fed_path": "", "route": "",
                        "output_dir": "", "status": "FAIL", "run_id": "", "stages": {},
                        "warnings": [], "error": str(exc), "ms": 0,
                    })
                sys.stderr.write("\rprocessed {0}/{1}".format(done, len(items)))
                sys.stderr.flush()
        sys.stderr.write("\n")
    results.sort(key=lambda r: r["index"])
    payload["documents"] = results

    tally = {}
    for stage in STAGE_ORDER:
        counts = {}
        for r in results:
            st = (r["stages"].get(stage) or {}).get("status", "MISSING")
            counts[st] = counts.get(st, 0) + 1
        tally[stage] = counts
    tally["overall"] = {}
    for r in results:
        tally["overall"][r["status"]] = tally["overall"].get(r["status"], 0) + 1
    payload["stage_tally"] = tally

    # audit csv
    audit_path = run_root / "batch_audit.csv"
    with audit_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["index", "original", "route", "overall", "repair", "layout", "text", "table",
                    "financial_data", "tables", "cells", "ms", "warnings", "error"])
        for r in results:
            rep = r["stages"].get("repair", {})
            tab = r["stages"].get("table", {})
            w.writerow([
                r["index"], Path(r["original"]).name if r["original"] else "", r["route"], r["status"],
                rep.get("status", ""),
                (r["stages"].get("layout") or {}).get("status", ""),
                (r["stages"].get("text") or {}).get("status", ""),
                tab.get("status", ""),
                (rep.get("counts") or {}).get("financial_data", ""),
                (tab.get("counts") or {}).get("tables", ""),
                (tab.get("counts") or {}).get("cells", ""),
                r["ms"], " | ".join(r["warnings"]), r["error"],
            ])

    # reconciliation
    if args.baseline:
        base_fin = Path(args.baseline) / "01_repair" / "financial_data.jsonl"
        baseline = load_financial(base_fin)
        fresh = collect_new_financial(runs_root)
        if baseline:
            rec = reconcile(baseline, fresh)
            payload["reconciliation"] = {
                "enabled": True,
                "baseline_records": len(baseline),
                "new_records": len(fresh),
                "tally": rec["tally"],
                "sample": [r for r in rec["rows"] if r["verdict"] == "MISMATCH"][:40],
            }
            recon_path = run_root / "reconciliation.csv"
            with recon_path.open("w", encoding="utf-8-sig", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=["filename", "metric", "period",
                                                   "baseline_values", "new_values", "verdict"])
                w.writeheader()
                w.writerows(rec["rows"])

    payload["elapsed_s"] = round(time.perf_counter() - started, 2)
    (run_root / "batch_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    emit(payload, args.emit)
    return 0


def emit(payload: dict, target: str):
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if target:
        p = Path(target)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
