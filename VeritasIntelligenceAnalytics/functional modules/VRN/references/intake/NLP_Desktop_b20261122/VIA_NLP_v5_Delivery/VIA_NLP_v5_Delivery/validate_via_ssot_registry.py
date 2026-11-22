from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REGISTRY = Path(__file__).with_name("VIA_SSOT_Engine_Registry_v5.json")


def unique(items: list[str], label: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for item in items:
        if item in seen:
            errors.append(f"duplicate {label}: {item}")
        seen.add(item)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a VIA SSOT engine registry")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    args = parser.parse_args(argv)
    selected_registry = args.registry.expanduser().resolve()
    data = json.loads(selected_registry.read_text(encoding="utf-8"))
    errors: list[str] = []
    engines = data["engines"]
    accelerators = data["accelerators"]
    profiles = data["acceleration_profiles"]
    adapters = data["adapters"]
    contracts = data["contracts"]
    gates = data["gates"]

    engine_ids = [item["engine_id"] for item in engines]
    accel_ids = [item["accelerator_id"] for item in accelerators]
    profile_ids = [item["profile_id"] for item in profiles]
    adapter_ids = [item["adapter_id"] for item in adapters]
    contract_ids = [item["contract_id"] for item in contracts]
    gate_ids = [item["gate_id"] for item in gates]
    unique(engine_ids, "engine_id", errors)
    unique(accel_ids, "accelerator_id", errors)
    unique(profile_ids, "profile_id", errors)
    unique(adapter_ids, "adapter_id", errors)
    unique(contract_ids, "contract_id", errors)
    unique(gate_ids, "gate_id", errors)

    engine_set = set(engine_ids)
    accel_set = set(accel_ids)
    profile_by_id = {item["profile_id"]: item for item in profiles}
    contract_set = set(contract_ids)
    adapter_set = set(adapter_ids)

    for engine in engines:
        eid = engine["engine_id"]
        if engine.get("acceleration_profile_id") not in profile_by_id:
            errors.append(f"{eid} missing acceleration profile")
        for dep in engine.get("depends_on", []):
            if dep not in engine_set:
                errors.append(f"{eid} missing dependency: {dep}")
        for cid in engine.get("input_contracts", []) + engine.get("output_contracts", []):
            if cid not in contract_set:
                errors.append(f"{eid} references missing contract: {cid}")
        for aid in engine.get("adapter_ids", []):
            if aid not in adapter_set:
                errors.append(f"{eid} references missing adapter: {aid}")
        profile = profile_by_id.get(engine.get("acceleration_profile_id"), {})
        if set(profile.get("accelerators", [])) != accel_set:
            errors.append(f"{eid} does not bind every standard accelerator")

    for profile in profiles:
        if profile["engine_id"] not in engine_set:
            errors.append(f"profile references missing engine: {profile['engine_id']}")
        for aid in profile.get("accelerators", []):
            if aid not in accel_set:
                errors.append(f"profile references missing accelerator: {aid}")

    for accelerator in accelerators:
        if accelerator["owner_engine"] != "VIA-ENG-011":
            errors.append(f"accelerator owner is not Celeritas: {accelerator['accelerator_id']}")

    for adapter in adapters:
        if adapter["from_engine"] not in engine_set:
            errors.append(f"adapter source missing: {adapter['adapter_id']}")
        for eid in adapter.get("to_engines", []):
            if eid not in engine_set:
                errors.append(f"adapter target missing: {adapter['adapter_id']} -> {eid}")

    # Kahn-style dependency cycle check.
    remaining = {engine["engine_id"]: set(engine.get("depends_on", [])) for engine in engines}
    order: list[str] = []
    while remaining:
        ready = sorted(eid for eid, deps in remaining.items() if not deps)
        if not ready:
            errors.append(f"dependency cycle: {sorted(remaining)}")
            break
        order.extend(ready)
        for eid in ready:
            remaining.pop(eid)
        for deps in remaining.values():
            deps.difference_update(ready)

    required_gates = set(data.get("activation_gates", []))
    if not required_gates.issubset(set(gate_ids)):
        errors.append("activation_gates contains an unknown gate")
    if data["system"]["acceleration_fabric"] != "VIA-ENG-011":
        errors.append("system acceleration fabric is not VIA-ENG-011")
    if data["system"]["governance_engine"] != "VIA-ENG-008":
        errors.append("system governance engine is not VIA-ENG-008")
    if data["source_policy"]["automatic_code_execution"] is not False:
        errors.append("automatic code execution must be false")
    if data["source_policy"]["silent_overwrite"] is not False:
        errors.append("silent overwrite must be false")

    result = {
        "schema": "VIA_SSOT_REGISTRY_VALIDATION/1.0",
        "registry": str(selected_registry),
        "status": "PASS" if not errors else "FAIL",
        "engine_count": len(engines),
        "accelerator_count": len(accelerators),
        "profile_count": len(profiles),
        "adapter_count": len(adapters),
        "contract_count": len(contracts),
        "gate_count": len(gates),
        "topological_order": order,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
