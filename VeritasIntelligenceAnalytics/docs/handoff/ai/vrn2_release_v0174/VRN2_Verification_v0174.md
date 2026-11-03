# VRN-2 v0174 驗證紀錄(2026-11-03 · Workbench v0108:ENG049 視覺模板鎖定 · 時效 / Ticker / YFinance + Name / 券商縮寫 / YYYY 日期 / Source · 套件 v0174 · RoundAll v0130 · Handle-All v0122)

## 1. 操作員要求 → 做法

| 要求 | Workbench v0108(v0107 薄尾 · `window.VRN2_DATA` 一字不改)|
|---|---|
| Ticker Symbol / 股票代號 → Ticker / YFinance · 同步顯示 · 代號下一欄接 Name | 資料頁每一冊:「Ticker / YFinance」一欄(2330 / 2330.TW)· 下一欄一定是 Name(沒有 NAME 的冊用 Combined 合併名稱補)|
| Broker 英文縮寫 | KGI · GS · MS · JPM · CTBC · MQ · Cathay · Mega · HNS …(候選表 · 等 VCGC 核發 · 對不到照原文並標記)|
| 報告日左邊加時效欄 | 早於最近已過的法定公布期限(3/31 · 5/15 · 8/14 · 11/14)或距今 > 30 個交易日 → **過期**;交易日 = 週一到五 − VDF 台股休市表(VDF_MDL001 · ast 唯讀)|
| ENG049 對帳頁當靜態視覺模板 · 字體與顏色一致且鎖定 · 左右面板等加上去 | VRN_ENG049_ContentReconcile v0102 對帳頁抽出 15 色 / 字級 19 · 11 · 9.5 · 9 · 8 px / 三種字型 → 一段 CSS 蓋整頁 · SHA-256 `4a9fe74d7aba` 釘在模組(自測核對 · 改就紅)|
| 時間 YYYY / YYYY-MM / YYYY-MM-DD | 期間:2026E → 2026 · Dec-26F → 2026-12 · 12/25 → 2025-12 · FY26E → 2026;日期:2026/5/2 → 2026-05-02;滑過看原文 |
| 所有資料最後加 Source | 每一冊最後一欄 Source(歷史 TWSE/TPEX · 報告預估 · 報告實際 · 報告 …)· CSV / JSON / MD 匯出值照輸出冊 + 最後一欄 SOURCE |

說明:Workbench v0105 的「有底色的字白色」改成模板的淡底深字標籤(新要求「顏色跟模板一致」優先)。

## 2. 測試

| 項目 | 結果 |
|---|---|
| Workbench v0108 自測 | [GREEN] VRN2_Workbench v0108 自測 全過(12 項) |
| Workbench v0107 回歸 | [GREEN] VRN2_Workbench v0107 自測 全過(15 項) |
| 啟動器 v0174 自測 | 全過 · [PASS] v0174: Workbench v0108 (ENG049 template lock · Freshness · Ticker / YFinance + Name · broker  |
| RoundAll v0130 自測 | [PASS] VRN2_RoundAll v0130 --selftest · 100 項 · 不過 0 |
| PowerShell 剖析 | pwsh 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| 桌機形狀資料(操作員上傳的 FinancialData 匯出 · 只在沙盒用)| 11,905 列期間全部轉成 YYYY 格式(預估 6,489 · 實際 5,416 · 讀不出 0)· 13 家券商全有縮寫 · 疊在另一線 v0104 → v0107 → v0108 上 JS 0 錯 |
| 瀏覽器(Chromium)| 資料頁欄序:時效 → 報告日 → … → Ticker / YFinance → Name → … → Source(最後)· 整冊 CSV 最後一欄 SOURCE · 內文 JhengHei 11px `#33403f` · 標題 Cormorant 19px · 表頭 Consolas 9px · 底 `#f2f1ec` · JS 錯 0 |
| e2e(最短一行 · 沙盒)| auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · auto1 整輪(啟動器 v0174 → Workbench v0108)→ 模擬桌機頁是 v0107 → auto2 repair 只排 workbench(補放 v0108 + v0107 → 重渲染)→ 竄改開機檔不執行 |
| 收尾負責方 | VRN-2 項與 v0171 基準相同(沙盒限定 · 沒有真 OCR 環境)|

## 3. 桌機下一步

1. 貼 `vrn2_release_v0174/VRN2_HandleAll_v0122.md` 的最短一行(收據 ≥ v0170 → repair · 一分鐘上下 · 只重渲染 Workbench)→ 打開工作台看資料頁。
2. MQ-1560 看過原圖:`python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0130.py" --confirm H-fd2ea35f --note "…"`(只有操作員打才算)。
3. 券商縮寫表要成為正式同義字 → 交 VCGC 核(VRN 只顯示用 · 不寫進輸出冊)。
