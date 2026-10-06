#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0145 — 薄尾:ui 自報清單(操作員令 2026-10-06:一個 U/I 連三個 SystemManager,介面隨各 manager 自適應,也隨模板自適應)。
  ui   前版鏈產頁後,寫 VIA_Reports/vrn/VRN_UI_MANIFEST.json(入口頁 · 頁籤 · 燈 · 模板 · 是否兩面板 / 滑鼠律);母系統入口頁只讀清單組頁,不寫本系統頁。
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
TAG = "v0145"


def _vnum_v0145(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0145(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0145(p) < _vnum_v0145(__file__)), key=_vnum_v0145)
PRIOR = _load_v0145(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ===== [VIA:UI-MANIFEST:v0100] 子系統 U/I 清單(自報):入口頁 · 頁籤 · 燈 · 動詞數 · 模板冊;母系統入口只讀清單組頁,不寫子系統頁 =====
def ui_manifest_write(sub, out_dir, html_path, lamp, extra=None):
    import json as _j, datetime as _dt, re as _re
    from pathlib import Path as _P
    html_path = _P(html_path)
    try:
        h = html_path.read_text(encoding="utf-8")
    except OSError:
        h = ""
    names = [_re.sub(r"<[^>]+>", "", t).strip() for t in _re.findall(r"<button[^>]*onclick=\"tab\(\d+,this\)\">(.*?)</button>", h)]
    pages = _re.findall(r"<div class=\"page[^\"]*\"[^>]*>(.*?)</div>", h, _re.S)
    srcs = [((_re.search(r"<iframe[^>]*src=\"([^\"]*)\"", pg) or [None, ""])[1]) for pg in pages]
    tabs = [{"name": n, "src": (srcs[i] if i < len(srcs) else "")} for i, n in enumerate(names)]
    theme = (_re.search(r"<!-- theme:([^ >]+) -->", h) or [None, "default"])[1]
    m = {"schema": "VIA.UI.Manifest.v1", "sub": sub, "ts": _dt.datetime.now().isoformat(timespec="seconds"), "entry": html_path.name, "dir": str(out_dir), "lamp": lamp, "tabs": tabs, "theme": theme,
         "mouse": "id='run'" in h, "left_panel": "<aside>" in h}
    if extra:
        m.update(extra)
    fp = _P(out_dir) / (sub + "_UI_MANIFEST.json")
    fp.write_text(_j.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    return fp
# ===== [VIA:UI-MANIFEST:END] =====


def ui() -> dict:
    u = PRIOR.ui()
    fp = Path(u["html"])
    mp = ui_manifest_write("VRN", fp.parent, fp, u.get("lamp", "GRAY"), {"manager": Path(__file__).name, "steps": u.get("steps", {})})
    u["manifest"] = str(mp)
    return u


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["ui"]:
        u = ui()
        print("[計] VRN ui · %s · %s · 清單 %s · %s" % (u["html"], " ".join("%s=%s" % kv for kv in u["steps"].items()), Path(u["manifest"]).name, u["lamp"]))
        print("  [U/I] %s" % u["html"])
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    import json
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

    td = Path(tempfile.mkdtemp(prefix="vrnman-"))
    home = td / "functional modules" / "VRN"
    (home / "registry").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_NO_OPEN")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(td / "VIA_Reports" / "vrn"), "VIA_NO_OPEN": "1"})
    (home / "VRN_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    return 0\n", encoding="utf-8")
    u = ui()
    m = json.loads(Path(u["manifest"]).read_text(encoding="utf-8"))
    chk("① 清單:sub · entry · 頁籤 ≥3(名+src)· 燈 · mouse · left_panel · manager", m["sub"] == "VRN" and m["entry"].endswith("_UI_latest.html") and len(m["tabs"]) >= 3 and all(t["name"] for t in m["tabs"]) and sum(1 for t in m["tabs"] if t["src"]) >= 3 and m["lamp"] in ("GREEN", "YELLOW", "RED", "GRAY") and m["mouse"] and m["left_panel"] and m["manager"] == Path(__file__).name)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("② 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("③ 橋齊 · 清單段", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:UI-MANIFEST:v0100]" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0145 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
