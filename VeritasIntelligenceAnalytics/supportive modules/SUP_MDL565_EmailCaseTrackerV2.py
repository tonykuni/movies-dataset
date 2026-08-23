# -*- coding: utf-8 -*-
"""
Email Case Tracker v2.0 — Stakeholder DB + PMBOK Control Sheet + Process Mining Event Log
=========================================================================================
建立在 v1(email_case_tracker.py,需同資料夾)之上,append-only 擴充,不修改 v1。

新增三大能力:
  A. Stakeholder Database(SQLite, append-only 三表:S01/S02/S03)
  B. PMBOK Control Sheet(xlsx 六表:ControlSheet / StakeholderRegister /
     RACI / IssueLog / RiskRegister / ChangeLog)
  C. Process Mining Event Log 匯出(pm4py 相容 CSV:case_id, activity,
     timestamp, resource)+ 每人回覆延遲與承諾兌現統計

用法:
  pip install pandas openpyxl python-docx
  python email_case_tracker_v2.py --input ./mail_export --start 2026-04-01 --end 2026-07-11
輸出:
  stakeholder.db / PMBOK_Control_Sheet.xlsx / event_log.csv
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from email_case_tracker import (ingest, normalize, classify_text,
                                    infer_status, extract_deadlines)
except ImportError:
    print("[FATAL] 找不到 email_case_tracker.py(v1),請與本檔置於同一資料夾。",
          file=sys.stderr)
    sys.exit(1)

# ============================================================
# Activity 分類(process mining 用)— 規則式,可稽核,append-only
# ============================================================
ACTIVITY_RULES = [
    ("Escalation", [r"escalat", r"升級", r"urgent", r"management\s+attention"]),
    ("Reminder",   [r"reminder", r"follow\s*up", r"gentle\s+reminder", r"催", r"再次提醒", r"still\s+waiting"]),
    ("Delivery",   [r"attached", r"please\s+find", r"as\s+requested", r"提供如附", r"檢附", r"deliver"]),
    ("Commitment", [r"will\s+provide", r"we\s+commit", r"by\s+\d", r"承諾", r"預計.*提供", r"deadline"]),
    ("Request",    [r"please\s+(provide|send|share|confirm)", r"could\s+you", r"請提供", r"請協助", r"需要"]),
    ("Response",   [r"^\s*(re|回覆)[::]", r"in\s+response", r"回覆如下", r"as\s+below"]),
]
DEFAULT_ACTIVITY = "Correspondence"

EMAIL_ADDR = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def classify_activity(subject: str, body: str) -> str:
    text = f"{subject}\n{body[:2000]}"
    for act, patterns in ACTIVITY_RULES:
        for p in patterns:
            if re.search(p, text, re.IGNORECASE | re.MULTILINE):
                return act
    return DEFAULT_ACTIVITY


def norm_person(raw: str) -> str:
    """從 'Name <a@b.com>' 取 email 作自然鍵;無 email 則取整串小寫。"""
    m = EMAIL_ADDR.search(raw or "")
    return m.group(0).lower() if m else (raw or "").strip().lower()


def display_name(raw: str) -> str:
    name = re.sub(r"<[^>]*>", "", raw or "").strip().strip('"')
    return name or norm_person(raw)


# ============================================================
# A. Stakeholder Database(SQLite, append-only)
# ============================================================
DDL = """
CREATE TABLE IF NOT EXISTS S01_STAKEHOLDER(
    sk_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT UNIQUE NOT NULL,          -- 自然鍵
    name       TEXT,
    org_guess  TEXT,                          -- 由 domain 推測
    first_seen TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS S02_INTERACTION(  -- 事件流:永不 UPDATE/DELETE
    ev_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id    TEXT NOT NULL,
    activity   TEXT NOT NULL,
    ts         TEXT,
    resource   TEXT NOT NULL,                 -- sender email(natural key)
    to_list    TEXT,
    subject    TEXT,
    source     TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS S03_ASSESSMENT(   -- PMBOK 評估快照:新評估=新增列
    as_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    sk_email   TEXT NOT NULL,
    power      TEXT,                          -- High/Low
    interest   TEXT,                          -- High/Low
    engagement_current TEXT,                  -- Unaware/Resistant/Neutral/Supportive/Leading
    engagement_desired TEXT,
    strategy   TEXT,
    assessed_at TEXT DEFAULT (datetime('now')),
    assessed_by TEXT DEFAULT 'auto-v2'
);
CREATE VIEW IF NOT EXISTS V_LATEST_ASSESSMENT AS
    SELECT * FROM S03_ASSESSMENT a
    WHERE as_id = (SELECT MAX(as_id) FROM S03_ASSESSMENT b
                   WHERE b.sk_email = a.sk_email);
"""


def build_stakeholder_db(threads, db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)
    cur = conn.cursor()
    case_no = 0
    for subj, msgs in threads.items():
        case_no += 1
        cid = f"CASE-{case_no:04d}"
        for m in msgs:
            sender = norm_person(m["sender"])
            if not sender:
                continue
            org = sender.split("@")[-1] if "@" in sender else ""
            ts = m["parsed_date"].isoformat() if m["parsed_date"] else None
            cur.execute(
                "INSERT OR IGNORE INTO S01_STAKEHOLDER(email,name,org_guess,first_seen)"
                " VALUES(?,?,?,?)",
                (sender, display_name(m["sender"]), org, ts))
            cur.execute(
                "INSERT INTO S02_INTERACTION"
                "(case_id,activity,ts,resource,to_list,subject,source)"
                " VALUES(?,?,?,?,?,?,?)",
                (cid, classify_activity(m["subject"], m["body"]), ts, sender,
                 m.get("to", ""), m["subject"], m["source"]))
    conn.commit()
    return conn


# ============================================================
# 每人統計(data mining):回覆延遲 + 承諾兌現率初值
# ============================================================
def stakeholder_metrics(conn):
    df = pd.read_sql_query(
        "SELECT case_id, activity, ts, resource FROM S02_INTERACTION"
        " WHERE ts IS NOT NULL ORDER BY case_id, ts", conn)
    if df.empty:
        return pd.DataFrame()
    df["ts"] = pd.to_datetime(df["ts"])
    rows = []
    for person, _ in df.groupby("resource"):
        # 回覆延遲:別人發出 Request/Reminder 後,此人下一封信的間隔
        latencies, commits, deliveries = [], 0, 0
        for _, cdf in df.groupby("case_id"):
            cdf = cdf.reset_index(drop=True)
            for i, r in cdf.iterrows():
                if r["resource"] == person:
                    if r["activity"] == "Commitment":
                        commits += 1
                    if r["activity"] == "Delivery":
                        deliveries += 1
                    continue
                if r["activity"] in ("Request", "Reminder"):
                    nxt = cdf.iloc[i + 1:]
                    hit = nxt[nxt["resource"] == person]
                    if not hit.empty:
                        latencies.append(
                            (hit.iloc[0]["ts"] - r["ts"]).total_seconds() / 3600)
        rows.append({
            "人員": person,
            "事件數": int((df["resource"] == person).sum()),
            "平均回覆延遲(小時)": round(sum(latencies) / len(latencies), 1) if latencies else None,
            "被催後回覆樣本數": len(latencies),
            "Commitment次數": commits,
            "Delivery次數": deliveries,
            "初步兌現率": round(deliveries / commits, 2) if commits else None,
        })
    return pd.DataFrame(rows).sort_values("事件數", ascending=False)


def auto_assess(conn, metrics: pd.DataFrame):
    """依互動量與回覆行為給 Power/Interest/Engagement 初評(人工可覆寫=新增列)。"""
    cur = conn.cursor()
    if metrics.empty:
        return
    q75 = metrics["事件數"].quantile(0.75)
    for _, r in metrics.iterrows():
        interest = "High" if r["事件數"] >= q75 else "Low"
        lat = r["平均回覆延遲(小時)"]
        engagement = ("Resistant" if (lat is not None and lat > 96)
                      else "Neutral" if (lat is None or lat > 48)
                      else "Supportive")
        cur.execute(
            "INSERT INTO S03_ASSESSMENT"
            "(sk_email,power,interest,engagement_current,engagement_desired,strategy)"
            " VALUES(?,?,?,?,?,?)",
            (r["人員"], "TBD-manual", interest, engagement, "Supportive",
             "回覆延遲>48h 者納入 48 小時升級規則書面追蹤"))
    conn.commit()


# ============================================================
# B. PMBOK Control Sheet(六表 xlsx)
# ============================================================
def build_control_sheet(threads, metrics, conn, out_path: Path):
    control, raci, issues, risks = [], [], [], []
    case_no = 0
    now = datetime.now()
    for subj, msgs in sorted(threads.items(),
                             key=lambda kv: kv[1][-1]["parsed_date"] or datetime.min,
                             reverse=True):
        case_no += 1
        cid = f"CASE-{case_no:04d}"
        full = " ".join(m["subject"] + " " + m["body"] for m in msgs)
        cats = "; ".join(dict.fromkeys(c for c, _ in classify_text(full))) or "Uncategorized"
        first, last = msgs[0]["parsed_date"], msgs[-1]["parsed_date"]
        status = infer_status(msgs[-1]["subject"] + " " + msgs[-1]["body"], last)
        promised = extract_deadlines(full)
        stale_days = (now - last).days if last else None
        escalate = bool(status in ("Blocked", "Overdue") or
                        (stale_days is not None and stale_days > 2))
        senders = [norm_person(m["sender"]) for m in msgs if norm_person(m["sender"])]
        responsible = max(set(senders), key=senders.count) if senders else ""
        control.append({
            "Case ID": cid, "WBS Ref": "", "分類": cats,
            "案件主旨": msgs[0]["norm_subject"],
            "R(Responsible)": responsible, "A(Accountable)": "",
            "基準日(Baseline)": "", "承諾日(Promised)": promised,
            "最後往來": last.strftime("%Y-%m-%d") if last else "",
            "無回應天數": stale_days, "狀態": status,
            "48h升級旗標": "YES" if escalate else "",
            "下一步行動": "", "證據連結": "; ".join(
                dict.fromkeys(m["source"] for m in msgs))[:200],
        })
        for p in dict.fromkeys(senders):
            raci.append({"Case ID": cid, "人員": p,
                         "RACI": "R" if p == responsible else "C"})
        if status == "Blocked":
            issues.append({"Issue ID": f"ISS-{len(issues)+1:03d}", "Case ID": cid,
                           "描述": msgs[0]["norm_subject"], "根因": "", "Owner": responsible,
                           "提出日": last.strftime("%Y-%m-%d") if last else "",
                           "目標解決日": "", "狀態": "Open"})
        if escalate:
            risks.append({"Risk ID": f"RSK-{len(risks)+1:03d}", "Case ID": cid,
                          "風險描述": f"{cats} 交付停滯", "機率": "M", "衝擊": "H",
                          "觸發條件": "承諾日逾期或無回應>2工作日",
                          "應對": "書面升級主管/BU 並附影響評估"})

    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        pd.DataFrame(control).to_excel(w, "ControlSheet", index=False)
        reg = pd.read_sql_query(
            "SELECT s.email AS 人員, s.name AS 姓名, s.org_guess AS 組織, "
            "a.power AS Power, a.interest AS Interest, "
            "a.engagement_current AS 現況投入, a.engagement_desired AS 期望投入, "
            "a.strategy AS 溝通策略 "
            "FROM S01_STAKEHOLDER s LEFT JOIN V_LATEST_ASSESSMENT a "
            "ON a.sk_email = s.email", conn)
        if not metrics.empty:
            reg = reg.merge(metrics, left_on="人員", right_on="人員", how="left")
        reg.to_excel(w, "StakeholderRegister", index=False)
        pd.DataFrame(raci).to_excel(w, "RACI", index=False)
        pd.DataFrame(issues).to_excel(w, "IssueLog", index=False)
        pd.DataFrame(risks).to_excel(w, "RiskRegister", index=False)
        pd.DataFrame(columns=["Change ID", "Case ID", "日期", "變更內容",
                              "原值", "新值", "提出人", "核准人"]
                     ).to_excel(w, "ChangeLog", index=False)
    return len(control)


# ============================================================
# C. Process Mining Event Log 匯出(pm4py 相容)
# ============================================================
def export_event_log(conn, out_path: Path):
    df = pd.read_sql_query(
        "SELECT case_id AS 'case:concept:name', activity AS 'concept:name', "
        "ts AS 'time:timestamp', resource AS 'org:resource' "
        "FROM S02_INTERACTION WHERE ts IS NOT NULL ORDER BY case_id, ts", conn)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    # 附:activity 轉移矩陣(不裝 pm4py 也能看流程形狀)
    trans = {}
    for _, g in df.groupby("case:concept:name"):
        acts = g["concept:name"].tolist()
        for a, b in zip(acts, acts[1:]):
            trans[(a, b)] = trans.get((a, b), 0) + 1
    tm = pd.DataFrame([{"From": a, "To": b, "次數": n}
                       for (a, b), n in sorted(trans.items(),
                                               key=lambda x: -x[1])])
    tm.to_csv(out_path.with_name("activity_transitions.csv"),
              index=False, encoding="utf-8-sig")
    return len(df)


# ============================================================
# main
# ============================================================
def main():
    ap = argparse.ArgumentParser(description="Email Case Tracker v2 — PMBOK edition")
    ap.add_argument("--input", required=True)
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d") if args.start else None
    end = datetime.strptime(args.end, "%Y-%m-%d") if args.end else None
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    records = ingest(Path(args.input))
    print(f"[1/5] 讀入 {len(records)} 封郵件")
    threads = normalize(records, start, end)
    print(f"[2/5] 串接 {len(threads)} 個案件")

    conn = build_stakeholder_db(threads, outdir / "stakeholder.db")
    print("[3/5] Stakeholder DB 完成(S01/S02/S03)")

    metrics = stakeholder_metrics(conn)
    auto_assess(conn, metrics)
    n_cases = build_control_sheet(threads, metrics, conn,
                                  outdir / "PMBOK_Control_Sheet.xlsx")
    print(f"[4/5] PMBOK Control Sheet 完成({n_cases} 案件,六表)")

    n_events = export_event_log(conn, outdir / "event_log.csv")
    print(f"[5/5] Event log 匯出 {n_events} 筆(pm4py 相容)"
          f" + activity_transitions.csv")

    if not metrics.empty:
        print("\n=== Stakeholder 回應行為統計(前10)===")
        print(metrics.head(10).to_string(index=False))
    conn.close()


if __name__ == "__main__":
    main()
