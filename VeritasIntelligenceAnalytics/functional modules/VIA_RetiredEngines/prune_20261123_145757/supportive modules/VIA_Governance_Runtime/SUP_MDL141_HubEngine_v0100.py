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
# =====================================================================================
# VIA Hub Engine v0100 — 活化樞紐(U/I 進一步最佳化)
# 靜態 Hub 進化為「開啟即探測」:每次 via-ui 先跑輕量探測(接線/依賴/生產庫/Mega 燈/UI 數)
# → 生成帶即時狀態徽章的十四介面樞紐(左樞右詳 + 頂部即時摘要帶)→ 自動開啟。
# 產出 run-local(VIA_Reports/VIA_UI_Hub_Live.html);靜態 Hub v0108 保留為離線回退。
# 治理:唯讀探測;Porcelain(DesignLock SSOT v0101);--no-open 支援。
# =====================================================================================
import os, sys, json, glob, datetime as dt

VERSION = "v0100"
ROOT = os.environ.get("VIA_HOME") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
C_OK, C_WARN, C_FAIL, C_MUT = "#3d7a52", "#8a6420", "#a4472f", "#9aa5a1"

def probe():
    p = {}
    cmds = glob.glob(os.path.join(ROOT, "bin", "via*.cmd"))
    p["cmds"] = len(cmds)
    ok = 0
    for m in ["duckdb", "rich", "scipy", "numpy", "pandas"]:
        try: __import__(m); ok += 1
        except ImportError: pass
    p["deps"] = "%d/5" % ok; p["deps_ok"] = (ok == 5)
    fs = os.path.join(ROOT, "functional modules", "VRN", "output", "FINANCIAL_DATA_STORE.csv")
    p["store"] = (sum(1 for _ in open(fs, encoding="utf-8", errors="replace")) - 1) if os.path.exists(fs) else 0
    p["mega"] = "-"
    ms = os.path.join(ROOT, "VIA_Reports", "mega_state.json")
    if os.path.exists(ms):
        try: p["mega"] = json.load(open(ms, encoding="utf-8"))[-1]["rounds"][-1]["light"]
        except Exception: p["mega"] = "?"
    p["ui_pages"] = len(glob.glob(os.path.join(ROOT, "supportive modules", "ui_support", "*.html")))
    vmt = os.environ.get("VMT_ROOT") or r"C:\VIA\VeritasMailTracker"
    p["vmt"] = "資料層在位" if os.path.isdir(vmt) else "未布建(via-vmt-init)"
    return p

TILES = [
 ("func", "鑑", "#3c6660", "VAP WORKBENCH", "自動繪圖工作台 v010", "via-all 內含", ""),
 ("func", "鍛", "#4a6b45", "VDF WORKBENCH", "資料鍛造側欄工作台 v0160C", "via-vdf", ""),
 ("func", "記", "#3d8f8f", "NOTE PRO", "智能資產筆記", "直接開啟 .dc.html", ""),
 ("func", "研", "#24457f", "VRN EXTRACT", "內容級擷取 v0101 ACTIVE", "via-extract", "STORE"),
 ("func", "理", "#9e2b25", "TRINITY 三系模板", "VIA>鍛研鑑 整合模板 v0100", "via-trinity", ""),
 ("supp", "理", "#24457f", "CONTROL TOWER", "治理總控台 v005", "via-tower", ""),
 ("supp", "郵", "#8a7340", "VMT MASTERRUN", "郵件追蹤主引擎 v0103 Porcelain", "via-vmt", "VMT"),
 ("supp", "核", "#5e5540", "MEGA MATRIX", "公定模式三輪全景(動態最新版)", "via-mega", "MEGA"),
 ("supp", "治", "#3f4f78", "CENTRAL GOVERNANCE", "中央治理 CGE v0401", "via-gov", ""),
 ("supp", "流", "#9e2b25", "FLOW OVERVIEW", "資金流總覽 Console v0101 Porcelain", "via-ui 內連", ""),
 ("supp", "湧", "#3c6660", "FLOW SYSTEM", "FlowSystem OneShot v0101 Porcelain", "via-flow", ""),
 ("supp", "預", "#24457f", "IF FORECAST", "產業預測整合引擎 v0100", "via-if", ""),
 ("supp", "驗", "#8a7340", "FIS VALIDATION", "FIS 驗證 harness v3", "via-fis", ""),
 ("supp", "橋", "#9e2b25", "COMMAND BRIDGE", "前後端狀態矩陣 v0100", "via-bridge", ""),
]

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def badge(kind, p):
    if kind == "STORE":
        return "<span class='live' style='background:%s'>庫 %d 列</span>" % (C_OK if p["store"] else C_MUT, p["store"])
    if kind == "MEGA":
        col = {"GREEN": C_OK, "YELLOW": C_WARN, "RED": C_FAIL}.get(p["mega"], C_MUT)
        return "<span class='live' style='background:%s'>%s</span>" % (col, esc(p["mega"]))
    if kind == "VMT":
        return "<span class='live' style='background:%s'>%s</span>" % (C_OK if "在位" in p["vmt"] else C_WARN, esc(p["vmt"]))
    return ""

def build(p, out):
    btns_f, btns_s = "", ""
    for z, seal, acc, wm, sub, cmd, live in TILES:
        b = ("<div class='btn' style='--acc:%s' onclick=\"sel(this)\" data-wm='%s' data-sub='%s' data-cmd='%s' data-seal='%s'>"
             "<div class='bseal'>%s</div><div class='bn'>%s</div><div class='bm'>%s</div>%s</div>"
             % (acc, esc(wm), esc(sub), esc(cmd), esc(seal), esc(seal), esc(wm.split(" ")[0]), esc(cmd), badge(live, p)))
        if z == "func": btns_f += b
        else: btns_s += b
    summary = ("<div class='sumband'>"
      "<span class='sk'>指令</span><span class='sv'>%d</span>"
      "<span class='sk'>依賴</span><span class='sv' style='color:%s'>%s</span>"
      "<span class='sk'>生產庫</span><span class='sv'>%d 列</span>"
      "<span class='sk'>Mega</span><span class='sv'>%s</span>"
      "<span class='sk'>UI 歸檔</span><span class='sv'>%d 頁</span>"
      "<span class='sk'>探測</span><span class='sv'>%s</span></div>"
      % (p["cmds"], C_OK if p["deps_ok"] else C_WARN, p["deps"], p["store"], esc(p["mega"]),
         p["ui_pages"], dt.datetime.now().strftime("%H:%M:%S")))
    page = ("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA UI Hub Live</title>"
      "<link href='https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Noto+Serif+TC:wght@500;600&display=swap' rel='stylesheet'><style>"
      ":root{--bg:#f0efeb;--paper:#fbfaf7;--paper2:#fdfbf6;--ink:#1b1a17;--mut:#6b6860;--mut2:#9aa5a1;--hair:#dcdad3;"
      "--seal:#9e2b25;--teal:#3d8f8f;--serif:'Cormorant Garamond',Georgia,serif;"
      "--cjk:'Noto Serif TC','Noto Serif CJK TC','Songti TC','PMingLiU',serif;"
      "--mono:'SFMono-Regular',Consolas,'Liberation Mono',monospace;--sans:'Microsoft JhengHei','Segoe UI',system-ui,sans-serif}"
      "*{box-sizing:border-box;margin:0;padding:0}body{background:var(--bg);color:var(--ink);font-family:var(--sans);padding:24px;max-width:1160px;margin:0 auto}"
      ".chip{display:inline-block;padding:2px 7px;background:var(--ink);color:#fbfaf7;font:700 9px var(--mono);letter-spacing:.14em;margin-bottom:8px}"
      "header{display:flex;align-items:center;border-bottom:3px solid var(--seal);padding-bottom:12px}"
      ".hseal{width:40px;height:40px;background:var(--seal);color:#fbfaf7;display:flex;align-items:center;justify-content:center;font-family:var(--cjk);font-size:22px;border-radius:4px;margin-right:12px}"
      "h1{font:500 19px/1.2 var(--serif);letter-spacing:.055em}.wmcjk{font:600 9.5px var(--cjk);letter-spacing:.22em;color:var(--teal);margin-top:2px}"
      ".sumband{display:flex;gap:10px;align-items:center;flex-wrap:wrap;background:var(--paper);border:1px solid var(--hair);border-radius:6px;padding:9px 14px;margin:12px 0}"
      ".sk{font:700 9px var(--mono);letter-spacing:.1em;color:var(--mut);text-transform:uppercase}"
      ".sv{font:700 13px var(--mono);margin-right:8px}"
      ".strip{height:4px;background:linear-gradient(90deg,#24457f 0 16.6%,#3c6660 0 33.3%,#4a6b45 0 50%,#8a7340 0 66.6%,#5e5540 0 83.3%,#3f4f78 0 100%);margin:0 0 14px;border-radius:2px}"
      "h2{font:700 10px var(--mono);letter-spacing:2px;color:var(--mut);margin:14px 0 8px;text-transform:uppercase;display:flex;align-items:center;gap:8px}"
      "h2 .zh{font:600 11px var(--cjk);letter-spacing:.3em;color:#3c6660}h2 .ln{flex:1;height:1px;background:var(--hair)}"
      ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:9px}"
      ".btn{position:relative;display:flex;flex-direction:column;align-items:center;gap:4px;background:var(--paper2);border:1px solid var(--hair);border-top:3px solid var(--acc);border-radius:6px;padding:10px 6px 8px;cursor:pointer;transition:.12s}"
      ".btn:hover{border-color:var(--acc)}.btn.on{background:var(--ink)}.btn.on .bn{color:#fbfaf7}"
      ".bseal{width:28px;height:28px;background:var(--seal);color:#fbfaf7;display:inline-flex;align-items:center;justify-content:center;font-family:var(--cjk);font-size:15px;border-radius:4px}"
      ".bn{font:600 11px var(--sans)}.bm{font:500 8px var(--mono);color:var(--mut2)}"
      ".live{position:absolute;top:-7px;right:-4px;color:#fbfaf7;font:700 8px var(--mono);padding:2px 6px;border-radius:8px}"
      ".detail{background:var(--paper2);border:1px solid var(--hair);border-radius:8px;padding:14px 18px;margin-top:14px;font-size:12px}"
      ".dcmd{display:inline-block;font:700 12px var(--mono);background:var(--ink);color:#fbfaf7;border-radius:4px;padding:5px 12px;margin-top:6px}"
      "footer{margin-top:18px;font:9.5px var(--mono);color:var(--mut2)}</style></head><body>"
      "<span class='chip'>HUB LIVE " + VERSION + "</span>"
      "<header><div class='hseal'>樞</div><div><h1>VERITAS UI HUB — 活化樞紐</h1>"
      "<div class='wmcjk'>維里塔斯 · 十四介面 · 開啟即探測</div></div></header>"
      "<div class='strip' style='margin-top:12px'></div>" + summary +
      "<h2><span class='zh'>功能性</span>FUNCTIONAL<span class='ln'></span></h2><div class='grid'>" + btns_f + "</div>"
      "<h2><span class='zh'>支援性</span>SUPPORTIVE<span class='ln'></span></h2><div class='grid'>" + btns_s + "</div>"
      "<div class='detail' id='det'>點任一介面卡查看啟動指令。每次 via-ui 開啟本頁時即時重探,摘要帶=當下真相。</div>"
      "<footer>via_hub_engine " + VERSION + " · Porcelain(DesignLock v0101)| 每跑必重生 run-local | 離線回退:靜態 Hub v0108(via-ui 自動 fallback)</footer>"
      "<script>function sel(el){document.querySelectorAll('.btn').forEach(function(b){b.classList.remove('on')});el.classList.add('on');"
      "document.getElementById('det').innerHTML='<b style=\"font-family:var(--serif);font-size:15px\">'+el.dataset.seal+' '+el.dataset.wm+"
      "'</b><div style=\"color:#6b6860;margin-top:2px\">'+el.dataset.sub+'</div><span class=\"dcmd\">'+el.dataset.cmd+'</span>';}</script>"
      "</body></html>")
    open(out, "w", encoding="utf-8").write(page)

def main():
    print("=" * 56); print("  VIA Hub Engine %s  |  活化樞紐 · 開啟即探測" % VERSION); print("=" * 56)
    p = probe()
    rep = os.path.join(ROOT, "VIA_Reports"); os.makedirs(rep, exist_ok=True)
    out = os.path.join(rep, "VIA_UI_Hub_Live.html")
    build(p, out)
    print("[探測] 指令 %d · 依賴 %s · 生產庫 %d 列 · Mega %s · UI %d 頁"
          % (p["cmds"], p["deps"], p["store"], p["mega"], p["ui_pages"]))
    print("[樞紐] " + out)
    if os.name == "nt" and "--no-open" not in sys.argv:
        os.startfile(out)  # noqa
    return 0

if __name__ == "__main__":
    sys.exit(main())
