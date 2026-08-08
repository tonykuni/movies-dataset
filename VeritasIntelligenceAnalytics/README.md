# Veritas Intelligence Analytics(VIA)

台股/全球市場情報平台:資料鍛造(VDF)× 自動繪圖(VAP)× 研報擷取(VRN),
以 SSOT 單一真相與 hash 鎖定治理貫穿。**2026-08-05 全綠穩態版(Mega 10 域 1208 檔 GREEN)。**

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
| `via-one` | **全系統總啟動器 v0110**:十四階段一支到底(DEPS 預檢+sync+Mega+VMT+CGE+VRN×2+FLOW+IF+FIS+**WORKOPS+FORGE+BRIDGE**+Hub 活化,引擎全動態最新版)或 `-Only <鍵>` 選子系統看 U/I |
| `via-all` | 互動全套:VDF + VAP + VRN 預檢 + Control Tower(不含長跑稽核,不卡斷) |
| `via-audit` | 長跑稽核三件套:TurboOptimizer SafeAudit + Panorama + Polyglot(預期數分鐘以上) |
| `via-tower` | 治理總控台 `http://127.0.0.1:8765`(桌面捷徑同此) |
| `via-shim` | TickerRegex v0100 墊片入口:`via-shim -Target <檔> [-DryRun]` |
| `via-sync` | repo 同步(fetch + merge claude 分支 + push main) |
| `via-batch` | **VRN 批次**:incoming 全部 PDF 過 No-OCR 生產線(並行池、可續跑;`-Fresh` 全部重跑) |
| `via-import` | manifest 匯入:Downloads 批次去重入庫(清單由 Claude 寫進 `import_manifests/`) |
| `via-vmt` | VMT SuperBOM 總指揮 v0103(Porcelain 刊頭;問卷→附件→收斂→CPM,缺件優雅略過) |
| `via-vmt-init` | VMT 資料層 bootstrap:OneShot 對準 VMT 根建 DB/SSOT 種子 + 跑郵件器 + Command Center |
| `via-mega` | 公定處理模式 v0108:三輪全景 **14 域**(+巢狀 git repo 圍堵)(+WORKOPS/FORGE/STORAGE)x 20 加速器 x Matrix;參數置頂可增減(`--set k=v`)、附掛掃描根、parquet 增量 store(DuckDB)、rich 摘要矩陣;hydra 僅平台域+慣例檔名白名單;SSOT 9 項 |
| `via-code` | 自動識別編號器:`via-code <類別> <元件> [suffix]`(冪等給號;`--list`;`--register`) |
| `via-gov` | 中央治理引擎 CGE v0401:TAB 多頁儀表板+台股登記簿 1977 檔(dry-run 預設;`--commit`;`--fetch-tw`) |
| `via-vdf` | VDF 一鍵側欄工作台(v0160C 一般瀏覽器 HTML U/I + 本機 HTTP 橋;SHA256+AST 閘門;回退 v0102/v0101) |
| `via-flow` | FlowSystem OneShot v0101:五鏡頭 FIS+fusion+五 QA 閘+自產 **Porcelain** UI(漲跌色功能語意保留;run-local) |
| `via-if` | VIA-IF 產業預測整合引擎:唯讀掃描+append-only 輸出(`--selftest` 自檢) |
| `via-fis` | FIS 驗證 harness v3:E1/E2/E3 實驗+Matrix 報告(需 `py -m pip install scipy`) |
| `via-pipe` | 統一輪動引擎(回測+自演化+證偽;**待同伴檔 rotation_engine.py 補齊**) |
| `via-envfix` | EnvManager 決策式無衝突安裝:五依賴 plan-install 留痕 → NumPy 黃金律 constraints → py 基底聯合安裝 → pip check 後驗 |
| `via-bridge` | **Command Bridge**:一鍵前後端對接——後端 B1-B5 探測(接線/SSOT/依賴/資料庫/UI)+ test/debug 三輪 + 多 TAB 前端,首頁=總覽+全系統狀態矩陣(每跑必重生=當下真相) |
| `via-trinity` | 功能三系整合模板:VIA 母刊頭 > 鍛 VDF/研 VRN/鑑 VAP 四 TAB(Porcelain;22 個 {{…}} 資料綁定槽) |
| `via-workops` | **WorkOps 指揮板**:一支到底=唯讀掃描+控管表自動對帳+兩頁指揮板(①專案指揮 ②追蹤哨,≥3 天未回主動跳出);`ui` 開靜態儀表板;`Scan\|Reconcile\|Draft\|FollowUp\|Templates\|All` 走引擎非互動面 |
| `via-forge` | **VIA_Forge 五引擎家族**(45/45 驗收):無參數開工作台 UI;`check` 跑驗收矩陣;`server` 啟本機服務(127.0.0.1) |
| `via-storage` | **Storage Optimizer AIO**:預覽制清理(雙引擎+GUI;`-Execute` 才刪;`-TestAll` 全鏈測試;`.veritas_protect` 禁區跳過) |
| `via-pack` | 子系統獨立打包:`via-pack <cge\|mega\|bridge\|audit\|flow\|if\|vmt\|tools>` — 產品號自動編號(PKG 序號×內容 SHA8,冪等)+ **單機綁定**(Install 綁主機指紋、Launch 驗證,不符 fail-closed)+ **每包自帶封面 U/I**(產品/綁定/manifest 矩陣/報告出口,Launch 自動開)+ 逐檔 SHA256 manifest + zip |

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
├── ssot/、registry/、audit_tools/       真相層(+同義字引擎/種子)、登錄層(+編號器)、稽核紀錄(永不改寫)
├── 70_VRN_Rules/                        規則模組(TickerFilename SSOT、墊片、券商別名…)
├── VIA_Canonical_Units/                 UNIT03 治理管線(v0109-v0113)+ 判定表 + 晉升記錄
├── VIA_Control_Tower/                   HTML 總控台 v005(Veritas 鎖定版式)
├── VIA_Governance_Runtime/              Mega 引擎 v0100-v0102、v0160A/B/C 工作台家族、installers(OneShot 等)
├── VMT_SuperBOM/                        VMT 引擎家族 + master engine v1.0/v0101/v0102 + BatchMailer + SuperBOM 財務模型
├── VIA_Central_Governance/              CGE 引擎家族 v0100-v0401(唯一正本家)+ TW 登記簿快照
├── specs/                               規格文件庫(宏觀 md 11 篇 + MI 附錄 + EarningsInsight)
├── VIA_FlowSystem/、VIA_Pipeline/、     FlowSystem+FIS 家族、pipeline/io/devils_advocate、
│   VIA_IF_Engine/、VIA_EngineForge/     VIA-IF 引擎、EngineForge 方法論+協調器(批次 G 歸位)
├── ui_support/                          UI 歸檔 base(Hub v0103 + Flow Console + 40+ 儀表板)
└── bin/ + Install-VIA.ps1(於 VIA 根)   20+ 指令 + 一鍵布建
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
| 設計鎖 tokens | `supportive modules/ssot/VIA_DesignLock_SSOT_v0102.json` | v0102 ACTIVE(視覺鎖源=VAP_Workbench_v009:暖紙底+墨印+六彩 accent;Porcelain v0101 降前代保留;回退=改引 v0101) |
| 公定處理模式 | `supportive modules/ssot/VIA_MegaPrompt_OfficialMode_v0100.md` | v0100(三輪硬性上限、20 加速器、沙盒循環;執行載體 `via-mega`) |
| AI 撰寫規範 | `supportive modules/ssot/VIA_AICodegen_Prompt_SSOT_v0103.md` | v0103(地板 one v0107/vmt v0103/Hub Live;**動態解析鐵律**嚴禁寫死版號;ENG/PKG 取號義務) |
| 欄位 regex 庫 | `functional modules/VRN/InvestmentRegexPattern_VALIDATED.py` | v3.0 ACTIVE(525 patterns;PROMOTION_RECORD 錨定 SHA256) |
| 同義字引擎 | `supportive modules/ssot/via_synonym_engine_v0100.py` + Seed | v0100 ACTIVE(41 canonical 錨點;同義字增量只增不減) |
| 編碼註冊中心 | `supportive modules/registry/VIA_AutoCode_Registry_v0100.json` | v0100(八架構類別+泛用狀態;六共存域不侵入;`via-code`) |
| regex/同義字普查 | `supportive modules/ssot/VIA_RegexSynonym_Census_v0100.json` | v0100(四族無遺漏;兩遺漏已晉升) |

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
*營運手冊 2026-08-06 · 對應 Tower v005 / Mega v0106 / VMT v0103 / VDF 工作台 v0160C / UI Hub Live(活化樞紐)+ 靜態 v0108 回退 / TickerRegex v0100 / VRN v1.1.0 / 判定表 v002*
