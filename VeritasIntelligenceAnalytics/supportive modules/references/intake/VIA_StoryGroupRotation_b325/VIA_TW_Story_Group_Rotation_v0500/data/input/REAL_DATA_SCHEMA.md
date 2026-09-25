# v0.5 真實資料契約

本引擎只讀取本機、可追溯的 point-in-time（PIT）資料，不會自行抓網路資料，也不會用推估值補正式結論。正式執行前會把主線必要資料與選配參考資料分開檢查：主線缺檔、缺市場、時間戳未知或資料不完整時，採 `BLOCKED`／`HOLD`；月營收缺少只代表沒有事後基本面參考，不得阻擋主引擎。

## 共通規則

- 股票代碼使用 `2330.TW`（TWSE）或 `6488.TWO`（TPEX）；需要聚合廣度時，以去尾碼後的唯一代碼去重。
- 日期是台灣交易日；無時區的 `ApprovedAt`／`RecordedAt`／`KnownAt`／`AvailableAt`／`IngestedAt` 一律解讀為 `Asia/Taipei`，引擎內部轉為 UTC 比較。
- `AvailableAt` 表示該資料實際可被模型知道的時間，不可用資料所屬日、抓取日或檔案修改時間倒填。
- 價格、成交值、法人、融資券與 ETF 持股不可 forward-fill；若選配月營收存在，也不得 forward-fill。
- 回測的訊號最早於所有必要證據均可得之後的下一個交易日生效；交易日曆必須包含 as-of 日之後至少一個交易日。
- 有指定 `as-of` 時，統一 snapshot 是不晚於該日的最近正式交易日；週末或休市日會映射到前一 session。`full_market_daily` 若缺該目標 session 必須阻擋，不得退回更舊行情。未指定 `as-of` 時才使用最新完整 session。所有帶 `Date` 的輸出先截到同一 snapshot，後續模組不得各自選截面。歷史資料契約一律先做 as-of 截點，再驗證截面內的逐列 lineage 與 coverage；截點後才追加的列不得使既有歷史截面失敗或改變。
- `evidence_cutoff_at` 必須不早於 snapshot 當日最新 `MarketDataAvailableAt`，且其 Asia/Taipei 本地日期不可晚於 snapshot；它可以納入同日較晚公布的證據，但不得納入次日資料。

## 正式 runner 主線必要檔案

`run_system.py preflight-real` 必須找到下列六個主線輸入：

1. `full_market_daily`
2. `universe_history`
3. `trading_calendar`
4. `membership_events`
5. `macro_vintages`
6. `active_etf_holdings`

`candidate_story_membership` 另作候選 cohort 檢查。`monthly_revenue` 是 `OPTIONAL_REFERENCE_ONLY`，應在 preflight 的選配區單獨顯示；缺少時不得令主線 preflight 失敗或改變 exit code。`active_etf_registry` 是可選的 append-only 名單稽核檔，目前不由正式 runner 消費；正式 runner 假設 holdings 已由上游限制為台股主動式股票 ETF。

## `trading_calendar`

主鍵：`Date`

| 欄位 | 必要 | 說明 |
|---|---:|---|
| `Date` | 是 | TWSE／TPEX 共用交易日；須包含 as-of 之後的下一交易日 |

## `market_universe_history`

正式 append-only 主鍵：`UniverseRecordId + RevisionId`。既有
`Ticker + ValidFrom` 單版本檔只保留唯讀相容性，不得用覆寫原列的方式修訂。

| 欄位 | 必要 | 說明 |
|---|---:|---|
| `Ticker` | 是 | 正典股票代碼 |
| `Market` | 是 | `TWSE`／`TPEX` |
| `AssetType` | 是 | 普通股型別，例如 `COMMON_STOCK` |
| `ValidFrom` | 是 | 納入全市場母體的起日 |
| `ValidTo` | 是 | 含首含尾；仍有效可空白 |
| `KnownAt` | 是 | 來源內容第一次可知的 PIT 時間，不得以 `ValidFrom` 倒填 |
| `UniverseRecordId` | 版本化模式是 | 同一邏輯有效區間跨修訂不變的穩定識別碼 |
| `RevisionId` | 版本化模式是 | 該 record 內不可重複的 immutable 修訂識別碼 |
| `RecordedAt` | 版本化模式是 | 此修訂實際寫入／取得時間 |
| `RevisionAction` | 版本化模式是 | `UPSERT`／`RETRACT` |
| `SourcePayloadHash` | 否 | 來源 payload 的 64 位 SHA-256 完整性雜湊；不是簽章，也不用來選版 |

版本化欄位採 all-or-none：在某一 as-of 截面內，只要任一列使用
`UniverseRecordId`、`RevisionId`、`RecordedAt`、`RevisionAction`，該截面所有列都必須完整提供四欄；不可混合無識別碼舊列與新修訂。舊格式只有在每個
`Ticker + ValidFrom` 唯一、普通股有效區間不重疊且永不覆寫時才安全相容。

每個修訂的實際知悉時間為
`UniverseEventKnownAt = max(KnownAt, RecordedAt)`。逐交易日以該日完整市場檔的最新
`MarketDataAvailableAt` 作精確 cutoff，只從
`UniverseEventKnownAt <= cutoff` 的列中，按 `UniverseRecordId` 選最後一版，再套用
`RevisionAction` 與 `ValidFrom`／`ValidTo`。同一 record 的修訂區間可以重疊，因為後版取代前版；materialize 後若不同 record 對同一普通股仍同日有效，則阻擋。相同 record 的兩個修訂若具有相同知悉時間，也因無法安全排序而阻擋。

append-only replay 先以知悉時間截斷修訂列，再驗證截面內 payload。因此晚知的修訂、晚知的新欄位或後來才入庫的 interval correction，不得改變較早 as-of 的結果；`RecordedAt` 可防止把事後取得但回填舊 `KnownAt` 的修訂倒灌進歷史。

每日 `full_market_daily` 必須與當下已知且有效的兩市普通股 roster **雙向完全一致**，且 2330 必須恰有一筆。缺少 roster 成分會阻擋；觀測檔中出現任何不在該日 PIT roster 的正典 TWSE／TPEX ticker（包含其 universe 列尚未可知）也會阻擋，不得靜默排除。因子引擎的來源母體識別為含 2330 錨點的完整兩市普通股母體；通過閘門後，2330 才從市場比較因子與逐股 rolling residual 輸出移除，並且不進入規模門檻及主要族群指數。

## `full_market_daily`

主鍵：`Date + Ticker`

### 必要量價欄位

| 欄位 | 說明 |
|---|---|
| `Date`, `Ticker` | 交易日與正典股票代碼 |
| `Adj_Close` | 還原權息收盤價；不可用 raw close 靜默替代 |
| `TurnoverValue` | 當日總成交值 |
| `DayTradeTurnover` | 當沖成交值 |
| `MarketCap` | 當日市值；有 `FreeFloatMarketCap` 時，階層指數優先使用流通市值 |
| `MarketDataAvailableAt` | 量價與市值資料可得時間 |
| `IsLimitUpLocked`, `IsLimitDownLocked` | PIT 漲跌停鎖定狀態；未知不得當作 `False` |

### 方向性資金欄位

| 數值欄 | 對應可得時間欄 |
|---|---|
| `ForeignNetAmount` | `ForeignNetAmountAvailableAt` |
| `InvestmentTrustNetAmount` | `InvestmentTrustNetAmountAvailableAt` |
| `DealerNetAmount` | `DealerNetAmountAvailableAt` |
| `MarginBalanceValue` | `MarginBalanceValueAvailableAt` |
| `ShortBalanceValue` | `ShortBalanceValueAvailableAt` |

上述五個可得時間欄是正式 runner 的必要欄。某一方向性數值可以缺漏，但該證據 lane 會維持缺值／`HOLD`；若數值存在而可得時間缺失，該數值不會進入判定。

### ETR 的正確語意

`ETR = TurnoverValue - DayTradeTurnover`

- ETR 是扣除當沖後的「非當沖成交注意力」，不是買賣方向，也不是資金淨流入。
- `DayTradeTurnover > TurnoverValue`、負值或缺值不會被截成零，而是阻擋。
- 漲停鎖定且鎖定狀態已知時，資金熱度 lane 使用 `AttentionETR = max(當日 ETR, 前一交易日 ETR)`，避免鎖死量縮被誤判為注意力撤退；`GI_ETR` 仍是獨立的 T-1 ETR 權重價格指數。
- Attention Share 的市場分母要求當日去 2330 普通股 ETR 完整覆蓋，族群分子也要求全部比較成分有值。部分／無效覆蓋時 `AttentionShare` 必須為缺值並標為 `HOLD`；不得用可見子集重正規化，也不得在該日建立任何注意力或方向性 rotation edge。

## `membership_events`

append-only 關係鍵：`GroupId + Ticker`。一股可同時屬於多個故事族群，但同群同股的有效區間不可重疊。

正式建議欄位：

`Sequence,EventId,EventType,GroupId,GroupName,Ticker,ExposureShare,ApprovalStatus,ApprovedAt,ValidFrom,ValidTo,Reason,SourceVersion,SupersedesEventId,RecordedAt,KnownAt,AvailableAt,IngestedAt,PreviousLedgerHash,LedgerHash`

- 引擎必要欄為 `EventType,GroupId,GroupName,Ticker,ApprovedAt,ValidFrom,ValidTo`；正式資料另應明確提供 `ApprovalStatus`。
- `EventType`：`ADD`／`REMOVE`／`KEEP`；`ApprovalStatus`：`PENDING`／`APPROVED`／`REJECTED`。
- 只有核准事件會被物化為歷史區間；最早於核准日之後的第一個交易日生效。
- `EventKnownAt` 由 `ApprovedAt`、`RecordedAt`、`KnownAt`、`AvailableAt`、`IngestedAt` 所有已填欄位的最大時間衍生並納入 event hash-chain 驗證；任一已填但無法解析的時間都阻擋。使用 knowledge cutoff 回放時，只可物化 `EventKnownAt <= cutoff` 的事件，即使其 `EffectiveDate` 在未來也只能作已排程狀態，不能提前套用。
- `ExposureShare` 是選配、經人工稽核的多故事資金分攤比例，值域為 `[0,1]`；它隨事件寫入 hash chain 並保留於物化歷史，`KEEP` 可在下一生效日起更新。未提供時保持缺值，交由守恆映射規則處理，不得捏造為研究結論。
- 原始 event ledger 不得直接進入指數、資金分攤或驗證；必須先物化為 PIT membership history。
- `UNRELATED` 只會形成 `REMOVE_CANDIDATE`；須人工核准後再追加 `REMOVE`，既有紀錄不覆寫、不刪除。

## `candidate_membership_v21`

設定檔聲明的 49 群、252 個多標籤占位、241 個唯一代碼，只是待驗證 cohort 的結構契約，不代表已核准成分或實證結果。

- 候選檔中的原始 L/P/G 標籤與數值只保留在來源稽核，不進入 runtime 分類或權重。
- 衝突列會被阻擋。
- 候選即使通過統計驗證，也只進入人工 review queue；未核准前 `IndexEligible = false`。

## `macro_vintages`

主鍵：`ObservationDate + AvailableAt`

必要欄：

`ObservationDate,AvailableAt,USDTWD,DXY,Taiwan10YYield,Source,SourceAuthority,SourceURL,SourcePayloadHash,YieldUnit,InstrumentId,OfficialSourceVerified`

- 只做 backward-asof；較晚公布的舊觀察日修訂不會覆蓋當下已知的較新觀察日。
- DXY 必須使用台股決策時點前已可得的資料；不可把美國當日尚未收盤數值放入台股同日訊號。
- 台灣 10 年期公債殖利率只有在 `Source` 非空、`SourceAuthority = TAIPEI_EXCHANGE_TPEX`、`SourceURL` 為 HTTPS 且實際 hostname 是 `tpex.org.tw` 或其子網域、`SourcePayloadHash` 為 64 位 SHA-256 hex、`YieldUnit = PERCENT`、`InstrumentId = TAIWAN_10Y_GOVERNMENT_BOND_YIELD` 且 `OfficialSourceVerified = true` 時，才可換算每日無風險報酬。
- `SourcePayloadHash` 只驗證為 payload 完整性 digest 的格式；它不是來源簽章，也不能單獨證明該 URL 或櫃買中心發布了內容。回測會從上述原始列證據重新建立 `RiskFreeSourceStatus`，不信任輸入檔自帶的狀態字串。
- 禁止固定無風險利率替代。來源未驗證或 PIT 覆蓋不完整時，Sharpe／Sortino 保持 `HOLD`。

## `active_etf_holding_snapshots`

主鍵：`SnapshotId + Ticker`；最少必要欄為 `ETFId,PortfolioDate,AvailableAt,Ticker`。

正式建議欄位：

`ETFId,ETFName,PortfolioDate,AvailableAt,Ticker,Shares,WeightPct,ETFUnits,NAV,AUM,Price,IsComplete,CompletenessReason,SourceType,SourceURL,SourcePayloadHash,FetchedAt,SnapshotId`

相容別名：`SnapshotComplete → IsComplete`、`Weight → WeightPct`、`ETFUnitsOutstanding → ETFUnits`、`SourceHash → SourcePayloadHash`。

- 第一份快照只能標為 `INITIAL`；不完整快照不得產生 `EXIT`。
- 只有同時具備持股股數與 ETF 流通單位，才能把持股變動拆為規模機械變動與 `ActiveQty`；否則只回報未歸因的快照變化，不宣稱經理人主動買賣。
- 主動式 ETF lane 是投信交易的子集合，不可再與投信買賣超相加。
- `STORY_FULL` 顯示所有故事曝險；`CAPITAL_CONSERVED` 優先使用物化 membership 上已稽核的 `ExposureShare`。若完全未提供則在有效故事間等分；部分已知時將剩餘比例等分給未知項；全部已知但合計小於 1 時，餘額進入 `UNMAPPED`。每筆原始資金守恆為 1。
- `AvailableAt` 決定最早可交易日；`PortfolioDate` 不等於可得時間。
- 所有正式 ETF 輸出（包括 `prepared_snapshots`、品質、最新持股、事件、基金流、共識、重疊／擁擠、故事與 2330 錨點稽核）都必須先限於 `AvailableAt <= evidence cutoff`；正規化或稽核表也不可洩漏未來 vintage。
- 完整基金持股與守恆稽核可保留 2330；正式故事事件、故事曝險與群組共識一律排除 2330，對應持股／事件／共識另列於 `active_etf_tsmc_anchor_*`，不得回流故事比較。
- 故事映射以訊號 `EffectiveDate` 的有效 PIT membership 為準；尚無生效日時才回到 evidence date。同群同股有效區間重疊、映射倍增或守恆權重不等於 1 都必須阻擋，不得靜默重複同一筆股票證據。

## `monthly_revenue_vintages`（選配、只供事後參考）

主鍵：`Ticker + ReportMonth + AvailableAt`

必要欄：`Ticker,ReportMonth,AvailableAt,Revenue`

建議欄：`RevenuePreviousYear,CumulativeRevenue,CumulativeRevenuePreviousYear,OfficialYoY,OfficialMoM,OfficialCumulativeYoY,ReportingPeriodMonths,Source,EvidenceTier`

- 同一報告月可以有多個修訂 vintage；as-of 時只選當時已知的最新版。
- `ReportingPeriodMonths != 1`（例如 1–2 月合併或多月申報）列為不可直接比較的 `HOLD`。
- 缺少整份月營收輸入、個別股票月份、可比較基期，或輸入內容／欄位無效時，不阻擋族群驗證、角色分類、指數、資金訊號或回測主線；只是不顯示相應參考。
- 月營收絕不進入族群分類、`LEAD/PEER/LAG/UNRELATED` 角色、指數、權重、布局／退場訊號或選樣，也不得改寫族群成分。
- 只有主線證據已先形成機會後，才可顯示個股與族群的 YoY、累計 YoY、季節偏離、正成長廣度與加速廣度，作為事後基本面驗證；不得反向改變原訊號或把它包裝成前置篩選條件。
- 無效月營收輸入的狀態為 `OPTIONAL_REFERENCE_INVALID_CORE_UNAFFECTED`；公司與族群參考表保持空白，錯誤型別及訊息寫入 `reference_revenue_audit`，且 `CorePipelineBlocked = false`。
- 正式 pipeline 先由 `stock_positioning_transition_latest.VerifiedPhase` 篩出 strict stage 3（穩定布局／價格回落盤整）或 stage 4（價格再啟動）的機會 ticker，之後才允許開啟月營收檔；讀入後也必須先限縮到這批 ticker，才進行欄位正規化與指標計算。公司參考表不得含非機會 ticker；族群參考表只可含這批 ticker 依 snapshot 有效 PIT membership 所連到的族群，不得輸出非機會群。
- 沒有 stage 3／4 核心機會時不開啟也不解析月營收，audit 為 `OPTIONAL_REFERENCE_WAITING_FOR_CORE_OPPORTUNITY`；即使檔案本身無效也不影響核心主線。

## 輸出契約

- 每張表同時輸出 `.csv` 與 `.parquet`；同一表名不加時間或版本尾碼。
- run 以 `data/output/RUN_YYYYMMDD_<hash>/` 隔離，包含 `manifest.json`，既有 run 不覆寫。
- CSV 日期顯示為 `YYYY/MM/DD`；Parquet 保留日期型別。
- 缺少 Parquet engine 或任一表寫入失敗時，整批阻擋並清理 staging 目錄，不降級為 CSV-only。

### 指標與參考輸出邊界

- `tsmc_anchor_daily`、`tsmc_anchor_membership` 與 `active_etf_tsmc_anchor_*` 只供 2330 獨立錨點觀察與稽核；不得回流至市場門檻、全市場同儕、四角色、故事資金比較或主要族群指數。ETF 完整基金守恆表仍保留 2330，但正式故事事件、曝險與群組共識表一律排除它。
- 正式 runner 的殘差模型網格必須**恰為** `LaggedCap`／`LaggedETR` 兩條 factor lane × 60／120／240 日三個同窗，共六組；缺少、額外或重複組合都阻擋整次正式執行。
- `rolling_residuals` 的來源 lineage schema 為 `VIA_FULL_MARKET_RESIDUAL_LINEAGE_V2`，必須逐列持久化並可跨 CSV／Parquet 保存；至少綁定 schema／engine、含 2330 錨點的來源母體、ex-2330 殘差母體、完整兩市閘門、PIT、factor lanes、windows、`ResidualLineageUniverseVersionPolicy`、`ResidualLineageUniverseKnowledgeCutoffPolicy` 與 SHA-256 lineage ID。兩個 universe policy 欄位證明來源使用 append-only record revision，並以同 session 的精確 `MarketDataAvailableAt` 限制 `UniverseEventKnownAt`；只比較本地日期的舊 V1 lineage 不得進入正式 bridge 或個股布局。`DataFrame.attrs` 只作可選的矛盾檢查，不能取代列欄位。每個日期另以 `ResidualUniverseExpectedTickerCount`、`ResidualUniverseExpectedTWSECount`、`ResidualUniverseExpectedTPEXCount` 證明 ex-2330 殘差列完整；任何分市數量不合即 fail closed。
- `stock_positioning_*` 以股票 × 60／120／240 日窗口 × 方向性 lane 為粒度。每組必須使用同窗口、具完整 TWSE + TPEX ordinary-equity ex-2330 PIT provenance 的殘差，且 factor lane、beta window、來源欄及 evidence window 必須逐列一致。provenance 缺失／錯置直接 fail closed；beta warm-up 或個別殘差缺值列保持 `HOLD`，不得以 raw stock return 回填。`stock_positioning_grid_audit` 稽核六組身分與完整性。族群驗證的 descriptor-matched null 也必須逐窗口接入同一 60／120／240 日 PIT 規模與流動性描述子，不得固定借用另一窗口。
- `index_weights` 與 transfer allocation 在 `AppliedDate=T` 使用 T 當日有效 membership，讓 ADD／REMOVE 在其有效日立即反映；但 `WeightDate`／`AllocationDate` 仍必須是上一交易日，價格、市值、ETR 與配置輸入不得取 T 日值。
- 雙 factor lane 只能用 exact agreement 形成 `stock_positioning_model_consensus`；外資、國內資金與主動式 ETF 仍分列，不互相加權。`stock_positioning_raw_consensus_story_evidence` 與 `stock_positioning_conserved_consensus_story_evidence` 分別保存完整故事與守恆映射。ETR 欄只可稱注意力，不能命名為淨流入。
- `group_flow_states` 的主鍵粒度是 `Date + GroupId + DirectionalLane`，固定以長格式分列 `FOREIGN`、`DOMESTIC_EX_FOREIGN`、`ACTIVE_ETF`。三條 lane 各自驗證群組／市場覆蓋、方向值及可得時間、注意力、價格和正式交易日曆；不得用「至少一條通過」、跨 lane `any`、投票或權重合成。某 lane 缺證據只讓該 lane `HOLD`。
- `stock_positioning_group_phase_daily` 只彙整已達模型共識的**當日階段**成分數與廣度，不可建立跨 lane 綜合分數或排名，也不能視為四階段已依序完成。
- `stock_positioning_transition_ledger` 才是嚴格四階段狀態機：股票 × 窗口 × 方向性 lane 各自獨立，只接受 cutoff 前已可得且 `EffectiveDate` 不晚於 cutoff 本地日期的 exact-consensus 狀態，尚未生效的觀察不得進 ledger。序列不得跳階或倒退；未完成序列在自己的 `EvidenceWindowDays` 個交易日後動態逾期；distribution 或 price breakdown 立即重置。每個 stream 使用 SHA-256 previous-hash chain。
- immutable ledger 只記實際已生效觀察；`stock_positioning_transition_latest` 必須同時接正式交易日曆與 as-of 物化當前狀態。即使沒有新的 exact observation，逾期序列也須在 expiry 後第一個交易日顯示 `MATERIALIZED_CLOCK_DRIVEN_EXPIRY`／`NO_ACTIVE_SEQUENCE`。它只描述 PIT 觀察順序，不是因果或交易指令。
- `stock_positioning_raw_transition_story_evidence` 與 `stock_positioning_conserved_transition_story_evidence` 把 transition 事件依 PIT membership 分別映射至完整故事與資金守恆視圖。
- `rotation_associations` 只可在守恆映射及完整 ETR coverage 通過的相鄰可比較日期建立；部分覆蓋日不建 edge，且下一個有效日不得跨越該缺口計算注意力變化。方向性 edge 還要求同一日期同一 lane 的全部比較族群皆為 `PASS_COMPLETE_DIRECTIONAL_COVERAGE`；任何部分／無效 coverage 或 `NOT_SUPPLIED` 都不得建立該 lane edge，也不得由另一 lane 補位。
- `reference_company_revenue_latest`、`reference_group_revenue_latest` 與 `reference_revenue_audit` 是 strict transition stage 3／4 機會集合形成後才 lazy-load 的月營收選配參考輸出；名稱中的 `reference` 是契約的一部分，非機會 ticker／族群不得出現。它們不得被任何分類、權重、訊號、選樣或成分流程讀回。
