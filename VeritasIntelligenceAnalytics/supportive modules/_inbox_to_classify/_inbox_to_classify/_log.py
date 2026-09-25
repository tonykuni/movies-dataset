"""Customize logging

Defines custom logger class for the `logger.verbose(...)` method.

init_logging() must be called before any other modules that call logging.getLogger.
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

import logging
from typing import Any, cast

# custom log level for `--verbose` output
# between DEBUG and INFO
VERBOSE = 15


class VerboseLogger(logging.Logger):
    """Custom Logger, defining a verbose log-level

    VERBOSE is between INFO and DEBUG.
    """

    def verbose(self, msg: str, *args: Any, **kwargs: Any) -> None:
        return self.log(VERBOSE, msg, *args, **kwargs)


def getLogger(name: str) -> VerboseLogger:
    """logging.getLogger, but ensures our VerboseLogger class is returned"""
    return cast(VerboseLogger, logging.getLogger(name))


def init_logging() -> None:
    """Register our VerboseLogger and VERBOSE log level.

    Should be called before any calls to getLogger(),
    i.e. in pip._internal.__init__
    """
    logging.setLoggerClass(VerboseLogger)
    logging.addLevelName(VERBOSE, "VERBOSE")
