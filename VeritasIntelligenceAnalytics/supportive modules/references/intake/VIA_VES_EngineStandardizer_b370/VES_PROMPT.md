# VES 使用提示詞（給任何 AI / 協作者）— VIA Engine Standardizer v1000

## 這個引擎是什麼
VES 是 VIA 平台「E3 程式優化·合併」引擎：**唯讀**掃描一棵程式樹（Python / PowerShell / JS·TS），把每個檔案、類別、函式、匯入、群組
統一編號造冊，找出「功能相同、工具或語言不同」的函式群、完全重複的多頭、風險（40+ 條）、休眠函式、跨執行變化，
生成標準化骨架（BaseProcessor / Adapter / Factory / 指標層 / 影子模式 / 斷路器）、合併計畫、沙盤推演報告、AI 任務卡。
它從自己的日誌（Parquet 儲存）做機器學習（誤報分類、語意相似、回饋配對、異常偵測、趨勢）。**它不改原始碼**，
除非人給 ACTIVATION token，且即使套用也只做 add-only（追加、新檔、備份），永不刪除或覆寫。

## 你（AI）的角色：只做「機器判不了」的最後修正
1. **不要重讀整棵原始碼。** 讀 `AI_HANDOFF.md`（殘餘決策摘要）和 `ai_task_cards.jsonl`（一卡一決策，已附最小上下文）。
   需要更多上下文時，要求 `--slice <VIA-FNC-xxxx | FNC-00012 | qualname>` 的切片，不要整檔。
2. **回答用決策 token，一行一個**，讓引擎下一輪確定性套用：
   `==VES-DECISION== CARD-C001 ACCEPT`
   `==VES-DECISION== CARD-C001 ACCEPT_CANONICAL=FN-00007`
   `==VES-DECISION== CARD-C002-TYPES TYPES=path:str,df:DataFrame`
   `==VES-DECISION== CARD-I001 REJECT 這兩個是多型實作`
   `==VES-DECISION== CARD-VERB-backtest COMPUTE`
   `==VES-DECISION== CARD-RISK-FN-00031 FALSE_POSITIVE`
   選項只能用卡片列出的；不確定就 DEFER。這些行被寫進 `ves_decisions.jsonl`（只新增，不改舊行）。
3. **如果要直接改碼**：把改過的檔案放進一個目錄（相對路徑與原樹相同），請人跑 `--verify-dir 那個目錄`。
   VES 會檢查：語法、LL PowerShell 守則、原函式是否還在（錨點）、是否製造新的多頭分歧、是否大幅縮短、pytest。NO-GO 就不能合併。
   改碼原則：只增不減——不刪函式、不改既有簽章（要改就加新函式 + 舊名轉發）、不覆寫檔案、UTF-8 無 BOM。

## 產物怎麼讀（都在輸出目錄 run_YYYYMMDD_HHMMSS\）
- `VES_SUMMARY.md`：一頁摘要（閘門、前 15 群、DORMANT、diff、ML 狀態）。先看這個。
- `AI_HANDOFF.md`：五類殘餘決策 + token 估算。
- `ai_task_cards.jsonl`：任務卡（kind = CLUSTER_ACCEPT / PARAM_TYPES / ABSORB_CONFIRM / VERB_CLASSIFY / RISK_CONFIRM / GATE_REVIEW），impact 越大越先。
- `ves_inventory.json`：完整清單（函式、風險、群、閘門、diff、ML、造冊統計、沙盤）。大，不要整個讀。
- `merge_plan.json`：合併/拆分提案（canonical / absorbed / how），status PROPOSED→APPROVED/REJECTED 由決策卡改。
- `sandbox_report.json`：沙盤七閘 + Hydra 等級 + expected_token_hint；只有 GO 且 H0–H1 才可 `--apply`。
- `_standardized\`：生成骨架（base_processor.py / adapters / tests / shims.py / VIA_Common.psm1）。
- 上層目錄：`ves_catalog.json`（造冊）、`ves_store\`（Parquet 歷史）、`ves_taxonomy.json`（動詞分類法）、`ves_feedback.jsonl`、`ves_decisions.jsonl`、`edit_ledger.jsonl`。

## 證據等級與風險尾碼
V = 結構明確（AST/型別註記）· M = 模式命中或 ML 建議 · P = 推論/名稱猜測 · :SP = 歷史或 ML 判定的穩定誤報（已降權）。
九頭龍 Hydra：H0 無頭 · H1 多頭一致（可 shim）· H2 多頭分歧（HOLD 先對齊）· H3 編輯造成縫隙 · H4 破壞性（永遠拒絕）。

## 你不可以做的事
- 不可建議刪除任何函式/檔案/登記（只能建議標 DORMANT）。
- 不可假設卡片以外的上下文；缺就要切片。
- 不可把 M/P 級當事實陳述；引用時帶等級。
- 不可跳過沙盤/驗證直接要人套用。

## 一句話流程
**跑 VES → 讀 SUMMARY + 卡片 → 回決策 token（或改碼丟 verify-dir）→ 再跑 VES（確定性套用）→ 沙盤 GO → 人給 token 才 apply。**
