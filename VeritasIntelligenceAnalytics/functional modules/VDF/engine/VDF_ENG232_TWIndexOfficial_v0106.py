#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG232_TWIndexOfficial v0106 — 薄尾:修 v0105 兩個問題(PR 688 審查 P1 · P2)。

  ① P1:v0105 只把 run 裝到 v0104,而 `run` 動詞由 v0103 的 main 處理、叫的是 v0103 自己的全域 run(= v0104 的)
     → 經命令列(擷取系統就是這樣叫)v0105 的分段從沒執行,櫃買照樣 2021 → 今天 71 個月整段重抓(2026-11-19 實錄)。
     本版 main 自己處理 `run` 動詞(閘照 v0103:只經 VCGC/VDF 入口)叫本版的 run;其他動詞照前版。
  ② P2:v0105 只看庫內最早 / 最新一天;頭段補到一半停(例:2021-01 成了、2021-02 回空)之後,最早一天已經 ≈ 起日,
     中間的洞就再也不排、還回 UP_TO_DATE(2026-11-19 實錄:加權 2021-01 有、2021-02 ~ 2023-02 空)。
     本版看實際有的日子:起日 → 第一天(晚於起日 10 天以上)· 相鄰兩天差超過 16 天(2023 春節休市差 13 天)· 最後一天 → 迄日,
     每個洞都是一段;每段照前版按月寫庫、回空就停,下次從同一個洞接著抓。
  ③ 一個指數停了不擋另一個指數;總狀態取最差,stopped_at 記第一個停的地方。
沒給 --start:照前版(各自從最新日隔天接著抓)。不代設同意閘。
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
GAP_DAYS = 16                      # 2023 春節休市 01-17 → 01-30 差 13 天;整月缺 ≥ 28 天
FAR = "9999-12-31"
NEED = ("TAIEX", "TPEX")
_RC = {"OK": 0, "UP_TO_DATE": 0, "DENY": 4, "EMPTY": 2, "GAP": 2}
_RANK = {"OK": 0, "UP_TO_DATE": 0, "EMPTY": 1, "GAP": 2}


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_vdf_eng232_prior_for_" + ENGINE_TAG, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0105(_run_one 只放行一個指數)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V2 = PRIOR.V2
BASE = PRIOR.BASE


def __getattr__(name):
    return getattr(PRIOR, name)


def _d(s: str) -> date:
    return date.fromisoformat(str(s)[:10])


def dates_in(db, start: str, end: str) -> dict:
    """每個指數在 [start, end] 內實際有的日子(唯讀;庫或表不在 = {})。"""
    p = Path(db or BASE.DB_IDX)
    if not p.is_file():
        return {}
    import duckdb
    con = duckdb.connect(str(p), read_only=True)
    try:
        rows = con.execute("SELECT index_code, CAST(date AS VARCHAR) FROM tw_index_daily WHERE CAST(date AS VARCHAR) >= ? "
                           "AND CAST(date AS VARCHAR) <= ? ORDER BY 1, 2", [start, end + "~"]).fetchall()
    except Exception:
        return {}
    finally:
        con.close()
    out = {}
    for k, d in rows:
        out.setdefault(k, []).append(str(d)[:10])
    return out


def segments(start: str, end: str, db=None) -> dict:
    """每個指數要抓的洞:[(a, b), …],依日期排;起日前的缺口容許 10 天,中間兩天差超過 16 天才算洞。"""
    have = dates_in(db, start, end)
    out = {}
    for k in NEED:
        ds = have.get(k) or []
        if not ds:
            out[k] = [(start, end)]
            continue
        segs = []
        if _d(ds[0]) > _d(start) + timedelta(days=HEAD_TOLERANCE_DAYS):
            segs.append((start, (_d(ds[0]) - timedelta(days=1)).isoformat()))
        for x, y in zip(ds, ds[1:]):
            if (_d(y) - _d(x)).days > GAP_DAYS:
                segs.append(((_d(x) + timedelta(days=1)).isoformat(), (_d(y) - timedelta(days=1)).isoformat()))
        nxt = (_d(ds[-1]) + timedelta(days=1)).isoformat()
        if nxt <= end:
            segs.append((nxt, end))
        out[k] = [(a, b) for a, b in segs if a <= b]
    return out


def run(start=None, end=None, net=None, db=None, dry: bool = False, inner=None, http=None, echo=print, sleep=None) -> dict:
    if not start:
        return PRIOR._V4_RUN(None, end, net=net, db=db, dry=dry, inner=inner, http=http, echo=echo, sleep=sleep)
    end_s = end or date.today().isoformat()
    plan = segments(start, end_s, db)
    res = {"state": "UP_TO_DATE", "start": start, "end": end_s, "fetched": 0, "added": 0, "calls": 0, "incremental": True,
           "floor": start, "engine": ENGINE_TAG, "segments": {k: [list(s) for s in v] for k, v in plan.items()},
           "by_index": {k: {"state": "UP_TO_DATE", "added": 0} for k in NEED}}
    echo("  [TW 指數 %s] 起日下限 %s · 加權 %d 洞 %s · 櫃買 %d 洞 %s" % (ENGINE_TAG.rsplit("_", 1)[-1], start, len(plan["TAIEX"]), plan["TAIEX"][:3] or "已齊",
                                                              len(plan["TPEX"]), plan["TPEX"][:3] or "已齊"), flush=True)
    worst = "UP_TO_DATE"
    for k in NEED:
        for a, b in plan[k]:
            r = PRIOR._run_one(k, a, b, net, db, dry, inner, http, echo, sleep)
            for f in ("fetched", "added", "calls"):
                res[f] += int(r.get(f) or 0)
            bi = (r.get("by_index") or {}).get(k) or {}
            res["by_index"][k]["added"] += int(bi.get("added") or 0)
            st = r.get("state") or "GAP"
            res["by_index"][k]["state"] = bi.get("state") or st
            if st not in ("OK", "EMPTY", "UP_TO_DATE"):
                res["by_index"][k]["stopped_at"] = r.get("stopped_at") or a
                if "stopped_at" not in res:
                    res.update(stopped_at="%s %s" % (k, r.get("stopped_at") or a), note=r.get("note") or "")
                worst = st if _RANK.get(st, 3) >= _RANK.get(worst, 0) else worst
                break                                    # 這個指數停在這個洞;下次從這裡接著抓,另一個指數照跑
            if st == "OK" and worst == "UP_TO_DATE":
                worst = "OK"
    if worst == "UP_TO_DATE" and any(plan.values()):
        worst = "EMPTY"
    res["state"] = worst
    return res


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb != "run":
        return PRIOR.main(argv)
    if not BASE._allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    import time as _time
    r = run(BASE._arg(a, "--start"), BASE._arg(a, "--end"), dry="--dry" in a, sleep=_time.sleep)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return _RC.get(r["state"], 1)


def selftest() -> int:
    import os
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    quiet = lambda *x, **k: None  # noqa: E731
    print("=== %s 薄尾自測(命令列真的走本版 · 看實際日子找洞;零網路;庫只在暫存夾)===" % ENGINE_TAG)
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
        with tempfile.TemporaryDirectory(prefix="eng232_v0106_") as td:
            db = Path(td) / "idx.duckdb"
            PRIOR.PRIOR.PRIOR.ensure_schema(db)
            # 2026-11-19 實錄的形狀:加權頭段補到 2021-01 停 → 中間空到 2023-03;櫃買 2022-08 ~ 2022-12 空
            V2._write(db, [row("2021-01-04", "TAIEX"), row("2021-01-12", "TAIEX"), row("2021-01-22", "TAIEX"), row("2021-01-29", "TAIEX"), row("2023-03-01", "TAIEX"), row("2023-12-29", "TAIEX"),
                           row("2021-01-04", "TPEX"), row("2022-07-29", "TPEX"), row("2023-01-03", "TPEX"), row("2026-11-18", "TPEX"),
                           row("2024-02-06", "TPEX"), row("2024-02-15", "TPEX"), row("2023-01-17", "TPEX"), row("2023-01-30", "TPEX")])
            seg = segments("2021-01-01", "2026-11-18", db)
            chk("① 中間的洞也排:加權 2021-01-30 → 2023-02-28 + 2023-12-30 起;櫃買 2022-07-30 → 2023-01-02",
                seg["TAIEX"] == [("2021-01-30", "2023-02-28"), ("2023-03-02", "2023-12-28"), ("2023-12-30", "2026-11-18")] and ("2022-07-30", "2023-01-02") in seg["TPEX"], seg)
            chk("② 春節不算洞(2024 差 9 天 · 2023 差 13 天)", not any(a <= "2024-02-10" <= b or a <= "2023-01-20" <= b for a, b in seg["TPEX"]), seg["TPEX"])
            neg = PRIOR.segments("2021-01-01", "2026-11-18", db)
            chk("③ 負控:v0105 的分段看不到加權中間的洞(只看最早 / 最新)", ("2021-01-30", "2023-02-28") not in neg["TAIEX"], neg["TAIEX"])
            chk("④ 空庫:兩個指數都從起日抓到迄日", segments("2021-01-01", "2026-11-18", Path(td) / "none.duckdb") == {"TAIEX": [("2021-01-01", "2026-11-18")], "TPEX": [("2021-01-01", "2026-11-18")]})
            calls = []
            orig = PRIOR._V4_RUN

            def fake_v4(start, end, **k):
                calls.append((dict(V2.starts()), end))
                return {"state": "OK", "fetched": 1, "added": 1, "calls": 1, "by_index": {kk: {"state": "OK", "added": 1} for kk in NEED}}

            def gap_taiex(start, end, **k):
                s = V2.starts()
                calls.append((dict(s), end))
                if s["TAIEX"] != FAR:
                    return {"state": "GAP", "stopped_at": s["TAIEX"], "note": "回空", "fetched": 0, "added": 0, "calls": 1, "by_index": {"TAIEX": {"state": "GAP", "added": 0}}}
                return {"state": "OK", "fetched": 1, "added": 1, "calls": 1, "by_index": {"TPEX": {"state": "OK", "added": 1}}}

            saved_env = os.environ.get("VIA_FROM_VCGC")
            os.environ["VIA_FROM_VCGC"] = "YES"
            saved_db = BASE.DB_IDX
            PRIOR._V4_RUN = fake_v4
            try:
                BASE.DB_IDX = db
                import contextlib
                import io
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = main(["run", "--start", "2021-01-01", "--end", "2026-11-18"])
                ran = [c[1] for c in calls]
                chk("⑤ 命令列 run --start 真的走本版分段(P1):每個洞叫一次前版,不是一次整段",
                    rc == 0 and len(calls) == len(seg["TAIEX"]) + len(seg["TPEX"]) and "2023-02-28" in ran and '"engine": "%s"' % ENGINE_TAG in buf.getvalue(), (rc, ran))
                v3 = PRIOR.PRIOR.PRIOR
                chk("⑥ 負控:v0103 的 main 叫的 run 不是 v0105 的(所以 v0105 經命令列沒生效)", v3.run is not PRIOR.run, v3.run)
                calls.clear()
                PRIOR._V4_RUN = gap_taiex
                r = run("2021-01-01", "2026-11-18", db=db, echo=quiet)
                chk("⑦ 加權第一個洞回空 → 加權停在那裡;櫃買照跑;總狀態 GAP",
                    r["state"] == "GAP" and r["by_index"]["TAIEX"]["state"] == "GAP" and r["by_index"]["TPEX"]["state"] == "OK"
                    and sum(1 for c in calls if c[0]["TAIEX"] != FAR) == 1 and sum(1 for c in calls if c[0]["TPEX"] != FAR) == len(seg["TPEX"]), r.get("by_index"))
                calls.clear()
                PRIOR._V4_RUN = lambda start, end, **k: calls.append(("plain", start, end)) or {"state": "OK"}
                run(None, "2026-11-18", db=db, echo=quiet)
                chk("⑧ 沒給 --start:照前版一次(不分段)", calls == [("plain", None, "2026-11-18")], calls)
                os.environ["VIA_FROM_VCGC"] = "NO"
                with contextlib.redirect_stdout(io.StringIO()):
                    rc_deny = main(["run", "--start", "2021-01-01"])
                chk("⑨ 不經入口 → DENY rc 2(零外呼)", rc_deny == 2)
            finally:
                PRIOR._V4_RUN = orig
                BASE.DB_IDX = saved_db
                if saved_env is None:
                    os.environ.pop("VIA_FROM_VCGC", None)
                else:
                    os.environ["VIA_FROM_VCGC"] = saved_env
            chk("⑩ 跑完還原:v0102 的 starts 是原件", V2.starts.__name__ == "starts")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 加速器橋真的匯入 · 網路工具橋在 · 不含本機路徑 · 不寫同意值", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "via_net_unified_v*.py" in src
        and ("C:" + "\\Users") not in src and ("_CONSENT\"] " + "=") not in src)
    with __import__("contextlib").redirect_stdout(__import__("io").StringIO()):
        rc = PRIOR.selftest()
    chk("⑫ 前版鏈自測照過", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s 本版 %d/%d · %s" % (ENGINE_TAG, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
