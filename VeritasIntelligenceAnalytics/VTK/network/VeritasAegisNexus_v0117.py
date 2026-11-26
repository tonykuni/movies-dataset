#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VeritasAegisNexus_v0117 — the anti-block ladder keeps the caller's proxy.

v0116 replaced AutoFailover.resilient_fetch. It accepts `proxy` but never passes it on:
curl_cffi, cloudscraper and requests all went direct. The unversioned body passed
proxy.to_dict() to its requests lane. Since R20a every VIA process mounts the versioned
tail, so a deployment that needs a proxy would go direct (or fail where direct is blocked).

v0117 keeps the v0116 order (curl_cffi impersonate, cloudscraper, requests, playwright)
and hands `proxies=proxy.to_dict()` to the three HTTP lanes. Playwright here cannot take
the proxy, so when a proxy is given it is not tried: no direct request behind the
caller's back. Nothing is installed, nothing is fetched at import. v0116 stays as it is.
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VeritasAegisNexus"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _prior() -> Path:
    mine = _vnum(Path(__file__))
    older = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < mine]
    if not older:
        raise ImportError(f"{STEM}: no version below v{mine:04d}")
    return max(older, key=_vnum)


PRIOR = _prior()
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)

_body = _PRIOR._body
#: The unversioned body this tail runs on (loaded once, by the prior tail). Checked, not assumed.
BODY_PATH = Path(__file__).with_name("VeritasAegisNexus.py")
if Path(getattr(_body, "__file__", "")).resolve() != BODY_PATH.resolve():
    raise ImportError(f"{STEM} body is {getattr(_body, '__file__', None)}, expected {BODY_PATH}")
VERSION = f"{_vnum(Path(__file__)):04d}"
ANTI_BLOCK_ORDER = _PRIOR.ANTI_BLOCK_ORDER


def _proxies(proxy) -> dict | None:
    if proxy is None:
        return None
    if isinstance(proxy, dict):
        return proxy or None
    to_dict = getattr(proxy, "to_dict", None)
    return to_dict() if callable(to_dict) else None


def _bypass_get(self, url: str, **kw):
    proxies = kw.get("proxies")
    session = _PRIOR._curl_session()
    if session is not None:
        try:
            got = _PRIOR._text_ok(session.get(url, **kw))
            if got:
                return got
        except Exception as exc:
            _body_log("curl_cffi", exc)
    scraper = getattr(self, "_scraper", None)
    if scraper is not None:
        try:
            got = _PRIOR._text_ok(scraper.get(url, **kw))
            if got:
                return got
        except Exception as exc:
            _body_log("cloudscraper", exc)
    requests_m = getattr(_body, "requests_m", None)
    if requests_m is not None:
        try:
            got = _PRIOR._text_ok(requests_m.get(url, timeout=kw.get("timeout", 30), verify=False,
                                                 proxies=proxies))
            if got:
                return got
        except Exception as exc:
            _body_log("requests", exc)
    return None


def _body_log(lane: str, exc: Exception) -> None:
    """A failed lane moves on to the next one; the reason is kept, not swallowed."""
    LANE_ERRORS.append(f"{lane}: {type(exc).__name__}: {str(exc)[:80]}")
    del LANE_ERRORS[:-20]


LANE_ERRORS: list = []


def _resilient_fetch(cls, url: str, proxy=None, max_retries: int = 2):
    proxies = _proxies(proxy)
    kw = {"proxies": proxies} if proxies else {}
    sleep = getattr(_body, "_via_sleep", None)
    for _ in range(max_retries):
        got = _body.CloudflareBypass().get(url, **kw)
        if not got and not proxies:
            got = cls.fetch_playwright(url)
        if got:
            return got
        if sleep:
            sleep(1.5)
    return None


_body.CloudflareBypass.get = _bypass_get
_body.AutoFailover.resilient_fetch = classmethod(_resilient_fetch)
_body.VERSION = VERSION

for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name: str):
    """Every public name of the prior version stays reachable here."""
    return getattr(_PRIOR, name)


def selftest() -> int:
    """Offline: fake lanes record what they were given. No network."""
    seen = []

    class _Resp:
        status_code = 200
        text = "ok"

    class _Requests:
        @staticmethod
        def get(url, **kw):
            seen.append(("requests", kw.get("proxies")))
            return _Resp()

    class _Proxy:
        @staticmethod
        def to_dict():
            return {"http": "http://p:1", "https": "http://p:1"}

    saved = (getattr(_body, "requests_m", None), _PRIOR._curl_session, _body.AutoFailover.fetch_playwright)
    played = []
    try:
        _body.requests_m = _Requests
        _PRIOR._curl_session = lambda: None
        _body.AutoFailover.fetch_playwright = staticmethod(lambda url: played.append(url) or None)
        bypass = _body.CloudflareBypass()
        bypass._scraper = None
        got_proxy = _body.AutoFailover.resilient_fetch("http://x.invalid/a", _Proxy(), max_retries=1)
        got_direct = _body.AutoFailover.resilient_fetch("http://x.invalid/b", None, max_retries=1)
    finally:
        _body.requests_m, _PRIOR._curl_session, _body.AutoFailover.fetch_playwright = saved
    checks = [
        ("proxy reaches the requests lane", got_proxy == "ok" and seen[:1] == [("requests", _Proxy.to_dict())]),
        ("no proxy = direct, as before", got_direct == "ok" and seen[1:2] == [("requests", None)]),
        ("playwright is not tried behind a given proxy", played == []),
        ("order unchanged", ANTI_BLOCK_ORDER[0] == "curl_cffi" and ANTI_BLOCK_ORDER[-1] == "playwright"),
        ("public API still there", callable(getattr(_body, "fetch_json", None)) and callable(getattr(_body, "fetch_text", None))),
    ]
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    ok = all(c for _n, c in checks)
    print(f"[Aegis v{VERSION}] {'PASS' if ok else 'FAIL'} {sum(c for _n, c in checks)}/{len(checks)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest())
