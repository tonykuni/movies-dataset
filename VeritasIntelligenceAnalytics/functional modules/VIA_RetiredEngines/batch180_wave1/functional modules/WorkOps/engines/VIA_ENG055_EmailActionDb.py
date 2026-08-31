# -*- coding: utf-8 -*-
"""
email_action_db.py  v1.0
========================
讀取郵件 → 修復內文 → 多重分類 → 轉化為專案管理「行動資料庫」(SQLite)

設計原則:
  - 修復層:處理編碼宣告錯誤、Big5/GB 亂碼、HTML 信、回覆鏈與簽名檔雜訊
  - 多重分類:一封信可同時命中多個維度、每維度多個標籤(junction table 儲存)
  - append-only:T01/T02/T03 只插入不更新;同一封信重跑以內容雜湊去重
  - 零依賴:核心只用標準庫;.msg 支援需 extract-msg(可選)

輸入格式:.eml / .txt(首行主旨、次行寄件人、其後內文)/ .csv(Outlook 匯出)
          / .msg(pip install extract-msg 後自動啟用)
輸出:actions.db(SQLite)+ actions_export.csv(欄位對齊 WorkMatrix)

用法:
  python email_action_db.py --input ./mail_export --db actions.db --since 2026-04-01
  python email_action_db.py --input ./mail_export --report        # 只看統計不寫檔
"""
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

import argparse
import csv
import email
import email.policy
import email.utils
import hashlib
import html
import html.parser
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
# 分類 Taxonomy(全部可增修;原則:只增不減,改動留註記)
# ============================================================
# 維度 CASE:案件歸屬(關鍵字 → 案件代碼;依實際料號/專案名增補)
CASE_RULES = {
    "案01": [r"case\s*0?1\b", r"案0?1\b"],
    "案02": [r"case\s*0?2\b", r"案0?2\b"],
    "案03": [r"case\s*0?3\b", r"案0?3\b"],
    "案04": [r"case\s*0?4\b", r"案0?4\b"],
    "案05": [r"case\s*0?5\b", r"案0?5\b"],
    "案06": [r"case\s*0?6\b", r"案0?6\b"],
    "案07": [r"case\s*0?7\b", r"案0?7\b"],
    "案08": [r"case\s*0?8\b", r"案0?8\b"],
    "案09": [r"case\s*0?9\b", r"案0?9\b"],
    "案10": [r"case\s*10\b", r"案10\b"],
    "案11": [r"case\s*11\b", r"案11\b"],
    "案12": [r"case\s*12\b", r"案12\b"],
    "案13": [r"case\s*13\b", r"案13\b"],
    "案14": [r"case\s*14\b", r"案14\b"],
}
# 維度 ACTION:行動類型(多選)
ACTION_RULES = {
    "Escalation": [r"escalat", r"升級", r"management\s+attention", r"highest\s+priority"],
    "Reminder":   [r"reminder", r"follow\s*up", r"still\s+waiting", r"催", r"再次提醒"],
    "Delivery":   [r"attached", r"please\s+find", r"as\s+requested", r"檢附", r"提供如附"],
    "Commitment": [r"will\s+provide", r"we\s+commit", r"承諾", r"預計.*提供", r"by\s+end\s+of"],
    "Request":    [r"please\s+(provide|send|share|confirm|advise)", r"could\s+you", r"請提供", r"請協助", r"請確認"],
    "Info":       [r"fyi", r"for\s+your\s+(information|reference)", r"供參", r"知會"],
}
# 維度 URGENCY:緊急度
URGENCY_RULES = {
    "Urgent": [r"\burgent\b", r"\basap\b", r"immediately", r"緊急", r"急件", r"立即", r"今日內"],
}
# 維度 PMAREA:專案管理領域(多選)
PMAREA_RULES = {
    "時程":       [r"schedule", r"delay", r"deadline", r"postpone", r"時程", r"延誤", r"期限"],
    "風險":       [r"\brisk\b", r"issue", r"blocker", r"風險", r"卡住", r"斷點"],
    "品質":       [r"quality", r"defect", r"reject", r"verification", r"驗證", r"不良", r"品質"],
    "溝通":       [r"meeting", r"minutes", r"con-?call", r"會議", r"紀錄", r"討論"],
    "利害關係人": [r"approval", r"sign-?off", r"stakeholder", r"簽核", r"核准", r"主管"],
}
DIMENSIONS = [("CASE", CASE_RULES), ("ACTION", ACTION_RULES),
              ("URGENCY", URGENCY_RULES), ("PMAREA", PMAREA_RULES)]

# 期限樣式(行動抽取用)
DEADLINE_PATTERNS = [
    r"by\s+(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)",
    r"before\s+(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)",
    r"deadline[:\s]+(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
    r"(\d{1,2}\s*月\s*\d{1,2}\s*日)\s*前",
    r"by\s+(EOD|EOW|EOM|end\s+of\s+(?:day|week|month))",
    r"(this|next)\s+(monday|tuesday|wednesday|thursday|friday)",
]
# 回覆鏈/簽名/免責 雜訊切除樣式(命中即截斷其後內容)
NOISE_CUT_PATTERNS = [
    r"-{3,}\s*Original Message\s*-{3,}",
    r"^From:.*\n(Sent|Date):", r"^寄件者[::]", r"^發件人[::]",
    r"^On .{5,60} wrote:$", r"^在 .{5,60} 寫道[::]",
    r"^_{10,}$", r"此電子郵件(及其附件)?(僅|可能)", r"CONFIDENTIALITY NOTICE",
    r"^Best [Rr]egards", r"^BR[,，]?$", r"^Thanks\s*&\s*Best",
]


# ============================================================
# 修復層
# ============================================================
class _HtmlToText(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self._skip += 1
        if tag in ("br", "p", "div", "tr", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("style", "script") and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data):
        if self._skip == 0:
            self.parts.append(data)

    def text(self):
        return "".join(self.parts)


def html_to_text(raw: str) -> str:
    p = _HtmlToText()
    try:
        p.feed(raw)
        return html.unescape(p.text())
    except Exception:
        return re.sub(r"<[^>]+>", " ", raw)


def repair_bytes(raw: bytes, declared: str | None):
    """依序嘗試:宣告編碼 → utf-8 → cp950(Big5) → gb18030 → latin-1,回傳(文字, 修復註記)。"""
    tried = []
    order = []
    if declared:
        order.append(declared.lower())
    order += ["utf-8", "cp950", "gb18030", "latin-1"]
    seen = set()
    for enc in order:
        if enc in seen:
            continue
        seen.add(enc)
        try:
            text = raw.decode(enc)
            note = "" if declared and enc == declared.lower() else f"decoded-as:{enc}"
            return text, note
        except (UnicodeDecodeError, LookupError):
            tried.append(enc)
    return raw.decode("utf-8", errors="replace"), "forced-utf8-replace(" + ",".join(tried) + ")"


def repair_mojibake(text: str):
    """常見亂碼:UTF-8 位元組被誤解為 latin-1/cp1252。嘗試回轉,若中日韓字元比例明顯提升則採用。"""
    def cjk_ratio(s):
        if not s:
            return 0.0
        cjk = sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")
        return cjk / len(s)
    base = cjk_ratio(text)
    best, note = text, ""
    for enc in ("latin-1", "cp1252"):
        try:
            cand = text.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if cjk_ratio(cand) > max(base, 0.05) + 0.10:
            best, note = cand, f"mojibake-fixed:{enc}->utf8"
            base = cjk_ratio(cand)
    return best, note


def strip_noise(text: str):
    """截掉回覆鏈、簽名檔、免責聲明;回傳(乾淨文字, 截除字元數)。"""
    cut_at = len(text)
    for pat in NOISE_CUT_PATTERNS:
        m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
        if m and m.start() < cut_at and m.start() > 0:
            cut_at = m.start()
    cleaned = text[:cut_at]
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned, len(text) - cut_at


def repair_body(msg) -> tuple[str, str]:
    """從 email.message 取出最佳內文並修復;回傳(clean_text, repair_notes)。"""
    notes = []
    plain, html_body = None, None
    for part in (msg.walk() if msg.is_multipart() else [msg]):
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        text, n = repair_bytes(payload, part.get_content_charset())
        if n:
            notes.append(n)
        if ctype == "text/plain" and plain is None:
            plain = text
        elif ctype == "text/html" and html_body is None:
            html_body = text
    body = plain
    if body is None and html_body is not None:
        body = html_to_text(html_body)
        notes.append("html->text")
    if body is None:
        body = ""
        notes.append("no-text-part")
    body, n = repair_mojibake(body)
    if n:
        notes.append(n)
    body, cut = strip_noise(body)
    if cut > 0:
        notes.append(f"noise-cut:{cut}chars")
    return body, "; ".join(notes)


# ============================================================
# 讀取層
# ============================================================
def load_eml(path: Path):
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)
    body, notes = repair_body(msg)
    d = None
    try:
        d = email.utils.parsedate_to_datetime(msg.get("Date", "")).replace(tzinfo=None)
    except Exception:
        pass
    return [{"subject": str(msg.get("Subject", "")), "sender": str(msg.get("From", "")),
             "to": str(msg.get("To", "")), "date": d, "body": body,
             "repair": notes, "source": path.name}]


def load_msg(path: Path):
    try:
        import extract_msg
    except ImportError:
        print(f"[SKIP] {path.name}: .msg 需 pip install extract-msg", file=sys.stderr)
        return []
    m = extract_msg.Message(str(path))
    body = m.body or ""
    body, n1 = repair_mojibake(body)
    body, cut = strip_noise(body)
    notes = "; ".join(x for x in [n1, f"noise-cut:{cut}chars" if cut else ""] if x)
    d = None
    if m.date:
        try:
            d = m.date if isinstance(m.date, datetime) else datetime.strptime(
                str(m.date)[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    return [{"subject": m.subject or "", "sender": m.sender or "", "to": m.to or "",
             "date": d, "body": body, "repair": notes, "source": path.name}]


def load_txt(path: Path):
    raw = path.read_bytes()
    text, n = repair_bytes(raw, None)
    lines = text.splitlines()
    if not lines:
        return []
    body, n2 = repair_mojibake("\n".join(lines[2:]))
    body, cut = strip_noise(body)
    notes = "; ".join(x for x in [n, n2, f"noise-cut:{cut}chars" if cut else ""] if x)
    return [{"subject": lines[0].strip(), "sender": lines[1].strip() if len(lines) > 1 else "",
             "to": "", "date": None, "body": body, "repair": notes, "source": path.name}]


def load_csv_file(path: Path):
    rows = []
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            r = {k.strip().lower(): (v or "") for k, v in r.items()}
            body, n1 = repair_mojibake(r.get("body", r.get("content", "")))
            body, cut = strip_noise(body)
            d = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y-%m-%d", "%m/%d/%Y"):
                try:
                    d = datetime.strptime(r.get("date", r.get("received", ""))[:19], fmt)
                    break
                except ValueError:
                    continue
            rows.append({"subject": r.get("subject", ""), "sender": r.get("from", r.get("sender", "")),
                         "to": r.get("to", ""), "date": d, "body": body,
                         "repair": "; ".join(x for x in [n1, f"noise-cut:{cut}chars" if cut else ""] if x),
                         "source": path.name})
    return rows


LOADERS = {".eml": load_eml, ".msg": load_msg, ".txt": load_txt, ".csv": load_csv_file}


def ingest(input_path: Path):
    files = [input_path] if input_path.is_file() else sorted(input_path.rglob("*"))
    out = []
    for f in files:
        loader = LOADERS.get(f.suffix.lower())
        if not loader:
            continue
        try:
            out.extend(loader(f))
        except Exception as e:
            print(f"[WARN] {f.name}: {e}", file=sys.stderr)
    return out


# ============================================================
# 多重分類 + 行動抽取
# ============================================================
def classify_multi(subject: str, body: str):
    """回傳 [(dimension, label, evidence_pattern), ...];多維度、每維度可多標籤。"""
    text = subject + "\n" + body[:4000]
    hits = []
    for dim, rules in DIMENSIONS:
        for label, patterns in rules.items():
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    hits.append((dim, label, p))
                    break
    return hits


def extract_actions(mail, labels):
    """從已分類郵件抽出行動項目:Request/Commitment/Escalation 類 → 一筆行動。"""
    action_types = {lb for d, lb, _ in labels if d == "ACTION"}
    cases = [lb for d, lb, _ in labels if d == "CASE"] or ["待歸類"]
    urgent = any(d == "URGENCY" for d, _, _ in labels)
    deadlines = []
    for p in DEADLINE_PATTERNS:
        for m in re.findall(p, mail["subject"] + " " + mail["body"], re.IGNORECASE):
            deadlines.append(m if isinstance(m, str) else " ".join(m))
    deadline = "; ".join(dict.fromkeys(deadlines))[:80]
    actions = []
    mapping = {
        "Request":    ("待回覆", "對方要求,需回覆或交付"),
        "Commitment": ("追蹤承諾", "對方/我方承諾,期限前追蹤"),
        "Escalation": ("處理升級", "已升級事項,優先處理"),
        "Reminder":   ("催辦中", "已在催辦,兩天無果即上報"),
    }
    for at in action_types:
        if at not in mapping:
            continue
        status, desc = mapping[at]
        for case in cases:
            actions.append({
                "case_code": case, "action_type": at,
                "description": (("[急] " if urgent else "") + desc + ":" + mail["subject"])[:200],
                "counterpart": mail["sender"][:120],
                "due_date": deadline, "status": status,
            })
    return actions


# ============================================================
# 行動資料庫(append-only)
# ============================================================
DDL = """
CREATE TABLE IF NOT EXISTS T01_MAIL(
    mail_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    msg_hash  TEXT UNIQUE,
    mail_date TEXT, sender TEXT, to_list TEXT, subject TEXT,
    body_clean TEXT, repair_notes TEXT, source TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS T02_LABEL(
    label_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_id INTEGER NOT NULL,
    dimension TEXT NOT NULL, label TEXT NOT NULL, evidence TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS T03_ACTION(
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_id INTEGER NOT NULL,
    case_code TEXT, action_type TEXT, description TEXT,
    counterpart TEXT, due_date TEXT, status TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE VIEW IF NOT EXISTS V_OPEN_ACTIONS AS
    SELECT a.action_id, a.case_code, a.action_type, a.description,
           a.counterpart, a.due_date, a.status, m.mail_date, m.subject
    FROM T03_ACTION a JOIN T01_MAIL m ON m.mail_id = a.mail_id
    WHERE a.status <> '已完成';
CREATE VIEW IF NOT EXISTS V_CASE_SUMMARY AS
    SELECT case_code, action_type, COUNT(*) AS n
    FROM T03_ACTION GROUP BY case_code, action_type;
"""


def build_db(mails, db_path: Path, since: datetime | None):
    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)
    cur = conn.cursor()
    n_mail = n_label = n_action = n_dup = 0
    for m in mails:
        if since and m["date"] and m["date"] < since:
            continue
        h = hashlib.blake2s(
            (m["subject"] + "|" + m["sender"] + "|" + str(m["date"]) + "|" + m["body"][:500]
             ).encode("utf-8"), digest_size=12).hexdigest()
        cur.execute("SELECT mail_id FROM T01_MAIL WHERE msg_hash=?", (h,))
        row = cur.fetchone()
        if row:
            n_dup += 1
            continue
        cur.execute(
            "INSERT INTO T01_MAIL(msg_hash,mail_date,sender,to_list,subject,body_clean,repair_notes,source)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (h, m["date"].isoformat() if m["date"] else None, m["sender"], m["to"],
             m["subject"], m["body"], m["repair"], m["source"]))
        mail_id = cur.lastrowid
        n_mail += 1
        labels = classify_multi(m["subject"], m["body"])
        for dim, label, ev in labels:
            cur.execute("INSERT INTO T02_LABEL(mail_id,dimension,label,evidence) VALUES(?,?,?,?)",
                        (mail_id, dim, label, ev))
            n_label += 1
        for a in extract_actions(m, labels):
            cur.execute(
                "INSERT INTO T03_ACTION(mail_id,case_code,action_type,description,counterpart,due_date,status)"
                " VALUES(?,?,?,?,?,?,?)",
                (mail_id, a["case_code"], a["action_type"], a["description"],
                 a["counterpart"], a["due_date"], a["status"]))
            n_action += 1
    conn.commit()
    return conn, n_mail, n_label, n_action, n_dup


def export_matrix_csv(conn, out_path: Path):
    """匯出欄位對齊 WorkMatrix,可直接貼進矩陣。"""
    cur = conn.execute(
        "SELECT a.case_code, a.description, a.counterpart, a.due_date, a.status, m.subject, m.mail_date"
        " FROM T03_ACTION a JOIN T01_MAIL m ON m.mail_id=a.mail_id"
        " WHERE a.status <> '已完成' ORDER BY a.case_code, m.mail_date")
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["編號", "類別", "事務名稱", "進度在誰手上", "對口(等誰)",
                    "等什麼(交付物)", "狀態", "承諾日期", "下一步", "備註"])
        i = 0
        for case, desc, cp, due, status, subj, mdate in cur.fetchall():
            i += 1
            row_status = {"待回覆": "等回覆", "追蹤承諾": "等回覆",
                          "催辦中": "卡住", "處理升級": "卡住"}.get(status, "進行中")
            w.writerow([f"A{i:03d}", "移轉案" if case.startswith("案") else "跨部門",
                        f"{case}:{subj[:40]}", "他人", cp, desc[:60],
                        row_status, due, "依行動類型處理", f"來源信件日 {mdate or ''}"])
    return i


# ============================================================
# main
# ============================================================
def main():
    ap = argparse.ArgumentParser(description="郵件修復 + 多重分類 + 行動資料庫")
    ap.add_argument("--input", required=True, help="郵件檔或資料夾(.eml/.msg/.txt/.csv)")
    ap.add_argument("--db", default="actions.db")
    ap.add_argument("--since", default=None, help="只納入此日期後郵件 YYYY-MM-DD")
    ap.add_argument("--export", default="actions_export.csv")
    ap.add_argument("--report", action="store_true", help="只列統計,不落地檔案")
    args = ap.parse_args()

    since = datetime.strptime(args.since, "%Y-%m-%d") if args.since else None
    mails = ingest(Path(args.input))
    print(f"[1/4] 讀入 {len(mails)} 封,修復層已套用")
    repaired = sum(1 for m in mails if m["repair"])
    print(f"[2/4] 內文經修復處理:{repaired} 封(編碼/亂碼/HTML/雜訊切除)")

    if args.report:
        from collections import Counter
        c = Counter()
        for m in mails:
            for dim, label, _ in classify_multi(m["subject"], m["body"]):
                c[(dim, label)] += 1
        for (dim, label), n in sorted(c.items()):
            print(f"    {dim:8s} {label:12s} {n}")
        return

    conn, n_mail, n_label, n_action, n_dup = build_db(mails, Path(args.db), since)
    print(f"[3/4] 資料庫:新增 {n_mail} 封 / {n_label} 個標籤 / {n_action} 筆行動;重複略過 {n_dup}")
    n = export_matrix_csv(conn, Path(args.export))
    print(f"[4/4] 匯出 {n} 筆未結行動 → {args.export}(欄位對齊 WorkMatrix)")
    print("\n=== 各案行動統計 ===")
    for case, at, cnt in conn.execute("SELECT * FROM V_CASE_SUMMARY ORDER BY case_code"):
        print(f"    {case:6s} {at:12s} {cnt}")
    conn.close()


if __name__ == "__main__":
    main()
