"""Outlook 桌面 adapter（Windows 專用）。

透過你『已登入的 Outlook』讀取（win32com / MAPI），程式看到的就是你本人看得到的信，
權限與你一致 —— 這是最乾淨的合規論述：只是讓程式幫你點開你本來就看得到的信。

能力：
  - 讀指定資料夾、近 N 個月或全部
  - 完整擷取：寄件人/收件人/CC/時間/主旨/內文
  - 附件落地到本機資料夾，交給 attachments.py 擷取文字
  - 回報 seen/extracted/failed 給完整性驗證

注意：此檔在非 Windows 環境 import 會自動降級（不中斷），方便在其他平台開發測試。
真實讀取請在你的 Windows 機器執行，並先 `pip install pywin32`。
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Iterable

from ..schema import Record
from ..textrepair import clean_email_text

try:
    import win32com.client  # type: ignore
    _HAS_WIN32 = True
except Exception:
    _HAS_WIN32 = False


class OutlookDesktopAdapter:
    source_type = "outlook"

    def __init__(self, months: int | None = 3, folders: list[str] | None = None,
                 attachment_dir: str = "attachments", audit=None):
        self.months = months
        self.folders = folders or ["收件匣", "Inbox", "寄件備份", "Sent Items"]
        self.attachment_dir = attachment_dir
        self.audit = audit

    def available(self) -> bool:
        return _HAS_WIN32

    def _iter_messages(self):
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        cutoff = None
        if self.months:
            cutoff = datetime.now() - timedelta(days=30 * self.months)

        for store in outlook.Folders:
            for folder in store.Folders:
                if self.folders and folder.Name not in self.folders:
                    continue
                items = folder.Items
                items.Sort("[ReceivedTime]", True)
                for it in items:
                    try:
                        if cutoff and getattr(it, "ReceivedTime", None):
                            rt = it.ReceivedTime
                            if rt.replace(tzinfo=None) < cutoff:
                                break    # 已排序，過期就停這個資料夾
                        yield folder.Name, it
                    except Exception:
                        continue

    def read(self) -> Iterable[Record]:
        if not _HAS_WIN32:
            print("  [outlook] 非 Windows / 未裝 pywin32，略過（請於你的 Windows 機器執行）")
            return
        os.makedirs(self.attachment_dir, exist_ok=True)
        a = self.audit.audit("outlook") if self.audit else None

        for folder_name, msg in self._iter_messages():
            if a:
                a.seen += 1
            try:
                body = getattr(msg, "Body", "") or ""
                cleaned, _ = clean_email_text(body)
                rec = Record(source_type=self.source_type)
                rec.title = getattr(msg, "Subject", "") or ""
                rec.body = cleaned
                rec.actor = getattr(msg, "SenderName", "") or ""
                to = getattr(msg, "To", "") or ""
                cc = getattr(msg, "CC", "") or ""
                rec.counterparts = ";".join(x for x in [to, cc] if x)
                rt = getattr(msg, "ReceivedTime", None)
                rec.event_time = rt.strftime("%Y-%m-%d %H:%M") if rt else ""
                eid = getattr(msg, "EntryID", "")
                rec.source_ref = f"outlook::{folder_name}::{eid[:12]}"

                # 附件落地
                atts = []
                for att in getattr(msg, "Attachments", []):
                    fn = att.FileName
                    safe = "".join(c for c in fn if c not in '\\/:*?"<>|')
                    dst = os.path.join(self.attachment_dir, f"{eid[:8]}_{safe}")
                    try:
                        att.SaveAsFile(os.path.abspath(dst))
                        atts.append(dst)
                    except Exception:
                        pass
                rec.raw_keys = " | ".join(f"att={os.path.basename(p)}" for p in atts)

                if a:
                    a.extracted += 1
                yield rec
            except Exception as e:
                if a:

                    a.failures.append((getattr(msg, "Subject", "?")[:40], f"error:{e.__class__.__name__}"))
                continue
