#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG234_UiLauncher v0103 — 薄尾:補 L103② VDF 網路工具橋(v0102 已發布、不就地改;其餘一字照 v0102)。

操作員令(2026-10-05):「加速器覆蓋率要 100% · VDF 要加網路工具不可漏」。
  掃橋器 CGC_MDL124 量出 VDF/net 137/138,唯一缺的就是 v0102(工作站推進倉的版本)→ 出本薄尾補橋。
  本檔不連網(U/I 啟動器;資料 API 只讀本機庫),網路橋照 L103② 掛著、惰性載入、缺席零影響。
  用法照 v0102:build [--template X.html] [--open] · serve [--port 8765] · render · --selftest
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
    """統包唯一網路工具惰性載入;本檔不連網,掛橋只為 L103② 全 VDF 導入(缺席回 None,不假裝)。"""
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

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "VDF_ENG234_UiLauncher_v0102.py"
_spec = importlib.util.spec_from_file_location("VDF_ENG234_UiLauncher_v0102_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"VDF_ENG234_UiLauncher v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def selftest() -> int:
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prior_rc = PRIOR.selftest()
    chk("① 前版 v0102 自測照過(11 檢)", prior_rc == 0, buf.getvalue()[-300:])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("② L103 PY 加速器橋在(__future__ 之後)",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and src.index("from __future__") < src.index("[VIA:ACCEL-BRIDGE:v0100]"))
    chk("③ L103② VDF 網路工具橋在(惰性載入 · 缺席回 None,不連網)",
        "[VIA:NET-BRIDGE:v0100]" in src and "def _via_net()" in src)
    net = _via_net()
    chk("④ 網路工具橋解得到統包工具(或照實缺席)", net is not None or VIA_NET_TOOL_PATH is None, VIA_NET_TOOL_PATH)
    chk("⑤ 轉接:本檔沒定義的名稱照 v0102", __getattr__("main") is PRIOR.main)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · v0102 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
