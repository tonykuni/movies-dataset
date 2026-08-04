# VIS Workbench · 企業 OAuth 唯讀設定（授權一次，之後自動）

_當公司停用 App Password 時的正解。Google 已於 2025/3 停 Basic Auth；微軟 App Password 自 2026/3 起分階段停止。OAuth 唯讀是必走的後路。_

---

## 一、運作原理：為何「授權一次，之後自動」

OAuth 不用密碼。流程是:使用者在瀏覽器點一次「允許」→ 系統拿到 **refresh token** → 存進本機保險庫 → 之後每次用 refresh token **靜默續期** access token 自動讀,不必再授權。只要帳號/app 仍有效、且定期執行,就一直自動。

最小權限**唯讀** scope:Gmail 用 `gmail.readonly`、Microsoft 365 用 `Mail.Read`。只能讀、不能改不能寄——客戶資安看得安心。

---

## 二、一次性設定（由你或客戶 IT 做一次，之後所有人只要點允許）

### Gmail / Google Workspace
1. Google Cloud Console 建一個 OAuth 用戶端(類型:桌面 App)→ 下載 `client_secret.json`。
2. 啟用 Gmail API。
3. 第一次執行:
```
pip install google-auth-oauthlib google-api-python-client
python fetch_mailbox.py gmail_oauth --client_secret client_secret.json --days 180
```
→ 瀏覽器跳出 Google 授權頁,點「允許」一次。token 存進 `VIA_RUNS/mailbox/gmail_oauth_token.json`(含 refresh token)。
4. 之後:`python fetch_mailbox.py`(裸跑)或雙擊 .bat → **自動讀,免再授權**。

### Microsoft 365 / Outlook
1. Azure Entra(舊稱 AAD)註冊一個應用程式 → 取得 `client_id` 與 `tenant`(租戶 ID)。
2. API 權限加 **Microsoft Graph → Mail.Read(委派/Delegated)** + `offline_access`。
3. 第一次執行:
```
pip install msal requests
python fetch_mailbox.py m365_oauth --client_id <你的ID> --tenant <租戶ID> --days 180
```
→ 終端顯示「到此網址輸入代碼」(device flow),用瀏覽器授權一次。MSAL 把 refresh token 存進 `m365_oauth_cache.bin`。
4. 之後:裸跑 → **MSAL 靜默續期自動讀**。

---

## 三、誠實交代的三個前提（不寫進去就會踩雷）

1. **OAuth 需要先「註冊一個應用程式」拿 client_id** — 這是和 App Password 最大的差別。但只要**你(供應商)或客戶 IT 註冊一次**,之後所有使用者只是點「允許」,不必碰 Cloud Console。
2. **企業租戶常需「租戶管理員同意(tenant admin consent)」** — 委派唯讀(Mail.Read)很多租戶允許使用者自行同意;但若 IT 設定需管理員同意,得請 IT 按一次。
3. **若 IT 全面封鎖第三方 OAuth app** — 連 OAuth 也不通。此時備援鏈降級:**Outlook COM(本機已登入 session,免任何雲端授權)→ 匯出檔**。這就是為什麼我們保留多條路。

---

## 四、四種連線方式總表（備援鏈順序）

| 方式 | 認證 | 授權一次後 | 公司停 App Password | 公司封 OAuth |
|------|------|-----------|--------------------|-------------|
| **Outlook COM** | 用已登入 session,免密碼 | ✅ 永遠自動 | ✅ 不受影響 | ✅ 不受影響 |
| **OAuth 唯讀**(Gmail/M365) | 瀏覽器點允許一次 | ✅ refresh token 靜默續期 | ✅ 正解 | ❌ 退回 COM/匯出 |
| **IMAP + App Password** | 貼一次 App Password | ✅ 存保險庫自動載 | ❌ 失效 | — |
| **匯出檔** | 無 | 需重新匯出 | ✅ 不受影響 | ✅ 不受影響 |

**選擇邏輯**:Windows 有 Outlook → 首選 COM(最省事);純 Gmail/跨平台 → OAuth 唯讀;都不行 → 匯出檔。系統用備援鏈自動依序嘗試。

---

## 五、安全與合規

- **唯讀**:scope 只給讀(gmail.readonly / Mail.Read),程式無法改、刪、寄。
- **可撤銷**:使用者隨時可在 Google/Microsoft 帳號後台撤銷此 app 授權。
- **本機**:refresh token 存本機保險庫,郵件解析全本機、不外傳。
- **最小揭露**:委派權杖綁定登入者本人,不碰其他人信箱。
