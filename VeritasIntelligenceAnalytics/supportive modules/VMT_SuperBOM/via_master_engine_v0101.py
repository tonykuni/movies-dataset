# -*- coding: utf-8 -*-
"""
============================================================================
 VIA Master Engine v1.0  --  一支 Python 主引擎 + 一份 JSON 參數, 整合全部
----------------------------------------------------------------------------
 做兩件事:
 [1] 整合接線 (真正的 integrate, 不只是串跑):
     - 讀問卷 overrides_*.json -> 自動改寫 convergence_params.json 門檻
       (auto_accept + delta, max_questions_per_round)  => 問卷填完即生效
     - 合併所有使用者的 domain 詞庫 (labels / warning_keywords / attach_keywords)
       -> data/domain_keywords.json, 供分類器/附件路由/郵件器取用
 [2] 管線執行: 依 JSON stages 順序跑全部引擎 (survey→attach→①OUT→reply→①IN→
     收斂→③→探勘→CPM), 缺 DB/缺檔/失敗都優雅略過並誠實記錄, 不中斷整條.
 產出: reports/MasterRun.html (Visual Lock 總覽) + data/master_state.json.
 v0101: 報告刊頭對齊 Veritas 設計鎖(郵章 · Cormorant 字標 · 七段 reson 帶);邏輯與 v1.0 完全相同.
 治理: 只讀來源; 寫入僅限 convergence_params.json(接線) 與自家產物; append-only.
============================================================================
"""
import os, re, sys, json, glob, html, subprocess, datetime as dt

def hsafe(s): return html.escape("" if s is None else str(s))

# ---------------------------------------------------------------- 參數 ------
def load_params():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "via_master_params.json")
    cfg = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    root = os.environ.get("VMT_ROOT") or cfg.get("paths", {}).get("vmt_root") or r"C:\VIA\VeritasMailTracker"
    cfg.setdefault("paths", {})["vmt_root"] = root
    if not cfg["paths"].get("engines_dir"):
        cfg["paths"]["engines_dir"] = here
    return cfg, here

def P(cfg, *keys, default=None):
    cur = cfg
    for k in keys:
        if not isinstance(cur, dict) or k not in cur: return default
        cur = cur[k]
    return cur

# ------------------------------------------------ [1] 整合接線 --------------
def wire_overrides(cfg, root, log):
    if not P(cfg, "integration", "apply_survey_overrides", default=True):
        return
    ov_glob = os.path.join(root, P(cfg, "integration", "overrides_glob", default="data/overrides_*.json"))
    ovs = []
    for p in sorted(glob.glob(ov_glob)):
        try: ovs.append((os.path.basename(p), json.load(open(p, encoding="utf-8"))))
        except Exception: pass
    if not ovs:
        log.append(("wire", "SKIP", "無 overrides (問卷未填) — 用預設參數"))
        return
    # 多使用者: 取最保守 auto_accept delta (最大值=最謹慎), 最小 max_questions
    deltas = [o.get("convergence", {}).get("auto_accept_delta", 0.0) for _, o in ovs]
    maxqs  = [o.get("convergence", {}).get("max_questions_per_round", 5) for _, o in ovs]
    delta = max(deltas); maxq = min(maxqs)
    # 改寫 convergence_params.json (引擎旁)
    eng_dir = P(cfg, "paths", "engines_dir")
    cp_path = os.path.join(eng_dir, "convergence_params.json")
    if P(cfg, "integration", "wire_convergence_thresholds", default=True) and os.path.exists(cp_path):
        cp = json.load(open(cp_path, encoding="utf-8"))
        base = 0.80
        cp.setdefault("confidence", {})["auto_accept"] = round(min(0.95, max(0.55, base + delta)), 2)
        cp["confidence"]["max_questions_per_round"] = int(maxq)
        cp.setdefault("_wired", {})["from_overrides"] = [n for n, _ in ovs]
        cp["_wired"]["at"] = dt.datetime.now().isoformat()
        json.dump(cp, open(cp_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        log.append(("wire", "OK", "convergence: auto_accept=%.2f (delta %+0.2f), 問題預算=%d, 來源=%d 份問卷" %
                    (cp["confidence"]["auto_accept"], delta, maxq, len(ovs))))
    # 合併 domain 詞庫
    if P(cfg, "integration", "wire_domain_keywords", default=True):
        merged = {}
        for _, o in ovs:
            for k, v in (o.get("domain") or {}).items():
                if isinstance(v, list):
                    merged.setdefault(k, [])
                    for x in v:
                        if x not in merged[k]: merged[k].append(x)
                else:
                    merged[k] = v
        kw_out = os.path.join(root, P(cfg, "integration", "domain_keywords_out", default="data/domain_keywords.json"))
        os.makedirs(os.path.dirname(kw_out), exist_ok=True)
        json.dump({"generated": dt.datetime.now().isoformat(), "users": [n for n, _ in ovs],
                   "domain": merged}, open(kw_out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        nkw = sum(len(v) for v in merged.values() if isinstance(v, list))
        log.append(("wire", "OK", "domain 詞庫合併: %d 鍵 / %d 詞 -> %s" %
                    (len(merged), nkw, os.path.basename(kw_out))))

# ------------------------------------------------ [2] 管線執行 --------------
BANNER = re.compile(r"PM4Py|License|Welcome|Docs|processintelligence|Business|Open-Source|https?://|^=+$")

def run_stage(cfg, root, st, log):
    eng_dir = P(cfg, "paths", "engines_dir")
    script = os.path.join(eng_dir, st["script"])
    if not os.path.exists(script):
        log.append((st["id"], "MISSING", st["script"])); return
    sbom = P(cfg, "paths", "sbom_db", default="superbom.duckdb")
    if not os.path.isabs(sbom): sbom = os.path.join(root, sbom)
    parser = P(cfg, "paths", "parser", default="")
    if parser and not os.path.isabs(parser):
        cand = os.path.join(eng_dir, parser)
        parser = cand if os.path.exists(cand) else os.path.join(root, parser)
    if st.get("needs_db") and not os.path.exists(sbom):
        log.append((st["id"], "SKIP", "無 SuperBOM DB (%s)" % os.path.basename(sbom))); return
    args = [a.replace("{sbom_db}", sbom).replace("{parser}", parser) for a in st.get("args", [])]
    env = dict(os.environ); env["VMT_ROOT"] = root
    t0 = dt.datetime.now()
    try:
        r = subprocess.run([sys.executable, script] + args + ["--no-open"],
                           capture_output=True, text=True, env=env,
                           timeout=P(cfg, "run", "timeout_sec_per_stage", default=180))
        sec = (dt.datetime.now() - t0).total_seconds()
        lines = [l.strip() for l in (r.stdout + "\n" + r.stderr).splitlines()
                 if l.strip() and not BANNER.search(l)]
        tail = lines[-1] if lines else ""
        # 找比「完成.」更有資訊量的一行
        for l in reversed(lines):
            if any(k in l for k in ("[分級", "[CPM", "[結果", "[縫合", "[OUT", "[IN ", "[寫回", "[評分", "[事件log")):
                tail = l; break
        status = "OK" if r.returncode == 0 else "FAIL"
        log.append((st["id"], status, "%s (%.1fs)" % (tail[:110], sec)))
    except subprocess.TimeoutExpired:
        log.append((st["id"], "TIMEOUT", "超過 %ds" % P(cfg, "run", "timeout_sec_per_stage", default=180)))
    except Exception as e:
        log.append((st["id"], "FAIL", str(e)[:110]))

# ------------------------------------------------ 報告 ----------------------
def build_report(cfg, root, log, out_html):
    col = {"OK": "#5a9e6f", "SKIP": "#8a857c", "MISSING": "#8a857c", "FAIL": "#b5443a", "TIMEOUT": "#b5443a", "wire": "#439a9a"}
    stage_desc = {s["id"]: s.get("desc", "") for s in P(cfg, "stages", default=[])}
    rows = ""
    for sid, status, detail in log:
        c = col.get(status, col.get(sid, "#999"))
        rows += ("<tr><td><span class='pill' style='background:%s'>%s</span></td><td>%s</td><td>%s</td><td>%s</td></tr>"
                 % (c, hsafe(status), hsafe(sid), hsafe(stage_desc.get(sid, "整合接線")), hsafe(detail)))
    ok = sum(1 for _, s, _ in log if s == "OK")
    tot = sum(1 for sid, _, _ in log if sid != "wire")
    # 儀表板連結卡
    reports = [("Dashboard.html", "郵件儀表板"), ("ConfirmationQueue.html", "收斂確認佇列"),
               ("SurveyForm.html", "上手問卷"), ("ReplyForm.html", "回覆表"), ("ReplyLoop.html", "回覆閉環"),
               ("SuperBOM_Bridge.html", "隔離橋"), ("AttachmentRouter.html", "附件路由"),
               ("UnifiedEventStream.html", "統一事件流"), ("ProcessMining.html", "流程探勘"),
               ("CriticalPath.html", "關鍵路徑/甘特")]
    cards = ""
    for f, n in reports:
        exists = os.path.exists(os.path.join(root, "reports", f))
        cls = "rc" if exists else "rc off"
        href = f if exists else "#"
        miss = "" if exists else "<span class='miss'>未產生</span>"
        cards += "<a class='%s' href='%s'><div class='rn'>%s%s</div></a>" % (cls, hsafe(href), hsafe(n), miss)
    nows = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    page = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>Master Run</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Noto+Serif+TC:wght@600&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet"><style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--ink2:#33403f;--mut:#6b6860;--hair:#dbd9d3;--blue:#4c78a8;
--serif:"Cormorant Garamond",Georgia,serif;--cjkserif:"Noto Serif TC","Noto Serif CJK TC","PMingLiU",serif;
--reson:linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.eyebrow{display:flex;align-items:center;gap:9px;margin-bottom:9px}
.chip{padding:2px 8px;background:var(--ink);color:#fff;font:700 10px "DM Mono",monospace;letter-spacing:.14em}
.ey{font:700 10px "DM Mono",monospace;letter-spacing:.13em;color:var(--mut);text-transform:uppercase}
.seal{display:inline-flex;width:44px;height:44px;background:var(--ink);color:#f2f1ec;align-items:center;justify-content:center;font-family:var(--cjkserif);font-size:23px;border-radius:4px;margin-right:14px;flex:none}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font:600 23px/1.2 var(--serif);letter-spacing:.07em}
.wmcjk{font:600 11px var(--cjkserif);letter-spacing:.22em;color:var(--mut);margin-top:2px}
.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:4px}
.strip{height:4px;background:var(--reson);margin:14px 0 20px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:22px 0 10px;text-transform:uppercase}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair)}tr:last-child td{border-bottom:none}
.pill{color:#fff;font-size:11px;font-family:"DM Mono",monospace;padding:2px 8px;border-radius:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}
.rc{display:block;background:var(--paper);border:1px solid var(--hair);border-radius:4px;padding:14px;text-decoration:none;color:var(--ink)}
.rc:hover{border-color:var(--blue)}.rc.off{opacity:.45;pointer-events:none}
.rn{font-size:13px}.miss{font-size:10px;color:#b5443a;font-family:"DM Mono",monospace;margin-left:6px}
footer{margin-top:26px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
</style></head><body>
<div class="eyebrow"><span class="chip">v0101</span><span class="ey">Veritas Intelligence Analytics · Mail Tracker</span></div>
<header><div class="seal">郵</div><div><h1>VERITAS MAIL TRACKER — 整合執行總覽</h1>
<div class="wmcjk">維里塔斯 · 郵件追蹤 · 主引擎總覽</div>
<div class="sub">{{NOW}} · 引擎 {{OK}}/{{TOT}} OK · 問卷接線自動生效 · 參數 via_master_params.json</div></div></header>
<div class="strip"></div>
<h2>接線 + 管線</h2>
<table><tr><th>狀態</th><th>階段</th><th>說明</th><th>結果</th></tr>{{ROWS}}</table>
<h2>儀表板入口</h2><div class="grid">{{CARDS}}</div>
<footer>via_master_engine v0101 (logic = v1.0) | 一份 JSON 管全部 | 缺件優雅略過、誠實記錄 | Veritas 設計鎖刊頭</footer>
</body></html>"""
    page = (page.replace("{{NOW}}", nows).replace("{{OK}}", str(ok)).replace("{{TOT}}", str(tot))
                .replace("{{ROWS}}", rows).replace("{{CARDS}}", cards))
    open(out_html, "w", encoding="utf-8").write(page)

# ------------------------------------------------ 主流程 --------------------
def main():
    cfg, here = load_params()
    root = P(cfg, "paths", "vmt_root")
    print("=" * 62)
    print("  VIA Master Engine v1.0  |  一支主引擎 + 一份 JSON 整合全部")
    print("=" * 62)
    print("[根目錄] %s" % root)
    os.makedirs(os.path.join(root, "reports"), exist_ok=True)
    os.makedirs(os.path.join(root, "data"), exist_ok=True)
    log = []
    # [1] 整合接線
    wire_overrides(cfg, root, log)
    for sid, status, detail in [l for l in log if l[0] == "wire"]:
        print("  [接線 %s] %s" % (status, detail))
    # [2] 管線
    for st in P(cfg, "stages", default=[]):
        if not st.get("enabled", True):
            log.append((st["id"], "SKIP", "stages 設定停用")); continue
        run_stage(cfg, root, st, log)
        sid, status, detail = log[-1]
        print("  [%s] %-12s %s" % (status, sid, detail))
    # 報告
    out_html = os.path.join(root, P(cfg, "report", "html", default="reports/MasterRun.html"))
    build_report(cfg, root, log, out_html)
    state = {"ts": dt.datetime.now().isoformat(), "root": root,
             "log": [{"stage": a, "status": b, "detail": c} for a, b, c in log]}
    json.dump(state, open(os.path.join(root, P(cfg, "report", "state", default="data/master_state.json")),
              "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    ok = sum(1 for _, s, _ in log if s == "OK")
    print("[總結] %d OK / %d 項 | 報告: %s" % (ok, len(log), out_html))
    try:
        if os.name == "nt" and "--no-open" not in sys.argv: os.startfile(out_html)  # noqa
    except Exception: pass
    print("完成.")

if __name__ == "__main__":
    main()
