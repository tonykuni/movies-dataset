"""Eight local conflict checks and a guarded uv install lane for MDL135.

This module is loaded by the existing via-envgov command. It never changes an
active environment name, deletes packages, or promotes a central registry.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

HUB_NAMES = (
    "interpreter_identity", "native_abi", "installed_requirements",
    "distribution_shadow", "pip_check", "tool_roster",
    "family_isolation", "runtime_tools",
)
RUNTIME_COMMANDS = ("uv", "pwsh", "node", "npm", "pandoc", "tesseract", "java", "rustc", "go")
RUN_TIMEOUT = 180
UV_TIMEOUT = 300
MAX_WORKERS = 8
REPORT_SCHEMA = "VIA.EnvGovernance.EightHub.v1"
DIAGNOSTIC_TOOLS = ("pip", "pipdeptree", "deptry", "pipgrip", "johnnydep",
                    "pip-tools", "pip-check-reqs", "packaging")


def _result(state: str, detail: str = "") -> dict:
    return {"state": state, "detail": detail[:400]}


def _installed(scans: list[dict]) -> dict:
    return {s["env"]["name"]: s for s in scans}


def _risk_row(core, scan: dict, identity: dict, tools: dict, baseline: dict) -> dict:
    name = scan["env"]["name"]
    dists = scan.get("dists") or {}
    problems = scan.get("conflicts") or []
    status = identity.get("status", identity.get("state", "NODATA"))
    checks = {}
    checks[HUB_NAMES[0]] = _result("PASS" if scan.get("ok") and status == "OK" else "BLOCK",
                                  f"python={scan.get('python')} identity={status} {scan.get('err', '')}")
    checks[HUB_NAMES[1]] = _result("PASS" if status == "OK" or (name == "BASE" and scan.get("ok")) else "BLOCK",
                                  f"identity={status}; native tags and pyvenv.cfg must agree")
    checks[HUB_NAMES[2]] = _result("PASS" if scan.get("ok") and not problems else "BLOCK",
                                  f"missing/mismatched={len(problems)}")
    checks[HUB_NAMES[3]] = _result("PASS" if scan.get("ok") and not scan.get("dup") else "BLOCK",
                                  f"duplicate distributions={len(scan.get('dup') or {})}")
    py = scan["env"].get("py")
    pip = core.run_cmd([py, "-m", "pip", "check"], timeout=RUN_TIMEOUT) if py and scan.get("ok") else {"rc": -1, "err": "interpreter unavailable"}
    checks[HUB_NAMES[4]] = _result("PASS" if pip["rc"] == 0 else "BLOCK",
                                  (pip.get("out") or pip.get("err") or "")[-220:])
    stage_rows = [s for s in tools.get("stages", []) if s["env"] == name]
    broken = [s for s in stage_rows if s["kind"] in ("REPAIR_TOOLS", "REBUILD_ENV")]
    checks[HUB_NAMES[5]] = _result("PASS" if not broken else "BLOCK", f"repair/rebuild stages={len(broken)}")
    blocked = set()
    if name == "BASE":
        forbidden = set(baseline.get("base", {}).get("never_in_base_families") or [])
        for family, data in (baseline.get("families") or {}).items():
            if family in forbidden:
                blocked.update(core.canon(v) for v in (data.get("members") or []))
        present = blocked.intersection(dists)
    else:
        # The canonical roster enforces exclusive _M/_H environments; a shared
        # alias for an exclusive environment is never accepted.
        present = set()
        row = next((e for e in tools.get("envs", []) if e["name"] == name), {})
        if row.get("isolation") == "EXCLUSIVE" and row.get("found") not in (name, None):
            present.add("exclusive_alias")
    checks[HUB_NAMES[6]] = _result("PASS" if not present else "BLOCK", f"forbidden={','.join(sorted(present)[:8])}")
    external = [x for x in tools.get("external", []) if x.get("env") == name]
    checks[HUB_NAMES[7]] = _result("PASS" if not external else "REVIEW",
                                  f"external runtime/model needs manual verification={len(external)}")
    state = "BLOCK" if any(x["state"] == "BLOCK" for x in checks.values()) else (
        "REVIEW" if any(x["state"] == "REVIEW" for x in checks.values()) else "PASS")
    return {"env": name, "python": scan.get("python"), "interpreter": py,
            "installed": {n: v.get("ver") for n, v in sorted(dists.items())},
            "conflicts": problems, "checks": checks, "state": state}


def _pending(tools: dict) -> list[dict]:
    return [{"env": s["env"], "kind": s["kind"], "packages": s.get("pkgs") or [], "id": s["id"]}
            for s in tools.get("stages", []) if s["kind"] in ("INSTALL_TOOLS", "REPAIR_TOOLS", "REBUILD_ENV", "ENSURE_ENV")]


def _uv_preflight(core, rows: list[dict], tools: dict) -> list[dict]:
    """Resolve the full per-environment install set without changing the environment."""
    uv = shutil.which("uv")
    dry = []
    for row in rows:
        env = row["env"]
        packages = sorted(set(p for st in tools.get("stages", []) if st["env"] == env
                              and st["kind"] == "INSTALL_TOOLS" for p in st.get("pkgs", [])))
        if not packages:
            continue
        if row["state"] != "PASS":
            dry.append({"env": env, "state": "BLOCK", "packages": packages, "reason": "eight-hub checks incomplete"})
            continue
        if not uv or not row.get("interpreter"):
            dry.append({"env": env, "state": "NOT_RUN", "packages": packages, "reason": "uv or interpreter missing"})
            continue
        args = [uv, "pip", "install", "--dry-run", "--python", row["interpreter"], *packages]
        r = core.run_cmd(args, timeout=UV_TIMEOUT)
        dry.append({"env": env, "state": "PASS" if r["rc"] == 0 else "BLOCK",
                    "packages": packages, "reason": (r.get("out", "") + r.get("err", ""))[-400:]})
    return dry


def _save(core, report: dict, lesson: bool = False) -> Path:
    folder = core.OUT / "eight_hub"
    folder.mkdir(parents=True, exist_ok=True)
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + str(os.getpid())
    path = folder / (name + ".json")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    event = {"at": report["at"], "run": str(path), "state": report["state"],
             "affected": [r["env"] for r in report["envs"] if r["state"] != "PASS"]}
    with (folder / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    if lesson and report["state"] not in ("PASS", "PASS_NO_CHANGES", "READY"):
        issues = []
        for row in report["envs"]:
            for hub, info in row["checks"].items():
                if info["state"] == "PASS":
                    continue
                issues.append((row["env"], hub, info["state"]))
        for item in report.get("uv_dry_run") or []:
            if item["state"] != "PASS":
                issues.append((item["env"], "uv_resolver", item["state"]))
        if report.get("execution") and report["execution"]["summary"].get("fails"):
            issues.append(("*", "install", "FAIL"))
        for env, hub, state in sorted(set(issues)):
                signature = f"{env}|{hub}|{state}"
                entry = {"at": report["at"], "fingerprint": hashlib.sha256(signature.encode()).hexdigest(),
                         "env": env, "hub": hub, "state": state,
                         "evidence": str(path), "status": "OBSERVED_ONLY"}
                with (folder / "lesson_candidates.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def _snapshot(core, base_python: str | None, env_root: str) -> dict:
    baseline = core.load_baseline()
    envs = core.discover_envs(baseline, [], env_root, base_python)
    scans = core.panorama(envs, workers=MAX_WORKERS, task_timeout=RUN_TIMEOUT, quiet=True)
    roster = core.union_roster(baseline, core.load_roster())
    toolplan = core.tools_plan(roster, envs, env_root, timeout=RUN_TIMEOUT)
    ident = {x["env"]: x for x in core.identity_scan(scans)}
    rows = [_risk_row(core, s, ident.get(s["env"]["name"], {}), toolplan, baseline) for s in scans]
    base = next(s for s in scans if s["env"]["name"] == "BASE")
    drift = core.base_identity_drift(core.base_identity(base))
    base_analysis = core.analyze_base(base, baseline,
                                      {s["env"]["name"] for s in scans}, core.lessons_skip())
    if drift["state"] == "CHANGED":
        rows[0]["checks"][HUB_NAMES[0]] = _result("BLOCK", drift["why"])
        rows[0]["state"] = "BLOCK"
    return {"rows": rows, "toolplan": toolplan, "drift": drift,
            "base_analysis": {k: base_analysis.get(k) for k in
                              ("manifest_missing", "blocked_present", "extras", "os_managed")},
            "baseline": baseline.get("_src"), "roster": roster.get("_src"),
            "diagnostics": {n: (base.get("dists") or {}).get(n, {}).get("ver") for n in DIAGNOSTIC_TOOLS},
            "runtime_commands": {name: shutil.which(name) for name in RUNTIME_COMMANDS}}


def _apply_green(core, rows: list[dict], dry: list[dict], plan: dict,
                 bootstrap_prechecked: bool = False) -> dict:
    """Delegate all installation to MDL135's existing guarded tools_apply."""
    allowed = {r["env"] for r in rows if r["state"] == "PASS"}
    allowed.intersection_update(d["env"] for d in dry if d["state"] == "PASS")
    stages = [dict(s) for s in plan.get("stages", []) if s["env"] in allowed
              and s["kind"] in ("INSTALL_TOOLS", "VERIFY_TOOLS")]
    ids = {s["id"] for s in stages}
    stages = [s for s in stages if all(d in ids for d in s.get("deps", []))]
    # Never include a repair or destructive stage, including one indirectly
    # required by a VERIFY_TOOLS step.
    filtered = {"stages": stages, "state": "PLAN"}
    summary = core.tools_apply(filtered, approve=True, bootstrap_prechecked=bootstrap_prechecked)
    return {"summary": summary, "stages": stages, "state": filtered["state"]}


def _provision_missing(core, plan: dict, env_root: str) -> list[dict]:
    """Create only absent, declared via_ environments. Recheck them before installing."""
    result = []
    uv = shutil.which("uv")
    root = Path(env_root).resolve()
    ok, _ = core.unitest_gate()
    bootstrap, reason = core.rungate_bootstrap_only() if not ok else (False, "")
    for stage in plan.get("stages", []):
        if stage["kind"] != "ENSURE_ENV":
            continue
        name = stage["env"]
        path = (root / name).resolve()
        if not ok and not bootstrap:
            result.append({"env": name, "state": "BLOCK", "why": f"L19: {reason or 'RunGate not GREEN'}"})
            continue
        if not uv or not name.lower().startswith("via_") or path.parent != root or path.exists():
            result.append({"env": name, "state": "BLOCK", "why": "invalid, existing, or uv absent"})
            continue
        version = stage.get("python")
        if not version:
            result.append({"env": name, "state": "BLOCK", "why": "missing declared Python version"})
            continue
        outcome = core.run_cmd([uv, "venv", str(path), "--python", str(version)], timeout=UV_TIMEOUT)
        result.append({"env": name, "state": "CREATED" if outcome["rc"] == 0 else "BLOCK",
                       "why": (outcome.get("out", "") + outcome.get("err", ""))[-300:]})
        if outcome["rc"] != 0:
            break
    return result


def run(core, args: list[str]) -> int:
    env_root = core._arg_after(args, "--env-root") or str(Path.home() / "envs")
    base_python = core._arg_after(args, "--base-python")
    execute = "--execute" in args
    before = _snapshot(core, base_python, env_root)
    rows = before["rows"]
    dry = _uv_preflight(core, rows, before["toolplan"])
    runnable = bool(dry) and all(d["state"] == "PASS" for d in dry) and all(
        r["state"] == "PASS" for r in rows)
    base_ok = rows[0]["state"] == "PASS" and before["drift"]["state"] != "CHANGED"
    gate_ok, gate_reason = core.unitest_gate() if execute else (False, "plan only")
    bootstrap, boot_reason = core.rungate_bootstrap_only() if execute and not gate_ok else (False, "")
    previous = (core._read_json(core.LKGC_LATEST, {}) or {}) if core.LKGC_LATEST.exists() else {}
    restore = {name: {"good_at": value.get("good_at"), "lock": value.get("lock_lkgc") or value.get("lock"),
                      "stale_since": value.get("stale_since")}
               for name, value in (previous.get("envs") or {}).items()}
    rebuild = [r["env"] for r in rows if r["env"] != "BASE" and
               any(r["checks"][h]["state"] == "BLOCK" for h in
                   ("interpreter_identity", "native_abi", "distribution_shadow"))]
    report = {"schema": REPORT_SCHEMA, "at": datetime.now(timezone.utc).isoformat(),
              "mode": "execute" if execute else "plan", "base_python": base_python,
              "env_root": env_root, "baseline": before["baseline"], "roster": before["roster"],
              "unitest_gate": gate_reason, "bootstrap_prechecked": bootstrap,
              "bootstrap_reason": boot_reason,
              "drift": before["drift"], "base_optimization": before["base_analysis"],
              "hubs": HUB_NAMES, "diagnostic_tools": before["diagnostics"],
              "diagnostic_tools_missing": [k for k, v in before["diagnostics"].items() if not v],
              "runtime_commands": before["runtime_commands"],
              "envs": rows, "pending": _pending(before["toolplan"]), "uv_dry_run": dry,
              "rebuild_required": rebuild, "restore_points": restore,
              "routing": before["toolplan"].get("isolation", {}),
              "multi_version_hubs": before["toolplan"].get("hubs", {}),
              "previous_success": str(core.LKGC_LATEST) if core.LKGC_LATEST.exists() else None,
              "provision": [], "execution": None, "postcheck": None, "state": "PLAN"}
    # Write a pre-action restore point even for a blocked or failed run.
    report["state"] = "READY" if base_ok and runnable else "BLOCKED"
    prepath = _save(core, report)
    if execute and base_ok and core._consent():
        report["provision"] = _provision_missing(core, before["toolplan"], env_root)
        if report["provision"]:
            refreshed = _snapshot(core, base_python, env_root)
            rows = refreshed["rows"]
            report["envs"] = rows
            report["pending"] = _pending(refreshed["toolplan"])
            report["diagnostic_tools"] = refreshed["diagnostics"]
            dry = _uv_preflight(core, rows, refreshed["toolplan"])
            report["uv_dry_run"] = dry
            before = refreshed
            runnable = bool(dry) and all(d["state"] == "PASS" for d in dry)
            base_ok = rows[0]["state"] == "PASS" and before["drift"]["state"] != "CHANGED"
        if any(s["state"] == "BLOCK" for s in report["provision"]):
            runnable = False
    if any(r["state"] != "PASS" for r in rows):
        runnable = False
    if execute and base_ok and runnable and core._consent():
        report["execution"] = _apply_green(core, rows, dry, before["toolplan"],
                                           bootstrap_prechecked=bootstrap)
        after = _snapshot(core, base_python, env_root)
        report["postcheck"] = [{"env": x["env"], "state": x["state"], "checks": x["checks"]}
                               for x in after["rows"]]
        report["state"] = ("PASS" if report["execution"]["summary"]["ran"] > 0
                           and report["execution"]["summary"]["fails"] == 0
                           and all(x["state"] == "PASS" for x in after["rows"])
                           and not _pending(after["toolplan"]) else "POSTCHECK_FAILED")
        if report["state"] == "PASS":
            # Reuse the canonical per-environment success ledger and lock files.
            scans = core.panorama(core.discover_envs(core.load_baseline(), [], env_root, base_python),
                                  workers=MAX_WORKERS, task_timeout=RUN_TIMEOUT, quiet=True)
            base_scan = next(x for x in scans if x["env"]["name"] == "BASE")
            analysis = core.analyze_base(base_scan, core.load_baseline(),
                                         {x["env"]["name"] for x in scans}, core.lessons_skip())
            problems = core.classify_conflicts(scans, core.load_baseline(), analysis, core.lessons_skip())
            lkgc = core.lkgc_snapshot(scans, analysis, problems, core._RUN_ID)
            report["lkgc"] = core.lkgc_promote(lkgc)
    elif execute and not report["pending"] and all(r["state"] == "PASS" for r in rows):
        report["state"] = "PASS_NO_CHANGES"
    elif execute:
        report["state"] = "BLOCKED_CONSENT" if not core._consent() else "BLOCKED"
    finalpath = _save(core, report, lesson=True)
    print(f"[八路衝突+uv] {report['state']} · 境 {len(rows)} · 待裝 {len(report['pending'])} 段")
    if report["rebuild_required"]:
        print("  身分或 ABI 錯位，需先由現有 via-rebuild 重建: " + ", ".join(report["rebuild_required"]))
    for row in rows:
        if row["state"] != "PASS":
            issues = [f"{k}:{v['detail'][:50]}" for k, v in row["checks"].items() if v["state"] != "PASS"]
            print(f"  {row['env']} {row['state']} " + "; ".join(issues[:4]))
    print(f"  成功基線 {report['previous_success'] or '尚無'} · 前檢 {prepath} · 結果 {finalpath}")
    return 0 if report["state"] in ("READY", "PASS", "PASS_NO_CHANGES") else 2
