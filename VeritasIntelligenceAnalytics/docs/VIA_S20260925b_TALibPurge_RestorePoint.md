# 側線 2026-09-25 第十六段 b:TA-Lib 全拔 · 許可冊 · 最佳還原點 · 驗證鎖定

主線批號由併線的手指定(L25)。本批接在 PR #125(14bca8a4)之後。

## 一、操作員令(原文)

- 「No ta-lib allowed」「NO TA-LIBS ALLOWED.」「NO TA-LIBS ALLOWED REMOVE ALL TAL-LIB」
- 「THE ONLY THING RELAVENT TO VRN IS TO USE CLOSE AND ADJ CLOSE TO CALCULATE ADJ OPEN / ADJ LOW / ADJ HIGH AND USE THEM FOR THE STCOK AS PRICE INDICATOR IN THE POLOCY.」
- 「WE'VE USE GUANTGUARD TO REPLACE TA-LIB ALREADY.」「WORKFLOW IS FROM VDF TO QUANTGUARD.」
- 「檢視VCGC及測試要求過關就鎖定不要一直重複」「之前最成功的兩三次紀錄…檢查 成功重疊者規則就鎖定」
- 「將最佳還原點的自動建置放在系統政策 環境及工具管理 測試AUDIT都要建立最佳還原點機制 LESSON-LEARNED LOGGING」
- 「測到一個階段自動上傳GITHUB」

## 二、TA-Lib 全拔(先量誰真的在用,再拔)

AST 實量:全樹 575 支檔提到 talib,**活碼裡真的 import 的 0 支**。其餘是禁令、歷史、收容正本(零觸碰)與偵測器(find_spec 看有沒有裝,L50 的執法)。本批拔掉的是**真的殘留**:

| 件 | 處置 |
|---|---|
| VeritasCeleritas 六份副本(不可動清單,批345) | 位元對齊 `supportive modules/accelerator/VeritasCeleritas.py`(sha256 464f6c14…,零 talib 路徑);許可冊逐件放行 |
| `VeritasCeleritas_v1140.py`(帶 talib 惰性路徑) | 刪;`v1141` = v1140 照八條差異重放,零 talib 行 |
| 退役 `VIA_ENG003_TALibEngine.py`(55,036 B,含 talib 碼) | 換成**同名墓碑**:零可執行碼、只記清除裁示與 git 出處。直接刪檔的第一版讓總控頁契約 test_01 紅(退役存證 117 → 116 族,違反只增不減),墓碑是那一次紅燈的修法 |
| `functional modules/TALib.zip`(vendored ta-lib-python 原始碼) | 拔 |
| 母頁 07 子系統「TALib 技術指標 64 式」(動詞 `via-wf talib` 已是死路) | CGC_MDL039 v0106 改 07 = QuantGuard(`via-quantguard`,狀態照實寫「工作站驗」) |
| 子系統頁建構器的 talib 鍵、`VIA_Sub_talib.html` | CGC_MDL038 v0103 換 quantguard 鍵;孤兒頁 `--prune` 刪 |
| 商品 PKG-015「TALib 技術指標 64 式」 | CGC_MDL036 v0101 移出 PRODUCTS、記 RETIRED(編號不回收);指針檔刪 |
| `.ps1` 三支(WorkflowEngine · TheoryAudit · WorkOps-All v0111)的 talib 接線 | 拔(L70 逐次許可;BOM/CRLF 保留) |
| VRN 全景探針把 talib 列成「加速候選庫」 | 拔(VRN 只認 ADJ OHLC,L104) |
| `VDF_TA_Engine_Spec_v0100.json` talib_policy | 撤銷,改指 L50 + QuantGuard |

留著不動的(照實記):收容正本(`references/intake/`,KILL-03 正本零觸碰)裡的 talib 碼只是存證,執行期不可達;法冊、教訓、退役帳裡講 TA-Lib 禁令的文字是律本身。

## 三、許可冊 + 擊斃閘 v0101 + 加速器控制面 v0110

- **CGC_MDL187 v0101**:v0100 沒有「許可」這個東西,奉令的改跟私改一樣被殺。加 `VIA_ModuleChange_Permits_v0100.json`:只許 KILL-02/04/05(條款本文寫著要操作員逐次許可的三條);modify 釘 sha256、delete 釘檔真的不在;每筆要 ruled_by / ruling / date;冊讀不到 = 沒有許可(fail-closed)。自測 23 → 25(㉔ 正控 · ㉕ 負控五種),突變 7/7 全抓。
- **CGC_MDL156 v0110**:⑦「收容正本 vs 掛載本」不一致時,掛載本位元正好等於 Celeritas 基線冊 `immutable_b345.sha256` 且帶 `ruling_*` 才照裁示通過;差一個位元、沒裁示、冊讀不到照紅。37/37,五種正負情形實量。

## 四、最佳還原點(L105)與驗證鎖定

- **L104 ⑥**:流程 VDF(ENG060 → tw_prices_adj 的 ADJ OHLC)→ QuantGuard(VDF_ENG086)→ VRN;TA-Lib 不在任何一站。
- **L105 過關就鎖定 · 最佳還原點自動建置**:環境及工具管理 = CGC_MDL135 LKGC(既有,逐境晉升);測試/AUDIT = 格子 v0498 起全跑過關(FAIL 0 · TIMEOUT 0 · 沒中斷 · 正式庫前後一致)自動建點 `VIA_Reports/restore_points/BRP_test_audit_latest.json`,沒過關只寫 candidate、**舊的最佳點一個位元不動**。
  - 實跑咬到的一個洞:格子自測 ② 會真的呼叫一次 main(),第一版把還原點寫進了真目錄。已補:② 一併導走 `BRP_DIR`,⑧ 加「整支自測前後真還原點夾零足跡」,突變證明抓得到。
- **驗證鎖定冊** `VIA_Validation_Lock_v0100.json`:四筆全綠紀錄(88d7a3e3 · 4cdb368e · 767d1f02 · adee3b1c)逐筆實量,重疊的是 S1 編號冊同步 / S2 VCGC 自測 / S3 改動引擎自測 / S5 推前全格子;S4 擊斃閘、S6 總控頁契約、S7 按清單還原是照規則列入,冊上逐步標 basis。
- **LL459–LL462**:沒有許可的閘會殺奉令的改 · 過關就鎖定 · 最佳還原點壞的一跑不准蓋好的 · 拔禁用庫要量誰真的用它。

## 五、驗證(照鎖定冊各跑一次;之後只補跑受影響的)

| 步 | 結果 |
|---|---|
| S1 registry-sync --apply | 新 9 · 變更 78 · 退役 0 · AST 錯 0(補改後再同步:新 4 · 變更 16) |
| S2 VCGC 自測 | 三十八檢 38/38 |
| S3 改動引擎自測 | MDL187 25/25 · MDL156 37/37 · 格子 8/8 · MDL039 5/5 · MDL038 3/3 · MDL036 3/3 · VRN 探針單元 14/14 · 墓碑 1/1 |
| S4 擊斃閘 --base origin/main --run-selftest | rc0 · 判 39 檔 · 11 條全過 · 10 件操作員許可(位元吻合) |
| S5 全格子(一次) | OK 340 · FAIL 4 · SKIP 17 · TIMEOUT 0 · 688s · 正式庫三本前後一致;FAIL:工具升階梯(Z216 境缺)· UI Matrix 讀舊存證 · MDL120 生成頁不在(境)· 總控頁契約(→ S6 修好);沒過關 → 不建最佳還原點(照律) |
| S6 總控頁再生 + 契約 | 正式任務 92 · 契約 19/19 |
| S7 按清單還原 | 格子再生的 38 支已追蹤檔逐檔還原 |

## 六、還原

- 碼:`git restore --source=14bca8a4 -- <檔>` 逐檔退回本批之前。
- TA-Lib 全拔這件事**不做還原**(操作員令);要看被拔掉的內容,查 git 歷史 14bca8a4。

## 七、下一步(已排)

- **Z217 / B 批**:VCGC 唯一向下入口(先過政策 → 輔助工具有何可用 → 自動註冊/自動編號 → 上下交互檢查,自適應)· 四個管理器寫現況還原交接紀錄 · 經管理器才可讀個別引擎 · CGC_MDL157 AST 向下入口探針。
- **三輪多面相沙盒引擎**(操作員令「定位目前通過為最佳現況…VCGC VRN VDF 格子測試及可能結果預判沙盒測試三輪…用 VCGC 為單一路徑…一個 PowerShell 25 個加速器不卡斷…紅字錯誤 綠字貼給 AI」):由 `via-vcgc tri` 進入,委派既有正主不重寫;結果放最底下。
- **Z216**:工具升階梯在缺件環境回 rc1 → 改誠實 rc3。
