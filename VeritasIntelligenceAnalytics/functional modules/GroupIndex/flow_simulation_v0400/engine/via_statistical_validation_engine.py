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

from typing import Any

import numpy as np
import pandas as pd


def def_pca_absorption_rate(
    returns: pd.DataFrame,
    *,
    iterations: int = 120,
) -> dict[str, Any]:
    """M-01 PCA absorption using a deterministic power iteration on the correlation matrix."""
    clean = returns.replace([np.inf, -np.inf], np.nan).dropna(axis=0, how="any")
    if clean.shape[0] < 20 or clean.shape[1] < 2:
        return {"Status": "BLOCKED_INSUFFICIENT_RETURNS", "PCAAbsorption": np.nan, "Observations": len(clean)}
    std = clean.std(ddof=1).replace(0, np.nan)
    standardized = (clean - clean.mean()) / std
    standardized = standardized.dropna(axis=1, how="any")
    if standardized.shape[1] < 2:
        return {"Status": "BLOCKED_ZERO_VARIANCE", "PCAAbsorption": np.nan, "Observations": len(clean)}
    correlation = standardized.corr().to_numpy(dtype=float)
    vector = np.ones(correlation.shape[0], dtype=float)
    vector /= np.linalg.norm(vector)
    for _ in range(iterations):
        next_vector = correlation @ vector
        norm = np.linalg.norm(next_vector)
        if norm <= 1e-15:
            return {"Status": "BLOCKED_DEGENERATE_MATRIX", "PCAAbsorption": np.nan, "Observations": len(clean)}
        vector = next_vector / norm
    leading_eigenvalue = float(vector @ correlation @ vector)
    total = float(np.trace(correlation))
    return {
        "Status": "PASS",
        "PCAAbsorption": leading_eigenvalue / total if total > 0 else np.nan,
        "LeadingEigenvalue": leading_eigenvalue,
        "TotalEigenvalue": total,
        "Iterations": iterations,
        "Observations": int(len(clean)),
        "Constituents": int(standardized.shape[1]),
    }


def _lagged_pair(leader: np.ndarray, follower: np.ndarray, lag: int) -> tuple[np.ndarray, np.ndarray]:
    if lag > 0:
        return leader[:-lag], follower[lag:]
    if lag < 0:
        return leader[-lag:], follower[:lag]
    return leader, follower


def def_ccf_lag_spectrum(
    leader: pd.Series | np.ndarray,
    follower: pd.Series | np.ndarray,
    *,
    max_lag: int = 5,
) -> pd.DataFrame:
    """M-02 corr(leader[t], follower[t+L]) for all L in [-max_lag, max_lag]."""
    aligned = pd.concat(
        [pd.Series(leader).reset_index(drop=True), pd.Series(follower).reset_index(drop=True)],
        axis=1,
    ).dropna()
    left = aligned.iloc[:, 0].to_numpy(dtype=float)
    right = aligned.iloc[:, 1].to_numpy(dtype=float)
    rows: list[dict[str, Any]] = []
    for lag in range(-max_lag, max_lag + 1):
        x, y = _lagged_pair(left, right, lag)
        correlation = np.nan
        if len(x) >= 20 and np.std(x) > 1e-15 and np.std(y) > 1e-15:
            correlation = float(np.corrcoef(x, y)[0, 1])
        rows.append(
            {
                "Lag": lag,
                "Correlation": correlation,
                "Observations": int(len(x)),
                "Confidence95": 1.96 / np.sqrt(len(x)) if len(x) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def def_permutation_max_ccf_test(
    leader: pd.Series | np.ndarray,
    follower: pd.Series | np.ndarray,
    *,
    max_lag: int = 5,
    permutations: int = 200,
    seed: int = 20260818,
) -> dict[str, Any]:
    """M-03 max-over-lags permutation test correcting CCF lag selection."""
    spectrum = def_ccf_lag_spectrum(leader, follower, max_lag=max_lag)
    valid = spectrum.dropna(subset=["Correlation"])
    if valid.empty:
        return {"Status": "BLOCKED_INSUFFICIENT_RETURNS", "PValue": np.nan}
    observed_row = valid.loc[valid["Correlation"].idxmax()]
    observed = float(observed_row["Correlation"])
    follower_array = pd.Series(follower).reset_index(drop=True).to_numpy(dtype=float)
    generator = np.random.default_rng(seed)
    exceedances = 0
    null_maxima: list[float] = []
    for _ in range(permutations):
        permuted = generator.permutation(follower_array)
        null_spectrum = def_ccf_lag_spectrum(leader, permuted, max_lag=max_lag)
        null_max = float(null_spectrum["Correlation"].max(skipna=True))
        null_maxima.append(null_max)
        exceedances += int(null_max >= observed)
    return {
        "Status": "PASS",
        "DetectedLag": int(observed_row["Lag"]),
        "ObservedMaxCorrelation": observed,
        "Confidence95AtPeak": float(observed_row["Confidence95"]),
        "PValue": (exceedances + 1) / (permutations + 1),
        "Permutations": permutations,
        "Seed": seed,
        "NullMaxMean": float(np.mean(null_maxima)),
        "MultipleLagCorrection": "MAX_OVER_LAGS",
    }


def def_validate_leader_follower(
    group_returns: pd.DataFrame,
    leader_column: str,
    follower_column: str,
    *,
    absorption_min: float = 0.40,
    p_value_max: float = 0.05,
    max_lag: int = 5,
    permutations: int = 200,
) -> dict[str, Any]:
    pca = def_pca_absorption_rate(group_returns)
    permutation = def_permutation_max_ccf_test(
        group_returns[leader_column],
        group_returns[follower_column],
        max_lag=max_lag,
        permutations=permutations,
    )
    ccf_significant = (
        permutation.get("Status") == "PASS"
        and permutation["ObservedMaxCorrelation"] > permutation["Confidence95AtPeak"]
        and permutation["PValue"] < p_value_max
    )
    passed = pca.get("Status") == "PASS" and pca["PCAAbsorption"] >= absorption_min and ccf_significant
    return {
        "ValidationStatus": "PASS" if passed else "BLOCKED",
        "PCA": pca,
        "CCFPermutation": permutation,
        "Thresholds": {
            "PCAAbsorptionMin": absorption_min,
            "PermutationPMax": p_value_max,
            "MaxLag": max_lag,
            "Permutations": permutations,
        },
    }
