# VIA HTML U/I 六大構面：拆解、對接與治理藍圖 v0.1.0

**交付性質：架構提案與可驗證的規格範例；不是已部署的 UI 產生器、權限引擎或 Windows I/O 橋接器。**

本包保留使用者提供的 Layout、Components、Theme、Behavior、Binding、Access 六構面。每構面再定義兩個工作分類，形成可核對的「6 × 2 = 12」。這是本專案提議採用的分類口徑，不宣稱是所有企業或網頁標準強制使用的唯一架構。

來源檔案未修改；既有 VIA／VDF／VAP／VRN 引擎未修改；未上傳 GitHub。

## def 01｜六大構面與十二個工作分類

| 構面 | 第一子類 | 第二子類 | 要回答的問題 |
|---|---|---|---|
| Layout | L01：Page、Region、外部 Slot | L02：Grid、Breakpoints、Constraints | 內容放在哪裡，寬度改變時如何重排？ |
| Components | C01：元件類型、Props、內容引用 | C02：內部 Slots、Variants、Icons | 用哪一種元件，有哪些輸入與顯示狀態？ |
| Theme | T01：色票、字體、字級階層 | T02：間距、圓角、邊框、陰影、動態 Token | 視覺長什麼樣，允許怎樣調整？ |
| Behavior | B01：Events、Actions、Interactions | B02：State Machine、Lifecycle、聯動 | 操作如何改變狀態，失敗如何回復？ |
| Binding | D01：來源、資料契約、欄位映射 | D02：轉換、查詢、分頁、刷新與發布 | 元件顯示什麼資料，從哪裡來？ |
| Access | A01：Roles、Visibility、資料欄位範圍 | A02：Capabilities、執行端授權、敏感資訊 | 誰能讀、能執行什麼，在哪裡真正擋下？ |

`meta` 與 `validation` 是跨構面支援層，不另外算成第七、第八個 UI 構面。

### Layout：不只是一個 columns 數字

建議抽取 Page → Region → Section → Component 的關係、Header 位置、Gate 面板收合狀態、工作區捲動責任、Footer、Grid/Flex、gap、span、min/max width、容器斷點與列印設定。

外部 Slot 是「這個元件放在何處」；Component 內部 Slot 則是「元件自己的 Header／Body／Footer 如何組成」。兩者名稱相似，但不可混為一個規格。

VIA 對接目標：Header 留在不捲動的殼層列，左側 Gate 管輸入，右側 Workspace 管輸出。手機窄畫面改成單欄、Gate 可收合；不是用旋轉畫面的方式強迫 PC 或手機方向。

### Components：元件數不等於 ID 加 Class 的數量

建議分辨 Header、導覽、選檔器、資料夾選擇、Dropzone、Select、Checkbox、Date Picker、KPI、表格、圖表、敘事報告、Preview、Progress、Alerts、Audit Log、Dialog。

每個元件至少有 component ID、類型、實例 ID、所屬 Slot、Props、內容引用、Variant、鍵盤操作／可及性名稱、Binding Ref、Action Ref、狀態與來源證據。同一個 Class 可以套用多個元件，一個元件也可以有多個 Class，不能用 Class 數推導元件數。

圖片、SVG、圖示、字型與其他資產要有登記與來源。附件提出的本地 SVG Sprite 可放在此構面；資產授權、雜湊、依賴狀態放在 meta。

### Theme：鎖定階層，而不是鎖住所有像素

建議抽取 CSS Variables、字型 fallback、system title／section／body／table／chart／meta 六級字階、行高、色票、間距、圓角、邊框、陰影、對比與 reduced-motion 設定。

本包提供的小字配置是提案：桌面主標題 15px、區塊標題 12px、正文 11px、表格與圖表 10.5px；手機保留階層而不繼續壓小字體。實際可讀性要經瀏覽器與使用者驗收，不能只因數值落在範圍內就宣稱通過。

Visual Lock 鎖定核准的視覺語彙，不應讓檔案選擇、拖曳、篩選與左側收合一起失效。Design Token 日後仍可經版本化更新；不可把視覺鎖定與使用者指定的台股代碼永久不可變規則混在一起。

### Behavior：事件、狀態與生命週期

建議抽取 click／change／input／drop／resize 等事件、對應 action、loading／empty／partial／error／cancelled 狀態、Keyboard／Focus 行為、表格與圖表聯動、錯誤回復、解除綁定與 Observer 清理。

聯動流程建議固定為：Event → Validated Action → State Reducer → Adapter Request → Snapshot Response → Components → Layout Measure → Bounded Fit → Audit。

`ResizeObserver` 用於量測容器，`requestAnimationFrame` 用於安排更新；還需要單一待執行工作、尺寸未變則跳過、隱藏容器略過與迴圈保護，不能只加一個 rAF 就宣稱完全不卡頓。[E4]

### Binding：連資料，不等於內嵌資料

建議抽取 Data Source ID、API／本機 Bridge、輸入參數、輸出欄位、型別、單位、幣別、日期與時區、主鍵、snapshot、資料來源、轉換規則、刷新、分頁、快取鍵與失敗策略。

附件的 DuckDB 表格分頁、Distinct、Pivot、圖表聚合與發布格式可歸在這裡；可見按鈕是 Components，點擊流程是 Behavior，真正授權是 Access。

`null`、`[]` 與非空選取清單要各自定義：本提案採 null＝不設限、[]＝不匹配任何項目、非空陣列＝選取值。沒有此契約，取消所有勾選可能反而變回全選。

價格、成交量及財務原值預設不插補、不平滑、不裁切極值。格式化只影響顯示；必要的推估資料另存並標示。

### Access：不是單純隱藏按鈕

角色與可見性只控制使用體驗；檔案讀寫、系統命令、資料查詢、雲端發布必須在可信本機主程式或後端再驗權。前端顯示隱藏不可作為授權依據。[E3]

本機 I/O 需要明確授權的 File Handle／選取路徑或受控 Bridge；文字框出現 Windows 路徑不代表瀏覽器已取得讀取能力。密鑰只存後端／作業系統安全儲存，不放 HTML、公開 JSON 或 MD 報告。

JSON 規格不能保證 HTML／CSS／JS 不被讀取。凡交付到客戶端的程式碼，不應當作秘密；敏感邏輯與憑證應保留在可信執行端。

## def 02｜本包的實際資料夾

```text
VIA_UI_Six_Dimensions_v0100/
├── README.md
├── governance.yaml                 # 唯一人工編輯入口：提案
├── schemas/
│   └── governance.schema.json       # 結構檢查與不可變規則基準
├── ui-spec/                         # 以下六份是生成檢視，不可各自修改
│   ├── layout/layout.json
│   ├── components/components.json
│   ├── theme/theme.json
│   ├── behavior/behavior.json
│   ├── binding/binding.json
│   └── access/access.json
├── meta/
│   ├── anchor-index.json
│   ├── source-inventory.json
│   ├── conflicts.json
│   ├── template-static-audit.json
│   └── file-hashes.json
├── runtime/
│   └── ui-spec.compiled.json         # 統一 JSON 編譯檢視
└── validation/
    ├── acceptance-plan.json
    └── results.json
```

本包的 `governance.yaml`、編譯 JSON、schema 都已讀取與檢查，但只是規格檔通過檢查，不代表網頁、UIAction、資料庫、Windows 對話框或雲端發布已通過實測。

### 原 A 架構的完整擴充方式（規劃，不是本包已實作的檔案）

```text
ui-spec/
├── layout/
│   ├── page.json / page.schema.json
│   ├── regions.json
│   ├── grid.json
│   ├── breakpoints.json
│   └── constraints.json
├── components/
│   ├── registry.json
│   ├── input/{file-picker,folder-picker,dropzone,select,checkbox}.json
│   ├── card/{card.schema,variants}.json
│   ├── table/{table.schema,columns,virtual-scroll,pivot}.json
│   ├── chart/{chart.schema,axis,legend,interaction}.json
│   ├── narrative/{sections,source-references}.json
│   └── icons/{registry,asset-policy}.json
├── theme/
│   ├── tokens/{colors,typography,spacing,radius,shadow,motion}.json
│   ├── profiles/{desktop,mobile,print}.json
│   ├── header-profiles.json
│   ├── light.json
│   └── visual-lock.json
├── behavior/
│   ├── events.schema.json
│   ├── actions.json
│   ├── interactions.json
│   ├── state-machine.json
│   ├── cross-filter.json
│   ├── resize-policy.json
│   └── error-recovery.json
├── binding/
│   ├── source-registry.json
│   ├── contracts/{request,response,dataset}.schema.json
│   ├── api-map.json
│   ├── field-map.json
│   ├── transforms.json
│   ├── refresh-policy.json
│   ├── pagination-cache.json
│   └── publish-policy.json
├── access/
│   ├── roles.json
│   ├── visibility.json
│   ├── capabilities.json
│   ├── path-policy.json
│   ├── secret-policy.json
│   └── enforcement-contract.json
└── meta/
    ├── version.json
    ├── source-inventory.json
    ├── anchor-index.json
    ├── dependency-registry.json
    ├── conflicts.json
    ├── compatibility.json
    ├── changelog.md
    └── rollback-manifest.json
```

`.schema.json` 定義「允許什麼結構」，一般 `.json` 存實際設定，兩者不可混用。[E1] 初期先採每構面一份生成 JSON；當單一構面需要獨立發布與維護時，再依上面的細分架構拆出子檔。

不建議 YAML 與 JSON 兩邊都人工編輯。若未來改用分檔 JSON 當 SSOT，就把 YAML 改成索引；兩種維護模式選一種。

## def 03｜附件內容如何歸位

| 附件段落 | 主責構面 | 跨構面依賴 |
|---|---|---|
| 240–249：Design Token / Theme | Theme | meta：來源與版本 |
| 251–258：共用 Grid / Left Panel / Footer | Layout | Components：槽位 |
| 260–270：Header 與 Schema 產生控制元件 | Layout、Components | Theme、Binding |
| 330–405：SVG Sprite 與圖示登記 | Components | Theme：currentColor；meta：資產來源 |
| 412–536：低格線表格 | Components、Theme | Binding：數字型別、單位 |
| 541–633：自適應欄位格式化 | Binding | Components：欄位契約 |
| 638–803：虛擬捲動與分批讀取 | Behavior、Binding | Layout：Viewport；驗證：快取與一致性 |
| 808–1067：排序、隱藏、Distinct、Pivot | Components、Behavior | Binding：查詢；Access：資料範圍 |
| 1072–1457：單向資料流、多圖表聯動 | Behavior | Binding：snapshot、filters、aggregation |
| 1462–1555：收合與圖表尺寸調整 | Layout、Behavior | Theme：字階；驗證：實際 overflow |
| 5–15、150–211：發布設定與 vrn2:// | Binding、Behavior | Access：憑證與發布權；Components：輸入表單 |

以上是內容分類，不代表已驗證附件中每個範例的正確性、效能或執行結果。附件中的「毫秒」「O(1)」「一次 I/O」等性能敘述不直接成為本包保證；需要指定資料量、查詢計畫與硬體的量測。

## def 04｜分析一個 HTML 的實際工作流程

1. **來源與資產盤點。** 唯讀讀取 HTML 與其 CSS／JS／SVG／資料引用，記錄編碼、雜湊、相對路徑與缺失依賴。ZIP、資料夾或選取檔案不代表已取得所有引用資產。
2. **靜態拆解。** HTML 用結構解析器；CSS 用 CSS parser；JS 用 JS parser/AST。保存來源節點定位。Regex 可以輔助找候選，不作完整 CSS／JS 語意分析的替代品。
3. **映射六構面。** 先輸出觀測資料，再與目標規格比對。只看檔名或 class，不足以確定系統類型、欄位單位或權限。
4. **隔離執行觀測。** 需要取得計算後樣式、動態 DOM、尺寸、圖表與互動效果時，在受控瀏覽器執行。預設封鎖來源寫入、外部網路與 Native Bridge；需要的資產依清單放行。
5. **記錄缺口與衝突。** 找不到後端權限、外部 JS、查詢定義或憑證時，填 unknown／NOT_AVAILABLE，而不是補上一個理想化答案。
6. **輸出規格與報告。** 單一治理檔、六構面檢視、來源證據、元件關係、驗證結果與 MD 交接報告。

HTML `DOMParser` 不會執行解析文件中的一般 script，因此適合其中一部分靜態工作，但不是動態 UI 測試器；解析的文件仍可能下載特定資源，插回活動 DOM 亦有注入風險。離線、安全與渲染正確性需另外設計。[E5]

建議每項發現都有：

```json
{
  "finding_id": "UI-FINDING-001",
  "facet": "behavior",
  "anchor_id": "UI-ACTION-PANEL",
  "source_ref": {
    "artifact": "template.html",
    "sha256": "actual-source-hash-required",
    "selector": "#collapseBtn",
    "ast_symbol": "toggleLeftPanel"
  },
  "evidence_status": "source_observed",
  "runtime_status": "NOT_RUN",
  "observed": "button references a toggle handler",
  "inference": null
}
```

這是紀錄格式示意，雜湊與節點應由分析器填入，不可照樣複製假值。

## def 05｜精準錨點與安全調整

本包有 36 個業務錨點，每個指向 `governance.yaml` 對應 JSON 結構的精準 JSON Pointer。

```yaml
anchor_id: UI-LAYOUT-HEADER
file: governance.yaml
json_pointer: /def_layout/regions/header
expected_version: 0.1.0
expected_hash: <執行時讀取的原始節點或檔案雜湊>
operation: replace
```

`anchor_id` 是 VIA 業務身分；JSON Pointer 是資料位置；JSON Schema 的 `$anchor` 是 schema 子結構引用；DOM `data-*` 與 CSS/JS 註解錨點則是原始碼定位。這些都不是同一種東西。YAML 的 `&anchor`／`*alias` 只用於重用資料，也不等於編輯授權。[E1]

更新流程：Stage 副本 → 身分／舊版本／hash 前置檢查 → parsed patch → schema → 引用完整性 → 測試 → 人工或已授權政策審核 → 新版提交。陣列必須先以穩定 ID 尋找成員，不依賴會因排序改變的索引。

`readOnly: true`、`editable: false` 與 CSS Visual Lock 都不是自動生效的安全防線；規格需由可信載入器與執行端強制檢查。JSON Schema 的 readOnly 屬於註記用途，不能代替授權。[E2][E3]

僅使用者指定的三種台股股票代碼與關係列入業務不可變規則；UI Theme、布局、其他字典可在受控變更流程下修改。

## def 06｜來源差異：不偷偷合併

**Header：**附件描述品牌小字 → 子系統與印鑑 → 說明三行；前面確認版是子系統／主標題 → 品牌兩行且無圖像 Logo。本包保留兩個 profile，以既有確認版為基準；附件方案仍是候選，不自動套版。

**Ticker：**附件 `^[1-9]\\d{3}$` 範例沒有排除 2021–2030。使用者明確規則優先；本包以 ASCII 四碼、排除指定區間、三格式同碼與 TW/TWO 市場關係做檢查。這是 VIA 的股票識別政策，不表示 ETF、指數或所有市場代碼都要符合它。

**字級：**附件表格範例為 14px，但使用者偏好緊湊小字。本包以可讀性驗收為前提提供 desktop/mobile 階層提案，未聲稱兩個來源完全一致。

**視覺鎖定：**前版整塊輸入區被 `.editable-only` 一起鎖住，不符合「可操作、不可破壞視覺」目標。記錄在 audit 中，未在此包修改原始模板。

## def 07｜上一版 HTML 的具體靜態觀測

來源：`VIA_Universal_Resonance_Template_Adapter_v002_CONFIRMED.html`。詳細定位與 hash 見 `meta/template-static-audit.json`。

| 項目 | 原始碼觀測 | 結論範圍 |
|---|---|---|
| Input Visual Lock | `.visual-locked .editable-only` 設定 `pointer-events:none`，輸入卡片使用該 class | 功能輸入被視覺鎖定擋住的靜態證據；未進行瀏覽器操作測試 |
| Auto Dock | `autoDetectFromDrop` 以 `f.name` 分類 | 只是檔名推測，不是內容分析或成功引擎對接證據 |
| Run Validation | 函式直接呼叫 `log("PASS", ...)` | 日誌不代表有量測的驗證 |
| Windows I/O | HTML 中找不到 `input[type=file]` | 這份原始碼沒有該選檔元件；未驗證外部 Bridge |

這些觀測是為了界定規格與測試工作，不宣稱已修正所有問題。

## def 08｜建議的 MD 交接報告格式

每個 HTML 一份 `UI_Analysis.md`：

```text
1. 文件身分與分析範圍
2. 一頁摘要：用途、可確認能力、主要風險
3. Layout：區域樹、Slot、斷點與尺寸
4. Components：元件清單、Props、內容引用
5. Theme：Tokens、字階、視覺鎖定差異
6. Behavior：事件、狀態、動作、聯動
7. Binding：資料契約、Adapter、轉換與缺口
8. Access：已知政策與尚未驗證的執行端
9. 六構面關係：元件 ↔ 事件 ↔ 資料 ↔ 權限
10. 衝突與修改建議：不能把建議寫成已完成
11. 驗證結果：PASS / FAIL / WARN / NOT_RUN / NOT_AVAILABLE
12. 來源定位、原始內容與限制
```

多個 HTML 再產生 `UI_Consolidation.md`，依構面比較共通模板、差異、缺失引用、候選元件與衝突。摘要與原文分開；不得把幾個檔案的 UI 標籤直接混接成「正式規格」。

## def 09｜驗證狀態與交付邊界

本次靜態規格檢查 19 項通過、0 項失敗：YAML/JSON 一致、schema 結構、六構面與十二分類、36 錨點唯一且指向正確、元件 Slot／Action 權限引用、字階關係、台股代碼正反案例、不可變規則修改拒絕、可編輯 Theme 的結構通過。

**未執行：**瀏覽器畫面回歸、Windows 原生對話框、PowerShell 啟動器、VDF／VRN／VAP 實際引擎對接、後端授權、真實大資料效能。請勿把本包的 19 項靜態檢查當作上述功能已成功。

schema 只驗證藍圖的主要結構、分類與保護規則基準，並非每個第三方 API 參數的完整 schema，也不會自行提供 UI 渲染或安全授權。

## def 10｜來源與技術依據

**使用者來源：**`貼上的文字 (1)(3).txt`（Design Tokens、Grid、Header、SVG、表格、虛擬捲動、聯動與發布範例）；上一輪確認版 HTML（靜態檢視）。雜湊見 source inventory。本包未從這些文件臆造實測結果。

**新增工程建議依據（非附件原文）：**

- [E1] JSON Schema，Modular JSON Schema combination：`https://json-schema.org/understanding-json-schema/structuring`
- [E2] JSON Schema，Annotations：`https://json-schema.org/understanding-json-schema/reference/annotations`
- [E3] OWASP，Authorization Cheat Sheet：`https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html`
- [E4] MDN，ResizeObserver：`https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver`
- [E5] MDN，DOMParser.parseFromString：`https://developer.mozilla.org/en-US/docs/Web/API/DOMParser/parseFromString`
