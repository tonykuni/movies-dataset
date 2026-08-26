"""VPL-C01 Registry + VPL-C03 LocalStore.
Append-only-friendly SQLite layer. Holds projects, tasks, milestones,
budget lines, risks, stakeholders, resources. Ships with a seed dataset
so the PPT engine has something real to render on first run.
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
import sqlite3
import os
from datetime import date

SCHEMA = """
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY, code TEXT, name TEXT, owner TEXT,
    start TEXT, finish TEXT, status TEXT, summary TEXT
);
CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT,
    start TEXT, finish TEXT, progress REAL, status TEXT, lane TEXT
);
CREATE TABLE IF NOT EXISTS milestone (
    id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, due TEXT, hit INTEGER
);
CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY, project_id INTEGER, category TEXT,
    planned REAL, actual REAL
);
CREATE TABLE IF NOT EXISTS risk (
    id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT,
    probability INTEGER, impact INTEGER, owner TEXT, status TEXT
);
CREATE TABLE IF NOT EXISTS stakeholder (
    id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT,
    power INTEGER, interest INTEGER, role TEXT, category TEXT
);
CREATE TABLE IF NOT EXISTS resource (
    id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, load REAL, capacity REAL,
    url TEXT, kind TEXT
);
CREATE TABLE IF NOT EXISTS flow_node (
    id INTEGER PRIMARY KEY, project_id INTEGER, node_key TEXT, label TEXT,
    meta TEXT, kind TEXT, x INTEGER, y INTEGER
);
CREATE TABLE IF NOT EXISTS flow_edge (
    id INTEGER PRIMARY KEY, project_id INTEGER, src TEXT, dst TEXT
);
CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY, project_id INTEGER, day TEXT, item TEXT,
    category TEXT, amount REAL
);
CREATE TABLE IF NOT EXISTS checklist (
    id INTEGER PRIMARY KEY, project_id INTEGER, item TEXT, done INTEGER,
    priority TEXT, due TEXT
);
CREATE TABLE IF NOT EXISTS event (
    id INTEGER PRIMARY KEY, project_id INTEGER, title TEXT, day TEXT,
    at_time TEXT, kind TEXT, remind_min INTEGER, source TEXT
);
CREATE TABLE IF NOT EXISTS contact (
    id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, role TEXT,
    org TEXT, channel TEXT, handle TEXT, tags TEXT
);
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY, day TEXT, at_time TEXT, source TEXT,
    headline TEXT, url TEXT, urgency TEXT, kind TEXT
);
CREATE TABLE IF NOT EXISTS news_source (
    id INTEGER PRIMARY KEY, name TEXT, url TEXT, enabled INTEGER
);
CREATE TABLE IF NOT EXISTS team (
    id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, role TEXT,
    allocation REAL, current TEXT, status TEXT
);
CREATE TABLE IF NOT EXISTS weeklog (
    id INTEGER PRIMARY KEY, project_id INTEGER, dow TEXT,
    focus REAL, deep REAL, meeting REAL
);
CREATE TABLE IF NOT EXISTS note (
    id INTEGER PRIMARY KEY, parent_id INTEGER, title TEXT, body TEXT,
    kind TEXT, ord INTEGER
);
CREATE TABLE IF NOT EXISTS plan (
    id INTEGER PRIMARY KEY, name TEXT, kind TEXT, phases TEXT
);
CREATE TABLE IF NOT EXISTS meeting (
    id INTEGER PRIMARY KEY, project_id INTEGER, title TEXT, day TEXT,
    attendees TEXT, status TEXT
);
CREATE TABLE IF NOT EXISTS segment (
    id INTEGER PRIMARY KEY, meeting_id INTEGER, ord INTEGER, at_time TEXT,
    text TEXT, category TEXT, speaker TEXT, action INTEGER, keypt INTEGER, confirmed INTEGER
);
CREATE TABLE IF NOT EXISTS minutes (
    id INTEGER PRIMARY KEY, meeting_id INTEGER, summary TEXT,
    actions TEXT, decisions TEXT, discussion TEXT
);
"""

SEED_PROJECT = dict(
    code="VPL-DEMO-01", name="VIA Visual Lock v1 — Closeout",
    owner="Tony", start="2026-05-01", finish="2026-06-20",
    status="active",
    summary="Formalise the VIA design-DNA spec and close the VDF/VRN PanoramaFix "
            "278-issue backlog across a 5-wave, risk-tiered plan.",
)

SEED_TASKS = [
    # name, start, finish, progress, status, lane
    ("VRN Fetch v4 — BRIDGE integration", "2026-05-01", "2026-05-12", 1.00, "done",    "VRN"),
    ("M01 TIFF → PDF migration",           "2026-05-03", "2026-05-10", 1.00, "done",    "VRN"),
    ("Celeritas v1.1 lazy modules",        "2026-05-06", "2026-05-14", 1.00, "done",    "VIA"),
    ("Visual Lock — forbidden list",       "2026-05-12", "2026-05-31", 0.82, "active",  "VIA"),
    ("PanoramaFix — wave 1-2",             "2026-05-13", "2026-05-22", 1.00, "done",    "VIA"),
    ("PanoramaFix — wave 3 verify",        "2026-05-22", "2026-06-04", 0.65, "active",  "VIA"),
    ("Module Standard v1.0 S0-S7",         "2026-06-04", "2026-06-16", 0.00, "blocked", "VIA"),
    ("ConformanceAudit tooling",           "2026-06-10", "2026-06-20", 0.00, "waiting", "VIA"),
]

SEED_MILESTONES = [
    ("Visual Lock spec frozen", "2026-05-31", 0),
    ("PanoramaFix closeout (applied>0)", "2026-06-04", 0),
    ("Module Standard GA", "2026-06-20", 0),
]

SEED_BUDGET = [
    # category, planned, actual
    ("Engineering hours", 120000, 98500),
    ("Compute / infra",    18000, 14200),
    ("Tooling / licences", 9000,  9000),
    ("Contingency",        15000, 3000),
]

SEED_RISKS = [
    # name, probability(1-5), impact(1-5), owner, status
    ("wave-3 patch fails applied>0 gate", 3, 5, "Tony", "active"),
    ("numpy 2.0 leak into vpl_core",      2, 4, "Tony", "active"),
    ("Seaborn/matplotlib pin drift",      2, 3, "Tony", "watch"),
    ("Google API quota on sync",          2, 2, "Tony", "watch"),
    ("Font fallback breaks brand render", 4, 2, "Tony", "active"),
]

SEED_STAKEHOLDERS = [
    # name, power, interest, role, PMBOK category (power/interest grid)
    ("Tony (Owner/Architect)", 5, 5, "Decision", "Manage Closely"),
    ("VIA downstream consumers", 2, 5, "Affected", "Keep Informed"),
    ("Future maintainers",       3, 4, "Affected", "Keep Informed"),
    ("Anthropic tooling",        2, 2, "Support",  "Monitor"),
]

SEED_RESOURCES = [
    # name, load, capacity, url/API, kind
    ("Tony", 0.92, 1.0, "", "human"),
    ("vpl_core CI", 0.40, 1.0, "https://ci.local/vpl", "api"),
    ("via_plot_basic", 0.30, 1.0, "", "env"),
    ("VRN Fetch API", 0.50, 1.0, "https://vrn.local/api/fetch", "api"),
]

SEED_FLOW_NODES = [
    # node_key, label, meta, kind, x, y
    ("n1", "Scan VDF/VRN", "START", "start", 40, 170),
    ("n2", "AST 分析", "VPN M02", "step", 250, 90),
    ("n3", "Risk 分級", "7 layers", "step", 250, 250),
    ("n4", "SafePatch", "applied>0?", "decision", 470, 170),
    ("n5", "Closeout", "END", "end", 680, 170),
]
SEED_FLOW_EDGES = [("n1", "n2"), ("n1", "n3"), ("n2", "n4"), ("n3", "n4"), ("n4", "n5")]

SEED_LEDGER = [
    # day, item, category, amount (negative = spend)
    ("2026-05-04", "GPU compute hrs", "Compute / infra", -1800),
    ("2026-05-09", "python-pptx licence", "Tooling / licences", 0),
    ("2026-05-13", "Contractor — wave1", "Engineering hours", -6200),
    ("2026-05-20", "Storage tier", "Compute / infra", -640),
    ("2026-05-27", "Contractor — wave2", "Engineering hours", -7100),
]

SEED_CHECKLIST = [
    # item, done, priority, due
    ("Confirm PanoramaFix wave-3 applied>0", 0, "high", "2026-05-31"),
    ("Freeze Visual Lock forbidden list", 0, "high", "2026-05-31"),
    ("Review Aegis import-time round 2", 0, "med", "2026-05-31"),
    ("Daily shutdown review", 1, "low", "2026-05-31"),
    ("Tag VRN Fetch v4 release", 1, "med", "2026-05-30"),
]

SEED_EVENTS = [
    # title, day, at_time, kind, remind_min, source
    ("Visual Lock — forbidden list closeout", "2026-05-31", "09:30", "focus", 10, "vtn"),
    ("Sync — VRN Fetch v4 review", "2026-05-31", "11:00", "meeting", 15, "gcal"),
    ("PanoramaFix wave-3 verify", "2026-05-31", "14:00", "focus", 30, "vtn"),
    ("LL handbook — document LL#34", "2026-05-31", "16:30", "task", 10, "vtn"),
]

SEED_CONTACTS = [
    # name, role, org, channel, handle, tags
    ("Tony", "Owner / Architect", "VIA", "email", "tony@via", "decision,core"),
    ("VRN Maintainer", "Maintainer", "VIA/VRN", "slack", "#vrn-fetch", "affected"),
    ("Infra On-call", "Compute", "VIA", "slack", "#infra", "support"),
    ("Anthropic Tooling", "Support", "Anthropic", "email", "support@", "support"),
]

# Sample headlines — real fetch is a backend step (RSS via gated network).
SEED_NEWS = [
    # day, at_time, source, headline, url, urgency, kind
    ("2026-05-31", "08:55", "鉅亨網", "台股開盤走勢與權值股動向", "https://www.cnyes.com/", "important", "market"),
    ("2026-05-31", "08:40", "Yahoo奇摩股市", "美股收盤與台積電 ADR 變化", "https://tw.stock.yahoo.com/", "normal", "market"),
    ("2026-05-31", "08:10", "CNBC", "Fed commentary and rate outlook", "https://www.cnbc.com/", "important", "macro"),
    ("2026-05-31", "07:30", "鉅亨網", "外資買賣超與期貨未平倉", "https://www.cnyes.com/", "normal", "market"),
    ("2026-05-30", "21:15", "CNBC", "Tech earnings recap", "https://www.cnbc.com/", "normal", "tech"),
]

SEED_NEWS_SOURCES = [
    ("CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html", 1),
    ("Yahoo奇摩股市", "https://tw.stock.yahoo.com/rss", 1),
    ("鉅亨網", "https://www.cnyes.com/rss", 1),
]

SEED_TEAM = [
    # name, role, allocation(0-1), current task, status
    ("Tony", "Architect / Lead", 0.92, "Visual Lock closeout", "active"),
    ("VRN Maintainer", "Engineer", 0.55, "VRN Fetch v4", "active"),
    ("Infra On-call", "DevOps", 0.30, "Compute monitoring", "active"),
    ("Reviewer", "QA / Review", 0.20, "PanoramaFix verify", "waiting"),
]

SEED_WEEKLOG = [
    # dow, focus, deep, meeting (hours)
    ("Mon", 1.5, 3.2, 0.9), ("Tue", 2.0, 2.7, 0.6), ("Wed", 1.2, 3.6, 1.2),
    ("Thu", 2.3, 2.8, 0.5), ("Fri", 1.8, 3.3, 0.8), ("Sat", 2.6, 2.0, 0.3),
    ("Sun", 0.7, 0.9, 0.0),
]

# Notion/AppFlowy-style nested notes (tree). parent_id 0 = root.
SEED_NOTES = [
    # id, parent_id, title, body(markdown), kind, ord
    (1, 0, "VIA 知識庫", "# VIA 知識庫\n\nVeritas Intelligence Analytics 的中央筆記。\n\n- 子頁可**樹枝狀展開**\n- 支援 *Markdown*\n- 連結 [docs](https://example)", "page", 1),
    (2, 1, "Visual Lock v1", "## Visual Lock v1\n\n設計 DNA 規範。\n\n**配色**\n- 暖白 `#f5f4f0`\n- 橄欖綠 `#5e7032`\n\n**字體**: Syne / DM Sans / DM Mono\n\n**Forbidden**\n- 無紫色漸層\n- 無標題底線", "page", 1),
    (3, 1, "LL Handbook", "## Lesson Learned\n\n- LL#10: 區塊註解內不可有 `<#`\n- LL#16: numba/ortools 需 Py<=3.12\n- LL#21: 永久隔離 venv\n- LL#25: Celeritas lazy import 13x", "page", 2),
    (4, 0, "個人規劃", "# 個人規劃\n\n非專案的個人計畫與筆記。", "page", 2),
    (5, 4, "本週重點", "## 本週重點\n\n1. 關閉 PanoramaFix wave-3\n2. 凍結 Visual Lock\n3. VeritasPulse S1", "page", 1),
    (6, 4, "閱讀清單", "## 閱讀清單\n\n- [ ] Notion API docs\n- [ ] AppFlowy 架構\n- [x] Open-Meteo API", "page", 2),
]

# Progress matrix — projects + personal plans, phases with progress (0-100)
SEED_PLANS = [
    ("VIA Visual Lock", "project", '[["Spec",100],["Forbidden",82],["Apply",40],["Audit",0]]'),
    ("PanoramaFix", "project", '[["Wave1",100],["Wave2",100],["Wave3",65],["Closeout",0]]'),
    ("VRN Fetch v4", "project", '[["Design",100],["Build",100],["BRIDGE",100],["Ship",90]]'),
    ("VeritasPulse 學習", "personal", '[["Plan",100],["Build",70],["Test",50],["Ship",10]]'),
    ("健康 / 作息", "personal", '[["規劃",100],["執行",60],["回顧",30],["優化",0]]'),
]

SEED_MEETING = dict(project_id=1, title="VRN Fetch v4 — 設計審查會議",
                    day="2026-05-31", attendees="Tony, VRN Maintainer, Reviewer",
                    status="review")  # raw → review → minutes

# Transcript segments — already AI-parsed (id,time,text,category,speaker,action,keypt,confirmed)
SEED_SEGMENTS = [
    # ord, time, text, category, speaker, action, keypt, confirmed
    (1, "00:00", "今天審查 VRN Fetch v4 的 BRIDGE 整合與 ControlCenter UI。", "Discussion", "Tony", 0, 0, 1),
    (2, "00:42", "MDL010 到 MDL014 已全部接上 BRIDGE,測試 21/21 PASS。", "Decision", "VRN Maintainer", 0, 1, 1),
    (3, "01:30", "我們決定 M01 維持 PDF 流程,TIFF 不再保留 fallback。", "Decision", "Tony", 0, 1, 1),
    (4, "02:15", "ControlCenter 的即時狀態燈號需要補上 error 重試計數。", "Action", "Reviewer", 1, 0, 0),
    (5, "03:05", "風險:numpy 2.0 若洩漏進 vpl_core 會破壞相依。", "Risk", "Tony", 0, 1, 1),
    (6, "03:48", "下週前要完成 ControlCenter 重試計數並補單元測試。", "Action", "VRN Maintainer", 1, 0, 0),
    (7, "04:30", "討論是否把 Fetch 重試上限做成可設定參數。", "Discussion", "Reviewer", 0, 0, 1),
    (8, "05:12", "決議:重試上限預設 3,可由設定檔覆寫。", "Decision", "Tony", 0, 1, 1),
    (9, "05:55", "Action:Reviewer 補寫 ControlCenter 的 e2e 測試腳本。", "Action", "Reviewer", 1, 0, 0),
    (10, "06:40", "風險:Google API 配額在大量同步時可能受限。", "Risk", "VRN Maintainer", 0, 0, 0),
]


def connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path: str, seed: bool = True) -> None:
    fresh = not os.path.exists(db_path)
    con = connect(db_path)
    con.executescript(SCHEMA)
    if seed and fresh:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO project(code,name,owner,start,finish,status,summary) "
            "VALUES(:code,:name,:owner,:start,:finish,:status,:summary)", SEED_PROJECT)
        pid = cur.lastrowid
        cur.executemany(
            "INSERT INTO task(project_id,name,start,finish,progress,status,lane) "
            "VALUES(?,?,?,?,?,?,?)", [(pid, *t) for t in SEED_TASKS])
        cur.executemany(
            "INSERT INTO milestone(project_id,name,due,hit) VALUES(?,?,?,?)",
            [(pid, *m) for m in SEED_MILESTONES])
        cur.executemany(
            "INSERT INTO budget(project_id,category,planned,actual) VALUES(?,?,?,?)",
            [(pid, *b) for b in SEED_BUDGET])
        cur.executemany(
            "INSERT INTO risk(project_id,name,probability,impact,owner,status) "
            "VALUES(?,?,?,?,?,?)", [(pid, *r) for r in SEED_RISKS])
        cur.executemany(
            "INSERT INTO stakeholder(project_id,name,power,interest,role,category) "
            "VALUES(?,?,?,?,?,?)", [(pid, *s) for s in SEED_STAKEHOLDERS])
        cur.executemany(
            "INSERT INTO resource(project_id,name,load,capacity,url,kind) "
            "VALUES(?,?,?,?,?,?)", [(pid, *r) for r in SEED_RESOURCES])
        cur.executemany(
            "INSERT INTO flow_node(project_id,node_key,label,meta,kind,x,y) "
            "VALUES(?,?,?,?,?,?,?)", [(pid, *n) for n in SEED_FLOW_NODES])
        cur.executemany(
            "INSERT INTO flow_edge(project_id,src,dst) VALUES(?,?,?)",
            [(pid, *e) for e in SEED_FLOW_EDGES])
        cur.executemany(
            "INSERT INTO ledger(project_id,day,item,category,amount) VALUES(?,?,?,?,?)",
            [(pid, *l) for l in SEED_LEDGER])
        cur.executemany(
            "INSERT INTO checklist(project_id,item,done,priority,due) VALUES(?,?,?,?,?)",
            [(pid, *c) for c in SEED_CHECKLIST])
        cur.executemany(
            "INSERT INTO event(project_id,title,day,at_time,kind,remind_min,source) "
            "VALUES(?,?,?,?,?,?,?)", [(pid, *e) for e in SEED_EVENTS])
        cur.executemany(
            "INSERT INTO contact(project_id,name,role,org,channel,handle,tags) "
            "VALUES(?,?,?,?,?,?,?)", [(pid, *c) for c in SEED_CONTACTS])
        cur.executemany(
            "INSERT INTO news(day,at_time,source,headline,url,urgency,kind) "
            "VALUES(?,?,?,?,?,?,?)", list(SEED_NEWS))
        cur.executemany(
            "INSERT INTO news_source(name,url,enabled) VALUES(?,?,?)",
            list(SEED_NEWS_SOURCES))
        cur.executemany(
            "INSERT INTO team(project_id,name,role,allocation,current,status) "
            "VALUES(?,?,?,?,?,?)", [(pid, *t) for t in SEED_TEAM])
        cur.executemany(
            "INSERT INTO weeklog(project_id,dow,focus,deep,meeting) VALUES(?,?,?,?,?)",
            [(pid, *w) for w in SEED_WEEKLOG])
        cur.executemany(
            "INSERT INTO note(id,parent_id,title,body,kind,ord) VALUES(?,?,?,?,?,?)",
            list(SEED_NOTES))
        cur.executemany(
            "INSERT INTO plan(name,kind,phases) VALUES(?,?,?)", list(SEED_PLANS))
        mcur = cur.execute(
            "INSERT INTO meeting(project_id,title,day,attendees,status) "
            "VALUES(:project_id,:title,:day,:attendees,:status)", SEED_MEETING)
        mid = mcur.lastrowid
        cur.executemany(
            "INSERT INTO segment(meeting_id,ord,at_time,text,category,speaker,action,keypt,confirmed) "
            "VALUES(?,?,?,?,?,?,?,?,?)", [(mid, *s) for s in SEED_SEGMENTS])
        con.commit()
    con.close()


def load_project(db_path: str, project_id: int = 1) -> dict:
    con = connect(db_path)
    p = dict(con.execute("SELECT * FROM project WHERE id=?", (project_id,)).fetchone())
    p["tasks"]        = [dict(r) for r in con.execute("SELECT * FROM task WHERE project_id=? ORDER BY start", (project_id,))]
    p["milestones"]   = [dict(r) for r in con.execute("SELECT * FROM milestone WHERE project_id=? ORDER BY due", (project_id,))]
    p["budget"]       = [dict(r) for r in con.execute("SELECT * FROM budget WHERE project_id=?", (project_id,))]
    p["risks"]        = [dict(r) for r in con.execute("SELECT * FROM risk WHERE project_id=?", (project_id,))]
    p["stakeholders"] = [dict(r) for r in con.execute("SELECT * FROM stakeholder WHERE project_id=?", (project_id,))]
    p["resources"]    = [dict(r) for r in con.execute("SELECT * FROM resource WHERE project_id=?", (project_id,))]
    p["flow_nodes"]   = [dict(r) for r in con.execute("SELECT * FROM flow_node WHERE project_id=?", (project_id,))]
    p["flow_edges"]   = [dict(r) for r in con.execute("SELECT * FROM flow_edge WHERE project_id=?", (project_id,))]
    p["ledger"]       = [dict(r) for r in con.execute("SELECT * FROM ledger WHERE project_id=? ORDER BY day", (project_id,))]
    p["checklist"]    = [dict(r) for r in con.execute("SELECT * FROM checklist WHERE project_id=?", (project_id,))]
    p["events"]       = [dict(r) for r in con.execute("SELECT * FROM event WHERE project_id=? ORDER BY at_time", (project_id,))]
    p["contacts"]     = [dict(r) for r in con.execute("SELECT * FROM contact WHERE project_id=?", (project_id,))]
    p["news"]         = [dict(r) for r in con.execute("SELECT * FROM news ORDER BY day DESC, at_time DESC", ())]
    p["news_sources"] = [dict(r) for r in con.execute("SELECT * FROM news_source", ())]
    p["team"]         = [dict(r) for r in con.execute("SELECT * FROM team WHERE project_id=?", (project_id,))]
    p["weeklog"]      = [dict(r) for r in con.execute("SELECT * FROM weeklog WHERE project_id=?", (project_id,))]
    p["notes"]        = [dict(r) for r in con.execute("SELECT * FROM note ORDER BY parent_id, ord", ())]
    import json as _json
    p["plans"]        = [{**dict(r), "phases": _json.loads(r["phases"])}
                         for r in con.execute("SELECT * FROM plan", ())]
    p["meetings"]     = [dict(r) for r in con.execute("SELECT * FROM meeting WHERE project_id=?", (project_id,))]
    p["segments"]     = [dict(r) for r in con.execute("SELECT * FROM segment ORDER BY meeting_id, ord", ())]
    p["minutes"]      = [dict(r) for r in con.execute("SELECT * FROM minutes", ())]
    con.close()
    return p
