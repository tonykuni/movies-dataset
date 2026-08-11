#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_DataHub_Orchestrator_v0101 — NoStall 版(正本零觸碰;版本前進)
====================================================================
正本 VDF_DataHub_Orchestrator.py 的煙測 TIMEOUT 根因:
  def_import_all_supportive_modules() 於主程序內 bootstrap 7 個重支援模組
  (含 VIA_EnvManager — 與 via-envmgr conflicts 卡斷同源:內部環境掃描小時級)。
本版修法(與 via_envmgr_nostall 同型):
  ① 支援模組導入丟到「子程序」跑,硬逾時 --supportive-timeout(預設 180s)到點 kill
     → 誠實記 TIMEOUT 狀態,主流程繼續(不卡斷),整體 status 仍 fail-closed 誠實判
  ② --skip-supportive:完全跳過支援模組段(記 SKIPPED,不假綠)
  ③ DB 檢查段完全重用正本函式(runtime 注入替換,正本檔案零觸碰)
用法:
  py VDF_DataHub_Orchestrator_v0101.py --data-root <dir> --run-root <dir>
     --core-root <supportive modules dir> --output <hb.json>
     [--supportive-timeout 180] [--skip-supportive]
  (內部)--import-worker <core-root>:子程序模式,單做支援模組導入印 JSON
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_CANON = _HERE / "VDF_DataHub_Orchestrator.py"


def load_canon():
    spec = importlib.util.spec_from_file_location("vdf_datahub_canon", _CANON)
    m = importlib.util.module_from_spec(spec)
    sys.modules["vdf_datahub_canon"] = m  # dataclass/typing 解析需先註冊
    spec.loader.exec_module(m)
    return m


def supportive_via_subprocess(core_root: str, timeout_sec: int) -> dict:
    """子程序隔離跑正本的支援模組導入;硬逾時 kill → 誠實 TIMEOUT 狀態。"""
    try:
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--import-worker", core_root],
            capture_output=True, text=True, timeout=timeout_sec,
        )
        for line in reversed((proc.stdout or "").strip().splitlines()):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
        return {
            "ready": False, "imported_count": 0, "expected_count": 7,
            "missing_modules": [], "module_errors":
                {"worker": f"no-json-output exit={proc.returncode} stderr={(proc.stderr or '')[-400:]}"},
            "state_failures": [], "nostall": "WORKER_NO_OUTPUT",
        }
    except subprocess.TimeoutExpired:
        return {
            "ready": False, "imported_count": 0, "expected_count": 7,
            "missing_modules": [], "module_errors": {},
            "state_failures": [],
            "nostall": f"TIMEOUT_{timeout_sec}s_KILLED",
            "note": "支援模組 bootstrap 逾時被誠實截停(與 via-envmgr 卡斷同源;"
                    "主流程不卡斷續跑 DB 檢查;整體 status 仍 fail-closed)",
        }
    except Exception as exc:
        return {
            "ready": False, "imported_count": 0, "expected_count": 7,
            "missing_modules": [], "module_errors": {"worker": f"{type(exc).__name__}: {exc}"},
            "state_failures": [], "nostall": "WORKER_ERROR",
        }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--import-worker", metavar="CORE_ROOT")
    p.add_argument("--data-root")
    p.add_argument("--run-root")
    p.add_argument("--core-root")
    p.add_argument("--output")
    p.add_argument("--supportive-timeout", type=int, default=180)
    p.add_argument("--skip-supportive", action="store_true")
    args = p.parse_args()

    m = load_canon()

    if args.import_worker:
        # 子程序模式:單做支援模組導入(重活隔離在此;被父程序硬逾時管束)
        result = m.def_import_all_supportive_modules(Path(args.import_worker))
        print(json.dumps(result, ensure_ascii=False, default=str))
        return 0

    for req in ("data_root", "run_root", "core_root", "output"):
        if not getattr(args, req):
            p.error(f"--{req.replace('_','-')} is required")

    if args.skip_supportive:
        supportive = {
            "ready": False, "imported_count": 0, "expected_count": 7,
            "missing_modules": [], "module_errors": {}, "state_failures": [],
            "nostall": "SKIPPED_BY_FLAG",
            "note": "--skip-supportive:支援模組段跳過(誠實記 SKIPPED,整體仍 fail-closed)",
        }
    else:
        supportive = supportive_via_subprocess(args.core_root, args.supportive_timeout)

    # runtime 注入:正本 def_bootstrap 內呼叫的導入函式換成預算結果(檔案零觸碰)
    m.def_import_all_supportive_modules = lambda _core_root: supportive
    payload = m.def_bootstrap(Path(args.data_root), Path(args.run_root), Path(args.core_root))
    payload["orchestrator_version"] = "v0101-nostall"
    payload["supportive_timeout_sec"] = args.supportive_timeout
    m.def_write_json(Path(args.output), payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
