#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0111 — 薄尾:live 改道收 requests 的 (連線, 讀取) 兩段 timeout(akshare 1.20 預設 (10, 60))

操作員 2026-11-21 令:「三個都是獨立系統 授權給你做到 VDF 輸出資料且快」。
容器實跑(啟動器 MDL022 v0106 → 擷取群 MDL012 → 擷取系統尾版 v0110 → 011d deep-macro,RUN_20261121_022400):
中國宏觀 31 條序列(macro_china_insurance_income · macro_china_mobile_number · macro_china_new_house_price …)每次都
FAIL「TypeError: int() argument must be … not 'tuple'」;11-19 那輪同因 97 / 100 失敗。
根因:akshare 1.20 的 akshare.utils.http 對每個請求 setdefault timeout = config.timeout = (10, 60);
v0100 live 改道 via_tool 直接 int(k.get("timeout")) → tuple 進 int() 當場丟例外,序列根本沒出網。
(v0107 收 curl_cffi 時已把 tuple 取最大值,requests 這條漏了。)容器裸跑同一支(不經改道)正常回資料 = 改道層的錯,不是來源。
本版只改一件事:live 改道裝好後,在 requests Session.request 最外層把 tuple / list timeout 正規成「最大的那個秒數」
(同 v0107 的判法;None 段略過;全是 None = 拿掉讓下層用預設 30)。其餘(冊 · 子行程 · curl_cffi · 計數 · 同意閘)全照 v0110。
子行程照 v0110 的作法改指本檔(run 期間 v0107 的 __file__ = 本檔)→ 子行程也裝本版改道。
不碰 TA-Lib;不讀寫同意閘;零網路(自測用假網路工具,子行程探針)。
用法同前;自測 --selftest(本版)· --selftest --deep(+ 前版鏈)。
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


import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0111(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0111(p) < _vnum_v0111(__file__)), key=_vnum_v0111)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0107, V0105, V0101, BASE = PRIOR.V0107, PRIOR.V0105, PRIOR.V0101, PRIOR.BASE
_LIVE_V0107 = V0107.install_live_routes_v0107
_RUN_V0110 = PRIOR.run_v0110


def __getattr__(name):
    return getattr(PRIOR, name)


def norm_timeout_v0111(t):
    """(10, 60) → 60.0 · [5, None] → 5.0 · (None, None) → None · 數字照回。"""
    if isinstance(t, (tuple, list)):
        vals = [float(x) for x in t if x is not None]
        return max(vals) if vals else None
    return t


def install_live_routes_v0111(nt) -> None:
    """v0107 live 改道(requests · urllib · curl_cffi · yfinance / akshare 過閘)+ requests 最外層收兩段 timeout。"""
    _LIVE_V0107(nt)
    import requests
    inner = requests.sessions.Session.request
    if getattr(inner, "_via_timeout_v0111", False):
        return

    def req(self, method, url, *a, **k):
        if "timeout" in k:
            t = norm_timeout_v0111(k["timeout"])
            if t is None:
                k.pop("timeout")
            else:
                k["timeout"] = t
        return inner(self, method, url, *a, **k)
    req._via_timeout_v0111 = True
    requests.sessions.Session.request = req


def run_v0111(*args, **kwargs):
    """同 v0110 run;呼叫期間 v0107 的 __file__ 指向本檔 → 子行程 = 本版(裝本版改道)。結束還原。"""
    keep = V0107.__dict__.get("__file__")
    V0107.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        return PRIOR.PRIOR._RUN_V0107(*args, **kwargs)
    finally:
        V0107.__dict__["__file__"] = keep


def _install_v0111() -> None:
    BASE._install_live_routes = install_live_routes_v0111
    V0105.PRIOR.run_v0104 = V0101.run_v0101 = V0105.PRIOR.V0102.run_v0102 = BASE.run = run_v0111
    V0105.run_v0105 = V0107.PRIOR.run_v0106 = V0107.run_v0107 = PRIOR.PRIOR.run_v0109 = PRIOR.run_v0110 = run_v0111


def _restore_v0110() -> None:
    PRIOR.run_v0110 = _RUN_V0110
    BASE._install_live_routes = _LIVE_V0107
    PRIOR._install_v0110()                             # run 換回 v0110(子行程 = v0110)


_install_v0111()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest(deep=False)
    if args == ["--selftest", "--deep"]:
        return selftest(deep=True)
    return PRIOR.PRIOR.PRIOR.main(args)                # v0108 main(換裝已是本版)


_PROBE_V0111 = r'''
import importlib.util, sys, json
sp = importlib.util.spec_from_file_location("m111", sys.argv[1]); m = importlib.util.module_from_spec(sp); sys.modules["m111"] = m; sp.loader.exec_module(m)
seen = []
class NT:
    def gate_state(self): return {"open": True}
    def http_bytes(self, url, timeout=30, headers=None):
        seen.append(("GET", timeout)); return {"state": "OK", "data": {"result": {"data": [{"v": 1}]}}}
    def post_json(self, url, payload=None, headers=None, timeout=30):
        seen.append(("POST", timeout)); return {"state": "OK", "data": {"echo": payload}}
mode = sys.argv[2]
(m.BASE._install_live_routes if mode == "tail" else m.PRIOR.V0107.install_live_routes_v0107)(NT())
import requests
out = {"seen": [], "err": None}
try:
    s = requests.Session()
    r1 = s.get("https://dc.invalid/api", params={"a": 1}, timeout=(10, 60))
    r2 = s.post("https://dc.invalid/p", json={"q": 1}, timeout=(5, None))
    r3 = requests.get("https://dc.invalid/n", timeout=12)
    r4 = s.get("https://dc.invalid/z", timeout=(None, None))
    out["json"] = [r1.json(), r2.json()]
except Exception as e:
    out["err"] = type(e).__name__ + ": " + str(e)[:120]
out["seen"] = seen
print("PROBE " + json.dumps(out, ensure_ascii=False))
'''


def _probe_v0111(mode: str) -> dict:
    r = subprocess.run([sys.executable, "-c", _PROBE_V0111, str(Path(__file__).resolve()), mode], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    line = next((x for x in reversed(r.stdout.splitlines()) if x.startswith("PROBE ")), "")
    try:
        return json.loads(line[6:]) if line else {"err": "NO_PROBE", "tail": (r.stdout[-200:], r.stderr[-300:])}
    except ValueError:
        return {"err": "BAD_PROBE", "tail": line[:200]}


def selftest(deep: bool = False) -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = None
    if deep:
        _restore_v0110()
        try:
            rc0 = PRIOR.selftest(deep=True)
        finally:
            _install_v0111()
    print(f"=== {TAG} · 薄尾自測(live 改道收 requests 兩段 timeout)===")
    if deep:
        chk("⓪ 前版鏈 v0110(含 v0109 · v0108 · 尾版冊 · 子行程)自測過", rc0 == 0, f"rc {rc0}")
    chk("① 正規化:(10,60)→60 · [5,None]→5 · (None,None)→None · 12→12",
        norm_timeout_v0111((10, 60)) == 60.0 and norm_timeout_v0111([5, None]) == 5.0 and norm_timeout_v0111((None, None)) is None
        and norm_timeout_v0111(12) == 12)
    old = _probe_v0111("prior")
    chk("② 重現:前版改道(v0107 = v0110 現役)遇 timeout=(10,60) → TypeError int() … tuple",
        "TypeError" in str(old.get("err")) and "tuple" in str(old.get("err")), old)
    new = _probe_v0111("tail")
    seen = new.get("seen") or []
    chk("③ 本版改道:GET (10,60) → 網路工具收 60 · POST (5,None) → 5 · 數字 12 照送 · 全 None → 預設 30 · 回應照原樣解出",
        new.get("err") is None and seen == [["GET", 60], ["POST", 5], ["GET", 12], ["GET", 30]]
        and new.get("json") == [{"result": {"data": [{"v": 1}]}}, {"echo": {"q": 1}}], new)
    cmd = PRIOR._child_cmd_v0110("009")
    chk("④ 子行程檔 = 本檔(子行程也裝本版改道)", len(cmd) > 3 and Path(cmd[3]).name == Path(__file__).name, cmd[:4])
    chk("⑤ run 呼叫完 v0107 的 __file__ 還原 · 換裝全指本版(改道 · run)",
        Path(V0107.__dict__.get("__file__", "")).name == "VDF_MDL008_FetchSystem_v0107.py"
        and BASE._install_live_routes is install_live_routes_v0111 and BASE.run is run_v0111 and V0107.run_v0107 is run_v0111
        and PRIOR.run_v0110 is run_v0111 and BASE.load_book is PRIOR.load_book_v0110)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑥ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑦ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    tailnote = "" if deep else " · 前版鏈自測另跑(--selftest --deep)"
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}{tailnote}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
