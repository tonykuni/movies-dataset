# PMIS-Lite 韌性設計：30 失敗模式 × 內建多元備援 × 2026 函式庫選型

_目標：把「單點掛掉就整個失敗」降成「所有備援都掛才失敗」。每個失敗模式都預留多元解決方案，內建於工具。_

---

## 一、核心韌性機制：備援鏈（已內建 `resilience.py`）

每個關鍵能力都不押注單一作法，而是排一串策略**依序自動嘗試**，第一個成功的就用，並記錄走到第幾條、前面為何失敗。

```
讀 MS Project = [另存XML] → [COM自動化] → [mpxj直讀]
讀 郵件       = [Outlook COM] → [libpff 讀 OST/PST] → [IMAP]
OCR          = [Tesseract] → [RapidOCR] → [PaddleOCR]
編碼偵測      = [BOM 判斷] → [charset-normalizer] → [常見編碼實測回退]
分類          = [關鍵字] → [討論串傳播] → [模糊指派]
```

---

## 二、30 個失敗模式與內建備援（FMEA）

### A. 連線 / 擷取（1–6）

| # | 失敗模式 | 內建備援 |
|---|---------|---------|
| 1 | Outlook COM 不可用（未安裝/非 Windows） | 改讀 OST/PST 檔（libpff）→ 再不行走 IMAP |
| 2 | Gmail OAuth 授權過期/被撤 | 自動偵測 401 → 引導重新授權；暫存上次結果不中斷 |
| 3 | IMAP 連線逾時/被防火牆擋 | 重試退避（backoff）3 次 → 改用已下載的本機快取 |
| 4 | 公司租戶停用程式化存取 | 退回「只讀本機快取信箱/匯出檔」路徑，不碰伺服器 |
| 5 | MS Project 未安裝（COM 失敗） | 另存 XML 路徑 → mpxj 直讀 .mpp |
| 6 | PLM 無 API / 廠牌不同 | 改吃使用者有權限的匯出檔（CSV/Excel）+ 欄位對應 |

### B. 編碼 / 文字（7–11）

| # | 失敗模式 | 內建備援 |
|---|---------|---------|
| 7 | 亂碼（big5/cp950/utf-8 混雜） | BOM 判斷 → charset-normalizer → 常見編碼逐一實測回退 |
| 8 | 雙重解碼亂碼（mojibake） | 修復後比對 CJK 字數，變多才採用，否則保留原文 |
| 9 | 全形/半形、簡繁混用 | OpenCC 正規化 + 全半形統一 |
| 10 | 信件含巨量引用尾巴/簽名 | 只切「明確尾巴」，主體一字不刪，並記錄刪了什麼 |
| 11 | 超長內文撐爆記憶體 | 串流分段處理 + 字元上限截斷（保留前段） |

### C. 解析 / 格式（12–18）

| # | 失敗模式 | 內建備援 |
|---|---------|---------|
| 12 | 掃描型 PDF（無文字層） | OCR 救回：Tesseract → RapidOCR → PaddleOCR |
| 13 | PDF 解析失敗（壞檔/加密） | pdfplumber → PyMuPDF 換引擎 → 標記可救回 |
| 14 | 不支援的附件類型（.dat 等） | 誠實標記 unsupported + 建議轉存；不偽裝成功 |
| 15 | Excel 合併儲存格/多表/公式值 | 讀全部工作表 + data_only 取計算值 + 整列保底當標題 |
| 16 | CSV 分隔符/引號錯亂（中文括號） | 自動嗅探分隔符 + 逐欄解析 |
| 17 | .msg/.eml 內嵌附件 | extract-msg / email 標準庫拆解，遞迴擷取 |
| 18 | MS Project 摘要任務（無名稱） | 視為結構性略過（不算漏），非失敗 |

### D. 分類 / 關鍵字（19–24）

| # | 失敗模式 | 內建備援 |
|---|---------|---------|
| 19 | 行話/簡寫系統不認得 | 從資料自動生成關鍵字候選 → 核可 → 詞庫自長 |
| 20 | 關鍵字過度合併污染 SSOT | 只提議不自動合併；停用單位/角色縮寫；專一性懲罰 |
| 21 | 歸類率太低（未分類過多） | 三道遞進：關鍵字→討論串傳播→模糊指派 |
| 22 | 分類桶不存在（新公司零設定） | 從來源欄位值自動長出分類桶（標籤即關鍵字） |
| 23 | 模糊指派亂分 | 需超門檻且領先第二名 1.3 倍才分，否則留未分類 |
| 24 | 繁中斷詞不準（jieba 偏簡中） | 改用 CKIP（繁中專用）；TF-IDF/TextRank 抽關鍵字 |

### E. 完整性 / 資料（25–28）

| # | 失敗模式 | 內建備援 |
|---|---------|---------|
| 25 | 漏抓資料卻不自知 | 完整性 gate：可見−擷取−已記錄失敗=未解釋遺漏，>0 即 FAIL |
| 26 | 同一件事重複計算 | 內容雜湊去重 + 穩定身分編號 |
| 27 | 同案內容變了看不出 | 身分碼穩定、變動指紋另算 → 標示「變更」非「新增」 |
| 28 | 並發/重跑覆蓋資料 | append-only + 每次快照（snapshot），可回溯 |

### F. 環境 / 部署（門外漢）/ 合規（29–30）

| # | 失敗模式 | 內建備援 |
|---|---------|---------|
| 29 | 缺 Python/套件、不會裝 | 一鍵 .bat 自動裝（使用者範圍，免管理員）；出錯開說明頁不崩潰；未來打包 .exe 免裝 Python |
| 30 | 誤讀無權限資料/違反 AUP | 僅用使用者自有認證與權限；啟動印 AUP 提醒；全本機不外傳；只記工作事實不側寫個人 |

---

## 三、15 個 2026 最佳本機免費函式庫（全部功能對應）

| # | 函式庫 | 角色 | 為何選它（2026） | 授權 |
|---|--------|------|-----------------|------|
| 1 | **mpxj 16.2** | 讀 MS Project .mpp（及 P6/XER 等） | 業界最完整、跨格式；JPype 橋接 Python（需 Java） | LGPL |
| 2 | **pywin32 (win32com)** | Outlook/MS Project 即時 COM | 用你已登入的程式讀，權限與你一致 | PSF |
| 3 | **libpff / libratom** | 讀 OST/PST 離線信箱 | 不需開 Outlook 即可解析 PFF/OFF | LGPL/Apache |
| 4 | **extract-msg** | 解析 .msg 郵件 | 單封 .msg + 內嵌附件拆解 | GPL/BSD |
| 5 | **google-api-python-client + google-auth-oauthlib** | Gmail readonly | 官方 API + OAuth 唯讀，個人帳號可控 | Apache |
| 6 | **Tesseract 5.5 (pytesseract)** | OCR 輕量 | ~10MB、CPU 快、易部署，門外漢首選 | Apache |
| 7 | **RapidOCR** | OCR（ONNX，CJK） | PaddleOCR 模型跑 ONNX、~80MB 無 Paddle 依賴、低資源最佳 | Apache |
| 8 | **PaddleOCR (PP-OCRv5 / PP-Structure)** | OCR（繁中+表格） | 強 CJK + 版面/表格抽取，重檔可救 | Apache |
| 9 | **pdfplumber + PyMuPDF** | PDF 文字/表格 | 雙引擎互為備援，pdfplumber 表格、PyMuPDF 速度 | MIT/AGPL |
| 10 | **python-docx / python-pptx / openpyxl** | Office 文件 | docx/pptx/xlsx 讀寫標準三件套 | MIT |
| 11 | **CKIP Transformers** | 繁中斷詞/POS/NER | 中研院出品，繁體中文準度勝 jieba | GPL |
| 12 | **jieba** | 中文斷詞 + 關鍵字 | 快、含 TF-IDF/TextRank 抽詞、可自訂詞典 | MIT |
| 13 | **rapidfuzz** | 模糊字串比對 | 高速 Levenshtein，去重/同義/錯字歸位 | MIT |
| 14 | **charset-normalizer**（含 chardet 備援） | 編碼偵測 | 治亂碼首選，比 chardet 更穩 | MIT |
| 15 | **DuckDB + Polars + PyArrow** | 本機資料庫/增量 | Parquet 增量、查詢快、零伺服器 | MIT/Apache |

**輔助（加分）**：OpenCC（繁簡轉換對齊）、symspellpy（拼字/模糊校正）、pdf2image+poppler（PDF 轉圖供 OCR）、winloop（Windows 非同步）。

---

## 四、2026 最佳實務（與本工具設計一致）

1. **本機優先 / 氣隙處理**：敏感資料不出機器，自我掌控，免 IT 開通——這是 2026 知識工作工具的主流共識。
2. **備援鏈 / 優雅降級**：關鍵能力都備援，單點失效不致命。
3. **OCR 分層**：CPU/門外漢用 Tesseract/RapidOCR；要表格/繁中準度才上 PaddleOCR；VLM-OCR（Qwen2.5-VL 等）效果好但吃 GPU，非門外漢預設。
4. **人在迴圈核准**：關鍵字/同義字只提議不自動套用，避免污染擴散。
5. **完整性 gate**：區分「結構性略過 / 可救回 / 真錯誤」，涵蓋率才誠實。
6. **DuckDB + Parquet 增量倉**：本機、快、零伺服器，append-only 可回溯。
7. **OAuth 唯讀 / COM 自有 session**：以使用者自身權限存取，合規清楚。

---

## 五、Gmail 等信箱「自動連結」泛用設計

- **個人 Gmail**：google-api-python-client + OAuth `readonly`，一次授權後自動連；或 IMAP + app password。
- **Outlook（公司/個人）**：win32com 用你已登入的 session；離線檔 libpff 讀 OST/PST。
- **泛用關鍵**：信箱來源都實作同一個 adapter 介面（回傳統一 Record），核心引擎不變；新信箱=多一個 adapter，備援鏈讓任一條路通就好。
- **自動連結降低失敗**：連線走備援鏈（COM→libpff→IMAP），授權失效自動偵測並引導重連，期間用本機快取不中斷。
