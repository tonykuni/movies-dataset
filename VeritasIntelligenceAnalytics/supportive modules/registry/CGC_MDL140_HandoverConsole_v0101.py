"""SYSTEM MANAGER / 使用者：交接防遺漏閘 v0101。
Check 比對需求、待辦、來源通道、模組註冊、加速器、成功鎖及測試相依指紋；
checkpoint 保存可續接快照，test 經 VCGC 留存實測證據；build/status/md 延續舊頁。
交接 GREEN 只表示資料可續接，closeout 另判；缺件或無證據不能升格為驗收成功。
不執行 OCR、不連資料庫、不搬動舊依賴、不使用 TA-Lib。版本 v0101；更新 2026-09-29T15:38:10+00:00"""
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
import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = "v0101"
ENGINE = "CGC_MDL140_HandoverConsole"
_STEM = ENGINE
POLICY = HERE / "VIA_Handoff_Continuity_SSOT_v0100.json"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def sha(path):
    # Git text may be checked out as CRLF on Windows. Binary bytes stay exact.
    data = Path(path).read_bytes()
    if Path(path).suffix.lower() in {".py", ".ps1", ".json", ".jsonl", ".md", ".yml", ".txt", ".log"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def local(via, relative):
    p = (Path(via) / relative).resolve()
    if not p.is_relative_to(Path(via).resolve()):
        raise ValueError("outside project: " + str(relative))
    return p


def newest(via, pattern):
    hits = list(Path(via).glob(pattern))
    return max(hits, key=lambda p: int(re.search(r"_v(\d+)", p.name)[1])) if hits else None


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
    tmp.replace(path)


def capture(via=VIA, policy=None):
    """Read declared owners only; no engines, OCR, database or network calls."""
    via = Path(via)
    policy = policy or read(via / POLICY.relative_to(VIA))
    files = {}
    for pattern in policy["watch"]:
        for p in sorted(via.glob(pattern)):
            if p.is_file():
                files[p.relative_to(via).as_posix()] = sha(p)
    reqpath = newest(via, policy["requirements"])
    book = read(reqpath) if reqpath else {}
    rows = book.get("requirements", [])
    if len({r["code"] for r in rows}) != len(rows):
        raise ValueError("duplicate requirement IDs")
    return {"files": files, "requirements": {r["code"]: {
        "definition": fingerprint({k: r.get(k) for k in ("requirement", "homes", "quotes")}),
        "status": r.get("status"), "next": r.get("next"), "owner": r.get("hand"),
        "topic": r.get("topic"), "homes": r.get("homes", [])} for r in rows}}


def evidence_status(via, receipt):
    """A zero exit code alone is insufficient: exact target marker and dependency hashes are required."""
    errors = []
    if receipt.get("schema") != "VIA.Handoff.TestReceipt.v1":
        errors.append("receipt schema")
    if receipt.get("rc") != 0 or not receipt.get("target_marker_seen") or not receipt.get("completed_at"):
        errors.append("test did not prove target success")
    if not receipt.get("command") or not receipt.get("dependencies"):
        errors.append("missing command/dependencies")
    for rel, expected in receipt.get("dependencies", {}).items():
        p = local(via, rel)
        if not p.is_file() or sha(p) != expected:
            errors.append("dependency changed: " + rel)
    log = local(via, receipt.get("log", "__absent__"))
    if not log.is_file() or sha(log) != receipt.get("log_sha256"):
        errors.append("test log missing/changed")
    return errors


def audit(via=VIA, policy=None, baseline=None, require_baseline=True):
    """Resume GREEN means nothing omitted. Closeout remains YELLOW while work is pending."""
    via = Path(via)
    policy = policy or read(via / POLICY.relative_to(VIA))
    state = capture(via, policy)
    rows, pending, reusable = [], [], []
    def issue(lamp, rule, detail):
        rows.append({"lamp": lamp, "rule": rule, "detail": detail})
    point = local(via, policy["checkpoint"])
    baseline = baseline if baseline is not None else read(point) if point.exists() else None
    if baseline:
        old = baseline.get("state", {})
        for rel, expected in baseline.get("frozen_sources", {}).items():
            if policy["frozen_sources"].get(rel) != expected:
                issue("RED", "LOCK_DEFINITION_REMOVED_OR_CHANGED", rel)
        for key in ("required_source_lanes", "managed_modules"):
            removed = sorted(set(baseline.get(key, [])) - set(policy[key]))
            if removed:
                issue("RED", "POLICY_SCOPE_REMOVED", {key: removed})
        for code in sorted(set(old.get("requirements", {})) - set(state["requirements"])):
            issue("RED", "REQ_REMOVED", code)
        for code, value in state["requirements"].items():
            if old.get("requirements", {}).get(code) != value:
                issue("YELLOW", "REQ_CHANGED", code)
        for rel in sorted(set(old.get("files", {})) - set(state["files"])):
            issue("RED", "FILE_REMOVED", rel)
        changed = [rel for rel, h in state["files"].items() if old.get("files", {}).get(rel) != h]
        if changed:
            issue("YELLOW", "CHECKPOINT_STALE", changed)
        # Pending work cannot disappear merely because it was absent from a new conversation.
        current = {x["id"]: x for x in policy["work_items"]}
        for code, item in baseline.get("work_items", {}).items():
            if code not in current:
                issue("RED", "WORK_ITEM_REMOVED", code)
    elif require_baseline:
        issue("YELLOW", "CHECKPOINT_MISSING", policy["checkpoint"])
    for rel, expected in policy["frozen_sources"].items():
        p = local(via, rel)
        if not p.is_file() or sha(p) != expected:
            issue("RED", "SUCCESS_LOCK_CHANGED", rel)
    # The central tool lock is authoritative, not a duplicate list of tool versions.
    lock = read(local(via, policy["tool_lock"]))
    for name, definition in lock.items():
        if not isinstance(definition, dict) or "sha256" not in definition:
            continue
        rel = definition["path"].removeprefix("VeritasIntelligenceAnalytics/")
        p = local(via, rel)
        if not p.is_file() or sha(p) != definition["sha256"]:
            issue("RED", "TOOL_LOCK_CHANGED", name)
    reqs = state["requirements"]
    if not reqs:
        issue("RED", "REQUIREMENTS_MISSING", policy["requirements"])
    for code, req in reqs.items():
        if req["status"] in {"PARTIAL", "MISSING"}:
            # Preserve the owner's exact open state. Do not turn COVERED declarations into test passes.
            pending.append({"id": code, "state": req["status"], "owner": req["owner"] or "AI",
                            "next": req["next"] or "核對正主需求與證據後補齊驗收", "topic": req["topic"]})
    items = policy["work_items"]
    if len({x["id"] for x in items}) != len(items):
        issue("RED", "DUPLICATE_WORK_ITEM", "work_items")
    receipts = {}
    tested_dependencies = set()
    for item in items:
        if item.get("requirement") not in reqs:
            issue("RED", "UNREGISTERED_REQUIREMENT", item["id"])
        if item.get("state") == "VERIFIED":
            rel = item.get("receipt", "")
            p = local(via, rel or "__absent__")
            try:
                receipt = read(p)
                problems = evidence_status(via, receipt)
                if receipt.get("case") != item.get("case"):
                    problems.append("receipt belongs to a different case")
                declared = policy.get("test_cases", {}).get(item.get("case"))
                if declared and receipt.get("command", [])[1:] != ["run", *declared["argv"]]:
                    problems.append("command differs from declared test")
                if declared and receipt.get("case_sha256") != fingerprint(declared):
                    problems.append("test contract changed")
            except (OSError, ValueError, KeyError) as exc:
                problems = [str(exc)]
            if problems:
                issue("RED", "EVIDENCE_INVALID", {"id": item["id"], "why": problems})
            else:
                reusable.append(item["id"])
                receipts[item["id"]] = {"path": rel, "sha256": sha(p)}
                tested_dependencies.update(receipt["dependencies"])
        elif item.get("state") in {"PENDING", "BLOCKED", "REVIEW"}:
            if not item.get("owner") or not item.get("next") or not item.get("reason"):
                issue("RED", "PENDING_WITHOUT_NEXT", item["id"])
            pending.append(item)
        else:
            issue("RED", "INVALID_WORK_STATE", item["id"])
    # Every new managed Python/PowerShell module must be registered and have the acceleration bridge.
    invpath = local(via, policy["component_inventory"])
    registered = {x.get("source") for x in read(invpath).get("records", [])} if invpath.exists() else set()
    changed_code = {rel for rel, value in state["files"].items()
                    if Path(rel).suffix in {".py", ".ps1"} and baseline
                    and baseline.get("state", {}).get("files", {}).get(rel) != value}
    required_tests = changed_code | set(policy["managed_modules"])
    for rel in sorted(required_tests - tested_dependencies):
        issue("RED", "CHANGED_CODE_WITHOUT_TEST", rel)
    registration_required = set(policy["managed_modules"]) | {
        p for p in changed_code if "/tests/" not in p and not Path(p).name.startswith("test_")}
    for rel in sorted(registration_required):
        p = local(via, rel)
        if not p.is_file():
            issue("RED", "MODULE_MISSING", rel)
            continue
        if rel not in registered:
            issue("RED", "MODULE_UNREGISTERED", rel)
        if p.suffix == ".py" and "[VIA:ACCEL-BRIDGE:" not in p.read_text(encoding="utf-8"):
            issue("RED", "ACCEL_BRIDGE_MISSING", rel)
    # Source fields are catalogued by source type, not deduplicated by value.
    src = read(local(via, policy["source_contract"]))
    kinds = [x["key"] for x in src["sources"]]
    if len(kinds) != len(set(kinds)) or not set(policy["required_source_lanes"]) <= set(kinds):
        issue("RED", "SOURCE_LANE_MISSING", kinds)
    lamps = [x["lamp"] for x in rows]
    lamp = "RED" if "RED" in lamps else "YELLOW" if lamps else "GREEN"
    return {"schema": "VIA.Handoff.Audit.v1", "engine": ENGINE + "_" + VERSION, "at": now(),
            "lamp": lamp, "closeout_lamp": "RED" if lamp == "RED" else "YELLOW" if pending or lamp == "YELLOW" else "GREEN",
            "meaning": "handoff integrity is separate from completed extraction or production acceptance",
            "rows": rows, "pending": pending, "reusable_successes": reusable,
            "receipts": receipts, "state": state,
            "frozen_sources": dict(policy["frozen_sources"]),
            "required_source_lanes": list(policy["required_source_lanes"]),
            "managed_modules": list(policy["managed_modules"]),
            "work_items": {x["id"]: copy.deepcopy(x) for x in items},
            "summary": {"requirements": len(reqs), "watched_files": len(state["files"]),
                        "pending": len(pending), "reusable": len(reusable), "findings": len(rows)}}


def checkpoint(via=VIA):
    policy = read(Path(via) / POLICY.relative_to(VIA))
    report = audit(via, policy, require_baseline=False)
    if report["lamp"] == "RED":
        return report
    # A changed requirement/code is acknowledged explicitly by checkpoint, never by check.
    # Frozen sources, removed requirements and invalid receipts already fail closed above.
    report["rows"] = []
    report["lamp"] = "GREEN"
    report["summary"]["findings"] = 0
    report["closeout_lamp"] = "YELLOW" if report["pending"] else "GREEN"
    point = local(via, policy["checkpoint"])
    if point.exists():
        old = read(point)
        archive = point.parent / "history" / (fingerprint(old) + ".json")
        if not archive.exists():
            atomic_json(archive, old)
    atomic_json(point, report)
    return report


def run_case(name, via=VIA):
    """Run only the declared test through VCGC. No shell interpolation or package installation."""
    via = Path(via)
    policy = read(via / POLICY.relative_to(VIA))
    case = policy["test_cases"][name]
    root = local(via, policy["evidence_dir"])
    receipt_path = root / (name + ".json")
    if receipt_path.exists():
        previous = read(receipt_path)
        if (previous.get("case_sha256") == fingerprint(case)
                and not evidence_status(via, previous)):
            print("[沿用成功] " + name + " · command / dependency / evidence unchanged")
            return 0
        history = root / "history" / (name + "-" + fingerprint(previous))
        prior_log = local(via, previous.get("log", "__absent__"))
        if not history.exists():
            history.mkdir(parents=True)
            atomic_json(history / "receipt.json", previous)
            if prior_log.exists():
                (history / "original_log.txt").write_bytes(prior_log.read_bytes())
    entry = newest(via, "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
    dependencies = {}
    for pattern in case["dependencies"] + ["supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"]:
        hits = [p for p in via.glob(pattern) if p.is_file()]
        if not hits:
            raise ValueError("dependency pattern absent: " + pattern)
        dependencies.update({p.relative_to(via).as_posix(): sha(p) for p in hits})
    command = [str(entry.relative_to(via)), "run", *case["argv"]]
    env = dict(os.environ, VIA_FROM_VCGC="YES", VIA_VCGC_PUSH="NO", VIA_HUB_RUN="handoff-" + name)
    started = now()
    try:
        result = subprocess.run([sys.executable, *command], cwd=via, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=case["timeout_seconds"])
        output, rc = result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        output, rc = "TIMEOUT: declared test budget exceeded\n", 124
    changed = any(sha(local(via, rel)) != h for rel, h in dependencies.items())
    marker = case["success_marker"] in output and not changed
    log = root / (name + ".txt")
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(output, encoding="utf-8", newline="")
    receipt = {"schema": "VIA.Handoff.TestReceipt.v1", "case": name, "command": command,
               "case_sha256": fingerprint(case),
               "started_at": started, "completed_at": now(), "rc": rc,
               "target_marker_seen": marker, "dependencies": dependencies,
               "environment": {"python": sys.version.split()[0], "platform": sys.platform},
               "log": log.relative_to(via).as_posix(), "log_sha256": sha(log),
               "scope": case["scope"], "production_database_verified": False}
    atomic_json(root / (name + ".json"), receipt)
    print(json.dumps({"case": name, "rc": rc, "marker": marker, "scope": case["scope"]}, ensure_ascii=False))
    return 0 if rc == 0 and marker else 1


_PRIOR = None


def prior():
    global _PRIOR
    if _PRIOR is None:
        _PRIOR = load_module(HERE / "CGC_MDL140_HandoverConsole_v0100.py", "_handover_original")
    return _PRIOR


def __getattr__(name):
    return getattr(prior(), name)


def gather(via=VIA, do_git=True):
    report = prior().gather(via, do_git)
    continuity = audit(via)
    report["cats"].append({"id": "continuity", "zh": "交接防遺漏", "matrices": [
        prior().matrix("continuity", "可接續／驗收分開判定", [dict(continuity["summary"],
            handoff=continuity["lamp"], closeout=continuity["closeout_lamp"])], continuity["lamp"]),
        prior().matrix("continuity", "必須接續的待辦", continuity["pending"], "YELLOW" if continuity["pending"] else "GREEN", empty_ok=True)]})
    report["lamps"]["continuity"] = continuity["lamp"]
    lamps = report["lamps"].values()
    report["summary"]["verdict"] = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN"
    return report


def selftest():
    path = HERE / "tests" / "test_handoff_continuity_v0100.py"
    suite = load_module(path, "_handoff_contract_tests")
    return suite.run(sys.modules[__name__])


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] VCGC entry required")
        return 2
    if args == ["--selftest"]:
        return selftest()
    parser = argparse.ArgumentParser(description="交接防遺漏：check 唯讀、checkpoint 保存、test 留存實測證據")
    parser.add_argument("verb", choices=["check", "checkpoint", "test", "build", "status", "md"])
    parser.add_argument("case", nargs="?")
    parser.add_argument("--json", action="store_true")
    options = parser.parse_args(args or ["check"])
    if options.verb == "test":
        return run_case(options.case)
    if options.verb in {"build", "status", "md"}:
        report = gather()
        if options.verb == "build":
            prior().build(rep=report)
        elif options.verb == "status":
            prior().status(report)
        else:
            print(prior().to_markdown(report))
        return 0
    report = checkpoint() if options.verb == "checkpoint" else audit()
    if options.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("[交接防遺漏] " + report["lamp"] + " · 驗收 " + report["closeout_lamp"] + " · " + json.dumps(report["summary"], ensure_ascii=False))
        for row in report["rows"]:
            print("[" + row["lamp"] + "] " + row["rule"] + " " + str(row["detail"])[:300])
        print("[下一步] " + "; ".join(x["id"] + ": " + x.get("next", "") for x in report["pending"][:5]))
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[report["lamp"]]


if __name__ == "__main__":
    raise SystemExit(main())
