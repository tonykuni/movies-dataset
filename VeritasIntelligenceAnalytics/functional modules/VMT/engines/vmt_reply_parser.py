# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Reply Parser Engine  v1.0   --  回覆解析 (勾選 -> 事件, 閉環收口)
----------------------------------------------------------------------------
 定位: 閉環的最後一哩。把對方回信裡的勾選, 變成台帳上的狀態事件。

 解析對象 (依可靠度排序, 只採信高可靠的部分):
   1 【追蹤編號】TASK-0003   -> 對應到哪個任務 (唯一可靠鍵; 主旨會被對方改, 編號不會)
   2 [x] 1-4                 -> 回覆選項 (勾選, 不是自由文字, 因此不會解析錯)
   3 ETA / 新期限            -> 選項 4 才採用, 換算成絕對日期
   4 備註                    -> 原文照收, 只入事件不做語意判斷

 事件對應:
   1 已完成      -> TASK_ACK + TASK_DONE
   2 需要補資料  -> TASK_ACK + TASK_BLOCKED
   3 需要澄清    -> TASK_ACK + TASK_BLOCKED
   4 需要延長    -> TASK_ACK + TASK_DUE_EXTENDED(new due)  ※ 沒給 ETA 就不展延
 找不到追蹤編號的回信 -> Q01 隔離 (UNMATCHED_REPLY), 絕不猜對應, 也絕不丟棄。
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

import re
import sys
import argparse
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vmt_core import (  # noqa: E402
    EngineResult, EventLog, Quarantine, Workspace, add_common_args, banner,
    clip, esc, kpi_cards, mode_label, pill, render_report, table, try_open,
)
from vmt_lang import resolve_due  # noqa: E402
from vmt_outlook_intake import load_mails  # noqa: E402
from vmt_task_ssot import load_tasks  # noqa: E402

ENGINE = "vmt_reply_parser"
VERSION = "v1.0"

OPTION_LABEL = {1: "已完成", 2: "需要補資料", 3: "需要澄清需求", 4: "需要延長時間"}
OPTION_EVENT = {1: "TASK_DONE", 2: "TASK_BLOCKED", 3: "TASK_BLOCKED", 4: "TASK_DUE_EXTENDED"}

_TASK_RE = re.compile(r"(TASK-\d{4,})", re.IGNORECASE)
_OPT_RE = re.compile(r"\[\s*[xX✓✔v√]\s*\]\s*([1-4])")
_NOTE_RE = re.compile(r"備註\s*[:：]?\s*(.+)")
_CONFIRM_RE = re.compile(r"確認\s*[:：]?\s*(是|否|yes|no)", re.IGNORECASE)


def parse_reply(mail: dict, base_date: dt.date | None = None) -> dict:
    """解析單封回信。無法確定的欄位一律留 None, 不做推測。"""
    body = mail.get("body") or ""
    subject = mail.get("subject") or ""
    blob = "%s\n%s" % (subject, body)

    m = _TASK_RE.search(blob)
    task_id = m.group(1).upper() if m else None

    opt_m = _OPT_RE.search(body)
    option = int(opt_m.group(1)) if opt_m else None

    note_m = _NOTE_RE.search(body)
    note = note_m.group(1).strip() if note_m else ""
    note = "" if note.startswith("____") else clip(note, 200)

    conf_m = _CONFIRM_RE.search(body)
    confirmed = None
    if conf_m:
        confirmed = conf_m.group(1).lower() in ("是", "yes")

    eta = None
    if option == 4:
        # ETA 只在選項 4 採用: 其他選項裡出現的日期通常是在描述現況, 不是新期限
        due = resolve_due(note or body, base_date)
        eta = due[0].isoformat() if due else None

    return {"mail_uid": mail.get("mail_uid"), "task_id": task_id, "option": option,
            "option_label": OPTION_LABEL.get(option, ""), "note": note,
            "confirmed": confirmed, "eta": eta,
            "sender": mail.get("sender", ""), "subject": subject,
            "received": mail.get("received", "")}


def run(ws: Workspace, commit: bool = False, no_open: bool = True,
        base_date: dt.date | None = None) -> EngineResult:
    ws.ensure()
    events = EventLog(ws, commit)
    quar = Quarantine(ws, commit)
    known_tasks = {t.get("task_id") for t in load_tasks(ws)}

    processed = {(e.get("payload") or {}).get("mail_uid")
                 for e in events.read() if e.get("event") == "TASK_ACK"}

    applied, unmatched, skipped = [], [], 0
    for mail in load_mails(ws):
        r = parse_reply(mail, base_date)
        if r["option"] is None and not r["task_id"]:
            continue                                     # 不是回覆信, 略過
        if r["mail_uid"] in processed:
            skipped += 1
            continue
        if not r["task_id"] or r["task_id"] not in known_tasks:
            held = quar.hold("REPLY:%s" % r["mail_uid"], "UNMATCHED_REPLY", 0.3,
                             {"subject": r["subject"], "sender": r["sender"],
                              "option": r["option"], "note": r["note"],
                              "found_id": r["task_id"]}, ref=r["mail_uid"] or "")
            if held is None:
                skipped += 1          # 先前已隔離, 不重複計數
            else:
                unmatched.append(r)
            continue

        events.emit("TASK_ACK", r["task_id"],
                    "%s 回覆選項 %s %s" % (r["sender"], r["option"], r["option_label"]),
                    mail_uid=r["mail_uid"], option=r["option"],
                    option_label=r["option_label"], note=r["note"],
                    confirmed=r["confirmed"], eta=r["eta"])
        ev = OPTION_EVENT.get(r["option"])
        if ev == "TASK_DONE" and r["confirmed"] is False:
            ev = None                                    # 勾了完成卻寫「確認：否」-> 不收口
            r["note"] = (r["note"] + " ｜系統：勾選已完成但確認欄為否，未收口").strip()
        if ev == "TASK_DUE_EXTENDED" and not r["eta"]:
            ev = "TASK_BLOCKED"                          # 要延期卻沒給 ETA -> 視為受阻
            r["note"] = (r["note"] + " ｜系統：申請延期但未提供 ETA").strip()
        if ev:
            events.emit(ev, r["task_id"],
                        "%s（%s）%s" % (r["option_label"], r["sender"], clip(r["note"], 60)),
                        mail_uid=r["mail_uid"], due=r["eta"])
        r["event"] = ev or "TASK_ACK"
        applied.append(r)

    print("[回覆] 套用 %d 封 / 無法對應 %d 封 (已隔離) / 冪等略過 %d 封"
          % (len(applied), len(unmatched), skipped))
    report = _report(ws, applied, unmatched, skipped, commit)
    try_open(report, no_open)
    return EngineResult(engine=ENGINE,
                        counts={"applied": len(applied), "unmatched": len(unmatched),
                                "skipped": skipped},
                        records=applied, report=str(report))


def _report(ws, applied, unmatched, skipped, commit) -> Path:
    ev_hex = {"TASK_DONE": "#5a9e6f", "TASK_BLOCKED": "#b5443a",
              "TASK_DUE_EXTENDED": "#d08343", "TASK_ACK": "#439a9a"}
    rows = table(
        ["任務", "回覆者", "選項", "產生事件", "新 ETA", "備註"],
        [["<span class='mono'>%s</span>" % r["task_id"], esc(r["sender"]),
          "%s %s" % (r["option"], esc(r["option_label"])),
          pill(r["event"], ev_hex.get(r["event"], "#999")),
          esc(r["eta"] or "—"), esc(clip(r["note"], 50))] for r in applied],
        "本次無新回覆")
    un = table(["寄件者", "主旨", "勾選", "備註", "處置"],
               [[esc(r["sender"]), esc(clip(r["subject"], 40)), esc(r["option"] or "—"),
                 esc(clip(r["note"], 40)), pill("Q01 隔離待人工", "#c9a13a")]
                for r in unmatched],
               "所有回覆都成功對應到任務")
    kpi = kpi_cards([("已收口", sum(1 for r in applied if r["event"] == "TASK_DONE"), "#5a9e6f"),
                     ("受阻", sum(1 for r in applied if r["event"] == "TASK_BLOCKED"), "#b5443a"),
                     ("展延", sum(1 for r in applied if r["event"] == "TASK_DUE_EXTENDED"), "#d08343"),
                     ("無法對應", len(unmatched), "#c9a13a"),
                     ("冪等略過", skipped, "#8a857c")])
    return render_report(
        ws.reports / "VMT_Replies.html", "覆", "VMT 回覆解析引擎 — 閉環收口",
        "勾選為準 · 不猜自由文字 · %s" % mode_label(commit),
        "治理：只採信【追蹤編號】與勾選這兩個高可靠訊號；找不到編號的回信送 Q01 隔離，"
        "既不猜對應也不丟棄。兩個刻意的保守設計："
        "勾「已完成」但確認欄填「否」<strong>不收口</strong>；"
        "申請延期卻未提供 ETA <strong>不展延</strong>，改記為受阻。",
        [("KPI", kpi), ("已套用的回覆", rows), ("無法對應的回覆（Q01）", un)],
        "%s %s | 事件: events.jsonl" % (ENGINE, VERSION), commit)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT Reply Parser Engine")
    add_common_args(ap)
    a = ap.parse_args()
    banner("VMT · Reply Parser Engine %s" % VERSION, mode_label(a.commit))
    r = run(Workspace(a.root), a.commit, a.no_open)
    print("[輸出] 報告:", r.report)
    print("完成.")


if __name__ == "__main__":
    main()
