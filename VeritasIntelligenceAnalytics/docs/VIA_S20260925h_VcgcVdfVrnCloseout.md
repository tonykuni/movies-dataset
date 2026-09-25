# 2026-09-25h · VCGC / VDF / VRN 收尾

只補「指標寫著、倉上也有」的檔，再量。沒改卡書、沒立版號、沒跑 `registry-sync --apply`、沒跑 `page --publish`、沒設同意閘。

工作站對照的樹就是這倉的 `VeritasIntelligenceAnalytics`。上一輪寫「accelerator/ 與 network/ 沒有那兩支」是目錄探錯，檔在。

## 鎖住

| 處 | 燈 |
| --- | --- |
| VCGC 自測 | 38 過 37。剩下那項是這棵樹沒整棵載，不是該退役 |
| VRN 政策 | 綠。律 10 · lessons 37 |
| VRN 邏輯 | 綠。守門 rc0，指標 53 全在尾版，過期 0、不在 0 |
| VRN 同義字 | 綠。券商閘拒 20 |
| VRN 紀錄 | 綠 |
| VDF 政策 | 綠。釘住 6/6 |
| VDF 因子 | 綠。參數 678，對映引擎 57、參數 317、缺口 6 |
| VDF 橋 | 綠。加速器 40/40，網路 40/40，真擷取缺橋 0 |
| VDF 工具 | 綠。正典位兩支都在，與看到的副本同一份（版本數 1）。沒把旁邊的副本拷進去 |
| VDF 七處 | 7/7 |
| VDF 開機鏈 | `.sh` 與 `.ps1` 各 44 步，同鏈 |

正典位：

- 加速器 `supportive modules/accelerator/VeritasCeleritas.py`（sha12 `464f6c14bf28`，237382 字節）
- 網路 `supportive modules/network/VeritasAegisNexus.py`（sha12 `f5f81f04479d`，203952 字節）
- 橋：`SUP_MDL737_SuperAccelModule_v0106`、`SUP_MDL740_NetUnified_v0114`。引擎不直接 import 這兩支正典（L09）

同意閘是另一件事。檔在，閘仍是關：`VIA_NET_CONSENT` 與 `VIA_SCRAPE_CONSENT` 都沒設。啟動仍是 GATED。L07 不代設。

## 停在這裡，不代修

| 燈 | 為什麼不動 |
| --- | --- |
| VDF 邏輯 STALE | 卡書有一張 `sector_rotation_capital_flow_engine` 在 `candidates/`，不算尾版。另 5 支沒有版號。不手改卡書、不代立版號 |
| VDF / VRN 交接 STALE | 一頁是批715，律冊是批2026。這棵樹不齊，不發佈 |
| VDF 啟動 GATED | 同意閘沒開。工具燈綠不等於閘開了 |
| VRN 因子 NODATA | AllInOne 在收容子夾。不把收容件拷出來 |
| VRN 樣本 ABSENT | 路徑是工作站 `C:\` 測試樣本，這裡沒有 |
| 兩邊引擎鏈 NODATA | 存證不入倉。沒跑過就不編一份 |
| 加速器控制面 NODATA | `VIA_Reports` 不入倉。要 `via-accel-check` 跑過才有 |

兩邊 rc 仍是 1。綠的那幾盞不回頭改。
