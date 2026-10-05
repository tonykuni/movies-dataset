#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL261_UIEngine v0102 — 薄尾:操作台重組。左側固定側欄用矩陣分組導覽;頁面依序是摘要 → 驗證結果 → 明細矩陣。

操作員 2026-10-05(附 VRN v0159 側欄截圖):「USE MATRIX TO GROUP AND REORGANIZE ALL U/I IN THE LEFT PANNEL AND MULTIPLE PAGES
  DISPLAYING SUMMARY OF INPUT ENGINES OUTPUT · THE LAST PAGE IS VERY DETAIL MATRIX RECORDS · MIDDLE PAGES ARE RESULTS VERIFIED ·
  MAKE IT CONSOLIDATED AND SIMPLE. AND WELL ORGANIZED.」
  · 版面照 VRN 視覺鎖 v0159(VIA_VRN_VisualLock_Sidebar_v0159.json):固定左側欄 232px · 側欄獨立捲動 · 不用上方頁籤 · 色票不改;
    首頁只放輸入摘要與一鍵套用,明細不上首頁。
  · 左側欄 = 一張小矩陣(大類 × 輸入 · 輸出 · 驗證,格子是燈,點了跳頁)+ 四組導覽:
      摘要 SUMMARY(01 總覽 · 02 輸入 · 03 引擎 · 04 輸出)· 驗證 VERIFIED(每大類一頁 · DuckDB · 環境)· 記錄 RECORDS(明細矩陣)· 系統 SYSTEMS。
  · 輸入控制全部從側欄搬到「02 輸入」頁,排成矩陣(大類一列:起始日 · 族群勾選 · 成員方塊);仍全滑鼠,沒有文字輸入框。
  · 無資料族群在總覽與驗證頁列出補擷取路線(VDF 擷取冊上的來源:FRED · 政府開放資料 · AkShare);頁面只顯示,不擷取。
  · 匯出格式不變(VIA_UI_Input/1);套用照舊:via_activate_vdf 發現下載夾的匯出就問要不要寫入。
其餘(快照 · 匯入 · 元件矩陣 · DuckDB · 參數疊層 · 自訂範本)全照 v0101 / v0100;預設 file://,不需伺服器(L100)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = int(Path(__file__).stem.rsplit("_v", 1)[1])
    hits = [p for p in HERE.glob("CGC_MDL261_UIEngine_v*.py") if re.search(r"_v\d+$", p.stem) and int(p.stem.rsplit("_v", 1)[1]) < me]
    return max(hits, key=lambda p: int(p.stem.rsplit("_v", 1)[1]))


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR          # v0100 本體:build / inject / BUILTIN 在這裡


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"CGC_MDL261_UIEngine v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
PRIOR.TAG = TAG
BASE.TAG = TAG
_SNAPSHOT_V0101 = BASE.snapshot
BUILTIN_V0101 = PRIOR.BUILTIN_V0101

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------- 快照補充:無資料族群的補擷取路線(只讀冊,不連網) ----------
def _refill_book() -> dict:
    """VDF 族群冊尾版裡每個族群的 refill 分層(MDL012 refill 照這個跑);讀不到 = 空(照實退回族群自己的引擎)。"""
    p = PRIOR._tail(PRIOR.VDF, "VDF_FetchGroups_SSOT_v*.json")
    try:
        book = json.loads(p.read_text(encoding="utf-8")) if p else {}
    except (OSError, ValueError) as exc:
        PRIOR.SKIPPED.append({"file": str(p), "why": f"{type(exc).__name__}: {exc}"})
        book = {}
    return {g.get("id"): g.get("refill") or [] for g in book.get("groups") or []}


def refill_routes(vdf: dict, tiers_by_group: dict | None = None) -> list:
    """無資料(NODATA)或部分無資料的族群 → 冊上的 refill 分層(照順序:提供者 · 引擎 · 要的鑰);冊上沒寫就退族群自己的引擎並註明。"""
    tiers_by_group = _refill_book() if tiers_by_group is None else tiers_by_group
    io_by = {r.get("group"): r for r in (vdf.get("io") or [])}
    eng_by = {e.get("id"): e for e in (vdf.get("engines") or [])}
    out = []
    for g in vdf.get("groups") or []:
        s = g.get("summary") or {}
        states = s.get("states") or {}
        if s.get("worst") != "NODATA" and not states.get("NODATA"):
            continue
        tiers = tiers_by_group.get(g.get("id")) or []
        if tiers:
            engines = [e for t in tiers for e in (t.get("engines") or [])]
            providers = []
            for t in tiers:
                if t.get("provider") and t["provider"] not in providers:
                    providers.append(t["provider"])
            route = " → ".join(f"{i}. {t.get('provider', '')} {','.join(t.get('engines') or [])}" + (f"(要 {t['key']})" if t.get("key") else "")
                               for i, t in enumerate(tiers, 1))
        else:
            engines = list(g.get("engines") or [])
            providers = sorted({str(eng_by.get(e, {}).get("group") or "") for e in engines} - {""})
            route = "冊上沒寫 refill → 族群自己的引擎 " + ",".join(engines)
        out.append({"group": g.get("id"), "zh": g.get("zh"), "category": g.get("category"),
                    "nodata": states.get("NODATA", 0) if s.get("worst") != "NODATA" else (s.get("sources") or len(g.get("rows") or [])),
                    "engines": engines, "sources": providers, "route": route, "tiers": tiers,
                    "input": (io_by.get(g.get("id")) or {}).get("input", ""),
                    "how": "via-vdf-refill(看計畫)→ 本視窗開雙閘後 via-vdf-refill -Apply"})
    return out


def snapshot_v0102(cfg: dict, home):
    snap = _SNAPSHOT_V0101(cfg, home)
    snap["refill"] = refill_routes(snap.get("vdf") or {})
    snap["layout_lock"] = {"source": "VIA_VRN_VisualLock_Sidebar_v0159.json", "state": "VISUAL_LOCKED_SIDEBAR_MULTIPAGE"}
    return snap


BASE.snapshot = snapshot_v0102


# ---------- 內建標準範本(v0102:矩陣側欄 · 多頁) ----------
BUILTIN_V0102 = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--vl-bg:#f5f4f0;--vl-paper:#ffffff;--vl-ink:#1e1d1a;--vl-muted:#6b6860;--vl-line:#dbd9d3;--vl-soft:#ecebe6;--vl-teal:#439a9a;--vl-amber:#c4943a;
 --vl-blue:#4c78a8;--vl-up:#c96b5a;--vl-down:#5a9e6f;--vl-violet:#7a6daa;--vl-accent:#439a9a;--vl-side:232px;--vl-r:6px;--vl-fs:12.5px;
 --vl-mono:ui-monospace,"Cascadia Mono",Consolas,"SFMono-Regular",monospace;--vl-sans:"Noto Sans TC","Microsoft JhengHei","PingFang TC",system-ui,sans-serif}
:root[data-theme=dark]{--vl-bg:#151412;--vl-paper:#1e1d1a;--vl-ink:#ecebe6;--vl-muted:#a3a097;--vl-line:#3a3833;--vl-soft:#2a2925}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--vl-bg:#151412;--vl-paper:#1e1d1a;--vl-ink:#ecebe6;--vl-muted:#a3a097;--vl-line:#3a3833;--vl-soft:#2a2925}}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--vl-bg);color:var(--vl-ink);font:var(--vl-fs)/1.45 var(--vl-sans)}
.app{display:grid;grid-template-columns:var(--vl-side) minmax(0,1fr);height:100vh}
.side{background:var(--vl-paper);border-right:1px solid var(--vl-line);display:flex;flex-direction:column;min-height:0}
.side .scroll{overflow:auto;flex:1;min-height:0}
.spec{height:4px;background:linear-gradient(90deg,var(--vl-teal),var(--vl-blue),var(--vl-violet),var(--vl-amber),var(--vl-up))}
.brand{display:flex;gap:10px;align-items:center;padding:14px 14px 10px;border-bottom:1px solid var(--vl-line)}
.seal{width:34px;height:34px;border:2px solid var(--vl-up);color:var(--vl-up);display:grid;place-items:center;font-weight:700;font-size:18px;border-radius:3px;flex:none}
.brand b{display:block;font-size:15px}.brand small{display:block;color:var(--vl-muted);font-size:11px}
.ver{font:10.5px var(--vl-mono);color:var(--vl-teal);padding:6px 14px 0;letter-spacing:.5px}
.sec{font:10.5px var(--vl-mono);color:var(--vl-muted);letter-spacing:1.2px;padding:14px 14px 4px;text-transform:uppercase}
.mm{margin:2px 10px 0;border:1px solid var(--vl-line);border-radius:var(--vl-r);overflow:hidden}
.mm table{width:100%;border-collapse:collapse;font-size:11px}.mm th{font:10px var(--vl-mono);color:var(--vl-muted);padding:4px 3px;background:var(--vl-soft);text-align:center}
.mm th:first-child{text-align:left;padding-left:7px}.mm td{padding:3px;border-top:1px solid var(--vl-soft);text-align:center}.mm td:first-child{text-align:left;padding-left:7px;white-space:nowrap}
.dot{display:inline-block;width:12px;height:12px;border-radius:50%;cursor:pointer;vertical-align:middle}
.d-GREEN{background:var(--vl-down)}.d-YELLOW{background:var(--vl-amber)}.d-RED{background:var(--vl-up)}.d-NODATA{background:transparent;border:1.5px solid var(--vl-muted)}
.nav a{display:flex;gap:10px;align-items:baseline;margin:1px 8px;padding:7px 8px;border-radius:var(--vl-r);color:var(--vl-ink);text-decoration:none;cursor:pointer}
.nav a:hover{background:var(--vl-soft)}.nav a.on{background:var(--vl-ink);color:var(--vl-paper)}.nav a.on .en,.nav a.on .no{color:var(--vl-soft)}
.nav .no{font:10.5px var(--vl-mono);color:var(--vl-muted);width:16px;flex:none}.nav .t{flex:1;min-width:0}.nav .en{display:block;font:10px var(--vl-mono);color:var(--vl-muted);letter-spacing:.4px}
.nav .cnt{font:10px var(--vl-mono);border-radius:8px;padding:0 6px;background:var(--vl-soft);color:var(--vl-ink)}.nav a.absent{opacity:.45;cursor:default}
.foot{border-top:1px solid var(--vl-line);display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;padding:10px 14px}
.foot div{font:10px var(--vl-mono);color:var(--vl-muted);letter-spacing:.8px}.foot b{display:block;font:600 12px var(--vl-mono);color:var(--vl-ink)}
.main{overflow:auto;min-width:0}
.hd{display:flex;justify-content:space-between;gap:16px;padding:16px 26px 14px;border-bottom:1px solid var(--vl-line);background:var(--vl-bg);position:sticky;top:0;z-index:2;flex-wrap:wrap}
.crumb{font:10.5px var(--vl-mono);color:var(--vl-teal);letter-spacing:1px}.hd h1{margin:4px 0 2px;font-size:21px}.hd h1 small{font-size:12px;color:var(--vl-muted);font-weight:400;margin-left:8px}
.hd .sub{color:var(--vl-muted)}.meta{display:flex;gap:18px}.meta div{font:10px var(--vl-mono);color:var(--vl-muted);letter-spacing:.8px}.meta b{display:block;font:600 13px var(--vl-mono);color:var(--vl-ink);margin-top:4px}
.pg{display:none;padding:18px 26px 40px;max-width:1240px}.pg.on{display:block}
.hero{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.hc{background:var(--vl-paper);border:1px solid var(--vl-line);border-radius:var(--vl-r);padding:14px}
.hc b{display:block;font:600 20px var(--vl-mono);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hc b .b{font-size:13px;padding:2px 10px}.hc span{font:10px var(--vl-mono);color:var(--vl-muted);letter-spacing:.8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,460px),1fr));gap:14px}
.card{background:var(--vl-paper);border:1px solid var(--vl-line);border-radius:var(--vl-r);padding:14px 16px;min-width:0}
.card h4{margin:0 0 10px;font-size:14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}.card h4 small{font-size:11px;color:var(--vl-muted);font-weight:400}
.card .sc{max-height:460px;overflow:auto}.wide{grid-column:1/-1}
table{border-collapse:collapse;width:100%}th,td{padding:5px 6px;border-bottom:1px solid var(--vl-soft);text-align:left;vertical-align:top;word-break:break-word}
th{font:10px var(--vl-mono);color:var(--vl-muted);letter-spacing:.6px;position:sticky;top:0;background:var(--vl-paper);font-weight:500}td.n{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--vl-mono)}
tr.go{cursor:pointer}tr.go:hover td{background:var(--vl-soft)}
.b{display:inline-block;padding:0 7px;border-radius:9px;font:10.5px var(--vl-mono);white-space:nowrap;border:1px solid transparent}
.b-OK,.b-GREEN{background:color-mix(in srgb,var(--vl-down) 16%,transparent);color:var(--vl-down)}
.b-YELLOW,.b-LOCKED,.b-RUNNING{background:color-mix(in srgb,var(--vl-amber) 18%,transparent);color:var(--vl-amber)}
.b-RED,.b-ERR{background:color-mix(in srgb,var(--vl-up) 16%,transparent);color:var(--vl-up)}.b-NODATA,.b-NODATE{border-color:var(--vl-line);color:var(--vl-muted)}
.mut{color:var(--vl-muted)}pre{white-space:pre-wrap;margin:0;font:10.5px/1.4 var(--vl-mono)}
.d .card{padding:10px 12px}.d table{font-size:11px}.d td,.d th{padding:2px 4px}
select{padding:4px 6px;border:1px solid var(--vl-line);border-radius:var(--vl-r);background:var(--vl-paper);color:var(--vl-ink);font:inherit;max-width:100%}
.drop{border:1.5px dashed var(--vl-line);border-radius:var(--vl-r);padding:8px;text-align:center;color:var(--vl-muted);font-size:11px;margin-top:6px}
.drop.on{border-color:var(--vl-accent);color:var(--vl-accent)}
.chk{display:inline-flex;align-items:center;gap:5px;margin:2px 10px 2px 0;cursor:pointer;white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:4px;margin:4px 0}.chip{border:1px solid var(--vl-line);border-radius:10px;padding:1px 8px;font:11px var(--vl-mono);cursor:pointer;user-select:none}
.chip.on{background:color-mix(in srgb,var(--vl-accent) 16%,transparent);border-color:var(--vl-accent)}
.btn{background:var(--vl-ink);color:var(--vl-paper);border:0;border-radius:var(--vl-r);padding:9px 14px;font:inherit;cursor:pointer;margin:0 6px 6px 0}
.btn.o{background:none;color:var(--vl-ink);border:1px solid var(--vl-line)}
.sw{display:inline-block;width:18px;height:18px;border-radius:4px;margin:2px;cursor:pointer;border:1px solid var(--vl-line)}
.kv{display:grid;grid-template-columns:110px 1fr;gap:6px 12px;font-size:12px}.kv span{font:10px var(--vl-mono);color:var(--vl-muted);letter-spacing:.6px;padding-top:2px}
svg.wf .bx{fill:var(--vl-paper);stroke:var(--vl-teal)}svg.wf text{fill:var(--vl-ink);font-size:11px}svg.wf line{stroke:var(--vl-muted)}
@media (max-width:760px){.app{grid-template-columns:194px minmax(0,1fr)}.pg,.hd{padding-left:14px;padding-right:14px}.meta{display:none}}
</style></head>
<body><div class="app"><aside class="side"><div class="spec"></div><div class="scroll" id="side"></div><div class="foot" id="foot"></div></aside>
<main class="main" id="main"><div class="hd" id="hd"></div><div id="pages"></div></main></div>
<script>
(function(){
var S=window.VIA||{},C=window.VIA_CONFIG||{},V=S.vdf||{},$=function(s){return document.querySelector(s)},$$=function(s){return Array.prototype.slice.call(document.querySelectorAll(s))};
var esc=function(v){return v===null||v===undefined?'':String(v).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};
var B=function(s){return '<span class="b b-'+esc(s)+'">'+esc(s)+'</span>'},N=function(v){return v===null||v===undefined||v===''?'':Number(v).toLocaleString()};
var KEY='via.ui.engine.v0102',st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}var save=function(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}};
function T(rows,cols,go){if(!rows||!rows.length)return '<div class="mut">(無資料)</div>';var h='<table><tr>'+cols.map(function(c){return '<th>'+esc(c[1])+'</th>'}).join('')+'</tr>';
 rows.forEach(function(r){h+='<tr'+(go&&r[go]?' class="go" data-go="'+esc(r[go])+'"':'')+'>'+cols.map(function(c){var v=r[c[0]];return c[2]==='b'?'<td>'+B(v)+'</td>':c[2]==='n'?'<td class="n">'+N(v)+'</td>':c[2]==='h'?'<td>'+(v||'')+'</td>':'<td>'+esc(Array.isArray(v)?v.join(' · '):v)+'</td>'}).join('')+'</tr>'});return h+'</table>'}
var RANK={RED:3,YELLOW:2,NODATA:1,GREEN:0},worst=function(a){var w='GREEN';a.forEach(function(x){if((RANK[x]||0)>(RANK[w]||0))w=x});return a.length?w:'NODATA'};
var G={};(V.groups||[]).forEach(function(g){G[g.id]=g});var CATS=V.categories||[],LOC=S.locations||{system:[],db:[],selected:{}},D=S.duckdb||{dbs:[]},E=S.env||{},RF=S.refill||[];
st.loc=st.loc||{};st.start=st.start||{};st.mem=st.mem||{};st.run=st.run||(S.run_groups&&S.run_groups.length?S.run_groups:Object.keys(G));
CATS.forEach(function(c){if(!st.start[c.id])st.start[c.id]=c.start});
['TW_FIN','INTL_FIN'].forEach(function(k){if(G[k]&&!st.mem[k])st.mem[k]=(G[k].members||[]).slice()});
// ---- 每大類的三個燈:輸入(有勾族群)· 輸出(有列)· 驗證(最差燈)----
var CS={};CATS.forEach(function(c){var gs=c.groups.map(function(id){return G[id]}).filter(Boolean),lamps=gs.map(function(g){return (g.summary||{}).worst||'NODATA'}),cnt={GREEN:0,YELLOW:0,RED:0,NODATA:0},rows=0,mx='';
 lamps.forEach(function(l){cnt[l]=(cnt[l]||0)+1});gs.forEach(function(g){var s=g.summary||{};rows+=s.rows_asof||0;if((s.max_date||'')>mx)mx=s.max_date||''});
 var engs={};gs.forEach(function(g){(g.engines||[]).forEach(function(e){engs[e]=1})});
 CS[c.id]={gs:gs,cnt:cnt,rows:rows,max:mx,engines:Object.keys(engs),verify:worst(lamps),output:rows>0?(cnt.NODATA?'YELLOW':'GREEN'):'NODATA'}});
function inLamp(c){var on=c.groups.filter(function(g){return st.run.indexOf(g)>=0}).length;return on===c.groups.length?'GREEN':on?'YELLOW':'NODATA'}
var short=function(c){return String(c.zh||c.id).split(/[ ·(]/)[0]};
// ---- 頁表(四組)----
var P=[['sum','總覽','OVERVIEW','摘要','輸入 · 引擎 · 輸出 一頁看完'],['inp','輸入','INPUT','摘要','全滑鼠:位置 · 大類起始日 · 族群 · 成員'],['eng','引擎','ENGINES','摘要','擷取引擎 · 工具 · 功能'],['out','輸出','OUTPUT','摘要','執行紀錄 · 各族群產出']];
CATS.forEach(function(c){P.push(['v_'+c.id,short(c),'VERIFIED · '+c.id,'驗證',c.zh])});
P.push(['vdb','DuckDB','DATABASE','驗證','資料庫 · 表 · 列 · 日期範圍']);P.push(['venv','環境','ENVIRONMENT','驗證','照測過的版本(LKGC)· 工具']);
P.push(['rec','明細矩陣','DETAIL RECORDS','記錄','流程 · 元件註冊 · 參數 · regex · 同義字 · 編號 · SSOT']);
var GRP=[['摘要','SUMMARY'],['驗證','VERIFIED'],['記錄','RECORDS']];
var nodata=RF.length,allL=[];CATS.forEach(function(c){allL.push(CS[c.id].verify)});var W=worst(allL);
function cntFor(id){if(id.indexOf('v_')===0){var k=CS[id.slice(2)];return k?(k.cnt.GREEN+k.cnt.YELLOW)+'/'+k.gs.length:''}if(id==='sum')return nodata?nodata+' 缺':'';if(id==='vdb')return D.n_tables||'0';return ''}
// ---- 側欄 ----
var h='<div class="brand"><div class="seal">觀</div><div><b>中央治理控制台</b><small>VIA Central Governance Console</small></div></div><div class="ver">+ VCGC + VDF · '+esc((S.tool||'').replace('CGC_MDL261_UIEngine ',''))+'</div>';
h+='<div class="sec">矩陣 MATRIX</div><div class="mm"><table><tr><th>大類</th><th>輸入</th><th>輸出</th><th>驗證</th></tr>'
 +CATS.map(function(c){var k=CS[c.id];return '<tr><td title="'+esc(c.zh)+'">'+esc(short(c))+'</td><td><span class="dot d-'+inLamp(c)+'" data-go="inp" title="輸入"></span></td><td><span class="dot d-'+k.output+'" data-go="out" title="輸出 '+N(k.rows)+' 列"></span></td><td><span class="dot d-'+k.verify+'" data-go="v_'+c.id+'" title="驗證 '+k.verify+'"></span></td></tr>'}).join('')+'</table></div>';
var no=0;GRP.forEach(function(g){h+='<div class="sec">'+g[0]+' '+g[1]+'</div><div class="nav">';P.forEach(function(p){if(p[3]!==g[0])return;no++;var n=cntFor(p[0]);
 h+='<a data-go="'+p[0]+'"><span class="no">'+(no<10?'0':'')+no+'</span><span class="t">'+esc(p[1])+'<span class="en">'+esc(p[2])+'</span></span>'+(n!==''?'<span class="cnt">'+esc(n)+'</span>':'')+'</a>'});h+='</div>'});
h+='<div class="sec">系統 SYSTEMS</div><div class="nav">'+((S.nav||{}).parent||[]).concat((S.nav||{}).systems||[]).map(function(x){return x.exists?'<a href="'+esc(x.href)+'"><span class="no">↗</span><span class="t">'+esc(x.label)+'</span></a>':'<a class="absent"><span class="no">·</span><span class="t">'+esc(x.label)+'<span class="en">ABSENT</span></span></a>'}).join('')+'</div>';
$('#side').innerHTML=h;
$('#foot').innerHTML='<div>STATE<b>'+esc(W)+'</b></div><div>AS-OF<b>'+esc(V.as_of||'—')+'</b></div><div>NODATA<b>'+nodata+'</b></div><div>LKGC<b>'+esc(E.lkgc||'—')+'</b></div>';
$('#pages').innerHTML=P.map(function(p){return '<section class="pg" id="'+p[0]+'"></section>'}).join('');
// ---- 輸入匯出(格式不變:VIA_UI_Input/1)----
function input(){var cats={};CATS.forEach(function(c){cats[c.id]={start:st.start[c.id]}});var mem={};Object.keys(st.mem).forEach(function(k){mem[k]=st.mem[k]});
 return {schema:S.input_schema||'VIA_UI_Input/1',exported_at:new Date().toISOString(),from:S.tool,locations:{system_root:st.loc.system_root||LOC.selected.system_root,db_root:st.loc.db_root||LOC.selected.db_root},
  run_groups:st.run,active_template:st.tpl||null,theme:{primary_color:st.pc||(C.theme||{}).primary_color,font_size:st.fs||(C.theme||{}).font_size,mode:st.mode||(C.theme||{}).mode||'auto'},
  vdf:{categories:cats,members:mem,as_of:st.asof||V.asof_setting||'latest'}}}
function changes(){var I=input(),n=0,L=[];CATS.forEach(function(c){if(I.vdf.categories[c.id].start!==c.start){n++;L.push(short(c)+' 起始 '+c.start+' → '+I.vdf.categories[c.id].start)}});
 ['TW_FIN','INTL_FIN'].forEach(function(k){if(!G[k])return;var a=(G[k].members||[]).join(','),b=(I.vdf.members[k]||[]).join(',');if(a!==b){n++;L.push(k+' 成員 '+a+' → '+b)}});return L}
// ---- 01 總覽 ----
var tg=(V.groups||[]).length,ok=0;(V.groups||[]).forEach(function(g){var w=(g.summary||{}).worst;if(w==='GREEN'||w==='YELLOW')ok++});
var sumRows=CATS.map(function(c){var k=CS[c.id],sel=0;['TW_FIN','INTL_FIN'].forEach(function(m){if(c.groups.indexOf(m)>=0)sel+=(st.mem[m]||[]).length});
 return {go:'v_'+c.id,cat:c.zh,start:st.start[c.id],inp:c.groups.filter(function(g){return st.run.indexOf(g)>=0}).length+'/'+c.groups.length+' 族群'+(sel?' · '+sel+' 成員':''),
  eng:k.engines.length+' 支',rows:k.rows,max:k.max||'—',ver:'<span class="b b-GREEN">'+k.cnt.GREEN+'</span> <span class="b b-YELLOW">'+k.cnt.YELLOW+'</span> <span class="b b-RED">'+k.cnt.RED+'</span> <span class="b b-NODATA">'+k.cnt.NODATA+'</span>',w:k.verify}});
function act(){return '<div class="card"><h4>套用與啟動 <small>One-click Apply</small></h4><button class="btn" id="b_exp">匯出輸入</button><button class="btn o" id="b_cmd">複製啟動指令</button><button class="btn o" id="b_rst">還原預設</button>'
 +'<div class="kv" style="margin-top:8px"><span>待寫改動</span><div id="chg"></div><span>流程</span><div>匯出 → 下載夾 VIA_UI_Input.json → PowerShell 跑 <b>via_activate_vdf</b> → 問 Y 就寫入 → 重產並開這頁</div></div><div class="mut" id="msg"></div></div>'}
function showChg(){var L=changes(),el=document.getElementById('chg');if(el)el.innerHTML=L.length?L.map(esc).join('<br>'):'<span class="mut">沒有(照現況)</span>'}
$('#sum').innerHTML='<div class="hero"><div class="hc"><b>'+B(W)+'</b><span>總燈 STATE</span></div><div class="hc"><b>'+ok+'/'+tg+'</b><span>有資料族群 GROUPS</span></div>'
 +'<div class="hc"><b>'+nodata+'</b><span>無資料 NODATA</span></div><div class="hc"><b>'+N((D.n_tables||0))+'</b><span>DuckDB 表 TABLES</span></div>'
 +'<div class="hc"><b>'+esc(V.as_of||'—')+'</b><span>同一天 AS-OF</span></div><div class="hc"><b>'+B(E.lkgc||'NODATA')+'</b><span>環境 LKGC</span></div></div>'
 +'<div class="grid"><div class="card wide"><h4>摘要矩陣 <small>大類 × 輸入 · 引擎 · 輸出 · 驗證(點列看驗證頁)</small></h4><div class="sc">'
 +T(sumRows,[['cat','大類'],['start','起始日'],['inp','輸入'],['eng','引擎'],['rows','輸出列','n'],['max','最晚'],['ver','驗證 綠/黃/紅/無','h'],['w','燈','b']],'go')+'</div></div>'
 +act()+'<div class="card"><h4>無資料 · 補擷取路線 <small>冊上的來源;擷取在工作站跑</small></h4><div class="sc">'
 +T(RF.map(function(r){return {go:'v_'+r.category,g:r.zh,s:r.route,n:r.nodata}}),[['g','族群'],['s','補擷取分層(照順序)'],['n','缺','n']],'go')+'</div></div></div>';
// ---- 02 輸入(矩陣表單)----
function opt(list,sel,lab){return list.map(function(x){var v=typeof x==='string'?x:x.path;return '<option value="'+esc(v)+'"'+(v===sel?' selected':'')+'>'+esc(lab?lab(x):v)+'</option>'}).join('')}
var lb=function(x){return x.name+' · '+x.why+' — '+x.path};
var ih='<div class="grid"><div class="card"><h4>系統存放位置 <small>VCGC</small></h4><select id="l_sys" style="width:100%">'+opt(LOC.system,st.loc.system_root||LOC.selected.system_root,lb)+'</select><div class="drop" id="d_sys">把資料夾拖進來(Windows 檔案總管)</div></div>'
 +'<div class="card"><h4>資料庫位置 <small>VCGC</small></h4><select id="l_db" style="width:100%">'+opt(LOC.db,st.loc.db_root||LOC.selected.db_root,lb)+'</select><div class="drop" id="d_db">把 .duckdb 檔或資料夾拖進來</div></div>'
 +'<div class="card wide"><h4>大類矩陣 <small>起始日只能按大類改 · 打勾 = 這次要跑的族群 · 方塊 = 財報成員</small></h4><div class="sc"><table><tr><th>大類</th><th>起始日</th><th>族群</th><th>成員</th></tr>';
CATS.forEach(function(c){var ds=(S.date_options||[]).slice();if(ds.indexOf(c.default_start)<0)ds.push(c.default_start);if(ds.indexOf(c.start)<0)ds.push(c.start);ds.sort();
 ih+='<tr><td><b>'+esc(short(c))+'</b><div class="mut">'+esc(c.note||c.zh)+'</div></td><td><select class="c_start" data-c="'+c.id+'">'+ds.map(function(d){return '<option value="'+d+'"'+(d===st.start[c.id]?' selected':'')+'>'+d+(d===c.default_start?'(預設)':'')+'</option>'}).join('')+'</select></td><td>';
 c.groups.forEach(function(gid){var g=G[gid]||{};ih+='<label class="chk"><input type="checkbox" class="c_run" value="'+gid+'"'+(st.run.indexOf(gid)>=0?' checked':'')+'>'+(g.membership==='FIXED_ALL'?'🔒 ':'')+esc(g.zh||gid)+'</label>'});
 ih+='</td><td>';c.groups.forEach(function(gid){if(gid!=='TW_FIN'&&gid!=='INTL_FIN')return;var pool=gid==='TW_FIN'?((S.members_pick||{}).TW||[]):((S.members_pick||{}).INTL||[]);
  ih+='<div><span class="mut">'+esc((G[gid]||{}).zh||gid)+'</span><div class="chips" id="ch_'+gid+'"></div><select class="m_add" data-g="'+gid+'"><option value="">+ 加入(下拉選)</option>'+pool.map(function(m){return '<option value="'+esc(m.code)+'">'+esc(m.code+' '+(m.name||''))+'</option>'}).join('')+'</select></div>'});
 ih+='</td></tr>'});
ih+='</table></div></div><div class="card"><h4>as-of <small>全族群同一天</small></h4><select id="asof">'+(S.asof_options||['latest']).map(function(d){return '<option'+(d===(st.asof||(V.asof_setting||'latest'))?' selected':'')+'>'+d+'</option>'}).join('')+'</select></div>'
 +'<div class="card"><h4>外觀 <small>範本 · 強調色 · 字級 · 主題</small></h4><select id="tpl"><option value="">內建標準範本</option>'+(S.templates||[]).map(function(t){return '<option'+(t===(st.tpl||C.active_template)?' selected':'')+'>'+esc(t)+'</option>'}).join('')+'</select> '
 +['#439a9a','#4c78a8','#7a6daa','#c4943a','#c96b5a','#1e1d1a'].map(function(c){return '<span class="sw" data-c="'+c+'" style="background:'+c+'"></span>'}).join('')
 +' <select id="fs"><option value="11.5px">字級 小</option><option value="12.5px">字級 中</option><option value="14px">字級 大</option></select> <select id="mode"><option value="auto">主題 跟系統</option><option value="light">淺色</option><option value="dark">深色</option></select></div>'
 +act().replace('id="b_exp"','id="b_exp2"').replace('id="b_cmd"','id="b_cmd2"').replace('id="b_rst"','id="b_rst2"').replace('id="chg"','id="chg2"').replace('id="msg"','id="msg2"')
 +'<div class="card wide"><h4>輸入摘要去重矩陣 <small>同值多處 = 次數 &gt; 1</small></h4><div class="sc" id="m_in"></div></div></div>';
$('#inp').innerHTML=ih;
function chips(){['TW_FIN','INTL_FIN'].forEach(function(k){var el=document.getElementById('ch_'+k);if(!el)return;var d=(G[k]||{}).default_members||[];
 var all=(st.mem[k]||[]).concat(d.filter(function(x){return (st.mem[k]||[]).indexOf(x)<0}));
 el.innerHTML=all.map(function(x){return '<span class="chip'+((st.mem[k]||[]).indexOf(x)>=0?' on':'')+'" data-g="'+k+'" data-v="'+esc(x)+'">'+esc(x)+(d.indexOf(x)>=0?' ★':'')+'</span>'}).join('')||'<span class="mut">(無)</span>';
 $$('#ch_'+k+' .chip').forEach(function(c){c.onclick=function(){var a=st.mem[k],v=c.dataset.v,i=a.indexOf(v);if(i>=0)a.splice(i,1);else a.push(v);save();chips();refresh()}})})}
function mx1(){var I=input(),rows=[],seen={};
 function add(item,cat,val,where,src){var k=item+'|'+val;if(seen[k]){seen[k].where.push(where);seen[k].dup++;return}seen[k]={item:item,cat:cat,val:val,where:[where],dup:1,src:src};rows.push(seen[k])}
 add('系統存放位置','VCGC',I.locations.system_root,'VCGC','下拉 / 拖放');add('資料庫位置','VCGC',I.locations.db_root,'VCGC','下拉 / 拖放');add('as-of','全族群',I.vdf.as_of,'全部','下拉');
 CATS.forEach(function(c){add('起始日','大類',I.vdf.categories[c.id].start,short(c),'下拉(只按大類)')});
 I.run_groups.forEach(function(g){add('勾選族群','族群',g,((G[g]||{}).category)||'','打勾')});
 Object.keys(I.vdf.members).forEach(function(k){I.vdf.members[k].forEach(function(m){add('成員',k,m,(G[k]||{}).zh||k,'方塊 / 下拉')})});
 rows.forEach(function(r){r.where=r.where.join(' · ')});
 $('#m_in').innerHTML='<div class="mut">'+rows.length+' 項(去重後)</div>'+T(rows,[['item','輸入'],['cat','類'],['val','值'],['where','出現在'],['dup','次','n'],['src','來源']])}
function refresh(){mx1();showChg();var e=document.getElementById('chg2');if(e)e.innerHTML=document.getElementById('chg').innerHTML}
chips();
$$('.c_start').forEach(function(s){s.onchange=function(){st.start[s.dataset.c]=s.value;save();refresh()}});
$$('.c_run').forEach(function(s){s.onchange=function(){st.run=$$('.c_run').filter(function(x){return x.checked}).map(function(x){return x.value});save();refresh()}});
$$('.m_add').forEach(function(s){s.onchange=function(){if(!s.value)return;var a=st.mem[s.dataset.g];if(a.indexOf(s.value)<0)a.push(s.value);s.value='';save();chips();refresh()}});
$('#l_sys').onchange=function(){st.loc.system_root=this.value;save();refresh()};$('#l_db').onchange=function(){st.loc.db_root=this.value;save();refresh()};
$('#asof').onchange=function(){st.asof=this.value;save();refresh()};$('#tpl').onchange=function(){st.tpl=this.value;save()};
var R=document.documentElement;function look(){if(st.pc)R.style.setProperty('--vl-accent',st.pc);if(st.fs)R.style.setProperty('--vl-fs',st.fs);if(st.mode&&st.mode!=='auto')R.setAttribute('data-theme',st.mode);else R.removeAttribute('data-theme')}
$$('.sw').forEach(function(s){s.onclick=function(){st.pc=s.dataset.c;save();look()}});$('#fs').value=st.fs||'12.5px';$('#fs').onchange=function(){st.fs=this.value;save();look()};
$('#mode').value=st.mode||((C.theme||{}).mode)||'auto';$('#mode').onchange=function(){st.mode=this.value;save();look()};look();
function dropz(id,list,key){var d=$(id);['dragenter','dragover'].forEach(function(e){d.addEventListener(e,function(ev){ev.preventDefault();d.classList.add('on')})});
 d.addEventListener('dragleave',function(){d.classList.remove('on')});
 d.addEventListener('drop',function(ev){ev.preventDefault();d.classList.remove('on');var f=ev.dataTransfer.files&&ev.dataTransfer.files[0];if(!f){return}
  var nm=f.name,hit=null;(list||[]).forEach(function(x){if(!hit&&(x.name===nm||x.path.split(/[\\/]/).pop()===nm))hit=x});
  if(!hit&&key==='db_root'){(D.dbs||[]).forEach(function(db){if(!hit&&db.name===nm){var p=db.db.replace(/[\\/][^\\/]+$/,'');hit={path:p,name:p.split(/[\\/]/).pop()}}})}
  if(hit){st.loc[key]=hit.path;save();(key==='system_root'?$('#l_sys'):$('#l_db')).value=hit.path;d.textContent='對到:'+hit.path;refresh()}
  else d.textContent='「'+nm+'」沒對到候選(瀏覽器不給完整路徑)→ 用下拉'})}
dropz('#d_sys',LOC.system,'system_root');dropz('#d_db',LOC.db,'db_root');
function say(t){['msg','msg2'].forEach(function(i){var e=document.getElementById(i);if(e)e.textContent=t})}
function exp(){var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(input(),null,1)],{type:'application/json'}));a.download='VIA_UI_Input.json';a.click();say('已下載 VIA_UI_Input.json → PowerShell 跑 via_activate_vdf,問到就按 Y')}
function cmd(){var t='via_activate_vdf';if(navigator.clipboard)navigator.clipboard.writeText(t);say('已複製:'+t+'(PowerShell 視窗按右鍵貼上)')}
function rst(){st={};save();location.reload()}
['b_exp','b_exp2'].forEach(function(i){$('#'+i).onclick=exp});['b_cmd','b_cmd2'].forEach(function(i){$('#'+i).onclick=cmd});['b_rst','b_rst2'].forEach(function(i){$('#'+i).onclick=rst});
refresh();
// ---- 03 引擎 ----
var eng=(V.engines||[]).map(function(e){return {c:e.id,k:'擷取引擎',g:e.group,v:(e.file||'').split('/').pop(),a:e.role,s:e.state}});
$('#eng').innerHTML='<div class="grid"><div class="card wide"><h4>擷取引擎 <small>'+eng.length+' 支 · 來源 · 檔 · 最近燈</small></h4><div class="sc">'+T(eng,[['c','代碼'],['g','來源'],['v','檔'],['a','做什麼'],['s','燈','b']])+'</div></div>'
 +'<div class="card"><h4>工具</h4><div class="sc">'+T(S.tools,[['tool','工具'],['kind','類'],['version','版本'],['state','燈','b'],['note','註']])+'</div></div>'
 +'<div class="card"><h4>功能</h4><div class="sc">'+T(S.functions,[['module','模組'],['verbs','動詞'],['what','做什麼']])+'</div></div></div>';
// ---- 04 輸出 ----
var runs=[];(V.fg_runs||[]).forEach(function(r){runs.push({w:'族群執行',id:r.run_id,r:'',m:r.as_of,s:'GREEN',n:r.groups+' · '+r.rc})});
(V.vake_runs||[]).forEach(function(r){runs.push({w:'AkShare 執行',id:r.run_id,r:r.rows_new,m:r.finished,s:(r.fail?'YELLOW':'GREEN'),n:'ok '+r.ok+' / fail '+r.fail})});
var gout=(V.groups||[]).map(function(g){var s=g.summary||{};return {go:'v_'+g.category,g:g.zh,c:g.category,r:s.rows_asof,m:s.max_date,s:s.worst||'NODATA'}});
$('#out').innerHTML='<div class="grid"><div class="card wide"><h4>各族群產出 <small>點列看驗證頁</small></h4><div class="sc">'+T(gout,[['g','族群'],['c','大類'],['r','列(≤as-of)','n'],['m','最晚'],['s','燈','b']],'go')+'</div></div>'
 +'<div class="card"><h4>執行紀錄</h4><div class="sc">'+T(runs,[['w','類'],['id','代碼'],['r','新列','n'],['m','時間'],['s','燈','b'],['n','註']])+'</div></div>'
 +'<div class="card"><h4>Live log</h4><pre class="sc">'+esc(((V.live||{}).lines||[]).slice(-40).join('\n')||'(無日誌)')+'</pre></div></div>';
// ---- 驗證頁(每大類)----
CATS.forEach(function(c){var k=CS[c.id],html='<div class="hero"><div class="hc"><b>'+B(k.verify)+'</b><span>驗證 VERIFIED</span></div><div class="hc"><b>'+k.cnt.GREEN+'</b><span>綠 GREEN</span></div><div class="hc"><b>'+k.cnt.YELLOW+'</b><span>黃 YELLOW</span></div>'
 +'<div class="hc"><b>'+k.cnt.RED+'</b><span>紅 RED</span></div><div class="hc"><b>'+k.cnt.NODATA+'</b><span>無資料 NODATA</span></div><div class="hc"><b>'+N(k.rows)+'</b><span>列 ROWS · 起始 '+esc(c.start)+'</span></div></div><div class="grid">';
 k.gs.forEach(function(g){var s=g.summary||{},rf=RF.filter(function(r){return r.group===g.id})[0];
  html+='<div class="card"><h4>'+esc(g.zh)+' '+B(s.worst||'NODATA')+' <small>'+esc(g.membership)+(g.n===null||g.n===undefined?' · 全部':' · '+g.n+' 個')+' · 最晚 '+esc(s.max_date||'—')+'</small></h4>'
   +(rf?'<div class="mut" style="margin-bottom:6px">補擷取:'+esc(rf.route||'')+'</div>':'')
   +'<div class="sc">'+T(g.rows,[['table_name','表 / 函式'],['rows_asof','≤as-of','n'],['min_date','最早'],['max_date','最晚'],['lag_days','落後','n'],['state','燈','b'],['note','註']])+'</div></div>'});
 $('#v_'+c.id).innerHTML=html+'</div>'});
$('#vdb').innerHTML='<div class="hero"><div class="hc"><b>'+N(D.n_dbs||0)+'</b><span>庫 DBS</span></div><div class="hc"><b>'+N(D.n_tables||0)+'</b><span>表 TABLES</span></div><div class="hc"><b>'+N(D.rows||0)+'</b><span>列 ROWS</span></div><div class="hc"><b>'+B(D.locked?'LOCKED':(D.n_dbs?'OK':'NODATA'))+'</b><span>狀態</span></div></div><div class="grid">'
 +((D.dbs||[]).map(function(d){return '<div class="card"><h4>'+esc(d.name)+' '+B(d.state)+' <small>'+esc(d.mb)+' MB · '+d.tables.length+' 表</small></h4><div class="sc">'
 +T(d.tables.map(function(t){return {t:t.table,k:t.kind,r:t.rows!==null?t.rows:t.est_rows,c:t.columns.length,d:t.date_col?(t.min_date+' → '+t.max_date):''}}),[['t','表'],['k','類'],['r','列','n'],['c','欄','n'],['d','日期']])+'</div></div>'}).join('')||'<div class="card mut">(資料庫位置沒有 .duckdb;到 02 輸入選資料庫位置)</div>')+'</div>';
$('#venv').innerHTML='<div class="grid"><div class="card"><h4>照測過的版本(LKGC)</h4>'+T([E],[['lkgc','判定','b'],['eligible','可用'],['ts','時間'],['path','檔']])+'</div><div class="card"><h4>工具</h4><div class="sc">'+T(S.tools,[['tool','工具'],['version','版本'],['state','燈','b'],['note','註']])+'</div></div></div>';
// ---- 明細矩陣(最後一頁,小字)----
var wf=(V.workflow||{}),steps=(wf.steps||[]).map(function(s){return {c:s.code,n:s.name,e:s.engine,v:s.verb,ev:s.evidence}});
var order=String((wf.plan||{}).order||'').split('→').map(function(x){return x.trim()}).filter(Boolean);
var svg='<svg class="wf" viewBox="0 0 '+Math.max(600,order.length*150)+' 56" width="100%">'+order.map(function(o,i){var x=6+i*150;return '<rect class="bx" x="'+x+'" y="8" width="132" height="34" rx="6"/><text x="'+(x+66)+'" y="30" text-anchor="middle">'+esc(o.slice(0,20))+'</text>'+(i?'<line x1="'+(x-18)+'" y1="25" x2="'+(x-2)+'" y2="25"/>':'')}).join('')+'</svg>';
$('#rec').innerHTML='<div class="d"><div class="card wide" style="margin-bottom:12px"><h4>流程 workflow chart · '+esc(wf.code||'')+' '+esc(wf.name||'')+'</h4>'+svg+'</div><div class="grid">'
 +'<div class="card"><h4>工作流步驟</h4><div class="sc">'+T(steps,[['c','代碼'],['n','步'],['e','正主'],['v','動詞'],['ev','證據']])+'</div></div>'
 +'<div class="card"><h4>元件 · 註冊 · 版本鎖</h4><div class="sc">'+T(S.components,[['component','元件'],['kind','類'],['version','版'],['sha12','sha256'],['number','編號'],['registry','註冊碼'],['lock','鎖'],['state','燈','b']])+'</div></div>'
 +'<div class="card"><h4>輸入輸出參數邏輯</h4><div class="sc">'+T(V.io,[['group','族群'],['membership','名單'],['input','輸入'],['engines','引擎'],['asof_args','日期參數'],['output','輸出'],['cadence','頻率']])+'</div></div>'
 +'<div class="card"><h4>無資料 · 補擷取路線</h4><div class="sc">'+T(RF,[['group','族群'],['category','大類'],['route','分層(照順序)'],['sources','提供者'],['input','輸入'],['how','怎麼補']])+'</div></div>'
 +'<div class="card"><h4>regex</h4><div class="sc">'+T(V.regex,[['scope','範圍'],['name','名'],['pattern','式'],['use','用途']])+'</div></div>'
 +'<div class="card"><h4>同義字</h4><div class="sc">'+T(V.synonyms,[['key','鍵'],['canonical','正典'],['aliases','同義字']])+'</div></div>'
 +'<div class="card"><h4>編號</h4><div class="sc">'+T(V.numbering,[['code','編號'],['kind','類'],['name','名'],['version','版']])+'</div></div>'
 +'<div class="card"><h4>SSOT 冊</h4><div class="sc">'+T(V.ssot,[['book','冊'],['version','版'],['sha12','sha'],['mtime','時間'],['state','狀態']])+'</div></div>'
 +'<div class="card"><h4>大類起始日規則</h4><div>'+esc(V.start_rule||'')+'</div>'+T(CATS,[['id','大類'],['zh','名稱'],['start','目前起始日'],['default_start','預設'],['groups','族群']])+'</div>'
 +'<div class="card wide"><h4>有效參數 <small>疊層 '+esc((S.config_layers||[]).join(' ← '))+'</small></h4><pre class="sc">'+esc(JSON.stringify(C,null,1))+'</pre></div></div></div>';
// ---- 換頁 ----
function show(id){if(!document.getElementById(id))id='sum';var p=P.filter(function(x){return x[0]===id})[0]||P[0];$$('.pg').forEach(function(x){x.classList.toggle('on',x.id===id)});
 $$('.nav a[data-go]').forEach(function(a){a.classList.toggle('on',a.dataset.go===id)});
 $('#hd').innerHTML='<div><div class="crumb">VCGC → VDF → '+esc(p[3])+' · '+esc(p[2])+' · VISUAL LOCK</div><h1>'+esc(p[1])+'<small>'+esc(p[2])+'</small></h1><div class="sub">'+esc(p[4])+'</div></div>'
  +'<div class="meta"><div>建置 BUILD<b>'+esc((S.built||'').slice(0,16))+'</b></div><div>AS-OF<b>'+esc(V.as_of||'—')+'</b></div><div>規範 LOCK<b>v0159 🔒</b></div></div>';
 st.page=id;save();$('#main').scrollTop=0}
document.addEventListener('click',function(ev){var t=ev.target.closest('[data-go]');if(t&&!t.getAttribute('href')){ev.preventDefault();show(t.dataset.go)}});
show(st.page||'sum');
if((V.live||{}).running)setTimeout(function(){location.reload()},15000);
})();
</script></body></html>
"""
BASE.BUILTIN = BUILTIN_V0102
PRIOR.BUILTIN = BUILTIN_V0102


# ---------- 自測 ----------
def selftest() -> int:
    import shutil
    import tempfile
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    keep_b, keep_s = BASE.BUILTIN, BASE.snapshot
    BASE.BUILTIN, BASE.snapshot = BUILTIN_V0101, _SNAPSHOT_V0101
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
    finally:
        BASE.BUILTIN, BASE.snapshot = keep_b, keep_s
        BASE.TAG = PRIOR.TAG = TAG
    chk("① v0101 自測照過(連 v0100 鏈;用 v0101 自己的內建範本)", prior_rc == 0, buf.getvalue()[-300:])
    tmp = Path(tempfile.mkdtemp(prefix="mdl261v2_"))
    keep = (BASE.WORK_DIR, BASE.WORK_CONFIG)
    try:
        BASE.WORK_DIR = tmp / "work"
        BASE.WORK_CONFIG = BASE.WORK_DIR / "ui_config.json"
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        duck = BASE._duck()
        c = duck.connect(str(home / "output_hub" / "mega" / "demo.duckdb"))
        c.execute("CREATE TABLE prices(date DATE, ticker VARCHAR, close DOUBLE)")
        c.execute("INSERT INTO prices VALUES ('2026-10-02','2330',1)")
        c.close()
        cfg = BASE.load_config(sets=[f"locations.db_root={home}"])
        with contextlib.redirect_stdout(io.StringIO()):
            snap, out, rep = BASE.build(cfg, home, tmp / "ui" / "page.html")
        page = out.read_text(encoding="utf-8")
        script = page[page.index("<script>\n(function"):] if "<script>\n(function" in page else page
        chk("② 視覺鎖:固定左側欄 · 側欄獨立捲動 · 沒有上方頁籤 · v0159 色票原值",
            'class="side"' in page and 'id="tabs"' not in page and ".tabs" not in page
            and all(t in page for t in ("#f5f4f0", "#1e1d1a", "#439a9a", "#c4943a", "#c96b5a", "--vl-side:232px")))
        chk("③ 側欄 = 矩陣(大類 × 輸入 · 輸出 · 驗證)+ 四組導覽(摘要 · 驗證 · 記錄 · 系統)",
            all(k in page for k in ("矩陣 MATRIX", "'摘要','SUMMARY'", "'驗證','VERIFIED'", "'記錄','RECORDS'", "系統 SYSTEMS"))
            and "<th>輸入</th><th>輸出</th><th>驗證</th>" in page)
        chk("④ 頁序:總覽 · 輸入 · 引擎 · 輸出 → 每大類驗證 · DuckDB · 環境 → 最後明細矩陣",
            re.search(r"\['sum',.*\['inp',.*\['eng',.*\['out',.*'v_'\+c\.id.*\['vdb',.*\['venv',.*\['rec',", script, re.S) is not None)
        chk("⑤ 全滑鼠:沒有文字輸入框 / 文字區;輸入頁大類矩陣有起始日下拉 · 族群打勾 · 成員方塊 · 兩個位置 + 拖放",
            not re.search(r"<input[^>]*type=\"?(text|search|number|date)", page) and "<textarea" not in page
            and all(k in page for k in ('id="l_sys"', 'id="l_db"', "d_sys", "d_db", "c_start", "c_run", "ch_'+gid", "m_add")))
        chk("⑥ 匯出格式不變(VIA_UI_Input/1 · vdf.categories / members / as_of)· 啟動指令 = via_activate_vdf",
            "schema:S.input_schema||'VIA_UI_Input/1'" in page and "vdf:{categories:cats,members:mem,as_of:" in page and "via_activate_vdf" in page)
        groups = {"groups": [{"id": "A", "zh": "甲", "category": "X", "engines": ["e1"], "summary": {"worst": "NODATA", "sources": 2}, "rows": [{}, {}]},
                             {"id": "B", "zh": "乙", "category": "X", "engines": ["e2"], "summary": {"worst": "YELLOW", "states": {"YELLOW": 1, "NODATA": 1}}},
                             {"id": "C", "zh": "丙", "category": "X", "engines": [], "summary": {"worst": "GREEN", "states": {"GREEN": 1}}}],
                  "engines": [{"id": "e1", "group": "FRED"}, {"id": "e2", "group": "AkShare"}], "io": [{"group": "A", "input": "冊"}]}
        tiers = {"A": [{"provider": "FRED", "engines": ["e1"], "key": "FRED_API_KEY"}, {"provider": "GOV", "engines": ["e9"]}]}
        rf = refill_routes(groups, tiers)
        live = {r["group"]: r for r in snap.get("refill") or []}
        chk("⑦ 補擷取路線照冊 refill 分層(順序 · 提供者 · 引擎 · 要的鑰);冊沒寫退族群引擎並註明;全綠不列;真冊 US_MACRO 含 e055fed",
            [r["group"] for r in rf] == ["A", "B"] and rf[0]["engines"] == ["e1", "e9"] and rf[0]["sources"] == ["FRED", "GOV"]
            and rf[0]["route"].startswith("1. FRED e1(要 FRED_API_KEY) → 2. GOV e9") and rf[0]["nodata"] == 2
            and rf[1]["route"].startswith("冊上沒寫 refill") and rf[1]["nodata"] == 1
            and ("US_MACRO" not in live or "e055fed" in live["US_MACRO"]["engines"]), (rf, live.get("US_MACRO")))
        chk("⑧ 零 CDN / 零 fetch / 不需伺服器(file://)", not re.search(r'(src|href)="https?://', page) and "fetch(" not in script
            and "XMLHttpRequest" not in page)
    finally:
        BASE.WORK_DIR, BASE.WORK_CONFIG = keep
        shutil.rmtree(tmp, ignore_errors=True)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · v0101 鏈 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
