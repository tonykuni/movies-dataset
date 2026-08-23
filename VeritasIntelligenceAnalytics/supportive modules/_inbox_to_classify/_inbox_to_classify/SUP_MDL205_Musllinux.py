"""PEP 656 support.

This module implements logic to detect if the currently running Python is
linked against musl, and what musl version is used.
"""

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

import functools
import re
import subprocess
import sys
from typing import Iterator, NamedTuple, Sequence

from ._elffile import ELFFile


class _MuslVersion(NamedTuple):
    major: int
    minor: int


def _parse_musl_version(output: str) -> _MuslVersion | None:
    lines = [n for n in (n.strip() for n in output.splitlines()) if n]
    if len(lines) < 2 or lines[0][:4] != "musl":
        return None
    m = re.match(r"Version (\d+)\.(\d+)", lines[1])
    if not m:
        return None
    return _MuslVersion(major=int(m.group(1)), minor=int(m.group(2)))


@functools.lru_cache
def _get_musl_version(executable: str) -> _MuslVersion | None:
    """Detect currently-running musl runtime version.

    This is done by checking the specified executable's dynamic linking
    information, and invoking the loader to parse its output for a version
    string. If the loader is musl, the output would be something like::

        musl libc (x86_64)
        Version 1.2.2
        Dynamic Program Loader
    """
    try:
        with open(executable, "rb") as f:
            ld = ELFFile(f).interpreter
    except (OSError, TypeError, ValueError):
        return None
    if ld is None or "musl" not in ld:
        return None
    proc = subprocess.run([ld], stderr=subprocess.PIPE, text=True)
    return _parse_musl_version(proc.stderr)


def platform_tags(archs: Sequence[str]) -> Iterator[str]:
    """Generate musllinux tags compatible to the current platform.

    :param archs: Sequence of compatible architectures.
        The first one shall be the closest to the actual architecture and be the part of
        platform tag after the ``linux_`` prefix, e.g. ``x86_64``.
        The ``linux_`` prefix is assumed as a prerequisite for the current platform to
        be musllinux-compatible.

    :returns: An iterator of compatible musllinux tags.
    """
    sys_musl = _get_musl_version(sys.executable)
    if sys_musl is None:  # Python not dynamically linked against musl.
        return
    for arch in archs:
        for minor in range(sys_musl.minor, -1, -1):
            yield f"musllinux_{sys_musl.major}_{minor}_{arch}"


if __name__ == "__main__":  # pragma: no cover
    import sysconfig

    plat = sysconfig.get_platform()
    assert plat.startswith("linux-"), "not linux"

    print("plat:", plat)
    print("musl:", _get_musl_version(sys.executable))
    print("tags:", end=" ")
    for t in platform_tags(re.sub(r"[.-]", "_", plat.split("-", 1)[-1])):
        print(t, end="\n      ")
