# 郵件智能大引擎 · 能力總體規劃書(只增不減版)
版本 v2.0-PLAN · 2026-07-13
治理原則:**只增不減**——所有既有模組、資料表、規則、輸出檔一律保留;新能力以「新增表/新增欄/新增模組/新增視圖」方式疊加,永不 ALTER 破壞、永不 DROP。

---

## 一、能力登錄冊(Capability Registry)— 現況盤點

| 編號 | 能力 | 狀態 | 載體 |
|---|---|---|---|
| CAP-001 | 多格式讀取+四道修復(編碼鏈/亂碼/HTML/雜訊) | ✅ 已建成已測 | email_super_engine v1.1 |
| CAP-002 | 五維多重分類(CASE/TOPIC/ACTION/URGENCY/PMAREA) | ✅ 已建成已測 | 同上 |
| CAP-003 | 外掛規則檔 rules_addendum.json(規則只增不減) | ✅ 已建成已測 | 同上 |
| CAP-004 | 期限正規化(7/15、EOW→ISO 日期) | ✅ 已建成已測 | 同上 |
| CAP-005 | 統一資料庫 E01–E07(append-only) | ✅ 已建成已測 | super_engine.db |
| CAP-006 | 利害關係人庫+回覆延遲/兌現率+自動初評 | ✅ 已建成已測 | E04/E05/E06 |
| CAP-007 | PMBOK 六表 xlsx / WorkMatrix CSV / 事件流輸出 | ✅ 已建成已測 | S5 匯出層 |
| CAP-008 | NLP(jieba/TF-IDF/TextRank/聚類auto-k/監督式建議/相似thread) | ✅ 已建成已測 | engine_analytics v1.1 |
| CAP-009 | DM(延遲離群/週信量/Pareto/共現) | ✅ 已建成已測 | 同上 |
| CAP-010 | PM(DFG等待時間/催辦迴圈/一致性/變體/工期/SLA違約) | ✅ 已建成已測 | 同上 |
| CAP-011 | 系統管理器 HTML UI(即時進度同步) | ✅ 已建成已測 | engine_manager v1.1 |
| CAP-012 | WorkMatrix 強矩陣範本+Outlook 行事曆同步 | ✅ 已交付 | WorkMatrix.xlsx / PS1 |
| CAP-013 | 合規自動化路線(Power Automate/Power Query) | ✅ SOP 已交付 | SOP_Compliant_Automation.md |

## 二、新能力吸收對照表(上傳規劃 → 落地設計)

> 原則:上傳文件的每個概念都對照「既有能力/缺口/落地方式/風險註記」,概念全收、實作務實。

| 上傳概念 | 既有對應 | 缺口 → 新增(只增) | 誠實註記 |
|---|---|---|---|
| **UPIM 大矩陣(SSOT)** | E01–E07 已是實質 SSOT | 新增 **V_UPIM 統一視圖**:JOIN 七表輸出單一寬表,供 pivot/儀表板/投影片唯一來源 | 用 VIEW 不用新表,零資料重複 |
| **Auto-Index 自動編號器** | CASE-#### 已有 | 新增 **E10_INDEX_REGISTRY**:`DG-IN-{TYPE}-{blake2s3碼}` 全類型編號(PRJ/EML/SIG/WKF/RSK/EXC/CTL),雜湊輸入存表內 | 對齊 VIA MI 編碼 LL#30:hash 輸入必須入 SSOT 否則編號不可驗證 |
| **畫押系統(Yes/No/TBA)** | 無 | 新增 **E08_SIGNATURE** 表 + 三級合規收集路徑(見 §四) | ⚠️ Actionable Message **必須 IT 註冊租戶 Provider,一定驚動 IT**;預設走 A/B 路徑 |
| **Email_Event / Stakeholder Schema** | E01/E04 已有 | E04 **新增欄**:role/influence/responsibility(ALTER ADD COLUMN,只增欄) | — |
| **異常偵測(落後/未回覆/完成不一致)** | Stale>14d、SLA違約已有 | 新增 **E09_EXCEPTION** 表 + Mismatch 偵測器(流程完成但行動未結) | — |
| **催辦引擎(24/48/72h 升級梯)** | PS 行事曆 R1–R3 已有 | 新增升級梯規則模組:逾時分級→提醒/強提醒/升級PM/升級主管,產出**催辦草稿**(不自動寄) | 自動寄信=治理紅線,引擎只出草稿人工寄 |
| **Workflow 自動推進** | 狀態欄已有 | 畫押 Yes→行動結案 / No→標卡住+升級 / TBA→維持+催辦排程(寫 E07 新列,不改舊列) | — |
| **風險/成功率預測(28%~92%)** | 規則式健康旗標已有 | 分兩期:**P1 規則式健康分**(權重公開可稽核);**P2 ML 預測**僅在累積 ≥50 筆已標結果後啟用 | ⚠️ 上傳文件的成功率數字為**虛構示意**;依證據分級,預測分數一律標 **Syn/T4、上限59**,嚴禁當 V 級呈報 |
| **Auto-Reply 引擎** | 無 | 新增回覆**草稿生成器**:標準版/畫押請求版/升級版三模板,含 SCF 畫押格式 | 只生成草稿,永不自動發送 |
| **七案健康度總表/Control Tower** | manager UI 已有 | manager 新增「健康度」頁籤:落後/未回覆/不一致三燈號矩陣(讀 E09+V_UPIM) | — |
| **自動週報** | engine_report.html 已有 | 新增 **weekly_report 生成器**:七段式(總覽/健康矩陣/畫押/催辦/風險/預測/行動建議) | 預測段落強制附證據等級聲明 |
| **不動主管原表** | 引擎本就唯讀 | 新增 CTL 編號:讀主管控制表→外部編號映射存 E10,**永不回寫原表** | 0 侵入原則制度化 |

## 三、統一編號規格(Auto-Index,對齊 VIA 慣例)

```
格式:DG-IN-{TYPE}-{SEQ3}          # 人讀序號
驗證:blake2s("DG-IN|{TYPE}|{自然鍵}", digest=3).hexUpper   # 機器可驗碼
TYPE ∈ {PRJ 專案, EML 郵件, SIG 畫押, WKF 流程, RSK 風險, EXC 異常, CTL 控制表項}
```
E10_INDEX_REGISTRY 欄位:index_code / type / seq / natural_key / blake2s_code / created_at。
**自然鍵必須入表**(LL#30),否則編號不可回溯驗證。序號只增不重用。

## 四、畫押收集三級路徑(合規分級,誠實標註)

| 級 | 方式 | 需要 IT? | 說明 |
|---|---|---|---|
| **A(預設)** | **格式紀律**:回信首行照 SCF 格式 `Tony(2026/07/13): Yes/No/TBA`,引擎 regex 解析入 E08 | ❌ 不需要 | 零技術門檻,今天就能上路;引擎新增 SCF 解析器 |
| **B(半自動)** | **Power Automate Approvals**:M365 內建核准功能,對方點按鈕,結果表自動落 SharePoint,引擎讀取 | ❌ 不需要 | 有真下拉/按鈕體驗,標準連接器即可 |
| **C(全自動)** | Outlook **Actionable Message**(Adaptive Card 下拉) | ⚠️ **需要** | Provider 須向微軟註冊+租戶管理員核准回呼網域——**一定驚動 IT**,列為遠期選項 |

SCF 解析規則(A 路徑,入引擎):`^(?P<name>[\w\u4e00-\u9fff .]+)\s*[（(](?P<date>\d{4}/\d{1,2}/\d{1,2})[)）]\s*[::]\s*(?P<decision>Yes|No|TBA)`

## 五、新增資料結構(全部只增)

```
E08_SIGNATURE   sig_id / index_code / mail_id / signer_email / signer_name /
                decision(Yes|No|TBA) / sign_date / source(SCF|Approvals|Card) /
                sla_hours / created_at
E09_EXCEPTION   exc_id / index_code / case_seq / exc_type(DELAY|NO_REPLY|MISMATCH) /
                detail / risk_level / detected_at / status(待稽核|催辦中|已升級|已結)
E10_INDEX_REGISTRY  (見 §三)
E04 增欄        role / influence_level / responsibility_area
V_UPIM(視圖)    案件×分類×狀態×利害關係人×畫押×異常×期限 單一寬表
V_HEALTH(視圖)  每案三燈號(落後/未回覆/不一致)+未結數+SLA 逾期數
```

## 六、版本路線圖(每版皆為疊加)

| 版本 | 內容 | 前置 |
|---|---|---|
| **v1.2** | E08/E09/E10 建表、SCF 畫押解析器、Mismatch 偵測、V_UPIM/V_HEALTH 視圖、Auto-Index | 無,立即可做 |
| **v1.3** | 催辦升級梯(草稿生成)、回覆草稿三模板、週報生成器、manager 健康度頁籤 | v1.2 |
| **v1.4** | Power Automate Approvals 讀取器(B 路徑)、規則式健康分 P1 | v1.2 + SharePoint 表 |
| **v2.0** | Control Tower 2.0(全鏈路追蹤圖 PRJ→EML→SIG→WKF→RSK→EXC)、ML 預測 P2 | 累積 ≥50 筆已標結果 |

## 七、治理紅線(不可逾越)

1. **永不自動發送郵件**——引擎只產草稿,寄出永遠是人。
2. **永不回寫主管原表**——原表唯讀,編號與狀態存於引擎側。
3. **永不呈報虛構百分比**——預測分數一律標 Syn/T4(上限 59),週報附證據等級聲明;規則式健康分公開權重供稽核。
4. **DDL 只增**——新表、新欄(ADD COLUMN)、新視圖;禁止 ALTER 改型、禁止 DROP;棄用者標 DORMANT。
5. **IT 邊界**——A/B 路徑與全部引擎功能不需 IT;唯 C 路徑(Actionable Message)需 IT,啟動前必須明確簽核。
