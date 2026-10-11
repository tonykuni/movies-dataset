#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL261_UIEngine v0105 — 薄尾:VCGC 操作台字體 / 階層一致 + 版面自動最佳化 + 日期一律 YYYY-MM-DD(字級套件)

操作員令(2026-10-11):「u/i請字體一致或階層一致姓  左右面板都凌亂」「很多展現都要重新思考整理」「日期規格一律用YYYY-MM-DD」。
  ① 字級套件:讀 registry 的 VIA_UI_Template_SSOT 尾版(v0101 起有字級 token;只讀資料冊)→ 頁內一段 CSS + 一小段 JS:
     四級字(標題 / 段頭 / 內文 / 註記)· 兩種字重 · 一種主字體(等寬只給指令與代碼)· 按鈕輸入框繼承字體;頁上任何字級吸到最近一級
     (之後 JS 產的內容也跟,MutationObserver 只處理新元素)。短欄不換行 · 長欄限寬 · 寬表外包橫捲 · 左面板有輸入框 / 按鈕的表兩行一列。
  ② 日期一律 YYYY-MM-DD:日期框改 YYYY-MM-DD 文字框 + 日曆鈕(滑鼠選日照用,L118);頁上 2026/10/11 · 2026.10.11 · 2026年10月11日 · 2026-1-5
     改寫成 YYYY-MM-DD;指令 / 代碼 / 檔名 / 代號裡的日期不動。純 CSS + 頁內小段 JS;不連網、不裝套件、不載外部函式庫。
  ③ 冊讀不到 / 沒有字級 token → 內建同一份預設照常套,並寫明原因;頁 body 加 data-via-typekit="off" 可關。
  ④ 範圍:build 產的操作台頁(先不開 → 套件 → 要開才開);左下 GATE 閘戳時間 MM-DD HH:MM → YYYY-MM-DD HH:MM(範本換段一處)。
其餘照 v0104(L121 三系統統一版面 · 五頁 · 匯入 · 自動跳出)。只讀:不連網、不寫冊;不代跑他系統。只收 VCGC 呼叫。
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
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0105", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE           # v0100 本體:build / inject / BUILTIN / snapshot 在這裡


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"CGC_MDL261_UIEngine v{Path(__file__).stem.rsplit('_v', 1)[-1]}"

# 閘戳時間一律 YYYY-MM-DD HH:MM(操作員 2026-10-11「日期規格一律用YYYY-MM-DD」;v0104 範本是 slice(5,16) = MM-DD HH:MM,沒有年)
_TS_OLD = "String(g.ts).slice(5,16).replace('T',' ')"
_TS_NEW = "String(g.ts).slice(0,16).replace('T',' ')"
PATCH_MISSES_V0105 = [] if PRIOR.BUILTIN_V0104.count(_TS_OLD) == 1 else [_TS_OLD]
BUILTIN_V0105 = PRIOR.BUILTIN_V0104.replace(_TS_OLD, _TS_NEW, 1)
BASE.BUILTIN = BUILTIN_V0105
PRIOR.PRIOR.BUILTIN = BUILTIN_V0105
BASE.TAG = PRIOR.PRIOR.TAG = TAG


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


def _out_path(argv: list) -> Path:
    if "--out" in argv and argv.index("--out") + 1 < len(argv):
        return Path(argv[argv.index("--out") + 1])
    cfg = BASE.load_config()
    return BASE._abs(cfg.get("output", "VIA_Reports/ui_engine/VIA_UI_Engine_latest.html"), BASE.default_home())


def cmd_build(argv: list) -> int:
    """build 照前版鏈產頁(先不開)→ 套字級套件 → 要開才開。"""
    want_open = "--open" in argv
    a = [x for x in argv if x != "--open"]
    rc = PRIOR.main(a)
    out = _out_path(a)
    tk = typekit_book()
    r = typekit_apply(out, tk) if rc == 0 else {"page": out.name, "how": "沒套(build rc %s)" % rc}
    print("[ui-engine] 字級套件(四級字 · 兩種字重 · 一種主字體 · 短欄不換行 · 寬表橫捲)· %s · 冊 %s%s" % (
        r["how"], tk.get("book") or "內建預設", (" · " + tk["why"]) if tk.get("why") else ""))
    if want_open and rc == 0:
        print(f"[ui-engine] {PRIOR.open_page(out)} · {out}")
    return rc


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    if argv[:1] == ["build"]:
        return cmd_build(argv)
    return PRIOR.main(argv)


# ---------- 自測 ----------
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

    print(f"=== {TAG} · 薄尾自測(字級套件:操作台字體 / 階層一致 + 版面自動最佳化)===")
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        prior_rc = 0
        print("  ── 前版鏈自測略過(VIA_SKIP_PRIOR_SELFTEST=1)──")
    else:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
        print("  ── 前版鏈自測(摘末行)── " + (buf.getvalue().strip().splitlines() or ["(無輸出)"])[-1])
    chk(f"① 前版鏈 {PRIOR_PATH.stem} 自測 rc 0", prior_rc == 0)
    tk = typekit_book()
    t = tk["tokens"]
    chk(f"② 冊尾版有字級 token:四級 16 / 13 / 12 / 11 · 字重 400 / 700(冊 {tk.get('book')})",
        tk.get("book") and not tk.get("why") and [t["fs-title"], t["fs-h"], t["fs"], t["fs-note"]] == ["16px", "13px", "12px", "11px"]
        and t["w-normal"] == "400" and t["w-bold"] == "700", tk)
    blk = typekit_block(tk)
    chk("③ 套件:四級 px · 按鈕輸入框繼承字體 · 左面板選擇器含操作台的 .side · 一段 style + 一段 script · 零外部連結 · 可關 · 後長內容照吸附",
        all(f"--via-t{i + 1}:{v}px" in blk for i, v in enumerate(("16", "13", "12", "11"))) and "button,input,select,textarea{font-family:inherit" in blk
        and ".side .card" in blk and blk.count("<style") == 1 and blk.count("<script") == 1
        and not re.search(r"https?://(?!www\.w3\.org/1999/xhtml)|<link|\bsrc=|@import|fetch\(", blk) and "data-via-typekit" in blk and "MutationObserver" in blk)
    tmp = Path(tempfile.mkdtemp(prefix="mdl261v5_"))
    keep_wd = (BASE.WORK_DIR, BASE.WORK_CONFIG)
    keep_main, keep_open = PRIOR.main, os.environ.get("VIA_NO_OPEN")
    try:
        BASE.WORK_DIR = tmp / "work"
        BASE.WORK_CONFIG = BASE.WORK_DIR / "ui_config.json"
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        cfg = BASE.load_config(sets=[f"locations.db_root={home}"])
        with contextlib.redirect_stdout(io.StringIO()):
            snap, out, rep = BASE.build(cfg, home, tmp / "ui" / "page.html")
        r1, r2 = typekit_apply(out, tk), typekit_apply(out, tk)
        page = out.read_text(encoding="utf-8")
        chk("④ 真建頁(v0104 範本 + 快照)→ 套件插在 </head> 前、只一段;再套 same;左下 GATE · 三系統仍在",
            (r1["how"], r2["how"]) == ("inserted", "same") and page.count("via-typekit:begin") == 1
            and page.find("via-typekit:begin") < page.lower().rfind("</head>") and 'id="gates3"' in page, (r1, r2))
        chk("④b 日期一律 YYYY-MM-DD:閘戳時間取 slice(0,16)(YYYY-MM-DD HH:MM)· 範本換段恰好一次;套件日期框 = YYYY-MM-DD 文字框 + 日曆鈕",
            not PATCH_MISSES_V0105 and _TS_NEW in page and _TS_OLD not in page and "placeholder='YYYY-MM-DD'" in page and "showPicker" in page,
            PATCH_MISSES_V0105)
        made = tmp / "ui" / "made.html"

        def _fake(a):
            made.write_text("<html><head><style>b{}</style></head><body><b>x</b></body></html>", encoding="utf-8")
            return 0
        PRIOR.main = _fake
        os.environ["VIA_NO_OPEN"] = "1"
        o = io.StringIO()
        with contextlib.redirect_stdout(o):
            rc = main(["build", "--out", str(made), "--open"])
        chk("⑤ build 包裝:前版鏈產頁 → 套件 → 才開頁(--open 不往前版傳;VIA_NO_OPEN=1 不開)",
            rc == 0 and made.read_text(encoding="utf-8").count("via-typekit:begin") == 1 and "字級套件" in o.getvalue() and "不開瀏覽器" in o.getvalue(), o.getvalue()[-300:])
    finally:
        PRIOR.main = keep_main
        BASE.WORK_DIR, BASE.WORK_CONFIG = keep_wd
        if keep_open is None:
            os.environ.pop("VIA_NO_OPEN", None)
        else:
            os.environ["VIA_NO_OPEN"] = keep_open
        shutil.rmtree(tmp, ignore_errors=True)
    text = Path(__file__).read_text(encoding="utf-8")
    import ast
    chk("⑥ 檔頭:加速器橋 · 網路橋在(__future__ 之後);不碰 TA-Lib;不直派子行程;不載外部函式庫",
        "[VIA:ACCEL-BRIDGE:" in text and "[VIA:NET-BRIDGE:" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in text and "cdn" + "js" not in text and "unp" + "kg.com" not in text
        and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.name or "").split(".")[0] == "sub" + "process" for x in n.names) for n in ast.walk(ast.parse(text))))
    print(f"[計] {TAG} 本版 {p}/{p + f} · {'PASS' if f == 0 else 'FAIL'}")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
