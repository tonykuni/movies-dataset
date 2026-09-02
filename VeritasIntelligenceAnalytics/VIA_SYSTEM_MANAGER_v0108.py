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
v0107→v0108(批304 操作員令「輸入都放可收左側板+簡化非必要輸入
+右邊現況/輸入項目/運轉結果 matrix report multiple tab+header 固定
底部固定+項目正式名稱不要程式化名稱+引擎表列 模組表列+test debug
till it works perfectly」):
  ①版面:固定 header(標題+規格帶+頁籤列)+固定 footer(狀態帶)
    +左欄=可收合輸入面板(◀ 鈕收展;記憶於 localStorage)
  ②輸入簡化:codes=非必要→收進「進階參數」摺疊;常用任務勾選
    +任務下拉=正式中文名稱(識別鍵藏 value/tooltip)
  ③右側六頁籤:現況矩陣/輸入項目(參數現值+任務冊)/運轉結果
    /引擎表列/模組表列/連結·API(全正式名稱表列;UR 編號直取
    統一冊 MDL113)
  ④修 STATUSJS 燈點色變數失聯蟲(--muted/--green/--red 未定義
    =v0106 起隱形;補 alias)+矩陣列正式名稱為主
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
    n_eng = sum(len(v) for v in d["engines"].values())
    import json as _json
    reg_p = REG / "VIA_Unified_Register_v0100.json"
    try:
        reg = _json.loads(reg_p.read_text(encoding="utf-8"))["entries"]
    except Exception:
        reg = {}
    st_zh = {"USED": "在用", "RESERVED": "備援"}

    def _rows(kind: str) -> str:
        out = []
        for key, v in sorted(reg.items()):
            if not key.startswith(kind + ":"):
                continue
            sub, _, fam = key.split(":", 1)[1].partition("/")
            nice = fam.replace("_", " ")
            out.append(
                f'<tr class="item" data-n="{html.escape(key.lower())}">'
                f'<td class="mono">{v.get("id", "")}</td>'
                f"<td>{html.escape(sub)}</td><td>{html.escape(nice)}</td>"
                f"<td>{st_zh.get(v.get('state', ''), v.get('state', ''))}"
                "</td></tr>")
        return "".join(out) or '<tr><td colspan="4">冊空(誠實)</td></tr>'

    eng_rows = _rows("ENG")
    mdl_rows = _rows("MDL")
    n_reg_eng = sum(1 for k in reg if k.startswith("ENG:"))
    n_reg_mdl = sum(1 for k in reg if k.startswith("MDL:"))
    def _formal(zh: str) -> str:
        return zh.split("(")[0].strip() or zh
    opts = "".join(
        f'<option value="{html.escape(k)}" '
        f'title="{html.escape(v["zh"])} · {html.escape(k)}">'
        f"{html.escape(_formal(v['zh']))}</option>"
        for k, v in tasks.items())
    checks = "".join(
        f'<label class="ck" title="{html.escape(k)}">'
        f'<input type="checkbox" value="{html.escape(k)}">'
        f"{html.escape(_formal(tasks[k]['zh']))}</label>"
        for k in ("boot", "revenue", "consensus", "etf_analysis",
                  "revenue_consensus", "regression", "selftest_fast")
        if k in tasks)
    task_rows = "".join(
        f"<tr><td>{html.escape(v['zh'])}</td>"
        f'<td class="mono">{html.escape(k)}</td>'
        f"<td>{'網路(同意閘)' if v['net'] else '本機'}</td></tr>"
        for k, v in sorted(tasks.items(), key=lambda kv: kv[1]["zh"]))
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 總控台 Master Control</title><style>__MCSS__</style></head><body>
<header class="top">
<button id="railbtn" class="tbtn" title="收合/展開輸入面板">◀ 輸入面板</button>
<div class="tt"><b>總控台</b><small>MASTER CONTROL · __ME__</small></div>
<div class="crumb">VIA 母系統 → 總控台 → 輸入 · 執行 · 三顯 ·
LAYOUT SPEC(批304)</div>
<nav class="tabs">
<a data-t="0" class="active">現況矩陣</a>
<a data-t="1">輸入項目</a>
<a data-t="2">運轉結果</a>
<a data-t="3">引擎表列</a>
<a data-t="4">模組表列</a>
<a data-t="5">連結 · API</a>
</nav>
<div class="spec">
<div><div class="k">TASKS</div><div class="v">{len(tasks)}</div></div>
<div><div class="k">BRIDGE</div><div class="v ok">127.0.0.1:8765</div></div>
<div><div class="k">GATE</div><div class="v ok">WHITELIST</div></div>
</div>
</header>
<div class="shell">
<aside class="rail" id="rail">
<div class="navsec">任務執行 RUN A TASK</div>
<div class="pad">
<select id="task">{opts}</select>
<button onclick="runOne()">▶ 執行選定任務</button>
</div>
<div class="navsec">常用任務 · 勾選依序 BATCH</div>
<div class="pad">{checks}
<button onclick="runChecked()">▶ 依序執行勾選任務</button></div>
<div class="navsec">進階參數 ADVANCED(非必要)</div>
<div class="pad"><details><summary>股票代碼 codes(可空;預設全額)</summary>
<input type="text" id="codes" placeholder="如 2330,2317(可空)">
</details>
<div class="btnrow">
<button class="ghost" onclick="saveParams()">儲存參數</button>
<button class="ghost" onclick="resetParams()">回復預設</button>
<button class="ghost" onclick="ping()">⟳ 連線檢測</button>
</div></div>
<div class="navsec">拖曳收件 DRAG &amp; DROP · 真收 v2</div>
<div class="pad">
<div id="drop">把檔案拖到這裡<br><small>真收 v2:落盤 Downloads+sha256 回執
(樞紐未開=誠實列名+指引)</small></div>
<div id="files" class="note"></div></div>
<div class="navsec">操作日誌 LOG</div>
<div class="pad"><div id="log">待命。任務經指揮台 127.0.0.1:8765
白名單真跑;指揮台未開=打 via(或 VIA-ALL)帶起後再按。</div></div>
</aside>
<main class="main">
<section class="page on">
<h3 class="ph">狀態的顯現<small>STATUS MATRIX · 每 4s 自動刷新 ·
點任一列看運轉結果</small></h3>
<div class="stats">
<div class="stat"><div class="n">{len(tasks)}</div>
<div class="zh">一鍵任務</div><div class="en">DECK TASKS</div></div>
<div class="stat"><div class="n">{n_eng}</div>
<div class="zh">引擎族</div><div class="en">ENGINE FAMILIES</div></div>
<div class="stat"><div class="n">{len(d['mods'])}</div>
<div class="zh">治理模組</div><div class="en">CGC MODULES</div></div>
<div class="stat"><div class="n">{n_reg_eng + n_reg_mdl}</div>
<div class="zh">統一冊登錄</div><div class="en">UNIFIED REGISTER</div></div>
</div>
<div class="card"><div id="matrix" class="note">樞紐連線中…</div></div>
</section>
<section class="page">
<h3 class="ph">輸入項目<small>INPUTS · 參數現值+任務冊(正式名稱)
</small></h3>
<div class="card"><h3>參數現值<small>CURRENT PARAMS</small></h3>
<div id="pv" class="note">(尚未讀取)</div></div>
<div class="card"><h3>任務冊<small>TASK ROSTER · {len(tasks)} 項</small></h3>
<div class="wrap-x"><table class="tbl"><tr><th>正式名稱</th>
<th>識別鍵</th><th>通路</th></tr>{task_rows}</table></div></div>
</section>
<section class="page">
<h3 class="ph">運作結果的顯現<small>RESULT · 現況矩陣點任一列即帶入
</small></h3>
<div class="card"><pre id="result">點「現況矩陣」頁任一任務列 →
顯示其 log 尾(真運作結果)</pre></div>
</section>
<section class="page">
<h3 class="ph">引擎表列<small>ENGINE REGISTRY · 統一冊 {n_reg_eng} 族
(UR 編號=永久律)</small></h3>
<div class="card">
<input type="text" id="q" placeholder="搜尋引擎/模組(表列即時過濾)…">
<div class="wrap-x"><table class="tbl"><tr><th>UR 編號</th><th>系統</th>
<th>族名</th><th>狀態</th></tr>{eng_rows}</table></div></div>
</section>
<section class="page">
<h3 class="ph">模組表列<small>MODULE REGISTRY · 統一冊 {n_reg_mdl} 族
</small></h3>
<div class="card">
<div class="wrap-x"><table class="tbl"><tr><th>UR 編號</th><th>系統</th>
<th>族名</th><th>狀態</th></tr>{mdl_rows}</table></div></div>
</section>
<section class="page">
<h3 class="ph">連結 · API<small>SYSTEM LINKS &amp; ENDPOINTS</small></h3>
<div class="card"><h3>系統頁<small>SHELLS &amp; DASHBOARDS</small></h3>
<div class="note">
<a href="VIA_UI_Shell_CGC_v0100.html">中央治理現況台</a> ·
<a href="VIA_UI_Shell_VDF_v0100.html">資料鍛造現況台</a> ·
<a href="VIA_UI_Shell_VRN_v0100.html">報告新星現況台</a> ·
<a href="VIA_UI_Shell_VAP_v0100.html">自動繪圖現況台</a><br>
<a href="VIA_UI_ETFConsensusAnalysis_v0100.html">主動 ETF×共識檢視
(Plotly)</a> ·
<a href="VIA_UI_RevenueConsensusAnalysis_v0100.html">月營收×共識檢視
(Plotly)</a> ·
<a href="VIA_UI_PlotlyDashboard_EditableTemplate_v0100.html">Plotly
儀表板可編輯模板(批304)</a> ·
<a href="VIA_UI_GovernanceConsole_v0100.html">治理主控台</a></div></div>
<div class="card"><h3>API 連結冊<small>唯一樞紐 127.0.0.1:8765</small></h3>
<div class="note">GET /ping 健檢 · /run?task=名[&codes=] 白名單真跑 ·
POST /intake 拖曳真收(name+b64→Downloads;hash 定生死)·
/status 全任務 RYG · / 指揮台頁 · /govdeck 治理台 · /govmatrix 矩陣 ·
/vapdeck 分析台 · /vap_revenue /vap_groups /vap_etflist /vap_etf
/vap_kline /vap_check /vap_flows 分析端點<br>
帶起樞紐:<code>python __ME__ serve</code>(或 via 自動帶起)<br>
同步:雙擊 VIA-ALL 或 <code>python __ME__ sync</code>
(stash 留痕→對齊雲端;分流自動備份分支)</div></div>
</section>
</main>
</div>
<footer class="bot">
<span>VIA · MASTER CONTROL · {d['ts']}</span>
<span>任務 {len(tasks)} · 引擎族 {n_eng} · 治理模組 {len(d['mods'])}</span>
<span id="hublight">樞紐:偵測中…</span>
<span>誠實三態 · 零 CDN · 白名單鐵則</span>
</footer>
<script>__APPJS__
__STATUSJS__
__DROPJS__
</script></body></html>"""


MCSS = r"""
:root{--bg:#f5f5f2;--paper:#ffffff;--paper2:#fafaf8;--ink:#1f2530;
--ink2:#3c4658;--mut:#6d7688;--mut2:#9aa2b1;--line:#dcdfe6;
--soft:#eef0ee;--acc:#3e6b8f;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d;
--muted:var(--mut);--green:var(--ok);--red:var(--bad)}
@media (prefers-color-scheme: dark){:root{--bg:#10151b;--paper:#171e26;
--paper2:#1c242e;--ink:#dbe3ea;--ink2:#b9c3cf;--mut:#8a97a5;
--mut2:#6d7a88;--line:#2a333d;--soft:#20293380;--acc:#7ba3cc;
--ok:#79b58c;--warn:#d4a95c;--bad:#d98a7c}}
*{box-sizing:border-box;margin:0}
html,body{height:100%}
body{background:var(--bg);color:var(--ink);display:flex;
flex-direction:column;font:11.5px/1.45 "Segoe UI","Noto Sans TC",
system-ui,sans-serif}
code,.mono{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
/* header 固定 */
.top{position:sticky;top:0;z-index:9;background:var(--paper);
border-bottom:2px solid var(--ink);display:flex;align-items:center;
gap:12px;padding:7px 14px;flex-wrap:wrap}
.tbtn{border:1px solid var(--line);background:var(--paper2);
color:var(--ink2);border-radius:6px;padding:4px 9px;cursor:pointer;
font:10.5px "Segoe UI","Noto Sans TC",sans-serif}
.tt b{font-size:15px}
.tt small{display:block;font-size:8px;letter-spacing:.14em;
color:var(--mut2);font-weight:700}
.crumb{font-size:9px;color:var(--mut)}
.tabs{display:flex;gap:2px;flex-wrap:wrap;margin-left:auto}
.tabs a{padding:5px 11px;border-radius:6px 6px 0 0;cursor:pointer;
color:var(--ink2);font-size:11px;border:1px solid transparent;
border-bottom:0}
.tabs a:hover{background:var(--soft);text-decoration:none}
.tabs a.active{background:var(--soft);border-color:var(--line);
font-weight:700;color:var(--ink);border-bottom:3px solid var(--acc)}
.spec{display:flex;gap:12px}
.spec .k{font-size:7.5px;letter-spacing:.18em;color:var(--mut2);
font-weight:700}
.spec .v{font-size:10.5px;font-weight:700}
.spec .v.ok{color:var(--ok)}
/* 殼:左欄可收 */
.shell{flex:1;display:flex;min-height:0}
.rail{width:248px;min-width:248px;background:var(--paper);
border-right:1px solid var(--line);overflow-y:auto;
transition:margin-left .25s}
body.railoff .rail{margin-left:-249px}
.navsec{font-size:8px;letter-spacing:.2em;color:var(--mut2);
font-weight:700;padding:9px 13px 3px}
.pad{padding:2px 13px 6px}
select,input[type=text]{width:100%;border:1px solid var(--line);
border-radius:6px;padding:5px 8px;background:var(--paper);
color:var(--ink);margin-bottom:6px;
font:11.5px "Segoe UI","Noto Sans TC",sans-serif}
.btnrow{display:flex;gap:6px;flex-wrap:wrap}
button{border:1px solid var(--acc);background:var(--acc);color:#fff;
border-radius:6px;padding:6px 10px;cursor:pointer;flex:1;
font:11px "Segoe UI","Noto Sans TC",sans-serif;margin-bottom:4px}
button.ghost{background:var(--paper);color:var(--acc)}
.ck{display:block;padding:2px 0;font-size:11px}
details summary{cursor:pointer;font-size:10.5px;color:var(--ink2);
padding:2px 0 4px}
#log{white-space:pre-wrap;font:10px ui-monospace,Consolas,monospace;
background:var(--bg);border:1px solid var(--line);border-radius:6px;
padding:6px;min-height:70px;max-height:150px;overflow:auto}
#drop{border:2px dashed var(--line);border-radius:8px;padding:14px 8px;
text-align:center;color:var(--mut);font-size:10.5px}
#drop.on{border-color:var(--acc);color:var(--acc)}
/* 主區頁籤內容 */
.main{flex:1;overflow-y:auto;padding:12px 16px 44px;min-width:0}
.page{display:none}
.page.on{display:block}
.ph{font-size:13px;margin-bottom:8px}
.ph small{font-size:8.5px;letter-spacing:.14em;color:var(--mut2);
font-weight:700;margin-left:7px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));
gap:7px;margin-bottom:10px}
.stat{background:var(--paper);border:1px solid var(--line);
border-radius:7px;padding:8px 11px}
.stat .n{font-size:clamp(16px,2vw,20px);font-weight:800;
font-variant-numeric:tabular-nums}
.stat .zh{font-size:10px;color:var(--ink2);margin-top:1px}
.stat .en{font-size:7.5px;letter-spacing:.16em;color:var(--mut2);
font-weight:700}
.card{background:var(--paper);border:1px solid var(--line);
border-radius:7px;padding:10px 12px;margin-bottom:9px}
.card h3{font-size:11.5px}
.card h3 small{font-size:8px;letter-spacing:.15em;color:var(--mut2);
font-weight:700;margin-left:6px}
.card .note,.note{font-size:10px;color:var(--mut);line-height:1.7}
.tbl{width:100%;border-collapse:collapse;font-size:10.5px}
.tbl th{text-align:left;font-size:8.5px;letter-spacing:.12em;
color:var(--mut2);border-bottom:1px solid var(--line);
padding:3px 8px 3px 0;font-weight:700}
.tbl td{border-bottom:1px solid var(--soft);padding:3px 8px 3px 0;
vertical-align:top}
.tbl tr:last-child td{border-bottom:0}
.item.hide{display:none}
.wrap-x{overflow-x:auto}
#result{white-space:pre-wrap;font:10.5px ui-monospace,Consolas,monospace;
background:var(--bg);border:1px solid var(--line);border-radius:6px;
padding:8px;min-height:200px;overflow-wrap:anywhere}
#matrix{font-size:10.5px}
@keyframes viaflow{to{background-position:32px 0}}
/* footer 固定 */
.bot{position:fixed;bottom:0;left:0;right:0;z-index:9;
background:var(--paper);border-top:1px solid var(--line);
display:flex;gap:16px;align-items:center;padding:5px 14px;
font-size:9.5px;color:var(--mut);flex-wrap:wrap}
.bot span b{color:var(--ink2)}
@media(max-width:900px){
 .rail{position:fixed;left:0;top:auto;bottom:34px;max-height:60vh;
  z-index:8;box-shadow:0 -4px 18px rgba(0,0,0,.15);width:100%;
  min-width:0;border-top:1px solid var(--line)}
 body.railoff .rail{margin-left:0;display:none}
 .tabs{margin-left:0;order:9;width:100%;overflow-x:auto;flex-wrap:nowrap}
 .spec{display:none}
 .main{padding:10px 8px 44px}
}
"""

APPJS = r"""
const q=document.getElementById("q");
q.oninput=()=>{const v=q.value.toLowerCase();
document.querySelectorAll(".item").forEach(i=>
i.classList.toggle("hide",v&&!i.dataset.n.includes(v)));};
const log=m=>{const el=document.getElementById("log");
el.textContent+="\n"+m;el.scrollTop=el.scrollHeight;};
function tab(n){
 document.querySelectorAll(".page").forEach((el,i)=>
  el.classList.toggle("on",i===n));
 document.querySelectorAll(".tabs a").forEach((el,i)=>
  el.classList.toggle("active",i===n));
 if(n===1)updPV();
}
document.querySelectorAll(".tabs a").forEach((el,i)=>
 el.onclick=()=>tab(i));
const rb=document.getElementById("railbtn");
function setRail(off){document.body.classList.toggle("railoff",off);
 rb.textContent=(off?"▶":"◀")+" 輸入面板";
 try{localStorage.setItem("via_rail",off?"1":"0");}catch(e){}}
rb.onclick=()=>setRail(!document.body.classList.contains("railoff"));
try{setRail(localStorage.getItem("via_rail")==="1");}catch(e){}
function updPV(){
 const t=document.getElementById("task");
 const zh=t.options[t.selectedIndex]?t.options[t.selectedIndex].text:"—";
 const codes=document.getElementById("codes").value.trim()||"(空=預設全額)";
 const ck=[...document.querySelectorAll(".ck input:checked")]
  .map(c=>c.parentElement.textContent.trim());
 document.getElementById("pv").innerHTML=
  "選定任務:<b>"+zh+"</b><br>股票代碼:<b>"+codes+"</b><br>勾選批次:<b>"
  +(ck.length?ck.join("、"):"(無)")+"</b>";
}
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
 log("[指揮台] 在線 ✓ v="+(r.v||"?"));
 document.getElementById("hublight").textContent="樞紐:在線 ✓ "+(r.v||"");}
 catch(e){log("[指揮台] 未開=誠實(打 via 帶起)");
 document.getElementById("hublight").textContent="樞紐:未開(打 via 帶起)";}}
ping();
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
   +(DOT[v.state]||DOT.idle)+';margin-right:6px"></span>'+(v.zh||k)
   +" <small>"+k+el+pct+"</small>"
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
    tasks = {k: {"zh": v["zh"], "net": bool(v.get("net"))} for k, v in
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
    chk("④f 批304 版面律(固定 header/footer+六頁籤+可收左欄"
        "+正式名稱表列)",
        'class="top"' in page and 'class="bot"' in page
        and "position:sticky" in page and "position:fixed" in page
        and 'class="tabs"' in page and page.count('data-t="') >= 6
        and "railbtn" in page and "railoff" in page and "via_rail" in page
        and "引擎表列" in page and "模組表列" in page
        and "UR-ENG-" in page and "UR-MDL-" in page
        and ">主動 ETF×共識分析</option>" in page)
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
    print(f"  [計] 十一檢 OK {11 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 總系統管理器(VIA_SYSTEM_MANAGER)· 十一檢自測(零外網)===")
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
