#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_provision_v0100 — 首啟布建精靈 + 機況體檢(存安裝計畫)
============================================================
操作員令(2026-08-12):
  ① 首啟詢問:系統存放位置初次啟動跳出詢問,確定後依規畫布建文件夾
  ② 新機鏈:PS7 升級/libs/環境/PATH — 重用既有 FreshPC 鏈不重造
     (Bootstrap-VIA-FreshPC-v0100.cmd → Install-VIA-Product-v0101.ps1
      已含 winget PS7 自救/pip/綁機/商品組合號)
  ③ 體檢:依 VIA_EngineForge_Config 模板 + 系統需求檢「該裝的是否都裝了」,
     無衝突 base 檢核,結果存安裝計畫 JSON(誠實 OK/WARN/FAIL 不卡斷)
模式:
  via-provision              首啟精靈(互動詢問存放位置→布建;已布建則顯示現況)
  via-provision --root PATH  免互動指定存放位置布建
  via-provision --check      機況體檢 → VIA_Install_Plan_<ts>.json
  via-provision --fresh      新機引導(指路 FreshPC 鏈,不重造)
綁機:machine_hash=sha256(電腦名+平台)[:16](與 via-pack 單機綁定同族口徑)
"""
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

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CFG = VIA / "VIA_Deploy_Config.json"

# 布建骨架(依現行倉庫實際布局整理;只增不減——已在之夾誠實 SKIP)
SKELETON = [
    "functional modules/VRN/input/incoming",
    "functional modules/VRN/staging/ocr_out",
    "functional modules/VRN/SSOT/v2",
    "functional modules/VDF",
    "functional modules/VAP",
    "supportive modules/registry",
    "bin",
    "VIA_Reports",
    "VIA_Products",
]

# 系統需求(依在庫引擎實際 import 整理;OCR 層為選配誠實分級)
REQ_CORE = ["pandas", "pyarrow", "duckdb", "fitz", "requests", "jsonschema",
            "plotly", "matplotlib", "openpyxl"]
REQ_DOCX = ["docx2python", "docx"]
REQ_OCR = ["paddleocr", "paddlex"]  # 選配:掃描件救援鏈
ENV_VARS = ["FRED_API_KEY"]


def machine_hash() -> str:
    return hashlib.sha256(f"{platform.node()}|{platform.system()}".encode()).hexdigest()[:16]


def ps_version() -> str:
    for exe in ("pwsh", "powershell"):
        try:
            r = subprocess.run([exe, "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and r.stdout.strip():
                return f"{exe} {r.stdout.strip()}"
        except Exception:
            continue
    return "無(候 FreshPC 鏈)"


def check_import(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def do_provision(root: Path) -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== 首啟布建 v0100 · 存放位置 {root} ===")
    made = skipped = 0
    for rel in SKELETON:
        d = root / rel
        if d.is_dir():
            skipped += 1
        else:
            d.mkdir(parents=True, exist_ok=True)
            made += 1
            print(f"  [建  ] {rel}")
    print(f"  [夾] 新建 {made} · 已在 {skipped}(只增不減)")
    cfg = {
        "schema": "VIA.DeployConfig.v1",
        "system_root": str(root),
        "machine_hash": machine_hash(),
        "ps": ps_version(),
        "python": platform.python_version(),
        "provisioned_at": ts,
    }
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  [檔] {CFG.name} 落定(machine {cfg['machine_hash']})")
    bin_dir = VIA / "bin"
    print("  [PATH] 動詞入路徑(印令不代改;--auto 才執行):")
    print(f'     setx PATH "%PATH%;{bin_dir}"')
    if "--auto" in sys.argv and os.name == "nt":
        subprocess.run(["setx", "PATH", f"{os.environ.get('PATH', '')};{bin_dir}"], check=False)
        print("  [PATH] 已執行(新視窗生效)")
    print("  [次步] via-provision --check 機況體檢 · via-master 母版入口")
    return 0


def do_check() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=== 機況體檢 v0100(依系統需求;誠實分級)===")
    plan = {"schema": "VIA.InstallPlan.v1", "ts": ts, "machine_hash": machine_hash(),
            "stages": [], "install_commands": []}

    def stage(name, ok, note, cmd=None):
        tag = "OK  " if ok else "缺  "
        print(f"  [{tag}] {name}:{note}")
        plan["stages"].append({"stage": name, "ok": bool(ok), "note": note})
        if cmd and not ok:
            plan["install_commands"].append(cmd)

    ps = ps_version()
    ps7 = "pwsh 7" in ps or ps.startswith("pwsh")
    stage("PowerShell 7", ps7, ps, "winget install --id Microsoft.PowerShell --silent")
    stage("Python", True, platform.python_version())

    for group, names, cmd_t, req in (("核心", REQ_CORE, "py -m pip install --user {}", True),
                                     ("DOCX", REQ_DOCX, "py -m pip install --user {}", True),
                                     ("OCR(選配)", REQ_OCR, 'py -m pip install --user "paddlex[ocr]" paddleocr', False)):
        missing = [n for n in names if not check_import(n)]
        pipname = {"fitz": "PyMuPDF", "docx": "python-docx"}
        miss_pip = [pipname.get(m, m) for m in missing]
        ok = not missing
        note = f"{len(names) - len(missing)}/{len(names)} 在位" + (f" · 缺 {','.join(missing)}" if missing else "")
        stage(f"libs·{group}", ok or not req, note,
              (cmd_t.format(" ".join(miss_pip)) if "{}" in cmd_t else cmd_t) if missing else None)

    for ev in ENV_VARS:
        v = os.environ.get(ev)
        stage(f"env·{ev}", bool(v), "已設(值不印;紅線)" if v else "未設(新視窗才生效;setx 後重開)",
              f"setx {ev} <你的金鑰>")

    try:
        r = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True, timeout=120)
        clean = r.returncode == 0
        stage("pip 衝突掃描", clean, "無衝突 base" if clean else (r.stdout.strip().splitlines() or ["?"])[0][:90])
    except Exception as exc:
        stage("pip 衝突掃描", False, f"{type(exc).__name__}(誠實 WARN)")

    ef = VIA / "supportive modules/VIA_EngineForge_Config.v062.template.json"
    stage("EngineForge 模板", ef.exists(), ef.name if ef.exists() else "候上傳(graceful)")
    em = VIA / "supportive modules/VIA_EnvManager.py"
    stage("EnvManager", em.exists(),
          "在庫(深掃用 via-envmgr;重件不在體檢 eager 跑——180s 實證)" if em.exists() else "候上傳")
    canon_db = Path.home() / "OneDrive/VeritasIntelligenceAnalytics/module/VeritasDataForge/data/via.duckdb"
    stage("via.duckdb 正典", canon_db.exists(),
          f"{canon_db}" if canon_db.exists() else "未落庫(via-store --init --commit)")
    stage("Deploy 配置", CFG.exists(), CFG.name if CFG.exists() else "首啟未跑(via-provision)")

    out = VIA / "VIA_Reports" / f"VIA_Install_Plan_{ts}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n_bad = sum(1 for s in plan["stages"] if not s["ok"])
    print(f"  [計畫] {out.name} · 缺項 {n_bad}")
    if plan["install_commands"]:
        print("  [補裝令](逐行貼 PowerShell):")
        for c in plan["install_commands"]:
            print(f"     {c}")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--check" in args:
        return do_check()
    if "--fresh" in args:
        print("=== 新機引導(重用既有鏈,不重造)===")
        print("  ① 裸機一鍵:supportive modules\\registry\\Bootstrap-VIA-FreshPC-v0100.cmd <PKG指針> [基座]")
        print("     (自動:winget PS7 → Python → Install-VIA-Product-v0101.ps1 全自動布建+綁機)")
        print("  ② 已有 PS 環境:via-provision --root <存放位置> 再 via-provision --check")
        return 0
    if "--root" in args:
        return do_provision(Path(args[args.index("--root") + 1]))
    if CFG.exists():
        cfg = json.loads(CFG.read_text(encoding="utf-8"))
        print("=== 首啟精靈:已布建(冪等)===")
        for k, v in cfg.items():
            print(f"  {k}: {v}")
        print("  重布建:via-provision --root <新位置> · 體檢:via-provision --check")
        return 0
    default = str(VIA)
    if sys.stdin.isatty():
        ans = input(f"系統存放位置?[Enter=預設 {default}] > ").strip()
        return do_provision(Path(ans or default))
    print(f"[提示] 非互動環境——用 via-provision --root <位置>(預設建議 {default})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
