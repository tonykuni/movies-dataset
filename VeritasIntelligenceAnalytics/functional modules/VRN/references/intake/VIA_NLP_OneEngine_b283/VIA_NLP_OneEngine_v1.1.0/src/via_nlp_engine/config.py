"""Configuration loading, validation and path resolution."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.json"
ENV_CONFIG_PATH = "VIA_NLP_CONFIG"
ENV_PREFIX = "VIA_NLP__"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _parse_env_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _apply_env(config: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(config)
    for name, raw in os.environ.items():
        if not name.startswith(ENV_PREFIX):
            continue
        keys = name[len(ENV_PREFIX) :].lower().split("__")
        cursor = result
        for key in keys[:-1]:
            cursor = cursor.setdefault(key, {})
        cursor[keys[-1]] = _parse_env_value(raw)
    return result


def _resolve_project_path(value: str, project_root: Path) -> str:
    path = Path(value).expanduser()
    return str(path if path.is_absolute() else (project_root / path).resolve())


def validate_config(config: dict[str, Any]) -> None:
    required_sections = {"engine", "resources", "routing", "cache", "jobs", "knowledge", "ml", "deep", "translation", "security"}
    missing = required_sections.difference(config)
    if missing:
        raise ValueError(f"Missing configuration sections: {sorted(missing)}")

    resources = config["resources"]
    thresholds = [
        float(resources["warning_ram_percent"]),
        float(resources["shed_ram_percent"]),
        float(resources["critical_ram_percent"]),
    ]
    if not (0 < thresholds[0] < thresholds[1] < thresholds[2] <= 100):
        raise ValueError("RAM thresholds must satisfy 0 < warning < shed < critical <= 100")
    if int(config["engine"]["max_concurrency"]) < 1:
        raise ValueError("max_concurrency must be >= 1")
    if int(config["engine"]["max_text_chars"]) < 1:
        raise ValueError("max_text_chars must be >= 1")
    if any(int(tier) not in {1, 2, 3, 4} for tier in config["routing"]["allow_tiers"]):
        raise ValueError("allow_tiers may only contain 1, 2, 3, 4")
    knowledge = config["knowledge"]
    if not (0 < float(knowledge["topic_threshold"]) <= float(knowledge["topic_merge_threshold"]) <= 1):
        raise ValueError("knowledge thresholds must satisfy 0 < topic <= merge <= 1")
    if int(knowledge["max_topics"]) < 1 or int(knowledge["max_ai_graph_edges"]) < 100:
        raise ValueError("knowledge limits are invalid")


def load_config(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    selected = Path(path or os.environ.get(ENV_CONFIG_PATH, DEFAULT_CONFIG_PATH)).expanduser().resolve()
    with selected.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if overrides:
        config = _deep_merge(config, overrides)
    config = _apply_env(config)

    project_root = selected.parent.parent if selected.parent.name == "config" else PROJECT_ROOT
    config["_meta"] = {"config_path": str(selected), "project_root": str(project_root)}
    config["engine"]["data_dir"] = _resolve_project_path(config["engine"]["data_dir"], project_root)
    config["engine"]["lexicon_path"] = _resolve_project_path(config["engine"]["lexicon_path"], project_root)
    config["engine"]["governance_path"] = _resolve_project_path(config["engine"]["governance_path"], project_root)
    validate_config(config)
    return config
