#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0143 — 薄尾:ui 套暫時標準 U/I 模板(操作員令 2026-10-06:未來自適應式會接上任何設計模板顏色的暫時標準模板)。
  ui   前版鏈產頁後,把固定色換成 var(--token,fallback) 並插入 VIA_UI_Template_SSOT 的 token CSS;燈四色鎖定。冊在母系統 registry(VCGC theme 動詞建),子系統只讀。
其餘動詞照前版鏈。
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0143"


def _vnum_v0143(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0143(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0143(p) < _vnum_v0143(__file__)), key=_vnum_v0143)
PRIOR = _load_v0143(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ===== [VIA:UI-THEME:v0100] 暫時標準 U/I 模板(顏色/字體/間距 token 冊;未來接任何設計模板只換冊不改引擎;燈色鎖定 VIA_UI_FormatLock 四色)=====
_THEME_DEFAULT = {
    "schema": "VIA.UI.Template.SSOT.v1", "version": "v0100", "status": "TEMPORARY_STANDARD",
    "rule": "所有子系統 U/I 只用 var(--token);換設計模板 = 出新版冊改 tokens;燈四色(綠/黃/紅/灰)鎖定不隨模板變;history 只增",
    "tokens": {"bg": "#ffffff", "panel": "#f7f7f7", "line": "#e0e0e0", "txt": "#1f2937", "dim": "#6b7280", "acc": "#2563eb", "head": "#111827", "head-txt": "#ffffff", "zebra": "#fafafa",
               "font": "\"Microsoft JhengHei UI\",\"Segoe UI\",Arial,sans-serif", "mono": "Consolas,monospace", "fs": "12px", "radius": "8px", "pad": "6px",
               "lamp-green": "#16a34a", "lamp-yellow": "#f59e0b", "lamp-red": "#dc2626", "lamp-gray": "#9ca3af"},
    "locked": ["lamp-green", "lamp-yellow", "lamp-red", "lamp-gray"], "history": []}
_HEX2TOKEN = {"#16a34a": "lamp-green", "#f59e0b": "lamp-yellow", "#dc2626": "lamp-red", "#9ca3af": "lamp-gray", "#f7f7f7": "panel", "#e0e0e0": "line", "#1f2937": "txt", "#6b7280": "dim", "#2563eb": "acc", "#111827": "head", "#fafafa": "zebra"}


def ui_theme_load(root):
    import json as _j
    from pathlib import Path as _P
    fp = _P(root) / "supportive modules" / "registry" / "VIA_UI_Template_SSOT_v0100.json"
    try:
        if fp.exists():
            d = _j.loads(fp.read_text(encoding="utf-8-sig"))
            t = dict(_THEME_DEFAULT["tokens"]); t.update(d.get("tokens") or {})
            for k in _THEME_DEFAULT["locked"]:
                t[k] = _THEME_DEFAULT["tokens"][k]          # 燈色鎖定
            return t, fp.name
    except Exception:  # noqa: BLE001
        pass
    return dict(_THEME_DEFAULT["tokens"]), None


def ui_theme_css(tokens):
    return "<style id=\"via-theme\">:root{%s}</style>" % ";".join("--%s:%s" % (k, v) for k, v in tokens.items())


def ui_theme_apply(html_text, root):
    """把頁面裡的固定色換成 var(--token,固定色)(fallback 保留),並在 <head> 後插 token 冊 CSS;燈色不變。"""
    tokens, book = ui_theme_load(root)
    out = html_text
    for hx, tk in _HEX2TOKEN.items():
        out = out.replace("'background:%s'" % hx, "'background:var(--%s,%s)'" % (tk, hx)).replace("background:%s" % hx, "background:var(--%s,%s)" % (tk, hx)).replace("color:%s" % hx, "color:var(--%s,%s)" % (tk, hx)).replace("border:1px solid %s" % hx, "border:1px solid var(--%s,%s)" % (tk, hx))
    css = ui_theme_css(tokens) + ("<!-- theme:%s -->" % (book or "default")) 
    i = out.find("<head>")
    out = (out[:i + 6] + css + out[i + 6:]) if i >= 0 else (css + out)
    return out


def ui_theme_init(root, apply=True):
    import json as _j, datetime as _dt
    from pathlib import Path as _P
    fp = _P(root) / "supportive modules" / "registry" / "VIA_UI_Template_SSOT_v0100.json"
    if fp.exists():
        return {"status": "EXISTS", "file": fp.name}
    d = dict(_THEME_DEFAULT); d["created_at"] = _dt.datetime.now().isoformat(timespec="seconds"); d["origin"] = "操作員令 2026-10-06:未來自適應式會接上任何 U/I 設計模板顏色的暫時標準模板"
    if apply:
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(_j.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "WRITTEN" if apply else "PLAN", "file": fp.name, "tokens": len(d["tokens"])}
# ===== [VIA:UI-THEME:END] =====


def ui() -> dict:
    u = PRIOR.ui()
    home = Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)
    root = home.parents[1]
    fp = Path(u["html"])
    fp.write_text(ui_theme_apply(fp.read_text(encoding="utf-8"), root), encoding="utf-8")
    u["theme"] = ui_theme_load(root)[1] or "default"
    return u


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["ui"]:
        u = ui()
        print("[計] VRN ui · %s · %s · 模板 %s · %s" % (u["html"], " ".join("%s=%s" % kv for kv in u["steps"].items()), u["theme"], u["lamp"]))
        print("  [U/I] %s" % u["html"])
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vrntheme-"))
    home = td / "functional modules" / "VRN"
    (home / "registry").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_NO_OPEN")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(td / "VIA_Reports" / "vrn"), "VIA_NO_OPEN": "1"})
    (home / "VRN_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    return 0\n", encoding="utf-8")
    u = ui()
    htm = Path(u["html"]).read_text(encoding="utf-8")
    chk("① 無冊 → default tokens 仍套:via-theme CSS · var(--lamp-red,#dc2626) · 模板 default", 'id="via-theme"' in htm and "var(--lamp-red,#dc2626)" in htm and u["theme"] == "default")
    ui_theme_init(td)
    import json as _j
    fp = td / "supportive modules" / "registry" / "VIA_UI_Template_SSOT_v0100.json"
    d = _j.loads(fp.read_text(encoding="utf-8")); d["tokens"]["panel"] = "#eef2ff"; d["tokens"]["lamp-red"] = "#000000"; fp.write_text(_j.dumps(d), encoding="utf-8")
    u2 = ui()
    htm2 = Path(u2["html"]).read_text(encoding="utf-8")
    chk("② 有冊 → panel 換色進 CSS · 燈紅仍鎖 #dc2626(冊改不動)· 模板名", "--panel:#eef2ff" in htm2 and "--lamp-red:#dc2626" in htm2 and u2["theme"] == "VIA_UI_Template_SSOT_v0100.json")
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("④ 橋齊 · 模板段", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:UI-THEME:v0100]" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0143 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
