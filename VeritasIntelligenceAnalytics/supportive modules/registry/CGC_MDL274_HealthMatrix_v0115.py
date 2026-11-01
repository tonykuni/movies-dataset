#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL274_HealthMatrix v0115 — 薄尾:設計稿「Veritas Header」1a 母系統視覺(VCGC 頁 · 健康矩陣頁 · 入口頁;只動顏色 · 字體 · 邊角 · 頁首)+ theme preview

操作員令(2026-10-12):「1a for vcgc html u/i design 1b for vrn 1c for vdf only follow visual design and colors」(Claude Design 設計稿兩檔上傳;
  承同日「vrn vdf vcgc都是獨立操作台 只是顏色及lauout基本規劃相同」)。
冊:registry 的 VIA_UI_Template_SSOT 尾版(v0103 起有 systems.VCGC / VRN / VDF 覆蓋 + design.css);本檔只讀冊、不寫冊、不改他系統的檔(L120)。
  ① design_book():冊尾版 tokens + systems.VCGC(1a:米白紙底 #f2f1ec · 白卡 · 印泥紅 #9e2b25 · 青 #2f6f6f)→ 燈四色仍鎖 → design.css 只收純 CSS;
  ② 字級套件(v0114 本體)的 typekit_book / typekit_block 換成本版:同一段 <style> 尾端接 :root{全部 token} + design.css(仍一段 style + 一段 script,冪等換新);
     JS 字體吸附對冊 serif_selector 放行(品牌標題襯線);
  ③ v0112 本體的 ui_theme_load 換成讀冊尾版 + systems.VCGC(VCGC 頁 · 入口頁 · 健康矩陣頁的 via-theme 段跟著冊走);
  ④ portal 後把入口頁 VIA_Reports/VIA_UI_latest.html 也補套(前版的夾內補套掃不到它);theme preview:三系統頁首預覽頁 VIA_Reports/review/vcgc_health/VIA_UI_DesignPreview_latest.html(1a / 1b / 1c 各一區,只攤開冊值;
     1b 由 VRN 自己的 manager 套,本頁不寫 VRN 的檔)。
其餘(matrix · ui · portal · theme init/show · 展現規則 · 只收 VCGC 呼叫 · 零網路 · 不碰 TA-Lib)照 v0114。
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

import ast
import contextlib
import html
import importlib.util
import io
import json
import os
import re
import sys
import types
from pathlib import Path

ME = Path(__file__).resolve()
HERE = ME.parent
_STEM = "CGC_MDL274_HealthMatrix"
TAG = "v0115"
SELF_ID = "VCGC"
LOCK_LAMPS_V0115 = {"lamp-green": "#16a34a", "lamp-yellow": "#f59e0b", "lamp-red": "#dc2626", "lamp-gray": "#9ca3af"}
CSS_BAD_RX_V0115 = re.compile(r"<|@import|url\s*\(|https?:", re.I)
SERIF_DEFAULT_V0115 = "h1,.via-serif,.brand"
SNAP_OLD_V0115 = "else if(v2[3])st.fontFamily='var(--via-font)'"
SNAP_NEW_V0115 = "else if(v2[3]&&!r[0].closest('%s'))st.fontFamily='var(--via-font)'"
PREVIEW_NAME = "VIA_UI_DesignPreview_latest.html"


def _vnum_v0115(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0115(p) < _vnum_v0115(ME)), key=_vnum_v0115)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0115", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
TK_ROOT = PRIOR.TK_ROOT


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def _chain_v0115() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _owner_v0115(name: str):
    for m in _chain_v0115():
        if name in vars(m):
            return m
    return None


_OWN_TK = _owner_v0115("typekit_block")        # v0114 本體(字級套件 v2)
_OWN_TH = _owner_v0115("ui_theme_apply")       # v0112 本體(via-theme 段 · _paths · ui · portal)
_ORIG_BOOK = _OWN_TK.typekit_book if _OWN_TK else None
_ORIG_BLOCK = _OWN_TK.typekit_block if _OWN_TK else None
_ORIG_JS = _OWN_TK._TK_JS if _OWN_TK else ""
_ORIG_THEME_LOAD = _OWN_TH.ui_theme_load if _OWN_TH else None


# ---------------------------------------------------------------- 設計稿視覺(只讀冊)
def _tk_safe_v0115(v) -> str:
    return re.sub(r"[<>{};\\]", "", str(v))


def _read_book_v0115(root=None):
    root = Path(root or TK_ROOT)
    hits = sorted((root / "supportive modules" / "registry").glob("VIA_UI_Template_SSOT_v*.json"), key=_vnum_v0115)
    if not hits:
        return None, None, "找不到 VIA_UI_Template_SSOT_v*.json,設計稿視覺不套"
    try:
        return hits[-1].name, json.loads(hits[-1].read_text(encoding="utf-8-sig")), None
    except (OSError, ValueError, AttributeError) as exc:
        return hits[-1].name, None, "讀不了 %s:%s,設計稿視覺不套" % (hits[-1].name, type(exc).__name__)


def design_tokens(d: dict, sid: str) -> dict:
    """冊 tokens + systems.<sid> 純量覆蓋 + 燈四色鎖定(任何系統都可算,預覽頁用;本系統只用 SELF_ID)。"""
    toks = {k: str(v) for k, v in (d.get("tokens") or {}).items() if not isinstance(v, (list, dict))}
    sysd = (d.get("systems") or {}).get(sid) or {}
    toks.update({k: str(v) for k, v in sysd.items() if not isinstance(v, (list, dict)) and k not in ("note", "design_section", "theme_zh")})
    toks.update(LOCK_LAMPS_V0115)
    return toks


def design_book(root=None, sid: str = SELF_ID) -> dict:
    """→ {book, tokens, css, serif, theme, why}:冊尾版 tokens + systems.<sid> · 燈四色鎖定 · design.css 只收純 CSS;沒冊 / 壞冊照實。"""
    name, d, err = _read_book_v0115(root)
    out = {"book": name, "tokens": {}, "css": "", "serif": SERIF_DEFAULT_V0115, "theme": "", "why": err}
    if d is None:
        return out
    toks = design_tokens(d, sid)
    sysd = (d.get("systems") or {}).get(sid) or {}
    des = d.get("design") or {}
    css = str(des.get("css") or "")
    why = []
    if not css:
        why.append("%s 沒有 design.css,只套顏色 token" % name)
    elif CSS_BAD_RX_V0115.search(css):
        css = ""
        why.append("%s 的 design.css 含 < / url( / @import / http,整段不收(零網路 · 不注入標記)" % name)
    if not sysd:
        why.append("%s 沒有 systems.%s,用共用 tokens" % (name, sid))
    serif = re.sub(r"[^A-Za-z0-9 ,.#_>-]", "", str(des.get("serif_selector") or "")) or SERIF_DEFAULT_V0115
    out.update({"tokens": toks, "css": css, "serif": serif, "theme": str(sysd.get("theme_zh") or ""), "why": ";".join(why) or None})
    return out


def _root_vars_v0115(toks: dict) -> str:
    return ";".join("--%s:%s" % (re.sub(r"[^a-z0-9-]", "", k), _tk_safe_v0115(v)) for k, v in toks.items())


def design_css(db=None) -> str:
    """→ :root{全部 token} + design.css(接在字級套件 CSS 尾端;版面不動)。沒 token 回空字串。"""
    db = db or design_book()
    if not db.get("tokens"):
        return ""
    return "/* [VIA:DESIGN:%s] %s · %s */\n:root{%s}\n%s" % (db.get("book") or "none", SELF_ID, db.get("theme") or "", _root_vars_v0115(db["tokens"]), db.get("css") or "")


def typekit_book(root=None) -> dict:
    tk = _ORIG_BOOK(root) if _ORIG_BOOK else {"tokens": {}, "auto": {}, "present": {}, "book": None, "why": "前版鏈沒有字級套件"}
    tk["design"] = design_book(root)
    return tk


def typekit_block(tk=None) -> str:
    """字級套件那一段 + 設計稿視覺(同一段 <style> 尾端;仍一段 style + 一段 script)。"""
    tk = tk or typekit_book()
    blk = _ORIG_BLOCK(tk) if _ORIG_BLOCK else ""
    extra = design_css(tk.get("design") or design_book())
    if extra and blk:
        i = blk.find("</style>")
        if i >= 0:
            blk = blk[:i] + extra + "\n" + blk[i:]
    return blk


def ui_theme_load(root):
    """v0112 via-theme 段的讀冊:冊尾版 tokens + systems.VCGC(燈四色鎖定);沒冊 → 前版本體(內建預設)。"""
    db = design_book(root)
    if not db.get("book") or not db.get("tokens"):
        return _ORIG_THEME_LOAD(root) if _ORIG_THEME_LOAD else ({}, None)
    t = dict((_OWN_TH._THEME_DEFAULT["tokens"]) if _OWN_TH else {})
    t.update(db["tokens"])
    t.update(LOCK_LAMPS_V0115)
    return t, db["book"]


def _patch_owners_v0115() -> dict:
    r = {"typekit": [], "theme": False, "js": False}
    if _OWN_TK is not None:
        for m in _chain_v0115():                         # 鏈上每個有這兩個名字的模組都換(v0114 本體 · v0113 被 v0114 指派的那份)
            if "typekit_book" in vars(m):
                m.typekit_book = typekit_book
                r["typekit"].append(Path(m.__file__).stem[-5:])
            if "typekit_block" in vars(m):
                m.typekit_block = typekit_block
        _OWN_TK._TK_JS = _ORIG_JS.replace(SNAP_OLD_V0115, SNAP_NEW_V0115 % design_book()["serif"])
        r["js"] = SNAP_OLD_V0115 not in _OWN_TK._TK_JS
    if _OWN_TH is not None:
        _OWN_TH.ui_theme_load = ui_theme_load
        r["theme"] = True
    return r


PATCHED_V0115 = _patch_owners_v0115()


# ---------------------------------------------------------------- theme preview:三系統頁首預覽頁(只攤開冊值)
_PREVIEW_CSS = """body{margin:0;padding:16px 20px}
.strip{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0 0 14px;font-family:var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}
.pill{display:inline-flex;gap:5px;padding:3px 8px;border-radius:99px;font-family:var(--mono);letter-spacing:.12em;text-transform:uppercase}
.sys{margin:0 0 22px}
.tagline{display:flex;gap:10px;align-items:center;margin:0 0 8px;font-family:var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}
.tagline .tg{background:var(--seal);color:#fff;padding:3px 9px}
.shell{display:grid;grid-template-columns:var(--aside-w) minmax(0,1fr);border:1px solid var(--line);border-radius:8px;overflow:hidden;background:var(--bg);box-shadow:var(--shadow)}
.shell aside{padding:0;border-right:1px solid var(--line)}
.logo{min-height:72px;display:flex;align-items:center;gap:12px;padding:8px 16px;border-bottom:1px solid var(--line);background:var(--head);color:var(--head-txt)}
.logo .seal{width:42px;height:42px;border-radius:6px;display:grid;place-items:center;font-family:var(--serif);font-size:22px;font-weight:600;flex:none}
.logo b{display:block;font-family:var(--serif);letter-spacing:.07em}
.logo small{display:block;font-family:var(--mono);letter-spacing:.2em;text-transform:uppercase;color:var(--caption)}
.logo i{display:block;font-style:normal;font-family:var(--cjk-serif);letter-spacing:.34em;color:var(--nav-dim)}
nav{padding:10px}
nav .g{display:flex;gap:7px;align-items:center;font-family:var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--nav-dim);padding:6px}
nav .g:after{content:"";flex:1;height:1px;background:var(--hair)}
nav a{display:grid;grid-template-columns:20px 1fr auto;gap:8px;padding:6px 8px;border-radius:5px;color:var(--nav);text-decoration:none;border-left:2px solid transparent}
nav a.on{background:var(--sys-bg);border-left-color:var(--sys)}
nav a .n,nav a .e{font-family:var(--mono);color:var(--nav-dim)}
.shell main{padding:0 18px 16px;min-width:0}
.shell header{min-height:72px;display:flex;align-items:flex-end;justify-content:space-between;gap:16px;padding:12px 0 10px;background:transparent;border-bottom:1px solid var(--line)}
.shell header h1{margin:0;font-size:var(--fs-title)}
.shell header h1 small{display:block;font-family:var(--mono);letter-spacing:.3em;text-transform:uppercase;color:var(--sys)}
.acts button{margin:0 0 0 6px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin:10px 0}
.kpi{padding:9px 11px;border-top:2px solid var(--sys)}.kpi b{display:block;font-family:var(--mono);font-size:17px}.kpi span{font-family:var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--dim)}
table{border-collapse:collapse;width:100%}th,td{padding:4px 8px;text-align:left;border-bottom:1px solid var(--hair)}
.lp{display:inline-block;width:11px;height:11px;border-radius:50%;vertical-align:middle;margin-right:4px}.lp.GREEN{background:var(--lamp-green)}.lp.YELLOW{background:var(--lamp-yellow)}.lp.RED{background:var(--lamp-red)}.lp.GRAY{background:var(--lamp-gray)}
.sw{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 0}.sw span{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);letter-spacing:.06em;color:var(--dim)}.sw i{width:14px;height:14px;border-radius:3px;border:1px solid var(--line);display:inline-block}
.foot{margin:10px 0 0;color:var(--dim)}"""
_PREVIEW_SYS = (("VCGC", "1a", "母系統 · VCGC 操作台", "VERITAS INTELLIGENCE ANALYTICS", "Central Governance", "智能分析平台", "VIA CENTRAL GOVERNANCE CONSOLE", "Veritas Intelligence Analytics · Mother System"),
                ("VRN", "1b", "VRN 定版 · 青花(VRN 自己的 manager 套;本頁只攤開冊值)", "VERITAS REPORT NOVA", "VRN Workbench", "投資報告資訊平台", "投資報告資訊平台", "Home · Input + Summary"),
                ("VDF", "1c", "VDF 汝窯天青 · 完整工作區", "VERITAS DATA FORGE", "Ru celadon", "總體財經資料庫平台", "總體財經資料庫平台", "Market Data Acquisition · Validation · Database Engineering"))


def theme_preview(P: dict | None = None) -> dict:
    """三系統頁首預覽頁:冊尾版 tokens + systems.<每系統> 各一區(inline token 覆蓋),同一段設計 CSS;不寫他系統的檔。"""
    P = P or PRIOR._paths()
    name, d, err = _read_book_v0115(P["root"])
    out_fp = Path(P["out"]) / PREVIEW_NAME
    if d is None:
        return {"verb": "theme preview", "state": "NODATA", "why": err, "html": str(out_fp)}
    e = html.escape
    ver = (re.search(r"_v(\d{4})", name or "") or [None, "0000"])[1] if name else "0000"
    ver = "v" + ver
    sections, pills = [], []
    for sid, tag, zh, brand, sub, bzh, title, subtitle in _PREVIEW_SYS:
        t = design_tokens(d, sid)
        sysd = (d.get("systems") or {}).get(sid) or {}
        inline = _root_vars_v0115(t)
        pills.append("<span class='pill' style='background:%s;color:%s'>%s · IN PROGRESS</span>" % (e(t.get("sys-bg", "#f4f3ef")), e(t.get("sys", "#6b6860")), e({"VCGC": "母系統 VIA", "VRN": "VRN 研究報告", "VDF": "VDF 資料庫"}[sid])))
        sw = "".join("<span><i style='background:%s'></i>%s %s</span>" % (e(t[k]), e(k), e(t[k])) for k in ("bg", "panel", "line", "txt", "dim", "acc", "head", "head-txt", "sys", "sys-bg", "panel-2", "seal") if k in t)
        sections.append(
            "<section class='sys' id='%s' style=\"%s\"><div class='tagline'><span class='tg'>%s</span><span>%s · %s</span></div>"
            "<div class='shell'><aside><div class='logo'><span class='seal' style='background:var(--seal);color:#fff'>理</span><div><b class='via-serif'>%s</b><small>%s · %s</small><i>%s</i></div></div>"
            "<nav><div class='g'>主控 Console</div><a class='on' href='#%s'><span class='n'>01</span><span>首頁</span><span class='e'>HOME</span></a>"
            "<a href='#%s'><span class='n'>02</span><span>執行控制台</span><span class='e'>RUN</span></a><a href='#%s'><span class='n'>03</span><span>健康矩陣</span><span class='e'>HEALTH</span></a></nav></aside>"
            "<main><header><h1>%s <small>%s</small></h1><div class='acts'><button class='p'>RUN</button><button>VALIDATE</button><button>RUNDIR</button></div></header>"
            "<div class='kpis'><div class='kpi card'><b>%s</b><span>版本 VERSION</span></div><div class='kpi card'><b>3</b><span>系統 SYSTEMS</span></div><div class='kpi card'><b>4</b><span>燈 LAMPS · 鎖定</span></div></div>"
            "<table><tr><th>燈</th><th>項目 ITEM</th><th>狀態 STATE</th></tr><tr><td><i class='lp GREEN'></i>GREEN</td><td>自測 selftest</td><td>PASS</td></tr>"
            "<tr><td><i class='lp YELLOW'></i>YELLOW</td><td>交接 handoff</td><td>REVIEW</td></tr><tr><td><i class='lp RED'></i>RED</td><td>閘 gate</td><td>HOLD</td></tr><tr><td><i class='lp GRAY'></i>GRAY</td><td>未跑</td><td>—</td></tr></table>"
            "</main></div><div class='sw'>%s</div><div class='foot'>%s</div></section>"
            % (sid, e(inline), e(tag), e(sid), e(zh), e(brand), e(sub), e(ver), e(bzh), sid, sid, sid, e(title), e(subtitle), e(name or ""), sw, e(str(sysd.get("note") or ""))))
    tk = typekit_book(P["root"])
    blk = typekit_block(tk)
    page = ("<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>VIA 三系統視覺預覽</title>"
            "<style>%s</style>\n%s\n</head><body><div class='strip'><span>母系統工作區 · Parent Platform Shell</span><span>本日範圍 Today's scope</span>%s"
            "<span class='pill' style='background:#f2ecdd;color:#6f5c31'>VAP 繪圖稽核 · IN PROGRESS</span></div>%s"
            "<p class='foot'>冊 %s · %s · 三系統各讀自己那一組 token(L120)· 1b 由 VRN 自己的 manager 套 · 燈四色鎖定 · 零網路(襯線字體本機有才用)</p></body></html>"
            % (_PREVIEW_CSS, blk, "".join(pills), "".join(sections), e(name or ""), e(PRIOR._now() if hasattr(PRIOR, "_now") else "")))
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    out_fp.write_text(page, encoding="utf-8")
    opened = False
    if os.environ.get("VIA_NO_OPEN") != "1" and os.name == "nt":
        try:
            os.startfile(str(out_fp))  # type: ignore[attr-defined]
            opened = True
        except OSError:
            pass
    return {"verb": "theme preview", "state": "WRITTEN", "html": str(out_fp), "book": name, "systems": [s[0] for s in _PREVIEW_SYS], "opened": opened}


def design_page(path) -> dict:
    """把字級套件(含設計稿視覺)補套到一支 VCGC 自己的頁;入口頁 VIA_Reports/VIA_UI_latest.html 不在健康矩陣夾,前版的夾內補套掃不到,portal 後由本版補。"""
    if _OWN_TK is None or not hasattr(_OWN_TK, "typekit_apply"):
        return {"page": Path(path).name, "how": "no-typekit"}
    return _OWN_TK.typekit_apply(Path(path), typekit_book())


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    if a[:1] == ["portal"]:
        rc = PRIOR.main(a)
        r = design_page(Path(PRIOR._paths()["root"]) / "VIA_Reports" / "VIA_UI_latest.html")
        print("  [設計] 入口頁補套(字級套件 + 1a 視覺)· %s" % r.get("how"))
        return rc
    if a[:2] == ["theme", "preview"]:
        r = theme_preview()
        print("[計] vcgc theme preview · %s · %s · 冊 %s · 1a / 1b / 1c 各一區 · 已開 %s" % (r["state"], r["html"], r.get("book") or "—", r.get("opened", False)))
        if r.get("why"):
            print("  [why] %s" % r["why"])
        return 0 if r["state"] == "WRITTEN" else 2
    return PRIOR.main(a)


_PAGE_V0115 = """<!doctype html><html><head><meta charset="utf-8"><style>:root{--line:#e0e0e0;--panel:#f7f7f7}body{font:12px Arial}th{background:#111827;color:#fff}</style></head>
<body><header><h1>VCGC · 母系統</h1><small>x</small></header><aside><div class='card'><b>k</b><label>l</label><button>改</button></div></aside>
<main><table><tr><th>燈</th><th>項</th></tr><tr><td><i class='lp GREEN'></i></td><td>v</td></tr></table></main></body></html>"""


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

    print("=== %s %s · 薄尾自測(設計稿 1a 母系統視覺 + theme preview)===" % (_STEM, TAG))
    db = design_book()
    t = db.get("tokens") or {}
    chk("① 冊尾版 ≥ v0103:有 systems.VCGC · design.css · serif / cjk-serif token · serif_selector(冊 %s)" % db.get("book"),
        db.get("book") and _vnum_v0115(db["book"]) >= 103 and db.get("css") and not db.get("why") and t.get("serif") and t.get("cjk-serif")
        and db.get("serif") == "h1,.via-serif,.brand", db)
    chk("② 1a 覆蓋:米白紙底 #f2f1ec · 白卡 · 頁首 #ffffff / #1b1a17 · 青 acc #2f6f6f · 印泥紅 sys #9e2b25 · 標 \"1a\" · 品牌 VERITAS INTELLIGENCE ANALYTICS · 燈四色仍鎖",
        t.get("bg") == "#f2f1ec" and t.get("panel") == "#ffffff" and t.get("head") == "#ffffff" and t.get("head-txt") == "#1b1a17" and t.get("acc") == "#2f6f6f"
        and t.get("sys") == "#9e2b25" and t.get("tag") == '"1a"' and t.get("brand") == '"VERITAS INTELLIGENCE ANALYTICS"' and t.get("lamp-red") == "#dc2626"
        and t.get("lamp-yellow") == "#f59e0b", {k: t.get(k) for k in ("bg", "head", "acc", "sys", "tag", "lamp-red")})
    tk = typekit_book()
    blk = typekit_block(tk)
    chk("③ 套件仍一段 style + 一段 script(v2:present / pick 仍在):尾端接 [VIA:DESIGN] :root(--sys:#9e2b25 · --lamp-red:#dc2626 · --serif)+ design.css · JS 字體吸附對 h1 / .via-serif / .brand 放行 · 零外部連結",
        blk.count("<style") == 1 and blk.count("<script") == 1 and "function present(" in blk and "[VIA:DESIGN:" in blk and "--sys:#9e2b25" in blk and "--lamp-red:#dc2626" in blk
        and "--serif:" in blk and "header h1::before" in blk and "closest('h1,.via-serif,.brand')" in blk and SNAP_OLD_V0115 not in blk
        and not re.search(r"https?://(?!www\.w3\.org/1999/xhtml)|<link|\bsrc=|@import|fetch\(", blk), blk[:200])
    once, h1 = PRIOR.typekit_apply_text(_PAGE_V0115, blk)
    twice, h2 = PRIOR.typekit_apply_text(once, blk)
    chk("④ 冪等:插在 </head> 前(頁自己的 style 之後)→ 第二次 same · 只一段;頁上 :root 有 --head:#ffffff · --bg:#f2f1ec(壓過頁內固定色)",
        h1 == "inserted" and h2 == "same" and twice.count("via-typekit:begin") == 1 and "--head:#ffffff" in twice and "--bg:#f2f1ec" in twice
        and twice.index("<style>") < twice.index("[VIA:DESIGN:"), (h1, h2))
    chk("⑤ 本體已換:v0114 的 typekit_block / _TK_JS · 鏈上每份 typekit_book · v0112 的 ui_theme_load 都指到本版(matrix / ui / portal 後補套與 via-theme 段都走本版)",
        PATCHED_V0115.get("theme") and PATCHED_V0115.get("js") and len(PATCHED_V0115.get("typekit") or []) >= 2 and _OWN_TK.typekit_block is typekit_block
        and _OWN_TH.ui_theme_load is ui_theme_load and all(getattr(m, "typekit_book", None) is typekit_book for m in _chain_v0115() if "typekit_book" in vars(m)), PATCHED_V0115)
    tt, bk = ui_theme_load(TK_ROOT)
    css = _OWN_TH.ui_theme_css(tt)
    chk("⑥ via-theme 段改讀冊尾版 + systems.VCGC:--sys:#9e2b25 · --acc:#2f6f6f · --lamp-red:#dc2626 · 冊名 = 尾版",
        bk == db.get("book") and 'id="via-theme"' in css and "--sys:#9e2b25" in css and "--acc:#2f6f6f" in css and "--lamp-red:#dc2626" in css, (bk, css[:120]))
    td = Path(tempfile.mkdtemp(prefix="pv_mdl274v115_"))
    keep_paths, keep_open = _OWN_TH._paths, os.environ.get("VIA_NO_OPEN")
    try:
        own = td / "VIA_Reports" / "review" / "vcgc_health"
        own.mkdir(parents=True)
        _OWN_TH._paths = lambda: {"root": TK_ROOT, "out": own, "registry": Path(TK_ROOT) / "supportive modules" / "registry"}
        os.environ["VIA_NO_OPEN"] = "1"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["theme", "preview"])
        pg = (own / PREVIEW_NAME).read_text(encoding="utf-8") if (own / PREVIEW_NAME).is_file() else ""
        chk("⑦ theme preview:rc 0 · 一頁三區(1a VERITAS INTELLIGENCE ANALYTICS · 1b VERITAS REPORT NOVA · 1c VERITAS DATA FORGE)· 各區 inline token(--head:#ccd8ea · --head:#cfe0dc)· 套件一段 · 燈四色 · 零外部連結",
            rc == 0 and all(x in pg for x in ("VERITAS INTELLIGENCE ANALYTICS", "VERITAS REPORT NOVA", "VERITAS DATA FORGE", "--head:#ccd8ea", "--head:#cfe0dc", "--head:#ffffff", "lp GREEN", "lp RED"))
            and pg.count("via-typekit:begin") == 1 and pg.count('<style id="via-typekit">') == 1 and "[VIA:DESIGN:" in pg and "[計] vcgc theme preview · WRITTEN" in buf.getvalue()
            and not re.search(r"https?://(?!www\.w3\.org/1999/xhtml)|<link|\bsrc=|@import|fetch\(", pg), buf.getvalue()[:200])
        portal = td / "VIA_Reports" / "VIA_UI_latest.html"
        portal.write_text(_PAGE_V0115.replace("VCGC · 母系統", "VIA"), encoding="utf-8")
        r_p = design_page(portal)
        pg2 = portal.read_text(encoding="utf-8")
        chk("⑦b 入口頁補套(portal 後):VIA_Reports/VIA_UI_latest.html 插一段套件 + 1a 視覺(--sys:#9e2b25)· 再補 same",
            r_p.get("how") == "inserted" and pg2.count("via-typekit:begin") == 1 and "[VIA:DESIGN:" in pg2 and "--sys:#9e2b25" in pg2 and design_page(portal).get("how") == "same", r_p)
        reg = td / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "VIA_UI_Template_SSOT_v0100.json").write_text(json.dumps({"tokens": {"panel": "#eef2ff", "lamp-red": "#000000"}, "design": {"css": "a{color:red}@import url(x)"}}), encoding="utf-8")
        d0 = design_book(td)
        d1 = design_book(td / "none")
        chk("⑧ 誠實退路:冊沒 systems.VCGC / design.css 壞(@import)→ css 不收 · why 寫明 · 燈紅仍 #dc2626;沒冊 → why · 不套 · preview NODATA",
            d0["book"] == "VIA_UI_Template_SSOT_v0100.json" and d0["css"] == "" and d0["tokens"]["panel"] == "#eef2ff" and d0["tokens"]["lamp-red"] == "#dc2626"
            and d0["why"] and "@import" in d0["why"] and "systems.VCGC" in d0["why"] and d1["book"] is None and d1["why"] and design_css(d1) == ""
            and theme_preview({"root": td / "none", "out": own})["state"] == "NODATA", (d0["why"], d1["why"]))
    finally:
        _OWN_TH._paths = keep_paths
        if keep_open is None:
            os.environ.pop("VIA_NO_OPEN", None)
        else:
            os.environ["VIA_NO_OPEN"] = keep_open
        shutil.rmtree(td, ignore_errors=True)
    body = ME.read_text(encoding="utf-8")
    chk("⑨ 檔頭:加速器橋在(__future__ 之後);不碰 TA-Lib;不直派子行程;不載外部函式庫;只讀冊不寫冊;不寫他系統的檔",
        "[VIA:ACCEL-BRIDGE:v0100]" in body and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
        and "import " + "talib" not in body and "cdn" + "js" not in body and "unp" + "kg.com" not in body
        and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.name or "").split(".")[0] == "sub" + "process" for x in n.names) for n in ast.walk(ast.parse(body)))
        and "VIA_UI_Template_SSOT_v*.json\").write" not in body and "VRN_" + "SystemManager" not in body and "VDF_" + "SystemManager" not in body)
    print("  ── 前版鏈自測(VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑩ 前版 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s %s 本版 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
