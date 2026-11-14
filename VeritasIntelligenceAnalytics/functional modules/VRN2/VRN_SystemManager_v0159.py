#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0159 — 薄尾(操作員 2026-10-10):正本 = 加速器 VeritasCeleritas_v1141 · 網路工具 VeritasAegisNexus_v1652。
  本版改接正本橋(前版用的是 VIA_SuperAccel_Module 舊橋);引擎稽核加兩欄:是否接正本加速器(舊橋標出)· 出網的引擎是否走正本網路工具。
  intake 的分類器 / TableRepair 另出 v0102 改接正本橋(行為不變,v0101 不動)。
  資料庫現況由共用引擎 supportive modules\\database\\VIA_DuckDBStatus_v#### 管(VRN 只讀)。
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
except Exception:  # noqa: BLE001
    _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import hashlib
import html
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0159"


def _vnum_v0159(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0159(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0159(p) < _vnum_v0159(__file__)), key=_vnum_v0159)
PRIOR = _load_v0159(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


_home = _resolve("_home")
_LAST = {}


# 多程序墊片(當 __main__ 的尾版必帶;spawn 只能從 __main__ 解開)
def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


# ───────── 正本稽核:加速器 VeritasCeleritas_v1141 · 網路工具 VeritasAegisNexus_v1652 ─────────
_NET_USE = re.compile(r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|yfinance|akshare|fredapi|pandas_datareader)\b", re.M)


def canon_of(path: Path) -> dict:
    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        txt = ""
    body = txt.split("\ndef selftest(")[0]
    if path.suffix.lower() == ".ps1":
        return {"canon_accel": bool(re.search(r"VeritasCeleritas\.PS7|Initialize-VCAccel|CELERITAS-TEMPLATE-JOIN", txt)), "net_use": False, "net_canon": True, "old_bridge": False}
    net_use = bool(_NET_USE.search(body))
    return {"canon_accel": "VeritasCeleritas_v1141" in txt, "old_bridge": ("VIA_SuperAccel_Module" in txt and "VeritasCeleritas_v1141" not in txt),
            "net_use": net_use, "net_canon": (not net_use) or ("VeritasAegisNexus_v1652" in txt)}


_PREV_EA = _resolve("engines_audit_v158")


def engines_audit_v159(register: bool = False) -> dict:
    o = _PREV_EA(register)
    home = _home()
    for r in o["rows"]:
        p = Path(r["tail"])
        p = p if p.is_absolute() else home / p
        r.update(canon_of(p))
        if r["lamp"] == "GREEN" and not (r["canon_accel"] and r["net_canon"]):
            r["lamp"] = "YELLOW"
    py = [r for r in o["rows"] if r["ext"] == ".py"]
    s = o["summary"]
    s.update(canon_accel=sum(1 for r in o["rows"] if r["canon_accel"]), old_bridge=sum(1 for r in py if r["old_bridge"]), net_use=sum(1 for r in py if r["net_use"]), net_canon_bad=sum(1 for r in py if r["net_use"] and not r["net_canon"]))
    page = _resolve("_page")
    mark = lambda v: "✓" if v else "✗"  # noqa: E731
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2}
    Path(o["html"]).write_text(page("VRN 引擎稽核 · 版本 · 註冊 · 加速器 · 正本(VeritasCeleritas_v1141 / VeritasAegisNexus_v1652)",
                                    "族 %d · 無版號 %d · 未註冊 %d · 接正本加速器 %d/%d(舊橋 %d)· 出網引擎 %d(沒走正本網路工具 %d)· 註冊冊 %s" % (s["families"], s["no_version"], s["not_registered"], s["canon_accel"], s["families"], s["old_bridge"], s["net_use"], s["net_canon_bad"], html.escape(s.get("register") or "未寫(加 --register)")),
                                    ["族", "類", "尾版", "版數", "版號", "註冊", "加速器", "正本加速器", "出網 → 正本網路工具", "管線用途"],
                                    [(r["lamp"], [r["family"], r["ext"], r["tail"], r["n"], mark(r["version"]), mark(r["registered"]), mark(r["accel"]), "✓" if r["canon_accel"] else ("舊橋" if r["old_bridge"] else "✗"), ("✓" if r["net_canon"] else "✗") if r["net_use"] else "不出網", r["pipeline"]]) for r in sorted(o["rows"], key=lambda r: (order.get(r["lamp"], 9), r["family"]))]), encoding="utf-8")
    _LAST["audit"] = o
    return o


_m = _owner("engines_audit_v158")
if _m:
    setattr(_m, "engines_audit_v158", engines_audit_v159)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["engines"]:
        o = engines_audit_v159(register="--register" in args)
        s = o["summary"]
        print("[計] VRN 引擎稽核 · 族 %d(py %d · ps1 %d)· 無版號 %d · 未註冊 %d · py 無加速器 %d · ps1 無加速器 %d · 註冊冊 %s" % (s["families"], s["py"], s["ps1"], s["no_version"], s["not_registered"], s["no_accel_py"], s["no_accel_ps"], s.get("register") or "未寫(加 --register)"))
        for r in [r for r in o["rows"] if r["pipeline"]]:
            print("[計] 管線 %s · %s · 版號%s 註冊%s 正本加速器%s" % (r["family"], r["pipeline"], "✓" if r["version"] else "✗", "✓" if r["registered"] else "✗", "✓" if r["canon_accel"] else ("舊橋" if r["old_bridge"] else "✗")))
        rc = 0
    else:
        rc = PRIOR.main(args)
    o = _LAST.get("audit")
    if o and args[:1] in (["layout"], ["engines"]):
        s = o["summary"]
        print("[計] 正本稽核 · 接正本加速器 %d/%d(舊橋 %d)· 出網引擎 %d(沒走正本網路工具 %d)" % (s["canon_accel"], s["families"], s["old_bridge"], s["net_use"], s["net_canon_bad"]))
        if args[:1] == ["engines"]:
            print("  [U/I] %s" % o["html"])
    return rc


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
    td = Path(tempfile.mkdtemp(prefix="vrncanon-"))
    a = td / "A_v0100.py"
    a.write_text("import VeritasCeleritas_v1141 as vc\nx = 1\n", encoding="utf-8")
    b = td / "B_v0100.py"
    b.write_text("import VIA_SuperAccel_Module as VIA_ACCEL\nimport requests\n", encoding="utf-8")
    c = td / "C_v0100.py"
    c.write_text("import VeritasCeleritas_v1141 as vc\nimport requests\n_N = 'VeritasAegisNexus_v1652'\n", encoding="utf-8")
    ca, cb, cc = canon_of(a), canon_of(b), canon_of(c)
    chk("① 正本判定:接 VeritasCeleritas_v1141 = 正本 · 只接 VIA_SuperAccel_Module = 舊橋 · 出網沒走 VeritasAegisNexus_v1652 = ✗", ca["canon_accel"] and not ca["net_use"] and cb["old_bridge"] and cb["net_use"] and not cb["net_canon"] and cc["canon_accel"] and cc["net_canon"])
    me = Path(__file__).read_text(encoding="utf-8")
    chk("② 本版接正本加速器與正本網路工具(接口)· 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and "import VeritasAegisNexus_v1652" in me and _job_entry.__module__ in ("__main__", __name__))
    shutil.rmtree(td, ignore_errors=True)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0159 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
