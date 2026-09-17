# VIA／VRN／VDF／VAP B527：統一 SSOT 與附件自動編碼整合交接

**驗收批次：** B527
**驗收時間：** 2026-09-16 10:17 UTC
**中央入口：** `CGC_MDL149_VeritasCentralGovernanceConsole`
**新增中央橋：** `CGC_MDL155_VIAUnifiedSSOTAutoCode_v0100.py`

## 結論

附件 `VIA_AutoCodeGenerator.py` 已完成收容、掛載與中央註冊。它現在由 `CGC_MDL155` 作為 VIA 唯一受控入口使用。既有 VIA Naming Registry、Component Inventory 與 Interface Contract Registry 仍是系統正典，因此本次整合**沒有重發既有編號，也沒有改名實體檔案**。

本批的程式與中央治理驗收均通過。`CGC_MDL155` 自測為 **9/9**，中央治理主控台為 **19/19**，中央治理家族為 **12/12**，Workflow Composer 為 **12/12**。介面契約最後掃描為 **0 新編、0 漂移、2780 穩定、1 語法錯誤誠實跳過**；中央元件冊最後同步為 **4953 個 active 元件、0 新增、0 變更、0 退役、0 AST 錯誤**。

總裁決仍標為 **YELLOW**，原因只有一項：`functional modules/VRN/db/vrn_reports.duckdb` 尚不存在。此缺口沒有被建立空資料庫掩蓋，也沒有被標成 GREEN。系統、引擎、VRN/VDF/VAP/CGC 子系統、Regex/同義字、參數、因子、模組與收容狀態均已被明確記錄；真正的 VRN 報告資料庫必須在 VRN 結構化入庫合約與可讀取的報告樣本到位後再建立。

## 這次整合的內容

`VIA_AutoCodeGenerator_v0100.py` 是使用者附件的收容副本，SHA-256 為 `644a99a8c63e988b51f00106e33f7074c1bc285a81169a09a88ba2702988a47c`。既有 `VIA_AutoCode_Registry_v0100.json` 已將它記錄為 `SPT-002`，並新增 CodeChain、KNO、IDX、PRD 與 `CGC-SSOT-` 共存命名空間。

`CGC_MDL155` 會讀取現有正本而不複製或覆寫它們。來源矩陣已涵蓋 Regex／同義字、VRN 邏輯、VIA 參數、QuantGuard 因子、VDF DuckDB、VIA 模組冊、系統狀態與 VRN 收容模組。收容目錄只做存在性、雜湊與狀態盤點，並以 `quarantine_execution=FORBIDDEN` 固定禁止執行。

Regex 與同義字已完成合併。結果為 **12 個 Regex、310 個同義字、0 個未解衝突**。其中 35 個是跨正本的語意合併，例如 `PRICE_TARGET → TARGET_PRICE`、`BASIC_EPS → EPS` 與 `DILUTED_EPS → EPS`。`合理價` 實測分類結果為 `TARGET_PRICE`，命中 3 個來源。

附件自動編碼器的四種協定已在隔離 SSOT 中實際產生並互相連結，結果如下：

| 協定 | 實測結果 |
| --- | --- |
| CodeChain | `VIA-VRN-MDL001-FNC001-VIA_CENTRAL-V1.0` |
| KNO | `KNO-TA-TW-MOMENTUM-RSI-VIA-D-V1-0001` |
| IDX | `IDX-TW-TW-EQUITY-2330-TWSE-D-V1-0001` |
| PRD | `PRD-EQUITY-TW-STOCK-2330-TWSE-D-V1-0001` |
| Governance link | `LNK-0001` |
| Isolated health | `GREEN`, 1/1/1/1 object counts, 0 issues |

## 中央掛載結果

`via_ssot_autocode` 已寫入 VIA InputConsole 的中央 acceptance group，並新增 `via_ssot_autocode_governance` 測試工作流。PowerShell 命令冊已加入 `via-ssot` 與中文別名 `SSOT治理`。可用命令包括 `selftest`、`status`、`manifest`、`routes` 與 `classify <text>`。

自動命名冊沒有覆寫既有編號。中央實際解析結果如下：

| 實體家族 | 中央 canonical | 介面 URN |
| --- | --- | --- |
| `CGC_MDL155_VIAUnifiedSSOTAutoCode` | `CGC_MDL182_CGCMDL155VIAUnifiedSSOTAutoCode` | `VIA-IFACE-3753` |
| `VIA_AutoCodeGenerator` | `CGC_MDL183_AutoCodeGenerator` | `VIA-IFACE-3754` |

檔名中的 `CGC_MDL155` 是本批功能橋的版本標識；中央 append-only 命名冊依既有序號狀態配置 canonical 編號，因此沒有與既有 `CGC_MDL155_CGCMDL130UIBridge` 發生重編或覆寫。

## 來源與狀態矩陣

| 類別 | 存在數 | 缺口 | 狀態 |
| --- | ---: | --- | --- |
| Regex／同義字 | 5/5 | 無 | GREEN |
| 邏輯庫 | 2/2 | 無 | GREEN |
| 參數庫 | 4/4 | 無 | GREEN |
| 因子庫 | 3/3 | 無 | GREEN |
| VDF／VRN 資料庫 | 2/3 | `vrn_report_db` | YELLOW |
| 模組庫與中央冊 | 8/8 | 無 | GREEN |
| 系統狀態來源 | 3/3 | 無 | GREEN |
| 收容來源 | 2/2 | 無；執行仍禁止 | GREEN / FORBIDDEN |

系統狀態為 **GREEN**，引擎狀態為 **GREEN**，VRN、VDF、VAP 與 CGC 子系統均為 **GREEN**。資料狀態為 **YELLOW**，只反映 VRN 報告 DuckDB 尚未存在。

## 可重跑命令

在 Linux 驗收環境中，使用下列命令可取得同一份結果：

```bash
PY=/home/ubuntu/work/quantguard_venv/bin/python
ROOT=/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics

"$PY" "$ROOT/supportive modules/registry/CGC_MDL155_VIAUnifiedSSOTAutoCode_v0100.py" selftest
"$PY" "$ROOT/supportive modules/registry/CGC_MDL155_VIAUnifiedSSOTAutoCode_v0100.py" status
"$PY" "$ROOT/supportive modules/registry/CGC_MDL155_VIAUnifiedSSOTAutoCode_v0100.py" classify '合理價'
```

在已載入 `Register-VIA-Commands-v0208.ps1` 的 Windows VIA 工作站中，使用：

```powershell
via-ssot selftest
via-ssot status
via-ssot classify 合理價
# 或：
SSOT治理 manifest
```

## 後續唯一阻擋項

下一步不是再增加別的自動編碼器，而是依 VRN 結構化資料庫正本契約建立 `vrn_reports.duckdb`。在實際報告 PDF/DOCX 已掛載且 ENG073 結構化入庫成功前，不應建立空表來取得假 GREEN。完成後需重新執行 `CGC_MDL155 status`、`via-functional-acceptance`、VRN ENG073、VCGC 與 Workflow Composer，並以新一批證據更新本報告。

## References

[1]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/supportive%20modules/registry/CGC_MDL155_VIAUnifiedSSOTAutoCode_v0100.py "CGC_MDL155 VIA 統一 SSOT／自動編碼中央橋"

[2]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/supportive%20modules/registry/VIA_AutoCodeGenerator_v0100.py "VIA 自動編碼器附件收容副本"

[3]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/ssot_autocode/VIA_SSOT_AUTOCODE_latest.json "VIA 統一 SSOT 自動編碼機器狀態"

[4]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/supportive%20modules/registry/VIA_AutoCode_Registry_v0100.json "VIA 自動編碼中央註冊表"

[5]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/supportive%20modules/registry/VIA_InputConsole_Spec_v0100.json "VIA InputConsole 中央輸入契約"

[6]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/supportive%20modules/registry/VIA_Workflow_SSOT_v0100.json "VIA Workflow SSOT"


## B528 附錄：VRN 報告資料庫已建立並驗收 GREEN

B527 原先記錄的唯一 YELLOW 缺口是 `functional modules/VRN/db/vrn_reports.duckdb` 尚不存在。B528 已透過 ENG072→ENG073 實際處理兩個倉內可讀取的收容樣本，建立實體 DuckDB 並寫入 2 筆 `vrn_report_basic`。指定資料庫 `--status`、只讀 SQL 與 ENG073 自測均已驗證，ENG073 自測為 **36/36 PASS**。因此 B527 機器狀態已更新為 **GREEN**。

本次 GREEN 只代表 VRN 報告資料庫的存在性、結構、可讀取性、可重跑性與自測驗收已通過。使用者提供的 Windows 路徑清單共 64 份原始 PDF/DOCX 尚未掛載到本 Linux 沙盒，因此華南投顧、凱基投顧等原始檔的內容級驗收仍標記為 `PENDING_MOUNT`，沒有被本批假稱已完成。

B528 完整交接：`VIA_B528_VRN_DATABASE_ACCEPTANCE_HANDOVER.md`。機器狀態：`VIA_B528_VRN_DATABASE_ACCEPTANCE_STATUS.json`。

## References

[7]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/handover/VIA_B528_VRN_DATABASE_ACCEPTANCE_HANDOVER.md "B528 VRN 報告資料庫驗收交接"

[8]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/handover/VIA_B528_VRN_DATABASE_ACCEPTANCE_STATUS.json "B528 VRN 報告資料庫機器狀態"

[9]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/functional%20modules/VRN/db/vrn_reports.duckdb "VRN 報告結構化 DuckDB"

[10]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/handover/b528_visuals/B528_PASS_AND_COMPONENTS.png "B528 PASS 與中央元件冊圖表"

[11]: file:///home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/handover/b528_visuals/B528_ACCEPTANCE_DASHBOARD.html "B528 離線驗收儀表板"
