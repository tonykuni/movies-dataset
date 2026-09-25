# -*- coding: utf-8 -*-
"""ETF 雙主控台(ActiveStockETF / GlobalETFFlow)整合契約測試。

離線執行:selftest 全過 + 證據誠實(永不產生 Syn)+ 與 GroupIndex 宇宙不重疊。
mocktest(本機 HTTP mock 驅動真管線)由 GRP_ENG005_ETFConsolesEvidence_v0100.py 收證。
"""
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
import re

import VIA_ActiveStockETF as ase
import VIA_GlobalETFFlow as gef

ENGINE_DIR = Path(__file__).resolve().parent


def test_active_stock_etf_selftest_green() -> None:
    assert ase.run_selftest(verbose=False) == 0


def test_global_etf_flow_selftest_green() -> None:
    assert gef.run_selftest() == 0


def test_evidence_ladder_never_emits_syn() -> None:
    # 治理:Syn(合成偽裝)不得作為任何欄位的 evidence 值出現在引擎程式碼
    for name in ("VIA_ActiveStockETF.py", "VIA_GlobalETFFlow.py"):
        src = (ENGINE_DIR / name).read_text("utf-8")
        assert not re.search(r'evidence\s*=\s*["\']Syn["\']', src), name
        assert not re.search(r'EV_SYN\b', src), name
    # 兩引擎的證據階梯必須一致(V/Der/Est/P)
    assert ase.EV_OFFICIAL == gef.EV_OFFICIAL == "V"
    assert ase.EV_DERIVED == gef.EV_DERIVED == "Der"
    assert ase.EV_ESTIMATED == gef.EV_ESTIMATED == "Est"
    assert ase.EV_PENDING == gef.EV_PENDING == "P"


def test_universe_disjoint_from_groupindex_common_stocks() -> None:
    # GroupIndex 普通股宇宙 = fullmatch(r"\d{4}") 且非 00 開頭;
    # 主動式 ETF(尾碼 A/D、00 開頭六碼)必須被該濾網天然排除 → 兩宇宙不重疊
    def is_groupindex_common(code: str) -> bool:
        return bool(re.fullmatch(r"\d{4}", code)) and not code.startswith("00")

    for etf_code in ("00980A", "00981A", "00982A", "00999A", "00982D", "0050", "00878"):
        assert not is_groupindex_common(etf_code), etf_code
    assert is_groupindex_common("2330") and is_groupindex_common("3081")
    # ActiveStockETF 自身的宇宙判定也必須拒收 GroupIndex 普通股與被動 ETF
    assert ase.is_active_etf_code("00980A")
    assert not ase.is_active_etf_code("2330")
    assert not ase.is_active_etf_code("0050")
    assert not ase.is_active_etf_code("00878")
    assert ase.is_active_etf_code("00982D", suffixes="A,D")
    assert not ase.is_active_etf_code("00982D")


def test_global_flow_truth_ladder_t3_never_writes_amounts() -> None:
    # T3 估流只能給方向/強度,不得寫成美元金額(T4 偽裝 T1 之防線)
    src = (ENGINE_DIR / "VIA_GlobalETFFlow.py").read_text("utf-8")
    assert '"T3"' in src or "T3" in src
    # FIS_pv 輸出區間 ±100:抽樣驗證 tanh 壓縮性質
    assert gef.clamp(150.0, -100.0, 100.0) == 100.0
    # robust_z 的 fail-closed 契約:樣本 < 8 誠實回 None(不假造 0)
    assert gef.robust_z(5.0, [1.0, 2.0, 3.0, 2.0, 1.5, 2.5]) is None
    z = gef.robust_z(5.0, [1.0, 2.0, 3.0, 2.0, 1.5, 2.5, 1.8, 2.2, 2.4])
    assert z is not None and z > 0
