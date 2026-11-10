#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VeritaQuantGuard(VQG)v0110 — v0109 薄尾(v0109 一字不改 · SHA-256 釘在 PRIOR_SHA256)。

操作員 2026-11-10:「VQG 產出的數據到 TEMP 存放 · 增量更新去重維護 · 用 PARQUET 一樣 · 刪除機制未定 · 先維持現況」。

本版只加一件事:VQG 每次匯出的數據表進 TEMP 下的 VQG 增量 Parquet 庫(和其他系統同一套 = 共用套件 VIA_ParquetLake v0101:
本體 Parquet zstd 分片 · 管家 DuckDB VIEW · _manifest.jsonl 只增)。
  位置   TEMP 根 = VIA_TEMP_ROOT > Windows %LOCALAPPDATA%\VIA_TEMP > 系統 temp/VIA_TEMP(和 VDF ActivateVDF 同一條規則)
         庫根 = <TEMP 根>/VIA_Lake → VQG 只寫 <庫根>/VQG/;可用 VIA_VQG_STORE_ROOT 或 --store-root 換位置。
  九張表(去重鍵):series(ticker, date)· indicators(ticker, observation_date)·
         indicator_results(ticker, observation_date, indicator_id, window_n, solution_id)· quant_analysis(ticker, observation_date)·
         backtest_curve(ticker, date)· backtest_summary(ticker, strategy)· factor_ic(date)· stats(ticker)· return_corr(ticker)
         + store_runs(每次入庫一列 · 只當紀錄)。
  增量 / 去重:每列算內容指紋 vqg_row_sha(不含每輪都會變的欄:as_of · request_key · input_sha256 · engine_version · engine ·
         formula_engine · link_id · source_files 與中繼欄 vqg_export / vqg_row_sha / _ingested_at)。
         鍵沒見過 → 新增;鍵見過且指紋相同 → 跳過(同一份匯出重入 = 0 列);鍵見過但值變了 → 追加新版本,VIEW v_<表> 取最新。
  刪除:不刪。沒有任何程式路徑刪分片或列,舊版本留在舊分片(刪除機制未定 · 維持現況)。
  接法:export-vap 跑完(v0109 匯出 + 量化分析)自動入庫;--no-store 不入庫。單獨:store [--export-dir D] · store status。
  收據:<receipt 夾>/VQG_Store_latest.json(燈 · 庫位置 · 每表 新增 / 更新 / 跳過 · 分片)。
邊界:同 v0109(只讀 VDF 庫 · 零網路 · 不 import VAP · 不寫 VDF 夾);只寫 TEMP 下自己的 VQG 庫與 VQG 收據;前版被改過 → rc 2。
自測:python VQG_AllInOne_v0110.py selftest(本版 11 項 + v0109 自測於乾淨子行程 · 零網路 · 只在 tempfile 寫)。
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

VERSION_TAIL = "v0110"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VQG_AllInOne_v0109.py"
PRIOR_SHA256 = "dfe6baa1b67b25239a4438d621689e1cba9eda8c0ccfd5b6259f86531a182310"   # v0109(958efbc70 · main)
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(v0110 是 v0109 的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("vqg_v0109_for_v0110", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
V9 = PRIOR
V8 = PRIOR.V8                         # v0108(main 內 export_vap_0108 換裝點)
V7 = PRIOR.V7                         # v0107(via_root · safe_name)
pl = PRIOR.pl

LAKE_NAME = "VIA_ParquetLake_v0101.py"   # 五系統共用增量 Parquet 套件(main 上 · 只增不減);釘名不取尾版
LAKE_SYSTEM = "VQG"
TABLES = (
    # (表, 匯出夾內的檔(glob), 去重鍵, ticker 由檔名來)
    ("series", ("vqg_series.parquet",), ("ticker", "date"), False),
    ("indicators", ("indicators/*.parquet",), ("ticker", "observation_date"), True),
    ("indicator_results", ("vqg_indicator_results.parquet",), ("ticker", "observation_date", "indicator_id", "window_n", "solution_id"), False),
    ("quant_analysis", ("vqg_quant_analysis.parquet",), ("ticker", "observation_date"), False),
    ("backtest_curve", ("backtest/*.parquet",), ("ticker", "date"), True),
    ("backtest_summary", ("backtest/vqg_backtest_summary.parquet",), ("ticker", "strategy"), False),
    ("factor_ic", ("factor/vqg_factor_ic.parquet",), ("date",), False),
    ("stats", ("stats/vqg_stats.parquet",), ("ticker",), False),
    ("return_corr", ("stats/vqg_return_corr.parquet",), ("ticker",), False),
)
VOLATILE = frozenset(("as_of", "request_key", "input_sha256", "engine_version", "engine", "formula_engine", "link_id", "source_files"))
ROW_SHA = "vqg_row_sha"             # 共用套件會拿掉欄名開頭的底線 → 中繼欄不用底線開頭
EXPORT_COL = "vqg_export"

_NO_STORE = False
_STORE_ROOT_ARG = None


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def temp_root() -> tuple:
    """TEMP 根:VIA_TEMP_ROOT > Windows %LOCALAPPDATA%\\VIA_TEMP(不在 OneDrive)> 系統 temp/VIA_TEMP(和 VDF ActivateVDF 同一條規則)。"""
    env = os.environ.get("VIA_TEMP_ROOT")
    if env:
        return Path(env), "VIA_TEMP_ROOT"
    la = os.environ.get("LOCALAPPDATA")
    if os.name == "nt" and la:
        return Path(la) / "VIA_TEMP", "%LOCALAPPDATA%\\VIA_TEMP"
    return Path(tempfile.gettempdir()) / "VIA_TEMP", "系統 temp/VIA_TEMP"


def store_root(arg=None) -> tuple:
    """庫根:--store-root > VIA_VQG_STORE_ROOT > <TEMP 根>/VIA_Lake。VQG 只寫 <庫根>/VQG/。"""
    if arg:
        return Path(arg), "--store-root"
    env = os.environ.get("VIA_VQG_STORE_ROOT")
    if env:
        return Path(env), "VIA_VQG_STORE_ROOT"
    root, how = temp_root()
    return root / "VIA_Lake", how + "/VIA_Lake"


def lake_module():
    """往上找 supportive modules/VIA_ParquetLake_v0101.py;找不到 → (None, None)(入庫黃燈照實說,匯出不受影響)。"""
    p = HERE
    while p.parent != p:
        cand = p / "supportive modules" / LAKE_NAME
        if cand.is_file():
            name = "via_parquetlake_for_vqg_v0110"
            if name in sys.modules:
                return sys.modules[name], cand
            spec = importlib.util.spec_from_file_location(name, cand)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod, cand
        p = p.parent
    return None, None


def _norm(v):
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _row_sha(row: dict) -> str:
    body = {k: v for k, v in row.items() if k not in VOLATILE and k not in (ROW_SHA, EXPORT_COL) and not k.startswith("_")}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:24]


def _key(row: dict, keys) -> tuple:
    return tuple(None if row.get(k) is None else str(row.get(k)) for k in keys)


def _files(export_dir: Path, pats) -> list:
    out = []
    for pat in pats:
        for p in sorted(export_dir.glob(pat)):
            if p.is_file() and not (("*" in pat) and p.stem.startswith("vqg_")):
                out.append(p)
    return out


def table_rows(export_dir: Path, table: str) -> list:
    """匯出夾 → 一張表的列(日期轉 ISO 字串 · NaN → None · 檔名帶票時補 ticker · 加 vqg_export 與 vqg_row_sha)。"""
    spec = next(t for t in TABLES if t[0] == table)
    _, pats, _keys, from_stem = spec
    tickers = {}
    sp = export_dir / "vqg_series.parquet"
    if from_stem and sp.is_file():
        for t in pl.read_parquet(sp, columns=["ticker"])["ticker"].unique().to_list():
            tickers[V7.safe_name(t)] = t
    rows = []
    for p in _files(export_dir, pats):
        for r in pl.read_parquet(p).to_dicts():
            r = {k: _norm(v) for k, v in r.items()}
            if from_stem and "ticker" not in r:
                r = {"ticker": tickers.get(p.stem, p.stem), **r}
            r[EXPORT_COL] = export_dir.name
            r[ROW_SHA] = _row_sha(r)
            rows.append(r)
    return rows


def _current(lake_home: Path, table: str, keys) -> dict:
    """庫裡每個鍵目前(最新)版本的 _row_sha。"""
    tdir = lake_home / table
    if not tdir.is_dir() or not any(tdir.glob("part-*.parquet")):
        return {}
    import duckdb
    g = str(tdir / "part-*.parquet").replace("'", "''")
    sel = ", ".join('"%s"' % k for k in keys)
    con = duckdb.connect()
    try:
        got = con.execute("select %s, \"%s\" from (select %s, \"%s\", row_number() over (partition by %s order by _ingested_at desc, filename desc) as _rn "
                          "from read_parquet('%s', union_by_name=true, filename=true)) where _rn = 1" % (sel, ROW_SHA, sel, ROW_SHA, sel, g)).fetchall()
    finally:
        con.close()
    return {tuple(None if x is None else str(x) for x in r[:-1]): r[-1] for r in got}


def store(export_dir: Path, root_arg=None, receipt_dir: Path | None = None) -> dict:
    """匯出夾 → TEMP 下 VQG 增量庫。只增:新鍵新增 · 值變追加新版本 · 同值跳過;不刪任何分片或列。"""
    export_dir = Path(export_dir)
    root, how = store_root(root_arg)
    rec = {"engine": "VQG " + VERSION_TAIL, "at": _now(), "export_dir": str(export_dir), "store_root": str(root), "store_root_from": how,
           "home": str(root / LAKE_SYSTEM), "lake_module": None, "tables": {}, "lamp": "GREEN", "meaning": "", "delete_policy": "不刪(刪除機制未定 · 維持現況)"}
    mod, mp = lake_module()
    if mod is None:
        rec.update(lamp="YELLOW", meaning="找不到共用套件 supportive modules/%s → 本輪沒入庫(匯出照常)" % LAKE_NAME)
        return _write_store_receipt(rec, receipt_dir)
    rec["lake_module"] = "%s · sha256 %s" % (mp.name, hashlib.sha256(mp.read_bytes()).hexdigest()[:16])
    if not export_dir.is_dir():
        rec.update(lamp="RED", meaning="匯出夾不存在:%s" % export_dir)
        return _write_store_receipt(rec, receipt_dir)
    try:
        lake = mod.Lake(root, LAKE_SYSTEM)
        totals = {"rows_in": 0, "added_new": 0, "updated": 0, "unchanged": 0}
        for table, _pats, keys, _fs in TABLES:
            rows = table_rows(export_dir, table)
            if not rows:
                rec["tables"][table] = {"rows_in": 0, "note": "本輪匯出沒有這張表"}
                continue
            batch = {}
            for r in rows:
                batch[_key(r, keys)] = r                     # 同一份匯出裡重複鍵 → 留最後一列
            cur = _current(lake.home, table, keys)
            new = [r for k, r in batch.items() if k not in cur]
            upd = [r for k, r in batch.items() if k in cur and cur[k] != r[ROW_SHA]]
            same = len(batch) - len(new) - len(upd)
            res = lake.append(table, new + upd, keys=list(keys), dedupe=False) if (new or upd) else {"file": None}
            rec["tables"][table] = {"rows_in": len(rows), "dup_in_export": len(rows) - len(batch), "added_new": len(new), "updated": len(upd), "unchanged": same,
                                    "keys": list(keys), "file": res.get("file")}
            for k in totals:
                totals[k] += rec["tables"][table].get(k, 0)
        lake.append("store_runs", [{"run_at": rec["at"], "export": export_dir.name, "engine": rec["engine"], **totals,
                                    "tables": json.dumps({t: {k: v for k, v in d.items() if k in totals} for t, d in rec["tables"].items()}, ensure_ascii=False)}],
                    keys=["run_at"], dedupe=False)
        rec["totals"] = totals
        rec["meaning"] = "入庫 %d 表 · 新增 %d · 更新(新版本)%d · 未變跳過 %d · 不刪" % (sum(1 for d in rec["tables"].values() if d.get("rows_in")), totals["added_new"], totals["updated"], totals["unchanged"])
    except Exception as error:  # noqa: BLE001 — 入庫壞了照實紅,不吞
        rec.update(lamp="RED", meaning="入庫中斷 · %s: %s" % (type(error).__name__, str(error)[:200]))
    return _write_store_receipt(rec, receipt_dir)


def _write_store_receipt(rec: dict, receipt_dir: Path | None) -> dict:
    if receipt_dir is not None:
        try:
            Path(receipt_dir).mkdir(parents=True, exist_ok=True)
            (Path(receipt_dir) / "VQG_Store_latest.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
            rec["receipt"] = str(Path(receipt_dir) / "VQG_Store_latest.json")
        except OSError as error:
            rec["receipt_error"] = str(error)[:160]
    return rec


def store_status(root_arg=None) -> dict:
    root, how = store_root(root_arg)
    mod, _ = lake_module()
    if mod is None:
        return {"lamp": "YELLOW", "meaning": "找不到 %s" % LAKE_NAME, "store_root": str(root), "store_root_from": how}
    st = mod.Lake(root, LAKE_SYSTEM).status()
    st.update(store_root=str(root), store_root_from=how, lamp="GREEN" if st.get("exists") else "GRAY")
    return st


def export_vap_0110(args) -> int:
    rc = V9.export_vap_0109(args)
    if rc != 0 or _NO_STORE:
        if _NO_STORE and rc == 0:
            print("[INFO] VQG %s 入庫略過(--no-store)" % VERSION_TAIL, flush=True)
        return rc
    via = V7.via_root(getattr(args, "via_root", None))
    out_root = Path(getattr(args, "out_dir", None) or ((via / "VIA_Reports" / "vqg" / "vap_export") if via else Path.cwd() / "VIA_Reports" / "vqg" / "vap_export"))
    receipt_dir = Path(getattr(args, "receipt_dir", None) or ((via / "VIA_Reports" / "vqg") if via else Path.cwd() / "VIA_Reports" / "vqg"))
    try:
        final = Path(json.loads((out_root / "latest.json").read_text(encoding="utf-8"))["export_dir"])
    except (OSError, ValueError, KeyError) as error:
        print("[YELLOW] VQG %s 入庫略過 · 讀不到 latest.json(%s)" % (VERSION_TAIL, str(error)[:120]), flush=True)
        return rc
    s = store(final, _STORE_ROOT_ARG, receipt_dir)
    print("[%s] VQG %s TEMP 增量庫 · %s → %s" % (s["lamp"], VERSION_TAIL, s["meaning"], s["home"]), flush=True)
    return rc


def split_store_flags(argv: list) -> tuple:
    """拿掉本版旗標(--no-store · --store-root X),其餘原樣交給前版 argparse。"""
    argv = list(argv)
    no_store = "--no-store" in argv
    argv = [a for a in argv if a != "--no-store"]
    root = None
    if "--store-root" in argv:
        i = argv.index("--store-root")
        root = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
    return argv, no_store, root


def _bars(ticker, start, n, base, drift, seed):
    return V9._bars_varied(ticker, start, n, base, drift, seed)


def selftest() -> int:
    global LAKE_NAME
    ok = total = 0

    def chk(label, cond, note=""):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", label, (" · " + str(note)) if note else ""), flush=True)
    print("[VQG %s selftest]" % VERSION_TAIL, flush=True)
    cp = subprocess.run([sys.executable, str(PRIOR_PATH), "selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=1700, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    prior_lines = [l for l in (cp.stdout or "").splitlines() if l.strip().startswith(("[PASS]", "[FAIL]", "[VQG"))]
    prior_ok = cp.returncode == 0
    mod, mp = lake_module()
    chk("① 前版 v0109 SHA-256 釘住 · 共用套件 %s 找得到(main 上 · 只增不減)" % LAKE_NAME, PRIOR_SHA_OK and mod is not None, mp.name if mp else "缺")
    saved = {k: os.environ.pop(k, None) for k in ("VIA_TEMP_ROOT", "VIA_VQG_STORE_ROOT", "VQG_VDF_ROOT")}
    try:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            os.environ["VIA_TEMP_ROOT"] = str(t / "tmproot")
            r1, h1 = store_root()
            os.environ["VIA_VQG_STORE_ROOT"] = str(t / "override")
            r2, h2 = store_root()
            r3, h3 = store_root(str(t / "arg"))
            os.environ.pop("VIA_VQG_STORE_ROOT")
            os.environ.pop("VIA_TEMP_ROOT")
            r4, _h4 = store_root()
            want4 = (Path(os.environ["LOCALAPPDATA"]) / "VIA_TEMP" / "VIA_Lake") if (os.name == "nt" and os.environ.get("LOCALAPPDATA")) else (Path(tempfile.gettempdir()) / "VIA_TEMP" / "VIA_Lake")
            chk("② 庫根:VIA_TEMP_ROOT/VIA_Lake · VIA_VQG_STORE_ROOT 優先 · --store-root 最優先 · 都沒設 = 系統 TEMP 規則(同 VDF ActivateVDF)",
                r1 == t / "tmproot" / "VIA_Lake" and h1.startswith("VIA_TEMP_ROOT") and r2 == t / "override" and r3 == t / "arg" and h3 == "--store-root" and r4 == want4, str(r4))
            a, ns_, rt = split_store_flags(["export-vap", "--no-store", "--store-root", "X", "--max-tickers", "3"])
            chk("③ 旗標:--no-store / --store-root 由本版拿掉,其餘原樣交前版", a == ["export-vap", "--max-tickers", "3"] and ns_ is True and rt == "X")
            os.environ["VIA_TEMP_ROOT"] = str(t / "tmproot")
            vdf = t / "vdf_database"
            (vdf / "output_hub").mkdir(parents=True)
            d0 = date(2025, 9, 1)
            rows = []
            for tk, base, drift, seed in (("2330.TW", 100.0, 0.0008, 7), ("2317.TW", 80.0, -0.0003, 11), ("2454.TW", 60.0, 0.0012, 13)):
                rows += _bars(tk, d0, 300, base, drift, seed)
            V9.V5._vdf_like(vdf / "output_hub" / "tw_daily_prices_20261101_120000.parquet", rows)
            out = t / "out"
            rcpt = t / "rcpt"
            ns = types.SimpleNamespace(via_root=None, root=str(vdf), out_dir=str(out), receipt_dir=str(rcpt), ticker=[], max_tickers=50, metrics=None, windows=None,
                                       as_of=d0 + timedelta(days=320), series_rows=0, indicator_points=120, calendar="auto", snapshots="latest", market=None, vap_port=8765)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
                rc = export_vap_0110(ns)
            ed = Path(json.loads((out / "latest.json").read_text(encoding="utf-8"))["export_dir"]) if (out / "latest.json").is_file() else None
            s1 = json.loads((rcpt / "VQG_Store_latest.json").read_text(encoding="utf-8")) if (rcpt / "VQG_Store_latest.json").is_file() else {}
            home = t / "tmproot" / "VIA_Lake" / "VQG"
            tabs = s1.get("tables", {})
            chk("④ export-vap(v0109 原樣)→ 自動入 TEMP 庫:rc 0 · 燈 GREEN · 九表都有新增 · 庫在 <VIA_TEMP_ROOT>/VIA_Lake/VQG · 管家 VQG_catalog.duckdb",
                rc == 0 and s1.get("lamp") == "GREEN" and all(tabs.get(n, {}).get("added_new", 0) > 0 for n, *_ in TABLES) and Path(s1.get("home", "")) == home
                and (home / "VQG_catalog.duckdb").is_file(), s1.get("meaning"))
            parts1 = sorted(str(p) for p in home.rglob("part-*.parquet"))
            s2 = store(ed, None, rcpt)
            chk("⑤ 同一份匯出再入庫 = 0 新增 · 0 更新 · 全部未變跳過(去重 · 冪等)· 只多 store_runs 一列",
                s2["lamp"] == "GREEN" and s2["totals"]["added_new"] == 0 and s2["totals"]["updated"] == 0 and s2["totals"]["unchanged"] == s1["totals"]["added_new"], s2["meaning"])
            ed2 = t / ed.name.replace("vap_export_", "vap_export_mod_")
            shutil.copytree(ed, ed2)
            qa = pl.read_parquet(ed2 / "vqg_quant_analysis.parquet")
            tk0 = qa["ticker"][0]
            qa = qa.with_columns(pl.when(pl.col("ticker") == tk0).then(pl.lit(99.5)).otherwise(pl.col("rsi_14")).alias("rsi_14"))
            qa.write_parquet(ed2 / "vqg_quant_analysis.parquet")
            se = pl.read_parquet(ed2 / "vqg_series.parquet")
            tks = se["ticker"][0]                                            # 序列表自己的票號(量化表的票號寫法可能不同)
            last = se.filter(pl.col("ticker") == tks).sort("date").tail(1)
            se = pl.concat([se, last.with_columns((pl.col("date") + timedelta(days=1)).alias("date"))], how="vertical_relaxed")
            se.write_parquet(ed2 / "vqg_series.parquet")
            ir = pl.read_parquet(ed2 / "vqg_indicator_results.parquet")
            ir = ir.with_columns(pl.lit("v9999+test").alias("engine_version"), pl.lit("0" * 64).alias("input_sha256"), (pl.col("as_of") + timedelta(days=3)).alias("as_of"))
            ir.write_parquet(ed2 / "vqg_indicator_results.parquet")
            s3 = store(ed2, None, rcpt)
            t3 = s3.get("tables", {})
            chk("⑥ 增量更新:值變 1 列 → quant_analysis 追加新版本 1 · 其餘未變;series 多 1 天 → 新增 1",
                t3.get("quant_analysis", {}).get("updated") == 1 and t3.get("quant_analysis", {}).get("added_new") == 0
                and t3.get("series", {}).get("added_new") == 1 and t3.get("series", {}).get("updated") == 0, json.dumps({k: {kk: t3.get(k, {}).get(kk) for kk in ("rows_in", "dup_in_export", "added_new", "updated", "unchanged")} for k in ("quant_analysis", "series")}, ensure_ascii=False))
            chk("⑦ 每輪會變的欄(as_of · engine_version · input_sha256)不算更新:indicator_results 全部未變",
                t3.get("indicator_results", {}).get("updated") == 0 and t3.get("indicator_results", {}).get("added_new") == 0
                and t3.get("indicator_results", {}).get("unchanged") == tabs.get("indicator_results", {}).get("added_new"))
            import duckdb
            con = duckdb.connect(str(home / "VQG_catalog.duckdb"), read_only=True)
            try:
                v_rsi = con.execute("select rsi_14 from v_quant_analysis where ticker = ?", [tk0]).fetchone()
                n_view = con.execute("select count(*) from v_quant_analysis").fetchone()[0]
            finally:
                con.close()
            st = store_status()
            qrow = next((x for x in st.get("tables", []) if x.get("table") == "quant_analysis"), {})
            chk("⑧ VIEW v_quant_analysis 取最新版本(rsi_14 = 99.5)· 列數 = 鍵數 · 原始列 = 鍵數 + 1(舊版本留著)",
                v_rsi and abs(float(v_rsi[0]) - 99.5) < 1e-9 and n_view == qa.height and qrow.get("rows_raw") == qa.height + 1 and qrow.get("rows_view") == qa.height, qrow)
            parts3 = sorted(str(p) for p in home.rglob("part-*.parquet"))
            chk("⑨ 不刪:第一輪的分片全部還在 · 分片數只增不減 · _manifest.jsonl 只增",
                set(parts1) <= set(parts3) and len(parts3) > len(parts1) and (home / "_manifest.jsonl").is_file())
            src = Path(__file__).read_text(encoding="utf-8")
            tree = ast.parse(src)
            fn_names = ("store", "table_rows", "_current", "_write_store_receipt", "store_status", "export_vap_0110")
            calls = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name in fn_names:
                    for sub in ast.walk(node):
                        if isinstance(sub, ast.Call):
                            f = sub.func
                            calls.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
            chk("⑩ 入庫程式碼沒有刪除呼叫(unlink / rmtree / remove / rmdir / delete)", not (calls & {"unlink", "rmtree", "remove", "rmdir", "delete"}), sorted(calls & {"unlink", "rmtree", "remove", "rmdir"}))
            keep = LAKE_NAME
            LAKE_NAME = "VIA_ParquetLake_v9999_missing.py"
            try:
                s4 = store(ed, str(t / "nolake"), None)
            finally:
                LAKE_NAME = keep
            chk("⑪ 共用套件不在 → 入庫黃燈照實說 · 不建庫 · 匯出不受影響", s4["lamp"] == "YELLOW" and not (t / "nolake").exists(), s4["meaning"])
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
    for line in prior_lines[-3:]:
        print("    前版 " + line.strip()[:200], flush=True)
    ok_all = ok == total and prior_ok
    print("[%s] VQG %s selftest · 本版 %d/%d · 前版鏈 v0109 %s" % ("PASS" if ok_all else "FAIL", VERSION_TAIL, ok, total, "PASS" if prior_ok else "FAIL(rc %s)" % cp.returncode), flush=True)
    return 0 if ok_all else 1


def main(argv=None) -> int:
    global _NO_STORE, _STORE_ROOT_ARG
    argv, _NO_STORE, _STORE_ROOT_ARG = split_store_flags(list(sys.argv[1:] if argv is None else argv))
    cmd = next((a for a in argv if not a.startswith("-")), "scan")
    if cmd in ("selftest", "test") or "--selftest" in argv:
        try:
            return selftest()
        except Exception as error:  # noqa: BLE001
            print("[FAIL] VQG %s selftest 中斷 · %s: %s" % (VERSION_TAIL, type(error).__name__, str(error)[:200]), flush=True)
            return 1
    if not PRIOR_SHA_OK:
        print("[RED] VQG %s 前版 %s 被改過(SHA-256 不符)· 停" % (VERSION_TAIL, PRIOR_NAME), flush=True)
        return 2
    if cmd == "store":
        if "status" in argv:
            st = store_status(_STORE_ROOT_ARG)
            print(json.dumps(st, ensure_ascii=False, indent=1, default=str), flush=True)
            return 0 if st.get("lamp") in ("GREEN", "GRAY") else 2
        ed = next((argv[i + 1] for i, a in enumerate(argv) if a == "--export-dir" and i + 1 < len(argv)), None)
        via = V7.via_root(None)
        out_root = (via / "VIA_Reports" / "vqg" / "vap_export") if via else Path.cwd() / "VIA_Reports" / "vqg" / "vap_export"
        if not ed and (out_root / "latest.json").is_file():
            ed = json.loads((out_root / "latest.json").read_text(encoding="utf-8")).get("export_dir")
        if not ed or not Path(ed).is_dir():
            print("[RED] VQG %s store · 找不到匯出夾(--export-dir 或 %s)" % (VERSION_TAIL, out_root / "latest.json"), flush=True)
            return 2
        s = store(Path(ed), _STORE_ROOT_ARG, (via / "VIA_Reports" / "vqg") if via else None)
        print("[%s] VQG %s TEMP 增量庫 · %s → %s" % (s["lamp"], VERSION_TAIL, s["meaning"], s["home"]), flush=True)
        return 0 if s["lamp"] == "GREEN" else (1 if s["lamp"] == "YELLOW" else 2)
    if cmd == "export-vap":
        _orig = V8.export_vap_0108
        V8.export_vap_0108 = export_vap_0110                                 # v0108 main 換裝點 → 本版(v0109 匯出 + 量化分析 → 入庫)
        try:
            return V8.main(argv)
        finally:
            V8.export_vap_0108 = _orig
    if "--help" in argv or "-h" in argv:
        rc = V9.main(argv)
        print("v0110:export-vap 跑完自動入 TEMP 增量庫(--no-store 不入 · --store-root 換位置)· store [--export-dir D] · store status", flush=True)
        return rc
    return V9.main(argv)


if __name__ == "__main__":
    sys.exit(main())
