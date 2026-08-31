"""
VeritasAutoPlot™ Technical Analysis Engine
===========================================
Computes: SMA, EMA, Bollinger Bands, MACD, RSI, KD
All calculations use pure Pandas (no TA-Lib dependency).
"""

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
import pandas as pd
import numpy as np


class VeritasTAEngine:
    """Technical indicator calculation engine."""

    # ── SMA ──────────────────────────────────────────────────────
    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        return series.rolling(window=period, min_periods=1).mean()

    # ── EMA ──────────────────────────────────────────────────────
    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    # ── Bollinger Bands ──────────────────────────────────────────
    @staticmethod
    def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0):
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    # ── MACD ─────────────────────────────────────────────────────
    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    # ── RSI ──────────────────────────────────────────────────────
    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - (100 / (1 + rs))

    # ── KD (Stochastic Oscillator) ──────────────────────────────
    @staticmethod
    def kd(high: pd.Series, low: pd.Series, close: pd.Series,
           k_period: int = 9, d_period: int = 3):
        lowest_low = low.rolling(window=k_period, min_periods=1).min()
        highest_high = high.rolling(window=k_period, min_periods=1).max()
        rsv = (close - lowest_low) / (highest_high - lowest_low + 1e-10) * 100
        k_line = rsv.ewm(com=d_period - 1, adjust=False).mean()
        d_line = k_line.ewm(com=d_period - 1, adjust=False).mean()
        return k_line, d_line

    # ── Full Calculation Pipeline ────────────────────────────────
    @classmethod
    def calculate_all(cls, df: pd.DataFrame, price_col: str = 'Main_Price') -> pd.DataFrame:
        """
        Calculate all technical indicators and add them to the DataFrame.
        Requires: Main_Price column. Optionally: Open, High, Low, Close, Volume.
        """
        df = df.copy()
        price = df[price_col]

        # SMA System (5, 10, 20, 60, 120, 240)
        for period in [5, 10, 20, 60, 120, 240]:
            df[f'SMA_{period}'] = cls.sma(price, period)

        # EMA System (12, 26)
        for period in [12, 26]:
            df[f'EMA_{period}'] = cls.ema(price, period)

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = cls.bollinger_bands(price)
        df['BB_Upper'] = bb_upper
        df['BB_Middle'] = bb_middle
        df['BB_Lower'] = bb_lower

        # MACD
        macd_line, signal_line, histogram = cls.macd(price)
        df['MACD'] = macd_line
        df['MACD_Signal'] = signal_line
        df['MACD_Hist'] = histogram

        # RSI
        df['RSI'] = cls.rsi(price)

        # KD (needs High/Low/Close)
        has_hlc = all(
            any(c.lower() == name for c in df.columns)
            for name in ['high', 'low', 'close']
        )
        if has_hlc:
            high_col = next(c for c in df.columns if c.lower() == 'high')
            low_col = next(c for c in df.columns if c.lower() == 'low')
            close_col = next(c for c in df.columns if c.lower() == 'close')
            k_line, d_line = cls.kd(df[high_col], df[low_col], df[close_col])
            df['K'] = k_line
            df['D'] = d_line
        else:
            # Fallback: use Main_Price as proxy
            k_line, d_line = cls.kd(price, price, price)
            df['K'] = k_line
            df['D'] = d_line

        # Daily Returns
        df['Daily_Ret'] = price.pct_change()

        # Rolling Volatility (20-day annualized)
        df['Rolling_Vol'] = df['Daily_Ret'].rolling(20).std() * np.sqrt(252)

        # Drawdown
        cummax = price.cummax()
        df['Drawdown'] = (price - cummax) / cummax

        return df


class VeritasQuantEngine:
    """Quantitative metrics calculator."""

    @staticmethod
    def calc_metrics(df: pd.DataFrame, price_col: str = 'Main_Price',
                     risk_free_rate: float = 0.02) -> dict:
        """Calculate comprehensive quantitative metrics."""
        price = df[price_col].dropna()
        returns = price.pct_change().dropna()

        total_days = (price.index[-1] - price.index[0]).days if isinstance(price.index, pd.DatetimeIndex) else len(price)
        years = max(total_days / 365.25, 0.01)

        total_return = (price.iloc[-1] / price.iloc[0]) - 1
        cagr = (1 + total_return) ** (1 / years) - 1
        volatility = returns.std() * np.sqrt(252)

        # Sharpe
        sharpe = (cagr - risk_free_rate) / volatility if volatility > 0 else 0

        # Sortino
        downside = returns[returns < 0].std() * np.sqrt(252)
        sortino = (cagr - risk_free_rate) / downside if downside > 0 else 0

        # Max Drawdown
        cummax = price.cummax()
        drawdown = (price - cummax) / cummax
        max_dd = drawdown.min()

        # Distribution
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        # VaR (95%)
        var_95 = returns.quantile(0.05)

        # Win Rate
        win_rate = (returns > 0).sum() / len(returns)

        return {
            "Total_Return": total_return,
            "CAGR": cagr,
            "Volatility": volatility,
            "Sharpe_Ratio": sharpe,
            "Sortino_Ratio": sortino,
            "Max_Drawdown": max_dd,
            "Skewness": skewness,
            "Kurtosis": kurtosis,
            "VaR_95": var_95,
            "Win_Rate": win_rate,
            "Total_Days": total_days,
            "Years": years,
        }
