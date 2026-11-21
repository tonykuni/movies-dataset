#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN_MDL260_SafeParallelLaunch v0103 — 薄尾:跑的途中**不監控 CPU / DRAM**,開跑前先降壓等靜,之後固定 3 道(前版一字不動)
操作員 2026-11-20 桌機實跑(go → A 道)後:「為何跑這麼久 · 請改為不監控 cpu/dram · 一開始降壓力後統一分三步跑」。
桌機實錄:可用 DRAM 6.4 GB 起跑,子行程最多 9 支,DRAM 掉到 0.5–0.9 GB;監工判「過熱」→ 減到 1 道、暫停最新子行程,
但**暫停不釋放記憶體**,DRAM 一直在門檻下 → 01:07 起一直 1 道、反覆暫停 / 恢復,半小時沒有進度。
本版只做兩件事:
  ① 監工的壓力檢查(Supervisor._pressure)換成空的:跑的途中不量 CPU / DRAM、不減道、不加道、不暫停子行程。
     開跑前的「降壓 → 等靜」照舊(前版 calm_env / lower_priority 一字不動)。
  ② 道數固定 3:前版鏈上自己持有 MIN_SLOTS / MAX_SLOTS 的模組一律設成 3 / 3(auto 也只會得到 3)。
  ③ --via-db <via_database>(→ vrn_database)或 --output-dir <夾>:設本行程 VRN2_OUTPUT_DIR,VRN-2 整輪的輸出與增量 Parquet 庫寫到這裡。
其餘(就緒檢查 · 工作圖 · 結果併燈 · 頁面 · 指令列)全部轉給前版。
用法同前版:run … · check · --selftest
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

import importlib.util
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VRN_MDL260_SafeParallelLaunch"
VERSION = "v0103"
TAG = f"{STEM} {VERSION}"
FIXED_SLOTS = 3


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("vrn_launch_prior_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def chain_modules() -> list:
    """前版鏈上所有模組(沿 P / B / PRIOR 往下走;只看模組自己的全域,不經 __getattr__)。"""
    out, todo, seen = [], [PRIOR], set()
    while todo:
        m = todo.pop(0)
        if not isinstance(m, types.ModuleType) or id(m) in seen:
            continue
        seen.add(id(m))
        out.append(m)
        for k in ("P", "B", "PRIOR", "BASE"):
            v = vars(m).get(k)
            if isinstance(v, types.ModuleType):
                todo.append(v)
    return out


def _no_pressure(self):
    """跑的途中不量 CPU / DRAM、不增減道、不暫停(操作員 2026-11-20)。"""
    return None


_no_pressure._via_no_monitor = True
PATCHED = {"supervisors": [], "slots": []}
_ORIG_SLOTS: dict = {}


def install() -> dict:
    for m in chain_modules():
        sup = vars(m).get("Supervisor")
        if isinstance(sup, type) and "_pressure" in vars(sup) and not getattr(vars(sup)["_pressure"], "_via_no_monitor", False):
            sup._via_orig_pressure = vars(sup)["_pressure"]
            sup._pressure = _no_pressure
            if m.__name__ not in PATCHED["supervisors"]:
                PATCHED["supervisors"].append(m.__name__)
        if "MIN_SLOTS" in vars(m) or "MAX_SLOTS" in vars(m):
            _ORIG_SLOTS.setdefault(m.__name__, (vars(m).get("MIN_SLOTS"), vars(m).get("MAX_SLOTS")))
            m.MIN_SLOTS, m.MAX_SLOTS = FIXED_SLOTS, FIXED_SLOTS
            if m.__name__ not in PATCHED["slots"]:
                PATCHED["slots"].append(m.__name__)
    return PATCHED


def uninstall() -> None:
    for m in chain_modules():
        sup = vars(m).get("Supervisor")
        if isinstance(sup, type) and hasattr(sup, "_via_orig_pressure"):
            sup._pressure = sup._via_orig_pressure
            del sup._via_orig_pressure


install()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    args = abs_paths(args)
    note = output_dir_env(args)
    if note:
        print(note, flush=True)
    args = [a for i, a in enumerate(args) if not (a in ("--via-db", "--output-dir") or (i and args[i - 1] in ("--via-db", "--output-dir")))]
    return PRIOR.main(args)


DB_SUB = "vrn_database"


def output_dir_env(args: list, env=None) -> str:
    """--via-db <via_database>(→ <via_database>/vrn_database)或 --output-dir <夾> → 本行程 VRN2_OUTPUT_DIR(子行程繼承;
    VRN-2 整輪的增量 Parquet 庫就寫在這裡,不重抓已入庫的)。路徑的上一層要存在,否則拒用並點名(不建亂路徑)。"""
    env = __import__("os").environ if env is None else env
    val = None
    if "--output-dir" in args and args.index("--output-dir") + 1 < len(args):
        val = Path(args[args.index("--output-dir") + 1])
    elif "--via-db" in args and args.index("--via-db") + 1 < len(args):
        val = Path(args[args.index("--via-db") + 1]) / DB_SUB
    if val is None:
        return ""
    if not val.parent.is_dir():
        return f"[{TAG}] 輸出夾不用:上一層不存在 {val.parent}(照 VRN-2 自己的設定)"
    val.mkdir(exist_ok=True)
    env["VRN2_OUTPUT_DIR"] = str(val.resolve())
    return f"[{TAG}] VRN-2 輸出 / 增量庫 → {val.resolve()}"


PATH_FLAGS = ("--source", "--data-home", "--dir", "--root", "--params")


def abs_paths(args: list) -> list:
    """路徑旗標一律轉成絕對路徑再交前版(2026-11-20 容器實錄:相對 --source 檢查綠、子行程換工作目錄後找不到 → 紅)。"""
    out, i = [], 0
    while i < len(args):
        a = args[i]
        if a in PATH_FLAGS and i + 1 < len(args):
            out += [a, str(Path(args[i + 1]).expanduser().resolve())]
            i += 2
            continue
        k, eq, v = a.partition("=")
        out.append(f"{k}={Path(v).expanduser().resolve()}" if eq and k in PATH_FLAGS and v else a)
        i += 1
    return out


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} 薄尾自測(不監控 CPU / DRAM · 固定 3 道)===", flush=True)
    sups = [m for m in chain_modules() if isinstance(vars(m).get("Supervisor"), type)]
    ck("① 前版鏈上每一個監工類的壓力檢查都換成空的", sups and all(vars(m)["Supervisor"]._pressure is _no_pressure for m in sups), PATCHED)
    hot = {"n": 0}

    def hot_sampler():
        hot["n"] += 1
        return {"cpu_pct": 100.0, "mem_avail_gb": 0.1}

    class _Sup:
        slots, procs, hot, cool, samples, events = 3, {}, 5, 0, [], []
        sampler = staticmethod(hot_sampler)
    s = _Sup()
    for _ in range(5):
        _no_pressure(s)
    ck("② 就算 CPU 100% · DRAM 0.1 GB:不量(取樣 0 次)· 道數仍 3 · 沒有暫停事件", hot["n"] == 0 and s.slots == 3 and not s.events, (hot["n"], s.slots))
    mods = [m for m in chain_modules() if "MIN_SLOTS" in vars(m) or "MAX_SLOTS" in vars(m)]
    ck("③ 持有道數上下限的模組全是 3 / 3", mods and all((vars(m).get("MIN_SLOTS"), vars(m).get("MAX_SLOTS")) == (3, 3) for m in mods), [(m.__name__, vars(m).get("MIN_SLOTS"), vars(m).get("MAX_SLOTS")) for m in mods])
    ck("④ 開跑前降壓照舊(前版的降壓函式還在)", any(callable(vars(m).get(n)) for m in chain_modules() for n in ("calm_env", "lower_priority")))
    src = Path(__file__).read_text(encoding="utf-8")
    ck("⑤ 加速器橋真的匯入 · 不碰 TA-Lib · 不設同意閘 · 不含本機路徑", "import VIA_SuperAccel_Module as VIA_ACCEL" in src
       and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src)
       and ("C:" + "\\Users") not in src)
    uninstall()
    try:
        for m in mods:
            if m.__name__ in _ORIG_SLOTS:
                m.MIN_SLOTS, m.MAX_SLOTS = _ORIG_SLOTS[m.__name__]
        rc = PRIOR.main(["--selftest"])
    finally:
        install()
    ck("⑥ 前版 %s 自測照過(跑前還原監工與道數,跑完裝回)" % PRIOR_PATH.stem, rc == 0, "rc %s" % rc)
    ab = abs_paths(["run", "--source", "rel_dir", "--data-home=rel_home", "--slots", "auto"])
    ck("⑦ 相對路徑旗標轉絕對(--source x · --data-home=x);其他參數原樣", Path(ab[2]).is_absolute() and Path(ab[3].split("=", 1)[1]).is_absolute() and ab[-2:] == ["--slots", "auto"], ab)
    with __import__("tempfile").TemporaryDirectory() as td:
        e1, e2 = {}, {}
        (Path(td) / "via_database").mkdir()
        n1 = output_dir_env(["run", "--via-db", str(Path(td) / "via_database")], e1)
        n2 = output_dir_env(["run", "--output-dir", str(Path(td) / "沒有" / "out")], e2)
        try:
            import json as _js
            bk = max(HERE.glob("VRN_ParamControl_SSOT_v*.json"), key=_vnum)
            _b = _js.loads(bk.read_text(encoding="utf-8"))
            ew = [_b.get("run_params", {}).get("extract_workers")] + [g.get("params", {}).get("extract_workers") for g in _b.get("input_groups", []) if "extract_workers" in g.get("params", {})]
        except Exception as exc:  # noqa: BLE001
            bk, ew = None, [repr(exc)]
        ck("⑨ 參數冊尾版 extract_workers:run 與每個組覆寫都是 1(組值 auto 會蓋過 run 的 1,PR #701 Codex P2)", bk is not None and ew and all(x == 1 for x in ew), (bk and bk.name, ew))
        ck("⑧ --via-db → VRN2_OUTPUT_DIR = <via_database>/vrn_database(建夾);上一層不存在 → 不用、零建夾", e1.get("VRN2_OUTPUT_DIR") == str((Path(td) / "via_database" / "vrn_database").resolve())
           and (Path(td) / "via_database" / "vrn_database").is_dir() and not e2 and not (Path(td) / "沒有").exists(), (n1, n2))
    good = all(ok)
    print(f"[計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
