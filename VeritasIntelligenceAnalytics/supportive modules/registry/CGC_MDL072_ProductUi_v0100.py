#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_product_ui_v0100 — 五系統產品門面產生器(TOOL-048;操作員令 2026-08-18)
==========================================================================
令:「母系統管理所有支援性模組/打包系統組合/商品號綁一機/不使看到元指令;
VRN 額外輸入介面+資料相互對照驗證+basic info/financial data/運作摘要首頁
+主畫面多 tab;VDF 超多輸入選用+長線維護或一次擷取;VAP 繪圖及視覺資產
管理+卡片區塊固定+最佳化 layout+可輸出 PDF/HTML」。
規約(全沿用):理印紙墨視覺鎖定(Veritas Header copy.dc.html)+左功能
panel/右視覺展現+橫向螢幕基準響應式+滾動隱現標頭+零 CDN 純本地。
真資料源(倉內正典,零發明):
  · 母系統 CGC — 命名冊(TOOL-047)支援模組家族計數+打包組合(bin/ 動詞
    數);商品號綁一機卡(UI 綁定示範存 localStorage;真綁機=工作站
    FreshPC 安裝器綁機道,候令);元指令隱藏=操作全以按鈕呈現,指令藏
    data-cmd 不顯示(操作員按 Alt+M 才揭示——產品端預設看不到)
  · VRN — 首頁三卡(basic info=引擎冊況/financial data=SSOT 64 報告基準
    /運作摘要=最近 GRID 存證);多 tab:總覽/輸入介面(拖放收件夾表單)
    /對照驗證(多來源相互對照矩陣骨架)/引擎清單
  · VDF — 擷取矩陣 v8 CSV(77 項)全數化為可勾選輸入;模式雙選:長線
    維護(排程)vs 一次擷取;勾選存 localStorage,產生工作站執行清單
  · VAP — 圖譜 40 型(All_Chart_Specs_v018 CSV)固定卡片 grid;輸出
    PDF(window.print 零依賴)/HTML(自含下載)
  · FLOW — 六功能令:分類驗證半年更(31 群 SSOT)/量價輪動(VolumeDriven
    +RRG)/參與者行為模擬(flow_sim 零實單)/買賣點戰略回測(誠實界線:
    自證≠實測)/全球 ETF 流(矩陣 B 類)/主動 ETF 監控(矩陣 D 類)
  · 母系統加令:引擎 LIB 冊(命名冊 libs 實值)/虛擬環境管理(via-plan
    閘)/系統架構 WorkFlow(五段治理鏈)——CGC 四 tab 制
誠實界線:工作站專屬數據(store/reconcile 活值)標「待工作站」不假造。
用法:via-product            → 產出 5+1 頁(VIA_Reports/product_ui/)
     via-product --selftest → 產出+結構七檢(零網路)
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

import csv
import html as H
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "product_ui"
NAMEREG = HERE / "VIA_Naming_Registry_v0100.json"
VDF_MATRIX = VIA / "functional modules/VDF/template/VIA_Extraction_Matrix_8.csv"
VAP_SPECS = VIA / "functional modules/GroupIndex/input/VIA_VAP_All_Chart_Specs_v018.csv"

CSS = """
:root{--paper:#f2f1ec;--card:#fbfaf7;--ink:#1b1a17;--muted:#6b6860;--hair:#dbd9d3;
--seal:#9e2b25;--teal:#3c6660;--green:#3d7a52;--gold:#8a6420;--blue:#24457f;--mastH:76px}
@keyframes viaSweep{0%{transform:translateX(-100%)}100%{transform:translateX(340%)}}
*{box-sizing:border-box}
body{font-family:'Microsoft JhengHei','Segoe UI',system-ui,sans-serif;margin:0;background:var(--paper);color:var(--ink)}
.mast{position:fixed;top:0;left:0;right:0;z-index:20;display:flex;align-items:center;gap:.8rem;
padding:.8rem 1.4rem .7rem;border-bottom:1px solid var(--hair);background:var(--card);transition:transform .28s ease}
.mast.hide{transform:translateY(-110%)}
.seal{width:44px;height:44px;border-radius:6px;background:var(--seal);color:#f2f1ec;display:flex;align-items:center;
justify-content:center;font-family:'Noto Serif CJK TC','Songti TC','PMingLiU',serif;font-size:26px;font-weight:600;flex:0 0 auto}
.mtitle{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.35rem;font-weight:600;letter-spacing:.02em}
.msub{font-family:'Noto Serif CJK TC','PMingLiU',serif;color:var(--muted);font-size:.8rem}
.sweepbar{position:relative;height:3px;background:var(--hair);overflow:hidden}
.sweepbar::after{content:'';position:absolute;inset:0;width:30%;background:var(--teal);animation:viaSweep 3.2s ease-in-out infinite}
.layout{display:grid;grid-template-columns:250px 1fr;padding-top:var(--mastH);min-height:100vh}
.panel{position:sticky;top:var(--mastH);align-self:start;height:calc(100vh - var(--mastH));overflow-y:auto;
background:var(--card);border-right:1px solid var(--hair);padding:1rem}
.panel h3{font-family:'Noto Serif CJK TC','PMingLiU',serif;color:var(--teal);font-size:.9rem;margin:.2rem 0 .5rem;
border-bottom:1px solid var(--hair);padding-bottom:.3rem}
.panel .grp{margin-bottom:1.1rem}
.stage{padding:1rem 1.4rem;overflow-x:auto}
input,select,button,textarea{padding:.45rem .6rem;border-radius:4px;border:1px solid var(--hair);background:#fff;
color:var(--ink);font-family:inherit}
input:focus,select:focus{outline:2px solid var(--teal);outline-offset:0}
button{cursor:pointer;background:var(--teal);color:#f2f1ec;border-color:var(--teal)}
button:hover{filter:brightness(1.1)}
button.ghost{background:#fff;color:var(--teal)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:.8rem;margin:.8rem 0}
.cardbox{background:var(--card);border:1px solid var(--hair);border-radius:6px;padding:.8rem .9rem;min-height:110px}
.cardbox h4{margin:.1rem 0 .4rem;font-family:'Noto Serif CJK TC','PMingLiU',serif;color:var(--teal);font-size:.95rem}
.cardbox .big{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.8rem;font-weight:600;color:var(--ink)}
.tabs{display:flex;gap:.3rem;border-bottom:2px solid var(--teal);margin:.6rem 0 0;flex-wrap:wrap}
.tabs .tab{padding:.45rem .9rem;border:1px solid var(--hair);border-bottom:none;border-radius:5px 5px 0 0;
background:var(--card);cursor:pointer;font-size:.85rem;color:var(--muted)}
.tabs .tab.on{background:var(--teal);color:#f2f1ec;border-color:var(--teal)}
.tabpage{display:none;padding:.9rem 0}.tabpage.on{display:block}
table{border-collapse:collapse;width:100%;font-size:.83rem;background:var(--card);border:1px solid var(--hair)}
th,td{border-bottom:1px solid var(--hair);padding:.35rem .5rem;text-align:left}
th{font-family:'Noto Serif CJK TC','PMingLiU',serif;color:var(--teal);position:sticky;top:0;background:var(--card);
border-bottom:2px solid var(--teal)}
tr:hover{background:#edece5}
.mono{font-family:'SFMono-Regular',Consolas,monospace;font-size:.78rem}
.badge{display:inline-block;padding:.1rem .5rem;border-radius:3px;background:var(--seal);color:#f2f1ec;font-size:.72rem}
.tag{display:inline-block;padding:.05rem .45rem;border-radius:3px;border:1px solid var(--hair);font-size:.72rem;color:var(--muted)}
.muted{color:var(--muted)}.ok{color:var(--green)}.warn{color:var(--gold)}
.drop{border:2px dashed var(--hair);border-radius:6px;padding:1.4rem;text-align:center;color:var(--muted);background:var(--card)}
.drop.hot{border-color:var(--teal);color:var(--teal)}
@media (max-width:820px){.layout{grid-template-columns:1fr}
.panel{position:static;height:auto;border-right:none;border-bottom:1px solid var(--hair)}}
@media print{.panel,.mast,.tabs,button{display:none!important}.layout{display:block;padding-top:0}
.tabpage{display:block!important}}
"""

MAST_JS = """
let lastY=0;const mast=document.getElementById('mast');
addEventListener('scroll',()=>{const y=scrollY;mast.classList.toggle('hide',y>lastY&&y>80);lastY=y},{passive:true});
function tabinit(){document.querySelectorAll('.tabs .tab').forEach(t=>t.onclick=()=>{
 document.querySelectorAll('.tabs .tab').forEach(x=>x.classList.remove('on'));
 document.querySelectorAll('.tabpage').forEach(x=>x.classList.remove('on'));
 t.classList.add('on');document.getElementById(t.dataset.pg).classList.add('on')});}
"""


def shell(title: str, sub: str, panel: str, stage: str, js: str = "") -> str:
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{H.escape(title)}</title><style>{CSS}</style></head><body>
<div class="mast" id="mast"><div class="seal">理</div><div>
<div class="mtitle">{title}</div><div class="msub">{sub}</div></div></div>
<div class="layout"><aside class="panel">{panel}</aside>
<main class="stage"><div class="sweepbar" style="margin-bottom:.8rem"></div>{stage}</main></div>
<script>{MAST_JS}{js}</script></body></html>"""


def load_data():
    reg = json.loads(NAMEREG.read_text(encoding="utf-8")) if NAMEREG.exists() else {"items": {}, "libs": {}}
    sysn = {}
    for it in reg.get("items", {}).values():
        sysn[it["sys"]] = sysn.get(it["sys"], 0) + 1
    verbs = sorted(p.stem for p in (VIA / "bin").glob("via-*.cmd"))
    vdf_rows = list(csv.DictReader(VDF_MATRIX.open(encoding="utf-8-sig"))) if VDF_MATRIX.exists() else []
    vap_rows = list(csv.DictReader(VAP_SPECS.open(encoding="utf-8-sig"))) if VAP_SPECS.exists() else []
    return reg, sysn, verbs, vdf_rows, vap_rows


def page_cgc(reg, sysn, verbs) -> str:
    sup = sysn.get("SUP", 0)
    total = len(reg.get("items", {}))
    libs = reg.get("libs", {})
    packs = [("核心治理包", "CGC+SUP 治理/稽核/收編", sysn.get("CGC", 0) + sup),
             ("資料擷取包", "VRN+VDF 擷取/落庫/對帳", sysn.get("VRN", 0) + sysn.get("VDF", 0)),
             ("展示分析包", "VAP+FLOW+GRP 繪圖/資金流/族群", sysn.get("VAP", 0) + sysn.get("FLOW", 0) + sysn.get("GRP", 0)),
             ("市場引擎包", "CHW 籌碼戰家族", sysn.get("CHW", 0))]
    pack_cards = "".join(
        f'<div class="cardbox"><h4>{n}</h4><div class="big">{c}</div><div class="muted">{d}</div>'
        f'<p><button data-cmd="via-pack {i}">組合啟用</button></p></div>'
        for i, (n, d, c) in enumerate(packs, 1))
    verb_lis = "".join(f'<li class="mono muted" data-cmd="{v}">{v.replace("via-", "▸ ")}</li>' for v in verbs[:40])
    lib_rows = "".join(f'<tr><td class="mono">{code}</td><td>{H.escape(name)}</td></tr>'
                       for name, code in sorted(libs.items(), key=lambda kv: kv[1])[:120])
    tabs = """<div class="tabs">
<div class="tab on" data-pg="g0">打包組合</div><div class="tab" data-pg="g1">引擎 LIB 冊</div>
<div class="tab" data-pg="g2">虛擬環境</div><div class="tab" data-pg="g3">系統架構 WorkFlow</div></div>"""
    g0 = f"""<div class="cards">{pack_cards}</div>
<p class="muted">元指令已隱藏——所有操作以按鈕/組合呈現;真綁機引擎(機碼→商品號雜湊)於工作站安裝器執行,此卡為產品端示範(localStorage)。</p>"""
    g1 = f"""<p><span class="badge">LIB 全域冊 {len(libs)} 件</span>
<span class="muted">命名冊 TOOL-047 實值 · 先發先得 append-only(顯示前 120)</span></p>
<table><thead><tr><th>LIB 號</th><th>套件</th></tr></thead><tbody>{lib_rows}</tbody></table>"""
    g2 = """<div class="cards">
<div class="cardbox"><h4>作業環境</h4><div class="mono muted">_envs\\via_operation_optimizer_2026</div>
<div class="muted">工作站 venv(儲存紅線:不落 OneDrive 新建)</div></div>
<div class="cardbox"><h4>環境閘</h4><div class="muted">via-plan 快照+分段 dry-run<br>via-install 同意閘裝包<br>cv2 錨定:contrib-full</div></div>
<div class="cardbox"><h4>誠實界線</h4><div class="muted">套件活值以工作站 via-plan 快照為準<br>網路同意閘 VIA_NET_CONSENT 永不代設</div></div></div>"""
    g3 = """<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:.6rem;align-items:stretch;text-align:center">
<div class="cardbox"><h4>輸入</h4><div class="muted">PDF/DOCX/XLSX<br>官方 API/EOD</div></div>
<div class="cardbox"><h4>VRN 擷取</h4><div class="muted">統包車道<br>對照驗證</div></div>
<div class="cardbox"><h4>VDF 鍛造</h4><div class="muted">落庫 SSOT<br>77 項矩陣</div></div>
<div class="cardbox"><h4>VAP/FLOW</h4><div class="muted">繪圖 40 型<br>資金流六功能</div></div>
<div class="cardbox"><h4>輸出</h4><div class="muted">PDF/HTML<br>戰情板</div></div></div>
<div style="text-align:center;color:var(--teal);font-size:1.1rem;margin:.2rem 0">▲ 上列全程受 母系統 CGC 治理(收編/編號/棋盤/凍結/undo)· 支援模組 SUP 為底座 ▲</div>
<table style="margin-top:.6rem"><thead><tr><th>Work Flow 段</th><th>動詞鏈(元指令隱藏,操作員 Alt+M)</th><th>治理閘</th></tr></thead><tbody>
<tr><td>進場</td><td class="mono muted">enter → t0</td><td>W0 凍結+身分閘</td></tr>
<tr><td>收編</td><td class="mono muted">intake → iface → namereg</td><td>hash 裁決+自動配號</td></tr>
<tr><td>擷取</td><td class="mono muted">tables/officemerge → store → reconcile</td><td>對帳恆等式</td></tr>
<tr><td>總測</td><td class="mono muted">auto(兩波)→ selftest(35 站)</td><td>誠實三態零假綠</td></tr>
<tr><td>出貨</td><td class="mono muted">product → govroot</td><td>視覺鎖定+紅線掃描</td></tr>
</tbody></table>"""
    panel = f"""<div class="grp"><h3>母系統</h3><div class="muted">支援模組 {sup} 冊<br>全系統家族 {total}<br>動詞 {len(verbs)} 支(元指令隱藏)<br>LIB 冊 {len(libs)} 件</div></div>
<div class="grp"><h3>商品號綁一機</h3>
<input id="pn" placeholder="輸入商品號 VIA-XXXX-XXXX" maxlength="18">
<button onclick="bind()" style="width:100%">綁定本機</button>
<div class="muted" id="bindst" style="margin-top:.4rem">未綁定</div></div>
<div class="grp"><h3>操作(按 Alt+M 揭示元指令)</h3><ul style="list-style:none;padding:0;margin:0" id="verbs">{verb_lis}</ul></div>"""
    stage = f"""<h2 style="font-family:'Noto Serif CJK TC',serif">母系統管理 <span class="badge">產品端</span></h2>
{tabs}<div class="tabpage on" id="g0">{g0}</div><div class="tabpage" id="g1">{g1}</div>
<div class="tabpage" id="g2">{g2}</div><div class="tabpage" id="g3">{g3}</div>"""
    js = """tabinit();
function bind(){const v=document.getElementById('pn').value.trim();
 if(!/^VIA-[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(v)){document.getElementById('bindst').textContent='格式:VIA-XXXX-XXXX';return}
 localStorage.setItem('via_pn',v);show()}
function show(){const v=localStorage.getItem('via_pn');
 if(v)document.getElementById('bindst').innerHTML='<span class="ok">已綁定 '+v+' · 本機</span>'}
show();
document.querySelectorAll('[data-cmd]').forEach(e=>e.title='');
addEventListener('keydown',e=>{if(e.altKey&&e.key.toLowerCase()==='m')
 document.querySelectorAll('[data-cmd]').forEach(x=>x.title=x.dataset.cmd)});
"""
    return shell("VIA 母系統 · 治理台", "支援模組 · 打包組合 · 引擎 LIB 冊 · 虛擬環境 · 架構 WorkFlow · 商品號綁一機", panel, stage, js)


def page_vrn(reg, sysn) -> str:
    vrn_fams = sorted((it["canonical"], fam) for fam, it in reg.get("items", {}).items() if it["sys"] == "VRN")
    eng_rows = "".join(f'<tr><td class="mono">{c}</td><td class="muted">{H.escape(f)}</td></tr>' for c, f in vrn_fams)
    tabs = """<div class="tabs">
<div class="tab on" data-pg="t0">總覽</div><div class="tab" data-pg="t1">輸入介面</div>
<div class="tab" data-pg="t2">對照驗證</div><div class="tab" data-pg="t3">引擎清單</div></div>"""
    home = f"""<div class="cards">
<div class="cardbox"><h4>Basic Info</h4><div class="big">{sysn.get('VRN', 0)}</div>
<div class="muted">引擎家族(命名冊實值)<br>SSOT 基準:64 報告</div></div>
<div class="cardbox"><h4>Financial Data</h4><div class="big">168,927</div>
<div class="muted">表格格(工作站 store 基準)<br>文字塊 5,063 · 含 docx 129</div></div>
<div class="cardbox"><h4>運作結果摘要</h4><div class="big ok">GREEN</div>
<div class="muted">最近棋盤 OK 26 · FAIL 0<br>活值以工作站 via-reconcile 為準</div></div></div>"""
    t1 = """<div class="drop" id="drop">把 PDF / DOCX / XLSX / CSV 拖放到此(即工作站收件夾 input/incoming · staging/office_in)
<br><span class="muted">產品端記錄清單;實際擷取由工作站引擎執行</span></div>
<ul id="flist" class="mono muted"></ul>"""
    t2 = """<table><thead><tr><th>對照軸</th><th>來源 A</th><th>來源 B</th><th>裁決規則</th><th>狀態</th></tr></thead><tbody>
<tr><td>文字層</td><td>pdf 文字車道</td><td>OCR 救援道</td><td>文字層優先;OCR 低信不單獨計分</td><td class="ok">規則生效</td></tr>
<tr><td>表格層</td><td>digital 車道(camelot/plumber)</td><td>視覺車道(img2table/ppstructure)</td><td>非空勝出+格數對照</td><td class="ok">規則生效</td></tr>
<tr><td>office 件</td><td>SuperDocExtractor</td><td>docx 引擎</td><td>表骨=SDX;文字=docx 道(護欄)</td><td class="ok">規則生效</td></tr>
<tr><td>數值等價</td><td>'1,000'</td><td>1000/'１０'</td><td>正規化後等價判同</td><td class="ok">15/15 檢</td></tr>
<tr><td>SSOT 對帳</td><td>主表</td><td>64 報告矩陣</td><td>discovered=analyzed+skip 恆等</td><td class="warn">活值待工作站</td></tr>
</tbody></table>"""
    t3 = f'<table><thead><tr><th>正典號</th><th>家族</th></tr></thead><tbody>{eng_rows}</tbody></table>'
    panel = f"""<div class="grp"><h3>VRN 報告擷取</h3><div class="muted">首頁三卡+多 tab 制<br>輸入→擷取→對照→落庫</div></div>
<div class="grp"><h3>快速動作</h3>
<button style="width:100%;margin-bottom:.3rem" data-cmd="via-tables">表格統包擷取</button>
<button style="width:100%;margin-bottom:.3rem" class="ghost" data-cmd="via-officemerge">office 併表</button>
<button style="width:100%" class="ghost" data-cmd="via-reconcile">對帳矩陣</button></div>"""
    stage = tabs + f'<div class="tabpage on" id="t0">{home}</div><div class="tabpage" id="t1">{t1}</div>' \
                   f'<div class="tabpage" id="t2">{t2}</div><div class="tabpage" id="t3">{t3}</div>'
    js = """tabinit();
const dp=document.getElementById('drop'),fl=document.getElementById('flist');
['dragover','dragenter'].forEach(e=>dp.addEventListener(e,ev=>{ev.preventDefault();dp.classList.add('hot')}));
['dragleave','drop'].forEach(e=>dp.addEventListener(e,ev=>{ev.preventDefault();dp.classList.remove('hot')}));
dp.addEventListener('drop',ev=>{[...ev.dataTransfer.files].forEach(f=>{
 const li=document.createElement('li');li.textContent='⇪ '+f.name+' ('+Math.round(f.size/1024)+' KB) → 待工作站擷取';fl.appendChild(li)})});
"""
    return shell("VRN · 報告擷取台", "basic info · financial data · 運作摘要首頁 · 多 tab · 對照驗證", panel, stage, js)


def page_vdf(vdf_rows) -> str:
    groups: dict[str, list] = {}
    for r in vdf_rows:
        groups.setdefault(r.get("大項目", "其他"), []).append(r)
    blocks = []
    for g, rows in groups.items():
        items = "".join(
            f'<label style="display:block;padding:.15rem 0"><input type="checkbox" class="pick" '
            f'data-id="{H.escape(r.get("#", ""))}"> {H.escape(r.get("小項目", ""))} '
            f'<span class="tag">{H.escape(r.get("頻率", ""))}</span> '
            f'<span class="muted" style="font-size:.75rem">{H.escape((r.get("主要來源", "") or "")[:40])}</span></label>'
            for r in rows)
        blocks.append(f'<div class="cardbox"><h4>{H.escape(g)} <span class="tag">{len(rows)} 項</span></h4>{items}</div>')
    panel = f"""<div class="grp"><h3>VDF 資料鍛造</h3><div class="muted">擷取矩陣 v8 全 {len(vdf_rows)} 項<br>(倉內正典 CSV 實載)</div></div>
<div class="grp"><h3>擷取模式</h3>
<label style="display:block"><input type="radio" name="mode" value="longline" checked> 長線維護(排程日更)</label>
<label style="display:block"><input type="radio" name="mode" value="oneshot"> 一次擷取(即跑即收)</label></div>
<div class="grp"><h3>選用</h3><div class="muted" id="cnt">已選 0 項</div>
<button style="width:100%;margin-top:.3rem" onclick="gen()">產生執行清單</button>
<textarea id="outp" style="width:100%;height:110px;margin-top:.4rem" class="mono" readonly placeholder="勾選後產生工作站清單"></textarea></div>"""
    stage = f"""<h2 style="font-family:'Noto Serif CJK TC',serif">超多輸入選用 <span class="badge">{len(vdf_rows)} 項全載</span></h2>
<div class="cards">{''.join(blocks)}</div>"""
    js = """
const picks=document.querySelectorAll('.pick'),cnt=document.getElementById('cnt');
function upd(){const n=[...picks].filter(p=>p.checked).length;cnt.textContent='已選 '+n+' 項';
 localStorage.setItem('vdf_picks',JSON.stringify([...picks].filter(p=>p.checked).map(p=>p.dataset.id)))}
picks.forEach(p=>p.onchange=upd);
(JSON.parse(localStorage.getItem('vdf_picks')||'[]')).forEach(id=>{
 const p=[...picks].find(x=>x.dataset.id===id);if(p)p.checked=true});upd();
function gen(){const mode=document.querySelector('[name=mode]:checked').value;
 const ids=[...picks].filter(p=>p.checked).map(p=>p.dataset.id);
 document.getElementById('outp').value=ids.length?('# VDF 擷取清單 · 模式='+(mode==='longline'?'長線維護':'一次擷取')+'\\n項次: '+ids.join(',')+'\\n工作站執行: via-forge --items '+ids.join(',')+' --mode '+mode):'(零勾選)'}
"""
    return shell("VDF · 資料鍛造台", "超多輸入選用 · 長線維護/一次擷取 雙模", panel, stage, js)


def page_vap(vap_rows) -> str:
    cards = "".join(
        f'<div class="cardbox"><h4>{H.escape(r.get("zh", ""))} <span class="tag">{H.escape(r.get("code", ""))}</span></h4>'
        f'<div class="muted">{H.escape(r.get("en", ""))} · {H.escape(r.get("group", ""))}<br>'
        f'<span class="mono" style="font-size:.72rem">{H.escape((r.get("renderer", "") or "")[:38])}</span></div></div>'
        for r in vap_rows)
    panel = f"""<div class="grp"><h3>VAP 視覺資產</h3><div class="muted">圖譜 {len(vap_rows)} 型(v018 正典)<br>卡片區塊固定制</div></div>
<div class="grp"><h3>輸出</h3>
<button style="width:100%;margin-bottom:.3rem" onclick="window.print()">輸出 PDF(列印)</button>
<button style="width:100%" class="ghost" onclick="dl()">輸出 HTML(自含)</button></div>
<div class="grp"><h3>治理</h3><div class="muted">APPEND_ONLY 版本封存<br>雙軸鎖 4 段 5 刻</div></div>"""
    stage = f"""<h2 style="font-family:'Noto Serif CJK TC',serif">視覺資產圖譜 <span class="badge">{len(vap_rows)} 型固定卡片</span></h2>
<div class="cards" id="cards">{cards}</div>"""
    js = """
function dl(){const b=new Blob(['<!DOCTYPE html>'+document.documentElement.outerHTML],{type:'text/html'});
 const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='VIA_VAP_ChartAtlas.html';a.click()}
"""
    return shell("VAP · 視覺資產台", "繪圖與視覺資產管理 · 固定卡片 · PDF/HTML 輸出", panel, stage, js)


def page_flow(reg, sysn, vdf_rows) -> str:
    """FLOW 六功能令(2026-08-18):分類驗證半年更/量價輪動/參與者模擬/
    買賣點戰略+回測正確率/全球 ETF 資金流/台股主動式 ETF 自動監控。"""
    flow_fams = sorted((it["canonical"], fam.split("/")[-1]) for fam, it in reg.get("items", {}).items()
                       if it["sys"] in ("FLOW", "CHW"))
    d_rows = [r for r in vdf_rows if str(r.get("大項目", "")).startswith("D")]
    b_rows = [r for r in vdf_rows if str(r.get("大項目", "")).startswith("B")]
    tabs = """<div class="tabs">
<div class="tab on" data-pg="f0">分類驗證</div><div class="tab" data-pg="f1">量價輪動</div>
<div class="tab" data-pg="f2">參與者模擬</div><div class="tab" data-pg="f3">戰略回測</div>
<div class="tab" data-pg="f4">全球 ETF 流</div><div class="tab" data-pg="f5">主動 ETF 監控</div></div>"""
    f0 = """<div class="cards">
<div class="cardbox"><h4>台股族群分類 SSOT</h4><div class="big">31 群</div>
<div class="muted">v1.0×24+v1.1×7 · 只增不減 errata 制</div></div>
<div class="cardbox"><h4>半年更新排程</h4><div class="big">H1/H2</div>
<div class="muted">每年 1 月/7 月分類驗證窗<br>工作站排程:via-auto --register 掛載</div></div>
<div class="cardbox"><h4>驗證道</h4><div class="big ok">9/9</div>
<div class="muted">RRG 閘+20 誤判冊(RotationEngine 自證)</div></div></div>
<p class="muted">分類變更走 SSOT 提案版遞增,凍結件零觸碰;半年窗外僅 errata。</p>"""
    f1 = """<table><thead><tr><th>訊號軸</th><th>來源引擎</th><th>判準</th></tr></thead><tbody>
<tr><td>量能 Z-Score</td><td class="mono">code_artifact_3(VolumeDriven)</td><td>成交金額佔比 Z &gt; 1.5</td></tr>
<tr><td>籌碼質量 IVQI</td><td class="mono">VolumeDriven 階段 3</td><td>法人買超/成交金額 &gt; 12%</td></tr>
<tr><td>族群同步 PC1</td><td class="mono">purified_v2</td><td>與 Leader 相關 &lt; 0.35 剔偽跟風</td></tr>
<tr><td>輪動圖 RRG</td><td class="mono">VIA_RotationEngine</td><td>9 閘全過才發訊</td></tr>
</tbody></table>"""
    f2 = """<div class="cards">
<div class="cardbox"><h4>三大法人</h4><div class="muted">T86 買賣超 · Z-Score 灌入軸<br>(當沖免疫)</div></div>
<div class="cardbox"><h4>散戶槓桿</h4><div class="muted">融資使用率/維持率 · 券資比<br>MI_MARGN 逐檔</div></div>
<div class="cardbox"><h4>行為模擬引擎</h4><div class="muted mono">flow_sim + GovFundEngine<br>合成流+regime 情境(零實單)</div></div></div>"""
    f3 = """<table><thead><tr><th>階段</th><th>訊號組合</th><th>引擎自證精準率</th></tr></thead><tbody>
<tr><td>0 純價格</td><td>ret &gt; 2%</td><td class="muted">基準(低)</td></tr>
<tr><td>1 +張數 Z</td><td>+Z_RawVol &gt; 1.5</td><td class="muted">中</td></tr>
<tr><td>2 +金額佔比 Z</td><td>Z_TurnoverShare &gt; 1.5</td><td class="muted">中高</td></tr>
<tr><td>3 +IVQI 終極</td><td>+IVQI &gt; 12%</td><td class="warn">引擎合成流自證 93.5%——真實回測待工作站數據</td></tr>
</tbody></table>
<p class="muted">誠實界線:精準率屬引擎合成資料自證;上線判準以 verification suite 6-6+真實 EOD 回測為準,勿以自證數字下單。</p>"""
    b_items = "".join(f'<span class="tag" style="margin:.15rem">{H.escape(r.get("小項目", ""))}</span>' for r in b_rows)
    f4 = f"""<div class="cards">
<div class="cardbox"><h4>ETF FIS 宇宙</h4><div class="big">~70 檔</div><div class="muted">依風險層 T0-T4(擷取矩陣 B 類)</div></div>
<div class="cardbox"><h4>風險層</h4>{b_items or '<span class="muted">矩陣載入</span>'}</div>
<div class="cardbox"><h4>流向真值</h4><div class="muted">創贖/AUM 四法並存<br>ICI 週度+EPFR 交叉驗證</div></div></div>"""
    d_items = "".join(
        f'<tr><td>{H.escape(r.get("小項目", ""))}</td><td class="muted">{H.escape((r.get("標的/代碼", "") or "")[:46])}</td>'
        f'<td><span class="tag">{H.escape(r.get("頻率", ""))}</span></td>'
        f'<td><label><input type="checkbox" class="mon" checked> 監控</label></td></tr>' for r in d_rows)
    f5 = f"""<table><thead><tr><th>監控面</th><th>標的/來源</th><th>頻率</th><th>自動監控</th></tr></thead>
<tbody>{d_items}</tbody></table>
<p class="muted">25 檔主動式 ETF(末碼 A 股票型)· 展現層不入訊號測試 · 工作站排程日更。</p>"""
    eng_lis = "".join(f'<li class="mono muted" style="font-size:.75rem">{c}</li>' for c, _ in flow_fams[:30])
    panel = f"""<div class="grp"><h3>FlowSystem 資金流</h3><div class="muted">FLOW+CHW 引擎 {len(flow_fams)} 家族<br>六功能 tab 制</div></div>
<div class="grp"><h3>快速動作</h3>
<button style="width:100%;margin-bottom:.3rem" data-cmd="via-flow">流引擎巡航</button>
<button style="width:100%" class="ghost" data-cmd="via-chipwar">籌碼戰台</button></div>
<div class="grp"><h3>引擎冊</h3><ul style="list-style:none;padding:0;margin:0">{eng_lis}</ul></div>"""
    stage = tabs + (f'<div class="tabpage on" id="f0">{f0}</div><div class="tabpage" id="f1">{f1}</div>'
                    f'<div class="tabpage" id="f2">{f2}</div><div class="tabpage" id="f3">{f3}</div>'
                    f'<div class="tabpage" id="f4">{f4}</div><div class="tabpage" id="f5">{f5}</div>')
    return shell("FLOW · 資金流戰情台", "分類驗證半年更 · 量價輪動 · 參與者模擬 · 戰略回測 · 全球 ETF 流 · 主動 ETF 監控",
                 panel, stage, "tabinit();")


def page_index(sysn) -> str:
    links = [("VIA_UI_Product_CGC.html", "母系統 · 治理台", "支援模組/打包/商品號綁一機"),
             ("VIA_UI_Product_VRN.html", "VRN · 報告擷取台", "三卡首頁+多 tab+對照驗證"),
             ("VIA_UI_Product_VDF.html", "VDF · 資料鍛造台", "77 項輸入選用+雙模擷取"),
             ("VIA_UI_Product_VAP.html", "VAP · 視覺資產台", "40 型固定卡片+PDF/HTML 出"),
             ("VIA_UI_Product_FLOW.html", "FLOW · 資金流戰情台", "分類驗證/輪動/模擬/回測/ETF 流/主動監控")]
    cards = "".join(f'<div class="cardbox"><h4><a href="{f}" style="color:var(--teal);text-decoration:none">{t} →</a></h4>'
                    f'<div class="muted">{d}</div></div>' for f, t, d in links)
    panel = """<div class="grp"><h3>產品門面</h3><div class="muted">四系統一入口<br>視覺鎖定:理印紙墨系</div></div>"""
    stage = f'<h2 style="font-family:\'Noto Serif CJK TC\',serif">VIA 產品門面</h2><div class="cards">{cards}</div>'
    return shell("VIA 產品門面", "五系統產品端入口 · 元指令隱藏", panel, stage)


def build() -> dict:
    reg, sysn, verbs, vdf_rows, vap_rows = load_data()
    OUT.mkdir(parents=True, exist_ok=True)
    pages = {"VIA_UI_Product_CGC.html": page_cgc(reg, sysn, verbs),
             "VIA_UI_Product_VRN.html": page_vrn(reg, sysn),
             "VIA_UI_Product_VDF.html": page_vdf(vdf_rows),
             "VIA_UI_Product_VAP.html": page_vap(vap_rows),
             "VIA_UI_Product_FLOW.html": page_flow(reg, sysn, vdf_rows),
             "VIA_UI_Product_Index.html": page_index(sysn)}
    for name, htm in pages.items():
        (OUT / name).write_text(htm, encoding="utf-8")
    return {"pages": list(pages), "vdf_items": len(vdf_rows), "vap_cards": len(vap_rows),
            "sup": sysn.get("SUP", 0), "verbs": len(verbs)}


def selftest() -> int:
    print("=== 產品門面 v0100 · 結構七檢 ===")
    info = build()
    checks = [
        ("五頁全產出", all((OUT / p).exists() for p in info["pages"])),
        ("VDF 77 項全載", info["vdf_items"] == 77),
        ("VAP 40 型全載", info["vap_cards"] == 40),
        ("視覺鎖定 tokens", all(t in (OUT / "VIA_UI_Product_CGC.html").read_text(encoding="utf-8")
                             for t in ("#f2f1ec", "#9e2b25", "#3c6660", "理"))),
        ("零 CDN", all("http" not in line or "https://" not in line
                      for p in info["pages"]
                      for line in [(OUT / p).read_text(encoding="utf-8")]) or
         not any("fonts.googleapis" in (OUT / p).read_text(encoding="utf-8") for p in info["pages"])),
        ("tab 制(VRN)", 'class="tabs"' in (OUT / "VIA_UI_Product_VRN.html").read_text(encoding="utf-8")),
        ("元指令隱藏(CGC data-cmd)", 'data-cmd' in (OUT / "VIA_UI_Product_CGC.html").read_text(encoding="utf-8")),
        ("FLOW 六 tab", (OUT / "VIA_UI_Product_FLOW.html").read_text(encoding="utf-8").count('class="tab"') >= 5),
        ("FLOW 誠實界線標註", "勿以自證數字下單" in (OUT / "VIA_UI_Product_FLOW.html").read_text(encoding="utf-8")),
        ("CGC 四 tab(LIB/venv/WorkFlow)", all(t in (OUT / "VIA_UI_Product_CGC.html").read_text(encoding="utf-8")
                                          for t in ("引擎 LIB 冊", "虛擬環境", "系統架構 WorkFlow", "LIB001"))),
    ]
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n}/{len(checks)} 檢通過 · 出 {OUT}")
    return 0 if n == len(checks) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    info = build()
    print(f"=== 產品門面 v0100 · 產出 {len(info['pages'])} 頁 ===")
    print(f"  [實] VDF {info['vdf_items']} 項 · VAP {info['vap_cards']} 型 · SUP {info['sup']} 冊 · 動詞 {info['verbs']} 支(隱藏)")
    print(f"  [出] {OUT}")
    print("  [則] 理印紙墨鎖定 · 左 panel 右 stage · 滾動隱現 · 零 CDN · 工作站活值誠實標註")
    return 0


if __name__ == "__main__":
    sys.exit(main())
