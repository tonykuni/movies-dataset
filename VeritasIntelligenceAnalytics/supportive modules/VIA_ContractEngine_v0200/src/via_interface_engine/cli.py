"""Command-line entrypoint for governed local execution."""

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

import argparse
import json
from pathlib import Path
from typing import Sequence

from .config import DEFAULT_OUTPUT_DIRECTORY, ENGINE_NAME, ENGINE_VERSION
from .demo import def_run_demo


# def 01 CLI PARAMETERS
CLI_DESCRIPTION = f"{ENGINE_NAME} v{ENGINE_VERSION}"
CLI_DEFAULT_COMMAND = "demo"


def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=CLI_DESCRIPTION)
    subparsers = parser.add_subparsers(dest="command")
    demo_parser = subparsers.add_parser("demo", help="執行完整契約／DI／UI／Twin 範例")
    demo_parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help="輸出 Schema、HTML 與測試證據的目錄",
    )
    return parser


def def_main(argv: Sequence[str] | None = None) -> int:
    parser = def_build_parser()
    arguments = parser.parse_args(argv)
    command = arguments.command or CLI_DEFAULT_COMMAND
    if command == "demo":
        output_directory = getattr(arguments, "output_dir", DEFAULT_OUTPUT_DIRECTORY)
        summary = def_run_demo(output_directory)
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if summary["gate"] == "PASS" else 2
    parser.error(f"不支援的指令: {command}")
    return 2

