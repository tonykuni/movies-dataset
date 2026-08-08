# -*- coding: utf-8 -*-
# WorkOps 決策追蹤模組 v0100(ENG-027)— 會議決議 → 行動 → 追蹤 的中控帳本
#
# 操作員 2026/08/08 研究裁可(YES):會議記錄流程「議題→討論→決議→行動項目」、
#   決策追蹤標準欄位(What/Who/When/交什麼)、Decision DB 為唯一真相來源。
# 去重裁定:儲存用 sqlite(平台標準,同 super_engine E 庫;不新增 duckdb 硬依賴,
#   匯出時 via_io 在場可加 parquet/duckdb);編號沿 PLM 鐵律 DEC-####(永不變);
#   source 欄可掛 THR-#/CASE-#(與既有帳本互鏈);append-only 歷史逐筆留痕。
# 動詞:add "決議" 負責人 截止 [來源] / list [狀態] / done|block|start DEC-#### [備註]
#   / report(KPI:完成率/逾期率/平均延遲天數)/ export(utf8BOM CSV,Excel 中文安全)
# 治理:不卡斷;誠實輸出;絕不代寄(本模組只記錄不寄信)。
import argparse
import csv
import io
import json
import sqlite3
import sys
from datetime import datetime, date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent          # engines/
OUT = HERE.parent / "out"
DB = OUT / "decision_log.db"
STATUSES = ("OPEN", "IN_PROGRESS", "DONE", "BLOCKED")


def conn():
    OUT.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS DECISIONS(
        decision_id TEXT PRIMARY KEY, meeting_id TEXT, what TEXT NOT NULL,
        owner TEXT NOT NULL, due TEXT, status TEXT NOT NULL DEFAULT 'OPEN',
        source TEXT, created_at TEXT, updated_at TEXT, done_at TEXT, note TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS HISTORY(
        h_id INTEGER PRIMARY KEY AUTOINCREMENT, decision_id TEXT, ts TEXT,
        action TEXT, value TEXT)""")
    return c


def now():
    return datetime.now().isoformat(timespec="seconds")


def next_id(c):
    row = c.execute("SELECT decision_id FROM DECISIONS ORDER BY decision_id DESC LIMIT 1").fetchone()
    n = int(row[0].split("-")[1]) + 1 if row else 1
    return "DEC-%04d" % n


def hist(c, did, action, value=""):
    c.execute("INSERT INTO HISTORY(decision_id, ts, action, value) VALUES(?,?,?,?)",
              (did, now(), action, value))


def cmd_add(what, owner, due, source, meeting):
    if not what or not owner:
        print('[FAIL] add 需要:decisions add "決議內容" 負責人 [截止 yyyy-mm-dd] [來源如 THR-00012] [會議代碼]')
        return 1
    c = conn()
    did = next_id(c)
    c.execute("INSERT INTO DECISIONS(decision_id, meeting_id, what, owner, due, status,"
              " source, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
              (did, meeting or "", what, owner, due or "", "OPEN", source or "", now(), now()))
    hist(c, did, "ADD", "%s @%s due=%s" % (what[:60], owner, due or "-"))
    c.commit(); c.close()
    print("[新增] %s · %s · 負責人 %s · 截止 %s%s" %
          (did, what[:50], owner, due or "未定", (" · 來源 " + source) if source else ""))
    return 0


def _late_days(due, done_at=None):
    if not due:
        return 0
    try:
        d = date.fromisoformat(due[:10])
        ref = date.fromisoformat(done_at[:10]) if done_at else date.today()
        return max(0, (ref - d).days)
    except Exception:
        return 0


def cmd_list(status):
    c = conn()
    q = "SELECT decision_id, what, owner, due, status, source, note FROM DECISIONS"
    args = ()
    if status:
        q += " WHERE status=?"; args = (status.upper(),)
    q += " ORDER BY decision_id"
    rows = c.execute(q, args).fetchall()
    c.close()
    if not rows:
        print("[空] 無決議 — decisions add 開始記錄")
        return 0
    mark = {"OPEN": "○", "IN_PROGRESS": "◐", "DONE": "✔", "BLOCKED": "✖"}
    for did, what, owner, due, st, src, note in rows:
        late = _late_days(due) if st not in ("DONE",) else 0
        tail = (" · 逾期 %d 天" % late) if late else ""
        tail += (" · " + src) if src else ""
        tail += (" · " + note) if note else ""
        print("%s %s · %s · @%s · 截止 %s%s" % (mark.get(st, "?"), did, what[:60], owner, due or "-", tail))
    return 0


def cmd_status(did, new_status, note):
    c = conn()
    row = c.execute("SELECT status FROM DECISIONS WHERE decision_id=?", (did,)).fetchone()
    if not row:
        print("[FAIL] 查無 %s(decisions list 看現況)" % did)
        return 1
    done_at = now() if new_status == "DONE" else None
    c.execute("UPDATE DECISIONS SET status=?, updated_at=?, done_at=COALESCE(?, done_at),"
              " note=CASE WHEN ?<>'' THEN ? ELSE note END WHERE decision_id=?",
              (new_status, now(), done_at, note or "", note or "", did))
    hist(c, did, new_status, note or "")
    c.commit(); c.close()
    print("[%s] %s%s" % (new_status, did, (" · " + note) if note else ""))
    return 0


def cmd_report():
    c = conn()
    rows = c.execute("SELECT decision_id, due, status, done_at FROM DECISIONS").fetchall()
    c.close()
    if not rows:
        print("[空] 無資料")
        return 0
    total = len(rows)
    done = sum(1 for _, _, st, _ in rows if st == "DONE")
    blocked = sum(1 for _, _, st, _ in rows if st == "BLOCKED")
    open_late = [(_late_days(due)) for _, due, st, _ in rows if st not in ("DONE",) and _late_days(due) > 0]
    done_delays = [_late_days(due, da) for _, due, st, da in rows if st == "DONE" and due]
    print("========== 決策落地 KPI ==========")
    print("決議總數 %d · 完成率 %.0f%% · 卡住 %d" % (total, 100.0 * done / total, blocked))
    print("未結逾期 %d 件(最長 %d 天)" % (len(open_late), max(open_late) if open_late else 0))
    if done_delays:
        print("已完成平均延遲 %.1f 天(0=準時)" % (sum(done_delays) / len(done_delays)))
    print("(門檻參考:完成率>80%、逾期率<10% — 低於即列會議檢視)")
    return 0


def cmd_export():
    c = conn()
    rows = c.execute("SELECT decision_id, meeting_id, what, owner, due, status, source,"
                     " created_at, updated_at, done_at, note FROM DECISIONS ORDER BY decision_id").fetchall()
    c.close()
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "decision_log.csv"
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Decision ID", "Meeting ID", "決議內容", "負責人", "截止日", "狀態",
                    "來源(THR/CASE)", "建立", "更新", "完成", "備註/障礙"])
        for r in rows:
            w.writerow(r)
    print("[匯出] %d 筆 → %s(utf8BOM,Excel 中文安全)" % (len(rows), p))
    return 0


def main():
    ap = argparse.ArgumentParser(description="WorkOps 決策追蹤:決議→行動→KPI(編號 DEC-#### 永不變)")
    ap.add_argument("command", nargs="?", default="list",
                    choices=["add", "list", "start", "done", "block", "report", "export"])
    ap.add_argument("a1", nargs="?", default="")
    ap.add_argument("a2", nargs="?", default="")
    ap.add_argument("a3", nargs="?", default="")
    ap.add_argument("a4", nargs="?", default="")
    ap.add_argument("a5", nargs="?", default="")
    a = ap.parse_args()
    if a.command == "add":
        return cmd_add(a.a1, a.a2, a.a3, a.a4, a.a5)
    if a.command == "list":
        return cmd_list(a.a1)
    if a.command in ("start", "done", "block"):
        st = {"start": "IN_PROGRESS", "done": "DONE", "block": "BLOCKED"}[a.command]
        return cmd_status(a.a1, st, a.a2)
    if a.command == "report":
        return cmd_report()
    return cmd_export()


if __name__ == "__main__":
    sys.exit(main())
