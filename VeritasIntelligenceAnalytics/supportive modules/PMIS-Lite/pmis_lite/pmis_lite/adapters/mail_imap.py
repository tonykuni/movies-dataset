"""郵件自動直讀 adapter（取代手動匯出）。

用『你自己的帳號 + 你自己的權限』直接連到信箱自動讀取近 N 個月，
不必先手動匯出 .pst/.msg。全本機處理、不外傳。

合規前提（內建）：
  - 只連你本人有權限的信箱、用你本人的認證權杖
  - 全程本機解析，不上傳、不繞過稽核
  - 只記工作事實（誰/何時/主旨/狀態），不側寫個人

連線採 imap-tools（泛用通吃 Gmail/Outlook/企業自建 IMAP）。
連線是薄殼；真正的解析邏輯 message_to_record() 是純函式，可離線單元測試。
"""
from __future__ import annotations

from datetime import datetime, timedelta

try:
    from ..textrepair import clean_email_text
except Exception:
    def clean_email_text(s, *a, **k): return s or ""
try:
    from ..encoding import repair_mojibake
except Exception:
    def repair_mojibake(s): return s or ""

IMAP_HOSTS = {
    "gmail": "imap.gmail.com",
    "outlook": "outlook.office365.com",
    "office365": "outlook.office365.com",
    "yahoo": "imap.mail.yahoo.com",
}


def _norm_subject(s: str) -> str:
    import re
    s = re.sub(r"^(re|fw|fwd)[:：]\s*", "", (s or "").strip(), flags=re.IGNORECASE)
    return re.sub(r"^(re|fw|fwd)[:：]\s*", "", s, flags=re.IGNORECASE).strip()


def message_to_record(msg, source_type: str = "mail_imap"):
    """把一封郵件物件轉成統一 Record（純函式，可離線測試）。

    msg 需有屬性：uid, subject, from_, to, cc, date(或 date_str), text, html, headers。
    這正好對應 imap-tools 的 MailMessage 介面。
    """
    from ..schema import Record

    subject = repair_mojibake(getattr(msg, "subject", "") or "")
    body_raw = getattr(msg, "text", "") or getattr(msg, "html", "") or ""
    cleaned = clean_email_text(repair_mojibake(body_raw))
    body = cleaned[0] if isinstance(cleaned, tuple) else cleaned   # clean_email_text 回 (正文, 被刪清單)

    # 時間
    dt = getattr(msg, "date", None)
    if isinstance(dt, datetime):
        event_time = dt.isoformat(timespec="seconds")
    else:
        event_time = str(getattr(msg, "date_str", "") or "")

    to = getattr(msg, "to", ()) or ()
    cc = getattr(msg, "cc", ()) or ()
    counterparts = ";".join([*to, *cc])

    headers = getattr(msg, "headers", {}) or {}
    msg_id = ""
    if isinstance(headers, dict):
        mid = headers.get("message-id") or headers.get("Message-ID")
        if isinstance(mid, (list, tuple)):
            msg_id = mid[0] if mid else ""
        else:
            msg_id = mid or ""
    if not msg_id:
        msg_id = str(getattr(msg, "uid", "") or "")

    return Record(
        title=subject,
        body=body,
        actor=getattr(msg, "from_", "") or "",
        counterparts=counterparts,
        event_time=event_time,
        source_type=source_type,
        source_ref=f"imap:{msg_id}",
        raw_keys=subject,
        thread_id=_norm_subject(subject),
    )


class MailIMAPAdapter:
    """自動直讀 IMAP 信箱（近 N 天）。需 imap-tools 與你自己的認證。"""

    def __init__(self, provider: str, user: str, token: str,
                 lookback_days: int = 180, folder: str = "INBOX", limit: int = 500):
        self.host = IMAP_HOSTS.get((provider or "").lower(), provider)
        self.user = user
        self.token = token
        self.lookback_days = lookback_days
        self.folder = folder
        self.limit = limit
        self.source_type = "mail_imap"

    def available(self) -> bool:
        try:
            import imap_tools  # noqa
            return bool(self.host and self.user and self.token)
        except Exception:
            return False

    def fetch(self):
        """連線並自動讀取 → 產生 Record（generator，只增不減）。"""
        from imap_tools import MailBox, AND
        cutoff = (datetime.now() - timedelta(days=self.lookback_days)).date()
        with MailBox(self.host).login(self.user, self.token, initial_folder=self.folder) as mb:
            for msg in mb.fetch(AND(date_gte=cutoff), limit=self.limit, reverse=True):
                yield message_to_record(msg, self.source_type)

    def read(self):
        """adapter 協定別名（pipeline 呼叫 read）。不可用時安靜略過。"""
        if not self.available():
            return
        try:
            yield from self.fetch()
        except Exception:
            return
