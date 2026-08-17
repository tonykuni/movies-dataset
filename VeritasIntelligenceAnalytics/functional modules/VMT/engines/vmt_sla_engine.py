# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · SLA & Escalation Engine  v1.0   --  逾期偵測 · 自動升級 · 催辦排程
----------------------------------------------------------------------------
 定位: 決定「今天該催誰、催多急」。人工追蹤最容易失守的就是這一段 ——
       事情不會自己提醒你, 而愈是重要的案子愈容易被更急的事蓋掉。

 三件事:
   1 逾期偵測  : 由 due 與今日推導 (不是欄位), 規則改了重跑即可
   2 自動升級  : 逾期天數 -> 緊急度上調, 並記 TASK_ESCALATED 事件 (冪等, 不重複升級)
   3 催辦排程  : 依緊急度決定回催間隔, 產出「今天該寄的追蹤信」清單交給 composer

 刻意不做的事:
   - 不替沒有期限的任務「自動填一個期限」。系統推定的期限會被當成對方承諾的期限,
     那是憑空捏造。改為標記 NEEDS_ETA, 讓追蹤信去問對方要一個 ETA。
   - 不自動寄信。本引擎只排程, 寄送一律由 composer 在 --commit 下進行。
============================================================================
"""
from __future__ import annotations

import sys
import argparse
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vmt_core import (  # noqa: E402
    STATUS_HEX, URG_HEX, EngineResult, EventLog, Workspace, add_common_args,
    banner, clip, esc, kpi_cards, mode_label, pill, render_report, table, try_open,
)
from vmt_task_ssot import UNKNOWN, derive_states  # noqa: E402

ENGINE = "vmt_sla_engine"
VERSION = "v1.0"

# 緊急度 -> (建議處理天數, 回催間隔天數)。建議天數只用於「請對方給 ETA」的話術,
# 不會寫進 due 欄位。
SLA_DAYS = {5: (1, 1), 4: (2, 2), 3: (5, 3), 2: (10, 7), 1: (0, 0)}

# 逾期天數 -> 升級後的緊急度
ESCALATION_LADDER = [(7, 5), (3, 5), (1, 4)]


def _days_since(ts: str | None, as_of: dt.date) -> int | None:
    if not ts:
        return None
    try:
        return (as_of - dt.date.fromisoformat(str(ts)[:10])).days
    except ValueError:
        return None


def _last_mail_ts(state: dict) -> str | None:
    hist = state.get("history", []) if isinstance(state, dict) else []
    sent = [h["ts"] for h in hist if h["event"] == "TASK_MAIL_SENT"]
    return sent[-1] if sent else None


def sla_table(ws: Workspace) -> dict:
    """讀設定檔覆寫 SLA 天數。沒設定就用預設值, 設定壞掉也不影響主線。"""
    table = dict(SLA_DAYS)
    for k, v in (ws.load_config().get("sla_days") or {}).items():
        try:
            table[int(k)] = (int(v[0]), int(v[1]))
        except Exception:
            continue
    return table


def plan(ws: Workspace, as_of: dt.date | None = None) -> dict:
    """
    產生今日的 SLA 計畫。純函式 (不寫任何東西), 因此可以隨時試算、可以被測試。
    """
    as_of = as_of or dt.date.today()
    sla = sla_table(ws)
    states = derive_states(ws, as_of=as_of)
    escalations, reminders, needs_eta = [], [], []

    for s in states.values():
        if s["status"] in ("DONE", "CANCELLED"):
            continue
        t = s["task"]
        urg = s["urgency"]

        # 1 升級: 逾期天數決定新緊急度; 已達該級數者不重複升級 (冪等)
        od = s.get("overdue_days")
        if od:
            for threshold, new_urg in ESCALATION_LADDER:
                if od >= threshold:
                    if new_urg > urg:
                        escalations.append({"task_id": s["task_id"], "from": urg,
                                            "to": new_urg, "overdue_days": od,
                                            "title": t.get("title"), "owner": t.get("owner")})
                        urg = new_urg
                    break

        # 2 無期限 -> 索取 ETA (不自行填期限)
        if not s.get("due") or s["due"] == UNKNOWN:
            needs_eta.append({"task_id": s["task_id"], "title": t.get("title"),
                              "owner": t.get("owner"),
                              "suggest_days": sla.get(urg, (5, 3))[0]})

        # 3 催辦: 從未寄過 -> 立即寄; 寄過 -> 依緊急度間隔回催
        interval = sla.get(urg, (5, 3))[1]
        last = _last_mail_ts(s)
        since = _days_since(last, as_of)
        if s["status"] == "ACK" and not od:
            continue                                  # 對方已回覆且未逾期 -> 不打擾
        # 逾期本身不構成「再催一次」的理由 —— 逾期已經透過升級縮短了回催間隔。
        # 若讓逾期獨立觸發, 同一天每跑一次管線就會多寄一封, 對方會被洗版。
        if last is None:
            why = "尚未寄出追蹤信" + ("（已逾期 %d 天）" % od if od else "")
        elif interval and since is not None and since >= interval:
            why = "距上次追蹤已 %d 天（U%d 回催間隔 %d 天）%s" % (
                since, urg, interval, "，已逾期 %d 天" % od if od else "")
        else:
            continue
        reminders.append({"task_id": s["task_id"], "urgency": urg, "why": why,
                          "status": s["status"], "overdue_days": od,
                          "due": s.get("due"), "task": t,
                          "needs_eta": not s.get("due") or s["due"] == UNKNOWN,
                          "round": s["mail_sent"] + 1})

    reminders.sort(key=lambda r: (-r["urgency"], str(r.get("due") or "9999")))
    return {"as_of": as_of.isoformat(), "escalations": escalations,
            "reminders": reminders, "needs_eta": needs_eta, "states": states}


def run(ws: Workspace, commit: bool = False, no_open: bool = True,
        as_of: dt.date | None = None) -> EngineResult:
    ws.ensure()
    p = plan(ws, as_of)
    events = EventLog(ws, commit)
    for e in p["escalations"]:
        events.emit("TASK_ESCALATED", e["task_id"],
                    "逾期 %d 天 -> U%d (原 U%d)" % (e["overdue_days"], e["to"], e["from"]),
                    urgency=e["to"], overdue_days=e["overdue_days"])

    print("[SLA] 基準日 %s | 升級 %d / 待催辦 %d / 需索取 ETA %d"
          % (p["as_of"], len(p["escalations"]), len(p["reminders"]), len(p["needs_eta"])))
    report = _report(ws, p, commit)
    try_open(report, no_open)
    return EngineResult(engine=ENGINE,
                        counts={"escalated": len(p["escalations"]),
                                "reminders": len(p["reminders"]),
                                "needs_eta": len(p["needs_eta"])},
                        records=p["reminders"], report=str(report),
                        notes=["as_of=%s" % p["as_of"]])


def _report(ws, p, commit) -> Path:
    rem = table(
        ["急", "任務", "狀態", "負責人", "事項", "期限", "催辦理由", "第幾次"],
        [[pill("U%d" % r["urgency"], URG_HEX.get(r["urgency"], "#999")),
          "<span class='mono'>%s</span>" % r["task_id"],
          pill(r["status"], STATUS_HEX.get(r["status"], "#999")),
          esc(r["task"].get("owner")), esc(clip(r["task"].get("title"), 40)),
          esc(r["due"] or "—") if r["due"] != UNKNOWN else pill("無期限", "#c9a13a"),
          esc(r["why"]), esc(r["round"])] for r in p["reminders"]],
        "今日無需催辦 — 所有任務都在間隔內或已回覆")
    esc_t = table(["任務", "逾期天數", "緊急度", "負責人", "事項"],
                  [["<span class='mono'>%s</span>" % e["task_id"], esc(e["overdue_days"]),
                    "U%d → %s" % (e["from"], pill("U%d" % e["to"], URG_HEX[e["to"]])),
                    esc(e["owner"]), esc(clip(e["title"], 40))] for e in p["escalations"]],
                  "本次無需升級")
    eta = table(["任務", "負責人", "事項", "建議處理天數"],
                [["<span class='mono'>%s</span>" % n["task_id"], esc(n["owner"]),
                  esc(clip(n["title"], 44)), esc("%d 天" % n["suggest_days"])]
                 for n in p["needs_eta"]],
                "所有任務都有期限")
    kpi = kpi_cards([("今日待催辦", len(p["reminders"]), "#b5443a"),
                     ("自動升級", len(p["escalations"]), "#d08343"),
                     ("需索取 ETA", len(p["needs_eta"]), "#c9a13a"),
                     ("基準日", p["as_of"], "#4c78a8")])
    return render_report(
        ws.reports / "VMT_SLA.html", "催", "VMT SLA 引擎 — 逾期 · 升級 · 催辦",
        "逾期由推導得出 · 升級冪等 · %s" % mode_label(commit),
        "治理：逾期是 due 與今日推導的結果而非欄位，規則調整只需重跑；"
        "升級寫成 TASK_ESCALATED 事件且同一級不重複升級；"
        "<strong>系統不會替沒有期限的任務自行填期限</strong>——那等於捏造對方的承諾，"
        "改以追蹤信向對方索取 ETA。本引擎只排程，寄送由 composer 負責。",
        [("KPI", kpi), ("今日催辦清單", rem), ("自動升級", esc_t), ("需索取 ETA", eta)],
        "%s %s | 讀 tasks.jsonl + events.jsonl" % (ENGINE, VERSION), commit)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT SLA & Escalation Engine")
    add_common_args(ap)
    ap.add_argument("--as-of", default=None, help="以指定日期試算 (YYYY-MM-DD)")
    a = ap.parse_args()
    banner("VMT · SLA & Escalation Engine %s" % VERSION, mode_label(a.commit))
    as_of = dt.date.fromisoformat(a.as_of) if a.as_of else None
    r = run(Workspace(a.root), a.commit, a.no_open, as_of)
    print("[輸出] 報告:", r.report)
    print("完成.")


if __name__ == "__main__":
    main()
