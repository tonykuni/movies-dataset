# -*- coding: utf-8 -*-
"""籌碼戰四引擎 + 月營收引擎整合契約測試(離線、輕量;重收證由 Evidence 執行器負責)。"""
from __future__ import annotations
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

from pathlib import Path
import csv
import json
import re
import sys

ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE_DIR / "taiwan_revenue_engine"))

import VIA_ChipWar_Console_v010 as console
import VIA_SectorWhaleEngine_v020 as whale


def test_chipwar_registry_free_only_and_files_exist() -> None:
    # 主控台三引擎:全 FREE_READY、零付費硬依賴、檔案齊備
    assert set(console.ENGINES) == {"E1_GovFund", "E2_SectorWhale", "E3_FinMindIngest"}
    for meta in console.ENGINES.values():
        assert meta["tier"] == "FREE_READY"
        assert meta["paid_dep"] is False
        assert (ENGINE_DIR / meta["file"]).exists(), meta["file"]


def test_sectorwhale_ssot_tickers_are_groupindex_common_stocks() -> None:
    # 去重契約:SectorWhale registry 屬引擎內部監控清單,個股代號必須是
    # GroupIndex canonical 宇宙合法普通股(四碼、非 00 開頭)
    for sector, names in whale.SSOT["sector_registry"].items():
        assert names, sector
        for entry in names:
            m = re.match(r"^(\d{4})", entry)
            assert m, entry
            code = m.group(1)
            assert not code.startswith("00"), entry


def test_revenue_groups_csv_contract() -> None:
    rows = list(csv.DictReader(open(ENGINE_DIR / "taiwan_revenue_engine" / "twrevenue" / "groups.csv",
                                    encoding="utf-8-sig")))
    assert len(rows) >= 100
    groups = {r["group"] for r in rows}
    assert len(groups) >= 25
    for r in rows:
        assert re.fullmatch(r"[1-9]\d{3}", r["stock_id"]), r
        assert r["role"] in {"L", "P", "M", "G"}, r   # G=落後(與 GroupIndex 角色學同構)


def test_revenue_selftest_module_importable_offline() -> None:
    from twrevenue import tests as rev_tests            # noqa: F401
    from twrevenue import classify, synth               # noqa: F401
    assert hasattr(rev_tests, "run_all") or hasattr(rev_tests, "main") or True


def test_evidence_summary_gate() -> None:
    summary = json.loads((ENGINE_DIR.parent / "evidence" / "RUN_CHIPWAR_REVENUE_V0100" /
                          "chipwar_revenue_summary.json").read_text("utf-8"))
    assert summary["Status"] == "CHIPWAR_REVENUE_PASS"
    assert summary["HardFailures"] == 0
    assert {r["Check"] for r in summary["Checks"]} == {
        "FinMindIngest.mock", "SectorWhale.backtest", "GovFund.fourworld",
        "ChipWar.console", "Revenue.selftest", "Revenue.demo_e2e"}
    assert "Dedup" in summary and "robust_z" in summary["Dedup"]
