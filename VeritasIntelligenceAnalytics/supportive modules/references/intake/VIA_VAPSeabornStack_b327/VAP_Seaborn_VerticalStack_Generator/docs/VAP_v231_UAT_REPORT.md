# VAP Seaborn v2.3.1 UAT 與除錯報告

日期：2026-09-02  
結果：通過，可封裝

## 驗收摘要

- 完整自動化回歸：`155 passed`、`0 failed`、`3 skipped`。
- 正式 demo：5 張邏輯圖、6 個實體 panel，成功輸出自包含 HTML、300 DPI PNG、單頁向量 PDF、SVG、report 與 audit。
- 50,000 列壓力測試：CSV discovery、欄位投影、讀取上限、日期排序／去重、價格補值與 Volume 不補值皆通過。
- 大資料 renderer：line／area／step 使用多序列首尾與極值包絡；candlestick 使用連續桶 OHLCV 聚合；輸入／輸出點數、方法與警告均寫入 audit。
- 併發測試：12 路 config append 與 12 路 gallery append 均完整保存，無 JSON 損毀或遺失提交。
- Headless 使用流程：來源辨識 → auto-config → 目前表單／單圖輸出 → 存入圖庫 → 加入／複製／重排／刪除堆疊 → 圖組輸出，全流程通過。
- 封裝驗證：ZIP 完整性檢查通過；解壓到全新暫存目錄後再次執行 155 項測試，結果相同。

## 已修正的實際缺陷

| 類別 | 問題 | v2.3.1 修正 |
| --- | --- | --- |
| 刻度 | 小數 offset 被顯示成整數，或因二進位浮點產生 8 位雜訊 | 統一計算 tick 精度並保留必要尾零，例如 `1.25`、`2.50` |
| K 線 | render-one 曾關閉 K 線／Volume shared X；0.25 高度被最低值夾成 0.35 | 保留共享 X；實體列精確維持 75%／25% |
| 單軸 | `axis_mode=single` 仍可能殘留右軸欄位，導致 HTML 找不到欄位 | UI、資料投影與 Plotly 三層均忽略／清除無效右軸 |
| 樣式 | 右軸無獨立線寬與透明度 | 新增 `secondary_line_width`、`secondary_alpha` 並貫通 UI、CLI、靜態與 HTML renderer |
| UI | 切換 config 後可能保留舊來源；async 結果可能寫入新專案；queue callback 例外後停止輪詢 | 切換時清空來源 context；worker 帶 context token；poll 永遠在 `finally` 重排 |
| UI | defaults 頁被裁切、目前表單不能先預覽、HTML-only 輸出無法開啟 | defaults 頁加入捲動；新增目前表單預覽；依 HTML／PNG／SVG／PDF 順序開啟既有輸出 |
| 編輯 | 覆寫圖表會重設 UI 未顯示的 `axis_zero_policy`、`bar_gap_ratio` 等欄位 | 覆寫只更新 form-owned keys；新增圖才建立完整 defaults |
| 圖庫 | 預設圖庫路徑錯誤；可能嵌入 records、數值陣列、URL 密鑰或 root metadata 資料 | 圖庫跟隨 config；限制 data-free schema、大小並全面遮蔽 secret |
| 併發 | 多個程序同時 read-modify-write 會遺失資料；失敗可能留下大型 temp | 跨程序 transaction lock、唯一暫存檔、fsync／replace 與失敗清理 |
| 資料來源 | SQLite 路徑含 `#`／`?`、semicolon CSV、Parquet dataset traversal、SQL 欄位投影等邊界錯誤 | URI encode、delimiter sniff、root containment、selected-column projection 與 bounded Parquet read |
| Manifest | 曾可能保存 sample values、明文 query、ODBC／URL secret | 移除樣本與 query，遮蔽密碼、token、private key、fragment 等內容 |
| Windows | BOM-less PowerShell 5.1 中文解碼、舊 venv 無聲失敗、絕對輸出目錄與非 PNG 開啟 | UTF-8 BOM、優先 pwsh、完整 venv 健康檢查、格式與 rooted path 支援 |
| 效能 | 10,000+ 點自包含 HTML 與 Matplotlib artist 快速膨脹 | 新增預設 `render_max_points=5000`、可在全域／單圖修改並提供可稽核縮減 |

## 輸出契約實測

| 項目 | 結果 |
| --- | --- |
| PNG | `4720 × 4905`、約 `300 DPI`，可由 Pillow 讀取 |
| PDF | PDF 1.4、1 頁、非空、無 JavaScript，可由 `pdfinfo` 解析 |
| SVG | 合法 SVG 文件 |
| HTML | 自包含 Plotly、無 CDN、共享 X、unified hover、normalized series 可由圖例勾選 |
| 軸 | 各軸 5 ticks／4 intervals；範圍包住資料；nice step 契約通過 |
| K 線／量 | 紅漲綠跌、Volume 同色、價格可 ffill、Volume 不補值、上下兩個單軸 |
| 報告 | 版本、完整列數、實際渲染列數、資料品質與 render optimization 均可追溯 |

## 明確跳過與使用邊界

本次 Linux runner 未安裝 `pyarrow/fastparquet`，因此兩個要求真實 Parquet 引擎的額外 UAT 被跳過；套件的 `requirements.txt` 已固定安裝 `pyarrow`，現有 Parquet 偵測／投影的 mock 與相容回歸仍通過。Linux runner 也未安裝 PowerShell 7，因此一個實際 parser 測試跳過；PowerShell／CMD 的 12 個靜態與行為契約測試均通過。

遠端 SQL 文字檢查不是資料庫權限邊界。實際連線必須使用只具 `SELECT` 權限的專用帳號，並由資料庫端設定 timeout／resource limit。這項要求已加入 README 與資料庫文件。
