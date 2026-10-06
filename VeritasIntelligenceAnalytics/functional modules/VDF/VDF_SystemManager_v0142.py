#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0142 — 薄尾:chain 動詞 + 鏈解析器(操作員 2026-10-06「繼續思考驗證方式」:ui 在正式樹上報 health/table_matrix 缺動詞,沙盒卻找得到 → 不再靠 getattr 透傳碰運氣,改成可驗證的鏈走訪)。
  chain [名稱…]       走訪 PRIOR 鏈每一版:版 · 有無 __getattr__ · 定義的頂層函式數 · 每個要找的名稱在哪一版找到(深度);預設找 health table_matrix panorama ui extract fn table dormant tidy
                      → 貼回包一行一版;找不到的名稱 [RED];中途某版無 __getattr__ 且其上找不到 → [RED] 斷鏈在哪一版
  ui                  改用 _resolve():沿鏈逐版用 vars(模組) 直接找,不靠 __getattr__;任何一版壞掉都能跨過去;步驟結果帶「在 vNNNN 找到」
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
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v0142"


def _vnum_v0142(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0142(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0142(p) < _vnum_v0142(__file__)), key=_vnum_v0142)
PRIOR = _load_v0142(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0142() -> list:
    """[(版名, 模組)] 從 PRIOR 往下,每版用它自己的 PRIOR 屬性(vars 直取,不經 __getattr__)。"""
    import types as _types
    out, mod, seen = [], PRIOR, set()
    while isinstance(mod, _types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        v = vars(mod)
        out.append((Path(v.get("__file__", "?")).stem, mod))
        nxt = None
        for k in ("PRIOR", "_PRIOR", "PRIOR_MOD", "prior", "_prior"):
            if isinstance(v.get(k), _types.ModuleType):
                nxt = v[k]
                break
        if nxt is None and any(k in v for k in ("PRIOR", "_PRIOR", "PRIOR_MOD")):
            out.append(("(%s 的 PRIOR 不是模組:%s)" % (Path(v.get("__file__", "?")).stem, type(v.get("PRIOR") or v.get("_PRIOR") or v.get("PRIOR_MOD")).__name__), None))
        mod = nxt
    return [(s, m) for s, m in out if m is not None] + [(s, m) for s, m in out if m is None]


def _resolve(name: str):
    """沿鏈逐版 vars() 直找;回 (物件, 版名) 或 (None, None)。"""
    for stem, mod in _chain_v0142():
        if mod is not None and name in vars(mod):
            return vars(mod)[name], stem
    return None, None


def chain_report(names) -> dict:
    rows = []
    for stem, mod in _chain_v0142():
        if mod is None:
            rows.append({"version": stem, "getattr": False, "defs": 0, "has": []})
            continue
        v = vars(mod)
        rows.append({"version": stem, "getattr": "__getattr__" in v, "defs": sum(1 for k, x in v.items() if callable(x) and getattr(x, "__module__", None) == mod.__name__ and not k.startswith("__")), "has": [n for n in names if n in v]})
    found = {n: _resolve(n)[1] for n in names}
    broken = None
    for i, r in enumerate(rows):
        if not r["getattr"] and i < len(rows) - 1:
            below = {n for rr in rows[i + 1:] for n in rr["has"]}
            need = [n for n in names if n not in {m for rr in rows[:i + 1] for m in rr["has"]} and n in below]
            if need:
                broken = {"at": r["version"], "blocks": need}
            break
    missing = [n for n, s in found.items() if not s]
    return {"verb": "chain", "tail": Path(__file__).stem, "depth": len(rows), "rows": rows, "found": found, "missing": missing, "broken": broken, "lamp": "RED" if (missing or broken) else "GREEN"}


def _print_chain(o: dict) -> None:
    print("[計] VDF chain · 尾 %s · 深 %d · 找 %s · 缺 %s · 斷鏈 %s · %s" % (o["tail"], o["depth"], " ".join("%s@%s" % (n, s or "✗") for n, s in o["found"].items()), ",".join(o["missing"]) or "0", (o["broken"]["at"] + " 擋 " + ",".join(o["broken"]["blocks"])) if o["broken"] else "無", o["lamp"]))
    for r in o["rows"]:
        print("  [%s] %s · __getattr__ %s · 定義 %d%s" % ("OK" if r["getattr"] else "YEL", r["version"], "有" if r["getattr"] else "無", r["defs"], (" · 有:" + ",".join(r["has"])) if r["has"] else ""))
    for n in o["missing"]:
        print("  [RED] %s 整條鏈都沒有" % n)
    if o["broken"]:
        print("  [RED] 斷鏈:%s 無 __getattr__,擋住 %s(getattr 透傳到這裡就 AttributeError)" % (o["broken"]["at"], ",".join(o["broken"]["blocks"])))


def ui() -> dict:
    """同 v0141 的兩面板,但三段動詞改 _resolve 沿鏈直找;每段記在哪版找到。"""
    home = Path(os.environ.get("VIA_VDF_HOME") or HERE)
    out_dir = Path(os.environ.get("VIA_VDF_HEALTH_OUT") or (home.parents[1] / "VIA_Reports" / "vdf"))
    out_dir.mkdir(parents=True, exist_ok=True)
    steps = {}
    for name in ("health", "table_matrix", "panorama"):
        fn, where = _resolve(name)
        if not fn:
            steps[name] = "缺動詞(整條鏈)"
            continue
        try:
            steps[name] = ("OK@" + where) if fn() is not None else ("回 None@" + where)
        except Exception as exc:  # noqa: BLE001
            steps[name] = "%s@%s:%s" % (type(exc).__name__, where, str(exc)[:60])
    try:
        verbs = json.loads((out_dir / "PANORAMA_latest.json").read_text(encoding="utf-8-sig")).get("verbs", {})
    except (OSError, ValueError):
        verbs = {}
    sm_ui2, _ = _resolve("sm_ui2")
    launcher = os.environ.get("VIA_LAUNCHER") or str(Path(os.environ.get("USERPROFILE") or "~").expanduser() / "Downloads" / "Invoke-VIA-Launch-v0101.ps1")
    fp = sm_ui2("VDF", home, out_dir, datetime.datetime.now().isoformat(timespec="seconds"), verbs, launcher)
    opened = False
    if os.environ.get("VIA_NO_OPEN") != "1" and os.name == "nt":
        try:
            os.startfile(str(fp))  # type: ignore[attr-defined]
            opened = True
        except OSError:
            pass
    return {"verb": "ui", "html": str(fp), "steps": steps, "opened": opened, "lamp": "GREEN" if all(v.startswith("OK") for v in steps.values()) else "YELLOW"}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["chain"]:
        names = args[1:] or ["health", "table_matrix", "panorama", "ui", "extract", "fn", "table", "dormant", "tidy", "sm_health", "sm_ui2"]
        o = chain_report(names)
        _print_chain(o)
        return 1 if o["lamp"] == "RED" else 0
    if args[:1] == ["ui"]:
        u = ui()
        print("[計] VDF ui · %s · %s · 已開 %s · %s" % (u["html"], " ".join("%s=%s" % kv for kv in u["steps"].items()), u["opened"], u["lamp"]))
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

    o = chain_report(["health", "table_matrix", "panorama", "sm_ui2", "nosuch_zz"])
    chk("① chain:深度 ≥1 · health/table_matrix/panorama/sm_ui2 都在鏈上某版找到 · nosuch_zz 缺", o["depth"] >= 1 and all(o["found"][n] for n in ("health", "table_matrix", "panorama", "sm_ui2")) and o["missing"] == ["nosuch_zz"])
    td = Path(tempfile.mkdtemp(prefix="vdfchain-"))
    home = td / "functional modules" / "VDF"
    (home / "registry").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VDF_HOME", "VIA_VDF_HEALTH_OUT", "VIA_NO_OPEN")}
    os.environ.update({"VIA_VDF_HOME": str(home), "VIA_VDF_HEALTH_OUT": str(td / "VIA_Reports" / "vdf"), "VIA_NO_OPEN": "1"})
    (home / "VDF_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    return 0\n", encoding="utf-8")
    u = ui()
    chk("② ui 改 _resolve:三段都 OK@vNNNN(帶找到的版)· 頁在", all(v.startswith("OK@VDF_SystemManager_v") for v in u["steps"].values()) and Path(u["html"]).exists())
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("④ 帶加速器橋 · NET/LIB 橋 · 鏈解析器", "[VIA:ACCEL-BRIDGE:v0100]" in body and "def _resolve(" in body and "[VIA:NET-BRIDGE:v0100]" in body and "[VIA:LIB-BRIDGE:v0100]" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0142 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
