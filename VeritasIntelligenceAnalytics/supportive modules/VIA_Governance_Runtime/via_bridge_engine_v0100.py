# =====================================================================================
# VIA Bridge Engine v0100 — 前後端對接引擎(Command Bridge)
# 後端:全系統探測(指令接線/引擎正本/SSOT/資料庫/依賴/UI 盤點)→ bridge_state.json
# 前端:資料綁定 Porcelain 多 TAB 單頁(首頁=詳盡總覽+狀態矩陣)→ VIA_Reports/VIA_CommandBridge.html
# 同步:每次執行即重新探測+重生頁面 = 前端永遠反映後端當下真相(靜態綁定,無伺服器)
# 治理:唯讀探測;輸出全部 run-local(VIA_Reports);--no-open 支援;缺件誠實標示不中斷
# =====================================================================================
import os, re, sys, json, glob, hashlib, datetime as dt

VERSION = "v0100"
ROOT = os.environ.get("VIA_HOME") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

C_OK, C_WARN, C_FAIL, C_INFO = "#3d7a52", "#8a6420", "#a4472f", "#3c6660"

def sha12(p):
    try: return hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    except OSError: return "-"

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---------------------------------------------------------------- [B1] 指令接線探測
def probe_wiring():
    rows = []
    for cmd in sorted(glob.glob(os.path.join(ROOT, "bin", "via*.cmd"))):
        name = os.path.basename(cmd)[:-4]
        txt = open(cmd, encoding="utf-8", errors="replace").read()
        rem = next((l.strip()[4:] for l in txt.splitlines() if l.strip().lower().startswith("rem ")), "")
        m = re.search(r'"%~dp0(\.\.[^"]+\.(?:py|ps1|html))"', txt)
        target, ok = "", True
        if m:
            target = m.group(1).replace("\\", "/").lstrip("./")
            full = os.path.normpath(os.path.join(ROOT, "bin", m.group(1).replace("\\", os.sep)))
            ok = os.path.exists(full)
            target = os.path.relpath(full, ROOT).replace("\\", "/") if ok else target
        ver = (re.search(r"v\d{3,4}[A-Z]?", target) or re.search(r"v\d{1,2}\.\d", target))
        rows.append({"cmd": name, "target": target or "(複合啟動器)", "ver": ver.group(0) if ver else "-",
                     "sha12": sha12(os.path.join(ROOT, target)) if target and ok else "-",
                     "status": "OK" if ok else "MISS", "desc": rem[:120]})
    return rows

# ---------------------------------------------------------------- [B2] SSOT 對照
SSOT_REQUIRED = [
    "supportive modules/ssot/VRN_TickerRegexSSOT_v0100.json",
    "supportive modules/ssot/VIA_DesignLock_SSOT_v0101.json",
    "supportive modules/ssot/VIA_MegaPrompt_OfficialMode_v0100.md",
    "supportive modules/ssot/VIA_AICodegen_Prompt_SSOT_v0102.md",
    "functional modules/VAP/spec/ssot/vap_spec.json",
    "functional modules/VAP/spec/ssot/vap_chartlib.json",
    "functional modules/VAP/spec/UIUX_Design_Source/DESIGN_SOURCE_Manifest_v0101.json",
    "functional modules/VRN/registry/VRN_Production_Manifest.json",
    "supportive modules/registry/VIA_AutoCode_Registry_v0100.json",
]
def probe_ssot():
    return [{"path": s, "present": os.path.exists(os.path.join(ROOT, s)),
             "sha12": sha12(os.path.join(ROOT, s))} for s in SSOT_REQUIRED]

# ---------------------------------------------------------------- [B3] 依賴探測
def probe_deps():
    out = []
    for mod, why in [("duckdb", "Mega parquet 增量 store"), ("rich", "Mega 摘要矩陣"),
                     ("scipy", "FIS 驗證 harness"), ("numpy", "FIS/Pipeline 數值層"),
                     ("pandas", "Pipeline 資料層"), ("certifi", "via-gov --fetch-tw TLS")]:
        try:
            m = __import__(mod)
            out.append({"dep": mod, "status": "OK", "ver": getattr(m, "__version__", "?"), "why": why})
        except ImportError:
            out.append({"dep": mod, "status": "MISSING", "ver": "-", "why": why + "(via-envfix 可補)"})
    return out

# ---------------------------------------------------------------- [B4] 資料庫/證據探測
def probe_stores():
    rows = []
    fs = os.path.join(ROOT, "functional modules", "VRN", "output", "FINANCIAL_DATA_STORE.csv")
    if os.path.exists(fs):
        n = sum(1 for _ in open(fs, encoding="utf-8", errors="replace")) - 1
        rows.append({"store": "VRN 生產庫 FINANCIAL_DATA_STORE.csv", "status": "OK", "detail": "%d 列(append-only+record_hash 去重)" % n})
    else:
        rows.append({"store": "VRN 生產庫 FINANCIAL_DATA_STORE.csv", "status": "EMPTY", "detail": "尚無落地(via-extract --commit 後生成)"})
    pq = glob.glob(os.path.join(ROOT, "VIA_Reports", "mega_store", "run_*.parquet"))
    rows.append({"store": "Mega parquet 增量 store(DuckDB)", "status": "OK" if pq else "EMPTY",
                 "detail": "%d 個 run 檔" % len(pq) if pq else "首次 via-mega(parquet.enabled)後生成"})
    ms = os.path.join(ROOT, "VIA_Reports", "mega_state.json")
    if os.path.exists(ms):
        try:
            hist = json.load(open(ms, encoding="utf-8"))
            last = hist[-1]; lights = [r["light"] for r in last["rounds"]]
            rows.append({"store": "Mega 稽核歷史 mega_state.json", "status": lights[-1],
                         "detail": "%d 次 run;最近 %s %s(%d 檔)" % (len(hist), last.get("engine", "?"), "/".join(lights), last["rounds"][-1]["files"])})
        except Exception:
            rows.append({"store": "Mega 稽核歷史 mega_state.json", "status": "WARN", "detail": "存在但解析失敗"})
    else:
        rows.append({"store": "Mega 稽核歷史 mega_state.json", "status": "EMPTY", "detail": "尚無 run"})
    vmt = os.environ.get("VMT_ROOT") or r"C:\VIA\VeritasMailTracker"
    st = os.path.join(vmt, "data", "master_state.json")
    if os.path.exists(st):
        try:
            j = json.load(open(st, encoding="utf-8"))
            okn = sum(1 for l in j.get("log", []) if l.get("status") == "OK")
            rows.append({"store": "VMT 資料層 master_state.json", "status": "OK", "detail": "%s;%d OK 階段" % (j.get("ts", "?")[:16], okn)})
        except Exception:
            rows.append({"store": "VMT 資料層 master_state.json", "status": "WARN", "detail": "存在但解析失敗"})
    else:
        rows.append({"store": "VMT 資料層(VMT_ROOT)", "status": "EMPTY", "detail": vmt + " 未見(via-vmt-init 建立)"})
    return rows

# ---------------------------------------------------------------- [B5] UI 盤點
def probe_ui():
    ui_dir = os.path.join(ROOT, "supportive modules", "ui_support")
    hubs = sorted(glob.glob(os.path.join(ui_dir, "VIA_UI_Hub_v*.html")))
    consoles = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(ui_dir, "*.html")))]
    return {"hub_active": os.path.basename(hubs[-1]) if hubs else "-", "hub_versions": len(hubs),
            "total_pages": len(consoles),
            "key_pages": [p for p in consoles if any(k in p for k in ("Hub", "Flow_Overview", "Master_Overview", "SpotFut", "ETF_Group", "Macro_Tree", "ChipAnalysis"))][:10]}

# ---------------------------------------------------------------- 總評
def overall(wiring, ssot, deps, stores):
    fails = sum(1 for w in wiring if w["status"] == "MISS") + sum(1 for s in ssot if not s["present"])
    warns = sum(1 for d in deps if d["status"] == "MISSING") + sum(1 for s in stores if s["status"] in ("WARN", "RED"))
    return "RED" if fails else ("YELLOW" if warns else "GREEN")

# ---------------------------------------------------------------- 前端(多 TAB Porcelain)
def build_html(state, out):
    L = {"OK": C_OK, "GREEN": C_OK, "MISS": C_FAIL, "RED": C_FAIL, "FAIL": C_FAIL,
         "WARN": C_WARN, "YELLOW": C_WARN, "MISSING": C_WARN, "EMPTY": "#9aa5a1", "INFO": C_INFO}
    def pill(s): return "<span class='pill' style='background:%s'>%s</span>" % (L.get(s, C_INFO), esc(s))
    w, ss, dp, st, ui = state["wiring"], state["ssot"], state["deps"], state["stores"], state["ui"]
    ov = state["overall"]
    # TAB1 總覽:摘要卡 + 全系統狀態矩陣
    cards = ""
    for v, n, c in [(ov, "系統總燈號", L[ov]),
                    ("%d/%d" % (sum(1 for x in w if x["status"] == "OK"), len(w)), "指令接線 OK", C_OK),
                    ("%d/%d" % (sum(1 for x in ss if x["present"]), len(ss)), "SSOT 在位", C_INFO),
                    ("%d/%d" % (sum(1 for x in dp if x["status"] == "OK"), len(dp)), "依賴就緒", C_WARN),
                    (str(ui["total_pages"]), "UI 頁面歸檔", "#3f4f78"),
                    (state["ts"][11:16], "本次探測", "#5e5540")]:
        cards += "<div class='card'><div class='cv' style='color:%s'>%s</div><div class='cn'>%s</div></div>" % (c, esc(v), esc(n))
    mat = "".join("<tr><td>%s</td><td class='mono'>%s</td><td class='mono'>%s</td><td>%s</td><td class='mono'>%s</td><td>%s</td></tr>"
                  % (esc(x["cmd"]), esc(x["target"]), esc(x["ver"]), pill(x["status"]), esc(x["sha12"]), esc(x["desc"])) for x in w)
    tab1 = ("<h2>系統摘要</h2><div class='cards'>" + cards + "</div>"
            "<h2>全系統狀態矩陣(指令 × 接線 × 版本 × 雜湊)</h2>"
            "<table><tr><th style='width:92px'>指令</th><th>接線目標</th><th style='width:64px'>版本</th>"
            "<th style='width:58px'>狀態</th><th style='width:96px'>SHA12</th><th>說明</th></tr>" + mat + "</table>")
    # TAB2 資料庫/證據
    tab2 = ("<h2>資料庫與稽核證據</h2><table><tr><th style='width:280px'>庫/證據</th><th style='width:70px'>狀態</th><th>細節</th></tr>"
            + "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(x["store"]), pill(x["status"]), esc(x["detail"])) for x in st) + "</table>")
    # TAB3 SSOT
    tab3 = ("<h2>SSOT 真相層對照</h2><table><tr><th style='width:70px'>狀態</th><th>真相檔</th><th style='width:96px'>SHA12</th></tr>"
            + "".join("<tr><td>%s</td><td class='mono'>%s</td><td class='mono'>%s</td></tr>"
                      % (pill("OK" if x["present"] else "MISS"), esc(x["path"]), esc(x["sha12"])) for x in ss) + "</table>")
    # TAB4 依賴
    tab4 = ("<h2>依賴與環境(via-envfix 一鍵補齊)</h2><table><tr><th style='width:90px'>套件</th><th style='width:80px'>狀態</th>"
            "<th style='width:90px'>版本</th><th>用途</th></tr>"
            + "".join("<tr><td class='mono'>%s</td><td>%s</td><td class='mono'>%s</td><td>%s</td></tr>"
                      % (esc(x["dep"]), pill(x["status"]), esc(x["ver"]), esc(x["why"])) for x in dp) + "</table>")
    # TAB5 UI 版圖
    tab5 = ("<h2>UI 版圖</h2><table><tr><th style='width:200px'>項</th><th>值</th></tr>"
            "<tr><td>現役樞紐</td><td class='mono'>%s(歷代 %d 版原地保留)</td></tr>"
            "<tr><td>歸檔頁面總數</td><td>%d</td></tr>"
            "<tr><td>代表頁</td><td class='mono'>%s</td></tr></table>"
            % (esc(ui["hub_active"]), ui["hub_versions"], ui["total_pages"], esc(" · ".join(ui["key_pages"]))))
    tabs = [("總覽 · 狀態矩陣", tab1), ("資料庫", tab2), ("SSOT", tab3), ("依賴環境", tab4), ("UI 版圖", tab5)]
    bar = "".join("<span class='tab%s' onclick='show(%d)'>%s</span>" % (" on" if i == 0 else "", i, esc(t)) for i, (t, _) in enumerate(tabs))
    panes = "".join("<div class='pane%s' id='p%d'>%s</div>" % (" on" if i == 0 else "", i, b) for i, (_, b) in enumerate(tabs))
    page = ("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA Command Bridge</title>"
      "<link href='https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Noto+Serif+TC:wght@500;600&display=swap' rel='stylesheet'><style>"
      ":root{--ink:#1b1a17;--mut:#6b6860;--mut2:#9aa5a1;--hair:#dcdad3;--seal:#9e2b25;--teal:#3d8f8f;"
      "--serif:'Cormorant Garamond',Georgia,serif;--cjk:'Noto Serif TC','Noto Serif CJK TC','Songti TC','PMingLiU',serif;"
      "--mono:'SFMono-Regular',Consolas,'Liberation Mono',monospace}"
      "*{box-sizing:border-box;margin:0;padding:0}body{background:#f0efeb;color:var(--ink);font-family:'Microsoft JhengHei','Segoe UI',system-ui,sans-serif;padding:26px}"
      ".eyebrow{display:flex;gap:8px;align-items:center;margin-bottom:8px}.chip{padding:2px 7px;background:var(--ink);color:#fbfaf7;font:700 9px var(--mono);letter-spacing:.14em}"
      ".ey{font:700 8.5px var(--mono);letter-spacing:.13em;color:var(--mut);text-transform:uppercase}"
      "header{display:flex;align-items:center;border-bottom:3px solid var(--seal);padding-bottom:14px}"
      ".seal{width:38px;height:38px;background:var(--seal);color:#fbfaf7;display:flex;align-items:center;justify-content:center;font-family:var(--cjk);font-size:20px;border-radius:4px;margin-right:12px}"
      "h1{font:500 19px/1.2 var(--serif);letter-spacing:.055em}.wmcjk{font:600 9.5px var(--cjk);letter-spacing:.22em;color:var(--teal);margin-top:2px}"
      ".sub{font:10.5px var(--mono);color:var(--mut);margin-top:4px}"
      ".strip{height:4px;background:linear-gradient(90deg,#24457f 0 16.6%,#3c6660 0 33.3%,#4a6b45 0 50%,#8a7340 0 66.6%,#5e5540 0 83.3%,#3f4f78 0 100%);margin:13px 0 0;border-radius:2px}"
      ".tabs{display:flex;gap:6px;margin:14px 0 0;flex-wrap:wrap;border-bottom:1px solid var(--hair);padding-bottom:0}"
      ".tab{padding:8px 16px;border-radius:6px 6px 0 0;font:700 12px var(--mono);cursor:pointer;color:var(--mut);border:1px solid transparent}"
      ".tab.on{background:#fbfaf7;border:1px solid var(--hair);border-bottom-color:#fbfaf7;color:var(--seal)}"
      ".pane{display:none;padding-top:6px}.pane.on{display:block}"
      "h2{font:700 11px var(--mono);letter-spacing:2px;color:var(--mut);margin:20px 0 9px;text-transform:uppercase}"
      ".cards{display:flex;gap:12px;flex-wrap:wrap}"
      ".card{background:#fdfbf6;border:1px solid var(--hair);border-radius:4px;padding:12px 18px;min-width:120px}"
      ".cv{font:700 20px var(--mono)}.cn{font-size:11px;color:var(--mut);margin-top:2px}"
      "table{width:100%;border-collapse:collapse;background:#fbfaf7;border:1px solid var(--hair);table-layout:fixed}"
      "th{font:700 10px var(--mono);text-align:left;padding:8px 10px;border-bottom:1px solid var(--hair);color:var(--mut)}"
      "td{font-size:11.5px;padding:7px 10px;border-bottom:1px solid var(--hair);word-wrap:break-word;overflow-wrap:anywhere}"
      "tr:last-child td{border-bottom:none}.mono{font-family:var(--mono);font-size:10.5px}"
      ".pill{color:#fbfaf7;font:500 10px var(--mono);padding:2px 7px;border-radius:2px}"
      "footer{margin-top:22px;font:10px var(--mono);color:var(--mut2)}</style></head><body>"
      "<div class='eyebrow'><span class='chip'>" + VERSION + "</span><span class='ey'>Veritas Intelligence Analytics · Command Bridge · Porcelain</span></div>"
      "<header><div class='seal'>橋</div><div><h1>VIA COMMAND BRIDGE — 前後端對接總覽</h1>"
      "<div class='wmcjk'>維里塔斯 · 首頁即真相 · 狀態矩陣</div>"
      "<div class='sub'>" + esc(state["ts"]) + " · 每次 via-bridge 即重新探測+重生本頁(前端=後端當下真相)· 唯讀不落地</div></div></header>"
      "<div class='strip'></div><div class='tabs'>" + bar + "</div>" + panes +
      "<footer>via_bridge_engine " + VERSION + " · Porcelain(DesignLock v0101)| 後端探測 B1 接線/B2 SSOT/B3 依賴/B4 資料庫/B5 UI | run-local 產出不入庫</footer>"
      "<script>function show(i){document.querySelectorAll('.tab').forEach(function(t,j){t.classList.toggle('on',j===i)});"
      "document.querySelectorAll('.pane').forEach(function(p,j){p.classList.toggle('on',j===i)});}</script></body></html>")
    open(out, "w", encoding="utf-8").write(page)

# ---------------------------------------------------------------- 主流程
def main():
    print("=" * 62); print("  VIA Bridge Engine %s  |  前後端對接 · 狀態矩陣" % VERSION); print("=" * 62)
    print("[根目錄] " + ROOT)
    steps = [("B1 指令接線", probe_wiring), ("B2 SSOT", probe_ssot), ("B3 依賴", probe_deps),
             ("B4 資料庫", probe_stores), ("B5 UI 盤點", probe_ui)]
    state = {"ts": dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "engine": VERSION}
    keys = ["wiring", "ssot", "deps", "stores", "ui"]
    for i, ((name, fn), key) in enumerate(zip(steps, keys)):
        n = int((i + 1) / len(steps) * 20)
        sys.stdout.write("\r[%-20s] %3d%%  %s" % ("#" * n, (i + 1) * 20, name)); sys.stdout.flush()
        state[key] = fn()
    print()
    state["overall"] = overall(state["wiring"], state["ssot"], state["deps"], state["stores"])
    rep_dir = os.path.join(ROOT, "VIA_Reports"); os.makedirs(rep_dir, exist_ok=True)
    js = os.path.join(rep_dir, "bridge_state.json")
    json.dump(state, open(js, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    out = os.path.join(rep_dir, "VIA_CommandBridge.html")
    build_html(state, out)
    wOK = sum(1 for x in state["wiring"] if x["status"] == "OK")
    dOK = sum(1 for x in state["deps"] if x["status"] == "OK")
    print("[總結] 總燈號 %s | 接線 %d/%d | SSOT %d/%d | 依賴 %d/%d | UI 頁 %d"
          % (state["overall"], wOK, len(state["wiring"]),
             sum(1 for x in state["ssot"] if x["present"]), len(state["ssot"]),
             dOK, len(state["deps"]), state["ui"]["total_pages"]))
    print("[前端] " + out)
    if os.name == "nt" and "--no-open" not in sys.argv:
        os.startfile(out)  # noqa
    return 0

if __name__ == "__main__":
    sys.exit(main())
