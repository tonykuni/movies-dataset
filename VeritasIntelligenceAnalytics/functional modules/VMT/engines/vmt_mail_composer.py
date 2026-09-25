# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Mail Composer Engine  v1.0   --  追蹤信產生 (有限選項回覆 · 只建草稿)
----------------------------------------------------------------------------
 定位: 把 SLA 引擎排出的催辦清單, 變成可以直接寄出的追蹤信。

 沿用 VMT v1 的「有限選項回覆」格式, 這是整個閉環能自動化的關鍵:
   對方只要勾一個號碼, 系統就能解析成事件, 不需要 NLP 猜他的意思。
   自由文字回覆的解析錯誤率遠高於勾選, 而追蹤這件事錯不起。

 寄送階梯 (預設愈保守):
   dry-run          -> 只產出報告, 什麼都不寫
   --commit         -> 寫出 .txt 信稿到 mails/<日期>/, 記 TASK_MAIL_SENT 事件
   --commit --draft -> 另外在 Outlook 建立草稿 (仍需人按送出)
   --commit --send  -> 直接寄出 (不可逆, 需明確指定; 預設永遠關閉)

 為何預設不寄: 催辦信是寄給真人的。判讀錯誤造成的不是資料錯誤, 是人際成本。
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
    URG_EMOJI, URG_HEX, EngineResult, EventLog, Workspace, add_common_args,
    banner, clip, esc, kpi_cards, mode_label, pill, render_report, table, try_open,
)
from vmt_sla_engine import plan  # noqa: E402
from vmt_task_ssot import UNKNOWN  # noqa: E402

ENGINE = "vmt_mail_composer"
VERSION = "v1.0"

LIMITED_SELECTION = (
    "請選擇您的回覆（請勾選一項並直接回信）：\n"
    "[ ] 1. 已完成（請附上資料）\n"
    "[ ] 2. 需要補資料（請說明缺漏項目）\n"
    "[ ] 3. 需要澄清需求（請說明哪裡不清楚）\n"
    "[ ] 4. 需要延長時間（請提供原因＋新的 ETA，格式 YYYY-MM-DD）\n"
    "備註：______（選填，會一併記錄供專案組檢視）\n"
    "確認：是/否\n"
)


def compose(reminder: dict, sender_name: str = "專案管理系統",
            as_of: dt.date | None = None, roster: list | None = None) -> dict:
    """
    產生一封追蹤信。信中一定帶【追蹤編號】—— 那是回覆解析時唯一可靠的對應鍵,
    靠主旨比對會在對方改標題時整個斷掉。
    """
    as_of = as_of or dt.date.today()
    t = reminder["task"]
    urg = reminder["urgency"]
    case = t.get("case") or "NOCASE"
    stamp = as_of.strftime("%Y/%m/%d")
    round_no = reminder.get("round", 1)
    prefix = "催辦 %d – " % round_no if round_no > 1 else ""
    subject = "%s [%s] – %s%s – %s" % (URG_EMOJI.get(urg, ""), case, prefix,
                                       clip(t.get("title"), 40), stamp)

    if reminder.get("needs_eta"):
        due_line = "【期限】尚未確認 —— 請於回覆中提供您可以完成的 ETA"
    else:
        due_line = "【期限】%s%s" % (reminder.get("due"),
                                    "（已逾期 %d 天）" % reminder["overdue_days"]
                                    if reminder.get("overdue_days") else "")

    src = t.get("source", {})
    origin = {"MAIL": "來自郵件", "MINUTES": "來自會議記錄"}.get(src.get("type"), "來源")
    cite = "（%s，出處 %s%s）" % (origin, clip(src.get("ref", ""), 12),
                                 " 句 #" + src["cite"] if src.get("cite") else "")

    body = (
        "Dear %s，\n辛苦了，感謝您的協助。\n\n"
        "以下事項目前仍在追蹤中，需要您回覆現況，以免影響後續時程。\n\n"
        "【專案】%s\n【事項】%s\n【追蹤編號】%s\n【負責人】%s\n%s\n【追蹤理由】%s\n"
        "【說明】%s\n%s\n\n%s\n"
        "再次感謝您的協助。\nBest regards,\n%s\n（CC：管理團隊＋所有相關人）\n"
        % (t.get("owner") or "同仁", case, t.get("title"), reminder["task_id"],
           t.get("owner"), due_line, reminder["why"], t.get("detail", ""), cite,
           LIMITED_SELECTION, sender_name)
    )
    # 收件人 email 由名冊查表; 查不到就留空 —— 寧可讓人自己填, 也不猜地址
    addr = ""
    for p in (roster or []):
        if str(p.get("name") or "") == str(t.get("owner") or ""):
            addr = str(p.get("email") or "")
            break
    return {"task_id": reminder["task_id"], "to": t.get("owner"), "to_address": addr,
            "case": case, "urgency": urg, "subject": subject, "body": body,
            "round": round_no,
            "text": "主旨：%s\n收件人：%s\n%s\n%s" % (subject, addr or t.get("owner"),
                                                       "-" * 60, body)}


def _outlook_draft(mail: dict, send: bool = False) -> str:
    try:
        import win32com.client  # type: ignore
    except Exception:
        return "SKIP_NO_OUTLOOK"
    try:
        item = win32com.client.Dispatch("Outlook.Application").CreateItem(0)
        item.Subject = mail["subject"]
        item.Body = mail["body"]
        if mail.get("to_address"):
            item.To = mail["to_address"]
        if send and mail.get("to_address"):
            item.Send()
            return "SENT"
        item.Save()
        return "DRAFT"
    except Exception as e:
        return "ERROR:%s" % type(e).__name__


def run(ws: Workspace, commit: bool = False, no_open: bool = True,
        draft: bool = False, send: bool = False, as_of: dt.date | None = None,
        sender_name: str = "專案管理系統", me: str = "我",
        roster: list | None = None) -> EngineResult:
    """
    催辦清單分三流, 不能一律寄信:
      對外 : 負責人是別人 -> 產生追蹤信
      對內 : 負責人是自己 -> 這是我自己的待辦, 寄信給自己沒有意義, 列成清單
      待指派: 負責人是 [?] -> 沒有收件人可寄, 必須先由人指定負責人
    """
    ws.ensure()
    as_of = as_of or dt.date.today()
    cfg = ws.load_config()
    roster = roster if roster is not None else cfg.get("roster", [])
    p = plan(ws, as_of)
    events = EventLog(ws, commit)
    outdir = ws.outbox / as_of.strftime("%Y%m%d")

    outgoing, self_todo, unassigned = [], [], []
    for r in p["reminders"]:
        owner = (r["task"].get("owner") or UNKNOWN).strip()
        if owner == UNKNOWN:
            unassigned.append(r)
        elif owner == me:
            self_todo.append(r)
        else:
            outgoing.append(r)

    mails = []
    for r in outgoing:
        m = compose(r, sender_name, as_of, roster)
        outcome = "PLANNED"
        if commit:
            outdir.mkdir(parents=True, exist_ok=True)
            fp = outdir / ("%s_R%d_%s.txt" % (m["task_id"], m["round"], m["case"]))
            fp.write_text(m["text"], encoding="utf-8")
            outcome = "WRITTEN"
            if draft or send:
                outcome = _outlook_draft(m, send)
            events.emit("TASK_MAIL_SENT", m["task_id"],
                        "第 %d 次追蹤 | %s | %s" % (m["round"], outcome, clip(m["subject"], 50)),
                        round=m["round"], outcome=outcome)
        m["outcome"] = outcome
        mails.append(m)

    print("[信稿] 對外追蹤信 %d 封 / 自己的待辦 %d / 待指派負責人 %d (%s)"
          % (len(mails), len(self_todo), len(unassigned), mode_label(commit)))
    if commit and mails:
        print("       信稿目錄:", outdir)
    if send:
        print("       [警告] --send 已啟用: 信件直接寄出, 不可撤回")
    report = _report(ws, mails, self_todo, unassigned, commit, draft, send)
    try_open(report, no_open)
    return EngineResult(engine=ENGINE,
                        counts={"mails": len(mails), "self": len(self_todo),
                                "unassigned": len(unassigned)},
                        records=mails, report=str(report),
                        notes=["outbox=%s" % outdir] if commit else [])


def _report(ws, mails, self_todo, unassigned, commit, draft, send) -> Path:
    rows = table(
        ["急", "任務", "收件人", "主旨", "第幾次", "結果"],
        [[pill("U%d" % m["urgency"], URG_HEX.get(m["urgency"], "#999")),
          "<span class='mono'>%s</span>" % m["task_id"],
          esc(m["to"]) if m["to"] != UNKNOWN else pill("待確認", "#c9a13a"),
          esc(clip(m["subject"], 56)), esc(m["round"]),
          pill(m["outcome"], "#5a9e6f" if m["outcome"] in ("WRITTEN", "DRAFT", "SENT")
               else "#8a857c")] for m in mails],
        "今日無需寄出追蹤信")
    preview = ""
    if mails:
        preview = ("<table><tr><th>信稿預覽（第一封）</th></tr><tr><td>"
                   "<pre style='white-space:pre-wrap;font-size:12px;margin:0'>%s</pre>"
                   "</td></tr></table>" % esc(mails[0]["text"]))
    mine = table(["急", "任務", "事項", "期限", "催辦理由"],
                 [[pill("U%d" % r["urgency"], URG_HEX.get(r["urgency"], "#999")),
                   "<span class='mono'>%s</span>" % r["task_id"],
                   esc(clip(r["task"].get("title"), 46)),
                   esc(r["due"] or "—") if r["due"] != UNKNOWN else pill("無期限", "#c9a13a"),
                   esc(r["why"])] for r in self_todo],
                 "沒有屬於自己的待辦")
    una = table(["任務", "事項", "期限", "缺什麼"],
                [["<span class='mono'>%s</span>" % r["task_id"],
                  esc(clip(r["task"].get("title"), 46)),
                  esc(r["due"] or "—") if r["due"] != UNKNOWN else pill("無期限", "#c9a13a"),
                  pill("需先指定負責人", "#b5443a")] for r in unassigned],
                "所有待催辦任務都有負責人")
    mode = ("--send 直接寄出（不可逆）" if send else
            "--draft 建立 Outlook 草稿" if draft else
            "只寫出 .txt 信稿" if commit else "dry-run，不產生任何檔案")
    kpi = kpi_cards([("對外追蹤信", len(mails), "#b5443a"),
                     ("自己的待辦", len(self_todo), "#4c78a8"),
                     ("待指派負責人", len(unassigned), "#c9a13a"),
                     ("二次以上催辦", sum(1 for m in mails if m["round"] > 1), "#d08343"),
                     ("寄送模式", mode.split("（")[0], "#439a9a")])
    return render_report(
        ws.reports / "VMT_Mails.html", "信", "VMT 追蹤信引擎 — 有限選項回覆",
        "%s · %s" % (mode, mode_label(commit)),
        "治理：追蹤信一律採「有限選項回覆」，對方勾號碼即可被系統解析成事件，"
        "不需要猜測自由文字的意思。信中必帶【追蹤編號】，那是回覆解析唯一可靠的對應鍵。"
        "<strong>預設不寄送</strong>：dry-run 不產檔、--commit 只寫信稿、"
        "建草稿與寄出都需要額外明確指定。"
        "催辦分三流：負責人是別人才寄信；是自己的列成待辦清單；"
        "沒有負責人的<strong>不寄</strong>，先請人指派。",
        [("KPI", kpi), ("對外追蹤信", rows), ("我自己的待辦（不寄信）", mine),
         ("待指派負責人（無法寄信）", una), ("信稿預覽", preview)],
        "%s %s | 信稿: mails/<日期>/" % (ENGINE, VERSION), commit)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT Mail Composer Engine")
    add_common_args(ap)
    ap.add_argument("--draft", action="store_true", help="在 Outlook 建立草稿 (需 --commit)")
    ap.add_argument("--send", action="store_true",
                    help="直接寄出 (不可逆, 需 --commit; 預設關閉)")
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--sender", default="專案管理系統")
    ap.add_argument("--me", default=None, help="本人姓名 (自己的待辦不寄信)")
    a = ap.parse_args()
    banner("VMT · Mail Composer Engine %s" % VERSION, mode_label(a.commit))
    if a.send and not a.commit:
        print("[拒絕] --send 必須搭配 --commit")
        return
    ws = Workspace(a.root)
    cfg = ws.load_config()
    r = run(ws, a.commit, a.no_open, a.draft, a.send,
            dt.date.fromisoformat(a.as_of) if a.as_of else None,
            a.sender if a.sender != "專案管理系統" else cfg.get("sender_name", a.sender),
            a.me or cfg.get("me", "我"))
    print("[輸出] 報告:", r.report)
    print("完成.")


if __name__ == "__main__":
    main()
