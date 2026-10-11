#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0153 — 薄尾:VDF 頁字體 / 階層一致 + 版面自動最佳化(字級套件)

操作員令(2026-10-11):「u/i請字體一致或階層一致姓  左右面板都凌亂」「很多展現都要重新思考整理」。
  容器實測(改前):VDF 頁左面板 4 種字級(11 / 11.5 / 12 / 12.5px)+ Arial 混用(按鈕 / 輸入框不繼承字體);「改整族」欄被擠成
  直排字、表格超出卡片;右側全景頁窄欄逐字換行,每列 61px 大量留白;表頭彙整 / 全景頁各 5–6 種字級 3 種字體。
  ① 字級套件:讀 registry 的 VIA_UI_Template_SSOT 尾版(v0101 起有字級 token;只讀資料冊)→ 頁內一段 CSS + 一小段 JS:
     四級字(標題 / 段頭 / 內文 / 註記)· 兩種字重 · 一種主字體(等寬只給指令與代碼)· 按鈕輸入框繼承字體;
     頁上任何字級吸到最近一級(之後 JS 產的內容也跟,MutationObserver 只處理新元素)。
  ② 自動版面:短欄不換行 · 長欄限寬 · 寬表外包橫捲 · 左面板有輸入框 / 按鈕的表改兩行一列(名稱一行;輸入 + 按鈕一行)。
     純 CSS(Grid / Flex)+ 頁內小段 JS;不連網、不裝套件、不載外部函式庫。
  ③ 範圍:只動 VDF 自己的頁 —— VIA_Reports/vdf/ 直下的 *_latest.html(ui 套完 L121 後套;其他動詞跑完也補套;冪等;冊換 token 就換新);
     他系統的頁(VCGC 健康矩陣 · VRN)不碰(L120),由各自的 manager 照同一本冊套。
  ④ 冊讀不到 / 沒有字級 token → 內建同一份預設照常套,並寫明原因;頁 body 加 data-via-typekit="off" 可關。
  ⑤ 日期一律 YYYY-MM-DD(操作員 2026-10-11「日期規格一慮用YYYY-MM-DD」):日期框(瀏覽器依語系顯示 01/01/2015)改成 YYYY-MM-DD 文字框 + 日曆鈕
     (滑鼠選日照用,L118);頁上 2026/10/11 · 2026.10.11 · 2026年10月11日 · 2026-1-5 改寫成 YYYY-MM-DD;左下閘戳時間 MM-DD HH:MM → YYYY-MM-DD HH:MM。
     指令 / 代碼 / 檔名 / 代號裡的日期(例 20260928_050809)不動。
其餘照 v0152(L121 版面)。只收 VIA_FROM_VCGC=YES(舊名;= 經任一系統自己的 manager / 啟動器啟動,L120 ⑥ 甲)。不抓網、不碰 TA-Lib。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====


import datetime
import html
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
TK_ROOT = VIA_ROOT
_STEM = "VDF_SystemManager"
TAG = "v0153"
SELF_ID = "VDF"


def _vnum_v0153(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0153(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0153(p) < _vnum_v0153(__file__)), key=_vnum_v0153)
PRIOR = _load_v0153(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _stamp_v0153(x: dict, root: Path, page_dir: Path) -> dict:
    """閘戳時間一律 YYYY-MM-DD HH:MM(操作員 2026-10-11「日期規格一慮用YYYY-MM-DD」;v0152 是 MM-DD HH:MM,沒有年)。"""
    p = root / (x.get("file") or "")
    ok = bool(x.get("file")) and p.is_file()
    return {**x, "exists": ok, "href": PRIOR._href(p, page_dir) if ok else None,
            "ts": datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if ok else None}


PRIOR._stamp = _stamp_v0153                 # v0152 的 three_systems 用模組全域 _stamp → 本版的日期格式


def _out_dir() -> Path:
    return Path(os.environ.get("VIA_VDF_HEALTH_OUT") or (Path(os.environ.get("VIA_VDF_HOME") or HERE).parents[1] / "VIA_Reports" / "vdf"))


# ---------- 字級套件(VIA_UI_Template_SSOT 尾版的字級 token → 頁內一段 CSS + 一小段 JS;只讀冊 · 不連網 · 不載外部庫) ----------
TK_DEFAULT_TOKENS = {
    "font": '"Microsoft JhengHei UI","Microsoft JhengHei","PingFang TC","Noto Sans TC","Noto Sans CJK TC","Segoe UI",sans-serif',
    "mono": 'Consolas,"Cascadia Mono","Noto Sans Mono","DejaVu Sans Mono",monospace',
    "fs-title": "16px", "fs-h": "13px", "fs": "12px", "fs-note": "11px", "lh": "1.45", "w-normal": "400", "w-bold": "700", "line": "#e0e0e0"}
TK_DEFAULT_AUTO = {"cell_nowrap_max_chars": 24, "cell_long_max_ch": 48, "wide_table_scroll": True,
                   "stack_side_tables_with_controls": True, "side_selectors": "aside, .side"}
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
           ".via-cal{padding:0 6px;margin:0;cursor:pointer}.via-cal-p{width:auto}input[aria-invalid=true]{border-color:#dc2626;outline:1px solid #dc2626}\n")
_TK_JS = ("(function(){var L=[@T1@,@T2@,@T3@,@T4@],NW=@NW@,SCROLL=@SCROLL@,STACK=@STACK@,SIDE='@SIDE@',HN='http://www.w3.org/1999/xhtml',"
          "SKIP=/^(SCRIPT|STYLE|IFRAME|BR|HR|CANVAS|IMG|VIDEO|AUDIO|NOSCRIPT|TEMPLATE|OPTION)$/,CTL=/^(INPUT|SELECT|TEXTAREA|BUTTON)$/,seen=(typeof WeakSet!=='undefined')?new WeakSet():null,busy=false;\n"
          "function lv(p){return p>=(L[0]+L[1])/2?L[0]:p>=(L[1]+L[2])/2?L[1]:p>=(L[2]+L[3])/2?L[2]:L[3]}\n"
          "function own(e){for(var n=e.firstChild;n;n=n.nextSibling){if(n.nodeType===3&&/\\S/.test(n.nodeValue))return true}return false}\n"
          "function snap(){var a=document.body.getElementsByTagName('*'),R=[],i,e,c,B=getComputedStyle(document.body).fontFamily;for(i=0;i<a.length;i++){e=a[i];"
          "if(e.namespaceURI!==HN||SKIP.test(e.tagName))continue;if(seen){if(seen.has(e))continue;seen.add(e)}if(!CTL.test(e.tagName)&&!own(e))continue;"
          "c=getComputedStyle(e);R.push([e,parseFloat(c.fontSize)||L[2],parseInt(c.fontWeight,10)||400,/mono|consolas|courier|menlo/i.test(c.fontFamily),c.fontFamily])}\n"
          " for(i=0;i<R.length;i++){var r=R[i],s=lv(r[1]),w=r[2]>=600?'@WB@':'@WN@';if(Math.abs(r[1]-s)>0.01)r[0].style.fontSize=s+'px';"
          "if(String(r[2])!==w)r[0].style.fontWeight=w;if(r[3])r[0].style.fontFamily='var(--via-mono)';else if(r[4]!==B)r[0].style.fontFamily='var(--via-font)'}}\n"
          "function tables(){var d=document,i,x;if(STACK){var st=d.querySelectorAll(SIDE.split(',').map(function(s){return s.trim()+' table'}).join(','));"
          "for(i=0;i<st.length;i++){if(st[i].querySelector('input,select,textarea,button'))st[i].classList.add('via-stack')}}\n"
          " var cl=d.querySelectorAll('td:not(.via-nw):not(.via-long),th:not(.via-nw):not(.via-long)');for(i=0;i<cl.length;i++){x=cl[i];"
          "if(x.closest('table.via-stack'))continue;x.classList.add((x.textContent||'').trim().length<=NW?'via-nw':'via-long')}\n"
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
          "function run(){if(busy||!document.body||document.body.getAttribute('data-via-typekit')==='off')return;busy=true;"
          "try{snap();dates();tables()}finally{busy=false}}\n"
          "function watch(){if(typeof MutationObserver==='undefined'||!document.body)return;var tm=null;new MutationObserver(function(){"
          "if(tm)return;tm=setTimeout(function(){tm=null;run()},120)}).observe(document.body,{childList:true,subtree:true})}\n"
          "function go(){run();watch();window.addEventListener('load',run)}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go()})();\n")


def _tk_vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def typekit_book(root=None) -> dict:
    """→ {tokens, auto, book, why}:讀 registry 的 VIA_UI_Template_SSOT 尾版;冊讀不到 / 沒有字級 token → 內建同一份預設,並寫明原因。"""
    root = Path(root or TK_ROOT)
    hits = sorted((root / "supportive modules" / "registry").glob("VIA_UI_Template_SSOT_v*.json"), key=_tk_vnum)
    tok, auto, name, why = dict(TK_DEFAULT_TOKENS), dict(TK_DEFAULT_AUTO), None, "找不到 VIA_UI_Template_SSOT_v*.json,字級用內建預設"
    if hits:
        name = hits[-1].name
        try:
            d = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
            bt = d.get("tokens") or {}
            why = None if all(k in bt for k in ("fs-title", "fs-h", "fs", "fs-note")) else "%s 沒有字級 token(fs-title / fs-h / fs / fs-note),字級用內建預設" % name
            tok.update({k: str(v) for k, v in bt.items() if k in TK_DEFAULT_TOKENS})
            auto.update({k: v for k, v in (d.get("auto_layout") or {}).items() if k in TK_DEFAULT_AUTO})
        except (OSError, ValueError, AttributeError) as exc:
            why = "讀不了 %s:%s,字級用內建預設" % (name, type(exc).__name__)
    return {"tokens": tok, "auto": auto, "book": name, "why": why}


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


def _manifest_typekit(page: Path, r: dict) -> None:
    mp = page.parent / (SELF_ID + "_UI_MANIFEST.json")
    try:
        m = json.loads(mp.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("  [字級] 清單 %s 沒更新(%s)" % (mp.name, type(exc).__name__))
        return
    m.update({"typekit": {"book": r.get("book"), "why": r.get("why"), "pages": r.get("n"), "changed": r.get("changed"),
                          "levels": "fs-title / fs-h / fs / fs-note", "manager": Path(__file__).name}})
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")


def _say(r: dict) -> str:
    return "冊 %s%s · VDF 頁 %d 支(新套 / 換新 %d)" % (r.get("book") or "內建預設", (" · " + r["why"]) if r.get("why") else "", r.get("n", 0), r.get("changed", 0))


def ui_typekit(args) -> int:
    want_open = os.environ.get("VIA_NO_OPEN") != "1"
    keep = os.environ.get("VIA_NO_OPEN")
    os.environ["VIA_NO_OPEN"] = "1"          # 先不開:前版鏈產頁 + L121 套版 + 字級套件都套完再開
    try:
        rc = PRIOR.main(args)
    finally:
        if keep is None:
            os.environ.pop("VIA_NO_OPEN", None)
        else:
            os.environ["VIA_NO_OPEN"] = keep
    out = _out_dir()
    r = typekit_dir(out)
    page = out / (SELF_ID + "_UI_latest.html")
    if page.is_file():
        _manifest_typekit(page, r)
    opened = PRIOR._open(page) if (want_open and page.is_file()) else False
    lamp = "GREEN" if (page.is_file() and not r.get("why")) else "YELLOW"
    print("[計] %s ui %s · 字級套件(四級字 · 兩種字重 · 一種主字體 · 短欄不換行 · 寬表橫捲 · 左面板表兩行一列)· %s · %s%s" % (
        SELF_ID, TAG, _say(r), lamp, " · 已開頁" if opened else ""))
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["ui"]:
        return ui_typekit(args)
    rc = PRIOR.main(args)
    if args and not args[0].startswith("-"):
        r = typekit_dir(_out_dir())
        if r["changed"]:
            print("  [字級] %s 動詞 %s 跑完補套 · %s" % (SELF_ID, args[0], _say(r)))
    return rc


_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>body{font:11.5px Arial}</style></head>
<body><header><h1>X</h1></header><aside><div class='card'><table><tr><td>A</td><td><input value='1'></td><td><button>改</button></td></tr></table></div></aside>
<main><table><tr><td>短</td><td>一段很長很長很長很長很長很長很長很長很長很長很長很長的說明</td></tr></table></main></body></html>"""


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 薄尾自測(字級套件:字體 / 階層一致 + 版面自動最佳化)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="tk_" + SELF_ID.lower() + "_"))
    keep = {k: os.environ.get(k) for k in ("VIA_NO_OPEN", "VIA_VDF_HEALTH_OUT")}
    try:
        tk = typekit_book()
        t = tk["tokens"]
        chk("① 冊尾版有字級 token:四級 16 / 13 / 12 / 11 · 字重 400 / 700 · 主字體微軟正黑體(冊 %s)" % tk.get("book"),
            tk.get("book") and not tk.get("why") and [t["fs-title"], t["fs-h"], t["fs"], t["fs-note"]] == ["16px", "13px", "12px", "11px"]
            and t["w-normal"] == "400" and t["w-bold"] == "700" and t["font"].startswith('"Microsoft JhengHei UI"'), tk)
        old = td / "old" / "supportive modules" / "registry"
        old.mkdir(parents=True)
        (old / "VIA_UI_Template_SSOT_v0100.json").write_text(json.dumps({"tokens": {"font": "Foo", "fs": "12px"}}), encoding="utf-8")
        bad = td / "bad" / "supportive modules" / "registry"
        bad.mkdir(parents=True)
        (bad / "VIA_UI_Template_SSOT_v0100.json").write_text("{x", encoding="utf-8")
        fb = [typekit_book(td / "none"), typekit_book(td / "old"), typekit_book(td / "bad")]
        chk("② 冊讀不到 / 只有顏色沒字級 / 壞 JSON → 內建同一份預設照常套,並寫明原因(冊有的字體照用)",
            all(x["why"] and x["tokens"]["fs-title"] == "16px" for x in fb) and fb[1]["tokens"]["font"] == "Foo", [x["why"] for x in fb])
        blk = typekit_block(tk)
        chk("③ 套件:四級 px 都在 · 字體來自冊 · 按鈕輸入框繼承字體 · 只有一段 style + 一段 script · 零外部連結 · 可關(data-via-typekit=off)· 後長內容照吸附",
            all(("--via-t%d:%spx" % (i + 1, v)) in blk for i, v in enumerate(("16", "13", "12", "11"))) and "Microsoft JhengHei UI" in blk
            and "button,input,select,textarea{font-family:inherit" in blk and blk.count("<style") == 1 and blk.count("<script") == 1
            and not re.search(r"https?://(?!www\.w3\.org/1999/xhtml)|<link|\bsrc=|@import|fetch\(", blk)
            and "data-via-typekit" in blk and "MutationObserver" in blk, blk[:200])
        pg = td / "p.html"
        pg.write_text(_PAGE, encoding="utf-8")
        a1, a2 = typekit_apply(pg, tk), typekit_apply(pg, tk)
        h1 = pg.read_text(encoding="utf-8")
        tk2 = json.loads(json.dumps(tk))
        tk2["tokens"]["fs"] = "12.5px"
        a3 = typekit_apply(pg, tk2)
        h3 = pg.read_text(encoding="utf-8")
        chk("④ 冪等:第二次 same · 只有一段;冊換 token → replaced 仍只有一段;插在 </head> 前(在頁自己的 style 之後)",
            (a1["how"], a2["how"], a3["how"]) == ("inserted", "same", "replaced") and h1.count("via-typekit:begin") == 1 and h3.count("via-typekit:begin") == 1
            and "--via-t3:12.5px" in h3 and h1.find("font:11.5px Arial") < h1.find("via-typekit:begin") < h1.find("</head>"), (a1, a2, a3))
        nb = typekit_apply_text("<body><p>x</p></body>", blk)
        nobody = typekit_apply_text("<p>x</p>", blk)
        raw = td / "raw.html"
        raw.write_bytes(b"<html><head></head><body>\xff\xfe</body></html>")
        chk("⑤ 沒有 head → 插在 <body> 後;什麼都沒有 → 放最前;非 UTF-8 → 不動(照實回)",
            nb[0].startswith("<body><!--via-typekit:begin") and nobody[0].startswith("<!--via-typekit:begin") and typekit_apply(raw, tk)["how"] == "not-utf8"
            and raw.read_bytes() == b"<html><head></head><body>\xff\xfe</body></html>")
        own = td / "own"
        (own / "sub").mkdir(parents=True)
        for n in ("A_latest.html", "B_latest.html", "C.html"):
            (own / n).write_text(_PAGE, encoding="utf-8")
        (own / "sub" / "D_latest.html").write_text(_PAGE, encoding="utf-8")
        rd = typekit_dir(own, tk)
        chk("⑥ 範圍:只動本系統輸出夾直下 *_latest.html;子夾 · 非 _latest 不碰",
            rd["n"] == 2 and rd["changed"] == 2 and "via-typekit" not in (own / "C.html").read_text(encoding="utf-8")
            and "via-typekit" not in (own / "sub" / "D_latest.html").read_text(encoding="utf-8"), rd)
        os.environ["VIA_VDF_HEALTH_OUT"] = str(td / "real_out")
        os.environ["VIA_NO_OPEN"] = "1"
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["ui"])
        real = td / "real_out" / (SELF_ID + "_UI_latest.html")
        rh = real.read_text(encoding="utf-8") if real.is_file() else ""
        try:
            man = json.loads((td / "real_out" / (SELF_ID + "_UI_MANIFEST.json")).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            man = {"_err": type(exc).__name__}
        chk("⑦ 真跑 ui(前版鏈產頁 → L121 套版 → 字級套件):rc 0 · 頁有左下 GATE + 字級套件各一 · 清單記 typekit",
            rc == 0 and "id='gates3'" in rh and rh.count("via-typekit:begin") == 1 and (man.get("typekit") or {}).get("book")
            and man.get("layout") == "L121" and "字級套件" in buf.getvalue(), buf.getvalue()[-400:])
        late = td / "real_out" / "LATE_latest.html"
        keep_main = PRIOR.main

        def _fake(a):
            late.write_text(_PAGE, encoding="utf-8")
            return 0
        PRIOR.main = _fake
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rc2 = main(["fake-verb"])
        finally:
            PRIOR.main = keep_main
        chk("⑧ 其他動詞跑完補套:動詞新寫的 VDF 頁也套上(冪等)", rc2 == 0 and late.read_text(encoding="utf-8").count("via-typekit:begin") == 1)
        body = Path(__file__).read_text(encoding="utf-8")
        import ast
        chk("⑨ 橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式(只讀冊)· 不直派子行程 · 不載外部函式庫",
            all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
            and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "261_UIEngine_v" not in body
            and "cdn" + "js" not in body and "unp" + "kg.com" not in body
            and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((a.name or "").split(".")[0] == "sub" + "process" for a in n.names) for n in ast.walk(ast.parse(body))))
        gr = td / "gr"
        (gr / "VIA_Reports" / "ui_engine").mkdir(parents=True)
        (gr / "VIA_Reports" / "ui_engine" / "VIA_UI_Engine_latest.html").write_text("x", encoding="utf-8")
        ts = [g for s in PRIOR.three_systems(SELF_ID, td / "nope.json", gr / "VIA_Reports" / "vdf", gr)["systems"] for g in [s["ui"]] if g.get("exists")]
        chk("⑪ 日期一律 YYYY-MM-DD:閘戳時間 = YYYY-MM-DD HH:MM;套件把日期框改成 YYYY-MM-DD 文字框 + 日曆鈕(滑鼠選日)· 頁上 / . 年月日日期改寫 · 檔名 / 代號不動",
            len(ts) == 1 and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", ts[0]["ts"] or "") and "placeholder='YYYY-MM-DD'" in blk
            and "showPicker" in blk and "function fix(" in blk and "NOTXT=" in blk, ts)
        print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
        chk("⑩ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("[計] %s_%s 自測 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
