# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Task SSOT Engine  v1.0   --  工作管理單一真相 (宣告 add-only · 狀態由事件推導)
----------------------------------------------------------------------------
 定位: 整個系統的工作台帳。任務只「宣告」一次 (tasks.jsonl, add-only),
       之後所有變化 (回覆 / 展延 / 完成 / 升級) 一律寫成事件,
       狀態永遠是 replay 出來的 —— 沒有任何一列會被 UPDATE。

 為何堅持事件推導:
   1. 可稽核 : 「這件事為什麼變成逾期」能一路回放到當初那封信
   2. 可重算 : 規則改了 (例如 SLA 天數調整) 重跑即可, 歷史不需遷移
   3. 防競態 : 多個引擎同時寫入也不會互相覆蓋, 因為沒有人「改」東西

 任務來源 (provenance 必填, 無來源不得建案):
   MAIL    -> 來自某封信 (mail_uid)
   MINUTES -> 來自某場會議的某一句 (minute_uid + 句號 #012)

 狀態機: OPEN -> ACK -> IN_PROGRESS -> DONE
         任一狀態可轉 BLOCKED / CANCELLED; 逾期由 due 與今日推導, 不是欄位。
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
import argparse
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vmt_core import (  # noqa: E402
    STATUS_HEX, URG_HEX, EngineResult, EventLog, Ledger, Workspace,
    add_common_args, banner, clip, esc, fingerprint, kpi_cards, mode_label,
    next_serial, pill, render_report, table, try_open,
)

ENGINE = "vmt_task_ssot"
VERSION = "v1.0"

UNKNOWN = "[?]"
OPEN_STATES = ("OPEN", "ACK", "IN_PROGRESS", "BLOCKED", "OVERDUE")

# 事件 -> 狀態 (只列會改變狀態者)
_EVENT_STATE = {
    "TASK_CREATED": "OPEN",
    "TASK_MAIL_SENT": "OPEN",
    "TASK_ACK": "ACK",
    "TASK_PROGRESS": "IN_PROGRESS",
    "TASK_BLOCKED": "BLOCKED",
    "TASK_DONE": "DONE",
    "TASK_CANCELLED": "CANCELLED",
}


# ---------------------------------------------------------------- 建案 ------


def task_fingerprint(source_type: str, ref: str, cite: str, title: str) -> str:
    """
    冪等指紋。同一封信 / 同一句會議發言只會產生一個任務,
    無論管線重跑幾次 —— 這是「自動化不製造垃圾」的底線。
    """
    return fingerprint(source_type, ref, cite, str(title)[:40])


def build_task(title: str, owner: str, due: str | None, urgency: int,
               source_type: str, ref: str, cite: str = "",
               case: str | None = None, requester: str = "",
               detail: str = "") -> dict:
    return {
        "fingerprint": task_fingerprint(source_type, ref, cite, title),
        "title": str(title).strip(),
        "owner": owner or UNKNOWN,
        "requester": requester,
        "due": due or UNKNOWN,
        "urgency": int(urgency or 3),
        "case": case,
        "detail": detail,
        "source": {"type": source_type, "ref": ref, "cite": cite},
        "engine_version": VERSION,
    }


def create_tasks(ws: Workspace, candidates: list[dict], commit: bool = False) -> list[dict]:
    """宣告新任務。已存在指紋者略過 (冪等), 回傳本次真正新增的任務。"""
    ledger = Ledger(ws.tasks_ledger, commit)
    events = EventLog(ws, commit)
    existing = ledger.read()
    seen = {t.get("fingerprint") for t in existing}
    ids = [t.get("task_id") for t in existing]
    created = []
    for c in candidates:
        if c["fingerprint"] in seen:
            continue
        c = dict(c)
        c["task_id"] = next_serial("TASK", ids)
        ids.append(c["task_id"])
        seen.add(c["fingerprint"])
        ledger.append(c)
        events.emit("TASK_CREATED", c["task_id"],
                    "%s | %s | due %s" % (clip(c["title"], 40), c["owner"], c["due"]),
                    owner=c["owner"], due=c["due"], urgency=c["urgency"],
                    source=c["source"])
        created.append(c)
    return created


# ---------------------------------------------------------------- 狀態 ------


def load_tasks(ws: Workspace) -> list[dict]:
    return Ledger(ws.tasks_ledger, False).read()


def derive_states(ws: Workspace, events: list[dict] | None = None,
                  as_of: dt.date | None = None) -> dict[str, dict]:
    """
    replay 事件流, 推導每個任務的現況。
    逾期不是欄位而是推導結果: due < 今日 且未完成 -> OVERDUE。
    因此「今天」變了, 狀態自動跟著變, 不需要任何排程去改資料。
    """
    as_of = as_of or dt.date.today()
    evs = events if events is not None else EventLog(ws, False).read()
    tasks = {t["task_id"]: t for t in load_tasks(ws) if t.get("task_id")}
    state: dict[str, dict] = {
        tid: {"task_id": tid, "status": "OPEN", "due": t.get("due"),
              "urgency": t.get("urgency", 3), "history": [], "reply": None,
              "mail_sent": 0, "escalations": 0, "task": t}
        for tid, t in tasks.items()
    }
    for e in sorted(evs, key=lambda r: r.get("ts", "")):
        tid, ev = e.get("ref"), e.get("event", "")
        s = state.get(tid)
        if not s or not ev.startswith("TASK_"):
            continue
        s["history"].append({"ts": e.get("ts"), "event": ev, "detail": e.get("detail", "")})
        if ev in _EVENT_STATE:
            s["status"] = _EVENT_STATE[ev]
        payload = e.get("payload") or {}
        if ev == "TASK_MAIL_SENT":
            s["mail_sent"] += 1
        if ev == "TASK_ESCALATED":
            s["escalations"] += 1
            s["urgency"] = min(5, int(payload.get("urgency", s["urgency"])))
        if ev == "TASK_DUE_EXTENDED" and payload.get("due"):
            s["due"] = payload["due"]                 # 展延 = 新事件, 舊期限仍留在 history
        if ev == "TASK_ACK" and payload:
            s["reply"] = payload
        s["last_ts"] = e.get("ts")

    for s in state.values():
        if s["status"] in ("DONE", "CANCELLED"):
            continue
        due = s.get("due")
        if due and due != UNKNOWN:
            try:
                if dt.date.fromisoformat(due) < as_of:
                    s["overdue_days"] = (as_of - dt.date.fromisoformat(due)).days
                    s["status"] = "OVERDUE"
            except ValueError:
                pass
    return state


def open_tasks(ws: Workspace, as_of: dt.date | None = None) -> list[dict]:
    return [s for s in derive_states(ws, as_of=as_of).values() if s["status"] in OPEN_STATES]


# ---------------------------------------------------------------- 報告 ------


def run(ws: Workspace, commit: bool = False, no_open: bool = True,
        as_of: dt.date | None = None) -> EngineResult:
    """本引擎不建案 (建案由 vmt_extract_tasks), 只負責推導與呈現台帳現況。"""
    ws.ensure()
    states = derive_states(ws, as_of=as_of)
    rows = sorted(states.values(),
                  key=lambda s: (s["status"] not in OPEN_STATES, -s["urgency"],
                                 str(s.get("due") or "9999")))
    counts: dict[str, int] = {}
    for s in rows:
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    print("[台帳] 任務 %d 筆 | %s" % (len(rows),
                                     " / ".join("%s %d" % kv for kv in counts.items()) or "—"))
    report = _report(ws, rows, counts, commit)
    try_open(report, no_open)
    return EngineResult(engine=ENGINE, counts=counts, records=rows, report=str(report))


def _report(ws: Workspace, rows: list[dict], counts: dict, commit: bool) -> Path:
    body = table(
        ["任務", "狀態", "急", "負責人", "事項", "期限", "來源"],
        [["<span class='mono'>%s</span>" % s["task_id"],
          pill(s["status"] + (" +%dd" % s["overdue_days"] if s.get("overdue_days") else ""),
               STATUS_HEX.get(s["status"], "#999")),
          pill("U%d" % s["urgency"], URG_HEX.get(s["urgency"], "#999")),
          esc(s["task"].get("owner")), esc(clip(s["task"].get("title"), 46)),
          esc(s.get("due") or "—"),
          "<span class='cite'>%s %s%s</span>" % (
              s["task"]["source"]["type"], clip(s["task"]["source"]["ref"], 10),
              (" #" + s["task"]["source"]["cite"]) if s["task"]["source"].get("cite") else "")]
         for s in rows], "台帳尚無任務")
    kpi = kpi_cards([("進行中", sum(counts.get(k, 0) for k in ("OPEN", "ACK", "IN_PROGRESS")), "#4c78a8"),
                     ("逾期", counts.get("OVERDUE", 0), "#b5443a"),
                     ("受阻", counts.get("BLOCKED", 0), "#d08343"),
                     ("已完成", counts.get("DONE", 0), "#5a9e6f"),
                     ("總計", len(rows), "#8a857c")])
    return render_report(
        ws.reports / "VMT_Tasks.html", "帳", "VMT 工作管理台帳 — 任務 SSOT",
        "宣告 add-only · 狀態由事件推導 · %s" % mode_label(commit),
        "治理：任務只宣告一次；所有變化寫成事件，狀態一律 replay 推導，"
        "沒有任何一列被 UPDATE。逾期是推導結果而非欄位，因此不需要排程去改資料。"
        "每個任務都必須帶來源（哪封信／會議哪一句），無來源不得建案。",
        [("KPI", kpi), ("任務台帳", body)],
        "%s %s | 帳本: data/tasks.jsonl + events.jsonl" % (ENGINE, VERSION), commit)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT Task SSOT Engine")
    add_common_args(ap)
    a = ap.parse_args()
    banner("VMT · Task SSOT Engine %s" % VERSION, mode_label(a.commit))
    r = run(Workspace(a.root), a.commit, a.no_open)
    print("[輸出] 報告:", r.report)
    print("完成.")


if __name__ == "__main__":
    main()
