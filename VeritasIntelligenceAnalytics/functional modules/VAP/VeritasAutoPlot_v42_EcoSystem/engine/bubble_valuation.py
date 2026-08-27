"""
VeritasAutoPlot™ Bubble Detection & Valuation Engine
=====================================================
Bubble Radar: Z-Score statistical deviation detection
Valuation Watchdog: Log-Linear Regression fair value channels
"""

import pandas as pd
import numpy as np
from scipy import stats


class BubbleEngine:
    """
    Veritas Bubble Index (VBI) — Z-Score based bubble detection.
    Z-Score > 3.0 σ → BUBBLE (statistically improbable)
    Z-Score < -3.0 σ → OVERSOLD
    """

    @staticmethod
    def detect(df: pd.DataFrame, price_col: str = 'Main_Price',
               window: int = 240, sensitivity: float = 3.0) -> pd.DataFrame:
        df = df.copy()
        price = df[price_col]

        roll_mean = price.rolling(window, min_periods=60).mean()
        roll_std = price.rolling(window, min_periods=60).std()

        df['Z_Score'] = (price - roll_mean) / (roll_std + 1e-10)
        df['Deviation_Pct'] = ((price - roll_mean) / (roll_mean + 1e-10)) * 100

        df['Bubble_Status'] = 'Normal'
        df.loc[df['Z_Score'] > sensitivity, 'Bubble_Status'] = 'BUBBLE'
        df.loc[df['Z_Score'] < -sensitivity, 'Bubble_Status'] = 'OVERSOLD'

        return df

    @staticmethod
    def get_bubble_events(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        bubbles = df[df['Bubble_Status'] == 'BUBBLE'].copy()
        if bubbles.empty:
            return pd.DataFrame()
        return bubbles.nlargest(top_n, 'Z_Score')[
            ['Main_Price', 'Deviation_Pct', 'Z_Score', 'Bubble_Status']
        ]


class ValuationEngine:
    """
    Log-Linear Regression Valuation Engine.
    Calculates fair value using log-space regression channels.
    """

    @staticmethod
    def calculate(df: pd.DataFrame, price_col: str = 'Main_Price') -> pd.DataFrame:
        df = df.copy()
        price = df[price_col].dropna()

        if len(price) < 30:
            return df

        y = np.log(price.values)
        x = np.arange(len(y))

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        fair_log = slope * x + intercept
        residuals = y - fair_log
        std_dev = residuals.std()

        df.loc[price.index, 'Fair_Value'] = np.exp(fair_log)
        df.loc[price.index, 'Overvalued_Line'] = np.exp(fair_log + 2 * std_dev)
        df.loc[price.index, 'Undervalued_Line'] = np.exp(fair_log - 2 * std_dev)

        # Valuation Score (0-100)
        current_price = price.iloc[-1]
        fair = np.exp(fair_log[-1])
        upper = np.exp(fair_log[-1] + 2 * std_dev)
        lower = np.exp(fair_log[-1] - 2 * std_dev)

        if upper != lower:
            val_score = ((current_price - lower) / (upper - lower)) * 100
            val_score = np.clip(val_score, 0, 100)
        else:
            val_score = 50

        df.attrs['valuation_score'] = float(val_score)
        df.attrs['r_squared'] = float(r_value ** 2)
        df.attrs['regression_slope'] = float(slope)
        df.attrs['fair_value_current'] = float(fair)

        return df
