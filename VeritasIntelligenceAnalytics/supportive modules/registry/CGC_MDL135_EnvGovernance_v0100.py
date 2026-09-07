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
     via-envgov panorama | plan | apply --approve [--approve-remove] [--only S02,S03]
     via-envgov lkgc [snapshot|promote|status]
     via-envgov rollback [--to LKGC_xxx.json | --baseline] [--execute --approve [--approve-remove]]
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
VERSION = "0100"
BATCH = 381
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


def _newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def _arg_after(args: list, flag: str):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return None


def _read_json(path: Path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def _write_json(path: Path, payload) -> None:
    """原子寫(temp+replace):讀者永不見半檔。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    os.replace(tmp, path)


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
                sys.stdout.write("\r" + _bar_line(done_n[0], total, t0, active, spin) + "   ")
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
        sys.stdout.write("\r" + _bar_line(done_n[0], total, t0, set(), 0) + "\n")
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


def closure(dists: dict, roots: set, blocked: set | None = None) -> set:
    """已裝相依閉包(含 extra 相依—已裝即支援件);封鎖家族件永不被閉包收留。"""
    blocked = blocked or set()
    keep, stack = set(), [r for r in roots if r in dists]
    while stack:
        n = stack.pop()
        if n in keep or n in blocked:
            continue
        keep.add(n)
        for raw in dists[n].get("requires", []):
            nm, _spec, _opt = parse_req(raw)
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


def analyze_base(scan: dict, baseline: dict, present_envs: set, skips: dict) -> dict:
    """base 該有冊比對:manifest 缺件 / 相依閉包 / 拉出候選(家族整包)/ 影響評估。"""
    dists = scan.get("dists", {}) or {}
    ms = manifest_sets(baseline)
    fidx = family_index(baseline)
    never = set(baseline.get("base", {}).get("never_in_base_families", []))
    blocked_pkgs = {p for p, f in fidx.items() if f in never}
    manifest_missing = sorted(p for p in (ms["toolchain"] | ms["engine_core"]) if p not in dists and p not in BOOT)
    keep = closure(dists, ms["all"], blocked=blocked_pkgs)
    os_managed = sorted(p for p, i in dists.items() if i.get("layer") == "os" and p not in blocked_pkgs)  # Linux 發行版 dist-packages=OS 管理,不動不列
    extras = sorted(p for p in dists if p not in keep and p not in BOOT and p not in os_managed)
    # routing_order:via_core 白名單優先(政策母版)——白名單件+其私有相依閉包成群改道 via_core,不入家族整包
    wl = core_whitelist()
    wl_roots = sorted(p for p in extras if p in wl)
    wl_members = (closure(dists, set(wl_roots), blocked=blocked_pkgs - set(wl_roots)) - keep - BOOT) if wl_roots else set()
    fam_pool = [p for p in extras if p not in wl_members]
    # 家族整包(根+境內相依,不含閉包件;cv2 家族隨 OCR 家族)
    bundles: dict[str, dict] = {}
    assigned: set = set()
    for fam in sorted({fidx[p] for p in fam_pool if p in fidx}):
        roots = {p for p in fam_pool if fidx.get(p) == fam}
        full = closure(dists, roots)  # 目標境需完整閉包(含 base 留用件之副本)=自足境;LKGC 精神鎖現版
        members = full - keep - BOOT - wl_members
        members = {m for m in members if fidx.get(m) in (fam, None)}  # 他家族件歸他家族(各自拉出)
        tgt, pyv, ex = resolve_target(fam, baseline, present_envs)
        impact = sorted({r for m in members for r in reverse_deps(dists).get(m, set()) if r in keep})
        bundles[fam] = {"family": fam, "blocked": fam in never, "roots": sorted(roots), "members": sorted(members),
                        "install": sorted(full - BOOT), "target": tgt, "python": pyv, "target_exists": ex, "impact_kept": impact,
                        "severity": "RED" if fam in never else "YELLOW"}
        assigned |= members
    unclassified = [p for p in extras if p not in assigned]
    routed_other: dict[str, list] = {}
    for p in unclassified:
        r = route_package(p, baseline, present_envs, skips)
        via = r["via"] if (p in wl_roots or p not in wl_members) else "via_core_whitelist(相依隨行)"
        if p in wl_members and p not in wl_roots:  # 白名單件之私有相依隨行同境
            r = route_package(wl_roots[0], baseline, present_envs, skips) if wl_roots else r
        routed_other.setdefault(r["target"] or "(拒裝)", []).append({"pkg": p, "ver": dists[p]["ver"], "via": via,
                                                                   "note": r.get("note", ""), "exists": r["exists"], "python": r["python"]})
    blocked_present = sorted(p for p in dists if p in blocked_pkgs)
    return {"n_dists": len(dists), "manifest_missing": manifest_missing, "keep_n": len(keep), "extras": extras,
            "bundles": bundles, "routed_other": routed_other, "blocked_present": blocked_present, "os_managed": os_managed,
            "manifest_src": baseline.get("_src", "")}


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
               via_rows: list[dict], env_root: str, skips: dict) -> dict:
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
    elif k in ("DELEGATE_REBUILD", "DELEGATE_SPLIT", "PRUNE"):
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
               only: set | None = None) -> dict:
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
    verified: set = set()
    for i in plan["order"]:
        st = by[i]
        k = st["kind"]
        deps_ok = all(by[d]["result"].get("state") in ("OK", "SKIP_EXISTS") for d in st["deps"] if d in by)
        if k in ("LOCK", "PROMOTE_LKGC", "PRUNE", "DELEGATE_REBUILD", "DELEGATE_SPLIT"):
            st["result"] = {"state": "SKIP", "note": "R3/委派段由 run 收尾或操作員自跑"}
            summary["skipped"] += 1
            continue
        if only and st["id"] not in only:
            st["result"] = {"state": "SKIP", "note": "--only 未選"}
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
    parts.append("<div class='card'><h2>base 家族整包(拉出候選 → 目標境)</h2><table><tr><th style='width:14%'>家族</th><th style='width:8%'>級</th><th style='width:16%'>目標境</th><th>成員(根+境內相依)</th><th style='width:18%'>閉包相依受影響</th></tr>")
    for fam, b in sorted(ba.get("bundles", {}).items()):
        parts.append(f"<tr><td>{_esc(fam)}</td><td>{_lamp(b['severity'])}</td><td>{_esc(b['target'])}{'' if b['target_exists'] else '(待建)'} py{_esc(b.get('python'))}</td><td>{_esc(', '.join(b['members']))}</td><td>{_esc(', '.join(b.get('impact_kept', [])))}</td></tr>")
    if not ba.get("bundles"):
        parts.append("<tr><td colspan=5>base 無封鎖家族/閉包外家族件</td></tr>")
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
    L = [f"=== VIA 環境治理 digest · MDL135 v{VERSION} · {run.get('ts')} · 裁決 {run.get('verdict')} · 模式 {run.get('mode')} ==="]
    for s in scans:
        n = s["env"]["name"]
        st = "BROKEN" if not s.get("ok") else ("REBUILD" if s.get("conflicts") else "OK")
        if n == "BASE":
            st = "RED" if ba.get("blocked_present") else ("YELLOW" if ba.get("extras") or ba.get("manifest_missing") else "GREEN")
        L.append(f"  [{LAMP.get(st, LAMP.get('GREEN' if st == 'OK' else 'RED'))} {st:7s}] {n:22s} py{s.get('python', '?'):8s} 件 {_ndists(s):4d} · 快篩 {s.get('check_tool', '?'):7s} · 衝突 {len(s.get('conflicts', []))}")
    L.append(f"  base 該有冊({ba.get('manifest_src', '?')}):閉包 {ba.get('keep_n', 0)} · 閉包外 {len(ba.get('extras', []))} · manifest 缺 {len(ba.get('manifest_missing', []))} · 封鎖家族件 {len(ba.get('blocked_present', []))}" + (f" · OS 管理不動 {len(ba['os_managed'])}" if ba.get('os_managed') else ""))
    for fam, b in sorted(ba.get("bundles", {}).items())[:6]:
        L.append(f"    拉出 {LAMP[b['severity']]} {fam:16s} → {b['target']}{'' if b['target_exists'] else '(待建)'}:{', '.join(b['members'][:6])}{' …' if len(b['members']) > 6 else ''}")
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
    if run.get("mode") == "offline":
        nxt.append("$env:VIA_NET_CONSENT='YES'; via-envgov plan(上網模擬 uv pip compile 多輪)")
    if not lk.get("eligible"):
        nxt.append("最壞還原:via-envgov rollback(LKGC 有=lock 逐境 sync;無=原本規劃重建)")
    L.append("  下一指令:" + (" | ".join(nxt) if nxt else "無(全綠;LKGC 已晉升)"))
    return L[:25]


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
    ip = ingest_install_plans(baseline, [_arg_after(args, "--install-plan") or ""])
    plan = build_plan(scans, baseline, ba, conflicts, hydra, via_rows, er, skips)
    mirrors = mirror_health(baseline) if not offline else [{"label": l, "url": u, "state": "NOT_RUN", "ms": None, "note": "離線"} for l, u in zip(baseline["mirror_chain"].get("labels", []), baseline["mirror_chain"]["order"])]
    mirror_url = next((m["url"] for m in sorted([m for m in mirrors if m["state"] == "OK"], key=lambda m: m.get("ms") or 9e9)), "")
    if mode in ("run", "plan", "apply"):
        simulate(plan, scans, rounds_n, offline, mirror_url="" if (ROOT / "uv.toml").exists() else mirror_url)
    apply_summary = None
    if mode in ("run", "apply") and approve:
        print("--- apply(授權閉環:GREEN 非破壞段;移除須 --approve-remove)---")
        only_stages = {x.strip().upper() for x in (_arg_after(args, "--only") or "").split(",") if x.strip()} or None
        apply_summary = apply_plan(plan, scans, approve, approve_remove, baseline, skips, only_stages)
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
    verdict = "RED" if (ba.get("blocked_present") or any(c["severity"] == "RED" for c in hard)) else ("YELLOW" if (hard or ba.get("extras") or ba.get("manifest_missing") or any(r["status"] != "OK" for r in via_rows)) else "GREEN")
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
           "base_analysis": ba, "conflicts": conflicts, "hydra": hydra, "via_rows": via_rows, "install_plans": ip, "plan": plan, "mirrors": mirrors,
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


def do_rollback(args: list[str]) -> int:
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
def selftest() -> int:
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
            chk("⑥ OCR 家族整包(paddleocr+paddlex+albumentations+albucore+contrib 同包;RED;目標 paddle_312 待建)",
                ocr and set(ocr["members"]) >= {"paddleocr", "paddlex", "albumentations", "albucore", "opencv-contrib-python"} and ocr["severity"] == "RED" and ocr["target"] == "paddle_312" and not ocr["target_exists"])
            webui = ba["bundles"].get("webui", {})
            chk("⑦ webui 家族(streamlit+altair)整包;fastapi/pydantic → via_core 白名單改道;unknownlib → 黑環境", webui and "altair" in webui["members"]
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
        except Exception as exc:
            checks.append(("例外", False))
            print("  [FAIL] 例外:", type(exc).__name__, exc)
            traceback.print_exc()
        finally:
            LOG_PATH, OUT, LOCK_DIR, LKGC_LOCK_DIR, LKGC_LATEST, RUN_LATEST, MATRIX_LATEST = keep
    n_ok = sum(1 for _, c in checks if c)
    print(f"  [計] {n_ok}/{len(checks)} 檢 OK")
    return 0 if n_ok == len(checks) else 1


def main() -> int:
    args = sys.argv[1:]
    _ARGV_ALL[:] = args
    if "--selftest" in args:
        print(f"=== MDL135 EnvGovernance v{VERSION} 自測(零網路零環境依賴)===")
        return selftest()
    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0
    verb = next((a for a in args if not a.startswith("-")), "run")
    rest = [a for a in args if a != verb]
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
    if verb == "matrix":
        return do_matrix()
    if verb == "digest":
        return do_digest()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
