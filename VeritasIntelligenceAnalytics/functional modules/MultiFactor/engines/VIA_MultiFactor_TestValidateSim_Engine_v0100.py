#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA MultiFactor Test / Validate / Simulate Engine v0.1.00
- Legal/provenance-aware, append-only output engine.
- No network access, no destructive file operations, no canonical mutation.
- Demo mode generates deterministic synthetic market data to prove the full pipeline.

Outputs:
  factor_relation_ledger.csv
  anti_validation_ledger.csv
  resonance_matrix.csv
  hidden_factor_ledger.csv
  simulation_ledger.csv
  model_permission_ledger.csv
  engine_summary.json
  index.html
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

ENGINE_NAME = "VIA_MultiFactor_TestValidateSim_Engine"
ENGINE_VERSION = "v0.1.00"
DEFAULT_SEED = 260807

NON_NUMERIC_COLUMNS = {"date", "event_id", "event_name", "regime", "source_url"}
TARGET_DEFAULT = "TARGET_RISK_ASSET"
CORE_CONTROLS = ["DXY", "REAL_YIELD", "VIX"]


@dataclass
class GovernancePolicy:
    append_only: bool = True
    no_canonical_mutation: bool = True
    projection_cannot_be_confirmed: bool = True
    provenance_required: bool = True
    correlation_is_not_causality: bool = True
    anti_validation_required_for_supported: bool = True
    legal_data_only: bool = True
    source_ssot_path: str = ""
    source_ssot_kind: str = "unknown"
    source_ssot_version_date: str = "unknown"


@dataclass
class FactorResult:
    factor_id: str
    target_id: str
    n_obs: int
    best_window: int
    best_lag_days: int
    relation_direction: str
    pearson_corr: float
    pearson_p_value: float
    spearman_corr: float
    direction_hit_rate: float
    beta: float
    effect_size: float
    r2_single: float
    incremental_r2_vs_controls: float
    oos_direction_hit_rate: float
    oos_binom_p_value: float
    relation_label: str
    significance_label: str
    lead_label: str
    impact_label: str
    causal_role: str
    causal_status: str
    evidence_status: str
    model_permission: str
    notes: str


@dataclass
class AntiValidationResult:
    factor_id: str
    placebo_factor_p95_abs_corr: float
    observed_abs_corr: float
    placebo_factor_result: str
    lag_inversion_factor_lead_score: float
    lag_inversion_target_lead_score: float
    lag_inversion_result: str
    control_incremental_r2: float
    control_null_p95_incremental_r2: float
    control_result: str
    window_stability_sign_agreement: float
    window_stability_result: str
    oos_result: str
    anti_validation_result: str
    anti_fail_count: int
    anti_warning_count: int


@dataclass
class SimulationRow:
    scenario_id: str
    target_id: str
    method: str
    predicted_return_mean: float
    predicted_return_p05: float
    predicted_return_p95: float
    shock_summary: str
    evidence_status: str
    note: str


# ---------- basic utilities ----------

def html_escape(x: object) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def ensure_append_only_run_dir(out_base: Path, run_id: Optional[str] = None) -> Path:
    out_base.mkdir(parents=True, exist_ok=True)
    if run_id is None:
        run_id = datetime.now().strftime("RUN_%Y%m%d_%H%M%S_VIA_MF_TEST_VALIDATE_SIM_v0100")
    run_dir = out_base / run_id
    suffix = 1
    original = run_dir
    while run_dir.exists():
        run_dir = Path(f"{original}_{suffix:02d}")
        suffix += 1
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def load_governance_policy(ssot_path: Optional[Path]) -> GovernancePolicy:
    policy = GovernancePolicy()
    if ssot_path and ssot_path.exists():
        try:
            data = json.loads(ssot_path.read_text(encoding="utf-8"))
            raw_policy = data.get("policy", []) or []
            policy.source_ssot_path = str(ssot_path)
            policy.source_ssot_kind = data.get("ssot_kind", "unknown")
            policy.source_ssot_version_date = data.get("version_date", "unknown")
            # Map known SSOT terms into executable governance flags.
            policy.append_only = any("只增不減" in str(x) for x in raw_policy) or True
            policy.projection_cannot_be_confirmed = any("投影不得 Confirmed" in str(x) for x in raw_policy) or True
            policy.provenance_required = any("provenance" in str(x).lower() for x in raw_policy) or True
        except Exception:
            # Fail closed on provenance; keep strict defaults.
            policy.source_ssot_path = str(ssot_path)
            policy.source_ssot_kind = "load_error_strict_defaults"
    return policy


def safe_float(x: object, default: float = 0.0) -> float:
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def ols_r2_beta(y: np.ndarray, x: np.ndarray) -> Tuple[float, float, np.ndarray]:
    """Return beta for last column, R2, residuals. X should not include intercept."""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    valid = np.isfinite(y) & np.all(np.isfinite(x), axis=1)
    y = y[valid]
    x = x[valid]
    if len(y) < max(12, x.shape[1] + 3):
        return 0.0, 0.0, np.array([])
    X = np.column_stack([np.ones(len(y)), x])
    try:
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        pred = X @ coef
        ss_res = float(np.sum((y - pred) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 0.0 if ss_tot <= 0 else max(0.0, min(1.0, 1.0 - ss_res / ss_tot))
        beta_last = float(coef[-1])
        return beta_last, r2, y - pred
    except Exception:
        return 0.0, 0.0, np.array([])


# ---------- data ----------

def generate_demo_panel(n: int = 760, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Deterministic synthetic data with known lead-lag and resonance structure."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)

    def ar1(phi: float, sigma: float) -> np.ndarray:
        e = rng.normal(0.0, sigma, n)
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = phi * x[i - 1] + e[i]
        return x

    dxy = ar1(0.18, 0.006)
    real_yield = ar1(0.25, 0.0045)
    us2y = 0.55 * real_yield + ar1(0.20, 0.0035)
    vix = ar1(0.30, 0.012)
    hyg = -0.45 * vix - 0.20 * dxy + ar1(0.12, 0.005)
    oil = ar1(0.12, 0.011)
    gold = -0.35 * real_yield - 0.22 * dxy + 0.14 * vix + ar1(0.10, 0.007)
    etf_flow = -0.35 * dxy - 0.25 * vix + ar1(0.18, 0.009)
    copper = -0.28 * dxy + 0.20 * oil + ar1(0.12, 0.008)

    noise = rng.normal(0.0, 0.010, n)
    target = np.zeros(n)
    # target is intentionally driven by factor lags and coincident stress.
    for i in range(3, n):
        target[i] = (
            -0.52 * real_yield[i - 2]
            -0.40 * dxy[i - 1]
            -0.35 * vix[i]
            +0.32 * hyg[i]
            +0.26 * etf_flow[i - 1]
            +0.10 * copper[i]
            +noise[i]
        )

    safe_asset = 0.20 * vix - 0.15 * dxy - 0.45 * real_yield + rng.normal(0, 0.007, n)
    tw_proxy = 0.65 * target + 0.15 * copper - 0.20 * dxy + rng.normal(0, 0.006, n)

    df = pd.DataFrame({
        "date": dates,
        "DXY": dxy,
        "US2Y": us2y,
        "REAL_YIELD": real_yield,
        "VIX": vix,
        "HYG": hyg,
        "OIL": oil,
        "GOLD": gold,
        "COPPER": copper,
        "ETF_FLOW_EEM": etf_flow,
        TARGET_DEFAULT: target,
        "TARGET_SAFE_ASSET": safe_asset,
        "TARGET_TW_PROXY": tw_proxy,
    })

    # Add a synthetic event tag to prove event window handling without external data.
    shock_idx = int(n * 0.72)
    df["event_id"] = ""
    df.loc[df.index[shock_idx - 5: shock_idx + 6], "event_id"] = "DEMO_USD_STRESS_EVENT"
    df.loc[df.index[shock_idx - 5: shock_idx + 6], ["DXY", "REAL_YIELD", "VIX"]] += [0.020, 0.015, 0.035]
    df.loc[df.index[shock_idx - 3: shock_idx + 8], TARGET_DEFAULT] -= 0.025
    df.loc[df.index[shock_idx - 3: shock_idx + 8], "ETF_FLOW_EEM"] -= 0.018
    return df


def load_panel(args: argparse.Namespace) -> Tuple[pd.DataFrame, str]:
    if args.input_panel:
        p = Path(args.input_panel)
        if not p.exists():
            raise FileNotFoundError(f"input panel not found: {p}")
        df = pd.read_csv(p)
        source = str(p)
    else:
        df = generate_demo_panel(args.demo_rows, args.seed)
        source = "deterministic_demo_synthetic_panel"
    if args.date_col in df.columns:
        df[args.date_col] = pd.to_datetime(df[args.date_col], errors="coerce")
        df = df.sort_values(args.date_col).reset_index(drop=True)
    return df, source


def numeric_factor_columns(df: pd.DataFrame, target: str) -> List[str]:
    cols = []
    for c in df.columns:
        if c == target or c.lower() in NON_NUMERIC_COLUMNS or c.startswith("TARGET_"):
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(c)
    return cols


def auto_candidate_windows(n: int) -> List[int]:
    # System-generated from sample length and financial trading conventions; not user-weighted.
    candidates = [20, 60, 120, 252]
    valid = [w for w in candidates if n >= max(100, w * 4)]
    return valid or [max(20, min(60, n // 4))]


def align_lagged(factor: pd.Series, target: pd.Series, lag: int) -> Tuple[np.ndarray, np.ndarray]:
    # lag > 0 means factor leads target by lag days: factor(t-lag) -> target(t)
    if lag > 0:
        x = factor.shift(lag)
        y = target
    elif lag < 0:
        x = factor
        y = target.shift(-lag)
    else:
        x = factor
        y = target
    z = pd.concat([x, y], axis=1).dropna()
    if z.shape[1] != 2 or len(z) < 8:
        return np.array([]), np.array([])
    return z.iloc[:, 0].to_numpy(dtype=float), z.iloc[:, 1].to_numpy(dtype=float)


# ---------- tests ----------

def corr_p(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    if len(x) < 8 or np.std(x) == 0 or np.std(y) == 0:
        return 0.0, 1.0
    try:
        r, p = stats.pearsonr(x, y)
        return safe_float(r), safe_float(p, 1.0)
    except Exception:
        return 0.0, 1.0


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 8 or np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    try:
        r, _ = stats.spearmanr(x, y)
        return safe_float(r)
    except Exception:
        return 0.0


def direction_hit(x: np.ndarray, y: np.ndarray, corr_sign: float) -> float:
    if len(x) == 0:
        return 0.0
    sx = np.sign(x * (1 if corr_sign >= 0 else -1))
    sy = np.sign(y)
    valid = (sx != 0) & (sy != 0)
    if valid.sum() == 0:
        return 0.0
    return float((sx[valid] == sy[valid]).mean())


def max_abs_corr_for_lags(factor: pd.Series, target: pd.Series, lags: Iterable[int]) -> Tuple[int, float, float, np.ndarray, np.ndarray]:
    best = (0, 0.0, 1.0, np.array([]), np.array([]))
    for lag in lags:
        x, y = align_lagged(factor, target, lag)
        r, p = corr_p(x, y)
        if abs(r) > abs(best[1]):
            best = (lag, r, p, x, y)
    return best


def placebo_abs_corr_p95(x: np.ndarray, y: np.ndarray, seed: int, n_iter: int = 240) -> float:
    if len(x) < 20:
        return 1.0
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_iter):
        xs = np.array(x, copy=True)
        rng.shuffle(xs)
        r, _ = corr_p(xs, y)
        vals.append(abs(r))
    return float(np.quantile(vals, 0.95))


def control_incremental_r2(df: pd.DataFrame, target: str, factor: str, lag: int, controls: List[str]) -> Tuple[float, float, np.ndarray, np.ndarray, np.ndarray]:
    tmp = pd.DataFrame({"y": df[target]})
    tmp["factor"] = df[factor].shift(lag) if lag > 0 else df[factor]
    for c in controls:
        if c != factor and c in df.columns:
            tmp[c] = df[c].shift(lag) if lag > 0 else df[c]
    tmp = tmp.dropna()
    if len(tmp) < 40:
        return 0.0, 0.0, np.array([]), np.array([]), np.array([])
    y = tmp["y"].to_numpy(dtype=float)
    factor_x = tmp["factor"].to_numpy(dtype=float)
    control_cols = [c for c in tmp.columns if c not in {"y", "factor"}]
    if control_cols:
        X_base = tmp[control_cols].to_numpy(dtype=float)
        _, r2_base, _ = ols_r2_beta(y, X_base)
        X_full = tmp[control_cols + ["factor"]].to_numpy(dtype=float)
        beta_last, r2_full, resid = ols_r2_beta(y, X_full)
    else:
        r2_base = 0.0
        beta_last, r2_full, resid = ols_r2_beta(y, factor_x)
    return max(0.0, r2_full - r2_base), beta_last, y, factor_x, resid


def placebo_incremental_r2_p95(df: pd.DataFrame, target: str, factor: str, lag: int, controls: List[str], seed: int, n_iter: int = 160) -> float:
    inc, beta, y, factor_x, _ = control_incremental_r2(df, target, factor, lag, controls)
    if len(y) < 40:
        return 1.0
    rng = np.random.default_rng(seed)
    vals = []
    tmp_base = pd.DataFrame({"y": y})
    # Rebuild aligned controls based on control function's alignment for easier null test.
    aligned = pd.DataFrame({"y": df[target], "factor": df[factor].shift(lag) if lag > 0 else df[factor]})
    for c in controls:
        if c != factor and c in df.columns:
            aligned[c] = df[c].shift(lag) if lag > 0 else df[c]
    aligned = aligned.dropna()
    control_cols = [c for c in aligned.columns if c not in {"y", "factor"}]
    if len(aligned) < 40:
        return 1.0
    yv = aligned["y"].to_numpy(float)
    if control_cols:
        X_base = aligned[control_cols].to_numpy(float)
        _, r2_base, _ = ols_r2_beta(yv, X_base)
    else:
        r2_base = 0.0
    for _ in range(n_iter):
        shuffled = aligned["factor"].to_numpy(float).copy()
        rng.shuffle(shuffled)
        if control_cols:
            X_full = np.column_stack([aligned[control_cols].to_numpy(float), shuffled])
        else:
            X_full = shuffled.reshape(-1, 1)
        _, r2_full, _ = ols_r2_beta(yv, X_full)
        vals.append(max(0.0, r2_full - r2_base))
    return float(np.quantile(vals, 0.95))


def oos_direction_test(df: pd.DataFrame, target: str, factor: str, lag: int, train_frac: float = 0.70) -> Tuple[float, float]:
    x, y = align_lagged(df[factor], df[target], lag)
    n = len(x)
    if n < 80:
        return 0.0, 1.0
    split = int(n * train_frac)
    beta, _, _ = ols_r2_beta(y[:split], x[:split])
    pred = beta * x[split:]
    valid = np.sign(pred) != 0
    if valid.sum() == 0:
        return 0.0, 1.0
    hit = float((np.sign(pred[valid]) == np.sign(y[split:][valid])).mean())
    try:
        p = stats.binomtest(int(round(hit * valid.sum())), int(valid.sum()), 0.5, alternative="greater").pvalue
    except Exception:
        p = 1.0
    return hit, safe_float(p, 1.0)


def classify_relation(abs_corr: float, p95: float) -> str:
    return "relation_detected" if abs_corr > p95 else "relation_not_detected"


def classify_significance(p_value: float, effect_size: float) -> str:
    if p_value <= 0.01 and effect_size > 0:
        return "high_significance"
    if p_value <= 0.05:
        return "stat_significant"
    if p_value <= 0.10:
        return "weak_significance"
    return "not_significant"


def classify_lead(lag: int, inversion_result: str) -> str:
    if inversion_result == "anti_fail":
        return "lagging_or_feedback_risk"
    if lag > 0:
        return "leading"
    if lag == 0:
        return "coincident"
    return "lagging"


def classify_impact(inc_r2: float, null_p95: float, effect_size: float) -> str:
    if inc_r2 > null_p95 and effect_size > 0:
        return "incremental_impact_detected"
    if effect_size > 0:
        return "impact_possible_not_incremental"
    return "impact_not_detected"


def classify_permission(fr: Dict[str, object], anti: AntiValidationResult) -> Tuple[str, str, str]:
    # Deterministic rule engine; thresholds are anti-validation derived where possible.
    if anti.anti_fail_count >= 2:
        return "reject", "noise", "rejected"
    if fr["relation_label"] == "relation_not_detected":
        return "monitor_only", "noise", "weak"
    if fr["impact_label"] != "incremental_impact_detected":
        return "monitor_only", "confirmation", "plausible"
    if fr["lead_label"] == "leading" and anti.anti_validation_result == "anti_pass" and fr["oos_binom_p_value"] <= 0.10:
        return "allow", "driver", "supported"
    if fr["lead_label"] in {"leading", "coincident"} and anti.anti_validation_result in {"anti_pass", "anti_partial"}:
        return "regime_specific", "amplifier", "plausible"
    return "monitor_only", "confirmation", "plausible"


def evaluate_factor(df: pd.DataFrame, target: str, factor: str, windows: List[int], seed: int) -> Tuple[FactorResult, AntiValidationResult]:
    # Use full sample for now; window selected by highest absolute lead-lag relation within candidate windows.
    best_record = None
    for w in windows:
        sub = df.tail(w * 4 if len(df) >= w * 4 else len(df)) if w < len(df) else df
        lag, r, p, x, y = max_abs_corr_for_lags(sub[factor], sub[target], range(-10, 11))
        if best_record is None or abs(r) > abs(best_record[2]):
            best_record = (w, lag, r, p, x, y, sub)
    assert best_record is not None
    best_window, best_lag, r, p, x, y, sub = best_record

    sp = spearman(x, y)
    dh = direction_hit(x, y, np.sign(r))
    beta, r2, resid = ols_r2_beta(y, x)
    effect = abs(beta) * float(np.nanstd(x))
    p95_corr = placebo_abs_corr_p95(x, y, seed + abs(hash(factor)) % 10000)

    controls = [c for c in CORE_CONTROLS if c in df.columns and c != factor]
    inc_r2, beta_control, _, _, _ = control_incremental_r2(df, target, factor, best_lag, controls)
    null_inc_p95 = placebo_incremental_r2_p95(df, target, factor, best_lag, controls, seed + 7 + abs(hash(factor)) % 10000)

    # lag inversion: compare factor-leading target vs target-leading factor.
    factor_lead_corr = max(abs(max_abs_corr_for_lags(df[factor], df[target], range(1, 11))[1]), abs(r) if best_lag > 0 else 0.0)
    target_lead_corr = abs(max_abs_corr_for_lags(df[factor], df[target], range(-10, 0))[1])
    lag_inv_result = "anti_fail" if target_lead_corr > factor_lead_corr * 1.08 and target_lead_corr > p95_corr else "anti_pass"

    # stability: relation sign across candidate windows using selected lag.
    signs = []
    for w in windows:
        subw = df.tail(w * 4 if len(df) >= w * 4 else len(df))
        xw, yw = align_lagged(subw[factor], subw[target], best_lag)
        rw, _ = corr_p(xw, yw)
        if abs(rw) > 0:
            signs.append(np.sign(rw))
    sign_agree = float(np.mean([s == np.sign(r) for s in signs])) if signs else 0.0
    window_result = "anti_pass" if sign_agree >= 0.67 else "anti_warning"

    oos_hit, oos_p = oos_direction_test(df, target, factor, best_lag)
    placebo_result = "anti_pass" if abs(r) > p95_corr else "anti_fail"
    control_result = "anti_pass" if inc_r2 > null_inc_p95 else "anti_warning"
    oos_result = "anti_pass" if oos_p <= 0.10 else "anti_warning"

    fail_count = sum(1 for z in [placebo_result, lag_inv_result] if z == "anti_fail")
    warn_count = sum(1 for z in [control_result, window_result, oos_result] if z == "anti_warning")
    anti_overall = "anti_fail" if fail_count >= 2 else ("anti_partial" if (fail_count == 1 or warn_count >= 2) else "anti_pass")

    anti = AntiValidationResult(
        factor_id=factor,
        placebo_factor_p95_abs_corr=p95_corr,
        observed_abs_corr=abs(r),
        placebo_factor_result=placebo_result,
        lag_inversion_factor_lead_score=factor_lead_corr,
        lag_inversion_target_lead_score=target_lead_corr,
        lag_inversion_result=lag_inv_result,
        control_incremental_r2=inc_r2,
        control_null_p95_incremental_r2=null_inc_p95,
        control_result=control_result,
        window_stability_sign_agreement=sign_agree,
        window_stability_result=window_result,
        oos_result=oos_result,
        anti_validation_result=anti_overall,
        anti_fail_count=fail_count,
        anti_warning_count=warn_count,
    )

    relation_label = classify_relation(abs(r), p95_corr)
    sig_label = classify_significance(p, effect)
    lead_label = classify_lead(best_lag, lag_inv_result)
    impact_label = classify_impact(inc_r2, null_inc_p95, effect)

    tmp = {
        "relation_label": relation_label,
        "impact_label": impact_label,
        "lead_label": lead_label,
        "oos_binom_p_value": oos_p,
    }
    permission, causal_role, causal_status = classify_permission(tmp, anti)
    evidence_status = "Estimated_Model" if permission != "allow" else "Supported_Model_NotConfirmed"
    notes = "Projection/model result; cannot be Confirmed without external data/provenance and repeated validation."

    fr = FactorResult(
        factor_id=factor,
        target_id=target,
        n_obs=int(len(x)),
        best_window=int(best_window),
        best_lag_days=int(best_lag),
        relation_direction="positive" if r > 0 else "negative" if r < 0 else "neutral",
        pearson_corr=float(r),
        pearson_p_value=float(p),
        spearman_corr=float(sp),
        direction_hit_rate=float(dh),
        beta=float(beta),
        effect_size=float(effect),
        r2_single=float(r2),
        incremental_r2_vs_controls=float(inc_r2),
        oos_direction_hit_rate=float(oos_hit),
        oos_binom_p_value=float(oos_p),
        relation_label=relation_label,
        significance_label=sig_label,
        lead_label=lead_label,
        impact_label=impact_label,
        causal_role=causal_role,
        causal_status=causal_status,
        evidence_status=evidence_status,
        model_permission=permission,
        notes=notes,
    )
    return fr, anti


# ---------- resonance / hidden / simulation ----------

def build_resonance_matrix(df: pd.DataFrame, target: str, factor_results: List[FactorResult]) -> pd.DataFrame:
    factors = [fr.factor_id for fr in factor_results]
    if not factors:
        return pd.DataFrame()
    # Direction to adverse target move: if beta/corr negative, factor positive is adverse; if positive, factor negative is adverse.
    direction_map = {fr.factor_id: (-1 if fr.beta > 0 else 1) for fr in factor_results}
    z = df[factors].copy()
    z = (z - z.rolling(60, min_periods=20).mean()) / z.rolling(60, min_periods=20).std()
    abs_threshold = z.abs().stack().quantile(0.90)  # objective empirical threshold.
    rows = []
    for idx in range(len(df)):
        active = []
        adverse_count = 0
        for f in factors:
            val = safe_float(z.iloc[idx][f], np.nan)
            if np.isfinite(val) and abs(val) >= abs_threshold:
                active.append(f"{f}:{val:.2f}")
                if np.sign(val) == direction_map[f]:
                    adverse_count += 1
        if len(active) >= 2:
            rows.append({
                "date": str(pd.to_datetime(df.iloc[idx].get("date", idx)).date()) if "date" in df.columns else str(idx),
                "target_id": target,
                "active_factor_count": len(active),
                "adverse_factor_count": adverse_count,
                "resonance_level": min(6, max(1, adverse_count)),
                "active_factors": "; ".join(active),
                "threshold_method": "rolling_zscore_abs_empirical_p90",
                "evidence_status": "Estimated_Model_NotConfirmed",
            })
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values(["resonance_level", "active_factor_count"], ascending=False).head(30)
    return out


def hidden_factor_detection(df: pd.DataFrame, target: str, factors: List[str]) -> pd.DataFrame:
    cols = factors + [target]
    X = df[cols].dropna()
    if len(X) < 80 or len(cols) < 3:
        return pd.DataFrame()
    Z = (X - X.mean()) / X.std(ddof=0)
    Z = Z.replace([np.inf, -np.inf], np.nan).dropna()
    if len(Z) < 80:
        return pd.DataFrame()
    pca = PCA(n_components=min(3, len(cols)))
    comps = pca.fit_transform(Z.to_numpy(float))
    rows = []
    for k, ev in enumerate(pca.explained_variance_ratio_, start=1):
        loadings = dict(zip(cols, pca.components_[k - 1]))
        top = sorted(loadings.items(), key=lambda kv: abs(kv[1]), reverse=True)[:6]
        rows.append({
            "hidden_factor_id": f"Hidden_PC{k}",
            "method": "PCA",
            "explained_variance_ratio": float(ev),
            "top_loadings": "; ".join([f"{a}:{b:.3f}" for a, b in top]),
            "hidden_status": "Hidden_Candidate" if ev < 0.35 else "Hidden_Supported_NeedsInterpretation",
            "evidence_status": "Estimated_Model_NotConfirmed",
            "note": "Latent structure only; projection cannot be Confirmed without interpretation and external evidence.",
        })
    return pd.DataFrame(rows)


def build_multifactor_model(df: pd.DataFrame, target: str, allowed_factors: List[str]) -> Tuple[np.ndarray, List[str], np.ndarray]:
    if not allowed_factors:
        allowed_factors = [c for c in CORE_CONTROLS if c in df.columns]
    tmp = df[[target] + allowed_factors].dropna()
    if len(tmp) < 80 or not allowed_factors:
        return np.array([]), [], np.array([])
    y = tmp[target].to_numpy(float)
    X = tmp[allowed_factors].to_numpy(float)
    X1 = np.column_stack([np.ones(len(y)), X])
    coef, *_ = np.linalg.lstsq(X1, y, rcond=None)
    resid = y - X1 @ coef
    return coef, allowed_factors, resid


def simulate_scenarios(df: pd.DataFrame, target: str, factor_results: List[FactorResult], seed: int) -> pd.DataFrame:
    chosen = [fr.factor_id for fr in factor_results if fr.model_permission in {"allow", "regime_specific"}]
    if len(chosen) < 2:
        # fall back to highest relation factors for demo/reporting, still monitor-only if not allowed.
        chosen = [fr.factor_id for fr in sorted(factor_results, key=lambda z: abs(z.pearson_corr), reverse=True)[:4]]
    coef, factors, resid = build_multifactor_model(df, target, chosen)
    if len(coef) == 0:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    abs_q = {f: float(df[f].abs().quantile(0.95)) for f in factors}
    beta_map = dict(zip(factors, coef[1:]))

    scenarios = {}
    scenarios["BASE_ZERO_SHOCK"] = {f: 0.0 for f in factors}
    scenarios["ADVERSE_EMPIRICAL_P95"] = {f: -np.sign(beta_map[f]) * abs_q[f] for f in factors}
    scenarios["RELIEF_EMPIRICAL_P95"] = {f: np.sign(beta_map[f]) * abs_q[f] for f in factors}

    rows = []
    residual_draws = rng.choice(resid, size=(len(scenarios), 1200), replace=True) if len(resid) else np.zeros((len(scenarios), 1200))
    for i, (sid, shock) in enumerate(scenarios.items()):
        x = np.array([shock[f] for f in factors], dtype=float)
        mean = float(coef[0] + np.dot(coef[1:], x))
        sim = mean + residual_draws[i]
        rows.append(SimulationRow(
            scenario_id=sid,
            target_id=target,
            method="ols_multifactor_empirical_p95_shock_with_bootstrap_residual",
            predicted_return_mean=mean,
            predicted_return_p05=float(np.quantile(sim, 0.05)),
            predicted_return_p95=float(np.quantile(sim, 0.95)),
            shock_summary="; ".join([f"{k}={v:.5f}" for k, v in shock.items()]),
            evidence_status="Estimated_Model_NotConfirmed",
            note="Simulation is projection; governance rule forbids Confirmed status.",
        ).__dict__)
    return pd.DataFrame(rows)


def devil_advocate(factors_df: pd.DataFrame, anti_df: pd.DataFrame, resonance_df: pd.DataFrame, hidden_df: pd.DataFrame) -> List[str]:
    bullets = []
    if factors_df.empty:
        return ["No factor result exists; engine cannot support any claim."]
    allow_count = int((factors_df["model_permission"] == "allow").sum())
    reject_count = int((factors_df["model_permission"] == "reject").sum())
    monitor_count = int((factors_df["model_permission"].isin(["monitor_only", "regime_specific"])).sum())
    bullets.append(f"Allowed factors are limited: allow={allow_count}, monitor/regime_specific={monitor_count}, reject={reject_count}. Do not overstate model confidence.")
    if "pearson_p_value" in factors_df.columns:
        weak_sig = int((factors_df["pearson_p_value"] > 0.05).sum())
        if weak_sig:
            bullets.append(f"{weak_sig} factor(s) fail conventional statistical significance; they must remain monitor-only unless later validation improves.")
    if not anti_df.empty:
        failish = anti_df[anti_df["anti_validation_result"].isin(["anti_fail", "anti_partial"])]
        if len(failish):
            bullets.append(f"{len(failish)} factor(s) have failed or partial anti-validation; possible false signal, lag inversion, or weak incremental value remains.")
    if not resonance_df.empty:
        bullets.append("Resonance events are model-estimated by empirical z-score thresholds; they prove stress clustering, not legal/official causality.")
    if not hidden_df.empty:
        bullets.append("Hidden factors are latent statistical structures; they require interpretation before use in decision narratives.")
    bullets.append("ETF/factor simulations are projections; under SSOT policy they cannot be Confirmed and require provenance plus replay validation.")
    bullets.append("High confidence means the engine ran cleanly and produced internally consistent ledgers; it does not mean the market thesis is proven.")
    return bullets


# ---------- reporting ----------

def df_to_html_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df is None or df.empty:
        return "<p class='muted'>No rows.</p>"
    d = df.head(max_rows).copy()
    return d.to_html(index=False, escape=True, border=0, classes="tbl")


def write_html_report(run_dir: Path, summary: Dict[str, object], factor_df: pd.DataFrame, anti_df: pd.DataFrame, res_df: pd.DataFrame, hidden_df: pd.DataFrame, sim_df: pd.DataFrame, critique: List[str]) -> Path:
    css = """
    body{font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;background:#f6f4ef;color:#1f1d1a;margin:0;padding:24px;}
    h1{font-size:24px;margin:0 0 6px;} h2{font-size:18px;border-top:1px solid #d9d3c8;padding-top:18px;margin-top:24px;}
    .card{background:#fff;border:1px solid #ddd6ca;border-radius:14px;padding:18px;margin:12px 0;box-shadow:0 1px 2px rgba(0,0,0,.04)}
    .muted{color:#6b6760}.ok{color:#427a52;font-weight:700}.warn{color:#a66b00;font-weight:700}.fail{color:#a22b2b;font-weight:700}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}.metric{background:#faf9f6;border:1px solid #e4ded5;border-radius:10px;padding:10px}
    .tbl{border-collapse:collapse;width:100%;font-size:12px;background:#fff}.tbl th{background:#24231f;color:#fff;text-align:left}.tbl td,.tbl th{border:1px solid #ddd6ca;padding:6px;vertical-align:top}
    code,pre{background:#f0ede6;border-radius:6px;padding:2px 5px} li{margin:6px 0}
    """
    metrics = "".join([f"<div class='metric'><b>{html_escape(k)}</b><br>{html_escape(v)}</div>" for k, v in summary.items() if k not in {"governance_policy", "devil_advocate"}])
    crit = "".join([f"<li>{html_escape(x)}</li>" for x in critique])
    html_text = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{ENGINE_NAME} Report</title><style>{css}</style></head>
<body><h1>def {ENGINE_NAME} · {ENGINE_VERSION}</h1><p class="muted">Testing · Validating · Simulating · Devil's Advocate</p>
<div class="card"><h2>def Summary</h2><div class="grid">{metrics}</div></div>
<div class="card"><h2>def Devil's Advocate Critique</h2><ul>{crit}</ul></div>
<div class="card"><h2>def Factor Relation Ledger</h2>{df_to_html_table(factor_df)}</div>
<div class="card"><h2>def Anti-Validation Ledger</h2>{df_to_html_table(anti_df)}</div>
<div class="card"><h2>def Resonance Matrix</h2>{df_to_html_table(res_df)}</div>
<div class="card"><h2>def Hidden Factor Ledger</h2>{df_to_html_table(hidden_df)}</div>
<div class="card"><h2>def Simulation Ledger</h2>{df_to_html_table(sim_df)}</div>
</body></html>"""
    out = run_dir / "index.html"
    out.write_text(html_text, encoding="utf-8")
    return out


# ---------- main ----------

def run_engine(args: argparse.Namespace) -> Dict[str, object]:
    run_dir = ensure_append_only_run_dir(Path(args.out_base), args.run_id)
    policy = load_governance_policy(Path(args.ssot) if args.ssot else None)
    df, data_source = load_panel(args)
    target = args.target
    if target not in df.columns:
        raise ValueError(f"target column not found: {target}; available={list(df.columns)}")
    factors = numeric_factor_columns(df, target)
    windows = auto_candidate_windows(len(df))

    factor_results: List[FactorResult] = []
    anti_results: List[AntiValidationResult] = []
    for f in factors:
        fr, anti = evaluate_factor(df, target, f, windows, args.seed)
        factor_results.append(fr)
        anti_results.append(anti)

    factor_df = pd.DataFrame([asdict(x) for x in factor_results]).sort_values(
        ["model_permission", "incremental_r2_vs_controls", "effect_size"], ascending=[True, False, False]
    )
    # Put allow/regime first by custom order.
    perm_order = {"allow": 0, "regime_specific": 1, "monitor_only": 2, "reject": 3}
    factor_df["_perm_order"] = factor_df["model_permission"].map(perm_order).fillna(9)
    factor_df = factor_df.sort_values(["_perm_order", "incremental_r2_vs_controls", "effect_size"], ascending=[True, False, False]).drop(columns=["_perm_order"])

    anti_df = pd.DataFrame([asdict(x) for x in anti_results])
    res_df = build_resonance_matrix(df, target, factor_results)
    hidden_df = hidden_factor_detection(df, target, factors)
    sim_df = simulate_scenarios(df, target, factor_results, args.seed + 99)

    model_permission_df = factor_df[[
        "factor_id", "target_id", "model_permission", "causal_role", "causal_status", "evidence_status",
        "best_lag_days", "incremental_r2_vs_controls", "oos_direction_hit_rate", "notes"
    ]].copy()

    # Write ledgers.
    df.to_csv(run_dir / "aligned_factor_panel.csv", index=False)
    factor_df.to_csv(run_dir / "factor_relation_ledger.csv", index=False)
    anti_df.to_csv(run_dir / "anti_validation_ledger.csv", index=False)
    res_df.to_csv(run_dir / "resonance_matrix.csv", index=False)
    hidden_df.to_csv(run_dir / "hidden_factor_ledger.csv", index=False)
    sim_df.to_csv(run_dir / "simulation_ledger.csv", index=False)
    model_permission_df.to_csv(run_dir / "model_permission_ledger.csv", index=False)

    critique = devil_advocate(factor_df, anti_df, res_df, hidden_df)
    allow_count = int((factor_df["model_permission"] == "allow").sum())
    reject_count = int((factor_df["model_permission"] == "reject").sum())
    partial_count = int((anti_df["anti_validation_result"] == "anti_partial").sum()) if not anti_df.empty else 0
    high_confidence = bool(len(factor_df) >= 3 and len(sim_df) >= 3 and len(hidden_df) >= 1 and not factor_df.isna().any().any())

    summary = {
        "engine_name": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "run_dir": str(run_dir),
        "run_timestamp": datetime.now().isoformat(timespec="seconds"),
        "data_source": data_source,
        "target": target,
        "n_rows": int(len(df)),
        "n_factors": int(len(factors)),
        "candidate_windows_system_generated": windows,
        "allow_count": allow_count,
        "reject_count": reject_count,
        "anti_partial_count": partial_count,
        "high_confidence_engine_execution": high_confidence,
        "governance_policy": asdict(policy),
        "devil_advocate": critique,
        "outputs": {
            "aligned_factor_panel": "aligned_factor_panel.csv",
            "factor_relation_ledger": "factor_relation_ledger.csv",
            "anti_validation_ledger": "anti_validation_ledger.csv",
            "resonance_matrix": "resonance_matrix.csv",
            "hidden_factor_ledger": "hidden_factor_ledger.csv",
            "simulation_ledger": "simulation_ledger.csv",
            "model_permission_ledger": "model_permission_ledger.csv",
            "html_report": "index.html",
        },
    }
    (run_dir / "engine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_html_report(run_dir, summary, factor_df, anti_df, res_df, hidden_df, sim_df, critique)
    return summary


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=f"{ENGINE_NAME} {ENGINE_VERSION}")
    ap.add_argument("--ssot", default="/mnt/data/SSOT_VPT_ingest.json", help="Optional governance SSOT JSON path")
    ap.add_argument("--input-panel", default="", help="Optional CSV panel with date, target, and numeric factor columns")
    ap.add_argument("--target", default=TARGET_DEFAULT, help="Target return column")
    ap.add_argument("--date-col", default="date", help="Date column")
    ap.add_argument("--out-base", default="/mnt/data/VIA_MF_ENGINE_RUNS", help="Append-only output base directory")
    ap.add_argument("--run-id", default=None, help="Optional run id; if exists, suffix is added")
    ap.add_argument("--demo-rows", type=int, default=760, help="Rows for deterministic demo panel")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed")
    return ap.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    summary = run_engine(args)
    print(json.dumps({
        "status": "PASS",
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "run_dir": summary["run_dir"],
        "html_report": str(Path(summary["run_dir"]) / "index.html"),
        "high_confidence_engine_execution": summary["high_confidence_engine_execution"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
