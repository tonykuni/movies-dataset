#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC_StartupEngine_v0100 — 啟動引擎正本，只此一份。

擁有者是 VCGC（L20 唯一對接口 · L30 同一套啟動邏輯只寫一處）。
新系統要啟動引擎，從這裡取外掛，不另起第二套排程器（L05 · L26）。

政策截取（唯讀 tonykuni/movies-dataset，本檔不寫回 GitHub）：
  L16 誠實四態。沒有 System Manager = ABSENT，不是壞掉，不補一顆。
  L20 VCGC 是政策與註冊的唯一對接口，不是其他系統的主人。
  L31 引擎以冊綁定，尾版一出合約追碼；外掛只認管理器，不認路徑死結。
  L98：最頂端各自成庫的是 VRN、VDF、VIA。律冊沒有 L120 這條獨立律。
  LL120 是取號撞號的教訓，不是「沒有誰管誰」。
  批692B：每一道 py 都帶加速器。動詞未滿 100% 不放行。
  L09：加速器只認 VeritasCeleritas，鎖冊 v1141。
  網路只認 VeritasAegisNexus，鎖冊 v1652，引擎版 1.65.2。
  SUP_MDL737 / SUP_MDL740 是橋，不是這兩個工具，也不把橋的尾版號當成工具版本。
  本檔不複製本體。覆蓋面未滿 1.0 不放行。
  L05 / L20：不 import 他系統，不另起第二套啟動器，不寫他系統的樹。本引擎只吃 JSON 冊。
  L50：禁庫只有 TA-Lib 與 talib。以及其他是六種動作，不是第二份套件名單。
  失敗即停，日誌留下已完成的節點。下一手從日誌續，不把已完成的歸零重跑。

加速器標記（AST 與啟動包裝都認這一行）：
  VIA:PY-ACCEL:v0100
"""

from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋（批102；樹上沒有就誠實缺席，不另造本體） =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Iterable

ENGINE_ID = "VCGC_StartupEngine_v0100"
ACCEL_MARK = "VIA:PY-ACCEL:v0100"
ACCEL_BRIDGE_MARK = "[VIA:ACCEL-BRIDGE:v0100]"
ACCEL_MODULE = "VIA_SuperAccel_Module"
ACCEL_STEM = "SUP_MDL737_SuperAccelModule"
NET_BRIDGE_STEM = "SUP_MDL740_NetUnified"
LOCK_BOOK = "VIA_ToolVersion_Lock_v0100.json"
ACCEL_TOOL = "VeritasCeleritas"
ACCEL_LOCK_VERSION = "v1141"
ACCEL_LOCK_REL = "VeritasIntelligenceAnalytics/supportive modules/VeritasCeleritas_v1141.py"
ACCEL_LOCK_SHA = "ddcb5460bf64b0d8d773a8878cca1b4e642eac977f2d7aa2b0e267745d1ecea5"
NET_TOOL = "VeritasAegisNexus"
NET_LOCK_VERSION = "v1652"
NET_ENGINE_VERSION = "1.65.2"
NET_LOCK_REL = "VeritasIntelligenceAnalytics/supportive modules/network/VeritasAegisNexus_v1652.py"
NET_LOCK_SHA = "c2f401071adfde3c8e1eb903a3ef7923ce3974b6b5eb40960b9ea345ac4181ab"
TALIB_LIBS = ("TA-Lib", "talib")
TALIB_ACTIONS = ("install", "import", "load", "revive", "route", "benchmark_as_active")
QUANTGUARD = "VDF_ENG086_QuantGuardOneBridge_v0101"
# 省額度檢視。主人是既有動詞 token（盤點站 V-token），不是這支引擎另造的尺。
TOKEN_VERB = "token"
TOKEN_STATION = "V-token"
TOKEN_TOOL = "CGC_MDL158_VIAPanoramaAuditRepair_v0121"
# 貼給任何 AI 的只有這一行。下面六條是這頁的尺，不跟著貼。
TOKEN_CUE = "先呼叫工具再回答。只留路徑、sha或大小、一行錯誤、決定。十處無索引即缺席不拉取。24小時內不重讀。動詞token站V-token不另造尺。"
TOKEN_RULES: tuple[tuple[str, str], ...] = (
    ("tool-first", "要看就先呼叫工具。不要請人把全文貼進對話。"),
    ("index-only", "先要索引。全文只取索引點到的那幾行。"),
    ("reply-thin", "回覆只留路徑、sha 或大小、一行錯誤、決定。"),
    ("absent", "十處沒有索引就是缺席。不拉取、不猜測。"),
    ("reuse", "24 小時內已看過的索引不重讀。"),
    ("owner", "動詞仍是 token，站仍是 V-token。不另造尺。"),
)
INVENTORY_BOOK = "VIA_VCGC_FunctionInventory_SSOT_v0299.json"
INVENTORY_STATIONS = 551
INVENTORY_REUSE_HOURS = 24
WORKFLOW_BOOK = "VIA_Workflow_VRN_SSOT_v0122.json"
WORKFLOW_COUNT = 21
FASTRUN_TAIL = "VIA_FastRun_v0102.py"
FASTRUN_BEAT_SENTINEL = 10 ** 9
WAIT_SAFE_SEC = 2_000_000
# (鍵, 表面名, 便宜讀法)。沒有索引就不拉全文。
SUPPORT_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("mcp", "MCP", "只留工具回傳的索引與錯誤行，不把整包再貼一次。"),
    ("pc", "本機檔", "只讀路徑、大小、時間。不開全文。"),
    ("github", "GitHub", "只對檔名、sha、尾版。不把倉拉進來。"),
    ("claude", "Claude", "對話只留最後一則摘要。沒有索引就是缺席。"),
    ("chatgpt", "ChatGPT", "對話只留最後一則摘要。沒有索引就是缺席。"),
    ("grok", "Grok", "對話只留最後一則摘要。沒有索引就是缺席。"),
    ("manus", "Manus", "對話只留最後一則摘要。沒有索引就是缺席。"),
    ("gemini", "Gemini", "對話只留最後一則摘要。沒有索引就是缺席。"),
    ("perplexity", "Perplexity", "對話只留最後一則摘要。沒有索引就是缺席。"),
    ("copilot", "Copilot", "對話只留最後一則摘要。沒有索引就是缺席。"),
)
SCHEMA = "vcgc.startup-engine/1"
SELFTEST_TOTAL = 65
# 2026-11-24 已寫進盤點冊的站。這支引擎不另開站、不把本體塞進備份 zip。
TODAY_STATIONS: tuple[tuple[str, str, str], ...] = (
    ("C-rework-guard-v0100", "v0100", "重工守衛"),
    ("C-vrn-manager-v0289", "v0289", "VRN 行程內掃描"),
    ("C-rework-guard-v0102", "v0102", "正式身分。自測不吃環境變數"),
    ("C-rework-guard-v0101", "v0101", "真分支誤判。v0100 鎖定"),
    ("C-hub-v0101", "v0101", "短指令中樞。這個號留給既有鏈"),
    ("C-hub-v0105", "v0105", "照實燈"),
    ("C-hub-v0106", "v0106", "短指令接到 bak · pano"),
    ("C-hub-v0107", "v0107", "資料根不同仍找得到 bak"),
    ("C-hub-v0108", "v0108", "收據從工具實際寫的根讀"),
    ("C-hub-v0109", "v0109", "找工具與讀收據分開"),
    ("C-vrn-eng397-v0130", "v0130", "fidelity 量測"),
    ("C-vrn-eng397-v0131", "v0131", "fidelity 空共識"),
)

# 批628：同義字收進一冊。表面說法對上典籍碼；對不上就標未入冊，不另造一個名字。
CANON: tuple[tuple[str, str, str], ...] = (
    ("RAM_RESERVE", r"記憶體|RAM|OOM", "保留水位不夠。這一件跳過，不把別的系統歸零。"),
    ("DEP_BLOCKED", r"前置|依賴|blocked", "前置沒完成。沒有宣告這條邊的系統照走。"),
    ("ABSENT_MANAGER", r"ABSENT|無管理器|沒有 System Manager", "沒有 System Manager。不補、不啟動。"),
    ("NET_GATED", r"網路工具|觸網", "網路工具不在。這一件不啟動。不代裝。"),
    ("VERB_SHAPE", r"--selftest|位置動詞", "全景守衛 v0101–v0103 只吃位置動詞 selftest。v0104 轉譯 --selftest，前版不動。"),
    ("JOB_FAULT", r"中斷|失敗|fault|error", "此件失敗。不自動重試、不歸零。其他系統繼續。"),
)

# 對接失敗冊。二十五條都停在對接。融合（共寫狀態、代修、改既有樹）不在這冊，也不沿用這次啟動。
# (編號, 接縫, 失敗, 對接解法)
DOCK_FAILURES: tuple[tuple[str, str, str, str], ...] = (
    ("F01", "名冊", "把沒有管理器當成故障，現場補一顆，或把 AllInOne 當成 System Manager。", "燈維持 ABSENT。不裝、不啟動、不補。典籍只記 ABSENT_MANAGER。"),
    ("F02", "邊界", "為了銜接而跨系統 import。獨立被焊死，一改就連鎖。", "dock 閘見到跨系統 import 就紅燈。只吃 JSON 冊與 argv。短指令主人仍是既有入口。"),
    ("F03", "既有成果", "為了接上而改管理器尾版或 CommandHub 已經做好的檔。", "外掛放在管理器旁。sha12 只核對。不合就停，不進樹改。"),
    ("F04", "指令形狀", "排程指令寫成 shell 字串。加速器蓋不住，也有注入面。", "必須是 Python 陣列。第一個是本解譯器，中段先掛加速器。紅燈不啟動。"),
    ("F05", "加速器", "plan、launch、resume 這些排程動詞本身沒掛加速器，覆蓋未滿仍放行。", "動詞先過橋，任務先包裝。覆蓋未滿 1.0，整閘不放行。"),
    ("F06", "加速器", "註解或文件寫了加速器名字，就被當成已經橋上。", "只認 AST 的 import。字面出現不算。"),
    ("F07", "加速器", "尾版用字母排序，或把橋的尾版號當成工具版本。", "橋用數字取尾。工具版本只讀鎖冊：VeritasCeleritas v1141、VeritasAegisNexus v1652。不複製本體。"),
    ("F08", "加速器", "樹上沒有鎖冊指定的工具，就現場安裝或把本體抄進引擎。", "座位缺席就是 ABSENT。不現場取得套件，不把本體抄進來。"),
    ("F09", "函式庫", "環境已能解析 talib，仍放行啟動。禁庫在跑起來之後才爆。", "環境燈紅燈即停。禁庫只有 TA-Lib 與 talib。不移除套件，不改既有環境。"),
    ("F10", "函式庫", "只掃排程檔沒有禁庫 import，沒掃環境。檔乾淨、環境不符，仍啟動。", "檔內與環境兩盞分開。任一紅燈都不啟動。"),
    ("F11", "網路", "網路工具不在，觸網任務仍出去抓。", "缺席只關觸網任務。不代裝。"),
    ("F12", "網路", "網路工具缺席就把沒觸網的系統一起停掉。", "沒觸網的照排。缺席不升格成整機紅燈。"),
    ("F13", "時間", "對接前花大量時間修他系統、掃全倉、改 stub。啟動不再快。", "閘只讀本檔與 find_spec。紅燈即停，不進修復迴圈。"),
    ("F14", "日誌", "一件失敗就把已完成節點清掉重做。湖與日誌被重做。", "日誌留下完成者。續跑只補未完成。不把已完成的清掉。"),
    ("F15", "日誌", "暫時故障被寫成循環再跑，CPU 與記憶體被占滿。", "失敗件跳過記入典籍。下一手只接受人按從日誌續。"),
    ("F16", "獨立", "一件中斷，沒有依賴邊的其他系統也被拉去重來。", "只有冊上依賴指到失敗件的才擋。沒有這條邊的系統繼續。"),
    ("F17", "依賴", "實際要對方的資料，冊上沒寫邊。看起來獨立，跑起來互相踩。", "沒寫的邊就不存在。要交接就寫進依賴。循環依賴直接拒排。"),
    ("F18", "鎖", "同一把寫入鎖不重疊，被讀成一個系統管轄另一個。", "鎖只是資源閘，不是管轄。事件裡鎖與依賴分開記。"),
    ("F19", "配額", "一啟動就按機器滿載並行。桌面與其他系統一起被壓死。", "保留至少一檔水位，並行有上限。不夠就等，不去動別的行程。"),
    ("F20", "典籍", "同一種失敗各記一碼。監視與啟動對不上。", "表面說法收進既有一冊。對不上就標未入冊，不發明第二個名字。"),
    ("F21", "短指令", "既有短指令在引擎裡重寫一份。中樞與引擎兩套行為。", "中樞仍是主人。引擎只標交接點。安裝與備份類指令不搬。"),
    ("F22", "動詞", "舊尾不吃旗標形狀，就去改前版本體來配合。", "轉譯只放在新的薄尾。前版不動。形狀問題記入既有典籍碼。"),
    ("F23", "測試", "啟動時真的重跑三層測試與全倉掃描。時間拉長，還可能改產物。", "三層只展示讀到的契約。自測只跑本檔。啟動路徑不掃全倉。"),
    ("F24", "監視", "監視另存一份狀態。燈與即時紀錄分裂，人會去修狀態機。", "燈從同一條事件派生。不另存狀態，不進其他系統的樹。"),
    ("F25", "越界", "對接成功後順手融合：共庫、共設定、把沒有管理器的系統收進引擎行程。", "這一步不做。新系統從這裡取外掛。要共寫狀態必須另開合約。"),
)

# 2026-11-11 System Manager 標準動詞。只增不減：前版多出來的動詞留在掃到的集合裡。
VERBS = (
    "help",
    "version",
    "status",
    "health",
    "selftest",
    "test",
    "engines",
    "records",
    "peers",
    "conform",
    "plan",
    "dry-run",
    "launch",
    "mount",
    "resume",
)

# 截取當下看得到管理器尾版的系統才裝外掛。其餘 ABSENT。
SYSTEMS: dict[str, dict] = {
    "VCGC": {
        "independent": True,
        "has_manager": True,
        "manager": "CGC_MDL149_VeritasCentralGovernanceConsole",
        "tail": "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py",
        "law": "L20",
        "why": "唯一對接口。啟動引擎正本放這裡，給後來的系統取用。",
    },
    "VDF": {
        "independent": True,
        "has_manager": True,
        "manager": "VDF_SystemManager",
        "tail": "functional modules/VDF/VDF_SystemManager_v0168.py",
        "sha12": "95e25526bd0a",
        "law": "L98",
        "why": "L98 點名 VDF 是最頂端各自成庫的一座。外掛裝在 VDF_SystemManager v0168 旁，不取代它。不是 L120。",
    },
    "VRN": {
        "independent": True,
        "has_manager": True,
        "manager": "VRN_SystemManager",
        "tail": "functional modules/VRN/VRN_SystemManager_v*.py",
        "law": "L98",
        "why": "L98 三座庫的第一座是 VRN。外掛只認 VRN_SystemManager 尾版，不另造、不改前版。",
    },
    "VQG": {
        "independent": True,
        "has_manager": False,
        "manager": None,
        "seen": "VQG_AllInOne_v0107.py",
        "sha12": "7e278523b28f",
        "law": "L16 / L101",
        "why": "在冊，但律上沒有 VQG_SystemManager。技術分析只走 QuantGuard（VDF_ENG086 v0101）。AllInOne 不是管理器，不補一顆。",
    },
    "VAP": {
        "independent": True,
        "has_manager": False,
        "manager": None,
        "seen": "VAP_AllInOne_v0302.py",
        "sha12": "42aacb2599bc",
        "law": "L16 / L101",
        "why": "L98 沒有把 VAP 列成第四座庫。截取未見 VAP_SystemManager。ABSENT，啟動引擎不裝。",
    },
}


@dataclass
class Job:
    name: str
    cmd: list[str]
    est_ram_mb: int
    system: str
    deps: list[str] = field(default_factory=list)
    mutex: str | None = None
    timeout_sec: int = 3600
    rehearsal: bool = False                                   # 演練用的占位指令:跑得動,但不算完成、不寫典籍

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cmd": self.cmd,
            "est_ram_mb": self.est_ram_mb,
            "system": self.system,
            "deps": list(self.deps),
            "mutex": self.mutex,
            "timeout_sec": self.timeout_sec,
            "rehearsal": self.rehearsal,
        }


@dataclass
class HardwareProfile:
    total_ram_mb: int
    physical_cores: int
    max_parallel: int
    threads_per_job: int
    reserve_free_ram_mb: int

    def to_dict(self) -> dict:
        return {
            "total_ram_mb": self.total_ram_mb,
            "physical_cores": self.physical_cores,
            "max_parallel": self.max_parallel,
            "threads_per_job": self.threads_per_job,
            "reserve_free_ram_mb": self.reserve_free_ram_mb,
        }


def detect_hardware(total_ram_mb: int | None = None, physical_cores: int | None = None) -> HardwareProfile:
    """實體記憶體與實體核心決定配額。不夠就少開，不事後重試來補。"""
    if total_ram_mb is None or physical_cores is None:
        cores = os.cpu_count() or 4
        # 沒有 psutil 時不假裝量過 DRAM。呼叫端應傳入；此處只給保守 16GB 檔。
        ram = 16384
        try:
            import psutil  # type: ignore

            ram = int(psutil.virtual_memory().total / (1024 * 1024))
            cores = psutil.cpu_count(logical=False) or cores
        except Exception:
            pass
        total_ram_mb = total_ram_mb or ram
        physical_cores = physical_cores or cores

    reserve = max(3500, int(total_ram_mb * 0.25))
    usable = max(2, physical_cores - 1)
    if total_ram_mb <= 18000:
        parallel = 2
    elif total_ram_mb <= 36000:
        parallel = min(3, max(2, usable // 2))
    else:
        parallel = min(4, max(2, usable // 2))
    threads = max(1, min(4, usable // parallel))
    return HardwareProfile(total_ram_mb, physical_cores, parallel, threads, reserve)


def accel_env(job: Job, hw: HardwareProfile, base: dict[str, str] | None = None) -> dict[str, str]:
    """批692B：子程序環境帶執行緒上限與溢寫目錄，不靠事後熔斷重試。"""
    env = dict(base or os.environ)
    cap = str(hw.threads_per_job)
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "POLARS_MAX_THREADS",
        "NUMEXPR_MAX_THREADS",
    ):
        env[key] = cap
    env["PYTHONUTF8"] = "1"
    env["VIA_PY_ACCEL"] = ACCEL_MARK
    env["VIA_JOB_MAX_RAM_MB"] = str(job.est_ram_mb)
    env["VIA_JOB_MAX_THREADS"] = cap
    env["VIA_ENGINE"] = ENGINE_ID
    if VIA_ACCEL is not None:
        # 子程序的轉接要 import 得到加速器；路徑取自本檔加速器橋已找到的那一份，不另找本體。
        seat_dir = str(Path(VIA_ACCEL.__file__).resolve().parent)
        parts = [part for part in env.get("PYTHONPATH", "").split(os.pathsep) if part]
        if seat_dir not in parts:
            env["PYTHONPATH"] = os.pathsep.join([seat_dir, *parts])
    return env


def _tail_num(name: str) -> int:
    match = re.search(r"_v(\d+)\.py$", name)
    return int(match.group(1)) if match else -1


def pick_newest_tail(names: Iterable[str]) -> str | None:
    """數字尾版。字母排序會把 v0999 排在 v1000 前面，那不是最新。"""
    ranked = [( _tail_num(name), name) for name in names if _tail_num(name) >= 0]
    if not ranked:
        return None
    ranked.sort()
    return ranked[-1][1]


def _version_num(name: str) -> int:
    match = re.search(r"_v(\d+)\.[A-Za-z0-9]+$", name)
    return int(match.group(1)) if match else -1


def find_via_root(start: str | None = None) -> Path | None:
    """往上找 VIA 樹。這支預覽單檔通常不在樹上。"""
    here = Path(start or __file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "supportive modules" / f"{ACCEL_MODULE}.py").is_file():
            return parent
        nested = parent / "VeritasIntelligenceAnalytics"
        if (nested / "supportive modules" / f"{ACCEL_MODULE}.py").is_file():
            return nested
    return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_locked(root: Path, rel: str) -> Path:
    candidate = root / rel
    if candidate.is_file():
        return candidate
    parts = Path(rel).parts
    if parts and parts[0] == "VeritasIntelligenceAnalytics":
        stripped = root / Path(*parts[1:])
        if stripped.is_file():
            return stripped
    return candidate


def read_lock_book(root: Path) -> dict | None:
    registry = root / "supportive modules" / "registry"
    if not registry.is_dir():
        return None
    books = [item for item in registry.glob("VIA_ToolVersion_Lock_v*.json") if _version_num(item.name) >= 0]
    if not books:
        return None
    books.sort(key=lambda item: _version_num(item.name))
    path = books[-1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"path": str(path), "broken": True}
    return {"path": str(path), "name": path.name, "broken": False, "data": data}


def _tool_seat(kind: str, start: str | None = None) -> dict:
    """座位只跟鎖冊走。find_spec 會撞上無版號凍結本，不算在座。"""
    if kind == "accelerator":
        tool, version, rel, sha = ACCEL_TOOL, ACCEL_LOCK_VERSION, ACCEL_LOCK_REL, ACCEL_LOCK_SHA
        engine = ""
    else:
        tool, version, rel, sha = NET_TOOL, NET_LOCK_VERSION, NET_LOCK_REL, NET_LOCK_SHA
        engine = NET_ENGINE_VERSION
    seat = {
        "lamp": "ABSENT",
        "tool": tool,
        "version": version,
        "engine": engine,
        "via": "lock",
        "sha_ok": False,
        "path": None,
        "why": "",
    }
    root = find_via_root(start)
    if root is None:
        engine_note = f"（{engine}）" if engine else ""
        seat["why"] = (
            f"這支單檔不在 VIA 樹上。鎖冊 {LOCK_BOOK} 的契約是 {tool} {version}{engine_note}。"
            f" {ACCEL_STEM} 與 {NET_BRIDGE_STEM} 是橋，不是工具。不把缺席說成已載入，也不另造本體。"
        )
        return seat
    book = read_lock_book(root)
    if book is None or book.get("broken"):
        seat["why"] = "有 VIA 樹，讀不到鎖冊。不改用 find_spec，也不現場安裝。"
        return seat
    locked = (book.get("data") or {}).get("accelerator" if kind == "accelerator" else "network") or {}
    book_version = str(locked.get("version") or "")
    book_rel = str(locked.get("path") or "")
    book_sha = str(locked.get("sha256") or "")
    if book_version != version or book_rel != rel or book_sha != sha:
        seat["lamp"] = "RED"
        seat["why"] = f"樹上鎖冊的 {tool} 與這支引擎記下的契約不一致。不改冊、不啟動。"
        return seat
    target = _resolve_locked(root, book_rel)
    if not target.is_file():
        seat["why"] = f"鎖冊點名 {tool} {version}，檔不在。ABSENT，不代裝。"
        return seat
    digest = _file_sha256(target)
    if digest != book_sha:
        seat["lamp"] = "RED"
        seat["path"] = str(target)
        seat["why"] = f"{tool} {version} 在，但 sha 與鎖冊不符。不覆蓋、不啟動。"
        return seat
    seat["lamp"] = "GREEN"
    seat["sha_ok"] = True
    seat["path"] = str(target)
    seat["why"] = f"鎖冊 {tool} {version}，sha 對上。不是橋的尾版號。"
    return seat


def find_accel_seat(start: str | None = None) -> dict:
    return _tool_seat("accelerator", start)


def find_net_seat(start: str | None = None) -> dict:
    return _tool_seat("network", start)


def fold_canon(surface: str) -> dict:
    """一個表面說法只落到一個典籍碼。舉不出實例的不記成新碼。"""
    for code, pattern, reason in CANON:
        if re.search(pattern, surface, re.IGNORECASE):
            return {"code": code, "surface": surface, "reason": reason}
    return {"code": "UNCATALOGUED", "surface": surface, "reason": "對不上既有典籍碼。不發明新名字。"}


def dock_ledger() -> dict:
    """二十五條對接失敗。解法欄不得滑進融合：代裝、改樹、循環再跑、另造管理器。"""
    expect = [f"F{n:02d}" for n in range(1, 26)]
    ids = [row[0] for row in DOCK_FAILURES]
    refused = ("pip ", "uninstall", "改他系統", "重跑全樹", "自動重試", "另造管理器", "import VDF_")
    leaks = [row[0] for row in DOCK_FAILURES if any(token in row[3] for token in refused)]
    blank = [row[0] for row in DOCK_FAILURES if not all(part.strip() for part in row)]
    ok = ids == expect and not leaks and not blank
    return {
        "count": len(DOCK_FAILURES),
        "ok": ok,
        "phase": "dock",
        "fusion": False,
        "leaks": leaks,
        "rows": [{"id": a, "seam": b, "fail": c, "dock": d} for a, b, c, d in DOCK_FAILURES],
    }


def clamp_wait(seconds: float | None) -> float | None:
    """Event.wait 吃得下的秒數。None 表示等到結束，不送逾時。

    v0102 為了壓住 v0100 的心跳，傳 beat=10**9。Windows 上這個數字會
    OverflowError: timeout value is too large。沉默就是等到結束，不是把
    十億秒丟進去。v0100 一字不動。
    """
    if seconds is None:
        return None
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return None
    if value < 0 or value >= FASTRUN_BEAT_SENTINEL:
        return None
    if value > WAIT_SAFE_SEC:
        return float(WAIT_SAFE_SEC)
    return value


def token_directive() -> dict:
    """任何 AI 主動取用工具的整份指引。貼出去的只有 cue 那一行。"""
    return {
        "cue": TOKEN_CUE,
        "rules": [{"id": rule_id, "do": text} for rule_id, text in TOKEN_RULES],
        "paste": "cue",
        "verb": TOKEN_VERB,
        "station": TOKEN_STATION,
        "new_meter": False,
    }


# 現況對接的列號。全文在這頁，不在這支引擎裡重貼。兩份 Agent OS 壓縮包是同一份。
PLATFORM_IDS = (
    "status", "mdl283", "mdl282", "mcp", "connect", "diag", "align", "local",
    "token6", "cue", "tokenconsole", "handoff", "sdd", "constitution", "vcgc", "vdf", "vrn",
    "vdfdb", "t3017", "onedrive", "g01", "g02", "g03", "g05", "g06", "g08", "g09",
    "c05", "c12", "c13", "quality", "req225", "regsync", "prstack", "startuppr", "overflow",
    "fourtools", "psyntax", "feedback", "flare", "agentos", "connectors", "pyarrow",
    "matrix", "fail20", "bench", "fiveentry",
)
PLATFORM_COMMANDS = (
    "via-vcgc monitor status --last",
    "Invoke-VIA-VCGC-Connect-v0100.ps1 -NoSwitch -NoFetch",
    "Invoke-VIA-VCGC-LatestToolsDiag-v0100.ps1 -NoOpen",
    "Invoke-VIA-PCAlign-HandleAll-v0100.ps1 -NoAlign -NoOpen",
    "Invoke-VIA-LocalMonitor-v0100.ps1 -NoOpen",
    "Invoke-VIA-WorkbenchLocal-v0104.ps1",
    "py -3.12 CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py matrix install",
    "py VIA_SystemIntegrationEngine.py --doctor",
)


def platform_dock() -> dict:
    """附件與壓縮包只對接。不跑、不裝、不寫倉、不加 --apply、不把 v0194 放進 registry。"""
    joined = " | ".join(PLATFORM_COMMANDS)
    return {
        "runs": False,
        "install": False,
        "holds_apply": "--apply" in joined or " -Sync" in joined,
        "writes_books": False,
        "fusion": False,
        "go_live": "BLOCKED",
        "agentos_same": True,
        "agentos_sha": "97ca853d253ea58194a2938762899624852f8651c9853fa3224d93d46855f304",
        "v0194_in_registry": False,
        "count": len(PLATFORM_IDS),
        "ids": list(PLATFORM_IDS),
        "commands": joined,
    }


def support_review(already: Iterable[str] | None = None) -> dict:
    """先走既有 token 動詞。十個來源只看索引。24 小時內不重讀。不拉全文，不代裝。"""
    seen = {item for item in (already or ())}
    sources = []
    for key, label, cheap in SUPPORT_SOURCES:
        if key in seen:
            sources.append({
                "id": key,
                "label": label,
                "lamp": "NODATA",
                "detail": f"{INVENTORY_REUSE_HOURS} 小時內已看過索引。不重讀。",
            })
        else:
            sources.append({"id": key, "label": label, "lamp": "ABSENT", "detail": cheap})
    return {
        "verb": TOKEN_VERB,
        "station": TOKEN_STATION,
        "tool": TOKEN_TOOL,
        "reuse_hours": INVENTORY_REUSE_HOURS,
        "sources": sources,
        "pulled_bodies": False,
        "install": False,
        "directive": token_directive(),
        "receipt": {
            "tool": FASTRUN_TAIL,
            "argv": ["--set", "env,fidelity", "--push"],
            "beat": FASTRUN_BEAT_SENTINEL,
            "wait": clamp_wait(FASTRUN_BEAT_SENTINEL),
            "cause": "v0102 把 10**9 秒交給 v0100 的 heartbeat。要沉默就等到結束，不改 v0100。",
            "steps": [
                {"name": "env:doctor_before", "rc": 1, "lamp": "RED", "secs": 889.2},
                {"name": "env:install", "rc": 0, "lamp": "GREEN", "secs": 317.6, "pkgs": ["dateparser", "opencv-contrib-python"]},
                {"name": "env:doctor_after", "rc": 1, "lamp": "RED", "secs": 650.3},
            ],
            "books": {
                "inventory": INVENTORY_BOOK,
                "stations": INVENTORY_STATIONS,
                "workflow": WORKFLOW_BOOK,
                "workflows": WORKFLOW_COUNT,
                "fastrun_v0102_registered": False,
            },
        },
    }


def complement_survey() -> dict:
    """四個名字只對接。今日的站已在盤點冊，不另開，也不改備份尾。"""
    tools = [
        {
            "id": "GRAPHIFY",
            "label": "Graphify",
            "station": "V-graphify",
            "lamp": "ABSENT",
            "backup": True,
            "dock": "冊上有站，動詞 graphify status，缺件 rc 3 是黃。這頁看不到隔離環境，座位仍是缺席。備份只收已產出的圖，不跑工具。圖不是正式證據。",
        },
        {
            "id": "OMNIROUTE",
            "label": "OmniRoute",
            "station": "",
            "lamp": "ABSENT",
            "backup": True,
            "dock": "沒有自己的站。備份只收各系統的路由設定檔，不收程式、不收金鑰。VRN 執行路徑不准經過它。這頁不啟動、不佔埠。",
        },
        {
            "id": "PONYTAIL",
            "label": "Ponytail",
            "station": "",
            "lamp": "ABSENT",
            "backup": False,
            "dock": "沒有站。v0102 的備份範圍沒有它。它是操作員本機的外掛，倉內零改動。不安裝、不進引擎路徑。",
        },
        {
            "id": "AGENCY-MEM",
            "label": "Agency-Mem",
            "station": "",
            "lamp": "ABSENT",
            "backup": False,
            "dock": "冊上沒有這個名字，不另開站。VRN-WKF017 的 resources 七格寫了 agentmemory，那不是這支引擎，也不等於 Agent OS。",
        },
    ]
    return {
        "phase": "dock",
        "fusion": False,
        "install": False,
        "runs_tools": False,
        "writes_books": False,
        "backup": {
            "tail": "VIA_DailyBackup_v0102.py",
            "station": "C-daily-backup-v0102",
            "scopes": ["GRAPHIFY", "OMNIROUTE"],
            "runs_tools": False,
            "prior_kept": True,
        },
        "tools": tools,
        "today": {
            "date": "2026-11-24",
            "count": len(TODAY_STATIONS),
            "already": True,
            "in_backup_zip": False,
            "stations": [{"id": a, "version": b, "note": c} for a, b, c in TODAY_STATIONS],
        },
    }


def dock_walk() -> dict:
    """沿既有管理器、同義字冊、參數形狀走一輪。走完不是已裝，也不改它們的檔。"""
    memory_a = fold_canon("記憶體不足")
    memory_b = fold_canon("OOM")
    absent = fold_canon("沒有 System Manager")
    same = memory_a["code"] == memory_b["code"] == "RAM_RESERVE"
    steps: list[dict] = [
        {
            "id": "synonym",
            "lane": "同義字",
            "lamp": "GREEN" if same else "YELLOW",
            "code": memory_a["code"],
            "note": "記憶體不足與 OOM 收成同一個典籍碼。對不上就不發明新名字。",
        },
        {
            "id": "params",
            "lane": "參數",
            "lamp": "GREEN",
            "code": "",
            "note": "輸入是 Python 陣列，輸出是燈與典籍。短指令主人仍是 CommandHub。",
        },
    ]
    for system, spec in SYSTEMS.items():
        has = bool(spec["has_manager"])
        steps.append({
            "id": system,
            "lane": "管理器",
            "lamp": "GREEN" if has else "ABSENT",
            "code": "" if has else absent["code"],
            "note": ("外掛靠在 " + str(spec["manager"]) + " 旁。不進它的樹。") if has else absent["reason"],
        })
    steps.append({
        "id": "accel",
        "lane": "加速器",
        "lamp": "GREEN",
        "code": "",
        "note": ACCEL_TOOL + " " + ACCEL_LOCK_VERSION + "。排程先掛橋。不複製本體。",
    })
    steps.append({
        "id": "backup",
        "lane": "備份",
        "lamp": "GREEN",
        "code": "",
        "note": "只對接範圍。不跑備份、不收今日引擎本體。",
    })
    for tool in complement_survey()["tools"]:
        steps.append({
            "id": tool["id"],
            "lane": "工具",
            "lamp": "ABSENT",
            "code": "",
            "note": "座位缺席。對接不代跑、不另開站。",
        })
    return {
        "steps": steps,
        "fusion": False,
        "writes_books": False,
        "install": False,
        "pct": 100,
        "accel": ACCEL_TOOL + " " + ACCEL_LOCK_VERSION,
    }


def through_accel(verb: str) -> dict:
    """每個動詞先掛橋，再做事。冊外的動詞直接拒絕。"""
    if verb not in VERBS:
        raise ValueError(f"動詞不在冊: {verb}")
    return {
        "verb": verb,
        "module": ACCEL_MODULE,
        "bridge": ACCEL_BRIDGE_MARK,
        "accel_lock": ACCEL_LOCK_VERSION,
        "net_lock": NET_LOCK_VERSION,
        "net_engine": NET_ENGINE_VERSION,
        "tool": ACCEL_TOOL,
        "net_tool": NET_TOOL,
        "mark": ACCEL_MARK,
        "loaded": VIA_ACCEL is not None,
        "seat": find_accel_seat(),
    }


def accel_argv(args: list[str]) -> list[str]:
    """子程序先掛轉接再執行原指令。禁止 shell 字串。樹上沒有轉接就 rc 3，不假跑。"""
    if not args or any(not isinstance(part, str) or not part.strip() for part in args):
        raise ValueError("指令必須是非空字串陣列")
    bootstrap = (
        "import os,sys\n"
        "try:\n"
        " import VIA_SuperAccel_Module\n"
        "except Exception as exc:\n"
        " sys.stderr.write('ACCEL_ABSENT %s\\n' % exc)\n"
        " sys.exit(3)\n"
        "import subprocess\n"
        "argv = sys.argv[1:]\n"
        "if os.path.basename(argv[0]).lower() in ('python', 'python3', 'python.exe', 'python3.exe'):\n"
        " argv[0] = sys.executable\n"
        "sys.exit(subprocess.call(argv))\n"
    )
    return [sys.executable, "-c", bootstrap, *args]


# 編號只增。不跟行號。不在這三份裡的名字就是還沒登記。
AST_CLS_FLOOR = ("Job", "HardwareProfile")
AST_LIB_FLOOR = (
    "__future__",
    "argparse",
    "ast",
    "dataclasses",
    "graphlib",
    "hashlib",
    "importlib",
    "json",
    "os",
    "pathlib",
    "re",
    "sys",
    "typing",
    "subprocess",
    "tempfile",
    "concurrent",
    "signal",
)
AST_ABSENT = ("LibCST", "ruff", "tree-sitter", "PSScriptAnalyzer", "Pyre")
AST_FNC_FLOOR: tuple[str, ...] = (
    "detect_hardware",
    "accel_env",
    "_tail_num",
    "pick_newest_tail",
    "_version_num",
    "find_via_root",
    "_file_sha256",
    "_resolve_locked",
    "read_lock_book",
    "_tool_seat",
    "find_accel_seat",
    "find_net_seat",
    "fold_canon",
    "dock_ledger",
    "clamp_wait",
    "token_directive",
    "platform_dock",
    "support_review",
    "complement_survey",
    "dock_walk",
    "through_accel",
    "accel_argv",
    "parse_source",
    "ast_inventory",
    "ast_string_verbs",
    "coverage",
    "engine_coverage",
    "mount",
    "assist_interface",
    "validate_jobs",
    "dependency_waves",
    "_fits",
    "simulate",
    "default_jobs",
    "_spec_found",
    "source_activates_talib",
    "preflight",
    "plan_report",
    "conform",
    "_check",
    "selftest",
    "main",
    "_duckdb",
    "_parquet_target",
    "vdf_parquet_increment",
    "vqg_analyze",
    "vap_view",
    "pipeline_rehearse",
    "run_job",
    "journal_path",
    "load_journal",
    "save_journal",
    "_kill_tree",
    "load_jobs",
    "launch_status",
    "launch_run",
)


def parse_source(source: str) -> ast.AST:
    """全檔只從這裡解析。呼叫端把樹傳下去，不各自再解析。"""
    return ast.parse(source)


def ast_inventory(source: str | None = None) -> dict:
    """CLS / FNC / LIB 編號。缺的庫保持缺席。不寫檔，不融合。"""
    src = source if source is not None else Path(__file__).read_text(encoding="utf-8")
    tree = parse_source(src)
    classes: list[str] = []
    functions: list[str] = []
    libs: list[str] = []
    parse_owners: list[str] = []
    assist_imports = 0
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
            for inner in ast.walk(node):
                called = (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Attribute)
                    and isinstance(inner.func.value, ast.Name)
                    and inner.func.value.id == "ast"
                    and inner.func.attr == "parse"
                )
                if called:
                    parse_owners.append(node.name)
                if node.name == "assist_interface" and isinstance(inner, (ast.Import, ast.ImportFrom)):
                    assist_imports += 1
        elif isinstance(node, ast.Import):
            libs.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            libs.append(node.module.split(".")[0])

    def rows(names: list[str], floor: tuple[str, ...], kind: str) -> list[dict]:
        return [
            {"id": f"AST-{kind}-CORE-{index:04d}", "name": name, "present": name in names}
            for index, name in enumerate(floor, start=1)
        ]

    lib_set = sorted(set(libs))
    return {
        "writes": False,
        "fusion": False,
        "cls": rows(classes, AST_CLS_FLOOR, "CLS"),
        "fnc": rows(functions, AST_FNC_FLOOR, "FNC"),
        "lib": lib_set,
        "lost_cls": [name for name in AST_CLS_FLOOR if name not in classes],
        "lost_fnc": [name for name in AST_FNC_FLOOR if name not in functions],
        "extra_fnc": [name for name in functions if name not in AST_FNC_FLOOR],
        "lost_lib": [name for name in AST_LIB_FLOOR if name not in lib_set],
        "extra_lib": [name for name in lib_set if name not in AST_LIB_FLOOR],
        "hold": ["_tail_num", "_version_num"],
        "composed": {"body": "_tool_seat", "names": ["find_accel_seat", "find_net_seat"]},
        "absent": list(AST_ABSENT),
        "parse_owners": parse_owners,
        "assist_imports": assist_imports,
    }


def ast_string_verbs(source: str, tree: ast.AST | None = None) -> set[str]:
    """用 AST 收動詞，不靠關鍵字全文搜。只認賦值、choices、以及與字串常數的比較。"""
    if tree is None:
        tree = parse_source(source)
    found: set[str] = set()

    def take_seq(node: ast.AST) -> None:
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    found.add(elt.value)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(n in {"VERBS", "STANDARD_VERBS", "CHOICES"} for n in names):
                take_seq(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in {"VERBS", "STANDARD_VERBS", "CHOICES"} and node.value is not None:
                take_seq(node.value)
        elif isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "choices":
                    take_seq(kw.value)
        elif isinstance(node, ast.Compare):
            nodes = [node.left, *node.comparators]
            for item in nodes:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    if item.value in VERBS:
                        found.add(item.value)
    return found


def coverage(source: str, required: Iterable[str] = VERBS, tree: ast.AST | None = None) -> dict:
    text_has_accel = ACCEL_MARK in source
    try:
        found = ast_string_verbs(source, tree)
        parsed = True
        error = ""
    except SyntaxError as exc:
        found = set()
        parsed = False
        error = f"語法錯誤 第 {exc.lineno} 行"
    need = list(required)
    missing = [v for v in need if v not in found]
    ratio = 0.0 if not need else (len(need) - len(missing)) / len(need)
    ok = parsed and text_has_accel and not missing
    return {
        "parsed": parsed,
        "error": error,
        "accel": text_has_accel,
        "found": sorted(found),
        "missing": missing,
        "ratio": ratio,
        "ok": ok,
    }


def engine_coverage(source: str | None = None, tree: ast.AST | None = None) -> dict:
    """啟動面：環境標記、橋、鎖冊版本、動詞派發、任務包裝、十五個動詞。未滿 1.0 不放行。"""
    src = source if source is not None else Path(__file__).read_text(encoding="utf-8")
    parsed = True
    if tree is None:
        try:
            tree = parse_source(src)
        except SyntaxError:
            tree = None
            parsed = False
    imported = False
    has_through = False
    has_wrap = False
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(alias.name == ACCEL_MODULE for alias in node.names):
                imported = True
            if isinstance(node, ast.FunctionDef) and node.name == "through_accel":
                has_through = True
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "accel_argv":
                has_wrap = True
    verb_gate = coverage(src, tree=tree) if parsed else {"found": [], "missing": list(VERBS), "ok": False}
    found = set(verb_gate.get("found") or [])
    flags = [
        ("環境標記", ACCEL_MARK in src),
        ("橋 import", imported),
        ("橋標記", ACCEL_BRIDGE_MARK in src),
        ("鎖冊版本", ACCEL_TOOL in src and ACCEL_LOCK_VERSION in src and NET_TOOL in src and NET_LOCK_VERSION in src and NET_ENGINE_VERSION in src),
        ("動詞派發", has_through),
        ("任務包裝", has_wrap),
    ]
    for verb in VERBS:
        flags.append((verb, verb in found))
    missing = [name for name, ok in flags if not ok]
    required = len(flags)
    covered = required - len(missing)
    ratio = 0.0 if not required else covered / required
    return {
        "parsed": parsed,
        "required": required,
        "covered": covered,
        "ratio": ratio,
        "missing": missing,
        "ok": parsed and not missing and ratio == 1.0,
        "seat": find_accel_seat(),
    }


def mount(system_id: str) -> dict:
    """外掛契約。沒有管理器就 rc 3 ABSENT，不建立管理器。"""
    spec = SYSTEMS.get(system_id)
    if spec is None:
        return {"system": system_id, "rc": 3, "lamp": "ABSENT", "plugin": None, "why": "不在五系統名冊。"}
    if not spec["has_manager"]:
        return {
            "system": system_id,
            "rc": 3,
            "lamp": "ABSENT",
            "plugin": None,
            "manager": None,
            "independent": True,
            "why": spec["why"],
            "seen": spec.get("seen"),
        }
    return {
        "system": system_id,
        "rc": 0,
        "lamp": "GREEN",
        "plugin": ENGINE_ID,
        "manager": spec["manager"],
        "tail": spec["tail"],
        "independent": True,
        "verbs": list(VERBS),
        "accel": ACCEL_MARK,
        "why": spec["why"],
    }


def assist_interface(overlay: dict | None = None) -> dict:
    """一座系統一塊接口。改一座不會改到另一座。融合先不做。REGISTER 不丟。"""
    seats = []
    for sid, spec in SYSTEMS.items():
        local = dict(spec)
        if overlay and sid in overlay:
            local.update(overlay[sid])
        has = bool(local.get("has_manager"))
        seats.append({
            "id": sid,
            "manager": local.get("manager"),
            "phase": "interface" if has else "absent",
            "fusion": False,
            "blast": sid,
            "why": local.get("why"),
        })
    prior = [item[0] for item in TODAY_STATIONS]
    return {
        "phase": "interface",
        "fusion": False,
        "register": prior,
        "lost": [],
        "duplicates": [item for item in prior if prior.count(item) > 1],
        "seats": seats,
    }


def validate_jobs(jobs: list[Job]) -> None:
    names = [j.name for j in jobs]
    if len(names) != len(set(names)):
        raise ValueError("任務名稱重複")
    known = set(names)
    for job in jobs:
        if not job.cmd or not all(isinstance(p, str) and p.strip() for p in job.cmd):
            raise ValueError(f"{job.name} 的 cmd 必須是非空字串陣列（禁止 shell 字串）")
        if job.est_ram_mb <= 0:
            raise ValueError(f"{job.name} 的 est_ram_mb 必須為正整數")
        for dep in job.deps:
            if dep == job.name or dep not in known:
                raise ValueError(f"{job.name} 的前置依賴不合法: {dep}")
        mounted = mount(job.system)
        if mounted["rc"] != 0:
            raise ValueError(f"{job.name} 屬於 {job.system}，該系統沒有 System Manager，不排入啟動")
    graph = {j.name: set(j.deps) for j in jobs}
    try:
        TopologicalSorter(graph).prepare()
    except CycleError as exc:
        raise ValueError(f"循環依賴: {exc}") from exc


def dependency_waves(jobs: list[Job]) -> list[list[str]]:
    validate_jobs(jobs)
    remaining = {j.name: set(j.deps) for j in jobs}
    waves: list[list[str]] = []
    while remaining:
        ready = sorted(n for n, deps in remaining.items() if not deps)
        if not ready:
            raise ValueError("循環依賴")
        waves.append(ready)
        for name in ready:
            remaining.pop(name)
        for deps in remaining.values():
            deps.difference_update(ready)
    return waves


def _fits(running: list[Job], job: Job, hw: HardwareProfile) -> bool:
    if any(r.mutex and r.mutex == job.mutex for r in running):
        return False
    if len(running) >= hw.max_parallel:
        return False
    used = sum(r.est_ram_mb for r in running)
    # 有人在跑時守住保留水位；沒人在跑時放行最小的一個，避免整條管線餓死。
    if running and used + job.est_ram_mb + hw.reserve_free_ram_mb > hw.total_ram_mb:
        return False
    return True


def simulate(
    jobs: list[Job],
    hw: HardwareProfile,
    journal: Iterable[str] | None = None,
    fail_name: str | None = None,
    on_fault: str = "halt",
    gated: Iterable[str] | None = None,
    runner=None,
    on_done=None,
) -> dict:
    """on_fault=halt：失敗即停，已完成的留在 journal。
    on_fault=skip：失敗的那一件記入典籍並跳過，沒有這條依賴的系統繼續。不自動重試，不歸零。"""
    if on_fault not in {"halt", "skip"}:
        raise ValueError("on_fault 只接受 halt 或 skip")
    validate_jobs(jobs)
    done = set(journal or ())
    unknown = done - {j.name for j in jobs}
    if unknown:
        raise ValueError(f"日誌裡有不存在的任務: {sorted(unknown)}")
    by_name = {j.name: j for j in jobs}
    pending = {j.name for j in jobs if j.name not in done}
    running: list[Job] = []
    events: list[dict] = []
    canon: list[dict] = []
    skipped: set[str] = set()
    failed: str | None = None
    steps = 0
    gated_names = set(gated or ())
    runs: list[dict] = []
    futures: dict = {}
    pool = ThreadPoolExecutor(max_workers=max(1, len(jobs))) if runner is not None else None

    def release_blocked() -> None:
        progressed = True
        while progressed:
            progressed = False
            for name in list(pending):
                held = name in gated_names
                blocked = any(dep in skipped for dep in by_name[name].deps)
                if not held and not blocked:
                    continue
                pending.remove(name)
                skipped.add(name)
                hit = fold_canon("網路工具不在，觸網任務不啟動" if held else "前置依賴未完成")
                hit["name"] = name
                hit["system"] = by_name[name].system
                canon.append(hit)
                events.append({"kind": "skip", "name": name, "system": by_name[name].system, "code": hit["code"]})
                progressed = True

    while pending or running:
        steps += 1
        if steps > 10000:
            raise RuntimeError("排程沒有前進，拒絕空轉")
        release_blocked()
        if not pending and not running:
            break
        ready = [
            by_name[n]
            for n in sorted(pending)
            if all(d in done for d in by_name[n].deps)
        ]
        ready.sort(key=lambda j: (j.est_ram_mb, j.name))
        started = False
        for job in ready:
            if not _fits(running, job, hw):
                continue
            pending.remove(job.name)
            running.append(job)
            events.append({"kind": "start", "name": job.name, "system": job.system, "ram": job.est_ram_mb})
            started = True
        if running and runner is not None:
            # launch / resume：每件被放行的任務各自在工作緒裡真的跑（准入照舊看依賴、記憶體、互斥），誰先跑完先收。
            for j in running:
                if j.name not in futures:
                    if fail_name and j.name == fail_name and failed is None:
                        fut: Future = Future()
                        fut.set_result({"name": j.name, "ok": False, "rc": None, "why": "指定中斷（--fail）"})
                        futures[j.name] = fut
                    else:
                        futures[j.name] = pool.submit(runner, j)
            finished, _ = wait([futures[j.name] for j in running], return_when=FIRST_COMPLETED)
            first = next(iter(finished))
            job = next(j for j in running if futures[j.name] is first)
            running.remove(job)
            outcome = futures.pop(job.name).result()
            runs.append(outcome)
            if not outcome["ok"]:
                if failed is None:
                    failed = job.name
                skipped.add(job.name)
                hit = fold_canon("此件中斷")
                hit["name"] = job.name
                hit["system"] = job.system
                hit["rc"] = outcome["rc"]
                canon.append(hit)
                events.append({"kind": "fail", "name": job.name, "system": job.system, "code": hit["code"], "rc": outcome["rc"]})
                if on_fault == "halt":
                    for other in running:                      # 已在跑的等它跑完、照實記，不再放行新的
                        late = futures.pop(other.name).result()
                        runs.append(late)
                        if late["ok"]:
                            done.add(other.name)
                            events.append({"kind": "done", "name": other.name, "system": other.system})
                            if on_done is not None:
                                on_done(sorted(done))
                        else:
                            skipped.add(other.name)
                            events.append({"kind": "fail", "name": other.name, "system": other.system, "rc": late["rc"]})
                    running.clear()
                    break
                continue
            done.add(job.name)
            events.append({"kind": "done", "name": job.name, "system": job.system})
            if on_done is not None:
                on_done(sorted(done))                          # 每收一件就落典籍(中途被打斷也不丟已完成的)
            continue
        if running:
            job = running.pop(0)
            if fail_name and job.name == fail_name and failed is None:
                failed = job.name
                skipped.add(job.name)
                hit = fold_canon("此件中斷")
                hit["name"] = job.name
                hit["system"] = job.system
                canon.append(hit)
                events.append({"kind": "fail", "name": job.name, "system": job.system, "code": hit["code"]})
                if on_fault == "halt":
                    running.clear()
                    break
                continue
            done.add(job.name)
            events.append({"kind": "done", "name": job.name, "system": job.system})
            continue
        if pending and not started:
            smallest = min(ready, key=lambda j: j.est_ram_mb) if ready else None
            if smallest is None:
                raise RuntimeError("有任務懸空且依賴未滿足")
            if not running:
                pending.remove(smallest.name)
                running.append(smallest)
                events.append({
                    "kind": "start",
                    "name": smallest.name,
                    "system": smallest.system,
                    "ram": smallest.est_ram_mb,
                    "note": "獨佔放行，避免餓死",
                })
                continue
            events.append({"kind": "wait", "name": smallest.name})
            break

    if pool is not None:
        pool.shutdown(wait=True)
    return {
        "events": events,
        "journal": sorted(done),
        "failed": failed,
        "pending": sorted(pending),
        "skipped": sorted(skipped),
        "canon": canon,
        "stopped": failed is not None and on_fault == "halt",
        "reset": False,
        "executed": runner is not None,
        "runs": runs,
    }


def _kill_tree(proc) -> None:
    """逾時:整棵行程樹一起收(轉接行程底下真正的指令也算),收完才回。"""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=60)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        proc.kill()
    try:
        proc.communicate(timeout=60)
    except (OSError, ValueError, subprocess.SubprocessError):
        proc.wait()


def run_job(job: Job, hw: HardwareProfile, run=None) -> dict:
    """launch / resume 用：跑這件的指令（已先掛加速器），完成與否只看回傳碼。不重試、不改指令、不用 shell。
    逾時 → 整棵行程樹砍掉並收屍後才回 rc 124(不留孤兒寫手占著記憶體與互斥)。run 只給自測注入假的執行器。"""
    if run is not None:
        try:
            proc = run(job.cmd, env=accel_env(job, hw), timeout=job.timeout_sec, capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            return {"name": job.name, "ok": False, "rc": 124, "why": "逾時"}
        except OSError as exc:
            return {"name": job.name, "ok": False, "rc": 127, "why": type(exc).__name__}
        out, err, code = proc.stdout, proc.stderr, proc.returncode
    else:
        group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        try:
            proc = subprocess.Popen(job.cmd, env=accel_env(job, hw), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    encoding="utf-8", errors="replace", **group)   # 子程序被 PYTHONUTF8=1 → 一律 UTF-8 解,壞字元換掉不炸
        except OSError as exc:
            return {"name": job.name, "ok": False, "rc": 127, "why": type(exc).__name__}
        try:
            out, err = proc.communicate(timeout=job.timeout_sec)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            return {"name": job.name, "ok": False, "rc": 124, "why": "逾時(整棵行程樹已收)"}
        code = proc.returncode
    tail = ((err or "") + (out or "")).strip().splitlines()
    return {"name": job.name, "ok": code == 0, "rc": code, "why": tail[-1][:200] if tail else ""}


def journal_path(override: str = "") -> Path:
    """完成典籍放哪:--journal 指定 > VIA 樹的 VIA_Reports/vcgc_startup/ > 系統暫存夾(單檔不在樹上時)。"""
    if override:
        return Path(override)
    root = find_via_root()
    base = (root.parent if root and root.name == "VeritasIntelligenceAnalytics" else root) if root else None
    folder = (base / "VIA_Reports" / "vcgc_startup") if base else Path(tempfile.gettempdir()) / "vcgc_startup"
    return folder / "JOURNAL_latest.json"


def load_journal(path: Path, jobs: list[Job]) -> tuple[list[str], list[str]]:
    """回 (已完成且仍在冊上的任務, 冊上已沒有的舊名)。檔不在 = 空典籍。不歸零、不改檔。"""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], []
    names = {j.name for j in jobs}
    done = [n for n in data.get("journal", []) if isinstance(n, str)]
    return [n for n in done if n in names], [n for n in done if n not in names]


def save_journal(path: Path, result: dict, verb: str) -> None:
    """只記完成的任務(失敗與跳過不算),先寫暫存檔再換名。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"engine": ENGINE_ID, "verb": verb, "journal": result["journal"], "failed": result["failed"],
                               "skipped": result["skipped"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def default_jobs() -> list[Job]:
    """只排已裝外掛的系統。VQG / VAP 不在冊上。每道指令先掛加速器，不觸網。
    VCGC 的三件只依賴自己。VRN 抽取那條邊是資料依賴，不是 VDF 管轄 VRN。"""
    quiet = accel_argv(["python", "-c", "print('ok')"])
    jobs = [
        Job("VCGC_01_PolicySeat", quiet, 400, "VCGC"),
        Job("VCGC_02_PanoramaGuard", quiet, 800, "VCGC", deps=["VCGC_01_PolicySeat"]),
        Job("VCGC_03_TestLanes", quiet, 600, "VCGC", deps=["VCGC_02_PanoramaGuard"]),
        Job("VDF_01_TWSE_Daily", quiet, 1400, "VDF", mutex="net_twse"),
        Job("VDF_02_TPEX_Daily", quiet, 1400, "VDF", mutex="net_tpex"),
        Job("VDF_04_Lakehouse_Merge", quiet, 3000, "VDF", deps=["VDF_01_TWSE_Daily", "VDF_02_TPEX_Daily"], mutex="duckdb_write"),
        Job("VRN_01_PDF_Layout", quiet, 4200, "VRN", mutex="vrn_ocr"),
        Job("VRN_02_Extract", quiet, 2200, "VRN", deps=["VRN_01_PDF_Layout", "VDF_04_Lakehouse_Merge"], mutex="duckdb_write"),
    ]
    for job in jobs:
        job.rehearsal = True                                   # 還沒接各系統管理器的真指令(接口相位):只能演練
    return jobs


def load_jobs(path: str | Path) -> list[Job]:
    """--jobs 指定的任務清單(JSON:{"jobs":[{name, cmd, est_ram_mb, system, deps, mutex, timeout_sec}]} 或直接是清單)。
    每道 cmd 照樣先掛加速器(accel_argv);系統沒有管理器的照 validate_jobs 拒絕。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get("jobs") if isinstance(data, dict) else data
    if not isinstance(rows, list) or not rows:
        raise ValueError("--jobs 檔裡沒有任務清單")
    jobs = []
    for row in rows:
        jobs.append(Job(str(row["name"]), accel_argv(list(row["cmd"])), int(row["est_ram_mb"]), str(row["system"]),
                        deps=list(row.get("deps") or []), mutex=row.get("mutex"), timeout_sec=int(row.get("timeout_sec") or 3600)))
    validate_jobs(jobs)
    return jobs


def launch_status(result: dict, rehearsal: bool) -> tuple[str, int]:
    """失敗 → FAILED rc 1;演練 → REHEARSAL rc 3;有跳過 / 未跑 → INCOMPLETE rc 3;全跑完 → COMPLETE rc 0。"""
    if result.get("failed"):
        return "FAILED", 1
    if rehearsal:
        return "REHEARSAL", 3
    if result.get("skipped") or result.get("pending"):
        return "INCOMPLETE", 3
    return "COMPLETE", 0


def launch_run(verb: str, jobs: list[Job], hw: HardwareProfile, gated: list[str], jpath: Path,
               fail_name: str | None = None, runner=None) -> tuple[dict, int]:
    """launch / resume 的本體(main 與自測共用)。演練清單不讀也不寫典籍;真清單每件完成就落典籍。"""
    rehearsal = any(job.rehearsal for job in jobs)
    run = runner or (lambda job: run_job(job, hw))
    if rehearsal:
        prior, stale = [], []
        result = simulate(jobs, hw, journal=None, fail_name=fail_name, on_fault="skip", gated=gated, runner=run)
        result["journal_file"] = None
        result["note"] = "演練:任務是占位指令,還沒接各系統管理器的真指令 → 不寫典籍、不算完成(給 --jobs <清單.json> 才是真跑)"
    else:
        prior, stale = load_journal(jpath, jobs) if verb == "resume" else ([], [])
        if verb == "launch":                                   # launch 是新的一輪:先把典籍歸到這一輪(空),不讀上一輪的
            save_journal(jpath, {"journal": [], "failed": None, "skipped": []}, verb)
        result = simulate(jobs, hw, journal=prior, fail_name=fail_name, on_fault="skip", gated=gated, runner=run,
                          on_done=lambda names: save_journal(jpath, {"journal": names, "failed": None, "skipped": []}, verb))
        save_journal(jpath, result, verb)
        result["journal_file"] = str(jpath)
    result["resumed_from"] = prior
    result["stale_journal_names"] = stale
    result["rehearsal"] = rehearsal
    status, rc = launch_status(result, rehearsal)
    result["status"] = status
    return result, rc


def _duckdb():
    """資料庫只在呼叫時載入。沒有就不假造 parquet。不在檔案頂層綁死。"""
    try:
        import duckdb
    except ImportError:
        return None
    return duckdb


def _parquet_target(folder: Path, batch: int) -> Path:
    root = folder.resolve()
    target = (root / f"batch_{batch:04d}.parquet").resolve()
    if target.parent != root:
        raise ValueError("parquet 路徑越界")
    return target


def vdf_parquet_increment(folder: str | Path, batch: int, rows: list[tuple[str, int, float]]) -> dict:
    """VDF 的增量。DuckDB 持有本座的庫。寫出的 parquet 只含這次新進的列。重跑同一批不插入。"""
    duckdb = _duckdb()
    if duckdb is None:
        return {"lamp": "ABSENT", "inserted": 0, "replay": False, "parquet": None}
    root = Path(folder)
    root.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(root / "vdf.duckdb"))
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS bars (
                symbol VARCHAR, t INTEGER, close DOUBLE, batch INTEGER,
                PRIMARY KEY (symbol, t)
            )
            """
        )
        con.execute("CREATE TABLE IF NOT EXISTS ingest_log (batch INTEGER PRIMARY KEY, inserted INTEGER)")
        seen = con.execute("SELECT inserted FROM ingest_log WHERE batch = ?", [batch]).fetchone()
        if seen is not None:
            return {"lamp": "GREEN", "inserted": 0, "replay": True, "parquet": None}
        fresh: list[tuple[str, int, float]] = []
        taken: set[tuple[str, int]] = set()
        for symbol, t, close in rows:
            key = (symbol, t)
            if key in taken:
                continue
            taken.add(key)
            fresh.append((symbol, t, float(close)))
        con.execute("CREATE TEMP TABLE incoming (symbol VARCHAR, t INTEGER, close DOUBLE)")
        if fresh:
            con.executemany("INSERT INTO incoming VALUES (?, ?, ?)", fresh)
        con.execute(
            """
            INSERT INTO bars
            SELECT i.symbol, i.t, i.close, ?
            FROM incoming i
            ANTI JOIN bars b ON i.symbol = b.symbol AND i.t = b.t
            """,
            [batch],
        )
        inserted = con.execute("SELECT count(*) FROM bars WHERE batch = ?", [batch]).fetchone()[0]
        parquet_name = None
        if inserted:
            target = _parquet_target(root, batch)
            safe = target.as_posix().replace("'", "''")
            con.execute(
                f"COPY (SELECT symbol, t, close, batch FROM bars WHERE batch = {int(batch)}) TO '{safe}' (FORMAT PARQUET)"
            )
            parquet_name = target.name
        con.execute("INSERT INTO ingest_log VALUES (?, ?)", [batch, inserted])
        return {"lamp": "GREEN", "inserted": int(inserted), "replay": False, "parquet": parquet_name}
    finally:
        con.close()


def vqg_analyze(vdf_folder: str | Path, vqg_folder: str | Path) -> dict:
    """VQG 只讀 VDF 的 parquet。結果寫在自己的庫。不開 vdf.duckdb。沒有管理器。"""
    duckdb = _duckdb()
    if duckdb is None:
        return {"ok": False, "lamp": "ABSENT"}
    files = sorted(Path(vdf_folder).glob("batch_*.parquet"))
    if not files:
        return {"ok": False, "lamp": "RED", "why": "沒有 parquet"}
    root = Path(vqg_folder)
    root.mkdir(parents=True, exist_ok=True)
    glob = (Path(vdf_folder).resolve() / "batch_*.parquet").as_posix().replace("'", "''")
    con = duckdb.connect(str(root / "vqg.duckdb"))
    try:
        got = con.execute(
            f"SELECT symbol, t, close FROM read_parquet('{glob}') ORDER BY symbol, t"
        ).fetchall()
        if not got or any(close is None or symbol is None or t is None for symbol, t, close in got):
            return {"ok": False, "lamp": "RED", "why": "欄位不完整"}
        symbols = sorted({row[0] for row in got})
        if len(symbols) != 1:
            return {"ok": False, "lamp": "RED", "why": f"有 {len(symbols)} 檔標的。持有報酬一次只算一檔，不把不同標的接起來算。"}
        start = float(got[0][2])
        end = float(got[-1][2])
        if start == 0:
            return {"ok": False, "lamp": "RED", "why": "起點是 0"}
        ret = (end - start) / start
        con.execute("CREATE TABLE IF NOT EXISTS result (symbol VARCHAR, rows INTEGER, ret DOUBLE, template VARCHAR)")
        con.execute("DELETE FROM result")
        con.execute(
            "INSERT INTO result VALUES (?, ?, ?, 'TPL-HOLD-0001')",
            [got[0][0], len(got), ret],
        )
        return {
            "ok": True,
            "lamp": "GREEN",
            "symbol": got[0][0],
            "rows": len(got),
            "ret": ret,
            "template": "TPL-HOLD-0001",
        }
    finally:
        con.close()


def vap_view(analysis: dict) -> dict:
    """VAP 只顯示 VQG 的結果。不寫庫，不補管理器。"""
    if not analysis.get("ok"):
        return {"ok": False, "lamp": analysis.get("lamp", "RED"), "lines": [], "note": "沒有可顯示的結果。"}
    pct = analysis["ret"] * 100
    return {
        "ok": True,
        "lamp": "GREEN",
        "symbol": analysis["symbol"],
        "rows": analysis["rows"],
        "template": analysis["template"],
        "ret": analysis["ret"],
        "lines": [
            f"{analysis['symbol']} · {analysis['rows']} 列",
            f"{analysis['template']} · 持有報酬 {pct:.2f}%",
        ],
        "note": "模板回測。不是行情。VQG 與 VAP 仍沒有管理器。",
    }


def pipeline_rehearse(work: str | Path) -> dict:
    """VDF 寫、VQG 讀、VAP 顯示。不新增管理器，不融合。"""
    if _duckdb() is None:
        return {"lamp": "ABSENT", "fusion": False, "managers_added": False, "why": "沒有 duckdb。不假造 parquet。"}
    root = Path(work)
    vdf = root / "vdf"
    vqg = root / "vqg"
    first = vdf_parquet_increment(vdf, 1, [("DEMO", 1, 100.0), ("DEMO", 2, 101.0)])
    replay = vdf_parquet_increment(vdf, 1, [("DEMO", 1, 100.0), ("DEMO", 2, 101.0)])
    second = vdf_parquet_increment(vdf, 2, [("DEMO", 2, 999.0), ("DEMO", 3, 102.0)])
    before = {path.name: _file_sha256(path) for path in vdf.iterdir() if path.is_file()}
    analysis = vqg_analyze(vdf, vqg)
    after = {path.name: _file_sha256(path) for path in vdf.iterdir() if path.is_file()}
    view = vap_view(analysis)
    return {
        "lamp": view["lamp"] if view.get("ok") else "RED",
        "fusion": False,
        "managers_added": False,
        "vdf_unchanged": before == after,
        "inserted": [first["inserted"], replay["inserted"], second["inserted"]],
        "replay": replay["replay"],
        "view": view,
    }


def _spec_found(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False


def source_activates_talib(src: str, tree: ast.AST | None = None) -> bool:
    """L50 的尺是 import 與 _si('talib')，不是全文搜到 talib 這個字。"""
    if tree is None:
        try:
            tree = parse_source(src)
        except SyntaxError:
            return True
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "talib" or alias.name.startswith("talib.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "talib" or node.module.startswith("talib."):
                return True
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_si":
            if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "talib":
                return True
    return False


def preflight(source: str | None = None) -> dict:
    """啟動前快閘。只讀本檔與 find_spec。不安裝、不修復、不寫他系統的檔。"""
    src = source if source is not None else Path(__file__).read_text(encoding="utf-8")
    try:
        shared = parse_source(src)
    except SyntaxError:
        shared = None
    rows: list[dict] = []
    talib_import = True if shared is None else source_activates_talib(src, shared)
    rows.append({
        "id": "libs_source",
        "lamp": "RED" if talib_import else "GREEN",
        "law": "L50",
        "detail": "禁庫只有 TA-Lib 與 talib。尺是 import 與 _si('talib')，不是提到這個字。不另列套件。",
    })
    talib_env = _spec_found("talib")
    rows.append({
        "id": "libs_env",
        "lamp": "RED" if talib_env else "GREEN",
        "law": "L50",
        "detail": "環境解析到 talib 就拒絕啟動。六個動作都不做：不安裝、不載入、不復活、不路由、不當活動基準，也不移除。",
    })
    try:
        cov = engine_coverage(src, shared)
        seat = cov["seat"]
        contract_ok = bool(cov["ok"])
    except Exception as exc:  # noqa: BLE001
        cov = {"covered": 0, "required": 0}
        seat = {"lamp": "RED", "why": str(exc)}
        contract_ok = False
    rows.append({
        "id": "accel_contract",
        "lamp": "GREEN" if contract_ok else "RED",
        "law": "批692B",
        "detail": f"排程指令經加速器 {cov['covered']}/{cov['required']}。",
    })
    rows.append({
        "id": "accel_seat",
        "lamp": seat["lamp"],
        "law": "L09",
        "detail": f"{seat['why']} 只認 {ACCEL_TOOL} {ACCEL_LOCK_VERSION}。本體不在不另造、不安裝。",
    })
    net = find_net_seat()
    rows.append({
        "id": "net_tool",
        "lamp": net["lamp"],
        "law": "L09",
        "detail": f"{net['why']} 只認 {NET_TOOL} {NET_LOCK_VERSION}（{NET_ENGINE_VERSION}）。",
    })
    crosses = re.search(r"(?m)^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_)", src) is not None
    rows.append({
        "id": "dock",
        "lamp": "RED" if crosses else "GREEN",
        "law": "L20",
        "detail": "對接不 import 他系統。短指令的主人仍是既有入口。",
    })
    try:
        jobs = default_jobs()
        py_ok = all(
            job.cmd and job.cmd[0] == sys.executable and "VIA_SuperAccel_Module" in "\n".join(job.cmd)
            for job in jobs
        )
    except Exception:  # noqa: BLE001
        py_ok = False
    rows.append({
        "id": "sched_py",
        "lamp": "GREEN" if py_ok else "RED",
        "law": "L103",
        "detail": "排程指令是 Python 陣列，先掛加速器，沒有 shell 字串。",
    })
    reds = [row["id"] for row in rows if row["lamp"] == "RED"]
    return {
        "rows": rows,
        "ok": not reds,
        "reds": reds,
        "repair": False,
        "install": False,
        "touched_existing": False,
        "net_jobs": "OPEN" if net["lamp"] == "GREEN" else "GATED",
    }


def plan_report(jobs: list[Job] | None = None, hw: HardwareProfile | None = None) -> dict:
    jobs = jobs or default_jobs()
    hw = hw or detect_hardware()
    mounts = [mount(sid) for sid in SYSTEMS]
    gate = preflight()
    return {
        "schema": SCHEMA,
        "engine": ENGINE_ID,
        "accel": ACCEL_MARK,
        "hardware": hw.to_dict(),
        "mounts": mounts,
        "waves": dependency_waves(jobs),
        "jobs": [j.to_dict() for j in jobs],
        "preflight": {"ok": gate["ok"], "reds": gate["reds"], "net_jobs": gate["net_jobs"], "repair": False, "install": False},
        "policy": {
            "fail_fast": False,
            "skip_and_continue": True,
            "auto_retry": False,
            "reset_on_fail": False,
            "resume_from_journal": True,
            "repair_others": False,
            "dock_before_fusion": True,
        },
        "dock_failures": {"count": len(DOCK_FAILURES), "phase": "dock", "fusion": False},
    }


def conform(source: str | None = None) -> dict:
    src = source if source is not None else Path(__file__).read_text(encoding="utf-8")
    try:
        shared = parse_source(src)
    except SyntaxError:
        shared = None
    gate = coverage(src, tree=shared)
    cov = engine_coverage(src, shared)
    mounts = [mount(sid) for sid in ("VCGC", "VDF", "VRN", "VQG", "VAP")]
    present = [m for m in mounts if m["rc"] == 0]
    absent = [m for m in mounts if m["rc"] == 3]
    return {
        "engine": ENGINE_ID,
        "accel_mark": ACCEL_MARK,
        "accel_module": ACCEL_MODULE,
        "accel_lock": ACCEL_LOCK_VERSION,
        "accel_tool": ACCEL_TOOL,
        "net_tool": NET_TOOL,
        "net_lock": NET_LOCK_VERSION,
        "net_engine": NET_ENGINE_VERSION,
        "verb_coverage": gate,
        "engine_coverage": {k: cov[k] for k in ("required", "covered", "ratio", "missing", "ok")},
        "seat": cov["seat"],
        "mounted": [m["system"] for m in present],
        "absent": [m["system"] for m in absent],
        "ok": gate["ok"] and cov["ok"] and len(present) == 3 and len(absent) == 2,
    }


def _check(name: str, cond: bool, detail: str, rows: list[dict]) -> None:
    rows.append({"name": name, "ok": bool(cond), "detail": detail})


def selftest() -> list[dict]:
    rows: list[dict] = []
    src = Path(__file__).read_text(encoding="utf-8")
    gate = coverage(src)
    _check("AST 可解析且加速器標記在檔內", gate["parsed"] and gate["accel"], ACCEL_MARK, rows)
    _check("動詞 100% 由 AST 收齊", gate["ok"], "缺 " + ",".join(gate["missing"]) if gate["missing"] else "15/15", rows)

    bare = "VERBS = ('help', 'status')\n"
    bare_gate = coverage(bare)
    _check("裸檔動詞未滿且無加速器 → 不放行", not bare_gate["ok"] and not bare_gate["accel"], f"ratio={bare_gate['ratio']:.2f}", rows)

    for sid in ("VCGC", "VDF", "VRN"):
        m = mount(sid)
        _check(f"{sid} 外掛裝上", m["rc"] == 0 and m["plugin"] == ENGINE_ID, m["manager"], rows)
    for sid in ("VQG", "VAP"):
        m = mount(sid)
        _check(f"{sid} 無管理器 → ABSENT 不補", m["rc"] == 3 and m["plugin"] is None, m["why"], rows)

    try:
        validate_jobs([Job("x", ["python", "a.py"], 100, "VQG")])
        refused = False
    except ValueError:
        refused = True
    _check("無管理器的系統排不進啟動冊", refused, "VQG", rows)

    hw = detect_hardware(16384, 8)
    _check("16GB 並行上限為 2", hw.max_parallel == 2 and hw.reserve_free_ram_mb >= 3500, str(hw.to_dict()), rows)
    hw32 = detect_hardware(32768, 8)
    _check("32GB 並行不超過 3", hw32.max_parallel <= 3, str(hw32.max_parallel), rows)

    jobs = default_jobs()
    waves = dependency_waves(jobs)
    _check("依賴波次：合併在兩條擷取之後", "VDF_04_Lakehouse_Merge" in waves[-2] or "VDF_04_Lakehouse_Merge" in waves[1], str(waves), rows)

    first = simulate(jobs, detect_hardware(16384, 4), fail_name="VRN_01_PDF_Layout")
    _check("失敗即停且不歸零", first["stopped"] and first["reset"] is False, str(first["journal"]), rows)
    _check("失敗前已完成的留下", "VDF_01_TWSE_Daily" in first["journal"] or "VDF_02_TPEX_Daily" in first["journal"], ",".join(first["journal"]), rows)
    second = simulate(jobs, detect_hardware(16384, 4), journal=first["journal"], fail_name=None)
    replayed = [e["name"] for e in second["events"] if e["kind"] == "start" and e["name"] in first["journal"]]
    _check("續跑不重做已完成節點", not replayed, "重做 " + ",".join(replayed) if replayed else "無重做", rows)
    _check("續跑後日誌蓋滿且沒有失敗", second["failed"] is None and len(second["journal"]) == len(jobs), str(second["journal"]), rows)

    live_mutex: dict[str, str] = {}
    clash = False
    for event in simulate(jobs, detect_hardware(65536, 16))["events"]:
        if event["kind"] == "start":
            job = next(j for j in jobs if j.name == event["name"])
            if job.mutex and job.mutex in live_mutex:
                clash = True
            if job.mutex:
                live_mutex[job.mutex] = job.name
        elif event["kind"] == "done":
            job = next(j for j in jobs if j.name == event["name"])
            if job.mutex and live_mutex.get(job.mutex) == job.name:
                live_mutex.pop(job.mutex, None)
    _check("同一互斥鎖不重疊", not clash, "duckdb_write", rows)

    env = accel_env(jobs[0], hw)
    _check("加速器環境帶標記與執行緒帽", env.get("VIA_PY_ACCEL") == ACCEL_MARK and env.get("POLARS_MAX_THREADS") == str(hw.threads_per_job), env["VIA_PY_ACCEL"], rows)

    picked = pick_newest_tail([
        "SUP_MDL737_SuperAccelModule_v0110.py",
        "SUP_MDL737_SuperAccelModule_v0999.py",
        "SUP_MDL737_SuperAccelModule_v1000.py",
    ])
    _check("尾版用數字不用字母排序", picked == "SUP_MDL737_SuperAccelModule_v1000.py", picked or "", rows)
    _check(
        "鎖冊是 Celeritas v1141 與 AegisNexus v1652",
        ACCEL_LOCK_VERSION == "v1141"
        and NET_LOCK_VERSION == "v1652"
        and NET_ENGINE_VERSION == "1.65.2"
        and ACCEL_TOOL == "VeritasCeleritas"
        and NET_TOOL == "VeritasAegisNexus"
        and TALIB_LIBS == ("TA-Lib", "talib"),
        f"{ACCEL_TOOL} {ACCEL_LOCK_VERSION} / {NET_TOOL} {NET_LOCK_VERSION}",
        rows,
    )

    full = engine_coverage(src)
    _check("啟動面覆蓋 100%", full["ok"] and full["ratio"] == 1.0, f"{full['covered']}/{full['required']}", rows)
    synth = "import os\nVERBS = ('help',)\n"
    bad = engine_coverage(synth)
    _check("拿掉加速器掛點 → 覆蓋不是 100%", not bad["ok"] and bad["ratio"] < 1, f"{bad['ratio']:.2f} 缺 {','.join(bad['missing'][:4])}", rows)

    argv = jobs[0].cmd
    wrapped = all("VIA_SuperAccel_Module" in " ".join(job.cmd) and job.cmd[0] == sys.executable for job in jobs)
    _check("每個任務的指令先掛加速器", wrapped and ACCEL_MODULE in argv[2], argv[1], rows)

    import tempfile

    with tempfile.TemporaryDirectory() as off_tree:
        seat = find_accel_seat(off_tree)
        net = find_net_seat(off_tree)
    seat_ok = seat["lamp"] == "ABSENT" and net["lamp"] == "ABSENT" and seat["version"] == "v1141" and net["version"] == "v1652" and net["engine"] == "1.65.2"
    _check("沒有 VIA 樹就不把缺席說成已載入", seat_ok and seat["via"] == "lock" and net["via"] == "lock", seat["lamp"] + " " + net["lamp"], rows)

    hook = through_accel("launch")
    _check(
        "launch 動詞掛上橋與鎖冊版本",
        hook["module"] == ACCEL_MODULE and hook["accel_lock"] == "v1141" and hook["net_lock"] == "v1652" and hook["tool"] == ACCEL_TOOL and hook["net_tool"] == NET_TOOL,
        hook["bridge"],
        rows,
    )
    try:
        through_accel("shutdown")
        unknown_refused = False
    except ValueError:
        unknown_refused = True
    _check("冊外動詞不掛", unknown_refused, "shutdown", rows)

    skipped_run = simulate(jobs, detect_hardware(16384, 4), fail_name="VRN_01_PDF_Layout", on_fault="skip")
    others_done = "VDF_04_Lakehouse_Merge" in skipped_run["journal"] and "VCGC_03_TestLanes" in skipped_run["journal"]
    _check("跳過後沒有這條邊的系統仍做完", others_done and skipped_run["stopped"] is False, ",".join(skipped_run["journal"]), rows)
    _check(
        "失敗件不進日誌，只有宣告的後續被標前置",
        "VRN_01_PDF_Layout" not in skipped_run["journal"]
        and "VRN_02_Extract" in skipped_run["skipped"]
        and "VDF_01_TWSE_Daily" not in skipped_run["skipped"],
        ",".join(skipped_run["skipped"]),
        rows,
    )
    oom = fold_canon("OOM")
    ram = fold_canon("記憶體不足")
    _check("OOM 與記憶體不足收成同一個典籍碼", oom["code"] == ram["code"] == "RAM_RESERVE", oom["code"], rows)
    _check("對不上的表面不發明新碼", fold_canon("今天月色很好")["code"] == "UNCATALOGUED", "UNCATALOGUED", rows)
    gate_now = preflight()
    _check(
        "政策閘只擋紅燈且不安裝不修復",
        gate_now["repair"] is False and gate_now["install"] is False and gate_now["touched_existing"] is False and gate_now["ok"] == (not gate_now["reds"]),
        "紅 " + ",".join(gate_now["reds"]) if gate_now["reds"] else gate_now["net_jobs"],
        rows,
    )
    poisoned = preflight("import talib\n")
    _check("排程檔出現 talib import 就擋", poisoned["ok"] is False and "libs_source" in poisoned["reds"], ",".join(poisoned["reds"]), rows)
    from_talib = preflight("from talib import SMA\n")
    si_talib = preflight("value = _si('talib')\n")
    mention = preflight("note = '禁止 talib'\n")
    def _lamp(report: dict, row_id: str) -> str:
        return next(row["lamp"] for row in report["rows"] if row["id"] == row_id)
    _check("from talib import 與 _si('talib') 都擋", _lamp(from_talib, "libs_source") == "RED" and _lamp(si_talib, "libs_source") == "RED", "L50", rows)
    _check("只提到 talib 這個字不當成違規", _lamp(mention, "libs_source") == "GREEN", "L50", rows)
    cited = {spec["law"] for spec in SYSTEMS.values()}
    _check("系統律不引用不存在的 L120", cited == {"L20", "L98", "L16 / L101"}, ",".join(sorted(cited)), rows)
    _check(
        "排程指令是帶加速器的 Python 且不 import 他系統",
        any(row["id"] == "sched_py" and row["lamp"] == "GREEN" for row in gate_now["rows"])
        and any(row["id"] == "dock" and row["lamp"] == "GREEN" for row in gate_now["rows"]),
        "sched_py dock",
        rows,
    )
    book = dock_ledger()
    _check(
        "對接失敗冊二十五條且解法不滑進融合",
        book["ok"] and book["fusion"] is False and book["count"] == 25 and book["phase"] == "dock",
        f"{book['count']} leaks={','.join(book['leaks'])}",
        rows,
    )
    _check("10**9 秒不送進 wait", clamp_wait(FASTRUN_BEAT_SENTINEL) is None and clamp_wait(20) == 20 and clamp_wait(None) is None, "沉默", rows)
    review = support_review()
    source_ids = [item["id"] for item in review["sources"]]
    expect_ids = [item[0] for item in SUPPORT_SOURCES]
    _check("省額度來源就是點名的十處", source_ids == expect_ids and len(expect_ids) == 10, " ".join(source_ids), rows)
    _check(
        "沒有索引就不拉全文也不代裝",
        review["pulled_bodies"] is False and review["install"] is False and all(item["lamp"] == "ABSENT" for item in review["sources"]),
        review["station"],
        rows,
    )
    again = support_review(source_ids)
    _check("24 小時內不重讀索引", all(item["lamp"] == "NODATA" for item in again["sources"]), str(INVENTORY_REUSE_HOURS), rows)
    receipt = review["receipt"]
    _check(
        "快跑器溢位對接到沉默等待",
        receipt["wait"] is None and receipt["beat"] == FASTRUN_BEAT_SENTINEL and "v0100" in receipt["cause"],
        receipt["tool"],
        rows,
    )
    _check(
        "盤點冊沒有把快跑器 v0102 登成站",
        receipt["books"]["fastrun_v0102_registered"] is False and receipt["books"]["stations"] == INVENTORY_STATIONS and receipt["books"]["workflows"] == WORKFLOW_COUNT,
        INVENTORY_BOOK,
        rows,
    )
    directive = token_directive()
    rule_ids = [item["id"] for item in directive["rules"]]
    _check(
        "指引只是一行且不另造尺",
        directive["paste"] == "cue"
        and directive["new_meter"] is False
        and directive["verb"] == TOKEN_VERB
        and directive["station"] == TOKEN_STATION
        and "\n" not in directive["cue"]
        and "先呼叫工具" in directive["cue"]
        and "不另造尺" in directive["cue"]
        and rule_ids == ["tool-first", "index-only", "reply-thin", "absent", "reuse", "owner"]
        and review["directive"]["cue"] == TOKEN_CUE,
        TOKEN_STATION,
        rows,
    )
    docked = platform_dock()
    _check(
        "現況包只對接且兩份 Agent OS 是同一份",
        docked["runs"] is False and docked["install"] is False and docked["holds_apply"] is False
        and docked["writes_books"] is False and docked["fusion"] is False
        and docked["go_live"] == "BLOCKED" and docked["agentos_same"] is True
        and docked["agentos_sha"].startswith("97ca853d") and docked["v0194_in_registry"] is False
        and docked["count"] == 47 and "--apply" not in docked["commands"]
        and "agentos" in docked["ids"] and "bench" in docked["ids"] and "fiveentry" in docked["ids"],
        str(docked["count"]),
        rows,
    )
    survey = complement_survey()
    tool_ids = [item["id"] for item in survey["tools"]]
    _check(
        "展勘四名且停在對接",
        tool_ids == ["GRAPHIFY", "OMNIROUTE", "PONYTAIL", "AGENCY-MEM"]
        and survey["phase"] == "dock" and survey["fusion"] is False and survey["writes_books"] is False and survey["install"] is False,
        " ".join(tool_ids),
        rows,
    )
    agency = survey["tools"][-1]
    _check(
        "AGENCY-MEM 沒有站就不登記成引擎",
        agency["id"] == "AGENCY-MEM" and agency["station"] == "" and agency["lamp"] == "ABSENT" and agency["backup"] is False,
        agency["label"],
        rows,
    )
    _check(
        "今日十二站已在冊且備份不收本體也不代跑",
        survey["today"]["count"] == 12 and survey["today"]["already"] is True and survey["today"]["in_backup_zip"] is False
        and survey["backup"]["runs_tools"] is False and survey["backup"]["station"] == "C-daily-backup-v0102"
        and survey["backup"]["scopes"] == ["GRAPHIFY", "OMNIROUTE"],
        str(survey["today"]["count"]),
        rows,
    )
    walk = dock_walk()
    by_id = {step["id"]: step for step in walk["steps"]}
    _check(
        "同義字收成一碼且無管理器不擋有管理器",
        fold_canon("記憶體不足")["code"] == fold_canon("OOM")["code"] == "RAM_RESERVE"
        and by_id["VQG"]["lamp"] == "ABSENT" and by_id["VAP"]["lamp"] == "ABSENT"
        and by_id["VQG"]["code"] == by_id["VAP"]["code"] == "ABSENT_MANAGER"
        and by_id["VCGC"]["lamp"] == by_id["VDF"]["lamp"] == by_id["VRN"]["lamp"] == "GREEN"
        and walk["fusion"] is False and walk["install"] is False,
        by_id["synonym"]["code"],
        rows,
    )
    tool_lamps = [step["lamp"] for step in walk["steps"] if step["lane"] == "工具"]
    _check(
        "對接走完仍不把缺席工具說成已裝",
        tool_lamps == ["ABSENT", "ABSENT", "ABSENT", "ABSENT"]
        and walk["pct"] == 100 and walk["writes_books"] is False and ACCEL_LOCK_VERSION in walk["accel"],
        walk["accel"],
        rows,
    )
    face = assist_interface()
    bumped = {row["id"]: row for row in assist_interface({"VDF": {"why": "只動 VDF"}})["seats"]}
    base = {row["id"]: row for row in face["seats"]}
    book = ast_inventory()
    imports_clear = book["assist_imports"] == 0
    floor = [
        "C-rework-guard-v0100",
        "C-vrn-manager-v0289",
        "C-rework-guard-v0102",
        "C-rework-guard-v0101",
        "C-hub-v0101",
        "C-hub-v0105",
        "C-hub-v0106",
        "C-hub-v0107",
        "C-hub-v0108",
        "C-hub-v0109",
        "C-vrn-eng397-v0130",
        "C-vrn-eng397-v0131",
    ]
    _check(
        "協助接口各走各的且 REGISTER 不丟",
        face["phase"] == "interface" and face["fusion"] is False and face["lost"] == [] and face["duplicates"] == []
        and face["register"] == floor
        and [row["id"] for row in face["seats"]] == ["VCGC", "VDF", "VRN", "VQG", "VAP"]
        and base["VQG"]["phase"] == base["VAP"]["phase"] == "absent"
        and base["VCGC"]["phase"] == base["VDF"]["phase"] == base["VRN"]["phase"] == "interface"
        and bumped["VDF"]["why"] == "只動 VDF" and bumped["VRN"]["why"] == base["VRN"]["why"]
        and bumped["VCGC"]["manager"] == base["VCGC"]["manager"]
        and all(row["blast"] == row["id"] and row["fusion"] is False for row in face["seats"])
        and imports_clear,
        str(len(face["register"])),
        rows,
    )
    _check(
        "語法樹只解析一次且編號不丟",
        book["writes"] is False and book["fusion"] is False
        and book["lost_cls"] == [] and book["lost_fnc"] == [] and book["extra_fnc"] == []
        and book["lost_lib"] == [] and book["extra_lib"] == []
        and book["parse_owners"] == ["parse_source"]
        and book["hold"] == ["_tail_num", "_version_num"]
        and book["absent"] == list(AST_ABSENT)
        and len(book["fnc"]) == len(AST_FNC_FLOOR) and len(book["cls"]) == len(AST_CLS_FLOOR),
        str(len(book["fnc"])),
        rows,
    )
    with tempfile.TemporaryDirectory() as folder:
        rehearsed = pipeline_rehearse(folder)
    if rehearsed.get("lamp") == "ABSENT":
        _check("VDF 增量寫 parquet，VQG 只讀，VAP 只顯示", False, "ABSENT · " + rehearsed["why"] + " 這一條沒跑。", rows)
        rows[-1]["lamp"] = "ABSENT"
    else:
        _check(
            "VDF 增量寫 parquet，VQG 只讀，VAP 只顯示",
            rehearsed["fusion"] is False and rehearsed["managers_added"] is False
            and rehearsed["vdf_unchanged"] is True and rehearsed["replay"] is True
            and rehearsed["inserted"] == [2, 0, 1]
            and rehearsed["view"]["symbol"] == "DEMO"
            and rehearsed["view"]["rows"] == 3
            and rehearsed["view"]["template"] == "TPL-HOLD-0001"
            and abs(rehearsed["view"]["ret"] - 0.02) < 1e-9
            and "不是行情" in rehearsed["view"]["note"],
            str(rehearsed["inserted"]),
            rows,
        )
    if _duckdb() is None:
        _check("多檔標的不接起來算持有報酬", False, "ABSENT · 沒有 duckdb。這一條沒跑。", rows)
        rows[-1]["lamp"] = "ABSENT"
    else:
        with tempfile.TemporaryDirectory() as folder:
            vdf_parquet_increment(Path(folder) / "vdf", 1, [("AAA", 1, 100.0), ("AAA", 2, 110.0), ("BBB", 1, 50.0), ("BBB", 2, 40.0)])
            mixed = vqg_analyze(Path(folder) / "vdf", Path(folder) / "vqg")
        _check("多檔標的不接起來算持有報酬", mixed["ok"] is False and mixed["lamp"] == "RED" and "2 檔" in mixed["why"], mixed.get("why", ""), rows)

    calls: list[list[str]] = []

    def fake_run(cmd, env=None, timeout=None, capture_output=None, text=None):
        calls.append(list(cmd))
        code = 7 if cmd[-1] == "fail" else 0
        return type("Done", (), {"returncode": code, "stdout": "", "stderr": "boom" if code else ""})()

    probe = [
        Job("P_ok", ["python", "-c", "ok"], 100, "VCGC"),
        Job("P_bad", ["python", "-c", "fail"], 100, "VCGC"),
        Job("P_after", ["python", "-c", "after"], 100, "VCGC", deps=["P_bad"]),
    ]
    ran = simulate(probe, detect_hardware(16384, 4), on_fault="skip", runner=lambda job: run_job(job, hw, run=fake_run))
    _check(
        "launch 真的跑指令，完成只看回傳碼",
        ran["executed"] is True and len(calls) == 2 and ran["journal"] == ["P_ok"]
        and ran["failed"] == "P_bad" and "P_after" in ran["skipped"]
        and sorted(r["rc"] for r in ran["runs"]) == [0, 7],
        f"跑了 {len(calls)} 件 · 完成 {ran['journal']}",
        rows,
    )
    import threading
    import time as _time

    live = {"now": 0, "peak": 0}
    lock = threading.Lock()

    def slow_run(cmd, env=None, timeout=None, capture_output=None, text=None):
        with lock:
            live["now"] += 1
            live["peak"] = max(live["peak"], live["now"])
        _time.sleep(0.4)
        with lock:
            live["now"] -= 1
        return type("Done", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    trio = [Job("Q_%d" % i, ["python", "-c", "q%d" % i], 100, "VCGC") for i in range(3)]
    big = detect_hardware(65536, 16)
    t0 = _time.time()
    par = simulate(trio, big, on_fault="skip", runner=lambda job: run_job(job, big, run=slow_run))
    took = _time.time() - t0
    _check("放行的任務真的同時跑(不是一件跑完才跑下一件)", par["journal"] == ["Q_0", "Q_1", "Q_2"] and live["peak"] >= 2
           and took < 1.1, f"同時最多 {live['peak']} 件 · {took:.2f}s(逐件會是 1.2s 以上)", rows)
    with tempfile.TemporaryDirectory() as jdir:
        jp = Path(jdir) / "JOURNAL_latest.json"
        calls.clear()
        first = simulate(probe, detect_hardware(16384, 4), on_fault="skip", runner=lambda job: run_job(job, hw, run=fake_run))
        save_journal(jp, first, "launch")
        prior, stale = load_journal(jp, probe)
        calls.clear()
        again = simulate(probe, detect_hardware(16384, 4), journal=prior, on_fault="skip", runner=lambda job: run_job(job, hw, run=fake_run))
    _check("resume 讀上一輪的完成典籍:已完成的不重跑,失敗的與其下游照實再試",
           prior == ["P_ok"] and stale == [] and all(c[-1] != "ok" for c in calls) and "P_ok" in again["journal"],
           f"典籍 {prior} · 這輪跑了 {[c[-1] for c in calls]}", rows)
    with tempfile.TemporaryDirectory() as jdir:
        jp2 = Path(jdir) / "JOURNAL_latest.json"

        def dies_second(job):
            if job.name == "P_after":
                raise KeyboardInterrupt("中途被打斷")
            return {"name": job.name, "ok": True, "rc": 0, "why": ""}

        chain = [Job("P_ok", ["python", "-c", "ok"], 100, "VCGC"), Job("P_after", ["python", "-c", "after"], 100, "VCGC", deps=["P_ok"])]
        try:
            simulate(chain, detect_hardware(16384, 4), on_fault="skip", runner=dies_second,
                     on_done=lambda names: save_journal(jp2, {"journal": names, "failed": None, "skipped": []}, "launch"))
            interrupted = False
        except KeyboardInterrupt:
            interrupted = True
        kept, _ = load_journal(jp2, chain)
    _check("每完成一件就落典籍:中途被打斷,已完成的照樣在典籍裡(resume 不重跑)", interrupted and kept == ["P_ok"], str(kept), rows)
    with tempfile.TemporaryDirectory() as kdir:
        marker = Path(kdir) / "orphan_wrote.txt"
        inner = "import time,pathlib,sys; time.sleep(2.5); pathlib.Path(sys.argv[1]).write_text('x')"
        outer = "import subprocess,sys; sys.exit(subprocess.call([sys.executable,'-c',sys.argv[1],sys.argv[2]]))"
        tree = Job("K_tree", [sys.executable, "-c", outer, inner, str(marker)], 100, "VCGC", timeout_sec=1)
        killed = run_job(tree, hw)
        import time as _t2
        _t2.sleep(3.0)
        orphan = marker.exists()
    _check("逾時把整棵行程樹砍掉(外層轉接底下的指令不會事後再寫檔)", killed["rc"] == 124 and not orphan,
           f"rc {killed['rc']} · 事後寫檔 {orphan}", rows)
    ok_run = lambda job: {"name": job.name, "ok": True, "rc": 0, "why": ""}   # noqa: E731
    with tempfile.TemporaryDirectory() as ldir:
        lj = Path(ldir) / "JOURNAL_latest.json"
        reh, reh_rc = launch_run("launch", default_jobs(), detect_hardware(65536, 16), [], lj, runner=ok_run)
        _check("占位任務只算演練:REHEARSAL rc 3、不寫典籍(resume 不會因此跳過真工作)",
               reh["status"] == "REHEARSAL" and reh_rc == 3 and not lj.exists(), f"{reh['status']} rc {reh_rc} · 典籍 {lj.exists()}", rows)
        real_jobs = [Job("R_ok", ["python", "-c", "ok"], 100, "VCGC"), Job("R_net", ["python", "-c", "net"], 100, "VDF", mutex="net_x"),
                     Job("R_after", ["python", "-c", "after"], 100, "VDF", deps=["R_net"])]
        part, part_rc = launch_run("launch", real_jobs, detect_hardware(65536, 16), ["R_net"], lj, runner=ok_run)
        _check("網路工具缺席、要連網的任務被擋:INCOMPLETE rc 3(不再回 0),獨立的照跑",
               part["status"] == "INCOMPLETE" and part_rc == 3 and part["journal"] == ["R_ok"] and {"R_net", "R_after"} <= set(part["skipped"]),
               f"{part['status']} rc {part_rc} · 完成 {part['journal']} · 跳過 {part['skipped']}", rows)
        spec = Path(ldir) / "jobs.json"
        spec.write_text(json.dumps({"jobs": [{"name": "J_vcgc", "cmd": ["python", "-c", "pass"], "est_ram_mb": 100, "system": "VCGC"}]}), encoding="utf-8")
        loaded = load_jobs(spec)
        full, full_rc = launch_run("launch", loaded, detect_hardware(65536, 16), [], lj, runner=ok_run)
        kept_full, _ = load_journal(lj, loaded)
        _check("--jobs 真清單:每道先掛加速器、不是演練;全跑完 COMPLETE rc 0 並寫典籍",
               loaded[0].rehearsal is False and loaded[0].cmd[0] == sys.executable and ACCEL_MODULE in loaded[0].cmd[2]
               and full["status"] == "COMPLETE" and full_rc == 0 and kept_full == ["J_vcgc"],
               f"{full['status']} rc {full_rc} · 典籍 {kept_full}", rows)
    utf = run_job(Job("U_utf8", [sys.executable, "-c", "import sys; sys.stdout.buffer.write('\\u5b8c\\u6210 \\u2705\\n'.encode('utf-8')); sys.stdout.buffer.write(b'\\xff\\n')"], 100, "VCGC"), hw)
    _check("子程序輸出一律用 UTF-8 解(父行程是 CP950 也不炸;壞位元組換掉)· 回傳碼照收", utf["ok"] is True and utf["rc"] == 0, str(utf), rows)
    real = run_job(default_jobs()[0], hw)
    want = 0 if VIA_ACCEL is not None else 3
    _check("預設任務的指令實跑：先掛加速器再執行原指令", real["rc"] == want, f"rc {real['rc']} · {real['why']}", rows)
    _check("自測條數與常數一致", len(rows) + 1 == SELFTEST_TOTAL, f"{len(rows) + 1}/{SELFTEST_TOTAL}", rows)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VCGC 啟動引擎 v0100（System Manager 外掛）")
    parser.add_argument("verb", nargs="?", default="help", choices=list(VERBS))
    parser.add_argument("--system", default="", help="mount 時指定系統")
    parser.add_argument("--fail", default="", help="模擬時指定失敗節點，不自動重跑")
    parser.add_argument("--ram-mb", type=int, default=0)
    parser.add_argument("--cores", type=int, default=0)
    parser.add_argument("--jobs", default="", help="launch / resume 的真任務清單 JSON(沒給 = 占位演練,不算完成)")
    parser.add_argument("--journal", default="", help="launch / resume 的完成典籍檔(預設 VIA_Reports/vcgc_startup/JOURNAL_latest.json)")
    args = parser.parse_args(argv)
    verb = args.verb
    hw = detect_hardware(args.ram_mb or None, args.cores or None)

    if verb == "help":
        print(ENGINE_ID)
        print("動詞: " + " ".join(VERBS))
        print("已裝外掛: " + " ".join(s for s, spec in SYSTEMS.items() if spec["has_manager"]))
        print("ABSENT: " + " ".join(s for s, spec in SYSTEMS.items() if not spec["has_manager"]))
        print("加速器: " + ACCEL_TOOL + " " + ACCEL_LOCK_VERSION + " · 橋 " + ACCEL_MODULE)
        print("網路: " + NET_TOOL + " " + NET_LOCK_VERSION + " · " + NET_ENGINE_VERSION)
        print("省額度: 動詞 " + TOKEN_VERB + " 仍歸 " + TOKEN_STATION + " · 來源 " + " ".join(item[0] for item in SUPPORT_SOURCES))
        print("省額度指引: 只貼一行。不另造尺。")
        print("現況對接: " + str(len(PLATFORM_IDS)) + " 列。不跑、不裝、不加 --apply。Agent OS 正式放行 BLOCKED。")
        print("協助接口: 五座各走各的。有管理器的先接口。REGISTER " + str(len(TODAY_STATIONS)) + " 站不丟。融合先不做。")
        print("資料面: VDF 增量 parquet。VQG 只讀。VAP 只顯示。不補管理器。")
        print("展勘: 對接 GRAPHIFY OMNIROUTE PONYTAIL AGENCY-MEM · 今日站 " + str(len(TODAY_STATIONS)) + " 已在冊 · 不改備份尾")
        print("對接輪: 同義字 · 參數 · 管理器 · " + ACCEL_TOOL + " · 備份 · 四工具。走完不是已裝。")
        return 0
    if verb == "version":
        cov = engine_coverage()
        print(json.dumps({
            "engine": ENGINE_ID,
            "schema": SCHEMA,
            "accel": ACCEL_MARK,
            "accel_module": ACCEL_MODULE,
            "accel_lock": ACCEL_LOCK_VERSION,
            "accel_tool": ACCEL_TOOL,
            "net_tool": NET_TOOL,
            "net_lock": NET_LOCK_VERSION,
            "net_engine": NET_ENGINE_VERSION,
            "coverage": f"{cov['covered']}/{cov['required']}",
            "seat": cov["seat"]["lamp"],
        }, ensure_ascii=False))
        return 0 if cov["ok"] else 1
    if verb == "mount":
        if not args.system:
            print(json.dumps([mount(s) for s in SYSTEMS], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(mount(args.system), ensure_ascii=False, indent=2))
        return 0
    if verb in {"conform", "health", "selftest", "test"}:
        if verb == "selftest" or verb == "test":
            rows = selftest()
            failed = [r for r in rows if not r["ok"]]
            for row in rows:
                flag = "PASS" if row["ok"] else row.get("lamp", "FAIL")
                print(f"[{flag}] {row['name']} — {row['detail']}")
            print(f"{len(rows) - len(failed)}/{len(rows)}")
            return 1 if failed else 0
        report = conform()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1
    if verb in {"status", "engines", "records", "peers"}:
        print(json.dumps(plan_report(hw=hw), ensure_ascii=False, indent=2))
        return 0
    if verb in {"plan", "dry-run"}:
        report = plan_report(hw=hw)
        print(json.dumps({"waves": report["waves"], "hardware": report["hardware"]}, ensure_ascii=False, indent=2))
        return 0
    if verb in {"launch", "resume"}:
        hooked = through_accel(verb)
        cov = engine_coverage()
        gate = preflight()
        if not cov["ok"] or not gate["ok"]:
            print(json.dumps({
                "ok": False,
                "why": "政策閘未過，不啟動",
                "missing": cov["missing"],
                "reds": gate["reds"],
                "repair": False,
                "install": False,
            }, ensure_ascii=False, indent=2))
            return 1
        jobs = load_jobs(args.jobs) if args.jobs else default_jobs()
        if gate["net_jobs"] != "OPEN":
            gated = [job.name for job in jobs if (job.mutex or "").startswith("net_")]
        else:
            gated = []
        result, rc = launch_run(verb, jobs, hw, gated, journal_path(args.journal), fail_name=args.fail or None)
        result["accel"] = hooked
        result["coverage"] = {"required": cov["required"], "covered": cov["covered"], "ratio": cov["ratio"], "ok": True}
        result["preflight"] = {"ok": True, "net_jobs": gate["net_jobs"], "repair": False, "install": False, "touched_existing": False}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return rc
    print("未知動詞", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
