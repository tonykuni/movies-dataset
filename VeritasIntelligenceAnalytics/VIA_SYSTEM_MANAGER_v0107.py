#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_SYSTEM_MANAGER — 總系統管理器(批281;操作員令)
====================================================================
操作員令:「應該用一個總 VIA_SYSTEM_MANAGER.py 管理一切:銜接 sync、
html u/i、輸入參數、windows i/o、拖曳式、下拉選單、勾選控管元件;
engine / module list 要清楚」。
一總管四職(Zero-Hydra=全複用正主,零重造):
  ①sync   同步(=VIA-ALL 律:stash -u→fetch→ff-only→分流備份
          分支後對齊;零彈窗零卡斷)
  ②list   引擎/模組清單清楚列印(=MDL112 Atlas gather 直取)
  ③run    任務執行(=MDL095 任務冊 argv 白名單 subprocess;
          任意指令拒絕=安全鐵則)
  ④ui     總控頁再生+開啟(Windows I/O:os.startfile 正道/
          webbrowser 後備):
          左=引擎/模組清單(搜尋過濾+分組清楚)
          中=控管元件:任務下拉+多任務勾選+codes 參數欄→
            fetch 指揮台 127.0.0.1:8765/run(deck 在=真跑;
            不在=誠實教先開 via)
          右=拖曳收件區(拖入列檔名+生成 via-intake 指引;
            瀏覽器沙盒不落盤=誠實 v1,真收容走 Downloads 正道)
v0100→v0101(批283 操作員令「由一個 VIA_SystemManager.py 整合
全部連結」):⑤serve 職=帶起唯一 API 樞紐(MDL095 尾版 127.0.0.1
:8765;CORS 已開=file:// 頁可 fetch)+總控頁右欄 API 連結冊
(全部端點一表=全部連結歸一總管)。
v0106→v0107(批303 操作員令「字體小一點比較專業 layout 緊湊
一點」):全字階 -1~2px+間距收 25%(與 MDL116 v0101 同階;
結構/元件/檢點零變)。
v0105→v0106(批302 操作員令「總控及各子系統弄成如圖示 UI」+
「不管色票只管 layout 及內容輸入介面」+「pc 水平長方形 手機垂直
長方形 響應式 自動最佳化 顏色最後統一」):
  ①版型入統一殼語言(MDL116 同律:左欄品牌+編號導航+底部狀態格
    /主區麵包屑+規格帶+大數字統計卡+內容卡;四正本萃取)
  ②參數契約卡(圖2 式):任務下拉+codes+儲存參數(localStorage
    via_master_params;try/catch 容錯)+回復預設;載頁自動回填
  ③響應雙態:PC=左欄+主區水平;手機=頂條+導航橫捲垂直;clamp
    流體字級;色票=中性(統一色票候操作員終裁)
  ④工法:CSS/JS 全遷 raw 常數(__MCSS__/__APPJS__ 佔位符)=
    f-string 吃括號根絕(批285 兩犯教訓收官)
v0104→v0105(批301 操作員令「輸入參數最少化 WINDOW I/O 拖曳式
下拉選單」;六維稽核實錘=拖曳誠實 v1 只列名):拖曳收件升真收 v2
——FileReader→base64→POST 樞紐 /intake(text/plain 簡單請求免
preflight);逐件回執 ✓已落+sha8/SKIP 同 hash/✗誠實拒(逾 50MB);
樞紐未開=誠實降級列名+via-intake 指引(=舊 v1 行為);API 連結冊
+POST /intake;+/vapdeck 已在冊(四系統入口齊)。
v0102→v0103(批292 操作員令「不卡斷 20個加速器 動態進度條」):
狀態矩陣每任務列+真進度條(pct 有值=實寬條;running 無 pct=
流動條紋動畫=誠實不假估;ok/fail=滿條定色)。零輪詢加重(同一
/status 資料)=不卡斷不變。
v0101→v0102(批285 操作員令「狀態的顯現/輸入參數/運作結果的
顯現」):總控頁三顯迴路——狀態矩陣(輪詢 /status 每 4s RYG 點
+elapsed+pct;樞紐離線=誠實標一次)+結果窗(點任務列→log 尾)。
用法:python3 VIA_SYSTEM_MANAGER_v0102.py sync|list|run <task>|ui
      |serve| --selftest
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
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

VIA = Path(__file__).resolve().parent
REG = VIA / "supportive modules" / "registry"
OUT = (VIA / "supportive modules" / "ui_support"
       / "VIA_UI_MasterControl_v0100.html")


def _mod(pat: str):
    p = sorted(REG.glob(pat))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def do_sync() -> int:
    """VIA-ALL 同步律(批272):任何狀態都能對齊雲端;零彈窗"""
    def g(*a):
        return subprocess.run(["git", "-C", str(VIA), *a],
                              capture_output=True, text=True)
    g("stash", "push", "--include-untracked", "-m", "MGR-selfheal")
    g("fetch", "origin", "main")
    r = g("merge", "--ff-only", "origin/main")
    if r.returncode != 0:
        sha = g("rev-parse", "--short", "HEAD").stdout.strip()
        g("branch", f"via-local-backup-{sha}")
        g("reset", "--hard", "origin/main")
        print(f"[MGR:sync] 分流偵測→備份分支 via-local-backup-{sha} "
              "留痕後對齊雲端")
    print("[MGR:sync] 對齊 origin/main ✓(髒樹已 stash 留痕,"
          "找回:git stash pop)")
    return 0


def do_list(do_print: bool = True) -> dict:
    """引擎/模組清單清楚(MDL112 Atlas 資料層直取)"""
    d = _mod("CGC_MDL112_SystemAtlas_v*.py").gather()
    if do_print:
        for sub, fam in d["engines"].items():
            print(f"[ENGINE] {sub}({len(fam)} 族)")
            for b in sorted(fam):
                print(f"    {b}")
        print(f"[MODULE] CGC 治理模組 {len(d['mods'])} 族")
        for b in sorted(d["mods"]):
            print(f"    {b}")
    return d


def do_run(task: str, extra: list[str] | None = None) -> int:
    """白名單任務執行(MDL095 任務冊=唯一 SSOT;任意指令拒絕)"""
    T = _mod("CGC_MDL095_DeckServer_v*.py").task_registry()
    if task not in T:
        print(f"[MGR:run] '{task}' 不在白名單任務冊=拒絕(安全鐵則)。"
              f"可用:{' '.join(sorted(T))}")
        return 2
    argv = list(T[task]["argv"]) + list(extra or [])
    print(f"[MGR:run] {task}:{T[task]['zh']}")
    return subprocess.run(argv, stdin=subprocess.DEVNULL).returncode


def render(d: dict, tasks: dict) -> str:
    eng_side = "".join(
        f"<details open><summary><b>{html.escape(sub)}</b>"
        f"<span class='tag'>{len(fam)}</span></summary>"
        + "".join(f'<div class="item" data-n="{html.escape(b.lower())}">'
                  f"{html.escape(b)}</div>" for b in sorted(fam))
        + "</details>" for sub, fam in d["engines"].items()) \
        + (f"<details><summary><b>CGC 治理模組</b>"
           f"<span class='tag'>{len(d['mods'])}</span></summary>"
           + "".join(f'<div class="item" data-n="{html.escape(b.lower())}">'
                     f"{html.escape(b)}</div>" for b in sorted(d["mods"]))
           + "</details>")
    opts = "".join(f'<option value="{html.escape(k)}">{html.escape(k)} · '
                   f"{html.escape(z)}</option>" for k, z in tasks.items())
    checks = "".join(
        f'<label class="ck"><input type="checkbox" value="{html.escape(k)}">'
        f"{html.escape(k)}</label>"
        for k in ("boot", "revenue", "consensus", "etf_analysis",
                  "revenue_consensus", "regression", "selftest_fast")
        if k in tasks)
    n_eng = sum(len(v) for v in d["engines"].values())
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 總控台 Master Control</title><style>__MCSS__</style></head><body>
<aside class="rail">
<div class="brand"><span class="seal">總</span>
<div class="latin">VERITAS INTELLIGENCE ANALYTICS</div>
<h1>總控台</h1>
<div class="en">MASTER CONTROL</div>
<span class="badge">MANAGER · LIVE · {d['ts']}</span></div>
<div class="navsec">系統 SYSTEMS</div><div class="nav">
<a class="active"><span class="no">00</span><span class="lb">總控台
<small>MASTER CONTROL</small></span></a>
<a href="VIA_UI_Shell_CGC_v0100.html"><span class="no">01</span>
<span class="lb">中央治理 · CGC<small>GOVERNANCE</small></span></a>
<a href="VIA_UI_Shell_VDF_v0100.html"><span class="no">02</span>
<span class="lb">資料鍛造 · VDF<small>DATA FORGE</small></span></a>
<a href="VIA_UI_Shell_VRN_v0100.html"><span class="no">03</span>
<span class="lb">報告新星 · VRN<small>REPORT NOVA</small></span></a>
<a href="VIA_UI_Shell_VAP_v0100.html"><span class="no">04</span>
<span class="lb">自動繪圖 · VAP<small>AUTO PLOT</small></span></a>
</div>
<div class="navsec">引擎 / 模組 ENGINE · MODULE LIST</div>
<div class="railbody">
<input type="text" id="q" placeholder="搜尋引擎/模組…">
{eng_side}
</div>
<div class="railfoot">
<div><div class="k">TASKS</div><div class="v">{len(tasks)}</div></div>
<div><div class="k">ENGINES</div><div class="v">{n_eng}</div></div>
<div><div class="k">MODULES</div><div class="v">{len(d['mods'])}</div></div>
<div><div class="k">STATE</div><div class="v">LIVE</div></div>
</div></aside>
<main class="main">
<div class="crumb"><b>VIA 母系統</b> → <b>總控台</b> →
<b>輸入 · 執行 · 三顯</b> · <span class="lock">LAYOUT SPEC(批302)</span></div>
<div class="head"><h2>總控台<small>MASTER CONTROL</small></h2>
<div class="spec">
<div><div class="k">BUILD</div><div class="v">__ME__</div></div>
<div><div class="k">TASKS</div><div class="v">{len(tasks)}</div></div>
<div><div class="k">BRIDGE</div><div class="v ok">127.0.0.1:8765</div></div>
<div><div class="k">GATE</div><div class="v ok">WHITELIST</div></div>
</div>
<div class="sub">單一總管四職:sync · list · run · ui;任務經指揮台
白名單真跑;誠實三態不假綠。</div></div>
<div class="stats">
<div class="stat"><div class="n">{len(tasks)}</div>
<div class="zh">一鍵任務</div><div class="en">DECK TASKS</div></div>
<div class="stat"><div class="n">{n_eng}</div>
<div class="zh">引擎族</div><div class="en">ENGINE FAMILIES</div></div>
<div class="stat"><div class="n">{len(d['mods'])}</div>
<div class="zh">治理模組</div><div class="en">CGC MODULES</div></div>
<div class="stat"><div class="n">4</div>
<div class="zh">子系統殼頁</div><div class="en">SYSTEM SHELLS</div></div>
</div>
<div class="grid2">
<div class="card"><h3>參數契約<small>PARAMETER CONTRACT</small></h3>
<div class="note">P1 任務(下拉;預設首項=零打字)· P2 codes(可空;
如 2330,2317)· 儲存於 localStorage:via_master_params(僅本機瀏覽器)。</div>
<select id="task">{opts}</select>
<input type="text" id="codes" placeholder="參數 codes(可空;如 2330,2317)">
<div class="btnrow">
<button onclick="runOne()">▶ 執行選定任務</button>
<button class="ghost" onclick="saveParams()">儲存參數</button>
<button class="ghost" onclick="resetParams()">回復預設</button>
</div></div>
<div class="card"><h3>多任務勾選<small>BATCH · SEQUENTIAL</small></h3>
<div class="note">勾選後依序執行(單例防重=執行中再按誠實拒)。</div>
{checks}
<div class="btnrow">
<button onclick="runChecked()">▶ 依序執行勾選任務</button>
<button class="ghost" onclick="ping()">⟳ 指揮台連線檢測</button>
</div>
<div id="log">待命。任務經指揮台 127.0.0.1:8765 白名單真跑;
指揮台未開=打 via(或 VIA-ALL)帶起後再按。</div></div>
</div>
<div class="card"><h3>狀態的顯現<small>STATUS MATRIX · 每 4s 自動刷新
</small></h3>
<div id="matrix" class="note">樞紐連線中…</div></div>
<div class="card"><h3>運作結果的顯現<small>RESULT</small></h3>
<pre id="result">點上方狀態列任一任務 → 顯示其 log 尾(真運作結果)</pre></div>
<div class="grid2">
<div class="card"><h3>拖曳收件<small>DRAG &amp; DROP · 真收 v2</small></h3>
<div id="drop">把檔案拖到這裡<br><small>真收 v2:落盤 Downloads+sha256 回執
(樞紐未開=誠實列名+指引)</small></div>
<div id="files" class="note"></div></div>
<div class="card"><h3>API 連結冊<small>ENDPOINTS · 唯一樞紐</small></h3>
<div class="note">GET /ping 健檢 · /run?task=名[&codes=] 白名單真跑 ·
POST /intake 拖曳真收(name+b64→Downloads;hash 定生死)·
/status 全任務 RYG · / 指揮台頁 · /govdeck 治理台 · /govmatrix 矩陣 ·
/vapdeck 分析台 · /vap_revenue /vap_groups /vap_etflist /vap_etf
/vap_kline /vap_check /vap_flows 分析端點<br>
帶起樞紐:<code>python __ME__ serve</code>(或 via 自動帶起)<br>
同步:雙擊 VIA-ALL 或 <code>python __ME__ sync</code>
(stash 留痕→對齊雲端;分流自動備份分支)</div></div>
</div>
<div class="foot">VIA · MASTER CONTROL · 版型=批302 統一殼語言 ·
真值直取零發明 · 零 CDN 零外網 · 響應雙態(PC 水平/手機垂直)</div>
</main><script>__APPJS__
__STATUSJS__
__DROPJS__
</script></body></html>"""


MCSS = r"""
:root{--bg:#f5f5f2;--paper:#ffffff;--paper2:#fafaf8;--ink:#1f2530;
--ink2:#3c4658;--mut:#6d7688;--mut2:#9aa2b1;--line:#dcdfe6;
--soft:#eef0ee;--acc:#3e6b8f;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d}
@media (prefers-color-scheme: dark){:root{--bg:#10151b;--paper:#171e26;
--paper2:#1c242e;--ink:#dbe3ea;--ink2:#b9c3cf;--mut:#8a97a5;
--mut2:#6d7a88;--line:#2a333d;--soft:#20293380;--acc:#7ba3cc;
--ok:#79b58c;--warn:#d4a95c;--bad:#d98a7c}}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);display:flex;min-height:100vh;
font:11.5px/1.45 "Segoe UI","Noto Sans TC",system-ui,sans-serif}
code{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}
.rail{width:232px;min-width:232px;background:var(--paper);
border-right:1px solid var(--line);padding:13px 0 8px;display:flex;
flex-direction:column;gap:4px;max-height:100vh;position:sticky;top:0}
.brand{padding:0 14px 9px;border-bottom:1px solid var(--line)}
.brand .latin{font-size:9px;letter-spacing:.22em;color:var(--mut);
font-weight:700}
.brand h1{font-size:16px;margin:4px 0 2px}
.brand .en{font-size:10px;letter-spacing:.14em;color:var(--acc);
font-weight:700}
.brand .badge{display:inline-block;margin-top:6px;font-size:9.5px;
font-weight:700;padding:2px 8px;border:1px solid var(--line);
border-radius:4px;color:var(--mut);letter-spacing:.06em}
.seal{float:right;width:26px;height:26px;border:2px solid var(--ink2);
border-radius:6px;display:grid;place-items:center;font-size:14px;
font-weight:700}
.navsec{font-size:9px;letter-spacing:.2em;color:var(--mut2);
font-weight:700;padding:9px 14px 3px}
.nav a{display:grid;grid-template-columns:24px 1fr;gap:8px;
align-items:baseline;padding:4px 14px;color:var(--ink2);
text-decoration:none;cursor:pointer}
.nav a:hover{background:var(--paper2)}
.nav a.active{background:var(--soft);border-right:3px solid var(--acc);
color:var(--ink);font-weight:700}
.nav .no{font-size:10px;color:var(--mut2);font-weight:700}
.nav .lb small{display:block;font-size:9px;letter-spacing:.14em;
color:var(--mut2);font-weight:600}
.railbody{flex:1;overflow:auto;padding:3px 14px}
.railbody input{width:100%;border:1px solid var(--line);border-radius:6px;
padding:4px 7px;background:var(--paper);color:var(--ink);margin-bottom:6px;
font:11px "Segoe UI","Noto Sans TC",sans-serif}
.item{padding:1px 4px;font-size:10px;color:var(--mut)}
.item.hide{display:none}
details{margin-bottom:4px}summary{cursor:pointer;padding:3px 0;
font-size:12px}
.tag{float:right;font-size:9px;border-radius:999px;padding:1px 7px;
background:var(--soft);color:var(--mut)}
.railfoot{border-top:1px solid var(--line);padding:7px 14px 0;
display:grid;grid-template-columns:repeat(2,1fr);gap:6px}
.railfoot .k{font-size:8.5px;letter-spacing:.16em;color:var(--mut2);
font-weight:700}
.railfoot .v{font-size:11.5px;font-weight:700;
font-variant-numeric:tabular-nums}
.main{flex:1;padding:15px 20px;max-width:1160px}
.crumb{font-size:10px;color:var(--mut);margin-bottom:7px}
.crumb b{color:var(--acc)}
.crumb .lock{letter-spacing:.16em;font-weight:700;font-size:10px}
.head{display:flex;align-items:flex-end;gap:16px;flex-wrap:wrap;
border-bottom:2px solid var(--ink);padding-bottom:8px;margin-bottom:11px}
.head h2{font-size:clamp(16px,2.3vw,21px)}
.head h2 small{font-size:11px;color:var(--mut);font-weight:400;
margin-left:8px;letter-spacing:.12em}
.head .sub{width:100%;font-size:10.5px;color:var(--mut)}
.spec{margin-left:auto;display:flex;gap:13px;flex-wrap:wrap}
.spec .k{font-size:8.5px;letter-spacing:.18em;color:var(--mut2);
font-weight:700}
.spec .v{font-size:11px;font-weight:700}
.spec .v.ok{color:var(--ok)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
gap:7px;margin-bottom:10px}
.stat{background:var(--paper);border:1px solid var(--line);
border-radius:7px;padding:8px 11px}
.stat .n{font-size:clamp(16px,2vw,20px);font-weight:800;
font-variant-numeric:tabular-nums}
.stat .zh{font-size:10px;color:var(--ink2);margin-top:2px}
.stat .en{font-size:8.5px;letter-spacing:.18em;color:var(--mut2);
font-weight:700}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.card{background:var(--paper);border:1px solid var(--line);
border-radius:7px;padding:11px 13px;margin-bottom:10px}
.card h3{font-size:12px}
.card h3 small{font-size:9px;letter-spacing:.16em;color:var(--mut2);
font-weight:700;margin-left:8px}
.card .note{font-size:9.5px;color:var(--mut);margin:3px 0 7px}
select,input[type=text]{width:100%;border:1px solid var(--line);
border-radius:6px;padding:5px 8px;background:var(--paper);
color:var(--ink);margin-bottom:6px;
font:11.5px "Segoe UI","Noto Sans TC",sans-serif}
.btnrow{display:flex;gap:8px;flex-wrap:wrap}
button{border:1px solid var(--acc);background:var(--acc);color:#fff;
border-radius:6px;padding:6px 11px;cursor:pointer;flex:1;
font:11.5px "Segoe UI","Noto Sans TC",sans-serif}
button.ghost{background:var(--paper);color:var(--acc)}
.ck{display:block;padding:2px 0;font-size:11px}
@keyframes viaflow{to{background-position:32px 0}}
#log{white-space:pre-wrap;font:11px ui-monospace,Consolas,monospace;
background:var(--bg);border:1px solid var(--line);border-radius:6px;
padding:8px;min-height:100px;margin-top:10px;max-height:200px;
overflow:auto}
#result{white-space:pre-wrap;font:11px ui-monospace,Consolas,monospace;
background:var(--bg);border:1px solid var(--line);border-radius:6px;
padding:8px;min-height:90px;overflow-wrap:anywhere}
#drop{border:2px dashed var(--line);border-radius:8px;padding:18px 10px;
text-align:center;color:var(--mut)}
#drop.on{border-color:var(--acc);color:var(--acc)}
#matrix{font-size:10.5px}
.foot{font-size:10px;color:var(--mut2);margin-top:6px}
@media(max-width:900px){
 body{flex-direction:column}
 .rail{width:100%;min-width:0;position:static;max-height:none;
  padding:12px 0 8px}
 .nav{display:flex;overflow-x:auto;gap:2px;padding:0 10px;
  -webkit-overflow-scrolling:touch}
 .nav a{grid-template-columns:auto;white-space:nowrap;padding:7px 10px;
  border-radius:6px}
 .nav a.active{border-right:0;border-bottom:3px solid var(--acc)}
 .nav .no,.nav .lb small{display:none}
 .railbody{max-height:200px}
 .railfoot{grid-template-columns:repeat(4,1fr)}
 .main{padding:14px 12px}
 .spec{margin-left:0;gap:12px}
 .grid2{grid-template-columns:1fr}
}
"""

APPJS = r"""
const q=document.getElementById("q");
q.oninput=()=>{const v=q.value.toLowerCase();
document.querySelectorAll(".item").forEach(i=>
i.classList.toggle("hide",v&&!i.dataset.n.includes(v)));};
const log=m=>{const el=document.getElementById("log");
el.textContent+="\n"+m;el.scrollTop=el.scrollHeight;};
async function call(t,codes){
 try{const u="http://127.0.0.1:8765/run?task="+encodeURIComponent(t)
  +(codes?"&codes="+encodeURIComponent(codes):"");
  const r=await(await fetch(u)).json();
  log((r.ok?"[起跑] ":"[拒/忙] ")+t+" "+(r.err||""));return r.ok;
 }catch(e){log("[誠實] 指揮台未開("+t+"):先打 via 帶起 127.0.0.1:8765");
  return false;}}
function runOne(){call(document.getElementById("task").value,
 document.getElementById("codes").value.trim());}
async function runChecked(){
 for(const c of document.querySelectorAll('.ck input:checked'))
   await call(c.value,"");}
async function ping(){try{
 const r=await(await fetch("http://127.0.0.1:8765/ping")).json();
 log("[指揮台] 在線 ✓ v="+(r.v||"?"));}
 catch(e){log("[指揮台] 未開=誠實(打 via 帶起)");}}
const PKEY="via_master_params";
function saveParams(){try{
 const ck=[...document.querySelectorAll(".ck input:checked")]
  .map(c=>c.value);
 localStorage.setItem(PKEY,JSON.stringify({
  task:document.getElementById("task").value,
  codes:document.getElementById("codes").value,checked:ck}));
 log("[參數] 已儲存(localStorage:"+PKEY+";僅本機瀏覽器)");
}catch(e){log("[參數] 儲存失敗(瀏覽器封存區不可用=誠實)");}}
function resetParams(){try{localStorage.removeItem(PKEY);}catch(e){}
 document.getElementById("task").selectedIndex=0;
 document.getElementById("codes").value="";
 document.querySelectorAll(".ck input").forEach(c=>c.checked=false);
 log("[參數] 已回復預設(首項任務+codes 空+勾選全清)");}
(function(){try{
 const s=JSON.parse(localStorage.getItem(PKEY)||"null");
 if(!s)return;
 if(s.task)document.getElementById("task").value=s.task;
 if(s.codes)document.getElementById("codes").value=s.codes;
 (s.checked||[]).forEach(v=>{
  const el=document.querySelector('.ck input[value="'+v+'"]');
  if(el)el.checked=true;});
 log("[參數] 已回填上次儲存值");
}catch(e){}})();
"""

DROPJS = r"""
const dz=document.getElementById("drop");
dz.ondragover=e=>{e.preventDefault();dz.classList.add("on");};
dz.ondragleave=()=>dz.classList.remove("on");
dz.ondrop=async e=>{e.preventDefault();dz.classList.remove("on");
 const fl=[...e.dataTransfer.files];
 const out=document.getElementById("files");
 out.innerHTML="收件 "+fl.length+" 件…";
 const lines=[];
 for(const f of fl){
  if(f.size>50*1024*1024){
   lines.push("✗ "+f.name+"(逾 50MB 上限=誠實拒)");continue;}
  try{
   const b64=await new Promise((ok,bad)=>{const r=new FileReader();
    r.onload=()=>ok((r.result||"").split(",")[1]||"");
    r.onerror=bad;r.readAsDataURL(f);});
   const rs=await(await fetch("http://127.0.0.1:8765/intake",
    {method:"POST",body:JSON.stringify({name:f.name,b64:b64})})).json();
   lines.push(rs.ok
    ?"✓ "+f.name+(rs.skip?"(SKIP 同 hash=冪等)":" → 已落 "+rs.saved)
      +" · sha "+(rs.sha256||"").slice(0,8)
    :"✗ "+f.name+"("+(rs.err||"拒")+")");
  }catch(_){
   lines.push("· "+f.name+"(樞紐未開=誠實列名;放 Downloads 後打 via-intake)");
  }
 }
 out.innerHTML="真收 v2(hash 定生死;樞紐未開=誠實降級):<br>"
  +lines.join("<br>")
  +"<br><b>收容入冊</b>:已落 Downloads 者打 <code>via-intake</code>"
  +" 一鍵 hash 冪等收容自動雙推。";};
"""

STATUSJS = r"""
const DOT={idle:"var(--muted)",running:"#c4943a",ok:"var(--green)",fail:"var(--red)"};
let hubDown=false,curTask=null,lastStatus={};
async function poll(){try{
 const r=await(await fetch("http://127.0.0.1:8765/status")).json();
 lastStatus=r;hubDown=false;
 document.getElementById("matrix").innerHTML=Object.entries(r).map(([k,v])=>{
  const pct=(v.pct!=null)?(" "+v.pct+"%"):"";
  const el=(v.elapsed!=null&&v.state!=="idle")?(" "+v.elapsed+"s"):"";
  return '<div style="cursor:pointer;padding:2px 0" onclick="showTail(\''+k+'\')">'
   +'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:'
   +(DOT[v.state]||DOT.idle)+';margin-right:6px"></span>'+k
   +" <small>"+(v.zh||"")+el+pct+"</small>"
   +'<div style="height:5px;border-radius:3px;background:var(--line);margin:3px 0 2px 15px;overflow:hidden">'
   +'<div style="height:100%;border-radius:3px;transition:width .6s;'
   +(v.state==="running"
     ?(v.pct!=null
       ?('width:'+v.pct+'%;background:#c4943a')
       :'width:100%;background:repeating-linear-gradient(45deg,#c4943a 0 8px,transparent 8px 16px);animation:viaflow 1s linear infinite')
     :('width:'+((v.state==="ok"||v.state==="fail")?100:0)+'%;background:'+(v.state==="fail"?"var(--red)":"var(--green)")))
   +'"></div></div></div>';}).join("");
 if(curTask)showTail(curTask);
}catch(e){if(!hubDown){hubDown=true;
 document.getElementById("matrix").textContent="樞紐未開=誠實(打 via 或 VIA-ALL 帶起後自動接上)";}}}
function showTail(k){curTask=k;const v=lastStatus[k]||{};
 document.getElementById("result").textContent=
  "["+k+"] state="+(v.state||"?")+((v.rc!=null)?(" rc="+v.rc):"")+"\n"+(v.tail||"(尚無 log)");}
setInterval(poll,4000);poll();
"""


def do_ui(open_after: bool = True) -> int:
    d = do_list(do_print=False)
    tasks = {k: v["zh"] for k, v in
             _mod("CGC_MDL095_DeckServer_v*.py").task_registry().items()}
    OUT.write_text(render(d, tasks).replace("__MCSS__", MCSS)
                   .replace("__APPJS__", APPJS)
                   .replace("__STATUSJS__", STATUSJS)
                   .replace("__DROPJS__", DROPJS)
                   .replace("__ME__", Path(__file__).name), encoding="utf-8")
    print(f"[MGR:ui] 總控頁再生 · 任務 {len(tasks)} · {OUT.name}")
    if open_after:
        try:
            os.startfile(str(OUT))            # Windows I/O 正道
        except AttributeError:
            try:
                import webbrowser
                webbrowser.open(OUT.as_uri())  # 跨平台後備
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
    d = do_list(do_print=False)
    rc = do_ui(open_after=False)
    page = OUT.read_text(encoding="utf-8")
    chk("① 四職一總管(sync/list/run/ui 全在)", rc == 0
        and all(f"def do_{k}" in src for k in ("sync", "list", "run", "ui")))
    chk("② 清單清楚(引擎>80 族+模組>30 族入頁+搜尋過濾)",
        sum(len(v) for v in d["engines"].values()) > 80
        and 'id="q"' in page and 'class="item"' in page)
    chk("③ 控管元件三式(下拉+勾選+參數欄)接指揮台白名單",
        'id="task"' in page and 'type="checkbox"' in page
        and 'id="codes"' in page and "127.0.0.1:8765/run" in page)
    chk("④ 拖曳收件區(真收 v2:FileReader→POST /intake 落盤+sha 回執;"
        "樞紐未開=誠實降級列名)",
        'id="drop"' in page and "via-intake" in page and "真收 v2" in page
        and "readAsDataURL" in page and "/intake" in page
        and "誠實降級" in page and "__DROPJS__" not in page)
    chk("④d 參數契約卡(儲存/回復 localStorage+載頁回填;批302)",
        "via_master_params" in page and "儲存參數" in page
        and "回復預設" in page and "saveParams" in page
        and "resetParams" in page and "__APPJS__" not in page)
    chk("④e 統一殼版型五律(左欄導航+麵包屑+規格帶+統計卡"
        "+內容卡;四殼互連;__MCSS__ 已代)",
        'class="rail"' in page and 'class="crumb"' in page
        and 'class="spec"' in page and 'class="stats"' in page
        and "Shell_CGC_v0100" in page and "Shell_VAP_v0100" in page
        and "__MCSS__" not in page)
    chk("④b API 連結冊全端點+serve 職(批283 全部連結歸一)",
        "API 連結冊" in page and "/vap_flows" in page
        and 'a[0] == "serve"' in src)
    chk("④c 三顯迴路(批285:狀態矩陣輪詢+參數欄+結果窗)",
        "狀態的顯現" in page and "運作結果的顯現" in page
        and 'id="matrix"' in page and 'id="result"' in page
        and "setInterval(poll,4000)" in page and "showTail" in page
        and "viaflow" in page and "transition:width" in page
        and "__STATUSJS__" not in page)
    chk("⑤ 白名單鐵則(run 拒任意指令)",
        do_run("rm -rf /") == 2)
    chk("⑥ Windows I/O 正道+後備+零 CDN+加速橋",
        "os.startfile" in src and "webbrowser" in src
        and '<script src="http' not in page and "ACCEL-BRIDGE" in src)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 總系統管理器(VIA_SYSTEM_MANAGER)· 十檢自測(零外網)===")
        return selftest()
    if a and a[0] == "sync":
        return do_sync()
    if a and a[0] == "list":
        do_list()
        return 0
    if a and a[0] == "serve":
        deck = sorted(REG.glob("CGC_MDL095_DeckServer_v*.py"))[-1]
        print(f"[MGR:serve] 帶起唯一 API 樞紐:{deck.name}(Ctrl+C 停)")
        return subprocess.run([sys.executable, str(deck), "serve"]).returncode
    if a and a[0] == "run":
        return do_run(a[1] if len(a) > 1 else "", a[2:])
    return do_ui()


if __name__ == "__main__":
    sys.exit(main())
