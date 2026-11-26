#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG239_ParquetLakeBuild v0104 — 薄尾(v0100–v0103 一字不動):輸出 DataFrame 前後(起日 · 迄日)可調整,一次帶到底

操作員 2026-11-26:「讀取資料庫 …\via_database 裡面有資料 · 增量擷取 · 必要時調整資料庫與引擎對齊 · 前後 DATAFRAME 設為可調整」。
讀碼(VCGC 省 Token read / slice)確認:
  · 資料家已對:VDF_DataHome_SSOT 尾版第一個家就是 …\via_database\vdf_database;v0103 入湖先讀它的 output_hub。
  · 範圍冊已對:DataPlane 冊 params.fetch = 2018-01-01 → latest;FetchGroups 帳本 TW_MARKET · FIN · OTHER 起日 2018-01-01(2026-11-22),MACRO 1990。
  · 缺口(前後沒有一個地方一起調):
      起日:v0103 只從 DataPlane 冊讀 start;迄日:冊上的 params.fetch.end 沒人讀,v0100 自己用「今天」;
      ⓪ 全族群擷取(FetchGroups)不帶 --as-of → 用它自己帳本的 as-of,兩邊的「最新」可能不是同一天;
      ③ 管家 VIEW 是整張湖(只有入湖時看起日),輸出 DataFrame 的「後」端沒有界線。
本版(只換裝,不改前版邏輯):
  ① 視窗 = 起日 · 迄日:--start / --end(命令列)> DataPlane 冊 params.fetch.start / end > 預設(2018-01-01 · latest)。
     latest = 台北時間最近一個已收盤交易日(週一至週五;15:00 前算前一交易日;跟 FetchGroups 冊 latest_rule 同一條)。
     格式錯 / 起日晚於迄日 → 當場拒絕 rc 2、零寫入。
  ② 同一個視窗帶到每一段:⓪ FetchGroups run 加 --as-of <迄日>;① ENG064 回補 --start / --end;② 入湖起日(增量:水位 + 遲到鍵,照 v0102);
     ③ 管家 VIEW 帶日期的表只露 起日 ≤ 日期 ≤ 迄日(湖本身只增不刪;視窗改寬再跑一次 VIEW 就回來);
     狀態收據多一段 window 與每表 lag_to_end_days(對迄日落後幾天)。
  ③ window 動詞(唯讀):印出生效視窗與來源 · FetchGroups 各大類起日與 as-of 設定;大類起日晚於視窗起日 = 黃並點名、給該系統自己的改法
     (FetchGroups start --category X --set … --apply;本支不代寫帳本)。
零網路(擷取由 ENG064 / FetchGroups 經網路工具與雙同意閘負責);不設同意閘;不用 TA-Lib。
用法:py VDF_ENG239_ParquetLakeBuild_v0104.py window [--start S] [--end E|latest] [--json]
      py VDF_ENG239_ParquetLakeBuild_v0104.py run --all [--start S] [--end E|latest] [--jobs 3] · status · --selftest
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

import datetime as _dt
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
STEM = "VDF_ENG239_ParquetLakeBuild"
VERSION = "v0104"
TAG = f"{STEM} {VERSION}"
DEFAULT_START, DEFAULT_END = "2018-01-01", "latest"
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0                                       # v0100 本體(run 依模組全域名找 catalog / status / fetch)
P1 = getattr(getattr(PRIOR, "PRIOR", None), "P1", None)   # v0101(run --all 依模組全域名找 fetch_all)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _tail(d: Path, pat: str):
    hits = sorted(d.glob(pat), key=_vnum)
    return hits[-1] if hits else None


def _book(pat: str) -> dict:
    p = _tail(VDF, pat)
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p else {}
    except (OSError, ValueError):
        return {}


def latest_close(now=None) -> str:
    """台北時間最近一個已收盤交易日:週一至週五;當天 15:00 前算前一交易日(假日表不在這裡,照 FetchGroups 冊 latest_rule)。"""
    tpe = _dt.timezone(_dt.timedelta(hours=8))
    t = (now or _dt.datetime.now(_dt.timezone.utc)).astimezone(tpe)
    d = t.date() if t.hour >= 15 else t.date() - _dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= _dt.timedelta(days=1)
    return d.isoformat()


def _opt(argv: list, k: str):
    return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else None


def resolve_window(argv: list, book: dict | None = None, now=None) -> dict:
    """→ {start, end, end_setting, start_why, end_why, ok, why}。命令列 > DataPlane 冊 > 預設。"""
    fetch = ((book if book is not None else _book("VDF_DataPlane_SSOT_v*.json")).get("params") or {}).get("fetch") or {}
    s_cli, e_cli = _opt(argv, "--start"), _opt(argv, "--end")
    s = s_cli or fetch.get("start") or DEFAULT_START
    e_set = e_cli or fetch.get("end") or DEFAULT_END
    w = {"start": s, "end_setting": e_set,
         "start_why": "--start" if s_cli else ("DataPlane 冊 params.fetch.start" if fetch.get("start") else "預設"),
         "end_why": "--end" if e_cli else ("DataPlane 冊 params.fetch.end" if fetch.get("end") else "預設")}
    if not _ISO.match(str(s)):
        return dict(w, end=None, ok=False, why=f"起日格式要 YYYY-MM-DD:{s}")
    e = latest_close(now) if str(e_set).lower() == "latest" else e_set
    if not _ISO.match(str(e)):
        return dict(w, end=None, ok=False, why=f"迄日格式要 YYYY-MM-DD 或 latest:{e_set}")
    try:
        ds, de = _dt.date.fromisoformat(s), _dt.date.fromisoformat(e)
    except ValueError as exc:
        return dict(w, end=e, ok=False, why=f"日期不存在:{exc}")
    if ds > de:
        return dict(w, end=e, ok=False, why=f"起日 {s} 晚於迄日 {e}")
    return dict(w, end=e, ok=True, why="")


def category_starts(book: dict | None = None, ledger_path: Path | None = None) -> dict:
    """FetchGroups 冊的大類預設起日,再套成員帳本 kind=start(後寫的蓋前面;value=default 回預設)。"""
    book = book if book is not None else _book("VDF_FetchGroups_SSOT_v*.json")
    lp = ledger_path if ledger_path is not None else (VDF / "VDF_FetchGroups_MemberLedger_v0100.jsonl")
    out = {c["id"]: c.get("default_start") for c in book.get("categories") or [] if c.get("id")}
    dflt = dict(out)
    asof = (book.get("as_of") or {}).get("default", "latest")
    try:
        lines = lp.read_text(encoding="utf-8").splitlines() if lp.is_file() else []
    except OSError:
        lines = []
    for ln in lines:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("kind") == "start" and r.get("category") in out:
            out[r["category"]] = dflt[r["category"]] if r.get("value") == "default" else r.get("value")
        elif r.get("kind") == "asof":
            asof = r.get("value") or asof
    return {"starts": out, "as_of_setting": asof}


def alignment(w: dict, cs: dict) -> dict:
    """大類起日晚於視窗起日 → 該大類從視窗起日到它的起日之間抓不到(黃,點名);早於視窗不算錯(湖與 VIEW 只露視窗)。"""
    late = {k: v for k, v in (cs.get("starts") or {}).items() if v and w.get("start") and str(v) > str(w["start"])}
    fix = [f"VDF_MDL012_FetchGroups start --category {k} --set {w['start']} --apply" for k in sorted(late)]
    return {"late_categories": late, "fix": fix, "rc": 2 if late else 0}


W = {}                                              # 這一輪的視窗(run / status 用)


def fetch_all(groups: str = "ALL", jobs: int = 5) -> dict:
    """⓪ 同 v0101,但 FetchGroups run 帶 --as-of <視窗迄日>(全族群跟湖同一個「最新」)。"""
    hits = sorted(VDF.glob("VDF_MDL012_FetchGroups_v*.py"), key=_vnum)
    if not hits:
        return {"state": "ABSENT", "note": "找不到 VDF_MDL012_FetchGroups"}
    gates = {k: os.environ.get(k, "") for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    gated = not all(v.upper() == "YES" for v in gates.values())
    args = [sys.executable, str(hits[-1]), "run", "--groups", groups, "--jobs", str(jobs), "--mode", "live"]
    if W.get("end"):
        args += ["--as-of", W["end"]]
    print(f"[⓪全族群] {hits[-1].name} run --groups {groups} --jobs {jobs} --mode live"
          + (f" --as-of {W['end']}" if W.get("end") else "") + f" · 同意閘 {gates}", flush=True)
    env = dict(os.environ, VIA_FROM_VCGC=os.environ.get("VIA_FROM_VCGC", "YES"), PYTHONUTF8="1")
    p = subprocess.run(args, env=env, cwd=str(VDF))
    state = "GATED" if gated else ("OK" if p.returncode == 0 else ("PARTIAL" if p.returncode in (2, 3, 4) else "FAIL"))
    return {"state": state, "rc": p.returncode, "engine": hits[-1].name,
            "note": "同意閘沒開 → 擷取引擎拒抓;湖用庫內現有資料" if gated else ""}


def catalog(lake: Path) -> Path:
    """③ 同 v0100,但帶日期的表 VIEW 只露視窗 起日 ≤ 日期 ≤ 迄日(湖分片不動)。"""
    import duckdb
    s, e = W.get("start"), W.get("end")
    cat = lake / "VDF_catalog.duckdb"
    con = duckdb.connect(str(cat))
    try:
        for dbdir in sorted(p for p in lake.iterdir() if p.is_dir() and not p.name.startswith(".")):
            for tdir in sorted(p for p in dbdir.iterdir() if p.is_dir()):
                parts = sorted(tdir.glob("part-*.parquet"))
                if not parts:
                    continue
                cols = [r[0] for r in P0._mem().execute(f"describe select * from read_parquet('{parts[-1].as_posix()}')").fetchall()]
                dc = P0._date_col(cols)
                src = f"'{tdir.as_posix()}/*.parquet'" if dc else f"'{parts[-1].as_posix()}'"
                where = (f' where try_cast("{dc}" as date) between DATE \'{s}\' and DATE \'{e}\'') if (dc and s and e) else ""
                con.execute(f'create or replace view "v_{dbdir.name}__{tdir.name}" as select * from read_parquet({src}, union_by_name=true){where}')
    finally:
        con.close()
    return cat


def status(lake: Path, write: bool = True) -> dict:
    """同 v0100,另記 window 與每表 lag_to_end_days(對視窗迄日落後幾天)。"""
    out = _STATUS_BEFORE(lake, write=False)
    if W.get("end"):
        de = _dt.date.fromisoformat(W["end"])
        for r in out.get("tables") or []:
            hi = r.get("max_date")
            r["lag_to_end_days"] = (de - _dt.date.fromisoformat(hi[:10])).days if hi else None
        out["window"] = {k: W.get(k) for k in ("start", "end", "end_setting", "start_why", "end_why")}
    out["engine"] = TAG
    if write and out.get("tables") is not None and (lake / "VDF_catalog.duckdb").is_file():
        (lake / "LAKE_STATUS_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    return out


_STATUS_BEFORE = P0.status
_SAVED = {}


def _install(w: dict):
    W.clear()
    W.update(w)
    _SAVED.update(catalog=P0.catalog, status=P0.status, fetch_all=getattr(P1, "fetch_all", None) if P1 else None)
    P0.catalog, P0.status = catalog, status
    if P1 is not None and hasattr(P1, "fetch_all"):
        P1.fetch_all = fetch_all


def _uninstall():
    if _SAVED:
        P0.catalog, P0.status = _SAVED["catalog"], _SAVED["status"]
        if P1 is not None and _SAVED.get("fetch_all") is not None:
            P1.fetch_all = _SAVED["fetch_all"]
    _SAVED.clear()
    W.clear()


def _strip(argv: list, keys=("--start", "--end")) -> list:
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a in keys:
            skip = True
            continue
        out.append(a)
    return out


def window(argv: list) -> int:
    w = resolve_window(argv)
    cs = category_starts()
    al = alignment(w, cs) if w["ok"] else {"late_categories": {}, "fix": [], "rc": 2}
    rc = 2 if not w["ok"] else al["rc"]
    res = {"engine": TAG, "window": w, "fetchgroups": cs, "alignment": al, "rc": rc}
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return rc
    if not w["ok"]:
        print(f"[拒絕] {w['why']}(零寫入)")
        return 2
    print(f"[視窗] 起 {w['start']}({w['start_why']})· 迄 {w['end']}({w['end_why']};設定 {w['end_setting']})")
    print(f"[FetchGroups] as-of 設定 {cs['as_of_setting']}(run 時改帶 --as-of {w['end']})· 大類起日 "
          + " · ".join(f"{k} {v}" for k, v in cs["starts"].items()))
    if al["late_categories"]:
        print("[黃] 這些大類起日晚於視窗起日,中間那段抓不到:" + " · ".join(f"{k} {v}" for k, v in al["late_categories"].items()))
        for f in al["fix"]:
            print(f"   改法(VDF 自己的動詞;本支不代寫):{f}")
    else:
        print("[綠] 各大類起日都不晚於視窗起日(早於的大類,湖與 VIEW 只露視窗)")
    return rc


def run(argv: list) -> int:
    w = resolve_window(argv)
    if not w["ok"]:
        print(f"[拒絕] {w['why']}(零寫入)", flush=True)
        return 2
    al = alignment(w, category_starts())
    print(f"[視窗] 起 {w['start']}({w['start_why']})· 迄 {w['end']}({w['end_why']})· ⓪ as-of · ① 回補 · ② 入湖 · ③ VIEW 同一個視窗", flush=True)
    if al["late_categories"]:
        print("[黃] 大類起日晚於視窗起日:" + " · ".join(f"{k} {v}" for k, v in al["late_categories"].items()) + " · 改法:" + " ; ".join(al["fix"]), flush=True)
    keep = sys.argv[:]
    _install(w)
    try:
        sys.argv = [keep[0] if keep else __file__, "run", *_strip(argv), "--start", w["start"], "--end", w["end"]]
        rc = PRIOR.main()
    finally:
        sys.argv = keep
        _uninstall()
    return PRIOR_worse(rc, al["rc"])


def PRIOR_worse(a: int, b: int) -> int:                # 0 綠 < 2 黃 < 1 紅
    rank = {0: 0, 2: 1, 1: 2}
    return max((a, b), key=lambda x: rank.get(x, 2))


def main() -> int:
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        return selftest()
    if a and a[0] == "window":
        return window(a[1:])
    if a and a[0] == "run":
        return run(a[1:])
    if a and a[0] == "status":
        w = resolve_window(a[1:])
        _install(w if w["ok"] else {})
        try:
            return PRIOR.main()
        finally:
            _uninstall()
    return PRIOR.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 自測(全在暫存夾;不讀本機庫、不出網)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    bk = {"params": {"fetch": {"start": "2018-01-01", "end": "latest"}}}
    fri = _dt.datetime(2026, 11, 28, 3, 0, tzinfo=_dt.timezone.utc)          # 台北週六 11:00
    mon_am = _dt.datetime(2026, 11, 30, 2, 0, tzinfo=_dt.timezone.utc)       # 台北週一 10:00
    tue_pm = _dt.datetime(2026, 12, 1, 8, 0, tzinfo=_dt.timezone.utc)        # 台北週二 16:00
    chk("③ latest = 台北最近已收盤交易日(週六 → 週五 · 週一 15:00 前 → 上週五 · 週二收盤後 → 當天)",
        (latest_close(fri), latest_close(mon_am), latest_close(tue_pm)) == ("2026-11-27", "2026-11-27", "2026-12-01"))
    w0 = resolve_window([], bk, fri)
    w1 = resolve_window(["--start", "2020-03-01", "--end", "2024-12-31"], bk, fri)
    chk("④ 視窗來源:沒給 → 冊 2018-01-01 · latest;給了 → 命令列蓋冊(前後都可調)",
        (w0["ok"], w0["start"], w0["end"], w0["start_why"].startswith("DataPlane"), w0["end_why"].startswith("DataPlane")) == (True, "2018-01-01", "2026-11-27", True, True)
        and (w1["start"], w1["end"], w1["start_why"], w1["end_why"]) == ("2020-03-01", "2024-12-31", "--start", "--end"), (w0, w1))
    bads = [resolve_window(x, bk, fri) for x in (["--start", "2025-01-01", "--end", "2024-01-01"], ["--start", "2018/01/01"],
                                                  ["--end", "yesterday"], ["--start", "2018-02-30"])]
    chk("⑤ 起日晚於迄日 · 格式錯 · 日期不存在 → ok=False(run 會 rc 2 零寫入)", not any(b["ok"] for b in bads), [b["why"] for b in bads])
    keep_main = PRIOR.main
    try:
        PRIOR.main = lambda: (_ for _ in ()).throw(AssertionError("不該跑到前版"))
        chk("⑥ run 視窗錯 → 當場拒絕 rc 2,沒進前版", run(["--start", "2025-01-01", "--end", "2024-01-01"]) == 2)
    finally:
        PRIOR.main = keep_main
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fb = {"categories": [{"id": "TW_MARKET", "default_start": "2022-07-01"}, {"id": "MACRO", "default_start": "1990-01-01"},
                             {"id": "FIN", "default_start": "2021-01-01"}], "as_of": {"default": "latest"}}
        lp = td / "ledger.jsonl"
        lp.write_text(json.dumps({"kind": "start", "category": "TW_MARKET", "value": "2018-01-01"}) + "\n", encoding="utf-8")
        cs = category_starts(fb, lp)
        al = alignment({"start": "2018-01-01"}, cs)
        chk("⑦ 大類起日:帳本蓋預設(TW_MARKET 2018)· 晚於視窗的 FIN 2021 點名黃並給改法 · 早於的 MACRO 不算錯",
            cs["starts"] == {"TW_MARKET": "2018-01-01", "MACRO": "1990-01-01", "FIN": "2021-01-01"}
            and list(al["late_categories"]) == ["FIN"] and al["rc"] == 2 and "--category FIN --set 2018-01-01" in al["fix"][0], (cs, al))
        import duckdb
        db = td / "vdf_tw_market.duckdb"
        c = duckdb.connect(str(db))
        c.execute("create table tw_daily_prices(ticker varchar, date date, close double)")
        c.execute("insert into tw_daily_prices values ('2330','2017-12-29',1),('2330','2018-01-02',2),('2330','2024-06-03',3),('2330','2026-11-20',4)")
        c.execute("create table tw_stock_list(ticker varchar, name varchar)")
        c.execute("insert into tw_stock_list values ('2330','x')")
        c.close()
        lake = td / "lake"
        P0.ingest(lake, "2017-01-01", [db])
        _install({"start": "2018-01-01", "end": "2024-12-31", "end_setting": "2024-12-31", "start_why": "t", "end_why": "t"})
        try:
            P0.catalog(lake)
            q = duckdb.connect(str(lake / "VDF_catalog.duckdb"), read_only=True)
            n1 = q.execute('select count(*) from "v_vdf_tw_market__tw_daily_prices"').fetchone()[0]
            s1 = q.execute('select count(*) from "v_vdf_tw_market__tw_stock_list"').fetchone()[0]
            q.close()
            st = P0.status(lake)
            row = [r for r in st["tables"] if r["view"].endswith("tw_daily_prices")][0]
            saved = json.loads((lake / "LAKE_STATUS_latest.json").read_text(encoding="utf-8"))
        finally:
            _uninstall()
        chk("⑧ VIEW 只露視窗 2018-01-01 → 2024-12-31(湖有 4 列、VIEW 2 列)· 快照表整張",
            (n1, s1) == (2, 1), (n1, s1))
        chk("⑨ 狀態收據帶 window 與 lag_to_end_days(對迄日:2024-12-31 − 2024-06-03 = 211)",
            saved.get("window", {}).get("end") == "2024-12-31" and row.get("lag_to_end_days") == 211 and row["min_date"] == "2018-01-02", row)
        _install({"start": "2018-01-01", "end": "2026-11-27"})
        try:
            P0.catalog(lake)
            q = duckdb.connect(str(lake / "VDF_catalog.duckdb"), read_only=True)
            n2 = q.execute('select count(*) from "v_vdf_tw_market__tw_daily_prices"').fetchone()[0]
            q.close()
        finally:
            _uninstall()
        chk("⑩ 迄日放寬再建 VIEW → 列回來(湖只增不刪;不用重抓)", n2 == 3, n2)
        lake_files = sorted(p.name for p in (lake / "vdf_tw_market" / "tw_daily_prices").glob("*.parquet"))
        chk("⑪ 改視窗不動湖分片(分片數不變)", len(lake_files) == 1, lake_files)
        seen = {}
        keep_run = subprocess.run
        _install({"start": "2018-01-01", "end": "2026-11-27"})
        try:
            subprocess.run = lambda args, **kw: seen.setdefault("args", args) and type("R", (), {"returncode": 0})()
            P1.fetch_all("ALL", 3) if P1 is not None else None
        finally:
            subprocess.run = keep_run
            _uninstall()
        a = seen.get("args") or []
        chk("⑫ ⓪ 全族群擷取帶 --as-of <迄日>(跟湖同一個「最新」)· 跑完換回 v0101 原函式",
            P1 is not None and a[-2:] == ["--as-of", "2026-11-27"] and P1.fetch_all is not fetch_all and P0.catalog is not catalog, a[-4:])
    rc = PRIOR.selftest()
    chk("⑬ 前版 v0103 自測照過(rc 0)", rc == 0, rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑭ 檔面:第 3 行加速器標記 · 雙橋 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:NET-BRIDGE:v0100]" in src and "HERE.glob(STEM" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
