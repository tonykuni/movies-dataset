"""
vdf_fetchers_derived.py — Derived macro models

Computes 9 derived macro signals defined in the SSOT:
  1. US.Model.FedPolicy.Stance
  2. US.Model.FedPolicy.LiquidityImpulse
  3. US.Model.USDIndex.PolicyDiff
  4. US.Model.USDIndex.YieldDiff2Y
  5. US.Model.USDIndex.RiskFactor
  6. US.Model.USDIndex.Composite
  7. US.Model.YieldCurve.Inversion
  8. US.Model.Fiscal.MonthlyImpulse
  9. US.Model.Sentiment.RiskOnOff

All models take a dict mapping series_id -> {date: value} as input.
Each returns a list of {date, series_id, value, source} records.
"""

from __future__ import annotations
import math
from typing import Any

SOURCE = "Derived"

# DXY weights per USD Index spec
DXY_WEIGHTS = {
    "EUR": 0.576,
    "JPY": 0.136,
    "GBP": 0.119,
    "CAD": 0.091,
    "SEK": 0.042,
    "CHF": 0.036,
}

# Neutral rate estimate for Fed policy stance
R_NEUTRAL = 0.75


# ============================================================
# Helpers
# ============================================================

def _get_series(data: dict[str, dict[str, float]], series_id: str) -> dict[str, float]:
    """Get a series dict, or empty if missing."""
    return data.get(series_id, {})


def _common_dates(*series: dict[str, float]) -> list[str]:
    """Intersection of dates across multiple series, sorted ascending."""
    if not series:
        return []
    s = set(series[0].keys())
    for x in series[1:]:
        s &= set(x.keys())
    return sorted(s)


def _delta(series: dict[str, float], window: int = 1) -> dict[str, float]:
    """Compute series_t - series_{t-window} by date order."""
    dates = sorted(series.keys())
    out: dict[str, float] = {}
    for i in range(window, len(dates)):
        d_now = dates[i]
        d_prev = dates[i - window]
        try:
            out[d_now] = series[d_now] - series[d_prev]
        except (TypeError, KeyError):
            continue
    return out


def _normalize_series(series: dict[str, float]) -> dict[str, float]:
    """Z-score normalize, robust to constant series."""
    vals = [v for v in series.values() if v is not None]
    if not vals:
        return {}
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / max(len(vals), 1)
    std = math.sqrt(var) if var > 0 else 1.0
    return {d: (v - mean) / std for d, v in series.items() if v is not None}


def _emit(out: list, date: str, series_id: str, value: float | None) -> None:
    if value is not None and not math.isnan(value) if isinstance(value, float) else value is not None:
        out.append({"date": date, "series_id": series_id, "value": value, "source": SOURCE})


# ============================================================
# Model 1: Fed Policy Stance
# ============================================================

def compute_fed_policy_stance(data: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """Classify Fed stance:
        Tightening / RestrictiveHold / Neutral / Easing / EmergencyEasing
    Encoded as score: -2, -1, 0, +1, +2 respectively for downstream use.
    """
    ffr_u = _get_series(data, "US.Fed.Rates.FedFundsTarget.Upper")
    pce_y = _get_series(data, "US.Prices.PCE.Core.YoY")
    unemp = _get_series(data, "US.Labor.UnempRate.U3")

    dates = _common_dates(ffr_u, pce_y, unemp)
    out: list[dict[str, Any]] = []
    for d in dates:
        try:
            ffr_gap = ffr_u[d] - R_NEUTRAL
            inflation_gap  = pce_y[d] - 2.0
            unemp_gap      = unemp[d] - 4.0
            # Score: high FFR + high inflation → tightening; low FFR + high unemp → easing
            score = ffr_gap * 0.5 + inflation_gap * 0.3 - unemp_gap * 0.2
            _emit(out, d, "US.Model.FedPolicy.Stance", score)
        except (TypeError, KeyError):
            continue
    return out


# ============================================================
# Model 2: Liquidity Impulse
# ============================================================

def compute_liquidity_impulse(data: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """Δ(BankReserves - RRP - TGA). Positive = liquidity injection."""
    reserves = _get_series(data, "US.Fed.BalanceSheet.BankReserves")
    rrp      = _get_series(data, "US.Fed.BalanceSheet.ReverseRepo")
    tga      = _get_series(data, "US.Fed.BalanceSheet.TGA")

    dates = _common_dates(reserves, rrp, tga)
    net_liq: dict[str, float] = {}
    for d in dates:
        try:
            net_liq[d] = reserves[d] - rrp[d] - tga[d]
        except (TypeError, KeyError):
            continue
    delta = _delta(net_liq, window=1)

    out: list[dict[str, Any]] = []
    for d, v in delta.items():
        _emit(out, d, "US.Model.FedPolicy.LiquidityImpulse", v)
    return out


# ============================================================
# Models 3-6: USD Index Components
# ============================================================

def compute_usd_policy_diff(data: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """USD policy premium = FFR - weighted G6 policy rates."""
    ffr  = _get_series(data, "US.Fed.Rates.FedFundsTarget.Upper")
    ecb  = _get_series(data, "EU.ECB.DepositFacilityRate")
    boj  = _get_series(data, "JP.BOJ.PolicyRate")
    boe  = _get_series(data, "UK.BOE.BankRate")

    dates = _common_dates(ffr, ecb, boj, boe)
    out: list[dict[str, Any]] = []
    for d in dates:
        try:
            weighted = (
                ecb[d] * DXY_WEIGHTS["EUR"]
                + boj[d] * DXY_WEIGHTS["JPY"]
                + boe[d] * DXY_WEIGHTS["GBP"]
            )
            normalizer = DXY_WEIGHTS["EUR"] + DXY_WEIGHTS["JPY"] + DXY_WEIGHTS["GBP"]
            weighted /= normalizer
            diff = ffr[d] - weighted
            _emit(out, d, "US.Model.USDIndex.PolicyDiff", diff)
        except (TypeError, KeyError):
            continue
    return out


def compute_usd_yield_diff_2y(data: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """Approximate as US2Y level (G10 weighted 2Y not yet sourced)."""
    us2y = _get_series(data, "US.Rates.Treasury.2Y")
    out: list[dict[str, Any]] = []
    for d, v in us2y.items():
        _emit(out, d, "US.Model.USDIndex.YieldDiff2Y", v)
    return out


def compute_usd_risk_factor(data: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """Z-score sum of VIX + MOVE + NFCI."""
    vix  = _get_series(data, "US.Sentiment.VIX")
    move = _get_series(data, "US.Sentiment.MOVE")
    nfci = _get_series(data, "US.FinCond.NFCI")

    nz_vix  = _normalize_series(vix)
    nz_move = _normalize_series(move)
    nz_nfci = _normalize_series(nfci)

    dates = _common_dates(nz_vix, nz_move, nz_nfci)
    out: list[dict[str, Any]] = []
    for d in dates:
        try:
            out.append({
                "date": d, "series_id": "US.Model.USDIndex.RiskFactor",
                "value": nz_vix[d] + nz_move[d] + nz_nfci[d], "source": SOURCE,
            })
        except (TypeError, KeyError):
            continue
    return out


def compute_usd_composite(
    policy_diff: list[dict[str, Any]],
    yield_diff_2y: list[dict[str, Any]],
    liquidity_impulse: list[dict[str, Any]],
    risk_factor: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Weighted composite: 0.35*Policy + 0.30*Y2 + 0.15*Liq + 0.10*Risk."""
    def _to_dict(records: list[dict[str, Any]]) -> dict[str, float]:
        return {r["date"]: r["value"] for r in records}

    p = _to_dict(policy_diff)
    y = _to_dict(yield_diff_2y)
    l = _to_dict(liquidity_impulse)
    r = _to_dict(risk_factor)

    dates = _common_dates(p, y, l, r)
    out: list[dict[str, Any]] = []
    for d in dates:
        v = 0.35 * p[d] + 0.30 * y[d] + 0.15 * l[d] + 0.10 * r[d]
        _emit(out, d, "US.Model.USDIndex.Composite", v)
    return out


# ============================================================
# Model 7: Yield Curve Inversion
# ============================================================

def compute_yield_curve_inversion(data: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """Fraction of (2s10s, 3m10y) spreads that are negative."""
    s_2s10s = _get_series(data, "US.Rates.Spread.2s10s")
    s_3m10y = _get_series(data, "US.Rates.Spread.3m10y")

    dates = _common_dates(s_2s10s, s_3m10y)
    out: list[dict[str, Any]] = []
    for d in dates:
        spreads = [s_2s10s[d], s_3m10y[d]]
        valid = [s for s in spreads if s is not None]
        if not valid:
            continue
        inverted_frac = sum(1 for s in valid if s < 0) / len(valid)
        _emit(out, d, "US.Model.YieldCurve.Inversion", inverted_frac)
    return out


# ============================================================
# Model 8: Monthly Fiscal Impulse
# ============================================================

def compute_fiscal_impulse(data: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """(Outlays - Receipts) / GDP_nominal_monthly."""
    outlays  = _get_series(data, "US.Fiscal.MTS.GrossOutlays")
    receipts = _get_series(data, "US.Fiscal.MTS.GrossReceipts")
    gdp      = _get_series(data, "US.Growth.GDP.Nominal")

    out: list[dict[str, Any]] = []
    dates = sorted(set(outlays.keys()) & set(receipts.keys()))
    for d in dates:
        try:
            # Estimate monthly GDP from nearest quarter (forward-fill)
            year_month = d[:7]
            gdp_val = None
            for gd in sorted(gdp.keys()):
                if gd <= d:
                    gdp_val = gdp[gd] / 12
            if gdp_val is None or gdp_val == 0:
                continue
            impulse = (outlays[d] - receipts[d]) / gdp_val
            _emit(out, d, "US.Model.Fiscal.MonthlyImpulse", impulse)
        except (TypeError, KeyError, ZeroDivisionError):
            continue
    return out


# ============================================================
# Model 9: Risk-On/Off Sentiment
# ============================================================

def compute_risk_on_off(data: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """norm(AAII_Spread) + norm(CNN_FG) - norm(VIX)."""
    aaii = _get_series(data, "US.Sentiment.AAII.BullBearSpread")
    cnn  = _get_series(data, "US.Sentiment.CNN.FearGreed")
    vix  = _get_series(data, "US.Sentiment.VIX")

    nz_a = _normalize_series(aaii)
    nz_c = _normalize_series(cnn)
    nz_v = _normalize_series(vix)

    dates = _common_dates(nz_a, nz_c, nz_v)
    out: list[dict[str, Any]] = []
    for d in dates:
        v = nz_a[d] + nz_c[d] - nz_v[d]
        _emit(out, d, "US.Model.Sentiment.RiskOnOff", v)
    return out


# ============================================================
# Unified entry
# ============================================================

def compute_all_models(data: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """Run all 9 derived models. Returns flat list of records.

    `data` is a dict mapping SSOT series_id -> {date_str: value}.
    Missing series are silently skipped within each model.
    """
    out: list[dict[str, Any]] = []

    stance   = compute_fed_policy_stance(data)
    liquid   = compute_liquidity_impulse(data)
    policy_d = compute_usd_policy_diff(data)
    yield2y  = compute_usd_yield_diff_2y(data)
    risk     = compute_usd_risk_factor(data)
    composite = compute_usd_composite(policy_d, yield2y, liquid, risk)
    inversion = compute_yield_curve_inversion(data)
    fiscal_i  = compute_fiscal_impulse(data)
    risk_oo   = compute_risk_on_off(data)

    out.extend(stance)
    out.extend(liquid)
    out.extend(policy_d)
    out.extend(yield2y)
    out.extend(risk)
    out.extend(composite)
    out.extend(inversion)
    out.extend(fiscal_i)
    out.extend(risk_oo)
    return out


if __name__ == "__main__":
    # Synthetic test
    fake_data = {
        "US.Fed.Rates.FedFundsTarget.Upper": {"2026-01-01": 5.5, "2026-02-01": 5.25},
        "US.Prices.PCE.Core.YoY":            {"2026-01-01": 3.2, "2026-02-01": 3.0},
        "US.Labor.UnempRate.U3":             {"2026-01-01": 4.1, "2026-02-01": 4.2},
        "US.Fed.BalanceSheet.BankReserves":  {"2026-01-01": 3200, "2026-02-01": 3250, "2026-03-01": 3300},
        "US.Fed.BalanceSheet.ReverseRepo":   {"2026-01-01": 600,  "2026-02-01": 550,  "2026-03-01": 500},
        "US.Fed.BalanceSheet.TGA":           {"2026-01-01": 700,  "2026-02-01": 750,  "2026-03-01": 720},
    }
    results = compute_all_models(fake_data)
    print(f"Computed {len(results)} derived records from {len(fake_data)} input series")
    for r in results[:5]:
        print(f"  {r}")
