#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG232_TWIndexOfficial v0102 — 薄尾:分段擷取、逐段入庫(逾時不歸零)· 給 --start 也不重抓庫內已有的日子

R78(操作員 2026-10-14 在地測試):FG_20261012T113922Z 的 e232 rc 124 —— 族群冊 TW_INDEX 帶 --start 2022-07-01,
v0101 一給 --start 就關增量;v0100 的 run 把整段(1,118 個營業日 × 7 次外呼 + 每日 1.4 秒等待)全抓完才 upsert 一次,
30 分鐘被殺 = 零進度,下次又從 2022-07-01 重來。
v0102(本體 v0100 / v0101 不動;只換 run · main):
  ① 分段:整段切成 31 天一段(--chunk-days N 可改),每段交給前版 run(抓 → upsert 這一段);逾時只丟當段。
  ② 接續:給了 --start,但庫內兩指數(TAIEX · TPEX)都已抓到比它晚的日子 → 起點改用 next_start(庫內最新日 + 1),不重抓;
     庫空 / 少一個指數 / 庫內還沒到 --start = 照 --start(--start 仍是下界;往更早回補另案)。沒給 --start = v0101 增量。
  ③ 判決彙總:任一段 OK = OK(fetched / added / calls 加總;segments 列每段);全部 EMPTY = EMPTY;DENY / FAIL 當段即停、照回。
其餘(收容件只讀、網路只經 SUP_MDL740 curl_bytes、同意閘在工具裡、upsert 只增、status 動詞)全沿用 v0101 / v0100。

用法(經 VCGC;VIA_FROM_VCGC=YES):
  status                                                        唯讀(v0101)
  run [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--chunk-days N] [--dry]
  --selftest
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


import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHUNK_DAYS = 31


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})\.py$", Path(path).name)
    return int(m.group(1)) if m else -1


_ME = _vnum(__file__)
_PRIOR_PATH = max((p for p in HERE.glob("VDF_ENG232_TWIndexOfficial_v*.py") if 0 <= _vnum(p) < _ME), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"_vdf_eng232_prior_{_vnum(_PRIOR_PATH):04d}", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
ENGINE_TAG = "VDF_ENG232_TWIndexOfficial_v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def __getattr__(name):
    return getattr(PRIOR, name)


def chunks(start: str, end: str, days: int = CHUNK_DAYS) -> list:
    """[start, end] 切成連續、不重疊的 days 天段(含頭尾);start > end 回空。"""
    days = max(1, int(days))
    s, e, out = date.fromisoformat(start), date.fromisoformat(end), []
    while s <= e:
        ce = min(s + timedelta(days=days - 1), e)
        out.append((s.isoformat(), ce.isoformat()))
        s = ce + timedelta(days=1)
    return out


def resolve_start(start, db: Path | None = None) -> tuple:
    """回 (起點, resumed, 說明)。沒給 --start = v0101 增量;給了 --start 但庫內兩指數都已過它 = 從 next_start 接續(不重抓)。"""
    db = db or PRIOR.DB_IDX
    if not start:
        return PRIOR.next_start(db), False, "增量(v0101 next_start)"
    c = PRIOR.count(db)
    if all(k in c for k in PRIOR.NEED):
        nxt = PRIOR.next_start(db)
        if nxt > start:
            return nxt, True, f"庫內 {' · '.join(PRIOR.NEED)} 已到 {nxt} 前一日;--start {start} 不重抓,從 {nxt} 接續"
    return start, False, "照 --start"


def run(start: str | None = None, end: str | None = None, net=None, db: Path | None = None, dry: bool = False,
        chunk_days: int = CHUNK_DAYS) -> dict:
    db = db or PRIOR.DB_IDX
    end = end or date.today().isoformat()
    s0, resumed, why = resolve_start(start, db)
    res = {"state": "UP_TO_DATE", "start": s0, "end": end, "fetched": 0, "added": 0, "calls": 0,
           "incremental": not start, "resumed": resumed, "chunk_days": max(1, int(chunk_days)), "segments": [], "note": why}
    if s0 > end:
        res["note"] = "庫已到最新日;零外呼"
        return res
    net = net if net is not None else PRIOR.net_tool()
    states = []
    for cs, ce in chunks(s0, end, chunk_days):
        r = PRIOR.run(cs, ce, net=net, db=db, dry=dry)            # 前版 run:這一段 抓 → upsert
        seg = {"start": cs, "end": ce, "state": r.get("state"), "fetched": int(r.get("fetched") or 0),
               "added": int(r.get("added") or 0), "calls": int(r.get("calls") or 0)}
        res["segments"].append(seg)
        states.append(seg["state"])
        for k in ("fetched", "added", "calls"):
            res[k] += seg[k]
        if seg["state"] in ("DENY", "FAIL"):
            res["state"] = seg["state"]
            res["note"] = f"第 {len(states)} 段 {cs} → {ce} {seg['state']}:{r.get('note', '')}(前 {len(states) - 1} 段已入庫)"
            return res
    res["state"] = "OK" if "OK" in states else "EMPTY"
    if res["state"] == "EMPTY":
        res["note"] = "各段都沒有可用的官方指數列(非交易日或來源回空)"
    return res


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not PRIOR._allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb == "run":
        cd = PRIOR._arg(a, "--chunk-days")
        r = run(PRIOR._arg(a, "--start"), PRIOR._arg(a, "--end"), dry="--dry" in a, chunk_days=int(cd) if cd else CHUNK_DAYS)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return {"OK": 0, "UP_TO_DATE": 0, "DENY": 4, "EMPTY": 2}.get(r["state"], 1)
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(分段入庫 · 接續;零外呼)===")
    os.environ["VIA_ENG232_NOSLEEP"] = "1"
    segs = chunks("2026-01-01", "2026-03-15", 31)
    chk("① 分段:2026-01-01 → 03-15 切 31 天 = 3 段、連續不重疊、頭尾不變",
        segs == [("2026-01-01", "2026-01-31"), ("2026-02-01", "2026-03-03"), ("2026-03-04", "2026-03-15")] and chunks("2026-03-16", "2026-03-15") == [], segs)
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "idx.duckdb"
        chk("② 庫空:給 --start 照 --start(不被 BOOT 蓋掉);沒給 = BOOT", resolve_start("2022-07-01", db)[:2] == ("2022-07-01", False) and resolve_start(None, db)[0] == PRIOR.BOOT)
        PRIOR.PRIOR._LIB.UTILS.upsert_rows(db, PRIOR.TABLE, [{"date": "2026-09-30", "index_code": "TAIEX", "close": 1.0}], PRIOR.KEYS, counts=True)
        chk("③ 少一個指數:--start 照給(兩個都要補齊)", resolve_start("2022-07-01", db)[:2] == ("2022-07-01", False))
        PRIOR.PRIOR._LIB.UTILS.upsert_rows(db, PRIOR.TABLE, [{"date": "2026-09-25", "index_code": "TPEX", "close": 1.0}], PRIOR.KEYS, counts=True)
        r_res = resolve_start("2022-07-01", db)
        chk("④ 兩指數都已過 --start:從 next_start 接續(resumed)· --start 比庫內更晚則照 --start",
            r_res[:2] == ("2026-09-26", True) and resolve_start("2026-10-05", db)[:2] == ("2026-10-05", False), r_res[2])
        net = PRIOR.PRIOR._FakeNet()
        r = run("2022-07-01", "2026-09-20", net=net, db=db)
        chk("⑤ 接續後起點晚於迄日 = UP_TO_DATE、零外呼、零段", r["state"] == "UP_TO_DATE" and r["resumed"] and not net.urls and r["segments"] == [], r["state"])
        seen = []

        def fake_run(cs, ce, net=None, db=None, dry=False):
            seen.append((cs, ce))
            st = {1: "EMPTY", 2: "OK", 3: "OK"}.get(len(seen), "OK")
            return {"state": st, "start": cs, "end": ce, "fetched": 2 if st == "OK" else 0, "added": 1 if st == "OK" else 0, "calls": 7, "note": ""}
        keep = PRIOR.run
        PRIOR.run = fake_run
        try:
            db2 = Path(td) / "empty.duckdb"
            r2 = run("2026-01-01", "2026-03-15", net=net, db=db2, chunk_days=31)
            seen.clear()

            def fake_fail(cs, ce, net=None, db=None, dry=False):
                seen.append((cs, ce))
                return {"state": "OK" if len(seen) == 1 else "FAIL", "fetched": 1, "added": 1, "calls": 7, "note": "網路工具缺"} if len(seen) <= 2 else {"state": "OK"}
            PRIOR.run = fake_fail
            r3 = run("2026-01-01", "2026-03-15", net=net, db=db2, chunk_days=31)
            seen.clear()
            PRIOR.run = lambda cs, ce, net=None, db=None, dry=False: {"state": "EMPTY", "fetched": 0, "added": 0, "calls": 1}
            r4 = run("2026-01-01", "2026-01-10", net=net, db=db2, chunk_days=5)
        finally:
            PRIOR.run = keep
        chk("⑥ 三段逐段交前版 run:EMPTY · OK · OK → 總判 OK,fetched / added / calls 加總,segments 三列",
            r2["state"] == "OK" and len(r2["segments"]) == 3 and (r2["fetched"], r2["added"], r2["calls"]) == (4, 2, 21) and r2["incremental"] is False and not r2["resumed"],
            (r2["state"], r2["fetched"], r2["added"], r2["calls"]))
        chk("⑦ 第二段 FAIL 當段即停(第三段不跑)· note 記前 1 段已入庫;全 EMPTY = EMPTY",
            r3["state"] == "FAIL" and len(r3["segments"]) == 2 and "前 1 段已入庫" in r3["note"] and r4["state"] == "EMPTY" and len(r4["segments"]) == 2, (r3["state"], r3["note"][:40], r4["state"]))
        db3 = Path(td) / "real.duckdb"
        net3 = PRIOR.PRIOR._FakeNet()
        r5 = run("2026-10-01", "2026-10-02", net=net3, db=db3, chunk_days=1)
        c3 = PRIOR.count(db3)
        chk("⑧ 真鏈(替身網路):2 天切 2 段 → 前版 run 逐段 抓 + upsert,庫內有列(v0100 本體不動)",
            r5["state"] == "OK" and len(r5["segments"]) == 2 and bool(c3) and net3.urls, (r5["state"], len(net3.urls), list(c3)))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋 · 網路橋在;不代設同意閘;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "VIA_NET_CONSENT\"] =" not in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    prior = PRIOR.selftest()
    chk("⑩ 前版自測 PASS(v0101 → v0100)", prior == 0)
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
