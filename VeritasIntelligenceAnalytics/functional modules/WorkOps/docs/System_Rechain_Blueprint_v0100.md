# WorkOps × Forge 系統重串接藍圖 v0100(2026-08-08)

操作員裁決:「將功能拆開重新檢視,去重、補不足的功能及工具後,再重新串接成系統。」
本文即拆解 → 去重裁定 → 補缺 → 重串接的正本記錄(只增不減;裁定變更以新版藍圖追加)。

---

## 一、功能拆解總表(重檢)

### A. 資料取得層
| 功能 | 工具 | 治理 |
|---|---|---|
| Outlook 全資料夾時段唯讀掃描(含內文) | `Invoke-VIA-Outlook-TimeRange-ReadOnly.ps1`(scanrange) | 唯讀/user-scope/原件零觸碰 |
| Outlook 即時唯讀拉取(工作台按鈕) | Forge `via_connect.LocalOutlookConnector`(COM;CoInit 已修) | 唯讀 |
| 控制表拖放歸一化上傳 | 指揮板①拖放區(Big5/UTF-8 自辨) | 不改控管表 |
| 行事曆唯讀讀取 | Forge `LocalOutlookCalendar` | 唯讀 |

### B. 語料統一層
| 功能 | 工具 |
|---|---|
| 多世代 CSV schema 統一 → corpus.csv | `workops_corpus_bridge.py`(ENG-019) |
| WorkOps 語料 → Forge 統一 records(結合層) | `via_manager._load_workops_corpus`(唯讀,保留編號+名稱) |

### C. 智慧引擎層
| 功能 | 工具 |
|---|---|
| 修復/五維分類/thread/案件/E01-E12 庫/PMBOK 匯出 | `email_super_engine.py`(CAP-001..007) |
| NLP(TF-IDF/聚類/監督建議)/DM(延遲/Pareto/週量)/PM(DFG/一致性/SLA) | `engine_analytics.py` v1.3(CAP-008..010;pm4py+可攜 dot) |
| 行動資料庫 | `email_action_db.py` |
| 命名核對(編號不變,名稱別名層) | `workops_namer.py`(ENG-023) |

### D. 環境治理層
| 功能 | 工具 |
|---|---|
| 中央治理安裝(gatekeeper 決策→執行) | `workops_envmanager_bridge.py`(ENG-020)+ PmSetup v0103 |
| graphviz 可攜版(官方 API 動態+sha256) | `workops_graphviz_setup.py`(ENG-021) |
| Forge 自域 .venv(office/pdf/連接器依賴) | `Start-VIA.ps1`(邊界:不與 .venv_pm 混用) |

### E. 呈現/操作層
| 功能 | 工具 |
|---|---|
| 六頁指揮板(專案/追蹤哨/範疇/VMT/Copilot/⑥矩陣) | `Invoke-VIA-WorkOps-CommandBoard` v0111 |
| 智慧工作台 12 分頁(擷取/網格/矩陣/全景/流程/關係人/匯出/連結/郵箱/專案) | Forge `via_server.py` + `ui/index.html` |
| 分析報告(編號·名稱) | `analytics_report.html` / `engine_report.html` |
| 週報/KPI/toast/靜默/vbs | 板一支到底附帶 |

### F. 指揮層
| 功能 | 工具 |
|---|---|
| ALL 總指揮(環境自癒→板→深鏈→總結) | `Invoke-VIA-WorkOps-All`(ENG-022) |
| 動詞路由(全動態解析最新版) | `via-workops.cmd`(help 動詞可查全表)/ `via-forge.cmd` v002 |

---

## 二、去重裁定(正本 vs 消費者)

| 重疊功能 | 正本(canonical) | 消費者/替代路 | 裁定理由 |
|---|---|---|---|
| 郵件語料 | WorkOps 深度鏈(scanrange→bridge→super_engine.db) | 工作台 fusion 自動載入;oneclick 保留為 UI 內主動拉 | 深度鏈含逐封內文+E 庫+編號,批次快照可稽核 |
| 案件編號 | super_engine CASE + 板 THR/WOP side-car 帳本 | Forge MailForge case_id 於 fusion 時被 WorkOps CASE 覆蓋 | 編號不變鐵律,單一來源 |
| 名稱 | `workops_naming.json`(namer 帳本) | 工作台 cluster_label 消費之;分析報告七表顯示 | 核對迴圈只能有一本帳 |
| 回覆狀態 | 板②追蹤哨(THR 佇列+草稿;管控主線) | 工作台 replystatus(同語料分析視圖) | 管控動作(草稿/圈選)在板;檢視在台 |
| 利害關係人 | super_engine S4(87 對口+初評) | 工作台 stakeholders 視圖 | 同上 |
| 流程探勘 | analytics PM(pm4py DFG png+一致性+SLA) | 工作台 pmine 互動視圖 | 報表正本可歸檔;互動為輔 |
| 匯出 | engine S5(WorkMatrix/PMBOK xlsx/事件流) | Forge sink 多格式(工作台匯出面) | 各服其面,不合併 |
| 環境 | EnvManager 橋管 `.venv_pm`;Forge 自管 `.venv` | — | 兩域依賴不同(pm4py vs office/pdf),隔離即治理 |
| 分段動詞(bridge/engine/analytics/scanrange) | 保留 | — | 回退路設計,非重複 |

## 三、補不足(本輪已補 / 候補)

已補:⑥矩陣收錄 EnvManager/graphviz/命名/工作台結合/ALL 五列即時狀態(板 v0111);
`via-workops help` 動詞總表;工作台 CoInitialize 崩潰修;SyntaxWarning 清除;結合層(共用語料)。

候補(待操作員裁示):THR↔CASE 跨帳本對映(需 ConversationID 入語料);Outlook 資料夾
歸戶 UI;關鍵字核對 UI;必回選擇題範本入草稿線;Voice-Minutes 提示入 Copilot 卡;
深度輸出入板分頁;hub Forge 磁貼直達活服務;控制表仍未放(專案 0)。

## 四、重新串接圖

```
                    ┌────────────── via-workops all(ENG-022 總指揮)──────────────┐
                    │ [0] 環境自癒:pmsetup(EnvManager)· dotsetup · envmgr 健檢 │
                    └───────────────┬───────────────────────┬────────────────────┘
                                    ▼                       ▼
        ┌── 指揮板一支到底(v0111)──┐        ┌── 深度鏈(Deep v0101)──────────┐
        │ 掃描→對帳→THR/WOP 編號→   │        │ scanrange→語料橋→super_engine→ │
        │ 佇列→六頁板+週報+KPI      │        │ analytics(DFG)→命名提議        │
        └────────────┬─────────────┘        └──────┬─────────────────────────┘
                     │   side-car 帳本:id_ledger · workops_naming(names apply 核對)
                     ▼                              ▼
        ┌──────────────── 共 用 語 料(super_engine.db + 命名帳本)───────────────┐
        └──────┬─────────────────────────────────────────────────┬──────────────┘
               ▼                                                 ▼
   分析報告(編號·名稱七表)                     智慧工作台 via-workops workbench
                                                (Forge 12 分頁;fusion 唯讀消費;
                                                 一鍵讀取=UI 內主動唯讀拉取)
```

紅線不變:絕不代寄 · Outlook 原件/分類零觸碰 · 編號永不變 · 基底零觸碰 · 只增不減。

---

## 五、補遺(2026-08-09 補不足令落地)

**帳本互鏈完成**:namer v0101 於 propose 尾端自動做 THR↔CASE 對映(正規化主旨
比對板側 mails.csv+id_ledger × 深鏈 E01;剝 Re/Fw/[THR-#] 標籤)→ side-car
`out/thr_case_map.json`;THR 繼承所連 CASE 名稱入命名帳本(approved 永不覆蓋,
LINK/REPROPOSE-LINK 入 history),核對表單表涵蓋兩套編號。原候補「THR↔CASE
跨帳本對映」結案 — 不需 ConversationID 入語料(主旨錨足矣,誠實比對不硬連)。

**關係網絡圖落地**:analytics 新增利害關係人網絡 SVG(同案共現=邊、信量=節點,
圓形佈局純 stdlib)— 原候補「networkx 關係圖」以零依賴方式結案,networkx 免引入
(去重原則);對口<3 或無共現誠實不出圖。

**圈選勾選閉環**(同日 v0112):圈選件=必回選擇題範本+Outlook 原生投票鈕;
控管表庫根後備路。候補清單餘:via-ocr 重段代跑、via_fetch_prices→via-pipe、
rapidfuzz 併案、取消訂閱清單、多帳號聚合、hub 磁貼 — 候令。
