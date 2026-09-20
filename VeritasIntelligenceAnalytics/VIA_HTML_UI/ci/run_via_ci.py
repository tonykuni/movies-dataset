#!/usr/bin/env python3
"""Run the VSX → module validation → TriEngine Hub quality gate."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path


def run_step(name: str, command: list[str], cwd: Path, log_dir: Path) -> dict:
    started = time.time()
    proc = subprocess.run(command, cwd=str(cwd), text=True, capture_output=True, encoding="utf-8", errors="replace")
    (log_dir / f"{name}.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (log_dir / f"{name}.stderr.log").write_text(proc.stderr, encoding="utf-8")
    return {
        "name": name,
        "command": shlex.join(command),
        "returncode": proc.returncode,
        "duration_s": round(time.time() - started, 3),
        "stdout_log": str(log_dir / f"{name}.stdout.log"),
        "stderr_log": str(log_dir / f"{name}.stderr.log"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="VIA CI/CD quality gate")
    ap.add_argument("--extractor", required=True, help="via_spec_extractor.py")
    ap.add_argument("--hub", required=True, help="via_triengine_hub.py")
    ap.add_argument("--html", required=True, help="standalone UI or SYNCHRONIZER HTML")
    ap.add_argument("--profile", required=True, help="industry-profile.json")
    ap.add_argument("--industry", required=True, help="profile key")
    ap.add_argument("--source", nargs="+", required=True, help="VSX input files/directories")
    ap.add_argument("--out", required=True, help="CI artifact directory")
    ap.add_argument("--root", default=".", help="TriEngine project root")
    ap.add_argument("--python-exe", default=sys.executable)
    args = ap.parse_args()

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    logs = out / "logs"
    logs.mkdir(exist_ok=True)
    root = Path(args.root).resolve()
    sources = [str(Path(x).resolve()) for x in args.source]
    py = args.python_exe
    steps = []

    vsx = out / "vsx"
    steps.append(run_step("01_vsx_extract", [py, args.extractor, "--in", *sources, "--out", str(vsx), "--title", args.industry], root, logs))
    ir = vsx / "via_spec_ir.json"
    validation = out / "validation"
    steps.append(run_step("02_generate_validators", [py, str(Path(__file__).with_name("generate_module_validation.py")), "--ir", str(ir), "--html", str(Path(args.html).resolve()), "--profile", str(Path(args.profile).resolve()), "--industry", args.industry, "--out", str(validation)], root, logs))
    validator = validation / f"validate_{args.industry}.py"
    report = validation / "module-validation-report.json"
    steps.append(run_step("03_module_validation", [py, str(validator), "--html", str(Path(args.html).resolve()), "--ir", str(ir), "--report", str(report)], root, logs))
    steps.append(run_step("04_hub_selftest", [py, args.hub, "selftest"], root, logs))
    steps.append(run_step("05_hub_route", [py, args.hub, "route", "--root", str(root), "--in", *sources], root, logs))
    steps.append(run_step("06_hub_pipeline", [py, args.hub, "pipeline", "--root", str(root), "--in", *sources, "--out", str(out / "hub-pipeline")], root, logs))

    failed = [step for step in steps if step["returncode"] != 0]
    result = {"ok": not failed, "industry": args.industry, "artifacts": str(out), "steps": steps, "failed_steps": [s["name"] for s in failed]}
    (out / "ci_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
