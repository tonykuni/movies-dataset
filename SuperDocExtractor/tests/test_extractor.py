"""pytest wrapper around the selftest checks.

    cd SuperDocExtractor && python -m pytest tests/ -v

The same checks also run without pytest via:
    python super_extract.py selftest
"""
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
