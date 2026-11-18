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
