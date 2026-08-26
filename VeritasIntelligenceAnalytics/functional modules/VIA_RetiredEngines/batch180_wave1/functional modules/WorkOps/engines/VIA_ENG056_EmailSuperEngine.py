# -*- coding: utf-8 -*-
"""
email_super_engine.py  v1.1
===========================
郵件智能超級引擎:整合 v1(案件追蹤)+ v2(利害關係人/PMBOK/事件流)+ v3(修復/多重分類/行動庫)

管線五階段:
  S1 INGEST+REPAIR  多格式讀取(.eml/.msg/.txt/.csv,選配 .xlsx/.docx)+ 四道修復工序
  S2 THREAD         主旨正規化 + 串接案件 thread
  S3 CLASSIFY       五維多重分類(CASE/TOPIC/ACTION/URGENCY/PMAREA)
  S4 STAKEHOLDER    利害關係人資料庫 + 回覆延遲/承諾兌現統計 + 自動初評
  S5 ACTION+EXPORT  行動資料庫 + PMBOK 六表 xlsx + WorkMatrix CSV + 事件流 + HTML 報告

統一資料庫 super_engine.db(append-only):
  E01_MAIL / E02_THREAD / E03_LABEL / E04_STAKEHOLDER / E05_INTERACTION /
  E06_ASSESSMENT / E07_ACTION + Views

進度標記:stderr 輸出 @@PROGRESS|pct|label,可掛主啟動器即時進度條。
相依:核心零依賴;xlsx 輸出需 pandas+openpyxl(缺少時自動降級為 CSV)。

用法:
  python email_super_engine.py --input ./mail_export --outdir ./engine_out --since 2026-04-01
  python email_super_engine.py --input ./mail_export --report          # 只看統計
  python email_super_engine.py --input ./mail_export --no-xlsx        # 跳過 xlsx
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
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ENGINE_VERSION = "1.4"


def progress(pct: int, label: str):
    print(f"@@PROGRESS|{pct}|{label}", file=sys.stderr, flush=True)
    print(f"[{pct:3d}%] {label}")


# ============================================================
# Taxonomy(五維;只增不減,改動留註記)
# ============================================================
CASE_RULES = {f"案{i:02d}": [rf"case\s*0?{i}\b" if i < 10 else rf"case\s*{i}\b",
                             rf"案0?{i}\b" if i < 10 else rf"案{i}\b"]
              for i in range(1, 15)}
TOPIC_RULES = {
    "GreenLight":      [r"green\s*light", r"量產放行", r"mass\s*production\s*(approval|release)"],
    "ReliabilityData": [r"reliability", r"信賴性", r"missing\s*data", r"手寫紀錄", r"manual\s*record"],
    "DVT_Risk":        [r"\bDVT\b", r"re-?verification", r"重新驗證"],
    "Handover":        [r"hand\s*over", r"transition", r"交接"],
    "Complaint":       [r"complaint", r"客訴", r"投訴"],
    "Delay":           [r"delay", r"postpone", r"延誤", r"延期", r"behind\s*schedule"],
}
ACTION_RULES = {
    "Escalation": [r"escalat", r"升級", r"management\s+attention", r"highest\s+priority"],
    "Reminder":   [r"reminder", r"follow\s*up", r"still\s+waiting", r"催", r"再次提醒"],
    "Delivery":   [r"attached", r"please\s+find", r"as\s+requested", r"檢附", r"提供如附"],
    "Commitment": [r"will\s+provide", r"we\s+commit", r"承諾", r"預計.*提供", r"by\s+end\s+of"],
    "Request":    [r"please\s+(provide|send|share|confirm|advise)", r"could\s+you", r"請提供", r"請協助", r"請確認"],
    "Info":       [r"\bfyi\b", r"for\s+your\s+(information|reference)", r"供參", r"知會"],
}
URGENCY_RULES = {"Urgent": [r"\burgent\b", r"\basap\b", r"immediately", r"緊急", r"急件", r"立即"]}
PMAREA_RULES = {
    "時程":       [r"schedule", r"delay", r"deadline", r"時程", r"延誤", r"期限"],
    "風險":       [r"\brisk\b", r"issue", r"blocker", r"風險", r"卡住", r"斷點"],
    "品質":       [r"quality", r"defect", r"verification", r"驗證", r"不良", r"品質"],
    "溝通":       [r"meeting", r"minutes", r"會議", r"紀錄"],
    "利害關係人": [r"approval", r"sign-?off", r"簽核", r"核准"],
}
DIMENSIONS = [("CASE", CASE_RULES), ("TOPIC", TOPIC_RULES), ("ACTION", ACTION_RULES),
              ("URGENCY", URGENCY_RULES), ("PMAREA", PMAREA_RULES)]


def load_rules_addendum(path="rules_addendum.json"):
    """外掛規則檔(只增不減):{"CASE": {"案03": ["料號X"]}, "TOPIC": {...}} 逐鍵合併進既有規則。"""
    import json
    p = Path(path)
    if not p.exists():
        return 0
    try:
        add = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] rules_addendum.json 解析失敗:{e}", file=sys.stderr)
        return 0
    table = {"CASE": CASE_RULES, "TOPIC": TOPIC_RULES, "ACTION": ACTION_RULES,
             "URGENCY": URGENCY_RULES, "PMAREA": PMAREA_RULES}
    n = 0
    for dim, labels in add.items():
        target = table.get(dim)
        if target is None:
            continue
        for label, patterns in labels.items():
            target.setdefault(label, [])
            for pat in patterns:
                if pat not in target[label]:
                    target[label].append(pat)
                    n += 1
    return n


_WEEKDAY = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4}


def normalize_deadline(raw: str, anchor):
    """把 7/15、2026-07-20、7月15日、EOW/EOD/EOM、next friday 正規化為 ISO 日期。
    anchor=信件日期(相對表達的基準);解析失敗回傳 None,原字串仍保留。"""
    if not raw or anchor is None:
        return None
    from datetime import timedelta
    s = raw.strip().lower()
    m = re.match(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})$", s)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date().isoformat()
        except ValueError:
            return None
    m = re.match(r"(\d{1,2})[/-](\d{1,2})$", s)
    if m:
        mo, dy = int(m.group(1)), int(m.group(2))
        try:
            d = datetime(anchor.year, mo, dy).date()
        except ValueError:
            return None
        if d < anchor.date():   # 已過 -> 視為明年
            d = d.replace(year=anchor.year + 1)
        return d.isoformat()
    m = re.match(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日?$", s)
    if m:
        try:
            d = datetime(anchor.year, int(m.group(1)), int(m.group(2))).date()
            if d < anchor.date():
                d = d.replace(year=anchor.year + 1)
            return d.isoformat()
        except ValueError:
            return None
    if s in ("eod", "end of day"):
        return anchor.date().isoformat()
    if s in ("eow", "end of week"):
        return (anchor + timedelta(days=(4 - anchor.weekday()) % 7)).date().isoformat()
    if s in ("eom", "end of month"):
        nxt = (anchor.replace(day=28) + timedelta(days=4)).replace(day=1)
        return (nxt - timedelta(days=1)).date().isoformat()
    m = re.match(r"(this|next)\s+(monday|tuesday|wednesday|thursday|friday)$", s)
    if m:
        wd = _WEEKDAY[m.group(2)]
        delta = (wd - anchor.weekday()) % 7
        if m.group(1) == "next":
            delta += 7 if delta == 0 else (7 if delta <= 0 else 7 - 0)
            delta = ((wd - anchor.weekday()) % 7) + 7
        return (anchor + timedelta(days=delta)).date().isoformat()
    return None

DEADLINE_PATTERNS = [
    r"by\s+(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)", r"before\s+(\d{1,2}[/-]\d{1,2})",
    r"deadline[:\s]+(\d{4}[/-]\d{1,2}[/-]\d{1,2})", r"(\d{1,2}\s*月\s*\d{1,2}\s*日)\s*前",
    r"by\s+(EOD|EOW|EOM|end\s+of\s+(?:day|week|month))",
]
NOISE_CUT_PATTERNS = [
    r"-{3,}\s*Original Message\s*-{3,}", r"^From:.*\n(Sent|Date):", r"^寄件者[::]",
    r"^發件人[::]", r"^On .{5,60} wrote:$", r"^在 .{5,60} 寫道[::]", r"^_{10,}$",
    r"此電子郵件(及其附件)?(僅|可能)", r"CONFIDENTIALITY NOTICE",
    r"^Best [Rr]egards", r"^BR[,，]?$",
]
SUBJECT_NOISE = re.compile(r"^\s*((RE|FW|FWD|回覆|轉寄)[::]\s*)+", re.IGNORECASE)
EMAIL_ADDR = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


# ============================================================
# S1 修復層
# ============================================================
class _H2T(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self._skip = [], 0

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


def html_to_text(raw: str) -> str:
    p = _H2T()
    try:
        p.feed(raw)
        return html.unescape("".join(p.parts))
    except Exception:
        return re.sub(r"<[^>]+>", " ", raw)


def repair_bytes(raw: bytes, declared):
    order, seen = ([declared.lower()] if declared else []) + ["utf-8", "cp950", "gb18030", "latin-1"], set()
    for enc in order:
        if enc in seen:
            continue
        seen.add(enc)
        try:
            return raw.decode(enc), ("" if declared and enc == declared.lower() else f"decoded-as:{enc}")
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace"), "forced-utf8-replace"


def repair_mojibake(text: str):
    def cjk(s):
        return (sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff") / len(s)) if s else 0.0
    base, best, note = cjk(text), text, ""
    for enc in ("latin-1", "cp1252"):
        try:
            cand = text.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if cjk(cand) > max(base, 0.05) + 0.10:
            best, note, base = cand, f"mojibake-fixed:{enc}->utf8", cjk(cand)
    return best, note


def strip_noise(text: str):
    cut_at = len(text)
    for pat in NOISE_CUT_PATTERNS:
        m = re.search(pat, text, re.MULTILINE | re.IGNORECASE)
        if m and 0 < m.start() < cut_at:
            cut_at = m.start()
    cleaned = re.sub(r"\n{3,}", "\n\n", text[:cut_at]).strip()
    return cleaned, len(text) - cut_at


def repair_body(msg):
    notes, plain, html_body = [], None, None
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
        body, _ = html_body, notes.append("html->text")
        body = html_to_text(html_body)
    if body is None:
        body, _ = "", notes.append("no-text-part")
    body, n = repair_mojibake(body)
    if n:
        notes.append(n)
    body, cut = strip_noise(body)
    if cut > 0:
        notes.append(f"noise-cut:{cut}chars")
    return body, "; ".join(notes)


# ============================================================
# S1 讀取層
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
             "to": str(msg.get("To", "")), "cc": str(msg.get("Cc", "")), "date": d,
             "body": body, "repair": notes, "source": path.name}]


def load_msg(path: Path):
    try:
        import extract_msg
    except ImportError:
        print(f"[SKIP] {path.name}: .msg 需 pip install extract-msg", file=sys.stderr)
        return []
    m = extract_msg.Message(str(path))
    body, n1 = repair_mojibake(m.body or "")
    body, cut = strip_noise(body)
    notes = "; ".join(x for x in [n1, f"noise-cut:{cut}chars" if cut else ""] if x)
    d = m.date if isinstance(m.date, datetime) else None
    return [{"subject": m.subject or "", "sender": m.sender or "", "to": m.to or "",
             "cc": m.cc or "", "date": d, "body": body, "repair": notes, "source": path.name}]


def load_txt(path: Path):
    text, n = repair_bytes(path.read_bytes(), None)
    lines = text.splitlines()
    if not lines:
        return []
    body, n2 = repair_mojibake("\n".join(lines[2:]))
    body, cut = strip_noise(body)
    return [{"subject": lines[0].strip(), "sender": lines[1].strip() if len(lines) > 1 else "",
             "to": "", "cc": "", "date": None, "body": body,
             "repair": "; ".join(x for x in [n, n2, f"noise-cut:{cut}chars" if cut else ""] if x),
             "source": path.name}]


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
                         "to": r.get("to", ""), "cc": r.get("cc", ""), "date": d, "body": body,
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
# S2 Thread / S3 分類 / 行動抽取
# ============================================================
def build_threads(mails):
    threads = defaultdict(list)
    for m in mails:
        m["norm_subject"] = SUBJECT_NOISE.sub("", m["subject"]).strip() or "(no subject)"
        threads[m["norm_subject"].lower()].append(m)
    for t in threads.values():
        t.sort(key=lambda x: x["date"] or datetime.min)
    return threads


def classify_multi(subject, body):
    text = subject + "\n" + body[:4000]
    hits = []
    for dim, rules in DIMENSIONS:
        for label, patterns in rules.items():
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    hits.append((dim, label, p))
                    break
    return hits


def activity_of(labels):
    order = ["Escalation", "Reminder", "Delivery", "Commitment", "Request", "Info"]
    acts = {lb for d, lb, _ in labels if d == "ACTION"}
    for a in order:
        if a in acts:
            return a
    return "Correspondence"


def extract_deadline(text):
    found = []
    for p in DEADLINE_PATTERNS:
        for m in re.findall(p, text, re.IGNORECASE):
            found.append(m if isinstance(m, str) else " ".join(m))
    return "; ".join(dict.fromkeys(found))[:80]


def extract_actions(mail, labels):
    acts = {lb for d, lb, _ in labels if d == "ACTION"}
    cases = [lb for d, lb, _ in labels if d == "CASE"] or ["待歸類"]
    urgent = any(d == "URGENCY" for d, _, _ in labels)
    deadline = extract_deadline(mail["subject"] + " " + mail["body"])
    due_iso = None
    for piece in deadline.split(";"):
        due_iso = normalize_deadline(piece.strip(), mail.get("date"))
        if due_iso:
            break
    mapping = {"Request": ("等回覆", "對方要求,需回覆或交付"),
               "Commitment": ("等回覆", "承諾事項,期限前追蹤"),
               "Escalation": ("卡住", "升級事項,優先處理"),
               "Reminder": ("卡住", "催辦中,兩天無果即上報")}
    out = []
    for at in acts:
        if at not in mapping:
            continue
        status, desc = mapping[at]
        for case in cases:
            out.append({"case_code": case, "action_type": at,
                        "description": (("[急] " if urgent else "") + desc + ":" + mail["subject"])[:200],
                        "counterpart": mail["sender"][:120], "due_date": deadline,
                        "due_date_iso": due_iso, "status": status})
    return out


def norm_person(raw):
    m = EMAIL_ADDR.search(raw or "")
    return m.group(0).lower() if m else (raw or "").strip().lower()


# ============================================================
# 統一資料庫
# ============================================================
DDL = """
CREATE TABLE IF NOT EXISTS E01_MAIL(
  mail_id INTEGER PRIMARY KEY AUTOINCREMENT, msg_hash TEXT UNIQUE,
  thread_key TEXT, case_seq TEXT, mail_date TEXT, sender TEXT, to_list TEXT,
  subject TEXT, body_clean TEXT, repair_notes TEXT, source TEXT,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS E02_THREAD(
  thread_key TEXT PRIMARY KEY, case_seq TEXT, norm_subject TEXT,
  first_date TEXT, last_date TEXT, mail_count INTEGER,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS E03_LABEL(
  label_id INTEGER PRIMARY KEY AUTOINCREMENT, mail_id INTEGER NOT NULL,
  dimension TEXT NOT NULL, label TEXT NOT NULL, evidence TEXT,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS E04_STAKEHOLDER(
  sk_id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL,
  name TEXT, org_guess TEXT, first_seen TEXT,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS E05_INTERACTION(
  ev_id INTEGER PRIMARY KEY AUTOINCREMENT, case_seq TEXT NOT NULL,
  activity TEXT NOT NULL, ts TEXT, resource TEXT NOT NULL,
  subject TEXT, source TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS E06_ASSESSMENT(
  as_id INTEGER PRIMARY KEY AUTOINCREMENT, sk_email TEXT NOT NULL,
  power TEXT, interest TEXT, engagement_current TEXT, engagement_desired TEXT,
  strategy TEXT, avg_latency_hr REAL, fulfill_rate REAL,
  assessed_at TEXT DEFAULT (datetime('now')), assessed_by TEXT DEFAULT 'engine-v1');
CREATE TABLE IF NOT EXISTS E07_ACTION(
  action_id INTEGER PRIMARY KEY AUTOINCREMENT, mail_id INTEGER NOT NULL,
  case_code TEXT, action_type TEXT, description TEXT, counterpart TEXT,
  due_date TEXT, due_date_iso TEXT, status TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE VIEW IF NOT EXISTS V_LATEST_ASSESSMENT AS
  SELECT * FROM E06_ASSESSMENT a WHERE as_id =
    (SELECT MAX(as_id) FROM E06_ASSESSMENT b WHERE b.sk_email = a.sk_email);
CREATE VIEW IF NOT EXISTS V_OPEN_ACTIONS AS
  SELECT a.*, m.mail_date FROM E07_ACTION a JOIN E01_MAIL m ON m.mail_id=a.mail_id
  WHERE a.status <> '已完成';
CREATE VIEW IF NOT EXISTS V_CASE_STATUS AS
  SELECT case_code, status, COUNT(*) AS n FROM E07_ACTION GROUP BY case_code, status;
CREATE TABLE IF NOT EXISTS E08_SIGNATURE(
  sig_id INTEGER PRIMARY KEY AUTOINCREMENT, index_code TEXT, mail_id INTEGER NOT NULL,
  signer_name TEXT, decision TEXT, sign_date TEXT, source TEXT DEFAULT 'SCF',
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS E09_EXCEPTION(
  exc_id INTEGER PRIMARY KEY AUTOINCREMENT, index_code TEXT, case_seq TEXT,
  exc_type TEXT, detail TEXT, risk_level TEXT,
  detected_at TEXT DEFAULT (datetime('now')), status TEXT DEFAULT '待稽核');
CREATE TABLE IF NOT EXISTS E10_INDEX_REGISTRY(
  idx_id INTEGER PRIMARY KEY AUTOINCREMENT, index_code TEXT UNIQUE, type TEXT,
  seq INTEGER, natural_key TEXT, blake2s_code TEXT,
  created_at TEXT DEFAULT (datetime('now')));
CREATE VIEW IF NOT EXISTS V_UPIM AS
  SELECT m.case_seq, t.norm_subject, m.mail_id, m.mail_date, m.sender,
         a.action_type, a.status AS action_status, a.due_date_iso,
         s.signer_name, s.decision AS sign_decision, s.sign_date,
         e.exc_type, e.risk_level
  FROM E01_MAIL m
  LEFT JOIN E02_THREAD t ON t.thread_key = m.thread_key
  LEFT JOIN E07_ACTION a ON a.mail_id = m.mail_id
  LEFT JOIN E08_SIGNATURE s ON s.mail_id = m.mail_id
  LEFT JOIN E09_EXCEPTION e ON e.case_seq = m.case_seq;
CREATE TABLE IF NOT EXISTS E11_GROUP(
  group_id TEXT PRIMARY KEY, group_name TEXT, centroid_subject TEXT,
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS E12_GROUP_MEMBER(
  gm_id INTEGER PRIMARY KEY AUTOINCREMENT, group_id TEXT NOT NULL,
  thread_key TEXT UNIQUE NOT NULL, similarity REAL,
  created_at TEXT DEFAULT (datetime('now')));
CREATE VIEW IF NOT EXISTS V_GROUP AS
  SELECT g.group_id, g.group_name, gm.thread_key, gm.similarity,
         t.case_seq, t.norm_subject, t.mail_count, t.last_date
  FROM E11_GROUP g JOIN E12_GROUP_MEMBER gm ON gm.group_id=g.group_id
  LEFT JOIN E02_THREAD t ON t.thread_key=gm.thread_key;
CREATE VIEW IF NOT EXISTS V_HEALTH AS
  SELECT t.case_seq, t.norm_subject,
    MAX(CASE WHEN e.exc_type='DELAY' THEN 1 ELSE 0 END) AS delay_flag,
    MAX(CASE WHEN e.exc_type='NO_REPLY' THEN 1 ELSE 0 END) AS no_reply_flag,
    MAX(CASE WHEN e.exc_type='MISMATCH' THEN 1 ELSE 0 END) AS mismatch_flag,
    (SELECT COUNT(*) FROM E07_ACTION a JOIN E01_MAIL m2 ON m2.mail_id=a.mail_id
      WHERE m2.case_seq=t.case_seq AND a.status <> '已完成') AS open_actions
  FROM E02_THREAD t LEFT JOIN E09_EXCEPTION e ON e.case_seq=t.case_seq
  GROUP BY t.case_seq;
"""

E04_NEW_COLUMNS = ["role TEXT", "influence_level TEXT", "responsibility_area TEXT"]

SCF_RE = re.compile(
    r"^\s*(?P<name>[^\n()（）:：]{1,40}?)\s*[（(](?P<date>\d{4}[/-]\d{1,2}[/-]\d{1,2})[)）]"
    r"\s*[:：]\s*(?P<decision>Yes|No|TBA)\s*$",
    re.MULTILINE | re.IGNORECASE)


def migrate_db(conn):
    """append-only 遷移:舊 DB 補 E04 新欄(僅 ADD COLUMN,失敗即已存在)。"""
    cur = conn.cursor()
    for col in E04_NEW_COLUMNS:
        try:
            cur.execute(f"ALTER TABLE E04_STAKEHOLDER ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass
    conn.commit()


def auto_index(cur, typ: str, natural_key: str) -> str:
    """DG-IN-{TYPE}-{SEQ3} 自動編號;自然鍵入表(LL#30),同鍵冪等回傳既有碼。"""
    row = cur.execute("SELECT index_code FROM E10_INDEX_REGISTRY"
                      " WHERE type=? AND natural_key=?", (typ, natural_key)).fetchone()
    if row:
        return row[0]
    seq = cur.execute("SELECT COALESCE(MAX(seq),0)+1 FROM E10_INDEX_REGISTRY"
                      " WHERE type=?", (typ,)).fetchone()[0]
    code = f"DG-IN-{typ}-{seq:03d}"
    b3 = hashlib.blake2s(f"DG-IN|{typ}|{natural_key}".encode("utf-8"),
                         digest_size=3).hexdigest().upper()
    cur.execute("INSERT INTO E10_INDEX_REGISTRY(index_code,type,seq,natural_key,blake2s_code)"
                " VALUES(?,?,?,?,?)", (code, typ, seq, natural_key, b3))
    return code


def parse_scf(body: str):
    """SCF 畫押解析:Tony(2026/07/13): Yes → [(name,date,decision)],最多取前 5 筆。"""
    out = []
    for m in SCF_RE.finditer(body or ""):
        out.append((m.group("name").strip(), m.group("date"),
                    m.group("decision").upper() if m.group("decision").lower() != "tba"
                    else "TBA"))
        if len(out) >= 5:
            break
    # 正規化 decision 大小寫
    return [(n, d, {"YES": "Yes", "NO": "No", "TBA": "TBA"}[dec.upper()])
            for n, d, dec in out]


def detect_exceptions(conn, threads_meta):
    """異常偵測(冪等:同案同型未結異常不重複建):
    DELAY=最後往來>2天且有未結行動;NO_REPLY=Request/Reminder 未結且>48h;
    MISMATCH=已有 Delivery 事件但仍有未結行動。"""
    cur = conn.cursor()
    now = datetime.now()
    n_new = 0
    for t in threads_meta:
        cs = t["case_seq"]
        open_n = cur.execute(
            "SELECT COUNT(*) FROM E07_ACTION a JOIN E01_MAIL m ON m.mail_id=a.mail_id"
            " WHERE m.case_seq=? AND a.status <> '已完成'", (cs,)).fetchone()[0]
        last = datetime.fromisoformat(t["last_date"]) if t["last_date"] else None
        findings = []
        if open_n and last and (now - last).days > 2:
            findings.append(("DELAY", f"最後往來 {(now-last).days} 天前,未結行動 {open_n} 件", "中"))
        stale_req = cur.execute(
            "SELECT COUNT(*) FROM E07_ACTION a JOIN E01_MAIL m ON m.mail_id=a.mail_id"
            " WHERE m.case_seq=? AND a.status <> '已完成'"
            " AND a.action_type IN ('Request','Reminder')"
            " AND m.mail_date IS NOT NULL AND m.mail_date < ?",
            (cs, (now - timedelta(hours=48)).isoformat())).fetchone()[0]
        if stale_req:
            findings.append(("NO_REPLY", f"要求/催辦逾 48h 未結 {stale_req} 件", "高"))
        has_delivery = cur.execute(
            "SELECT COUNT(*) FROM E05_INTERACTION WHERE case_seq=? AND activity='Delivery'",
            (cs,)).fetchone()[0]
        if has_delivery and open_n:
            findings.append(("MISMATCH", f"已有交付事件但仍有 {open_n} 件未結(完成度不一致)", "高"))
        for exc_type, detail, risk in findings:
            exists = cur.execute(
                "SELECT 1 FROM E09_EXCEPTION WHERE case_seq=? AND exc_type=?"
                " AND status <> '已結'", (cs, exc_type)).fetchone()
            if exists:
                continue
            code = auto_index(cur, "EXC", f"{cs}|{exc_type}|{now.date().isoformat()}")
            cur.execute("INSERT INTO E09_EXCEPTION(index_code,case_seq,exc_type,detail,"
                        "risk_level) VALUES(?,?,?,?,?)", (code, cs, exc_type, detail, risk))
            n_new += 1
    conn.commit()
    return n_new



def stakeholder_metrics(conn):
    rows = conn.execute(
        "SELECT case_seq, activity, ts, resource FROM E05_INTERACTION"
        " WHERE ts IS NOT NULL ORDER BY case_seq, ts").fetchall()
    by_case = defaultdict(list)
    for cs, act, ts, res in rows:
        by_case[cs].append((act, datetime.fromisoformat(ts), res))
    persons = sorted({r[3] for r in rows})
    out = []
    for person in persons:
        latencies, commits, delivers, events = [], 0, 0, 0
        for cs, evs in by_case.items():
            for i, (act, ts, res) in enumerate(evs):
                if res == person:
                    events += 1
                    if act == "Commitment":
                        commits += 1
                    if act == "Delivery":
                        delivers += 1
                    continue
                if act in ("Request", "Reminder"):
                    nxt = [(a2, t2) for a2, t2, r2 in evs[i + 1:] if r2 == person]
                    if nxt:
                        latencies.append((nxt[0][1] - ts).total_seconds() / 3600)
        out.append({"person": person, "events": events,
                    "avg_latency_hr": round(sum(latencies) / len(latencies), 1) if latencies else None,
                    "commits": commits, "delivers": delivers,
                    "fulfill_rate": round(delivers / commits, 2) if commits else None})
    return sorted(out, key=lambda x: -x["events"])


def auto_assess(conn, metrics):
    if not metrics:
        return
    counts = sorted(m["events"] for m in metrics)
    q75 = counts[int(len(counts) * 0.75)] if counts else 0
    cur = conn.cursor()
    for m in metrics:
        lat = m["avg_latency_hr"]
        eng = ("Resistant" if (lat is not None and lat > 96)
               else "Neutral" if (lat is None or lat > 48) else "Supportive")
        cur.execute(
            "INSERT INTO E06_ASSESSMENT(sk_email,power,interest,engagement_current,"
            "engagement_desired,strategy,avg_latency_hr,fulfill_rate) VALUES(?,?,?,?,?,?,?,?)",
            (m["person"], "TBD-manual", "High" if m["events"] >= q75 else "Low",
             eng, "Supportive", "回覆延遲>48h 者納入 48 小時升級規則書面追蹤",
             lat, m["fulfill_rate"]))
    conn.commit()


# ============================================================
# 主旨智慧分群(v1.4):跨主旨模糊分群,增量歸群,append-only
# ============================================================
GROUP_SIM_THRESHOLD = 0.55
_SUBJ_STOP = set("re fw fwd the a an of to in for on and or with is are at by 的 了 與 及".split())


def subject_tokens(subject: str):
    """主旨切詞:英數詞 + 中文逐字;去停用詞與純數字雜訊(保留案號類 token)。"""
    toks = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", (subject or "").lower())
    return [t for t in toks if t not in _SUBJ_STOP]


def subject_similarity(a: str, b: str) -> float:
    """雙演算法加權:token Jaccard(語意重疊)0.5 + SequenceMatcher(字序)0.5。"""
    import difflib
    ta, tb = set(subject_tokens(a)), set(subject_tokens(b))
    jac = (len(ta & tb) / len(ta | tb)) if (ta or tb) else 0.0
    seq = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return round(0.5 * jac + 0.5 * seq, 3)


def auto_group_name(subjects):
    """群名自動生成:成員主旨最高頻的 3 個有意義 token。"""
    cnt = Counter()
    for s in subjects:
        for t in set(subject_tokens(s)):
            if len(t) >= 2 or "\u4e00" <= t <= "\u9fff":
                cnt[t] += 1
    top = [t for t, _ in cnt.most_common(3)]
    return " · ".join(top) if top else (subjects[0][:20] if subjects else "未命名")


def smart_subject_grouping(conn, threads_meta):
    """增量分群:未入群 thread 逐一與既有群組比對(取群內成員最大相似度),
    ≥ 門檻歸入既有群;否則建新群(DG-IN-GRP 編號)。重跑冪等。"""
    cur = conn.cursor()
    # 載入既有群組與成員主旨(每群取樣至多 10 筆代表)
    groups = {}
    for gid, in cur.execute("SELECT group_id FROM E11_GROUP"):
        subs = [r[0] for r in cur.execute(
            "SELECT t.norm_subject FROM E12_GROUP_MEMBER gm"
            " JOIN E02_THREAD t ON t.thread_key=gm.thread_key"
            " WHERE gm.group_id=? LIMIT 10", (gid,))]
        groups[gid] = subs
    assigned = {r[0] for r in cur.execute("SELECT thread_key FROM E12_GROUP_MEMBER")}
    n_new_groups = n_joined = 0
    for t in threads_meta:
        if t["thread_key"] in assigned:
            continue
        subj = t["norm_subject"]
        best_gid, best_sim = None, 0.0
        for gid, subs in groups.items():
            sim = max((subject_similarity(subj, s) for s in subs), default=0.0)
            if sim > best_sim:
                best_gid, best_sim = gid, sim
        if best_gid and best_sim >= GROUP_SIM_THRESHOLD:
            cur.execute("INSERT INTO E12_GROUP_MEMBER(group_id,thread_key,similarity)"
                        " VALUES(?,?,?)", (best_gid, t["thread_key"], best_sim))
            groups[best_gid].append(subj)
            # 群名隨成員演進更新(名稱可變,群組編號永不變)
            cur.execute("UPDATE E11_GROUP SET group_name=? WHERE group_id=?",
                        (auto_group_name(groups[best_gid]), best_gid))
            n_joined += 1
        else:
            gid = auto_index(cur, "GRP", t["thread_key"])
            cur.execute("INSERT OR IGNORE INTO E11_GROUP(group_id,group_name,centroid_subject)"
                        " VALUES(?,?,?)", (gid, auto_group_name([subj]), subj))
            cur.execute("INSERT INTO E12_GROUP_MEMBER(group_id,thread_key,similarity)"
                        " VALUES(?,?,1.0)", (gid, t["thread_key"]))
            groups[gid] = [subj]
            n_new_groups += 1
        assigned.add(t["thread_key"])
    conn.commit()
    return n_new_groups, n_joined


def export_subject_groups(conn, outdir: Path):
    rows = conn.execute(
        "SELECT group_id, group_name, thread_key, case_seq, norm_subject, similarity,"
        " mail_count FROM V_GROUP ORDER BY group_id, similarity DESC").fetchall()
    out = outdir / "subject_groups.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["群組編號", "群組名稱", "案件", "主旨", "相似度", "郵件數"])
        for gid, gname, tk, cs, subj, sim, mc in rows:
            w.writerow([gid, gname, cs, subj, sim, mc])
    n_groups = conn.execute("SELECT COUNT(*) FROM E11_GROUP").fetchone()[0]
    return n_groups, len(rows)


# ============================================================
# 匯出層
# ============================================================
def export_matrix_csv(conn, out_path: Path):
    cur = conn.execute(
        "SELECT case_code, description, counterpart, due_date, status, mail_date"
        " FROM V_OPEN_ACTIONS ORDER BY case_code, mail_date")
    i = 0
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["編號", "類別", "事務名稱", "進度在誰手上", "對口(等誰)",
                    "等什麼(交付物)", "狀態", "承諾日期", "下一步", "備註"])
        for case, desc, cp, due, status, mdate in cur.fetchall():
            i += 1
            w.writerow([f"A{i:03d}", "移轉案" if case.startswith("案") else "跨部門",
                        f"{case}:{desc[:45]}", "他人", cp, desc[:60], status, due,
                        "依行動類型處理", f"來源信件日 {mdate or ''}"])
    return i


def export_event_log(conn, outdir: Path):
    rows = conn.execute(
        "SELECT case_seq, activity, ts, resource FROM E05_INTERACTION"
        " WHERE ts IS NOT NULL ORDER BY case_seq, ts").fetchall()
    with open(outdir / "event_log.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case:concept:name", "concept:name", "time:timestamp", "org:resource"])
        for r in rows:
            w.writerow(r)
    trans = Counter()
    by_case = defaultdict(list)
    for cs, act, ts, res in rows:
        by_case[cs].append(act)
    for acts in by_case.values():
        for a, b in zip(acts, acts[1:]):
            trans[(a, b)] += 1
    with open(outdir / "activity_transitions.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["From", "To", "次數"])
        for (a, b), n in trans.most_common():
            w.writerow([a, b, n])
    return len(rows)


def export_xlsx(conn, threads_meta, outdir: Path):
    try:
        import pandas as pd
    except ImportError:
        print("[INFO] 無 pandas,跳過 xlsx(已有 CSV 輸出)", file=sys.stderr)
        return False
    control = []
    now = datetime.now()
    for t in threads_meta:
        last = datetime.fromisoformat(t["last_date"]) if t["last_date"] else None
        stale = (now - last).days if last else None
        open_n = conn.execute(
            "SELECT COUNT(*) FROM E07_ACTION a JOIN E01_MAIL m ON m.mail_id=a.mail_id"
            " WHERE m.thread_key=? AND a.status <> '已完成'", (t["thread_key"],)).fetchone()[0]
        status = "卡住" if open_n and stale and stale > 2 else ("等回覆" if open_n else "進行中")
        control.append({"Case ID": t["case_seq"], "案件主旨": t["norm_subject"],
                        "郵件數": t["mail_count"], "首封": t["first_date"] or "",
                        "最後往來": t["last_date"] or "", "無回應天數": stale,
                        "未結行動數": open_n, "狀態": status,
                        "48h升級旗標": "YES" if (stale is not None and stale > 2 and open_n) else ""})
    reg = pd.read_sql_query(
        "SELECT s.email AS 人員, s.org_guess AS 組織, a.power AS Power, a.interest AS Interest,"
        " a.engagement_current AS 現況投入, a.avg_latency_hr AS 平均回覆延遲hr,"
        " a.fulfill_rate AS 兌現率, a.strategy AS 溝通策略"
        " FROM E04_STAKEHOLDER s LEFT JOIN V_LATEST_ASSESSMENT a ON a.sk_email=s.email", conn)
    actions = pd.read_sql_query(
        "SELECT action_id, case_code, action_type, description, counterpart, due_date, status,"
        " mail_date FROM V_OPEN_ACTIONS ORDER BY case_code", conn)
    issues = actions[actions["status"] == "卡住"].copy()
    risks = actions[actions["action_type"].isin(["Escalation", "Reminder"])].copy()
    with pd.ExcelWriter(outdir / "PMBOK_Control_Sheet.xlsx", engine="openpyxl") as w:
        pd.DataFrame(control).to_excel(w, sheet_name="ControlSheet", index=False)
        reg.to_excel(w, sheet_name="StakeholderRegister", index=False)
        actions.to_excel(w, sheet_name="OpenActions", index=False)
        issues.to_excel(w, sheet_name="IssueLog", index=False)
        risks.to_excel(w, sheet_name="RiskRegister", index=False)
        pd.DataFrame(columns=["Change ID", "日期", "變更內容", "原值", "新值", "提出人", "核准人"]
                     ).to_excel(w, sheet_name="ChangeLog", index=False)
    return True


def export_html_report(conn, metrics, stats, outdir: Path):
    rows_case = conn.execute("SELECT * FROM V_CASE_STATUS ORDER BY case_code").fetchall()
    sb = []
    sb.append('<!DOCTYPE html><html><head><meta charset="utf-8"><title>超級引擎報告</title>')
    sb.append('<style>body{font-family:"Microsoft JhengHei",sans-serif;background:#f5f4f0;'
              'color:#26313a;margin:32px}h1{font-size:20px}h2{font-size:16px;margin-top:28px}'
              'table{border-collapse:collapse;background:#fff;margin-top:8px}'
              'td,th{border:1px solid #dbd9d3;padding:6px 12px;font-size:13px;text-align:left}'
              'th{background:#2b3a42;color:#fff}.k{display:inline-block;margin-right:28px}'
              '.n{font-size:26px;font-weight:bold;color:#0e7c86}</style></head><body>')
    sb.append(f'<h1>郵件超級引擎報告 v{ENGINE_VERSION} · {datetime.now():%Y-%m-%d %H:%M}</h1><p>')
    for label, n in stats:
        sb.append(f'<span class="k"><span class="n">{n}</span> {label}</span>')
    sb.append('</p><h2>各案行動狀態</h2><table><tr><th>案件</th><th>狀態</th><th>件數</th></tr>')
    for case, st, n in rows_case:
        sb.append(f'<tr><td>{case}</td><td>{st}</td><td>{n}</td></tr>')
    sb.append('</table><h2>利害關係人行為統計</h2><table><tr><th>人員</th><th>事件數</th>'
              '<th>平均回覆延遲(hr)</th><th>Commit</th><th>Deliver</th><th>兌現率</th></tr>')
    for m in metrics:
        sb.append(f'<tr><td>{m["person"]}</td><td>{m["events"]}</td>'
                  f'<td>{m["avg_latency_hr"] if m["avg_latency_hr"] is not None else "-"}</td>'
                  f'<td>{m["commits"]}</td><td>{m["delivers"]}</td>'
                  f'<td>{m["fulfill_rate"] if m["fulfill_rate"] is not None else "-"}</td></tr>')
    sb.append('</table><p style="color:#6b7a85;font-size:12px">統計為 M 級證據(依信件樣本推算);'
              '正式上報前請註明資料範圍。分類規則命中證據存於 E03_LABEL,可稽核。</p></body></html>')
    (outdir / "engine_report.html").write_text("".join(sb), encoding="utf-8")


# ============================================================
# 主管線
# ============================================================
def run(args):
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    ssot = Path(args.ssot) if getattr(args, "ssot", None) else None
    if ssot:
        ssot.mkdir(parents=True, exist_ok=True)
    db_path = (ssot / "super_engine.db") if ssot else (outdir / "super_engine.db")
    since = datetime.strptime(args.since, "%Y-%m-%d") if args.since else None

    n_add = load_rules_addendum(str(ssot / "rules_addendum.json")) if ssot         else load_rules_addendum()
    if n_add:
        progress(3, f"外掛規則載入:+{n_add} 條 pattern(rules_addendum.json)")
    progress(5, "S1 讀取與修復郵件")
    mails = ingest(Path(args.input))
    if since:
        mails = [m for m in mails if not m["date"] or m["date"] >= since]
    repaired = sum(1 for m in mails if m["repair"])
    progress(20, f"S1 完成:{len(mails)} 封,修復 {repaired} 封")

    progress(25, "S2 串接案件 thread")
    threads = build_threads(mails)
    thread_keys = {k: f"CASE-{i+1:04d}" for i, k in enumerate(sorted(
        threads, key=lambda k: threads[k][-1]["date"] or datetime.min, reverse=True))}
    progress(35, f"S2 完成:{len(threads)} 個 thread")

    if args.report:
        c = Counter()
        for m in mails:
            for dim, label, _ in classify_multi(m["subject"], m["body"]):
                c[(dim, label)] += 1
        for (dim, label), n in sorted(c.items()):
            print(f"    {dim:8s} {label:16s} {n}")
        progress(100, "report-only 完成")
        return

    progress(40, "S3 多重分類 + 入庫")
    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)
    migrate_db(conn)
    cur = conn.cursor()
    n_mail = n_dup = n_label = n_action = 0
    threads_meta = []
    for key, msgs in threads.items():
        seq = thread_keys[key]
        threads_meta.append({"thread_key": key, "case_seq": seq,
                             "norm_subject": msgs[0]["norm_subject"],
                             "first_date": msgs[0]["date"].isoformat() if msgs[0]["date"] else None,
                             "last_date": msgs[-1]["date"].isoformat() if msgs[-1]["date"] else None,
                             "mail_count": len(msgs)})
        cur.execute("INSERT OR IGNORE INTO E02_THREAD(thread_key,case_seq,norm_subject,"
                    "first_date,last_date,mail_count) VALUES(?,?,?,?,?,?)",
                    (key, seq, msgs[0]["norm_subject"],
                     threads_meta[-1]["first_date"], threads_meta[-1]["last_date"], len(msgs)))
        for m in msgs:
            h = hashlib.blake2s((m["subject"] + "|" + m["sender"] + "|" + str(m["date"]) + "|"
                                 + m["body"][:500]).encode("utf-8"), digest_size=12).hexdigest()
            if cur.execute("SELECT 1 FROM E01_MAIL WHERE msg_hash=?", (h,)).fetchone():
                n_dup += 1
                continue
            cur.execute("INSERT INTO E01_MAIL(msg_hash,thread_key,case_seq,mail_date,sender,"
                        "to_list,subject,body_clean,repair_notes,source) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (h, key, seq, m["date"].isoformat() if m["date"] else None, m["sender"],
                         m["to"], m["subject"], m["body"], m["repair"], m["source"]))
            mail_id = cur.lastrowid
            n_mail += 1
            auto_index(cur, "EML", h)
            for sname, sdate, sdec in parse_scf(m["body"]):
                scode = auto_index(cur, "SIG", f"{h}|{sname}|{sdec}")
                cur.execute("INSERT INTO E08_SIGNATURE(index_code,mail_id,signer_name,"
                            "decision,sign_date) VALUES(?,?,?,?,?)",
                            (scode, mail_id, sname, sdec, sdate.replace("/", "-")))
            labels = classify_multi(m["subject"], m["body"])
            for dim, label, ev in labels:
                cur.execute("INSERT INTO E03_LABEL(mail_id,dimension,label,evidence)"
                            " VALUES(?,?,?,?)", (mail_id, dim, label, ev))
                n_label += 1
            sender = norm_person(m["sender"])
            if sender:
                cur.execute("INSERT OR IGNORE INTO E04_STAKEHOLDER(email,name,org_guess,first_seen)"
                            " VALUES(?,?,?,?)",
                            (sender, re.sub(r"<[^>]*>", "", m["sender"]).strip().strip('"') or sender,
                             sender.split("@")[-1] if "@" in sender else "",
                             m["date"].isoformat() if m["date"] else None))
                cur.execute("INSERT INTO E05_INTERACTION(case_seq,activity,ts,resource,subject,source)"
                            " VALUES(?,?,?,?,?,?)",
                            (seq, activity_of(labels),
                             m["date"].isoformat() if m["date"] else None,
                             sender, m["subject"], m["source"]))
            for a in extract_actions(m, labels):
                cur.execute("INSERT INTO E07_ACTION(mail_id,case_code,action_type,description,"
                            "counterpart,due_date,due_date_iso,status) VALUES(?,?,?,?,?,?,?,?)",
                            (mail_id, a["case_code"], a["action_type"], a["description"],
                             a["counterpart"], a["due_date"], a["due_date_iso"], a["status"]))
                n_action += 1
    conn.commit()
    progress(60, f"S3 完成:{n_mail} 封入庫 / {n_label} 標籤 / {n_action} 行動 / 重複略過 {n_dup}")

    for t in threads_meta:
        auto_index(cur, "PRJ", t["thread_key"])
    conn.commit()
    n_exc = detect_exceptions(conn, threads_meta)
    n_grp_new, n_grp_join = smart_subject_grouping(conn, threads_meta)
    n_sig = conn.execute("SELECT COUNT(*) FROM E08_SIGNATURE").fetchone()[0]
    progress(62, f"S3.5 畫押 {n_sig} 筆 / 新異常 {n_exc} 筆 /"
                  f" 主旨分群 新群 {n_grp_new}+歸入 {n_grp_join}(E08–E12)")
    progress(65, "S4 利害關係人統計與初評")
    metrics = stakeholder_metrics(conn)
    auto_assess(conn, metrics)
    progress(75, f"S4 完成:{len(metrics)} 位對口")

    progress(80, "S5 匯出:WorkMatrix CSV / 事件流 / PMBOK xlsx / HTML")
    n_csv = export_matrix_csv(conn, outdir / "actions_export.csv")
    n_ev = export_event_log(conn, outdir)
    n_g, n_gm = export_subject_groups(conn, outdir)
    has_xlsx = export_xlsx(conn, threads_meta, outdir)
    export_html_report(conn, metrics,
                       [("封郵件", n_mail), ("個 thread", len(threads)),
                        ("個標籤", n_label), ("筆行動", n_action),
                        ("位對口", len(metrics))], outdir)
    conn.close()
    progress(100, f"完成:CSV {n_csv} 筆 / 事件 {n_ev} 筆 / 群組 {n_g} 群 {n_gm} 成員"
                  f" / xlsx {'OK' if has_xlsx else '略過'}"
                  f" / 報告 engine_report.html")


def main():
    ap = argparse.ArgumentParser(description="郵件智能超級引擎")
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="./engine_out")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD")
    ap.add_argument("--report", action="store_true", help="只列分類統計")
    ap.add_argument("--ssot", default=None,
                    help="SSOT 資料夾:DB 與 rules_addendum.json 常駐於此(選填)")
    ap.add_argument("--no-xlsx", action="store_true")
    args = ap.parse_args()
    if args.no_xlsx:
        global export_xlsx
        _orig = export_xlsx
        export_xlsx = lambda *a, **k: False
    run(args)


if __name__ == "__main__":
    main()
