#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL134_ParallelLanes v0102 — 薄尾:清單先行 — lists 鏈(tw_list → etf_list)在所有資料鏈之前;--only 子集也自動帶上;清單步帶 VCGC 入口標記

操作員令(2026-10-13):「要先確令台股個股清單生成引擎自動更新以及主動式台股ETF清單自動更新生成引擎正常作業  輸出作為其他引擎的輸入  VDF 一鍵啟動」。
步冊 CGC_MDL125 v0112 起多了 tw_list(VDF_MDL009)· etf_list(VDF_MDL010);本版把它們配進鏈冊並讓其他步等它們:
  ① 鏈冊 CHAINS += tw_list:(lists, 等 datahome)· etf_list:(lists, 等 tw_list)(單寫者律:同鏈序跑;寫同一 vdf_master_lists.duckdb);
  ② assign():pip / node 安裝鏈以外的每一步(datahome 與清單步除外)after += etf_list → 資料鏈(tw · gl · etf · join · grid)全在清單之後起跑;
  ③ select():--only 子集沒列清單步也自動帶上(啟動器 Invoke-VIA-VdfFetch 的 $stepBook 不必改,-Steps 照舊只收它自己的步);
  ④ make_runner():清單步子行程帶 VIA_FROM_VCGC=YES(MDL009 / MDL010 入口律:VDF 總控或 VCGC;本編排是 VCGC 的),其餘步環境照舊(同意閘照前版「起跑即同意」)。
前版 plan / run / preflight / 哨兵 / 頁 / 冊 一字不動。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
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

import importlib.util
import os
import re
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL134_ParallelLanes"
TAG = "v0102"
LIST_CHAIN_V0102 = "lists"
LIST_STEPS_V0102 = ("tw_list", "etf_list")
INSTALL_CHAINS_V0102 = ("pip", "node")


def _vnum_v0102(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_ORIG_ASSIGN, _ORIG_SELECT, _ORIG_MAKE_RUNNER = PRIOR.assign, PRIOR.select, PRIOR.make_runner
PRIOR.CHAINS["tw_list"] = (LIST_CHAIN_V0102, ["datahome"])
PRIOR.CHAINS["etf_list"] = (LIST_CHAIN_V0102, ["tw_list"])
CHAINS = PRIOR.CHAINS


def __getattr__(name):
    return getattr(PRIOR, name)


def assign(steps: list) -> list:
    """前版配鏈(清單步已在鏈冊)+ 資料鏈每步 after += 最後一支在場的清單步(安裝鏈與 datahome 除外)。"""
    out = _ORIG_ASSIGN(steps)
    ids = {s["id"] for s in out}
    present = [x for x in LIST_STEPS_V0102 if x in ids]
    if not present:
        return out
    last = present[-1]
    for s in out:
        if s["id"] in LIST_STEPS_V0102 or s["id"] == "datahome" or s.get("chain") in INSTALL_CHAINS_V0102:
            continue
        if last not in s["after"]:
            s["after"] = list(s["after"]) + [last]
    return out


def select(steps: list, only: list | None) -> list:
    """--only 子集沒列清單步 → 自動帶上(清單先行律;啟動器步清單不必改)。"""
    if only:
        ids = {s["id"] for s in steps}
        extra = [x for x in LIST_STEPS_V0102 if x in ids and x not in only]
        if extra:
            only = extra + [x for x in only]
    return _ORIG_SELECT(steps, only)


def exec_with_entry(exec_fn=None):
    """清單步子行程帶 VIA_FROM_VCGC=YES(MDL009 / MDL010 入口律);其餘步原樣。"""
    base = exec_fn or PRIOR._exec

    def wrapped(s: dict, env: dict, lp):
        if s.get("id") in LIST_STEPS_V0102:
            env = dict(env)
            env["VIA_FROM_VCGC"] = "YES"
        return base(s, env, lp)
    return wrapped


def make_runner(logdir: Path, dry: bool, net_ok: bool, exec_fn=None):
    return _ORIG_MAKE_RUNNER(logdir, dry, net_ok, exec_with_entry(exec_fn))


PRIOR.assign, PRIOR.select, PRIOR.make_runner = assign, select, make_runner   # 前版 plan / run 走本版


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 十道並行安全編排(" + _STEM + " " + TAG + ")· 薄尾自測(清單先行)===")
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + str(note))
        if not cond:
            fails.append(name)

    chk("① 鏈冊有 lists 鏈:tw_list 等 datahome · etf_list 等 tw_list(前版 CHAINS 同一本,只增)",
        CHAINS.get("tw_list") == (LIST_CHAIN_V0102, ["datahome"]) and CHAINS.get("etf_list") == (LIST_CHAIN_V0102, ["tw_list"]) and PRIOR.CHAINS is CHAINS)
    fake = [{"id": i, "zh": i, "engine_ok": True, "net": False, "to": 5, "argv": ["x", "y"]}
            for i in ("datahome", "tw_list", "etf_list", "opencc", "hist_2023", "global", "etf_universe", "etf_revenue", "refail")]
    fa = assign(fake)
    by = {s["id"]: s for s in fa}
    chk("② assign:清單步入 lists 鏈;資料鏈每步 after 含 etf_list(hist_2023 · global · etf_universe · etf_revenue · refail);安裝鏈 opencc 與 datahome 不等",
        by["tw_list"]["chain"] == "lists" and by["etf_list"]["after"] == ["tw_list"]
        and all("etf_list" in by[x]["after"] for x in ("hist_2023", "global", "etf_universe", "etf_revenue", "refail"))
        and "etf_list" not in by["opencc"]["after"] and by["datahome"]["after"] == [], {k: v["after"] for k, v in by.items()})
    sel = select(fa, ["hist_2023", "global"])
    sid = [s["id"] for s in sel]
    chk("③ select --only 沒列清單步 → 自動帶上(tw_list · etf_list · datahome 之後的依賴邊保留)",
        set(sid) == {"tw_list", "etf_list", "hist_2023", "global"} and "etf_list" in by["hist_2023"]["after"]
        and all("etf_list" in s["after"] for s in sel if s["id"] in ("hist_2023", "global")), sid)
    log, lk = [], threading.Lock()

    def rec_runner(s):
        with lk:
            log.append(("start", s["id"], time.time()))
        time.sleep(0.03)
        with lk:
            log.append(("end", s["id"], time.time()))
        return {"id": s["id"], "state": "OK", "sec": 0.03}
    PRIOR.schedule(fa, rec_runner, workers=10, do_print=False)
    ends = {i: t for k, i, t in log if k == "end"}
    starts = {i: t for k, i, t in log if k == "start"}
    chk("④ 排程:清單兩步跑完,資料鏈才起跑(hist_2023 · global · etf_universe 起點 ≥ etf_list 終點;etf_list 起點 ≥ tw_list 終點)",
        all(starts[x] >= ends["etf_list"] for x in ("hist_2023", "global", "etf_universe")) and starts["etf_list"] >= ends["tw_list"]
        and starts["tw_list"] >= ends["datahome"], {k: round(v - min(starts.values()), 3) for k, v in starts.items()})
    seen = {}

    def fake_exec(s, env, lp):
        seen[s["id"]] = env.get("VIA_FROM_VCGC")
        return 0, "ok"
    w = exec_with_entry(fake_exec)
    w({"id": "tw_list"}, {"PATH": "x"}, None)
    w({"id": "hist_2023"}, {"PATH": "x"}, None)
    chk("⑤ 清單步子行程帶 VIA_FROM_VCGC=YES(入口律);其他步環境不動;前版 make_runner / assign / select 已換成本版",
        seen == {"tw_list": "YES", "hist_2023": None} and PRIOR.make_runner is make_runner and PRIOR.assign is assign and PRIOR.select is select)
    real = assign(PRIOR.steps_from_fixall())
    rid = [s["id"] for s in real]
    rby = {s["id"]: s for s in real}
    chk("⑥ 真步冊(CGC_MDL125 尾版):tw_list · etf_list 在 datahome 之後且入 lists 鏈;hist_2023 / global / etf_universe / consensus 都等 etf_list;全部入鏈冊",
        rid[:3] == ["datahome", "tw_list", "etf_list"] and rby["tw_list"]["chain"] == "lists"
        and all("etf_list" in rby[x]["after"] for x in ("hist_2023", "global", "etf_universe", "consensus") if x in rby) and all(s["mapped"] for s in real), rid[:6])
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘(只給入口標記)· 本檔不直派子行程",
        "[VIA:ACCEL-BRIDGE:" in body and "[VIA:NET-BRIDGE:" in body and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in body and 'env["VIA_NET_' + 'CONSENT"]' not in body and "import " + "subprocess" not in body)
    print("  ── 前版自測(VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑧ 前版 " + PRIOR_PATH.stem + " 自測 rc 0", prc == 0)
    print("  [計] " + _STEM + " " + TAG + " 薄尾 " + str(8 - len(fails)) + "/8 · " + ("PASS" if not fails else "FAIL"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
