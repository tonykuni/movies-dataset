# VIA Zero-Hydra 修復與收編協議 v0101(SPEC-014)

操作員令(2026-08-17):錯誤分類雙軌+AST 精準/彈性定位+免疫九頭龍+
編號註冊+可同步流程最大併發。本文=常備協議(結構化封存,誠實態)。

## 最高指導原則(Zero-Hydra Risk Policy)
- 代碼變更一律經 AST 節點定位:**彈性定位**=模組語意層(類/函式/匯入拓撲);
  **精準定位**=行號+節點。嚴禁碰未受感染命名空間;健康度不得退化。
- 紅線覆蓋顧問建議:零刪除(封存搬移+manifest+undo)、不開第三根
  (Core/Plugins 落倉內 system_core/plugins_pool,git 版控=真 Add-Only)、
  URN 獨立名空間(VIA-CORE/VIA-PLUG-####,與 TOOL/ENG/SPEC 共存)。

## Stage-Gate 管線
| Phase | 內容 | 落地引擎 | 態 |
|---|---|---|---|
| P1 診斷分類 | AST 掃描→錯誤分「可同步軌」(逐檔獨立:語法錯/格式遺漏)與「順序軌」(跨模組依賴/狀態流轉,依賴拓撲由底至高) | via-intake ①(py ast.parse+ps1 pwsh AST)/sysman C1/C4 | IMPLEMENTED |
| P2 雙軌自癒 | A 軌批次同步修;B 軌依拓撲順序修(讀→定位→修→驗) | 建議制:sysman 列示+人裁;自動修 NOT_RUN(誠實) | PARTIAL |
| P3 檢視+註冊 | 二次 AST 歸零確認→URN 賦碼→SSOT 建檔 | via-intake ②③(語法敗不收編) | IMPLEMENTED |
| P4 併發編排 | 互不依賴流程併發(寫集互斥五要件),依賴者阻塞等待 | via-auto 五站並行/via-tables 輕車道併發/重車道子行程 | IMPLEMENTED |

## 分層收編拓撲(Truth-by-Filename)
- CORE 鍵詞:CentralGovernance/MotherRoot/SystemManager/SmartSync/SSOT/IDNumbering/Governance → system_core/
- PLUG 鍵詞:VDF/VRN/VAP/SixFlow/HTML/Flow/VisualLock/FIS/Recovery/Rehydration… → plugins_pool/
- ARCHIVE:_EXTRACTED/DryRun/_Deploy/過渡 zip → 來源側 _VIA_Intake_Archive/(零刪除)
- (N) 副本:hash 對本體——全同=封存;**不同=HOLD 候裁**(檔名不定生死)
- 語法敗:列示不收編(可同步軌逐檔修後重進)

## 靜態報表規約
高資訊密度、確切數字、零動畫:Total Scanned/Registered/Archived/HOLD +
URN | Action | Version | Status 清單;存證 VIA_Reports/intake_runs/。


## v0100→v0101 增補(操作員令 2026-08-18)

### 錯誤分類法 E01-E15(同步/順序分流依據)
E01 Syntax/AST(不同檔可同步)· E02 Command/Parameter(視共用入口)·
E03 Type/Schema(通常順序)· E04 Path/Environment(查同步/修順序)·
E05 Import/Dependency(依拓撲)· E06 SSOT/Registry(強制順序)·
E07 Synonym/Regex(測同步/發布順序)· E08 Data Contract(順序)·
E09 Concurrency/Lock(強制順序)· E10 Runtime/Process(分子系統同步)·
E11 Performance(析同步/驗逐項)· E12 UI/Rendering(獨立 UI 可同步)·
E13 Security/Integrity(Fail-Closed)· E14 Integration(依資料流順序)·
E15 Activation/Rollback(強制順序)

### Parallel-Fixable 十條件(全符才入同步批;缺一轉順序軌)
WriteSet 零重疊/不寫共同 SSOT·Registry·Lockfile·Launcher·Manifest/
不變公開簽名·Schema·ID·Owner/不動他系統環境依賴/可完整回復/
獨立 RunDir·Port·DuckDB Connection·Evidence/Hydra=LOW/
Targeted Test 可獨跑/敗不斷他 Lane/零 Activation·Promotion·Canonical Mutation。
同步判定=WriteSet+Dependency+SSOT Owner+Hydra 四項共判,非「不同子系統」即同步。

### AST 四級定位(A1-A4)
A1 Exact Node(唯一命中→可自動修)· A2 +Symbol Context(Hash 驗證後可修)·
A3 Elastic Semantic(只產候選 Patch)· A4 Text/Regex Fallback(人工/沙盒複核)。
每 Patch 必記:源 SHA-256/節點種類/Symbol/定位範圍/前後片段 Hash/
命中數(非唯一不得自動套)/影響呼叫者/回歸測試編號。

### 編號規約(先發先得;與 TOOL/ENG/VIA-IFACE 共存)
RUN-{ts}-{系統}-{輪} · VIA-ERR-{子系統}-{E類}-{流水} · VIA-FIX-{子系統}-{流水} ·
VIA-TST-{層}-{子系統}-{流水} · VIA-PL-{子系統}-{號} · VIA-ART-{類}-{Hash8} ·
VIA-GATE-T0~T9 · VIA-HOLD-{因}-{流水}

### 三輪流程摘錄
R1 全景唯讀掃+Parallel-Fixable 批修(各 Lane 獨立沙盒)→
R2 拓撲順序修(路徑→語法→依賴→SSOT→Data→系統內→跨系統→UI→Launcher→Activation,每節點 Targeted Test 敗即停下游)→
R3 重掃+全回歸+DeepDiff 對 R0;三輪未過=HOLD_REMEDIATION_REQUIRED 不假 PASS。

### 落地對照(誠實態)
T0 稽核=via-t0(TOOL-042 IMPLEMENTED AUDIT-ONLY)· E 分類引擎=NOT_RUN(候)·
智慧化介面引擎=ContractEngine v0200 已在(Pydantic 契約+DI+Twin;32/32+19/19)·
四層測試工具=via-plan 段 9-10 dry-run 先測(第二批 Pester 屬 PowerShell 模組,
Install-Module 非 pip——候裁另軌)。
