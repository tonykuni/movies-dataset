import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.decomposition import PCA
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.vector_ar.var_model import VAR


class SectorAnalysisEngine:
    """
    A quantitative analysis engine for multi-stock sectors evaluating:
    1. Co-movement (族群性): Correlation Matrix, PCA Absorption Ratio, Cointegration
    2. Lead-Lag (領先性): Cross-Correlation Lag Matrix, Lead/Lag Ranking
    3. Market Heat (熱門度): Volume Expansion, Volatility-Volume Boost
    """

    def __init__(self, prices: pd.DataFrame, volumes: pd.DataFrame):
        """
        :param prices: DataFrame of Adjusted Close prices (index=Date, columns=Stock Tickers)
        :param volumes: DataFrame of Trading Volume / Turnover (index=Date, columns=Stock Tickers)
        """
        self.prices = prices.copy().dropna()
        self.volumes = volumes.reindex(self.prices.index).fillna(0)
        self.tickers = list(self.prices.columns)
        
        # Calculate log returns
        self.log_returns = np.log(self.prices / self.prices.shift(1)).dropna()

    def calculate_co_movement(self) -> Dict[str, Any]:
        """
        Category 1: 族群性 (Co-movement Analysis)
        Computes return correlation matrix, average correlation, PCA absorption ratio, and cointegration.
        """
        # 1. Pearson & Spearman correlation of log returns
        pearson_corr = self.log_returns.corr(method='pearson')
        spearman_corr = self.log_returns.corr(method='spearman')

        # Extract non-diagonal correlation values
        n = len(self.tickers)
        if n > 1:
            triu_indices = np.triu_indices_from(pearson_corr, k=1)
            avg_pearson = float(pearson_corr.values[triu_indices].mean())
            avg_spearman = float(spearman_corr.values[triu_indices].mean())
        else:
            avg_pearson, avg_spearman = 1.0, 1.0

        # 2. PCA Absorption Ratio (explained variance of PC1)
        pca = PCA(n_components=min(5, len(self.tickers)))
        pca.fit(self.log_returns)
        pc1_absorption_ratio = float(pca.explained_variance_ratio_[0])
        pc2_absorption_ratio = float(pca.explained_variance_ratio_[:2].sum())

        # 3. Pairwise Cointegration (Long-term price equilibrium)
        cointegrated_pairs = []
        for i in range(len(self.tickers)):
            for j in range(i + 1, len(self.tickers)):
                t1, t2 = self.tickers[i], self.tickers[j]
                try:
                    score, p_value, _ = ts.coint(self.prices[t1], self.prices[t2])
                    if p_value < 0.05:
                        cointegrated_pairs.append({
                            'pair': (t1, t2),
                            'p_value': round(p_value, 4),
                            't_stat': round(score, 2)
                        })
                except Exception:
                    pass

        return {
            'avg_pearson_corr': round(avg_pearson, 4),
            'avg_spearman_corr': round(avg_spearman, 4),
            'pc1_absorption_ratio': round(pc1_absorption_ratio, 4),
            'top_2_pc_absorption': round(pc2_absorption_ratio, 4),
            'pearson_matrix': pearson_corr.round(4),
            'cointegrated_pairs': cointegrated_pairs
        }

    def calculate_lead_lag(self, max_lag: int = 5) -> Dict[str, Any]:
        """
        Category 2: 領先性 (Lead-Lag Relationship)
        Calculates cross-correlation function (CCF) matrices and ranks leading vs follower stocks.
        """
        lead_scores = {ticker: 0.0 for ticker in self.tickers}
        lag_matrix = pd.DataFrame(index=self.tickers, columns=self.tickers, dtype=float)

        # Pairwise Cross-Correlation Analysis
        for i, t1 in enumerate(self.tickers):
            for j, t2 in enumerate(self.tickers):
                if i == j:
                    lag_matrix.loc[t1, t2] = 0
                    continue

                r1 = self.log_returns[t1]
                r2 = self.log_returns[t2]

                best_lag = 0
                max_corr = -1.0

                # Test lags from -max_lag to +max_lag
                for lag in range(-max_lag, max_lag + 1):
                    if lag < 0:
                        corr = r1.iloc[-lag:].corr(r2.iloc[:lag])
                    elif lag > 0:
                        corr = r1.iloc[:-lag].corr(r2.iloc[lag:])
                    else:
                        corr = r1.corr(r2)

                    if not np.isnan(corr) and abs(corr) > max_corr:
                        max_corr = abs(corr)
                        best_lag = lag

                lag_matrix.loc[t1, t2] = best_lag
                # If best_lag > 0, t1 leads t2 by `best_lag` days
                lead_scores[t1] += best_lag

        # Rank leadership
        ranked_leaders = sorted(lead_scores.items(), key=lambda x: x[1], reverse=True)

        return {
            'optimal_lag_matrix': lag_matrix,
            'leader_scores': lead_scores,
            'ranked_leaders': ranked_leaders
        }

    def calculate_market_heat(self, lookback: int = 20) -> Dict[str, Any]:
        """
        Category 3: 熱門度 (Market Attention & Volume Dynamics)
        Measures volume expansion, relative turnover ratio, and price-volatility surge.
        """
        # 1. Volume Turnover Expansion Ratio (Current Volume / N-day Moving Average Volume)
        vol_ma = self.volumes.rolling(window=lookback).mean()
        volume_expansion = (self.volumes / vol_ma).iloc[-1].fillna(1.0)

        # 2. Relative Volume Share within Sector
        latest_volumes = self.volumes.iloc[-1]
        sector_total_volume = latest_volumes.sum()
        volume_share = (latest_volumes / sector_total_volume) if sector_total_volume > 0 else latest_volumes * 0

        # 3. Volume-Volatility Surge Index
        daily_std = self.log_returns.rolling(window=lookback).std().iloc[-1]
        heat_index = (volume_expansion * (1 + daily_std)).round(4)

        return {
            'volume_expansion_ratio': volume_expansion.round(2).to_dict(),
            'sector_volume_share': volume_share.round(4).to_dict(),
            'heat_index': heat_index.to_dict(),
            'overall_sector_heat_score': round(float(volume_expansion.mean()), 2)
        }

    def analyze(self) -> Dict[str, Any]:
        """Runs the entire quantitative sector diagnostic."""
        co_mov = self.calculate_co_movement()
        lead_lag = self.calculate_lead_lag()
        heat = self.calculate_market_heat()

        return {
            'co_movement': co_mov,
            'lead_lag': lead_lag,
            'market_heat': heat
        }


def generate_mock_sector_data(days: int = 120) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generates synthetic stock price and volume series with built-in sector lead-lag relationships."""
    np.random.seed(42)
    dates = pd.date_range(end='2026-07-28', periods=days, freq='B')
    
    # Common sector market driver
    sector_factor = np.random.normal(0.001, 0.02, size=days)
    
    # Leader stock (A)
    ret_A = sector_factor + np.random.normal(0, 0.008, size=days)
    
    # Follower stocks (B lags A by 2 days, C lags A by 1 day)
    ret_B = np.roll(ret_A, 2) * 0.8 + np.random.normal(0, 0.01, size=days)
    ret_C = np.roll(ret_A, 1) * 0.9 + np.random.normal(0, 0.009, size=days)
    ret_D = sector_factor * 0.5 + np.random.normal(0, 0.015, size=days)

    returns_df = pd.DataFrame({'StockA': ret_A, 'StockB': ret_B, 'StockC': ret_C, 'StockD': ret_D}, index=dates)
    price_df = 100 * np.exp(returns_df.cumsum())
    
    # Volume data with surge on recent days
    base_vol = pd.DataFrame(np.random.randint(1000, 5000, size=(days, 4)), index=dates, columns=returns_df.columns)
    base_vol.iloc[-5:, 0] *= 3.5  # StockA volume surge

    return price_df, base_vol


if __name__ == '__main__':
    print("=== Generating Synthetic Stock Sector Data ===")
    prices, volumes = generate_mock_sector_data()

    print("\n=== Initializing Sector Analysis Engine ===")
    engine = SectorAnalysisEngine(prices, volumes)
    results = engine.analyze()

    print("\n--- 1. 族群性 (Sector Co-movement) ---")
    print(f"Average Return Correlation: {results['co_movement']['avg_pearson_corr']}")
    print(f"PC1 Absorption Ratio: {results['co_movement']['pc1_absorption_ratio'] * 100:.2f}%")
    print(f"Cointegrated Pairs Count: {len(results['co_movement']['cointegrated_pairs'])}")

    print("\n--- 2. 領先性 (Lead-Lag Ranking) ---")
    print("Leader Ranking (Higher score = Leads more stocks):")
    for ticker, score in results['lead_lag']['ranked_leaders']:
        print(f"  {ticker}: Lead Score = {score}")

    print("\n--- 3. 熱門度 (Market Attention & Volume Dynamics) ---")
    print("Volume Expansion Ratios (Current / 20MA):")
    for ticker, val in results['market_heat']['volume_expansion_ratio'].items():
        print(f"  {ticker}: {val}x")
    print(f"Overall Sector Heat Score: {results['market_heat']['overall_sector_heat_score']}")
```eoc