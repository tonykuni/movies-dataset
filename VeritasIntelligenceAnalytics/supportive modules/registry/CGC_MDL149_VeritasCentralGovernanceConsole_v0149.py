#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registration tail. Read the plan first. Write only when nothing would be retired.

Layout-only stays on v0148. NLP-only adds the roster and the named uses.
TA-Lib is refused. A registry-sync without --layout-only or --nlp-only is not
accepted here.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0148.py"
ROSTER = HERE / "VIA_NLP_Roster_v0100.json"
USES = HERE / "VIA_NLP_Uses_v0100.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0148_for_v0149")
body = prev.body


def __getattr__(name: str):
    return getattr(prev, name)


def _nlp_rows() -> tuple[list[dict], list[str]]:
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    uses = json.loads(USES.read_text(encoding="utf-8"))
    rows: list[dict] = []
    missing: list[str] = []
    for item in roster["rows"]:
        path = VIA / item["path"]
        if not path.is_file():
            missing.append(item["id"])
            continue
        source = Path(item["path"]).as_posix()
        identity = "nlp/" + item["id"]
        rows.append({"key": "feature|" + identity, "category": "feature", "identity": identity, "source": source})
        if path.suffix == ".py":
            rows.append({"key": "module|" + identity, "category": "module", "identity": identity, "source": source})
    inside = VIA / uses["inside"]
    for name in uses["uses"]:
        if not (inside / f"{name}.py").is_file():
            missing.append(name)
            continue
        identity = "nlp/use/" + name
        rows.append({"key": "feature|" + identity, "category": "feature", "identity": identity, "source": uses["inside"] + "/" + name + ".py"})
    engine = "functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1_9_0/VIA_NLP_OneEngine_v1_9_0.py"
    for name in uses["inside_190_only"]:
        identity = "nlp/inside/" + name
        rows.append({"key": "feature|" + identity, "category": "feature", "identity": identity, "source": engine})
    return rows, missing


def _sync(selected: list[dict], apply: bool) -> dict:
    if any("talib" in row["key"].lower() for row in selected):
        return {"state": "REFUSED", "why": "talib", "stale": 0, "new": 0}
    baseline = body._json(body.COMPONENT_REGISTRY) or {}
    retained = {row["key"]: dict(row) for row in baseline.get("records") or [] if row.get("state", "ACTIVE") == "ACTIVE"}
    retained.update({row["key"]: row for row in selected})
    inventory = {"rows": list(retained.values()), "counts": {}, "parse_errors": []}
    for row in inventory["rows"]:
        inventory["counts"][row["category"]] = inventory["counts"].get(row["category"], 0) + 1
    saved = body.live_components

    def _live():
        return inventory

    try:
        body.live_components = _live
        plan = body.registry_sync(False)
        if plan.get("stale"):
            plan["state"] = "REFUSED"
            plan["why"] = "stale before write"
            return plan
        if not apply:
            return plan
        return body.registry_sync(True)
    finally:
        body.live_components = saved


def _gates() -> int:
    for gate in (body.require_token_gate, body.policy_step, body.env_step):
        if gate():
            return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["registry-sync"] and "--nlp-only" in args:
        rows, missing = _nlp_rows()
        if missing:
            print(json.dumps({"state": "REFUSED", "missing": missing}, ensure_ascii=False))
            return 2
        if "--selftest" not in args and _gates():
            return 2
        result = _sync(rows, "--apply" in args and "--selftest" not in args)
        print(json.dumps({k: result.get(k) for k in ("state", "new", "changed", "stale", "why")}, ensure_ascii=False, indent=1))
        return 0 if not result.get("stale") and result.get("state") != "REFUSED" else 2
    if args[:1] == ["registry-sync"] and "--layout-only" in args:
        if "--selftest" not in args and _gates():
            return 2
        plan = prev.def_registry_layout(False)
        if plan.get("stale"):
            print(json.dumps({"state": "REFUSED", "why": "stale before write", "stale": plan["stale"]}, ensure_ascii=False))
            return 2
        if "--apply" not in args:
            print(json.dumps({k: plan.get(k) for k in ("state", "new", "changed", "stale")}, ensure_ascii=False, indent=1))
            return 0
        result = prev.def_registry_layout(True)
        print(json.dumps({k: result.get(k) for k in ("state", "new", "changed", "stale")}, ensure_ascii=False, indent=1))
        return 0 if not result.get("stale") else 2
    return prev.main(args)


def selftest() -> int:
    rows, missing = _nlp_rows()
    plan = _sync(rows, False)
    ok = not missing and plan.get("stale") == 0 and plan.get("state") != "REFUSED" and len(rows) == 41
    print("  [OK]" if ok else "  [FAIL] " + ",".join(missing))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
