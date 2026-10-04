#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0107 — 薄尾:live 模式 curl_cffi 也收進鎖版網路工具(akshare 國家統計局 NBS 等走 curl_cffi)

操作員 2026-10-04「Akshare 截取中國經濟數據 各國經濟數據 航運指數 資料要往下載一截取深入一點細節點的資料」+ 前令「全部都要跨入最新網路工具」。
實測:akshare 1.19.1 的國家統計局通用接口(macro_china_nbs_nation / _region 的目錄樹 · 指標 · 資料)用 curl_cffi.requests.Session,
v0105 的 live 改道只收 requests / urllib / yfinance —— curl_cffi 這條**繞過網路工具**,計數也是 0。
本版 live:curl_cffi.requests.Session.request(模組層 get / post 也走它)→ 轉給已改道的 requests(= 鎖版網路工具 http_bytes /
post_json,帶 params · headers · json/data),回應是 requests.Response(.json() · .text · .content · .status_code 同介面);
impersonate 等 curl 專屬參數照收不用;計數 curl。block / fixture 的 curl_cffi 封口照 v0106。其餘全照 v0106。
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

import importlib.util
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0107(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0107(p) < _vnum_v0107(__file__)), key=_vnum_v0107)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0105, V0101, BASE = PRIOR.PRIOR, PRIOR.V0101, PRIOR.BASE


def __getattr__(name):
    return getattr(PRIOR, name)


_RUN_V0106 = PRIOR.run_v0106
_LIVE_V0105 = V0105.install_live_routes_v0105
_CURL_KEYS = ("params", "headers", "json", "data", "timeout", "cookies", "allow_redirects")
_TL7 = threading.local()


def install_live_routes_v0107(nt) -> None:
    """v0105 live 改道(requests · urllib · yfinance · akshare 過閘)+ curl_cffi Session.request → 改道後的 requests。"""
    _LIVE_V0105(nt)
    try:
        from curl_cffi.requests import Session as CurlSession
    except Exception:                                  # 沒裝 curl_cffi = 沒有這條路要收
        return
    import requests
    stats = BASE.FIX_STATS
    stats.setdefault("curl", 0)
    if getattr(CurlSession.request, "_via_curl_v0107", False):
        return

    def routed(self, method, url, *a, **k):
        if getattr(_TL7, "inside", False):
            raise RuntimeError("VDF_FETCH_CURL_REENTRY")    # 網路工具不會用 curl_cffi;真遇到就照實擋,不繞道
        stats["curl"] += 1
        kw = {key: k[key] for key in _CURL_KEYS if key in k and k[key] is not None}
        if isinstance(kw.get("timeout"), (tuple, list)):
            kw["timeout"] = max(float(x) for x in kw["timeout"] if x is not None)
        _TL7.inside = True
        try:
            with requests.Session() as s:              # Session.request 已是 v0100/v0105 改道(= 鎖版網路工具 · 計 requests)
                return s.request(str(method).upper(), str(url), **kw)
        finally:
            _TL7.inside = False
    routed._via_curl_v0107 = True
    CurlSession.request = routed


def run_v0107(*args, **kwargs):
    """同 v0106 run;子行程改從本版起(curl_cffi 改道在子行程裡生效),呼叫完還原。"""
    keep = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        return _RUN_V0106(*args, **kwargs)
    finally:
        PRIOR.__dict__["__file__"] = keep


def _install_v0107() -> None:
    BASE._install_live_routes = install_live_routes_v0107
    V0105.PRIOR.run_v0104 = V0101.run_v0101 = V0105.PRIOR.V0102.run_v0102 = BASE.run = run_v0107
    V0105.run_v0105 = PRIOR.run_v0106 = run_v0107


def _restore_v0106() -> None:
    BASE._install_live_routes = V0105.install_live_routes_v0105
    PRIOR.run_v0106 = _RUN_V0106
    PRIOR._install_v0106()


_install_v0107()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


_PROBE_V0107 = r'''
import importlib.util, sys, json
sp = importlib.util.spec_from_file_location("m107", sys.argv[1]); m = importlib.util.module_from_spec(sp); sys.modules["m107"] = m; sp.loader.exec_module(m)
calls = []
class NT:
    def gate_state(self): return {"open": True}
    def http_bytes(self, url, timeout=30, headers=None):
        calls.append(("GET", url, (headers or {}).get("Referer")))
        return {"state": "OK", "data": b'{"data": [{"_id": "root"}]}'}
    def post_json(self, url, payload=None, headers=None, timeout=30):
        calls.append(("POST", url, payload)); return {"state": "OK", "data": {"echo": payload}}
for k in m.BASE.FIX_STATS: m.BASE.FIX_STATS[k] = 0
m.BASE._install_live_routes(NT())
from curl_cffi import requests as cr
s = cr.Session()
r1 = s.get("https://nbs.invalid/tree", params={"pid": "", "code": 1}, headers={"Referer": "https://nbs.invalid/r"}, timeout=30, impersonate="chrome")
r2 = s.post("https://nbs.invalid/es", json={"q": 1})
r3 = cr.get("https://nbs.invalid/mod")
st = m.BASE.FIX_STATS
ok = (r1.json() == {"data": [{"_id": "root"}]} and r1.status_code == 200 and r2.json() == {"echo": {"q": 1}}
      and calls[0] == ("GET", "https://nbs.invalid/tree?pid=&code=1", "https://nbs.invalid/r") and calls[1][0] == "POST"
      and len(calls) == 3 and st["curl"] == 3 and st["requests"] == 3)
print("PROBE", ok, json.dumps(st), len(calls))
'''


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    _restore_v0106()
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install_v0107()
    print(f"=== {TAG} · 薄尾自測(live curl_cffi 改道進鎖版網路工具)===")
    chk("① v0106 自測過(curl_cffi 封口 · 冊 v0105 · 整合實跑)", rc0 == 0, f"rc {rc0}")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    pr = subprocess.run([sys.executable, "-c", _PROBE_V0107, str(Path(__file__).resolve())], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=600, env=env)
    line = next((x for x in pr.stdout.splitlines() if x.startswith("PROBE ")), "")
    chk("② live(子行程):curl_cffi Session.get / post / 模組層 get → 網路工具 http_bytes / post_json(帶 params · headers · json);"
        "回應 .json() · status_code 同介面;計數 curl 3 · requests 3(一請求一抓)",
        line.startswith("PROBE True"), line or pr.stderr.strip()[-200:])
    chk("③ 換裝:BASE live 改道 / run 全指本版", BASE._install_live_routes is install_live_routes_v0107 and BASE.run is run_v0107)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 · 網路橋(模組層 VIA_NET_TOOL_PATH + def _via_net)在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0106 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
