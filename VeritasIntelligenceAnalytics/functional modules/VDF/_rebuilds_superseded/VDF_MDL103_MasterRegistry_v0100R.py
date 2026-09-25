#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL103_MasterRegistry.py
================================================================================
  VERITAS DATA FRAMEWORK · Master Registry
  Version    : 1.0.0R  |  Module ID : VDF-MASTER-REG

  重建R(2026-08-12「完成全部」令;工作站正本候上傳,到件即讓位)。
  全生態 33 模組(5 類:VDF Active 8 含 2 lib · VDF Legacy 11 · VRN Active 6 ·
  Supportive 4 · Control UI 4)註冊中樞 + 在庫健康檢查。輸出 → 0-0-MasterRegistry。
================================================================================
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from VDF_MDL101_OutputManager import OutputManager

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

BASE_DIR = str(Path(__file__).parent / "db")

MODULES = (
    [("VDF-MDL001-VRF", "TW Universe Verifier", "VDF Active", "VDF_MDL001_TWUniverseVerify.py"),
     ("VDF-MDL003", "Sentiment + Macro Engine", "VDF Active", "VDF_MDL003_SentimentMacroEngine.py"),
     ("VDF-MDL004", "TW Full Market Engine", "VDF Active", "VDF_ENG006_MDL004TWFullMarketEngine.py"),
     ("VDF-MDL005", "TW Stock Filter + Consensus", "VDF Active", "VDF_MDL005_TWStockFilter.py"),
     ("VDF-MDL006", "Financial Model + PE/PB Band", "VDF Active", "VDF_MDL006_FinancialModel.py"),
     ("VDF-MASTER-REG", "Master Registry", "VDF Active", "VDF_MDL103_MasterRegistry.py"),
     ("VDF-OM-CORE", "OutputManager (shared lib)", "VDF Active", "VDF_MDL101_OutputManager.py"),
     ("VDF-UPGRADER", "Format Retrofit Upgrader", "VDF Active", "VDF_ENG011_MDL102FormatUpgrader.py")]
    + [("VDF-LEG-%02d" % i, n, "VDF Legacy", "") for i, n in enumerate(
        ["D2-FRED", "D2-YF", "D2-Data", "D2-Global", "D2-Integrated",
         "E0-Bootstrap", "E1-Fetch", "E2-Normalize", "E3-Validate", "E4-Publish",
         "Master-Legacy"], 1)]
    + [("VRN-MDL%03d" % i, n, "VRN Active", "") for i, n in
       [(4, "OCR Table Fetch"), (10, "Layout Parser"), (11, "Table Restorer"),
        (12, "Text Extractor"), (13, "CrossValidator"), (14, "Report Writer")]]
    + [("SUP-%02d" % i, n, "Supportive", "") for i, n in enumerate(
        ["SSOT", "Aegis", "Celeritas", "super_engine"], 1)]
    + [("CUI-%02d" % i, n, "Control UI", "") for i, n in enumerate(
        ["Bridge", "ControlServer", "ControlCenter", "DataModule UI"], 1)]
)


class MasterRegistryEngine:
    def __init__(self):
        self.save_results = {}

    def run(self):
        if not PANDAS_AVAILABLE:
            print("❌ pandas 未裝,中止")
            return 2
        here = Path(__file__).parent
        reg = pd.DataFrame(MODULES, columns=["module_id", "name", "category", "file"])
        health = reg[reg["file"] != ""].copy()
        health["exists"] = health["file"].map(lambda f: (here / f).exists())
        health["status"] = health["exists"].map(lambda x: "OK" if x else "MISSING")
        mgr = OutputManager(base_dir=BASE_DIR, output_dir="0-0-MasterRegistry",
                            duckdb_filename="VDF_MDL103_MasterRegistry.duckdb")
        self.save_results["module_registry"] = mgr.save("module_registry", reg)
        self.save_results["module_health"] = mgr.save("module_health", health)
        n_miss = int((~health["exists"]).sum())
        print("MasterReg:%d modules · %d categories · 在庫健康 %d/%d"
              % (len(reg), reg["category"].nunique(), len(health) - n_miss, len(health)))
        return 0


if __name__ == "__main__":
    ec = MasterRegistryEngine().run()
    if "--no-pause" not in sys.argv:
        try:
            input("\n按 Enter 鍵退出...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(ec)
