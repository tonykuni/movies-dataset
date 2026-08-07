#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA MailForge  ——  via_mailforge.py   (\u90f5\u7bb1/\u6587\u4ef6\u8b80\u53d6\u5206\u985e\u7d71\u5408\u529f\u80fd)
================================================================================
\u628a\u3010\u5206\u985e + \u7de8\u865f + \u4fee\u5fa9\u6587\u5b57\u3011\u5408\u6210\u4e00\u652f\u300c\u90f5\u7bb1/\u6587\u4ef6\u8b80\u53d6\u5206\u985e\u529f\u80fd\u300d\u3002

\u4f86\u6e90\u878d\u5408\uff1a
  \u2022 via_forge.py (\u5eab) \u2014 \u8b80\u53d6 39 \u683c\u5f0f(\u542b .eml/.msg) + \u4fee\u5fa9\u6587\u5b57(\u7de8\u78bc/big5/\u6bc0\u640d)
                        + \u6587\u4ef6\u5206\u985e(\u9818\u57df/\u654f\u611f/PII) + VIA-DOC \u7de8\u865f
  \u2022 email_case_tracker_v2 \u2014 \u90f5\u4ef6 activity \u898f\u5247\u5206\u985e + \u6848\u4ef6\u4e32\u63a5 + \u53c3\u8207\u8005/\u7d44\u7e54

\u5340\u5225\u65bc v2\uff1a\u4e0d\u4f9d\u8cf4\u7f3a\u5e2d\u7684 v1\uff1b\u4e0d\u7528 SQLite(\u6539 append-only JSONL\uff0c\u5b88 no_db_write)\uff1b
        \u6cbf\u7528 VIA auto-ID \u683c\u5f0f\u8207\u53ea\u589e\u4e0d\u6e1b\u6cbb\u7406\u3002

\u7d71\u4e00\u8f38\u51fa\uff1a\u6bcf\u7b46 = forge record + email_intel(activity/case_id/sender/participants/orgs)\u3002
================================================================================
"""

import os
import re
import sys
import json
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import via_forge as F

UTC = timezone.utc


def _now():
    return datetime.now(UTC).isoformat()


# ============================================================ \u90f5\u4ef6\u5206\u985e\u898f\u5247 ==
# activity \u898f\u5247(\u81ea email_case_tracker_v2\uff0c\u898f\u5247\u5f0f\u3001\u53ef\u7a3d\u6838\u3001append-only)
ACTIVITY_RULES = [
    ("Escalation", [r"escalat", r"\u5347\u7d1a", r"urgent", r"management\s+attention", r"\u6025\u4ef6"]),
    ("Reminder",   [r"reminder", r"follow\s*up", r"\u50ac", r"\u518d\u6b21\u63d0\u9192", r"still\s+waiting"]),
    ("Delivery",   [r"attached", r"please\s+find", r"as\s+requested", r"\u63d0\u4f9b\u5982\u9644", r"\u6aa2\u9644", r"deliver"]),
    ("Commitment", [r"will\s+provide", r"we\s+commit", r"by\s+\d", r"\u627f\u8afe", r"\u9810\u8a08.*\u63d0\u4f9b", r"deadline"]),
    ("Request",    [r"please\s+(provide|send|share|confirm)", r"could\s+you", r"\u8acb\u63d0\u4f9b", r"\u8acb\u5354\u52a9", r"\u9700\u8981"]),
    ("Response",   [r"^\s*(re|\u56de\u8986)[:\uff1a]", r"in\s+response", r"\u56de\u8986\u5982\u4e0b", r"as\s+below"]),
]
DEFAULT_ACTIVITY = "Correspondence"
RE_EMAIL_ADDR = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
RE_SUBJ_PREFIX = re.compile(r"^\s*(re|fwd|fw|\u56de\u8986|\u8f49\u5bc4)[:\uff1a]\s*", re.IGNORECASE)
RE_BRACKET = re.compile(r"[\[\(\u3010\uff08][^\]\)\u3011\uff09]*[\]\)\u3011\uff09]")
# \u96fb\u5b50\u696d\u7968\u865f\u932f\uff1aPN-9942 / PO-100 / ECN-12 / RMA-7\u2026\uff08\u5f8c\u9762\u5e36 dash \u62162+\u6578\u5b57\uff0c\u6216\u7121 dash \u4f463+\u6578\u5b57\uff09
RE_TICKET = re.compile(r"\b([A-Za-z]{2,5}-\d{2,6})\b|\b([A-Za-z]{2,5}\d{3,6})\b")


def classify_activity(subject, body):
    text = "%s\n%s" % (subject or "", (body or "")[:2000])
    for act, patterns in ACTIVITY_RULES:
        for p in patterns:
            if re.search(p, text, re.IGNORECASE | re.MULTILINE):
                return act
    return DEFAULT_ACTIVITY


def norm_person(raw):
    m = RE_EMAIL_ADDR.search(raw or "")
    return m.group(0).lower() if m else (raw or "").strip().lower()


def display_name(raw):
    name = re.sub(r"<[^>]*>", "", raw or "").strip().strip('"')
    return name or norm_person(raw)


def norm_subject(subj):
    """\u5265\u9664 Re:/Fwd:/\u56de\u8986: \u524d\u7db4 + [\u5df2\u89e3\u6c7a] \u985e\u6a19\u7c64\uff0c\u4f9b\u6848\u4ef6\u4e32\u63a5\u3002"""
    s = subj or ""
    prev = None
    while prev != s:
        prev = s
        s = RE_SUBJ_PREFIX.sub("", s).strip()
    s = RE_BRACKET.sub(" ", s)                 # \u53bb [\u5df2\u89e3\u6c7a]/\uff08\u6025\u4ef6\uff09 \u7b49\u6a19\u7c64
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()


def thread_key(subject, headers=None):
    """\u7a69\u5b9a\u4e3b\u65e8\u7fa4\u7d44\u9375\uff1a\u771f\u5be6 threading header > \u7968\u865f\u932f > \u6e05\u7406\u5f8c\u4e3b\u65e8\u3002
    \u2192 \u540c\u4e00\u4e3b\u984c\u7684\u591a\u6b21\u56de\u8986/\u8f49\u5bc4\uff08\u6a94\u540d\u3001\u6642\u9593\u3001\u5c3e\u5b57\u4e0d\u540c\uff09\u90fd\u6b78\u540c\u4e00\u7fa4\u3002"""
    headers = headers or {}
    for h in ("In-Reply-To", "References"):
        v = headers.get(h, "")
        m = re.search(r"<([^>]+)>", v)
        if m:
            return "MID:" + m.group(1).strip().lower()
    mt = RE_TICKET.search(subject or "")
    if mt:
        tok = mt.group(1) or mt.group(2)
        return "TKT:" + re.sub(r"[-\s]", "", tok).lower()
    return "SUB:" + norm_subject(subject)


# ============================================================ \u4e3b\u9ad4\u5f15\u64ce ==
class MailForgeEngine:
    """\u7d71\u4e00\u90f5\u7bb1/\u6587\u4ef6\u8b80\u53d6\u5206\u985e\uff1a\u8b80\u53d6\u2192\u4fee\u5fa9\u2192\u5206\u985e\u2192\u7de8\u865f\u3002"""

    def __init__(self, cfg=None):
        self.cfg = cfg or F.load_config()
        self.forge = F.ForgeEngine(self.cfg)
        self.ledger_path = os.path.join(self.cfg["paths"]["ledger"], "mailforge_ledger.jsonl")
        self._case_ids = {}   # norm_subject -> case_id
        self._case_seq = 0

    # --- \u7de8\u865f\uff1a\u6848\u4ef6 VIA-CASE-YYYYMMDD-######\uff08\u4f9d thread_key \u4e32\u63a5\uff09---
    def _case_id(self, tkey):
        if tkey not in self._case_ids:
            self._case_seq += 1
            day = datetime.now(UTC).strftime("%Y%m%d")
            self._case_ids[tkey] = "VIA-CASE-%s-%06d" % (day, self._case_seq)
        return self._case_ids[tkey]

    # --- \u90f5\u4ef6\u60c5\u5831\u5c64(\u50c5 EMAIL_*) ---
    def _email_intel(self, rec):
        fam = rec.get("format_family")
        if fam not in ("EMAIL_EML", "EMAIL_MSG"):
            return None
        struct = rec.get("structured") or {}
        hdr = struct.get("headers", {}) if isinstance(struct, dict) else {}
        subject = hdr.get("Subject", "") or (rec.get("aspects", {}) or {}).get("title", "")
        body = rec.get("text_preview", "")
        es = F.tl_email_structure(struct) or {}
        tkey = thread_key(subject, hdr)
        # \u6848\u65cf\u7fa4\u6a19\u793a\uff1a\u7968\u865f\u932f/\u4e3b\u984c\u4f5c\u70ba\u53ef\u8b80\u7fa4\u7c64
        if tkey.startswith("TKT:"):
            cluster = tkey[4:].upper()
        elif tkey.startswith("MID:"):
            cluster = norm_subject(subject)[:40]
        else:
            cluster = tkey[4:][:40]
        return {
            "is_email": True,
            "activity": classify_activity(subject, body),
            "case_id": self._case_id(tkey),
            "thread_key": tkey,
            "cluster_label": cluster,            # \u6848\u65cf\u7fa4\u6a19\u793a\uff08\u4f8b PN9942\uff09
            "norm_subject": norm_subject(subject),
            "sender": norm_person(hdr.get("From", "")),
            "sender_name": display_name(hdr.get("From", "")),  # \u5bc4\u4ef6\u8005\u6a19\u793a
            "participants": es.get("participants", []),
            "organizations": es.get("organizations", []),
        }

    def read_and_classify(self, target, do_fix=True, append_ledger=True):
        """\u8b80\u53d6\u90f5\u7bb1\u532f\u51fa/\u6587\u4ef6 \u2192 \u4fee\u5fa9\u2192\u5206\u985e\u2192\u7de8\u865f\uff0c\u56de\u50b3\u7d71\u4e00 records\u3002"""
        base = self.forge.scan(target, do_fix=do_fix)  # \u8b80\u53d6+\u4fee\u5fa9+\u6587\u4ef6\u5206\u985e+VIA-DOC \u7de8\u865f
        unified = []
        for rec in base:
            if not isinstance(rec, dict) or rec.get("status") in ("SKIP", "ERROR"):
                unified.append(rec)
                continue
            intel = self._email_intel(rec)
            rec["email_intel"] = intel  # None for non-email docs
            rec["kind"] = "EMAIL" if intel else "DOCUMENT"
            unified.append(rec)
        if append_ledger:
            self._append(unified)
        return unified

    def _append(self, records):
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        with open(self.ledger_path, "a", encoding="utf-8") as fh:
            for r in records:
                if not isinstance(r, dict) or r.get("status") in ("SKIP", "ERROR"):
                    continue
                slim = {
                    "doc_id": r.get("doc_id"), "kind": r.get("kind"),
                    "file_name": r.get("file_name"), "format_family": r.get("format_family"),
                    "health": r.get("health"),
                    "content_domain": (r.get("aspects") or {}).get("content_domain"),
                    "sensitivity": (r.get("aspects") or {}).get("sensitivity"),
                    "pii": (r.get("aspects") or {}).get("pii", []),
                    "email_intel": r.get("email_intel"),
                    "logged_at": _now(),
                }
                fh.write(json.dumps(slim, ensure_ascii=False) + "\n")

    # --- \u56de\u8986\u72c0\u614b + \u5229\u5bb3\u95dc\u4fc2\u4eba\u7be9\u9078\uff08\u53bb\u91cd\u4f46\u4e0d\u79fb\u9664\uff1b\u5f85\u56de\u8986\u512a\u5148\uff09 ---
    @staticmethod
    def _msg_time(rec):
        hdr = ((rec.get("structured") or {}).get("headers", {}))
        d = hdr.get("Date", "")
        if d:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(d)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except Exception:
                pass
        return None

    def reply_status(self, records, target=None):
        """\u4f9d\u6848\u4ef6\u7d50\u56de\u8986\u72c0\u614b\uff1b\u53ef\u4f9d target \u5229\u5bb3\u95dc\u4fc2\u4eba\u7be9\u9078\uff1b\u5f85\u56de\u8986\u512a\u5148\u6392\u5e8f\u3002
        \u53bb\u91cd\uff1a\u91cd\u8907\u4fe1\u4e0d\u91cd\u8907\u8a08\u5165\u72c0\u614b\uff0c\u4f46\u4fdd\u7559\u65bc\u5e33\u672c\uff08\u53ea\u589e\u4e0d\u6e1b\uff09\u3002"""
        emails = [r for r in records if isinstance(r, dict) and r.get("status") == "OK"
                  and r.get("kind") == "EMAIL" and r.get("email_intel")]
        kept_dup = sum(1 for r in emails if r.get("is_duplicate"))
        active = [r for r in emails if not r.get("is_duplicate")]   # \u53bb\u91cd\uff1a\u4e0d\u91cd\u8907\u8a08\u5165

        cases = {}
        for r in active:
            cid = r["email_intel"].get("case_id") or "NO-CASE"
            cases.setdefault(cid, []).append(r)

        AWAIT_REPLY = ("Request", "Reminder", "Escalation")
        AWAIT_DELIV = ("Commitment",)
        RESOLVED = ("Delivery", "Response")
        out = []
        for cid, msgs in cases.items():
            msgs.sort(key=lambda r: (self._msg_time(r) or datetime.min.replace(tzinfo=UTC)))
            last = msgs[-1]
            ei = last["email_intel"]
            act = ei.get("activity")
            sender = ei.get("sender")
            parts = []
            for m in msgs:
                for p in m["email_intel"].get("participants", []):
                    if p not in parts:
                        parts.append(p)
            others = [p for p in parts if p != sender]
            if act in AWAIT_REPLY:
                needs_reply, state, owed_by = True, "AWAITING_REPLY", others
            elif act in AWAIT_DELIV:
                needs_reply, state, owed_by = True, "AWAITING_DELIVERY", [sender]
            elif act in RESOLVED:
                needs_reply, state, owed_by = False, "REPLIED", []
            else:
                needs_reply, state, owed_by = False, "OPEN", []
            lt = self._msg_time(last)
            stale_days = (datetime.now(UTC) - lt).days if lt else None
            if act == "Escalation":
                priority = "CRITICAL"
            elif needs_reply and stale_days is not None and stale_days > 2:
                priority = "HIGH"
            elif needs_reply:
                priority = "MED"
            else:
                priority = "LOW"
            out.append({
                "case_id": cid, "subject": ei.get("norm_subject"),
                "last_activity": act, "last_sender": sender,
                "state": state, "needs_reply": needs_reply,
                "owed_by": owed_by, "priority": priority,
                "stale_days": stale_days, "message_count": len(msgs),
                "participants": parts,
            })

        if target:
            t = target.strip().lower()
            out = [c for c in out if any(t in p.lower() for p in c["participants"])]

        prio_rank = {"CRITICAL": 0, "HIGH": 1, "MED": 2, "LOW": 3}
        out.sort(key=lambda c: (0 if c["needs_reply"] else 1,      # \u5f85\u56de\u8986\u5148
                                prio_rank.get(c["priority"], 9),
                                -(c["stale_days"] or 0)))
        return {
            "target": target,
            "cases": out,
            "needs_reply_count": sum(1 for c in out if c["needs_reply"]),
            "dedup": {"duplicates_retained": kept_dup, "active_counted": len(active),
                      "policy": "\u53bb\u91cd\u4f46\u4e0d\u79fb\u9664\uff08\u53ea\u589e\u4e0d\u6e1b\uff09"},
        }

    def stakeholders(self, records):
        """\u5f9e\u90f5\u4ef6\u7d2f\u7a4d\u5229\u5bb3\u95dc\u4fc2\u4eba\u540d\u55ae\uff08\u4f9b FILTER BY TARGET KEY STAKEHOLDER\uff09\u3002"""
        from collections import Counter
        seen = Counter(); orgs = {}
        for r in records:
            if not (isinstance(r, dict) and r.get("email_intel")):
                continue
            for p in r["email_intel"].get("participants", []):
                seen[p] += 1
                if "@" in p:
                    orgs[p] = p.split("@")[-1]
        return [{"stakeholder": p, "message_count": n, "org": orgs.get(p, "")}
                for p, n in seen.most_common()]

    # --- \u56de\u9023\u539f\u59cb\u90f5\u4ef6\u9023\u7d50\uff08Outlook / Gmail\uff09---
    @staticmethod
    def original_link(headers, source_method=""):
        mid = (headers or {}).get("Message-ID", "").strip().strip("<>")
        if not mid:
            return {"outlook": None, "gmail": None, "message_id": None}
        return {
            "message_id": mid,
            "outlook": "outlook://message-id/%s" % mid,
            "gmail": "https://mail.google.com/mail/u/0/#search/rfc822msgid:%s" % mid,
        }

    _KP_PATTERNS = [
        ("DECISION", [r"\u6c7a\u5b9a", r"\u6838\u51c6", r"\u78ba\u8a8d", r"\u62cd\u677f", r"approved?", r"decision", r"sign[\s-]?off"]),
        ("RISK",     [r"\u98a8\u96aa", r"\u554f\u984c", r"\u7570\u5e38", r"\u4e0d\u826f", r"\u505c\u7dda", r"delay", r"risk", r"issue", r"block"]),
        ("DEADLINE", [r"\u622a\u6b62", r"\u671f\u9650", r"\u4ea4\u671f", r"deadline", r"due", r"by\s+\d", r"\d{1,2}/\d{1,2}"]),
        ("REQUEST",  [r"\u8acb\u63d0\u4f9b", r"\u8acb\u5354\u52a9", r"\u9700\u8981", r"\u8acb\u78ba\u8a8d", r"please\s+(provide|confirm|send)", r"could\s+you"]),
        ("CHANGE",   [r"\u8b8a\u66f4", r"\u4fee\u6539", r"ecn", r"\u6539\u7248", r"change", r"revision"]),
    ]

    @classmethod
    def _key_points(cls, text):
        t = (text or "")[:4000]
        found = {}
        for label, pats in cls._KP_PATTERNS:
            for p in pats:
                m = re.search(p, t, re.IGNORECASE)
                if m:
                    seg = t[max(0, m.start() - 12):m.start() + 24].replace("\n", " ").strip()
                    found.setdefault(label, seg)
                    break
        return found

    def case_intelligence(self, records, target=None):
        """\u6bcf\u6848\u4ef6\u77e9\u9663\u5316\u60c5\u5831\uff08\u5168\u672c\u6a5f\u3001\u898f\u5247\u5f0f\u3001\u7121 LLM\uff09\uff1a
        \u6642\u9593\u7dda + \u8acb\u6c42/\u89e3\u6c7a\u65b9\u6848\u77e9\u9663 + \u672a\u4f86\u884c\u52d5\u77e9\u9663 + \u95dc\u9375\u9ede + \u56de\u9023\u9023\u7d50\u3002"""
        emails = [r for r in records if isinstance(r, dict) and r.get("status") == "OK"
                  and r.get("kind") == "EMAIL" and r.get("email_intel")]
        active = [r for r in emails if not r.get("is_duplicate")]
        by_case = {}
        for r in active:
            by_case.setdefault(r["email_intel"]["case_id"], []).append(r)

        AWAIT_REPLY = ("Request", "Reminder", "Escalation")
        AWAIT_DELIV = ("Commitment",)
        out = []
        for cid, msgs in by_case.items():
            msgs.sort(key=lambda r: (self._msg_time(r) or datetime.min.replace(tzinfo=UTC)))
            ei0 = msgs[0]["email_intel"]
            timeline, requests, solutions, keypoints = [], [], [], {}
            for r in msgs:
                ei = r["email_intel"]
                hdr = (r.get("structured") or {}).get("headers", {})
                t = self._msg_time(r)
                timeline.append({
                    "time": t.isoformat() if t else None,
                    "sender": ei.get("sender"), "activity": ei.get("activity"),
                    "link": self.original_link(hdr, r.get("source_method", "")),
                })
                if ei.get("activity") in ("Request", "Reminder"):
                    requests.append({"from": ei.get("sender"), "time": t.isoformat() if t else None,
                                     "activity": ei.get("activity")})
                if ei.get("activity") in ("Delivery", "Response", "Commitment"):
                    solutions.append({"by": ei.get("sender"), "time": t.isoformat() if t else None,
                                      "activity": ei.get("activity")})
                for k, v in self._key_points(r.get("text_preview", "")).items():
                    keypoints.setdefault(k, v)

            last = msgs[-1]; lei = last["email_intel"]
            lact = lei.get("activity"); lsender = lei.get("sender")
            parts = []
            for m in msgs:
                for p in m["email_intel"].get("participants", []):
                    if p not in parts:
                        parts.append(p)
            others = [p for p in parts if p != lsender]
            lt = self._msg_time(last)
            stale = (datetime.now(UTC) - lt).days if lt else 0

            if lact in AWAIT_REPLY:
                needs, owed = True, others
                act_desc = "\u56de\u8986 %s \u7684%s" % (lsender, {"Request": "\u8acb\u6c42", "Reminder": "\u50ac\u4fc3", "Escalation": "\u5347\u7d1a"}.get(lact, ""))
            elif lact in AWAIT_DELIV:
                needs, owed = True, [lsender]
                act_desc = "\u4ea4\u4ed8 %s \u627f\u8afe\u7684\u4e8b\u9805" % lsender
            else:
                needs, owed, act_desc = False, [], "\u7121\u5f85\u8fa6\uff08\u5df2\u56de\u8986/\u7d50\u6848\uff09"
            sens = (last.get("aspects") or {}).get("sensitivity", "")
            urgency = min(100, (40 if lact == "Escalation" else 0) + min(stale, 10) * 6 + (20 if needs else 0))
            impact = min(100, (35 if lact == "Escalation" else 0) + (35 if sens == "CONFIDENTIAL" else 15) + (20 if needs else 0))
            clarity = 80 if lact in ("Request", "Commitment", "Delivery") else 55
            priority = ("CRITICAL" if lact == "Escalation" else
                        "HIGH" if needs and stale > 2 else
                        "MED" if needs else "LOW")
            out.append({
                "case_id": cid, "cluster_label": ei0.get("cluster_label"),
                "subject": ei0.get("norm_subject"),
                "participants": parts, "message_count": len(msgs),
                "timeline": timeline,
                "request_matrix": requests, "solution_matrix": solutions,
                "key_points": keypoints,
                "future_action": {
                    "needs_reply": needs, "owed_by": owed, "action": act_desc,
                    "urgency_score": urgency, "impact_score": impact, "clarity_score": clarity,
                    "priority": priority, "stale_days": stale,
                    "suggested_next_step": ("\u5148\u56de\u8986\uff1a" + act_desc) if needs else "\u7121\u9700\u52d5\u4f5c",
                },
                "original_link": self.original_link(
                    (last.get("structured") or {}).get("headers", {}), last.get("source_method", "")),
            })

        if target:
            tl = target.strip().lower()
            out = [c for c in out if any(tl in p.lower() for p in c["participants"])]
        prio = {"CRITICAL": 0, "HIGH": 1, "MED": 2, "LOW": 3}
        out.sort(key=lambda c: (0 if c["future_action"]["needs_reply"] else 1,
                                prio.get(c["future_action"]["priority"], 9),
                                -c["future_action"]["stale_days"]))
        return {"target": target, "cases": out,
                "needs_reply_count": sum(1 for c in out if c["future_action"]["needs_reply"])}

    def clusters(self, records, target=None):
        """\u6309\u4e3b\u984c\u5206\u7fa4\uff08\u6848\u65cf\uff09\uff0c\u6bcf\u7fa4\u6a19\u793a\u7fa4\u7c64 + \u5bc4\u4ef6\u8005 + \u8a0a\u606f\u6578\u3002
        \u540c\u4e00\u4e3b\u984c\u7684\u591a\u6b21\u56de\u8986\u5806\u7a4d\u5f52\u540c\u4e00\u7fa4\uff08\u6a94\u540d/\u6642\u9593\u4e0d\u540c\u4e0d\u62c6\u7fa4\uff09\u3002"""
        emails = [r for r in records if isinstance(r, dict) and r.get("status") == "OK"
                  and r.get("kind") == "EMAIL" and r.get("email_intel")]
        from collections import Counter
        groups = {}
        for r in emails:
            ei = r["email_intel"]
            cid = ei.get("case_id")
            g = groups.setdefault(cid, {
                "case_id": cid, "cluster_label": ei.get("cluster_label"),
                "thread_key": ei.get("thread_key"), "subject": ei.get("norm_subject"),
                "message_count": 0, "duplicates_retained": 0,
                "senders": Counter(), "participants": set(), "activities": Counter(),
            })
            g["message_count"] += 1
            if r.get("is_duplicate"):
                g["duplicates_retained"] += 1
            g["senders"][ei.get("sender")] += 1
            for p in ei.get("participants", []):
                g["participants"].add(p)
            g["activities"][ei.get("activity")] += 1
        out = []
        for g in groups.values():
            if target and not any(target.strip().lower() in p.lower() for p in g["participants"]):
                continue
            out.append({
                "case_id": g["case_id"], "cluster_label": g["cluster_label"],
                "thread_key": g["thread_key"], "subject": g["subject"],
                "message_count": g["message_count"],
                "duplicates_retained": g["duplicates_retained"],
                "senders": [{"sender": s, "count": n} for s, n in g["senders"].most_common()],
                "participants": sorted(g["participants"]),
                "activities": dict(g["activities"]),
            })
        out.sort(key=lambda c: -c["message_count"])
        return {"target": target, "clusters": out, "cluster_count": len(out)}

    def summary(self, records):
        ok = [r for r in records if isinstance(r, dict) and r.get("status") == "OK"]
        emails = [r for r in ok if r.get("kind") == "EMAIL"]
        from collections import Counter
        acts = Counter(r["email_intel"]["activity"] for r in emails if r.get("email_intel"))
        cases = set(r["email_intel"]["case_id"] for r in emails
                    if r.get("email_intel") and r["email_intel"]["case_id"])
        health = Counter(r.get("health") for r in ok)
        domains = Counter((r.get("aspects") or {}).get("content_domain") for r in ok)
        return {
            "ok": len(ok), "total": len(ok), "emails": len(emails), "documents": len(ok) - len(emails),
            "cases": len(cases), "activities": dict(acts),
            "health": dict(health), "domains": dict(domains),
        }


# ==================================================================== SELFTEST ==
def selftest():
    import tempfile
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] mailforge: %s" % n)
        else: f += 1; print("  [FAIL] mailforge: %s" % n)

    cfg = F.load_config()
    side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)

    d = tempfile.mkdtemp()
    # two emails in the same thread (Request -> Response) + one document
    open(os.path.join(d, "m1.eml"), "w", encoding="utf-8").write(
        "From: qa.li@corp.com\nTo: rd.wang@corp.com\nSubject: PN-9942 AOI \u505c\u7dda\n\n\u8acb\u63d0\u4f9b\u91cd\u5de5\u65b9\u6848 \u9700\u8981\u5354\u52a9")
    open(os.path.join(d, "m2.eml"), "w", encoding="utf-8").write(
        "From: rd.wang@corp.com\nTo: qa.li@corp.com\nSubject: Re: PN-9942 AOI \u505c\u7dda\n\n\u63d0\u4f9b\u5982\u9644 \u91cd\u5de5\u65b9\u6848\u5df2\u6aa2\u9644")
    open(os.path.join(d, "spec.md"), "w", encoding="utf-8").write("# \u898f\u683c\u66f8\n\u71df\u6536 \u6bdb\u5229")

    eng = MailForgeEngine(cfg)
    recs = eng.read_and_classify(d, do_fix=True)
    ok = [r for r in recs if r.get("status") == "OK"]
    ck("read all 3 items", len(ok) == 3)

    emails = [r for r in ok if r.get("kind") == "EMAIL"]
    docs = [r for r in ok if r.get("kind") == "DOCUMENT"]
    ck("2 emails + 1 document", len(emails) == 2 and len(docs) == 1)

    # \u7de8\u865f\uff1a\u6bcf\u7b46\u90fd\u6709 VIA-DOC id
    ck("all have VIA-DOC id", all(r.get("doc_id", "").startswith("VIA-DOC-") for r in ok))

    # \u4fee\u5fa9\u6587\u5b57\uff1ahealth \u6b04\u4f4d\u5b58\u5728
    ck("repair health present", all(r.get("health") in ("OK", "REPAIRED", "DAMAGED", "UNREADABLE", "DUPLICATE") for r in ok))

    # \u5206\u985e\uff1a\u6587\u4ef6\u5c64(\u9818\u57df/\u654f\u611f) + \u90f5\u4ef6\u5c64(activity)
    ck("doc classified (domain)", all((r.get("aspects") or {}).get("content_domain") for r in ok))
    byname = {r["file_name"]: r for r in emails}
    m1 = byname.get("m1.eml", {}); m2 = byname.get("m2.eml", {})
    ck("m1 activity = Request", m1.get("email_intel", {}).get("activity") == "Request")
    ck("m2 activity = Delivery", m2.get("email_intel", {}).get("activity") in ("Delivery", "Response"))

    # \u6848\u4ef6\u4e32\u63a5\uff1aRe: \u540c\u4e3b\u65e8 \u2192 \u540c\u4e00 VIA-CASE
    ck("same thread -> same case_id",
       m1.get("email_intel", {}).get("case_id") == m2.get("email_intel", {}).get("case_id")
       and m1.get("email_intel", {}).get("case_id", "").startswith("VIA-CASE-"))

    # \u53c3\u8207\u8005/\u7d44\u7e54
    ck("participants extracted", "qa.li@corp.com" in m1.get("email_intel", {}).get("participants", []))
    ck("org from domain", "corp.com" in m1.get("email_intel", {}).get("organizations", []))

    # \u6587\u4ef6\u4e0d\u5e36 email_intel
    ck("document has no email_intel", docs[0].get("email_intel") is None)

    # append-only JSONL ledger
    ck("ledger written", os.path.exists(eng.ledger_path))
    n1 = sum(1 for _ in open(eng.ledger_path, encoding="utf-8"))
    eng.read_and_classify([os.path.join(d, "spec.md")], do_fix=True)
    n2 = sum(1 for _ in open(eng.ledger_path, encoding="utf-8"))
    ck("ledger append-only grows", n2 > n1)

    # summary
    s = eng.summary(recs)
    ck("summary counts", s["emails"] == 2 and s["documents"] == 1 and s["cases"] >= 1)
    ck("summary has activities", "Request" in s["activities"])

    # --- \u56de\u8986\u72c0\u614b + \u5229\u5bb3\u95dc\u4fc2\u4eba\u7be9\u9078 + \u53bb\u91cd\u4fdd\u7559 ---
    d2 = tempfile.mkdtemp()
    # case A: request awaiting reply (no response yet)
    open(os.path.join(d2, "a1.eml"), "w", encoding="utf-8").write(
        "From: qa.li@corp.com\nTo: rd.wang@corp.com\nSubject: PN-1 \u7d1a\u4ef6\nDate: Mon, 06 Jul 2026 09:00:00 +0800\n\n\u8acb\u63d0\u4f9b\u65b9\u6848")
    # case B: request then delivery (replied)
    open(os.path.join(d2, "b1.eml"), "w", encoding="utf-8").write(
        "From: pm.chen@corp.com\nTo: qa.li@corp.com\nSubject: PN-2 \u554f\u984c\nDate: Mon, 06 Jul 2026 09:00:00 +0800\n\n\u8acb\u5354\u52a9")
    open(os.path.join(d2, "b2.eml"), "w", encoding="utf-8").write(
        "From: qa.li@corp.com\nTo: pm.chen@corp.com\nSubject: Re: PN-2 \u554f\u984c\nDate: Mon, 06 Jul 2026 15:00:00 +0800\n\n\u63d0\u4f9b\u5982\u9644 \u5df2\u6aa2\u9644")
    # duplicate of a1 (same content) -> must be retained, not counted
    open(os.path.join(d2, "a1_copy.eml"), "w", encoding="utf-8").write(
        "From: qa.li@corp.com\nTo: rd.wang@corp.com\nSubject: PN-1 \u7d1a\u4ef6\nDate: Mon, 06 Jul 2026 09:00:00 +0800\n\n\u8acb\u63d0\u4f9b\u65b9\u6848")
    recs2 = eng.read_and_classify(d2, do_fix=True)
    rs = eng.reply_status(recs2)
    caseA = next((c for c in rs["cases"] if "pn-1" in (c["subject"] or "")), None)
    caseB = next((c for c in rs["cases"] if "pn-2" in (c["subject"] or "")), None)
    ck("case A awaiting reply", caseA and caseA["needs_reply"] and caseA["state"] == "AWAITING_REPLY")
    ck("case B replied", caseB and not caseB["needs_reply"] and caseB["state"] == "REPLIED")
    ck("needs-reply sorted first", rs["cases"][0]["needs_reply"] is True)
    ck("dedup retained not removed", rs["dedup"]["duplicates_retained"] >= 1)
    ck("owed_by identifies counterpart", caseA and "rd.wang@corp.com" in caseA["owed_by"])

    # filter by target key stakeholder
    rs_f = eng.reply_status(recs2, target="rd.wang@corp.com")
    ck("filter by stakeholder", all("rd.wang@corp.com" in c["participants"] for c in rs_f["cases"])
       and len(rs_f["cases"]) >= 1)
    stk = eng.stakeholders(recs2)
    ck("stakeholder roster", any(s["stakeholder"] == "qa.li@corp.com" for s in stk))

    # --- \u4e3b\u984c\u5206\u7fa4\uff1a\u5c3e\u5b57/\u6a19\u7c64\u4e0d\u540c\u4f46\u540c\u7968\u865f \u2192 \u540c\u4e00\u7fa4 ---
    ck("thread_key ticket anchor",
       thread_key("Re: RE: PN-9942 AOI \u505c\u7dda \u8acb\u63d0\u4f9b\u65b9\u6848") ==
       thread_key("PN-9942 AOI \u505c\u7dda") == "TKT:pn9942")
    ck("thread_key strips bracket tag",
       thread_key("Fwd: PN-9942 [\u5df2\u89e3\u6c7a]") == "TKT:pn9942")
    ck("thread_key no false merge (Q2)",
       thread_key("Q2 \u8ca1\u5831") != thread_key("Q2 \u9810\u7b97") or "TKT:" not in thread_key("Q2 \u8ca1\u5831"))

    d3 = tempfile.mkdtemp()
    variants = ["PN-7788 \u8a2d\u8a08\u8b8a\u66f4", "Re: PN-7788 \u8a2d\u8a08\u8b8a\u66f4",
                "RE: RE: PN-7788 \u8a2d\u8a08\u8b8a\u66f4 \u8acb\u78ba\u8a8d", "Fwd: PN-7788 \u8a2d\u8a08\u8b8a\u66f4 [\u5df2\u7d50\u6848]"]
    for i, sub in enumerate(variants):
        who = "qa.li@corp.com" if i % 2 == 0 else "rd.wang@corp.com"
        open(os.path.join(d3, "v%d.eml" % i), "w", encoding="utf-8").write(
            "From: %s\nTo: other@corp.com\nSubject: %s\n\n\u5167\u6587%d" % (who, sub, i))
    recs3 = eng.read_and_classify(d3, do_fix=True)
    cl = eng.clusters(recs3)
    ck("4 variants -> 1 cluster", cl["cluster_count"] == 1 and cl["clusters"][0]["message_count"] == 4)
    ck("cluster labeled by ticket", cl["clusters"][0]["cluster_label"] == "PN7788")
    ck("cluster labels senders", len(cl["clusters"][0]["senders"]) == 2)

    # --- \u6848\u4ef6\u77e9\u9663\u5316\u60c5\u5831\uff1a\u56de\u9023\u9023\u7d50 + \u6642\u9593\u7dda + \u672a\u4f86\u884c\u52d5\u77e9\u9663 + \u95dc\u9375\u9ede ---
    d4 = tempfile.mkdtemp()
    open(os.path.join(d4, "c1.eml"), "w", encoding="utf-8").write(
        "From: qa.li@corp.com\nTo: rd.wang@corp.com\nSubject: PN-5501 \u505c\u7dda\nMessage-ID: <abc123@corp.com>\nDate: Mon, 06 Jul 2026 09:00:00 +0800\n\n\u8acb\u63d0\u4f9b\u91cd\u5de5\u65b9\u6848 \u98a8\u96aa\u9ad8 \u622a\u6b62 07/10")
    ci = eng.case_intelligence(eng.read_and_classify(d4, do_fix=True))
    c = ci["cases"][0]
    ck("case_intel builds", len(ci["cases"]) == 1 and c["message_count"] == 1)
    ck("original link outlook+gmail",
       c["original_link"]["outlook"] == "outlook://message-id/abc123@corp.com"
       and "rfc822msgid:abc123@corp.com" in c["original_link"]["gmail"])
    ck("timeline present", len(c["timeline"]) == 1 and c["timeline"][0]["activity"] == "Request")
    ck("future action needs reply", c["future_action"]["needs_reply"]
       and c["future_action"]["owed_by"] == ["rd.wang@corp.com"])
    ck("future action scores", 0 <= c["future_action"]["urgency_score"] <= 100
       and c["future_action"]["priority"] in ("CRITICAL", "HIGH", "MED", "LOW"))
    ck("request matrix", len(c["request_matrix"]) == 1)
    ck("key points extracted", "RISK" in c["key_points"] and "REQUEST" in c["key_points"])

    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(description="VIA MailForge — \u90f5\u7bb1/\u6587\u4ef6\u8b80\u53d6\u5206\u985e\u7d71\u5408")
    ap.add_argument("--scan", help="\u90f5\u7bb1\u532f\u51fa/\u6587\u4ef6\u8cc7\u6599\u593e")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        a, b = selftest(); print("mailforge: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)
    if args.scan:
        eng = MailForgeEngine()
        recs = eng.read_and_classify(args.scan, do_fix=True)
        s = eng.summary(recs)
        print(json.dumps(s, ensure_ascii=False, indent=2))
        for r in recs:
            if r.get("status") != "OK":
                continue
            ei = r.get("email_intel")
            tag = ("[%s|%s]" % (ei["activity"], ei["case_id"])) if ei else "[DOC]"
            print("  %-30s %-10s %-10s %s" % (
                r["file_name"][:30], r["health"],
                (r.get("aspects") or {}).get("content_domain"), tag))


if __name__ == "__main__":
    main()
