# S20261014 收尾一鍵:隔離區找回 · AI 常用動作引擎 · 輸出表頭全面 + DataFrame 固定 · 自壓頁五支 · 一支 PS 串全部

操作員 2026-10-14(逐字,需求冊 v0193 VCGC-REQ180/181/182 入冊):
「丟失的文件可到隔離區尋找　修正完善收尾功能不要發散　ＶＤＦ　ＶＲＮ　輸出ＨＥＡＤＥＲ還要檢查權全面　自動更新台股權清單及主動式台股ＥＴＦ全清單
ＥＴＦ資料要抓到ＮＡＶ　ＡＵＭ　ＣＡＳＨ　ＩＮＦＬＯＷ　ＡＮＤ　ＯＵＴ　ＦＬＯＷ　ＡＮＤ　ＢＲＥＡＫＤＯＷＮ　輸出ＨＥＡＤＥＲ完整確認然後ＤＡＴＡＦＲＡＭＥ固定
ＤＡＤＡＢＡＳＥ結構最佳化省ＡＰＩ擷取ＴＯＫＥＮ及ＡＩ讀取現況　回顧對話紀錄ＡＩ常做的動作做引擎讓ＡＩ啟動接受結果在反饋以節省ＴＯＫＥＮ
… 整合起來進一個ps指令一起執行 …」→「繼續收尾 開PR 綠了就合併 給我一個指令去完成以上全部」

## 一、一個指令(工作站)

```powershell
pwsh -NoProfile -File VeritasIntelligenceAnalytics\launchers\Invoke-VIA-OneShot-v0100.ps1 -Consent -Apply -Since 2023-06-01
```

- `-Consent` = 操作員親手開同意閘(只在本行程設 `VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT`=YES,跑完還原);AI 不代打。
- `-Apply` = 寫入(ENG094 進庫 · DataFrame 鎖帳 · VCGC closeout --apply);仍不 push(`VIA_VCGC_PUSH=NO`)。
- 不帶旗標 = 乾跑 + 同意閘關(抓網段只看計畫 / SKIP)。其他:`-Grid`(格子整張重跑)· `-Only 1,5,10` · `-NoOpen`。
- 跑完自動跳出 `VIA_Reports\aiops\AIOPS_RUN_latest.html`(15 段燈號表);結束碼 0 綠 · 2 黃 · 1 紅 · 3 環境缺件。

## 二、十五段(各系統走自己的入口 / 管理器,L120)

| # | 段 | 正主 |
|---|---|---|
| 1 | VCGC 省 Token | CGC_MDL149 `token` |
| 2 | VCGC 交接 check | CGC_MDL149 `handoff check` |
| 3 | 隔離區找回(丟失檔) | CGC_MDL276 `lost` |
| 4 | AI 庫卡 | CGC_MDL277 `dbcard` |
| 5 | 台股清單 + 主動式台股 ETF 全清單 → 全步擷取 | Invoke-VIA-VdfFetch 尾版(v0108) |
| 6 | 主動 ETF NAV · AUM · 單位數 · 淨流入 / 流出 | VDF_ENG094 `fetch` |
| 7 | 主動 ETF 持股 / 產業 breakdown | VDF_ENG094 `breakdown` |
| 8 | VDF 管理器 | VDF_SystemManager 尾版 `status` |
| 9 | VRN 管理器 | VRN_SystemManager 尾版 `status` |
| 10 | 輸出表頭全面 + DataFrame 固定 | CGC_MDL249 `all` |
| 11 | PS 檢查(加速器橋 · 自壓頁) | CGC_MDL277 `pslint` |
| 12 | 撞號(對 origin/main 新增) | CGC_MDL277 `collide` |
| 13 | 整合全景實測 | CGC_MDL248 FullCheck |
| 14 | VCGC 收尾 | CGC_MDL149 `closeout` |
| 15 | AI 狀態索引 | CGC_MDL277 `status` |

## 三、新件

- **CGC_MDL276_QuarantineRecover v0100**:隔離區(`functional modules/VIA_RetiredEngines` · `VIA_RetiredEngines`)索引 446 檔(清單 414 · 無清單批次推回 32);`lost` 掃登記冊引用 → 丟失 0;`restore` 只複製、核 sha256、目的地有檔拒絕,隔離區沒有才從 git 取回;只增帳。自測 7/7。
- **CGC_MDL277_AiOps v0100**:AI 每輪重做的動作 → 一個動詞一張卡。`status`(93 份報告判決 + 交接頭 · etag / 304)· `dbcard`(輸出庫每表列數 · 日期區間,先看卡再決定抓不抓)· `collide --base`(只報新增撞號)· `pslint`(重用 FullCheck + BridgeSweeper)· `killgate` · `report`。自測 6/6。
- **CGC_MDL249_DataFrameLock v0101**:+json 型別 · `coverage`(VDF / VRN 全部輸出庫每表 vs 表頭冊)· `all`(check → coverage → lock)。自測 5/5(+v0100 15/15;前版公開面 check_table 等照轉)。
- **VIA_Output_Header_SSOT_v0102**:+7 表(etf_book · tw_listings · active_tw_etf_universe · etf_holdings_changes · etf_fetch_status · etf_holdings_coverage · etf_stats_daily),欄位照寫入程式 DDL / 列字典(evidence 帶檔:行)。容器實資料 9 表 GREEN → 鎖帳 +9。
- **自壓頁五支新版**(許可冊 P013–P017):唯一入口 v0112 · RunAll v0103 · CloseoutChain v0101 · GitHubFirst-Closeout v0101 · SyncFolders v0101 —— 自己的頁改走 `Open-VIAOwnPage`(cmdlet 全名,不經零跳出閘代理)+ 還原 `VIA_NO_OPEN`;pslint 自壓頁 6 → 0。
- **收尾一鍵 v0100**(許可冊 P018):本文第一節。

## 四、照實(不是綠的)

- 毛申購 / 毛贖回(units_subscribed · units_redeemed)仍查無官方端點 → NULL;資金流入 / 流出 = 淨流量正負拆分(kind=ESTIMATE)。
- 表頭覆蓋:輸出庫 5 · 表 43 · 有表頭 9 · 冊外有資料 28 · 冊外空表 6 → 交接待辦 VCGC-REQ158:header-coverage(各 manager 照寫入程式補)。
- VRN 管理器 status RED(邏輯索引過期 2)= VRN 自己的 manager 處理(L120,本批不代修)。
- 版號:未併分支 `claude/kind-cannon-pti15g` 也用了需求冊 v0193–v0199、盤點冊 v0168–v0177、VCGC-REQ180/181;本批照主線連號(需求冊 v0193 · 盤點冊 v0168 · VCGC-REQ180–182;刪除閘 KILL-11 不准跳號 · 編號系統只發連號),該分支若之後併入由後併者改號(LL334)。

## 五、容器實跑紀錄

2026-10-14 容器 pwsh 7 實跑 2118 秒
- 結束碼 1:

- ① 省 Token GREEN 3.9s
- ② 交接 check RED(本批新模組未登錄
- 相依證據因新檔失效 → 登錄後重測)· ③ 隔離區找回 GREEN(丟失 0)· ④ 庫卡 GREEN
- ⑤ VdfFetch v0108 -Dry GREEN 37.9s
- ⑥ ENG094 fetch SKIP(同意閘關 NO_CONSENT)· ⑦ breakdown GREEN(143 列)· ⑧ VDF 管理器 YELLOW(邏輯 STALE;容器實跑時誤標 SKIP,已改為只有抓網段才可 SKIP)· ⑨ VRN 管理器 RED(邏輯索引過期 2,VRN 自己的)· ⑩ 表頭 all YELLOW(NODATA 12
- 冊外 28)· ⑪ pslint GREEN
- ⑫ collide GREEN(新增 0)· ⑬ FullCheck RED 1899.6s(三橋 GREEN:ACCEL 1645/1645
- NET 137/137
- PS-ACCEL 993/993
- 自擋開頁 0;串測逾時 1800s
- 單一路徑版本不齊 3
- 格子存證 366.7h 舊
- 交接驗收 RED)· ⑭ closeout(乾跑)RED:停在 VRN provenance 案(rc 0 但標記「[來源回歸] fail=0」沒印,VRN 自己的)· ⑮ status:98 份報告紅 17;總頁 AIOPS_RUN_latest.html 經 Open-VIAOwnPage 實際跳出(xdg-open 記錄 07:38:24)
