---
title: "VOFIE_Sample_Input"
engine: Veritas OmniFormat Intelligence Engine
engine_version: 1.4.0
run_id: RUN-F8DCFFC2365B717D
created_at: 2026-08-30T15:12:50+00:00
quality_gate: PASS
source_policy: READ_ONLY_NEW_ARTIFACTS_ONLY
---

# VOFIE_Sample_Input

> 由 **Veritas 全格式智慧重構與模板生成引擎（VOFIE）** 產生。原檔未改寫；重複與雜訊採標記／隔離，並保留在 IR。

## 格式與治理摘要

| 項目 | 結果 |
|---|---|
| 來源檔 | 1 |
| 主題區塊 | 5 |
| 程式元件 | 2 |
| 隔離片段 | 0 |
| 重複主題 | 0 |
| 品質 Gate | PASS |
| 來源 script | 不執行 |
| AI 改寫 | 僅候選，禁止直接套用 |

## 來源登記

| Source ID | 檔名 | 類型 | 編碼 | Bytes | BLAKE2s |
|---|---|---|---|---:|---|
| SRC-29E8C61C0DAF607B | VOFIE_Sample_Input.md | markdown | utf-8-sig | 724 | `d5e4960d8292a36314dd7bfc61f814e267bfe53e6cb21cf8aab8215273dd1be2` |

## ST 能力定位

| ST | Action | 基準定位 | 彈性 | 測試 | 說明備註 |
|---|---|---|---|---|---|
| ST-FMT-001 | `detect_and_read` | INPUT_CORE | FORMAT_ADAPTER | CRITICAL | 來源唯讀與雜湊前後一致。 |
| ST-FMT-002 | `topic_segment` | SEMANTIC_CORE | ANCHOR_ADAPTER | CRITICAL | 主題含來源行號與雜湊。 |
| ST-FMT-003 | `code_component_ir` | POLYGLOT_CORE | AST_ADAPTER | CRITICAL | 跨語言元件寫入 Markdown。 |
| ST-FMT-004 | `markdown_emit` | CANONICAL_OUTPUT | TEMPLATE_ADAPTER | CRITICAL | 所有格式共用 Markdown／IR 中介層。 |
| ST-FMT-005 | `office_emit` | DOCUMENT_ADAPTER | DOCX_PPTX_XLSX_ADAPTER | CRITICAL | 格式特性不同但來源追溯欄位不變。 |
| ST-FMT-006 | `web_template_emit` | UI_OUTPUT | HTML_CSS_JS_TOKEN_ADAPTER | CRITICAL | 三檔分離、無 CDN、無來源 script 執行。 |
| ST-FMT-007 | `audit_chain` | GOVERNANCE | APPEND_ONLY | CRITICAL | 每次輸出以 hash chain 記錄。 |
| ST-FMT-008 | `vsis_bridge` | VIA_INTEGRATION | OPTIONAL_OVERLAY | STANDARD | 沿用 VSIS 1.2 能力，缺少時本地降級。 |
| ST-FMT-009 | `text_merge` | CONSOLIDATION | CATEGORY_VIEW_ADAPTER | CRITICAL | 文字依主題分類合併成視圖，原區塊仍完整保留。 |
| ST-FMT-010 | `code_merge` | POLYGLOT_CONSOLIDATION | LANGUAGE_SYMBOL_ADAPTER | CRITICAL | 跨語言元件依語言／符號整合，API 簽章不變。 |
| ST-FMT-011 | `restructure` | STRUCTURAL_CANDIDATE | ORDER_ADAPTER | CRITICAL | 只重排輸出視圖，保留來源順序與行號。 |
| ST-FMT-012 | `deduplicate` | ADD_ONLY_DEDUP | CANONICAL_RULE_ADAPTER | CRITICAL | 標記 canonical／duplicate，不刪除任何內容。 |
| ST-FMT-013 | `optimize` | EQUIVALENCE_GATE | CANDIDATE_ONLY | CRITICAL | 優化只形成候選視圖，不直接改寫來源或 API。 |
| ST-FMT-014 | `simple_five_outputs` | USER_PROFILE | FIXED_PRIMARY_CONTRACT | CRITICAL | 簡易模式固定 MD／HTML／Component JSON／Word／CSV 五個主要檔。 |
| ST-FMT-015 | `engine_system_roles` | ROLE_BOUNDARY | SYSTEM_SIDECAR_ADAPTER | CRITICAL | ENGINE 只輸出五檔；SYSTEM 另在 _system 保留治理資料。 |
| ST-FMT-016 | `failure_recovery` | RESILIENCE_GATE | HANDLER_REGISTRY | CRITICAL | 八個環節各 Top 20 failure，且每項有多個已實作復原處理器。 |
| ST-FMT-017 | `window_drag_drop` | WINDOW_IO | DND_OR_FILE_DIALOG | STANDARD | Windows 視窗可選檔或拖放，最多五檔，拖放模組缺少時降級。 |
| ST-UI-001 | `ui_spec_extract` | UI_CORE | DOM_ADAPTER | CRITICAL | HTML 與 Markdown 雙軌保留。 |
| ST-UI-002 | `state_machine` | UI_LOGIC | GENERATED_SPEC | STANDARD | 事件與狀態分離。 |
| ST-UI-003 | `interaction_graph` | UI_LOGIC | GENERATED_SPEC | STANDARD | 元件、事件、目標可追溯。 |
| ST-UI-004 | `test_cases` | UI_QA | RULE_EXTENSIBLE | CRITICAL | 每個互動元件至少一個測試。 |
| ST-UI-005 | `usability` | UI_QA | RULE_EXTENSIBLE | STANDARD | 標籤、錯誤回饋與鍵盤路徑。 |
| ST-UI-006 | `accessibility` | UI_QA | WCAG_RULE_ADAPTER | CRITICAL | 語意元素、ARIA、對比與焦點。 |
| ST-UI-007 | `security` | UI_GATE | FAIL_CLOSED | CRITICAL | 不執行來源 script，不信任外部資源。 |
| ST-UI-008 | `layout_optimize` | UI_ENHANCEMENT | TOKEN_DRIVEN | STANDARD | PC／Mobile 響應式。 |
| ST-UI-009 | `component_refactor` | UI_ENHANCEMENT | CANDIDATE_ONLY | CRITICAL | 不直接覆寫來源 UI。 |
| ST-UI-010 | `performance` | UI_ENHANCEMENT | BUDGET_ADAPTER | STANDARD | 離線與資源預算。 |
| ST-UI-011 | `responsive` | UI_ENHANCEMENT | CSS_ADAPTER | CRITICAL | 單欄與多欄斷點。 |
| ST-UI-012 | `dark_mode` | UI_OPTIONAL | TOKEN_ADAPTER | SIMPLE | 預設淺色，支援系統深色。 |
| ST-UI-013 | `telemetry` | UI_OPS | OPT_IN | CRITICAL | 本地、匿名、預設關閉。 |

## 合併／重組／去重／優化視圖

**執行角色**：`SYSTEM`
**動作順序**：`text_merge`, `code_merge`, `restructure`, `deduplicate`, `optimize`
**來源主題／視圖主題**：5 / 5
**保留政策**：來源、重複項、行號與雜湊全部保留；優化只產生候選視圖。

| Action | Status | Affected | Source mutated | Policy |
|---|---|---:|---|---|
| `text_merge` | PASS | 4 | False | ADD_ONLY_VIEW |
| `code_merge` | PASS | 2 | False | ADD_ONLY_VIEW |
| `restructure` | PASS | 5 | False | ADD_ONLY_VIEW |
| `deduplicate` | PASS | 0 | False | ADD_ONLY_VIEW |
| `optimize` | PASS | 5 | False | STRUCTURAL_CANDIDATE_ONLY |

### 文字主題整合索引

| Category | Topics | Headings |
|---|---:|---|
| code_restructure | 2 | Python 元件；JavaScript 元件 |
| document_output | 1 | VOFIE 範例需求 |
| general | 1 | 文字內容 |
| ui_specification | 1 | HTML 規格 |

### 程式元件整合索引

| Language | Components | Symbols |
|---|---:|---|
| javascript | 1 | selectTopic |
| python | 1 | normalize_title |

## 主題重構內容

# 來源：VOFIE_Sample_Input.md

來源雜湊：`d5e4960d8292a36314dd7bfc61f814e267bfe53e6cb21cf8aab8215273dd1be2`

## VOFIE 範例需求

**定位**：`document_output` · `ST-CORE` · 來源行 1-4

**標籤**：`vofie`, `範例需求`, `javascript`, `powerpoint`, `markdown`, `本文應依主題重構`, `excel`, `html`

# VOFIE 範例需求

本文應依主題重構，轉為 Markdown、Word、PowerPoint、Excel、CSV，以及 HTML／CSS／JavaScript 模板。

## 文字內容

**定位**：`general` · `ST-CORE` · 來源行 5-8

**標籤**：`文字內容`, `universal`, `同一份資料先建立`, `content`, `重複內容只標記`, `再依用途輸出`, `原檔不可改寫`, `不可刪除`

## 文字內容

同一份資料先建立 Universal Content IR，再依用途輸出。原檔不可改寫，重複內容只標記，不可刪除。

## Python 元件

**定位**：`code_restructure` · `ST-CORE` · 來源行 9-16

**標籤**：`python`, `return`, `value`, `str`, `元件`, `normalize_title`, `changing`, `compact`

### 程式元件圖譜

| Language | Type | Symbol | Signature | Lines | Syntax |
|---|---|---|---|---:|---|
| python | function | `normalize_title` | `normalize_title(value)` | 12-14 | PASS |

### 結構化原文／候選基線

> 下列程式內容僅重新分區與補齊 Markdown 語言標籤；未做未驗證的語意改寫。

## Python 元件

```python
def normalize_title(value: str) -> str:
    """Return a compact title without changing its words."""
    return " ".join(value.split())
```

## JavaScript 元件

**定位**：`code_restructure` · `ST-CORE` · 來源行 17-24

**標籤**：`javascript`, `item`, `元件`, `selecttopic`, `function`, `return`, `topics`, `find`

### 程式元件圖譜

| Language | Type | Symbol | Signature | Lines | Syntax |
|---|---|---|---|---:|---|
| javascript | function | `selectTopic` | `function selectTopic` | 20-20 | STRUCTURAL_ONLY |

### 結構化原文／候選基線

> 下列程式內容僅重新分區與補齊 Markdown 語言標籤；未做未驗證的語意改寫。

## JavaScript 元件

```javascript
function selectTopic(id) {
  return topics.find((item) => item.id === id);
}
```

## HTML 規格

**定位**：`ui_specification` · `ST-CORE` · 來源行 25-27

**標籤**：`html`, `規格`, `所有互動應支援鍵`, `需要一個搜尋欄位`, `結果表格與匯出`, `分類下拉選單`, `盤與可見焦點`, `csv`

## HTML 規格

需要一個搜尋欄位、分類下拉選單、結果表格與匯出 CSV 按鈕。所有互動應支援鍵盤與可見焦點。

## 品質 Gate

```json
{
  "gate": "PASS",
  "duplicates": 0,
  "fence_normalization_warnings": [],
  "vsis_bridge": {
    "status": "PASS",
    "version": "1.2-compatible",
    "actions": [
      {
        "action": "normalize",
        "status": "PASS"
      },
      {
        "action": "segment",
        "status": "PASS"
      },
      {
        "action": "categorize",
        "status": "PASS"
      },
      {
        "action": "semantic_check",
        "status": "PASS"
      }
    ]
  },
  "st_contract": "PASS",
  "all_original_sources_embedded_in_ir": true,
  "registry_overlay": {
    "status": "PASS",
    "added_extensions": 4,
    "enabled_tools": [
      "TOOL-VOFIE-STDLIB-001",
      "TOOL-VOFIE-VSIS-001",
      "TOOL-VOFIE-DOCX-001",
      "TOOL-VOFIE-ARTIFACT-001",
      "TOOL-VOFIE-PYPDF-001",
      "TOOL-VOFIE-TK-001",
      "TOOL-VOFIE-DND-001",
      "TOOL-VOFIE-RECOVERY-001",
      "TOOL-VOFIE-SIMPLE5-001",
      "TOOL-VOFIE-POLYGLOT-CATALOG-001",
      "TOOL-VOFIE-JS-BRIDGE-001",
      "TOOL-VOFIE-PS-BRIDGE-001",
      "TOOL-VOFIE-HYDRA-GATE-001",
      "TOOL-VOFIE-RUNTIME-COPY-001"
    ]
  },
  "consolidation": {
    "contract": "veritas.vofie-consolidated-view/1.1",
    "operations": [
      "text_merge",
      "code_merge",
      "restructure",
      "deduplicate",
      "optimize"
    ],
    "operation_results": [
      {
        "operation": "text_merge",
        "enabled": true,
        "status": "PASS",
        "affected": 4,
        "source_mutated": false,
        "policy": "ADD_ONLY_VIEW"
      },
      {
        "operation": "code_merge",
        "enabled": true,
        "status": "PASS",
        "affected": 2,
        "source_mutated": false,
        "policy": "ADD_ONLY_VIEW"
      },
      {
        "operation": "restructure",
        "enabled": true,
        "status": "PASS",
        "affected": 5,
        "source_mutated": false,
        "policy": "ADD_ONLY_VIEW"
      },
      {
        "operation": "deduplicate",
        "enabled": true,
        "status": "PASS",
        "affected": 0,
        "source_mutated": false,
        "policy": "ADD_ONLY_VIEW"
      },
      {
        "operation": "optimize",
        "enabled": true,
        "status": "PASS",
        "affected": 5,
        "source_mutated": false,
        "policy": "STRUCTURAL_CANDIDATE_ONLY"
      }
    ],
    "source_topic_count": 5,
    "visible_topic_count": 5,
    "duplicates_marked_and_retained": [],
    "text_groups": [
      {
        "category": "code_restructure",
        "topic_count": 2,
        "topics": [
          {
            "topic_id": "TOP-3EAAAF987526914F",
            "source_id": "SRC-29E8C61C0DAF607B",
            "source_name": "VOFIE_Sample_Input.md",
            "heading": "Python 元件",
            "order": 2,
            "content_hash": "baa2d831030da817a47ee8530eb6a97b192450891b1176340e3dd4feebedbcc8",
            "excerpt": "Python 元件 [code]"
          },
          {
            "topic_id": "TOP-E73F7D46BBBF3B58",
            "source_id": "SRC-29E8C61C0DAF607B",
            "source_name": "VOFIE_Sample_Input.md",
            "heading": "JavaScript 元件",
            "order": 3,
            "content_hash": "63d0e9b6339c2354b4583ec5624bfa11fe7585e971bb4b823778df8ef21c26f1",
            "excerpt": "JavaScript 元件 [code]"
          }
        ]
      },
      {
        "category": "document_output",
        "topic_count": 1,
        "topics": [
          {
            "topic_id": "TOP-EB745C760EF506AF",
            "source_id": "SRC-29E8C61C0DAF607B",
            "source_name": "VOFIE_Sample_Input.md",
            "heading": "VOFIE 範例需求",
            "order": 0,
            "content_hash": "6c1c9f72e31ec56dc4f19fa38d0ead733770c9885c1683562186837a7459d9ed",
            "excerpt": "VOFIE 範例需求 本文應依主題重構，轉為 Markdown、Word、PowerPoint、Excel、CSV，以及 HTML／CSS／JavaScript 模板。"
          }
        ]
      },
      {
        "category": "general",
        "topic_count": 1,
        "topics": [
          {
            "topic_id": "TOP-6405A59147DB8D2D",
            "source_id": "SRC-29E8C61C0DAF607B",
            "source_name": "VOFIE_Sample_Input.md",
            "heading": "文字內容",
            "order": 1,
            "content_hash": "aaced0c96a4ad261dcf21b62bea329ea97b32ee31832cb3db7e0bc34ae95b69b",
            "excerpt": "文字內容 同一份資料先建立 Universal Content IR，再依用途輸出。原檔不可改寫，重複內容只標記，不可刪除。"
          }
        ]
      },
      {
        "category": "ui_specification",
        "topic_count": 1,
        "topics": [
          {
            "topic_id": "TOP-3A89F88521B01A3C",
            "source_id": "SRC-29E8C61C0DAF607B",
            "source_name": "VOFIE_Sample_Input.md",
            "heading": "HTML 規格",
            "order": 4,
            "content_hash": "966cb8fe984c76be3931394727848d741f48b948c67a3cfa0ef44812930af834",
            "excerpt": "HTML 規格 需要一個搜尋欄位、分類下拉選單、結果表格與匯出 CSV 按鈕。所有互動應支援鍵盤與可見焦點。"
          }
        ]
      }
    ],
    "code_groups": [
      {
        "language": "javascript",
        "component_count": 1,
        "components": [
          {
            "unit_id": "CU-C96059028B275531",
            "topic_id": "TOP-E73F7D46BBBF3B58",
            "source_name": "VOFIE_Sample_Input.md",
            "symbol": "selectTopic",
            "unit_type": "function",
            "signature": "function selectTopic",
            "syntax_status": "STRUCTURAL_ONLY",
            "content_hash": "fcf666a74a8c02ea3b181dfe0eef2eab076dcf15846dbcc2da65dfe1bc6df0af"
          }
        ]
      },
      {
        "language": "python",
        "component_count": 1,
        "components": [
          {
            "unit_id": "CU-5F5D23AF9FA166C4",
            "topic_id": "TOP-3EAAAF987526914F",
            "source_name": "VOFIE_Sample_Input.md",
            "symbol": "normalize_title",
            "unit_type": "function",
            "signature": "normalize_title(value)",
            "syntax_status": "PASS",
            "content_hash": "0465ff36b0ca1fb1099b44a69ce24205a0eec505384f60c8040422a50ee931d0"
          }
        ]
      }
    ],
    "source_policy": "READ_ONLY_NO_DELETE_NO_OVERWRITE",
    "api_signature_policy": "KEEP_OR_CANDIDATE_ONLY",
    "view_hash": "7ca58958ef96cbb5cfbd0665a73745fbe7d0ccf4656ed01a0ece3f10fd36f1dd"
  },
  "run_role": "SYSTEM",
  "source_preservation": "PASS",
  "topic_identity": "PASS",
  "source_script_execution": "DENIED",
  "ai_direct_apply": "DENIED",
  "duplicates_retained": true,
  "warnings": [],
  "failures": [],
  "simple_profile": {
    "contract": "veritas.vofie-simple-run/1.1",
    "role": "SYSTEM",
    "max_inputs": 5,
    "primary_outputs": [
      "md",
      "html",
      "component_json",
      "docx",
      "csv"
    ],
    "operations": [
      "text_merge",
      "code_merge",
      "restructure",
      "deduplicate",
      "optimize"
    ],
    "preflight_gate": "PASS"
  }
}
```
