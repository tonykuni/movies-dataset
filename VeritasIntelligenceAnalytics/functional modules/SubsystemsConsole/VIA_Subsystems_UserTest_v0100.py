# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_Subsystems_UserTest_v0100.py — VAP/VDF/VRN 使用者測試統包執行器

USER-TEST 情境(全離線、暫存目錄執行零 repo 污染):
  U-VAP  v025 套件測試(靜態+runtime+node core)於暫存副本全跑
  U-VDF  MDL105 CrossValidator selftest + 前瞻評價 self-test + Hybrid unittest
  U-VRN  HardGate BootPrecheck 七工具滿封(BOOT_PRECHECKED)

輸出 evidence:usertest_summary.json(+SHA256 manifest),供主控台 Builder 嵌入。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time

SCRIPT_DIR = Path(__file__).resolve().parent
FM_DIR = SCRIPT_DIR.parent
RUN_OUT = SCRIPT_DIR / "evidence" / "RUN_SUBSYSTEMS_USERTEST_V0100"
VERSION = "0.1.00"
TIMEOUT = 900


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def def_run(label: str, subsystem: str, args: List[str], cwd: Path,
            ok_fn) -> Dict[str, Any]:
    t0 = time.time()
    sp = subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True,
                        text=True, timeout=TIMEOUT)
    out = (sp.stdout or "") + (sp.stderr or "")
    ok, detail = ok_fn(sp.returncode, out)
    return {"Check": label, "Subsystem": subsystem, "ExitCode": sp.returncode,
            "Seconds": round(time.time() - t0, 1), "Detail": detail,
            "Verdict": "PASS" if ok else "FAIL",
            "Tail": "" if ok else out.strip().splitlines()[-6:]}


def def_main() -> int:
    RUN_OUT.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []

    # ---- U-VAP:v025 套件測試 ----
    with tempfile.TemporaryDirectory(prefix="via_ut_vap_") as td:
        pkg = Path(td) / "pkg"
        shutil.copytree(FM_DIR / "VAP" / "VAP_v025_Complete_Package", pkg)

        def vap_ok(rc: int, out: str):
            m = re.search(r'"passed":\s*(\d+)', out)
            n = int(m.group(1)) if m else 0
            return (rc == 0 and '"status": "PASS"' in out and n >= 17), f"{n} checks"
        rows.append(def_run("VAP.v025_package_tests", "VAP",
                            ["tests/run_all_tests_v025.py"], pkg, vap_ok))

    # ---- U-VDF:三測試面 ----
    with tempfile.TemporaryDirectory(prefix="via_ut_vdf_") as td:
        tdp = Path(td)

        def sel_ok(rc: int, out: str):
            return (rc == 0 and "Validated" in out), out.strip().splitlines()[-1][:80]
        rows.append(def_run("VDF.crossvalidator_selftest", "VDF",
                            [str(FM_DIR / "VDF" / "VDF_MDL105_CrossValidator.py"), "--selftest"],
                            tdp, sel_ok))
        shutil.copy2(FM_DIR / "VDF" / "engine" / "forward_valuation_vintage_v2.py",
                     tdp / "forward_valuation_vintage_v2.py")

        def val_ok(rc: int, out: str):
            return (rc == 0 and '"status": "pass"' in out), "vintage self-test"
        rows.append(def_run("VDF.valuation_selftest", "VDF",
                            ["forward_valuation_vintage_v2.py", "--self-test"], tdp, val_ok))
        hyb = tdp / "hybrid"
        shutil.copytree(FM_DIR / "VDF" / "FinMind_TW_Flow_Engine", hyb)

        def hy_ok(rc: int, out: str):
            m = re.search(r"Ran (\d+) tests", out)
            return (rc == 0 and out.rstrip().endswith("OK")), f"{m.group(1) if m else '?'} unittests"
        rows.append(def_run("VDF.hybrid_unittest", "VDF",
                            ["-m", "unittest", "discover", "-s", "tests"], hyb, hy_ok))

    # ---- U-VRN:HardGate 滿封 ----
    with tempfile.TemporaryDirectory(prefix="via_ut_vrn_") as td:
        def hg_ok(rc: int, out: str):
            m = re.search(r'"seal":\s*"([A-Z_]+)"', out)
            seal = m.group(1) if m else "?"
            return (rc == 0 and seal == "BOOT_PRECHECKED"), f"seal={seal}"
        rows.append(def_run("VRN.hardgate_seven_tools", "VRN",
                            [str(FM_DIR / "VRN" / "VIA_HardGate_BootPrecheck.py"), "--quiet"],
                            Path(td), hg_ok))

    hard_fail = sum(1 for r in rows if r["Verdict"] != "PASS")
    status = "SUBSYSTEMS_USERTEST_PASS" if hard_fail == 0 else "SUBSYSTEMS_USERTEST_BLOCKED"
    summary = {
        "Harness": "VIA_Subsystems_UserTest", "Version": VERSION,
        "GeneratedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "Status": status, "HardFailures": hard_fail, "Checks": rows,
        "Policy": "offline user-test / temp-dir isolation / append-only evidence",
    }
    (RUN_OUT / "usertest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {p.name: sha256(p) for p in sorted(RUN_OUT.glob("*.json"))
                if p.name != "SHA256_MANIFEST.json"}
    (RUN_OUT / "SHA256_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 80)
    print(f"VIA Subsystems USER-TEST v{VERSION}")
    for r in rows:
        print(f"  [{r['Verdict']}] {r['Check']:<32} {r['Detail']}  ({r['Seconds']}s)")
    print("Status :", status)
    print("=" * 80)
    return 0 if hard_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(def_main())
