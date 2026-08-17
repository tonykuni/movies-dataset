# VIA Zero-Hydra 修復與收編協議 v0100(SPEC-014)

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
