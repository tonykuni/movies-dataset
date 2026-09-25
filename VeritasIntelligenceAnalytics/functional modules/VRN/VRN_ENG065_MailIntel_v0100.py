#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG065_MailIntel — NLP×郵件追蹤×報告摘要整合管線(批143;via-mail)
====================================================================
操作員令:NLP support mailing tracking and report summarized。
三件合流(批141 收容件全走轉接,原件零觸碰):
  ① mail tracker v2(收容包)=UID/語意分類/專案/部門/SLA/生命線/工單
  ② NLP 知識堆疊(VRN_ENG064 轉接)=正規化+實體+三元組+關鍵詞
  ③ 摘要器=逐信情報卡+批次彙總報告(分類×風險×SLA×部門矩陣
     +TF-IDF 關鍵詞榜+高風險清單)→ JSON+Markdown 落
     VIA_Reports/mailintel_runs/(append-only)
輸入:--inbox <json>(信件陣列:sender/receiver/subject/body/timestamp)
     |--demo(內建六信合成集:中文金融×英文專案×風險×一般)
用法:via-mail --demo | --inbox F [--md] | --selftest
"""
from __future__ import annotations
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

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = VIA / "new modules engines" / "VIA_KnowledgeStack_Batch141"
TRACKER = INTAKE / "mail_tracker_v2_packaged"
OUT = VIA / "VIA_Reports" / "mailintel_runs"

DEMO_INBOX = [
    {"sender": "rd_lead@example.com", "receiver": "pm@example.com",
     "subject": "P2382 risk on validation schedule",
     "body": "We see potential risk and delay on validation phase.",
     "timestamp": "2026-08-25 16:50"},
    {"sender": "analyst@bank.example", "receiver": "risk@bank.example",
     "subject": "信用風險月報:NPL 走勢",
     "body": "受房地產市場波動影響,其 NPL Ratio 攀升至 1.85%。"
             "為防範風險,金管會要求將備抵呆帳覆蓋率提升至150%。",
     "timestamp": "2026-08-25 09:10"},
    {"sender": "pm@example.com", "receiver": "qa_team@example.com",
     "subject": "PROJ-77 action items after review",
     "body": "Please complete the action items before Friday.",
     "timestamp": "2026-08-24 14:00"},
    {"sender": "fin_ops@example.com", "receiver": "cfo@example.com",
     "subject": "Q3 營收預估更新",
     "body": "因為新產品出貨優於預期,Q3 營收預估上調至 120 億元。",
     "timestamp": "2026-08-24 11:30"},
    {"sender": "it_support@example.com", "receiver": "all@example.com",
     "subject": "Scheduled maintenance notice",
     "body": "System maintenance window this weekend, no action needed.",
     "timestamp": "2026-08-23 18:00"},
    {"sender": "rd_lead@example.com", "receiver": "pm@example.com",
     "subject": "P2382 update: risk mitigated",
     "body": "Validation risk resolved after schedule adjustment.",
     "timestamp": "2026-08-26 10:00"},
]


def _load_tracker():
    """收容包管線動態載入(byte-exact 原件零觸碰)"""
    if str(TRACKER) not in sys.path:
        sys.path.insert(0, str(TRACKER))
    import importlib
    mod = importlib.import_module("mail_tracker_v2")
    return mod.mail_tracker_v2


def _load_nlp():
    """VRN_ENG064 知識堆疊轉接(glob 最新)"""
    hits = sorted(HERE.glob("VRN_ENG064_KnowledgeStack_v*.py"))
    spec = importlib.util.spec_from_file_location("via_know_dyn", hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules["via_know_dyn"] = m
    spec.loader.exec_module(m)
    return m


def enrich(email: dict, tracker_fn, nlp_mod) -> dict:
    """單信合流:追蹤欄+NLP 情報(實體/三元組/正規文)"""
    tracked = tracker_fn(dict(email))
    text = f"{email.get('subject', '')}。{email.get('body', '')}"
    nl = nlp_mod.analyze(text)
    return {
        "uid": tracked.get("UID"),
        "subject": email.get("subject"),
        "from": email.get("sender"), "to": email.get("receiver"),
        "timestamp": email.get("timestamp"),
        "semantic": tracked.get("Semantic"),
        "project": (tracked.get("Project") or {}).get("project")
        if isinstance(tracked.get("Project"), dict) else tracked.get("Project"),
        "dept": (tracked.get("Dept") or {}).get("dept")
        if isinstance(tracked.get("Dept"), dict) else tracked.get("Dept"),
        "sla": tracked.get("SLA"), "task": tracked.get("Task"),
        "nlp": {
            "normalized": nl["normalized_text"][:200],
            "entities": [{"text": e.get("text"), "label": e.get("label")}
                         for e in nl["parsed"].get("entities", [])][:12],
            "triples": [{"s": t["subject"], "p": t["predicate"], "o": t["object"],
                         "type": t["attributes"].get("type")}
                        for t in nl["triples"]][:8],
        },
    }


def summarize(cards: list[dict], nlp_mod) -> dict:
    """批次彙總:分類×風險×SLA×部門矩陣+關鍵詞榜+高風險清單"""
    def _label(v):
        if isinstance(v, dict):
            v = next((x for x in v.values() if isinstance(x, str)), None) or "未標"
        return str(v) if v not in (None, "") else "未標"

    def tally(key_fn):
        out = {}
        for c in cards:
            k = _label(key_fn(c))
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items(), key=lambda x: -x[1]))

    sem = lambda c: (c.get("semantic") or {}).get("category")      # noqa: E731
    risk = lambda c: str((c.get("semantic") or {}).get("risk_level"))  # noqa: E731
    texts = [f"{c.get('subject', '')} {(c.get('nlp') or {}).get('normalized', '')}"
             for c in cards]
    stack = nlp_mod.load_stack()
    kw = stack["local_knowledge_engine"].LocalKnowledgePipeline.rank_keywords(
        texts, top_k=12)
    def _risk_num(c):
        v = (c.get("semantic") or {}).get("risk_level")
        try:
            return float(v)
        except (TypeError, ValueError):
            return {"high": 8, "critical": 9}.get(str(v).lower(), 0)

    high = [c for c in cards
            if _risk_num(c) >= 7
            or str((c.get("task") or {}).get("priority")) in ("P0", "P1")]
    triple_n = sum(len((c.get("nlp") or {}).get("triples", [])) for c in cards)
    return {
        "total": len(cards),
        "by_category": tally(sem),
        "by_risk": tally(risk),
        "by_dept": tally(lambda c: c.get("dept")),
        "by_sla": tally(lambda c: str(c.get("sla"))),
        "keywords": [{"term": t, "score": round(float(s), 4)} for t, s in kw],
        "high_priority": [{"uid": c["uid"], "subject": c["subject"],
                           "priority": (c.get("task") or {}).get("priority")
                           or f"risk{(c.get('semantic') or {}).get('risk_level')}"}
                          for c in high],
        "knowledge_triples": triple_n,
    }


def to_markdown(summary: dict, cards: list[dict]) -> str:
    ln = [f"# 郵件情報彙總報告", f"",
          f"產出:{datetime.now().strftime('%Y-%m-%d %H:%M')} · 信件 {summary['total']}"
          f" · 知識三元組 {summary['knowledge_triples']}", ""]
    ln.append("## 分佈矩陣")
    for name, key in (("分類", "by_category"), ("風險", "by_risk"),
                      ("部門", "by_dept")):
        row = " · ".join(f"{k}×{v}" for k, v in summary[key].items())
        ln.append(f"- **{name}**:{row}")
    ln.append("")
    ln.append("## 高優先清單")
    if summary["high_priority"]:
        for h in summary["high_priority"]:
            ln.append(f"- [{h['priority']}] {h['subject']}(uid {str(h['uid'])[:10]}…)")
    else:
        ln.append("-(無)")
    ln.append("")
    ln.append("## 關鍵詞榜(TF-IDF)")
    ln.append(" · ".join(k["term"] for k in summary["keywords"]))
    ln.append("")
    ln.append("## 逐信情報卡")
    for c in cards:
        sem = c.get("semantic") or {}
        ln.append(f"### {c['subject']}")
        ln.append(f"- {c['from']} → {c['to']} @ {c['timestamp']}")
        ln.append(f"- 分類 {sem.get('category')} · 風險 {sem.get('risk_level')}"
                  f" · 部門 {c.get('dept')} · SLA {c.get('sla')}"
                  f" · 工單 {(c.get('task') or {}).get('priority')}")
        for t in (c.get("nlp") or {}).get("triples", []):
            ln.append(f"  - ◇ {t['s']} —{t['p']}→ {t['o']}({t['type']})")
    return "\n".join(ln) + "\n"


def run(inbox: list[dict], write_md: bool = True) -> dict:
    tracker_fn = _load_tracker()
    nlp_mod = _load_nlp()
    cards = [enrich(e, tracker_fn, nlp_mod) for e in inbox]
    summary = summarize(cards, nlp_mod)
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (OUT / f"MAILINTEL_{stamp}.json").write_text(
        json.dumps({"summary": summary, "cards": cards}, ensure_ascii=False,
                   indent=1, default=str), encoding="utf-8")
    if write_md:
        (OUT / f"MAILINTEL_{stamp}.md").write_text(
            to_markdown(summary, cards), encoding="utf-8")
    print(f"[彙總] 信 {summary['total']} · 三元組 {summary['knowledge_triples']}"
          f" · 高優先 {len(summary['high_priority'])} · 存 MAILINTEL_{stamp}.*")
    return {"summary": summary, "cards": cards, "stamp": stamp}


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 收容雙件在位(tracker 包+堆疊轉接)",
        TRACKER.exists() and bool(sorted(HERE.glob("VRN_ENG064_KnowledgeStack_v*.py"))))
    tracker_fn = _load_tracker()
    nlp_mod = _load_nlp()
    chk("② 雙管線載入(原件零觸碰)", callable(tracker_fn) and nlp_mod is not None)

    c1 = enrich(DEMO_INBOX[0], tracker_fn, nlp_mod)
    chk("③ 英文信合流(P2382→Risk 分類+SLA+UID)",
        c1["uid"] and c1["project"] and "risk" in str(c1["semantic"]).lower(),
        f"(proj={c1['project']})")

    c2 = enrich(DEMO_INBOX[1], tracker_fn, nlp_mod)
    types = {t["type"] for t in c2["nlp"]["triples"]}
    chk("④ 中文金融信 NLP 增強(三元組≥3 型)",
        {"metric_change", "causation", "policy_action"} <= types,
        f"(型={sorted(types)})")

    r = run(DEMO_INBOX, write_md=True)
    s = r["summary"]
    chk("⑤ 彙總矩陣(分類/風險/部門/SLA 四表)",
        all(k in s for k in ("by_category", "by_risk", "by_dept", "by_sla"))
        and s["total"] == 6)
    chk("⑥ 高優先清單+關鍵詞榜", isinstance(s["high_priority"], list)
        and len(s["keywords"]) >= 5)
    md = (OUT / f"MAILINTEL_{r['stamp']}.md").read_text(encoding="utf-8")
    chk("⑦ Markdown 報告(矩陣+情報卡+三元組)",
        "分佈矩陣" in md and "逐信情報卡" in md and "◇" in md)
    chk("⑧ JSON 存證落盤", (OUT / f"MAILINTEL_{r['stamp']}.json").exists())
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 郵件情報管線(VRN_ENG065)· 八檢自測(零網路)===")
        return selftest()
    inbox = None
    if "--demo" in args:
        inbox = DEMO_INBOX
    elif "--inbox" in args:
        inbox = json.loads(Path(args[args.index("--inbox") + 1])
                           .read_text(encoding="utf-8-sig"))
    if inbox is None:
        print(__doc__.split("用法:")[1])
        return 0
    run(inbox, write_md=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
