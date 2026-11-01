# VRN-2 v0166 驗證紀錄(2026-11-01 · 管理器 v0258 輸出冊前表格修補 · 套件 v0166 · RoundAll v0122 · Handle-All v0114)

## 1. 起因

桌機 2026-11-01 06:32(v0165 repair)收尾 **REVIEW**:人工 2 項 —— H-fd2ea35f(MQ-1560 影像頁四點 OCR)· H-275f449a(輸出冊缺項 3 份 · 年度數據:Daiwa-6278 · 欣銓 3264 · 華南投顧-6143)。
操作員上傳原文 4 份(MQ-1560 · 3014TT · Daiwa-6278 · 欣銓 3264 · 只在容器沙盒用 · 不進倉)。

## 2. 原文核對結論

| 檔 | 結論 |
|---|---|
| MQ-1560(影像頁) | 四點都在原文(三點在 Why it matters · 一點在 What's new)· 數字全對(70-80% · 10% · 20-30% · 25-30%)· OCR 有字距雜訊(GP M · ram ping · m gmt)· **一處字詞錯**:原文 chip layers → 摘錄 chi players。影像頁的年度表 OCR 值照舊全進剔除冊(68 值裡 4 值跟原圖不符 · 剔除是對的)|
| 欣銓 3264(CTBC) | **原文有年度表**(第 5 頁 資產負債表 / 現金流量表 2022-2025 · 損益表 / 比率分析 2023-2027F · 第 1 頁表 2022-2027F)→ 擷取後輸出冊漏掉:科目印在數字下方約 3pt,擷取成「只有數字」+「只有科目」兩列,輸出冊兩列都略過(剔除冊也沒有)|
| Daiwa-6278 | **原文有年度數據**(第 2 頁 financial summary 2024 / 2025 實績 · Target price n.a. · 沒有預估年)→ 年份橫幅蓋在真正的期間表頭上,一格 3 ~ 5 個值,全進剔除冊「一格多值」|
| 3014TT | 年度數據 430 筆照舊(2023/2024 年報告 · 共識要的 2026 EPS 原文本來就沒有)· 四點:第 2 點從句中開始(「CPU(Meteor Lake)…」· 原文那段是字距拉開的排版)· 第 1 / 3 點講同一件事(Type-C PD 10%)→ 摘要器下一輪再看 |
| 華南投顧-6143 | 沒上傳 · 桌機剔除冊 40 值(轉置表第三讀法對不上)→ 要原文才能判 |

以前寫的「原文沒有就是真的沒有」用的是本機 ~20 KB 的合成替身 —— 對 3264 / 6278 不成立,這裡更正。

## 3. 修正:管理器 VRN_SystemManager_v0258(薄尾 · PRIOR v0257)

輸出冊之前,在擷取結果的**副本**上修兩種表(P1VIEW 不動),然後 v0257 的輸出冊照跑:
- ① 科目半行配對:「只有數字」列旁邊是「只有科目」列 → 第二讀取器(pypdfium2)同一印刷列有「科目 + 這串年度欄數字」(整頁唯一 · ≥ 2 個數)才併 · 科目被切成幾格接回(中中不空 · 中英一格空白)。
- ② 兩層期間表頭:表頭下一列才是真正的期間(全是期間字 · ≥ 2 個年度 · 不重複 · 有格裝了好幾個)→ 依那一列重排:第二讀取器找得到那一行(唯一)· 每一列「科目 + 同一串數字」找得到(唯一)· 每個數字歸最近的表頭字(一對一 · 順序 · 0.4 欄距內)· 放不進去的列移剔除冊(帶理由)。
- 修補出錯 → 輸出冊照 v0257(原始結果)· 印一行原因。

## 4. 測試

| 項目 | 結果 |
|---|---|
| 管理器 v0258 自測 | [PASS] v0258: table repair before the books — label half-line pairing and two-level period header re-grid, both confirme |
| 啟動器 v0166 自測 | [PASS] v0166: manager v0258 is the active manager (table repair before the books |
| RoundAll v0122 自測 | [PASS] VRN2_RoundAll v0122 --selftest · 88 項 · 不過 0 |
| PowerShell 剖析 | pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| 原文(沙盒 · 管理器直跑) | 欣銓 3264 → 225 筆 · Daiwa-6278 → 30 筆 · v0257 的筆數一筆不少 · 獨立驗證 v0114:[驗證] 年度數據 685 筆 · {'ALIGNED': 685} |
| 回歸(沙盒 14 份真報告) | FinancialData 4905 → 4937 (removed 0 · added 32 晶心科 6533 P5) · Rejected 744 = 744 (0 changed) · BasicInfo / Summary identical · 獨立驗證:[驗證] 年度數據 4937 筆 · {'ALIGNED': 4410, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} |
| e2e(最短一行 · 沙盒 14 份) | auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · b_full rc 0 · auto 第一次 → 整輪(收據 v0153)· 第二次 → repair(收據 v0166)· 竄改開機檔 → 不執行 · 收尾 BLOCKED(VRN-2 0 · 等 VCGC 的沙盒環境 · 人工 1 = MQ-1560 四點)|
| e2e 變體(沙盒 + 兩份原文 · 16 份) | 整輪 · 年度數據 5192 筆(欣銓 225 · Daiwa-6278 30 · 晶心科 111)· ⑪ 獨立驗證錯值 0(ALIGNED 4665 · SUBALIGNED 452 · TRANSALIGNED 75)· 兩份新檔的摘要在沙盒失敗 = 容器測試環境 numpy 1.26.4 配 scikit-learn 1.9.1(np.long · 環境問題 · 不是 VRN-2 程式 · 摘要器這輪沒動 · 桌機 06:32 這兩份已有四點)|

e2e 收尾狀態:{"auto1": {"state": "BLOCKED", "per_owner": {"VCGC": 8, "人工": 1}}, "auto2": {"state": "BLOCKED", "per_owner": {"VCGC": 6, "人工": 1}}, "b_full": {"state": "OPEN", "per_owner": {"VCGC": 8, "VRN-2": 3, "人工": 6}}}

## 5. 一行指令

cmd 一行 1240 字元 · PowerShell 最短一行 443 字元 · 開機檔 `vrn2_release_v0166/VRN2_HandleAll_v0114_boot.txt`(SHA-256 `26774199d3e6`)· Handle-All 一行 `48cef1e897b6` · RoundAll v0122 `9d63be0ebd65` · 套件 `68d6d03d3fd1`。
auto:上一輪收據不是啟動器 v0166 做的 → 整輪(輸出冊由 v0258 重做 · 桌機約 40 分鐘)。

## 6. 沒做 / 待辦

- 人工確認:只有操作員親手打 `--confirm`(AI 不代打)。
- 華南投顧-6143 原文沒上傳(轉置表第三讀法對不上 40 值)。
- 3014TT 四點(第 2 點從句中開始 · 第 1 / 3 點重複)· MQ-1560 OCR 字詞錯(chi players)→ 摘要器 / OCR 下一輪。
