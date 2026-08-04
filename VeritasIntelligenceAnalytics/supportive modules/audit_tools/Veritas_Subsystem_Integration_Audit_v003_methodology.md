# Veritas Subsystem Integration Audit v003

## def 結論
目前 SSOT 已經進入可用的統一註冊階段，但還不是完全充分整合。v002 有完整的 append-only universe registry；v003 補上 data/lib/parameter 三層稽核與缺口矩陣。

## def 維護規則
- def 只增不減：舊列不得刪除；改動以 `status`, `preferred_current`, `superseded_by`, `duplicate_group` 表示。
- def Veritas ID：`veritas_id` 是穩定主鍵，不因去重重編。
- def Canonical Key：用於偵測同義/重複，不等於可以刪除。
- def Data Adapter：每個 dataset 必須有 source adapter、endpoint hint、field schema、freshness rule。
- def Library Registry：每個 subsystem 的 Python/PowerShell/lib/external binary 需求都要成為 SSOT row。
- def Parameter Contract：參數應外部 JSON 化，Python/PowerShell 只讀，不硬寫。
- def Validation：每次更新跑 schema|required|unique|append_only_diff|provenance_hash|capability_probe。

## def 智慧方法論
1. def Register：先登錄資料/函式庫/參數/介面，不直接 live fetch。
2. def Normalize：建立 alias map、unit map、ticker map、source map。
3. def Dedup：標記 duplicate_group，不刪行。
4. def Route：所有 functional modules 先接 NexusCore，再接 grouped frozen engines。
5. def Probe：用 dry-run capability probe 檢查 endpoint、import、schema、row count。
6. def Validate：用 HardGate 檢查 no mutation、no DB write、no canonical merge。
7. def Promote：只有通過 sequential review 的 staging row 才能進 canonical。

## def 下一步
- def Build `FetchPlanBuilder_v003`: 將 dataset/source adapter/asset universe 轉成 dry-run fetch queue。
- def Build `LibraryProbe_v003`: import/version/external binary/PowerShell module capability probe。
- def Build `ParamsSchema_v003`: VDF/VRN/FlowSystem/VAP/VETF/VIAS 各自 JSON schema。
- def Build `VRNIdentityRepairPlan_v003`: 只在 staging copy 修 report_id/date/broker issue。
