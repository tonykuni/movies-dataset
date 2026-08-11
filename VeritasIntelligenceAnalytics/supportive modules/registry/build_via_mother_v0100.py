# -*- coding: utf-8 -*-
"""build_via_mother_v0100.py — VIA 母頁產生器 v0100(操作員令:FlowSystem 先不列入,其他加速完整)。

三段式規約:P1 消費者頁(設定+輸入現況+輸入前檢查+運作結果)→ 矩陣頁 → 末頁說明(可隱藏)。
左 panel:00 母頁 · 01-07 功能子系統(無 FlowSystem)· 90 商品目錄 · 91 規格母版 · 底部誠實燈。
零 CDN 單檔;配色=WorkOps v2 視覺鎖佔位,候操作員介面連結到件即換膚(風格鎖+色鎖)。
產出:<VIA根>/VIA_Mother.html(追蹤;pull 即開)。資料源:pkg_pointers/ + 登錄簿 + 盤點正本。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Mother.html"

T = {"bg": "#f2f1ec", "paper": "#ffffff", "paper2": "#faf9f6", "ink": "#1b1a17",
     "ink2": "#33403f", "mut": "#6b6860", "mut2": "#8a877e", "line": "#dcdad3",
     "line2": "#e8e6df", "teal": "#3d8f8f", "up": "#c96b5a", "down": "#5a9e6f",
     "accent": "#5980a6", "amber": "#c4943a"}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


SUBS = [
    ("workops", "01", "WorkOps 母版", "郵件×專案治理+指揮板", "🟢 生產",
     "BoardQA 四層全綠(unit+integration 14/14 · system 9/9 · 封印驗真)",
     ["via-workops board   → 產最新指揮板(開啟 run 目錄內 VIA_WorkOps_CommandBoard.html)",
      "via-boardqa         → 四層品保", "via-usertest        → U01-U12 使用者旅程"],
     "functional modules/WorkOps/VIA_WorkOps_主力包與對照卡_v002.html"),
    ("vap", "02", "VAP 繪圖", "chartlib+seaborn/plotly 雙線+SSOT 28 圖型", "🟢 生產",
     "chartlib v007 端到端+--sql/--panels;seaborn/plotly selftest 65 PASS;跨系統實渲(VDF/MultiFactor)",
     ["via-vap --demo --auto        → 零依賴 SVG 線出圖",
      "via-plot probe ・ via-plot demo --out vap_demo → 28 型全譜",
      "via-plot render --chart line --file <任何子系統csv/sqlite> --x 欄 --y 欄"],
     "functional modules/VAP/ui/VAP_Workbench_v010.html"),
    ("vrn", "03", "VRN 研報", "研報 OCR/表格還原/交叉驗證治理", "🟢 測試鏈全綠",
     "SmokeTest 11/0 · Pipeline Runner 全綠 · XCheck 無硬矛盾 · 53 凍結鎖 · 正典入口已宣告(OCR 語料在工作站)",
     ["via-probe / via-extract      → 內容萃取(dry-run 預設)",
      "via-batch                    → AllInOne 批次", "via-ocr                      → OCR 統一路由"],
     "functional modules/VRN/template/VDF_VRN_Integrated_ReportSSOT_AutoLayout_FINAL.html"),
    ("vdf", "04", "VDF 資料鍛造", "市場資料取數契約 SSOT+intake+六模組重建R", "🟢 測試鏈全綠",
     "MDL301 硬閘全綠 · MDL302 九階段全綠(80/80 完整性·7/7 整合·4/4 edge)· 契約 277 項 PASS;v0160 三本體+MDL002/007 等候上傳",
     ["via-vdf contract check       → 取數契約盤點",
      "py \"functional modules\\VDF\\VDF_MDL302_FinalActivation.py\" --no-pause → 端到端",
      "via-vdf                      → OneClick 側欄(工作站)"],
     "functional modules/VDF/VDF_VRN_Integrated_ReportSSOT_AutoLayout_FINAL.html"),
    ("chipwar", "05", "ChipWar", "晶片戰情 12 引擎指標族", "🟢 已驗",
     "harness L1 6/6+L2 8/8 存證;FOMO 報告樣張在庫",
     ["via-wf chipwar               → 戰情儀表板(工作站產 _generated)"],
     "functional modules/ChipWar/docs/VIA_FOMO_Index_Report_sample_20260812.html"),
    ("multifactor", "06", "MultiFactor", "多因子驗證模擬", "🟢 已驗",
     "test v0101 過;simulation_ledger 已被 via-plot 跨系統實渲",
     ["via-wf multifactor           → 驗證模擬鏈"], ""),
    ("talib", "07", "TALib", "技術指標 64 式(adj 鐵律)", "🟢 已驗",
     "64 指標全測過;一律還原價",
     ["via-wf talib                 → 指標批跑"], ""),
]

FAMILIES = [
    ("治理/登錄", "registry · 20_Registry_SSOT · VIA_Central_Governance · VIA_Governance_Runtime · 30_HardGate · audit_tools · VisualLock · specs · ssot", "全體", "🟢"),
    ("執行入口", "60_PowerShell_Entry_Internal · bin(45 支 via-* 動詞)", "全體", "🟢"),
    ("子系統級引擎", "VIA_Pipeline · VMT_SuperBOM · PMIS-Lite · TFE_Engine · VIA_IF_Engine · EngineForge · Forge · Optimizer_Suite", "各對應線", "🟡"),
    ("執行環境", "10_Core_Runtime · 40_Environment_Health · 50_Protection · AutoSandbox20 · runtime_bridge · VHS · VVX · VPNS 等", "全體", "🟡"),
    ("UI 支援", "ui_support · Dashboard_Format_Standardization · Decision_Studio · Control_Tower", "母頁/各子系統", "🟡"),
    ("規則庫", "70_VRN_Rules(25) · 80_VETF_Sort · VIA_OCR_Router", "VRN/VETF", "🟢"),
    ("nexuscore 家族", "_nexuscore_*(12)· _via_mother_system_manager 等", "母系統編排", "🟡 待對帳"),
    ("待整理族", "_inbox_to_classify(611 件)· _superseded · _quarantine · Rescue_Staging · VRN_Helpers_Rescued", "—", "🔴 清冊已列"),
]


def load_pointers():
    rows = []
    for p in sorted((HERE / "pkg_pointers").glob("PKG_*_Pointer.json")):
        j = json.loads(p.read_text(encoding="utf-8"))
        rows.append((j["pkg_code"], j["name"], j["contents_n"],
                     j["contents_bytes"] // 1024, ", ".join(j["install"]["bin_verbs"]),
                     "supportive modules/registry/pkg_pointers/" + p.name))
    return rows


def build():
    try:
        reg = json.loads((HERE / "VIA_AutoCode_Registry_v0100.json").read_text(encoding="utf-8"))
        n_ledger = len(reg.get("ledger", []))
    except Exception:
        n_ledger = 0
    pkgs = load_pointers()

    nav = ['<button class="nv on" data-p="home"><span class="n">00</span><span>母頁<span class="en">CONSUMER</span></span></button>']
    for pid, num, zh, _r, _s, _e, _c, _u in SUBS:
        nav.append('<button class="nv" data-p="%s"><span class="n">%s</span><span>%s<span class="en">%s</span></span></button>'
                   % (pid, num, esc(zh), pid.upper()))
    nav.append('<div class="sep">治理</div>')
    nav.append('<button class="nv" data-p="pkgs"><span class="n">90</span><span>商品目錄<span class="en">PKG MATRIX</span></span></button>')
    nav.append('<button class="nv" data-p="spec"><span class="n">91</span><span>規格母版<span class="en">SPEC MASTER</span></span></button>')

    # P1 消費者頁
    pkg_rows = "".join('<tr><td class="mono">%s</td><td>%s</td><td class="r">%d</td><td class="r">%s KB</td><td class="mono">%s</td></tr>'
                       % (c, esc(n), cn, "{:,}".format(kb), esc(v)) for c, n, cn, kb, v, _ in pkgs)
    sub_lights = "".join('<tr><td class="mono">%s</td><td>%s</td><td>%s</td><td class="small">%s</td></tr>'
                         % (num, esc(zh), st, esc(ev)) for _p, num, zh, _r, st, ev, _c, _u in SUBS)
    home = """<div class="pg on" id="pg-home"><div class="tin">
<div class="card"><h3>① 設定 + 輸入現況(消費者頁 — 只需看本頁)</h3>
<table><tr><th>項</th><th>值</th><th>說明</th></tr>
<tr><td>基座 base</td><td class="mono">C:\\VeritasIntelligenceAnalytics</td><td>首次導入即定;所有商品落此</td></tr>
<tr><td>環境需求</td><td class="mono">PowerShell 7+ · Python 3.10+</td><td>安裝器自動檢查/引導安裝</td></tr>
<tr><td>安裝指令</td><td class="mono">pwsh -File Install-VIA-Product-v0100.ps1 -Pointer &lt;指針&gt;</td><td>全自動;僅商品代碼增減交您</td></tr>
<tr><td>登錄簿</td><td class="mono">%d 筆 append-only</td><td>編號永不變 · 現有代碼 sha256 舉證於指針</td></tr></table>
<h3 style="margin-top:12px">② 輸入前檢查(先擋後跑)</h3>
<div class="cmd">via-precheck --file 資料.csv --key date,ticker --required close</div>
<p class="small">偵測:重複輸入(整列/鍵欄)· 缺欄缺值 · 路徑不存在 — 有問題誠實列出再放行。</p></div>
<div class="card"><h3>③ 已裝商品代碼(勾選=您的系統組成)</h3>
<table><tr><th>編號</th><th>商品</th><th>內容物</th><th>大小</th><th>動詞</th></tr>%s</table>
<p class="small">增減商品=執行/移除對應指針安裝;共用資源族自動去重。FlowSystem(PKG-005)本波操作員令先不列入。</p></div>
<div class="card"><h3>④ 運作後結果(誠實燈 — 本會話實測/存證)</h3>
<table><tr><th>#</th><th>子系統</th><th>狀態</th><th>證據</th></tr>%s</table></div>
</div></div>""" % (n_ledger, pkg_rows, sub_lights)

    # 子系統頁(同構 lite:狀態+命令+UI iframe/誠實缺席)
    subpages = []
    for pid, num, zh, role, st, ev, cmds, ui in SUBS:
        cmdhtml = "".join('<div class="cmd">%s</div>' % esc(c) for c in cmds)
        if ui and (VIA / ui).exists():
            uihtml = ('<div class="card"><h3>介面(在庫正本)</h3>'
                      '<iframe data-src="%s" title="%s"></iframe></div>' % (esc(ui), esc(zh)))
        else:
            uihtml = ('<div class="card"><h3>介面</h3><p class="small">本子系統無獨立追蹤 UI —'
                      '以命令列動詞+產出報告呈現(誠實缺席,不佔位假圖)。</p></div>')
        subpages.append("""<div class="pg" id="pg-%s"><div class="tin">
<div class="card"><h3>%s %s — %s</h3><p>%s · <span class="small">%s</span></p>
<h3 style="margin-top:10px">操作動詞</h3>%s</div>%s</div></div>"""
                        % (pid, num, esc(zh), esc(role), st, esc(ev), cmdhtml, uihtml))

    fam_rows = "".join('<tr><td>%s</td><td class="small">%s</td><td>%s</td><td>%s</td></tr>'
                       % (esc(f), esc(d), esc(sv), st) for f, d, sv, st in FAMILIES)
    pkg_detail = "".join('<tr><td class="mono">%s</td><td>%s</td><td class="r">%d</td><td class="r">%s KB</td><td class="mono small">%s</td><td class="mono small">%s</td></tr>'
                         % (c, esc(n), cn, "{:,}".format(kb), esc(v), esc(pp)) for c, n, cn, kb, v, pp in pkgs)
    pkgs_pg = """<div class="pg" id="pg-pkgs"><div class="tin">
<div class="card"><h3>商品目錄矩陣(PKG;編號永不變 · 指針=內容物 sha256 舉證)</h3>
<table><tr><th>編號</th><th>商品</th><th>件</th><th>大小</th><th>動詞</th><th>指針</th></tr>%s</table>
<p class="small">既有 PKG-001…008 沿用(005=FlowSystem 本波不列入);組合安裝時 shared_supportive 共用族去重。</p></div>
<div class="card"><h3>資源性模組 8 族 × 功能模組對映(資源清單→功能清單)</h3>
<table><tr><th>族</th><th>目錄</th><th>服務對象</th><th>狀態</th></tr>%s</table>
<p class="small">待整理族清冊:supportive modules/registry/unsorted_inventory_v0100.json(報告only不搬移)。</p></div>
</div></div>""" % (pkg_detail, fam_rows)

    spec_pg = """<div class="pg" id="pg-spec"><div class="tin">
<div class="card"><h3>規格母版(最後一頁)</h3>
<iframe data-src="VIA_Reports/VIA_Spec_Master_LastPage.html" title="spec"></iframe>
<p class="small">缺席時先跑:via-spec</p></div></div>"""

    docs = """<div class="card" id="docs" style="display:none"><h3>末頁 · 說明/規格(預設隱藏)</h3>
<ul><li>三段式規約:P1 消費者頁=設定+現況+輸入前檢查+結果;矩陣頁;末頁可隱藏(本區)。</li>
<li>配色=WorkOps v2 視覺鎖<b>佔位</b> — 操作員介面連結到件即換膚(風格鎖+色鎖)。</li>
<li>紅線:絕不代寄 · 唯讀原件 · 編號永不變 · 只增不減 · 零 CDN 離線 · 誠實 OK/FAIL。</li>
<li>規劃正本:functional modules/VIA_Mother_Productization_Plan_v0100.md · 大架構:VIA_Architecture_Progress_v0100.md</li></ul></div>"""

    page = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA 母系統 · Veritas Intelligence Analytics(一窗)</title><style>
*{box-sizing:border-box;margin:0;padding:0}html,body{height:100%%}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif;font-size:13px;display:flex;overflow:hidden}
.sb{flex:none;width:222px;height:100vh;background:%(paper)s;border-right:1px solid %(line)s;display:flex;flex-direction:column}
.brand{padding:16px 14px 10px;border-bottom:1px solid %(line2)s}
.brand .k{font:700 9.5px Consolas,monospace;letter-spacing:.13em;text-transform:uppercase;color:%(mut2)s}
.brand h2{font-size:15px;color:%(ink)s;margin-top:3px}
.brand p{font:600 9.5px Consolas,monospace;color:%(teal)s;margin-top:4px}
.nav{flex:1;overflow-y:auto;padding:8px}
.nav .sep{font:700 9px Consolas,monospace;letter-spacing:.12em;color:%(mut2)s;padding:10px 9px 4px;text-transform:uppercase}
.nav button{display:flex;align-items:center;gap:9px;width:100%%;text-align:left;border:1px solid transparent;background:none;border-radius:6px;padding:8px 9px;font-family:inherit;font-size:12px;color:%(ink2)s;cursor:pointer;margin-bottom:2px}
.nav button:hover{background:%(paper2)s;border-color:%(line2)s}
.nav button.on{background:%(ink)s;color:#fff}
.nav .n{font:700 9.5px Consolas,monospace;color:%(mut2)s;width:20px;flex:none}
.nav button.on .n{color:#fff;opacity:.7}
.nav .en{display:block;font-size:9px;opacity:.6}
.foot{border-top:1px solid %(line2)s;padding:9px 14px;font-size:9.5px;color:%(mut)s}
.main{flex:1;height:100vh;overflow:hidden}
.pg{display:none;height:100%%}.pg.on{display:block}
.tin{height:100%%;overflow-y:auto;padding:16px 20px}
.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:13px 16px;margin-bottom:13px;box-shadow:0 1px 2px rgba(27,26,23,.04)}
.card h3{font-size:13px;color:%(ink)s;margin-bottom:8px}
table{width:100%%;border-collapse:collapse;font-size:12px}
th,td{text-align:left;border-bottom:1px solid %(line2)s;padding:6px 8px;vertical-align:top}
th{color:%(mut)s;font-weight:700;font-size:11px}
.r{text-align:right}.mono{font-family:Consolas,monospace;font-size:11.5px}
.small{font-size:11px;color:%(mut)s}
.cmd{font-family:Consolas,monospace;font-size:11.5px;background:%(paper2)s;border:1px solid %(line2)s;border-radius:6px;padding:7px 10px;margin:4px 0;user-select:all}
iframe{width:100%%;height:62vh;border:1px solid %(line)s;border-radius:6px;background:%(paper2)s}
.toggle{font-size:11px;color:%(accent)s;cursor:pointer;text-decoration:underline}
</style></head><body>
<aside class="sb">
<div class="brand"><div class="k">Veritas Intelligence Analytics</div>
<h2>VIA 母系統</h2><p>MOTHER · ONE WINDOW · v0100</p></div>
<div class="nav">%(nav)s</div>
<div class="foot">誠實燈:登錄簿 %(n_ledger)d 筆 · 零 CDN 離線 · 配色佔位候視覺鎖<br>
<span class="toggle" onclick="var d=document.getElementById('docs');d.style.display=d.style.display=='none'?'block':'none'">末頁說明 顯示/隱藏</span></div>
</aside>
<div class="main">%(home)s%(subpages)s%(pkgs_pg)s%(spec_pg)s
<div class="pg" id="pg-docswrap"></div>
</div>
<script>
document.querySelectorAll('.nav button').forEach(function(b){
 b.addEventListener('click',function(){
  document.querySelectorAll('.nav button').forEach(function(x){x.classList.remove('on');});
  document.querySelectorAll('.pg').forEach(function(x){x.classList.remove('on');});
  b.classList.add('on');
  var pg=document.getElementById('pg-'+b.dataset.p);if(!pg)return;pg.classList.add('on');
  var f=pg.querySelector('iframe');
  if(f&&!f.src)f.src=f.dataset.src; /* 懶載 */
 });});
document.querySelector('#pg-home .tin').insertAdjacentHTML('beforeend', %(docs)s);
</script></body></html>""" % dict(T, nav="".join(nav), home=home, subpages="".join(subpages),
                                  pkgs_pg=pkgs_pg, spec_pg=spec_pg, n_ledger=n_ledger,
                                  docs=json.dumps(docs, ensure_ascii=False))
    # 位元組穩定寫出:LF 固定(Windows 預設 CRLF 會弄髒追蹤檔→git pull 被擋)+內容未變不重寫
    data = page.encode("utf-8")
    if OUT.exists() and OUT.read_bytes() == data:
        print("[母頁] 內容未變 — 不重寫(避免弄髒工作樹)· %s" % OUT)
        return 0
    OUT.write_bytes(data)
    print("[母頁] %s(%d KB · 左panel 00+01-07+90/91 · FlowSystem 依令未列)" % (OUT, len(page) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(build())
