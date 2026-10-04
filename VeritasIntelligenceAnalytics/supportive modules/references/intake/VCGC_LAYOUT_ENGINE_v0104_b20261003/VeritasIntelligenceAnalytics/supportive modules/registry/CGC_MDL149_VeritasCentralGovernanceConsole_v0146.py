#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC: add layout review through the existing GLE hub; keep all old routes."""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from pathlib import Path

# def 01_PARAMETERS
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = "v0146"
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0144.py"
LAYOUT_HUB = VIA / "supportive modules/70_VRN_Rules"
LAYOUT_PATTERN = "SUP_MDL743_GenericLayoutHub_v*.py"
DEFAULT_OUTPUT = VIA / "VIA_Reports/layout_review"

# ===== [VIA:ACCEL-BRIDGE:v0100] existing compatibility bridge =====
try:
    sys.path.insert(0, str(VIA / "supportive modules"))
    import VIA_SuperAccel_Module as VIA_ACCEL
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====


def def_load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = def_load(PREVIOUS, "vcgc_layout_previous")
body = prev.prev.body


def __getattr__(name: str):
    return getattr(prev, name)


def def_layout_hub():
    choices = sorted(LAYOUT_HUB.glob(LAYOUT_PATTERN))
    if not choices:
        raise RuntimeError("ABSENT: GenericLayoutHub")
    hub = def_load(choices[-1], "vcgc_layout_hub")
    if not callable(getattr(hub, "def_run_batch", None)):
        raise RuntimeError("ABSENT: complete layout review route")
    return hub


def def_layout_command(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="VCGC Layout review; locked extraction stays unchanged")
    parser.add_argument("--dir", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args(argv)
    locator = def_load(HERE / "CGC_MDL149_LayoutUse_v0100.py", "vcgc_layout_input_locator")
    source = args.dir if args.dir is not None else locator.sample_dir()
    hub = def_layout_hub()
    report = hub.def_run_batch(source, args.out)
    summary = {k: report[k] for k in ("via", "state", "errors", "cache_hits", "financial_database_written")}
    summary.update(documents=len(report["documents"]), page=str(args.out / hub.HTML_NAME))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.open:
        import webbrowser
        webbrowser.open((args.out / hub.HTML_NAME).resolve().as_uri())
    return 1 if report["errors"] else 2


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["layout", "--selftest"]:
        return def_layout_hub().selftest()
    if args and args[0] == "layout":
        for gate in (body.require_token_gate, body.policy_step, body.env_step):
            if gate():
                return 2
        return def_layout_command(args[1:])
    original = sys.argv
    try:
        sys.argv = [original[0], *args]
        result = prev.main()
        if args and args[0] in {"help", "-h", "--help"}:
            print("layout [--dir PATH] [--out PATH] [--open] · complete layout review, no stock database writes")
        return result
    finally:
        sys.argv = original


if __name__ == "__main__":
    raise SystemExit(main())
