#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VeritasAegisNexus_v0116 — anti-block order on the existing body.

The unversioned VeritasAegisNexus.py stays as it is. This file loads it and
changes only the block ladder: curl_cffi impersonate, then cloudscraper, then
requests, then playwright. A missing library is skipped. Nothing is installed
and nothing is fetched at import.
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

import importlib.util
import sys
from pathlib import Path

VERSION = "0116"
ANTI_BLOCK_ORDER = ("curl_cffi", "cloudscraper", "requests", "playwright")
_IMPERSONATE = ("chrome131", "chrome124", "chrome120")

_BODY_PATH = Path(__file__).with_name("VeritasAegisNexus.py")
if not _BODY_PATH.is_file():
    raise ImportError(f"VeritasAegisNexus.py 不在 {_BODY_PATH}")
_spec = importlib.util.spec_from_file_location("VeritasAegisNexus_body", _BODY_PATH)
_body = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _body
_spec.loader.exec_module(_body)


def _curl_session():
    cls = getattr(_body, "curl_session_cls", None)
    if not getattr(_body, "curl_cffi_m", None) or cls is None:
        return None
    for profile in _IMPERSONATE:
        try:
            return cls(impersonate=profile)
        except Exception:
            continue
    return None


def _text_ok(response) -> str | None:
    if response is None or getattr(response, "status_code", 0) != 200:
        return None
    text = getattr(response, "text", None)
    return text or None


def _bypass_get(self, url: str, **kw):
    session = _curl_session()
    if session is not None:
        try:
            got = _text_ok(session.get(url, **kw))
            if got:
                return got
        except Exception:
            pass
    scraper = getattr(self, "_scraper", None)
    if scraper is not None:
        try:
            got = _text_ok(scraper.get(url, **kw))
            if got:
                return got
        except Exception:
            pass
    requests_m = getattr(_body, "requests_m", None)
    if requests_m is not None:
        try:
            got = _text_ok(requests_m.get(url, timeout=kw.get("timeout", 30), verify=False))
            if got:
                return got
        except Exception:
            pass
    return None


def _resilient_fetch(cls, url: str, proxy=None, max_retries: int = 2):
    sleep = getattr(_body, "_via_sleep", None)
    for _ in range(max_retries):
        bypass = _body.CloudflareBypass()
        got = bypass.get(url)
        if not got:
            got = cls.fetch_playwright(url)
        if got:
            return got
        if sleep:
            sleep(1.5)
    return None


_body.CloudflareBypass.get = _bypass_get
_body.AutoFailover.resilient_fetch = classmethod(_resilient_fetch)
_body.ANTI_BLOCK_ORDER = ANTI_BLOCK_ORDER
_body.VERSION = VERSION

for _name, _value in vars(_body).items():
    if not _name.startswith("__"):
        globals()[_name] = _value


def anti_block_probe() -> dict:
    """Which of the four lanes can be imported. No network."""
    return {
        "curl_cffi": bool(getattr(_body, "curl_cffi_m", None)),
        "cloudscraper": bool(getattr(_body, "cloudscraper_m", None)),
        "requests": bool(getattr(_body, "requests_m", None)),
        "playwright": bool(getattr(_body, "playwright_s", None)),
        "order": list(ANTI_BLOCK_ORDER),
    }


def selftest() -> int:
    probe = anti_block_probe()
    ok = (
        ANTI_BLOCK_ORDER[0] == "curl_cffi"
        and ANTI_BLOCK_ORDER[-1] == "playwright"
        and callable(fetch_json)
        and callable(fetch_text)
    )
    print(f"[Aegis v{VERSION}] order {' → '.join(ANTI_BLOCK_ORDER)} · present { {k: v for k, v in probe.items() if k != 'order'} }")
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest())
