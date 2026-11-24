#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC_CommandHub_v0101.py — 薄尾(v0100 一字不動):全部指令改 Python + VCGC 既有工具當外掛 + 一支 PS 管全部

操作員 2026-11-23:「最好所指令用 PY 寫導入加速器 · VCGC 檢查所有工具及環境 衝突 安裝及遺漏」
                 「與現有 VCGC 工具大整合 PLUG-IN · 優化 GRAPHIFY OMNIROUTE AGENCY-MEM · ONE PS TO SET UP AND HANDLE ALL」

本版新增 / 改寫的指令(PS 那一支 VIA_ProfileLoader_v0104 只轉呼叫這裡,PS 端不再有邏輯):
  doctor   環境醫生。不另寫掃描器,只把 VCGC 現役工具當外掛並行跑(3 道,可 --lanes 1~6,30 秒心跳):
             CGC_MDL240 EnvManager check · CGC_MDL056 InstallGate --check-only / --doctor(零安裝)·
             CGC_MDL273 EnvToolAudit audit · CGC_MDL156 加速器控制 status · CGC_MDL186 八樞 check ·
             CGC_SystemManager connect check(Graphify · OmniRoute · Agency-mem · 備份)
           + 中樞自己的內建檢查(Python 套件 · PowerShell / Spectre / $PROFILE · 授權狀態 · 各系統入口 · 外掛尾版的加速器橋)。
           合成一張矩陣:燈 · 衝突 · 遺漏 · 安裝計畫;帶三數(應掃 / 已掃 / 略過清單)。
           寫 VIA_Reports/vcgc_hub/doctor/DOCTOR_latest.{json,txt}(txt ≤300 行、NEXT: 結尾)。唯讀,不安裝。
  install  照 doctor 的安裝計畫(或指定套件)走 VCGC 安裝閘 CGC_MDL056(不直接 pip);
           同意閘由操作員當場輸入 YES,且只放進子行程的環境,本行程與呼叫端 PS 都不留。
  auth     FRED key:遮罩輸入(getpass)→ Windows 使用者層環境變數(HKCU\\Environment);不寫檔 · 不入 git · 不印任何字元
           (只印長度與 SHA-256 前 6 碼指紋,換 key 看得出來)。--clear 移除。
  run      全線:VDF_SystemManager 尾版 launch --run → VRN_MDL260_SafeParallelLaunch 尾版 run;
           同意閘只在子行程環境開,跑完父行程從未設過 → 無需關閘;各段計時。
  setup    常態設定 $PROFILE:備份 → 寫標記區塊(try/catch;自動取 VIA_CODE_ROOT / VIA_ROOT 下最新 loader)→
           原子換檔 → 剖析 + 連 3 次新開 pwsh 載入 + -NoProfile 逃生閥,任一失敗自動還原。--check / --uninstall。
  bak      增量備份(取代 v0100 每次整份複製):size+mtime 快取 → 只對有變的檔算 SHA-256 → 只複製變動檔到 <時戳>_delta;
           Graphify 拓撲按 sha 沿用未變節點;OmniRoute 帳本只記本次真的本地解析數;agency-mem 交接記憶只增帳。
           再交給 VIA_DailyBackup 尾版 backup(zip + SHA256SUMS + MANIFEST,含各系統 Graphify / OmniRoute 收據)。
           --refresh:先叫各系統自己的入口重產圖與路由(VDF / VRN 管理器 graphify · omniroute,CGC_SystemManager omniroute)。
  plug     外掛清單:每支外掛的尾版路徑 · 有無加速器橋(語法樹)· 做什麼。
  boot / pano / ast 照 v0100;boot 多印一列「前次 doctor」。
邊界:VCGC 工具只讀各系統自報;run / bak --refresh 叫的是各系統自己的入口(它們只寫自己的夾);
      AI 不代設 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT / FRED_API_KEY;市場資料與庫內容不離機;不用 TA-Lib、不碰 MOPS。
用法:python VCGC_CommandHub_v0101.py <doctor|install|auth|run|setup|bak|plug|boot|pano|ast> … | --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import ast
import getpass
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0101"
FAMILY = "VCGC_CommandHub"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


CODE_ROOT = HERE                       # 程式樹(中樞 + loader 同夾)
DATA_ROOT = PRIOR.VIA_ROOT             # 資料根(VIA_ROOT;母系統)
HUB_DIR = PRIOR.HUB_DIR
STATE_DIR = PRIOR.STATE_DIR
DOCTOR_DIR = HUB_DIR / "doctor"
IS_WIN = os.name == "nt"

PRIOR.SHORT_COMMANDS_SPEC = [
    ("via", "主控台＋晨間快照", "前次備份 / 前次 doctor / 系統摘要;選擇題或 Enter 直接貼上", "PS 殼 → PY"),
    ("via-update", "架構快照(被動)", "啟動才更新:系統卡 · SSOT/SDD/註冊/regex/同義字矩陣 · 燈號 · 視覺鎖定 HTML", "PY 外掛取證"),
    ("via-doctor", "環境醫生", "VCGC 工具外掛並行:衝突 · 遺漏 · 加速器 · Graphify/OmniRoute/Agency-mem → 安裝計畫", "PY 外掛 ×7"),
    ("via-install", "安裝閘", "照 doctor 計畫走 CGC_MDL056 安裝閘;YES 才開同意閘(只在子行程)", "InstallGate"),
    ("via-pano", "全景檢視＋AST修復", "掃描本機 PC File,一輪安全 AST 修復(--apply --scope 才寫)", "Python AST/CST"),
    ("via-bak", "增量備份", "只備變動檔 + Graphify/OmniRoute 收據 + agency-mem;交 VIA_DailyBackup 打包", "SHA-256 增量"),
    ("via-ast", "AST 導入加速器", "剪貼簿 / --code-file / --code,diff 預覽 + 確認,可 --rollback", "AST Compile"),
    ("via-auth", "授權", "FRED key 遮罩輸入 → Windows 使用者層;不寫檔、不顯示", "PY getpass"),
    ("via-run", "全線啟動", "YES → VDF launch --run → VRN MDL260 run(同意閘只在子行程)", "各系統入口"),
    ("via-setup", "常態設定", "$PROFILE 備份 + 標記區塊 + 3 次載入檢查,失敗自動還原", "PY → pwsh"),
]

# ------------------------------------------------------------------------------
# 尾版索引(一次走樹,多根;排除退役 / 收容 / 副本 / 輸出夾)
# ------------------------------------------------------------------------------
_SKIP_DIRS = re.compile(r"(?i)^(\.git|\.venv|venv|node_modules|__pycache__|VIA_Reports|VIA_RetiredEngines|RetiredEngines|"
                        r"SCOPE_COPY|ASSETS|intake|_archive|_superseded|references|backups|vcgc_hub|via_database|"
                        r"graphify-out|private)$")
_TAIL_RX = re.compile(r"^(?P<fam>.+)_v(?P<n>\d{4})\.py$")
_INDEX: dict[str, dict[str, list[Path]]] = {}


def search_roots() -> list[Path]:
    out: list[Path] = []
    for r in (DATA_ROOT, CODE_ROOT, os.environ.get("VIA_CODE_ROOT")):
        if not r:
            continue
        p = Path(r).resolve()
        if p.is_dir() and p not in out:
            out.append(p)
    return out


def _index_root(root: Path, max_depth: int = 6) -> dict[str, list[Path]]:
    key = str(root)
    if key in _INDEX:
        return _INDEX[key]
    fams: dict[str, list[Path]] = {}
    base_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        dirnames[:] = [n for n in dirnames if not _SKIP_DIRS.match(n)] if len(d.parts) - base_depth < max_depth else []
        for fn in filenames:
            m = _TAIL_RX.match(fn)
            if m:
                fams.setdefault(m.group("fam"), []).append(d / fn)
    _INDEX[key] = fams
    return fams


def find_tail(family: str, roots: list[Path] | None = None) -> Path | None:
    """依序在各根找家族尾版;第一個有命中的根勝出(資料根優先,與 PS v0103 Find-ViaTail 同序)。"""
    for r in roots if roots is not None else search_roots():
        hits = _index_root(Path(r)).get(family)
        if hits:
            return max(hits, key=_vnum)
    return None


def tool_root(p: Path) -> Path:
    """工具所屬 VIA 根 = 含 'supportive modules' 的最近祖先;找不到回檔案所在夾。"""
    for a in p.resolve().parents:
        if (a / "supportive modules").is_dir():
            return a
    return p.parent


def has_accel_bridge(p: Path) -> bool:
    """語法樹判定:真的 import VIA_SuperAccel_Module(只有標記註解不算)。"""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] == "VIA_SuperAccel_Module" for a in n.names):
            return True
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "VIA_SuperAccel_Module":
            return True
    return False


# ------------------------------------------------------------------------------
# 外掛冊(只掛 VCGC 現役工具,不另寫掃描器)
# ------------------------------------------------------------------------------
PLUGINS = [
    {"key": "envmgr", "family": "CGC_MDL240_EnvManager", "args": ["check"], "zh": "環境總管:LIB · 執行檔 · 家族境 · 輔助工具"},
    {"key": "gate_conflict", "family": "CGC_MDL056_InstallGate", "args": ["--check-only"], "zh": "安裝閘:pip 衝突快照(零安裝)"},
    {"key": "gate_doctor", "family": "CGC_MDL056_InstallGate", "args": ["--doctor"], "zh": "安裝閘:多層 site 互撞(零安裝)"},
    {"key": "envtools", "family": "CGC_MDL273_EnvToolAudit", "args": ["audit"], "zh": "工具冊 vs 實裝:缺冊列 · 只 import 未列冊"},
    {"key": "accel", "family": "CGC_MDL156_VIAAcceleratorControl", "args": ["status"], "zh": "加速器控制:各加速器生效"},
    {"key": "envgov", "family": "CGC_MDL186_EnvGovernance_8Hub", "args": ["check"], "zh": "八樞環境治理"},
    {"key": "connect", "family": "CGC_SystemManager", "args": ["connect", "check"],
     "zh": "連線全景:Graphify · OmniRoute · Agency-mem · 備份 · MCP"},
]
ENTRY_FAMILIES = {"VDF": "VDF_SystemManager", "VRN": "VRN_SystemManager", "VRN_LAUNCH": "VRN_MDL260_SafeParallelLaunch",
                  "VCGC": "CGC_SystemManager", "BACKUP": "VIA_DailyBackup"}

_LAMP_ORDER = {"RED": 3, "YELLOW": 2, "GRAY": 1, "GREEN": 0}
_LAMP_MAP = {"RED": "RED", "FAIL": "RED", "AMBER": "YELLOW", "YELLOW": "YELLOW", "YELLOW_ABSENT": "YELLOW",
             "NODATA": "GRAY", "GRAY": "GRAY", "SKIP": "YELLOW", "GREEN": "GREEN", "PASS": "GREEN", "OK": "GREEN"}
_VERDICT_RX = [re.compile(p) for p in (
    r"總判\s+([A-Z_]+)", r"總燈\s+([A-Z_]+)", r"\[裁決\]\s*([A-Z_]+)", r'"verdict"\s*:\s*"([A-Z_]+)"',
    r"\blamp[=:]\s*([A-Z_]+)", r"^\[(PASS|FAIL)\]")]
_FIND_RX = re.compile(r"(RED|AMBER|YELLOW|FAIL|缺|衝突|互撞|找不到|未裝|沒裝|ABSENT)")


def worst(*lamps: str) -> str:
    ls = [l for l in lamps if l]
    return max(ls, key=lambda l: _LAMP_ORDER.get(l, 1)) if ls else "GRAY"


def parse_lamp(text: str, rc: int | None) -> str:
    for rx in _VERDICT_RX:
        for line in text.splitlines():
            m = rx.search(line)
            if m:
                return _LAMP_MAP.get(m.group(1).upper(), "YELLOW")
    if rc is None:
        return "GRAY"
    return "GREEN" if rc == 0 else "YELLOW"


def parse_findings(text: str, limit: int = 6) -> list[str]:
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("{") or s.startswith('"') or any(rx.search(s) for rx in _VERDICT_RX[:3]):
            continue
        if _FIND_RX.search(s) and not re.search(r"\b(GREEN|PASS)\b", s):
            out.append(re.sub(r"\s+", " ", s)[:180])
        if len(out) >= limit:
            break
    return out


def extract_plan(outputs: dict[str, str]) -> dict:
    """從外掛輸出抽:要裝的 pip 套件(走安裝閘)· 衝突 · 互撞;只照工具自己印的字,不猜。"""
    pip: list[str] = []
    conflicts: list[str] = []
    dupes: list[str] = []
    for m in re.finditer(r"via-install\s+([A-Za-z0-9_.\-\[\] ]+)", outputs.get("gate_doctor", "")):
        pip += [x for x in m.group(1).split() if re.match(r"^[A-Za-z0-9][A-Za-z0-9_.\-\[\]]*$", x)]
    m = re.search(r"缺冊列[::]\s*(.+)", outputs.get("envtools", ""))
    if m:
        pip += [x.strip() for x in m.group(1).split(",") if re.match(r"^[A-Za-z0-9][A-Za-z0-9_.\-]*$", x.strip())]
    for line in outputs.get("gate_doctor", "").splitlines():
        if "使用者層" in line and "系統層" in line:
            dupes.append(line.strip(" ·\t"))
    m = re.search(r"衝突\s*(\d+)\s*條", outputs.get("gate_conflict", ""))
    if m and int(m.group(1)) > 0:
        conflicts.append(f"pip check 衝突 {m.group(1)} 條(CGC_MDL056 --check-only)")
    return {"pip": sorted(dict.fromkeys(pip), key=str.lower), "conflicts": conflicts, "dupes": dupes}


def _child_env(extra: dict | None = None, root: Path | None = None) -> dict:
    env = dict(os.environ)
    env["VIA_FROM_VCGC"] = "YES"
    env["PYTHONIOENCODING"] = "utf-8"
    env["VIA_NO_MENU"] = "1"
    env["VIA_PANORAMA_AUTO"] = "0"        # 被動:VCGC 動作收尾不在背景起全景監控(啟動更新才更新)
    if root is not None:
        env["VIA_ROOT"] = str(root)
    env.update(extra or {})
    return env


def run_plugin(pl: dict, timeout: int = 900) -> dict:
    tail = find_tail(pl["family"])
    row = {"key": pl["key"], "zh": pl["zh"], "family": pl["family"], "tail": str(tail) if tail else None,
           "accel_ast": bool(tail and has_accel_bridge(tail))}
    if not tail:
        row.update({"lamp": "GRAY", "rc": None, "secs": 0.0, "findings": [f"找不到 {pl['family']}_v*.py(略過)"], "out": ""})
        return row
    t = time.time()
    try:
        cp = subprocess.run([sys.executable, str(tail), *pl["args"]], cwd=str(tool_root(tail)), capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=timeout,
                            env=_child_env(root=tool_root(tail)))
        out, rc = (cp.stdout or "") + (cp.stderr or ""), cp.returncode
    except subprocess.TimeoutExpired:
        out, rc = f"逾時 {timeout}s", 124
    row.update({"rc": rc, "secs": round(time.time() - t, 1), "out": out})
    row["lamp"] = worst(parse_lamp(out, rc), "YELLOW" if rc == 124 else "GREEN")
    row["findings"] = parse_findings(out)
    return row


def _pwsh() -> str | None:
    return shutil.which("pwsh") or shutil.which("pwsh.exe")


def _ps(cmd: str, profile: bool = False, timeout: int = 60, env: dict | None = None) -> tuple[int, str]:
    pw = _pwsh()
    if not pw:
        return 127, "pwsh 找不到"
    args = [pw, "-NoLogo"] + ([] if profile else ["-NoProfile"]) + ["-Command", cmd]
    try:
        cp = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=timeout, env=env or _child_env())
        return cp.returncode, ((cp.stdout or "") + (cp.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        return 124, f"逾時 {timeout}s"


# ------------------------------------------------------------------------------
# 使用者層環境變數(Windows HKCU\Environment;其他平台只讀本行程)
# ------------------------------------------------------------------------------
def user_env_get(name: str) -> str | None:
    if IS_WIN:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                return winreg.QueryValueEx(k, name)[0] or None
        except OSError:
            return None
    return None


def user_env_set(name: str, value: str | None) -> bool:
    if not IS_WIN:
        return False
    import ctypes
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
        if value is None:
            try:
                winreg.DeleteValue(k, name)
            except FileNotFoundError:
                pass
        else:
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)
    try:  # 廣播 WM_SETTINGCHANGE,新開的程式讀得到
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)
    except Exception:  # noqa: BLE001
        pass
    return True


def mask(secret: str | None) -> str:
    """不印任何 key 字元:只給長度 + SHA-256 前 6 碼指紋。"""
    if not secret:
        return "未設定"
    return f"已設定(長度 {len(secret)} · 指紋 {hashlib.sha256(secret.encode()).hexdigest()[:6]})"


def _yes(prompt: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin or not sys.stdin.isatty():
        print("[取消] 非互動環境且未帶 --yes,不執行。")
        return False
    try:
        return input(prompt).strip() == "YES"
    except EOFError:
        return False


def _rows_print(title: str, rows: list[dict], note: str = "") -> None:
    zh = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "GRAY": "灰"}
    PRIOR.print_detailed_summary_matrix(title, [
        {"category": r["category"], "metric": r["metric"], "status": zh.get(r["lamp"], r["lamp"]) + "燈"
         if r["lamp"] in zh else r["lamp"], "detail": r["detail"], "action": r.get("action", "-")} for r in rows],
        footer_note=f"VCGC Hub {VERSION}{(' | ' + note) if note else ''}")


# ------------------------------------------------------------------------------
# doctor
# ------------------------------------------------------------------------------
def builtin_checks() -> list[dict]:
    rows: list[dict] = []
    miss = [m for m in ("rich", "libcst") if importlib.util.find_spec(m) is None]
    rows.append({"category": "PY", "metric": "中樞套件 rich · libcst", "lamp": "YELLOW" if miss else "GREEN",
                 "detail": ("缺 " + ", ".join(miss) + "(無 rich 自動純文字;無 libcst pano 退回 ast)") if miss else "齊",
                 "action": "via-install " + " ".join(miss) if miss else "-", "pip": miss})
    rows.append({"category": "ACCEL", "metric": "中樞加速器橋(執行時)", "lamp": "GREEN" if VIA_ACCEL else "RED",
                 "detail": "VIA_SuperAccel_Module 已載入" if VIA_ACCEL else "載不到 VIA_SuperAccel_Module(只有標記不算)",
                 "action": "-" if VIA_ACCEL else "確認 supportive modules 在程式樹"})
    pw = _pwsh()
    if not pw:
        rows.append({"category": "PS", "metric": "PowerShell 7(pwsh)", "lamp": "GRAY" if not IS_WIN else "RED",
                     "detail": "PATH 上找不到 pwsh", "action": "winget install Microsoft.PowerShell(操作員自己裝)"})
    else:
        rc, out = _ps("$PSVersionTable.PSVersion.ToString(); if (Get-Module -ListAvailable PwshSpectreConsole) {'SPECTRE_Y'} "
                      "else {'SPECTRE_N'}; $PROFILE", timeout=60)
        lines = out.splitlines()
        ver = lines[0] if lines else "?"
        spectre = "SPECTRE_Y" in out
        prof = Path(lines[-1].strip()) if lines else None
        has_block = bool(prof and prof.is_file() and PROFILE_BEGIN in prof.read_text(encoding="utf-8-sig", errors="replace"))
        rows.append({"category": "PS", "metric": "pwsh · Spectre", "lamp": "GREEN" if spectre else "YELLOW",
                     "detail": f"pwsh {ver} · PwshSpectreConsole {'有' if spectre else '沒有(選單退回純文字)'}",
                     "action": "-" if spectre else "Install-Module PwshSpectreConsole -Scope CurrentUser(操作員)"})
        rows.append({"category": "PS", "metric": "$PROFILE 常態掛載", "lamp": "GREEN" if has_block else "YELLOW",
                     "detail": f"{prof} · {'有 VIA 區塊' if has_block else '沒有 VIA 區塊'}",
                     "action": "-" if has_block else "via-setup"})
    fred = os.environ.get("FRED_API_KEY") or user_env_get("FRED_API_KEY")
    gate_open = os.environ.get("VIA_NET_CONSENT") == "YES" or os.environ.get("VIA_SCRAPE_CONSENT") == "YES"
    rows.append({"category": "AUTH", "metric": "FRED key · 同意閘", "lamp": "YELLOW" if gate_open else ("GREEN" if fred else "GRAY"),
                 "detail": f"FRED {mask(fred)} · 同意閘 {'開著(應只在 via-run 子行程開)' if gate_open else '關'}",
                 "action": "關掉這個視窗的同意閘" if gate_open else ("-" if fred else "via-auth -Fred(可選)")})
    for sysn in ("VDF", "VRN", "VRN_LAUNCH", "VCGC", "BACKUP"):
        t = find_tail(ENTRY_FAMILIES[sysn])
        acc = has_accel_bridge(t) if t else False
        rows.append({"category": "ENTRY", "metric": f"{sysn} 入口尾版", "lamp": "GREEN" if t and acc else ("YELLOW" if t else "RED"),
                     "detail": f"{t.name} · 加速器橋 {'語法樹有' if acc else '沒有'}" if t else f"找不到 {ENTRY_FAMILIES[sysn]}_v*.py",
                     "action": "-" if t and acc else "檢查搜尋根 / VIA_CODE_ROOT"})
    db = DATA_ROOT / "via_database"
    vs = DATA_ROOT / "private" / "vrn_samples"
    rows.append({"category": "DATA", "metric": "資料根 · 庫 · VRN 樣本", "lamp": "GREEN" if db.is_dir() and vs.is_dir() else "YELLOW",
                 "detail": f"{DATA_ROOT} · via_database {'在' if db.is_dir() else '不在'} · private/vrn_samples {'在' if vs.is_dir() else '不在'}",
                 "action": "-" if db.is_dir() and vs.is_dir() else "設使用者層 VIA_ROOT 指母系統"})
    return rows


class _Heartbeat:
    def __init__(self, running: dict, every: int = 30):
        self.running, self.every, self._stop = running, every, threading.Event()
        self.t = threading.Thread(target=self._loop, daemon=True)

    def _loop(self):
        while not self._stop.wait(self.every):
            if self.running:
                print(f"[心跳] {datetime.now():%H:%M:%S} 執行中:" + " · ".join(sorted(self.running)), file=sys.stderr, flush=True)

    def __enter__(self):
        self.t.start()
        return self

    def __exit__(self, *a):
        self._stop.set()


def _settle(max_wait: int = 20) -> str:
    """啟動前先降壓:CPU 高於 85% 就等(最多 max_wait 秒);沒有 psutil 就跳過並照實說。"""
    try:
        import psutil  # type: ignore
    except Exception:  # noqa: BLE001
        return "psutil 缺 → 未量 CPU(照實)"
    t0 = time.time()
    while time.time() - t0 < max_wait:
        c = psutil.cpu_percent(interval=1.0)
        if c < 85:
            return f"CPU {c:.0f}% 已靜"
    return f"CPU 仍高,已等 {max_wait}s 照跑"


def cmd_doctor(lanes: int = 3, only: list[str] | None = None, as_json: bool = False, timeout: int = 900) -> int:
    lanes = max(1, min(6, lanes))
    DOCTOR_DIR.mkdir(parents=True, exist_ok=True)
    plugins = [p for p in PLUGINS if not only or p["key"] in only]
    log = (lambda *a: print(*a, file=sys.stderr, flush=True)) if as_json else (lambda *a: print(*a, flush=True))
    log(f"[doctor] {VERSION} · 外掛 {len(plugins)} 支 · {lanes} 道 · {_settle()}")
    results: list[dict] = []
    running: dict[str, float] = {}
    with _Heartbeat(running), ThreadPoolExecutor(max_workers=lanes) as ex:
        futs = {}
        for pl in plugins:
            running[pl["key"]] = time.time()
            futs[ex.submit(run_plugin, pl, timeout)] = pl["key"]
        for f in as_completed(futs):
            r = f.result()
            running.pop(futs[f], None)
            results.append(r)
            log(f"[完] {r['key']:<14} {r['lamp']:<6} rc {r['rc']} · {r['secs']}s")
    results.sort(key=lambda r: [p["key"] for p in PLUGINS].index(r["key"]))
    builtin = builtin_checks()
    plan = extract_plan({r["key"]: r.get("out", "") for r in results})
    plan["pip"] = sorted(dict.fromkeys(plan["pip"] + [m for b in builtin for m in b.get("pip", [])]), key=str.lower)
    skipped = [r["key"] for r in results if r["tail"] is None]
    lamp = worst(*[r["lamp"] for r in results], *[b["lamp"] for b in builtin])
    rep = {"tool": f"{FAMILY} {VERSION}", "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "lamp": lamp, "lanes": lanes, "data_root": str(DATA_ROOT), "code_root": str(CODE_ROOT),
           "counts": {"should": len(plugins), "scanned": len(plugins) - len(skipped), "skipped": skipped},
           "plugins": [{k: v for k, v in r.items() if k != "out"} for r in results], "builtin": builtin, "plan": plan}
    nxt = ("via-install(照計畫裝:" + ", ".join(plan["pip"][:8]) + (" …" if len(plan["pip"]) > 8 else "") + ")") if plan["pip"] \
        else ("看紅黃列的建議動作" if lamp in ("RED", "YELLOW") else "無")
    lines = [f"# VCGC doctor {VERSION} · {rep['at']} · 總燈 {lamp} · 應掃 {len(plugins)} · 已掃 {rep['counts']['scanned']} · "
             f"略過 {skipped or '無'}"]
    for r in results:
        lines.append(f"[{r['lamp']}] {r['key']} · {Path(r['tail']).name if r['tail'] else '—'} · rc {r['rc']} · "
                     f"{r['secs']}s · 加速器橋 {'有' if r['accel_ast'] else '無'} · {r['zh']}")
        lines += [f"    · {x}" for x in r["findings"]]
    for b in builtin:
        lines.append(f"[{b['lamp']}] {b['category']} · {b['metric']} · {b['detail']} · {b['action']}")
    lines.append(f"[計畫] pip(走安裝閘){len(plan['pip'])}:{', '.join(plan['pip']) or '無'}")
    lines.append(f"[計畫] 衝突 {len(plan['conflicts'])} · 多層互撞 {len(plan['dupes'])}(互撞只列不動,要清走 CGC_MDL135 EnvGovernance)")
    lines += [f"    · {d}" for d in plan["dupes"][:10]]
    lines = lines[:299] + [f"NEXT: {nxt}"]
    rep["next"] = nxt
    (DOCTOR_DIR / "DOCTOR_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    (DOCTOR_DIR / "DOCTOR_latest.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if as_json:
        print(json.dumps(rep, ensure_ascii=False))
        return 0 if lamp != "RED" else 1
    rows = [{"category": "PLUG", "metric": r["key"], "lamp": r["lamp"],
             "detail": f"{Path(r['tail']).name if r['tail'] else '找不到'} · rc {r['rc']} · {r['secs']}s · 加速器橋 "
                       f"{'有' if r['accel_ast'] else '無'}" + ("" if not r["findings"] else " · " + r["findings"][0]),
             "action": r["zh"]} for r in results] + builtin
    rows.append({"category": "PLAN", "metric": "安裝計畫(安裝閘)", "lamp": "YELLOW" if plan["pip"] else "GREEN",
                 "detail": ", ".join(plan["pip"]) or "無遺漏", "action": "via-install" if plan["pip"] else "-"})
    rows.append({"category": "PLAN", "metric": "衝突 · 多層互撞", "lamp": "YELLOW" if plan["conflicts"] or plan["dupes"] else "GREEN",
                 "detail": f"衝突 {len(plan['conflicts'])} · 互撞 {len(plan['dupes'])}", "action": "只列不動"})
    _rows_print(f"VCGC DOCTOR — 總燈 {lamp} · 應掃 {len(plugins)} / 已掃 {rep['counts']['scanned']} / 略過 {len(skipped)}", rows)
    print(f"[報告] {DOCTOR_DIR / 'DOCTOR_latest.txt'}\nNEXT: {nxt}")
    return 0 if lamp != "RED" else 1


def cmd_plug() -> int:
    rows = []
    for pl in PLUGINS:
        t = find_tail(pl["family"])
        rows.append({"category": "PLUG", "metric": pl["key"], "lamp": "GREEN" if t and has_accel_bridge(t) else ("YELLOW" if t else "GRAY"),
                     "detail": f"{t} {' '.join(pl['args'])}" if t else f"找不到 {pl['family']}", "action": pl["zh"]})
    for k, fam in ENTRY_FAMILIES.items():
        t = find_tail(fam)
        rows.append({"category": "ENTRY", "metric": k, "lamp": "GREEN" if t and has_accel_bridge(t) else ("YELLOW" if t else "GRAY"),
                     "detail": str(t) if t else f"找不到 {fam}", "action": "-"})
    _rows_print("VCGC HUB 外掛清單", rows, note="搜尋根 " + " | ".join(str(r) for r in search_roots()))
    return 0


# ------------------------------------------------------------------------------
# install(只走 CGC_MDL056 安裝閘;同意閘只在子行程)
# ------------------------------------------------------------------------------
_PKG_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-\[\]]*(==[A-Za-z0-9_.\-]+)?$")


def cmd_install(pkgs: list[str], assume_yes: bool = False) -> int:
    if not pkgs:
        rep = PRIOR._read_json(DOCTOR_DIR / "DOCTOR_latest.json")
        pkgs = rep.get("plan", {}).get("pip", [])
        if not rep:
            print("[install] 沒有 DOCTOR_latest.json → 先跑 via-doctor。")
            return 2
    bad = [p for p in pkgs if not _PKG_RX.match(p)]
    if bad:
        print(f"[install] 套件名不合法,拒絕(零安裝):{bad}")
        return 2
    if not pkgs:
        print("[install] 計畫是空的:沒有要裝的。")
        return 0
    gate = find_tail("CGC_MDL056_InstallGate")
    if not gate:
        print("[install] 找不到 CGC_MDL056_InstallGate 尾版 → 不裝(不直接 pip)。")
        return 2
    print(f"[install] 安裝閘 {gate.name} · 套件 {len(pkgs)}:{' '.join(pkgs)}")
    if not _yes("本次開網路同意閘(只在安裝子行程)並安裝?輸入 YES 繼續:", assume_yes):
        print("[取消] 同意閘未開,未安裝。")
        return 1
    cp = subprocess.run([sys.executable, str(gate), *pkgs], cwd=str(tool_root(gate)),
                        env=_child_env({"VIA_NET_CONSENT": "YES"}, root=tool_root(gate)))
    print(f"[install] 安裝閘 rc {cp.returncode}(同意閘只存在於子行程,本行程未設)\nNEXT: via-doctor 重驗")
    return cp.returncode


# ------------------------------------------------------------------------------
# auth
# ------------------------------------------------------------------------------
def cmd_auth(fred: bool = False, clear: bool = False) -> int:
    if clear:
        if user_env_set("FRED_API_KEY", None):
            print("[授權] FRED_API_KEY 已自 Windows 使用者層移除。")
        else:
            print("[授權] 非 Windows:沒有使用者層可清;本行程環境請自己 unset。")
    if fred:
        if not IS_WIN:
            print("[授權] 使用者層儲存只支援 Windows(HKCU\\Environment);本平台不存。")
        else:
            try:
                key = getpass.getpass("貼上 FRED API key(輸入不顯示):").strip()
            except (EOFError, KeyboardInterrupt):
                key = ""
            if not re.fullmatch(r"[0-9a-f]{32}", key):
                print("[授權] 格式不符(FRED key 應為 32 位小寫十六進位),未儲存。")
                key = ""
                return 2
            user_env_set("FRED_API_KEY", key)
            print(f"[授權] FRED_API_KEY 已存入 Windows 使用者層 · {mask(key)}(新開的程式讀得到;remote-control 要重開)")
            key = ""
    print("  授權狀態")
    print(f"  FRED_API_KEY(使用者層): {mask(user_env_get('FRED_API_KEY'))}")
    print(f"  FRED_API_KEY(本行程)  : {mask(os.environ.get('FRED_API_KEY'))}")
    print(f"  VIA_NET_CONSENT        : {'開(本行程)' if os.environ.get('VIA_NET_CONSENT') == 'YES' else '關(via-run / via-install 時只在子行程開)'}")
    return 0


# ------------------------------------------------------------------------------
# run(同意閘只在子行程環境;父行程從未設)
# ------------------------------------------------------------------------------
def cmd_run(vdf_only: bool = False, vrn_only: bool = False, vrn_source: str | None = None, via_db: str | None = None,
            assume_yes: bool = False, plan_only: bool = False, roots: list[Path] | None = None) -> int:
    vdf = find_tail(ENTRY_FAMILIES["VDF"], roots)
    vrn = find_tail(ENTRY_FAMILIES["VRN_LAUNCH"], roots)
    src = Path(vrn_source) if vrn_source else DATA_ROOT / "private" / "vrn_samples"
    db = Path(via_db) if via_db else DATA_ROOT / "via_database"
    fred = os.environ.get("FRED_API_KEY") or user_env_get("FRED_API_KEY")
    print("  全線啟動計畫")
    print(f"  搜尋根   : {' | '.join(str(r) for r in (roots or search_roots()))}")
    print(f"  VDF 入口 : {vdf or '找不到(VDF_SystemManager_v*.py)'}")
    print(f"  VRN 入口 : {vrn or '找不到(VRN_MDL260_SafeParallelLaunch_v*.py)'}")
    print(f"  VRN 報告 : {src}{'' if src.is_dir() else '(不存在)'}")
    print(f"  資料庫   : {db}{'' if db.is_dir() else '(不存在)'}")
    print(f"  FRED key : {mask(fred)}(沒有也能跑,FRED 序列照實標黃)")
    if plan_only:
        return 0
    if not _yes("本次要開網路同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT,只在子行程)並開始擷取?輸入 YES 繼續:", assume_yes):
        print("[取消] 同意閘未開,未擷取。")
        return 1
    extra = {"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}
    if fred and not os.environ.get("FRED_API_KEY"):
        extra["FRED_API_KEY"] = fred
    summary: dict[str, str] = {}
    rc_all = 0
    steps = []
    if not vrn_only:
        steps.append(("VDF launch --run", vdf, ["launch", "--run"]))
    if not vdf_only:
        steps.append(("VRN MDL260 run", vrn if src.is_dir() else None, ["run", "--source", str(src), "--via-db", str(db)]))
    for name, entry, args in steps:
        if not entry:
            summary[name] = "入口或報告夾不在,略過(黃)"
            rc_all = rc_all or 3
            continue
        t = time.time()
        cp = subprocess.run([sys.executable, str(entry), *args], cwd=str(tool_root(entry)),
                            env=_child_env(extra, root=tool_root(entry)))
        summary[name] = f"rc {cp.returncode} · {(time.time() - t) / 60:.1f} 分"
        rc_all = rc_all or cp.returncode
    extra.clear()
    print("\n  全線結果(同意閘只在子行程,本行程從未開)")
    for k, v in summary.items():
        print(f"  {k:<18} {v}")
    return rc_all


# ------------------------------------------------------------------------------
# setup($PROFILE 常態設定;Python 主控,pwsh 只做剖析 / 載入檢查)
# ------------------------------------------------------------------------------
PROFILE_BEGIN = "# >>> VIA LOADER (managed by via-setup) >>>"
PROFILE_END = "# <<< VIA LOADER <<<"


def profile_block() -> str:
    return "\n".join([
        PROFILE_BEGIN,
        "try {",
        "    if (-not $env:VIA_NO_LOADER) {",
        "        $__viaL = @([Environment]::GetEnvironmentVariable('VIA_CODE_ROOT', 'User'),",
        "                    [Environment]::GetEnvironmentVariable('VIA_ROOT', 'User'), $env:VIA_CODE_ROOT) |",
        "            Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique |",
        "            ForEach-Object { Get-ChildItem -LiteralPath $_ -Filter 'VIA_ProfileLoader_v*.ps1' -File -ErrorAction SilentlyContinue } |",
        "            Sort-Object Name | Select-Object -Last 1",
        "        if ($__viaL) { . $__viaL.FullName }",
        "    }",
        "} catch {",
        "    Write-Host \"[VIA] loader 載入失敗,已略過(PS 照常可用):$($_.Exception.Message)\" -ForegroundColor DarkYellow",
        "}",
        PROFILE_END,
    ])


def strip_block(text: str) -> str:
    return re.sub(r"(?s)\r?\n?" + re.escape(PROFILE_BEGIN) + r".*?" + re.escape(PROFILE_END) + r"\r?\n?", "\n", text)


def compose_profile(orig: str, uninstall: bool = False) -> str:
    base = strip_block(orig).rstrip()
    if uninstall:
        return base + "\n" if base else ""
    return (base + "\n\n" if base else "") + profile_block() + "\n"


def profile_path() -> Path | None:
    rc, out = _ps("$PROFILE", timeout=60)
    return Path(out.splitlines()[-1].strip()) if rc == 0 and out else None


def check_profile(prof: Path, env: dict | None = None) -> tuple[bool, list[str]]:
    ok, lines = True, []
    q = str(prof).replace("'", "''")
    rc, out = _ps(f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{q}',[ref]$null,[ref]$e); $e.Count",
                  env=env)
    if rc == 0 and out.splitlines()[-1:] == ["0"]:
        lines.append("  [OK] ① $PROFILE 語法剖析 0 錯")
    else:
        ok = False
        lines.append(f"  [FAIL] ① 剖析:{out[-200:]}")
    for i in (1, 2, 3):
        t = time.time()
        rc, out = _ps("if (Get-Command via-doctor -ErrorAction SilentlyContinue) { 'VIA_OK' } else { 'VIA_MISSING' }",
                      profile=True, env=env)
        ms = int((time.time() - t) * 1000)
        if rc == 0 and "VIA_OK" in out:
            lines.append(f"  [OK] ②-{i} 新開 pwsh 載入 profile → via 指令就緒({ms} ms,未跳選單)")
        else:
            ok = False
            flat = re.sub(r"\s+", " ", out)[-200:]
            lines.append(f"  [FAIL] ②-{i} 新開 pwsh 載入(rc {rc}):{flat}")
    rc, out = _ps("'NOPROFILE_OK'", env=env)
    if "NOPROFILE_OK" in out:
        lines.append("  [OK] ③ 逃生閥 pwsh -NoProfile 正常")
    else:
        ok = False
        lines.append("  [FAIL] ③ -NoProfile 異常")
    return ok, lines


def cmd_setup(check: bool = False, uninstall: bool = False, prof: Path | None = None) -> int:
    if not _pwsh():
        print("[setup] 找不到 pwsh(PowerShell 7)→ 先裝:winget install Microsoft.PowerShell(操作員)。")
        return 2
    loader = sorted(CODE_ROOT.glob("VIA_ProfileLoader_v*.ps1"), key=lambda p: p.name)
    if not uninstall and not loader:
        print(f"[setup] {CODE_ROOT} 下沒有 VIA_ProfileLoader_v*.ps1 → 不設定。")
        return 2
    env = _child_env({"VIA_CODE_ROOT": str(CODE_ROOT)})
    prof = prof or profile_path()
    if not prof:
        print("[setup] 讀不到 $PROFILE 路徑。")
        return 2
    if check:
        ok, lines = check_profile(prof, env)
        print("\n".join(lines))
        return 0 if ok else 1
    if not uninstall and IS_WIN:
        user_env_set("VIA_CODE_ROOT", str(CODE_ROOT))      # 非秘密:loader 所在程式樹
    prof.parent.mkdir(parents=True, exist_ok=True)
    orig = prof.read_text(encoding="utf-8-sig") if prof.is_file() else ""
    bak = prof.with_name(prof.name + f".via_backup_{datetime.now():%Y%m%d_%H%M%S}")
    bak.write_text(orig, encoding="utf-8-sig")
    tmp = prof.with_name(prof.name + f".via_tmp_{os.getpid()}")
    tmp.write_text(compose_profile(orig, uninstall), encoding="utf-8-sig")
    os.replace(tmp, prof)
    print(f"[setup] 已備份原 profile → {bak}")
    if uninstall:
        print("[setup] 已移除 VIA 區塊(其餘內容不動)。")
        return 0
    print(f"[setup] 寫入完成(loader 尾版 {loader[-1].name} · VIA_CODE_ROOT={CODE_ROOT}),開始多次檢查…")
    ok, lines = check_profile(prof, env)
    print("\n".join(lines))
    if not ok:
        prof.write_text(orig, encoding="utf-8-sig")
        print("[setup] 檢查未全過 → 已自動還原原 profile,PS 不受影響。請把 FAIL 行貼給 AI。")
        return 1
    print("[setup] ✔ 全部通過。之後每次開 pwsh 自動進 VIA;不想進:$env:VIA_NO_LOADER=1 或 pwsh -NoProfile。")
    return 0


# ------------------------------------------------------------------------------
# bak(增量)
# ------------------------------------------------------------------------------
BAK_EXTS = {".py", ".ps1", ".json", ".md", ".toml"}
MANIFEST_FILE = STATE_DIR / "bak_manifest.json"
MEM_LEDGER = STATE_DIR / "agency_mem_ledger.jsonl"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def scan_delta(root: Path, manifest: dict) -> tuple[dict, list[str], list[str], list[str], int]:
    """回 (新 manifest, 新增, 變更, 刪除, 本次真的算雜湊數)。size+mtime 沒變就沿用舊 sha。"""
    new: dict = {}
    added, changed = [], []
    hashed = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [n for n in dirnames if not _SKIP_DIRS.match(n) and n not in PRIOR._PANO_EXCLUDE]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in BAK_EXTS:
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            rel = p.relative_to(root).as_posix()
            old = manifest.get(rel)
            if old and old[0] == st.st_size and old[1] == st.st_mtime_ns:
                new[rel] = old
                continue
            sha = _sha(p)
            hashed += 1
            new[rel] = [st.st_size, st.st_mtime_ns, sha]
            if not old:
                added.append(rel)
            elif old[2] != sha:
                changed.append(rel)
    deleted = sorted(set(manifest) - set(new))
    return new, sorted(added), sorted(changed), deleted, hashed


def graph_update(root: Path, manifest: dict, touched: set[str]) -> tuple[int, int]:
    """Graphify 拓撲:未變的 .py 沿用舊節點,只重解析變動檔。回 (節點數, 本次解析數)。"""
    old = {n.get("module"): n for n in PRIOR._read_json(PRIOR.GRAPHIFY_FILE).get("nodes", [])}
    nodes, parsed = [], 0
    for rel, (_s, _m, sha) in manifest.items():
        if not rel.endswith(".py"):
            continue
        o = old.get(rel)
        if o and o.get("sha256_16") == sha[:16] and rel not in touched:
            nodes.append(o)
            continue
        try:
            tree = ast.parse((root / rel).read_text(encoding="utf-8-sig"))
            funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            imps = sorted({(a.name if isinstance(n, ast.Import) else (n.module or "")).split(".")[0]
                           for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                           for a in (n.names if isinstance(n, ast.Import) else [n])} - {""})
            nodes.append({"module": rel, "functions": funcs, "imports": imps, "sha256_16": sha[:16]})
            parsed += 1
        except (SyntaxError, ValueError, OSError, UnicodeDecodeError) as e:
            nodes.append({"module": rel, "error": type(e).__name__, "sha256_16": sha[:16]})
    return nodes, parsed


def _git_head(root: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(root), "rev-parse", "--short=9", "HEAD"], capture_output=True, text=True,
                              timeout=20).stdout.strip() or "-"
    except Exception:  # noqa: BLE001
        return "-"


def cmd_bak(note: str = "Routine Active Checkpoint", refresh: bool = False, assume_yes: bool = False,
            root: Path | None = None, daily: bool = True) -> int:
    root = (root or DATA_ROOT).resolve()
    PRIOR.ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    sub: dict[str, str] = {}
    if refresh:  # 各系統自己的入口重產圖與路由(它們只寫自己的夾)
        for label, fam, args in (("VDF graphify", "VDF_SystemManager", ["graphify"]), ("VDF omniroute", "VDF_SystemManager", ["omniroute"]),
                                 ("VRN graphify", "VRN_SystemManager", ["graphify"]), ("VRN omniroute", "VRN_SystemManager", ["omniroute"]),
                                 ("VCGC omniroute", "CGC_SystemManager", ["omniroute"])):
            t = find_tail(fam)
            if not t:
                sub[label] = "入口找不到(灰)"
                continue
            try:
                cp = subprocess.run([sys.executable, str(t), *args], cwd=str(tool_root(t)), capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=900, env=_child_env(root=tool_root(t)))
                sub[label] = f"rc {cp.returncode}"
            except subprocess.TimeoutExpired:
                sub[label] = "逾時 900s(黃)"
    manifest = PRIOR._read_json(MANIFEST_FILE).get("files", {}) if MANIFEST_FILE.is_file() else {}
    first = not manifest
    new, added, changed, deleted, hashed = scan_delta(root, manifest)
    delta = added + changed
    if first:
        mb = sum(v[0] for v in new.values()) / 1e6
        print(f"[bak] 第一次:沒有前次清單 → 要整份複製 {len(new)} 檔 · {mb:.1f} MB(之後只備變動檔)。")
        if not _yes("確定建立第一份基準備份?輸入 YES:", assume_yes):
            print("[取消] 未備份。")
            return 1
    snap = PRIOR.BACKUP_ROOT / f"{ts}_{'base' if first else 'delta'}"
    for rel in delta:
        d = snap / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, d)
    if delta or deleted:
        snap.mkdir(parents=True, exist_ok=True)
        (snap / "DELTA_MANIFEST.json").write_text(json.dumps(
            {"ts": ts, "root": str(root), "added": added, "changed": changed, "deleted": deleted,
             "sha256": {r: new[r][2] for r in delta}}, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp = MANIFEST_FILE.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps({"ts": ts, "root": str(root), "files": new}, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, MANIFEST_FILE)
    nodes, parsed = graph_update(root, new, set(delta))
    PRIOR.GRAPHIFY_FILE.write_text(json.dumps({"updated_at": ts, "node_count": len(nodes), "incremental_parsed": parsed,
                                               "nodes": nodes}, ensure_ascii=False, indent=1), encoding="utf-8")
    prev = PRIOR._read_json(PRIOR.OMNIROUTE_FILE).get("cumulative_ast_local_ops", 0)
    PRIOR.OMNIROUTE_FILE.write_text(json.dumps({"updated_at": ts, "route": "Local-AST-First -> CPU -> LLM-Minimal",
                                                "cumulative_ast_local_ops": prev + parsed, "this_run_parsed": parsed,
                                                "this_run_hashed": hashed}, ensure_ascii=False, indent=1), encoding="utf-8")
    if daily:
        db = find_tail("VIA_DailyBackup")
        if db:
            cp = subprocess.run([sys.executable, str(db), "backup"], cwd=str(tool_root(db)), capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=1800, env=_child_env(root=tool_root(db)))
            tail = [l for l in (cp.stdout or "").splitlines() if l.strip()][-1:] or ["-"]
            sub["VIA_DailyBackup backup"] = f"rc {cp.returncode} · {tail[0][:120]}"
        else:
            sub["VIA_DailyBackup backup"] = "尾版找不到(灰)"
    doc = PRIOR._read_json(DOCTOR_DIR / "DOCTOR_latest.json")
    mem = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "active_focus": note,
           "last_backup_dir": str(snap) if snap.exists() else PRIOR._read_json(PRIOR.AGENCY_MEM_FILE).get("last_backup_dir", "無"),
           "backed_up_files": len(delta), "tracked_files": len(new), "added": len(added), "changed": len(changed),
           "deleted": len(deleted), "graphify_nodes": len(nodes), "hashed_this_run": hashed, "code_git_head": _git_head(CODE_ROOT),
           "doctor_lamp": doc.get("lamp", "未跑"), "doctor_next": doc.get("next", "-"), "subtools": sub,
           "changed_top20": delta[:20]}
    PRIOR.AGENCY_MEM_FILE.write_text(json.dumps(mem, ensure_ascii=False, indent=1), encoding="utf-8")
    with MEM_LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps({k: mem[k] for k in ("timestamp", "active_focus", "backed_up_files", "added", "changed", "deleted",
                                                "doctor_lamp", "code_git_head")}, ensure_ascii=False) + "\n")
    with PRIOR.LEDGER_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts, "event": "INCREMENTAL_BACKUP", "count": len(delta), "deleted": len(deleted)}, ensure_ascii=False) + "\n")
    rows = [{"category": "SNAPSHOT", "metric": "增量備份", "lamp": "GREEN",
             "detail": f"追蹤 {len(new)} · 新增 {len(added)} · 變更 {len(changed)} · 刪除 {len(deleted)} · 本次算雜湊 {hashed}"
                       + (f" → {snap.name}" if snap.exists() else "(無變動,不建夾)"), "action": "只備變動檔"},
            {"category": "GRAPHIFY", "metric": "AST 拓撲(增量)", "lamp": "GREEN",
             "detail": f"節點 {len(nodes)} · 本次重解析 {parsed}", "action": PRIOR.GRAPHIFY_FILE.name},
            {"category": "OMNIROUTE", "metric": "本地路由帳本", "lamp": "GREEN",
             "detail": f"累計本地 AST {prev + parsed}(本次 +{parsed})", "action": "Zero-Token 優先"},
            {"category": "AGENCY-MEM", "metric": "交接記憶(只增帳)", "lamp": "GREEN",
             "detail": f"焦點 {note} · doctor {mem['doctor_lamp']} · git {mem['code_git_head']}", "action": MEM_LEDGER.name}]
    for k, v in sub.items():
        rows.append({"category": "SUBTOOL", "metric": k, "lamp": "GREEN" if v.startswith("rc 0") else "YELLOW",
                     "detail": v, "action": "各系統自己的入口"})
    _rows_print("VIA INCREMENTAL BACKUP — 增量備份 · Graphify · OmniRoute · Agency-mem", rows)
    return 0


# ------------------------------------------------------------------------------
# update(被動快照:啟動才更新 · 視覺鎖定 HTML · 清單矩陣 · 卡片 · 燈號)
# ------------------------------------------------------------------------------
ARCH_DIR = HUB_DIR / "arch"
SYSTEMS = [  # (系統, 夾, 入口家族, SSOT 全景的層名)
    ("VCGC", "supportive modules", "CGC_SystemManager", "VCGC"),
    ("VDF", "functional modules/VDF", "VDF_SystemManager", "VDF"),
    ("VRN", "functional modules/VRN", "VRN_SystemManager", "VRN"),
    ("VQG", "functional modules/VQG", "VQG_AllInOne", None),
    ("VAP", "functional modules/VAP", "VAP_SystemManager", None),
]
SSOT_FAMILY_ZH = {"REGEX": "正則 regex", "SYN": "同義字", "NUM": "自動編號", "NAME": "命名", "REG": "註冊 register",
                  "LINK": "連結"}
_PACK_RX = re.compile(r"尾版\s*(\d+)\s*·\s*未版號\s*(\d+)\s*·\s*略過\s*(\d+)")
_NUM_RX = re.compile(r"\[註冊完整性\]\s+([A-Z]+)\s+([A-Z_]+)\s+(\d+)\s+·\s+(.*)")


def norm_lamp(x: str | None) -> str:
    x = (x or "").upper()
    if x == "NODATA":
        return "NODATA"
    return _LAMP_MAP.get(x, "GRAY")


def token_tool(via: Path) -> Path | None:
    """鎖冊 token 那一支(VCGC 啟用的省 Token 工具);只取鎖冊記的檔名,在本樹 registry 找。"""
    reg = via / "supportive modules" / "registry"
    try:
        name = Path(json.loads((reg / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))["token"]["path"]).name
    except (OSError, ValueError, KeyError):
        return None
    p = reg / name
    return p if p.is_file() else None


def ui_lock(via: Path) -> dict:
    """視覺鎖定冊尾版(VIA_UI_FormatLock_v*.json);讀不到回 {} → 頁首標 UI_TOKENS=灰,文字燈,不自編色碼。"""
    hits = sorted((via / "supportive modules" / "registry").glob("VIA_UI_FormatLock_v*.json"), key=_vnum)
    for p in reversed(hits):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("tokens"):
                d["_file"] = p.name
                return d
        except (OSError, ValueError):
            continue
    return {}


def _job(cmd: list[str], cwd: Path, timeout: int) -> dict:
    t = time.time()
    try:
        cp = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=timeout, env=_child_env(root=cwd))
        return {"rc": cp.returncode, "out": (cp.stdout or "") + (cp.stderr or ""), "secs": round(time.time() - t, 1)}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "out": f"逾時 {timeout}s", "secs": round(time.time() - t, 1)}


def collect(via: Path, lanes: int = 3, timeout: int = 900, with_doctor: bool = True, log=print) -> dict:
    """叫 VCGC 現役工具取證(不另寫掃描器):SSOT 全景 · SDD · 編號稽核 · 省 Token pack(各系統夾)· doctor。"""
    V = find_tail("CGC_MDL149_VeritasCentralGovernanceConsole", [via])
    sdd = find_tail("CGC_MDL245_SDDValidator", [via])
    E = token_tool(via)
    jobs: dict[str, tuple[list[str], int]] = {}
    if V:
        jobs["ssot"] = ([sys.executable, str(V), "ssot", "panorama"], timeout)
        jobs["num"] = ([sys.executable, str(V), "run", "CGC_MDL237_NumberingSystem", "audit"], timeout)
    if sdd:
        jobs["sdd"] = ([sys.executable, str(sdd)], timeout)
    if E:
        for sysn, folder, _f, _l in SYSTEMS:
            if (via / folder).is_dir():
                jobs[f"pack:{sysn}"] = ([sys.executable, str(E), "pack", str(via / folder), "--limit", "1"], 300)
    if E and DATA_ROOT.resolve() != via.resolve() and DATA_ROOT.is_dir():   # 資料根(母系統)另成一張卡
        jobs["pack:DATA"] = ([sys.executable, str(E), "pack", str(DATA_ROOT), "--limit", "1"], 300)
    if with_doctor:
        jobs["doctor"] = ([sys.executable, str(Path(__file__).resolve()), "doctor", "--json", "--lanes", "2"], timeout + 300)
    should = ["ssot", "num", "sdd", "doctor"] + [f"pack:{s[0]}" for s in SYSTEMS]
    if "pack:DATA" in jobs:
        should.append("pack:DATA")
    if not with_doctor:
        should.remove("doctor")
    res: dict[str, dict] = {}
    running: dict[str, float] = {}
    log(f"[update] 取證 {len(jobs)} 項 · {max(1, min(6, lanes))} 道 · {_settle()}")
    with _Heartbeat(running), ThreadPoolExecutor(max_workers=max(1, min(6, lanes))) as ex:
        futs = {}
        for k, (cmd, to) in jobs.items():
            running[k] = time.time()
            futs[ex.submit(_job, cmd, via, to)] = k
        for f in as_completed(futs):
            k = futs[f]
            running.pop(k, None)
            res[k] = f.result()
            log(f"[完] {k:<12} rc {res[k]['rc']} · {res[k]['secs']}s")
    skipped = [k for k in should if k not in jobs]
    return {"res": res, "should": should, "skipped": skipped, "tools": {"console": V.name if V else None,
            "sdd": sdd.name if sdd else None, "token": E.name if E else None}}


def build_arch(via: Path, col: dict, prev: dict | None = None) -> dict:
    res = col["res"]
    rd = PRIOR._read_json
    ssot = rd(via / "VIA_Reports" / "ssot_panorama" / "SSOT_PANORAMA_latest.json") if "ssot" in res else {}
    sddj = rd(via / "VIA_Reports" / "sdd" / "SDD_CHECK_latest.json") if "sdd" in res else {}
    probe = rd(via / "VIA_Reports" / "toolprobe" / "TOOLPROBE_latest.json")
    doctor = {}
    if "doctor" in res:
        try:
            doctor = json.loads([l for l in res["doctor"]["out"].splitlines() if l.startswith("{")][-1])
        except (IndexError, ValueError):
            doctor = rd(DOCTOR_DIR / "DOCTOR_latest.json")
    cells = {(c.get("family"), c.get("layer")): c for c in ssot.get("cells", [])}
    layers = ssot.get("layers", ["VCGC", "VDF", "VRN", "SUP"])
    ssot_rows = []
    for fam, zh in SSOT_FAMILY_ZH.items():
        row = {"family": fam, "zh": zh, "lamp": norm_lamp(ssot.get("families", {}).get(fam)) if ssot else "GRAY", "cells": {}}
        for lay in layers:
            c = cells.get((fam, lay))
            row["cells"][lay] = {"lamp": norm_lamp(c.get("state")) if c else "GRAY",
                                 "detail": (c or {}).get("detail", "—(此層無此族)")[:400], "next": (c or {}).get("next", ""),
                                 "owner": (c or {}).get("owner", "")}
        ssot_rows.append(row)
    sdd_rows = [{"lamp": norm_lamp(r.get("lamp")) if r.get("lamp") != "INFO" else "GREEN", "rule": r.get("rule", ""),
                 "msg": r.get("msg", "")[:400], "ref": r.get("ref", "")} for r in sddj.get("rows", [])]
    num_rows = []
    for line in res.get("num", {}).get("out", "").splitlines():
        m = _NUM_RX.search(line)
        if m:
            num_rows.append({"lamp": norm_lamp(m.group(1)), "key": m.group(2), "n": int(m.group(3)), "msg": m.group(4)[:300]})
    cards = []
    for sysn, folder, fam, layer in SYSTEMS:
        tail = find_tail(fam, [via])
        acc = bool(tail and has_accel_bridge(tail))
        m = _PACK_RX.search(res.get(f"pack:{sysn}", {}).get("out", ""))
        pack = {"tails": int(m.group(1)), "unversioned": int(m.group(2)), "skipped": int(m.group(3))} if m else None
        lay = "SUP" if sysn == "VCGC" and layer is None else layer
        ss = {f: cells.get((f, lay), {}).get("state") for f in SSOT_FAMILY_ZH} if lay else {}
        lamp = worst("GREEN" if tail and acc else ("YELLOW" if tail else "RED"),
                     *[norm_lamp(v) for v in ss.values() if v], "GREEN" if pack else "GRAY")
        cards.append({"system": sysn, "folder": folder, "entry": tail.name if tail else None, "accel": acc, "pack": pack,
                      "ssot": {k: norm_lamp(v) for k, v in ss.items() if v}, "lamp": lamp})
    if "pack:DATA" in res:
        m = _PACK_RX.search(res["pack:DATA"]["out"])
        db = DATA_ROOT / "via_database"
        cards.append({"system": "資料根", "folder": str(DATA_ROOT), "entry": f"via_database {'在' if db.is_dir() else '不在'}",
                      "accel": None, "pack": {"tails": int(m.group(1)), "unversioned": int(m.group(2)), "skipped": int(m.group(3))}
                      if m else None, "ssot": {}, "lamp": "GREEN" if m and db.is_dir() else "YELLOW"})
    gov = [
        {"name": "SSOT 全景", "lamp": norm_lamp(ssot.get("verdict")) if ssot else "GRAY",
         "detail": " · ".join(f"{SSOT_FAMILY_ZH[k]} {norm_lamp(v)}" for k, v in ssot.get("families", {}).items() if k in SSOT_FAMILY_ZH)
         or "沒跑到", "src": "CGC_MDL247 SSOTPanorama"},
        {"name": "SDD 驗證", "lamp": norm_lamp(sddj.get("lamp")) if sddj else "GRAY",
         "detail": f"工作流 {sddj.get('workflows', '?')} · 步 {sddj.get('steps', '?')} · 需求 {sddj.get('requirements', '?')}"
                   if sddj else "沒跑到", "src": "CGC_MDL245 SDDValidator"},
        {"name": "編號 · 註冊", "lamp": worst(*[r["lamp"] for r in num_rows]) if num_rows else "GRAY",
         "detail": " · ".join(f"{r['key']} {r['n']}" for r in num_rows[:8]) or "沒跑到", "src": "CGC_MDL237 NumberingSystem audit"},
        {"name": "環境 · 工具", "lamp": norm_lamp(doctor.get("lamp")) if doctor else "GRAY",
         "detail": f"外掛 {doctor.get('counts', {}).get('scanned', '?')}/{doctor.get('counts', {}).get('should', '?')} · "
                   f"待裝 {len(doctor.get('plan', {}).get('pip', []))}" if doctor else "沒跑到", "src": f"{FAMILY} doctor"},
        {"name": "加速器 · 網路橋", "lamp": norm_lamp(probe.get("verdict")) if probe else "GRAY",
         "detail": next((k[2] for k in probe.get("kpi", []) if "覆蓋" in str(k[0])), "沒有 TOOLPROBE(doctor 會產)")[:300]
         if probe else "沒有 TOOLPROBE", "src": "CGC_MDL230 ToolCoverageProbe"},
    ]
    nxt = []
    for r in ssot_rows:
        for lay, c in r["cells"].items():
            if c["lamp"] in ("RED", "YELLOW") and c["next"]:
                nxt.append({"lamp": c["lamp"], "area": f"SSOT {r['zh']} @ {lay}", "next": c["next"][:240], "owner": c["owner"]})
    nxt += [{"lamp": r["lamp"], "area": f"SDD {r['rule']}", "next": r["msg"][:240], "owner": "CGC_MDL245"}
            for r in sdd_rows if r["lamp"] in ("RED", "YELLOW")]
    nxt += [{"lamp": r["lamp"], "area": f"編號 {r['key']}", "next": r["msg"][:240], "owner": "CGC_MDL237"}
            for r in num_rows if r["lamp"] in ("RED", "YELLOW")]
    nxt += [{"lamp": norm_lamp(t[0]), "area": f"工具 {t[1]} · {t[2]}", "next": f"{t[3]} → {t[4]}"[:240], "owner": "CGC_MDL230"}
            for t in probe.get("todo", []) if len(t) >= 5 and norm_lamp(t[0]) in ("RED", "YELLOW")]
    nxt += [{"lamp": b["lamp"], "area": f"環境 {b['category']} {b['metric']}", "next": b["action"], "owner": "doctor"}
            for b in doctor.get("builtin", []) if b.get("lamp") in ("RED", "YELLOW")]
    nxt.sort(key=lambda x: -_LAMP_ORDER.get(x["lamp"], 1))
    lamp = worst(*[c["lamp"] for c in cards], *[g["lamp"] for g in gov])
    sources = [{"key": k, "rc": v["rc"], "secs": v["secs"],
                "lamp": "GREEN" if v["rc"] == 0 else ("GRAY" if v["rc"] is None else "YELLOW")} for k, v in sorted(res.items())]
    snap = {"tool": f"{FAMILY} {VERSION}", "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mode": "被動快照(啟動 update 才更新;不在背景監控)", "via_root": str(via), "lamp": lamp,
            "counts": {"should": len(col["should"]), "scanned": len(col["should"]) - len(col["skipped"]), "skipped": col["skipped"]},
            "tools": col["tools"], "sources": sources, "cards": cards, "governance": gov, "ssot_layers": layers,
            "ssot": ssot_rows, "sdd": sdd_rows, "numbering": num_rows,
            "doctor": {"plugins": doctor.get("plugins", []), "plan": doctor.get("plan", {})}, "next": nxt[:40]}
    snap["delta"] = diff_snap(prev or {}, snap)
    return snap


def _lamp_index(s: dict) -> dict:
    out = {f"卡 {c['system']}": c["lamp"] for c in s.get("cards", [])}
    out.update({f"治理 {g['name']}": g["lamp"] for g in s.get("governance", [])})
    for r in s.get("ssot", []):
        out.update({f"SSOT {r['zh']} @ {k}": v["lamp"] for k, v in r.get("cells", {}).items()})
    out.update({f"SDD {r['rule']}": r["lamp"] for r in s.get("sdd", [])})
    out.update({f"編號 {r['key']}": r["lamp"] for r in s.get("numbering", [])})
    return out


def diff_snap(prev: dict, cur: dict) -> list[dict]:
    """跟上一份快照比:燈變了才列(變好 / 變差 / 新出現 / 不見)。成功只增不減 → 由綠變差、綠項不見 = 紅標。"""
    a, b = _lamp_index(prev), _lamp_index(cur)
    out = []
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if x == y:
            continue
        kind = "新出現" if x is None else "不見" if y is None else ("變好" if _LAMP_ORDER.get(y, 1) < _LAMP_ORDER.get(x, 1) else "變差")
        out.append({"item": k, "from": x, "to": y, "kind": kind, "regress": x == "GREEN" and kind in ("變差", "不見")})
    return out


def render_html(s: dict, lock: dict) -> str:
    import html as H
    e = lambda v: H.escape(str(v), quote=True)  # noqa: E731
    tk = lock.get("tokens", {})
    have = bool(tk)

    def lamp(l: str) -> str:
        l = l if l in ("GREEN", "YELLOW", "RED", "GRAY", "NODATA") else "GRAY"
        zh = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "GRAY": "灰", "NODATA": "無資料"}[l]
        return f'<span class="lamp {l}" title="{l}"></span>{zh}' if have else f"[{zh}]"

    css = ""
    if have:
        css = (f":root{{--pw:{tk['panel_w_px']}px;--hh:{tk['header_h_px']}px;--bg:{tk['color_bg']};--pbg:{tk['color_panel_bg']};"
               f"--bd:{tk['color_border']};--grid:{tk['color_grid']};--alert:{tk['alert_bg']};--tx:{tk['text']};--ac:{tk['accent']};"
               f"--act:{tk['accent_text']};--ok:{tk['status_OK']};--fail:{tk['status_FAIL']};--skip:{tk['status_SKIP']};"
               f"--unt:{tk['status_UNTESTED']}}}"
               f"body{{margin:0;font-family:{tk['font_family']};font-size:{tk['font_pc_px']}px;background:var(--bg);color:var(--tx)}}"
               "header{height:var(--hh);display:flex;align-items:center;gap:12px;padding:0 10px;background:var(--ac);color:var(--act);"
               "position:sticky;top:0;z-index:2}header b{font-size:1.2em}"
               ".wrap{display:flex;align-items:flex-start}"
               "aside{width:var(--pw);flex:0 0 var(--pw);background:var(--pbg);border-right:1px solid var(--bd);padding:8px;box-sizing:border-box;"
               "position:sticky;top:var(--hh);max-height:calc(100vh - var(--hh));overflow:auto;overflow-wrap:anywhere}"
               "main{flex:1;min-width:0;padding:8px}"
               "table{border-collapse:collapse;width:100%;margin:4px 0 10px}th,td{border:1px solid var(--grid);padding:3px 5px;"
               "vertical-align:top;text-align:left;overflow-wrap:anywhere}th{background:var(--pbg)}"
               ".cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:6px;margin-bottom:10px}"
               ".card{border:1px solid var(--bd);background:var(--bg);padding:6px;border-radius:4px}.card h3{margin:0 0 4px;font-size:1.15em}"
               ".muted{color:var(--unt)}.alert{background:var(--alert);border:1px solid var(--bd);padding:5px;margin:6px 0}"
               ".reg{color:var(--fail);font-weight:bold}details{margin-bottom:6px}summary{cursor:pointer;font-weight:bold;padding:3px 0}"
               f"@media (max-width:{tk['breakpoint_px']}px){{.wrap{{display:block}}aside{{width:auto;position:static;max-height:none}}"
               "header{height:auto;min-height:var(--hh);flex-wrap:wrap;position:static}"
               f"body{{font-size:{tk['font_mobile_px']}px}}}}" + lock.get("lamp_css", ""))
    c = s["counts"]
    out = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
           f"<title>VIA 系統架構</title><style>{css}</style></head><body>",
           f"<header><b>VIA 系統架構全景</b><span>{lamp(s['lamp'])}</span><span>快照 {e(s['at'])} UTC</span>"
           f"<span>{e(s['mode'])}</span>{'' if have else '<span>UI_TOKENS=灰</span>'}</header><div class='wrap'><aside>",
           f"<div><b>取證三數</b><br>應掃 {c['should']} · 已掃 {c['scanned']} · 略過 {e(c['skipped'] or '無')}</div>",
           f"<div class='muted'>根 {e(s['via_root'])}<br>主控台 {e(s['tools'].get('console'))}<br>SDD {e(s['tools'].get('sdd'))}"
           f"<br>省 Token {e(s['tools'].get('token'))}<br>視覺鎖 {e(lock.get('_file', '缺'))}</div><table><tr><th>來源</th><th>燈</th><th>rc</th><th>秒</th></tr>"]
    out += [f"<tr><td>{e(x['key'])}</td><td>{lamp(x['lamp'])}</td><td>{e(x['rc'])}</td><td>{e(x['secs'])}</td></tr>" for x in s["sources"]]
    out.append("</table><div class='alert'>本頁不會自己更新。要更新:<br><code>via-update</code></div></aside><main>")
    reg = [d for d in s["delta"] if d["regress"]]
    if reg:
        out.append("<div class='alert reg'>成功退步 " + str(len(reg)) + " 項:" + " · ".join(e(d["item"]) for d in reg[:12]) + "</div>")
    out.append("<div class='cards'>")
    for cd in s["cards"]:
        pk = cd["pack"] or {}
        ss = " ".join(f"{e(SSOT_FAMILY_ZH.get(k, k))} {lamp(v)}" for k, v in cd["ssot"].items())
        out.append(f"<div class='card'><h3>{lamp(cd['lamp'])} {e(cd['system'])}</h3><div>入口 {e(cd['entry'] or '找不到')}</div>"
                   f"<div>加速器橋 {'—(資料夾)' if cd['accel'] is None else '語法樹有' if cd['accel'] else '沒有'}</div>"
                   f"<div>尾版 {e(pk.get('tails', '?'))} · 未版號 {e(pk.get('unversioned', '?'))} · 略過 {e(pk.get('skipped', '?'))}</div>"
                   f"<div class='muted'>{ss or 'SSOT 全景無此層'}</div></div>")
    for g in s["governance"]:
        out.append(f"<div class='card'><h3>{lamp(g['lamp'])} {e(g['name'])}</h3><div>{e(g['detail'])}</div>"
                   f"<div class='muted'>{e(g['src'])}</div></div>")
    out.append("</div><details open><summary>SSOT 矩陣:正則 regex · 同義字 · 編號 · 命名 · 註冊 · 連結 × 系統層</summary><table><tr><th>族</th><th>總</th>")
    out += [f"<th>{e(l)}</th>" for l in s["ssot_layers"]] + ["</tr>"]
    for r in s["ssot"]:
        out.append(f"<tr><td>{e(r['zh'])}</td><td>{lamp(r['lamp'])}</td>" + "".join(
            f"<td title='{e(v['detail'])}'>{lamp(v['lamp'])}<div class='muted'>{e(v['detail'][:120])}</div></td>"
            for v in r["cells"].values()) + "</tr>")
    out.append("</table></details><details open><summary>SDD 驗證</summary><table><tr><th>燈</th><th>規則</th><th>說明</th></tr>")
    out += [f"<tr><td>{lamp(r['lamp'])}</td><td>{e(r['rule'])}</td><td>{e(r['msg'])}</td></tr>" for r in s["sdd"]]
    out.append("</table></details><details open><summary>編號 · 註冊完整性(CGC_MDL237 audit)</summary><table><tr><th>燈</th><th>項</th><th>數</th><th>說明</th></tr>")
    out += [f"<tr><td>{lamp(r['lamp'])}</td><td>{e(r['key'])}</td><td>{r['n']}</td><td>{e(r['msg'])}</td></tr>" for r in s["numbering"]]
    out.append("</table></details><details><summary>環境 · 工具外掛(doctor)</summary><table><tr><th>燈</th><th>外掛</th><th>尾版</th><th>rc</th><th>加速器橋</th><th>發現</th></tr>")
    for p in s["doctor"]["plugins"]:
        out.append(f"<tr><td>{lamp(p.get('lamp', 'GRAY'))}</td><td>{e(p.get('key'))}</td><td>{e(Path(p['tail']).name if p.get('tail') else '—')}</td>"
                   f"<td>{e(p.get('rc'))}</td><td>{'有' if p.get('accel_ast') else '無'}</td><td>{e(' · '.join(p.get('findings', [])[:3]))}</td></tr>")
    pl = s["doctor"]["plan"]
    out.append(f"</table><div>安裝計畫(走安裝閘):{e(', '.join(pl.get('pip', [])) or '無')}</div></details>")
    out.append("<details open><summary>整合待辦(由現況證據排序;紅先)</summary><table><tr><th>燈</th><th>範圍</th><th>下一步</th><th>正主</th></tr>")
    out += [f"<tr><td>{lamp(n['lamp'])}</td><td>{e(n['area'])}</td><td>{e(n['next'])}</td><td>{e(n['owner'])}</td></tr>" for n in s["next"]]
    out.append("</table></details><details><summary>跟上一份快照比(燈有變才列)</summary><table><tr><th>項</th><th>前</th><th>後</th><th>變化</th></tr>")
    out += [f"<tr class='{'reg' if d['regress'] else ''}'><td>{e(d['item'])}</td><td>{e(d['from'])}</td><td>{e(d['to'])}</td><td>{e(d['kind'])}</td></tr>"
            for d in s["delta"]] or ["<tr><td colspan='4'>第一次快照或沒有變化</td></tr>"]
    out.append("</table></details></main></div></body></html>")
    return "".join(out)


def snap_txt(s: dict) -> str:
    c = s["counts"]
    lines = [f"# VIA 架構快照 {s['at']} · 總燈 {s['lamp']} · 應掃 {c['should']} · 已掃 {c['scanned']} · 略過 {c['skipped'] or '無'}"]
    lines += [f"[{cd['lamp']}] {cd['system']} · 入口 {cd['entry']} · 加速器橋 {'—' if cd['accel'] is None else '有' if cd['accel'] else '無'} · pack {cd['pack']}"
              for cd in s["cards"]]
    lines += [f"[{g['lamp']}] {g['name']} · {g['detail']}" for g in s["governance"]]
    lines += [f"[{r['lamp']}] SSOT {r['zh']} · " + " ".join(f"{k}={v['lamp']}" for k, v in r["cells"].items()) for r in s["ssot"]]
    lines += [f"[{d['to'] or '-'}] 變化 {d['item']}:{d['from']} → {d['to']}{' · 退步' if d['regress'] else ''}" for d in s["delta"][:40]]
    lines += [f"[{n['lamp']}] 待辦 {n['area']} → {n['next']}" for n in s["next"][:60]]
    nxt = s["next"][0]["area"] + " → " + s["next"][0]["next"] if s["next"] else "無"
    return "\n".join(lines[:299] + [f"NEXT: {nxt}"]) + "\n"


def cmd_update(lanes: int = 3, with_doctor: bool = True, open_page: bool = True, via: Path | None = None) -> int:
    via = (via or DATA_ROOT).resolve()
    if not (via / "supportive modules").is_dir():
        alt = [r for r in search_roots() if (r / "supportive modules").is_dir()]
        print(f"[update] {via} 沒有 supportive modules(不是 VIA 程式樹)" + (f" → 改用 {alt[0]}" if alt else ""))
        if not alt:
            return 2
        via = alt[0]
    ARCH_DIR.mkdir(parents=True, exist_ok=True)
    prev = PRIOR._read_json(ARCH_DIR / "ARCH_latest.json")
    col = collect(via, lanes=lanes, with_doctor=with_doctor)
    snap = build_arch(via, col, prev)
    lock = ui_lock(via)
    page = render_html(snap, lock)
    for name, body in (("ARCH_latest.json", json.dumps(snap, ensure_ascii=False, indent=1)), ("ARCH_latest.html", page),
                       ("ARCH_latest.txt", snap_txt(snap))):
        tmp = ARCH_DIR / f".{name}.{os.getpid()}.tmp"
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, ARCH_DIR / name)
    with (ARCH_DIR / "ARCH_history.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": snap["at"], "lamp": snap["lamp"], "counts": snap["counts"],
                            "regress": [d["item"] for d in snap["delta"] if d["regress"]]}, ensure_ascii=False) + "\n")
    rows = [{"category": "CARD", "metric": cd["system"], "lamp": cd["lamp"],
             "detail": f"{cd['entry'] or '入口找不到'} · 加速器橋 {'—' if cd['accel'] is None else '有' if cd['accel'] else '無'} · "
                       f"尾版 {(cd['pack'] or {}).get('tails', '?')}", "action": cd["folder"]} for cd in snap["cards"]]
    rows += [{"category": "GOV", "metric": g["name"], "lamp": g["lamp"], "detail": g["detail"], "action": g["src"]} for g in snap["governance"]]
    reg = [d for d in snap["delta"] if d["regress"]]
    rows.append({"category": "DELTA", "metric": "跟上一份比", "lamp": "RED" if reg else "GREEN",
                 "detail": f"變化 {len(snap['delta'])} · 退步 {len(reg)}" + (":" + " · ".join(d["item"] for d in reg[:5]) if reg else ""),
                 "action": "成功只增不減"})
    _rows_print(f"VIA 架構快照 — 總燈 {snap['lamp']} · 應掃 {snap['counts']['should']} / 已掃 {snap['counts']['scanned']}", rows,
                note="被動:啟動才更新")
    page_path = ARCH_DIR / "ARCH_latest.html"
    print(f"[頁] {page_path}\n[卡] {ARCH_DIR / 'ARCH_latest.txt'}\nNEXT: {snap_txt(snap).splitlines()[-1][6:]}")
    if open_page and IS_WIN and os.environ.get("VIA_NO_OPEN") != "1":
        try:
            os.startfile(str(page_path))  # noqa: S606 — 只開本機報告頁
        except OSError:
            pass
    return 0 if snap["lamp"] != "RED" else 1


# ------------------------------------------------------------------------------
# boot(v0100 + 前次 doctor 一列)
# ------------------------------------------------------------------------------
def cmd_boot() -> int:
    rc = PRIOR.cmd_boot()
    doc = PRIOR._read_json(DOCTOR_DIR / "DOCTOR_latest.json")
    if doc:
        print(f"  前次 doctor:{doc.get('at')} · 總燈 {doc.get('lamp')} · NEXT: {doc.get('next')}")
    else:
        print("  前次 doctor:沒有 → via-doctor")
    return rc


# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if argv[:1] in (["pano"], ["ast"]):
        sys.argv = [sys.argv[0]] + argv
        return PRIOR.main()
    ap = argparse.ArgumentParser(description=f"VCGC Hub {VERSION}(全指令 Python · VCGC 工具外掛)")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("boot")
    d = sub.add_parser("doctor")
    d.add_argument("--lanes", type=int, default=3)
    d.add_argument("--only", nargs="*")
    d.add_argument("--json", action="store_true")
    d.add_argument("--timeout", type=int, default=900)
    i = sub.add_parser("install")
    i.add_argument("pkgs", nargs="*")
    i.add_argument("--yes", action="store_true")
    a = sub.add_parser("auth")
    a.add_argument("--fred", action="store_true")
    a.add_argument("--clear", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("--vdf-only", action="store_true")
    r.add_argument("--vrn-only", action="store_true")
    r.add_argument("--vrn-source")
    r.add_argument("--via-db")
    r.add_argument("--yes", action="store_true")
    r.add_argument("--plan", action="store_true")
    s = sub.add_parser("setup")
    s.add_argument("--check", action="store_true")
    s.add_argument("--uninstall", action="store_true")
    b = sub.add_parser("bak")
    b.add_argument("--note", default="Routine Active Checkpoint")
    b.add_argument("--refresh", action="store_true")
    b.add_argument("--yes", action="store_true")
    b.add_argument("--no-daily", action="store_true")
    sub.add_parser("plug")
    u = sub.add_parser("update")
    u.add_argument("--lanes", type=int, default=3)
    u.add_argument("--no-doctor", action="store_true")
    u.add_argument("--no-open", action="store_true")
    u.add_argument("--root")
    x = ap.parse_args(argv)
    if x.command == "boot":
        return cmd_boot()
    if x.command == "doctor":
        return cmd_doctor(x.lanes, x.only, x.json, x.timeout)
    if x.command == "install":
        return cmd_install(x.pkgs, x.yes)
    if x.command == "auth":
        return cmd_auth(x.fred, x.clear)
    if x.command == "run":
        return cmd_run(x.vdf_only, x.vrn_only, x.vrn_source, x.via_db, x.yes, x.plan)
    if x.command == "setup":
        return cmd_setup(x.check, x.uninstall)
    if x.command == "bak":
        return cmd_bak(x.note, x.refresh, x.yes, daily=not x.no_daily)
    if x.command == "plug":
        return cmd_plug()
    if x.command == "update":
        return cmd_update(x.lanes, not x.no_doctor, not x.no_open, Path(x.root) if x.root else None)
    return 2


# ------------------------------------------------------------------------------
# selftest(全在暫存夾造資料,不吃本機狀態;零網路)
# ------------------------------------------------------------------------------
def selftest() -> int:
    ok = bad = skip = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    with tempfile.TemporaryDirectory(prefix="vcgc_hub_st_") as td:
        T = Path(td)
        reg = T / "tree" / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (T / "tree" / "supportive modules" / "VIA_SuperAccel_Module.py").write_text("X=1\n", encoding="utf-8")
        for v in ("0100", "0102", "0101"):
            (reg / f"CGC_MDL999_Fake_v{v}.py").write_text("import VIA_SuperAccel_Module\n" if v == "0102" else "# [VIA:ACCEL-BRIDGE]\n",
                                                           encoding="utf-8")
        (T / "tree" / "intake").mkdir()
        (T / "tree" / "intake" / "CGC_MDL999_Fake_v0999.py").write_text("x=1\n", encoding="utf-8")
        _INDEX.clear()
        t = find_tail("CGC_MDL999_Fake", [T / "tree"])
        chk("① 尾版索引:取最大號、跳過 intake", t is not None and t.name == "CGC_MDL999_Fake_v0102.py", f"({t.name if t else None})")
        chk("② 加速器橋以語法樹判:import 才算,只有標記不算",
            has_accel_bridge(reg / "CGC_MDL999_Fake_v0102.py") and not has_accel_bridge(reg / "CGC_MDL999_Fake_v0101.py"))
        chk("③ tool_root = 含 supportive modules 的祖先", tool_root(reg / "CGC_MDL999_Fake_v0102.py") == (T / "tree").resolve())
        chk("④ 燈號解析:總判 / 裁決 / verdict / 預設 rc",
            parse_lamp("[ENV MANAGER] 總判 RED · AMBER 5", 1) == "RED" and parse_lamp("  [裁決] YELLOW_ABSENT(誠實)", 1) == "YELLOW"
            and parse_lamp('{"verdict": "RED"}', 2) == "RED" and parse_lamp("all fine", 0) == "GREEN"
            and parse_lamp("x", None) == "GRAY")
        outs = {"gate_doctor": "  [修法] cv2 未裝(非互撞)——擇需:via-install opencv-contrib-python\n"
                               "     · pyyaml:6.0.3(使用者層) / 6.0.1(系統層)\n",
                "envtools": "      缺冊列:duckdb, pyarrow, psutil\n", "gate_conflict": "  [裝前] pip check 衝突 2 條\n"}
        pl = extract_plan(outs)
        chk("⑤ 安裝計畫:只抽工具自己印的套件 + 互撞 + 衝突",
            pl["pip"] == ["duckdb", "opencv-contrib-python", "psutil", "pyarrow"] and len(pl["dupes"]) == 1 and len(pl["conflicts"]) == 1,
            f"({pl['pip']})")
        chk("⑥ 套件名驗證擋注入", not _PKG_RX.match("x; rm -rf /") and _PKG_RX.match("rich==13.7.1") is not None)
        key = "0123456789abcdef0123456789abcdef"
        m = mask(key)
        chk("⑦ 遮罩不含任何 key 片段", all(key[i:i + 4] not in m for i in range(0, 29)) and "長度 32" in m)
        orig = "Set-Alias ll Get-ChildItem\n"
        once = compose_profile(orig)
        twice = compose_profile(once)
        chk("⑧ profile 區塊:冪等、原內容保留、可移除",
            once == twice and once.count(PROFILE_BEGIN) == 1 and orig.strip() in once
            and compose_profile(once, uninstall=True).strip() == orig.strip())
        src = T / "src"
        (src / "pkg").mkdir(parents=True)
        (src / "pkg" / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        (src / "b.json").write_text("{}", encoding="utf-8")
        (src / "data.parquet").write_bytes(b"PAR1")
        man, add, chg, dele, h = scan_delta(src, {})
        man2, add2, chg2, dele2, h2 = scan_delta(src, man)
        chk("⑨ 增量:第一次全收、第二次 0 變動 0 雜湊、非文字副檔名不收",
            len(add) == 2 and h == 2 and not (add2 or chg2 or dele2) and h2 == 0 and "data.parquet" not in man)
        time.sleep(0.01)
        (src / "pkg" / "a.py").write_text("def f():\n    return 2\n", encoding="utf-8")
        (src / "b.json").unlink()
        man3, add3, chg3, dele3, h3 = scan_delta(src, man2)
        chk("⑩ 增量:改一檔、刪一檔 → 變更 1 · 刪除 1 · 只算 1 次雜湊", chg3 == ["pkg/a.py"] and dele3 == ["b.json"] and h3 == 1)
        nodes, parsed = graph_update(src, man3, {"pkg/a.py"})
        chk("⑪ Graphify 增量:節點含函式與匯入", parsed == 1 and nodes and nodes[0]["functions"] == ["f"])
        fake = T / "tree" / "functional modules" / "VDF"
        fake.mkdir(parents=True)
        probe = T / "consent_seen.txt"
        (fake / "VDF_SystemManager_v0100.py").write_text(
            "import os,sys\nopen(sys.argv[-1] if False else %r,'w').write(os.environ.get('VIA_NET_CONSENT','-'))\n" % str(probe),
            encoding="utf-8")
        _INDEX.clear()
        before = os.environ.get("VIA_NET_CONSENT")
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cmd_run(vdf_only=True, assume_yes=True, roots=[T / "tree"])
        chk("⑫ run:同意閘只進子行程、父行程未設",
            rc == 0 and probe.read_text() == "YES" and os.environ.get("VIA_NET_CONSENT") == before)
        with contextlib.redirect_stdout(io.StringIO()):
            rc_no = cmd_run(vdf_only=True, assume_yes=False, roots=[T / "tree"])
        chk("⑬ run:非互動且沒 --yes → 不跑", rc_no == 1)
        _INDEX.clear()
    pv = {"cards": [{"system": "VDF", "lamp": "GREEN"}], "governance": [], "ssot": [], "sdd": [{"rule": "X-REG", "lamp": "GREEN"}],
          "numbering": []}
    cu = {"cards": [{"system": "VDF", "lamp": "YELLOW"}], "governance": [], "ssot": [], "sdd": [], "numbering": [{"key": "XCODE", "lamp": "GREEN"}]}
    dl = {d["item"]: d for d in diff_snap(pv, cu)}
    chk("⑱ 快照比對:綠變差 / 綠不見 = 退步;新出現不算退步",
        dl["卡 VDF"]["regress"] and dl["SDD X-REG"]["kind"] == "不見" and dl["SDD X-REG"]["regress"] and not dl["編號 XCODE"]["regress"])
    lock = ui_lock(CODE_ROOT)
    fake = {"at": "t", "mode": "被動", "via_root": "<r>", "lamp": "RED", "counts": {"should": 1, "scanned": 1, "skipped": []},
            "tools": {}, "sources": [], "cards": [{"system": "VDF<x>", "folder": "f", "entry": None, "accel": False, "pack": None,
            "ssot": {}, "lamp": "RED"}], "governance": [], "ssot_layers": ["VDF"], "ssot": [], "sdd": [], "numbering": [],
            "doctor": {"plugins": [], "plan": {}}, "next": [], "delta": []}
    pg = render_html(fake, lock)
    tk = lock.get("tokens", {})
    chk("⑲ HTML 只用視覺鎖定冊的值(字體 · 底色 · 燈 CSS)、內容有跳脫",
        bool(tk) and tk["font_family"] in pg and tk["color_bg"] in pg and lock.get("lamp_css", "")[:40] in pg
        and "VDF&lt;x&gt;" in pg and "<x>" not in pg, f"({lock.get('_file')})")
    chk("⑳ 讀不到鎖冊 → 文字燈 + UI_TOKENS=灰,不自編色碼", "UI_TOKENS=灰" in render_html(fake, {}) and "#" not in render_html(fake, {}).split("<style>")[1].split("</style>")[0])
    chk("㉑ 被動:子行程帶 VIA_PANORAMA_AUTO=0(不在背景起監控)", _child_env()["VIA_PANORAMA_AUTO"] == "0")
    chk("㉒ token 工具 = 鎖冊那一支", (token_tool(CODE_ROOT) or Path("x")).name.startswith("CGC_MDL158_"))
    chk("⑭ 外掛冊 7 支、家族名皆有尾版(本樹)", len(PLUGINS) == 7 and all(find_tail(p["family"], [CODE_ROOT]) for p in PLUGINS),
        f"({sum(bool(find_tail(p['family'], [CODE_ROOT])) for p in PLUGINS)}/7)")
    chk("⑮ 本檔加速器橋執行時載入(生效)", VIA_ACCEL is not None)
    chk("⑯ v0100 前版鏈在(pano / ast 沿用)", hasattr(PRIOR, "cmd_panorama") and hasattr(PRIOR, "cmd_ast_inject"))
    if _pwsh():
        with tempfile.TemporaryDirectory(prefix="vcgc_prof_") as td:
            p = Path(td) / "profile.ps1"
            p.write_text(compose_profile("$x = 1\n"), encoding="utf-8-sig")
            rc, out = _ps(f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{p}',[ref]$null,[ref]$e); $e.Count")
            chk("⑰ profile 區塊 pwsh 剖析 0 錯", rc == 0 and out.splitlines()[-1:] == ["0"], f"({out[-60:]})")
    else:
        skip += 1
        print("  [SKIP] ⑰ pwsh 不在本機 → 區塊剖析待工作站(黃)")
    print(f"  [計] {FAMILY} {VERSION} 自測 OK {ok} · FAIL {bad} · SKIP {skip}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
