# VRN-2 v0136 容器實測紀錄(2026-10-21 · 整合一支 第二回:驗證器 v0105 + ⑫a VRN-1 倉同步)

操作員在 v0135(PR #562)合併後再令「integrate INTO ONE CODE TO HANDLE ALL ABOVE」。v0135 之後還留著的四件 —— DUPKEY 82 一行都沒進摘要、標籤對調 3 筆、MS-6669 EPS、⑫ 要手動 `git switch main; git pull` —— 全部整進同一支啟動器 **v0136**(只換內嵌驗證器 v0105 + ⑫a + 交接 v0136;v0102 / v0103 / v0104 留著,⑪ 取最新版)。
四系統(VRN-1 · VRN-2 · VDF · VCGC)各自獨立;⑫a 只 fast-forward VRN-1 本機倉自己的 main,不改寫歷史、不提交、不推。

## 1. 主體不動(逐位元組)

`VRN2_Release_v0136.json` 內嵌清單 22 個元件:管理器鏈 v0231 → v0239、ENG397 v0127、ENG062 v0114、工具橋 v0101、OCR 橋 v0100、規則目錄、處理器 v0102 / v0103 / v0104、驗證器 v0102 / v0103 / v0104 **全部與 v0135(MAIN)相同**;
新增 `VRN2_IndependentVerifier_v0105.py`(sha256 `f16abb73b282…`)、交接 `VRN2_Handover_v0136.md`。只增不減。

| 檔 | SHA-256 |
|---|---|
| `ActivateVRN-2_v0136.py` | `cb6bf142a0e33824e3ef97ec134f37fd970b6225cd1384cecdee409c77d68354`(`VRN2_Release_v0136.json` launcher.sha256)|
| 一鍵程式碼(`VRN2_OneClick_v0136.md` 內 · 即 ActivateVRN-2.ps1)| `eebbd1755d50…`(md 內「程式碼 SHA-256」)|

## 2. 整進啟動器的四件

| # | v0135 之後還留著的(Windows 2026-10-21 13:06 實跑) | 追到的根因 | v0136 做法 | 在哪支 |
|---|---|---|---|---|
| 1 | ⑪ DUPKEY 82 筆,但「貼給 AI」一行都沒有 | 摘要 150 行的上限先被基本資料 25 筆 + 一標題四重點 + BADITEM 12 筆吃掉,DUPKEY 排在 BADITEM 之後被截掉 | 每一類錯值先各印 6 筆(標題 + 檔分佈 + 例子)再補滿 150 行;基本資料不過只印 16 筆 + 一行「另有 n 筆」 | 驗證器 v0105 `write_digest` |
| 2 | DUPKEY 兩筆都標錯值,分不出哪筆對 | 舊規則只看「同鍵有兩個值」 | 看位置證據:同鍵只有一個值對位(ALIGNED / SUBALIGNED / TRANSALIGNED)→ 那筆保留判決並註記、另一筆 DUPKEY 並註記對位的值;都對位 / 都不對位 → 照舊兩筆都 DUPKEY。⑫ PIVOT 只收對位的格 → 對的那筆進得了 PIVOT | 驗證器 v0105 `dupkey` |
| 3 | 標籤對調 3 筆只寫「但旁邊是目標價標籤」 | 擷取端把目標價 / 現價放錯欄 | `_swap_hint`:目標價在股價標籤旁且現價在目標價標籤旁 → 「對調」· 同值在目標價標籤旁 → 「現價被填成目標價」· 單邊 → 「可能把 … 當成 …」;值仍 FAIL(照實) | 驗證器 v0105 `verify_basic` |
| 4 | MS-6669 一標題四重點 EPS 251.50 不是年度數據的值 | 摘要器用錯格 | 不符時印「年度數據 2025 年 EPS 是 EPS (NT$) 2025E=…」 | 驗證器 v0105 `_eps_ok` |
| 5 | ⑫ 灰:「cd VIA-VDF-VRN; git fetch; git switch …; git pull」要操作員手動 | 操作員本機的 VRN-1 倉停在沒有工具冊的版本 | ⑫a:借工具前自己做 —— 找倉(VIA_VRN1_ROOT · C:\Users\tonyk\VIA-VDF-VRN · 家目錄 · VIA 倉旁邊)→ 已追蹤檔沒改動才動 → fetch origin main → 不在 main 就 switch main(原分支名印出 · `git switch -` 切得回)→ `merge --ff-only`;改過 / 沒網路 / 分岔 → 不動、照實說;`VIA_VRN2_NO_VRN1_SYNC=1` 不同步 | 啟動器 v0136 `_vrn1_sync` |
| 6 | 沒動(照實說)| 對調 / DUPKEY 另一筆 / EPS 用錯格的根因在擷取 / 摘要器(ENG397 · ENG062 · 管理器)| 本輪只把證據寫清楚;等 Windows 用 v0136 跑一次、把帶證據的摘要貼回來再修擷取端 | — |

## 3. 自測

| 項目 | 結果 |
|---|---|
| 驗證器 v0105 `--selftest` | **30 / 30**(v0104 的 26 條 + 4 條:DUPKEY 位置證據 3 種組合 · 對調診斷 5 種組合 · EPS 不符印年度數據那一格 · 摘要每類都出現 ≤ 150 行)|
| 啟動器 v0136 `--selftest` | **35 / 35**(多 1 條:⑫a VRN-1 倉同步 git 夾具 —— origin 2 個提交、clone 退回 1 個且在 feature 分支 → 切回 main 並 fast-forward(a.txt = 2 · 原分支名在說明)· 已追蹤檔改過 → 黃不動 · `VIA_VRN2_NO_VRN1_SYNC=1` → 灰;內嵌驗證器檢查改認 v0105:`_ALIGNED_V` · `_swap_hint` · 內嵌清單 v0102 / v0103 / v0104 / v0105) |
| 一鍵 ⑤b / ⑤c pwsh 單元 | **23 / 23**(⑤b 認處理器 v0104 · 版號 v0136) |

## 3b. 驗證器回歸(容器同一本冊 · 14 份 · 4,905 筆)

v0104 與 v0105 對同一本輸出冊的判決**逐類相同**:年度數據 ALIGNED 4,378 · TRANSALIGNED 75 · SUBALIGNED 452(錯值 0)· 基本資料 PASS 193 / OCR 1 · 一標題四重點 PASS 64 / OCR 4 · 冊指紋相同。
(這本冊沒有 DUPKEY、沒有對調、沒有 EPS 不符,所以四項改法在這裡都不觸發;Windows 那本冊會。)

## 4. 沙盒端到端(啟動器 v0136 · 19 份真實 PDF · 個股 14)

| 情境 | 結果 |
|---|---|
| A1 預設來源(環境 VIA_VRN_INPUT) | ②b 綠(檔 19 · 個股範圍 14 · 範圍外 5)· ⑥c 灰(非 Windows · 處理器 v0104)· ⑦ **14 / 14** · ⑧ 完成 紅 0 黃 4 · ⑪ **v0105** 錯值 0(基本資料 PASS 193 / OCR 1 · 一標題四重點 PASS 64 / OCR 4 · 年度 4,905)· **⑫a 綠:容器的 VRN-1 clone 原在 `claude/optimistic-goodall-yhalc5`(乾淨)→ 切回 main `876a4f6` · fast-forward 0 · 原分支名印在說明** · ⑫ 綠 4,653 / 4,905 · ⑫b 綠 · 註冊核對 全部登記成功 |
| P1pick → P1(U/I 選資料夾 · 9 檔)| 稽核 PDF 6 · Word 1 · TXT 1 · 影像 1 → 個股 5 · 範圍外 1 → ⑦ 5 / 5 · ⑪ 錯值 0 · ⑫a 已在 main 最新 · ⑫ 2,056 / 2,214 |
| P2pick → P2(U/I 選檔案 · 2 PDF + txt → 暫存夾)| ⑦ 2 / 2 · ⑧ 完成 · ⑪ 錯值 0 |
| R / R2 / audit | 產業 / 其他 拒絕 rc 3 · 重新稽核綠 |

與 v0135(MAIN)同一組數字(沒有退步);⑪ 跑的是 `VRN2_IndependentVerifier_v0105.py`;⑫a 真的動了容器裡那份 VRN-1 clone(只 fast-forward、沒提交、沒推)。

## 5. 一鍵 v0135(MAIN)→ v0136 沙盒情境

Downloads 是 **MAIN 的 v0135 啟動器**(SHA-256 `b97adc67c9ed…`)· 發行夾 `vrn2_release_v0136` 在 GitHub 分支 · `$env:VRN2_SOURCE` 指向樣本夾 · 貼一行:一鍵程式碼 SHA-256 `eebbd1755d50` 相符 → ③ 舊啟動器 v0135 備份 · **v0136 就位(雜湊相符)** → 啟動器 ①~⑫ 綠(③ 環境檢查紅 = 沙盒 `--no-install` 仍缺 7 套件 · ② 船包 / ⑥c vrn2:// 灰 = 非 Windows;與 v0135 情境相同)· ⑦ 14 / 14 · ⑧ 完成 紅 0 黃 4 · ⑪ v0105 錯值 0 · ⑫a 綠(VRN-1 倉已在 main 最新)· ⑫ 綠 · ⑫b 綠 · 註冊核對 處理器 v0104 → ⑤b 黃(Linux 沒 HKCU)· ⑤c 黃(容器沒瀏覽器)→ NEXT YELLOW · rc 2。Windows 上 ⑥c 會註冊並讀回核對、啟動器自己彈出 U/I、⑫a 會把 `C:\Users\tonyk\VIA-VDF-VRN` fast-forward 到 main → ⑫ 應轉綠。

這份情境跑的就是最後一版啟動器(交接的實測文字改一次就重建、重跑一次;最後一次的結果與前一次逐項相同)。

## 6. U/I 真瀏覽器

一鍵情境樹:既有 U/I `ui_test.js` **35 / 35** · 輸入區塊 `ui_input.js` **14 / 14**。
