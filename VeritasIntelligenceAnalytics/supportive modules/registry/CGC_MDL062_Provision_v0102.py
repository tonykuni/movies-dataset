#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_provision_v0102 — 首啟布建精靈 + 機況體檢(批382 base 共用冊令版)
============================================================
v0101→v0102(批382 操作員令「BASE 應該放都用得到的工具;功能性的工具應該都放到 via_ 相關環境」):
  libs·核心改為共用基座(功能件 fitz/docx 移出);+libs·功能·docs/ocr 改於 via_ 家族境檢(via_vrn_312/via_paddle_311 等,
  境缺=候建;仍在 base=誠實標「候拉出」);+EnvGovernance 段(MDL135 RUN_latest 裁決)。
v0100→v0101:儲存不落 OneDrive——via.duckdb 正典檢改「本機 repo 樹
VDF/db」優先;OneDrive 命中誠實標示舊制候遷移(via-store --migrate)。
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
REQ_CORE = ["pandas", "numpy", "pyarrow", "duckdb", "requests", "jsonschema",
            "plotly", "matplotlib", "openpyxl", "scipy"]  # 批382:共用基座(功能件移出 base)
# 功能件於 via_ 家族境檢(批382):群 → (import 名, 候選境依序;首個在位者為準)
REQ_FUNCTIONAL = {
    "docs": (["fitz", "docx2python", "docx"], ["via_vrn_312", "via_extract_312", "via_vrn4", "via_vrn"]),
    "ocr": (["paddleocr", "paddlex"], ["via_paddle_311", "paddle_311", "via_paddle_312", "paddle_312"]),
}
ENV_ROOTS = [Path.home() / "envs", Path(r"C:\Users\tonyk\envs"), Path(r"C:\VeritasIntelligenceAnalytics\Environments")]
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
    print("=== 機況體檢 v0102(批382 base 共用冊;功能件於 via_ 境檢;誠實分級)===")
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

    missing = [n for n in REQ_CORE if not check_import(n)]
    stage("libs·核心(共用)", not missing, f"{len(REQ_CORE) - len(missing)}/{len(REQ_CORE)} 在位" + (f" · 缺 {','.join(missing)}" if missing else ""),
          ("py -m pip install --user " + " ".join(missing)) if missing else None)
    for group, (names, envs) in REQ_FUNCTIONAL.items():
        env_py = None
        for root in ENV_ROOTS:
            for e in envs:
                for sub in ("Scripts/python.exe", "bin/python"):
                    cand = root / e / sub
                    if cand.exists():
                        env_py, env_name = cand, e
                        break
                if env_py:
                    break
            if env_py:
                break
        if env_py is None:
            in_base = [n for n in names if check_import(n)]
            stage(f"libs·功能·{group}(via_)", False,
                  f"家族境缺({'/'.join(envs[:2])} 候建)" + (f" · 仍在 base:{','.join(in_base)}=候拉出(功能件不屬 base)" if in_base else " · base 亦無"),
                  f"via-envgov rename / via-envgov apply --approve(家族 {group} 建境+裝件)")
            continue
        miss = []
        for n in names:
            r = subprocess.run([str(env_py), "-c", f"import {n}"], capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                miss.append(n)
        ok = not miss
        note = f"{len(names) - len(miss)}/{len(names)} 在位於 {env_name}" + (f" · 缺 {','.join(miss)}" if miss else "")
        stage(f"libs·功能·{group}(via_)", ok, note, f"uv pip install --python \"{env_py}\" " + " ".join({"fitz": "PyMuPDF", "docx": "python-docx"}.get(m, m) for m in miss) if miss else None)

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
    gov = VIA / "VIA_Reports/env_governance/RUN_latest.json"
    try:
        g = json.loads(gov.read_text(encoding="utf-8")) if gov.exists() else {}
        stage("EnvGovernance(MDL135)", bool(g) and g.get("verdict") != "RED",
              (f"裁決 {g.get('verdict')} · 境 {len(g.get('panorama', []))} · {g.get('ts', '')[:16]}(via-envgov digest 看摘要)") if g else "尚未跑 via-envgov(唯讀全景)",
              None if g else "via-envgov")
    except Exception as exc:
        stage("EnvGovernance(MDL135)", False, f"{type(exc).__name__}(誠實 WARN)")
    local_db = VIA / "functional modules/VDF/db/via.duckdb"
    od_db = Path.home() / "OneDrive/VeritasIntelligenceAnalytics/module/VeritasDataForge/data/via.duckdb"
    if local_db.exists():
        stage("via.duckdb 正典(本機)", True, str(local_db))
    elif od_db.exists():
        stage("via.duckdb 正典(本機)", False,
              "OneDrive 舊制庫在——依令遷本機:via-store --migrate --commit", "via-store --migrate --commit")
    else:
        stage("via.duckdb 正典(本機)", False, "未落庫(via-store --init --commit)")
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
