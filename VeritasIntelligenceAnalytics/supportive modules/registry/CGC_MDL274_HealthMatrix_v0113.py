#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL274_HealthMatrix v0113 — 薄尾:健康矩陣頁(VDF 頁右側「健康」頁籤就是它)字體 / 階層一致 + 日期一律 YYYY-MM-DD(字級套件)

操作員令(2026-10-11):「u/i請字體一致或階層一致姓  左右面板都凌亂」「很多展現都要重新思考整理」「日期規格一律用YYYY-MM-DD」。
  容器實測(改前):VDF 頁右側各頁 5–6 種字級、3 種字體;健康矩陣頁是 VDF 頁第一個頁籤。
  ① 字級套件:讀 registry 的 VIA_UI_Template_SSOT 尾版(v0101 起有字級 token;只讀資料冊)→ 頁內一段 CSS + 一小段 JS:
     四級字(標題 / 段頭 / 內文 / 註記)· 兩種字重 · 一種主字體(等寬只給指令與代碼)· 按鈕輸入框繼承字體;頁上任何字級吸到最近一級
     (之後 JS 產的內容也跟,MutationObserver 只處理新元素)。短欄不換行 · 長欄限寬 · 寬表外包橫捲 · 左面板有輸入框 / 按鈕的表兩行一列。
  ② 日期一律 YYYY-MM-DD:日期框改 YYYY-MM-DD 文字框 + 日曆鈕(滑鼠選日照用,L118);頁上 2026/10/11 · 2026.10.11 · 2026年10月11日 · 2026-1-5
     改寫成 YYYY-MM-DD;指令 / 代碼 / 檔名 / 代號裡的日期不動。純 CSS + 頁內小段 JS;不連網、不裝套件、不載外部函式庫。
  ③ 冊讀不到 / 沒有字級 token → 內建同一份預設照常套,並寫明原因;頁 body 加 data-via-typekit="off" 可關。
  ④ 範圍:只動 VCGC 自己的 VIA_Reports/review/vcgc_health/ 直下 *_latest.html(matrix / ui 產完先不開 → 套件 → 要開才開;
     其他動詞跑完也補套;冪等)。VDF / VRN 的頁不碰(L120),由各自的 manager 照同一本冊套。
其餘照 v0112。只收 VCGC 呼叫。零網路。不用 TA-Lib。
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


import contextlib
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

ME = Path(__file__).resolve()
HERE = ME.parent
_STEM = "CGC_MDL274_HealthMatrix"
TAG = "v0113"
SELF_ID = "VCGC"


def _vnum_v0113(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0113(p) < _vnum_v0113(ME)), key=_vnum_v0113)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0113", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
TK_ROOT = PRIOR._root()


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


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


def _own_dir() -> Path:
    return PRIOR._paths()["out"]


_OPEN_PAGE = {"matrix": "HEALTH_MATRIX_latest.html", "ui": "VCGC_UI_latest.html"}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    if not a or a[0].startswith("-"):
        return PRIOR.main(a)
    page = _OPEN_PAGE.get(a[0])
    want_open = page is not None and os.environ.get("VIA_NO_OPEN") != "1" and os.name == "nt"
    keep = os.environ.get("VIA_NO_OPEN")
    if page:
        os.environ["VIA_NO_OPEN"] = "1"      # 先不開:頁產完 + 字級套件套完再開
    try:
        rc = PRIOR.main(a)
    finally:
        if page:
            if keep is None:
                os.environ.pop("VIA_NO_OPEN", None)
            else:
                os.environ["VIA_NO_OPEN"] = keep
    r = typekit_dir(_own_dir())
    if r["changed"] or page:
        print("  [字級] VCGC 健康矩陣夾 %d 頁(新套 / 換新 %d)· 冊 %s%s" % (r["n"], r["changed"], r.get("book") or "內建預設",
                                                                  (" · " + r["why"]) if r.get("why") else ""))
    if want_open:
        fp = _own_dir() / page
        if fp.is_file():
            try:
                os.startfile(str(fp))  # type: ignore[attr-defined]  # noqa: S606 — 本機頁面
            except OSError as exc:
                print("  [開頁] 沒開成(%s):%s" % (type(exc).__name__, fp))
    return rc


_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>body{font:10.5px Arial}</style></head>
<body><h1>健康矩陣</h1><table><tr><td>2026/10/11</td><td>OK</td></tr></table></body></html>"""


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

    print("=== %s %s · 薄尾自測(字級套件:健康矩陣頁字體 / 階層一致 + 日期 YYYY-MM-DD)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="tk_mdl274_"))
    keep_paths, keep_main, keep_open = PRIOR._paths, PRIOR.main, os.environ.get("VIA_NO_OPEN")
    try:
        tk = typekit_book()
        t = tk["tokens"]
        chk("① 冊尾版有字級 token:四級 16 / 13 / 12 / 11 · 字重 400 / 700(冊 %s)" % tk.get("book"),
            tk.get("book") and not tk.get("why") and [t["fs-title"], t["fs-h"], t["fs"], t["fs-note"]] == ["16px", "13px", "12px", "11px"]
            and t["w-normal"] == "400" and t["w-bold"] == "700", tk)
        blk = typekit_block(tk)
        chk("② 套件:四級 px · 按鈕輸入框繼承字體 · 日期框 YYYY-MM-DD + 日曆鈕 · 一段 style + 一段 script · 零外部連結 · 可關 · 後長內容照吸附",
            all(("--via-t%d:%spx" % (i + 1, v)) in blk for i, v in enumerate(("16", "13", "12", "11"))) and "button,input,select,textarea{font-family:inherit" in blk
            and "placeholder='YYYY-MM-DD'" in blk and blk.count("<style") == 1 and blk.count("<script") == 1
            and not re.search(r"https?://(?!www\.w3\.org/1999/xhtml)|<link|\bsrc=|@import|fetch\(", blk) and "data-via-typekit" in blk and "MutationObserver" in blk)
        own = td / "VIA_Reports" / "review" / "vcgc_health"
        (own / "sub").mkdir(parents=True)
        other = td / "VIA_Reports" / "vdf"
        other.mkdir(parents=True)
        (own / "sub" / "X_latest.html").write_text(_PAGE, encoding="utf-8")
        (other / "VDF_UI_latest.html").write_text(_PAGE, encoding="utf-8")
        PRIOR._paths = lambda: {"root": td, "out": own, "registry": td / "supportive modules" / "registry"}

        def _fake(a):
            (own / "HEALTH_MATRIX_latest.html").write_text(_PAGE, encoding="utf-8")
            print("[fake] VIA_NO_OPEN=%s" % os.environ.get("VIA_NO_OPEN"))
            return 0
        PRIOR.main = _fake
        os.environ.pop("VIA_NO_OPEN", None)
        o = io.StringIO()
        with contextlib.redirect_stdout(o):
            rc = main(["matrix"])
        hm = (own / "HEALTH_MATRIX_latest.html").read_text(encoding="utf-8")
        chk("③ matrix:前版鏈產頁時先不開(VIA_NO_OPEN=1)→ 套件 → 環境還原;頁上只有一段套件",
            rc == 0 and "[fake] VIA_NO_OPEN=1" in o.getvalue() and os.environ.get("VIA_NO_OPEN") is None and hm.count("via-typekit:begin") == 1, o.getvalue()[-300:])
        with contextlib.redirect_stdout(io.StringIO()):
            main(["matrix"])
        chk("④ 冪等 · 範圍:再跑仍一段;只動 VCGC 健康矩陣夾直下 *_latest.html(子夾 · VDF 的頁不碰,L120)",
            (own / "HEALTH_MATRIX_latest.html").read_text(encoding="utf-8").count("via-typekit:begin") == 1
            and "via-typekit" not in (own / "sub" / "X_latest.html").read_text(encoding="utf-8")
            and "via-typekit" not in (other / "VDF_UI_latest.html").read_text(encoding="utf-8"))
        os.environ["VIA_FROM_VCGC"], keep_from = "NO", os.environ.get("VIA_FROM_VCGC")
        with contextlib.redirect_stdout(io.StringIO()):
            rc_no = main(["matrix"])
        if keep_from is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = keep_from
        chk("⑤ 只收 VCGC 呼叫(VIA_FROM_VCGC≠YES → rc 2,照前版)", rc_no == 2)
    finally:
        PRIOR._paths, PRIOR.main = keep_paths, keep_main
        if keep_open is None:
            os.environ.pop("VIA_NO_OPEN", None)
        else:
            os.environ["VIA_NO_OPEN"] = keep_open
        shutil.rmtree(td, ignore_errors=True)
    body = ME.read_text(encoding="utf-8")
    import ast
    chk("⑥ 檔頭:加速器橋在(__future__ 之後);不碰 TA-Lib;不直派子行程;不載外部函式庫",
        "[VIA:ACCEL-BRIDGE:v0100]" in body and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
        and "import " + "talib" not in body and "cdn" + "js" not in body and "unp" + "kg.com" not in body
        and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.name or "").split(".")[0] == "sub" + "process" for x in n.names) for n in ast.walk(ast.parse(body))))
    print("  ── 前版鏈自測(VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s %s 本版 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
