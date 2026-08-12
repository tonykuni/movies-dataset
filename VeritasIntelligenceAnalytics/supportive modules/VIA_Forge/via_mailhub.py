#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA MailHub  ——  via_mailhub.py   (\u7261 \u00b7 \u90f5\u4ef6/\u5c08\u6848\u5f37\u5f15\u64ce)
================================================================================
\u5408\u4f75 mailforge + connect + project \u70ba\u55ae\u4e00\u5f37\u5f15\u64ce\uff08\u4fe1\u2192\u6848\u2192\u5c08\u6848\u4e00\u689d\u9f8d\uff09\uff1a
  \u2022 \u90f5\u4ef6\u667a\u6167\uff1a\u8b80\u53d6\u2192\u4fee\u5fa9\u2192\u5206\u985e\u2192\u7de8\u865f + activity/\u6848\u4ef6/\u56de\u8986\u72c0\u614b/\u6848\u4ef6\u77e9\u9663
  \u2022 \u9023\u63a5\u5668\uff1aGmail/Drive/Outlook/\u672c\u6a5f Outlook + \u884c\u4e8b\u66c6\uff08\u552f\u8b80\u3001\u9810\u6aa2\u3001\u4e00\u9375\uff09
  \u2022 \u5c08\u6848\uff1a\u64f7\u53d6\u7279\u5b9a\u671f\u9593+\u4e3b\u984c \u2192 \u5c08\u6848\u7ba1\u7406 + WorkMatrix/ICS \u5408\u898f\u532f\u51fa
\u5e95\u5c64 via_mailforge / via_connect / via_project \u4fdd\u7559\u4e0d\u52d5\uff08\u53ea\u589e\u4e0d\u6e1b\uff09\u3002
================================================================================
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import via_mailforge as _M
import via_connect as _C
import via_project as _P
import via_ops as _O
import via_signal as _SG
# 2026-08-12 真環拆解令(sysman C4):via_rebuild 頂層互引成載入環——
# 改於 work_rebuild() 內 lazy 導入(用點本就延遲初始化,行為零改變)


class MailHubEngine:
    """\u90f5\u4ef6/\u5c08\u6848\u5f37\u5f15\u64ce\uff1a\u90f5\u4ef6\u667a\u6167 + \u9023\u63a5\u5668 + \u5c08\u6848\uff0c\u4e00\u652f\u7d71\u540c\u3002"""
    seal = "\u7261"
    caps = ["activity", "cluster", "reply_status", "case_intelligence", "links",
            "connectors", "preflight", "calendar",
            "project", "period_filter", "topic_filter", "workmatrix", "ics",
            "operations_board", "kanban", "owner_view", "overdue_alert"]

    def __init__(self, cfg=None):
        self.cfg = cfg or _M.F.load_config()
        self._mail = None
        self._connect = None
        self._project = None

    @property
    def mail(self):
        if self._mail is None:
            self._mail = _M.MailForgeEngine(self.cfg)
        return self._mail

    @property
    def connect(self):
        if self._connect is None:
            cfg = _C._ensure_connect_cfg(self.cfg) if hasattr(_C, "_ensure_connect_cfg") else self.cfg
            self._connect = _C.ConnectEngine(cfg)
        return self._connect

    @property
    def project(self):
        if self._project is None:
            self._project = _P.ProjectEngine(self.cfg)
        return self._project

    @property
    def ops(self):
        if getattr(self, "_ops", None) is None:
            self._ops = _O.OpsEngine(self.cfg)
        return self._ops

    # --- \u5de5\u4f5c\u91cd\u5efa (rebuild) ---
    def work_rebuild(self, records, control_sheet=None, control_data=None):
        if getattr(self, "_rebuild", None) is None:
            import via_rebuild as _RB  # lazy:拆頂層互引載入環(2026-08-12)
            self._rebuild = _RB.RebuildEngine(self.cfg)
        return self._rebuild.rebuild(records, control_sheet=control_sheet, control_data=control_data)

    # --- \u4fe1\u4ef6\u72c0\u614b\u71c8\u865f (signal) ---
    def signal_board(self, records, ci=None):
        if getattr(self, "_signal", None) is None:
            self._signal = _SG.SignalEngine(self.cfg)
        return self._signal.signal_board(records, ci=ci)

    def classification_proposals(self, records):
        if getattr(self, "_signal", None) is None:
            self._signal = _SG.SignalEngine(self.cfg)
        return self._signal.classification_proposals(records)

    # --- \u65e5\u5e38\u4f5c\u696d\u63a7\u5236\u53f0 (ops) ---
    def operations_board(self, records, owner=None, ci=None):
        return self.ops.board(records, owner=owner, ci=ci)

    def operations_html(self, board, path=None):
        return self.ops.to_html(board, path)

    # --- \u90f5\u4ef6\u667a\u6167 (mailforge) ---
    def read_and_classify(self, target, do_fix=True):
        return self.mail.read_and_classify(target, do_fix=do_fix)

    def summary(self, records):
        return self.mail.summary(records)

    def clusters(self, records, target=None):
        return self.mail.clusters(records, target=target)

    def reply_status(self, records, target=None):
        return self.mail.reply_status(records, target=target)

    def case_intelligence(self, records, target=None):
        return self.mail.case_intelligence(records, target=target)

    def stakeholders(self, records):
        return self.mail.stakeholders(records)

    # --- \u9023\u63a5\u5668 (connect) ---
    def connectors_status(self):
        return {**self.connect.status(), **self.connect.preflight()}

    def pull(self, connector, **kw):
        return self.connect.pull(connector, **kw)

    def calendar_events(self, transport=None, **kw):
        cal = _C.LocalOutlookCalendar(self.cfg, transport=transport)
        return cal.events(**kw) if cal.available() else []

    # --- \u4e00\u9375\u81ea\u52d5\u9023 Outlook\uff08\u975e\u5c08\u696d\u64cd\u4f5c\u8005 \u00b7 \u96f6\u96f2\u7aef\u8a2d\u5b9a\uff09---
    def outlook_oneclick(self, days_back=7, max_items=100, transport=None,
                         since=None, until=None, keyword=None):
        """\u672c\u6a5f Outlook COM\uff1a\u7e7c\u627f\u5df2\u767b\u5165\u8eab\u5206\u3001\u96f6 OAuth\u3001\u96f6\u96f2\u7aef\u8a2d\u5b9a\u3002
        \u53ef\u9644\u8d77\u8a16\u6642\u9593(since/until) + \u95dc\u9375\u5b57(keyword)\uff1bIT \u5bb9\u5fcd\u7bc4\u570d\u5167\u53ea\u8b80\u81ea\u5df1\u4fe1\u3002"""
        conn = _C.LocalOutlookConnector(self.cfg, transport=transport)
        if transport is None and not conn.available():
            reason = ("\u9700\u5728 Windows \u4e0a\u57f7\u884c" if os.name != "nt"
                      else "\u9700\u5b89\u88dd pywin32\uff08\u555f\u52d5\u5668\u6703\u81ea\u52d5\u88dd\uff09\uff0c\u4e14\u684c\u9762 Outlook \u9700\u5df2\u5b89\u88dd\u4e26\u767b\u5165")
            return {"ok": False, "ready": False, "reason": reason,
                    "hint": "\u5728\u5df2\u767b\u5165\u684c\u9762 Outlook \u7684 Windows \u6a5f\u5668\u4e0a\u96d9\u64ca activate.bat \u5373\u53ef\u4e00\u9375\u8b80\u53d6"}
        # \u8d77\u8a16\u6642\u9593 \u2192 \u63db\u7b97 days_back\uff08\u53d6\u6db5\u84cb\u5230 until \u7684\u5929\u6578\uff09
        if since:
            try:
                sdt = _P._parse_when(since)
                if sdt:
                    days_back = max(1, (datetime.now(UTC) - sdt).days + 1)
            except Exception:
                pass
        fetched = conn.fetch("", max_items=max_items, days_back=days_back)
        paths = [it["saved_path"] for it in fetched if it.get("saved_path")]
        recs = self.read_and_classify(paths, do_fix=True)
        # \u8d77\u8a16 + \u95dc\u9375\u5b57\u7be9\u9078\uff08\u5728 project \u5c64\u505a\uff09
        if since or until or keyword:
            recs = self.project.filter_emails(recs, topic=keyword, since=since, until=until) + \
                   [r for r in recs if r.get("kind") != "EMAIL"]
        ok = [r for r in recs if r.get("status") == "OK"]
        return {"ok": True, "ready": True, "count": len(ok), "records": recs,
                "summary": self.summary(recs) if hasattr(self.mail, "summary") else {},
                "source": "local_outlook", "days_back": days_back,
                "filter": {"since": since, "until": until, "keyword": keyword}}

    # --- \u5c08\u6848 (project) ---
    def create_project(self, name, records, **kw):
        return self.project.create_project(name, records, **kw)

    def export_workmatrix(self, proj, path):
        return self.project.export_workmatrix(proj, path)

    def export_ics(self, proj, path):
        return self.project.export_ics(proj, path)

    def project_html(self, proj, path=None):
        return self.project.to_html(proj, path)


def selftest():
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] mailhub: %s" % n)
        else: f += 1; print("  [FAIL] mailhub: %s" % n)
    import tempfile
    cfg = _M.F.load_config(); side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)
    d = tempfile.mkdtemp()
    for i, (fr, su, bd) in enumerate([("qa.li@corp.com", "PN-9942 \u505c\u7dda", "\u8acb\u63d0\u4f9b\u65b9\u6848 \u98a8\u96aa\u9ad8"),
                                       ("rd.wang@corp.com", "Re: PN-9942 \u505c\u7dda", "\u627f\u8afe 07/10 \u63d0\u4f9b ECN")]):
        open(os.path.join(d, "m%d.eml" % i), "w", encoding="utf-8").write(
            "From: %s\nTo: t@c\nSubject: %s\nMessage-ID: <m%d@c>\nDate: Mon, 0%d Jul 2026 09:00:00 +0800\n\n%s" % (fr, su, i, 6 + i, bd))
    eng = MailHubEngine(cfg)
    recs = eng.read_and_classify(d, do_fix=True)
    ck("\u90f5\u4ef6\u667a\u6167 read_and_classify", len(recs) == 2)
    ck("clusters", eng.clusters(recs)["cluster_count"] == 1)
    ck("reply_status", "needs_reply_count" in eng.reply_status(recs))
    ck("case_intelligence", bool(eng.case_intelligence(recs)["cases"]))
    ck("connectors preflight", len(eng.connectors_status()["preflight"]) == 4)
    ck("calendar (fake transport)",
       eng.calendar_events(transport=lambda a, b, c: [{"subject": "x", "start": "2026-07-09 10:00:00"}]) != [])
    proj = eng.create_project("\u6e2c\u8a66", recs, topic="PN-9942")
    ck("create_project", proj["project_id"].startswith("VIA-PROJ-"))
    wm = eng.export_workmatrix(proj, os.path.join(side, "WM.xlsx"))
    ck("export_workmatrix", wm.get("ok") and wm["table"] == "MatrixTable")
    ic = eng.export_ics(proj, os.path.join(side, "r.ics"))
    ck("export_ics", ic.get("ok"))
    oc = eng.outlook_oneclick(transport=lambda db,mx:[{"id":"o1","subject":"PN-9942 \u505c\u7dda","body":"\u8acb\u63d0\u4f9b\u65b9\u6848","sender":"qa.li@corp.com","received":"2026-07-06 09:00:00"}])
    ck("outlook \u4e00\u9375(fake transport)", oc.get("ok") and oc.get("count") == 1)
    # \u672a\u5c31\u7dd2\u8a3a\u65b7\u6539\u78ba\u5b9a\u6027\u6a21\u64ec\uff1a\u539f\u5beb\u6cd5\u4f9d\u8cf4\u4e3b\u6a5f\u7121 Outlook\uff0c\u5728\u771f Outlook \u5728\u4f4d\u7684\u6a5f\u5668\u6703\u8b80\u771f\u4fe1\u7bb1\u4e14\u5fc5 FAIL
    _avail = _C.LocalOutlookConnector.available
    try:
        _C.LocalOutlookConnector.available = lambda self: False
        nr = eng.outlook_oneclick()
        ck("outlook \u672a\u5c31\u7dd2\u53cb\u5584\u8a3a\u65b7", nr.get("ok") is False and "hint" in nr)
    finally:
        _C.LocalOutlookConnector.available = _avail
    b = eng.operations_board(recs)
    rb = eng.work_rebuild(recs)
    ck("work_rebuild", "rows" in rb and "risk_control" in rb and "rebuild_plan" in rb and "stakeholder_control" in rb)
    sb = eng.signal_board(recs)
    ck("signal_board 燈號", "items" in sb and "immediate" in sb and "india" in sb and "counts" in sb)

    ck("operations_board (\u65e5\u5e38\u4f5c\u696d)", "lanes" in b and "today" in b and "owner_view" in b)
    # roll up sub-engine selftests
    import io, contextlib
    for mod, nm in ((_M, "mailforge"), (_C, "connect"), (_P, "project"), (_O, "ops"), (_SG, "signal"), (_RB, "rebuild")):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            a, b = mod.selftest()
        ck("%s \u5e95\u5c64 %d PASS" % (nm, a), b == 0)
    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    if ap.parse_args().selftest:
        a, b = selftest(); print("mailhub: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)


if __name__ == "__main__":
    main()
