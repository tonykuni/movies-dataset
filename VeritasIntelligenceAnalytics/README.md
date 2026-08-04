# Veritas Intelligence Analytics(VIA)

台股/全球市場情報平台:資料鍛造(VDF)× 自動繪圖(VAP)× 研報擷取(VRN),
以 SSOT 單一真相與 hash 鎖定治理貫穿。**2026-08-04 全系統整合收官版。**

---

## 快速開始

```powershell
# 第一次(或新機器):一鍵布建(冪等、免管理員)
pwsh -File "VeritasIntelligenceAnalytics\Install-VIA.ps1"     # 加 -AutoStart 可開機自啟
```

之後任何終端機、任何目錄:

| 指令 | 作用 |
|---|---|
| `via` | 同步 + VDF 進料 + VAP 繪圖 + 自動開 UI(日常預設) |
| `via-all` | 互動全套:VDF + VAP + VRN 預檢 + Control Tower(不含長跑稽核,不卡斷) |
| `via-audit` | 長跑稽核三件套:TurboOptimizer SafeAudit + Panorama + Polyglot(預期數分鐘以上) |
| `via-tower` | 治理總控台 `http://127.0.0.1:8765`(桌面捷徑同此) |
| `via-shim` | TickerRegex v0100 墊片入口:`via-shim -Target <檔> [-DryRun]` |
| `via-sync` | repo 同步(fetch + merge claude 分支 + push main) |
| `via-batch` | **VRN 批次**:incoming 全部 PDF 過 No-OCR 生產線(並行池、可續跑;`-Fresh` 全部重跑) |
| `via-import` | manifest 匯入:Downloads 批次去重入庫(清單由 Claude 寫進 `import_manifests/`) |
| `via-vmt` | VMT SuperBOM 總指揮(via_master_engine:問卷→附件→收斂→CPM,缺件優雅略過) |
| `via-vdf` | VDF 一鍵側欄工作台(v0160C 一般瀏覽器 HTML U/I + 本機 HTTP 橋;SHA256+AST 閘門;回退 v0102/v0101) |

## 系統架構

```
functional modules/
├── VDF/   資料鍛造:進料引擎(GREEN gate)、MDL001-006 擷取引擎、
│          registry/(擷取登錄 Schema/Full 238 項/覆蓋率/資料源矩陣 77 項)、六槽標準
├── VAP/   自動繪圖:engine v001(正本)+ chartlib_v002(UNIT03 晉升版)、
│          Workbench v009/v010、spec/(視覺鎖三層,見下)
└── VRN/   研報擷取:生產線 v1.1.0(MDL001-008,manifest hash 9/9)、
           TrustPolish v04.4、Incremental DB AIO、Finalize AIO、SSOT 鏈、六槽標準
supportive modules/
├── ssot/、registry/、audit_tools/       真相層、登錄層、稽核紀錄(永不改寫)
├── 70_VRN_Rules/                        規則模組(TickerFilename SSOT、墊片、券商別名…)
├── VIA_Canonical_Units/                 UNIT03 治理管線(v0109-v0113)+ 判定表
├── VIA_Control_Tower/                   HTML 總控台 v005(Veritas 鎖定版式)
└── bin/ + Install-VIA.ps1(於 VIA 根)   五指令 + 一鍵布建
```

## SSOT 總表(現役真相)

| 真相 | 檔案 | 版本 |
|---|---|---|
| 股號規則 | `supportive modules/ssot/VRN_TickerRegexSSOT_v0100.json` | v0100 ACTIVE:四碼首碼非零;2021–2030 交消歧層,**年份排除不得寫入 regex** |
| 消歧實作 | `supportive modules/70_VRN_Rules/VIS_VRN_TickerFilenameSSOT_v0100.py` | 首頁股號 0.97 / 官方清單 0.9 / 日期線索→YEAR / 無佐證→AMBIGUOUS 人工覆核 |
| VAP 繪圖規範 | `functional modules/VAP/spec/ssot/vap_spec.json` | v1.0.0(線粗 1、line 0.9、區域 0.75、柱 0.6/0.8、via 色票鎖定) |
| VAP 圖庫 | `functional modules/VAP/spec/ssot/vap_chartlib.json` | v1.0.1(28 型 VAP-CH-01…28) |
| 視覺判定表 | `supportive modules/VIA_Canonical_Units/VAP_VisualLock_Adjudication_Table_v002.json` | v002 分項閘(方案 A);Seaborn 0.80 為獨立域 |
| Header 鎖 | `functional modules/VAP/spec/Veritas_Header_Masthead_1d.html` | 1d LOCKED(幾何/色票/字體不得覆寫) |
| VRN 資料契約 | `functional modules/VRN/registry/VRN_REPORT_*_SSOT_v0100.json` | v0100(parquet 正本 + DuckDB 鏡像) |
| VRN 生產線 | `functional modules/VRN/registry/VRN_Production_Manifest.json` | v1.1.0(核心模組 SHA256 錨定) |

## 治理原則(不可違背)

1. **只增不減**:SSOT 修改必升版 + changelog;稽核紀錄(audit_tools)永不改寫。
2. **正本不就地修改**:runtime 墊片(`via-shim`)或版本前進(new file);被取代版本進 `_superseded/` 隔離,不刪除。
3. **hash 鎖定交易**:任何晉升附 SHA256 前後對照與 PROMOTION_RECORD。
4. **fail-closed**:替換次數不符、hash 漂移、原因不唯一 → 一律中止不寫檔。
5. **巨檔紅線**:>45MB 永不入 git(.gitignore 已鎖 iconforge 與 v141D6 七檔);產出物(db/output/temp)不入庫。
6. **九頭龍防治**:同名檔以 SHA256 判 REDUNDANT_COPY(去重)或 VERSION_CONFLICT(裁決),不放任並存。

## 日常工作流

- **研報進料**:PDF 丟 `functional modules/VRN/input/incoming/` → Tower 按 intake → probe → lanes → run。
- **舊模組用新股號規則**:`via-shim -Target "functional modules\VRN\VRN_MDL001_StockReportPipeline.py"`(先 `-DryRun` 看報告)。
- **收尾/稽核**:Tower「收尾流程」FLOW A–F(唯讀提案型)與 20 加速器。
- **凍結債務**:106 個舊 regex 檔案見 `audit_tools/TickerRegex_LegacyDebt_Census_v0100.json`(16 墊片候選/53 稽核紀錄/8 已隔離/29 待自然升版)。

## 疑難排解

| 症狀 | 處置 |
|---|---|
| push 被拒 non-fast-forward | `via-sync`(內建 fetch+merge+push;必要時 `git pull --rebase --autostash origin main`) |
| pull 被本機修改擋住 | `git stash push -- <檔>` → pull → push → `git stash pop` |
| 貼上長腳本被截斷 | 不要貼長腳本——一律用 repo 內腳本 + `pwsh -File`(本平台鐵律) |
| ps1 疑似語法錯 | `[System.Management.Automation.Language.Parser]::ParseFile()` 做正式 AST 驗證 |
| 範疇已凍結項目 | 見 `audit_tools/VIA_ScopeFreeze_Closure_v0100.json`;重開需操作員點名 |

---
*營運手冊 2026-08-04 · 對應 Control Tower v005 / TickerRegex v0100 / VRN v1.1.0 / 判定表 v002*
