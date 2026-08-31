# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_ChipWar_Revenue_Evidence_v0100.py

籌碼戰四引擎 + 月營收引擎收證執行器:

  [1] ChipWar Console  統一調度 GovFund v0.4(四世界對抗+LOEO)、
      SectorWhale v0.2(MAD 穩健 z+遲滯+週錨貝氏)、FinMind Ingest v0.1(MOCK)
      —— test→debug→optimize→consolidate→user-test→activate 全循環
  [2] 各引擎單獨執行(個別 EXIT 閘門)
  [3] 月營收引擎 twrevenue selftest(8 面向)+ demo 合成端到端
      (fetch→store(parquet+duckdb)→analyze→group→cyclical→dashboard)

治理:全部離線(MOCK/合成資料;LIVE 模式僅本機自行啟用)、
執行於暫存目錄零 repo 污染、append-only 證據 + SHA256 manifest。
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
MODULE_DIR = SCRIPT_DIR.parent
RUN_OUT = MODULE_DIR / "evidence" / "RUN_CHIPWAR_REVENUE_V0100"
REVENUE_DIR = SCRIPT_DIR / "taiwan_revenue_engine"
VERSION = "0.1.00"
TIMEOUT_SECONDS = 900

# GovFund 的 canonical 家在 ChipWar 子系統(去重:GroupIndex 不留副本,執行時取 canonical)
GOVFUND_CANONICAL = MODULE_DIR.parent / "ChipWar" / "engines" / "VIA_GovFundEngine_v040.py"
CHIPWAR_SOURCES = {
    "VIA_FinMind_Ingest_v010.py": SCRIPT_DIR / "VIA_FinMind_Ingest_v010.py",
    "VIA_SectorWhaleEngine_v020.py": SCRIPT_DIR / "VIA_SectorWhaleEngine_v020.py",
    "VIA_GovFundEngine_v040.py": GOVFUND_CANONICAL,
    "VIA_ChipWar_Console_v010.py": SCRIPT_DIR / "VIA_ChipWar_Console_v010.py",
}
PASS_TOKEN = "全數通過 EXIT=0"
CONSOLE_TOKEN = "全循環通過 EXIT=0"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_run(label: str, args: List[str], cwd: Path, token: str) -> Dict[str, Any]:
    t0 = time.time()
    sp = subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True,
                        text=True, timeout=TIMEOUT_SECONDS)
    out = (sp.stdout or "") + (sp.stderr or "")
    ok = sp.returncode == 0 and token in out
    passes = len(re.findall(r"^\s*(?:PASS|\[PASS\]|✓|✔)", out, flags=re.M))
    return {"Check": label, "ExitCode": sp.returncode, "PassLines": passes,
            "Seconds": round(time.time() - t0, 1),
            "Verdict": "PASS" if ok else "FAIL",
            "Tail": "" if ok else out.strip().splitlines()[-8:]}


def def_main() -> int:
    RUN_OUT.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []

    # 籌碼戰四引擎:於暫存目錄執行(FinMind MOCK 會落 duckdb 檔,零 repo 污染)
    with tempfile.TemporaryDirectory(prefix="via_chipwar_") as td:
        tdp = Path(td)
        for name, src in CHIPWAR_SOURCES.items():
            shutil.copy2(src, tdp / name)
        rows.append(def_run("FinMindIngest.mock", ["VIA_FinMind_Ingest_v010.py"], tdp, PASS_TOKEN))
        rows.append(def_run("SectorWhale.backtest", ["VIA_SectorWhaleEngine_v020.py"], tdp, PASS_TOKEN))
        rows.append(def_run("GovFund.fourworld", ["VIA_GovFundEngine_v040.py"], tdp, PASS_TOKEN))
        rows.append(def_run("ChipWar.console", ["VIA_ChipWar_Console_v010.py"], tdp, CONSOLE_TOKEN))

    # 月營收引擎:selftest + demo 合成端到端(於暫存副本執行,零 repo 污染)
    with tempfile.TemporaryDirectory(prefix="via_revenue_") as td:
        tdp = Path(td)
        shutil.copytree(REVENUE_DIR, tdp / "taiwan_revenue_engine")
        rcwd = tdp / "taiwan_revenue_engine"
        rows.append(def_run("Revenue.selftest", ["-m", "twrevenue.cli", "selftest"], rcwd, "全部通過"))
        rows.append(def_run("Revenue.demo_e2e", ["-m", "twrevenue.cli", "demo"], rcwd, "儀表板已產生"))

    # 第三波整合:Hybrid TW Flow(官方 TWSE/TPEX/TDCC + FinMind 混合)/ 前瞻評價 /
    # VUSIPE 語意插件 / VOFIE 全格式引擎——各自官方測試面,暫存副本執行
    sup = MODULE_DIR.parent.parent / "supportive modules"
    with tempfile.TemporaryDirectory(prefix="via_wave3_") as td:
        tdp = Path(td)
        shutil.copytree(SCRIPT_DIR / "FinMind_TW_Flow_Engine", tdp / "hybrid")
        rows.append(def_run("HybridTWFlow.unittest", ["-m", "unittest", "discover", "-s", "tests"],
                            tdp / "hybrid", "OK"))
        shutil.copy2(SCRIPT_DIR / "forward_valuation_vintage_v2.py", tdp / "forward_valuation_vintage_v2.py")
        rows.append(def_run("ForwardValuation.selftest", ["forward_valuation_vintage_v2.py", "--self-test"],
                            tdp, '"status": "pass"'))
        shutil.copytree(sup / "Veritas_Universal_Semantic_Intelligence_Plugin_Engine_v0100", tdp / "vusipe")
        rows.append(def_run("VUSIPE.pytest", ["-m", "pytest", "-q", "tests"], tdp / "vusipe", "passed"))
        shutil.copytree(sup / "Veritas_OmniFormat_Intelligence_Engine_v0140", tdp / "vofie")
        rows.append(def_run("VOFIE.pytest", ["-m", "pytest", "-q", "tests"], tdp / "vofie", "passed"))

    hard_fail = sum(1 for r in rows if r["Verdict"] != "PASS")
    status = "CHIPWAR_REVENUE_PASS" if hard_fail == 0 else "CHIPWAR_REVENUE_BLOCKED"
    summary = {
        "Harness": "VIA_ChipWar_Revenue_Evidence", "Version": VERSION,
        "GeneratedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "Status": status, "HardFailures": hard_fail,
        "Checks": rows,
        "GovernanceBoundary": (
            "ChipWar 四引擎(FinMind MOCK/大戶/官股)與月營收 twrevenue 皆為 LiveData 邊界;"
            "收證一律離線(MOCK/合成),LIVE 模式僅本機顯式啟用;暫存目錄執行零 repo 污染"
        ),
        "Dedup": {
            "robust_z": "SectorWhale MAD-z 與 GroupIndex/GlobalETFFlow robust_z 同法異參——引擎各自獨立成立,方法論已同源",
            "ssot": "SectorWhale 四族群 registry 與 GroupIndex SSOT 語意重疊(被動元件/PCB/ABF)——名冊以 GroupIndex SSOT 為 canonical,SectorWhale registry 屬引擎內部監控清單",
            "vap": "VAP v015 與 v018 規格 40/40 逐欄一致(僅版本戳),舊版免整合",
            "finmind": "Hybrid TW Flow v1.5.0(官方優先+FinMind 缺口接手)為 TW 入庫 canonical;VIA_FinMind_Ingest v0.1 保留為 ChipWar E3 MOCK 車道(Console 相依),不重複發展",
            "vusipe_dist": "VUSIPE dist/ wheel 為同源建置產物,已刪除(留 pyproject 可重建)",
            "govfund": "VIA_GovFundEngine_v040 canonical 家為 functional modules/ChipWar/engines;GroupIndex 原重複副本已刪除,收證改引 canonical(位元組級同雜湊驗證後去重)",
        },
        "SourceHashes": {n: sha256(src) for n, src in CHIPWAR_SOURCES.items()},
    }
    (RUN_OUT / "chipwar_revenue_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {p.name: sha256(p) for p in sorted(RUN_OUT.glob("*.json")) if p.name != "SHA256_MANIFEST.json"}
    (RUN_OUT / "SHA256_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 88)
    print(f"VIA ChipWar + Revenue Evidence v{VERSION}")
    print(f"{'CHECK':<26} {'PASS-LINES':>10} {'SECONDS':>8}  VERDICT")
    for r in rows:
        print(f"{r['Check']:<26} {r['PassLines']:>10} {r['Seconds']:>8}  {r['Verdict']}")
    print("Status     :", status)
    print("Run Dir    :", RUN_OUT)
    print("=" * 88)
    return 0 if hard_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(def_main())
