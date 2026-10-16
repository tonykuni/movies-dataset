#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ActivateVDF.py — VDF 獨立系統的一鍵啟動入口(固定檔名;本體 = 同夾 VDF_MDL013_ActivateVDF_v*.py 尾版)

  python "VeritasIntelligenceAnalytics/functional modules/VDF/ActivateVDF.py"            ① CPU/DRAM → ② 兩張清單 → ③ 三流程 → ④ U/I
  python ".../ActivateVDF.py" plan | resources | --selftest | run --mode fixture --no-open …(參數照本體)
本檔只負責找本體尾版並交出 main(固定入口;本體換版不必改這裡)。VDF 自己的 main,不經 VCGC / VRN、不載入他系統程式。
同意閘是操作員的手(不讀不寫);不碰 TA-Lib。
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BODY_GLOB = "VDF_MDL013_ActivateVDF_v*.py"


def body_path() -> Path | None:
    hits = [p for p in HERE.glob(BODY_GLOB) if re.search(r"_v\d{4}$", p.stem)]
    return max(hits, key=lambda p: int(p.stem.rsplit("_v", 1)[1])) if hits else None


def main(argv=None) -> int:
    p = body_path()
    if p is None:
        print(f"[FAIL] ActivateVDF:本體 {BODY_GLOB} 不在 {HERE}")
        return 1
    spec = importlib.util.spec_from_file_location(p.stem, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[p.stem] = mod
    spec.loader.exec_module(mod)
    return mod.main(list(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main())
