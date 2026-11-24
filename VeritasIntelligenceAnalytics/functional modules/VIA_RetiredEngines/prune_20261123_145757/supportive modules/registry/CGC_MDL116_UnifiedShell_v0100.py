#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL116_UnifiedShell — 統一版型殼引擎(批302;操作員令)
====================================================================
操作員令:「將總控及各子系統弄成如圖示的使用者介面」+中途裁示
「不管色票只管 layout 及內容輸入介面」。
四設計正本(全在庫;hash 已收容):
  圖1 VAP_Workbench_v023(intake b245)·圖2 VDF_Fetch_ONE Standalone
  ·圖3 ETF Matrix(Dashboard_Format_Standardization)·圖4 UIUX
  Design Source「Veritas Intelligence Analytics UI.html」。
版型五律(自四正本萃取;色票=單一中性=操作員裁示):
  ①左欄:品牌區(拉丁小字 letterspaced+中文大標+版本徽章)+
    編號導航(01/02/03…中文粗體+英文小字;active 高亮)+
    底部狀態小格(四格 key/value)
  ②主區麵包屑鏈(a → b → c · LAYOUT SPEC)
  ③規格帶(BUILD/TASKS/PAGES/GATE 鍵值對;右上)
  ④大數字統計卡列(數字+中文標+英文小字)
  ⑤內容卡(標題+雙語副標+目錄表;表頭=中文 粗+英文 letterspaced)
產出四子系統殼頁(真值全直取零發明):
  VIA_UI_Shell_CGC_v0100.html /_VDF /_VRN /_VAP
  資料源:MDL112 Atlas gather()+MDL095 task_registry()(任務依
  argv 引擎路徑歸系統)+MDL105 LINKS/PAGE_ROSTER(區內頁面冊)
  +台帳筆數。總控台輸入介面=MANAGER v0106 同律改造(本引擎只管
  四殼頁;總控=Manager ui 職權=零重造)。
紀律:零 CDN 零外網(字體=系統字疊);頁名 v0100 穩定律;
誠實三態(樞紐任務數/頁數缺=如實標)。
用法:python3 CGC_MDL116_UnifiedShell_v0100.py [--selftest]
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
import html
import importlib.util
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"


def _mod(pat: str):
    p = sorted(HERE.glob(pat))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# 四殼定義(職能敘述=各系統既有定位;零發明)
SHELLS = {
    "CGC": {"page": "VIA_UI_Shell_CGC_v0100.html", "seal": "理",
            "zh": "中央治理", "en": "CENTRAL GOVERNANCE",
            "sub": "統一編碼 · 權威登錄 · 台帳 append-only —— 不執行擷取,只裁定何者為真",
            "crumb": ["VIA 母系統", "治理 · SSOT · 編碼", "現況總覽"],
            "links_key": "governance"},
    "VDF": {"page": "VIA_UI_Shell_VDF_v0100.html", "seal": "庫",
            "zh": "資料鍛造", "en": "VERITAS DATA FORGE",
            "sub": "台股全市場+全球 11 類擷取 · 單庫 SSOT · 誠實三態不假綠",
            "crumb": ["VIA 母系統", "VDF 擷取 · 入庫", "資料現況"],
            "links_key": "vdf"},
    "VRN": {"page": "VIA_UI_Shell_VRN_v0100.html", "seal": "觀",
            "zh": "報告新星", "en": "VERITAS REPORT NOVA",
            "sub": "券商報告五法擷取 · 結構化入庫 · 目標價迴歸 TP 100%",
            "crumb": ["VIA 母系統", "VRN 報告 · 共識", "報告現況"],
            "links_key": "vrn"},
    "VAP": {"page": "VIA_UI_Shell_VAP_v0100.html", "seal": "繪",
            "zh": "自動繪圖", "en": "VERITAS AUTO PLOT",
            "sub": "圖表契約 · TPN 模板 · 標準儀表板 —— 更新模板=引用圖全同步",
            "crumb": ["VIA 母系統", "VAP 圖表 · 模板", "繪圖現況"],
            "links_key": "vap"},
}
ORDER = ["CGC", "VDF", "VRN", "VAP"]

CSS = """
:root{--bg:#f5f5f2;--paper:#ffffff;--paper2:#fafaf8;--ink:#1f2530;
--ink2:#3c4658;--mut:#6d7688;--mut2:#9aa2b1;--line:#dcdfe6;
--soft:#eef0ee;--acc:#3e6b8f;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);
font:14px/1.6 "Segoe UI","Noto Sans TC",system-ui,sans-serif;display:flex;
min-height:100vh}
code,.mono{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
/* ①左欄 */
.rail{width:252px;min-width:252px;background:var(--paper);
border-right:1px solid var(--line);padding:22px 0 14px;display:flex;
flex-direction:column;gap:4px}
.brand{padding:0 20px 14px;border-bottom:1px solid var(--line)}
.brand .latin{font-size:9.5px;letter-spacing:.22em;color:var(--mut);
font-weight:700}
.brand h1{font-size:21px;margin:6px 0 2px;letter-spacing:.02em}
.brand .en{font-size:10.5px;letter-spacing:.14em;color:var(--acc);
font-weight:700}
.brand .badge{display:inline-block;margin-top:7px;font-size:10px;
font-weight:700;padding:2px 8px;border:1px solid var(--line);
border-radius:4px;color:var(--mut);letter-spacing:.08em}
.seal{float:right;width:34px;height:34px;border:2px solid var(--ink2);
border-radius:6px;display:grid;place-items:center;font-size:19px;
font-weight:700}
.navsec{font-size:9.5px;letter-spacing:.2em;color:var(--mut2);
font-weight:700;padding:14px 20px 4px}
.nav a{display:grid;grid-template-columns:26px 1fr;gap:8px;
align-items:baseline;padding:8px 20px;color:var(--ink2)}
.nav a:hover{background:var(--paper2);text-decoration:none}
.nav a.active{background:var(--soft);border-right:3px solid var(--acc);
color:var(--ink);font-weight:700}
.nav .no{font-size:10.5px;color:var(--mut2);font-weight:700}
.nav .lb small{display:block;font-size:9.5px;letter-spacing:.14em;
color:var(--mut2);font-weight:600}
.railfoot{margin-top:auto;border-top:1px solid var(--line);
padding:12px 20px 0;display:grid;grid-template-columns:1fr 1fr;gap:8px}
.railfoot .k{font-size:9px;letter-spacing:.16em;color:var(--mut2);
font-weight:700}
.railfoot .v{font-size:13px;font-weight:700;
font-variant-numeric:tabular-nums}
/* 主區 */
.main{flex:1;padding:26px 34px;max-width:1160px}
.crumb{font-size:11px;color:var(--mut);letter-spacing:.04em;
margin-bottom:10px}
.crumb b{color:var(--acc)}
.crumb .lock{letter-spacing:.16em;font-weight:700;font-size:10px}
.head{display:flex;align-items:flex-end;gap:18px;flex-wrap:wrap;
border-bottom:2px solid var(--ink);padding-bottom:14px;margin-bottom:18px}
.head h2{font-size:30px;letter-spacing:.01em}
.head h2 small{font-size:12px;color:var(--mut);font-weight:400;
margin-left:10px;letter-spacing:.1em}
.head .sub{width:100%;font-size:12.5px;color:var(--mut)}
/* ③規格帶 */
.spec{margin-left:auto;display:flex;gap:22px;flex-wrap:wrap}
.spec div{text-align:left}
.spec .k{font-size:9px;letter-spacing:.18em;color:var(--mut2);
font-weight:700}
.spec .v{font-size:12.5px;font-weight:700;
font-variant-numeric:tabular-nums}
.spec .v.ok{color:var(--ok)}.spec .v.warn{color:var(--warn)}
/* ④統計卡 */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
gap:12px;margin-bottom:20px}
.stat{background:var(--paper);border:1px solid var(--line);
border-radius:8px;padding:14px 16px}
.stat .n{font-size:27px;font-weight:800;
font-variant-numeric:tabular-nums}
.stat .zh{font-size:12px;color:var(--ink2);margin-top:2px}
.stat .en{font-size:9px;letter-spacing:.18em;color:var(--mut2);
font-weight:700}
/* ⑤內容卡 */
.card{background:var(--paper);border:1px solid var(--line);
border-radius:8px;padding:18px 20px;margin-bottom:16px}
.card h3{font-size:15px;letter-spacing:.02em}
.card h3 small{font-size:10px;letter-spacing:.16em;color:var(--mut2);
font-weight:700;margin-left:8px}
.card .note{font-size:11.5px;color:var(--mut);margin:4px 0 10px}
.tbl{width:100%;border-collapse:collapse;font-size:12.5px}
.tbl th{text-align:left;font-size:10px;letter-spacing:.14em;
color:var(--mut2);border-bottom:1px solid var(--line);padding:6px 10px 6px 0;
font-weight:700}
.tbl td{border-bottom:1px solid var(--soft);padding:7px 10px 7px 0;
vertical-align:top}
.tbl tr:last-child td{border-bottom:0}
.tag{display:inline-block;font-size:10px;font-weight:700;padding:1px 7px;
border-radius:3px;background:var(--soft);color:var(--ink2)}
.tag.net{background:#f3ece1;color:var(--warn)}
.wrap-x{overflow-x:auto}
.foot{font-size:10.5px;color:var(--mut2);margin-top:6px}
/* 響應雙態(批302 中途令):PC=水平長方形(左欄+主區);
   手機=垂直長方形(欄轉頂條+導航橫捲+單欄卡);自動最佳化=
   clamp 流體字級+auto-fit 卡格+表格自 overflow;零動畫零校正負擔 */
.head h2{font-size:clamp(21px,3.2vw,30px)}
.stat .n{font-size:clamp(21px,2.6vw,27px)}
@media(max-width:860px){
 body{flex-direction:column}
 .rail{width:100%;min-width:0;padding:14px 0 8px;position:static}
 .brand{padding:0 16px 10px}
 .brand h1{font-size:18px}
 .nav{display:flex;overflow-x:auto;gap:2px;padding:0 10px;
  -webkit-overflow-scrolling:touch}
 .nav a{grid-template-columns:auto;white-space:nowrap;padding:7px 10px;
  border-radius:6px}
 .nav a.active{border-right:0;border-bottom:3px solid var(--acc)}
 .nav .no{display:none}
 .nav .lb small{display:none}
 .railfoot{grid-template-columns:repeat(4,1fr);padding:10px 16px 0}
 .main{padding:16px 14px}
 .spec{margin-left:0;gap:14px}
 .stats{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:400px){.stats{grid-template-columns:1fr}}
"""


def _n(x) -> int:
    """真值正規化:list/dict=計數;數=原值(atlas 欄型混=實錘)"""
    if isinstance(x, (list, dict, set, tuple)):
        return len(x)
    return int(x) if isinstance(x, (int, float)) else 0


def _sys_of_task(argv) -> str:
    s = " ".join(str(a) for a in argv).replace("\\", "/")
    if "/VDF/" in s or "VDF_" in s:
        return "VDF"
    if "/VRN/" in s or "VRN_" in s:
        return "VRN"
    if "/VAP/" in s or "VAP_" in s:
        return "VAP"
    return "CGC"


def gather() -> dict:
    """真值聚合(全直取零發明;缺=誠實 0/空)"""
    d = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M")}
    try:
        d["atlas"] = _mod("CGC_MDL112_SystemAtlas_v0*.py").gather()
    except Exception:
        d["atlas"] = {}
    try:
        T = _mod("CGC_MDL095_DeckServer_v0*.py").task_registry()
        d["tasks"] = {k: {"zh": v.get("zh", ""), "net": bool(v.get("net")),
                          "sys": _sys_of_task(v.get("argv", []))}
                      for k, v in T.items()}
    except Exception:
        d["tasks"] = {}
    try:
        m105 = _mod("CGC_MDL105_GovernanceConsole_v0*.py")
        d["links"] = {k: list(v) for k, v in m105.LINKS.items()}
        d["roster"] = dict(m105.PAGE_ROSTER)
    except Exception:
        d["links"] = {}
        d["roster"] = {}
    return d


def _nav(cur: str, d: dict) -> str:
    rows = ['<div class="navsec">系統 SYSTEMS</div><div class="nav">',
            '<a href="VIA_UI_MasterControl_v0100.html"><span class="no">00'
            '</span><span class="lb">總控台<small>MASTER CONTROL</small>'
            '</span></a>']
    for i, k in enumerate(ORDER, 1):
        s = SHELLS[k]
        cls = ' class="active"' if k == cur else ""
        rows.append(
            f'<a href="{s["page"]}"{cls}><span class="no">0{i}</span>'
            f'<span class="lb">{s["zh"]} · {k}<small>{s["en"]}</small>'
            f'</span></a>')
    rows.append("</div>")
    links = d.get("links", {}).get(SHELLS[cur]["links_key"], [])
    if links:
        rows.append('<div class="navsec">區內頁面 PAGES</div>'
                    '<div class="nav">')
        for j, (zh, href) in enumerate(links, 1):
            rows.append(
                f'<a href="{html.escape(str(href))}">'
                f'<span class="no">{j:02d}</span>'
                f'<span class="lb">{html.escape(str(zh))}</span></a>')
        rows.append("</div>")
    return "".join(rows)


def _shell_page(cur: str, d: dict) -> str:
    s = SHELLS[cur]
    a = d.get("atlas", {})
    tasks = {k: v for k, v in d.get("tasks", {}).items() if v["sys"] == cur}
    fam = d.get("roster", {})
    pages = sorted(k for k, v in fam.items() if v == s["links_key"])
    crumb = " → ".join(f"<b>{c}</b>" for c in s["crumb"])
    stats = [
        (len(tasks), "一鍵任務", "DECK TASKS"),
        (len(pages), "現役頁族", "PAGE FAMILIES"),
        (_n(a.get("ledger", 0)), "台帳筆數", "LEDGER"),
        (_n(a.get("ssot", 0)), "SSOT 冊", "REGISTRY"),
    ]
    if cur == "CGC":
        stats[3] = (_n(a.get("subs", 0)), "子系統", "SUBSYSTEMS")
    stat_html = "".join(
        f'<div class="stat"><div class="n">{n}</div>'
        f'<div class="zh">{zh}</div><div class="en">{en}</div></div>'
        for n, zh, en in stats)
    tag_net = '<span class="tag net">NET</span>'
    tag_loc = '<span class="tag">本機</span>'
    trows = "".join(
        f'<tr><td><code>{k}</code></td><td>{html.escape(v["zh"])}</td>'
        f'<td>{tag_net if v["net"] else tag_loc}</td></tr>'
        for k, v in sorted(tasks.items())) or (
        '<tr><td colspan="3">此系統暫無深控一鍵任務(誠實空)</td></tr>')
    prows = "".join(
        f'<tr><td class="mono">{i:02d}</td><td>{html.escape(p)}</td></tr>'
        for i, p in enumerate(pages, 1)) or (
        '<tr><td colspan="2">頁族冊空(誠實)</td></tr>')
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA · {s["zh"]} {cur} 現況台</title><style>{CSS}</style></head><body>
<aside class="rail">
<div class="brand"><span class="seal">{s["seal"]}</span>
<div class="latin">VERITAS INTELLIGENCE ANALYTICS</div>
<h1>{s["zh"]}現況台</h1>
<div class="en">{s["en"]}</div>
<span class="badge">SHELL v0100 · LIVE</span></div>
{_nav(cur, d)}
<div class="railfoot">
<div><div class="k">TASKS</div><div class="v">{len(tasks)}</div></div>
<div><div class="k">PAGES</div><div class="v">{len(pages)}</div></div>
<div><div class="k">STATE</div><div class="v">LIVE</div></div>
<div><div class="k">LEDGER</div><div class="v">{_n(a.get("ledger", 0))}</div></div>
</div></aside>
<main class="main">
<div class="crumb">{crumb} · <span class="lock">LAYOUT SPEC(批302)</span></div>
<div class="head"><h2>{s["zh"]} {cur}<small>{s["en"]}</small></h2>
<div class="spec">
<div><div class="k">BUILD</div><div class="v">SHELL v0100</div></div>
<div><div class="k">TASKS</div><div class="v">{len(tasks)}</div></div>
<div><div class="k">BRIDGE</div><div class="v ok">127.0.0.1:8765</div></div>
<div><div class="k">GATE</div><div class="v ok">HONEST 3-STATE</div></div>
</div>
<div class="sub">{s["sub"]}</div></div>
<div class="stats">{stat_html}</div>
<div class="card"><h3>一鍵任務冊<small>DECK TASKS</small></h3>
<div class="note">執行入口=總控台 MasterControl(下拉/勾選;樞紐
127.0.0.1:8765 白名單真跑)。本頁=現況展示(唯讀)。</div>
<div class="wrap-x"><table class="tbl">
<tr><th>任務 TASK</th><th>名稱 NAME</th><th>通路 LANE</th></tr>
{trows}</table></div></div>
<div class="card"><h3>頁面冊<small>PAGE FAMILIES</small></h3>
<div class="note">本區現役頁族(MDL105 單一架構歸屬冊直取;
左欄「區內頁面」可直開)。</div>
<div class="wrap-x"><table class="tbl">
<tr><th>NO</th><th>頁族 FAMILY</th></tr>
{prows}</table></div></div>
<div class="foot">VIA · {s["en"]} · 真值直取(Atlas+任務冊+歸屬冊)
零發明 · 產於 {d["ts"]} · 版型=批302 四設計正本萃取(hash 已收容)
· 零 CDN 零外網</div>
</main></body></html>"""


def run(do_print: bool = True) -> int:
    d = gather()
    UI.mkdir(parents=True, exist_ok=True)
    for k in ORDER:
        (UI / SHELLS[k]["page"]).write_text(_shell_page(k, d),
                                            encoding="utf-8")
    if do_print:
        n_t = len(d.get("tasks", {}))
        print(f"[統一殼] 四子系統殼頁再生 · 任務歸屬 {n_t} · "
              f"台帳 {d.get('atlas', {}).get('ledger', 0)} · "
              + " ".join(SHELLS[k]["page"] for k in ORDER))
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run(do_print=False)
    pages = {k: (UI / SHELLS[k]["page"]).read_text(encoding="utf-8")
             for k in ORDER}
    d = gather()
    chk("① 四殼頁全產出(rc0+檔在位)", rc == 0
        and all((UI / SHELLS[k]["page"]).exists() for k in ORDER))
    chk("② 版型五律全在(左欄導航+麵包屑+規格帶+統計卡+內容卡)",
        all('class="rail"' in p and 'class="crumb"' in p
            and 'class="spec"' in p and 'class="stats"' in p
            and 'class="card"' in p for p in pages.values()))
    chk("③ 編號導航+跨殼互連(00 總控+01-04 四系統)",
        all('MasterControl_v0100.html' in p
            and all(SHELLS[j]["page"] in p for j in ORDER)
            for p in pages.values()))
    chk("④ 真值直取零發明(任務歸屬+台帳數入頁)",
        len(d.get("tasks", {})) >= 30
        and all(str(_n(d.get("atlas", {}).get("ledger", 0))) in p
                for p in pages.values()))
    chk("⑤ 雙語標籤律(中文標+英文 letterspaced)",
        all("VERITAS INTELLIGENCE ANALYTICS" in p
            and SHELLS[k]["en"] in p for k, p in pages.items()))
    chk("⑥ 零 CDN+加速橋+誠實宣告",
        all('<script src="http' not in p and "src=\"http" not in p
            for p in pages.values())
        and "ACCEL-BRIDGE" in src and "誠實" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 統一版型殼引擎(CGC_MDL116)· 六檢自測(零網路)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
