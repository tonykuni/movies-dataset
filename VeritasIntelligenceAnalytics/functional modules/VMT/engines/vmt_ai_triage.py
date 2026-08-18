# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · AI Triage Engine  v1.0   --  郵件判讀引擎 (意圖 / 緊急度 / 期限 / 歸案)
----------------------------------------------------------------------------
 定位: 「高智慧」的核心第一關。把一封信讀成結構化判斷:
        意圖 REQUEST/REPLY/ESCALATION/NOTICE/FYI、緊急度 1-5、是否需要行動、
        期限 (相對時間已換算為絕對日期)、歸屬案號、建議負責人。

 雙軌判讀 (刻意設計):
   規則層 (vmt_lang)  : 一定會跑, 每個判斷都附觸發 cue -> 可解釋、可稽核、離線可用
   LLM 層  (選配)     : 只在規則層信心不足時補位, 且永不覆寫高信心的規則結論;
                        規則與 LLM 不一致時兩者都記錄, 並降低信心 -> 進 Q01 待人工
 為何這樣做: 郵件會直接觸發催辦信寄給真人。判斷錯誤的成本很高,
             因此系統寧可把不確定的信「留給人」, 也不猜。

 產出: data/triage.jsonl (add-only, 冪等: 同一 mail_uid + 同引擎版本不重判)
 治理: 只讀 mails.jsonl; 低信心 -> Q01 隔離但不阻斷主線; 預設 dry-run。
============================================================================
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import sys
import json
import argparse
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vmt_core import (  # noqa: E402
    URG_HEX, EngineResult, EventLog, Ledger, LocalLLM, Quarantine, Workspace,
    add_common_args, banner, clip, esc, fingerprint, kpi_cards, mode_label,
    pill, render_report, table, try_open,
)
from vmt_lang import classify_mail, resolve_due  # noqa: E402
from vmt_outlook_intake import load_mails  # noqa: E402

ENGINE = "vmt_ai_triage"
VERSION = "v1.0"

LOW_CONFIDENCE = 0.5          # 低於此值送 Q01
CHECKBOX_RE = r"\[\s*[xX✓v]\s*\]\s*([1-4])"

_LLM_PROMPT = """你是企業郵件分流助理。只輸出 JSON，不要任何說明文字。
判斷這封信並輸出欄位：
  intent: REQUEST | REPLY | ESCALATION | NOTICE | FYI
  urgency: 1-5 的整數（5 最急）
  needs_action: true/false（我方是否需要採取行動）
  suggested_owner: 建議負責人姓名，判斷不出來就填 ""
  summary: 20 字以內的中文摘要

主旨：{subject}
內文：{body}
"""


# ---------------------------------------------------------------- 判讀 ------


def _checkbox_option(body: str) -> int | None:
    import re
    m = re.search(CHECKBOX_RE, body or "")
    return int(m.group(1)) if m else None


def triage_one(mail: dict, llm: LocalLLM | None = None,
               base_date: dt.date | None = None) -> dict:
    """
    單封信判讀。回傳結構含 `cues` 與 `llm` 兩段, 讓報告能呈現判斷依據。
    """
    subject, body = mail.get("subject", ""), mail.get("body", "")
    opt = _checkbox_option(body)
    rule = classify_mail(subject, body, has_checkbox_reply=opt is not None)

    due = resolve_due("%s\n%s" % (subject, body), base_date)
    due_date = due[0].isoformat() if due else None
    due_cue = due[1] if due else ""

    out = {
        "triage_uid": fingerprint(mail.get("mail_uid"), VERSION),
        "mail_uid": mail.get("mail_uid"),
        "engine_version": VERSION,
        "subject": subject,
        "sender": mail.get("sender", ""),
        "case": mail.get("case"),
        "thread_key": mail.get("thread_key"),
        "intent": rule["intent"],
        "urgency": rule["urgency"],
        "needs_action": rule["needs_action"],
        "confidence": rule["confidence"],
        "cues": rule["cues"],
        "due_date": due_date,
        "due_cue": due_cue,
        "reply_option": opt,
        "suggested_owner": mail.get("sender", "") if rule["intent"] != "REPLY" else "",
        "llm": None,
        "disagreement": [],
    }

    if llm is not None and llm.available():
        got = llm.ask_json(_LLM_PROMPT.format(subject=clip(subject, 200),
                                              body=clip(body, 1500)))
        if got:
            out["llm"] = got
            # LLM 只補位, 不覆寫高信心規則結論
            if out["confidence"] < 0.7 and got.get("intent") in (
                    "REQUEST", "REPLY", "ESCALATION", "NOTICE", "FYI"):
                out["intent"] = got["intent"]
                out["needs_action"] = bool(got.get("needs_action", out["needs_action"]))
                out["confidence"] = round(min(0.75, out["confidence"] + 0.2), 2)
                out["cues"].append("llm:intent")
            elif got.get("intent") and got["intent"] != out["intent"]:
                out["disagreement"].append("intent rule=%s llm=%s" % (out["intent"], got["intent"]))
                out["confidence"] = round(max(0.2, out["confidence"] - 0.3), 2)
            if not out["suggested_owner"] and got.get("suggested_owner"):
                out["suggested_owner"] = str(got["suggested_owner"])[:40]
            out["summary"] = clip(got.get("summary", ""), 60)
    return out


# ---------------------------------------------------------------- 主流程 ----


def run(ws: Workspace, commit: bool = False, use_llm: bool = False,
        no_open: bool = True, base_date: dt.date | None = None) -> EngineResult:
    ws.ensure()
    ledger = Ledger(ws.triage_ledger, commit)
    events = EventLog(ws, commit)
    quar = Quarantine(ws, commit)
    llm = LocalLLM() if use_llm else None
    if llm is not None:
        print("[LLM] %s" % ("已連線 %s" % llm.model if llm.available()
                            else "無法連線 -> 全程使用規則判讀 (功能不受影響)"))

    done = {r.get("triage_uid") for r in ledger.read()}
    rows, held = [], 0
    for mail in load_mails(ws):
        t = triage_one(mail, llm, base_date)
        if t["triage_uid"] in done:
            continue
        done.add(t["triage_uid"])
        ledger.append(t)
        events.emit("MAIL_TRIAGED", t["mail_uid"],
                    "%s U%d %s" % (t["intent"], t["urgency"], clip(t["subject"], 40)),
                    intent=t["intent"], urgency=t["urgency"], due=t["due_date"])
        if t["confidence"] < LOW_CONFIDENCE or t["disagreement"]:
            if quar.hold("MAIL:%s" % t["mail_uid"],
                         "LOW_CONFIDENCE" if not t["disagreement"] else "AMBIGUOUS",
                         t["confidence"], {"subject": t["subject"], "cues": t["cues"],
                                           "disagreement": t["disagreement"]},
                         ref=t["mail_uid"]) is not None:
                held += 1
        rows.append(t)

    act = sum(1 for r in rows if r["needs_action"])
    print("[判讀] 新判 %d 封 / 需行動 %d / 低信心隔離 %d" % (len(rows), act, held))
    report = _report(ws, rows, held, commit)
    try_open(report, no_open)
    return EngineResult(engine=ENGINE, counts={"triaged": len(rows), "action": act,
                                               "quarantined": held},
                        records=rows, report=str(report))


def load_triage(ws: Workspace) -> list[dict]:
    """給下游用: 每封信取最新一次判讀結果。"""
    latest: dict[str, dict] = {}
    for r in Ledger(ws.triage_ledger, False).read():
        latest[r.get("mail_uid")] = r
    return list(latest.values())


def _report(ws: Workspace, rows: list[dict], held: int, commit: bool) -> Path:
    body = table(
        ["緊急", "意圖", "寄件者", "主旨", "期限", "信心", "判斷依據"],
        [[pill("U%d" % r["urgency"], URG_HEX.get(r["urgency"], "#999")),
          esc(r["intent"]), esc(r["sender"]), esc(clip(r["subject"], 46)),
          esc(r["due_date"] or "—"), esc(r["confidence"]),
          "<span class='mono'>%s</span>" % esc(", ".join(r["cues"])[:60] or "—")]
         for r in sorted(rows, key=lambda x: -x["urgency"])],
        "本次無新信需判讀")
    kpi = kpi_cards([
        ("需要行動", sum(1 for r in rows if r["needs_action"]), "#b5443a"),
        ("有明確期限", sum(1 for r in rows if r["due_date"]), "#d08343"),
        ("僅供參考", sum(1 for r in rows if r["intent"] in ("FYI", "NOTICE")), "#8a857c"),
        ("低信心 → Q01", held, "#c9a13a")])
    return render_report(
        ws.reports / "VMT_Triage.html", "判", "VMT AI 判讀引擎 — 郵件分流",
        "規則優先 · LLM 補位 · 低信心進 Q01 · %s" % mode_label(commit),
        "治理：每一筆判斷都附觸發 cue（可稽核）；LLM 僅在規則層信心不足時補位，"
        "永不覆寫高信心結論；規則與 LLM 不一致者降低信心並送 Q01 交人工，主線不阻斷。",
        [("KPI", kpi), ("判讀結果", body)],
        "%s %s | 帳本: data/triage.jsonl" % (ENGINE, VERSION), commit)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT AI Triage Engine")
    add_common_args(ap)
    ap.add_argument("--llm", action="store_true", help="啟用本地 LLM 補位判讀 (選配)")
    a = ap.parse_args()
    banner("VMT · AI Triage Engine %s" % VERSION, mode_label(a.commit))
    r = run(Workspace(a.root), a.commit, a.llm, a.no_open)
    print("[輸出] 報告:", r.report)
    print("完成.")


if __name__ == "__main__":
    main()
