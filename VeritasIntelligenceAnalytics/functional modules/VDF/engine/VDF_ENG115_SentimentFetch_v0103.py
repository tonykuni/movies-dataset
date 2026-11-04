#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG115_SentimentFetch v0103 — 薄尾:直連改經 VIA 網路工具(SUP_MDL740 NetUnified · 最高政策 L103「VDF 導入網路工具」)

操作員 2026-11-04 令「開始 VDF / VCGC CLOSE OUT」;收尾規格 §8 第 3 項「外連動詞 100% 經網路工具」。
全景 AST 稽核:擷取矩陣列的 23 支現役引擎裡,本族 v0100 的 _get(CNN Fear & Greed · AAII 頁)直接 urllib.request.urlopen。
本版只改這一件(v0100 / v0101 / v0102 一字不動):
  ① 載入 v0101(真正的實作)當模組,包住它取前版的 _prior():取回的 v0100 先把那幾個直連函數換成經網路工具的版本
     (http_json / http_bytes · 雙閘先行 · 永不代設);資料解析與回傳格式照原樣。
  ② 網路工具不在或同意閘沒開 → 照實丟出例外(呼叫端原本就把例外記成 FAIL)· 不退回直連。
  ③ 直接執行 = v0101 的 main(參數 · 輸出 · 結束碼照舊);--selftest 先跑前版 v0102 自測,再驗改道(假網路工具 · 零網路)。
VDF 自己的模組:不匯入他系統程式(網路工具 = 全樹統包工具)· 同意閘不讀不寫 · 不碰 TA-Lib · 不裝套件。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG115_SentimentFetch"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
RUNTIME_PATH = HERE / (_STEM + "_v0101.py")      # 真正的實作(v0102 只是轉接 + runpy 交給它)
PRIOR_PATH = HERE / (_STEM + "_v0102.py")        # 前版(轉接層 · 自測照跑)
_NET_OVERRIDE = None                              # 自測用假網路工具;正式執行 = None


def _load(p: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _net():
    """VIA 網路工具(統包 · 雙閘先行 · 永不代設);不在 → 照實拒絕,不退回直連。"""
    net = _NET_OVERRIDE if _NET_OVERRIDE is not None else _via_net()
    if net is None:
        raise RuntimeError("VIA 網路工具不在(supportive modules/network/via_net_unified_v*.py)· 不直連")
    return net


def _ok(res, what: str) -> dict:
    """網路工具回 OK 才往下;DENY(同意閘沒開)/ FAIL 照實丟出(呼叫端原本就把例外記成 FAIL)。"""
    res = res if isinstance(res, dict) else {"state": "FAIL", "note": "網路工具回傳不是 dict"}
    if res.get("state") != "OK":
        raise RuntimeError("%s · 網路工具 %s · %s" % (what, res.get("state"), (res.get("note") or res.get("why") or "")[:160]))
    return res


def _install(m) -> None:
    def _get(url, headers):
        r = _ok(_net().http_bytes(url, timeout=25, retries=1, headers=headers), url)
        raw = r["data"] or b""
        ctype = "application/json" if raw.lstrip()[:1] in (b"{", b"[") else "text/html"   # 網路工具不回表頭 → 看內容判型(呼叫端只看有沒有 json)
        return r.get("status", 200), ctype, raw

    m._get = _get


def FAKE_JSON(url):
    return {}


def FAKE_BYTES(url):
    return b'{"fear_and_greed": {"score": 50}}' if "cnn" in url else b"<html>ok</html>"


PROBE_NAME = "_get(CNN JSON · AAII 頁)"


def PROBE(m):
    return (m._get("https://production.dataviz.cnn.io/x", {"User-Agent": "t"}), m._get("https://www.aaii.com/x", {"User-Agent": "t"}))


def EXPECT(got):
    (s1, c1, r1), (s2, c2, r2) = got
    return s1 == 200 and "json" in c1 and r1.startswith(b"{") and "json" not in c2


RT = _load(RUNTIME_PATH, _STEM + "_rt_v0101_from_v0103")
_ORIG_PRIOR = RT._prior


def _prior_net():
    """v0101 每次取前版(v0100)時,把它的直連函數換成經網路工具的版本(只換這幾個;其他一字不動)。"""
    m = _ORIG_PRIOR()
    _install(m)
    return m


RT._prior = _prior_net
_FWD = None


def __getattr__(name):
    """薄尾轉接:先找改道後的實作(v0101),再找前版轉接層(v0102);雙底線不轉;找不到照實 AttributeError。"""
    global _FWD
    if name.startswith("__"):
        raise AttributeError(name)
    if name in vars(RT):
        return vars(RT)[name]
    if _FWD is None:
        _FWD = _load(PRIOR_PATH, _STEM + "_fwd_v0102_from_v0103")
    if name in vars(_FWD):
        return vars(_FWD)[name]
    raise AttributeError("%s:v0101 / v0102 都沒有 %s" % (TAG, name))


def main() -> int:
    return RT.main()


def selftest() -> int:
    global _NET_OVERRIDE
    import urllib.request
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s · 薄尾自測(直連改經 VIA 網路工具;零網路 · 假網路工具)===" % TAG, flush=True)
    env = dict(os.environ)
    p = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    chk("① 前版 %s 自測 rc 0(轉接 + v0101 自測照跑)" % PRIOR_PATH.stem, p.returncode == 0, "rc %s" % p.returncode)
    calls = []

    class FakeNet:
        def __init__(self, state="OK"):
            self.state = state

        def http_json(self, url, timeout=30):
            calls.append(("json", url, timeout))
            return {"state": self.state, "data": FAKE_JSON(url), "note": "fake"} if self.state == "OK" else {"state": self.state, "note": "fail-closed:閘一未開"}

        def http_bytes(self, url, timeout=30, retries=3, backoff=1.0, headers=None):
            calls.append(("bytes", url, timeout, dict(headers or {})))
            return {"state": self.state, "data": FAKE_BYTES(url), "status": 200} if self.state == "OK" else {"state": self.state, "note": "fail-closed:閘一未開"}

    real_urlopen = urllib.request.urlopen

    def no_direct(*a, **k):
        raise AssertionError("直連 urlopen 被呼叫")

    urllib.request.urlopen = no_direct
    try:
        _NET_OVERRIDE = FakeNet("OK")
        got, err = None, None
        try:
            got = PROBE(RT._prior())
        except Exception as exc:                       # noqa: BLE001 — 自測要看到任何例外
            err = "%s: %s" % (type(exc).__name__, exc)
        chk("② 改道:%s 經假網路工具拿到資料 · 直連 urlopen 0 次" % PROBE_NAME, err is None and EXPECT(got) and calls, err or got)
        _NET_OVERRIDE = FakeNet("DENY")
        try:
            PROBE(RT._prior())
            denied = False
        except RuntimeError as exc:
            denied = "DENY" in str(exc)
        chk("③ 同意閘沒開(網路工具回 DENY)→ 照實丟出 RuntimeError(含 DENY)· 不退直連", denied)
        _NET_OVERRIDE = None
        saved = globals()["_via_net"]
        globals()["_via_net"] = lambda: None
        try:
            _net()
            missing = False
        except RuntimeError as exc:
            missing = "不直連" in str(exc)
        finally:
            globals()["_via_net"] = saved
        chk("④ 網路工具不在 → 照實拒絕(不退回直連)", missing)
    finally:
        urllib.request.urlopen = real_urlopen
        _NET_OVERRIDE = None
    fwd = _load(PRIOR_PATH, _STEM + "_fwd_check_v0103")
    names = [n for n in vars(fwd) if not n.startswith("_") and callable(vars(fwd)[n])]
    miss = [n for n in names if n not in ("main", "selftest") and globals().get(n) is None and not _has(n)]
    chk("⑤ 前版公開名稱本版都取得到(TAILAPI)", not miss, miss[:6])
    src = Path(__file__).read_text(encoding="utf-8")
    head = src.split("def selftest", 1)[0]
    chk("⑥ 加速器橋 · 網路工具橋在;本檔(自測以外)沒有直連 urlopen / requests;不代設同意閘;不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and ".urlopen(" not in head and "requests." not in head
        and "CONSENT\"] =" not in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    good = all(ok)
    print("[計] %s 本版 %d/%d · 前版 %s · %s" % (TAG, sum(ok), len(ok), "PASS" if p.returncode == 0 else "FAIL", "PASS" if good else "FAIL"), flush=True)
    return 0 if good else 1


def _has(name) -> bool:
    try:
        __getattr__(name)
        return True
    except AttributeError:
        return False


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else main())
