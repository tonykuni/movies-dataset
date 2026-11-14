#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL012_FetchGroups v0110 — 薄尾:擷取結果照 L16 判燈 · 自測的真頁檢查不受「剛跑過擷取」影響。

VDF 啟動實測(2026-11-14 · ActivateVDF run --mode fixture · 同意閘未開)兩件事:
  ① run 收尾把每支引擎 rc ≠ 0 都記「失敗」→ 擷取道 15/16 失敗 · rc 1 · 流程一 RED。實際是:同意閘未開照實拒抓(rc 2 / 4)、
     庫還沒建(rc 2)、缺第三方套件(rc 3,或 rc 1 + 日誌 No module named 第三方)——依 L16 是「等閘 / 沒資料 / 缺件」黃,不是壞。
     本版 run 跑完(本體一字不動)照報告逐支重判:真失敗(其他 rc · 自家模組缺)才紅;rc 照 L16:
     有真失敗 1 · 否則有等閘 4 · 否則有缺件 3 · 否則有沒資料 2 · 全成 0(中途停 5 照舊)。判讀寫回本輪 PARALLEL_latest(l16 欄)+ 印一行。
  ② v0108 自測 ④「真頁閒置只開 ① ②」讀真實輸出根的擷取日誌:日誌 120 秒內有更新就判「擷取中」多開 Live log →
     ActivateVDF 一輪裡擷取道剛跑完、引擎啟動檢查接著跑自測,必紅(單獨跑又綠)。本版自測跑前版鏈時,只把「真實輸出根」的
     Live log 看成閒置(夾具照原樣);正式頁的擷取中判斷一字不動。
其餘(族群 · 分道 · 守門 · 串流 · 頁 · 各動詞)全照前版鏈。VDF 自己的模組:不代設同意閘 · 零 TA-Lib · 不裝套件。
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

import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG_V0110 = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
OWN_PREFIX = ("VDF_", "VIA_", "CGC_", "VRN_", "SUP_")          # 自家 / 他系統模組缺 = 真壞,不算第三方缺件


def _vnum_v0110(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if 0 <= _vnum_v0110(p) < _vnum_v0110(__file__)), key=_vnum_v0110)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0110", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


V0107 = PRIOR.V0107                                              # run 動詞本體(cmd_run_v0107 · run_parallel 所在版)
V0100 = vars(V0107)["V0100"]
_RUN_BEFORE_V0110 = vars(V0107)["cmd_run_v0107"]
def _live_slots() -> list:
    """前版鏈上所有 live_log* 名稱(畫頁時查的是各模組自己的全域,副本也一起算)→ [(模組, 名稱)]。"""
    return [(m, n) for m in _chain() for n, f in list(vars(m).items()) if n.startswith("live_log") and callable(f)]


def missing_lib(text: str) -> str:
    """日誌裡的 No module named X:X 是第三方 → 回 X;自家 / 他系統模組或沒有 → 空字串。"""
    for m in re.finditer(r"No module named ['\"]([\w.]+)['\"]", text or ""):
        top = m.group(1).split(".")[0]
        if not top.startswith(OWN_PREFIX):
            return top
    return ""


def _tail_text(e: dict) -> str:
    txt = "\n".join(e.get("tail") or [])
    p = e.get("log")
    if p and Path(p).is_file():
        try:
            txt += "\n" + "\n".join(Path(p).read_text(encoding="utf-8", errors="replace").splitlines()[-200:])
        except OSError as exc:                                   # 日誌讀不到:照實附一行(只用 tail 判)
            txt += "\n[log 讀不到 %s]" % type(exc).__name__
    return txt


def classify(report: dict) -> dict:
    """逐支照 L16 重判:OK · NODATA(rc 2)· ABSENT(rc 3 / 缺第三方套件)· GATED(rc 4)· FAIL(其他)。"""
    rows = list(report.get("lists") or []) + [e for L in report.get("lanes") or [] for e in (L.get("engines") or [])]
    out = {"ok": [], "nodata": [], "absent": {}, "gated": [], "fail": []}
    for e in rows:
        rc, eid = e.get("rc"), e.get("id")
        if rc in (0, None):
            out["ok"].append(eid)
        elif rc == 2:
            out["nodata"].append(eid)
        elif rc == 4:
            out["gated"].append(eid)
        elif rc == 3:
            out["absent"][eid] = missing_lib(_tail_text(e)) or "缺件"
        else:
            lib = missing_lib(_tail_text(e)) if rc == 1 else ""
            if lib:
                out["absent"][eid] = lib
            else:
                out["fail"].append(eid)
    out["rc"] = 1 if out["fail"] else (4 if out["gated"] else (3 if out["absent"] else (2 if out["nodata"] else 0)))
    out["lamp"] = {0: "GREEN", 1: "RED", 2: "YELLOW", 3: "ABSENT", 4: "GATED"}[out["rc"]]
    return out


def _report_path(argv: list) -> Path | None:
    try:
        ap = argparse.ArgumentParser(add_help=False)
        ap.add_argument("--home")
        a, _ = ap.parse_known_args(argv)
        home = V0100._ctx(argparse.Namespace(home=a.home))[-1]
        return Path(home).parent / "_fetch_groups" / vars(V0107)["PARALLEL_LATEST"]
    except Exception:                                            # noqa: BLE001 — 找不到報告就照本體 rc(不冒充)
        return None


def cmd_run_v0110(argv: list) -> int:
    rp = _report_path(argv)
    before = rp.stat().st_mtime if rp and rp.is_file() else None
    rc = _RUN_BEFORE_V0110(argv)
    if rc in (0, 5) or not rp or not rp.is_file() or rp.stat().st_mtime == before:
        return rc                                                # 全成 · 中途停 · 沒有本輪報告 → 照本體
    rep = json.loads(rp.read_text(encoding="utf-8"))
    c = classify(rep)
    rep["l16"] = c
    rp.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    ab = " ".join(f"{k}({v})" for k, v in sorted(c["absent"].items()))
    print(f"[run · 並行 · L16 判讀] {c['lamp']} · 真失敗 {len(c['fail'])}{(' ' + str(c['fail'])) if c['fail'] else ''}"
          f" · 等同意閘 {len(c['gated'])} · 沒資料 / 庫缺 {len(c['nodata'])} · 缺件 {len(c['absent'])}{(' ' + ab) if ab else ''}"
          f" · 成 {len(c['ok'])} → rc {c['rc']}(本體記的「失敗」含等閘 / 缺件;照 L16 只算真失敗)", flush=True)
    return c["rc"]


V0107.cmd_run_v0107 = cmd_run_v0110                              # v0107 main 依模組全域名找 cmd_run_v0107 → 本版接手


def _idle_real_home(fn):
    """自測用:只把真實輸出根的 Live log 看成閒置(夾具照原樣)。"""
    try:
        real = Path(V0100._ctx(argparse.Namespace(home=None))[-1]).resolve()
    except Exception:                                            # noqa: BLE001 — 解不出真實輸出根 = 不改
        return fn

    def live(home, *a, **kw):
        d = fn(home, *a, **kw)
        if isinstance(home, (str, Path)) and Path(home).resolve() == real:
            d = dict(d, running=False)
        return d
    return live


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)
    print(f"=== {TAG_V0110} · 薄尾自測(L16 判燈 · 自測真頁不受剛跑過擷取影響)===", flush=True)
    chk("① 缺件判讀:第三方 polars → polars · 自家 VDF_ENG999 → 不算缺件(真壞)· 沒有 → 空",
        missing_lib("ModuleNotFoundError: No module named 'polars'") == "polars"
        and missing_lib("No module named 'VDF_ENG999_X'") == "" and missing_lib("all good") == "")
    with tempfile.TemporaryDirectory() as td:
        lg = Path(td) / "e011.log"
        lg.write_text("Traceback ...\nModuleNotFoundError: No module named 'polars'\n", encoding="utf-8")
        rep = {"lists": [{"id": "009", "rc": 0}],
               "lanes": [{"engines": [{"id": "e054", "rc": 2}, {"id": "e229", "rc": 4}, {"id": "e077", "rc": 3},
                                      {"id": "011d", "rc": 1, "log": str(lg), "tail": []}, {"id": "006", "rc": 0}]}]}
        c = classify(rep)
        chk("② 同意閘沒開那一輪:等閘 / 庫缺 / 缺件都不算失敗 → rc 4(等閘)· 真失敗 0",
            c["fail"] == [] and c["gated"] == ["e229"] and c["nodata"] == ["e054"] and c["absent"] == {"e077": "缺件", "011d": "polars"}
            and c["rc"] == 4 and c["lamp"] == "GATED", c)
        rep["lanes"][0]["engines"].append({"id": "e999", "rc": 1, "tail": ["Traceback", "KeyError: 'x'"]})
        c2 = classify(rep)
        chk("③ 有真失敗(rc 1 · 不是缺套件)→ rc 1 RED · 只點名真失敗那支", c2["fail"] == ["e999"] and c2["rc"] == 1 and c2["lamp"] == "RED", c2)
        home = Path(td) / "home" / "dict"
        home.mkdir(parents=True)
        work = home.parent / "_fetch_groups"
        work.mkdir()
        rp = work / vars(V0107)["PARALLEL_LATEST"]
        keep_run, keep_ctx = vars(V0107)["cmd_run_v0107"], V0100._ctx
        calls = []

        def fake_run(argv):
            calls.append(argv)
            rp.write_text(json.dumps({"lists": [], "lanes": [{"engines": [{"id": "e054", "rc": 2}, {"id": "006", "rc": 0}]}]}), encoding="utf-8")
            return 1
        keep_before = globals()["_RUN_BEFORE_V0110"]
        globals()["_RUN_BEFORE_V0110"] = fake_run
        V0100._ctx = lambda a: (None,) * 7 + (home,)
        try:
            rc = PRIOR.main(["run", "--groups", "ALL", "--home", str(home)])
        finally:
            globals()["_RUN_BEFORE_V0110"] = keep_before
            V0100._ctx = keep_ctx
        rep2 = json.loads(rp.read_text(encoding="utf-8"))
        chk("④ run 動詞經前版 main 分派到本版:本體 rc 1(只有庫缺)→ 照 L16 rc 2 · 報告寫回 l16 欄",
            keep_run is cmd_run_v0110 and calls and rc == 2 and rep2.get("l16", {}).get("nodata") == ["e054"], (rc, rep2.get("l16")))
    real_home = Path(V0100._ctx(argparse.Namespace(home=None))[-1])
    slots = _live_slots()
    chk("⑤ 前版鏈上的 live_log* 都找到(含 v0101 本體與 v0102 清理版)· 真實輸出根解得出",
        any(n == "live_log_v0102" for _, n in slots) and len(slots) >= 2 and str(real_home) != "", [(m.__name__, n) for m, n in slots][:6])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 不代設同意閘 · 不用 TA-Lib · 加速器 / 網路工具橋在",
        "environ[\"VIA_NET" + "_CONSENT\"] =" not in src and "import " + "talib" not in src and "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src)
    print(f"  前版鏈 {PRIOR_PATH.name} selftest ↓(真實輸出根的 Live log 看成閒置;夾具照原樣)", flush=True)
    keep = [(m, n, vars(m)[n]) for m, n in slots]
    for m, n, f in keep:
        setattr(m, n, _idle_real_home(f))
    try:
        prior_rc = PRIOR.selftest()
    finally:
        for m, n, f in keep:
            setattr(m, n, f)
    chk("⑦ 前版鏈 v0109 → … → v0100 自測照過 · 跑完 run 動詞仍是本版", prior_rc == 0 and vars(V0107)["cmd_run_v0107"] is cmd_run_v0110, prior_rc)
    good = all(ok)
    print(f"  [計] {TAG_V0110} 本版 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
