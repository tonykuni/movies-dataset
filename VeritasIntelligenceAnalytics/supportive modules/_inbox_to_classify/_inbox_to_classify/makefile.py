# -*- coding: utf-8 -*-
"""
backports.makefile
~~~~~~~~~~~~~~~~~~

Backports the Python 3 ``socket.makefile`` method for use with anything that
wants to create a "fake" socket object.
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
import io
from socket import SocketIO


def backport_makefile(
    self, mode="r", buffering=None, encoding=None, errors=None, newline=None
):
    """
    Backport of ``socket.makefile`` from Python 3.5.
    """
    if not set(mode) <= {"r", "w", "b"}:
        raise ValueError("invalid mode %r (only r, w, b allowed)" % (mode,))
    writing = "w" in mode
    reading = "r" in mode or not writing
    assert reading or writing
    binary = "b" in mode
    rawmode = ""
    if reading:
        rawmode += "r"
    if writing:
        rawmode += "w"
    raw = SocketIO(self, rawmode)
    self._makefile_refs += 1
    if buffering is None:
        buffering = -1
    if buffering < 0:
        buffering = io.DEFAULT_BUFFER_SIZE
    if buffering == 0:
        if not binary:
            raise ValueError("unbuffered streams must be binary")
        return raw
    if reading and writing:
        buffer = io.BufferedRWPair(raw, raw, buffering)
    elif reading:
        buffer = io.BufferedReader(raw, buffering)
    else:
        assert writing
        buffer = io.BufferedWriter(raw, buffering)
    if binary:
        return buffer
    text = io.TextIOWrapper(buffer, encoding, errors, newline)
    text.mode = mode
    return text
