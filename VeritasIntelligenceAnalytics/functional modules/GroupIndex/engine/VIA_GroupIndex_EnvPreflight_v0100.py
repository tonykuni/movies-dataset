# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_GroupIndex_EnvPreflight_v0100.py

GroupIndex 環境前哨檢查——接軌 VIA 中央環境治理(VIA_EnvManager 契約):

1. 執行環境判定:目前直譯器必須位於 via_core / via_ 前綴之管理環境
   (base / 系統 Python 視為污染風險,--enforce 時 fail-closed)。
2. 工具安裝檢核:GroupIndex 套件所需套件逐一 import 驗證 + 版本盤點,
   缺件時生成指向 via_ 環境的安裝命令(不自動安裝,append-only 建議)。
3. base 純淨度稽核:可觸及時盤點 base 站台套件數與越界安裝;
   本沙盒無 Windows envs 佈局時誠實回報 AUDIT_TARGET_NOT_PRESENT。
4. EnvManager 白名單交叉比對:本套件超出 via_core 白名單之套件
   輸出「擴充白名單或專用 via_groupindex 環境」之重建計畫建議。

治理不變項:只掃描、分類、建議;零安裝、零解除安裝、零環境改寫。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import datetime as dt
import importlib
import json
import os
import re
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
RUN_OUT = MODULE_DIR / "evidence" / "RUN_ENV_PREFLIGHT_V0100"
VERSION = "0.1.00"

# —— VIA_EnvManager 契約(supportive modules/VIA_EnvManager.py)——
MANAGED_ENV_PREFIXES = ["via_"]
BASE_ENV_NAMES = {"base", "root", "python", "python3", "system", "usr", "anaconda3", "miniconda3"}
PREFERRED_ENVS = ["via_core_313", "via_core_312", "via_groupindex_312"]
WINDOWS_ENV_ROOTS = [Path(os.environ.get("USERPROFILE", "")) / "envs"] if os.environ.get("USERPROFILE") else []
VIA_CORE_WHITELIST = {
    "requests", "httpx", "aiohttp", "orjson", "numpy", "pandas", "pyarrow", "duckdb",
    "polars", "plotly", "openpyxl", "xlsxwriter", "fastapi", "uvicorn",
}

# —— GroupIndex 套件工具需求(import 名 → pip 名)——
REQUIRED_TOOLS = {
    "numpy": "numpy",
    "pandas": "pandas",
    "sklearn": "scikit-learn",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "openpyxl": "openpyxl",
    "bs4": "beautifulsoup4",
    "pytest": "pytest",
}


def def_detect_env() -> Dict[str, Any]:
    """判定目前直譯器所屬環境名稱與治理分類。"""
    venv = os.environ.get("VIRTUAL_ENV", "")
    conda = os.environ.get("CONDA_DEFAULT_ENV", "")
    prefix = Path(sys.prefix)
    name = (Path(venv).name if venv else "") or conda or prefix.name
    normalized = name.strip().lower()
    is_managed = any(normalized.startswith(p) for p in MANAGED_ENV_PREFIXES)
    is_base = (not venv and not conda and normalized in BASE_ENV_NAMES) or normalized in BASE_ENV_NAMES
    return {
        "EnvName": name,
        "SysPrefix": str(prefix),
        "PythonVersion": sys.version.split()[0],
        "PythonExe": sys.executable,
        "IsManagedVia": bool(is_managed),
        "IsViaCore": normalized.startswith("via_core"),
        "IsBaseOrSystem": bool(is_base or not (venv or conda or is_managed)),
        "Classification": (
            "VIA_MANAGED" if is_managed else
            ("BASE_OR_SYSTEM_POLLUTION_RISK" if (is_base or not (venv or conda)) else "UNMANAGED_FOREIGN_ENV")
        ),
    }


def def_check_tools() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for mod, pip_name in REQUIRED_TOOLS.items():
        try:
            m = importlib.import_module(mod)
            rows.append({"Import": mod, "PipName": pip_name, "Installed": True,
                         "Version": str(getattr(m, "__version__", "?"))})
        except ImportError:
            rows.append({"Import": mod, "PipName": pip_name, "Installed": False, "Version": ""})
    return rows


def def_discover_via_envs() -> List[Dict[str, Any]]:
    """盤點 Windows 佈局下的 via_ 管理環境(C:\\Users\\<u>\\envs\\via_*)。"""
    found: List[Dict[str, Any]] = []
    for root in WINDOWS_ENV_ROOTS:
        if not root.exists():
            continue
        for entry in sorted(root.iterdir()):
            if entry.is_dir() and entry.name.lower().startswith("via_"):
                exe = entry / "Scripts" / "python.exe"
                found.append({"EnvName": entry.name, "PythonExe": str(exe), "ExeExists": exe.exists()})
    return found


def def_audit_base_cleanliness() -> Dict[str, Any]:
    """base 純淨度:僅在可觸及 base site-packages 時盤點;否則誠實標記。"""
    if not WINDOWS_ENV_ROOTS or not WINDOWS_ENV_ROOTS[0].exists():
        return {"Status": "AUDIT_TARGET_NOT_PRESENT",
                "Detail": "非 Windows envs 佈局(沙盒/CI);base 稽核於本機執行"}
    try:
        import sysconfig
        site = Path(sysconfig.get_paths()["purelib"])
        env = def_detect_env()
        if env["IsManagedVia"]:
            return {"Status": "RUNNING_IN_MANAGED_ENV",
                    "Detail": f"目前於 {env['EnvName']},base 未被本次執行觸碰"}
        dists = [p.name for p in site.glob("*.dist-info")]
        offenders = sorted({re.split(r"-\d", d)[0].lower() for d in dists}
                           - {"pip", "setuptools", "wheel", "packaging"})
        return {"Status": "BASE_IN_USE_POLLUTION_RISK", "SitePackages": len(dists),
                "NonToolingPackages": offenders[:20],
                "Detail": "base 含非基礎套件即為未優化;建議遷移至 via_ 環境"}
    except Exception as exc:
        return {"Status": "AUDIT_ERROR", "Detail": f"{type(exc).__name__}: {exc}"}


def def_whitelist_gap() -> Dict[str, Any]:
    """GroupIndex 需求 vs via_core 白名單缺口 → EnvManager 決策建議。"""
    need = {v.lower() for v in REQUIRED_TOOLS.values()}
    gap = sorted(need - {w.lower() for w in VIA_CORE_WHITELIST})
    return {
        "ViaCoreWhitelistGap": gap,
        "Recommendation": (
            "OPTION_A: EnvManager 白名單擴充 via_core += " + ", ".join(gap) +
            " | OPTION_B: 專用環境 via_groupindex_312(EnvManager 決策後擇一,append-only)"
        ) if gap else "無缺口:全部落於 via_core 白名單",
    }


def def_run_preflight(enforce: bool) -> Dict[str, Any]:
    RUN_OUT.mkdir(parents=True, exist_ok=True)
    env = def_detect_env()
    tools = def_check_tools()
    via_envs = def_discover_via_envs()
    base_audit = def_audit_base_cleanliness()
    wl = def_whitelist_gap()

    missing = [t["PipName"] for t in tools if not t["Installed"]]
    target_exe = next((e["PythonExe"] for e in via_envs if e["ExeExists"]
                       and any(e["EnvName"].lower().startswith(p) for p in ("via_core", "via_groupindex"))),
                      "<via_core_312 python.exe>")
    install_cmd = f'"{target_exe}" -m pip install ' + " ".join(missing) if missing else ""

    env_ok = env["IsManagedVia"]
    tools_ok = not missing
    hard_fail = 0
    if enforce and not env_ok:
        hard_fail += 1
    if enforce and not tools_ok:
        hard_fail += 1

    status = (
        "ENV_PREFLIGHT_PASS" if (env_ok and tools_ok) else
        ("ENV_PREFLIGHT_BLOCKED" if enforce else "ENV_PREFLIGHT_REPORT_ONLY_NONCOMPLIANT")
    )
    report = {
        "Harness": "VIA_GroupIndex_EnvPreflight", "Version": VERSION,
        "GeneratedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "Mode": "ENFORCE" if enforce else "REPORT_ONLY",
        "Status": status, "HardFailures": hard_fail,
        "CurrentEnv": env,
        "RequiredTools": tools,
        "MissingTools": missing,
        "InstallCommand": install_cmd,
        "DiscoveredViaEnvs": via_envs,
        "BaseCleanlinessAudit": base_audit,
        "WhitelistCrossCheck": wl,
        "Policy": "scan-classify-recommend only / zero install / zero env mutation / append-only",
    }
    (RUN_OUT / "env_preflight_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="VIA GroupIndex environment preflight")
    parser.add_argument("--enforce", action="store_true",
                        help="非 via_ 管理環境或缺件時 fail-closed(本機 OneClick 預設)")
    ns = parser.parse_args(argv)
    report = def_run_preflight(enforce=ns.enforce)
    print("=" * 88)
    print(f"VIA GroupIndex Env Preflight v{VERSION} · mode={report['Mode']}")
    print("Status      :", report["Status"])
    e = report["CurrentEnv"]
    print(f"Env         : {e['EnvName']} ({e['Classification']}) · Python {e['PythonVersion']}")
    print("Exe         :", e["PythonExe"])
    ok = sum(1 for t in report["RequiredTools"] if t["Installed"])
    print(f"Tools       : {ok}/{len(report['RequiredTools'])} installed",
          ("· missing: " + ", ".join(report["MissingTools"])) if report["MissingTools"] else "")
    if report["InstallCommand"]:
        print("Install     :", report["InstallCommand"])
    print("Via envs    :", [v["EnvName"] for v in report["DiscoveredViaEnvs"]] or "none discovered (non-Windows layout)")
    print("Base audit  :", report["BaseCleanlinessAudit"]["Status"], "·", report["BaseCleanlinessAudit"].get("Detail", ""))
    print("Whitelist   :", report["WhitelistCrossCheck"]["Recommendation"][:110])
    print("=" * 88)
    return 0 if report["HardFailures"] == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
