from __future__ import absolute_import
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

# For backwards compatibility, provide imports that used to be here.
from .connection import is_connection_dropped
from .request import SKIP_HEADER, SKIPPABLE_HEADERS, make_headers
from .response import is_fp_closed
from .retry import Retry
from .ssl_ import (
    ALPN_PROTOCOLS,
    HAS_SNI,
    IS_PYOPENSSL,
    IS_SECURETRANSPORT,
    PROTOCOL_TLS,
    SSLContext,
    assert_fingerprint,
    resolve_cert_reqs,
    resolve_ssl_version,
    ssl_wrap_socket,
)
from .timeout import Timeout, current_time
from .url import Url, get_host, parse_url, split_first
from .wait import wait_for_read, wait_for_write

__all__ = (
    "HAS_SNI",
    "IS_PYOPENSSL",
    "IS_SECURETRANSPORT",
    "SSLContext",
    "PROTOCOL_TLS",
    "ALPN_PROTOCOLS",
    "Retry",
    "Timeout",
    "Url",
    "assert_fingerprint",
    "current_time",
    "is_connection_dropped",
    "is_fp_closed",
    "get_host",
    "parse_url",
    "make_headers",
    "resolve_cert_reqs",
    "resolve_ssl_version",
    "split_first",
    "ssl_wrap_socket",
    "wait_for_read",
    "wait_for_write",
    "SKIP_HEADER",
    "SKIPPABLE_HEADERS",
)
