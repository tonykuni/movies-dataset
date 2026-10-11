# 三系統全景式檢視 → 問題矩陣 → 第一輪安全修正(VCGC-REQ180 · 2026-10-12)

操作員令(2026-10-12,原話逐字入需求冊 VCGC-REQ180):「用VCGC節省TOKEN工具全景式檢是VCGC/VDF SYSTEM MANAGER及相關SSOT引擎REGEX同義字 收尾完成VCGC VDF後並啟動VCGC及VDF系統跳出HTML U/I完成功能」「…將問題分為可同時修正及應順序修正…不產生九頭龍風險前提下 進行一輪安全修正後 再進行一次事後全景式顯示…成功被鎖定及記錄 錯誤越來越少…直到VDF VCGC這2個獨立系統完美運作無誤…跳出HTML U/I」

全景只讀(VCGC 省 Token 工具 read / slice / digest;L120 三系統對等:VRN 的項只攤開不代修)。燈:紅 = 壞 · 黃 = 缺料 / 環境 / 待裁 · 綠 = 過。

## 一、問題矩陣(改前 → 改後;容器)

| # | 系統 | 項 | 改前 | 根因(讀日誌 / 原始碼定位) | 類 | 錨點(AST) | 修法 | 改後(容器) | 歸屬 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | VCGC | 串測 V-val | 紅 | 驗證冊沒登多段交叉代碼 X-REQ-BACK · X-REQ-OPEN · X-PEER · X-PEER-TEXT;MDL246 v0100 正則 `^X-[A-Z]+$` 只認單段 | 可同時 | `CGC_MDL246_ValidationSSOT_v0100.check` L214-252 | MDL246 **v0101**(換兩條正則,本體不動;8/8)+ 冊 **VIA_Validation_SSOT_v0101**(只增 4 碼 + 三系統 cross_check) | **綠**(`val` GREEN rc 0 · 交叉代碼 27) | AI |
| 2 | VCGC | 串測 P-ui_cmds | 紅 | Register-VIA-Commands 自 v0270 是 PS 薄尾(每版點源前版);站只讀尾版文字,章在 v0269 / v0273 | 可同時 | `CGC_MDL224_TestAuto_v0101.ps_check` L322 | TestAuto **v0106**:章對整條點源鏈(≤ 64 支 · 不迴圈 · 不在略過),章全在才 pwsh 語法檢;6/6 | **黃**(容器沒 pwsh,章在鏈上 7 支;工作站有 pwsh → 綠) | AI |
| 3 | VDF | 串測 C-vdf_fetch_groups_v0100–v0105(6 站) | 紅 ×6 | **不是網路**:v0100 自測 ⑫ 斷言 3 個庫,但 `_db_files` 的根含 VDF 活資料樞 `functional modules/VDF/output_hub`(2026-10-02 起有 vdf_tw_market.duckdb;工作站必有)→ 4 庫 → 整條鏈 FAIL | 可同時 | `VDF_MDL012_FetchGroups_v0100._db_files` L741 · `find_db` L358 · ⑫ L1154 | VDF_MDL012 **v0106**:只在自測跑前版鏈時把 find_db 換「只在自測家找」,跑完換回;正式路徑不動;4/4 · 鏈 10/10 · 9/9。六案標記釘 v0106(v0102 / v0104 / v0105 改跑尾版) | **綠 ×6**(handoff test 六案 rc 0 標記在) | AI |
| 4 | VCGC | SDD X-NUM(V-sdd · V-closeout ⑥) | 紅(4 支) | CGC_MDL183 v0105 · CGC_MDL140 v0107 沒編號;健康矩陣另列 VCGC 7 支 · VDF 4 支沒號 | 順序(先 registry-sync 再編號) | 編號冊 VIA_NumberBooks | registry-sync --apply(新 7 · 變 18)→ MDL237 --apply --scope 19 檔(+288 列)→ audit 遺失 0 · 改身分 0 · 重號 0 | X-NUM 只剩 VRN 2 支(見 #9) | AI |
| 5 | VCGC | 交接閘 5 紅(V-closeout ①⑨ · 全景閘「落後 482 · 快照 213h · 未登 102」) | 紅 | CHANGED_CODE_WITHOUT_TEST:ENG086 v0102(案要 polars)· MDL264 v0100(案要 pwsh)· VRN FirstPageEngine v0130(案要真 sidecar ≥ 20)· SUP_MDL749 v0116 / v0117(操作員 VRN 暫緩);checkpoint 紅就拒寫 → 全景閘永遠落後 | 順序(工作站先過五案 → checkpoint) | `CGC_MDL140_HandoverConsole_v0101.checkpoint` L293 | 容器不能過(不裝套件);工作站一貼(見三) | 紅(工作站可清) | 操作員(工作站) |
| 6 | VCGC | SDD X-LOCK 黃 6 處 | 黃 | 已鎖工作流尾版換了(MDL156 v0114 · MDL866 v0108 · MDL140 v0107 · MDL149 v0191 · VDF_SystemManager v0154 · VRN_SystemManager v0151) | 順序(交接綠 → real → lock) | `CGC_MDL245_SDDValidator_v0103.lock` L96(交接不綠拒寫) | 工作站交接綠後 `sdd real` → `lock --apply`(燈鎖冊下一版;VRN-WKF008 交 VRN) | 黃 | AI(工作站交接綠後) |
| 7 | VCGC/VDF | 串測 C-vdf_akshare_v0101 / v0102 · C-via_unified · P-entry / P-step1 / P-vdf_fill / P-vdf_groups_ui / P-ui_engine · V-ssot / V-check / V-panorama · QG-ENG086 | 紅 3 · 黃 9 | 容器環境:polars 缺 · pwsh 缺 · VIA_ENV_ROOT 沒設;不裝套件(操作員令) | — | — | 工作站環境齊就綠;容器照實 | 同 | 操作員(環境) |
| 8 | VRN | 串測 C-vrn_layout · C-first_page_engine · C-cov_vrn_firstpage_engine · V-systems(VRN logic 紅)· 健康矩陣 VRN lib 缺 pdfplumber | 紅 | reportlab 缺 · 真 sidecar 只在工作站 · VRN 邏輯冊紅 · pdfplumber 缺 | — | — | VRN 自己的 manager / 工作站;VCGC 只攤開(L120) | 同 | VRN |
| 9 | VRN | SDD X-NUM 剩 2 支 | 紅 | VRN_ENG086_FirstPageLogicBridge_v0120 · VRN_SystemManager_v0151(工作站 v0192)沒編號;L120「不改他系統的號」 | — | — | VRN 自己編(或操作員授權:`run CGC_MDL237_NumberingSystem --apply --scope <兩支>`) | 紅 | VRN / 操作員 |
| 10 | VCGC | E-number-audit FPSTALE 529 | 黃 | 529 / 800 本 SSOT 冊指紋過期(VCGC/SUP 336 · VRN 108 · VDF 85;無版號 275 · 有版號 254,多在 new modules engines / GroupIndex / intake 歷史件) | 順序(先定「活冊不驗指紋」規則) | `CGC_MDL237_NumberingSystem_v0109.fpstale` L355 | 重編只會再過期(活冊天天改);本輪不動,待編號規則分「活冊 / 凍結冊」 | 黃 | AI(下一輪) |
| 11 | VCGC | V-workflow 黃(NOT_RUN 44)· V-ssot-panorama 黃(要 --full) | 黃 | 工作流實測沒跑;SSOT 全景沒跑全量 | 順序 | — | `sdd real`(重;工作站)· `ssot panorama --full` | 黃 | AI |
| 12 | VCGC | 工作站主控台印 `SyntaxWarning: invalid escape sequence` | 黃 | 79 處 docstring 帶反斜線沒用 r"""(MDL156 v0114 L3 `\*` · MDL273 v0102 L6 `\C` …);Python 3.12+ 編譯時警告,容器 3.11 不印;掃描器重剖「變更檔」時冒出 | — | 各檔第 3 行 docstring | 不就地改已發布檔;各家族下一版用 r""";本輪新尾版已照做 | 黃(工作站 registry-sync --apply 後不再重剖) | AI(各家族下一版) |
| 13 | 三系統 | 健康矩陣「副本檔名 → DORMANT 候選」黃 · 版號有洞 | 黃 | `_sha` 存證副本是操作員 2026-10-10 裁定保留的;版號洞是歷史 | — | `CGC_MDL274_HealthMatrix` 語意判定 | 展現層可改「存證副本(裁定保留)」不計黃;本輪不擴 | 黃 | AI(下一輪) |

## 二、事後全景(容器)
(見本檔末「改後計數」;整輪 `test` 與健康矩陣在推送前重跑)

## 三、工作站一貼(操作員)
```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset
git fetch origin claude/kind-cannon-pti15g
git merge --ff-only origin/claude/kind-cannon-pti15g
cd VeritasIntelligenceAnalytics
$V = (Get-ChildItem "supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName
$env:VIA_FROM_VCGC = "YES"
# 1 交接五案(容器過不了的:polars · pwsh · sidecar · VRN 暫緩的唯讀自測)
foreach ($c in @("qg_onebridge","via_unified","first_page_engine","cov_vrn_firstpage_engine","vrn_ssot_consistency")) { python $V handoff test $c }
python $V handoff check
# 2 交接綠才做:快照 → 鎖成功版(燈鎖冊下一版)
python $V handoff checkpoint
python $V run CGC_MDL245_SDDValidator real
python $V run CGC_MDL245_SDDValidator lock --apply
# 3 跳出 U/I
python $V run CGC_MDL274_HealthMatrix matrix
python $V run --family vdf VDF_SystemManager ui
python $V run CGC_MDL261_UIEngine build --open
```
VRN 兩支編號(VRN 自己決定;若授權 VCGC):`python $V run CGC_MDL237_NumberingSystem --apply --scope "functional modules/VRN/VRN_ENG086_FirstPageLogicBridge_v0120.py" "functional modules/VRN/VRN_SystemManager_v0192.py"` → `audit`。
