from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY = Path(__file__).with_name("VIA_SSOT_Engine_Registry_v5.json")


class SSOTRegistry:
    """Read-only resolver for the VIA SSOT engine registry.

    This runtime helper does not import, install, execute, or modify any engine.
    It resolves names and returns execution plans only.
    """

    def __init__(self, path: str | Path = DEFAULT_REGISTRY) -> None:
        self.path = Path(path).expanduser().resolve()
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        self.engines = {item["engine_id"]: item for item in self.data["engines"]}
        self.accelerators = {item["accelerator_id"]: item for item in self.data["accelerators"]}
        self.profiles = {item["profile_id"]: item for item in self.data["acceleration_profiles"]}
        self.adapters = {item["adapter_id"]: item for item in self.data["adapters"]}
        self.contracts = {item["contract_id"]: item for item in self.data["contracts"]}
        self.aliases: dict[str, list[str]] = {}
        for item in self.data.get("legacy_aliases", []):
            ids = item.get("canonical_ids") or [item["canonical_id"]]
            self.aliases[str(item["alias"]).casefold()] = [str(value) for value in ids]
        for engine in self.data["engines"]:
            for alias in engine.get("legacy_aliases", []):
                self.aliases.setdefault(str(alias).casefold(), []).append(engine["engine_id"])
        for engine_ids in self.aliases.values():
            # Preserve insertion order while removing duplicate resolutions.
            seen: set[str] = set()
            engine_ids[:] = [value for value in engine_ids if not (value in seen or seen.add(value))]

    def resolve_engine(self, name_or_id: str) -> dict[str, Any]:
        key = str(name_or_id)
        if key in self.engines:
            return dict(self.engines[key])
        matches = self.aliases.get(key.casefold(), [])
        if not matches:
            raise KeyError(f"Unknown engine or legacy alias: {name_or_id}")
        if len(matches) > 1:
            raise KeyError(f"Ambiguous legacy alias {name_or_id!r}: {matches}")
        return dict(self.engines[matches[0]])

    def acceleration_plan(self, name_or_id: str, workload: dict[str, Any] | None = None) -> dict[str, Any]:
        engine = self.resolve_engine(name_or_id)
        profile = self.profiles[engine["acceleration_profile_id"]]
        workload = dict(workload or {})
        requested_mode = str(workload.get("mode", profile["mode"]))
        allowed_modes = {"safe", "balanced", "maxsafe", "aggressive"}
        mode = requested_mode if requested_mode in allowed_modes else profile["mode"]
        return {
            "schema": "VIA_ACCELERATION_DECISION/2.0",
            "engine_id": engine["engine_id"],
            "engine_version": engine["version"],
            "profile_id": profile["profile_id"],
            "mode": mode,
            "specialization": profile["specialization"],
            "accelerator_ids": list(profile["accelerators"]),
            "workload": workload,
            "safety": {
                "source_write": False,
                "code_execution": False,
                "network": False,
                "subprocess": False,
                "package_install": False,
            },
            "fallback": "sequential_order_preserving",
            "status": "PLAN_ONLY_NOT_EXECUTED",
        }

    def dependencies(self, name_or_id: str) -> list[str]:
        return list(self.resolve_engine(name_or_id).get("depends_on", []))

    def summary(self) -> dict[str, Any]:
        return {
            "schema": "VIA_SSOT_RUNTIME_SUMMARY/1.0",
            "registry_id": self.data["registry_id"],
            "registry_version": self.data["registry_version"],
            "system_id": self.data["system"]["system_id"],
            "engine_count": len(self.engines),
            "accelerator_count": len(self.accelerators),
            "profile_count": len(self.profiles),
            "adapter_count": len(self.adapters),
            "contract_count": len(self.contracts),
            "activation": self.data["system"]["activation"],
            "network_default": self.data["system"]["network_default"],
            "code_execution_default": self.data["system"]["code_execution_default"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only VIA SSOT registry resolver")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("summary")
    resolve = sub.add_parser("resolve")
    resolve.add_argument("name_or_id")
    plan = sub.add_parser("acceleration-plan")
    plan.add_argument("name_or_id")
    plan.add_argument("--mode", choices=["safe", "balanced", "maxsafe", "aggressive"])
    args = parser.parse_args()
    registry = SSOTRegistry(args.registry)
    if args.command == "summary":
        result = registry.summary()
    elif args.command == "resolve":
        result = registry.resolve_engine(args.name_or_id)
    else:
        result = registry.acceleration_plan(args.name_or_id, {"mode": args.mode} if args.mode else {})
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
