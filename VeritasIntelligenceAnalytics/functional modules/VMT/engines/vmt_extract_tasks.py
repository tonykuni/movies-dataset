# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Task Extraction Engine  v1.0   --  任務抽取 (郵件 / 會議 -> 工作台帳)
----------------------------------------------------------------------------
 定位: 把「散在信件與會議裡的承諾」變成台帳上的一筆任務, 並且每一筆都帶著
       它的出處 —— 哪封信、會議的哪一句。沒有出處的任務不准進台帳。

 兩條來源:
   郵件  : triage 判定 needs_action 者 -> 我方任務 (owner = 本人, requester = 寄件者)
   會議  : minutes 的待辦 -> 該負責人的任務 (owner = 會上認領的人, cite = 句號)

 缺欄位不丟棄: 沒有負責人或期限的待辦照樣建案, 欄位填 [?] 並在報告標成「待確認」。
   理由與會議記錄引擎一致 —— 資訊不完整是事實, 讓它消失才是問題。

 重複偵測: 同一件事可能同時出現在信裡和會議上。系統不自動合併 (合併會失去出處),
   而是在報告中並列標示「疑似重複」, 由人決定。
============================================================================
"""
from __future__ import annotations

import re
import sys
import json
import argparse
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vmt_core import (  # noqa: E402
    URG_HEX, EngineResult, Ledger, Workspace, add_common_args, banner, clip,
    esc, kpi_cards, mode_label, pill, render_report, table, try_open,
)
from vmt_lang import _ratio  # noqa: E402
from vmt_ai_triage import load_triage  # noqa: E402
from vmt_task_ssot import UNKNOWN, build_task, create_tasks, load_tasks  # noqa: E402

ENGINE = "vmt_extract_tasks"
VERSION = "v1.0"

DUP_THRESHOLD = 0.75


def _clean_title(subject: str) -> str:
    s = re.sub(r"[\U0001F300-\U0001FAFF]", "", str(subject or ""))
    s = re.sub(r"^\s*(?:re|fw|fwd|回覆|轉寄)\s*[:：]\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\[\s*CASE[-\s]?\d+\s*\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*[-–]\s*\d{4}/\d{2}/\d{2}.*$", "", s)
    return s.strip(" -–—") or "（無主旨）"


def _urgency_from_due(due: str | None, base: dt.date, default: int = 3) -> int:
    """期限越近越急。會議待辦通常沒有人明說緊急度, 用期限推導比一律給 3 合理。"""
    if not due or due == UNKNOWN:
        return default
    try:
        days = (dt.date.fromisoformat(due) - base).days
    except ValueError:
        return default
    if days < 0:
        return 5
    if days <= 2:
        return 4
    if days <= 7:
        return 3
    return 2


# ---------------------------------------------------------------- 抽取 ------


def from_mails(ws: Workspace, me: str) -> list[dict]:
    """
    郵件型任務以「會話」為單位, 不是以「每封信」為單位。
    「請提供產能數字」與三天後的「逾期提醒：產能數字尚未收到」是同一件事,
    逐封建案會讓台帳上出現兩筆同樣的任務, 然後被催兩次。
    同一會話取: 最早那封的標題 (原始請求)、最急的緊急度、最早的期限。
    """
    threads: dict[str, list[dict]] = {}
    for t in load_triage(ws):
        if not t.get("needs_action") or t.get("intent") == "REPLY":
            continue
        threads.setdefault(t.get("thread_key") or t.get("mail_uid", ""), []).append(t)

    out = []
    for key, group in threads.items():
        group.sort(key=lambda x: str(x.get("received") or ""))
        first = group[0]
        dues = sorted(d for d in (g.get("due_date") for g in group) if d)
        urgency = max(int(g.get("urgency", 3)) for g in group)
        cues = ", ".join(dict.fromkeys(c for g in group for c in g.get("cues", [])))
        out.append(build_task(
            title=_clean_title(first.get("subject")),
            owner=me,
            requester=first.get("sender", ""),
            due=dues[0] if dues else None,
            urgency=urgency,
            source_type="MAIL", ref=key, cite="",
            case=first.get("case"),
            detail="來自 %s 的請求；同一會話 %d 封信；判讀 cue: %s"
                   % (first.get("sender", ""), len(group), cues[:80]),
        ))
    return out


def from_minutes(ws: Workspace, include_questions: bool = False) -> list[dict]:
    out = []
    for m in Ledger(ws.minutes_ledger, False).read():
        ref = m.get("minute_uid", "")
        title = m.get("title", "會議")
        base = dt.date.fromisoformat(m["date"]) if m.get("date") else dt.date.today()
        for a in (m.get("records") or {}).get("actions", []):
            out.append(build_task(
                title=clip(a.get("task"), 60),
                owner=a.get("owner") or UNKNOWN,
                requester=m.get("chair", ""),
                due=None if a.get("due") == UNKNOWN else a.get("due"),
                urgency=_urgency_from_due(a.get("due"), base),
                source_type="MINUTES", ref=ref, cite=a.get("cite", ""),
                case=m.get("case"),
                detail="%s／議題「%s」；原文用語「%s」"
                       % (title, a.get("topic", ""), a.get("due_cue") or "未提期限"),
            ))
        if include_questions:
            for q in (m.get("records") or {}).get("questions", []):
                out.append(build_task(
                    title="待釐清：%s" % clip(q.get("text"), 50),
                    owner=q.get("raised_by") or UNKNOWN, requester=m.get("chair", ""),
                    due=None, urgency=3,
                    source_type="MINUTES", ref=ref, cite=q.get("cite", ""),
                    case=m.get("case"), detail="%s／未解問題" % title))
    return out


def find_duplicates(candidates: list[dict], existing: list[dict]) -> list[dict]:
    """疑似重複 (同一負責人 + 標題高度相似)。只標示不合併 —— 合併會弄丟其中一個出處。"""
    pool = [{"task_id": t.get("task_id", "(新)"), "owner": t.get("owner"),
             "title": t.get("title", ""), "source": t.get("source", {})}
            for t in existing]
    dups = []
    for c in candidates:
        for p in pool:
            if p["owner"] != c["owner"]:
                continue
            r = _ratio(str(c["title"]), str(p["title"]))
            if r >= DUP_THRESHOLD and p["source"] != c["source"]:
                dups.append({"new": c["title"], "owner": c["owner"],
                             "existing": p["title"], "existing_id": p["task_id"],
                             "similarity": round(r, 2)})
                break
        pool.append({"task_id": "(新)", "owner": c["owner"], "title": c["title"],
                     "source": c["source"]})
    return dups


# ---------------------------------------------------------------- 主流程 ----


def run(ws: Workspace, me: str = "我", commit: bool = False, no_open: bool = True,
        include_questions: bool = False) -> EngineResult:
    ws.ensure()
    cands = from_mails(ws, me) + from_minutes(ws, include_questions)
    before = load_tasks(ws)
    known = {t.get("fingerprint") for t in before}
    fresh = [c for c in cands if c["fingerprint"] not in known]
    dups = find_duplicates(fresh, before)
    created = create_tasks(ws, cands, commit)

    incomplete = [c for c in created if c["owner"] == UNKNOWN or c["due"] == UNKNOWN]
    print("[抽取] 候選 %d / 新建 %d / 冪等略過 %d / 缺欄位 %d / 疑似重複 %d"
          % (len(cands), len(created), len(cands) - len(created), len(incomplete), len(dups)))
    report = _report(ws, created, dups, incomplete, len(cands), commit)
    try_open(report, no_open)
    return EngineResult(engine=ENGINE,
                        counts={"candidates": len(cands), "created": len(created),
                                "incomplete": len(incomplete), "duplicates": len(dups)},
                        records=created, report=str(report))


def _report(ws, created, dups, incomplete, total, commit) -> Path:
    body = table(
        ["任務", "急", "負責人", "事項", "期限", "來源", "說明"],
        [["<span class='mono'>%s</span>" % c.get("task_id", "—"),
          pill("U%d" % c["urgency"], URG_HEX.get(c["urgency"], "#999")),
          esc(c["owner"]) if c["owner"] != UNKNOWN else pill("待確認", "#c9a13a"),
          esc(clip(c["title"], 44)),
          esc(c["due"]) if c["due"] != UNKNOWN else pill("待確認", "#c9a13a"),
          "<span class='cite'>%s%s</span>" % (c["source"]["type"],
                                              " #" + c["source"]["cite"] if c["source"]["cite"] else ""),
          "<span class='mono'>%s</span>" % esc(clip(c["detail"], 46))]
         for c in created], "本次無新任務 (可能全部已在台帳中, 冪等略過)")
    dup = table(["疑似重複的新任務", "負責人", "台帳既有", "相似度"],
                [[esc(clip(d["new"], 40)), esc(d["owner"]),
                  "%s %s" % (d["existing_id"], esc(clip(d["existing"], 34))),
                  esc(d["similarity"])] for d in dups],
                "無疑似重複")
    kpi = kpi_cards([("新建任務", len(created), "#5a9e6f"),
                     ("候選總數", total, "#4c78a8"),
                     ("缺負責人/期限", len(incomplete), "#c9a13a"),
                     ("疑似重複", len(dups), "#d08343")])
    return render_report(
        ws.reports / "VMT_Extract.html", "抽", "VMT 任務抽取引擎 — 郵件 × 會議",
        "provenance 必填 · 缺欄位不丟棄 · %s" % mode_label(commit),
        "治理：每筆任務都必須帶出處（哪封信／會議哪一句），無出處不得建案；"
        "缺負責人或期限者照樣建案並標成「待確認」，不讓不完整的資訊悄悄消失；"
        "疑似重複只標示不自動合併，因為合併會弄丟其中一個出處。",
        [("KPI", kpi), ("本次新建任務", body), ("疑似重複（需人工判斷）", dup)],
        "%s %s | 帳本: data/tasks.jsonl" % (ENGINE, VERSION), commit)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT Task Extraction Engine")
    add_common_args(ap)
    ap.add_argument("--me", default=None, help="本人姓名 (郵件型任務的負責人)")
    ap.add_argument("--include-questions", action="store_true",
                    help="會議未解問題也建成任務 (預設只留在記錄的待確認區)")
    a = ap.parse_args()
    banner("VMT · Task Extraction Engine %s" % VERSION, mode_label(a.commit))
    ws = Workspace(a.root)
    me = a.me or ws.load_config().get("me", "我")
    r = run(ws, me, a.commit, a.no_open, a.include_questions)
    print("[輸出] 報告:", r.report)
    print("完成.")


if __name__ == "__main__":
    main()
