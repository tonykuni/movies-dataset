# -*- coding: utf-8 -*-
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
import importlib.util
import json
import math
import sys

import numpy as np
import pandas as pd

MODULE_PATH = Path(__file__).with_name("VIA_SectorFlow_Dashboard_Builder_v0100.py")
SPEC = importlib.util.spec_from_file_location("via_dashboard_vap", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_vap_ticks_axis_contract_properties() -> None:
    rng = np.random.default_rng(7)
    for _ in range(300):
        lo = float(rng.uniform(-1e5, 1e5))
        hi = lo + float(rng.uniform(1e-3, 1e6))
        ticks, dec = MODULE.def_vap_ticks(lo, hi)
        assert len(ticks) == 5                      # 5 ticks / 4 intervals
        step = ticks[1] - ticks[0]
        for i in range(4):                          # 等間隔
            assert abs((ticks[i + 1] - ticks[i]) - step) < step * 1e-6
        mant = step / (10 ** math.floor(math.log10(step)))
        assert min(abs(mant - f) for f in MODULE.VAP_STEP_FAMILY) < 1e-6  # 合法間隔
        assert ticks[0] <= lo + 1e-9 and ticks[4] >= hi - 1e-9            # 覆蓋
        assert dec >= 0


def test_vap_spec_csv_archived() -> None:
    spec = pd.read_csv(MODULE.VAP_SPEC_CSV)
    assert len(spec) == 40
    assert set(spec["axisMode"].unique()) <= {"SINGLE", "DUAL_LOCKED", "NONE"}
    assert (spec["code"].str.fullmatch(r"VAP-CH-\d{2}")).all()


def test_vap_compliance_evidence() -> None:
    summary = json.loads((MODULE.RUN_VAP / "vap_compliance_summary.json").read_text("utf-8"))
    ledger = pd.read_csv(MODULE.RUN_VAP / "vap_compliance_ledger.csv")
    assert summary["SpecCanonicalCharts"] == 40
    assert all(summary["PropertyChecks"].values())
    assert len(ledger) == summary["LedgerRows"]
    assert (ledger["Status"].str.startswith(("COMPLIANT", "ANNOTATION", "DIRECT"))).all()


def test_dashboard_embeds_vap_block() -> None:
    html = MODULE.DEFAULT_OUT.read_text("utf-8")
    assert "vapTicks" in html
    assert "VAP 視覺鎖合規" in html
    assert '"vap":' in html
