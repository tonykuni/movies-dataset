# VIA 成功鎖定帳(唯讀檢視;正本 VIA_SuccessLock_Ledger_v0100.jsonl,只增)

每列 = 一個完成項:檔 · 版本 · VCGC 編號 · 鎖定時間(UTC)· 內容雜湊(先把 CRLF 換成 LF 再算 SHA-256)· 當時的證據。
檔的內容之後若變了,雜湊對不上 = 這一列的鎖不再成立,要重新驗過再加新列(不改舊列)。

| 鎖定時間 | 檔 | 版本 | VCGC 編號 | 雜湊前 12 碼 | 做了什麼 | 證據 |
|---|---|---|---|---|---|---|
| 2026-11-16T19:01:30Z | VRN_SystemManager_v0276.py | 0276 | VIA-VRN-MDL349 | 20d0f5663139 | 檔名下載時間戳不當報告日期 | 自測 7/7 · 實跑 2 份日期改對 |
| 2026-11-16T19:01:30Z | VRN_SystemManager_v0277.py | 0277 | VIA-VRN-MDL351 | 04f91d692eed | 引擎矩陣 accel / net 兩欄(語法樹 + 執行時 + 鎖冊) | 自測 9/9 · 實跑 86/86 |
| 2026-11-16T19:01:30Z | VDF_SystemManager_v0185.py | 0185 | VIA-VDF-MDL287 | a141941906cd | 引擎矩陣 accel / net 兩欄 | 自測 9/9 · 實跑 109/109 · 網路工具缺 0 |
| 2026-11-16T19:01:30Z | VRN_MDL260_SafeParallelLaunch_v0102.py | 0102 | VIA-VRN-MDL350 | ed3e090dfee3 | VRN 一個指令:就緒檢查 · 分群 · 結果併燈 | 自測 18/18 · 容器 24 份整輪跑完(總燈紅:缺 pymupdf) |
| 2026-11-16T19:01:30Z | VDF_MDL022_SafeParallelLaunch_v0102.py | 0102 | VIA-VDF-MDL288 | ce102efe928e | VDF 結果併燈 · 閘開著時真的補擷取 | 自測 8/8 · 未在有資料庫的機器實跑 |
| 2026-11-16T19:01:30Z | VRN2_MarketFetch_v0113.py | 0113 | VIA-VRN-MDL352 | 52334e5ceb4e | 補上真的加速器橋(v0112 只有標記) | 自測 13/13 |
| 2026-11-16T19:01:30Z | VRN_ENG112_FinancialRead_v0101.py | 0101 | VIA-VRN-ENG332 | 85de23248917 | 補上加速器橋(v0100 沒掛) | 自測 rc 0 · 橋載入 True |
| 2026-11-16T19:01:30Z | VRN_ENG110_TabReport_v0117.py | 0117 | VIA-VRN-ENG333 | 095456a7b884 | 改釘 ENG112 v0101,橋才真的生效 | 自測 rc 0 |
| 2026-11-16T19:01:30Z | VRN_ParamControl_SSOT_v0101.json | 0101 | — | 310b39f03f87 | 參數一本 JSON:執行參數 · 輸入分群 · 單檔例外 | 啟動器自測涵蓋 · VRN 自己的冊(VCGC 不發號) |
| 2026-11-16T19:01:30Z | Invoke-VIA-VrnVdf-HandleAll-v0101.ps1 | 0101 | VIA-CORE-MDL866 | d21b801fcb05 | 一支 PS:同步 · 進環境 · VRN · VDF · 總結;-OpenGates | 只做靜態檢查,未在 PowerShell 實跑 |
| 2026-11-16T19:01:30Z | sitecustomize.py | 無版號 | VIA-SUP-MDL878 | 2676cd1549c6 | 啟動鉤直讀鎖冊,不再每支 python 載九版鏈 | 容器兩種模式掛上同兩支工具 · 桌機未驗 |
| 2026-11-17T12:32:07Z | CGC_MDL282_LocalMonitor_v0100.py | 0100 | VIA-VCGC-MDL1645 | 0e863dd1b2af | 本機唯讀現況矩陣:系統 · 工具 · 參數 · 模組引擎 · 收據 | 自測 16/16 · 經主控台實跑 · 骨架卡 問題 0 |
| 2026-11-17T12:32:07Z | CGC_MDL283_CardMatrixFeedback_v0100.py | 0100 | VIA-VCGC-MDL1646 | 318bc3e7dc6f | 卡片摘要 · 矩陣明細 · AI 回饋兩段篩選(只摺不丟 · 五條對帳) | 自測 25/25 · 實跑 2,520 列收成 60 行、對帳相符 · 無頭瀏覽器開頁無腳本錯誤 |
| 2026-11-17T12:32:07Z | CGC_MDL283_CardMatrixFeedback_v0101.py | 0101 | VIA-VCGC-MDL1648 | 09c671384efb | 成功鎖 · 給動作主力的更新回饋 · 本機免費工具紀錄 · 回饋包遮家目錄 | 自測 22/22(另跑 v0100 鏈 25/25)· 實跑對帳六條相符 |
| 2026-11-17T12:32:07Z | CGC_MDL279_MCPServer_v0104.py | 0104 | VIA-VCGC-MDL1647 | f2b508332caa | MCP 唯讀門面多三把回饋鍵(feedback / feedback-delta / feedback-full) | 自測 4/4 · 前版鏈 rc 0 · 未接真的 MCP 客戶端 |
| 2026-11-17T12:32:07Z | VIA_UI_WorkPlatform_TemplateLock_v0100.json | 0100 | — | 7b44f30e1300 | 對內工作平台模板鎖冊(版面 css 只用 token) | css 與 token 冊雜湊由引擎每輪核 |
| 2026-11-17T12:32:07Z | VIA_UI_WorkPlatform_TemplateLock_v0101.json | 0101 | — | e8481ef3f86b | 燈號四色一律白字(操作員 2026-11-17 令) | 引擎自測核 css 規則 · 無頭瀏覽器看過 |
| 2026-11-17T12:33:44Z | CGC_MDL283_CardMatrixFeedback_v0101.py | 0101 | VIA-VCGC-MDL1648 | 8614a630f477 | 成功鎖 · 給動作主力的更新回饋 · 本機免費工具紀錄 · 模組引擎鍵改家族名(推送前修正後重鎖;同檔以本列為準) | 自測 23/23(另跑 v0100 鏈 25/25)· 實跑對帳六條相符 |
| 2026-11-17T13:12:16Z | CGC_MDL282_LocalMonitor_v0101.py | 0101 | VIA-VCGC-MDL1649 | dade5f0cb2e9 | 現況矩陣補十二塊偵測 + 管理面覆蓋 · 黃燈白字 | 自測 25/25(另跑 v0100 鏈 16/16)· 實跑新增 689 項、對帳相符 |
| 2026-11-17T13:12:16Z | CGC_MDL283_CardMatrixFeedback_v0102.py | 0102 | VIA-VCGC-MDL1650 | 778aeb091631 | 延伸偵測併進卡片與矩陣 · [主機] · [沒管到] | 自測 9/9(另跑 v0101 鏈 23/23 · v0100 鏈 25/25)· 實跑 3,246 列對帳六條相符 |
| 2026-11-17T16:22:54Z | CGC_MDL282_LocalMonitor_v0102.py | 0102 | VIA-VCGC-MDL1651 | 49074d9f9992 | 延伸偵測增量快取 · 彙總列標記 | 自測 9/9(另跑 v0101 鏈 25/25 · v0100 鏈 16/16)· 實跑 13.1 秒 → 0.3 秒 |
| 2026-11-17T16:22:54Z | CGC_MDL283_CardMatrixFeedback_v0103.py | 0103 | VIA-VCGC-MDL1652 | 8d5ff66ece65 | 現況顯示最佳化:彙總列不另計 · 三排卡片 · 收據 STATUS_latest.json · status() · manifest | 自測 20/20(另跑前版鏈 57/57)· 實跑對帳八條相符 |
| 2026-11-17T16:25:27Z | CGC_MDL283_CardMatrixFeedback_v0103.py | 0103 | VIA-VCGC-MDL1652 | 2cbb8baa1ceb | 現況顯示最佳化(推送前修正後重鎖;同檔以本列為準):彙總列不另計 · 三排卡片 · 收據 · status() · manifest | 自測 21/21(另跑前版鏈 57/57)· 實跑對帳八條相符 |
| 2026-11-17T16:28:06Z | CGC_MDL283_CardMatrixFeedback_v0103.py | 0103 | VIA-VCGC-MDL1652 | bd60f3a2d4ba | 現況顯示最佳化(推送版;同檔以本列為準):彙總列不另計 · 三排卡片 · 收據 · status() · manifest | 自測 21/21(另跑前版鏈 57/57)· 實跑對帳八條相符 · 無頭瀏覽器點過三排卡片 |
| 2026-11-18T01:51:19Z | CGC_MDL149_VeritasCentralGovernanceConsole_v0197.py | 0197 | VIA-VCGC-MDL1653 | d6d7ecfd8665 | 現況顯示接線:monitor status 子動詞(既有 monitor 其他子動詞照舊轉交) | 自測 16/16 · 經入口實跑一輪(收據更新 · rc 與燈一致)· test --quick 該站綠 |
| 2026-11-18T01:51:19Z | CGC_MDL282_LocalMonitor_v0103.py | 0103 | VIA-VCGC-MDL1655 | 66793f36ed49 | 選配收據不計系統格;自己的收據不讀自己的燈 | 自測 42 項過(含 v0102 · v0101 · v0100 鏈)· 實跑該列為綠且標選配 |
| 2026-11-18T01:51:19Z | CGC_MDL279_MCPServer_v0106.py | 0106 | VIA-VCGC-MDL1654 | cd30cd88a6a0 | MCP 唯讀資源 +vcgc/status | 本版 6 項過 · v0105 鏈 rc 0 |
| 2026-11-18T01:51:19Z | VIA_SystemReceipt_Contract_SSOT_v0101.json | 0101 | — | 0e4d98e5344a | 收據契約 +VCGC status-display(選配) | 其餘四節與 VCGC 前兩筆逐項比對相同 |
| 2026-11-18T01:51:19Z | VIA_Requirements_SSOT_v0256.json | 0256 | — | 9ace971be3ad | 需求冊 +VCGC-REQ225(PARTIAL) | 舊 284 條逐項比對相同 · SDD X-REQ-BACK 綠 |
| 2026-11-18T01:51:19Z | VIA_Workflow_VCGC_SSOT_v0152.json | 0152 | — | f81224971613 | 工作流冊 +VCGC-WKF043(4 步) | 舊 42 條逐項比對相同 · SDD X-CODE · X-ENGINE 綠 |
| 2026-11-18T01:51:19Z | VIA_VCGC_FunctionInventory_SSOT_v0245.json | 0245 | — | 852f6ef13105 | 盤點冊 +5 站 · +4 工作流步 · manifest 豁免 | 舊 428 站逐項比對相同 · test --quick verb 58/58 · workflow 181/181 |
| 2026-11-18T02:41:24Z | CGC_MDL283_CardMatrixFeedback_v0104.py | 0104 | VIA-VCGC-MDL1656 | 1effae5975ca | token 冊雜湊先統一成 LF 再算(Windows 上頁面樣式不掉)· 收據 version 寫本版 | 自測 88 項過(含前版鏈;放了一份 CRLF 檔,舊算法會判錯)· 經入口實跑收據 version v0104 |
| 2026-11-18T16:13:45Z | CGC_MDL134_ParallelLanes_v0103.py | 0103 | VIA-VCGC-MDL1662 | 4fb2a0997e6f | cmd 動詞:短指令的 Python 路由(list / check / plan / run)· 先降壓 → 3~6 道 → 監工過熱減道、暫停最新子行程、冷卻恢復 | 自測 35/35 · cmd run via-six 實跑綠(71 秒)· cmd run via-panorama-all 兩步同時起跑,兩步都紅(紅在既有問題:收容夾 9 支沒帶橋 · 已修冊回歸 2 筆) |
| 2026-11-18T16:13:45Z | VIA_ShortCommand_PyRoute_SSOT_v0100.json | 0100 | VIA-VCGC-SSOT404 | be269b34ac86 | 短指令 → Python 路由冊:212 支全列,第一批 4 支有可跑的步 | 應掃 212 · 已掃 212 · 略過 0 · cmd check:這輪改 4(綠 4)· 原本就是 Python 142(綠 135 · 紅 7)· 待改 23 · 轉呼叫 / PS 本職 43 |
| 2026-11-18T16:13:45Z | Register-VIA-Commands-v0279.ps1 | 0279 | VIA-CORE-MDL868 | 84e18a848dc6 | via-vrnrun · via-vdffetch · via-six · via-panorama-all 改成只轉呼叫 Python 入口 | 靜態檢查:括號引號配對 · 與 v0278 同編碼同換行 · 不含本機路徑;未在主機 PowerShell 實跑(這一列鎖的是檔內容,不是主機驗收) |
| 2026-11-18T17:22:58Z | VDF_ENG054_TWDailyBackfill_v0112.py | 0112 | VIA-VDF-ENG372 | 73c55b5b124d | 台股日量價回補一跑就倒的錯修掉(清非主動式 ETF 時少給庫路徑)· worker 動詞 | 自測 12/12(負控重現 TypeError)· 經 VDF 擷取系統真跑:2017 檔自 2022-07-01 起 +2,048,559 列 · 失敗 0 · 275 秒 |
| 2026-11-18T17:22:58Z | VDF_FetchSystem_SSOT_v0111.json | 0111 | —(VDF 自己的冊;VCGC 邊界閘不代發) | 90f2b8d50bc4 | 擷取冊:e054 指到 v0112 worker(只改這一列) | 其餘 36 支逐項相同 · 擷取系統自測 9/9 · 真跑 e054 rc 0 |
| 2026-11-18T17:22:58Z | VDF_MDL022_SafeParallelLaunch_v0104.py | 0104 | VIA-VDF-MDL293 | cd4bbe378757 | VDF 自己的啟動器就是入口(子行程帶入口標記)· 總結行印本版 | 自測 8/8 · 真跑:e115 / e116 由 DENY 變 rc 0(e116 寫入 2049 列) |
| 2026-11-18T17:22:58Z | VDF_ENG077_ActiveETFUniverse_v0107.py | 0107 | 待編 | 4311df7707c0 | VCGC 的 ScrapeGate 尺檔不在 / 壞掉時照樣載得起來(VDF 自己的同一把尺) | 自測 12/12 · 正常樹與拿掉 VCGC 的副本都過 |
| 2026-11-18T17:22:58Z | VDF_ENG055_OmniFetch_v0124.py | 0124 | 待編 | 0efbb5d36071 | 同上(擷取冊 e055 四列都是這一支) | 自測 8/8 · 正常樹與拿掉 VCGC 的副本都過 |
| 2026-11-18T17:22:58Z | CGC_MDL245_SDDValidator_v0109.py | 0109 | VIA-VCGC-MDL1663 | 6aa0b9d90a18 | SDD X-REQ:需求歸屬是倉內存在的檔也算 | 自測 12/12 · 真冊 288 條 X-REQ 由紅轉綠 |
| 2026-11-18T17:22:58Z | VIA_Workflow_VCGC_SSOT_v0154.json | 0154 | VIA-VCGC-SSOT405 | 1fe53636f6b6 | 釘死舊版號的 14 步改取尾版(L54) | 點名以外逐條差異 0 · SDD X-REG 綠 |
| 2026-11-18T17:22:58Z | VIA_Workflow_VDF_SSOT_v0115.json | 0115 | —(邊界閘擋,VDF 自己登) | 08a3cbcef0d4 | 釘死舊版號的 13 步改取尾版 | 點名以外逐條差異 0 |
| 2026-11-18T17:22:58Z | VIA_Workflow_VRN_SSOT_v0111.json | 0111 | —(邊界閘擋,VRN 自己登) | c7a3e85640df | VRN-WKF010 補欄 · 2 步改取尾版 | SDD X-COL 由紅轉綠 · tests.real 寫的是容器實跑 |
| 2026-11-18T17:22:58Z | VQG_AllInOne_v0112.py | 0112 | VIA-VQG-MDL009 | e6c94589ed64 | 加速器橋補成真的匯入(前版只有標記) | 自測 6/6 · 前版 SHA 釘住 |
| 2026-11-18T17:22:58Z | VQG_SectorActiveWeight_v0101.py | 0101 | VIA-VQG-MDL010 | ff9f4937ccf2 | 補加速器橋 | 自測 6/6 |
| 2026-11-18T17:22:58Z | VDF_TW_TickerClass_v0101.py | 0101 | VIA-VDF-MDL295 | 8bb5ae7fa1db | 補加速器橋(v0100 是操作員分支的成果,已併入) | 自測 6/6(含前版 kinds=14) |
| 2026-11-18T18:40:37Z | CGC_MDL134_ParallelLanes_v0103.py | 0103 | VIA-VCGC-MDL1664 | 4fb2a0997e6f | 更正編號:與 main(#675)撞號,以 main 為準重編;檔內容沒變 | 原記 VIA-VCGC-MDL1662 作廢 → 現為本列編號;雜湊與先前那一列相同 |
| 2026-11-18T18:40:37Z | CGC_MDL245_SDDValidator_v0109.py | 0109 | VIA-VCGC-MDL1665 | 6aa0b9d90a18 | 更正編號:同上 | 原記 VIA-VCGC-MDL1663 作廢;雜湊與先前那一列相同 |
| 2026-11-18T18:40:37Z | VIA_ShortCommand_PyRoute_SSOT_v0100.json | 0100 | VIA-VCGC-SSOT409 | be269b34ac86 | 更正編號:同上 | 原記 VIA-VCGC-SSOT404 作廢;雜湊與先前那一列相同 |
| 2026-11-18T18:40:37Z | VIA_Workflow_VCGC_SSOT_v0155.json | 0155 | VIA-VCGC-SSOT410 | b5c34edeaf13 | 以 main 的 v0154 為底重出:釘死版號的 79 步改取尾版(分支先前的 v0154 / v0155 與 main 撞名,作廢) | 點名以外逐條差異 0 · SDD X-REG 綠 |
| 2026-11-18T18:40:37Z | VDF_ENG077_ActiveETFUniverse_v0107.py | 0107 | VIA-VDF-ENG373 | 4311df7707c0 | 補記編號(先前那一列寫待編) | 檔內容沒變 |
| 2026-11-18T18:40:37Z | VDF_ENG055_OmniFetch_v0124.py | 0124 | VIA-VDF-ENG374 | 0efbb5d36071 | 補記編號(先前那一列寫待編) | 檔內容沒變 |
| 2026-11-18T18:40:37Z | VDF_ENG094_ActiveETFActivity_v0102.py | 0102 | VIA-VDF-ENG375 | 86d69c960844 | VCGC 的 ScrapeGate 尺不在 / 壞掉時改用 VDF 自己的同一把尺 | 自測 7/7(含負控)· 正常樹與拿掉 VCGC 的副本都過 |
| 2026-11-18T18:40:37Z | VDF_ENG232_TWIndexOfficial_v0102.py | 0102 | VIA-VDF-ENG376 | 42349599810b | 櫃買指數改走現行官方端點 · 兩個指數各自接續 · 按月寫庫並出聲 · 櫃買先抓 | 自測 13/13 · 真跑:櫃買 935 列 2023-01-03 → 2026-11-18(含開高低收與量值) |
| 2026-11-18T18:40:37Z | VDF_ENG232_TWIndexOfficial_v0103.py | 0103 | VIA-VDF-ENG377 | b709d935f44b | 寫庫前確保欄型 · 加權某月回空就停在那裡不留洞 | 自測 10/10(含負控)· 真跑壞欄型的湖庫:欄型修成 DOUBLE · 加權補進 63 列含法人數字 |
| 2026-11-18T18:40:37Z | VDF_FetchSystem_SSOT_v0114.json | 0114 | —(VDF 自己的冊;VCGC 邊界閘不代發) | 72d84dbafa51 | 擷取冊尾版:e054 → v0112 worker · e077 → v0107 · e232 → v0103(v0111 ~ v0114 每版只改一列) | 每版點名以外差異 0 · 三支都經 VDF 擷取系統真跑過 |
| 2026-11-18T18:40:37Z | SUP_MDL744_NLPApplicationHub_v0103.py | 0103 | VIA-SUP-MDL1203 | 5e18c7bb0d9e | 補編號:先補上 VIA_DownloadsSync v0100 / v0101 缺的模組列之後才編得進去 | 稽核 遺失 0 · 改身分 0 · 重號 0;檔內容沒動 |
| 2026-11-18T18:47:04Z | VDF_ENG094_ActiveETFActivity_v0103.py | 0103 | VIA-VDF-ENG378 | d2724a42cb89 | 接回「在尾版上替換 analyze,build 用得到」(v0102 漏了,CI 紅);v0102 的同意尺退路保留 | 自測 8/8(含負控)· 本機重跑 CI 的 test_via_etf_activity 23 項全過 |
| 2026-11-18T18:58:07Z | VDF_ENG232_TWIndexOfficial_v0104.py | 0104 | VIA-VDF-ENG379 | 875ca00e47f9 | 櫃買某個歷史月份來源回空也停在那裡(PR 審查 P1);擷取冊 v0115 的 e232 指到本版 | 自測 11/11(含負控:前版把洞埋住;來源恢復後補回)· 經擷取系統真跑:加權 2024-01 來源回空 → 停在那裡 rc 2,沒有往後寫 |
| 2026-11-19T17:34:37Z | VDF_ENG054_TWDailyBackfill_v0113.py | 0113 | VIA-VDF-ENG380 | 9876fa83798c | 起日 2021-01-01 往前補:庫內最早一天晚於起日的標的加進計畫(頭帳記已試過,不重試) | 自測 13/13(含負控)· 經 VDF 啟動器真擷取:tw_daily_prices 2021-01-04 → 2026-11-18 · 1425 個交易日 · 2,695,891 列 · rc 0 |
| 2026-11-19T17:34:37Z | VDF_ENG232_TWIndexOfficial_v0105.py | 0105 | VIA-VDF-ENG386 | af663fea2632 | 帶 --start 時只抓頭段缺口 + 尾段,不再整段重抓 | 自測 10/10 · 真擷取:櫃買 2021-01 → 2022-07 補進 · 加權 2021-02 來源回空照停(同時段個股擷取把官方源壓住;單跑同月 22 列 OK) |
| 2026-11-19T17:34:37Z | VDF_ENG060_AdjPriceLayer_v0109.py | 0109 | VIA-VDF-ENG383 | 9afeb1f7d563 | 自測不吃本機狀態:暫存夾造 TW + GL 兩個庫 | 自測 6/6(根因 v0107 L254-255 無條件讀 gl) |
| 2026-11-19T17:34:37Z | VDF_MDL020_DataPlane_v0103.py | 0103 | VIA-VDF-MDL296 | b214aa1275b4 | 自測不吃本機狀態:清單閘用暫存 VIA/HERE,去掉 VIA_VDF_FETCH_HOME | 自測 6/6 |
| 2026-11-19T17:34:37Z | VDF_ENG057_TradingValueBackfill_v0112.py | 0112 | VIA-VDF-ENG382 | cbfafa37f1ae | 開始抓時不靠 VCGC 尺檔(系統獨立);同意閘用 VDF 自己的判法 | 自測 7/7 · 拿掉 CGC_*.py 的副本照樣跑到同意閘 · 真擷取 tw_trading_daily 自 2021-01-04 起寫入中 |
| 2026-11-19T17:34:37Z | VDF_ENG078_ActiveETFHoldingsHistory_v0114.py | 0114 | VIA-VDF-ENG385 | d72255813d7f | 開始抓時不靠 VCGC 尺檔(系統獨立) | 自測 7/7 · 獨立演練與正常樹同結果 · 真擷取 rc 0 |
| 2026-11-19T17:34:37Z | VDF_FetchSystem_SSOT_v0116.json | 0116 | —(VDF 自己的冊;VCGC 邊界閘不代發) | 849a765a95c3 | e054 → v0113 · e232 → v0105 | 點名以外差異 0 · 真擷取用到 |
| 2026-11-19T17:34:37Z | VDF_FetchSystem_SSOT_v0117.json | 0117 | —(VDF 自己的冊;VCGC 邊界閘不代發) | d3b2865d2893 | e056 → v0109 · e057 → v0112 · e075 → v0108 · e078 → v0114 | 點名以外差異 0 · 真擷取用到 e057 v0112 / e078 |
| 2026-11-19T17:34:37Z | VDF_FetchGroups_SSOT_v0103.json | 0103 | —(VDF 自己的冊;VCGC 邊界閘不代發) | 6d6e1cb6ba51 | TW_PRICE_VOL 起日帶到 e054;TW_MONTHLY_REV 加 e075 + --since | 計畫列驗過:e054 ['worker','--start','2021-01-01'] · e075 ['run','--since','2021-01-01'] |
| 2026-11-19T17:34:37Z | VDF_FetchGroups_SSOT_v0104.json | 0104 | —(VDF 自己的冊;VCGC 邊界閘不代發) | bb816d0a4df7 | TW_CHIP 起日帶到 e056 | 計畫列驗過:e056 ['--start','2021-01-01'] |
| 2026-11-19T17:51:45Z | VDF_ENG232_TWIndexOfficial_v0106.py | 0106 | VIA-VDF-ENG388 | 5e342ab73be9 | 命令列 run 真的走本版分段(PR 688 P1);看實際日子找中間的洞(P2,> 16 天才算洞);一個指數停了不擋另一個 | 自測 12/12(兩個負控)· 命令列乾跑印 v0106 分段 · 真庫副本:加權 3 洞(2021-01-30→2023-01-02 · 2023-04→07 · 2023-12-30 起)· 櫃買 1 洞(2022-07-30→2023-01-02) |
| 2026-11-19T17:51:45Z | VDF_ENG054_TWDailyBackfill_v0114.py | 0114 | VIA-VDF-ENG387 | c919ab615f8d | 往前補的試過帳:每批以起日抓回來、不在失敗名單才記(PR 688 P1);帳換新檔 | 自測 12/12(負控:v0113 一排計畫就記 3 檔) |
| 2026-11-19T17:51:45Z | VDF_FetchSystem_SSOT_v0118.json | 0118 | —(VDF 自己的冊;VCGC 邊界閘不代發) | f22064c02b67 | e054 → v0114 · e232 → v0106 | 點名以外差異 0(10 行 = version + 兩列 file / doc) |
| 2026-11-20T13:29:43Z | CGC_MDL140_HandoverConsole_v0109.py | 0109 | VIA-VCGC-MDL1677 | 58dc1dc54914 | 交接閘停用檔名冊:retired_files 具名 · 接手者此刻有效綠才放行 · 名冊外不放寬(UIEngine v0101–v0107 停用) | 自測 10/10 · 前版鏈 v0102–v0108 PASS · daily_handover / handoff 案 rc 0 |
| 2026-11-20T13:29:43Z | VDF_TW_TickerClass_v0102.py | 0102 | VIA-VDF-MDL297 | 1de6bbeacff3 | 補統包網路工具橋(v0101 一字不動,SHA 釘住) | 自測 7/7(含前版鏈)· 交接案 vdf_tickerclass VERIFIED |
| 2026-11-20T13:29:43Z | VDF_ENG094_ActiveETFActivity_v0104.py | 0104 | VIA-VDF-ENG389 | abea9570252f | 補統包網路工具橋;保留 v0103 尾版替換 analyze 接法(v0103 一字不動,SHA 釘住) | 自測 9/9(含前版鏈)· CI test_via_etf_activity 23/23 · 交接案 vdf_etf_metrics rc 0 |
| 2026-11-20T13:58:59Z | CGC_MDL140_HandoverConsole_v0110.py | 0110 | VIA-VCGC-MDL1678 | 19963d02872d | 舊版號檔的加速器橋看家族尾版(標記 + 語法樹真的匯入);尾版本身照舊判(操作員裁定 a) | 自測 10/10 · 前版鏈 v0102–v0109 PASS · 交接閘 ACCEL_BRIDGE_MISSING 7 → 2 · handoff / daily_handover 案 rc 0 |
| 2026-11-20T15:00:44Z | VIA_Workflow_VCGC_SSOT_v0154.json | 0154 | VIA-VCGC-SSOT405 | 89285f3921c9 | 重鎖(只增):同號撞名 —— 另一線 4473f004f 也出了 v0154(+VCGC-WKF045),合併時以 main 為準,原鎖 1fe53636f6b6 的內容被取代;不是內容倒退 | 原鎖版 106 步取尾版:在尾版 v0158 逐步比對,重新釘版 0 · 消失 0(成功仍在,載體換到尾版) |
| 2026-11-20T15:00:44Z | VIA_Workflow_VCGC_SSOT_v0158.json | 0158 | —(工作流冊尾版;VCGC 自己的冊) | cea3bacf61ba | 承接 v0154 原鎖的「釘死舊版號的步改取尾版」(L54) | 183 → 191 步;原 106 步取尾版仍取尾版 |
| 2026-11-20T15:24:46Z | VIA_VCGC_ApplyRun_v0105.py | 0105 | VIA-CORE-MDL876 | 4286c1461c93 | go 一個動詞(同步 → A 啟用 → G,K 驗證 → 收據合成一份 · 剪貼簿)· --data-home 驗了才用 · 心跳帶最後一行 | 自測 11/11 · 前版鏈 v0100–v0104 · Codex P2 修正(A 紅不被 G,K 蓋)· 容器 go --no-activate 實跑 |
| 2026-11-20T15:24:46Z | CGC_MDL223_FlowConsistency_v0103.py | 0103 | VIA-VCGC-MDL1679 | 3bed669bb729 | 流程閘頁帶產生時間 · 版本(機讀 meta;視覺零改)· 蓋章裝在寫頁那一層 | 自測 10/10 · 前版 v0102 9/9 · synchronizer 頁 5/5 綠(重現 test --quick → synchronizer 順序) |
| 2026-11-20T15:24:46Z | CGC_MDL226_StepMatrix_v0104.py | 0104 | VIA-VCGC-MDL1680 | f61b1738c702 | 步驟矩陣頁帶產生時間 · 版本(機讀 meta;視覺零改)· 蓋章裝在寫頁那一層 | 自測 10/10 · 前版 v0103 13/13 · synchronizer 頁 5/5 綠 |
| 2026-11-20T15:50:12Z | VRN_ENG086_FirstPageLogicBridge_v0120.py | 0120 | VIA-VRN-ENG328 | 5add61dcaef7 | 無效跳脫字元修正(1050 行 docstring '\-' → '\\-');位元組碼與原版逐層相同 | 自測 121/121 · 零 SyntaxWarning · 交接案 vrn_firstpage_bridge rc 0 |
| 2026-11-20T16:22:49Z | VIA_VCGC_ApplyRun_v0106.py | 0106 | VIA-CORE-MDL877 | 384c4d29fee8 | go 的 A 道改走 VDF_MDL022 / VRN_MDL260 安全並行啟動器(3~6 道 auto · 監工過熱減道 / 暫停)· --vrn-source | 自測 9/9 · 前版鏈 v0100–v0105 · 兩啟動器 check 實跑各自 3 道 · 交接案 C-applyrun-v0106 rc 0 |
| 2026-11-20T17:22:26Z | CGC_MDL283_CardMatrixFeedback_v0109.py | 0109 | VIA-VCGC-MDL1681 | b58049ad0e0d | 展現精簡:先做這幾件(原因歸組)· 其餘卡片收合 · 矩陣欄寬 · 整頁下載 MD | 自測全過(含 v0108)· 瀏覽器實按下載 MD:現況 3351 列 · 功能一覽 1273 列全在 · 點卡片照樣篩矩陣 · 頁面零錯誤 |
| 2026-11-20T17:22:26Z | VIA_UI_WorkPlatform_DashboardLayout_v0101.json | 0101 | — | ef5734e7f866 | 版面冊:先做這幾件 · 收合區 · 矩陣欄寬(只有寬度;不帶顏色) | v0100 規則照抄在前 · 無色碼 · 雜湊相符 · 兩頁實套 |
| 2026-11-20T18:26:01Z | VRN_MDL260_SafeParallelLaunch_v0103.py | 0103 | VIA-VRN-MDL357 | 4f21dfe8448b | 跑的途中不監控 CPU / DRAM · 先降壓 · 固定 3 道 · 路徑轉絕對 · --via-db → vrn_database 增量庫 | 自測 8/8 · 開閘整輪 202 秒 · 降壓 0 次 · 第二輪增量 GREEN 零追加 180 秒 |
| 2026-11-20T18:26:01Z | VRN_ParamControl_SSOT_v0103.json | 0103 |  | 7c147cc7cde8 | VRN 參數冊:slots 3/3 · extract_workers 1 | check 綠 · 同時道數 3(夾在 3~3) |
| 2026-11-20T18:26:01Z | VDF_MDL022_SafeParallelLaunch_v0106.py | 0106 | VIA-VDF-MDL299 | b70d4ab776aa | 不監控 · 固定 3 道 · --via-db → vdf_database · 開跑前名稱反解 | 自測 9/9 · 模擬併入 #690 v0105 照過 · check / 橋閘 GREEN |
| 2026-11-20T18:26:01Z | VDF_MDL009_TWStockList_v0104.py | 0104 | VIA-VDF-MDL298 | 5cdadde36a1f | V10 名稱字形 · fixnames 先備份就地反解 | 自測 13/13 · 開閘實跑 1987 列亂碼 0 · fixnames 庫 2679 列 / 檔 1786 格 剩 0 · 再跑零改動 |
| 2026-11-20T18:26:01Z | SUP_MDL740_NetUnified_v0120.py | 0120 | VIA-SUP-MDL1204 | 3f640f8627e8 | http_json 先位元組自己解碼 | 自測 8/8 · 開閘重抓名單亂碼 892 → 0 |
| 2026-11-20T18:26:01Z | VIA_VCGC_ApplyRun_v0107.py | 0107 | VIA-CORE-MDL878 | 562fe603528f | go --via-db · 收尾整份備份 | 自測 8/8 · 前版鏈 v0100–v0106 照過 |
| 2026-11-20T18:34:45Z | VDF_MDL022_SafeParallelLaunch_v0106.py | 0106 | VIA-VDF-MDL299 | 15fa19bd79aa | Codex P1 / P2:run --dry 名稱反解只數不寫 · --via-db 固定 vdf_database(沒有就建) | 自測 11/11 · 交接案收據 · 串測站 GREEN |
| 2026-11-20T18:36:26Z | VRN_MDL260_SafeParallelLaunch_v0103.py | 0103 | VIA-VRN-MDL357 | 510925ff0148 | Codex P2:自測守參數冊各組 extract_workers = 1 | 自測 9/9 · 交接案收據 · 串測站 GREEN |
| 2026-11-20T18:36:26Z | VRN_ParamControl_SSOT_v0103.json | 0103 | VRN-B-0046 | a23ee3addc39 | Codex P2:EQUITY / INDUSTRY / DAILY 組 extract_workers auto → 1 | check:分群 EQUITY extract 行程 1 |
| 2026-11-21T01:29:50Z | VRN_SystemManager_v0279.py | 0279 | VIA-VRN-MDL358 | 36bc80a45516 | VRN 自己發號定案(不等 VCGC 核號) | 自測 10/10 · 交接案收據 · 串測站 GREEN · 實跑 extract 112 號已確認 · 再跑不換版 |
| 2026-11-21T01:29:50Z | VRN_Asset_Register_v0102.json | 0102 | (VRN 自己的冊) | afda0f933731 | VRN 資產登記:105 冊號 + 7 參數號 全部已確認(VRN 自發)· 號碼同 v0101 | 由 VRN 管理器 v0279 實跑寫出 |
| 2026-11-21T01:38:57Z | VRN_SystemManager_v0279.py | 0279 | VIA-VRN-MDL358 | 9bba6bc85f31 | Codex P2:沿用下來的舊冊 / 舊參數也轉已確認(號不變) | 自測 11/11 · 交接案收據 · 串測站 GREEN · 實跑 extract 無變更 |
| 2026-11-21T01:53:46Z | VRN_SystemManager_v0279.py | 0279 | VIA-VRN-MDL358 | 36bc80a45516 | 還原為已合併位元(同 main);取代本線 2026-11-21 01:4x 那列(那列的雜湊是就地改過的內容,已作廢) | sha 對 main · 自測 10/10 |
| 2026-11-21T01:53:46Z | VRN_SystemManager_v0280.py | 0280 | VIA-VRN-MDL359 | e5f205b84aca | 沿用舊冊 / 舊參數轉已確認 · 規格冊深拷貝 · 唯一替換者 | 自測 12/12 · 交接案收據 · 串測站 GREEN · 實跑 v0103 記到 v0280 · 再跑不換版 |
| 2026-11-21T01:53:46Z | VRN_Asset_Register_v0103.json | 0103 | (VRN 自己的冊) | 8b045c46a34d | VRN 資產登記 v0103:112 號已確認(VRN 自發)· 規格 1083 筆(含 v0280) | 由 VRN 管理器 v0280 實跑寫出 |
| 2026-11-21T02:09:15Z | VDF_SSOTSync_v0103.py | 0103 | VIA-VDF-MDL300 | 0f0ec0f48f22 | VDF 自己發號定案(不等 VCGC 核號) | 自測 7/7 · 交接案收據 · 串測站 GREEN · 實跑 495 條全部已確認 · 再跑不換版 |
| 2026-11-21T02:09:15Z | VDF_SSOT_Register_v0113.json | 0113 | (VDF 自己的帳) | 76c11fe70cac | VDF 帳本 v0113:495 條已確認(VDF 自發 12 · 先前 VCGC 核發 483 照留)· 號與 ssot_id 不變 | 由 VDF_SSOTSync v0103 實跑寫出 |
| 2026-11-21T02:15:58Z | VDF_SSOTSync_v0103.py | 0103 | VIA-VDF-MDL300 | b33e5b2cb214 | Codex P2:VDF 自發條目內容有變也升 semver | 自測 8/8 · 交接案收據 · 串測站 GREEN · 真倉 sync 無變更 |
| 2026-11-21T02:21:49Z | VDF_SSOTSync_v0103.py | 0103 | VIA-VDF-MDL300 | 0f0ec0f48f22 | 還原為已合併位元(同 main);取代本線 02:15:58 那列(那列雜湊是合併後就地改的內容,作廢) | sha 對 main · 自測 7/7 |
| 2026-11-21T02:21:49Z | VDF_SSOTSync_v0104.py | 0104 | VIA-VDF-MDL301 | af0c0fc65003 | VDF 自發條目內容有變也升 semver(PR #705 Codex P2) | 自測 8/8 · 交接案收據 · 串測站 GREEN |
| 2026-11-21T02:57:45Z | VDF_MDL009_TWStockList_v0105.py | 0105 | VIA-VDF-MDL302 | 11b2ec223085 | 前版鏈網路入口轉到尾版(MDL010 替身注入恢復) | 自測 5/5 · MDL010 照過 · 交接案收據 · 串測站 GREEN |
| 2026-11-21T02:57:45Z | VDF_MDL012_FetchGroups_v0111.py | 0111 | VIA-VDF-MDL303 | ec30c7797d27 | 族群冊升版不再讓舊斷言紅(前版鏈冊釘 v0102 · 現役冊驗內容) | 自測 4/4 · 前版鏈全照過 · 交接案收據 · 串測站 GREEN |
| 2026-11-21T03:40:00Z | VDF_MDL008_FetchSystem_v0111.py | 0111 | VIA-VDF-MDL304 | c7cd2a4ed403 | live 改道收 requests 兩段 timeout(akshare 1.20 預設 (10, 60) 不再 int(tuple) 失敗) | 自測 7/7 · 深測前版鏈 v0108–v0111 照過 · 真網路 175 列 · 交接案收據 · 串測站 GREEN |
| 2026-11-21T03:40:00Z | VDF_MDL011_AkshareFetcher_v0105.py | 0105 | VIA-VDF-MDL305 | e2e0bd340e66 | 快照 TTL 逐函式覆寫(選單 v0101 統計局 168h · 平常增量不再整批重抓) | 自測 9/9 · 前版鏈 v0104 → v0102 照過 · 交接案收據 · 串測站 GREEN |
| 2026-11-21T07:05:19Z | VDF_ENG232_TWIndexOfficial_v0107.py | 0107 | VIA-VDF-ENG391 | 14428e6d42bc | 加權休市段不判洞(櫃買交易日曆) | 自測 10/10 · 真庫:春節段 EMPTY 往下 · 2025-02 +19 · 03 +21 · 與櫃買日對齊 |
| 2026-11-21T07:05:19Z | VDF_ENG066_GlobalUniverse_v0103.py | 0103 | VIA-VDF-ENG390 | 693267f372e4 | 空庫先建 global_daily | 自測 8/8 · 真庫:177,712 列 · 78 檔 · 2018-01-01 → 2026-11-20 |
| 2026-11-21T07:05:19Z | VDF_MDL022_SafeParallelLaunch_v0107.py | 0107 | VIA-VDF-MDL306 | e9e65e364ad1 | 補標準網路橋 | 自測 5/5 · 前版 11/11 |
| 2026-11-21T07:05:19Z | VDF_MDL022_SafeParallelLaunch_v0108.py | 0108 | VIA-VDF-MDL309 | 89c046124ad0 | run 後自動官方對帳 | 自測 9/9 |
| 2026-11-21T07:05:19Z | VDF_MDL012_FetchGroups_v0112.py | 0112 | VIA-VDF-MDL308 | 43d2c187f542 | 並行道套擷取冊列 env(VAKE 回資料家) | 自測 8/8 · 前版鏈照過 |
| 2026-11-21T07:05:19Z | VDF_MDL008_FetchSystem_v0112.py | 0112 | VIA-VDF-MDL307 | d9f80680c84e | --home 轉絕對路徑 | 自測 6/6 · fixture 子行程落指定夾 |
| 2026-11-21T07:05:19Z | VDF_ENG057_TradingValueBackfill_v0113.py | 0113 | VIA-VDF-ENG392 | 6b6aebf2585f | 交易日曆 ∪ 官方指數日 | 自測 9/9 |
| 2026-11-21T07:05:19Z | VDF_MDL032_TWPriceReconcile_v0100.py | 0100 | VIA-VDF-MDL310 | bfc90ee6320b | 台股日價官方對帳(官方值覆蓋) | 自測 11/11 · 資料家實跑 GREEN · 抽驗 5 檔與官方逐欄相同 |
| 2026-11-21T07:16:31Z | VDF_MDL032_TWPriceReconcile_v0101.py | 0101 | VIA-VDF-MDL311 | f476802fd184 | 刪休市佔位要官方指數日曆證明(Codex P1) | 自測 10/10 · 真庫乾跑冪等 |
| 2026-11-21T07:27:55Z | VRN_ENG049_ContentReconcile_v0106.py | 0106 | VIA-VRN-ENG339 | c7a26b2c7382 | 矩陣 ADJ CLOSE 讀 VDF 官方對帳後日價 | 自測 9/9 · ADJ CLOSE 38/42 · 綠 8 |
| 2026-11-21T10:24:53Z | VIA_RepoSafeSync_v0100.py | 0100 | VIA-CORE-MDL879 | 19153a22cec2 | 桌機倉安全快轉(擋路同名檔先備份 · main 為準) | 自測 10/10 · 桌機版本容器重現快轉成功 |
| 2026-11-21T10:24:53Z | VIA_VCGC_ApplyRun_v0108.py | 0108 | VIA-CORE-MDL880 | 11899a37e924 | go 先安全同步再跑(更新後尾版重跑) | 自測 9/9 |
| 2026-11-21T10:52:00Z | VIA_RepoSafeSync_v0101.py | 0101 | VIA-CORE-MDL881 | 6cc0c7cd5fa1 | 桌機倉安全快轉 v0101(被忽略檔 · 暫存區 · -z 路徑) | 自測 9/9 |
| 2026-11-21T11:04:00Z | VIA_RepoSafeSync_v0102.py | 0102 | VIA-CORE-MDL882 | 3d50b8e42bc2 | 桌機倉安全快轉 v0102(祖孫衝突 · 備份兩夾 · 符號連結) | 自測 10/10 |
| 2026-11-21T11:22:00Z | VIA_RepoSafeSync_v0103.py | 0103 | VIA-CORE-MDL883 | e2b0a0ee28da | 桌機倉安全快轉 v0103(失敗就停 · 巢狀倉 · 連結 manifest · 大小寫) | 自測 11/11 |
| 2026-11-21T11:26:00Z | VIA_RepoSafeSync_v0104.py | 0104 | VIA-CORE-MDL884 | e300a053908d | 桌機倉安全快轉 v0104(pathspec 照字面) | 自測 9/9 |
| 2026-11-21T11:46:00Z | VIA_RepoSafeSync_v0105.py | 0105 | VIA-CORE-MDL885 | 0c89652eed1d | 桌機倉安全快轉 v0105(檔名位元組原樣 · 找不到就停) | 自測 11/11 |
| 2026-11-21T15:50:00Z | VDF_ENG240_SP500SectorWeight_v0101.py | 0101 | VIA-VDF-ENG393 | fe11d3eef398 | ENG240 --selftest 薄尾 | 自測 4/4 |
| 2026-11-21T15:50:00Z | VDF_Engine_aaii_sentiment.py | — | (VDF-REQ043) | d443a0613479 | AAII 走網路工具 + 官方 xls 來源 | AST 加速器匯入 + 載入 |
| 2026-11-21T15:50:00Z | VDF_Engine_cnn_fear_greed_proxy.py | — | (VDF-REQ043) | 5361e80f80c2 | CNN 代理 yfinance 先過雙閘 | AST 加速器匯入 + 載入 |
| 2026-11-21T17:05:00Z | VDF_SystemManager_v0188.py | 0188 | VIA-VDF-MDL312 | 40290aa44c01 | VDF monitor 九格(唯讀動詞 + DuckDB / parquet 收據 · 鎖定模板頁) | 自測 12/12 |
| 2026-11-21T17:05:00Z | VRN_SystemManager_v0281.py | 0281 | VIA-VRN-MDL360 | 5319601f841c | VRN monitor 九格(VRN-2 收據 + 零寫入動詞 · 鎖定模板頁) | 自測 11/11 |
| 2026-11-21T18:00:00Z | VDF_SystemManager_v0189.py | 0189 | VIA-VDF-MDL313 | 91838426564f | VDF monitor 每格看自己的收據年齡(含 parquet) | 自測 10/10 |
| 2026-11-21T18:00:00Z | VRN_SystemManager_v0282.py | 0282 | VIA-VRN-MDL361 | 07a0bed08e80 | VRN monitor 每格看自己的收據年齡 | 自測 9/9 |
| 2026-11-21T18:00:00Z | VDF_Engine_aaii_sentiment.py | — | (VDF-REQ043) | 7f205065e65e | 還原 main 原位元組(PR 712 Codex P1:修改開新版;AAII 由 ENG116 負責) | 位元與 main 相同 |
| 2026-11-21T18:00:00Z | VDF_Engine_cnn_fear_greed_proxy.py | — | (VDF-REQ043) | 05c96473bcb1 | 還原 main 原位元組(PR 712 Codex P1) | 位元與 main 相同 |
| 2026-11-21T18:45:00Z | VDF_SystemManager_v0190.py | 0190 | VIA-VDF-MDL314 | d574c641402b | VDF monitor 心跳 · 逐動詞起訖 · 單支時限 | 自測 8/8 |
| 2026-11-21T17:25:00Z | VRN_SystemManager_v0283.py | 0283 | VIA-VRN-MDL362 | 7bd0c95a09c3 | VRN launch 走 TEMP · 起跑前備份 · resources | 自測 21/21 |
| 2026-11-21T17:45:00Z | VDF_SystemManager_v0191.py | 0191 | VIA-VDF-MDL315 | 370d539518c9 | VDF monitor --json 只留 JSON | 自測 8/8 |
| 2026-11-21T17:50:00Z | VRN_SystemManager_v0284.py | 0284 | VIA-VRN-MDL363 | d030b13fb5dc | Graphify 看 VRN 自己的燈 · 備份驗過才發布 | 自測 17/17 |
| 2026-11-21T18:00:00Z | VRN_SystemManager_v0285.py | 0285 | VIA-VRN-MDL364 | 00682bf75c65 | VRN 備份串行化(檔案鎖) | 自測 13/13 |
| 2026-11-22T03:50:00Z | VRN_MDL002_LayoutExtractor_v0101.py | 0101 | VIA-VRN-MDL365 | c51224477ac7 | VRN MDL002 7 處 bare except 改 except Exception | 自測 10/10 |
| 2026-11-22T03:50:00Z | VDF_MDL004_TWFullMarketEngine_v0101.py | 0101 | VIA-VDF-MDL316 | 32b557a90b39 | VDF MDL004 2 處 bare except 改 except Exception | 自測 10/10 |
| 2026-11-22T03:40:00Z | SUP_MDL866_VIAUnifiedNLPOrchestrator_v0109.py | 0109 | VIA-SUP-MDL1205 | 3df95cb227fb | NLP 收件整合四動詞(收容夾只讀;合併前依 Codex P2 重鎖) | 自測 21/21 |
| 2026-11-22T04:44:00Z | VRN_SystemManager_v0286.py | 0286 | VIA-VRN-MDL367 | a153a7f84dc7 | 版本 / 健康看現役尾版與整條鏈 · help 補齊 · verbs · 掃描快取 | 自測 20/20 |
| 2026-11-22T05:14:00Z | VRN_SystemManager_v0287.py | 0287 | VIA-VRN-MDL368 | e77f953123d0 | version / health --json 合法 JSON(v0286 鎖定不動)| 自測 13/13 |
| 2026-11-22T06:57:00Z | VIA_FastRun_v0100.py | 0100 | VIA-CORE-MDL886 | 9e612b99d8c6 | 快跑器:VCGC 一次 · 並行 · 一行輸出 | 自測 15/15 |
| 2026-11-22T07:09:00Z | VIA_FastRun_v0101.py | 0101 | VIA-CORE-MDL887 | 3f0e2eba0e9d | 快跑器:失敗不能是綠(v0100 鎖定不動)| 自測 9/9 |
| 2026-11-22T08:06:00Z | VIA_DailyBackup_v0102.py | 0102 | VIA-CORE-MDL888 | eceea946bd06 | 每日備份加 Graphify / OmniRoute | 自測 9/9 |
| 2026-11-24T05:40:00Z | VIA_ReworkGuard_v0100.py | 0100 | VIA-CORE-MDL890 | 1af3dddd37f8 | 重工守門 13 類 · 解法內建 | 自測 16/16 |
| 2026-11-24T05:40:00Z | VRN_SystemManager_v0289.py | 0289 | VIA-VRN-MDL374 | 32d7edf95e46 | 自測提速 · bridges 語法樹 | 自測 11/11 |
| 2026-11-24T06:35:00Z | VIA_ReworkGuard_v0101.py | 0101 | VIA-CORE-MDL891 | ea9589b5c317 | 重工守門:真分支誤判修正(v0100 鎖定不動)| 自測 10/10 |
| 2026-11-24T05:25:00Z | VIA_ReworkGuard_v0102.py | 0102 | VIA-CORE-MDL892 | 5b51476924f1 | 重工守門:撞號比正式身分(v0100 · v0101 鎖定不動)| 自測 9/9 |
| 2026-11-24T08:10:00Z | VCGC_CommandHub_v0105.py | 0105 | VIA-CORE-MDL893 | 1fc5d88ff64a | 中樞:#730 照實燈改發(v0101–v0104 不動)| 自測 11/11 |
| 2026-11-24T08:40:00Z | VCGC_CommandHub_v0106.py | 0106 | VIA-CORE-MDL894 | 90e7031e5a4b | 中樞:短指令與選單接到 v0105(v0101–v0105 不動)| 自測 6/6 + 前版 11/11 |
| 2026-11-24T08:05:00Z | VCGC_CommandHub_v0107.py | 0107 | VIA-CORE-MDL895 | d66242bd6032 | 中樞:資料根 ≠ 程式樹時找得到工具(v0101–v0106 不動)| 自測 6/6 + 前版 6/6 · 11/11 |
| 2026-11-24T08:40:00Z | VCGC_CommandHub_v0108.py | 0108 | VIA-CORE-MDL896 | 04b979eb2821 | 中樞:收據從工具所在的根讀(v0101–v0107 不動) | 自測 5/5 + 前版 |
| 2026-11-24T08:40:00Z | VRN_ENG397_P1Segment_v0130.py | 0130 | VIA-VRN-ENG341 | 8dd1d5ed4848 | VRN 擷取還原量測 fidelity(v0129 不動) | 自測 7/7 + 前版 35/35 |
| 2026-11-24T09:00:00Z | VCGC_CommandHub_v0109.py | 0109 | VIA-CORE-MDL897 | dab7181eceba | 中樞:找工具與讀收據分開(v0101–v0108 不動) | 自測 4/4 + 前版 |
| 2026-11-24T09:00:00Z | VRN_ENG397_P1Segment_v0131.py | 0131 | VIA-VRN-ENG342 | 70256c10656f | VRN fidelity 兩處量測修正(v0129 · v0130 不動) | 自測 5/5 + 前版 |
| 2026-11-24T09:50:00Z | VCGC_CommandHub_v0110.py | 0110 | VIA-CORE-MDL898 | 4bfcdb627869 | 中樞:doctor 總表不再崩潰(v0101–v0109 不動)| 自測 4/4 + 前版 |
| 2026-11-24T10:35:00Z | VIA_FastRun_v0102.py | 0102 | VIA-CORE-MDL899 | 36df686bd210 | 快跑器:env · fidelity · 動態進度條(v0100 · v0101 不動)| 自測 8/8 + 前版 9/9 |
| 2026-11-24T11:00:00Z | VIA_HostBoot_v0100.py | 0100 | VIA-CORE-MDL900 | b246e6a9f911 | 桌機啟動器:git 同步改在 Python | 自測 6/6 |
| 2026-11-24T11:30:00Z | VIA_FastRun_v0103.py | 0103 | VIA-CORE-MDL901 | bb103eb99975 | 心跳不溢位 · env 提速 | 自測 8/8 + 前版 8/8 |
| 2026-11-24T11:30:00Z | VCGC_CommandHub_v0111.py | 0111 | VIA-CORE-MDL902 | e34f917bf5d8 | via-health 短令 | 自測 5/5 + 前版鏈 v0110~v0105 全過 |
| 2026-11-24T13:30:00Z | CGC_MDL056_InstallGate_v0105.py | 0105 | VIA-VCGC-MDL1708 | 44b098423c1f | 三鏡像查衝突 · 依計畫安裝 | 自測 11/11 |
| 2026-11-24T13:30:00Z | VCGC_CommandHub_v0112.py | 0112 | VIA-CORE-MDL903 | 2759245f8bda | via-install 先查再裝 | 自測 6/6 + 前版鏈全過 |
| 2026-11-24T13:30:00Z | VIA_FastRun_v0104.py | 0104 | VIA-CORE-MDL904 | f9ed53db78d0 | env 組照規範 | 自測 6/6 + 前版 8/8 |
| 2026-11-24T13:30:00Z | VRN_ENG397_P1Segment_v0132.py | 0132 | VIA-VRN-ENG343 | 7f3e0cc3bd1d | 橋 OCR 一頁一批 | 自測 5/5 + 前版 5/5 |
| 2026-11-24T14:10:00Z | VCGC_CommandHub_v0113.py | 0113 | VIA-CORE-MDL905 | 991ceee73aef | 舊名照原意 | 自測 4/4 |
| 2026-11-24T15:20:00Z | VDF_MDL020_DataPlane_v0104.py | 0104 | VIA-VDF-MDL318 | c04457beda85 | parquet 對齊 DataFrame | 自測 6/6 |
| 2026-11-24T15:20:00Z | VDF_ENG053_ParamEngineMap_v0105.py | 0105 | VIA-VDF-ENG397 | f249cc3ad5be | 起始日 2018 自測 | 自測 5/5 |
| 2026-11-24T16:10:00Z | VIA_FastRun_v0105.py | 0105 | VIA-CORE-MDL906 | 4732ba7dcff6 | 前置檢查要新鮮 | 自測 5/5 + 前版鏈 |
| 2026-11-24T16:10:00Z | CGC_MDL056_InstallGate_v0106.py | 0106 | VIA-VCGC-MDL1709 | 9d6c97e1f3b5 | 計畫綁環境 | 自測 5/5 + 前版 11/11 |
| 2026-11-24T16:40:00Z | VCGC_CommandHub_v0114.py | 0114 | VIA-CORE-MDL907 | d065f9471a11 | install 只用這一輪的計畫 | 自測 5/5 + 前版鏈 |
| 2026-11-24T15:35:00Z | VIA_ReworkGuard_v0103.py | 0103 | VIA-CORE-MDL908 | c036e1f99084 | R11 不誤判工具檔名 | 自測 6/6 + 前版鏈 |
| 2026-11-24T15:55:00Z | CGC_MDL056_InstallGate_v0107.py | 0107 | VIA-VCGC-MDL1710 | b3cbd60f99a9 | 照計畫目標裝 | 自測 5/5 + 前版鏈 |
| 2026-11-24T16:45:00Z | VCGC_StartupEngine_v0100.py | 0100 | VIA-VCGC-MDL1711 | 8f6ca058b2ee | 啟動引擎 9 項修正 | 自測 62/62 |
| 2026-11-24T17:05:00Z | VCGC_StartupEngine_v0100.py | 0100 | VIA-VCGC-MDL1711 | 9fcbcf825d49 | 演練不算完成 · INCOMPLETE | 自測 65/65 |
| 2026-11-24T17:15:00Z | VCGC_StartupEngine_v0100.py | 0100 | VIA-VCGC-MDL1711 | 4ebfedeadf31 | 典籍綁指紋 · 演練標記照留 | 自測 67/67 |
| 2026-11-24T17:23:10Z | VCGC_StartupEngine_v0100.py | 0100 | VIA-VCGC-MDL1711 | b98a26696abb | 前置換了下游作廢 · 混單先拒絕 | 自測 69/69 |
| 2026-11-24T17:55:00Z | VCGC_CommandHub_v0115.py | 0115 | VIA-CORE-MDL909 | 046c6507766e | via-graph · via-bak 子動詞 | 自測 6/6 |
| 2026-11-24T17:55:00Z | VIA_DailyBackup_v0103.py | 0103 | VIA-CORE-MDL910 | 40c5c2e4f433 | 還原先驗證 · 備份卡 | 自測 10/10 |
| 2026-11-24T18:05:00Z | VIA_DailyBackup_v0103.py | 0103 | VIA-CORE-MDL910 | 4f961277ce1d | 真入口保留範圍 · 空選擇回紅 | 自測 12/12 |
| 2026-11-24T18:45:00Z | VCGC_StartupEngine_v0101.py | 0101 | VIA-VCGC-MDL1712 | 2189da877a6c | 典籍鎖 · 唯一暫存檔 | 自測 73/73 |
| 2026-11-25T03:10:00Z | VCGC_CommandHub_v0116.py | 0116 | VIA-CORE-MDL911 | 838a506ab22b | 長跑心跳 · Ctrl+C 收樹 | 自測 6/6 |
| 2026-11-25T04:45:00Z | VIA_RepoSafeSync_v0106.py | 0106 | VIA-CORE-MDL912 | fcc4ce307770 | 四階段進度 · 真實 % | 自測 8/8 |
| 2026-11-25T04:45:00Z | VCGC_CommandHub_v0117.py | 0117 | VIA-CORE-MDL913 | 22511ba7af7b | 建圖進度條 · 估 % | 自測 6/6 |
| 2026-11-25T05:05:00Z | VIA_RepoSafeSync_v0106.py | 0106 | VIA-CORE-MDL912 | 16ce248d044c | 階段界線 · 照實收尾 · 備份心跳 | 自測 11/11 |
| 2026-11-27T02:45:00Z | VCGC_CommandHub_v0122.py | 0122 | VIA-CORE-MDL917 | 532eaff904b3 | via-graph 路由 · 舊名照原意 | 自測 7/7 |
| 2026-11-27T07:45:00Z | VIA_HostBoot_v0107.py | 0107 | VIA-CORE-MDL918 | ef5fac720be7 | up 三步同時 | 自測 7/7 |
| 2026-11-27T08:20:00Z | VIA_VCGC_ToolModules_v0100.py | 0100 | VIA-SUP-MDL1208 | 68d9623e3906 | 導入補強工具模組 | 自測 2/2 · 回歸 34 |
| 2026-11-27T12:45:00Z | CGC_MDL245_SDDValidator_v0110.py | 0110 | VIA-VCGC-MDL1724 | f1f390716183 | 主機實跑步對事件帳(match_args) | 自測 12/12 |
| 2026-11-27T12:45:00Z | VIA_Workflow_VCGC_SSOT_v0166.json | 0166 | — | 479f44b50d3b | WKF056 欄位 · 主機步用事件帳 | X-COL 綠 · STP003 NOT_RUN |
| 2026-11-27T13:10:00Z | CGC_MDL245_SDDValidator_v0110.py | 0110 | VIA-VCGC-MDL1724 | b650660acd1f | 同版修正後重鎖:參數要連在一起 | 自測 14/14 |
| 2026-11-27T13:10:00Z | VIA_Workflow_VCGC_SSOT_v0166.json | 0166 | — | fbe7f6ec0f3f | 同版修正後重鎖:STP003 要 --system VDF | X-COL 綠 |
| 2026-11-27T14:30:00Z | CGC_MDL237_NumberingSystem_v0124.py | 0124 | VIA-VCGC-MDL1725 | b8de710e4d13 | 需求號對齊冊上代碼 | 自測 20/20 · 三個 0 |
| 2026-11-27T14:30:00Z | VIA_Numbering_Realign_Ledger_v0100.jsonl | 0100 | — | 2fe326721192 | 對齊帳 14 列 | 已套用 14 / 14 |
| 2026-11-27T15:00:00Z | CGC_MDL237_NumberingSystem_v0124.py | 0124 | VIA-VCGC-MDL1725 | 06cfbb469845 | 同版修正後重鎖:audit 只放行帳上那一步 | 自測 23/23 |
| 2026-11-27T15:30:00Z | CGC_MDL237_NumberingSystem_v0124.py | 0124 | VIA-VCGC-MDL1725 | d44a5de09b38 | 同版修正後重鎖:原主要在目的地 | 自測 24/24 |
| 2026-11-27T15:50:00Z | CGC_MDL237_NumberingSystem_v0124.py | 0124 | VIA-VCGC-MDL1725 | 93fabd070903 | 同版修正後重鎖:退役列的號算佔用 | 自測 25/25 |
| 2026-11-27T14:34:00Z | CGC_MDL230_ToolCoverageProbe_v0108.py | 0108 | VIA-VCGC-MDL1726 | 831ae7d2edf0 | 自測改在暫存樹上比對;真樹整鏈對照改 --selftest --full | 自測 13/13 |
| 2026-11-27T14:45:00Z | CGC_MDL230_ToolCoverageProbe_v0108.py | 0108 | VIA-VCGC-MDL1726 | 3ba4ca34bb27 | 同版修正後重鎖:只認 --selftest 旗標 | 自測 13/13 |
| 2026-11-27T15:13:50Z | CGC_MDL149_VeritasCentralGovernanceConsole_v0203.py | 0203 | VIA-VCGC-MDL1727 | a6f5337702e2 | 元件掃描同名兩份登正本 | 自測 16/16 |
| 2026-11-27T15:13:50Z | CGC_MDL245_SDDValidator_v0111.py | 0111 | VIA-VCGC-MDL1728 | 2fae1238d0e3 | X-REG 分開步釘前版與註冊冊落後 | 自測 12/12 |
| 2026-11-27T15:43:03Z | CGC_MDL245_SDDValidator_v0112.py | 0112 | VIA-VCGC-MDL1729 | 5835ae2e39f9 | X-REG:已退役的步不要求正主註冊 | 自測 11/11 |
| 2026-11-27T16:52:36Z | CGC_MDL140_HandoverConsole_v0112.py | 0112 | VIA-VCGC-MDL1730 | 464fe45626a8 | 有退役清冊的搬移不算 FILE_REMOVED | 自測 12/12 |
| 2026-11-27T18:15:27Z | CGC_SystemManager_v0122.py | 0122 | VIA-VCGC-MDL1731 | 3f8c1ed8379a | launch:VCGC 一鍵啟用 | 自測 19/19 |
| 2026-11-27T18:15:27Z | Start-VCGC-v0101.ps1 | 0101 | VIA-CORE-MDL924 | e31eb06de447 | 一支 PS 啟用 VCGC(只認主工作倉) | 主機起跑 |
| 2026-11-27T19:32:46Z | CGC_SystemManager_v0123.py | 0123 | VIA-VCGC-MDL1732 | a1fb3768d1f0 | launch 總燈與三數照實 | 自測 13/13 |
| 2026-11-27T19:45:36Z | CGC_SystemManager_v0124.py | 0124 | VIA-VCGC-MDL1733 | 0514e62930e6 | 容器跑的 launch 最多黃 | 自測 10/10 |
| 2026-11-27T19:58:19Z | CGC_SystemManager_v0125.py | 0125 | VIA-VCGC-MDL1734 | d358611cb50b | launch 的 NEXT 也看 overview | 自測 11/11 |
| 2026-11-27T20:31:36Z | CGC_MDL140_HandoverConsole_v0113.py | 0113 | VIA-VCGC-MDL1735 | f281d6124a00 | 舊案不計入現況燈 · 兩系統範圍 | 自測 19/19 |
| 2026-11-27T21:54:32Z | VIA_HostBoot_v0108.py | 0108 | VIA-CORE-MDL928 | 25e159740b0c | 一支 PY 同時啟用 VCGC 與 VDF | 自測 12/12 |
| 2026-11-27T22:07:42Z | VIA_HostBoot_v0109.py | 0109 | VIA-CORE-MDL929 | 54f07ee702d3 | 一鍵啟用也用網路模組 | 自測 11/11 |
| 2026-11-27T22:24:15Z | VIA_HostBoot_v0110.py | 0110 | VIA-CORE-MDL930 | dd068af048fe | 監工不卡死 · 三數照三道 | 自測 9/9 |
| 2026-11-28T01:56:42Z | CGC_MDL183_CeleritasPolicyGate_v0107.py | 0107 | VIA-VCGC-MDL1738 | 8ce0cc1c81b3 | 加速器政策閘照裁定甲:18 支既有 PS · 前版鏈 PY 2 支列帳,帳外照紅 | 自測 7/7 ×3 · handoff test rc 0 |
| 2026-11-28T01:56:42Z | CGC_MDL058_Lessons_v0104.py | 0104 | VIA-VCGC-MDL1736 | 747fd0f1e281 | 教訓帳自測不吃本機帳(暫存合成帳)· 明寫轉出跨行程鎖 | 自測 5/5 ×3 · handoff test rc 0 |
| 2026-11-28T01:56:42Z | CGC_MDL256_SubsystemBundle_v0102.py | 0102 | VIA-VCGC-MDL1739 | ae18154a4be8 | 下載包認退役清冊證明(retired 照列) | 自測 5/5 · handoff test rc 0 |
| 2026-11-28T01:56:42Z | CGC_MDL170_VDFChainRunner_v0106.py | 0106 | VIA-VCGC-MDL1737 | dd8c336d7560 | VDF 鏈跑器自測只驗本版與直接前版 · 真樹未審 0 | 自測 6/6 ×3 · handoff test rc 0 |
| 2026-11-28T01:56:42Z | via_bridge_sweeper_v0106.py | 0106 | VIA-VCGC-MDL1740 | 916ea11100a3 | 掃橋器:系統收件夾一律收容件 · 真樹加速缺 0 | 自測 7/7 ×3 · handoff test rc 0 |
| 2026-11-28T01:56:42Z | VIA_WorkbenchLock_v0103.py | 0103 | VIA-CORE-MDL932 | 3d6beb7ae24b | WorkbenchLock 自測只驗本版與直接前版 | 自測 4/4 ×3 · handoff test rc 0 |
| 2026-11-28T01:56:42Z | VIA_LakeMatrix_v0102.py | 0102 | VIA-CORE-MDL931 | eb693645be7f | LakeMatrix 自測時鐘凍在夾具時刻 | 自測 5/5 ×3 · handoff test rc 0 |
| 2026-11-28T02:05:20Z | VIA_WorkbenchLock_v0103.py | 0103 | VIA-CORE-MDL938 | 3d6beb7ae24b | 改號(CORE-MDL932 讓給 main 的 GovernanceApply_v0102) | 重號 0 |
| 2026-11-28T07:07:17Z | VDF_MDL004_TWFullMarketEngine_v0104.py | 0104 | VIA-VDF-MDL343 | bea70fb20eae | 前版自測要跑完才容忍舊 ⓪ | 自測 4/4 ×3 |
| 2026-11-28T05:12:23Z | CGC_MDL253_ToolingInventory_v0106.py | 0106 | VIA-VCGC-MDL1741 | 3acf836d6f26 | 工具盤點自測只驗本版與直接前版 · 前版鏈照實寫未跑 | 自測 4/4 ×3 · handoff test rc 0 |
| 2026-11-28T05:12:23Z | SUP_MDL866_VIAUnifiedNLPOrchestrator_v0110.py | 0110 | VIA-SUP-MDL1212 | e1772496e479 | SUP_MDL866 歸 VCGC 後補發中央編號(檔未改) | 尾版 v0111 自測 6/6(含本版 8/8)· handoff test nlp ×2 rc 0 |
| 2026-11-28T06:39:02Z | CGC_MDL149_SourceLane_v0103.py | 0103 | VIA-VCGC-MDL1742 | 28fe5fb91139 | 貼回包不帶市場數值 | 自測 4/4 ×3 |
| 2026-11-28T11:20:00Z | VDF_MDL008_FetchSystem_v0115.py | 0115 | VIA-VDF-MDL387 | 0f24af5b76f5 | 擷取家改寫認得參數橋相對寫法 · 夾具不寫倉內 db/ | 自測 8/8 ×3 · fetch test 23/23 |
| 2026-11-28T11:55:00Z | VDF_MDL020_DataPlane_v0107.py | 0107 | VIA-VDF-MDL388 | 5c4b23677cb0 | 自測只驗本版與直接前版 v0106(裁定甲)· 功能本體 v0104 六檢照跑 | 自測 4/4 ×3 |
| 2026-11-28T11:55:00Z | VDF_MDL022_SafeParallelLaunch_v0114.py | 0114 | VIA-VDF-MDL389 | 1a1d5bb60441 | 自測只驗本版與直接前版 v0113(裁定甲) | 自測 4/4 ×3 |
