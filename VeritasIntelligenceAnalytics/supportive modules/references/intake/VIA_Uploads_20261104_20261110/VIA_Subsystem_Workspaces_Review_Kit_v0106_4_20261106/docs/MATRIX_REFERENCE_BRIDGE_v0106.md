# VIA Matrix Reference Bridge v0106

> **文件狀態：設計／唯讀分析；本次唯一新增檔案。**
>
> 本橋接不是 AllInOne 啟動紀錄、不是五引擎合併器，也不是 VCGC 註冊或自動修復器。它只定義一個可驗證、可追溯的**證據／管理頁 additive bridge**，把不同來源的來源雜湊、測試 scope、wrapper 狀態與 SSOT ID candidate 放在同一個報告 envelope；不改 runtime、DB、既有 audit、既有腳本／設定／舊 artifact。Native VCGC `EnvManager`／`InstallGate` 保持原樣。

## 1. 依循規範與本輪結論

本規格先依循：

- `/home/ubuntu/skills/via-ucc-triengine-workbench/SKILL.md`：local-only、schema-stable、source-bound、E1/E2/E3 交接與 append-only evidence；不把 UI bridge 當成引擎替換。
- `/home/ubuntu/skills/vrn-panorama-fixer/SKILL.md`：A（analysis）→ B（safe fix）→ C（verify）三軌；本文件只定義 A／受授權的 B 邊界／C 的證據要求，不替代正在進行的各系統獨立 audit。

**結論：** AllInOne 的 `ticker_id`／`amount`／`node_target` 是一筆業務輸入 payload 的欄位；v0105 governance inventory 的 row 是靜態治理觀測（file、I/O、command、environment、conflict、policy、test、requirement）。兩者 root、主鍵、狀態語意、證據層級均不同，不能以欄名或字串相似度直接 join。

## 2. Pinned source contract

以下雜湊是本次 sandbox 唯讀檢視時觀察到的 contract pin。任何來源缺失、版本或 SHA-256 不符時，bridge 必須 `BLOCKED_SOURCE_PIN_MISMATCH`，不得以「最新」或檔名推測替代。

| 來源 | 版本／宣告 scope | SHA-256 | bridge 用途 |
|---|---|---|---|
| `/home/ubuntu/upload/VIA_MatrixGovernance_AllInOne_v0100.py` | v0100；local reference engine；source/static contract | `bb8d5911a0e15765b9a4e0ad9d01a6104a78a044878db71b509b326f1f80b7b0` | 只引用輸入正規化、五階段報告欄位、manifest／checkpoint 語意；不在本 bridge 執行 |
| `/home/ubuntu/upload/VIA_MatrixGovernance_README_v0100.md` | v0100；輸入／限制／Go-Live policy | `f1d25131e9b11718e1a453f054c272baf27e37c9cb71894a2089b97e6e2b6338` | 以 lines 34–55、72–106 作為人可讀 contract |
| `/home/ubuntu/upload/VIA_MatrixGovernance_QA_v0100.html` | v0100；交付 QA／63 lifecycle／正式門檻 | `5d6ff4c59ca2dea122f86839e396d6abca22cfdb9ce8c63c126faf8ba7e7ac8b` | 只作 evidence reference；fixture PASS 不升級成 native certification |
| `/home/ubuntu/viaatlas/data/governance_inventory_v0105.json` | v0105；`29_MANIFEST_ATTACHMENTS_PLUS_PASTED_CONTENT_13_STATIC_ONLY` | `43c74dbe2b35862d06d507ef27c16cd15502686abeb1bb101362a15632a74754` | 固定 inventory；8 個 matrix、159 files／30 observed attachments；只讀 query |
| `/home/ubuntu/viaatlas/data/governance_evidence_v0105.json` | v0105；source observations + bounded local receipts | `b3d6c2aacbecbf60d94d2b740f817ce6087e079a80155bf89d7b4f3c20c5ff65` | 既有系統 gate、local receipt、NOT_EXECUTED／formal registration 狀態 |
| `/home/ubuntu/viaatlas/scripts/via_governance_mcp_v0105.py` | v0105；stdio candidate、非 connector | `901b91eb4add9db2c19f5a62e6ea291caa6a681294148fc6ca7ebc14a349225a` | 只沿用固定 inventory SHA check、bounded read-only query、3 tools 的限制 |

目前 AllInOne 的 `POLICY.ssot_id` 與 `NETWORK_REGISTRY.ssot_id` 均為 `null`；bridge 的 `ssot_id_candidate` 初始也必須為 `null`，不得自行發號。上述 hash 是完整 source reference，不等於來源已被正式註冊。

## 3. 精確 scope map：兩種 row 不可混用

### 3.1 AllInOne 業務輸入 row（`--run` 的唯一業務形狀）

靜態來源：AllInOne lines 34–46、170–211，README lines 34–55；CLI lines 965–985。

- root 必須是**非空 JSON array**，最多 100,000 rows、12 MiB。
- 每個 row 必須是 object；`ticker_id`、`amount` 必填，`node_target`、`asset_type` 可選。
- 欄位值必須是 string；`amount` 以 Decimal 正規化至兩位小數；`node_target` 預設 `NODE_DEFAULT`；`asset_type` 預設 `stock`。
- aliases 僅在本 contract 內正規化：`code/symbol/stock_id → ticker_id`、`price/val/fee → amount`、`endpoint/target → node_target`。
- unknown field、alias collision、缺欄位、duplicate JSON key、NaN／Infinity、boolean／float 或 regex 不符均 fail-closed；正規化後相同 row 去重。
- `node_target` 是 local fixture payload／測試欄位，不是把資料送至名稱相同的外部 node。

例（**可作 AllInOne 業務 input；不是 inventory row**）：

```json
[
  {"ticker_id":"2330","amount":"100.00","node_target":"NODE_TWSE_01","asset_type":"stock"}
]
```

### 3.2 Governance inventory row（`governance_inventory_v0105.json`）

- root 是 object，含 `version`、`generated_at`、`scope`、`counts`、`matrices`。
- `matrices` 的固定 categories 是 `files`、`io`、`commands`、`environment`、`conflicts`、`policy`、`tests`、`requirements`。
- row 的治理主鍵／語意是 `id`、`status`、`ssot_name`、`system`、`source`、`source_sha256`、`version`、`kind`、`scope`、`evidence` 及 category-specific fields；不是交易 payload。
- inventory 的 `POLICY-*` 列可在 `value` 中記錄文字 `ticker_id`、`amount`、`node_target`（例如 `required`／`regex`／`synonyms`／`allowed`），但那是「政策被靜態觀測」；不表示 inventory 收到任何 ticker、金額或節點目標。
- 代表性列：`POLICY-5cb26f8a5e0efe9d`（required）、`POLICY-260320f584f2ed54`（synonyms）、`POLICY-78e8325e4f4d1345`（allowed）均為 `STATIC_PARSE_ONLY`，不可當作業務 row。

### 3.3 直接回答「`--run` 能否接受全部 subsystem matrix rows」

**不能，且本輪不執行。** 依靜態 CLI／parser 契約：

1. 把 inventory object（`{"matrices": ...}`）傳給 `--run --input`，在 list boundary 即不符。
2. 把某一個 inventory row array 傳入，row 會因缺少 `ticker_id`／`amount` 或含有 `id/status/system/source` 等 unknown fields 而拒絕。
3. 即使人工為 inventory row 加上兩個業務欄位，也只是新造的 AllInOne input，不能因此取得原治理 row 的身份、證據或系統 mapping。
4. 因此 bridge 必須把「業務 input validation」和「inventory evidence query」分成兩個 source-bound stream；不得以全 matrix rows 餵入 `--run`，不得推定 all-systems remediation。

## 4. Additive bridge 的 normative envelope

下列是共同 evidence／management page 的最小 schema。它是報告 envelope，不是 runtime／DB schema；raw business rows 預設以外部 immutable artifact reference 保存，不嵌入報告。

```json
{
  "bridge_schema": "VIA-MATRIX-REFERENCE-BRIDGE",
  "bridge_version": "v0106",
  "artifact_id": "MATRIX-REFERENCE-BRIDGE-v0106.<seq>-<content_root_16>",
  "report_id": "<owner-issued-or-local-run-id>",
  "mode": "analyze",
  "wrapper_status": "BLOCKED_OWNER_SCHEMA_MISSING",
  "source_refs": [],
  "test_scope": {
    "level": "STATIC_SOURCE",
    "systems": ["VIA_MATRIX_GOVERNANCE"],
    "receipt_ids": [],
    "executed": false
  },
  "ssot": {
    "ssot_id_candidate": null,
    "authority": null,
    "owner_approval_ref": null,
    "formal_registration": false
  },
  "business_input": {
    "contract_ref": "ALLINONE_POLICY_v0100",
    "input_artifact_ref": null,
    "input_sha256": null,
    "row_count": 0,
    "accepted_count": 0,
    "rejected_count": 0,
    "rows_embedded": false
  },
  "governance_refs": [],
  "subsystem_reports": [],
  "evidence": [],
  "actions": {
    "performed": false,
    "external_calls": 0,
    "writes": [],
    "runtime_or_db_merge": false,
    "envmanager_installgate_touched": false,
    "auto_remediation": false
  },
  "limitations": []
}
```

### 4.1 欄位規則

| 欄位 | 規則 |
|---|---|
| `source_refs[]` | 每項必含 `path`、`version`、`sha256`、`scope`、`role`；只接受已 pin 的 source／receipt。 |
| `test_scope.level` | 僅可為 `STATIC_SOURCE`、`LOCAL_FIXTURE`、`NATIVE_ENGINE`、`LIVE_INTEGRATION`、`FORMAL_REGISTRATION`；scope 不可由 PASS 字串自動升級。 |
| `wrapper_status` | `READY`、`ANALYZED`、`EXECUTED_LOCAL_FIXTURE`、`VERIFIED`、`BLOCKED_*`、`NOT_IMPLEMENTED`；與單一 subsystem 的 `evidence.status` 分離。 |
| `ssot.*` | candidate 可為 null；只有 owner 提供 authority／approval／registry receipt 後才可變更；bridge 不 mint SSOT。 |
| `business_input` | 僅記錄 contract、輸入 artifact hash、計數與拒絕摘要；不得把 inventory rows 或未授權原始業務資料內嵌。 |
| `governance_refs[]` | 只能列明確 inventory `id`，並附 `matrix`、`relation`、`source_sha256`、`evidence_scope`；不能依 `ticker_id`／`system` 字串猜 join。 |
| `evidence[]` | 每項必含 `evidence_id`、`status`、`scope`、`source_sha256`、`receipt_ref`、`observed_at`；`formal_registration` 預設 false。 |
| `actions` | 目前全部為 false／空陣列；任何 write、install、external call、DB/runtime merge 都須另有 owner authorization，否則直接 BLOCKED。 |

### 4.2 明確 link 語意

唯一允許的跨 stream link 是 owner 明確提供的關係，例如 `describes_input_policy`、`receipt_for`、`source_of`、`supersedes`。`ticker_id → inventory.id`、`amount → status`、`node_target → system` 都不是預設關係。沒有 owner mapping 時 `governance_refs=[]`，狀態為 `UNMAPPED_OWNER_CONTRACT`，不是「無資料即通過」。

## 5. 缺失的正式 owner adapter schema inputs

本文件提供格式，但不能替 owner 猜出正式 adapter contract。owner 必須以一份獨立、hash-pinned 的 `owner_adapter_contract` 提供下列欄位；任一必要項缺失，safeexecute／verify 均保持 BLOCKED：

```json
{
  "adapter_schema_version": "<owner-issued>",
  "owner_system_id": "<exact registry name>",
  "owner_subsystem_id": "<exact subsystem name>",
  "owner_contract_sha256": "<lowercase sha256>",
  "source_ref": {"path":"<immutable source>","version":"<version>","sha256":"<sha256>"},
  "input_contract": {
    "root_type": "array|object|stream",
    "required_fields": [],
    "optional_fields": [],
    "field_types": {},
    "alias_policy": "<explicit or none>",
    "bounds_units_precision": {},
    "unknown_duplicate_null_policy": "<explicit>",
    "dedup_key": "<explicit or none>"
  },
  "row_identity": {
    "stable_key": "<not inferred from ticker_id>",
    "canonicalization": "<versioned rule>",
    "join_authority": "<owner registry/ref>"
  },
  "mapping": {
    "business_to_governance": [],
    "allowed_relations": [],
    "unmapped_policy": "BLOCK"
  },
  "evidence_contract": {
    "receipt_fields": [],
    "source_locator": "<path/json-pointer/line-range>",
    "test_scope_enum": [],
    "status_enum": []
  },
  "execution_authorization": {
    "mode": "analyze|safeexecute|verify",
    "external_calls": false,
    "writes": [],
    "install_or_env_change": false,
    "runtime_db_merge": false
  },
  "ssot_registration": {
    "ssot_id_candidate": null,
    "authority": "<owner>",
    "approval_ref": null,
    "formal_registration": false
  },
  "artifact_policy": {
    "immutable_root": "<owner-approved path/store>",
    "retention": "<owner rule>",
    "signing_or_attestation": "<owner rule>"
  }
}
```

Owner 目前尚未提供：正式 subsystem registry ID、業務 row stable key／join authority、`amount` 的幣別／單位／方向／precision、`node_target` 的 target registry 與副作用、正式 evidence receipt 欄位、SSOT approval／registration ref、不可變 artifact store／retention／signing policy。故目前只能輸出候選 envelope，不能宣稱正式 adapter ready。

## 6. 證據／管理頁整合內容

可整合的是一個共用的 evidence view，不是把所有系統的執行面合成單一 runtime：

1. **Source pins**：來源檔、版本、SHA-256、inspection mode、source scope。
2. **Wrapper status**：`ANALYZED`／`BLOCKED`／`EXECUTED_LOCAL_FIXTURE`／`VERIFIED`，與每個 subsystem 的 native status 分欄。
3. **Scope matrix**：`STATIC_SOURCE`、`LOCAL_FIXTURE`、`NATIVE_ENGINE`、`LIVE_INTEGRATION`、`FORMAL_REGISTRATION`；顯示已做、未做、阻塞原因。
4. **Input contract card**：AllInOne 的 `ticker_id`／`amount`／`node_target` 規則、alias／Decimal／dedup 結果；不顯示為 inventory row。
5. **Governance references**：explicit inventory IDs、matrix category、relation、evidence scope；沒有 owner mapping 就顯示 `UNMAPPED`。
6. **SSOT card**：`ssot_id_candidate`、authority、approval ref、`formal_registration`；現狀是 candidate null／not registered。
7. **Receipt panel**：local fixture、MCP stdio candidate、GitHub metadata read 等各自列 receipt 與限制；不能把 wrapper PASS 合併成「五引擎 PASS」。
8. **Action audit**：`external_calls`、writes、EnvManager／InstallGate touched、runtime/DB merge、auto remediation 均應可見且目前為 false／空。

可重用的 AllInOne feature 是 strict input boundary、Decimal／alias conflict、五階段 matrix／trace 欄位、audit event、checkpoint／manifest 的證據語意；可重用的 MCP feature 是固定 inventory path + caller SHA check、max 50 bounded query、portable relative path 與 `LOCAL_CANDIDATE_EVIDENCE_NOT_LIVE`。這些 feature 僅作 adapter／報告層重用，不把 unrelated records 餵回 AllInOne，也不改 native VCGC／VDF／VRN／VQG／VAP 的 lifecycle。

## 7. 三階段 gate

| stage | 允許行為 | 必須產出 | 本輪狀態 |
|---|---|---|---|
| **analyze** | 讀取並驗證 pinned source／inventory／evidence；strict JSON／schema／hash／scope 分類；建立 unmapped queue。禁止 import／execute、network、install、DB write。 | `ANALYZED` 或 `BLOCKED_*` report；source index；不變更既有檔案。 | 可完成靜態 scope map；owner adapter 未提供。 |
| **safeexecute** | 只有 owner contract、receipt schema、授權與 immutable output root 齊備後，才可做 local adapter／fixture。可回放已 pin 的 reference receipt；不可啟動 native peer、不可碰 EnvManager／InstallGate。 | 每個 subsystem 獨立 receipt + bridge report；`external_calls=0`、writes 明列。 | **未執行**；不能用本輪 63/63 或 MCP protocol PASS 代替。 |
| **verify** | 重算 source／input／artifact hashes；驗證 receipt scope、manifest chain、explicit mapping、status monotonicity、未混入 unrelated rows；確認 formal registration 仍由 owner 決定。 | `VERIFIED` 或 `REVIEW_REQUIRED`；hash mismatch／scope mismatch 一律 BLOCKED。 | **未完成**；無 owner contract／SSOT approval／Tony-NB native receipt。 |

## 8. 不可實作／明確不在 v0106

- 不把 `governance_inventory_v0105.json` 的全部 matrix rows 送給 AllInOne `--run`。
- 不將不同系統的 runtime、DB、帳戶、registry、audit log 合併成一個執行引擎；本 bridge 只有共同 evidence envelope。
- 不安裝、升級、替換或修復任何套件／原始碼／設定；不觸碰 native VCGC `EnvManager`／`InstallGate`。
- 不建立真正 VCGC connector、MCP registration、SSOT number、OAuth／HTTP provider、Tony-NB workspace 或 native VDF／VRN／VQG／VAP execution。
- 不依 `ticker_id`、`amount`、`node_target` 或 system name 做猜測式 cross-system join、lookup、dispatch 或外部傳送。
- 不做 all-systems auto-remediation、批次改檔、刪除舊 artifact、DB migration、rollback／deployment、Git push。
- 不把 AllInOne 63/63 local scratch fixture、QA 63/63、MCP stdio 3-tool／31-case local protocol 或 GitHub metadata read 3/3 宣稱為五引擎 certification、production approval、capacity proof 或 formal registration。
- 不重做／取代各 subsystem 正在進行的獨立 audit；bridge 只引用其已封存 receipt，且維持各自 status／scope。

## 9. 本輪已知 receipts 與限制

- AllInOne current scratch receipt：`63/63` 是 source-bound local fixture／五階段 reference lifecycle；evidence `OBS-0189` 明載 `formal_registration=false`、非五 native engines、非 production。
- MCP current local candidate：3 tools（`via_status`、`via_inventory_query`、`via_token_prepare`）；evidence `OBS-0192` 的 `31/31` 是 local stdio protocol suite，無 native VCGC；adapter 自報 `CANDIDATE_NOT_REGISTERED`、無 network/provider/repository writes。
- Parent round 的 GitHub metadata read `3/3` 只屬 metadata read receipt，不是 engine／SSOT／connector receipt。
- `OBS-0185`：Tony-NB workspace unavailable；`OBS-0186`：沒有可核實 VCGC connector/server。故 peer runtime execution 必須維持 `NOT_RUN`。
- inventory 的 GREEN 僅表示 bounded static intake；evidence 的 YELLOW／RED／GREEN 必須連同 `scope` 閱讀。任何 fixture PASS 都不能覆蓋正式 gate 的 `NOT_EXECUTED`。

## 10. Immutable versioned artifact mechanism（規格，不在本輪建立）

建議由 owner 提供可 append-only 的 artifact root，例如：

```text
<immutable-root>/matrix_reference_bridge/v0106/
  <artifact_id>/
    manifest.json
    bridge_report.json
    source_index.json
    receipts/
      <receipt_id>.json
```

規則如下：

1. `artifact_version` 由 owner 的單調序號分配，例如 `v0106.<seq>`；不得重用既有版本。`artifact_id = MATRIX-REFERENCE-BRIDGE-v0106.<seq>-<content_root_sha256 前 16 碼>`。
2. `source_index.json` 固定每個 source／receipt 的相對路徑、bytes、version、scope、SHA-256；絕不只存檔名。
3. `content_root_sha256` 由排序後的 `relative_path + NUL + file_sha256 + NUL + bytes` canonical entries 計算；`manifest.json` 再記錄 `artifact_id`、`created_at_utc`、`previous_manifest_sha256`、`content_root_sha256`、`sealed=true`。
4. 先寫同目錄暫存檔、flush／fsync、atomic rename；seal 後禁止覆寫或刪除。修正只能建立新 `artifact_version`，以 `supersedes` 指向前一版；既有 manifest／receipt 保留。
5. SHA-256 提供完整性，不等於 owner 身份／簽章／正式註冊。若需要 authenticity，owner 必須另提供 signing／attestation contract；bridge 不自行創造信任根。
6. AllInOne 自己的 `manifest.json`、checkpoint、report 與本 bridge manifest 必須分開命名與 hash；不能把 reference engine 的輸出誤當成五引擎或 owner registry artifact。

本次沒有建立上述 artifact root、沒有寫入 report／receipt、沒有執行 `--run` 或任何 subsystem operation；本文件只固定下一步 adapter 與 evidence page 的界面、限制和阻擋條件。
