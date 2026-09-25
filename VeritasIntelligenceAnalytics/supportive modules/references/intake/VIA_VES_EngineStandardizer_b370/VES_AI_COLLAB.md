# VES × AI 協作協定（VES_AI_COLLAB/1.0）

適用：Claude / 本機 Ollama / 任何能讀檔回文字的 AI。目的：AI 只花 token 在「機器判不了的決策」，程式碼的讀取、分群、風險、造冊、沙盤全由 VES 做。

## 0. 角色分工
| 誰 | 做什麼 | 不做什麼 |
|---|---|---|
| **VES（引擎）** | 唯讀掃描、造冊編號、分群、風險、骨架、合併計畫、沙盤推演、九頭龍分級、任務卡、決策套用、日誌 ML | 不改原始碼（除非人給 token，且只 add-only） |
| **AI** | 讀摘要與任務卡 → 回決策 token；必要時要切片；改碼只交 verify-dir | 不重讀整樹、不猜卡片外的上下文、不建議刪除、不跳過沙盤 |
| **人（Tony）** | 跑指令、把 AI 的 token 貼進 ves_decisions.jsonl、最後 `-Apply -Token` | 不需要自己讀 inventory |

## 1. 一輪協作的固定順序（Handshake）
```
[人]  pwsh -File Invoke-VIA-EngineStandardizer.ps1 -Root <tree>          # 第 1 跑
[VES] run_YYYYMMDD_HHMMSS\  ← VES_SUMMARY.md / AI_HANDOFF.md / ai_task_cards.jsonl / VES_PROMPT.md / sandbox_report.json
[人]  把 VES_PROMPT.md + VES_SUMMARY.md + ai_task_cards.jsonl 貼給 AI（≈ 幾千 tokens）
[AI]  回：一行一個 ==VES-DECISION== …；需要上下文時回 ==VES-NEED-SLICE== <碼或函式名>
[人]  (若有 NEED-SLICE) pwsh … -Slice <碼>  → 把 slice_*.txt 貼回 AI → AI 再回決策
[人]  把所有 ==VES-DECISION== 行追加到 <上層目錄>\ves_decisions.jsonl
[人]  再跑一次 VES                                                        # 第 2 跑：確定性套用決策
[VES] 卡片減少、merge_plan 步驟變 APPROVED/REJECTED、taxonomy 更新、配對模型重排、沙盤重推
[人]  看 sandbox_report.json：GO 且 Hydra ≤ H1 → pwsh … -Apply -Token <expected_token_hint>
[VES] add-only 套用：原檔 .orig 備份、尾端追加、新檔只新增、edit_ledger.jsonl
```
HOLD-H2（多頭分歧）→ 不 apply；先請 AI 對分歧的頭出決策（CARD-I… ACCEPT_CANONICAL=…），再跑。

## 2. AI 輸出格式（唯一合法格式）
```
==VES-DECISION== CARD-C001 ACCEPT
==VES-DECISION== CARD-C001 ACCEPT_CANONICAL=FN-00007
==VES-DECISION== CARD-C002-TYPES TYPES=path:str,df:DataFrame,start:str
==VES-DECISION== CARD-I003 REJECT 兩者是多型實作，不是重複
==VES-DECISION== CARD-VERB-backtest COMPUTE
==VES-DECISION== CARD-RISK-FN-00031 FALSE_POSITIVE
==VES-DECISION== CARD-GATE-VES_PARSE_RATE ACCEPT_AS_IS
==VES-NEED-SLICE== VIA-FNC-3C6D3E
==VES-NEED-SLICE== load_prices
==VES-DEFER== CARD-C005 需要看呼叫者
```
規則：選項只能用卡片列出的；每張卡最多一行；不確定用 DEFER；不要輸出解釋長文（引擎不讀）。

## 3. AI 讀取順序（省 token 的順序）
1. `VES_SUMMARY.md`（1 頁）→ 2. `ai_task_cards.jsonl` 依 impact 由大到小 → 3. 只對想確認的卡要 `--slice` → 4. 從不讀 `ves_inventory.json` 整檔。

## 4. AI 直接改碼時
1. 只改「卡片指到的函式」；新增函式 + 舊名轉發，不刪、不改既有簽章、不覆寫、UTF-8 無 BOM。
2. 改過的檔放進一個目錄，相對路徑與原樹相同；請人跑 `-VerifyDir <該目錄>`。
3. 閘：VF_SYNTAX / VF_LL_AUDIT / VF_FUNCTIONS_KEPT / VF_RENAMES_TRACKED / VF_NO_MASS_SHRINK / VF_HYDRA_NEW_DIVERGENCE / VF_PYTEST。任何 RED = 不合併，AI 收 verify_report.json 再修。

## 5. 範例對話（縮短）
```
人 → AI：[貼 VES_PROMPT.md] [貼 VES_SUMMARY.md] [貼 ai_task_cards.jsonl 21 張]
AI → 人：
==VES-DECISION== CARD-VERB-recover VALIDATE
==VES-DECISION== CARD-VERB-handle TRANSFORM
==VES-DECISION== CARD-C001 ACCEPT_CANONICAL=FN-00412
==VES-DECISION== CARD-I002 ACCEPT
==VES-NEED-SLICE== VIA-FNC-9A21F0
==VES-DEFER== CARD-C003
人 → 跑 -Slice VIA-FNC-9A21F0 → 貼回
AI → 人：==VES-DECISION== CARD-C003 REJECT 同名但一個是檔案讀取一個是 API 拉取
人 → 追加到 ves_decisions.jsonl → 再跑 VES → sandbox GO / H1 → -Apply -Token VES-ACTIVATE-7F3A
```

## 6. 失敗時
- 卡片全空：代表沒有殘餘決策；直接看 sandbox。
- AI 回了卡片以外的選項：引擎忽略該行（不報錯），下輪同卡再出。
- 決策互相矛盾：後寫的優先（append-only，最後一行勝）。
- 想撤回：再寫一行新決策覆蓋，不要刪舊行。

## 7. 證據與誠實
AI 引用 VES 的任何判斷都要帶等級：V（結構）/ M（模式或 ML）/ P（推論）/ :SP（穩定誤報已降權）。九頭龍 H0–H4 由引擎判，AI 不可自行降級。
