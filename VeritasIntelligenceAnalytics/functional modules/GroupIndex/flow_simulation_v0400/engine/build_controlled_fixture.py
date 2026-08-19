from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine.via_classification_intake import SOURCE_HTML_NAME, def_extract_candidate_membership


# =============================================================================
# PARAMETERS · controlled fixture only
# =============================================================================
FIXTURE_GROUP_COUNT = 31
FIXTURE_START_DATE = "2025-10-01"
FIXTURE_TRADING_DAYS = 220
FIXTURE_RANDOM_SEED = 20260819
FIXTURE_DATA_MODE = "DEMO_FIXTURE_DO_NOT_PROMOTE"


def def_parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the VIA controlled 31-group fixture")
    parser.add_argument("--output-dir", default="data/input", help="Fixture output directory")
    return parser.parse_args()


def def_build_membership(reference_dir: Path | None = None) -> tuple[pd.DataFrame, dict[str, object]]:
    """Use the attached 31-group list as candidate identity, never as market truth."""
    resolved = reference_dir or Path(__file__).resolve().parents[1] / "references" / "intake"
    membership, quality = def_extract_candidate_membership(resolved / SOURCE_HTML_NAME, resolved)
    membership["PrimaryEconomicIdentity"] = membership["GroupName"]
    membership["SourceVersion"] = "ATTACHED_CANDIDATE_LIST_WITH_CONTROLLED_MARKET_FIXTURE_V0200"
    membership["DataEvidence"] = FIXTURE_DATA_MODE
    return membership, quality


def def_build_market_tables(membership: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(FIXTURE_RANDOM_SEED)
    dates = pd.bdate_range(FIXTURE_START_DATE, periods=FIXTURE_TRADING_DAYS)
    market_factor = rng.normal(0.00035, 0.0080, len(dates))
    price_rows: list[dict[str, object]] = []
    institutional_rows: list[dict[str, object]] = []
    margin_rows: list[dict[str, object]] = []
    etf_rows: list[dict[str, object]] = []
    main_force_rows: list[dict[str, object]] = []

    group_factors: dict[str, np.ndarray] = {}
    group_numbers: dict[str, int] = {}
    for group_number, group_id in enumerate(sorted(membership["GroupId"].unique()), start=1):
        group_factor = 0.58 * market_factor + rng.normal(0.00012, 0.0065, len(dates))
        group_factors[str(group_id)] = group_factor
        group_numbers[str(group_id)] = group_number

    # One synthetic market row per distinct ticker. A ticker may retain more than one
    # economic identity in membership without creating duplicate Date+Ticker rows.
    primary_membership = membership.sort_values(["Ticker", "GroupId"]).drop_duplicates("Ticker")
    for member_number, row in enumerate(primary_membership.itertuples(index=False), start=1):
            ticker = str(row.Ticker)
            group_id = str(row.GroupId)
            group_number = group_numbers[group_id]
            group_factor = group_factors[group_id]
            role = str(getattr(row, "CandidateRole", "PEER"))
            flow_cycle = np.sin(np.arange(len(dates)) / (11.0 + group_number % 7))
            idio = rng.normal(0.0, 0.0072 + (member_number % 5) * 0.00035, len(dates))
            lead_component = np.roll(group_factor, -1) * (0.18 if role == "LEADER" else 0.0)
            lag_component = np.roll(group_factor, 1) * (0.18 if role == "LAGGARD" else 0.0)
            returns = group_factor + idio + lead_component + lag_component
            returns[0] = 0.0
            close = (35.0 + group_number * 1.55 + (member_number % 7) * 1.8) * np.cumprod(1.0 + returns)
            volume = rng.lognormal(13.7 + group_number / 120.0, 0.35, len(dates))
            volume[(group_number * 13 + member_number * 7) % len(dates)] = np.nan
            turnover = close * volume
            analytical_turnover = close * np.where(np.isnan(volume), np.nanmedian(volume), volume)
            daytrade_ratio = np.clip(rng.normal(0.24, 0.06, len(dates)), 0.05, 0.55)
            market_cap = close * (58_000_000 + group_number * 2_300_000 + member_number * 900_000)
            institutional_driver = (returns * 2.6 + flow_cycle * 0.012) * analytical_turnover
            regime = group_number % 3
            foreign_weight = {1: 0.72, 2: 0.16, 0: 0.10}[regime]
            trust_weight = {1: 0.18, 2: 0.72, 0: 0.10}[regime]
            dealer_weight = {1: 0.10, 2: 0.12, 0: 0.08}[regime]
            main_weight = {1: 0.05, 2: 0.06, 0: 0.88}[regime]
            foreign_noise = {1: 0.004, 2: 0.014, 0: 0.018}[regime]
            trust_noise = {1: 0.010, 2: 0.004, 0: 0.018}[regime]
            main_noise = {1: 0.014, 2: 0.014, 0: 0.003}[regime]
            foreign = institutional_driver * foreign_weight + rng.normal(0.0, foreign_noise, len(dates)) * analytical_turnover
            trust = institutional_driver * trust_weight + rng.normal(0.0, trust_noise, len(dates)) * analytical_turnover
            dealer = institutional_driver * dealer_weight + rng.normal(0.0, 0.006, len(dates)) * analytical_turnover
            main_force = institutional_driver * main_weight
            main_force += rng.normal(0.0, main_noise, len(dates)) * analytical_turnover
            branch_concentration = np.clip(
                (0.28 if regime == 0 else 0.10) + np.abs(main_force) / np.maximum(analytical_turnover, 1.0) * 1.8
                + rng.normal(0.0, 0.018, len(dates)),
                0.02,
                0.78,
            )
            margin_delta = (-returns * 0.7 + flow_cycle * 0.005) * analytical_turnover
            short_delta = (returns * 0.17 - flow_cycle * 0.0015) * analytical_turnover
            margin_balance = 900_000_000 + group_number * 22_000_000 + np.cumsum(margin_delta)
            short_balance = 85_000_000 + group_number * 1_100_000 + np.cumsum(short_delta)
            active_etf_flow = institutional_driver * (0.08 + member_number * 0.01)

            for index, date in enumerate(dates):
                price_rows.append(
                    {
                        "Date": date.strftime("%Y-%m-%d"),
                        "Ticker": ticker,
                        "Adj_Close": float(close[index]),
                        "Volume": None if np.isnan(volume[index]) else float(volume[index]),
                        "TurnoverValue": None if np.isnan(volume[index]) else float(turnover[index]),
                        "DayTradeTurnover": None if np.isnan(volume[index]) else float(turnover[index] * daytrade_ratio[index]),
                        "MarketCap": float(market_cap[index]),
                    }
                )
                institutional_rows.append(
                    {
                        "Date": date.strftime("%Y-%m-%d"),
                        "Ticker": ticker,
                        "ForeignNetAmount": float(foreign[index]),
                        "InvestmentTrustNetAmount": float(trust[index]),
                        "DealerNetAmount": float(dealer[index]),
                    }
                )
                margin_rows.append(
                    {
                        "Date": date.strftime("%Y-%m-%d"),
                        "Ticker": ticker,
                        "MarginBalanceValue": float(max(margin_balance[index], 0.0)),
                        "ShortBalanceValue": float(max(short_balance[index], 0.0)),
                    }
                )
                etf_rows.append(
                    {
                        "Date": date.strftime("%Y-%m-%d"),
                        "Ticker": ticker,
                        "ETFId": f"FETF{group_number:02d}",
                        "ActiveETFFlowAmount": float(active_etf_flow[index]),
                    }
                )
                main_force_rows.append(
                    {
                        "Date": date.strftime("%Y-%m-%d"),
                        "Ticker": ticker,
                        "MainForceNetAmount": float(main_force[index]),
                        "BranchConcentration": float(branch_concentration[index]),
                    }
                )

    institutional = pd.DataFrame(institutional_rows)
    missing_mask = institutional.index % 997 == 0
    institutional.loc[missing_mask, ["ForeignNetAmount", "InvestmentTrustNetAmount", "DealerNetAmount"]] = np.nan
    return {
        "price": pd.DataFrame(price_rows),
        "institutional": institutional,
        "margin_short": pd.DataFrame(margin_rows),
        "active_etf_pcf": pd.DataFrame(etf_rows),
        "main_force": pd.DataFrame(main_force_rows),
    }


def def_write_fixture(output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    project_root = output_dir.resolve().parents[1]
    reference_dir = project_root / "references" / "intake"
    if not (reference_dir / SOURCE_HTML_NAME).exists():
        reference_dir = Path(__file__).resolve().parents[1] / "references" / "intake"
    membership, quality = def_build_membership(reference_dir)
    evidence_dir = project_root / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "classification_candidate_quality.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    tables = def_build_market_tables(membership)
    membership.to_csv(output_dir / "membership.csv", index=False, encoding="utf-8-sig")
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False, encoding="utf-8-sig")
    counts = {"membership": int(len(membership))}
    counts.update({name: int(len(frame)) for name, frame in tables.items()})
    counts["groups"] = int(quality["GroupCount"])
    counts["unverified_market_rows"] = int(quality["UnverifiedMarketRows"])
    return counts


def def_main() -> int:
    args = def_parse_args()
    counts = def_write_fixture(Path(args.output_dir).resolve())
    print("def Fixture Status : CONTROLLED_FIXTURE_READY")
    for name, count in counts.items():
        print(f"def {name:<16}: {count:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(def_main())
