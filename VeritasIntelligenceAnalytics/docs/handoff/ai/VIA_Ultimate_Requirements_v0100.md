# VIA 最嚴格要求 · Ultimate Performance Standard v1.0 · 規格正本 + 現況差距矩陣(2026-11-03)

> 來源:操作員 2026-11-03 貼上「請寫出我對 VIA 系統最嚴格的要求效能」全文(一~二十章 · KPI · SDD 狀態圖),並授權「自動解決完善三個獨立系統一切問題 · **完成既有範圍不可擴張**」。
> 本檔做兩件事:① 把要求**逐條編號**成規格正本(不改原意 · 矩陣化);② 每條寫**現況**(只寫有證據的 · 證據 = 檔名 / 版號 / 收據 / 測試)。
> 本檔**不是**已部署,也**不擴張範圍**:未做的項目只列待辦與負責系統,不在本輪動工。四系統對等獨立(政策 L123):VRN 只改 VRN 自己的檔;VDF / VCGC 的項目只列不代修。
> 需求登錄中央需求冊 / 工作流冊、正式編號,是 VCGC 的事(本檔 `UP-` 前綴只是本檔內的行號,不是正式編號 · ssot_id 留空等 VCGC 核發)。

狀態圖例:**✅ 已做**(有證據)· **◐ 部分**(寫明缺什麼)· **✗ 未做** · **—** 他系統(只列)· **?** 未量測(不冒充)

---

## 0. 核心理念與鐵律

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-0.1 | 最少輸入 · 最少點擊 · 最少等待 · 最少記憶體 · 最少重工 · 最少維護成本 | ◐ VRN:一行 Handle-All(收據 ≥ v0170 自動選 repair · 幾分鐘);仍要貼一行 PowerShell,不是 0 輸入 |
| UP-0.2 | 最高自動化 · 穩定性 · 成功率 · 可追溯性 · 資料品質 | ◐ 每步收據 + 收尾頁負責方分類;收尾仍 REVIEW(人工 1 · 資料源 3) |
| UP-0.3 | 可慢不可錯 · 可保守不可遺失資料 · 可增加保護不可增加九頭龍 | ✅ VRN:前版一字不改、只增新版號;寫檔 tmp → 換上;讀回不符不冒充成功(例 HistoryAlign v0103) |
| UP-0.4 | 任何修改可測試 · 可追溯 · 可回滾 · 可復原;任何故障可定位 · 可隔離 · 可恢復 · 不可擴散 | ◐ 可測試 / 可追溯 / 可回滾 ✅(自測 + 收據 + 封存);「不可擴散」:VRN 非關鍵步驟永不紅、不擋後續 ✅;跨系統故障隔離未系統化量測 ? |

## 一、架構

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-1.1 | VCGC / VDF / VRN 可獨立啟動 · 關閉 · 升級 · 部署 · 除錯 | ◐ VRN 自己的啟動器 / runtime / 收據 ✅;VDF 引擎由 VRN ⑥e 以子行程唯讀呼叫(VDF 失敗 → VRN 黃,不停)✅ |
| UP-1.2 | 禁止:VRN 掛掉使 VDF 停 · VDF 掛掉使 VCGC 停 · VCGC 掛掉造成資料遺失 | ◐ VRN 側成立(VDF / VCGC 不可用時 VRN 照跑、SSOT 號留空等核發);VDF ↔ VCGC 方向 — |
| UP-1.3 | Single Sign-On:共帳號 · 不共執行流程(Shared Identity ≠ Shared Runtime) | ✗ 沒有任何 SSO 實作證據(現在「同一套帳」= 同一治理帳冊)— VCGC 階段 |

## 二、UI

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-2.1 | Matrix First:Card → Grid → Table → Text;禁止文字堆疊 / 流水帳 / 長段落 | ◐ VRN Workbench v0107:驗證燈格 · 共識矩陣 · Basic Info 合併矩陣 · 收尾頁卡片;交接頁 / 工作計畫仍是文字區塊 |
| UP-2.2 | 95% 以上操作不需鍵盤;能拖曳不輸入;能推論不詢問 | ◐ Windows 選檔 / 選夾(vrn2://pick)✅;拖曳輸入待實測(F4);人工核對仍需打 `--confirm` |
| UP-2.3 | 主要功能 ≤ 3 click(理想 1);> 5 click = UX 缺陷 | ? 未量測;現況主流程 = 貼一行 → 收尾頁自動開 |

## 三、VRN

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-3.1 | 輸入只允許 Windows IO / Drag & Drop | ◐ Windows IO ✅ · 拖曳待實測(F4) |
| UP-3.2 | Smart Grouping(檔名 · 容量 · 格式 · 日期 · Hash)→ Input List · Possible Duplicate 自動標示 | ◐ 矩陣一:淡黃 = 時間 / 格式 / 容量相同(候選)· 淡綠 = SHA-256 完全相同 ✅;名稱相似 + 同報告日 · 同個股 + 券商 + 日期 的分群規則見收尾規格 §6,未全做 |
| UP-3.3 | 直接預覽 PDF / Word / Image,不需額外開程式 | ✗ 現在點檔名是用 Windows 關聯程式開 |
| UP-3.4 | 輸出統一 PARQUET;CSV / Excel 不得為主格式 | ✅ 增量庫 DuckDB + Parquet 正本;FinancialAligned Parquet 寫不出(F1)已由 HistoryAlign v0103 修(v0172) |

## 四、VDF(只列 · VDF 負責)

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-4.1 | 資料工廠:Transform · Normalize · Validate · Export;Pipeline 化 · 批次化 · 並行化 | — |
| UP-4.2 | Temp Batch Fetching:Chunk · Streaming · Incremental Loading,避免大檔爆 RAM | — (VDF 已有增量:價格每輪重抓 · 財報只補缺 · 溢寫夾;是否全覆蓋由 VDF 階段核實) |

## 五、VCGC(只列 · VCGC 負責)

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-5.1 | VCGC 不執行,只治理:SSOT · Regex · Synonym · Policy · Conflict | — |
| UP-5.2 | Conflict Center:欄位 / 名稱 / 同義字 / Regex / 政策衝突 · 自動編號 `CFG-000001…` · 每筆附來源 · 影響範圍 · 優先級 · 修復建議 | — **注意衝突**:收尾規格 §2 記「不另立 CFG- 新編號體系 · 沿用 VCGC 既有 AutoCode / Component Inventory」;要不要開 `CFG-` 前綴由 VCGC 裁定(VRN 不代決)|
| UP-5.3 | 待核號清零 | — 桌機 02:50:待核號 500 · 提案 17 · 自撞 0(VRN 只讀等待) |

## 六、網路工具

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-6.1 | Web / API / RSS / Search / News / Public Data 統一納管 · 禁止 VRN / VDF 各一套規則 · VCGC Network Registry 統一管理 | ◐ VRN ⑥f 共識經 SUP_MDL740_NetUnified v0119(桌機收據實證)✅;共用 MarketFetch v0112 有非拒絕錯誤時的直連支路 — VDF / VCGC(VRN 唯讀不改) |
| UP-6.2 | 網路工具支援不受阻 | ◐ 同意閘 `VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` 只由操作員設(政策 · 不代設);閘關時 VRN 用碟上快照補位並標 ASOF |

## 七、資料庫

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-7.1 | Primary Format = PARQUET | ✅ |
| UP-7.2 | Export Layer:CSV(UTF-8 BOM)· Google Sheets · JSON | ◐ CSV BOM + 公式前綴轉義 ✅ · JSON ✅ · Google Sheets 走可匯入 CSV(沒有直接寫入 API) |
| UP-7.3 | 欄位語意清楚(單位 / 刻度) | ✅ v0172:`UPSIDE_ADJ`(純小數)新增 · 舊欄 `UPSIDE_PCT(ADJ)`(百分數)保留並標註 · `VRN2_Combined_columns_latest.json` |

## 八、穩定性

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-8.1 | Crash Recovery 100% · Auto Resume 100% · Rollback 100% · Audit Trace 100% | ◐ Rollback:⑧ 完成判定通過 → 鎖定 + backup/ 快照 ✅;Audit:逐步收據 + 收尾收據 + 貼回包 ✅;Auto Resume:過期鎖自動清 · repair 只重跑需要的步驟 ◐;百分比 ? 未量測 |
| UP-8.2 | 任何操作可回溯 · 可還原 · 有 Log | ✅ VRN 收據 / 日誌 / 封存;同名不同內容不覆寫 |

## 九、Git

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-9.1 | Issue → Root Cause → Fix → Test → Commit → Regression → Merge | ✅ VRN 每輪:根因寫進發行清單 → 自測 / 端到端 → 推分支 → 操作員合併 PR |
| UP-9.2 | 禁止直接改 Main · 未測試 Commit · 大雜燴 Commit | ✅ 不推 main · 推前自測;◐ 一輪一個提交但含多個模組(同一主題的修正 + 發行夾) |

## 十、九頭龍零容忍

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-10.1 | 修一個長出更多 → 立即停止;不得流程分叉 · 特殊規則堆疊 · 跨系統依賴 · 隱藏耦合 · 不可控例外 | ◐ add-only 薄尾 · 前版不動 ✅;兩條 VRN 工作線同號不同內容(v0124 後)= 實際發生過的九頭龍 → 已合併 main、本線跳號、出號前查兩邊 ✅;Workbench v0105 沒帶加速器標記被桌機 accelfix 複製成 v0106 → v0107 起自帶標記並跳過複本 ✅ |

## 十一、故障復原(Disaster Recovery)

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-11.1 | RPO ≈ 0:崩潰 / 重開機 / 斷網 / API 失敗 / 斷電不得丟已完成結果 · Input List · 流程狀態 | ◐ 輸出 tmp → 換上(不留半檔)✅;Input List 落盤 `VRN2_Input_latest.json` ✅;流程狀態 = 收據(步驟級)◐ |
| UP-11.2 | Auto Checkpoint(步驟 · 已完成 · 狀態 · 進度 · 輸出位置)每 30 秒或每 500 筆 | ✗ 沒有定時 / 定筆數 checkpoint;現在是步驟級收據 + 每份報告中間結果寫 TEMP 溢寫夾 |
| UP-11.3 | Resume Anywhere:重開恢復 ≥ 95% 進度 | ◐ repair 模式只補缺的步驟;共識沿用當天已抓的 payload;⑥e 增量 · 財報只補缺;整輪中途斷掉要重跑該輪 |
| UP-11.4 | 單點故障零容忍:設定檔 · SSOT · Regex · Metadata · Pipeline Queue 都有備份 · 版本史 · 回滾點 | ◐ VRN 自己的冊有 backup/ 快照;SSOT / Regex 正本在 VCGC — |
| UP-11.5 | 啟動自檢 · 能修就修 · 不能修發 Incident ID(例 INC-20261102-0001) | ◐ RoundAll 診斷 → ⑤ 自動修 ✅;不能修的列在收尾頁並分負責方 ✅;**沒有 INC- 編號**(編號體系屬 VCGC)✗ |
| UP-11.6 | Recovery Success ≥ 99% · Recovery Time ≤ 5 分 · Checkpoint Restore ≥ 95% · Data Loss = 0 | ? 未量測(repair 實測幾分鐘;成功率沒有統計) |

## 十二、壓力測試

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-12.1 | VRN:PDF 1 / 100 / 1,000 / 10,000 份 · 10 MB ~ 10 GB+ · 混合格式同時輸入 · 量 RAM / CPU / 速度 / 穩定 | ✗ 最大實跑:桌機 52 份 PDF + 201 影像 + 7 Word + 1 TXT(輸出冊約 9 分鐘);1,000+ 份未測 |
| UP-12.2 | VDF:10 萬 / 100 萬 / 1,000 萬筆 · 不阻塞 · 不爆 Queue · 不 OOM | — |
| UP-12.3 | VCGC:SSOT 10 萬 ~ 1,000 萬條 · Synonym 100 萬+ · Regex 10 萬+ 的查詢 / 衝突 / 套用速度 | — |
| UP-12.4 | 燒機 24 h / 72 h / 168 h · 無 Memory / Handle / Thread Leak | ✗ |
| UP-12.5 | 故障注入:斷網 30 秒 / 5 分 / 30 分 · 磁碟滿 / 唯讀 / 移除 · API 404 / 429 / 500 / 503 · DB 斷線 / 逾時 / 連線池耗盡 | ◐ 自測有:網路 DENY · 404 · 一時抓不到重試 · 過期擷取鎖 · 逾時 · 讀檔被鎖重試 · 舊套件夾權限讀不到;磁碟滿 / 移除 · 429 / 503 · DB 連線池 ✗ |

## 十三、Final Gate(正式 Release 前)

| 編號 | 指標 | 現況(VRN) |
|---|---|---|
| UP-13.1 | Critical Bug = 0 · High Severity Bug = 0 | ? 沒有嚴重度分級的缺陷冊;收尾頁 VRN 待修 0(桌機 02:50) |
| UP-13.2 | Data Loss = 0 · Hydra Risk = 0 | ◐ 見 UP-11.1 / UP-10.1 |
| UP-13.3 | Recovery ≥ 99% · Checkpoint Restore ≥ 95% | ? |
| UP-13.4 | Memory / Thread Leak = 0 · Unhandled Exception = 0 · 7-Day Burn-in PASS | ✗ 未測 |
| UP-13.5 | VRN / VDF / VCGC PASS · Git Rollback · DR · Stress · Load · Regression PASS | ◐ VRN Regression(自測 + 端到端)✅;其餘 ✗ / — |

## 十四 ~ 二十、SDD(Self-Driving Design · 自適應 · 自修復 · 自優化)

| 編號 | 要求 | 現況 |
|---|---|---|
| UP-14.1 | 使用者少思考 · 能推測不提問 · 能預載不等待(Input List 建立時同步做預覽索引 / Metadata / Hash / Grouping Cache) | ◐ 去重矩陣在渲染時算 Hash;預覽索引 ✗ |
| UP-15.1 | 90% 流程免設定 · 拖入 → 確認 → 完成 | ◐ 見 UP-2.2 |
| UP-15.2 | 自動路徑判斷(PDF → PDF Pipeline · Excel → Data Pipeline · 影像 → OCR);禁止「請選擇格式 / 類型 / 流程」 | ◐ VRN 主體只擷取 PDF(個股報告);Word / TXT / 影像「收下未擷取」誠實標示;非個股報告(產業 / 晨會 / 總經 / 訊息)是另一個摘要器(NON_STOCK v0300)的範圍,依賴缺件(見 §備註) |
| UP-15.3 | 資料量決定 Single / Multi Thread / Batch | ◐ VRN 平行 3 路擷取 / 驗收 · 驗證器 6 路;沒有依資料量自動切換 |
| UP-16.1 | 依 CPU / RAM / Storage / GPU / Network 自動 Low Resource / Performance Mode | ◐ 子行程上限 / 逾時 / 心跳 ✅;VDF 記憶體閘 + 溢寫(VDF);自動模式切換 ✗ |
| UP-17.1 | Adaptive UI:新手只留「開始 · 確認 · 輸出」· 進階自動展開 | ✗ |
| UP-18.1 | 可學操作習慣;**禁止**自行改政策 / 規則 / SSOT / Regex / 同義字 —— 治理層經 VCGC 核准 | ✅ VRN 只送提案(ssot_id 空白)· 等 VCGC 核發;不自建正式同義字 / 規則 |
| UP-19.1 | RAM / CPU / Queue 過高或太慢 → 降載 · 切批 · 延遲 · 暫停非核心;優先保護資料與流程完整 | ◐ 非關鍵步驟逾時 → 黃不擋;沒有動態降載 |
| UP-20.1 | 手動輸入 −95% · 點擊 ≤ 3 · 自動分類 / 群組 ≥ 90% · 自動修復 ≥ 80% · 故障恢復 ≥ 99% · 資料遺失 0 · 自動決策 ≥ 90% · SSOT 衝突 0 · Critical 0 | ? 皆未量測;能量的先列:SSOT 自撞 0(✅)· 待核號 500(VCGC) |

## 狀態機(操作員給的 SDD 流程 · 對照 VRN 現有步驟)

| 操作員狀態 | VRN 現有對應 |
|---|---|
| Environment Detection → Resource Assessment → Low / Standard / Performance Mode | ③ 環境檢查(只檢查 · 缺的交 VCGC InstallGate)· 子行程上限;模式切換 ✗ |
| Input Acquisition(Drag & Drop · Windows IO · Batch)→ Scanner → Metadata → Smart Grouping → Duplicate Detection → User Confirmation | ②b 輸入來源 · 矩陣一(容量 / 時間 / 格式 / SHA-256)· Confirm Input List(Workbench) |
| VRN:IDLE → SCANNING → GROUPING → PREVIEW_READY → USER_CONFIRM → PROCESSING → VALIDATING → EXPORTING → PARQUET_COMPLETED → FINISHED | ⑦ 擷取 → ⑪ 獨立驗證 / 四點原文核對 → ⑬ 增量庫(Parquet)→ ⑧ 完成判定 + 收尾頁;PREVIEW_READY ✗ |
| Recovery:INCIDENT → CHECKPOINT RESTORE → (失敗)ROLLBACK → SAFE RECOVERY → RESUME | RoundAll 診斷 → ⑤ 自動修 → 收尾頁;CHECKPOINT RESTORE ✗(步驟級收據代替) |
| Load Test:監看 CPU / RAM / Disk / Queue / Threads → Threshold → Adaptive Scaling → Batch Reduce | ✗ |
| VCGC Governance:SSOT / Regex / Policy → Conflict Check → 無衝突繼續 / 有衝突發 CFG-ID → Governance Review | — VCGC |

## 待辦(依收尾順序 VRN → VDF → VCGC · 每階段全 PASS 才進下一個 · 不擴張)

| 順序 | 負責 | 項目(只列 · 本輪不動工的標「下一階段」) |
|---|---|---|
| 1 | VRN | ✅ v0172:F1 Parquet 型別 · F2 UPSIDE_ADJ 小數欄(舊欄保留標註)· F3 Basic Info 合併檢視 |
| 2 | 操作員 | MQ-1560 四點看原圖後 `--confirm H-fd2ea35f`(收尾只剩這件人工) |
| 3 | VRN · 下一階段 | F4 拖曳 / 刪除勾選接後端 · F5 匯出給 Parquet 檔 · UP-3.3 內建預覽 · UP-11.2 checkpoint · UP-12.1 壓測(100 / 1,000 份) |
| 4 | VDF | UP-4.x · UP-6.1 外連 100% 經網路工具的執行收據 · UP-12.2 |
| 5 | VCGC | UP-1.3 SSO · UP-5.x Conflict Center(含 CFG- 是否開號的裁定)· 待核號 500 · UP-11.4 / 11.5 INC- 編號 · UP-12.3 · Auto Deploy |

## 備註(本輪核實的相關事實)

- **非個股摘要器**(VIA_NON_STOCK_SUMMARIZER_ENGINE v0300 · 操作員附件 · 另一個引擎):桌機實跑預覽(RESULTS_PREVIEW.md)可見品質待修點 —— 有一點開頭混入頁碼 / 行號的數字殘字、Messenger 列有 `P4: nan`、晨會摘要四點來自不同公司段落卻併在同一份。它的依賴 `internal/NON_STOCK_CORE_v0200.py` 與 `reuse/vrn2/` 不在任何倉 / 上傳(zip `VIA_NON_STOCK_SUMMARIZER_ENGINE_v0300.zip` SHA-256 `8d7d2cef673f…` 未上傳)→ 本線無法重現;屬 VRN 之後的階段,先記錄。
- **ClickStart v0103**(另一線 · 原生工作台):根因是 Windows venv 啟動器父子行程 PID 不同、被監看端誤判逾時;它內含的 `VRN2_RoundAll_v0127.py` 雜湊 `bdff099737f6…` = 本線 v0127(相容)。之前另一線的 ClickStart 結束碼 3221225786 = 0xC000013A(STATUS_CONTROL_C_EXIT:視窗被關或 Ctrl+C),不是 VRN 引擎錯誤。本線只讀不改。
- **Graphify v0101**:修桌機「Documents\VeritasIntelligenceAnalytics 存在但不是 VIA 根 → 4 系統全灰、總結印綠」(見 `via_graphify_v0101/`)。
- **Workbench 頁面 13 MB**(桌機 02:50):頁內嵌全部冊的資料,重渲染超過 60 秒 —— 頁面主體是另一線的 v0104;記為 UP-0.1「最少等待」的待辦,不在本輪改另一線的碼。
