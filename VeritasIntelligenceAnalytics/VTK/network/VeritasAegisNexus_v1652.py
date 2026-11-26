#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VeritasAegisNexus_v1652 — 網路新舊整合版(1.65.1 本體 + 舊線反封鎖梯與代理 + 合規只發訊號)

操作員 2026-09-28:「網路新舊整合模組化 AST 整合合一更新新版本」「只有 MOPS 為主 其他不受限
偵測 COMPLIANCE 只有訊號 限不限我決定」。

本體 = 版號小於本檔、頂層有 ENGINE_VERSION 的最新具體本體(今天是操作員送達的 1.65.1 = v1651,位元不動)。本檔只疊三件事,疊之前先用 AST
確認疊加點真的在本體裡(不在就不疊、誠實報,不猜):
  ① 舊線 v0116/v0117 的反封鎖梯:curl_cffi impersonate → cloudscraper → requests → playwright
     (CloudflareBypass.get / AutoFailover.resilient_fetch)。
  ② 舊線 v0117 的代理:給了 proxy,三條 HTTP 道都帶 proxies;playwright 走不了代理就不試,不在背後直連。
  ③ 合規只發訊號:ComplianceReactor.get_strategy 判「不宜抓」時,非 MOPS 網址照給 allowed=True,
     理由改寫成 "SIGNAL: …" 並記進 COMPLIANCE_SIGNALS;**MOPS(mops.twse / mopsov.twse)照本體原判**。
     要恢復強制 = 操作員設 VIA_COMPLIANCE_ENFORCE=YES(AI 永不代設;L07/L08 同理)。
     網路同意閘(VIA_NET_CONSENT)是另一層,照舊由載入器 SUP_MDL740 與各引擎守,本檔不碰。
不安裝、不在匯入時連網。啟用只經 VCGC:via-vcgc tools activate network VeritasAegisNexus_v1652.py --apply。
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

import ast
import importlib.util
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _vnum(path: Path) -> int:
    digits = path.stem.rsplit("_v", 1)[-1]
    return int(digits) if digits.isdigit() else -1


UNREADABLE: list = []


def _concrete_body() -> Path | None:
    """Newest VeritasAegisNexus_v* below this one that is a real body (top-level ENGINE_VERSION),
    not a thin tail. Today: the operator's 1.65.1 (v1651). Found by glob + AST, never by a pinned name."""
    mine = _vnum(Path(__file__))
    for cand in sorted(HERE.glob("VeritasAegisNexus_v*.py"), key=_vnum, reverse=True):
        if not 0 <= _vnum(cand) < mine:
            continue
        try:
            tree = ast.parse(cand.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as exc:
            UNREADABLE.append(f"{cand.name} L{exc.lineno}")   # a body that does not parse is not a candidate
            continue
        if any(isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "ENGINE_VERSION" for t in n.targets)
               for n in tree.body):
            return cand
    return None


#: The body this version runs on (the lock book names this file, not the body).
BODY_PATH = _concrete_body() or Path(__file__).with_name("ABSENT-concrete-body")
VERSION = "1652"
ENGINE_VERSION = "1.65.2"
ANTI_BLOCK_ORDER = ("curl_cffi", "cloudscraper", "requests", "playwright")
_IMPERSONATE = ("chrome131", "chrome124", "chrome120")
MOPS_HOSTS = ("mops.twse.com.tw", "mopsov.twse.com.tw", "mops.twse")   # = body policy table "match" for MOPS
OVERLAY_POINTS = (("CloudflareBypass", "get"), ("AutoFailover", "resilient_fetch"),
                  ("ComplianceReactor", "get_strategy"))


def overlay_points_present(path: Path = BODY_PATH) -> dict:
    """AST: which Class.method overlay points exist in the body. Nothing is executed."""
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    have = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    have.add((node.name, item.name))
    return {f"{c}.{m}": (c, m) in have for c, m in OVERLAY_POINTS}


if not BODY_PATH.is_file():
    raise ImportError(f"VeritasAegisNexus: no concrete body below v{VERSION} in {HERE}")
POINTS = overlay_points_present()
_spec = importlib.util.spec_from_file_location("VeritasAegisNexus_v1651_body", BODY_PATH)
_body = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _body
# The 1.65.1 body runs `from VeritasAegisNexus import *` (L186): written for a body that *is* the canonical
# module, so it was a self-import. Mounted under that name, this wrapper would be half-built at that moment
# and its names (ENGINE_VERSION 1.65.2, HERE, BODY_PATH …) would be copied into the body. While the body
# executes, the canonical name points at the body itself — the self-import it was written for.
_CANON = "VeritasAegisNexus"
_had = _CANON in sys.modules
_held = sys.modules.get(_CANON)
sys.modules[_CANON] = _body
try:
    _spec.loader.exec_module(_body)
finally:
    if _had:
        sys.modules[_CANON] = _held
    else:
        sys.modules.pop(_CANON, None)

LANE_ERRORS: list = []
COMPLIANCE_SIGNALS: list = []


def _note(bucket: list, text: str) -> None:
    bucket.append(text)
    del bucket[:-50]


def _text_ok(response):
    if response is None or getattr(response, "status_code", 0) != 200:
        return None
    return getattr(response, "text", None) or None


def _curl_session():
    cls = getattr(_body, "curl_session_cls", None)
    if not getattr(_body, "curl_cffi_m", None) or cls is None:
        return None
    for profile in _IMPERSONATE:
        try:
            return cls(impersonate=profile)
        except Exception as exc:
            _note(LANE_ERRORS, f"curl_cffi {profile}: {type(exc).__name__}")
    return None


def _proxies(proxy):
    if not proxy:
        return None
    if isinstance(proxy, dict):
        return proxy
    to_dict = getattr(proxy, "to_dict", None)
    return to_dict() if callable(to_dict) else None


def _bypass_get(self, url: str, **kw):
    """① curl_cffi impersonate → cloudscraper → requests; ② proxies travel with every lane."""
    proxies = kw.get("proxies")
    lanes = (("curl_cffi", lambda: _curl_session()), ("cloudscraper", lambda: getattr(self, "_scraper", None)))
    for lane, make in lanes:
        client = make()
        if client is None:
            continue
        try:
            got = _text_ok(client.get(url, **kw))
            if got:
                return got
        except Exception as exc:
            _note(LANE_ERRORS, f"{lane}: {type(exc).__name__}: {str(exc)[:80]}")
    requests_m = getattr(_body, "requests_m", None)
    if requests_m is not None:
        try:
            got = _text_ok(requests_m.get(url, timeout=kw.get("timeout", 30), verify=False, proxies=proxies))
            if got:
                return got
        except Exception as exc:
            _note(LANE_ERRORS, f"requests: {type(exc).__name__}: {str(exc)[:80]}")
    return None


def _resilient_fetch(cls, url: str, proxy=None, max_retries: int = 2):
    proxies = _proxies(proxy)
    kw = {"proxies": proxies} if proxies else {}
    sleep = getattr(_body, "_via_sleep", time.sleep)
    for _ in range(max_retries):
        got = _body.CloudflareBypass().get(url, **kw)
        if not got and not proxies:
            got = cls.fetch_playwright(url)
        if got:
            return got
        sleep(1.5)
    return None


def is_mops(url: str) -> bool:
    text = str(url).lower()
    return any(h in text for h in MOPS_HOSTS)


def compliance_enforced() -> bool:
    """The operator's switch. Never set by AI."""
    return os.environ.get("VIA_COMPLIANCE_ENFORCE", "").strip().upper() == "YES"


_ORIG_GET_STRATEGY = _body.ComplianceReactor.get_strategy if POINTS["ComplianceReactor.get_strategy"] else None


def _get_strategy(self, url: str):
    """③ Compliance is a signal. MOPS keeps the body's decision; VIA_COMPLIANCE_ENFORCE=YES restores blocking."""
    strat = _ORIG_GET_STRATEGY(self, url)
    if strat.allowed or is_mops(url) or compliance_enforced():
        return strat
    _note(COMPLIANCE_SIGNALS, f"{url} · {strat.reason}")
    strat.allowed = True
    strat.reason = "SIGNAL: " + str(strat.reason)
    return strat


if POINTS["CloudflareBypass.get"]:
    _body.CloudflareBypass.get = _bypass_get
if POINTS["AutoFailover.resilient_fetch"]:
    _body.AutoFailover.resilient_fetch = classmethod(_resilient_fetch)
if _ORIG_GET_STRATEGY is not None:
    _body.ComplianceReactor.get_strategy = _get_strategy
_body.ANTI_BLOCK_ORDER = ANTI_BLOCK_ORDER

for _name, _value in vars(_body).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name: str):
    return getattr(_body, name)


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
    """Offline. Fake lanes record what they receive; the reactor runs with offline robots."""
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    chk("① AST:三個疊加點都在本體裡", all(POINTS.values()), str(POINTS))
    seen, played = [], []

    class _Resp:
        status_code = 200
        text = "ok"

    class _Requests:
        @staticmethod
        def get(url, **kw):
            seen.append(kw.get("proxies"))
            return _Resp()

    class _Proxy:
        @staticmethod
        def to_dict():
            return {"http": "http://p:1", "https": "http://p:1"}

    saved = (getattr(_body, "requests_m", None), getattr(_body, "curl_cffi_m", None), _body.AutoFailover.fetch_playwright,
             getattr(_body, "cloudscraper_m", None))
    try:
        _body.requests_m, _body.curl_cffi_m, _body.cloudscraper_m = _Requests, None, None
        _body.AutoFailover.fetch_playwright = staticmethod(lambda url: played.append(url) or None)
        a = _body.AutoFailover.resilient_fetch("http://x.invalid/a", _Proxy(), max_retries=1)
        b = _body.AutoFailover.resilient_fetch("http://x.invalid/b", None, max_retries=1)
    finally:
        (_body.requests_m, _body.curl_cffi_m, _body.AutoFailover.fetch_playwright, _body.cloudscraper_m) = saved
    chk("② 代理帶到 requests 道", a == "ok" and seen[:1] == [_Proxy.to_dict()], str(seen[:1]))
    chk("② 沒給代理 = 直連(同舊)", b == "ok" and seen[1:2] == [None])
    chk("② 給了代理不試 playwright(不在背後直連)", played == [])
    keep = os.environ.pop("VIA_COMPLIANCE_ENFORCE", None)
    try:
        r = _body.ComplianceReactor(offline_mode=True)
        r._block_risk = {"HIGH", "MEDIUM", "LOW", "VERY_LOW", "CRITICAL", "UNKNOWN"}   # force the body to say "no"
        other = r.get_strategy("https://www.example.com/page")
        mops = r.get_strategy("https://mops.twse.com.tw/mops/web/t05st09")
        os.environ["VIA_COMPLIANCE_ENFORCE"] = "YES"
        forced = r.get_strategy("https://www.example.com/page")
    finally:
        os.environ.pop("VIA_COMPLIANCE_ENFORCE", None)
        if keep is not None:
            os.environ["VIA_COMPLIANCE_ENFORCE"] = keep
    chk("③ 非 MOPS:合規判不宜 → 只發訊號,照給抓", other.allowed and other.reason.startswith("SIGNAL:"), other.reason[:60])
    chk("③ MOPS:照本體原判", mops.allowed is False, mops.reason[:60])
    chk("③ 操作員設 VIA_COMPLIANCE_ENFORCE=YES → 恢復擋", forced.allowed is False, forced.reason[:60])
    chk("本體是 1.65.1 具體本體(glob + AST 找到,不寫死)", getattr(_body, "ENGINE_VERSION", "") == "1.65.1", BODY_PATH.name)
    chk("本體 API 仍在(fetch_json / fetch_text / net_status_report)",
        all(callable(getattr(_body, n, None)) for n in ("fetch_json", "fetch_text", "net_status_report")))
    ok = all(results)
    print(f"[Aegis v{VERSION} = 1.65.1 + ①②③] {'PASS' if ok else 'FAIL'} {sum(results)}/{len(results)}")
    return 0 if ok else 1


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["version"]:
        print(f"VeritasAegisNexus {ENGINE_VERSION} (body {getattr(_body, 'ENGINE_VERSION', '?')})")
        sys.exit(0)
    sys.exit(selftest())
