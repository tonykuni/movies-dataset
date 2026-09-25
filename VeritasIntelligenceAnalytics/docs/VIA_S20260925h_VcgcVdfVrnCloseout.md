# 2026-09-25h · VCGC / VDF / VRN 收尾

只補「指標寫著、倉上也有」的檔，再量。沒改卡書、沒立版號、沒跑 `registry-sync --apply`、沒跑 `page --publish`、沒設同意閘。

## 鎖住

| 處 | 燈 |
| --- | --- |
| VCGC 自測 | 38 過 37。剩下那項是這棵樹沒整棵載，不是該退役 |
| VRN 政策 | 綠。律 10 · lessons 37 |
| VRN 邏輯 | 綠。守門 rc0，指標 53 全在尾版，過期 0、不在 0。上一輪不在的那一支是 `vrn_method_kernel_v0102.py`，補上後轉綠 |
| VRN 同義字 | 綠。券商閘拒 20 |
| VRN 紀錄 | 綠 |
| VDF 政策 | 綠。釘住 6/6 |
| VDF 因子 | 綠。參數 678，對映引擎 57、參數 317、缺口 6 |
| VDF 橋 | 綠。加速器 40/40，網路 40/40，真擷取缺橋 0 |
| VDF 七處 | 7/7 |
| VDF 開機鏈 | `.sh` 與 `.ps1` 各 44 步，同鏈 |

## 停在這裡，不代修

| 燈 | 為什麼不動 |
| --- | --- |
| VDF 邏輯 STALE | 卡書有一張 `sector_rotation_capital_flow_engine` 在 `candidates/`，不算尾版。另 5 支沒有版號。接口規定不手改卡書、不代立版號 |
| VDF 工具 ABSENT | 正典位 `accelerator/` 與 `network/` 倉上沒有那兩支檔。不把旁邊的副本拷進去當正典 |
| VDF / VRN 交接 STALE | 一頁是批715，律冊是批2026。要 `via-vcgc page --publish`，這棵樹不齊，不發佈 |
| VDF 啟動 GATED | `VIA_NET_CONSENT` 沒設。L07 不代設 |
| VRN 因子 NODATA | AllInOne 在收容子夾，不在接口要的那一層。不把收容件拷出來 |
| VRN 樣本 ABSENT | 路徑是工作站 `C:\` 測試樣本，這裡沒有 |
| 兩邊引擎鏈 NODATA | `VDFCHAIN_latest.json` 等存證不入倉。沒跑過就不編一份 |
| 參數冊仍缺 | 剩下的是別本冊，沒在這次指標裡。不另開一條補檔路 |

兩邊 rc 仍是 1。綠的那幾盞不回頭改。
