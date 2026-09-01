#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL105_GovernanceConsole — 中央治理主控台(批258;操作員設計稿)
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
用法:python3 CGC_MDL105_GovernanceConsole_v0101.py [--open] | --selftest
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
    "overview": [("測試結果總表", "VIA_UI_TestResults_v0100.html"),
                 ("總入口 Portal", "VIA_UI_Portal_v0100.html")],
    "governance": [("治理矩陣", "VIA_UI_GovernanceMatrix_v0100.html")],
    "ssot": [("指令冊", "VIA_UI_CommandRoster_v0100.html")],
    "support": [("同步狀態台", "VIA_UI_SyncStatus_v0100.html")],
    "vdf": [("資料庫目錄", "VIA_UI_DataCatalog_v0100.html"),
            ("全球市場觀測", "VIA_UI_GlobalMarkets_v0100.html")],
    "vrn": [("券商報告卡", "VIA_UI_ReportCards_v0100.html")],
    "vap": [("TPN 模板冊", "VIA_UI_TemplateRegistry_v0100.html"),
            ("儀表板", "VIA_UI_Dashboard_v0100.html")],
}


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
    # preview 框→現役頁真連結(設計保真:框樣式不動,內容換連結)
    for view, links in LINKS.items():
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
    tpl = tpl.replace("</body>",
                      f'<div style="text-align:center;color:#9aa3ad;'
                      f'font-size:9px;padding:8px">真值時戳 {ts} · '
                      "設計稿=收容 b258 原件保真 · 七閘=既有存證導入"
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
    chk("⑥ 零 CDN+零網路+加速橋", 'src="http' not in page
        and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 中央治理主控台(CGC_MDL105)· 八檢自測(零網路)===")
        return selftest()
    return run("--open" in args)


if __name__ == "__main__":
    sys.exit(main())
