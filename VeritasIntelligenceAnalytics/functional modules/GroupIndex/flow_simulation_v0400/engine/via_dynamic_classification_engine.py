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

import math
from typing import Any

import numpy as np
import pandas as pd


DATE_COLUMN = "Date"


def def_derive_dynamic_parameters(price: pd.DataFrame) -> dict[str, Any]:
    """Derive all rolling windows from available history; output is auditable."""
    observations = int(price[DATE_COLUMN].nunique())
    short = int(np.clip(round(observations * 0.025), 5, 10))
    medium = int(np.clip(round(observations * 0.09), 15, 30))
    long = int(np.clip(round(observations * 0.27), 45, 90))
    robust = int(np.clip(round(observations * 0.55), 80, 160))
    return {
        "observations": observations,
        "shortWindow": short,
        "mediumWindow": medium,
        "longWindow": long,
        "robustZWindow": robust,
        "minimumObservations": max(12, int(round(long * 0.55))),
        "rebalanceStep": medium,
        "sizeQuantiles": [1 / 3, 2 / 3],
        "styleConfidencePolicy": "CROSS_SECTIONAL_SCORE_GAP_Q40",
        "purityThresholdPolicy": "CROSS_GROUP_Q25",
        "lookaheadPolicy": "LAGGED_OR_ASOF_ONLY",
    }


def def_prepare_main_force(main_force: pd.DataFrame) -> pd.DataFrame:
    required = {DATE_COLUMN, "Ticker", "MainForceNetAmount", "BranchConcentration"}
    missing = sorted(required - set(main_force.columns))
    if missing:
        raise ValueError(f"main_force missing required columns: {missing}")
    frame = main_force.copy()
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    frame["Ticker"] = frame["Ticker"].astype(str).str.strip().str.upper()
    frame["MainForceNetAmount"] = pd.to_numeric(frame["MainForceNetAmount"], errors="coerce")
    frame["BranchConcentration"] = pd.to_numeric(frame["BranchConcentration"], errors="coerce")
    invalid = int(frame[DATE_COLUMN].isna().sum())
    duplicates = int(frame.duplicated([DATE_COLUMN, "Ticker"], keep=False).sum())
    if invalid or duplicates:
        raise ValueError(f"main_force invalid: invalid_dates={invalid}; duplicate Date+Ticker rows={duplicates}")
    return frame.sort_values(["Ticker", DATE_COLUMN]).reset_index(drop=True)


def def_safe_corr(left: pd.Series, right: pd.Series, minimum: int) -> float:
    pair = pd.concat([left, right], axis=1).dropna()
    if len(pair) < minimum:
        return np.nan
    if pair.iloc[:, 0].std(ddof=0) <= 1e-12 or pair.iloc[:, 1].std(ddof=0) <= 1e-12:
        return np.nan
    return float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))


def def_last_robust_z(values: pd.Series, minimum: int) -> float:
    clean = values.dropna().to_numpy(dtype=float)
    if clean.size < minimum:
        return np.nan
    median = float(np.median(clean))
    mad = float(np.median(np.abs(clean - median)))
    scale = 1.4826 * mad
    if scale <= 1e-12 or not math.isfinite(scale):
        return 0.0
    return float((clean[-1] - median) / scale)


def def_group_validation(
    membership: pd.DataFrame,
    price: pd.DataFrame,
    parameters: dict[str, Any],
) -> pd.DataFrame:
    latest_date = price[DATE_COLUMN].max()
    long_window = int(parameters["longWindow"])
    rows: list[dict[str, Any]] = []
    for group_id, members in membership.groupby("GroupId", sort=True):
        tickers = list(dict.fromkeys(members["Ticker"].astype(str)))
        sample = price.loc[price["Ticker"].isin(tickers), [DATE_COLUMN, "Ticker", "Return"]]
        matrix = sample.pivot(index=DATE_COLUMN, columns="Ticker", values="Return").tail(long_window)
        valid_columns = [column for column in matrix if matrix[column].notna().sum() >= parameters["minimumObservations"]]
        matrix = matrix[valid_columns].dropna(how="all") if valid_columns else pd.DataFrame()
        absorption = average_corr = loading_floor = np.nan
        coverage = len(valid_columns) / max(len(tickers), 1)
        if matrix.shape[1] >= 2:
            complete = matrix.fillna(matrix.mean())
            standardized = (complete - complete.mean()) / complete.std(ddof=0).replace(0, np.nan)
            standardized = standardized.dropna(axis=1, how="any")
            if standardized.shape[1] >= 2:
                covariance = np.cov(standardized.to_numpy(dtype=float), rowvar=False)
                eigenvalues, eigenvectors = np.linalg.eigh(covariance)
                order = np.argsort(eigenvalues)[::-1]
                eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
                absorption = float(max(eigenvalues[0], 0.0) / max(eigenvalues.clip(min=0).sum(), 1e-12))
                # PC sign is arbitrary; absolute loading is the invariant evidence.
                loading_floor = float(np.min(np.abs(eigenvectors[:, 0])))
                corr = standardized.corr().to_numpy(dtype=float)
                average_corr = float(corr[np.triu_indices_from(corr, k=1)].mean())
        rows.append(
            {
                "GroupId": group_id,
                "GroupName": str(members["GroupName"].iloc[0]),
                "AsOfDate": latest_date,
                "CandidateMembers": len(tickers),
                "ValidatedMembers": len(valid_columns),
                "Coverage": coverage,
                "PCAAbsorption": absorption,
                "AbsoluteLoadingFloor": loading_floor,
                "AverageCorrelation": average_corr,
            }
        )
    result = pd.DataFrame(rows)
    for column in ["PCAAbsorption", "AbsoluteLoadingFloor", "AverageCorrelation", "Coverage"]:
        threshold = float(result[column].dropna().quantile(0.25)) if result[column].notna().any() else np.nan
        result[f"DynamicThreshold_{column}"] = threshold
    result["ValidationStatus"] = np.where(
        result[["PCAAbsorption", "AverageCorrelation"]].isna().any(axis=1),
        "REVIEW_INSUFFICIENT_EVIDENCE",
        np.where(
            (result["PCAAbsorption"] >= result["DynamicThreshold_PCAAbsorption"])
            & (result["AverageCorrelation"] >= result["DynamicThreshold_AverageCorrelation"])
            & (result["Coverage"] >= result["DynamicThreshold_Coverage"]),
            "PASS_DYNAMIC_PURITY_GATE",
            "REVIEW_LOW_RELATIVE_PURITY",
        ),
    )
    return result


def def_compute_dynamic_classification(
    membership: pd.DataFrame,
    price: pd.DataFrame,
    institutional: pd.DataFrame,
    main_force: pd.DataFrame,
    roles: pd.DataFrame,
    parameters: dict[str, Any],
    ledger: list[dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    long_window = int(parameters["longWindow"])
    minimum = int(parameters["minimumObservations"])
    latest_date = price[DATE_COLUMN].max()
    price_latest = price.loc[price[DATE_COLUMN] == latest_date, ["Ticker", "LaggedMarketCap"]].copy()
    cap = price_latest["LaggedMarketCap"]
    q1, q2 = (float(cap.quantile(q)) for q in parameters["sizeQuantiles"])
    price_latest["SizeTier"] = np.select(
        [price_latest["LaggedMarketCap"] >= q2, price_latest["LaggedMarketCap"] >= q1],
        ["LARGE_CAP", "MID_CAP"],
        default="SMALL_CAP",
    )
    price_latest.loc[price_latest["LaggedMarketCap"].isna(), "SizeTier"] = "UNRESOLVED"

    panel = price[[DATE_COLUMN, "Ticker", "Return", "TurnoverValue", "DayTradeTurnover"]].copy()
    panel["RealTurnover"] = (panel["TurnoverValue"] - panel["DayTradeTurnover"]).where(
        panel["TurnoverValue"].notna() & panel["DayTradeTurnover"].notna()
    )
    panel = panel.merge(
        institutional[[DATE_COLUMN, "Ticker", "ForeignNetAmount", "InvestmentTrustNetAmount"]],
        on=[DATE_COLUMN, "Ticker"],
        how="left",
    ).merge(
        main_force[[DATE_COLUMN, "Ticker", "MainForceNetAmount", "BranchConcentration"]],
        on=[DATE_COLUMN, "Ticker"],
        how="left",
    )
    panel["FOREIGN"] = panel["ForeignNetAmount"] / panel["RealTurnover"].replace(0, np.nan)
    panel["DOMESTIC_INSTITUTION"] = panel["InvestmentTrustNetAmount"] / panel["RealTurnover"].replace(0, np.nan)
    panel["MAIN_FORCE"] = panel["MainForceNetAmount"] / panel["RealTurnover"].replace(0, np.nan)
    style_rows: list[dict[str, Any]] = []
    for ticker, history in panel.groupby("Ticker", sort=True):
        history = history.sort_values(DATE_COLUMN).tail(long_window)
        scores: dict[str, float] = {}
        evidence: dict[str, dict[str, float]] = {}
        for style in ["FOREIGN", "DOMESTIC_INSTITUTION", "MAIN_FORCE"]:
            values = history[style]
            observations = int(values.notna().sum())
            z_score = def_last_robust_z(values, minimum)
            correlation = def_safe_corr(values, history["Return"], minimum)
            pair = pd.concat([values, history["Return"]], axis=1).dropna()
            consistency = float((np.sign(pair.iloc[:, 0]) == np.sign(pair.iloc[:, 1])).mean()) if len(pair) >= minimum else np.nan
            level = float(values.abs().median()) if observations >= minimum else np.nan
            score = (
                0.38 * min(abs(z_score), 4.0) / 4.0
                + 0.34 * abs(correlation)
                + 0.18 * consistency
                + 0.10 * min(level * 25.0, 1.0)
                if all(np.isfinite([z_score, correlation, consistency, level]))
                else np.nan
            )
            if style == "MAIN_FORCE" and np.isfinite(score):
                branch = float(history["BranchConcentration"].dropna().tail(max(3, parameters["shortWindow"])).median())
                score = 0.82 * score + 0.18 * min(max(branch, 0.0), 1.0)
            scores[style] = score
            evidence[style] = {"z": z_score, "corr": correlation, "consistency": consistency}
        finite = sorted(((style, value) for style, value in scores.items() if np.isfinite(value)), key=lambda x: x[1], reverse=True)
        top_style = finite[0][0] if finite else "UNRESOLVED"
        gap = finite[0][1] - finite[1][1] if len(finite) > 1 else np.nan
        style_rows.append(
            {
                "Ticker": ticker,
                "CapitalControlStyleRaw": top_style,
                "CapitalControlTopScore": finite[0][1] if finite else np.nan,
                "CapitalControlGap": gap,
                "ForeignControlScore": scores["FOREIGN"],
                "DomesticInstitutionControlScore": scores["DOMESTIC_INSTITUTION"],
                "MainForceControlScore": scores["MAIN_FORCE"],
                "CapitalStyleEvidence": evidence,
            }
        )
    style = pd.DataFrame(style_rows)
    gap_threshold = float(style["CapitalControlGap"].dropna().quantile(0.40)) if style["CapitalControlGap"].notna().any() else np.nan
    style["CapitalControlStyle"] = np.where(
        style["CapitalControlGap"].notna() & (style["CapitalControlGap"] >= gap_threshold),
        style["CapitalControlStyleRaw"],
        "MIXED_OR_UNRESOLVED",
    )
    style["CapitalControlConfidenceThreshold"] = gap_threshold
    style["CapitalStyleEvidence"] = style["CapitalStyleEvidence"].map(lambda value: str(value))

    enriched = roles.merge(
        membership[["GroupId", "Ticker", "CandidateRole", "MarketVerified", "MarketSource"]],
        on=["GroupId", "Ticker"],
        how="left",
        validate="one_to_one",
    ).merge(price_latest, on="Ticker", how="left").merge(style, on="Ticker", how="left")
    enriched["ManualReviewEligible"] = enriched["ClassificationRoleCode"].eq("C_LAGGARD_EXCEPTION")
    enriched["CanonicalDecision"] = "NO_MUTATION_PENDING_HUMAN_REVIEW"
    enriched["ReviewAction"] = np.where(enriched["ManualReviewEligible"], "X_EXCLUDE_PROPOSAL_OR_KEEP", "NOT_APPLICABLE")
    group_validation = def_group_validation(membership, price, parameters)

    ledger.append(
        {
            "CheckId": "CLASS001",
            "Check": "Dynamic size and capital-control classification",
            "Status": "PASS",
            "Severity": "REVIEW",
            "FindingCount": int(enriched["CapitalControlStyle"].eq("MIXED_OR_UNRESOLVED").sum()),
            "Detail": f"size uses lagged market cap q33/q67; style gap threshold={gap_threshold:.6f}; no dealer-to-main-force proxy",
        }
    )
    ledger.append(
        {
            "CheckId": "CLASS002",
            "Check": "Human X review is proposal-only",
            "Status": "PASS",
            "Severity": "HARD",
            "FindingCount": 0,
            "Detail": "C rows are review-eligible; canonical membership is never deleted or mutated by the engine/UI.",
        }
    )
    return enriched, group_validation
