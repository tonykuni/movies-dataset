#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Connect  ——  via_connect.py   (stage-2 \u6388\u6b0a\u9023\u63a5\u5668 / \u7b2c\u4e09\u652f\u5f15\u64ce)
================================================================================
Veritas Intelligence Analytics \u00b7 VeritasDataForge subsystem \u00b7 \u8f14

\u53ea\u8d70\u5b98\u65b9 API + OAuth2 \u6388\u6b0a + readonly scope\u3002\u62c9\u4e0b\u7684\u4fe1\u4ef6/\u9644\u4ef6/\u6587\u4ef6
\u76f4\u63a5\u4e1f\u56de via_forge.ForgeEngine \u7ba1\u7dda\u5206\u985e/\u53bb\u91cd/\u5165\u5e33\uff0c\u5f62\u6210\u9583\u74b0\u3002

\u754c\u7dda (\u9396\u5b9a)\uff1a
  \u00b7 \u50c5\u81ea\u5df1\u5e33\u865f\u3001\u81ea\u5df1\u9ede\u982d\u6388\u6b0a (delegated)\u3002\u4e0d\u505a\u4efb\u4f55\u76e3\u63a7\u898f\u907f\u3002
  \u00b7 \u5168\u90e8 readonly scope\uff1a\u4e0d\u522a\u3001\u4e0d\u767c\u3001\u4e0d\u6539\u5c0d\u65b9\u4fe1\u7bb1\u3002
  \u00b7 token \u5feb\u53d6\u5728\u672c\u6a5f runtime\uff1boauth loopback \u7d81 127.0.0.1\u3002
  \u00b7 append-only ledger\uff1b\u6bcf\u6b21\u62c9\u53d6\u90fd\u7559\u7a3d\u6838\u8ecc\u8de1 (\u8207\u6cbb\u7406\u539f\u5247\u4e00\u81f4)\u3002

\u9023\u63a5\u5668\uff1a
  Gmail        google-api-python-client + google-auth-oauthlib  (gmail.readonly)
  GoogleDrive  \u540c\u4e0a  (drive.readonly) \u2014 gdoc/gsheet/gslides \u5b98\u65b9 export
  Outlook      Microsoft Graph  (Mail.Read, delegated)

\u4f9d\u8cf4 (\u7686\u9078\u7528\uff0c\u7f3a\u5957\u4ef6 \u2192 \u8a72\u9023\u63a5\u5668\u512a\u96c5\u505c\u7528\uff0c\u4e0d crash)\uff1a
  google-api-python-client google-auth-oauthlib msal requests

CLI:
  python via_connect.py --selftest
  python via_connect.py --gmail   --query "newer_than:7d" --max 50
  python via_connect.py --drive   --query "mimeType='application/vnd.google-apps.document'"
  python via_connect.py --outlook --query "receivedDateTime ge 2026-07-01"
  python via_connect.py --status                # \u9023\u63a5\u5668\u53ef\u7528\u77e9\u9663
================================================================================
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import os
import sys
import json
import base64
import argparse
import importlib
from datetime import datetime, timezone

UTC = timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# via_forge \u662f\u540c\u76ee\u9304\u5f15\u64ce\uff1b\u62c9\u4e0b\u7684\u6a94\u4e1f\u56de\u5b83\u7684\u7ba1\u7dda
try:
    import via_forge as _forge
except Exception:
    _forge = None


# ============================================================ lazy \u4f9d\u8cf4 ==
def _try(name):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def sdk_matrix():
    return {
        "google-api-python-client": _try("googleapiclient") is not None,
        "google-auth-oauthlib": _try("google_auth_oauthlib") is not None,
        "msal": _try("msal") is not None,
        "requests": _try("requests") is not None,
    }


def _now():
    return datetime.now(UTC).isoformat()


def _safe_name(s, maxlen=80):
    bad = '\\/:*?"<>|\n\r\t'
    out = "".join("_" if c in bad else c for c in (s or ""))
    return out[:maxlen].strip() or "untitled"


# ======================================================= \u6388\u6b0a (OAuth2) ==
class GoogleAuth:
    """Installed-app OAuth2, loopback redirect. \u4f7f\u7528\u8005\u5728\u700f\u89bd\u5668\u540c\u610f\u3002
    client_secret.json \u7531\u4f7f\u7528\u8005\u5f9e Google Cloud Console \u81ea\u884c\u5efa\u7acb\u3002"""

    def __init__(self, cfg, scopes, token_name):
        self.cfg = cfg
        self.scopes = scopes
        self.token_path = os.path.join(cfg["paths"]["runtime"], token_name)
        self.client_secret = os.path.join(cfg["paths"]["runtime"],
                                           cfg["connect"]["google"]["client_secret_file"])

    def credentials(self):
        oauthlib = _try("google_auth_oauthlib.flow")
        gauth_creds = _try("google.oauth2.credentials")
        greq = _try("google.auth.transport.requests")
        if not (oauthlib and gauth_creds and greq):
            raise RuntimeError("google-auth-oauthlib \u672a\u5b89\u88dd\uff1bpip install google-auth-oauthlib google-api-python-client")
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secret):
                    raise FileNotFoundError(
                        "\u7f3a client_secret.json\uff1a\u8acb\u5f9e Google Cloud Console \u5efa OAuth client \u4e26\u653e\u5230 %s"
                        % self.client_secret)
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret, self.scopes)
                creds = flow.run_local_server(port=0)  # loopback, \u4f7f\u7528\u8005\u6d4f\u89bd\u5668\u540c\u610f
            with open(self.token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        return creds


class GraphAuth:
    """Microsoft Graph delegated OAuth2 (device code / interactive)\u3002"""

    def __init__(self, cfg, scopes):
        self.cfg = cfg
        self.scopes = scopes
        self.token_cache = os.path.join(cfg["paths"]["runtime"], "graph_token_cache.json")

    def token(self):
        msal = _try("msal")
        if msal is None:
            raise RuntimeError("msal \u672a\u5b89\u88dd\uff1bpip install msal")
        gc = self.cfg["connect"]["outlook"]
        cache = msal.SerializableTokenCache()
        if os.path.exists(self.token_cache):
            cache.deserialize(open(self.token_cache, encoding="utf-8").read())
        app = msal.PublicClientApplication(
            gc["client_id"], authority=gc["authority"], token_cache=cache)
        result = None
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(self.scopes, account=accounts[0])
        if not result:
            flow = app.initiate_device_flow(scopes=self.scopes)
            print(flow["message"])  # \u4f7f\u7528\u8005\u4f9d\u63d0\u793a\u5728\u700f\u89bd\u5668\u767b\u5165\u6388\u6b0a
            result = app.acquire_token_by_device_flow(flow)
        if cache.has_state_changed:
            with open(self.token_cache, "w", encoding="utf-8") as f:
                f.write(cache.serialize())
        if "access_token" not in result:
            raise RuntimeError("Graph \u6388\u6b0a\u5931\u6557: %s" % result.get("error_description", "?"))
        return result["access_token"]


# ============================================================ \u9023\u63a5\u5668 ==
class BaseConnector:
    """\u62bd\u8c61\u4ecb\u9762\uff1atransport \u53ef\u6ce8\u5165 (\u771f\u5be6 SDK \u6216 mock)\u3002"""
    name = "base"

    def __init__(self, cfg, transport=None):
        self.cfg = cfg
        self.transport = transport  # None = \u771f\u5be6\u6388\u6b0a\uff1b\u53ef\u6ce8\u5165 fake \u4f9b\u6e2c\u8a66
        self.inbox = cfg["paths"]["inbox"]
        os.makedirs(self.inbox, exist_ok=True)

    def available(self):
        raise NotImplementedError

    def fetch(self, query, max_items):
        """\u56de\u50b3 list[dict]: {kind, id, name, saved_path, meta}\u3002"""
        raise NotImplementedError


class GmailConnector(BaseConnector):
    name = "gmail"
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def available(self):
        m = sdk_matrix()
        return m["google-api-python-client"] and m["google-auth-oauthlib"]

    def _service(self):
        if self.transport is not None:
            return self.transport
        from googleapiclient.discovery import build
        creds = GoogleAuth(self.cfg, self.SCOPES, "gmail_token.json").credentials()
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def fetch(self, query="newer_than:7d", max_items=50):
        svc = self._service()
        out = []
        resp = svc.users().messages().list(userId="me", q=query, maxResults=max_items).execute()
        for m in resp.get("messages", [])[:max_items]:
            full = svc.users().messages().get(userId="me", id=m["id"], format="raw").execute()
            raw = base64.urlsafe_b64decode(full["raw"].encode("ASCII"))
            fn = "gmail_%s.eml" % m["id"]
            path = os.path.join(self.inbox, fn)
            with open(path, "wb") as f:
                f.write(raw)
            out.append({"kind": "email", "id": m["id"], "name": fn,
                        "saved_path": path, "meta": {"source": "gmail"}})
        return out


class DriveConnector(BaseConnector):
    name = "drive"
    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    EXPORT = {
        "application/vnd.google-apps.document":
            ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
        "application/vnd.google-apps.spreadsheet":
            ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
        "application/vnd.google-apps.presentation":
            ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
    }

    def available(self):
        m = sdk_matrix()
        return m["google-api-python-client"] and m["google-auth-oauthlib"]

    def _service(self):
        if self.transport is not None:
            return self.transport
        from googleapiclient.discovery import build
        creds = GoogleAuth(self.cfg, self.SCOPES, "drive_token.json").credentials()
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    def fetch(self, query="mimeType='application/vnd.google-apps.document'", max_items=50):
        svc = self._service()
        out = []
        resp = svc.files().list(q=query, pageSize=max_items,
                                fields="files(id,name,mimeType)").execute()
        for fobj in resp.get("files", [])[:max_items]:
            mime = fobj["mimeType"]
            if mime in self.EXPORT:
                export_mime, ext = self.EXPORT[mime]
                data = svc.files().export(fileId=fobj["id"], mimeType=export_mime).execute()
            else:
                ext = os.path.splitext(fobj["name"])[1] or ".bin"
                data = svc.files().get_media(fileId=fobj["id"]).execute()
            if isinstance(data, str):
                data = data.encode("utf-8")
            fn = _safe_name(os.path.splitext(fobj["name"])[0]) + ext
            path = os.path.join(self.inbox, fn)
            with open(path, "wb") as f:
                f.write(data)
            out.append({"kind": "drive_file", "id": fobj["id"], "name": fn,
                        "saved_path": path, "meta": {"source": "drive", "mime": mime}})
        return out


class OutlookConnector(BaseConnector):
    name = "outlook"
    SCOPES = ["Mail.Read"]

    def available(self):
        m = sdk_matrix()
        return m["msal"] and m["requests"]

    def _get(self, url, token):
        if self.transport is not None:
            return self.transport(url, token)
        import requests
        r = requests.get(url, headers={"Authorization": "Bearer %s" % token}, timeout=30)
        r.raise_for_status()
        return r.json()

    def fetch(self, query="", max_items=50):
        if self.transport is not None:
            token = "FAKE"
        else:
            token = GraphAuth(self.cfg, self.SCOPES).token()
        base = "https://graph.microsoft.com/v1.0/me/messages?$top=%d" % max_items
        if query:
            base += "&$filter=%s" % query
        data = self._get(base, token)
        out = []
        for msg in data.get("value", [])[:max_items]:
            # \u5c07\u90f5\u4ef6\u5beb\u6210 .eml \u98a8\u683c\u7d14\u6587\u5b57 (\u984c\u7c21\u5316\uff1bMIME \u62c9\u53d6\u53ef\u64f4\u5145)
            hdr = "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n" % (
                (msg.get("from", {}).get("emailAddress", {}) or {}).get("address", ""),
                ";".join((r.get("emailAddress", {}) or {}).get("address", "")
                         for r in msg.get("toRecipients", [])),
                msg.get("subject", ""), msg.get("receivedDateTime", ""))
            body = (msg.get("body", {}) or {}).get("content", "") or msg.get("bodyPreview", "")
            fn = "outlook_%s.eml" % _safe_name(msg.get("id", "msg"), 40)
            path = os.path.join(self.inbox, fn)
            with open(path, "w", encoding="utf-8") as f:
                f.write(hdr + body)
            out.append({"kind": "email", "id": msg.get("id"), "name": fn,
                        "saved_path": path, "meta": {"source": "outlook"}})
        return out


CONNECTORS = {"gmail": GmailConnector, "drive": DriveConnector, "outlook": OutlookConnector}


class LocalOutlookConnector(BaseConnector):
    """\u8b80\u53d6\u4f7f\u7528\u8005\u672c\u4eba\u7684\u672c\u6a5f Outlook \u6536\u4ef6\u5323 (pywin32 COM)\u3002
    \u2014 \u7e7c\u627f\u4f60\u76ee\u524d Windows \u767b\u5165\u8eab\u5206\uff0c\u53ea\u8b80\u4f60\u770b\u5f97\u5230\u7684\u4fe1\uff0c\u4e0d\u5b58\u5bc6\u78bc\u3002
    \u2014 \u81ea\u5df1\u5e33\u865f\u3001\u81ea\u5df1\u6b0a\u9650\u7684\u6b63\u7576\u672c\u6a5f\u81ea\u52d5\u5316\u3002
    \u2014 \u82e5\u7528\u65bc\u516c\u53f8\u74b0\u5883\uff0c\u61c9\u900f\u660e\u4f7f\u7528\uff0c\u4e0d\u4f5c\u76e3\u63a7\u898f\u907f\u7528\u9014\u3002
    Windows-only\uff1b\u975e Windows / \u7121 pywin32 \u2192 available()==False\uff0c\u4e0d crash\u3002"""
    name = "local_outlook"

    def available(self):
        return _try("win32com") is not None and os.name == "nt"

    def fetch(self, query="", max_items=50, days_back=7, all_mailboxes=False):
        if self.transport is not None:
            items = self.transport(days_back, max_items)  # \u6ce8\u5165\u5f0f fake \u4f9b\u6e2c\u8a66
        else:
            items = self._read_inbox(days_back, max_items, all_mailboxes=all_mailboxes)
        out = []
        for m in items[:max_items]:
            fn = "local_outlook_%s.eml" % _safe_name(m.get("id", "msg"), 40)
            path = os.path.join(self.inbox, fn)
            # \u5c07 received \u8f49 RFC2822 \u65e5\u671f\uff08mailforge \u624d\u89e3\u5f97\u51fa\u6642\u9593\uff0c\u671f\u9593\u7be9\u9078\u624d\u6b63\u78ba\uff09
            recv = m.get("received", "")
            date_hdr = recv
            try:
                from email.utils import format_datetime as _fmtdt
                from datetime import datetime as _dt
                for _fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                    try:
                        _d = _dt.strptime(recv, _fmt).replace(tzinfo=UTC)
                        date_hdr = _fmtdt(_d); break
                    except Exception:
                        continue
            except Exception:
                pass
            hdr = "From: %s\nSubject: %s\nDate: %s\n\n" % (
                m.get("sender", ""), m.get("subject", ""), date_hdr)
            with open(path, "w", encoding="utf-8") as f:
                f.write(hdr + m.get("body", ""))
            out.append({"kind": "email", "id": m.get("id"), "name": fn,
                        "saved_path": path, "meta": {"source": "local_outlook"}})
        return out

    def _read_inbox(self, days_back, max_items, all_mailboxes=False):
        # ThreadingHTTPServer 的工作執行緒未初始化 COM(操作員實跑:CoInitialize 尚未被呼叫)
        try:
            import pythoncom
        except Exception:
            pythoncom = None
        if pythoncom is not None:
            pythoncom.CoInitialize()
        try:
            return self._read_inbox_impl(days_back, max_items, all_mailboxes=all_mailboxes)
        finally:
            if pythoncom is not None:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def _read_inbox_impl(self, days_back, max_items, all_mailboxes=False):
        import win32com.client
        from datetime import timedelta as _td
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")
        folders = []
        if all_mailboxes:
            # \u8b80\u4f60\u5df2\u639b\u8f09\u7684\u6240\u6709\u4fe1\u7bb1\u7684\u6536\u4ef6\u5323\uff08\u5171\u4eab/\u59d4\u6d3e\u4e5f\u9700\u5df2\u6388\u6b0a\uff09
            try:
                for store in ns.Stores:
                    try:
                        folders.append(store.GetDefaultFolder(6))
                    except Exception:
                        continue
            except Exception:
                folders = [ns.GetDefaultFolder(6)]
        else:
            folders = [ns.GetDefaultFolder(6)]
        start = datetime.now(UTC) - _td(days=days_back)
        out = []
        for inbox in folders:
            items = inbox.Items
            items.Sort("[ReceivedTime]", True)
            for it in items:
                try:
                    if it.Class != 43:
                        continue
                    rt = it.ReceivedTime
                    rt_utc = rt.astimezone(UTC) if rt.tzinfo else rt.replace(tzinfo=UTC)
                    if rt_utc < start:
                        break
                    out.append({"id": str(it.EntryID), "subject": str(it.Subject or ""),
                                "body": str(it.Body or ""), "sender": str(it.SenderName or ""),
                                "received": rt_utc.strftime("%Y-%m-%d %H:%M:%S"),
                                "mailbox": str(getattr(inbox.Parent, "Name", "") or "")})
                    if len(out) >= max_items:
                        break
                except Exception:
                    continue
        return out


CONNECTORS["local_outlook"] = LocalOutlookConnector


class LocalOutlookCalendar:
    """\u8b80\u53d6\u4f7f\u7528\u8005\u672c\u4eba\u672c\u6a5f Outlook \u884c\u4e8b\u66c6 (pywin32 COM)\u3002\u552f\u8b80\u3001\u81ea\u5df1\u884c\u4e8b\u66c6\u3002
    \u975e Windows / \u7121 pywin32 \u2192 available()==False\uff0c\u4e0d crash\u3002\u6ce8\u5165\u5f0f transport \u4f9b\u6e2c\u8a66\u3002"""
    name = "local_outlook_calendar"

    def __init__(self, cfg, transport=None):
        self.cfg = cfg
        self.transport = transport

    def available(self):
        if self.transport is not None:
            return True
        if os.name != "nt":
            return False
        return _try("win32com") is not None

    def events(self, days_back=30, days_ahead=30, max_items=100):
        if self.transport is not None:
            return self.transport(days_back, days_ahead, max_items)
        # ThreadingHTTPServer 工作執行緒需先初始化 COM(同 _read_inbox)
        try:
            import pythoncom
        except Exception:
            pythoncom = None
        if pythoncom is not None:
            pythoncom.CoInitialize()
        try:
            return self._events_impl(days_back, days_ahead, max_items)
        finally:
            if pythoncom is not None:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def _events_impl(self, days_back=30, days_ahead=30, max_items=100):
        out = []
        try:
            import win32com.client
            ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            cal = ns.GetDefaultFolder(9)  # olFolderCalendar
            items = cal.Items
            items.IncludeRecurrences = True
            items.Sort("[Start]")
            start = datetime.now(UTC) - _td(days=days_back)
            end = datetime.now(UTC) + _td(days=days_ahead)
            restrict = "[Start] >= '%s' AND [Start] <= '%s'" % (
                start.strftime("%m/%d/%Y"), end.strftime("%m/%d/%Y"))
            for it in items.Restrict(restrict):
                try:
                    out.append({
                        "subject": str(getattr(it, "Subject", "")),
                        "start": str(getattr(it, "Start", "")),
                        "end": str(getattr(it, "End", "")),
                        "organizer": str(getattr(it, "Organizer", "")),
                        "location": str(getattr(it, "Location", "")),
                    })
                    if len(out) >= max_items:
                        break
                except Exception:
                    continue
        except Exception:
            return []
        return out


# ============================================================ \u5f15\u64ce\u4e3b\u9ad4 ==
class ConnectEngine:
    def __init__(self, cfg=None, transports=None):
        self.cfg = cfg or _forge.load_config()
        self.transports = transports or {}
        self.ledger_path = os.path.join(self.cfg["paths"]["ledger"],
                                        self.cfg["connect"]["ledger_file"])

    def status(self):
        st = {}
        for name, cls in CONNECTORS.items():
            st[name] = cls(self.cfg, self.transports.get(name)).available()
        return {"connectors": st, "sdks": sdk_matrix()}

    def preflight(self):
        """\u6bcf\u500b\u9023\u63a5\u5668\u7684\u5c31\u7dd2\u5ea6 + \u5bb9\u6613\u5ea6\u5206\u7d1a + \u4e0b\u4e00\u6b65\u52d5\u4f5c\uff08\u4f9b\u4e00\u9375\u9023\u7d50 UI\uff09\u3002"""
        rt = self.cfg["paths"]["runtime"]
        def dep(mod):
            return _try(mod) is not None
        cred_google = os.path.exists(os.path.join(rt, self.cfg["connect"]["google"]["client_secret_file"]))
        azure_id = self.cfg["connect"]["outlook"].get("client_id", "")
        cred_azure = bool(azure_id) and not azure_id.startswith("<")

        specs = {
            "local_outlook": {
                "label": "\u672c\u6a5f Outlook", "ease": "ONE_CLICK", "cloud_setup": False,
                "deps_ok": dep("win32com") and os.name == "nt",
                "creds_ok": True,
                "needs": [] if (dep("win32com") and os.name == "nt") else
                         (["\u9700 Windows"] if os.name != "nt" else ["pip install pywin32"]),
                "note": "\u6851\u9762 Outlook \u5df2\u767b\u5165\u5373\u53ef\uff0c\u96f6\u96f2\u7aef\u8a2d\u5b9a\u3001\u96f6 OAuth\uff08\u6700\u5bb9\u6613\uff09",
            },
            "gmail": {
                "label": "Gmail", "ease": "ONE_TIME_SETUP", "cloud_setup": True,
                "deps_ok": dep("google_auth_oauthlib") and dep("googleapiclient"),
                "creds_ok": cred_google,
                "needs": ([] if (dep("google_auth_oauthlib") and dep("googleapiclient")) else
                          ["pip install google-auth-oauthlib google-api-python-client"]) +
                         ([] if cred_google else ["Google Cloud Console \u5efa OAuth client \u2192 client_secret.json \u653e runtime/"]),
                "note": "\u9996\u6b21\u9700 client_secret.json + \u700f\u89bd\u5668\u540c\u610f\u4e00\u6b21\uff1btoken \u5feb\u53d6\u5f8c\u5373\u4e00\u9375",
            },
            "drive": {
                "label": "Google Drive", "ease": "ONE_TIME_SETUP", "cloud_setup": True,
                "deps_ok": dep("google_auth_oauthlib") and dep("googleapiclient"),
                "creds_ok": cred_google,
                "needs": ([] if (dep("google_auth_oauthlib") and dep("googleapiclient")) else
                          ["pip install google-auth-oauthlib google-api-python-client"]) +
                         ([] if cred_google else ["\u5171\u7528 client_secret.json\uff08\u540c Gmail\uff09"]),
                "note": "\u8207 Gmail \u5171\u7528 Google OAuth \u8a2d\u5b9a",
            },
            "outlook": {
                "label": "Outlook (Graph)", "ease": "ONE_TIME_SETUP", "cloud_setup": True,
                "deps_ok": dep("msal"),
                "creds_ok": cred_azure,
                "needs": ([] if dep("msal") else ["pip install msal"]) +
                         ([] if cred_azure else ["Azure \u8a3b\u518a app \u2192 client_id \u586b\u5165 config"]),
                "note": "O365/\u4f01\u696d\u4fe1\u7bb1\uff1b\u9996\u6b21\u9700 Azure app client_id + device-code \u540c\u610f",
            },
        }
        for name, sp in specs.items():
            ready = sp["deps_ok"] and sp["creds_ok"]
            sp["ready"] = ready
            sp["gate"] = "GREEN" if ready else ("YELLOW" if sp["creds_ok"] or not sp["cloud_setup"] else "YELLOW")
            sp["connector"] = name
        # ease ordering: one-click first
        order = {"ONE_CLICK": 0, "ONE_TIME_SETUP": 1}
        ranked = sorted(specs.values(), key=lambda s: (order.get(s["ease"], 9), not s["ready"]))
        return {"preflight": ranked,
                "easiest_ready": next((s["connector"] for s in ranked if s["ready"]), None)}

    def pull(self, connector, query=None, max_items=50, feed_forge=True):
        cls = CONNECTORS.get(connector)
        if cls is None:
            return {"error": "unknown connector: %s" % connector}
        conn = cls(self.cfg, self.transports.get(connector))
        if self.transports.get(connector) is None and not conn.available():
            return {"error": "%s SDK/\u6388\u6b0a\u672a\u5099\u59a5\uff1b\u898b --status" % connector, "sdks": sdk_matrix()}

        q = query or self.cfg["connect"].get("default_query", {}).get(connector, "")
        fetched = conn.fetch(q, max_items)
        for item in fetched:
            self._append_ledger({
                "action": "pull", "connector": connector, "id": item["id"],
                "name": item["name"], "saved_path": item["saved_path"],
                "meta": item["meta"], "pulled_at": _now(),
                "evidence": "AUTHORIZED_OAUTH", "scope": "readonly",
            })

        result = {"connector": connector, "query": q, "count": len(fetched),
                  "items": fetched}

        # \u9583\u74b0\uff1a\u62c9\u4e0b\u7684\u6a94\u4e1f\u56de\u7ba1\u7dda\u5206\u985e/\u53bb\u91cd/\u5165\u5e33\uff1b\u90f5\u4ef6\u4f86\u6e90\u8d70 mailforge(activity/\u6848\u4ef6)
        if feed_forge and fetched and _forge is not None:
            paths = [it["saved_path"] for it in fetched]
            is_mail = connector in ("gmail", "outlook", "local_outlook")
            mf = None
            if is_mail:
                try:
                    import via_mailforge as _mf
                    mf = _mf.MailForgeEngine(self.cfg)
                except Exception:
                    mf = None
            if mf is not None:
                recs = mf.read_and_classify(paths, do_fix=True)
                result["forge_summary"] = mf.summary(recs)
                result["forge_records"] = recs
                result["routed_through"] = "mailforge"
            else:
                eng = _forge.ForgeEngine(self.cfg)
                recs = eng.scan(paths, do_fix=True)
                result["forge_summary"] = eng.summary(recs)
                result["forge_records"] = recs
                result["routed_through"] = "forge"
        return result

    def _append_ledger(self, rec):
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ============================================================ FAKE transports ==
class _FakeGmail:
    """\u6a21\u64ec Gmail API service\uff0c\u4f9b\u7121\u7db2\u7d61/\u7121\u6191\u8b49 self-test\u3002"""
    def __init__(self):
        import email
        from email.message import EmailMessage
        m = EmailMessage()
        m["From"] = "ivy@dongguan.com"; m["To"] = "sandeep@india.com"
        m["Subject"] = "\u4ea4\u671f\u63a1\u8cfc"; m.set_content("\u5ba2\u6236\u8a02\u55ae\u4ea4\u671f\u78ba\u8a8d")
        self._raw = base64.urlsafe_b64encode(m.as_bytes()).decode("ASCII")

    def users(self):
        return self
    def messages(self):
        return self
    def list(self, userId, q, maxResults):
        self._n = min(2, maxResults); return self
    def get(self, userId, id, format):
        self._id = id; return self
    def execute(self):
        if hasattr(self, "_n"):
            n = self._n; del self._n
            return {"messages": [{"id": "msgA"}, {"id": "msgB"}][:n]}
        return {"raw": self._raw}


class _FakeDrive:
    def __init__(self):
        self._docx = base64.b64decode("UEsDBBQAAAAIAA==")  # \u975e\u771f docx\uff0c\u50c5\u9a57\u843d\u5730
    def files(self):
        return self
    def list(self, q, pageSize, fields):
        self._mode = "list"; return self
    def export(self, fileId, mimeType):
        self._mode = "export"; return self
    def get_media(self, fileId):
        self._mode = "media"; return self
    def execute(self):
        if self._mode == "list":
            return {"files": [{"id": "d1", "name": "\u5b63\u5831\u8349\u7a3f",
                               "mimeType": "application/vnd.google-apps.document"}]}
        return "# \u5b63\u5831\u8349\u7a3f\n\u672c\u5b63\u71df\u6536\u6210\u9577\n".encode("utf-8")  # \u7576\u4f5c\u532f\u51fa\u5167\u5bb9


def _fake_graph(url, token):
    return {"value": [{
        "id": "AAMk123", "subject": "\u5408\u7d04\u5be9\u67e5",
        "from": {"emailAddress": {"address": "legal@corp.com"}},
        "toRecipients": [{"emailAddress": {"address": "me@corp.com"}}],
        "receivedDateTime": "2026-07-10T08:00:00Z",
        "body": {"content": "\u5408\u7d04\u689d\u6b3e\u8207\u4fdd\u5bc6\u7d04\u5b9a NDA"}}]}


def _fake_local_outlook(days_back, max_items):
    return [{"id": "LOCAL-1", "subject": "PN-9942 AOI \u505c\u7dda\u6025\u4ef6",
             "body": "\u5927A\u7dda AOI \u72c2\u5831\u4e0d\u826f\uff0c\u8acb\u7814\u767c\u78ba\u8a8d", "sender": "\u54c1\u4fdd\u674e\u7d93\u7406",
             "received": "2026-07-11 09:00:00"},
            {"id": "LOCAL-2", "subject": "ECR \u898f\u683c\u8b8a\u66f4\u7c3d\u6838",
             "body": "PN-1024 \u8173\u4f4d\u6700\u4f73\u5316\u5df2\u7c3d\u6838", "sender": "\u5ba2\u6236A",
             "received": "2026-07-11 10:00:00"}]


# ==================================================================== SELFTEST ==
def selftest():
    import tempfile
    p, f = 0, 0

    def ck(n, c):
        nonlocal p, f
        if c:
            p += 1; print("  [PASS] connect: %s" % n)
        else:
            f += 1; print("  [FAIL] connect: %s" % n)

    if _forge is None:
        print("  [FAIL] connect: via_forge import"); print("connect: 0 PASS / 1 FAIL"); return 0, 1

    cfg = _forge.load_config()
    side = tempfile.mkdtemp()
    cfg["paths"]["inbox"] = os.path.join(side, "inbox")
    cfg["paths"]["ledger"] = side
    cfg["paths"]["cache"] = os.path.join(side, "cache")
    cfg["paths"]["quarantine"] = os.path.join(side, "q")
    os.makedirs(cfg["paths"]["cache"], exist_ok=True)
    # \u6ce8\u5165 connect \u533a\u584a\uff08\u82e5 config \u5c1a\u672a\u542b\uff09
    cfg.setdefault("connect", CONNECT_DEFAULTS)

    eng = ConnectEngine(cfg, transports={
        "gmail": _FakeGmail(), "drive": _FakeDrive(), "outlook": _fake_graph,
        "local_outlook": _fake_local_outlook})

    # status
    st = eng.status()
    ck("status shape", "connectors" in st and "sdks" in st)

    # gmail pull -> eml saved -> forge closed loop
    r = eng.pull("gmail", query="newer_than:7d", max_items=5)
    ck("gmail count", r["count"] == 2)
    ck("gmail eml saved", all(os.path.exists(it["saved_path"]) for it in r["items"]))
    ck("gmail forge loop", "forge_summary" in r and r["forge_summary"]["ok"] >= 1)
    rec0 = r["forge_records"][0]
    ck("gmail record family EML", rec0["format_family"] == "EMAIL_EML")
    ck("gmail email structure", rec0["email_structure"] is not None)

    # drive pull -> gdoc exported to .docx-named file -> forge
    r2 = eng.pull("drive", query="mimeType='application/vnd.google-apps.document'", max_items=5)
    ck("drive count", r2["count"] == 1)
    ck("drive file saved", os.path.exists(r2["items"][0]["saved_path"]))
    ck("drive forge loop", "forge_summary" in r2)

    # outlook pull -> eml -> forge classifies LEGAL
    r3 = eng.pull("outlook", query="", max_items=5)
    ck("outlook count", r3["count"] == 1)
    ok3 = [x for x in r3["forge_records"] if x.get("status") == "OK"]
    ck("outlook classified LEGAL", any(x["aspects"]["content_domain"] == "LEGAL" for x in ok3))

    # local outlook (\u672c\u6a5f\u81ea\u5df1\u4fe1\u7bb1) -> eml -> forge
    r4 = eng.pull("local_outlook", query="", max_items=10)
    ck("local_outlook count", r4["count"] == 2)
    ck("local_outlook eml saved", all(os.path.exists(it["saved_path"]) for it in r4["items"]))
    ck("local_outlook forge loop", "forge_summary" in r4 and r4["forge_summary"]["ok"] >= 1)

    # ledger append-only, evidence tagged
    with open(eng.ledger_path, encoding="utf-8") as fh:
        lines = [json.loads(l) for l in fh if l.strip()]
    ck("ledger append-only", len(lines) == 6)  # 2 gmail + 1 drive + 1 outlook + 2 local
    ck("ledger evidence AUTHORIZED_OAUTH", all(l["evidence"] == "AUTHORIZED_OAUTH" for l in lines))
    ck("ledger scope readonly", all(l["scope"] == "readonly" for l in lines))

    # readonly guarantee: connectors expose no write/delete/send methods
    ck("no write methods", not any(hasattr(GmailConnector, m) for m in ("send", "delete", "modify")))

    # unknown connector guarded
    pf = eng.preflight()
    ck("preflight lists 4 connectors", len(pf["preflight"]) == 4)
    ck("preflight local_outlook one-click", any(s["connector"]=="local_outlook" and s["ease"]=="ONE_CLICK" for s in pf["preflight"]))
    ck("preflight actionable needs", all("needs" in s and "ready" in s for s in pf["preflight"]))
    ck("unknown connector guarded", "error" in eng.pull("slack"))

    return p, f


# connect \u9810\u8a2d\u533a\u584a\uff08\u82e5 via_forge_config.json \u5c1a\u672a\u52a0\u5165\uff0c\u9019\u88e1\u4f5c\u70ba fallback\uff09
CONNECT_DEFAULTS = {
    "enabled": True,
    "ledger_file": "connect_ledger.jsonl",
    "default_query": {
        "gmail": "newer_than:7d",
        "drive": "mimeType='application/vnd.google-apps.document'",
        "outlook": "",
    },
    "google": {"client_secret_file": "client_secret.json"},
    "outlook": {
        "client_id": "<YOUR_AZURE_APP_CLIENT_ID>",
        "authority": "https://login.microsoftonline.com/common",
    },
    "governance": {
        "scopes_readonly_only": True,
        "note": "\u50c5\u81ea\u5df1\u5e33\u865f delegated \u6388\u6b0a\uff1b\u4e0d\u505a\u76e3\u63a7\u898f\u907f\uff1b\u4e0d\u5beb\u4e0d\u522a\u4e0d\u767c\u3002",
    },
}


def _ensure_connect_cfg(cfg):
    if "connect" not in cfg:
        cfg["connect"] = CONNECT_DEFAULTS
    return cfg


def main():
    ap = argparse.ArgumentParser(description="VIA Connect — stage-2 authorized connector")
    ap.add_argument("--gmail", action="store_true")
    ap.add_argument("--drive", action="store_true")
    ap.add_argument("--outlook", action="store_true")
    ap.add_argument("--query", default=None)
    ap.add_argument("--max", type=int, default=50)
    ap.add_argument("--no-forge", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        a, b = selftest(); print("connect: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)

    cfg = _ensure_connect_cfg(_forge.load_config())
    eng = ConnectEngine(cfg)

    if args.status:
        print(json.dumps(eng.status(), ensure_ascii=False, indent=2)); return

    conn = "gmail" if args.gmail else "drive" if args.drive else "outlook" if args.outlook else None
    if conn is None:
        print("\u8acb\u6307\u5b9a --gmail / --drive / --outlook\uff08\u6216 --status / --selftest\uff09"); return

    r = eng.pull(conn, query=args.query, max_items=args.max, feed_forge=not args.no_forge)
    if "error" in r:
        print("\u932f\u8aa4\uff1a%s" % r["error"]); return
    print("%s \u62c9\u53d6 %d \u7b46 \u2192 inbox" % (conn, r["count"]))
    if "forge_summary" in r:
        s = r["forge_summary"]
        print("  forge: ok=%d healthy=%d dup=%d bad=%d" % (s["ok"], s["healthy"], s["dup"], s["bad"]))
        print("  by_domain:", s["by_domain"])


if __name__ == "__main__":
    main()

# ==============================================================================
# \u4f7f\u7528\u8005\u672c\u6a5f\u8a2d\u5b9a (\u4e00\u6b21\u6027)\uff1a
#   Google : \u5230 Google Cloud Console \u5efa OAuth client (Desktop app)\uff0c\u4e0b\u8f09
#            client_secret.json \u653e\u5230 runtime\\ \u3002\u9996\u6b21\u57f7\u884c\u6703\u958b\u700f\u89bd\u5668\u8b93\u4f60\u540c\u610f\u3002
#   Outlook: \u5230 Azure Portal \u8a3b\u518a\u4e00\u500b public client app\uff0c\u628a client_id \u586b\u9032 config\uff0c
#            \u9996\u6b21\u57f7\u884c\u8d70 device code flow \u767b\u5165\u3002
# \u5168\u90e8 readonly\u3002token \u5b58\u672c\u6a5f runtime\uff0c\u4e0d\u96e2\u6a5f\u3002IT \u672c\u4f86\u5c31\u8a72\u770b\u5f97\u5230\u9019\u4e9b\u6388\u6b0a\u3002
# ==============================================================================
