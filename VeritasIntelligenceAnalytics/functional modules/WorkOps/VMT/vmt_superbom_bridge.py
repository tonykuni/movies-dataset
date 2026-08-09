# -*- coding: utf-8 -*-
"""
============================================================================
 VMT x SuperBOM  Quarantine Bridge  v1.0   --  雙向閉環接縫
----------------------------------------------------------------------------
 接縫定位: 兩個 SSOT 不合併, 只在此對接.
   OUT (SuperBOM -> VMT):  讀 Q01_QUARANTINE 未解列 -> 在 VMT ssot.json 開
        追蹤 issue (ISS-####, 帶 sbom_q_uid 交叉參照) -> 產下拉追蹤信.
        壞列 (REF_QTY_MISMATCH = 10K->10000 類錯) 自動變成要人澄清的案件.
   IN  (VMT -> SuperBOM):  VMT issue 因回覆而 DONE -> 在 G01_LEDGER append
        一筆 QUARANTINE_RESOLVED 事件 (add-only), 連回 q_uid.
        開放隔離狀態由 ledger 推導 (V_QUARANTINE_OPEN), 永不 UPDATE Q01.
----------------------------------------------------------------------------
 治理紅線 (硬性):
   - SuperBOM canonical M01/M02/M03/R* : 完全不碰
   - Q01_QUARANTINE                    : 只讀, 永不 UPDATE/DELETE
   - G01_LEDGER                        : 只 append (該表本就是事件帳), 且需 --commit
   - VMT ssot.json                     : 只增 issue + 讀狀態 (只增不減)
   - 預設 propose/dry-run: 不寫 canonical DB, 只輸出計畫供審閱; --commit 才 append
   - 冪等: q_uid 已有對應 issue 不重開; q_uid 已有 RESOLVED 事件不重記
 相容: Python 3.11+, duckdb. VMT ssot.json 由 VeritasMailTracker_v1.ps1 產生.
============================================================================
"""
import os, re, sys, json, argparse, datetime as dt

try:
    import duckdb
except Exception:
    print("需要 duckdb:  pip install duckdb"); sys.exit(1)

# ---------------------------------------------------------------- 設定 ------
VMT_ROOT   = os.environ.get("VMT_ROOT", r"C:\VIA\VeritasMailTracker")
SSOT_PATH  = os.path.join(VMT_ROOT, "data", "ssot.json")
EVENT_PATH = os.path.join(VMT_ROOT, "data", "events.jsonl")
OUT_DIR    = os.path.join(VMT_ROOT, "reports")
MAIL_ROOT  = os.path.join(VMT_ROOT, "mails")

# reason_code -> (VMT 標題前綴, 緊急度 1-5, 郵件類型, 建議負責方 hint)
REASON_MAP = {
    "REF_QTY_MISMATCH": ("數量/位號不符 (疑 10K→10000 類錯)", 5, "Warning",  "來源窗口"),
    "HALLUCINATION":    ("疑似 AI 幻覺資料需人工核對",        5, "Warning",  "來源窗口"),
    "REF_QTY":          ("位號與數量不一致",                  5, "Warning",  "來源窗口"),
    "LOW_CONFIDENCE":   ("低信心資料待確認",                  4, "Reminder", "來源窗口"),
    "AMBIGUOUS":        ("資料語意模糊待澄清",                4, "Reminder", "來源窗口"),
    "UNKNOWN_TYPE":     ("無法辨識類別待歸類",                4, "Reminder", "來源窗口"),
    "ENCODING":         ("編碼異常需重送檔案",                3, "FollowUp", "來源窗口"),
}
DEFAULT_REASON = ("隔離資料待處理", 4, "Reminder", "來源窗口")
# SuperBOM 資料品質專用 VMT 案號 (add-only 加入 cases, 不佔用 01-14 業務案)
SBOM_CASE_ID    = os.environ.get("VMT_SBOM_CASE", "CASE-90")
SBOM_CASE_NAME  = "SuperBOM 資料品質"

def now_iso():  return dt.datetime.now().isoformat()

# ---------------------------------------------- VMT SSOT ---------------------
def load_ssot():
    if not os.path.exists(SSOT_PATH):
        print("[VMT] 找不到 ssot.json (%s) -- 請先跑 VeritasMailTracker_v1.ps1" % SSOT_PATH)
        return None
    ss = json.load(open(SSOT_PATH, encoding="utf-8"))
    ss.setdefault("counters", {}).setdefault("issue", 0)
    ss["counters"].setdefault("mail", 0)
    ss.setdefault("issues", [])
    ss.setdefault("cases", [])
    return ss

def save_ssot(ss):
    tmp = SSOT_PATH + ".tmp"
    json.dump(ss, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp, SSOT_PATH)

def append_vmt_event(evt, ref, detail):
    line = json.dumps({"ts": now_iso(), "event": evt, "ref": ref, "detail": detail}, ensure_ascii=False)
    with open(EVENT_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def ensure_sbom_case(ss):
    if not any(c.get("id") == SBOM_CASE_ID for c in ss["cases"]):
        ss["cases"].append({"id": SBOM_CASE_ID, "name": SBOM_CASE_NAME, "status": "ACTIVE"})

def new_ids(ss):
    ss["counters"]["issue"] = int(ss["counters"]["issue"]) + 1
    ss["counters"]["mail"]  = int(ss["counters"]["mail"]) + 1
    return ("ISS-%04d" % ss["counters"]["issue"], "MAIL-%04d" % ss["counters"]["mail"])

def existing_qref(ss):
    """已建立過的 q_uid -> issueId, 供冪等去重"""
    m = {}
    for i in ss["issues"]:
        q = i.get("sbom_q_uid")
        if q:
            m[q] = i["issueId"]
    return m

# ---------------------------------------------- 郵件產生 (與 v1 相容) --------
URG_EMOJI = {5: "\U0001F534", 4: "\U0001F7E0", 3: "\U0001F7E1", 2: "\U0001F7E2", 1: "\U0001F7E9"}
LIMITED_SELECTION = (
    "請選擇您的回覆（請勾選一項並直接回信）：\n"
    "[ ] 1. 已完成（請附上資料）\n"
    "[ ] 2. 需要補資料（請說明缺漏項目）\n"
    "[ ] 3. 需要澄清需求（請說明哪裡不清楚）\n"
    "[ ] 4. 需要延長時間（請提供原因＋新的 ETA）\n"
    "備註：______（選填，會一併記錄供專案組檢視）\n"
    "確認：是/否\n"
)

def make_mail(issue, q_reason, q_raw):
    stamp = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    subj = "%s [%s] – %s – %s" % (URG_EMOJI[issue["urgency"]], issue["caseId"], issue["title"], stamp)
    body = (
        "Dear all，\n辛苦了，感謝您的協助。\n\n"
        "系統在 SuperBOM 資料載入時，將以下項目隔離，需請您協助確認，以免影響後續 BOM 正確性。\n\n"
        "【專案】%s\n【問題】%s\n【追蹤編號】%s\n【隔離原因】%s\n【原始資料摘要】%s\n\n%s\n"
        "再次感謝您的協助。\nBest regards\n（CC：管理團隊＋所有相關人）\n"
        % (issue["caseId"], issue["title"], issue["issueId"], q_reason, q_raw[:200], LIMITED_SELECTION)
    )
    return subj, "主旨：%s\n%s\n%s" % (subj, "-" * 60, body)

# ---------------------------------------------- OUT: Q01 -> VMT --------------
def read_open_quarantine(con):
    """讀未解隔離列: resolved=FALSE 且 G01 尚無 QUARANTINE_RESOLVED 事件 (雙保險)"""
    rows = con.execute("""
        SELECT q.q_uid, q.src_system, q.ingest_batch, q.reason_code,
               CAST(q.raw_json AS VARCHAR) AS raw, q.confidence
        FROM sbom.Q01_QUARANTINE q
        WHERE q.resolved = FALSE
          AND NOT EXISTS (
              SELECT 1 FROM sbom.G01_LEDGER g
              WHERE g.action = 'QUARANTINE_RESOLVED' AND g.target_uid = q.q_uid)
        ORDER BY q.intake_ts
    """).fetchall()
    cols = ["q_uid", "src", "batch", "reason", "raw", "conf"]
    return [dict(zip(cols, r)) for r in rows]

def bridge_out(con, ss, mk_mail_dir):
    ensure_sbom_case(ss)
    qref = existing_qref(ss)
    opened = []
    for q in read_open_quarantine(con):
        if q["q_uid"] in qref:
            continue  # 冪等: 此 q_uid 已有 issue
        title_suffix, urg, mtype, owner_hint = REASON_MAP.get(q["reason"], DEFAULT_REASON)
        title = "%s〔%s〕" % (title_suffix, q["src"] or "SOURCE")
        iss_id, mail_id = new_ids(ss)
        issue = {
            "issueId": iss_id, "mailId": mail_id, "caseId": SBOM_CASE_ID,
            "title": title, "urgency": urg, "type": mtype,
            "owner": owner_hint, "due": "", "status": "OPEN",
            "created": now_iso(),
            "sbom_q_uid": q["q_uid"], "sbom_reason": q["reason"],
            "sbom_src": q["src"], "sbom_batch": q["batch"],
        }
        ss["issues"].append(issue)
        subj, full = make_mail(issue, q["reason"], q["raw"])
        if mk_mail_dir:
            os.makedirs(mk_mail_dir, exist_ok=True)
            fp = os.path.join(mk_mail_dir, "%s_%s_%s.txt" % (mail_id, SBOM_CASE_ID, mtype))
            open(fp, "w", encoding="utf-8").write(full)
        append_vmt_event("SBOM_QUARANTINE_LINK", iss_id,
                         "q_uid=%s reason=%s src=%s -> %s" % (q["q_uid"][:8], q["reason"], q["src"], iss_id))
        opened.append({"iss": iss_id, "reason": q["reason"], "src": q["src"],
                       "urg": urg, "title": title, "q_uid": q["q_uid"], "conf": q["conf"]})
    return opened

# ---------------------------------------------- IN: VMT DONE -> G01 ----------
def ensure_open_view(con):
    """建立/更新 V_QUARANTINE_OPEN: 由 ledger 推導開放狀態, 不動 Q01 (add-only DDL)"""
    con.execute("""
        CREATE OR REPLACE VIEW sbom.V_QUARANTINE_OPEN AS
        SELECT q.* FROM sbom.Q01_QUARANTINE q
        WHERE q.resolved = FALSE
          AND NOT EXISTS (
              SELECT 1 FROM sbom.G01_LEDGER g
              WHERE g.action = 'QUARANTINE_RESOLVED' AND g.target_uid = q.q_uid)
    """)

def already_resolved(con, q_uid):
    r = con.execute("SELECT 1 FROM sbom.G01_LEDGER WHERE action='QUARANTINE_RESOLVED' AND target_uid=? LIMIT 1",
                    [q_uid]).fetchone()
    return bool(r)

def bridge_in(con, ss, commit):
    """VMT 中帶 sbom_q_uid 且 status=DONE 的 issue -> 提議/寫入 G01 RESOLVED 事件"""
    proposals = []
    for i in ss["issues"]:
        q_uid = i.get("sbom_q_uid")
        if not q_uid or i.get("status") != "DONE":
            continue
        if already_resolved(con, q_uid):
            continue
        rp = i.get("reply", {})
        note = "VMT %s opt=%s(%s) ETA=%s by=%s confirmed=%s" % (
            i["issueId"], rp.get("option", ""), rp.get("optionLabel", ""),
            rp.get("eta", i.get("due", "")), rp.get("by", ""), rp.get("confirmed", False))
        proposals.append({"q_uid": q_uid, "iss": i["issueId"], "note": note})
    if commit:
        for p in proposals:
            con.execute(
                "INSERT INTO sbom.G01_LEDGER (actor,action,target_tbl,target_uid,before_json,after_json,note) "
                "VALUES ('VMT_BRIDGE','QUARANTINE_RESOLVED','Q01_QUARANTINE',?,NULL,?,?)",
                [p["q_uid"], json.dumps({"resolved_via": p["iss"]}), p["note"]])
            append_vmt_event("SBOM_QUARANTINE_RESOLVED", p["iss"], "q_uid=%s -> G01 ledger" % p["q_uid"][:8])
    return proposals

# ---------------------------------------------- Visual Lock 報告 -------------
def build_report(opened, proposals, committed, watch, out_path):
    def esc(s): return ("" if s is None else str(s)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    urg_hex = {5: "#b5443a", 4: "#d08343", 3: "#c9a13a", 2: "#7ba86a", 1: "#4d8f63"}
    watch_rows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(r[0]), r[1]) for r in watch) \
                 or "<tr><td colspan='2' class='empty'>無未解隔離</td></tr>"
    out_rows = "".join(
        "<tr><td>%s</td><td><span class='pill' style='background:%s'>U%s</span></td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (esc(o["iss"]), urg_hex.get(o["urg"], "#999"), o["urg"], esc(o["reason"]), esc(o["src"]), esc(o["title"]))
        for o in opened) or "<tr><td colspan='5' class='empty'>本次無新開追蹤 (可能已冪等去重)</td></tr>"
    in_label = "已寫入 G01 (committed)" if committed else "提議 (dry-run，加 --commit 才寫入)"
    in_rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                      % (esc(p["iss"]), esc(p["q_uid"][:12]), esc(p["note"])) for p in proposals) \
              or "<tr><td colspan='3' class='empty'>無已 DONE 的隔離追蹤可回寫</td></tr>"
    now = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>VMT×SuperBOM 橋</title><style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;--teal:#439a9a;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.seal{display:inline-flex;width:44px;height:44px;background:#439a9a;color:#fff;align-items:center;justify-content:center;font-size:20px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font-size:20px;letter-spacing:1px}.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 22px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:24px 0 10px;text-transform:uppercase}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair)}tr:last-child td{border-bottom:none}
.pill{color:#fff;font-size:11px;font-family:"DM Mono",monospace;padding:2px 8px;border-radius:2px}
.empty{color:#999;text-align:center}
.gov{background:#f0f6f4;border:1px solid #cfe3dc;border-left:5px solid #439a9a;border-radius:3px;padding:10px 14px;font-size:12px;color:#2f5d52;margin-bottom:14px}
footer{margin-top:30px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
</style></head><body>
<header><div class="seal">橋</div><div><h1>VMT × SuperBOM 隔離追蹤橋 — 雙向閉環</h1>
<div class="sub">{{NOW}} | canonical 不碰 · Q01 只讀 · G01 只 append</div></div></header>
<div class="strip"></div>
<div class="gov">治理：SuperBOM M01/M02/M03 完全未觸碰；Q01 只讀取、永不 UPDATE；關閉狀態改由 G01_LEDGER 事件推導 (V_QUARANTINE_OPEN)。VMT 端只新增 issue。</div>
<h2>SuperBOM 未解隔離 (依原因)</h2>
<table><tr><th>reason_code</th><th>未解數</th></tr>{{WATCH}}</table>
<h2>OUT：本次為隔離開的 VMT 追蹤 issue</h2>
<table><tr><th>ISS</th><th>緊急</th><th>原因</th><th>來源</th><th>標題</th></tr>{{OUT}}</table>
<h2>IN：VMT 已 DONE → 回寫 G01（{{INLABEL}}）</h2>
<table><tr><th>ISS</th><th>q_uid</th><th>回寫摘要</th></tr>{{IN}}</table>
<footer>vmt_superbom_bridge v1.0 | OUT: Q01→ISS(帶 sbom_q_uid) | IN: DONE→G01 QUARANTINE_RESOLVED | 開放狀態由 ledger 推導</footer>
</body></html>"""
    html = (html.replace("{{NOW}}", now).replace("{{WATCH}}", watch_rows)
                .replace("{{OUT}}", out_rows).replace("{{INLABEL}}", in_label).replace("{{IN}}", in_rows))
    open(out_path, "w", encoding="utf-8").write(html)

# ---------------------------------------------- 主流程 -----------------------
def main():
    ap = argparse.ArgumentParser(description="VMT x SuperBOM Quarantine Bridge")
    ap.add_argument("--db", required=True, help="SuperBOM DuckDB 路徑")
    ap.add_argument("--commit", action="store_true", help="實際 append G01 RESOLVED 事件 (預設 dry-run 只提議)")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    print("=" * 60)
    print("  VMT x SuperBOM Quarantine Bridge v1.0  |  雙向閉環")
    print("=" * 60)
    if not os.path.exists(args.db):
        print("[SuperBOM] 找不到 DB: %s" % args.db); return
    ss = load_ssot()
    if ss is None:
        return

    # 連線: 需寫 ledger(commit) 或建 view 時 read-write; 否則 read-only 保護 canonical
    read_only = not args.commit
    con = duckdb.connect(args.db, read_only=read_only)
    try:
        watch = con.execute(
            "SELECT reason_code, COUNT(*) FROM sbom.Q01_QUARANTINE WHERE resolved=FALSE "
            "AND NOT EXISTS (SELECT 1 FROM sbom.G01_LEDGER g WHERE g.action='QUARANTINE_RESOLVED' "
            "AND g.target_uid=Q01_QUARANTINE.q_uid) GROUP BY reason_code ORDER BY 2 DESC").fetchall()

        mail_dir = os.path.join(MAIL_ROOT, dt.datetime.now().strftime("%Y%m%d"))
        opened = bridge_out(con, ss, mail_dir)
        print("[OUT] 為隔離開了 %d 筆 VMT 追蹤 issue (其餘冪等略過)" % len(opened))
        for o in opened:
            print("       %s U%d %s <- %s" % (o["iss"], o["urg"], o["reason"], o["q_uid"][:8]))

        proposals = bridge_in(con, ss, args.commit)
        if args.commit:
            ensure_open_view(con)
            print("[IN ] 已 append %d 筆 QUARANTINE_RESOLVED 到 G01_LEDGER" % len(proposals))
        else:
            print("[IN ] 提議回寫 %d 筆 (dry-run; 加 --commit 才寫 G01)" % len(proposals))
        for p in proposals:
            print("       %s -> q_uid %s" % (p["iss"], p["q_uid"][:8]))
    finally:
        con.close()

    save_ssot(ss)  # VMT 端只增 issue
    os.makedirs(OUT_DIR, exist_ok=True)
    rep = os.path.join(OUT_DIR, "SuperBOM_Bridge.html")
    build_report(opened, proposals, args.commit, watch, rep)
    print("[輸出] 橋接報告:", rep)
    try:
        if os.name == "nt" and not args.no_open:
            os.startfile(rep)  # noqa
    except Exception:
        pass
    print("完成.")

if __name__ == "__main__":
    main()
