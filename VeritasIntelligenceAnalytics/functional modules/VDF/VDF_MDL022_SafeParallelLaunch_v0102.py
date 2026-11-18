#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_MDL022_SafeParallelLaunch v0102 — 結果併進總燈(回傳碼 0 不等於資料到齊)+ 同意閘開著時真的補擷取。

容器實跑 v0101(2026-11-16)查到兩個缺口,本版補上(v0101 一字不動;本版薄尾,只換它的三個名字):
  ① 假綠:總經交叉比對 12 對全是 NODATA,流程回 0,v0101 記成綠;擷取被同意閘擋下(GATED)、擷取矩陣「到齊 0」也只看回傳碼。
     本版跑完讀三支流程自己的日誌:擷取矩陣(到齊 / 待補 / 缺 / 未量)· 分道擷取是否 GATED · 總經每一對的判定,
     有沒到齊 / 沒比到的就是黃並點名;總燈不會是綠。
  ② 補擷取沒真的寫:ActivateVDF 的資料庫流程沒帶 --refill-apply 只列計畫。本版在兩道同意閘都開著(操作員自己設)或
     操作員明給 --refill-apply 時,把 --refill-apply 交給 ActivateVDF(它的正式用法);閘沒開就照舊只列計畫,並在總結點名。
不做的:不設同意閘、不安裝、不出網(出網的是 ActivateVDF 底下各擷取引擎,走它們自己的網路橋與雙閘)。
rc:0 全綠 · 2 有黃 · 1 有紅。用法同 v0101,多一個旗標:run [--refill-apply] · check · --selftest
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(本啟動器零連線,橋只為全樹契約齊備) =====
VIA_NET_TOOL_PATH = None


def _via_net():
    """本啟動器**零連線**:出網的是它起的擷取引擎(各自帶網路橋與雙閘);本函式永遠回 None。"""
    return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

SYSTEM = "VDF"
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0102"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / f"{STEM}_v0101.py"
GATES = ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


B = _load(PRIOR_PATH, "vdf_launch_prior_for_" + VERSION)
_ORIG = {}
_CTX = {"refill": False}


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(B, name)


def gates_open(env=None) -> bool:
    env = os.environ if env is None else env
    return all(str(env.get(g, "")).upper() in ("YES", "1", "TRUE") for g in GATES)


def parse(argv: list) -> dict:
    a = _ORIG["parse"]([x for x in argv if x != "--refill-apply"])
    a["refill_apply"] = "--refill-apply" in argv or gates_open()
    _CTX["refill"] = a["refill_apply"]
    return a


def build_jobs(t: dict, a: dict, py: str = sys.executable) -> list:
    jobs = _ORIG["build_jobs"](t, a, py)
    if a.get("refill_apply"):
        for j in jobs:
            if j["id"] == "fetch" and "--refill-apply" not in j["cmd"]:
                j["cmd"] = list(j["cmd"]) + ["--refill-apply"]
                j["title"] += " · 補擷取真的寫(--refill-apply)"
    return jobs


_MATRIX_RX = re.compile(r"\[擷取矩陣\]\s*表\s*(\d+)\s*·\s*到齊\s*(\d+)\s*·\s*待補\s*(\d+)\s*·\s*缺\s*(\d+)\s*·\s*未量\s*(\d+)")
_MACRO_RX = re.compile(r"^\s*\[([A-Z_]+)\]\s+([A-Z]{2,4}_[A-Z0-9_]+)", re.M)


def fetch_summary(text: str) -> dict:
    out = {"gated": "[分道擷取] GATED" in (text or ""), "matrix": None}
    ms = _MATRIX_RX.findall(text or "")
    if ms:
        n, ok, todo, miss, unk = (int(x) for x in ms[-1])
        out["matrix"] = {"tables": n, "ready": ok, "todo": todo, "missing": miss, "unmeasured": unk}
    return out


def macro_summary(text: str) -> dict:
    counts, bad = {}, []
    for st, sid in _MACRO_RX.findall(text or ""):
        counts[st] = counts.get(st, 0) + 1
        if st not in ("MATCH", "OK", "SAME", "GREEN", "PASS"):
            bad.append("%s(%s)" % (sid, st))
    return {"pairs": sum(counts.values()), "counts": counts, "bad": bad}


def fold_results(rep: dict) -> None:
    run = rep.get("run")
    if not run:
        return
    rows, ids = [], {j["id"]: j for j in run["jobs"]}

    def log_of(jid):
        try:
            return Path(ids[jid]["log"]).read_text(encoding="utf-8", errors="replace")
        except (KeyError, OSError, TypeError):
            return ""
    if "fetch" in ids:
        fs = fetch_summary(log_of("fetch"))
        rep["fetch_result"] = fs
        if fs["gated"]:
            rows.append({"item": "結果 · 擷取", "lamp": "YELLOW", "detail": "被同意閘擋下(GATED):零出網、零寫入。兩道同意閘由操作員在自己的視窗設"})
        m = fs["matrix"]
        if m:
            done = m["todo"] == 0 and m["missing"] == 0 and m["unmeasured"] == 0 and m["tables"] > 0
            rows.append({"item": "結果 · 擷取矩陣", "lamp": "GREEN" if done else "YELLOW",
                         "detail": "表 %(tables)d · 到齊 %(ready)d · 待補 %(todo)d · 缺 %(missing)d · 未量 %(unmeasured)d" % m})
        elif not fs["gated"]:
            rows.append({"item": "結果 · 擷取矩陣", "lamp": "YELLOW", "detail": "日誌裡沒有擷取矩陣總表(沒跑到或被截斷)"})
        if not _CTX["refill"]:
            rows.append({"item": "結果 · 補擷取", "lamp": "YELLOW", "detail": "只列計畫、沒有寫(同意閘沒開,也沒給 --refill-apply)"})
    if "macro" in ids:
        ms = macro_summary(log_of("macro"))
        rep["macro_result"] = ms
        rows.append({"item": "結果 · 總經官方 × AKShare", "lamp": "GREEN" if ms["pairs"] and not ms["bad"] else "YELLOW",
                     "detail": ("%d 對 · " % ms["pairs"] + " ".join("%s %d" % kv for kv in sorted(ms["counts"].items()))
                                + ((" · 沒比到:" + "、".join(ms["bad"][:12])) if ms["bad"] else "")) if ms["pairs"] else "日誌裡沒有任何一對的判定"})
    rep["env"]["rows"] += rows
    if rep.get("lamp") == "GREEN" and any(r["lamp"] == "YELLOW" for r in rows):
        rep["lamp"] = "YELLOW"
    for r in rows:
        print(f"  {r['lamp']:<7}{r['item']:<22}{r['detail']}", flush=True)


def _save(rep: dict, out: Path, a: dict) -> None:
    fold_results(rep)
    _ORIG["_save"](rep, out, a)


def install() -> None:
    if _ORIG:
        return
    _ORIG.update(parse=B.parse, build_jobs=B.build_jobs, _save=B._save, TAG=B.TAG, VERSION=B.VERSION)
    B.parse, B.build_jobs, B._save, B.TAG, B.VERSION = parse, build_jobs, _save, TAG, VERSION


def uninstall() -> None:
    if not _ORIG:
        return
    B.parse, B.build_jobs, B._save, B.TAG, B.VERSION = (_ORIG[k] for k in ("parse", "build_jobs", "_save", "TAG", "VERSION"))
    _ORIG.clear()


def cmd_run(argv: list, check_only=False) -> int:
    install()
    try:
        return B.cmd_run(argv, check_only=check_only)
    finally:
        uninstall()


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:260]) if note and not cond else ""), flush=True)
    print(f"[計] {TAG} 自測開始(本版 + 前版 {PRIOR_PATH.name} 另起行程)", flush=True)
    fs = fetch_summary("x\n  [分道擷取] GATED · 雙閘沒開\n  [擷取矩陣] 表 58 · 到齊 0 · 待補 7 · 缺 44 · 未量 7 · 端點實測 7/32\n")
    ck("V1 擷取日誌:GATED 與擷取矩陣(到齊 / 待補 / 缺 / 未量)讀得出來",
       fs["gated"] and fs["matrix"] == {"tables": 58, "ready": 0, "todo": 7, "missing": 44, "unmeasured": 7}, fs)
    ms = macro_summary("  [NODATA] US_UNRATE 美國失業率 · 兩邊都沒資料\n  [MATCH] US_CPI_YOY 一致\n  [DIFF] CN_PMI 差 0.2\n")
    ck("V2 總經日誌:每一對的判定都算到 · 不是 MATCH 的逐對點名", ms["pairs"] == 3 and ms["bad"] == ["US_UNRATE(NODATA)", "CN_PMI(DIFF)"], ms)
    ck("V3 空日誌:不編總表(擷取矩陣 None · 總經 0 對)", fetch_summary("")["matrix"] is None and macro_summary("")["pairs"] == 0)
    ck("V4 同意閘只讀不設:兩道都開才算開", gates_open({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "1"})
       and not gates_open({"VIA_NET_CONSENT": "YES"}) and not gates_open({}))
    install()
    try:
        keep = {g: os.environ.pop(g, None) for g in GATES}
        try:
            a0, a1 = parse(["--dry"]), parse(["--dry", "--refill-apply"])
            t = B.tails()
            j0 = [j for j in build_jobs(t, a0, "py") if j["id"] == "fetch"]
            j1 = [j for j in build_jobs(t, a1, "py") if j["id"] == "fetch"]
            ck("V5 補擷取:閘沒開、沒給旗標 → 不帶 --refill-apply;操作員給旗標 → 帶上(交給 ActivateVDF)",
               j0 and j1 and "--refill-apply" not in j0[0]["cmd"] and j1[0]["cmd"][-1] == "--refill-apply" and not a0["refill_apply"], (j0[:1], j1[:1]))
        finally:
            for g, v in keep.items():
                if v is not None:
                    os.environ[g] = v
        rep = {"lamp": "GREEN", "env": {"rows": []}, "run": {"jobs": [{"id": "fetch", "log": "/nonexistent"}, {"id": "macro", "log": "/nonexistent"}]}}
        _CTX["refill"] = False
        fold_results(rep)
        ck("V6 併燈:日誌讀不到 / 沒有總表 / 沒補擷取 → 黃,總燈不會留在綠",
           rep["lamp"] == "YELLOW" and len(rep["env"]["rows"]) == 3 and all(r["lamp"] == "YELLOW" for r in rep["env"]["rows"]), rep["env"]["rows"])
    finally:
        uninstall()
    text = Path(__file__).read_text(encoding="utf-8")
    ck("V7 還原 + 檔面:前版三個名字是原件 · 加速器橋與網路橋標記 · 不寫同意閘 · 沒有本機路徑",
       not _ORIG and B.TAG.endswith("v0101") and "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text
       and "_CONSENT\"] " + "=" not in text and "\\" + "Users" not in text and "/" + "home/" not in text)
    pr = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ck("V8 前版 %s 自測照過(另起行程)" % PRIOR_PATH.name, pr.returncode == 0, (pr.stdout or "")[-260:])
    n = sum(ok)
    print(f"[計] {STEM} {VERSION} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if args[0] in ("--selftest", "selftest"):
        return selftest()
    if args[0] == "bridge-gate":
        return B.cmd_bridge_gate()
    if args[0] == "check":
        return cmd_run(args[1:] + ["--no-open"], check_only=True)
    if args[0] == "run":
        return cmd_run(args[1:])
    print(f"[{TAG}] 未知動詞 {args[0]}(run · check · bridge-gate · --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
