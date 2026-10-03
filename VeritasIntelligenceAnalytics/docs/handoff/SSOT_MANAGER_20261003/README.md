# 單一引擎：SSOT／Regex／同義字管理

正主為 CGC_MDL237_NumberingSystem_v0115。沿用原中央 allocator 與 L1 引擎，不另建流水號或第二套 SSOT。使用現有 VCGC 入口：

```text
via-vcgc run CGC_MDL237_NumberingSystem manager plan
via-vcgc run CGC_MDL237_NumberingSystem manager sync --apply --owner VCGC --input <絕對路徑records.json> --out <絕對路徑輸出夾>
```

第二行一次完成：讀中央候選冊及已登錄 SSOT → 檢查衝突 → 在排他寫入鎖內呼叫既有中央發號 → 重新讀中央 → 更新規則快照 → 執行 L1 同義詞／Regex 清洗 → Parquet、CSV 與 manifest。只同步規則時可省略 input；只預覽時省略 --apply。沒有常駐 daemon：每次呼叫自動讀取最新中央狀態並比較指紋；無變更且快照 SHA 正確即重用。

## 管理與衝突

- 最新 VIA_AssetCandidates_SSOT_v*.json 為正式候選來源。manager plan --candidates <外部檔> 只預覽；外部檔不能直接 --apply。正式候選必須先出新版、提交 git，再由中央 scoped allocator 登錄。引擎不自動改 git 或偷偷批准規則。
- 同一來源／候選／版本保號；不同來源即使值相同仍分號。版本變更必須明示 supersedes，舊版歷史保留。
- owner + scope 限定別名；NFKC + casefold 後的一詞多主、連鎖改寫及循環會阻擋。不同來源但同一標準詞可共存，匹配證據保留所有中央 rule_codes。
- Regex 使用 RE2。只對既有固定寬度子集證明重疊；同範圍不同目標重疊阻擋，無法證明維持 REVIEW。不將少量測資通過當作一般正則等價證明。
- 已登錄 Regex 在其 scope 以 fullmatch 驗證欄位；不截短無效代碼來湊成功。同義詞全文匹配沿用 L1 的中文／英文邊界規則。
- 檢查不可變版本、定義 SHA 漂移、最新版退役、同 binding 異值、偽造號碼及禁止依賴。最新版失效不回退啟用舊規則。
- 同步後 L1 立即使用新中央規則。歷史中央同義冊與已註冊 SYNONYM 資產都可投影；只有明確登錄且驗證過的 REGEX 資產自動啟用。缺 scope 的歷史 Regex 保留在衝突檢查，不猜測執行意義。
- 無效 scope 進 REVIEW，受規則衝突影響的資料隔離；模糊／語意候選不自動入冊。L1 record 的 ssot_code 仍為 null，不能把規則碼當作資料身分。

plan/show/conflicts/sync 都回傳中央 plan 與 catalog；snapshot 是可刪除重建的唯讀投影。source_fingerprint 改變會自動刷新；快照損壞也重建。預覽依據已發布中央冊，實際 apply 由原 collector 再檢查來源後發號；不宣稱未提交來源已同步。allocator 回 rc=0 但仍有 READY 未登錄時，manager 不報成功。

## 驗證與限制

新增自測與原中央 30 項自測經 VCGC 執行，涵蓋來源分離、重跑保號、Regex、同義字循環、規則更新、快照修復及唯一 allocator 派送。實際中央字典和 L1 測資有留存執行證據。自測中的新增資產只進暫存 state，沒有為了湊成功寫入虛構正式規則。

TA-Lib 禁用。沿用先前隔離 Linux/Python 3.12 與相依 lock；Windows、原始 134 車道及正式 DB/OCR 沒有在此環境驗收。先前 MOM 同義詞與 TWSE/TPEX Regex 三個候選仍待審，不能自動略過。

中央 writer 忙碌時回 HOLD，不強制接管；跨程序、跨檔崩潰原子性及舊寫入者不宣稱已保證。本次前次作業遺留鎖已確認沒有對應存活 Python 行程，原鎖及復原紀錄存於本目錄；runtime manager 不自動解除他人鎖。
