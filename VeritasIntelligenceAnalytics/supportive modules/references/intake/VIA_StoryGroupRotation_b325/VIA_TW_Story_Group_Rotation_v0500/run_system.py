from __future__ import annotations

"""Command-line entrypoint for VIA story-group rotation v0.5.0."""

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from engine.via_candidate49_adapter import def_prepare_candidate49
from engine.via_system_orchestrator import (
    def_input_preflight,
    def_load_json,
    def_read_table,
    def_resolve_path,
    def_run_pipeline_from_config,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = BASE_DIR / "config" / "system_config.json"


def def_json_default(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def def_main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("candidate49", "preflight-real", "run-real"),
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--as-of")
    parser.add_argument(
        "--evidence-cutoff-at",
        help="PIT cutoff for after-close ETF/revenue evidence; defaults to market availability",
    )
    parser.add_argument("--proposed-at", default="2026-09-02 18:00:00+08:00")
    parser.add_argument("--no-write", action="store_true")
    arguments = parser.parse_args()
    raw_config = def_load_json(arguments.config)
    base_dir = arguments.config.parent.parent
    if arguments.command == "preflight-real":
        result = def_input_preflight(base_dir, raw_config)
        print(result.to_json(orient="records", force_ascii=False, date_format="iso", indent=2))
        return 0 if not result["BlocksCorePipeline"].any() else 2
    if arguments.command == "candidate49":
        path = def_resolve_path(base_dir, raw_config["candidate_story_membership"])
        _, audit = def_prepare_candidate49(def_read_table(path), arguments.proposed_at)
        print(json.dumps(audit, ensure_ascii=False, indent=2, default=def_json_default))
        return 0 if audit["DeclaredShapeMatches"] else 2
    output = def_run_pipeline_from_config(
        arguments.config,
        proposed_at=arguments.proposed_at,
        as_of_date=arguments.as_of,
        evidence_cutoff_at=arguments.evidence_cutoff_at,
        write_output=not arguments.no_write,
    )
    summary = {
        "Status": "PASS",
        "TableCount": len(output["Tables"]),
        "Manifest": output["Manifest"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=def_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(def_main())
