# VIS Workbench · 末日級擷取引擎（格式無關 + 完整性保證）

_處理 word/excel/text/csv/image 內部未知內容，回答五問並吐 JSON 給下一階段（指令解取）。stdlib 優先、永不崩、抓不到必有原因。已測試（40/40）。_

---

## 設計原則

- **stdlib 優先**：docx/xlsx 用 `zipfile`+XML 自解，**不依賴 python-docx/openpyxl**——你的 Windows 不裝任何庫也能跑。
- **永不崩**：任何檔壞掉只記原因、不中斷（末日情境）。
- **抓不到必有原因**：每個未擷取單元都歸因（結構性/可回收/錯誤），這是「保證全抓」的基礎。
- **誠實**：圖片無 OCR 時標 `needs-OCR`，**不假裝抓到**。

---

## 五問，逐一回答

### 1. 你能保證資料全抓了嗎？（指標計算）
每個檔逐單元稽核，算出：
```
覆蓋率 = 擷取 / 看到
未解釋遺漏 unexplained_gap = 看到 − 擷取 − 已歸因失敗
保證 PASS ⇔ unexplained_gap = 0
```
**實測**：6 檔共 20 單元、擷取 15、覆蓋 75%；未擷取的 5 個全有原因（4 結構性空段落/空格/空列 + 1 圖片 needs-OCR）→ **unexplained_gap=0 → 保證全抓 PASS**。75% 不是漏抓，是那 25% 本來就空或需 OCR，且**每一項都指名道姓**。

### 2. 各型別校正驗證
mojibake 修復 + 編碼偵測（chardet／多編碼回退）+ CSV 分隔嗅探 + 空白正規化。修完**驗證無資料流失**（有字不得變空）→ `verify_pass`。

### 3. 無遺漏去重
完整性 gate 確認無遺漏；`content_hash` 去重。**實測**：15→14，抓到 1 筆跨檔重複。

### 4. 有意義分類再分類
`auto_ssot` 自舉桶＋多道分類；**可注入行業骨架**（電子＋散熱 38 品類）→ 元件描述行歸到正確品類，其餘誠實留未分類。

### 5. 重點摘要
抽取式：高鑑別關鍵詞 + 關鍵句（含 需/請/截止/風險/變更/客戶/交期 或日期數字）。**實測**撈出：客戶交期提前、GaN 單一供應源、改銅質散熱片、客戶電話要求降溫。

---

## 支援格式與擷取法

| 格式 | 擷取法 | 未擷取歸因 |
|------|--------|-----------|
| **docx** | zip→word/document.xml→段落/表格 | 空段落=結構性；內嵌圖=needs-OCR |
| **xlsx** | zip→sharedStrings+sheet XML→非空 cell | 空格=結構性 |
| **csv** | 分隔嗅探+編碼偵測 | 空列=結構性 |
| **text** | 編碼偵測+mojibake 修復 | 空行=結構性 |
| **image** | magic bytes 辨識 | needs-OCR=可回收（誠實標記） |
| 其他/壞檔 | — | 記原因不中斷 |

---

## 輸出：parameters + data in JSON

```json
{
  "parameters": { "files": N, "guarantee": {...指標}, "correction": {...},
                  "dedup": {...}, "classification": {...} },
  "completeness": { "unexplained_gap": 0, "guarantee_pass": true },
  "data": [ {"text": "...", "kind": "line", "ref": "L3", "hash": "...", "class": "..."} ],
  "summary": { "key_terms": [...], "key_points": [...] }
}
```

`parameters` = 指標與組態；`data` = 去重校正後的內容單元。**這份 JSON 就是下一階段「檔案內文/郵件內文指令解取」的輸入。**

---

## 郵件自動搜尋（接上既有能力）

Gmail/Outlook 全信箱自動讀已由 `fetch_mailbox.py` + `mail_chain`（Outlook COM→OAuth→IMAP 回退）處理；抓下的郵件同樣進本引擎走「保證全抓→校正→去重→分類→摘要」。

---

## 交付

- `ingest_engine.py`：末日擷取引擎（偵測/擷取/保證/校正/去重/分類/摘要/JSON）。
- `ingest_result.json`：實測輸出範例。

_下一步（你已預告）：以這份 JSON 為輸入，做「檔案內文＋郵件內文的指令解取 → 有效工作控管」。_
