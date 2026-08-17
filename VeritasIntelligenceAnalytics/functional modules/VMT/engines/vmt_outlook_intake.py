# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Outlook Intake Engine  v1.0   --  收信引擎 (來源只讀 · MD5 去重)
----------------------------------------------------------------------------
 定位: 系統的唯一入口。把郵件從來源「複製」進 add-only 帳本, 之後所有引擎
       一律讀帳本、不再碰來源 —— 來源信箱永遠保持原狀 (不標已讀、不搬、不刪)。

 來源 (自動偵測, 逐級降級):
   1. 本機 Outlook (win32com)  -- 只讀收件匣, 依 ReceivedTime 篩選
   2. mail_inbox/ 資料夾        -- .eml / .txt / .json (半自動, 無 Outlook 也能跑)
   3. 內建範例                  -- 讓整條管線在乾淨機器上可立即驗證

 產出: data/mails.jsonl (add-only) — 每封信一列, 欄位:
   mail_uid(md5) / message_id / subject / sender / received / body /
   case(CASE-XX) / thread_key / source / attachments

 治理: 來源只讀; MD5 去重 (同一封信重跑不會產生第二列); 預設 dry-run。
============================================================================
"""
from __future__ import annotations

import os
import re
import sys
import json
import argparse
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vmt_core import (  # noqa: E402
    EngineResult, EventLog, Ledger, Workspace, add_common_args, banner, clip,
    esc, kpi_cards, md5_bytes, mode_label, norm_case, now_iso, pill,
    render_report, table, try_open,
)

ENGINE = "vmt_outlook_intake"
VERSION = "v1.0"

DAYS_BACK = int(os.environ.get("VMT_DAYS_BACK", "30"))
MAIL_EXT = {".eml", ".txt", ".json", ".msg"}


# ---------------------------------------------------------------- 正規化 ----


def thread_key(subject: str, case: str | None) -> str:
    """會話鍵: 去掉 RE:/FW: 前綴後的主旨 + 案號。回覆串才能歸到同一條追蹤。"""
    # 順序重要: 先去 emoji, RE: 前綴才會落在字首 (「🔴 RE: …」很常見)
    s = re.sub(r"[\U0001F300-\U0001FAFF]", "", str(subject or ""))
    for _ in range(3):                                     # RE: RE: FW: 連續前綴
        s2 = re.sub(r"^\s*(?:re|fw|fwd|回覆|轉寄)\s*[:：]\s*", "", s, flags=re.IGNORECASE)
        if s2 == s:
            break
        s = s2
    s = re.sub(r"\s*[-–]\s*\d{4}/\d{2}/\d{2}.*$", "", s)   # 去掉標題尾端時間戳
    return "%s|%s" % (case or "NOCASE", s.strip().lower())


def normalize_mail(raw: dict, source: str) -> dict:
    subject = str(raw.get("subject") or "").strip()
    body = str(raw.get("body") or "").strip()
    sender = str(raw.get("sender") or "").strip()
    received = str(raw.get("received") or now_iso())
    case = raw.get("case") or norm_case(subject) or norm_case(body)
    uid = md5_bytes(("%s|%s|%s|%s" % (raw.get("message_id") or "", subject, sender, body))
                    .encode("utf-8"))
    return {
        "mail_uid": uid,
        "message_id": raw.get("message_id") or "",
        "subject": subject,
        "sender": sender,
        "sender_email": raw.get("sender_email") or "",
        "to": raw.get("to") or "",
        "received": received,
        "body": body,
        "case": case,
        "thread_key": thread_key(subject, case),
        "attachments": raw.get("attachments") or [],
        "source": source,
        "ingest_ts": now_iso(),
    }


# ---------------------------------------------------------------- 來源 ------


def source_outlook(days_back: int = DAYS_BACK) -> list[dict] | None:
    """本機 Outlook, 純讀取。任何一封信讀失敗都只跳過該封, 不中斷整批。"""
    try:
        import win32com.client  # type: ignore
    except Exception:
        return None
    try:
        ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        items = ns.GetDefaultFolder(6).Items          # 6 = olFolderInbox
        items.Sort("[ReceivedTime]", True)
        cutoff = dt.datetime.now() - dt.timedelta(days=days_back)
        try:
            items = items.Restrict("[ReceivedTime] >= '%s'"
                                   % cutoff.strftime("%m/%d/%Y %H:%M %p"))
        except Exception:
            pass
        out: list[dict] = []
        for m in items:
            try:
                if getattr(m, "Class", None) != 43:     # 43 = olMail
                    continue
                atts = []
                try:
                    atts = [a.FileName for a in m.Attachments]
                except Exception:
                    pass
                out.append({
                    "message_id": getattr(m, "EntryID", "") or "",
                    "subject": m.Subject or "",
                    "sender": getattr(m, "SenderName", "") or "",
                    "sender_email": getattr(m, "SenderEmailAddress", "") or "",
                    "to": getattr(m, "To", "") or "",
                    "received": str(getattr(m, "ReceivedTime", "") or ""),
                    "body": (m.Body or "")[:20000],
                    "attachments": atts,
                })
            except Exception:
                continue
        if not out:
            return None
        print("[來源] 本機 Outlook: %d 封 (近 %d 天, 只讀)" % (len(out), days_back))
        return out
    except Exception as e:
        print("[來源] Outlook 略過:", e)
        return None


def _parse_eml(data: bytes) -> dict:
    from email import policy
    from email.parser import BytesParser
    from email.utils import parseaddr

    msg = BytesParser(policy=policy.default).parsebytes(data)
    body = ""
    try:
        part = msg.get_body(preferencelist=("plain", "html"))
        body = part.get_content() if part else ""
    except Exception:
        body = str(msg.get_payload())
    name, addr = parseaddr(msg.get("From", ""))
    return {
        "message_id": msg.get("Message-ID", "") or "",
        "subject": msg.get("Subject", "") or "",
        "sender": name or addr,
        "sender_email": addr,
        "to": msg.get("To", "") or "",
        "received": msg.get("Date", "") or "",
        "body": re.sub(r"<[^>]+>", " ", body or "")[:20000],
        "attachments": [p.get_filename() for p in msg.iter_attachments()
                        if p.get_filename()] if hasattr(msg, "iter_attachments") else [],
    }


def source_folder(inbox: Path) -> list[dict] | None:
    """mail_inbox/ — 沒有 Outlook 的機器 (或 Mac/Linux) 走這條。"""
    if not inbox.is_dir():
        return None
    out: list[dict] = []
    for fn in sorted(os.listdir(inbox)):
        p = inbox / fn
        if not p.is_file() or p.suffix.lower() not in MAIL_EXT:
            continue
        try:
            if p.suffix.lower() == ".json":
                payload = json.loads(p.read_text(encoding="utf-8"))
                out.extend(payload if isinstance(payload, list) else [payload])
            elif p.suffix.lower() == ".eml":
                out.append(_parse_eml(p.read_bytes()))
            else:
                text = p.read_text(encoding="utf-8", errors="replace")
                first, _, rest = text.partition("\n")
                out.append({"subject": first.strip(), "body": rest.strip(),
                            "sender": "FOLDER", "message_id": p.name})
        except Exception as e:
            print("[來源] 略過 %s: %s" % (fn, e))
    if not out:
        return None
    print("[來源] mail_inbox/: %d 封" % len(out))
    return out


def source_sample() -> list[dict]:
    """內建範例: 涵蓋請求 / 逾期升級 / 勾選回覆 / FYI 四種典型。"""
    print("[來源] 無真實信件 -> 使用內建範例")
    base = dt.datetime.now()
    return [
        {"message_id": "SMP-001", "subject": "[CASE-07] 請協助提供東莞線 8 月產能數字",
         "sender": "陳志豪", "sender_email": "chih.hao@example.com",
         "received": (base - dt.timedelta(days=2)).isoformat(timespec="seconds"),
         "body": "Hi，麻煩您在下週三前提供東莞線 8 月的產能數字與稼動率，"
                 "我們要放進月度營運報告。感謝協助。"},
        # 同一會話的催信 (真實的催辦幾乎都是在原信上回覆, 主旨帶 RE:)
        {"message_id": "SMP-002", "subject": "🔴 RE: [CASE-07] 請協助提供東莞線 8 月產能數字",
         "sender": "陳志豪", "sender_email": "chih.hao@example.com",
         "received": (base - dt.timedelta(hours=6)).isoformat(timespec="seconds"),
         "body": "此案已逾期，請盡快回覆，否則會影響月報結案時程。緊急。"},
        {"message_id": "SMP-003", "subject": "回覆：[CASE-03] BOM 位號與數量不符確認",
         "sender": "李美華", "sender_email": "mei.hua@example.com",
         "received": (base - dt.timedelta(days=1)).isoformat(timespec="seconds"),
         "body": "請選擇您的回覆（請勾選一項並直接回信）：\n"
                 "[ ] 1. 已完成（請附上資料）\n"
                 "[x] 2. 需要補資料（請說明缺漏項目）\n"
                 "[ ] 3. 需要澄清需求\n"
                 "[ ] 4. 需要延長時間\n"
                 "備註：東莞規格書缺 R100 的封裝資訊，已向供應商索取，預計 8/10 補齊。\n"
                 "確認：是\n"},
        {"message_id": "SMP-004", "subject": "FYI - 週會簡報已上傳共用資料夾",
         "sender": "王小明", "sender_email": "ming@example.com",
         "received": (base - dt.timedelta(days=3)).isoformat(timespec="seconds"),
         "body": "供參，無需回覆。簡報放在 \\\\share\\weekly\\2026W31。"},
    ]


# ---------------------------------------------------------------- 主流程 ----


def run(ws: Workspace, source: str = "auto", days_back: int = DAYS_BACK,
        commit: bool = False, no_open: bool = True) -> EngineResult:
    ws.ensure()
    ledger = Ledger(ws.mails_ledger, commit)
    events = EventLog(ws, commit)
    known = {r.get("mail_uid") for r in ledger.read()}

    raws, src_name = None, "sample"
    if source in ("auto", "outlook"):
        raws = source_outlook(days_back)
        src_name = "outlook" if raws else src_name
    if raws is None and source in ("auto", "folder"):
        raws = source_folder(ws.mail_inbox)
        src_name = "folder" if raws else src_name
    if raws is None:
        if source in ("auto", "sample"):
            raws, src_name = source_sample(), "sample"
        else:
            raws, src_name = [], source

    new_rows, dup = [], 0
    for raw in raws:
        rec = normalize_mail(raw, src_name)
        if rec["mail_uid"] in known:
            dup += 1
            continue
        known.add(rec["mail_uid"])
        ledger.append(rec)
        events.emit("MAIL_INGESTED", rec["mail_uid"],
                    "%s <- %s" % (clip(rec["subject"], 60), rec["sender"]),
                    case=rec["case"], thread=rec["thread_key"])
        new_rows.append(rec)

    print("[收信] 新增 %d 封 / 去重跳過 %d 封 (來源 %s)" % (len(new_rows), dup, src_name))
    report = _report(ws, new_rows, dup, src_name, commit)
    try_open(report, no_open)
    return EngineResult(engine=ENGINE, counts={"new": len(new_rows), "dedup": dup},
                        records=new_rows, report=str(report),
                        notes=["source=%s" % src_name])


def load_mails(ws: Workspace) -> list[dict]:
    """給下游引擎用: 讀出所有已入帳的郵件。"""
    return Ledger(ws.mails_ledger, False).read()


def _report(ws: Workspace, rows: list[dict], dup: int, src: str, commit: bool) -> Path:
    body = table(
        ["收件時間", "寄件者", "主旨", "案號", "附件"],
        [[esc(clip(r["received"], 19)), esc(r["sender"]), esc(clip(r["subject"], 60)),
          esc(r["case"] or "—"), esc(len(r["attachments"]) or "—")] for r in rows],
        "本次無新信 (可能全部已在帳本中, 冪等去重)")
    kpi = kpi_cards([("本次新增", len(rows), "#5a9e6f"),
                     ("去重跳過", dup, "#8a857c"),
                     ("帳本總量", len(load_mails(ws)) + (len(rows) if not commit else 0), "#4c78a8"),
                     ("來源", src, "#439a9a")])
    return render_report(
        ws.reports / "VMT_Intake.html", "收", "VMT 收信引擎 — 郵件入帳",
        "來源只讀 · MD5 去重 · add-only · %s" % mode_label(commit),
        "治理：來源信箱全程唯讀（不標已讀、不搬移、不刪除）；以內容 MD5 去重，"
        "同一封信重跑不會產生第二列；帳本 mails.jsonl 只 append。",
        [("KPI", kpi), ("本次入帳郵件", body)],
        "%s %s | 帳本: data/mails.jsonl" % (ENGINE, VERSION), commit)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT Outlook Intake Engine")
    add_common_args(ap)
    ap.add_argument("--source", default="auto", choices=["auto", "outlook", "folder", "sample"])
    ap.add_argument("--days-back", type=int, default=DAYS_BACK)
    a = ap.parse_args()
    banner("VMT · Outlook Intake Engine %s" % VERSION, mode_label(a.commit))
    ws = Workspace(a.root)
    days = a.days_back if a.days_back != DAYS_BACK else int(ws.load_config().get("days_back", DAYS_BACK))
    r = run(ws, a.source, days, a.commit, a.no_open)
    print("[輸出] 報告:", r.report)
    print("完成.")


if __name__ == "__main__":
    main()
