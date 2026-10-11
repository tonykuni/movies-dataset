#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL261_UIEngine v0106 — 薄尾:VCGC 操作台展現重整(燈欄第一 · 問題在前 · 燈號列 · 空值 — · 路徑縮檔名)

操作員令(2026-10-11):「很多展現都要重新思考整理」→「GO ON」(承「u/i請字體一致或階層一致姓  左右面板都凌亂」「日期規格一慮用YYYY-MM-DD」)。
  展現規則(讀 registry 的 VIA_UI_Template_SSOT 尾版 presentation 節;只讀資料冊):
  ① 燈號表:燈欄只有一欄就移到第一欄;列照 紅 → 黃 → 綠 → 灰 排(同燈保留原順序;頁上自己的篩選鈕照用)
  ② 列多(≥ 8)且頁上沒有自己的「只看紅 / 只看黃」鈕 → 表上方加燈號列(紅 n · 黃 n · 綠 n · 灰 n · 共 n 列 · 問題在前)+「只看紅黃」
  ③ 空值一律 —(NaN · None · null …);格子裡整串路徑只顯示檔名(滑鼠停留看全路徑);燈號計數 JSON 改「紅 n · 黃 n · 綠 n」
  ④ 網址 #via-pick=<字> → 載入後點同名鈕;表格換行改一欄一條規則(取前 60 列量字數),大表載入快
  字級 / 字重 / 字體 / 日期 YYYY-MM-DD 照前版。純 CSS + 頁內小段 JS;不連網、不裝套件、不載外部函式庫。
  作法:前版 v0105 build 用的字級套件換成本版 v2(build 先不開 → 套件 → 要開才開照舊;閘戳 YYYY-MM-DD HH:MM 照舊)。
其餘照 v0105。只讀:不連網、不寫冊;不代跑他系統。只收 VCGC 呼叫。
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
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
TK_ROOT = VIA
SELF_ID = "VCGC"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = _vnum(__file__)
    hits = [p for p in HERE.glob("CGC_MDL261_UIEngine_v*.py") if 0 <= _vnum(p) < me]
    return max(hits, key=_vnum)


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0106", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"CGC_MDL261_UIEngine v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


# ---------- 字級套件(VIA_UI_Template_SSOT 尾版的字級 token → 頁內一段 CSS + 一小段 JS;只讀冊 · 不連網 · 不載外部庫) ----------
TK_DEFAULT_TOKENS = {
    "font": '"Microsoft JhengHei UI","Microsoft JhengHei","PingFang TC","Noto Sans TC","Noto Sans CJK TC","Segoe UI",sans-serif',
    "mono": 'Consolas,"Cascadia Mono","Noto Sans Mono","DejaVu Sans Mono",monospace',
    "fs-title": "16px", "fs-h": "13px", "fs": "12px", "fs-note": "11px", "lh": "1.45", "w-normal": "400", "w-bold": "700", "line": "#e0e0e0"}
TK_DEFAULT_AUTO = {"cell_nowrap_max_chars": 24, "cell_long_max_ch": 48, "wide_table_scroll": True,
                   "stack_side_tables_with_controls": True, "side_selectors": "aside, .side"}
TK_DEFAULT_PRESENT = {"bar_min_rows": 8, "lamp_ratio": 0.6, "path_min_len": 40, "pick_hash": "via-pick"}
_TK_RE = re.compile(r"<!--via-typekit:begin[^>]*-->.*?<!--via-typekit:end-->", re.S)
_TK_CSS = (":root{--via-font:@FONT@;--via-mono:@MONO@;--via-t1:@T1@px;--via-t2:@T2@px;--via-t3:@T3@px;--via-t4:@T4@px;--via-lh:@LH@}\n"
           "html body{font-family:var(--via-font);font-size:var(--via-t3);line-height:var(--via-lh);-webkit-text-size-adjust:100%;text-size-adjust:100%}\n"
           "button,input,select,textarea{font-family:inherit;font-size:var(--via-t3);line-height:1.3}\n"
           "code,pre,kbd,samp,.mono,.cmd,textarea{font-family:var(--via-mono)}\n"
           "h1{font-size:var(--via-t1)}h2,h3{font-size:var(--via-t2)}h4,h5,h6{font-size:var(--via-t3)}h1,h2,h3,h4,h5,h6,th,b,strong{font-weight:@WB@}\n"
           "small{font-size:var(--via-t4)}td,th{font-variant-numeric:tabular-nums;vertical-align:middle}button{white-space:nowrap}\n"
           "@SIDECARD@{overflow-x:auto}\n"
           "table.via-stack thead{display:none}table.via-stack,table.via-stack tbody{display:block;width:100%}\n"
           "table.via-stack tr{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 8px;align-items:center;padding:6px 0;"
           "border-bottom:1px solid var(--line,@LINE@)}\n"
           "table.via-stack td{display:block;border:0;padding:0;min-width:0}table.via-stack td:first-child{grid-column:1/-1}\n"
           "table.via-stack td input,table.via-stack td select{width:100%}table.via-stack td button{margin:0}\n"
           "td.via-nw,th.via-nw{white-space:nowrap}td.via-long{max-width:@LONG@ch;overflow-wrap:anywhere}.via-scroll{overflow-x:auto;max-width:100%}\n"
           ".via-date{display:inline-flex;gap:4px;align-items:center;max-width:100%}.via-date input{flex:1;min-width:0}table.via-stack td .via-date{display:flex;width:100%}\n"
           ".via-cal{padding:0 6px;margin:0;cursor:pointer}.via-cal-p{width:auto}input[aria-invalid=true]{border-color:#dc2626;outline:1px solid #dc2626}\n"
           ".via-lampbar{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;margin:6px 0 8px}.via-lampbar b{font-weight:@WB@}"
           ".via-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px;vertical-align:middle}"
           ".via-dot.RED{background:var(--lamp-red,#dc2626)}.via-dot.YELLOW{background:var(--lamp-yellow,#f59e0b)}"
           ".via-dot.GREEN{background:var(--lamp-green,#16a34a)}.via-dot.GRAY{background:var(--lamp-gray,#9ca3af)}\n"
           "table.via-issues tr[data-via-l=GREEN],table.via-issues tr[data-via-l=GRAY]{display:none}"
           "td.via-empty{color:var(--dim,#9ca3af);text-align:center}td.via-path{color:var(--dim,#6b7280)}\n")
_TK_JS = ("(function(){var L=[@T1@,@T2@,@T3@,@T4@],NW=@NW@,SCROLL=@SCROLL@,STACK=@STACK@,SIDE='@SIDE@',HN='http://www.w3.org/1999/xhtml',"
          "SKIP=/^(SCRIPT|STYLE|IFRAME|BR|HR|CANVAS|IMG|VIDEO|AUDIO|NOSCRIPT|TEMPLATE|OPTION)$/,CTL=/^(INPUT|SELECT|TEXTAREA|BUTTON)$/,seen=(typeof WeakSet!=='undefined')?new WeakSet():null,seenT=(typeof WeakSet!=='undefined')?new WeakSet():null,busy=false,TN=0;\n"
          "function lv(p){return p>=(L[0]+L[1])/2?L[0]:p>=(L[1]+L[2])/2?L[1]:p>=(L[2]+L[3])/2?L[2]:L[3]}\n"
          "function own(e){for(var n=e.firstChild;n;n=n.nextSibling){if(n.nodeType===3&&/\\S/.test(n.nodeValue))return true}return false}\n"
          "function sig(e){return e.tagName+'.'+(e.getAttribute('class')||'')+'#'+(e.getAttribute('style')||'')}\n"
          "function snap(){var a=document.body.getElementsByTagName('*'),R=[],i,e,c,B=getComputedStyle(document.body).fontFamily,PM=new Map(),PC={};PM.set(document.body,'B');\n"
          " function pathOf(x){if(PM.has(x))return PM.get(x);var p=x.parentElement;var k=(p&&p!==document.documentElement?pathOf(p):'')+'>'+sig(x);PM.set(x,k);return k}\n"
          " for(i=0;i<a.length;i++){e=a[i];if(e.namespaceURI!==HN||SKIP.test(e.tagName))continue;if(seen){if(seen.has(e))continue;seen.add(e)}if(!CTL.test(e.tagName)&&!own(e))continue;"
          "var k=pathOf(e),v=PC[k];if(!v){c=getComputedStyle(e);v=PC[k]=[parseFloat(c.fontSize)||L[2],parseInt(c.fontWeight,10)||400,/mono|consolas|courier|menlo/i.test(c.fontFamily),c.fontFamily!==B]}R.push([e,v])}\n"
          " for(i=0;i<R.length;i++){var r=R[i],v2=r[1],s=lv(v2[0]),w=v2[1]>=600?'@WB@':'@WN@',st=r[0].style;if(Math.abs(v2[0]-s)>0.01)st.fontSize=s+'px';"
          "if(String(v2[1])!==w)st.fontWeight=w;if(v2[2])st.fontFamily='var(--via-mono)';else if(v2[3])st.fontFamily='var(--via-font)'}}\n"
          "function tables(){var d=document,i,x;if(STACK){var st=d.querySelectorAll(SIDE.split(',').map(function(s){return s.trim()+' table'}).join(','));"
          "for(i=0;i<st.length;i++){if(st[i].querySelector('input,select,textarea,button'))st[i].classList.add('via-stack')}}\n"
          " var tl=d.querySelectorAll('table:not([data-via-t])'),css='';for(i=0;i<tl.length;i++){var T=tl[i];TN++;T.setAttribute('data-via-t',TN);if(T.classList.contains('via-stack'))continue;"
          "var rs=[].slice.call(T.rows,0,60);if(T.querySelector('[colspan]')){var cl=T.querySelectorAll('td,th');for(var u=0;u<cl.length;u++){x=cl[u];x.classList.add((x.textContent||'').trim().length<=NW?'via-nw':'via-long')}continue}"
          "var mx=[];rs.forEach(function(r){for(var q=0;q<r.cells.length;q++){var n=(r.cells[q].textContent||'').trim().length;if(!(mx[q]>=n))mx[q]=n}});"
          "mx.forEach(function(n,q){var sel='table[data-via-t=\"'+TN+'\"]>*>tr>:nth-child('+(q+1)+')';css+=n<=NW?sel+'{white-space:nowrap}':sel+'{max-width:@LONG@ch;overflow-wrap:anywhere}'})}"
          "if(css){var se=d.createElement('style');se.className='via-cols';se.textContent=css;d.head.appendChild(se)}\n"
          " if(SCROLL){var tb=d.querySelectorAll('table');for(i=0;i<tb.length;i++){var t=tb[i],p=t.parentElement;"
          "if(!p||t.closest(SIDE)||p.classList.contains('via-scroll'))continue;"
          "if(t.scrollWidth>p.clientWidth+1){var w=d.createElement('div');w.className='via-scroll';p.insertBefore(w,t);w.appendChild(t)}}}}\n"
          "var RX=/^\\d{4}-\\d{2}-\\d{2}$/,NOTXT='script,style,code,pre,kbd,samp,textarea,.cmd,.mono,[data-cmd],[data-l121cmd]';\n"
          "function p2(n){n=String(n);return n.length<2?'0'+n:n}\n"
          "function ok(y,m,dd){m=+m;dd=+dd;return m>=1&&m<=12&&dd>=1&&dd<=31}\n"
          "function iso(v){v=String(v||'').trim();var m=v.match(/^((?:19|20)\\d{2})\\s*[-\\/.年]\\s*(\\d{1,2})\\s*[-\\/.月]\\s*(\\d{1,2})\\s*日?$/);"
          "return m&&ok(m[1],m[2],m[3])?m[1]+'-'+p2(m[2])+'-'+p2(m[3]):''}\n"
          "function fix(t){return t.replace(/((?:19|20)\\d{2})(\\/|\\.|年|-)(\\d{1,2})(?:\\2|月)(\\d{1,2})(日)?(?![\\d.])/g,function(all,y,sep,m,dd){"
          "if(sep==='-'&&m.length===2&&dd.length===2)return all;return ok(y,m,dd)?y+'-'+p2(m)+'-'+p2(dd):all})}\n"
          "function dates(){var d=document,i,x,ins=d.querySelectorAll('input[type=date]:not(.via-cal-p)');for(i=0;i<ins.length;i++){x=ins[i];"
          "var v=x.value;x.type='text';x.value=v;x.placeholder='YYYY-MM-DD';x.setAttribute('pattern','\\\\d{4}-\\\\d{2}-\\\\d{2}');x.setAttribute('inputmode','numeric');x.maxLength=10;"
          "x.addEventListener('blur',function(){var z=iso(this.value);if(z)this.value=z;this.setAttribute('aria-invalid',(!this.value||RX.test(this.value))?'false':'true')});"
          "var w=d.createElement('span'),b=d.createElement('button');w.className='via-date';b.type='button';b.className='via-cal';b.title='選日期(滑鼠)· 存成 YYYY-MM-DD';"
          "b.textContent='\\uD83D\\uDCC5';x.parentNode.insertBefore(w,x);w.appendChild(x);w.appendChild(b);"
          "b.addEventListener('click',(function(t){return function(){var q=d.createElement('input');q.type='date';q.className='via-cal-p';q.value=RX.test(t.value)?t.value:'';"
          "t.parentNode.appendChild(q);q.addEventListener('change',function(){if(q.value){t.value=q.value;t.setAttribute('aria-invalid','false');"
          "t.dispatchEvent(new Event('input',{bubbles:true}));t.dispatchEvent(new Event('change',{bubbles:true}))}if(q.parentNode)q.parentNode.removeChild(q)});"
          "q.addEventListener('blur',function(){setTimeout(function(){if(q.parentNode)q.parentNode.removeChild(q)},400)});"
          "if(q.showPicker){try{q.showPicker()}catch(e){q.focus()}}else{q.focus()}}})(x))}\n"
          " var tw=d.createTreeWalker(d.body,NodeFilter.SHOW_TEXT,null),n,L2=[];while((n=tw.nextNode())){if(seen&&seen.has(n))continue;if(seen)seen.add(n);"
          "var pe=n.parentElement;if(!pe||pe.closest(NOTXT))continue;if(/(?:19|20)\\d{2}[\\/.年-]\\d/.test(n.nodeValue))L2.push(n)}"
          "for(i=0;i<L2.length;i++){var nv=fix(L2[i].nodeValue);if(nv!==L2[i].nodeValue)L2[i].nodeValue=nv}}\n"
          "var SEV={RED:0,FAIL:0,'紅':0,YELLOW:1,WARN:1,'黃':1,GREEN:2,OK:2,PASS:2,INFO:2,'綠':2,GRAY:3,NODATA:3,'灰':3},GRP=['RED','YELLOW','GREEN','GRAY'],"
          "LW=/^(RED|YELLOW|GREEN|GRAY|NODATA|INFO|OK|PASS|FAIL|WARN|紅|黃|綠|灰)$/,BARMIN=@BARMIN@,LRATIO=@LRATIO@,PATHMIN=@PATHMIN@,OWNF=null;\n"
          "function cellLamp(c){var e=c.querySelector('.lp');if(e){var m=String(e.className).match(/\\b(RED|YELLOW|GREEN|GRAY|NODATA)\\b/);if(m)return m[1]}"
          "var t=(c.textContent||'').trim().toUpperCase();return LW.test(t)?t:null}\n"
          "function lampText(t){return t.replace(/\\{\\s*\"RED\"\\s*:\\s*(\\d+)\\s*,\\s*\"YELLOW\"\\s*:\\s*(\\d+)\\s*,\\s*\"GREEN\"\\s*:\\s*(\\d+)(?:\\s*,\\s*\"INFO\"\\s*:\\s*(\\d+))?\\s*\\}/g,"
          "function(a,r,y,g,i){return '紅 '+r+' · 黃 '+y+' · 綠 '+g+(i!==undefined?' · 資訊 '+i:'')})}\n"
          "function present(){var d=document,i,q;if(OWNF===null){OWNF=false;var bb=d.querySelectorAll('button');for(i=0;i<bb.length;i++){if(/只看(紅|黃)/.test(bb[i].textContent||'')){OWNF=true;break}}}\n"
          " var tds=d.getElementsByTagName('td');for(i=0;i<tds.length;i++){var c=tds[i];if(seenT){if(seenT.has(c))continue;seenT.add(c)}if(c.children.length)continue;var t=(c.textContent||'').trim();"
          "if(/^(NaN|nan|None|null|undefined|NaT)$/.test(t)){c.textContent='\\u2014';c.classList.add('via-empty')}"
          "else if(t.length>=PATHMIN&&/^(?:[A-Za-z]:[\\\\\\/]|\\/)[^\\n]*[\\\\\\/][^\\\\\\/\\n]+$/.test(t)){c.title=t;c.textContent=t.replace(/^.*[\\\\\\/]/,'');c.classList.add('via-path')}}\n"
          " var tw=d.createTreeWalker(d.body,NodeFilter.SHOW_TEXT,null),n,L3=[];while((n=tw.nextNode())){if(n.nodeValue.indexOf('\"RED\"')>=0&&!(n.parentElement&&n.parentElement.closest(NOTXT)))L3.push(n)}"
          "for(i=0;i<L3.length;i++){var nv=lampText(L3[i].nodeValue);if(nv!==L3[i].nodeValue)L3[i].nodeValue=nv}\n"
          " var tbs=d.querySelectorAll('table:not([data-via-present])');for(i=0;i<tbs.length;i++){var tb=tbs[i];tb.setAttribute('data-via-present','1');"
          "if(tb.classList.contains('via-stack')||tb.getAttribute('data-via-sort')==='off'||tb.querySelector('[rowspan],[colspan]'))continue;var body=tb.tBodies[0];if(!body)continue;"
          "var rows=[].slice.call(body.rows).filter(function(r){return !r.querySelector('th')});if(rows.length<2)continue;var cols={},info=[];\n"
          " var smp=rows.slice(0,40);smp.forEach(function(r){for(q=0;q<r.cells.length;q++){if(cellLamp(r.cells[q]))cols[q]=(cols[q]||0)+1}});"
          "var lc=Object.keys(cols).filter(function(k){return cols[k]>=smp.length*LRATIO}).map(Number);\n"
          " rows.forEach(function(r,k){var best=9,dl=r.getAttribute('data-l');if(dl&&SEV[dl]!==undefined)best=SEV[dl];for(var z=0;z<lc.length;z++){var cc=r.cells[lc[z]];"
          "var L=cc?cellLamp(cc):null;if(L&&SEV[L]<best)best=SEV[L]}info.push({r:r,k:k,s:best})});\n"
          " if(info.filter(function(x){return x.s<9}).length<rows.length*LRATIO)continue;"
          "if(lc.length===1&&lc[0]>0){var ci=lc[0];[].slice.call(tb.rows).forEach(function(r){if(r.cells.length>ci)r.insertBefore(r.cells[ci],r.cells[0])})}\n"
          " var srt=true;info.forEach(function(x,k){x.r.setAttribute('data-via-l',x.s<9?GRP[x.s]:'');if(k&&info[k-1].s>x.s)srt=false});if(!srt){info.sort(function(a,b){return a.s-b.s||a.k-b.k});"
          "var fr=d.createDocumentFragment();info.forEach(function(x){fr.appendChild(x.r)});body.appendChild(fr)}\n"
          " if(rows.length>=BARMIN&&!OWNF){var cn=[0,0,0,0];info.forEach(function(x){if(x.s<4)cn[x.s]++});var bar=d.createElement('div');bar.className='via-lampbar';"
          "bar.innerHTML='<span><span class=\"via-dot RED\"></span>紅 <b>'+cn[0]+'</b></span><span><span class=\"via-dot YELLOW\"></span>黃 <b>'+cn[1]+'</b></span>'"
          "+'<span><span class=\"via-dot GREEN\"></span>綠 <b>'+cn[2]+'</b></span><span><span class=\"via-dot GRAY\"></span>灰 <b>'+cn[3]+'</b></span><span>共 '+rows.length+' 列 · 問題在前</span>'"
          "+'<button type=\"button\" class=\"via-only\">只看紅黃</button>';tb.parentNode.insertBefore(bar,tb);"
          "bar.querySelector('.via-only').addEventListener('click',(function(t){return function(){var on=t.classList.toggle('via-issues');this.textContent=on?'全部':'只看紅黃'}})(tb))}}}\n"
          "function pick(){var m=new RegExp('@PICK@=([^&]+)').exec(location.hash||'');if(!m)return;var w=decodeURIComponent(m[1]),bs=document.querySelectorAll('button,a');"
          "for(var i=0;i<bs.length;i++){if((bs[i].textContent||'').trim()===w){bs[i].click();break}}}\n"
          "function run(){if(busy||!document.body||document.body.getAttribute('data-via-typekit')==='off')return;busy=true;"
          "try{snap();dates();present();tables()}finally{busy=false}}\n"
          "function watch(){if(typeof MutationObserver==='undefined'||!document.body)return;var tm=null;new MutationObserver(function(){"
          "if(tm)return;tm=setTimeout(function(){tm=null;run()},120)}).observe(document.body,{childList:true,subtree:true})}\n"
          "function go(){run();watch();window.addEventListener('load',function(){run();pick()})}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go()})();\n")


def _tk_vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def typekit_book(root=None) -> dict:
    """→ {tokens, auto, book, why}:讀 registry 的 VIA_UI_Template_SSOT 尾版;冊讀不到 / 沒有字級 token → 內建同一份預設,並寫明原因。"""
    root = Path(root or TK_ROOT)
    hits = sorted((root / "supportive modules" / "registry").glob("VIA_UI_Template_SSOT_v*.json"), key=_tk_vnum)
    tok, auto, name, why = dict(TK_DEFAULT_TOKENS), dict(TK_DEFAULT_AUTO), None, "找不到 VIA_UI_Template_SSOT_v*.json,字級用內建預設"
    pres = dict(TK_DEFAULT_PRESENT)
    if hits:
        name = hits[-1].name
        try:
            d = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
            bt = d.get("tokens") or {}
            why = None if all(k in bt for k in ("fs-title", "fs-h", "fs", "fs-note")) else "%s 沒有字級 token(fs-title / fs-h / fs / fs-note),字級用內建預設" % name
            tok.update({k: str(v) for k, v in bt.items() if k in TK_DEFAULT_TOKENS})
            auto.update({k: v for k, v in (d.get("auto_layout") or {}).items() if k in TK_DEFAULT_AUTO})
            pres.update({k: v for k, v in (d.get("presentation") or {}).items() if k in TK_DEFAULT_PRESENT})
        except (OSError, ValueError, AttributeError) as exc:
            why = "讀不了 %s:%s,字級用內建預設" % (name, type(exc).__name__)
    return {"tokens": tok, "auto": auto, "present": pres, "book": name, "why": why}


def _tk_num(v, dflt: float) -> float:
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(v))
    return float(m.group(1)) if m else dflt


def _tk_safe(v) -> str:
    return re.sub(r"[<>{};\\]", "", str(v))


def typekit_block(tk=None) -> str:
    """→ 一段可插進任何頁的字級套件(<!--via-typekit:begin--> … <!--via-typekit:end-->)。"""
    tk = tk or typekit_book()
    t, a = tk["tokens"], tk["auto"]
    sides = [s.strip() for s in str(a.get("side_selectors") or "aside").split(",") if re.fullmatch(r"[A-Za-z.#][A-Za-z0-9_.#-]*", s.strip())] or ["aside"]
    lv = [_tk_num(t.get(k), dv) for k, dv in (("fs-title", 16), ("fs-h", 13), ("fs", 12), ("fs-note", 11))]
    rep = {"@FONT@": _tk_safe(t["font"]), "@MONO@": _tk_safe(t["mono"]), "@T1@": "%g" % lv[0], "@T2@": "%g" % lv[1], "@T3@": "%g" % lv[2],
           "@T4@": "%g" % lv[3], "@LH@": "%g" % _tk_num(t.get("lh"), 1.45), "@WB@": "%d" % _tk_num(t.get("w-bold"), 700),
           "@WN@": "%d" % _tk_num(t.get("w-normal"), 400), "@LINE@": _tk_safe(t.get("line") or "#e0e0e0"),
           "@LONG@": "%d" % _tk_num(a.get("cell_long_max_ch"), 48), "@NW@": "%d" % _tk_num(a.get("cell_nowrap_max_chars"), 24),
           "@SCROLL@": "true" if a.get("wide_table_scroll") else "false", "@STACK@": "true" if a.get("stack_side_tables_with_controls") else "false",
           "@SIDE@": ",".join(sides), "@SIDECARD@": ",".join(s + " .card" for s in sides)}
    pr = dict(TK_DEFAULT_PRESENT)
    pr.update(tk.get("present") or {})
    rep.update({"@BARMIN@": "%d" % _tk_num(pr.get("bar_min_rows"), 8), "@LRATIO@": "%g" % _tk_num(pr.get("lamp_ratio"), 0.6),
                "@PATHMIN@": "%d" % _tk_num(pr.get("path_min_len"), 40), "@PICK@": re.sub(r"[^a-z-]", "", str(pr.get("pick_hash") or "via-pick")) or "via-pick"})
    css, js = _TK_CSS, _TK_JS
    for k, v in rep.items():
        css, js = css.replace(k, v), js.replace(k, v)
    return ('<!--via-typekit:begin %s-->\n<style id="via-typekit">\n%s</style>\n<script id="via-typekit-js">\n%s</script>\n<!--via-typekit:end-->'
            % (_tk_safe(tk.get("book") or "內建預設"), css, js))


def typekit_apply_text(h: str, block: str) -> tuple:
    """→ (新頁, inserted / replaced / same)。已套過就換成新的一段(冊換 token 跟著換),不重複插。"""
    if _TK_RE.search(h):
        new = _TK_RE.sub(lambda _m: block, h, count=1)
        return new, ("same" if new == h else "replaced")
    heads = list(re.finditer(r"</head\s*>", h, re.I))
    if heads:
        i = heads[-1].start()
        return h[:i] + block + "\n" + h[i:], "inserted"
    m = re.search(r"<body[^>]*>", h, re.I)
    if m:
        return h[:m.end()] + block + h[m.end():], "inserted"
    return block + h, "inserted"


def typekit_apply(page, tk=None) -> dict:
    page = Path(page)
    if not page.is_file():
        return {"page": page.name, "how": "missing"}
    try:
        h = page.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"page": page.name, "how": "not-utf8"}
    new, how = typekit_apply_text(h, typekit_block(tk))
    if new != h:
        page.write_text(new, encoding="utf-8")
    return {"page": page.name, "how": how}


def typekit_dir(out_dir, tk=None) -> dict:
    """只動 out_dir 直下的 *_latest.html(本系統自己的頁);子夾 · 他系統的夾不碰。"""
    tk = tk or typekit_book()
    rows = [typekit_apply(p, tk) for p in sorted(Path(out_dir).glob("*_latest.html"))] if Path(out_dir).is_dir() else []
    return {"book": tk.get("book"), "why": tk.get("why"), "rows": rows,
            "changed": sum(1 for r in rows if r["how"] in ("inserted", "replaced")), "n": len(rows)}


PRIOR.typekit_book = typekit_book            # 前版 v0105 build → 走本版 v2 套件
PRIOR.typekit_block = typekit_block
PRIOR.typekit_apply = typekit_apply


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)

def _v2_checks(chk, tk, blk):
    pr = tk.get("present") or {}
    chk("① 冊尾版有 presentation 節:燈號列門檻 8 列 · 燈欄比例 0.6 · 路徑 40 字 · 預選 via-pick(冊 %s)" % tk.get("book"),
        tk.get("book") and not tk.get("why") and pr.get("bar_min_rows") == 8 and pr.get("lamp_ratio") == 0.6 and pr.get("path_min_len") == 40
        and pr.get("pick_hash") == "via-pick", tk)
    chk("② 套件 v2:燈欄第一 · 問題在前 · 燈號列 · 空值 — · 路徑縮檔名 · 燈號 JSON 改人話 · #via-pick · 換行一欄一條;門檻來自冊;仍只一段 style + 一段 script · 零外部連結",
        all(x in blk for x in ("function present(", "function pick(", "function lampText(", "BARMIN=8", "LRATIO=0.6", "PATHMIN=40", "via-pick=", "data-via-t", "via-lampbar",
                               "placeholder='YYYY-MM-DD'", "MutationObserver")) and blk.count("<style") == 1 and blk.count("<script") == 1
        and not re.search(r"https?://(?!www\.w3\.org/1999/xhtml)|<link|\bsrc=|@import|fetch\(", blk))
    old = ('<html><head><style>b{}</style><!--via-typekit:begin v0101-->\n<style id="via-typekit">x</style>\n<script id="via-typekit-js">y</script>\n'
           '<!--via-typekit:end--></head><body><b>x</b></body></html>')
    new, how = typekit_apply_text(old, blk)
    chk("③ 頁上舊版套件(v1)→ 換成 v2,仍只一段(冪等換新,不疊加)",
        how == "replaced" and new.count("via-typekit:begin") == 1 and "function present(" in new and typekit_apply_text(new, blk)[1] == "same")


def selftest() -> int:
    import shutil
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print(f"  [OK] {name}")
        else:
            f += 1
            print(f"  [FAIL] {name}" + (f" · {str(note)[:300]}" if note else ""))

    print(f"=== {TAG} · 薄尾自測(展現規則:操作台)===")
    tk = typekit_book()
    blk = typekit_block(tk)
    _v2_checks(chk, tk, blk)
    chk("④ 前版 v0105 build 已改走本版套件:typekit_book · typekit_block · typekit_apply 換成 v0106",
        PRIOR.typekit_apply is typekit_apply and PRIOR.typekit_block is typekit_block and PRIOR.typekit_book is typekit_book)
    tmp = Path(tempfile.mkdtemp(prefix="mdl261v6_"))
    keep_wd = (BASE.WORK_DIR, BASE.WORK_CONFIG)
    try:
        BASE.WORK_DIR = tmp / "work"
        BASE.WORK_CONFIG = BASE.WORK_DIR / "ui_config.json"
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        cfg = BASE.load_config(sets=[f"locations.db_root={home}"])
        with contextlib.redirect_stdout(io.StringIO()):
            snap, out, rep = BASE.build(cfg, home, tmp / "ui" / "page.html")
        r1 = typekit_apply(out, tk)
        page = out.read_text(encoding="utf-8")
        chk("⑤ 真建頁(v0104 範本 + 快照)→ 套件 v2 只一段 · 左下 GATE · 三系統仍在 · 閘戳 slice(0,16)",
            r1["how"] == "inserted" and page.count("via-typekit:begin") == 1 and "function present(" in page and 'id="gates3"' in page
            and "String(g.ts).slice(0,16)" in page, r1)
    finally:
        BASE.WORK_DIR, BASE.WORK_CONFIG = keep_wd
        shutil.rmtree(tmp, ignore_errors=True)
    text = Path(__file__).read_text(encoding="utf-8")
    import ast
    chk("⑥ 檔頭:加速器橋 · 網路橋在(__future__ 之後);不碰 TA-Lib;不直派子行程;不載外部函式庫",
        "[VIA:ACCEL-BRIDGE:" in text and "[VIA:NET-BRIDGE:" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in text and "cdn" + "js" not in text and "unp" + "kg.com" not in text
        and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.name or "").split(".")[0] == "sub" + "process" for x in n.names) for n in ast.walk(ast.parse(text))))
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        prior_rc = 0
        print("  ── 前版鏈自測略過(VIA_SKIP_PRIOR_SELFTEST=1)──")
    else:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
        print("  ── 前版鏈自測(摘末行)── " + (buf.getvalue().strip().splitlines() or ["(無輸出)"])[-1])
    chk(f"⑦ 前版鏈 {PRIOR_PATH.stem} 自測 rc 0", prior_rc == 0)
    print(f"[計] {TAG} 本版 {p}/{p + f} · {'PASS' if f == 0 else 'FAIL'}")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
