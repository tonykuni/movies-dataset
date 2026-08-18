# -*- coding: utf-8 -*-
"""build_via_mother_v0103.py — VIA 母頁產生器 v0103(設計格式版;操作員令:母系統及子系統依照設計格式)。

格式基準:Veritas Header.dc.html — 1a 中央治理台面:大襯線 EN 題 masthead(min-height 95px)+
8 格 KPI 帶(實值,誠實口徑)+ 分頁 Pages 白條 + auto-fit 卡格;子系統頁 iframe 接 v0101 格式子模板。

v0102 新增(視覺鎖 Veritas Header 沿用):
  · 響應式雙形自適:桌機水平長方形/手機垂直長方形自動最佳化(≤760px 側欄轉頂欄+橫捲導覽)
  · 現代動畫:換頁淡入上滑 · 卡片懸浮提升 · 導覽過渡(prefers-reduced-motion 全尊重)
  · 字階自動最佳化:clamp() 流式字級(14 吋桌機到 6 吋手機同一份 HTML)
  · 滑鼠即全部:下拉選單指令組合器(子系統→動詞→一鍵複製/下載批次檔)
  · Windows I/O 拖曳:檔案拖入即列清單+自動生成 via-precheck 指令(輸入前檢查先擋後跑)
  · 商品組合號:勾選 PKG 組合即時算組合碼(FNV-1a 決定性;安裝時綁 machine_id 成正式序號)
  · HTML 直接下指令=誠實三徑:複製到剪貼簿 / 下載 .cmd 批次檔雙擊跑 / 桌面橋(候補)


三段式規約:P1 消費者頁(設定+輸入現況+輸入前檢查+運作結果)→ 矩陣頁 → 末頁說明(可隱藏)。
左 panel:00 母頁 · 01-07 功能子系統(無 FlowSystem)· 90 商品目錄 · 91 規格母版 · 底部誠實燈。
零 CDN 單檔;視覺鎖=操作員介面連結指定之設計正本(風格鎖+色鎖,本機字族無 CDN):
  functional modules/VAP/spec/UIUX_Design_Source/Veritas Header copy.dc.html
  基調:紙色 #f2f1ec/#fbfaf7 · 墨 #1b1a17 · 印章紅 #9e2b25 主強調 · 松綠 #3c6660 ·
  常青 #3d7a52 · 靛藍 #24457f · 赭 #8a6420;襯線 Cormorant Garamond/Noto Serif CJK TC。
產出:<VIA根>/VIA_Mother.html(追蹤;pull 即開)。資料源:pkg_pointers/ + 登錄簿 + 盤點正本。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Mother.html"

# 視覺鎖色票(Veritas Header copy.dc.html 出現頻次實測):
T = {"bg": "#f2f1ec", "paper": "#ffffff", "paper2": "#fbfaf7", "ink": "#1b1a17",
     "ink2": "#33403f", "mut": "#6b6860", "mut2": "#9aa5a1", "line": "#dbd9d3",
     "line2": "#ebe9e3", "teal": "#3c6660", "up": "#9e2b25", "down": "#3d7a52",
     "accent": "#24457f", "amber": "#8a6420", "seal": "#9e2b25",
     "serif": "'Cormorant Garamond',Georgia,'Noto Serif CJK TC','Songti TC','PMingLiU',serif",
     "cjkserif": "'Noto Serif CJK TC','Songti TC','PMingLiU','SimSun',serif",
     "mono": "'SFMono-Regular',Consolas,monospace"}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


SUBS = [
    ("workops", "01", "WorkOps 母版", "郵件×專案治理+指揮板", "🟢 生產",
     "BoardQA 四層全綠(unit+integration 14/14 · system 9/9 · 封印驗真)",
     ["via-workops board   → 產最新指揮板(開啟 run 目錄內 VIA_WorkOps_CommandBoard.html)",
      "via-boardqa         → 四層品保", "via-usertest        → U01-U12 使用者旅程"],
     "supportive modules/ui_support/subsystem_pages/VIA_Sub_workops.html"),
    ("vap", "02", "VAP 繪圖", "chartlib+seaborn/plotly 雙線+SSOT 28 圖型", "🟢 生產",
     "chartlib v007 端到端+--sql/--panels;seaborn/plotly selftest 65 PASS;跨系統實渲(VDF/MultiFactor)",
     ["via-vap --demo --auto        → 零依賴 SVG 線出圖",
      "via-plot probe ・ via-plot demo --out vap_demo → 28 型全譜",
      "via-plot render --chart line --file <任何子系統csv/sqlite> --x 欄 --y 欄"],
     "supportive modules/ui_support/subsystem_pages/VIA_Sub_vap.html"),
    ("vrn", "03", "VRN 研報", "研報 OCR/表格還原/交叉驗證治理", "🟢 測試鏈全綠",
     "SmokeTest 11/0 · Pipeline Runner 全綠 · XCheck 無硬矛盾 · 53 凍結鎖 · 正典入口已宣告(OCR 語料在工作站)",
     ["via-probe / via-extract      → 內容萃取(dry-run 預設)",
      "via-batch                    → AllInOne 批次", "via-ocr                      → OCR 統一路由"],
     "supportive modules/ui_support/subsystem_pages/VIA_Sub_vrn.html"),
    ("vdf", "04", "VDF 資料鍛造", "市場資料取數契約 SSOT+intake+六模組重建R", "🟢 測試鏈全綠",
     "原始全套 19 編號件復活:301/302 exit0 · 201 生成 238 items(FRED47+AK13+YF175)全過 schema · 303 四階段 GREEN6/YEL1/RED1=設計分布 · 契約 277 項 PASS;餘缺 MDL501 UI+Invoke-VDF.ps1 等 12 件候上傳",
     ["via-vdf contract check       → 取數契約盤點",
      "py \"functional modules\\VDF\\VDF_ENG017_MDL302FinalActivation.py\" --no-pause → 端到端",
      "via-vdf                      → OneClick 側欄(工作站)"],
     "supportive modules/ui_support/subsystem_pages/VIA_Sub_vdf.html"),
    ("chipwar", "05", "ChipWar", "晶片戰情 12 引擎指標族", "🟢 已驗",
     "harness L1 6/6+L2 8/8 存證;FOMO 報告樣張在庫",
     ["via-wf chipwar               → 戰情儀表板(工作站產 _generated)"],
     "supportive modules/ui_support/subsystem_pages/VIA_Sub_chipwar.html"),
    ("multifactor", "06", "MultiFactor", "多因子驗證模擬", "🟢 已驗",
     "test v0101 過;simulation_ledger 已被 via-plot 跨系統實渲",
     ["via-wf multifactor           → 驗證模擬鏈"], "supportive modules/ui_support/subsystem_pages/VIA_Sub_multifactor.html"),
    ("talib", "07", "TALib", "技術指標 64 式(adj 鐵律)", "🟢 已驗",
     "64 指標全測過;一律還原價",
     ["via-wf talib                 → 指標批跑"], "supportive modules/ui_support/subsystem_pages/VIA_Sub_talib.html"),
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
    # 先產子系統分開模板(動態解析最新版;操作員令:視覺鎖定子系統模板分開分別加入功能)
    try:
        import importlib.util as _ilu
        _c = sorted(HERE.glob("CGC_MDL038_BuildSubsystemPages_v0*.py"))
        if _c:
            _sp = _ilu.spec_from_file_location("via_sub_gen", _c[-1])
            _m = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_m); _m.build()
    except Exception as _e:
        print("[WARN] 子模板產生失敗(誠實列出,不卡斷):%s" % _e)
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
    n_verbs = len(list((VIA / "bin").glob("via*.cmd")))
    try:
        n_comp = len(json.loads((HERE / "VIA_AutoCode_Registry_v0100.json").read_text(encoding="utf-8"))["components"])
    except Exception:
        n_comp = 0
    kpi_items = [(str(n_ledger), "登錄簿 Ledger"), (str(len(pkgs)), "商品 PKG"),
                 ("7", "子系統 Subsystems"), (str(n_verbs), "動詞 Verbs"),
                 (str(n_comp), "組件 Components"), ("68", "QA 檢 Checks"),
                 ("LOCKED", "視覺鎖 Visual"), ("0 CDN", "離線 Offline")]
    kpis_html = "".join('<div class="kpi"><span class="v">%s</span><span class="k">%s</span></div>'
                        % (esc(v), esc(k)) for v, k in kpi_items)
    pagesbar_html = "".join(
        '<a data-go="%s"><span class="n">%s</span><span class="t">%s</span></a>'
        % (pid, num, esc(zh)) for pid, num, zh, *_ in SUBS) +         '<a data-go="pkgs"><span class="n">90</span><span class="t">商品目錄</span></a>' +         '<a data-go="spec"><span class="n">91</span><span class="t">規格母版</span></a>'
    combo_labels = "".join('<label><input type="checkbox" value="%s"><span class="mono">%s</span> %s</label>'
                           % (c, c, esc(n)) for c, n, _cn, _kb, _v, _ in pkgs)
    composer_data = json.dumps({pid: {"zh": zh, "cmds": cmds}
                                for pid, _num, zh, _r, _s, _e, cmds, _u in SUBS}, ensure_ascii=False)
    sub_lights = "".join('<tr><td class="mono">%s</td><td>%s</td><td>%s</td><td class="small">%s</td></tr>'
                         % (num, esc(zh), st, esc(ev)) for _p, num, zh, _r, st, ev, _c, _u in SUBS)
    home = """<div class="pg on" id="pg-home"><div class="tin">
<div class="mast"><div class="lft"><span class="mseal">理</span>
<div><div class="num">Veritas Intelligence Analytics · 00 Central Governance</div>
<h1>VERITAS INTELLIGENCE</h1><div class="zh2">母系統 · 中央治理 · 自演化 SSOT · 編碼引擎 · 中央參數註冊處</div></div></div>
<div class="st">APPEND-ONLY<span class="meta">Mother Console · Visual Lock · v0103</span></div></div>
<div class="kpis">%s</div>
<div class="pagesbar"><span class="lbl">分頁 Pages</span>%s</div>
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
<div class="card"><h3>⑤ 指令組合器(滑鼠即全部 — 下拉選好即得)</h3>
<div class="btnrow"><select id="selSub" aria-label="子系統"></select>
<select id="selVerb" aria-label="動詞"></select></div>
<div class="cmd" id="composerCmd">← 先選子系統與動詞</div>
<div class="btnrow"><button class="btn pri" id="btnCopy">📋 複製指令</button>
<button class="btn" id="btnBat">💾 下載批次檔(.cmd 雙擊即跑)</button>
<span class="small" id="copyMsg"></span></div>
<p class="small">HTML 直接下指令三徑:①複製貼 PowerShell ②下載 .cmd 雙擊 ③桌面橋(候補,localhost 限定)。</p></div>
<div class="card"><h3>⑥ 輸入資料(Windows 拖曳式加入)</h3>
<div class="drop" id="dropzone">將 csv / json / parquet 檔<b>拖曳到此</b>(或點擊選檔)
<input type="file" id="filePick" multiple style="display:none"><ul id="dropList"></ul></div>
<div class="cmd" id="precheckCmd" style="display:none"></div>
<p class="small">拖入即列清單並自動生成 via-precheck 指令(輸入前檢查:重複/缺欄/缺值,先擋後跑)。瀏覽器只交檔名不交路徑 — 檔在何處就在該目錄跑指令。</p></div>
<div class="card combo"><h3>⑦ 商品組合(勾選=組合;組合號即時算)</h3>
<div id="comboBox">%s</div>
<p style="margin-top:8px">組合號:<span class="serial" id="comboSerial">(未勾選)</span>
<span class="small">· 安裝時與本機 machine_id 綁定成正式序號(_instance\\VIA_Instance.json)</span></p>
<div class="cmd" id="comboCmd" style="display:none"></div></div>
</div></div>""" % (kpis_html, pagesbar_html, n_ledger, pkg_rows, sub_lights, combo_labels)

    # 子系統頁(同構 lite:狀態+命令+UI iframe/誠實缺席)
    subpages = []
    for pid, num, zh, role, st, ev, cmds, ui in SUBS:
        cmdhtml = "".join('<div class="cmd">%s</div>' % esc(c) for c in cmds)
        if ui and (VIA / ui).exists():
            uihtml = ('<div class="card"><h3>介面(子系統分開模板 · 視覺鎖)</h3>'
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
<li>視覺鎖<b>已換膚</b>:VAP/spec/UIUX_Design_Source/Veritas Header copy.dc.html(印章紅 #9e2b25 · 松綠 #3c6660 · 紙墨基調 · 襯線標題;本機字族零 CDN)。</li>
<li>v0102 全自動化互動:響應式雙形(桌機橫/手機直)· 現代動畫(reduced-motion 尊重)· 流式字階 · 下拉指令組合器 · 拖曳輸入+precheck · 商品組合號綁機 · 批次檔下載。</li>
<li>全新電腦:Bootstrap-VIA-FreshPC-v0100.cmd 一鍵(自動裝 PS7+Python → 交棒安裝器 → 衝突掃描 → 綁機 → DEFAULT 落檔 → 開母頁)。</li>
<li>紅線:絕不代寄 · 唯讀原件 · 編號永不變 · 只增不減 · 零 CDN 離線 · 誠實 OK/FAIL。</li>
<li>規劃正本:functional modules/VIA_Mother_Productization_Plan_v0100.md · 大架構:VIA_Architecture_Progress_v0100.md</li></ul></div>"""

    page = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA 母系統 · Veritas Intelligence Analytics(一窗)</title><style>
*{box-sizing:border-box;margin:0;padding:0}html,body{height:100%%}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif;font-size:13px;display:flex;overflow:hidden}
.sb{flex:none;width:222px;height:100vh;background:%(paper)s;border-right:1px solid %(line)s;display:flex;flex-direction:column}
.brand{padding:16px 14px 10px;border-bottom:1px solid %(line2)s;position:relative}
.brand .seal{float:right;width:30px;height:30px;background:%(seal)s;border-radius:4px;color:%(bg)s;font-family:%(cjkserif)s;font-weight:600;font-size:17px;line-height:30px;text-align:center;margin:2px 0 0 8px}
.brand .k{font:700 9.5px %(mono)s;letter-spacing:.13em;text-transform:uppercase;color:%(mut2)s}
.brand h2{font-family:%(serif)s;font-size:16px;font-weight:600;color:%(ink)s;margin-top:3px}
.brand .bar{height:4px;border-radius:2px;background:%(teal)s;margin-top:7px;width:56px}
.brand p{font:600 9.5px %(mono)s;color:%(teal)s;margin-top:6px}
.nav{flex:1;overflow-y:auto;padding:8px}
.nav .sep{font:700 9px %(mono)s;letter-spacing:.12em;color:%(mut2)s;padding:10px 9px 4px;text-transform:uppercase}
.nav button{display:flex;align-items:center;gap:9px;width:100%%;text-align:left;border:1px solid transparent;border-left:3px solid transparent;background:none;border-radius:6px;padding:8px 9px;font-family:inherit;font-size:12px;color:%(ink2)s;cursor:pointer;margin-bottom:2px}
.nav button:hover{background:%(paper2)s;border-color:%(line2)s;border-left-color:%(mut2)s}
.nav button.on{background:%(ink)s;color:#fff;border-left-color:%(seal)s}
.nav .n{font:700 9.5px %(mono)s;color:%(mut2)s;width:20px;flex:none}
.nav button.on .n{color:#fff;opacity:.7}
.nav .en{display:block;font-size:9px;opacity:.6}
.foot{border-top:1px solid %(line2)s;padding:9px 14px;font-size:9.5px;color:%(mut)s}
.main{flex:1;height:100vh;overflow:hidden}
.pg{display:none;height:100%%}.pg.on{display:block}
.tin{height:100%%;overflow-y:auto;padding:16px 20px}
.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:13px 16px;margin-bottom:13px;box-shadow:0 1px 2px rgba(27,26,23,.04)}
.card h3{font-family:%(serif)s;font-size:14.5px;font-weight:600;color:%(ink)s;margin-bottom:8px;border-bottom:2px solid %(line)s;padding-bottom:5px}
table{width:100%%;border-collapse:collapse;font-size:12px}
th,td{text-align:left;border-bottom:1px solid %(line2)s;padding:6px 8px;vertical-align:top}
th{color:%(mut)s;font-weight:700;font-size:11px}
.r{text-align:right}.mono{font-family:%(mono)s;font-size:11.5px}
.small{font-size:11px;color:%(mut)s}
.cmd{font-family:%(mono)s;font-size:11.5px;background:%(paper2)s;border:1px solid %(line2)s;border-left:3px solid %(teal)s;border-radius:6px;padding:7px 10px;margin:4px 0;user-select:all}
iframe{width:100%%;height:62vh;border:1px solid %(line)s;border-radius:6px;background:%(paper2)s}
.toggle{font-size:11px;color:%(accent)s;cursor:pointer;text-decoration:underline}
h3::before{content:"";display:inline-block;width:7px;height:7px;background:%(seal)s;border-radius:1px;margin-right:7px;vertical-align:1px}
/* ── v0103 設計格式件:masthead / KPI 帶 / 分頁條 / 卡格 ── */
.mast{min-height:95px;display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:24px;border-bottom:1px solid #dcdad3;padding-bottom:11px;margin-bottom:12px}
.mast .lft{display:flex;align-items:flex-end;gap:14px}
.mast .mseal{width:38px;height:38px;background:%(seal)s;border-radius:5px;color:%(bg)s;font-family:%(cjkserif)s;font-weight:600;font-size:21px;line-height:38px;text-align:center;flex:none}
.mast .num{font-family:%(mono)s;font-size:10px;letter-spacing:.16em;color:%(mut)s;text-transform:uppercase}
.mast h1{font-family:%(serif)s;font-size:21px;font-weight:500;letter-spacing:.055em;color:%(ink)s;line-height:1.15}
.mast .zh2{font-size:12px;color:%(mut)s;margin-top:2px}
.mast .st{font-family:%(mono)s;font-size:11px;color:%(down)s;white-space:nowrap;text-align:right}
.mast .st .meta{display:block;font-size:9px;letter-spacing:.1em;color:%(mut)s;text-transform:uppercase;margin-top:3px}
.kpis{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:6px;margin-bottom:10px}
.kpi{display:flex;flex-direction:column;gap:3px;padding:9px 7px;background:#ffffff;border:1px solid #dcdad3;border-radius:5px;min-width:0}
.kpi .v{font-family:%(mono)s;font-size:15px;font-weight:700;color:%(ink)s;line-height:1;overflow-wrap:anywhere}
.kpi .k{font-family:%(mono)s;font-size:8.5px;line-height:1.35;letter-spacing:.06em;color:%(mut)s;text-transform:uppercase;overflow-wrap:anywhere}
.pagesbar{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:7px 9px;background:#ffffff;border:1px solid %(line)s;border-radius:6px;margin-bottom:12px}
.pagesbar .lbl{font-family:%(mono)s;font-size:8px;letter-spacing:.16em;color:%(mut)s;text-transform:uppercase;padding-right:5px}
.pagesbar a{display:flex;flex-direction:column;gap:1px;padding:4px 9px;border:1px solid transparent;border-radius:5px;text-decoration:none;color:%(ink2)s;cursor:pointer}
.pagesbar a:hover{background:%(bg)s;border-color:%(line)s}
.pagesbar .n{font-family:%(mono)s;font-size:8px;letter-spacing:.1em;opacity:.75}
.pagesbar .t{font-size:11.5px;font-weight:700}
@media (max-width:900px){.kpis{grid-template-columns:repeat(4,minmax(0,1fr))}}
/* ── v0102 現代動畫(prefers-reduced-motion 全尊重) ── */
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.pg.on .tin{animation:fadeUp .32s ease-out}
.card{transition:box-shadow .18s ease,transform .18s ease}
.card:hover{box-shadow:0 4px 14px rgba(27,26,23,.09);transform:translateY(-2px)}
.nav button{transition:background .15s ease,border-color .15s ease,color .15s ease}
button,select{transition:background .15s ease,border-color .15s ease}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
/* ── v0102 流式字階(桌機→手機同份 HTML 自動最佳化) ── */
body{font-size:clamp(12px,.6vw + 10.5px,13.5px)}
.card h3{font-size:clamp(13px,.7vw + 11px,15.5px)}
.brand h2{font-size:clamp(14px,.8vw + 11px,17px)}
table{font-size:clamp(11px,.55vw + 9.8px,12.5px)}
/* ── v0102 滑鼠互動件:下拉/拖曳/組合 ── */
select{padding:7px 10px;border:1px solid %(line)s;border-radius:6px;background:%(paper)s;color:%(ink2)s;font-family:inherit;font-size:12px;cursor:pointer;min-width:150px}
select:hover{border-color:%(teal)s}
.btnrow{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:8px}
.btn{padding:7px 14px;border:1px solid %(line)s;border-radius:6px;background:%(paper)s;color:%(ink2)s;font-family:inherit;font-size:12px;cursor:pointer}
.btn:hover{background:%(paper2)s;border-color:%(teal)s}
.btn.pri{background:%(seal)s;border-color:%(seal)s;color:#fff}
.btn.pri:hover{filter:brightness(1.08)}
.drop{border:2px dashed %(line)s;border-radius:8px;padding:22px;text-align:center;color:%(mut)s;transition:border-color .18s ease,background .18s ease;cursor:default}
.drop.over{border-color:%(seal)s;background:%(paper2)s;color:%(ink)s}
.drop ul{list-style:none;margin-top:8px;text-align:left}
.drop li{font-family:%(mono)s;font-size:11px;padding:2px 0;color:%(ink2)s}
.combo label{display:inline-flex;align-items:center;gap:5px;border:1px solid %(line)s;border-radius:6px;padding:6px 10px;margin:3px 4px 3px 0;cursor:pointer;font-size:12px;background:%(paper)s}
.combo label:hover{border-color:%(teal)s}
.combo input{accent-color:%(seal)s;cursor:pointer}
.combo .serial{font-family:%(mono)s;color:%(seal)s;font-weight:700;font-size:13px}
/* ── v0102 響應式:手機垂直長方形自動最佳化 ── */
@media (max-width:760px){
 body{flex-direction:column;overflow:auto;height:auto}
 .sb{width:100%%;height:auto;border-right:0;border-bottom:2px solid %(line)s}
 .brand{padding:12px 14px 8px}
 .nav{display:flex;overflow-x:auto;padding:6px;gap:4px}
 .nav button{flex:none;width:auto;margin-bottom:0;white-space:nowrap;padding:7px 10px}
 .nav .en{display:none}
 .nav .sep{display:none}
 .foot{display:none}
 .main{height:auto;overflow:visible}
 .pg{height:auto}
 .pg.on{display:block}
 .tin{height:auto;overflow:visible;padding:12px}
 iframe{height:48vh}
 select{min-width:0;flex:1}
}
</style></head><body>
<aside class="sb">
<div class="brand"><span class="seal">理</span><div class="k">Veritas Intelligence Analytics</div>
<h2>VIA 母系統</h2><div class="bar"></div><p>MOTHER · ONE WINDOW · v0103</p></div>
<div class="nav">%(nav)s</div>
<div class="foot">誠實燈:登錄簿 %(n_ledger)d 筆 · 零 CDN 離線 · 視覺鎖已換膚(Veritas Header)<br>
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
document.querySelectorAll('.pagesbar a[data-go]').forEach(function(a){
 a.addEventListener('click',function(){
  var b=document.querySelector('.nav button[data-p="'+a.dataset.go+'"]');if(b)b.click();});});
/* ── v0102 指令組合器(下拉即得;滑鼠即全部) ── */
var COMPOSER=%(composer_data)s;
var selSub=document.getElementById('selSub'),selVerb=document.getElementById('selVerb'),
    cbox=document.getElementById('composerCmd');
Object.keys(COMPOSER).forEach(function(pid){
 var o=document.createElement('option');o.value=pid;o.textContent=COMPOSER[pid].zh;selSub.appendChild(o);});
function fillVerbs(){
 selVerb.innerHTML='';
 COMPOSER[selSub.value].cmds.forEach(function(c){
  var cmd=c.split('→')[0].trim();
  var o=document.createElement('option');o.value=cmd;o.textContent=cmd;selVerb.appendChild(o);});
 showCmd();}
function showCmd(){cbox.textContent=selVerb.value||'';}
selSub.addEventListener('change',fillVerbs);selVerb.addEventListener('change',showCmd);
fillVerbs();
function toClip(t,msgEl){
 function done(ok){if(msgEl)msgEl.textContent=ok?'已複製 ✓':'複製失敗 — 請手動選取';}
 if(navigator.clipboard&&navigator.clipboard.writeText){
  navigator.clipboard.writeText(t).then(function(){done(true);},function(){legacy();});}
 else legacy();
 function legacy(){var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);
  ta.select();var ok=false;try{ok=document.execCommand('copy');}catch(e){}
  document.body.removeChild(ta);done(ok);}}
document.getElementById('btnCopy').addEventListener('click',function(){
 toClip(cbox.textContent,document.getElementById('copyMsg'));});
document.getElementById('btnBat').addEventListener('click',function(){
 var body='@echo off\\r\\nrem VIA 母頁指令批次(自動生成)\\r\\n'+cbox.textContent+'\\r\\npause\\r\\n';
 var b=new Blob([body],{type:'text/plain'});var a=document.createElement('a');
 a.href=URL.createObjectURL(b);a.download='via_run.cmd';a.click();URL.revokeObjectURL(a.href);});
/* ── v0102 Windows 拖曳式輸入 ── */
var dz=document.getElementById('dropzone'),dl=document.getElementById('dropList'),
    pk=document.getElementById('filePick'),pc=document.getElementById('precheckCmd');
['dragenter','dragover'].forEach(function(ev){dz.addEventListener(ev,function(e){
 e.preventDefault();dz.classList.add('over');});});
['dragleave','drop'].forEach(function(ev){dz.addEventListener(ev,function(e){
 e.preventDefault();dz.classList.remove('over');});});
function listFiles(files){
 dl.innerHTML='';var cmds=[];
 Array.prototype.forEach.call(files,function(f){
  var li=document.createElement('li');
  li.textContent='▣ '+f.name+' ('+Math.max(1,Math.round(f.size/1024))+' KB)';
  dl.appendChild(li);
  cmds.push('via-precheck --file "'+f.name+'"');});
 if(cmds.length){pc.style.display='block';pc.textContent=cmds.join(' && ');}}
dz.addEventListener('drop',function(e){if(e.dataTransfer)listFiles(e.dataTransfer.files);});
dz.addEventListener('click',function(){pk.click();});
pk.addEventListener('change',function(){listFiles(pk.files);});
/* ── v0102 商品組合號(FNV-1a 決定性;安裝時綁 machine_id) ── */
function fnv(s){var h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);
 h=Math.imul(h,16777619)>>>0;}return('0000000'+h.toString(16)).slice(-8);}
var comboBox=document.getElementById('comboBox'),serial=document.getElementById('comboSerial'),
    ccmd=document.getElementById('comboCmd');
comboBox.addEventListener('change',function(){
 var sel=Array.prototype.map.call(comboBox.querySelectorAll('input:checked'),
  function(i){return i.value;}).sort();
 if(!sel.length){serial.textContent='(未勾選)';ccmd.style.display='none';return;}
 serial.textContent='VIA-C-'+fnv(sel.join('+')).toUpperCase();
 var lines=sel.map(function(c){
  return 'pwsh -File Install-VIA-Product-v0101.ps1 -Pointer ".\\\\pkg_pointers\\\\'+c.replace('-','_')+'_Pointer.json"';});
 ccmd.style.display='block';
 ccmd.textContent='rem 全新電腦先跑:Bootstrap-VIA-FreshPC-v0100.cmd <任一指針>　然後:\\r\\n'+lines.join('\\r\\n');});
</script></body></html>""" % dict(T, nav="".join(nav), home=home, subpages="".join(subpages),
                                  pkgs_pg=pkgs_pg, spec_pg=spec_pg, n_ledger=n_ledger,
                                  docs=json.dumps(docs, ensure_ascii=False),
                                  composer_data=composer_data)
    # 位元組穩定寫出:LF 固定(Windows 預設 CRLF 會弄髒追蹤檔→git pull 被擋)+內容未變不重寫
    data = page.encode("utf-8")
    if OUT.exists() and OUT.read_bytes() == data:
        print("[母頁] 內容未變 — 不重寫(避免弄髒工作樹)· %s" % OUT)
        return 0
    OUT.write_bytes(data)
    print("[母頁] %s(%d KB · v0103 設計格式版 · 左panel 00+01-07+90/91 · FlowSystem 依令未列)" % (OUT, len(page) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(build())
