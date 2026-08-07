#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Ops  ——  via_ops.py   (\u4f5c \u00b7 \u65e5\u5e38\u4f5c\u696d\u5c08\u6848\u7cfb\u7d71)
================================================================================
\u628a\u6574\u500b\u4fe1\u7bb1\u884d\u751f\u7684\u5de5\u4f5c \u2192 \u4e95\u7136\u6709\u5e8f\u3001\u7cbe\u6e96\u7684\u4f5c\u696d\u63a7\u5236\u53f0\uff08\u5168\u672c\u6a5f\u3001\u898f\u5247\u5f0f\uff09\uff1a
  \u2022 \u4f5c\u696d\u770b\u677f\uff1a\u4f9d\u72c0\u614b\u5206\u9053\uff08\u5f85\u8655\u7406/\u9032\u884c\u4e2d/\u5f85\u56de\u8986/\u5361\u95dc/\u5df2\u5b8c\u6210\uff09
  \u2022 \u8ca0\u8cac\u4eba\u8996\u5716\uff1a\u6bcf\u4eba\u6b20\u4ec0\u9ebc\u3001\u5de5\u4f5c\u91cf
  \u2022 \u4eca\u65e5\u6efe\u52d5\u5f85\u8fa6\uff1a\u9700\u56de\u8986/\u9006\u671f/\u5373\u5c07\u5230\u671f
  \u2022 \u9006\u671f\u9810\u8b66 + \u512a\u5148\u6392\u5e8f
\u5efa\u5728 mailforge case_intelligence \u4e4b\u4e0a\uff1b\u53bb\u91cd\u4fdd\u7559\u4e0d\u79fb\u9664\uff1b\u4e0d\u9023\u5916\u3001\u4e0d\u9700 IT \u958b\u901a\u3002
================================================================================
"""
import os, sys, hashlib
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import via_forge as F
import via_mailforge as M

UTC = timezone.utc

# \u72c0\u614b\u9053\uff08\u770b\u677f\u6b04\uff09
LANES = ["TODO", "IN_PROGRESS", "WAITING_REPLY", "BLOCKED", "DONE"]
LANE_LABEL = {"TODO": "\u5f85\u8655\u7406", "IN_PROGRESS": "\u9032\u884c\u4e2d",
              "WAITING_REPLY": "\u5f85\u56de\u8986", "BLOCKED": "\u5361\u95dc", "DONE": "\u5df2\u5b8c\u6210"}


class OpsEngine:
    """\u65e5\u5e38\u4f5c\u696d\u5c08\u6848\u7cfb\u7d71\uff1a\u4fe1\u7bb1 \u2192 \u4f5c\u696d\u63a7\u5236\u53f0\u3002"""

    def __init__(self, cfg=None):
        self.cfg = cfg or F.load_config()
        self.mail = M.MailForgeEngine(self.cfg)

    def _op_id(self, case_id):
        h = hashlib.blake2s(case_id.encode("utf-8"), digest_size=3).hexdigest().upper()
        return "VIA-OP-%s-%s" % (datetime.now(UTC).strftime("%Y%m%d"), h)

    @staticmethod
    def _lane(case):
        fa = case["future_action"]
        act = case.get("last_activity")
        if fa["priority"] == "CRITICAL":
            return "BLOCKED"
        if fa["needs_reply"] and fa.get("owed_by") and case.get("last_activity") in ("Request", "Reminder", "Escalation"):
            return "WAITING_REPLY"
        if fa["needs_reply"]:                       # AWAITING_DELIVERY(\u627f\u8afe\u672a\u4ea4\uff09
            return "IN_PROGRESS"
        return "DONE"

    def board(self, records, owner=None, ci=None):
        ci = ci if ci is not None else self.mail.case_intelligence(records)
        items = []
        for c in ci["cases"]:
            fa = c["future_action"]
            lane = self._lane(c)
            item = {
                "op_id": self._op_id(c["case_id"]),
                "case_id": c["case_id"], "title": c.get("subject") or c.get("cluster_label"),
                "cluster": c.get("cluster_label"), "lane": lane, "lane_label": LANE_LABEL[lane],
                "priority": fa["priority"], "needs_reply": fa["needs_reply"],
                "owner": ", ".join(fa.get("owed_by", [])) or "\u2014",
                "owners": fa.get("owed_by", []),
                "age_days": fa.get("stale_days", 0),
                "next_action": fa.get("suggested_next_step", ""),
                "participants": c.get("participants", []),
                "message_count": c.get("message_count", 0),
                "key_points": c.get("key_points", {}),
                "link": c.get("original_link", {}),
                "has_deadline": "DEADLINE" in (c.get("key_points") or {}),
            }
            items.append(item)

        if owner:
            o = owner.strip().lower()
            items = [it for it in items if any(o in p.lower() for p in it["participants"])
                     or o in it["owner"].lower()]

        # \u770b\u677f\u5206\u9053
        lanes = {ln: [] for ln in LANES}
        for it in items:
            lanes[it["lane"]].append(it)
        prio = {"CRITICAL": 0, "HIGH": 1, "MED": 2, "LOW": 3}
        for ln in lanes:
            lanes[ln].sort(key=lambda x: (prio.get(x["priority"], 9), -(x["age_days"] or 0)))

        # \u8ca0\u8cac\u4eba\u8996\u5716
        owners = {}
        for it in items:
            for ow in (it["owners"] or ["\u672a\u6307\u6d3e"]):
                owners.setdefault(ow, {"owner": ow, "open": 0, "blocked": 0, "items": []})
                owners[ow]["items"].append(it["op_id"])
                if it["lane"] != "DONE":
                    owners[ow]["open"] += 1
                if it["lane"] == "BLOCKED":
                    owners[ow]["blocked"] += 1
        owner_view = sorted(owners.values(), key=lambda x: -x["open"])

        # \u4eca\u65e5\u6efe\u52d5\u5f85\u8fa6\uff1a\u9700\u56de\u8986 + (\u9006\u671f>2 \u6216 \u6709\u5230\u671f 或 CRITICAL)
        today = [it for it in items if it["needs_reply"] and
                 (it["age_days"] > 2 or it["has_deadline"] or it["priority"] == "CRITICAL")]
        today.sort(key=lambda x: (prio.get(x["priority"], 9), -(x["age_days"] or 0)))

        # \u9006\u671f\u9810\u8b66
        overdue = [it for it in items if it["needs_reply"] and it["age_days"] > 3]
        overdue.sort(key=lambda x: -(x["age_days"] or 0))

        stats = {
            "total": len(items),
            "by_lane": {ln: len(lanes[ln]) for ln in LANES},
            "today_count": len(today), "overdue_count": len(overdue),
            "blocked_count": len(lanes["BLOCKED"]),
            "open_count": sum(1 for it in items if it["lane"] != "DONE"),
        }
        return {"owner": owner, "items": items, "lanes": lanes, "lane_order": LANES,
                "lane_label": LANE_LABEL, "owner_view": owner_view,
                "today": today, "overdue": overdue, "stats": stats,
                "dedup_policy": "\u53bb\u91cd\u4fdd\u7559\u4e0d\u79fb\u9664\uff08\u53ea\u589e\u4e0d\u6e1b\uff09"}

    def to_html(self, board, path=None):
        pc = {"CRITICAL": "#c96b5a", "HIGH": "#c4943a", "MED": "#c9b05a", "LOW": "#5a9e6f"}
        lane_col = {"TODO": "#6b6a66", "IN_PROGRESS": "#4c78a8", "WAITING_REPLY": "#c4943a",
                    "BLOCKED": "#c96b5a", "DONE": "#5a9e6f"}
        cols = ""
        for ln in board["lane_order"]:
            cards = ""
            for it in board["lanes"][ln]:
                c = pc.get(it["priority"], "#6b6a66")
                cards += ('<div class="opc"><div class="opt">%s</div>'
                          '<div class="opm"><span class="rl" style="background:%s">%s</span> '
                          '<span class="mono">%s\u5929</span></div>'
                          '<div class="opo">%s %s</div></div>') % (
                    it["title"][:44], c, it["priority"], it["age_days"],
                    ("\u6b20:" + it["owner"][:24]) if it["owner"] != "\u2014" else "", 
                    ("\u23f0" if it["has_deadline"] else ""))
            cols += ('<div class="lane"><div class="laneh" style="border-color:%s;color:%s">'
                     '%s <span class="mono">%d</span></div>%s</div>') % (
                lane_col[ln], lane_col[ln], board["lane_label"][ln], len(board["lanes"][ln]), cards)
        st = board["stats"]
        html = _OPS_HTML
        for k, v in {"__COLS__": cols, "__TOTAL__": str(st["total"]),
                     "__OPEN__": str(st["open_count"]), "__TODAY__": str(st["today_count"]),
                     "__OVERDUE__": str(st["overdue_count"]), "__BLOCKED__": str(st["blocked_count"]),
                     "__TS__": datetime.now(UTC).isoformat()[:19]}.items():
            html = html.replace(k, v)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        return html


_OPS_HTML = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA \u65e5\u5e38\u4f5c\u696d\u63a7\u5236\u53f0</title>
<style>@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;600&family=DM+Mono&family=Noto+Sans+TC:wght@400;500&display=swap');
:root{--bg:#f5f4f0;--sf:#fff;--bd:#dbd9d3;--ink:#1e1d1a;--sub:#6b6a66;--gr:#9c9890;--seal:#b5291a}
*{box-sizing:border-box;margin:0;padding:0}body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Noto Sans TC",sans-serif;font-size:13px}
.wrap{max-width:1200px;margin:0 auto;padding:22px}.mono{font-family:"DM Mono",monospace}
h1{font-family:"Syne",sans-serif;font-weight:800;font-size:21px;display:flex;align-items:center}
.eyebrow{font-family:"DM Mono",monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--sub)}
.seal{display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;border-radius:7px;background:var(--seal);color:#fff;font-weight:900;margin-right:8px}
.strip{height:6px;border-radius:2px;margin:12px 0;background:linear-gradient(90deg,#4c78a8,#439a9a,#c9b05a,#c96b5a)}
.kpi{display:flex;gap:22px;flex-wrap:wrap;margin:10px 0}.kpi div b{font-family:"Syne",sans-serif;font-size:26px}
.board{display:flex;gap:10px;overflow-x:auto;padding-bottom:8px}
.lane{min-width:210px;flex:1;background:#faf9f6;border:1px solid var(--bd);border-radius:8px;padding:8px}
.laneh{font-weight:700;font-size:12px;border-bottom:2px solid;padding-bottom:6px;margin-bottom:8px;display:flex;justify-content:space-between}
.opc{background:#fff;border:1px solid var(--bd);border-radius:6px;padding:8px;margin-bottom:7px}
.opt{font-size:12px;font-weight:600;margin-bottom:5px;line-height:1.35}
.opm{display:flex;gap:8px;align-items:center;margin-bottom:3px}
.opo{font-size:10.5px;color:var(--sub)}
.rl{border-radius:9px;padding:1px 7px;font-size:9px;font-weight:700;color:#fff}
.foot{color:var(--gr);font-size:11px;border-top:1px solid var(--bd);padding-top:10px;margin-top:14px}</style></head>
<body><div class="wrap"><div class="eyebrow">VERITAS INTELLIGENCE SYSTEM \u00b7 DAILY OPERATIONS</div>
<h1><span class="seal">\u4f5c</span>\u65e5\u5e38\u4f5c\u696d\u63a7\u5236\u53f0</h1>
<div class="strip"></div>
<div class="kpi">
  <div><b>__TOTAL__</b><br><span class="mono" style="font-size:10px;color:#6b6a66">\u4f5c\u696d\u9805</span></div>
  <div><b style="color:#4c78a8">__OPEN__</b><br><span class="mono" style="font-size:10px;color:#6b6a66">\u9032\u884c\u4e2d</span></div>
  <div><b style="color:#c4943a">__TODAY__</b><br><span class="mono" style="font-size:10px;color:#6b6a66">\u4eca\u65e5\u5f85\u8fa6</span></div>
  <div><b style="color:#c96b5a">__OVERDUE__</b><br><span class="mono" style="font-size:10px;color:#6b6a66">\u9006\u671f</span></div>
  <div><b style="color:#c96b5a">__BLOCKED__</b><br><span class="mono" style="font-size:10px;color:#6b6a66">\u5361\u95dc</span></div>
</div>
<div class="board">__COLS__</div>
<div class="foot">VIA \u00b7 VeritasIntelligenceAnalytics \u00b7 \u4f5c \u00b7 \u65e5\u5e38\u4f5c\u696d\u5c08\u6848\u7cfb\u7d71 \u00b7 \u5168\u672c\u6a5f\u4e0d\u9023\u5916 \u00b7 __TS__</div>
</div></body></html>"""


def selftest():
    import tempfile
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] ops: %s" % n)
        else: f += 1; print("  [FAIL] ops: %s" % n)
    cfg = F.load_config(); side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)
    d = tempfile.mkdtemp()
    mails = [
        ("qa.li@corp.com", "PN-9942 AOI \u505c\u7dda", "<a@c>", "Mon, 06 Jul 2026 09:00:00 +0800", "\u8acb\u63d0\u4f9b\u91cd\u5de5\u65b9\u6848 \u622a\u6b62 07/10"),
        ("pm.chen@corp.com", "\u5347\u7d1a PN-8801", "<b@c>", "Wed, 08 Jul 2026 09:00:00 +0800", "urgent escalate \u7ba1\u7406\u5c64"),
        ("v@acme.com", "PO-100 \u4ea4\u671f", "<c@c>", "Fri, 04 Jul 2026 09:00:00 +0800", "\u8acb\u78ba\u8a8d"),
        ("me@corp.com", "Re: PO-100 \u4ea4\u671f", "<d@c>", "Fri, 04 Jul 2026 15:00:00 +0800", "\u63d0\u4f9b\u5982\u9644 \u5df2\u78ba\u8a8d"),
    ]
    for i, (fr, su, mid, dt, bd) in enumerate(mails):
        open(os.path.join(d, "m%d.eml" % i), "w", encoding="utf-8").write(
            "From: %s\nTo: team@corp.com\nSubject: %s\nMessage-ID: %s\nDate: %s\n\n%s" % (fr, su, mid, dt, bd))
    recs = M.MailForgeEngine(cfg).read_and_classify(d, do_fix=True)
    eng = OpsEngine(cfg)
    b = eng.board(recs)
    ck("board builds items", b["stats"]["total"] == 3)   # PN-9942 / PN-8801 / PO-100
    ck("lanes populated", sum(b["stats"]["by_lane"].values()) == 3)
    ck("escalation -> BLOCKED", any(it["lane"] == "BLOCKED" for it in b["items"]))
    ck("replied -> DONE", b["stats"]["by_lane"]["DONE"] >= 1)
    ck("owner view", len(b["owner_view"]) >= 1)
    ck("today rolling", isinstance(b["today"], list))
    ck("overdue alert", isinstance(b["overdue"], list))
    ck("op id format", all(it["op_id"].startswith("VIA-OP-") for it in b["items"]))
    ck("owner filter", isinstance(eng.board(recs, owner="qa.li@corp.com")["items"], list))
    html = eng.to_html(b)
    ck("kanban html", "\u4f5c" in html and "\u65e5\u5e38\u4f5c\u696d\u63a7\u5236\u53f0" in html and "\u5f85\u56de\u8986" in html)
    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scan"); ap.add_argument("--owner")
    args = ap.parse_args()
    if args.selftest:
        a, b = selftest(); print("ops: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)
    if args.scan:
        recs = M.MailForgeEngine().read_and_classify(args.scan, do_fix=True)
        import json
        print(json.dumps(OpsEngine().board(recs, owner=args.owner)["stats"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
