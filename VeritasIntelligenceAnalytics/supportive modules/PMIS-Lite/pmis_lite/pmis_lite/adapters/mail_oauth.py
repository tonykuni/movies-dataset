"""企業 OAuth 唯讀郵件擷取（授權一次，之後自動）。

當公司停用 App Password（微軟 2026/3 起、Google 已於 2025/3 停 Basic Auth）時，
改用 OAuth 2.0 唯讀授權：使用者在瀏覽器點一次「允許」→ 取得 refresh token →
存進本機保險庫 → 之後每次靜默續期 access token 自動讀，不必再授權。

最小權限唯讀 scope：
  - Gmail：https://www.googleapis.com/auth/gmail.readonly
  - Microsoft 365：Mail.Read（+ offline_access 取得 refresh token）

誠實前提（務必先懂）：
  1. OAuth 需要先『註冊一個應用程式』拿 client_id（Google Cloud Console / Azure Entra）。
     這由你（供應商）或客戶 IT 註冊一次即可，之後所有使用者只要點「允許」。
  2. 企業租戶常需『租戶管理員同意(tenant admin consent)』。若客戶 IT 全面封鎖第三方
     OAuth app，連 OAuth 也不通——此時退回 Outlook COM（本機 session）或匯出檔。
  3. 全程唯讀、本機處理、不外傳；refresh token 存系統保險庫。

本模組的網路/瀏覽器流程需在你自己機器跑；訊息→Record 轉換為純函式可離線測試。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

try:
    from ..textrepair import clean_email_text
except Exception:
    def clean_email_text(s): return (s or "", [])
try:
    from ..encoding import repair_mojibake
except Exception:
    def repair_mojibake(s): return s or ""

import re
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GRAPH_SCOPES = ["Mail.Read"]            # MSAL 會自動帶 offline_access 取得 refresh token


def _norm_subject(s: str) -> str:
    s = re.sub(r"^(re|fw|fwd)[:：]\s*", "", (s or "").strip(), flags=re.IGNORECASE)
    return re.sub(r"^(re|fw|fwd)[:：]\s*", "", s, flags=re.IGNORECASE).strip()


def _make_record(subject, body, sender, to, cc, when, source_type, msg_id):
    """共用：把各家 API 的訊息欄位收斂成統一 Record（純函式，可離線測試）。"""
    from ..schema import Record
    subject = repair_mojibake(subject or "")
    cleaned = clean_email_text(repair_mojibake(body or ""))
    body_clean = cleaned[0] if isinstance(cleaned, tuple) else cleaned
    cps = ";".join([x for x in [*(to or []), *(cc or [])] if x])
    return Record(
        title=subject, body=body_clean, actor=sender or "",
        counterparts=cps, event_time=when or "",
        source_type=source_type, source_ref=f"oauth:{msg_id}",
        raw_keys=subject, thread_id=_norm_subject(subject),
    )


# ---------- Gmail API（gmail.readonly）----------
def _gmail_msg_to_record(api_msg) -> "Record":
    headers = {h["name"].lower(): h["value"]
               for h in api_msg.get("payload", {}).get("headers", [])}
    body = _gmail_extract_body(api_msg.get("payload", {})) or api_msg.get("snippet", "")
    return _make_record(
        subject=headers.get("subject", ""), body=body,
        sender=headers.get("from", ""),
        to=[headers.get("to", "")] if headers.get("to") else [],
        cc=[headers.get("cc", "")] if headers.get("cc") else [],
        when=_gmail_date(headers.get("date", "")),
        source_type="gmail_oauth", msg_id=api_msg.get("id", ""))


def _gmail_extract_body(payload) -> str:
    import base64
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", "replace")
    for part in payload.get("parts", []) or []:
        t = _gmail_extract_body(part)
        if t:
            return t
    return ""


def _gmail_date(s: str) -> str:
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(s).isoformat(timespec="seconds")
    except Exception:
        return ""


def fetch_gmail_oauth(client_secret_path: str, token_store: str, lookback_days: int = 180,
                      limit: int = 500) -> list:
    """授權一次→存 refresh token→之後靜默讀。需 google-auth-oauthlib + google-api-python-client。"""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if os.path.exists(token_store):
        creds = Credentials.from_authorized_user_file(token_store, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())                    # 靜默續期，不需再授權
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)        # 瀏覽器點一次「允許」
        with open(token_store, "w", encoding="utf-8") as f:
            f.write(creds.to_json())                     # 存含 refresh_token

    svc = build("gmail", "v1", credentials=creds)
    after = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y/%m/%d")
    out, page = [], None
    while True:
        resp = svc.users().messages().list(userId="me", q=f"after:{after}",
                                            maxResults=min(limit, 100), pageToken=page).execute()
        for m in resp.get("messages", []):
            full = svc.users().messages().get(userId="me", id=m["id"], format="full").execute()
            out.append(_gmail_msg_to_record(full))
            if len(out) >= limit:
                return out
        page = resp.get("nextPageToken")
        if not page:
            break
    return out


# ---------- Microsoft 365 Graph（Mail.Read）----------
def _graph_msg_to_record(j) -> "Record":
    frm = (((j.get("from") or {}).get("emailAddress")) or {}).get("address", "")
    to = [((r.get("emailAddress") or {}).get("address", "")) for r in j.get("toRecipients", [])]
    cc = [((r.get("emailAddress") or {}).get("address", "")) for r in j.get("ccRecipients", [])]
    body = (j.get("body") or {}).get("content", "") or j.get("bodyPreview", "")
    return _make_record(
        subject=j.get("subject", ""), body=body, sender=frm, to=to, cc=cc,
        when=(j.get("receivedDateTime", "") or "").replace("Z", "+00:00"),
        source_type="m365_oauth", msg_id=j.get("id", ""))


def fetch_m365_oauth(client_id: str, tenant: str, token_cache: str,
                     lookback_days: int = 180, shared_mailbox: str = None, limit: int = 500) -> list:
    """授權一次（device/interactive）→ MSAL 快取 refresh token → 之後靜默讀。需 msal + requests。

    shared_mailbox：若提供，改讀共用信箱 /users/{mailbox}/messages（需該信箱委派權限）。
    """
    import msal
    import requests

    cache = msal.SerializableTokenCache()
    if os.path.exists(token_cache):
        cache.deserialize(open(token_cache, encoding="utf-8").read())
    app = msal.PublicClientApplication(
        client_id, authority=f"https://login.microsoftonline.com/{tenant}", token_cache=cache)

    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(GRAPH_SCOPES, account=accounts[0])  # 靜默續期
    if not result:
        flow = app.initiate_device_flow(scopes=GRAPH_SCOPES)
        print("  [授權一次]", flow["message"])           # 顯示「到此網址輸入代碼」
        result = app.acquire_token_by_device_flow(flow)
    if cache.has_state_changed:
        with open(token_cache, "w", encoding="utf-8") as f:
            f.write(cache.serialize())
    if "access_token" not in result:
        raise RuntimeError(f"OAuth 失敗：{result.get('error_description', result)}")

    token = result["access_token"]
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
    out = []
    box = f"users/{shared_mailbox}" if shared_mailbox else "me"   # 共用信箱 vs 本人
    url = (f"https://graph.microsoft.com/v1.0/{box}/messages"
           f"?$filter=receivedDateTime ge {cutoff}&$top=50"
           "&$select=subject,from,toRecipients,ccRecipients,receivedDateTime,body,bodyPreview")
    headers = {"Authorization": f"Bearer {token}"}
    while url and len(out) < limit:
        r = requests.get(url, headers=headers, timeout=30).json()
        for j in r.get("value", []):
            out.append(_graph_msg_to_record(j))
        url = r.get("@odata.nextLink")
    return out[:limit]
