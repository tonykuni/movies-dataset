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
