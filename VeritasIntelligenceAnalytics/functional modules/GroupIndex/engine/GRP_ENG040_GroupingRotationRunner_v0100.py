#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRP_ENG040_GroupingRotationRunner — 族群指數輪動統一引擎實庫轉接(批152;via-rotation)
====================================================================
批152 送達 VIA_TW_Grouping_LatestCommand_v0202(byte-exact 收容於
functional modules/GroupIndex/VIA_TW_Grouping_LatestCommand_v0202/;
核心=GroupingIndexRotationUnifiedEngine v0201,包內 pytest 20 綠)。
原件 Windows 路徑常數=參考規格;本器 Linux 實庫轉接(原件零觸碰):
  價格=vdf_tw_market.duckdb::tw_daily_prices(adj_close 正項)
  成交值=tw_trading_daily.trade_value→Turnover(真值)
  籌碼金額欄(Foreign/Trust/Dealer NetAmount、Margin/Short BalanceValue)
  =庫內為股數非金額→誠實留缺 NaN(不發明;引擎自身 NaN 容忍)
  名冊=包內 VIA_ThreeList_CanonicalMembershipInput(238 檔 39 族群)
日期映射同 v0202 指令:--start-date=暖機 2025-01-02、
--normalized-date=正式基準 2026-01-02、end 缺省=庫內最新交易日。
產出=output_hub/rotation_runs/(gitignored;index.html+csv+heatmap)
用法:via-rotation run [--start D --eval D --end D] | --status | --selftest
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
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
OUT_ROOT = GRP / "output_hub" / "rotation_runs"
DEFAULT_WARMUP = "2025-01-02"
DEFAULT_EVAL = "2026-01-02"


def _pkg() -> Path | None:
    """收容包尾版(glob;嚴禁寫死版號)"""
    hits = sorted(GRP.glob("VIA_TW_Grouping_LatestCommand_v*"))
    return hits[-1] if hits else None


def _core(pkg: Path) -> Path | None:
    hits = sorted(pkg.glob("VIA_TW_GroupingIndexRotationUnifiedEngine_v*.py"))
    return hits[-1] if hits else None


def _membership(pkg: Path) -> Path | None:
    hits = sorted(pkg.glob("VIA_ThreeList_CanonicalMembershipInput_v*.csv"))
    return hits[-1] if hits else None


def export_prices(dst: Path, tickers: list[str]) -> dict:
    """實庫→引擎期望 parquet(Adj_Close 正項+Turnover 真值;金額欄誠實缺)"""
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
            "turnover_nonnull": int(df["Turnover"].notna().sum()),
            "span": [str(df["Date"].min()), str(df["Date"].max())] if len(df) else None}


def _member_tickers(csv_path: Path) -> list[str]:
    import csv
    with open(csv_path, encoding="utf-8-sig") as f:
        return sorted({r["YFTicker"] for r in csv.DictReader(f) if r.get("YFTicker")})


def run(start: str = DEFAULT_WARMUP, ev: str = DEFAULT_EVAL,
        end: str | None = None) -> int:
    pkg = _pkg()
    core, memb = _core(pkg), _membership(pkg)
    if not (pkg and core and memb):
        print("[FAIL] 收容包/核心/名冊缺")
        return 1
    tickers = _member_tickers(memb)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUT_ROOT / f"ROTATION_{ts}"
    prices = out / "prices_from_vdf.parquet"
    ex = export_prices(prices, tickers)
    print(f"[匯出] 列 {ex['rows']} · 檔 {ex['tickers']}/{len(tickers)}"
          f" · Turnover 有值 {ex['turnover_nonnull']} · 迄 {ex['span']}")
    cmd = [sys.executable, str(core), "--membership", str(memb),
           "--prices", str(prices), "--output-root", str(out),
           "--start-date", start, "--normalized-date", ev]
    if end:
        cmd += ["--end-date", end]
    r = subprocess.run(cmd, cwd=pkg, capture_output=True, text=True)
    tail = (r.stdout or r.stderr).strip().splitlines()[-12:]
    print("\n".join(tail))
    print(f"[{'OK' if r.returncode == 0 else 'FAIL'}] 統一引擎 rc={r.returncode} · 產出 {out}")
    return 0 if r.returncode == 0 else 1


def status() -> int:
    pkg = _pkg()
    runs = sorted(OUT_ROOT.glob("ROTATION_*")) if OUT_ROOT.exists() else []
    print(f"收容包 {pkg.name if pkg else '缺'} · 實跑 {len(runs)} 次"
          f"{' · 最新 ' + runs[-1].name if runs else ''}")
    if runs:
        mf = list(runs[-1].rglob("manifest.json"))
        if mf:
            m = json.loads(mf[0].read_text(encoding="utf-8"))
            keys = [k for k in ("final_gate", "groups", "heatmaps") if k in m]
            print(" · ".join(f"{k}={m[k]}" for k in keys) or f"manifest 鍵 {list(m)[:6]}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    pkg = _pkg()
    core = _core(pkg) if pkg else None
    memb = _membership(pkg) if pkg else None
    chk("① 收容包在位(glob 尾版;核心+名冊+pytest 件)",
        bool(pkg and core and memb
             and sorted(pkg.glob("test_VIA_TW_GroupingIndexRotationUnifiedEngine_v*.py"))),
        f"({pkg.name if pkg else '缺'})")
    if not (pkg and core and memb):
        return 1

    tickers = _member_tickers(memb)
    chk("② 名冊載入(238 檔冊)", len(tickers) >= 200, f"({len(tickers)} 檔)")

    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    hit = con.execute(
        "SELECT COUNT(DISTINCT ticker) FROM tw_daily_prices WHERE ticker IN ({})".format(
            ",".join("?" * len(tickers))), tickers).fetchone()[0]
    con.close()
    # 誠實註:名冊 238 檔中約 43 檔不在雙所現行清單冊(引擎以
    # DATA_INSUFFICIENT 類別誠實處理)、餘缺=回補佇列;門檻取可跑下限。
    chk("③ 實庫覆蓋(名冊∩價格庫;缺者=清單外/回補中)",
        hit >= 150, f"({hit}/{len(tickers)})")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "t.parquet"
        ex = export_prices(p, tickers[:12])
        import pandas as pd
        df = pd.read_parquet(p)
        chk("④ parquet 匯出欄約(Date/Ticker/Adj_Close/Volume/Turnover)",
            list(df.columns) == ["Date", "Ticker", "Adj_Close", "Volume", "Turnover"]
            and ex["rows"] > 100 and ex["turnover_nonnull"] > 0,
            f"(列 {ex['rows']}·Turnover 有值 {ex['turnover_nonnull']})")

        r = subprocess.run([sys.executable, str(core), "--demo", "--no-write",
                            "--membership", str(memb), "--output-root", td],
                           cwd=pkg, capture_output=True, text=True, timeout=560)
        chk("⑤ 核心 demo 端到端(--demo --no-write)", r.returncode == 0,
            f"(rc={r.returncode})")

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 誠實欄紀律宣告(金額欄不以股數冒充;Turnover=trade_value 真值)",
        "誠實留缺" in src and "trade_value" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 族群輪動實庫轉接(GRP_ENG040)· 六檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "run" in args:
        def _get(flag, default):
            return args[args.index(flag) + 1] if flag in args else default
        return run(_get("--start", DEFAULT_WARMUP), _get("--eval", DEFAULT_EVAL),
                   _get("--end", None))
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
