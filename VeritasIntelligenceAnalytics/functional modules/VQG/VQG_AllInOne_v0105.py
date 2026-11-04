#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VeritaQuantGuard(VQG)v0105 — v0104 薄尾(v0104 一字不改 · SHA-256 釘在 PRIOR_SHA256)。

VQG 是獨立系統(操作員 2026-11-04:「VQG 輸入來自 VDF 生成的資料庫 · 為獨立系統」):
  · 只讀 VDF 的資料庫(VDF 的冊 VDF_DataHome_SSOT 寫的 db_home · 預設照它找)· 不寫 VDF 的夾 · 不改 VDF 的檔 · 不連網。
  · 自己的收據寫在 <VIA 根>\VIA_Reports\vqg\VQG_Closeout_latest.json(別的系統只讀這份)。
  · 技術指標唯一正主 = QuantGuard(政策 L50 · 不用 TA-Lib)· 公式 / 三解 / 驗證全照 v0104(calculate · validate_frame 不動)。

為什麼要 v0105(拿 VDF 形狀的資料實測 v0104 · 2026-11-04):
  ① VDF 的日線檔(ENG054 tw_daily_prices_<時間>.parquet · CentralHub *_latest_<時間>.parquet)欄位是
     date · ticker · open … close · adj_close · volume —— 沒有 market、session_index(交易日序號)、available_on(可用日);
     VDF 引擎也沒有任何一支寫交易日曆(只有 ENG086 這座橋自己要)。v0104 嚴格模式因此:
       台股 → NEED_VDF_CALENDAR_OR_AVAILABILITY;美股 → MARKET_UNRESOLVED: NONE(還是原始 traceback)。
  ② VDF 每輪擷取寫一個新批次檔;還原價(adj_close)會隨除權息重算 → 同一天在新舊批次值不同 → v0104 照設計 CONFLICT 拒算。

v0105 做法(預設照 v0104 嚴格 · 新行為都要明講才開 · 結果都帶標記):
  · --calendar vdf(預設 · 嚴格 = v0104)| derive | auto(先嚴格 · 只因缺曆 / 缺市場才改 derive)。
    derive:交易日序號 = 同市場在 VDF 日線出現過的日期聯集排序(VDF 自己的交易日 · 不猜假日表);
            該檔沒有價的交易日插明確的空列(v0104 要求「OMITTED_SESSION_INSERT_EXPLICIT_NULL_UPSTREAM」);
            可用日缺 → = 該日(日線收盤後可用 · EOD_SAME_DAY · 台股仍照 v0104 只用 as-of 前一日以前);
            市場欄缺 → 台股代號(.TW / .TWO / 4–6 碼 / ^TWII ^TWOII)= TW · 其他英文代號 = US(或 --market 指定)。
            每列 engine_version = "v0104+derived_calendar" · 統計帶 calendar 段 · 快取另放 derived_calendar 子夾(不跟嚴格結果混)。
  · --snapshots strict(預設 = v0104 衝突拒算)| latest(同一張表的時間戳批次檔只取最新一份 · 被取代的檔列在統計)。
  · doctor:VDF 庫對 VQG 合約的就緒檢查(只讀)· closeout:自測 + doctor + 探針計算 → 收據(GREEN / YELLOW / RED / GRAY)。
  · 已知錯誤一律一行紅字 + 下一步(不吐 traceback)· rc 2。
自測:python VQG_AllInOne_v0105.py selftest(v0104 自測 + 本版 10 項 · 零網路 · 只在 tempfile 沙盒寫)。
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import types
from datetime import date, datetime, timedelta
from pathlib import Path

VERSION_TAIL = "v0105"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VQG_AllInOne_v0104.py"
PRIOR_SHA256 = "d2a5ca07fa4d29435584c111095a31951075ab585b51cc74b14b22ef48ca1d02"   # 操作員 2026-11-04 上傳原檔
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(v0105 是 v0104 的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
_spec = importlib.util.spec_from_file_location("vqg_v0104_for_v0105", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
pl = PRIOR.pl
ENGINE_VERSION = PRIOR.VERSION                                          # 公式引擎 = v0104(calculate 不動)
DERIVED_TAG = ENGINE_VERSION + "+derived_calendar"


def __getattr__(name):
    return getattr(PRIOR, name)


# ── 市場 / 交易日 ─────────────────────────────────────────────────────────
_TW_TICKER = re.compile(r"^(\d{4,6}[A-Z]?(\.TWO?)?|\^TWII|\^TWOII|TAIEX|TPEX)$")
_US_TICKER = re.compile(r"^(\^[A-Z0-9]{2,8}|[A-Z][A-Z0-9\-]{0,9}(\.[A-Z])?)$")
_MARKET_WORDS = {"TW": "TW", "TWSE": "TW", "TPEX": "TW", "TWO": "TW", "上市": "TW", "上櫃": "TW", "US": "US", "NYSE": "US", "NASDAQ": "US"}
_SNAP = re.compile(r"^(.*?)_{1,2}(\d{8}_\d{6})$")
_CALENDAR_STEM = re.compile(r"calendar|trading_sessions|交易(日曆|曆)", re.I)
_CTX = {"calendar": "vdf", "snapshots": "strict", "market": None, "stats": None}


def infer_market(symbol: str, forced=None) -> tuple:
    """(市場, 依據)。只支援 v0104 認的 TW / US;認不出 → ValueError MARKET_UNRESOLVED(乾淨的錯)。"""
    if forced:
        return PRIOR.market_code(forced), "--market"
    s = str(symbol or "").strip().upper()
    if _TW_TICKER.match(s):
        return "TW", "台股代號樣式"
    if _US_TICKER.match(s):
        return "US", "非台股英文代號 → US(VDF 只抓 TW / US · R-ADJ-03)"
    raise ValueError("MARKET_UNRESOLVED: %s(加 --market TW|US)" % symbol)


def _market_of_ticker(t: str):
    s = str(t or "").strip().upper()
    if _TW_TICKER.match(s):
        return "TW"
    if _US_TICKER.match(s):
        return "US"
    return None


def _daily_price_sources(sources):
    out = []
    for path, cols in sources:
        if "report_id" in cols and "report_date" in cols:
            continue
        if "monthly_revenue" in cols or _CALENDAR_STEM.search(path.stem):
            continue
        if {"date", "ticker", "adj_close"} <= cols.keys():
            out.append((path, cols))
    return out


def market_sessions(sources, market: str, as_of, start=None) -> list:
    """同市場在 VDF 日線出現過的日期聯集(≤ as-of · ≥ start)· 排序 · 這就是 derive 的交易日曆(VDF 自己的資料 · 不另猜假日)。"""
    days = set()
    for path, cols in _daily_price_sources(sources):
        dt = PRIOR.date_expr(cols["date"])
        q = pl.scan_parquet(path)
        if "market" in cols:
            m = pl.col(cols["market"]).cast(pl.String).str.to_uppercase().replace_strict(_MARKET_WORDS, default=None)
            q = q.filter(m == market)
            frame = q.select(dt.alias("d")).filter(pl.col("d") <= as_of)
            if start:
                frame = frame.filter(pl.col("d") >= start)
            days.update(frame.unique().collect()["d"].drop_nulls().to_list())
            continue
        frame = q.select(dt.alias("d"), pl.col(cols["ticker"]).cast(pl.String).str.to_uppercase().alias("t")).filter(pl.col("d") <= as_of)
        if start:
            frame = frame.filter(pl.col("d") >= start)
        part = frame.unique().collect()
        days.update(d for d, t in part.iter_rows() if d is not None and _market_of_ticker(t) == market)
    return sorted(days)


def snapshot_family(path: Path):
    m = _SNAP.match(path.stem)
    return ((str(path.parent), m.group(1)), m.group(2)) if m else ((str(path.parent), path.stem), "")


def latest_snapshots(sources) -> tuple:
    """同一張表(同夾 · 同檔名前綴 · 尾巴是 _YYYYmmdd_HHMMSS)只留時間最新的一份;回 (留下, 被取代)。"""
    best, dropped = {}, []
    for path, cols in sources:
        fam, ts = snapshot_family(path)
        key = (ts, path.stat().st_mtime)
        if fam in best and best[fam][0] >= key:
            dropped.append(path)
            continue
        if fam in best:
            dropped.append(best[fam][1][0])
        best[fam] = (key, (path, cols))
    kept = [v[1] for v in best.values()]
    order = {str(p): i for i, (p, _) in enumerate(sources)}
    kept.sort(key=lambda pc: order[str(pc[0])])
    return kept, sorted(str(p) for p in dropped)


_ORIG_LOAD_SERIES = PRIOR.load_series
_ORIG_RUN_LOCAL = PRIOR.run_local


def load_series(sources, symbol, fields, as_of, start=None, kind="daily", available_cutoff=True, tail_rows=None):
    """v0105:--snapshots latest → 同表只用最新批次;--calendar derive → 補 market / session_index / available_on + 缺的交易日插空列。其他 = v0104。"""
    st = _CTX.get("stats")
    if _CTX.get("snapshots") == "latest":
        sources, dropped = latest_snapshots(sources)
        if st is not None and dropped:
            st["superseded_snapshots"] = sorted(set(st.get("superseded_snapshots", []) + dropped))
    records = _ORIG_LOAD_SERIES(sources, symbol, fields, as_of, start, kind, available_cutoff, tail_rows)
    if _CTX.get("calendar") != "derive" or kind != "daily" or "session_index" not in fields or not records:
        return records
    market = next((r.get("market") for r in records if r.get("market") is not None), None)
    if market is not None:
        market, how = PRIOR.market_code(market), "VDF 檔的 market 欄"
    else:
        market, how = infer_market(symbol, _CTX.get("market"))
    have_idx = all("session_index" in r for r in records)
    cal = market_sessions(sources, market, as_of, start)
    pos = {d: i + 1 for i, d in enumerate(cal)}
    inserted = filled_avail = 0
    if not have_idx:
        first = records[0]["date"]                                       # 上市前不插;停牌 / 到 as-of 為止沒價的交易日都插空列(= 上游明寫空列)
        known = {r["date"] for r in records}
        for d in cal:
            if d >= first and d not in known:
                records.append({"date": d, "adj_close": None})
                inserted += 1
        records.sort(key=lambda r: r["date"])
        if tail_rows is not None:
            records = records[-tail_rows:]                               # 跟 v0104 讀明寫空列的來源一樣:最後 tail_rows 個交易日
        for r in records:
            if r["date"] not in pos:
                raise ValueError("DERIVED_CALENDAR_MISS: %s %s 不在同市場 VDF 日線日期裡" % (symbol, r["date"]))
            r["session_index"] = pos[r["date"]]
    for r in records:
        r["market"] = market
        if r.get("available_on") is None:
            r["available_on"] = r["date"]
            filled_avail += 1
    if st is not None:
        st["calendar"] = {"mode": "derived", "market": market, "market_source": how, "sessions_in_vdf": len(cal),
                          "session_index": "VDF 原有" if have_idx else "同市場 VDF 日線日期聯集排序",
                          "inserted_null_sessions": inserted, "available_on_filled": filled_avail,
                          "availability_rule": "EOD_SAME_DAY(台股仍只用 as-of 前一日以前 · v0104)", "engine_version": DERIVED_TAG}
    return records


PRIOR.load_series = load_series                                        # run_local / activity / chart 都經這一支


def run_local(sources, args):
    """v0105:--calendar vdf(預設 · = v0104)| derive | auto;--snapshots strict | latest。回 (rows, stats) · stats 多 engine / calendar / snapshots。"""
    mode = getattr(args, "calendar", None) or _CTX.get("default_calendar") or "vdf"
    snaps = getattr(args, "snapshots", None) or _CTX.get("default_snapshots") or "strict"
    forced = getattr(args, "market", None) or _CTX.get("default_market")

    def once(cal):
        a = types.SimpleNamespace(**vars(args))
        stats = {}
        _CTX.update(calendar=cal, snapshots=snaps, market=forced, stats=stats)
        if cal == "derive" and getattr(a, "cache_dir", None):
            a.cache_dir = Path(a.cache_dir) / "derived_calendar"           # 不跟嚴格結果共用快取
        PRIOR.VERSION = DERIVED_TAG if cal == "derive" else ENGINE_VERSION
        try:
            rows, st = _ORIG_RUN_LOCAL(sources, a)
        finally:
            PRIOR.VERSION = ENGINE_VERSION
            _CTX.update(calendar="vdf", snapshots="strict", market=None, stats=None)
        return rows, dict(st, **stats)

    first_error = None
    if mode in ("vdf", "auto"):
        try:
            rows, st = once("vdf")
            st.setdefault("calendar", {"mode": "vdf", "engine_version": ENGINE_VERSION})
            return rows, dict(st, engine="VQG " + VERSION_TAIL, snapshots=snaps)
        except ValueError as error:
            code = str(error)
            if mode == "vdf" or not code.startswith(("NEED_VDF_CALENDAR_OR_AVAILABILITY", "MARKET_UNRESOLVED")):
                raise
            first_error = code
    rows, st = once("derive")
    if first_error:
        st["calendar"]["auto_reason"] = "嚴格先試 → " + first_error[:120]
    return rows, dict(st, engine="VQG " + VERSION_TAIL, snapshots=snaps)


PRIOR.run_local = run_local


# ── VDF 庫的位置(照 VDF 自己的冊)· VIA 根 ─────────────────────────────────
def via_root(explicit=None):
    for c in [explicit, os.environ.get("VIA_ROOT")] + list(HERE.parents) + [Path.home() / "OneDrive" / "Documents" / "movies-dataset" / "VeritasIntelligenceAnalytics"]:
        if c and (Path(c) / "functional modules").is_dir() and (Path(c) / "supportive modules").is_dir():
            return Path(c).resolve()
    return None


def default_root(via=None) -> tuple:
    """(VDF 庫根, 依據):VQG_VDF_ROOT → VDF 的冊 VDF_DataHome_SSOT 尾版 homes 照順序第一個在的 db_home → v0104 預設。"""
    env = os.environ.get("VQG_VDF_ROOT")
    if env:
        return Path(env), "環境變數 VQG_VDF_ROOT"
    via = via if via is not None else via_root()
    if via is not None:
        books = sorted((via / "functional modules" / "VDF").glob("VDF_DataHome_SSOT_v[0-9][0-9][0-9][0-9].json"))
        if books:
            try:
                homes = json.loads(books[-1].read_text(encoding="utf-8")).get("homes") or []
            except (OSError, ValueError):
                homes = []
            for h in homes:
                p = Path(str(h.get("db_home") or ""))
                if str(p) not in ("", ".") and p.is_dir():
                    return p, "VDF 的冊 %s · %s" % (books[-1].name, h.get("id"))
            if homes:
                return Path(str(homes[0].get("db_home"))), "VDF 的冊 %s · %s(這台機器沒有這個夾)" % (books[-1].name, homes[0].get("id"))
    return Path(PRIOR.ROOT), "v0104 預設"


# ── doctor:VDF 庫對 VQG 合約的就緒檢查(只讀)──────────────────────────────
def doctor(root) -> dict:
    root = Path(root)
    if not root.is_dir():
        return {"verdict": "NO_VDF_ROOT", "root": str(root), "why": "VDF 庫根不在這台機器"}
    sources, errors = PRIOR.discover(root)
    files, families = [], {}
    for path, cols in sources:
        if "report_id" in cols and "report_date" in cols:
            kind = "report(VRN)"
        elif "monthly_revenue" in cols:
            kind = "monthly"
        elif _CALENDAR_STEM.search(path.stem) and {"market", "date", "session_index"} <= cols.keys():
            kind = "calendar"
        elif {"date", "ticker", "adj_close"} <= cols.keys():
            kind = "daily_price"
        elif {"date", "ticker"} <= cols.keys():
            kind = "daily_other"
        else:
            kind = "other"
        fam, ts = snapshot_family(path)
        if kind == "daily_price":
            families.setdefault(fam, []).append(ts or "-")
        files.append({"file": str(path.relative_to(root.resolve())), "kind": kind,
                      "has": {k: k in cols for k in ("ticker", "date", "adj_close", "market", "session_index", "available_on", "volume")}})
    daily = [f for f in files if f["kind"] == "daily_price"]
    cal = [f for f in files if f["kind"] == "calendar"]
    missing = sorted({k for f in daily for k in ("market", "session_index", "available_on") if not f["has"][k]} - ({"session_index"} if cal else set()))
    multi = {"%s/%s" % (Path(k[0]).name, k[1]): sorted(v) for k, v in families.items() if len(v) > 1}
    tickers = []
    for f in daily[:3]:
        p = root.resolve() / f["file"]
        col = dict(sources)[p]["ticker"]
        tickers += pl.scan_parquet(p).select(pl.col(col).cast(pl.String)).unique().limit(20).collect().to_series().to_list()
    verdict = "NO_DAILY_PRICES" if not daily else ("STRICT_READY" if not missing else "DERIVE_READY")
    return {"verdict": verdict, "root": str(root), "files": len(files), "daily_price_files": len(daily), "calendar_files": len(cal),
            "missing_for_strict": missing, "multi_snapshot_tables": multi, "unreadable": errors[:20], "tickers_sample": sorted(set(tickers))[:20],
            "next": {"STRICT_READY": "嚴格模式可直接算(--calendar vdf)",
                     "DERIVE_READY": "VDF 檔缺 %s → 用 --calendar derive(或 auto)· 要嚴格綠 = VDF 那側出 session_index / available_on / market" % "、".join(missing),
                     "NO_DAILY_PRICES": "VDF 庫裡沒有 ticker + date + adj_close 的日線 parquet → 先讓 VDF 擷取日線"}[verdict]
                    + (" · 同一張表有多個批次:%d 張 → 值不同時加 --snapshots latest" % len(multi) if multi else "")}


# ── closeout:自測 + doctor + 探針計算 → VQG 自己的收據 ────────────────────────
def _probe_ticker(root, sources):
    seen = []
    for path, cols in _daily_price_sources(sources)[:4]:
        seen += pl.scan_parquet(path).select(pl.col(cols["ticker"]).cast(pl.String)).unique().limit(400).collect().to_series().to_list()
    up = {str(t).upper() for t in seen if t}
    for want, sym in (("2330.TW", "2330.TW"), ("2330", "2330.TW")):
        if want in up:
            return sym
    tw = sorted(t for t in up if _market_of_ticker(t) == "TW" and not t.startswith("^"))
    if tw:
        return tw[0] if "." in tw[0] else tw[0] + ".TW"
    return sorted(up)[0] if up else None


def closeout(args) -> int:
    t0 = datetime.now()
    via = via_root(getattr(args, "via_root", None))
    root, how = (Path(args.root), "--root") if getattr(args, "root_given", False) else default_root(via)
    out_dir = Path(getattr(args, "out_dir", None) or ((via / "VIA_Reports" / "vqg") if via else Path.cwd() / "VIA_Reports" / "vqg"))
    if root.is_dir() and out_dir.resolve().is_relative_to(root.resolve()):
        print("[RED] VQG 收據夾在 VDF 庫裡面(%s)· VQG 只讀 VDF · 不寫" % out_dir, flush=True)
        return 2
    rec = {"system": "VQG", "engine": "VeritaQuantGuard " + VERSION_TAIL, "formula_engine": ENGINE_VERSION, "at": t0.isoformat(timespec="seconds"),
           "via_root": str(via or ""), "vdf_root": str(root), "vdf_root_from": how, "rule": "VQG 只讀 VDF 庫 · 不連網 · 不寫 VDF 的夾 · 四 / 五系統對等(只讀互看)", "steps": []}

    def step(name, lamp, detail):
        rec["steps"].append({"step": name, "lamp": lamp, "detail": detail})
        print("[%s] %s · %s" % (lamp, name, detail), flush=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc_self = selftest()
        except Exception as error:  # noqa: BLE001
            rc_self = 1
            print("selftest %s: %s" % (type(error).__name__, error))
    tail = [l for l in buf.getvalue().splitlines() if l.strip()]
    step("① 自測", "GREEN" if rc_self == 0 else "RED", tail[-1][:160] if tail else "—")
    doc = doctor(root)
    rec["doctor"] = doc
    lampd = {"STRICT_READY": "GREEN", "DERIVE_READY": "YELLOW", "NO_DAILY_PRICES": "RED", "NO_VDF_ROOT": "GRAY"}[doc["verdict"]]
    step("② VDF 庫就緒(%s)" % how, lampd, "%s · %s · 日線檔 %s · %s" % (doc["verdict"], doc["root"], doc.get("daily_price_files", 0), doc.get("next") or doc.get("why")))
    calc_lamp = "GRAY"
    if doc["verdict"] in ("STRICT_READY", "DERIVE_READY"):
        sources, _ = PRIOR.discover(root)
        ticker = getattr(args, "ticker", None) or _probe_ticker(root, sources)
        a = types.SimpleNamespace(root=root, ticker=ticker, metrics=["sma", "rsi", "macd"], windows=None, as_of=getattr(args, "as_of", None) or date.today(),
                                  start=None, report_id=None, cache_dir=None, calendar="auto", snapshots=getattr(args, "snapshots", None) or "strict", market=getattr(args, "market", None))
        try:
            try:
                rows, st = run_local(sources, a)
            except ValueError as error:
                if not str(error).startswith("CONFLICT") or a.snapshots == "latest":
                    raise
                a.snapshots = "latest"
                rows, st = run_local(sources, a)
                st["snapshots_reason"] = "嚴格批次衝突(%s)→ 同表取最新批次" % str(error)[:100]
            valid = sum(1 for r in rows if r.get("valid"))
            derived = (st.get("calendar") or {}).get("mode") == "derived" or st.get("snapshots") == "latest"
            calc_lamp = "YELLOW" if derived else "GREEN"
            rec["probe"] = {"ticker": ticker, "rows": len(rows), "valid": valid, "stats": st,
                            "sample": [{k: r.get(k) for k in ("indicator_id", "window_n", "solution_id", "value_num", "valid", "verdict", "observation_date", "engine_version")} for r in rows[:6]]}
            step("③ 探針計算 %s(sma · rsi · macd)" % ticker, calc_lamp, "%d 列 · 有效 %d · 曆 %s%s" % (len(rows), valid, (st.get("calendar") or {}).get("mode"),
                 " · 批次取最新" if st.get("snapshots") == "latest" else ""))
        except (ValueError, OSError) as error:
            calc_lamp = "RED"
            rec["probe"] = {"ticker": ticker, "error": str(error)[:300]}
            step("③ 探針計算 %s" % ticker, "RED", "%s → %s" % (str(error)[:160], hint(str(error))))
    lamps = [s["lamp"] for s in rec["steps"]]
    rec["lamp"] = "RED" if "RED" in lamps else ("GRAY" if lampd == "GRAY" else ("YELLOW" if "YELLOW" in lamps else "GREEN"))
    rec["meaning"] = {"GREEN": "VDF 庫合 VQG 嚴格合約 · 指標可直接用", "YELLOW": "能算 · 但交易日序號 / 可用日 / 市場是 VQG 從 VDF 日線推的(列上 engine_version 標 derived)· 要嚴格綠 = VDF 出 session_index / available_on / market",
                      "RED": "自測不過或算不出來 · 看 steps", "GRAY": "這台機器沒有 VDF 庫(容器 / CI)· 只驗了自測"}[rec["lamp"]]
    rec["elapsed_s"] = round((datetime.now() - t0).total_seconds(), 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    body = json.dumps(rec, ensure_ascii=False, indent=1, default=str)
    (out_dir / "VQG_Closeout_latest.json").write_text(body, encoding="utf-8")
    (out_dir / ("VQG_Closeout_%s.json" % t0.strftime("%Y%m%d_%H%M%S"))).write_text(body, encoding="utf-8")
    print("[%s] VQG 收尾 · %s · 收據 %s · %.1f 秒" % (rec["lamp"], rec["meaning"], out_dir / "VQG_Closeout_latest.json", rec["elapsed_s"]), flush=True)
    return 0 if rec["lamp"] in ("GREEN", "YELLOW", "GRAY") else 2


HINTS = (("NEED_VDF_CALENDAR_OR_AVAILABILITY", "VDF 檔沒有交易日序號 / 可用日 → 加 --calendar derive(用 VDF 日線自己的交易日 · 結果標 derived)或 auto;要嚴格 = VDF 出 session_index / available_on"),
         ("MARKET_UNRESOLVED", "VDF 檔沒有 market 欄 · 代號不是台股樣式 → 加 --calendar derive(英文代號推為 US)或 --market TW|US"),
         ("CONFLICT", "VDF 同一張表有多個批次檔、同一天值不同(還原價重算)→ 加 --snapshots latest(同表只用最新批次)"),
         ("DUPLICATE_DATE", "同一檔裡同一天出現兩次 → 那是 VDF 檔的問題(VQG 不任選)· 交 VDF"),
         ("HISTORY_LIMIT", "歷史超過 5000 列 → 加 --start YYYY-MM-DD"),
         ("NO_VISIBLE_PRICE", "這個代號在 VDF 庫找不到、或 as-of 之前沒有價 → 用 doctor 看 tickers_sample"),
         ("OMITTED_SESSION", "VDF 有 session_index 但跳號(缺日沒插空列)→ 交 VDF;或改 --calendar derive"),
         ("VDF_ROOT", "VDF 庫根不在 → --root 或 $env:VQG_VDF_ROOT(VDF 的冊 VDF_DataHome_SSOT 寫的 db_home)"))


def hint(text: str) -> str:
    return next((h for k, h in HINTS if k in text), "看上面那一行;要全貌跑 doctor")


# ── 自測(v0104 自測 + 本版 11 項)──────────────────────────────────────────
def _vdf_like(path: Path, rows: list):
    """照 VDF ENG054 寫法:date 是 'YYYY-MM-DD' 字串 · ticker · OHLC · adj_close · volume(沒有 market / session_index / available_on)。"""
    pl.DataFrame(rows, schema={"date": pl.String, "ticker": pl.String, "open": pl.Float64, "high": pl.Float64, "low": pl.Float64,
                               "close": pl.Float64, "adj_close": pl.Float64, "volume": pl.Float64}, orient="row").write_parquet(path)


def _bars(ticker, start, n, skip=(), base=100.0, bump=None):
    out = []
    for i in range(n):
        d = start + timedelta(days=i)
        if i in skip:
            continue
        p = base + 0.3 * i + 2.0 * ((i * 7) % 5 - 2) + (bump.get(i, 0.0) if bump else 0.0)
        out.append((d.isoformat(), ticker, p, p + 1, p - 1, p, p, 1000.0 + i))
    return out


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("  [OK] " if cond else "  [FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            PRIOR.selftest()
        prior_ok = "PASS" in buf.getvalue()
    except Exception as error:  # noqa: BLE001
        prior_ok = False
        buf.write("%s: %s" % (type(error).__name__, error))
    chk("① v0104 自測照過(%s)" % (buf.getvalue().strip().splitlines() or ["—"])[-1][:60], prior_ok)
    src_text = Path(__file__).read_text(encoding="utf-8")
    chk("② 第 3 行加速器標記 · 前版 v0104 位元組 = 操作員原檔(SHA-256 釘住)· 本檔不匯入任何網路模組",
        src_text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and hashlib.sha256(PRIOR_PATH.read_bytes()).hexdigest() == PRIOR_SHA256
        and not re.search(r"^\s*(import|from)\s+(urllib|requests|socket|http|httpx|aiohttp)\b", src_text, re.M))
    d0 = date(2026, 1, 1)
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        vdf = t / "vdf_database"
        (vdf / "output_hub").mkdir(parents=True)
        _vdf_like(vdf / "output_hub" / "tw_daily_prices_20261101_120000.parquet", _bars("2330.TW", d0, 120) + _bars("2317.TW", d0, 120, skip=(100,), base=80))
        _vdf_like(vdf / "output_hub" / "us_daily_prices_20261101_120000.parquet", _bars("NVDA", d0, 120, base=50))
        src, err = PRIOR.discover(vdf)
        as_of = d0 + timedelta(days=125)
        mk = lambda tk, cal: types.SimpleNamespace(root=vdf, ticker=tk, metrics=["sma", "rsi", "macd"], windows=None, as_of=as_of, start=None, report_id=None,
                                                   cache_dir=None, calendar=cal, snapshots="strict", market=None)

        def err_of(fn):
            try:
                fn()
                return ""
            except ValueError as e:
                return str(e)
        e_tw, e_us = err_of(lambda: run_local(src, mk("2330.TW", "vdf"))), err_of(lambda: run_local(src, mk("NVDA", "vdf")))
        chk("③ VDF 形狀的日線(沒有 market / session_index / available_on)· 嚴格模式 = v0104:台股 NEED_VDF_CALENDAR_OR_AVAILABILITY · 美股 MARKET_UNRESOLVED(乾淨的 ValueError)",
            not err and e_tw.startswith("NEED_VDF_CALENDAR_OR_AVAILABILITY") and e_us.startswith("MARKET_UNRESOLVED"))
        rows_d, st_d = run_local(src, mk("2330.TW", "derive"))
        cal = st_d.get("calendar") or {}
        # 對照組:同一份價格,交易日序號 / 可用日 / 市場明寫(= derive 該推出的)→ v0104 嚴格模式
        ref = t / "ref"
        ref.mkdir()
        days = sorted({d0 + timedelta(days=i) for i in range(120)})
        idx = {d: i + 1 for i, d in enumerate(days)}

        def explicit(bars, path, nulls=()):
            rows = [{"date": date.fromisoformat(b[0]), "ticker": b[1], "adj_close": b[6], "market": "TW", "session_index": idx[date.fromisoformat(b[0])],
                     "available_on": date.fromisoformat(b[0])} for b in bars]
            rows += [{"date": d, "ticker": bars[0][1], "adj_close": None, "market": "TW", "session_index": idx[d], "available_on": d} for d in nulls]
            pl.DataFrame(rows).sort("date").write_parquet(path)
        explicit(_bars("2330.TW", d0, 120), ref / "a.parquet")
        explicit(_bars("2317.TW", d0, 120, skip=(100,), base=80), ref / "b.parquet", nulls=(d0 + timedelta(days=100),))
        rsrc, _ = PRIOR.discover(ref)
        key = lambda rs: {(r["indicator_id"], r["window_n"], r["solution_id"]): r["value_json"] for r in rs}
        rows_r, _ = run_local(rsrc, types.SimpleNamespace(**dict(vars(mk("2330.TW", "vdf")), root=ref)))
        chk("④ --calendar derive:台股 2330.TW 算得出 · 數值與「同價格 + 明寫序號 / 可用日」的 v0104 嚴格結果逐格相同(%d 格)· 每列 engine_version = %s"
            % (len(rows_d), DERIVED_TAG), key(rows_d) == key(rows_r) and len(rows_d) == 24 and all(r["engine_version"] == DERIVED_TAG for r in rows_d) and all(r["engine_version"] == ENGINE_VERSION for r in rows_r))
        rows_h, st_h = run_local(src, mk("2317.TW", "derive"))
        rows_hr, _ = run_local(rsrc, types.SimpleNamespace(**dict(vars(mk("2317.TW", "vdf")), root=ref)))
        chk("⑤ 停牌日:2317.TW 少第 101 天(同市場 2330 有)→ derive 插 1 列明確空值(v0104 要求的上游插空列)· 結果 = 明寫空列的嚴格結果",
            (st_h.get("calendar") or {}).get("inserted_null_sessions") == 1 and key(rows_h) == key(rows_hr))
        rows_u, st_u = run_local(src, mk("NVDA", "derive"))
        chk("⑥ 美股 NVDA(VDF 檔沒有 market 欄)→ derive 推為 US · 算得出 %d 列 · 依據寫進統計" % len(rows_u),
            len(rows_u) == 24 and (st_u.get("calendar") or {}).get("market") == "US" and "US" in (st_u.get("calendar") or {}).get("market_source", ""))
        rows_a, st_a = run_local(src, mk("2330.TW", "auto"))
        chk("⑦ --calendar auto:嚴格先試 → 只因缺曆才改 derive(原因記在統計)· 結果 = derive",
            key(rows_a) == key(rows_d) and "NEED_VDF_CALENDAR" in (st_a.get("calendar") or {}).get("auto_reason", ""))
        snap = t / "snap"
        snap.mkdir()
        old = _bars("2330.TW", d0, 120)
        new = _bars("2330.TW", d0, 120, bump={5: -3.0})                    # 除權息後舊日還原價重算
        _vdf_like(snap / "tw_daily_prices_20261101_120000.parquet", old)
        _vdf_like(snap / "tw_daily_prices_20261102_120000.parquet", new)
        only = t / "only_new"
        only.mkdir()
        _vdf_like(only / "tw_daily_prices_20261102_120000.parquet", new)
        ssrc, _ = PRIOR.discover(snap)
        osrc, _ = PRIOR.discover(only)
        e_c = err_of(lambda: run_local(ssrc, types.SimpleNamespace(**dict(vars(mk("2330.TW", "derive")), root=snap, metrics=["ema"]))))
        rl, sl = run_local(ssrc, types.SimpleNamespace(**dict(vars(mk("2330.TW", "derive")), root=snap, metrics=["ema"], snapshots="latest")))
        ro, _ = run_local(osrc, types.SimpleNamespace(**dict(vars(mk("2330.TW", "derive")), root=only, metrics=["ema"])))
        chk("⑧ 同表兩個批次、舊日還原價不同:strict = v0104 CONFLICT 拒算 · --snapshots latest = 只用最新批次(= 只有新批次時的結果 · 被取代的檔列在統計)",
            e_c.startswith("CONFLICT") and key(rl) == key(ro) and any("20261101" in p for p in sl.get("superseded_snapshots", [])))
        dv = doctor(vdf)
        dr = doctor(ref)
        ds = doctor(snap)
        chk("⑨ doctor:VDF 形狀 → DERIVE_READY(缺 available_on · market · session_index)· 明寫的 → STRICT_READY · 多批次表點名",
            dv["verdict"] == "DERIVE_READY" and dv["missing_for_strict"] == ["available_on", "market", "session_index"] and dr["verdict"] == "STRICT_READY"
            and ds["multi_snapshot_tables"] and doctor(t / "nope")["verdict"] == "NO_VDF_ROOT")
        via = t / "VIA"
        (via / "functional modules" / "VDF").mkdir(parents=True)
        (via / "supportive modules").mkdir()
        (via / "functional modules" / "VDF" / "VDF_DataHome_SSOT_v0101.json").write_text(json.dumps({"homes": [{"id": "gone", "db_home": str(t / "nope")}, {"id": "here", "db_home": str(vdf)}]}), encoding="utf-8")
        got_root, got_how = default_root(via)
        chk("⑩ 預設 VDF 庫根照 VDF 的冊(VDF_DataHome_SSOT 尾版 · homes 照順序取第一個在的)", got_root == vdf and "here" in got_how)
        ob = io.StringIO()
        with contextlib.redirect_stdout(ob):
            _CTX["in_selftest"] = True
            try:
                rc_c = _closeout_inner(types.SimpleNamespace(via_root=str(via), root=None, root_given=False, out_dir=None, ticker=None, as_of=as_of, snapshots=None, market=None))
                rc_bad = _closeout_inner(types.SimpleNamespace(via_root=str(via), root=str(vdf), root_given=True, out_dir=str(vdf / "out"), ticker=None, as_of=as_of, snapshots=None, market=None))
            finally:
                _CTX.pop("in_selftest", None)
        recj = json.loads((via / "VIA_Reports" / "vqg" / "VQG_Closeout_latest.json").read_text(encoding="utf-8"))
        chk("⑪ closeout:收據寫在 VIA_Reports\\vqg(YELLOW = 曆是推的 · 探針 %s)· 收據夾在 VDF 庫裡 → 拒寫 rc 2 · VDF 夾沒多任何檔" % (recj.get("probe") or {}).get("ticker"),
            rc_c == 0 and recj["lamp"] == "YELLOW" and (recj.get("probe") or {}).get("ticker") == "2330.TW" and rc_bad == 2 and not (vdf / "out").exists()
            and sorted(p.name for p in (vdf / "output_hub").iterdir()) == ["tw_daily_prices_20261101_120000.parquet", "us_daily_prices_20261101_120000.parquet"])
    print("[%s] VQG %s selftest · v0104 + 本版 %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", VERSION_TAIL, 10, len(bad)), flush=True)
    return 0 if not bad else 1


def _closeout_inner(args):
    """closeout 本體(自測裡不再跑一次自測 · 避免遞迴)。"""
    if _CTX.get("in_selftest"):
        global selftest
        real = selftest
        selftest = lambda: (print("[PASS] (自測中 · 略過內層自測)") or 0)    # noqa: E731
        try:
            return closeout(args)
        finally:
            selftest = real
    return closeout(args)


# ── 入口 ────────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    ext = argparse.ArgumentParser(add_help=False)
    ext.add_argument("--calendar", choices=["vdf", "derive", "auto"])
    ext.add_argument("--snapshots", choices=["strict", "latest"])
    ext.add_argument("--market", choices=["TW", "US"])
    ext.add_argument("--via-root")
    ext.add_argument("--out-dir")
    opts, rest = ext.parse_known_args(argv)
    cmd = next((a for a in rest if not a.startswith("-")), "scan")
    if cmd in ("selftest", "test") or "--selftest" in argv:               # 全樹契約 L53:位置動詞與 --selftest 都吃
        try:
            return selftest()
        except Exception as error:  # noqa: BLE001  自測本身炸了也照實記 FAIL(不吐 traceback)
            print("[FAIL] VQG %s selftest 中斷 · %s: %s" % (VERSION_TAIL, type(error).__name__, str(error)[:200]), flush=True)
            return 1
    if "--help" in rest or "-h" in rest:
        print(__doc__)
        print("v0105 指令:selftest | doctor [--root R] | closeout [--root R] [--ticker T] | scan | calc … [--calendar vdf|derive|auto] [--snapshots strict|latest] [--market TW|US] | activity | chart | catalog")
        return 0
    root_given = "--root" in rest
    if not root_given:
        r, how = default_root(via_root(opts.via_root))
        rest = rest + ["--root", str(r)]
        print("[計] VDF 庫根 %s(%s)" % (r, how), file=sys.stderr, flush=True)
    if cmd in ("doctor", "closeout"):
        ap = argparse.ArgumentParser(prog="VQG " + cmd)
        ap.add_argument("command")
        ap.add_argument("--root", required=True)
        ap.add_argument("--ticker")
        ap.add_argument("--as-of", type=date.fromisoformat)
        a = ap.parse_args(rest)
        if cmd == "doctor":
            print(json.dumps(doctor(a.root), ensure_ascii=False, indent=1, default=str))
            return 0
        return closeout(types.SimpleNamespace(via_root=opts.via_root, root=a.root, root_given=root_given, out_dir=opts.out_dir, ticker=a.ticker,
                                              as_of=a.as_of, snapshots=opts.snapshots, market=opts.market))
    _CTX.update(default_calendar=opts.calendar, default_snapshots=opts.snapshots, default_market=opts.market)
    old = sys.argv
    try:
        sys.argv = [str(PRIOR_PATH)] + rest
        PRIOR.main()
        return 0
    except (ValueError, OSError) as error:
        text = "%s: %s" % (type(error).__name__, error) if isinstance(error, OSError) else str(error)
        if isinstance(error, FileNotFoundError):
            text = "VDF_ROOT 不在:%s" % error
        print("[RED] VQG %s · %s → %s" % (cmd, text[:300], hint(text)), flush=True)
        return 2
    finally:
        sys.argv = old
        _CTX.update(default_calendar=None, default_snapshots=None, default_market=None)


if __name__ == "__main__":
    raise SystemExit(main())
