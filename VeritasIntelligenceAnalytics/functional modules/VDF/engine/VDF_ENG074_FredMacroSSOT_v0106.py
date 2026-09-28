#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG074_FredMacroSSOT tail. The newest file carries both bridges. v0104 still owns the scrape gate.

v0105→v0106(側線 2026-09-28 R16-4;VDF 系統管理 engine 燈 RED 的根因):VDF_ENG073 DataArchitecture 動態載入 ENG074 尾版讀
FETCH_ACCEL 與 ssot_path(),v0105 只轉 main / selftest → 例外被吞 → 20 擷取加速器燈變 0、⑧ FAIL、鏈跑器 RED。
本版加模組層 __getattr__,沿委派鏈走到本體(走法與 main() 相同:v0104 在 _prior() 換上 CGC_MDL224 掃描閘,不繞過);
前一版 glob 取,不另釘版號;main / selftest 行為照 v0105。
This file does not fetch during selftest.
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 前一版 = 同族裡檔名比自己小的最新一支(glob,不釘版號 L54);本體 = 前一版委派的那一支(前一版的 PRIOR)
_TAIL_PRIOR = [p for p in sorted(HERE.glob("VDF_ENG074_FredMacroSSOT_v*.py")) if p.name < Path(__file__).name][-1]
_IMPL = None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prior():
    return _load(_TAIL_PRIOR, "fred_prior_for_v0106")


#: 本體的公開面記號:沿委派鏈走到「真的有這些名稱」的那一層才停
_SURFACE = ("FETCH_ACCEL", "ssot_path")


def _impl():
    """沿委派鏈走到本體,走法與 main() 相同:薄尾有 _prior() 就用它(v0104 在這一步把掃描閘 gate_open 換成 CGC_MDL224 那把,
    不能繞過),只有 PRIOR 就載 PRIOR;走到公開面齊了就停(最多 6 層)。載一次記住。"""
    global _IMPL
    if _IMPL is None:
        m = _prior()
        for depth in range(6):
            if all(hasattr(m, n) for n in _SURFACE):
                break
            if callable(getattr(m, "_prior", None)):
                m = m._prior()
            elif getattr(m, "PRIOR", None):
                m = _load(Path(m.PRIOR), f"fred_chain{depth}_for_v0106")
            else:
                break
        _IMPL = m
    return _IMPL


def __getattr__(name: str):
    """PEP 562:v0103 本體的公開面照舊可叫(FETCH_ACCEL · ssot_path · fetch_series …;TAILAPI)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_impl(), name)


def main() -> int:
    return _impl().main()


def selftest() -> int:
    text = Path(__file__).read_text(encoding="utf-8")
    ok = "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and bool(VIA_NET_TOOL_PATH)
    mod = sys.modules.get(__name__)
    fwd = len(getattr(mod, "FETCH_ACCEL", ())) == 20 and callable(getattr(mod, "ssot_path", None))
    gate = getattr(mod, "gate_open", None)
    gated = callable(gate) and gate({}) is False and gate({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "OFF"}) is False \
        and "scrape_gate" in str(getattr(gate, "__module__", ""))
    print(f"  [{'OK' if ok else 'FAIL'}] 兩座橋在")
    print(f"  [{'OK' if fwd else 'FAIL'}] 轉接:FETCH_ACCEL(20 盞)· ssot_path 叫得到(ENG073 ⑧ 讀的就是這兩個)")
    print(f"  [{'OK' if gated else 'FAIL'}] 轉接到的本體用的是 CGC_MDL224 掃描閘(v0104 那一步沒被繞過;未開同意 = 關)")
    body = _impl().selftest() == 0
    print(f"  [{'OK' if body else 'FAIL'}] 本體自測")
    return 0 if (ok and fwd and gated and body) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
