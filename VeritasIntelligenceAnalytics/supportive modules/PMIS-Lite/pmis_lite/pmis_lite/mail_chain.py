"""郵件連線備援鏈（自動降級）。

依序嘗試:Outlook COM → OAuth 唯讀 → IMAP App Password → 匯出檔。
第一條通的就用,全失敗才回報;每條為何失敗都留證據。
任何單一政策被擋(停 App Password、封 OAuth、無 Outlook),還有下一條。
"""
from __future__ import annotations

import os
from .resilience import Strategy, run_chain


def build_mail_strategies(cfg: dict, fetchers: dict) -> list:
    """依設定與環境組裝策略清單。fetchers 提供各方法的擷取函式(便於注入測試)。

    cfg 範例:
      {"outlook":{"enabled":true,"months":6},
       "m365_oauth":{"client_id":"..","tenant":".."},
       "gmail_oauth":{"client_secret":"client_secret.json"},
       "imap":{"provider":"gmail","user":"..","token":".."},
       "export":{"dir":"C:/exports"}}
    """
    S = []

    # 1) Outlook COM（本機已登入 session，免雲端授權，最抗政策變動）
    if cfg.get("outlook", {}).get("enabled", True):
        def _com():
            return fetchers["outlook"](months=cfg.get("outlook", {}).get("months", 6))
        def _com_ok():
            try:
                import win32com  # noqa
                return os.name == "nt"
            except Exception:
                return False
        S.append(Strategy("Outlook COM", _com, available=_com_ok))

    # 2) OAuth 唯讀（M365 / Gmail）
    if cfg.get("m365_oauth", {}).get("client_id"):
        cm = cfg["m365_oauth"]
        S.append(Strategy("M365 OAuth 唯讀",
                          lambda c=cm: fetchers["m365_oauth"](c["client_id"], c.get("tenant", "common"),
                                                              c.get("cache", "m365_cache.bin"),
                                                              c.get("days", 180), c.get("shared_mailbox"))))
    if cfg.get("gmail_oauth", {}).get("client_secret"):
        cg = cfg["gmail_oauth"]
        S.append(Strategy("Gmail OAuth 唯讀",
                          lambda c=cg: fetchers["gmail_oauth"](c["client_secret"],
                                                               c.get("token", "gmail_token.json"),
                                                               c.get("days", 180))))

    # 3) IMAP + App Password（仍可用時）
    if cfg.get("imap", {}).get("token"):
        ci = cfg["imap"]
        S.append(Strategy("IMAP App Password",
                          lambda c=ci: fetchers["imap"](c.get("provider", "gmail"),
                                                        c.get("user", ""), c["token"], c.get("days", 180))))

    # 4) 匯出檔（最後保底，不受任何政策影響）
    if cfg.get("export", {}).get("dir"):
        d = cfg["export"]["dir"]
        def _exp():
            return fetchers["export"](d)
        S.append(Strategy("匯出檔", _exp, available=lambda: os.path.isdir(d)))

    return S


def fetch_with_fallback(cfg: dict, fetchers: dict):
    """跑備援鏈,回傳 (records, ChainResult)。records 為第一條成功的結果。"""
    strategies = build_mail_strategies(cfg, fetchers)
    result = run_chain(strategies, validate=lambda v: isinstance(v, list))
    return (result.value or []), result
