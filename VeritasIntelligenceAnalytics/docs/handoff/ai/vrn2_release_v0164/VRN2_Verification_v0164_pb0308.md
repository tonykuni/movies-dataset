# VRN-2 v0164 驗證補記 · 桌機 2026-11-01 03:08 貼回包(RoundAll v0119 · 套件 v0163)分析與 v0164 預演

只記結論(貼回包內容不入倉)。這份貼回包是 v0164 發行**之前**那一輪(Handle-All v0111 · repair · 90 秒)。

## 1. ⑥e「擷取 YELLOW · 跑 10 次 · 失敗 0」的錨點

收據 ⑥e 那格(RoundAll 修正後 · 上一次 ⑤ 重抓 10-31 19:56)的視窗清單,被 300 字截斷前可見:

| 視窗(2025)| 檔數 | rc | 這個視窗裡的報告 |
|---|---|---|---|
| 09-18 ~ 10-04 · 10-04 ~ 10-11 · 05-28 ~ 06-03 · 07-11 ~ 07-17 | 2 · 3 · 1 · 1 | 0 | 其他代號 |
| 08-12 ~ 08-21 | 2 | **2** | 3706(報告 2025-08-22)+ 6873 |
| 09-24 ~ 10-06 | 3 | **2** | 6669(報告 2025-10-01 · 2025-10-07)|
| 11-21 ~ 12-07 | 13 | (截斷)| 3706(報告 2025-11-28 · 2025-11-30)|

- rc 2 = VDF 引擎 `status.json` PARTIAL(MarketFetch 的「失敗」只數 rc 不在 (0, 2) → 失敗 0 但燈黃)。
- rc 2 落在**正好包含 3706 / 6669 報告日的視窗**;其他視窗 rc 0。
- MarketFetch 填值的「MISSING(報告日前沒有日資料 · 需 --start 回補)」= 報告日前沒有 **adj_close 非空**的列;VDF 在 Yahoo 收盤 ≠ TWSE 收盤(CLOSE_MISMATCH → 品質 REVIEW)或 Yahoo 沒那天時不給 adj_close。
  → 3706 / 6669 的 MISSING 與 ⑥e 的 rc 2 是同一件事(資料源:Yahoo 與 TWSE 對不上的日子),不是 VRN-2 抓漏。
- 最新收盤 3706 = 76.8 · 6669 = 1810(2026-10-30 · Yahoo 與 TWSE 一致 · 有 adj_close)。是哪一種(除權 / 分割的追溯調整 → 可同步還原,或資料不一致 → 照舊 MISSING)
  由 v0164 的 ConsensusJoin v0105 讀 VDF 日線分區判定,證據寫 `market\VRN2_TPAdjSync_latest.json`(貼回包會收)。

## 2. 增量庫

累計 FinancialAligned 16588 / Deleted 38 仍在(v0119 / OutputStore v0101 不清)· 輸出冊的 FinancialAligned 已是「無歷史 44」· 市場資料沒有殘留的 MOPS 財報(financial_annual 0 份)。

## 3. RoundAll v0120 在這份狀態上的預演(容器 · 只算不跑)

- ⑤ 計畫:history(⑬b)→ **combined**(ConsensusJoin v0105:TARGET_PRICE(ADJ) 同步還原 + TWSE / TPEX 格式合併)→ **store**(清掉 MOPS 算的列 · 先備份 · 可還原)→ Workbench。
- 收尾頁:⑥e → **資料源**(「VDF 引擎回 rc 2(PARTIAL · 不是失敗)· 填值缺 = 非台股代號 1」)· Combined 的 TARGET_PRICE(ADJ) 缺 → 資料源 · 不再有 VRN-2 未結案項。
- 結論:這份貼回包不需要新版;下一步在桌機跑 v0164(`VRN2_HandleAll_v0112.md` 的 cmd 一行)。
