# VCGC 每日資料鏈：實查、修正與啟用邊界

操作員 2026-09-25 要求：全台股、全主動台股 ETF、持股/AUM/流量/估計成本、月營收、FactSet/Yahoo 共識、全球指數商品與原始來源；擷取前先看庫，增量去重補缺。承接 PR #122（main `2333185c`）已驗過的唯一 HTML 模板與 VRN 修正。以下程式變更均在隔離庫／假網路驗證，正式庫缺席，**尚未實證工作站全資料日更成功**。

## 現況對表

| 項目 | 正主／現有機制 | 本輪修正與仍須驗證 |
|---|---|---|
| 每日入口 | `via_boot_update.sh`／`.ps1`；開啟系統時每日首跑，並非 24 小時常駐排程 | 臺北日期；互斥鎖獨立；子步非零不寫完成標記，同日可重試；舊 marker 不當成功證據。異常斷電遺留鎖須先核對工作站行程，不能直接刪活鎖 |
| 抓前查庫 | CGC_MDL123 catalog → ENG089 plan --deep → 各正主水位 | 雙入口已接線；查庫／計畫失敗即停。未知路徑、讀鎖或缺庫不當空庫重抓；沒有改啟動器的既有常令同意設定 |
| 台股清單 | ENG055 L1：TWSE/TPEX 公司冊；ENG081、CGC_MDL142 核對 | 兩所清單已有每日車道；新共識／月營收讀 `tw_listings` 與官方 `tw_listings_industry`。**不冒稱已驗過興櫃、下市狀態、全市場筆數與正式庫當日新鮮度** |
| 主動式 ETF 清單 | ENG077、官方 t187ap47_L；ENG051 CSV、ENG078 持股史 | v0101 先讀庫再抓；有官方回包才更新 last_seen；後備回 rc2。原本「既有∪新名單」永遠不會發現消失者，改以本次官方回包核對；歷史保留、缺席標記、當日 CSV 排除。既有名單改讀每基金一列主檔，不掃歷史全表 |
| 主動 ETF 持股 | ENG078 v0110：上市日起缺口與來源日期硬閘 | 已在雙入口；仍需工作站正式庫逐 ETF×交易日確認完整性，不能用有入口代替持股已齐 |
| ETF AUM／申贖／成分資金流 | ENG055 L5 `etf_stats_daily` 有 AUM/NAV 快照及 flow_est 計算 | **現況缺口**：flow_est 只計算可算筆數，未完整落成申贖／成分流量／估計買賣均價資料集；Yahoo AUM/NAV 是否同一期也未證實。不宣告此需求已完成 |
| 月營收 | ENG063 官方 MOPS 雙所＋ENG075 歷史回補 | v0107 全名冊核對、期別期限委派 SUP_MDL753；先讀庫、同日已核取免重抓；缺碼／逾期／來源失敗 rc2。預設不逐股盲探商用候選端點；視圖每碼每月選一筆，官方優先，避免跨源雙算 |
| FactSet／Yahoo 共識 | ENG069／070／071，`consensus_daily` 與既有 ADJ 旁表 | 原預設只有三檔、Yahoo 一律 .TW；已改全正式雙所名冊與 .TW/.TWO／TWS/TWO。新增 `consensus_observations` 保存完整回包、原始來源日期、UTC 抓取時間、雜湊與狀態。成功/明確無覆蓋當天免重抓，傳輸或不完整回包可重試。來源無時間留 NULL，不冒充最新 |
| 共識期別與價格 | 既有 ENG069 → ENG073 ADJ 正典 | 鉅亨 runtime 依快照年對齊當年/次年，缺次年不拿 2029 假充；全年度原文仍保存。Yahoo 價格只取所屬交易所且不晚於快照日。⑦f 抓完兩源後由 ENG069 再建 ADJ；未知財政年度／來源生效時點仍須覆核 |
| 全球指數／商品／期現貨／ETF | ENG055 L6、ENG066、VIA_Global_Universe；L7 ETF 代理估值 | v0118 修掉永久 done 導致不再日更；改庫水位＋7 日補缺並聯集正典標的冊，保存 Yahoo 端點與 UTC 抓取時間。冊上候源類及缺載逐項回 PARTIAL；**內部歷史洞、既有值修訂、期貨轉倉、期現貨對應與全指數估值尚未全部驗證**；PROXY_ETF 不等於指數自身 P/E |
| 總經原始來源 | ENG074 FRED registry 已存 src/freq/unit/theme；另 CBC、Eurostat 等道 | 存量來源有冊可查，但尚未逐觀測值證實發布時間／修订批次／原始发布机构完整。FRED/Yahoo 是配送商時，仍需原始機構欄，不能混為一個 source |

## 共用資料框架

保留現有正式 DuckDB 及各領域表，不另造一份正式大庫。共同契約為：

`entity_id + market + instrument_type + metric + observation_period + provider_asof + fetched_at_utc + source/provider + source_url + currency/unit/scale + value + revision/content_hash + quality_state`。

1. **主檔**：股票／ETF／指數／商品分開 instrument_type；上市、上櫃與其他市場分開；名冊觀測日與生效日分開。歷史不刪，來源消失先列待核。
2. **事實表**：行情以日期×標的，持股以 ETF×持股日×成分，月營收以公司×年月×來源，預測以公司×指標×財政期間×来源×版本；來源優先選擇由視圖處理，原文保留。
3. **來源旁表**：本輪實作的 `consensus_observations` 包含 snapshot_date/code/source/symbol/source_urls/provider_asof_raw/fetched_at_utc/content_sha256/payload_json/state。舊 `consensus_daily` 14 欄不加欄，避免破壞其他寫入者。完整 JSON 保存未映射欄位，後續解析不必重打 API 或重耗模型 token。
   Yahoo 請求 financialData、earningsTrend、earningsHistory、recommendationTrend、upgradeDowngradeHistory、defaultKeyStatistics（本環境 yfinance 1.7.0 的可用模組冊包含這六種）；實際覆蓋仍以來源回包為準。鉅亨端保存 targetPrice 與 estimateProfit 全欄，不代表取得 FactSet 的付費直連授權或其全部產品。
4. **水位與覆蓋**：先讀目錄与實庫水位，按標的/來源/期別補缺；寫入去重委派 SUP_MDL753。整天 marker 只表示子步完成，資料是否齊由 coverage 和 source state 判斷。EMPTY、ERROR、NODATA、未知源時點均不得當有效零值。
5. **模型使用**：資料擷取、欄位映射、雜湊、去重、期別核對以引擎完成；只有修復後文本／歧義需要 NLP。共識原始 JSON、月營收、行情與名冊不逐列送模型。

## ETF 流量與估計成本的必要條件

還需要官方或投信的同一期 NAV、AUM、流通受益權單位與申贖資料，以及前後持股完整快照、股票交易價格、分割／配股／換股事件。AUM 變化包含價格效果；基金申贖與成分股買賣是不同量。

若只能用持股淨變化與同期 VWAP 等價格估計，欄位必須標 `ESTIMATE_FROM_NET_CHANGE`，帶估算區間、價格代理來源及假設。日內買賣相抵、現金部位、實物申贖、費用與公司行動不能從淨持股變化唯一還原；缺任一必要輸入時回 NULL/REVIEW。實際平均買入成本／售價必須有交易明細或可核的官方披露，不用估計值冒充。

## VCGC 與 VRN 啟用範圍

VCGC 為版本、註冊、政策、資料狀態與操作入口的中央控管；VDF/VRN 正主處理領域邏輯，唯一 VIA_HTML_UI 沿用。新來源不另起其他 HD 頁面。

**個股先啟用，非個股第二線仍未開通。** 非個股先保存 DATE/FILENAME/BROKER 與證據；個股/VDF 完成後才接文字修復→NLP→依主題及證據密度自調摘要。混合報告逐段保留多公司／總經主題；Evernote 只有連結時標 LINK_ONLY，不產生未讀內容摘要。細節見 `VIA_NonStock_Database_Framework_20260925.md`。

## 已驗與未驗

本機新增回歸共 37 項：雙載體 12、共識 12、月營收 6、全球水位 4、ETF 名冊 3；全部只用暫存資料庫和假網路。另跑各尾版自測及 VCGC/VDF/六層冊契約；最終結果及 GitHub head 由 PR 補記。Windows CI 也執行這些測試，其中 POSIX 六案明示略過，PowerShell 六案原生實跑；POSIX 已在本機 Linux 實跑。

容器沒有正式三庫、無法操作本機 Windows 排程、未持有完整正式流量與交易資料。因此這輪能交付的是可驗收的日更修正與已知缺口，**不是全市場所有資料已更新完成的聲明**。工作站驗收須提供可讀的正式庫／副本及正式網路環境，再經 VCGC 的 status/catalog/增量計畫與真跑結果核對；不因授權完整就編造資料或跳過缺口。

### PR #123 驗證存證

初次送審 head `9dc585ec60a55e2aa9df74a2110a69408981b144` 的 Windows bundled Chromium UAT 已通過（run 36084483686／job 107913191702），包含日更契約、桌機／手機、VRN 空庫／有合成資料及同步編輯測試。

同一棵樹全格子 v0496 完整跑 361 站：**OK 339／FAIL 13／SKIP 9／TIMEOUT 0**，333 秒。12 個紅站名稱與先前交接存證一致；本次新增的一紅是五支新測試缺少 L102 加速器橋。已由正典工作橋補齊，未改豁免或基線；守門複驗 Python 缺 0、PowerShell 基線外新增缺 0，37 項日更回歸再次全過。這是「原全格子＋修後定點複驗」，不把原 13 紅改寫成另一個未實跑的全格子結果。

VCGC 38 檢、VDF 管理器 31 檢、OmniFetch 16 檢、月營收 10 檢均通過。三本正式庫在此環境前後均缺席；此項只证明未建立／寫入正式庫，不代表正式資料內容驗收。精簡機器存證見 `VIA_DailyData_Evidence_20260925.json`；後續 GitHub head 的 CI 結果以 PR #123 Checks 為準。
