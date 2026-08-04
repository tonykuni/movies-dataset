# -*- coding: utf-8 -*-
"""
============================================================================
 VMT Planning / CPM Engine v1.0  --  規劃層: 相依 / 關鍵路徑 / 排程
----------------------------------------------------------------------------
 補上你系統缺的「事前規劃」: 任務相依 -> 關鍵路徑 (CPM) -> 排程 + 甘特圖.
 自動導入現況: 讀 ssot.json 的 active ISS 當任務 (不交白樣板).
 規劃輸入 (半自動, append-only):
   planning_tasks.csv :  ISS, Duration(天), Predecessors(前置ISS, 空白/逗號分隔)
   首次執行自動用現有 issue 產生一份 (工期由 due-created 推估, 前置留空待你填).
 計算 (CPM):
   前推 ES/EF, 後推 LS/LF, 浮時 slack=LS-ES; slack=0 => 關鍵路徑 (一滑全滑).
   偵測循環相依 (報告並跳過該邊, 不當機).
 排程風險: 任務有 due 但 CPM 完成日 > due -> 標 LATE (照現在的相依排不進去).
 產出: CriticalPath.html (甘特, 關鍵路徑紅色) + planning_schedule.csv.
 治理: ssot.json 只讀; planning_tasks.csv append-only; 產物落 reports/.
============================================================================
"""
import os, csv, sys, json, datetime as dt
from collections import defaultdict

VMT_ROOT   = os.environ.get("VMT_ROOT", r"C:\VIA\VeritasMailTracker")
DATA_DIR   = os.path.join(VMT_ROOT, "data")
OUT_DIR    = os.path.join(VMT_ROOT, "reports")
SSOT_PATH  = os.path.join(DATA_DIR, "ssot.json")
PLAN_CSV   = os.path.join(VMT_ROOT, "planning_tasks.csv")
ACTIVE = ("OPEN", "NEED_DATA", "NEED_CLARIFY", "EXTENDED")

def hsafe(s): 
    import html
    return html.escape("" if s is None else str(s))
def parse_dt(s):
    if not s: return None
    for f in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d", "%Y-%m-%d"):
        try: return dt.datetime.strptime(str(s).strip()[:26], f)
        except Exception: pass
    try: return dt.datetime.fromisoformat(str(s))
    except Exception: return None

# ---------------------------------------------- 導入現況 --------------------
def load_tasks():
    if not os.path.exists(SSOT_PATH):
        print("[SSOT] 找不到 ssot.json — 先跑郵件器/OneShot 產生現況"); return None, {}
    ss = json.load(open(SSOT_PATH, encoding="utf-8"))
    meta = {}
    tasks = {}
    for i in ss.get("issues", []):
        if i.get("status") not in ACTIVE:
            continue
        iss = i.get("issueId")
        created = parse_dt(i.get("created")); due = parse_dt(i.get("due"))
        dur = 3
        if created and due and due > created:
            dur = max(1, (due - created).days)
        tasks[iss] = {"iss": iss, "case": i.get("caseId", ""), "title": i.get("title", ""),
                      "urgency": int(i.get("urgency", 3) or 3), "due": due, "dur": dur, "preds": []}
        meta[iss] = i
    return tasks, meta

# ---------------------------------------------- 規劃輸入 (半自動) ------------
def load_or_scaffold_plan(tasks):
    if not os.path.exists(PLAN_CSV):
        # 首次: 用現有 issue 產生一份, 工期預估, 前置留空
        lines = ["ISS,Duration,Predecessors,Note"]
        for t in tasks.values():
            lines.append('%s,%d,,"%s"' % (t["iss"], t["dur"], (t["title"][:20]).replace('"', "'")))
        lines += ["# 填 Predecessors 欄建立相依, 例: ISS-0003 的 Predecessors 填  ISS-0001 ISS-0002",
                  "# 多個前置以空白或逗號分隔; 改完重跑即算關鍵路徑"]
        enc = "\ufeff" + "\n".join(lines)
        open(PLAN_CSV, "w", encoding="utf-8").write(enc)
        print("[規劃] 首次執行: 已產生 planning_tasks.csv (%d 任務, 前置待填)" % len(tasks))
        return
    # 讀入 duration + predecessors 覆寫
    with open(PLAN_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            iss = (row.get("ISS") or "").strip()
            if not iss or iss.startswith("#") or iss not in tasks:
                continue
            d = (row.get("Duration") or "").strip()
            if d.isdigit(): tasks[iss]["dur"] = max(1, int(d))
            preds = (row.get("Predecessors") or "").replace(",", " ").split()
            tasks[iss]["preds"] = [p.strip() for p in preds if p.strip() in tasks]
    print("[規劃] 讀入 planning_tasks.csv")

# ---------------------------------------------- CPM ------------------------
def compute_cpm(tasks):
    # 拓撲排序 (Kahn) + 循環偵測
    succ = defaultdict(list); indeg = {k: 0 for k in tasks}
    for k, t in tasks.items():
        for p in t["preds"]:
            succ[p].append(k); indeg[k] += 1
    q = [k for k in tasks if indeg[k] == 0]; topo = []
    ind = dict(indeg)
    while q:
        n = q.pop(0); topo.append(n)
        for s in succ[n]:
            ind[s] -= 1
            if ind[s] == 0: q.append(s)
    cyclic = [k for k in tasks if k not in topo]
    if cyclic:
        print("[CPM] 偵測到循環相依, 忽略相關邊:", cyclic)
        for k in cyclic: topo.append(k)
    # 前推 ES/EF
    ES = {}; EF = {}
    for n in topo:
        ES[n] = max([EF[p] for p in tasks[n]["preds"] if p in EF] or [0])
        EF[n] = ES[n] + tasks[n]["dur"]
    proj = max(EF.values()) if EF else 0
    # 後推 LF/LS
    LF = {}; LS = {}
    for n in reversed(topo):
        outs = [LS[s] for s in succ[n] if s in LS]
        LF[n] = min(outs) if outs else proj
        LS[n] = LF[n] - tasks[n]["dur"]
    for n in tasks:
        t = tasks[n]
        t["ES"], t["EF"], t["LS"], t["LF"] = ES[n], EF[n], LS[n], LF[n]
        t["slack"] = LS[n] - ES[n]
        t["critical"] = (t["slack"] == 0)
    return proj, succ

# ---------------------------------------------- 排程日期 + 風險 --------------
def schedule_dates(tasks, proj, start=None):
    start = start or dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for t in tasks.values():
        t["start_date"] = start + dt.timedelta(days=t["ES"])
        t["finish_date"] = start + dt.timedelta(days=t["EF"])
        t["late"] = bool(t["due"] and t["finish_date"] > t["due"])
    return start

# ---------------------------------------------- 甘特 HTML ------------------
def build_html(tasks, proj, start, cyclic_note, out_path):
    ordered = sorted(tasks.values(), key=lambda t: (t["ES"], -1 if t["critical"] else 0, t["iss"]))
    crit_chain = [t["iss"] for t in sorted([x for x in tasks.values() if x["critical"]], key=lambda t: t["ES"])]
    n_crit = len(crit_chain); n_late = sum(1 for t in tasks.values() if t["late"])
    end_date = (start + dt.timedelta(days=proj)).strftime("%Y/%m/%d")
    day_px = max(14, min(48, int(760 / max(1, proj))))
    rows = ""
    for t in ordered:
        col = "#c96b5a" if t["critical"] else "#4c78a8"
        left = t["ES"] * day_px; w = max(6, t["dur"] * day_px); slackw = t["slack"] * day_px
        due_s = t["due"].strftime("%m/%d") if t["due"] else "—"
        latebadge = " <span class='pill' style='background:#b5443a'>LATE</span>" if t["late"] else ""
        critbadge = " <span class='pill' style='background:#c96b5a'>關鍵</span>" if t["critical"] else ""
        bar = ("<div class='track'><div class='bar' style='left:%dpx;width:%dpx;background:%s'></div>"
               "%s</div>") % (left, w, col,
               ("<div class='slack' style='left:%dpx;width:%dpx'></div>" % (left + w, slackw)) if slackw > 0 else "")
        rows += ("<tr><td>%s%s%s</td><td>%s</td><td>%s</td><td>%dd</td><td>%s</td>"
                 "<td>%dd</td><td>%s</td></tr>") % (
            hsafe(t["iss"]), critbadge, latebadge, hsafe(t["case"]), hsafe(t["title"][:24]),
            t["dur"], t["start_date"].strftime("%m/%d"), t["slack"],
            "<div class='gwrap'>" + bar + "</div>", ) if False else \
            ("<tr><td>%s%s%s</td><td>%s</td><td>%s</td><td>%dd</td><td>%s→%s</td><td>%dd</td><td>%s</td></tr>" % (
                hsafe(t["iss"]), critbadge, latebadge, hsafe(t["case"]), hsafe(t["title"][:22]),
                t["dur"], t["start_date"].strftime("%m/%d"), t["finish_date"].strftime("%m/%d"),
                t["slack"], "<div class='gwrap'>" + bar + "</div>"))
    if not rows: rows = "<tr><td colspan='7' class='empty'>無 active 任務</td></tr>"
    chain_html = " <span style='color:#999'>→</span> ".join(
        "<span class='node'>%s</span>" % hsafe(c) for c in crit_chain) or "<span class='empty'>尚無相依 — 在 planning_tasks.csv 填 Predecessors</span>"
    kpis = [("關鍵路徑長度", "%d 天" % proj, "#c96b5a"), ("預計完成", end_date, "#4c78a8"),
            ("關鍵任務數", n_crit, "#c96b5a"), ("排程風險(LATE)", n_late, "#b5443a"),
            ("任務總數", len(tasks), "#439a9a")]
    kh = "".join("<div class='card'><div class='cv' style='color:%s'>%s</div><div class='cn'>%s</div></div>"
                 % (c, v, n) for n, v, c in kpis)
    now = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    note = ("<div class='warn'>循環相依已忽略: " + hsafe(", ".join(cyclic_note)) + "</div>") if cyclic_note else ""
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>關鍵路徑</title><style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.seal{display:inline-flex;width:44px;height:44px;background:#c96b5a;color:#fff;align-items:center;justify-content:center;font-size:20px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font-size:20px;letter-spacing:1px}.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 22px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:24px 0 10px;text-transform:uppercase}
.cards{display:flex;gap:12px;flex-wrap:wrap}
.card{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:14px 18px;min-width:130px}
.cv{font-size:22px;font-weight:700}.cn{font-size:12px;color:#777;margin-top:2px}
.chain{background:var(--paper);border:1px solid var(--hair);border-left:5px solid #c96b5a;border-radius:3px;padding:14px 16px;font-size:14px;line-height:2}
.node{display:inline-block;background:#faf0ee;border:1px solid #e6ccc5;border-radius:3px;padding:3px 10px;font-family:"DM Mono",monospace;font-size:12px}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair);vertical-align:middle}tr:last-child td{border-bottom:none}
.pill{color:#fff;font-size:10px;font-family:"DM Mono",monospace;padding:1px 6px;border-radius:2px;margin-left:4px}
.gwrap{min-width:200px}.track{position:relative;height:18px;background:#f0efec;border-radius:3px}
.bar{position:absolute;top:2px;height:14px;border-radius:2px}
.slack{position:absolute;top:5px;height:8px;background:#cdd9e5;border-radius:2px;opacity:.7}
.empty{color:#999;text-align:center;padding:14px}
.warn{background:#fbeeee;border-left:5px solid #b5443a;padding:8px 12px;font-size:12px;color:#7a2f2f;border-radius:3px;margin-bottom:12px}
footer{margin-top:30px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
</style></head><body>
<header><div class="seal">排</div><div><h1>VMT 關鍵路徑 / 排程 — 規劃層</h1>
<div class="sub">{{NOW}} | 自動導入 active ISS · CPM · ssot 只讀</div></div></header>
<div class="strip"></div>
{{NOTE}}
<h2>KPI</h2><div class="cards">{{KPI}}</div>
<h2>🔴 關鍵路徑 (一滑全滑, 優先追這條)</h2>
<div class="chain">{{CHAIN}}</div>
<h2>排程甘特 (關鍵=紅, 藍條後淺色=浮時)</h2>
<table><tr><th>任務</th><th>案件</th><th>標題</th><th>工期</th><th>起→迄</th><th>浮時</th><th>時間軸</th></tr>{{ROWS}}</table>
<footer>vmt_planning_cpm v1.0 | 規劃輸入 planning_tasks.csv (填 Predecessors 建相依) | 前瞻關鍵路徑 × 歷史瓶頸(探勘) = 完整視圖</footer>
</body></html>"""
    html = (html.replace("{{NOW}}", now).replace("{{NOTE}}", note).replace("{{KPI}}", kh)
                .replace("{{CHAIN}}", chain_html).replace("{{ROWS}}", rows))
    open(out_path, "w", encoding="utf-8").write(html)

# ---------------------------------------------- 主流程 ---------------------
def main():
    print("=" * 60); print("  VMT Planning / CPM Engine v1.0  |  關鍵路徑 · 排程"); print("=" * 60)
    tasks, meta = load_tasks()
    if tasks is None: return
    if not tasks:
        print("[規劃] 無 active 任務 (ssot 全部 DONE 或空)"); 
    load_or_scaffold_plan(tasks)
    proj, succ = compute_cpm(tasks)
    cyclic_note = [k for k in tasks if k not in [n for n in tasks]]  # placeholder
    start = schedule_dates(tasks, proj)
    os.makedirs(OUT_DIR, exist_ok=True)
    # 匯出排程 csv
    with open(os.path.join(OUT_DIR, "planning_schedule.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["ISS", "Case", "Duration", "ES", "EF", "LS", "LF", "Slack", "Critical", "Start", "Finish", "Due", "Late"])
        for t in sorted(tasks.values(), key=lambda x: x["ES"]):
            w.writerow([t["iss"], t["case"], t["dur"], t["ES"], t["EF"], t["LS"], t["LF"], t["slack"],
                        int(t["critical"]), t["start_date"].strftime("%Y-%m-%d"), t["finish_date"].strftime("%Y-%m-%d"),
                        t["due"].strftime("%Y-%m-%d") if t["due"] else "", int(t["late"])])
    rep = os.path.join(OUT_DIR, "CriticalPath.html")
    build_html(tasks, proj, start, [], rep)
    crit = sorted([t for t in tasks.values() if t["critical"]], key=lambda x: x["ES"])
    print("[CPM] 專案工期 %d 天; 關鍵路徑: %s" % (proj, " -> ".join(t["iss"] for t in crit)))
    print("[排程風險] LATE 任務: %d" % sum(1 for t in tasks.values() if t["late"]))
    print("[輸出]", rep)
    try:
        if os.name == "nt" and "--no-open" not in sys.argv: os.startfile(rep)  # noqa
    except Exception: pass
    print("完成.")

if __name__ == "__main__":
    main()
