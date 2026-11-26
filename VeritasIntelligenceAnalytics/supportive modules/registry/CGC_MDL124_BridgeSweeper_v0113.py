#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL124_BridgeSweeper v0113 — 薄尾(v0112 一字不動):`--effective` 提速 · 收起 SyntaxWarning

主機實跑 v0112(2026-11-25 21:38,操作員貼回):應掃 15404 · 已掃 1822 · 238.5s;13582 支落在 intake / site-packages / venv /
VIA_RetiredEngines 等排除夾,每支都還是先 rglob 出來再逐支問一次排除規則;NET 與 PS 又各自從頭 rglob 一遍(共三遍)。
另外被掃的舊檔裡有 `'\\C'` 之類的跳脫字元,ast.parse 在終端印 SyntaxWarning,洗掉進度條。

本版只換 `effective` 的檔案清單與解析,判定規則與輸出格式照 v0112:
  ① 一次 os.walk:碰到前版排除夾(EXCLUDE_PARTS · _backup*)整夾跳過,只數裡面的 .py 檔數(不讀檔、不問排除規則),
     略過理由照前版「第一個命中的夾名」記帳 → 三數(應掃 / 已掃 / 略過)與 v0112 相同。
  ② PY · NET · PS 共用這一份清單:NET 照前版 callers_only 判準(工具本體 / vendored → 排除;沒直呼網路原語 → 不算),
     PS 照前版 _excluded + _ps_excluded + 版史。每支 .py 只讀一次。
  ③ 語法樹解析收起 SyntaxWarning / DeprecationWarning(只是被掃檔自己的寫法,不影響判定)。
自測比對:同一棵樹,v0113 與 v0112 的各系統數字、非綠清單、略過總數逐項相同。零網路 · 零 TA-Lib · 不 import 他系統。
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

import collections
import importlib.util
import os
import re
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL124_BridgeSweeper"
VERSION = "v0113"


def _vnum_v0113(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum_v0113(p) < _vnum_v0113(__file__)), key=_vnum_v0113)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v

_BODY = PRIOR._BODY
_ACCEL_IMPORTS_V0112 = PRIOR.accel_imports


def accel_imports(src: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")          # 被掃檔自己的跳脫字元等寫法:不影響判定,不洗版
        return _ACCEL_IMPORTS_V0112(src)


PRIOR.accel_imports = accel_imports              # v0112 的 classify 從自己的模組全域找它


def _pruned_dir(name: str) -> str:
    if name in _BODY["EXCLUDE_PARTS"] or name.startswith("_backup"):
        return name
    return ""


def walk(via: Path):
    """一次走訪:回 (候選 .py 清單, 候選 .ps1 清單, 整夾略過的 .py 計數 Counter, 應掃 .py 總數)。"""
    py, ps, pruned, total = [], [], collections.Counter(), 0
    for root, dirs, files in os.walk(via):
        keep = []
        for d in dirs:
            why = _pruned_dir(d)
            if why == ".git":                         # v0112 的清單本來就不含 .git 底下
                continue
            if why:
                n = sum(1 for _r, _d, fs in os.walk(os.path.join(root, d)) for f in fs if f.endswith(".py"))
                if n:
                    pruned[why] += n
                    total += n
            else:
                keep.append(d)
        dirs[:] = sorted(keep)
        for f in sorted(files):
            if f.endswith(".py"):
                total += 1
                py.append(Path(root) / f)
            elif f.endswith(".ps1"):
                ps.append(Path(root) / f)
    return py, ps, pruned, total


def effective(apply: bool = False, scope: str = "vcgc", write: bool = True, via: Path | None = None) -> dict:
    via = Path(via or _BODY["VIA"]).resolve()
    sup = via / "supportive modules"
    probe = PRIOR.runtime_probe(sup)
    locks = PRIOR.locked_paths(via)
    bodies = PRIOR.tool_bodies(via)
    t0 = datetime.now(timezone.utc)
    py_files, ps_files, skipped, n_all = walk(via)
    rows, net = [], []
    net_start = _BODY["NET_START"]
    for i, p in enumerate(py_files, 1):
        PRIOR._progress(i, len(py_files), "PY")
        rel = str(p.relative_to(via)).replace("\\", "/")
        why = _BODY["_excluded"](p)
        if not why and PRIOR.is_tool_body(rel, bodies):
            why = "加速器 / 網路工具本體(不導入自己)"
        if why:
            skipped[why if len(why) < 40 else why[:40] + "…"] += 1
            continue
        st, note = PRIOR.classify(p, probe)
        rows.append({"file": rel, "sys": PRIOR.system_of(rel), "state": st, "note": note})
        try:                                          # NET:同一份清單、照前版 callers_only 判準
            src = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _BODY["_caller_untouchable"](p, src) or not _BODY["_is_net_caller"](src):
            continue
        net.append({"file": rel, "sys": PRIOR.system_of(rel),
                    "state": "HAS" if (net_start in src or "via_net_unified_v" in src) else "MISSING"})
    ps_rows = []
    for p in ps_files:
        ex = _BODY["_excluded"](p) or _BODY["_ps_excluded"](p)
        rel = str(p.relative_to(via)).replace("\\", "/")
        if ex:
            ps_rows.append({"file": rel, "state": "EXCLUDED", "why": ex})
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        ps_rows.append({"file": rel, "state": "HAS" if (_BODY["PS_START"] in t or "VIA_PS_Accel_Module.ps1" in t) else "MISSING", "why": ""})
    hist = set(_BODY["_ps_history"](ps_rows)) if "_ps_history" in _BODY else set()
    ps_mod = sup / "VIA_PS_Accel_Module.ps1"
    ps_rt = PRIOR._pwsh_probe(ps_mod) if ps_mod.is_file() else "模組不在"
    ps = []
    for r in ps_rows:
        if r["state"] == "EXCLUDED" or r["file"] in hist:
            continue
        st = r["state"]
        if st == "HAS":
            st = "EFFECTIVE" if ps_rt == "ok" else ("UNRESOLVED" if ps_rt == "模組不在" or ps_rt.startswith("rc ") else "HAS_UNTESTED")
        ps.append({"file": r["file"], "sys": PRIOR.system_of(r["file"]), "state": st})
    acts = []
    if apply:
        todo = [r for r in rows if r["state"] in ("MISSING", "MARKER_ONLY")] + [dict(r, state="NET_MISSING") for r in net if r["state"] == "MISSING"]
        for j, r in enumerate(todo, 1):
            PRIOR._progress(j, len(todo), "APPLY")
            if scope != "all" and r["sys"] != "VCGC":
                acts.append({"file": r["file"], "kind": r["state"], "result": "OUT_OF_SCOPE", "why": "%s 的檔由它自己的管理器處理" % r["sys"]})
                continue
            if r["file"] in locks:
                acts.append({"file": r["file"], "kind": r["state"], "result": "LOCKED", "why": "成功鎖點名;換版時帶橋"})
                continue
            a = _BODY["inject"](r["file"], "net" if r["state"] == "NET_MISSING" else "accel", True)
            acts.append({"file": r["file"], "kind": r["state"], "result": a["state"], "why": a.get("why", "")})
        done = {a["file"] for a in acts if a["result"] == "INJECTED"}
        for r in rows:
            if r["file"] in done:
                r["state"], r["note"] = PRIOR.classify(via / r["file"], probe)
        for r in net:
            if r["file"] in done:
                r["state"] = "HAS"
    for r in rows:
        if r["state"] in ("MISSING", "MARKER_ONLY") and r["file"] in locks:
            r["note"] = (r["note"] + " · " if r["note"] else "") + "成功鎖點名(換版時帶橋)"
    rep = PRIOR.summarize(rows, net, ps, skipped, probe, ps_rt, acts, apply, scope, n_all, t0, via)
    rep["tool"] = "%s %s" % (STEM, VERSION)
    if write:
        PRIOR.write_outputs(rep, via)
    return rep


PRIOR.effective = effective                       # v0112 main 叫的是自己模組的 effective


def _key(rep: dict) -> dict:
    return {"systems": rep["systems"], "not_green": sorted((x["state"], x["file"]) for x in rep["not_green"]),
            "should": rep["should_scan"], "scanned": rep["scanned"], "skipped": rep["skipped"], "total": rep["total"]}


def selftest() -> int:
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + n + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s %s 自測開始(本版 5 項 · 前版 %s 在子行程)" % (STEM, VERSION, PRIOR_PATH.name), flush=True)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        mods, err = accel_imports("x = '\\C'\nimport VIA_SuperAccel_Module as VIA_ACCEL\n")
    chk("T1 被掃檔的無效跳脫字元:照樣判出導入,而且不印 SyntaxWarning", mods == {"VIA_SuperAccel_Module"} and not err
        and not [x for x in w if issubclass(x.category, SyntaxWarning)], (mods, err, [str(x.message) for x in w]))
    via = Path(_BODY["VIA"]).resolve()
    t1 = time.time()
    new = effective(write=False, via=via)
    t_new = time.time() - t1
    code = ("import importlib.util,json,sys\ns=importlib.util.spec_from_file_location('p',sys.argv[1]);m=importlib.util.module_from_spec(s);"
            "sys.modules['p']=m;s.loader.exec_module(m)\nr=m.effective(write=False)\n"
            "print('@@'+json.dumps({'systems':r['systems'],'not_green':sorted([x['state'],x['file']] for x in r['not_green']),"
            "'should':r['should_scan'],'scanned':r['scanned'],'skipped':r['skipped'],'total':r['total']},ensure_ascii=False))")
    t2 = time.time()
    cp = subprocess.run([sys.executable, "-B", "-c", code, str(PRIOR_PATH)], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=1800, env=dict(os.environ, PYTHONWARNINGS="ignore"))
    t_old = time.time() - t2
    import json
    line = [x for x in cp.stdout.splitlines() if x.startswith("@@")]
    old = json.loads(line[-1][2:]) if line else {}
    mine = json.loads(json.dumps(_key(new), ensure_ascii=False))
    mine["not_green"] = [list(x) for x in mine["not_green"]]
    chk("T2 同一棵樹:各系統數字 · 非綠清單 · 應掃 / 已掃 / 略過 與 v0112 逐項相同", old and mine == old,
        {k: (mine.get(k), old.get(k)) for k in mine if mine.get(k) != old.get(k)})
    cand, _ps, pruned, total = walk(via)
    print("  [注] 計時(資訊,不判):本版 %.1fs · v0112 %.1fs(含子行程啟動);整夾略過 %d 支不逐支讀" % (t_new, t_old, sum(pruned.values())), flush=True)
    chk("T3 整夾略過的檔不逐支讀:候選 %d = 應掃 %d − 整夾略過 %d" % (len(cand), total, sum(pruned.values())),
        len(cand) == total - sum(pruned.values()) and total == new["should_scan"])
    cp2 = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=1800)
    chk("T4 前版 %s 自測照過(子行程)" % PRIOR_PATH.name, cp2.returncode == 0, [x for x in cp2.stdout.splitlines() if "FAIL" in x][:3])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T5 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M))
    n = sum(ok)
    print("[計] %s %s 自測 %d/%d · %s" % (STEM, VERSION, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if a == ["--selftest"]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
