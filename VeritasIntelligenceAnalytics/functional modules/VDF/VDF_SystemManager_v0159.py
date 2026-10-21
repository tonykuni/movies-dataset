#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [改號接線 2026-10-20] 本檔 = 工作站分支 workstation-20261020 的 VDF_SystemManager v0155 原文,改號 v0159 接到 main 尾版之上(兩條線同號不同內容;操作員裁定「接到 main 上」)。
#   只改寫死的本版版號;文中其他 v0155 字樣指工作站線的同一支(即本線 v0159)。前版照 glob 取本族比本檔小的最大一支 = main 的尾版。
"""VDF_SystemManager v0155 — 薄尾:`all` 一鍵全部(健康 → 啟動就緒 → 問參數頁啟動全部擷取 → 族群並行擷取 → 輸入清單 → USER-TEST → 頁 → 跳出)+ 啟動就緒門回來

操作員令(2026-10-12):「給我一個啟動VDF啟動全部及HTML U/I 的指令並在上面操作」→ 貼回 Open-VIA-VDF 問參數頁 → 「INTEGRATE ALL ABOVE INTO ONE」。
之前分開給的:Open-VIA-VDF(問參數頁 → 11 步擷取 → 資料庫狀況頁)· VDF_MDL012_FetchGroups run(清單引擎 009 · 010 先跑 → 依庫分道並行)·
  usertest(功能鍵實測)· ui(族群頁)· VDF_SystemManager ui(主頁)· via-groups-ui(跳出)。本版合成一個動詞:
  all [--groups ALL] [--jobs auto] [--mode live] [--no-ask] [--skip a,b] [--no-open] [--dry]
    ① health      VDF 健康(本管理員 health)
    ② ready       啟動就緒(本版 read_launch;問參數頁上那一格之前是 ABSENT,見下)
    ③ ask         Open-VIA-VDF 尾版(pwsh 子行程;問參數頁 → 你在頁上按啟動 → 11 步擷取 → 資料庫狀況頁);沒有 pwsh / 沒有檔 / --no-ask → 跳過照實記
    ④ groups      VDF_MDL012_FetchGroups 尾版 run --groups … --jobs … --mode …(清單引擎先跑,紅就停 rc 5 → 後面的步 SKIP;雙閘沒開 rc 4 = GATED 黃,不是壞)
    ⑤ lists       universe list(範圍冊 + 市場清單 → 輸入清單 OUT-01)
    ⑥ usertest    族群頁功能鍵實測(有瀏覽器 headless 逐鍵點)
    ⑦ page        族群頁重建(結果掛頁)   ⑧ hub  本管理員 ui(VDF 主頁)   ⑨ open  跳出族群頁(VIA_NO_OPEN=1 / --no-open 不開)
  每步一列(燈 · rc · 秒 · 說明),總燈 = 最壞;報告 VIA_Reports/vdf/ONE_LAUNCH_latest.json(+ ONE_LAUNCH_runs.jsonl 只增)。
啟動就緒門:VDF_ENG093 問參數頁的「啟動就緒」讀 VDF_SystemManager 尾版的 read_launch;本體在 v0104,薄尾鏈到 v0154 已經接不到 → 頁上 ABSENT。
  本版 read_launch(probe=False, environ=None) 直接載 v0104 本體代答(只量不動手;同意閘永不代設)。
子行程:python 引擎走前版鏈的 run_path(v0149,唯一起 python 子行程的地方);pwsh 啟動器走本版 run_cmd_v0155(本版唯一起子行程的地方)。
不載入 VCGC 程式(ENG093 那條 11 步鏈由 Open-VIA-VDF 自己管)· 不代設同意閘 · 零網路(連網全在引擎子行程)· 不碰 TA-Lib。
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

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0159"
SELF_ID = "VDF"
STEPS_V0155 = ("health", "ready", "ask", "groups", "lists", "usertest", "page", "hub", "open")
GROUPS_PAGE = VIA_ROOT / "supportive modules" / "ui_support" / "VIA_UI_VDFFetchGroups_v0100.html"
JOBS_RANGE = (1, 5)


def _vnum_v0155(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0155(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0155(p) < _vnum_v0155(__file__)), key=_vnum_v0155)
PRIOR = _load_v0155(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _out_dir() -> Path:
    return Path(os.environ.get("VIA_VDF_HEALTH_OUT") or (Path(os.environ.get("VIA_VDF_HOME") or HERE).parents[1] / "VIA_Reports" / "vdf"))


# ---------------------------------------------------------------- 啟動就緒門(問參數頁讀的 read_launch)
_DOOR = {"mod": None, "why": None}


def _door_v0104():
    """read_launch 本體在 v0104;薄尾鏈接不到 → 直接載那一支代答。載不到回 (None, why)。"""
    if _DOOR["mod"] is None and _DOOR["why"] is None:
        p = HERE / (_STEM + "_v0104.py")
        if not p.is_file():
            _DOOR["why"] = f"{p.name} 不在(啟動就緒本體缺)"
        else:
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    _DOOR["mod"] = _load_v0155(p, _STEM + "_door_v0104_for_" + TAG)
            except Exception as exc:
                _DOOR["why"] = f"{p.name} 載入炸 {type(exc).__name__}: {str(exc)[:120]}"
    return _DOOR["mod"], _DOOR["why"]


def read_launch(probe: bool = False, environ=None) -> dict:
    """啟動就緒(只量不動手;同意閘永不代設):委派 v0104 本體;本體缺席回 ABSENT + why(不編)。"""
    m, why = _door_v0104()
    if m is None or not callable(getattr(m, "read_launch", None)):
        return {"state": "ABSENT", "rc": 2, "why": why or "v0104 沒有 read_launch", "via": TAG, "consent": {}, "python": {}, "hist_limit": {}, "next": []}
    with contextlib.redirect_stdout(io.StringIO()):
        r = m.read_launch(probe=probe, environ=environ)
    r = dict(r)
    r["via"] = TAG
    r["door"] = "v0104 本體代答(v0155)"
    return r


# ---------------------------------------------------------------- 子行程(python 走前版 run_path;pwsh 走這裡,本版唯一起子行程的地方)
def run_cmd_v0155(cmd: list, timeout=None) -> dict:
    """啟動器子行程(pwsh);stdout / stderr 直通本視窗(頁與進度要讓操作員看到)。env 只加 VIA_FROM_VCGC=YES;同意閘不加不減。"""
    import subprocess
    env = dict(os.environ, VIA_FROM_VCGC="YES")
    t0 = time.time()
    try:
        r = subprocess.run([str(c) for c in cmd], cwd=str(VIA_ROOT), env=env, timeout=timeout)
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc = "TIMEOUT"
    except OSError as exc:
        rc = f"OSERROR:{type(exc).__name__}"
    return {"rc": rc, "secs": round(time.time() - t0, 1)}


def _run_py(path: Path, args: list, capture: bool, timeout=None) -> dict:
    return PRIOR.run_path(path, args, timeout=timeout, capture=capture)


def _run_in(argv: list) -> dict:
    """本管理員自己的動詞,同行程跑(前版鏈 main),stdout 先收再原樣印出;回 rc 與尾三行。"""
    buf = io.StringIO()
    t0 = time.time()
    try:
        with contextlib.redirect_stdout(buf):
            rc = PRIOR.main(list(argv))
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else 1
    except Exception as exc:
        buf.write(f"[例外] {type(exc).__name__}: {exc}\n")
        rc = 1
    txt = buf.getvalue()
    sys.stdout.write(txt)
    return {"rc": rc, "secs": round(time.time() - t0, 1), "tail": [ln for ln in txt.splitlines() if ln.strip()][-3:]}


RUN_PY, RUN_CMD, RUN_IN, READY = _run_py, run_cmd_v0155, _run_in, read_launch   # 自測換替身(不起真子行程 · 不量真環境)


def _vnum_any(path) -> int:
    """版號:_vNNNN(python 尾版)或 -vNNNN(PowerShell 啟動器 Open-VIA-VDF-v0103.ps1)都認;沒有版號 = -1。"""
    m = re.search(r"[-_]v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _tail(glob: str, folder: Path):
    hits = sorted(folder.glob(glob), key=_vnum_any)
    return hits[-1] if hits else None


def _auto_jobs() -> int:
    lo, hi = JOBS_RANGE
    return max(lo, min(hi, (os.cpu_count() or 2) - 1))


def _lamp(rc, yellow=(2,), skip=False) -> str:
    if skip:
        return "SKIP"
    if rc == 0:
        return "GREEN"
    if rc in yellow:
        return "YELLOW"
    return "RED"


def plan_all(opts: dict) -> dict:
    """一鍵全部的計畫(不起子行程、不寫檔):各步要跑什麼、用哪支尾版、會不會跳過與原因。"""
    mdl012 = _tail("VDF_MDL012_FetchGroups_v*.py", HERE)
    opener = _tail("Open-VIA-VDF-v*.ps1", VIA_ROOT)
    pwsh = shutil.which("pwsh")
    jobs = _auto_jobs() if str(opts.get("jobs", "auto")).lower() == "auto" else max(JOBS_RANGE[0], min(JOBS_RANGE[1], int(opts["jobs"])))
    skip = set(opts.get("skip") or [])
    if opts.get("no_ask"):
        skip.add("ask")
    if opts.get("no_open") or os.environ.get("VIA_NO_OPEN") == "1":
        skip.add("open")
    steps = []
    for s in STEPS_V0155:
        d = {"step": s, "skip": s in skip, "why": "", "what": ""}
        if s == "health":
            d["what"] = f"{PRIOR_PATH.name} health"
        elif s == "ready":
            d["what"] = "read_launch(probe=False)(v0104 本體代答)"
        elif s == "ask":
            d["what"] = f"pwsh ← {opener.name if opener else 'Open-VIA-VDF-v*.ps1'}(問參數頁 → 11 步擷取 → 資料庫狀況頁)"
            if not d["skip"] and opener is None:
                d["skip"], d["why"] = True, "Open-VIA-VDF-v*.ps1 不在 VIA 根"
            elif not d["skip"] and pwsh is None:
                d["skip"], d["why"] = True, "pwsh 不在 PATH(容器 / 非 Windows):問參數頁要工作站開"
        elif s == "groups":
            d["what"] = f"{mdl012.name if mdl012 else 'VDF_MDL012_FetchGroups_v*.py'} run --groups {opts.get('groups', 'ALL')} --jobs {jobs} --mode {opts.get('mode', 'live')}" + (" --dry" if opts.get("dry") else "")
            if not d["skip"] and mdl012 is None:
                d["skip"], d["why"] = True, "VDF_MDL012_FetchGroups_v*.py 不在"
        elif s == "lists":
            d["what"] = f"{PRIOR_PATH.name} universe list(範圍冊 + 市場清單 → 輸入清單 OUT-01)"
        elif s == "usertest":
            d["what"] = f"{mdl012.name if mdl012 else '—'} usertest"
        elif s == "page":
            d["what"] = f"{mdl012.name if mdl012 else '—'} ui → {GROUPS_PAGE.name}"
        elif s == "hub":
            d["what"] = f"{PRIOR_PATH.name} ui → {_out_dir() / (SELF_ID + '_UI_latest.html')}"
        elif s == "open":
            d["what"] = f"跳出 {GROUPS_PAGE.name}(主頁路徑印出)"
            if d["skip"] and not d["why"]:
                d["why"] = "VIA_NO_OPEN=1 / --no-open"
        if d["skip"] and not d["why"]:
            d["why"] = "--skip / --no-ask"
        steps.append(d)
    return {"steps": steps, "mdl012": str(mdl012) if mdl012 else None, "opener": str(opener) if opener else None, "pwsh": pwsh, "jobs": jobs,
            "groups": opts.get("groups", "ALL"), "mode": opts.get("mode", "live"), "dry": bool(opts.get("dry"))}


def run_all(plan: dict, log=None) -> dict:
    """照計畫跑;每步一列;groups 回 5(清單引擎紅)→ 後面的步 SKIP;總燈 = 最壞(SKIP 不算)。"""
    log = log or (lambda s: print(s, flush=True))
    rows, stop = [], None
    mdl012 = Path(plan["mdl012"]) if plan.get("mdl012") else None
    me = Path(__file__)
    for d in plan["steps"]:
        s = d["step"]
        row = {"step": s, "lamp": "SKIP", "rc": None, "secs": 0.0, "note": d["why"], "what": d["what"]}
        if d["skip"] or stop:
            if stop and not d["skip"]:
                row["note"] = f"前步 {stop} 紅 → 不起"
            rows.append(row)
            log(f"  [SKIP ] {s:<9} {row['note']}")
            continue
        log(f"  ── {s} · {d['what']}")
        t0 = time.time()
        try:
            if s == "health":
                r = RUN_IN(["health"])
                row.update(rc=r["rc"], lamp=_lamp(r["rc"]), note=(r.get("tail") or [""])[-1][:160])
            elif s == "ready":
                rd = READY(probe=False)
                st = str(rd.get("state"))
                row.update(rc=rd.get("rc"), lamp={"GREEN": "GREEN", "GATED": "YELLOW", "ABSENT": "YELLOW"}.get(st, "RED") if st != "RED" else "RED",
                           note=f"{st} · 閘 {json.dumps(rd.get('consent') or {}, ensure_ascii=False)[:120]} · {rd.get('why') or ''}"[:200])
                log(f"  [啟動就緒] {row['note']}")
            elif s == "ask":
                r = RUN_CMD(["pwsh", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f". '{plan['opener']}'"])
                row.update(rc=r["rc"], lamp=_lamp(r["rc"], yellow=(2,)), note="問參數頁 → 擷取 → 狀況頁(rc 0 完成 / 不啟動 · 2 逾時沒決定 · 其他 = 引擎紅)")
            elif s == "groups":
                args = ["run", "--groups", plan["groups"], "--jobs", str(plan["jobs"]), "--mode", plan["mode"]] + (["--dry"] if plan["dry"] else [])
                r = RUN_PY(mdl012, args, False)
                rc = r["rc"]
                row.update(rc=rc, lamp="YELLOW" if rc == 4 else _lamp(rc), note={4: "GATED:雙閘沒開(本視窗 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT,操作員的手)", 5: "清單引擎紅 → 停", 0: "清單先跑 → 分道並行 完成"}.get(rc, f"rc {rc}:有引擎失敗(看 _fetch_groups/PARALLEL_latest.json)"))
                if rc == 5:
                    stop = s
            elif s == "lists":
                r = RUN_IN(["universe", "list"])
                row.update(rc=r["rc"], lamp=_lamp(r["rc"]), note=(r.get("tail") or [""])[0][:160] if r.get("tail") else "")
            elif s == "usertest":
                r = RUN_PY(mdl012, ["usertest"], True)
                row.update(rc=r["rc"], lamp=_lamp(r["rc"]), note=(r.get("tail") or [""])[-1][:160])
            elif s == "page":
                r = RUN_PY(mdl012, ["ui"], True)
                row.update(rc=r["rc"], lamp=_lamp(r["rc"]), note=(r.get("tail") or [""])[0][:160] if r.get("tail") else "")
            elif s == "hub":
                r = RUN_IN(["ui"])
                row.update(rc=r["rc"], lamp=_lamp(r["rc"]), note=(r.get("tail") or [""])[-1][:160])
            elif s == "open":
                ok = False
                if GROUPS_PAGE.is_file():
                    import webbrowser
                    ok = bool(webbrowser.open(GROUPS_PAGE.resolve().as_uri()))
                row.update(rc=0 if ok else 2, lamp="GREEN" if ok else "YELLOW", note=f"族群頁 {GROUPS_PAGE}" + ("" if ok else "(瀏覽器沒開成 / 頁不在)") + f" · 主頁 {_out_dir() / (SELF_ID + '_UI_latest.html')}")
        except Exception as exc:
            row.update(rc=1, lamp="RED", note=f"{type(exc).__name__}: {str(exc)[:160]}")
        row["secs"] = round(time.time() - t0, 1)
        rows.append(row)
        log(f"  [{row['lamp']:<5}] {s:<9} rc {row['rc']} · {row['secs']:.0f}s · {row['note']}")
    order = {"RED": 3, "YELLOW": 2, "GREEN": 1, "SKIP": 0}
    worst = max((r["lamp"] for r in rows), key=lambda L: order[L], default="SKIP")
    return {"rows": rows, "lamp": worst, "stopped_at": stop}


def cmd_all(argv: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog=f"{_STEM} {TAG} all", description="一鍵全部:健康 → 啟動就緒 → 問參數頁啟動 → 族群並行 → 輸入清單 → USER-TEST → 頁 → 主頁 → 跳出")
    ap.add_argument("--groups", default="ALL"); ap.add_argument("--jobs", default="auto"); ap.add_argument("--mode", default="live", choices=["live", "fixture", "block"])
    ap.add_argument("--no-ask", action="store_true"); ap.add_argument("--no-open", action="store_true"); ap.add_argument("--skip", default="")
    ap.add_argument("--dry", action="store_true", help="只列計畫(族群那步也帶 --dry);不起子行程、不寫檔")
    a = ap.parse_args(argv)
    opts = {"groups": a.groups, "jobs": a.jobs, "mode": a.mode, "no_ask": a.no_ask, "no_open": a.no_open, "dry": a.dry,
            "skip": [x.strip() for x in a.skip.split(",") if x.strip()]}
    bad = [x for x in opts["skip"] if x not in STEPS_V0155]
    if bad:
        print(f"[拒跑] --skip 不認得 {bad}(可用:{' · '.join(STEPS_V0155)})")
        return 2
    plan = plan_all(opts)
    print(f"[VDF 一鍵全部 {TAG}] 步 {len(plan['steps'])} · 族群 {plan['groups']} · 流程 {plan['jobs']} · 模式 {plan['mode']} · 啟動器 {Path(plan['opener']).name if plan['opener'] else '—'} · pwsh {plan['pwsh'] or '—'} · 族群尾版 {Path(plan['mdl012']).name if plan['mdl012'] else '—'}")
    for d in plan["steps"]:
        print(f"  {'跳過' if d['skip'] else '  跑'} {d['step']:<9} {d['what']}" + (f" · {d['why']}" if d["why"] else ""))
    if a.dry:
        print("  (--dry:只列計畫,不起子行程、不寫檔)")
        return 0
    started = _now()
    out = run_all(plan)
    rep = {"via": TAG, "started": started, "finished": _now(), "lamp": out["lamp"], "stopped_at": out["stopped_at"], "plan": {k: v for k, v in plan.items() if k != "steps"},
           "rows": out["rows"], "groups_page": str(GROUPS_PAGE), "hub_page": str(_out_dir() / (SELF_ID + "_UI_latest.html"))}
    od = _out_dir()
    od.mkdir(parents=True, exist_ok=True)
    (od / "ONE_LAUNCH_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with (od / "ONE_LAUNCH_runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"started": started, "finished": rep["finished"], "lamp": out["lamp"], "rows": [(r["step"], r["lamp"], r["rc"], r["secs"]) for r in out["rows"]]}, ensure_ascii=False, default=str) + "\n")
    print(f"[計] {_STEM}_{TAG} all · {out['lamp']} · " + " · ".join(f"{r['step']} {r['lamp']}" for r in out["rows"]) + f" · 報告 {od / 'ONE_LAUNCH_latest.json'}")
    return {"GREEN": 0, "YELLOW": 2, "SKIP": 2}.get(out["lamp"], 1)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["all"]:
        return cmd_all(args[1:])
    return PRIOR.main(args)


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 薄尾自測(all 一鍵全部 + 啟動就緒門)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="pv_vdf155_"))
    keep = {k: os.environ.get(k) for k in ("VIA_NO_OPEN", "VIA_VDF_HEALTH_OUT")}
    g = globals()
    keep_run = (g["RUN_PY"], g["RUN_CMD"], g["RUN_IN"], g["READY"])
    try:
        rd = read_launch(probe=False)
        chk("① 啟動就緒門:read_launch 由 v0104 本體代答(有 state · consent · python · hist_limit;同意閘只讀)",
            isinstance(rd, dict) and rd.get("door", "").startswith("v0104") and all(k in rd for k in ("state", "consent", "python", "hist_limit"))
            and str(rd.get("state")) in ("GREEN", "GATED", "ABSENT", "RED", "YELLOW"), {k: rd.get(k) for k in ("state", "why", "door")})
        try:
            e93 = _tail("VDF_ENG093_LaunchConsole_v*.py", HERE)
            with contextlib.redirect_stdout(io.StringIO()):
                m93 = _load_v0155(e93, "eng093_for_" + TAG)
                r93 = m93.readiness()
        except Exception as exc:
            r93 = {"state": "EXC", "why": f"{type(exc).__name__}: {exc}"}
        chk("② 問參數頁那一格:ENG093 readiness() 經尾版門拿到狀態(不再是 ABSENT 空因由)",
            str(r93.get("state")) not in ("EXC",) and not (r93.get("state") == "ABSENT" and not r93.get("why")) and ("gates" in r93 or r93.get("why")),
            {k: r93.get(k) for k in ("state", "src", "why")})
        os.environ["VIA_VDF_HEALTH_OUT"] = str(td / "out")
        os.environ["VIA_NO_OPEN"] = "1"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_dry = main(["all", "--dry", "--jobs", "9"])
        txt = buf.getvalue()
        openers = sorted(VIA_ROOT.glob("Open-VIA-VDF-v*.ps1"), key=_vnum_any)
        chk("③ all --dry:列 9 步 · 流程夾到 5 · 啟動器取 Open-VIA-VDF 最大版號(-vNNNN 也認)· pwsh 缺就跳過 ask 並講原因 · 不寫檔 rc 0",
            rc_dry == 0 and all(s in txt for s in STEPS_V0155) and "流程 5" in txt and ("跳過 ask" in txt or "pwsh" in txt) and not (td / "out").exists()
            and (not openers or f"啟動器 {openers[-1].name}" in txt) and _vnum_any("Open-VIA-VDF-v0103.ps1") == 103 and _vnum_any("X_v0159.py") == 159,
            (txt[:300], openers[-1].name if openers else None))
        calls = []

        def st_py(path, args, capture, timeout=None):
            calls.append(("py", Path(path).name, tuple(args)))
            return {"rc": 5 if args[:1] == ["run"] and g["_FAKE_RC5"] else 0, "secs": 0.1, "tail": ["ok"]}

        def st_cmd(cmd, timeout=None):
            calls.append(("cmd", cmd[0], tuple(cmd[1:])))
            return {"rc": 0, "secs": 0.1}

        def st_in(argv):
            calls.append(("in", argv[0], tuple(argv[1:])))
            return {"rc": 0, "secs": 0.1, "tail": ["[計] fake"]}

        g["RUN_PY"], g["RUN_CMD"], g["RUN_IN"] = st_py, st_cmd, st_in
        g["READY"] = lambda probe=False, environ=None: {"state": "GATED", "rc": 2, "consent": {"VIA_NET_CONSENT": "UNSET", "VIA_SCRAPE_CONSENT": "UNSET"}, "why": ""}
        g["_FAKE_RC5"] = False
        plan = plan_all({"groups": "ALL", "jobs": 3, "mode": "block", "skip": ["ask"], "no_open": True})
        o1 = run_all(plan, log=lambda s: None)
        seq = [c[0] + ":" + (c[1] if c[0] != "py" else c[2][0]) for c in calls]
        chk("④ 替身跑:步序 health → ready → groups(run) → lists(universe) → usertest → page(ui) → hub(ui);就緒 GATED = 黃不擋;ask / open 跳過",
            o1["lamp"] == "YELLOW" and seq == ["in:health", "py:run", "in:universe", "py:usertest", "py:ui", "in:ui"]
            and [r["lamp"] for r in o1["rows"]] == ["GREEN", "YELLOW", "SKIP", "GREEN", "GREEN", "GREEN", "GREEN", "GREEN", "SKIP"], (seq, [r["lamp"] for r in o1["rows"]]))
        calls.clear()
        g["_FAKE_RC5"] = True
        o2 = run_all(plan, log=lambda s: None)
        chk("⑤ 清單引擎紅(groups rc 5)→ 後面的步 SKIP 並註明;總燈 RED;report 寫得出來",
            o2["lamp"] == "RED" and o2["stopped_at"] == "groups" and [r["lamp"] for r in o2["rows"][4:]] == ["SKIP"] * 5
            and all("前步 groups 紅" in r["note"] for r in o2["rows"][4:8]) and not any(c[0] == "py" and c[2][0] in ("usertest", "ui") for c in calls),
            [(r["step"], r["lamp"], r["note"][:30]) for r in o2["rows"]])
        g["_FAKE_RC5"] = False
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_all = main(["all", "--skip", "ask", "--no-open", "--mode", "block"])
        repp = td / "out" / "ONE_LAUNCH_latest.json"
        rep = json.loads(repp.read_text(encoding="utf-8")) if repp.is_file() else {}
        chk("⑥ main all(替身)總燈 YELLOW rc 2 · [計] 行 · 報告 ONE_LAUNCH_latest.json + runs.jsonl 一行(步 · 燈 · rc · 秒)",
            rc_all == 2 and "[計] %s_%s all · YELLOW" % (_STEM, TAG) in buf.getvalue() and rep.get("lamp") == "YELLOW" and len(rep.get("rows") or []) == 9
            and (td / "out" / "ONE_LAUNCH_runs.jsonl").read_text(encoding="utf-8").count("\n") == 1, buf.getvalue()[-300:])
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑦ 橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式 · 子行程只在 run_cmd_v0155 一處(python 走前版 run_path)· 不載外部函式庫",
            all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
            and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "1" not in body.replace("CGC_MDL" + "137", "")
            and body.count("import " + "subprocess") == 1 and "cdn" + "js" not in body)
    finally:
        g["RUN_PY"], g["RUN_CMD"], g["RUN_IN"], g["READY"] = keep_run
        g.pop("_FAKE_RC5", None)
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s_%s 自測 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
