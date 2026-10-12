#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0157 — 薄尾:設計稿「Veritas Header」1c 汝窯天青視覺(只動顏色 · 字體 · 邊角 · 頁首;版面 · 功能 · 燈四色不動)

操作員令(2026-10-12):「1a for vcgc html u/i design 1b for vrn 1c for vdf only follow visual design and colors」(Claude Design 設計稿兩檔上傳)。
冊:registry 的 VIA_UI_Template_SSOT 尾版(v0103 起有 systems.VDF 覆蓋 + design.css);本檔只讀冊,不寫冊,不載入他系統程式(L120)。
  ① design_book():冊尾版 tokens + systems.VDF(1c:頁首條 #cfe0dc · 青瓷綠 #3c6660 · 左欄 #f2f8f6 …)→ 燈四色仍鎖 → design.css 只收純 CSS
     (含 < · url( · @import · http 整段不收,照實寫 why);
  ② 字級套件本體(v0154 起的 v2;鏈上每份 typekit_book / typekit_block)換成本版:同一段 <style> 尾端接 :root{全部 token} + design.css(仍一段 style + 一段 script,
     冪等換新);VDF 頁 · VIA_Reports/vdf 直下 *_latest.html · VDF_MDL012 族群頁(經尾版 typekit_block)全套;
  ③ 字級套件 JS 的字體吸附對冊 serif_selector(h1 · .via-serif · .brand)放行 → 品牌標題用襯線(其餘仍主字體 / 等寬);
  ④ v0144 本體的 ui_theme_load 換成讀冊尾版 + systems.VDF(via-theme 段與清單 theme 名跟著冊走;沒冊照舊內建預設)。
其餘(all · 問參數頁 · 啟動就緒門 · 子行程 · 不代設同意閘 · 零網路 · 不碰 TA-Lib)照 v0156。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
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
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0157"
SELF_ID = "VDF"
LOCK_LAMPS_V0157 = {"lamp-green": "#16a34a", "lamp-yellow": "#f59e0b", "lamp-red": "#dc2626", "lamp-gray": "#9ca3af"}
CSS_BAD_RX_V0157 = re.compile(r"<|@import|url\s*\(|https?:", re.I)
SERIF_DEFAULT_V0157 = "h1,.via-serif,.brand"
SNAP_V0157 = (("else if(r[4]!==B)r[0].style.fontFamily='var(--via-font)'", "else if(r[4]!==B&&!r[0].closest('%s'))r[0].style.fontFamily='var(--via-font)'"),   # 套件 v1(v0153)
              ("else if(v2[3])st.fontFamily='var(--via-font)'", "else if(v2[3]&&!r[0].closest('%s'))st.fontFamily='var(--via-font)'"))                     # 套件 v2(v0154 起)


def _vnum_v0157(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0157(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0157(p) < _vnum_v0157(__file__)), key=_vnum_v0157)
PRIOR = _load_v0157(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0157() -> list:
    """前版鏈(只收真模組;某版把 PRIOR 包成替身就停在它前面)。"""
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _owner_v0157(name: str):
    """沿前版鏈找第一個真正定義 name 的那一版(本體);找不到回 None。"""
    for m in _chain_v0157():
        if name in vars(m):
            return m
    return None


_OWN_TK = _owner_v0157("typekit_block")        # 字級套件本體(v0154 起 v2;v0153 v1)
_OWN_TH = _owner_v0157("ui_theme_apply")       # v0144 本體(via-theme 段)
_ORIG_BOOK = _OWN_TK.typekit_book if _OWN_TK else None
_ORIG_BLOCK = _OWN_TK.typekit_block if _OWN_TK else None
_ORIG_JS = _OWN_TK._TK_JS if _OWN_TK else ""
_ORIG_THEME_LOAD = _OWN_TH.ui_theme_load if _OWN_TH else None
TK_ROOT = getattr(_OWN_TK, "TK_ROOT", VIA_ROOT)


# ---------------------------------------------------------------- 設計稿視覺(只讀冊)
def _tk_safe_v0157(v) -> str:
    return re.sub(r"[<>{};\\]", "", str(v))


def design_book(root=None) -> dict:
    """→ {book, tokens, css, serif, theme, why}:冊尾版 tokens + systems.VDF 覆蓋(純量)· 燈四色鎖定 · design.css 只收純 CSS;沒冊 / 壞冊照實。"""
    root = Path(root or TK_ROOT)
    hits = sorted((root / "supportive modules" / "registry").glob("VIA_UI_Template_SSOT_v*.json"), key=_vnum_v0157)
    out = {"book": None, "tokens": {}, "css": "", "serif": SERIF_DEFAULT_V0157, "theme": "", "why": "找不到 VIA_UI_Template_SSOT_v*.json,設計稿視覺不套"}
    if not hits:
        return out
    out["book"] = hits[-1].name
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
        toks = {k: str(v) for k, v in (d.get("tokens") or {}).items() if not isinstance(v, (list, dict))}
        sysd = (d.get("systems") or {}).get(SELF_ID) or {}
        toks.update({k: str(v) for k, v in sysd.items() if not isinstance(v, (list, dict)) and k not in ("note", "design_section", "theme_zh")})
        toks.update(LOCK_LAMPS_V0157)
        des = d.get("design") or {}
        css = str(des.get("css") or "")
        why = []
        if not css:
            why.append("%s 沒有 design.css,只套顏色 token" % out["book"])
        elif CSS_BAD_RX_V0157.search(css):
            css = ""
            why.append("%s 的 design.css 含 < / url( / @import / http,整段不收(零網路 · 不注入標記)" % out["book"])
        if not sysd:
            why.append("%s 沒有 systems.%s,用共用 tokens" % (out["book"], SELF_ID))
        serif = re.sub(r"[^A-Za-z0-9 ,.#_>-]", "", str(des.get("serif_selector") or "")) or SERIF_DEFAULT_V0157
        out.update({"tokens": toks, "css": css, "serif": serif, "theme": str(sysd.get("theme_zh") or ""), "why": ";".join(why) or None})
    except (OSError, ValueError, AttributeError) as exc:
        out["why"] = "讀不了 %s:%s,設計稿視覺不套" % (out["book"], type(exc).__name__)
    return out


def design_css(db=None) -> str:
    """→ :root{全部 token} + design.css(接在字級套件 CSS 尾端;版面不動)。沒 token 回空字串。"""
    db = db or design_book()
    if not db.get("tokens"):
        return ""
    root = ";".join("--%s:%s" % (re.sub(r"[^a-z0-9-]", "", k), _tk_safe_v0157(v)) for k, v in db["tokens"].items())
    return "/* [VIA:DESIGN:%s] %s · %s */\n:root{%s}\n%s" % (db.get("book") or "none", SELF_ID, db.get("theme") or "", root, db.get("css") or "")


def typekit_book(root=None) -> dict:
    tk = _ORIG_BOOK(root) if _ORIG_BOOK else {"tokens": {}, "auto": {}, "book": None, "why": "前版鏈沒有字級套件"}
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
    """v0144 via-theme 段的讀冊:冊尾版 tokens + systems.VDF(燈四色鎖定);沒冊 → 前版本體(內建預設)。"""
    db = design_book(root)
    if not db.get("book") or not db.get("tokens"):
        return _ORIG_THEME_LOAD(root) if _ORIG_THEME_LOAD else ({}, None)
    t = dict((_OWN_TH._THEME_DEFAULT["tokens"]) if _OWN_TH else {})
    t.update(db["tokens"])
    t.update(LOCK_LAMPS_V0157)
    return t, db["book"]


def _js_patched_v0157(serif: str) -> str:
    """字級套件 JS 的字體吸附對 serif 選擇器放行(v1 / v2 兩種寫法都認;都不在 → 原樣回,自測會紅)。"""
    js = _ORIG_JS
    for old, new in SNAP_V0157:
        js = js.replace(old, new % serif)
    return js


def _patch_owners_v0157() -> dict:
    """把字級套件本體(鏈上每份 typekit_book / typekit_block)與 v0144 的 via-theme 讀冊換成本版(模組層一次;自測會確認)。"""
    r = {"typekit": [], "theme": False, "js": False}
    if _OWN_TK is not None:
        for m in _chain_v0157():                         # v0154 本體 · v0153 被 v0154 指派的那份 … 都換,前版自己的「已改走本版」檢查仍成立
            if "typekit_book" in vars(m):
                m.typekit_book = typekit_book
                r["typekit"].append(Path(m.__file__).stem[-5:])
            if "typekit_block" in vars(m):
                m.typekit_block = typekit_block
        _OWN_TK._TK_JS = _js_patched_v0157(design_book()["serif"])
        r["js"] = ".closest('" in _OWN_TK._TK_JS and _OWN_TK._TK_JS != _ORIG_JS
    if _OWN_TH is not None:
        _OWN_TH.ui_theme_load = ui_theme_load
        r["theme"] = True
    return r


PATCHED_V0157 = _patch_owners_v0157()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


_PAGE_V0157 = """<!doctype html><html><head><meta charset="utf-8"><style>:root{--line:#e0e0e0;--panel:#f7f7f7}body{font:12px Arial}th{background:#111827;color:#fff}</style></head>
<body><header><h1>VDF U/I</h1><small>x</small></header><aside><div class='card'><b>k</b><label>l</label><button class='p'>跑</button></div></aside>
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

    print("=== %s %s · 薄尾自測(設計稿 1c 汝窯天青視覺)===" % (_STEM, TAG))
    db = design_book()
    t = db.get("tokens") or {}
    chk("① 冊尾版 ≥ v0103:有 systems.VDF · design.css · serif / cjk-serif token · serif_selector(冊 %s)" % db.get("book"),
        db.get("book") and _vnum_v0157(db["book"]) >= 103 and db.get("css") and not db.get("why") and t.get("serif") and t.get("cjk-serif")
        and db.get("serif") == "h1,.via-serif,.brand", db)
    chk("② 1c 覆蓋:頁首條 #cfe0dc / #16302b · 青瓷綠 acc #3c6660 · 左欄 #f2f8f6 · 標 \"1c\" · 品牌 VERITAS DATA FORGE · 燈四色仍鎖(#dc2626)· 主字體仍微軟正黑體",
        t.get("head") == "#cfe0dc" and t.get("head-txt") == "#16302b" and t.get("acc") == "#3c6660" and t.get("panel-2") == "#f2f8f6"
        and t.get("tag") == '"1c"' and t.get("brand") == '"VERITAS DATA FORGE"' and t.get("lamp-red") == "#dc2626" and t.get("lamp-green") == "#16a34a"
        and str(t.get("font", "")).startswith('"Microsoft JhengHei UI"'), {k: t.get(k) for k in ("head", "acc", "panel-2", "tag", "lamp-red")})
    tk = typekit_book()
    blk = typekit_block(tk)
    chk("③ 套件仍一段 style + 一段 script:尾端接 [VIA:DESIGN] :root(--sys:#3c6660 · --lamp-red:#dc2626 · --serif)+ design.css · 零外部連結 · JS 字體吸附對 h1 / .via-serif / .brand 放行",
        blk.count("<style") == 1 and blk.count("<script") == 1 and "[VIA:DESIGN:" in blk and "--sys:#3c6660" in blk and "--lamp-red:#dc2626" in blk and "--serif:" in blk
        and "header h1::before" in blk and "closest('h1,.via-serif,.brand')" in blk and not any(o in blk for o, _ in SNAP_V0157)
        and not re.search(r"https?://(?!www\.w3\.org/1999/xhtml)|<link|\bsrc=|@import|fetch\(", blk), blk[:200])
    once, h1 = PRIOR.typekit_apply_text(_PAGE_V0157, blk)
    twice, h2 = PRIOR.typekit_apply_text(once, blk)
    chk("④ 冪等:插在 </head> 前(頁自己的 style 之後)→ 第二次 same · 只一段;頁上 :root 有 --head:#cfe0dc(壓過頁內固定色)",
        h1 == "inserted" and h2 == "same" and twice.count("via-typekit:begin") == 1 and "--head:#cfe0dc" in twice and twice.index("<style>") < twice.index("[VIA:DESIGN:"), (h1, h2))
    chk("⑤ 本體已換:字級套件本體 %s 的 typekit_block / _TK_JS · 鏈上每份 typekit_book · v0144 的 ui_theme_load 都指到本版(MDL012 族群頁 · 其他動詞補套 · via-theme 段都走本版)" % Path(_OWN_TK.__file__).stem[-5:],
        PATCHED_V0157.get("theme") and PATCHED_V0157.get("js") and len(PATCHED_V0157.get("typekit") or []) >= 2 and _OWN_TK.typekit_block is typekit_block
        and all(getattr(m, "typekit_book", None) is typekit_book for m in _chain_v0157() if "typekit_book" in vars(m))
        and _OWN_TH.ui_theme_load is ui_theme_load and _OWN_TK.typekit_block is not _ORIG_BLOCK, PATCHED_V0157)
    tt, bk = ui_theme_load(TK_ROOT)
    css = _OWN_TH.ui_theme_css(tt)
    chk("⑥ via-theme 段改讀冊尾版 + systems.VDF:--head:#cfe0dc · --acc:#3c6660 · --lamp-red:#dc2626 · 冊名 = 尾版",
        bk == db.get("book") and 'id="via-theme"' in css and "--head:#cfe0dc" in css and "--acc:#3c6660" in css and "--lamp-red:#dc2626" in css, (bk, css[:120]))
    td = Path(tempfile.mkdtemp(prefix="pv_vdf157_"))
    try:
        reg = td / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "VIA_UI_Template_SSOT_v0100.json").write_text(json.dumps({"tokens": {"panel": "#eef2ff", "lamp-red": "#000000"}, "design": {"css": "a{color:red}@import url(x)"}}), encoding="utf-8")
        d0 = design_book(td)
        d1 = design_book(td / "none")
        chk("⑦ 誠實退路:冊沒 systems.VDF / design.css 壞(@import)→ css 不收 · why 寫明 · 燈紅仍 #dc2626;沒冊 → why · 不套",
            d0["book"] == "VIA_UI_Template_SSOT_v0100.json" and d0["css"] == "" and d0["tokens"]["panel"] == "#eef2ff" and d0["tokens"]["lamp-red"] == "#dc2626"
            and d0["why"] and "@import" in d0["why"] and "systems.VDF" in d0["why"] and d1["book"] is None and d1["why"] and design_css(d1) == "", (d0["why"], d1["why"]))
    finally:
        shutil.rmtree(td, ignore_errors=True)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式 · 本檔不起子行程 · 零網路 · 不寫冊",
        all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
        and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "1" not in body
        and "import " + "subprocess" not in body and "url" + "lib" not in body and "req" + "uests" not in body)
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑨ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s_%s 自測 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
