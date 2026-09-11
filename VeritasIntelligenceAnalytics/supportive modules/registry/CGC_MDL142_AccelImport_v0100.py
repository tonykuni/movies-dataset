#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL142_AccelImport v0100 — 加速器套件導入閘(批384 操作員令「將所有加速器依照 via_envmanager 規定
導入 via_core via_ 相關環境;vdf 所有引擎都要加入加速器跟網路工具」)

實錄起點(工作站 2026-09-12 via-vdffetch ⑥):vdf 家族境 via_vdf_312 跑加速器啟動報告=
  「lib 冊 88 · 可用 14 · 缺 74 · 真實能力 10/31」+「缺(lazy stub 代位,誠實非真加速)」
→ 橋掛滿(VDF 在冊 184 件:ACCEL 橋 154/154、NET 橋 154/154、真用統包網路 153)但套件不在境內=
  加速器只是代位樁。本閘補的正是這一段:把 88 件冊依《VIA_EnvManager 防衝突管理規範》(MDL135 尾版
  正本:via_core 白名單 → 高風險家族隔離 → purpose hints → base 不碰)路由進 via_core 與 via_* 家族境。

職權(只增不減;base 零觸碰):
  ① 冊 — 自 VeritasCeleritas 尾版 _LIB_MAP 逐字解析 88 件(import 名),配 pip 名(cv2→opencv-contrib-python
     等;MDL135「cv2 家族換錨 contrib」同律);永不自行發明冊。
  ② 路由 — MDL135 尾版 core_whitelist()/high_risk()/purpose_hints() 直取(缺席=內建同義保守退路):
     via_core 白名單件→via_core;高風險(torch/tensorflow/paddleocr/onnxruntime/opencv)→家族/隔離境,
     永不入 base;通用算力件→via_core + 三家族境(vdf/vrn/vap);平台不適用/GPU 專屬/需系統二進位者→
     誠實標 NOT_APPLICABLE / MANUAL 不列計畫(不空轉、不假裝可裝)。
  ③ 探 — 逐境以該境 python 跑 find_spec 探針(不 import=零副作用),得每境「已裝/缺」真值。
  ④ 計畫 — 境 × 缺件;預設唯讀。--apply --approve 才裝:uv pip install 優先(缺 uv 退 pip),逐件逐境,
     誠實 OK/FAIL/SKIP;單境失敗不影響其他境(不卡斷);逾時可殺(--timeout)。
  ⑤ 存證 — VIA_Reports/accel_import/ACCEL_IMPORT_<ts>.json + 頁 VIA_UI_AccelImport_v0100.html(零 CDN
     手機單欄)+ 冊 VIA_AccelImport_v0100.json;台帳由呼端記。
律:base 不動(除 --include-base 明令)、零刪除、零 force、尾版律(Celeritas/MDL135 皆 glob 尾版)、
    誠實三態、逾時不卡斷、網路安裝走同意閘(VIA_NET_CONSENT)。
用法:via-accel-import                      → plan(唯讀:冊/路由/逐境缺件/計畫)
      via-accel-import --apply --approve    → 真裝(uv 優先;base 零觸碰)
      via-accel-import --env-root <路徑>    → 指定環境根(預設 %USERPROFILE%\envs 等)
      python <本檔> --selftest              → 九檢
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

import html
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"
REP = VIA / "VIA_Reports" / "accel_import"
PAGE = UI / "VIA_UI_AccelImport_v0100.html"
BOOK = HERE / "VIA_AccelImport_v0100.json"
ENGINE_TAG = "CGC_MDL142_AccelImport v0100"

# import 名 → pip 名(僅列與 import 名不同者;其餘同名)
PIP_NAME = {"cv2": "opencv-contrib-python", "PIL": "Pillow", "skimage": "scikit-image", "sklearn": "scikit-learn",
            "Levenshtein": "Levenshtein", "talib": "TA-Lib", "snappy": "python-snappy", "blosc2": "blosc2",
            "pandas_ta": "pandas-ta", "cpuinfo": "py-cpuinfo", "rapidjson": "python-rapidjson", "mmh3": "mmh3",
            "cityhash": "cityhash", "msgspec": "msgspec", "brotli": "Brotli", "redis": "redis", "jax": "jax",
            "paddleocr": "paddleocr", "onnxruntime": "onnxruntime", "tensorflow": "tensorflow", "torch": "torch",
            "pyvips": "pyvips", "rawpy": "rawpy", "pytesseract": "pytesseract", "ta": "ta", "ffn": "ffn"}
# GPU 專屬:無 CUDA 即 NOT_APPLICABLE(誠實不空轉)
GPU_ONLY = {"cudf", "cupy"}
# 需系統二進位/編譯鏈(pip 單裝常敗):誠實 MANUAL 並記原因
MANUAL = {"talib": "需先裝 TA-Lib C 函式庫(Windows 請用對應 wheel)", "snappy": "需 snappy C 函式庫",
          "pyvips": "需 libvips 執行檔", "rawpy": "需 LibRaw", "datatable": "Windows wheel 常缺",
          "modin": "需 ray/dask 後端先備", "vaex": "相依重且常與 pandas 版本相衝"}
# 平台限定
PLATFORM_ONLY = {"uvloop": "posix", "winloop": "windows"}
# 高風險(MDL135 high_risk 同義退路):永不入 base;只進家族/隔離境
FALLBACK_HIGH_RISK = {"torch", "tensorflow", "paddleocr", "onnxruntime", "cv2", "jax", "paddlepaddle"}
FALLBACK_CORE_WHITELIST = {"requests", "httpx", "aiohttp", "orjson", "numpy", "pandas", "pyarrow", "duckdb",
                           "polars", "openpyxl", "rich", "loguru"}
# 家族境(批384 家族境律;via_core 為共用核心)
FAMILY_ENVS = ["via_core", "via_vdf", "via_vrn", "via_vap"]
ENV_ALIASES = {"via_core": ["via_core", "via_core_312", "venv_core"],
               "via_vdf": ["via_vdf_312", "via_vdf", "via_vdf_313"],
               "via_vrn": ["via_vrn_312", "via_vrn", "via_extract_312", "via_vrn4"],
               "via_vap": ["via_vap_312", "via_vap"]}
RULES = ["base 零觸碰(除 --include-base 明令):「base 只放該有的工具」",
         "路由正本=MDL135 尾版 core_whitelist/high_risk/purpose_hints;本閘不自行發明政策",
         "冊正本=VeritasCeleritas 尾版 _LIB_MAP(88 件);不自行增刪",
         "誠實三態:GPU 專屬無卡=NOT_APPLICABLE;需系統二進位=MANUAL;平台不符=NOT_APPLICABLE(皆不列計畫)",
         "只增不減零刪除零 force;逾時可殺不卡斷;安裝走同意閘 VIA_NET_CONSENT"]


# ---------------------------------------------------------------- 冊
def newest(pat: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pat))
    return hits[-1] if hits else None


def celeritas_path() -> Path | None:
    p = VIA / "supportive modules" / "VeritasCeleritas.py"
    return p if p.exists() else None


def roster() -> list:
    """自 Celeritas 尾版 _LIB_MAP 逐字解析 import 名(88 件);缺=空冊(誠實)"""
    p = celeritas_path()
    if not p:
        return []
    src = p.read_text(encoding="utf-8", errors="ignore")
    if "_LIB_MAP" not in src:
        return []
    blk = src.split("_LIB_MAP: Dict[str, Any] = {", 1)[-1].split("\n}", 1)[0]
    out, seen = [], set()
    for name in re.findall(r'"([A-Za-z0-9_.\-]+)":', blk):
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def _mdl135():
    try:
        p = newest("CGC_MDL135_EnvGovernance_v0*.py", HERE)
        if not p:
            return None
        spec = importlib.util.spec_from_file_location("envgov_ai", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["envgov_ai"] = m
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def policy() -> dict:
    """路由政策:MDL135 尾版直取;缺席=保守退路(誠實標 source)"""
    m = _mdl135()
    if m is not None:
        try:
            return {"core": {str(x).lower() for x in m.core_whitelist()},
                    "high": {str(x).lower() for x in m.high_risk()},
                    "hints": {k: [str(x).lower() for x in v] for k, v in m.purpose_hints().items()},
                    "source": "MDL135 " + (newest("CGC_MDL135_EnvGovernance_v0*.py", HERE) or Path("?")).name}
        except Exception:
            pass
    return {"core": set(FALLBACK_CORE_WHITELIST), "high": set(FALLBACK_HIGH_RISK), "hints": {}, "source": "內建保守退路(MDL135 缺席)"}


def pip_name(imp: str) -> str:
    return PIP_NAME.get(imp, imp)


def has_cuda() -> bool:
    return bool(shutil.which("nvidia-smi"))


def classify(imp: str, pol: dict) -> dict:
    """單件路由:(狀態, 目標境清單, 理由);NOT_APPLICABLE/MANUAL 不列計畫"""
    low = imp.lower()
    pkg = pip_name(imp)
    if imp in GPU_ONLY and not has_cuda():
        return {"state": "NOT_APPLICABLE", "targets": [], "why": "GPU 專屬且本機無 CUDA(nvidia-smi 缺)"}
    plat = PLATFORM_ONLY.get(imp)
    if plat:
        is_win = platform.system().lower().startswith("win")
        if (plat == "windows") != is_win:
            return {"state": "NOT_APPLICABLE", "targets": [], "why": "平台限定 " + plat + ",本機 " + platform.system()}
    if imp in MANUAL:
        return {"state": "MANUAL", "targets": [], "why": MANUAL[imp]}
    if low in pol["high"] or pkg.lower() in pol["high"]:
        return {"state": "PLAN", "targets": ["via_vrn", "via_vap"], "why": "高風險家族=只進家族境,永不入 base/via_core"}
    if low in pol["core"] or pkg.lower() in pol["core"]:
        return {"state": "PLAN", "targets": ["via_core", "via_vdf", "via_vrn", "via_vap"], "why": "via_core 白名單件(共用核心+三家族)"}
    return {"state": "PLAN", "targets": ["via_core", "via_vdf", "via_vrn", "via_vap"], "why": "通用算力/工具件→共用核心+三家族"}


# ---------------------------------------------------------------- 境
def env_roots(extra: str | None = None) -> list:
    out = []
    if extra:
        out.append(Path(extra))
    for e in (os.environ.get("VIA_ENV_ROOT"), os.environ.get("VIA_ENV_ROOTS")):
        for part in str(e or "").split(";"):
            if part.strip():
                out.append(Path(part.strip()))
    up = os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""
    if up:
        out += [Path(up) / "envs", Path(up) / "miniconda3" / "envs", Path(up) / "anaconda3" / "envs", Path(up) / ".virtualenvs"]
    return [p for p in out if p.exists()]


def find_envs(extra: str | None = None) -> dict:
    """家族鍵 → 境 python 路徑(別名序;找不到=None 誠實)"""
    found = {}
    roots = env_roots(extra)
    for fam in FAMILY_ENVS:
        found[fam] = None
        for name in ENV_ALIASES.get(fam, [fam]):
            for r in roots:
                for sub in ("Scripts/python.exe", "python.exe", "bin/python3", "bin/python"):
                    cand = r / name / sub
                    if cand.exists():
                        found[fam] = str(cand)
                        break
                if found[fam]:
                    break
            if found[fam]:
                break
    return found


PROBE = ("import importlib.util,json,sys\n"
         "names=json.loads(sys.argv[1])\n"
         "print(json.dumps({n: (importlib.util.find_spec(n) is not None) for n in names}))\n")


def probe_env(py: str, names: list, timeout: int = 120) -> dict:
    """以該境 python 探 find_spec(不 import=零副作用);失敗=空(誠實)"""
    try:
        r = subprocess.run([py, "-c", PROBE, json.dumps(names)], capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {}
    return {}


def _installer(py: str) -> list:
    """uv 優先(毫秒級);缺 uv 退 pip(同一境 python)"""
    if shutil.which("uv"):
        return ["uv", "pip", "install", "--python", py]
    return [py, "-m", "pip", "install"]


def install_one(py: str, pkg: str, timeout: int = 900) -> dict:
    cmd = _installer(py) + [pkg]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        tail = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        return {"pkg": pkg, "state": "OK" if r.returncode == 0 else "FAIL", "rc": r.returncode,
                "sec": round(time.time() - t0, 1), "note": (tail[-1][:160] if tail else ""), "via": cmd[0]}
    except subprocess.TimeoutExpired:
        return {"pkg": pkg, "state": "FAIL", "rc": -1, "sec": round(time.time() - t0, 1), "note": "逾時 " + str(timeout) + "s 終止(不卡斷)", "via": cmd[0]}
    except Exception as exc:
        return {"pkg": pkg, "state": "FAIL", "rc": -2, "sec": round(time.time() - t0, 1), "note": type(exc).__name__, "via": cmd[0]}


def gate_open() -> bool:
    return os.environ.get("VIA_NET_CONSENT") == "YES"


# ---------------------------------------------------------------- 計畫/執行
def build(extra_root: str | None = None, apply: bool = False, approve: bool = False, include_base: bool = False,
          timeout: int = 900, probe_timeout: int = 120, do_print: bool = True, envs: dict | None = None,
          install_fn=None, probe_fn=None, write: bool = True) -> dict:
    t0 = time.time()
    libs = roster()
    pol = policy()
    envs = envs if envs is not None else find_envs(extra_root)
    if include_base:
        envs = dict(envs)
        envs["base"] = sys.executable
    probe_fn = probe_fn or probe_env
    install_fn = install_fn or install_one

    routed = []
    for imp in libs:
        c = classify(imp, pol)
        routed.append({"imp": imp, "pkg": pip_name(imp), **c})
    plan_libs = [r for r in routed if r["state"] == "PLAN"]

    env_rep = []
    for fam in (list(envs.keys())):
        py = envs.get(fam)
        want = [r for r in plan_libs if fam in r["targets"] or fam == "base"]
        ent = {"env": fam, "python": py or "", "want": len(want), "have": 0, "missing": [], "state": "SKIP", "installs": []}
        if not py:
            ent["note"] = "境未找到(別名 " + ", ".join(ENV_ALIASES.get(fam, [fam])) + ";--env-root 可指定)"
            env_rep.append(ent)
            continue
        present = probe_fn(py, [r["imp"] for r in want], probe_timeout)
        if not present:
            ent["note"] = "探針失敗=誠實未知(不猜裝)"
            env_rep.append(ent)
            continue
        ent["have"] = sum(1 for k, v in present.items() if v)
        ent["missing"] = [r["pkg"] for r in want if not present.get(r["imp"], False)]
        ent["state"] = "OK" if not ent["missing"] else "PLAN"
        if apply and ent["missing"]:
            if not approve:
                ent["note"] = "--apply 需同時 --approve(授權閉環)"
            elif not gate_open():
                ent["note"] = "同意閘未開=拒裝(VIA_NET_CONSENT=YES;fail-closed 誠實)"
            else:
                for pkg in ent["missing"]:
                    r = install_fn(py, pkg, timeout)
                    ent["installs"].append(r)
                    if do_print:
                        print("  [" + r["state"] + "] " + fam + " ← " + pkg + " · " + str(r["sec"]) + "s" + (" · " + r["note"] if r.get("note") else ""), flush=True)
                ok = sum(1 for r in ent["installs"] if r["state"] == "OK")
                ent["state"] = "OK" if ok == len(ent["installs"]) else ("PART" if ok else "FAIL")
        env_rep.append(ent)

    rep = {"engine": ENGINE_TAG, "stamp": datetime.now().strftime("%Y%m%d_%H%M%S"), "policy_source": pol["source"],
           "libs_total": len(libs), "plan_libs": len(plan_libs),
           "not_applicable": [r["imp"] + "(" + r["why"] + ")" for r in routed if r["state"] == "NOT_APPLICABLE"],
           "manual": [r["imp"] + "(" + r["why"] + ")" for r in routed if r["state"] == "MANUAL"],
           "routed": routed, "envs": env_rep, "apply": apply, "approve": approve, "include_base": include_base,
           "gate": gate_open(), "rules": RULES}
    rep["state"] = ("OK" if all(e["state"] in ("OK", "SKIP") for e in env_rep) and env_rep else
                    ("FAIL" if any(e["state"] == "FAIL" for e in env_rep) else "PLAN"))
    rep["elapsed_s"] = round(time.time() - t0, 1)
    if write:
        REP.mkdir(parents=True, exist_ok=True)
        (REP / ("ACCEL_IMPORT_" + rep["stamp"] + ".json")).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        PAGE.parent.mkdir(parents=True, exist_ok=True)
        PAGE.write_text(render(rep), encoding="utf-8")
        BOOK.write_text(json.dumps({"engine": ENGINE_TAG, "libs_total": rep["libs_total"], "plan_libs": rep["plan_libs"],
                                    "family_envs": FAMILY_ENVS, "aliases": ENV_ALIASES, "rules": RULES,
                                    "last": rep["stamp"], "last_state": rep["state"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        digest(rep)
        if write:
            print("  [頁] " + str(PAGE) + "\n  [冊] " + str(BOOK))
    return rep


def digest(rep: dict) -> int:
    print("VIA ACCEL IMPORT · " + rep["stamp"] + " · " + rep["state"] + " · 冊 " + str(rep["libs_total"])
          + " 件 · 可計畫 " + str(rep["plan_libs"]) + " · 政策 " + rep["policy_source"]
          + " · " + ("APPLY" if rep["apply"] else "PLAN 唯讀") + " · 同意閘 " + ("開" if rep["gate"] else "關"))
    for e in rep["envs"]:
        line = "  " + e["state"].ljust(5) + " " + e["env"].ljust(9) + "已裝 " + str(e["have"]) + "/" + str(e["want"])
        if e["missing"]:
            line += " · 缺 " + str(len(e["missing"])) + ":" + ", ".join(e["missing"][:8]) + ("…" if len(e["missing"]) > 8 else "")
        if e.get("note"):
            line += " · " + e["note"]
        print(line)
    if rep["not_applicable"]:
        print("  [不適用] " + "; ".join(rep["not_applicable"]))
    if rep["manual"]:
        print("  [需手動] " + "; ".join(rep["manual"]))
    return 0 if rep["state"] in ("OK", "PLAN") else 1


# ---------------------------------------------------------------- 頁
def _b(s: str) -> str:
    c = {"OK": "gr", "PLAN": "ye", "PART": "ye", "SKIP": "gy", "MANUAL": "ye", "NOT_APPLICABLE": "gy", "FAIL": "rd"}.get(s, "gy")
    return '<span class="b ' + c + '">' + html.escape(s) + "</span>"


def render(r: dict) -> str:
    e = html.escape
    erows = "".join('<tr><td class="m">' + e(x["env"]) + '</td><td class="c">' + _b(x["state"]) + '</td><td class="c m">'
                    + str(x["have"]) + "/" + str(x["want"]) + '</td><td class="dim">' + e(", ".join(x["missing"])[:400] or "—")
                    + '</td><td class="dim">' + e(str(x.get("note", ""))[:120]) + "</td></tr>" for x in r["envs"])
    rrows = "".join('<tr><td class="m">' + e(x["imp"]) + '</td><td class="m">' + e(x["pkg"]) + '</td><td class="c">' + _b(x["state"])
                    + '</td><td class="m">' + e(", ".join(x["targets"]) or "—") + '</td><td class="dim">' + e(x["why"]) + "</td></tr>"
                    for x in r["routed"])
    head = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>VIA · 加速器套件導入閘</title><style>:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}*{box-sizing:border-box}"
            "body{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}"
            ".wrap{max-width:1300px;margin:0 auto;padding:18px 14px 48px}h1{font-size:14px;margin:0}.sub{color:var(--mu);margin:3px 0 14px}"
            "h2{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}.nav a{color:#7dd3fc;margin-right:12px;text-decoration:none}"
            ".kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:14px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}.kpi .n{font-size:16px;font-weight:600}.kpi .l{font-size:10px;color:var(--mu)}"
            "table{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}th{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}td{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}td.c{text-align:center}.m{font-family:ui-monospace,Consolas,monospace;font-size:10px}.dim{color:var(--mu)}"
            ".b{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}.gr{background:#064e3b;color:#34d399;border-color:#059669}.ye{background:#78350f;color:#fde047;border-color:#d97706}.rd{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}.gy{background:#1f2937;color:#9ca3af;border-color:#374151}"
            ".note{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}"
            "@media(max-width:700px){table,thead,tbody,tr,td,th{display:block}thead{display:none}td{border:0;padding:2px 6px}tr{border-bottom:1px solid var(--line);padding:6px 0}}</style></head><body><div class=\"wrap\">")
    body = ("<h1>VIA ACCEL IMPORT · 加速器套件導入閘 · via_core + via_ 家族境</h1>"
            '<p class="sub">' + e(r["engine"]) + " · " + e(r["stamp"]) + " · 政策 " + e(r["policy_source"]) + " · "
            + ("APPLY" if r["apply"] else "PLAN 唯讀") + " · 同意閘 " + ("開" if r["gate"] else "關") + " · " + str(r.get("elapsed_s", "")) + " s</p>"
            '<p class="nav"><a href="VIA_UI_ParallelLanes_v0100.html">道</a><a href="VIA_UI_ProductGate_v0100.html">產</a>'
            '<a href="VIA_UI_ProjectCompletion_v0100.html">竣</a><a href="VIA_UI_VDFArchitecture_v0100.html">架</a></p>'
            '<div class="kpis"><div class="kpi"><div class="n">' + _b(r["state"]) + '</div><div class="l">state</div></div>'
            '<div class="kpi"><div class="n">' + str(r["libs_total"]) + '</div><div class="l">冊件數(Celeritas)</div></div>'
            '<div class="kpi"><div class="n">' + str(r["plan_libs"]) + '</div><div class="l">可計畫件</div></div>'
            '<div class="kpi"><div class="n">' + str(len(r["not_applicable"])) + " · " + str(len(r["manual"])) + '</div><div class="l">不適用 · 需手動</div></div></div>'
            "<h2>ENVS — 逐境已裝/缺(探針=find_spec,零副作用)</h2>"
            '<table><colgroup><col style="width:12%"><col style="width:8%"><col style="width:10%"><col style="width:48%"><col style="width:22%"></colgroup>'
            "<thead><tr><th>env</th><th>state</th><th>已裝/應有</th><th>缺件(pip 名)</th><th>note</th></tr></thead><tbody>" + erows + "</tbody></table>"
            "<h2>ROUTING — 88 件逐件路由(MDL135 規範;高風險永不入 base)</h2>"
            '<table><colgroup><col style="width:13%"><col style="width:17%"><col style="width:12%"><col style="width:26%"><col style="width:32%"></colgroup>'
            "<thead><tr><th>import</th><th>pip</th><th>state</th><th>targets</th><th>why</th></tr></thead><tbody>" + rrows + "</tbody></table>"
            '<div class="note">' + "<br>".join(e(x) for x in r["rules"]) + "</div></div></body></html>")
    return head + body


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    global REP, PAGE, BOOK
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + note)
        if not cond:
            fails.append(name)

    libs = roster()
    chk("① 冊自 Celeritas 尾版 _LIB_MAP 逐字解析(≥80 件;含 numpy/polars/duckdb;零發明)",
        len(libs) >= 80 and all(k in libs for k in ("numpy", "polars", "duckdb", "orjson", "numba")), "(冊 " + str(len(libs)) + " 件)")
    pol = policy()
    chk("② 路由政策正本=MDL135 尾版(core_whitelist/high_risk/purpose_hints;缺席=保守退路誠實標)",
        bool(pol["core"]) and bool(pol["high"]) and ("MDL135" in pol["source"] or "退路" in pol["source"]), "(" + pol["source"] + ")")
    c_core = classify("duckdb", pol)
    c_high = classify("torch", pol)
    c_gen = classify("numba", pol)
    chk("③ 路由三律(白名單件→via_core+三家族;高風險→只家族境不入 base/via_core;通用算力→核心+三家族)",
        "via_core" in c_core["targets"] and c_high["state"] == "PLAN" and "via_core" not in c_high["targets"]
        and "base" not in c_high["targets"] and "via_core" in c_gen["targets"])
    c_gpu = classify("cudf", pol)
    c_man = classify("talib", pol)
    c_plat = classify("uvloop" if platform.system().lower().startswith("win") else "winloop", pol)
    chk("④ 誠實不空轉(GPU 無卡=NOT_APPLICABLE;需系統二進位=MANUAL;平台不符=NOT_APPLICABLE;皆零目標)",
        (c_gpu["state"] == "NOT_APPLICABLE" or has_cuda()) and c_man["state"] == "MANUAL"
        and c_plat["state"] == "NOT_APPLICABLE" and not c_man["targets"] and not c_plat["targets"])
    chk("⑤ pip 名對映(cv2→opencv-contrib-python 同 MDL135 換錨;PIL→Pillow;skimage→scikit-image;同名者原樣)",
        pip_name("cv2") == "opencv-contrib-python" and pip_name("PIL") == "Pillow" and pip_name("skimage") == "scikit-image" and pip_name("numpy") == "numpy")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        _s = (REP, PAGE, BOOK)
        REP, PAGE, BOOK = tdp / "rep", tdp / "p.html", tdp / "b.json"
        calls = []

        def fake_probe(py, names, timeout=120):
            return {n: (n in ("numpy", "pandas")) for n in names}

        def fake_install(py, pkg, timeout=900):
            calls.append((py, pkg))
            return {"pkg": pkg, "state": "OK" if pkg != "polars" else "FAIL", "rc": 0, "sec": 0.1, "note": "", "via": "fake"}
        envs = {"via_core": "PY_CORE", "via_vdf": "PY_VDF", "via_vrn": None, "via_vap": None}
        p1 = build(envs=envs, probe_fn=fake_probe, install_fn=fake_install, do_print=False, write=True)
        chk("⑥ 計畫唯讀(未 --apply=零安裝;境未找到=SKIP 具名別名;已裝 numpy/pandas 不重裝)",
            not calls and p1["state"] == "PLAN" and all(e["state"] in ("PLAN", "SKIP") for e in p1["envs"])
            and any(e["env"] == "via_vrn" and e["state"] == "SKIP" and "別名" in e.get("note", "") for e in p1["envs"])
            and all("numpy" not in e["missing"] for e in p1["envs"]))
        _g = os.environ.get("VIA_NET_CONSENT")
        os.environ.pop("VIA_NET_CONSENT", None)
        p2 = build(envs=envs, probe_fn=fake_probe, install_fn=fake_install, apply=True, approve=True, do_print=False, write=False)
        chk("⑦ fail-closed(同意閘未開=拒裝零呼叫;並印指令)", not calls and all("同意閘" in (e.get("note") or "") for e in p2["envs"] if e["python"]))
        os.environ["VIA_NET_CONSENT"] = "YES"
        p3 = build(envs=envs, probe_fn=fake_probe, install_fn=fake_install, apply=True, approve=False, do_print=False, write=False)
        chk("⑧ 授權閉環(--apply 無 --approve=零安裝並註明)", not calls and all("--approve" in (e.get("note") or "") for e in p3["envs"] if e["python"]))
        p4 = build(envs=envs, probe_fn=fake_probe, install_fn=fake_install, apply=True, approve=True, do_print=False, write=True)
        if _g is None:
            os.environ.pop("VIA_NET_CONSENT", None)
        else:
            os.environ["VIA_NET_CONSENT"] = _g
        t = PAGE.read_text(encoding="utf-8")
        base_touched = any(e["env"] == "base" for e in p4["envs"])
        chk("⑨ 真裝道+base 零觸碰+頁冊(逐件逐境呼叫;polars 敗=PART 不假綠;頁含 ENVS/ROUTING+@media+零 CDN)",
            calls and not base_touched and any(e["state"] == "PART" for e in p4["envs"])
            and all(x in t for x in ("ENVS", "ROUTING", "@media")) and "https://" not in t and BOOK.exists())
        REP, PAGE, BOOK = _s
    src = Path(__file__).read_text(encoding="utf-8")
    print("  [計] 九檢 OK " + str(9 - len(fails)) + " · FAIL " + str(len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 加速器套件導入閘(" + ENGINE_TAG + ")· 九檢自測 ===")
        return selftest()

    def opt(name, default=None):
        return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default
    if a and a[0] == "digest":
        hits = sorted(REP.glob("ACCEL_IMPORT_*.json")) if REP.exists() else []
        if not hits:
            print("VIA ACCEL IMPORT · 無存證(via-accel-import)")
            return 1
        return digest(json.loads(hits[-1].read_text(encoding="utf-8")))
    rep = build(extra_root=opt("--env-root"), apply="--apply" in a, approve="--approve" in a,
                include_base="--include-base" in a, timeout=int(opt("--timeout", "900")))
    if "--open" in a and os.environ.get("VIA_NO_OPEN", "0") != "1":
        try:
            import webbrowser
            webbrowser.open(PAGE.as_uri())
        except Exception:
            pass
    return 0 if rep["state"] in ("OK", "PLAN") else 1


if __name__ == "__main__":
    sys.exit(main())
