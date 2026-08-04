# VTR · DG-IN Meeting Transcript Restoration Engine

**中英文會議紀錄修復引擎** —— VIA 功能子系統，代號 **VTR**（Veritas Transcript Restoration）。

Best Solution Portfolio 定義了「要哪七大模組」；本目錄是它的**下一層工程規格**：可實作、可驗證、可回溯。

---

## 🟢 新電腦？完全不懂指令？先看這裡

這台電腦剛裝好、什麼都沒有也沒關係。**只要做一件事：**

> **在檔案總管裡，雙擊 `Install-VTR.cmd`**

它會自動幫你：**先裝最新版 PowerShell 7** → 檢查有沒有 Python，沒有就自動下載安裝
→ 設好 PATH → 跑一次完整驗證確認能用。全程中文提示，告訴你每一步在做什麼，
全程**不需要管理員權限**。

裝好之後，日常只要**雙擊 `Run-VTR.cmd`** 就會跑一次完整檢查。就這樣，不用記任何指令。

### 想先看它跑起來？（用內建範例）

專案內附了一份範例逐字稿 `samples\meeting-sample.txt`。在終端機依序執行：

```powershell
Run-VTR.cmd -Action Restore -Path .\samples\
Run-VTR.cmd -Action Inspect -DocId meeting-sample -ShowReview
```

第一行會把範例修復好（畫面會顯示 doc-id 是 `meeting-sample`），第二行檢視結果與待裁決清單。

| 你想做的事 | 怎麼做 |
|---|---|
| 第一次安裝（新電腦） | 雙擊 `Install-VTR.cmd` |
| 平常檢查系統正不正常 | 雙擊 `Run-VTR.cmd` |
| 先看範例跑一次 | `Run-VTR.cmd -Action Restore -Path .\samples\` |
| 修復你自己的逐字稿 | 把 `.txt` 放進一個資料夾（例如自己建一個 `input`），執行 `Run-VTR.cmd -Action Restore -Path .\input\` |
| 檢視某份修復結果 | `Run-VTR.cmd -Action Inspect -DocId <畫面顯示的id> -ShowReview` |

> 需要管理員權限嗎？**不需要。** PowerShell 與 Python 都優先裝給你目前的帳號。
> 出現「系統禁止執行指令碼」的紅字嗎？**不會。** 那兩個 `.cmd` 已經幫你處理好了。
> 打了一個還沒修復過的 doc-id？**不會噴一堆英文錯誤。** 會用中文告訴你先跑 restore。

下面是給工程師看的細節。一般使用者看到這裡就夠了。

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
| `engine/vtr_py/` | **可執行的引擎**：骨架 + 步驟 1–2 + P0 遮罩（零第三方相依） |
| `engine/tests/` | 49 個測試（單元・不變式・對抗・回歸・突變驗證） |
| `config/vtr.json` | 兩版引擎共用的門檻與權重設定 |
| `Invoke-VTR.ps1` | **單一 PowerShell 進入點**（operator workstation 用） |
| `tools/build_manifest.py` | Manifest 重算工具（可重現的 hash-lock 輸入） |
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

全部零第三方相依（連 PowerShell 模組也不需要），clone 下來就能跑。

### 一個指令處理全部 —— `Invoke-VTR.ps1`

```powershell
cd "VeritasIntelligenceAnalytics\functional modules\VTR"

.\Invoke-VTR.ps1                                   # 全套驗證（Doctor+Lexicon+Test+Manifest）
.\Invoke-VTR.ps1 -Action Doctor                    # 只檢查環境
.\Invoke-VTR.ps1 -Action Restore -Path .\input\    # 批次修復整個資料夾
.\Invoke-VTR.ps1 -Action Inspect -DocId MTG-001 -ShowReview
.\Invoke-VTR.ps1 -Action Replay  -DocId MTG-001 -ToRev 1
.\Invoke-VTR.ps1 -Action Manifest -Update          # 重算 hash-lock
```

退出碼：`0` 通過 · `2` 契約/schema · `3` SSOT 或 sentinel 違反 · `4` 改壞率 ·
`5` manifest 不一致 · `10` 環境不符。可直接掛 CI 或排程。

三個非顯而易見但必要的設計（都源自本 repo 踩過的坑）：

| 決定 | 理由 |
|---|---|
| 不用 `Start-Process` | 本 repo 路徑含空白（`functional modules`），`ArgumentList` 會在空白處把參數拆開 —— git log 有兩次修這個 bug 的紀錄。改用 `& $exe @args`。 |
| 強制 UTF-8（含 `PYTHONUTF8=1`） | 輸出含中文與遮罩符 `⟦⟧`；Windows 主控台預設 cp950 會變亂碼。 |
| 檔案存成 **UTF-8 with BOM** | Windows PowerShell 5.1 對無 BOM 的檔案假設 ANSI，會把中文字串解析成亂碼。這是 5.1 相容性的硬性要求，不是風格選擇。 |

### 直接呼叫 Python（Linux / macOS / CI）

```bash
cd "VeritasIntelligenceAnalytics/functional modules/VTR"

python3 lexicon/tools/validate_lexicon.py                    # 詞庫（exit 0/2/3）
python3 tools/build_manifest.py                              # manifest（exit 0/5）
cd engine && python3 -m unittest discover -s tests -t .      # 49 tests

python3 -m vtr_py.cli restore transcript.txt --doc-id MTG-001 --out ./out/
python3 -m vtr_py.cli inspect ./out --review                 # 看待裁決佇列
python3 -m vtr_py.cli replay  ./out --to-rev 1               # 回滾到任一版本
```

### 實際輸出範例

輸入（ASR 原始逐字稿）：

```
嗯，那個  我們先看一下dashboard的ＫＰＩ
VeritasAutoPlot在v0162B已經鎖定, 請在14:30前回覆tony@example.com
```

輸出：

```
嗯，那個我們先看一下 dashboard 的 KPI
⟦P0001⟧ 在 ⟦P0002⟧ 已經鎖定，請在 ⟦P0003⟧ 前回覆 ⟦P0004⟧
    ⟦P0001⟧ = 'VeritasAutoPlot'   (code_ident)
    ⟦P0002⟧ = 'v0162B'            (part_number)
    ⟦P0003⟧ = '14:30'             (timestamp)
    ⟦P0004⟧ = 'tony@example.com'  (email)

待裁決：'嗯' → ''（conf 0.70，疑似語助詞，不自動套用）
        '那個' → ''（conf 0.70）
```

全形 ＫＰＩ 轉半形、中英交界補空白、半形逗號在中文語境轉全形、專名與料號全部遮罩；
語助詞只提建議不自動刪除；`v0162B` 沒有被拆成 `v0162 B`。

目前狀態：**種子詞庫 29 詞條・26 啟用・3 草稿・74 別名**；**引擎 49 個測試全過**。

---

## 治理

與 VRN / VDF / VAP 同一閘門：

- 引擎**不得**直接改寫 canonical 逐字稿；只產生 candidate + patch log。
- 新詞一律 `enabled=false` 草稿，需 operator 覆核（由驗證器強制）。
- 晉升需 operator 覆核 + hash-locked transaction。
- 每一筆改動可回答：誰改的、依據什麼規則、為什麼、信心多少。

---

## 已實作 vs 尚未實作

| 元件 | 狀態 |
|---|---|
| 資料契約 · Pipeline 不變式 · 信心度閘門 | ✅ |
| 步驟 1 LANG_DETECT · 步驟 2 NORMALIZE | ✅ |
| P0 PROTECT / UNPROTECT（pattern 規則） | ✅ |
| Diff & Versioning（patch log · replay · 回滾） | ✅ |
| CLI（restore / inspect / replay） | ✅ |
| PowerShell 單一進入點 `Invoke-VTR.ps1` | ✅ |
| P0 詞庫精確命中（接上 SSOT Lexicon） | ⬜ |
| 步驟 3–8（標點／斷句／錯字／文法／專名／結構化） | ⬜ 需模型層 |
| LLM 仲裁層 | ⬜ |
| `@dg-in/vtr-js` | ⬜ |

### 下一步（依相依順序）

1. **黃金測試集**：≥200 段人工標註（中／英／混雜各三分之一）。**應早於模型層建立** ——
   否則「改壞率」沒有東西可以量測，而那是本引擎唯一真正重要的安全指標。
2. `lexicon/store.py` + `matcher.py`，把 SSOT Lexicon 接上 P0（精確命中）與步驟 7（模糊比對）。
3. 步驟 3–4（標點恢復、斷句）—— 第一次引入模型相依與信心度校準。
4. `@dg-in/vtr-js` 本地管線 + Review Queue UI + 跨引擎一致性測試。
5. LLM 仲裁層。
