#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_DailyBackup v0104 — 薄尾(v0100–v0103 一字不動):full = 三道前置閘並行(Graphify · 環境衝突 · 工具安裝來源)→ 缺件當輪補裝 → 備份

操作員 2026-11-25:「備份功能要加入 GRAPHIFY 並檢查 base / via_core / via_ 開頭的環境都無衝突 · vcgc / vdf / vrn 的工具及網路工具及加速器工具
都有用 vcgc 的工具進行安裝無衝突 · 整個列入備份功能 · 用 py 寫 ast 導入加速器」。
第五章六題定案:Q1 A(引擎倉:程式碼 + 三本尾版冊)· Q2 Mode C(py)· Q3 本機隔離區 · Q4 5 份輪替 · Q5 Fail-Closed · Q6 純本地歸檔 · 缺件當輪補裝。

full [--via <VIA 根>] [--out <備份根>] [--keep 5] [--no-install] [--sys VCGC,VDF,VRN]
  ① 三道並行(互不相依;每 20 秒一行心跳):
     G1 Graphify + 三冊  VCGC 中樞 graph build --sys <每個系統>(本機 code-only;一次一個系統)
                         三本尾版冊(Policy_Laws · ToolRoster · VRN LogicArchitecture)JSON 可解析 + 雜湊。
                         三冊先刷齊:VIA_BooksSync 尾版 apply(Mode C;出新版號冊 · 前版不動 · 寫前寫後 ssot panorama;
                         --books-check-only 只查不寫)。三冊 DataFrame(book · current · diff)另收 extras/BOOKS_FRAMES.zip。
     G2 環境衝突          VCGC 中樞 doctor(7 支 VCGC 環境工具:envmgr 管 base · via_core · via_* · 安裝閘 pip check / 多層互撞 · 加速器 · 八樞)
                         讀 DOCTOR_latest.json 的總燈 · 安裝計畫 · 衝突 · 互撞。
     G3 工具安裝來源      鎖冊每一家(加速器 · 網路 · 省 Token · NLP …)+ 加速器本體 + VCGC / VDF / VRN 入口尾版:
                         AST 簽章(ast.parse + compile + 加速器橋)· 模組層第三方匯入在各自的境真的找得到(core / vdf / vrn 境的 python 子行程 find_spec)·
                         找得到的件有沒有在 VIA_Lib_Registry(安裝閘帳)出現過(沒有 = 黃:不是經 VCGC 裝的)。
  ② 缺件當輪補裝(--no-install 關):doctor 計畫有件 → 中樞 install --from-plan --yes;G3 缺的件(必要件 + try 裡的加速器 / 網路選配件)→ 中樞 install --yes <件>
     (選配件補完仍缺 = 黃不擋;都經 CGC_MDL056 安裝閘,同意閘只在它的子行程裡開)→ 重跑 G2 · G3 一次。衝突 / 互撞只列不動(重建境由操作員下 via-envgov apply --approve)。
  ③ Fail-Closed:任一閘 RED(補裝後仍紅)→ 不備份、零寫入備份根,rc 1。
  ④ 備份:前版 backup(--manifest-dir 改到備份根 _manifests,倉內零寫入)+ extras/:
       CODE.zip(git archive HEAD:引擎倉程式碼)· BOOKS.zip(三本尾版冊)· GRAPHIFY.zip(各系統 graphify-out)· GATES.json(三閘收據)
       每檔先寫 .sdd_tmp,驗非空 + zip 可讀才換名;extras/SHA256SUMS.txt。
  ⑤ 輪替:備份根下時間戳夾最多留 --keep 份(預設 5),多的刪最舊;_pre_restore / _manifests 不動。
  ⑥ 重寫備份卡(前版 card)。不碰 git(Q6 純本地)。
備份根預設(Q3 本機隔離區):%LOCALAPPDATA%\\VIA\\_via_backups(非 Windows:~/_via_backups);
  落在倉內或 OneDrive 底下 = 當場拒絕、零寫入。
其餘動詞(backup · check · restore · card · selftest)全照前版。rc:0 綠 · 2 黃 · 1 紅
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import ast
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
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0104"
FAMILY = "VIA_DailyBackup"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
_T0 = time.time()
ENV_ALIAS = {"core": ["via_core_312", "via_core", "venv_core"], "vdf": ["via_vdf_312", "via_vdf", "via_vdf_313"],
             "vrn": ["via_vrn_312", "via_vrn", "via_extract_312", "via_vrn4"]}          # 照 Get-VIAEnvPython
ENV_SUBS = [("Scripts", "python.exe"), ("python.exe",), ("bin", "python3"), ("bin", "python")]
PIP_NAME = {"cv2": "opencv-python", "yaml": "pyyaml", "PIL": "pillow", "sklearn": "scikit-learn", "fitz": "pymupdf",
            "bs4": "beautifulsoup4", "dateutil": "python-dateutil", "docx": "python-docx", "Crypto": "pycryptodome",
            "win32api": "pywin32", "win32con": "pywin32", "dotenv": "python-dotenv", "jwt": "pyjwt"}
LOCK_REL = Path("supportive modules") / "registry" / "VIA_ToolVersion_Lock_v0100.json"
LIBREG_REL = Path("supportive modules") / "registry" / "VIA_Lib_Registry_v0100.json"
BOOKS = [("supportive modules/registry", "VIA_Policy_Laws_SSOT_v*.json"), ("supportive modules/registry", "VIA_ToolRoster_SSOT_v*.json"),
         ("supportive modules/registry", "VIA_VRN_LogicArchitecture_SSOT_v*.json")]
GRAPH_REL = Path("VIA_Reports") / "vcgc" / "agentos" / "graphify"
ENTRY_TAILS = {"core": [("supportive modules/registry", "CGC_SystemManager_v*.py")],
               "vdf": [("functional modules/VDF", "VDF_SystemManager_v*.py")],
               "vrn": [("functional modules/VRN", "VRN_SystemManager_v*.py")]}
LOCK_ENV = {"accelerator": ["core", "vdf", "vrn"], "network": ["core", "vdf", "vrn"], "frame": ["core", "vdf", "vrn"],
            "token": ["core"], "nlp": ["vrn"], "layout": ["vrn"], "praddle": ["vrn"], "pdfplumber": ["vrn"]}   # ocr 在自己的隔離境:不在三境驗
MAX_EXTRA_BYTES = 200 * 1024 * 1024


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def newest(d: Path, pat: str):
    c = [p for p in d.glob(pat) if _vnum(p) >= 0]
    return max(c, key=_vnum) if c else None


# ---------------------------------------------------------------- 中樞
def hub(via: Path):
    return newest(via, "VCGC_CommandHub_v*.py")


def hub_run(via: Path, args: list, timeout: int = 3600, capture: bool = True):
    h = hub(via)
    if h is None:
        return 3, "找不到 VCGC_CommandHub 尾版"
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", VIA_CODE_ROOT=str(via))
    env.setdefault("VIA_ROOT", str(via))
    env.pop("VIA_FROM_VCGC", None)
    try:
        r = subprocess.run([sys.executable, str(h), *args], cwd=str(via), env=env, timeout=timeout,
                           capture_output=capture, text=True, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return 124, f"逾時 {timeout}s"
    return r.returncode, ((r.stdout or "") + (r.stderr or ""))[-4000:] if capture else ""


# ---------------------------------------------------------------- G1 Graphify + 三冊
def books_sync_tail(via: Path):
    return newest(HERE.parent, "VIA_BooksSync_v*.py") or newest(via / "docs" / "handoff" / "ai", "VIA_BooksSync_v*.py")


def run_books(via: Path, apply: bool) -> dict:
    """三冊重產器(VIA_BooksSync 尾版;Mode C 先刷齊):apply = 出新版號冊(前版不動 · 寫前寫後 ssot panorama);check = 只出 SYNCED / OUT_OF_SYNC。"""
    t = books_sync_tail(via)
    if t is None:
        return {"lamp": "YELLOW", "note": "找不到 VIA_BooksSync 尾版 → 三冊只驗不重產"}
    args = [sys.executable, str(t), "apply" if apply else "check", "--via", str(via)]
    prm = newest(t.parent, "VIA_BooksSync_Params_v*.json")
    if prm and newest(via / "docs" / "handoff" / "ai", "VIA_BooksSync_Params_v*.json") is None:
        args += ["--params", str(prm)]                                   # 從 TEMP 跑:參數冊跟著本檔一起取出
    try:
        r = subprocess.run(args, cwd=str(via), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800,
                           env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", VIA_REPO=str(via.parent)))
    except subprocess.TimeoutExpired:
        return {"lamp": "RED", "note": "三冊重產器逾時 1800s"}
    return {"rc": r.returncode, "mode": "apply" if apply else "check", "lamp": {0: "GREEN", 2: "YELLOW"}.get(r.returncode, "RED"),
            "tool": t.name, "tail": (r.stdout or "")[-1500:] + (r.stderr or "")[-500:]}


def gate_graphify(via: Path, systems: list, books_apply: bool = True) -> dict:
    out = {"gate": "G1_graphify", "systems": {}, "books": {}, "notes": []}
    out["books_sync"] = run_books(via, books_apply)
    for s in systems:                                                    # 一次一個系統(大夾吃記憶體)
        rc, tail = hub_run(via, ["graph", "build", "--sys", s], timeout=3600)
        absent = "ABSENT" in tail or "沒有隔離環境" in tail
        out["systems"][s] = {"rc": rc, "lamp": "GREEN" if rc == 0 else "RED", "absent_env": absent, "tail": tail[-600:]}
    for d, pat in BOOKS:
        p = newest(via / d, pat)
        if p is None:
            out["books"][pat] = {"lamp": "RED", "note": "不在"}
            continue
        try:
            json.loads(p.read_text(encoding="utf-8"))
            out["books"][pat] = {"lamp": "GREEN", "tail": p.name, "sha12": sha256(p)[:12]}
        except Exception as e:  # noqa: BLE001
            out["books"][pat] = {"lamp": "RED", "tail": p.name, "note": f"{type(e).__name__}: {e}"}
    reds = [k for k, v in {**out["systems"], **out["books"], "books_sync": out["books_sync"]}.items() if v["lamp"] == "RED"]
    out["red"] = reds
    out["lamp"] = "RED" if reds else ("YELLOW" if out["books_sync"]["lamp"] == "YELLOW" else "GREEN")
    if any(v.get("absent_env") for v in out["systems"].values()):
        out["fix"] = "桌機先建 Graphify 隔離境(via-graph status 印的那一行;建境由操作員下)"
    return out


# ---------------------------------------------------------------- G2 環境衝突(VCGC doctor)
def gate_doctor(via: Path) -> dict:
    rc, tail = hub_run(via, ["doctor"], timeout=3600)
    p = via / "VIA_Reports" / "vcgc_hub" / "doctor" / "DOCTOR_latest.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"gate": "G2_doctor", "lamp": "RED", "rc": rc, "note": f"讀不到 DOCTOR_latest.json:{type(e).__name__}", "tail": tail[-800:]}
    plan = d.get("plan") or {}
    plugs = {x.get("key"): x.get("lamp") for x in d.get("plugins", [])}
    return {"gate": "G2_doctor", "lamp": d.get("lamp", "RED"), "rc": rc, "counts": d.get("counts"), "plugins": plugs,
            "plan_pip": plan.get("pip", []), "conflicts": plan.get("conflicts", []), "dupes": plan.get("dupes", []),
            "red": [k for k, v in plugs.items() if v == "RED"], "next": d.get("next", "")}


# ---------------------------------------------------------------- G3 工具安裝來源
def env_python(family: str, via: Path):
    ov = os.environ.get("VIA_PY_" + family.upper(), "")
    if ov and Path(ov).is_file():
        return Path(ov)
    home = Path.home()
    roots = [os.environ.get("VIA_ENV_ROOT", "")] + os.environ.get("VIA_ENV_ROOTS", "").split(";")
    roots += [home / "envs", home / "miniconda3" / "envs", home / "Miniconda3" / "envs", home / "anaconda3" / "envs",
              home / ".virtualenvs", via / "Environments", via]
    names = ENV_ALIAS.get(family, []) + [f"via_{family}_312", f"via_{family}", f"via_{family}_313", f"via_{family}_311", f".venv-via_{family}"]
    for r in roots:
        if not r or not Path(r).is_dir():
            continue
        for n in dict.fromkeys(names):
            for sub in ENV_SUBS:
                p = Path(r).joinpath(n, *sub)
                if p.is_file():
                    return p
    return None


def local_modules(via: Path) -> set:
    names = set()
    for d in ("supportive modules", "functional modules", "docs/handoff/ai", "."):
        base = via / d
        if base.is_dir():
            names.update(p.stem for p in base.rglob("*.py"))
            names.update(p.name for p in base.rglob("*") if p.is_dir())
    return names


def top_imports(src: str) -> set:
    """模組層(不在 try 裡)的匯入;try 裡的是選配件,不算必要。"""
    tree = ast.parse(src)
    out = set()
    for n in tree.body:
        if isinstance(n, ast.Import):
            out.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            out.add(n.module.split(".")[0])
    return out


def try_imports(src: str) -> set:
    """try 區塊裡的匯入(選配件:加速器 / 網路工具多半這樣寫,缺了只降級)。"""
    out = set()
    for t in ast.walk(ast.parse(src)):
        if isinstance(t, ast.Try):
            for n in (x for b in t.body for x in ast.walk(b)):
                if isinstance(n, ast.Import):
                    out.update(a.name.split(".")[0] for a in n.names)
                elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                    out.add(n.module.split(".")[0])
    return out


def ast_signature(p: Path) -> dict:
    src = p.read_text(encoding="utf-8-sig", errors="replace")
    try:
        compile(ast.parse(src), str(p), "exec")
    except SyntaxError as e:
        return {"ok": False, "note": f"SyntaxError L{e.lineno}: {e.msg}", "imports": set(), "optional": set()}
    return {"ok": True, "bridge": "VIA:ACCEL-BRIDGE" in src[:6000] or "VIA_SuperAccel_Module" in src,
            "imports": top_imports(src), "optional": try_imports(src)}


def probe(py: Path, mods: list) -> dict:
    code = ("import importlib.util, json, sys\n"
            "m = json.loads(sys.argv[1])\n"
            "print(json.dumps({k: importlib.util.find_spec(k) is not None for k in m}))\n")
    try:
        r = subprocess.run([str(py), "-c", code, json.dumps(mods)], capture_output=True, text=True, timeout=120)
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:  # noqa: BLE001
        return {"__error__": f"{type(e).__name__}: {e}"}


def ledger_packages(via: Path) -> set:
    try:
        d = json.loads((via / LIBREG_REL).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return set()
    out = set()
    for row in d.get("ledger", []):
        for pk in row.get("packages", []) or []:
            name = pk.get("name") if isinstance(pk, dict) else str(pk)
            out.add(re.split(r"[=<>!~\[ ]", str(name))[0].lower().replace("_", "-"))
    return out


def gate_tools(via: Path) -> dict:
    repo = via.parent
    try:
        lock = json.loads((via / LOCK_REL).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"gate": "G3_tools", "lamp": "RED", "note": f"鎖冊讀不到:{type(e).__name__}"}
    items = []                                                           # (名, 檔, [境])
    for k, v in lock.items():
        if isinstance(v, dict) and v.get("path") and k in LOCK_ENV:
            items.append((k, repo / v["path"], LOCK_ENV[k]))
    sup = newest(via / "supportive modules", "SUP_MDL737_SuperAccelModule_v*.py")
    if sup:
        items.append(("superaccel", sup, ["core", "vdf", "vrn"]))
    for fam, pats in ENTRY_TAILS.items():
        for d, pat in pats:
            p = newest(via / d, pat)
            items.append((pat.split("_v*")[0], p, [fam]) if p else (pat, via / d / pat, [fam]))
    local = local_modules(via)
    std = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    need: dict = {}
    optional: dict = {}
    sigs = {}
    for name, p, envs in items:
        if not p.is_file():
            sigs[name] = {"ok": False, "note": "檔不在"}
            continue
        s = ast_signature(p)
        sigs[name] = {"file": p.name, "ok": s["ok"], "bridge": s.get("bridge"), "note": s.get("note", "")}
        third = sorted(m for m in s["imports"] if m not in std and m not in local and not m.startswith("_"))
        opt = sorted(m for m in s.get("optional", ()) if m not in std and m not in local and not m.startswith("_") and m not in third)
        sigs[name]["third_party"], sigs[name]["optional"] = third, opt
        for e in envs:
            need.setdefault(e, set()).update(third)
            optional.setdefault(e, set()).update(opt)
    envs, missing, opt_missing = {}, {}, {}
    for fam in sorted(set(need) | set(optional)):
        mods, opts = need.get(fam, set()), optional.get(fam, set()) - need.get(fam, set())
        py = env_python(fam, via)
        label = str(py) if py else f"{sys.executable}(BASE_FALLBACK)"
        res = probe(py or Path(sys.executable), sorted(mods | opts)) if (mods or opts) else {}
        envs[fam] = {"python": label, "found": py is not None, "checked": sorted(mods), "optional_checked": sorted(opts),
                     "optional_present": sorted(k for k in opts if res.get(k) is True),
                     "result": {k: v for k, v in res.items() if k in mods or k == "__error__"}}
        miss = sorted(k for k in mods if res.get(k) is False)
        if miss or "__error__" in res:
            missing[fam] = miss + (["__error__"] if "__error__" in res else [])
        om = sorted(k for k in opts if res.get(k) is False)
        if om:
            opt_missing[fam] = om
    led = ledger_packages(via)
    present = {m for e in envs.values() for m, ok in e["result"].items() if ok is True} | {m for e in envs.values() for m in e["optional_present"]}
    not_via_gate = sorted(m for m in present if PIP_NAME.get(m, m).lower().replace("_", "-") not in led)
    bad_sig = [k for k, v in sigs.items() if not v.get("ok")]
    no_bridge = [k for k, v in sigs.items() if v.get("ok") and not v.get("bridge")]
    no_env = [f for f, e in envs.items() if not e["found"]]
    red = bad_sig + [f"{f}:{','.join(m)}" for f, m in missing.items()]
    lamp = "RED" if red else ("YELLOW" if not_via_gate or no_bridge or no_env or opt_missing else "GREEN")
    return {"gate": "G3_tools", "lamp": lamp, "red": red, "signatures": sigs, "envs": envs, "missing": missing,
            "optional_missing": opt_missing,
            "not_via_gate": not_via_gate, "no_bridge": no_bridge, "env_not_found": no_env,
            "counts": {"should": len(items), "scanned": len(sigs), "skipped": [k for k, v in sigs.items() if v.get("note") == "檔不在"]}}


# ---------------------------------------------------------------- 並行 + 補裝
def run_parallel(jobs: dict, beat: float = 20.0) -> dict:
    res, stop = {}, threading.Event()

    def heart():
        while not stop.wait(beat):
            say("心跳 · 還在跑:" + " · ".join(k for k in jobs if k not in res))

    threading.Thread(target=heart, daemon=True).start()
    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        futs = {k: (time.time(), ex.submit(fn)) for k, fn in jobs.items()}
        for k, (t0, f) in futs.items():
            try:
                res[k] = f.result()
            except Exception as e:  # noqa: BLE001 - 一閘爆 = 該閘紅
                res[k] = {"gate": k, "lamp": "RED", "red": [f"{type(e).__name__}: {e}"]}
            res[k]["seconds"] = round(time.time() - t0, 1)
            say(f"{k} · {res[k]['lamp']} · {res[k]['seconds']}s" + (" · 紅:" + " · ".join(map(str, res[k].get('red', [])))[:300] if res[k].get("red") else ""))
    stop.set()
    return res


def repair(via: Path, g2: dict, g3: dict) -> list:
    done = []
    if g2.get("plan_pip"):
        say("② 補裝:doctor 計畫 " + ", ".join(g2["plan_pip"]) + " → 中樞 install --from-plan --yes(安裝閘)")
        rc, _ = hub_run(via, ["install", "--from-plan", "--yes"], capture=False)
        done.append({"what": "install --from-plan --yes", "rc": rc})
    want = list((g3.get("missing") or {}).values()) + list((g3.get("optional_missing") or {}).values())
    pk = sorted({PIP_NAME.get(m, m) for ms in want for m in ms if m != "__error__"})
    if pk:
        say("② 補裝:工具缺件(必要 + 加速器 / 網路選配)" + ", ".join(pk) + " → 中樞 install --yes(安裝閘:三鏡像先查衝突,解不出的點名剔除)")
        rc, _ = hub_run(via, ["install", "--yes", *pk], capture=False)
        done.append({"what": "install --yes " + " ".join(pk), "rc": rc})
    return done


# ---------------------------------------------------------------- 備份根 · extras · 輪替
def default_out() -> Path:
    la = os.environ.get("LOCALAPPDATA")
    return (Path(la) / "VIA" / "_via_backups") if la else (Path.home() / "_via_backups")


def bad_out(out: Path, repo: Path):
    o = out.expanduser().resolve()
    if "onedrive" in str(o).lower():
        return "備份根在 OneDrive 底下(同步會鎖檔)"
    try:
        o.relative_to(repo.resolve())
        return "備份根在倉內"
    except ValueError:
        return None


def _atomic_zip(dest: Path, build) -> dict:
    tmp = dest.with_name(dest.name + ".sdd_tmp")
    build(tmp)
    if not tmp.exists() or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{dest.name} 空檔")
    with zipfile.ZipFile(tmp) as z:
        if z.testzip() is not None:
            raise RuntimeError(f"{dest.name} 壓縮檔壞")
        n = len(z.namelist())
    os.replace(tmp, dest)
    return {"file": dest.name, "entries": n, "bytes": dest.stat().st_size, "sha256": sha256(dest)}


def _zip_files(files: list, base: Path):
    def build(tmp: Path):
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for f in files:
                if f.is_file() and f.stat().st_size <= MAX_EXTRA_BYTES:
                    z.write(f, f.relative_to(base).as_posix())
    return build


def write_extras(bdir: Path, via: Path, gates: dict, systems: list) -> dict:
    ex = bdir / "extras"
    ex.mkdir(exist_ok=True)
    repo = via.parent
    rows = []
    if (repo / ".git").exists():
        rows.append(_atomic_zip(ex / "CODE.zip", lambda t: subprocess.run(
            ["git", "-C", str(repo), "archive", "--format=zip", "-o", str(t), "HEAD"], check=True)))
    books = [b for b in (newest(via / d, pat) for d, pat in BOOKS) if b]
    if books:
        rows.append(_atomic_zip(ex / "BOOKS.zip", _zip_files(books, via)))
    fr = sorted((via / "VIA_Reports" / "books_sync").glob("2*"))
    ffiles = [p for p in fr[-1].iterdir() if p.is_file()] if fr else []
    if ffiles:
        rows.append(_atomic_zip(ex / "BOOKS_FRAMES.zip", _zip_files(ffiles, via)))
    gfiles = [p for s in systems for p in (via / GRAPH_REL / s / "graphify-out").rglob("*") if p.is_file()]
    if gfiles:
        rows.append(_atomic_zip(ex / "GRAPHIFY.zip", _zip_files(gfiles, via)))
    gp = ex / "GATES.json"
    tmp = gp.with_name(gp.name + ".sdd_tmp")
    tmp.write_text(json.dumps(gates, ensure_ascii=False, indent=1, default=sorted), encoding="utf-8")
    os.replace(tmp, gp)
    rows.append({"file": gp.name, "bytes": gp.stat().st_size, "sha256": sha256(gp)})
    (ex / "SHA256SUMS.txt").write_text("".join(f"{r['sha256']}  {r['file']}\n" for r in rows), encoding="utf-8")
    (ex / "EXTRAS_MANIFEST.json").write_text(json.dumps({"engine": TAG, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"rows": rows, "graph_files": len(gfiles), "books": [b.name for b in books]}


def rotate(out: Path, keep: int) -> list:
    snaps = sorted(p for p in out.iterdir() if p.is_dir() and re.fullmatch(r"\d{8}_\d{6}Z", p.name))
    gone = []
    for p in snaps[:-keep] if keep > 0 else []:
        shutil.rmtree(p)
        gone.append(p.name)
    return gone


# ---------------------------------------------------------------- full
def do_full(via: Path, out: Path, keep: int = 5, install: bool = True, systems=None, books_apply: bool = True) -> int:
    systems = systems or ["VCGC", "VDF", "VRN"]
    repo = via.parent
    why = bad_out(out, repo)
    if why:
        say(f"[RED] {why}:{out} → 拒絕,零寫入(用 --out 指到本機非 OneDrive 的夾)")
        return 1
    say(f"{TAG} full · VIA {via} · 備份根 {out} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'}")
    say("① 三閘並行:G1 Graphify + 三冊 · G2 環境衝突(doctor)· G3 工具安裝來源")
    gates = run_parallel({"G1_graphify": lambda: gate_graphify(via, systems, books_apply), "G2_doctor": lambda: gate_doctor(via),
                          "G3_tools": lambda: gate_tools(via)})
    need = gates["G2_doctor"].get("plan_pip") or gates["G3_tools"].get("missing") or gates["G3_tools"].get("optional_missing")
    if install and need:
        gates["repair"] = repair(via, gates["G2_doctor"], gates["G3_tools"])
        say("② 補裝後重驗 G2 · G3")
        gates.update(run_parallel({"G2_doctor": lambda: gate_doctor(via), "G3_tools": lambda: gate_tools(via)}))
    reds = [k for k in ("G1_graphify", "G2_doctor", "G3_tools") if gates[k]["lamp"] == "RED"]
    if reds:
        say("[RED] Fail-Closed:" + " · ".join(reds) + " 紅 → 不備份(零寫入備份根)")
        for k in reds:
            g = gates[k]
            say(f"  {k}:" + " · ".join(map(str, g.get("red", [])))[:400] + (f" · 解法:{g['fix']}" if g.get("fix") else ""))
        if gates["G2_doctor"]["lamp"] == "RED":
            say("  衝突 / 互撞只列不動:via-envgov plan 看重建計畫,由你下 via-envgov apply --approve")
        return 1
    say("③ 三閘無紅 → 備份(前版 backup,MANIFEST 寫備份根 _manifests,倉內零寫入)")
    out.mkdir(parents=True, exist_ok=True)
    mdir = out / "_manifests"
    rc = PRIOR.main(["backup", "--via", str(via), "--out", str(out), "--manifest-dir", str(mdir)])
    try:
        bdir = Path(json.loads((out / "BACKUP_latest.json").read_text(encoding="utf-8"))["backup_dir"])
    except Exception as e:  # noqa: BLE001
        say(f"[RED] 前版 backup 沒留下 BACKUP_latest.json({type(e).__name__})rc {rc}")
        return 1
    ex = write_extras(bdir, via, gates, systems)
    for r in ex["rows"]:
        say(f"  extras/{r['file']} · {r['bytes']} B · sha {r['sha256'][:12]}")
    gone = rotate(out, keep)
    if gone:
        say(f"⑤ 輪替:留 {keep} 份,刪最舊 " + " · ".join(gone))
    PRIOR.main(["card", "--via", str(via), "--out", str(out), "--manifest-dir", str(mdir)])
    lamps = [gates[k]["lamp"] for k in ("G1_graphify", "G2_doctor", "G3_tools")] + (["YELLOW"] if VIA_ACCEL is None else [])
    total = "YELLOW" if "YELLOW" in lamps or rc != 0 else "GREEN"
    say(f"完成 · {total} · {bdir} · 總計 {time.time() - _T0:.0f}s(Q6 純本地:沒碰 git)")
    return 0 if total == "GREEN" else 2


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    if argv[:1] != ["full"]:
        return PRIOR.main(argv)
    ap = argparse.ArgumentParser(prog=HERE.name)
    ap.add_argument("verb", choices=["full"])
    ap.add_argument("--via", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep", type=int, default=5)
    ap.add_argument("--no-install", action="store_true")
    ap.add_argument("--sys", default="VCGC,VDF,VRN")
    ap.add_argument("--books-check-only", action="store_true", help="三冊只查不寫(預設 Mode C 先刷齊)")
    a = ap.parse_args(argv)
    via = Path(a.via).resolve() if a.via else PRIOR.BASE.VIA
    return do_full(via, Path(a.out) if a.out else default_out(), a.keep, not a.no_install, [s for s in a.sys.split(",") if s], not a.books_check_only)


# ---------------------------------------------------------------- 自測(全在暫存夾造資料)
FAKE_HUB = r'''
import json, os, sys
from pathlib import Path
via = Path(__file__).parent
a = sys.argv[1:]
log = via / "hub_calls.txt"
log.open("a", encoding="utf-8").write(" ".join(a) + "\n")
if a[:2] == ["graph", "build"]:
    g = via / "VIA_Reports" / "vcgc" / "agentos" / "graphify" / a[3] / "graphify-out"
    g.mkdir(parents=True, exist_ok=True)
    (g / "graph.json").write_text("{}", encoding="utf-8")
    sys.exit(int(os.environ.get("FAKE_GRAPH_RC", "0")))
if a[:1] == ["doctor"]:
    fixed = (via / "installed.flag").exists()
    d = via / "VIA_Reports" / "vcgc_hub" / "doctor"
    d.mkdir(parents=True, exist_ok=True)
    lamp = "YELLOW" if fixed else os.environ.get("FAKE_DOCTOR", "RED")
    (d / "DOCTOR_latest.json").write_text(json.dumps({"lamp": lamp, "counts": {"should": 7, "scanned": 7, "skipped": []},
        "plugins": [{"key": "envmgr", "lamp": "GREEN" if fixed else lamp}], "plan": {"pip": [] if fixed else ["rich"], "conflicts": [], "dupes": []}}), encoding="utf-8")
    sys.exit(0)
if a[:1] == ["install"]:
    (via / "installed.flag").write_text("1", encoding="utf-8")
    sys.exit(0)
sys.exit(9)
'''


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("前版經 glob 載入(v0103)", PRIOR_PATH.name == FAMILY + "_v0103.py")
    chk("TAILAPI 轉接前版公開名稱", __getattr__("verify_backup") is PRIOR.verify_backup)
    chk("try 裡的匯入不算必要件 · 另列選配件", top_imports("import os\ntry:\n    import cv2\nexcept ImportError:\n    pass\nimport polars\n") == {"os", "polars"}
        and try_imports("import os\ntry:\n    import cv2\nexcept ImportError:\n    pass\n") == {"cv2"})
    keep_env = {k: os.environ.get(k) for k in ("FAKE_DOCTOR", "FAKE_GRAPH_RC", "VIA_PY_CORE", "VIA_PY_VDF", "VIA_PY_VRN", "LOCALAPPDATA")}
    try:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            repo = td / "repo"
            via = repo / "VeritasIntelligenceAnalytics"
            reg = via / "supportive modules" / "registry"
            reg.mkdir(parents=True)
            (via / "VCGC_CommandHub_v0116.py").write_text(FAKE_HUB, encoding="utf-8")
            (via / "supportive modules" / "network").mkdir()
            (via / "supportive modules" / "network" / "VeritasAegisNexus_v1652.py").write_text(
                "# [VIA:ACCEL-BRIDGE:v0111]\nimport json\nimport zz_not_installed_pkg\n", encoding="utf-8")
            (via / "supportive modules" / "VeritasCeleritas_v1141.py").write_text(
                "# [VIA:ACCEL-BRIDGE:v0111]\nimport os\ntry:\n    import numba\nexcept ImportError:\n    numba = None\n", encoding="utf-8")
            (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({
                "accelerator": {"path": "VeritasIntelligenceAnalytics/supportive modules/VeritasCeleritas_v1141.py"},
                "network": {"path": "VeritasIntelligenceAnalytics/supportive modules/network/VeritasAegisNexus_v1652.py"}}), encoding="utf-8")
            (reg / "VIA_Lib_Registry_v0100.json").write_text(json.dumps({"schema": "x", "ledger": [{"packages": [{"name": "rich==13"}]}]}), encoding="utf-8")
            for d, pat in BOOKS:
                (via / d).mkdir(parents=True, exist_ok=True)
                (via / d / pat.replace("v*", "v0101")).write_text('{"k": 1}', encoding="utf-8")
            (reg / "CGC_SystemManager_v0120.py").write_text("# [VIA:ACCEL-BRIDGE:v0111]\nimport sys\n", encoding="utf-8")
            for k in ("CORE", "VDF", "VRN"):
                os.environ["VIA_PY_" + k] = sys.executable
            g3 = gate_tools(via)
            chk("G3 缺件 = 紅並點名境與件", g3["lamp"] == "RED" and g3["missing"].get("core") == ["zz_not_installed_pkg"], str(g3.get("red")))
            chk("G3 入口尾版不在 = 簽章紅", any("VDF_SystemManager" in r for r in g3["red"]))
            chk("G3 三數(應 = 已掃)", g3["counts"]["should"] == g3["counts"]["scanned"])
            g1 = gate_graphify(via, ["VCGC", "VDF"])
            chk("G1 圖建好 + 三冊重產器跑過 + 三冊可解析", g1["lamp"] in ("GREEN", "YELLOW") and len(g1["books"]) == 3
                and g1["books_sync"].get("mode") == "apply", str((g1.get("red"), g1["books_sync"].get("tail", "")[-200:])))
            chk("--books-check-only = 只查", gate_graphify(via, ["VCGC"], books_apply=False)["books_sync"].get("mode") == "check")
            os.environ["FAKE_GRAPH_RC"] = "1"
            chk("G1 建圖失敗 = 紅", gate_graphify(via, ["VDF"])["lamp"] == "RED")
            os.environ.pop("FAKE_GRAPH_RC")
            g2 = gate_doctor(via)
            chk("G2 讀 doctor JSON(紅 · 計畫 rich)", g2["lamp"] == "RED" and g2["plan_pip"] == ["rich"])
            os.environ["LOCALAPPDATA"] = str(td / "local")
            chk("備份根預設 = LOCALAPPDATA/VIA/_via_backups", default_out() == td / "local" / "VIA" / "_via_backups")
            chk("備份根在倉內 = 拒絕零寫入", do_full(via, repo / "bk") == 1 and not (repo / "bk").exists())
            chk("備份根在 OneDrive = 拒絕", bad_out(td / "OneDrive" / "x", repo) is not None)
            out = td / "local" / "bk"
            rc = do_full(via, out, install=False)
            chk("Fail-Closed:不補裝時紅 → 不備份、備份根零寫入", rc == 1 and not out.exists(), f"rc {rc}")
            calls = (via / "hub_calls.txt").read_text(encoding="utf-8")
            chk("三閘都經中樞(graph build · doctor)", "graph build --sys VCGC" in calls and "doctor" in calls)
            (reg / "CGC_SystemManager_v0120.py").unlink()
            (via / "supportive modules" / "network" / "VeritasAegisNexus_v1652.py").write_text("# [VIA:ACCEL-BRIDGE:v0111]\nimport json\n", encoding="utf-8")
            for k, sub in (("vdf", "functional modules/VDF/VDF_SystemManager_v0191.py"), ("vrn", "functional modules/VRN/VRN_SystemManager_v0290.py"),
                           ("core", "supportive modules/registry/CGC_SystemManager_v0120.py")):
                (via / sub).parent.mkdir(parents=True, exist_ok=True)
                (via / sub).write_text("# [VIA:ACCEL-BRIDGE:v0111]\nimport json\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "t"], check=True)
            os.environ["FAKE_DOCTOR"] = "RED"
            rc = do_full(via, out, keep=5)
            calls = (via / "hub_calls.txt").read_text(encoding="utf-8")
            chk("缺件當輪補裝 → 重驗 → 備份(黃)", rc == 2 and "install --from-plan --yes" in calls, f"rc {rc}")
            snaps = sorted(p for p in out.iterdir() if re.fullmatch(r"\d{8}_\d{6}Z", p.name))
            ex = snaps[-1] / "extras" if snaps else td
            chk("extras:CODE · BOOKS · GRAPHIFY · GATES + SHA256SUMS", all((ex / f).exists() for f in
                ("CODE.zip", "BOOKS.zip", "BOOKS_FRAMES.zip", "GRAPHIFY.zip", "GATES.json", "SHA256SUMS.txt")))
            chk("沒有殘留 .sdd_tmp", not list(out.rglob("*.sdd_tmp")))
            sums = (ex / "SHA256SUMS.txt").read_text(encoding="utf-8").split()
            chk("SHA256SUMS = 實檔", sums[0] == sha256(ex / sums[1]))
            chk("MANIFEST 寫備份根 _manifests(倉內零寫入)", (out / "_manifests").is_dir() and not (via / "docs" / "handoff" / "backup").exists())
            chk("前版 restore 驗證認得這份備份", PRIOR.verify_backup(snaps[-1])["ok"])
            for i in range(6):
                (out / f"2026010{i}_000000Z").mkdir()
            gone = rotate(out, 5)
            left = sorted(p.name for p in out.iterdir() if re.fullmatch(r"\d{8}_\d{6}Z", p.name))
            chk("輪替留 5 份、刪最舊", len(left) == 5 and "20260100_000000Z" in gone and snaps[-1].name in left)
    finally:
        for k, v in keep_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
