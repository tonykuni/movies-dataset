# VRN-2 v0164 驗證補記 · 桌機 2026-11-01 04:11 實跑結果(Handle-All v0112 · RoundAll v0120 · 套件 v0164 · repair · 74 秒)

只記結論(桌機輸出不入倉)。來源:操作員貼回的主控台與收尾頁文字(貼回包 04:11 未上傳)。

| 項目 | 桌機結果 | 判定 |
|---|---|---|
| 開機鏈 | `[GREEN] boot: Handle-All v0112 SHA-256 OK` · RoundAll v0120 `860cdd5b5fd4` 相符 · 套件 v0164 `84834e330fac` 11 檔逐檔相符 | 過 |
| ⑤ 計畫 | ⑬b → combined(ConsensusJoin v0105)→ store(清 MOPS 列 · 備份)→ Workbench(與 03:08 貼回包的容器預演一致)| 過 |
| 增量庫 MOPS 列 | 清掉 FinancialAligned 4584 · Deleted 38(備份夾 `_mops_purge_20261101_041125` · 可 restore-purge)· 累計 FinancialAligned 16588 → 12004 · Deleted 38 → 0 · 其他冊不動 | 過(與容器桌機規模模擬 12004 / 0 相同)|
| TARGET_PRICE(ADJ) 同步還原 | 補 5 · 仍缺 0(SYNC_YAHOO_RATIO 5)= 3706 ×3 · 6669 ×2 · Combined 的 TARGET_PRICE(ADJ) 空格 15 → 10(9 原文沒有目標價 · 1 AAPL 非台股)| 過(比值 / 日期證據在 `market\VRN2_TPAdjSync_latest.json` · 待貼回包核)|
| ⑥e 錨點 | VDF status.json PARTIAL · 日線品質 COMPLETE 624 / REVIEW 26 / PARTIAL 10 · CLOSE_MISMATCH 3706 19 列(2025-08-12 ~ 2025-12-05)· 6669 7 列(2025-09-24 ~ 2025-10-03)| 收尾頁歸資料源(不再是 VRN-2 未結案)|
| 兩家中位數 / TWSE / TPEX 格式 | FactSet 中位數 48 · YFinance 中位數 47 並存 · tw_consensus 40 · tw_consensus_estimate 320 · tw_market_consensus 40(40 檔都配到 TWSE / TPEX 價)· 增量庫 MarketConsensus 40 | 過 |
| 收尾 | **REVIEW** · VRN-2 0 · VCGC 0 · 人工 2(MQ-1560 影像頁 4 點 OCR_PENDING · 輸出冊缺項 3 份)· 資料源 3(⑥e PARTIAL · Combined 空格 · 市場資料 MISSING 1 = AAPL)| VRN-2 側可結案 |

還沒做到的:
- 這輪是 repair,收據仍沿用啟動器 v0158 的 `VRN2_Closeout_v0158.json`。
- ⑤b 的 SSOT 請求仍是「提案 9」:提案冊 v0101(新 8 條)要等整輪跑啟動器 v0164 時才放進 functional modules\VRN2 並送出。
- 下一步:整輪(`set "VRN2_MODE=full"` 再貼同一條 cmd 一行)· 上傳 04:11 或整輪後的貼回包,核 5 筆同步還原的比值是否對得上除權 / 分割事件。
