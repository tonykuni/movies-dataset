# -*- coding: utf-8 -*-
"""VIS 自適應完美分類引擎契約測試(受控 DGP;快速面)。"""
from __future__ import annotations

from pathlib import Path
import datetime as dt
import json

import polars as pl

import VIA_VIS_AdaptiveClassification_v0100 as vis

RUN = Path(__file__).resolve().parent.parent / "evidence" / "RUN_VIS_ADAPTIVE_V0100"


def test_run_summary_green_and_governed() -> None:
    s = json.loads((RUN / "vis_run_summary.json").read_text("utf-8"))
    assert s["Status"] == "VIS_ADAPTIVE_PASS"
    assert s["HardFailures"] == 0 and s["Iterations"] <= 3
    assert s["BaseDate"] == "2026-01-02" and s["MaxAttentionWeight"] == 0.18
    assert {t["TestID"] for t in s["Tests"]} == {f"V{i:02d}" for i in range(1, 16)}
    assert "非實盤績效" in s["Boundary"] and "Adj Close" in s["Boundary"]


def test_engine_core_contracts() -> None:
    res = vis.def_run_engine(vis.def_generate_panel(n_days=180))
    df, idx = res["panel"], res["indices"]
    # 巨錨隔離 + AS 自洽
    assert df.filter(pl.col("ticker") == vis.TSMC).height == 0
    ssum = df.group_by("date").agg(pl.col("att_share").sum().alias("s"))
    assert float((ssum["s"] - 1.0).abs().max()) < 1e-6
    # 三指數欄位 + HHI 監控
    for c in ["index_equal", "index_tier", "index_att", "hhi_att", "max_w_att"]:
        assert c in idx.columns, c
    # Attention cap 憲法
    assert float(df["as_cap"].max()) <= vis.MAX_ATT_WEIGHT + 1e-12
    # lag-aware 同動:三個 lag 欄 + lead_lag ∈ {0,1,2}
    assert {"corr_lag0", "corr_lag1", "corr_lag2", "lead_lag"} <= set(df.columns)
    assert set(df["lead_lag"].unique().to_list()) <= {0, 1, 2}
    # 角色與籌碼欄位
    assert set(df["role"].unique().to_list()) <= {"LEADER", "PEER", "LAGGER", "UNRELATED"}
    for c in ["z_foreign", "z_sitc", "z_dealer", "z_margin_buy", "z_margin_short", "daytrade_ratio"]:
        assert c in df.columns, c


def test_t1_weights_no_lookahead() -> None:
    res = vis.def_run_engine(vis.def_generate_panel(n_days=120))
    df = res["panel"].sort(["ticker", "date"])
    chk = (df.with_columns(pl.col("w_att_raw").shift(1).over("ticker").alias("_e"))
             .filter(pl.col("_e").is_not_null()))
    assert float((chk["w_att"] - chk["_e"]).abs().max()) < 1e-12


def test_no_fixed_market_thresholds_in_gates() -> None:
    # 半動態規範:shock 觸發/流動性/同動門檻皆為滾動或橫截面分位
    src = Path(vis.__file__).read_text("utf-8")
    assert "rolling_quantile" in src
    assert "shock_th" in src and "corr_th" in src
    # shock 旗標不得寫死 z>2 之類固定比較(觸發常數只作為 Type-D 預設註記)
    assert 'pl.col("vol_shock") > P["shock_z_trigger"]' not in src
