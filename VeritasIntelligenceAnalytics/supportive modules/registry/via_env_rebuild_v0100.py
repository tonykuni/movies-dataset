#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_env_rebuild_v0100 — 多環境隔離重建計畫引擎(TOOL-032;操作員令 2026-08-12)
===============================================================================
令:與 VIA_EnvManager(政策母版)+ VIA_EngineForge_Config(紅線組態)+ via-deps
(TOOL-031 衝突判定)相互搭配——先檢視 via_core 及 via_* 全環境有無版本衝突,
有則取出風險因子出重建計畫;中高風險與特殊 libs 一律單獨虛擬環境隔離;
numpy 等易衝突件可多版本環境×多 Python 版本;三鏡像全測導入;
先完成安裝計畫、反覆實測無誤才准安裝;BASE 一併最佳化。依既有狀況改善,不從頭開始。
方法(七段):
  ① 環境盤點 — EnvManager 環境根+管理前綴(via_/base/paddle/camelot)+BASE(本解譯器)
  ② 逐環境掃描 — 子行程探針(stdlib)拉全發行版圖譜,via-deps 判定器算衝突
  ③ 風險因子 — 互撞/缺件·cv2 偏錨·高中風險庫在境·via_core 白名單違規·
     BASE 污染(政策:BASE 封鎖 MEDIUM/HIGH)·跨環境 numpy 分歧·混居超標
  ④ 隔離重建計畫 — 依既有件單改善:REBUILD 旁建新環境(零破壞,sandbox_first;
     切換候裁)·WARN 原地修補·高風險隔離編成·numpy×Python 多版本支架·BASE 瘦身
  ⑤ 鏡像測選 — official/tsinghua/aliyun 三源測速取最快(網路;同意閘)
  ⑥ 反覆實測 — 逐段 pip --dry-run × max_rounds 輪(EngineForge 政策),
     末兩輪解析一致且 rc0=穩定 GREEN;失敗 RED;飄移 YELLOW 候裁
  ⑦ 裁決出令 — GREEN 段寫入執行檔(.ps1/.sh)供操作員檢閱後自跑;
     破壞性動作(刪env/移除件)一律候裁清單,絕不入執行檔
紅線:本引擎零安裝零落地零刪改(destructive_delete=false);dry-run/測速屬網路
     行為過同意閘(VIA_NET_CONSENT=YES);執行檔由操作員自跑(或走 via-install)
用法:via-rebuild                  → 全程七段(② 起需在境環境;無網路段誠實 NOT_RUN)
     via-rebuild --offline        → 只 ①~④+⑦(零網路;實測 NOT_RUN)
     via-rebuild --env 名         → 只治理單一環境
     via-rebuild --roots 路徑     → 附加環境根(os.pathsep 分隔;測試/異機用)
     via-rebuild --rounds N       → 覆寫實測輪數(預設從 EngineForge max_rounds)
     via-rebuild --selftest       → 內建 13 檢(零網路零環境依賴)
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SUP = VIA / "supportive modules"
OUT = VIA / "VIA_Reports" / "rebuild_runs"
PYCMD = "py" if os.name == "nt" else "python3"


def _load_by_path(mod_name: str, path: Path):
    try:
        spec = importlib.util.spec_from_file_location(mod_name, str(path))
        if spec is None or spec.loader is None:
            return None
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def _newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


# ── 搭配載入:via-deps 判定器(必備)+ EnvManager 政策母版(graceful)──
_dep_path = _newest("via_dep_super_v0*.py", HERE)
DEP = _load_by_path("via_dep_super_latest", _dep_path) if _dep_path else None
EM = _load_by_path("VIA_EnvManager_policy", SUP / "VIA_EnvManager.py")


def canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _em_set(attr: str, fallback: list) -> set:
    vals = getattr(EM, attr, None) if EM else None
    return {canon(x) for x in (vals if isinstance(vals, list) and vals else fallback)}


# 政策(EnvManager 在則以母版為準;缺則鏡射其值 graceful)
HIGH_RISK = _em_set("def_PARAM_HIGH_RISK_LIBS", [
    "torch", "tensorflow", "paddleocr", "paddlepaddle", "opencv-python", "opencv-contrib-python",
    "onnxruntime", "pyvips", "camelot-py", "tabula-py", "weasyprint", "playwright", "selenium",
    "jax", "xgboost", "lightgbm", "catboost"])
MED_RISK = _em_set("def_PARAM_MEDIUM_RISK_LIBS", [
    "pymupdf", "pdfplumber", "polars", "duckdb", "pyarrow", "plotly", "fastapi", "uvicorn",
    "aiohttp", "httpx", "orjson", "openpyxl", "xlsxwriter"])
CORE_WL = _em_set("def_PARAM_VIA_CORE_WHITELIST", [
    "pip", "setuptools", "wheel", "packaging", "requests", "httpx", "aiohttp", "orjson", "numpy",
    "pandas", "pyarrow", "duckdb", "polars", "openpyxl", "xlsxwriter", "plotly", "fastapi",
    "uvicorn", "rich", "loguru", "pydantic"])
PREFIXES = [str(x).lower() for x in getattr(EM, "def_PARAM_MANAGED_ENV_PREFIXES", None) or
            ["via_", "base", "paddle", "camelot"]]
PURPOSE = {k: [canon(x) for x in v] for k, v in (getattr(EM, "def_PARAM_ENV_PURPOSE_HINTS", None) or {
    "via_core": ["requests", "httpx", "aiohttp", "orjson", "numpy", "pandas", "pyarrow", "duckdb",
                 "polars", "plotly", "openpyxl", "xlsxwriter", "fastapi", "uvicorn"],
    "via_vdf": ["numpy", "pandas", "pyarrow", "duckdb", "polars", "plotly", "openpyxl", "xlsxwriter"],
    "via_vrn": ["pymupdf", "pdfplumber", "numpy", "pandas", "pyarrow"],
    "paddle_311": ["paddleocr", "paddlepaddle", "opencv-python"],
    "camelot_311": ["camelot-py", "tabula-py", "pdfplumber"],
}).items()}
BASE_BLOCK = set(getattr(EM, "def_PARAM_BASE_BLOCK_RISK_LEVELS", None) or ["MEDIUM", "HIGH"])
CV2_FAMILY = {"opencv-python", "opencv-python-headless", "opencv-contrib-python",
              "opencv-contrib-python-headless"}
KEEP_CV2 = "opencv-contrib-python"  # 安裝閘 v0103 裁定之統包錨(順 paddlex/img2table 相依鏈)
WATCH_DIVERGE = ["numpy", "torch", "paddlepaddle", "pandas", "pyarrow"]  # numpy 明令;餘比照
BOOT = {"pip", "setuptools", "wheel"}


def _forge_policy() -> dict:
    """EngineForge 組態:實際組態優先,模板保底;取 policy 紅線(max_rounds 等)。"""
    cands = sorted(SUP.glob("VIA_EngineForge_Config*.json"))
    cands = [c for c in cands if "template" not in c.name.lower()] + \
            [c for c in cands if "template" in c.name.lower()]
    for c in cands:
        try:
            pol = json.loads(c.read_text(encoding="utf-8")).get("policy", {})
            if pol:
                return {"src": c.name, **pol}
        except Exception:
            continue
    return {"src": "內建保底", "sandbox_first": True, "append_only": True,
            "destructive_delete": False, "max_rounds": 3}


def _consent() -> bool:
    try:
        if DEP:
            return bool(DEP._consent())
    except Exception:
        pass
    return os.environ.get("VIA_NET_CONSENT", "").upper() in ("YES", "1", "TRUE")


# ── ① 環境盤點 ───────────────────────────────────────────────────
def _env_py(env_path: Path) -> Path | None:
    for sub in ("Scripts/python.exe", "bin/python", "python.exe"):
        p = env_path / sub
        if p.exists():
            return p
    return None


def discover_roots(extra: list[str]) -> list[Path]:
    roots: list[Path] = []
    for raw in os.environ.get("VIA_ENV_ROOTS", "").split(os.pathsep):
        if raw.strip():
            roots.append(Path(raw.strip()))
    roots += [Path(x) for x in extra]
    for c in (getattr(EM, "def_PARAM_ENV_ROOT_CANDIDATES", None) or []):
        roots.append(Path(str(c)))
    roots += [Path.home() / "envs", Path.home() / ".virtualenvs", VIA / "Environments"]
    seen, out = set(), []
    for r in roots:
        k = str(r).lower()
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def _managed(name: str) -> bool:
    n = name.strip().lower()
    return any(n.startswith(p) for p in PREFIXES)


def discover_envs(extra_roots: list[str], only: str | None) -> list[dict]:
    envs = [{"name": "BASE", "path": sys.prefix, "py": sys.executable, "kind": "base(本解譯器)"}]
    for root in discover_roots(extra_roots):
        try:
            if not root.is_dir():
                continue
            for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
                if not child.is_dir() or not _managed(child.name):
                    continue
                if not ((child / "pyvenv.cfg").exists() or _env_py(child)):
                    continue
                py = _env_py(child)
                envs.append({"name": child.name, "path": str(child),
                             "py": str(py) if py else None, "kind": "venv"})
        except Exception:
            continue
    if only:
        envs = [e for e in envs if e["name"].lower() == only.lower()]
    return envs


# ── ② 逐環境掃描(子行程探針;stdlib-only)──────────────────────────
PROBE_SRC = r"""
import json, re, sys, os, platform
def canon(s): return re.sub(r"[-_.]+", "-", s).lower()
from importlib.metadata import distributions
eff, seen = {}, {}
for d in distributions():
    try:
        name = canon((d.metadata["Name"] or "").strip())
        if not name: continue
        p = getattr(d, "_path", None)
        root = str(p.parent) if p is not None else "?"
        lst = seen.setdefault(name, [])
        if root not in [x["root"] for x in lst]:
            lst.append({"ver": d.version or "0", "root": root})
        if name not in eff:
            eff[name] = {"ver": d.version or "0", "requires": list(d.requires or [])}
    except Exception: continue
menv = {"python_version": ".".join(platform.python_version_tuple()[:2]),
 "python_full_version": platform.python_version(), "sys_platform": sys.platform,
 "platform_system": platform.system(), "platform_machine": platform.machine(),
 "platform_python_implementation": platform.python_implementation(),
 "implementation_name": sys.implementation.name, "os_name": os.name,
 "platform_release": platform.release(), "extra": ""}
print(json.dumps({"python": platform.python_version(), "dists": eff, "menv": menv,
 "dup": {n: l for n, l in seen.items() if len(l) > 1}}))
"""


def probe_env(env: dict) -> dict:
    if env["name"] == "BASE" and DEP:
        eff, dup = DEP.get_dists_full()
        return {"ok": True, "python": ".".join(map(str, sys.version_info[:3])),
                "dists": {k: {"ver": v["ver"], "requires": v["requires"]} for k, v in eff.items()},
                "menv": DEP._marker_env(), "dup": dup}
    if not env.get("py"):
        return {"ok": False, "err": "python 執行檔缺(BROKEN 候)"}
    try:
        r = subprocess.run([env["py"], "-I", "-c", PROBE_SRC], capture_output=True,
                           text=True, timeout=120, stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            return {"ok": False, "err": "探針 rc" + str(r.returncode) + ":" + r.stderr.strip()[:80]}
        return {"ok": True, **json.loads(r.stdout)}
    except Exception as exc:
        return {"ok": False, "err": f"{type(exc).__name__}:{str(exc)[:70]}"}


def scan_env(env: dict) -> dict:
    pr = probe_env(env)
    if not pr.get("ok"):
        return {"env": env, "ok": False, "err": pr.get("err", "?")}
    _, contains = DEP._pep440()
    r = DEP.analyze(pr["dists"], pr["menv"], contains)
    return {"env": env, "ok": True, "python": pr.get("python", "?"), "dists": pr["dists"],
            "dup": pr.get("dup", {}), "missing": r["missing"], "mismatch": r["mismatch"],
            "rev": r["rev"], "unevaluated": r["unevaluated"]}


# ── ③ 風險因子抽取(政策母版規則)──────────────────────────────────
def risk_factors(scan: dict) -> list[dict]:
    f: list[dict] = []
    name = scan["env"]["name"].lower()
    dists = scan.get("dists", {})
    if not scan.get("ok"):
        return [{"code": "PROBE_FAIL", "sev": "RED", "detail": scan.get("err", "?"), "pkgs": []}]
    if scan["missing"] or scan["mismatch"]:
        pkgs = sorted({m["pkg"] for m in scan["missing"]} | {m["pkg"] for m in scan["mismatch"]})
        f.append({"code": "BROKEN_DEPS", "sev": "RED", "pkgs": pkgs,
                  "detail": f"缺件 {len(scan['missing'])}+互撞 {len(scan['mismatch'])} 條(即時衝突)"})
    cv = sorted(n for n in dists if n in CV2_FAMILY)
    if len(cv) > 1 or (cv and cv != [KEEP_CV2]):
        f.append({"code": "CV2_OFF_ANCHOR", "sev": "RED", "pkgs": cv,
                  "detail": f"cv2 家族偏錨(裁定統包版 {KEEP_CV2};多變體=互撞回歸源)"})
    hi = sorted(n for n in dists if n in HIGH_RISK)
    me = sorted(n for n in dists if n in MED_RISK)
    if name == "base":
        bad = (hi if "HIGH" in BASE_BLOCK else []) + (me if "MEDIUM" in BASE_BLOCK else [])
        if bad:
            f.append({"code": "BASE_POLLUTION", "sev": "YELLOW", "pkgs": sorted(bad),
                      "detail": "BASE 污染:政策封鎖 MEDIUM/HIGH 入 base——遷出至專屬環境(BASE 最佳化)"})
    elif hi:
        f.append({"code": "HIGH_RISK_PRESENT", "sev": "YELLOW", "pkgs": hi,
                  "detail": f"高風險庫在境 {len(hi)} 件" + ("——混居超標,拆分隔離" if len(hi) >= 3 else "(單獨隔離原則)")})
    if name == "via_core":
        off = sorted(n for n in dists if n not in CORE_WL and n not in BOOT)
        if off:
            f.append({"code": "CORE_WL_VIOLATION", "sev": "YELLOW", "pkgs": off[:20],
                      "detail": f"via_core 白名單外 {len(off)} 件(政策:白名單制)"})
    if scan.get("dup"):
        f.append({"code": "DUP_LAYERS", "sev": "YELLOW", "pkgs": sorted(scan["dup"])[:10],
                  "detail": f"多層同名 {len(scan['dup'])} 件(遮蔽風險;via-install --doctor 可深診)"})
    return f


def env_status(factors: list[dict]) -> str:
    """EnvManager 四態裁決:BROKEN/REBUILD/WARN/OK。"""
    codes = {x["code"] for x in factors}
    if "PROBE_FAIL" in codes:
        return "BROKEN"
    if any(x["sev"] == "RED" for x in factors):
        return "REBUILD"
    return "WARN" if factors else "OK"


def diverge_matrix(scans: list[dict]) -> dict:
    out = {}
    for lib in WATCH_DIVERGE:
        vers = {}
        for s in scans:
            if s.get("ok") and lib in s.get("dists", {}):
                vers[s["env"]["name"]] = s["dists"][lib]["ver"]
        majors = {v.split(".")[0] for v in vers.values()}
        out[lib] = {"vers": vers, "majors": sorted(majors), "diverged": len(majors) > 1}
    return out


# ── ④ 隔離重建計畫(依既有件單改善;旁建零破壞)────────────────────
def top_level_pins(scan: dict) -> list[str]:
    """既有件單→改善配方:頂層件鎖現版;衝突件放開讓解析器選;cv2 換錨;bootstrap 除外。"""
    dists, rev = scan["dists"], scan["rev"]
    conflicted = {m["pkg"] for m in scan["mismatch"]} | {m["by"] for m in scan["mismatch"]}
    pins, cv_swapped = [], False
    for name in sorted(dists):
        if name in BOOT or name in rev:  # 被人依賴=非頂層,交解析器
            continue
        if name in CV2_FAMILY:
            if not cv_swapped:
                pins.append(KEEP_CV2)
                cv_swapped = True
            continue
        pins.append(name if name in conflicted else f"{name}=={dists[name]['ver']}")
    if not cv_swapped and any(n in CV2_FAMILY for n in dists):
        pins.append(KEEP_CV2)
    return pins


def build_stages(scans: list[dict], diverge: dict, ts: str) -> list[dict]:
    stages, n = [], 0
    for s in scans:
        st = env_status(s.get("factors", []))
        env = s["env"]
        if st in ("REBUILD", "BROKEN") and env["name"] != "BASE":
            n += 1
            newp = str(Path(env["path"]).parent / f"{env['name']}__rb{ts}") if env.get("path") else ""
            pins = top_level_pins(s) if s.get("ok") else []
            out_iso = []
            if env["name"].lower() == "via_core":  # 白名單制:重建時白名單外中高風險件改道隔離
                keep = []
                for p in pins:
                    base_n = canon(re.split(r"[<>=!~\[]", p)[0])
                    if base_n not in CORE_WL and (base_n in HIGH_RISK or base_n in MED_RISK):
                        out_iso.append({"lib": base_n, "env": _route_env(base_n), "pins": [p]})
                    else:
                        keep.append(p)
                pins = keep
            stages.append({
                "n": n, "kind": "rebuild", "env": env["name"], "newenv": newp,
                "goal": f"旁建重建 {env['name']}(零破壞;原環境不動,驗畢切換候裁)",
                "why": ";".join(x["detail"][:46] for x in s["factors"][:2]),
                "watch": "旁建=sandbox_first;切換(改名/alias)屬破壞性→候裁清單",
                "pins": pins, "python_ver": s.get("python", "?")})
            if out_iso:
                n += 1
                stages.append({"n": n, "kind": "isolate", "env": env["name"],
                               "goal": f"via_core 白名單外中高風險 {len(out_iso)} 件改道專屬環境",
                               "why": "政策:via_core 白名單制;中高風險一律單獨隔離",
                               "watch": "只旁建+裝件;原環境移除屬破壞性→候裁",
                               "pins": [], "targets": out_iso, "python_ver": s.get("python", "?")})
        elif st == "WARN":
            miss = [m["pkg"] + (m["spec"] or "") for m in s.get("missing", [])][:8]
            hi_here = next((x for x in s["factors"] if x["code"] == "HIGH_RISK_PRESENT" and len(x["pkgs"]) >= 3), None)
            if hi_here:
                n += 1
                stages.append({"n": n, "kind": "isolate", "env": env["name"],
                               "goal": f"混居拆分:{env['name']} 高風險 {len(hi_here['pkgs'])} 件各出專屬環境",
                               "why": "單獨隔離原則(中高風險 libs 一律專屬 venv+輔助工具共存)",
                               "watch": "只旁建新環境+裝件;原環境移除件屬破壞性→候裁",
                               "pins": [], "targets": [
                                   {"lib": p, "env": _route_env(p), "pins": [p + "==" + s["dists"][p]["ver"]]}
                                   for p in hi_here["pkgs"]], "python_ver": s.get("python", "?")})
            if miss:
                n += 1
                stages.append({"n": n, "kind": "repair", "env": env["name"],
                               "env_path": env.get("path", ""),
                               "goal": f"原地修補 {env['name']} 缺件 {len(miss)} 件",
                               "why": "WARN 級免重建,依既有狀況補齊", "watch": "修補後 pip check 回驗",
                               "pins": miss, "python_ver": s.get("python", "?")})
    base = next((s for s in scans if s["env"]["name"] == "BASE"), None)
    if base and base.get("ok"):
        bad = next((x for x in base.get("factors", []) if x["code"] == "BASE_POLLUTION"), None)
        if bad:
            n += 1
            stages.append({"n": n, "kind": "base_opt", "env": "BASE",
                           "goal": f"BASE 最佳化:遷出封鎖級 {len(bad['pkgs'])} 件至專屬環境",
                           "why": "政策 BASE 封鎖 MEDIUM/HIGH;base 只留工具鏈+LOW",
                           "watch": "遷入=可執行;BASE 端移除=破壞性→候裁",
                           "pins": [], "targets": [
                               {"lib": p, "env": _route_env(p), "pins": [p]} for p in bad["pkgs"][:12]],
                           "python_ver": base.get("python", "?")})
    np_d = diverge.get("numpy", {})
    if np_d.get("diverged"):
        n += 1
        stages.append({"n": n, "kind": "scaffold", "env": "(新)",
                       "goal": f"numpy 多版本支架:大版 {'/'.join(np_d['majors'])} 各配專屬環境×Python",
                       "why": "操作員令:常用易衝突件(numpy)多版本環境可搭多版本 Python;現況已分歧",
                       "watch": "Python 供應:pyenv install / uv python install;{PY} 由操作員選版",
                       "pins": [], "targets": [
                           {"lib": "numpy", "env": f"via_np{mj}_py{{PYMM}}", "pins": [f"numpy=={ver}" if ver.split('.')[0] == mj else f"numpy<{int(mj) + 1},>={mj}"]}
                           for mj in np_d["majors"]
                           for ver in [next(v for v in np_d["vers"].values() if v.split(".")[0] == mj)]],
                       "python_ver": "多版"})
    return stages


def _route_env(lib: str) -> str:
    for env_name, hints in PURPOSE.items():
        if canon(lib) in hints:
            return env_name
    return f"via_{canon(lib).replace('-', '_')}"


# ── ⑤ 鏡像測選 + ⑥ 反覆實測 ─────────────────────────────────────
def pick_mirror() -> dict:
    if not DEP:
        return {"state": "NOT_RUN", "url": "", "note": "via-deps 判定器缺"}
    if not _consent():
        return {"state": "NOT_RUN", "url": "", "note": "同意閘關(VIA_NET_CONSENT=YES 後三源全測)"}
    rows = []
    for k, (label, url) in DEP.MIRRORS.items():
        ms, note = DEP._probe(url)
        rows.append({"mirror": k, "label": label, "url": url, "ms": ms, "note": note})
    ok = sorted([x for x in rows if x["ms"] is not None], key=lambda x: x["ms"])
    if not ok:
        return {"state": "FAIL", "url": "", "rows": rows, "note": "三源皆不通(誠實;dry-run 改走預設源)"}
    return {"state": "OK", "mirror": ok[0]["mirror"], "url": ok[0]["url"], "rows": rows,
            "note": f"最快 {ok[0]['mirror']} {ok[0]['ms']}ms(三源全測畢)"}


def judge_rounds(rounds: list[dict]) -> tuple[str, str, str]:
    """輪次判讀(可自測):全 rc0+末兩輪清單一致=GREEN;rc≠0=RED;飄移=YELLOW。"""
    if not rounds:
        return "NOT_RUN", "候", "零輪(網路/同意閘)"
    if any(r["rc"] != 0 for r in rounds):
        return "FAIL", "RED", "解析失敗:" + (rounds[-1].get("tail", "") or "?")[:80]
    if len(rounds) >= 2 and rounds[-1]["would"] != rounds[-2]["would"]:
        return "UNSTABLE", "YELLOW", "末兩輪解析飄移(鏡像快取/上游變動?)——候裁再測"
    if not rounds[-1]["would"]:
        return "NOOP", "GREEN", "已全滿足零變動"
    return "OK", "GREEN", f"{len(rounds)} 輪一致,會裝 {len(rounds[-1]['would'])} 件"


def _dry_groups(stage: dict) -> list[tuple[str, list[str]]]:
    """實測分靶:targets 各屬不同環境=各自獨立解析(numpy 多大版絕不同鍋);可自測。"""
    groups: list[tuple[str, list[str]]] = []
    if stage.get("targets"):
        for t in stage["targets"]:
            pins = [p for p in t["pins"] if "{" not in p]
            if pins:
                groups.append((t["env"], pins))
    else:
        pins = [p for p in stage.get("pins", []) if "{" not in p]
        if pins:
            groups.append((stage.get("newenv") or stage["env"], pins))
    return groups


_RISK_ORDER = {"GREEN": 0, "候": 1, "YELLOW": 2, "RED": 3}


def _dryrun_rounds(pins: list[str], mirror_url: str, rounds_n: int) -> list[dict]:
    py = sys.executable  # 新環境未生,解析可行性以本解譯器代測(同大版原則,誠實註記)
    rounds = []
    for _ in range(max(2, rounds_n)):
        cmd = [py, "-m", "pip", "install", "--dry-run", "--no-color"]
        if mirror_url:
            cmd += ["-i", mirror_url]
        try:
            r = subprocess.run(cmd + pins, capture_output=True, text=True, timeout=600,
                               stdin=subprocess.DEVNULL)
        except Exception as exc:
            rounds.append({"rc": -1, "would": [], "tail": f"{type(exc).__name__}"})
            break
        would = []
        for line in r.stdout.splitlines():
            if line.strip().startswith("Would install"):
                would = sorted(line.strip()[len("Would install"):].split())
        tail = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-1:]
        rounds.append({"rc": r.returncode, "would": would, "tail": (tail[0][:90] if tail else "")})
        if r.returncode != 0:
            break
    return rounds


def dryrun_stage(stage: dict, mirror_url: str, rounds_n: int) -> dict:
    groups = _dry_groups(stage)
    if not groups:
        return {"per": [], "state": "NOT_RUN", "risk": "候", "note": "無可實測件(支架待選版/候裁)"}
    per, worst = [], "GREEN"
    for gname, pins in groups:
        rounds = _dryrun_rounds(pins, mirror_url, rounds_n)
        state, risk, note = judge_rounds(rounds)
        per.append({"target": gname, "state": state, "risk": risk, "note": note, "rounds": rounds})
        if _RISK_ORDER.get(risk, 3) > _RISK_ORDER.get(worst, 0):
            worst = risk
    note = " / ".join(f"{Path(p['target']).name if os.sep in p['target'] else p['target']}"
                      f":{p['note'][:44]}" for p in per[:3])
    state = "OK" if worst == "GREEN" else ("FAIL" if worst == "RED" else "MIX")
    return {"per": per, "state": state, "risk": worst, "note": note}


# ── ⑦ 執行檔生成(GREEN 段限定;操作員自跑)────────────────────────
def emit_scripts(stages: list[dict], mirror_url: str, ts: str) -> tuple[str, str]:
    uv = bool(shutil.which("uv"))
    mi = f" -i {mirror_url}" if mirror_url else ""
    mu = f" --index-url {mirror_url}" if mirror_url else ""
    ps, sh = ['$ErrorActionPreference = "Stop"',
              f"# VIA 重建執行檔 {ts} — 只含 GREEN 段;候裁(切換/移除)不在此檔;跑前先閱"], \
             ["#!/bin/sh", "set -e", f"# VIA 重建執行檔 {ts} — 只含 GREEN 段;候裁不在此檔"]

    def _emit(env_dir_ps: str, env_dir_sh: str, pins: list[str], mk: bool):
        q = " ".join(f'"{p}"' if any(c in p for c in "<>=![]") else p for p in pins)
        if mk:
            ps.append(f'py -m venv "{env_dir_ps}"')
            sh.append(f'python3 -m venv "{env_dir_sh}"')
        pyw, pyu = f"{env_dir_ps}\\Scripts\\python.exe", f"{env_dir_sh}/bin/python"
        if uv:
            ps.append(f'uv pip install --python "{pyw}"{mu} {q}')
            sh.append(f'uv pip install --python "{pyu}"{mu} {q}')
        else:
            ps.append(f'& "{pyw}" -m pip install{mi} {q}')
            sh.append(f'"{pyu}" -m pip install{mi} {q}')
        ps.append(f'& "{pyw}" -m pip check')
        sh.append(f'"{pyu}" -m pip check')

    for st in stages:
        if st.get("dryrun", {}).get("risk") != "GREEN":
            continue
        ps.append(f"# 段{st['n']} {st['goal']}")
        sh.append(f"# 段{st['n']} {st['goal']}")
        if st["kind"] == "rebuild":
            newp = st["newenv"]
            _emit(newp, newp, st["pins"], mk=True)
        elif st["kind"] == "repair":
            envp = st.get("env_path") or str(Path.home() / "envs" / st["env"])
            ps.append(f"# 原地修補 {st['env']}(實際路徑)")
            sh.append(f"# 原地修補 {st['env']}(實際路徑)")
            _emit(envp, envp, st["pins"], mk=False)
        elif st["kind"] in ("isolate", "base_opt", "scaffold"):
            for t in st.get("targets", []):
                envd_ps = f"$env:USERPROFILE\\envs\\{t['env']}"
                envd_sh = str(Path.home() / "envs" / t["env"])
                if "{" in t["env"] or any("{" in p for p in t["pins"]):
                    ps.append(f"# 候裁:{t['env']} 需操作員選 Python 版({{PYMM}})後自填")
                    sh.append(f"# 候裁:{t['env']} 需操作員選 Python 版後自填")
                    continue
                _emit(envd_ps, envd_sh, t["pins"], mk=True)
    ps.append("Write-Host '重建執行檔跑畢——回驗:via-rebuild --offline'")
    sh.append("echo '重建執行檔跑畢——回驗:via-rebuild --offline'")
    return "\r\n".join(ps) + "\r\n", "\n".join(sh) + "\n"


# ── 主流程 ───────────────────────────────────────────────────────
def cmd_govern(args: list[str]) -> int:
    if DEP is None:
        print("  ✗ via_dep_super 判定器缺(TOOL-031)——本引擎需搭配,誠實停")
        return 2
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    offline = "--offline" in args
    only = _arg_after(args, "--env")
    extra = [_arg_after(args, "--roots")] if _arg_after(args, "--roots") else []
    pol = _forge_policy()
    rounds_n = int(_arg_after(args, "--rounds") or pol.get("max_rounds", 3))
    print(f"=== 多環境隔離重建計畫引擎 v0100 · {ts} · 零安裝零刪改(旁建 sandbox_first)===")
    print(f"  [政策] EngineForge:{pol['src']} · max_rounds={rounds_n} · destructive_delete="
          f"{pol.get('destructive_delete', False)}(破壞性一律候裁)· EnvManager 母版:{'導入 OK' if EM else '缺(鏡射保底)'}")
    print("── ① 環境盤點(via_*/base/paddle/camelot + BASE)──")
    envs = discover_envs([e for e in extra if e], only)
    if not envs:
        print("  ✗ 零環境命中(--env 名有誤?或環境根不在此機——用 --roots/VIA_ENV_ROOTS 指路)")
        return 2
    for e in envs:
        print(f"  · {e['name']:16s} {e['kind']:12s} {e['path']}")
    print("── ② 逐環境掃描+③ 風險因子 ──")
    scans = []
    for e in envs:
        s = scan_env(e)
        s["factors"] = risk_factors(s)
        s["status"] = env_status(s["factors"])
        scans.append(s)
        mark = {"OK": "OK  ", "WARN": "WARN", "REBUILD": "重建", "BROKEN": "壞損"}[s["status"]]
        base_info = f"Py {s.get('python', '?')} · {len(s.get('dists', {}))} 件" if s.get("ok") else s.get("err", "?")
        print(f"  [{mark}] {s['env']['name']:16s} {base_info}")
        for x in s["factors"]:
            print(f"     {'✗' if x['sev'] == 'RED' else '~'} [{x['code']}] {x['detail'][:84]}")
            if x["pkgs"]:
                print(f"        件:{', '.join(x['pkgs'][:8])}{' …' if len(x['pkgs']) > 8 else ''}")
    div = diverge_matrix(scans)
    for lib, d in div.items():
        if d["diverged"]:
            print(f"  ~ [跨境分歧] {lib}:大版 {'/'.join(d['majors'])} — " +
                  " · ".join(f"{k}={v}" for k, v in list(d["vers"].items())[:5]))
    print("── ④ 隔離重建計畫(依既有件單改善,不從頭開始)──")
    stages = build_stages(scans, div, ts)
    if not stages:
        print("  全境 OK——無段可出(維持:新件一律 via-plan→via-install)")
    for st in stages:
        print(f"  [段{st['n']}·{st['kind']}] {st['goal']}")
        print(f"     由:{st['why'][:80]}")
        print(f"     防:{st['watch'][:80]}")
        pin_show = st.get("pins") or [p for t in st.get("targets", []) for p in t["pins"]]
        if pin_show:
            print(f"     件:{' '.join(pin_show[:6])}{' …共 ' + str(len(pin_show)) + ' 件' if len(pin_show) > 6 else ''}")
    mirror = {"state": "NOT_RUN", "url": "", "note": "--offline(零網路)"}
    if stages and not offline:
        print("── ⑤ 鏡像測選(official/tsinghua/aliyun 三源全測)──")
        mirror = pick_mirror()
        for row in mirror.get("rows", []):
            print(f"  [{'OK  ' if row['ms'] is not None else 'FAIL'}] {row['mirror']:8s} "
                  f"{str(row['ms']) + ' ms' if row['ms'] is not None else '—'} · {row['note'][:56]}")
        print(f"  [裁] {mirror['note']}")
    print(f"── ⑥ 反覆實測(pip --dry-run × {rounds_n} 輪;末兩輪一致才綠)──")
    if offline:
        print("  SKIP(--offline)——段全列候,實測待網路窗")
        for st in stages:
            st["dryrun"] = {"state": "NOT_RUN", "risk": "候", "note": "--offline"}
    elif not _consent():
        print("  NOT_RUN(dry-run 連 PyPI 解析=網路行為,同意閘關)——")
        print('     PowerShell:$env:VIA_NET_CONSENT="YES" · bash:export VIA_NET_CONSENT=YES')
        for st in stages:
            st["dryrun"] = {"state": "NOT_RUN", "risk": "候", "note": "同意閘關"}
    else:
        for st in stages:
            st["dryrun"] = dryrun_stage(st, mirror.get("url", ""), rounds_n)
            d = st["dryrun"]
            print(f"  [{d['risk']:6s}] 段{st['n']} · {d['note'][:90]}")
    print("── ⑦ 裁決出令 ──")
    greens = [st for st in stages if st.get("dryrun", {}).get("risk") == "GREEN"]
    reds = [st for st in stages if st.get("dryrun", {}).get("risk") == "RED"
            or st["kind"] == "rebuild" and not st.get("pins")]
    n_broken = sum(1 for s in scans if s["status"] in ("REBUILD", "BROKEN"))
    print(f"  環境:{len(scans)} 境(重建/壞損 {n_broken})· 計畫:{len(stages)} 段 · "
          f"GREEN {len(greens)} · RED {len(reds)} · 候 {len(stages) - len(greens) - len(reds)}")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"REBUILD_{ts}.json"
    ev.write_text(json.dumps({
        "schema": "VIA.EnvRebuild.v1", "ts": ts, "policy": pol,
        "envs": [{"name": s["env"]["name"], "status": s["status"], "python": s.get("python"),
                  "dists_n": len(s.get("dists", {})), "factors": s["factors"],
                  "missing": s.get("missing", []), "mismatch": s.get("mismatch", [])} for s in scans],
        "diverge": div, "mirror": {k: v for k, v in mirror.items() if k != "rows"},
        "stages": [{k: v for k, v in st.items() if k != "rev"} for st in stages],
        "red_lines": "zero_install·side_build_only·green_only_scripts·destructive_to_adjudication"},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}")
    if greens:
        ps_txt, sh_txt = emit_scripts(stages, mirror.get("url", ""), ts)
        ps_f, sh_f = OUT / f"REBUILD_EXEC_{ts}.ps1", OUT / f"REBUILD_EXEC_{ts}.sh"
        ps_f.write_text(ps_txt, encoding="utf-8-sig")
        sh_f.write_text(sh_txt, encoding="utf-8")
        print(f"  [執行檔] {ps_f.name} / {sh_f.name}(只含 GREEN 段;操作員檢閱後自跑或走 via-install)")
    else:
        print("  無 GREEN 段——不出執行檔(反覆實測無誤後才准安裝,紅線)")
    cand = [st for st in stages if st.get("dryrun", {}).get("risk") in ("候", "YELLOW", "RED")]
    if cand:
        print("  [候裁] " + " · ".join(f"段{st['n']}({st['dryrun']['risk']})" for st in cand[:8]) +
              " ——含切換/移除等破壞性動作,操作員裁後另跑")
    return 1 if (reds or n_broken) else 0


# ── 自測 12 檢(零網路零環境依賴)──────────────────────────────────
def cmd_selftest() -> int:
    ok_scan = {"env": {"name": "via_demo", "path": "/x", "py": "/x/bin/python"}, "ok": True,
               "python": "3.11.9", "dup": {},
               "dists": {"numpy": {"ver": "1.26.4", "requires": []},
                         "torch": {"ver": "2.3.0", "requires": []},
                         "webapp": {"ver": "1.0", "requires": ["numpy>=2.0"]}},
               "missing": [], "mismatch": [{"pkg": "numpy", "installed": "1.26.4",
                                            "spec": ">=2.0", "by": "webapp"}],
               "rev": {"numpy": [("webapp", ">=2.0")]}, "unevaluated": 0}

    def t01():
        assert "torch" in HIGH_RISK and "duckdb" in MED_RISK and "requests" in CORE_WL

    def t02():
        f = risk_factors(ok_scan)
        assert any(x["code"] == "BROKEN_DEPS" and x["sev"] == "RED" for x in f)
        assert env_status(f) == "REBUILD"

    def t03():
        s = dict(ok_scan, mismatch=[], dists={"opencv-python": {"ver": "4.10", "requires": []},
                                              "opencv-contrib-python-headless": {"ver": "4.10", "requires": []}})
        f = risk_factors(s)
        assert any(x["code"] == "CV2_OFF_ANCHOR" for x in f) and env_status(f) == "REBUILD"

    def t04():
        s = dict(ok_scan, mismatch=[], env={"name": "BASE", "path": "", "py": ""},
                 dists={"torch": {"ver": "2.3.0", "requires": []}, "duckdb": {"ver": "1.0", "requires": []}})
        f = risk_factors(s)
        assert any(x["code"] == "BASE_POLLUTION" for x in f) and env_status(f) == "WARN"

    def t05():
        s = dict(ok_scan, mismatch=[], env={"name": "via_core", "path": "", "py": ""},
                 dists={"torch": {"ver": "2.3.0", "requires": []}, "requests": {"ver": "2.32", "requires": []}})
        assert any(x["code"] == "CORE_WL_VIOLATION" and "torch" in x["pkgs"] for x in risk_factors(s))

    def t06():
        assert env_status([{"code": "PROBE_FAIL", "sev": "RED"}]) == "BROKEN"
        assert env_status([]) == "OK"

    def t07():
        pins = top_level_pins(ok_scan)
        assert "torch==2.3.0" in pins          # 潔淨頂層件鎖現版
        assert "webapp" in pins and "webapp==1.0" not in pins  # 衝突邊頂層件放開
        assert not any(p.startswith("numpy") for p in pins)    # 非頂層交解析器(隨 webapp>=2.0)

    def t08():
        s2 = dict(ok_scan, env={"name": "via_two", "path": "/y", "py": "/y/bin/python"},
                  dists={"numpy": {"ver": "2.1.0", "requires": []}}, mismatch=[], factors=[])
        d = diverge_matrix([dict(ok_scan, factors=[]), s2])
        assert d["numpy"]["diverged"] and d["numpy"]["majors"] == ["1", "2"]
        st = build_stages([dict(ok_scan, factors=risk_factors(ok_scan),
                                status="REBUILD")], d, "TS")
        assert any(x["kind"] == "scaffold" for x in st) and any(x["kind"] == "rebuild" for x in st)

    def t09():
        assert judge_rounds([{"rc": 0, "would": ["a-1.0"]}, {"rc": 0, "would": ["a-1.0"]}])[1] == "GREEN"
        assert judge_rounds([{"rc": 1, "would": [], "tail": "boom"}])[1] == "RED"
        assert judge_rounds([{"rc": 0, "would": ["a-1.0"]}, {"rc": 0, "would": ["a-2.0"]}])[1] == "YELLOW"
        assert judge_rounds([])[0] == "NOT_RUN"

    def t10():
        st = [{"n": 1, "kind": "rebuild", "env": "via_demo", "newenv": "/e/via_demo__rbTS",
               "goal": "G", "why": "W", "watch": "P", "pins": ["numpy", "torch==2.3.0"],
               "dryrun": {"risk": "GREEN"}},
              {"n": 2, "kind": "rebuild", "env": "via_red", "newenv": "/e/r", "goal": "R",
               "why": "W", "watch": "P", "pins": ["x==1"], "dryrun": {"risk": "RED"}}]
        ps, sh = emit_scripts(st, "https://pypi.org/simple/", "TS")
        assert "via_demo__rbTS" in ps and "via_red" not in ps and "via_red" not in sh
        assert "pip check" in sh and "set -e" in sh

    def t11():
        assert _managed("via_core") and _managed("paddle_311") and _managed("BASE".lower()) \
            and not _managed("random_env")
        assert _route_env("paddleocr") == "paddle_311" and _route_env("newlib") == "via_newlib"

    def t12():
        assert DEP is not None and callable(DEP.analyze)  # 搭配件在位
        pol = _forge_policy()
        assert int(pol.get("max_rounds", 3)) >= 1 and pol.get("destructive_delete") is False

    def t13():
        g = _dry_groups({"targets": [{"lib": "numpy", "env": "via_np1_py{PYMM}", "pins": ["numpy==1.26.4"]},
                                     {"lib": "numpy", "env": "via_np2_py{PYMM}", "pins": ["numpy==2.1.0"]}]})
        assert len(g) == 2 and g[0][1] == ["numpy==1.26.4"]  # 分靶各測,大版絕不同鍋
        assert _dry_groups({"pins": ["a==1"], "env": "e", "newenv": "/n"}) == [("/n", ["a==1"])]

    battery = [("政策母版三表", t01), ("互撞→REBUILD", t02), ("cv2 偏錨", t03),
               ("BASE 污染", t04), ("via_core 白名單", t05), ("四態裁決", t06),
               ("重建配方(衝突放開)", t07), ("numpy 分歧+支架", t08), ("輪次判讀", t09),
               ("執行檔只含 GREEN", t10), ("前綴+用途路由", t11), ("搭配件+紅線組態", t12),
               ("實測分靶群組", t13)]
    print(f"=== 重建計畫引擎自測 13 檢(EnvManager:{'母版' if EM else '保底'};零網路零改動)===")
    n_ok = 0
    for name, fn in battery:
        try:
            fn()
            n_ok += 1
            print(f"  [OK  ] {name}")
        except Exception as exc:
            print(f"  [FAIL] {name} · {type(exc).__name__}:{str(exc)[:70]}")
    print(f"  [計] {n_ok}/{len(battery)} 綠")
    return 0 if n_ok == len(battery) else 1


def _arg_after(args: list, flag: str):
    try:
        return args[args.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return cmd_selftest()
    if "-h" in a or "--help" in a or "--doc" in a:
        print(__doc__)
        return 0
    return cmd_govern(a)


if __name__ == "__main__":
    sys.exit(main())
