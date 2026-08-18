# -*- coding: utf-8 -*-
"""
============================================================================
 VMT Process Mining Engine v1.0  --  郵件追蹤流程探勘引擎
 (VeritasMailTracker 的 [E3] Process Mining 引擎, PMBOK 對接版)
----------------------------------------------------------------------------
 三大黃金欄位:  Case ID  /  Activity  /  Timestamp
 資料來源優先序 (自動偵測, 全程本地端):
   1. 本機 Outlook 收件匣 (win32com) -- 讀取「你自己已登入」的信箱, 指定日期區間
   2. VeritasMailTracker 產物  events.jsonl + ssot.json (與 v1 腳本直接串接)
   3. 控制表 control_sheet.csv / .xlsx  (Case_ID, Activity, Timestamp[, Resource])
   4. 皆無 -> 產生範例事件流以供展示
 探勘核心:
   - PM4Py (若已安裝): DFG 流程圖 + 效能 DFG (活動間等待時間) + 變體 + 案件工期
   - 無 PM4Py 時: pandas 純手算 DFG + 等待時間, 結果一致可用
 輸出:  Visual Lock 風格 HTML 儀表板 (瓶頸熱點 / 等待時間 / 案件工期 / 活動頻率)
 治理:  只讀不改來源信箱; 產物只增不減; 全程本地, 不外送
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
import os, re, sys, json, html, glob, datetime as dt
from collections import defaultdict, Counter

try:
    import pandas as pd
except Exception:
    print("需要 pandas:  pip install pandas"); sys.exit(1)

# ---------------------------------------------------------------- 設定 ------
VMT_ROOT   = os.environ.get("VMT_ROOT", r"C:\VIA\VeritasMailTracker")
OUT_DIR    = os.path.join(VMT_ROOT, "reports")
# Outlook 抓取區間 (可改); 預設近 90 天
DAYS_BACK  = int(os.environ.get("VMT_DAYS_BACK", "90"))
# 從主旨萃取 Case ID 的樣式: 相容 v1 郵件格式 [CASE-03] / [Case 3] / 案號 003
CASE_PATTERNS = [r"\[CASE[-\s]?0*(\d{1,3})\]", r"\[Case\s*0*(\d{1,3})\]", r"案號\s*0*(\d{1,3})"]

def norm_case(raw):
    """把任何形式的案號正規化為 CASE-XX"""
    if raw is None: return None
    s = str(raw)
    for pat in CASE_PATTERNS:
        m = re.search(pat, s, re.IGNORECASE)
        if m:
            return "CASE-%02d" % int(m.group(1))
    m = re.search(r"CASE-(\d{2,3})", s, re.IGNORECASE)
    if m: return "CASE-%02d" % int(m.group(1))
    return None

def classify_activity(subject, from_self):
    """依主旨標記 / 關鍵字 + 寄收方向, 映射為流程活動節點"""
    s = subject or ""
    if ("🔴" in s) or ("延遲" in s) or ("警告" in s) or ("Warning" in s):
        return "③ 延遲警告寄出" if from_self else "④ 收到延遲回覆"
    if ("🟠" in s) or ("提醒" in s) or ("Reminder" in s):
        return "② 晨間提醒寄出" if from_self else "④ 對方回覆"
    if ("核准" in s) or ("approve" in s.lower()) or ("同意" in s):
        return "⑦ 主管核准"
    if ("完成" in s) or ("已交付" in s) or ("done" in s.lower()):
        return "⑨ 結案收斂"
    if from_self:
        return "① 跟進寄出"
    return "④ 對方回覆"

# ---------------------------------------------- 來源 1: 本機 Outlook -----------
def load_from_outlook():
    """讀取本機已登入的 Outlook 收件匣 (你自己的信箱), 指定日期區間.
    僅在 Windows + 已安裝 Outlook + pywin32 時可用; 其他環境自動略過."""
    try:
        import win32com.client
        import pywintypes
    except Exception:
        return None
    try:
        ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = ns.GetDefaultFolder(6)          # 6 = 收件匣
        items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        me = ""
        try: me = ns.CurrentUser.Name
        except Exception: pass
        cutoff = dt.datetime.now() - dt.timedelta(days=DAYS_BACK)
        # Restrict 加速 (伺服器不涉入, 純本機快取查詢)
        flt = "[ReceivedTime] >= '" + cutoff.strftime("%m/%d/%Y %H:%M %p") + "'"
        try: items = items.Restrict(flt)
        except Exception: pass
        rows = []
        for m in items:
            try:
                if getattr(m, "Class", None) != 43:  # 43 = MailItem
                    continue
                subj = m.Subject or ""
                case = norm_case(subj)
                if not case:
                    continue
                sender = ""
                try: sender = m.SenderName or ""
                except Exception: pass
                from_self = bool(me) and (me.strip() == sender.strip())
                ts = m.ReceivedTime
                ts = dt.datetime(ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second)
                rows.append({
                    "Case_ID": case,
                    "Activity": classify_activity(subj, from_self),
                    "Timestamp": ts,
                    "Resource": sender or ("SELF" if from_self else "OTHER"),
                    "Subject": subj,
                })
            except Exception:
                continue
        if not rows:
            return None
        print("[來源] 本機 Outlook 收件匣: 擷取 %d 筆含案號郵件 (近 %d 天)" % (len(rows), DAYS_BACK))
        return pd.DataFrame(rows)
    except Exception as e:
        print("[來源] Outlook 讀取略過:", e)
        return None

# -------------------------------------- 來源 2: VMT events.jsonl + ssot -------
def load_from_vmt():
    ev_path = os.path.join(VMT_ROOT, "data", "events.jsonl")
    ss_path = os.path.join(VMT_ROOT, "data", "ssot.json")
    if not os.path.exists(ev_path):
        return None
    # 建 ISS -> CASE 對照
    iss2case = {}
    if os.path.exists(ss_path):
        try:
            ss = json.load(open(ss_path, encoding="utf-8"))
            for it in ss.get("issues", []):
                iss2case[it.get("issueId")] = it.get("caseId")
        except Exception:
            pass
    act_map = {
        "ISSUE_NEW": "⓪ 問題登錄",
        "MAIL_GEN":  "① 跟進寄出",
        "ISSUE_DONE":"⑨ 結案收斂",
    }
    rows = []
    for line in open(ev_path, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: e = json.loads(line)
        except Exception: continue
        evt = e.get("event"); ref = e.get("ref"); detail = e.get("detail", "")
        if evt not in act_map: continue
        case = iss2case.get(ref) or norm_case(ref) or norm_case(detail)
        if not case: continue
        try: ts = dt.datetime.fromisoformat(e.get("ts"))
        except Exception: continue
        if ts.tzinfo: ts = ts.replace(tzinfo=None)
        rows.append({"Case_ID": case, "Activity": act_map[evt], "Timestamp": ts, "Resource": "VMT", "Subject": detail})
    if not rows:
        return None
    print("[來源] VeritasMailTracker events.jsonl: %d 筆事件" % len(rows))
    return pd.DataFrame(rows)

# -------------------------------------- 來源 3: 控制表 CSV / XLSX -------------
def load_from_control():
    for p in glob.glob(os.path.join(VMT_ROOT, "control_sheet.*")) + glob.glob("control_sheet.*"):
        try:
            df = pd.read_excel(p) if p.lower().endswith((".xlsx", ".xls")) else pd.read_csv(p)
            cols = {c.lower().strip(): c for c in df.columns}
            cid = cols.get("case_id") or cols.get("caseid") or cols.get("案號")
            act = cols.get("activity") or cols.get("活動")
            tsc = cols.get("timestamp") or cols.get("時間")
            if not (cid and act and tsc): continue
            out = pd.DataFrame({
                "Case_ID":  df[cid].map(norm_case),
                "Activity": df[act].astype(str),
                "Timestamp":pd.to_datetime(df[tsc], errors="coerce"),
                "Resource": df[cols["resource"]] if "resource" in cols else "SHEET",
                "Subject":  "",
            }).dropna(subset=["Case_ID", "Timestamp"])
            if len(out):
                print("[來源] 控制表 %s: %d 筆" % (os.path.basename(p), len(out)))
                return out
        except Exception:
            continue
    return None

# -------------------------------------- 來源 4: 範例事件流 --------------------
def load_sample():
    print("[來源] 無真實資料 -> 產生範例事件流 (展示瓶頸偵測)")
    base = dt.datetime(2026, 7, 6, 20, 0, 0)
    rows = []
    def add(case, act, day_off, hour):
        rows.append({"Case_ID": case, "Activity": act,
                     "Timestamp": base + dt.timedelta(days=day_off, hours=hour),
                     "Resource": "SELF", "Subject": act})
    # 三個案件, 刻意製造「等對方回覆」的長等待瓶頸
    for c, delay in [("CASE-03", 3.0), ("CASE-07", 2.5), ("CASE-01", 0.4)]:
        add(c, "⓪ 問題登錄", 0, 0)
        add(c, "① 跟進寄出", 0, 0.2)
        add(c, "② 晨間提醒寄出", 1, 12)
        rows.append({"Case_ID": c, "Activity": "④ 對方回覆",
                     "Timestamp": base + dt.timedelta(days=1+delay, hours=13),
                     "Resource": "OTHER", "Subject": "回覆"})
        rows.append({"Case_ID": c, "Activity": "⑦ 主管核准",
                     "Timestamp": base + dt.timedelta(days=1+delay, hours=20),
                     "Resource": "MGR", "Subject": "核准"})
        rows.append({"Case_ID": c, "Activity": "⑨ 結案收斂",
                     "Timestamp": base + dt.timedelta(days=2+delay, hours=10),
                     "Resource": "SELF", "Subject": "結案"})
    return pd.DataFrame(rows)

# ------------------------------------------------ 探勘: pandas 手算 -----------
def mine_pandas(df):
    df = df.sort_values("Timestamp").reset_index(drop=True)
    edges = Counter()           # (a,b) -> 次數
    wait  = defaultdict(list)   # (a,b) -> 等待秒數清單
    durations = {}
    act_freq = Counter(df["Activity"])
    for case, g in df.groupby("Case_ID"):
        g = g.sort_values("Timestamp")
        acts = list(g["Activity"]); ts = list(g["Timestamp"])
        durations[case] = (ts[-1] - ts[0]).total_seconds()
        for i in range(len(acts) - 1):
            e = (acts[i], acts[i+1])
            edges[e] += 1
            wait[e].append((ts[i+1] - ts[i]).total_seconds())
    perf = {e: (sum(w)/len(w)) for e, w in wait.items()}
    starts = Counter(); ends = Counter()
    for case, g in df.groupby("Case_ID"):
        g = g.sort_values("Timestamp")
        starts[g["Activity"].iloc[0]] += 1
        ends[g["Activity"].iloc[-1]] += 1
    return edges, perf, durations, act_freq, dict(starts), dict(ends)

# ------------------------------------------------ 探勘: PM4Py -----------------
def mine_pm4py(df):
    try:
        import pm4py
    except Exception:
        return None
    try:
        d = df.rename(columns={"Case_ID": "case:concept:name",
                               "Activity": "concept:name",
                               "Timestamp": "time:timestamp"}).copy()
        d["time:timestamp"] = pd.to_datetime(d["time:timestamp"])
        freq_dfg, starts, ends = pm4py.discover_dfg(d)
        perf_dfg, _, _ = pm4py.discover_performance_dfg(d)
        # perf_dfg 值可能是 dict(含 mean) 或直接秒數
        perf = {}
        for e, v in perf_dfg.items():
            perf[e] = v.get("mean", 0) if isinstance(v, dict) else float(v)
        durations = {}
        for case, g in df.groupby("Case_ID"):
            g = g.sort_values("Timestamp")
            durations[case] = (g["Timestamp"].iloc[-1] - g["Timestamp"].iloc[0]).total_seconds()
        act_freq = Counter(df["Activity"])
        print("[引擎] PM4Py %s: DFG %d 邊 / 效能 DFG 已算" % (pm4py.__version__, len(freq_dfg)))
        return dict(freq_dfg), perf, durations, act_freq, dict(starts), dict(ends)
    except Exception as e:
        print("[引擎] PM4Py 探勘失敗, 改用 pandas:", e)
        return None

# ------------------------------------------------ 工具 -----------------------
def hum_dur(sec):
    sec = float(sec)
    d = int(sec // 86400); h = int((sec % 86400) // 3600); m = int((sec % 3600) // 60)
    if d: return "%dd %dh" % (d, h)
    if h: return "%dh %dm" % (h, m)
    return "%dm" % m

VLOCK_CSS = """
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;--blue:#4c78a8;--teal:#439a9a;--red:#c96b5a;--grn:#5a9e6f;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.seal{display:inline-flex;width:44px;height:44px;background:#3a6491;color:#fff;align-items:center;justify-content:center;font-size:22px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px;margin-bottom:8px}
h1{font-size:21px;letter-spacing:1px}
.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 22px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:26px 0 10px;text-transform:uppercase}
.kpis{display:flex;gap:12px;flex-wrap:wrap}
.kpi{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:14px 20px;min-width:150px}
.kv{font-size:24px;font-weight:700}.kn{font-size:12px;color:#777;margin-top:2px}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666;letter-spacing:1px}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair)}
tr:last-child td{border-bottom:none}
.bar{height:14px;background:var(--blue);border-radius:2px;display:inline-block;vertical-align:middle}
.barwait{height:14px;border-radius:2px;display:inline-block;vertical-align:middle}
.flow{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:16px;font-size:13px;line-height:2.4}
.node{display:inline-block;background:#eef2f6;border:1px solid #cdd9e5;border-radius:3px;padding:3px 10px;margin:2px;font-size:12px}
.arr{color:#999;margin:0 4px}.warn{color:var(--red);font-weight:700}
.pm{background:var(--paper);border:1px solid var(--hair);border-left:5px solid var(--teal);border-radius:3px;padding:12px 16px;margin-bottom:8px;font-size:13px}
.pml{font-family:"DM Mono",monospace;font-size:11px;color:var(--teal);font-weight:700}
footer{margin-top:30px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
.empty{color:#999;text-align:center;padding:16px}
"""

def build_html(df, edges, perf, durations, act_freq, starts, ends, engine):
    n_cases = df["Case_ID"].nunique(); n_ev = len(df)
    avg_dur = sum(durations.values())/len(durations) if durations else 0
    # 瓶頸: 依平均等待時間排序
    bn = sorted(perf.items(), key=lambda kv: kv[1], reverse=True)
    top_wait = bn[0][1] if bn else 1
    bn_rows = ""
    for (a, b), sec in bn[:12]:
        w = max(4, int(200 * (sec / top_wait))) if top_wait else 4
        col = "var(--red)" if sec >= avg_dur*0.4 and sec > 0 else "var(--blue)"
        cnt = edges.get((a, b), "")
        bn_rows += ("<tr><td>%s <span class='arr'>&rarr;</span> %s</td><td>%s</td>"
                    "<td><span class='barwait' style='width:%dpx;background:%s'></span> %s</td></tr>"
                    % (html.escape(a), html.escape(b), cnt, w, col, hum_dur(sec)))
    if not bn_rows: bn_rows = "<tr><td colspan='3' class='empty'>無轉移</td></tr>"
    # 活動頻率
    mx = max(act_freq.values()) if act_freq else 1
    af_rows = ""
    for a, c in act_freq.most_common():
        af_rows += ("<tr><td>%s</td><td><span class='bar' style='width:%dpx'></span> %d</td></tr>"
                    % (html.escape(a), int(200*c/mx), c))
    # 案件工期 (最久滯留)
    du_rows = ""
    for case, sec in sorted(durations.items(), key=lambda kv: kv[1], reverse=True)[:14]:
        flag = " <span class='warn'>&#9888; 瓶頸</span>" if sec >= avg_dur*1.3 else ""
        du_rows += "<tr><td>%s</td><td>%s%s</td></tr>" % (html.escape(case), hum_dur(sec), flag)
    if not du_rows: du_rows = "<tr><td colspan='2' class='empty'>無資料</td></tr>"
    # 主要變體流 (最常見路徑)
    variant_counter = Counter()
    for case, g in df.groupby("Case_ID"):
        seq = tuple(g.sort_values("Timestamp")["Activity"])
        variant_counter[seq] += 1
    flow_html = ""
    for seq, c in variant_counter.most_common(3):
        nodes = " <span class='arr'>&rarr;</span> ".join("<span class='node'>%s</span>" % html.escape(x) for x in seq)
        flow_html += "<div>%s <span style='color:#999'>&times;%d 案</span></div>" % (nodes, c)
    if not flow_html: flow_html = "<div class='empty'>無變體</div>"

    # PMBOK 對接卡
    pmbok = [
        ("進度控制 / 變異分析", "上方「等待時間瓶頸」= 每個交接點的實際 Lead Time, 紅色即逾常"),
        ("品質管理 / 一致性檢查", "主要變體流 vs 你的標準 SOP, 出現繞道或缺節點即偏差"),
        ("風險管理 / 預測", "案件工期 &ge; 平均 1.3 倍標記瓶頸, 提前兩天即可示警主管"),
        ("資源管理 / 組織挖掘", "Resource 欄 (SELF/OTHER/MGR) 顯示交接落在誰身上"),
    ]
    pm_html = "".join("<div class='pm'><span class='pml'>%s</span><br>%s</div>" % (t, d) for t, d in pmbok)

    kpi = [("案件數", n_cases, "var(--blue)"), ("事件總數", n_ev, "var(--teal)"),
           ("平均案件工期", hum_dur(avg_dur), "var(--red)"),
           ("最長瓶頸等待", hum_dur(bn[0][1]) if bn else "-", "var(--red)"),
           ("探勘引擎", engine, "var(--grn)")]
    kpi_html = "".join("<div class='kpi'><div class='kv' style='color:%s'>%s</div><div class='kn'>%s</div></div>"
                       % (c, v, n) for n, v, c in kpi)
    now = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    return """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VMT 流程探勘</title><style>%s</style></head><body>
<header><div class="seal">探</div><div><h1>VMT 流程探勘儀表板 &mdash; 真實郵件流程 X 光</h1>
<div class="sub">CASE ID / ACTIVITY / TIMESTAMP | %s | 引擎: %s | 全程本地</div></div></header>
<div class="strip"></div>
<h2>KPI 總覽</h2><div class="kpis">%s</div>
<h2>&#128293; 等待時間瓶頸 (交接點實際 Lead Time, 由長到短)</h2>
<table><tr><th>流程轉移 (由 &rarr; 到)</th><th>次數</th><th>平均等待</th></tr>%s</table>
<h2>主要變體流 (最常走的實際路徑)</h2><div class="flow">%s</div>
<h2>案件工期 &mdash; 滯留最久 Top 14</h2><table><tr><th>案件</th><th>總工期</th></tr>%s</table>
<h2>活動頻率</h2><table><tr><th>活動節點</th><th>次數</th></tr>%s</table>
<h2>PMBOK 對接</h2>%s
<footer>VMT Process Mining Engine v1.0 | 資料只讀不改 | 產物只增不減 | 可再匯入 PM4Py / bupaR 做進階分析</footer>
</body></html>""" % (VLOCK_CSS, now, engine, kpi_html, bn_rows, flow_html, du_rows, af_rows, pm_html)

# ------------------------------------------------ 主流程 ---------------------
def main():
    print("=" * 60)
    print("  VMT Process Mining Engine v1.0  |  郵件流程探勘")
    print("=" * 60)
    df = load_from_outlook()
    if df is None: df = load_from_vmt()
    if df is None: df = load_from_control()
    if df is None: df = load_sample()
    df = df.dropna(subset=["Case_ID", "Timestamp"]).copy()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    print("[事件log] %d 筆 / %d 案件 / %d 種活動" %
          (len(df), df["Case_ID"].nunique(), df["Activity"].nunique()))

    res = mine_pm4py(df)
    engine = "PM4Py"
    if res is None:
        res = mine_pandas(df); engine = "pandas 內建"
        print("[引擎] 使用 pandas 內建探勘 (未偵測到 PM4Py)")
    edges, perf, durations, act_freq, starts, ends = res

    os.makedirs(OUT_DIR, exist_ok=True)
    # 匯出乾淨事件log供 PM4Py / bupaR 進階使用
    ev_csv = os.path.join(OUT_DIR, "event_log.csv")
    df.sort_values("Timestamp").to_csv(ev_csv, index=False, encoding="utf-8-sig")
    html_out = build_html(df, edges, perf, durations, act_freq, starts, ends, engine)
    rep = os.path.join(OUT_DIR, "ProcessMining.html")
    with open(rep, "w", encoding="utf-8") as f:
        f.write(html_out)
    print("[輸出] 事件log:", ev_csv)
    print("[輸出] 儀表板:", rep)
    # 自動開啟 (Windows)
    try:
        if os.name == "nt" and "--no-open" not in sys.argv:
            os.startfile(rep)  # noqa
    except Exception:
        pass
    print("完成.")

if __name__ == "__main__":
    main()
