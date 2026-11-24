#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL105_GovernanceConsole — 中央治理主控台(批258;操作員設計稿;批324 連結冊補齊 v0116;批325 +StoryRotation v0117)
====================================================================
操作員令:「U/I 畫面優化簡化以此為主」+上傳 Central Governance
Console 設計稿(淺色雙欄:System Units 導覽/GATE 七閘/Input
Interface;右側單元工作區)。
律:設計稿=收容藍本(VIA_CGC_Console_Design_b258 原件不動);
本引擎=代入真值再生現役頁(設計保真,零重排):
  ①七閘真燈:G00 Root=倉庫在/G01 AST=MDL101 掃可修 0/G02 SSOT=
    registry 冊在/G03 Env=加速器覆蓋 manifest/G04 Data=grid FAIL 0
    /G05 Integration=任務冊全在位/G06 User Test=候操作員(紅=誠實)
  ②KPI 真數(任務冊/短指令/grid 站數)③工作區 preview 框→現役頁
    連結(同夾相對;零 CDN)④Run ID=LIVE 時戳
v0100→v0101(批265 操作員令「轉換各類文件為MD為左邊功能之一+
Prompt Management 也是儲存功能之一」):左欄+二功能鈕(設計母版
.nav-btn/.workspace/meta 三處同構注入,樣式零改=保真):
  ⑧mdconvert 視圖=文件→MD 轉換(ENG075 十一檢引擎+md_to_json;
    接指揮台 mdconvert 任務+CommandDeck 頁)
  ⑨prompts 視圖=Prompt 儲存管理(MDL109 冊;append-only+hash 定
    生死;連 VIA_UI_PromptManager 現役頁)
v0101→v0102(批271 操作員令「從 Console 進去看台股月營收分析/主動
ETF 持股分析;系統狀況說明自動接」):
  ⑨VDF 視圖直連二分析現役頁(ETF×共識/營收×共識;批264 產)
  ⑩overview 視圖+三軌測試矩陣(系統狀況=自動接存證頁)
v0102→v0103(批277 操作員令「將 VIA 總管理與各系統一個 U/I 架構
完成」):單一 U/I 架構收編——ui_support 全頁族(28 族)自動盤點
(尾版 glob),PAGE_ROSTER 定唯一歸屬(總管理/七區),每 workspace
區尾注入「頁面冊」;未分類族=support 區誠實列(零漏頁);⑩檢=
全族覆蓋守恆。主控台自此=總管理+各系統唯一入口架構。
v0103→v0104(批278 操作員令「100% 視覺鎖定」+元件冊):
  ①設計鎖:b258 設計稿(sha d9732989…)=100% 視覺鎖定正本(操作員
    重傳同 hash 檔=SKIP_IDENTICAL 再確認);樣式表/版面永不改,
    真值/連結注入僅用設計自身元件類=視覺零新樣式
  ②PAGE_ROSTER+ComponentRoster(MDL111 元件盤點冊→ssot 區)
v0113→v0114(批307「用擷取數據做最佳分類法:LEAD/LAG+大中小+價格指數」):
vdf 區+族群分類×價格指數頁(ENG070;三加權並立 T-1 律)+ROSTER 歸屬。
v0112→v0113(批306 操作員令「先把 VRN 做出來符合剛上傳的模板」):
vrn 區+VRN 控制塔連結(ENG079 產;Codex 模板版面=固定 header 徽章列
/可收欄/頁籤/固定 footer;產出索引真掃+共識雙 Plotly)+ROSTER 歸屬。
v0111→v0112(批302 操作員令「總控及各子系統如圖示 UI」):四區
各補「現況台(統一殼)」連結+PAGE_ROSTER 四殼族歸屬(MDL116 統一
版型殼引擎產;左欄編號導航+規格帶+統計卡+響應雙態)。
v0110→v0111(批301 六維稽核實錘=VAP 無點擊入口):vap 區補二連結
——VAP 分析台 /vapdeck(樞紐在線頁)+標準儀表板 StdDashboard 現產頁;
四系統自此皆有主控台點擊入口(deck 亦同批 +std_dashboard 一鍵任務)。
v0104→v0105(批279):+StdDashboard(ENG014 標準儀表板模板→vap
區;頁=日更再生類不入 git,工作站引擎現產)。
v0105→v0106(批280 重新規劃):①SystemAtlas(MDL112 現況總圖=
新主畫面)入 overview 置首 ②b280 讓位:Hub 舊版 8 件+VAPConsole
→_retired_b280(manifest 存證;Template_SysMan=sysman 模板輸入
不可動)。
v0106→v0107(批281):+MasterControl(VIA_SYSTEM_MANAGER 總控頁
→governance 區)。
v0107→v0108(批287):+UnifiedRegister(MDL113 統一編號冊→ssot 區)。
v0108→v0109(批288):+CommandCenter(MDL114 AIO 健康總圖→governance 區)。
v0109→v0110(批296):+SSOTRegexDict(MDL115 中央 Regex/同義字治理→ssot 區)。
用法:python3 CGC_MDL105_GovernanceConsole_v0110.py [--open] | --selftest
"""
from __future__ import annotations
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

import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
TPL = (VIA / "supportive modules" / "references" / "intake"
       / "VIA_CGC_Console_Design_b258" / "preview.html")
OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_GovernanceConsole_v0100.html"  # 頁名穩定律:連結網/VIA-ALL 皆指此名;版前進=引擎,頁=同名刷新

LINKS = {
    "overview": [("系統現況總圖 Atlas", "VIA_UI_SystemAtlas_v0100.html"),
                 ("CGC 現況台(統一殼)", "VIA_UI_Shell_CGC_v0100.html"),
                 ("測試結果總表", "VIA_UI_TestResults_v0100.html"),
                 ("三軌測試矩陣", "VIA_UI_TriTestMatrix_v0100.html"),
                 ("總入口 Portal", "VIA_UI_Portal_v0100.html")],
    "governance": [("治理矩陣", "VIA_UI_GovernanceMatrix_v0100.html"),
                   # 批324:CGC 殼=全功能整合殼(分析台四頁籤內嵌+全頁索引)
                   ("VAP 分析台(已整合於 CGC 殼)", "VIA_UI_Shell_CGC_v0100.html#deck"),
                   ("全頁索引(CGC 殼)", "VIA_UI_Shell_CGC_v0100.html#allpages"),
                   ("系統控制台", "VIA_UI_SystemConsole_v0100.html"),
                   ("指令甲板", "VIA_UI_CommandDeck_v0100.html")],
    "ssot": [("指令冊", "VIA_UI_CommandRoster_v0100.html")],
    "support": [("同步狀態台", "VIA_UI_SyncStatus_v0100.html")],
    "vdf": [("VDF 現況台(統一殼)", "VIA_UI_Shell_VDF_v0100.html"),
            ("族群回測 Group Backtest(ENG071)", "VIA_UI_GroupBacktest_v0100.html"),
            ("族群分類×價格指數(批307)", "VIA_UI_GroupClassIndex_v0100.html"),
            ("故事族群輪動橋接 v0.5(批325;ENG072)", "VIA_UI_StoryRotation_v0100.html"),
            ("主動 ETF×共識分析", "VIA_UI_ETFConsensusAnalysis_v0100.html"),
            ("月營收×共識分析", "VIA_UI_RevenueConsensusAnalysis_v0100.html"),
            ("資料庫目錄", "VIA_UI_DataCatalog_v0100.html"),
            ("全球市場觀測", "VIA_UI_GlobalMarkets_v0100.html")],
    "vrn": [("VRN 控制塔(Codex 模板版面;批306)", "VIA_UI_VRNControlTower_v0100.html"),
            ("VRN 現況台(統一殼)", "VIA_UI_Shell_VRN_v0100.html"),
            ("券商報告卡", "VIA_UI_ReportCards_v0100.html"),
            ("每日觀察", "VIA_UI_DailyBrief_v0100.html"),
            # 批324 操作員令「完成系統與 U/I 連結」:VRN 殼直連二共識分析頁(跨區 VDF 產出;歸屬冊不變)
            ("月營收×共識分析(跨區 VDF)", "VIA_UI_RevenueConsensusAnalysis_v0100.html"),
            ("主動 ETF×共識分析(跨區 VDF)", "VIA_UI_ETFConsensusAnalysis_v0100.html")],
    "vap": [("VAP 現況台(統一殼)", "VIA_UI_Shell_VAP_v0100.html"),
            ("TPN 模板冊", "VIA_UI_TemplateRegistry_v0100.html"),
            ("儀表板", "VIA_UI_Dashboard_v0100.html"),
            ("VAP 分析台(樞紐在線)", "http://127.0.0.1:8765/vapdeck"),
            ("標準儀表板(三頁 Plotly)", "VIA_UI_StdDashboard_v0100.html")],
}


# 批277:單一 U/I 架構歸屬冊(頁族→區;唯一歸屬=零重複零漏)
PAGE_ROSTER = {
    "Portal": "overview", "TestResults": "overview", "TriTestMatrix": "overview",
    "VRNControlTower": "vrn", "GroupClassIndex": "vdf",
    "GroupBacktest": "vdf", "StoryRotation": "vdf",
    "Shell_CGC": "governance", "Shell_VDF": "vdf",
    "Shell_VRN": "vrn", "Shell_VAP": "vap",
    "GovDeck": "governance", "GovernanceMatrix": "governance",
    "CommandDeck": "governance", "SystemConsole": "governance",
    "UserTestDebug": "governance", "SystemTestPages": "governance",
    "CommandRoster": "ssot", "Charter": "ssot",
    "ComponentRoster": "ssot",
    "UnifiedRegister": "ssot",
    "SSOTRegexDict": "ssot",
    "SyncStatus": "support", "SystemHub": "support", "Hub": "support",
    "BaseTemplate": "support", "Template_SysMan": "support",
    "DataCatalog": "vdf", "GlobalMarkets": "vdf",
    "ETFConsensusAnalysis": "vdf", "RevenueConsensusAnalysis": "vdf",
    "ReportCards": "vrn", "DailyBrief": "vrn",
    "Dashboard": "vap", "TemplateRegistry": "vap",
    "VapDeck": "vap",
    "StdDashboard": "vap",
    "SystemAtlas": "overview",
    "MasterControl": "governance",
    "CommandCenter": "governance",
    "PromptManager": "prompts",
    "GovernanceConsole": None,               # 本頁自身=架構殼,不自列
}


def page_families() -> dict:
    """ui_support 全頁族盤點(尾版 glob;族名=去 _vNNNN)"""
    import re as _re
    ui = VIA / "supportive modules" / "ui_support"
    fam: dict = {}
    for f in sorted(ui.glob("VIA_UI_*.html")):
        base = _re.sub(r"_v\d+$", "", f.stem)[len("VIA_UI_"):]
        fam[base] = f.name                    # sorted=尾版最後覆寫
    return fam


NAV_ADD = (
    '<button class="nav-btn" data-view="mdconvert">▨ 文件→MD 轉換 '
    '<span class="tag">MD</span></button>'
    '<button class="nav-btn" data-view="prompts">✎ Prompt 管理 '
    '<span class="tag">LIB</span></button>')
SEC_ADD = """
    <section class="workspace hidden" id="mdconvert">
      <div class="grid2">
        <div class="card"><div class="card-h">文件→MD 轉換(批265)</div>
        <div class="card-b">
          <div class="flow"><span class="node">docx/pdf/html/txt</span>
          <span class="arr">→</span><span class="node">ENG075 十一檢</span>
          <span class="arr">→</span><span class="node">.md + .json sidecar</span></div>
          <p style="font-size:10px;color:var(--muted)">正主=VRN_ENG075
          DocToMarkdown 尾版(markitdown 正道+內建後備;券商衍生物
          不入 git 紅線;產物=VIA_Reports/md_out)</p>
        </div></div>
        <div class="card"><div class="card-h">執行與產物</div>
        <div class="card-b"><div class="preview">
          <a href="VIA_UI_CommandDeck_v0100.html" style="color:var(--blue)">指揮台跑 mdconvert 任務</a> ·
          工作站短令 <b>via-md</b><br>產物冊:VIA_Reports/md_out/(本機)
        </div></div></div>
      </div>
    </section>
    <section class="workspace hidden" id="prompts">
      <div class="grid2">
        <div class="card"><div class="card-h">Prompt 儲存律(批265)</div>
        <div class="card-b">
          <table class="table"><tr><th>Rule</th><th>Policy</th></tr>
          <tr><td>儲存</td><td>append-only 只增不減零刪除</td></tr>
          <tr><td>冪等</td><td>hash 定生死(同文=SKIP)</td></tr>
          <tr><td>版本</td><td>異文=新版;舊標 SUPERSEDED 本文保留</td></tr>
          <tr><td>取用</td><td>UI 一鍵複製 / CLI get</td></tr></table>
        </div></div>
        <div class="card"><div class="card-h">Prompt Workspace</div>
        <div class="card-b"><div class="preview">
          <a href="VIA_UI_PromptManager_v0100.html" style="color:var(--blue)">Prompt 管理冊(現役頁)</a><br>
          CLI:python MDL109 add --id 名 --title 題 --file 檔
        </div></div></div>
      </div>
    </section>
"""
META_ADD = (' mdconvert:["文件→MD 轉換","ENG075 · markitdown 正道 · '
            '.md+.json Sidecar"],\n prompts:["Prompt 管理",'
            '"append-only 儲存 · hash 冪等 · 版本回溯"],')


def gates() -> dict:
    """七閘真燈(全讀既有存證;缺=黃=誠實)"""
    g: dict = {}
    g["G00"] = "g" if (VIA / "VIA.ps1").exists() else "r"
    grid_p = sorted((VIA / "VIA_Reports").rglob("GRID_*.json"))
    fails = None
    if grid_p:
        d = json.loads(grid_p[-1].read_text(encoding="utf-8"))
        rows = d if isinstance(d, list) else \
            d.get("results") or d.get("rows") or list(d.values())[0]
        fails = sum(1 for r in rows
                    if str(r.get("state", "")).upper().startswith("FAIL"))
    g["G04"] = "g" if fails == 0 else ("y" if fails is None else "r")
    g["G01"] = g["G04"]                       # AST 站含於 grid(sysman)
    g["G02"] = "g" if (HERE / "VIA_AutoCode_Registry_v0100.json").exists() \
        else "y"
    g["G03"] = "g" if list((VIA / "VIA_Reports" / "accel_coverage")
                           .glob("inject_*.json")) else "y"
    try:
        deck = sorted(HERE.glob("CGC_MDL095_DeckServer_v*.py"))[-1]
        spec = importlib.util.spec_from_file_location("m95c", deck)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        T = m.task_registry()
        ok = sum(1 for t in T.values()
                 if t["argv"][1] and Path(str(t["argv"][1])).exists())
        g["G05"] = "g" if ok == len(T) else "r"
        g["tasks"] = len(T)
    except Exception:
        g["G05"], g["tasks"] = "y", "?"
    g["G06"] = "r"                            # 候操作員實測=誠實紅
    return g


def render() -> str:
    tpl = TPL.read_text(encoding="utf-8")
    g = gates()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    for gid in ("G00", "G01", "G02", "G03", "G04", "G05", "G06"):
        tpl = re.sub(
            r'(<span class="gate-id">' + gid +
            r'</span><span>[^<]*</span><span class="light) [gyr]("></span>)',
            r"\1 " + g[gid] + r"\2", tpl)
    tpl = tpl.replace("Run ID: PREVIEW", f"LIVE · {ts}")
    tpl = tpl.replace(
        'value="C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics"',
        'value="C:\\Users\\tonyk\\movies-dataset\\VeritasIntelligenceAnalytics"')
    tpl = tpl.replace('<div class="n">7</div><div class="l">Gate Checks',
                      f'<div class="n">{g["tasks"]}</div><div class="l">'
                      '指揮台任務(尾版)', 1)
    # overview 區無 preview 框(v0100 起 regex 靜默空轉=批271 揪蟲)
    # →專道:連結列注入 Current State 卡頭下(設計保真,樣式零改)
    ov = " · ".join(f'<a href="{f}" style="color:var(--blue)">{n}</a>'
                    for n, f in LINKS["overview"])
    tpl = tpl.replace(
        '<div class="card-h">Current State</div>',
        '<div class="card-h">Current State · 自動接存證</div>'
        '<div style="padding:7px 12px 0;font-size:10px">' + ov + "</div>", 1)
    # preview 框→現役頁真連結(設計保真:框樣式不動,內容換連結)
    for view, links in LINKS.items():
        if view == "overview":
            continue
        a = " · ".join(f'<a href="{f}" style="color:var(--blue)">{n}</a>'
                       for n, f in links)
        tpl = re.sub(
            r'(<section class="workspace[^"]*" id="' + view +
            r'">(?:(?!</section>).)*?<div class="preview">)(?:(?!</div>).)*?(</div>)',
            r"\1" + a + r"\2", tpl, flags=re.S)
    # 批265:左欄二功能(母版三處同構注入=設計保真)
    tpl = tpl.replace(
        '<button class="nav-btn" data-view="vap">▥ VAP · AutoPlot '
        '<span class="tag">VIZ</span></button>',
        '<button class="nav-btn" data-view="vap">▥ VAP · AutoPlot '
        '<span class="tag">VIZ</span></button>' + NAV_ADD)
    tpl = tpl.replace("  </main>", SEC_ADD + "  </main>")
    tpl = tpl.replace(' vap:["VAP', META_ADD + '\n vap:["VAP')
    # 批277:單一 U/I 架構——各區尾注入「頁面冊」(尾版真連結;
    # 未分類族=support 誠實列=零漏頁)
    import re as _re2
    fam = page_families()
    by_view: dict = {}
    for base, fname in fam.items():
        view = PAGE_ROSTER.get(base, "__UNROSTERED__")
        if view is None:
            continue
        by_view.setdefault("support" if view == "__UNROSTERED__" else view,
                           []).append((base, fname,
                                       view == "__UNROSTERED__"))
    for view, pages in by_view.items():
        links = " · ".join(
            f'<a href="{f}" style="color:var(--blue)">{b}</a>'
            + ("<small>(未分類=誠實列)</small>" if un else "")
            for b, f, un in sorted(pages))
        block = ('<div style="padding:8px 12px;border-top:1px dashed '
                 'var(--line);font-size:10px"><b style="font-size:9px;'
                 'letter-spacing:.08em">頁面冊</b> · ' + links + "</div>")
        tpl = _re2.sub(
            r'(<section class="workspace[^"]*" id="' + view + r'">)((?:(?!</section>).)*)(</section>)',
            lambda m: m.group(1) + m.group(2) + block + m.group(3),
            tpl, count=1, flags=_re2.S)
    tpl = tpl.replace("</body>",
                      f'<div style="text-align:center;color:#9aa3ad;'
                      f'font-size:9px;padding:8px">真值時戳 {ts} · '
                      "設計稿 b258=100% 視覺鎖定(批278;sha d9732989)· 七閘=既有存證導入"
                      "(G06 候操作員=誠實紅)</div></body>")
    return tpl


def run(open_after: bool = False) -> int:
    if not TPL.exists():
        print("[主控台] 設計稿收容缺=誠實停")
        return 2
    OUT.write_text(render(), encoding="utf-8")
    print(f"[UI] {OUT.name} · 中央治理主控台(設計保真+七閘真燈)")
    if open_after:
        try:
            import webbrowser
            webbrowser.open(OUT.as_uri())
        except Exception:
            pass
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 設計稿收容在位(原件不動+manifest)", TPL.exists()
        and (TPL.parent / "_INTAKE_MANIFEST.json").exists())
    rc = run()
    page = OUT.read_text(encoding="utf-8")
    g = gates()
    chk("② 七閘真燈代入(G04=grid 存證;G06=誠實紅)", rc == 0
        and g["G06"] == "r"
        and f'<span class="gate-id">G04</span><span>Data Contract</span>'
            f'<span class="light {g["G04"]}"></span>' in page)
    chk("③ 設計保真(淺色主題/雙欄/GATE 卡原樣)",
        "--navw:308px" in page and "GATE · 系統閘門" in page)
    chk("④ 現役頁真連結(preview 框換連結;DataCatalog/ReportCards/TPN)",
        all(k in page for k in ("VIA_UI_DataCatalog_v0100.html",
                                "VIA_UI_ReportCards_v0100.html",
                                "VIA_UI_TemplateRegistry_v0100.html")))
    chk("⑤ LIVE 時戳+真值腳註(非 PREVIEW)", "LIVE ·" in page
        and "Run ID: PREVIEW" not in page and "誠實紅" in page)
    chk("⑦ 左欄二功能注入(mdconvert+prompts 三處同構)",
        'data-view="mdconvert"' in page and 'data-view="prompts"' in page
        and 'id="mdconvert"' in page and 'id="prompts"' in page
        and 'mdconvert:["文件→MD 轉換"' in page)
    chk("⑧ 二功能真連結(CommandDeck+PromptManager 現役頁)",
        "VIA_UI_CommandDeck_v0100.html" in page
        and "VIA_UI_PromptManager_v0100.html" in page
        and (VIA / "supportive modules" / "ui_support"
             / "VIA_UI_PromptManager_v0100.html").exists())
    chk("⑨ VDF 直連二分析頁+overview 三軌矩陣(批271)",
        all(k in page for k in ("VIA_UI_ETFConsensusAnalysis_v0100.html",
                                "VIA_UI_RevenueConsensusAnalysis_v0100.html",
                                "VIA_UI_TriTestMatrix_v0100.html"))
        and all((VIA / "supportive modules" / "ui_support" / f).exists()
                for f in ("VIA_UI_ETFConsensusAnalysis_v0100.html",
                          "VIA_UI_RevenueConsensusAnalysis_v0100.html",
                          "VIA_UI_TriTestMatrix_v0100.html")))
    fam = page_families()
    placed = sum(1 for b, f, in [(b, f) for b, f in fam.items()]
                 if PAGE_ROSTER.get(b, "x") is None or f in page)
    chk("⑩ 單一架構全族覆蓋守恆(批277:每頁族入冊或=本頁自身)",
        placed == len(fam) and len(fam) >= 25,
        f"({placed}/{len(fam)} 族)")
    chk("⑥ 零 CDN+零網路+加速橋", 'src="http' not in page
        and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 中央治理主控台(CGC_MDL105)· 十檢自測(零網路)===")
        return selftest()
    return run("--open" in args)


if __name__ == "__main__":
    sys.exit(main())
