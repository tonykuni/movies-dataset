#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_ConsensusJoin v0105 — v0104 薄尾(v0104 ~ v0100 一字不改):TARGET_PRICE(ADJ) 同步還原 · 兩家目標價中位數並存 · 共識照 TWSE / TPEX 的輸出格式落盤後合併。

操作員 2026-11-01:「Yahoo 和共識照用 · Target Price(Adj) 也應該同步還原才有可比較性 · 兩個單位所算的目標價中位數並存方便比較 ·
只要最後把他跟 TWSE / TPEX 輸出個格式一樣再合併即可」。本版:
  ① TARGET_PRICE(ADJ) 同步還原:MarketFetch 填值只認 VDF 還原過(Yahoo 收盤 = TWSE 收盤)的日子;報告日前那天 Yahoo 收盤 ≠ TWSE 收盤
     (CLOSE_MISMATCH · VDF 不還原)→ 整列 MISSING。本版只讀 VRN-2 輸出夾裡 VDF 落盤的日線(market/vdf/parquet/tw_equity_daily · 不改)逐份查:
       a. 報告日前最後一個交易日 VDF 已還原 → 因子 = adj_close / close(跟 MarketFetch 同一條規則)。
       b. CLOSE_MISMATCH,但 Yahoo 收盤 ÷ TWSE 收盤 = r 在報告日前整段一致(±0.5%)、報告日後有一天起 Yahoo = TWSE(MATCH)、r 離 1 超過 1%
          → Yahoo 對除權 / 分割 / 面額變更的追溯調整:因子 = Yahoo 還原收盤 ÷ TWSE 收盤(跟最新 ADJ_CLOSE 同一個 Yahoo 還原基準)。
       c. 其他(沒有報告日前的日線 · Yahoo 沒那天 · r 不一致 · 看不出調整點)→ 照舊 MISSING,原因寫實(不猜)。
     TARGET_PRICE(ADJ) / ADJ_CLOSE_BEFORE_REPORT / UPSIDE_PCT(ADJ) 三格同一個因子;STATUS 寫哪條規則 · 那天 · 比值。證據 → market/VRN2_TPAdjSync_latest.json
     (也收 VDF 自己的 status.json 與日線品質 = ⑥e「擷取 YELLOW · 失敗 0」(VDF 回 rc 2 PARTIAL)的錨點)。MarketFetch 的 VRN2_Market_latest.json 不改。
  ② FACTSET_TARGET_PRICE_MEDIAN 與 YFINANCE_TARGET_PRICE_MEDIAN 兩欄照舊並存(Combined 欄序不動);合併資料集另給兩家差距 % 與各自的上漲空間。
  ③ 共識照 TWSE / TPEX 的輸出格式(VDF 落盤格式:識別欄 date · ticker · yfinance_ticker · bloomberg_ticker · name 在前 · 小寫欄名 · 主鍵 [date, ticker] ·
     parquet/<資料集>/ticker=<代號>/year=<年>/data.parquet 分區 + 整合檔 <資料集>.parquet(zstd)+ 大寫表頭 CSV)落在 consensus/dataset/:
       tw_consensus(兩家目標價中位數 / 平均 / 人數 · 現價 · 閘)· tw_consensus_estimate(EPS / 本益比 · 主鍵 [date, ticker, fiscal_year, account])
     → 再跟 TWSE / TPEX 日線(VDF tw_equity_daily · 只讀)依 [date, ticker] 取「當天或之前最後一個交易日」合併 = tw_market_consensus
       (收盤 · 還原收盤 · 兩家中位數 · 兩家上漲空間 · 兩家差距)· 這輪的合併列另出 output/VRN2_MarketConsensus_latest(增量庫 OutputStore v0102 收這本)。
動詞同 v0104:run · join · --selftest · --engine-shim。
"""
from __future__ import annotations

import csv
import datetime
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile

VERSION = "v0105"
DISPLAY_NAME = "VRN2_ConsensusJoin"
TAG = "共識合併 v0105"
PRIOR_NAME = "VRN2_ConsensusJoin_v0104.py"
HERE = Path(__file__).resolve().parent
SYNC_JSON = "VRN2_TPAdjSync_latest.json"
BOOK_NAME = "MarketConsensus"
DATASET_DIR = ("consensus", "dataset")
IDENTITY = ["date", "ticker", "yfinance_ticker", "bloomberg_ticker", "name"]          # = VDF IDENTITY_PREFIX(TWSE / TPEX 落盤的前五欄)
RATIO_TOL = 0.005                     # 報告日前 Yahoo 收盤 ÷ TWSE 收盤 整段一致的容許差
MIN_GAP = 0.01                        # 比值離 1 不到 1% = 不是除權 / 分割的追溯調整
WINDOW_DAYS = 10                      # 報告日前看幾天(MarketFetch 視窗 = 報告日 -7 ~ -1)
MERGE_MAX_DAYS = 14                   # 合併:共識那天之前最多往回找幾天的 TWSE / TPEX 收盤(再舊就不配 · 價格欄空白)
DAILY_COLS = ("date", "ticker", "name", "market", "yfinance_ticker", "bloomberg_ticker", "close", "adj_close", "volume", "yf_close", "yf_adj_close",
              "close_check", "adjustment_status", "quality")
CONS_COLS = IDENTITY + ["market", "factset_target_price_median", "factset_target_price_mean", "factset_analyst_count", "factset_rate_date",
                        "yfinance_target_price_median", "yfinance_target_price_mean", "yfinance_analyst_count", "median_gap_pct",
                        "consensus_current_price", "yfinance_current_price", "source_agreement_gate", "quality", "source", "source_page", "source_yfinance", "fetched_at"]
EST_COLS = IDENTITY + ["market", "fiscal_year", "account", "value", "unit", "source", "fetched_at"]
MERGED_COLS = IDENTITY + ["market", "price_date", "close", "adj_close", "volume", "adjustment_status",
                          "factset_target_price_median", "yfinance_target_price_median", "median_gap_pct", "factset_analyst_count", "yfinance_analyst_count",
                          "upside_factset_pct", "upside_yfinance_pct", "source_agreement_gate", "quality", "source", "fetched_at"]
KEYS = {"tw_consensus": ["date", "ticker"], "tw_consensus_estimate": ["date", "ticker", "fiscal_year", "account"], "tw_market_consensus": ["date", "ticker"]}
COLS = {"tw_consensus": CONS_COLS, "tw_consensus_estimate": EST_COLS, "tw_market_consensus": MERGED_COLS}
_TS = {"date", "price_date"}
_INT = {"factset_analyst_count", "yfinance_analyst_count", "fiscal_year", "volume"}
_STR = {"ticker", "yfinance_ticker", "bloomberg_ticker", "name", "market", "factset_rate_date", "source_agreement_gate", "quality", "source", "source_page",
        "source_yfinance", "fetched_at", "account", "unit", "adjustment_status", "close_check"}
GATE_QUALITY = {"PASS": "OK", "CONFLICT": "REVIEW", "INCOMPLETE": "PARTIAL"}


def _load(path: Path, alias: str):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    return _load(path, "vrn2_consensus_join_prior_v0104")


PRIOR = _prior()                       # v0104(它再載 v0103 → v0102 → v0101 → v0100)
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
V0103 = PRIOR.PRIOR
V0102, V0101, V0100 = PRIOR.V0102, PRIOR.V0101, PRIOR.V0100
for _mod in (PRIOR, V0103, V0102, V0101, V0100):
    _mod.TAG = TAG
_v0104_run = PRIOR.run
_v0104_join = PRIOR.join               # = v0103 的 join(v0104 沒改 join)


# ── 共用小工具 ──────────────────────────────────────────────────────────────────────────────────────────────
def _num(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return f if f == f and abs(f) != float("inf") else None


def _int(v):
    f = _num(v)
    return int(f) if f is not None else None


def _day(v):
    if v is None:
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    try:
        return datetime.date.fromisoformat(str(v).strip()[:10].replace("/", "-"))
    except ValueError:
        return None


def _taipei_day(iso: str):
    """fetched_at_utc(ISO · 帶時區)→ 台北日期(UTC+8 · 台灣沒有日光節約)。"""
    try:
        t = datetime.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return _day(iso)
    if t.tzinfo is not None:
        t = t.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return (t + datetime.timedelta(hours=8)).date()


def _sql_list(files) -> str:
    return "[%s]" % ", ".join("'%s'" % str(f).replace("'", "''") for f in files)


def parquet_rows(files, cols=None) -> list | None:
    """parquet 檔(可多個 · 欄位聯集)→ list[dict](只取 cols 裡有的欄)· duckdb 優先 · pyarrow 備援 · 都沒有 → None(只讀)。"""
    files = [str(f) for f in files]
    if not files:
        return []
    try:
        import duckdb  # noqa: WPS433
    except ImportError:
        duckdb = None
    if duckdb is not None:
        con = duckdb.connect()
        try:
            src = "read_parquet(%s, union_by_name=true)" % _sql_list(files)
            have = [d[0] for d in con.execute("SELECT * FROM %s LIMIT 0" % src).description]
            pick = [c for c in (cols or have) if c in have]
            if not pick:
                return []
            cur = con.execute("SELECT %s FROM %s" % (", ".join('"%s"' % c.replace('"', '""') for c in pick), src))
            return [dict(zip(pick, r)) for r in cur.fetchall()]
        finally:
            con.close()
    try:
        import pyarrow.parquet as pq  # noqa: WPS433
    except ImportError:
        return None
    out = []
    for f in files:
        table = pq.read_table(f)
        pick = [c for c in (cols or table.column_names) if c in table.column_names]
        out.extend(table.select(pick).to_pylist())
    return out


def _conv(col: str, v):
    if col in _TS:
        d = _day(v)
        return datetime.datetime(d.year, d.month, d.day) if d else None
    if col in _INT:
        return _int(v)
    if col in _STR:
        return None if v is None else str(v)
    return _num(v)


def write_parquet(rows: list, cols: list, path: Path) -> str:
    """rows → parquet(zstd · tmp 再換上)· pyarrow 優先(timestamp[ns] · 跟 VDF 用 pandas 落盤的型別一樣)· duckdb 備援。回用了哪個。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.parquet")
    data = [[_conv(c, r.get(c)) for c in cols] for r in rows]
    try:
        import pyarrow as pa  # noqa: WPS433
        import pyarrow.parquet as pq  # noqa: WPS433
    except ImportError:
        pa = None
    if pa is not None:
        def typ(c):
            return pa.timestamp("ns") if c in _TS else (pa.int64() if c in _INT else (pa.string() if c in _STR else pa.float64()))
        schema = pa.schema([pa.field(c, typ(c)) for c in cols])
        table = pa.table({c: pa.array([row[i] for row in data], type=typ(c)) for i, c in enumerate(cols)}, schema=schema)
        pq.write_table(table, str(tmp), compression="zstd")
        used = "pyarrow"
    else:
        import duckdb  # noqa: WPS433
        con = duckdb.connect()
        try:
            def dtyp(c):
                return "TIMESTAMP_NS" if c in _TS else ("BIGINT" if c in _INT else ("VARCHAR" if c in _STR else "DOUBLE"))
            con.execute("CREATE TABLE t(%s)" % ", ".join('"%s" %s' % (c, dtyp(c)) for c in cols))
            if data:
                con.executemany("INSERT INTO t VALUES (%s)" % ", ".join("?" * len(cols)), data)
            con.execute("COPY t TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % str(tmp).replace("'", "''"))
        finally:
            con.close()
        used = "duckdb"
    os.replace(str(tmp), str(path))
    return used


def _key(ds: str, r: dict) -> tuple:
    return tuple(str(_day(r.get(k)) if k in _TS else ("" if r.get(k) is None else (_int(r.get(k)) if k in _INT else r.get(k)))) for k in KEYS[ds])


def _csv_value(c, v):
    if v is None:
        return ""
    if c in _TS:
        d = _day(v)
        return d.isoformat() if d else ""
    return v


def store_dataset(root: Path, ds: str, rows: list) -> dict:
    """VDF 的落盤法:parquet/<ds>/ticker=<代號>/year=<年>/data.parquet(同主鍵新蓋舊 · 其他保留)→ 整合檔 <ds>.parquet + <ds>.csv(大寫表頭 · utf-8-sig)。"""
    cols, written = COLS[ds], 0
    groups = {}
    for r in rows:
        d = _day(r.get("date"))
        if d and r.get("ticker"):
            groups.setdefault((str(r["ticker"]), d.year), []).append(r)
    engine = ""
    for (ticker, year), part in sorted(groups.items()):
        path = root / "parquet" / ds / ("ticker=%s" % ticker) / ("year=%d" % year) / "data.parquet"
        merged = {}
        if path.is_file():
            for old in parquet_rows([path], cols) or []:
                merged[_key(ds, old)] = old
        for r in part:
            merged[_key(ds, r)] = r
        engine = write_parquet([merged[k] for k in sorted(merged)], cols, path)
        written += len(part)
    files = sorted((root / "parquet" / ds).glob("ticker=*/year=*/data.parquet"))
    every = parquet_rows(files, cols) if files else []
    every = sorted(every or [], key=lambda r: _key(ds, r))
    if files:
        engine = write_parquet(every, cols, root / ("%s.parquet" % ds)) or engine
        with (root / ("%s.csv" % ds)).open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow([c.upper().replace("_", " ") for c in cols])
            for r in every:
                w.writerow([_csv_value(c, r.get(c)) for c in cols])
    return {"dataset": ds, "rows_this_run": written, "rows_total": len(every), "partitions": len(files), "engine": engine,
            "integrated": str(root / ("%s.parquet" % ds)) if files else "", "identity": cols[:5] == IDENTITY}


# ── ① TARGET_PRICE(ADJ) 同步還原 ──────────────────────────────────────────────────────────────────────────────
def daily_rows(v2: Path, code: str) -> list | None:
    """VRN-2 輸出夾裡 VDF 落盤的這檔日線(只讀)→ 依日期排序 · 同日留最後一列 · None = 讀不了(沒有 duckdb / pyarrow)。"""
    base = Path(v2) / "market" / "vdf" / "parquet" / "tw_equity_daily"
    files = sorted(base.glob("ticker=%s/year=*/data.parquet" % code))
    got = parquet_rows(files, DAILY_COLS)
    if got is None:
        return None
    byday = {}
    for r in got:
        d = _day(r.get("date"))
        if d:
            byday[d] = dict(r, date=d, close=_num(r.get("close")), adj_close=_num(r.get("adj_close")), yf_close=_num(r.get("yf_close")),
                            yf_adj_close=_num(r.get("yf_adj_close")), volume=_num(r.get("volume")), close_check=str(r.get("close_check") or ""),
                            adjustment_status=str(r.get("adjustment_status") or ""))
    return [byday[d] for d in sorted(byday)]


def sync_factor(rows: list, rd: datetime.date) -> dict:
    """報告日 rd 前最後一個交易日的還原因子(規則見檔頭 ① a / b / c)→ {mode, factor?, reason, 證據}。"""
    if not rows:
        return {"mode": "MISSING", "reason": "MISSING(VDF 日線沒有這檔 · ⑥e 沒抓到)"}
    pre = [r for r in rows if r["date"] < rd]
    if not pre:
        return {"mode": "MISSING", "reason": "MISSING(VDF 日線最早 %s · 報告日 %s 前沒有資料 · ⑥e 視窗沒抓到 · 需回補)" % (rows[0]["date"], rd)}
    b = pre[-1]
    base = {"before_date": str(b["date"]), "close": b.get("close"), "yf_close": b.get("yf_close"), "yf_adj_close": b.get("yf_adj_close"),
            "close_check": b.get("close_check") or "", "adjustment_status": b.get("adjustment_status") or ""}
    close = b.get("close")
    if not close or close <= 0:
        return dict(base, mode="MISSING", reason="MISSING(VDF %s 沒有 TWSE / TPEX 收盤)" % b["date"])
    if b.get("adj_close") and b["adj_close"] > 0 and base["adjustment_status"] in ("", "ADJUSTED"):
        return dict(base, mode="VDF_ADJUSTED", factor=b["adj_close"] / close, reason="VDF 已還原(adj_close ÷ close)")
    yc, ya = b.get("yf_close"), b.get("yf_adj_close")
    if not yc or yc <= 0 or not ya or ya <= 0:
        return dict(base, mode="MISSING", reason="MISSING(Yahoo 沒有 %s 的收盤 / 還原收盤 · VDF close_check %s · 還原因子算不出)" % (b["date"], base["close_check"] or "MISSING"))
    r0 = yc / close
    base["ratio"] = round(r0, 6)
    if abs(r0 - 1) <= MIN_GAP:
        return dict(base, mode="MISSING", reason="MISSING(Yahoo 收盤 ÷ TWSE 收盤 = %.4f · 差不到 1%% 但 VDF 沒還原(%s)· 不猜)" % (r0, base["adjustment_status"] or "—"))
    lo = b["date"] - datetime.timedelta(days=WINDOW_DAYS)
    win = [r for r in pre if r["date"] >= lo and (r.get("close") or 0) > 0 and (r.get("yf_close") or 0) > 0]
    spread = max(abs((r["yf_close"] / r["close"]) / r0 - 1) for r in win)
    after = [r for r in rows if r["date"] >= rd and r.get("close_check") == "MATCH"]
    base.update(days=len(win), spread=round(spread, 6), match_from=str(after[0]["date"]) if after else "")
    if spread > RATIO_TOL:
        return dict(base, mode="MISSING", reason="MISSING(Yahoo 收盤 ÷ TWSE 收盤 報告日前 %d 天不一致 · %.4f 差 %.2f%% · 不像除權 / 分割的追溯調整 · 不猜)" % (len(win), r0, spread * 100))
    if not after:
        return dict(base, mode="MISSING", reason="MISSING(Yahoo 收盤 ÷ TWSE 收盤 = %.4f 報告日前一致 · 但報告日後沒有一天 Yahoo = TWSE · 看不出調整點 · 不猜)" % r0)
    return dict(base, mode="SYNC_YAHOO_RATIO", factor=ya / close,
                reason="同步還原(Yahoo 收盤 ÷ TWSE 收盤 = %.4f · 報告日前 %d 天一致 · %s 起 Yahoo = TWSE → 除權 / 分割 / 面額變更的追溯調整 · 因子 = Yahoo 還原收盤 ÷ TWSE 收盤)"
                % (r0, len(win), base["match_from"]))


def vdf_quality(v2: Path, codes, cache: dict) -> dict:
    """⑥e 錨點(只讀):VDF 自己的 status.json(rc 2 = PARTIAL 的原因)+ 每檔日線 Yahoo 收盤對不上(MISMATCH)/ Yahoo 沒那天(MISSING)的列數與日期範圍。"""
    st = _jread(Path(v2) / "market" / "vdf" / "status.json", {}) or {}
    daily = ((st.get("datasets") or {}).get("daily") or {}) if isinstance(st.get("datasets"), dict) else {}
    q = {"status": st.get("status"), "finished_at": st.get("finished_at"), "issues": [json.dumps(i, ensure_ascii=False, default=str)[:200] for i in (st.get("issues") or [])][:6],
         "daily_quality": daily.get("quality") if isinstance(daily, dict) else None, "tickers": {}}
    for code in sorted(set(codes)):
        rows = cache.get(code)
        if rows is None and code not in cache:
            try:
                rows = cache[code] = daily_rows(v2, code)
            except Exception as error:  # noqa: BLE001
                q["tickers"][code] = {"error": "%s: %s" % (type(error).__name__, str(error)[:120])}
                continue
        rows = rows or []
        mm = [r for r in rows if r.get("close_check") == "MISMATCH"]
        ms = [r for r in rows if r.get("close_check") == "MISSING"]
        if mm or ms:
            q["tickers"][code] = {"rows": len(rows), "mismatch": len(mm), "missing_yahoo": len(ms),
                                  "mismatch_dates": "%s ~ %s" % (mm[0]["date"], mm[-1]["date"]) if mm else "", "missing_dates": "%s ~ %s" % (ms[0]["date"], ms[-1]["date"]) if ms else ""}
    return q


def tp_adj_sync(v2: Path) -> dict:
    """MarketFetch 填值沒給 TARGET_PRICE(ADJ) 的報告 → 依 ① 規則補(或寫實的 MISSING 原因)· 證據 market/VRN2_TPAdjSync_latest.json。"""
    v2 = Path(v2)
    market = _jread(v2 / "market" / "VRN2_Market_latest.json", {}) or {}
    per_file = market.get("per_file") or {}
    basic = _jread(v2 / "output" / "VRN2_BasicInfo_latest.json", []) or []
    rec = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "tp_adj_sync", "at": now(),
           "rule": "TARGET_PRICE(ADJ) = TARGET_PRICE × 報告日前最後交易日的還原因子:VDF 已還原 → adj_close ÷ close;CLOSE_MISMATCH 且 Yahoo 收盤 ÷ TWSE 收盤 報告日前一致、"
                   "報告日後回到一致 → Yahoo 還原收盤 ÷ TWSE 收盤(同步還原);其他 MISSING 不猜 · ADJ_CLOSE_BEFORE_REPORT / UPSIDE_PCT(ADJ) 同一個因子",
           "per_file": {}, "counts": {}}
    cache, codes = {}, []
    for b in basic if isinstance(basic, list) else []:
        if not isinstance(b, dict):
            continue
        cm = _CODE.match(str(b.get("TICKER") or "").strip())
        if cm:
            codes.append(cm.group(1))
        fn = b.get("FILENAME")
        m = per_file.get(fn) if isinstance(per_file.get(fn), dict) else None
        tp = _num(b.get("TARGET_PRICE"))
        rd = _day(b.get("REPORT_DATE"))
        if not m or m.get("target_price_adj") is not None or tp is None or not cm or not rd:
            continue
        code = cm.group(1)
        if code not in cache:
            try:
                cache[code] = daily_rows(v2, code)
            except Exception as error:  # noqa: BLE001
                cache[code] = None
                rec.setdefault("read_errors", {})[code] = "%s: %s" % (type(error).__name__, str(error)[:120])
        rows = cache[code]
        got = sync_factor(rows, rd) if rows is not None else {"mode": "MISSING", "reason": "MISSING(讀不了 VDF 日線:%s)" % (rec.get("read_errors", {}).get(code) or "沒有 duckdb / pyarrow")}
        got.update(ticker=code, report_date=str(rd), target_price=tp)
        if got.get("factor"):
            f = got["factor"]
            got["target_price_adj"] = round(tp * f, 2)
            got["adj_close_before_report"] = round(got["close"] * f, 6)
            if _num(m.get("adj_close")):
                got["upside_adj"] = round(got["target_price_adj"] / _num(m.get("adj_close")) - 1, 9)
                got["upside_pct_adj"] = round(got["upside_adj"] * 100, 1)
        rec["per_file"][fn] = got
        rec["counts"][got["mode"]] = rec["counts"].get(got["mode"], 0) + 1
    try:
        rec["vdf"] = vdf_quality(v2, codes, cache)
    except Exception as error:  # noqa: BLE001
        rec["vdf"] = {"error": "%s: %s" % (type(error).__name__, str(error)[:160])}
    n_sync = sum(v for k, v in rec["counts"].items() if k != "MISSING")
    rec["lamp"] = "GREEN" if not rec["counts"].get("MISSING") else "YELLOW"
    rec["why"] = "TARGET_PRICE(ADJ) 補 %d · 仍缺 %d(%s)" % (n_sync, rec["counts"].get("MISSING", 0), " · ".join("%s %d" % kv for kv in sorted(rec["counts"].items())) or "MarketFetch 都給了")
    (v2 / "market").mkdir(parents=True, exist_ok=True)
    (v2 / "market" / SYNC_JSON).write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return rec


def _augment(market: dict, sync: dict) -> dict:
    got = json.loads(json.dumps(market, ensure_ascii=False, default=str))
    pf = got.setdefault("per_file", {})
    for fn, s in (sync.get("per_file") or {}).items():
        m = pf.setdefault(fn, {})
        if s.get("target_price_adj") is not None:
            m.update(target_price_adj=s["target_price_adj"], adjustment_factor_report=s["factor"], adj_close_before_report=s["adj_close_before_report"],
                     adj_close_before_report_date=s.get("before_date", ""))
            if s.get("upside_pct_adj") is not None:
                m.update(upside_adj=s["upside_adj"], upside_pct_adj=s["upside_pct_adj"])
            m.pop("before_status", None)
        elif s.get("reason"):
            m["before_status"] = s["reason"]
    return got


def _rewrite_status(v2: Path, sync: dict) -> int:
    """同步還原的列:STATUS 的 TARGET_PRICE(ADJ) 段寫哪條規則 · 哪一天 · 因子(Combined json / csv / parquet 一起寫)。"""
    path = Path(v2) / "output" / "VRN2_Combined_latest.json"
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return 0
    hit = 0
    for row in rows if isinstance(rows, list) else []:
        s = (sync.get("per_file") or {}).get(row.get("FILENAME"))
        if not s or s.get("target_price_adj") is None:
            continue
        text = "TARGET_PRICE(ADJ): 報告目標價 × 還原因子 %s(%s · %s)" % (_fmt(s["factor"], 6), s.get("before_date", ""), s.get("reason", ""))
        segs = [x for x in str(row.get("STATUS") or "").split(" | ") if x]
        idx = next((i for i, x in enumerate(segs) if x.startswith("TARGET_PRICE(ADJ): ")), None)
        if idx is None:
            segs.insert(0, text)
        else:
            segs[idx] = text
        new = " | ".join(segs)
        if new != row.get("STATUS"):
            row["STATUS"] = new
            hit += 1
    if hit:
        V0100._write(path.parent, rows, list(rows[0].keys()))
    return hit


# ── ③ 共識 → TWSE / TPEX 格式 → 合併 ─────────────────────────────────────────────────────────────────────────
def _pct(a, b, digits=2):
    a, b = _num(a), _num(b)
    return round((a / b - 1) * 100, digits) if a is not None and b else None


def consensus_rows(v2: Path) -> tuple:
    """VRN2_Consensus_latest.json 的 per_code → (tw_consensus 列, tw_consensus_estimate 列) · 識別欄跟 VDF 一樣(代號 · .TW / .TWO · <代號> TT · 名稱)。"""
    v2 = Path(v2)
    cons = _jread(v2 / "consensus" / CONSENSUS_JSON, {}) or {}
    per_t = (_jread(v2 / "market" / "VRN2_Market_latest.json", {}) or {}).get("per_ticker") or {}
    ymap = cons.get("yf_ticker_map") if isinstance(cons.get("yf_ticker_map"), dict) else {}
    tpex = set(str(x) for x in (ymap.get("tpex") or []))
    main, est = [], []
    for code, c in sorted((cons.get("per_code") or {}).items()):
        if not isinstance(c, dict) or not re.fullmatch(r"[1-9]\d{3}", str(code)):
            continue
        d = _taipei_day(c.get("fetched_at_utc") or cons.get("at") or "")
        if not d:
            continue
        t = per_t.get(code) or {}
        yft = t.get("yfinance_ticker") or ("%s.TWO" % code if code in tpex else "%s.TW" % code)
        ident = {"date": d, "ticker": str(code), "yfinance_ticker": yft, "bloomberg_ticker": t.get("bloomberg_ticker") or "%s TT" % code,
                 "name": t.get("name") or c.get("company_name") or "", "market": "TPEX" if yft.endswith(".TWO") else "TWSE"}
        fs, yf = _num(c.get("factset_target_median")), _num(c.get("yf_target_median"))
        gate = str(c.get("source_agreement_gate") or "")
        main.append(dict(ident, factset_target_price_median=fs, factset_target_price_mean=_num(c.get("factset_target_mean")), factset_analyst_count=_int(c.get("factset_analyst_count")),
                         factset_rate_date=(_day(c.get("factset_rate_date")).isoformat() if _day(c.get("factset_rate_date")) else ""),
                         yfinance_target_price_median=yf, yfinance_target_price_mean=_num(c.get("yf_target_mean")), yfinance_analyst_count=_int(c.get("yf_analyst_count")),
                         median_gap_pct=_pct(fs, yf), consensus_current_price=_num(c.get("current_price")), yfinance_current_price=_num(c.get("yf_current_price")),
                         source_agreement_gate=gate, quality=GATE_QUALITY.get(gate.upper(), gate), source="cnyes FactSet + Yahoo Finance",
                         source_page=c.get("source_page") or "", source_yfinance=c.get("source_yfinance") or "", fetched_at=str(c.get("fetched_at_utc") or "")))
        for account, unit, values in (("diluted_eps_median", "TWD", c.get("eps_median")), ("forward_pe", "x", c.get("forward_pe"))):
            for y, v in sorted((values or {}).items()) if isinstance(values, dict) else []:
                if _num(v) is not None and _int(y):
                    est.append(dict(ident, fiscal_year=_int(y), account=account, value=_num(v), unit=unit, source="cnyes FactSet", fetched_at=str(c.get("fetched_at_utc") or "")))
    return main, est


def merge_market(v2: Path, cons: list, cache: dict) -> list:
    """共識列 × TWSE / TPEX 日線(VDF · 只讀):同代號取共識那天或之前 MERGE_MAX_DAYS 天內最後一個交易日 → 收盤 · 還原收盤 · 兩家中位數 · 兩家上漲空間 · 兩家差距。"""
    out = []
    for c in cons:
        code, d = c["ticker"], _day(c["date"])
        if code not in cache:
            try:
                cache[code] = daily_rows(v2, code)
            except Exception:  # noqa: BLE001  讀不了日線 → 這列價格欄空白(共識照出)
                cache[code] = None
        rows = [r for r in (cache.get(code) or []) if r["date"] <= d and (d - r["date"]).days <= MERGE_MAX_DAYS]
        p = rows[-1] if rows else {}
        price = p.get("adj_close") or None
        out.append({**{k: c.get(k) for k in IDENTITY + ["market"]}, "market": p.get("market") or c.get("market"), "price_date": p.get("date"), "close": p.get("close"),
                    "adj_close": p.get("adj_close"), "volume": p.get("volume"), "adjustment_status": p.get("adjustment_status") or "",
                    "factset_target_price_median": c.get("factset_target_price_median"), "yfinance_target_price_median": c.get("yfinance_target_price_median"),
                    "median_gap_pct": c.get("median_gap_pct"), "factset_analyst_count": c.get("factset_analyst_count"), "yfinance_analyst_count": c.get("yfinance_analyst_count"),
                    "upside_factset_pct": _pct(c.get("factset_target_price_median"), price), "upside_yfinance_pct": _pct(c.get("yfinance_target_price_median"), price),
                    "source_agreement_gate": c.get("source_agreement_gate"), "quality": c.get("quality"),
                    "source": "TWSE / TPEX(VDF)+ " + str(c.get("source") or ""), "fetched_at": c.get("fetched_at")})
    return out


def _book(v2: Path, merged: list) -> dict:
    """這輪的合併列 → output/VRN2_MarketConsensus_latest.json / .csv(大寫欄名 · 日期 YYYY-MM-DD · 價格兩位 · 百分比兩位)。"""
    out_dir = Path(v2) / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in merged:
        row = {}
        for c in MERGED_COLS:
            v = r.get(c)
            if c in _TS:
                v = _day(v).isoformat() if _day(v) else ""
            elif c in _INT:
                v = "" if _int(v) is None else str(_int(v))
            elif c not in _STR:
                v = _fmt(v)
            row[c.upper()] = "" if v is None else v
        rows.append(row)
    jp = out_dir / ("VRN2_%s_latest.json" % BOOK_NAME)
    jp.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out_dir / ("VRN2_%s_latest.csv" % BOOK_NAME)).open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[c.upper() for c in MERGED_COLS])
        w.writeheader()
        w.writerows(rows)
    return {"rows": len(rows), "json": str(jp)}


def consensus_dataset(v2: Path, cache: dict | None = None) -> dict:
    v2 = Path(v2)
    cache = {} if cache is None else cache
    root = v2.joinpath(*DATASET_DIR)
    main, est = consensus_rows(v2)
    if not main:
        return {"lamp": "GRAY", "why": "沒有共識資料(⑥f)· 不落 TWSE / TPEX 格式資料集", "datasets": {}}
    merged = merge_market(v2, main, cache)
    got = {}
    for ds, rows in (("tw_consensus", main), ("tw_consensus_estimate", est), ("tw_market_consensus", merged)):
        got[ds] = store_dataset(root, ds, rows)
    book = _book(v2, merged)
    priced = sum(1 for r in merged if r.get("adj_close"))
    return {"lamp": "GREEN" if priced == len(merged) else "YELLOW", "root": str(root), "datasets": got, "book": book,
            "why": "TWSE / TPEX 格式:tw_consensus %d · tw_consensus_estimate %d · 合併 tw_market_consensus %d(有 TWSE / TPEX 價 %d)· 累計 %d 列" % (
                len(main), len(est), len(merged), priced, got["tw_market_consensus"]["rows_total"])}


# ── join:v0104(= v0103)的 join 前後各做一件 ───────────────────────────────────────────────────────────────────
def join(v2: Path) -> dict:
    """① 先算同步還原(只給 v0100 的 join 一份補過的市場資料 · 磁碟上的 VRN2_Market_latest.json 不改)→ v0104 的 join → STATUS 寫規則 → ③ 資料集 + 合併。"""
    v2 = Path(v2)
    try:
        sync = tp_adj_sync(v2)
    except Exception as error:  # noqa: BLE001  同步還原出錯 → 照前版 join(不擋 Combined)
        sync = {"per_file": {}, "lamp": "YELLOW", "why": "同步還原沒做成:%s: %s" % (type(error).__name__, str(error)[:160])}
    real = V0100._jread

    def jread_aug(p, default):
        got = real(p, default)
        if Path(p).name == "VRN2_Market_latest.json" and isinstance(got, dict) and sync.get("per_file"):
            return _augment(got, sync)
        return got
    V0100._jread = jread_aug
    try:
        got = _v0104_join(v2)
    finally:
        V0100._jread = real
    got["tp_adj_sync"] = {k: sync.get(k) for k in ("lamp", "why", "counts") if k in sync}
    try:
        got["tp_adj_status_rows"] = _rewrite_status(v2, sync)
    except Exception as error:  # noqa: BLE001
        got["tp_adj_status_rows"] = "沒寫:%s" % type(error).__name__
    try:
        ds = consensus_dataset(v2)
    except Exception as error:  # noqa: BLE001  資料集寫不成 → 黃 · Combined 照出
        ds = {"lamp": "YELLOW", "why": "TWSE / TPEX 格式資料集沒寫成:%s: %s" % (type(error).__name__, str(error)[:160])}
    got["consensus_dataset"] = ds
    if got.get("why"):
        got["why"] = "%s · 同步還原:%s · %s" % (got["why"], sync.get("why", "—"), ds.get("why", ""))
    return got


def _wire(run_fn, join_fn) -> None:
    for mod in (PRIOR, V0103, V0102, V0101, V0100):
        mod.run, mod.join = run_fn, join_fn


_wire(_v0104_run, join)
run = _v0104_run


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────────
def _daily_fixture(v2: Path, code: str, rows: list) -> None:
    by_year = {}
    for r in rows:
        by_year.setdefault(_day(r["date"]).year, []).append(r)
    cols = ["date", "ticker", "yfinance_ticker", "bloomberg_ticker", "name", "close", "adj_close", "volume", "yf_close", "yf_adj_close", "close_check", "adjustment_status", "market"]
    for y, part in by_year.items():
        write_parquet([dict(r, ticker=code) for r in part], cols, v2 / "market" / "vdf" / "parquet" / "tw_equity_daily" / ("ticker=%s" % code) / ("year=%d" % y) / "data.parquet")


def selftest(engine: str | None = None) -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    PRIOR._wire(PRIOR.run, PRIOR._v0103_join)                               # 前版自測照前版自己的接線跑(v0104 自己的 join 也還原)
    PRIOR.join = PRIOR._v0103_join
    try:
        rc = PRIOR.selftest(engine)
    finally:
        _wire(_v0104_run, join)
    chk("① v0104 自測(含 v0103 ~ v0100)照過", rc == 0)
    chk("② 啟動器 / CLI 的 join 都是本版(v0104 ~ v0100 的模組都指過來)· run 照 v0104", all(m.join is join and m.run is _v0104_run for m in (PRIOR, V0103, V0102, V0101, V0100)))
    try:
        import duckdb  # noqa: F401,WPS433
        have = True
    except ImportError:
        try:
            import pyarrow  # noqa: F401,WPS433
            have = True
        except ImportError:
            have = False
    D = datetime.date
    rd = D(2025, 11, 28)
    # a 正常 · b 分割(報告日前 Yahoo = TWSE × 0.25 · 2026-03-02 起一致)· c 不一致 · d 沒有報告日前 · e Yahoo 沒那天 · f 看不出調整點
    split = [{"date": D(2025, 11, 20) + datetime.timedelta(days=i), "close": 400.0 + i, "yf_close": (400.0 + i) * 0.25, "yf_adj_close": (400.0 + i) * 0.25 * 0.96, "close_check": "MISMATCH",
              "adjustment_status": "CLOSE_MISMATCH", "adj_close": None} for i in range(7)]
    split += [{"date": D(2026, 3, 2), "close": 120.0, "yf_close": 120.0, "yf_adj_close": 118.0, "close_check": "MATCH", "adjustment_status": "ADJUSTED", "adj_close": 118.0},
              {"date": D(2026, 10, 30), "close": 76.8, "yf_close": 76.8, "yf_adj_close": 76.8, "close_check": "MATCH", "adjustment_status": "ADJUSTED", "adj_close": 76.8}]
    g = sync_factor(split, rd)
    chk("③ b 分割:CLOSE_MISMATCH · 比值 0.25 一致 · 之後回到一致 → 同步還原 · 因子 = Yahoo 還原收盤 ÷ TWSE 收盤 = 0.24",
        g["mode"] == "SYNC_YAHOO_RATIO" and abs(g["factor"] - 0.24) < 1e-9 and g["before_date"] == "2025-11-26" and g["match_from"] == "2026-03-02" and "同步還原" in g["reason"])
    ok = [{"date": D(2025, 11, 27), "close": 100.0, "adj_close": 95.0, "yf_close": 100.0, "yf_adj_close": 95.0, "close_check": "MATCH", "adjustment_status": "ADJUSTED"}]
    chk("④ a VDF 已還原 → adj_close ÷ close(跟 MarketFetch 同規則)", sync_factor(ok, rd).get("mode") == "VDF_ADJUSTED" and abs(sync_factor(ok, rd)["factor"] - 0.95) < 1e-12)
    noisy = [dict(r) for r in split]
    noisy[3]["yf_close"] = noisy[3]["close"] * 0.30
    chk("⑤ c 報告日前比值不一致 → MISSING 不猜", sync_factor(noisy, rd)["mode"] == "MISSING" and "不一致" in sync_factor(noisy, rd)["reason"])
    late = [r for r in split if r["date"] >= D(2026, 1, 1)]
    chk("⑥ d 報告日前沒有日線 → MISSING(寫最早哪天 · 需回補)", sync_factor(late, rd)["mode"] == "MISSING" and "前沒有資料" in sync_factor(late, rd)["reason"] and "2026-03-02" in sync_factor(late, rd)["reason"])
    noy = [dict(split[-3], yf_close=None, yf_adj_close=None, close_check="MISSING")] + split[-2:]
    chk("⑦ e Yahoo 沒那天 → MISSING(close_check MISSING)", sync_factor(noy, rd)["mode"] == "MISSING" and "Yahoo 沒有" in sync_factor(noy, rd)["reason"])
    nostep = [dict(r) for r in split[:-2]]
    chk("⑧ f 報告日後沒有一天 Yahoo = TWSE → MISSING(看不出調整點)", sync_factor(nostep, rd)["mode"] == "MISSING" and "看不出調整點" in sync_factor(nostep, rd)["reason"])
    chk("⑨ 所有 MISSING 原因都以 MISSING( 開頭(RoundAll 的空格分類照舊歸資料源)", all(sync_factor(x, rd)["reason"].startswith("MISSING(") for x in (noisy, late, noy, nostep, [])))
    chk("⑩ 台北日期:UTC 2026-10-31T17:30Z → 2026-11-01 · 03:49Z → 2026-10-31", _taipei_day("2026-10-31T17:30:00+00:00") == D(2026, 11, 1) and _taipei_day("2026-10-31T03:49:24.262935+00:00") == D(2026, 10, 31))
    if not have:
        print("[SKIP] ⑪ ~ ⑱ 沒有 duckdb / pyarrow(讀寫 parquet)", flush=True)
    else:
        with tempfile.TemporaryDirectory(prefix="vrn2-cj105-") as td:
            v2 = Path(td) / "VIA_Reports" / "vrn2"
            (v2 / "output").mkdir(parents=True)
            (v2 / "consensus").mkdir()
            (v2 / "market").mkdir()
            for r in split:
                r.update(yfinance_ticker="3706.TW", bloomberg_ticker="3706 TT", name="神達", market="TWSE", volume=1000.0)
            _daily_fixture(v2, "3706", split)
            _daily_fixture(v2, "2330", [{"date": D(2026, 10, 30), "close": 1500.0, "adj_close": 1500.0, "yf_close": 1500.0, "yf_adj_close": 1500.0, "close_check": "MATCH",
                                          "adjustment_status": "ADJUSTED", "yfinance_ticker": "2330.TW", "bloomberg_ticker": "2330 TT", "name": "台積電", "market": "TWSE", "volume": 5.0}])
            basic = [{"FILENAME": "GS-3706.pdf", "REPORT_DATE": "2025-11-28", "TICKER": "3706", "TARGET_PRICE": "128", "NAME": "神達", "_STATUS": {}},
                     {"FILENAME": "a-2330.pdf", "REPORT_DATE": "2026-10-31", "TICKER": "2330", "TARGET_PRICE": "1800", "NAME": "台積電", "_STATUS": {}}]
            (v2 / "output" / "VRN2_BasicInfo_latest.json").write_text(json.dumps(basic, ensure_ascii=False), encoding="utf-8")
            mk = {"per_file": {"GS-3706.pdf": {"ticker": "3706", "adj_close": 76.8, "adj_close_date": "2026-10-30", "before_status": "MISSING(報告日前沒有日資料 · 需 --start 回補)", "status": "OK"},
                               "a-2330.pdf": {"ticker": "2330", "adj_close": 1500.0, "target_price_adj": 1800.0, "adjustment_factor_report": 1.0, "adj_close_before_report": 1500.0, "upside_pct_adj": 20.0, "status": "OK"}},
                  "per_ticker": {"3706": {"name": "神達", "yfinance_ticker": "3706.TW", "bloomberg_ticker": "3706 TT"}, "2330": {"name": "台積電", "yfinance_ticker": "2330.TW", "bloomberg_ticker": "2330 TT"}}}
            mtxt = json.dumps(mk, ensure_ascii=False)
            (v2 / "market" / "VRN2_Market_latest.json").write_text(mtxt, encoding="utf-8")
            (v2 / "market" / "vdf" / "status.json").write_text(json.dumps({"status": "PARTIAL", "issues": [], "datasets": {"daily": {"quality": {"REVIEW": 7, "OK": 2}}}}), encoding="utf-8")
            cons = {"year_n": 2026, "at": "2026-10-31T11:55:11", "per_code": {
                "3706": {"code": "3706", "company_name": "神達", "fetched_at_utc": "2026-10-31T03:49:28+00:00", "current_price": 76.8, "factset_target_median": 106.36, "factset_target_mean": 106.0,
                         "factset_analyst_count": "1", "factset_rate_date": "2026/07/21", "yf_target_median": 95.45, "yf_target_mean": 96.0, "yf_analyst_count": "4", "yf_current_price": 76.8,
                         "eps_median": {"2026": 6.39, "2027": 8.01}, "forward_pe": {"2026": 12.02}, "source_agreement_gate": "CONFLICT"},
                "2330": {"code": "2330", "company_name": "台積電", "fetched_at_utc": "2026-10-31T03:50:00+00:00", "factset_target_median": 1650.0, "yf_target_median": 1700.0,
                         "factset_analyst_count": "20", "yf_analyst_count": "30", "eps_median": {"2026": 60.0}, "source_agreement_gate": "PASS"}}}
            (v2 / "consensus" / CONSENSUS_JSON).write_text(json.dumps(cons, ensure_ascii=False), encoding="utf-8")
            got = join(v2)
            comb = {r["FILENAME"]: r for r in json.loads((v2 / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))}
            a = comb["GS-3706.pdf"]
            chk("⑪ join:3706 TARGET_PRICE(ADJ) = 128 × 0.24 = 30.72 · ADJ_CLOSE_BEFORE_REPORT = Yahoo 還原收盤 · UPSIDE_PCT(ADJ) 同一個因子 · STATUS 寫同步還原",
                a["TARGET_PRICE(ADJ)"] == "30.72" and a["ADJ_CLOSE_BEFORE_REPORT"] == _fmt(406.0 * 0.24) and a["UPSIDE_PCT(ADJ)"] == _fmt((30.72 / 76.8 - 1) * 100, 1)
                and "還原因子 0.240000" in a["STATUS"] and "同步還原" in a["STATUS"] and got.get("tp_adj_status_rows") == 1)
            chk("⑫ 已有 TARGET_PRICE(ADJ) 的(2330)不動 · 兩家中位數並存(FACTSET / YFINANCE 兩欄 · 欄序不變)",
                comb["a-2330.pdf"]["TARGET_PRICE(ADJ)"] == "1800.00" and a["FACTSET_TARGET_PRICE_MEDIAN"] == "106.36" and a["YFINANCE_TARGET_PRICE_MEDIAN"] == "95.45"
                and list(a.keys()) == columns(2026))
            chk("⑬ 磁碟上的 VRN2_Market_latest.json 一字不改 · 證據 market/VRN2_TPAdjSync_latest.json(SYNC 1 · VDF status PARTIAL · 3706 MISMATCH 7 列)",
                (v2 / "market" / "VRN2_Market_latest.json").read_text(encoding="utf-8") == mtxt and json.loads((v2 / "market" / SYNC_JSON).read_text(encoding="utf-8"))["counts"] == {"SYNC_YAHOO_RATIO": 1}
                and json.loads((v2 / "market" / SYNC_JSON).read_text(encoding="utf-8"))["vdf"]["status"] == "PARTIAL"
                and json.loads((v2 / "market" / SYNC_JSON).read_text(encoding="utf-8"))["vdf"]["tickers"]["3706"]["mismatch"] == 7)
            root = v2.joinpath(*DATASET_DIR)
            ds = got.get("consensus_dataset") or {}
            mc = parquet_rows([root / "tw_market_consensus.parquet"])
            byc = {r["ticker"]: r for r in mc}
            chk("⑭ TWSE / TPEX 格式:三個資料集 · 前五欄 = date · ticker · yfinance_ticker · bloomberg_ticker · name · 分區 ticker=/year= · 整合檔 + CSV 大寫表頭",
                all((root / ("%s.parquet" % n)).is_file() and (root / ("%s.csv" % n)).is_file() and (ds["datasets"][n]["identity"]) for n in COLS)
                and (root / "parquet" / "tw_consensus" / "ticker=3706" / "year=2026" / "data.parquet").is_file()
                and (root / "tw_consensus.csv").read_text(encoding="utf-8-sig").splitlines()[0].startswith("DATE,TICKER,YFINANCE TICKER,BLOOMBERG TICKER,NAME,MARKET,FACTSET TARGET PRICE MEDIAN"))
            chk("⑮ 合併:3706 取 2026-10-30 的 TWSE 收盤 / 還原收盤 · 兩家中位數並存 · 上漲空間各算 · 差距 % · 品質 CONFLICT → REVIEW",
                _day(byc["3706"]["price_date"]) == D(2026, 10, 30) and byc["3706"]["adj_close"] == 76.8 and byc["3706"]["factset_target_price_median"] == 106.36
                and byc["3706"]["yfinance_target_price_median"] == 95.45 and byc["3706"]["upside_factset_pct"] == round((106.36 / 76.8 - 1) * 100, 2)
                and byc["3706"]["median_gap_pct"] == round((106.36 / 95.45 - 1) * 100, 2) and byc["3706"]["quality"] == "REVIEW" and _day(byc["3706"]["date"]) == D(2026, 10, 31))
            old = merge_market(v2, [{"ticker": "3706", "date": D(2026, 3, 20), "factset_target_price_median": 100.0}], {"3706": split})
            chk("⑮b 合併只配 14 天內的收盤:3706 共識 2026-03-20 · 最近收盤 2026-03-02(18 天前)→ 價格欄空白(不拿舊價冒充)",
                old[0]["price_date"] is None and old[0]["adj_close"] is None and old[0]["upside_factset_pct"] is None)
            est = parquet_rows([root / "tw_consensus_estimate.parquet"])
            chk("⑯ EPS / 本益比 長表:主鍵 [date, ticker, fiscal_year, account] · 3706 三列 + 2330 一列",
                len(est) == 4 and {(r["ticker"], r["fiscal_year"], r["account"]) for r in est} >= {("3706", 2026, "diluted_eps_median"), ("3706", 2027, "diluted_eps_median"), ("3706", 2026, "forward_pe")})
            book = json.loads((v2 / "output" / ("VRN2_%s_latest.json" % BOOK_NAME)).read_text(encoding="utf-8"))
            chk("⑰ 這輪合併冊 output/VRN2_MarketConsensus_latest(json / csv)· 大寫欄名 · 日期 YYYY-MM-DD · 價格兩位",
                len(book) == 2 and book[0]["DATE"] == "2026-10-31" and book[0]["TICKER"] == "2330" and book[1]["ADJ_CLOSE"] == "76.80" and (v2 / "output" / ("VRN2_%s_latest.csv" % BOOK_NAME)).is_file())
            cons["per_code"]["3706"]["fetched_at_utc"] = "2026-11-01T03:00:00+00:00"
            cons["per_code"]["3706"]["yf_target_median"] = 97.0
            (v2 / "consensus" / CONSENSUS_JSON).write_text(json.dumps(cons, ensure_ascii=False), encoding="utf-8")
            join(v2)
            again = join(v2)
            mc2 = parquet_rows([root / "tw_market_consensus.parquet"])
            chk("⑱ 隔天再抓:新的一天加一列 · 同一天重跑新蓋舊(不重複)· 舊的那天保留(累計 3 列)",
                len(mc2) == 3 and again["consensus_dataset"]["datasets"]["tw_market_consensus"]["rows_total"] == 3
                and sorted((_day(r["date"]).isoformat(), r["ticker"]) for r in mc2) == [("2026-10-31", "2330"), ("2026-10-31", "3706"), ("2026-11-01", "3706")])
    print("[%s] %s %s --selftest · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest(argv[1] if len(argv) > 1 else None)
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
