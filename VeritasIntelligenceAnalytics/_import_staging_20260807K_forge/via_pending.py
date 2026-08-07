#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Pending  ——  via_pending.py   (\u5f85 \u00b7 \u6838\u51c6\u4f47\u5217)
================================================================================
\u91cd\u5927\u8b8a\u66f4\u4e0d\u9759\u9ed8\u57f7\u884c\uff0c\u800c\u662f\u9032 PENDING \u5f85\u6838\u51c6\uff08\u53ea\u589e\u4e0d\u6e1b\u3001\u6cbb\u7406\u53ef\u8ffd\uff09\uff1a
  \u2022 \u4fee\u5fa9\u6587\u5b57\u81ea\u52d5\u6d41\u7a0b\u518d\u9020 \u2192 DAMAGED \u6a94\u63d0\u51fa\u4fee\u5fa9\u63d0\u6848\uff0c\u5f85\u6838\u51c6
  \u2022 \u81ea\u52d5\u5229\u5bb3\u95dc\u4fc2\u4eba\u518d\u9020 \u2192 \u540c\u4eba\u4e0d\u540c\u4fe1\u7bb1/\u540d\u7a31\u6b78\u4e00\u63d0\u6848\uff0c\u5f85\u6838\u51c6
  \u2022 PENDING \u9805\u76ee\u7acb\u5373\u8655\u7406 \u2192 \u5217\u51fa + \u6838\u51c6\uff08\u72c0\u614b\u8f49\u63db\u9644\u52a0\uff0c\u4e0d\u8986\u5beb\uff09
================================================================================
"""
import os, sys, re, json, hashlib
from datetime import datetime, timezone
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import via_forge as F

UTC = timezone.utc


class PendingEngine:
    def __init__(self, cfg=None):
        self.cfg = cfg or F.load_config()
        self.ledger = os.path.join(self.cfg["paths"]["ledger"], "pending_ledger.jsonl")

    def _pid(self, kind, key):
        h = hashlib.blake2s(("%s|%s" % (kind, key)).encode("utf-8"), digest_size=4).hexdigest().upper()
        return "VIA-PEND-%s-%s" % (datetime.now(UTC).strftime("%Y%m%d"), h)

    def _append(self, rec):
        os.makedirs(os.path.dirname(self.ledger), exist_ok=True)
        with open(self.ledger, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ---------- \u4fee\u5fa9\u6587\u5b57\u81ea\u52d5\u6d41\u7a0b\u518d\u9020\uff08\u5f85\u6838\u51c6\uff09 ----------
    def text_repair_proposals(self, records):
        props = []
        for r in records:
            if not isinstance(r, dict) or r.get("status") != "OK":
                continue
            if r.get("health") in ("DAMAGED", "UNREADABLE"):
                key = r.get("doc_id", r.get("file_name", ""))
                props.append({
                    "pend_id": self._pid("REPAIR", key),
                    "kind": "TEXT_REPAIR", "status": "PENDING",
                    "target": r.get("file_name"), "doc_id": r.get("doc_id"),
                    "health": r.get("health"),
                    "proposal": "\u91cd\u65b0\u4ee5\u5b57\u5143\u5075\u6e2c\u89e3\u78bc + \u4e8c\u9032\u4f4d\u6e05\u6d17\u5f8c\u91cd\u5efa\u6587\u5b57",
                    "reason": "\u5075\u6e2c\u5230\u53ef\u80fd\u7684\u7de8\u78bc/\u640d\u640d\uff0c\u5efa\u8b70\u4eba\u5de5\u78ba\u8a8d\u5f8c\u518d\u4fee\u5fa9",
                    "auto_applied": False,
                    "created_at": datetime.now(UTC).isoformat(),
                })
        return props

    # ---------- \u81ea\u52d5\u5229\u5bb3\u95dc\u4fc2\u4eba\u518d\u9020\uff08\u5f85\u6838\u51c6\uff09 ----------
    @staticmethod
    def _name_of(addr):
        return addr.split("@")[0].lower() if "@" in addr else addr.lower()

    def stakeholder_reengineering(self, records):
        """\u5075\u6e2c\u540c\u4eba\u4e0d\u540c\u4fe1\u7bb1 / \u540d\u7a31\u6b78\u4e00\uff0c\u63d0\u51fa\u5408\u4f75\u63d0\u6848\uff08\u5f85\u6838\u51c6\uff0c\u4e0d\u81ea\u52d5\u5408\uff09\u3002"""
        addrs = set()
        for r in records:
            ei = r.get("email_intel") if isinstance(r, dict) else None
            if ei:
                for p in ei.get("participants", []):
                    addrs.add(p)
        # \u4f9d local-part \u5206\u7fa4\uff08\u540c\u540d\u4e0d\u540c\u57df\uff09
        by_name = defaultdict(list)
        for a in addrs:
            by_name[self._name_of(a)].append(a)
        props = []
        for name, group in by_name.items():
            if len(group) > 1:   # \u540c\u4e00 local-part \u51fa\u73fe\u65bc\u591a\u500b\u57df \u2192 \u53ef\u80fd\u540c\u4eba
                props.append({
                    "pend_id": self._pid("STAKEHOLDER", name),
                    "kind": "STAKEHOLDER_MERGE", "status": "PENDING",
                    "canonical": sorted(group)[0], "aliases": sorted(group),
                    "proposal": "\u5c07\u9019\u4e9b\u4fe1\u7bb1\u6b78\u4e00\u70ba\u540c\u4e00\u5229\u5bb3\u95dc\u4fc2\u4eba",
                    "reason": "\u76f8\u540c\u540d\u7a31(local-part)\u51fa\u73fe\u65bc\u4e0d\u540c\u57df\uff0c\u53ef\u80fd\u70ba\u540c\u4e00\u4eba",
                    "auto_applied": False,
                    "created_at": datetime.now(UTC).isoformat(),
                })
        return props

    # ---------- \u7522\u751f + \u5165\u4f47 ----------
    def regenerate(self, records):
        """\u91cd\u65b0\u7522\u751f\u6240\u6709\u5f85\u6838\u51c6\u63d0\u6848\u4e26\u9644\u52a0\u81f3\u4f47\u5217\uff08\u53ea\u589e\u4e0d\u6e1b\uff09\u3002"""
        props = self.text_repair_proposals(records) + self.stakeholder_reengineering(records)
        for p in props:
            self._append(p)
        return props

    def list_pending(self, kind=None):
        """PENDING \u9805\u76ee\u7acb\u5373\u8655\u7406\uff1a\u5217\u51fa\u5c1a\u672a\u6838\u51c6\u7684\uff08\u4f9d\u4f47\u5217\u72c0\u614b\u8f49\u63db\u89e3\u6790\uff09\u3002"""
        if not os.path.exists(self.ledger):
            return []
        latest = {}
        for line in open(self.ledger, encoding="utf-8"):
            try:
                rec = json.loads(line)
            except Exception:
                continue
            latest[rec["pend_id"]] = rec   # \u5f8c\u5beb\u80dc\u51fa\uff08\u72c0\u614b\u8f49\u63db\uff09
        out = [r for r in latest.values() if r.get("status") == "PENDING"]
        if kind:
            out = [r for r in out if r.get("kind") == kind]
        return out

    def approve(self, pend_id, decision="APPROVED", note=""):
        """\u6838\u51c6/\u99c1\u56de\uff08\u72c0\u614b\u8f49\u63db\u9644\u52a0\uff0c\u539f\u63d0\u6848\u4e0d\u522a\uff09\u3002"""
        rec = {"pend_id": pend_id, "kind": "DECISION", "status": decision,
               "note": note, "decided_at": datetime.now(UTC).isoformat()}
        self._append(rec)
        return rec

    def summary(self, records):
        tr = self.text_repair_proposals(records)
        sh = self.stakeholder_reengineering(records)
        return {"text_repair_pending": len(tr), "stakeholder_merge_pending": len(sh),
                "total_pending": len(tr) + len(sh),
                "policy": "\u91cd\u5927\u8b8a\u66f4\u9032\u5f85\u6838\u51c6\uff1b\u6838\u51c6\u524d\u4e0d\u81ea\u52d5\u5957\u7528\uff08\u53ea\u589e\u4e0d\u6e1b\uff09"}


def selftest():
    import tempfile
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] pending: %s" % n)
        else: f += 1; print("  [FAIL] pending: %s" % n)
    import via_mailforge as M
    cfg = F.load_config(); side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)
    d = tempfile.mkdtemp()
    # DAMAGED \u6a94
    with open(os.path.join(d, "bad.txt"), "wb") as fb:
        fb.write(bytes([0xff, 0xfe, 0x00, 0x01, 0xC0, 0x00, 0x02]))
    # \u540c\u4eba\u4e0d\u540c\u57df\uff08qa.li@corp.com / qa.li@vendor.com\uff09
    for i, fr in enumerate(["qa.li@corp.com", "qa.li@vendor.com"]):
        open(os.path.join(d, "m%d.eml" % i), "w", encoding="utf-8").write(
            "From: %s\nTo: t@c\nSubject: PN-9942 \u505c\u7dda\nMessage-ID: <m%d@c>\nDate: Mon, 06 Jul 2026 09:00:00 +0800\n\n\u8acb\u63d0\u4f9b" % (fr, i))
    recs = M.MailForgeEngine(cfg).read_and_classify(d, do_fix=True)

    eng = PendingEngine(cfg)
    tr = eng.text_repair_proposals(recs)
    ck("\u4fee\u5fa9\u6587\u5b57\u63d0\u6848(DAMAGED\u2192\u5f85\u6838\u51c6)", len(tr) >= 1 and tr[0]["status"] == "PENDING" and not tr[0]["auto_applied"])
    sh = eng.stakeholder_reengineering(recs)
    ck("\u5229\u5bb3\u95dc\u4fc2\u4eba\u518d\u9020(\u540c\u4eba\u4e0d\u540c\u57df\u2192\u5408\u4f75\u63d0\u6848)",
       any(set(x["aliases"]) == {"qa.li@corp.com", "qa.li@vendor.com"} for x in sh))
    props = eng.regenerate(recs)
    ck("\u5165\u4f47(\u53ea\u589e\u4e0d\u6e1b)", os.path.exists(eng.ledger) and len(props) >= 2)
    pend = eng.list_pending()
    ck("PENDING \u7acb\u5373\u8655\u7406(\u5217\u51fa)", len(pend) >= 2)
    # \u6838\u51c6\u5f8c\u4e0d\u518d\u5217\u5165 PENDING
    eng.approve(pend[0]["pend_id"], "APPROVED")
    pend2 = eng.list_pending()
    ck("\u6838\u51c6\u5f8c\u8f49\u51fa PENDING(\u72c0\u614b\u8f49\u63db)", len(pend2) == len(pend) - 1)
    ck("\u539f\u63d0\u6848\u4e0d\u522a(\u4f47\u5217\u53ea\u589e)", sum(1 for _ in open(eng.ledger, encoding="utf-8")) > len(props))
    s = eng.summary(recs)
    ck("summary", s["total_pending"] >= 2)
    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    if ap.parse_args().selftest:
        a, b = selftest(); print("pending: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)


if __name__ == "__main__":
    main()
