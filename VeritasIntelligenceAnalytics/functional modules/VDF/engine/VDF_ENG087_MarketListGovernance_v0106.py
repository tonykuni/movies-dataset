#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG087 v0106 — Taiwan stock list: day-over-day diff (ACTIVE / NEW / DELISTED).

v0105 stays (L04); this thin tail only adds `diff`. Everything else forwards to v0105 via __getattr__.

  diff [--prev <json>] [--json] [--dry] [--accept-mass]
      current = v0105 load_stock_list() (same source: vdf_tw_market.duckdb::tw_listings_industry,
                written by VDF_ENG055 lane L1 from TWSE t187ap03_L + TPEX mopsfin_t187ap03_O)
      previous = VIA_Reports/vdf/central_lists/TW_STOCK_LIST_SNAPSHOT_latest.json (or --prev <json>;
                 also accepts v0105's TW_LISTS_latest.json or a plain row list)
      every code gets one status: ACTIVE (in both) · NEW (only today) · DELISTED (only before).
      Rows are never dropped: a DELISTED code stays in the snapshot for good; codes are never renumbered.
      A code that comes back after DELISTED is NEW with relisted=true (first_seen kept).
      Guards: the current list must be GREEN/AMBER (a failed fetch is not a mass delisting → HOLD, no write);
              more than max(5, 2%) delisted in one step = REVIEW, snapshot not rolled unless --accept-mass.
      Writes (unless --dry) the new snapshot + a dated copy under VIA_Reports/vdf/central_lists/ (derived; never committed).

Runs only through VCGC (VIA_FROM_VCGC=YES) except `--selftest`, which is offline, deterministic, in-memory + temp dir.
Read-only on every DB; zero network (the list itself is refreshed by `refresh --plan` steps, operator-gated).
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

import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG087_MarketListGovernance"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.py$", p.name)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))),
                  key=_vnum, default=HERE / "VDF_ENG087_MarketListGovernance_v0105.py")
_SPEC = importlib.util.spec_from_file_location("eng087_prior_of_v0106", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = PRIOR          # v0105 自測用 sys.modules[__name__]
_SPEC.loader.exec_module(PRIOR)

ENGINE = Path(__file__).name
DIFF_SCHEMA = "VIA.VDF.TWStockListDiff.v1"
STATUSES = ("ACTIVE", "NEW", "DELISTED")
SNAPSHOT = PRIOR.CORE.REPORT_DIR / "TW_STOCK_LIST_SNAPSHOT_latest.json"
#: 一步內下市超過 max(5, 2%) = 疑似抓一半(REVIEW,不滾快照)
MASS_DELIST_MIN, MASS_DELIST_RATIO = 5, 0.02


def __getattr__(name: str):
    """PEP 562:v0105(以及其後轉的 v0104/v0103)公開面照舊可叫。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- 前一份快照
def _prev_rows(payload) -> list:
    """認三種形狀:本支快照 {rows}、v0105 TW_LISTS_latest {stock:{rows}}、純列表。"""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("rows"), list):
            return payload["rows"]
        stock = payload.get("stock")
        if isinstance(stock, dict) and isinstance(stock.get("rows"), list):
            return stock["rows"]
    return []


def load_prev(path: Path | None = None) -> tuple:
    """回 (rows, path_or_None)。檔不在 = 首跑(基準)。"""
    p = Path(path) if path else SNAPSHOT
    if not p.is_file():
        if path is None:
            legacy = PRIOR.LISTS_REPORT
            if legacy.is_file():
                p = legacy
            else:
                return [], None
        else:
            raise FileNotFoundError(str(p))
    return _prev_rows(json.loads(p.read_text(encoding="utf-8"))), p


# ---------------------------------------------------------------- 比對(純函式;不刪列、不改碼)
def diff_rows(current: list, previous: list, today: str) -> dict:
    prev = {}
    for r in previous or []:
        code = PRIOR._bare(r.get("code"))
        if code:
            prev[code] = r
    baseline = not prev
    cur = {}
    for r in current or []:
        code = PRIOR._bare(r.get("code"))
        if code and code not in cur:
            cur[code] = r
    out = []
    for code in sorted(set(prev) | set(cur)):
        p, c = prev.get(code), cur.get(code)
        if c is not None:
            base = {k: c.get(k, "") for k in ("name", "market", "yf_ticker", "industry")}
            if p is None:
                status, first, relisted = ("ACTIVE" if baseline else "NEW"), today, False
            elif str(p.get("status") or "ACTIVE") == "DELISTED":
                status, first, relisted = "NEW", p.get("first_seen") or today, True
            else:
                status, first, relisted = "ACTIVE", p.get("first_seen") or today, bool(p.get("relisted"))
            row = {"code": code, **base, "status": status, "first_seen": first, "last_seen": today,
                   "delisted_on": None, "relisted": relisted}
        else:
            row = {"code": code, **{k: p.get(k, "") for k in ("name", "market", "yf_ticker", "industry")},
                   "status": "DELISTED", "first_seen": p.get("first_seen") or "",
                   "last_seen": p.get("last_seen") or "",
                   "delisted_on": p.get("delisted_on") or today, "relisted": bool(p.get("relisted"))}
        out.append(row)
    counts = {s: sum(1 for r in out if r["status"] == s) for s in STATUSES}
    newly_delisted = [r["code"] for r in out if r["status"] == "DELISTED" and r["delisted_on"] == today
                      and str((prev.get(r["code"]) or {}).get("status") or "ACTIVE") != "DELISTED"]
    was_live = sum(1 for r in prev.values() if str(r.get("status") or "ACTIVE") != "DELISTED")
    limit = max(MASS_DELIST_MIN, int(was_live * MASS_DELIST_RATIO))
    return {"schema": DIFF_SCHEMA, "date": today, "baseline": baseline, "rows": out, "counts": counts,
            "new": [r["code"] for r in out if r["status"] == "NEW"], "delisted_today": newly_delisted,
            "mass_delist_limit": limit, "mass_delist": len(newly_delisted) > limit, "n": len(out)}


def run_diff(db: Path | None = None, prev_path: Path | None = None, today: str | None = None,
             write: bool = True, accept_mass: bool = False, out: Path | None = None) -> dict:
    today = today or date.today().isoformat()
    cur = PRIOR.load_stock_list(db)
    if cur["state"] not in ("GREEN", "AMBER"):
        return {"schema": DIFF_SCHEMA, "state": "HOLD", "date": today, "written": None,
                "why": f"現在的股票清單是 {cur['state']}({cur['why']});不能拿失敗的抓取判下市,快照不動"}
    prev, used = load_prev(prev_path)
    res = diff_rows(cur["rows"], prev, today)
    res.update(source={"db": cur["db"], "table": cur.get("table"), "list_state": cur["state"]},
               prev=str(used) if used else None)
    if res["mass_delist"] and not accept_mass:
        res.update(state="REVIEW", written=None,
                   why=f"一步下市 {len(res['delisted_today'])} 檔 > 上限 {res['mass_delist_limit']}(疑似抓一半);"
                       "確認後加 --accept-mass 才滾快照")
        return res
    res["state"] = "GREEN" if cur["state"] == "GREEN" else "AMBER"
    res["why"] = (f"{'基準' if res['baseline'] else '比對'} {res['n']} 檔 · " +
                  " · ".join(f"{k} {v}" for k, v in res["counts"].items()))
    res["written"] = None
    if write:
        target = Path(out) if out else SNAPSHOT
        target.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(res, ensure_ascii=False, indent=1)
        dated = target.with_name(target.name.replace("_latest", "_" + today.replace("-", "")))
        for t in (dated, target):
            tmp = t.with_suffix(".tmp")
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(t)
        res["written"] = str(target)
    return res


def _print_diff(res: dict) -> None:
    print(f"[VDF_ENG087 v0106 diff] {res['state']} · {res.get('why', '')}")
    if res.get("new"):
        print(f"  NEW({len(res['new'])}): {', '.join(res['new'][:30])}")
    if res.get("delisted_today"):
        print(f"  DELISTED today({len(res['delisted_today'])}): {', '.join(res['delisted_today'][:30])}")
    if res.get("written"):
        print(f"  snapshot: {res['written']}")


# ---------------------------------------------------------------- 自測(記憶體假料 + 暫存夾;不碰正庫、不寫 VIA_Reports)
def selftest() -> int:
    rc_prior = PRIOR.selftest()
    checks = []

    def chk(name, ok, note=""):
        checks.append((name, bool(ok), note))

    chk("前版 v0105 自測仍綠", rc_prior == 0, f"rc={rc_prior}")
    d0 = [{"code": "2330", "name": "台積電", "market": "TWSE"}, {"code": "2317", "name": "鴻海", "market": "TWSE"},
          {"code": "6488", "name": "環球晶", "market": "TPEX"}]
    b = diff_rows(d0, [], "2026-09-28")
    chk("首跑 = 基準:全 ACTIVE、沒有 NEW", b["baseline"] and b["counts"] == {"ACTIVE": 3, "NEW": 0, "DELISTED": 0})
    d1 = [{"code": "2330.TW", "name": "台積電", "market": "TWSE"}, {"code": "2317", "name": "鴻海", "market": "TWSE"},
          {"code": "7777", "name": "新掛牌", "market": "TPEX"}]
    r = diff_rows(d1, b["rows"], "2026-09-29")
    st = {x["code"]: x["status"] for x in r["rows"]}
    chk("新掛牌 = NEW", st.get("7777") == "NEW" and r["new"] == ["7777"], str(st))
    chk("下市 = DELISTED(列不刪)", st.get("6488") == "DELISTED" and r["n"] == 4 and r["delisted_today"] == ["6488"], str(st))
    chk("兩天都在 = ACTIVE(去後綴同碼)", st.get("2330") == "ACTIVE" and st.get("2317") == "ACTIVE")
    row = {x["code"]: x for x in r["rows"]}
    chk("代號不改、first_seen 保留、delisted_on 記日", row["2330"]["first_seen"] == "2026-09-28"
        and row["6488"]["delisted_on"] == "2026-09-29" and row["6488"]["last_seen"] == "2026-09-28")
    r2 = diff_rows(d1, r["rows"], "2026-09-30")
    st2 = {x["code"]: x for x in r2["rows"]}
    chk("已下市的第二天仍在、下市日不變、不再算今日下市", st2["6488"]["status"] == "DELISTED"
        and st2["6488"]["delisted_on"] == "2026-09-29" and r2["delisted_today"] == [] and st2["7777"]["status"] == "ACTIVE")
    r3 = diff_rows(d1 + [{"code": "6488", "name": "環球晶", "market": "TPEX"}], r2["rows"], "2026-10-01")
    st3 = {x["code"]: x for x in r3["rows"]}
    chk("下市後回來 = NEW + relisted(first_seen 保留)", st3["6488"]["status"] == "NEW" and st3["6488"]["relisted"]
        and st3["6488"]["first_seen"] == "2026-09-28")
    big = [{"code": str(1000 + i), "market": "TWSE"} for i in range(100)]
    m = diff_rows(big[:90], diff_rows(big, [], "2026-09-28")["rows"], "2026-09-29")
    chk("一步下市 10 > 上限 5 = mass_delist", m["mass_delist"] and m["mass_delist_limit"] == 5)
    chk("前快照三種形狀都認", _prev_rows({"rows": [1]}) == [1] and _prev_rows({"stock": {"rows": [2]}}) == [2]
        and _prev_rows([3]) == [3] and _prev_rows("x") == [])
    try:
        import duckdb  # noqa: F401
        have_duckdb = True
    except ImportError:
        have_duckdb = False
    if have_duckdb:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tw, _ = PRIOR._mk_dbs(root)
            snap = root / "out" / "TW_STOCK_LIST_SNAPSHOT_latest.json"
            prev = root / "prev.json"
            prev.write_text(json.dumps({"stock": {"rows": [{"code": "2330"}, {"code": "1101"}]}}), encoding="utf-8")
            res = run_diff(tw, prev, "2026-09-29", write=True, out=snap)
            st = {x["code"]: x["status"] for x in res["rows"]}
            chk("庫到快照:v0105 形狀當前快照 → 1101 DELISTED、6488 NEW", st == {"1101": "DELISTED", "2317": "NEW", "2330": "ACTIVE",
                                                                         "6488": "NEW", "8069": "NEW"}, str(st))
            chk("寫快照 + 日期副本(自測寫暫存夾)", snap.is_file() and (snap.parent / "TW_STOCK_LIST_SNAPSHOT_20260929.json").is_file()
                and json.loads(snap.read_text(encoding="utf-8"))["schema"] == DIFF_SCHEMA)
            again = run_diff(tw, snap, "2026-09-30", write=False)
            chk("用自己的快照再比:全 ACTIVE 或 DELISTED、無 NEW", again["counts"] == {"ACTIVE": 4, "NEW": 0, "DELISTED": 1}, str(again["counts"]))
            hold = run_diff(root / "nope.duckdb", snap, "2026-09-30", write=True, out=root / "o2.json")
            chk("清單抓不到 = HOLD,不寫、不判下市", hold["state"] == "HOLD" and not (root / "o2.json").exists())
    else:
        chk("duckdb 缺:庫測略過(ABSENT,不算綠)", False, "duckdb ModuleNotFoundError")
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        denied = main(["diff", "--dry"]) == 2
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    chk("不經 VCGC 就拒跑", denied)
    bad = [(n, note) for n, ok, note in checks if not ok]
    for n, ok, note in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {n}" + (f" · {note}" if (note and not ok) else ""))
    print(f"[VDF_ENG087 v0106] {len(checks) - len(bad)}/{len(checks)}" + (" FAIL" if bad else " OK"))
    return 1 if bad else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or "selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = a[0] if a else "status"
    if verb == "diff":
        prev = a[a.index("--prev") + 1] if "--prev" in a and a.index("--prev") + 1 < len(a) else None
        res = run_diff(prev_path=Path(prev) if prev else None, write="--dry" not in a, accept_mass="--accept-mass" in a)
        if "--json" in a:
            slim = {k: v for k, v in res.items() if k != "rows"}
            print(json.dumps(slim, ensure_ascii=False))
        else:
            _print_diff(res)
        return {"GREEN": 0, "AMBER": 0}.get(res["state"], 2)
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
