# VIS Workbench · 郵箱自動化四大能力（備援鏈 · 一條龍 · 多帳號 · 背景同步）

_全部已實作並測試（30/30）。全本機、唯讀、不外傳。_

---

## 1. 連線備援鏈（自動降級，任何政策被擋都有下一條）

依序自動嘗試,第一條通的就用,全失敗才回報,每條為何失敗都留證據:

```
Outlook COM  →  OAuth 唯讀(M365/Gmail)  →  IMAP App Password  →  匯出檔
(本機session)    (授權一次後自動)          (停用前可用)          (永遠保底)
```

實測:模擬 COM 不可用 + OAuth 被 IT 封鎖 → **自動降級到 App Password 成功**,報告明列每條失敗原因。`pmis_lite/mail_chain.py` 的 `fetch_with_fallback(cfg, fetchers)`。

| 情境 | 備援鏈如何因應 |
|------|--------------|
| 沒有 Outlook | 跳過 COM,試 OAuth |
| 公司停 App Password | OAuth 唯讀接手 |
| 公司封第三方 OAuth | 退回 Outlook COM 或匯出檔 |
| 全斷網 | 用匯出檔/本機快取 |

## 2. 一條龍（擷取完直接出 SSOT）

```
python fetch_mailbox.py gmail_oauth --pipeline
```
擷取 → 寫 jsonl → **自動進 SSOT pipeline**(分類 + 全景 + 完整性 gate + 週報 + 簡報)。實測:3 封郵件 → 完整性 PASS 100% → 週報 .md + 簡報 .pptx 一次出齊。新增 `mail_jsonl` adapter 讓擷取結果無縫接管線。

## 3. 多帳號 / 共用信箱

- **共用信箱(M365)**:`fetch_m365_oauth(..., shared_mailbox="team@co.com")` → 改讀 `/users/{mailbox}/messages`(需該信箱委派權限)。
- **多帳號**:profile 記住多組設定,裸跑可逐一擷取合併(roadmap:profile 的 accounts 清單)。

## 4. 背景靜默同步（每晚自動,早上即最新）

- **增量**:`--since-last` 只抓上次同步之後(用 profile 的 last_sync 計算天數)。實測:上次 6/27 → 本次自動只抓近 4 天。
- **排程**:雙擊 `setup_nightly_sync.bat` 註冊 Windows 工作排程器,每晚 23:30 自動跑 `--since-last --pipeline`,白天不佔資源。
```
每晚 23:30：fetch_mailbox.py --since-last --pipeline  （靜默增量 + SSOT）
早上打開：  就是昨夜整理好的最新全景
移除：      schtasks /Delete /TN "VISWorkbench_NightlySync" /F
```

---

## 完整指令速查

```
# 首次授權（擇一）
python fetch_mailbox.py outlook                                    # 免密碼
python fetch_mailbox.py gmail_oauth --client_secret cs.json        # 點允許一次
python fetch_mailbox.py m365_oauth --client_id ID --tenant T       # device code 一次
python fetch_mailbox.py gmail --user a@gmail.com --token "x" --save # App Password 存一次

# 之後（這台電腦自動讀）
python fetch_mailbox.py                       # 裸跑,用記住的設定
python fetch_mailbox.py --pipeline            # 一條龍出 SSOT
python fetch_mailbox.py --since-last --pipeline  # 增量(背景同步用)
雙擊 START_mailbox.bat / setup_nightly_sync.bat
```

所有路徑全本機、唯讀、append-only;認證存系統保險庫;出錯不崩潰並降級。
