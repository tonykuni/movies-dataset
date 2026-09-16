#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUP_MDL866_VIAUnifiedNLPOrchestrator v0100

VIA 中央唯一 NLP 控制入口。它把既有的 SUP_MDL744 NLPApplicationHub、
VRN_ENG087 NLP→VRN→VDF 橋與已收容的外部附件放在同一個可驗收契約下。
附件只作受控 adapter/intake 參考，不在本檔直接執行外部資料抓取、排程、
自動修碼或來源覆寫。所有文字處理皆為離線、可回溯、可重跑。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENGINE_ID = "SUP_MDL866_VIAUnifiedNLPOrchestrator"
VERSION = "v0100"
HERE = Path(__file__).resolve()
VIA = HERE.parents[2]
HUB_ROOT = VIA / "supportive modules" / "70_VRN_Rules"
REGISTRY_ROOT = VIA / "supportive modules" / "registry"
MANIFEST_PATH = REGISTRY_ROOT / "VIA_UnifiedNLP_Attachment_Manifest_v0100.json"
REPORT_ROOT = VIA / "VIA_Reports" / "nlp_unified"
LATEST_JSON = REPORT_ROOT / "VIA_UNIFIED_NLP_latest.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module spec: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def latest_hub_path() -> Path | None:
    hits = sorted(HUB_ROOT.glob("SUP_MDL744_NLPApplicationHub_v*.py"))
    return hits[-1] if hits else None


def load_hub() -> tuple[Any | None, dict[str, Any]]:
    path = latest_hub_path()
    if path is None:
        return None, {"state": "ABSENT", "why": "SUP_MDL744 NLP Hub not found"}
    try:
        hub = load_module(path, "via_unified_nlp_sup_mdl744")
        info = hub.status() if hasattr(hub, "status") else {}
        info.update({"state": "VERIFIED", "path": str(path), "sha256": sha256_file(path)})
        return hub, info
    except Exception as exc:  # pragma: no cover - surfaced in status
        return None, {"state": "FAILED", "path": str(path), "why": f"{type(exc).__name__}: {exc}"}


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        return {"state": "ABSENT", "attachments": []}
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    payload.setdefault("attachments", [])
    return payload


def accelerator_status() -> dict[str, Any]:
    return {
        "roster": os.environ.get("VIA_ACCELERATOR_ROSTER", "UNSET"),
        "control": os.environ.get("VIA_ACCELERATOR_CONTROL", "UNSET"),
        "bootstrap": "sitecustomize" in sys.modules,
        "family": os.environ.get("VIA_FAMILY", "UNSET"),
        "network_consent": os.environ.get("VIA_NET_CONSENT", "OFF"),
    }


def adapter_status() -> list[dict[str, Any]]:
    manifest = load_manifest()
    out = []
    for item in manifest.get("attachments", []):
        out.append({
            "id": item.get("id"),
            "kind": item.get("kind"),
            "nlp_role": item.get("nlp_role"),
            "execution_state": item.get("execution_state"),
            "network": item.get("network", False),
            "route": item.get("route"),
        })
    return out


def status() -> dict[str, Any]:
    hub, hub_status = load_hub()
    manifest = load_manifest()
    return {
        "schema": "VIA.UnifiedNLP.Status.v1",
        "engine": ENGINE_ID,
        "version": VERSION,
        "hub": hub_status,
        "manifest": {
            "path": str(MANIFEST_PATH),
            "state": manifest.get("state", "ABSENT"),
            "attachments": len(manifest.get("attachments", [])),
            "sha256": sha256_file(MANIFEST_PATH) if MANIFEST_PATH.is_file() else None,
        },
        "adapters": adapter_status(),
        "accelerator": accelerator_status(),
        "network_mode": "OFFLINE_ONLY",
        "policy": "SUP_MDL744 is the NLP capability provider; attachments are governed adapters and are not implicit execution paths.",
        "hub_loaded": hub is not None,
    }


def run_text(text: str, points: int = 5) -> dict[str, Any]:
    hub, hub_status = load_hub()
    raw = str(text or "")
    if hub is None:
        return {"state": "BLOCKED", "why": hub_status.get("why", "NLP Hub unavailable"), "text_sha256": sha256_text(raw)}
    normalized = hub.nfkc(raw)
    segments = hub.segments(normalized)
    tables = hub.tables(normalized)
    layout = hub.layout(normalized)
    roles = hub.roles(normalized)
    summary = hub.summarize(normalized, max(1, int(points)))
    return {
        "state": "PASS",
        "engine": ENGINE_ID,
        "hub": hub_status,
        "raw_char_count": len(raw),
        "normalized_char_count": len(normalized),
        "raw_sha256": sha256_text(raw),
        "normalized_sha256": sha256_text(normalized),
        "normalized_text": normalized,
        "segment_count": len(segments),
        "table_count": len(tables),
        "layout_block_count": len(layout.get("blocks", [])) if isinstance(layout, dict) else 0,
        "role_count": len(roles.get("records", [])) if isinstance(roles, dict) else 0,
        "roles_why": hub.roles_why() if hasattr(hub, "roles_why") else "",
        "summary": summary,
        "adapter_policy": adapter_status(),
        "accelerator": accelerator_status(),
        "network_mode": "OFFLINE_ONLY",
    }


def run_pipeline(inputs: list[str], db: str = "", out: str = "", points: int = 5, force: bool = False) -> dict[str, Any]:
    """檔案級唯一入口：把 PDF/DOCX/Image 交給既有 VRN_ENG087，不複製第二套解析器。"""
    bridge_hits = sorted((VIA / "functional modules" / "VRN").glob("VRN_ENG087_NLPTextSummaryBridge_v*.py"))
    if not bridge_hits:
        return {"state": "BLOCKED", "why": "VRN_ENG087 NLP→VRN→VDF bridge absent", "inputs": inputs}
    bridge = bridge_hits[-1]
    out_dir = Path(out) if out else (VIA / "VIA_Reports" / "vrn" / "nlp_pipeline")
    db_path = Path(db) if db else (VIA / "functional modules" / "VRN" / "db" / "vrn_reports.duckdb")
    argv = [sys.executable, str(bridge), "run"]
    for item in inputs:
        argv.extend(["--in", item])
    argv.extend(["--db", str(db_path), "--out", str(out_dir), "--points", str(max(1, int(points)))])
    if force:
        argv.append("--force")
    env = dict(os.environ)
    env.setdefault("VIA_FAMILY", "vrn")
    env.setdefault("VIA_NET_CONSENT", "OFF")
    proc = subprocess.run(argv, cwd=str(VIA), env=env, text=True, capture_output=True, check=False)
    result = {
        "state": "PASS" if proc.returncode == 0 else "YELLOW",
        "engine": ENGINE_ID,
        "dispatch": "VRN_ENG087_NLPTextSummaryBridge",
        "bridge": str(bridge),
        "argv": argv,
        "returncode": proc.returncode,
        "inputs": inputs,
        "db": str(db_path),
        "out": str(out_dir),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "network_mode": "OFFLINE_ONLY",
        "accelerator": accelerator_status(),
        "note": "YELLOW is retained when VDF coverage blocks the downstream bridge; no false GREEN.",
    }
    write_evidence({"schema": "VIA.UnifiedNLP.Pipeline.v1", "pipeline": result})
    return result


def write_evidence(payload: dict[str, Any]) -> Path:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    sealed = dict(payload)
    sealed["generated_at"] = now_iso()
    sealed["manifest_sha256"] = sha256_file(MANIFEST_PATH) if MANIFEST_PATH.is_file() else None
    LATEST_JSON.write_text(json.dumps(sealed, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return LATEST_JSON


def selftest() -> int:
    checks: list[tuple[str, bool, str]] = []
    manifest = load_manifest()
    hub, hs = load_hub()
    checks.append(("attachment manifest exists", MANIFEST_PATH.is_file(), str(MANIFEST_PATH)))
    checks.append(("seven attachment records", len(manifest.get("attachments", [])) == 7, str(len(manifest.get("attachments", [])))))
    checks.append(("NLP Hub VERIFIED", hub is not None and hs.get("state") == "VERIFIED", hs.get("state", "ABSENT")))
    services = set(hs.get("report_services", []))
    checks.append(("six report NLP services", {"table_ops", "layout_analysis", "content_roles", "context_reconstruction", "summarization", "function_classifier"}.issubset(services), f"{len(services)}/6"))
    sample = "台積電 (2330 TT) 買進，目標價 1250 元\n| 項目 | 2025F | 2026F |\n| --- | --- | --- |\n| 稀釋EPS | 58.7 | 66.1 |\n風險為匯率波動。"
    result = run_text(sample, 3)
    checks.append(("TextProcessor normalization", result.get("state") == "PASS" and result.get("normalized_text", "") != sample, result.get("normalized_text", "")[:40]))
    checks.append(("table/layout services", result.get("table_count", 0) >= 1 and result.get("layout_block_count", 0) >= 1, f"tables={result.get('table_count')};blocks={result.get('layout_block_count')}"))
    sm = result.get("summary", {})
    checks.append(("evidence summary", sm.get("state") in ("OK", "EMPTY") and all(isinstance(p.get("source_span"), dict) for p in sm.get("points", [])), f"{sm.get('state')};points={len(sm.get('points', []))}"))
    adapters = adapter_status()
    checks.append(("adapter execution is fail-closed", bool(adapters) and all(x.get("execution_state") != "ACTIVE_NETWORK" for x in adapters), str([(x.get("id"), x.get("execution_state")) for x in adapters])))
    checks.append(("network mode offline", result.get("network_mode") == "OFFLINE_ONLY", result.get("network_mode", "")))
    checks.append(("VRN file bridge present", bool(list((VIA / "functional modules" / "VRN").glob("VRN_ENG087_NLPTextSummaryBridge_v*.py"))), "VRN_ENG087"))
    evidence = {
        "schema": "VIA.UnifiedNLP.Selftest.v1",
        "engine": ENGINE_ID,
        "version": VERSION,
        "verdict": "GREEN" if all(x[1] for x in checks) else "YELLOW",
        "checks": [{"name": n, "state": "PASS" if ok else "FAIL", "actual": note} for n, ok, note in checks],
        "status": status(),
        "probe": {k: v for k, v in result.items() if k != "normalized_text"},
    }
    report = write_evidence(evidence)
    failures = 0
    for name, ok, note in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name} {note}")
        failures += int(not ok)
    print(f"  [計] Unified NLP 十檢 OK {len(checks) - failures} · FAIL {failures}")
    print(f"  evidence={report}")
    return 0 if failures == 0 else 1



# ===== 批534:VIA 全樹以 `--selftest` 呼叫自測(格子站/匯流排/Deck/總控頁);本引擎原只認位置動詞(L39 等價轉換,只增不減)。=====
_FLAG_VERBS_B534 = {"--selftest": "selftest", "--status": "status", "--manifest": "manifest", "--routes": "routes"}


def _normalise_argv_b534(argv):
    out, verb = [], None
    for a in argv:
        if a in _FLAG_VERBS_B534 and verb is None:
            verb = _FLAG_VERBS_B534[a]
        else:
            out.append(a)
    return ([verb] + out) if verb else out

def main() -> int:
    parser = argparse.ArgumentParser(description="VIA central Unified NLP orchestrator")
    sub = parser.add_subparsers(dest="verb")
    sub.add_parser("status")
    sub.add_parser("selftest")
    text_cmd = sub.add_parser("text")
    text_cmd.add_argument("--text", default="")
    text_cmd.add_argument("--file", default="")
    text_cmd.add_argument("--points", type=int, default=5)
    pipe_cmd = sub.add_parser("pipeline")
    pipe_cmd.add_argument("--in", dest="inputs", action="append", required=True)
    pipe_cmd.add_argument("--db", default="")
    pipe_cmd.add_argument("--out", default="")
    pipe_cmd.add_argument("--points", type=int, default=5)
    pipe_cmd.add_argument("--force", action="store_true")
    args = parser.parse_args(_normalise_argv_b534(sys.argv[1:]))   # 批534:旗標=位置動詞(L39)
    if args.verb in (None, "status"):
        print(json.dumps(status(), ensure_ascii=False, indent=2, default=str))
        return 0
    if args.verb == "selftest":
        return selftest()
    if args.verb == "text":
        text = Path(args.file).read_text(encoding="utf-8", errors="replace") if args.file else args.text
        result = run_text(text, args.points)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0 if result.get("state") == "PASS" else 2
    if args.verb == "pipeline":
        result = run_pipeline(args.inputs, args.db, args.out, args.points, args.force)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0 if result.get("state") == "PASS" else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
