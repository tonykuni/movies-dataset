#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Signal  ——  via_signal.py   (\u865f \u00b7 \u4fe1\u4ef6\u72c0\u614b\u71c8\u865f\u7cfb\u7d71)
================================================================================
\u8b80 E-MAIL / CONTROL SHEET \u2192 \u81ea\u52d5\u7de8\u865f + \u6bcf\u5c01\u72c0\u614b\u71c8\u865f\u986f\u73fe\uff1a
  \U0001f534 \u7d05\u71c8\uff1a\u672a\u8655\u7406 / \u5370\u5ea6\u4e8b\u52d9\uff08\u6700\u9ad8\uff09\u2192 \u7acb\u5373\u8655\u7406
  \U0001f7e1 \u9ec3\u71c8\uff1a\u7dca\u6025\uff08escalation/\u5230\u671f/\u50ac\u8fa6\uff09\u2192 \u7acb\u5373\u8655\u7406
  \U0001f7e2 \u7da0\u71c8\uff1a\u525b\u6536\u5230 / \u5df2\u8655\u7406
\u5206\u985e\uff1a\u4f9d\u5167\u6587\u81ea\u52d5\u5206\u985e\u2192\u66ab\u5b9a\uff08TENTATIVE\uff09\u2192\u6838\u51c6\u5f8c\u624d\u6b63\u5f0f\uff08APPROVED\uff09\u3002
\u5370\u5ea6\u4e8b\u52d9\u4e00\u51fa\u73fe\u7acb\u5373\u7d05\u71c8\u6700\u9ad8\u7d1a\u3002
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
import os, sys, re, hashlib
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import via_forge as F
import via_mailforge as M

UTC = timezone.utc

# \u71c8\u865f
RED, YELLOW, GREEN = "RED", "YELLOW", "GREEN"
LIGHT_LABEL = {RED: "\U0001f534 \u7d05\u71c8", YELLOW: "\U0001f7e1 \u9ec3\u71c8", GREEN: "\U0001f7e2 \u7da0\u71c8"}
LIGHT_COLOR = {RED: "#c96b5a", YELLOW: "#c4943a", GREEN: "#5a9e6f"}

# \u5370\u5ea6\u4e8b\u52d9\u5075\u6e2c\uff08\u7db2\u57df / \u95dc\u9375\u5b57\uff09\u2014\u2014 \u53ef\u4f9d\u9700\u6c42\u64f4\u5145\u5ba2\u6236/\u4f9b\u61c9\u5546\u540d\u55ae
_INDIA_DOMAINS = (".in",)
_INDIA_KEYWORDS = [
    "india", "\u5370\u5ea6", "mumbai", "delhi", "bangalore", "bengaluru", "chennai",
    "hyderabad", "pune", "kolkata", "gurgaon", "noida", "ahmedabad",
    "\u5b5f\u8cb7", "\u65b0\u5fb7\u91cc", "\u73ed\u52a0\u7f85\u723e", "inr", "rupee", "\u76e7\u6bd4",
]


def _is_india(text, participants):
    t = (text or "").lower()
    for kw in _INDIA_KEYWORDS:
        if kw in t:
            return True, kw
    for p in (participants or []):
        pl = p.lower()
        if any(pl.endswith(d) or (d + ">") in pl or (d + " ") in pl for d in _INDIA_DOMAINS):
            return True, p
        if "@" in pl and pl.split("@")[-1].endswith(".in"):
            return True, p
    return False, None


class SignalEngine:
    def __init__(self, cfg=None):
        self.cfg = cfg or F.load_config()
        self.mail = M.MailForgeEngine(self.cfg)

    def _sig_id(self, key):
        h = hashlib.blake2s(str(key).encode("utf-8"), digest_size=3).hexdigest().upper()
        return "VIA-SIG-%s-%s" % (datetime.now(UTC).strftime("%Y%m%d"), h)

    @staticmethod
    def _case_text(case, records):
        """\u84ee\u96c6\u8a72\u6848\u76f8\u95dc\u4fe1\u4ef6\u7684\u4e3b\u65e8+\u5167\u6587\uff08\u4f9b\u5370\u5ea6\u5075\u6e2c\uff09\u3002"""
        cl = case.get("cluster_label")
        parts = [case.get("subject", "")]
        for r in records:
            ei = r.get("email_intel") if isinstance(r, dict) else None
            if ei and ei.get("cluster_label") == cl:
                parts.append(r.get("structured", {}).get("preview", "") if isinstance(r.get("structured"), dict) else "")
                parts.append(ei.get("norm_subject", ""))
        return " ".join(p for p in parts if p)

    def signal_board(self, records, ci=None):
        ci = ci if ci is not None else self.mail.case_intelligence(records)
        items = []
        for c in ci["cases"]:
            fa = c["future_action"]
            text = self._case_text(c, records)
            india, india_hit = _is_india(text, c.get("participants", []))
            last = c.get("last_activity")
            kp = c.get("key_points") or {}
            stale = fa.get("stale_days", 0)

            # \u71c8\u865f\u5224\u5b9a\uff08\u9806\u5e8f = \u512a\u5148\u5e8f\uff09
            if india:
                light, reason = RED, "\u5370\u5ea6\u4e8b\u52d9\uff08\u6700\u9ad8\u7d1a\uff09"
            elif not fa["needs_reply"]:
                light, reason = GREEN, "\u5df2\u8655\u7406/\u5df2\u56de\u8986"
            elif fa["priority"] == "CRITICAL" or last == "Escalation" or "DEADLINE" in kp or last == "Reminder":
                light, reason = YELLOW, "\u7dca\u6025\uff08\u5347\u7d1a/\u5230\u671f/\u50ac\u8fa6\uff09"
            elif stale > 1:
                light, reason = RED, "\u672a\u8655\u7406\uff08\u9700\u56de\u8986\u4e14\u505c\u6ef1\uff09"
            else:
                light, reason = GREEN, "\u525b\u6536\u5230\uff08\u5f85\u8655\u7406\u4e2d\uff09"

            items.append({
                "signal_id": self._sig_id(c["case_id"]),
                "case_id": c["case_id"], "title": c.get("subject") or c.get("cluster_label"),
                "cluster": c.get("cluster_label"),
                "light": light, "light_label": LIGHT_LABEL[light], "light_color": LIGHT_COLOR[light],
                "reason": reason, "india": india, "india_hit": india_hit,
                "priority": fa["priority"], "needs_reply": fa["needs_reply"],
                "age_days": stale, "owner": ", ".join(fa.get("owed_by", [])) or "\u2014",
                "needs_immediate": light in (RED, YELLOW),
                # \u5206\u985e\uff1a\u81ea\u52d5\u5f97\u51fa\u4f46\u66ab\u5b9a\uff0c\u5f85\u6838\u51c6
                "classification": {"domain": None, "project": c.get("cluster_label"),
                                   "status": "TENTATIVE", "note": "\u81ea\u52d5\u5206\u985e\uff0c\u5f85\u6838\u51c6\u5f8c\u6b63\u5f0f\u78ba\u5b9a"},
            })

        # \u9678\u57df\u5206\u985e\uff08\u53d6 domain\uff09
        for it in items:
            for r in records:
                ei = r.get("email_intel") if isinstance(r, dict) else None
                if ei and ei.get("cluster_label") == it["cluster"]:
                    it["classification"]["domain"] = (r.get("aspects") or {}).get("content_domain")
                    break

        # \u6392\u5e8f\uff1a\u7d05\u2192\u9ec3\u2192\u7da0\uff1b\u5370\u5ea6\u512a\u5148\uff1b\u518d\u4f9d\u505c\u6ef1
        order = {RED: 0, YELLOW: 1, GREEN: 2}
        items.sort(key=lambda x: (0 if x["india"] else 1, order[x["light"]], -(x["age_days"] or 0)))

        immediate = [it for it in items if it["needs_immediate"]]
        india_items = [it for it in items if it["india"]]
        counts = {RED: 0, YELLOW: 0, GREEN: 0}
        for it in items:
            counts[it["light"]] += 1

        return {
            "items": items, "immediate": immediate, "india": india_items,
            "counts": counts,
            "stats": {"total": len(items), "red": counts[RED], "yellow": counts[YELLOW],
                      "green": counts[GREEN], "immediate": len(immediate), "india": len(india_items)},
            "light_label": LIGHT_LABEL, "light_color": LIGHT_COLOR,
            "policy": "\u7d05\u9ec3\u71c8\u7acb\u5373\u8655\u7406\uff1b\u5370\u5ea6\u4e8b\u52d9\u6700\u9ad8\u7d05\u71c8\uff1b\u5206\u985e\u6838\u51c6\u5f8c\u624d\u6b63\u5f0f",
        }

    # \u5206\u985e\u6838\u51c6\uff1a\u63d0\u51fa\u5f85\u6838\u51c6\u5206\u985e\u63d0\u6848\uff08\u4e32 pending\uff09
    def classification_proposals(self, records):
        board = self.signal_board(records)
        props = []
        for it in board["items"]:
            props.append({
                "kind": "CLASSIFICATION", "status": "PENDING",
                "case_id": it["case_id"], "title": it["title"],
                "proposed_domain": it["classification"]["domain"],
                "proposed_project": it["classification"]["project"],
                "light": it["light"], "india": it["india"],
                "proposal": "\u5c07\u6b64\u6848\u6b78\u985e\u70ba %s / %s" % (
                    it["classification"]["domain"] or "?", it["classification"]["project"] or "?"),
                "auto_applied": False,
            })
        return props


def selftest():
    import tempfile
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] signal: %s" % n)
        else: f += 1; print("  [FAIL] signal: %s" % n)
    cfg = F.load_config(); side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)
    d = tempfile.mkdtemp()
    mails = [
        # \u5370\u5ea6\u4e8b\u52d9 \u2192 \u7d05\u71c8\u6700\u9ad8
        ("rajesh@vendor.in", "Mumbai \u5de5\u5ee0 PO-500 \u4ea4\u671f", "<a@c>", "Mon, 06 Jul 2026 09:00:00 +0800", "\u8acb\u78ba\u8a8d India \u4ea4\u671f"),
        # \u7dca\u6025\uff08escalation\uff09\u2192 \u9ec3\u71c8
        ("pm.chen@corp.com", "\u5347\u7d1a PN-8801", "<b@c>", "Wed, 08 Jul 2026 09:00:00 +0800", "urgent escalate \u7ba1\u7406\u5c64"),
        # \u672a\u8655\u7406\u505c\u6ef1 \u2192 \u7d05\u71c8
        ("qa.li@corp.com", "PN-9942 \u91cd\u5de5", "<c@c>", "Sun, 28 Jun 2026 09:00:00 +0800", "\u8acb\u63d0\u4f9b\u65b9\u6848"),
        # \u5df2\u56de\u8986 \u2192 \u7da0\u71c8
        ("buyer@corp.com", "PO-100 \u4ea4\u671f", "<e@c>", "Fri, 04 Jul 2026 09:00:00 +0800", "\u8acb\u78ba\u8a8d"),
        ("me@corp.com", "Re: PO-100 \u4ea4\u671f", "<g@c>", "Fri, 04 Jul 2026 15:00:00 +0800", "\u63d0\u4f9b\u5982\u9644 \u5df2\u78ba\u8a8d"),
    ]
    for i, (fr, su, mid, dt, bd) in enumerate(mails):
        open(os.path.join(d, "m%d.eml" % i), "w", encoding="utf-8").write(
            "From: %s\nTo: team@corp.com\nSubject: %s\nMessage-ID: %s\nDate: %s\n\n%s" % (fr, su, mid, dt, bd))
    recs = M.MailForgeEngine(cfg).read_and_classify(d, do_fix=True)
    eng = SignalEngine(cfg)
    b = eng.signal_board(recs)
    ck("\u71c8\u865f\u677f\u7522\u751f", b["stats"]["total"] == 4)
    ck("\u5370\u5ea6\u4e8b\u52d9\u2192\u7d05\u71c8", any(it["india"] and it["light"] == "RED" for it in b["items"]))
    ck("\u5370\u5ea6\u6392\u6700\u524d", b["items"][0]["india"] is True)
    ck("\u7dca\u6025\u2192\u9ec3\u71c8", any(it["light"] == "YELLOW" for it in b["items"]))
    ck("\u672a\u8655\u7406\u505c\u6ef1\u2192\u7d05\u71c8", any(it["light"] == "RED" and not it["india"] for it in b["items"]))
    ck("\u5df2\u56de\u8986\u2192\u7da0\u71c8", any(it["light"] == "GREEN" for it in b["items"]))
    ck("\u7d05\u9ec3\u71c8\u9032\u7acb\u5373\u8655\u7406", len(b["immediate"]) == b["stats"]["red"] + b["stats"]["yellow"])
    ck("\u81ea\u52d5\u7de8\u865f", all(it["signal_id"].startswith("VIA-SIG-") for it in b["items"]))
    ck("\u5206\u985e\u66ab\u5b9a\u5f85\u6838\u51c6", all(it["classification"]["status"] == "TENTATIVE" for it in b["items"]))
    props = eng.classification_proposals(recs)
    ck("\u5206\u985e\u6838\u51c6\u63d0\u6848(\u4e32pending)", len(props) == 4 and all(not x["auto_applied"] for x in props))
    return p, f


def main():
    import argparse, json
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scan")
    args = ap.parse_args()
    if args.selftest:
        a, b = selftest(); print("signal: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)
    if args.scan:
        recs = M.MailForgeEngine().read_and_classify(args.scan, do_fix=True)
        print(json.dumps(SignalEngine().signal_board(recs)["stats"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
