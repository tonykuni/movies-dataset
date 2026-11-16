# 交接 · 2026-11-16(晚)· VRN 一個指令 + 檔名日期修正 + 參數一本 JSON

## 這三天的接近成功紀錄與現況
| 日期 | 紀錄 | 當時結果 | 現況 | 有沒有重工 |
|---|---|---|---|---|
| 11-13 | 容器全量實跑 VDF 85 · VRN 74 引擎;ENG049 矩陣 v0104 / v0105 | 四紅修掉 | 在;本輪矩陣照跑 | 無 |
| 11-14 | 桌機 97 份樣本跑管理器 extract(v0270 → v0271 平行) | READ 60 · REVIEW 23 | 尾版 v0276;容器 24 份 READ 13 · REVIEW 8 · TEXT_DOC 1 · NODATA 2 · ERROR 0 | 有:分支線 v0267–v0269 與 main 線 v0270–v0275 各做各的;併線後鏈實測可用(v0275 / v0276 自測過),不必重做 |
| 11-14 | VIA_NearCompleteLock v0101(里程碑鎖) | 已上鎖 | 沒重建(見「沒做的」) | 無 |
| 11-15 07:33 | 每日備份 BACKUP_MANIFEST 20261115_073319Z | backup / check GREEN · 441 檔 | 之後同日另有 15:48 · 18:06 · 18:38 三份;本輪再備一份 | 無 |
| 11-16 | 啟動器 v0100 → v0101 → v0102 | v0100 桌機卡住;v0101 沒上桌(同步被擋) | v0102 容器整輪跑完 | 有:v0100 的擷取路設計錯,v0101 重做;v0102 是薄尾,不重寫 |

## 本輪新增(只增;舊檔一字不動)
| 檔 | VCGC 編號 | 做什麼 | 驗證 |
|---|---|---|---|
| `VRN/VRN_SystemManager_v0276.py` | VIA-VRN-MDL349 | 檔名尾巴 `(YYYYMMDD-HHMMSS)` 是下載時間戳,不當報告日期;平行子行程改用尾版檔起跑 | 自測 7/7;實跑 2 份日期改對(2026-10-06 → 2025-12-08 / 2025-12-02) |
| `VRN/VRN_MDL260_SafeParallelLaunch_v0102.py` | VIA-VRN-MDL350 | `--source` 一個參數餵 extract 與文件整輪;就緒檢查;輸入分群;結果併燈;與上一輪比 | 自測 18/18;容器 24 份整輪實跑 |
| `VRN/VRN_ParamControl_SSOT_v0101.json` | VRN 自己的冊(VCGC 邊界閘不替 VRN 正本發號,照擋) | run_params · input_groups(個股 / 產業 / 晨會日報 / 其他)· file_overrides | 啟動器自測 P1–P4 |

## 容器整輪實跑(24 份真 PDF · v0102)
| 流程 | 燈 | 說明 |
|---|---|---|
| 加速器橋閘 | GREEN | 100% 且執行時載得到 |
| 管理器 extract(三組) | 回傳碼 GREEN → 併燈 YELLOW | READ 13 · TEXT_DOC 1 · REVIEW 8 · NODATA 2;10 份逐檔點名 |
| VRN-2 文件整輪 | RED | 基本資料 178/178 過;年度數據 5,662 筆(對不上 40);一標題四重點 19/19 紅 = 容器沒有 pymupdf(ModuleNotFoundError),屬環境 |
| ENG049 矩陣 | 回傳碼 GREEN → 併燈 YELLOW | 個股 42 列 YELLOW 15 · NODATA 27;非個股 22 列全 NODATA |
| 衝突 · 安裝計畫 · 收尾 | YELLOW | 同意閘沒開(不代設)· 缺件要經 VCGC InstallGate |
| OmniRoute · Graphify | GREEN | |

10 份待看的原因:pdfplumber 找不到表 3(3014TT · Daiwa-1319 · Daiwa-6278;容器沒有 camelot / tabula)· 表在但沒有期間表頭 5
(GS-6415 · JP-2330 · 華南 6143 · 華南 3017 · 中信債券 ETF 周報)· 掃描件待 OCR 2(MQ-1560 兩個檔名同一份)。

## 輸出表(DataFrame)檢查(本輪 7 張 Parquet)
| 表 | 列 × 欄 | 重複欄名 | 整列重複 | 型別 | 要注意 |
|---|---|---|---|---|---|
| 個股矩陣 | 42 × 43 | 0 | 0 | 43 欄全文字 | 21 欄是數字卻存成文字(EPS · BVPS · 目標價 …);9 欄整欄空 |
| 非個股矩陣 | 22 × 22 | 0 | 0 | 全文字 | 11 欄整欄空(四重點等) |
| VRN2_BasicInfo | 19 × 21 | 0 | 0 | 全文字 | TITLE · TARGET_PRICE · ADJ_CLOSE 等 6 欄整欄空 |
| VRN2_FinancialData | 5,662 × 15 | 0 | 0 | 文字 13 · 整數 1 · 小數 1 | VALUE 是文字(照原文) |
| VRN2_Summary | 19 × 12 | 0 | 0 | | 標題與四重點整欄空(摘要器沒跑起來) |
| VRN2_Combined | 19 × 28 | 0 | 0 | 全文字 | 15 欄整欄空 |
| VRN2_Rejected | 766 × 15 | 0 | 3 | | 3 列整列重複 |
結論:欄名沒有重複、鍵欄都在;但矩陣的數值欄沒有定型別(全文字),整欄空的多半是容器缺 pymupdf / 沒開同意閘造成。
沒有拿表頭冊逐欄比對(本輪沒做),型別定義也還沒寫成冊 → 待辦。

## 沒做的 / 做不到的(照實)
- 桌機實測(`C:\測試樣本報告` 97 份)· 滑鼠走 U/I:這個工作階段連不到桌機。
- 容器沒有 pymupdf · camelot · tabula · OCR · yfinance:安裝要經 VCGC InstallGate,它要同意閘,同意閘只由操作員設 → 沒裝。
- 沒有期間表頭的 5 份與 pdfplumber 找不到表的 3 份:沒有硬修(亂配欄位會出錯值);要第二讀取器或逐份看原文。
- NearCompleteLock 沒重建(要里程碑清單);本輪成功另記在 `VRN_SuccessLock_20261116.json`(檔雜湊 + 收據)。交接冊的成功鎖案(V-…)沒登。
- VCGC `test --quick` 仍 RED(綠 8 · 黃 2 · 紅 3,三紅是併線後既有的,本輪沒變);`ssot panorama` rc 1 是既有的 _TP 正則教訓(第 39 次),本輪沒碰。
- 編號稽核:遺失 0 · 改身分 0 · 重號 0 · IMMUT 0;「冊內不一致 1」(rule 冊 54 列宣告碼 ≠ 發出號)是既有的。

## 桌機一行(PowerShell 7)
```powershell
$W="$env:LOCALAPPDATA\VIA\movies-dataset-vdf-main"; git -C $W fetch origin claude/optimistic-goodall-yhalc5; git -C $W checkout --detach FETCH_HEAD; $F="$W\VeritasIntelligenceAnalytics\functional modules\VRN\VRN_MDL260_SafeParallelLaunch_v0102.py"; if (Test-Path $F) { py $F run --source "C:\測試樣本報告" } else { "檔不在:同步沒成功,把上面 git 的訊息貼回" }
```
只想先看就緒檢查:把 `run` 換成 `preflight`。看參數與分群表:`params --source "C:\測試樣本報告" --csv`。
