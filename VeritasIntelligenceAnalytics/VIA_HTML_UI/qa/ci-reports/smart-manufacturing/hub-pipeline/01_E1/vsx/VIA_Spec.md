# VIA-SYNCHRONIZER-Standalone — 規格書（VSX v0100）

- contract: `VIA_SPEC_IR/1.0` · 產生 2026-09-15 10:21:59 · 規格項 441 · 缺口 60 · registry 新增 501 / 累計 501
- 證據等級：**V** 結構明確（標籤/AST/schema）· **M** 模式命中（規則句/正則）· **P** 推論（型別/單位/名稱）

## 來源

| 檔案 | 類型 | bytes | blake2s | 編碼 |
|---|---|---:|---|---|
| VIA-SYNCHRONIZER-Standalone.html | html | 72555 | `bc446f6ecf8cc7f2` | utf-8-sig |

## 1. UI 規格

### 1.1 元件（90）

| ID | 元件 | 選擇器 | role | data-* | 事件 | 子元件 | 文字 | 等級 |
|---|---|---|---|---|---|---:|---|---|
| SPEC-UI-COMPCLS-984B6D0ECAB1 | <header> header | `html > body > div.shell > header.top` |  |  |  | 2 | 理 VERITAS INTELLIGENCE ANALYTICS SYNCHRO | V |
| SPEC-UI-COMPCLS-272EDED95C27 | <section> hero | `html > body > div.shell > section.hero` |  |  |  | 3 | 本機智慧銜接同步器 以分層狀態模型管理 VIA UI 的視圖、同步規則與自定義管 | V |
| SPEC-UI-COMPCLS-2225C80C7DE7 | <div> hero ×2 | `html > body > div.shell > section.hero > div.hero-actions` |  |  |  | 8 | 立即同步至其他分頁 匯出 JSON 匯出模組 CSV 匯出歷史 CSV 匯出 E | V |
| SPEC-UI-COMPONEN-FEADAD40E8E6 | <button> syncNow | `button#syncNow` |  |  |  | 0 | 立即同步至其他分頁 | V |
| SPEC-UI-COMPONEN-A71B0920B8DD | <button> exportJson | `button#exportJson` |  |  |  | 0 | 匯出 JSON | V |
| SPEC-UI-COMPONEN-9377C845A28F | <button> exportCsv | `button#exportCsv` |  |  |  | 0 | 匯出模組 CSV | V |
| SPEC-UI-COMPONEN-57312736B8DE | <button> exportHistory | `button#exportHistory` |  |  |  | 0 | 匯出歷史 CSV | V |
| SPEC-UI-COMPONEN-98585E71AB1A | <button> exportExcel | `button#exportExcel` |  |  |  | 0 | 匯出 Excel 樞紐 | V |
| SPEC-UI-COMPCLS-DBE082AEDCD0 | <label> btn | `html > body > div.shell > section.hero > div.hero-actions > label.btn` |  |  |  | 0 | 匯入 JSON／CSV／Excel | V |
| SPEC-UI-COMPONEN-FEDA3B64E3EF | <input> importData | `input#importData` |  |  |  | 0 |  | V |
| SPEC-UI-COMPCLS-492A4E179888 | <a> btn | `html > body > div.shell > section.hero > div.hero-actions > a.btn` |  |  |  | 0 | 開啟中央管理 UI | V |
| SPEC-UI-COMPCLS-7460BD30B26C | <main> grid | `html > body > div.shell > main.grid` |  |  |  | 10 | 同步通道狀態 本機資料不會送往遠端服務；同步只發生於同源瀏覽器分頁。 資料來源  | V |
| SPEC-UI-COMPCLS-1EFE650F6C3D | <section> panel ×6 | `html > body > div.shell > main.grid > section.panel` |  |  |  | 7 | 同步通道狀態 本機資料不會送往遠端服務；同步只發生於同源瀏覽器分頁。 資料來源  | V |
| SPEC-UI-COMPCLS-EF5C14DF5A09 | <div> grid | `html > body > div.shell > main.grid > section.panel > div.status-grid` |  |  |  | 4 | 資料來源 Local Storage 即時通道 BroadcastChannel | V |
| SPEC-UI-COMPCLS-4FAC331E397F | <div> card ×4 | `html > body > div.shell > main.grid > section.panel > div.status-grid > div.status-card` |  |  |  | 2 | 資料來源 Local Storage | V |
| SPEC-UI-COMPONEN-B474D147EBCC | <strong> source | `strong#source` |  |  |  | 0 | Local Storage | V |
| SPEC-UI-COMPONEN-84BF39A10FE7 | <strong> channelStatus | `strong#channelStatus` |  |  |  | 0 | BroadcastChannel | V |
| SPEC-UI-COMPONEN-47A3001C90D6 | <strong> lastSync | `strong#lastSync` |  |  |  | 0 | 尚未同步 | V |
| SPEC-UI-COMPONEN-9706279A435C | <strong> version | `strong#version` |  |  |  | 0 | v2 | V |
| SPEC-UI-COMPCLS-A969E02FE451 | <div> list ×2 | `html > body > div.shell > main.grid > section.panel > div.check-list` |  |  |  | 4 | 本機儲存可用 跨分頁通道可用 | V |
| SPEC-UI-COMPCLS-24E0C56BE133 | <label> label ×7 | `html > body > div.shell > main.grid > section.panel > div.check-list > label.check` |  |  |  | 1 | 本機儲存可用 | V |
| SPEC-UI-COMPONEN-043D39F31B39 | <input> storageCheck | `input#storageCheck` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-C6106F7D0C6D | <input> channelCheck | `input#channelCheck` |  |  |  | 0 |  | V |
| SPEC-UI-COMPCLS-4565BA920275 | <div> grid | `html > body > div.shell > main.grid > section.panel > div.rule-grid` |  |  |  | 3 | 同步範圍 視圖＋模組＋規則 只同步視圖 只同步模組 手動同步 衝突處理 最新時間 | V |
| SPEC-UI-COMPCLS-1806A5DCB868 | <label> label ×21 | `html > body > div.shell > main.grid > section.panel > div.rule-grid > label:nth-of-type(1)` |  |  |  | 1 | 同步範圍 視圖＋模組＋規則 只同步視圖 只同步模組 手動同步 | V |
| SPEC-UI-COMPONEN-EC00658B560F | <select> syncScope | `select#syncScope` |  |  |  | 4 | 視圖＋模組＋規則 只同步視圖 只同步模組 手動同步 | V |
| SPEC-UI-COMPONEN-EBFDA2B29D81 | <select> conflictRule | `select#conflictRule` |  |  |  | 3 | 最新時間優先 保留本頁狀態 接受遠端狀態 | V |
| SPEC-UI-COMPONEN-DE763B66B66C | <input> debounceMs | `input#debounceMs` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-27B11C7F04AB | <div> ruleSummary | `div#ruleSummary` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-43B303FDC344 | <button> applyRules | `button#applyRules` |  |  |  | 0 | 套用同步規則 | V |
| SPEC-UI-COMPCLS-303BDA5A77AB | <section> panel ×3 | `html > body > div.shell > main.grid > section.panel.panel-wide` |  |  |  | 7 | 產業管理模組範本 選擇產業範本後，可一鍵建立模組、圖表與歷史趨勢資料；可選擇替換 | V |
| SPEC-UI-COMPCLS-8CFEAB414F36 | <div> grid | `html > body > div.shell > main.grid > section.panel.panel-wide > div.template-grid` |  |  |  | 3 | 產業範本 一般空白管理範本 智慧製造 · OEE／品質／停機 金融資安 · 事件 | V |
| SPEC-UI-COMPONEN-DEAB416E1A71 | <select> templateSelect | `select#templateSelect` |  |  |  | 5 | 一般空白管理範本 智慧製造 · OEE／品質／停機 金融資安 · 事件／威脅／合 | V |
| SPEC-UI-COMPONEN-68B11C4010DC | <select> templateMode | `select#templateMode` |  |  |  | 2 | 替換目前自定義模組 合併到現有模組 | V |
| SPEC-UI-COMPONEN-6F032DA39E45 | <button> applyTemplate | `button#applyTemplate` |  |  |  | 0 | 快速建立範本 | V |
| SPEC-UI-COMPONEN-0D0F59EDBF4C | <button> exportTemplate | `button#exportTemplate` |  |  |  | 0 | 匯出範本包 JSON | V |
| SPEC-UI-COMPONEN-5359C26BA49E | <div> templateSummary | `div#templateSummary` |  |  |  | 0 |  | V |
| SPEC-UI-COMPCLS-0324465DA10C | <div> chart | `html > body > div.shell > main.grid > section.panel.panel-wide > div.chart-add` |  |  |  | 5 | 圖表 ID 圖表名稱 圖表類型 折線圖 柱狀圖 面積圖 KPI 卡 指標／欄位  | V |
| SPEC-UI-COMPONEN-FCFC4F3318CC | <input> chartId | `input#chartId` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-93FB8A22A72E | <input> chartName | `input#chartName` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-A332274AEB3A | <select> chartType | `select#chartType` |  |  |  | 4 | 折線圖 柱狀圖 面積圖 KPI 卡 | V |
| SPEC-UI-COMPONEN-0D7C3D596385 | <input> chartMetric | `input#chartMetric` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-838315A45279 | <button> addChart | `button#addChart` |  |  |  | 0 | 新增圖表 | V |
| SPEC-UI-COMPCLS-B03150700494 | <div> grid | `html > body > div.shell > main.grid > section.panel.panel-wide > div.analytics-grid` |  |  |  | 3 | 目前範本 一般空白 自定義圖表 0 歷史資料筆數 0 | V |
| SPEC-UI-COMPCLS-AE7EB23AA18F | <div> card ×3 | `html > body > div.shell > main.grid > section.panel.panel-wide > div.analytics-grid > div.analytics-card` |  |  |  | 2 | 目前範本 一般空白 | V |
| SPEC-UI-COMPONEN-63B3EC3A3B0D | <strong> templateName | `strong#templateName` |  |  |  | 0 | 一般空白 | V |
| SPEC-UI-COMPONEN-E74A32A81FDF | <strong> chartCount | `strong#chartCount` |  |  |  | 0 | 0 | V |
| SPEC-UI-COMPONEN-2281584E40BD | <strong> historyCount | `strong#historyCount` |  |  |  | 0 | 0 | V |
| SPEC-UI-COMPONEN-1253A5F4EB1B | <div> chartList | `div#chartList` |  |  |  | 0 |  | V |
| SPEC-UI-COMPCLS-E100E9295963 | <div> grid | `html > body > div.shell > main.grid > section.panel.panel-wide > div.pivot-grid` |  |  |  | 5 | 樞紐列欄位 日期 分類 模組 ID 樞紐欄欄位 指標 分類 模組 ID 數值欄位 | V |
| SPEC-UI-COMPONEN-5317C9FDD067 | <select> pivotRow | `select#pivotRow` |  |  |  | 3 | 日期 分類 模組 ID | V |
| SPEC-UI-COMPONEN-94B061993B5A | <select> pivotColumn | `select#pivotColumn` |  |  |  | 3 | 指標 分類 模組 ID | V |
| SPEC-UI-COMPONEN-DF01E41270A6 | <select> pivotValue | `select#pivotValue` |  |  |  | 1 | 數值 | V |
| SPEC-UI-COMPONEN-17B78E04EF99 | <select> pivotAgg | `select#pivotAgg` |  |  |  | 4 | 總和 平均 最小 最大 | V |
| SPEC-UI-COMPONEN-33F37919F24B | <button> applyPivot | `button#applyPivot` |  |  |  | 0 | 套用樞紐設定 | V |
| SPEC-UI-COMPONEN-A884A7239E7D | <div> historySummary | `div#historySummary` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-3C695D9FF9E4 | <section> syncAddonSlot | `section#syncAddonSlot` |  | data-addon-slot |  | 2 | OPTIONAL MODULE ADD-ON local manifest ·  | V |
| SPEC-UI-COMPONEN-3F2971803772 | <div> syncAddonSlotBody | `div#syncAddonSlotBody` |  |  |  | 0 | 可由未來產業包註冊研究指標、匯入器或自訂匯出器。 | V |
| SPEC-UI-COMPONEN-F51D71FEB54E | <span> moduleCount | `span#moduleCount` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-EBD86E77EA68 | <input> moduleId | `input#moduleId` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-48C4CBD22A5C | <input> moduleName | `input#moduleName` |  |  |  | 0 |  | V |
| SPEC-UI-COMPCLS-D2022A04E9E2 | <label> label | `html > body > div.shell > main.grid > section.panel.panel-wide > div.module-add > label.module-type` |  |  |  | 1 | 模組類型 儀表板 資料端點 自動化 治理稽核 外部整合 | V |
| SPEC-UI-COMPONEN-5BB671E85FDE | <select> moduleType | `select#moduleType` |  |  |  | 5 | 儀表板 資料端點 自動化 治理稽核 外部整合 | V |
| SPEC-UI-COMPCLS-148E397E4CBC | <label> label | `html > body > div.shell > main.grid > section.panel.panel-wide > div.module-add > label.module-pin` |  |  |  | 1 | 固定顯示 | V |
| SPEC-UI-COMPONEN-5EEE32542E00 | <input> modulePinned | `input#modulePinned` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-10E7CF921A84 | <button> addModule | `button#addModule` |  |  |  | 0 | 新增模組 | V |
| SPEC-UI-COMPONEN-E259DAF7F352 | <div> moduleList | `div#moduleList` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-309DAF9AAEC2 | <select> density | `select#density` |  |  |  | 3 | 舒適 平衡 緊湊 | V |
| SPEC-UI-COMPONEN-03109D0C954C | <select> theme | `select#theme` |  |  |  | 3 | 明亮 高對比 系統 | V |
| SPEC-UI-COMPONEN-65C30F5CFB47 | <input> motion | `input#motion` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-A97D91DE0D56 | <input> hints | `input#hints` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-40B907D1C7D9 | <input> live | `input#live` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-E73C9433F86C | <input> autoApply | `input#autoApply` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-A56607A721F5 | <button> applyView | `button#applyView` |  |  |  | 0 | 套用視圖並同步 | V |
| SPEC-UI-COMPONEN-2B8776D0AC79 | <select> fontScale | `select#fontScale` |  |  |  | 3 | 小 標準 大 | V |
| SPEC-UI-COMPONEN-8138EDDA930E | <input> headerHeight | `input#headerHeight` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-AEC61F389BFE | <input> panelHeight | `input#panelHeight` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-5AB1B826157C | <input> equalPanels | `input#equalPanels` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-E65C9234B43B | <select> surface | `select#surface` |  |  |  | 2 | 淺色 柔和灰綠 | V |
| SPEC-UI-COMPCLS-0DAB4E383F3B | <div> form | `html > body > div.shell > main.grid > section.panel > div.format-actions` |  |  |  | 5 | JSON 狀態 模組 CSV 歷史 CSV 圖表 CSV Excel 樞紐 `. | V |
| SPEC-UI-COMPONEN-412D8BDE0808 | <button> exportJson2 | `button#exportJson2` |  |  |  | 0 | JSON 狀態 | V |
| SPEC-UI-COMPONEN-F7AB0D9EBD6A | <button> exportCsv2 | `button#exportCsv2` |  |  |  | 0 | 模組 CSV | V |
| SPEC-UI-COMPONEN-FBC9DB41AC7B | <button> exportHistory2 | `button#exportHistory2` |  |  |  | 0 | 歷史 CSV | V |
| SPEC-UI-COMPONEN-DE5054558A4E | <button> exportCharts | `button#exportCharts` |  |  |  | 0 | 圖表 CSV | V |
| SPEC-UI-COMPONEN-FDDD7C4DB47D | <button> exportExcel2 | `button#exportExcel2` |  |  |  | 0 | Excel 樞紐 `.xls` | V |
| SPEC-UI-COMPONEN-1EC61AF88BEB | <textarea> jsonPreview | `textarea#jsonPreview` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-13D129D794EF | <button> loadState | `button#loadState` |  |  |  | 0 | 重新讀取本機狀態 | V |
| SPEC-UI-COMPONEN-658F41D13345 | <button> clearState | `button#clearState` |  |  |  | 0 | 清除本機同步狀態 | V |
| SPEC-UI-COMPONEN-D22A1F258671 | <div> log | `div#log` |  |  |  | 0 |  | V |
| SPEC-UI-COMPCLS-6B66734D958E | <footer> footer | `html > body > div.shell > footer.footer` |  |  |  | 2 | VIA CENTRAL · ADAPTIVE SMART BRIDGE · fi | V |

### 1.2 表單欄位（32）

| ID | 欄位 | 型別 | 必填 | 驗證 | 選項 | label | 表單 |
|---|---|---|---|---|---|---|---|
| SPEC-UI-FORM_FIE-3A67853467C0 | importData | file |  | accept=application/json,.json,text/csv,.csv,application/vnd.ms-excel,.xls,.xml |  | 匯入 JSON／CSV／Excel |  |
| SPEC-UI-FORM_FIE-E91CABE67C51 | storageCheck | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-099C4E31E64C | channelCheck | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-59EBDDB56445 | syncScope | select |  |  | 視圖＋模組＋規則/只同步視圖/只同步模組/手動同步 |  |  |
| SPEC-UI-FORM_FIE-67E096D5A038 | conflictRule | select |  |  | 最新時間優先/保留本頁狀態/接受遠端狀態 |  |  |
| SPEC-UI-FORM_FIE-4553A6F01385 | debounceMs | number |  | min=0, max=5000, step=50 |  |  |  |
| SPEC-UI-FORM_FIE-A1B0987F9EBB | templateSelect | select |  |  | 一般空白管理範本/智慧製造 · OEE／品質／停機/金融資安 · 事件／威脅／合規/智慧醫療 · 流量／品質／安全/投資研究 · Watchlist／技術／風險 |  |  |
| SPEC-UI-FORM_FIE-E10DA8E88C05 | templateMode | select |  |  | 替換目前自定義模組/合併到現有模組 |  |  |
| SPEC-UI-FORM_FIE-B3298D2DD8D7 | chartId | text |  |  |  | 例如：oee-trend |  |
| SPEC-UI-FORM_FIE-93DE9DF12F95 | chartName | text |  |  |  | 例如：OEE 趨勢 |  |
| SPEC-UI-FORM_FIE-8EF1001DD6FE | chartType | select |  |  | 折線圖/柱狀圖/面積圖/KPI 卡 |  |  |
| SPEC-UI-FORM_FIE-E00755381263 | chartMetric | text |  |  |  | 例如：oee |  |
| SPEC-UI-FORM_FIE-65BF9EFFCF95 | pivotRow | select |  |  | 日期/分類/模組 ID |  |  |
| SPEC-UI-FORM_FIE-641461760571 | pivotColumn | select |  |  | 指標/分類/模組 ID |  |  |
| SPEC-UI-FORM_FIE-E098AC3CFBE2 | pivotValue | select |  |  | 數值 |  |  |
| SPEC-UI-FORM_FIE-466DEBFA9FA5 | pivotAgg | select |  |  | 總和/平均/最小/最大 |  |  |
| SPEC-UI-FORM_FIE-F001AD6BDE05 | moduleId | text |  |  |  | 例如：risk-center |  |
| SPEC-UI-FORM_FIE-3E85739A903F | moduleName | text |  |  |  | 例如：風險中心 |  |
| SPEC-UI-FORM_FIE-8A323CB10446 | moduleType | select |  |  | 儀表板/資料端點/自動化/治理稽核/外部整合 |  |  |
| SPEC-UI-FORM_FIE-B834F5EFD011 | modulePinned | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-8583ED50F29E | density | select |  |  | 舒適/平衡/緊湊 | 內容密度 |  |
| SPEC-UI-FORM_FIE-9CC943D9E881 | theme | select |  |  | 明亮/高對比/系統 | 色彩模式 |  |
| SPEC-UI-FORM_FIE-C640C92D1A66 | motion | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-87EAD4558C37 | hints | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-38B38CE22EE4 | live | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-8452D9AE177A | autoApply | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-C2B0F47F76DE | fontScale | select |  |  | 小/標準/大 | 專業字級 |  |
| SPEC-UI-FORM_FIE-949E84F87DAE | headerHeight | number |  | min=36, max=72, step=2 |  | 標題高度（px） |  |
| SPEC-UI-FORM_FIE-73F465CB36B4 | panelHeight | number |  | min=220, max=560, step=10 |  | 左右面板高度（px） |  |
| SPEC-UI-FORM_FIE-B73FBF5290D6 | equalPanels | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-E8AD4A4BAC75 | surface | select |  |  | 淺色/柔和灰綠 | 淺色表面 |  |
| SPEC-UI-FORM_FIE-901A22A5B3B5 | jsonPreview | textarea |  |  |  |  |  |

### 1.x 版面（grid/flex）（30）

- `.top` .top: flex {"props": {"align-items": "center", "justify-content": "space-between", "gap": "18px"}}
- `.brand` .brand: flex {"props": {"align-items": "center", "gap": "12px"}}
- `.seal` .seal: grid {"props": {}}
- `.hero-actions` .hero-actions: flex {"props": {"gap": "9px"}}
- `.grid` .grid: grid {"props": {"grid-template-columns": "1fr 1fr", "gap": "16px"}}
- `.status-grid` .status-grid: grid {"props": {"grid-template-columns": "repeat(2,1fr)", "gap": "10px"}}
- `.field` .field: grid {"props": {"gap": "6px"}}
- `.check-list` .check-list: grid {"props": {"gap": "9px"}}
- `.check` .check: flex {"props": {"align-items": "center", "justify-content": "space-between"}}
- `.footer` .footer: flex {"props": {"justify-content": "space-between", "gap": "12px"}}
- `.log` .log: grid {"props": {"gap": "7px"}}
- `.module-add` .module-add: grid {"props": {"grid-template-columns": "1fr 1.35fr 1fr auto auto", "gap": "8px", "align-items": "end"}}
- `.module-add label,.rule-grid label` .module-add label,.rule-grid label: grid {"props": {"gap": "5px"}}
- `.module-list` .module-list: grid {"props": {"gap": "7px"}}
- `.module-row` .module-row: grid {"props": {"grid-template-columns": "24px minmax(120px,1.1fr) .9fr 92px 72px 72px 34px", "gap": "8px", "align-items": "center"}}
- `.module-actions` .module-actions: flex {"props": {"gap": "4px"}}
- `.rule-grid` .rule-grid: grid {"props": {"grid-template-columns": "1fr 1fr 1fr", "gap": "10px"}}
- `.rule-foot` .rule-foot: flex {"props": {"align-items": "center", "justify-content": "space-between", "gap": "10px"}}
- `.format-actions` .format-actions: flex {"props": {"gap": "8px"}}
- `.template-grid` .template-grid: grid {"props": {"grid-template-columns": "1fr 1fr 1.2fr", "gap": "10px", "align-items": "end"}}
- `.template-grid label,.chart-add label,.pivot-grid label` .template-grid label,.chart-add label,.pivot-grid label: grid {"props": {"gap": "5px"}}
- `.template-actions` .template-actions: flex {"props": {"gap": "8px"}}
- `.chart-add` .chart-add: grid {"props": {"grid-template-columns": "1.1fr 1.1fr 1fr 1fr auto", "gap": "8px", "align-items": "end"}}
- `.analytics-grid` .analytics-grid: grid {"props": {"grid-template-columns": "repeat(3,1fr)", "gap": "10px"}}
- `.chart-list` .chart-list: grid {"props": {"gap": "7px"}}
- `.chart-row` .chart-row: grid {"props": {"grid-template-columns": "24px 1.2fr 1fr 1fr 72px 34px", "gap": "8px", "align-items": "center"}}
- `.pivot-grid` .pivot-grid: grid {"props": {"grid-template-columns": "1fr 1fr 1fr 1fr auto", "gap": "8px", "align-items": "end"}}
- `.layout-control` .layout-control: grid {"props": {"grid-template-columns": "1fr 1fr 1fr 1fr 1fr", "gap": "7px", "align-items": "end"}}
- `.shell` .shell: grid {"props": {}}
- `.addon-slot-head` .addon-slot-head: flex {"props": {"align-items": "center", "justify-content": "space-between", "gap": "8px"}}

## 2. 設計 Token

- **CSS 變數**（44）：`--ink: #17241f`, `--muted: #71817a`, `--line: #dbe6e0`, `--paper: #f4f8f5`, `--panel: rgba(255,255,255,.9)`, `--accent: #b84436`, `--teal: #257f70`, `--teal-soft: #e3f3ed`, `--shadow: 0 18px 50px rgba(28,58,46,.10)`, `--ui-font-scale: 1`, `--ui-header-h: 44px`, `--ui-panel-h: 292px`, `--ui-surface: #fbfcfb`, `--bg: #f5f4f0`, `--paper: #fff`, `--paper2: #fafaf8`, `--ink: #1e1d1a`, `--ink2: #33403f`, `--muted: #6b6860`, `--line: #dbd9d3`, `--accent: #c96b5a`, `--teal: #439a9a`, `--teal-soft: #e1eeee`, `--blue: #4c78a8`, `--gold: #c4943a`, `--soft: #ecebe6`, `--shadow: none`, `--space-1: 4px`, `--space-2: 8px`, `--space-3: 12px`, `--space-4: 16px`, `--type-xs: 10px`, `--type-sm: 11px`, `--type-md: 12px`, `--type-lg: 16px`, `--type-xl: 22px`, `--modern-bg: #f7f9fc`, `--modern-panel: #fff`, `--modern-line: #e2e8ef`, `--modern-ink: #182431`
- **顏色**（57）：`#17241f`, `#71817a`, `#dbe6e0`, `#f4f8f5`, `rgba(255,255,255,.9)`, `#b84436`, `#257f70`, `#e3f3ed`, `rgba(28,58,46,.10)`, `#fff`, `#edf4ef`, `#bfe0d2`, `#effaf4`, `#277762`, `#38aa78`, `rgba(56,170,120,.12)`, `rgba(233,245,238,.84)`, `#9c342d`, `#e7bdb8`, `#fff8f7`, `rgba(32,64,50,.06)`, `#fbfdfc`, `#a97822`, `#405249`, `#9acdbb`, `#f6fbf8`, `#53655d`, `#f2faf6`, `#fbfcfb`, `#f8faf9`, `#f1f5f3`, `#edf3f0`, `rgba(32,64,50,.045)`, `#f5f4f0`, `#fafaf8`, `#1e1d1a`, `#33403f`, `#6b6860`, `#dbd9d3`, `#c96b5a`
- **字型**（6）：`Inter,ui-sans-serif,system-ui,-apple-system,"Noto Sans TC","Microsoft JhengHei",sans-serif`, `serif`, `ui-monospace,SFMono-Regular,Menlo,monospace`, `'DM Sans','Noto Sans TC',system-ui,sans-serif !important`, `'DM Mono',ui-monospace,monospace`, `'Cormorant Garamond','Noto Serif TC',serif`
- **字級**（19）：`24px`, `10px`, `20px`, `11px`, `28px`, `13px`, `12px`, `15px`, `14px`, `16px`, `23px`, `17px`, `8px`, `9px`, `22px`, `8.5px`, `10.5px`, `9.5px`, `7.5px`
- **間距**（70）：`0`, `24px 18px 42px`, `auto`, `18px`, `0 auto 20px`, `12px`, `5px 0 0`, `7px`, `7px 11px`, `24px 26px`, `16px`, `0 0 7px`, `9px`, `17px`, `9px 13px`, `5px 0 15px`, `10px`, `6px`, `12px 0`, `7px 9px`, `8px`, `5px`, `9px 10px`, `5px 7px`, `4px`, `8px 10px`, `14px 11px 28px`, `19px 17px`, `6px 8px`, `16px 14px 30px`, `3px`, `6px 9px`, `16px 18px`, `11px`, `7px 10px`, `13px`, `4px 0 10px`, `8px 0`, `7px 8px`, `4px 6px`
- **圓角**（13）：`9px`, `999px`, `50%`, `18px`, `15px`, `11px`, `8px`, `10px`, `7px`, `13px`, `0 !important`, `var(--ui-radius)`, `6px`
- **陰影**（7）：`0 0 0 4px rgba(56,170,120,.12)`, `var(--shadow)`, `0 10px 32px rgba(32,64,50,.06)`, `0 5px 16px rgba(32,64,50,.045)`, `none !important`, `0 2px 9px rgba(29,48,68,.04)`, `0 2px 9px rgba(29,48,68,.035)`
- **斷點**（3）：`900px`, `680px`, `430px`

## 3. 互動邏輯

### 3.x 事件（4）

- `L155` change — `const renderModules=()=>{const root=$('#moduleList');root.replaceChildren();if(!state.modules.length){root.innerHTML='<div class="module-empty">尚未建立管理模組，請使用上方表單`
- `L155` click — `const renderModules=()=>{const root=$('#moduleList');root.replaceChildren();if(!state.modules.length){root.innerHTML='<div class="module-empty">尚未建立管理模組，請使用上方表單`
- `L198` onload — `$('#importData').addEventListener('change',event=>{const file=event.target.files?.[0];if(!file)return;const reader=new FileReader();reader.onload=()=>{try{impor`
- `L201` storage — `window.addEventListener('storage',event=>{if(event.key===KEY&&event.newValue){try{const incoming=normalize(JSON.parse(event.newValue));if(shouldAccept(incoming)`

### 3.x 儲存（1）

- `L122` localStorage — `const canStore=(()=>{try{const k='__via_test__';localStorage.setItem(k,'1');localStorage.removeItem(k);return true}catch`

## 4. API / 函式規格

### 4.x 函式簽章（39）

| ID | 規格 | 來源 | 等級 |
|---|---|---|---|
| SPEC-API-FUNCTION-96DB253282D1 | `canStore(()` | VIA-SYNCHRONIZER-Standalone.html:L122 | V |
| SPEC-API-FUNCTION-B56CAA6CFD62 | `now()` | VIA-SYNCHRONIZER-Standalone.html:L133 | V |
| SPEC-API-FUNCTION-209D7517D451 | `log(message)` | VIA-SYNCHRONIZER-Standalone.html:L135 | V |
| SPEC-API-FUNCTION-2E851DAC317A | `makeHistory(definitions)` | VIA-SYNCHRONIZER-Standalone.html:L143 | V |
| SPEC-API-FUNCTION-C98D3114AF67 | `read()` | VIA-SYNCHRONIZER-Standalone.html:L151 | V |
| SPEC-API-FUNCTION-70631C6DC4B9 | `activeModules()` | VIA-SYNCHRONIZER-Standalone.html:L153 | V |
| SPEC-API-FUNCTION-2049FE9F276E | `renderStatus()` | VIA-SYNCHRONIZER-Standalone.html:L154 | V |
| SPEC-API-FUNCTION-45437A446EBA | `renderModules()` | VIA-SYNCHRONIZER-Standalone.html:L155 | V |
| SPEC-API-FUNCTION-D5821864EF41 | `renderTemplate()` | VIA-SYNCHRONIZER-Standalone.html:L156 | V |
| SPEC-API-FUNCTION-C492F268042A | `renderAnalytics()` | VIA-SYNCHRONIZER-Standalone.html:L157 | V |
| SPEC-API-FUNCTION-5DA8709F18CE | `applyTemplate()` | VIA-SYNCHRONIZER-Standalone.html:L158 | V |
| SPEC-API-FUNCTION-D87E06B4EAED | `addChart()` | VIA-SYNCHRONIZER-Standalone.html:L159 | V |
| SPEC-API-FUNCTION-5B9B6943AED2 | `applyPivot()` | VIA-SYNCHRONIZER-Standalone.html:L160 | V |
| SPEC-API-FUNCTION-FD6716B1011C | `pivotRows()` | VIA-SYNCHRONIZER-Standalone.html:L161 | V |
| SPEC-API-FUNCTION-C47FB5E56E18 | `templateBundle()` | VIA-SYNCHRONIZER-Standalone.html:L162 | V |
| SPEC-API-FUNCTION-B36D44BA2B98 | `reorder()` | VIA-SYNCHRONIZER-Standalone.html:L163 | V |
| SPEC-API-FUNCTION-372E92CECB3A | `moveModule(index,delta)` | VIA-SYNCHRONIZER-Standalone.html:L164 | V |
| SPEC-API-FUNCTION-C0B9C592E381 | `currentView()` | VIA-SYNCHRONIZER-Standalone.html:L165 | V |
| SPEC-API-FUNCTION-A81FC3FBBD54 | `applyScope(incoming,local)` | VIA-SYNCHRONIZER-Standalone.html:L166 | V |
| SPEC-API-FUNCTION-4F8161E89FA9 | `shouldAccept(incoming)` | VIA-SYNCHRONIZER-Standalone.html:L167 | V |
| SPEC-API-FUNCTION-A8913506D804 | `persist(broadcast=true,message='已更新本機同步狀態',bump=true)` | VIA-SYNCHRONIZER-Standalone.html:L168 | V |
| SPEC-API-FUNCTION-0E169568BDF2 | `commit(message,broadcast=true)` | VIA-SYNCHRONIZER-Standalone.html:L169 | V |
| SPEC-API-FUNCTION-DAE3A66EC85F | `applyIncoming(incoming)` | VIA-SYNCHRONIZER-Standalone.html:L170 | V |
| SPEC-API-FUNCTION-B3E9F0DCAD29 | `download(content,name,type)` | VIA-SYNCHRONIZER-Standalone.html:L171 | V |
| SPEC-API-FUNCTION-F43512DCBD77 | `modulesCsv()` | VIA-SYNCHRONIZER-Standalone.html:L174 | V |
| SPEC-API-FUNCTION-F146C80D7893 | `historyCsv()` | VIA-SYNCHRONIZER-Standalone.html:L175 | V |
| SPEC-API-FUNCTION-D8B33D28A302 | `chartsCsv()` | VIA-SYNCHRONIZER-Standalone.html:L176 | V |
| SPEC-API-FUNCTION-C1150BAA35E4 | `worksheet(name,headers,rows)` | VIA-SYNCHRONIZER-Standalone.html:L179 | V |
| SPEC-API-FUNCTION-10C5B32675D3 | `excelXml()` | VIA-SYNCHRONIZER-Standalone.html:L180 | V |
| SPEC-API-FUNCTION-1E55E5D91BBC | `exportJson()` | VIA-SYNCHRONIZER-Standalone.html:L181 | V |
| SPEC-API-FUNCTION-5BD56F4D89E6 | `exportCsv()` | VIA-SYNCHRONIZER-Standalone.html:L182 | V |
| SPEC-API-FUNCTION-5714DFAD94D0 | `exportExcel()` | VIA-SYNCHRONIZER-Standalone.html:L183 | V |
| SPEC-API-FUNCTION-1158C1C0A450 | `exportHistory()` | VIA-SYNCHRONIZER-Standalone.html:L184 | V |
| SPEC-API-FUNCTION-FE583DDCC85C | `exportCharts()` | VIA-SYNCHRONIZER-Standalone.html:L185 | V |
| SPEC-API-FUNCTION-6068945E6BAD | `importText(text,filename)` | VIA-SYNCHRONIZER-Standalone.html:L190 | V |
| SPEC-API-FUNCTION-9C2FFA0FB2A6 | `applyRules()` | VIA-SYNCHRONIZER-Standalone.html:L191 | V |
| SPEC-API-FUNCTION-22A38CE41312 | `applyLayoutCss()` | VIA-SYNCHRONIZER-Standalone.html:L192 | V |
| SPEC-API-FUNCTION-308A6ACF2BE7 | `applyLayout()` | VIA-SYNCHRONIZER-Standalone.html:L193 | V |
| SPEC-API-FUNCTION-DFA256A940A6 | `applyView()` | VIA-SYNCHRONIZER-Standalone.html:L194 | V |

## 5. 資料規格

## 6. 業務規則

### MUST（1）

- **SPEC-RULE-MUST-C32F30FB0A23** Excel 匯出為可用 Excel 開啟的 SpreadsheetML `.xls`，不需外部套件。  ⟨VIA-SYNCHRONIZER-Standalone.html:L100⟩

## 7. 內容模型

- 標題 11 · 段落 11 · 清單/任務/步驟 0 · 程式碼區塊 0 · 連結 2 · 圖片 0

- SYNCHRONIZER  ⟨VIA-SYNCHRONIZER-Standalone.html:L90⟩
  - 本機智慧銜接同步器  ⟨VIA-SYNCHRONIZER-Standalone.html:L91⟩
    - 同步通道狀態  ⟨VIA-SYNCHRONIZER-Standalone.html:L93⟩
    - 同步規則  ⟨VIA-SYNCHRONIZER-Standalone.html:L94⟩
    - 產業管理模組範本  ⟨VIA-SYNCHRONIZER-Standalone.html:L95⟩
    - 自定義圖表與歷史趨勢  ⟨VIA-SYNCHRONIZER-Standalone.html:L96⟩
    - 自定義管理模組  ⟨VIA-SYNCHRONIZER-Standalone.html:L98⟩
    - 視圖同步設定  ⟨VIA-SYNCHRONIZER-Standalone.html:L99⟩
    - 資料交換格式  ⟨VIA-SYNCHRONIZER-Standalone.html:L100⟩
    - JSON 狀態預覽  ⟨VIA-SYNCHRONIZER-Standalone.html:L101⟩
    - 操作紀錄  ⟨VIA-SYNCHRONIZER-Standalone.html:L102⟩

## 8. 缺口（Gap）

| ID | 類型 | 說明 | 等級 | 來源 |
|---|---|---|---|---|
| SPEC-GAP-COMPONEN-0F0AA1E3EF8B | component_no_behavior | button#syncNow <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#syncNow |
| SPEC-GAP-COMPONEN-C25C33574672 | component_no_behavior | button#exportJson <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportJson |
| SPEC-GAP-COMPONEN-7BCFAF162C61 | component_no_behavior | button#exportCsv <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportCsv |
| SPEC-GAP-COMPONEN-179D31D7D071 | component_no_behavior | button#exportHistory <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportHistory |
| SPEC-GAP-COMPONEN-5BB346922EE4 | component_no_behavior | button#exportExcel <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportExcel |
| SPEC-GAP-FIELD_NO-245261113D71 | field_no_label | 欄位 storageCheck 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:input#storageCheck |
| SPEC-GAP-FIELD_NO-D16FB8689BE1 | field_no_label | 欄位 channelCheck 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:input#channelCheck |
| SPEC-GAP-COMPONEN-60EDBB517791 | component_no_behavior | select#syncScope <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#syncScope |
| SPEC-GAP-FIELD_NO-93CA851D35BF | field_no_label | 欄位 syncScope 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#syncScope |
| SPEC-GAP-COMPONEN-C1DE3428A9EB | component_no_behavior | select#conflictRule <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#conflictRule |
| SPEC-GAP-FIELD_NO-CE6AA281FECB | field_no_label | 欄位 conflictRule 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#conflictRule |
| SPEC-GAP-FIELD_NO-213993219B29 | field_no_label | 欄位 debounceMs 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:input#debounceMs |
| SPEC-GAP-COMPONEN-B5BA1526E01C | component_no_behavior | button#applyRules <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#applyRules |
| SPEC-GAP-COMPONEN-B55CAAD5395E | component_no_behavior | select#templateSelect <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#templateSelect |
| SPEC-GAP-FIELD_NO-08F519EBC8A9 | field_no_label | 欄位 templateSelect 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#templateSelect |
| SPEC-GAP-COMPONEN-2333007D55C7 | component_no_behavior | select#templateMode <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#templateMode |
| SPEC-GAP-FIELD_NO-1D57320FE8EC | field_no_label | 欄位 templateMode 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#templateMode |
| SPEC-GAP-COMPONEN-BBD5B7B54F95 | component_no_behavior | button#applyTemplate <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#applyTemplate |
| SPEC-GAP-COMPONEN-465CFD850205 | component_no_behavior | button#exportTemplate <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportTemplate |
| SPEC-GAP-FIELD_NO-BE429B2F1948 | field_no_validation | 欄位 chartId 無任何驗證(required/pattern/min/max) | V | VIA-SYNCHRONIZER-Standalone.html:input#chartId |
| SPEC-GAP-FIELD_NO-0ADA6A944F2E | field_no_validation | 欄位 chartName 無任何驗證(required/pattern/min/max) | V | VIA-SYNCHRONIZER-Standalone.html:input#chartName |
| SPEC-GAP-COMPONEN-F70D9169BD5E | component_no_behavior | select#chartType <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#chartType |
| SPEC-GAP-FIELD_NO-8E256A6F77EB | field_no_label | 欄位 chartType 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#chartType |
| SPEC-GAP-FIELD_NO-5DC8755F84CE | field_no_validation | 欄位 chartMetric 無任何驗證(required/pattern/min/max) | V | VIA-SYNCHRONIZER-Standalone.html:input#chartMetric |
| SPEC-GAP-COMPONEN-BB9703BC970F | component_no_behavior | button#addChart <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#addChart |
| SPEC-GAP-COMPONEN-554F4A1C4408 | component_no_behavior | select#pivotRow <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#pivotRow |
| SPEC-GAP-FIELD_NO-BC62BB9371B8 | field_no_label | 欄位 pivotRow 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#pivotRow |
| SPEC-GAP-COMPONEN-613E3AA344D7 | component_no_behavior | select#pivotColumn <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#pivotColumn |
| SPEC-GAP-FIELD_NO-F81BAF6F1AA6 | field_no_label | 欄位 pivotColumn 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#pivotColumn |
| SPEC-GAP-COMPONEN-1B80FFA40C24 | component_no_behavior | select#pivotValue <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#pivotValue |
| SPEC-GAP-FIELD_NO-BE7EA80F2F73 | field_no_label | 欄位 pivotValue 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#pivotValue |
| SPEC-GAP-COMPONEN-A5F92942DC0D | component_no_behavior | select#pivotAgg <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#pivotAgg |
| SPEC-GAP-FIELD_NO-BFBAE986D3E0 | field_no_label | 欄位 pivotAgg 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#pivotAgg |
| SPEC-GAP-COMPONEN-3E2654170424 | component_no_behavior | button#applyPivot <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#applyPivot |
| SPEC-GAP-FIELD_NO-08E769FDF862 | field_no_validation | 欄位 moduleId 無任何驗證(required/pattern/min/max) | V | VIA-SYNCHRONIZER-Standalone.html:input#moduleId |
| SPEC-GAP-FIELD_NO-F231EF832E04 | field_no_validation | 欄位 moduleName 無任何驗證(required/pattern/min/max) | V | VIA-SYNCHRONIZER-Standalone.html:input#moduleName |
| SPEC-GAP-COMPONEN-3E3E3B4B99EA | component_no_behavior | select#moduleType <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#moduleType |
| SPEC-GAP-FIELD_NO-2E311A884A1F | field_no_label | 欄位 moduleType 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:select#moduleType |
| SPEC-GAP-FIELD_NO-5177E84F9CDB | field_no_label | 欄位 modulePinned 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:input#modulePinned |
| SPEC-GAP-COMPONEN-9FC86E33BD42 | component_no_behavior | button#addModule <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#addModule |
| SPEC-GAP-COMPONEN-B9A9B6631A2E | component_no_behavior | select#density <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#density |
| SPEC-GAP-COMPONEN-FEC6A90401DC | component_no_behavior | select#theme <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#theme |
| SPEC-GAP-FIELD_NO-C93ACBE684EE | field_no_label | 欄位 motion 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:input#motion |
| SPEC-GAP-FIELD_NO-969F22D2B62D | field_no_label | 欄位 hints 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:input#hints |
| SPEC-GAP-FIELD_NO-5C9EDADC1F04 | field_no_label | 欄位 live 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:input#live |
| SPEC-GAP-FIELD_NO-4C2CA4534667 | field_no_label | 欄位 autoApply 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:input#autoApply |
| SPEC-GAP-COMPONEN-BD837C10926D | component_no_behavior | button#applyView <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#applyView |
| SPEC-GAP-COMPONEN-96847501A91F | component_no_behavior | select#fontScale <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#fontScale |
| SPEC-GAP-FIELD_NO-C7E2035396BC | field_no_label | 欄位 equalPanels 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:input#equalPanels |
| SPEC-GAP-COMPONEN-14728BB80CAC | component_no_behavior | select#surface <select> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:select#surface |
| SPEC-GAP-RULE_NO_-DE7F16117125 | rule_no_condition | 規則缺觸發條件/門檻: Excel 匯出為可用 Excel 開啟的 SpreadsheetML `.xls`，不需外部套件。 | M | VIA-SYNCHRONIZER-Standalone.html:L100 |
| SPEC-GAP-COMPONEN-755720C04767 | component_no_behavior | button#exportJson2 <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportJson2 |
| SPEC-GAP-COMPONEN-C18A32CBE4EA | component_no_behavior | button#exportCsv2 <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportCsv2 |
| SPEC-GAP-COMPONEN-3752BE3245AF | component_no_behavior | button#exportHistory2 <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportHistory2 |
| SPEC-GAP-COMPONEN-569FF42175F0 | component_no_behavior | button#exportCharts <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportCharts |
| SPEC-GAP-COMPONEN-E2F25E24E6BF | component_no_behavior | button#exportExcel2 <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#exportExcel2 |
| SPEC-GAP-FIELD_NO-97C5484B0477 | field_no_label | 欄位 jsonPreview 無 label/placeholder/aria-label | V | VIA-SYNCHRONIZER-Standalone.html:textarea#jsonPreview |
| SPEC-GAP-FIELD_NO-5AE9EB21F030 | field_no_validation | 欄位 jsonPreview 無任何驗證(required/pattern/min/max) | V | VIA-SYNCHRONIZER-Standalone.html:textarea#jsonPreview |
| SPEC-GAP-COMPONEN-2C540DE0B214 | component_no_behavior | button#loadState <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#loadState |
| SPEC-GAP-COMPONEN-7B2AA286D427 | component_no_behavior | button#clearState <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | VIA-SYNCHRONIZER-Standalone.html:button#clearState |
