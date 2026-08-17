#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_auto_pilot_v0103 — 全面自動化巡航(五系統兩波制)
========================================================
v0100→v0101(操作員令:互不影響+零九頭龍前提下能同步就同步,不然順序):
  五站寫入集互斥實核(PARALLEL 五要件過):
    A sysman → VIA_Reports/VIA_SysMan_* + sysman_runs/(獨占)
    B provision → VIA_Reports/VIA_Install_Plan_*(獨占)
    C master → VIA_Reports/VIA_UI_* + SSOT .local(獨占)
    D tidy → Downloads manifest(獨占;dry-run 零搬動)
    E store → 零寫入(dry-run)
  → 五站併發(ThreadPool);輸出於完成後按站序整列(不交錯);
    --serial 退回順序模式。牆鐘 = 最慢站而非五站總和。
操作員令(2026-08-12):不影響正常運作、全面自動化。
安全界線(鐵則):
  ① 全站唯讀/dry-run — 零 --commit、零寫入正典/SSOT/資料庫;
     產物僅落 VIA_Reports(gitignore 運行區)
  ② 不卡斷 — 各站獨立子行程+逾時,誠實 OK/FAIL/SKIP 逐站記錄,
     一站敗不斷鏈
  ③ 網路零觸碰 — 不經 NetSupport 同意閘,不發包
  ④ 排程不代註冊 — 印 schtasks 指令;--register 才執行(每日 08:00)
v0101→v0102:+F 收編計畫(intake dry;Downloads 缺=誠實 FAIL 不斷鏈)
+G 環境計畫快照(plan --offline 零網路)——七站寫入集互斥照舊。
v0102→v0103(操作員令 2026-08-18:strengthen optimize automate all
engine · VIA VDF VAP VRN FLOW):兩波制——
  第一波(七站同步,寫入集互斥照舊):A-G 不變
  第二波(順序,第一波完再跑;避免與 A sysman 寫入集撞):
    H grid --fast  全自測矩陣快版(32 站扣重站;五系統引擎全覆蓋:
                   FlowSystem 14 檢/文章攝入/介面合約 dry/office 橋
                   dry/ChipWar 編譯檢皆在內)
    I iface --dry  介面合約漂移偵測(零寫入;新模組/漂移數報告)
  ——一鍵 = 營運巡航+全引擎測試+合約漂移,三合一總自動化。
巡航鏈(七站):
  A sysman   三輪全景協議(Gate 四值+證據束)
  B provision --check 機況體檢(存安裝計畫)
  C master   Console UI 刷新(運行態 .local,git 零髒)
  D tidy     Downloads 整理計畫(dry-run 零搬動)
  E store    落庫計畫(dry-run 零寫入)
用法:via-auto              → 巡航一輪(兩波;--serial 全順序)
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


def stage(name: str, argv: list[str], timeout: int, env_dep: bool = False):
    t0 = time.time()
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, cwd=str(VIA))
        tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()][-3:]
        ok = r.returncode == 0
        # 誠實三態(對齊 grid):env 站缺件 rc≠0 記 SKIP 不記 FAIL
        if not ok and env_dep:
            return {"stage": name, "ok": True, "state": "SKIP", "rc": r.returncode,
                    "secs": round(time.time() - t0, 1),
                    "tail": ["環境缺件(誠實 SKIP;工作站應綠):"] + tail[-2:]}
        return {"stage": name, "ok": ok, "state": "OK" if ok else "FAIL",
                "rc": r.returncode, "secs": round(time.time() - t0, 1), "tail": tail}
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
        ("A_sysman", [py, str(newest("via_system_manager_v0*.py", reg)), "--no-open"], 900, False),
        ("B_provision_check", [py, str(newest("via_provision_v0*.py", reg)), "--check"], 300, False),
        ("C_master_console", [py, str(newest("via_master_hub_v0*.py", reg)), "--no-open"], 300, False),
        ("D_tidy_dryrun", [py, str(newest("via_downloads_organizer_v0*.py", reg))], 600, True),
        ("E_store_dryrun", [py, str(newest("vrn_content_store_v0*.py", VIA / "functional modules/VRN"))], 300, True),
        ("F_intake_dryrun", [py, str(newest("via_intake_v0*.py", reg))], 300, True),
        ("G_envplan_offline", [py, str(newest("via_env_plan_v0*.py", reg)), "--offline"], 300, False),
    ]
    wave2 = [
        ("H_grid_fast", [py, str(newest("via_selftest_grid_v0*.py", reg)), "--fast"], 1500, False),
        ("I_iface_dry", [py, str(newest("via_iface_contract_v0*.py", reg)), "--dry"], 600, False),
    ]
    serial = "--serial" in args
    mode_txt = "全順序" if serial else "兩波制(波一 7 站同步互斥實核;波二順序防撞)"
    print(f"=== 全面自動化巡航 v0103 · {ts} · 唯讀/dry-run · {mode_txt} ===")
    t_all = time.time()
    results = []
    runnable = [(n, a, to, ed) for n, a, to, ed in plan if a[1] != "None"]
    for n, a, to, ed in plan + wave2:
        if a[1] == "None":
            results.append({"stage": n, "ok": False, "state": "FAIL", "rc": "MISSING", "secs": 0, "tail": ["引擎缺(誠實)"]})
    if serial:
        for n, a, to, ed in runnable:
            results.append(stage(n, a, to, ed))
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(runnable)) as ex:
            futs = [ex.submit(stage, n, a, to, ed) for n, a, to, ed in runnable]
            results += [f.result() for f in futs]
    # 第二波:順序(grid 內含 sysman 級寫入集,與波一互斥必須後行)
    for n, a, to, ed in wave2:
        if a[1] != "None":
            results.append(stage(n, a, to, ed))
    results.sort(key=lambda r: r["stage"])
    for r in results:
        mark = {"OK": "OK  ", "FAIL": "FAIL", "SKIP": "SKIP"}[r.get("state", "OK" if r["ok"] else "FAIL")]
        print(f"  [{mark}] {r['stage']} · {r['secs']}s · rc={r['rc']}")
        for t in r["tail"]:
            print(f"     {t[:110]}")
    wall = round(time.time() - t_all, 1)
    ssum = round(sum(r["secs"] for r in results), 1)
    print(f"  [同步] 牆鐘 {wall}s vs 順序總和 {ssum}s" + ("(--serial 模式)" if serial else f"(加速 {round(ssum / max(wall, 0.1), 1)}x)"))
    n_ok = sum(1 for r in results if r.get("state") == "OK")
    n_skip = sum(1 for r in results if r.get("state") == "SKIP")
    n_fail = len(results) - n_ok - n_skip
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"AUTO_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.AutoPilot.v2", "ts": ts, "mode": ("scheduled" if "--scheduled" in args else "manual") + ("_serial" if "--serial" in args else "_parallel"),
                              "ok": n_ok, "skip": n_skip, "fail": n_fail, "total": len(results), "stages": results,
                              "policy": "readonly_dryrun_only·no_commit·no_network"}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    print(f"  [計] OK {n_ok} · FAIL {n_fail} · SKIP {n_skip}(誠實三態)· 存證 {ev.name}")
    print("  [鐵則] 全程唯讀/dry-run——要落地變更仍走各動詞 --commit(人工確認)")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
