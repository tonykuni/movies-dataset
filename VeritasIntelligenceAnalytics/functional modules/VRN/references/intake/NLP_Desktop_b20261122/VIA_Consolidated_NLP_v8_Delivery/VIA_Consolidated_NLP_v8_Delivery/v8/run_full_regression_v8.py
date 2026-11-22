from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "v8" / "v8_full_regression.json"
LOG = ROOT / "v8" / "v8_full_regression.log"


def run(name: str, command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> dict[str, object]:
    started = time.time()
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(command, cwd=str(cwd or ROOT), env=merged, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"\n===== {name} =====\n$ {' '.join(command)}\n{proc.stdout}\n")
    return {"name": name, "status": "PASS" if proc.returncode == 0 else "FAIL", "returncode": proc.returncode, "elapsed_seconds": round(time.time() - started, 3), "tail": proc.stdout[-1200:]}


def main() -> int:
    LOG.write_text("VIA v8 full regression\n", encoding="utf-8")
    v18 = ROOT / "nlp_v7_upgrade" / "vendor" / "VIA_NLP_Application_System_v1.8.0"
    results = [
        run("registry", [sys.executable, str(ROOT / "v8" / "validate_consolidation_v8.py")]),
        run("v8_core", [sys.executable, str(ROOT / "v8" / "test_consolidated_nlp_v8.py")], env={"PYTHONPATH": str(ROOT / "v8")}),
        run("v8_cli", [sys.executable, str(ROOT / "v8" / "via_consolidated_nlp_v8_cli.py"), str(ROOT / "testmessage.txt"), "/home/ubuntu/upload/pasted_content.txt", "--out", str(ROOT / "v8" / "regression_cli_output")], env={"PYTHONPATH": str(ROOT / "v8")}),
        run("native_v18", [sys.executable, str(v18 / "scripts" / "run_tests.py")], cwd=v18),
        run("v7_adapter", [sys.executable, str(ROOT / "nlp_v7_upgrade" / "tests" / "test_unified_v7.py")]),
        run("v5_core", [sys.executable, str(ROOT / "v5" / "test_via_nlp_reconstruction_v5.py")]),
        run("folder_scanner", [sys.executable, str(ROOT / "test_via_folder_context_scanner.py")], env={"PYTHONPATH": str(ROOT)}),
        run("pdf_docx", [sys.executable, str(ROOT / "test_pdf_docx_ingest.py")], env={"PYTHONPATH": str(ROOT)}),
        run("api_e2e", [sys.executable, str(ROOT / "v8" / "test_control_center_v8_e2e.py")], env={"PYTHONPATH": str(ROOT / "v8")}),
    ]
    overall = "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL"
    payload = {"schema": "VIA_CONSOLIDATED_NLP_FULL_REGRESSION/8.0", "status": overall, "tests": results, "log": str(LOG)}
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
