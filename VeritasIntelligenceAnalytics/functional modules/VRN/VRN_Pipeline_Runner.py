#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_Pipeline_Runner.py — 生產管線 runner(v0100R 重建;README 載明「delegates to above」,
工作站正本候上傳到件即讓位)。

委派序(全 dry-run 預設,不動正本):
  ① SmokeTest 煙霧閘 → ② HealthCheck(--no-html --quiet)→ ③ content probe(唯讀)
  → ④ content extract(dry-run;--commit 才落盤,本 runner 不帶)
缺件/缺依賴=誠實 SKIP 列名;任一硬紅=exit 非零。
用法:python VRN_Pipeline_Runner.py [--no-pause]
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

STAGES = [
    ("SmokeTest", [sys.executable, str(HERE / "VRN_SmokeTest.py"), "--no-pause"], True),
    ("HealthCheck", [sys.executable, str(HERE / "VRN_HealthCheck.py"),
                     "--vrn-dir", str(HERE), "--no-html", "--quiet"], False),
    ("ContentProbe", [sys.executable, str(HERE / "vrn_content_probe_v0100.py")], False),
    ("ContentExtract(dry)", [sys.executable, str(HERE / "vrn_content_extract_v0101.py")], False),
]


def run():
    print("=== VRN Pipeline Runner v0100R(dry-run 全程,不動正本)===")
    n_fail = 0
    for name, cmd, hard in STAGES:
        script = Path(cmd[1])
        if not script.exists():
            print("  [SKIP] %s — %s 不在位(誠實列名)" % (name, script.name))
            continue
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            ok = r.returncode == 0
            tail = (r.stdout or r.stderr).strip().splitlines()[-1:] or [""]
            print("  [%s] %s rc=%d · %s" % ("OK  " if ok else ("FAIL" if hard else "WARN"),
                                            name, r.returncode, tail[0][:90]))
            if not ok and hard:
                n_fail += 1
        except Exception as e:
            print("  [%s] %s 例外:%s" % ("FAIL" if hard else "WARN", name, str(e)[:70]))
            if hard:
                n_fail += 1
    print("-" * 46)
    print("  Pipeline Runner:%s" % ("全綠" if n_fail == 0 else "%d 硬紅" % n_fail))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    ec = run()
    if "--no-pause" not in sys.argv:
        try:
            input("按 Enter 鍵退出...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(ec)
