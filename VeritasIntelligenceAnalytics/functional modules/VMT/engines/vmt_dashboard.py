# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Dashboard Engine  v1.0   --  戰情總覽 (單頁看完全部)
----------------------------------------------------------------------------
 定位: 一頁回答四個問題 —— 誰欠我東西、我欠誰東西、哪些要爆了、哪些系統不敢自己決定。

 資料一律取自帳本推導, 本引擎不寫任何東西 (純讀), 因此隨時可跑、跑幾次都一樣。
 「系統不敢自己決定」的那一區 (Q01 隔離 + 待確認欄位) 刻意放在顯眼位置:
 自動化系統最危險的失敗模式, 是讓人以為它已經處理完了。
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
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vmt_core import (  # noqa: E402
    STATUS_HEX, URG_HEX, EngineResult, EventLog, Ledger, Quarantine, Workspace,
    add_common_args, banner, clip, esc, kpi_cards, mode_label, pill,
    render_report, table, try_open,
)
from vmt_ai_triage import load_triage  # noqa: E402
from vmt_outlook_intake import load_mails  # noqa: E402
from vmt_sla_engine import plan  # noqa: E402
from vmt_task_ssot import OPEN_STATES, UNKNOWN, derive_states  # noqa: E402

ENGINE = "vmt_dashboard"
VERSION = "v1.0"


def run(ws: Workspace, commit: bool = True, no_open: bool = True,
        as_of: dt.date | None = None) -> EngineResult:
    ws.ensure()
    as_of = as_of or dt.date.today()
    states = derive_states(ws, as_of=as_of)
    p = plan(ws, as_of)
    mails = load_mails(ws)
    triage = load_triage(ws)
    quar = Quarantine(ws, False).open_items()
    minutes = Ledger(ws.minutes_ledger, False).read()
    events = EventLog(ws, False).read()

    rows = list(states.values())
    counts = Counter(s["status"] for s in rows)
    overdue = sorted([s for s in rows if s["status"] == "OVERDUE"],
                     key=lambda s: -s.get("overdue_days", 0))
    open_rows = sorted([s for s in rows if s["status"] in OPEN_STATES],
                       key=lambda s: (-s["urgency"], str(s.get("due") or "9999")))
    pending = [s for s in rows if s["status"] in OPEN_STATES
               and (s["task"].get("owner") == UNKNOWN or not s.get("due")
                    or s.get("due") == UNKNOWN)]

    by_case = Counter((s["task"].get("case") or "NOCASE") for s in rows
                      if s["status"] in OPEN_STATES)
    by_owner = Counter(s["task"].get("owner") for s in rows if s["status"] in OPEN_STATES)

    print("[總覽] 任務 %d (進行中 %d / 逾期 %d / 完成 %d) | 今日待催 %d | Q01 未解 %d"
          % (len(rows), sum(counts[k] for k in ("OPEN", "ACK", "IN_PROGRESS")),
             counts["OVERDUE"], counts["DONE"], len(p["reminders"]), len(quar)))

    report = _report(ws, as_of, rows, counts, overdue, open_rows, pending, p,
                     by_case, by_owner, mails, triage, quar, minutes, events)
    try_open(report, no_open)
    return EngineResult(engine=ENGINE,
                        counts={"tasks": len(rows), "overdue": counts["OVERDUE"],
                                "reminders": len(p["reminders"]), "q01": len(quar)},
                        records=rows, report=str(report))


def _report(ws, as_of, rows, counts, overdue, open_rows, pending, p,
            by_case, by_owner, mails, triage, quar, minutes, events) -> Path:
    kpi = kpi_cards([
        ("逾期", counts["OVERDUE"], "#b5443a"),
        ("進行中", sum(counts[k] for k in ("OPEN", "ACK", "IN_PROGRESS")), "#4c78a8"),
        ("今日待催辦", len(p["reminders"]), "#d08343"),
        ("待確認欄位", len(pending), "#c9a13a"),
        ("Q01 未解", len(quar), "#c9a13a"),
        ("已完成", counts["DONE"], "#5a9e6f"),
    ])
    od = table(["逾期", "急", "任務", "負責人", "事項", "期限", "催了幾次"],
               [[pill("+%dd" % s.get("overdue_days", 0), "#b5443a"),
                 pill("U%d" % s["urgency"], URG_HEX.get(s["urgency"], "#999")),
                 "<span class='mono'>%s</span>" % s["task_id"],
                 esc(s["task"].get("owner")), esc(clip(s["task"].get("title"), 42)),
                 esc(s.get("due")), esc(s["mail_sent"])] for s in overdue],
               "沒有逾期任務")
    op = table(["急", "狀態", "任務", "負責人", "事項", "期限", "來源"],
               [[pill("U%d" % s["urgency"], URG_HEX.get(s["urgency"], "#999")),
                 pill(s["status"], STATUS_HEX.get(s["status"], "#999")),
                 "<span class='mono'>%s</span>" % s["task_id"],
                 esc(s["task"].get("owner")), esc(clip(s["task"].get("title"), 40)),
                 esc(s.get("due") or "—") if s.get("due") != UNKNOWN
                 else pill("無期限", "#c9a13a"),
                 "<span class='cite'>%s</span>" % s["task"]["source"]["type"]]
                for s in open_rows], "台帳沒有進行中的任務")
    hold = table(["需要人工判斷的項目", "原因", "信心", "來源"],
                 [[esc(clip(str(q.get("raw")), 60)), esc(q.get("reason_code")),
                   esc(q.get("confidence")), "<span class='cite'>%s</span>"
                   % esc(clip(q.get("source", ""), 24))] for q in quar],
                 "沒有待人工處理的項目")
    pend = table(["任務", "負責人", "事項", "缺什麼"],
                 [["<span class='mono'>%s</span>" % s["task_id"],
                   esc(s["task"].get("owner")) if s["task"].get("owner") != UNKNOWN
                   else pill("待確認", "#c9a13a"),
                   esc(clip(s["task"].get("title"), 44)),
                   esc("、".join(x for x in
                                 (["負責人"] if s["task"].get("owner") == UNKNOWN else []) +
                                 (["期限"] if not s.get("due") or s.get("due") == UNKNOWN
                                  else [])))] for s in pending],
                 "所有進行中的任務欄位都完整")
    dist = table(["案號 / 負責人", "進行中任務數"],
                 [[esc(k), esc(v)] for k, v in (list(by_case.most_common()) +
                                                list(by_owner.most_common()))],
                 "無進行中任務")
    src = table(["帳本", "筆數", "說明"],
                [["mails.jsonl", len(mails), "已入帳郵件（來源只讀）"],
                 ["triage.jsonl", len(triage), "AI 判讀結果"],
                 ["minutes.jsonl", len(minutes), "會議記錄（含標記逐字稿）"],
                 ["tasks.jsonl", len(rows), "任務宣告（add-only）"],
                 ["events.jsonl", len(events), "事件流（狀態的唯一真相）"],
                 ["quarantine.jsonl", len(quar), "Q01 待人工（未解）"]])
    return render_report(
        ws.reports / "VMT_Dashboard.html", "覽", "VMT 戰情總覽 — Outlook × 工作管理",
        "基準日 %s · 純讀推導 · 不寫任何資料" % as_of.isoformat(),
        "治理：本頁所有數字都由帳本 replay 推導，不存在任何快取或可變狀態，"
        "因此隨時可跑、跑幾次結果都一樣。"
        "「需要人工判斷」與「待確認欄位」兩區刻意放在前段——"
        "自動化系統最危險的失敗模式，是讓人以為它已經全部處理完了。",
        [("KPI", kpi), ("逾期任務（最優先）", od), ("需要人工判斷 · Q01", hold),
         ("待確認欄位（缺負責人或期限）", pend), ("進行中任務", op),
         ("分佈", dist), ("帳本統計", src)],
        "%s %s | 全部數據來自 data/*.jsonl 推導" % (ENGINE, VERSION), True)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT Dashboard Engine")
    add_common_args(ap)
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args()
    banner("VMT · Dashboard Engine %s" % VERSION, "純讀，不寫任何資料")
    r = run(Workspace(a.root), True, a.no_open,
            dt.date.fromisoformat(a.as_of) if a.as_of else None)
    print("[輸出] 報告:", r.report)
    print("完成.")


if __name__ == "__main__":
    main()
