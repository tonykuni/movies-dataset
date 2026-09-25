# 主動台股 ETF：申贖、成分活動與期間均價接口

承接已合併的 PR #122／#123。新增 `functional modules/VDF/engine/VDF_ENG094_ActiveETFActivity_v0100.py`，由 VCGC 正主掃描註冊；純離線計算、先查庫、沿用正式 `ActiveTWETF.duckdb`。沒有新造第四本正式庫，也沒有把舊 Yahoo 擷取日改當基金淨值日。

**完成的是分析接口與唯一模板的 add-on；官方資料正規化接線及工作站正式資料驗收仍未完成。** 目前沒有把這個未取得正式來源輸入的接口接成每日完成標記的成功步驟。`production_ready` 保持 false；計算得到 `ESTIMATE` 也不是正式啟用證明。既有 ENG077 名冊、ENG078 持股、ENG055 快照保留其資料所有權。

## 分開計算的量

| 量 | 算法／狀態 | 必要輸入 |
|---|---|---|
| 基金淨申贖金額估計 | `(本期單位數 − 前期單位數 × 單位調整因子) × 本期 NAV` | 同期 AUM、NAV、受益權單位；一致幣別、資料日、來源與抓取時點；分割／合併已核對 |
| 成分淨持股變化 | `本期持股 − 前期持股 × 股票數量調整因子` | 完整的前後持股快照，股數單位已正規化；未持有才能當 0，漏表不能當清倉 |
| 成分資金變化估計 | 上列淨股數 × 區間 VWAP 或明示的收盤價代理 | 區間、幣別、資料日及價格來源一致；區間覆蓋已核對 |
| 期間淨增持／淨減持推估均價 | 分別以正／負淨股數加權價格代理 | 區間不重疊、無缺口、相鄰快照股數一致、價格完整；跨分割期間先列待正規化，不混不同股數基礎求均價 |

單位差只能辨認淨申贖，不能還原期間申購與買回總額；持股差含實物移轉與其他因素，不能唯一還原實際買賣。`gross_subscriptions`、`gross_redemptions`、`actual_trade_cost`、`actual_trade_proceeds` 保持 NULL。缺資料、未核公司行動、來源／時間／單位衝突回 REVIEW，均價不以 0 填補。

原始制度來源：證交所 [ETF 申購買回機制](https://www.twse.com.tw/zh/products/securities/etf/overview/issuing.html) 說明現金及實物申贖；[主動式交易所交易基金](https://www.twse.com.tw/zh/products/securities/etf/products/active-list.html) 說明投資組合揭露與 A／D 類型。這些是方法與來源契約的依據，不是本輪已抓得正式流量資料的證據。

## 資料庫契約與節省方式

| 表／產物 | 鍵 | 用途 |
|---|---|---|
| 既有 `holdings_daily`、`fetch_status`、`active_tw_etf_registry` | 由各正主持有 | plan 唯讀檢查列數與欄位，不改原表 |
| `etf_activity_inputs` | `input_sha256` | 保存正規化來源區間 JSON 與 `ingested_at_utc`，相同輸入去重 |
| `etf_activity_results` | `input_sha256 + engine_version` | 結果 JSON 與 `computed_at_utc`；同雜湊／同引擎直接用快取，來源修訂保留舊版 |
| `ETF_ACTIVITY.json` | 本次區間視圖 | 來源、缺項、估算法、原始数量、摘要及正式啟用狀態 |

去重落庫交 SUP_MDL753 `upsert_select`，輸入／結果同一個交易提交，結果失敗時輸入一併回滾。同區間有不同來源版本，必須有不同且含時區的 `source_revision_at` 才能選新版；不能用雜湊排序或抓取順序猜。`as_of`、`fetched_at_utc`、`ingested_at_utc`、`computed_at_utc` 分開，後兩者加入 SSOT 的 record_only。

`plan` 不寫庫；正式庫缺席回 `FORMAL_DATABASE_ABSENT`，`--apply` 不會在錯路徑建空庫。引擎零網路、零 LLM 呼叫。現版會讀取已保存的正規化區間及快取結果，尚非大量持股明細的串流查詢器；原始持股與行情仍由各正主增量擷取。

## 正規化輸入與操作

來源正規化器應產出 `schema: VIA.ETFActivityInput.v1`，包含：

- `etf_ticker`（五碼數字＋A）、`currency: TWD`、ISO `start/end`。
- `fund_previous/current`：`as_of/aum/nav/units/currency/source_url/fetched_at_utc`。
- `holdings_previous/current`：`as_of/complete/currency/source_url/fetched_at_utc/positions[{code,shares}]`。
- `fund_adjustment` 與每一成分的 `holding_adjustments`：`state: VERIFIED`、`factor/start/end/as_of/source_url/fetched_at_utc`。因子 1 也須有已核區間依據，不能因資料缺席就預設沒有公司行動。
- 各成分 `prices`：`price/method/start/end/as_of/currency/coverage_complete/source_url/fetched_at_utc`；method 只認 `INTERVAL_VWAP` 或 `END_CLOSE_PROXY`。
- 同區間來源修訂使用 `source_revision_at`。來源 URL 與上述旗標是生產者交接契約，**引擎沒有連網核證 URL 內容**；正式接線前必須核對生產者。

執行於有 VDF 依賴的 Python 環境，取 glob 尾版：

```text
python "functional modules/VDF/engine/VDF_ENG094_ActiveETFActivity_v0100.py" plan
python "functional modules/VDF/engine/VDF_ENG094_ActiveETFActivity_v0100.py" build --input verified_intervals.json --db <既有 ActiveTWETF.duckdb> --apply --out <報告夾>
```

`build` 不帶 `--input` 時，讀該庫已收容的區間。`--apply` 才存結果；不帶即乾跑。回碼 0 表示來源區間可估計，2 表示 NODATA／REVIEW。**未有已驗的官方正規化器時，先用 plan 查缺，不把合成夾具當正式進件。**

## 唯一 UI 與驗證

輸出從 `VIA_HTML_UI` 取三支正式頁，先委派 ENG090 → CGC_MDL160 驗正典套件；只在中央頁插入 `VIA_REGISTER_ADDON` 模組，不另造版面、不改正本。入口為報告夾 `ui/VIA-Complete-System.html`。所有原始來源文字以 JSON 跳脫並用 DOM textContent 呈現。

本機回歸 **20／20**：基金／成分流量分離、基金與股票分割、未知公司行動、AUM／NAV 衝突、價格區間與幣別、完整／缺漏快照、進出場、負數／重複股數、期間加權、缺口／重疊、股數不連續、跨分割均價、雜湊去重／修訂、交易回滾、缺庫不建、正典模板與 HTML 注入防護。

真 Chromium 桌機 1440 與手機 390 共 **12／12**：模組只註冊一次、來源文字不執行、估算標示可见、無頁面錯誤、無外部請求、無整頁橫捲。測試輸入全為合成，Windows CI 執行同套測試並上傳畫面，與正式資料驗收分開。
