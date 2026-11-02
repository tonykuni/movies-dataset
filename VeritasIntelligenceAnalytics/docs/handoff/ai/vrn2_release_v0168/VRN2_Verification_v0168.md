# VRN-2 v0168 驗證紀錄(2026-11-02 · 管理器 v0259 轉置表再驗 · 套件 v0168 · RoundAll v0124 · Handle-All v0116)

## 1. 起因

- 桌機 2026-11-02 10:30(Handle-All v0115 repair · 75 秒):收尾 **REVIEW**(VRN-2 0 · 人工 2 · 資料源 3)· 缺項只剩華南投顧-6143 · 收尾行印了兩次
  「Write-Host 無法繫結參數 ForegroundColor」。
- 操作員上傳華南投顧-6143-振曜-1141128.pdf(只在容器沙盒用 · 不進倉)。

## 2. 6143 原文核對

第 1 頁「年度EPS預估」:年份在列(2022 · 2023 · 2024 · 2025(F) · 2026(F))· 科目在欄(營收 · 毛利率(%) · 營益率(%) · 業外收支率(%) · 股本 · 稅前純益 · 稅前EPS · 稅後EPS)= 40 值。
**原文有年度表**。第二讀取器(pypdfium2)每一列都讀得到;v0236 轉置表第三讀法閘(pdfplumber)整張剔除「每個年份一行對不上」:2026(F) 那列的一位小數值上疊了一個
別的字型(Calibri · 低 2pt)的空白字(Word 留下的),pdfplumber 把那個數切成「3」「.0」兩個字(兩個字其實相連)→ 那一列數字序列不同 → 40 值全剔。
桌機 09:19 剔除冊裡帶這個理由的剛好 40 列 · 全是 6143。

## 3. 修正

- **管理器 VRN_SystemManager_v0259**(薄尾 · PRIOR v0258):只對「轉置表第三讀法(pdfplumber)對不上」的剔除列 · 依表分組 · 第三讀法同一行裡相連(間距 ≤ 0.5pt)的數字碎片接回
  (左邊有數字 · 接點是小數點 / 千分位 · 接起來是數字)再問 v0236 同一個閘;過了整張表回主冊(VERIFY 註明 v0259)· 該份的「年度數據」缺項清掉;還是不過 / 主冊已有同鍵 → 照留剔除冊;
  再驗出錯 → 輸出冊照 v0258。
- **Handle-All v0116**:v0113 起建置時把 --confirm 提示塞進了顏色表的 REVIEW(第一個 `REVIEW = '…'`)→ 收尾 REVIEW 時 Write-Host 顏色參數錯 · 改回 'Yellow' · 提示移到「下一步」那行。
- 套件 v0168(啟動器 v0168 · runtime v0159 = v0158 的 197 個成員不動 + v0259)· RoundAll v0124 · Handle-All v0116 · 啟動器版號跳過 v0167。

## 4. 測試

| 項目 | 結果 |
|---|---|
| 管理器 v0259 自測 | [PASS] v0259: transposed tables asked again with the third reader's touching number fragments joined · still failing sta |
| 啟動器 v0168 自測 | [PASS] v0168: manager v0259 is the active manager (transposed tables re-asked with the thi |
| RoundAll v0124 自測 | [PASS] VRN2_RoundAll v0124 --selftest · 90 項 · 不過 0 |
| PowerShell 剖析 | pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| 6143 原文(沙盒 · 管理器直跑) | 40 / 40 值回主冊(剔除 40 → 0)· 獨立驗證 TRANSALIGNED 40 · 逐格等於原文 |
| 回歸(沙盒 14 份真報告 + 5 份原文) | 年度數據 5622 → 5662(少 0 · 多 40 = 6143)· 剔除冊 806 → 766(同那 40)· 基本資料 / 摘要不變 |
| Handle-All 顏色 | v0115 那兩行在 pwsh 照樣報 ForegroundColor 錯 · v0116 正常印 |
| e2e(最短一行 · 沙盒含三份原文) | auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · auto 第一次 → 整輪(收據 v0153)· 第二次 → repair(收據 v0168)· 竄改開機檔 → 不執行 · 整輪裡 v0259 補回 6143 的 40 值 · ⑪ 年度 5232 筆錯值 0(TRANSALIGNED 75 → 115)· 缺項不再有 6143 年度數據 · 收尾 {"auto1": {"state": "OPEN", "per_owner": {"VCGC": 8, "VRN-2": 3, "人工": 8}}, "auto2": {"state": "OPEN", "per_owner": {"VCGC": 6, "VRN-2": 3, "人工": 8}}}(VRN-2 3 項 = 新加的三份在沙盒做不出摘要:容器測試環境 numpy 1.26.4 配 scikit-learn 1.9.1 · 環境問題 · 摘要器這輪沒動 · 桌機這三份已有四點)|

## 5. 一行指令

cmd 一行 1240 字元 · PowerShell 最短一行 443 字元 · 開機檔 `vrn2_release_v0168/VRN2_HandleAll_v0116_boot.txt`(SHA-256 `f3d3821564ba`)· Handle-All 一行 `e0bb916f23bb` · RoundAll v0124 `47cdc2b2a16e` · 套件 `931b6a9ac38c`。
auto:上一輪收據不是啟動器 v0168 做的 → 整輪(輸出冊要由 v0259 重做 · 桌機約 90 分鐘)。PowerShell 視窗設同意閘要用 `$env:VIA_SCRAPE_CONSENT = 'YES'`(`set "…"` 是 cmd 的寫法)。

## 6. 沒做 / 待辦

- 人工確認只有操作員親手打 `--confirm`(AI 不代打)· MQ-1560 四點 H-fd2ea35f。
- 3014TT 四點(第 2 點從句中開始 · 第 1 / 3 點重複)· MQ-1560 OCR 字詞錯(chi players)→ 摘要器 / OCR 另一輪。
- 主控台前面那段 VDF / VCGC / SettleAll 的訊息是其他系統的(VDF_SystemManager rc 1 · claude/vrn2-closeout-authorization-y4ixl7 分支的 SettleAll 雜湊不符)· VRN-2 只讀不動。
