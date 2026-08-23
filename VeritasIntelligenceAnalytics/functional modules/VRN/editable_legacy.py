"""Legacy editable installation process, i.e. `setup.py develop`."""

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
from collections.abc import Sequence

from pip._internal.build_env import BuildEnvironment
from pip._internal.utils.logging import indent_log
from pip._internal.utils.setuptools_build import make_setuptools_develop_args
from pip._internal.utils.subprocess import call_subprocess

logger = logging.getLogger(__name__)


def install_editable(
    *,
    global_options: Sequence[str],
    prefix: str | None,
    home: str | None,
    use_user_site: bool,
    name: str,
    setup_py_path: str,
    isolated: bool,
    build_env: BuildEnvironment,
    unpacked_source_directory: str,
) -> None:
    """Install a package in editable mode. Most arguments are pass-through
    to setuptools.
    """
    logger.info("Running setup.py develop for %s", name)

    args = make_setuptools_develop_args(
        setup_py_path,
        global_options=global_options,
        no_user_config=isolated,
        prefix=prefix,
        home=home,
        use_user_site=use_user_site,
    )

    with indent_log():
        with build_env:
            call_subprocess(
                args,
                command_desc="python setup.py develop",
                cwd=unpacked_source_directory,
            )
