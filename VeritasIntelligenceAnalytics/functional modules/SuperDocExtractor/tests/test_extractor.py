"""pytest wrapper around the selftest checks.

    cd SuperDocExtractor && python -m pytest tests/ -v

The same checks also run without pytest via:
    python super_extract.py selftest
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
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from superextract.samples import build_all           # noqa: E402
from superextract import selftest as _selftest       # noqa: E402


@pytest.fixture(scope="session")
def sample_paths(tmp_path_factory):
    outdir = tmp_path_factory.mktemp("superextract_samples")
    return build_all(str(outdir))


@pytest.mark.parametrize("check", _selftest.CHECKS,
                         ids=[c.__name__.replace("check_", "") for c in _selftest.CHECKS])
def test_pipeline(check, sample_paths):
    check(sample_paths)
