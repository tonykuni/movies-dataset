# 資料庫與檔案來源範例

## DuckDB

```json
{
  "kind": "duckdb",
  "path": "C:\\Data\\tw_market.duckdb",
  "table": "tw_prices_adj"
}
```

## SQLite

```json
{
  "kind": "sqlite",
  "path": "C:\\Data\\tw_market.sqlite",
  "table": "prices"
}
```

## 無副檔名 Parquet

```json
{
  "kind": "parquet",
  "path": "C:\\Users\\tonyk\\OneDrive\\桌面\\tw_stock\\StockData.parquet"
}
```

若檔案真的沒有副檔名，v2.2 會先讀取檔頭：`PAR1` 判定為 Parquet；可保留 `kind = parquet` 作為明確覆寫。

## Adjusted OHLCV（Candlestick + Volume）

資料表若提供以下欄位，Discovery 會優先建議 `candlestick_volume`：

```text
Date, Adj Open, Adj High, Adj Low, Adj Close, Volume
```

`Adj Open`／`Adj High`／`Adj Low`／`Adj Close` 必須已由資料源完成價格調整；生成器不從 raw OHLC 重算 adjusted price。預設 K 線為台股慣例紅漲綠跌，Volume 柱沿用每根 K 線顏色。`missing = ffill` 時只向前延續價格缺值，Volume 永不補值。

若欄名不同，可在 `charts[]` 明確對應：

```json
{
  "id": "tw_ohlcv",
  "type": "candlestick",
  "axis_mode": "single",
  "x": "trade_time",
  "open": "adjusted_open",
  "high": "adjusted_high",
  "low": "adjusted_low",
  "close": "adjusted_close",
  "volume": "shares_traded",
  "missing": "ffill",
  "up_color": "#D62728",
  "down_color": "#2CA02C"
}
```

## 無副檔名 CSV／TSV

```json
{
  "kind": "auto",
  "path": "C:\\Data\\daily_prices"
}
```

存在的無副檔名文字檔會依 UTF-8／CP950 與 delimiter 自動判定 CSV 或 TSV。

## Parquet 資料夾

```json
{
  "kind": "parquet_dataset",
  "path": "C:\\Data\\daily_prices",
  "table": "2026.parquet"
}
```

## Excel Sheet

```json
{
  "kind": "excel",
  "path": "C:\\Data\\control_sheet.xlsx",
  "sheet": "Daily"
}
```

## SQL Server

先安裝：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-database-optional.txt
```

SQL Server 另需由 Microsoft 安裝 **ODBC Driver 18 for SQL Server**；Python 套件不會代為安裝系統驅動。

連線字串範例：

```text
mssql+pyodbc://USER:PASSWORD@SERVER/DATABASE?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

## PostgreSQL

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

## MySQL

```text
mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE
```

遠端資料庫驅動屬選配。SQLite、CSV、Excel、JSON 可使用標準／核心套件；Parquet 與 DuckDB 由主 requirements 安裝。

Discovery manifest 會在來源允許時保留資料庫 declared type、nullable、primary key 與 index；不保存 sample values、明文 query、URL 密碼、token 或 secret。所有 SQL 只允許單一 `SELECT`／`WITH`，並拒絕寫入型關鍵字。

文字層檢查不是資料庫權限邊界。連接 PostgreSQL、MySQL、SQL Server、Oracle 等遠端來源時，請務必使用只具 `SELECT` 權限的專用帳號，並由資料庫端設定 query timeout／resource limit；不要在 URL、query 或自訂 metadata 內保存長期憑證。完整規格與所有可調參數請看 [`VAP_v22_PARAMETER_REFERENCE.md`](VAP_v22_PARAMETER_REFERENCE.md)。
