"""Execute exactly this copy of pip, within a different environment.

This file is named as it is, to ensure that this module can't be imported via
an import statement.
"""
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

# /!\ This version compatibility check section must be Python 2 compatible. /!\

import sys

# Copied from pyproject.toml
PYTHON_REQUIRES = (3, 9)


def version_str(version):  # type: ignore
    return ".".join(str(v) for v in version)


if sys.version_info[:2] < PYTHON_REQUIRES:
    raise SystemExit(
        "This version of pip does not support python {} (requires >={}).".format(
            version_str(sys.version_info[:2]), version_str(PYTHON_REQUIRES)
        )
    )

# From here on, we can use Python 3 features, but the syntax must remain
# Python 2 compatible.

import runpy  # noqa: E402
from importlib.machinery import PathFinder  # noqa: E402
from os.path import dirname  # noqa: E402

PIP_SOURCES_ROOT = dirname(dirname(__file__))


class PipImportRedirectingFinder:
    @classmethod
    def find_spec(self, fullname, path=None, target=None):  # type: ignore
        if fullname != "pip":
            return None

        spec = PathFinder.find_spec(fullname, [PIP_SOURCES_ROOT], target)
        assert spec, (PIP_SOURCES_ROOT, fullname)
        return spec


sys.meta_path.insert(0, PipImportRedirectingFinder())

assert __name__ == "__main__", "Cannot run __pip-runner__.py as a non-main module"
runpy.run_module("pip", run_name="__main__", alter_sys=True)
