# VMT · AI 高智慧自動 Outlook 郵箱及工作管理系統 v1.0

VeritasMailTracker 引擎組。把「收到的信」與「會議上講的話」變成同一份可稽核的工作台帳，
然後自動追蹤到收口。

```
Outlook ──┐
          ├─► 判讀 ─► 任務台帳 ─► SLA ─► 追蹤信 ─► 回覆解析 ─┐
逐字稿 ───┘         (SSOT)                                   │
   ▲                                                          │
   └──────────────── 事件流 events.jsonl ◄────────────────────┘
```

---

## 快速開始

```bash
# 1. 先看它「打算做什麼」（dry-run，不寫任何東西）
python3 engines/vmt_pipeline.py --demo

# 2. 確認無誤後才落帳
python3 engines/vmt_pipeline.py --demo --commit

# 3. 打開戰情總覽
open $VMT_ROOT/reports/VMT_Dashboard.html
```

不需要安裝任何套件，標準庫即可跑完整條管線。`--demo` 使用內建的範例信件與逐字稿，
可在乾淨機器上立即驗證。

### 接上真實資料

```bash
export VMT_ROOT="C:\VIA\VeritasMailTracker"        # Windows
cp samples/vmt_config.example.json "$VMT_ROOT/data/vmt_config.json"

# Windows + Outlook（自動偵測，只讀收件匣）
python3 engines/vmt_pipeline.py --commit

# 沒有 Outlook：把 .eml / .json 丟進 $VMT_ROOT/mail_inbox/
python3 engines/vmt_pipeline.py --source folder --commit

# 加上會議逐字稿
python3 engines/vmt_pipeline.py --transcript meeting.json \
        --meeting-config samples/meeting_config.json --commit
```

---

## 十二個引擎

| 引擎 | 職責 | 單獨執行 |
|---|---|---|
| `vmt_core.py` | 工作區、add-only 帳本、事件流、Q01 隔離、Visual Lock 報告 | （函式庫） |
| `vmt_lang.py` | 切句、相對期限換算、郵件意圖、句子性質、同音字校正 | （函式庫） |
| `vmt_outlook_intake.py` | 收信（Outlook → 資料夾 → 範例三級降級），MD5 去重 | ✔ |
| `vmt_ai_triage.py` | 意圖 / 緊急度 / 期限 / 歸案；規則優先、LLM 補位 | ✔ `--llm` |
| `vmt_meeting_minutes.py` | 逐字稿 → 標主詞 → 標性質 → 會議記錄 + 完整性稽核 | ✔ |
| `vmt_extract_tasks.py` | 郵件會話 + 會議待辦 → 任務候選（provenance 必填） | ✔ |
| `vmt_task_ssot.py` | 工作台帳；宣告 add-only，狀態由事件 replay 推導 | ✔ |
| `vmt_sla_engine.py` | 逾期推導、冪等升級、催辦排程 | ✔ `--as-of` |
| `vmt_mail_composer.py` | 有限選項追蹤信；對外／自己／待指派三流分開 | ✔ `--draft` |
| `vmt_reply_parser.py` | 勾選 + 追蹤編號 → 事件，閉環收口 | ✔ |
| `vmt_dashboard.py` | 戰情總覽（純讀，不寫任何資料） | ✔ |
| `vmt_pipeline.py` | 一鍵跑完整條閉環 | ✔ `--demo` |

每個引擎都能單獨執行、單獨產出報告，方便逐段檢查。

---

## 治理紅線

沿用你既有 VMT / SuperBOM 的規則，由 `vmt_core` 統一強制：

| 紅線 | 實作 |
|---|---|
| **來源只讀** | Outlook 全程唯讀：不標已讀、不搬移、不刪除、不回寫 |
| **帳本 add-only** | 所有 `*.jsonl` 只 append，永不 UPDATE / DELETE |
| **狀態由事件推導** | 任務狀態、逾期與否一律 replay `events.jsonl`，沒有可變欄位 |
| **預設 dry-run** | 不加 `--commit` 只產報告；報告頁首會顯著標示 DRY-RUN |
| **冪等** | 郵件用 MD5、任務用來源指紋、隔離用 q_uid；重跑不長資料 |
| **低信心不阻斷** | 判讀信心不足送 Q01 隔離，主線照跑 |

### 寄送階梯

催辦信是寄給真人的，所以預設一路關到底：

```
dry-run          什麼都不寫
--commit         只寫出 .txt 信稿到 mails/<日期>/
--commit --draft 另外在 Outlook 建草稿（仍需人按送出）
--commit --send  直接寄出（不可逆，需明確指定）
```

### 系統不會憑空生成的五件事

這是整套設計最核心的部分——自動化系統最危險的失敗模式，
是讓人以為它已經全部處理完了。

1. 主詞判不出來 → 標 `[?]`，不猜
2. 待辦缺負責人或期限 → 填 `[?]` 並列入「待確認」，不丟棄也不臆測
3. 任務沒有期限 → **不自動填期限**，改以追蹤信向對方索取 ETA
4. 議程有而未討論 → 明寫「本次未討論」，不靜默略過
5. 摘要有列數上限 → 明寫「另有 N 句未列入」，不靜默截斷

另外兩個刻意保守的行為：勾「已完成」但確認欄填「否」**不收口**；
申請延期卻沒給 ETA **不展延**，改記為受阻。

---

## 資料模型

全部落在 `$VMT_ROOT/data/`，皆為 JSON Lines：

| 帳本 | 內容 | 冪等鍵 |
|---|---|---|
| `mails.jsonl` | 已入帳郵件 | 內容 MD5 |
| `triage.jsonl` | AI 判讀結果 | mail_uid + 引擎版本 |
| `minutes.jsonl` | 會議記錄 + 標記逐字稿（證據） | minute_uid |
| `tasks.jsonl` | 任務宣告（**不含任何狀態欄位**） | 來源指紋 |
| `events.jsonl` | 事件流 — 狀態的唯一真相 | — |
| `quarantine.jsonl` | Q01 待人工 | q_uid |

任務狀態機：`OPEN → ACK → IN_PROGRESS → DONE`，任一狀態可轉 `BLOCKED` / `CANCELLED`。
`OVERDUE` **不是狀態欄位**，而是 `due < 基準日` 的推導結果——所以改 SLA 規則只要重跑，
歷史資料不需要遷移。

---

## 會議記錄引擎

逐字稿 → 記錄的六步，每步都可單獨檢查：

```
1 切句   → [001] 一句一列，時間戳依字數比例內插
2 清洗   → 贅詞／簡繁／同音字校正（原文另存供覆核）
3 標主詞 → 指派 > 第一人稱 > 我們 > 你 > 他 > 人名 > 繼承 > [?]
4 標性質 → 決 / 辦 / 議 / 問 / 資（附觸發 cue）
5 分議題 → 議程對照為主，轉場語與時間間隔為輔
6 產記錄 → 每條結論掛來源句號 #012，可回查原文
```

標記逐字稿長這樣，它是會議記錄的原始證據，會一起保存：

```
[007] 00:52 王小明 |決| 好，那就決定下一檔的宣傳期拉長到四週。
[008] 01:03 李美華 |辦| 了解，我下週三前提出新的宣傳排程。
[010] 01:26 林佳蓉 |辦| 麻煩林佳蓉幫忙確認一下東莞那邊的排程有沒有衝突。
[019] 04:12 [?]    |drop| 謝謝觀看謝謝觀看謝謝觀看
```

第 010 句由王小明所說，但主詞是被指派的林佳蓉；第 019 句是 ASR 幻覺，
標記丟棄但原列仍留在帳本。

### 完整性稽核（漏掉比寫錯更難發現）

- **議程對照**：議程有、逐字稿沒有 → 明寫「本次未討論」
- **引用反查**：未被任何結論引用、卻含期限或數字的句子 → 列為「疑似遺漏」
- **時間軸缺口**：相鄰句間隔過大 → 提示該段可能漏轉
- **幻覺過濾**：靜音段有字 / `no_speech_prob` 過高 / n-gram 連續重複

---

## 判讀為什麼是規則優先

`vmt_lang` 的每個判斷都回傳觸發它的 cue 詞，報告上看得到「系統為什麼這樣判」。
LLM（`--llm`，走本地 Ollama）只在規則層信心不足時補位，**永不覆寫高信心的規則結論**；
規則與 LLM 不一致時兩者都記錄、降低信心並送 Q01 交人工。

LLM 無法連線時，整套系統功能不受影響——這是刻意的，判讀結果會直接觸發寄信給真人。

### 同音字校正

ASR 中文錯誤幾乎都是同音字替換。校正需同時滿足三個條件，缺一不可：

| 條件 | 例 |
|---|---|
| 等長且至多 1 字不同 | 稼動**律** → 稼動**率** ✔ |
| 差異字必須同音 | 宣傳**排**程 ✘ 不會被改成宣傳**期**程 |
| 互為子字串者不改 | 「宣傳」是合法的較短詞，不是「宣傳期」的錯誤 |

同音字群定義在 `vmt_lang._HOMOPHONE_GROUPS`，可依自家專有名詞擴充。

---

## 接真實語音辨識

本引擎組從**逐字稿**開始。前段語音轉文字建議（皆為免費開源、Python 可用）：

| 情境 | 建議組合 |
|---|---|
| 中文／繁中會議 | Silero VAD → FunASR（Paraformer + 標點 + 分離）→ OpenCC `s2twp` |
| 英文、要最快 | Silero VAD → NVIDIA Parakeet TDT v3（NeMo）→ Sortformer |
| 多語混雜、要最穩 | WhisperX（large-v3 + hotwords）→ pyannote 4.0 community-1 |

輸出成本引擎接受的格式即可：

```json
{"segments": [{"start": 0.0, "end": 14.0, "speaker": "SPEAKER_00", "text": "..."}]}
```

`speaker` 用 `SPEAKER_00` 也沒關係，在 `meeting_config.json` 的 `speaker_map` 對照成真實姓名。
若 segment 帶有 `no_speech_prob` 或 `is_silence`，幻覺過濾會一併使用。

---

## 測試

```bash
python3 tests/test_vmt_engines.py
```

34 項，標準庫 `unittest`，無外部相依。測試集中在「錯了會出事」的地方：
治理紅線、相對期限換算、決議 vs 提議、主詞標示、完整性稽核、
郵件會話合併、冪等重跑、回覆閉環、逾期推導、升級冪等。

---

## 與既有子系統的關係

- **VMT v1**：沿用 `CASE-XX` 案號規則與「有限選項回覆」郵件格式。
  本引擎組自持 `tasks.jsonl` / `events.jsonl`，**不改寫** v1 的 `ssot.json`。
- **SuperBOM**：共用 `CASE` 命名與 Q01 隔離精神。兩邊 SSOT 不合併，僅於橋接處對接
  （`vmt_superbom_bridge.py` / `vmt_superbom_attach_router.py`）。

工作區資料（`$VMT_ROOT` 下的 `data/`、`reports/`、`mails/`）不進版控。
