# VIA WorkOps 市場工具盤點與功能吸收裁決 v0100(2026/08)

操作員指令:檢視市場上各類提升工作效率及郵件管理工具,吸收同類功能。
本文件為 append-only 裁決紀錄;吸收=在地重作(local-free、唯讀、不代寄),非引入外部服務。

## 一、市場掃描(2026/08 主流工具 × 核心功能)

| 功能 | 市場代表 | WorkOps 現況 | 裁決 |
|---|---|---|---|
| AI/優先級收件匣分流 | Superhuman、SaneBox、Shortwave | 規則式分類(v001)+ 五級亮燈 | 已具備(本地規則式);雲端 AI 不引入 |
| 未回自動追蹤提醒 | Boomerang、Superhuman | 追蹤哨(≥3/7 天亮燈+主動跳出) | **已具備且更強**(草稿預填一次產生) |
| 主題自動歸串 | Shortwave bundles | 代號叢集歸納(v0101 ③頁) | 已具備 |
| 郵件轉任務 | Missive、Front、Asana | pending→草稿佇列;控管表建議 | 已具備(形式為佇列+建議) |
| 專案看板/時間線/負責人 | Monday、Asana、Jira | ①專案指揮(燈/負責人/建議) | 已具備核心;時間線=候選 backlog |
| **報表/儀表板** | Monday dashboards、Asana reporting | 無 | **本輪吸收:一鍵週報(v0102)** |
| **PLM 式項目編號** | Windchill/Teamcenter item numbering | 無 | **本輪吸收:WOP/THR side-car 帳本(v0102)** |
| 排程寄送/追蹤讀取 | Boomerang send-later、Mailtrack | 無 | 拒收:違反「不代寄」紅線與隱私原則 |
| 收件匣暫停/貪睡 | Boomerang、CMDK | 無 | 拒收:須改動使用者信箱狀態,違反「不動原件」 |
| 共享收件匣協作 | Front、Hiver、Gmelius | 無 | 暫緩:單人系統定位 |
| 自動化規則引擎 | SaneBox 過濾、Monday automations | v001 分類 + 對帳規則 | 已具備;mail_rules 表=候選 backlog |

來源:timetoreply/missiveapp/fyxer/work-management.org/thesoftwarescout/cmdk 2026 郵件工具評比;asana/monday/technologyadvice/inc 2026 PM 工具評比。

## 二、本輪吸收實作(v0102)

1. **PLM 式自動編號(side-car)**:專案 `WOP-####`、郵件串 `THR-#####`。
   - append-only 帳本 `out/workops_id_ledger.json`,依 案號/ConversationID 首見指配,冪等(重跑同號)。
   - **鐵則:編號只存在本系統與其輸出。Outlook 原件、分類、標籤、資料夾一概不動 — 尊重既有系統與原始資料。**
2. **一鍵週報**:每跑產出 `VIA_Reports/workops_run/VIA_WorkOps_WeeklyReport.html`(專案狀態+未回追蹤,含編號);`via-workops report` 直開。

## 三、候選 backlog(依操作員指示啟動)
- 時間線/甘特視圖(①頁擴充)
- mail_rules 使用者自訂規則表(關鍵字→專案歸戶)
- 週報自動排程(via-one 階段或 Windows 工作排程器)
