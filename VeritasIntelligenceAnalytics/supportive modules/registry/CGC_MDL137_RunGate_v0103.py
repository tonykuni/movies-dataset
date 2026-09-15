#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL137_RunGate v0103 — VDF/VRN/VAP 能跑閘(批511 併線)
v0102→v0103(批511 併線:並行線 v0102 假綠修 + 本線 批509 解譯器探針):操作員實錄 via_vdf_312/via_vrn_312 全站 0.2s `SRE module mismatch`,舊版判「必要庫缺」開補庫令=判錯的紅燈。
  +interp_check(先於庫探針):家族境 python -c "import re,json,sys" 失敗=解譯器壞(STDLIB_MISMATCH/STDLIB_MISSING/STARTUP_FAIL/NOT_FOUND),-E/-S/-I 三試分病因
  (環境變數 PYTHONHOME/PYTHONPATH · site 層 .pth/sitecustomize · venv 本體 pyvenv.cfg home),存證 pyvenv.cfg 與現值;RED 理由=解譯器壞(不列缺庫);補庫 SKIP;不探庫不跑站;
  次步=診斷+重建境(候裁=操作員的手;via-envrecover 印令)。十二檢(+⑪ 探針三試 ⑫ 判定/補庫/次步)。
v0101→v0102(批508 結案驗收):修掉兩種假綠——家族零自測站、站檔缺席(SKIP)以前都能判 GREEN。
  run/fast/all 現在要求每個受測家族至少一站且每站 OK；probe 仍只驗套件，不偽稱跑過引擎。
v0100→v0101(批476 操作員令「所有 PY 檔案都要加上加速器」):
  run_station 的子行程 env 前置 <VIA>/supportive modules/bootstrap(sitecustomize.py),
  每一站起跑就綁加速器;VIA_FAMILY 只在站上有講時才設。同意閘照舊不設。

CGC_MDL137_RunGate v0100 — VDF/VRN/VAP 能跑閘(批384)
====================================================================
操作員令(批384):「以此為中央控管,將 session_01R2d69oa1AGvnPVwjSUdSv5(VIA系統後續工作;分支
claude/via-system-followup-tz7k9t @ c14d428 = main = 本分支基底;0 未併)整合完畢;vdf vrn 能跑」。
「能跑」的誠實定義=以家族境 python 真跑引擎自測(不是 base 有沒有裝):
  ① python_for(family):MDL136 EntryBridge resolve_env_python(VIA_PY_<FAMILY> 覆寫 > 境根×Baseline
     別名 via_vdf_312/via_vrn_312/via_vap_312 > base 退路=誠實 BASE_FALLBACK)
  ② probe:家族境 python 逐庫 import(vdf:duckdb/pandas/numpy/pyarrow 必要;vrn:fitz/duckdb/plotly 必要(批389 +plotly);
     vap:pandas/matplotlib/duckdb/plotly 必要;其餘選配)→ 缺件=誠實列 + 修法(REPAIR_BASE/ENSURE_ENV)
  ③ run:SelftestGrid 尾版 battery 中家族站(functional modules/VDF|VRN|VAP 且 --selftest)改以家族境
     python 執行(--fast 每族 3 站;預設 8 站;--all 全站)→ OK/FAIL/TIMEOUT + 尾行存證
  ④ 判定:族內任一 FAIL=RED;base 退路或必要庫缺=YELLOW(能跑但非本位);全綠=GREEN;總判=最壞
  ⑤ 鏈路燈:DeckServer 尾版任務冊 argv[0] 家族路由(v0129 起)=ParallelLanes/CompletionAutomator/
     MasterControl 同律;VIA.ps1 開機鏈仍 base python(誠實列)
落 VIA_Reports/rungate/RUNGATE_latest.json + .html(零 CDN)+ logs/rungate.log(JSONL)。
律:只增不減;正本零觸碰(引擎/SelftestGrid/EntryBridge 皆唯讀複用=Zero-Hydra);誠實三態;
    零網路(引擎自測皆零觸網站;VIA_NET_CONSENT 不設);尾版律(glob 尾版,嚴禁寫死版號)。
  ⑥ 補庫(批387):家族境在而必要庫缺 → 印 uv pip install --python <家族境> <缺件>(import 名→pip 名對映 fitz→pymupdf 等);
     --approve-install 才裝(觸網;只增不減;只裝進家族境,base 退路一律不裝功能件)→ 裝後重探
用法:python3 CGC_MDL137_RunGate_v0103.py run [--fast|--all] [--family vdf,vrn,vap] [--approve-install] [--json] [--quiet]
      | probe [--family …] | status | --selftest
批387 工作站實錄:via-rungate --family vrn 把 vrn 當動詞印用法(旗標值誤判動詞)→ 動詞白名單;via_vrn_312 無 duckdb → VRN 引擎
ModuleNotFoundError → --approve-install 補庫道
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

import datetime as _dt
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "rungate"
LOG = VIA / "logs" / "rungate.log"
FAMILY_DIRS = {"vdf": "functional modules/VDF", "vrn": "functional modules/VRN", "vap": "functional modules/VAP"}
FAMILY_LIBS = {
    "vdf": {"required": ["duckdb", "pandas", "numpy", "pyarrow"], "optional": ["polars", "plotly", "yfinance", "openpyxl"]},
    "vrn": {"required": ["fitz", "duckdb", "plotly"], "optional": ["docx", "pdfplumber", "markitdown", "pandas", "openpyxl", "bs4", "lxml"]},   # 批389:plotly 入必要(VRN 控制塔互動圖;工作站實錄「誠實降級:plotly 未安裝」)
    "vap": {"required": ["pandas", "matplotlib", "duckdb", "plotly"], "optional": ["seaborn", "numpy", "talib", "pyarrow"]},
}
FAST_N, DEFAULT_N = 3, 8
VERBS = ("run", "probe", "status")
PIP_NAMES = {"fitz": "pymupdf", "docx": "python-docx", "bs4": "beautifulsoup4", "PIL": "pillow", "talib": "TA-Lib", "yaml": "pyyaml", "sklearn": "scikit-learn", "cv2": "opencv-contrib-python"}
PROBE_SRC = ("import importlib, json, sys\n"
             "out = {}\n"
             "for n in sys.argv[1:]:\n"
             "    try:\n"
             "        m = importlib.import_module(n)\n"
             "        out[n] = str(getattr(m, '__version__', None) or getattr(m, 'version', None) or 'ok')\n"
             "    except Exception as e:\n"
             "        out[n] = None\n"
             "print(json.dumps(out))\n")

INTERP_SRC = ("import re, json, sys, os\n"
              "print('@@INTERP@@' + json.dumps({'version': sys.version.split()[0], 'exe': sys.executable, 'prefix': sys.prefix, "
              "'base_prefix': getattr(sys, 'base_prefix', ''), 'path': sys.path[:4]}))\n")


def interp_check(py: str, timeout: int = 30, environ: dict | None = None) -> dict:
    """批509:解譯器健康(先於庫探針)。import re 都不行=解譯器壞(標準庫錯配),不是缺庫;-E/-S/-I 三試分辨病因。"""
    env = dict(environ if environ is not None else os.environ)
    env["PYTHONUTF8"] = "1"
    env.pop("VIA_NET_CONSENT", None)

    def _run(extra):
        try:
            r = subprocess.run([py, *extra, "-c", INTERP_SRC], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, env=env,
                               encoding="utf-8", errors="replace")
            return r.returncode, (r.stdout or ""), (r.stderr or "")
        except Exception as exc:
            return -1, "", f"{type(exc).__name__}:{str(exc)[:120]}"
    rc, out, err = _run([])
    info = {"state": "OK", "kind": "", "cause": "", "trials": {}, "err": "",
            "env": {k: (env.get(k) or "")[:160] for k in ("PYTHONHOME", "PYTHONPATH") if env.get(k)}, "pyvenv": {}, "pyvenv_path": ""}
    line = next((l for l in out.splitlines() if l.startswith("@@INTERP@@")), "")
    if rc == 0 and line:
        try:
            info.update(json.loads(line[len("@@INTERP@@"):]))
        except Exception:
            pass
        return info
    tail = "\n".join([l for l in (err or out).strip().splitlines() if l.strip()][-3:])[:400]
    info.update(state="BROKEN", err=tail)
    low = tail.lower()
    info["kind"] = ("STDLIB_MISMATCH" if ("sre module mismatch" in low or "magic" in low)
                    else "STDLIB_MISSING" if ("no module named" in low or "encodings" in low)
                    else "NOT_FOUND" if rc == -1 else "STARTUP_FAIL")
    for flag in ("-E", "-S", "-I"):
        rc2, o2, _e2 = _run([flag])
        info["trials"][flag] = bool(rc2 == 0 and "@@INTERP@@" in o2)
    tr = info["trials"]
    if tr.get("-E"):
        info["cause"] = "環境變數帶錯版標準庫(PYTHONHOME/PYTHONPATH;-E 即好)"
    elif tr.get("-S"):
        info["cause"] = "site 層帶錯版(.pth/sitecustomize/usercustomize;-S 即好)"
    elif tr.get("-I"):
        info["cause"] = "環境變數+site 皆有嫌疑(-I 才好)"
    else:
        info["cause"] = "venv 本體錯配(pyvenv.cfg home 指到被換掉/升級的 Python;三試皆壞)→ 重建境(候裁,你的手)"
    try:
        cfg = Path(py).resolve().parent.parent / "pyvenv.cfg"
        if cfg.exists():
            info["pyvenv_path"] = str(cfg)
            for l in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
                if "=" in l:
                    k, v = l.split("=", 1)
                    info["pyvenv"][k.strip()] = v.strip()[:160]
    except Exception:
        pass
    return info



def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _newest(root: Path, pat: str) -> Path | None:
    hits = sorted(root.glob(pat)) if root.exists() else []
    return hits[-1] if hits else None


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def log_event(kind: str, msg: str, **kw) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _dt.datetime.now().isoformat(timespec="seconds"), "kind": kind, "msg": msg, **kw}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _say(s: str, quiet: bool = False) -> None:
    if not quiet:
        try:
            print(s, flush=True)
        except (BrokenPipeError, UnicodeEncodeError):
            pass


# ---------------------------------------------------------------- ① 家族與 python
def family_of(path) -> str:
    s = str(path).replace("\\", "/")
    for fam, d in FAMILY_DIRS.items():
        if f"/{d}/" in s or s.endswith(f"/{d}"):
            return fam
    name = Path(s).name.lower()
    for fam in FAMILY_DIRS:
        if name.startswith(fam + "_"):
            return fam
    return "base"


def _bridge():
    p = _newest(HERE, "CGC_MDL136_EntryBridge_v*.py")
    if not p:
        return None
    try:
        spec = importlib.util.spec_from_file_location("entry_bridge_rungate", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["entry_bridge_rungate"] = m
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def python_for(family: str, roots: list | None = None, environ: dict | None = None) -> dict:
    """家族境 python(MDL136 正本解析;缺=base 退路誠實)"""
    if family == "base":
        return {"family": "base", "env": "BASE", "python": sys.executable, "source": "本解譯器", "state": "OK"}
    m = _bridge()
    if m is not None:
        try:
            return m.resolve_env_python(family, roots=roots, environ=environ)
        except Exception:
            pass
    e = environ if environ is not None else os.environ
    ov = (e.get(f"VIA_PY_{family.upper()}") or "").strip()
    if ov and Path(ov).exists():
        return {"family": family, "env": Path(ov).parent.parent.name, "python": ov, "source": f"env VIA_PY_{family.upper()}", "state": "OK"}
    return {"family": family, "env": "", "python": sys.executable, "source": "base 退路(MDL136 缺/境未見)", "state": "BASE_FALLBACK"}


# ---------------------------------------------------------------- ② 庫探針
def probe_libs(py: str, libs: list, timeout: int = 90) -> dict:
    """單一子程序逐庫 import(家族境 python);回 {lib: version|None};失敗=全 None(誠實)"""
    if not libs:
        return {}
    try:
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1"
        env["VIA_NO_OPEN"] = "1"
        r = subprocess.run([py, "-c", PROBE_SRC, *libs], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, env=env)
        line = [l for l in (r.stdout or "").splitlines() if l.strip().startswith("{")]
        if r.returncode == 0 and line:
            return json.loads(line[-1])
    except Exception:
        pass
    return {n: None for n in libs}


def pick_verb(a: list, default: str = "run") -> str:
    """動詞白名單(旗標值如 --family vrn 不得誤判為動詞;批387 實錄)"""
    return next((x for x in a if x in VERBS), default)


def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _newest(root: Path, pat: str) -> Path | None:
    hits = sorted(root.glob(pat)) if root.exists() else []
    return hits[-1] if hits else None


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def log_event(kind: str, msg: str, **kw) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _dt.datetime.now().isoformat(timespec="seconds"), "kind": kind, "msg": msg, **kw}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _say(s: str, quiet: bool = False) -> None:
    if not quiet:
        try:
            print(s, flush=True)
        except (BrokenPipeError, UnicodeEncodeError):
            pass


# ---------------------------------------------------------------- ① 家族與 python
def family_of(path) -> str:
    s = str(path).replace("\\", "/")
    for fam, d in FAMILY_DIRS.items():
        if f"/{d}/" in s or s.endswith(f"/{d}"):
            return fam
    name = Path(s).name.lower()
    for fam in FAMILY_DIRS:
        if name.startswith(fam + "_"):
            return fam
    return "base"


def _bridge():
    p = _newest(HERE, "CGC_MDL136_EntryBridge_v*.py")
    if not p:
        return None
    try:
        spec = importlib.util.spec_from_file_location("entry_bridge_rungate", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["entry_bridge_rungate"] = m
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def python_for(family: str, roots: list | None = None, environ: dict | None = None) -> dict:
    """家族境 python(MDL136 正本解析;缺=base 退路誠實)"""
    if family == "base":
        return {"family": "base", "env": "BASE", "python": sys.executable, "source": "本解譯器", "state": "OK"}
    m = _bridge()
    if m is not None:
        try:
            return m.resolve_env_python(family, roots=roots, environ=environ)
        except Exception:
            pass
    e = environ if environ is not None else os.environ
    ov = (e.get(f"VIA_PY_{family.upper()}") or "").strip()
    if ov and Path(ov).exists():
        return {"family": family, "env": Path(ov).parent.parent.name, "python": ov, "source": f"env VIA_PY_{family.upper()}", "state": "OK"}
    return {"family": family, "env": "", "python": sys.executable, "source": "base 退路(MDL136 缺/境未見)", "state": "BASE_FALLBACK"}


# ---------------------------------------------------------------- ② 庫探針
def probe_libs(py: str, libs: list, timeout: int = 90) -> dict:
    """單一子程序逐庫 import(家族境 python);回 {lib: version|None};失敗=全 None(誠實)"""
    if not libs:
        return {}
    try:
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1"
        env["VIA_NO_OPEN"] = "1"
        r = subprocess.run([py, "-c", PROBE_SRC, *libs], capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, env=env)
        line = [l for l in (r.stdout or "").splitlines() if l.strip().startswith("{")]
        if r.returncode == 0 and line:
            return json.loads(line[-1])
    except Exception:
        pass
    return {n: None for n in libs}


def pick_verb(a: list, default: str = "run") -> str:
    """動詞白名單(旗標值如 --family vrn 不得誤判為動詞;批387 實錄)"""
    return next((x for x in a if x in VERBS), default)


def install_missing(fam: str, pyinfo: dict, missing: list, approve: bool, timeout: int = 900) -> dict:
    """家族境補庫(批387):uv pip install --python <家族境> <缺件>;無 uv 退 pip;--approve-install 才裝;base 退路不裝功能件"""
    if not missing:
        return {"state": "NONE"}
    if (pyinfo.get("interp") or {}).get("state") == "BROKEN":       # 批509:解譯器壞=補庫是錯藥
        return {"state": "SKIP", "note": f"{fam} 境解譯器壞({(pyinfo.get('interp') or {}).get('kind')}):不補庫(import re 都不行);先修解譯器(見次步)"}
    if pyinfo.get("state") != "OK":
        return {"state": "SKIP", "note": f"{fam} 家族境未見=不往 base 裝功能件(建境:via-envgov apply --approve;或設 VIA_PY_{fam.upper()})"}
    pkgs = [PIP_NAMES.get(n, n) for n in missing]
    import shutil as _sh
    uv = _sh.which("uv") or next((str(c) for c in (Path.home() / ".local" / "bin" / "uv.exe", Path.home() / ".local" / "bin" / "uv") if c.exists()), None)
    cmd = ([uv, "pip", "install", "--python", pyinfo["python"], *pkgs] if uv else [pyinfo["python"], "-m", "pip", "install", *pkgs])
    idx = (os.environ.get("VIA_PIP_INDEX_URL") or "").strip()
    if idx:
        cmd += ["--index-url", idx]
    if not approve:
        return {"state": "PLAN", "cmd": " ".join(cmd), "note": "via-rungate --approve-install 才裝(觸網;只增不減;只裝進家族境)"}
    try:
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1"
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, env=env, encoding="utf-8", errors="replace")
        tail = [l for l in ((r.stdout or "") + (r.stderr or "")).strip().splitlines() if l.strip()][-2:]
        log_event("INSTALL", " ".join(cmd), rc=r.returncode, family=fam)
        return {"state": "OK" if r.returncode == 0 else "FAIL", "cmd": " ".join(cmd), "rc": r.returncode, "tail": [t[:160] for t in tail]}
    except Exception as exc:
        return {"state": "FAIL", "cmd": " ".join(cmd), "note": str(exc)[:160]}


# ---------------------------------------------------------------- ③ 站冊(SelftestGrid 尾版 battery 複用)
def grid_stations() -> list:
    p = _newest(HERE, "CGC_MDL064_SelftestGrid_v*.py")
    if not p:
        return []
    try:
        spec = importlib.util.spec_from_file_location("selftest_grid_rungate", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["selftest_grid_rungate"] = m
        spec.loader.exec_module(m)
        return list(m.battery(True))
    except Exception:
        return []


def family_stations(battery: list, family: str, limit: int | None) -> list:
    """家族站=路徑落家族夾且 --selftest/--self-test;同檔去重;取尾(引擎編號最新)limit 站"""
    seen, out = set(), []
    for b in battery:
        pth = b.get("path")
        if not pth or pth == "PYCODE" or family_of(pth) != family:
            continue
        if not any(str(a) in ("--selftest", "--self-test") for a in (b.get("args") or [])):
            continue
        key = str(pth)
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": b.get("name", ""), "path": str(pth), "args": list(b.get("args") or []), "timeout": int(b.get("timeout") or 300)})
    out.sort(key=lambda s: Path(s["path"]).name)
    return out[-limit:] if limit else out


def run_station(py: str, st: dict) -> dict:
    p = Path(st["path"])
    if not p.exists():
        return {"name": st["name"], "file": p.name, "state": "SKIP", "note": "引擎缺", "secs": 0}
    env = dict(os.environ)
    env.update({"PYTHONUTF8": "1", "VIA_NO_OPEN": "1", "PYTHONIOENCODING": "utf-8"})
    env.pop("VIA_NET_CONSENT", None)
    # 批476 啟動層注入:站的子行程起跑就綁加速器(sitecustomize 住 bootstrap/;零引擎改動)。
    # 家族只在站上有講時才設;沒講就不猜(網路件只掛 vdf)。同意閘照上一行的規矩:不設。
    _boot = VIA / "supportive modules" / "bootstrap"
    if _boot.is_dir():
        _prev = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(_boot) + (os.pathsep + _prev if _prev else "")
    env["VIA_ROOT"] = str(VIA)
    if st.get("family"):
        env["VIA_FAMILY"] = str(st["family"]).lower()
    t0 = time.time()
    try:
        r = subprocess.run([py, str(p), *st["args"]], capture_output=True, text=True, timeout=st["timeout"], stdin=subprocess.DEVNULL, cwd=str(p.parent), env=env,
                           encoding="utf-8", errors="replace")
        secs = round(time.time() - t0, 1)
        tail = [l for l in ((r.stdout or "") + (r.stderr or "")).strip().splitlines() if l.strip()][-2:]
        return {"name": st["name"], "file": p.name, "state": "OK" if r.returncode == 0 else "FAIL", "rc": r.returncode, "secs": secs, "tail": [t[:160] for t in tail]}
    except subprocess.TimeoutExpired:
        return {"name": st["name"], "file": p.name, "state": "TIMEOUT", "secs": round(time.time() - t0, 1), "note": f"逾時 {st['timeout']}s(不卡斷;kill)"}
    except Exception as exc:
        return {"name": st["name"], "file": p.name, "state": "FAIL", "secs": round(time.time() - t0, 1), "note": str(exc)[:160]}


# ---------------------------------------------------------------- ④ 判定/報告
def verdict_for(pyinfo: dict, libs: dict, required: list, results: list,
                require_results: bool = True) -> tuple[str, list]:
    """判家族能跑燈。

    run 模式的「沒有測到」不能等同「全部通過」：零站或 SKIP 都是證據缺口，
    必須 RED。probe 模式明示 ``require_results=False``，只回答套件探針。
    """
    reasons = []
    it = pyinfo.get("interp") or {}
    if it.get("state") == "BROKEN":                        # 批509:解譯器壞=RED,理由是解譯器不是缺庫(判錯的紅燈與假綠同罪)
        reasons.append(f"解譯器壞({it.get('kind')}):{it.get('cause')}")
        fails = [r["file"] for r in results if r.get("state") in ("FAIL", "TIMEOUT")]
        if fails:
            reasons.append("引擎自測 FAIL/TIMEOUT(同因):" + ",".join(fails))
        return "RED", reasons
    bad = [r for r in results if r.get("state") != "OK"]
    if require_results and not results:
        reasons.append("家族自測站為 0=沒有通過證據")
        v = "RED"
    elif bad:
        reasons.append("引擎自測非 OK:" + ",".join(
            f"{r.get('file', '?')}({r.get('state', '?')})" for r in bad))
        v = "RED"
    else:
        v = "GREEN"
    miss = [n for n in required if libs.get(n) is None]
    if miss:
        reasons.append("必要庫缺:" + ",".join(miss))
        v = "RED" if v == "RED" else "YELLOW"
    if pyinfo.get("state") != "OK":
        reasons.append("家族境未見=base 退路(能跑≠本位;via-envgov apply --approve 建境)")
        v = "RED" if v == "RED" else "YELLOW"
    return v, reasons


def chain_lamps() -> list:
    out = []
    deck = _newest(HERE, "CGC_MDL095_DeckServer_v*.py")
    if deck:
        txt = deck.read_text(encoding="utf-8", errors="replace")
        ok = "_py(\"vdf\")" in txt or "_py('vdf')" in txt
        out.append({"layer": "DeckServer", "lamp": "GREEN" if ok else "YELLOW", "msg": f"{deck.name} 任務冊 argv[0] {'家族路由(ParallelLanes/CompletionAutomator/MasterControl 同律)' if ok else '仍 base python(升 v0129+ 才路由)'}"})
    reg = _newest(VIA, "Register-VIA-Commands-v*.ps1")
    if reg:
        txt = reg.read_text(encoding="utf-8", errors="replace")
        n = txt.count("Get-VIAEnvPython")
        out.append({"layer": "Register", "lamp": "GREEN" if n >= 12 else "YELLOW", "msg": f"{reg.name} 短令家族路由 Get-VIAEnvPython ×{n}"})
    vp = VIA / "VIA.ps1"
    if vp.exists():
        out.append({"layer": "VIA.ps1", "lamp": "YELLOW", "msg": "開機鏈 Start-Process python=base(正本零觸碰;引擎能跑以 via-entry/via-rungate/短令為準)"})
    return out


def render_html(rep: dict) -> str:
    col = {"GREEN": "#34d399", "YELLOW": "#fde047", "RED": "#fca5a5", "GREY": "#94a3b8"}
    rows = ""
    for fam, f in rep["families"].items():
        libs = " ".join(f"{n}:{'✓' if v else '✗'}" for n, v in f["libs"].items())
        eng = "".join(f"<tr><td></td><td>{html.escape(r['file'])}</td><td style='color:{col.get('GREEN' if r['state'] == 'OK' else ('GREY' if r['state'] == 'SKIP' else 'RED'))}'>{r['state']}</td><td>{r.get('secs', 0)}s {html.escape(' | '.join(r.get('tail') or []) or r.get('note', ''))}</td></tr>" for r in f["results"])
        rows += (f"<tr><td style='color:{col.get(f['verdict'], '#ddd')}'><b>{f['verdict']}</b></td><td><b>{fam}</b></td><td>{html.escape(f['python']['python'])} ({html.escape(f['python']['state'])})</td>"
                 f"<td>{html.escape(libs)}<br>{html.escape('; '.join(f['reasons']) or '—')}</td></tr>{eng}")
    chains = "".join(f"<tr><td style='color:{col.get(c['lamp'], '#ddd')}'>{c['lamp']}</td><td>{html.escape(c['layer'])}</td><td colspan='2'>{html.escape(c['msg'])}</td></tr>" for c in rep["chains"])
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>VIA 能跑閘 · RunGate</title><style>body{background:#0f172a;color:#f8fafc;font:11px/1.35 -apple-system,'Segoe UI',Roboto,Arial,sans-serif;padding:12px}"
            "table{border-collapse:collapse;width:100%}td,th{border:1px solid #334155;padding:3px 6px;text-align:left;vertical-align:top}th{background:#1e293b}</style></head><body>"
            f"<h1 style='font-size:14px;margin:0 0 6px'>VDF/VRN/VAP 能跑閘 · {html.escape(rep['verdict'])} · {html.escape(rep['ts'])} · 模式 {html.escape(rep['mode'])}</h1>"
            "<div style='color:#94a3b8;margin-bottom:8px'>能跑=家族境 python 真跑引擎自測;零網路;零 CDN;正本零觸碰</div>"
            f"<table><tr><th>燈</th><th>族/引擎</th><th>python/狀態</th><th>庫/原因/尾行</th></tr>{rows}<tr><th colspan='4'>鏈路</th></tr>{chains}</table></body></html>")


def run(families: list | None = None, mode: str = "default", do_print: bool = True, quiet: bool = False, reports: Path = OUT,
        battery: list | None = None, python_fn=None, probe_fn=None, run_fn=None, chains_fn=None, approve_install: bool = False, install_fn=None, interp_fn=None) -> dict:
    q = quiet or not do_print
    families = families or list(FAMILY_DIRS)
    limit = {"fast": FAST_N, "default": DEFAULT_N, "all": None}.get(mode, DEFAULT_N)
    battery = battery if battery is not None else (grid_stations() if mode != "probe" else [])
    python_fn = python_fn or python_for
    probe_fn = probe_fn or probe_libs
    run_fn = run_fn or run_station
    chains_fn = chains_fn or chain_lamps
    install_fn = install_fn or install_missing
    rep = {"schema": "VIA.RunGate.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "mode": mode, "families": {}, "chains": [], "verdict": "GREEN"}
    _say(f"=== [via-rungate] 能跑閘 · 模式 {mode} · 族 {','.join(families)}(家族境 python 真跑引擎自測;零網路)===", q)
    worst = 0
    order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    for fam in families:
        pyinfo = python_fn(fam)
        spec = FAMILY_LIBS.get(fam, {"required": [], "optional": []})
        interp = (interp_fn or interp_check)(pyinfo["python"]) if pyinfo.get("python") else {"state": "SKIP"}
        pyinfo["interp"] = interp
        broken = interp.get("state") == "BROKEN"
        if broken:
            _say(f"  [INTERP ] {fam} 解譯器壞({interp.get('kind')}):{interp.get('cause')} · 三試 {interp.get('trials')} · {str(interp.get('err', ''))[-100:]}", q)
        libs = probe_fn(pyinfo["python"], spec["required"] + spec["optional"]) if not broken else {n: None for n in spec["required"] + spec["optional"]}
        inst = {"state": "NONE"} if not broken else {"state": "SKIP", "note": "解譯器壞:不補庫"}
        missing_req = [n for n in spec["required"] if libs.get(n) is None]
        if missing_req and not broken:
            inst = install_fn(fam, pyinfo, missing_req, approve_install)
            _say(f"  [{inst['state']:<5}] {fam} 補庫 {','.join(PIP_NAMES.get(n, n) for n in missing_req)}:{inst.get('cmd', '')} {inst.get('note', '')} {' | '.join(inst.get('tail') or [])}"[:220], q)
            if inst["state"] == "OK":
                libs = probe_fn(pyinfo["python"], spec["required"] + spec["optional"])
        sts = family_stations(battery, fam, limit) if (mode != "probe" and not broken) else []
        results = []
        for st in sts:
            r = run_fn(pyinfo["python"], st)
            results.append(r)
            _say(f"  [{r['state']:<7}] {fam} {r['file']} · {r.get('secs', 0)}s · {' | '.join(r.get('tail') or []) or r.get('note', '')}"[:200], q)
        v, reasons = verdict_for(pyinfo, libs, spec["required"], results,
                                 require_results=(mode != "probe"))
        worst = max(worst, order[v])
        req = sum(1 for n in spec["required"] if libs.get(n))
        opt = sum(1 for n in spec["optional"] if libs.get(n))
        rep["families"][fam] = {"verdict": v, "python": pyinfo, "libs": libs, "required": spec["required"], "optional": spec["optional"], "results": results, "reasons": reasons, "install": inst,
                                "summary": {"required_ok": req, "required_n": len(spec["required"]), "optional_ok": opt, "optional_n": len(spec["optional"]),
                                            "engines_ok": sum(1 for r in results if r["state"] == "OK"), "engines_n": len(results)}}
        s = rep["families"][fam]["summary"]
        _say(f"{v:<7} {fam:<5} python={pyinfo['python']}({pyinfo['state']}) · 必要庫 {s['required_ok']}/{s['required_n']} 選配 {s['optional_ok']}/{s['optional_n']} · 引擎 {s['engines_ok']}/{s['engines_n']} OK"
             + (f" · {'; '.join(reasons)}" if reasons else ""), q)
    rep["chains"] = chains_fn()
    for c in rep["chains"]:
        _say(f"{c['lamp']:<7} {c['layer']:<10} {c['msg']}", q)
    rep["verdict"] = ["GREEN", "YELLOW", "RED"][worst]
    rep["next"] = []
    for fam, f in rep["families"].items():
        it = f["python"].get("interp") or {}
        if it.get("state") == "BROKEN":
            rep["next"].append(f"{fam} 境解譯器壞({it.get('kind')};{it.get('cause')}):不補庫;查 $env:PYTHONHOME/$env:PYTHONPATH(現值 {it.get('env') or '無'})、"
                               f"{it.get('pyvenv_path') or 'pyvenv.cfg'}(home={(it.get('pyvenv') or {}).get('home')})、三試 {it.get('trials')};重建境=你的手(via-envrecover 印令)")
            continue
        if f["python"]["state"] != "OK":
            rep["next"].append(f"建 {fam} 境:via-envgov apply --approve(ENSURE_ENV via_{fam}_312)或 uv venv <境根>\\via_{fam}_312 --python 3.12 → uv pip install {' '.join(PIP_NAMES.get(n, n) for n in f['required'])}")
        miss = [n for n in f["required"] if f["libs"].get(n) is None]
        if miss and f["python"]["state"] == "OK":
            rep["next"].append(f"{fam} 境補庫:via-rungate --family {fam} --approve-install(= {f['install'].get('cmd') or 'uv pip install --python <境> ' + ' '.join(PIP_NAMES.get(n, n) for n in miss)})")
        elif miss:
            rep["next"].append(f"base 補 manifest 缺件:via-envgov apply --approve --only-kind REPAIR_BASE({','.join(miss)})")
    try:
        reports.mkdir(parents=True, exist_ok=True)
        _write_json(reports / f"RUNGATE_{_ts()}.json", rep)
        _write_json(reports / "RUNGATE_latest.json", rep)
        (reports / "RUNGATE_latest.html").write_text(render_html(rep), encoding="utf-8")
    except Exception as exc:
        _say(f"YELLOW  Report     存證失敗 {str(exc)[:60]}", q)
    log_event("RUN", f"{mode} {rep['verdict']}", families={k: v["verdict"] for k, v in rep["families"].items()})
    _say(f"[via-rungate] 判定 {rep['verdict']} · 存證 {reports / 'RUNGATE_latest.json'}" + (f" · 次步:{' | '.join(rep['next'])}" if rep["next"] else " · 三族皆以家族境 python 真跑綠燈"), q)
    return rep


def status(do_print: bool = True) -> int:
    p = OUT / "RUNGATE_latest.json"
    if not p.exists():
        _say("GREY    RunGate    未跑;via-rungate(預設每族 8 站;--fast 3 站;--all 全站)")
        return 2
    rep = json.loads(p.read_text(encoding="utf-8"))
    _say(f"[via-rungate status] {rep['verdict']} · {rep['ts']} · 模式 {rep['mode']}")
    for fam, f in rep["families"].items():
        s = f["summary"]
        _say(f"{f['verdict']:<7} {fam:<5} {f['python']['python']}({f['python']['state']}) · 必要庫 {s['required_ok']}/{s['required_n']} · 引擎 {s['engines_ok']}/{s['engines_n']}" + (f" · {'; '.join(f['reasons'])}" if f["reasons"] else ""))
    for n in rep.get("next", []):
        _say(f"  [次步] {n}")
    return 0 if rep["verdict"] != "RED" else 1


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 家族判定(夾路徑/檔名前綴;其餘=base)",
        family_of(VIA / "functional modules/VDF/engine/VDF_ENG079_X_v0100.py") == "vdf" and family_of("C:/x/functional modules/VRN/vrn_report_digest_v0113.py") == "vrn"
        and family_of("/a/functional modules/VAP/engine/VAP_ENG016_AutoplotOne_v0100.py") == "vap" and family_of("VDF_ENG064_HistoryBackfill_v0108.py") == "vdf"
        and family_of(HERE / "CGC_MDL135_EnvGovernance_v0100.py") == "base")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "via_vdf_312" / "Scripts").mkdir(parents=True)
        (root / "via_vdf_312" / "Scripts" / "python.exe").write_text("", encoding="utf-8")
        r1 = python_for("vdf", roots=[root], environ={})
        r2 = python_for("vrn", roots=[root], environ={})
        r3 = python_for("base")
        chk("② 家族境 python(MDL136 正本解析:境在=OK;境缺=BASE_FALLBACK 誠實;base=本解譯器)",
            r1["state"] == "OK" and r1["env"] == "via_vdf_312" and r2["state"] == "BASE_FALLBACK" and r2["python"] == sys.executable and r3["python"] == sys.executable)
        libs = probe_libs(sys.executable, ["json", "sqlite3", "no_such_lib_xyz_"])
        chk("③ 庫探針(單子程序逐庫 import;缺=None 誠實)", libs.get("json") and libs.get("sqlite3") and libs.get("no_such_lib_xyz_") is None, f"({libs})")
        ok_py = root / "ok_eng.py"
        ok_py.write_text("import sys; print('OK 1/1'); sys.exit(0)\n", encoding="utf-8")
        bad_py = root / "bad_eng.py"
        bad_py.write_text("import sys; print('FAIL 0/1'); sys.exit(1)\n", encoding="utf-8")
        slow_py = root / "slow_eng.py"
        slow_py.write_text("import time; time.sleep(5)\n", encoding="utf-8")
        fake_battery = [{"name": "ok", "path": str(VIA / "functional modules/VDF/engine" / "VDF_ENG900_Ok_v0100.py"), "args": ["--selftest"], "timeout": 30},
                        {"name": "dup", "path": str(VIA / "functional modules/VDF/engine" / "VDF_ENG900_Ok_v0100.py"), "args": ["--selftest"], "timeout": 30},
                        {"name": "noarg", "path": str(VIA / "functional modules/VDF/engine" / "VDF_ENG901_Run_v0100.py"), "args": ["run"], "timeout": 30},
                        {"name": "vrn", "path": str(VIA / "functional modules/VRN" / "VRN_ENG900_X_v0100.py"), "args": ["--self-test"], "timeout": 30},
                        {"name": "reg", "path": str(HERE / "CGC_MDL999_X_v0100.py"), "args": ["--selftest"], "timeout": 30},
                        {"name": "doc", "path": None, "args": [], "timeout": 10}]
        st_vdf = family_stations(fake_battery, "vdf", None)
        st_vrn = family_stations(fake_battery, "vrn", 5)
        chk("④ 家族站篩選(家族夾+--selftest/--self-test;同檔去重;非家族/無自測/佔位排除)",
            [s["name"] for s in st_vdf] == ["ok"] and [s["name"] for s in st_vrn] == ["vrn"] and family_stations(fake_battery, "vap", None) == [])
        res = [run_station(sys.executable, {"name": "ok", "path": str(ok_py), "args": [], "timeout": 30}),
               run_station(sys.executable, {"name": "bad", "path": str(bad_py), "args": [], "timeout": 30}),
               run_station(sys.executable, {"name": "slow", "path": str(slow_py), "args": [], "timeout": 1}),
               run_station(sys.executable, {"name": "miss", "path": str(root / "none.py"), "args": [], "timeout": 5})]
        chk("⑤ 站執行(rc0=OK/rc1=FAIL/逾時=TIMEOUT 不卡斷/缺=SKIP;尾行存證)",
            [r["state"] for r in res] == ["OK", "FAIL", "TIMEOUT", "SKIP"] and res[0]["tail"] == ["OK 1/1"] and res[1]["tail"] == ["FAIL 0/1"])
        ok_info = {"state": "OK", "python": "x", "env": "via_vdf_312"}
        fb_info = {"state": "BASE_FALLBACK", "python": sys.executable, "env": ""}
        chk("⑥ 判定律(FAIL/TIMEOUT/SKIP/零站=RED;必要庫缺=YELLOW;base 退路=YELLOW;全綠=GREEN;probe 可明示只驗套件)",
            verdict_for(ok_info, {"duckdb": "1"}, ["duckdb"], [{"state": "OK", "file": "a"}])[0] == "GREEN"
            and verdict_for(ok_info, {"duckdb": None}, ["duckdb"], [{"state": "OK", "file": "a"}])[0] == "YELLOW"
            and verdict_for(ok_info, {"duckdb": "1"}, ["duckdb"], [])[0] == "RED"
            and verdict_for(ok_info, {"duckdb": "1"}, ["duckdb"], [{"state": "SKIP", "file": "a"}])[0] == "RED"
            and verdict_for(fb_info, {"duckdb": "1"}, ["duckdb"], [], require_results=False)[0] == "YELLOW"
            and verdict_for(fb_info, {"duckdb": None}, ["duckdb"], [{"state": "FAIL", "file": "a"}])[0] == "RED")
        reports = root / "reports"

        def fake_py(fam):
            return {"family": fam, "env": f"via_{fam}_312", "python": sys.executable, "source": "fake", "state": "OK"}

        def fake_probe(py, libs):
            return {n: "1.0" for n in libs}

        def fake_run(py, st):
            return run_station(py, {"name": st["name"], "path": str(ok_py if "Ok" in st["path"] else bad_py), "args": [], "timeout": 30})
        rep = run(["vdf", "vrn"], "all", do_print=False, reports=reports, battery=fake_battery, python_fn=fake_py, probe_fn=fake_probe, run_fn=fake_run,
                  chains_fn=lambda: [{"layer": "DeckServer", "lamp": "GREEN", "msg": "x"}])
        chk("⑦ 整合跑(vdf 綠/vrn FAIL=RED;總判 RED;RUNGATE_latest.json/.html 零 CDN;鏈路燈入冊)",
            rep["families"]["vdf"]["verdict"] == "GREEN" and rep["families"]["vrn"]["verdict"] == "RED" and rep["verdict"] == "RED"
            and (reports / "RUNGATE_latest.json").exists() and 'src="http' not in (reports / "RUNGATE_latest.html").read_text(encoding="utf-8")
            and rep["chains"][0]["layer"] == "DeckServer", f"({rep['families']['vrn']['reasons']})")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/正本零觸碰/誠實三態/零網路/尾版律/Zero-Hydra/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "正本零觸碰", "誠實三態", "零網路", "尾版律", "Zero-Hydra", "ACCEL-BRIDGE")))
    chk("⑨ 動詞白名單(批387 實錄:--family vrn 不得誤判為動詞;status/probe 仍可)",
        pick_verb(["--family", "vrn"]) == "run" and pick_verb(["status"]) == "status" and pick_verb(["probe", "--family", "vdf"]) == "probe" and pick_verb(["--fast"]) == "run")
    okpy = {"state": "OK", "python": sys.executable, "env": "via_vrn_312"}
    plan = install_missing("vrn", okpy, ["fitz", "duckdb"], approve=False)
    skip = install_missing("vrn", {"state": "BASE_FALLBACK", "python": sys.executable}, ["duckdb"], approve=False)
    chk("⑩ 補庫道(PLAN 印 uv/pip 令且 import 名→pip 名 fitz→pymupdf;base 退路 SKIP 不裝功能件;缺件空=NONE;未授權零執行)",
        plan["state"] == "PLAN" and "pymupdf" in plan["cmd"] and "duckdb" in plan["cmd"] and skip["state"] == "SKIP" and install_missing("vrn", okpy, [], False)["state"] == "NONE")
    ok_i = interp_check(sys.executable)
    with tempfile.TemporaryDirectory() as td2:
        sh = Path(td2) / "re"
        sh.mkdir()
        (sh / "__init__.py").write_text("raise AssertionError('SRE module mismatch')\n", encoding="utf-8")
        env2 = dict(os.environ)
        env2["PYTHONPATH"] = td2 + (os.pathsep + env2["PYTHONPATH"] if env2.get("PYTHONPATH") else "")
        bad_i = interp_check(sys.executable, environ=env2)
    chk("⑪ 解譯器探針(批509):本解譯器 OK 帶版本;假 re 遮蔽(PYTHONPATH)→ BROKEN/STDLIB_MISMATCH · -E ok -I ok -S fail → 病因=環境變數;存證 env/pyvenv",
        ok_i["state"] == "OK" and bool(ok_i.get("version")) and bad_i["state"] == "BROKEN" and bad_i["kind"] == "STDLIB_MISMATCH"
        and bad_i["trials"]["-E"] and bad_i["trials"]["-I"] and not bad_i["trials"]["-S"] and "環境變數" in bad_i["cause"] and "PYTHONPATH" in bad_i["env"],
        f"({bad_i.get('kind')} · {bad_i.get('cause')} · 三試 {bad_i.get('trials')})")
    calls = []

    def cnt_probe(py, libs):
        calls.append(py)
        return {n: "1.0" for n in libs}

    def fake_interp(py):
        return {"state": "BROKEN", "kind": "STDLIB_MISMATCH", "cause": "測", "trials": {"-E": True, "-S": False, "-I": True}, "err": "SRE module mismatch", "env": {}, "pyvenv": {}}
    bi = {"state": "OK", "python": "x", "env": "via_vdf_312", "interp": fake_interp("x")}
    v12, r12 = verdict_for(bi, {"duckdb": None}, ["duckdb"], [{"state": "FAIL", "file": "a"}])
    with tempfile.TemporaryDirectory() as td3:
        rep12 = run(["vdf"], "probe", do_print=False, reports=Path(td3), battery=[], python_fn=fake_py, probe_fn=cnt_probe, run_fn=fake_run,
                    chains_fn=lambda: [], interp_fn=fake_interp)
    chk("⑫ 解譯器壞=RED 且理由是解譯器不是缺庫(判錯的紅燈=假綠同罪);補庫 SKIP;run 不探庫不跑站;次步=診斷+重建境(候裁),不是 pip install",
        v12 == "RED" and r12[0].startswith("解譯器壞") and not any("必要庫缺" in r for r in r12) and install_missing("vdf", bi, ["duckdb"], False)["state"] == "SKIP"
        and rep12["families"]["vdf"]["verdict"] == "RED" and calls == [] and any("解譯器壞" in n for n in rep12["next"]) and not any("pip install" in n for n in rep12["next"]))
    print(f"  [計] 十二檢 OK {12 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VDF/VRN/VAP 能跑閘(CGC_MDL137_RunGate v0103)· 十二檢自測(零網路)===")
        return selftest()
    verb = pick_verb(a)
    raw_families = _arg(a, "--family")
    if "--family" in a and (raw_families is None or not raw_families.strip()):
        print("  [FAIL] --family 後要給 vdf,vrn,vap 之一或逗號合寫")
        return 2
    fams = list(dict.fromkeys(
        x.strip().lower() for x in (raw_families or "").split(",") if x.strip())) or None
    bad_families = [x for x in (fams or []) if x not in FAMILY_DIRS]
    if bad_families:
        print(f"  [FAIL] --family 只收 vdf|vrn|vap，不收 {','.join(bad_families)}")
        return 2
    if "--fast" in a and "--all" in a:
        print("  [FAIL] --fast 與 --all 不可同時使用")
        return 2
    as_json, quiet = "--json" in a, "--quiet" in a
    try:
        if verb in ("run", "probe"):
            mode = "probe" if verb == "probe" else ("fast" if "--fast" in a else ("all" if "--all" in a else "default"))
            rep = run(fams, mode, do_print=not as_json, quiet=quiet, approve_install="--approve-install" in a)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1))
            return 0 if rep["verdict"] != "RED" else 1
        if verb == "status":
            return status()
        print(__doc__)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
