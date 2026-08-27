# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_ETF_Consoles_Evidence_v0100.py

ETF 雙主控台收證執行器——把兩個 LiveData 邊界引擎的完整測試面跑成可稽核證據:

  [1] VIA_ActiveStockETF   --selftest(離線單元)+ mocktest(本機 HTTP mock 驅動真管線)
  [2] VIA_GlobalETFFlow    --selftest(離線單元)+ --mocktest(本機 HTTP mock 驅動真管線)

治理邊界:兩主控台屬 LiveData 邊界模組(live 模式允許對交易所/行情源收資料,
fail-closed、證據階梯 V/Der/Est/P、永不 Syn);本收證執行器一律離線執行——
mock 伺服器綁 127.0.0.1,零外部網路。輸出 append-only + SHA256 manifest。
"""
from __future__ import annotations
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

from pathlib import Path
from typing import Any, Dict, List
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time

SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
RUN_OUT = MODULE_DIR / "evidence" / "RUN_ETF_CONSOLES_V0100"
VERSION = "0.1.00"
TIMEOUT_SECONDS = 900

CHECKS = [
    {"Check": "ActiveStockETF.selftest", "Args": ["VIA_ActiveStockETF.py", "--selftest"],
     "Pattern": r"(\d+)/(\d+) PASS"},
    {"Check": "ActiveStockETF.mocktest", "Args": ["GRP_ENG002_ActiveStockETFMocktest.py"],
     "Pattern": r"(\d+)/(\d+) CHECKS PASS"},
    {"Check": "GlobalETFFlow.selftest", "Args": ["VIA_GlobalETFFlow.py", "--selftest"],
     "Pattern": r"(\d+)/(\d+) PASS"},
    {"Check": "GlobalETFFlow.mocktest", "Args": ["VIA_GlobalETFFlow.py", "--mocktest"],
     "Pattern": r"(\d+)/(\d+) CHECKS PASS"},
]
HASHED_SOURCES = ["VIA_ActiveStockETF.py", "GRP_ENG002_ActiveStockETFMocktest.py", "VIA_GlobalETFFlow.py"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_run_check(spec: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    sp = subprocess.run([sys.executable] + spec["Args"], cwd=SCRIPT_DIR,
                        capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    out = (sp.stdout or "") + (sp.stderr or "")
    m = None
    for m in re.finditer(spec["Pattern"], out):
        pass                                        # 取最後一個總結行
    passed = int(m.group(1)) if m else 0
    total = int(m.group(2)) if m else 0
    ok = sp.returncode == 0 and total > 0 and passed == total
    return {"Check": spec["Check"], "ExitCode": sp.returncode, "Passed": passed,
            "Total": total, "Seconds": round(time.time() - t0, 1),
            "Verdict": "PASS" if ok else "FAIL",
            "Tail": "" if ok else out.strip().splitlines()[-8:]}


def def_main() -> int:
    RUN_OUT.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = [def_run_check(spec) for spec in CHECKS]
    hard_fail = sum(1 for r in rows if r["Verdict"] != "PASS")
    status = "ETF_CONSOLES_PASS" if hard_fail == 0 else "ETF_CONSOLES_BLOCKED"
    summary = {
        "Harness": "VIA_ETF_Consoles_Evidence", "Version": VERSION,
        "GeneratedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "Status": status, "HardFailures": hard_fail,
        "Checks": rows,
        "GovernanceBoundary": (
            "LiveData boundary consoles: live 模式允許對官方行情源收資料(fail-closed, "
            "evidence ladder V/Der/Est/P, never Syn);本收證一律離線(mock=127.0.0.1, 零外網)"
        ),
        "SourceHashes": {n: sha256(SCRIPT_DIR / n) for n in HASHED_SOURCES},
    }
    (RUN_OUT / "etf_consoles_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {p.name: sha256(p) for p in sorted(RUN_OUT.glob("*.json")) if p.name != "SHA256_MANIFEST.json"}
    (RUN_OUT / "SHA256_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 88)
    print(f"VIA ETF Consoles Evidence v{VERSION}")
    print(f"{'CHECK':<28} {'RESULT':<10} {'SECONDS':>8}  VERDICT")
    for r in rows:
        print(f"{r['Check']:<28} {str(r['Passed']) + '/' + str(r['Total']):<10} "
              f"{r['Seconds']:>8}  {r['Verdict']}")
    print("Status     :", status)
    print("Run Dir    :", RUN_OUT)
    print("=" * 88)
    return 0 if hard_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(def_main())
