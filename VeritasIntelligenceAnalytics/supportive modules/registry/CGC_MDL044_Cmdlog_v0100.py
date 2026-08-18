#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_cmdlog_v0100 — 指令執行留痕包裝器(TOOL-038;操作員令 2026-08-17)
======================================================================
令:執行任何指令若因錯誤中斷,前面任何紀錄要留下 LOGS。
機制:
  ① 逐行即時落檔 — 子行程輸出每一行「先寫 LOG 再上螢幕」(行緩衝
     +逐行 flush):崩潰/中斷/逾時當下,LOG 已含此前全部紀錄
  ② 三態終線 — 結尾必記 EXIT rc=N / INTERRUPTED(Ctrl+C)/
     SPAWN_FAIL,含起訖時戳與耗時;Ctrl+C 不吞:記錄後原樣退出
  ③ 零改被包指令 — 參數原樣透傳;rc 原樣回傳;stdin 接管(DEVNULL)
     防 input() 卡死(Windows 缺陷一前例)
  ④ LOG 落 VIA_Reports/command_logs/CMDLOG_<ts>_<名>.log(運行區)
用法:via-run <指令> [參數…]     例:via-run via-govroot
     via-run --list             → 列最近 10 筆 LOG
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LOGDIR = VIA / "VIA_Reports" / "command_logs"


def main() -> int:
    args = sys.argv[1:]
    if not args or args == ["--list"]:
        LOGDIR.mkdir(parents=True, exist_ok=True)
        logs = sorted(LOGDIR.glob("CMDLOG_*.log"))[-10:]
        print("=== via-run 留痕包裝器 v0100 ===")
        if args == ["--list"]:
            for p in logs:
                print(f"  {p.name} · {p.stat().st_size:,}B")
            print(f"  [計] 最近 {len(logs)} 筆 · {LOGDIR}")
            return 0
        print(__doc__)
        return 2

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = Path(args[0]).stem.replace(" ", "_")[:40]
    LOGDIR.mkdir(parents=True, exist_ok=True)
    logp = LOGDIR / f"CMDLOG_{ts}_{name}.log"
    cmd = (["cmd", "/c"] + args) if os.name == "nt" else args
    t0 = time.time()
    with open(logp, "a", encoding="utf-8", buffering=1) as lf:
        lf.write(f"=== via-run · {' '.join(args)} · start {ts} ===\n")
        print(f"[via-run] 留痕:{logp.name}(中斷前紀錄必存)", flush=True)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, text=True,
                                    encoding="utf-8", errors="replace")
        except Exception as exc:
            line = f"[終線] SPAWN_FAIL · {type(exc).__name__}: {exc}"
            lf.write(line + "\n")
            print(line)
            return 1
        rc = None
        try:
            for line in proc.stdout:
                line = line.rstrip("\n")
                lf.write(line + "\n")  # 先落檔(行緩衝即時)
                print(line, flush=True)
            rc = proc.wait()
        except KeyboardInterrupt:
            lf.write(f"[終線] INTERRUPTED(Ctrl+C)· 已跑 {round(time.time() - t0, 1)}s · 此前紀錄全存\n")
            lf.flush()
            proc.kill()
            proc.wait()
            print(f"\n[via-run] 已中斷——此前全部紀錄在 {logp}", flush=True)
            return 130
        secs = round(time.time() - t0, 1)
        lf.write(f"[終線] EXIT rc={rc} · {secs}s · end {datetime.now().strftime('%Y%m%d_%H%M%S')}\n")
    print(f"[via-run] rc={rc} · {secs}s · LOG:{logp.name}", flush=True)
    return rc if rc is not None else 1


if __name__ == "__main__":
    sys.exit(main())
