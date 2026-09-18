#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL135_EnvGovernance v0100 — 環境治理統一引擎(批381;VIA_EnvManager Unified Governance Engine)
====================================================================================
操作員令(2026-09-07):「依照已成功地建構布局向上新增;最壞還原成原本規劃;
base 只放該有的工具;其他放在 via_core 及 via_ 開頭的環境」+《VIA_EnvManager.py
環境與函式庫防衝突管理規範》(全景式分析先行·uv 極速衝突快篩·衝突立拔與動態隔離·
LKGC 歷史基線與授權閉環·單一 PowerShell 一貼即用·自適應 HTML UI Matrix)。
證據(上船件 VIA_Install_Plan_20260820_062418/230001/235933):三次體檢同狀=
「pip 衝突掃描 FAIL:albucore 0.0.24 requires opencv-python-headless, which is not
installed.」→ 既有工具(EnvFix/InstallGate doctor)未閉環;根因=OCR 家族住在 base。
職權(向上新增;正本零觸碰):
  ① 全景式分析 Panorama — base(本解譯器/--base-python)+ via_core* + via_*/paddle*/
     camelot*/vmt_* 全境:平行探針(--workers;硬逾時可殺=不卡斷;動態進度條)拉
     發行版圖譜(dists/requires/多層遮蔽)+ 逐境 lock 快照。
  ② uv 極速衝突快篩 — uv pip check(毫秒級)→ 退 pip check → 退 DepSuper(MDL046)
     判定 → NOT_RUN 誠實;衝突結構化(requirer/required/spec/installed/kind)。
  ③ base 該有冊 — VIA_EnvGovernance_Baseline(工具鏈+引擎核心+LOW 白名單)+相依閉包
     =base 該有;閉包外=拉出候選;封鎖家族(OCR/DL/瀏覽器/GIS/WebUI…)=RED 立拔。
  ④ 衝突立拔與家族路由 — 衝突要求者所屬家族整包(家族根+境內相依)路由至專屬境
     (via_core 白名單 → 家族 target_env → EnvManager purpose hints → 5D 矩陣 → 黑環境
     via_iso_quarantine 候裁);Lessons SKIP 拒裝名單永不入計畫;cv2 家族換錨 contrib。
  ⑤ 九頭龍風險與分流 — H1 多層遮蔽/H2 跨境大版分歧/H3 共用節點(反向相依≥閾)
     /H4 單寫者/H5 尾版/H6 拒裝;Parallel-Fixable(獨立目標境建/裝/驗)一口氣並行;
     Sequence-Dependent(base 端移除、共用節點、numpy 軸)依拓撲序(Kahn)。
  ⑥ 三輪 — R1 全面性(並行段)/R2 順序性(拓撲段)/R3 收尾硬化(lock/prune 候裁/LKGC)。
  ⑦ 沙盒模擬 — uv pip compile 多輪(EngineForge max_rounds;末兩輪一致=GREEN)→ 退
     pip --dry-run;網路行為過同意閘(VIA_NET_CONSENT=YES);離線 NOT_RUN 誠實。
  ⑧ 授權閉環 — plan 唯讀;apply --approve 才跑 GREEN 非破壞段(建境/裝件/驗證/base
     補齊);base 端移除須 --approve-remove 且目標境 VERIFY 綠後逐件印令執行。
  ⑨ LKGC — 每跑存 LKGC_<ts>.json+lock;全境零衝突且 base 乾淨才晉升 LKGC_latest;
     rollback:①LKGC lock 逐境 uv pip sync ②無 LKGC → 原本規劃(Baseline)重建。
  ⑩ 存證 — logs/env_governance.log(JSONL append-only;成敗皆記)+ VIA_Reports/
     env_governance/RUN_<ts>.json + 四分區(MODULE/ENGINE/FUNCTION-LIB/OTHERS)
     自適應 HTML UI Matrix(小字體、自動換行、RYG、進度條;零跳出 VIA_NO_OPEN)。
用法:via-envgov [run] [--offline] [--roots P1;P2] [--env-root P] [--base-python EXE]
                 [--workers 20] [--task-timeout 120] [--rounds N] [--approve]
                 [--approve-remove] [--open] [--install-plan F]
     via-envgov panorama | plan | apply --approve [--approve-remove] [--only S02,S03] [--only-kind REPAIR_BASE,INSTALL]   (批383:段類過濾;REPAIR_BASE=只補 base manifest 缺件)
     via-envgov tools [--apply --approve] [--tool-env via_vrn_312] [--roster F] [--env-root P]   (批495:工具冊導入——逐境探針→修復/安裝/外部/驗證)

v0107→v0108(批509 操作員實錄:家族境 python 全站 `SRE module mismatch`——探針連 import re 都不行,v0107 會把整境判 UNKNOWN 或當缺件排裝):
  探針失敗且訊息帶 SRE/MAGIC/encodings/Fatal → 境 ENV_BROKEN_INTERP · 件 INTERP_BROKEN(不是 ABSENT,不排 INSTALL)· 只出 REBUILD_ENV 候裁段
  (印 Remove-Item 境 → uv venv → lock 重裝;tools_apply 永不自跑,--approve-remove 亦不跑=境刪除是操作員的手);recover ③ 段列 broken_interp;㊷。
v0106→v0107(批508 操作員令「環境安裝出了問題可以先還原原本前次環境然後把所有工具順序安裝上 中高風險一律單獨隔離」→ 律 L24 環境復原律):
  +recover 動詞(via-envrecover)= ①還原前次(LKGC lock 逐境;無 LKGC → Baseline 原本規劃;sync 破壞段仍候裁 --approve-remove)
  ②順序裝全部工具(段依 境層級 CORE 白名單→LOW 家族境→MEDIUM 隔離境→HIGH 隔離境 × 段類 建境→修復→安裝→驗證 穩定排序;tools 動詞同序)
  ③中高風險一律單獨隔離:_M 家族比照 _H 只認同名獨立境,不再借 alt 境(webui 不借 via_vap_312、ml_boost 不借 via_ml/via_vdf、http_async 不借 via_core);
  執行:--execute --approve;①不受 L19 擋(LKGC 本身即曾 GREEN;同意閘仍要)②新裝段過 L19(RunGate GREEN 24h 內)否則 RESTORED_BLOCKED_UNITEST 誠實停;
  recover 模式下 ENSURE_ENV(uv venv 建隔離境)可執行(只增);存證 RECOVER_latest.json/.ps1 + RECOVER_<run>.json;㊶ 自測。
v0103→v0104(批498 操作員 EnvManager v0300 實錄:via_core 真在(14 件白名單境)——v0103 只在 via_core **不在**時才不排裝,在的話會把
  69 件加速器通用件排進白名單境=違反白名單律):無家族的加速器通用件一律列在虛境「(未路由:加速器通用件)」只作 INFO,永不排進 via_core;
  分發仍走 via-accel-import(MDL142)。實錄另證:via_paddle_311 在(easyocr/paddleocr/pytesseract 齊)、四家族境 Python 3.13.7、
  via_vap_312 pyarrow 半拆+seaborn 缺、pdf2docx/easyocr 要的 opencv-python-headless 依 Baseline 錨 contrib 不裝(接受殘餘)。
v0102→v0103(批497b):via_core 是白名單境(Baseline env_layout.via_core)——聯集裡無家族的加速器通用件在 via_core **不在**時不再排
  ENSURE_ENV+INSTALL 69 件進去,改列 [未路由](INFO;走 via-accel-import 分發三家族境);via_core 在則照探針。標頭批號改讀 BATCH。
v0101→v0102(批497 操作員律「特殊/中高風險者直接拉出獨立環境連同相關工具隔離;numpy 這種常撞的可多環境多版本搭配多 Python;
  加速器及網路工具中的工具很多請勿遺漏」):tools 預設走**全冊聯集**——冊 + Celeritas _LIB_MAP(經 MDL142 roster/pip_name,100+ 件)+
  AegisNexus 相依;每件依 Baseline families 路由(target_env 尾 _H=HIGH 隔離境、_M=MEDIUM、家族境=LOW、無家族→via_core),
  hydra.watch_diverge 樞紐件=SPECIAL(多版本允許;印樞紐矩陣 境×版本 只作 INFO);--sheet-only 只看手寫冊。
v0100→v0101(批495 操作員令「透過 envmanager 安全地導入全部工具,基於目前環境衝突問題修復後,如環境工具管理所定」):
  +tools 動詞——讀工具冊 VIA_ToolRoster_SSOT_v*.json(尾版律;OCR 生態依本冊 families.ocr 進 via_paddle_311 專屬境,不混進 vrn 境):
  逐境(名/別名)找到 python 就跑探針(import → 健康:attr 缺=半拆 BROKEN、版本低=CONFLICT、tesseract 語言包/easyocr 模型=EXTERNAL/NEEDS_MODELS)
  → 段:REPAIR_TOOLS(force-reinstall 半拆件;實錄 via_vap_312 pyarrow 命名空間包)→ INSTALL_TOOLS(缺件/升版;torch 走 CPU index)→ VERIFY_TOOLS
  (重探+uv pip check);境不在→ ENSURE_ENV+INSTALL;外部本體(Tesseract-OCR/語言包/模型)只印令。plan 唯讀寫 TOOLS_PLAN_latest.json/.ps1;
  --apply --approve 才裝(裝前 freeze 存證可回捲;同意閘 VIA_NET_CONSENT 未開=誠實停,不代設)。
     via-envgov lkgc [snapshot|promote|status]
     via-envgov conflicts [--env X] [--limit N]   (批385:自 RUN_latest 印各境衝突明細;零重掃;BASE 預設只印計數)
     via-envgov rollback [--to LKGC_xxx.json | --baseline] [--execute --approve [--approve-remove]]
     via-envgov recover  [--to LKGC_xxx.json | --baseline] [--roster F] [--sheet-only] [--tool-env E] [--env-root P] [--execute --approve [--approve-remove]]   (批508 律 L24:①還原前次 ②順序裝全部工具 ③_M/_H 單獨隔離)
     via-envgov rename [--from 舊境 [--to 新境]] [--execute --approve [--approve-remove]]   (批382 命名律:非 via_ 境換名重建)
     via-envgov matrix | digest | --selftest
紅線:零安裝零刪除預設;破壞段永不自動;尾版律(引擎動態尾版);Zero-Hydra;誠實三態。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import concurrent.futures
import hashlib
import html as _html
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows cp950 主控台印中文
except Exception:
    pass

MODULE_ID = "VIS-ENV-GOVERNANCE-000001"
VERSION = "0108"
BATCH = 509
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ROOT = VIA.parent
SUP = VIA / "supportive modules"
REG = HERE
OUT = VIA / "VIA_Reports" / "env_governance"
LOCK_DIR = OUT / "lock"
LKGC_LOCK_DIR = OUT / "lock_lkgc"
LKGC_LATEST = OUT / "LKGC_latest.json"
RUN_LATEST = OUT / "RUN_latest.json"
MATRIX_LATEST = OUT / "VIA_EnvGovernance_Matrix_latest.html"
LOG_PATH = Path(os.environ.get("VIA_ENV_GOV_LOG") or (VIA / "logs" / "env_governance.log"))
BOOT = {"pip", "setuptools", "wheel", "uv", "packaging"}
_UV = shutil.which("uv")
_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{os.getpid() % 10000:04d}"  # H4 單寫者:並行呼叫(via-lanes)不撞檔
_ARGV_ALL: list[str] = []

CHECK_KINDS = ("MISSING", "MISMATCH", "BROKEN")
LAMP = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴", "NOT_RUN": "⚪", "SKIP": "⚪"}


# ══════════════════════════════════════════════════════════════════════════════
# 基礎工具
# ══════════════════════════════════════════════════════════════════════════════
def canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", str(name or "").strip()).lower()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def machine_hash() -> str:
    return hashlib.sha256(f"{platform.node()}|{platform.system()}".encode()).hexdigest()[:16]


# ===== [VIA:TAILPICK-BRIDGE:v0100] 尾版取用正典橋(批590;正典 SUP_MDL751_VIATailPick)=====
# 批589 量到 CGC 族最大的一筆整合債:**33 個家族各寫一份 `newest`**,而且 32 份裡有 13 種行為
# ——最大兩群的參數順序是相反的、兩支走 rglob、一支缺件回 pattern、一支按 mtime 排序。
# 批590 把規則收進正典並**逐群重放證明零損失**(8 種變體 × 6 組語料,48 組全同)。
# 這裡是**模組層綁定**不是再定義一支橋函式:本檔從此不再有 `def newest`,
# 能力庫裡這一家族就真的消失了(再包一層 def 的話家族數不會掉,等於沒併)。
# `newest_pr` = 參數順序 (pattern, root),沿用本檔原本的用法,呼叫端零改動。
import importlib.util as _tp_ilu
from pathlib import Path as _tp_Path
_TP_MOD = None
_tp_p = _tp_Path(__file__).resolve()
while _tp_p.parent != _tp_p:
    _tp_hits = sorted((_tp_p / "supportive modules").glob("SUP_MDL751_VIATailPick_v*.py"))
    if _tp_hits:
        _tp_spec = _tp_ilu.spec_from_file_location("VIA_TAILPICK", _tp_hits[-1])
        _TP_MOD = _tp_ilu.module_from_spec(_tp_spec)
        _tp_spec.loader.exec_module(_TP_MOD)
        break
    _tp_p = _tp_p.parent
if _TP_MOD is None:      # 大聲壞掉:回錯檔比壞掉更糟(尾版取錯=整條鏈指到舊引擎)
    raise RuntimeError("[FAIL] 尾版取用正典缺席:supportive modules/SUP_MDL751_VIATailPick_v*.py")
_newest = _TP_MOD.newest_pr
# ===== [VIA:TAILPICK-BRIDGE:END] =====


def _arg_after(args: list, flag: str):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return None


# ===== [VIA:JSONIO-BRIDGE:v0100] JSON 讀寫正典橋(批592;正典 SUP_MDL752_VIAJsonIO)=====
# 本處原本的行為:utf-8-sig · try/except→第二個位置參數 default
# 批592 量過:活樹尾版 168 支只有 **20 處**定義 / **17 個行為群**(debt 報的 83/35 檔含版本史,LL142)。
# 差異軸:讀=編碼 utf-8-sig vs utf-8(**活的不一致**:帶 BOM 的檔有些引擎讀得到有些讀不到)、
# 缺檔與壞檔**是兩個旋鈕**(合成一個 default 會把壞檔說成不存在=假的零,LL138);
# 寫=原子寫 / indent / 尾換行 / default=str ——**indent 與尾換行是產出契約,不得統一**。
# 所以正典把差異變成明示選項,並逐群重放證零損失(讀 9 種 × 4 語料全同;寫 4 種**逐位元組相同**)。
# 這裡是**綁定**不是再定義一支 def(寫 def 家族數不會掉=等於沒併,LL143)。
import importlib.util as _js_ilu
from pathlib import Path as _js_Path
_JS_MOD = None
_js_p = _js_Path(__file__).resolve()
while _js_p.parent != _js_p:
    _js_hits = sorted((_js_p / "supportive modules").glob("SUP_MDL752_VIAJsonIO_v*.py"))
    if _js_hits:
        _js_spec = _js_ilu.spec_from_file_location("VIA_JSONIO", _js_hits[-1])
        _JS_MOD = _js_ilu.module_from_spec(_js_spec)
        _js_spec.loader.exec_module(_JS_MOD)
        break
    _js_p = _js_p.parent
if _JS_MOD is None:      # 大聲壞掉:讀錯編碼/寫錯 indent 都是無聲的錯
    raise RuntimeError("[FAIL] JSON 讀寫正典缺席:supportive modules/SUP_MDL752_VIAJsonIO_v*.py")
_read_json = _JS_MOD.bind_read()
# ===== [VIA:JSONIO-BRIDGE:END] =====


_write_json = _JS_MOD.bind_write(indent=1, default=str, newline=True)


def log_event(kind: str, env: str = "", pkg: str = "", verdict: str = "", detail: str = "", **extra) -> None:
    """logs/env_governance.log:JSONL append-only(成敗皆記;寫失敗誠實吞不炸)。"""
    row = {"ts": now_iso(), "run_id": _RUN_ID, "module": f"CGC_MDL135_v{VERSION}", "machine": machine_hash(),
           "kind": kind, "env": env, "pkg": pkg, "verdict": verdict, "detail": str(detail)[:400]}
    row.update({k: v for k, v in extra.items() if v is not None})
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _consent() -> bool:
    return os.environ.get("VIA_NET_CONSENT", "").upper() in ("YES", "1", "TRUE")


def _no_open() -> bool:
    return os.environ.get("VIA_NO_OPEN", "") == "1"


def _load_by_path(mod_name: str, path: Path):
    try:
        spec = importlib.util.spec_from_file_location(mod_name, str(path))
        if spec is None or spec.loader is None:
            return None
        m = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = m  # dataclass+future annotations 需先掛載
        try:
            spec.loader.exec_module(m)
        except Exception:
            sys.modules.pop(mod_name, None)
            raise
        return m
    except Exception:
        return None


def run_cmd(argv: list, timeout: int = 120, cwd: Path | None = None, input_text: str | None = None) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run([str(a) for a in argv], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, cwd=str(cwd) if cwd else None,
                           input=input_text, stdin=None if input_text is not None else subprocess.DEVNULL)
        return {"rc": r.returncode, "out": r.stdout or "", "err": r.stderr or "", "s": round(time.time() - t0, 2)}
    except subprocess.TimeoutExpired:
        return {"rc": -9, "out": "", "err": f"TIMEOUT {timeout}s(硬逾時殺除,不卡斷)", "s": round(time.time() - t0, 2)}
    except Exception as exc:
        return {"rc": -1, "out": "", "err": f"{type(exc).__name__}:{str(exc)[:160]}", "s": round(time.time() - t0, 2)}


# ══════════════════════════════════════════════════════════════════════════════
# 政策載入:Baseline(本冊)+ EnvManager 政策母版 + 5D 矩陣 + Lessons SKIP + EngineForge
# ══════════════════════════════════════════════════════════════════════════════
_FALLBACK_BASELINE = {
    "base": {"python_expected": "3.13", "toolchain": ["pip", "setuptools", "wheel", "packaging", "uv"],
             "engine_core": ["pandas", "numpy", "pyarrow", "duckdb", "pymupdf", "requests", "jsonschema", "plotly",
                             "matplotlib", "openpyxl", "scipy", "rich", "psutil", "docx2python", "python-docx"],
             "low_risk_allow": ["colorama", "click", "tabulate", "humanize"],
             "never_in_base_families": ["ocr", "deep_learning", "browser"]},
    "families": {
        "ocr": {"members": ["paddleocr", "paddlex", "paddlepaddle", "albumentations", "albucore", "opencv-contrib-python",
                            "opencv-python", "opencv-python-headless", "opencv-contrib-python-headless", "onnxruntime"],
                "target_env": "paddle_312", "alt_envs": ["paddle_311"], "python": "3.12"},
        "deep_learning": {"members": ["torch", "torchvision", "tensorflow", "jax"], "target_env": "via_iso_ml_cuda_H",
                          "alt_envs": [], "python": "3.11"},
        "browser": {"members": ["playwright", "selenium"], "target_env": "via_iso_scrape_H", "alt_envs": [], "python": "3.11"},
    },
    "cv2_family": ["opencv-python", "opencv-python-headless", "opencv-contrib-python", "opencv-contrib-python-headless"],
    "cv2_anchor": "opencv-contrib-python",
    "env_layout": {"via_core": {"aliases": ["via_core", "via_core_312", "venv_core"], "python": "3.12"},
                   "via_iso_quarantine": {"python": "3.12"}, "protected_envs": ["via_core", "via_core_312", "vmt_pm"]},
    "managed_prefixes": ["via_", "base", "paddle", "camelot", "vmt_", "venv_core", "vgf_"],
    "hydra": {"watch_diverge": ["numpy", "pandas", "pyarrow", "torch", "paddlepaddle", "pydantic", "protobuf", "sqlalchemy"],
              "shared_node_threshold": 5, "high_risk_mix_threshold": 3},
    "rounds": {"max_rounds": 3},
    "mirror_chain": {"order": ["https://pypi.tuna.tsinghua.edu.cn/simple", "https://mirrors.aliyun.com/pypi/simple/",
                               "https://pypi.org/simple"], "labels": ["tsinghua", "aliyun", "pypi-official"]},
    "install_plan_ingest": {"glob": "VIA_Reports/VIA_Install_Plan_*.json",
                            "intake": "supportive modules/references/intake/VIA_EnvGovernance_InstallPlans_b381",
                            "stage": "pip 衝突掃描", "persisted_threshold": 2},
}


def load_baseline() -> dict:
    p = _newest("VIA_EnvGovernance_Baseline_v*.json", REG)
    d = _read_json(p, None) if p else None
    if not isinstance(d, dict) or "base" not in d:
        d = json.loads(json.dumps(_FALLBACK_BASELINE))
        d["_src"] = "內建保底(本冊缺)"
    else:
        d["_src"] = p.name
    return d


_EM = None


def em_policy():
    """EnvManager 政策母版(唯讀 import;缺=None graceful)。"""
    global _EM
    if _EM is None:
        _EM = _load_by_path("VIA_EnvManager_policy_ro", SUP / "VIA_EnvManager.py") or False
    return _EM or None


def em_list(attr: str, fallback: list) -> list:
    em = em_policy()
    vals = getattr(em, attr, None) if em else None
    return [canon(x) for x in (vals if isinstance(vals, list) and vals else fallback)]


def core_whitelist() -> set:
    return set(em_list("def_PARAM_VIA_CORE_WHITELIST", [
        "pip", "setuptools", "wheel", "packaging", "requests", "httpx", "aiohttp", "orjson", "numpy", "pandas",
        "pyarrow", "duckdb", "polars", "openpyxl", "xlsxwriter", "plotly", "fastapi", "uvicorn", "rich", "loguru", "pydantic"]))


def high_risk() -> set:
    return set(em_list("def_PARAM_HIGH_RISK_LIBS", ["torch", "tensorflow", "paddleocr", "paddlepaddle", "opencv-python",
                                                    "opencv-contrib-python", "onnxruntime", "playwright", "selenium"]))


def medium_risk() -> set:
    return set(em_list("def_PARAM_MEDIUM_RISK_LIBS", ["pymupdf", "pdfplumber", "polars", "duckdb", "pyarrow", "plotly",
                                                      "fastapi", "uvicorn", "aiohttp", "httpx", "orjson", "openpyxl", "xlsxwriter"]))


def purpose_hints() -> dict:
    em = em_policy()
    raw = getattr(em, "def_PARAM_ENV_PURPOSE_HINTS", None) if em else None
    if not isinstance(raw, dict) or not raw:
        raw = {"via_core": ["requests", "httpx", "aiohttp", "orjson", "numpy", "pandas", "pyarrow", "duckdb", "polars",
                            "plotly", "openpyxl", "xlsxwriter", "fastapi", "uvicorn"],
               "via_vdf": ["numpy", "pandas", "pyarrow", "duckdb", "polars", "plotly", "openpyxl", "xlsxwriter"],
               "via_vrn": ["pymupdf", "pdfplumber", "numpy", "pandas", "pyarrow"],
               "paddle_311": ["paddleocr", "paddlepaddle", "opencv-python"],
               "camelot_311": ["camelot-py", "tabula-py", "pdfplumber"]}
    return {k: [canon(x) for x in v] for k, v in raw.items()}


def matrix5d_route() -> dict:
    """5D 矩陣 lib_index(序號→件名)× environments(libs 序號)→ 件名→境(首見)。"""
    d = _read_json(REG / "VIA_Env_Matrix_5D_v0100.json", {})
    idx = {str(k): canon(v) for k, v in (d.get("lib_index") or {}).items()}
    out = {}
    for env in d.get("environments") or []:
        for n in env.get("libs") or []:
            nm = idx.get(str(n))
            if nm and nm not in out:
                out[nm] = env.get("via_name")
    return out


def lessons_skip() -> dict:
    """Lessons 帳本 SKIP 拒裝名單 {canon 件名: scope};缺=空。"""
    p = _newest("VIA_Lessons_Ledger_v*.json", REG)
    d = _read_json(p, {}) if p else {}
    return {canon(e["pkg"]): e.get("scope", "everywhere") for e in d.get("entries", [])
            if e.get("kind") == "SKIP" and e.get("pkg")}


def forge_policy() -> dict:
    cands = sorted(SUP.glob("VIA_EngineForge_Config*.json"))
    cands = [c for c in cands if "template" not in c.name.lower()] + [c for c in cands if "template" in c.name.lower()]
    for c in cands:
        pol = _read_json(c, {}).get("policy", {})
        if pol:
            return {"src": c.name, **pol}
    return {"src": "內建保底", "sandbox_first": True, "append_only": True, "destructive_delete": False, "max_rounds": 3}


# ══════════════════════════════════════════════════════════════════════════════
# 需求字串/衝突行解析(純函式;可自測)
# ══════════════════════════════════════════════════════════════════════════════
_REQ_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def parse_req(raw: str) -> tuple[str, str, bool]:
    """'opencv-python-headless>=4.9; extra == "x"' → (canon 名, spec, optional_extra?)。"""
    s = str(raw or "")
    body, _, marker = s.partition(";")
    m = _REQ_NAME.match(body)
    name = canon(m.group(1)) if m else ""
    spec = body[m.end():].strip() if m else ""
    spec = re.sub(r"^\[[^\]]*\]", "", spec).strip()
    optional = "extra" in marker
    return name, spec, optional


_PIP_MISSING = re.compile(r"^(?P<a>\S+) (?P<av>\S+) requires (?P<b>[^,]+), which is not installed\.?$")
_PIP_MISMATCH = re.compile(r"^(?P<a>\S+) (?P<av>\S+) has requirement (?P<spec>.+?), but you have (?P<b>\S+) (?P<bv>\S+?)\.?$")
_UV_MISSING = re.compile(r"^The package `(?P<a>[^`]+)` requires `(?P<spec>[^`]+)`, but it's not installed")
_UV_MISMATCH = re.compile(r"^The package `(?P<a>[^`]+)` requires `(?P<spec>[^`]+)`, but `(?P<bv>[^`]+)` is installed")
_UV_BROKEN = re.compile(r"^The package `(?P<a>[^`]+)` is broken or incomplete")


def parse_check_lines(text: str, source: str = "uv", env: str = "BASE") -> list[dict]:
    """pip check / uv pip check 輸出 → 結構化衝突列(去重保序)。"""
    out, seen = [], set()
    for line in (text or "").splitlines():
        t = line.strip()
        if not t:
            continue
        rec = None
        m = _PIP_MISSING.match(t)
        if m:
            b, spec, _ = parse_req(m.group("b"))
            rec = {"requirer": canon(m.group("a")), "requirer_ver": m.group("av"), "required": b, "spec": spec,
                   "installed": "", "kind": "MISSING"}
        if rec is None:
            m = _PIP_MISMATCH.match(t)
            if m:
                b, spec, _ = parse_req(m.group("spec"))
                rec = {"requirer": canon(m.group("a")), "requirer_ver": m.group("av"), "required": canon(m.group("b")),
                       "spec": spec, "installed": m.group("bv"), "kind": "MISMATCH"}
        if rec is None:
            m = _UV_MISSING.match(t)
            if m:
                b, spec, _ = parse_req(m.group("spec"))
                rec = {"requirer": canon(m.group("a")), "requirer_ver": "", "required": b, "spec": spec,
                       "installed": "", "kind": "MISSING"}
        if rec is None:
            m = _UV_MISMATCH.match(t)
            if m:
                b, spec, _ = parse_req(m.group("spec"))
                rec = {"requirer": canon(m.group("a")), "requirer_ver": "", "required": b, "spec": spec,
                       "installed": m.group("bv"), "kind": "MISMATCH"}
        if rec is None:
            m = _UV_BROKEN.match(t)
            if m:
                rec = {"requirer": canon(m.group("a")), "requirer_ver": "", "required": "", "spec": "",
                       "installed": "", "kind": "BROKEN"}
        if rec is None:
            continue
        rec.update({"env": env, "source": source, "raw": t[:200]})
        key = (rec["requirer"], rec["required"], rec["kind"])
        if key not in seen:
            seen.add(key)
            out.append(rec)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# ① 環境發現 + 平行探針(硬逾時;動態進度條)
# ══════════════════════════════════════════════════════════════════════════════
def env_python(env_path: Path) -> Path | None:
    for sub in ("Scripts/python.exe", "bin/python", "bin/python3", "python.exe"):
        p = env_path / sub
        if p.exists():
            return p
    return None


def discover_roots(extra: list[str], env_root: str | None = None) -> list[Path]:
    roots: list[Path] = []
    if env_root:
        roots.append(Path(env_root))
    for raw in os.environ.get("VIA_ENV_ROOTS", "").split(os.pathsep):
        if raw.strip():
            roots.append(Path(raw.strip()))
    roots += [Path(x) for x in extra if x]
    em = em_policy()
    for c in (getattr(em, "def_PARAM_ENV_ROOT_CANDIDATES", None) or []) if em else []:
        roots.append(Path(str(c)))
    roots += [Path.home() / "envs", Path.home() / ".virtualenvs", VIA / "Environments"]
    seen, out = set(), []
    for r in roots:
        k = str(r).lower()
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def is_managed(name: str, prefixes: list[str]) -> bool:
    n = name.strip().lower()
    return any(n.startswith(p.lower()) for p in prefixes) and not n.startswith("_retire_")


def discover_envs(baseline: dict, extra_roots: list[str], env_root: str | None, base_python: str | None,
                  only: str | None = None) -> list[dict]:
    bp = base_python or sys.executable
    in_venv = (sys.prefix != getattr(sys, "base_prefix", sys.prefix)) and not base_python
    envs = [{"name": "BASE", "path": str(Path(bp).parent.parent) if base_python else sys.prefix, "py": bp,
             "kind": "base(本解譯器)" if not base_python else "base(--base-python)",
             "warn": "本解譯器為 venv 非 base;建議 --base-python <系統 python>" if in_venv else ""}]
    prefixes = baseline.get("managed_prefixes") or ["via_", "base", "paddle", "camelot"]
    for root in discover_roots(extra_roots, env_root):
        try:
            if not root.is_dir():
                continue
            for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
                if not child.is_dir() or not is_managed(child.name, prefixes):
                    continue
                py = env_python(child)
                if not ((child / "pyvenv.cfg").exists() or py):
                    continue
                if any(e["name"].lower() == child.name.lower() for e in envs):
                    continue  # 同名境(H1):首根先得,誠實不重列
                envs.append({"name": child.name, "path": str(child), "py": str(py) if py else None, "kind": "venv",
                             "root": str(root), "warn": "" if py else "python 執行檔缺(BROKEN 候)"})
        except Exception:
            continue
    if only:
        envs = [e for e in envs if e["name"].lower() == only.lower() or e["name"] == "BASE"]
    return envs


PROBE_SRC = r"""
import json, re, sys, platform, site
def canon(s): return re.sub(r"[-_.]+", "-", s).lower()
from importlib.metadata import distributions
eff, seen = {}, {}
try:
    usr = site.getusersitepackages() or ""
except Exception:
    usr = ""
for d in distributions():
    try:
        name = canon((d.metadata["Name"] or "").strip())
        if not name: continue
        p = getattr(d, "_path", None)
        root = str(p.parent) if p is not None else "?"
        layer = "user" if usr and root.lower().startswith(usr.lower()) else ("os" if "dist-packages" in root.replace("\\", "/") else "site")
        lst = seen.setdefault(name, [])
        if root not in [x["root"] for x in lst]:
            lst.append({"ver": d.version or "0", "root": root, "layer": layer})
        if name not in eff:
            eff[name] = {"ver": d.version or "0", "requires": list(d.requires or []), "layer": layer}
    except Exception: continue
print(json.dumps({"python": platform.python_version(), "prefix": sys.prefix, "exe": sys.executable,
 "user_site": usr, "dists": eff, "dup": {n: l for n, l in seen.items() if len(l) > 1}}))
"""


def probe_env(env: dict, timeout: int = 120) -> dict:
    if not env.get("py"):
        return {"ok": False, "err": "python 執行檔缺(BROKEN 候)"}
    r = run_cmd([env["py"], "-c", PROBE_SRC], timeout=timeout)
    if r["rc"] != 0:
        return {"ok": False, "err": (r["err"] or "探針 rc%s" % r["rc"]).strip()[-160:]}
    try:
        line = [l for l in r["out"].splitlines() if l.strip().startswith("{")][-1]
        return {"ok": True, **json.loads(line), "s": r["s"]}
    except Exception as exc:
        return {"ok": False, "err": f"探針輸出解析失敗:{type(exc).__name__}"}


def fast_check(env: dict, timeout: int = 90) -> dict:
    """uv pip check(毫秒級)→ pip check → NOT_RUN 誠實。"""
    py = env.get("py")
    if not py:
        return {"tool": "NOT_RUN", "rc": -1, "conflicts": [], "note": "python 缺"}
    if _UV:
        r = run_cmd([_UV, "pip", "check", "--python", py], timeout=timeout)
        text = (r["out"] + "\n" + r["err"])
        if r["rc"] in (0, 1) and ("Checked" in text or "incompatib" in text or "The package" in text):
            return {"tool": "uv", "rc": r["rc"], "conflicts": parse_check_lines(text, "uv", env["name"]), "s": r["s"]}
    r = run_cmd([py, "-m", "pip", "check"], timeout=max(timeout, 180))
    text = (r["out"] + "\n" + r["err"])
    if "No module named pip" in text:
        return {"tool": "NOT_RUN", "rc": r["rc"], "conflicts": [], "note": "境內無 pip 且 uv 缺(NOT_RUN 誠實)"}
    if r["rc"] in (0, 1) and r["rc"] != -9:
        return {"tool": "pip", "rc": r["rc"], "conflicts": parse_check_lines(text, "pip", env["name"]), "s": r["s"]}
    return {"tool": "NOT_RUN", "rc": r["rc"], "conflicts": [], "note": (r["err"] or "?")[:120]}


BAR_W = 24


def _bar_line(done: int, total: int, t0: float, active: set, spin: int) -> str:
    filled = int(BAR_W * done / total) if total else BAR_W
    b = "█" * filled + "░" * (BAR_W - filled)
    act = "、".join(sorted(active)[:3]) or "—"
    return "  %s [%s] %d/%d · %.0fs · 探針中: %s" % ("|/-\\"[spin % 4], b, done, total, time.time() - t0, act[:36])


def panorama(envs: list[dict], workers: int = 20, task_timeout: int = 120, quiet: bool = False) -> list[dict]:
    """全景式分析:平行探針+快篩;硬逾時可殺;動態進度條(非 TTY 改行印)。"""
    total = len(envs)
    t0 = time.time()
    active: set = set()
    lock = threading.Lock()
    done_n = [0]
    results: dict[str, dict] = {}

    def one(env: dict) -> tuple[str, dict]:
        with lock:
            active.add(env["name"])
        try:
            pr = probe_env(env, timeout=task_timeout)
            chk = fast_check(env, timeout=max(30, task_timeout // 2)) if pr.get("ok") else {"tool": "NOT_RUN", "conflicts": [], "note": "探針失敗"}
            return env["name"], {"env": env, "probe": pr, "check": chk}
        except Exception as exc:
            return env["name"], {"env": env, "probe": {"ok": False, "err": f"{type(exc).__name__}"}, "check": {"tool": "NOT_RUN", "conflicts": []}}
        finally:
            with lock:
                active.discard(env["name"])
                done_n[0] += 1

    stop = threading.Event()
    tty = sys.stdout.isatty() and not quiet

    def painter():
        spin, last = 0, 0.0
        while not stop.is_set():
            if tty:
                sys.stdout.write("\r" + _bar_line(done_n[0], total, t0, active, spin).ljust(110))
                sys.stdout.flush()
            elif not quiet and time.time() - last > 3:
                print(_bar_line(done_n[0], total, t0, active, spin), flush=True)
                last = time.time()
            spin += 1
            stop.wait(0.3)

    th = threading.Thread(target=painter, daemon=True)
    th.start()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for name, payload in ex.map(one, envs):
            results[name] = payload
    stop.set()
    th.join(timeout=1)
    if tty:
        sys.stdout.write("\r" + _bar_line(done_n[0], total, t0, set(), 0).ljust(110) + "\n")
    scans = []
    for env in envs:
        p = results.get(env["name"], {})
        pr, chk = p.get("probe", {}), p.get("check", {})
        row = {"env": env, "ok": bool(pr.get("ok")), "python": pr.get("python", "?"), "err": pr.get("err", ""),
               "dists": pr.get("dists", {}) if pr.get("ok") else {}, "dup": pr.get("dup", {}) if pr.get("ok") else {},
               "user_site": pr.get("user_site", ""), "check_tool": chk.get("tool", "NOT_RUN"),
               "conflicts": chk.get("conflicts", []), "check_note": chk.get("note", ""), "probe_s": pr.get("s")}
        log_event("SCAN_ENV", env["name"], verdict="OK" if row["ok"] else "FAIL",
                  detail=f"python={row['python']} dists={len(row['dists'])} check={row['check_tool']} conflicts={len(row['conflicts'])} {row['err']}")
        scans.append(row)
    return scans


# ══════════════════════════════════════════════════════════════════════════════
# ②③④ 分析:manifest 閉包 / 家族路由 / 衝突分類 / 九頭龍
# ══════════════════════════════════════════════════════════════════════════════
def manifest_sets(baseline: dict) -> dict:
    b = baseline.get("base", {})
    tool = {canon(x) for x in b.get("toolchain", [])}
    core = {canon(x) for x in b.get("engine_core", [])}
    low = {canon(x) for x in b.get("low_risk_allow", [])}
    return {"toolchain": tool, "engine_core": core, "low_risk_allow": low, "all": tool | core | low | BOOT}


def family_index(baseline: dict) -> dict:
    """canon 件名 → 家族鍵。"""
    idx = {}
    for fam, spec in (baseline.get("families") or {}).items():
        for m in spec.get("members", []):
            idx.setdefault(canon(m), fam)
    return idx


def closure(dists: dict, roots: set, blocked: set | None = None, follow_optional: bool = True) -> set:
    """已裝相依閉包;封鎖家族件永不被閉包收留。
    follow_optional=True(base 該有冊):extra 可選相依已裝即視為支援件(保守留 base);
    follow_optional=False(家族整包/白名單群):只走必要相依(批382 工作站實錄:extras 把 bleach/greenlet 拖進 browser 家族=誤判根因)。"""
    blocked = blocked or set()
    keep, stack = set(), [r for r in roots if r in dists]
    while stack:
        n = stack.pop()
        if n in keep or n in blocked:
            continue
        keep.add(n)
        for raw in dists[n].get("requires", []):
            nm, _spec, opt = parse_req(raw)
            if opt and not follow_optional:
                continue
            if nm and nm in dists and nm not in keep and nm not in blocked:
                stack.append(nm)
    return keep


def reverse_deps(dists: dict) -> dict:
    rev: dict[str, set] = {}
    for n, info in dists.items():
        for raw in info.get("requires", []):
            nm, _s, opt = parse_req(raw)
            if nm and nm in dists and not opt:
                rev.setdefault(nm, set()).add(n)
    return rev


def env_alias_of(name: str, baseline: dict) -> str:
    """境名 → 規範鍵(via_core_312/venv_core → via_core;paddle_311 → paddle_312 家族錨等)。"""
    n = name.lower()
    for key, spec in (baseline.get("env_layout") or {}).items():
        if not isinstance(spec, dict):
            continue
        if n == key.lower() or n in [a.lower() for a in spec.get("aliases", [])]:
            return key
    if n.startswith("via_core"):
        return "via_core"
    return name


def resolve_target(fam: str, baseline: dict, present_envs: set) -> tuple[str, str, bool]:
    """家族 → (目標境, python 版, 已存在?):主目標存在優先;否則別境存在;否則主目標(待建)。"""
    spec = (baseline.get("families") or {}).get(fam, {})
    cands = [spec.get("target_env", "")] + list(spec.get("alt_envs", []))
    pres = {e.lower(): e for e in present_envs}
    for c in cands:
        if c and c.lower() in pres:
            return pres[c.lower()], spec.get("python", ""), True
    return (cands[0] or "via_iso_quarantine"), spec.get("python", "3.12"), False


def route_package(pkg: str, baseline: dict, present_envs: set, skips: dict) -> dict:
    """單件路由(routing_order):SKIP → via_core 白名單 → 家族 → purpose hints → 5D → 黑環境。"""
    p = canon(pkg)
    if skips.get(p) == "everywhere":
        return {"pkg": p, "target": "", "python": "", "exists": False, "via": "lessons_skip", "note": "拒裝名單(everywhere)永不入計畫"}
    fam = family_index(baseline).get(p)
    ov = {canon(k): v for k, v in (baseline.get("package_env_overrides") or {}).items()}
    if p in ov:  # explicit_preferred_env:本冊專屬境覆寫(catboost→via_catboost;lightgbm→via_lightgbm;onnxruntime→via_onnxruntime)
        pres = {e.lower(): e for e in present_envs}
        return {"pkg": p, "target": pres.get(ov[p].lower(), ov[p]), "python": "", "exists": ov[p].lower() in pres, "via": "package_env_overrides", "family": fam or ""}
    if p in core_whitelist():  # 政策母版白名單優先(既有健康 via_core 承接;routing_order)
        pres = {e.lower(): e for e in present_envs}
        for a in ["via_core"] + list((baseline.get("env_layout") or {}).get("via_core", {}).get("aliases", [])):
            if a.lower() in pres:
                return {"pkg": p, "target": pres[a.lower()], "python": "3.12", "exists": True, "via": "via_core_whitelist", "family": fam or ""}
        return {"pkg": p, "target": "via_core", "python": "3.12", "exists": False, "via": "via_core_whitelist", "family": fam or ""}
    if fam:
        tgt, pyv, ex = resolve_target(fam, baseline, present_envs)
        return {"pkg": p, "target": tgt, "python": pyv, "exists": ex, "via": "family", "family": fam}
    for env_name, hints in purpose_hints().items():
        if p in hints:
            pres = {e.lower(): e for e in present_envs}
            return {"pkg": p, "target": pres.get(env_name.lower(), env_name), "python": "", "exists": env_name.lower() in pres,
                    "via": "envmanager_purpose_hints", "family": ""}
    m5 = matrix5d_route().get(p)
    if m5:
        pres = {e.lower(): e for e in present_envs}
        return {"pkg": p, "target": pres.get(m5.lower(), m5), "python": "", "exists": m5.lower() in pres, "via": "matrix_5d", "family": ""}
    q = "via_iso_quarantine"
    pres = {e.lower(): e for e in present_envs}
    return {"pkg": p, "target": pres.get(q, q), "python": "3.12", "exists": q in pres, "via": "quarantine", "family": ""}


_IMPORT_NAME = {"pymupdf": "fitz", "python-docx": "docx", "beautifulsoup4": "bs4", "pillow": "PIL", "opencv-python": "cv2", "opencv-contrib-python": "cv2",
                "opencv-python-headless": "cv2", "opencv-contrib-python-headless": "cv2", "scikit-learn": "sklearn", "scikit-image": "skimage", "pyyaml": "yaml",
                "python-dateutil": "dateutil", "pdfminer-six": "pdfminer", "python-pptx": "pptx", "pypdf2": "PyPDF2", "opencc-python-reimplemented": "opencc",
                "readability-lxml": "readability", "python-dotenv": "dotenv", "typing-extensions": "typing_extensions", "markdown-it-py": "markdown_it", "attrs": "attr",
                "camelot-py": "camelot", "tabula-py": "tabula", "requests-html": "requests_html", "curl-cffi": "curl_cffi", "spacy-pkuseg": "spacy_pkuseg",
                "pywin32": "win32api", "msgpack": "msgpack", "tables": "tables", "gradio-client": "gradio_client", "flake8-polyfill": "flake8_polyfill"}
_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)
_ENGINE_INDEX: dict | None = None


def import_name(pkg: str) -> str:
    return _IMPORT_NAME.get(canon(pkg), canon(pkg).replace("-", "_"))


def engine_import_index(force: bool = False) -> dict:
    """倉庫引擎 import 索引 {檔名: {頂層模組}}(一次掃描快取;排除退役/收容/鏡像/副本)——家族拉出後之引擎影響評估(以 base python 啟動之引擎會失去該件)。"""
    global _ENGINE_INDEX
    if _ENGINE_INDEX is not None and not force:
        return _ENGINE_INDEX
    idx: dict[str, set] = {}
    skip = ("VIA_RetiredEngines", "references", "SCOPE_COPY", "BACKUP", "__pycache__", "_superseded", "_nexuscore", "VIA_Standalone_Package", "VIA_CentralGovernance_ALL")
    for root in (VIA / "functional modules", REG, SUP):
        if not root.is_dir():
            continue
        for f in root.rglob("*.py"):
            sp = str(f)
            if any(k in sp for k in skip) or re.search(r"_sha[0-9a-f]{6,}", f.name):
                continue
            try:
                mods = {m.lower() for m in _IMPORT_RE.findall(f.read_text(encoding="utf-8", errors="replace"))}
            except Exception:
                continue
            if mods:
                idx[f.stem] = mods
    _ENGINE_INDEX = idx
    return idx


def engine_impact(pkgs, index: dict) -> dict:
    """件群 → 倉庫中 import 該件之引擎(檔名);純函式可自測。"""
    names = {import_name(p).lower() for p in pkgs}
    hit = sorted(f for f, mods in index.items() if mods & names)
    return {"n": len(hit), "names": hit}


def naming_check(scans: list[dict], baseline: dict) -> list[dict]:
    """H7 命名律(批382):受管境一律 via_ 前綴;非 via_ 境=NAMING_VIOLATION(BASE/_retire_/受保護境/冊 exempt 豁免;批385 工作站實錄 vmt_pm 受保護境被列=噪音)。"""
    law = baseline.get("naming_law") or {}
    prefix = str(law.get("prefix", "via_")).lower()
    renames = {k.lower(): v for k, v in (law.get("renames") or {}).items()}
    exempt = {str(x).lower() for x in (law.get("exempt") or [])} | {str(x).lower() for x in ((baseline.get("env_layout") or {}).get("protected_envs") or [])}
    out = []
    for s in scans:
        n = s["env"]["name"]
        if n == "BASE" or n.lower().startswith(prefix) or n.startswith("_retire_") or n.lower() in exempt:
            continue
        out.append({"env": n, "suggested": renames.get(n.lower(), prefix + n), "python": s.get("python"), "path": s["env"].get("path"),
                    "py": s["env"].get("py"), "n_dists": _ndists(s), "ok": s.get("ok"), "conflicts": len(s.get("conflicts", []))})
    for v in out:
        log_event("NAMING", v["env"], "", "YELLOW", f"非 via_ 境 → {v['suggested']}(via-envgov rename)")
    return out


def analyze_base(scan: dict, baseline: dict, present_envs: set, skips: dict) -> dict:
    """base 該有冊比對:manifest 缺件 / 相依閉包 / 拉出候選(家族整包;單寫者律)/ 影響評估(閉包相依+引擎 import)。"""
    dists = scan.get("dists", {}) or {}
    ms = manifest_sets(baseline)
    fidx = family_index(baseline)
    never = set(baseline.get("base", {}).get("never_in_base_families", []))
    overrides = {canon(k): v for k, v in (baseline.get("package_env_overrides") or {}).items()}
    blocked_pkgs = {p for p, f in fidx.items() if f in never}
    manifest_missing = sorted(p for p in (ms["toolchain"] | ms["engine_core"]) if p not in dists and p not in BOOT)
    keep = closure(dists, ms["all"], blocked=blocked_pkgs)
    os_managed = sorted(p for p, i in dists.items() if i.get("layer") == "os" and p not in blocked_pkgs)  # Linux 發行版 dist-packages=OS 管理,不動不列
    extras = sorted(p for p in dists if p not in keep and p not in BOOT and p not in os_managed)
    ov_pkgs = sorted(p for p in extras if p in overrides)  # ① 專屬境覆寫(catboost→via_catboost 等)
    # ② routing_order:via_core 白名單優先(政策母版)——白名單件+其必要相依閉包成群改道 via_core
    wl = core_whitelist()
    wl_roots = sorted(p for p in extras if p in wl and p not in overrides)
    wl_members = (closure(dists, set(wl_roots), blocked=blocked_pkgs - set(wl_roots), follow_optional=False) - keep - BOOT - set(ov_pkgs)) if wl_roots else set()
    fam_pool = [p for p in extras if p not in wl_members and p not in overrides]
    # ③ 家族整包:只走必要相依;單寫者律(H4b)=件只歸一家族;多家族共用相依=共用支援件(最後候裁)
    rev = reverse_deps(dists)
    claims: dict[str, set] = {}
    fam_roots: dict[str, set] = {}
    fam_full: dict[str, set] = {}
    for fam in sorted({fidx[p] for p in fam_pool if p in fidx}):
        roots = {p for p in fam_pool if fidx.get(p) == fam}
        full = closure(dists, roots, follow_optional=False)
        fam_roots[fam], fam_full[fam] = roots, full
        for m in full - keep - BOOT - wl_members - set(ov_pkgs):
            if fidx.get(m) in (fam, None):  # 他家族件歸他家族(各自拉出;目標境仍自足=install 含之)
                claims.setdefault(m, set()).add(fam)
    shared = sorted(m for m, fs in claims.items() if len(fs) > 1)
    bundles: dict[str, dict] = {}
    assigned: set = set(shared)
    index = engine_import_index() if fam_roots else {}
    for fam, roots in fam_roots.items():
        members = sorted(m for m, fs in claims.items() if fs == {fam})
        tgt, pyv, ex = resolve_target(fam, baseline, present_envs)
        impact = sorted({r for m in members for r in rev.get(m, set()) if r in keep})
        eng = engine_impact(roots, index)
        bundles[fam] = {"family": fam, "blocked": fam in never, "roots": sorted(roots), "members": members,
                        "install": sorted(fam_full[fam] - BOOT), "target": tgt, "python": pyv, "target_exists": ex, "impact_kept": impact,
                        "engines_n": eng["n"], "engines": eng["names"][:8],
                        "severity": "RED" if fam in never else "YELLOW"}
        assigned |= set(members)
    unclassified = [p for p in extras if p not in assigned and p not in overrides]
    routed_other: dict[str, list] = {}
    for p in unclassified:
        r = route_package(p, baseline, present_envs, skips)
        via = r["via"] if (p in wl_roots or p not in wl_members) else "via_core_whitelist(相依隨行)"
        if p in wl_members and p not in wl_roots:  # 白名單件之私有相依隨行同境
            r = route_package(wl_roots[0], baseline, present_envs, skips) if wl_roots else r
        routed_other.setdefault(r["target"] or "(拒裝)", []).append({"pkg": p, "ver": dists[p]["ver"], "via": via,
                                                                   "note": r.get("note", ""), "exists": r["exists"], "python": r["python"]})
    pres = {e.lower(): e for e in present_envs}
    for p in ov_pkgs:
        tgt = overrides[p]
        routed_other.setdefault(pres.get(tgt.lower(), tgt), []).append({"pkg": p, "ver": dists[p]["ver"], "via": "package_env_overrides",
                                                                        "note": "專屬境(本冊 package_env_overrides)", "exists": tgt.lower() in pres, "python": ""})
    blocked_present = sorted(p for p in dists if p in blocked_pkgs)
    return {"n_dists": len(dists), "manifest_missing": manifest_missing, "keep_n": len(keep), "extras": extras,
            "bundles": bundles, "routed_other": routed_other, "blocked_present": blocked_present, "os_managed": os_managed,
            "shared_support": shared, "overrides": ov_pkgs, "manifest_src": baseline.get("_src", "")}


def classify_conflicts(scans: list[dict], baseline: dict, base_analysis: dict, skips: dict) -> list[dict]:
    """衝突分類:base 封鎖家族=PULL_OUT(RED);base manifest 件缺相依=REPAIR_BASE;
    via_* 境=REBUILD 候(委 MDL050);SKIP 件被要求且 cv2 錨在=METADATA_SHADOWED(YELLOW,非 base)。"""
    fidx = family_index(baseline)
    never = set(baseline.get("base", {}).get("never_in_base_families", []))
    cv2f = {canon(x) for x in baseline.get("cv2_family", [])}
    out = []
    for s in scans:
        name = s["env"]["name"]
        dists = s.get("dists", {})
        for c in s.get("conflicts", []):
            req, need = c["requirer"], c["required"]
            fam = fidx.get(req) or fidx.get(need)
            rec = dict(c)
            rec["family"] = fam or ""
            if name == "BASE":
                if fam in never or req in base_analysis.get("extras", []):
                    rec["action"], rec["severity"] = "PULL_OUT", "RED"
                    rec["note"] = f"要求者 {req} 屬 base 不該有({fam or '閉包外'})→ 家族整包拉出"
                elif need in skips and skips[need] == "everywhere":
                    rec["action"], rec["severity"] = "PULL_OUT", "RED"
                    rec["note"] = f"所需 {need} 為拒裝件(Lessons SKIP)→ 要求者 {req} 拉出 base"
                else:
                    rec["action"], rec["severity"] = "REPAIR_BASE", "YELLOW"
                    rec["note"] = f"manifest/閉包件缺相依 {need}{c.get('spec','')} → base 補齊(非封鎖件)"
            else:
                if need in cv2f and skips.get(need) == "everywhere" and any(x in dists for x in cv2f):
                    rec["action"], rec["severity"] = "METADATA_SHADOWED", "YELLOW"
                    rec["note"] = "cv2 家族換錨 contrib 遮蔽(metadata-only 殘餘;接受,不裝 headless)"
                elif c["kind"] == "BROKEN":
                    rec["action"], rec["severity"] = "REBUILD", "RED"
                    rec["note"] = "發行版損壞 → 旁建重建(via-rebuild --env)"
                else:
                    rec["action"], rec["severity"] = "REBUILD", "RED"
                    rec["note"] = "境內衝突 → via-rebuild --env(MDL050 旁建零破壞)/ 原地修補候裁"
            log_event("CONFLICT", name, req, rec["severity"], f"{rec['action']}:{c['raw']}", required=need, conflict_kind=c["kind"], source=c.get("source"))
            out.append(rec)
    return out


def hydra_risks(scans: list[dict], baseline: dict, base_analysis: dict) -> list[dict]:
    h = baseline.get("hydra", {})
    watch = [canon(x) for x in h.get("watch_diverge", [])]
    thr = int(h.get("shared_node_threshold", 5))
    out = []
    # H2 跨境大版分歧
    for lib in watch:
        vers = {s["env"]["name"]: s["dists"][lib]["ver"] for s in scans if s.get("ok") and lib in s.get("dists", {})}
        majors = {v.split(".")[0] for v in vers.values()}
        if len(majors) > 1:
            out.append({"code": "H2_DIVERGE", "sev": "YELLOW", "pkg": lib, "detail": f"大版分歧 {'/'.join(sorted(majors))}:{vers}", "seq": True})
    # H1 多層遮蔽
    for s in scans:
        if s.get("dup"):
            out.append({"code": "H1_DUP_LAYERS", "sev": "YELLOW", "pkg": ",".join(sorted(s["dup"])[:8]), "env": s["env"]["name"],
                        "detail": f"同名多層 {len(s['dup'])} 件(使用者層蓋系統層;via-install --doctor 深診)", "seq": True})
    # H3 共用節點(base 反向相依 ≥ 閾)碰到拉出包
    base = next((s for s in scans if s["env"]["name"] == "BASE"), None)
    if base and base.get("ok"):
        rev = reverse_deps(base["dists"])
        shared = {p: len(v) for p, v in rev.items() if len(v) >= thr}
        touched = set()
        for b in base_analysis.get("bundles", {}).values():
            touched |= set(b["members"])
        hit = sorted(p for p in touched if p in shared)
        if hit:
            out.append({"code": "H3_SHARED_NODE", "sev": "RED", "pkg": ",".join(hit[:8]),
                        "detail": f"拉出包含共用節點(反向相依≥{thr}):{ {p: shared[p] for p in hit[:8]} } → 一律 Sequence-Dependent", "seq": True})
        out.append({"code": "H3_SHARED_TOP", "sev": "GREEN", "pkg": ",".join(f"{p}({n})" for p, n in sorted(shared.items(), key=lambda x: -x[1])[:8]),
                    "detail": f"base 共用節點 {len(shared)} 件(閾 {thr})", "seq": False})
    # 高風險混居
    hr = high_risk()
    mix_thr = int(h.get("high_risk_mix_threshold", 3))
    for s in scans:
        if s["env"]["name"] == "BASE" or not s.get("ok"):
            continue
        hi = sorted(n for n in s["dists"] if n in hr)
        if len(hi) >= mix_thr:
            out.append({"code": "HIGH_RISK_MIX", "sev": "YELLOW", "env": s["env"]["name"], "pkg": ",".join(hi[:6]),
                        "detail": f"高風險混居 {len(hi)} 件(閾 {mix_thr})→ via-rebuild --split {s['env']['name']}", "seq": True})
    for r in out:
        log_event("HYDRA", r.get("env", "BASE"), r.get("pkg", ""), r["sev"], f"{r['code']}:{r['detail']}")
    return out


def analyze_via_envs(scans: list[dict], baseline: dict) -> list[dict]:
    """via_core 白名單違規 / via_* 境四態。"""
    rows = []
    wl = core_whitelist()
    fidx = family_index(baseline)
    for s in scans:
        name = s["env"]["name"]
        if name == "BASE":
            continue
        row = {"env": name, "python": s.get("python"), "n_dists": len(s.get("dists", {})), "conflicts": len(s.get("conflicts", [])),
               "check_tool": s.get("check_tool"), "status": "OK", "notes": []}
        if not s.get("ok"):
            row["status"] = "BROKEN"
            row["notes"].append(s.get("err", "探針失敗"))
        elif s.get("conflicts"):
            row["status"] = "REBUILD"
        if env_alias_of(name, baseline) == "via_core" and s.get("ok"):
            keep = closure(s["dists"], wl | BOOT)
            off = sorted(p for p in s["dists"] if p not in keep and p not in BOOT)
            if off:
                row["core_violations"] = off
                if row["status"] == "OK":
                    row["status"] = "WARN"
                row["notes"].append(f"via_core 白名單外 {len(off)} 件 → 依家族改道:" + ", ".join(f"{p}→{fidx.get(p, '?')}" for p in off[:6]))
        if s.get("dup") and row["status"] == "OK":
            row["status"] = "WARN"
        if "__rb" in name:
            row["notes"].append("旁建候換境(MDL050 via-rebuild 驗綠後切換候裁;原境不動)")
        law = baseline.get("naming_law") or {}
        if not name.lower().startswith(str(law.get("prefix", "via_")).lower()) and not name.startswith("_retire_"):
            row["notes"].append(f"命名律違反(H7)→ via-envgov rename(建議 {(law.get('renames') or {}).get(name, law.get('prefix', 'via_') + name)})")
            if row["status"] == "OK":
                row["status"] = "WARN"
        rows.append(row)
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# 上船件證據:VIA_Install_Plan_*.json(Provision --check)攝入
# ══════════════════════════════════════════════════════════════════════════════
def ingest_install_plans(baseline: dict, extra_files: list[str]) -> dict:
    cfg = baseline.get("install_plan_ingest", {})
    files: list[Path] = []
    for pat in [cfg.get("glob", "VIA_Reports/VIA_Install_Plan_*.json")]:
        files += sorted(VIA.glob(pat))
    intake = VIA / cfg.get("intake", "supportive modules/references/intake/VIA_EnvGovernance_InstallPlans_b381")
    if intake.is_dir():
        files += sorted(intake.glob("*.json"))
    files += [Path(f) for f in extra_files if f]
    seen_notes: dict[str, int] = {}
    rows = []
    for f in files:
        d = _read_json(f, None)
        if not isinstance(d, dict) or d.get("schema") != "VIA.InstallPlan.v1":
            continue
        st = {s.get("stage"): s for s in d.get("stages", [])}
        bad = st.get(cfg.get("stage", "pip 衝突掃描"), {})
        note = bad.get("note", "") if bad and not bad.get("ok", True) else ""
        conf = parse_check_lines(note, "install_plan", "BASE") if note else []
        if note:
            seen_notes[note] = seen_notes.get(note, 0) + 1
        rows.append({"file": f.name, "ts": d.get("ts"), "machine": d.get("machine_hash"), "python": (st.get("Python") or {}).get("note"),
                     "fail_stages": [k for k, v in st.items() if not v.get("ok", True)], "pip_note": note[:160], "conflicts": conf})
    persisted = [{"note": n, "count": c} for n, c in seen_notes.items() if c >= int(cfg.get("persisted_threshold", 2))]
    return {"n_plans": len(rows), "plans": rows[-6:], "persisted": persisted}


# ══════════════════════════════════════════════════════════════════════════════
# ⑤⑥ 計畫:段/分流/拓撲序/三輪
# ══════════════════════════════════════════════════════════════════════════════
def _pins_for_bundle(bundle: dict, dists: dict, baseline: dict, skips: dict) -> tuple[list[str], list[str]]:
    """家族包 → 目標境安裝 pins(鎖 base 現版=LKGC 精神);cv2 換錨;SKIP everywhere 剔除。"""
    cv2f = {canon(x) for x in baseline.get("cv2_family", [])}
    anchor = canon(baseline.get("cv2_anchor", "opencv-contrib-python"))
    pins, dropped, cv_done = [], [], False
    for m in bundle.get("install") or bundle["members"]:
        if skips.get(m) == "everywhere":
            dropped.append(m)
            continue
        if m in cv2f:
            if not cv_done:
                ver = dists.get(anchor, {}).get("ver")
                pins.append(f"{anchor}=={ver}" if ver else anchor)
                cv_done = True
            continue
        ver = dists.get(m, {}).get("ver")
        pins.append(f"{m}=={ver}" if ver else m)
    if not cv_done and any(m in cv2f for m in (bundle.get("install") or bundle["members"])):
        pins.append(anchor)
    return pins, dropped


def build_plan(scans: list[dict], baseline: dict, base_analysis: dict, conflicts: list[dict], hydra: list[dict],
               via_rows: list[dict], env_root: str, skips: dict, naming: list[dict] | None = None) -> dict:
    """段冊:ENSURE_ENV/INSTALL/VERIFY(並行)→ REMOVE_BASE(候裁序跑)→ VERIFY base → LOCK → PROMOTE。"""
    base = next((s for s in scans if s["env"]["name"] == "BASE"), {})
    dists = base.get("dists", {}) if base else {}
    stages: list[dict] = []
    n = [0]

    def add(kind, env, **kw):
        n[0] += 1
        st = {"id": f"S{n[0]:02d}", "kind": kind, "env": env, "deps": [], "cls": "PARALLEL", "round": 1, "destructive": False,
              "sim": {"state": "NOT_RUN", "risk": "NOT_RUN", "note": ""}, "result": {"state": "PENDING"}}
        st.update(kw)
        stages.append(st)
        return st

    shared_hit = set()
    for r in hydra:
        if r["code"] == "H3_SHARED_NODE":
            shared_hit |= set(r["pkg"].split(","))
    verify_ids_by_env: dict[str, str] = {}
    ensure_by_env: dict[str, str] = {}
    # 家族整包 → 目標境
    for fam, b in sorted(base_analysis.get("bundles", {}).items()):
        pins, dropped = _pins_for_bundle(b, dists, baseline, skips)
        tgt = b["target"]
        env_path = str(Path(env_root) / tgt)
        if tgt not in ensure_by_env:
            e = add("ENSURE_ENV", tgt, python=b["python"], env_path=env_path, exists=b["target_exists"],
                    goal=f"確保目標境 {tgt}(Python {b['python'] or '同 base'};{'已在=SKIP' if b['target_exists'] else 'uv venv 新建'})")
            ensure_by_env[tgt] = e["id"]
        i = add("INSTALL", tgt, pins=pins, dropped=dropped, family=fam, env_path=env_path, python=b["python"], deps=[ensure_by_env[tgt]], no_deps=True,
                goal=f"家族 {fam} 整包 {len(pins)} 件裝入 {tgt}(完整閉包鎖 base 現版;--no-deps 防解析器回拉拒裝件;拒裝剔除 {len(dropped)})", severity=b["severity"])
        v = add("VERIFY", tgt, env_path=env_path, deps=[i["id"]], goal=f"uv pip check {tgt}")
        verify_ids_by_env[f"{tgt}:{fam}"] = v["id"]
        seq = bool(set(b["members"]) & shared_hit) or bool(b.get("impact_kept"))
        rm = add("REMOVE_BASE", "BASE", pins=b["members"], family=fam, deps=[v["id"]], cls="SEQUENTIAL", round=2, destructive=True,
                 goal=f"base 端移除家族 {fam} {len(b['members'])} 件(候裁;--approve-remove;目標境 VERIFY 綠後)",
                 note=("共用節點/閉包相依受影響:" + ", ".join(b.get("impact_kept", [])[:6])) if seq else "獨立包(無閉包相依)")
        rm["seq_reason"] = "H3 共用節點/閉包相依" if seq else "破壞性一律序跑"
    # 閉包外未分類/白名單件 → 各目標境(單件)
    for tgt, items in sorted(base_analysis.get("routed_other", {}).items()):
        if tgt == "(拒裝)":
            continue
        pins = [f"{it['pkg']}=={it['ver']}" for it in items]
        env_path = str(Path(env_root) / tgt)
        pyv = next((it.get("python") for it in items if it.get("python")), "")
        ex = any(it.get("exists") for it in items)
        if tgt not in ensure_by_env:
            e = add("ENSURE_ENV", tgt, python=pyv, env_path=env_path, exists=ex, goal=f"確保目標境 {tgt}({'已在' if ex else '新建'})")
            ensure_by_env[tgt] = e["id"]
        via = sorted({it["via"] for it in items})
        i = add("INSTALL", tgt, pins=pins, dropped=[], family="(單件路由:" + "/".join(via) + ")", env_path=env_path, python=pyv,
                deps=[ensure_by_env[tgt]], goal=f"閉包外 {len(pins)} 件改道 {tgt}", severity="YELLOW")
        v = add("VERIFY", tgt, env_path=env_path, deps=[i["id"]], goal=f"uv pip check {tgt}")
        add("REMOVE_BASE", "BASE", pins=[it["pkg"] for it in items], family="(單件)", deps=[v["id"]], cls="SEQUENTIAL", round=2, destructive=True,
            goal=f"base 端移除閉包外 {len(items)} 件(候裁;--approve-remove)", note="單件路由;移除前目標境須 VERIFY 綠")
    # 共用支援件(多家族必要相依;單寫者律):待所有家族目標境 VERIFY 綠後最後候裁移除
    if base_analysis.get("shared_support"):
        fam_verifies = [s["id"] for s in stages if s["kind"] == "VERIFY" and s["env"] != "BASE"]
        add("REMOVE_BASE", "BASE", pins=list(base_analysis["shared_support"]), family="(共用支援件)", deps=fam_verifies, cls="SEQUENTIAL", round=2, destructive=True,
            goal=f"base 端移除共用支援件 {len(base_analysis['shared_support'])} 件(多家族相依;所有家族境 VERIFY 綠後最後候裁;--approve-remove)",
            note="H4b 單寫者律:多家族共用相依不歸任一家族,各目標境自足後方移除")
    # 命名律(H7):非 via_ 境 → 委派 via-envgov rename(換名重建;唯讀印令)
    for v in (naming or []):
        add("RENAME_ENV", v["env"], cls="SEQUENTIAL", round=2, goal=f"命名律:{v['env']} → {v['suggested']}(uv venv 同 Python {v.get('python') or '?'} + uv pip sync 舊境 lock + check;驗綠後舊境 _retire_ 候裁)",
            argv_hint=f"via-envgov rename --from {v['env']} --execute --approve", note="via-envgov rename 唯讀出令;--execute --approve 建境+同步+驗證;--approve-remove 退役舊境")
    # base manifest 缺件補齊(非封鎖件)
    repair = [c["required"] + (c.get("spec") or "") for c in conflicts if c.get("action") == "REPAIR_BASE" and c.get("required")]
    repair += base_analysis.get("manifest_missing", [])
    repair = sorted(set(p for p in repair if p and skips.get(canon(re.split(r"[<>=!~]", p)[0])) != "everywhere"))
    if repair:
        seq = any(canon(re.split(r"[<>=!~]", p)[0]) in shared_hit for p in repair)
        add("REPAIR_BASE", "BASE", pins=repair, cls="SEQUENTIAL" if seq else "PARALLEL", round=2 if seq else 1,
            goal=f"base 該有冊補齊 {len(repair)} 件(manifest 缺件+閉包相依缺)", note="只增不減;--upgrade-strategy only-if-needed")
    # via_* 境:重建/拆分委派(唯讀印令)
    for row in via_rows:
        if row["status"] in ("REBUILD", "BROKEN"):
            add("DELEGATE_REBUILD", row["env"], cls="SEQUENTIAL", round=2, goal=f"{row['env']} {row['status']} → via-rebuild --env {row['env']}(MDL050 旁建零破壞)",
                argv_hint=f"via-rebuild --env {row['env']}", note="; ".join(row.get("notes", [])))
        if row.get("core_violations"):
            add("DELEGATE_SPLIT", row["env"], cls="SEQUENTIAL", round=2, goal=f"{row['env']} 白名單外 {len(row['core_violations'])} 件 → via-rebuild --split {row['env']}",
                argv_hint=f"via-rebuild --split {row['env']}", pins=row["core_violations"][:20])
    for r in hydra:
        if r["code"] == "HIGH_RISK_MIX":
            add("DELEGATE_SPLIT", r["env"], cls="SEQUENTIAL", round=2, goal=r["detail"], argv_hint=f"via-rebuild --split {r['env']}")
    # base 驗證 + R3 硬化
    rm_ids = [s["id"] for s in stages if s["kind"] in ("REMOVE_BASE", "REPAIR_BASE")]
    if rm_ids:
        add("VERIFY", "BASE", deps=rm_ids, cls="SEQUENTIAL", round=2, goal="base 端 pip/uv check 回驗(移除+補齊後)")
    all_ver = [s["id"] for s in stages if s["kind"] == "VERIFY"]
    lk = add("LOCK", "*", deps=all_ver, cls="SEQUENTIAL", round=3, goal="R3 收尾:逐境 lock 快照(VIA_Reports/env_governance/lock)")
    add("PRUNE", "*", deps=[lk["id"]], cls="SEQUENTIAL", round=3, goal="R3 硬化:uv cache prune(候裁;印令不自跑)", argv_hint="uv cache prune")
    add("PROMOTE_LKGC", "*", deps=[lk["id"]], cls="SEQUENTIAL", round=3, goal="LKGC 晉升判定(全境零衝突且 base 乾淨)")
    order = topo_order(stages)
    waves = wave_groups(stages, order)
    return {"stages": stages, "order": order, "waves": waves,
            "n_parallel": sum(1 for s in stages if s["cls"] == "PARALLEL"), "n_sequential": sum(1 for s in stages if s["cls"] == "SEQUENTIAL"),
            "n_destructive": sum(1 for s in stages if s["destructive"])}


def topo_order(stages: list[dict]) -> list[str]:
    """Kahn 拓撲序(A04);同層以 round、cls(PARALLEL 先)、id 排序;循環=誠實截斷。"""
    ids = {s["id"] for s in stages}
    indeg = {s["id"]: len([d for d in s["deps"] if d in ids]) for s in stages}
    by = {s["id"]: s for s in stages}
    ready = sorted([i for i, d in indeg.items() if d == 0], key=lambda i: (by[i]["round"], by[i]["cls"] != "PARALLEL", i))
    out = []
    while ready:
        cur = ready.pop(0)
        out.append(cur)
        for s in stages:
            if cur in s["deps"]:
                indeg[s["id"]] -= 1
                if indeg[s["id"]] == 0:
                    ready.append(s["id"])
                    ready.sort(key=lambda i: (by[i]["round"], by[i]["cls"] != "PARALLEL", i))
    return out


def wave_groups(stages: list[dict], order: list[str]) -> list[list[str]]:
    """並行波:同波內互不相依(PARALLEL 同波齊發;SEQUENTIAL 各自一波)。"""
    by = {s["id"]: s for s in stages}
    level: dict[str, int] = {}
    for i in order:
        deps = [d for d in by[i]["deps"] if d in level]
        lv = (max(level[d] for d in deps) + 1) if deps else 0
        if by[i]["cls"] == "SEQUENTIAL":
            lv = max([lv] + [v + 1 for v in level.values()]) if level else lv
        level[i] = lv
    waves: dict[int, list] = {}
    for i, lv in level.items():
        waves.setdefault(lv, []).append(i)
    return [sorted(waves[k]) for k in sorted(waves)]


# ══════════════════════════════════════════════════════════════════════════════
# ⑦ 沙盒模擬(uv pip compile 多輪;同意閘)+ 鏡像健康
# ══════════════════════════════════════════════════════════════════════════════
def mirror_health(baseline: dict, timeout: float = 4.0) -> list[dict]:
    if not _consent():
        return [{"label": l, "url": u, "state": "NOT_RUN", "ms": None, "note": "同意閘關(VIA_NET_CONSENT=YES)"}
                for l, u in zip(baseline["mirror_chain"].get("labels", []), baseline["mirror_chain"]["order"])]
    import urllib.request
    rows = []
    for l, u in zip(baseline["mirror_chain"].get("labels", []), baseline["mirror_chain"]["order"]):
        t0 = time.time()
        try:
            req = urllib.request.Request(u.rstrip("/") + "/pip/", method="HEAD", headers={"User-Agent": "VIA-EnvGov/0100"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ok = 200 <= resp.status < 400
            rows.append({"label": l, "url": u, "state": "OK" if ok else "FAIL", "ms": int((time.time() - t0) * 1000), "note": ""})
        except Exception as exc:
            rows.append({"label": l, "url": u, "state": "FAIL", "ms": None, "note": f"{type(exc).__name__}"[:40]})
    for r in rows:
        log_event("MIRROR", "", r["label"], r["state"], f"{r.get('ms')}ms {r['note']}")
    return rows


def _parse_uv_compile(text: str) -> list[str]:
    return sorted(t.strip().split()[0] for t in text.splitlines() if t.strip() and not t.strip().startswith("#"))


def _uv_round(pins: list[str], py_mm: str, mirror_url: str = "", no_deps: bool = False) -> dict:
    cmd = [_UV, "pip", "compile", "-", "--no-header", "--no-annotate", "--quiet"] + (["--no-deps"] if no_deps else [])
    if py_mm:
        cmd += ["--python-version", py_mm]
    if mirror_url:
        cmd += ["--index-url", mirror_url]
    r = run_cmd(cmd, timeout=300, cwd=ROOT if (ROOT / "uv.toml").exists() and not mirror_url else None, input_text="\n".join(pins) + "\n")
    tail = [l for l in r["err"].splitlines() if l.strip()][-1:]
    return {"rc": r["rc"], "would": _parse_uv_compile(r["out"]), "tail": ("uv:" + tail[0][:100]) if tail else ""}


def _pip_round(pins: list[str], py: str, mirror_url: str = "", no_deps: bool = False) -> dict:
    cmd = [py, "-m", "pip", "install", "--dry-run", "--ignore-installed", "--no-color"] + (["--no-deps"] if no_deps else []) + (["-i", mirror_url] if mirror_url else [])
    r = run_cmd(cmd + pins, timeout=600)
    would = []
    for line in r["out"].splitlines():
        if line.strip().startswith("Would install"):
            would = sorted(line.strip()[len("Would install"):].split())
    tail = [l for l in (r["out"] + r["err"]).splitlines() if l.strip()][-1:]
    return {"rc": r["rc"], "would": would, "tail": (tail[0][:100] if tail else "")}


def judge_rounds(rounds: list[dict]) -> tuple[str, str, str]:
    if not rounds:
        return "NOT_RUN", "NOT_RUN", "零輪(離線/同意閘)"
    if any(r["rc"] != 0 for r in rounds):
        return "FAIL", "RED", "解析失敗:" + (rounds[-1].get("tail") or "?")[:90]
    if len(rounds) >= 2 and rounds[-1]["would"] != rounds[-2]["would"]:
        return "UNSTABLE", "YELLOW", "末兩輪解析飄移(鏡像快取/上游變動)→ 候裁再測"
    if not rounds[-1]["would"]:
        return "NOOP", "GREEN", "已全滿足零變動"
    return "OK", "GREEN", f"{len(rounds)} 輪一致,會裝 {len(rounds[-1]['would'])} 件"


def simulate(plan: dict, scans: list[dict], rounds_n: int, offline: bool, mirror_url: str = "") -> None:
    base = next((s for s in scans if s["env"]["name"] == "BASE"), {})
    base_py = base.get("env", {}).get("py") or sys.executable
    base_mm = ".".join(str(base.get("python", "")).split(".")[:2]) if str(base.get("python", ""))[:1].isdigit() else ""
    for st in plan["stages"]:
        if st["kind"] not in ("INSTALL", "REPAIR_BASE"):
            continue
        pins = [p for p in st.get("pins", []) if p]
        if not pins:
            st["sim"] = {"state": "NOT_RUN", "risk": "NOT_RUN", "note": "無件"}
            continue
        if offline or not _consent():
            st["sim"] = {"state": "NOT_RUN", "risk": "NOT_RUN", "note": "離線/同意閘關 → 未模擬(apply 拒跑本段)"}
            continue
        py_mm = ".".join(str(st.get("python") or "").split(".")[:2]) if st["kind"] == "INSTALL" and st.get("python") else base_mm
        rs = []
        for _ in range(max(2, rounds_n)):
            rd = _uv_round(pins, py_mm, mirror_url, bool(st.get("no_deps"))) if _UV else _pip_round(pins, base_py, mirror_url, bool(st.get("no_deps")))
            rs.append(rd)
            if rd["rc"] != 0:
                break
        state, risk, note = judge_rounds(rs)
        st["sim"] = {"state": state, "risk": risk, "note": note, "rounds": rs, "tool": "uv" if _UV else "pip"}
        log_event("SIMULATE", st["env"], ",".join(pins[:4]), risk, f"{st['id']} {note}")


# ══════════════════════════════════════════════════════════════════════════════
# ⑧ 執行(apply --approve):GREEN 非破壞段;REMOVE_BASE 須 --approve-remove
# ══════════════════════════════════════════════════════════════════════════════
def stage_commands(st: dict, base_py: str) -> tuple[list[list[str]], list[str], list[str]]:
    """段 → (argv 列, ps 令, sh 令)。"""
    argvs, ps, sh = [], [], []
    k = st["kind"]
    ep = st.get("env_path", "")
    pyw = f"{ep}\\Scripts\\python.exe"
    pyu = str(PurePosixPath(ep.replace("\\", "/")) / "bin" / "python")
    pyv = st.get("python") or ""
    uvq = "uv"
    if k == "ENSURE_ENV":
        if not st.get("exists"):
            argvs.append([_UV or "uv", "venv", ep] + (["--python", pyv] if pyv else []))
            ps.append(f'{uvq} venv "{ep}"' + (f" --python {pyv}" if pyv else ""))
            sh.append(f'{uvq} venv "{ep.replace(chr(92), "/")}"' + (f" --python {pyv}" if pyv else ""))
    elif k == "INSTALL":
        q = " ".join(f'"{p}"' if any(c in p for c in "<>=![]") else p for p in st.get("pins", []))
        nd = ["--no-deps"] if st.get("no_deps") else []
        argvs.append([_UV or "uv", "pip", "install", "--python", "{PY}"] + nd + list(st.get("pins", [])))
        ps.append(f'{uvq} pip install --python "{pyw}" {" ".join(nd)} {q}'.replace("  ", " "))
        sh.append(f'{uvq} pip install --python "{pyu}" {" ".join(nd)} {q}'.replace("  ", " "))
    elif k == "VERIFY":
        if st["env"] == "BASE":
            argvs.append([_UV or "uv", "pip", "check", "--python", base_py])
            ps.append(f'{uvq} pip check --python "{base_py}"')
            sh.append(f'{uvq} pip check --python "{base_py}"')
        else:
            argvs.append([_UV or "uv", "pip", "check", "--python", "{PY}"])
            ps.append(f'{uvq} pip check --python "{pyw}"')
            sh.append(f'{uvq} pip check --python "{pyu}"')
    elif k == "REPAIR_BASE":
        user = ["--user"] if (sys.prefix == getattr(sys, "base_prefix", sys.prefix) and os.name == "nt") else []
        pins = list(st.get("pins", []))
        argvs.append([base_py, "-m", "pip", "install", "--upgrade-strategy", "only-if-needed"] + user + pins)
        q = " ".join(f'"{p}"' if any(c in p for c in "<>=![]") else p for p in pins)
        ps.append(f'& "{base_py}" -m pip install --upgrade-strategy only-if-needed {" ".join(user)} {q}'.replace("  ", " "))
        sh.append(f'"{base_py}" -m pip install --upgrade-strategy only-if-needed {q}')
    elif k == "REMOVE_BASE":
        for p in st.get("pins", []):
            argvs.append([base_py, "-m", "pip", "uninstall", "-y", p])
            ps.append(f'& "{base_py}" -m pip uninstall -y {p}   # 候裁(--approve-remove)')
            sh.append(f'"{base_py}" -m pip uninstall -y {p}   # 候裁(--approve-remove)')
    elif k in ("DELEGATE_REBUILD", "DELEGATE_SPLIT", "PRUNE", "RENAME_ENV"):
        ps.append(f"# {st.get('argv_hint', '')}   # 委派/候裁:操作員自跑")
        sh.append(f"# {st.get('argv_hint', '')}   # 委派/候裁:操作員自跑")
    return argvs, ps, sh


def emit_scripts(plan: dict, base_py: str, ts: str) -> tuple[str, str]:
    ps = ['$ErrorActionPreference = "Stop"', f"# VIA 環境治理執行檔 {ts}(MDL135)— 段依拓撲序;候裁段以 # 註記,跑前先閱;鏡像鏈走 uv.toml"]
    sh = ["#!/bin/sh", "set -e", f"# VIA 環境治理執行檔 {ts}(MDL135)— 候裁段以 # 註記"]
    by = {s["id"]: s for s in plan["stages"]}
    for i in plan["order"]:
        st = by[i]
        tag = f"# [{st['id']}·R{st['round']}·{st['cls']}·{st['kind']}] {st['goal']} · 模擬 {st['sim'].get('risk', 'NOT_RUN')}"
        ps.append(tag)
        sh.append(tag)
        _a, p, s = stage_commands(st, base_py)
        if st["destructive"]:
            p = ["# " + x if not x.startswith("#") else x for x in p]
            s = ["# " + x if not x.startswith("#") else x for x in s]
        ps += p
        sh += s
    return "\n".join(ps) + "\n", "\n".join(sh) + "\n"


def verify_env(name: str, py: str, baseline: dict, skips: dict, timeout: int = 120) -> dict:
    """VERIFY:探針+快篩+分類;衝突全屬 METADATA_SHADOWED(cv2 錨遮蔽殘餘)=OK*(接受),否則 FAIL。"""
    env = {"name": name, "py": py}
    pr = probe_env(env, timeout=timeout)
    if not pr.get("ok"):
        return {"ok": False, "note": pr.get("err", "探針失敗"), "conflicts": []}
    chk = fast_check(env, timeout=timeout)
    scan = {"env": env, "ok": True, "python": pr.get("python"), "dists": pr.get("dists", {}), "dup": {}, "conflicts": chk.get("conflicts", []), "check_tool": chk.get("tool")}
    cc = classify_conflicts([scan], baseline, {"extras": []}, skips) if name != "BASE" else [dict(c, action="REPAIR_BASE" if c["kind"] != "BROKEN" else "REBUILD") for c in chk.get("conflicts", [])]
    hard = [c for c in cc if c.get("action") != "METADATA_SHADOWED"]
    accepted = len(cc) - len(hard)
    if chk.get("tool") == "NOT_RUN":
        return {"ok": False, "note": "快篩 NOT_RUN(uv/pip 皆缺)→ 不假綠", "conflicts": cc}
    return {"ok": not hard, "note": f"{chk.get('tool')} check 衝突 {len(hard)}(接受殘餘 {accepted})", "conflicts": cc}


def apply_plan(plan: dict, scans: list[dict], approve: bool, approve_remove: bool, baseline: dict | None = None, skips: dict | None = None,
               only: set | None = None, only_kinds: set | None = None) -> dict:
    baseline = baseline or load_baseline()
    skips = skips if skips is not None else lessons_skip()
    base = next((s for s in scans if s["env"]["name"] == "BASE"), {})
    base_py = base.get("env", {}).get("py") or sys.executable
    by = {s["id"]: s for s in plan["stages"]}
    summary = {"ran": 0, "ok": 0, "fail": 0, "skipped": 0, "blocked": 0}
    if not approve:
        for st in plan["stages"]:
            st["result"] = {"state": "SKIP", "note": "未授權(plan 唯讀;apply --approve 才跑)"}
        return summary
    ok_u, why_u = unitest_gate()                 # 批506 L19:環境統一測式未綠=不核可安裝(零動作)
    if not ok_u:
        for st in plan["stages"]:
            st["result"] = {"state": "SKIP", "note": f"L19 安裝核可律:{why_u}"}
        plan["state"] = "BLOCKED_UNITEST"
        summary["blocked"] = len(plan["stages"])
        summary["note"] = f"L19:{why_u}"
        return summary
    verified: set = set()
    for i in plan["order"]:
        st = by[i]
        k = st["kind"]
        deps_ok = all(by[d]["result"].get("state") in ("OK", "SKIP_EXISTS") for d in st["deps"] if d in by)
        if k in ("LOCK", "PROMOTE_LKGC", "PRUNE", "DELEGATE_REBUILD", "DELEGATE_SPLIT", "RENAME_ENV"):
            st["result"] = {"state": "SKIP", "note": "R3/委派段由 run 收尾或操作員自跑(rename 走 via-envgov rename)"}
            summary["skipped"] += 1
            continue
        if only and st["id"] not in only:
            st["result"] = {"state": "SKIP", "note": "--only 未選"}
            summary["skipped"] += 1
            continue
        if only_kinds and k not in only_kinds:   # 批383:--only-kind REPAIR_BASE(base 補 manifest 缺件;VERIFY 段同列才驗)
            st["result"] = {"state": "SKIP", "note": "--only-kind 未選"}
            summary["skipped"] += 1
            continue
        if not deps_ok:
            st["result"] = {"state": "BLOCKED", "note": "前置段未綠"}
            summary["blocked"] += 1
            log_event("APPLY_STAGE", st["env"], "", "BLOCKED", f"{st['id']} {k} 前置未綠")
            continue
        if k in ("INSTALL", "REPAIR_BASE") and st["sim"].get("risk") != "GREEN":
            st["result"] = {"state": "SKIP", "note": f"模擬非 GREEN({st['sim'].get('risk')})→ 拒跑(授權閉環:先模擬後執行)"}
            summary["skipped"] += 1
            log_event("APPLY_STAGE", st["env"], "", "SKIP", f"{st['id']} {k} 模擬 {st['sim'].get('risk')}")
            continue
        if k == "REMOVE_BASE":
            if not approve_remove:
                st["result"] = {"state": "SKIP", "note": "破壞段須 --approve-remove(逐件印令,不自動)"}
                summary["skipped"] += 1
                log_event("APPLY_STAGE", "BASE", ",".join(st["pins"][:4]), "SKIP", f"{st['id']} 未授權移除")
                continue
            if not all(d in verified for d in st["deps"]):
                st["result"] = {"state": "BLOCKED", "note": "目標境 VERIFY 未於本跑綠燈"}
                summary["blocked"] += 1
                continue
        if k == "ENSURE_ENV" and st.get("exists"):
            st["result"] = {"state": "SKIP_EXISTS", "note": "已在(只增不減)"}
            continue
        if k == "VERIFY":
            vpy = base_py if st["env"] == "BASE" else str(env_python(Path(st.get("env_path", ""))) or "")
            vr = verify_env(st["env"], vpy, baseline, skips) if vpy else {"ok": False, "note": "目標境 python 缺"}
            st["result"] = {"state": "OK" if vr["ok"] else "FAIL", "note": vr["note"]}
            summary["ran"] += 1
            summary["ok" if vr["ok"] else "fail"] += 1
            if vr["ok"]:
                verified.add(st["id"])
            log_event("APPLY_STAGE", st["env"], "", "OK" if vr["ok"] else "FAIL", f"{st['id']} VERIFY {vr['note']}")
            print(f"  [{'OK ' if vr['ok'] else 'FAIL'}] {st['id']} VERIFY {st['env']} · {vr['note']}")
            continue
        argvs, ps, _sh = stage_commands(st, base_py)
        if not argvs:
            st["result"] = {"state": "OK", "note": "無需執行"}
            continue
        py = env_python(Path(st.get("env_path", ""))) if st.get("env_path") else None
        results = []
        ok = True
        for a in argvs:
            a = [str(py) if x == "{PY}" else x for x in a]
            if "{PY}" in a or (st["env"] != "BASE" and k in ("INSTALL", "VERIFY") and not py):
                results.append({"rc": -1, "err": "目標境 python 缺(ENSURE_ENV 未成?)"})
                ok = False
                break
            print(f"     $ {' '.join(a)[:160]}")
            r = run_cmd(a, timeout=1800, cwd=ROOT if (ROOT / "uv.toml").exists() else None)
            results.append({"rc": r["rc"], "s": r["s"], "tail": ((r["out"] + r["err"]).strip().splitlines() or [""])[-1][:160]})
            if r["rc"] != 0:
                ok = False
                break
        st["result"] = {"state": "OK" if ok else "FAIL", "cmds": results}
        summary["ran"] += 1
        summary["ok" if ok else "fail"] += 1
        if ok and k == "VERIFY":
            verified.add(st["id"])
        log_event("APPLY_STAGE", st["env"], ",".join(st.get("pins", [])[:4]), "OK" if ok else "FAIL",
                  f"{st['id']} {k} {results[-1].get('tail', '') if results else ''}")
        print(f"  [{'OK ' if ok else 'FAIL'}] {st['id']} {k} {st['env']} · {results[-1].get('tail', '') if results else ''}"[:170])
    return summary


# ══════════════════════════════════════════════════════════════════════════════
# ⑨ LKGC:快照/晉升/狀態;rollback
# ══════════════════════════════════════════════════════════════════════════════
def write_locks(scans: list[dict], lock_dir: Path) -> dict:
    lock_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for s in scans:
        if not s.get("ok"):
            continue
        lines = sorted(f"{n}=={i['ver']}" for n, i in s["dists"].items())
        p = lock_dir / f"{s['env']['name']}.lock.txt"
        p.write_text(f"# VIA env lock · {s['env']['name']} · python {s.get('python')} · {now_iso()}\n" + "\n".join(lines) + "\n", encoding="utf-8")
        out[s["env"]["name"]] = str(p)
    return out


def lkgc_snapshot(scans: list[dict], base_analysis: dict, conflicts: list[dict], ts: str) -> dict:
    locks = write_locks(scans, LOCK_DIR)
    n_conf = {s["env"]["name"]: len(s.get("conflicts", [])) for s in scans}
    accepted = sum(1 for c in conflicts if c.get("action") == "METADATA_SHADOWED")
    hard = sum(1 for c in conflicts if c.get("action") != "METADATA_SHADOWED")
    reasons = []
    if hard:
        reasons.append(f"衝突 {hard} 條(接受殘餘 {accepted} 不計)")
    if base_analysis.get("blocked_present"):
        reasons.append(f"base 封鎖家族件 {len(base_analysis['blocked_present'])}:{','.join(base_analysis['blocked_present'][:5])}")
    if base_analysis.get("manifest_missing"):
        reasons.append(f"base manifest 缺 {len(base_analysis['manifest_missing'])}:{','.join(base_analysis['manifest_missing'][:5])}")
    if any(not s.get("ok") for s in scans):
        reasons.append("有境探針失敗")
    eligible = not reasons
    verdict = "GREEN" if eligible else ("RED" if hard or base_analysis.get("blocked_present") else "YELLOW")
    snap = {"schema": "VIA.EnvGovernance.LKGC.v1", "ts": ts, "machine": machine_hash(), "run_id": _RUN_ID,
            "verdict": verdict, "eligible": eligible, "reasons": reasons,
            "envs": {s["env"]["name"]: {"path": s["env"].get("path"), "py": s["env"].get("py"), "python": s.get("python"),
                                        "n_dists": len(s.get("dists", {})), "conflicts": n_conf[s["env"]["name"]],
                                        "lock": locks.get(s["env"]["name"], ""), "ok": s.get("ok")} for s in scans},
            "base": {"manifest_missing": base_analysis.get("manifest_missing", []), "blocked_present": base_analysis.get("blocked_present", []),
                     "extras_n": len(base_analysis.get("extras", []))}}
    OUT.mkdir(parents=True, exist_ok=True)
    _write_json(OUT / f"LKGC_{ts}.json", snap)
    log_event("LKGC_SNAPSHOT", "*", "", verdict, "; ".join(reasons) or "eligible")
    return snap


def lkgc_promote(snap: dict) -> dict:
    prev = _read_json(LKGC_LATEST, None)
    if snap.get("eligible"):
        LKGC_LOCK_DIR.mkdir(parents=True, exist_ok=True)
        for name, e in snap["envs"].items():
            if e.get("lock") and Path(e["lock"]).exists():
                shutil.copy2(e["lock"], LKGC_LOCK_DIR / Path(e["lock"]).name)
                e["lock_lkgc"] = str(LKGC_LOCK_DIR / Path(e["lock"]).name)
        snap["promoted_at"] = now_iso()
        snap["previous"] = (prev or {}).get("ts")
        _write_json(LKGC_LATEST, snap)
        log_event("LKGC_PROMOTE", "*", "", "GREEN", f"LKGC_latest ← {snap['ts']}(前 {snap.get('previous')})")
        return {"promoted": True, "ts": snap["ts"], "previous": snap.get("previous")}
    _write_json(OUT / "LKGC_candidate.json", snap)
    log_event("LKGC_NOT_PROMOTED", "*", "", snap.get("verdict", "?"), "; ".join(snap.get("reasons", [])))
    return {"promoted": False, "reasons": snap.get("reasons", []), "latest": (prev or {}).get("ts"), "candidate": str(OUT / "LKGC_candidate.json")}


def lkgc_status() -> dict:
    latest = _read_json(LKGC_LATEST, None)
    hist = sorted(OUT.glob("LKGC_*.json")) if OUT.exists() else []
    hist = [h for h in hist if h.name not in ("LKGC_latest.json", "LKGC_candidate.json")]
    return {"latest": latest, "history_n": len(hist), "history": [h.name for h in hist[-8:]],
            "candidate": _read_json(OUT / "LKGC_candidate.json", None)}


def rollback_plan(baseline: dict, to_file: str | None, force_baseline: bool, scans: list[dict] | None, env_root: str) -> dict:
    """還原計畫:①LKGC(lock 逐境 uv pip sync)②原本規劃(Baseline manifest+layout)。"""
    src, mode = None, ""
    if not force_baseline:
        p = Path(to_file) if to_file else LKGC_LATEST
        src = _read_json(p, None) if p.exists() else None
        if isinstance(src, dict) and src.get("schema") == "VIA.EnvGovernance.LKGC.v1":
            mode = f"LKGC({p.name} · {src.get('ts')})"
    ps = ['$ErrorActionPreference = "Continue"', f"# VIA 還原執行檔(MDL135;{_RUN_ID})"]
    sh = ["#!/bin/sh", f"# VIA 還原執行檔(MDL135;{_RUN_ID})"]
    items = []
    if src:
        for name, e in src["envs"].items():
            lock = e.get("lock_lkgc") or e.get("lock") or ""
            if not lock or not Path(lock).exists():
                items.append({"env": name, "state": "SKIP", "note": "lock 檔缺(誠實)"})
                continue
            if name == "BASE":
                py = e.get("py") or sys.executable
                ps.append(f"# BASE 還原:先補齊(非破壞);sync(移除 lock 外件)屬破壞=候裁 --approve-remove")
                ps.append(f'uv pip install --python "{py}" -r "{lock}"')
                ps.append(f'# uv pip sync --python "{py}" "{lock}"   # 候裁')
                sh.append(f'uv pip install --python "{py}" -r "{lock}"')
                sh.append(f'# uv pip sync --python "{py}" "{lock}"   # 候裁')
                items.append({"env": name, "state": "PLAN", "lock": lock, "destructive": True})
            else:
                ep = e.get("path") or str(Path(env_root) / name)
                pyv = ".".join(str(e.get("python", "")).split(".")[:2]) if str(e.get("python", ""))[:1].isdigit() else ""
                pyw, pyu = f"{ep}\\Scripts\\python.exe", str(PurePosixPath(ep.replace("\\", "/")) / "bin" / "python")
                ps.append(f'if (-not (Test-Path "{ep}")) {{ uv venv "{ep}"' + (f" --python {pyv}" if pyv else "") + " }")
                ps.append(f'uv pip sync --python "{pyw}" "{lock}"')
                ps.append(f'uv pip check --python "{pyw}"')
                sh.append(f'[ -d "{ep}" ] || uv venv "{ep}"' + (f" --python {pyv}" if pyv else ""))
                sh.append(f'uv pip sync --python "{pyu}" "{lock}"')
                sh.append(f'uv pip check --python "{pyu}"')
                items.append({"env": name, "state": "PLAN", "lock": lock, "destructive": True, "path": ep})
    else:
        mode = "原本規劃(Baseline;無 LKGC 或 --baseline)"
        ms = manifest_sets(baseline)
        need = sorted((ms["toolchain"] | ms["engine_core"] | ms["low_risk_allow"]) - BOOT)
        base_py = next((s["env"]["py"] for s in (scans or []) if s["env"]["name"] == "BASE"), sys.executable)
        ps.append("# ① base 該有冊補齊(只增;非破壞)")
        ps.append(f'& "{base_py}" -m pip install --upgrade-strategy only-if-needed ' + " ".join(need))
        sh.append(f'"{base_py}" -m pip install --upgrade-strategy only-if-needed ' + " ".join(need))
        items.append({"env": "BASE", "state": "PLAN", "n": len(need), "destructive": False})
        seen_fams = set()
        for s in (scans or []):
            if s["env"]["name"] != "BASE" or not s.get("ok"):
                continue
            for p in s["dists"]:
                fam = family_index(baseline).get(p)
                if fam:
                    seen_fams.add(fam)
        layout = baseline.get("env_layout", {})
        envs_needed = {k: v for k, v in layout.items() if isinstance(v, dict) and (v.get("python") or v.get("family"))}
        for fam in sorted(seen_fams):
            spec = baseline["families"][fam]
            envs_needed.setdefault(spec["target_env"], {"family": fam, "python": spec.get("python", "3.12")})
        present = {s["env"]["name"].lower() for s in (scans or [])} | {s["env"]["name"].lower() for s in (scans or [])}
        for name, spec in sorted(envs_needed.items()):
            if name in ("base",) or spec.get("protected"):
                continue
            aliases = {name.lower()} | {a.lower() for a in spec.get("aliases", [])}
            if aliases & present:  # 既有健康境不動(只增):別名境已在=不重建
                items.append({"env": name, "state": "SKIP", "note": "已在(別名境:" + ", ".join(sorted(aliases & present)) + ")", "destructive": False})
                continue
            ep = str(Path(env_root) / name)
            pyv = spec.get("python", "3.12")
            fam = spec.get("family")
            mem = [m for m in (baseline["families"].get(fam, {}).get("members", []) if fam else [])
                   if lessons_skip().get(canon(m)) != "everywhere" and canon(m) not in {canon(x) for x in baseline.get("cv2_family", [])}]
            if fam and any(canon(x) in {canon(m) for m in baseline["families"][fam]["members"]} for x in baseline.get("cv2_family", [])):
                mem.append(baseline.get("cv2_anchor", "opencv-contrib-python"))
            ps.append(f"# ② 境 {name}(家族 {fam or '—'};Python {pyv})")
            ps.append(f'if (-not (Test-Path "{ep}")) {{ uv venv "{ep}" --python {pyv} }}')
            if mem and fam in seen_fams:
                ps.append(f'uv pip install --python "{ep}\\Scripts\\python.exe" ' + " ".join(mem[:12]))
            sh.append(f'[ -d "{ep}" ] || uv venv "{ep}" --python {pyv}')
            if mem and fam in seen_fams:
                sh.append(f'uv pip install --python "{ep}/bin/python" ' + " ".join(mem[:12]))
            items.append({"env": name, "state": "PLAN", "family": fam or "", "python": pyv, "destructive": False, "path": ep})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"ROLLBACK_{_RUN_ID}.ps1").write_text("\n".join(ps) + "\n", encoding="utf-8-sig")
    (OUT / f"ROLLBACK_{_RUN_ID}.sh").write_text("\n".join(sh) + "\n", encoding="utf-8")
    log_event("ROLLBACK_PLAN", "*", "", "PLAN", f"{mode};境 {len(items)}")
    return {"mode": mode, "items": items, "ps": str(OUT / f"ROLLBACK_{_RUN_ID}.ps1"), "sh": str(OUT / f"ROLLBACK_{_RUN_ID}.sh"), "lines_sh": sh}


def rollback_execute(rb: dict, approve: bool, approve_remove: bool) -> dict:
    if not approve:
        return {"executed": 0, "note": "未授權(--execute --approve)"}
    ran = ok = 0
    for line in rb.get("lines_sh", []):
        t = line.strip()
        if not t or t.startswith("#") or t.startswith("set ") or t.startswith("[ -d"):
            continue
        destructive = " sync " in t
        if destructive and not approve_remove:
            print(f"  [SKIP] 破壞段候裁:{t[:120]}")
            continue
        import shlex
        argv = shlex.split(t.split("#")[0])
        if argv and argv[0] == "uv" and _UV:
            argv[0] = _UV
        print(f"     $ {' '.join(argv)[:160]}")
        r = run_cmd(argv, timeout=1800, cwd=ROOT if (ROOT / "uv.toml").exists() else None)
        ran += 1
        ok += 1 if r["rc"] == 0 else 0
        log_event("ROLLBACK_EXEC", "", "", "OK" if r["rc"] == 0 else "FAIL", t[:160])
    return {"executed": ran, "ok": ok}



# ═════════════════════════════════════════════════════════
# ⑨c 環境復原(批508 律 L24):①還原前次 ②順序裝全部工具 ③中高風險單獨隔離;via-envgov recover / via-envrecover
# ═════════════════════════════════════════════════════════
def recover_plan(args: list) -> dict:
    baseline, rb, env_root = rollback_inputs(args)
    roster = load_roster(_arg_after(args, "--roster"))
    if "--sheet-only" not in args:
        roster = union_roster(baseline, roster)
    roots = [r for r in (_arg_after(args, "--roots") or "").split(os.pathsep) if r]
    envs = discover_envs(baseline, roots, _arg_after(args, "--env-root"), None, None)
    plan = tools_plan(roster, envs, env_root, only_env=_arg_after(args, "--tool-env"))
    rec = {"schema": "VIA.EnvGovernance.RECOVER.v1", "law": "L24", "batch": BATCH, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "run_id": _RUN_ID, "env_root": env_root, "roster": roster.get("_src"), "order": ORDER_LAW,
           "restore": {"mode": rb["mode"], "items": rb["items"], "ps": rb["ps"], "sh": rb["sh"],
                       "destructive_n": sum(1 for i in rb["items"] if i.get("destructive"))},
           "install": {"stages": [{k: st.get(k) for k in ("id", "kind", "env", "tier", "goal")} for st in plan["stages"]],
                       "counts": plan["counts"], "risk": plan["risk_counts"], "external": plan["external"],
                       "unrouted": len(plan.get("unrouted") or []), "whitelist_hold": len(plan.get("whitelist_hold") or [])},
           "isolation": plan.get("isolation", {}), "broken_interp": plan.get("broken_interp", []),
           "borrow_blocked": [e["name"] for e in plan["envs"] if e.get("isolation") == "EXCLUSIVE" and e["state"] == "ENV_ABSENT"],
           "state": "PLAN", "_rb": rb, "_plan": plan}
    return rec


def recover_ps(rec: dict) -> str:
    rb, plan = rec["_rb"], rec["_plan"]
    lines = [f"# VIA 環境復原(律 L24;批508;{rec['run_id']})· 境根 {rec['env_root']} · 冊 {rec.get('roster')}",
             "# 律:①還原前次(LKGC lock;無則 Baseline 原本規劃)②順序裝全部工具 " + " → ".join(x.split("(")[0] for x in ORDER_LAW) + " ③_M/_H 一律同名獨立境,不借 alt 境",
             "# plan 唯讀。要跑:$env:VIA_NET_CONSENT='YES'; via-envrecover -Execute -Approve [-ApproveRemove 才做 sync 破壞段]",
             "#   ① 不受 L19 擋(LKGC 本身即曾 GREEN;同意閘仍要)· ② 新裝段過 L19(via-rungate GREEN 24h 內)否則 RESTORED_BLOCKED_UNITEST 誠實停",
             "", f"# ═ ① 還原前次 · {rb['mode']} ═"]
    try:
        raw = Path(rb["ps"]).read_text(encoding="utf-8-sig").splitlines()
        lines += [l for l in raw if not l.startswith(("$ErrorActionPreference", "# VIA 還原執行檔"))]
    except Exception as exc:
        lines.append(f"# (還原執行檔缺:{type(exc).__name__})")
    lines += ["", "# ═ ② 順序裝全部工具 ═"] + [l for l in tools_ps(plan).splitlines() if not l.startswith("# VIA 工具導入計畫") and not l.startswith("# plan 唯讀")]
    lines += ["", "# ═ ③ 隔離 ═",
              "# 單獨隔離境(_M/_H;不借 alt):" + (", ".join(rec["isolation"].get("exclusive", [])) or "—"),
              "# 共用境(core 白名單/LOW 家族):" + (", ".join(rec["isolation"].get("shared", [])) or "—"),
              "# 借境封鎖(隔離境不在→只建同名境,不把件裝進 alt 境):" + (", ".join(rec["borrow_blocked"]) or "—"),
              "# 解譯器壞境(標準庫錯配;先重建再談裝;見 ② 段 REBUILD_ENV 候裁行):" + (", ".join(rec.get("broken_interp") or []) or "—")]
    return "\n".join(lines) + "\n"


def recover_execute(rec: dict, approve: bool, approve_remove: bool) -> dict:
    out = {"restore": None, "install": None, "state": "PLAN", "note": ""}
    if not approve:
        out["note"] = "未授權(plan 唯讀;recover --execute --approve 才跑)"
        return out
    if not _consent():
        out["state"], out["note"] = "BLOCKED_CONSENT", "同意閘未開(VIA_NET_CONSENT 不代設;$env:VIA_NET_CONSENT='YES' 後再跑)→ ①② 零動作"
        return out
    out["restore"] = rollback_execute(rec["_rb"], True, approve_remove)   # ① 回到前次:不受 L19(LKGC 曾 GREEN);sync 破壞段仍 --approve-remove 候裁
    ok_u, why_u = unitest_gate()
    if not ok_u:
        out["install"] = {"ran": 0, "fails": 0, "note": f"L19:{why_u} → ② 順序安裝 BLOCKED_UNITEST(先 via-rungate,GREEN 後再跑一次 recover --execute --approve;① 已做段 no-op)"}
        rec["_plan"]["state"] = "BLOCKED_UNITEST"
        out["state"] = "RESTORED_BLOCKED_UNITEST"
        return out
    out["install"] = tools_apply(rec["_plan"], True, ensure_env=True)      # ② 順序裝(含隔離境 uv venv 只增)
    out["state"] = rec["_plan"]["state"]
    return out


def do_recover(rest: list) -> int:
    rec = recover_plan(rest)
    plan, rb = rec["_plan"], rec["_rb"]
    print(f"=== 環境復原 MDL135 v{VERSION}(批{BATCH};律 L24)· {'execute' if '--execute' in rest else 'plan(唯讀)'} · 境根 {rec['env_root']} · 冊 {rec.get('roster')} ===")
    print(f"  [① 還原] {rb['mode']} · 境 {len(rb['items'])} · 破壞段候裁 {rec['restore']['destructive_n']}(--approve-remove 才做;其餘只增)")
    for it in rb["items"][:14]:
        print(f"      [{it['state']:4s}] {it['env']:24s} {str(it.get('lock') or it.get('family') or it.get('note') or '')[:70]}")
    print(f"  [② 順序裝] 段 {len(plan['stages'])} · 件態 {plan['counts']} · 風險 {plan['risk_counts']} · 次序 {' → '.join(x.split('(')[0] for x in ORDER_LAW)}")
    for st in plan["stages"]:
        print(f"      [{st['id']}] {st.get('tier', '?'):7s} {st['kind']:13s} {st['env']:24s} {st.get('goal', '')[:80]}")
    print(f"  [③ 隔離] 單獨境 {rec['isolation'].get('exclusive') or '—'} · 借境封鎖 {rec['borrow_blocked'] or '—'} · 解譯器壞境 {rec.get('broken_interp') or '—'}")
    for x in plan["external"][:8]:
        print(f"  [外部] {x['env']} · {x['tool']} · {x['state']} · {x['why'][:60]}")
    if "--execute" in rest:
        r = recover_execute(rec, "--approve" in rest, "--approve-remove" in rest)
        rec["state"], rec["exec"] = r["state"], r
        print(f"  [執行] ① {r.get('restore')} · ② {r.get('install')} · 態 {r['state']}" + (f" · {r['note']}" if r.get("note") else ""))
    slim = {k: v for k, v in rec.items() if not k.startswith("_")}
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        _write_json(OUT / "RECOVER_latest.json", slim)
        _write_json(OUT / f"RECOVER_{_RUN_ID}.json", slim)
        (OUT / "RECOVER_latest.ps1").write_text(recover_ps(rec), encoding="utf-8-sig")
        print(f"  [檔] {OUT / 'RECOVER_latest.json'} + .ps1(一貼即用;plan 唯讀)")
    except Exception as exc:
        print(f"  [檔] 存證失敗 {type(exc).__name__}:{str(exc)[:60]}")
    log_event("RECOVER", "*", "", rec["state"], f"{rb['mode']};段 {len(plan['stages'])};隔離 {len(rec['isolation'].get('exclusive', []))}")
    st = rec["state"]
    return 0 if st in ("PLAN", "APPLIED") else (2 if st.startswith(("BLOCKED", "RESTORED_BLOCKED")) else 1)


# ══════════════════════════════════════════════════════════════════════════════
# ⑨b 命名律換名重建(批382):via-envgov rename [--from X [--to Y]] [--execute --approve [--approve-remove]]
# ══════════════════════════════════════════════════════════════════════════════
def rename_plan(envs: list[dict], baseline: dict, env_root: str, only_from: str | None = None, to_name: str | None = None) -> list[dict]:
    """非 via_ 境 → 換名重建計畫(純函式可自測):新境=via_<舊名>(冊 renames 優先;--to 覆寫);Python=舊境實際版本;lock=舊境現況。"""
    law = baseline.get("naming_law") or {}
    prefix = str(law.get("prefix", "via_"))
    renames = {k.lower(): v for k, v in (law.get("renames") or {}).items()}
    items = []
    for e in envs:
        n = e["name"]
        if n == "BASE" or n.lower().startswith(prefix.lower()) or n.startswith("_retire_"):
            continue
        if only_from and n.lower() != only_from.lower():
            continue
        new = to_name if (only_from and to_name) else renames.get(n.lower(), prefix + n)
        items.append({"old": n, "new": new, "old_path": e.get("path", ""), "new_path": str(Path(env_root) / new), "py": e.get("py"),
                      "python": e.get("python", ""), "lock": "", "state": "PLAN"})
    return items


def rename_commands(it: dict) -> tuple[list[str], list[str]]:
    mm = ".".join(str(it.get("python") or "").split(".")[:2]) if str(it.get("python") or "")[:1].isdigit() else ""
    np_, op = it["new_path"], it["old_path"]
    pyw, pyu = f"{np_}\\Scripts\\python.exe", str(PurePosixPath(np_.replace("\\", "/")) / "bin" / "python")
    retire = str(Path(op).parent / f"_retire_{it['old']}") if op else ""
    lock = it.get("lock") or "<lock>"
    ps = [f"# 命名律 {it['old']} → {it['new']}(Python {mm or '同 base'};lock {lock})",
          f'uv venv "{np_}"' + (f" --python {mm}" if mm else ""),
          f'uv pip sync --python "{pyw}" "{lock}"',
          f'uv pip check --python "{pyw}"',
          f'# Rename-Item -LiteralPath "{op}" "_retire_{it["old"]}"   # 候裁(--approve-remove;驗綠後;掃描自然除名)',
          f"# 別名冊 A 法:VIA_Env_Alias_Map {it['old']} → {it['new']}(路由/工具改指新境;零檔案移動可即回退)"]
    sh = [f"# 命名律 {it['old']} → {it['new']}",
          f'uv venv "{np_.replace(chr(92), "/")}"' + (f" --python {mm}" if mm else ""),
          f'uv pip sync --python "{pyu}" "{lock.replace(chr(92), "/")}"',
          f'uv pip check --python "{pyu}"',
          f'# mv "{op.replace(chr(92), "/")}" "{retire.replace(chr(92), "/")}"   # 候裁(--approve-remove)']
    return ps, sh


def do_rename(args: list[str]) -> int:
    baseline = load_baseline()
    skips = lessons_skip()
    roots = [r for r in (_arg_after(args, "--roots") or "").split(os.pathsep) if r]
    env_root = _arg_after(args, "--env-root")
    envs = discover_envs(baseline, roots, env_root, _arg_after(args, "--base-python"))
    er = env_root or next((str(r) for r in discover_roots(roots, None) if r.is_dir()), str(Path.home() / "envs"))
    items = rename_plan(envs, baseline, er, _arg_after(args, "--from"), _arg_after(args, "--to"))
    execute, approve, approve_remove = "--execute" in args, "--approve" in args, "--approve-remove" in args
    ts = _RUN_ID
    print(f"=== 命名律換名重建(批382)· MDL135 v{VERSION} · {ts} · 非 via_ 境 {len(items)} · {'執行' if execute and approve else '唯讀出令'} ===")
    if not items:
        print("  [OK ] 受管境全數 via_ 前綴(命名律 H7 綠)")
        log_event("RENAME", "*", "", "GREEN", "無非 via_ 境")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    ps_all = ['$ErrorActionPreference = "Stop"', f"# VIA 命名律換名重建 {ts}(MDL135)— 候裁段以 # 註記"]
    sh_all = ["#!/bin/sh", "set -e", f"# VIA 命名律換名重建 {ts}"]
    for it in items:
        env = {"name": it["old"], "py": it["py"], "path": it["old_path"]}
        pr = probe_env(env, timeout=120) if it["py"] else {"ok": False, "err": "python 缺"}
        if pr.get("ok"):
            it["python"] = pr.get("python", it.get("python", ""))
            lock = LOCK_DIR / f"{it['old']}.lock.txt"
            lock.write_text(f"# VIA env lock · {it['old']} · python {it['python']} · {now_iso()}\n" + "\n".join(sorted(f"{n}=={i['ver']}" for n, i in pr.get("dists", {}).items())) + "\n", encoding="utf-8")
            it["lock"] = str(lock)
            it["n_dists"] = len(pr.get("dists", {}))
        else:
            it["state"] = "SKIP"
            it["note"] = f"舊境探針失敗:{pr.get('err')}"
        ps, sh = rename_commands(it)
        ps_all += ps
        sh_all += sh
        print(f"  [{it['state']:4s}] {it['old']} → {it['new']} · py{it.get('python') or '?'} · 件 {it.get('n_dists', '?')} · lock {Path(it['lock']).name if it.get('lock') else '—'}{(' · ' + it['note']) if it.get('note') else ''}")
        if not (execute and approve) or it["state"] == "SKIP":
            continue
        newp = Path(it["new_path"])
        mm = ".".join(str(it["python"]).split(".")[:2]) if str(it["python"])[:1].isdigit() else ""
        ok = True
        if not env_python(newp):
            a = [_UV or "uv", "venv", str(newp)] + (["--python", mm] if mm else [])
            print(f"     $ {' '.join(a)[:160]}")
            r = run_cmd(a, timeout=900, cwd=ROOT if (ROOT / "uv.toml").exists() else None)
            if r["rc"] != 0:
                ok = False
                tail = (r["err"] or r["out"]).strip().splitlines()
                it["state"], it["note"] = "FAIL", "venv:" + (tail[-1][:120] if tail else "rc" + str(r["rc"]))
        npy = env_python(newp) if ok else None
        if ok and not npy:
            ok, it["state"], it["note"] = False, "FAIL", "新境 python 缺"
        if ok:
            a = [_UV or "uv", "pip", "sync", "--python", str(npy), it["lock"]]
            print(f"     $ {' '.join(a)[:160]}")
            r = run_cmd(a, timeout=1800, cwd=ROOT if (ROOT / "uv.toml").exists() else None)
            if r["rc"] != 0:
                tail = (r["err"] or r["out"]).strip().splitlines()
                ok, it["state"], it["note"] = False, "FAIL", "sync:" + (tail[-1][:120] if tail else "?")
        if ok:
            vr = verify_env(it["new"], str(npy), baseline, skips)
            it["verify"] = vr["note"]
            if not vr["ok"]:
                ok, it["state"], it["note"] = False, "FAIL", "verify:" + vr["note"]
        if ok:
            it["state"] = "OK"
            if approve_remove and it["old_path"] and Path(it["old_path"]).is_dir():
                retire = Path(it["old_path"]).parent / f"_retire_{it['old']}"
                try:
                    os.rename(it["old_path"], retire)
                    it["retired"] = str(retire)
                except Exception as exc:
                    it["note"] = f"退役改名失敗(舊境保留):{type(exc).__name__}"
            else:
                it["note"] = "新境驗綠;舊境保留(--approve-remove 才退役)"
        log_event("RENAME_EXEC", it["old"], "", it["state"], f"→ {it['new']} {it.get('note', '')} {it.get('verify', '')}")
        print(f"  [{it['state']:4s}] {it['old']} → {it['new']} · {it.get('verify', '')} · {it.get('note', '')}{(' · 退役 ' + it['retired']) if it.get('retired') else ''}")
    (OUT / f"RENAME_EXEC_{ts}.ps1").write_text("\n".join(ps_all) + "\n", encoding="utf-8-sig")
    (OUT / f"RENAME_EXEC_{ts}.sh").write_text("\n".join(sh_all) + "\n", encoding="utf-8")
    _write_json(OUT / f"RENAME_{ts}.json", {"schema": "VIA.EnvGovernance.Rename.v1", "ts": ts, "machine": machine_hash(), "items": items, "executed": bool(execute and approve)})
    print(f"  [檔] RENAME_EXEC_{ts}.ps1/.sh · RENAME_{ts}.json(VIA_Reports/env_governance)")
    if not (execute and approve):
        print("  [次步] via-envgov rename --execute --approve(建境+lock 同步+驗證;舊境不動)→ 再加 --approve-remove 退役舊境(改名 _retire_);工具改指新境:別名冊 A 法")
    log_event("RENAME", "*", "", "PLAN" if not (execute and approve) else "EXEC", f"{len(items)} 境:" + ", ".join(f"{i['old']}→{i['new']}:{i['state']}" for i in items))
    return 0 if all(i["state"] in ("OK", "PLAN") for i in items) else 1


# ══════════════════════════════════════════════════════════════════════════════
# ⑩ HTML UI Matrix(四分區;小字體;自動換行;RYG;進度條;零 CDN)
# ══════════════════════════════════════════════════════════════════════════════
def _esc(x) -> str:
    return _html.escape(str(x if x is not None else ""))


def _ndists(s: dict) -> int:
    return int(s.get("n_dists", len(s.get("dists", {}) or {})))


def _lamp(v: str) -> str:
    cls = {"GREEN": "g", "OK": "g", "YELLOW": "y", "WARN": "y", "RED": "r", "FAIL": "r", "REBUILD": "r", "BROKEN": "r"}.get(str(v), "n")
    return f'<span class="lamp {cls}"></span>{_esc(v)}'


def render_matrix(run: dict) -> str:
    scans = run.get("panorama", [])
    ba = run.get("base_analysis", {})
    plan = run.get("plan", {"stages": []})
    conflicts = run.get("conflicts", [])
    hydra = run.get("hydra", [])
    via_rows = run.get("via_rows", [])
    lk = run.get("lkgc", {})
    ip = run.get("install_plans", {})
    mirrors = run.get("mirrors", [])
    acc = run.get("accelerators", {})
    pipes = run.get("pipelines", {})
    rounds = run.get("round_progress", {})
    css = """
    :root{--bg:#f6f7fb;--fg:#1f2937;--card:#fff;--line:#d6dae3;--g:#16a34a;--y:#f59e0b;--r:#dc2626;--n:#9ca3af;--acc:#4f46e5}
    @media (prefers-color-scheme: dark){:root{--bg:#0f1115;--fg:#e5e7eb;--card:#161a22;--line:#2a2f3a}}
    *{box-sizing:border-box} body{margin:0;padding:10px;background:var(--bg);color:var(--fg);font:11px/1.35 Segoe UI,Arial,'Microsoft JhengHei',sans-serif}
    h1{font-size:15px;margin:0 0 4px} h2{font-size:12px;margin:0 0 6px;color:var(--acc)} .meta{font-size:10px;color:var(--n);margin-bottom:8px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:10px}
    .card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px;min-width:0}
    table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:10.5px} th,td{border:1px solid var(--line);padding:3px 4px;text-align:left;vertical-align:top;word-break:break-word;overflow-wrap:anywhere;white-space:pre-wrap}
    th{background:rgba(79,70,229,.08)} .lamp{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;background:var(--n)}
    .lamp.g{background:var(--g)} .lamp.y{background:var(--y)} .lamp.r{background:var(--r)}
    .bar{height:8px;background:var(--line);border-radius:4px;overflow:hidden} .bar>i{display:block;height:100%;background:var(--acc)}
    .zone{border-left:4px solid var(--acc);padding-left:6px;margin:12px 0 6px;font-size:12px;font-weight:700}
    .small{font-size:10px;color:var(--n)} .wrap{overflow-x:auto}
    """
    verdict = run.get("verdict", "NOT_RUN")
    parts = [f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
             f"<title>VIA EnvGovernance Matrix {_esc(run.get('ts'))}</title><style>{css}</style></head><body>"
             f"<h1>VIA 環境治理 UI Matrix · CGC_MDL135 v{VERSION}(批{BATCH})· 裁決 {_lamp(verdict)}</h1>"
             f"<div class='meta'>run {_esc(run.get('run_id'))} · {_esc(run.get('ts'))} · machine {_esc(run.get('machine'))} · base python {_esc(run.get('base_python'))} · "
             f"境 {len(scans)} · 衝突 {len(conflicts)} · 段 {len(plan.get('stages', []))}(並行 {plan.get('n_parallel', 0)}/序 {plan.get('n_sequential', 0)}/破壞候裁 {plan.get('n_destructive', 0)}) · "
             f"模式 {_esc(run.get('mode'))} · log {_esc(LOG_PATH)}</div>"]
    # 三輪進度
    parts.append("<div class='card'><h2>三輪進度(R1 全面並行 / R2 順序拓撲 / R3 收尾硬化)</h2><table><tr><th style='width:22%'>輪</th><th>進度</th><th style='width:45%'>說明</th></tr>")
    for r in ("R1", "R2", "R3"):
        pr = rounds.get(r, {"pct": 0, "note": ""})
        parts.append(f"<tr><td>{r}</td><td><div class='bar'><i style='width:{int(pr.get('pct', 0))}%'></i></div>{int(pr.get('pct', 0))}%</td><td>{_esc(pr.get('note'))}</td></tr>")
    parts.append("</table></div>")
    parts.append("<div class='zone'>MODULE — 環境(base / via_core / via_* / paddle_* / camelot_*)</div><div class='grid'>")
    parts.append("<div class='card'><table><tr><th style='width:16%'>境</th><th style='width:9%'>python</th><th style='width:8%'>件數</th><th style='width:10%'>快篩</th><th style='width:9%'>衝突</th><th style='width:12%'>狀態</th><th>說明</th></tr>")
    for s in scans:
        name = s["env"]["name"]
        st = "BROKEN" if not s.get("ok") else ("REBUILD" if s.get("conflicts") else "OK")
        if name == "BASE":
            st = "RED" if ba.get("blocked_present") else ("YELLOW" if ba.get("extras") or ba.get("manifest_missing") else "GREEN")
            note = f"該有冊閉包 {ba.get('keep_n', 0)} · 閉包外 {len(ba.get('extras', []))} · manifest 缺 {len(ba.get('manifest_missing', []))} · 封鎖家族件 {len(ba.get('blocked_present', []))}:{', '.join(ba.get('blocked_present', [])[:8])}"
        else:
            row = next((r for r in via_rows if r["env"] == name), {})
            st = row.get("status", st)
            note = "; ".join(row.get("notes", [])) or s.get("err", "") or s.get("check_note", "")
        parts.append(f"<tr><td>{_esc(name)}</td><td>{_esc(s.get('python'))}</td><td>{_ndists(s)}</td><td>{_esc(s.get('check_tool'))}</td><td>{len(s.get('conflicts', []))}</td><td>{_lamp(st)}</td><td>{_esc(note)}</td></tr>")
    parts.append("</table></div>")
    parts.append("<div class='card'><h2>九頭龍風險(H1 多層 / H2 分歧 / H3 共用節點 / 混居)</h2><table><tr><th style='width:20%'>碼</th><th style='width:10%'>級</th><th style='width:22%'>件</th><th>說明</th></tr>")
    for h in hydra or [{"code": "—", "sev": "GREEN", "pkg": "", "detail": "無風險項"}]:
        parts.append(f"<tr><td>{_esc(h.get('code'))}</td><td>{_lamp(h.get('sev'))}</td><td>{_esc(h.get('pkg'))}</td><td>{_esc(h.get('detail'))}</td></tr>")
    parts.append("</table></div></div>")
    parts.append("<div class='zone'>ENGINE — 引擎鏈與段冊(拓撲序)</div><div class='grid'>")
    parts.append("<div class='card'><h2>段冊(Parallel-Fixable 並行 / Sequence-Dependent 序跑)</h2><div class='wrap'><table><tr><th style='width:7%'>段</th><th style='width:5%'>輪</th><th style='width:12%'>類</th><th style='width:12%'>境</th><th>目標</th><th style='width:14%'>模擬</th><th style='width:12%'>執行</th></tr>")
    by = {s["id"]: s for s in plan.get("stages", [])}
    for i in plan.get("order", [s["id"] for s in plan.get("stages", [])]):
        s = by[i]
        parts.append(f"<tr><td>{_esc(s['id'])}</td><td>R{s['round']}</td><td>{_esc(s['cls'])}{'·破壞候裁' if s['destructive'] else ''}</td><td>{_esc(s['env'])}</td>"
                     f"<td>{_esc(s['goal'])}{('<br><span class=small>' + _esc(' '.join(s.get('pins', [])[:8])) + ('…' if len(s.get('pins', [])) > 8 else '') + '</span>') if s.get('pins') else ''}</td>"
                     f"<td>{_lamp(s['sim'].get('risk', 'NOT_RUN'))}<br><span class=small>{_esc(s['sim'].get('note', ''))}</span></td><td>{_lamp(s['result'].get('state', 'PENDING'))}<br><span class=small>{_esc(s['result'].get('note', ''))}</span></td></tr>")
    parts.append("</table></div></div>")
    parts.append("<div class='card'><h2>引擎鏈(多引擎整合 A19)</h2><table><tr><th style='width:30%'>引擎</th><th style='width:10%'>在位</th><th>職權</th></tr>")
    for e in run.get("engine_chain", []):
        parts.append(f"<tr><td>{_esc(e['name'])}</td><td>{_lamp('GREEN' if e['present'] else 'RED')}</td><td>{_esc(e['role'])}</td></tr>")
    parts.append("</table></div></div>")
    parts.append("<div class='zone'>FUNCTION-LIB — 函式庫(衝突 / 家族整包 / 閉包外路由)</div><div class='grid'>")
    parts.append("<div class='card'><h2>衝突(uv/pip check + 上船件證據)</h2><table><tr><th style='width:10%'>境</th><th style='width:16%'>要求者</th><th style='width:18%'>所需</th><th style='width:9%'>種類</th><th style='width:14%'>處置</th><th>說明</th></tr>")
    for c in conflicts or []:
        parts.append(f"<tr><td>{_esc(c.get('env'))}</td><td>{_esc(c.get('requirer'))} {_esc(c.get('requirer_ver'))}</td><td>{_esc(c.get('required'))}{_esc(c.get('spec'))} {('(裝 ' + _esc(c.get('installed')) + ')') if c.get('installed') else ''}</td><td>{_esc(c.get('kind'))}</td><td>{_lamp(c.get('severity'))} {_esc(c.get('action'))}</td><td>{_esc(c.get('note'))}<br><span class=small>{_esc(c.get('source'))}: {_esc(c.get('raw'))}</span></td></tr>")
    if not conflicts:
        parts.append("<tr><td colspan=6>無衝突(或 NOT_RUN 誠實—見 MODULE 快篩欄)</td></tr>")
    parts.append("</table></div>")
    parts.append("<div class='card'><h2>base 家族整包(拉出候選 → 目標境;單寫者律)</h2><table><tr><th style='width:12%'>家族</th><th style='width:7%'>級</th><th style='width:14%'>目標境</th><th style='width:22%'>家族根件</th><th>境內必要相依(隨行移除)</th><th style='width:16%'>引擎影響(import 根件)</th></tr>")
    for fam, b in sorted(ba.get("bundles", {}).items()):
        deps_only = [m for m in b['members'] if m not in set(b.get('roots', []))]
        parts.append(f"<tr><td>{_esc(fam)}</td><td>{_lamp(b['severity'])}</td><td>{_esc(b['target'])}{'' if b['target_exists'] else '(待建)'} py{_esc(b.get('python'))}</td><td>{_esc(', '.join(b.get('roots', [])))}</td>"
                     f"<td>{_esc(', '.join(deps_only))}<br><span class=small>閉包相依受影響:{_esc(', '.join(b.get('impact_kept', [])))}</span></td>"
                     f"<td>{b.get('engines_n', 0)}:{_esc(', '.join(b.get('engines', [])))}</td></tr>")
    if ba.get("shared_support"):
        parts.append(f"<tr><td>(共用支援件)</td><td>{_lamp('YELLOW')}</td><td>—</td><td colspan=3>多家族必要相依 {len(ba['shared_support'])} 件,所有家族境 VERIFY 綠後最後候裁:{_esc(', '.join(ba['shared_support']))}</td></tr>")
    for v in run.get("naming", []):
        parts.append(f"<tr><td>(命名律 H7)</td><td>{_lamp('YELLOW')}</td><td>{_esc(v['suggested'])}</td><td colspan=3>非 via_ 境 {_esc(v['env'])}(py{_esc(v.get('python'))} 件 {v.get('n_dists', 0)})→ via-envgov rename --from {_esc(v['env'])}</td></tr>")
    if not ba.get("bundles"):
        parts.append("<tr><td colspan=6>base 無封鎖家族/閉包外家族件</td></tr>")
    parts.append("</table><h2 style='margin-top:8px'>閉包外單件路由</h2><table><tr><th style='width:22%'>目標境</th><th>件(路由依據)</th></tr>")
    for tgt, items in sorted(ba.get("routed_other", {}).items()):
        items_txt = ", ".join("%s==%s(%s)" % (it["pkg"], it["ver"], it["via"]) for it in items)
        parts.append(f"<tr><td>{_esc(tgt)}</td><td>{_esc(items_txt)}</td></tr>")
    if ba.get("manifest_missing"):
        parts.append(f"<tr><td>BASE 補齊</td><td>manifest 缺:{_esc(', '.join(ba['manifest_missing']))}</td></tr>")
    parts.append("</table></div></div>")
    parts.append("<div class='zone'>OTHERS — 鏡像 / LKGC / 上船件證據 / 加速器 / 六流程</div><div class='grid'>")
    parts.append("<div class='card'><h2>鏡像鏈健康(清華 → 阿里 → PyPI 兜底)</h2><table><tr><th style='width:20%'>鏡像</th><th style='width:14%'>狀態</th><th style='width:12%'>ms</th><th>URL / 說明</th></tr>")
    for m in mirrors:
        parts.append(f"<tr><td>{_esc(m['label'])}</td><td>{_lamp('GREEN' if m['state'] == 'OK' else ('NOT_RUN' if m['state'] == 'NOT_RUN' else 'RED'))}</td><td>{_esc(m.get('ms'))}</td><td>{_esc(m['url'])} {_esc(m.get('note'))}</td></tr>")
    parts.append(f"</table><h2 style='margin-top:8px'>LKGC(前一次成功組合)</h2><table><tr><th style='width:30%'>項</th><th>值</th></tr>"
                 f"<tr><td>本跑快照</td><td>{_lamp(lk.get('verdict', 'NOT_RUN'))} eligible={_esc(lk.get('eligible'))} · {_esc('; '.join(lk.get('reasons', [])))}</td></tr>"
                 f"<tr><td>晉升</td><td>{_esc(json.dumps(run.get('lkgc_promote', {}), ensure_ascii=False)[:300])}</td></tr>"
                 f"<tr><td>還原序</td><td>①LKGC_latest lock 逐境 uv pip sync(base 端 --approve-remove)②無 LKGC → 原本規劃(Baseline)重建;via-envgov rollback</td></tr></table></div>")
    parts.append("<div class='card'><h2>上船件證據(VIA_Install_Plan_*.json)</h2><table><tr><th style='width:34%'>檔</th><th style='width:14%'>python</th><th>FAIL 段 / pip 註</th></tr>")
    for p in ip.get("plans", []):
        parts.append(f"<tr><td>{_esc(p['file'])}</td><td>{_esc(p.get('python'))}</td><td>{_esc(', '.join(p.get('fail_stages', [])))} · {_esc(p.get('pip_note'))}</td></tr>")
    for p in ip.get("persisted", []):
        parts.append(f"<tr><td colspan=3>{_lamp('RED')} 持續未閉環 ×{p['count']}:{_esc(p['note'])}</td></tr>")
    if not ip.get("plans"):
        parts.append("<tr><td colspan=3>無上船件(VIA_Reports/VIA_Install_Plan_*.json 或收容冊)</td></tr>")
    parts.append("</table></div>")
    parts.append("<div class='card'><h2>二十加速器(本引擎點亮)</h2><table><tr><th style='width:10%'>碼</th><th style='width:10%'>燈</th><th>職責 / 本跑用法</th></tr>")
    for k, v in sorted(acc.items()):
        parts.append(f"<tr><td>{_esc(k)}</td><td>{_lamp(v.get('lamp'))}</td><td>{_esc(v.get('zh'))}</td></tr>")
    parts.append("</table></div>")
    parts.append("<div class='card'><h2>六個獨立同步推進流程</h2><table><tr><th style='width:8%'>ID</th><th style='width:10%'>燈</th><th>流程 / 引擎</th></tr>")
    for k, v in sorted(pipes.items()):
        parts.append(f"<tr><td>{_esc(k)}</td><td>{_lamp(v.get('lamp'))}</td><td>{_esc(v.get('zh'))} — {_esc(v.get('engine'))}</td></tr>")
    parts.append("</table></div></div>")
    parts.append(f"<pre class='card' style='white-space:pre-wrap;margin-top:10px'>{_esc(chr(10).join(run.get('digest', [])))}</pre>")
    parts.append("</body></html>")
    return "".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# 摘要(digest ≤25 行;A17 動態說明)+ 加速器/流程燈 + 引擎鏈
# ══════════════════════════════════════════════════════════════════════════════
def engine_chain() -> list[dict]:
    rows = [("VIA_EnvManager.py(政策母版)", SUP / "VIA_EnvManager.py", "Gatekeeper:base 擋 M/H·via_core 白名單·purpose hints"),
            ("CGC_MDL050_EnvRebuild(旁建重建/拆分)", _newest("CGC_MDL050_EnvRebuild_v0*.py", REG), "via-rebuild --env/--split;uv pip compile 實測;GREEN 執行檔"),
            ("CGC_MDL051_EnvmgrNostall(平行掃描)", _newest("CGC_MDL051_EnvmgrNostall_v0*.py", REG), "20 工作器不卡斷"),
            ("CGC_MDL052_EnvmgrRouter(via-envmgr 路由)", _newest("CGC_MDL052_EnvmgrRouter_v0*.py", REG), "conflicts/scan→NoStall;govern→MDL135;餘→正本"),
            ("CGC_MDL056_InstallGate(via-install)", _newest("CGC_MDL056_InstallGate_v0*.py", REG), "安裝閘;--doctor 多層互撞;Lib Registry"),
            ("CGC_MDL062_Provision(via-provision --check)", _newest("CGC_MDL062_Provision_v0*.py", REG), "機況體檢→VIA_Install_Plan JSON(本引擎攝入)"),
            ("CGC_MDL046_DepSuper(via-deps)", _newest("CGC_MDL046_DepSuper_v0*.py", REG), "PEP440 判定;三鏡像測速"),
            ("VIA_MambaBridge(SAT dry-run 橋)", SUP / "VIA_MambaBridge_v0100.py", "micromamba 衝突併入 EnvManager 報告"),
            ("uv.toml + scripts/envcheck.{sh,ps1}", ROOT / "uv.toml", "鏡像鏈 清華→阿里→PyPI;Top 8 快篩"),
            ("VIA_EnvGovernance_Baseline(本冊)", _newest("VIA_EnvGovernance_Baseline_v*.json", REG), "base 該有冊/家族/路由/LKGC 律"),
            ("VIA_Env_Matrix_5D(25 規劃境)", REG / "VIA_Env_Matrix_5D_v0100.json", "5D 分類×環境分配藍圖"),
            ("VIA_Lessons_Ledger(SKIP 拒裝)", _newest("VIA_Lessons_Ledger_v*.json", REG), "H6 拒裝名單永不入計畫")]
    return [{"name": n, "present": bool(p and Path(p).exists()), "role": r} for n, p, r in rows]


def accel_lamps(run: dict) -> dict:
    b = run.get("_baseline", {}).get("accelerators", {})
    on = {"A03": bool(run.get("hydra") is not None), "A04": bool(run.get("plan", {}).get("order")), "A05": any(s["sim"].get("risk") not in ("NOT_RUN", None) for s in run.get("plan", {}).get("stages", [])),
          "A07": True, "A08": bool(run.get("_baseline")), "A09": True, "A10": True, "A11": any(s.get("check_tool") == "uv" for s in run.get("panorama", [])),
          "A12": len(run.get("panorama", [])) > 1, "A13": True, "A15": True, "A16": True, "A17": True, "A18": True, "A19": True,
          "A20": (run.get("apply_summary") or {}).get("ran", 0) > 0}
    out = {}
    for k, zh in b.items():
        out[k] = {"zh": zh, "lamp": "GREEN" if on.get(k) else "NOT_RUN"}
    return out


def pipeline_lamps(run: dict) -> dict:
    b = run.get("_baseline", {}).get("pipelines", {})
    ok = {"P4": True, "P6": True, "P1": bool(_newest("CGC_MDL127_SixStreams_v0*.py", REG)), "P2": bool(_newest("CGC_MDL115_SSOTRegexDict_v*.py", REG)),
          "P3": bool(_newest("CGC_MDL113_UnifiedRegistry_v*.py", REG)), "P5": bool(_newest("CGC_MDL064_SelftestGrid_v0*.py", REG))}
    return {k: {"zh": v.get("zh"), "engine": v.get("engine"), "lamp": "GREEN" if ok.get(k) else "NOT_RUN"} for k, v in b.items()}


def make_digest(run: dict) -> list[str]:
    scans = run.get("panorama", [])
    ba = run.get("base_analysis", {})
    plan = run.get("plan", {"stages": []})
    conflicts = run.get("conflicts", [])
    L = [f"=== VIA 環境治理 digest · MDL135 v{VERSION} · {run.get('ts')} · 裁決 {run.get('verdict')} · 模式 {run.get('mode')} · 境 {len(scans)} ==="]
    ok_names = []
    for s in scans:
        n = s["env"]["name"]
        st = "BROKEN" if not s.get("ok") else ("REBUILD" if s.get("conflicts") else "OK")
        if n == "BASE":
            st = "RED" if ba.get("blocked_present") else ("YELLOW" if ba.get("extras") or ba.get("manifest_missing") else "GREEN")
        elif st == "OK":
            ok_names.append(n)  # 24 境實錄:OK 境收攏一行,保住拉出/段冊/LKGC/下一指令
            continue
        L.append(f"  [{LAMP.get(st, LAMP.get('GREEN' if st == 'OK' else 'RED'))} {st:7s}] {n:22s} py{s.get('python', '?'):8s} 件 {_ndists(s):4d} · 快篩 {s.get('check_tool', '?'):7s} · 衝突 {len(s.get('conflicts', []))}")
    if ok_names:
        L.append(f"  [{LAMP['GREEN']} OK     ] 其餘 {len(ok_names)} 境零衝突:{', '.join(ok_names[:10])}{' …' if len(ok_names) > 10 else ''}")
    L.append(f"  base 該有冊({ba.get('manifest_src', '?')}):閉包 {ba.get('keep_n', 0)} · 閉包外 {len(ba.get('extras', []))} · manifest 缺 {len(ba.get('manifest_missing', []))} · 封鎖家族件 {len(ba.get('blocked_present', []))}" + (f" · OS 管理不動 {len(ba['os_managed'])}" if ba.get('os_managed') else ""))
    for fam, b in sorted(ba.get("bundles", {}).items(), key=lambda kv: (kv[1]["severity"] != "RED", -len(kv[1]["members"])))[:7]:
        roots = b.get("roots", [])
        L.append(f"    拉出 {LAMP[b['severity']]} {fam:16s} → {b['target']}{'' if b['target_exists'] else '(待建)'}:{', '.join(roots[:4])}{' …' if len(roots) > 4 else ''}"
                 f" +相依 {max(0, len(b['members']) - len(roots))} · 引擎影響 {b.get('engines_n', 0)}")
    if ba.get("shared_support"):
        L.append(f"    共用支援件 {len(ba['shared_support'])}(多家族相依;最後候裁):{', '.join(ba['shared_support'][:8])}{' …' if len(ba['shared_support']) > 8 else ''}")
    for v in run.get("naming", [])[:3]:
        L.append(f"    命名律 🟡 非 via_ 境 {v['env']} → {v['suggested']}(py{v.get('python') or '?'} 件 {v.get('n_dists', 0)};via-envgov rename --from {v['env']})")
    for tgt, items in sorted(ba.get("routed_other", {}).items())[:4]:
        L.append(f"    改道 → {tgt}:{', '.join(it['pkg'] for it in items[:8])}{' …' if len(items) > 8 else ''}")
    for c in conflicts[:6]:
        L.append(f"    衝突 {LAMP[c['severity']]} {c['env']} {c['requirer']} → {c['required']}{c.get('spec', '')} [{c['kind']}] {c['action']}")
    ip = run.get("install_plans", {})
    for p in ip.get("persisted", [])[:2]:
        L.append(f"    上船件持續未閉環 ×{p['count']}:{p['note'][:90]}")
    L.append(f"  段冊 {len(plan.get('stages', []))}:並行 {plan.get('n_parallel', 0)} · 序 {plan.get('n_sequential', 0)} · 破壞候裁 {plan.get('n_destructive', 0)} · 波 {len(plan.get('waves', []))}")
    sims = [s for s in plan.get("stages", []) if s["kind"] in ("INSTALL", "REPAIR_BASE")]
    if sims:
        L.append("  模擬:" + " · ".join(f"{s['id']} {s['sim'].get('risk')}" for s in sims[:8]))
    ap = run.get("apply_summary")
    if ap:
        L.append(f"  執行:跑 {ap.get('ran', 0)} OK {ap.get('ok', 0)} FAIL {ap.get('fail', 0)} SKIP {ap.get('skipped', 0)} BLOCKED {ap.get('blocked', 0)}")
    lk = run.get("lkgc", {})
    L.append(f"  LKGC:{lk.get('verdict')} eligible={lk.get('eligible')} {'; '.join(lk.get('reasons', []))[:100]} · 晉升 {run.get('lkgc_promote', {}).get('promoted')}")
    L.append(f"  存證:{run.get('run_json')} · matrix {run.get('matrix')} · log {LOG_PATH}")
    nxt = []
    if ba.get("bundles") or ba.get("routed_other"):
        nxt.append("via-envgov apply --approve(GREEN 非破壞段:建境/裝件/驗證)→ 目標境綠後 via-envgov apply --approve --approve-remove")
    if any(s["kind"] in ("DELEGATE_REBUILD", "DELEGATE_SPLIT") for s in plan.get("stages", [])):
        nxt.append("; ".join(sorted({s.get('argv_hint', '') for s in plan.get('stages', []) if s.get('argv_hint') and s['kind'].startswith('DELEGATE')})))
    if run.get("naming"):
        nxt.append("via-envgov rename(唯讀出令)→ via-envgov rename --execute --approve(建境+同步+驗證)→ --approve-remove 退役舊境")
    if run.get("mode") == "offline":
        nxt.append("$env:VIA_NET_CONSENT='YES'; via-envgov plan(上網模擬 uv pip compile 多輪)")
    if not lk.get("eligible"):
        nxt.append("最壞還原:via-envgov rollback(LKGC 有=lock 逐境 sync;無=原本規劃重建)")
    L.append("  下一指令:" + (" | ".join(nxt) if nxt else "無(全綠;LKGC 已晉升)"))
    if len(L) > 25:  # 上限 25 行:中段省略,尾三行(LKGC/存證/下一指令)必留
        L = L[:21] + [f"  …(省略 {len(L) - 24} 行;完整見矩陣 {run.get('matrix')} 或 RUN JSON)"] + L[-3:]
    return L


# ══════════════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════════════
def do_run(args: list[str], mode: str = "run") -> int:
    t0 = time.time()
    baseline = load_baseline()
    offline = "--offline" in args or not _consent()
    quiet = "--quiet" in args
    workers = int(_arg_after(args, "--workers") or 20)
    task_timeout = int(_arg_after(args, "--task-timeout") or 120)
    rounds_n = int(_arg_after(args, "--rounds") or forge_policy().get("max_rounds", 3))
    roots = [r for r in (_arg_after(args, "--roots") or "").split(os.pathsep) if r]
    env_root = _arg_after(args, "--env-root")
    base_python = _arg_after(args, "--base-python")
    only = _arg_after(args, "--env")
    approve = "--approve" in args
    approve_remove = "--approve-remove" in args
    ts = _RUN_ID
    skips = lessons_skip()
    print(f"=== VIA 環境治理引擎 MDL135 v{VERSION}(批{BATCH})· {mode} · {ts} · {'離線' if offline else '上網(同意閘開)'} · 加速器 {workers} · 逾時 {task_timeout}s/境 ===")
    print(f"  [冊] {baseline.get('_src')} · EnvManager 母版 {'在' if em_policy() else '缺(鏡射保底)'} · Lessons SKIP {len(skips)} · uv {'在' if _UV else '缺'} · log {LOG_PATH}")
    log_event("RUN_START", "*", "", mode, f"offline={offline} workers={workers} argv={' '.join(args)[:120]}")
    envs = discover_envs(baseline, roots, env_root, base_python, only)
    if envs[0].get("warn"):
        print(f"  [警] {envs[0]['warn']}")
    er = env_root or next((str(r) for r in discover_roots(roots, None) if r.is_dir()), str(Path.home() / "envs"))
    print(f"  [境] {len(envs)} 個:{', '.join(e['name'] for e in envs)} · 目標境根 {er}")
    scans = panorama(envs, workers=workers, task_timeout=task_timeout, quiet=quiet)
    base = next(s for s in scans if s["env"]["name"] == "BASE")
    present = {s["env"]["name"] for s in scans if s["env"]["name"] != "BASE"}
    ba = analyze_base(base, baseline, present, skips)
    conflicts = classify_conflicts(scans, baseline, ba, skips)
    hydra = hydra_risks(scans, baseline, ba)
    via_rows = analyze_via_envs(scans, baseline)
    naming = naming_check(scans, baseline)
    ip = ingest_install_plans(baseline, [_arg_after(args, "--install-plan") or ""])
    plan = build_plan(scans, baseline, ba, conflicts, hydra, via_rows, er, skips, naming)
    mirrors = mirror_health(baseline) if not offline else [{"label": l, "url": u, "state": "NOT_RUN", "ms": None, "note": "離線"} for l, u in zip(baseline["mirror_chain"].get("labels", []), baseline["mirror_chain"]["order"])]
    mirror_url = next((m["url"] for m in sorted([m for m in mirrors if m["state"] == "OK"], key=lambda m: m.get("ms") or 9e9)), "")
    if mode in ("run", "plan", "apply"):
        simulate(plan, scans, rounds_n, offline, mirror_url="" if (ROOT / "uv.toml").exists() else mirror_url)
    apply_summary = None
    if mode in ("run", "apply") and approve:
        print("--- apply(授權閉環:GREEN 非破壞段;移除須 --approve-remove)---")
        only_stages = {x.strip().upper() for x in (_arg_after(args, "--only") or "").split(",") if x.strip()} or None
        only_kinds = {x.strip().upper() for x in (_arg_after(args, "--only-kind") or "").split(",") if x.strip()} or None
        if only_kinds:
            print(f"  [apply] --only-kind {','.join(sorted(only_kinds))}(段類過濾;其餘段 SKIP)")
        apply_summary = apply_plan(plan, scans, approve, approve_remove, baseline, skips, only_stages, only_kinds)
        if apply_summary.get("ran"):
            print("  [再掃] 執行後全景複驗")
            envs2 = discover_envs(baseline, roots, env_root, base_python, only)
            scans = panorama(envs2, workers=workers, task_timeout=task_timeout, quiet=True)
            base = next(s for s in scans if s["env"]["name"] == "BASE")
            present = {s["env"]["name"] for s in scans if s["env"]["name"] != "BASE"}
            ba = analyze_base(base, baseline, present, skips)
            conflicts = classify_conflicts(scans, baseline, ba, skips)
    lk = lkgc_snapshot(scans, ba, conflicts, ts)
    promote = lkgc_promote(lk) if mode in ("run", "apply", "panorama", "plan") else {}
    hard = [c for c in conflicts if c.get("action") != "METADATA_SHADOWED"]
    verdict = "RED" if (ba.get("blocked_present") or any(c["severity"] == "RED" for c in hard)) else ("YELLOW" if (hard or ba.get("extras") or ba.get("manifest_missing") or naming or any(r["status"] != "OK" for r in via_rows)) else "GREEN")
    n_st = len(plan["stages"]) or 1
    r1 = [s for s in plan["stages"] if s["round"] == 1]
    r2 = [s for s in plan["stages"] if s["round"] == 2]
    r3 = [s for s in plan["stages"] if s["round"] == 3]

    def pct(lst):
        if not lst:
            return 100
        done = sum(1 for s in lst if s["result"].get("state") in ("OK", "SKIP_EXISTS"))
        return int(100 * done / len(lst))
    run = {"schema": "VIA.EnvGovernance.Run.v1", "run_id": ts, "ts": now_iso(), "machine": machine_hash(), "mode": ("offline" if offline else "online") + f"/{mode}",
           "base_python": base.get("python"), "verdict": verdict, "_baseline": baseline, "panorama": [{k: v for k, v in s.items()} for s in scans],
           "base_analysis": ba, "conflicts": conflicts, "hydra": hydra, "via_rows": via_rows, "naming": naming, "install_plans": ip, "plan": plan, "mirrors": mirrors,
           "apply_summary": apply_summary, "lkgc": lk, "lkgc_promote": promote, "engine_chain": engine_chain(),
           "round_progress": {"R1": {"pct": pct(r1), "note": f"全面性(並行段 {len(r1)}):{'已授權執行' if approve else '計畫唯讀'}"},
                              "R2": {"pct": pct(r2), "note": f"順序性(拓撲段 {len(r2)};破壞候裁 {sum(1 for s in r2 if s['destructive'])}):{'--approve-remove' if approve_remove else '候裁'}"},
                              "R3": {"pct": 100 if lk.get("eligible") else 33, "note": f"硬化:lock {len(lk.get('envs', {}))} 境 · LKGC {'晉升' if promote.get('promoted') else '未晉升'}"}},
           "elapsed_s": round(time.time() - t0, 1)}
    run["accelerators"] = accel_lamps(run)
    run["pipelines"] = pipeline_lamps(run)
    OUT.mkdir(parents=True, exist_ok=True)
    run_json = OUT / f"RUN_{ts}.json"
    run["run_json"] = str(run_json)
    mpath = OUT / f"VIA_EnvGovernance_Matrix_{ts}.html"
    run["matrix"] = str(mpath)
    run["digest"] = make_digest(run)
    slim = dict(run)
    slim["panorama"] = [{**{k: v for k, v in s.items() if k != "dists"}, "n_dists": len(s.get("dists", {}))} for s in scans]  # 全 dists 存 lock 檔,RUN 精簡
    _write_json(run_json, slim)
    _write_json(RUN_LATEST, slim)
    html_txt = render_matrix(run)
    mpath.write_text(html_txt, encoding="utf-8")
    MATRIX_LATEST.write_text(html_txt, encoding="utf-8")
    if mode in ("run", "plan", "apply"):
        ps_txt, sh_txt = emit_scripts(plan, base.get("env", {}).get("py") or sys.executable, ts)
        (OUT / f"PLAN_EXEC_{ts}.ps1").write_text(ps_txt, encoding="utf-8-sig")
        (OUT / f"PLAN_EXEC_{ts}.sh").write_text(sh_txt, encoding="utf-8")
    print("\n".join(run["digest"]))
    print(f"  [段檔] PLAN_EXEC_{ts}.ps1/.sh(候裁段以 # 註記)· 耗時 {run['elapsed_s']}s")
    log_event("RUN_END", "*", "", verdict, f"envs={len(scans)} conflicts={len(conflicts)} stages={len(plan['stages'])} lkgc={lk.get('verdict')} promoted={promote.get('promoted')} {run['elapsed_s']}s")
    if "--open" in args and not _no_open():
        try:
            import webbrowser
            webbrowser.open(mpath.as_uri())
        except Exception:
            pass
    return 0 if verdict != "RED" else 1


def do_matrix() -> int:
    run = _read_json(RUN_LATEST, None)
    if not run:
        print("  [matrix] 無 RUN_latest.json(先 via-envgov run)")
        return 2
    run["_baseline"] = load_baseline()
    run["accelerators"] = accel_lamps(run)
    run["pipelines"] = pipeline_lamps(run)
    html_txt = render_matrix(run)
    MATRIX_LATEST.write_text(html_txt, encoding="utf-8")
    print(f"  [matrix] {MATRIX_LATEST}")
    return 0


def do_digest() -> int:
    run = _read_json(RUN_LATEST, None)
    if not run:
        print("  [digest] 無 RUN_latest.json(先 via-envgov run)")
        return 2
    try:
        print("\n".join(make_digest(run)))  # 以現行碼自 RUN 存證重生(舊存證 digest 若被截斷亦可補全)
    except BrokenPipeError:
        return 0
    except Exception:
        print("\n".join(run.get("digest", [])))
    return 0


def do_lkgc(args: list[str]) -> int:
    sub = next((a for a in args if a in ("snapshot", "promote", "status")), "status")
    if sub == "status":
        st = lkgc_status()
        lt = st.get("latest") or {}
        print(f"  [LKGC] latest {lt.get('ts', '無')} · verdict {lt.get('verdict', '—')} · 境 {len(lt.get('envs', {}))} · 史 {st['history_n']} 筆:{', '.join(st['history'])}")
        if st.get("candidate"):
            print(f"  [候選] {st['candidate'].get('ts')} 未晉升:{'; '.join(st['candidate'].get('reasons', []))}")
        return 0
    return do_run(args, mode="panorama")


def rollback_inputs(args: list[str]) -> tuple:
    """批508:還原輸入(LKGC 或 Baseline 的 scans/境根/計畫)——do_rollback 與 do_recover 共用(同一判準只寫一處)。"""
    baseline = load_baseline()
    to = _arg_after(args, "--to")
    force_base = "--baseline" in args
    env_root = _arg_after(args, "--env-root") or next((str(r) for r in discover_roots([], None) if r.is_dir()), str(Path.home() / "envs"))
    scans = None
    if force_base or not LKGC_LATEST.exists():
        run = _read_json(RUN_LATEST, None)
        if run:
            scans = [{"env": s["env"], "ok": s.get("ok"), "dists": {}, "python": s.get("python")} for s in run.get("panorama", [])]
            lk = _read_json(OUT / f"LKGC_{run.get('run_id')}.json", None)
            if lk:
                for s in scans:
                    lock = (lk.get("envs", {}).get(s["env"]["name"]) or {}).get("lock")
                    if lock and Path(lock).exists():
                        s["dists"] = {l.split("==")[0]: {"ver": l.split("==")[1]} for l in Path(lock).read_text(encoding="utf-8").splitlines() if "==" in l and not l.startswith("#")}
    rb = rollback_plan(baseline, to, force_base, scans, env_root)
    return baseline, rb, env_root


def do_rollback(args: list[str]) -> int:
    baseline, rb, env_root = rollback_inputs(args)
    print(f"=== 還原計畫 · {rb['mode']} ===")
    for it in rb["items"]:
        print(f"  [{it['state']:4s}] {it['env']:22s} {it.get('lock') or it.get('family', '')} {'(破壞:sync 候裁)' if it.get('destructive') else ''}")
    print(f"  [檔] {rb['ps']} / {rb['sh']}")
    if "--execute" in args:
        r = rollback_execute(rb, "--approve" in args, "--approve-remove" in args)
        print(f"  [執行] {r}")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# 自測(零網路零環境依賴)
# ══════════════════════════════════════════════════════════════════════════════
def _selftest_body() -> int:
    import tempfile
    checks = []

    def chk(name, cond):
        checks.append((name, bool(cond)))
        print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
    global LOG_PATH, OUT, LOCK_DIR, LKGC_LOCK_DIR, LKGC_LATEST, RUN_LATEST, MATRIX_LATEST
    keep = (LOG_PATH, OUT, LOCK_DIR, LKGC_LOCK_DIR, LKGC_LATEST, RUN_LATEST, MATRIX_LATEST)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        LOG_PATH = tdp / "logs" / "env_governance.log"
        OUT = tdp / "out"
        LOCK_DIR, LKGC_LOCK_DIR = OUT / "lock", OUT / "lock_lkgc"
        LKGC_LATEST, RUN_LATEST, MATRIX_LATEST = OUT / "LKGC_latest.json", OUT / "RUN_latest.json", OUT / "m.html"
        try:
            b = load_baseline()
            chk("① 本冊載入(base manifest 三層+families+cv2 錨)", b.get("base", {}).get("engine_core") and b.get("families") and b.get("cv2_anchor"))
            pip_txt = "albucore 0.0.24 requires opencv-python-headless, which is not installed.\nyake 0.7.3 has requirement click>=6, but you have click 5.0."
            uv_txt = "The package `albucore` requires `opencv-python-headless>=4.9.0.80`, but it's not installed\nThe package `fakepkg` requires `oldlib>=2.0`, but `1.0` is installed\nThe package `oldlib` is broken or incomplete (unable to read `WHEEL` file)."
            pc, uc = parse_check_lines(pip_txt, "pip"), parse_check_lines(uv_txt, "uv")
            chk("② pip check 行解析(MISSING+MISMATCH)", len(pc) == 2 and pc[0]["required"] == "opencv-python-headless" and pc[0]["kind"] == "MISSING" and pc[1]["kind"] == "MISMATCH" and pc[1]["installed"] == "5.0")
            chk("③ uv pip check 行解析(MISSING+MISMATCH+BROKEN;spec 抽取)", len(uc) == 3 and uc[0]["spec"] == ">=4.9.0.80" and uc[1]["installed"] == "1.0" and uc[2]["kind"] == "BROKEN")
            chk("④ 需求字串解析(名/spec/extra)", parse_req('opencv-python-headless>=4.9; extra == "x"') == ("opencv-python-headless", ">=4.9", True) and parse_req("Numpy") == ("numpy", "", False))
            dists = {"pandas": {"ver": "3.0.2", "requires": ["numpy>=1.26", "python-dateutil", "pytz"]}, "numpy": {"ver": "2.2.0", "requires": []},
                     "python-dateutil": {"ver": "2.9", "requires": ["six"]}, "six": {"ver": "1.17", "requires": []}, "pytz": {"ver": "2025.1", "requires": []},
                     "paddleocr": {"ver": "3.1.0", "requires": ["paddlex", "numpy", "albumentations"]}, "paddlex": {"ver": "3.1.0", "requires": ["opencv-contrib-python", "numpy"]},
                     "albumentations": {"ver": "2.0.8", "requires": ["albucore", "numpy", "pyyaml", "scipy"]}, "albucore": {"ver": "0.0.24", "requires": ["opencv-python-headless>=4.9.0.80", "numpy"]},
                     "opencv-contrib-python": {"ver": "4.11.0.86", "requires": ["numpy"]}, "streamlit": {"ver": "1.40", "requires": ["pandas<3", "altair"]}, "altair": {"ver": "5.4", "requires": []},
                     "pip": {"ver": "25.0", "requires": []}, "rich": {"ver": "13.9", "requires": []}, "scipy": {"ver": "1.15", "requires": ["numpy"]}, "pyyaml": {"ver": "6.0", "requires": []},
                     "fastapi": {"ver": "0.115", "requires": ["starlette", "pydantic"]}, "starlette": {"ver": "0.41", "requires": []}, "pydantic": {"ver": "2.10", "requires": []},
                     "unknownlib": {"ver": "0.1", "requires": []}}
            base_scan = {"env": {"name": "BASE", "py": sys.executable}, "ok": True, "python": "3.13.7", "dists": dists, "dup": {}, "conflicts": pc[:1], "check_tool": "uv"}
            skips = {"opencv-python-headless": "everywhere", "opencv-python": "everywhere", "opencv-contrib-python": "base", "enum34": "everywhere"}
            ba = analyze_base(base_scan, b, {"via_core_312"}, skips)
            ocr = ba["bundles"].get("ocr", {})
            chk("⑤ base 該有冊閉包(pandas→numpy/dateutil/six/pytz 留;閉包外=拉出候選)", "six" not in ba["extras"] and "numpy" not in ba["extras"] and "paddleocr" in ba["extras"])
            chk("⑥ OCR 家族整包(paddleocr+paddlex+albumentations+albucore+contrib 同包;RED;目標 via_paddle_311 待建=命名律)",
                ocr and set(ocr["members"]) >= {"paddleocr", "paddlex", "albumentations", "albucore", "opencv-contrib-python"} and ocr["severity"] == "RED" and ocr["target"] == "via_paddle_311" and not ocr["target_exists"]
                and ocr["roots"] == ["albucore", "albumentations", "opencv-contrib-python", "paddleocr", "paddlex"] and "engines_n" in ocr)
            webui = ba["bundles"].get("webui", {})
            plotui = ba["bundles"].get("plot_ui", {})
            chk("⑦ webui(streamlit)與 plot_ui(altair)各歸各家族(單寫者律);fastapi → via_core 白名單改道;unknownlib → 黑環境",
                webui and webui["members"] == ["streamlit"] and plotui and plotui["members"] == ["altair"]
                and any(it["pkg"] == "fastapi" and it["via"] == "via_core_whitelist" for it in ba["routed_other"].get("via_core_312", []))
                and any(it["pkg"] == "unknownlib" for it in ba["routed_other"].get("via_iso_quarantine", [])))
            cc = classify_conflicts([base_scan], b, ba, skips)
            chk("⑧ 衝突分類:base albucore→headless = PULL_OUT RED(要求者屬 OCR 家族)", cc and cc[0]["action"] == "PULL_OUT" and cc[0]["severity"] == "RED" and cc[0]["family"] == "ocr")
            via_scan = {"env": {"name": "paddle_312", "py": sys.executable, "path": "/x/paddle_312"}, "ok": True, "python": "3.12.4",
                        "dists": {"albucore": {"ver": "0.0.24", "requires": ["opencv-python-headless>=4.9"]}, "opencv-contrib-python": {"ver": "4.11", "requires": []}},
                        "dup": {}, "conflicts": uc[:1], "check_tool": "uv"}
            via_scan["conflicts"][0]["env"] = "paddle_312"
            cc2 = classify_conflicts([via_scan], b, ba, skips)
            chk("⑨ OCR 境內 albucore→headless 且 contrib 錨在 = METADATA_SHADOWED YELLOW(接受殘餘;不裝 headless)", cc2 and cc2[0]["action"] == "METADATA_SHADOWED" and cc2[0]["severity"] == "YELLOW")
            pins, dropped = _pins_for_bundle(ocr, dists, b, skips)
            chk("⑩ 目標境 pins:完整閉包鎖 base 現版(含 numpy);cv2 家族換錨 contrib;SKIP everywhere 剔除", "paddleocr==3.1.0" in pins and "numpy==2.2.0" in pins and "opencv-contrib-python==4.11.0.86" in pins and not any("headless" in p for p in pins) and "numpy" not in ocr["members"])
            hy = hydra_risks([base_scan, via_scan], b, ba)
            chk("⑪ 九頭龍:H3 共用節點統計在;H2 分歧偵測(numpy 2 vs 無)不誤報", any(h["code"] == "H3_SHARED_TOP" for h in hy) and not any(h["code"] == "H2_DIVERGE" for h in hy))
            vr = analyze_via_envs([base_scan, via_scan, {"env": {"name": "via_core_312"}, "ok": True, "python": "3.12", "dists": {"requests": {"ver": "2.32", "requires": []}, "torch": {"ver": "2.5", "requires": []}}, "dup": {}, "conflicts": []}], b)
            chk("⑫ via_core 白名單違規偵測(torch 外件→家族改道)", any(r["env"] == "via_core_312" and r.get("core_violations") == ["torch"] for r in vr))
            plan = build_plan([base_scan, via_scan], b, ba, cc, hy, vr, str(tdp / "envs"), skips)
            kinds = [s["kind"] for s in plan["stages"]]
            order = plan["order"]
            by = {s["id"]: s for s in plan["stages"]}
            rm = next(s for s in plan["stages"] if s["kind"] == "REMOVE_BASE" and s.get("family") == "ocr")
            ver = by[rm["deps"][0]]
            chk("⑬ 段冊:ENSURE/INSTALL/VERIFY 並行 R1;REMOVE_BASE 序跑 R2 破壞候裁;LOCK/PROMOTE R3", "ENSURE_ENV" in kinds and rm["cls"] == "SEQUENTIAL" and rm["round"] == 2 and rm["destructive"] and ver["kind"] == "VERIFY" and "PROMOTE_LKGC" in kinds)
            chk("⑭ 拓撲序(Kahn):每段前置皆先於本段;波分組覆蓋全段", all(order.index(d) < order.index(s["id"]) for s in plan["stages"] for d in s["deps"]) and sum(len(w) for w in plan["waves"]) == len(order))
            chk("⑮ 模擬判讀:一致=GREEN/飄移=YELLOW/失敗=RED/零輪=NOT_RUN", judge_rounds([{"rc": 0, "would": ["a"]}, {"rc": 0, "would": ["a"]}])[1] == "GREEN" and judge_rounds([{"rc": 0, "would": ["a"]}, {"rc": 0, "would": ["b"]}])[1] == "YELLOW"
                and judge_rounds([{"rc": 1, "would": [], "tail": "x"}])[1] == "RED" and judge_rounds([])[1] == "NOT_RUN")
            ap = apply_plan(plan, [base_scan], approve=False, approve_remove=False)
            chk("⑯ 未授權 apply = 全段 SKIP(零安裝零刪除)", ap["ran"] == 0 and all(s["result"]["state"] == "SKIP" for s in plan["stages"]))
            lk = lkgc_snapshot([base_scan, via_scan], ba, cc, "t")
            pr = lkgc_promote(lk)
            chk("⑰ LKGC:base 封鎖家族在=不晉升(誠實原因;候選檔);lock 檔落地", not pr["promoted"] and any("封鎖" in r for r in lk["reasons"]) and (LOCK_DIR / "BASE.lock.txt").exists())
            clean = {"env": {"name": "BASE", "py": sys.executable}, "ok": True, "python": "3.13.7", "dists": {k: v for k, v in dists.items() if k in ("pandas", "numpy", "python-dateutil", "six", "pytz", "pip", "rich", "scipy", "pyyaml")}, "dup": {}, "conflicts": [], "check_tool": "uv"}
            ba2 = analyze_base(clean, b, set(), skips)
            lk2 = lkgc_snapshot([clean], ba2, [], "t2")
            pr2 = lkgc_promote(lk2)
            chk("⑱ LKGC:乾淨 base(manifest 缺件除外判定=僅衝突/封鎖/探針)→ 缺件時仍不晉升;無缺件方晉升", (not pr2["promoted"] and any("manifest 缺" in r for r in lk2["reasons"])))
            rb = rollback_plan(b, None, True, [clean], str(tdp / "envs"))
            chk("⑲ rollback 原本規劃(無 LKGC):base 補齊+layout 境建;檔落地", rb["mode"].startswith("原本規劃") and any(i["env"] == "BASE" for i in rb["items"]) and Path(rb["sh"]).exists())
            ip = ingest_install_plans(b, [])
            chk("⑳ 上船件攝入(收容冊 InstallPlan;缺=誠實 0)", isinstance(ip.get("n_plans"), int))
            run = {"run_id": "t", "ts": "t", "machine": "m", "mode": "offline/test", "base_python": "3.13.7", "verdict": "RED", "_baseline": b, "panorama": [base_scan, via_scan],
                   "base_analysis": ba, "conflicts": cc, "hydra": hy, "via_rows": vr, "install_plans": ip, "plan": plan, "mirrors": mirror_health({"mirror_chain": b["mirror_chain"]}) if not _consent() else [],
                   "lkgc": lk, "lkgc_promote": pr, "engine_chain": engine_chain(), "round_progress": {"R1": {"pct": 0, "note": ""}, "R2": {"pct": 0, "note": ""}, "R3": {"pct": 0, "note": ""}}}
            run["accelerators"], run["pipelines"] = accel_lamps(run), pipeline_lamps(run)
            run["digest"] = make_digest(run)
            h = render_matrix(run)
            chk("㉑ HTML 四分區(MODULE/ENGINE/FUNCTION-LIB/OTHERS)+RYG+進度條+自動換行 CSS+零 CDN", all(z in h for z in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS")) and "overflow-wrap" in h and "class='bar'" in h and "http" not in h.split("<body>")[0].replace("http-equiv", ""))
            chk("㉒ digest ≤25 行且含下一指令", 0 < len(run["digest"]) <= 25 and any("下一指令" in l for l in run["digest"]))
            chk("㉓ log JSONL append-only 落地(成敗皆記)", LOG_PATH.exists() and len(LOG_PATH.read_text(encoding="utf-8").splitlines()) >= 5 and all(json.loads(l).get("kind") for l in LOG_PATH.read_text(encoding="utf-8").splitlines()))
            root = tdp / "envs"
            for n in ("via_core_312", "paddle_312", "_retire_via_old", "notmanaged"):
                (root / n).mkdir(parents=True)
                (root / n / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
            ev = discover_envs(b, [str(root)], None, None)
            names = [e["name"] for e in ev]
            chk("㉔ 環境發現:管理前綴+pyvenv.cfg;_retire_ 與非管理名除名;BASE 首列", names[0] == "BASE" and "via_core_312" in names and "paddle_312" in names and "_retire_via_old" not in names and "notmanaged" not in names)
            argvs, ps, sh = stage_commands(next(s for s in plan["stages"] if s["kind"] == "INSTALL"), sys.executable)
            chk("㉕ 段令:INSTALL 出 uv pip install --python;ps/sh 雙令;sh 路徑 posix", argvs and argvs[0][1:3] == ["pip", "install"] and ps and sh and "\\" not in sh[0])
            # 批382:非可選閉包+單寫者律+專屬境覆寫+命名律+引擎影響
            d2 = {"pip": {"ver": "25", "requires": []}, "numpy": {"ver": "2.2", "requires": []},
                  "paddleocr": {"ver": "3.1", "requires": ["numpy", "shared-util", 'optdep; extra == "full"']}, "shared-util": {"ver": "1.0", "requires": []}, "optdep": {"ver": "0.1", "requires": []},
                  "streamlit": {"ver": "1.40", "requires": ["shared-util", "numpy"]}, "catboost": {"ver": "1.2", "requires": ["numpy"]}, "lxml": {"ver": "5.3", "requires": []},
                  "pdf2docx": {"ver": "0.5", "requires": ["lxml", "numpy"]}}
            sc2 = {"env": {"name": "BASE", "py": sys.executable}, "ok": True, "python": "3.13.7", "dists": d2, "dup": {}, "conflicts": [], "check_tool": "uv"}
            ba2 = analyze_base(sc2, b, {"via_core_312", "via_catboost", "via_html_312"}, skips)
            chk("㉖ 家族整包只走必要相依(extra 可選件 optdep 不入包);多家族共用 shared-util=共用支援件不歸任一家族;lxml 歸 html_parse 但 docs 境 install 含之(自足)",
                "optdep" not in ba2["bundles"]["ocr"]["members"] and "optdep" not in ba2["bundles"]["ocr"]["install"]
                and ba2["shared_support"] == ["shared-util"] and all("shared-util" not in bb["members"] for bb in ba2["bundles"].values())
                and "lxml" in ba2["bundles"]["html_parse"]["members"] and "lxml" not in ba2["bundles"]["docs"]["members"] and "lxml" in ba2["bundles"]["docs"]["install"])
            chk("㉗ 專屬境覆寫:catboost → via_catboost(package_env_overrides;既有境)不入 ml_boost 家族整包", "ml_boost" not in ba2["bundles"]
                and any(it["pkg"] == "catboost" and it["via"] == "package_env_overrides" and it["exists"] for it in ba2["routed_other"].get("via_catboost", [])))
            fake = [sc2, {"env": {"name": "paddle_311", "py": sys.executable, "path": str(tdp / "envs" / "paddle_311")}, "ok": True, "python": "3.13.7", "dists": {"six": {"ver": "1.17", "requires": []}}, "dup": {}, "conflicts": [], "check_tool": "uv"},
                    {"env": {"name": "via_core_312", "py": sys.executable, "path": str(tdp / "envs" / "via_core_312")}, "ok": True, "python": "3.12.4", "dists": {}, "dup": {}, "conflicts": [], "check_tool": "uv"}]
            nv = naming_check(fake, b)
            rp = rename_plan([{"name": s["env"]["name"], "path": s["env"].get("path", ""), "py": s["env"]["py"], "python": s.get("python", "")} for s in fake], b, str(tdp / "envs"))
            ps2, sh2 = rename_commands(rp[0]) if rp else ([], [])
            chk("㉘ 命名律 H7:paddle_311 違律 → via_paddle_311(冊 renames);BASE/via_ 豁免;rename 計畫出 uv venv --python 3.13 + uv pip sync + check;退役段候裁註記",
                len(nv) == 1 and nv[0]["env"] == "paddle_311" and nv[0]["suggested"] == "via_paddle_311" and len(rp) == 1 and rp[0]["new"] == "via_paddle_311"
                and any("uv venv" in l and "--python 3.13" in l for l in ps2) and any("uv pip sync" in l for l in ps2) and any(l.startswith("# Rename-Item") for l in ps2) and any("mv " in l for l in sh2))
            plan2 = build_plan(fake, b, ba2, [], [], analyze_via_envs(fake, b), str(tdp / "envs"), skips, nv)
            chk("㉙ 段冊含 RENAME_ENV 委派段(序跑 R2)與共用支援件 REMOVE_BASE(待所有家族 VERIFY);引擎影響索引純函式可判",
                any(st["kind"] == "RENAME_ENV" and st["env"] == "paddle_311" and st["cls"] == "SEQUENTIAL" for st in plan2["stages"])
                and any(st["kind"] == "REMOVE_BASE" and st.get("family") == "(共用支援件)" and st["pins"] == ["shared-util"] for st in plan2["stages"])
                and engine_impact(["pymupdf"], {"VRN_ENG001_X": {"fitz", "json"}, "VDF_ENG002_Y": {"pandas"}})["names"] == ["VRN_ENG001_X"])
            ap3 = apply_plan(plan2, [base_scan], approve=True, approve_remove=False, only_kinds={"NO_SUCH_KIND"})
            chk("㉚ 批383 --only-kind 段類過濾:授權但段類皆未選=全段 SKIP 零執行(REPAIR_BASE 單跑之閘同律)",
                ap3["ran"] == 0 and ap3["ok"] == 0 and ap3["fail"] == 0
                and all(st["result"]["state"] == "SKIP" for st in plan2["stages"])
                and any(st["result"]["note"] == "--only-kind 未選" for st in plan2["stages"]))
            b_prot = json.loads(json.dumps(b))
            b_prot.setdefault("env_layout", {})["protected_envs"] = ["paddle_311"]
            chk("㉛ 批385 旗標白名單(未知 --x 誠實停;已知/數值放行)+命名律豁免受保護境與冊 exempt",
                unknown_flags(["apply", "--approve", "--only-kind", "REPAIR_BASE", "--workers", "8"]) == []
                and unknown_flags(["apply", "--approve", "--onlykind", "--zzz"]) == ["--onlykind", "--zzz"]
                and naming_check(fake, b_prot) == [] and len(naming_check(fake, b)) == 1)
        except Exception as exc:
            checks.append(("例外", False))
            print("  [FAIL] 例外:", type(exc).__name__, exc)
            traceback.print_exc()
        finally:
            LOG_PATH, OUT, LOCK_DIR, LKGC_LOCK_DIR, LKGC_LATEST, RUN_LATEST, MATRIX_LATEST = keep
    # 批495 ㉜㉝㉞:工具冊導入(假境根=本解譯器 symlink;真境零觸碰;同意閘不代設)
    try:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            OUT = tdp / "out"
            er = tdp / "envs"
            fe = er / "via_vrn_312"
            (fe / "bin").mkdir(parents=True)
            os.symlink(sys.executable, fe / "bin" / "python")
            (fe / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
            roster = {"_src": "自測冊", "envs": {
                "via_vrn_312": {"python": "3.12", "aliases": [], "tools": [
                    {"pip": "json-x", "imp": "json"},
                    {"pip": "definitely-absent-xyz", "imp": "definitely_absent_xyz_123"},
                    {"pip": "json-broken", "imp": "json", "health": ["attr:__nope__"]},
                    {"pip": "sys-old", "imp": "sys", "health": ["version_min:99.0"]},
                    {"pip": "easyocr", "imp": "os", "health": ["easyocr_models"], "note": "模型首跑下載"},
                    {"pip": "opt-x", "imp": "nope_optional_x", "optional": True}]},
                "via_missing_x": {"python": "3.12", "aliases": [], "tools": [{"pip": "numpy", "imp": "numpy"}]}}}
            hs = os.environ.get("HOME"); os.environ["HOME"] = str(tdp)
            cs = os.environ.pop("VIA_NET_CONSENT", None)
            try:
                envs = discover_envs({"managed_prefixes": ["via_"]}, [], str(er), None, None)
                plan = tools_plan(roster, envs, str(er))
                st = {t["pip"]: t.get("state") for e in plan["envs"] for t in e["tools"]}
                kinds = [(x["kind"], x["env"]) for x in plan["stages"]]
                chk("㉜ 工具冊探針:OK/ABSENT/BROKEN(attr 缺=半拆)/CONFLICT(版本低)/NEEDS_MODELS(外部)/境不在=ENV_ABSENT;optional 缺不排安裝;段序 REPAIR→INSTALL→VERIFY,缺境 ENSURE_ENV→INSTALL",
                    st.get("json-x") == "OK" and st.get("definitely-absent-xyz") == "ABSENT" and st.get("json-broken") == "BROKEN"
                    and st.get("sys-old") == "CONFLICT" and st.get("easyocr") == "NEEDS_MODELS" and st.get("opt-x") == "ABSENT" and st.get("numpy") == "ENV_ABSENT"
                    and kinds == [("REPAIR_TOOLS", "via_vrn_312"), ("INSTALL_TOOLS", "via_vrn_312"), ("VERIFY_TOOLS", "via_vrn_312"), ("ENSURE_ENV", "via_missing_x"), ("INSTALL_TOOLS", "via_missing_x")]
                    and [x["pkgs"] for x in plan["stages"] if x["kind"] == "INSTALL_TOOLS"][0] == ["definitely-absent-xyz", "sys-old"]
                    and len(plan["external"]) == 1 and plan["external"][0]["state"] == "NEEDS_MODELS")
                s0 = tools_apply(json.loads(json.dumps(plan)), False)
                p1 = json.loads(json.dumps(plan)); s1 = tools_apply(p1, True)
                chk("㉝ 授權閉環:apply 未 --approve=全 SKIP 零動作;--approve 但同意閘未開=BLOCKED_CONSENT 零動作(不代設 VIA_NET_CONSENT)",
                    s0["ran"] == 0 and s1["ran"] == 0 and p1["state"] == "BLOCKED_CONSENT" and all(x["result"]["state"] == "SKIP" for x in p1["stages"])
                    and os.environ.get("VIA_NET_CONSENT") is None)
                ps = tools_ps(plan)
                chk("㉞ 一貼即用 .ps1:半拆件 --force-reinstall、缺件 uv pip install --python <境>、缺境 uv venv、外部件只印令(#)",
                    "--force-reinstall json-broken" in ps and "definitely-absent-xyz sys-old" in ps and "uv venv" in ps and "# [via_vrn_312] easyocr NEEDS_MODELS" in ps)
            finally:
                if hs is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = hs
                if cs is not None:
                    os.environ["VIA_NET_CONSENT"] = cs
    except Exception as exc:
        checks.append(("批495 例外", False))
        print("  [FAIL] 批495 例外:", type(exc).__name__, exc)
        traceback.print_exc()
    finally:
        LOG_PATH, OUT, LOCK_DIR, LKGC_LOCK_DIR, LKGC_LATEST, RUN_LATEST, MATRIX_LATEST = keep
    # 批497 ㉟㊱:全冊聯集零遺漏 + 風險分級/隔離境路由 + 樞紐矩陣
    try:
        b = load_baseline()
        u = union_roster(b, load_roster())
        alltools = [t for v in u["envs"].values() for t in v["tools"]]
        srcs = {t.get("source") for t in alltools}
        risks = {t.get("risk") for t in alltools}
        iso = [e for e in u["envs"] if e.endswith("_H") or e.endswith("_M")]
        acc_n = u["stats"]["accel"]
        if acc_n:
            chk("㉟ 全冊聯集零遺漏:冊 + Celeritas _LIB_MAP(≥80 件經 MDL142)+ AegisNexus 相依(requests…)皆入冊;HIGH/MEDIUM 件路由到 Baseline 家族的 _H/_M 隔離境;numpy 等樞紐件標 SPECIAL",
                acc_n >= 80 and {"sheet", "accelerator", "network"} <= srcs and any(_canon(t["pip"]) == "requests" for t in alltools)
                and "HIGH" in risks and "SPECIAL" in risks and any(e.endswith("_H") for e in iso)
                and all(t.get("special") for t in alltools if _canon(t["pip"]) == "numpy"))
        else:
            chk("㉟ 全冊聯集(Celeritas 缺席=SKIP 誠實)", True)
        fake_plan = {"envs": [{"name": "via_vdf_312", "tools": [{"pip": "numpy", "special": True, "ver": "2.1.0", "state": "OK", "risk": "SPECIAL"}]},
                              {"name": "via_paddle_311", "tools": [{"pip": "numpy", "special": True, "ver": "1.26.4", "state": "OK", "risk": "SPECIAL"}]}],
                     "stages": [], "external": [], "counts": {}}
        hubs = set(u.get("hubs") or [])
        mat: dict = {}
        for e in fake_plan["envs"]:
            for t in e["tools"]:
                if t.get("special") or _canon(t["pip"]) in hubs:
                    mat.setdefault(_canon(t["pip"]), {})[e["name"]] = t.get("ver")
        chk("㊱ 樞紐矩陣:同一樞紐件跨獨立境不同版本只作 INFO(numpy via_vdf_312=2.1.0 · via_paddle_311=1.26.4),不列衝突不強制對齊",
            mat.get("numpy") == {"via_vdf_312": "2.1.0", "via_paddle_311": "1.26.4"} and "numpy" in hubs)
        if acc_n:
            with tempfile.TemporaryDirectory() as td7:
                er7 = Path(td7) / "envs"
                er7.mkdir()
                (er7 / "via_core" / "bin").mkdir(parents=True)
                os.symlink(sys.executable, er7 / "via_core" / "bin" / "python")
                (er7 / "via_core" / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
                envs7 = discover_envs({"managed_prefixes": ["via_"]}, [], str(er7), None, None)   # via_core 在(白名單境)
                p7 = tools_plan(u, envs7, str(er7))
                wl7 = core_whitelist()
                core7 = [e for e in p7["envs"] if e["name"] == "via_core"]
                core_tools7 = [t for e in core7 for t in e["tools"]]
                bad_stage = [st for st in p7["stages"] if st["env"] == "via_core" and st["kind"] in ("INSTALL_TOOLS", "REPAIR_TOOLS")
                             and any(_canon(pk) not in wl7 for pk in (st.get("pkgs") or []))]
                held7 = {x["tool"] for x in p7.get("whitelist_hold", [])}
                chk("㊲ via_core 白名單律:無家族且非白名單的加速器通用件永不排進 via_core(列 [未路由]);白名單件(numpy/pandas/requests…)照白名單制進 via_core;非白名單缺件(如 joblib)只留置 WHITELIST_HOLD;其餘缺境照排 ENSURE_ENV",
                    len(p7.get("unrouted", [])) >= 40 and not bad_stage and bool(core7)
                    and all((t["state"] == "WHITELIST_HOLD" and t["pip"] in held7) for t in core_tools7 if _canon(t["pip"]) not in wl7 and t.get("state") != "OK")
                    and all(_canon(t["pip"]) in wl7 for t in core_tools7 if t.get("source") == "accelerator")
                    and any(_canon(t["pip"]) == "numpy" for t in core_tools7) and not any(x in ("numpy", "pandas", "requests") for x in p7.get("unrouted", []))
                    and any(st["kind"] == "ENSURE_ENV" and st["env"].endswith("_H") for st in p7["stages"]))
                # ㊴ 批500 隔離律:HIGH 家族只認同名獨立境——假境根有 via_ml(alt)沒有 via_iso_ml_cuda_H → 仍 ENSURE_ENV 獨立境,不把 jax/tensorflow 排進 via_ml
                with tempfile.TemporaryDirectory() as td8:
                    er8 = Path(td8) / "envs"
                    (er8 / "via_ml" / "bin").mkdir(parents=True)
                    os.symlink(sys.executable, er8 / "via_ml" / "bin" / "python")
                    (er8 / "via_ml" / "pyvenv.cfg").write_text("home = x\n", encoding="utf-8")
                    envs8 = discover_envs({"managed_prefixes": ["via_"]}, [], str(er8), None, None)
                    p8 = tools_plan(u, envs8, str(er8), only_env="via_iso_ml_cuda_H")
                    rec8 = [e for e in p8["envs"] if e["name"] == "via_iso_ml_cuda_H"]
                    chk("㊴ 隔離律:HIGH 家族 via_iso_ml_cuda_H 不借 alt 境 via_ml(操作員實錄要把 jax+tensorflow 裝進既有 torch 境)→ ENV_ABSENT + ENSURE_ENV 獨立境;MEDIUM 家族仍可用 alt",
                        bool(rec8) and rec8[0]["state"] == "ENV_ABSENT" and rec8[0]["found"] is None
                        and any(st["kind"] == "ENSURE_ENV" and st["env"] == "via_iso_ml_cuda_H" for st in p8["stages"])
                        and not any(st["env"] == "via_ml" for st in p8["stages"]))
                chk("㊳ 白名單單一來源:core_whitelist() 讀 VIA_EnvManager def_PARAM_VIA_CORE_WHITELIST(≥14 件,含 requests/numpy/duckdb;joblib 不在)",
                    len(wl7) >= 14 and {"requests", "numpy", "duckdb"} <= wl7 and "joblib" not in wl7)
        else:
            chk("㊲ via_core 白名單律(Celeritas 缺席=SKIP 誠實)", True)
    except Exception as exc:
        checks.append(("批497 例外", False))
        print("  [FAIL] 批497 例外:", type(exc).__name__, exc)
        traceback.print_exc()
    n_ok = sum(1 for _, c in checks if c)
    # ㊵ 批506 L19 安裝核可律:RunGate 缺=BLOCKED_UNITEST 零動作;非 GREEN=擋;GREEN 且新鮮=放行(tools_apply 與 apply_plan 同律)
    try:
        import tempfile as _tf40
        with _tf40.TemporaryDirectory() as td40:
            _sv40 = os.environ.get("VIA_RUNGATE_LATEST"); _cs40 = os.environ.get("VIA_NET_CONSENT")
            os.environ["VIA_NET_CONSENT"] = "YES"
            try:
                os.environ["VIA_RUNGATE_LATEST"] = str(Path(td40) / "none.json")
                p40 = {"stages": [{"id": "T01", "kind": "INSTALL_TOOLS", "env": "x", "pkgs": ["nothing"], "deps": [], "result": {"state": "PENDING"}}], "state": "PLAN"}
                r40 = tools_apply(p40, True)
                q40 = {"stages": [{"id": "S01", "kind": "INSTALL", "env": "x", "deps": [], "result": {"state": "PENDING"}}], "order": ["S01"], "state": "PLAN"}
                a40 = apply_plan(q40, [], True, False, baseline={}, skips={})
                Path(td40, "red.json").write_text(json.dumps({"verdict": "RED", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}), encoding="utf-8")
                os.environ["VIA_RUNGATE_LATEST"] = str(Path(td40) / "red.json")
                r41 = tools_apply({"stages": [dict(p40["stages"][0])], "state": "PLAN"}, True)
                Path(td40, "g.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}), encoding="utf-8")
                os.environ["VIA_RUNGATE_LATEST"] = str(Path(td40) / "g.json")
                ok42, _ = unitest_gate()
            finally:
                if _sv40 is None:
                    os.environ.pop("VIA_RUNGATE_LATEST", None)
                else:
                    os.environ["VIA_RUNGATE_LATEST"] = _sv40
                if _cs40 is None:
                    os.environ.pop("VIA_NET_CONSENT", None)
                else:
                    os.environ["VIA_NET_CONSENT"] = _cs40
        chk("㊵ L19 安裝核可律(批506):RunGate 缺→tools_apply/apply_plan 皆 BLOCKED_UNITEST 零動作;判定 RED→擋;GREEN 且 24h 內→放行",
            r40["ran"] == 0 and p40["state"] == "BLOCKED_UNITEST" and q40["state"] == "BLOCKED_UNITEST" and a40["blocked"] == 1 and r41["ran"] == 0 and ok42)
    except Exception as exc:
        checks.append(("㊵ 例外", False)); print("  [FAIL] ㊵ 例外:", type(exc).__name__, exc)
    # ㊶ 批508 L24 環境復原律:_M/_H 不借 alt 境(via_iso_webui_M 的 alt via_vap_312 在位仍 ENV_ABSENT)· 段序 LOW→MEDIUM→HIGH · recover plan 唯讀零動作 · 無同意閘=BLOCKED_CONSENT
    try:
        import tempfile as _tf41
        with _tf41.TemporaryDirectory() as td41:
            _cs41 = os.environ.pop("VIA_NET_CONSENT", None)
            try:
                ro41 = {"_src": "自測冊", "envs": {
                    "via_iso_x_H": {"python": "3.11", "aliases": ["via_ml"], "tools": [{"pip": "torchfake41", "imp": "torchfake41", "risk": "HIGH"}]},
                    "via_iso_webui_M": {"python": "3.12", "aliases": ["via_vap_312"], "tools": [{"pip": "streamlitfake41", "imp": "streamlitfake41", "risk": "MEDIUM"}]},
                    "via_vdf_312": {"python": "3.12", "aliases": ["via_vdf"], "tools": [{"pip": "nosuchpkg41", "imp": "nosuchpkg41"}]},
                    "via_core": {"python": "3.12", "aliases": [], "tools": [{"pip": "pip", "imp": "pip"}]}}}
                ev41 = [{"name": "BASE", "py": sys.executable}, {"name": "via_vap_312", "py": sys.executable}, {"name": "via_ml", "py": sys.executable},
                        {"name": "via_vdf_312", "py": sys.executable}, {"name": "via_core", "py": sys.executable}]
                p41 = tools_plan(ro41, ev41, td41, timeout=60)
                by41 = {e["name"]: e for e in p41["envs"]}
                iso41 = (by41["via_iso_webui_M"]["state"] == "ENV_ABSENT" and by41["via_iso_x_H"]["state"] == "ENV_ABSENT"
                         and by41["via_iso_webui_M"].get("isolation") == "EXCLUSIVE" and by41["via_vdf_312"].get("isolation") == "SHARED"
                         and p41["isolation"]["exclusive"] == ["via_iso_x_H", "via_iso_webui_M"])
                ranks41 = [st.get("rank") for st in p41["stages"]]
                inst41 = [st["env"] for st in p41["stages"] if st["kind"] == "INSTALL_TOOLS"]
                ord41 = (ranks41 == sorted(ranks41) and all("tier" in st for st in p41["stages"]) and inst41 == ["via_vdf_312", "via_iso_webui_M", "via_iso_x_H"]
                         and [st["env"] for st in p41["stages"] if st["kind"] == "ENSURE_ENV"] == ["via_iso_webui_M", "via_iso_x_H"])
                r41a = tools_apply({"stages": [dict(s) for s in p41["stages"]], "state": "PLAN"}, False)
                q41 = {"stages": [dict(s) for s in p41["stages"]], "state": "PLAN"}
                r41b = tools_apply(q41, True)                                   # 同意閘未開 → BLOCKED_CONSENT 零動作
                rec41 = recover_plan(["--env-root", td41])
                ps41 = recover_ps(rec41)
                x41a = recover_execute(rec41, False, False)
                x41b = recover_execute(rec41, True, False)
                rec_ok = (rec41["schema"] == "VIA.EnvGovernance.RECOVER.v1" and rec41["law"] == "L24" and rec41["order"] == ORDER_LAW
                          and rec41["restore"]["mode"].startswith("原本規劃") and rec41["state"] == "PLAN" and "# ═ ① 還原前次" in ps41 and "# ═ ③ 隔離 ═" in ps41
                          and x41a["restore"] is None and x41b["state"] == "BLOCKED_CONSENT" and x41b["restore"] is None and x41b["install"] is None)
            finally:
                if _cs41 is not None:
                    os.environ["VIA_NET_CONSENT"] = _cs41
        chk("㊶ L24 環境復原律(批508):_M/_H 不借 alt 境(有 via_vap_312/via_ml 在位仍 ENV_ABSENT 建同名境)· 段序 LOW→MEDIUM→HIGH · tools_apply 無授權/無同意皆零動作 · recover plan 唯讀(Baseline 模式)· 無同意=BLOCKED_CONSENT",
            iso41 and ord41 and r41a["ran"] == 0 and r41b["ran"] == 0 and q41["state"] == "BLOCKED_CONSENT" and rec_ok)
    except Exception as exc:
        checks.append(("㊶ 例外", False)); print("  [FAIL] ㊶ 例外:", type(exc).__name__, exc)
    # ㊷ 批509 解譯器壞(操作員實錄:via_vdf_312/via_vrn_312 全站 SRE module mismatch;RunGate 卻判「必要庫缺」)→ ENV_BROKEN_INTERP · INTERP_BROKEN · REBUILD_ENV 候裁 · apply 零動作 · ps 印令
    try:
        _rc_sv = globals()["run_cmd"]

        def _rc_fake(argv, timeout=120, cwd=None, input_text=None):
            return {"rc": 1, "out": "", "err": "  File \"<frozen re._compiler>\", line 44\n    assert _sre.MAGIC == MAGIC, \"SRE module mismatch\"\nAssertionError: SRE module mismatch", "s": 0.1}
        globals()["run_cmd"] = _rc_fake
        try:
            ro42 = {"_src": "自測冊", "envs": {"via_vdf_312": {"python": "3.12", "aliases": [], "tools": [{"pip": "duckdb", "imp": "duckdb"}, {"pip": "pandas", "imp": "pandas"}]}}}
            ev42 = [{"name": "BASE", "py": sys.executable}, {"name": "via_vdf_312", "py": sys.executable, "path": str(Path(sys.executable).resolve().parent.parent)}]
            p42 = tools_plan(ro42, ev42, str(Path(sys.executable).resolve().parent), timeout=30)
        finally:
            globals()["run_cmd"] = _rc_sv
        e42 = p42["envs"][0]
        k42 = [s["kind"] for s in p42["stages"]]
        _cs42 = os.environ.get("VIA_NET_CONSENT")
        os.environ["VIA_NET_CONSENT"] = "YES"
        try:
            r42 = tools_apply({"stages": [dict(s) for s in p42["stages"]], "state": "PLAN"}, True, ensure_env=True)
        finally:
            if _cs42 is None:
                os.environ.pop("VIA_NET_CONSENT", None)
            else:
                os.environ["VIA_NET_CONSENT"] = _cs42
        ps42 = tools_ps(p42)
        chk("㊷ 解譯器壞(批509):探針 SRE module mismatch → 境 ENV_BROKEN_INTERP · 件 INTERP_BROKEN(不是 ABSENT)· 段只有 REBUILD_ENV(候裁)· apply 零動作(有同意閘亦不跑)· ps 印 Remove-Item/uv venv 令(註解,不自跑)",
            e42["state"] == "ENV_BROKEN_INTERP" and all(t["state"] == "INTERP_BROKEN" for t in e42["tools"]) and k42 == ["REBUILD_ENV"]
            and p42.get("broken_interp") == ["via_vdf_312"] and r42["ran"] == 0 and "# Remove-Item" in ps42 and "uv venv" in ps42 and _interp_broken("AssertionError: SRE module mismatch") and not _interp_broken("ModuleNotFoundError: No module named 'duckdb'"))
    except Exception as exc:
        checks.append(("㊷ 例外", False)); print("  [FAIL] ㊷ 例外:", type(exc).__name__, exc)
    n_ok = sum(1 for _, c in checks if c)          # 批506:㊵ 在原 n_ok 之後加入,重算(批508 ㊶/批509 ㊷ 同)
    print(f"  [計] {n_ok}/{len(checks)} 檢 OK")
    return 0 if n_ok == len(checks) else 1


# 批385:旗標白名單(工作站實錄:舊版 MDL135 不識 --only-kind 卻靜默照跑全段=版本落差風險)→ 未知旗標=誠實停(fail-closed)
# ══════════════════════════════════════════════
# 批495:工具冊導入(tools 動詞)——逐境探針 → 修復/安裝/外部/驗證;plan 唯讀,--apply --approve 才裝
# ══════════════════════════════════════════════
ROSTER_GLOB = "VIA_ToolRoster_SSOT_v*.json"
TOOL_PROBE_SRC = r"""
import json, sys, importlib, os
spec = json.loads(sys.argv[1]); out = {}
def _t(v):
    xs = "".join(ch if (ch.isdigit() or ch == ".") else " " for ch in str(v or "")).split()
    xs = (xs[0] if xs else "0").split(".")
    return tuple(int(x) for x in xs[:3] if x.isdigit()) or (0,)
for t in spec:
    imp = t["imp"]; key = t.get("key") or imp; rec = {"state": "OK", "why": "", "ver": "", "file": ""}
    try:
        m = importlib.import_module(imp)
        rec["ver"] = str(getattr(m, "__version__", "") or "")
        rec["file"] = str(getattr(m, "__file__", "") or "")
        for h in t.get("health", []):
            if h.startswith("attr:"):
                a = h.split(":", 1)[1]
                if not hasattr(m, a):
                    rec.update(state="BROKEN", why="import 得到但缺 " + a + "(半拆/命名空間包;file=" + (rec["file"] or "None") + ")"); break
            elif h.startswith("version_min:"):
                need = h.split(":", 1)[1]
                if _t(rec["ver"]) < _t(need):
                    rec.update(state="CONFLICT", why="版本 " + (rec["ver"] or "?") + " < " + need); break
            elif h.startswith("tesseract_langs:"):
                lang = h.split(":", 1)[1]
                try:
                    langs = list(m.get_languages(config=""))
                    if lang not in langs:
                        rec.update(state="EXTERNAL", why="tesseract 語言包缺 " + lang + "(有:" + ",".join(langs[:6]) + ")"); break
                except Exception as exc:
                    rec.update(state="EXTERNAL", why="tesseract 本體不可呼叫 " + type(exc).__name__ + ":" + str(exc)[:60]); break
            elif h == "easyocr_models":
                d = os.path.join(os.path.expanduser("~"), ".EasyOCR", "model")
                if not (os.path.isdir(d) and any(True for _ in os.scandir(d))):
                    rec.update(state="NEEDS_MODELS", why="~/.EasyOCR/model 無模型(首跑觸網下載;同意閘)"); break
    except ModuleNotFoundError as exc:
        rec.update(state="ABSENT", why=str(exc)[:80])
    except Exception as exc:
        rec.update(state="BROKEN", why=type(exc).__name__ + ":" + str(exc)[:100])
    out[key] = rec
print("@@TOOLS@@" + json.dumps(out))
"""


def load_roster(path: str | None = None) -> dict:
    p = Path(path) if path else _newest(ROSTER_GLOB, REG)
    if not p or not Path(p).exists():
        return {"_src": "缺(VIA_ToolRoster_SSOT_v*.json)", "envs": {}}
    j = json.loads(Path(p).read_text(encoding="utf-8"))
    j["_src"] = Path(p).name
    return j


def _canon(s: str) -> str:
    return re.sub(r"[-_.]+", "-", str(s or "")).lower()


def _mdl142():
    try:
        p = _newest("CGC_MDL142_AccelImport_v*.py", REG)
        if not p:
            return None
        spec = importlib.util.spec_from_file_location("via_accel_import_ro", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = m
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def aegis_deps() -> list:
    """AegisNexus 網路核心的第三方相依(掃 import;VIA 內部件與標準庫剔除;缺=空)。"""
    for rel in ("supportive modules/network/VeritasAegisNexus.py", "supportive modules/VeritasAegisNexus.py"):
        f = VIA / rel
        if f.exists():
            try:
                src = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return []
            std = set(getattr(sys, "stdlib_module_names", set()))
            out = []
            for m in re.finditer(r"^\s*(?:import|from)\s+([A-Za-z_][\w]*)", src, re.M):
                n = m.group(1)
                if n in std or n.startswith(("VIA", "VIS", "Veritas", "accelerator", "__")) or n in out:
                    continue
                out.append(n)
            return out
    return []


def union_roster(baseline: dict, sheet: dict) -> dict:
    """批497 全冊聯集:手寫冊 + Celeritas _LIB_MAP(MDL142)+ AegisNexus 相依,逐件路由與風險分級;零遺漏。"""
    envs: dict = {k: {"python": v.get("python"), "aliases": list(v.get("aliases", [])), "purpose": v.get("purpose", ""),
                      "tools": [dict(t, source="sheet", risk=t.get("risk", "LOW")) for t in v.get("tools", [])]}
                  for k, v in (sheet.get("envs") or {}).items()}
    fams = baseline.get("families") or {}
    layout = baseline.get("env_layout") or {}
    hubs = {_canon(x) for x in (baseline.get("hydra") or {}).get("watch_diverge") or []}
    member_to_fam: dict = {}
    for fk, fv in fams.items():
        for mname in fv.get("members") or []:
            member_to_fam.setdefault(_canon(mname), fk)
    have = {(e, _canon(t["pip"])) for e, v in envs.items() for t in v["tools"]}

    def _ensure_env(name, python, purpose, aliases=None):
        if name not in envs:
            envs[name] = {"python": python or (layout.get(name) or {}).get("python") or "3.12", "aliases": list(aliases or (layout.get(name) or {}).get("aliases") or []),
                          "purpose": purpose, "tools": []}

    def _add(env, tool):
        key = (env, _canon(tool["pip"]))
        if key in have:
            return
        have.add(key)
        envs[env]["tools"].append(tool)
    m142 = _mdl142()
    acc = []
    if m142 is not None:
        try:
            acc = list(m142.roster())
        except Exception:
            acc = []
    stats = {"sheet": sum(len(v["tools"]) for v in envs.values()), "accel": 0, "aegis": 0, "hubs": 0}
    for imp in acc:
        pkg = m142.pip_name(imp) if m142 is not None else imp
        fk = member_to_fam.get(_canon(pkg)) or member_to_fam.get(_canon(imp))
        special = _canon(pkg) in hubs or _canon(imp) in hubs
        if fk:
            fv = fams[fk]
            tgt = fv.get("target_env") or "via_core"
            risk = "HIGH" if tgt.endswith("_H") else "MEDIUM" if tgt.endswith("_M") else "LOW"
            _ensure_env(tgt, fv.get("python"), f"家族 {fk}({fv.get('zh', '')[:24]})", fv.get("alt_envs"))
            _add(tgt, {"pip": pkg, "imp": imp, "role": f"加速器冊 · 家族 {fk}", "source": "accelerator", "family": fk, "risk": ("SPECIAL" if special else risk), "special": special})
        elif _canon(pkg) in core_whitelist():
            # 批500:無家族但在 via_core 白名單上的加速器件(numpy/pandas/pyarrow/duckdb/requests…)照白名單制進 via_core(只增)
            _ensure_env("via_core", None, "共用核心(白名單制)", None)
            _add("via_core", {"pip": pkg, "imp": imp, "role": "加速器冊 · 白名單件", "source": "accelerator", "family": "core_whitelist", "risk": ("SPECIAL" if special else "LOW"), "special": special})
        else:
            _ensure_env(UNROUTED_ENV, "-", "加速器冊無家族者:只列不排(via_core 白名單境不代裝;分發走 via-accel-import)", [])
            _add(UNROUTED_ENV, {"pip": pkg, "imp": imp, "role": "加速器冊 · 通用件", "source": "accelerator", "family": "", "risk": ("SPECIAL" if special else "LOW"), "special": special})
        stats["accel"] += 1
    for imp in aegis_deps():
        pkg = m142.pip_name(imp) if m142 is not None else imp
        for env in ("via_vdf_312", "via_vrn_312", "via_vap_312", "via_core"):
            _ensure_env(env, None, "家族境" if env != "via_core" else "共用核心", None)
            _add(env, {"pip": pkg, "imp": imp, "role": "網路工具 AegisNexus 相依", "source": "network", "family": "network", "risk": "LOW", "special": _canon(pkg) in hubs})
        stats["aegis"] += 1
    for v in envs.values():
        for t in v["tools"]:
            if _canon(t["pip"]) in hubs:
                t["special"] = True
                if t.get("risk") == "LOW":
                    t["risk"] = "SPECIAL"
    stats["hubs"] = sum(1 for v in envs.values() for t in v["tools"] if t.get("special"))
    return {"_src": f"{sheet.get('_src')} ∪ Celeritas _LIB_MAP({len(acc)})∪ AegisNexus 相依({stats['aegis']})", "envs": envs, "hubs": sorted(hubs), "stats": stats}


UNROUTED_ENV = "(未路由:加速器通用件)"
CORE_WHITELIST_FALLBACK = ("pip", "setuptools", "wheel", "packaging", "requests", "httpx", "aiohttp", "orjson", "numpy", "pandas", "pyarrow",
                           "duckdb", "polars", "openpyxl", "xlsxwriter", "plotly", "fastapi", "uvicorn", "rich", "loguru", "pydantic")
CORE_WHITELIST_ENVS = ("via_core", "via_core_312", "venv_core")
# 批508 律 L24 順序安裝律:段依境層級排序;_M/_H 一律同名獨立境(EXCLUSIVE),core/家族境共用(SHARED)
ORDER_LAW = ["RESTORE(前次 LKGC lock;無則 Baseline 原本規劃)", "CORE(via_core 白名單件)", "LOW(家族境 via_vdf/vrn/vap/html/nlp/tools)",
             "MEDIUM(_M 單獨隔離境;不借 alt)", "HIGH(_H 單獨隔離境;不借 alt)", "EXTERNAL(本體/語言包/模型:只印令)", "VERIFY(重探 + uv pip check)"]
_KIND_RANK = {"REBUILD_ENV": 0, "ENSURE_ENV": 0, "REPAIR_TOOLS": 1, "INSTALL_TOOLS": 2, "VERIFY_TOOLS": 3}
INTERP_BROKEN_MARKS = ("sre module mismatch", "_sre.magic", "no module named 'encodings'", "fatal python error")


def _interp_broken(err: str) -> bool:
    """批509:探針輸出帶這些字=解譯器壞(標準庫錯配),不是缺件。"""
    low = (err or "").lower()
    return any(m in low for m in INTERP_BROKEN_MARKS)


def env_tier(name: str) -> tuple:
    """境層級 (tier, rank):UNROUTED 9 · HIGH(_H) 5 · MEDIUM(_M) 4 · CORE 1 · LOW 2。"""
    n = str(name)
    if n == UNROUTED_ENV:
        return ("UNROUTED", 9)
    if n.endswith("_H"):
        return ("HIGH", 5)
    if n.endswith("_M"):
        return ("MEDIUM", 4)
    if n.lower() in CORE_WHITELIST_ENVS:
        return ("CORE", 1)
    return ("LOW", 2)


def core_whitelist() -> set:
    """批498 via_core 白名單(單一來源 VIA_EnvManager def_PARAM_VIA_CORE_WHITELIST;讀不到才用內建備份)。"""
    try:
        cand = sorted((VIA / "supportive modules" / "environment").glob("VIA_EnvManager*.py"))
        if cand:
            txt = cand[-1].read_text(encoding="utf-8", errors="replace")
            m = re.search(r"def_PARAM_VIA_CORE_WHITELIST\s*=\s*\[(.*?)\]", txt, re.S)
            if m:
                got = {_canon(x) for x in re.findall(r"[\"']([A-Za-z0-9_.\-]+)[\"']", m.group(1))}
                if len(got) >= 10:
                    return got
    except Exception:
        pass
    return {_canon(x) for x in CORE_WHITELIST_FALLBACK}


def _find_env(envs: list, names: list) -> dict | None:
    low = {e["name"].lower(): e for e in envs if e["name"] != "BASE"}
    for n in names:
        if str(n).lower() in low:
            return low[str(n).lower()]
    return None


def _tool_installer(py: str) -> list:
    uv = shutil.which("uv")
    return ["uv", "pip", "install", "--python", py] if uv else [py, "-m", "pip", "install"]


def tools_plan(roster: dict, envs: list, env_root: str, timeout: int = 180, only_env: str | None = None) -> dict:
    plan = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "roster": roster.get("_src"), "env_root": env_root,
            "envs": [], "stages": [], "external": [], "counts": {}, "state": "PLAN"}
    n = [0]

    def add(kind, env, **kw):
        n[0] += 1
        st = {"id": f"T{n[0]:02d}", "kind": kind, "env": env, "deps": [], "result": {"state": "PENDING"}}
        st.update(kw)
        st["tier"], st["rank"] = env_tier(env)          # 批508 L24:段帶境層級,尾端依序排
        plan["stages"].append(st)
        return st
    for ename, spec in (roster.get("envs") or {}).items():
        if only_env and ename.lower() != only_env.lower() and only_env.lower() not in [a.lower() for a in spec.get("aliases", [])]:
            continue
        # 批500 隔離律:HIGH 家族(_H)只認同名獨立境,不借 alt 境(操作員實錄:via_iso_ml_cuda_H → via_ml 要裝 jax+tensorflow 進既有 torch 境)
        # 批508 L24 中高風險一律單獨隔離:_M 比照 _H 只認同名獨立境,不借 alt 境(webui≠via_vap_312、ml_boost≠via_ml/via_vdf、http_async≠via_core)
        e = _find_env(envs, [ename] if ename.endswith(("_H", "_M")) else [ename] + list(spec.get("aliases", [])))
        rec = {"name": ename, "found": e["name"] if e else None, "py": (e or {}).get("py"), "tools": [], "state": "OK",
               "tier": env_tier(ename)[0], "isolation": ("EXCLUSIVE" if ename.endswith(("_H", "_M")) else "SHARED")}
        tools = list(spec.get("tools") or [])
        if ename == UNROUTED_ENV:
            # 批498:無家族的加速器通用件永遠只列不排(via_core 白名單境不代裝);分發走 MDL142
            rec["state"] = "UNROUTED"
            rec["tools"] = [dict(t, state="UNROUTED", why="無家族的加速器通用件:不排進白名單境 via_core;分發走 via-accel-import") for t in tools]
            plan.setdefault("unrouted", []).extend(t["pip"] for t in tools)
            plan["envs"].append(rec)
            continue
        if not e or not e.get("py"):
            rec["state"] = "ENV_ABSENT"
            rec["tools"] = [dict(t, state="ENV_ABSENT", why="境不在") for t in tools]
            ens = add("ENSURE_ENV", ename, python=spec.get("python"), env_path=str(Path(env_root) / ename),
                      goal=f"建境 {ename}(uv venv \"{Path(env_root) / ename}\" --python {spec.get('python') or '3.12'})")
            add("INSTALL_TOOLS", ename, py=str(Path(env_root) / ename), pkgs=[t["pip"] for t in tools if not t.get("optional")], deps=[ens["id"]],
                goal=f"建境後裝 {len([t for t in tools if not t.get('optional')])} 件")
            plan["envs"].append(rec)
            continue
        r = run_cmd([e["py"], "-c", TOOL_PROBE_SRC, json.dumps([{"key": t["pip"], "imp": t["imp"], "health": t.get("health", [])} for t in tools])], timeout=timeout)
        probe: dict = {}
        if "@@TOOLS@@" in (r["out"] or ""):
            try:
                probe = json.loads(r["out"].split("@@TOOLS@@", 1)[1].strip().splitlines()[0])
            except Exception as exc:
                rec["probe_err"] = f"探針輸出解析失敗 {type(exc).__name__}"
        else:
            rec["probe_err"] = (r["err"] or r["out"] or f"rc{r['rc']}").strip()[-160:]
            if _interp_broken(rec["probe_err"]):        # 批509:import re 都不行=解譯器壞;補庫是錯藥;重建境=操作員的手
                rec["state"] = "ENV_BROKEN_INTERP"
                rec["tools"] = [dict(t, state="INTERP_BROKEN", why="境解譯器壞(標準庫錯配):" + rec["probe_err"][-90:]) for t in tools]
                ep = str(e.get("path") or Path(e["py"]).resolve().parent.parent)
                add("REBUILD_ENV", ename, py=e["py"], python=spec.get("python"), env_path=ep, destructive=True,
                    goal=f"解譯器壞 → 重建境(候裁=你的手:Remove-Item 境 → uv venv --python {spec.get('python') or '3.12'} → LKGC lock/工具冊重裝;via-envrecover 印令)")
                plan.setdefault("broken_interp", []).append(ename)
                plan["envs"].append(rec)
                continue
        repair, install, ext = [], [], []
        core_env = ename.lower() in CORE_WHITELIST_ENVS or str((e or {}).get("name", "")).lower() in CORE_WHITELIST_ENVS
        wl = core_whitelist() if core_env else set()
        for t in tools:
            pr = probe.get(t["pip"], {"state": "UNKNOWN", "why": rec.get("probe_err", "探針失敗"), "ver": ""})
            tt = dict(t, **pr)
            st = pr.get("state")
            if core_env and st in ("ABSENT", "CONFLICT", "BROKEN") and _canon(t["pip"]).split(">")[0].split("=")[0] not in wl:
                # 批498 白名單律:via_core 只增白名單件;非白名單件缺/壞一律留置 INFO,不排裝不修(白名單由 VIA_EnvManager 決定)
                tt["state"], tt["why"] = "WHITELIST_HOLD", f"白名單境 via_core:{t['pip']} 不在 def_PARAM_VIA_CORE_WHITELIST,不代裝({st});要加=先入 EnvManager 白名單"
                plan.setdefault("whitelist_hold", []).append({"env": ename, "tool": t["pip"], "probe": st})
                rec["tools"].append(tt)
                continue
            rec["tools"].append(tt)
            if st == "BROKEN":
                repair.append(tt)
            elif st in ("ABSENT", "CONFLICT") and not t.get("optional"):
                install.append(tt)
            elif st in ("EXTERNAL", "NEEDS_MODELS"):
                ext.append(tt)
        deps = []
        if repair:
            x = add("REPAIR_TOOLS", ename, py=e["py"], pkgs=[t["pip"] for t in repair], force=True,
                    goal="半拆件 force-reinstall:" + ", ".join(f"{t['pip']}({t['why'][:40]})" for t in repair))
            deps.append(x["id"])
        groups: dict = {}
        for t in install:
            groups.setdefault(t.get("index_url", ""), []).append(t)
        for idx, ts_ in groups.items():
            x = add("INSTALL_TOOLS", ename, py=e["py"], pkgs=[t["pip"] for t in ts_], index_url=idx, deps=list(deps),
                    goal=("缺件/升版:" + ", ".join(f"{t['pip']}[{t['state']}]" for t in ts_)) + (f"(index {idx})" if idx else ""))
            deps.append(x["id"])
        for t in ext:
            plan["external"].append({"env": ename, "tool": t["pip"], "state": t["state"], "why": t.get("why", ""),
                                     "cmd": ((t.get("external") or {}).get("win") or t.get("note") or "")})
        if repair or install:
            add("VERIFY_TOOLS", ename, py=e["py"], deps=list(deps), goal=f"重探 {ename} + uv pip check")
        rec["state"] = "OK" if not (repair or install or ext) else "TODO"
        plan["envs"].append(rec)
    c: dict = {}
    for e in plan["envs"]:
        for t in e["tools"]:
            c[t.get("state", "?")] = c.get(t.get("state", "?"), 0) + 1
    plan["counts"] = c
    # 批497:樞紐件矩陣(境 × 版本)只作 INFO——多環境多版本多 Python 是設計允許,不強制對齊
    hubs = set(roster.get("hubs") or [])
    mat: dict = {}
    for e in plan["envs"]:
        for t in e["tools"]:
            if t.get("special") or _canon(t.get("pip", "")) in hubs:
                mat.setdefault(_canon(t["pip"]).split(">")[0].split("=")[0], {})[e["name"]] = (t.get("ver") or t.get("state") or "?")
    plan["hubs"] = mat
    plan["risk_counts"] = {}
    for e in plan["envs"]:
        for t in e["tools"]:
            r = t.get("risk", "LOW")
            plan["risk_counts"][r] = plan["risk_counts"].get(r, 0) + 1
    # 批508 L24 順序安裝律:CORE→LOW→MEDIUM→HIGH(同境內 建境→修復→安裝→驗證;相依全在同境,序不破)
    plan["stages"].sort(key=lambda s: s.get("rank", 2))     # 穩定排序:同層級內保留冊序與 建境→修復→安裝→驗證 原序
    plan["order_law"] = ORDER_LAW
    plan["isolation"] = {"exclusive": [e["name"] for e in plan["envs"] if e.get("isolation") == "EXCLUSIVE"],
                         "shared": [e["name"] for e in plan["envs"] if e.get("isolation") == "SHARED"]}
    return plan


def tools_ps(plan: dict) -> str:
    lines = [f"# VIA 工具導入計畫 {plan['ts']} · 冊 {plan.get('roster')} · 境根 {plan.get('env_root')}",
             "# plan 唯讀。要裝:$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve(裝前 freeze 存證;同意閘不代設)",
             "# 批508 L24 順序安裝律:" + " → ".join(x.split("(")[0] for x in ORDER_LAW) + ";_M/_H 一律同名獨立境不借 alt;安裝出問題先 via-envrecover(還原前次)"]
    for st in plan["stages"]:
        if st["kind"] == "ENSURE_ENV":
            lines.append(f"uv venv \"{st['env_path']}\" --python {st.get('python') or '3.12'}    # {st['id']} {st['env']}")
        elif st["kind"] in ("REPAIR_TOOLS", "INSTALL_TOOLS"):
            py = st.get("py") or ""
            if st["env"] and not py.lower().endswith(("python.exe", "python", "python3")):
                py = str(Path(py) / "Scripts" / "python.exe")
            cmd = f'uv pip install --python "{py}"' + (" --force-reinstall" if st.get("force") else "") + (f" --index-url {st['index_url']}" if st.get("index_url") else "") + " " + " ".join(st.get("pkgs") or [])
            lines.append(cmd + f"    # {st['id']} {st['kind']} {st['env']}")
        elif st["kind"] == "REBUILD_ENV":
            ep = st.get("env_path") or ""
            lines += [f"# ── {st['id']} {st['env']} 解譯器壞(標準庫錯配)→ 重建境(候裁=你的手;三行都不自跑)──",
                      f'# Remove-Item -Recurse -Force "{ep}"', f'# uv venv "{ep}" --python {st.get("python") or "3.12"}',
                      f'# uv pip install --python "{ep}\\Scripts\\python.exe" -r <LKGC lock;無則 via-envtools -Apply -Approve 重裝>']
        elif st["kind"] == "VERIFY_TOOLS":
            lines.append(f'uv pip check --python "{st.get("py")}"    # {st["id"]} {st["env"]}')
    if plan["external"]:
        lines.append("# ── 外部本體/語言包/模型(你的手;不代裝)──")
        for x in plan["external"]:
            lines.append(f"# [{x['env']}] {x['tool']} {x['state']}:{x['why'][:80]}" + (f"\n#   → {x['cmd']}" if x.get("cmd") else ""))
    return "\n".join(lines) + "\n"


UNITEST_MAX_AGE_H = 24.0


def unitest_gate() -> tuple:
    """批506 律 L19 安裝核可:環境統一測式(RunGate 家族境 python × 套件探針 × 引擎自測)判定 GREEN 且 24h 內才可核可安裝。
    讀 env VIA_RUNGATE_LATEST(自測用)或 VIA_Reports/rungate/RUNGATE_latest.json;缺/過期/非 GREEN=(False, why)。"""
    p = Path(os.environ.get("VIA_RUNGATE_LATEST") or (VIA / "VIA_Reports" / "rungate" / "RUNGATE_latest.json"))
    try:
        j = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return False, f"RunGate 報告缺({p.name});先跑 via-rungate"
    age = None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            age = (datetime.now() - datetime.strptime(str(j.get("ts", ""))[:19], fmt)).total_seconds() / 3600.0
            break
        except Exception:
            pass
    if j.get("verdict") != "GREEN":
        return False, f"RunGate 判定 {j.get('verdict')}(非 GREEN);修綠再裝"
    if age is None or age > UNITEST_MAX_AGE_H:
        return False, f"RunGate 報告過期({age if age is None else round(age, 1)} h > {UNITEST_MAX_AGE_H:.0f} h);重跑 via-rungate"
    return True, f"RunGate GREEN {round(age, 1)} h 前"


def tools_apply(plan: dict, approve: bool, ensure_env: bool = False) -> dict:
    ran, fails = 0, 0
    if not approve:
        for st in plan["stages"]:
            st["result"] = {"state": "SKIP", "note": "未授權(plan 唯讀;tools --apply --approve 才跑)"}
        plan["state"] = "PLAN"
        return {"ran": 0, "fails": 0, "note": "plan 唯讀"}
    if not _consent():
        for st in plan["stages"]:
            st["result"] = {"state": "SKIP", "note": "裝件要上網:VIA_NET_CONSENT 未開(不代設;$env:VIA_NET_CONSENT='YES' 後再跑)"}
        plan["state"] = "BLOCKED_CONSENT"
        return {"ran": 0, "fails": 0, "note": "同意閘未開,零動作"}
    ok_u, why_u = unitest_gate()
    if not ok_u:
        for st in plan["stages"]:
            st["result"] = {"state": "SKIP", "note": f"L19 安裝核可律:{why_u}"}
        plan["state"] = "BLOCKED_UNITEST"
        return {"ran": 0, "fails": 0, "note": f"L19 環境統一測式未核可:{why_u}"}
    done_ids: set = set()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for st in plan["stages"]:
        if any(d not in done_ids for d in st.get("deps", [])):
            st["result"] = {"state": "SKIP", "note": "前置段未綠"}
            continue
        if st["kind"] == "REBUILD_ENV":                     # 批509:境刪除=操作員的手;印令不自跑(--approve-remove 亦不跑)
            st["result"] = {"state": "SKIP", "note": "破壞段:境重建=操作員的手(印令不自跑;見 TOOLS_PLAN_latest.ps1 / RECOVER_latest.ps1)"}
            continue
        if st["kind"] == "ENSURE_ENV":
            if not ensure_env:
                st["result"] = {"state": "SKIP", "note": "建境走 via-envgov apply --approve(ENSURE_ENV)或印出的 uv venv 令;本動詞只裝工具"}
                continue
            ep = Path(st.get("env_path") or "")                # 批508 recover:隔離境 uv venv 只增(已在=SKIP_EXISTS)
            if str(ep) and ep.exists():
                st["result"] = {"state": "SKIP_EXISTS", "note": "已在(只增不減)"}
                done_ids.add(st["id"])
                continue
            argv = [_UV or "uv", "venv", str(ep)] + (["--python", str(st["python"])] if st.get("python") else [])
            r = run_cmd(argv, timeout=600)
            ran += 1
            st["result"] = {"state": "OK" if r["rc"] == 0 else "FAIL", "cmd": " ".join(argv), "rc": r["rc"], "tail": (r["out"] + r["err"])[-300:], "s": r["s"]}
            log_event("TOOLS_ENSURE_ENV", st["env"], "", st["result"]["state"], st["result"]["tail"][-160:])
            if r["rc"] == 0:
                done_ids.add(st["id"])
            else:
                fails += 1
            continue
        py = st.get("py")
        if py and Path(py).is_dir():                         # 批508:ENSURE_ENV 後段的 py 是境根 → 解析成解譯器
            py = str(env_python(Path(py)) or py)
        if st["kind"] in ("REPAIR_TOOLS", "INSTALL_TOOLS"):
            try:
                OUT.mkdir(parents=True, exist_ok=True)
                fr = run_cmd((["uv", "pip", "freeze", "--python", py] if shutil.which("uv") else [py, "-m", "pip", "freeze"]), timeout=120)
                (OUT / f"tools_before_{st['env']}_{ts}.txt").write_text(fr.get("out") or "", encoding="utf-8")
            except Exception:
                pass
            cmd = _tool_installer(py) + (["--force-reinstall"] if st.get("force") else []) + (["--index-url", st["index_url"]] if st.get("index_url") else []) + list(st.get("pkgs") or [])
            r = run_cmd(cmd, timeout=1800)
            ran += 1
            ok = r["rc"] == 0
            st["result"] = {"state": "OK" if ok else "FAIL", "cmd": " ".join(cmd), "rc": r["rc"], "tail": (r["out"] + r["err"])[-400:], "s": r["s"]}
            log_event("TOOLS_" + st["kind"], st["env"], " ".join(st.get("pkgs") or []), st["result"]["state"], st["result"]["tail"][-160:])
            if ok:
                done_ids.add(st["id"])
            else:
                fails += 1
        elif st["kind"] == "VERIFY_TOOLS":
            chk = run_cmd((["uv", "pip", "check", "--python", py] if shutil.which("uv") else [py, "-m", "pip", "check"]), timeout=300)
            st["result"] = {"state": "OK" if chk["rc"] == 0 else "FAIL", "tail": (chk["out"] + chk["err"])[-300:]}
            ran += 1
            if chk["rc"] != 0:
                fails += 1
            else:
                done_ids.add(st["id"])
    plan["state"] = "APPLIED" if not fails else "APPLIED_WITH_FAIL"
    return {"ran": ran, "fails": fails, "note": ""}


def do_tools(rest: list) -> int:
    baseline = load_baseline()
    roster = load_roster(_arg_after(rest, "--roster"))
    if "--sheet-only" not in rest:
        roster = union_roster(baseline, roster)          # 批497:預設全冊聯集,零遺漏
    roots = [r for r in (_arg_after(rest, "--roots") or "").split(os.pathsep) if r]
    env_root = _arg_after(rest, "--env-root")
    envs = discover_envs(baseline, roots, env_root, None, None)
    er = env_root or next((str(r) for r in discover_roots(roots, None) if r.is_dir()), str(Path.home() / "envs"))
    print(f"=== 工具冊導入 MDL135 v{VERSION}(批{BATCH})· 冊 {roster.get('_src')} · 境 {len(envs) - 1} 個(根 {er})· {'apply' if '--apply' in rest else 'plan(唯讀)'} ===")
    plan = tools_plan(roster, envs, er, only_env=_arg_after(rest, "--tool-env"))
    for e in plan["envs"]:
        c: dict = {}
        for t in e["tools"]:
            c[t.get("state")] = c.get(t.get("state"), 0) + 1
        print(f"  [境] {e['name']:16s} {('→ ' + str(e['found'])) if e['found'] else '缺(ENV_ABSENT)':24s} " + " · ".join(f"{k} {v}" for k, v in sorted(c.items(), key=lambda kv: str(kv[0])))
              + (f" · 探針:{e['probe_err']}" if e.get("probe_err") else ""))
        for t in e["tools"]:
            if t.get("state") != "OK":
                print(f"        {t.get('state', '?'):12s} {t['pip']:28s} {t.get('why', '')[:90]}")
    for st in plan["stages"]:
        print(f"  [{st['id']}] {st['kind']:13s} {st['env']:16s} {st.get('goal', '')[:110]}")
    for x in plan["external"]:
        print(f"  [外部] {x['env']} · {x['tool']} · {x['state']} · {x['why'][:70]}" + (f" → {x['cmd'][:90]}" if x.get("cmd") else ""))
    if plan.get("broken_interp"):
        print(f"  [解譯器壞] {plan['broken_interp']}:探針連 import re 都不行=標準庫錯配(不是缺件;不補庫);重建境=你的手(印令在 .ps1);病因看 via-rungate")
    if plan.get("unrouted"):
        print(f"  [未路由] {len(plan['unrouted'])} 件加速器通用件:不排進白名單境 via_core;分發走 via-accel-import(MDL142)· 例:{', '.join(plan['unrouted'][:6])}…")
    if plan.get("whitelist_hold"):
        print(f"  [白名單留置] via_core {len(plan['whitelist_hold'])} 件非白名單缺/壞件只列不裝:" + ", ".join(f"{x['tool']}({x['probe']})" for x in plan["whitelist_hold"][:8]) + " · 白名單=VIA_EnvManager def_PARAM_VIA_CORE_WHITELIST")
    for hub, byenv in sorted((plan.get("hubs") or {}).items()):
        print(f"  [樞紐] {hub:14s} " + " · ".join(f"{e}={v}" for e, v in sorted(byenv.items())) + "  (多境多版本=允許;同境內多版才是病)")
    if plan.get("risk_counts"):
        print("  [風險] " + " · ".join(f"{k} {v}" for k, v in sorted(plan["risk_counts"].items())) + f" · 來源 {roster.get('_src')}")
    summ = tools_apply(plan, "--approve" in rest) if "--apply" in rest else tools_apply(plan, False)
    if "--apply" in rest:
        for st in plan["stages"]:
            print(f"  [{st['id']}] {st['result'].get('state'):6s} {st['kind']} {st['env']} · {str(st['result'].get('note') or st['result'].get('tail') or '')[-120:]}")
        if summ["note"]:
            print(f"  [apply] {summ['note']}")
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "TOOLS_PLAN_latest.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        (OUT / "TOOLS_PLAN_latest.ps1").write_text(tools_ps(plan), encoding="utf-8")
        print(f"[工具冊] {plan['counts']} · 段 {len(plan['stages'])} · 外部 {len(plan['external'])} · 存證 {OUT / 'TOOLS_PLAN_latest.json'} + .ps1(一貼即用)")
    except Exception as exc:
        print(f"[工具冊] 存證失敗 {type(exc).__name__}:{str(exc)[:60]}")
    if plan["state"] == "APPLIED_WITH_FAIL":
        return 1
    return 0 if all(e["state"] == "OK" for e in plan["envs"]) else 2


KNOWN_FLAGS = {"--offline", "--online", "--quiet", "--workers", "--task-timeout", "--rounds", "--roots", "--env-root", "--base-python", "--env",
               "--apply", "--roster", "--tool-env", "--sheet-only",
               "--approve", "--approve-remove", "--only", "--only-kind", "--open", "--no-open", "--install-plan", "--to", "--baseline", "--execute", "--from",
               "--limit", "--json", "--selftest", "--help", "-h"}


def unknown_flags(args: list) -> list:
    return [a for a in args if a.startswith("-") and a not in KNOWN_FLAGS and not a.lstrip("-").replace(".", "").isdigit()]


def do_conflicts(args: list[str]) -> int:
    """批385:印各境衝突明細(自 RUN_latest.json;零重掃);--env X 只看一境;BASE 預設只印計數(--env BASE 全印);--limit N 每境上限"""
    if not RUN_LATEST.exists():
        print("[conflicts] 無 RUN_latest.json;先 via-envgov(唯讀全景)")
        return 2
    run = json.loads(RUN_LATEST.read_text(encoding="utf-8"))
    only = _arg_after(args, "--env")
    limit = int(_arg_after(args, "--limit") or 25)
    print(f"=== 衝突明細 · {run.get('ts', '')[:19]} · 裁決 {run.get('verdict')} · 來源 {RUN_LATEST.name}(零重掃)===")
    shown = 0
    for sc in run.get("panorama", []):
        name = sc["env"]["name"]
        c = sc.get("conflicts") or []
        if only and name.lower() != only.lower():
            continue
        if not c:
            if only:
                print(f"  [OK ] {name} 零衝突(python {sc.get('python')};{sc.get('check_tool')})")
            continue
        if name == "BASE" and not only:
            print(f"  [RED] BASE 衝突 {len(c)}(base 家族拉出候裁;全印:via-envgov conflicts --env BASE)")
            continue
        shown += 1
        py = sc["env"].get("py") or ""
        print(f"  [RED] {name} 衝突 {len(c)}(python {sc.get('python')};{sc.get('check_tool')};{py})")
        fixes = []
        for r in c[:limit]:
            kind, req, rv = r.get("kind", "?"), r.get("requirer", "?"), r.get("requirer_ver", "")
            need, spec, inst = r.get("required", ""), r.get("spec", ""), r.get("installed", "")
            if kind == "BROKEN":
                print(f"     BROKEN    {req}{(' ' + rv) if rv else ''}:{str(r.get('detail', r.get('line', '')))[:110]}")
                fixes.append(f'"{py}" -m pip install --force-reinstall --no-deps {req}')
            else:
                print(f"     {kind:<9} {req}{(' ' + rv) if rv else ''} 要求 {need}{spec}" + (f",裝的是 {inst}" if inst else ",未裝"))
                fixes.append(f'"{py}" -m pip install "{need}{spec}"' if kind == "MISSING" else f'"{py}" -m pip install "{need}{spec}"   # MISMATCH:先看家族冊是否鎖版(via-envgov plan 段冊)')
        if len(c) > limit:
            print(f"     … 其餘 {len(c) - limit} 條(--limit N)")
        for f in dict.fromkeys(fixes):
            print(f"     修法 $ {f}")
        print(f"     或整境重建:via-rebuild --env {name}(MDL050;LKGC lock 可 via-envgov rollback)")
    if shown == 0 and not only:
        print("  [OK ] via_* 境零衝突(BASE 見上計數)")
    return 0


def selftest() -> int:
    """批506:自測期間給一份新鮮 GREEN RunGate(暫存),讓既有的沙盒 apply 檢照跑;㊵ 另驗 L19 三態。"""
    import tempfile
    sv = os.environ.get("VIA_RUNGATE_LATEST")
    with tempfile.TemporaryDirectory() as td:
        g = Path(td) / "RUNGATE_latest.json"
        g.write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(g)
        try:
            return _selftest_body()
        finally:
            if sv is None:
                os.environ.pop("VIA_RUNGATE_LATEST", None)
            else:
                os.environ["VIA_RUNGATE_LATEST"] = sv


def main() -> int:
    args = sys.argv[1:]
    _ARGV_ALL[:] = args
    if "--selftest" in args:
        print(f"=== MDL135 EnvGovernance v{VERSION} 自測(零網路零環境依賴)===")
        return selftest()
    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0
    bad = unknown_flags(args)
    if bad:
        print(f"  [誠實停] 未知旗標 {' '.join(bad)}(本版 MDL135 v{VERSION} 不識;版本落差?先 via-reload 拉齊再試;已知旗標:{' '.join(sorted(KNOWN_FLAGS))})")
        return 2
    verb = next((a for a in args if not a.startswith("-")), "run")
    rest = [a for a in args if a != verb]
    if verb == "conflicts":
        return do_conflicts(rest)
    if verb == "tools":
        return do_tools(rest)
    if verb == "run":
        return do_run(rest, "run")
    if verb in ("panorama", "scan"):
        return do_run(rest, "panorama")
    if verb == "plan":
        return do_run(rest, "plan")
    if verb == "apply":
        if "--approve" not in rest:
            print("  [apply] 需 --approve(授權閉環);未授權=等同 plan(唯讀)")
        return do_run(rest, "apply")
    if verb == "lkgc":
        return do_lkgc(rest)
    if verb == "rollback":
        return do_rollback(rest)
    if verb == "recover":
        return do_recover(rest)
    if verb == "rename":
        return do_rename(rest)
    if verb == "matrix":
        return do_matrix()
    if verb == "digest":
        return do_digest()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
