# -*- coding: utf-8 -*-
"""
============================================================================
 VMT x SuperBOM  Event-Stream Unifier  v1.0   --  接縫③ 統一事件流探勘
----------------------------------------------------------------------------
 定位: 兩個 SSOT 不合併; 把各自的事件流「縫」成一條, 對跨系統生命週期做流程探勘.
   SuperBOM 側:  Q01_QUARANTINE.intake_ts (隔離起點) + G01_LEDGER (INSERT/
                 QUARANTINE_RESOLVED/PROMOTE/... 事件, 皆 actor+ts)
   VMT 側:       events.jsonl (SBOM_QUARANTINE_LINK / MAIL_GEN / REPLY_INGEST /
                 ISSUE_DONE / SBOM_QUARANTINE_RESOLVED ...)
 縫合鍵: 用①②已建的交叉參照 q_uid <-> ISS
   (VMT 的 SBOM_QUARANTINE_LINK 事件 detail 帶 q_uid 前綴 + ref=ISS;
    G01 的 QUARANTINE_RESOLVED target_uid = q_uid) -> 統一 case = q_uid.
 產出: 跨系統生命週期瓶頸 (哪一段等最久) + 各案時間軸 + 兩系統事件量 + DFG.
   「BOM 資料問題偵測 → 開追蹤 → 產信 → 回覆收斂 → 結案 → 回寫解除」全段可視化.
----------------------------------------------------------------------------
 治理: SuperBOM 與 VMT 兩邊都「只讀」(read_only 連線 / 只讀 jsonl); 不寫任何來源.
       產物 (unified CSV + HTML) 落到 reports/, 不動 canonical / ssot.json.
 相容: Python 3.11+; duckdb; pandas. 內建 pandas 探勘 (無需 PM4Py 也可跑).
       unified CSV 為引擎相容三欄格式, 可再餵 vmt_process_mining.py 做 PM4Py 級分析.
============================================================================
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
import os, re, sys, json, argparse, datetime as dt

try:
    import duckdb, pandas as pd
except Exception:
    print("需要 duckdb + pandas"); sys.exit(1)

VMT_ROOT   = os.environ.get("VMT_ROOT", r"C:\VIA\VeritasMailTracker")
EVENT_PATH = os.path.join(VMT_ROOT, "data", "events.jsonl")
OUT_DIR    = os.path.join(VMT_ROOT, "reports")

# 生命週期階段 (排序用前綴 + 顯示標籤); 跨系統
STAGE = {
    "SBOM_INTAKE":   "① SBOM 隔離",
    "VMT_LINK":      "② VMT 開追蹤",
    "VMT_MAIL":      "③ VMT 產信",
    "VMT_REPLY":     "④ VMT 回覆收斂",
    "VMT_DONE":      "⑤ VMT 結案",
    "VMT_WRITEBACK": "⑥ VMT 回寫",
    "SBOM_RESOLVED": "⑦ SBOM 解除隔離",
}
SYS_OF = {v: ("SBOM" if v.startswith(("①", "⑦")) else "VMT") for v in STAGE.values()}

def to_dt(x):
    if isinstance(x, dt.datetime): return x.replace(tzinfo=None)
    try:
        d = dt.datetime.fromisoformat(str(x))
        return d.replace(tzinfo=None)
    except Exception:
        return None

# ------------------------------------------- SuperBOM 側 (只讀) --------------
def read_superbom(con):
    ev = []
    quids = {}
    for q_uid, intake_ts, reason, src in con.execute(
            "SELECT q_uid, intake_ts, reason_code, src_system FROM sbom.Q01_QUARANTINE").fetchall():
        t = to_dt(intake_ts)
        quids[q_uid] = {"reason": reason, "src": src}
        if t:
            ev.append({"Case_ID": q_uid, "Activity": STAGE["SBOM_INTAKE"], "Timestamp": t,
                       "Resource": src or "SBOM", "System": "SBOM"})
    for action, target_uid, ts, actor in con.execute(
            "SELECT action, target_uid, event_ts, actor FROM sbom.G01_LEDGER "
            "WHERE action='QUARANTINE_RESOLVED'").fetchall():
        t = to_dt(ts)
        if t and target_uid in quids:
            ev.append({"Case_ID": target_uid, "Activity": STAGE["SBOM_RESOLVED"], "Timestamp": t,
                       "Resource": actor or "SBOM", "System": "SBOM"})
    return ev, quids

# ------------------------------------------- VMT 側 (只讀) -------------------
VMT_ACT = {
    "SBOM_QUARANTINE_LINK":     "VMT_LINK",
    "MAIL_GEN":                 "VMT_MAIL",
    "REPLY_INGEST":             "VMT_REPLY",
    "ISSUE_DONE":               "VMT_DONE",
    "SBOM_QUARANTINE_RESOLVED": "VMT_WRITEBACK",
}

def read_vmt_events(path, quids):
    if not os.path.exists(path):
        return []
    raw = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: raw.append(json.loads(line))
        except Exception: pass
    # ISS -> q_uid: 由 SBOM_QUARANTINE_LINK 的 detail(q_uid 前綴) 對回完整 q_uid
    iss2quid = {}
    for e in raw:
        if e.get("event") == "SBOM_QUARANTINE_LINK":
            iss = e.get("ref")
            m = re.search(r"q_uid=([0-9a-fA-F]+)", e.get("detail", ""))
            if iss and m:
                pref = m.group(1)
                full = next((q for q in quids if q.startswith(pref)), None)
                if full: iss2quid[iss] = full
    ev = []
    for e in raw:
        evt = e.get("event"); ref = e.get("ref")
        stage = VMT_ACT.get(evt)
        if not stage: continue
        # 找此事件對應的 q_uid: ref=ISS -> map; 或 detail 帶 q_uid 前綴
        quid = iss2quid.get(ref)
        if not quid:
            m = re.search(r"q_uid=([0-9a-fA-F]+)", e.get("detail", ""))
            if m: quid = next((q for q in quids if q.startswith(m.group(1))), None)
        if not quid:
            continue  # 非隔離生命週期事件, 略過 (本探勘聚焦跨系統隔離鏈)
        t = to_dt(e.get("ts"))
        if t:
            ev.append({"Case_ID": quid, "Activity": STAGE[stage], "Timestamp": t,
                       "Resource": "VMT", "System": "VMT"})
    return ev

# ------------------------------------------- 探勘 (pandas 內建) --------------
def mine(df):
    from collections import Counter, defaultdict
    df = df.sort_values("Timestamp")
    edges = Counter(); wait = defaultdict(list); durations = {}
    for case, g in df.groupby("Case_ID"):
        g = g.sort_values("Timestamp")
        acts = list(g["Activity"]); ts = list(g["Timestamp"])
        durations[case] = (ts[-1] - ts[0]).total_seconds()
        for i in range(len(acts) - 1):
            e = (acts[i], acts[i + 1]); edges[e] += 1
            wait[e].append((ts[i + 1] - ts[i]).total_seconds())
    perf = {e: sum(w) / len(w) for e, w in wait.items()}
    return edges, perf, durations

def hum(sec):
    sec = float(sec); d = int(sec // 86400); h = int((sec % 86400) // 3600); m = int((sec % 3600) // 60)
    if d: return "%dd %dh" % (d, h)
    if h: return "%dh %dm" % (h, m)
    return "%dm" % m

# ------------------------------------------- Visual Lock 儀表板 -------------
def build_html(df, edges, perf, durations, quids, out_path):
    def esc(s): return ("" if s is None else str(s)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    n_cases = df["Case_ID"].nunique()
    sys_counts = df["System"].value_counts().to_dict()
    avg_dur = sum(durations.values()) / len(durations) if durations else 0
    # 瓶頸: 依平均等待排序
    bn = sorted(perf.items(), key=lambda kv: kv[1], reverse=True)
    top = bn[0][1] if bn and bn[0][1] > 0 else 1
    bn_rows = ""
    for (a, b), sec in bn:
        cross = SYS_OF.get(a, "?") != SYS_OF.get(b, "?")
        w = max(4, int(200 * sec / top))
        col = "#b5443a" if cross else "#4c78a8"
        tag = " <span class='pill' style='background:#439a9a'>跨系統</span>" if cross else ""
        bn_rows += ("<tr><td>%s <span style='color:#999'>&rarr;</span> %s%s</td><td>%s</td>"
                    "<td><span class='barw' style='width:%dpx;background:%s'></span> %s</td></tr>"
                    % (esc(a), esc(b), tag, edges.get((a, b), ""), w, col, hum(sec)))
    if not bn_rows: bn_rows = "<tr><td colspan='3' class='empty'>無轉移 (需先跑 ①②③ 產生跨系統事件)</td></tr>"
    # 各案時間軸 (生命週期是否走完)
    life_rows = ""
    for case, sec in sorted(durations.items(), key=lambda kv: kv[1], reverse=True):
        g = df[df["Case_ID"] == case].sort_values("Timestamp")
        acts = list(g["Activity"])
        done = STAGE["SBOM_RESOLVED"] in acts or STAGE["VMT_DONE"] in acts
        badge = ("<span class='pill' style='background:#5a9e6f'>已閉環</span>" if done
                 else "<span class='pill' style='background:#c9a13a'>進行中</span>")
        reason = quids.get(case, {}).get("reason", "")
        life_rows += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                      % (esc(case[:12]), esc(reason), len(acts), hum(sec), badge))
    if not life_rows: life_rows = "<tr><td colspan='5' class='empty'>無案件</td></tr>"
    sys_html = " · ".join("%s <b>%d</b> 事件" % (k, v) for k, v in sys_counts.items()) or "—"
    kpis = [("跨系統案件 (q_uid)", n_cases, "#4c78a8"),
            ("事件總數", len(df), "#439a9a"),
            ("平均閉環工期", hum(avg_dur), "#c96b5a"),
            ("最長瓶頸", hum(bn[0][1]) if bn else "-", "#b5443a")]
    kh = "".join("<div class='card'><div class='cv' style='color:%s'>%s</div><div class='cn'>%s</div></div>"
                 % (c, v, n) for n, v, c in kpis)
    now = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>統一事件流探勘</title><style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.seal{display:inline-flex;width:44px;height:44px;background:#c96b5a;color:#fff;align-items:center;justify-content:center;font-size:20px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font-size:20px;letter-spacing:1px}.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 22px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:24px 0 10px;text-transform:uppercase}
.cards{display:flex;gap:12px;flex-wrap:wrap}
.card{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:14px 20px;min-width:150px}
.cv{font-size:22px;font-weight:700}.cn{font-size:12px;color:#777;margin-top:2px}
.line{font-size:13px;color:#555;margin:6px 0 0}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden;margin-top:6px}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair)}tr:last-child td{border-bottom:none}
.barw{height:14px;border-radius:2px;display:inline-block;vertical-align:middle}
.pill{color:#fff;font-size:11px;font-family:"DM Mono",monospace;padding:2px 8px;border-radius:2px}
.empty{color:#999;text-align:center}
.gov{background:#faf3f1;border:1px solid #e6ccc5;border-left:5px solid #c96b5a;border-radius:3px;padding:10px 14px;font-size:12px;color:#7a4238;margin:8px 0 14px}
footer{margin-top:30px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
</style></head><body>
<header><div class="seal">流</div><div><h1>VMT × SuperBOM 統一事件流探勘 — 跨系統生命週期</h1>
<div class="sub">{{NOW}} | 兩側只讀 · case=q_uid 由①②交叉參照縫合</div></div></header>
<div class="strip"></div>
<div class="gov">治理：SuperBOM (Q01/G01) 與 VMT (events.jsonl) 兩邊皆只讀，本工具不寫任何來源。case 以 q_uid 縫合：SBOM 隔離 intake → VMT 開追蹤/產信/回覆/結案 → SBOM 解除，全段可視化。</div>
<h2>KPI</h2><div class="cards">{{KPI}}</div>
<div class="line">系統事件分布：{{SYS}}</div>
<h2>🔥 跨系統瓶頸 (哪一段等最久)</h2>
<table><tr><th>流程轉移 (由 → 到)</th><th>次數</th><th>平均等待</th></tr>{{BN}}</table>
<h2>各案生命週期 (是否走完閉環)</h2>
<table><tr><th>q_uid</th><th>隔離原因</th><th>事件數</th><th>總工期</th><th>狀態</th></tr>{{LIFE}}</table>
<footer>vmt_superbom_eventstream v1.0 | 縫合鍵 q_uid↔ISS (①②) | 事件流可再餵 vmt_process_mining.py 做 PM4Py 級分析</footer>
</body></html>"""
    html = (html.replace("{{NOW}}", now).replace("{{KPI}}", kh).replace("{{SYS}}", sys_html)
                .replace("{{BN}}", bn_rows).replace("{{LIFE}}", life_rows))
    open(out_path, "w", encoding="utf-8").write(html)

# ------------------------------------------- 主流程 -------------------------
def main():
    ap = argparse.ArgumentParser(description="VMT x SuperBOM Event-Stream Unifier")
    ap.add_argument("--db", required=True, help="SuperBOM DuckDB 路徑")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    print("=" * 60)
    print("  VMT x SuperBOM Event-Stream Unifier v1.0  |  接縫③")
    print("=" * 60)
    if not os.path.exists(args.db):
        print("[SuperBOM] 找不到 DB:", args.db); return

    con = duckdb.connect(args.db, read_only=True)
    try:
        sbom_ev, quids = read_superbom(con)
    finally:
        con.close()
    vmt_ev = read_vmt_events(EVENT_PATH, quids)
    print("[縫合] SuperBOM 事件 %d / VMT 事件 %d / 隔離案(q_uid) %d" % (len(sbom_ev), len(vmt_ev), len(quids)))

    all_ev = sbom_ev + vmt_ev
    if not all_ev:
        print("[縫合] 無跨系統事件 (請先跑 ①②③ 產生 Q01/G01/events)")
    df = pd.DataFrame(all_ev, columns=["Case_ID", "Activity", "Timestamp", "Resource", "System"])
    if len(df):
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    edges, perf, durations = mine(df) if len(df) else ({}, {}, {})

    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, "event_log_unified.csv")
    df.sort_values("Timestamp").to_csv(csv_path, index=False, encoding="utf-8-sig") if len(df) else \
        open(csv_path, "w", encoding="utf-8-sig").write("Case_ID,Activity,Timestamp,Resource,System\n")
    rep = os.path.join(OUT_DIR, "UnifiedEventStream.html")
    build_html(df, edges, perf, durations, quids, rep)
    print("[輸出] 統一事件流 CSV:", csv_path)
    print("[輸出] 跨系統儀表板:", rep)
    # 印出跨系統瓶頸摘要
    bn = sorted(perf.items(), key=lambda kv: kv[1], reverse=True)
    for (a, b), sec in bn[:3]:
        cross = "跨系統" if SYS_OF.get(a) != SYS_OF.get(b) else "系統內"
        print("       瓶頸 %s: %s -> %s = %s" % (cross, a, b, hum(sec)))
    try:
        if os.name == "nt" and not args.no_open:
            os.startfile(rep)  # noqa
    except Exception:
        pass
    print("完成.")

if __name__ == "__main__":
    main()
