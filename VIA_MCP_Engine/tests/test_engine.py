# -*- coding: utf-8 -*-
"""pytest 入口:把引擎的離線自測掛成一個測試(不連網、不碰真實設定檔)。
   直接跑:python3 VIA_MCP_Engine_v0102.py selftest    或    python3 -m pytest VIA_MCP_Engine/tests -q
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "VeritasIntelligenceAnalytics" / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "VeritasIntelligenceAnalytics" / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("via_mcp_engine", HERE / "VIA_MCP_Engine_v0102.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["via_mcp_engine"] = mod
spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_selftest_passes():
    assert mod.selftest() == 0


def test_limit_is_five():
    assert mod.MAX_SERVERS_PER_PLATFORM == 5


def test_no_plaintext_secret_mode():
    api = mod.Api()
    code, _ = api.handle("POST", "/api/secret-mode", {}, {"mode": "plain"})
    assert code == 400


if __name__ == "__main__":
    sys.exit(mod.selftest())
