# VCGC 規則冊 / SSOT 優化 + DataFrame 標準化 卡(20261006)

> 唯讀 VDF/VRN。紅 = 要修;黃 = 待裁;灰 = 非表。契約 VIA_DataFrameContract_SSOT_v0100 DF01–DF11。

## 貼回包
```
[計] vcgc books · 2026-10-06T03:32:23 · 總燈 YELLOW · VCGC 冊 66 紅 0 黃 49 綠 0 灰 17 · VDF 冊 4 紅 0 黃 3 綠 0 灰 1 · VRN 冊 80 紅 0 黃 58 綠 0 灰 22 · 表頭定案冊 VIA_Output_Header_SSOT_v0101.json(14 表)· pandas True
[計] 形狀 · VCGC:CSV=2 · VCGC:JSONL=1 · VCGC:NESTED=61 · VCGC:TABLE=2 · VDF:CSV=1 · VDF:MAP=1 · VDF:NESTED=2 · VRN:CONFIG=2 · VRN:CSV=2 · VRN:JSONL=5 · VRN:NESTED=69 · VRN:TABLE=2
  [YEL] VCGC GovernanceRegistry.json · CRLF;表頭定案冊無此表
  [YEL] VCGC VIA_ActivationGateway_v02_Hotfix_Manifest.json · CRLF;表頭定案冊無此表;rows:數字存字串欄 1;非 snake_case 欄 12
  [YEL] VCGC VIA_ActivationGateway_v03_StableHotfix_Manifest.json · CRLF;表頭定案冊無此表;rows:數字存字串欄 1;無主鍵候選;非 snake_case 欄 12
  [YEL] VCGC VIA_ActivationGateway_v04_InlineReady_Manifest.json · CRLF;表頭定案冊無此表;rows:數字存字串欄 1;無主鍵候選;非 snake_case 欄 12
  [YEL] VCGC VIA_ActivationGateway_v05_ParamFirst_Manifest.json · CRLF;表頭定案冊無此表;rows:數字存字串欄 1;無主鍵候選;非 snake_case 欄 12
  [YEL] VCGC VIA_Canon_Registry_v0100.json · CRLF;表頭定案冊無此表;entries:格內巢狀欄 4;無主鍵候選
  [YEL] VCGC VIA_Central_Params_SSOT_v0100.json · CRLF;表頭定案冊無此表;locked_alignment:格內巢狀欄 1;books:格內巢狀欄 1
  [YEL] VCGC VIA_Central_Synonym_Regex_v0107.json · CRLF;表頭定案冊無此表;regex:格內巢狀欄 2;rulings:格內巢狀欄 1;synonyms_meta:數字存字串欄 1
  [YEL] VCGC VIA_DataFrameContract_SSOT_v0100.json · CRLF;表頭定案冊無此表
  [YEL] VCGC VIA_DataFrame_Lock_Ledger_v0100.jsonl · CRLF;表頭定案冊無此表;rows:格內巢狀欄 1
  [YEL] VCGC VIA_DeprecatedGateway_IgnoreManifest_v012.json · CRLF;表頭定案冊無此表;deprecated_files:非 snake_case 欄 3
  [YEL] VCGC VIA_EngineRegistry.20260626_174457.dup.json · CRLF;表頭定案冊無此表;rows:非 snake_case 欄 13
  [YEL] VCGC VIA_EngineRegistry.csv · BOM;表頭定案冊無此表
  [YEL] VCGC VIA_EngineRegistry.json · CRLF;表頭定案冊無此表;rows:非 snake_case 欄 13
  [YEL] VCGC VIA_EnvRegistry.json · CRLF;表頭定案冊無此表;items:非 snake_case 欄 17
  [YEL] VCGC VIA_Essentia_CardBook_CGC_v0100.json · CRLF;表頭定案冊無此表;cards:數字存字串欄 1;格內巢狀欄 6
  [YEL] VCGC VIA_Essentia_CardBook_VDF_v0100.json · CRLF;表頭定案冊無此表;cards:數字存字串欄 1;格內巢狀欄 6
  [YEL] VCGC VIA_Essentia_CardBook_VRN_v0100.json · CRLF;表頭定案冊無此表;cards:數字存字串欄 1;格內巢狀欄 6
  [YEL] VCGC VIA_Essentia_Product_SSOT_v0100.json · CRLF;表頭定案冊無此表
  [YEL] VCGC VIA_FinalParameters_CanonicalRegistry.csv · CRLF;表頭定案冊無此表;rows:數字存字串欄 4
  [YEL] VCGC VIA_FinalParameters_CanonicalRegistry.json · CRLF;表頭定案冊無此表;rows:數字存字串欄 1
  [YEL] VCGC VIA_LampLock_v0108.json · CRLF;表頭定案冊無此表;wkf:格內巢狀欄 3;wkf_open:格內巢狀欄 2
  [YEL] VCGC VIA_LibRegistry.json · CRLF;表頭定案冊無此表;items:非 snake_case 欄 17
  [YEL] VCGC VIA_MasterGovernance_SSOT_v0100.json · CRLF;表頭定案冊無此表;subsystems:格內巢狀欄 3
  [YEL] VCGC VIA_MasterGovernance_SSOT_v0100.local.json · CRLF;表頭定案冊無此表;subsystems:格內巢狀欄 3
  [YEL] VCGC VIA_MasterRegistry.json · CRLF;表頭定案冊無此表;items:非 snake_case 欄 17
  [YEL] VCGC VIA_NetGate_Wiring_Register_v0101.json · CRLF;表頭定案冊無此表
  [YEL] VCGC VIA_Numbering_SSOT_v0100.json · CRLF;表頭定案冊無此表;books:格內巢狀欄 3
  [YEL] VCGC VIA_Output_Header_SSOT_Candidates_v0100.json · CRLF;表頭定案冊無此表;tables:格內巢狀欄 3
  [YEL] VCGC VIA_Output_Header_SSOT_v0101.json · CRLF;表頭定案冊無此表;tables:格內巢狀欄 2
  [YEL] VCGC VIA_Policy_DBPanel_v0101.json · CRLF;表頭定案冊無此表
  [YEL] VCGC VIA_Policy_Laws_SSOT_v0106.json · CRLF;表頭定案冊無此表
  [YEL] VCGC VIA_ProductGate_v0100.json · CRLF;表頭定案冊無此表;projects:非 snake_case 欄 3
  [YEL] VCGC VIA_Registry_Architecture_SSOT_v0100.json · CRLF;表頭定案冊無此表;namespaces:數字存字串欄 1;entity_primary:格內巢狀欄 1
  [YEL] VCGC VIA_ReleaseRegistry.json · CRLF;表頭定案冊無此表;items:非 snake_case 欄 17
  [YEL] VCGC VIA_SSOT_ItemNumbers_v0100.json · CRLF;表頭定案冊無此表;items:混型欄 1
  [YEL] VCGC VIA_SSOT_Numbers_VRN_v0100.json · CRLF;表頭定案冊無此表
  [YEL] VCGC VIA_SSOT_PeriodRules_v0100.json · CRLF;表頭定案冊無此表;value_shapes:數字存字串欄 1;cadences:格內巢狀欄 1
  [YEL] VCGC VIA_SSOT_RegexDict_v0100.json · CRLF;表頭定案冊無此表;top_shared:格內巢狀欄 1
  [YEL] VCGC VIA_SSOT_SynonymUnion_v0107.json · CRLF;表頭定案冊無此表;deny_leak:無主鍵候選;rulings:格內巢狀欄 6;無主鍵候選
  [YEL] … 另 70 冊在卡
[計] mirror VCGC 冊鏡像 69 表 · 略過 102 · WRITTEN
NEXT: 紅 → 出新版冊轉 UTF-8/修 JSON;黃 → 看 Candidates 待審區,操作員+AI 裁表頭後併入 Output_Header_SSOT 讓 MDL249 鎖;VDF/VRN 冊由各自 manager 依 DataFrameContract 出新版
```

## 每冊
| 子系統 | 冊 | 形狀 | 表 | 編碼 | 表頭定案 | 燈 | 原因 |
|---|---|---|---|---|---|---|---|
| VCGC | GovernanceRegistry.json | NESTED | language_adapters(10×5) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VCGC | VIA_ActivationGateway_Manifest.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_ActivationGateway_v02_Hotfix_Manifest.json | NESTED | rows(9×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 1;非 snake_case 欄 12 |
| VCGC | VIA_ActivationGateway_v03_StableHotfix_Manifest.json | NESTED | rows(26×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 1;無主鍵候選;非 snake_case 欄 12 |
| VCGC | VIA_ActivationGateway_v04_InlineReady_Manifest.json | NESTED | rows(71×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 1;無主鍵候選;非 snake_case 欄 12 |
| VCGC | VIA_ActivationGateway_v05_ParamFirst_Manifest.json | NESTED | rows(71×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 1;無主鍵候選;非 snake_case 欄 12 |
| VCGC | VIA_Canon_Registry_v0100.json | NESTED | entries(35×10) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;entries:格內巢狀欄 4;無主鍵候選 |
| VCGC | VIA_Central_Params_SSOT_v0100.json | NESTED | locked_alignment(12×4), books(67×11) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;locked_alignment:格內巢狀欄 1;books:格內巢狀欄 1 |
| VCGC | VIA_Central_Synonym_Regex_v0107.json | NESTED | regex(137×17), rulings(10×10), synonyms_meta(75×6) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;regex:格內巢狀欄 2;rulings:格內巢狀欄 1;synonyms_meta:數字存字串欄 1 |
| VCGC | VIA_DataFrameContract_SSOT_v0100.json | NESTED | laws(11×2) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VCGC | VIA_DataFrame_Lock_Ledger_v0100.jsonl | JSONL | rows(2×11) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:格內巢狀欄 1 |
| VCGC | VIA_DeprecatedGateway_IgnoreManifest_v012.json | NESTED | deprecated_files(8×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;deprecated_files:非 snake_case 欄 3 |
| VCGC | VIA_EngineRegistry.20260626_174457.dup.json | TABLE | rows(120×13) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:非 snake_case 欄 13 |
| VCGC | VIA_EngineRegistry.csv | CSV | — | utf-8 BOM | 無 | YELLOW | BOM;表頭定案冊無此表 |
| VCGC | VIA_EngineRegistry.json | TABLE | rows(120×13) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:非 snake_case 欄 13 |
| VCGC | VIA_EntryLock_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_EnvRegistry.json | NESTED | items(5094×17) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;items:非 snake_case 欄 17 |
| VCGC | VIA_Essentia_CardBook_CGC_v0100.json | NESTED | cards(168×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;cards:數字存字串欄 1;格內巢狀欄 6 |
| VCGC | VIA_Essentia_CardBook_VDF_v0100.json | NESTED | cards(80×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;cards:數字存字串欄 1;格內巢狀欄 6 |
| VCGC | VIA_Essentia_CardBook_VRN_v0100.json | NESTED | cards(342×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;cards:數字存字串欄 1;格內巢狀欄 6 |
| VCGC | VIA_Essentia_Product_SSOT_v0100.json | NESTED | verbs(8×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VCGC | VIA_FinalParameters_CanonicalRegistry.csv | CSV | rows(34696×16) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 4 |
| VCGC | VIA_FinalParameters_CanonicalRegistry.json | NESTED | rows(34677×16) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 1 |
| VCGC | VIA_ForwardVintageLock_v0101.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_LampLock_v0108.json | NESTED | wkf(16×9), wkf_open(15×6) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;wkf:格內巢狀欄 3;wkf_open:格內巢狀欄 2 |
| VCGC | VIA_LibRegistry.json | NESTED | items(10595×17) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;items:非 snake_case 欄 17 |
| VCGC | VIA_MarketSyncLock_v0101.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_MasterGovernance_SSOT_v0100.json | NESTED | subsystems(3×7) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;subsystems:格內巢狀欄 3 |
| VCGC | VIA_MasterGovernance_SSOT_v0100.local.json | NESTED | subsystems(3×7) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;subsystems:格內巢狀欄 3 |
| VCGC | VIA_MasterRegistry.json | NESTED | items(29842×17) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;items:非 snake_case 欄 17 |
| VCGC | VIA_NetGate_Wiring_Register_v0101.json | NESTED | engines(94×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VCGC | VIA_Numbering_Ledger_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_Numbering_SSOT_v0100.json | NESTED | subsystems(14×3), kinds(26×3), books(26×9) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;books:格內巢狀欄 3 |
| VCGC | VIA_Output_Header_SSOT_Candidates_v0100.json | NESTED | tables(196×10) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;tables:格內巢狀欄 3 |
| VCGC | VIA_Output_Header_SSOT_v0101.json | NESTED | tables(14×8) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;tables:格內巢狀欄 2 |
| VCGC | VIA_PlotDataLaw_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_Policy_DBPanel_v0101.json | NESTED | ast_classes(18×6) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VCGC | VIA_Policy_DataSeat_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_Policy_FlowGate_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_Policy_Laws_SSOT_v0106.json | NESTED | lessons(362×6) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VCGC | VIA_Policy_PSCommandGate_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_Policy_TalibBan_v0101.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_Policy_TokenFirst_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_Policy_VRNTextScope_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_ProductGate_v0100.json | NESTED | gates(9×5), projects(4×7) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;projects:非 snake_case 欄 3 |
| VCGC | VIA_RegistryCore_v1.py.freeze.lock.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_Registry_Architecture_SSOT_v0100.json | NESTED | layers(7×5), namespaces(11×7), entity_primary(6×3), flow(8×3), risks(15×8) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;namespaces:數字存字串欄 1;entity_primary:格內巢狀欄 1 |
| VCGC | VIA_ReleaseRegistry.json | NESTED | items(18895×17) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;items:非 snake_case 欄 17 |
| VCGC | VIA_SSOT_ConsistencyChecker_Spec_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_SSOT_ItemNumbers_v0100.json | NESTED | items(58×10) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;items:混型欄 1 |
| VCGC | VIA_SSOT_Numbers_VRN_v0100.json | NESTED | entries(47×9) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VCGC | VIA_SSOT_PeriodRules_v0100.json | NESTED | ledger(6×4), value_shapes(9×5), cadences(2×6), cadence_candidates(2×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;value_shapes:數字存字串欄 1;cadences:格內巢狀欄 1 |
| VCGC | VIA_SSOT_RegexDict_v0100.json | NESTED | dropped_uncompilable(5×2), top_shared(25×3), synonyms(42×3), zone_stat(4×4) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;top_shared:格內巢狀欄 1 |
| VCGC | VIA_SSOT_SynonymUnion_v0107.json | NESTED | deny_leak(10×5), gate_bypass(54×5), rulings(26×18), unverified(1×4), key_alias(23×4) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;deny_leak:無主鍵候選;rulings:格內巢狀欄 6;無主鍵候選 |
| VCGC | VIA_SourceLaneLock_v0100.json | NESTED | rows(2×8) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 1 |
| VCGC | VIA_StatusLock_v0100.json | NESTED | locked(3×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;locked:格內巢狀欄 2 |
| VCGC | VIA_TWBackfillLock_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_ToolRegistry.json | NESTED | items(9713×17) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;items:非 snake_case 欄 17 |
| VCGC | VIA_UI_FormatLock_v0101.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_USMacroProbeLock_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VCGC | VIA_Workflow_Hub_SSOT_v0102.json | NESTED | sequence(4×2) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VCGC | VIA_Workflow_SSOT_v0100.json | NESTED | workflows(18×6) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;workflows:格內巢狀欄 1 |
| VCGC | VIA_Workflow_VAP_SSOT_v0100.json | NESTED | workflows(1×9) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;workflows:格內巢狀欄 4 |
| VCGC | VIA_Workflow_VCGC_SSOT_v0126.json | NESTED | workflows(21×9) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;workflows:格內巢狀欄 4 |
| VCGC | VIA_Workflow_VDF_SSOT_v0104.json | NESTED | workflows(14×9) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;workflows:格內巢狀欄 4 |
| VCGC | VIA_Workflow_VRN_SSOT_v0105.json | NESTED | workflows(9×9) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;workflows:格內巢狀欄 4 |
| VDF | VDF_MDL401_RegistrySchema_v1.json | NESTED | properties(2×8), definitions(4×6) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;properties:格內巢狀欄 3;非 snake_case 欄 2;definitions:格內巢狀欄 2;非 snake_case 欄 1 |
| VDF | VDF_MDL404_CoverageReport.json | MAP | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 MAP(純設定/巢狀,不當 DataFrame) |
| VDF | VIA_Extraction_Matrix_v8.csv | CSV | rows(77×10) | utf-8 BOM CRLF | 無 | YELLOW | BOM;CRLF;表頭定案冊無此表;rows:數字存字串欄 1;非 snake_case 欄 10 |
| VDF | VIA_VDF_Fetch_Contract.json | NESTED | domains(17×3), revisions(2×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;domains:格內巢狀欄 1 |
| VRN | VRN_BROKER_LIST_v04.json | NESTED | brokers(19×11), merge_log(1×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;brokers:格內巢狀欄 3 |
| VRN | VRN_OUTPUTS_SSOT_v0100.json | NESTED | def_output_bundles(8×5), def_validation_gates(7×4), def_canonical_ids(8×4), def_table_contracts(13×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;def_output_bundles:格內巢狀欄 1;def_canonical_ids:格內巢狀欄 2;def_table_contracts:格內巢狀欄 2 |
| VRN | VRN_Production_Manifest.json | NESTED | files(32×8) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VRN | VRN_REPORT_BASIC_INFO_SSOT_v0100.json | NESTED | def_validation_gates(10×4), def_historical_quality_evidence_not_revalidated_here(2×6) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VRN | VRN_REPORT_DATA_SSOT_INDEX_v0100.json | NESTED | def_datasets(2×7), def_artifact_manifest(2×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;def_datasets:格內巢狀欄 3 |
| VRN | VRN_REPORT_FINANCIAL_DATA_SSOT_v0100.json | NESTED | def_validation_gates(13×4), def_historical_quality_evidence_not_revalidated_here(2×10) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VRN | VRN_ResearchReport_Incremental_Manifest.schema.v0154.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_SSOT_Adopt_Ledger.jsonl | JSONL | rows(139×7) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:無主鍵候選 |
| VRN | VRN_SSOT_Index_v0100.json | NESTED | entries(47×17) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;entries:格內巢狀欄 1 |
| VRN | VRN_Audit_Evidence_v0100.json | NESTED | findings(8×5), verified_sources(16×6) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VRN | VRN_BrokerBackfillManifest_v029VRN1C41.json | CONFIG | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 CONFIG(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_ChainNodeLedger_v0100.json | NESTED | timeouts(2×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VRN | VRN_DocClass_SSOT_v0100.json | NESTED | rules(11×5), classes(5×7) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rules:格內巢狀欄 1 |
| VRN | VRN_Essentia_CardBook_VRN_v0100.json | NESTED | cards(342×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;cards:數字存字串欄 1;格內巢狀欄 6 |
| VRN | VRN_ExtractionLogic_SSOT_v0100.json | NESTED | ladder(3×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;ladder:格內巢狀欄 1 |
| VRN | VRN_FieldRules_SSOT_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_FieldSpec_SSOT_v0100.json | NESTED | fields(15×8) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VRN | VRN_FileRegistry_Stage_v029VRN1C.csv | CSV | rows(400×11) | utf-8 BOM CRLF | 無 | YELLOW | BOM;CRLF;表頭定案冊無此表;rows:數字存字串欄 5 |
| VRN | VRN_FinancialSSOT_Manifest_v0000.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_FinancialShown_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_Incremental_DB_Result_v0000.json | NESTED | files(60×7) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;files:數字存字串欄 1 |
| VRN | VRN_LayoutRestore_SSOT_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_LogicArchitecture_SSOT_v0100.json | NESTED | placed_by_batch662(15×7), off_book_pending(13×5), rulings_today(5×4), known_gaps(2×4), layers(6×5), rule_canons(10×8) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rulings_today:格內巢狀欄 1;layers:格內巢狀欄 1 |
| VRN | VRN_MDL024_VRN_v139O_AppendOnly_Bridge_Injector_Matrix__MODULE__v139O.json | NESTED | matrix(31×7), patched(24×10) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;matrix:數字存字串欄 1;非 snake_case 欄 7;patched:非 snake_case 欄 10 |
| VRN | VRN_MDL027_vrn_final_production_lock_registry_v061573__SUPPORT_RULE__v061573.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_MDL028_vrn_final_production_lock_registry_v061573__SUPPORT_RULE__v061573.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_MDL033_VRN_Hydra_Containment_Registry__SUPPORT_RULE__v0_0_v0000.json | NESTED | CanonicalValidation(5×11), ReclassifiedErrors(301×10), EvidenceOnlyDenylist(276×11) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;CanonicalValidation:非 snake_case 欄 11;ReclassifiedErrors:非 snake_case 欄 10;EvidenceOnlyDenylist:非 snake_case 欄 11 |
| VRN | VRN_MDL059_VRN_YFinance_Header_Canonical_Refresh_Manifest_v06147__DATA_SOURCE__v06147.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_MDL069_VRN_CANONICAL_ACTIVE_MANIFEST__MODULE__v0_0_v0000.json | NESTED | Evidence(6×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;Evidence:非 snake_case 欄 12 |
| VRN | VRN_MDL089_VRN_v141D8A2_SafeGetter_SourceManifestExtractor__MODULE__v141D8A2.json | NESTED | summary(11×9), previous_d8a_diagnosis(5×6), source_manifest_validated(64×11), text_anchor_evidence(64×11), basic_info_candidates(64×16), financial_data_text_candidates(634×12), issues(34×7), lineage(64×9), d9_gate(2×6) | utf-8 BOM CRLF | 無 | YELLOW | BOM;CRLF;表頭定案冊無此表;summary:數字存字串欄 2;非 snake_case 欄 9;previous_d8a_diagnosis:非 snake_case 欄 6;source_manifest_validated:數字存字串欄 1;非 snake_case 欄 11;text_anchor_evidence:數字存字串欄 2;非 snake_case 欄 11;basic_info_candidates:數字存字串欄 2;非 snake_case 欄 16;financial_data_text_candidates:數字存字串欄 3;無主鍵候選;非 snake_case 欄 12;issues:無主鍵候選;非 snake_case 欄 7;lineage:非 snake_case 欄 9;d9_gate:非 snake_case 欄 6 |
| VRN | VRN_MDL090_VRN_v141D8A3_SingleQuoted_SourceManifestExtractor__MODULE__v141D8A3.json | NESTED | summary(12×9), previous_d8a2_diagnosis(3×6), source_manifest_validated(64×11), text_anchor_evidence(64×11), basic_info_candidates(64×16), financial_data_text_candidates(634×12), issues(34×7), lineage(64×9), d9_gate(2×6) | utf-8 BOM CRLF | 無 | YELLOW | BOM;CRLF;表頭定案冊無此表;summary:數字存字串欄 2;非 snake_case 欄 9;previous_d8a2_diagnosis:非 snake_case 欄 6;source_manifest_validated:數字存字串欄 1;非 snake_case 欄 11;text_anchor_evidence:數字存字串欄 2;非 snake_case 欄 11;basic_info_candidates:數字存字串欄 2;非 snake_case 欄 16;financial_data_text_candidates:數字存字串欄 3;無主鍵候選;非 snake_case 欄 12;issues:無主鍵候選;非 snake_case 欄 7;lineage:非 snake_case 欄 9;d9_gate:非 snake_case 欄 6 |
| VRN | VRN_MDL105_VRN_DoNotRedo_DoneRegistry__SUPPORT_RULE__v0_0_v0000.json | NESTED | DoNotRedoRegistry(7×7), CurrentBaseEvidence(7×10), NextOrder(6×8) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;DoNotRedoRegistry:非 snake_case 欄 7;CurrentBaseEvidence:非 snake_case 欄 10;NextOrder:混型欄 1;非 snake_case 欄 8 |
| VRN | VRN_MDL117_VRN_Activation_RegistryOnly_Dry_v1_0_27__SUPPORT_RULE__v1_0_v0000.json | NESTED | rows(32×6) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 1;無主鍵候選;非 snake_case 欄 6 |
| VRN | VRN_MDL130_VRN_v140R_Release_Index_Pointer_MODULE_v140R.json | TABLE | rows(3×9) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:格內巢狀欄 2;非 snake_case 欄 9 |
| VRN | VRN_MDL133_VRN_v140J_Registry_Sidecar_Write_Gate__SUPPORT_RULE__v140J.json | NESTED | matrix(13×7), validation(9×4) | utf-8 BOM CRLF | 無 | YELLOW | BOM;CRLF;表頭定案冊無此表;matrix:非 snake_case 欄 7;validation:混型欄 2;非 snake_case 欄 4 |
| VRN | VRN_MDL134_VRN_v140I_SSOT_Registry_Pointer_Preview__SUPPORT_RULE__v140I.json | NESTED | matrix(12×7), supportive_ast_preview(3×7) | utf-8 BOM CRLF | 無 | YELLOW | BOM;CRLF;表頭定案冊無此表;matrix:數字存字串欄 1;非 snake_case 欄 7;supportive_ast_preview:非 snake_case 欄 7 |
| VRN | VRN_MDL203_VRN_MASTER_GOVERNANCE_REGISTRY_v0615703__GOVERNANCE__v0615703.json | NESTED | registry_rows(8×10), supportive_assets(6×8), governance_gates(7×4), future_flow(4×6), hard_rules(8×4) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;registry_rows:非 snake_case 欄 9;supportive_assets:非 snake_case 欄 2;governance_gates:非 snake_case 欄 4;future_flow:非 snake_case 欄 6;hard_rules:非 snake_case 欄 4 |
| VRN | VRN_MDL204_VRN_MASTER_GOVERNANCE_REGISTRY_v0615703__GOVERNANCE__v0615703.json | NESTED | registry_rows(8×10), supportive_assets(6×8), governance_gates(7×4), future_flow(4×6), hard_rules(8×4) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;registry_rows:非 snake_case 欄 9;supportive_assets:非 snake_case 欄 2;governance_gates:非 snake_case 欄 4;future_flow:非 snake_case 欄 6;hard_rules:非 snake_case 欄 4 |
| VRN | VRN_MDL205_VRN_NoSummarizer_CanonicalManifest_v02__MODULE__v02.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_MatrixApplicability_SSOT_v0100.json | NESTED | rules(3×9), pending_operator(2×7) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rules:格內巢狀欄 1 |
| VRN | VRN_ParquetUnifiedStageManifest_v029VRN1C3.json | CONFIG | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 CONFIG(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_PluginHub_SSOT_v0100.json | NESTED | stages(11×4), providers(19×9), ast_categories(11×2), plans(2×7) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;providers:格內巢狀欄 2;plans:格內巢狀欄 1 |
| VRN | VRN_Policy_VRNTextScope_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_ReportEntities_SSOT_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_ReportFieldRules_SSOT_v0101.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_ReportMeasure_v0101.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_Report_Parser_Integrated_SSOT.json | NESTED | support_modules(7×11), date_regex(4×10), report_date_regex(5×4), broker_aliases(171×5), financial_accounts(176×6), via_raw_regex(46×11), via_raw_lists(18×11), via_raw_synonyms(112×7) | utf-8 | 無 | YELLOW | 表頭定案冊無此表;support_modules:格內巢狀欄 2;date_regex:格內巢狀欄 3;broker_aliases:格內巢狀欄 2;無主鍵候選;financial_accounts:格內巢狀欄 1;無主鍵候選;via_raw_regex:格內巢狀欄 3;via_raw_lists:格內巢狀欄 1;via_raw_synonyms:格內巢狀欄 1 |
| VRN | VRN_ResearchReport_SSOT.active.json | NESTED | — | utf-8 | 無 | GRAY | 非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_ResearchReport_SSOT.jsonl | JSONL | rows(60×48) | utf-8 | 無 | YELLOW | 表頭定案冊無此表;rows:數字存字串欄 15 |
| VRN | VRN_ResearchReport_SSOT.schema.v1.json | NESTED | fields(46×5) | utf-8 | 無 | YELLOW | 表頭定案冊無此表 |
| VRN | VRN_S05_FieldRegistry_v0102.json | NESTED | valuation_methods_v0595(22×7), basicinfo_fields(30×12), financialdata_fields(76×10), all_regex(40×5), email_domain_to_broker(42×4) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;valuation_methods_v0595:格內巢狀欄 2;basicinfo_fields:格內巢狀欄 2;financialdata_fields:格內巢狀欄 3;all_regex:格內巢狀欄 2 |
| VRN | VRN_SisterLineage_Sync_v0100.json | NESTED | files(12×4) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VRN | VRN_SourceProvenance_SSOT_v0100.json | NESTED | sources(4×3), escalation(5×2) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;escalation:無主鍵候選 |
| VRN | VRN_StageAlias_Map_v0100.json | NESTED | map(9×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VRN | VRN_TabFields_v0100.json | NESTED | tabs(3×3) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;tabs:格內巢狀欄 2 |
| VRN | VRN_ValuationMethod_SSOT_v0100.json | NESTED | methods(16×16) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;methods:格內巢狀欄 8 |
| VRN | VRN_Verified_Module_Registry_v0000.csv | CSV | rows(300×12) | utf-8 BOM CRLF | 無 | YELLOW | BOM;CRLF;表頭定案冊無此表;rows:數字存字串欄 2;非 snake_case 欄 12 |
| VRN | VRN_Verified_Module_Registry_v0000.json | TABLE | rows(300×12) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:非 snake_case 欄 12 |
| VRN | VRN_Workflow_VRN_SSOT_v0105.json | NESTED | workflows(9×9) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;workflows:格內巢狀欄 4 |
| VRN | VRN_ResearchReport_SSOT.record.schema.v2.json | NESTED | allOf(1×3), properties(52×8) | utf-8 | 無 | YELLOW | 表頭定案冊無此表;allOf:格內巢狀欄 3;無主鍵候選;properties:混型欄 1;格內巢狀欄 3;非 snake_case 欄 3 |
| VRN | VRN_ResearchReport_SSOT.schema.v2.full.json | NESTED | conditional_rules_materialized(1×3), fields(46×5) | utf-8 | 無 | YELLOW | 表頭定案冊無此表;conditional_rules_materialized:格內巢狀欄 3;無主鍵候選 |
| VRN | VRN_ResearchReport_SSOT.v2.jsonl | JSONL | rows(64×52) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 16;格內巢狀欄 2 |
| VRN | VRN_ResearchReport_SSOT.v2.records60.pre_promote.f124bc875468191e.jsonl | JSONL | rows(60×52) | utf-8 | 無 | YELLOW | 表頭定案冊無此表;rows:數字存字串欄 15;格內巢狀欄 2 |
| VRN | VRN_ResearchReport_SSOT.v2.records64.v0155.2f771c00c6dd8d6e.jsonl | JSONL | rows(64×52) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;rows:數字存字串欄 16;格內巢狀欄 2 |
| VRN | SYNONYM_LIBRARY_v3.json | NESTED | scopes(4×381) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;scopes:格內巢狀欄 380;非 snake_case 欄 295 |
| VRN | SYNONYM_LIBRARY_v4.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_AnnualExtract_SSOT_v0100.json | NESTED | items(79×5) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;items:格內巢狀欄 2 |
| VRN | VRN_Broker_Dict_v0100.json | NESTED | brokers_extended(34×6), brokers(35×5) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;brokers_extended:格內巢狀欄 1;brokers:格內巢狀欄 1 |
| VRN | VRN_Canonical_Trilingual_Fill_v0100.json | NESTED | fills(195×4) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表 |
| VRN | VRN_Contact_Regex_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_Digest_Params_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_FinData_Synonym_v0100.json | NESTED | metrics(195×22) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;metrics:格內巢狀欄 10 |
| VRN | VRN_FinStatement_Synonym_v0100.json | NESTED | statements(7×5) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;statements:格內巢狀欄 2 |
| VRN | VRN_Lexicon_Fill_Template_v0100.json | NESTED | tree(8×4) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;tree:格內巢狀欄 1 |
| VRN | VRN_Lexicon_v0100.json | NESTED | history(3×7), tree(8×4), entries(162×10) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;history:格內巢狀欄 1;無主鍵候選;tree:格內巢狀欄 1;entries:格內巢狀欄 2 |
| VRN | VRN_Method_SSOT_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_NumberFormat_Regex_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_Rating_Dict_v0100.json | NESTED | levels(4×7) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;levels:格內巢狀欄 3 |
| VRN | VRN_TickerDate_Regex_v0100.json | NESTED | — | utf-8 CRLF | 無 | GRAY | CRLF;非表形狀 NESTED(純設定/巢狀,不當 DataFrame) |
| VRN | VRN_KeywordSSOT_v0100.json | NESTED | ingest_log(11×4), keywords(611×10) | utf-8 CRLF | 無 | YELLOW | CRLF;表頭定案冊無此表;keywords:格內巢狀欄 3 |
