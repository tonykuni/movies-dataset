# -*- coding: utf-8 -*-
r"""Veritas WorkOps 統一搜尋引擎 v0100 — GapFill 自建路 B(裁定序 A;全唯讀)

跨側車一次搜:郵件/WOP 專案/命名帳本/決策/回覆事件/里程碑/結案/教訓/待回。
用法:workops_unified_search.py 關鍵字 [關鍵字2 …](空白=AND)。零寫入。
via-workops search 關鍵字。
"""
import csv, io, json, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"


def jload(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return d


def rows(p):
    try:
        with io.open(p, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def hit(terms, *fields):
    blob = " ".join(str(x or "") for x in fields).lower()
    return all(t in blob for t in terms)


def main(argv):
    terms = [a.lower() for a in argv[1:] if a.strip()]
    if not terms:
        print("[用法] search 關鍵字 [關鍵字2 …](AND;跨九側車唯讀)")
        return 1
    R = []
    for r in rows(OUT / "mails.csv"):
        if hit(terms, r.get("Subject"), r.get("SenderEmail")):
            R.append(("郵件", r.get("ConversationID", ""), "%s · %s" % (r.get("Subject", "")[:60], r.get("SenderEmail", ""))))
    reg = jload(OUT / "wop_registry.json", {})
    for wid, pr in (reg.get("projects", {}) or {}).items():
        if hit(terms, wid, pr.get("label"), " ".join(pr.get("thr", []))):
            R.append(("專案", wid, "%s · %d 串 · %s" % (pr.get("label", ""), len(pr.get("thr", [])), pr.get("status", ""))))
    nm = jload(OUT / "workops_naming.json", {})
    for cid, e in (nm.get("entries", {}) or {}).items():
        if isinstance(e, dict) and hit(terms, cid, e.get("approved"), e.get("proposed")):
            R.append(("命名", cid, e.get("approved") or e.get("proposed") or ""))
    for r in rows(OUT / "decision_log.csv"):
        if hit(terms, *(r.get(k) for k in ("編號", "決議", "負責人", "來源"))):
            R.append(("決策", r.get("編號", ""), "%s · %s · %s" % (r.get("決議", "")[:50], r.get("負責人", ""), r.get("狀態", ""))))
    ev = OUT / "reply_events.jsonl"
    if ev.exists():
        for ln in ev.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(ln)
            except Exception:
                continue
            if hit(terms, e.get("thr"), e.get("subject"), e.get("sender"), e.get("status")):
                R.append(("回覆", e.get("thr", ""), "%s · %s" % (e.get("status", ""), e.get("subject", "")[:50])))
    for name, p, idk, fields in [
        ("里程碑", OUT / "milestones.json", "items", ("wop", "name", "owner", "status")),
        ("結案", OUT / "closures.json", "items", ("wop", "reason")),
        ("教訓", OUT / "lessons.json", "items", ("wop", "situation", "root_cause", "prevention", "reuse_rule")),
    ]:
        d = jload(p, {})
        for k, e in (d.get(idk, {}) or {}).items():
            if isinstance(e, dict) and hit(terms, k, *(e.get(f) for f in fields)):
                R.append((name, k, " · ".join(str(e.get(f, "")) for f in fields[:3])[:70]))
    for r in rows(OUT / "pending.csv"):
        if hit(terms, r.get("ThrID"), r.get("Subject")):
            R.append(("待回", r.get("ThrID", ""), "%s · 等 %s 天" % (r.get("Subject", "")[:50], r.get("WaitingDays", ""))))
    print("[搜尋] 「%s」— 命中 %d 筆(唯讀跨九側車)" % (" ".join(terms), len(R)))
    for src, key, desc in R[:40]:
        print("  %-4s %-12s %s" % (src, key, desc))
    if len(R) > 40:
        print("  …(僅列前 40;縮小關鍵字)")
    if not R:
        print("  (無命中 — 誠實回報;試較短關鍵字)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
