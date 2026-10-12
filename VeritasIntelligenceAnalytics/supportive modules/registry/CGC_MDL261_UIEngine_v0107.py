#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL261_UIEngine v0107 — 薄尾:設計稿「Veritas Header」1a 母系統視覺(VCGC 操作台;只動顏色 · 字體 · 邊角 · 頁首;版面 · 五頁 · GATE · 功能不動)

操作員令(2026-10-12):「1a for vcgc html u/i design 1b for vrn 1c for vdf only follow visual design and colors」(Claude Design 設計稿兩檔上傳;
  承同日「vrn vdf vcgc都是獨立操作台 只是顏色及lauout基本規劃相同」)。
冊:registry 的 VIA_UI_Template_SSOT 尾版(v0103 起有 systems.VCGC 覆蓋 + design.css);本檔只讀冊、不寫冊、不改他系統的檔(L120)。
  ① design_book():冊尾版 tokens + systems.VCGC(1a:米白紙底 #f2f1ec · 白卡 · 印泥紅 #9e2b25 · 青 #2f6f6f)→ 燈四色仍鎖 → design.css 只收純 CSS;
  ② 字級套件(v0106 本體)的 typekit_book / typekit_block 換成本版:同一段 <style> 尾端接 :root{全部 token} + design.css(仍一段 style + 一段 script,
     冪等換新);design.css 把操作台範本自己的 --paper / --ink / --mute / --blue / --co / --soft / --r 對到冊 token,所以 v0103 範本不改字就換色;
  ③ JS 字體吸附對冊 serif_selector(h1 · .via-serif · .brand)放行 → 品牌字與頁標題用襯線。
其餘(build · 五頁 · 匯入 · 自動跳出 · 展現規則 · 只收 VCGC 呼叫 · 零網路 · 不碰 TA-Lib)照 v0106。
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

import ast
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
_STEM = "CGC_MDL261_UIEngine"
SELF_ID = "VCGC"
LOCK_LAMPS_V0107 = {"lamp-green": "#16a34a", "lamp-yellow": "#f59e0b", "lamp-red": "#dc2626", "lamp-gray": "#9ca3af"}
CSS_BAD_RX_V0107 = re.compile(r"<|@import|url\s*\(|https?:", re.I)
SERIF_DEFAULT_V0107 = "h1,.via-serif,.brand"
SNAP_OLD_V0107 = "else if(v2[3])st.fontFamily='var(--via-font)'"
SNAP_NEW_V0107 = "else if(v2[3]&&!r[0].closest('%s'))st.fontFamily='var(--via-font)'"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = _vnum(__file__)
    hits = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < me]
    return max(hits, key=_vnum)


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0107", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
TK_ROOT = PRIOR.TK_ROOT


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _chain_v0107() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _owner_v0107(name: str):
    for m in _chain_v0107():
        if name in vars(m):
            return m
    return None


_OWN_TK = _owner_v0107("typekit_block")        # v0106 本體(字級套件 v2)
_ORIG_BOOK = _OWN_TK.typekit_book if _OWN_TK else None
_ORIG_BLOCK = _OWN_TK.typekit_block if _OWN_TK else None
_ORIG_JS = _OWN_TK._TK_JS if _OWN_TK else ""


# ---------------------------------------------------------------- 設計稿視覺(只讀冊)
def _tk_safe_v0107(v) -> str:
    return re.sub(r"[<>{};\\]", "", str(v))


def design_book(root=None) -> dict:
    """→ {book, tokens, css, serif, theme, why}:冊尾版 tokens + systems.VCGC 覆蓋(純量)· 燈四色鎖定 · design.css 只收純 CSS;沒冊 / 壞冊照實。"""
    root = Path(root or TK_ROOT)
    hits = sorted((root / "supportive modules" / "registry").glob("VIA_UI_Template_SSOT_v*.json"), key=_vnum)
    out = {"book": None, "tokens": {}, "css": "", "serif": SERIF_DEFAULT_V0107, "theme": "", "why": "找不到 VIA_UI_Template_SSOT_v*.json,設計稿視覺不套"}
    if not hits:
        return out
    out["book"] = hits[-1].name
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
        toks = {k: str(v) for k, v in (d.get("tokens") or {}).items() if not isinstance(v, (list, dict))}
        sysd = (d.get("systems") or {}).get(SELF_ID) or {}
        toks.update({k: str(v) for k, v in sysd.items() if not isinstance(v, (list, dict)) and k not in ("note", "design_section", "theme_zh")})
        toks.update(LOCK_LAMPS_V0107)
        des = d.get("design") or {}
        css = str(des.get("css") or "")
        why = []
        if not css:
            why.append("%s 沒有 design.css,只套顏色 token" % out["book"])
        elif CSS_BAD_RX_V0107.search(css):
            css = ""
            why.append("%s 的 design.css 含 < / url( / @import / http,整段不收(零網路 · 不注入標記)" % out["book"])
        if not sysd:
            why.append("%s 沒有 systems.%s,用共用 tokens" % (out["book"], SELF_ID))
        serif = re.sub(r"[^A-Za-z0-9 ,.#_>-]", "", str(des.get("serif_selector") or "")) or SERIF_DEFAULT_V0107
        out.update({"tokens": toks, "css": css, "serif": serif, "theme": str(sysd.get("theme_zh") or ""), "why": ";".join(why) or None})
    except (OSError, ValueError, AttributeError) as exc:
        out["why"] = "讀不了 %s:%s,設計稿視覺不套" % (out["book"], type(exc).__name__)
    return out


def design_css(db=None) -> str:
    """→ :root{全部 token} + design.css(接在字級套件 CSS 尾端;版面不動)。沒 token 回空字串。"""
    db = db or design_book()
    if not db.get("tokens"):
        return ""
    root = ";".join("--%s:%s" % (re.sub(r"[^a-z0-9-]", "", k), _tk_safe_v0107(v)) for k, v in db["tokens"].items())
    return "/* [VIA:DESIGN:%s] %s · %s */\n:root{%s}\n%s" % (db.get("book") or "none", SELF_ID, db.get("theme") or "", root, db.get("css") or "")


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


def _patch_owners_v0107() -> dict:
    r = {"typekit": [], "js": False}
    if _OWN_TK is not None:
        for m in _chain_v0107():                         # 鏈上每個有這兩個名字的模組都換(v0106 本體 · v0105 被 v0106 指派的那份)
            if "typekit_book" in vars(m):
                m.typekit_book = typekit_book
                r["typekit"].append(Path(m.__file__).stem[-5:])
            if "typekit_block" in vars(m):
                m.typekit_block = typekit_block
        _OWN_TK._TK_JS = _ORIG_JS.replace(SNAP_OLD_V0107, SNAP_NEW_V0107 % design_book()["serif"])
        r["js"] = SNAP_OLD_V0107 not in _OWN_TK._TK_JS
    return r


PATCHED_V0107 = _patch_owners_v0107()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


_PAGE_V0107 = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--line:#dbd9d3;--blue:#4c78a8;--co:#b5291a;--r:9px}body{font:13px x}</style></head>
<body><div class="app"><aside class="side"><div class="brand"><span class="seal">V</span><div class="bt"><b>VIA</b><small>x</small></div></div></aside>
<main class="main"><div class="top"><h1>操作台 <small>y</small></h1></div><div class="card"><table><tr><th>燈</th></tr><tr><td><i class='lp GREEN'></i></td></tr></table></div></main></div></body></html>"""


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print(f"  [OK] {name}")
        else:
            f += 1
            print(f"  [FAIL] {name}" + (f" · {str(note)[:300]}" if note else ""))

    print(f"=== {TAG} · 薄尾自測(設計稿 1a 母系統視覺:操作台)===")
    db = design_book()
    t = db.get("tokens") or {}
    chk("① 冊尾版 ≥ v0103:有 systems.VCGC · design.css · serif / cjk-serif token · serif_selector(冊 %s)" % db.get("book"),
        db.get("book") and _vnum(db["book"]) >= 103 and db.get("css") and not db.get("why") and t.get("serif") and t.get("cjk-serif")
        and db.get("serif") == "h1,.via-serif,.brand", db)
    chk("② 1a 覆蓋:米白紙底 #f2f1ec · 白卡 · 頁首 #ffffff / #1b1a17 · 青 acc #2f6f6f · 印泥紅 sys #9e2b25 · 標 \"1a\" · 品牌 VERITAS INTELLIGENCE ANALYTICS · 燈四色仍鎖",
        t.get("bg") == "#f2f1ec" and t.get("panel") == "#ffffff" and t.get("head") == "#ffffff" and t.get("head-txt") == "#1b1a17" and t.get("acc") == "#2f6f6f"
        and t.get("sys") == "#9e2b25" and t.get("tag") == '"1a"' and t.get("brand") == '"VERITAS INTELLIGENCE ANALYTICS"' and t.get("lamp-red") == "#dc2626"
        and t.get("lamp-green") == "#16a34a", {k: t.get(k) for k in ("bg", "head", "acc", "sys", "tag", "lamp-red")})
    tk = typekit_book()
    blk = typekit_block(tk)
    chk("③ 套件仍一段 style + 一段 script(v2:present / pick 仍在):尾端接 [VIA:DESIGN] :root(--sys:#9e2b25 · --lamp-red:#dc2626 · --serif)+ design.css(範本變數對映 --paper:var(--panel) · --ink:var(--txt) · --co:var(--seal))· JS 字體吸附對 h1 / .via-serif / .brand 放行 · 零外部連結",
        blk.count("<style") == 1 and blk.count("<script") == 1 and "function present(" in blk and "[VIA:DESIGN:" in blk and "--sys:#9e2b25" in blk and "--lamp-red:#dc2626" in blk
        and "--serif:" in blk and "--paper:var(--panel)" in blk and "--ink:var(--txt)" in blk and "--co:var(--seal)" in blk and ".top h1::before" in blk
        and "closest('h1,.via-serif,.brand')" in blk and SNAP_OLD_V0107 not in blk
        and not re.search(r"https?://(?!www\.w3\.org/1999/xhtml)|<link|\bsrc=|@import|fetch\(", blk), blk[:200])
    once, h1 = PRIOR.typekit_apply_text(_PAGE_V0107, blk)
    twice, h2 = PRIOR.typekit_apply_text(once, blk)
    chk("④ 冪等:插在 </head> 前(範本自己的 :root 之後 → 對映壓過固定色)→ 第二次 same · 只一段;頁上有 --bg:#f2f1ec · --seal:#9e2b25",
        h1 == "inserted" and h2 == "same" and twice.count("via-typekit:begin") == 1 and "--bg:#f2f1ec" in twice and "--seal:#9e2b25" in twice
        and twice.index("--co:#b5291a") < twice.index("[VIA:DESIGN:"), (h1, h2))
    chk("⑤ 本體已換:v0106 的 typekit_block / _TK_JS · 鏈上每份 typekit_book(v0106 · v0105 build 用的那份)都指到本版",
        PATCHED_V0107.get("js") and len(PATCHED_V0107.get("typekit") or []) >= 2 and _OWN_TK.typekit_block is typekit_block
        and all(getattr(m, "typekit_book", None) is typekit_book for m in _chain_v0107() if "typekit_book" in vars(m)), PATCHED_V0107)
    tmp = Path(tempfile.mkdtemp(prefix="mdl261v7_"))
    keep_wd = (BASE.WORK_DIR, BASE.WORK_CONFIG)
    try:
        BASE.WORK_DIR = tmp / "work"
        BASE.WORK_CONFIG = BASE.WORK_DIR / "ui_config.json"
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        cfg = BASE.load_config(sets=[f"locations.db_root={home}"])
        with contextlib.redirect_stdout(io.StringIO()):
            snap, out, rep = BASE.build(cfg, home, tmp / "ui" / "page.html")
        r1 = PRIOR.typekit_apply(out, tk)
        page = out.read_text(encoding="utf-8")
        chk("⑥ 真建頁(v0104 範本 + 快照)→ 套件只一段且帶 [VIA:DESIGN] 一段 · 範本 :root 在前、對映在後 · 左下 GATE · 三系統仍在",
            r1["how"] == "inserted" and page.count("via-typekit:begin") == 1 and page.count('<style id="via-typekit">') == 1 and "[VIA:DESIGN:" in page and 'id="gates3"' in page
            and page.index("--paper:#fff") < page.index("--paper:var(--panel)") and "function present(" in page, r1)
        reg = tmp / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "VIA_UI_Template_SSOT_v0100.json").write_text(json.dumps({"tokens": {"panel": "#eef2ff", "lamp-red": "#000000"}, "design": {"css": "a{color:red}@import url(x)"}}), encoding="utf-8")
        d0 = design_book(tmp)
        d1 = design_book(tmp / "none")
        chk("⑦ 誠實退路:冊沒 systems.VCGC / design.css 壞(@import)→ css 不收 · why 寫明 · 燈紅仍 #dc2626;沒冊 → why · 不套",
            d0["book"] == "VIA_UI_Template_SSOT_v0100.json" and d0["css"] == "" and d0["tokens"]["panel"] == "#eef2ff" and d0["tokens"]["lamp-red"] == "#dc2626"
            and d0["why"] and "@import" in d0["why"] and "systems.VCGC" in d0["why"] and d1["book"] is None and d1["why"] and design_css(d1) == "", (d0["why"], d1["why"]))
    finally:
        BASE.WORK_DIR, BASE.WORK_CONFIG = keep_wd
        shutil.rmtree(tmp, ignore_errors=True)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 檔頭:加速器橋 · 網路橋在(__future__ 之後);不碰 TA-Lib;不直派子行程;不載外部函式庫;只讀冊不寫冊;不寫他系統的檔",
        "[VIA:ACCEL-BRIDGE:" in text and "[VIA:NET-BRIDGE:" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in text and "cdn" + "js" not in text and "unp" + "kg.com" not in text
        and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.name or "").split(".")[0] == "sub" + "process" for x in n.names) for n in ast.walk(ast.parse(text)))
        and "VRN_" + "SystemManager" not in text and "VDF_" + "SystemManager" not in text)
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        prior_rc = 0
        print("  ── 前版鏈自測略過(VIA_SKIP_PRIOR_SELFTEST=1)──")
    else:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
        print("  ── 前版鏈自測(摘末行)── " + (buf.getvalue().strip().splitlines() or ["(無輸出)"])[-1])
    chk(f"⑨ 前版鏈 {PRIOR_PATH.stem} 自測 rc 0", prior_rc == 0)
    print(f"[計] {TAG} 本版 {p}/{p + f} · {'PASS' if f == 0 else 'FAIL'}")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
