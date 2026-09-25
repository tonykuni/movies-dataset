#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Rebuild  ——  via_rebuild.py   (\u7e3d \u00b7 \u5de5\u4f5c\u72c0\u614b/\u6d41\u7a0b/\u98a8\u96aa/\u5229\u5bb3\u95dc\u4fc2\u4eba\u91cd\u5efa)
================================================================================
\u4e00\u9375\u7d71\u7c4c\uff08\u4e0d\u52d5\u5206\u6beb\u3001\u5c0a\u91cd\u65e2\u6709\u7de8\u865f/\u683c\u5f0f\u3001\u5168\u672c\u6a5f\u3001readonly\uff09\uff1a
  \u2460 \u81ea\u52d5\u7de8\u865f\uff08\u5c0a\u91cd control sheet \u65e2\u6709\u7de8\u865f\uff0c\u6c92\u624d\u65b0\u7d66\uff09
  \u2461 \u5167\u5bb9\u591a\u91cd\u5206\u985e\u6b78\u7d0d\uff08\u9818\u57df/\u654f\u611f/PII/\u6d3b\u52d5\uff09
  \u2462 \u6b78\u5c6c\u54ea\u4e9b\u5c08\u6848\uff08cluster\u2192project\uff09
  \u2463 \u76ee\u524d\u5728\u54ea\u4e9b\u6d41\u7a0b\uff08\u6d41\u7a0b\u968e\u6bb5\uff09
  \u2464 \u7d05\u9ec3\u7da0\u71c8\uff08\u5370\u5ea6\u4e8b\u52d9\u6700\u9ad8\u7d05\uff09
  \u2465 \u5229\u5bb3\u95dc\u4fc2\u4eba\u662f\u8ab0
  \u2466 \u5982\u4f55\u91cd\u5efa\u5de5\u4f5c / \u91cd\u5efa\u6d41\u7a0b / \u98a8\u96aa\u63a7\u7ba1 / \u5229\u5bb3\u95dc\u4fc2\u4eba\u63a7\u7ba1
control sheet \u53ef\u7576 input\u3002
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
import os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import via_forge as F
import via_mailhub as MH
import via_signal as SG

UTC = timezone.utc


class RebuildEngine:
    def __init__(self, cfg=None):
        self.cfg = cfg or F.load_config()
        self.hub = MH.MailHubEngine(self.cfg)
        self.signal = SG.SignalEngine(self.cfg)

    # ---------- control sheet \u7576 input\uff08\u5c0a\u91cd\u65e2\u6709\u7de8\u865f/\u5206\u985e\uff09 ----------
    def read_control_sheet(self, path):
        """\u8b80\u65e2\u6709 control sheet xlsx/csv \u2192 {\u4e3b\u65e8\u7247\u6bb5: {id, classification}}\u3002\u53ea\u8b80\u4e0d\u6539\u3002"""
        existing = {}
        if not path or not os.path.exists(path):
            return existing
        rows = []
        try:
            if path.lower().endswith((".xlsx", ".xlsm")):
                import openpyxl
                wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                ws = wb.active
                headers = None
                for r in ws.iter_rows(values_only=True):
                    if headers is None:
                        headers = [str(c or "").strip() for c in r]; continue
                    rows.append(dict(zip(headers, r)))
            elif path.lower().endswith((".csv", ".tsv")):
                import csv
                delim = "\t" if path.lower().endswith(".tsv") else ","
                with open(path, encoding="utf-8-sig") as fh:
                    rows = list(csv.DictReader(fh, delimiter=delim))
        except Exception:
            return existing
        # \u5c0d\u61c9\u6b04\u4f4d\uff08\u5bec\u9b06\uff1a\u4e3b\u65e8/subject\u3001\u7de8\u865f/id\u3001\u5206\u985e/class\uff09
        def pick(row, *names):
            for n in names:
                for k in row:
                    if k and n in str(k).lower():
                        return row[k]
            return None
        for row in rows:
            subj = pick(row, "\u4e3b\u65e8", "subject", "\u6a19\u984c", "title")
            rid = pick(row, "\u7de8\u865f", "id", "no", "\u5e8f")
            cls = pick(row, "\u5206\u985e", "class", "\u9818\u57df", "domain", "\u5c08\u6848", "project")
            if subj:
                key = str(subj).lower().strip()[:40]
                existing[key] = {"id": rid, "classification": cls, "raw": row}
        return existing

    def _match_existing(self, existing, case):
        """\u5728\u65e2\u6709\u8868\u4e2d\u627e\u5c0d\u61c9\uff08\u4e3b\u65e8\u5305\u542b\uff09\u2192 \u56de\u65e2\u6709\u7de8\u865f\uff08\u5c0a\u91cd\uff0c\u4e0d\u91cd\u7de8\uff09\u3002"""
        if not existing:
            return None
        subj = (case.get("subject") or case.get("cluster_label") or "").lower()
        for key, val in existing.items():
            if key and (key in subj or subj[:20] in key):
                return val
        return None

    # ---------- \u4e00\u9375\u91cd\u5efa ----------
    def rebuild(self, records, control_sheet=None, control_data=None):
        existing = control_data if control_data is not None else self.read_control_sheet(control_sheet)
        ci = self.hub.case_intelligence(records)              # \u7b97\u4e00\u6b21\uff0c\u50b3\u7d66\u4e0b\u5c64\uff08\u907f\u514d\u91cd\u7b97\uff09
        board = self.signal.signal_board(records, ci=ci)
        stake = self.hub.stakeholders(records)
        ops = self.hub.operations_board(records, ci=ci)

        # \u9010\u4fe1/\u9010\u6848\uff1a\u7de8\u865f + \u591a\u91cd\u5206\u985e + \u5c08\u6848 + \u6d41\u7a0b\u968e\u6bb5 + \u71c8 + \u95dc\u4fc2\u4eba
        sig_by_case = {it["case_id"]: it for it in board["items"]}
        rows = []
        for c in ci["cases"]:
            sig = sig_by_case.get(c["case_id"], {})
            ex = self._match_existing(existing, c)
            # \u7de8\u865f\uff1a\u5c0a\u91cd\u65e2\u6709\uff1b\u6c92\u624d\u7528\u7cfb\u7d71 VIA-SIG
            num = (ex or {}).get("id") or sig.get("signal_id")
            num_source = "\u65e2\u6709(control sheet)" if (ex and ex.get("id")) else "\u7cfb\u7d71\u65b0\u7de8"
            # \u6d41\u7a0b\u968e\u6bb5\uff08\u7531\u6700\u5f8c\u6d3b\u52d5\u63a8\uff09
            last = c.get("last_activity")
            stage = {"Request": "\u5df2\u63d0\u51fa\u9700\u6c42", "Commitment": "\u5df2\u627f\u8afe\u5f85\u4ea4\u4ed8",
                     "Delivery": "\u5df2\u4ea4\u4ed8", "Escalation": "\u5df2\u5347\u7d1a", "Reminder": "\u50ac\u8fa6\u4e2d",
                     "Response": "\u5df2\u56de\u8986"}.get(last, last or "\u2014")
            rows.append({
                "number": num, "number_source": num_source,
                "signal_id": sig.get("signal_id"),
                "title": c.get("subject") or c.get("cluster_label"),
                "project": c.get("cluster_label"),
                "classification": {
                    "domain": sig.get("classification", {}).get("domain"),
                    "existing": (ex or {}).get("classification"),
                    "status": "TENTATIVE", "note": "\u5f85\u6838\u51c6\u5f8c\u6b63\u5f0f",
                },
                "process_stage": stage,
                "light": sig.get("light"), "light_label": sig.get("light_label"),
                "india": sig.get("india", False),
                "owner": sig.get("owner", "\u2014"),
                "message_count": c.get("message_count", 0),
                "respected": bool(ex and ex.get("id")),
            })

        # \u98a8\u96aa\u63a7\u7ba1
        risk = []
        for it in board["india"]:
            risk.append({"level": "HIGH", "type": "\u5370\u5ea6\u4e8b\u52d9", "item": it["title"], "action": "\u6700\u9ad8\u7d05\u71c8\u3001\u7acb\u5373\u8655\u7406"})
        for it in board["items"]:
            if it["light"] == "RED" and not it["india"]:
                risk.append({"level": "MED", "type": "\u672a\u8655\u7406\u505c\u6ef1", "item": it["title"],
                             "action": "\u9700\u56de\u8986\uff0c\u505c\u6ef1 %d \u5929" % it["age_days"]})

        # \u5229\u5bb3\u95dc\u4fc2\u4eba\u63a7\u7ba1\uff08\u5370\u5ea6\u76f8\u95dc\u6a19\u7d05\uff09
        india_addrs = set()
        for it in board["india"]:
            for r in records:
                ei = r.get("email_intel") if isinstance(r, dict) else None
                if ei and ei.get("cluster_label") == it["cluster"]:
                    for p in ei.get("participants", []):
                        india_addrs.add(p)
        stake_ctrl = []
        for s in stake:
            flag = any(s["stakeholder"] in a or a in s["stakeholder"] for a in india_addrs) \
                   or s["stakeholder"].lower().endswith(".in")
            stake_ctrl.append({"stakeholder": s["stakeholder"], "message_count": s["message_count"],
                               "red_flag": flag, "level": "\u7d05\u71c8\u76e3\u63a7" if flag else "\u4e00\u822c"})
        stake_ctrl.sort(key=lambda x: (not x["red_flag"], -x["message_count"]))

        # \u91cd\u5efa\u65b9\u6848
        rebuild_plan = {
            "immediate": [{"title": it["title"], "light": it["light"], "reason": it.get("reason")}
                          for it in board["immediate"]],
            "process_reengineering": [
                "\u4f9d\u6d41\u7a0b\u968e\u6bb5\u7f3a\u53e3\u91cd\u5efa\uff1a\u5df2\u627f\u8afe\u672a\u4ea4\u4ed8 \u2192 \u8ffd\u8e64\u5230\u671f",
                "\u5df2\u5347\u7d1a\u6848\u4ef6 \u2192 \u5efa\u7acb\u56de\u5831\u9ede\u8207\u8ca0\u8cac\u4eba",
                "\u5370\u5ea6\u4e8b\u52d9 \u2192 \u55ae\u7368\u7d05\u71c8\u901a\u9053\u3001\u6bcf\u65e5\u8907\u6838",
            ],
            "work_rebuild": {"lanes": ops["stats"]["by_lane"], "today": ops["stats"]["today_count"],
                             "overdue": ops["stats"]["overdue_count"]},
        }

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "source": "outlook/scan", "control_sheet_used": bool(existing),
            "respected_count": sum(1 for r in rows if r["respected"]),
            "rows": rows,
            "signal_stats": board["stats"],
            "projects": sorted(set(r["project"] for r in rows if r["project"])),
            "stakeholder_control": stake_ctrl,
            "risk_control": risk,
            "rebuild_plan": rebuild_plan,
            "policy": "\u4e0d\u52d5\u5206\u6beb\u00b7\u5c0a\u91cd\u65e2\u6709\u7de8\u865f\u8207\u683c\u5f0f\u00b7\u5168\u672c\u6a5f readonly\u00b7\u5206\u985e\u6838\u51c6\u5f8c\u6b63\u5f0f",
        }


def selftest():
    import tempfile
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] rebuild: %s" % n)
        else: f += 1; print("  [FAIL] rebuild: %s" % n)
    import via_mailforge as M
    cfg = F.load_config(); side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)
    d = tempfile.mkdtemp()
    mails = [
        ("rajesh@vendor.in", "Mumbai PO-500 India \u4ea4\u671f", "<a@c>", "Mon, 06 Jul 2026 09:00:00 +0800", "India \u8acb\u78ba\u8a8d"),
        ("qa.li@corp.com", "PN-9942 \u91cd\u5de5", "<c@c>", "Sun, 28 Jun 2026 09:00:00 +0800", "\u8acb\u63d0\u4f9b\u65b9\u6848"),
    ]
    for i, (fr, su, mid, dt, bd) in enumerate(mails):
        open(os.path.join(d, "m%d.eml" % i), "w", encoding="utf-8").write(
            "From: %s\nTo: team@corp.com\nSubject: %s\nMessage-ID: %s\nDate: %s\n\n%s" % (fr, su, mid, dt, bd))
    recs = M.MailForgeEngine(cfg).read_and_classify(d, do_fix=True)

    eng = RebuildEngine(cfg)
    # \u7121 control sheet
    rep = eng.rebuild(recs)
    ck("\u9010\u6848\u91cd\u5efa\u5217", len(rep["rows"]) == 2)
    ck("\u7de8\u865f(\u7121\u65e2\u6709\u2192\u7cfb\u7d71\u65b0\u7de8)", all(r["number_source"] == "\u7cfb\u7d71\u65b0\u7de8" for r in rep["rows"]))
    ck("\u591a\u91cd\u5206\u985e", all("domain" in r["classification"] for r in rep["rows"]))
    ck("\u5c08\u6848\u6b78\u5c6c", "PN9942" in rep["projects"])
    ck("\u6d41\u7a0b\u968e\u6bb5", all(r["process_stage"] for r in rep["rows"]))
    ck("\u7d05\u9ec3\u7da0\u71c8", "red" in rep["signal_stats"])
    ck("\u98a8\u96aa\u63a7\u7ba1\u542b\u5370\u5ea6", any(x["type"] == "\u5370\u5ea6\u4e8b\u52d9" for x in rep["risk_control"]))
    ck("\u5229\u5bb3\u95dc\u4fc2\u4eba\u63a7\u7ba1\u7d05\u71c8", any(s["red_flag"] for s in rep["stakeholder_control"]))
    ck("\u91cd\u5efa\u65b9\u6848", "process_reengineering" in rep["rebuild_plan"] and "work_rebuild" in rep["rebuild_plan"])

    # \u6709 control sheet \u7576 input\uff08\u5c0a\u91cd\u65e2\u6709\u7de8\u865f\uff09
    ctrl = {"pn-9942 \u91cd\u5de5": {"id": "EXIST-001", "classification": "\u88fd\u7a0b\u7570\u5e38", "raw": {}}}
    rep2 = eng.rebuild(recs, control_data=ctrl)
    ck("control sheet \u7576 input", rep2["control_sheet_used"])
    ck("\u5c0a\u91cd\u65e2\u6709\u7de8\u865f(\u4e0d\u91cd\u7de8)", any(r["number"] == "EXIST-001" and r["respected"] for r in rep2["rows"]))
    return p, f


def main():
    import argparse, json
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scan"); ap.add_argument("--control")
    args = ap.parse_args()
    if args.selftest:
        a, b = selftest(); print("rebuild: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)
    if args.scan:
        import via_mailforge as M
        recs = M.MailForgeEngine().read_and_classify(args.scan, do_fix=True)
        rep = RebuildEngine().rebuild(recs, control_sheet=args.control)
        print(json.dumps({k: v for k, v in rep.items() if k != "rows"}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
