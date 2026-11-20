#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG232_TWIndexOfficial v0105 — 薄尾:--start 是「起日下限」,不是「每次從這天整段重抓」。

VCGC 檢視參數樹(2026-11-19)的發現:族群冊把台股大類的起日以 `--start {start} --end {as_of}` 交給本引擎(TW_INDEX 的 asof_args),
而 v0102 起「給了 --start」就兩個指數都從那天抓到今天 → 經 VDF 啟動器每跑一次就把整段(三年多)重抓一次;
加權那一半每個月約 1~3 分鐘,整段重抓要一兩個小時,30 分鐘上限一到就被收掉。這是 VDF 一輪跑很久的原因之一。
本版(v0104 以前一字不動):
  ① 給了 --start:每個指數各自看庫 —— 庫內最早一天不晚於起日(容許 10 天,起日可能是假日)→ 只補最新日之後;
     庫內最早一天比起日晚 → 先補「起日 → 庫內最早一天前一天」那一段(往前補),再補最新日之後;庫裡沒有 → 從起日抓。
  ② 沒給 --start:照前版(各自從庫內最新日的隔天接著抓)。
  ③ 回報每個指數走了哪幾段。不留洞、按月寫庫、回空就停,照 v0103 / v0104。
不代設同意閘。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔自己不連網,連網的是回補本體。"""
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

import importlib.util
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG232_TWIndexOfficial"
ENGINE_TAG = Path(__file__).stem
HEAD_TOLERANCE_DAYS = 10
FAR = "9999-12-31"
NEED = ("TAIEX", "TPEX")


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_vdf_eng232_prior_for_" + ENGINE_TAG, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0104
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V2 = PRIOR.V2                                           # v0102(starts() 在這裡,run 以模組全域叫它)
BASE = PRIOR.BASE
_V4_RUN = PRIOR.run


def __getattr__(name):
    return getattr(PRIOR, name)


def segments(start: str, end: str, db=None) -> dict:
    """每個指數要抓的段:[(a, b), …];a > b 的段不列。"""
    c = BASE.count(db or BASE.DB_IDX)
    limit = (date.fromisoformat(start) + timedelta(days=HEAD_TOLERANCE_DAYS)).isoformat()
    out = {}
    for k in NEED:
        if k not in c:
            out[k] = [(start, end)]
            continue
        lo, hi = str(c[k][1])[:10], str(c[k][2])[:10]
        segs = []
        if lo > limit:
            segs.append((start, (date.fromisoformat(lo) - timedelta(days=1)).isoformat()))
        nxt = (date.fromisoformat(hi) + timedelta(days=1)).isoformat()
        if nxt <= end:
            segs.append((nxt, end))
        out[k] = [(a, b) for a, b in segs if a <= b]
    return out


def _run_one(idx: str, a: str, b: str, net, db, dry, inner, http, echo, sleep) -> dict:
    """只讓 idx 這個指數抓 [a, b];另一個指數這一段的起點設在最遠,前版自然略過。"""
    orig = V2.starts
    V2.starts = lambda _db=None: {k: (a if k == idx else FAR) for k in NEED}
    try:
        return _V4_RUN(None, b, net=net, db=db, dry=dry, inner=inner, http=http, echo=echo, sleep=sleep)
    finally:
        V2.starts = orig


def run(start=None, end=None, net=None, db=None, dry: bool = False, inner=None, http=None, echo=print, sleep=None) -> dict:
    if not start:
        return _V4_RUN(None, end, net=net, db=db, dry=dry, inner=inner, http=http, echo=echo, sleep=sleep)
    end_s = end or date.today().isoformat()
    plan = segments(start, end_s, db)
    res = {"state": "UP_TO_DATE", "start": start, "end": end_s, "fetched": 0, "added": 0, "calls": 0, "incremental": True,
           "floor": start, "segments": {k: [list(s) for s in v] for k, v in plan.items()}, "by_index": {k: {"state": "UP_TO_DATE", "added": 0} for k in NEED}}
    echo("  [TW 指數] 起日下限 %s · 加權 %s · 櫃買 %s" % (start, plan["TAIEX"] or "已到最新", plan["TPEX"] or "已到最新"), flush=True)
    for k in NEED:
        for a, b in plan[k]:
            r = _run_one(k, a, b, net, db, dry, inner, http, echo, sleep)
            for f in ("fetched", "added", "calls"):
                res[f] += int(r.get(f) or 0)
            bi = (r.get("by_index") or {}).get(k) or {}
            res["by_index"][k]["added"] += int(bi.get("added") or 0)
            res["by_index"][k]["state"] = bi.get("state") or r.get("state")
            st = r.get("state")
            if st not in ("OK", "EMPTY", "UP_TO_DATE"):
                res.update(state=st, stopped_at="%s %s" % (k, r.get("stopped_at") or a), note=r.get("note") or "")
                return res
            if st == "OK":
                res["state"] = "OK"
    if res["state"] == "UP_TO_DATE" and any(plan.values()):
        res["state"] = "EMPTY"
    return res


PRIOR.run = run          # v0104 的 main 以模組全域叫 run()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    quiet = lambda *x, **k: None  # noqa: E731
    print("=== %s 薄尾自測(--start 是下限;零網路;庫只在暫存夾)===" % ENGINE_TAG)
    try:
        import duckdb  # noqa: F401
        have = True
    except ImportError:
        have = False
    if not have:
        chk("① duckdb 在", False, "缺件:SKIP 不是綠")
    else:
        row = lambda d, code: {"date": d, "index_code": code, "index_name": "x", "open": 1.0, "low": 1.0, "high": 1.0, "close": 1.0, "volume": 1.0, "turnover": 1.0,  # noqa: E731
                               "inst_foreign_net": None, "inst_trust_net": None, "inst_dealer_net": None, "source": "s", "note": ""}
        with tempfile.TemporaryDirectory(prefix="eng232_v0105_") as td:
            db = Path(td) / "idx.duckdb"
            PRIOR.PRIOR.ensure_schema(db)
            V2._write(db, [row("2023-01-03", "TAIEX"), row("2026-11-17", "TAIEX"), row("2021-01-04", "TPEX"), row("2026-11-10", "TPEX")])
            seg = segments("2021-01-01", "2026-11-18", db)
            chk("① 分段:加權起點太晚 → 往前補 2021-01-01 → 2023-01-02 + 補 2026-11-18;櫃買已從起日開始 → 只補 2026-11-11 起",
                seg == {"TAIEX": [("2021-01-01", "2023-01-02"), ("2026-11-18", "2026-11-18")], "TPEX": [("2026-11-11", "2026-11-18")]}, seg)
            chk("② 空庫:兩個指數都從起日抓到迄日", segments("2021-01-01", "2026-11-18", Path(td) / "none.duckdb") == {"TAIEX": [("2021-01-01", "2026-11-18")], "TPEX": [("2021-01-01", "2026-11-18")]})
            V2._write(db, [row("2026-11-18", "TAIEX"), row("2026-11-18", "TPEX"), row("2021-01-04", "TAIEX")])
            chk("③ 已從起日開始又到最新 → 零段(不重抓)", segments("2021-01-01", "2026-11-18", db) == {"TAIEX": [], "TPEX": []})
            calls = []
            orig_v4 = globals()["_V4_RUN"]

            def fake_v4(start, end, **k):
                calls.append((dict(V2.starts()), end))
                return {"state": "OK", "fetched": 2, "added": 2, "calls": 1, "by_index": {kk: {"state": "OK", "added": 1} for kk in NEED}}

            globals()["_V4_RUN"] = fake_v4
            try:
                db2 = Path(td) / "idx2.duckdb"
                PRIOR.PRIOR.ensure_schema(db2)
                V2._write(db2, [row("2023-01-03", "TAIEX"), row("2026-11-17", "TAIEX"), row("2021-01-04", "TPEX"), row("2026-11-10", "TPEX")])
                r = run("2021-01-01", "2026-11-18", db=db2, echo=quiet)
                chk("④ 給 --start:加權兩段(往前補 + 最新之後)、櫃買一段;每段只放行一個指數",
                    [(c[0]["TAIEX"], c[0]["TPEX"], c[1]) for c in calls] == [("2021-01-01", FAR, "2023-01-02"), ("2026-11-18", FAR, "2026-11-18"), (FAR, "2026-11-11", "2026-11-18")] and r["state"] == "OK", calls)
                calls.clear()
                run(None, "2026-11-18", db=db2, echo=quiet)
                chk("⑤ 沒給 --start:照前版一次(不分段)", len(calls) == 1)
                calls.clear()

                def gap_v4(start, end, **k):
                    calls.append(end)
                    return {"state": "GAP", "stopped_at": "TAIEX 2021-03-01", "note": "回空", "fetched": 0, "added": 0, "calls": 1}

                globals()["_V4_RUN"] = gap_v4
                r2 = run("2021-01-01", "2026-11-18", db=db2, echo=quiet)
                chk("⑥ 某一段 GAP → 停,不往下一段(不留洞)", r2["state"] == "GAP" and len(calls) == 1 and "TAIEX" in r2["stopped_at"], r2.get("stopped_at"))
            finally:
                globals()["_V4_RUN"] = orig_v4
            chk("⑦ 跑完還原:v0102 的 starts 是原件", V2.starts.__name__ == "starts")
    chk("⑧ 裝進前版:v0104 的 main 叫到的就是本版的 run", PRIOR.run is run)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋真的匯入 · 網路工具橋在 · 不含本機路徑 · 不寫同意值", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "via_net_unified_v*.py" in src
        and ("C:" + "\\Users") not in src and ("_CONSENT\"] " + "=") not in src)
    PRIOR.run = _V4_RUN
    try:
        rc = PRIOR.selftest()
    finally:
        PRIOR.run = run
    chk("⑩ 前版鏈自測照過", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s 本版 %d/%d · %s" % (ENGINE_TAG, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
