# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_SectorFlow_SignalTradeBacktest_v0100.py

族群資金流訊號 → 交易層回測(布局/進場/退場 → 勝率/賺賠比/期望值)。

在 VIA_SectorFlow_AdaptiveChainedIndex_v0100 之上加上交易模擬層:

1. 訊號執行:DYNAMIC_SETUP 建 25% 底倉、DYNAMIC_BUY 補滿倉、DYNAMIC_EXIT 平倉;
   全部 T+1 執行(t 日收盤決策、t+1 日報酬生效),結構性杜絕同日前視。
2. 動態風控:族群指數 ATR(14) 移動停利與硬止損;宏觀曝險乘數縮放倉位。
3. 成本模型:台股手續費 0.1425%(買/賣)+ 證交稅 0.3%(賣)+ 滑價,
   依 |Δ倉位| 計費(結構性成本參數,非市場判定紅線)。
4. 統計對照:circular-shift 訊號置換 null(保留訊號頻率與自相關)
   + Buy-and-Hold 全族群等權基準。
5. Gate:ROTATION/STEALTH 期望值須優於 null 中位數;MARKET_TIDE 最大回撤
   須不劣於 Buy-and-Hold(宏觀熔斷保護);DRAIN 總報酬須優於 Buy-and-Hold。

治理不變項:controlled DGP 只驗證方法邏輯,不代表實盤績效;
append-only 輸出、零網路、零下單、零來源改寫。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
import argparse
import datetime as dt
import importlib.util
import json
import shutil
import sys
import warnings

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# =============================================================================
# def 00 PARAMETERS
# =============================================================================

ENGINE_NAME = "VIA_SectorFlow_SignalTradeBacktest"
VERSION = "0.1.00"

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_ENGINE_PATH = SCRIPT_DIR / "VIA_SectorFlow_AdaptiveChainedIndex_v0100.py"
MODULE_DIR = SCRIPT_DIR.parent
DEFAULT_OUT_DIR = MODULE_DIR / "evidence"
DEFAULT_RUN_TAG = "RUN_SECTORFLOW_TRADE_V0100"

# 交易結構參數(成本/資源,非市場判定紅線)。
FEE_RATE = 0.001425            # 台股單邊手續費
TAX_RATE = 0.003               # 證交稅(賣出)
SLIPPAGE_RATE = 0.0005         # 基礎滑價
SETUP_FRACTION = 0.25          # 布局底倉
FULL_FRACTION = 1.0            # 滿倉
ATR_WINDOW = 14
ATR_TRAIL_MULT = 1.5           # 移動停利 ATR 倍數
ATR_HARD_MULT = 1.5            # 硬止損 ATR 倍數
NULL_SHIFTS = 20               # circular-shift 置換次數
SIGNAL_CONFIRM_DAYS = 2        # BUY 進場確認:多頭訊號須連續 N 日(打掉單日假點火)
SETUP_CONFIRM_DAYS = 4         # SETUP 底倉確認:偷買訊號須更長持續性(真實鎖碼視窗 20-50 日)
REENTRY_COOLDOWN_DAYS = 3      # 出場後冷卻 N 日再准進場(防 whipsaw churn)
PLOT_DPI = 140


def def_load_base_engine():
    spec = importlib.util.spec_from_file_location("via_sectorflow_base_v0100", BASE_ENGINE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# =============================================================================
# def 01 TRADE SIMULATION CORE
# =============================================================================


def def_prepare_trade_panel(base, result: Dict[str, Any]) -> pd.DataFrame:
    """對齊族群鏈接指數報酬與訊號/宏觀乘數,建立交易模擬輸入面板。"""
    chained = result["chained"][["Group", "Date", "BasketRet", "ChainedIndex"]]
    flows = result["flows"][[
        "Group", "Date", "StrategySignal", "MigrationState", "ExposureMultiplier",
    ]]
    panel = chained.merge(flows, on=["Group", "Date"], how="left")
    panel["StrategySignal"] = panel["StrategySignal"].fillna("HOLD")
    panel["ExposureMultiplier"] = panel["ExposureMultiplier"].fillna(0.5)
    panel = panel.sort_values(["Group", "Date"], ignore_index=True)
    # 族群指數 ATR(14):以指數日報酬絕對值的滾動均值近似(百分比 ATR)。
    panel["AtrPct"] = panel.groupby("Group")["BasketRet"].transform(
        lambda s: s.abs().rolling(ATR_WINDOW, min_periods=5).mean()
    )
    return panel


def def_simulate_group_trades(g: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """單一族群狀態機模擬。t 日收盤訊號 → t+1 日起持有(T+1,無同日前視)。"""
    g = g.sort_values("Date").reset_index(drop=True)
    n = len(g)
    target = np.zeros(n, dtype=float)          # t 日收盤決定的目標倉位
    position = 0.0
    entry_level = np.nan
    peak_level = np.nan
    trades: List[Dict[str, Any]] = []
    entry_date = None
    entry_index_level = np.nan

    levels = g["ChainedIndex"].to_numpy(dtype=float)
    signals = g["StrategySignal"].to_numpy()
    states = g["MigrationState"].to_numpy() if "MigrationState" in g.columns else np.array([""] * n)
    mults = g["ExposureMultiplier"].to_numpy(dtype=float)
    atrs = g["AtrPct"].to_numpy(dtype=float)
    dates = g["Date"].to_numpy()
    bull_streak = 0      # 多頭訊號連續日數(進場確認濾網)
    cooldown = 0         # 出場後冷卻(防 whipsaw)

    for t in range(n):
        level = levels[t]
        atr = atrs[t] if np.isfinite(atrs[t]) else 0.0
        bull_streak = bull_streak + 1 if signals[t] in ("DYNAMIC_BUY", "DYNAMIC_SETUP") else 0
        if cooldown > 0:
            cooldown -= 1
        # 停損/停利檢查(以 t 日收盤價評估,t+1 生效)。
        stop_hit = False
        if position > 0 and np.isfinite(entry_level):
            peak_level = max(peak_level, level)
            # 等風險停損:部位低於半倉(SETUP 底倉)時停損帶放寬一倍
            # (0.25 倉 × 3.0 ATR 之美元風險 < 1.0 倉 × 1.5 ATR,風險不升反降)。
            widen = 2.0 if position < 0.5 * FULL_FRACTION else 1.0
            trail = peak_level * (1.0 - ATR_TRAIL_MULT * widen * atr)
            hard = entry_level * (1.0 - ATR_HARD_MULT * widen * atr)
            stop_hit = level <= max(trail, hard)

        sig = signals[t]
        new_position = position
        if sig == "DYNAMIC_EXIT" or stop_hit or mults[t] <= 0.0:
            # EXIT 訊號僅由宏觀熔斷或 OUTFLOW_DRAINING 觸發(引擎端已無
            # 噪音型 EXIT),故此處一律平倉;停損另行生效。
            new_position = 0.0
        elif sig == "DYNAMIC_BUY":
            new_position = FULL_FRACTION * mults[t]
        elif sig == "DYNAMIC_SETUP":
            new_position = max(position, SETUP_FRACTION * mults[t])
        else:
            # HOLD:維持倉位但依宏觀乘數封頂。
            new_position = min(position, FULL_FRACTION * mults[t]) if position > 0 else 0.0

        # 進場確認閘門:自空手建倉須通過連續訊號確認且不在冷卻期;
        # SETUP(僅偷買證據)須比 BUY(吸金+爆量雙證據)更長的持續性確認。
        if position <= 0 and new_position > 0:
            need = SIGNAL_CONFIRM_DAYS if sig == "DYNAMIC_BUY" else SETUP_CONFIRM_DAYS
            if bull_streak < need or cooldown > 0:
                new_position = 0.0
        if position <= 0 and new_position > 0:
            entry_level = level
            peak_level = level
            entry_date = dates[t]
            entry_index_level = level
        if position > 0 and new_position <= 0 and np.isfinite(entry_index_level) and entry_index_level > 0:
            cooldown = REENTRY_COOLDOWN_DAYS
            trades.append({
                "Group": g["Group"].iloc[0],
                "EntryDate": entry_date,
                "ExitDate": dates[t],
                "GrossReturn": level / entry_index_level - 1.0,
                "ExitReason": "STOP" if stop_hit else ("MACRO_HALT" if mults[t] <= 0.0 else "SIGNAL_EXIT"),
            })
            entry_level = np.nan
            peak_level = np.nan
            entry_index_level = np.nan
        position = new_position
        target[t] = position

    g["TargetPosition"] = target
    # T+1 生效:持倉報酬使用前一日目標倉位。
    g["EffectivePosition"] = g["TargetPosition"].shift(1).fillna(0.0)
    g["PositionChange"] = g["TargetPosition"].diff().fillna(g["TargetPosition"]).abs()
    buy_change = g["TargetPosition"].diff().fillna(g["TargetPosition"]).clip(lower=0.0)
    sell_change = (-g["TargetPosition"].diff().fillna(0.0)).clip(lower=0.0)
    g["CostDrag"] = (
        buy_change * (FEE_RATE + SLIPPAGE_RATE)
        + sell_change * (FEE_RATE + TAX_RATE + SLIPPAGE_RATE)
    )
    g["GrossPnlRet"] = g["EffectivePosition"] * g["BasketRet"]
    g["NetPnlRet"] = g["GrossPnlRet"] - g["CostDrag"]
    return g, trades


def def_run_trade_simulation(panel: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    parts: List[pd.DataFrame] = []
    all_trades: List[Dict[str, Any]] = []
    for _, g in panel.groupby("Group", sort=False):
        sim, trades = def_simulate_group_trades(g.copy())
        parts.append(sim)
        all_trades.extend(trades)
    sim_panel = pd.concat(parts, ignore_index=True)
    trade_ledger = pd.DataFrame(all_trades)
    if not trade_ledger.empty:
        # 每筆交易的淨報酬 = 毛報酬 - 進出成本近似(單次來回)。
        round_trip_cost = 2.0 * FEE_RATE + TAX_RATE + 2.0 * SLIPPAGE_RATE
        trade_ledger["NetReturn"] = trade_ledger["GrossReturn"] - round_trip_cost
    return sim_panel, trade_ledger


def def_portfolio_equity(sim_panel: pd.DataFrame) -> pd.DataFrame:
    daily = sim_panel.groupby("Date", as_index=False).agg(
        PortfolioRet=("NetPnlRet", "mean"),
        GrossRet=("GrossPnlRet", "mean"),
        AvgExposure=("EffectivePosition", "mean"),
    ).sort_values("Date", ignore_index=True)
    daily["Equity"] = (1.0 + daily["PortfolioRet"]).cumprod()
    daily["GrossEquity"] = (1.0 + daily["GrossRet"]).cumprod()
    return daily


def def_max_drawdown(equity: np.ndarray) -> float:
    if len(equity) == 0:
        return 0.0
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1.0
    return float(dd.min())


def def_trade_stats(trade_ledger: pd.DataFrame, equity: pd.DataFrame) -> Dict[str, float]:
    if trade_ledger.empty:
        return {
            "Trades": 0, "WinRate": np.nan, "AvgWin": np.nan, "AvgLoss": np.nan,
            "ProfitFactor": np.nan, "Expectancy": np.nan,
            "TotalReturn": float(equity["Equity"].iloc[-1] - 1.0) if len(equity) else 0.0,
            "MaxDrawdown": def_max_drawdown(equity["Equity"].to_numpy()) if len(equity) else 0.0,
        }
    rets = trade_ledger["NetReturn"].to_numpy(dtype=float)
    wins = rets[rets > 0]
    losses = rets[rets <= 0]
    win_rate = float(len(wins) / len(rets))
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(abs(losses.mean())) if len(losses) else 0.0
    profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else np.inf
    expectancy = win_rate * avg_win - (1.0 - win_rate) * avg_loss
    return {
        "Trades": int(len(rets)),
        "WinRate": win_rate,
        "AvgWin": avg_win,
        "AvgLoss": avg_loss,
        "ProfitFactor": profit_factor,
        "Expectancy": float(expectancy),
        "TotalReturn": float(equity["Equity"].iloc[-1] - 1.0),
        "MaxDrawdown": def_max_drawdown(equity["Equity"].to_numpy()),
    }


# =============================================================================
# def 02 BASELINES — Buy & Hold 與 circular-shift 訊號 null
# =============================================================================


def def_buy_and_hold_stats(panel: pd.DataFrame) -> Dict[str, float]:
    daily = panel.groupby("Date", as_index=False).agg(Ret=("BasketRet", "mean")).sort_values("Date")
    equity = (1.0 + daily["Ret"]).cumprod().to_numpy()
    return {
        "BHTotalReturn": float(equity[-1] - 1.0),
        "BHMaxDrawdown": def_max_drawdown(equity),
    }


def def_null_expectancies(base, panel: pd.DataFrame, seed: int) -> List[float]:
    """circular-shift 每群訊號與乘數序列(保留頻率/自相關),重演交易模擬。"""
    rng = np.random.default_rng(base.def_stable_seed(f"TRADE_NULL|{seed}"))
    out: List[float] = []
    for k in range(NULL_SHIFTS):
        shifted_parts: List[pd.DataFrame] = []
        for _, g in panel.groupby("Group", sort=False):
            g = g.sort_values("Date").reset_index(drop=True)
            n = len(g)
            if n < 10:
                continue
            shift = int(rng.integers(low=5, high=max(6, n - 5)))
            g2 = g.copy()
            g2["StrategySignal"] = np.roll(g["StrategySignal"].to_numpy(), shift)
            g2["ExposureMultiplier"] = np.roll(g["ExposureMultiplier"].to_numpy(), shift)
            shifted_parts.append(g2)
        if not shifted_parts:
            continue
        shifted = pd.concat(shifted_parts, ignore_index=True)
        sim, trades = def_run_trade_simulation(shifted)
        equity = def_portfolio_equity(sim)
        stats = def_trade_stats(trades, equity)
        if np.isfinite(stats.get("Expectancy", np.nan)):
            out.append(float(stats["Expectancy"]))
    return out


# =============================================================================
# def 03 SCENARIO TRADE BACKTEST
# =============================================================================


def def_run_trade_backtest(base, membership: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    keep: Dict[str, Dict[str, Any]] = {}
    for scenario in base.CONTROLLED_SCENARIOS:
        for seed in base.CONTROLLED_SEEDS:
            result = base.def_analyze_scenario(membership, seed, scenario)
            panel = def_prepare_trade_panel(base, result)
            sim, trades = def_run_trade_simulation(panel)
            equity = def_portfolio_equity(sim)
            stats = def_trade_stats(trades, equity)
            bh = def_buy_and_hold_stats(panel)
            nulls = def_null_expectancies(base, panel, seed) if scenario in {"ROTATION", "STEALTH_ACCUMULATION"} else []
            null_median = float(np.median(nulls)) if nulls else np.nan
            null_beat = float(np.mean(np.asarray(nulls) < stats["Expectancy"])) if nulls else np.nan
            rows.append({
                "Scenario": scenario,
                "Seed": seed,
                **stats,
                **bh,
                "NullMedianExpectancy": null_median,
                "NullBeatFraction": null_beat,
                "GrossMinusNetDrag": float(equity["GrossEquity"].iloc[-1] - equity["Equity"].iloc[-1]) if len(equity) else 0.0,
                "AvgExposure": float(equity["AvgExposure"].mean()) if len(equity) else 0.0,
            })
            if scenario == "ROTATION" and seed == base.CONTROLLED_SEEDS[-1]:
                keep["main"] = {"result": result, "sim": sim, "trades": trades, "equity": equity, "panel": panel}
            if scenario == "MARKET_TIDE" and seed == base.CONTROLLED_SEEDS[-1]:
                keep["tide"] = {"sim": sim, "trades": trades, "equity": equity, "panel": panel}
    return pd.DataFrame(rows), keep


# =============================================================================
# def 04 PLOTS
# =============================================================================


def def_plot_equity_curves(keep: Mapping[str, Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(12, 6))
    for label, color in [("main", "#0ea5e9"), ("tide", "#ef4444")]:
        bundle = keep.get(label)
        if bundle is None:
            continue
        eq = bundle["equity"]
        bh_daily = bundle["panel"].groupby("Date", as_index=False).agg(Ret=("BasketRet", "mean")).sort_values("Date")
        bh_equity = (1.0 + bh_daily["Ret"]).cumprod()
        title = "ROTATION" if label == "main" else "MARKET_TIDE"
        plt.plot(eq["Date"], eq["Equity"], color=color, linewidth=1.8, label=f"{title} strategy (net)")
        plt.plot(bh_daily["Date"], bh_equity, color=color, linewidth=1.0, linestyle="--", alpha=0.6, label=f"{title} buy&hold")
    plt.axhline(1.0, color="grey", linewidth=0.8)
    plt.title("Signal Trade Backtest — Strategy vs Buy & Hold Equity")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=PLOT_DPI)
    plt.close()


def def_plot_trade_distribution(trades: pd.DataFrame, path: Path) -> None:
    if trades.empty:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5))
    plt.hist(trades["NetReturn"] * 100.0, bins=25, color="#10b981", alpha=0.8, edgecolor="#064e3b")
    plt.axvline(0.0, color="#ef4444", linewidth=1.2)
    plt.title("Per-Trade Net Return Distribution (ROTATION main run, %)")
    plt.xlabel("Net return per trade (%)")
    plt.tight_layout()
    plt.savefig(path, dpi=PLOT_DPI)
    plt.close()


# =============================================================================
# def 05 TEST LEDGER + PIPELINE
# =============================================================================


def def_build_test_ledger(base, backtest: pd.DataFrame, keep: Mapping[str, Dict[str, Any]], run_dir: Path) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    def add(tid: str, name: str, ok: bool, severity: str, evidence: str) -> None:
        rows.append({"TestID": tid, "TestName": name, "Status": "PASS" if ok else "FAIL",
                     "Severity": severity, "Evidence": evidence})

    structured = backtest[backtest["Scenario"].isin(["ROTATION", "STEALTH_ACCUMULATION"])]
    add("B01", "結構化情境有實際交易", bool((structured["Trades"] > 0).all()), "HARD",
        structured[["Scenario", "Seed", "Trades"]].to_json(orient="records"))
    traded = backtest[backtest["Trades"] > 0]
    add("B02", "成本模型實際扣抵(毛 > 淨)", bool((traded["GrossMinusNetDrag"] > 0).all()), "HARD",
        traded[["Scenario", "Seed", "GrossMinusNetDrag"]].round(5).to_json(orient="records"))
    null_ok = bool(
        structured["NullMedianExpectancy"].notna().all()
        and (structured["Expectancy"] > structured["NullMedianExpectancy"]).all()
    )
    add("B03", "期望值優於 circular-shift 訊號 null 中位數", null_ok, "HARD",
        structured[["Scenario", "Seed", "Expectancy", "NullMedianExpectancy", "NullBeatFraction"]].round(5).to_json(orient="records"))
    tide = backtest[backtest["Scenario"] == "MARKET_TIDE"]
    tide_ok = bool((tide["MaxDrawdown"] >= tide["BHMaxDrawdown"]).all())
    add("B04", "MARKET_TIDE 策略回撤不劣於 Buy&Hold(宏觀閘門保護)", tide_ok, "HARD",
        tide[["Seed", "MaxDrawdown", "BHMaxDrawdown"]].round(4).to_json(orient="records"))
    drain = backtest[backtest["Scenario"] == "DRAIN"]
    drain_ok = bool((drain["TotalReturn"] > drain["BHTotalReturn"]).all())
    add("B05", "DRAIN 策略總報酬優於 Buy&Hold(失血迴避)", drain_ok, "HARD",
        drain[["Seed", "TotalReturn", "BHTotalReturn"]].round(4).to_json(orient="records"))
    main = keep["main"]
    t_plus_one = bool(
        (main["sim"].groupby("Group")["EffectivePosition"].first().fillna(0.0) == 0.0).all()
    )
    add("B06", "T+1 執行結構(首日持倉必為 0,無同日前視)", t_plus_one, "HARD",
        f"first_day_positions_zero={t_plus_one}")
    exposure_capped = bool((main["sim"]["EffectivePosition"] <= FULL_FRACTION + 1e-9).all())
    add("B07", "倉位不得超過滿倉上限(含宏觀乘數封頂)", exposure_capped, "HARD",
        f"max_position={float(main['sim']['EffectivePosition'].max()):.4f}")
    output_files = ["trade_backtest_summary.csv", "trade_ledger_main.csv", "portfolio_equity_main.csv"]
    output_ok = all((run_dir / f).exists() and (run_dir / f).stat().st_size > 0 for f in output_files)
    add("B08", "核心輸出完整", output_ok, "HARD", f"required={output_files}")

    rotation = backtest[backtest["Scenario"] == "ROTATION"]
    weak_edge = bool((rotation["WinRate"] < 0.5).any())
    rows.append({
        "TestID": "B09", "TestName": "ROTATION 勝率低於五成(保留觀察,靠賺賠比取勝)",
        "Status": "WARN" if weak_edge else "PASS", "Severity": "REVIEW",
        "Evidence": rotation[["Seed", "WinRate", "ProfitFactor"]].round(4).to_json(orient="records"),
    })
    return pd.DataFrame(rows)


def def_run_pipeline(out_dir: Path, run_tag: str) -> Dict[str, Any]:
    base = def_load_base_engine()
    run_dir = out_dir / run_tag
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    phases: List[Dict[str, Any]] = []

    def phase(name: str, status: str, detail: str) -> None:
        phases.append({"Phase": name, "Status": status, "At": dt.datetime.now().isoformat(timespec="seconds"), "Detail": detail})

    membership = base.def_extract_sector_membership(base.DEFAULT_SSOT)
    phase("TEST-1", "PASS", f"membership rows={len(membership)}")

    backtest, keep = def_run_trade_backtest(base, membership)
    phase("BACK-TEST", "PASS" if not backtest.empty else "FAIL", f"runs={len(backtest)}")

    main = keep["main"]
    def_write = base.def_write_csv
    def_write(backtest, run_dir / "trade_backtest_summary.csv")
    def_write(main["trades"], run_dir / "trade_ledger_main.csv")
    def_write(main["equity"], run_dir / "portfolio_equity_main.csv")
    def_write(main["sim"][[
        "Group", "Date", "StrategySignal", "TargetPosition", "EffectivePosition",
        "BasketRet", "GrossPnlRet", "NetPnlRet", "CostDrag",
    ]], run_dir / "position_timeline_main.csv")
    phase("CONSOLIDATE", "PASS", "append-only evidence written")

    plots = [run_dir / "plots" / "equity_curves.png", run_dir / "plots" / "trade_return_distribution.png"]
    def_plot_equity_curves(keep, plots[0])
    def_plot_trade_distribution(main["trades"], plots[1])
    phase("PLOT-RENDER", "PASS", f"plots={sum(1 for p in plots if p.exists())}")

    test_ledger = def_build_test_ledger(base, backtest, keep, run_dir)
    hard = int(((test_ledger["Status"] == "FAIL") & (test_ledger["Severity"] == "HARD")).sum())
    warn = int((test_ledger["Status"] == "WARN").sum())
    phase("TEST-2", "PASS" if hard == 0 else "FAIL", f"hard={hard} warn={warn}")

    status = "TRADE_BACKTEST_PASS_REVIEW_WARNINGS_RETAINED" if hard == 0 and warn else (
        "TRADE_BACKTEST_PASS" if hard == 0 else "TRADE_BACKTEST_BLOCKED"
    )
    phase("FINAL-TEST", "PASS" if hard == 0 else "FAIL", status)

    summary = {
        "Engine": ENGINE_NAME,
        "Version": VERSION,
        "BaseEngine": BASE_ENGINE_PATH.name,
        "GeneratedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "PythonVersion": sys.version.split()[0],
        "Status": status,
        "HardFailures": hard,
        "ReviewWarnings": warn,
        "CostModel": {"FeeRate": FEE_RATE, "TaxRate": TAX_RATE, "SlippageRate": SLIPPAGE_RATE},
        "AccuracyFilters": {"SignalConfirmDays": SIGNAL_CONFIRM_DAYS, "SetupConfirmDays": SETUP_CONFIRM_DAYS, "ReentryCooldownDays": REENTRY_COOLDOWN_DAYS},
        "Execution": "T_PLUS_ONE",
        "NullShifts": NULL_SHIFTS,
        "Policy": "research-only / controlled-DGP / no network / no order execution",
    }
    def_write(test_ledger, run_dir / "trade_test_ledger.csv")
    def_write(pd.DataFrame(phases), run_dir / "trade_phase_ledger.csv")
    base.def_write_json(summary, run_dir / "trade_run_summary.json")

    manifest = {
        str(p.relative_to(run_dir)): base.def_sha256(p)
        for p in sorted(run_dir.rglob("*"))
        if p.is_file() and p.name != "SHA256_MANIFEST.json"
    }
    base.def_write_json(manifest, run_dir / "SHA256_MANIFEST.json")
    manifest_ok = all(base.def_sha256(run_dir / rel) == digest for rel, digest in manifest.items())
    if not manifest_ok:
        raise RuntimeError("SHA256 manifest verification failed")

    return {"run_dir": run_dir, "summary": summary, "test_ledger": test_ledger, "backtest": backtest}


def main(argv: Optional[Sequence[str]] = None) -> int:
    warnings.filterwarnings("error", category=RuntimeWarning)
    warnings.filterwarnings("error", category=FutureWarning)
    parser = argparse.ArgumentParser(description="VIA sector-flow signal trade backtest")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-tag", default=DEFAULT_RUN_TAG)
    ns = parser.parse_args(argv)
    try:
        result = def_run_pipeline(ns.out_dir, ns.run_tag)
        print("=" * 96)
        print(f"{ENGINE_NAME} v{VERSION}")
        print("Status     :", result["summary"]["Status"])
        print("Run Dir    :", result["run_dir"])
        print("Hard Fail  :", result["summary"]["HardFailures"])
        print("Review Warn:", result["summary"]["ReviewWarnings"])
        print("=" * 96)
        print(result["backtest"][[
            "Scenario", "Seed", "Trades", "WinRate", "Expectancy", "TotalReturn",
            "MaxDrawdown", "BHTotalReturn", "BHMaxDrawdown", "NullMedianExpectancy",
        ]].round(4).to_string(index=False))
        return 0 if result["summary"]["HardFailures"] == 0 else 2
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
