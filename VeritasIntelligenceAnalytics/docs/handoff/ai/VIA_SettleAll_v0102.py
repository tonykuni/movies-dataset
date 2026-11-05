#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_SettleAll v0102 — 一支 Python 收尾五系統 + 兩個工具:全景檢視 → 同步 → VDF ui → VRN 狀態 → VCGC 驗 → Graphify → VQG → Agent OS → 報告 + 貼回包。

操作員 2026-11-04 桌機貼回四條一行的結果 → 「integrate into one code to handle above」。要處理的(v0101 一字不動 · 本版新檔):
  ⑦ Graphify v0101 一行:VCGC 那張圖用固定表「需要約 6 GB」在 4.6 GB 可用時直接跳過 → 本版改成**真跑 + 記憶體看門狗**:
     每秒量可用記憶體與子行程 RSS,可用 < 下限(預設 0.75 GB · --graphify-floor-gb)就殺整棵子行程(桌機不當掉)· 峰值 RSS 與最低可用記進收據,
     下次就有實測數字,不再靠猜。VRN · VRN_Shared · VDF 三張已綠的照 graphify 自己的增量快取,只重抽改過的檔。
  ⑧ VQG 一行:紅 NO_DAILY_PRICES。根因 = 桌機工作樹的 VDF 冊只有 v0100(家 = via_01_vdf · 2026-10-22 實測底下 .duckdb 0 個),
     分支上的 v0101 才把真正的家 via_database\\vdf_database 排第一;一行只取 VQG 兩個檔、沒更新工作樹 → VQG 照舊冊找錯家。
     本版:③ 同步先把分支併進來(乾淨才併)→ ⑧ VDF 家候選 = $env:VQG_VDF_ROOT → 工作樹 + 分支尾版兩邊所有 VDF_DataHome_SSOT_v*.json
     的 homes(新版冊優先 · 冊內照順序)→ 倉內 VDF\\output_hub 接點;每個在這台機器存在的家都跑 VQG 自己的 doctor,
     取第一個有日線 parquet 的家再 closeout(收據照 VQG 自己寫)。一個都沒有 → RED 列出每個家的 doctor 判決,並指明是 VDF 線要跑日線回填。
  ⑨ Agent OS 一行:selftest rc 2、其餘三項 rc 0。根因 = 引擎自測 test_scan_project_enforces_total_source_bytes_and_nofollow 用
     symlink_to 建捷徑,Windows 沒開「開發人員模式」或不是系統管理員會 OSError WinError 1314(容器 48 / 48 綠)。
     本版:讀自測 JSON 的 details 逐項分類 —— 只有「Windows 建 symlink 權限」這類環境項 → YELLOW(引擎本體照設計拒 symlink · 功能不受影響),
     其他失敗 → RED;不是 RED 才產生儀表板(一行原本 RED 就停)。引擎一字不改(SHA-256 釘住)。
  ⑤ VRN:--confirm H-fd2ea35f 已記、收尾頁 DATA_GAP(資料源缺口 · VRN-2 側結案)→ 本版 --vrn 預設 status:只讀 VRN-2 自己的收尾收據判燈,
     不重跑 40 分鐘那輪(要重跑仍可 --vrn repair / check)。
  取檔:VQG v0104 / v0105 與 Agent OS v0102 先看工作樹(SHA-256 對才用),不對或不在 → 從分支 origin/<BRANCH> git show 取到 Downloads\\VIA_Settle_v0102\\
     再核 SHA-256;不對就不跑。VQG 的 Python 照一行的順序找有 duckdb + polars 的(VQG 不 pip)。
五系統對等(VRN-1 · VRN-2 · VDF · VCGC · VQG)+ Agent OS / Graphify 工具:本檔只經各系統自己的入口跑,不改他系統的檔;
只寫 VIA_Reports/settle · VIA_Reports/agent_os · VIA_Reports/graphify 與 Downloads(VQG / VRN / VDF 的收據由它們自己寫)。
用法:python VIA_SettleAll_v0102.py [--root <倉根>] [--only scan,sync,vdf,vrn,vcgc,graphify,vqg,agentos,report] [--no-sync]
      [--vrn status|repair|check|skip] [--graphify-floor-gb 0.75] [--selftest]
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


import argparse
import ast
import contextlib
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

NAME = "VIA_SettleAll"
VERSION = "v0102"
BRANCH = "claude/optimistic-goodall-yhalc5"
STAGES = ("scan", "sync", "vdf", "vrn", "vcgc", "graphify", "vqg", "agentos", "report")
FAMILIES = {   # 家族 → (夾, 前綴);只讀,不改他系統的檔
    "VRN_SystemManager": ("functional modules/VRN", "VRN_SystemManager_v"),
    "VDF_SystemManager": ("functional modules/VDF", "VDF_SystemManager_v"),
    "VDF_ENG236_FetchMatrixUI": ("functional modules/VDF/engine", "VDF_ENG236_FetchMatrixUI_v"),
    "CGC_MDL149_Console": ("supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v"),
    "CGC_MDL261_UIEngine": ("supportive modules/registry", "CGC_MDL261_UIEngine_v"),
    "CGC_MDL274_HealthMatrix": ("supportive modules/registry", "CGC_MDL274_HealthMatrix_v"),
    "CGC_MDL224_TestAuto": ("supportive modules/registry", "CGC_MDL224_TestAuto_v"),
    "VRN2_RoundAll": ("docs/handoff/ai", "VRN2_RoundAll_v"),
    "VQG_AllInOne": ("functional modules/VQG", "VQG_AllInOne_v"),
    "VIA_AgentOS": ("supportive modules/agent_os", "VIA_AgentOS_v"),
}
PINNED = {   # 從工作樹 / 分支取檔時核 SHA-256(CRLF 先正規化成 LF · 與各一行的算法相同);不對就不跑
    "functional modules/VQG/VQG_AllInOne_v0104.py": "d2a5ca07fa4d29435584c111095a31951075ab585b51cc74b14b22ef48ca1d02",
    "functional modules/VQG/VQG_AllInOne_v0105.py": "cc050f0fe42786f7113dbf0dd920d954feaf0b020e216456f336ce0d30801619",
    "supportive modules/agent_os/VIA_AgentOS_v0102.py": "3d23c7adefce5e688277676fadc0a4a70311da3d41fd6b6ef6de1c1bcd9077fb",
}
VQG_FILES = ("functional modules/VQG/VQG_AllInOne_v0104.py", "functional modules/VQG/VQG_AllInOne_v0105.py")
AGENTOS_FILE = "supportive modules/agent_os/VIA_AgentOS_v0102.py"
GRAPHIFY_SYSTEMS = (("VRN", "functional modules/VRN2", 3), ("VRN_Shared", "functional modules/VRN", 4),
                    ("VDF", "functional modules/VDF", 4), ("VCGC", "supportive modules/registry", 6))   # gb = v0101 一行的估計(只記 · 不再拿來跳過)
GRAPHIFY_EXCLUDES = ("references/", "intake/", "_quarantine*/", "*quarantine*/", "VIA_RetiredEngines/", "backup*/", "archive*/")
WIN_SYMLINK_PRIVILEGE = ("winerror 1314", "privilege is not held")   # Windows 沒有建 symlink 權限(開發人員模式 / 系統管理員)
FRAME_RX = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+)(?:, in (?P<func>\S+))?')
EXC_RX = re.compile(r"^(?P<type>[A-Za-z_][\w.]*(?:Error|Exception|Warning|Exit|Interrupt))(?::\s*(?P<msg>.*))?$")
ATTR_RX = re.compile(r"(?:module|object) '(?P<mod>[^']+)' has no attribute '(?P<attr>[^']+)'")
LOG = []
RANK = {"GREEN": 0, "GRAY": 0, "YELLOW": 1, "RED": 2}


def worst(*lamps) -> str:
    """燈取最差:RED > YELLOW > GREEN(GRAY 當 GREEN);認不得的當 YELLOW(不冒充綠)。"""
    out = "GREEN"
    for x in lamps:
        x = x if x in RANK else "YELLOW"
        if RANK[x] > RANK[out]:
            out = x
    return out


def vdf_lamp(rc: int, lamps: list) -> str:
    """④ rc 不是 0 → RED;rc 0 → 頁上各段燈取最差(YELLOW 不升 GREEN)。"""
    return "RED" if rc != 0 else worst(*lamps)


def vrn_lamp(rc: int, state: dict | None, fresh: bool) -> str:
    """⑤ 本次 rc 不是 0 / 2 → RED(舊收據不救);收據不是本次寫的 → 最多 YELLOW;本次寫的 PASS → GREEN;VRN-2 側有待修 → RED。"""
    if rc not in (0, 2):
        return "RED"
    if not state or not fresh:
        return "YELLOW"
    if (state.get("per_owner") or {}).get("VRN-2"):
        return "RED"
    return "GREEN" if state.get("state") == "PASS" else "YELLOW"


def vrn_status_lamp(state: dict | None) -> str:
    """⑤ status 模式(只讀收據 · 不跑):沒收據 → YELLOW;VRN-2 側有待修 → RED;PASS → GREEN;其他(REVIEW / DATA_GAP …)→ YELLOW。"""
    if not state:
        return "YELLOW"
    if (state.get("per_owner") or {}).get("VRN-2"):
        return "RED"
    return "GREEN" if state.get("state") == "PASS" else "YELLOW"


def vcgc_lamp(test_lamp: str | None, test_rc: int, handoff_rc: int, handoff_red: dict) -> str:
    """⑥ test --quick 總燈與 handoff check 取最差:沒讀到總行 → RED;test rc 不是 0 / 2 → RED;交接閘有紅或 rc 不是 0 → RED。"""
    t = test_lamp if test_lamp in RANK else "RED"
    if test_rc not in (0, 2):
        t = "RED"
    h = "RED" if (handoff_rc != 0 or handoff_red) else "GREEN"
    return worst(t, h)


def agentos_classify(report: dict | None, windows: bool) -> dict:
    """⑨ 自測 JSON → 燈:ok → GREEN;失敗全是「Windows 沒有建 symlink 權限(WinError 1314)」→ YELLOW(環境 · 引擎照設計拒 symlink);
    其他(或不是 Windows 卻這樣)→ RED;讀不到 JSON → RED。"""
    if not isinstance(report, dict) or "ok" not in report:
        return {"lamp": "RED", "known_env": [], "unknown": [{"test": "?", "kind": "NO_JSON"}], "tests_run": 0, "failures": 0, "errors": 0}
    known, unknown = [], []
    for d in report.get("details") or []:
        text = str(d.get("detail") or "").lower()
        row = {"test": str(d.get("test") or "")[:120], "kind": d.get("kind")}
        if windows and any(k in text for k in WIN_SYMLINK_PRIVILEGE):
            known.append(dict(row, why="Windows 建 symlink 要開發人員模式或系統管理員(WinError 1314)· 引擎本體照設計拒 symlink · 功能不受影響"))
        else:
            unknown.append(dict(row, tail=str(d.get("detail") or "")[-300:]))
    lamp = "GREEN" if report.get("ok") else ("YELLOW" if (known and not unknown) else "RED")
    return {"lamp": lamp, "known_env": known, "unknown": unknown, "tests_run": int(report.get("tests_run") or 0),
            "failures": int(report.get("failures") or 0), "errors": int(report.get("errors") or 0)}


def graphify_lamp(results: list) -> str:
    """⑦ 有紅 → RED;沒有一張綠或有黃 → YELLOW;全綠(灰不算)→ GREEN。"""
    lamps = [r.get("lamp") for r in results]
    if "RED" in lamps:
        return "RED"
    if "YELLOW" in lamps or "GREEN" not in lamps:
        return "YELLOW"
    return "GREEN"


def say(lamp: str, step: str, text: str, nxt: str = "") -> None:
    line = "[%s] %s · %s" % (lamp, step, text)
    LOG.append({"lamp": lamp, "step": step, "text": text, "next": nxt})
    print(line + (("\n       → " + nxt) if nxt else ""), flush=True)


def vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def family_files(via: Path, folder: str, prefix: str) -> list:
    base = via / folder
    if not base.is_dir():
        return []
    pat = ("**/" if folder == "docs/handoff/ai" else "") + prefix + "*.py"
    return sorted((p for p in base.glob(pat) if vnum(p) >= 0), key=vnum)


def _env(env=None) -> dict:
    e = dict(os.environ)
    e.update({"PYTHONUTF8": "1", "VIA_FROM_VCGC": "YES", "VIA_NO_OPEN": "1"})
    e.update(env or {})
    return e


def run(cmd, cwd=None, timeout=1800, env=None) -> tuple:
    """→ (rc, 輸出全文 stdout+stderr);逾時回 rc 124。只跑各系統自己的入口。"""
    rc, out, err = run2(cmd, cwd=cwd, timeout=timeout, env=env)
    return rc, out + err


def run2(cmd, cwd=None, timeout=1800, env=None) -> tuple:
    """→ (rc, stdout, stderr) 分開拿(VQG doctor 的 JSON 在 stdout · 說明在 stderr);逾時 rc 124 · 找不到程式 rc 127。"""
    try:
        p = subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=_env(env))
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        return 124, (out.decode("utf-8", "replace") if isinstance(out, bytes) else out), "\n[逾時 %d 秒]" % timeout
    except OSError as exc:
        return 127, "", "%s: %s" % (type(exc).__name__, exc)


def run_raw(cmd, cwd=None, timeout=300) -> tuple:
    """→ (rc, stdout bytes);git show 取檔用(不經文字解碼)。"""
    try:
        p = subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None, capture_output=True, timeout=timeout, env=_env())
        return p.returncode, p.stdout or b""
    except (subprocess.TimeoutExpired, OSError):
        return 127, b""


# ---------------------------------------------------------------- 記憶體看門狗(⑦ Graphify)
def parse_meminfo_gb(text: str) -> float:
    m = re.search(r"^MemAvailable:\s*(\d+)\s*kB", text or "", re.M)
    return round(int(m.group(1)) / 2 ** 20, 2) if m else -1.0


def free_gb() -> float:
    """可用實體記憶體(GB);量不到回 -1(不猜)。"""
    try:
        if os.name == "nt":
            import ctypes

            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = _MS()
            m.dwLength = ctypes.sizeof(_MS)
            return round(m.ullAvailPhys / 2 ** 30, 2) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)) else -1.0
        return parse_meminfo_gb(Path("/proc/meminfo").read_text(encoding="utf-8"))
    except Exception:                                      # noqa: BLE001 — 量不到就 -1
        return -1.0


def rss_gb(pid: int) -> tuple:
    """子行程 (目前 RSS, 峰值 RSS) GB;量不到回 (0, 0)。"""
    try:
        if os.name == "nt":
            import ctypes

            class _PMC(ctypes.Structure):
                _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong), ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            k32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
            h = k32.OpenProcess(0x1000, False, int(pid))          # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return 0.0, 0.0
            pmc = _PMC()
            pmc.cb = ctypes.sizeof(_PMC)
            ok = psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
            k32.CloseHandle(h)
            return (round(pmc.WorkingSetSize / 2 ** 30, 3), round(pmc.PeakWorkingSetSize / 2 ** 30, 3)) if ok else (0.0, 0.0)
        txt = Path("/proc/%d/status" % pid).read_text(encoding="utf-8")
        cur = re.search(r"^VmRSS:\s*(\d+)\s*kB", txt, re.M)
        pk = re.search(r"^VmHWM:\s*(\d+)\s*kB", txt, re.M)
        return (round(int(cur.group(1)) / 2 ** 20, 3) if cur else 0.0), (round(int(pk.group(1)) / 2 ** 20, 3) if pk else 0.0)
    except Exception:                                      # noqa: BLE001 — 子行程已結束或量不到
        return 0.0, 0.0


def kill_tree(pid: int) -> None:
    """殺子行程整棵(graphify 有 worker):Windows taskkill /T;POSIX 殺整個 session。"""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, timeout=60)
        else:
            import signal
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except Exception:                                      # noqa: BLE001 — 已經死了就算了
        return


def run_watched(cmd, cwd=None, env=None, floor_gb: float = 0.75, timeout: int = 5400, poll: float = 1.0) -> dict:
    """跑子行程並看記憶體:每 poll 秒量可用記憶體與子行程 RSS;可用 < floor_gb → 殺整棵(rc 137)· 逾時 → 殺(rc 124)。
    → {rc, out, peak_rss_gb, min_free_gb, free_start_gb, killed, seconds}"""
    kw = {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)} if os.name == "nt" else {"start_new_session": True}
    t0 = time.time()
    f0 = free_gb()
    try:
        p = subprocess.Popen([str(c) for c in cmd], cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", env=_env(env), **kw)
    except OSError as exc:
        return {"rc": 127, "out": "%s: %s" % (type(exc).__name__, exc), "peak_rss_gb": 0.0, "min_free_gb": f0, "free_start_gb": f0, "killed": None, "seconds": 0}
    chunks = []

    def _drain():
        for line in p.stdout:
            chunks.append(line)
    th = threading.Thread(target=_drain, daemon=True)
    th.start()
    peak, min_free, killed = 0.0, f0, None
    while p.poll() is None:
        time.sleep(poll)
        f = free_gb()
        if f >= 0:
            min_free = f if min_free < 0 else min(min_free, f)
        cur, pk = rss_gb(p.pid)
        peak = max(peak, cur, pk)
        if 0 <= f < floor_gb:
            killed = "可用記憶體 %.2f GB < 下限 %.2f GB → 殺子行程(桌機不當掉)" % (f, floor_gb)
            kill_tree(p.pid)
            break
        if time.time() - t0 > timeout:
            killed = "逾時 %d 秒 → 殺子行程" % timeout
            kill_tree(p.pid)
            break
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        killed = (killed or "") + " · 殺不掉(還在跑)"
    th.join(timeout=10)
    rc = p.returncode if killed is None else (124 if "逾時" in killed else 137)
    return {"rc": rc, "out": "".join(chunks), "peak_rss_gb": round(peak, 3), "min_free_gb": min_free, "free_start_gb": f0,
            "killed": killed, "seconds": int(time.time() - t0)}


# ---------------------------------------------------------------- 取檔(SHA-256 釘住)· Python 探找 · VDF 家候選
def sha_lf(data: bytes) -> str:
    """CRLF 正規化成 LF 再算 SHA-256(與 VQG / Agent OS 一行的算法相同)。"""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def git_show_bytes(repo: Path, ref: str, rel_repo: str) -> bytes | None:
    rc, data = run_raw(["git", "-C", repo, "show", "%s:%s" % (ref, rel_repo)], timeout=300)
    return data if rc == 0 and data else None


def fetch_set(via: Path, rels, dst_dir: Path, pinned: dict | None = None) -> tuple:
    """同一組檔(VQG 兩個 · Agent OS 一個)一起取:工作樹每個 SHA 都對 → 就地用;否則全組從分支 origin/<BRANCH> 取到 dst_dir(逐檔核 SHA)。
    → (路徑清單 | None, 說明)"""
    pinned = pinned or PINNED
    ok_tree, paths = True, []
    for rel in rels:
        p = via / rel
        try:
            good = p.is_file() and sha_lf(p.read_bytes()) == pinned[rel]
        except OSError:
            good = False
        ok_tree = ok_tree and good
        paths.append(p)
    if ok_tree:
        return paths, "工作樹(SHA-256 全對)"
    out, why = [], []
    for rel in rels:
        data = git_show_bytes(via.parent, "origin/" + BRANCH, "VeritasIntelligenceAnalytics/" + rel)
        if data is None:
            why.append("%s:分支取不到" % Path(rel).name)
            continue
        if sha_lf(data) != pinned[rel]:
            why.append("%s:分支上 SHA-256 %s 不是釘住的 %s" % (Path(rel).name, sha_lf(data)[:12], pinned[rel][:12]))
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        q = dst_dir / Path(rel).name
        q.write_bytes(data.replace(b"\r\n", b"\n"))
        out.append(q)
    if why:
        return None, "工作樹的檔不在或 SHA 不符 · " + " · ".join(why)
    return out, "分支 origin/%s(SHA-256 全對)→ %s" % (BRANCH, dst_dir)


def find_python_with(mods, extra=()) -> Path | None:
    """照 VQG 一行的順序找有指定套件的 Python(不 pip):VQG_PY → envs\\via_core → via_core_312 → via_vdf_312 → C:\\Python313 → 本檔的 → PATH 上的。"""
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    sub = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    cands = [os.environ.get("VQG_PY"), *extra]
    cands += [home / "envs" / n / sub for n in ("via_core", "via_core_312", "via_vdf_312")]
    cands += ["C:/Python313/python.exe" if os.name == "nt" else None, sys.executable, shutil.which("python"), shutil.which("python3")]
    seen = set()
    for c in cands:
        if not c or "WindowsApps" in str(c) or str(c) in seen:
            continue
        seen.add(str(c))
        p = Path(c)
        if p.is_file() and run2([p, "-c", "import " + ", ".join(mods)], timeout=120)[0] == 0:
            return p
    return None


def vdf_homes(text: str) -> list:
    """VDF_DataHome_SSOT 冊 → [(id, db_home)] 照冊上順序(讀不懂回空)。"""
    try:
        d = json.loads(text)
    except ValueError:
        return []
    return [(str(h.get("id") or "?"), str(h.get("db_home") or "")) for h in (d.get("homes") or []) if isinstance(h, dict) and h.get("db_home")]


def vdf_root_candidates(via: Path, branch_book: tuple | None = None) -> list:
    """VDF 家候選(順序 = 試的順序):$env:VQG_VDF_ROOT → 工作樹 + 分支尾版的 VDF_DataHome_SSOT_v*.json(新版冊優先 · 冊內照順序)→ 倉內 VDF\\output_hub 接點。
    branch_book = (檔名, 冊內容文字) · 由呼叫端從 origin/<BRANCH> 取(本函數不碰 git)。"""
    out, seen = [], set()

    def add(path, how):
        key = str(path).rstrip("\\/").lower()
        if key and key not in seen:
            seen.add(key)
            out.append({"path": str(path), "how": how})
    env = os.environ.get("VQG_VDF_ROOT")
    if env:
        add(env, "環境變數 VQG_VDF_ROOT")
    books = {}
    for p in (via / "functional modules" / "VDF").glob("VDF_DataHome_SSOT_v[0-9][0-9][0-9][0-9].json"):
        try:
            books[vnum(p)] = (p.name, vdf_homes(p.read_text(encoding="utf-8")), "工作樹")
        except OSError:
            books[vnum(p)] = (p.name, [], "工作樹(讀不到)")
    if branch_book:
        v = vnum(Path(branch_book[0]))
        if v not in books:
            books[v] = (branch_book[0], vdf_homes(branch_book[1]), "分支 origin/" + BRANCH)
    for v in sorted(books, reverse=True):
        name, homes, where = books[v]
        for hid, home in homes:
            add(home, "VDF 的冊 %s · %s(%s)" % (name, hid, where))
    add(via / "functional modules" / "VDF" / "output_hub", "倉內 VDF\\output_hub 接點(桌機是指到資料家的 junction)")
    return out


def pick_vdf_root(cands: list, doctor_fn) -> tuple:
    """每個在這台機器存在的家跑 doctor_fn(path) → dict;取第一個 daily_price_files > 0 的家。→ (選到的列 | None, 全表)"""
    chosen, table = None, []
    for c in cands:
        p = Path(c["path"])
        if not p.is_dir():
            table.append(dict(c, exists=False))
            continue
        if chosen is not None:
            table.append(dict(c, exists=True, verdict="(已選到前面的家 · 未探)"))
            continue
        d = doctor_fn(p) or {}
        row = dict(c, exists=True, verdict=d.get("verdict"), daily_price_files=int(d.get("daily_price_files") or 0),
                   files=d.get("files"), missing_for_strict=d.get("missing_for_strict"))
        table.append(row)
        if row["daily_price_files"] > 0:
            chosen = row
    return chosen, table


# ---------------------------------------------------------------- 找根 · git
def find_root(explicit=None) -> Path | None:
    cands = [explicit, os.environ.get("VIA_ROOT"), os.environ.get("VRN2_ROOT")]
    cands += [str(p) for p in Path(__file__).resolve().parents]
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    cands += [str(home / "OneDrive" / "Documents" / "movies-dataset"), str(home / "Documents" / "movies-dataset")]
    for c in cands:
        if not c:
            continue
        p = Path(c)
        for via in (p, p / "VeritasIntelligenceAnalytics"):
            if (via / "functional modules").is_dir() and (via / "supportive modules").is_dir():
                return via
    return None


def parse_ahead_behind(text: str) -> tuple:
    """`git rev-list --left-right --count A...B` → (只在本機, 只在遠端)。"""
    m = re.match(r"\s*(\d+)\s+(\d+)\s*$", text or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def git_state(repo: Path, fetch: bool = True) -> dict:
    st = {"repo": str(repo), "branch": None, "head": None, "fetched": False}
    if shutil.which("git") is None:
        st["error"] = "沒有 git"
        return st
    st["branch"] = run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"])[1].strip()
    st["head"] = run(["git", "-C", repo, "rev-parse", "--short", "HEAD"])[1].strip()
    if fetch:
        for ref in (BRANCH, "main"):
            rc, _ = run(["git", "-C", repo, "fetch", "-q", "origin", ref], timeout=300)
            st["fetched"] = st["fetched"] or rc == 0
    for ref in (BRANCH, "main"):
        rc, out = run(["git", "-C", repo, "rev-list", "--left-right", "--count", "HEAD...origin/" + ref])
        a, b = parse_ahead_behind(out) if rc == 0 else (None, None)
        st[ref] = {"local_only": a, "remote_only": b}
    rc, out = run(["git", "-C", repo, "status", "--porcelain"])
    lines = [x for x in out.splitlines() if x.strip()] if rc == 0 else []
    st["dirty_tracked"] = sum(1 for x in lines if not x.startswith("??"))
    st["untracked"] = sum(1 for x in lines if x.startswith("??"))
    return st


# ---------------------------------------------------------------- AST 全景 · AST 定位
def ast_scan(paths) -> dict:
    """每檔 ast.parse + compile(只在記憶體 · 不執行)→ 錯誤位置;編譯警告(如無效跳脫)記檔:行,不印、不算錯。"""
    import warnings
    bad, warns = [], []
    for p in paths:
        try:
            src = Path(p).read_text(encoding="utf-8-sig")
        except OSError as exc:
            bad.append({"file": str(p), "kind": "READ", "msg": type(exc).__name__})
            continue
        try:
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter("always")
                compile(ast.parse(src, filename=str(p)), str(p), "exec")
            warns += [{"file": Path(p).name, "line": w.lineno, "msg": str(w.message)[:120]} for w in ws]
        except SyntaxError as exc:
            bad.append({"file": str(p), "kind": "SYNTAX", "line": exc.lineno, "msg": exc.msg})
        except (ValueError, TypeError) as exc:
            bad.append({"file": str(p), "kind": "COMPILE", "msg": str(exc)[:160]})
    return {"files": len(paths), "errors": bad, "warnings": warns}


def enclosing_def(path: Path, line: int) -> dict:
    """AST 定位:這一行在哪個 def / class 裡(最內層)+ 原文那一行。"""
    try:
        src = Path(path).read_text(encoding="utf-8-sig")
        tree = ast.parse(src)
    except (OSError, SyntaxError, ValueError):
        return {"def": None, "src": None}
    best = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.lineno <= line <= (n.end_lineno or n.lineno):
            if best is None or n.lineno >= best.lineno:
                best = n
    lines = src.splitlines()
    return {"def": ("%s (L%d-%d)" % (best.name, best.lineno, best.end_lineno)) if best else "<module>",
            "src": lines[line - 1].strip()[:200] if 0 < line <= len(lines) else None}


def _defined_names(tree) -> set:
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
                names.add(x.id)
            elif isinstance(x, ast.alias):
                names.add((x.asname or x.name).split(".")[0])
            elif isinstance(x, ast.Global):
                names.update(x.names)
            elif isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "setattr" and len(x.args) >= 2 \
                    and isinstance(x.args[1], ast.Constant) and isinstance(x.args[1].value, str):
                names.add(x.args[1].value)
    return names


def attr_trace(files, attr: str) -> dict:
    """同家族每一版:誰定義 attr、誰去讀它(X.attr / getattr(X, 'attr'))· 只讀 AST。"""
    defined, used = [], []
    for p in files:
        try:
            tree = ast.parse(Path(p).read_text(encoding="utf-8-sig"))
        except (OSError, SyntaxError, ValueError):
            continue
        if attr in _defined_names(tree):
            defined.append(Path(p).name)
        for n in ast.walk(tree):
            hit = (isinstance(n, ast.Attribute) and n.attr == attr) or (
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("getattr", "hasattr")
                and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value == attr)
            if hit:
                used.append("%s:L%d" % (Path(p).name, n.lineno))
    first_def = min((vnum(Path(x)) for x in defined), default=None)
    early = [u for u in used if first_def is None or vnum(Path(u.split(":")[0])) <= first_def]
    return {"attr": attr, "defined_in": defined, "used_at": used[:40], "used_before_defined": early[:20]}


def diagnose(text: str, via: Path | None = None) -> dict:
    """Traceback → 例外 · 每一框(AST 定位)· 前版鏈轉手 · 屬性缺 → 同家族誰定義 / 誰讀。"""
    frames = [m.groupdict() for m in FRAME_RX.finditer(text or "")]
    exc = None
    for ln in reversed((text or "").splitlines()):
        m = EXC_RX.match(ln.strip())
        if m and "Warning" not in m.group("type"):
            exc = {"type": m.group("type"), "msg": (m.group("msg") or "").strip()}
            break
    out = {"exception": exc, "frames": [], "recursion": False, "hint": ""}
    for f in frames[-12:]:
        p = Path(f["file"])
        loc = enclosing_def(p, int(f["line"])) if p.is_file() else {"def": None, "src": None}
        out["frames"].append({"file": p.name, "line": int(f["line"]), "func": f["func"], **loc})
    names = [(f["file"], f["line"]) for f in frames]
    out["recursion"] = len(names) > 40 and len(set(names[-40:])) <= 4 or "RecursionError" in (exc or {}).get("type", "")
    hops = [f for f in out["frames"] if f["func"] == "__getattr__"]
    if exc and exc["type"].endswith("AttributeError"):
        m = ATTR_RX.search(exc["msg"])
        attr = m.group("attr") if m else None
        out["attr"] = attr
        fam_files = []
        if attr and frames:
            stem = re.sub(r"_v\d+$", "", Path(frames[-1]["file"]).stem)
            folder = Path(frames[-1]["file"]).parent
            if folder.is_dir():
                fam_files = sorted((p for p in folder.glob(stem + "_v*.py") if vnum(p) >= 0), key=vnum)
            out["trace"] = attr_trace(fam_files, attr) if fam_files else None
        tr = out.get("trace") or {}
        if attr and tr.get("defined_in") == []:
            out["hint"] = "屬性 %s 整個家族都沒有定義 → 讀它的那一版(%s)要改成先檢查或出新版補定義" % (attr, ", ".join(tr.get("used_at", [])[:3]) or "?")
        elif attr and tr.get("used_before_defined"):
            out["hint"] = "屬性 %s 最早在 %s 定義,但更早的版就在讀(%s)→ 前版鏈轉手 %d 次後落到沒有它的那一版" % (
                attr, tr["defined_in"][0], ", ".join(tr["used_before_defined"][:3]), len(hops))
        elif attr:
            out["hint"] = "屬性 %s 經前版鏈轉手 %d 次後找不到 → 看 frames 第一個非 __getattr__ 的框(呼叫端)" % (attr, len(hops))
    elif out["recursion"]:
        out["hint"] = "遞迴:同幾框反覆出現(前版鏈互指或 __getattr__ 自己找自己)"
    elif exc:
        out["hint"] = "%s:看最後一框 %s" % (exc["type"], (out["frames"][-1]["file"] + ":%d" % out["frames"][-1]["line"]) if out["frames"] else "?")
    return out


# ---------------------------------------------------------------- 各階段
def stage_scan(via: Path, ctx: dict) -> None:
    env = {"python": sys.version.split()[0], "exe": sys.executable, "pwsh": shutil.which("pwsh") or shutil.which("pwsh.exe"), "free_gb": free_gb()}
    for mod in ("duckdb", "pyarrow", "polars", "pandas", "fitz", "pypdfium2"):
        try:
            m = __import__(mod)
            env[mod] = getattr(m, "__version__", "ok")
        except Exception:                              # noqa: BLE001 — 只量有沒有
            env[mod] = None
    ctx["env"] = env
    miss = [k for k in ("duckdb", "pyarrow") if not env[k]]
    say("YELLOW" if miss else "GREEN", "① 環境", "Python %s · duckdb %s · pyarrow %s · polars %s · pwsh %s · 可用記憶體 %s GB" % (
        env["python"], env["duckdb"], env["pyarrow"], env["polars"], "有" if env["pwsh"] else "沒有", env["free_gb"]),
        ("缺 %s → VDF 表頭 / 增量庫 / Parquet 自測會紅(經 VCGC 環境工具裝);VQG 另找有 duckdb + polars 的 Python" % " · ".join(miss)) if miss else "")
    fams = {}
    allfiles = []
    for fam, (folder, prefix) in FAMILIES.items():
        fs = family_files(via, folder, prefix)
        allfiles += fs
        fams[fam] = {"tail": fs[-1].name if fs else None, "versions": len(fs)}
    sc = ast_scan(allfiles)
    ctx["families"], ctx["ast"] = fams, sc
    say("RED" if sc["errors"] else "GREEN", "② AST 全景", "家族 %d · 檔 %d · 語法 / 編譯錯 %d · 編譯警告 %d(凍結版不改 · 檔:行在報告)· 尾版 %s" % (
        len(fams), sc["files"], len(sc["errors"]), len(sc["warnings"]), " · ".join("%s=%s" % (k, (v["tail"] or "—").rsplit("_v", 1)[-1].replace(".py", "")) for k, v in fams.items())),
        "錯誤位置在報告 ast.errors(檔:行)" if sc["errors"] else "")


def stage_sync(via: Path, ctx: dict, do_sync: bool) -> None:
    repo = via.parent
    st = git_state(repo)
    ctx["git_before"] = st
    if st.get("error"):
        say("RED", "③ 同步", st["error"])
        return
    br = st.get(BRANCH) or {}
    behind, ahead = br.get("remote_only"), br.get("local_only")
    txt = "分支 %s · HEAD %s · 比 GitHub 少 %s 個提交 · 多 %s 個沒推 · 改動 %d · 未追蹤 %d" % (st["branch"], st["head"], behind, ahead, st["dirty_tracked"], st["untracked"])
    if not do_sync or not behind:
        say("GREEN" if not behind else "YELLOW", "③ 同步", txt + (" · 已一致" if not behind else " · 這次不同步(--no-sync)"))
        return
    if st["dirty_tracked"]:
        say("YELLOW", "③ 同步", txt + " · 有沒提交的改動 → 不合併(不動你的檔)", "先提交或還原那些改動,再跑本檔(工作樹舊的冊 · 例 VDF_DataHome_SSOT 只有 v0100 · 就不會更新)")
        return
    rc, out = run(["git", "-C", repo, "merge", "--no-edit", "origin/" + BRANCH], timeout=600)
    if rc != 0:
        run(["git", "-C", repo, "merge", "--abort"])
        ctx["sync_error"] = out[-3000:]
        say("RED", "③ 同步", txt + " · 合併沒成功 → 已 merge --abort 還原", "把貼回包上傳給 AI(合併衝突的檔名在 sync_error)")
        return
    st2 = git_state(repo, fetch=False)
    ctx["git_after"] = st2
    say("GREEN", "③ 同步", "合併 origin/%s 成功(不 rebase · 不強推 · 桌機的提交保留)· HEAD %s → %s" % (BRANCH, st["head"], st2["head"]),
        "桌機自己的 %s 個提交還沒推 → 照 ChainShip 上船或 git push(你決定)" % ahead if ahead else "")


def _tail(via: Path, fam: str) -> Path | None:
    folder, prefix = FAMILIES[fam]
    fs = family_files(via, folder, prefix)
    return fs[-1] if fs else None


def stage_vdf(via: Path, ctx: dict) -> None:
    t = _tail(via, "VDF_SystemManager")
    if not t:
        say("RED", "④ VDF ui", "找不到 VDF_SystemManager 尾版")
        return
    rc, out = run([sys.executable, t, "ui"], cwd=t.parent, timeout=1800)
    ctx["vdf"] = {"tail": t.name, "rc": rc, "out_tail": out[-6000:]}
    lamps = re.findall(r"·\s*(GREEN|YELLOW|RED)\s*$", out, re.M)
    if rc == 0:
        lp = vdf_lamp(rc, lamps)
        say(lp, "④ VDF ui", "%s ui · rc 0 · 燈 %s" % (t.name, " ".join(lamps[-6:]) or "—"),
            "頁上有 %s 段 → 看 VDF 頁該段的原因(不是假綠)" % lp if lp != "GREEN" else "")
        return
    d = diagnose(out, via)
    ctx["vdf"]["diagnosis"] = d
    e = d.get("exception") or {}
    say("RED", "④ VDF ui", "%s ui · rc %s · %s: %s" % (t.name, rc, e.get("type", "?"), (e.get("msg") or "")[:160]),
        "AST 定位:" + (d.get("hint") or "見報告 vdf.diagnosis") + " · 把貼回包上傳給 AI")


def _read_vrn_closeout(via: Path) -> tuple:
    cj = via / "VIA_Reports" / "vrn2" / "VRN2_CloseoutUI_latest.json"
    try:
        c = json.loads(cj.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, cj
    state = {"state": c.get("state"), "at": c.get("at") or c.get("ts") or c.get("generated_at"),
             "per_owner": {o: sum(1 for i in c.get("items") or [] if i.get("owner") == o) for o in ("VRN-2", "VCGC", "人工", "資料源")}}
    return state, cj


def stage_vrn(via: Path, ctx: dict, mode: str) -> None:
    if mode == "skip":
        say("GRAY", "⑤ VRN", "這次不跑(--vrn skip)")
        return
    if mode == "status":
        state, cj = _read_vrn_closeout(via)
        ctx["vrn"] = {"mode": "status", "closeout": state, "closeout_file": str(cj)}
        lamp = vrn_status_lamp(state)
        say(lamp, "⑤ VRN", "只讀 VRN-2 自己的收尾收據 · 狀態 %s · 負責方 %s · 時間 %s(不重跑那輪;要重跑 --vrn repair)" % (
            (state or {}).get("state", "沒收據"), (state or {}).get("per_owner"), (state or {}).get("at")),
            "" if lamp == "GREEN" else ("VRN-2 側有待修 → 跑 --vrn repair" if lamp == "RED" else "REVIEW = 看收尾頁人工項原文後 --confirm · DATA_GAP = 外部資料源沒有(已附證據 · VRN-2 側結案)"))
        return
    t = _tail(via, "VRN2_RoundAll")
    if not t:
        say("RED", "⑤ VRN", "找不到 VRN2_RoundAll")
        return
    only = "package,fix,report,closeout,pasteback" if mode == "repair" else "package,preflight,selftest"
    t0 = _dt.datetime.now().timestamp()
    rc, out = run([sys.executable, t, "--root", via, "--only", only, "--no-open"], cwd=t.parent, timeout=14400)
    state, cj = _read_vrn_closeout(via)
    try:
        fresh = cj.stat().st_mtime >= t0 - 1
    except OSError:
        fresh = False
    nxt = [ln for ln in out.splitlines() if ln.startswith("NEXT:")]
    ctx["vrn"] = {"mode": mode, "roundall": t.name, "rc": rc, "closeout": state, "closeout_fresh": fresh, "next": nxt[-1] if nxt else None, "out_tail": out[-4000:]}
    lamp = vrn_lamp(rc, state, fresh)
    say(lamp, "⑤ VRN", "%s %s · rc %s · 收尾 %s %s%s" % (t.name, mode, rc, (state or {}).get("state"), (state or {}).get("per_owner"),
        "" if fresh else " · 收尾收據不是本次寫的(舊的 · 不拿來判綠)"),
        "REVIEW = 看收尾頁人工項原文後 --confirm(只有你打才算)" if state and state["state"] == "REVIEW" else ("把貼回包上傳給 AI" if lamp == "RED" else ""))


def stage_vcgc(via: Path, ctx: dict) -> None:
    t = _tail(via, "CGC_MDL149_Console")
    if not t:
        say("RED", "⑥ VCGC", "找不到 VCGC 主控台")
        return
    rc1, out1 = run([sys.executable, t, "handoff", "check"], cwd=via.parent, timeout=1200)
    kinds = {}
    for k in re.findall(r"^\[RED\] ([A-Z_]+) ", out1, re.M):
        kinds[k] = kinds.get(k, 0) + 1
    rc2, out2 = run([sys.executable, t, "test", "--quick"], cwd=via.parent, timeout=3600)
    m = re.search(r"\[VCGC 全功能串測\] (\w+) · ([^\n]{0,160})", out2)
    reds = re.findall(r"^\s*\[RED\s*\]\s+(\S+)", out2, re.M)
    ctx["vcgc"] = {"handoff_rc": rc1, "handoff_red": kinds, "test_rc": rc2, "test_line": m.group(0) if m else None, "test_red": reds}
    lamp = vcgc_lamp(m.group(1) if m else None, rc2, rc1, kinds)
    say(lamp, "⑥ VCGC", "串測 %s · 紅站 %s · 交接閘 rc %s · 紅 %s" % (
        (m.group(2)[:90] if m else "沒讀到總行"), ", ".join(reds) or "0", rc1, " · ".join("%s %d" % kv for kv in sorted(kinds.items())) or "0"),
        "VCGC 的 closeout_lamp 才是 VCGC 驗收;交接閘紅多為歷史版本沒有測試收據(逐案補或裁定)" if kinds else "")


def graphify_exe() -> tuple:
    """(隔離環境, graphify 可執行檔):VIA_GRAPHIFY_VENV 或 ~/envs/via_graphify(Graphify v0101 一行建的)。"""
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    venv = Path(os.environ.get("VIA_GRAPHIFY_VENV") or (home / "envs" / "via_graphify"))
    return venv, venv / ("Scripts/graphify.exe" if os.name == "nt" else "bin/graphify")


def stage_graphify(via: Path, ctx: dict, floor_gb: float = 0.75, gx_cmd: list | None = None, out_root: Path | None = None) -> None:
    venv, gx = graphify_exe()
    cmd0 = list(gx_cmd) if gx_cmd else [gx]
    out_root = out_root or Path(os.environ.get("VIA_GRAPHIFY_OUT") or (via / "VIA_Reports" / "graphify"))
    if not gx_cmd and not gx.is_file():
        ctx["graphify"] = {"lamp": "GRAY", "venv": str(venv), "why": "no graphify"}
        say("GRAY", "⑦ Graphify", "隔離環境 %s 沒有 graphify → 跳過(不裝 · 不連網)" % venv, "先貼 Graphify v0101 一行(docs/handoff/ai/via_graphify_v0101)建隔離環境,再跑本檔")
        return
    only = [s for s in re.split(r"[,; ]+", os.environ.get("VIA_GRAPHIFY_ONLY", "")) if s]
    env = {"GRAPHIFY_BACKEND": "none", "GRAPHIFY_QUERY_LOG_DISABLE": "1"}
    exa = [x for ex in GRAPHIFY_EXCLUDES for x in ("--exclude", ex)]
    res, t_all = [], time.time()
    for name, rel, gb in GRAPHIFY_SYSTEMS:
        if only and name not in only:
            continue
        src = via / rel
        if not src.is_dir():
            res.append({"system": name, "lamp": "GRAY", "why": "folder missing"})
            continue
        f0 = free_gb()
        if 0 <= f0 < max(floor_gb, 1.0):
            res.append({"system": name, "lamp": "YELLOW", "why": "free RAM %.2f GB < %.2f GB(連啟動都不夠)" % (f0, max(floor_gb, 1.0))})
            print("[YELLOW] ⑦ %s · 可用記憶體 %.2f GB 連啟動都不夠 · 跳過" % (name, f0), flush=True)
            continue
        o = out_root / name
        o.mkdir(parents=True, exist_ok=True)
        print("[計] ⑦ %s · %s · 可用記憶體 %s GB(v0101 估 %d GB · 本版真跑 + 看門狗下限 %.2f GB)· 抽取中" % (name, src, f0, gb, floor_gb), flush=True)
        r = run_watched(cmd0 + ["extract", src, "--code-only", "--max-workers", "2", "--out", o] + exa, env=env, floor_gb=floor_gb, timeout=5400)
        rc, peak, mfree, killed, secs = r["rc"], r["peak_rss_gb"], r["min_free_gb"], r["killed"], r["seconds"]
        tail = r["out"][-1500:]
        if rc == 0:
            r2 = run_watched(cmd0 + ["cluster-only", o, "--no-label"], env=env, floor_gb=floor_gb, timeout=3600)
            rc, killed, secs = r2["rc"], r2["killed"], secs + r2["seconds"]
            peak, mfree = max(peak, r2["peak_rss_gb"]), min(mfree, r2["min_free_gb"]) if mfree >= 0 else r2["min_free_gb"]
            tail += r2["out"][-1500:]
        gj = o / "graphify-out" / "graph.json"
        row = {"system": name, "seconds": secs, "peak_rss_gb": peak, "min_free_gb": mfree, "free_start_gb": f0, "estimate_gb_v0101": gb}
        if killed:
            row.update(lamp="YELLOW", why=killed, rc=rc)
            print("[YELLOW] ⑦ %s · %s · 峰值 RSS %.2f GB · 最低可用 %.2f GB" % (name, killed, peak, mfree), flush=True)
        elif rc != 0 or not gj.is_file():
            row.update(lamp="RED", rc=rc, out_tail=tail)
            print("[RED] ⑦ %s · rc %s · 沒有圖(graphify 的訊息在報告)" % (name, rc), flush=True)
        else:
            try:
                g = json.loads(gj.read_text(encoding="utf-8"))
                nn, ne = len(g.get("nodes") or []), len(g.get("links") or g.get("edges") or [])
            except (OSError, ValueError):
                nn, ne = 0, 0
            if nn <= 0:
                row.update(lamp="RED", why="graph.json has 0 nodes")
                print("[RED] ⑦ %s · graph.json 讀不出節點" % name, flush=True)
            else:
                row.update(lamp="GREEN", nodes=nn, edges=ne, html=str(o / "graphify-out" / "graph.html"), report=str(o / "graphify-out" / "GRAPH_REPORT.md"), graph=str(gj))
                print("[GREEN] ⑦ %s · 節點 %d · 連線 %d · %d 秒 · 峰值 RSS %.2f GB · 最低可用 %.2f GB" % (name, nn, ne, secs, peak, mfree), flush=True)
        res.append(row)
    out_root.mkdir(parents=True, exist_ok=True)
    rec = {"tool": "graphifyy", "engine": "%s %s (graphify stage · v0101 line commands + memory watchdog)" % (NAME, VERSION), "root": str(via),
           "mode": "code-only · GRAPHIFY_BACKEND=none · offline · one graph per system", "excludes": list(GRAPHIFY_EXCLUDES),
           "watchdog": {"floor_gb": floor_gb, "rule": "每秒量可用記憶體與子行程 RSS · 可用 < 下限就殺整棵 · 峰值 / 最低記進每個系統"},
           "systems": res, "seconds": int(time.time() - t_all), "at": _dt.datetime.now().isoformat(timespec="seconds")}
    (out_root / "VIA_Graphify_latest.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    ctx["graphify"] = rec
    lamp = graphify_lamp(res)
    g_ok = [r for r in res if r.get("lamp") == "GREEN"]
    ylw = [r for r in res if r.get("lamp") == "YELLOW"]
    say(lamp, "⑦ Graphify", "綠 %d · 黃 %d · 紅 %d · 灰 %d · %d 秒 · 收據 %s" % (
        len(g_ok), len(ylw), sum(1 for r in res if r.get("lamp") == "RED"), sum(1 for r in res if r.get("lamp") == "GRAY"), rec["seconds"], out_root / "VIA_Graphify_latest.json"),
        ("看門狗中止的:%s → 關掉別的程式再跑 `$env:VIA_GRAPHIFY_ONLY='%s'`(或 --graphify-floor-gb 調低 · 風險自負)" % (
            " · ".join("%s(%s)" % (r["system"], r.get("why")) for r in ylw), ",".join(r["system"] for r in ylw))) if ylw else "")


def stage_vqg(via: Path, ctx: dict) -> None:
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    dl = home / "Downloads" if (home / "Downloads").is_dir() else Path(tempfile.gettempdir())
    files, how = fetch_set(via, VQG_FILES, dl / ("VIA_Settle_" + VERSION) / "VQG")
    info = {"files_from": how}
    ctx["vqg"] = info
    if not files:
        say("RED", "⑧ VQG", "取不到 VQG v0104 / v0105 · %s" % how, "git -C <倉> fetch origin %s 後再跑;SHA 不符 = 檔被改過,不跑" % BRANCH)
        return
    v0105 = [p for p in files if p.name.endswith("_v0105.py")][0]
    py = find_python_with(("duckdb", "polars"))
    info["python"] = str(py) if py else None
    if not py:
        say("RED", "⑧ VQG", "找不到有 duckdb + polars 的 Python(VQG 不 pip)", "VCGC:via-install duckdb polars(或 $env:VQG_PY 指定)")
        return
    rc0, so0, _ = run2(["git", "-C", via.parent, "ls-tree", "--name-only", "origin/" + BRANCH, "VeritasIntelligenceAnalytics/functional modules/VDF/"], timeout=120)
    branch_book = None
    if rc0 == 0:
        names = sorted((n for n in so0.splitlines() if re.search(r"VDF_DataHome_SSOT_v\d{4}\.json$", n)), key=vnum)
        if names:
            data = git_show_bytes(via.parent, "origin/" + BRANCH, names[-1])
            if data:
                branch_book = (Path(names[-1]).name, data.decode("utf-8", "replace"))
    cands = vdf_root_candidates(via, branch_book)

    def doctor_fn(p):
        rc, so, se = run2([py, v0105, "doctor", "--root", p, "--via-root", via], cwd=v0105.parent, timeout=900)
        try:
            return json.loads(so[so.index("{"):]) if "{" in so else {"verdict": "DOCTOR_RC_%s" % rc, "error": (se or so)[-300:]}
        except ValueError:
            return {"verdict": "DOCTOR_UNREADABLE", "error": (se or so)[-300:]}
    chosen, table = pick_vdf_root(cands, doctor_fn)
    info.update(candidates=table, chosen=chosen, branch_book=branch_book[0] if branch_book else None)
    root = Path(chosen["path"]) if chosen else next((Path(c["path"]) for c in table if c.get("exists")), None)
    rec_path = via / "VIA_Reports" / "vqg" / "VQG_Closeout_latest.json"
    rc, so, se = run2([py, v0105, "closeout", "--via-root", via] + (["--root", root] if root else []), cwd=v0105.parent, timeout=1800)
    info.update(closeout_rc=rc, closeout_out=(so + se)[-3000:])
    try:
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        fresh = rec_path.stat().st_mtime >= time.time() - 3600
    except (OSError, ValueError):
        rec, fresh = None, False
    info["receipt"] = {"lamp": (rec or {}).get("lamp"), "vdf_root": (rec or {}).get("vdf_root"), "steps": [(s.get("step"), s.get("lamp")) for s in (rec or {}).get("steps") or []], "fresh": fresh}
    lamp = (rec or {}).get("lamp") if (rec and fresh) else "RED"
    lamp = lamp if lamp in RANK else "RED"
    probed = ["%s → %s(%s 日線 %s)" % (Path(c["path"]).name or c["path"], c.get("verdict") or ("不在" if not c.get("exists") else "?"), c["how"].split("(")[0][:28], c.get("daily_price_files", "-")) for c in table]
    if chosen:
        say(lamp, "⑧ VQG", "VDF 家 %s(%s)· closeout rc %s · 收據 %s · 步 %s" % (
            chosen["path"], chosen["how"], rc, (rec or {}).get("lamp"), " ".join("%s=%s" % (str(s)[:6], l) for s, l in info["receipt"]["steps"])),
            "YELLOW = 曆是 VQG 從 VDF 日線推的 · 要 GREEN 是 VDF 線出 market / session_index / available_on" if lamp == "YELLOW" else ("看收據 steps" if lamp == "RED" else ""))
    elif not any(c.get("exists") for c in table) and (rec or {}).get("lamp") == "GRAY":
        say("GRAY", "⑧ VQG", "這台機器沒有任何 VDF 家(容器 / CI)· 只驗了自測 · 收據 GRAY · 候選:%s" % " / ".join(probed),
            "桌機才有 VDF 庫;家不在清單 → $env:VQG_VDF_ROOT 指定")
    else:
        say("RED", "⑧ VQG", "每個 VDF 家都沒有日線 parquet(ticker + date + adj_close):%s · closeout rc %s" % (" / ".join(probed), rc),
            "VDF 線:跑 VDF 日線回填(ENG054 · 寫到 <db_home>\\output_hub\\mega\\tw_daily_prices_<時間>.parquet)後再跑本檔;家不在清單 → $env:VQG_VDF_ROOT 指定")


def stage_agentos(via: Path, ctx: dict) -> None:
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    dl = home / "Downloads" if (home / "Downloads").is_dir() else Path(tempfile.gettempdir())
    files, how = fetch_set(via, (AGENTOS_FILE,), dl / ("VIA_Settle_" + VERSION))
    info = {"file_from": how}
    ctx["agentos"] = info
    if not files:
        say("RED", "⑨ Agent OS", "取不到 VIA_AgentOS_v0102 · %s" % how, "git -C <倉> fetch origin %s 後再跑;SHA 不符 = 檔被改過,不跑" % BRANCH)
        return
    f = files[0]
    py = Path(os.environ.get("VIA_AGENTOS_PY") or sys.executable)
    out = via / "VIA_Reports" / "agent_os"
    out.mkdir(parents=True, exist_ok=True)
    repo = via.parent
    runs = {}
    for key, args in (("selftest", ["selftest"]), ("skills", ["skills", "test"]), ("status", ["status", "--repo-root", repo]), ("vcgc_status", ["vcgc-status", "--repo-root", repo])):
        rc, so, se = run2([py, f, *args], cwd=f.parent, timeout=900)
        (out / ("VIA_AgentOS_v0102_%s.json" % key)).write_text(so, encoding="utf-8")
        runs[key] = {"rc": rc, "stderr_tail": se[-600:]}
        if key == "selftest":
            try:
                report = json.loads(so[so.index("{"):]) if "{" in so else None
            except ValueError:
                report = None
    cls = agentos_classify(report, os.name == "nt")
    info.update(python=str(py), runs=runs, selftest=cls, out_dir=str(out))
    others_red = any(runs[k]["rc"] != 0 for k in ("skills", "status", "vcgc_status"))
    lamp = worst(cls["lamp"], "RED" if others_red else "GREEN")
    html = None
    if lamp != "RED":
        html = dl / ("VIA_AgentOS_Dashboard_v0102_%s.html" % _dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
        rcd, _, sed = run2([py, f, "dashboard", "--root", via, "--out", html, "--label", "VIA desktop"], cwd=f.parent, timeout=900)
        if rcd != 0 or not html.is_file():
            info["dashboard_error"] = sed[-600:]
            html = None
            lamp = worst(lamp, "YELLOW")
        info["dashboard"] = str(html) if html else None
    say(lamp, "⑨ Agent OS", "selftest %d 項 · 失敗 %d 錯誤 %d(環境 N/A %d · 真的 %d)· skills rc %s · status rc %s · vcgc-status rc %s · 儀表板 %s" % (
        cls["tests_run"], cls["failures"], cls["errors"], len(cls["known_env"]), len(cls["unknown"]), runs["skills"]["rc"], runs["status"]["rc"], runs["vcgc_status"]["rc"], html or "沒產生"),
        ("環境 N/A = %s" % cls["known_env"][0]["why"]) if cls["known_env"] and not cls["unknown"] else ("真的失敗在 VIA_Reports/agent_os/VIA_AgentOS_v0102_selftest.json 的 details → 貼回包上傳給 AI" if cls["unknown"] else ""))
    if html and os.name == "nt" and os.environ.get("VIA_NO_OPEN") != "1":
        try:
            os.startfile(str(html))                          # noqa: S606 — 只開本機剛寫的 HTML
        except OSError:
            info["dashboard_open"] = "沒開成 · 自己開"


def stage_report(via: Path, ctx: dict) -> Path:
    out_dir = via / "VIA_Reports" / "settle"
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx["log"] = LOG
    ctx["at"] = _dt.datetime.now().isoformat(timespec="seconds")
    j = out_dir / "SETTLE_latest.json"
    j.write_text(json.dumps(ctx, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    md = ["# %s %s · %s" % (NAME, VERSION, ctx["at"]), "", "| 燈 | 步驟 | 內容 | 下一步 |", "|---|---|---|---|"]
    md += ["| %s | %s | %s | %s |" % (x["lamp"], x["step"], x["text"].replace("|", "/"), x["next"].replace("|", "/")) for x in LOG]
    d = (ctx.get("vdf") or {}).get("diagnosis")
    if d:
        md += ["", "## VDF traceback · AST 定位", "", "例外:`%s`" % d.get("exception"), "", "提示:" + d.get("hint", ""), ""]
        md += ["- `%s:%d` · %s · `%s`" % (f["file"], f["line"], f.get("def"), f.get("src")) for f in d.get("frames", [])]
    cands = (ctx.get("vqg") or {}).get("candidates")
    if cands:
        md += ["", "## VQG · VDF 家候選(試的順序)", "", "| 家 | 來源 | 在 | doctor | 日線檔 |", "|---|---|---|---|---|"]
        md += ["| %s | %s | %s | %s | %s |" % (c["path"], c["how"], "是" if c.get("exists") else "否", c.get("verdict") or "—", c.get("daily_price_files", "—")) for c in cands]
    (out_dir / "SETTLE_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    dl = home / "Downloads" if (home / "Downloads").is_dir() else Path(tempfile.gettempdir())
    zp = dl / ("VIA_Settle_%s.zip" % _dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(j, "settle/SETTLE_latest.json")
        z.write(out_dir / "SETTLE_latest.md", "settle/SETTLE_latest.md")
        for rel in ("vrn2/VRN2_CloseoutUI_latest.json", "vrn2/VRN2_RoundAll_latest.json", "vdf/VDF_UI_MANIFEST.json", "graphify/VIA_Graphify_latest.json",
                    "vqg/VQG_Closeout_latest.json", "agent_os/VIA_AgentOS_v0102_selftest.json", "agent_os/VIA_AgentOS_v0102_skills.json",
                    "agent_os/VIA_AgentOS_v0102_status.json", "agent_os/VIA_AgentOS_v0102_vcgc_status.json"):
            p = via / "VIA_Reports" / rel
            if p.is_file():
                z.write(p, rel)
    worst_lamp = "RED" if any(x["lamp"] == "RED" for x in LOG) else "YELLOW" if any(x["lamp"] == "YELLOW" for x in LOG) else "GREEN"
    say(worst_lamp, "⑩ 報告", "%s · %s · 貼回包 %s" % (j, out_dir / "SETTLE_latest.md", zp), "把貼回包上傳給 AI" if worst_lamp != "GREEN" else "")
    print("NEXT: [%s] %s · 貼回包 %s" % (worst_lamp, NAME, zp), flush=True)
    return zp


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    with tempfile.TemporaryDirectory(prefix="via_settle_") as td:
        d = Path(td)
        (d / "Fam_v0100.py").write_text("def a():\n    return 1\nPRIOR = None\n", encoding="utf-8")
        (d / "Fam_v0101.py").write_text("PRIOR = None\n\ndef go():\n    return PRIOR.b()\n\ndef __getattr__(n):\n    return getattr(PRIOR, n)\n", encoding="utf-8")
        (d / "Fam_v0102.py").write_text("def b():\n    return 2\n", encoding="utf-8")
        (d / "Bad_v0100.py").write_text("def x(:\n", encoding="utf-8")
        tb = ('Traceback (most recent call last):\n  File "%s", line 4, in go\n    return PRIOR.b()\n'
              '  File "%s", line 7, in __getattr__\n    return getattr(PRIOR, n)\n'
              "AttributeError: module 'Fam_prior' has no attribute 'b'\n") % (d / "Fam_v0101.py", d / "Fam_v0101.py")
        g = diagnose(tb)
        chk("① traceback → AttributeError · 屬性 b · 兩框 · AST 定位到 go / __getattr__",
            g["exception"]["type"] == "AttributeError" and g.get("attr") == "b" and [f["def"].split()[0] for f in g["frames"]] == ["go", "__getattr__"])
        chk("② 同家族追屬性:b 只在 v0102 定義 · v0101 L4 先讀(轉手 1 次)→ 提示點名",
            g["trace"]["defined_in"] == ["Fam_v0102.py"] and "Fam_v0101.py:L4" in g["trace"]["used_before_defined"] and "v0102" in g["hint"], g["hint"])
        g2 = diagnose("RecursionError: maximum recursion depth exceeded\n")
        chk("③ RecursionError → 遞迴提示", g2["recursion"] and "遞迴" in g2["hint"])
        (d / "Esc_v0100.py").write_text('"""a \\d b"""\n', encoding="utf-8")
        sc = ast_scan([d / "Fam_v0100.py", d / "Bad_v0100.py", d / "Esc_v0100.py"])
        chk("④ AST 全景:語法錯抓到檔與行(不執行)· 無效跳脫記成警告(檔:行)不算錯", len(sc["errors"]) == 1 and sc["errors"][0]["kind"] == "SYNTAX"
            and sc["errors"][0]["line"] == 1 and len(sc["warnings"]) == 1 and sc["warnings"][0]["file"] == "Esc_v0100.py", sc["warnings"])
        chk("⑤ git 計數解析:'2\\t719' → (2, 719) · 壞輸入 → (None, None)", parse_ahead_behind("2\t719\n") == (2, 719) and parse_ahead_behind("x") == (None, None))
        chk("⑥ 警告不當例外:SyntaxWarning 行被略過", diagnose("<unknown>:3: SyntaxWarning: invalid escape\nValueError: boom\n")["exception"]["type"] == "ValueError")
        via = d / "repo" / "VeritasIntelligenceAnalytics"
        (via / "functional modules").mkdir(parents=True)
        (via / "supportive modules").mkdir(parents=True)
        chk("⑦ 找根:--root 給倉根或 VIA 根都認得", find_root(str(d / "repo")) == via and find_root(str(via)) == via)
        rc, out = run([sys.executable, "-c", "import sys;print('x');sys.exit(3)"])
        chk("⑧ 子行程:rc 與輸出都拿到 · 找不到程式回 127", rc == 3 and "x" in out and run(["__no_such_cmd__"])[0] == 127)
        # ---- v0102 新增
        chk("⑭ 記憶體:meminfo 解析 8 GB · 量不到回 -1 · free_gb() 是數字", parse_meminfo_gb("MemTotal: 16 kB\nMemAvailable: 8388608 kB\n") == 8.0
            and parse_meminfo_gb("") == -1.0 and isinstance(free_gb(), float))
        win_err = {"ok": False, "tests_run": 48, "failures": 0, "errors": 1, "details": [{"test": "t_nofollow", "kind": "ERROR", "detail": "OSError: [WinError 1314] A required privilege is not held by the client"}]}
        other = {"ok": False, "tests_run": 48, "failures": 1, "errors": 0, "details": [{"test": "t_x", "kind": "FAIL", "detail": "AssertionError: 1 != 2"}]}
        mixed = dict(win_err, details=win_err["details"] + other["details"])
        chk("⑮ Agent OS 分類:ok → GREEN · Windows 只有 symlink 權限項 → YELLOW · 同樣訊息在非 Windows → RED · 混有真失敗 → RED · 沒 JSON → RED",
            agentos_classify({"ok": True, "tests_run": 48, "details": []}, True)["lamp"] == "GREEN" and agentos_classify(win_err, True)["lamp"] == "YELLOW"
            and agentos_classify(win_err, False)["lamp"] == "RED" and agentos_classify(mixed, True)["lamp"] == "RED" and agentos_classify(None, True)["lamp"] == "RED"
            and len(agentos_classify(mixed, True)["known_env"]) == 1 and len(agentos_classify(mixed, True)["unknown"]) == 1)
        vdf = via / "functional modules" / "VDF"
        vdf.mkdir()
        home_a, home_b = d / "home_a", d / "home_b"
        home_a.mkdir()
        home_b.mkdir()
        (vdf / "VDF_DataHome_SSOT_v0100.json").write_text(json.dumps({"homes": [{"id": "ws", "db_home": str(home_a)}]}), encoding="utf-8")
        branch = ("VDF_DataHome_SSOT_v0101.json", json.dumps({"homes": [{"id": "ws", "db_home": str(home_b)}, {"id": "ws2", "db_home": str(home_a)}]}))
        old_env = os.environ.pop("VQG_VDF_ROOT", None)
        cands = vdf_root_candidates(via, branch)
        os.environ["VQG_VDF_ROOT"] = str(d / "env_home")
        cands_env = vdf_root_candidates(via, branch)
        if old_env is None:
            os.environ.pop("VQG_VDF_ROOT", None)
        else:
            os.environ["VQG_VDF_ROOT"] = old_env
        chk("⑯ VDF 家候選:分支 v0101 的家排前(B · A)· 工作樹 v0100 的 A 不重複 · 最後是倉內 output_hub 接點 · 環境變數最優先",
            [Path(c["path"]) for c in cands] == [home_b, home_a, vdf / "output_hub"] and "分支" in cands[0]["how"] and Path(cands_env[0]["path"]) == d / "env_home", [c["how"][:20] for c in cands])
        calls = []

        def fake_doctor(p):
            calls.append(Path(p).name)
            return {"verdict": "NO_DAILY_PRICES", "daily_price_files": 0} if Path(p) == home_a else {"verdict": "DERIVE_READY", "daily_price_files": 2}
        chosen, table = pick_vdf_root(cands_env, fake_doctor)
        first_calls = list(calls)
        chosen2, _ = pick_vdf_root([{"path": str(home_a), "how": "x"}], fake_doctor)
        chk("⑰ 選家:不在的家不探(env_home)· 第一個有日線的家被選(B · 2 檔)· 後面的家標「未探」· 全沒有 → None",
            chosen is not None and Path(chosen["path"]) == home_b and first_calls == ["home_b"] and table[0]["exists"] is False
            and any("未探" in str(r.get("verdict")) for r in table) and chosen2 is None, (first_calls, chosen2))
        chk("⑱ SHA-256 CRLF 正規化:CRLF 與 LF 同一個雜湊 · 與釘住格式(64 hex)相同",
            sha_lf(b"a\r\nb\r\n") == sha_lf(b"a\nb\n") and len(sha_lf(b"x")) == 64 and sha_lf(b"a\r\nb") != sha_lf(b"a\nb\n"))
        slow = d / "slow.py"
        slow.write_text("import time,sys\nprint('go',flush=True)\ntime.sleep(30)\n", encoding="utf-8")
        quick = d / "quick.py"
        quick.write_text("print('hi')\n", encoding="utf-8")
        r_ok = run_watched([sys.executable, quick], floor_gb=0.0, timeout=60, poll=0.2)
        r_to = run_watched([sys.executable, slow], floor_gb=0.0, timeout=1, poll=0.2)
        r_mem = run_watched([sys.executable, slow], floor_gb=10 ** 6, timeout=60, poll=0.2)
        chk("⑲ 看門狗:正常 rc 0 + 輸出 · 逾時 1 秒殺掉 rc 124 · 可用記憶體 < 下限(設成 100 萬 GB)立刻殺 rc 137 · 都在 10 秒內",
            r_ok["rc"] == 0 and "hi" in r_ok["out"] and r_to["rc"] == 124 and "逾時" in (r_to["killed"] or "") and r_mem["rc"] == 137 and "記憶體" in (r_mem["killed"] or "")
            and r_to["seconds"] <= 10 and r_mem["seconds"] <= 10, (r_ok["rc"], r_to["rc"], r_mem["rc"], r_to["seconds"], r_mem["seconds"]))
        fake_gx = d / "fake_graphify.py"
        fake_gx.write_text("import sys,json,pathlib\nargs=sys.argv[1:]\nif args[0]=='extract':\n    o=pathlib.Path(args[args.index('--out')+1])/'graphify-out'\n    o.mkdir(parents=True,exist_ok=True)\n"
                           "    (o/'graph.json').write_text(json.dumps({'nodes':[1,2,3],'links':[[1,2]]}))\nelif args[0]=='cluster-only':\n    pass\nelse:\n    sys.exit(9)\nprint('fake graphify',args[0])\n", encoding="utf-8")
        (via / "functional modules" / "VRN2").mkdir()
        (via / "supportive modules" / "registry").mkdir()
        gout = d / "gout"
        old_only = os.environ.get("VIA_GRAPHIFY_ONLY")
        os.environ["VIA_GRAPHIFY_ONLY"] = "VRN,VCGC,VRN_Shared"
        n0 = len(LOG)
        c_g = {}
        stage_graphify(via, c_g, floor_gb=0.0, gx_cmd=[sys.executable, fake_gx], out_root=gout)
        if old_only is None:
            os.environ.pop("VIA_GRAPHIFY_ONLY", None)
        else:
            os.environ["VIA_GRAPHIFY_ONLY"] = old_only
        g_lamp, g_sys = LOG[-1]["lamp"], {r["system"]: r["lamp"] for r in c_g["graphify"]["systems"]}
        del LOG[n0:]
        chk("⑳ Graphify 段(假 graphify):VRN · VCGC 綠(graph.json 3 節點)· VRN_Shared 夾不在 → 灰 · VDF 沒點名不跑 · 收據寫在 out · 總燈 GREEN",
            g_lamp == "GREEN" and g_sys == {"VRN": "GREEN", "VCGC": "GREEN", "VRN_Shared": "GRAY"} and (gout / "VIA_Graphify_latest.json").is_file()
            and c_g["graphify"]["systems"][0].get("nodes") == 3, (g_lamp, g_sys))
        chk("㉑ Graphify 判燈:有紅 → RED · 全黃 → YELLOW · 綠 + 黃 → YELLOW · 綠 + 灰 → GREEN · 空 → YELLOW",
            graphify_lamp([{"lamp": "GREEN"}, {"lamp": "RED"}]) == "RED" and graphify_lamp([{"lamp": "YELLOW"}]) == "YELLOW"
            and graphify_lamp([{"lamp": "GREEN"}, {"lamp": "YELLOW"}]) == "YELLOW" and graphify_lamp([{"lamp": "GREEN"}, {"lamp": "GRAY"}]) == "GREEN" and graphify_lamp([]) == "YELLOW")
        chk("㉒ VRN status 判燈:沒收據 → YELLOW · VRN-2 有待修 → RED · PASS → GREEN · DATA_GAP / REVIEW → YELLOW",
            vrn_status_lamp(None) == "YELLOW" and vrn_status_lamp({"state": "OPEN", "per_owner": {"VRN-2": 2}}) == "RED"
            and vrn_status_lamp({"state": "PASS", "per_owner": {"VRN-2": 0}}) == "GREEN" and vrn_status_lamp({"state": "DATA_GAP", "per_owner": {"VRN-2": 0}}) == "YELLOW")
    if shutil.which("git"):
        with tempfile.TemporaryDirectory(prefix="via_settle_git_") as tg:
            g = Path(tg)
            gx = lambda *a, cwd=None: run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd)  # noqa: E731
            gx("init", "-q", "--bare", "-b", BRANCH, str(g / "remote.git"))
            gx("clone", "-q", str(g / "remote.git"), str(g / "up"))
            up = g / "up"
            for sub in ("VeritasIntelligenceAnalytics/functional modules", "VeritasIntelligenceAnalytics/supportive modules"):
                (up / sub).mkdir(parents=True)
                (up / sub / "k.txt").write_bytes(b"1\n")
            pin_rel = "functional modules/pinned_v0100.py"
            (up / "VeritasIntelligenceAnalytics" / pin_rel).write_bytes(b"print(1)\r\n")
            gx("checkout", "-q", "-b", BRANCH, cwd=up)
            gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "a", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            gx("clone", "-q", "-b", BRANCH, str(g / "remote.git"), str(g / "desk"))
            (up / "new.txt").write_bytes(b"n\n"); gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "b", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            desk_via = g / "desk" / "VeritasIntelligenceAnalytics"
            (g / "desk" / "VeritasIntelligenceAnalytics" / "functional modules" / "k.txt").write_bytes(b"dirty\n")
            c1, n1 = {}, len(LOG)
            stage_sync(desk_via, c1, True)
            refused = LOG[-1]["lamp"] == "YELLOW" and "不合併" in LOG[-1]["text"] and not (g / "desk" / "new.txt").exists()
            run(["git", "-C", g / "desk", "checkout", "--", "."])
            c2 = {}
            stage_sync(desk_via, c2, True)
            merged = LOG[-1]["lamp"] == "GREEN" and (g / "desk" / "new.txt").is_file() and (c2.get("git_after") or {}).get(BRANCH, {}).get("remote_only") == 0
            del LOG[n1:]
            pinned = {pin_rel: sha_lf(b"print(1)\n")}
            f_tree, how_tree = fetch_set(desk_via, (pin_rel,), g / "dl", pinned)
            (desk_via / pin_rel).write_bytes(b"print(2)\n")
            f_br, how_br = fetch_set(desk_via, (pin_rel,), g / "dl", pinned)
            f_bad, how_bad = fetch_set(desk_via, (pin_rel,), g / "dl", {pin_rel: "0" * 64})
        chk("⑩ 同步(假遠端 · 真 git):有沒提交的改動 → 不合併、不動檔;乾淨 → 合併後跟遠端一致(少 0)", refused and merged, (refused, merged))
        chk("㉓ 取檔(釘 SHA):工作樹 SHA 對 → 就地用;工作樹被改 → 從分支 origin 取到 dl 並 LF 化;分支 SHA 也不對 → None 不跑",
            f_tree and f_tree[0] == desk_via / pin_rel and "工作樹" in how_tree and f_br and f_br[0] == g / "dl" / "pinned_v0100.py" and "分支" in how_br
            and f_bad is None and "不是釘住的" in how_bad, (how_tree[:12], how_br[:12], how_bad[:40]))
    chk("⑪ VDF 判燈:rc 0 + 頁上 YELLOW → YELLOW(不升綠)· 有 RED → RED · rc 1 → RED · 全綠 → GREEN",
        vdf_lamp(0, ["GREEN", "YELLOW"]) == "YELLOW" and vdf_lamp(0, ["GREEN", "RED"]) == "RED" and vdf_lamp(1, ["GREEN"]) == "RED" and vdf_lamp(0, ["GREEN"]) == "GREEN")
    st_pass = {"state": "PASS", "per_owner": {"VRN-2": 0}}
    chk("⑫ VRN 判燈:舊 PASS + 本次逾時 rc 124 → RED · 舊 PASS + rc 0(check 模式不重寫)→ YELLOW · 本次 PASS → GREEN · 本次 REVIEW → YELLOW · VRN-2 有待修 → RED",
        vrn_lamp(124, st_pass, False) == "RED" and vrn_lamp(0, st_pass, False) == "YELLOW" and vrn_lamp(0, st_pass, True) == "GREEN"
        and vrn_lamp(2, {"state": "REVIEW", "per_owner": {"VRN-2": 0}}, True) == "YELLOW" and vrn_lamp(2, {"state": "OPEN", "per_owner": {"VRN-2": 1}}, True) == "RED")
    chk("⑬ VCGC 判燈:串測 GREEN + 交接閘紅 → RED · 交接 rc 1 → RED · 沒讀到總行 → RED · 串測 YELLOW + 交接乾淨 → YELLOW · 都綠 → GREEN",
        vcgc_lamp("GREEN", 0, 0, {"EVIDENCE_INVALID": 1}) == "RED" and vcgc_lamp("GREEN", 0, 1, {}) == "RED" and vcgc_lamp(None, 0, 0, {}) == "RED"
        and vcgc_lamp("YELLOW", 2, 0, {}) == "YELLOW" and vcgc_lamp("GREEN", 0, 0, {}) == "GREEN" and vcgc_lamp("GREEN", 1, 0, {}) == "RED")
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    dirs = set(re.findall(r'"VIA_Reports"\s*/\s*"(\w+)"', body))
    chk("⑨ 橋在 · 不強推 · 不 rebase · 不 push · 不 pip · 不寫他系統的檔(VIA_Reports 只碰 settle / agent_os / graphify;vrn2 / vdf / vqg 只讀)",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "--force" not in body and "rebase\"" not in body and "push\"" not in body
        and "\"pip\"" not in body and dirs <= {"settle", "agent_os", "graphify", "vrn2", "vdf", "vqg"}, sorted(dirs))
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", NAME, VERSION, len(ok), bad), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):       # Windows 主控台不是 UTF-8 時也能印中文(印不出就照原樣)
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="%s_%s" % (NAME, VERSION), description="全景檢視 → 同步 → VDF ui(AST 定位)→ VRN 狀態 → VCGC 驗 → Graphify(看門狗)→ VQG(VDF 多家探根)→ Agent OS → 報告 · 各系統只經自己的入口")
    ap.add_argument("--root")
    ap.add_argument("--only", default=",".join(STAGES))
    ap.add_argument("--no-sync", action="store_true")
    ap.add_argument("--vrn", choices=("status", "repair", "check", "skip"), default="status")
    ap.add_argument("--graphify-floor-gb", type=float, default=0.75)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    via = find_root(a.root)
    if via is None:
        say("RED", "⓪ VIA 根", "找不到(查過 --root · VIA_ROOT · 本檔所在 · OneDrive\\Documents\\movies-dataset)", "加 --root <倉根>")
        return 1
    say("GREEN", "⓪ VIA 根", str(via))
    only = [s.strip() for s in a.only.split(",") if s.strip()]
    ctx = {"tool": NAME + " " + VERSION, "root": str(via), "branch": BRANCH}
    if "scan" in only:
        stage_scan(via, ctx)
    if "sync" in only:
        stage_sync(via, ctx, not a.no_sync)
    if "vdf" in only:
        stage_vdf(via, ctx)
    if "vrn" in only:
        stage_vrn(via, ctx, a.vrn)
    if "vcgc" in only:
        stage_vcgc(via, ctx)
    if "graphify" in only:
        stage_graphify(via, ctx, a.graphify_floor_gb)
    if "vqg" in only:
        stage_vqg(via, ctx)
    if "agentos" in only:
        stage_agentos(via, ctx)
    if "report" in only:
        stage_report(via, ctx)
    return 1 if any(x["lamp"] == "RED" for x in LOG) else 2 if any(x["lamp"] == "YELLOW" for x in LOG) else 0


if __name__ == "__main__":
    sys.exit(main())
