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

import logging
import os

from pip._vendor.pyproject_hooks import BuildBackendHookCaller, HookMissing

from pip._internal.utils.subprocess import runner_with_spinner_message

logger = logging.getLogger(__name__)


def build_wheel_editable(
    name: str,
    backend: BuildBackendHookCaller,
    metadata_directory: str,
    tempd: str,
) -> str | None:
    """Build one InstallRequirement using the PEP 660 build process.

    Returns path to wheel if successfully built. Otherwise, returns None.
    """
    assert metadata_directory is not None
    try:
        logger.debug("Destination directory: %s", tempd)

        runner = runner_with_spinner_message(
            f"Building editable for {name} (pyproject.toml)"
        )
        with backend.subprocess_runner(runner):
            try:
                wheel_name = backend.build_editable(
                    tempd,
                    metadata_directory=metadata_directory,
                )
            except HookMissing as e:
                logger.error(
                    "Cannot build editable %s because the build "
                    "backend does not have the %s hook",
                    name,
                    e,
                )
                return None
    except Exception:
        logger.error("Failed building editable for %s", name)
        return None
    return os.path.join(tempd, wheel_name)
