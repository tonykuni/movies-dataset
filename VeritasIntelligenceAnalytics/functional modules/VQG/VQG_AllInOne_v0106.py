#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VeritaQuantGuard(VQG)v0106 — v0105 薄尾(v0105 一字不改 · SHA-256 釘在 PRIOR_SHA256)。

VQG 是獨立系統:只讀 VDF 的資料庫 · 不寫 VDF 的夾 · 不連網 · 技術指標唯一正主 = QuantGuard(政策 L50 · 不用 TA-Lib)。
公式 / 三解 / 驗證 / 曆 / 批次全照 v0104 + v0105(calculate · validate_frame · load_series · run_local 一字不動)。

為什麼要 v0106(操作員 2026-11-06:「實測輸出增量 PARQUET 維護資料庫後 · VQG 擷取自資料庫檔案夾整理全部 · 無論有無加工計算 ·
統一輸出資料到其他應用如 VAP」):
  v0104 / v0105 只會「一次算一張票、--export-dir 丟一夾 vqg_<uuid>/vqg_result.parquet」;VAP(VeritasAutoPlot)要的是
  「VQG 正式輸入 + 連線證據(VIA-VQG-VAP-CONNECTION-MANIFEST/1.0 · 每筆連線帶 SHA-256 指紋)」,而且 VAP 的 HTML U/I 一張表 = 一條時間軸
  (x 不重複 · 升冪 · 至少 2 個數值欄 · 至少 3 列),兩邊沒有接口。

v0106 加一個動詞 export-vap(其餘動詞原樣交 v0105):
  python VQG_AllInOne_v0106.py export-vap [--root <VDF 庫根>] [--out-dir <輸出夾>] [--ticker T …] [--max-tickers N(預設 50 · 0 = 全部)]
                                          [--metrics sma rsi macd …] [--windows …] [--as-of YYYY-MM-DD] [--series-rows N] [--indicator-points N(預設 60)]
                                          [--calendar vdf|derive|auto] [--snapshots strict|latest] [--market TW|US] [--vap-port 8765]
  ① 整理全部:VDF 庫夾裡每一個 parquet(認得的 / 不認得的 / 被新批次取代的)列成 vqg_vdf_catalog.json(路徑 · 大小 · 批次戳 · 欄位 · 列數 · 票樣本 · SHA-256)。
  ② 無加工(SERIES):每張票的日線(還原價 adj_close · 量 · 值 · 市場 · 交易日序號 · 可用日)經 v0105 的 load_series 原樣倒出:
     series/<票>.parquet(+ .csv · 一票一表 · x = date · 全空的欄不列 · 值不補不改)給 VAP;vqg_series.parquet(+ .csv · 全部票長表)給其他應用。
     同表多批次照 --snapshots latest 只取最新;曆照 --calendar(預設 auto:嚴格先試 · 缺曆才推)。
  ③ 有加工(INDICATOR_RESULT):每張票跑 v0105 run_local(預設 sma rsi macd · 三解 · 驗證):
     indicators/<票>.parquet(+ .csv · 一票一表 · x = observation_date · 最近 --indicator-points 個交易日各算一次 · 欄 = <指標>_<窗>_<解>(例 SMA_20_S1)· 結構值展開 <欄>_<分量>(例 MACD_26_S1_line / _signal / _histogram)·
     截止日照市場(台股 = 觀測日隔天 · 美股 = 當日)· 觀測日不超過 --as-of · 無效值留空)給 VAP;
     vqg_indicator_results.parquet(+ .csv · as-of 當天的快照 · 欄位 = v0104 FIELDS 23 欄 · 長表)給其他應用;
     --out-dir 下既有的 vqg_<uuid>/vqg_result.parquet(v0104 calc --export-dir 丟的)一併合進長表(同 request_key + solution_id + observation_date 去重)。
  ④ 連線證據:vqg_connection_manifest.json(schema VIA-VQG-VAP-CONNECTION-MANIFEST/1.0 · 每張 VAP 表一筆 · state AUTHORIZED · readOnly · engine PARQUET ·
     sourceSystem VQG · datasetType SERIES / INDICATOR_RESULT · limits = v0104 的 5000 / 100 / 252 · xField · fieldSemantics(每個數值欄)· upstreamEvidence
     (ADJUSTED_PRICE_ONLY · CALCULATE_ONLY_NO_FETCH · 曆模式 · 批次模式 · VDF 庫根與依據)· fingerprint = sha256(去 fingerprint 後 sort_keys 緊湊 JSON) —— 照 VAP v0300 的驗法);
     vdf_connection_manifest.json(VDF 直連 VAP 不走 · connections 空 · VQG 才是 VAP 的正式輸入);VAP_AllInOne_v0300.config.json(每張表一個來源 ·
     authority VQG · allowedRoots 含輸出夾 · loopback)。VAP 啟動:python VAP_AllInOne_v03xx.py --config <輸出夾>\VAP_AllInOne_v0300.config.json。
  ⑤ 收據:export_receipt.json(每張表帶 VAP U/I 閘的預檢:列數 · x 不重複升冪 · 數值欄 ≥ 2)+ SHA256SUMS.txt(輸出夾)· VQG_ExportVAP_latest.json
     (<VIA 根>\VIA_Reports\vqg\)· 一行燈 + 下一步。
  邊界:輸出夾 / 收據夾不准在 VDF 庫裡(OUTPUT_INSIDE_SOURCE_ROOT · rc 2 · 連收據都不寫)· 跑前跑後核對 VDF 庫檔案清單與 mtime 一字沒動(收據 vdf_root_untouched)·
        前版 v0105 位元組被改過 → 不匯出(rc 2 · 血統要乾淨才能給別的應用)· 零網路(本檔不匯入任何網路模組 · VIA:NET-BRIDGE 不適用)· 不 import VAP。
  燈:GREEN = 全部票匯出且曆嚴格;YELLOW = 曆是推的(VDF 日線缺 session_index / available_on / market)或有票跳過 / 截斷;RED = 一張票都沒匯出 / 邊界違反。
自測:python VQG_AllInOne_v0106.py selftest(v0105 自測 + 本版 12 項 · 零網路 · 只在 tempfile 沙盒寫 · 跑 v0105 自測時暫時拿掉 $env:VQG_VDF_ROOT · 不然 v0105 ⑩ 會誤判)。
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import types
from datetime import date, datetime, timedelta
from pathlib import Path

VERSION_TAIL = "v0106"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VQG_AllInOne_v0105.py"
PRIOR_SHA256 = "cc050f0fe42786f7113dbf0dd920d954feaf0b020e216456f336ce0d30801619"   # v0105 入倉版(2026-11-04)
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(v0106 是 v0105 的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("vqg_v0105_for_v0106", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
pl = PRIOR.pl
ENGINE_VERSION = PRIOR.ENGINE_VERSION                                    # "v0104"(公式引擎)

# ── VAP 契約常數(抄 VAP v0300 的驗法 · 不 import VAP · 兩系統獨立)──────────────
VAP_VQG_SCHEMA = "VIA-VQG-VAP-CONNECTION-MANIFEST/1.0"
VAP_VDF_SCHEMA = "VIA-VDF-VAP-CONNECTION-MANIFEST/1.0"
VAP_CONFIG_SCHEMA = "VIA-VAP-RUNTIME-CONFIG/1.0"
VAP_CONFIG_NAME = "VAP_AllInOne_v0300.config.json"
VAP_UI_MIN_ROWS = 3                                                      # VAP U/I validateCatalogTable:MIN_COMPLETE_ROWS
SERIES_FIELDS = ["adj_close", "volume", "turnover", "daytrade_volume", "daytrade_turnover", "clean_volume", "clean_turnover", "market", "session_index", "available_on"]
SERIES_NUMERIC = ["adj_close", "volume", "turnover", "daytrade_volume", "daytrade_turnover", "clean_volume", "clean_turnover", "session_index"]
DEFAULT_METRICS = ["sma", "rsi", "macd"]
SHA_SMALL_FILE = 64 * 1024 * 1024
_SAFE = re.compile(r"[^0-9A-Za-z_\-]+")


def vap_fingerprint(connection: dict) -> str:
    """= VAP def_connection_fingerprint:去掉 fingerprint 後 sort_keys · 緊湊分隔 · ensure_ascii=False 的 JSON 的 SHA-256(先過一次 json 來回 · 跟 VAP 讀檔後算的一樣)。"""
    payload = json.loads(json.dumps({k: v for k, v in connection.items() if k != "fingerprint"}, ensure_ascii=False, default=str))
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _tree_signature(root: Path) -> list:
    """VDF 庫檔案清單 + 大小 + mtime(跑前跑後比 · 證明一字沒動)。"""
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            st = p.stat()
            out.append((str(p.relative_to(root)), st.st_size, st.st_mtime_ns))
    return out


def safe_name(ticker: str) -> str:
    return _SAFE.sub("_", str(ticker)).strip("_") or "TICKER"


def ui_gate(frame, x: str) -> dict:
    """VAP U/I 閘的預檢(照 UI validateCatalogTable):列 ≥ 3 · x 在 · x 不重複 · x 升冪 · 數值欄 ≥ 2(x 除外)→ {gate, failures, rows, numeric}。"""
    fails = []
    if frame.height < VAP_UI_MIN_ROWS:
        fails.append("ROWS_LT_%d" % VAP_UI_MIN_ROWS)
    if x not in frame.columns:
        fails.append("X_AXIS_MISSING")
        xs = []
    else:
        xs = [v for v in frame[x].to_list() if v is not None]
        if len(set(xs)) != len(xs):
            fails.append("DUPLICATE_TIME_KEY")
        if xs != sorted(xs):
            fails.append("TIME_NOT_SORTED")
    numeric = [c for c, t in zip(frame.columns, frame.dtypes) if c != x and (t.is_numeric()) and frame[c].null_count() < frame.height]
    if len(numeric) < 2:
        fails.append("NUMERIC_PAIR_MISSING")
    return {"gate": "FAIL" if fails else "PASS", "failures": fails, "rows": frame.height, "numeric": numeric}


def all_tickers(sources, cap: int = 50) -> tuple:
    """日線檔(最新批次)裡出現過的票 · 去重排序;cap > 0 時只取前 cap 張 → (票, 總數)。"""
    seen = set()
    kept, _ = PRIOR.latest_snapshots(sources)
    for path, cols in PRIOR._daily_price_sources(kept):
        vals = pl.scan_parquet(path).select(pl.col(cols["ticker"]).cast(pl.String)).unique().collect().to_series().to_list()
        seen |= {str(v).strip().upper() for v in vals if v is not None and str(v).strip()}
    tickers = sorted(seen)
    return (tickers[:cap] if cap and cap > 0 else tickers), len(tickers)


def vdf_catalog(root: Path, sources, errors) -> list:
    """① 整理全部:VDF 庫夾每一個 parquet 一列(認得 / 不認得 / 被取代)· 只讀。"""
    recognized = {str(p): c for p, c in sources}
    kept, dropped = PRIOR.latest_snapshots(sources)
    dropped = set(dropped)
    bad = {name: kind for name, kind in errors}
    rows = []
    for p in sorted(root.rglob("*.parquet")):
        if not p.resolve().is_relative_to(root.resolve()):
            continue
        fam, ts = PRIOR.snapshot_family(p)
        rel = str(p.relative_to(root))
        st = p.stat()
        row = {"file": rel, "bytes": st.st_size, "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
               "table": fam[1], "snapshot": ts or None, "superseded": str(p) in dropped,
               "recognized": str(p) in recognized, "columns": sorted(recognized.get(str(p), {}).keys()) if str(p) in recognized else [],
               "unreadable": bad.get(rel), "sha256": _sha256_file(p) if st.st_size <= SHA_SMALL_FILE else None}
        try:
            row["rows"] = int(pl.scan_parquet(p).select(pl.len()).collect().item())
            cols = recognized.get(str(p)) or {}
            if "ticker" in cols:
                row["tickers_sample"] = pl.scan_parquet(p).select(pl.col(cols["ticker"]).cast(pl.String)).unique().limit(8).collect().to_series().to_list()
        except Exception as error:  # noqa: BLE001  壞檔也列出來(不中斷整理)
            row["rows"] = None
            row["unreadable"] = row.get("unreadable") or type(error).__name__
        rows.append(row)
    return rows


def _series_schema(keys: list) -> dict:
    schema = {"date": pl.Date, "ticker": pl.String}
    for k in keys:
        schema[k] = pl.Date if k == "available_on" else pl.Int64 if k == "session_index" else pl.String if k in ("market", "benchmark_market") else pl.Float64
    schema["source_files"] = pl.String
    schema["engine_version"] = pl.String
    return schema


def export_series(sources, tickers: list, as_of, cal: str, snaps: str, forced, tail_rows: int) -> tuple:
    """② 無加工:每張票經 v0105 load_series 原樣倒出 → (長表 frame, {票: 一票一表 frame}, per_ticker, skipped, sessions{票: [date]})。"""
    kept, _ = PRIOR.latest_snapshots(sources) if snaps == "latest" else (sources, [])
    files = sorted({p.name for p, c in PRIOR._daily_price_sources(kept)})
    rows, per, skipped, per_frames, sessions = [], {}, {}, {}, {}
    tag = PRIOR.DERIVED_TAG if cal == "derive" else ENGINE_VERSION
    for tk in tickers:
        stats = {}
        PRIOR._CTX.update(calendar=cal, snapshots=snaps, market=forced, stats=stats)
        try:
            recs = PRIOR.load_series(sources, tk, SERIES_FIELDS, as_of, None, "daily", True, tail_rows)
        except (ValueError, OSError) as error:
            skipped[tk] = str(error)[:200]
            continue
        finally:
            PRIOR._CTX.update(calendar="vdf", snapshots="strict", market=None, stats=None)
        if not recs:
            skipped[tk] = "NO_ROWS"
            continue
        tk_rows = []
        for r in recs:
            row = {"date": r["date"], "ticker": tk}
            for k in SERIES_FIELDS:
                row[k] = r.get(k)
            row["source_files"] = " ".join(files)
            row["engine_version"] = tag
            tk_rows.append(row)
        rows.extend(tk_rows)
        per[tk] = len(recs)
        sessions[tk] = [r["date"] for r in recs if r.get("adj_close") is not None]
        f = pl.DataFrame(tk_rows, schema=_series_schema(SERIES_FIELDS)).sort("date")
        keep = ["date"] + [c for c in SERIES_FIELDS if f[c].null_count() < f.height] + ["source_files", "engine_version"]   # 全空的欄不列(整理 · 不是加工)
        per_frames[tk] = f.select(keep)
    frame = pl.DataFrame(rows, schema=_series_schema(SERIES_FIELDS)) if rows else pl.DataFrame(schema=_series_schema(SERIES_FIELDS))
    return frame, per_frames, per, skipped, sessions


def _indicator_schema() -> dict:
    return {k: {"VARCHAR": pl.String, "DOUBLE": pl.Float64, "DATE": pl.Date, "BOOLEAN": pl.Boolean, "INTEGER": pl.Int32}[t] for k, t in PRIOR.FIELDS.items()}


def _ind_col(row: dict) -> str:
    return "%s_%s_%s" % (str(row.get("indicator_id", "")).split(".")[-1], row.get("window_n"), row.get("solution_id"))


def _ind_values(row: dict) -> dict:
    """一列指標 → {欄名: 數值}:純量 = value_num;結構值(MACD line / signal / histogram · bollinger …)從 value_json 展開成 <欄>_<分量>(無效 → None)。"""
    base = _ind_col(row)
    if not row.get("valid"):
        return {base: None}
    if row.get("value_num") is not None:
        return {base: float(row["value_num"])}
    try:
        obj = json.loads(row.get("value_json") or "null")
    except ValueError:
        obj = None
    if isinstance(obj, dict):
        return {"%s_%s" % (base, k): (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None) for k, v in obj.items()}
    return {base: float(obj) if isinstance(obj, (int, float)) and not isinstance(obj, bool) else None}


def _cutoff_for(ticker: str, day, forced):
    """算 day 這個觀測日要給的 as-of:台股照 v0104「只用 as-of 前一日以前」→ day + 1;美股 as-of 當日含 → day。"""
    mkt = forced or PRIOR._market_of_ticker(ticker) or "TW"
    return day + timedelta(days=1) if mkt == "TW" else day


def export_indicators(sources, tickers: list, metrics: list, windows, as_of, cal: str, snaps: str, forced, root: Path, sessions: dict, points: int) -> tuple:
    """③ 有加工:每張票 (a) as-of 快照(長表 · v0104 FIELDS)(b) 最近 points 個交易日各跑一次 run_local → 一票一表(x = observation_date · 欄 = 指標_窗_解)。"""
    snap_rows, per, skipped, modes, per_frames, meta = [], {}, {}, set(), {}, {}

    def once(tk, day):
        a = types.SimpleNamespace(root=root, ticker=tk, metrics=list(metrics), windows=windows, as_of=day, start=None, report_id=None,
                                  cache_dir=None, calendar=cal, snapshots=snaps, market=forced)
        return PRIOR.run_local(sources, a)
    for tk in tickers:
        try:
            got, st = once(tk, as_of)
        except (ValueError, OSError) as error:
            skipped[tk] = str(error)[:200]
            continue
        modes.add((st.get("calendar") or {}).get("mode") or "vdf")
        snap_rows.extend(got)
        per[tk] = len(got)
        days = [d for d in (sessions.get(tk) or []) if d <= as_of]
        wide, cols_meta = {}, {}
        for day in (days[-points:] if points > 0 else []):
            cut = _cutoff_for(tk, day, forced)                                 # 截止日照市場(TW = day + 1 · US = day)· 觀測日 = day
            if cut > as_of:                                                    # 截止日不得超過 --as-of(台股 as-of 當天的價照 v0104 不用 · 最後觀測日 = 前一交易日)
                continue
            try:
                rows_d, _ = once(tk, cut)
            except (ValueError, OSError):
                continue
            for r in rows_d:
                od = r.get("observation_date")
                if od is None or od > as_of:                                   # 觀測日不得超過 --as-of(Codex P1:美股截止含當日 · 歷史匯出不漏未來)
                    continue
                for c, v in _ind_values(r).items():
                    wide.setdefault(od, {"observation_date": od})[c] = v
                    cols_meta.setdefault(c, {"indicatorId": r.get("indicator_id"), "window": r.get("window_n"), "solution": r.get("solution_id"), "estimator": r.get("estimator"), "unit": r.get("unit"),
                                             "component": c[len(_ind_col(r)) + 1:] or None})
        if wide:
            cols = sorted(cols_meta)
            schema = {"observation_date": pl.Date, **{c: pl.Float64 for c in cols}}
            f = pl.DataFrame([{**{c: None for c in cols}, **w} for _, w in sorted(wide.items())], schema=schema)
            per_frames[tk] = f
            meta[tk] = cols_meta
    snap = pl.DataFrame(snap_rows, schema=_indicator_schema()) if snap_rows else pl.DataFrame(schema=_indicator_schema())
    return snap, per_frames, meta, per, skipped, modes


def merge_prior_snapshots(frame, out_root: Path) -> tuple:
    """--out-dir 下既有 vqg_<uuid>/vqg_result.parquet(v0104 calc --export-dir)合進來 · 去重 → (frame, 合入檔數, 合入列數)。"""
    extra, n_files = [], 0
    for p in sorted(out_root.glob("vqg_*/vqg_result.parquet")):
        try:
            extra.append(pl.read_parquet(p).select(list(PRIOR.FIELDS.keys())).cast(_indicator_schema()))
            n_files += 1
        except Exception:  # noqa: BLE001  壞的快照略過(收據會寫數量差)
            continue
    if not extra:
        return frame, 0, 0
    merged = pl.concat([frame] + extra, how="vertical").unique(subset=["request_key", "solution_id", "observation_date", "indicator_id", "window_n", "ticker"], keep="first", maintain_order=True)
    return merged, n_files, merged.height - frame.height


def _sem(stable: str, subject: str, unit: str, dtype: str, role: str) -> dict:
    return {"stableId": stable, "subject": subject, "unit": unit, "dataType": dtype, "frequency": "DAILY", "role": role}


def series_semantics(frame) -> dict:
    out = {"date": _sem("VQG.FIELD.DATE", "Trading Date", "Date", "Date", "X_TIME")}
    for c in frame.columns:
        if c == "adj_close":
            out[c] = _sem("VQG.SERIES.ADJ_CLOSE", "Adjusted Close(VDF)", "Price", "Decimal", "LEFT_VALUE")
        elif c in ("volume", "clean_volume", "daytrade_volume"):
            out[c] = _sem("VQG.SERIES." + c.upper(), c.replace("_", " ").title() + "(VDF as-is)", "Shares", "Decimal", "RIGHT_VALUE")
        elif c in ("turnover", "clean_turnover", "daytrade_turnover"):
            out[c] = _sem("VQG.SERIES." + c.upper(), c.replace("_", " ").title() + "(VDF as-is)", "TWD", "Decimal", "RIGHT_VALUE")
        elif c == "session_index":
            out[c] = _sem("VQG.SERIES.SESSION_INDEX", "Session Index(trading-day ordinal)", "Count", "Integer", "RIGHT_VALUE")
    return out


def indicator_semantics(cols_meta: dict) -> dict:
    out = {"observation_date": _sem("VQG.FIELD.OBSERVATION_DATE", "Observation Date", "Date", "Date", "X_TIME")}
    for c, m in cols_meta.items():
        out[c] = dict(_sem("VQG.IND.%s" % c, "%s %s · %s %s%s" % (str(m.get("indicatorId", "")).split(".")[-1], m.get("window"), m.get("solution"), m.get("estimator") or "", (" · " + m["component"]) if m.get("component") else ""), str(m.get("unit") or "value"), "Decimal", "LEFT_VALUE"), indicatorId=m.get("indicatorId"))
    return out


def build_connection(contract_id: str, source_id: str, dataset_type: str, x_field: str, semantics: dict, data_path: Path, rows: int, cal: str, snaps: str, root: Path, how: str, at: str, ticker: str) -> dict:
    c = {"contractId": contract_id, "sourceId": source_id, "state": "AUTHORIZED", "readOnly": True, "engine": "PARQUET", "sourceSystem": "VQG",
         "vqgVersion": VERSION_TAIL, "formulaEngine": ENGINE_VERSION, "datasetType": dataset_type, "producerInputs": ["VDF"], "ticker": ticker,
         "limits": {"maxInputRows": int(PRIOR.MAX_INPUT_ROWS), "maxOutputRows": int(PRIOR.MAX_OUTPUT_ROWS), "maxWindow": int(PRIOR.MAX_WINDOW)},
         "xField": x_field, "fieldSemantics": semantics, "dataFile": str(data_path.relative_to(data_path.parent.parent)).replace("\\", "/"), "dataSha256": _sha256_file(data_path), "rows": int(rows),
         "upstreamEvidence": {"vdfAuthorized": True, "vdfRoot": str(root), "vdfRootFrom": how, "pricePolicy": "ADJUSTED_PRICE_ONLY",
                              "volumePolicy": "VDF_AS_IS_NO_VQG_FILL", "taLibPolicy": "CALCULATE_ONLY_NO_FETCH",
                              "indicatorEngine": "QuantGuard VQG %s(政策 L50 · 不用 TA-Lib)" % ENGINE_VERSION,
                              "calendarVerified": cal == "vdf", "calendarMode": cal, "snapshots": snaps, "network": "NONE"},
         "authorizedAt": at}
    c["fingerprint"] = vap_fingerprint(c)
    return c


def build_vap_config(export_dir: Path, out_root: Path, port: int, sources: list) -> dict:
    return {"schema": VAP_CONFIG_SCHEMA, "version": "VQG %s export-vap" % VERSION_TAIL, "host": "127.0.0.1", "port": int(port), "openBrowser": True, "syncConnectOnStart": True,
            "maxRows": int(PRIOR.MAX_INPUT_ROWS), "formalInputAuthority": "VQG", "allowedRoots": ["{PACKAGE_ROOT}", str(out_root), str(export_dir)], "allowedHosts": [],
            "vdfGateway": {"required": True, "manifest": str(export_dir / "vdf_connection_manifest.json")},
            "vqgGateway": {"required": True, "manifest": str(export_dir / "vqg_connection_manifest.json")},
            "sources": sources}


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def _write_table(frame, path: Path) -> None:
    frame.write_parquet(path, compression="zstd")
    frame.write_csv(path.with_suffix(".csv"), include_bom=True, date_format="%Y/%m/%d")


def export_vap(args) -> int:
    """export-vap 本體(args = SimpleNamespace · 見 main)。回 rc:0 GREEN / YELLOW · 2 RED。"""
    t0 = datetime.now()
    via = PRIOR.via_root(getattr(args, "via_root", None))
    if getattr(args, "root", None):
        root, how = Path(args.root), "--root"
    else:
        root, how = PRIOR.default_root(via)
    out_root = Path(getattr(args, "out_dir", None) or ((via / "VIA_Reports" / "vqg" / "vap_export") if via else Path.cwd() / "VIA_Reports" / "vqg" / "vap_export"))
    receipt_dir = Path(getattr(args, "receipt_dir", None) or ((via / "VIA_Reports" / "vqg") if via else Path.cwd() / "VIA_Reports" / "vqg"))
    receipt_ok = [True]                                                      # 收據夾在 VDF 庫裡 → False:finish 只印不寫(Codex P1 · 邊界不能被收據破)
    rec = {"system": "VQG", "verb": "export-vap", "engine": "VeritaQuantGuard " + VERSION_TAIL, "formula_engine": ENGINE_VERSION, "prior_sha_ok": PRIOR_SHA_OK,
           "at": t0.isoformat(timespec="seconds"), "via_root": str(via or ""), "vdf_root": str(root), "vdf_root_from": how, "out_root": str(out_root),
           "rule": "VQG 只讀 VDF 庫 · 不連網 · 不寫 VDF 的夾 · 輸出夾不在 VDF 庫裡 · VAP 只拿 VQG 的正式輸出(連線證據帶指紋)· 一票一表 = VAP U/I 一條時間軸", "steps": []}

    def step(name, lamp, detail):
        rec["steps"].append({"step": name, "lamp": lamp, "detail": detail})
        print("[%s] %s · %s" % (lamp, name, detail), flush=True)

    def finish(lamp, meaning, next_step=""):
        rec["lamp"] = lamp
        rec["meaning"] = meaning
        rec["elapsed_s"] = round((datetime.now() - t0).total_seconds(), 1)
        if not receipt_ok[0]:
            print("[%s] VQG export-vap · %s · 收據沒寫(收據夾 %s 在 VDF 庫裡 · VQG 不寫 VDF 的夾)· %.1f 秒%s" % (lamp, meaning, receipt_dir, rec["elapsed_s"], (" · 下一步:" + next_step) if next_step else ""), flush=True)
            return 0 if lamp in ("GREEN", "YELLOW") else 2
        with contextlib.suppress(OSError):
            receipt_dir.mkdir(parents=True, exist_ok=True)
            body = json.dumps(rec, ensure_ascii=False, indent=1, default=str)
            (receipt_dir / "VQG_ExportVAP_latest.json").write_text(body, encoding="utf-8")
            (receipt_dir / ("VQG_ExportVAP_%s.json" % t0.strftime("%Y%m%d_%H%M%S"))).write_text(body, encoding="utf-8")
        print("[%s] VQG export-vap · %s · 收據 %s · %.1f 秒%s" % (lamp, meaning, receipt_dir / "VQG_ExportVAP_latest.json", rec["elapsed_s"], (" · 下一步:" + next_step) if next_step else ""), flush=True)
        return 0 if lamp in ("GREEN", "YELLOW") else 2

    if not PRIOR_SHA_OK:
        step("⓪ 血統", "RED", "前版 %s 位元組跟 PRIOR_SHA256 不符(被改過)· 不匯出" % PRIOR_NAME)
        return finish("RED", "前版被改過 · 血統不乾淨 · 不給別的應用", "git checkout -- \"functional modules/VQG/%s\"" % PRIOR_NAME)
    if not root.is_dir():
        step("① VDF 庫", "RED", "VDF 庫根不在:%s(%s)" % (root, how))
        return finish("RED", "沒有 VDF 庫", "--root <VDF 庫根> 或 $env:VQG_VDF_ROOT")
    root = root.resolve()
    if receipt_dir.resolve().is_relative_to(root):
        receipt_ok[0] = False
    if out_root.resolve().is_relative_to(root) or not receipt_ok[0]:
        step("① 邊界", "RED", "OUTPUT_INSIDE_SOURCE_ROOT:輸出夾 / 收據夾在 VDF 庫裡(%s · %s)· VQG 只讀 VDF · 不寫 · 收據也不寫" % (out_root, receipt_dir))
        return finish("RED", "輸出夾不准在 VDF 庫裡", "--out-dir 指到 VDF 庫外(預設 <VIA 根>\\VIA_Reports\\vqg\\vap_export)")
    sig_before = _tree_signature(root)
    sources, errors = PRIOR.discover(root)
    doc = PRIOR.doctor(root)
    rec["doctor"] = {k: doc.get(k) for k in ("verdict", "files", "daily_price_files", "missing_for_strict", "multi_snapshot_tables", "unreadable")}
    if doc["verdict"] not in ("STRICT_READY", "DERIVE_READY"):
        step("① VDF 庫就緒(%s)" % how, "RED", "%s · %s" % (doc["verdict"], doc.get("next") or doc.get("why")))
        return finish("RED", "VDF 庫裡沒有日線 parquet(ticker + date + adj_close)", str(doc.get("next") or "")[:200])
    cal_opt = getattr(args, "calendar", None) or "auto"
    cal = cal_opt if cal_opt in ("vdf", "derive") else ("vdf" if doc["verdict"] == "STRICT_READY" else "derive")
    snaps = getattr(args, "snapshots", None) or "latest"
    forced = getattr(args, "market", None)
    as_of = getattr(args, "as_of", None) or date.today()
    points = max(0, int(getattr(args, "indicator_points", 60) or 0))
    step("① VDF 庫就緒(%s)" % how, "GREEN" if doc["verdict"] == "STRICT_READY" else "YELLOW",
         "%s · %s · parquet %s · 日線檔 %s · 曆 %s · 批次 %s · as-of %s" % (doc["verdict"], root, doc.get("files"), doc.get("daily_price_files"), cal, snaps, as_of))
    wanted = [str(t).strip().upper() for t in (getattr(args, "ticker", None) or []) if str(t).strip()]
    cap = int(getattr(args, "max_tickers", 50) or 0)
    if wanted:
        tickers, total = wanted, len(wanted)
    else:
        tickers, total = all_tickers(sources, cap)
    rec["tickers"] = {"requested": wanted, "exported_candidates": tickers, "in_vdf": total, "cap": cap}
    if not tickers:
        step("② 票", "RED", "VDF 日線裡一張票都沒有")
        return finish("RED", "沒有票可匯出", "VDF 線先回填日線")
    truncated = len(tickers) < total and not wanted
    step("② 票", "YELLOW" if truncated else "GREEN", "%d 張(VDF 裡 %d 張%s)" % (len(tickers), total, (" · --max-tickers %d 截斷 · 0 = 不截" % cap) if truncated else ""))
    stamp = t0.strftime("%Y%m%d_%H%M%S")
    out_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".vap_export-", dir=out_root))
    final = out_root / ("vap_export_%s" % stamp)
    try:
        catalog = vdf_catalog(root, sources, errors)
        _write_json(stage / "vqg_vdf_catalog.json", {"schema": "VIA-VQG-VDF-CATALOG/1.0", "vqgVersion": VERSION_TAIL, "vdfRoot": str(root), "vdfRootFrom": how, "at": rec["at"],
                                                      "files": len(catalog), "recognized": sum(1 for r in catalog if r["recognized"]), "superseded": sum(1 for r in catalog if r["superseded"]),
                                                      "unreadable": sum(1 for r in catalog if r.get("unreadable")), "entries": catalog})
        rec["catalog"] = {"files": len(catalog), "recognized": sum(1 for r in catalog if r["recognized"]), "superseded": sum(1 for r in catalog if r["superseded"]), "unreadable": sum(1 for r in catalog if r.get("unreadable"))}
        step("③ 整理全部(VDF 庫夾)", "GREEN", "parquet %d · 認得 %d · 被新批次取代 %d · 讀不了 %d → vqg_vdf_catalog.json" % (len(catalog), rec["catalog"]["recognized"], rec["catalog"]["superseded"], rec["catalog"]["unreadable"]))
        # ④ 無加工 SERIES
        tail_rows = max(10, min(int(getattr(args, "series_rows", 0) or (PRIOR.MAX_INPUT_ROWS - 1)), int(PRIOR.MAX_INPUT_ROWS) - 1))
        s_long, s_frames, s_per, s_skip, sessions = export_series(sources, tickers, as_of, cal, snaps, forced, tail_rows)
        (stage / "series").mkdir()
        _write_table(s_long, stage / "vqg_series.parquet")
        tables, vap_sources, conns = [], [], []
        at = t0.strftime("%Y-%m-%dT%H:%M:%S")
        for tk, f in s_frames.items():
            p = stage / "series" / (safe_name(tk) + ".parquet")
            _write_table(f, p)
            g = ui_gate(f, "date")
            tables.append({"ticker": tk, "kind": "SERIES", "file": "series/" + p.name, "rows": f.height, "columns": f.columns, "ui_gate": g})
            if g["gate"] == "PASS":
                sid = "VQG-SERIES-" + safe_name(tk)
                conns.append(build_connection("VQG-SERIES-v1", sid, "SERIES", "date", series_semantics(f), final / "series" / p.name if False else p, f.height, cal, snaps, root, how, at, tk))
                vap_sources.append({"id": sid, "vqgContractId": "VQG-SERIES-v1", "authority": "VQG", "alias": "VQG_SERIES_" + safe_name(tk), "engine": "PARQUET",
                                    "location": str(final / "series" / p.name), "table": "series_" + safe_name(tk), "enabled": True, "maxRows": int(PRIOR.MAX_INPUT_ROWS)})
        rec["series"] = {"long_rows": s_long.height, "tickers": len(s_per), "skipped": s_skip, "rows_per_ticker_cap": tail_rows, "ui_gate_pass": sum(1 for t in tables if t["ui_gate"]["gate"] == "PASS")}
        step("④ 無加工 SERIES", "GREEN" if s_per and not s_skip else ("YELLOW" if s_per else "RED"), "一票一表 %d(VAP 閘過 %d)· 長表 %d 列 · 跳過 %d%s → series/<票>.parquet · vqg_series.parquet" % (
            len(s_frames), rec["series"]["ui_gate_pass"], s_long.height, len(s_skip), (" · " + " / ".join("%s:%s" % (k, v[:40]) for k, v in list(s_skip.items())[:3])) if s_skip else ""))
        # ⑤ 有加工 INDICATOR_RESULT
        metrics = list(getattr(args, "metrics", None) or DEFAULT_METRICS)
        i_snap, i_frames, i_meta, i_per, i_skip, modes = export_indicators(sources, tickers, metrics, getattr(args, "windows", None), as_of, cal, snaps, forced, root, sessions, points)
        i_snap, n_merge_files, n_merge_rows = merge_prior_snapshots(i_snap, out_root)
        (stage / "indicators").mkdir()
        _write_table(i_snap, stage / "vqg_indicator_results.parquet")
        for tk, f in i_frames.items():
            p = stage / "indicators" / (safe_name(tk) + ".parquet")
            _write_table(f, p)
            g = ui_gate(f, "observation_date")
            tables.append({"ticker": tk, "kind": "INDICATOR_RESULT", "file": "indicators/" + p.name, "rows": f.height, "columns": f.columns, "ui_gate": g})
            if g["gate"] == "PASS":
                sid = "VQG-INDICATOR-" + safe_name(tk)
                conns.append(build_connection("VQG-INDICATOR-v1", sid, "INDICATOR_RESULT", "observation_date", indicator_semantics(i_meta[tk]), p, f.height, cal, snaps, root, how, at, tk))
                vap_sources.append({"id": sid, "vqgContractId": "VQG-INDICATOR-v1", "authority": "VQG", "alias": "VQG_INDICATOR_" + safe_name(tk), "engine": "PARQUET",
                                    "location": str(final / "indicators" / p.name), "table": "indicators_" + safe_name(tk), "enabled": True, "maxRows": int(PRIOR.MAX_INPUT_ROWS)})
        rec["indicators"] = {"snapshot_rows": i_snap.height, "tickers": len(i_per), "metrics": metrics, "points": points, "skipped": i_skip, "merged_prior_snapshots": n_merge_files,
                             "merged_prior_rows": n_merge_rows, "calendar_modes": sorted(modes), "ui_gate_pass": sum(1 for t in tables if t["kind"] == "INDICATOR_RESULT" and t["ui_gate"]["gate"] == "PASS")}
        step("⑤ 有加工 INDICATOR_RESULT(%s · 最近 %d 個交易日)" % (" ".join(metrics), points), "GREEN" if i_per and not i_skip else ("YELLOW" if i_per else "RED"),
             "一票一表 %d(VAP 閘過 %d)· as-of 快照 %d 列(併入舊快照 %d 夾 %d 列)· 跳過 %d → indicators/<票>.parquet · vqg_indicator_results.parquet" % (
                 len(i_frames), rec["indicators"]["ui_gate_pass"], i_snap.height, n_merge_files, n_merge_rows, len(i_skip)))
        if not vap_sources:
            raise ValueError("NOTHING_EXPORTED")
        # ⑥ 連線證據 + VAP config(dataFile 路徑相對輸出夾 · 檔案寫完才算指紋)
        for c in conns:
            c["dataFile"] = c["dataFile"]
        _write_json(stage / "vqg_connection_manifest.json", {"schema": VAP_VQG_SCHEMA, "version": VERSION_TAIL, "policy": "VQG_ONLY_READ_ONLY_FAIL_CLOSED", "producer": "VQG export-vap",
                                                               "exportDir": str(final), "connections": conns})
        _write_json(stage / "vdf_connection_manifest.json", {"schema": VAP_VDF_SCHEMA, "version": VERSION_TAIL, "policy": "VDF_AUTHORIZED_READ_ONLY_FAIL_CLOSED",
                                                               "note": "VDF 不直連 VAP;VAP 的正式輸入 = VQG(VDF/VRN → VQG → VAP)· connections 留空", "connections": []})
        cfg = build_vap_config(final, out_root, int(getattr(args, "vap_port", 8765) or 8765), vap_sources)
        _write_json(stage / VAP_CONFIG_NAME, cfg)
        rec["export_dir"] = str(final)
        rec["tables"] = tables
        rec["vap_sources"] = len(vap_sources)
        rec["files"] = sorted(str(p.relative_to(stage)).replace("\\", "/") for p in stage.rglob("*") if p.is_file())
        _write_json(stage / "export_receipt.json", rec)
        sums = "\n".join("%s  %s" % (_sha256_file(p), str(p.relative_to(stage)).replace("\\", "/")) for p in sorted(stage.rglob("*")) if p.is_file() and p.name != "SHA256SUMS.txt") + "\n"
        (stage / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
        stage.rename(final)
    except (ValueError, OSError) as error:
        shutil.rmtree(stage, ignore_errors=True)
        step("⑥ 匯出", "RED", "%s: %s" % (type(error).__name__, str(error)[:200]))
        return finish("RED", "匯出中斷 · 暫存夾已清", PRIOR.hint(str(error)))
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
    (out_root / VAP_CONFIG_NAME).write_text((final / VAP_CONFIG_NAME).read_text(encoding="utf-8"), encoding="utf-8")
    untouched = _tree_signature(root) == sig_before
    rec["vdf_root_untouched"] = untouched
    step("⑥ 連線證據 + VAP config", "GREEN", "vqg_connection_manifest.json(%d 筆 AUTHORIZED · 指紋)· vdf_connection_manifest.json(空)· %s(%d 來源)→ %s" % (len(conns), VAP_CONFIG_NAME, len(vap_sources), final))
    step("⑦ VDF 庫一字沒動", "GREEN" if untouched else "RED", "跑前跑後檔案清單 + 大小 + mtime 相同" if untouched else "VDF 庫在匯出期間變了(別的程序在寫?)")
    skipped = len(s_skip) + len(i_skip)
    gate_fail = sum(1 for t in tables if t["ui_gate"]["gate"] != "PASS")
    lamp = "RED" if not untouched else ("YELLOW" if (cal == "derive" or skipped or truncated or gate_fail) else "GREEN")
    rec["lamp_reason"] = {"calendar_mode": cal, "skipped": skipped, "truncated": truncated, "ui_gate_fail": gate_fail}
    _write_json(out_root / "latest.json", {"export_dir": str(final), "at": rec["at"], "lamp": lamp, "vap_sources": len(vap_sources)})
    meaning = {"GREEN": "全部票匯出 · 曆嚴格 · VAP 可直接 --config 接",
               "YELLOW": "已匯出 · 但 %s" % " / ".join(x for x in (("曆是 VQG 從 VDF 日線推的" if cal == "derive" else ""), ("%d 張票跳過" % skipped if skipped else ""),
                                                            ("票被 --max-tickers 截斷" if truncated else ""), ("%d 張表過不了 VAP U/I 閘(收據 tables)" % gate_fail if gate_fail else "")) if x),
               "RED": "匯出不可信 · 看 steps"}[lamp]
    return finish(lamp, meaning, "python VAP_AllInOne_v03xx.py --config \"%s\"" % (out_root / VAP_CONFIG_NAME))


def _same_point(wide, snap_rows, col) -> bool:
    """自測用:長表快照那一列(觀測日 · 值)在一票一表裡要有同觀測日同值。"""
    if snap_rows.height != 1 or wide is None:
        return False
    od, val = snap_rows["observation_date"][0], snap_rows["value_num"][0]
    hit = wide.filter(pl.col("observation_date") == od)
    return hit.height == 1 and val is not None and hit[col][0] is not None and abs(float(hit[col][0]) - float(val)) < 1e-9


# ── 自測(v0105 自測 + 本版 12 項 · 零網路 · 只在 tempfile 沙盒寫)──────────────
def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("  [OK] " if cond else "  [FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    buf = io.StringIO()
    env_root = os.environ.pop("VQG_VDF_ROOT", None)                      # v0105 自測 ⑩ 驗「預設庫根照 VDF 的冊」· 操作員設了 $env:VQG_VDF_ROOT 會誤判 → 自測期間拿掉 · 跑完放回
    try:
        with contextlib.redirect_stdout(buf):
            rc_prior = PRIOR.selftest()
        prior_ok = rc_prior == 0
    except Exception as error:  # noqa: BLE001
        prior_ok = False
        buf.write("%s: %s" % (type(error).__name__, error))
    finally:
        if env_root is not None:
            os.environ["VQG_VDF_ROOT"] = env_root
    chk("① v0105 自測照過(%s · 自測期間不受 $env:VQG_VDF_ROOT 影響)" % (buf.getvalue().strip().splitlines() or ["—"])[-1][:70], prior_ok)
    src_text = Path(__file__).read_text(encoding="utf-8")
    chk("② 第 3 行加速器標記 · 前版 v0105 位元組 = 入倉版(SHA-256 釘住)· 本檔不匯入任何網路模組 · 不 import VAP",
        src_text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and PRIOR_SHA_OK
        and not re.search(r"^\s*(import|from)\s+(urllib|requests|socket|http|httpx|aiohttp|VAP_AllInOne)\b", src_text, re.M))
    d0 = date(2026, 1, 1)
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        vdf = t / "vdf_database"
        (vdf / "output_hub").mkdir(parents=True)
        old = PRIOR._bars("2330.TW", d0, 120) + PRIOR._bars("2317.TW", d0, 120, skip=(100,), base=80)
        new = [(d, tk, o, h, l, c, ac * 0.97, v) for (d, tk, o, h, l, c, ac, v) in PRIOR._bars("2330.TW", d0, 126) + PRIOR._bars("2317.TW", d0, 126, skip=(100,), base=80)]
        PRIOR._vdf_like(vdf / "output_hub" / "tw_daily_prices_20261101_120000.parquet", old)
        PRIOR._vdf_like(vdf / "output_hub" / "tw_daily_prices_20261102_120000.parquet", new)
        PRIOR._vdf_like(vdf / "output_hub" / "us_daily_prices_20261101_120000.parquet", PRIOR._bars("NVDA", d0, 130, base=50))   # 美股 · 資料到 as-of 之後 4 天(驗觀測日不漏未來)
        (vdf / "notes.parquet").write_bytes(b"not a parquet")
        out = t / "out"
        out.mkdir()
        src, _ = PRIOR.discover(vdf)
        as_of = d0 + timedelta(days=125)
        a0 = types.SimpleNamespace(root=vdf, ticker="2330.TW", metrics=["sma"], windows=[5], as_of=as_of - timedelta(days=7), start=None, report_id=None, cache_dir=None, calendar="derive", snapshots="latest", market=None)
        rows0, _ = PRIOR.run_local(src, a0)
        PRIOR.export_snapshot(rows0, out)
        sig0 = _tree_signature(vdf)
        ns = types.SimpleNamespace(via_root=None, root=str(vdf), out_dir=str(out), receipt_dir=str(t / "rcpt"), ticker=[], max_tickers=50, metrics=["sma", "rsi", "macd"], windows=None,
                                   as_of=as_of, series_rows=50, indicator_points=12, calendar="auto", snapshots="latest", market=None, vap_port=8765)
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            rc = export_vap(ns)
        exp = sorted(out.glob("vap_export_*"))
        ed = exp[-1] if exp else None
        names = sorted(str(p.relative_to(ed)).replace("\\", "/") for p in ed.rglob("*") if p.is_file()) if ed else []
        chk("③ export-vap rc 0 · 輸出夾:series/<票> ×3 · indicators/<票> ×3(parquet + csv · 含美股 NVDA)· 兩張長表 · catalog · 兩份 manifest · config · receipt · SHA256SUMS",
            rc == 0 and ed is not None and {"series/2330_TW.parquet", "series/2317_TW.csv", "series/NVDA.parquet", "indicators/2330_TW.parquet", "indicators/2317_TW.csv", "indicators/NVDA.parquet", "vqg_series.parquet", "vqg_indicator_results.parquet",
                                            "vqg_vdf_catalog.json", "vqg_connection_manifest.json", "vdf_connection_manifest.json", VAP_CONFIG_NAME, "export_receipt.json", "SHA256SUMS.txt"} <= set(names))
        man = json.loads((ed / "vqg_connection_manifest.json").read_text(encoding="utf-8")) if ed else {}
        conns = man.get("connections") or []
        chk("④ 連線證據照 VAP 驗法:schema · 6 筆(3 票 × SERIES / INDICATOR_RESULT)AUTHORIZED readOnly PARQUET sourceSystem VQG · limits 5000/100/252 · 政策字串 · 指紋重算相同 · dataSha256 = 檔案",
            man.get("schema") == VAP_VQG_SCHEMA and len(conns) == 6 and all(c["state"] == "AUTHORIZED" and c["readOnly"] is True and c["engine"] == "PARQUET" and c["sourceSystem"] == "VQG" for c in conns)
            and {c["datasetType"] for c in conns} == {"SERIES", "INDICATOR_RESULT"} and all(c["limits"] == {"maxInputRows": 5000, "maxOutputRows": 100, "maxWindow": 252} for c in conns)
            and all(c["upstreamEvidence"]["pricePolicy"] == "ADJUSTED_PRICE_ONLY" and c["upstreamEvidence"]["taLibPolicy"] == "CALCULATE_ONLY_NO_FETCH" and c["upstreamEvidence"]["vdfAuthorized"] is True for c in conns)
            and all(c["fingerprint"] == vap_fingerprint(c) for c in conns) and all(c["dataSha256"] == _sha256_file(ed / c["dataFile"]) for c in conns))
        sf = pl.read_parquet(ed / "series" / "2330_TW.parquet") if ed else None
        lf = pl.read_parquet(ed / "vqg_series.parquet") if ed else None
        chk("⑤ SERIES 無加工:一票一表 2330 · ≤ --series-rows 50 列 · x = date 不重複升冪 · 欄 date / adj_close / volume / market / session_index / available_on · 全空欄不列 · 取最新批次(adj_close = 新批次 ×0.97)· 長表兩票都在",
            sf is not None and sf.height <= 50 and sf["date"].to_list() == sorted(set(sf["date"].to_list())) and {"date", "adj_close", "volume", "market", "session_index", "available_on"} <= set(sf.columns)
            and "turnover" not in sf.columns and abs(float(sf.sort("date")["adj_close"][-1]) - float([r for r in new if r[1] == "2330.TW" and date.fromisoformat(r[0]) <= as_of][-1][6])) < 1e-9
            and lf is not None and set(lf["ticker"].unique().to_list()) == {"2330.TW", "2317.TW", "NVDA"})
        inf = pl.read_parquet(ed / "vqg_indicator_results.parquet") if ed else None
        rcp0 = json.loads((ed / "export_receipt.json").read_text(encoding="utf-8")) if ed else {}
        chk("⑥ INDICATOR_RESULT 長表:欄位 = v0104 FIELDS(23 欄)· sma + rsi + macd 三票都有 · 既有 vqg_<uuid> 快照(早 7 天的 sma 5)合進來 3 列 · 去重後 sma 5 共 12 列",
            inf is not None and list(inf.columns) == list(PRIOR.FIELDS.keys()) and set(inf["ticker"].unique().to_list()) == {"2330.TW", "2317.TW", "NVDA"}
            and {"VQG.IND.SMA", "VQG.IND.RSI", "VQG.IND.MACD"} <= set(inf["indicator_id"].unique().to_list())
            and inf.unique(subset=["request_key", "solution_id", "observation_date", "indicator_id", "window_n", "ticker"]).height == inf.height
            and (rcp0.get("indicators") or {}).get("merged_prior_rows") == 3 and inf.filter((pl.col("window_n") == 5) & (pl.col("indicator_id") == "VQG.IND.SMA")).height == 12)
        wf = pl.read_parquet(ed / "indicators" / "2330_TW.parquet") if ed else None
        wn = pl.read_parquet(ed / "indicators" / "NVDA.parquet") if ed else None
        sn = pl.read_parquet(ed / "series" / "NVDA.parquet") if ed else None
        chk("⑦ INDICATOR 一票一表:x = observation_date 不重複升冪 · 最近 --indicator-points 12 個交易日 · 欄 SMA_5_S1 … RSI_14_S3 · SMA_5 值 = 長表同觀測日的值 · MACD 結構值展開 MACD_26_S1_line / _signal / _histogram 且最後一列有值 · 美股 NVDA 觀測日 ≤ as-of 且最後觀測日 = as-of(當日含)· 台股最後觀測日 = as-of 前一交易日",
            wf is not None and 3 <= wf.height <= 12 and wf["observation_date"].to_list() == sorted(set(wf["observation_date"].to_list()))
            and {"SMA_5_S1", "SMA_5_S2", "SMA_5_S3", "RSI_14_S1", "MACD_26_S1_line", "MACD_26_S1_signal", "MACD_26_S1_histogram"} <= set(wf.columns)
            and wf.sort("observation_date")["MACD_26_S1_line"][-1] is not None and "MACD_26_S1" not in wf.columns
            and _same_point(wf, inf.filter((pl.col("ticker") == "2330.TW") & (pl.col("window_n") == 5) & (pl.col("solution_id") == "S1") & (pl.col("as_of") == as_of)), "SMA_5_S1")
            and wn is not None and max(wn["observation_date"].to_list()) == as_of and max(wf["observation_date"].to_list()) == as_of - timedelta(days=1)
            and sn is not None and max(sn["date"].to_list()) <= as_of)
        cat = json.loads((ed / "vqg_vdf_catalog.json").read_text(encoding="utf-8")) if ed else {}
        ents = cat.get("entries") or []
        chk("⑧ 整理全部:VDF 庫夾 4 個 parquet 全列(3 認得 · 1 被新批次取代 · 1 讀不了)· 帶 SHA-256 / 列數 / 票樣本",
            len(ents) == 4 and cat.get("recognized") == 3 and cat.get("superseded") == 1 and cat.get("unreadable") == 1
            and any(e["superseded"] and e["snapshot"] == "20261101_120000" for e in ents) and all(e.get("sha256") for e in ents) and any(e.get("tickers_sample") for e in ents))
        cfg = json.loads((ed / VAP_CONFIG_NAME).read_text(encoding="utf-8")) if ed else {}
        root_cfg = json.loads((out / VAP_CONFIG_NAME).read_text(encoding="utf-8")) if (out / VAP_CONFIG_NAME).is_file() else {}
        chk("⑨ VAP config:formalInputAuthority VQG · 6 來源 authority VQG · engine PARQUET · 位置 / manifest 路徑真的在 · 每來源在 manifest 有同 id 同 contract 的證據 · allowedRoots 含輸出夾 · loopback · 輸出夾根有一份指最新",
            cfg.get("formalInputAuthority") == "VQG" and len(cfg.get("sources") or []) == 6 and all(s["authority"] == "VQG" and s["engine"] == "PARQUET" and Path(s["location"]).is_file() for s in cfg["sources"])
            and all(any(c["sourceId"] == s["id"] and c["contractId"] == s["vqgContractId"] for c in conns) for s in cfg["sources"])
            and Path(cfg["vqgGateway"]["manifest"]).is_file() and Path(cfg["vdfGateway"]["manifest"]).is_file() and str(ed) in cfg["allowedRoots"] and cfg["host"] == "127.0.0.1" and root_cfg == cfg)
        gates = [ui_gate(pl.read_parquet(s["location"]), next(c["xField"] for c in conns if c["sourceId"] == s["id"])) for s in (cfg.get("sources") or [])]
        chk("⑩ VAP U/I 閘預檢:6 張表都 PASS(列 ≥ 3 · x 不重複升冪 · 數值欄 ≥ 2)· 收據 tables 同結果 · manifest fieldSemantics 涵蓋每個數值欄",
            len(gates) == 6 and all(g["gate"] == "PASS" for g in gates) and all(tb["ui_gate"]["gate"] == "PASS" for tb in rcp0.get("tables") or [])
            and all(set(g["numeric"]) <= set(c["fieldSemantics"].keys()) for g, c in zip(gates, [next(c for c in conns if c["sourceId"] == s["id"]) for s in cfg["sources"]])))
        sums_ok = ed is not None and all(_sha256_file(ed / ln.split("  ", 1)[1]) == ln.split("  ", 1)[0] for ln in (ed / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if ln.strip())
        latest = json.loads((t / "rcpt" / "VQG_ExportVAP_latest.json").read_text(encoding="utf-8")) if (t / "rcpt" / "VQG_ExportVAP_latest.json").is_file() else {}
        chk("⑪ SHA256SUMS 全對(含子夾)· 收據(輸出夾 + VIA_Reports/vqg)· 燈 YELLOW(曆是推的)· VDF 庫一字沒動 · 暫存夾清掉",
            sums_ok and rcp0.get("verb") == "export-vap" and latest.get("lamp") == "YELLOW" and latest.get("vdf_root_untouched") is True and _tree_signature(vdf) == sig0
            and not list(out.glob(".vap_export-*")))
        buf3 = io.StringIO()
        with contextlib.redirect_stdout(buf3):
            rc_in = export_vap(types.SimpleNamespace(via_root=None, root=str(vdf), out_dir=str(vdf / "out"), receipt_dir=str(t / "rcpt2"), ticker=[], max_tickers=0, metrics=None, windows=None,
                                                     as_of=as_of, series_rows=0, indicator_points=0, calendar="auto", snapshots="latest", market=None, vap_port=8765))
            rc_in2 = export_vap(types.SimpleNamespace(via_root=None, root=str(vdf), out_dir=str(t / "out3"), receipt_dir=str(vdf / "receipts"), ticker=[], max_tickers=0, metrics=None, windows=None,
                                                      as_of=as_of, series_rows=0, indicator_points=0, calendar="auto", snapshots="latest", market=None, vap_port=8765))
        old_env = os.environ.get("VQG_VDF_ROOT")
        os.environ["VQG_VDF_ROOT"] = str(vdf)
        try:
            buf4 = io.StringIO()
            with contextlib.redirect_stdout(buf4):
                rc_env = main(["export-vap", "--out-dir", str(t / "out2"), "--receipt-dir", str(t / "rcpt3"), "--ticker", "2317.TW", "--metrics", "sma", "--as-of", as_of.isoformat(), "--series-rows", "20", "--indicator-points", "0"])
            buf5 = io.StringIO()
            with contextlib.redirect_stdout(buf5), contextlib.redirect_stderr(io.StringIO()):
                rc_doc = main(["doctor"])
            buf6 = io.StringIO()
            with contextlib.redirect_stdout(buf6), contextlib.redirect_stderr(io.StringIO()):
                rc_help = main(["--help"])
        finally:
            if old_env is None:
                os.environ.pop("VQG_VDF_ROOT", None)
            else:
                os.environ["VQG_VDF_ROOT"] = old_env
        e2 = sorted((t / "out2").glob("vap_export_*"))
        sf2 = pl.read_parquet(e2[-1] / "series" / "2317_TW.parquet") if e2 else None
        cfg2 = json.loads((e2[-1] / VAP_CONFIG_NAME).read_text(encoding="utf-8")) if e2 else {}
        chk("⑫ 邊界與指令列:輸出夾在 VDF 庫裡 → RED rc 2 不寫;收據夾在 VDF 庫裡 → RED rc 2 連收據都不寫(VDF 庫一字沒動 · 收據夾沒建);VQG_VDF_ROOT 當庫根 · --ticker 只匯那張 · --series-rows 20 · --indicator-points 0 → 只有 SERIES 來源 · rc 0;doctor 原樣交 v0105 · --help 有 export-vap",
            rc_in == 2 and not (vdf / "out").exists() and rc_in2 == 2 and not (vdf / "receipts").exists() and not (t / "out3").exists() and _tree_signature(vdf) == sig0 and "OUTPUT_INSIDE_SOURCE_ROOT" in buf3.getvalue() and "收據沒寫" in buf3.getvalue()
            and rc_env == 0 and sf2 is not None and sf2.height <= 20 and len(cfg2.get("sources") or []) == 1 and cfg2["sources"][0]["id"] == "VQG-SERIES-2317_TW"
            and rc_doc == 0 and '"verdict"' in buf5.getvalue() and rc_help == 0 and "export-vap [--root R]" in buf6.getvalue() and "v0105 指令" in buf6.getvalue())
    n = 12
    if bad:
        print("[FAIL] VQG %s selftest · %d/%d 不過:%s" % (VERSION_TAIL, len(bad), n, " / ".join(b[:40] for b in bad)), flush=True)
        return 1
    print("[PASS] VQG %s selftest · %d/%d(含 v0105 全部)· 零網路 · 只在沙盒寫" % (VERSION_TAIL, n, n), flush=True)
    return 0


def main(argv=None) -> int:
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = next((a for a in argv if not a.startswith("-")), "scan")
    if cmd in ("selftest", "test") or "--selftest" in argv:
        try:
            return selftest()
        except Exception as error:  # noqa: BLE001
            print("[FAIL] VQG %s selftest 中斷 · %s: %s" % (VERSION_TAIL, type(error).__name__, str(error)[:200]), flush=True)
            return 1
    if cmd == "export-vap":
        ap = argparse.ArgumentParser(prog="VQG export-vap", description="VDF 庫夾 → 整理全部 + 無加工 SERIES + 有加工 INDICATOR_RESULT(一票一表)+ VAP 連線證據(指紋)+ VAP config")
        ap.add_argument("command")
        ap.add_argument("--root")
        ap.add_argument("--via-root")
        ap.add_argument("--out-dir")
        ap.add_argument("--receipt-dir")
        ap.add_argument("--ticker", nargs="*", default=[])
        ap.add_argument("--max-tickers", type=int, default=50, help="沒給 --ticker 時最多匯幾張(0 = 全部)")
        ap.add_argument("--metrics", nargs="+", default=None, help="預設 sma rsi macd")
        ap.add_argument("--windows", nargs="+", type=int, default=None)
        ap.add_argument("--as-of", type=date.fromisoformat, default=None)
        ap.add_argument("--series-rows", type=int, default=0, help="每票 SERIES 最多幾個交易日(預設 4999 = v0104 上限 − 1)")
        ap.add_argument("--indicator-points", type=int, default=60, help="每票指標表算最近幾個交易日(0 = 只出 as-of 快照長表)")
        ap.add_argument("--calendar", choices=["vdf", "derive", "auto"], default="auto")
        ap.add_argument("--snapshots", choices=["strict", "latest"], default="latest")
        ap.add_argument("--market", choices=["TW", "US"], default=None)
        ap.add_argument("--vap-port", type=int, default=8765)
        a = ap.parse_args(argv)
        if not getattr(a, "root", None):
            r, how = PRIOR.default_root(PRIOR.via_root(a.via_root))
            print("[計] VDF 庫根 %s(%s)" % (r, how), file=sys.stderr, flush=True)
            a.root = str(r)
        return export_vap(a)
    if "--help" in argv or "-h" in argv:
        rc = PRIOR.main(argv)
        print("v0106 指令:export-vap [--root R] [--out-dir O] [--ticker T …] [--max-tickers N] [--metrics …] [--windows …] [--as-of D] [--series-rows N] [--indicator-points N] [--calendar vdf|derive|auto] [--snapshots strict|latest] [--market TW|US] [--vap-port 8765]")
        return rc
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
