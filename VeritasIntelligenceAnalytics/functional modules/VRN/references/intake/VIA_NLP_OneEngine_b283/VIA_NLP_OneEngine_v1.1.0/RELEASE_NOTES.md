# VIA NLP One Engine v1.1.0

發布日期：2026/08/27

## 本版成果

- CPU Sparse Hierarchical Topic Reconstruction：跨多段跳題後可回接同一主題，並建立 Topic Episodes。
- 來源與完善稿雙帳本：原文、offset、SHA-256、refinement、語意角色與修改紀錄全程可追溯。
- Mind Map 2.0：human tree + AI typed graph，包含 topic／episode／segment nodes 與切換、復返、來源關係。
- Engine Blueprint 2.0：函式參數與回傳介面、呼叫關係、外部依賴、拓撲順序、循環與人工啟用閘門。
- ML 演化升級：資料去重、同文異標拒絕、分層驗證、SGD champion 與兩層 Tiny MLP CPU challenger。
- 可選 Deep Semantic Enrichment：僅在明確啟用 Tier 3 時載入本機 Embedding，不保存原始向量。
- 自動 candidate evaluation 可按回饋筆數觸發；自動 promotion 仍維持關閉。

- 將原先以會議紀錄為中心的修復概念提升為「任何文章／任何文字」通用引擎。
- 四級 Task Router、Lazy Model Pool、RAM／CPU Watchdog、OOM admission gate。
- 通用 repair／analyze／structure／keywords／entities／summarize／classify 任務。
- 可選 spaCy、Sentence Transformers、ONNX Runtime、Ollama；預設不下載且不載入。
- HashingVectorizer + SGDClassifier 增量 ML，人工回饋與 Macro-F1 候選升版閘門。
- SQLite WAL cache、batch checkpoint、原子 stage queue、stale task recovery。
- FastAPI、CLI、淺色響應式監控 Dashboard、Windows PowerShell 一鍵安裝。
- 跳題對話無損 segment ledger、Body of Knowledge、Mind Map、SSOT 與 VIA Keyword。
- Python／PowerShell／JavaScript／TypeScript／JSON 唯讀解析與 Engine JSON 整合藍圖。
- Mega-Prompt 治理契約：三輪分析、六條管線、20 Accelerators、Zero-Hydra 風險矩陣。
- Argos／Ollama／Google Cloud 分段翻譯；明確拒絕不穩定的 Google 網頁自動貼上模擬。
- 24 項自動測試全部通過；三份實際附件精確重建與完善稿覆蓋均為 100%；500 篇短文併發壓測通過。

## 安全預設

- 僅綁定 localhost。
- 深度模型與 LLM 關閉。
- 模型自動升版關閉。
- 稽核記錄不保存原文，只保存輸入雜湊與處理 metadata。
- 模糊詞只提出候選，不靜默更改文章事實。

## 相容性

- Python 3.11+。
- Windows 11／PowerShell 7 為主要部署目標。
- Linux 與 macOS 可使用 Python CLI；PowerShell 一鍵安裝流程針對 Windows。
