# VPNS · 流程探勘知識體(從 `台達電.docx` 抽取)

> **檔案真相**:上傳的 `台達電.docx`(8,289 行)**不含任何台達電公司資料** —— 它是一篇 **IBM 來源的流程探勘 (Process Mining) 指南**。零次提及台達/康舒/散熱/營收/毛利/資本支出/PSU。檔名為 dictation/存檔誤名。
> **處理方式**:內容屬 IBM 版權,本檔**只把結構抽成 taxonomy 並以自有措辭改寫**,不重製原文段落。證據 tier=T2(第三方教材),來源已標。走 Normalized Extraction Block:docx → 中間層 `vpns_pm_kb.csv`(已驗證)→ 本知識體。
> **歸屬**:此知識屬 **VPNS**(流程探勘覆蓋層,今天 prompt 的 base),非 PSU/Thermal。

---

## 一、為什麼這份對 VPNS 有用

VPNS 是「架在 ERP/SAP 之上的**唯讀**流程探勘情報層」。這份 IBM 指南剛好把流程探勘的**問題型別、效益、應用案例**講成一套可對照的骨架 —— 正好可當 VPNS 的 **產業知識體(介面 7)** 種子,並把案例掛回 SAP 模組。

---

## 二、抽取結果(21 條 · 5 分類 · 已驗證 PASS)

**定義 / 核心技術(3)** — 流程探勘=從日誌自動還原實際流程並監控優化;數位雙胞胎=流程數據化模型;與傳統 BPM 差異=數據驅動還原 vs 專家事前設計。

**問題型別(5)** — 這 5 類直接對映 VPNS 的 discovery 輸出:根本原因識別 · 瓶頸減少 · 返工減少 · 自動化效益 · 合規性。

**效益(4)** — 效能與生產力 · 降營運成本 · 改善客戶體驗 · 數據驅動決策。

**應用案例(6)→ 掛 SAP 模組** — P2P 採購到付款(MM/FI)· O2C 訂單到收款(SD/FI)· AP 應付帳款(FI)· 智能自動化+RPA · 客戶 onboarding · IT 事件管理。

**工具功能(3)** — 流程自動發現 · RPA 腳本生成 · AI 流程模擬(對照,不背書特定廠商)。

---

## 三、掛回 VPNS 系統的錨點

| 知識分類 | VPNS hook | 對映既有元件 |
|---|---|---|
| 問題型別 | `VPNS.rootcause/bottleneck/rework` | VPNS workflow discovery(engine.py 的 9 站 demo:物料→採購→IQC→SMT→DIP→ICT→FCT→包裝→出貨,瓶頸 SMT/ICT) |
| 應用案例(P2P/O2C/AP) | `SAP.MM/SD/FI` | `sap_modules_ref.py`(固定 T-code)· VPNS_REGEX_REGISTRY(33 SAP patterns) |
| 合規性 | `VPNS.compliance` | 治理報告層 |
| 工具功能 | `VPNS.discover/rpa/sim` | pm4py 流程挖掘 |

---

## 四、誠實提醒 + 下一步

1. 若你**本來要的是台達電公司資料**(BU/產品/財務/製程),這個檔給不了 —— 請重傳正確檔(或 MOPS 財報 PDF),我再走一次抽取進 T02/T03/T06/T07。
2. 這 21 條知識要不要我**併進** `via_pt` 的 T07(VIA-KNW)當首批真實知識列,還是維持 VPNS 獨立 KB(`vpns_kb/`)?
3. VPNS 那支 `Invoke-VPNS-Panorama-v003.ps1` 已可在你本機 base 實跑 —— 這份 KB 可當它 SSOT 的 `knowledge` 區段來源。

---

## Top 10 free local libs(本輪新增函式;append-only)

| 函式區 / 語言 | Top 10 |
|---|---|
| docx / 文件抽取 · Python | `python-docx` · `pandoc(pypandoc)` · `mammoth` · `docx2txt` · `unstructured` · `textract` · `olefile` · `lxml` · `beautifulsoup4` · `markitdown` |
| 流程探勘 · Python | `pm4py` · `networkx` · `graphviz` · `pygraphviz` · `scipy` · `pandas` · `numpy` · `intervaltree`(時序)· `python-dateutil` · `matplotlib` |
| 知識體 / taxonomy / 分類 · Python | `rapidfuzz` · `jellyfish` · `rdflib`(知識圖)· `owlready2` · `spacy` · `scikit-learn`(分群)· `gensim` · `yake`(關鍵詞)· `keybert` · `pandera`(schema 驗證) |

---

## 方法論四問

1. **版權界線** — 我只抽 taxonomy + 自有改寫,不留原文。你認可這條界線嗎,還是連 taxonomy 都想再精簡?
2. **知識歸屬** — 這 21 條進 VPNS KB 還是 `via_pt` T07?(牽涉 SSOT 分合)
3. **誤名檔處理** — 要不要我加一個「上傳檔 content-sniff」步驟(讀前 200 字判斷真實主題 vs 檔名),避免下次又被 dictation 誤名誤導?
4. **案例→SAP 綁定** — P2P/O2C/AP 我掛到 MM/SD/FI;要不要進一步綁到 `sap_modules_ref` 的固定 T-code(如 P2P→ME21N/MIRO),讓知識體可直接對映交易碼?
