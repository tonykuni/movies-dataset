#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0112 — 薄尾:跨來源對照的結果交獨立驗證器逐筆核對(100%)· 可操作的對照頁(HTML U/I)· 收尾判定
  (合併 main 撞號:main 的 v0108 = 他系統表分開命名 VRN-1 / VRN-2 / VCGC · 資料庫流程 db where + db_xcheck(PR #537);
   本變更在分支上原為 v0111,改出 v0112 疊在 main 的 v0108 → v0109 → v0110 之上。
   「單一來源一致的來源空」那一處已併進 v0111,本版不再另外補。)

操作員令(2026-10-20):「GO ON TO RESULTS VERIFIED 100% CORRECT AND HTML U/I · 收尾變成功」。
本版(只在本版 activate 那一輪 · v0111 的 ⑦ 體檢 / ⑧ 對照之後):
  ⑨ 結果獨立驗證:VDF_XsrcVerifier 尾版(另一支檔 · 不匯入 ActivateVDF · 自己的日期解析與判定寫法)逐項核對 ——
     V0 中間檔每檔一來源 · V1 每一筆回資料庫原表整批比對(值與來源一字不差 · 同來源多次抓取取最新)· V2 日期標準且等於原寫法獨立重算 ·
     V3 判定 / 一致 / 離群 / 每個來源的值獨立重算 · V4 計數 · V5 日期體檢重掃 → 不符 0 = PASS(結果 100% 正確)。
  ⑩ 收尾判定:驗證 FAIL → 紅(結果不可信;總燈紅)· 沒有多來源資料 → INFO · 驗證 100% 且沒有衝突 → 綠「收尾成功」·
     驗證 100% 但有衝突 → 黃(列出待查;總燈照 v0111 黃)。引擎表的舊日期格式只在體檢列出,不擋收尾(改寫既有列會成重複列)。
  對照頁:VIA_Reports/vdf/xsrc/VDF_XSRC_latest.html(+ 本輪一份 · 驗證 JSON)—— 收尾判定 · 計數 · 驗證六項 · 逐筆表(資料集 / 判定篩選 ·
     搜尋 · 排序 · 分頁 · 每個來源的值)· 日期體檢 · 中間檔清單;頁面資料讀磁碟上的對照結果(= 驗證器核對的那份),頁面指紋 = 驗證指紋才套用判決。
     總覽卡多「結果獨立驗證 · 收尾 · 打開對照頁」;終端多 ⑨ ⑩ 兩行。
  其餘全照 v0111;本版一輪落檔標 v0112;換上的函式只在這一輪(跑完換回原樣)。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境;資料庫只唯讀。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import html
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0112(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0112(p) < _vnum_v0112(__file__)), key=_vnum_v0112)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100
_V0101 = vars(PRIOR).get("_V0101")
_V0106 = vars(PRIOR).get("_V0106")

_VER_PATH = max((p for p in HERE.glob("VDF_XsrcVerifier_v*.py") if _vnum_v0112(p) >= 0), key=_vnum_v0112)   # 獨立驗證器尾版(VDF 自己的)
_vspec = importlib.util.spec_from_file_location("VDF_XsrcVerifier_for_" + Path(__file__).stem, _VER_PATH)
VER = importlib.util.module_from_spec(_vspec)
sys.modules[_vspec.name] = VER
_vspec.loader.exec_module(VER)


def __getattr__(name):
    return getattr(PRIOR, name)


def _post_fetch_layer(prev):
    def post_fetch(opt, res: dict) -> dict:
        post = prev(opt, res)
        xs = post.get("xsrc") or {}
        if xs.get("note") and not (xs.get("temp") or {}).get("files"):
            xs["verify"] = {"verdict": "EMPTY", "checks": {}, "rows": 0, "items": 0}
            xs["closeout"] = closeout(xs, xs["verify"])
            return post
        try:
            rep = VER.verify(Path(xs["temp"]["dir"]), xs, PRIOR.db_files(opt), post.get("datefmt"))
        except Exception as exc:                   # noqa: BLE001 — 驗證器自己出錯 = 結果沒驗到 → 照實算 FAIL(不可信)
            rep = {"verdict": "FAIL", "checks": {"驗證器出錯": {"n": 0, "bad": 1, "examples": ["%s %s" % (type(exc).__name__, str(exc)[:200])], "note": ""}},
                   "fingerprint": "", "rows": 0, "items": 0}
        xs["verify"] = rep
        xs["closeout"] = closeout(xs, rep)
        stamp = Path(res["temp_run"]).name.replace("run_", "") or "now"
        try:
            xs["ui"] = write_ui(xs, post.get("datefmt") or {}, rep, stamp, V0100.REPORT_DIR.parent / "xsrc")
        except OSError as exc:
            xs["ui"] = {"error": "%s %s" % (type(exc).__name__, exc)}
        return post
    return post_fetch


def _summary_layer(prev):
    def summary_lines(post: dict) -> list:
        out = list(prev(post))
        xs = post.get("xsrc") or {}
        rep, co, ui = xs.get("verify") or {}, xs.get("closeout") or {}, xs.get("ui") or {}
        if rep:
            bad = ["%s 不符 %s" % (k.split(" ")[0], v["bad"]) for k, v in (rep.get("checks") or {}).items() if v.get("bad")]
            out.append("  ⑨ 結果獨立驗證 %s:中間檔 %s 筆回原表逐筆核對 · 日期 · 判定重算 · 計數 · 體檢重掃%s · 指紋 %s" % (
                rep.get("verdict"), rep.get("rows"), (" · " + ";".join(bad)) if bad else "(不符 0 → 100%)", str(rep.get("fingerprint", ""))[:16]))
        if co:
            out.append("  ⑩ 收尾 %s:%s" % (co.get("lamp"), co.get("text")))
        if ui.get("latest"):
            out.append("     · 對照頁(可篩選 · 驗證過的結果)→ %s" % ui["latest"])
        return out
    return summary_lines


def _card_layer(prev):
    def xsrc_card(card: dict) -> str:
        h = prev(card)
        xs = card.get("xsrc") or {}
        rep, co, ui = xs.get("verify") or {}, xs.get("closeout") or {}, xs.get("ui") or {}
        if not h or not (rep or co):
            return h
        e = html.escape
        col = {"GREEN": "#1a7f37", "PASS": "#1a7f37", "YELLOW": "#9a6700", "INFO": "#57606a", "EMPTY": "#57606a"}
        link = ""
        if ui.get("latest"):
            rel = os.path.relpath(ui["latest"], V0100.REPORT_DIR) if os.path.isabs(ui["latest"]) else ui["latest"]
            link = f'<br><a href="{e(Path(rel).as_posix())}">打開對照頁(可篩選 · 驗證過的結果)</a> <span class="mut">{e(ui["latest"])}</span>'
        blk = (f'<br><b>結果獨立驗證</b> <span class="lamp" style="background:{col.get(rep.get("verdict"), "#cf222e")}">{e(str(rep.get("verdict")))}</span> '
               f'中間檔 {e(str(rep.get("rows")))} 筆回原表逐筆核對 · 日期 · 判定重算 · 計數 · 體檢重掃 · 指紋 {e(str(rep.get("fingerprint", ""))[:16])}'
               f'<br><b>收尾</b> <span class="lamp" style="background:{col.get(co.get("lamp"), "#cf222e")}">{e(str(co.get("lamp")))}</span> {e(str(co.get("text")))}{link}')
        i = h.rfind("</section>")
        return h[:i] + blk + h[i:] if i >= 0 else h + blk
    return xsrc_card


def _overall_layer(prev):
    def overall(lists, flows):
        lamp = prev(lists, flows)
        xs = (vars(PRIOR).get("_POST") or {}).get("xsrc") or {}
        if (xs.get("verify") or {}).get("verdict") == "FAIL":
            return "RED"                           # 結果驗證沒過 = 結果不可信 → 紅
        return lamp
    return overall


def _stamp_layer(prev):
    def _stamp_then_write(c, u=None):
        c["schema"], c["tag"] = "VDF_ActivateVDF_v0112", TAG
        return prev(c, u) if u is not None else prev(c)
    return _stamp_then_write


_ACTIVATE_PRIOR = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0111 activate;這一輪對照完 → 獨立驗證器(⑨)→ 收尾判定(⑩)→ 對照頁。
    換上的東西只在這一輪(跑完換回原樣)。"""
    keep_tag = PRIOR.TAG
    PRIOR.TAG = TAG
    saved = {k: vars(PRIOR)[k] for k in ("post_fetch", "summary_lines", "xsrc_card")}
    keep_overall = _V0101["overall"]
    prev_w = vars(_V0106).get("_WRITE_REPORT_V0100") if _V0106 is not None else None
    PRIOR.post_fetch = _post_fetch_layer(saved["post_fetch"])
    PRIOR.summary_lines = _summary_layer(saved["summary_lines"])
    PRIOR.xsrc_card = _card_layer(saved["xsrc_card"])
    _V0101["overall"] = _overall_layer(keep_overall)
    if prev_w is not None:
        _V0106._WRITE_REPORT_V0100 = _stamp_layer(prev_w)
    try:
        return _ACTIVATE_PRIOR(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep_tag
        for k, v in saved.items():
            setattr(PRIOR, k, v)
        _V0101["overall"] = keep_overall
        if prev_w is not None:
            _V0106._WRITE_REPORT_V0100 = prev_w


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 對照頁(可操作的 HTML U/I:篩選 · 搜尋 · 分頁 · 驗證判決 · 收尾)
_PAGE = r"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VDF 跨來源對照</title><style>
:root{--bg:#f6f8fa;--card:#fff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--g:#1a7f37;--y:#9a6700;--r:#cf222e;--i:#57606a;--acc:#0969da}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--g:#3fb950;--y:#d29922;--r:#f85149;--i:#8b949e;--acc:#4493f8}}
:root[data-theme="dark"]{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--g:#3fb950;--y:#d29922;--r:#f85149;--i:#8b949e;--acc:#4493f8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:16px}h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:18px 0 8px}
.mut{color:var(--mut)}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:10px 0;overflow-wrap:anywhere}
.lamp{display:inline-block;color:#fff;border-radius:10px;padding:0 8px;font-size:12px;font-weight:600;vertical-align:middle;white-space:nowrap}
.GREEN,.PASS,.VERIFIED{background:var(--g)}.YELLOW,.CONFLICT{background:var(--y)}.RED,.FAIL{background:var(--r)}.INFO,.EMPTY,.SINGLE{background:var(--i)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px}.tile{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}
.tile b{display:block;font-size:22px}.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0}
select,input,button{font:inherit;color:var(--fg);background:var(--card);border:1px solid var(--line);border-radius:6px;padding:4px 8px;min-width:0}
input{flex:1 1 160px}.tw{overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
th{position:sticky;top:0;background:var(--card);cursor:pointer;white-space:nowrap}td.v{font-family:ui-monospace,Consolas,monospace;font-size:12px}
.ok{color:var(--g)}.bad{color:var(--r)}details{margin:6px 0}code{font-size:12px;overflow-wrap:anywhere}#meta,h1{overflow-wrap:anywhere}
</style></head><body><div class="wrap">
<h1>VDF 擷取後 · 跨來源對照 <span id="lamp" class="lamp"></span></h1><div class="mut" id="meta"></div>
<div class="card" id="closeout"></div>
<div class="tiles" id="tiles"></div>
<h2>獨立驗證(VDF_XsrcVerifier)</h2><div class="card"><div id="verdict"></div><div class="tw"><table id="checks"></table></div></div>
<h2>逐筆對照(驗證過的結果)</h2>
<div class="bar"><select id="fd"></select><select id="fs"><option value="">全部判定</option><option value="VERIFIED">成功(兩個以上來源相同)</option>
<option value="CONFLICT">衝突</option><option value="SINGLE">只有一個來源</option></select><input id="fq" placeholder="代號 / 日期 / 欄位 / 來源"><span class="mut" id="cnt"></span></div>
<div class="tw"><table id="tbl"><thead><tr><th data-k="dataset">資料集</th><th data-k="key">代號</th><th data-k="date">日期</th><th data-k="field">欄位</th>
<th data-k="status">判定</th><th data-k="agree">一致的來源</th><th data-k="outliers">離群</th><th>各來源的值</th></tr></thead><tbody></tbody></table></div>
<div class="bar"><button id="prev">上一頁</button><span id="pg" class="mut"></span><button id="next">下一頁</button></div>
<h2>日期格式體檢(引擎的表)</h2><div class="card" id="dfm"></div>
<h2>中間檔(本輪 TEMP · 依來源分檔)</h2><div class="card" id="files"></div>
<p class="mut">規則:同一筆(資料集 · 代號 · 日期 · 欄位)兩個以上來源相同 = 對照成功(第三個不同記離群);有兩個以上來源但沒有任兩個相同 = 衝突;只有一個來源 = 沒得對照。
相同:價格到 0.01 · 營收整數 · 其他數值照兩邊較粗的小數位。中間檔與結果的日期一律 YYYY / YYYY-MM / YYYY-MM-DD(原寫法另欄留)。
頁面資料的指紋 = 驗證報告的指紋,判決才套用到這一頁。</p></div>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
var D=JSON.parse(document.getElementById('data').textContent),it=D.items,$=function(i){return document.getElementById(i)};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
var ZH={VERIFIED:'成功',CONFLICT:'衝突',SINGLE:'單一來源',PASS:'PASS',FAIL:'FAIL',EMPTY:'沒有資料',GREEN:'GREEN',YELLOW:'YELLOW',RED:'RED',INFO:'INFO'};
var co=D.closeout||{};$('lamp').className='lamp '+(co.lamp||'INFO');$('lamp').textContent=co.lamp||'INFO';
$('meta').textContent=D.tag+' · '+D.stamp+' · 中間檔 '+D.temp_dir;
$('closeout').innerHTML='<b>收尾判定</b> <span class="lamp '+esc(co.lamp)+'">'+esc(co.lamp)+'</span> '+esc(co.text||'');
var c=D.counts||{},rate=D.rate==null?'—':(D.rate*100).toFixed(2)+'%';
$('tiles').innerHTML=[['成功(兩個以上來源相同)',c.VERIFIED],['衝突',c.CONFLICT],['只有一個來源',c.SINGLE],['可對照',D.comparable],['成功率',rate]]
 .map(function(t){return '<div class="tile"><span class="mut">'+esc(t[0])+'</span><b>'+esc(t[1])+'</b></div>'}).join('');
var V=D.verify||{},same=V.fingerprint&&V.fingerprint===D.page_fingerprint;
$('verdict').innerHTML='判決 <span class="lamp '+esc(V.verdict)+'">'+esc(V.verdict)+'</span> · 中間檔 '+esc(V.rows)+' 筆 · 結果 '+esc(V.items)+' 列 · '
 +(same?'<span class="ok">頁面指紋 = 驗證報告指紋('+esc(String(V.fingerprint).slice(0,16))+')→ 判決套用</span>'
       :'<span class="bad">頁面指紋 '+esc(String(D.page_fingerprint).slice(0,16))+' ≠ 驗證報告 '+esc(String(V.fingerprint).slice(0,16))+' → 判決不套用</span>')
 +(V.dup_count?' · <span class="mut">同一來源同一筆兩個值 '+esc(V.dup_count)+' 處(第一列生效)</span>':'');
$('checks').innerHTML='<tr><th>核對</th><th>筆數</th><th>不符</th><th>說明</th></tr>'+Object.keys(V.checks||{}).map(function(k){var x=V.checks[k];
 return '<tr><td>'+esc(k)+'</td><td>'+esc(x.n)+'</td><td class="'+(x.bad?'bad':'ok')+'">'+esc(x.bad)+'</td><td>'+esc(x.note||'')+(x.examples&&x.examples.length?'<br><code>'+x.examples.map(esc).join('<br>')+'</code>':'')+'</td></tr>'}).join('');
var ds=Array.from(new Set(it.map(function(r){return r.dataset}))).sort();
$('fd').innerHTML='<option value="">全部資料集</option>'+ds.map(function(d){return '<option>'+esc(d)+'</option>'}).join('');
var sortK='',sortD=1,page=0,PER=100,view=it;
function apply(){var d=$('fd').value,s=$('fs').value,q=$('fq').value.trim().toLowerCase();
 view=it.filter(function(r){return(!d||r.dataset===d)&&(!s||r.status===s)&&(!q||(r.key+' '+r.date+' '+r.field+' '+r.sources).toLowerCase().indexOf(q)>=0)});
 if(sortK)view=view.slice().sort(function(a,b){return(a[sortK]>b[sortK]?1:a[sortK]<b[sortK]?-1:0)*sortD});page=0;draw()}
function draw(){var n=view.length,pages=Math.max(1,Math.ceil(n/PER));if(page>=pages)page=pages-1;
 $('cnt').textContent='符合 '+n+' 筆';$('pg').textContent='第 '+(page+1)+' / '+pages+' 頁';
 $('tbl').tBodies[0].innerHTML=view.slice(page*PER,page*PER+PER).map(function(r){var vs=r.values||{};
  return '<tr><td>'+esc(r.dataset)+'</td><td>'+esc(r.key)+'</td><td>'+esc(r.date)+'</td><td>'+esc(r.field)+'</td><td><span class="lamp '+esc(r.status)+'">'+esc(ZH[r.status]||r.status)+'</span></td><td>'
   +esc(r.agree)+'</td><td>'+esc(r.outliers)+'</td><td class="v">'+Object.keys(vs).map(function(k){return esc(k)+' '+esc(vs[k])}).join('<br>')+'</td></tr>'}).join('')}
['fd','fs'].forEach(function(i){$(i).addEventListener('change',apply)});$('fq').addEventListener('input',apply);
$('prev').onclick=function(){if(page>0){page--;draw()}};$('next').onclick=function(){page++;draw()};
Array.prototype.forEach.call(document.querySelectorAll('#tbl th[data-k]'),function(th){th.onclick=function(){var k=th.getAttribute('data-k');sortD=(sortK===k)?-sortD:1;sortK=k;apply()}});
var F=D.datefmt||{};$('dfm').innerHTML=F.note?esc(F.note):('<span class="lamp '+esc(F.lamp)+'">'+esc(F.lamp)+'</span> 日期欄 '+esc(F.columns)+' · 標準 '+esc(F.standard)+' · 不標準 '+esc(F.nonstandard)
 +'(混兩種以上格式 '+esc(F.mixed)+')<div class="tw"><table><tr><th>庫</th><th>表.欄</th><th>型別</th><th>標準</th><th>格式(筆數)</th><th>例</th></tr>'
 +(F.items||[]).map(function(x){return '<tr><td>'+esc(x.db)+'</td><td>'+esc(x.table)+'.'+esc(x.column)+'</td><td>'+esc(x.type)+'</td><td class="'+(x.standard?'ok':'bad')+'">'+(x.standard?'是':'否')+(x.mixed?'(混用)':'')
  +'</td><td>'+Object.keys(x.formats||{}).map(function(k){return esc(k)+' ×'+esc(x.formats[k])}).join('<br>')+'</td><td><code>'+(x.examples||[]).map(esc).join(' / ')+'</code></td></tr>'}).join('')
 +'</table></div><p class="mut">引擎的表照它原本的格式存(各引擎 upsert 用自己的日期格式當鍵,改寫既有列下一輪會成重複列);標準格式在中間檔與這頁的結果裡。</p>');
$('files').innerHTML=(D.files||[]).map(function(f){return '<code>'+esc(f)+'</code>'}).join('<br>')||'—';
apply();
})();
</script></body></html>"""


def closeout(xs: dict, rep: dict) -> dict:
    """收尾判定:驗證器 FAIL = 紅(結果不可信)· 沒有可對照資料 = INFO · 驗證 100% 且沒有衝突 = 綠(收尾成功)· 驗證 100% 但有衝突 = 黃(列出待查)。"""
    v = (rep or {}).get("verdict")
    c = (xs or {}).get("counts") or {}
    if v == "FAIL":
        bad = [k.split(" ")[0] for k, x in (rep.get("checks") or {}).items() if x.get("bad")]
        return {"lamp": "RED", "text": "結果驗證沒過(%s 有不符)→ 結果不可信,不能收尾" % "、".join(bad)}
    if v != "PASS":
        return {"lamp": "INFO", "text": "本輪沒有兩個以上來源的資料可對照(%s)" % ((xs or {}).get("note") or "資料庫裡沒有多來源的表")}
    if c.get("CONFLICT"):
        return {"lamp": "YELLOW", "text": "結果 100%% 驗證過;成功 %s · 衝突 %s 筆(來源對不上,見下表「衝突」)· 單一來源 %s" % (c.get("VERIFIED"), c.get("CONFLICT"), c.get("SINGLE"))}
    return {"lamp": "GREEN", "text": "收尾成功:結果 100%% 驗證過 · 可對照 %s 筆全部兩個以上來源相同 · 單一來源 %s" % (xs.get("comparable"), c.get("SINGLE"))}


def write_ui(xs: dict, datefmt: dict, rep: dict, stamp: str, out_dir: Path) -> dict:
    """對照頁:讀磁碟上的對照結果(= 驗證器核對的那份)嵌進頁面;頁面指紋 = 驗證報告指紋才套用判決。"""
    xdir = Path((xs.get("temp") or {}).get("dir", ""))
    rows = VER.result_rows(xdir) if xdir.is_dir() else []
    items = []
    for r in rows:
        try:
            vals = json.loads(r["values"])
        except (ValueError, TypeError):
            vals = {}
        items.append({k: r[k] for k in ("dataset", "key", "date", "field", "status", "sources", "agree", "outliers")}
                     | {"values": {s: str(v) for s, v in vals.items()}})   # 原值照中間檔那格的字串(200.0 不變成 200)
    data = {"tag": TAG, "stamp": stamp, "temp_dir": str(xdir), "counts": xs.get("counts"), "comparable": xs.get("comparable"), "rate": xs.get("rate"),
            "verify": {k: rep.get(k) for k in ("verdict", "checks", "fingerprint", "rows", "items", "dup_count")}, "page_fingerprint": VER.fingerprint(rows),
            "closeout": xs.get("closeout"), "datefmt": datefmt, "files": (xs.get("temp") or {}).get("files", []), "items": items}
    blob = json.dumps(data, ensure_ascii=False, default=str).replace("</", "<\\/")
    out_dir.mkdir(parents=True, exist_ok=True)
    page = out_dir / ("VDF_XSRC_%s.html" % stamp)
    page.write_text(_PAGE.replace("__DATA__", blob), encoding="utf-8")
    latest = out_dir / "VDF_XSRC_latest.html"
    latest.write_text(page.read_text(encoding="utf-8"), encoding="utf-8")
    j = out_dir / ("XSRC_VERIFY_%s.json" % stamp)
    j.write_text(json.dumps({"verify": rep, "closeout": xs.get("closeout"), "page_fingerprint": data["page_fingerprint"]}, ensure_ascii=False, indent=1, default=str),
                 encoding="utf-8")
    (out_dir / "XSRC_VERIFY_latest.json").write_text(j.read_text(encoding="utf-8"), encoding="utf-8")
    return {"html": str(page), "latest": str(latest), "json": str(j), "page_fingerprint": data["page_fingerprint"]}


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note != "" else ""), flush=True)
    print(f"=== {TAG} · 薄尾自測(結果獨立驗證 + 對照頁 + 收尾判定;沙盒 · 零網路)===", flush=True)
    rows = [{"dataset": "d", "key": k, "date": "2026-08-24", "field": "close", "value": v, "source": s, "dec": 2}
            for k, s, v in (("A", "TWSE", 1.0), ("A", "YAHOO", 1.0), ("B", "TWSE", 2.0))]
    r = PRIOR.cross_check(rows)
    a_, b_ = (next(i for i in r["items"] if i["key"] == k) for k in ("A", "B"))
    chk("Ⓚ 只有一個來源 → 「一致的來源」是空的(v0111 起;獨立驗證器 V3 驗)· 成功那筆照舊",
        b_["status"] == "SINGLE" and b_["agree"] == [] and a_["agree"] == ["TWSE", "YAHOO"], (a_["agree"], b_["agree"]))
    cs = {"VERIFIED": 5, "CONFLICT": 1, "SINGLE": 3}
    co = [closeout({"counts": c_, "comparable": 6}, {"verdict": v_, "checks": {"V1 x": {"bad": 1}} if v_ == "FAIL" else {}})["lamp"]
          for c_, v_ in ((cs, "FAIL"), (cs, "EMPTY"), (cs, "PASS"), (dict(cs, CONFLICT=0), "PASS"))]
    chk("Ⓝ 收尾判定:驗證 FAIL → 紅(不可信)· 沒資料 → INFO · 驗證 100% 有衝突 → 黃 · 驗證 100% 沒衝突 → 綠(收尾成功)", co == ["RED", "INFO", "YELLOW", "GREEN"], co)
    have = PRIOR._duck() is not None
    keep_rep = V0100.REPORT_DIR
    if not have:
        chk("Ⓛ duckdb 不在本境 → 對照 / 驗證不跑(不代裝);收尾 INFO", closeout({"note": "沒有 duckdb"}, {"verdict": "EMPTY"})["lamp"] == "INFO")
    else:
        with tempfile.TemporaryDirectory(prefix="activatevdf111_") as td:
            t = Path(td)
            home = PRIOR.make_fixture(t / "output_hub")
            opt = type("O", (), {"db_home": str(home), "fetch_home": None})()
            V0100.REPORT_DIR = t / "rep" / "activate"
            try:
                post = _post_fetch_layer(PRIOR.post_fetch)(opt, {"temp_run": str(t / "tmp" / "run_20261020_090000")})
            finally:
                V0100.REPORT_DIR = keep_rep
            xs = post["xsrc"]
            rep, ui = xs.get("verify") or {}, xs.get("ui") or {}
            page = Path(ui.get("latest", "/nonexistent")).read_text(encoding="utf-8") if ui.get("latest") else ""
            chk("Ⓛ 測試庫整段:對照 → 獨立驗證 PASS(六項不符 0 · 回原表逐筆)→ 收尾 黃(有 1 筆衝突)→ 對照頁 + 驗證 JSON;頁面指紋 = 驗證指紋",
                rep.get("verdict") == "PASS" and xs["closeout"]["lamp"] == "YELLOW" and ui.get("page_fingerprint") == rep.get("fingerprint")
                and '"verdict": "PASS"' in page and Path(ui["json"]).is_file() and Path(ui["latest"]).name == "VDF_XSRC_latest.html",
                {k.split(" ")[0]: v["bad"] for k, v in (rep.get("checks") or {}).items()})
            f = next(Path(p) for p in xs["temp"]["files"] if p.endswith("tw_daily_close__TWSE.csv"))
            txt = f.read_text(encoding="utf-8-sig").replace(",1045.0,", ",1046.0,")
            f.write_text(txt, encoding="utf-8-sig")
            rep2 = VER.verify(Path(xs["temp"]["dir"]), xs, PRIOR.db_files(opt), post["datefmt"])
            keep_post = dict(vars(PRIOR)["_POST"])
            vars(PRIOR)["_POST"].clear()
            vars(PRIOR)["_POST"]["xsrc"] = dict(xs, verify=rep2)
            lamp = _overall_layer(lambda lists, flows: "GREEN")(None, None)
            vars(PRIOR)["_POST"].clear()
            vars(PRIOR)["_POST"].update(keep_post)
            chk("Ⓜ 中間檔被改一個值(1045.0 → 1046.0)→ 獨立驗證 FAIL(V1 回原表不符)→ 收尾 紅 · 總燈 紅",
                rep2["verdict"] == "FAIL" and rep2["checks"][next(k for k in rep2["checks"] if k.startswith("V1"))]["bad"] >= 1
                and closeout(xs, rep2)["lamp"] == "RED" and lamp == "RED", lamp)
            h = PRIOR.xsrc_card({"xsrc": xs, "datefmt": post["datefmt"]})
            h2 = _card_layer(PRIOR.xsrc_card)({"xsrc": xs, "datefmt": post["datefmt"]})
            sl = _summary_layer(PRIOR.summary_lines)(post)
            chk("Ⓞ 總覽卡多「結果獨立驗證 · 收尾 · 打開對照頁」(在同一張卡裡)· 終端多 ⑨ ⑩ 兩行與對照頁路徑",
                h and h2.startswith(h[:h.rfind("</section>")]) and "結果獨立驗證" in h2 and "打開對照頁" in h2 and h2.endswith("</section>")
                and any(x.startswith("  ⑨ 結果獨立驗證 PASS") for x in sl) and any(x.startswith("  ⑩ 收尾 YELLOW") for x in sl), [x[:30] for x in sl[-3:]])
            evil = dict(xs, temp={"dir": str(t / "nope"), "files": []})
            u2 = write_ui(evil, {"note": "</script><b>x"}, {"verdict": "EMPTY", "checks": {}}, "evil", t / "ui2")
            pg2 = Path(u2["latest"]).read_text(encoding="utf-8")
            chk("Ⓟ 對照頁資料嵌入安全:資料裡有 </script> 也不會提早結束(轉成 <\\/script>)· 篩選 / 搜尋 / 分頁 / 排序元件都在 · 深色模式",
                pg2.count("</script>") == 2 and "<\\/script>" in pg2 and all(x in pg2 for x in ('id="fd"', 'id="fs"', 'id="fq"', 'id="prev"', 'data-k="key"', "prefers-color-scheme:dark")))
    chk("Ⓠ 本輪換上的函式不在一輪裡時都是原樣(v0111 的 cross_check / post_fetch / summary_lines / xsrc_card · v0101 overall)",
        all("<locals>" not in getattr(vars(PRIOR)[k], "__qualname__", "") for k in ("cross_check", "post_fetch", "summary_lines", "xsrc_card"))
        and "<locals>" not in getattr(_V0101["overall"], "__qualname__", ""))
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    vsrc = Path(_VER_PATH).read_text(encoding="utf-8")
    chk("Ⓡ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫;驗證器是另一支檔(不匯入 ActivateVDF)",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC", "via_duck_temp"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src)
        and not re.search(r"^\s*(import|from)\s+(VDF_MDL013|ActivateVDF)", vsrc, re.M), _VER_PATH.name)
    n_ok = sum(ok)
    print(f"  [計] {TAG} 本版 {n_ok}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    if not all(ok):
        return 1
    print(f"  ── 獨立驗證器 {_VER_PATH.name} 自測 ──", flush=True)
    if VER.selftest() != 0:
        return 1
    rc1 = PRIOR.selftest()
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0102 / v0107 … v0111)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
