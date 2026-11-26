#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG242_ThreePeriodDistill v0103 — 薄尾(v0100–v0102 一字不動):inventory 也盤 Parquet 與 VAKE 來源

桌機實錄(2026-11-26 vdf3 · v0102 已讀資料家真庫):inventory sources 19 · ok 13 · missing_or_error 6。
讀碼:13 支 DuckDB 來源全部讀到;那 6 筆是 INTL_FIN 2 支 parquet + CN_MACRO / CN_NBS / GLOBAL_MACRO / SHIPPING 4 支 vake,
v0100 inventory 一律記 NOT_DUCKDB 並算進「缺或錯」→ 假黃(資料其實在,只是沒去看)。
本版:非 DuckDB 來源改交 VDF_MDL012_FetchGroups 尾版**現成的** source_status()(同系統的判法:parquet glob · vake 僅增分片 +
目錄庫 manifest;族群成員照 MDL012 load_inputs + read_ledger + effective_members),不另寫讀法。
  · 家(home)依 v0102 的找庫根順序試:資料家 → 倉內 output_hub → MDL012 暫存家;第一個「真的有那個 glob / vake\store」的家勝。
  · vake 一個族群多支成員 → 併成一列(成員數 · 有資料 · 紅 / 沒資料點名 · 最新日期)。
  · 狀態:有列且不是 RED / NODATA / LOCKED = OK(新鮮度另記 freshness);都沒有 = 照實 NODATA 並寫「所有根都沒有」。
唯讀(MDL012 source_status 本來就 READ_ONLY / read_parquet);不寫庫、不出網;資料內容不離開本機(只有列數 · 日期 · 路徑)。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
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
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG242_ThreePeriodDistill"
VERSION = "v0103"
TAG = f"{STEM} {VERSION}"
BAD_STATES = ("RED", "NODATA", "LOCKED")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{PRIOR_PATH.stem}_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                 # v0100 本體(v0102 已把 m012 / inventory / names 換裝在上面)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _home_for(src: dict, homes: list):
    """第一個真的有這個來源的家 → (Path, 為什麼);都沒有 → (None, '所有根都沒有')。"""
    for h, why in homes:
        h = Path(h)
        if not h.is_dir():
            continue
        if src.get("type") == "parquet" and src.get("glob") and any(h.glob(src["glob"])):
            return h, why
        if src.get("type") == "vake" and (h / "vake" / "store").is_dir():
            return h, why
    return None, "所有根都沒有"


def _fold(g: dict, src: dict, rows: list, home, why: str) -> dict:
    """source_status 的多列(vake 一支成員一列)→ inventory 一列。
    「有沒有資料」與「新不新」分開:有列 = 存在(state OK);source_status 的 RED 若只是過期(有列)記 stale,不當缺。"""
    n = lambda r: int(r.get("rows_asof") or r.get("rows_total") or 0)  # noqa: E731
    exist = [r for r in rows if n(r) > 0 and r.get("state") not in ("NODATA", "LOCKED")]
    missing = [r for r in rows if r not in exist]
    stale = [r for r in exist if r.get("state") == "RED"]
    latest = sorted((str(r["max_date"]) for r in rows if r.get("max_date")), reverse=True)
    out = {"group": g["id"], "db": src.get("glob") or "vake", "table": src.get("type"),
           "state": "OK" if exist else (rows[0].get("state", "NODATA") if rows else "NODATA"),
           "source_type": src.get("type"), "members": len(rows), "members_ok": len(exist),
           "rows": sum(n(r) for r in rows), "latest": latest[:3], "freshness": sorted({r.get("state") for r in rows if r.get("state")}),
           "home": PRIOR.tilde(home) if home is not None else None, "home_why": why}
    if missing:
        out["not_ok"] = [f"{r.get('table_name')}:{r.get('state')}{(' · ' + str(r.get('note'))[:60]) if r.get('note') else ''}" for r in missing][:20]
    if stale:
        out["stale"] = [f"{r.get('table_name')}:落後 {r.get('lag_days')} 天" for r in stale][:20]
    return out


def inventory(mod, rows_or_book, roots=None, lake=None):
    res = PRIOR.inventory(mod, rows_or_book, roots, lake)       # v0102:DuckDB 來源照讀(資料家優先)
    if not callable(getattr(mod, "source_status", None)):
        return res
    book = mod.load_book()
    try:
        ledger = mod.read_ledger() if callable(getattr(mod, "read_ledger", None)) else []
        sel, matrix = (mod.load_inputs(book)[:2] if callable(getattr(mod, "load_inputs", None)) else ({}, {}))
    except Exception as e:  # noqa: BLE001 - 成員冊讀不到照實記,不擋
        ledger, sel, matrix = [], {}, {}
        BASE.say(f"  [黃] MDL012 成員冊讀不到({type(e).__name__}),vake 族群成員照空集合盤")
    homes = PRIOR.search_roots(mod)
    as_of = date.today().isoformat()
    srcs = {(g["id"], i): (g, s) for g in book["groups"] for i, s in enumerate(g.get("sources") or []) if s.get("type") != "duckdb"}
    it = iter(sorted(srcs))
    new_rows = []
    for r in res["rows"]:
        if r.get("state") != "NOT_DUCKDB":
            new_rows.append(r)
            continue
        key = next(it, None)
        if key is None:
            new_rows.append(r)
            continue
        g, s = srcs[key]
        home, why = _home_for(s, homes)
        if home is None:
            new_rows.append({"group": g["id"], "db": s.get("glob") or "vake", "table": s.get("type"), "state": "NODATA",
                             "source_type": s.get("type"), "home": None, "home_why": why})
            BASE.say(f"  盤 {s.get('type')} {g['id']} ← 找不到({why})")
            continue
        try:
            eff = mod.effective_members(g, ledger, sel, matrix)
        except Exception:  # noqa: BLE001
            eff = {"members": []}
        rows = mod.source_status(s, g, book, as_of, eff, [p for p, _ in homes], home)
        row = _fold(g, s, rows, home, why)
        new_rows.append(row)
        BASE.say(f"  盤 {s.get('type')} {g['id']} ← {row['home']}({why})· 有資料 {row['members_ok']}/{row['members']} · 最新 {row['latest'][:1]}"
                 + (f" · 過期 {len(row['stale'])}" if row.get("stale") else ""))
    bad = [r for r in new_rows if r.get("state") != "OK"]
    stale = [r for r in new_rows if r.get("stale") or r.get("not_ok")]
    res["rows"] = new_rows
    res["counts"] = dict(res.get("counts") or {}, sources=len(new_rows), ok=len(new_rows) - len(bad), missing_or_error=len(bad),
                         stale_or_partial=len(stale))
    res["lamp"] = "GREEN" if not bad and not stale else "YELLOW"
    return res


_ORIG_INV = BASE.inventory


def _install():
    BASE.inventory = inventory
    BASE.TAG = TAG


def _uninstall():
    BASE.inventory = _ORIG_INV
    BASE.TAG = PRIOR.TAG


_install()


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    return BASE.main()


def selftest() -> int:
    import os
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("前版 = 同家族比自己小的最大版 · inventory 換裝在 v0100 本體 · 橫幅寫本版",
        _vnum(PRIOR_PATH) < _vnum(Path(__file__)) and BASE.inventory is inventory and BASE.TAG == TAG)
    keep_env = os.environ.get("VIA_VDF_DB_HOME")
    try:
        duckdb = BASE._duck()
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            home = td / "via_database" / "vdf_database"
            (home / "1-6-FinancialModel").mkdir(parents=True)
            c = duckdb.connect()
            c.execute(f"COPY (SELECT DATE '2026-09-30' AS date, 'NVDA' AS ticker, 1.0 AS eps UNION ALL "
                      f"SELECT DATE '2026-06-30', 'NVDA', 0.9) TO '{(home / '1-6-FinancialModel' / 'q.parquet').as_posix()}' (FORMAT parquet)")
            (home / "vake" / "store" / "akshare" / "macro_a" / "p0").mkdir(parents=True)
            c.execute(f"COPY (SELECT DATE '2026-10-01' AS _vake_date, 1.5 AS v) TO "
                      f"'{(home / 'vake' / 'store' / 'akshare' / 'macro_a' / 'p0' / 'part.parquet').as_posix()}' (FORMAT parquet)")
            c.close()
            os.environ["VIA_VDF_DB_HOME"] = str(home)
            mm = PRIOR._ORIG["m012"]()
            book = {"groups": [
                {"id": "INTL_FIN", "cadence": "quarterly", "membership": "FIXED_ALL", "sources": [{"type": "parquet", "glob": "1-6-FinancialModel/q.parquet", "date_col": "date", "key_col": "ticker"}]},
                {"id": "CN_MACRO", "cadence": "macro", "membership": "FIXED_ALL", "sources": [{"type": "vake"}]},
                {"id": "SHIPPING", "cadence": "macro", "membership": "FIXED_ALL", "sources": [{"type": "parquet", "glob": "nope/*.parquet"}]}],
                "cadence_tolerance_days": {}, "detect": {"date_cols": ["date"]}}

            class FakeMod:
                default_home = staticmethod(lambda: td / "stage")
                load_book = staticmethod(lambda: book)
                find_db = staticmethod(mm.find_db)
                source_status = staticmethod(mm.source_status)
                read_ledger = staticmethod(lambda: [])
                load_inputs = staticmethod(lambda b: ({}, {}, None, None))
                effective_members = staticmethod(lambda g, led, sel=None, mx=None: {"members": ["macro_a"] if g["id"] == "CN_MACRO" else None,
                                                                                    "exclude": [], "filter": False, "origin": "test"})

            PRIOR.HITS.clear()
            PRIOR.ROOTS_SHOWN.clear()
            res = inventory(FakeMod, None)
            by = {r["group"]: r for r in res["rows"]}
            chk("parquet 來源:在資料家找到 glob → OK · 列數 2 · 最新日期 · 家 = 資料家",
                by["INTL_FIN"]["state"] == "OK" and by["INTL_FIN"]["rows"] == 2 and "資料家" in by["INTL_FIN"]["home_why"]
                and by["INTL_FIN"]["latest"][:1] == ["2026-09-30"], by.get("INTL_FIN"))
            chk("vake 來源:讀資料家 vake\\store 的僅增分片 → 有資料 1/1 = OK(不再記 NOT_DUCKDB);資料舊 → 另記 stale,不當缺",
                by["CN_MACRO"]["state"] == "OK" and by["CN_MACRO"]["members"] == 1 and by["CN_MACRO"]["members_ok"] == 1
                and by["CN_MACRO"].get("stale") and "落後" in by["CN_MACRO"]["stale"][0], by.get("CN_MACRO"))
            chk("哪個家都沒有的 glob → NODATA 照實 · 寫「所有根都沒有」(不假綠)",
                by["SHIPPING"]["state"] == "NODATA" and by["SHIPPING"]["home_why"] == "所有根都沒有", by.get("SHIPPING"))
            chk("總數重算:3 來源 · OK 2 · 缺 1 · 過期 1 · YELLOW;不再有 NOT_DUCKDB",
                res["counts"]["sources"] == 3 and res["counts"]["ok"] == 2 and res["counts"]["stale_or_partial"] == 1 and res["lamp"] == "YELLOW"
                and not any(r.get("state") == "NOT_DUCKDB" for r in res["rows"]), res["counts"])
    finally:
        if keep_env is None:
            os.environ.pop("VIA_VDF_DB_HOME", None)
        else:
            os.environ["VIA_VDF_DB_HOME"] = keep_env
        PRIOR.HITS.clear()
        PRIOR.ROOTS_SHOWN.clear()
    _uninstall()
    try:
        print(f"[前版] {PRIOR_PATH.name} 自測(本版換裝卸下)", flush=True)
        rc = PRIOR.selftest()
    finally:
        _install()
    chk("前版 v0102 鏈自測照過(rc 0)· 跑完本版又換上", rc == 0 and BASE.inventory is inventory, rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:雙橋在 · 零 TA-Lib · 不設同意閘",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
