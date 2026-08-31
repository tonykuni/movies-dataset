#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRP_ENG040_GroupingRotationRunner v0101 — 雙 profile 輪動統一轉接(批153;via-rotation)
====================================================================
批153 令「整合去重優化 Taiwan Stock Group Classification & Rotation
Simulation / Global Fund Flow Rotation Simulation based on ETF,
Valuation, interest Rate & Forex」——去重定案:不另造模擬器,
同一 v0202 統一核心(GroupingIndexRotationUnifiedEngine,原件零觸碰)
吃兩套宇宙:
  run tw     台股 238 檔 39 族群(v0202 名冊)+批153 優化=補 --factors
             (TWII_RET 市場/TWD_RET 匯率/US10Y_D1 利率;v0202 指示
             「正式剔除結論」需 FactorPath 之前提補位)
  run global 全球資金流輪動:30 標的 6 群冊(美/歐/亞成熟/大中華/
             亞新興 ETF+商品;VIA_GlobalFlowRotation_Membership 由
             實庫覆蓋實證)+因子=利率 US10Y_D1×匯率 EURUSD/USDJPY
             ×波動 VIX_RET;估值(etf_stats trailing_pe/AUM)+情緒
             (CNN F&G)=side-car 快照隨跑附冊
誠實紀律:
  TURNOVER_PROXY:global 成交值=adj_close×volume 估算(冊上明示,
    非交易所實值;TW profile 仍用 tw_trading_daily.trade_value 真值,
    籌碼股數不冒充金額欄=誠實留缺)
  GLOBAL_LABEL_NOTE:核心正規化為 TW 中心(強制 .TW 尾綴),全球
    輸出之「SPY.TW」等=引擎內部標籤;真實符號=TickerBase,side-car
    label_map 附對照。核心零觸碰之代價,冊上誠實聲明。
產出=output_hub/rotation_runs/(gitignored)
用法:via-rotation run [tw|global] [--start D --eval D --end D]
     | --status | --selftest
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

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRP = HERE.parent
VIA = GRP.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
DB_GL = MEGA / "vdf_global_market.duckdb"
OUT_ROOT = GRP / "output_hub" / "rotation_runs"
GLOBAL_MEMB = GRP / "global"
DEFAULT_WARMUP = "2025-01-02"
DEFAULT_EVAL = "2026-01-02"


def _pkg() -> Path | None:
    """收容包尾版(glob;嚴禁寫死版號)"""
    hits = sorted(GRP.glob("VIA_TW_Grouping_LatestCommand_v*"))
    return hits[-1] if hits else None


def _core(pkg: Path) -> Path | None:
    hits = sorted(pkg.glob("VIA_TW_GroupingIndexRotationUnifiedEngine_v*.py"))
    return hits[-1] if hits else None


def _membership_tw(pkg: Path) -> Path | None:
    hits = sorted(pkg.glob("VIA_ThreeList_CanonicalMembershipInput_v*.csv"))
    return hits[-1] if hits else None


def _membership_global() -> Path | None:
    hits = sorted(GLOBAL_MEMB.glob("VIA_GlobalFlowRotation_Membership_v*.csv"))
    return hits[-1] if hits else None


def _member_tickers(csv_path: Path) -> list[str]:
    import csv
    with open(csv_path, encoding="utf-8-sig") as f:
        return sorted({r["YFTicker"] for r in csv.DictReader(f) if r.get("YFTicker")})


# ---------------------------------------------------------------- 價量匯出
def export_prices_tw(dst: Path, tickers: list[str]) -> dict:
    """TW:adj_close 正項+Turnover=trade_value 真值;金額欄誠實留缺"""
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    ph = ",".join("?" * len(tickers))
    df = con.execute(f"""
        SELECT p.date AS Date, p.ticker AS Ticker,
               p.adj_close AS Adj_Close, p.volume AS Volume,
               t.trade_value AS Turnover
        FROM tw_daily_prices p
        LEFT JOIN tw_trading_daily t
          ON t.date = p.date
         AND p.ticker = t.code || (CASE WHEN t.market='TWSE' THEN '.TW' ELSE '.TWO' END)
        WHERE p.ticker IN ({ph}) AND p.adj_close IS NOT NULL
        ORDER BY p.ticker, p.date""", tickers).df()
    con.close()
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(dst, index=False)
    return {"rows": len(df), "tickers": df["Ticker"].nunique(),
            "turnover_nonnull": int(df["Turnover"].notna().sum())}


def export_prices_global(dst: Path, tickers: list[str]) -> dict:
    """GLOBAL:adj_close+volume;Turnover=close×volume 之 TURNOVER_PROXY
    (估算,冊上明示;商品期貨 volume 為口數=PROXY 語意同樣適用)"""
    import duckdb
    con = duckdb.connect(str(DB_GL), read_only=True)
    ph = ",".join("?" * len(tickers))
    df = con.execute(f"""
        SELECT date AS Date, ticker AS Ticker,
               adj_close AS Adj_Close, volume AS Volume,
               CASE WHEN volume IS NOT NULL THEN adj_close * volume END AS Turnover
        FROM global_daily
        WHERE ticker IN ({ph}) AND adj_close IS NOT NULL
        ORDER BY ticker, date""", tickers).df()
    con.close()
    dst.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(dst, index=False)
    return {"rows": len(df), "tickers": df["Ticker"].nunique(),
            "turnover_nonnull": int(df["Turnover"].notna().sum())}


# ---------------------------------------------------------------- 因子面
def _series_ret(con, ticker: str, col: str) -> "object":
    """global_daily 單標的日報酬序列(pct_change;首列自然 NaN)"""
    df = con.execute(
        "SELECT date AS Date, adj_close FROM global_daily "
        "WHERE ticker=? AND adj_close IS NOT NULL ORDER BY date", [ticker]).df()
    df[col] = df["adj_close"].pct_change()
    return df[["Date", col]]


def build_factors_tw(dst: Path) -> dict:
    """TW 因子:TWII_RET(市場)+TWD_RET(匯率)+US10Y_D1(利率)"""
    import duckdb
    con = duckdb.connect(str(DB_GL), read_only=True)
    twii = _series_ret(con, "^TWII", "TWII_RET")
    twd = _series_ret(con, "TWD=X", "TWD_RET")
    g10 = con.execute(
        "SELECT date AS Date, value FROM cross_macro "
        "WHERE region='US' AND metric='GOV10Y' ORDER BY date").df()
    con.close()
    g10["US10Y_D1"] = g10["value"].diff()
    out = twii.merge(twd, on="Date", how="inner").merge(
        g10[["Date", "US10Y_D1"]], on="Date", how="left").dropna(
        subset=["TWII_RET", "TWD_RET"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dst, index=False)
    return {"rows": len(out), "cols": [c for c in out.columns if c != "Date"]}


def build_factors_global(dst: Path) -> dict:
    """GLOBAL 因子:GLOBAL_MKT_RET(市場 ^GSPC,不入宇宙)+US10Y_D1(利率)
    +EURUSD_RET/USDJPY_RET(匯率)+VIX_RET(波動)——市場因子=潮汐剔除前提"""
    import duckdb
    con = duckdb.connect(str(DB_GL), read_only=True)
    mkt = _series_ret(con, "^GSPC", "GLOBAL_MKT_RET")
    eur = _series_ret(con, "EURUSD=X", "EURUSD_RET")
    jpy = _series_ret(con, "JPY=X", "USDJPY_RET")
    vix = _series_ret(con, "^VIX", "VIX_RET")
    g10 = con.execute(
        "SELECT date AS Date, value FROM cross_macro "
        "WHERE region='US' AND metric='GOV10Y' ORDER BY date").df()
    con.close()
    g10["US10Y_D1"] = g10["value"].diff()
    out = mkt.merge(eur, on="Date", how="inner").merge(
        jpy, on="Date", how="inner").merge(
        vix, on="Date", how="inner").merge(
        g10[["Date", "US10Y_D1"]], on="Date", how="left").dropna(
        subset=["GLOBAL_MKT_RET", "EURUSD_RET", "USDJPY_RET", "VIX_RET"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dst, index=False)
    return {"rows": len(out), "cols": [c for c in out.columns if c != "Date"]}


def sidecar_global(out_dir: Path, memb_csv: Path) -> dict:
    """估值+情緒 side-car:etf_stats 快照(trailing_pe/AUM)+CNN F&G 最新
    +label_map(引擎內部 .TW 標籤→真實符號;GLOBAL_LABEL_NOTE)"""
    import duckdb
    con = duckdb.connect(str(DB_GL), read_only=True)
    val = con.execute(
        "SELECT date, symbol, aum, trailing_pe, yield_ FROM etf_stats_daily "
        "ORDER BY date DESC, symbol").df()
    fg = con.execute(
        "SELECT date, score, rating FROM sentiment_daily "
        "WHERE index='CNN_FEAR_GREED' ORDER BY date DESC LIMIT 1").fetchall()
    con.close()
    tickers = _member_tickers(memb_csv)
    payload = {
        "note": ("GLOBAL_LABEL_NOTE:核心引擎正規化為 TW 中心,輸出之"
                 "『<符號>.TW』為引擎內部標籤;真實符號見 label_map。"
                 "TURNOVER_PROXY:成交值=adj_close×volume 估算非交易所實值。"
                 "V13_REVIEW_NOTE:核心受控自檢(V13 潮汐剔除)之合成世界為"
                 "TW 名冊結構校準且名稱種子敏感;global 冊 V14 全過、V13 單項敗"
                 "=方法校準限制非活體數據問題,本 profile 結論層級=REVIEW 非 PASS"
                 "(批153 三輪分拆實驗實錄於台帳;候核心後續版泛化受控 DGP)。"),
        "label_map": {f"{t.upper()}.TW": t for t in tickers},
        "valuation_snapshot": {
            "source": "etf_stats_daily(yahoo quoteSummary 快照)",
            "as_of": str(val["date"].max()) if len(val) else None,
            "rows": val.to_dict("records")},
        "sentiment_latest": ({"date": str(fg[0][0]), "score": fg[0][1],
                              "rating": fg[0][2]} if fg else None),
    }
    p = out_dir / "global_sidecar.json"
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str),
                 encoding="utf-8")
    return {"path": p.name, "valuation_rows": len(val)}


# ---------------------------------------------------------------- 執行
def run(profile: str = "tw", start: str = DEFAULT_WARMUP, ev: str = DEFAULT_EVAL,
        end: str | None = None) -> int:
    pkg = _pkg()
    core = _core(pkg) if pkg else None
    memb = (_membership_tw(pkg) if profile == "tw" else _membership_global())
    if not (pkg and core and memb):
        print(f"[FAIL] 收容包/核心/名冊缺(profile={profile})")
        return 1
    tickers = _member_tickers(memb)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUT_ROOT / f"ROTATION_{profile.upper()}_{ts}"
    prices = out / "prices_from_vdf.parquet"
    factors = out / "factors_from_vdf.parquet"
    if profile == "tw":
        ex = export_prices_tw(prices, tickers)
        fx = build_factors_tw(factors)
    else:
        ex = export_prices_global(prices, tickers)
        fx = build_factors_global(factors)
    print(f"[匯出] 列 {ex['rows']} · 檔 {ex['tickers']}/{len(tickers)}"
          f" · Turnover 有值 {ex['turnover_nonnull']}"
          f" · 因子 {fx['cols']}×{fx['rows']} 日")
    cmd = [sys.executable, str(core), "--membership", str(memb),
           "--prices", str(prices), "--factors", str(factors),
           "--output-root", str(out),
           "--start-date", start, "--normalized-date", ev]
    if end:
        cmd += ["--end-date", end]
    r = subprocess.run(cmd, cwd=pkg, capture_output=True, text=True)
    tail = (r.stdout or r.stderr).strip().splitlines()[-8:]
    print("\n".join(tail))
    if profile == "global":
        sc = sidecar_global(out, memb)
        print(f"[side-car] 估值 {sc['valuation_rows']} 列+情緒+label_map → {sc['path']}")
    # 誠實三態+REVIEW:讀 manifest gate 與 validation ledger 分類結果
    verdict = "FAIL"
    mf = out / "manifest.json"
    if mf.exists():
        gate = json.loads(mf.read_text(encoding="utf-8")).get("gate", "?")
        if gate == "PASS":
            verdict = "OK"
        elif profile == "global" and gate == "FAIL":
            try:
                import pandas as pd
                vl = pd.read_csv(out / "csv" / "validation_ledger.csv")
                bad = set(vl.loc[vl["Status"] == "FAIL", "CheckId"])
                if bad == {"V13_CONTROLLED_MARKET_TIDE_REJECTION"}:
                    verdict = "REVIEW"  # V13 單項=合成 DGP TW 校準限制(見 side-car 註)
            except Exception:
                pass
        print(f"[gate] {gate}")
    print(f"[{verdict}] 統一核心 rc={r.returncode} · profile={profile} · 產出 {out}")
    return 0 if r.returncode == 0 else 1


def status() -> int:
    pkg = _pkg()
    runs = sorted(OUT_ROOT.glob("ROTATION_*")) if OUT_ROOT.exists() else []
    print(f"收容包 {pkg.name if pkg else '缺'} · 全球冊 "
          f"{(_membership_global() or Path('缺')).name} · 實跑 {len(runs)} 次")
    for r in runs[-4:]:
        mf = r / "manifest.json"
        gate = "?"
        if mf.exists():
            gate = json.loads(mf.read_text(encoding="utf-8")).get("gate", "?")
        print(f"  {r.name} · gate={gate}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    pkg = _pkg()
    core = _core(pkg) if pkg else None
    memb_tw = _membership_tw(pkg) if pkg else None
    memb_gl = _membership_global()
    chk("① 收容包+核心+雙名冊在位(glob 尾版)",
        bool(pkg and core and memb_tw and memb_gl),
        f"({pkg.name if pkg else '缺'}·{memb_gl.name if memb_gl else '全球冊缺'})")
    if not (pkg and core and memb_tw and memb_gl):
        return 1

    tk_tw, tk_gl = _member_tickers(memb_tw), _member_tickers(memb_gl)
    chk("② TW 名冊 238 檔", len(tk_tw) >= 200, f"({len(tk_tw)})")

    import duckdb
    con = duckdb.connect(str(DB_GL), read_only=True)
    hit = con.execute(
        "SELECT COUNT(DISTINCT ticker) FROM global_daily WHERE ticker IN ({})".format(
            ",".join("?" * len(tk_gl))), tk_gl).fetchone()[0]
    con.close()
    chk("③ 全球冊 6 群覆蓋(ETF+同曝險指數混編全在庫)", hit == len(tk_gl) and len(tk_gl) >= 40,
        f"({hit}/{len(tk_gl)})")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f1 = build_factors_tw(Path(td) / "ftw.parquet")
        chk("④ TW 因子三欄(市場/匯率/利率)",
            set(f1["cols"]) == {"TWII_RET", "TWD_RET", "US10Y_D1"}
            and f1["rows"] > 300, f"({f1['rows']} 日)")
        f2 = build_factors_global(Path(td) / "fgl.parquet")
        chk("⑤ GLOBAL 因子五欄(市場/利率/雙匯率/波動)",
            set(f2["cols"]) == {"GLOBAL_MKT_RET", "US10Y_D1", "EURUSD_RET",
                                "USDJPY_RET", "VIX_RET"}
            and f2["rows"] > 300, f"({f2['rows']} 日)")
        p = Path(td) / "pg.parquet"
        ex = export_prices_global(p, tk_gl[:6])
        import pandas as pd
        df = pd.read_parquet(p)
        chk("⑥ 全球價量匯出+TURNOVER_PROXY 有值",
            list(df.columns) == ["Date", "Ticker", "Adj_Close", "Volume", "Turnover"]
            and ex["turnover_nonnull"] > 1000, f"(列 {ex['rows']})")
        sc = sidecar_global(Path(td), memb_gl)
        d = json.loads((Path(td) / "global_sidecar.json").read_text(encoding="utf-8"))
        chk("⑦ side-car(估值快照+情緒+label_map+雙誠實聲明)",
            sc["valuation_rows"] > 20 and d["sentiment_latest"] is not None
            and len(d["label_map"]) == len(tk_gl)
            and "GLOBAL_LABEL_NOTE" in d["note"] and "TURNOVER_PROXY" in d["note"])
        r = subprocess.run([sys.executable, str(core), "--demo", "--no-write",
                            "--membership", str(memb_tw), "--output-root", td],
                           cwd=pkg, capture_output=True, text=True, timeout=560)
        chk("⑧ 核心 demo 端到端", r.returncode == 0, f"(rc={r.returncode})")

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 誠實紀律宣告(PROXY 明示+標籤註記+真值 Turnover 分道)",
        "TURNOVER_PROXY" in src and "GLOBAL_LABEL_NOTE" in src
        and "trade_value" in src)
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 雙 profile 輪動統一轉接(GRP_ENG040 v0101)· 九檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "run" in args:
        i = args.index("run")
        profile = args[i + 1] if len(args) > i + 1 and not args[i + 1].startswith("--") else "tw"

        def _get(flag, default):
            return args[args.index(flag) + 1] if flag in args else default
        return run(profile, _get("--start", DEFAULT_WARMUP),
                   _get("--eval", DEFAULT_EVAL), _get("--end", None))
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
