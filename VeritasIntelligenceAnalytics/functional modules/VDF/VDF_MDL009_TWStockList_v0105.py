#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL009_TWStockList v0105 — 薄尾(v0100–v0104 一字不動):網路入口轉接接到尾版(MDL010 等共用核心的替身注入恢復)

2026-11-21 容器實錄:VDF 啟動器 engine_launch 複驗 VDF_MDL010_ActiveETFList 自測 RED(拿掉 v0104 就 10/10)。
MDL010 把 MDL009 尾版當共用核心(CORE),自測時把 CORE._via_net 換成替身;v0103 有把前版鏈的網路入口一路轉接到 v0103 自己的 _via_net,
v0104 沒接這一段 → 鏈上的 fetch 找的是 v0103 的 _via_net,替身沒被用到 → 走真網路 → 自測紅。真實擷取兩條路都是真網路,不受影響。
本版只把 v0103 的 _via_net(鏈上最後一個轉接點)與 v0104 的 _via_net 轉接到本檔的 _via_net;其餘(V10 名稱字形 · fixnames · 讀前份反解)照 v0104。
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
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL009_TWStockList"


def _vnum_v0105(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0105(p) < _vnum_v0105(__file__)), key=_vnum_v0105)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0103 = PRIOR.PRIOR                                    # v0103(它把 v0102 的網路入口轉到自己的 _via_net)
P1 = PRIOR.P1
for _n, _v in vars(PRIOR).items():                     # 前版公開名稱全數轉接(TAILAPI)
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v

TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_ORIG_NET_V0103 = V0103._via_net
_ORIG_NET_V0104 = PRIOR._via_net


def _forward_via_net_v0105():
    """前版鏈要網路工具時,問本檔(尾版)的 _via_net —— 共用核心的呼叫者換替身只會換到尾版這一個名字。"""
    return globals()["_via_net"]()


def _wire_v0105(on: bool) -> None:
    V0103._via_net = _forward_via_net_v0105 if on else _ORIG_NET_V0103
    PRIOR._via_net = _forward_via_net_v0105 if on else _ORIG_NET_V0104


_wire_v0105(True)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    PRIOR.PRIOR.TAG = TAG
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:240]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} 薄尾自測(網路入口轉接到尾版)===", flush=True)
    calls = []

    class _FakeNet:
        @staticmethod
        def http_json(url, timeout=30):
            calls.append(url)
            return {"state": "OK", "data": [{"Code": "2330", "Name": "台積電"}]}
    keep = globals()["_via_net"]
    globals()["_via_net"] = lambda: _FakeNet()
    try:
        r = globals()["fetch_json_v0100"]("http://example.invalid/fixture")
    finally:
        globals()["_via_net"] = keep
    ck("① 換尾版的 _via_net 成替身 → 前版鏈的 fetch_json_v0100 真的用到替身(零網路)", calls == ["http://example.invalid/fixture"] and r[0] == "OK", (calls, r))
    ck("② 接線:v0103 與 v0104 的 _via_net 都轉到本檔", V0103._via_net is _forward_via_net_v0105 and PRIOR._via_net is _forward_via_net_v0105)
    m10 = sorted((p for p in HERE.glob("VDF_MDL010_ActiveETFList_v*.py") if _vnum_v0105(p) >= 0), key=_vnum_v0105)
    rc10 = None
    if m10:
        cp = subprocess.run([sys.executable, "-B", str(m10[-1]), "--selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=600, env=dict(__import__("os").environ, VIA_FROM_VDFSM="YES"))
        rc10 = cp.returncode
    ck("③ 共用本核心的 VDF_MDL010_ActiveETFList 尾版自測照過(另起行程;2026-11-21 實錄:v0104 下 RED)", rc10 == 0, f"rc {rc10}")
    src = Path(__file__).read_text(encoding="utf-8")
    ck("④ 加速器橋 + 網路橋真的匯入 · 不碰 TA-Lib · 不設同意閘 · 不含本機路徑",
       "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "[VIA:NET-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
       and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and ("C:" + "\\Users") not in src)
    _wire_v0105(False)
    try:
        rc = PRIOR.main(["--selftest"])
    finally:
        _wire_v0105(True)
    ck(f"⑤ 前版 {PRIOR_PATH.stem} 自測照過(跑前拆本版接線)", rc == 0, f"rc {rc}")
    print(f"[計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
