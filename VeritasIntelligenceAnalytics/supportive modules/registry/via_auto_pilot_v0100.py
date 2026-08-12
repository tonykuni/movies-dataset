#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_auto_pilot_v0100 — 全面自動化巡航(不影響正常運作)
========================================================
操作員令(2026-08-12):不影響正常運作、全面自動化。
安全界線(鐵則):
  ① 全站唯讀/dry-run — 零 --commit、零寫入正典/SSOT/資料庫;
     產物僅落 VIA_Reports(gitignore 運行區)
  ② 不卡斷 — 各站獨立子行程+逾時,誠實 OK/FAIL/SKIP 逐站記錄,
     一站敗不斷鏈
  ③ 網路零觸碰 — 不經 NetSupport 同意閘,不發包
  ④ 排程不代註冊 — 印 schtasks 指令;--register 才執行(每日 08:00)
巡航鏈(五站):
  A sysman   三輪全景協議(Gate 四值+證據束)
  B provision --check 機況體檢(存安裝計畫)
  C master   Console UI 刷新(運行態 .local,git 零髒)
  D tidy     Downloads 整理計畫(dry-run 零搬動)
  E store    落庫計畫(dry-run 零寫入)
用法:via-auto              → 巡航一輪
     via-auto --register   → 註冊 Windows 每日排程(08:00)
     via-auto --scheduled  → 排程模式(同巡航,靜默視窗用)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "autopilot_runs"


def newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def stage(name: str, argv: list[str], timeout: int):
    t0 = time.time()
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, cwd=str(VIA))
        tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()][-3:]
        ok = r.returncode == 0
        return {"stage": name, "ok": ok, "rc": r.returncode, "secs": round(time.time() - t0, 1),
                "tail": tail}
    except subprocess.TimeoutExpired:
        return {"stage": name, "ok": False, "rc": "TIMEOUT", "secs": round(time.time() - t0, 1),
                "tail": [f"逾時 {timeout}s(誠實 TIMEOUT,不卡斷續下一站)"]}
    except Exception as exc:
        return {"stage": name, "ok": False, "rc": type(exc).__name__, "secs": round(time.time() - t0, 1),
                "tail": [str(exc)[:100]]}


def main() -> int:
    args = sys.argv[1:]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if "--register" in args:
        cmd = str(VIA / "bin" / "via-auto.cmd")
        sch = ["schtasks", "/Create", "/F", "/SC", "DAILY", "/TN", "VIA_AutoPilot",
               "/TR", f'cmd /c "{cmd}" --scheduled', "/ST", "08:00"]
        print("=== 排程註冊(每日 08:00)===")
        print("  " + " ".join(sch))
        if sys.platform == "win32":
            r = subprocess.run(sch, capture_output=True, text=True)
            print(f"  [{'OK  ' if r.returncode == 0 else 'FAIL'}] {(r.stdout + r.stderr).strip()[:120]}")
            return r.returncode
        print("  [SKIP] 非 Windows——指令已印(工作站執行 via-auto --register)")
        return 0

    py = sys.executable
    reg = HERE
    plan = [
        ("A_sysman", [py, str(newest("via_system_manager_v0*.py", reg)), "--no-open"], 900),
        ("B_provision_check", [py, str(newest("via_provision_v0*.py", reg)), "--check"], 300),
        ("C_master_console", [py, str(newest("via_master_hub_v0*.py", reg)), "--no-open"], 300),
        ("D_tidy_dryrun", [py, str(newest("via_downloads_organizer_v0*.py", reg))], 600),
        ("E_store_dryrun", [py, str(newest("vrn_content_store_v0*.py", VIA / "functional modules/VRN"))], 300),
    ]
    print(f"=== 全面自動化巡航 v0100 · {ts} · 五站唯讀/dry-run(不影響正常運作)===")
    results = []
    for name, argv, to in plan:
        if argv[1] == "None":
            results.append({"stage": name, "ok": False, "rc": "MISSING", "secs": 0, "tail": ["引擎缺(誠實)"]})
            print(f"  [缺  ] {name}:引擎缺")
            continue
        r = stage(name, argv, to)
        results.append(r)
        mark = "OK  " if r["ok"] else "FAIL"
        print(f"  [{mark}] {name} · {r['secs']}s · rc={r['rc']}")
        for t in r["tail"]:
            print(f"     {t[:110]}")
    n_ok = sum(1 for r in results if r["ok"])
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"AUTO_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.AutoPilot.v1", "ts": ts, "mode": "scheduled" if "--scheduled" in args else "manual",
                              "ok": n_ok, "total": len(results), "stages": results,
                              "policy": "readonly_dryrun_only·no_commit·no_network"}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    print(f"  [計] {n_ok}/{len(results)} 站綠 · 存證 {ev.name}")
    print("  [鐵則] 全程唯讀/dry-run——要落地變更仍走各動詞 --commit(人工確認)")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
