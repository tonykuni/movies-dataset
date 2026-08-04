# VTR · DG-IN Meeting Transcript Restoration Engine

**中英文會議紀錄修復引擎** —— VIA 功能子系統，代號 **VTR**（Veritas Transcript Restoration）。

Best Solution Portfolio 定義了「要哪七大模組」；本目錄是它的**下一層工程規格**：可實作、可驗證、可回溯。

---

## 目錄

| 路徑 | 內容 |
|---|---|
| `contracts/vtr-document.schema.json` | **資料契約**（SSOT）—— Python 版與 JS 版共用的 Document / Segment / Patch / Revision 結構 |
| `docs/00_ARCHITECTURE.md` | 完整修復引擎架構圖：三層架構、八步管線、P0 遮罩、信心度閘門、四大 Pipeline、成本模型、評估指標 |
| `docs/01_PYTHON_ENGINE_SPEC.md` | Python 版規格書（權威實作／批次／模型層／LLM 仲裁） |
| `docs/02_JAVASCRIPT_ENGINE_SPEC.md` | JavaScript 版規格書（即時預覽／編輯器層／人工裁決 UI） |
| `docs/03_SSOT_LEXICON_SPEC.md` | SSOT Lexicon 結構規格書 |
| `lexicon/` | **可執行的詞庫**：schema、五個種子詞庫、索引、驗證器 |
| `VTR_Subsystem_Manifest.json` | 子系統 anchor manifest（SHA-256 登錄、治理閘門） |

---

## Portfolio 七大模組 → 本規格對照

| # | Portfolio 模組 | 落點 |
|---|---|---|
| 1 | 雙語混合修復架構 | `00_ARCHITECTURE.md` §1（L1/L2/L3 三層） |
| 2 | 八步修復法 | `00_ARCHITECTURE.md` §2（＋P0 遮罩補強） |
| 3 | Python Top 15 工具組 | `01_PYTHON_ENGINE_SPEC.md` §3（含取捨理由） |
| 4 | JavaScript Top 15 工具組 | `02_JAVASCRIPT_ENGINE_SPEC.md` §3（含刻意留白清單） |
| 5 | 五大模型組合 | `01_PYTHON_ENGINE_SPEC.md` §4 + §6（LLM 仲裁層） |
| 6 | SSOT Lexicon | `03_SSOT_LEXICON_SPEC.md` + `lexicon/`（**已可執行**） |
| 7 | 四大 Pipeline | `00_ARCHITECTURE.md` §4 |

---

## 相對 Portfolio 的三處工程補強

規格化過程中發現三個問題，若不處理，前面七大模組會在真實會議紀錄上失效：

1. **P0 保護遮罩**（`00_ARCHITECTURE.md` §2.3）
   沒有遮罩，第 3–6 步會親手破壞第 6 模組要保護的專有名詞：`VIA-0162B` 被標點恢復切成 `VIA-0162 B`、`VeritasAutoPlot` 被拼寫修正拆成三個字。遮罩是讓八步法在有專名的文本上成立的前提。

2. **拼音／音素比對**（`03_SSOT_LEXICON_SPEC.md` §5.1）
   中文 ASR 的主要錯誤是**同音字**，字面編輯距離完全抓不到（「維瑞塔斯」vs「威瑞塔斯」字面相似度僅 0.75，拼音相似度 1.00）。Portfolio 的 15+15 工具組沒有涵蓋這一塊，因此補入 `pypinyin` / `pinyin-pro` 與 `jellyfish`。

3. **信心度閘門 + LLM 上限 0.80**（`00_ARCHITECTURE.md` §3）
   LLM 不得在無人複核下獨自改動會議紀錄。它的職責是**仲裁與解釋**，不是最終權威。單獨 LLM 判斷的信心度上限設 0.80，因此永遠落在 review 頻帶。

另外對兩份工具清單做了取捨（`01` §3.2、`02` §3.2）：SnowNLP、DeepSegment、Punctuator、node-jieba 等因維護狀態、繁中表現或無法在瀏覽器執行而不入主管線，理由逐項列出。**JS 版對中文錯字與中文文法明確留白**（標記 `pending_server`），不用弱工具硬做 —— 在會議紀錄上，錯誤的修復比不修復傷害更大。

---

## 立即可執行

```bash
cd "VeritasIntelligenceAnalytics/functional modules/VTR/lexicon/tools"

python3 validate_lexicon.py                # 驗證詞庫（exit 0/2/3）
python3 validate_lexicon.py --write-index  # 驗證並更新 lexicon.index.json
```

目前種子詞庫：**29 詞條・26 啟用・3 草稿・74 別名**，驗證通過。

---

## 治理

與 VRN / VDF / VAP 同一閘門：

- 引擎**不得**直接改寫 canonical 逐字稿；只產生 candidate + patch log。
- 新詞一律 `enabled=false` 草稿，需 operator 覆核（由驗證器強制）。
- 晉升需 operator 覆核 + hash-locked transaction。
- 每一筆改動可回答：誰改的、依據什麼規則、為什麼、信心多少。

---

## 下一步（尚未實作）

本目錄是**規格與詞庫**，尚未包含引擎程式碼。依相依順序：

1. `vtr_py` 骨架：`document.py` / `pipeline.py` / `gate.py` / `protect.py` + 步驟 1–2（純確定性，無模型相依）
2. 黃金測試集：≥200 段人工標註（中／英／混雜各三分之一）—— **應早於模型層建立**，否則沒有東西可以量測
3. 步驟 3–4（標點／斷句，需模型）
4. 步驟 7 Lexicon 比對 + 跨引擎數值一致性測試
5. `@dg-in/vtr-js` 本地管線 + Review Queue UI
6. LLM 仲裁層
