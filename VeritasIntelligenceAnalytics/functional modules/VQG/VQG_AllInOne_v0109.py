#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VeritaQuantGuard(VQG)v0109 — v0108 薄尾(v0108 一字不改 · SHA-256 釘在 PRIOR_SHA256)。

操作員 2026-11-09:「VQG 會分為兩個部分:數據計算定義方式,及分析 / 回測 / 多因子分析 / 統計分析的量化分析功能;來源為資料庫自動擷取全部資料庫形成選項;
計算所需要的數據進行分析,輸出資料由 VAP 展現;實測自測修正、使用者測試修正、啟動測試修正到完美無誤即完成」。

第一部分(數據計算定義)仍是 v0104 公式引擎 + v0108 換裝的十個指標 —— 本版一字不動。
第二部分(量化分析)本版加:
  catalog    來源 = 資料庫自動擷取全部:VDF 庫夾每個 parquet 的欄 · 型別 · 列數 · 日期範圍 · 認得(v0104 別名)/ 不認得 → vqg_catalog_options.json / .md
             = 「選項」清單(認得的是序列輸入;其餘數值欄是候選因子 · 不自動啟用 · 不猜語意)。
  quant      讀 export-vap 輸出夾(series/<票> · indicators/<票>,公式全來自第一部分;不另算指標)→
             回測 backtest/<票>.parquet(買進持有 vs SMA 趨勢 · RSI 均值回歸 · MACD 柱三策略;訊號 t 用在 t+1 報酬 · 不偷看;
               RSI 門檻 = 自身歷史擴張百分位(資料驅動 · 不寫死 30/70);年化用序列自己近一年交易日數;rf 有 rf_annual 欄才扣,沒有照實標)
             多因子 factor/vqg_factor_ic.parquet(跨票截面:每日各因子值 vs 未來 h 日報酬的 Spearman IC · IC 均 / IR / 命中率 · 前半−後半分組價差;票 < 3 = INSUFFICIENT 照實)
             統計 stats/vqg_stats.parquet(報酬均 · 標準差 · 偏態 · 峰態 · JB · 自相關 1/5 · 變異比 2/5 · 正報酬比)+ stats/vqg_return_corr.parquet(票間相關)
             → 回測曲線與 IC 表登進 VAP(vqg_connection_manifest AUTHORIZED + 指紋 · VAP config sources;datasetType INDICATOR_RESULT / RISK_QUALITY = VAP 允許類)
             → export_receipt / VQG_ExportVAP_latest 加 quant 節 → SHA256SUMS 重生(永遠最後寫)。
  export-vap v0108 原樣跑完(匯出 + 量化分析①)→ 接 quant(本版)。
邊界:同 v0108(只讀 VDF 庫 · 零網路 · 不 import VAP · 不寫 VDF 夾 · 前版被改過 → rc 2);統計與回測只用匯出夾的資料。
自測:python VQG_AllInOne_v0109.py selftest(本版 12 項 + v0108 自測全部 · 零網路 · 只在 tempfile 寫)。
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
import sys
import tempfile
import types
from datetime import date, datetime, timedelta
from pathlib import Path

VERSION_TAIL = "v0109"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VQG_AllInOne_v0108.py"
PRIOR_SHA256 = "c4ba8cf2ec22edffebda33478587861509882101f8001d982aa7c960aacb2151"   # v0108(PR #621 · 09d7c42ba)
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(v0109 是 v0108 的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("vqg_v0108_for_v0109", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
V8 = PRIOR
V7 = PRIOR.PRIOR                      # v0107(export-vap 本體 · build_connection · ui_gate)
V5 = V7.PRIOR                         # v0105
V4 = V5.PRIOR                         # v0104(公式引擎 · COLUMN_ALIASES · norm)
pl = PRIOR.pl
ENGINE_VERSION = PRIOR.ENGINE_VERSION
_EXPORT_VAP_0108 = PRIOR.export_vap_0108
STRATEGIES = ("BUY_HOLD", "SMA_TREND", "RSI_MEANREV", "MACD_HIST")
FACTOR_COLS = ("RSI_14_S1", "SMA20_DEV", "VOLATILITY_20_S1", "OBV_20_S2", "DRAWDOWN_20_S1", "REL_STRENGTH_60_S1", "MACD_26_S1_histogram", "ATR_14_S3")
FWD_H = 5
LOW_PCT, HIGH_PCT = 0.2, 0.8          # 百分位位置(定義性 · 門檻值本身來自序列自身分布)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ── 共用 ───────────────────────────────────────────────────────────────────────────────────────
def _f(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _std(xs, ddof=1):
    xs = [x for x in xs if x is not None]
    if len(xs) <= ddof:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - ddof))


def _ppy(dates: list) -> int | None:
    """一年幾個交易日:序列自己近 365 天的觀測數(跨度 < 300 天 = None · 不寫死 252)。"""
    if not dates:
        return None
    last = dates[-1]
    if (last - dates[0]).days < 300:
        return None
    return sum(1 for d in dates if (last - d).days < 365)


def _rank(xs: list) -> list:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def spearman(a: list, b: list):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    ra, rb = _rank([p[0] for p in pairs]), _rank([p[1] for p in pairs])
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None


def expanding_pct(hist: list, x) -> float | None:
    """x 在 hist(含自己)裡的百分位(0..1);hist 只含到 t 為止 → 不偷看。"""
    vals = [h for h in hist if h is not None]
    if x is None or len(vals) < 5:
        return None
    return sum(1 for v in vals if v <= x) / len(vals)


def max_drawdown(eq: list) -> float:
    peak, mdd = -1e300, 0.0
    for v in eq:
        peak = max(peak, v)
        if peak > 0:
            mdd = min(mdd, v / peak - 1.0)
    return mdd


# ── catalog(來源 = 全部資料庫 → 選項)────────────────────────────────────────────────────────
def catalog(root: Path) -> dict:
    root = Path(root).expanduser().resolve()
    alias = {V4.norm(a): k for k, al in V4.COLUMN_ALIASES.items() for a in al}
    files, errors = [], []
    for p in sorted(root.rglob("*.parquet")):
        try:
            schema = pl.read_parquet_schema(p)
            lf = pl.scan_parquet(p)
            rows = lf.select(pl.len()).collect().item()
            cols = []
            date_col = next((c for c, t in schema.items() if V4.norm(c) in alias and alias[V4.norm(c)] == "date"), None) or next((c for c, t in schema.items() if t in (pl.Date, pl.Datetime)), None)
            dr = None
            if date_col is not None and rows:
                mm = lf.select(pl.col(date_col).min().alias("a"), pl.col(date_col).max().alias("b")).collect()
                dr = [str(mm["a"][0]), str(mm["b"][0])]
            for c, t in schema.items():
                known = alias.get(V4.norm(c))
                cols.append({"name": c, "dtype": str(t), "recognized_as": known, "role": "series_input" if known else ("candidate_factor" if t.is_numeric() else "key_or_text")})
            files.append({"file": str(p.relative_to(root)).replace("\\", "/"), "rows": rows, "columns": cols, "date_col": date_col, "date_range": dr,
                          "recognized": sum(1 for c in cols if c["recognized_as"]), "candidate_factors": [c["name"] for c in cols if c["role"] == "candidate_factor"]})
        except Exception as exc:  # noqa: BLE001
            errors.append({"file": str(p.relative_to(root)).replace("\\", "/"), "error": type(exc).__name__})
    inputs = sorted({c["recognized_as"] for f in files for c in f["columns"] if c["recognized_as"]})
    cands = sorted({c["name"] for f in files for c in f["columns"] if c["role"] == "candidate_factor"})
    return {"schema": "VIA-VQG-CATALOG-OPTIONS/1.0", "vqgVersion": VERSION_TAIL, "formulaEngine": ENGINE_VERSION, "vdfRoot": str(root), "at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "files": len(files), "unreadable": len(errors), "options": {"series_inputs": inputs, "candidate_factors": cands, "metrics": list(V4.CORE), "strategies": list(STRATEGIES), "factors": list(FACTOR_COLS)},
            "rule": "認得的欄(v0104 別名)= 序列輸入;其他數值欄 = 候選因子(列出 · 不自動啟用 · 不猜語意);指標公式全在第一部分,選項只決定用哪些", "entries": files, "errors": errors}


def write_catalog(cat: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "vqg_catalog_options.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# VQG 來源選項(資料庫全掃)· %s · %s" % (VERSION_TAIL, cat["at"]), "", "庫:`%s` · parquet %d · 讀不了 %d" % (cat["vdfRoot"], cat["files"], cat["unreadable"]), "",
         "- 序列輸入(認得):%s" % (" · ".join(cat["options"]["series_inputs"]) or "—"), "- 候選因子(數值欄 · 不自動啟用):%s" % (" · ".join(cat["options"]["candidate_factors"][:40]) or "—"),
         "- 指標(第一部分 v0104 CORE):%s" % " · ".join(cat["options"]["metrics"]), "- 回測策略:%s · 因子:%s" % (" · ".join(cat["options"]["strategies"]), " · ".join(cat["options"]["factors"])), "",
         "| 檔 | 列 | 日期範圍 | 認得欄 | 候選因子 |", "|---|---|---|---|---|"]
    L += ["| %s | %d | %s | %d | %s |" % (e["file"], e["rows"], " ~ ".join(e["date_range"]) if e["date_range"] else "—", e["recognized"], ", ".join(e["candidate_factors"][:8]) or "—") for e in cat["entries"]]
    (out_dir / "vqg_catalog_options.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# ── 回測 ───────────────────────────────────────────────────────────────────────────────────────
def backtest(series, ind, ticker: str) -> tuple:
    """series(date · adj_close [· rf_annual])× indicators(observation_date · 指標欄)→ (曲線 frame, 摘要 rows, 缺)。訊號 t → 報酬 t+1。"""
    j = series.select([c for c in ("date", "adj_close", "rf_annual") if c in series.columns]).join(ind.rename({"observation_date": "date"}), on="date", how="inner").sort("date")
    if j.height < 10:
        return None, [], ["INSUFFICIENT_OVERLAP"]
    dates = j["date"].to_list()
    px = [_f(x) for x in j["adj_close"].to_list()]
    rets = [None] + [(px[i] / px[i - 1] - 1.0) if (px[i] is not None and px[i - 1]) else None for i in range(1, len(px))]
    ppy = _ppy(dates)
    rf_daily = None
    if "rf_annual" in j.columns and ppy:
        rfa = _mean([_f(x) for x in j["rf_annual"].to_list()])
        rf_daily = (1.0 + rfa) ** (1.0 / ppy) - 1.0 if rfa is not None else None
    missing = []
    sma = [_f(x) for x in j["SMA_20_S1"].to_list()] if "SMA_20_S1" in j.columns else None
    rsi = [_f(x) for x in j["RSI_14_S1"].to_list()] if "RSI_14_S1" in j.columns else None
    mac = [_f(x) for x in j["MACD_26_S1_histogram"].to_list()] if "MACD_26_S1_histogram" in j.columns else None
    sigs = {"BUY_HOLD": [1] * len(px)}
    if sma:
        sigs["SMA_TREND"] = [1 if (p is not None and s is not None and p > s) else 0 for p, s in zip(px, sma)]
    else:
        missing.append("SMA_20_S1")
    if rsi:
        pos, s = 0, []
        for i, v in enumerate(rsi):
            pct = expanding_pct(rsi[: i + 1], v)
            if pct is not None and pct <= LOW_PCT:
                pos = 1
            elif pct is not None and pct >= HIGH_PCT:
                pos = 0
            s.append(pos)
        sigs["RSI_MEANREV"] = s
    else:
        missing.append("RSI_14_S1")
    if mac:
        sigs["MACD_HIST"] = [1 if (h is not None and h > 0) else 0 for h in mac]
    else:
        missing.append("MACD_26_S1_histogram")
    cols = {"date": dates, "adj_close": px}
    summary = []
    for name, sig in sigs.items():
        eq, e = [], 1.0
        sr = []
        for i in range(len(px)):
            r = (sig[i - 1] * rets[i]) if (i > 0 and rets[i] is not None) else 0.0
            e *= (1.0 + r)
            eq.append(e)
            sr.append(r if i > 0 else None)
        cols["eq_" + name] = eq
        if name != "BUY_HOLD":
            cols["pos_" + name] = sig
        n = len(px) - 1
        sr_v = [x for x in sr if x is not None]
        in_mkt = [sr[i] for i in range(1, len(px)) if sig[i - 1] == 1 and sr[i] is not None]
        vol = _std(sr_v)
        total = eq[-1] - 1.0
        cagr = (eq[-1] ** (ppy / n) - 1.0) if (ppy and n > 0 and eq[-1] > 0) else None
        exc = [(x - rf_daily) for x in sr_v] if rf_daily is not None else sr_v
        sharpe = (_mean(exc) / _std(exc) * math.sqrt(ppy)) if (ppy and _std(exc)) else None
        summary.append({"ticker": ticker, "strategy": name, "n_days": n, "total_return": total, "cagr": cagr, "vol_annual": (vol * math.sqrt(ppy)) if (vol is not None and ppy) else None,
                        "sharpe": sharpe, "sharpe_rf": "rf_annual" if rf_daily is not None else "NONE(RF_SERIES_MISSING)", "max_drawdown": max_drawdown(eq),
                        "hit_rate": (sum(1 for x in in_mkt if x > 0) / len(in_mkt)) if in_mkt else None, "exposure": sum(sig[:-1]) / n if n else None,
                        "turnover": sum(abs(sig[i] - sig[i - 1]) for i in range(1, len(sig))) / n if n else None, "vs_buy_hold": total - (cols["eq_BUY_HOLD"][-1] - 1.0),
                        "periods_per_year": ppy, "threshold_rule": {"SMA_TREND": "price > SMA_20_S1(定義性)", "RSI_MEANREV": "RSI_14_S1 自身擴張百分位 ≤ %.0f%% 進 · ≥ %.0f%% 出(資料驅動)" % (LOW_PCT * 100, HIGH_PCT * 100),
                                                                     "MACD_HIST": "柱 > 0(定義性)", "BUY_HOLD": "—"}[name], "signal_lag": 1})
    return pl.DataFrame(cols), summary, missing


# ── 多因子 ─────────────────────────────────────────────────────────────────────────────────────
def factor_ic(ind_frames: dict, series_frames: dict, h: int = FWD_H) -> tuple:
    """跨票截面:每日 factor 值 vs 未來 h 個觀測日報酬的 Spearman IC;票 < 3 → INSUFFICIENT。"""
    if len(ind_frames) < 3:
        return None, {"state": "INSUFFICIENT_TICKERS", "tickers": len(ind_frames), "note": "截面 IC 至少要 3 張票;本匯出 %d 張 · 照實" % len(ind_frames), "factors": {}}
    per = {}
    for tk, ind in ind_frames.items():
        s = series_frames.get(tk)
        if s is None:
            continue
        j = s.select(["date", "adj_close"]).join(ind.rename({"observation_date": "date"}), on="date", how="inner").sort("date")
        px = [_f(x) for x in j["adj_close"].to_list()]
        fwd = [(px[i + h] / px[i] - 1.0) if (i + h < len(px) and px[i] and px[i + h] is not None) else None for i in range(len(px))]
        vals = {}
        for fc in FACTOR_COLS:
            if fc == "SMA20_DEV":
                vals[fc] = [(p / s_ - 1.0) if (p is not None and s_) else None for p, s_ in zip(px, [_f(x) for x in j["SMA_20_S1"].to_list()])] if "SMA_20_S1" in j.columns else None
            else:
                vals[fc] = [_f(x) for x in j[fc].to_list()] if fc in j.columns else None
        per[tk] = {"dates": j["date"].to_list(), "fwd": fwd, "vals": vals}
    all_dates = sorted({d for p in per.values() for d in p["dates"]})
    rows, by_factor = [], {fc: [] for fc in FACTOR_COLS}
    spreads = {fc: [] for fc in FACTOR_COLS}
    for d in all_dates:
        for fc in FACTOR_COLS:
            xs, ys = [], []
            for tk, p in per.items():
                if p["vals"].get(fc) is None or d not in p["dates"]:
                    continue
                i = p["dates"].index(d)
                x, y = p["vals"][fc][i], p["fwd"][i]
                if x is not None and y is not None:
                    xs.append(x)
                    ys.append(y)
            if len(xs) >= 3:
                ic = spearman(xs, ys)
                if ic is not None:
                    rows.append({"date": d, "factor": fc, "ic": ic, "n": len(xs)})
                    by_factor[fc].append(ic)
                    order = sorted(range(len(xs)), key=lambda k: xs[k])
                    half = len(order) // 2
                    if half >= 1 and len(order) >= 4:
                        spreads[fc].append(_mean([ys[k] for k in order[-half:]]) - _mean([ys[k] for k in order[:half]]))
    summ = {}
    for fc, ics in by_factor.items():
        if not ics:
            summ[fc] = {"state": "NO_DATA"}
            continue
        m, sd = _mean(ics), _std(ics)
        summ[fc] = {"n_dates": len(ics), "mean_ic": m, "ic_ir": (m / sd) if sd else None, "hit_rate": sum(1 for x in ics if x > 0) / len(ics), "top_minus_bottom_fwd": _mean(spreads[fc]) if spreads[fc] else None}
    frame = pl.DataFrame(rows) if rows else None
    wide = None
    if frame is not None and frame.height:
        wide = frame.pivot(on="factor", index="date", values="ic").sort("date")
    return wide, {"state": "OK" if rows else "NO_OVERLAP", "tickers": len(per), "horizon": h, "factors": summ, "rows": len(rows)}


# ── 統計 ───────────────────────────────────────────────────────────────────────────────────────
def stats_rows(series_frames: dict) -> tuple:
    rows, rets_by = [], {}
    for tk, s in series_frames.items():
        s = s.sort("date")
        px = [_f(x) for x in s["adj_close"].to_list()]
        dts = s["date"].to_list()
        pairs = [(dts[i], px[i] / px[i - 1] - 1.0) for i in range(1, len(px)) if px[i] is not None and px[i - 1]]   # 日期與報酬一起過濾(缺價不錯位 · Codex #622 P2)
        r = [v for _, v in pairs]
        rets_by[tk] = dict(pairs)
        n = len(r)
        if n < 10:
            rows.append({"ticker": tk, "n": n, "state": "INSUFFICIENT"})
            continue
        m, sd = _mean(r), _std(r, ddof=0)
        skew = (sum((x - m) ** 3 for x in r) / n) / (sd ** 3) if sd else None
        kurt = ((sum((x - m) ** 4 for x in r) / n) / (sd ** 4) - 3.0) if sd else None
        jb = (n / 6.0) * (skew ** 2 + (kurt ** 2) / 4.0) if (skew is not None and kurt is not None) else None

        def acf(k):
            if n <= k + 1 or not sd:
                return None
            return sum((r[i] - m) * (r[i + k] - m) for i in range(n - k)) / sum((x - m) ** 2 for x in r)

        def vr(q):
            if n < q * 5 or not sd:
                return None
            rq = [sum(r[i:i + q]) for i in range(0, n - q + 1, q)]
            vq = _std(rq, ddof=0)
            return (vq ** 2) / (q * sd ** 2) if (vq is not None and sd) else None
        rows.append({"ticker": tk, "n": n, "state": "OK", "mean": m, "std": sd, "skew": skew, "excess_kurtosis": kurt, "jarque_bera": jb, "acf_1": acf(1), "acf_5": acf(5),
                     "variance_ratio_2": vr(2), "variance_ratio_5": vr(5), "positive_pct": sum(1 for x in r if x > 0) / n, "max": max(r), "min": min(r),
                     "periods_per_year": _ppy(s["date"].to_list())})
    tks = sorted(rets_by)
    corr = {"ticker": tks}
    for a in tks:
        col = []
        for b in tks:
            common = sorted(set(rets_by[a]) & set(rets_by[b]))
            xa, xb = [rets_by[a][d] for d in common], [rets_by[b][d] for d in common]
            if len(common) < 10:
                col.append(None)
                continue
            ma, mb = _mean(xa), _mean(xb)
            den = math.sqrt(sum((x - ma) ** 2 for x in xa) * sum((y - mb) ** 2 for y in xb))
            col.append(sum((x - ma) * (y - mb) for x, y in zip(xa, xb)) / den if den else None)
        corr[a] = col
    return pl.DataFrame(rows), pl.DataFrame(corr)


# ── quant(整合 · 登 VAP)───────────────────────────────────────────────────────────────────────
def _sem_cols(frame, x: str, kind: str) -> dict:
    out = {x: V7._sem("VQG.X.DATE", "observation_date", "date", "date", "x")}
    for c in frame.columns:
        if c == x:
            continue
        out[c] = V7._sem("VQG.%s.%s" % (kind, c.upper()), c, "ratio" if c.startswith(("eq_", "ic", "SMA", "RSI")) else "value", str(frame.schema[c]), "y")
    return out


def quant(export_dir: Path, receipt_dir: Path | None = None) -> dict:
    export_dir = Path(export_dir)
    rp = export_dir / "export_receipt.json"
    rec = json.loads(rp.read_text(encoding="utf-8"))
    series_frames = {p.stem: pl.read_parquet(p) for p in sorted((export_dir / "series").glob("*.parquet"))}
    ind_frames = {p.stem: pl.read_parquet(p) for p in sorted((export_dir / "indicators").glob("*.parquet"))}
    at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    root, how = Path(rec.get("vdf_root") or "."), rec.get("vdf_root_from") or "receipt"
    cal, snaps = (rec.get("lamp_reason") or {}).get("calendar_mode", "derive"), "latest"
    man_p, cfg_p = export_dir / "vqg_connection_manifest.json", export_dir / V7.VAP_CONFIG_NAME
    man, cfg = json.loads(man_p.read_text(encoding="utf-8")), json.loads(cfg_p.read_text(encoding="utf-8"))
    conns, sources = man["connections"], cfg["sources"]
    conns = [c for c in conns if not str(c.get("contractId", "")).startswith(("VQG-BACKTEST", "VQG-FACTOR"))]
    sources = [s for s in sources if not str(s.get("vqgContractId", "")).startswith(("VQG-BACKTEST", "VQG-FACTOR"))]
    (export_dir / "backtest").mkdir(exist_ok=True)
    (export_dir / "factor").mkdir(exist_ok=True)
    (export_dir / "stats").mkdir(exist_ok=True)
    bt_summary, bt_tables, bt_missing, gate_fail = [], [], {}, 0
    for tk, ind in ind_frames.items():
        s = series_frames.get(tk)
        if s is None:
            continue
        curve, summ, miss = backtest(s, ind, tk)
        if miss:
            bt_missing[tk] = miss
        if curve is None:
            continue
        bt_summary.extend(summ)
        p = export_dir / "backtest" / (tk + ".parquet")
        curve.write_parquet(p)
        g = V7.ui_gate(curve, "date")
        bt_tables.append({"ticker": tk, "kind": "BACKTEST", "file": "backtest/" + p.name, "rows": curve.height, "columns": curve.columns, "ui_gate": g})
        if g["gate"] == "PASS":
            sid = "VQG-BACKTEST-" + tk
            conns.append(V7.build_connection("VQG-BACKTEST-v1", sid, "INDICATOR_RESULT", "date", _sem_cols(curve, "date", "BT"), p, curve.height, cal, snaps, root, how, at, tk.replace("_", ".")))
            sources.append({"id": sid, "vqgContractId": "VQG-BACKTEST-v1", "authority": "VQG", "alias": "VQG_BACKTEST_" + tk, "engine": "PARQUET", "location": str(p), "table": "backtest_" + tk, "enabled": True, "maxRows": int(V4.MAX_INPUT_ROWS)})
        else:
            gate_fail += 1
    if bt_summary:
        bs = pl.DataFrame(bt_summary)
        bs.write_parquet(export_dir / "backtest" / "vqg_backtest_summary.parquet")
        bs.write_csv(export_dir / "backtest" / "vqg_backtest_summary.csv")
        (export_dir / "backtest" / "vqg_backtest_summary.json").write_text(json.dumps(bt_summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    ic_wide, ic_summary = factor_ic(ind_frames, series_frames)
    if ic_wide is not None and ic_wide.height:
        p = export_dir / "factor" / "vqg_factor_ic.parquet"
        ic_wide.write_parquet(p)
        ic_wide.write_csv(export_dir / "factor" / "vqg_factor_ic.csv")
        g = V7.ui_gate(ic_wide, "date")
        ic_summary["ui_gate"] = g
        if g["gate"] == "PASS":
            conns.append(V7.build_connection("VQG-FACTOR-v1", "VQG-FACTOR-IC", "RISK_QUALITY", "date", _sem_cols(ic_wide, "date", "IC"), p, ic_wide.height, cal, snaps, root, how, at, "CROSS_SECTION"))
            sources.append({"id": "VQG-FACTOR-IC", "vqgContractId": "VQG-FACTOR-v1", "authority": "VQG", "alias": "VQG_FACTOR_IC", "engine": "PARQUET", "location": str(p), "table": "factor_ic", "enabled": True, "maxRows": int(V4.MAX_INPUT_ROWS)})
    (export_dir / "factor" / "vqg_factor_summary.json").write_text(json.dumps(ic_summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    st, corr = stats_rows(series_frames)
    st.write_parquet(export_dir / "stats" / "vqg_stats.parquet")
    st.write_csv(export_dir / "stats" / "vqg_stats.csv")
    corr.write_parquet(export_dir / "stats" / "vqg_return_corr.parquet")
    corr.write_csv(export_dir / "stats" / "vqg_return_corr.csv")
    man["connections"], man["version"] = conns, VERSION_TAIL
    cfg["sources"], cfg["version"] = sources, "VQG %s export-vap" % VERSION_TAIL
    V7._write_json(man_p, man)
    V7._write_json(cfg_p, cfg)
    out_root = export_dir.parent
    (out_root / V7.VAP_CONFIG_NAME).write_text(cfg_p.read_text(encoding="utf-8"), encoding="utf-8")
    lamp = "RED" if not bt_summary else ("YELLOW" if (gate_fail or bt_missing or ic_summary["state"] != "OK") else "GREEN")
    summary = {"schema": "VIA-VQG-QUANT/1.0", "vqgVersion": VERSION_TAIL, "at": at, "lamp": lamp, "tickers": len(ind_frames), "backtest": {"tables": len(bt_tables), "strategies": list(STRATEGIES), "missing": bt_missing, "ui_gate_fail": gate_fail, "rows": len(bt_summary)},
               "factor": {k: v for k, v in ic_summary.items() if k != "ui_gate"}, "stats": {"tickers": st.height, "corr_shape": [corr.height, corr.width - 1]},
               "vap_sources_added": sum(1 for s in sources if str(s.get("vqgContractId", "")).startswith(("VQG-BACKTEST", "VQG-FACTOR"))),
               "meaning": {"GREEN": "回測 / 因子 / 統計齊 · 回測曲線與 IC 表已登 VAP", "YELLOW": "已算 · 但 %s" % " / ".join(x for x in (("因子 %s" % ic_summary["state"] if ic_summary["state"] != "OK" else ""), ("缺指標欄 %s" % json.dumps(bt_missing, ensure_ascii=False) if bt_missing else ""), ("%d 張回測表過不了 VAP 閘" % gate_fail if gate_fail else "")) if x), "RED": "沒有任何票能回測"}[lamp]}
    rec["quant"], rec["engine"] = summary, "VeritaQuantGuard " + VERSION_TAIL
    rec.setdefault("steps", []).append({"step": "⑨ 量化分析②(v0109 回測 / 多因子 / 統計 → VAP)", "lamp": lamp, "detail": "回測表 %d · 因子 %s · 統計 %d 票 · VAP 新來源 %d" % (len(bt_tables), ic_summary["state"], st.height, summary["vap_sources_added"])})
    rec["tables"] = [t for t in rec.get("tables", []) if t.get("kind") != "BACKTEST"] + bt_tables
    rec["vap_sources"] = len(sources)
    rp.write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    V8._resign(export_dir)
    if receipt_dir is not None:
        lp = Path(receipt_dir) / "VQG_ExportVAP_latest.json"
        if lp.is_file():
            lr = json.loads(lp.read_text(encoding="utf-8"))
            lr["quant"], lr["engine"], lr["vap_sources"] = summary, "VeritaQuantGuard " + VERSION_TAIL, len(sources)
            lp.write_text(json.dumps(lr, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        lj = out_root / "latest.json"
        if lj.is_file():
            d = json.loads(lj.read_text(encoding="utf-8"))
            d["vap_sources"] = len(sources)
            lj.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def export_vap_0109(args) -> int:
    rc = _EXPORT_VAP_0108(args)
    if rc != 0:
        return rc
    via = V7.via_root(getattr(args, "via_root", None))
    out_root = Path(getattr(args, "out_dir", None) or ((via / "VIA_Reports" / "vqg" / "vap_export") if via else Path.cwd() / "VIA_Reports" / "vqg" / "vap_export"))
    receipt_dir = Path(getattr(args, "receipt_dir", None) or ((via / "VIA_Reports" / "vqg") if via else Path.cwd() / "VIA_Reports" / "vqg"))
    try:
        final = Path(json.loads((out_root / "latest.json").read_text(encoding="utf-8"))["export_dir"])
        s = quant(final, receipt_dir)
        print("[%s] VQG %s 量化分析② · %s → %s" % (s["lamp"], VERSION_TAIL, s["meaning"], final / "backtest"), flush=True)
    except (OSError, ValueError, KeyError) as error:
        print("[RED] VQG %s 量化分析②中斷 · %s: %s" % (VERSION_TAIL, type(error).__name__, str(error)[:200]), flush=True)
        return 2
    return rc


# ── 自測 ───────────────────────────────────────────────────────────────────────────────────────
def _bars_varied(ticker, start, n, base, drift, seed):
    out, p, x = [], base, seed
    for i in range(n):
        x = (x * 1103515245 + 12345) % (2 ** 31)
        noise = (x / 2 ** 31 - 0.5) * 0.02
        p = p * (1.0 + drift + noise)
        d = start + timedelta(days=i)
        out.append((d.isoformat(), ticker, p, p * 1.01, p * 0.99, p, p, 1000.0 + (x % 500)))
    return out


def selftest() -> int:
    ok = total = 0

    def chk(label, cond):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print("  [%s] %s" % ("PASS" if cond else "FAIL", label), flush=True)
    print("[VQG %s selftest]" % VERSION_TAIL, flush=True)
    chk("① 前版 v0108 SHA-256 釘住 · 公式引擎仍 v0104 · 第一部分一字不動(CORE 來自 v0104)", PRIOR_SHA_OK and ENGINE_VERSION == "v0104" and V4.CORE is PRIOR.V4.CORE)
    chk("② spearman:完全同序 1 · 反序 −1 · 不足 3 點 None;擴張百分位只看到 t", spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0 and spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0 and spearman([1, 2], [1, 2]) is None
        and expanding_pct([5, 1, 2, 3, 4, 9], 9) == 1.0 and expanding_pct([1, 2, 3], 3) is None)
    env_root = os.environ.pop("VQG_VDF_ROOT", None)
    try:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            vdf = t / "vdf_database"
            (vdf / "output_hub").mkdir(parents=True)
            d0 = date(2025, 9, 1)
            rows = []
            for i, (tk, base, drift, seed) in enumerate((("2330.TW", 100.0, 0.0008, 7), ("2317.TW", 80.0, -0.0003, 11), ("2454.TW", 60.0, 0.0012, 13), ("3008.TW", 200.0, 0.0001, 17))):
                rows += _bars_varied(tk, d0, 420, base, drift, seed)
            V5._vdf_like(vdf / "output_hub" / "tw_daily_prices_20261101_120000.parquet", rows)
            cat = catalog(vdf)
            chk("③ catalog:全掃 1 檔 · 認得 date/ticker/adj_close/volume · open/high/low/close 其中未認得者列為候選因子 · 選項含策略與因子 · md 寫出",
                cat["files"] == 1 and {"date", "ticker", "adj_close", "volume"} <= set(cat["options"]["series_inputs"]) and "open" in cat["options"]["candidate_factors"] and "SMA_TREND" in cat["options"]["strategies"])
            write_catalog(cat, t / "cat")
            chk("③b vqg_catalog_options.json / .md", (t / "cat" / "vqg_catalog_options.json").is_file() and (t / "cat" / "vqg_catalog_options.md").is_file())
            out = t / "out"
            ns = types.SimpleNamespace(via_root=None, root=str(vdf), out_dir=str(out), receipt_dir=str(t / "rcpt"), ticker=[], max_tickers=50, metrics=None, windows=None,
                                       as_of=d0 + timedelta(days=440), series_rows=0, indicator_points=330, calendar="auto", snapshots="latest", market=None, vap_port=8765)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
                rc = export_vap_0109(ns)
            ed = Path(json.loads((out / "latest.json").read_text(encoding="utf-8"))["export_dir"]) if (out / "latest.json").is_file() else None
            rec = json.loads((ed / "export_receipt.json").read_text(encoding="utf-8")) if ed else {}
            q = rec.get("quant") or {}
            chk("④ export-vap(v0108 原樣)→ quant:rc 0 · 回測表 4 · 因子 OK(4 票 · h=5)· 統計 4 票 · VAP 新來源 5(4 回測 + IC)· 燈 GREEN",
                rc == 0 and q.get("backtest", {}).get("tables") == 4 and q.get("factor", {}).get("state") == "OK" and q.get("stats", {}).get("tickers") == 4 and q.get("vap_sources_added") == 5 and q.get("lamp") == "GREEN")
            cv = pl.read_parquet(ed / "backtest" / "2330_TW.parquet") if ed else pl.DataFrame()
            eq, pos, px = cv["eq_SMA_TREND"].to_list(), cv["pos_SMA_TREND"].to_list(), cv["adj_close"].to_list()
            lag_ok = all(abs((eq[i] / eq[i - 1] - 1.0) - pos[i - 1] * (px[i] / px[i - 1] - 1.0)) < 1e-9 for i in range(1, len(eq)))
            chk("⑤ 回測不偷看:eq[t]/eq[t−1]−1 = pos[t−1] × 價格報酬(訊號落後一日)· 曲線有 eq_BUY_HOLD / 三策略", lag_ok and {"eq_BUY_HOLD", "eq_RSI_MEANREV", "eq_MACD_HIST", "date"} <= set(cv.columns))
            bs = json.loads((ed / "backtest" / "vqg_backtest_summary.json").read_text(encoding="utf-8"))
            r = {(x["ticker"], x["strategy"]): x for x in bs}
            x = r[("2330_TW", "RSI_MEANREV")]
            chk("⑥ 摘要:max_drawdown ≤ 0 · exposure / hit_rate 0..1 · CAGR 有(歷史 ≥ 300 天 · 年化用資料推)· RSI 門檻規則寫「自身擴張百分位」不是 30/70 · rf 缺照實標",
                x["max_drawdown"] <= 0 and 0 <= x["exposure"] <= 1 and (x["hit_rate"] is None or 0 <= x["hit_rate"] <= 1) and x["cagr"] is not None and x["periods_per_year"] and "百分位" in x["threshold_rule"] and "RF_SERIES_MISSING" in x["sharpe_rf"])
            fs = json.loads((ed / "factor" / "vqg_factor_summary.json").read_text(encoding="utf-8"))
            ic = pl.read_parquet(ed / "factor" / "vqg_factor_ic.parquet")
            icv = [v for c in ic.columns if c != "date" for v in ic[c].to_list() if v is not None]
            chk("⑦ 因子:IC 全在 −1..1 · 每因子有 mean_ic / ic_ir / hit_rate · 前半−後半價差有值 · 寬表 x=date", icv and all(-1.0000001 <= v <= 1.0000001 for v in icv) and all(("mean_ic" in v) for v in fs["factors"].values() if v.get("state") != "NO_DATA")
                and any(v.get("top_minus_bottom_fwd") is not None for v in fs["factors"].values() if "mean_ic" in v) and ic.columns[0] == "date")
            st = pl.read_parquet(ed / "stats" / "vqg_stats.parquet")
            corr = pl.read_parquet(ed / "stats" / "vqg_return_corr.parquet")
            s0 = st.to_dicts()[0]
            chk("⑧ 統計:4 票 · JB ≥ 0 · 自相關在 −1..1 · 變異比 > 0 · 相關矩陣 4×4 對角 1", st.height == 4 and s0["jarque_bera"] >= 0 and -1 <= s0["acf_1"] <= 1 and s0["variance_ratio_2"] > 0 and corr.height == 4
                and all(abs(corr[tk][i] - 1.0) < 1e-9 for i, tk in enumerate(corr["ticker"].to_list())))
            man = json.loads((ed / "vqg_connection_manifest.json").read_text(encoding="utf-8"))
            new = [c for c in man["connections"] if c["contractId"] in ("VQG-BACKTEST-v1", "VQG-FACTOR-v1")]
            fp_ok = all(V7.vap_fingerprint({k: v for k, v in c.items() if k != "fingerprint"}) == c["fingerprint"] for c in new)
            sha_ok = all(V7._sha256_file(ed / c["dataFile"]) == c["dataSha256"] for c in new)
            cfg = json.loads((ed / V7.VAP_CONFIG_NAME).read_text(encoding="utf-8"))
            chk("⑨ VAP 契約:5 筆新連線 AUTHORIZED · 指紋 = VAP 公式 · dataSha256 = 檔 · datasetType ∈ INDICATOR_RESULT / RISK_QUALITY · config 來源含 VQG-BACKTEST-2330_TW 與 VQG-FACTOR-IC · 舊 4 筆原樣",
                len(new) == 5 and fp_ok and sha_ok and {c["datasetType"] for c in new} <= {"INDICATOR_RESULT", "RISK_QUALITY"} and {"VQG-BACKTEST-2330_TW", "VQG-FACTOR-IC"} <= {s["id"] for s in cfg["sources"]}
                and sum(1 for c in man["connections"] if c["contractId"] in ("VQG-SERIES-v1", "VQG-INDICATOR-v1")) == 8)
            sums_ok = all(V7._sha256_file(ed / ln.split("  ", 1)[1]) == ln.split("  ", 1)[0] for ln in (ed / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if ln.strip())
            chk("⑩ SHA256SUMS 全對(含 backtest / factor / stats 新檔)· 收據 step ⑨ · 根 config 與夾內同", sums_ok and any(s["step"].startswith("⑨") for s in rec["steps"]) and (out / V7.VAP_CONFIG_NAME).read_text(encoding="utf-8") == (ed / V7.VAP_CONFIG_NAME).read_text(encoding="utf-8"))
            s2 = quant(ed, t / "rcpt")
            man2 = json.loads((ed / "vqg_connection_manifest.json").read_text(encoding="utf-8"))
            chk("⑪ quant 重跑冪等:連線不重複(仍 13)· 燈同", len(man2["connections"]) == 13 and s2["lamp"] == "GREEN")
            two = {k: v for k, v in list({p.stem: pl.read_parquet(p) for p in (ed / "indicators").glob("*.parquet")}.items())[:2]}
            _, fs2 = factor_ic(two, {k: pl.read_parquet(ed / "series" / (k + ".parquet")) for k in two})
            chk("⑫ 票 < 3 → 因子 INSUFFICIENT_TICKERS 照實(不假算)", fs2["state"] == "INSUFFICIENT_TICKERS")
            sA = pl.read_parquet(ed / "series" / "2330_TW.parquet").sort("date")
            vals = sA["adj_close"].to_list()
            vals[40] = None                                                    # 中間缺一個價(v0105 load_series 會留 null 列)
            sB = sA.with_columns(pl.Series("adj_close", vals, dtype=pl.Float64))
            _, corrAB = stats_rows({"A": sA, "B": sB})
            cAB = corrAB["B"].to_list()[corrAB["ticker"].to_list().index("A")]
            chk("⑬ 統計:缺價那一列的日期與報酬一起過濾 → 同一序列挖一個洞仍相關 1.0(錯位會掉;Codex #622 P2)", cAB is not None and abs(cAB - 1.0) < 1e-9)
    finally:
        if env_root is not None:
            os.environ["VQG_VDF_ROOT"] = env_root
    print("  == v0109 %d/%d" % (ok, total), flush=True)
    with contextlib.redirect_stdout(io.StringIO()):
        prior_rc = PRIOR.selftest()
    good = ok == total and prior_rc == 0
    print("[%s] VQG %s selftest · 本版 %d/%d · 前版鏈 v0108 %s" % ("PASS" if good else "FAIL", VERSION_TAIL, ok, total, "PASS" if prior_rc == 0 else "FAIL"), flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = next((a for a in argv if not a.startswith("-")), "scan")
    if cmd in ("selftest", "test") or "--selftest" in argv:
        try:
            return selftest()
        except Exception as error:  # noqa: BLE001
            print("[FAIL] VQG %s selftest 中斷 · %s: %s" % (VERSION_TAIL, type(error).__name__, str(error)[:200]), flush=True)
            return 1
    if cmd == "catalog":
        root_arg = next((argv[i + 1] for i, a in enumerate(argv) if a in ("--root", "--vdf-root") and i + 1 < len(argv)), None)
        root, how = (Path(root_arg), "--root") if root_arg else V5.default_root()
        out_arg = next((argv[i + 1] for i, a in enumerate(argv) if a == "--out" and i + 1 < len(argv)), None)
        via = V7.via_root(None)
        out = Path(out_arg) if out_arg else ((via / "VIA_Reports" / "vqg") if via else Path.cwd() / "VIA_Reports" / "vqg")
        try:
            cat = catalog(root)
        except (OSError, ValueError) as error:
            print("[RED] VQG %s catalog · 庫根 %s(%s)· %s" % (VERSION_TAIL, root, how, error), flush=True)
            return 2
        cat["vdfRootFrom"] = how
        write_catalog(cat, out)
        print("[GREEN] VQG %s catalog · parquet %d · 序列輸入 %d · 候選因子 %d → %s" % (VERSION_TAIL, cat["files"], len(cat["options"]["series_inputs"]), len(cat["options"]["candidate_factors"]), out / "vqg_catalog_options.md"), flush=True)
        return 0
    if cmd == "quant":
        ed = next((argv[i + 1] for i, a in enumerate(argv) if a == "--export-dir" and i + 1 < len(argv)), None)
        via = V7.via_root(None)
        out_root = (via / "VIA_Reports" / "vqg" / "vap_export") if via else Path.cwd() / "VIA_Reports" / "vqg" / "vap_export"
        if not ed and (out_root / "latest.json").is_file():
            ed = json.loads((out_root / "latest.json").read_text(encoding="utf-8")).get("export_dir")
        if not ed or not Path(ed).is_dir():
            print("[RED] VQG %s quant · 找不到匯出夾(--export-dir 或 %s)" % (VERSION_TAIL, out_root / "latest.json"), flush=True)
            return 2
        s = quant(Path(ed), (via / "VIA_Reports" / "vqg") if via else None)
        print("[%s] VQG %s quant · %s → %s" % (s["lamp"], VERSION_TAIL, s["meaning"], Path(ed) / "backtest"), flush=True)
        return 0 if s["lamp"] != "RED" else 2
    if cmd == "export-vap":
        _orig = V8.export_vap_0108
        V8.export_vap_0108 = export_vap_0109                                 # v0108 main 換裝時指到的名字 → 走本版(先 v0108 原樣再量化分析②)
        try:
            return V8.main(argv)
        finally:
            V8.export_vap_0108 = _orig
    if "--help" in argv or "-h" in argv:
        rc = PRIOR.main(argv)
        print("v0109:catalog(資料庫全掃 → 選項)· quant [--export-dir](回測 / 多因子 / 統計 → VAP)· export-vap 自動接 quant", flush=True)
        return rc
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
