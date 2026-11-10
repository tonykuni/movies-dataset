# 操作員上傳 · VCGC MultiMatrix v0193 / v0194 等 5 件 · 入倉審查紀錄(2026-11-10)

操作員令:「授權一切整合 VCGC 功能強大 · 未來開發基礎建設完成於此」「先註冊記錄到每個細節 · 保持導入加速器及網路工具開口 · 標準化 · 整合去重補不足 · 測試無誤」。
本夾 = **byte-exact 收件 + 只讀審查**。沒有任何一件進 `supportive modules/registry/`(那裡的 `CGC_MDL149_*` 尾版就是 VCGC 入口,放進去等於上線)。
原件 SHA-256 見 `SHA256_originals.txt`;五件原樣包在 `upload_20261110.zip`。

## 1 · 收件

| 原件 | 大小 | 內容 | 歸屬(L123 / L125)|
|---|---|---|---|
| `VCGC_MultiMatrix_Integration_v0193.zip` | 2,080,736 B | 主控台 `CGC_MDL149_…_v0193.py`(1,070 行)· 離線頁 `VCGC_MultiMatrix_v0193.html` · README · QA_*.json · ReviewEvidence(snapshot + 9 個節點 JSON,~11 MB 解壓) | VCGC |
| `VCGC_MultiMatrix_Resilience_v0194.zip` | 89,692 B | 主控台 `…_v0194.py`(1,601 行)· `VCGC_MultiMatrix_v0194.html` · 20 項故障表 F01–F20 · Validation/(acceptance.py · adaptive_test.py · frontend_logic_test.cjs + 結果) | VCGC |
| `VIA_Settle_v0106.zip` | 39,213 B | `docs/handoff/ai/VIA_SettleAll_v0106.py` | VCGC(handoff)|
| `VIA_Settle_20261106_173158.zip` | 43,066 B | 桌機一跑的收據:settle · vrn2 · vdf · graphify · vqg · agent_os | 各系統自報(只讀)|
| `VAP_AllInOne_v0101.py` | 4,597,419 B | VAP All-in-One v0101(單檔 VQG→VAP 執行期 + 內嵌 UI;預設 127.0.0.1:8765) | **VAP**(不進 VAP 正本夾;只收在本 intake)|

## 2 · 驗證(只讀;**沒有執行任何上傳的程式**)

| 項目 | v0193 | v0194 |
|---|---|---|
| 包內 `SHA256SUMS.txt` | 17 / 17 相符 | 17 / 17 相符 |
| AST 剖析(MDL158 全景卡) | 過 · SWALLOW 4 | 過 · SWALLOW 8 |
| `git push` / `git commit` / `0.0.0.0` / 代設 `VIA_NET_CONSENT` | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| 子行程 · 改名 / 刪檔 | `subprocess.run` 2 · `Popen` 1 · `os.replace` 3 · unlink 4 | `subprocess.run` 4 · `Popen` 1 · `os.replace` 3 · `os.rename` 1 · unlink 5 |
| 自帶自測 / 故障測試 | **沒跑**(見 B6) | **沒跑**(見 B6) |

QA_*.json(Selftest / Integration / Resilience / UI)是對方環境自報,本倉**沒有重現**,不當成綠燈。

## 3 · 阻擋:為什麼現在不能把 v0193 / v0194 放成主控台尾版

| # | 問題 | 證據 | 影響 |
|---|---|---|---|
| B1 | **`matrix` 動詞被整個接走**:只要第一個參數是 `matrix` 就由 v0194 自己的 argparse 處理(14 個 action),不再交回原生 | v0194 L1171–1173;原生 `matrix` 門(`functions` 卡:「冊 × 啟動矩陣 × 引擎四態 × 修復候選」)仍被 `launchers/Invoke-VIA-AllInOne-v0111.ps1:625` 以 `matrix --family vdf,vrn,vap` 呼叫 | AllInOne 第 12 步會因 `--family` 不被接受而退出 → 紅;原生「冊 × 啟動矩陣 × 引擎四態」消失 |
| B2 | **自行發號**:install / register 自算 `VCGC-REQ` 與 `VCGC-WKF` 的「最大號 + 1」 | v0194 L865 · L868 | 違反 L125 ②(衝突未解期間編號留白,只由 VCGC 治理器發) |
| B3 | **自動寫冊 / 發號**:register 步驟依序跑 `registry-sync --apply`、`run CGC_MDL237_NumberingSystem --apply --scope` | v0194 L1395 · L1400 | `registry-sync --apply` 要操作員批准;衝突冊 OPEN 期間不發號(L125 ③) |
| B4 | **v0192 基準雜湊對不上**:包內基準 `66b1c49d…`(9,735 B);本倉與 main 的 v0192 都是 `5d968efa…`(9,734 B) | v0193 / v0194 `MERGE_BASELINE`;v0194 只核版號(L861)不核內容 | 很可能只差結尾換行,但「已知前版」的判定不比對內容 |
| B5 | **安裝閘本來就過不了**:install 要求原生 `test --quick` 綠 | 2026-11-10 本倉 `test --quick` 紅:`CGC_MDL237 v0119` 10/12、`CGC_MDL278` 8/9(撤掉本分支改動重跑結果相同,屬既有) | 照它自己的設計會停在安裝前 |
| B6 | **本工作階段不准執行外部上傳的程式碼**(自動模式擋下 `matrix selftest`) | — | 容器內沒有實測;實測要在操作員本機 |

## 4 · 其他上傳件

- `VIA_SettleAll_v0106.py`:上傳件 `4c80e095…` ≠ 本倉 v0106 `87062098…` → **同名不同內容**,依 L04 不覆蓋;main 已到 v0118,這份是舊線。
- Settle 收據(2026-11-06 17:31 · SettleAll v0105 · 分支 `claude/optimistic-goodall-yhalc5`):桌機環境 Python 3.13.7(`C:\Python313`)· pwsh 7 · duckdb 1.5.2 · pyarrow 24.0.0 · polars 1.40.1 → DuckDB 湖矩陣與 Parquet 在桌機可跑。
- `VAP_AllInOne_v0101.py`:VAP 自己的檔。依 L123 由 VAP 自己的 manager 決定入不入它的正本;VCGC 只留收件紀錄。

## 5 · 要整合時的做法(VCGC 出 v0195 薄尾;v0193 / v0194 原樣保留成版史)

1. `matrix` 只接 v0194 的 14 個 action;其他寫法(`--family` 等)一律交回原生鏈,或把新動詞改名(例:`mmatrix`)。
2. 拿掉自行發號:REQ / WKF 欄留白、只登列;發號照 L125 由 `CGC_MDL237 --apply --scope` 與治理器在衝突解完後做。
3. `registry-sync --apply` 與 `NumberingSystem --apply` 改成「印計畫、等操作員批准」。
4. 前版基準改成正規化後比對內容(去 CR、統一結尾換行),不只看版號。
5. 在操作員本機先跑(不加 `--apply`):`matrix selftest` · `matrix resilience-test` · `matrix install`(只出計畫),收據回傳後再決定。

## 6 · 貼上的建議清單 × 現有 VCGC 功能(去重 · 補不足)

| 建議 | 現有對應(不另造) | 結論 |
|---|---|---|
| 指令模組化 · 註冊表 · 依賴 / 衝突 | `CLAUDE.md` · `VIA_AI_FunctionCard_SSOT` · `VIA_VCGC_FunctionInventory_SSOT`(站 · 測法 · 豁免) | 已有;新動詞要登盤點冊,否則串測黃 |
| 每日早晨記憶膠囊(AgentMemory) | `handoff check` → `HANDOFF_latest.json` · token 卡 · MCP `via_receipt` / `via://…` 資源 | 已有;不另建第二份記憶 |
| 5 大矩陣(註冊 · 參數 I/O · 時序 · 拓撲 · AI 錯誤) | `matrix` · `ssot panorama` · `VIA_LakeMatrix`(DuckDB)· 上傳整合工作台頁 · MDL158 `read` 的錯誤分類 | 已有;B1 修好前 v0194 的 19 矩陣頁不上線 |
| AST 五級分類與定位器 | MDL158 `read` / `slice`(定義樹 · 行號 · SYNTAX / DUPDEF / UNREACH / BAREEXC / SWALLOW / MUTDEF / COMPILE / TAILAPI + 治理七類) | 已有 |
| 命名 `VIA_VRN_MDL002_…_v.012.py` | L126 ②:檔名四位版號 `_vNNNN`;系統段即歸屬(L125 ④) | **不採**(與憲法衝突) |
| 子系統 VSC / VRS | 不存在;現行 VCGC · VDF · VRN-2 · VQG · VAP + VRN-1(倉外只讀) | **不採** |
| 「嚴禁自動 push」 | 本倉做法:只推功能分支、不推 main、不自動合併 | 照現行 |
| Ruff 當加速器 | 鎖冊加速器席位 = VeritasCeleritas v1141;Ruff 不在鎖冊、未安裝 | 要用需操作員裝 + `tools activate` |
| Langfuse / Dify / Promptfoo / CrewAI 等外部平台 | L124 HARD FREEZE:不新增 Agent 框架 · 平台層 | **不採**(要解凍授權) |
| 網路工具開口 | `SUP_MDL740_NetUnified` → AegisNexus(雙閘)· `VIA_NetFetch` | 已有 |
| 加速器開口 | PY `[VIA:ACCEL-BRIDGE]` · PS `[VIA:PS-TEMPLATE]` / `[VIA:PS-ACCEL]` | 已有 |

## 7 · 下一步(操作員)

- 決定 B1–B4 的修法 → VCGC 出 v0195 薄尾;或先在本機跑第 5 點的三個指令把收據傳回。
- 本分支(`claude/practical-pasteur-p67i78`)比 main 舊;合併前要先接上 main(main 2026-11-10 `8fc49fff`)。

## 8 · 操作員本機實跑回報(2026-11-10 08:52–08:54 UTC · 照貼原文,未在本倉重現)

在 `C:\Users\tonyk\Downloads\mm194`(v0194 zip 解壓)以 `py -3` 執行:

| 指令 | 結果 | 範圍(引擎自述) |
|---|---|---|
| `matrix selftest`(兩次) | **45 / 45 PASS** · 12.7 s / 12.0 s | isolated fixtures;不證明 Windows VIA 正式環境 · `production_systems: NOT_RUN` · PS AST `AVAILABLE_NOT_CERTIFIED` |
| `matrix resilience-test`(兩次) | **22 / 22 PASS** · 2.2 s · `engine_sha256 66e83333…`(= 上傳件) | 合成故障注入;沒有 Windows 部署、沒有 VDF 實網驗證 · `production_systems: NOT_RUN` |
| `matrix install --roots "$HOME\OneDrive\Documents\movies-dataset"`(只出計畫) | **停:`UNSUPPORTED_NATIVE_PRIOR; known v0192/v0193 only, no blind upgrade`** | 本機倉的主控台尾版不是 v0192 / v0193 → 它拒絕升級(設計如此,不是故障) |

更新:B6 部分解除(引擎自帶測試在本機綠);B1–B4 不變(那是設計問題,自帶測試不涵蓋);B5 之前就先停在版本檢查。
下一步:查本機尾版是哪一版、本機倉在哪個分支、落後 / 超前 main 多少,再決定 v0195 要接哪一版。
