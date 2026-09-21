# VIA SSOT 唯讀盤點與增量補充

**最新增補 v0.2.0：**已加入官方代碼查名、檔名／首頁核對、版面修復、首頁四點摘要與年度財務核驗契約，詳見 `VRN_WORKFLOW_SPEC.md`。新增 64 筆帶來源的字詞記錄與 `VRN_Evidence_Core.py`；原 30 項檢查與新增 48 項合成測試通過。下列內容保留為初版盤點，197 筆與 24 筆等數字指初版輸入比較，不代表新版字庫總量。

已依「有差異的也列入同義字」收錄：原字詞、原分類及各來源對應都保留，不以最後讀到的值覆蓋先前資料。GitHub 倉庫未修改；本包是獨立的補充字库與診斷工具，尚未接入現役引擎。

基準：`tonykuni/movies-dataset`，commit `8e8e766f2c3d3aa42e89b78d643869faeb094cb4`，讀取日 2026-09-21。以機構主檔、欄位規則冊、券商冊和 SUP_MDL749 v0110 為主要依據；保留相關舊冊作為歷史證據。倉庫總樹回應截斷、registry 目錄 API 列表達 1,000 筆上限，因此改為直接取得已知主檔；這是指定來源的盤點，不能解讀成「全倉再無其他同義字」。

## 差異也納入的方式

`SYNONYM_LIBRARY.json` 的每個字詞保留多筆來源記錄。`resolve_synonym()` 指定來源時取該來源的對應；未指定來源且有不同分類時，回傳全部候選及 `SOURCE_REQUIRED`，不擅自改判。

| 字詞／鍵 | 原有或輸入差異 | 本次處理 |
|---|---|---|
| BOA、BOFA | 輸入鍵／機構主檔鍵不同 | 保留 BOA，對照 BOFA；不另建一家券商 |
| MCQ、MQ、MACQUARIE | 輸入鍵、檔名別名、機構鍵不同 | 同義字保留，對照 MACQUARIE |
| JP、JPM、JPMorgan | 券商冊與機構冊鍵不同 | 沿用來源對照，無需猜測 |
| CLST、CLSA | 券商冊已記錄操作員裁定合併 | 收錄兩個拼法，對照 CLSA |
| Strong Buy、強力買進、積極買進、Conviction Buy | STRONG_BUY／BUY | 差異全部保留，依來源尺度解析 |
| Accumulate、Add | BUY／ADD | 兩種對應均保留，避免無來源時強行單值化 |
| Strong Sell、強力賣出 | STRONG_SELL／SELL | 差異全部保留 |
| Base Case、Bull Case、Bear Case | 使用者放在目標價別名 | 保留目標價關聯，另存情境欄；必須有價格語境才能取數值 |
| GFHK | 在已檢視主檔找不到完整別名 | 字詞收錄為未核實，GF 只列建議對應；不以 GF 前綴直接定案 |

原先提供的 197 筆別名比較項目中：163 筆對應已存在、7 筆與來源分類有差異、24 筆在本次比對來源的別名索引未見、3 筆為情境詞。**全部已收錄**。NFKC、大小寫與空白正規化用於查重，原始拼法另存，故 `買進(初次)` 與 `買進（初次）` 不重複造義；`TARGET PRICE` 仍保留原文。

24 筆補充如下，完整來源對照見 `ALIAS_COMPARISON.json`：

| 分類 | 補充字詞 |
|---|---|
| STRONG_BUY | SB、買進(強烈)、買進(強力) |
| BUY | OP、OW、買進(維持)、買進(調升)、買進(重申) |
| HOLD | N、MP、EW、維持中立、中立(調降)、中立(調升) |
| SELL | UP、UW、賣出(調降)、賣出(重申) |
| STRONG_SELL | SS、積極賣出 |
| NOT_RATED | 未覆蓋、未納入研究範圍、CD、停止覆蓋 |

短字母必須出現在評等欄或有明確線索的結構中。調升、調降、維持、重申屬動作；NR、停止覆蓋、受限的覆蓋狀態也應另留原文。字庫收錄不代表任意正文命中都可當作評等。`Note` 是報告標籤，不自動變成未評等。範例中的 CTBC `B_買進`、`OW_增加持股` 另用受限的檔名模式保存。

## 實際重現的規則缺口

| 項目 | 基準結果 | 補充方式 |
|---|---|---|
| `2025.Q1` | 季度解析回空值 | 增加 `TW_YEAR_QUARTER_DOT_REGEX` |
| `3Q26` | 已解析為 2026-Q3 | 保留既有規則，無需重複新增 |
| `20250230` | 日期函式回傳不存在的 2025-02-30 | 增加日曆驗證，拒絕不可能日期 |
| `CTBC0915`／`CTBC0916` | 無完整年月日 | 留月日及 YEAR_MISSING，不補當年度 |
| `2330\tTT` | 基準平台 regex 接受 Tab | 增加嚴格單一半形空格的驗證式；舊式不刪 |
| `3014TT` | 基準接受緊接 TT | 保留檔名輸入相容；標準輸出另正規化為 `3014 TT` |
| ETF 外幣分類 | 原表欠 C、K、M、S，U/V 未區分 | 新命名空間補齊分類；原表留存 |

ETF 尾码依[證交所編碼原則第十三款](https://twse-regulation.twse.com.tw/TW/law/DAT0201.aspx?FLCODE=FL033103)核對：A／D、B／C、L／M、R／S、U／V 及 K、T。新表有 14 個格式分類、3 個平台，加 ETF 與 SECURITY 通用式，共 **48 個命名**，採 `TW_STOCK_REGEX`、`TW_YFINANCE_STOCK_REGEX`、`TW_BLOOMBERG_STOCK_REGEX` 等命名。英文字母按第六碼處理，未加入缺乏依據的內嵌字母位置。

保留既有 `00` 前綴及被動 ETF 四至六碼的範圍。這是一般個股與 ETF 的格式候選，不涵蓋特別股、權證、ETN 等所有證券；是否存在、Yahoo 是否收錄及應使用 TW/TWO，仍須查證券主檔。L/R 等碼也不能單獨判定底層資產。正則使用 ASCII 數字及嚴格結尾；其驗證更嚴，故與原式並存，未改現役接受範圍。

## 106 個檔名的測試結果

| 欄位 | 有候選值的檔案數 |
|---|---:|
| 券商 | 99 |
| 完整日期 | 97 |
| 個股代碼 | 58 |
| 明確結構中的評等 | 6 |

其餘日期為 7 筆無完整日期、2 筆缺年。這些是獨立診斷器的候選擷取數，**不是現役引擎準確率**；總經、產業、晨報等檔名沒有個股代碼並不自動代表錯誤。

`凱基投顧_2891 中信金_…` 中的中信金已按標的公司位置排除，不誤認為報告券商。`926708.jpg` 不判成日期或代碼。逐檔結果見 `FILENAME_RESULTS.html` 與 JSON。

**未取得 `C:\測試樣本報告\` 的實際檔案。**本次沒有讀取 PDF／DOCX／TXT／JPG 內容，也沒有核驗首頁、本文、分析師、目標價、三平台代碼一致性；所有結果保留 `NOT_RUN_NO_FILE_BYTES`。使用者提供的 `[cite: 3]` 無法定位來源，不作已查證引文。

## 保留的衝突與後續接線位置

跨來源評等索引有 9 個多分類字詞，詳見 `CROSS_REGISTRY_CONFLICTS.json`。其中既有冊可能採粗分類，機構主檔採六分類，不能只靠集合聯集得到唯一評等。歷史券商 knowledge 冊另有把 MS/JPM、國泰／國泰君安等混列的內容；歷史原文留在基準快照，不據此改寫機構身份。

欄位冊也有優先權文字差異：`rules.broker.evidence_tiers` 把電郵網域列弱證據，但 `rules.contact.cross_check` 與 `rules.source_priority.exception` 說網域優先。此次照原文留存；沒有取得報告內容，不能判定現役路徑究竟採何者。

上游增加字詞時保留來源鍵；中間層由既有 SUP_MDL749 統一讀冊；下游 ENG086、ENG073、TW02、首頁引擎應消費同一版本與來源資訊。此包沒有另改它們，也沒有繞過券商相容性 gate。`ADDITIVE_CANDIDATE.json` 是可檢閱的增量接口，不是自動安裝程式。

## 檔案與重跑

- `SYNONYM_LIBRARY.json`：含差異的來源分層同義字庫。
- `ADDITIVE_CANDIDATE.json`：增量項目、48 個命名 regex、適用條件。
- `ticker_regexes.py`／`ticker_schema.json`：同一份命名規則的 Python 與 JSON Schema 輸出。
- `ALIAS_COMPARISON.json`／`CROSS_REGISTRY_CONFLICTS.json`：逐詞差異與衝突證據。
- `FILENAME_RESULTS.html`／`.json`：106 筆檔名測試。
- `BASELINE_PROBES.json`／`AUDIT_SUMMARY.json`：基準重現結果、30 項測試結果。
- `baseline_manifest.json`／`baseline/`：來源路徑、Git blob SHA 與唯讀取回的相關快照。

需要 Python 3.10 以上，無第三方依賴。在解壓目錄執行：

```bash
python audit_ssot.py
```

程式只重建本包的輸出檔，不連網、不讀 Windows 報告、不修改倉庫。基準函式只經 AST 取出三個已檢視函式，沒有匯入或啟動整套引擎。30/30 檢查通過，含基準快照不變、所有輸入別名保留、差異不被覆蓋及負向樣例。

主要證據：[機構 SSOT](https://github.com/tonykuni/movies-dataset/blob/8e8e766f2c3d3aa42e89b78d643869faeb094cb4/VeritasIntelligenceAnalytics/supportive%20modules/ssot/VIA_Financial_Institution_SSOT_v0100.json)、[欄位規則 SSOT](https://github.com/tonykuni/movies-dataset/blob/8e8e766f2c3d3aa42e89b78d643869faeb094cb4/VeritasIntelligenceAnalytics/supportive%20modules/registry/VRN_FieldRules_SSOT_v0100.json)、[券商冊](https://github.com/tonykuni/movies-dataset/blob/8e8e766f2c3d3aa42e89b78d643869faeb094cb4/VeritasIntelligenceAnalytics/functional%20modules/VRN/registry/VRN_BROKER_LIST_v01.json)、[SUP_MDL749 v0110](https://github.com/tonykuni/movies-dataset/blob/8e8e766f2c3d3aa42e89b78d643869faeb094cb4/VeritasIntelligenceAnalytics/supportive%20modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0110.py)。
