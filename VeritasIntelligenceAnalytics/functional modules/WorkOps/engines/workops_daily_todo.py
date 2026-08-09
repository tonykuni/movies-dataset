# -*- coding: utf-8 -*-
r"""Veritas WorkOps 每日 TO-DO 引擎 v0100(ENG-046)— 同類工作一口氣,三時間錨

操作員令(2026/08/10):每日 TO-DO LIST,一口氣做相同工作 —
  [前日 16:00] 陸續寄出追蹤信(系統建草稿批;寄出人按 — 絕不代寄)
  [今日 11:00] 開始追蹤收件(回覆判讀批)
  [今日 16:00 前] 緊急追蹤未收到者(急件批)
  另掃可新增項(確認/結案/決策/里程碑批);每件追蹤附 AI 代筆提示
  (ai_prompt_templates.json 填真實案件資料 → 貼給 Copilot/任何 AI 產信文 → 人寄)。
時間錨全在 watchtower_params.json daily_rhythm(可改);全唯讀彙整,零寫入正本。
產物:out/daily_todo.json + out/daily_prompts.txt(逐件可貼提示)。
動詞:build(預設)。via-workops todo。
"""
import csv, io, json, sys
from datetime import datetime, date
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


def fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace("{{%s}}" % k, str(v))
    return tpl


def build():
    wt = jload(HERE / "watchtower_params.json", {})
    ry = wt.get("daily_rhythm", {}) or {}
    t_gen = ry.get("generate_drafts_time", "16:00")
    t_chk = ry.get("reply_check_time", "11:00")
    t_urg = ry.get("urgent_chase_before", "16:00")
    tpls = jload(HERE / "ai_prompt_templates.json", {}).get("templates", {})
    pend = rows(OUT / "pending.csv")
    rs = jload(OUT / "reply_status.json", {})
    status = rs.get("status", {})
    flags = rs.get("flags", {})
    reg = jload(OUT / "wop_registry.json", {}).get("projects", {}) or {}
    thr2label = {}
    for wid, pr in reg.items():
        for t in pr.get("thr", []):
            thr2label[t] = (wid, pr.get("label", ""))
    t1 = int(wt.get("t1_days", 3))
    t3 = int(wt.get("t3_days", 7))
    prompts = []

    # A[前日 16:00 寄出批] 達 T1 門檻未回 → 建草稿+AI 代筆提示
    batch_send = []
    for p in pend:
        thr = p.get("ThrID", "")
        if flags.get(thr, {}).get("ooo"):
            continue
        try:
            wd = int(p.get("WaitingDays") or 0)
        except ValueError:
            wd = 0
        risky = bool(flags.get(thr, {}).get("risk"))
        if t1 <= wd < t3 and not risky and thr not in status:   # 急件(≥t3/⚡)只進急件批 — 批次互斥
            wid, label = thr2label.get(thr, ("", ""))
            batch_send.append({"thr": thr, "subject": p.get("Subject", ""), "days": wd, "wop": wid, "label": label})
            if "followup_write" in tpls:
                prompts.append("### %s(%s · 等 %d 天)追蹤信 AI 代筆\n%s" % (thr, p.get("Subject", "")[:40], wd,
                    fill(tpls["followup_write"], 語言="繁體中文", 對口=p.get("SenderEmail", p.get("To", "對口")),
                         案名=label or p.get("Subject", ""), 案號=wid or thr, 寄出日=p.get("SentOn", ""),
                         主旨=p.get("Subject", ""), 天數=wd)))

    # C[今日 16:00 前 急件批] 達 T3 或 ⚡風險 → 緊急追蹤
    batch_urgent = []
    for p in pend:
        thr = p.get("ThrID", "")
        if flags.get(thr, {}).get("ooo") or thr in status:
            continue
        try:
            wd = int(p.get("WaitingDays") or 0)
        except ValueError:
            wd = 0
        risky = bool(flags.get(thr, {}).get("risk"))
        if wd >= t3 or risky:
            wid, label = thr2label.get(thr, ("", ""))
            batch_urgent.append({"thr": thr, "subject": p.get("Subject", ""), "days": wd, "risk": risky})
            if "urgent_write" in tpls:
                prompts.append("### %s(%s)緊急追蹤 AI 代筆%s\n%s" % (thr, p.get("Subject", "")[:40],
                    "(⚡風險)" if risky else "",
                    fill(tpls["urgent_write"], 語言="繁體中文", 對口=p.get("SenderEmail", "對口"),
                         案名=label or p.get("Subject", ""), 案號=wid or thr, 次數=3, 天數=wd,
                         影響="專案時程與對外承諾")))

    # B[今日 11:00 收件批] 已判讀回覆 → 核對;未解析 → 人工掃一眼
    replied = [{"thr": t, "status": v.get("status", ""), "date": v.get("mail_date", "")} for t, v in status.items()]
    un = (rs.get("unparsed") or {}).get("n", 0)

    # D-F 可新增項批
    ask = jload(OUT / "wop_ask.json", {})
    nm = jload(OUT / "workops_naming.json", {}).get("entries", {}) or {}
    n_nm = sum(1 for v in nm.values() if isinstance(v, dict) and not v.get("approved"))
    cls_c = jload(OUT / "closure_candidates.json", {}).get("candidates", [])
    dec_open = [r for r in rows(OUT / "decision_log.csv") if (r.get("狀態") or "") != "DONE"]
    ms = jload(OUT / "milestones.json", {}).get("items", {})
    today = date.today().isoformat()
    ms_late = [m for m, it in ms.items() if it["status"] == "OPEN" and it.get("due", "9999") < today]

    todo = {"ts": datetime.now().isoformat(timespec="seconds"),
            "rhythm": {"send": t_gen + "(前一日)", "check": t_chk, "urgent_before": t_urg},
            "batches": [
                {"anchor": "前日 %s" % t_gen, "batch": "追蹤信寄出批(建草稿→AI 代筆→人按寄出)", "n": len(batch_send), "items": batch_send,
                 "cmd": "via-workops drafts " + ",".join(x["thr"] for x in batch_send[:20]) if batch_send else ""},
                {"anchor": "今日 %s" % t_chk, "batch": "收件判讀批(已回 %d 串核對;未解析 %s 件掃一眼)" % (len(replied), un),
                 "n": len(replied), "items": replied[:20], "cmd": "via-workops replies"},
                {"anchor": "今日 %s 前" % t_urg, "batch": "緊急追蹤批(未收到者;⚡優先)", "n": len(batch_urgent), "items": batch_urgent,
                 "cmd": "via-workops drafts " + ",".join(x["thr"] for x in batch_urgent[:20]) + " urgent_escalation" if batch_urgent else ""},
                {"anchor": "全日", "batch": "確認批:歸戶 ASK %s · 命名待核 %d" % (ask.get("n_ask", 0), n_nm),
                 "n": (ask.get("n_ask", 0) or 0) + n_nm, "cmd": "板 04 確認中心"},
                {"anchor": "全日", "batch": "結案批:候選 %d 件(confirm 顯式)" % len(cls_c), "n": len(cls_c), "cmd": "via-workops closure"},
                {"anchor": "全日", "batch": "決策/里程碑批:未結決議 %d · 逾期里程碑 %d" % (len(dec_open), len(ms_late)),
                 "n": len(dec_open) + len(ms_late), "cmd": "via-workops decisions list / milestones list"},
            ]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "daily_todo.json").write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding="utf-8")
    ptxt = "═══ AI 代筆提示(逐件複製 → 貼給 Copilot/任何 AI → 產信文 → 貼回草稿 → 人按寄出)═══\n\n" + \
           ("\n\n".join(prompts) if prompts else "(今日無追蹤件需代筆)")
    if "todo_digest" in tpls:
        ptxt += "\n\n### 整份 TO-DO 請 AI 排版\n" + fill(tpls["todo_digest"], 語言="繁體中文",
                                                        TODO_JSON=json.dumps(todo, ensure_ascii=False))
    (OUT / "daily_prompts.txt").write_text(ptxt, encoding="utf-8")
    print("========== 每日 TO-DO(同類一口氣;時間錨 %s/%s/%s)==========" % (t_gen, t_chk, t_urg))
    for b in todo["batches"]:
        mark = "✓" if b["n"] == 0 else str(b["n"])
        print("  [%s] %-14s %s" % (mark, b["anchor"], b["batch"]))
        if b.get("cmd") and b["n"]:
            print("        → %s" % b["cmd"])
    print("[產物] out/daily_todo.json + out/daily_prompts.txt(%d 件 AI 代筆提示)" % len(prompts))
    print("[紅線] 系統只建草稿與提示;寄出永遠由您按")
    return 0


if __name__ == "__main__":
    sys.exit(build())
