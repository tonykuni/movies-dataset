# VDF Fetch Matrix
_Schema version: 3.0.0_  
_Build date: 2026-05-26_

## Global Settings

| Setting | Value |
|---|---|
| `default_start_date` | `2010-01-01` |
| `default_end_date` | `TODAY` |
| `fred_api_key_default` | `2d5ae8dfe834ffc409bf98d51f539c17` |
| `fred_api_key_env` | `VDF_FRED_API_KEY` |
| `yfinance_auto_adjust` | `False` |
| `throttle_ms` | `{'yfinance': 150, 'twse': 300, 'tpex': 400, 'mops': 500, 'fred': 300, 'akshare': 500}` |
| `retry_max` | `3` |
| `retry_backoff_sec` | `1.5` |

## Unified Headers

### prices_core
`Date` | `Ticker` | `YFinance_Ticker` | `Bloomberg_Ticker` | `Name` | `Open` | `Low` | `High` | `Close` | `Adj_Open` | `Adj_Low` | `Adj_High` | `Adj_Close` | `Volume` | `Turnover` | `Market_Cap`

### tw_chip_extension
`FI_Buy` | `FI_Sell` | `FI_Net` | `IT_Buy` | `IT_Sell` | `IT_Net` | `Dealer_Buy` | `Dealer_Sell` | `Dealer_Net` | `Total_Net` | `FI_Hold_Pct` | `IT_Hold_Pct` | `Dealer_Hold_Pct` | `Margin_Buy` | `Margin_Sell` | `Margin_Balance` | `Margin_Offset` | `Short_Buy` | `Short_Sell` | `Short_Balance` | `Margin_Maintenance_Pct` | `Short_Margin_Ratio_Pct` | `DayTrade_Buy_Vol` | `DayTrade_Sell_Vol` | `DayTrade_Volume` | `DayTrade_Amount` | `DayTrade_Ratio_Pct`

### tw_financial
`Date` | `Ticker` | `Period` | `Period_Type` | `Revenue` | `Gross_Profit` | `Operating_Income` | `Net_Income` | `EPS` | `Total_Assets` | `Total_Liabilities` | `Equity` | `Operating_CF` | `Investing_CF` | `Financing_CF` | `Free_CF` | `ROE` | `ROA` | `Gross_Margin` | `Operating_Margin` | `Net_Margin` | `Debt_To_Equity` | `Source`

### macro
`Date` | `Series_Id` | `Series_Name` | `Value` | `Unit` | `Source` | `Region` | `Category`

## Categories

| ID | Name (中文) | Sources | # Items | Output | Frequency |
|---|---|---|---|---|---|
| `tw_stock` | 台灣股票每日交易及籌碼資訊 | `YFINANCE / TWSE / TPEX` | 0 | `VDF_TWStock_Unified.parquet` | daily_after_close |
| `tw_index` | 台灣股票指數每日交易及籌碼資訊 | `TWSE / TPEX` | 2 | `VDF_TWIndex_Unified.parquet` | daily_after_close |
| `tw_etf_passive` | 台灣 ETF - 被動式 (追蹤指數) | `YFINANCE` | 12 | `VDF_TWETF_Passive.parquet` | daily_after_close |
| `tw_etf_active` | 台灣 ETF - 主動式 (經理人選股) | `YFINANCE` | 18 | `VDF_TWETF_Active.parquet` | daily_after_close |
| `intl_stock` | 國際股票每日交易資訊 | `YFINANCE` | 20 | `VDF_Intl_Stock.parquet` | daily_after_close |
| `intl_index` | 國際股票指數交易資訊 | `YFINANCE` | 15 | `VDF_Intl_Index.parquet` | daily_after_close |
| `tw_financials` | 台灣及國際股票財報資訊 | `MOPS / YFINANCE` | 6 | `VDF_Stock_Financials.parquet` | quarterly |
| `commodity` | 大宗商品 - 期貨 + 現貨 | `YFINANCE / AKSHARE` | 15 | `VDF_Commodity.parquet` | daily_after_close |
| `fx` | 外匯 | `YFINANCE` | 10 | `VDF_FX.parquet` | daily_after_close |
| `macro` | 總體經濟指標 | `FRED` | 29 | `VDF_Macro_FRED.parquet` | varies |
| `sentiment` | 市場情緒指標 | `YFINANCE / FRED` | 8 | `VDF_Sentiment.parquet` | daily |
| `shipping` | 航運指數 | `AKSHARE` | 3 | `VDF_Shipping.parquet` | weekly_daily |
