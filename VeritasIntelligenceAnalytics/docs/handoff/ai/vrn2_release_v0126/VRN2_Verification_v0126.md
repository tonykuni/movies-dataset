# VRN-2 v0126 驗證紀錄(2026-10-19 · Claude Code 雲端容器)

發行檔:`ActivateVRN-2_v0126.zip`(SHA-256 見 `VRN2_Release_v0126.json`)· 一鍵 PS:`VRN2_OneClick_v0126.md` · 交接報告:`../VRN2_Handover_v0126.md` · 日誌:`logs_v0126.zip`。

## 這一輪從哪來

使用者機器第 39 輪(v0125 · 52 份)貼回 U/I:⑧ 完成 紅 0 黃 5 · P1 黃 11 份「財報表沒對到期間欄」+ Citi-3231「沒找到財報頁」。容器重現其中 4 份(CLST · MS-3661 · 華南-3017 · Citi-3231)→ 分診出兩種版型(轉置表 · 表頭在表外);修完加跟讀法無關的一致性檢查(DUPKEY)→ 又抓到凱基季度欄被當年度輸出(v0122 起)與同名科目分段落。

## 情境實測(模擬使用者機器:先跑 v0125 並上船 → 另一台機器推了新提交 → 本機有別的系統的提交未推 → Downloads 裡是 v0125)

| 步驟 | 結果 | 證據 |
|---|---|---|
| 啟動器 v0126 自測 | 16/16 | `logs/launcher_selftest.log` |
| 管理器 v0231~v0236 自測 | 33/33 · 11/11 · 6/6 · 14/14 · 7/7 · 13/13 | `logs/oneclick_ps_run1.log` |
| 一鍵 PS 第 1 次 | ③ 備份 v0125 → 換 v0126 → 只落 v0236 → ⑧ 完成 紅 0 → ⑨ 只送 VRN-2 船包(疊在遠端最新 · 別的系統提交沒推)→ 獨立驗證錯值 0 · 約 1 分 45 秒 | `logs/oneclick_ps_run1.log` · `logs/ship_commit_remote_run1.log` · `logs/ship_commit_local.log` |
| 一鍵 PS 第 2 次 | ③ 已是 v0126 → ⑨ 已是最新 · 約 1 分 10 秒 | `logs/oneclick_ps_run2.log` |
| 新電腦(clone) | ② 船包補回 14/14 → ⑧ 完成 → ⑨ 只送船包 · 四本輸出冊與原機逐位元相同 | `logs/run_new_machine_clone.log` |
| 使用者自己 pull | 船包整檔衝突 · 取遠端 → 0 未解 | `logs/user_pull_merge_test.log` |

## 年度數據(14 份 · v0125 → v0126)

4,411 → **4,860**:華南 0 → 40(轉置表)· Citi 0 → 35(轉置表)· CLST 224 → 1,078 · JP 232 → 315 · MS-3661 366 → 430(表頭在表外)· 凱基慧洋 1,037 → 726 · 凱基貿聯 615 → 299(季度值 627 筆移到剔除冊)· 剔除冊 88 → 719 · ROW 標到 4,855 / 4,860。

## 輸出值驗證(獨立驗證器 v3 · 不 import VRN-2)

| 冊 | 結果 |
|---|---|
| 基本資料 | 194/194 |
| 一標題四重點 | 63/63 |
| 年度數據 4,860 | ALIGNED 4,323(pypdfium2)· SUBALIGNED 452(PyMuPDF)· TRANSALIGNED 75(PyMuPDF)· PRESENT 10 · **FAIL / BADITEM / SUBFAIL / TRANSFAIL / DUPKEY 0** |
| 反向測試 | 9/9(新增 ⑧ 同一列同期間兩個值 → DUPKEY · ⑨ 轉置表科目被改 → TRANSFAIL) |
| U/I 真瀏覽器 | 21/21 |

全景卡(只讀):管理器 v0236 問題 0 · 啟動器 9 項 SWALLOW(與 v0124 / v0125 相同 · 量測 / 視窗關閉的退路)· 驗證器 3 項(讀取器 / psutil 缺時的退路)。

## 沒驗到的(不寫成綠)

使用者機器 52 份(其他 P1 黃燈檔:260914_daiwa_aspeed · GFHK Apple · 南亞 · 啟碁 不在容器)· Windows PowerShell 5.1 · ③ 補裝(容器 `--no-install`)。
