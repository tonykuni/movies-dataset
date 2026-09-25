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
import platform

from pip._vendor.rich import inspect
from pip._vendor.rich.console import Console, get_windows_console_features
from pip._vendor.rich.panel import Panel
from pip._vendor.rich.pretty import Pretty


def report() -> None:  # pragma: no cover
    """Print a report to the terminal with debugging information"""
    console = Console()
    inspect(console)
    features = get_windows_console_features()
    inspect(features)

    env_names = (
        "CLICOLOR",
        "COLORTERM",
        "COLUMNS",
        "JPY_PARENT_PID",
        "JUPYTER_COLUMNS",
        "JUPYTER_LINES",
        "LINES",
        "NO_COLOR",
        "TERM_PROGRAM",
        "TERM",
        "TTY_COMPATIBLE",
        "TTY_INTERACTIVE",
        "VSCODE_VERBOSE_LOGGING",
    )
    env = {name: os.getenv(name) for name in env_names}
    console.print(Panel.fit((Pretty(env)), title="[b]Environment Variables"))

    console.print(f'platform="{platform.system()}"')


if __name__ == "__main__":  # pragma: no cover
    report()
