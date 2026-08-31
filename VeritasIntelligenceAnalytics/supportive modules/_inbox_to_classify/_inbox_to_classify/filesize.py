"""Functions for reporting filesizes. Borrowed from https://github.com/PyFilesystem/pyfilesystem2

The functions declared in this module should cover the different
use cases needed to generate a string representation of a file size
using several different units. Since there are many standards regarding
file size units, three different functions have been implemented.

See Also:
    * `Wikipedia: Binary prefix <https://en.wikipedia.org/wiki/Binary_prefix>`_

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

__all__ = ["decimal"]

from typing import Iterable, List, Optional, Tuple


def _to_str(
    size: int,
    suffixes: Iterable[str],
    base: int,
    *,
    precision: Optional[int] = 1,
    separator: Optional[str] = " ",
) -> str:
    if size == 1:
        return "1 byte"
    elif size < base:
        return f"{size:,} bytes"

    for i, suffix in enumerate(suffixes, 2):  # noqa: B007
        unit = base**i
        if size < unit:
            break
    return "{:,.{precision}f}{separator}{}".format(
        (base * size / unit),
        suffix,
        precision=precision,
        separator=separator,
    )


def pick_unit_and_suffix(size: int, suffixes: List[str], base: int) -> Tuple[int, str]:
    """Pick a suffix and base for the given size."""
    for i, suffix in enumerate(suffixes):
        unit = base**i
        if size < unit * base:
            break
    return unit, suffix


def decimal(
    size: int,
    *,
    precision: Optional[int] = 1,
    separator: Optional[str] = " ",
) -> str:
    """Convert a filesize in to a string (powers of 1000, SI prefixes).

    In this convention, ``1000 B = 1 kB``.

    This is typically the format used to advertise the storage
    capacity of USB flash drives and the like (*256 MB* meaning
    actually a storage capacity of more than *256 000 000 B*),
    or used by **Mac OS X** since v10.6 to report file sizes.

    Arguments:
        int (size): A file size.
        int (precision): The number of decimal places to include (default = 1).
        str (separator): The string to separate the value from the units (default = " ").

    Returns:
        `str`: A string containing a abbreviated file size and units.

    Example:
        >>> filesize.decimal(30000)
        '30.0 kB'
        >>> filesize.decimal(30000, precision=2, separator="")
        '30.00kB'

    """
    return _to_str(
        size,
        ("kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"),
        1000,
        precision=precision,
        separator=separator,
    )
