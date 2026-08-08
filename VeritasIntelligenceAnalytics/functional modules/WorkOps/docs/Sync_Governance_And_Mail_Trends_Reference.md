# 同步治理與 2026 郵件管理趨勢對照(參考吸收版 v0100 · 2026-08-08)

來源:操作員提供之四份外部研究(2026 郵件管理趨勢、Top20 免費 Outlook 工具、
資料同步錯誤排解、雙向同步衝突/時鐘漂移最佳實踐)。本檔為去重吸收後的精華 +
與 WorkOps/平台現況的誠實對照。只增不減。

---

## 一、2026 郵件管理趨勢 × WorkOps 現況對照

| 趨勢功能 | WorkOps 現況 | 判定 |
|---|---|---|
| AI 自動分類與優先排序 | 超級引擎五維分類 + 追蹤哨待回優先 + 延遲分型(人/系統) | 已有 |
| AI 草稿與回覆建議(多語) | drafts 佇列預填(繁/简/EN 三語;絕不代寄=比市售更嚴) | 已有 |
| 智能 Follow-up 提醒 | ≥3 天未回自動入佇列 + [THR-#] 編號閉環 | 已有 |
| 批量清理與取消訂閱 | bulk_senders 分型(系統/電子報不列升級);**取消訂閱清單=候補** | 部分 |
| 團隊共用收件匣/範本 | Templates 動詞(單機);團隊共用需 M365 Group(雲端線,休眠) | 候雲端核准 |
| 行事曆整合 | matrixsync(唯一寫入,主動觸發)+ Forge 行事曆唯讀 | 已有 |
| 多帳號聚合 | PMIS adapters(IMAP/OAuth/Outlook desktop)已在庫;聚合未串 | 候補 |
| 隱私與稽核軌跡 | append-only 稽核 + 絕不代寄 + 原件零觸碰 | 已有(強於市售) |

市售工具(SaneBox/Boomerang/Clean Email…)均為雲端付費 — 平台以本機免費自建
等價功能為既定路線;Top20 免費 Outlook 工具中可借鑑者:Duplicate Remover(去重)、
Attachment Saver(附件批存)、Outlook Backup(PST 備援)— 均可由 scanrange/PMIS
attachments 演進承接,列候補。

## 二、同步錯誤六大類 × 通用排查 SOP(吸收)

類別:連接層(超時/DNS/TLS)、認證(401/鎖定/授權)、格式(型別/長度/日期/必填)、
一致性(雙向衝突/重複/部分失敗)、效能(超時/限流/鎖定)、業務邏輯(狀態機/依賴/觸發)。

SOP:網路 → 認證 → 資料 → 日誌 → 業務 → 效能(先粗排查後細定位)。
監控閾值:成功率>95%、延遲<5min、錯誤率<5%、重複<1%、MTTR<2h。
結構化錯誤日誌欄位:sync_id/timestamp/source/target/status/error_type/
affected_records/retry_count/resolution。

## 三、雙向同步衝突分層(吸收 — 平台已內建同思想)

1. **設計期避免**(最佳):唯一真相來源 SoT / 欄位級權威 / 單向設計 / 分片
   → 平台對應:重串接藍圖「正本 vs 消費者」裁定即 SoT 法;WorkOps↔工作台
   為單向消費(fusion 唯讀),天然無雙向衝突。
2. **偵測分類**:主鍵/更新/刪除/結構衝突。
3. **自動解決**:LWW(需防時鐘漂移)/系統優先級/欄位級合併/人工覆核/CRDT。
   → 平台對應:命名帳本=「approved 永不被 propose 覆蓋」即系統優先級;
   id_ledger 冪等 append=UPSERT 思想。
4. 衝突日誌審計(conflict_id/雙端值/policy/resolved_by)→ 平台 append-only 慣例一致。

**未來適用點**:msproject_io 回寫(SSOT↔MSP round-trip 已有對帳)與 matrixsync
若走向雙向,採欄位級權威表 + 業務時間戳+版本號+來源系統 ID 多重戳。

## 四、時鐘漂移三層防護(吸收)

1. 基礎:統一 NTP/Chrony 時源;Windows `w32tm /config /syncfromflags:domhier`;
   偏移監控(內網>10ms 告警)。
2. 邏輯時鐘:HLC(物理+邏輯計數器)/向量時鐘(因果追蹤)— 分布式場景才需。
3. 容錯:時間戳比較加 ±100ms 不確定預算;鎖加唯一標識不只靠過期;冪等用
   邏輯時鐘視窗。
→ 平台現況:單機 side-car 帳本無分布式時鐘問題;若未來多機共用帳本,
  依本節設計。誠實註:目前不過度建設。

## 五、本輪驗收快照(2026-08-08)

- PMIS-Lite test_stage1:操作員機 **47/47**(cwd 錨定修正後)
- via-ocr probe:操作員機 **9/10 段可用**(fitz/pdfplumber/pdfminer/camelot/
  PaddleOCR/pytesseract/tesseract/easyocr;僅 surya 選配缺)— 重 OCR 段
  真接火(via-ocr 代跑 paddle 段)列候補,候操作員令。

## 六、Top15 本地免費庫 × 平台去重裁定(2026-08-08 追加)

| 庫 | 平台現況 | 裁定 |
|---|---|---|
| duckdb / pyarrow | via_io 匯出已支援(選配);主庫=sqlite(super_engine/decision_log) | 已有(選配層) |
| pandas / scikit-learn / jieba | analytics venv 全配 | 已有 |
| pm4py / streamlit? | pm4py 在 .venv_pm;Streamlit 不採 — 平台 UI=單檔 HTML(免服務常駐) | 已有/不採 |
| plotly | VAP 域已有 | 已有 |
| networkx | 未在 — 關係網絡圖候補(工作台 stake 現以表格呈現) | 候補 |
| polars | 不採 — pandas 已為基底,雙 DataFrame 庫違反去重 | 不採 |
| pydantic | 不採(現階段)— 平台驗證用 schema.py/Pydantic 屬重依賴 | 不採 |
| rapidfuzz | 候補 — 現以 normalized subject+規則去重;模糊比對可強化併案偵測 | 候補 |
| APScheduler | 不採 — 排程=Windows 開機 vbs/工作排程器(零常駐服務) | 不採 |
| loguru | 不採 — Write-WopsLog/結構化 print 已定;雙日誌系統違反去重 | 不採 |
| tenacity | 不採 — 平台重試=launcher 指數退避(via-sync/push 迴圈) | 不採 |

原則:單機、本機免費、不常駐、不雙軌。候補(networkx/rapidfuzz)待實際需求觸發。

## 七、決策追蹤模組(ENG-027 · 本輪落地)

Decision & Action Log 落地為 `via-workops decisions`(sqlite side-car + DEC-#### 編號
+ append-only 歷史 + source 掛 THR/CASE + KPI 完成率/逾期/平均延遲 + utf8BOM 匯出);
會議記錄範本 docs/Meeting_Minutes_Template.md(議題→討論→決議→行動骨架,行動項目
一行指令入帳)。流程重建器藍圖(model_builder/visualizer/stakeholder_overlay)經去重
裁定:DFG/瓶頸/一致性=analytics 已有、PetriNet/互動 cockpit=工作台 pmine 已有、
stakeholder overlay=E04+工作台 stake 已有 — 不重建,缺口僅 networkx 關係圖(候補)。
