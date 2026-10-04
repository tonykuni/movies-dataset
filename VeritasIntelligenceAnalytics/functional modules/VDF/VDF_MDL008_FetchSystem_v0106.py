#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0106 — 薄尾:block / fixture 的 curl_cffi 封口改成「屬性可取、呼叫才擋」· 冊 v0105

容器裝上 akshare 1.19.1 後(操作員 2026-10-04「開閘授權一切」),整合測試 MDL003(fixture)rc 1:
  akshare/economic/macro_china_nbs.py 在 import 時就讀 `curl_requests.Session`(型別註記),
  v0100 的封口把 curl_cffi 整個換成「每個屬性都是 deny 函式」的模組 → 'function' object has no attribute 'Session'。
  v0104 一樣紅(不是 v0105 造成;akshare 以前在容器裡缺席 = ABSENT 才沒踩到)。
  本版封口:curl_cffi 與 curl_cffi.requests 的任何屬性都是「拒絕類別」—— 可取屬性(.Session · .exceptions.X)、
  可當型別註記與父類別、isinstance 不炸;一旦呼叫 / 建構就照 v0100 計 blocked 並拋 OSError(VDF_FETCH_NET_BLOCKED)。
  socket · urllib 照 v0100 封;fixture 的 requests / yfinance 替身照 v0100。
冊 v0105:MDL011 改指 v0101(params 無註冊表 = NODATA rc 2,不再 KeyError)。
其餘(live urllib 改道與計數 · output_hub 歸位 · nodata 標記 · fill / fill-matrix / --progress · 雙閘 rc 4)照 v0105。
不碰 TA-Lib;不讀寫同意閘(只問網路工具)。
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

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0106(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0106(p) < _vnum_v0106(__file__)), key=_vnum_v0106)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0104, V0101, BASE = PRIOR.PRIOR, PRIOR.V0101, PRIOR.BASE


def __getattr__(name):
    return getattr(PRIOR, name)


_RUN_V0105 = PRIOR.run_v0105
_BLOCK_V0100 = BASE._install_block_sockets
_LOAD_V0105 = PRIOR.load_book_v0105
BOOK_V0105 = HERE / "VDF_FetchSystem_SSOT_v0105.json"


def load_book_v0106(path: Path = BOOK_V0105) -> dict:
    return _LOAD_V0105(path)


def _deny_v0106(*a, **k):
    BASE.FIX_STATS["blocked"] += 1
    raise OSError("VDF_FETCH_NET_BLOCKED")


class _DenyMeta(type):
    """拒絕類別的型別:取屬性回另一個拒絕類別(.Session · .exceptions.RequestException …);呼叫 / 建構 = 擋。"""

    def __getattr__(cls, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return _deny_class_v0106(name)

    def __call__(cls, *a, **k):
        _deny_v0106()


def _deny_class_v0106(name: str):
    return _DenyMeta(str(name), (), {"__module__": "curl_cffi"})


def _deny_module_v0106(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)

    def _ga(attr):
        if attr.startswith("__") and attr.endswith("__"):
            raise AttributeError(attr)
        return _deny_class_v0106(attr)
    mod.__getattr__ = _ga
    return mod


def block_sockets_v0106() -> None:
    """同 v0100 封口(socket · urllib · curl_cffi),只把 curl_cffi 換成屬性可取、呼叫才擋。"""
    _BLOCK_V0100()
    cc, ccr = _deny_module_v0106("curl_cffi"), _deny_module_v0106("curl_cffi.requests")
    cc.requests = ccr
    sys.modules["curl_cffi"] = cc
    sys.modules["curl_cffi.requests"] = ccr


def run_v0106(*args, **kwargs):
    """同 v0105 run(nodata 標記改判);子行程改從本版起(新封口與冊 v0105 在子行程裡生效),呼叫完還原。"""
    keep = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        return _RUN_V0105(*args, **kwargs)
    finally:
        PRIOR.__dict__["__file__"] = keep


def _install_v0106() -> None:
    BASE._install_block_sockets = block_sockets_v0106
    V0101.load_book_v0101, V0101.BOOK_V0101, BASE.load_book = load_book_v0106, BOOK_V0105, load_book_v0106
    V0104.load_book_v0104 = PRIOR.load_book_v0105 = load_book_v0106
    V0104.run_v0104 = V0101.run_v0101 = V0104.V0102.run_v0102 = BASE.run = PRIOR.run_v0105 = run_v0106


def _restore_v0105() -> None:
    BASE._install_block_sockets = _BLOCK_V0100
    PRIOR.load_book_v0105 = _LOAD_V0105
    PRIOR.run_v0105 = _RUN_V0105
    PRIOR._install_v0105()


_install_v0106()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


_PROBE_V0106 = r'''
import importlib.util, sys
sp = importlib.util.spec_from_file_location("m106", sys.argv[1]); m = importlib.util.module_from_spec(sp); sys.modules["m106"] = m; sp.loader.exec_module(m)
m.BASE.install_mode("block")
from curl_cffi import requests as curl_requests
from curl_cffi.requests import Session
def f(s: curl_requests.Session) -> curl_requests.Session: return s
class S(curl_requests.Session): pass
out = []
for call in (lambda: curl_requests.Session(), lambda: Session(), lambda: S(), lambda: curl_requests.get("https://example.invalid"),
             lambda: __import__("socket").create_connection(("example.invalid", 80))):
    try:
        call(); out.append("OPEN")
    except OSError as e:
        out.append(str(e))
ak = "absent"
try:
    import akshare  # noqa: F401
    ak = "import-ok"
except ImportError:
    ak = "absent"
print("PROBE", out == ["VDF_FETCH_NET_BLOCKED"] * 5, m.BASE.FIX_STATS["blocked"], ak)
'''


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    shims = ("akshare", "yfinance", "curl_cffi", "curl_cffi.requests")
    keep_mods = {k: sys.modules.get(k) for k in shims}  # 前版自測在本行程放的替身(無 __spec__)不留給 ④ 的 find_spec
    _restore_v0105()                                   # 前版自測驗前版自己的封口 · 冊 v0104 · 子行程鏈
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install_v0106()
        for k, v in keep_mods.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    print(f"=== {TAG} · 薄尾自測(curl_cffi 封口屬性可取、呼叫才擋 · 冊 v0105)===")
    chk("① v0105 自測過(live urllib 改道 · 真流量計數 · output_hub 歸位 · nodata 標記)", rc0 == 0, f"rc {rc0}")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    pr = subprocess.run([sys.executable, "-c", _PROBE_V0106, str(Path(__file__).resolve())], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=600, env=env)
    line = next((x for x in pr.stdout.splitlines() if x.startswith("PROBE ")), "")
    parts = line.split()
    chk("② block 封口(子行程):curl_requests.Session 可當註記與父類別;建構 / 呼叫 / socket 全擋並計數;akshare 裝了也 import 得起來",
        len(parts) == 4 and parts[1] == "True" and int(parts[2]) >= 5 and parts[3] in ("import-ok", "absent"), line or pr.stderr.strip()[-200:])
    bk = load_book_v0106()
    prev = _LOAD_V0105(PRIOR.BOOK_V0104)
    E = {r["id"]: r for r in bk["engines"]}
    def _defs(fname):
        return {(n.name, n.lineno) for n in ast.walk(ast.parse((HERE / fname).read_text(encoding="utf-8"))) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    same = [r["id"] for r in prev["engines"] if r["id"] != "011" and r != E.get(r["id"])]
    ff = E["011"]["fetch_functions"]
    chk("③ 冊 v0105:MDL011 → v0101;擷取函式留原件真擷取點(帶 file,AST 名@行對得上;PR #446 Codex P2)· 其他 34 支與 v0104 逐欄相同",
        E["011"]["file"] == "VDF_MDL011_AkshareFetcher_v0101.py" and {f["name"] for f in ff} == {"_get", "_call", "run_selection"}
        and all((f["name"], f["line"]) in _defs(f.get("file") or E["011"]["file"]) for f in ff)
        and not same and len(bk["engines"]) == len(prev["engines"]), same[:3])
    with tempfile.TemporaryDirectory() as tmp:
        rows = [dict(E["003"], needs=[])]
        r3 = run_v0106(rows, "fixture", Path(tmp) / "d", logs=Path(tmp) / "_l", timeout=900)
        r11 = run_v0106([dict(E["011"], needs=[])], "block", Path(tmp) / "e", logs=Path(tmp) / "_l", args_key="test_args", timeout=900)
        log11 = Path(r11[0]["log"]).read_text(encoding="utf-8", errors="replace") if r11 and r11[0].get("log") else ""
    chk("④ 整合實跑(子行程從本版起):MDL003 fixture rc 0 · MDL011 block params 無註冊表 = NODATA rc 2(或缺套件 ABSENT 3)· 不再 rc 1",
        r3 and r3[0]["rc"] == 0 and r11 and r11[0]["rc"] in (2, 3) and ("v0101" in log11 or r11[0]["rc"] == 3),
        (r3[0]["rc"] if r3 else None, r11[0]["rc"] if r11 else None))
    chk("⑤ 換裝:BASE 封口 / run / 冊載入全指本版;前版自測後已裝回",
        BASE._install_block_sockets is block_sockets_v0106 and BASE.run is run_v0106 and V0101.load_book_v0101 is load_book_v0106
        and V0104.load_book_v0104 is load_book_v0106)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋(模組層 VIA_NET_TOOL_PATH + def _via_net)在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0105 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
