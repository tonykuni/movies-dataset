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
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

STAGES = [
    ("SmokeTest", [sys.executable, str(HERE / "VRN_ENG028_SmokeTest.py"), "--no-pause"], True),
    ("HealthCheck", [sys.executable, str(HERE / "VRN_ENG008_HealthCheck.py"),
                     "--vrn-dir", str(HERE), "--no-html", "--quiet"], False),
    ("ContentProbe", [sys.executable, str(HERE / "VRN_ENG048_ContentProbe_v0100.py")], False),
    ("ContentExtract(dry)", [sys.executable, str(HERE / "VRN_ENG047_ContentExtract_v0101.py")], False),
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
            out_txt = (r.stdout or r.stderr).strip()
            tail = out_txt.splitlines()[-1:] or [""]
            print("  [%s] %s rc=%d · %s" % ("OK  " if ok else ("FAIL" if hard else "WARN"),
                                            name, r.returncode, tail[0][:90]))
            if not ok:
                # v0101R:紅站列明細行(遠端診斷可讀,不再只有尾行)
                for ln in out_txt.splitlines():
                    if "FAIL" in ln or "✗" in ln:
                        print("      ↳ %s" % ln.strip()[:100])
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
