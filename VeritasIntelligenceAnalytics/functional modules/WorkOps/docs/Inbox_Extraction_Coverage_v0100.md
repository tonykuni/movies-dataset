# INBOX 四維擷取範圍對照表 v0100(2026-08-09)

操作員令:核對「系統從收件匣及 Outlook 資料夾擷取的資訊四大維度」規格與實際系統。
本文為逐項對照正本 — 每項標明落點產物與消費者;缺口誠實列出。

## 一、郵件基礎元資料

| 規格項 | 實況 | 落點 |
|---|---|---|
| Message ID | ✅ | scanrange `INTERNET_MESSAGE_ID` + `MAIL_FINGERPRINT`(sha256 去重鍵) |
| Thread ID | ✅ | `CONVERSATION_ID` → THR-#####(id_ledger;編號永不變) |
| 收發時間戳 | ✅ | `TIME/RECEIVED_TIME/SENT_TIME/CREATION_TIME/LAST_MODIFICATION_TIME` |
| From / To / Cc | ✅ | scanrange `FROM/FROM_ADDRESS/TO/CC`;板側 mails.csv `SenderEmail` |
| **Bcc** | ⚠️ 誠實限制 | 收件端信件原生不含他人密件副本(協定使然,非系統缺陷);寄件備份之 Bcc 補抓需動正本掃描器 — 候令 |
| 主旨+代號萃取 | ✅ | 主旨 L1 直判;**v0105 新增:主旨漏帶時掃 `BODY_SNIPPET` 內文代號補全**(已知代號才直判、未知僅弱票 — 內文比主旨雜,不硬錨) |

## 二、語料與內文

| 規格項 | 實況 | 落點 |
|---|---|---|
| 清洗後內文 | ✅ | scanrange `BODY_SNIPPET`(預設 1200 字)→ 語料橋 `corpus.csv` body → E01_MAIL body_clean |
| 領域關鍵字 | ✅ | analytics NLP × `domain_dict.txt`(引擎目錄錨定)+ 命名帳本 338 筆 |
| 附件清單(零觸碰) | ✅ | `ATTACHMENT_COUNT/ATTACHMENT_NAMES` 僅元資料;L7 附件指紋消費;實體檔零下載 |

## 三、多訊號歸戶與專案關係

| 規格項 | 實況 | 落點 |
|---|---|---|
| 網域對映 | ✅ | `domain_map`(L5 白名單直判)+ 學習記憶網域軌 |
| 利害關係人網絡 | ✅ | 超級引擎 S4(87 對口)+ analytics 網絡 SVG + stakeholders.csv + 命名帳本代號 |
| THR↔CASE↔WOP 互鏈 | ✅ | `thr_case_map.json`(193 串)+ `wop_registry.json` thr2wop + L2 確認串繼承 |

## 四、流程與決策動向

| 規格項 | 實況 | 落點 |
|---|---|---|
| Next Steps | ✅ | analytics `workmatrix_next_steps.csv`(實跑 145 筆) |
| Decision Log | ✅ | ENG-027 `decision_log.db/csv`(DEC-####;KPI 完成率/逾期/延遲) |
| 流程探勘事件 | ✅ | E01 事件流 → PM4Py DFG(可攜 dot)/ PMIS fallback SVG / CPM |

## 稽核結論

四維規格 20 項:**19 項既有或本輪補齊,1 項(Bcc)為協定性限制誠實聲明**。
全部由 `via-workops all` 一支到底覆蓋 — 掃描(1)→深鏈(2)→WOP 歸戶(2b)→決策(2c);
逐層路由分佈 `wop_route_stats.json` 供週報 KPI。

紅線:唯讀 · 原件/分類零觸碰 · 附件零下載 · 絕不代寄 · 編號永不變。
