"""Local-first quantitative and technical-analysis engine built on Polars.

The calculation layer intentionally does not depend on TA-Lib, pandas, or
NumPy. NumPy is only used in the optional sector/PCA adapter in a separate
function. Market-data adapters are kept at the boundary; calculations accept
Polars DataFrame/LazyFrame inputs.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import date, datetime
from math import isfinite
from typing import Any, Literal, Mapping, Sequence

import polars as pl


SUPPORTED_WINDOWS: tuple[int, ...] = (5, 10, 20, 60, 120)
PRICE_REQUIRED_COLUMNS = {"date", "ticker", "adj_close"}
OHLCV_REQUIRED_COLUMNS = PRICE_REQUIRED_COLUMNS | {"high", "low", "non_day_trade_volume"}
TURNOVER_REQUIRED_COLUMNS = {"date", "ticker", "non_day_trade_turnover"}

# The catalog is intentionally compact. It distinguishes price/volume
# indicators from advanced market-structure inputs so feature engineering can
# select one representative from each family instead of duplicating highly
# collinear moving averages.
INDICATOR_CATEGORIES: dict[str, tuple[str, ...]] = {
    "trend": ("sma", "ema", "macd", "adx", "directional_index"),
    "momentum": ("rsi", "stochastic_kd", "roc", "williams_r", "cci"),
    "volatility": ("atr", "bollinger", "keltner", "donchian", "return_volatility", "true_range"),
    "volume_flow": ("obv", "mfi", "cmf", "adl", "vwap", "volume_ratio"),
    "relative_market": ("beta", "correlation", "residual_return", "relative_strength"),
    "microstructure_fundamental": ("institutional_flow", "margin_short", "toca", "valuation_band"),
    "statistical_structure": ("autocorrelation", "return_volume_correlation", "return_range_correlation", "cross_correlation"),
    "risk": ("beta", "sharpe", "sortino", "calmar", "var", "cvar", "drawdown"),
}

IMPORTANT_INDICATORS: dict[str, tuple[str, ...]] = {
    "trend": ("ema_20", "ema_60", "macd_line", "macd_signal", "adx_14"),
    "momentum": ("rsi_14", "stoch_k_14", "stoch_d_14", "roc_20", "williams_r_14", "cci_20"),
    "volatility": ("atr", "bb_width_20", "bb_position_20", "keltner_width", "donchian_upper_20", "return_vol_20"),
    "volume_flow": ("obv", "adl", "mfi_14", "cmf_20", "rolling_vwap_20", "volume_ratio_20"),
    "relative_market": ("rolling_beta", "rolling_corr", "clean_residual_ret"),
    "microstructure_fundamental": ("institutional_amount_ratio", "toca_z_score", "valuation_z_score"),
    "statistical_structure": ("return_autocorr_20", "return_volume_corr_20", "return_range_corr_20"),
    "risk": ("rolling_beta", "rolling_sharpe", "rolling_sortino", "rolling_calmar", "rolling_var", "rolling_cvar"),
}

CATEGORY_LABELS_ZH: dict[str, str] = {
    "TREND": "趨勢",
    "MOMENTUM": "動能",
    "VOLATILITY": "波動率",
    "VOLUME_FLOW": "成交量／資金流",
    "RELATIVE_MARKET": "相對市場",
    "MICROSTRUCTURE": "籌碼／微結構",
    "STATISTICAL_STRUCTURE": "統計結構／相關性",
    "RISK": "風險調整",
    "DATA_GOVERNANCE": "資料治理",
}


@dataclass(frozen=True)
class ParameterSpec:
    """Machine-readable parameter metadata and human-readable explanation."""

    code: str
    name_zh: str
    category_code: str
    unit: str
    default: Any
    description: str
    benchmark: str
    pros: str
    cons: str
    remedy: str
    alternatives: str


PARAMETER_REGISTRY: dict[str, ParameterSpec] = {
    "windows": ParameterSpec(
        "WIN_STD", "標準觀察窗", "DATA_GOVERNANCE", "trading_days", SUPPORTED_WINDOWS,
        "跨指標共用的輸出觀察窗", "5／10／20／60／120 日", "可比較且容易治理",
        "不同市場狀態可能需要不同衰減速度", "由 walk-forward 選擇並凍結至下一次 refit",
        "自適應 half-life、事件窗、YTD",
    ),
    "rsi_period": ParameterSpec(
        "MOM_RSI", "RSI 週期", "MOMENTUM", "trading_days", 14,
        "Wilder RSI 的平滑週期", "RSI 14", "容易解讀、跨標的可比較",
        "趨勢市場可能長時間停留在超買或超賣", "同時保留 RSI level、斜率與 regime，不單獨交易",
        "RSI 5／10／20、自適應半衰期 RSI",
    ),
    "macd_fast": ParameterSpec(
        "TRD_MACD_FAST", "MACD 快線週期", "TREND", "trading_days", 12,
        "MACD 快速 EMA 週期", "MACD 12／26／9", "可表達趨勢動能差",
        "交叉訊號延遲且在盤整期間反覆打滑", "加入 ADX、波動狀態與成交量確認",
        "EMA spread、回歸斜率、變點偵測",
    ),
    "macd_slow": ParameterSpec(
        "TRD_MACD_SLOW", "MACD 慢線週期", "TREND", "trading_days", 26,
        "MACD 慢速 EMA 週期", "MACD 12／26／9", "提供較穩定的方向濾網",
        "反應慢、轉折點落後", "以 walk-forward 選擇，不把單一歷史最佳值永久化",
        "EMA 60、EMA 120、價格對均線距離",
    ),
    "macd_signal": ParameterSpec(
        "TRD_MACD_SIGNAL", "MACD 訊號線週期", "TREND", "trading_days", 9,
        "MACD 線的平滑週期", "MACD 12／26／9", "降低單日雜訊",
        "增加訊號延遲", "搭配 histogram 斜率與突破確認",
        "EWM slope、ADX trend strength",
    ),
    "atr_period": ParameterSpec(
        "VOL_ATR", "ATR 週期", "VOLATILITY", "trading_days", 14,
        "Wilder True Range 平滑週期", "ATR 14", "適合動態停損與部位調整",
        "價格單位不可直接跨股比較", "同時輸出 atr_pct = ATR／adj_close",
        "Parkinson、Garman-Klass、realized volatility",
    ),
    "adx_period": ParameterSpec(
        "TRD_ADX", "ADX 週期", "TREND", "trading_days", 14,
        "趨勢強度平滑週期", "ADX 14", "區分有方向趨勢與亂盤",
        "不提供方向，且盤整後反應較慢", "與 +DI／-DI 及價格方向一起判讀",
        "回歸 R²、trend slope、change-point",
    ),
    "adx_smoothing_period": ParameterSpec(
        "TRD_ADX_SMOOTH", "ADX 平滑週期", "TREND", "trading_days", 14,
        "DX 轉 ADX 的 Wilder 平滑週期，可與 DI 週期分離", "DMI DI length／ADX smoothing",
        "控制趨勢強度訊號的平滑程度", "過短增加雜訊，與 DI 週期綁死會限制校準",
        "以 walk-forward 選擇，並保留 DI 與 ADX 兩個參數", "ADX 14／21、rolling R2、trend slope",
    ),
    "stochastic_period": ParameterSpec(
        "MOM_STOCH", "KD／ROC／Williams 週期", "MOMENTUM", "trading_days", 14,
        "高低位階與動能指標的觀察窗", "KD 14", "可捕捉區間轉折",
        "強趨勢中容易過早發出反向訊號", "加入 trend_regime 與持續性條件",
        "RSI、CCI、短期 return rank",
    ),
    "cci_period": ParameterSpec(
        "MOM_CCI", "CCI 週期", "MOMENTUM", "trading_days", 20,
        "典型價相對平均偏差的週期", "CCI 20／0.015", "補足 RSI/KD 之外的均值偏離動能",
        "盤整與趨勢市場的 100 門檻語意不同", "與趨勢 regime、成交量及波動狀態一起使用",
        "RSI、ROC、typical-price z-score",
    ),
    "money_flow_period": ParameterSpec(
        "FLOW_MFI", "MFI 週期", "VOLUME_FLOW", "trading_days", 14,
        "正負典型價資金流的觀察窗", "MFI 14", "把價格與成交量合併",
        "成交量口徑或低流動性會扭曲結果", "使用官方成交值並加入 coverage／liquidity gate",
        "CMF、A/D、OBV、rolling VWAP",
    ),
    "bollinger_period": ParameterSpec(
        "VOL_BB", "布林通道週期", "VOLATILITY", "trading_days", 20,
        "均值與價格帶寬的觀察窗", "Bollinger 20／2", "可描述波動收縮與擴張",
        "盤整突破與趨勢延伸難以單靠帶寬區分", "結合 breakout、ADX、volume_ratio",
        "Keltner Channel、ATR channel",
    ),
    "bollinger_k": ParameterSpec(
        "VOL_BB_K", "布林標準差倍數", "VOLATILITY", "standard_deviations", 2.0,
        "布林上下軌距離均值的標準差倍數", "Bollinger 20／2", "尺度直觀",
        "不同波動分布下固定 2 倍不一定同樣稀有", "以自身歷史 percentile 或 quantile 校準",
        "分位數通道、ATR channel",
    ),
    "keltner_period": ParameterSpec(
        "VOL_KC", "Keltner 基準週期", "VOLATILITY", "trading_days", 20,
        "Keltner 中線 EMA 的週期", "EMA 20 + ATR 14 × 2", "比布林通道更偏向 ATR 尺度的波動帶",
        "不同平台對 basis、ATR length 與 range style 定義可能不同", "獨立記錄 basis、ATR、倍數並做 TradingView fixture 校準",
        "Bollinger Bands、Donchian Channel",
    ),
    "keltner_atr_period": ParameterSpec(
        "VOL_KC_ATR", "Keltner ATR 週期", "VOLATILITY", "trading_days", 14,
        "Keltner 通道 ATR 的獨立週期", "EMA 20 + ATR 14 × 2", "可分別控制中線速度與波動帶反應",
        "若與中線週期混用，平台間結果容易不一致", "在參數與輸出欄位中明確分開 basis period 與 ATR period",
        "ATR 14、ATR 20、Keltner range mode",
    ),
    "keltner_multiplier": ParameterSpec(
        "VOL_KC_K", "Keltner ATR 倍數", "VOLATILITY", "ATR_multiple", 2.0,
        "Keltner 上下軌距離中線的 ATR 倍數", "ATR 14 × 2", "用價格單位的 ATR 控制帶寬",
        "固定倍數不能反映不同市場的尾部分布", "保留 KC width 並以歷史分位校準，不單獨作突破訊號",
        "Bollinger k、ATR stop、quantile channel",
    ),
    "ewm_half_life": ParameterSpec(
        "GOV_EWM_HALF_LIFE", "EWM 半衰期", "DATA_GOVERNANCE", "trading_days", 20.0,
        "動態平均與風險估計的權重衰減速度", "近期資料權重高於遠期資料",
        "比固定 rolling window 更能適應狀態變化", "太短會放大雜訊，太長會反應遲緩",
        "以 walk-forward 選擇並在下一次 refit 前凍結",
        "rolling window、EWMA span、Kalman filter",
    ),
    "min_observations": ParameterSpec(
        "GOV_MIN_OBS", "最小有效觀測數", "DATA_GOVERNANCE", "observations", 30,
        "計算指標前必須具備的最少有效資料量", "依指標與視窗登錄 min_samples",
        "阻擋小樣本假訊號", "增加暖機期並保留 null，不以零填補",
        "對小樣本輸出 insufficient_data，不產生交易級結論",
        "有效樣本權重、bootstrap confidence interval",
    ),
    "price_basis": ParameterSpec(
        "GOV_PRICE_BASIS", "價格基準", "DATA_GOVERNANCE", "enum", "adj_close",
        "股票價格與技術指標的統一價格口徑", "調整後價格／Adjusted OHLC",
        "避免除權息造成虛假跳點", "若沒有 adjusted price 必須先補足並記錄來源",
        "缺少 adjusted price 時停止計算或進入明確的補價流程",
        "raw close 僅供交易執行與漲跌停診斷，不作回報特徵主口徑",
    ),
    "turnover_source": ParameterSpec(
        "GOV_TURNOVER_SOURCE", "成交值來源", "DATA_GOVERNANCE", "enum", "TWSE_TPEX",
        "成交值與當沖欄位的官方資料來源", "TWSE／TPEX 官方成交值",
        "單位與市場口徑一致，可追溯修訂", "當沖資料可能在 T+1／T+2 修訂，且不是淨資金流",
        "保存 revision_status 與 available_at，不把活動量稱為淨資金流",
        "資料庫封裝的官方 fetcher，但不得改變來源語意",
    ),
    "feature_lag_sessions": ParameterSpec(
        "GOV_FEATURE_LAG", "外部特徵滯後交易日", "DATA_GOVERNANCE", "trading_sessions", 1,
        "公告或收盤後資料進入訊號的交易日延遲", "t+1 execution", "降低資料洩漏風險",
        "可能犧牲部分即時性，且不能取代 available_at", "使用 point-in-time available_at join",
        "lag 0 僅限已確認盤中可得資料；as-of join",
    ),
}

BENCHMARK_CATALOG: tuple[dict[str, str], ...] = (
    {
        "code": "MARKET_INDEX",
        "name_zh": "大盤指數",
        "benchmark": "TWII／TAIEX 或指定市場指數",
        "pros": "代表整體市場系統性風險，資料易取得，適合估計市場 Beta",
        "cons": "台股大型權值股集中，可能把台積電或少數權值股的波動誤當成全市場因子",
        "remedy": "同時報告原始 Beta、ex-giant Beta 與市場廣度，並保留殘差報酬",
        "alternatives": "EX_GIANT_MARKET、等權市場、自由流通市值市場",
        "recommended_for": "全市場風險、投資組合 Beta、基礎相對強弱",
    },
    {
        "code": "EX_GIANT_MARKET",
        "name_zh": "排除巨型權值股市場",
        "benchmark": "排除 2330 或註冊巨型股後的市場指數",
        "pros": "降低單一巨型權值股對中小型股與族群關聯的支配",
        "cons": "不再是可直接投資的市場組合，且巨型股本身的系統性影響會被移除",
        "remedy": "與 MARKET_INDEX 並列，不以單一版本取代另一版本",
        "alternatives": "市場等權指數、產業中性市場、兩版本殘差交叉檢查",
        "recommended_for": "中小型股、族群共振、TOCA 分母與去權值分析",
    },
    {
        "code": "GROUP_EQUAL_WEIGHT",
        "name_zh": "族群等權指數",
        "benchmark": "PIT 合格族群成分的滯後等權報酬鏈結",
        "pros": "避免單一大型股代表整個族群，適合檢驗族群內部共振",
        "cons": "小型低流動性股票會被賦予與大型股相同權重",
        "remedy": "加上最小流動性、coverage、停牌與成分數 gate；並列替代權重",
        "alternatives": "GROUP_LAGGED_FREE_FLOAT、liquidity-adjusted equal weight",
        "recommended_for": "族群方向、PCA、共同動因與 Leave-One-Out 相對強弱",
    },
    {
        "code": "GROUP_LAGGED_FREE_FLOAT",
        "name_zh": "族群落後自由流通市值加權",
        "benchmark": "t-1 point-in-time free-float market-cap weighted group index",
        "pros": "較接近可投資資金配置與實際市場曝險",
        "cons": "大型股重新主導指數，且自由流通市值資料可能修訂或延遲",
        "remedy": "只使用 t-1 可得權重，與等權版本並列並做權重集中度報告",
        "alternatives": "GROUP_EQUAL_WEIGHT、cap-capped free-float weight",
        "recommended_for": "可投資指數、資金容量與投資組合歸因",
    },
    {
        "code": "LEAVE_ONE_OUT_GROUP",
        "name_zh": "排除個股自身的族群基準",
        "benchmark": "group return excluding the focal ticker",
        "pros": "避免個股被放進自己的基準造成機械式高相關",
        "cons": "小族群的基準不穩定，成分變動時相對路徑容易跳變",
        "remedy": "設定最少 peer 數，成分變更時重設 membership episode",
        "alternatives": "產業等權基準、同市值匹配基準、market residual",
        "recommended_for": "Leader／Peer／Laggard 與個股族群相對強弱",
    },
    {
        "code": "NEGATIVE_CONTROL",
        "name_zh": "陰性對照基準",
        "benchmark": "隨機匹配族群、日期置換或來源符號置換",
        "pros": "檢查高相關、PCA 或領先關係是否只是樣本結構假象",
        "cons": "單次隨機結果不穩定，計算成本較高且不能直接形成交易基準",
        "remedy": "使用 block permutation、多次重抽樣與 FDR 控制",
        "alternatives": "industry-neutral matched control、date permutation",
        "recommended_for": "統計驗證與 release gate，不作交易訊號本身",
    },
)


@dataclass(frozen=True)
class EngineConfig:
    """Explicit defaults used by the engine.

    ``windows`` may contain only the supported standard windows. Indicator
    defaults are benchmark periods, not assumptions that every indicator must
    use the same period.
    """

    windows: tuple[int, ...] = SUPPORTED_WINDOWS
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    atr_period: int = 14
    adx_period: int = 14
    adx_smoothing_period: int = 14
    stochastic_period: int = 14
    money_flow_period: int = 14
    cci_period: int = 20
    bollinger_period: int = 20
    bollinger_k: float = 2.0
    keltner_period: int = 20
    keltner_atr_period: int = 14
    keltner_multiplier: float = 2.0
    ewm_half_life: float = 20.0
    min_observations: int = 30
    price_basis: Literal["adj_close"] = "adj_close"
    turnover_source: Literal["TWSE_TPEX"] = "TWSE_TPEX"

    def __post_init__(self) -> None:
        if not self.windows:
            raise ValueError("windows must not be empty")
        invalid = set(self.windows) - set(SUPPORTED_WINDOWS)
        if invalid:
            raise ValueError(
                f"unsupported windows: {sorted(invalid)}; "
                f"use only {SUPPORTED_WINDOWS}"
            )
        for name in (
            "rsi_period",
            "macd_fast",
            "macd_slow",
            "macd_signal",
            "atr_period",
            "adx_period",
            "adx_smoothing_period",
            "stochastic_period",
            "money_flow_period",
            "cci_period",
            "bollinger_period",
            "keltner_period",
            "keltner_atr_period",
        ):
            value = getattr(self, name)
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.macd_fast >= self.macd_slow:
            raise ValueError("macd_fast must be smaller than macd_slow")
        if self.bollinger_k <= 0:
            raise ValueError("bollinger_k must be positive")
        if self.keltner_multiplier <= 0:
            raise ValueError("keltner_multiplier must be positive")
        if self.ewm_half_life <= 0:
            raise ValueError("ewm_half_life must be positive")
        if self.min_observations < 2:
            raise ValueError("min_observations must be >= 2")


def _as_lazy(df: pl.DataFrame | pl.LazyFrame) -> pl.LazyFrame:
    return df.lazy() if isinstance(df, pl.DataFrame) else df


def _require_columns(df: pl.DataFrame | pl.LazyFrame, required: set[str]) -> None:
    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    missing = required - columns
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")


def _display_parameter_value(value: Any) -> str:
    if isinstance(value, bool):
        return "啟用" if value else "停用"
    if isinstance(value, (tuple, list)):
        return "／".join(_display_parameter_value(item) for item in value)
    if value is None:
        return "未設定"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def encode_parameters(
    config: EngineConfig | Mapping[str, Any] | None = None,
    *,
    include_unregistered: bool = True,
) -> pl.DataFrame:
    """Encode parameter values into stable codes, categories, and display text.

    The returned table is suitable for a dashboard, audit manifest, CSV, or
    API response. Unknown mapping keys are retained as ``UNREGISTERED`` by
    default so a UI can show them instead of silently dropping configuration.
    """

    if config is None:
        values: dict[str, Any] = asdict(EngineConfig())
    elif isinstance(config, EngineConfig):
        values = asdict(config)
    else:
        values = dict(config)

    rows: list[dict[str, Any]] = []
    for key, value in values.items():
        spec = PARAMETER_REGISTRY.get(key)
        if spec is None:
            if not include_unregistered:
                continue
            rows.append({
                "parameter_key": key,
                "parameter_code": f"UNREGISTERED_{key.upper()}",
                "category_code": "UNREGISTERED",
                "category_name_zh": "未登錄參數",
                "value": _display_parameter_value(value),
                "value_display": _display_parameter_value(value),
                "unit": "unknown",
                "default": None,
                "status": "UNREGISTERED",
                "description_zh": "此參數尚未加入治理 registry",
                "benchmark": "需補登 Benchmark",
                "pros": "可保留原始設定",
                "cons": "無法自動判斷語意與回測治理",
                "remedy": "註冊參數代碼、分類、單位與 point-in-time 規則",
                "alternatives": "明確移除或加入 PARAMETER_REGISTRY",
            })
            continue
        rows.append({
            "parameter_key": key,
            "parameter_code": spec.code,
            "category_code": spec.category_code,
            "category_name_zh": CATEGORY_LABELS_ZH.get(spec.category_code, spec.category_code),
            "value": _display_parameter_value(value),
            "value_display": f"{_display_parameter_value(value)} {spec.unit}",
            "unit": spec.unit,
            "default": _display_parameter_value(spec.default),
            "status": "DEFAULT" if value == spec.default else "OVERRIDE",
            "description_zh": spec.description,
            "benchmark": spec.benchmark,
            "pros": spec.pros,
            "cons": spec.cons,
            "remedy": spec.remedy,
            "alternatives": spec.alternatives,
        })
    return pl.DataFrame(rows).sort(["category_code", "parameter_code"])


def render_parameter_text(
    config: EngineConfig | Mapping[str, Any] | None = None,
    *,
    include_pros_cons: bool = True,
) -> str:
    """Render encoded parameters as compact Traditional-Chinese text."""

    table = encode_parameters(config)
    lines: list[str] = ["量化引擎參數摘要"]
    for row in table.iter_rows(named=True):
        lines.append(
            f"[{row['parameter_code']}] {row['category_name_zh']}｜"
            f"{row['parameter_key']}={row['value_display']}｜{row['status']}｜"
            f"{row['description_zh']}"
        )
        if include_pros_cons:
            lines.append(
                f"  Benchmark: {row['benchmark']}；優點: {row['pros']}；"
                f"缺點: {row['cons']}；修正: {row['remedy']}；替代: {row['alternatives']}"
            )
    return "\n".join(lines)


def benchmark_catalog_table() -> pl.DataFrame:
    """Return the Benchmark pros/cons/remedy/alternative catalog."""

    return pl.DataFrame(list(BENCHMARK_CATALOG))


def encode_category_label(category_code: str, *, language: str = "zh-Hant") -> str:
    """Map a stable category code to dashboard text."""

    if language not in {"zh-Hant", "en"}:
        raise ValueError("language must be zh-Hant or en")
    if language == "en":
        return category_code
    return CATEGORY_LABELS_ZH.get(category_code, "未分類")


def validate_input_schema(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    require_ohlcv: bool = False,
    require_turnover: bool = False,
) -> None:
    """Validate the canonical input contract before calculations."""

    _require_columns(df, OHLCV_REQUIRED_COLUMNS if require_ohlcv else PRICE_REQUIRED_COLUMNS)
    if require_turnover:
        _require_columns(df, TURNOVER_REQUIRED_COLUMNS)

    schema = df.collect_schema() if isinstance(df, pl.LazyFrame) else df.schema
    if schema["date"] not in (pl.Date, pl.Datetime):
        raise TypeError("date must be pl.Date or pl.Datetime")
    if "volume" in schema and "non_day_trade_volume" not in schema:
        raise ValueError("raw volume is forbidden in analysis; provide non_day_trade_volume")
    for column in ("adj_close", "high", "low", "volume", "non_day_trade_volume"):
        if column in schema and schema[column] not in (pl.Float32, pl.Float64, pl.Int32, pl.Int64, pl.UInt32, pl.UInt64):
            raise TypeError(f"{column} must be numeric")


def _validate_benchmark_schema(df: pl.DataFrame | pl.LazyFrame) -> None:
    """Validate a benchmark series, which does not need a ticker column."""

    _require_columns(df, {"date", "adj_close"})
    schema = df.collect_schema() if isinstance(df, pl.LazyFrame) else df.schema
    if schema["date"] not in (pl.Date, pl.Datetime):
        raise TypeError("benchmark date must be pl.Date or pl.Datetime")
    if schema["adj_close"] not in (pl.Float32, pl.Float64, pl.Int32, pl.Int64, pl.UInt32, pl.UInt64):
        raise TypeError("benchmark adj_close must be numeric")


def _prepare_adjusted_ohlc(df: pl.DataFrame | pl.LazyFrame) -> pl.LazyFrame:
    """Return a frame whose high/low columns are adjusted-price based.

    Preferred inputs are ``adj_high`` and ``adj_low``. When only raw OHLC is
    available, the adjusted factor ``adj_close / close`` is applied to raw
    high/low. This prevents mixing raw intraday ranges with adjusted closes.
    """

    _require_columns(df, {"date", "ticker", "adj_close", "non_day_trade_volume"})
    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    q = _as_lazy(df).with_columns(
        pl.col("non_day_trade_volume").alias("volume")
    )
    if {"adj_high", "adj_low"}.issubset(columns):
        return q.with_columns([
            pl.col("adj_high").alias("high"),
            pl.col("adj_low").alias("low"),
        ])
    if {"high", "low", "close"}.issubset(columns):
        factor = pl.when(pl.col("close") > 0).then(pl.col("adj_close") / pl.col("close")).otherwise(None)
        return q.with_columns([
            (pl.col("high") * factor).alias("high"),
            (pl.col("low") * factor).alias("low"),
        ])
    raise ValueError(
        "adjusted OHLC required: provide adj_high/adj_low, or raw high/low/close "
        "so the engine can derive them from adj_close/close"
    )


def load_data(
    *,
    source: str | pl.DataFrame | pl.LazyFrame | None = None,
    query: str | None = None,
    connection: Any | None = None,
    fetcher: Callable[..., pl.DataFrame | pl.LazyFrame] | None = None,
    fetcher_kwargs: dict[str, Any] | None = None,
) -> pl.DataFrame | pl.LazyFrame:
    """Load data from Polars, Parquet, a database, or a user-supplied fetcher.

    The engine does not prescribe a vendor. A fetcher should return a Polars
    frame already normalized to the canonical schema.
    """

    choices = sum(x is not None for x in (source, query, fetcher))
    if choices != 1:
        raise ValueError("provide exactly one of source, query, or fetcher")
    if isinstance(source, (pl.DataFrame, pl.LazyFrame)):
        return source
    if isinstance(source, str):
        if not source.lower().endswith((".parquet", ".parquet/")):
            raise ValueError("string source currently supports Parquet paths only")
        return pl.scan_parquet(source)
    if query is not None:
        if connection is None:
            raise ValueError("connection is required with query")
        return pl.read_database(query=query, connection=connection).lazy()
    assert fetcher is not None
    result = fetcher(**(fetcher_kwargs or {}))
    if not isinstance(result, (pl.DataFrame, pl.LazyFrame)):
        raise TypeError("fetcher must return pl.DataFrame or pl.LazyFrame")
    return result


def _ordered_prices(df: pl.DataFrame | pl.LazyFrame) -> pl.LazyFrame:
    validate_input_schema(df)
    return _as_lazy(df).sort(["ticker", "date"])


def _safe_div(numerator: pl.Expr, denominator: pl.Expr) -> pl.Expr:
    return pl.when(denominator.is_not_null() & (denominator.abs() > 1e-12)).then(
        numerator / denominator
    ).otherwise(None)


def _cci_window(values: pl.Series) -> float | None:
    """CCI window using mean absolute deviation, not standard deviation."""

    values = values.drop_nulls()
    if values.len() == 0:
        return None
    mean = float(values.mean())
    mean_deviation = sum(abs(float(value) - mean) for value in values) / values.len()
    if mean_deviation <= 1e-12:
        return None
    return (float(values[-1]) - mean) / (0.015 * mean_deviation)


def _ewm_mean(expr: pl.Expr, half_life: float, *, min_samples: int = 2) -> pl.Expr:
    return expr.ewm_mean(
        half_life=half_life,
        adjust=True,
        min_samples=min_samples,
        ignore_nulls=True,
    )


def _ewm_std(expr: pl.Expr, half_life: float, *, min_samples: int = 2) -> pl.Expr:
    return expr.ewm_std(
        half_life=half_life,
        adjust=True,
        min_samples=min_samples,
        ignore_nulls=True,
    )


def _return_expr(price_col: str, *, by_ticker: bool = True) -> pl.Expr:
    previous = pl.col(price_col).shift(1)
    if by_ticker:
        previous = previous.over("ticker")
    return pl.when(
        pl.col(price_col).is_not_null()
        & previous.is_not_null()
        & (previous > 0)
    ).then(pl.col(price_col) / previous - 1.0).otherwise(None)


def _rolling_zscore_expr(
    expr: pl.Expr,
    window: int,
    *,
    by_ticker: bool = True,
    min_samples: int | None = None,
) -> pl.Expr:
    min_samples = min_samples or window
    mean = expr.rolling_mean(window_size=window, min_samples=min_samples)
    std = expr.rolling_std(window_size=window, min_samples=min_samples, ddof=1)
    if by_ticker:
        mean = mean.over("ticker")
        std = std.over("ticker")
    return _safe_div(expr - mean, std)


def add_returns(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    price_col: str = "adj_close",
) -> pl.LazyFrame:
    """Add simple returns from adjusted prices without filling prices."""

    if price_col != "adj_close":
        raise ValueError("stocks must calculate returns from adj_close")
    return _ordered_prices(df).with_columns(
        _return_expr(price_col).alias("ret")
    )


def rolling_beta_corr(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    benchmark: pl.DataFrame | pl.LazyFrame | None = None,
    window: int = 60,
    min_samples: int | None = None,
    forward_fill_prices: bool = False,
) -> pl.DataFrame:
    """Calculate rolling Beta and Pearson correlation from synchronous returns.

    Input columns: ``date``, ``ticker``, ``adj_close``. If ``benchmark`` is
    supplied it must contain ``date`` and ``adj_close`` and is joined by date.
    If it is omitted, the input must contain ``bench_adj_close``.

    The default does *not* forward-fill prices. For a cross-market calendar,
    pass ``forward_fill_prices=True`` only when the economic convention is
    explicitly "stale last close represents held value". Missing observations
    are then still tracked through ``effective_n``.
    """

    if window < 2:
        raise ValueError("window must be >= 2")
    if min_samples is None:
        min_samples = window
    if min_samples < 2 or min_samples > window:
        raise ValueError("min_samples must be between 2 and window")

    validate_input_schema(df)
    asset = _as_lazy(df).select(["date", "ticker", "adj_close"])
    if benchmark is not None:
        _validate_benchmark_schema(benchmark)
        bench = _as_lazy(benchmark).select(
            ["date", pl.col("adj_close").alias("bench_adj_close")]
        )
        q = asset.join(bench, on="date", how="left")
    else:
        columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
        if "bench_adj_close" not in columns:
            raise ValueError("provide benchmark or bench_adj_close")
        q = _as_lazy(df).select(["date", "ticker", "adj_close", "bench_adj_close"])

    q = q.sort(["ticker", "date"])
    if forward_fill_prices:
        q = q.with_columns([
            pl.col("adj_close").forward_fill().over("ticker"),
            pl.col("bench_adj_close").forward_fill(),
        ])

    q = q.with_columns([
        _return_expr("adj_close").alias("asset_ret"),
        _return_expr("bench_adj_close", by_ticker=False).alias("bench_ret"),
    ])
    q = q.with_columns(
        pl.when(pl.col("asset_ret").is_not_null() & pl.col("bench_ret").is_not_null())
        .then(1)
        .otherwise(0)
        .rolling_sum(window_size=window, min_samples=min_samples)
        .over("ticker")
        .alias("effective_n")
    )
    # Polars rolling_cov uses sample covariance by default (ddof=1). This is
    # preferable to hand-expanding E[XY] because null rows then use the actual
    # effective N instead of an incorrect fixed N correction.
    q = q.with_columns([
        pl.rolling_cov(
            pl.col("asset_ret"),
            pl.col("bench_ret"),
            window_size=window,
            min_samples=min_samples,
            ddof=1,
        ).over("ticker").alias("rolling_cov"),
        pl.col("bench_ret").rolling_var(
            window_size=window, min_samples=min_samples, ddof=1
        ).over("ticker").alias("bench_var"),
        pl.col("asset_ret").rolling_std(
            window_size=window, min_samples=min_samples, ddof=1
        ).over("ticker").alias("asset_std"),
        pl.col("bench_ret").rolling_std(
            window_size=window, min_samples=min_samples, ddof=1
        ).over("ticker").alias("bench_std"),
    ])
    q = q.with_columns([
        _safe_div(pl.col("rolling_cov"), pl.col("bench_var")).alias("rolling_beta"),
        _safe_div(
            pl.col("rolling_cov"), pl.col("asset_std") * pl.col("bench_std")
        ).alias("rolling_corr"),
    ])
    return q.select([
        "date", "ticker", "adj_close", "bench_adj_close", "asset_ret",
        "bench_ret", "effective_n", "rolling_beta", "rolling_corr",
    ]).collect()


def technical_indicators(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    config: EngineConfig | None = None,
    windows: Iterable[int] | None = None,
) -> pl.DataFrame:
    """Calculate Polars-native technical indicators from adjusted OHLCV.

    RSI and ATR use Wilder-style smoothing through ``ewm_mean(alpha=1/n)``.
    MACD uses exponentially weighted means. Bollinger standard deviation is
    population standard deviation, matching the documented convention.
    """

    config = config or EngineConfig()
    q = _prepare_adjusted_ohlc(df)
    validate_input_schema(q, require_ohlcv=True)
    selected_windows = tuple(windows or config.windows)
    invalid = set(selected_windows) - set(SUPPORTED_WINDOWS)
    if invalid:
        raise ValueError(f"unsupported windows: {sorted(invalid)}")

    q = q.sort(["ticker", "date"])
    close = pl.col("adj_close")
    prev_close = close.shift(1).over("ticker")
    prev_high = pl.col("high").shift(1).over("ticker")
    prev_low = pl.col("low").shift(1).over("ticker")
    prev_volume = pl.col("volume").shift(1).over("ticker")
    delta = close - prev_close
    gain = pl.when(delta > 0).then(delta).otherwise(0.0)
    loss = pl.when(delta < 0).then(-delta).otherwise(0.0)
    up_move = pl.col("high") - prev_high
    down_move = prev_low - pl.col("low")
    plus_dm = pl.when((up_move > down_move) & (up_move > 0)).then(up_move).otherwise(0.0)
    minus_dm = pl.when((down_move > up_move) & (down_move > 0)).then(down_move).otherwise(0.0)
    typical_price = (pl.col("high") + pl.col("low") + close) / 3.0
    money_flow = typical_price * pl.col("volume")
    money_flow_sign = typical_price - typical_price.shift(1).over("ticker")
    volume_log_return = pl.when(
        (pl.col("volume") > 0) & (prev_volume > 0)
    ).then((pl.col("volume") / prev_volume).log()).otherwise(None)
    intraday_range_pct = _safe_div(pl.col("high") - pl.col("low"), close)
    true_range = pl.max_horizontal(
        close * 0 + (pl.col("high") - pl.col("low")),
        (pl.col("high") - prev_close).abs(),
        (pl.col("low") - prev_close).abs(),
    )
    true_range = pl.when(prev_close.is_null()).then(
        pl.col("high") - pl.col("low")
    ).otherwise(true_range)

    q = q.with_columns([
        _return_expr("adj_close").alias("ret"),
        delta.alias("price_delta"),
        gain.alias("gain"),
        loss.alias("loss"),
        plus_dm.alias("plus_dm"),
        minus_dm.alias("minus_dm"),
        typical_price.alias("typical_price"),
        money_flow.alias("money_flow"),
        volume_log_return.alias("volume_log_return"),
        intraday_range_pct.alias("intraday_range_pct"),
        pl.when(delta > 0).then(pl.col("volume")).when(delta < 0).then(-pl.col("volume")).otherwise(0.0).alias("obv_step"),
        pl.when(money_flow_sign > 0).then(money_flow).otherwise(0.0).alias("positive_money_flow"),
        pl.when(money_flow_sign < 0).then(money_flow).otherwise(0.0).alias("negative_money_flow"),
        pl.when((pl.col("high") - pl.col("low")).abs() > 1e-12)
        .then(((2.0 * close - pl.col("low") - pl.col("high")) / (pl.col("high") - pl.col("low"))) * pl.col("volume"))
        .otherwise(0.0)
        .alias("cmf_money_flow"),
        true_range.alias("true_range"),
    ])

    # The expressions below are created from existing columns in earlier
    # with_columns stages, keeping dependency order explicit and optimizer-safe.
    alpha_rsi = 1.0 / config.rsi_period
    q = q.with_columns([
        pl.col("gain").ewm_mean(
            alpha=alpha_rsi, adjust=False, min_samples=config.rsi_period,
            ignore_nulls=True,
        ).over("ticker").alias("avg_gain"),
        pl.col("loss").ewm_mean(
            alpha=alpha_rsi, adjust=False, min_samples=config.rsi_period,
            ignore_nulls=True,
        ).over("ticker").alias("avg_loss"),
        pl.col("true_range").ewm_mean(
            alpha=1.0 / config.atr_period, adjust=False,
            min_samples=config.atr_period, ignore_nulls=True,
        ).over("ticker").alias("atr"),
        pl.col("plus_dm").ewm_mean(
            alpha=1.0 / config.adx_period, adjust=False, min_samples=config.adx_period, ignore_nulls=True,
        ).over("ticker").alias("plus_dm_smoothed"),
        pl.col("minus_dm").ewm_mean(
            alpha=1.0 / config.adx_period, adjust=False, min_samples=config.adx_period, ignore_nulls=True,
        ).over("ticker").alias("minus_dm_smoothed"),
        close.ewm_mean(span=config.macd_fast, adjust=False, min_samples=config.macd_fast, ignore_nulls=True).over("ticker").alias("ema_fast"),
        close.ewm_mean(span=config.macd_slow, adjust=False, min_samples=config.macd_slow, ignore_nulls=True).over("ticker").alias("ema_slow"),
    ])
    q = q.with_columns([
        pl.when(pl.col("avg_loss") == 0).then(100.0).otherwise(
            100.0 - 100.0 / (1.0 + pl.col("avg_gain") / pl.col("avg_loss"))
        ).alias(f"rsi_{config.rsi_period}"),
        _safe_div(pl.col("plus_dm_smoothed") * 100.0, pl.col("atr")).alias(f"plus_di_{config.adx_period}"),
        _safe_div(pl.col("minus_dm_smoothed") * 100.0, pl.col("atr")).alias(f"minus_di_{config.adx_period}"),
        (pl.col("ema_fast") - pl.col("ema_slow")).alias("macd_line"),
    ])
    q = q.with_columns([
        _safe_div(
            (pl.col(f"plus_di_{config.adx_period}") - pl.col(f"minus_di_{config.adx_period}")).abs() * 100.0,
            pl.col(f"plus_di_{config.adx_period}") + pl.col(f"minus_di_{config.adx_period}"),
        ).alias(f"dx_{config.adx_period}"),
        pl.col("macd_line").ewm_mean(
            span=config.macd_signal, adjust=False,
            min_samples=config.macd_signal, ignore_nulls=True,
        ).over("ticker").alias("macd_signal"),
    ]).with_columns([
        (pl.col("macd_line") - pl.col("macd_signal")).alias("macd_histogram"),
        pl.col("obv_step").cum_sum().over("ticker").alias("obv"),
        pl.col("cmf_money_flow").cum_sum().over("ticker").alias("adl"),
    ])

    q = q.with_columns(
        pl.col("typical_price").rolling_map(
            _cci_window,
            window_size=config.cci_period,
            min_samples=config.cci_period,
        ).over("ticker").alias(f"cci_{config.cci_period}")
    )

    # Momentum and volume-flow benchmark indicators. All windows are applied
    # within ticker and use adjusted prices.
    stochastic_low = pl.col("low").rolling_min(window_size=config.stochastic_period, min_samples=config.stochastic_period).over("ticker")
    stochastic_high = pl.col("high").rolling_max(window_size=config.stochastic_period, min_samples=config.stochastic_period).over("ticker")
    stochastic_rsv = _safe_div((close - stochastic_low) * 100.0, stochastic_high - stochastic_low)
    q = q.with_columns([
        stochastic_rsv.alias(f"stoch_rsv_{config.stochastic_period}"),
        _safe_div(
            pl.col("positive_money_flow").rolling_sum(window_size=config.money_flow_period, min_samples=config.money_flow_period).over("ticker") * 100.0,
            (pl.col("positive_money_flow") + pl.col("negative_money_flow")).rolling_sum(window_size=config.money_flow_period, min_samples=config.money_flow_period).over("ticker"),
        ).alias(f"mfi_{config.money_flow_period}"),
        _safe_div(
            pl.col("cmf_money_flow").rolling_sum(window_size=20, min_samples=20).over("ticker"),
            pl.col("volume").rolling_sum(window_size=20, min_samples=20).over("ticker"),
        ).alias("cmf_20"),
        _safe_div(
            pl.col("money_flow").rolling_sum(window_size=20, min_samples=20).over("ticker"),
            pl.col("volume").rolling_sum(window_size=20, min_samples=20).over("ticker"),
        ).alias("rolling_vwap_20"),
        _safe_div(close - close.shift(config.stochastic_period).over("ticker"), close.shift(config.stochastic_period).over("ticker")).alias(f"roc_{config.stochastic_period}"),
        _safe_div(
            stochastic_high - close,
            stochastic_high - stochastic_low,
        ).alias(f"williams_r_{config.stochastic_period}"),
        _safe_div(
            pl.col("typical_price") - pl.col("typical_price").rolling_mean(window_size=14, min_samples=14).over("ticker"),
            pl.col("typical_price").rolling_std(window_size=14, min_samples=14, ddof=0).over("ticker"),
        ).alias(f"tp_z_{config.stochastic_period}"),
        pl.col(f"dx_{config.adx_period}").ewm_mean(
            alpha=1.0 / config.adx_smoothing_period, adjust=False, min_samples=config.adx_smoothing_period, ignore_nulls=True,
        ).over("ticker").alias(f"adx_{config.adx_period}"),
    ])
    q = q.with_columns([
        stochastic_rsv.ewm_mean(alpha=1.0 / 3.0, adjust=False, min_samples=config.stochastic_period, ignore_nulls=True).over("ticker").alias(f"stoch_k_{config.stochastic_period}"),
    ]).with_columns([
        pl.col(f"stoch_k_{config.stochastic_period}").ewm_mean(alpha=1.0 / 3.0, adjust=False, min_samples=config.stochastic_period, ignore_nulls=True).over("ticker").alias(f"stoch_d_{config.stochastic_period}"),
    ]).with_columns([
        _safe_div(pl.col(f"stoch_k_{config.stochastic_period}") - pl.col(f"stoch_d_{config.stochastic_period}"), pl.lit(100.0)).alias(f"stoch_kd_spread_{config.stochastic_period}"),
    ])

    indicator_exprs: list[pl.Expr] = []
    for period in selected_windows:
        indicator_exprs.extend([
            close.rolling_mean(window_size=period, min_samples=period).over("ticker").alias(f"sma_{period}"),
            close.ewm_mean(span=period, adjust=False, min_samples=period, ignore_nulls=True).over("ticker").alias(f"ema_{period}"),
            close.rolling_std(window_size=period, min_samples=period, ddof=0).over("ticker").alias(f"bb_std_{period}"),
            pl.col("volume").rolling_mean(window_size=period, min_samples=period).over("ticker").alias(f"volume_sma_{period}"),
            pl.col("ret").rolling_std(window_size=period, min_samples=period, ddof=1).over("ticker").alias(f"return_vol_{period}"),
            _rolling_zscore_expr(pl.col("ret"), period, by_ticker=True).alias(f"return_z_{period}"),
            pl.col("high").rolling_max(window_size=period, min_samples=period).over("ticker").alias(f"donchian_upper_{period}"),
            pl.col("low").rolling_min(window_size=period, min_samples=period).over("ticker").alias(f"donchian_lower_{period}"),
            pl.rolling_corr(
                pl.col("ret"), pl.col("ret").shift(1).over("ticker"),
                window_size=period, min_samples=period, ddof=1,
            ).over("ticker").alias(f"return_autocorr_{period}"),
            pl.rolling_corr(
                pl.col("ret"), pl.col("volume_log_return"),
                window_size=period, min_samples=period, ddof=1,
            ).over("ticker").alias(f"return_volume_corr_{period}"),
            pl.rolling_corr(
                pl.col("ret"), pl.col("intraday_range_pct"),
                window_size=period, min_samples=period, ddof=1,
            ).over("ticker").alias(f"return_range_corr_{period}"),
        ])
    q = q.with_columns(indicator_exprs)
    for period in selected_windows:
        q = q.with_columns([
            (pl.col(f"sma_{period}") + config.bollinger_k * pl.col(f"bb_std_{period}")).alias(f"bb_upper_{period}"),
            (pl.col(f"sma_{period}") - config.bollinger_k * pl.col(f"bb_std_{period}")).alias(f"bb_lower_{period}"),
        ])
        q = q.with_columns([
            _safe_div(pl.col(f"bb_upper_{period}") - pl.col(f"bb_lower_{period}"), pl.col(f"sma_{period}")).alias(f"bb_width_{period}"),
            _safe_div(close - pl.col(f"bb_lower_{period}"), pl.col(f"bb_upper_{period}") - pl.col(f"bb_lower_{period}")).alias(f"bb_position_{period}"),
            _safe_div(pl.col("volume"), pl.col(f"volume_sma_{period}")).alias(f"volume_ratio_{period}"),
            _safe_div(pl.col("obv") - pl.col("obv").shift(period).over("ticker"), pl.lit(float(period))).alias(f"obv_slope_{period}"),
        ])
    q = q.with_columns([
        _safe_div(pl.col("atr"), close).alias("atr_pct"),
        close.ewm_mean(
            span=config.keltner_period, adjust=False,
            min_samples=config.keltner_period, ignore_nulls=True,
        ).over("ticker").alias("keltner_basis"),
        pl.col("true_range").ewm_mean(
            alpha=1.0 / config.keltner_atr_period, adjust=False,
            min_samples=config.keltner_atr_period, ignore_nulls=True,
        ).over("ticker").alias("keltner_atr"),
    ]).with_columns([
        (pl.col("keltner_basis") + config.keltner_multiplier * pl.col("keltner_atr")).alias("keltner_upper"),
        (pl.col("keltner_basis") - config.keltner_multiplier * pl.col("keltner_atr")).alias("keltner_lower"),
    ]).with_columns([
        _safe_div(pl.col("keltner_upper") - pl.col("keltner_lower"), pl.col("keltner_basis")).alias("keltner_width"),
    ])

    # Keep raw fields and all configured outputs. Intermediate columns are
    # intentionally omitted from the returned frame.
    keep = [
        "date", "ticker", "adj_close", "high", "low", "non_day_trade_volume", "ret",
        f"rsi_{config.rsi_period}", "atr", "atr_pct", "macd_line", "macd_signal", "macd_histogram",
        f"adx_{config.adx_period}", f"stoch_k_{config.stochastic_period}",
        f"stoch_d_{config.stochastic_period}", f"roc_{config.stochastic_period}",
        f"williams_r_{config.stochastic_period}", f"mfi_{config.money_flow_period}", f"cci_{config.cci_period}",
        "cmf_20", "rolling_vwap_20", "obv", "adl", "keltner_basis", "keltner_atr", "keltner_upper", "keltner_lower", "keltner_width", f"tp_z_{config.stochastic_period}",
    ]
    for period in selected_windows:
        keep.extend([
            f"sma_{period}", f"ema_{period}", f"bb_upper_{period}", f"bb_lower_{period}",
            f"bb_width_{period}", f"bb_position_{period}", f"volume_sma_{period}",
            f"volume_ratio_{period}", f"obv_slope_{period}", f"return_vol_{period}", f"return_z_{period}",
            f"donchian_upper_{period}", f"donchian_lower_{period}",
            f"return_autocorr_{period}", f"return_volume_corr_{period}", f"return_range_corr_{period}",
        ])
    return q.select(keep).collect()


def _prepare_point_in_time_feature(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    feature_column: str,
    feature_name: str,
    lag_sessions: int,
) -> pl.LazyFrame:
    """Prepare one date/ticker feature for a point-in-time join.

    The value available on row ``t`` is shifted by ``lag_sessions`` rows
    within each ticker while the join key remains date ``t``. This is a
    trading-session lag rather than a calendar-day lag.
    """

    if lag_sessions < 0:
        raise ValueError("lag_sessions must be >= 0")
    _require_columns(df, {"date", "ticker", feature_column})
    schema = df.collect_schema() if isinstance(df, pl.LazyFrame) else df.schema
    if schema["date"] not in (pl.Date, pl.Datetime):
        raise TypeError(f"{feature_name} date must be pl.Date or pl.Datetime")
    if schema[feature_column] not in (
        pl.Float32, pl.Float64, pl.Int32, pl.Int64, pl.UInt32, pl.UInt64
    ):
        raise TypeError(f"{feature_name} must be numeric")

    prepared = (
        _as_lazy(df)
        .select(["date", "ticker", pl.col(feature_column).alias(feature_name)])
        .sort(["ticker", "date"])
        .collect()
    )
    duplicate_keys = prepared.select(
        pl.struct(["date", "ticker"]).is_duplicated()
    ).to_series().any()
    if duplicate_keys:
        raise ValueError(f"{feature_name} must have unique (date, ticker) keys")
    if lag_sessions:
        prepared = prepared.with_columns(
            pl.col(feature_name).shift(lag_sessions).over("ticker").alias(feature_name)
        )
    return prepared.lazy()


def build_feature_matrix(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    config: EngineConfig | None = None,
    windows: Iterable[int] | None = None,
    benchmark: pl.DataFrame | pl.LazyFrame | None = None,
    institutional_features: pl.DataFrame | pl.LazyFrame | None = None,
    toca_features: pl.DataFrame | pl.LazyFrame | None = None,
    feature_lag_sessions: int = 1,
    include_risk_metrics: bool = True,
    label_horizons: Iterable[int] = (),
) -> pl.DataFrame:
    """Build a compact cross-category feature matrix from adjusted OHLCV.

    The matrix deliberately contains regime, relative-distance, confirmation,
    and data-quality features rather than every possible indicator. It uses
    only information available at row ``t``. Optional ``label_horizons`` add
    future returns as clearly named supervised-learning labels; labels are not
    used to build any feature.

    Categories represented here are trend, momentum, volatility, volume-flow,
    and optional market-relative risk. When ``include_risk_metrics`` is true,
    rolling Sharpe, Sortino, Calmar, VaR, and CVaR are joined from the
    independent risk module. ``institutional_features`` must contain
    ``institutional_amount_ratio`` and ``toca_features`` must contain
    ``toca_z_score``. Both are joined by ``date,ticker`` and lagged by one
    trading session by default to avoid using post-close information in the
    same-day signal.
    """

    config = config or EngineConfig()
    selected_windows = set(windows or config.windows)
    selected_windows.update({20, 60})
    tech = technical_indicators(df, config=config, windows=tuple(sorted(selected_windows)))
    q = tech.lazy().sort(["ticker", "date"])
    rsi_col = f"rsi_{config.rsi_period}"

    # The prior rolling high is shifted before comparison, so a current-day
    # breakout cannot use today's own high/close as part of its threshold.
    prior_high_20 = pl.col("adj_close").shift(1).rolling_max(
        window_size=20, min_samples=20
    ).over("ticker")
    prior_low_20 = pl.col("adj_close").shift(1).rolling_min(
        window_size=20, min_samples=20
    ).over("ticker")
    rolling_high_60 = pl.col("adj_close").rolling_max(
        window_size=60, min_samples=60
    ).over("ticker")
    q = q.with_columns([
        _safe_div(pl.col("adj_close"), pl.col("ema_20") ).alias("price_vs_ema_20"),
        _safe_div(pl.col("adj_close"), pl.col("ema_60") ).alias("price_vs_ema_60"),
    ]).with_columns([
        _safe_div(pl.col("ema_20") - pl.col("ema_60"), pl.col("ema_60")).alias("ema_spread_20_60"),
        _safe_div(pl.col("return_vol_20"), pl.col("return_vol_60")).alias("volatility_ratio_20_60"),
        (pl.col("volume_ratio_20") - 1.0).alias("volume_shock_20"),
        _safe_div(pl.col("adj_close") - prior_high_20, prior_high_20).alias("breakout_distance_20"),
        _safe_div(pl.col("adj_close") - rolling_high_60, rolling_high_60).alias("drawdown_from_high_60"),
        _safe_div(pl.col("ret"), pl.col("atr_pct")).alias("return_to_atr"),
    ]).with_columns([
        ((pl.col("price_vs_ema_60") > 1.0) & (pl.col("ema_spread_20_60") > 0)).cast(pl.Int8).alias("trend_regime"),
        ((pl.col(rsi_col) - 50.0) / 50.0).alias("momentum_score"),
        (pl.col("bb_width_20") - pl.col("bb_width_60")).alias("volatility_expansion"),
        ((pl.col("cmf_20") > 0) & (pl.col("volume_ratio_20") > 1.0)).cast(pl.Int8).alias("volume_flow_confirmation"),
        pl.sum_horizontal([
            (pl.col("return_autocorr_20") > 0).cast(pl.Int8),
            (pl.col("return_volume_corr_20") > 0).cast(pl.Int8),
            (pl.col("return_range_corr_20") > 0).cast(pl.Int8),
        ]).alias("correlation_confirmation_count"),
        (pl.col("adj_close") > prior_high_20).cast(pl.Int8).alias("breakout_20"),
        (pl.col("adj_close") < prior_low_20).cast(pl.Int8).alias("breakdown_20"),
        ((pl.col(rsi_col) > 50) & (pl.col("macd_histogram") > 0)).cast(pl.Int8).alias("momentum_confirmation"),
    ])
    q = q.with_columns([
        (
            (pl.col("trend_regime") == 1)
            & (pl.col("momentum_confirmation") == 1)
            & (pl.col("volume_flow_confirmation") == 1)
        ).cast(pl.Int8).alias("cross_quadrant_long_confirmation"),
        pl.sum_horizontal([
            pl.col("ema_20").is_not_null().cast(pl.Int8),
            pl.col("ema_60").is_not_null().cast(pl.Int8),
            pl.col(rsi_col).is_not_null().cast(pl.Int8),
            pl.col("atr_pct").is_not_null().cast(pl.Int8),
            pl.col("volume_ratio_20").is_not_null().cast(pl.Int8),
            pl.col("cmf_20").is_not_null().cast(pl.Int8),
        ]).alias("base_feature_quality_count"),
    ])

    if benchmark is not None:
        relative = rolling_beta_corr(
            _as_lazy(df).select(["date", "ticker", "adj_close"]),
            benchmark=benchmark,
            window=60,
            min_samples=min(60, config.min_observations),
        ).select([
            "date", "ticker", "rolling_beta", "rolling_corr", "asset_ret", "bench_ret",
        ]).with_columns([
            (pl.col("asset_ret") - pl.col("rolling_beta") * pl.col("bench_ret")).alias("residual_return_60"),
        ])
        q = q.join(relative.lazy(), on=["date", "ticker"], how="left")

    if include_risk_metrics:
        from .risk import calculate_risk_metrics

        risk = calculate_risk_metrics(
            q.select(["date", "ticker", "adj_close", "ret"]),
        ).select([
            "date", "ticker", "rolling_sharpe", "rolling_sortino",
            "rolling_calmar", "rolling_var", "rolling_cvar",
            "rolling_max_drawdown", "rolling_cagr",
        ])
        q = q.join(risk.lazy(), on=["date", "ticker"], how="left", validate="m:1")

    # These fields are usually published after the close and may be revised
    # later. The default one-session lag makes them available on the next
    # trading session rather than leaking same-day post-close information.
    external_quality_terms: list[pl.Expr] = []
    if institutional_features is not None:
        institutional = _prepare_point_in_time_feature(
            institutional_features,
            feature_column="institutional_amount_ratio",
            feature_name="institutional_amount_ratio",
            lag_sessions=feature_lag_sessions,
        )
        q = q.join(
            institutional,
            on=["date", "ticker"],
            how="left",
            validate="m:1",
        )
        external_quality_terms.append(
            pl.col("institutional_amount_ratio").is_not_null().cast(pl.Int8)
        )

    if toca_features is not None:
        toca = _prepare_point_in_time_feature(
            toca_features,
            feature_column="toca_z_score",
            feature_name="toca_z_score",
            lag_sessions=feature_lag_sessions,
        )
        q = q.join(
            toca,
            on=["date", "ticker"],
            how="left",
            validate="m:1",
        )
        external_quality_terms.append(
            pl.col("toca_z_score").is_not_null().cast(pl.Int8)
        )

    if external_quality_terms:
        q = q.with_columns(
            pl.sum_horizontal(external_quality_terms).alias("capital_feature_quality_count")
        ).with_columns(
            (
                pl.col("base_feature_quality_count")
                + pl.col("capital_feature_quality_count")
            ).alias("feature_quality_count")
        )
    else:
        q = q.with_columns(
            pl.col("base_feature_quality_count").alias("feature_quality_count")
        )

    if institutional_features is not None and toca_features is not None:
        q = q.with_columns([
            (
                (pl.col("institutional_amount_ratio") > 0)
                & (pl.col("toca_z_score") > 0)
            ).cast(pl.Int8).alias("capital_flow_confirmation"),
            (
                pl.col("institutional_amount_ratio") * pl.col("toca_z_score")
            ).alias("capital_flow_heat"),
        ])

    horizons = tuple(label_horizons)
    if any(h <= 0 for h in horizons):
        raise ValueError("label horizons must be positive")
    if len(set(horizons)) != len(horizons):
        raise ValueError("label horizons must be unique")
    for horizon in horizons:
        q = q.with_columns(
            (
                _safe_div(
                    pl.col("adj_close").shift(-horizon).over("ticker"),
                    pl.col("adj_close"),
                ) - 1.0
            ).alias(f"label_forward_return_{horizon}")
        )
    return q.collect()


def build_factor_composite(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    factor_weights: Mapping[str, float],
    output_col: str = "factor_composite",
    normalize_weights: bool = True,
    require_complete: bool = True,
) -> pl.DataFrame:
    """Build a versionable weighted factor composite without filling nulls.

    ``factor_weights`` must reference already calculated factor columns. The
    function records how many factor inputs were present and returns null when
    ``require_complete`` is true but one input is unavailable. This keeps a
    partial factor vector from masquerading as a complete signal.
    """

    if not factor_weights:
        raise ValueError("factor_weights must not be empty")
    if not output_col.isidentifier():
        raise ValueError("output_col must be a simple identifier")
    if any(not isfinite(float(weight)) for weight in factor_weights.values()):
        raise ValueError("factor weights must be finite")
    weight_total = sum(abs(float(weight)) for weight in factor_weights.values())
    if normalize_weights and weight_total <= 1e-15:
        raise ValueError("normalized factor weights must have non-zero absolute sum")
    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    missing = set(factor_weights) - columns
    if missing:
        raise ValueError(f"factor columns missing: {sorted(missing)}")

    denominator = weight_total if normalize_weights else 1.0
    terms = [pl.col(name) * (float(weight) / denominator) for name, weight in factor_weights.items()]
    quality = pl.sum_horizontal([
        pl.col(name).is_not_null().cast(pl.Int8) for name in factor_weights
    ]).alias("factor_composite_quality_count")
    composite = pl.sum_horizontal(terms).alias(output_col)
    q = _as_lazy(df).with_columns([quality, composite])
    if require_complete:
        q = q.with_columns(
            pl.when(pl.col("factor_composite_quality_count") == len(factor_weights))
            .then(pl.col(output_col))
            .otherwise(None)
            .alias(output_col)
        )
    return q.collect()


def build_toca(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    ewm_half_life: float = 10.0,
    z_min_samples: int = 20,
    tsmc_ticker: str = "2330",
    exclude_tsmc_from_numerator: bool = False,
) -> pl.DataFrame:
    """Calculate ex-TSMC retained-capital share and no-look-ahead EWM z-score.

    Required input is official TWSE/TPEX **non-day-trade** turnover data with
    one row per ``date,ticker``. The ingestion layer must subtract and validate
    day-trade turnover before calling this function, then upsert corrections
    through T+2 before calculation.
    """

    if ewm_half_life <= 0 or z_min_samples < 2:
        raise ValueError("ewm_half_life must be positive and z_min_samples >= 2")
    _require_columns(df, TURNOVER_REQUIRED_COLUMNS)
    q = _as_lazy(df).sort(["ticker", "date"])
    q = q.with_columns([
        pl.col("non_day_trade_turnover").alias("retained_cap"),
    ]).with_columns([
        pl.col("retained_cap").sum().over("date").alias("market_retained_cap"),
        pl.when(pl.col("ticker") == tsmc_ticker).then(pl.col("retained_cap")).otherwise(0.0)
        .sum().over("date").alias("tsmc_retained_cap"),
    ]).with_columns([
        (pl.col("market_retained_cap") - pl.col("tsmc_retained_cap")).alias("valid_market_cap"),
        pl.when(
            (pl.col("ticker") == tsmc_ticker) & pl.lit(exclude_tsmc_from_numerator)
        ).then(None).otherwise(
            _safe_div(pl.col("retained_cap"), pl.col("market_retained_cap") - pl.col("tsmc_retained_cap"))
        ).alias("toca_ratio"),
    ])

    # Shift before EWM: today's z-score is measured against information known
    # through yesterday, not against a mean/std that includes today's shock.
    q = q.with_columns([
        _ewm_mean(pl.col("toca_ratio").shift(1).over("ticker"), ewm_half_life, min_samples=z_min_samples).over("ticker").alias("toca_ewm_mean_prev"),
        _ewm_std(pl.col("toca_ratio").shift(1).over("ticker"), ewm_half_life, min_samples=z_min_samples).over("ticker").alias("toca_ewm_std_prev"),
    ]).with_columns([
        _safe_div(
            pl.col("toca_ratio") - pl.col("toca_ewm_mean_prev"),
            pl.col("toca_ewm_std_prev"),
        ).alias("toca_z_score"),
    ])
    return q.select([
        "date", "ticker", "retained_cap", "market_retained_cap",
        "tsmc_retained_cap", "valid_market_cap", "toca_ratio",
        "toca_ewm_mean_prev", "toca_ewm_std_prev", "toca_z_score",
    ]).collect()


def build_residual_returns(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    benchmark: pl.DataFrame | pl.LazyFrame | None = None,
    half_life: float = 20.0,
    volatility_window: int = 60,
    volatility_quantile: float = 0.30,
    min_samples: int = 20,
    forward_fill_prices: bool = False,
) -> pl.DataFrame:
    """Remove dynamic market beta and mask low-volatility observations."""

    if volatility_window < 2 or not 0 < volatility_quantile < 1:
        raise ValueError("invalid volatility_window or volatility_quantile")
    asset = _prepare_adjusted_ohlc(df).sort(["ticker", "date"])
    validate_input_schema(asset, require_ohlcv=True)
    if benchmark is not None:
        _validate_benchmark_schema(benchmark)
        bench = _as_lazy(benchmark).select(["date", pl.col("adj_close").alias("bench_adj_close")])
        q = asset.join(bench, on="date", how="left")
    else:
        columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
        if "bench_adj_close" not in columns:
            raise ValueError("provide benchmark or bench_adj_close")
        q = asset
    q = q.sort(["ticker", "date"])
    if forward_fill_prices:
        q = q.with_columns([
            pl.col("adj_close").forward_fill().over("ticker"),
            pl.col("bench_adj_close").forward_fill(),
        ])
    prev = pl.col("adj_close").shift(1).over("ticker")
    q = q.with_columns([
        _return_expr("adj_close").alias("ret"),
        pl.when(prev.is_null()).then(pl.col("high") - pl.col("low")).otherwise(
            pl.max_horizontal(
                pl.col("high") - pl.col("low"),
                (pl.col("high") - prev).abs(),
                (pl.col("low") - prev).abs(),
            )
        ).alias("true_range"),
        _return_expr("bench_adj_close", by_ticker=False).alias("bench_ret"),
    ]).with_columns([
        (pl.col("ret") * pl.col("bench_ret")).ewm_mean(half_life=half_life, min_samples=min_samples, ignore_nulls=True).over("ticker").alias("ewm_xy"),
        pl.col("ret").ewm_mean(half_life=half_life, min_samples=min_samples, ignore_nulls=True).over("ticker").alias("ewm_x"),
        pl.col("bench_ret").ewm_mean(half_life=half_life, min_samples=min_samples, ignore_nulls=True).alias("ewm_y"),
        (pl.col("bench_ret") * pl.col("bench_ret")).ewm_mean(half_life=half_life, min_samples=min_samples, ignore_nulls=True).alias("ewm_yy"),
        pl.col("true_range").ewm_mean(half_life=half_life, min_samples=min_samples, ignore_nulls=True).over("ticker").alias("ewm_atr"),
    ]).with_columns([
        (pl.col("ewm_xy") - pl.col("ewm_x") * pl.col("ewm_y")).alias("ewm_cov"),
        (pl.col("ewm_yy") - pl.col("ewm_y") * pl.col("ewm_y")).alias("ewm_var_market"),
    ]).with_columns([
        _safe_div(pl.col("ewm_cov"), pl.col("ewm_var_market")).alias("dynamic_beta"),
        pl.col("ewm_atr").shift(1).over("ticker").rolling_quantile(
            quantile=volatility_quantile,
            window_size=volatility_window,
            min_samples=min_samples,
            interpolation="linear",
        ).over("ticker").alias("atr_threshold"),
    ]).with_columns([
        (pl.col("ret") - pl.col("dynamic_beta") * pl.col("bench_ret")).alias("residual_ret"),
    ]).with_columns([
        pl.when(pl.col("ewm_atr") > pl.col("atr_threshold")).then(pl.col("residual_ret")).otherwise(None).alias("clean_residual_ret"),
    ])
    return q.select([
        "date", "ticker", "ret", "bench_ret", "dynamic_beta", "ewm_atr",
        "atr_threshold", "residual_ret", "clean_residual_ret",
    ]).collect()


def analyze_foreign_intent(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    ewm_half_life: float = 20.0,
    spot_window: int = 3,
    oi_z_threshold: float = 1.5,
    spot_sell_threshold: float = -100.0,
) -> pl.DataFrame:
    """Classify hedging vs active shorting from spot and futures OI signals."""

    required = {"date", "spot_net_buy", "futures_net_oi"}
    _require_columns(df, required)
    if ewm_half_life <= 0 or spot_window < 2:
        raise ValueError("invalid ewm_half_life or spot_window")
    q = _as_lazy(df).sort("date").with_columns([
        pl.col("spot_net_buy").rolling_sum(window_size=spot_window, min_samples=spot_window).alias("spot_net_buy_window"),
        _ewm_mean(pl.col("futures_net_oi"), ewm_half_life).alias("oi_ewm_mean"),
        _ewm_std(pl.col("futures_net_oi"), ewm_half_life).alias("oi_ewm_std"),
    ]).with_columns([
        _safe_div(pl.col("futures_net_oi") - pl.col("oi_ewm_mean"), pl.col("oi_ewm_std")).alias("oi_z_score"),
    ]).with_columns([
        pl.when((pl.col("oi_z_score") < -oi_z_threshold) & (pl.col("spot_net_buy_window") <= spot_sell_threshold))
        .then(pl.lit("active_shorting"))
        .when((pl.col("oi_z_score") < -oi_z_threshold) & (pl.col("spot_net_buy_window") > 0))
        .then(pl.lit("pure_hedging"))
        .when(pl.col("oi_z_score") > oi_z_threshold)
        .then(pl.lit("short_covering"))
        .otherwise(pl.lit("neutral"))
        .alias("foreign_intent_signal"),
    ])
    return q.select([
        "date", "spot_net_buy", "spot_net_buy_window", "futures_net_oi",
        "oi_ewm_mean", "oi_ewm_std", "oi_z_score", "foreign_intent_signal",
    ]).collect()


def calculate_real_capital_flows(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    shares_per_lot: int = 1000,
) -> pl.DataFrame:
    """Convert institutional and margin lots into adjusted-price proxies.

    The analysis contract is strict: ``adj_close`` is the only price input and
    ``non_day_trade_turnover`` is the only turnover denominator. Raw close,
    raw turnover, and a second volume series are rejected at the boundary.
    """

    required = {
        "date", "ticker", "adj_close", "non_day_trade_turnover",
        "foreign_net_shares", "trust_net_shares", "margin_change_shares",
    }
    _require_columns(df, required)
    if shares_per_lot <= 0:
        raise ValueError("shares_per_lot must be positive")
    q = _as_lazy(df).with_columns([
        (pl.col("foreign_net_shares") * shares_per_lot * pl.col("adj_close")).alias("foreign_net_amount"),
        (pl.col("trust_net_shares") * shares_per_lot * pl.col("adj_close")).alias("trust_net_amount"),
        (pl.col("margin_change_shares") * shares_per_lot * pl.col("adj_close")).alias("margin_change_amount"),
    ]).with_columns([
        (pl.col("foreign_net_amount") + pl.col("trust_net_amount")).alias("total_institutional_amount"),
        _safe_div(
            pl.col("foreign_net_amount") + pl.col("trust_net_amount"),
            pl.col("non_day_trade_turnover"),
        ).alias("institutional_amount_ratio"),
    ])
    return q.collect()


def build_sector_index(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    weight_col: str = "non_day_trade_turnover",
    price_col: str = "adj_close",
) -> pl.DataFrame:
    """Create a daily sector price index with explicit turnover weights.

    Equal weighting is used when ``weight_col`` is absent; for market-value or
    free-float weighting, provide the relevant daily point-in-time column.
    """

    _require_columns(df, {"date", "ticker", price_col})
    from .governance import validate_governance_frame

    validate_governance_frame(df, require_price=True, require_non_day_trade_volume=False)
    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    if price_col != "adj_close":
        raise ValueError("sector index must use adj_close")
    q = _as_lazy(df).sort(["ticker", "date"]).with_columns([
        _return_expr(price_col).alias("ret"),
    ])
    if weight_col in columns:
        q = q.with_columns([
            pl.col(weight_col).sum().over("date").alias("sector_weight_total"),
            _safe_div(pl.col(weight_col), pl.col(weight_col).sum().over("date")).alias("sector_weight"),
        ])
    else:
        q = q.with_columns([
            pl.len().over("date").alias("sector_n"),
            _safe_div(pl.lit(1.0), pl.len().over("date")).alias("sector_weight"),
        ])
    return q.with_columns([
        (pl.col("ret") * pl.col("sector_weight")).sum().over("date").alias("sector_return"),
    ]).group_by("date", maintain_order=True).agg([
        pl.col("sector_return").first(),
        pl.col("sector_weight").sum().alias("weight_sum"),
    ]).sort("date").collect()


def fetch_yfinance_adjusted_prices(
    tickers: list[str],
    *,
    start: str | date | datetime,
    end: str | date | datetime,
) -> pl.DataFrame:
    """Optional I/O fallback: fetch Close and Adj Close from yfinance.

    yfinance returns pandas at the boundary. Pandas is not used by any
    calculation; the result is converted immediately to Polars. This adapter
    is for missing adjusted prices only. Official TWSE/TPEX turnover remains
    the sole turnover source.
    """

    if not tickers:
        raise ValueError("tickers must not be empty")
    try:
        import yfinance as yf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("install optional dependency yfinance to use fallback") from exc

    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=False,
        actions=False,
        progress=False,
        group_by="column",
    )
    if raw.empty:
        raise ValueError("yfinance returned no rows")
    raw = raw.reset_index()
    rows: list[pl.DataFrame] = []
    # yfinance's column layout differs for one vs many tickers and can change
    # between releases; normalize it here and nowhere else.
    for ticker in tickers:
        if hasattr(raw.columns, "levels"):
            candidates = [
                ("Date", ""), ("Close", ticker), ("Adj Close", ticker)
            ]
            if all(c in raw.columns for c in candidates):
                part = raw.select(list(candidates))
                part.columns = ["date", "close", "adj_close"]
            else:
                part = raw.select([("Date", ""), ("Close", ticker), ("Adj Close", ticker)])
                part.columns = ["date", "close", "adj_close"]
        else:
            part = raw.select(["Date", "Close", "Adj Close"])
            part.columns = ["date", "close", "adj_close"]
        rows.append(pl.from_pandas(part).with_columns(pl.lit(ticker).alias("ticker")))
    return pl.concat(rows, how="vertical").select(["date", "ticker", "close", "adj_close"])


__all__ = [
    "EngineConfig",
    "SUPPORTED_WINDOWS",
    "add_returns",
    "analyze_foreign_intent",
    "build_residual_returns",
    "build_sector_index",
    "build_toca",
    "calculate_real_capital_flows",
    "fetch_yfinance_adjusted_prices",
    "load_data",
    "rolling_beta_corr",
    "technical_indicators",
    "validate_input_schema",
]
