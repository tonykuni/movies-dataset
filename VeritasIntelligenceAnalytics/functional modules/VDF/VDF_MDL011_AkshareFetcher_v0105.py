#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL011_AkshareFetcher v0105 — 薄尾:快照 TTL 可逐函式覆寫(選單 snapshot_ttl_hours_by_fn)· 平常增量不再天天重打統計局

操作員 2026-11-21 令:「三個都是獨立系統 授權給你做到 VDF 輸出資料且快」「VDF/VRN 一定要輸出且要做到增量維護不重工」。
容器實量(啟動器 MDL022 v0106 → 011d deep-macro,RUN_20261121_022400):817 條序列,其中 macro_china_nbs_nation 721 條
(國家統計局月 / 季 / 年資料,period 1990-);每條 1 次上游呼叫 · 中位 6.7 秒 · 最長 196.6 秒;前 419 條加總 67.5 分鐘、
新增 0 列(rows_new = 0)、TTL 跳過 0 = 平常增量也整批重打,是 VDF 一輪裡最慢的一道。
根因:統計局序列是 FULL_SNAPSHOT,只靠選單「全域」snapshot_ttl_hours = 24 判新鮮;上一輪隔天以上 → 全部重抓。
全域 TTL 拉長會連帶讓同選單的航運日指數變舊,所以不動全域,改成逐函式:
本版只改一件事:plan_series 讀選單的 snapshot_ttl_hours_by_fn(函式名 → 小時),該函式的快照新鮮判斷用它的小時數,
沒列的函式照全域 snapshot_ttl_hours。只在 incremental 生效(backfill / 全量照舊整批重抓;原件語意不變)。
選單本身(哪些函式 · 幾小時)放在 VDF_AkshareSelection_MacroShipping_v0101.json(參數冊),不寫死在本檔。
其他(動詞 · deep-macro · NBS 節流 / 切段 · 缺套件 NODATA · 文件爬取經網路工具)照 v0104。
不代裝套件、不讀寫同意閘、不碰 TA-Lib;零網路(自測用假 store)。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL011_AkshareFetcher"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_NET_OVERRIDE = None                              # 自測用假網路工具;正式執行 = None


def _vnum_v0105(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0105(p) < _vnum_v0105(__file__)), key=_vnum_v0105)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0105() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _core_v0105():
    """原件(v0100):定義 plan_series 與 Store 的那一支;缺套件時 v0103 的鏈斷在 None → 回 None(誠實 NODATA 照前版)。"""
    for m in _chain_v0105():
        if callable(vars(m).get("plan_series")) and isinstance(vars(m).get("Store"), type):
            return m
    return None


CORE = _core_v0105()
_PLAN_V0100 = CORE.plan_series if CORE is not None else None


def ttl_by_fn_v0105(selection: dict) -> dict:
    """選單 snapshot_ttl_hours_by_fn → {函式: 小時(float)};壞值略過(不猜)。"""
    out = {}
    for k, v in ((selection or {}).get("snapshot_ttl_hours_by_fn") or {}).items():
        try:
            h = float(v)
        except (TypeError, ValueError):
            continue
        if h >= 0:
            out[str(k)] = h
    return out


def plan_series_v0105(selection, registry, store):
    """同 v0100 plan_series;快照新鮮判斷的小時數先看 snapshot_ttl_hours_by_fn[函式],沒列照全域。"""
    by_fn = ttl_by_fn_v0105(selection)
    if not by_fn:
        return _PLAN_V0100(selection, registry, store)
    orig = store.fresh_within
    had = "fresh_within" in vars(store)
    keep = vars(store).get("fresh_within")
    store.fresh_within = lambda fn, ph, hours: orig(fn, ph, by_fn.get(fn, hours))
    try:
        return _PLAN_V0100(selection, registry, store)
    finally:
        if had:
            store.fresh_within = keep
        else:
            vars(store).pop("fresh_within", None)


if CORE is not None:
    CORE.plan_series = plan_series_v0105              # run / plan_summary 都以模組全域 plan_series 叫


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


class _FakeStoreV0105:
    """假 store:每個函式上次成功在 age_h 小時前;fresh_within 照原件判法(小時數 > 年齡 = 新鮮)。"""

    def __init__(self, age_h: dict):
        self.age_h, self.asked = age_h, []

    def fresh_within(self, fn, ph, hours):
        self.asked.append((fn, hours))
        return self.age_h.get(fn, 1e9) < hours

    def last_date_for(self, fn, ph):
        return None


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    import json
    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(快照 TTL 逐函式覆寫)===")
    chk("⓪ 前版 v0104(含 v0103 · v0102 鏈)自測過", rc0 == 0, f"rc {rc0}")
    if CORE is None:
        chk("① 原件載得到(缺套件 = 前版 NODATA 路,本版不接)", False, "CORE None")
        print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 FAIL")
        return 1
    chk("① 換裝:原件 plan_series = 本版", CORE.plan_series is plan_series_v0105)
    ent = {"has_ast": True, "strategy": "FULL_SNAPSHOT", "category": "macro", "date_params": {}, "date_fmt": None, "param_specs": [], "params": []}
    reg = {"registry": {"fn_nbs": dict(ent), "fn_ship": dict(ent)}}
    sel = {"mode": "incremental", "start_date": "2021-01-01", "snapshot_ttl_hours": 24, "fns": ["fn_nbs", "fn_ship"],
           "snapshot_ttl_hours_by_fn": {"fn_nbs": 168, "bad": "x"}}
    age = {"fn_nbs": 50, "fn_ship": 50}                 # 兩支都 50 小時前抓過
    st_old = _FakeStoreV0105(age)
    s_old, _ = _PLAN_V0100(sel, reg, st_old)
    st_new = _FakeStoreV0105(age)
    s_new, _ = CORE.plan_series(sel, reg, st_new)
    fresh_old = {s["fn"]: s["skip_fresh"] for s in s_old}
    fresh_new = {s["fn"]: s["skip_fresh"] for s in s_new}
    chk("② 重現:前版只用全域 24h → 50h 前抓過的統計局照樣重抓", fresh_old == {"fn_nbs": False, "fn_ship": False}, fresh_old)
    chk("③ 本版:fn_nbs 列 168h → 跳過(新鮮)· fn_ship 沒列 → 照全域 24h 重抓 · 壞值略過",
        fresh_new == {"fn_nbs": True, "fn_ship": False} and ("fn_nbs", 168.0) in st_new.asked and ("fn_ship", 24) in st_new.asked
        and ttl_by_fn_v0105(sel) == {"fn_nbs": 168.0}, (fresh_new, st_new.asked))
    st_bf = _FakeStoreV0105(age)
    s_bf, _ = CORE.plan_series(dict(sel, mode="backfill"), reg, st_bf)
    chk("④ backfill:不看 TTL(整批重抓,原件語意)· 呼叫完 store 的 fresh_within 還原",
        all(not s["skip_fresh"] for s in s_bf) and "fresh_within" not in vars(st_new) and "fresh_within" not in vars(st_bf))
    st_none = _FakeStoreV0105({"fn_nbs": 10, "fn_ship": 10})
    s_none, _ = CORE.plan_series({k: v for k, v in sel.items() if k != "snapshot_ttl_hours_by_fn"}, reg, st_none)
    chk("⑤ 選單沒帶 by_fn → 與前版同(10h 前抓過 → 全域 24h 內都跳過)", all(s["skip_fresh"] for s in s_none) and len(s_none) == 2)
    tail = max(HERE.glob("VDF_AkshareSelection_MacroShipping_v*.json"), key=_vnum_v0105, default=None)
    book = json.loads(tail.read_text(encoding="utf-8")) if tail else {}
    by = ttl_by_fn_v0105(book)
    chk("⑥ 參數冊尾版(%s)帶 by_fn:統計局 macro_china_nbs_nation 有列 · 列到的函式都在選單 fns 裡 · 全域 TTL 照舊"
        % (tail.name if tail else "—"), "macro_china_nbs_nation" in by and set(by) <= set(book.get("fns") or [])
        and book.get("snapshot_ttl_hours") == 24, by)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑦ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
