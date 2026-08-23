"""
This code wraps the vendored appdirs module to so the return values are
compatible for the current pip code base.

The intention is to rewrite current usages gradually, keeping the tests pass,
and eventually drop this after all usages are changed.
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

import os
import sys

from pip._vendor import platformdirs as _appdirs


def user_cache_dir(appname: str) -> str:
    return _appdirs.user_cache_dir(appname, appauthor=False)


def _macos_user_config_dir(appname: str, roaming: bool = True) -> str:
    # Use ~/Application Support/pip, if the directory exists.
    path = _appdirs.user_data_dir(appname, appauthor=False, roaming=roaming)
    if os.path.isdir(path):
        return path

    # Use a Linux-like ~/.config/pip, by default.
    linux_like_path = "~/.config/"
    if appname:
        linux_like_path = os.path.join(linux_like_path, appname)

    return os.path.expanduser(linux_like_path)


def user_config_dir(appname: str, roaming: bool = True) -> str:
    if sys.platform == "darwin":
        return _macos_user_config_dir(appname, roaming)

    return _appdirs.user_config_dir(appname, appauthor=False, roaming=roaming)


# for the discussion regarding site_config_dir locations
# see <https://github.com/pypa/pip/issues/1733>
def site_config_dirs(appname: str) -> list[str]:
    if sys.platform == "darwin":
        dirval = _appdirs.site_data_dir(appname, appauthor=False, multipath=True)
        return dirval.split(os.pathsep)

    dirval = _appdirs.site_config_dir(appname, appauthor=False, multipath=True)
    if sys.platform == "win32":
        return [dirval]

    # Unix-y system. Look in /etc as well.
    return dirval.split(os.pathsep) + ["/etc"]
