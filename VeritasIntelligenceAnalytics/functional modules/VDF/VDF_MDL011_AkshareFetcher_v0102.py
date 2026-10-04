#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL011_AkshareFetcher v0102 — 薄尾:deep-macro 深度擷取(中國經濟 · 各國經濟 · 航運指數)· 參數列覆寫 __rows__

操作員 2026-10-04「Akshare 截取中國經濟數據 各國經濟數據 航運指數 資料要往下載一截取深入一點細節點的資料」。
  · deep-macro:讀選單正本 VDF_AkshareSelection_MacroShipping_v*.json(取尾版;與本檔同夾、進版控)→ 註冊表沒建就先離線 scan
    → 照選單 backfill(全歷史)經 v0100 的 run_selection 寫僅增 parquet 分片 + DuckDB 目錄;--plan 只列計畫(零網路)。
  · 「深」= 每支函式的全歷史 + 參數展開:國家統計局 NBS 十類目錄樹(全國 / 分省 月季年 · 主要城市 · 港澳台)逐葉節點、
    Drewry WCI 八條航線、70 城新房價指數(兩城一呼叫)…;選單裡由 overrides 指定。
  · 參數列覆寫:overrides[fn] = {"__rows__": [{...}, …]} = 明列每組參數(NBS 的 path 跟 kind 綁在一起,不能做笛卡兒積);
    其他寫法照 v0100(清單 = 笛卡兒積、純量 = 固定值)。
  · 國家統計局 NBS(容器實測):長區間一次查(如 1990- 月度)30 秒逾時回非 JSON、連發會被限流 →
    NBS 呼叫全域節流(兩呼叫間隔 ≥ NBS_MIN_INTERVAL 秒)· 長區間失敗時切 5 年一段逐段查、按指標列對齊拼回(新→舊、欄不重複)。
  · --group china_macro,global_macro,shipping 只跑指定組(容器先跑非 NBS 的各國 / 航運,NBS 慢慢補)。
  · 結果誠實:失敗逐支列出;失敗比例 ≤ 選單的 fail_tolerance 才 rc 0(上游介面改版是常態,照列不藏),超過 rc 1;一支都沒成 rc 2。
其餘(scan · fetch · schedule-run · views · params(v0101 無註冊表 NODATA)· compact · universe)全照前版。不碰 TA-Lib;不讀寫同意閘。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL011_AkshareFetcher"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
SEL_GLOB = "VDF_AkshareSelection_MacroShipping_v*.json"


def _vnum_v0102(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
CORE = PRIOR.PRIOR                                     # v0100 原件(C = K = A = R = S = F = 同一模組)
_EXPAND_V0100 = CORE.expand_params


def __getattr__(name):
    return getattr(PRIOR, name)


def expand_params_v0102(reg_entry, max_combos=None, overrides=None):
    """overrides 有 __rows__ → 明列參數組(純量鍵當固定值併入每組);否則照 v0100。"""
    if isinstance(overrides, dict) and isinstance(overrides.get("__rows__"), list):
        max_combos = max_combos or CORE.MAX_ENUM_COMBOS
        base = dict(reg_entry.get("base_kwargs", {}))
        base.update({k: v for k, v in overrides.items() if k != "__rows__" and not isinstance(v, list) and v is not None})
        return [dict(base, **row) for row in overrides["__rows__"] if isinstance(row, dict)][:max_combos]
    return _EXPAND_V0100(reg_entry, max_combos, overrides)


CORE.expand_params = expand_params_v0102               # plan_series 以 R.expand_params 叫(R = 原件模組)

import threading as _th
import time as _time
NBS_MIN_INTERVAL = 2.0
NBS_CHUNK_YEARS = 5
_NBS_LOCK = _th.Lock()
_NBS_LAST = [0.0]
NBS_STATS = {"calls": 0, "chunked": 0, "chunks": 0}
_CALL_V0100 = CORE._call


def _nbs_throttled(f, kwargs):
    with _NBS_LOCK:
        wait = NBS_MIN_INTERVAL - (_time.monotonic() - _NBS_LAST[0])
        if wait > 0:
            _time.sleep(wait)
        _NBS_LAST[0] = _time.monotonic()
    NBS_STATS["calls"] += 1
    return f(**kwargs)


def period_chunks_v0102(period: str, this_year: int, step: int = NBS_CHUNK_YEARS) -> list:
    """'1990-' / '1990-2025' → ['2021-2025', '2016-2020', …, '1990-1995'](新→舊,每段 ≤ step 年);不是年區間 = []。"""
    m = re.match(r"^\s*(\d{4})\s*-\s*(\d{4})?\s*$", str(period or ""))
    if not m:
        return []
    a, b = int(m.group(1)), int(m.group(2) or this_year)
    out, hi = [], b
    while hi >= a:
        lo = max(a, hi - step + 1)
        out.append(f"{lo}-{hi}")
        hi = lo - 1
    return out if len(out) > 1 else []


def nbs_call_v0102(f, kwargs):
    """NBS:節流;整段失敗且是長年區間 → 切段逐查、按指標列對齊拼回;一段都沒有 = 照拋原例外。"""
    try:
        return _nbs_throttled(f, kwargs)
    except Exception as first:
        import datetime as _dt
        chunks = period_chunks_v0102(kwargs.get("period"), _dt.date.today().year)
        if not chunks:
            raise
        import pandas as pd
        parts = []
        for per in chunks:
            for attempt in range(2):
                try:
                    df = _nbs_throttled(f, dict(kwargs, period=per))
                    if df is not None and len(df):
                        parts.append(df)
                    break
                except Exception:
                    if attempt:
                        break
        NBS_STATS["chunked"] += 1
        NBS_STATS["chunks"] += len(chunks)
        if not parts:
            raise first
        out = pd.concat(parts, axis=1)
        return out.loc[:, ~out.columns.duplicated()]


def _call_v0102(fn, kwargs, retries=3):
    if str(fn).startswith("macro_china_nbs"):
        return nbs_call_v0102(getattr(CORE._akshare(), fn), kwargs)
    return _CALL_V0100(fn, kwargs, retries)


CORE._call = _call_v0102


def selection_path_v0102(arg: str | None = None) -> Path | None:
    if arg:
        return Path(arg)
    hits = sorted(HERE.glob(SEL_GLOB), key=_vnum_v0102)
    return hits[-1] if hits else None


def apply_tier_v0102(sel: dict, tier: str) -> dict | None:
    """core = 選單本體;其他 tier = 本體 + tiers[tier].extra_fns + extra_rows(併進 overrides[fn].__rows__)。"""
    tiers = sel.pop("tiers", None) or {}
    if tier in ("", "core"):
        return sel
    t = tiers.get(tier)
    if not isinstance(t, dict):
        return None
    sel["fns"] = list(sel.get("fns") or []) + [f for f in t.get("extra_fns") or [] if f not in (sel.get("fns") or [])]
    ov = sel.setdefault("overrides", {})
    for fn, rows in (t.get("extra_rows") or {}).items():
        cur = dict(ov.get(fn) or {})
        cur["__rows__"] = list(cur.get("__rows__") or []) + list(rows)
        ov[fn] = cur
    return sel


def ensure_registry_v0102() -> dict:
    reg = CORE.load_registry()
    if not reg.get("generated_at"):
        print(f"[{TAG}] 註冊表還沒建 → 離線 scan(AST 盤點已裝 akshare;零網路)", flush=True)
        CORE.cmd_scan(argparse.Namespace(refresh_docs=False, offline=True))
        reg = CORE.load_registry()
    return reg


def plan_summary_v0102(sel: dict, reg: dict) -> dict:
    series, skipped = CORE.plan_series(sel, reg, CORE.Store())
    group_of = {fn: g for g, fns in (sel.get("groups") or {}).items() for fn in fns}
    by = {}
    for s in series:
        g = group_of.get(s["fn"], "other")
        b = by.setdefault(g, {"fns": set(), "series": 0, "windows": 0})
        b["fns"].add(s["fn"])
        b["series"] += 1
        b["windows"] += len(s["windows"])
    out = {g: {"fns": len(v["fns"]), "series": v["series"], "windows": v["windows"]} for g, v in sorted(by.items())}
    return {"groups": out, "series": len(series), "skipped": skipped}


def cmd_deep_macro_v0102(argv: list) -> int:
    ap = argparse.ArgumentParser(prog="deep-macro")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--selection")
    ap.add_argument("--workers", type=int)
    ap.add_argument("--tier", default="core")
    ap.add_argument("--group", default="")
    a = ap.parse_args(argv)
    sp = selection_path_v0102(a.selection)
    if sp is None or not sp.is_file():
        print(f"[{TAG}] ABSENT:選單正本 {SEL_GLOB} 不在 {HERE}", flush=True)
        return 3
    sel = json.loads(sp.read_text(encoding="utf-8"))
    sel = apply_tier_v0102({k: v for k, v in sel.items() if not k.startswith("_")}, a.tier)
    if sel is None:
        print(f"[{TAG}] 選單沒有 tier「{a.tier}」(只有 core 與 {sorted((json.loads(sp.read_text(encoding='utf-8')).get('tiers') or {}))})", flush=True)
        return 2
    if a.workers:
        sel["workers"] = a.workers
    if a.group:
        want = {g.strip() for g in a.group.split(",") if g.strip()}
        keep = {fn for g, fns in (sel.get("groups") or {}).items() if g in want for fn in fns}
        sel["fns"] = [fn for fn in sel.get("fns") or [] if fn in keep]
        print(f"[{TAG}] 只跑組 {sorted(want)} · 函式 {len(sel['fns'])}", flush=True)
    CORE.ensure_dirs()
    reg = ensure_registry_v0102()
    plan = plan_summary_v0102(sel, reg)
    for g, v in plan["groups"].items():
        print(f"[{TAG}] 計畫 {g:14} 函式 {v['fns']:4} · 序列 {v['series']:5} · 視窗 {v['windows']}", flush=True)
    for s in plan["skipped"][:30]:
        print(f"[{TAG}] 略過 {s['fn']} · {s['reason']}", flush=True)
    print(f"[{TAG}] 選單 {sp.name} · tier {a.tier} · 模式 {sel.get('mode')} · 起 {sel.get('start_date')} · 序列 {plan['series']} · 略過 {len(plan['skipped'])}", flush=True)
    if a.plan:
        return 0 if plan["series"] else 2
    state, report = CORE.run_selection(sel)
    fails = [t for t in state.get("tasks", []) if t.get("status") in ("FAIL", "ERROR")]
    for t in fails[:60]:
        print(f"[{TAG}] 失敗 {t['fn']} {json.dumps(t.get('params') or {}, ensure_ascii=False)[:80]} · {str(t.get('err') or '')[:120]}", flush=True)
    total = max(1, state["ok"] + state["fail"] + state["empty"])
    tol = float(sel.get("fail_tolerance") or 0.0)
    print(json.dumps({"run_id": state["run_id"], "ok": state["ok"], "fail": state["fail"], "empty": state["empty"],
                      "rows_new": state["rows_new"], "fail_ratio": round(state["fail"] / total, 4), "tolerance": tol, "report": str(report)},
                     ensure_ascii=False), flush=True)
    if state["ok"] == 0:
        return 2
    return 0 if state["fail"] / total <= tol else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args[:1] == ["deep-macro"]:
        return cmd_deep_macro_v0102(args[1:])
    return PRIOR.main(args)


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    rc0 = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(deep-macro · __rows__)===")
    chk("① v0101 自測過(params 無註冊表 NODATA)", rc0 == 0, f"rc {rc0}")
    e = {"base_kwargs": {"period": "LAST10"}}
    rows = CORE.expand_params(e, 10, {"__rows__": [{"kind": "月度数据", "path": "价格指数 > A"}, {"kind": "年度数据", "path": "人口 > B"}], "period": "1990-"})
    cart = CORE.expand_params({"base_kwargs": {}}, 10, {"symbol": ["a", "b"], "x": [1, 2]})
    chk("② __rows__ 明列參數組(kind 與 path 綁定,不做笛卡兒積;純量併入每組);清單寫法照 v0100 笛卡兒積",
        rows == [{"period": "1990-", "kind": "月度数据", "path": "价格指数 > A"}, {"period": "1990-", "kind": "年度数据", "path": "人口 > B"}]
        and len(cart) == 4, rows)
    sp = selection_path_v0102()
    sel = json.loads(sp.read_text(encoding="utf-8")) if sp else {}
    g = sel.get("groups") or {}
    chk("③ 選單正本在(同夾版號尾版):中國經濟 · 各國經濟 · 航運三組都有;NBS 走 __rows__;Drewry 八航線;全歷史(start ≤ 1990;FULL_SNAPSHOT 一呼叫回全歷史,incremental 可續跑)",
        sp is not None and all(g.get(k) for k in ("china_macro", "global_macro", "shipping"))
        and (sel.get("overrides", {}).get("macro_china_nbs_nation") or {}).get("__rows__")
        and len((sel.get("overrides", {}).get("drewry_wci_index") or {}).get("symbol") or []) == 8 and sel.get("mode") in ("backfill", "incremental")
        and sel.get("start_date", "9999") <= "1990-01-01",
        sp.name if sp else None)
    with tempfile.TemporaryDirectory() as td:
        buf = io.StringIO()
        reg = {"generated_at": "t", "stats": {}, "tree": {}, "registry": {
            "macro_china_cpi": {"has_ast": True, "category": "macro", "strategy": "FULL_SNAPSHOT", "date_params": {}, "date_fmt": "%Y%m%d", "param_specs": []},
            "macro_china_nbs_nation": {"has_ast": True, "category": "macro", "strategy": "FULL_SNAPSHOT", "date_params": {}, "date_fmt": "%Y%m%d",
                                       "param_specs": [{"name": "kind", "kind": "FREE", "required": True}, {"name": "path", "kind": "FREE", "required": True}]}}}

        class _St:
            def last_date_for(self, *a):
                return None

            def fresh_within(self, *a):
                return False
        keep_store = CORE.Store
        try:
            CORE.Store = _St
            with contextlib.redirect_stdout(buf):
                p = plan_summary_v0102({"fns": ["macro_china_cpi", "macro_china_nbs_nation", "no_such_fn"], "mode": "backfill",
                                        "groups": {"china_macro": ["macro_china_cpi", "macro_china_nbs_nation"]},
                                        "overrides": {"macro_china_nbs_nation": {"__rows__": [{"kind": "月度数据", "path": "a"}, {"kind": "年度数据", "path": "b"}]}}},
                                       reg)
        finally:
            CORE.Store = keep_store
        full = apply_tier_v0102(json.loads(json.dumps(sel)), "full") if sel else None
        core = apply_tier_v0102(json.loads(json.dumps(sel)), "core") if sel else None
        nat = lambda x: len(((x or {}).get("overrides", {}).get("macro_china_nbs_nation") or {}).get("__rows__") or [])
        chk("⑥ tier:core = 選單本體(NBS 全國月 / 季);full = + 全國年度 + 分省 × 31 省(extra_rows 併進 __rows__);沒有的 tier = None",
            full and core and nat(full) > nat(core) > 0 and "macro_china_nbs_region" in full["fns"] and "macro_china_nbs_region" not in core["fns"]
            and apply_tier_v0102(json.loads(json.dumps(sel)), "nope") is None, (nat(core), nat(full)))
        chk("④ 計畫(零網路):cpi 1 序列 + NBS 2 組 = 3 序列;冊外函式照實略過",
            p["series"] == 3 and p["groups"]["china_macro"]["series"] == 3 and [s["fn"] for s in p["skipped"]] == ["no_such_fn"], p)
    import pandas as pd
    calls = []

    def fake(kind=None, path=None, period=None):
        calls.append(period)
        a, b = [int(x) for x in period.split("-")] if period.count("-") == 1 and period.split("-")[1] else (int(period[:4]), 2026)
        if b - a + 1 > 5:
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return pd.DataFrame({f"{y}年": [float(y), float(y) + 0.5] for y in range(b, a - 1, -1)}, index=["指標A", "指標B"])
    keep_iv = globals()["NBS_MIN_INTERVAL"]
    globals()["NBS_MIN_INTERVAL"] = 0.0
    try:
        out = nbs_call_v0102(fake, {"kind": "年度数据", "path": "x", "period": "2012-2026"})
        short = nbs_call_v0102(fake, {"kind": "年度数据", "path": "x", "period": "2022-2026"})
    finally:
        globals()["NBS_MIN_INTERVAL"] = keep_iv
    chk("⑦ NBS 長區間失敗 → 切 5 年段逐查、按指標列對齊拼回(新→舊 15 欄不重複);短區間一次過不切段",
        period_chunks_v0102("2012-2026", 2026) == ["2022-2026", "2017-2021", "2012-2016"] and list(out.columns)[:2] == ["2026年", "2025年"]
        and out.shape == (2, 15) and out.loc["指標B", "2012年"] == 2012.5 and short.shape == (2, 5) and calls[0] == "2012-2026",
        (out.shape, calls[:5]))
    chk("⑧ NBS 呼叫走 v0102 節流 / 切段(原件 _call 由本版接手;其他函式照原件重試)", CORE._call is _call_v0102)
    text = Path(__file__).read_text(encoding="utf-8")
    names = {n.name for n in __import__("ast").parse(text).body if isinstance(n, __import__("ast").FunctionDef)}
    chk("⑤ L103:模組層加速器橋 + 網路工具橋(def _via_net);不碰 TA-Lib;不寫同意閘", "_via_net" in names and "VIA_ACCEL" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    n = sum(ok)
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · v0101 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if n == len(ok) else 'FAIL'}")
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
