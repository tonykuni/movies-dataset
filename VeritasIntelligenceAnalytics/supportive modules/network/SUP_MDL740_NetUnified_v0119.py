#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL740_NetUnified v0119 — 薄尾:http_text 先取位元組、再用亂碼問題解碼器(SUP_MDL756_SmartDecode)解碼

操作員令(2026-10-12):「先把它修正為非亂碼 再回朔到擷取他的工具加上亂碼問題解碼器 解取實用一次 輸出實用一次」。
倉內實錄:v0115 http_text 的三條道都在「當文字」這一步出事 — Aegis fetch_text 用 resp.text(無 charset 的 Big5 回應被當 latin-1,
可逆亂碼)、SuperAccel.fetch 同、標準庫退路 decode("utf-8","replace")(U+FFFD,不可逆)。台股官方 CSV / MOPS 多為 Big5。
本版 http_text:雙閘先行(照舊,永不代設)→ 先拿位元組(Aegis fetch_bytes → 標準庫 http_bytes 重試道)→ SUP_MDL756 smart_decode
(BOM → 宣告 → meta → utf-8 嚴格 → cp950 / big5hkscs … 嚴格 + 可信度;永不 replace / ignore)→ 回 {state · data · via · encoding · lossy}。
拿不到位元組才退回 v0118 的 http_text,並對結果做可逆亂碼反解(demojibake)。解碼器缺席 = 照 v0118(誠實,不假裝)。
其餘名稱全部沿前版;核心仍由鎖冊指定(v0118 規則不動)。This file does not fetch on import.
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
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "SUP_MDL740_NetUnified"
TAG = "v0119"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_PRIOR = _load(PRIOR, "net_prior_for_" + Path(__file__).stem)
_CODEC = {"mod": None, "why": None}


def _codec():
    """亂碼問題解碼器(SUP_MDL756 尾版;同夾;缺 = None 並記原因)。"""
    if _CODEC["mod"] is None and _CODEC["why"] is None:
        hits = [p for p in HERE.glob("SUP_MDL756_SmartDecode_v*.py") if _vnum(p) >= 0]
        if not hits:
            _CODEC["why"] = "SUP_MDL756_SmartDecode_v*.py 不在"
        else:
            try:
                _CODEC["mod"] = _load(max(hits, key=_vnum), "smartdecode_for_" + Path(__file__).stem)
            except Exception as exc:
                _CODEC["why"] = f"解碼器載入炸 {type(exc).__name__}: {str(exc)[:80]}"
    return _CODEC["mod"]


def http_text(url: str, timeout: int = 30) -> dict:
    """車道②:文本抓取 — 先位元組再智慧解碼;雙閘先行(永不代設)。"""
    d = _PRIOR._deny_if_closed()
    if d:
        return d
    c = _codec()
    if c is None:
        r = _PRIOR.http_text(url, timeout=timeout)
        r["decode_note"] = _CODEC["why"] or "解碼器缺席 → 照前版"
        return r
    raw, via, status, attempts = None, None, None, None
    try:
        ax = _PRIOR._aegis()
        if ax is not None and callable(getattr(ax, "fetch_bytes", None)):
            raw = ax.fetch_bytes(url, timeout=timeout)
            via = "AegisNexus"
    except Exception:
        raw = None
    if not raw:
        r = _PRIOR.http_bytes(url, timeout=timeout)
        if r.get("state") == "OK" and r.get("data"):
            raw, via, status, attempts = r["data"], r.get("via", "stdlib"), r.get("status"), r.get("attempts")
    if raw:
        dec = c.smart_decode(bytes(raw))
        out = {"state": "OK", "data": dec["text"], "via": f"{via}+smartdecode", "encoding": dec["encoding"], "decode_note": dec["note"], "lossy": bool(dec["lossy"])}
        if status is not None:
            out["status"] = status
        if attempts is not None:
            out["attempts"] = attempts
        return out
    p = _PRIOR.http_text(url, timeout=timeout)
    if p.get("state") == "OK" and isinstance(p.get("data"), str):
        fixed, kind = c.demojibake(p["data"])
        p["decode_fix"] = kind
        if kind not in ("ascii", "clean", "UNRECOVERABLE"):
            p["data"] = fixed
    return p


def smart_decode(data, declared=None) -> dict:
    c = _codec()
    if c is None:
        return {"text": bytes(data).decode("latin-1") if isinstance(data, (bytes, bytearray)) else str(data), "encoding": "latin-1", "note": _CODEC["why"] or "解碼器缺席", "lossy": True}
    return c.smart_decode(data, declared=declared)


def demojibake(text):
    c = _codec()
    return c.demojibake(text) if c is not None else (text, "no-codec")


for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def selftest() -> int:
    import types
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:240]) if note else ""))

    print("=== %s %s · 薄尾自測(http_text 先位元組再智慧解碼;零網路,全替身)===" % (STEM, TAG))
    zh = "台灣積體電路製造股份有限公司"
    keep = {k: getattr(_PRIOR, k) for k in ("_deny_if_closed", "_aegis", "http_bytes", "http_text")}
    calls = []
    try:
        chk("① 解碼器 SUP_MDL756 尾版載得到", _codec() is not None, _CODEC["why"])
        _PRIOR._deny_if_closed = lambda: None
        _PRIOR._aegis = lambda: types.SimpleNamespace(fetch_bytes=lambda url, timeout=30, headers=None: (calls.append("aegis") or zh.encode("cp950")))
        _PRIOR.http_bytes = lambda url, timeout=30, **kw: (calls.append("stdlib") or {"state": "FAIL", "note": "not used"})
        r1 = http_text("http://example.invalid/big5.csv")
        chk("② Aegis fetch_bytes 的 Big5 位元組 → 正字 · via AegisNexus+smartdecode · encoding cp950 · lossy False",
            r1.get("state") == "OK" and r1.get("data") == zh and r1.get("via") == "AegisNexus+smartdecode" and r1.get("encoding") == "cp950" and r1.get("lossy") is False, r1)
        _PRIOR._aegis = lambda: None
        _PRIOR.http_bytes = lambda url, timeout=30, **kw: (calls.append("stdlib") or {"state": "OK", "data": zh.encode("utf-8"), "via": "stdlib", "status": 200, "attempts": 1})
        r2 = http_text("http://example.invalid/utf8.json")
        chk("③ 核心缺席 → 標準庫 http_bytes 重試道 → utf-8 嚴格 · status / attempts 帶回", r2.get("data") == zh and r2.get("encoding") == "utf-8" and r2.get("status") == 200 and r2.get("attempts") == 1, r2)
        _PRIOR.http_bytes = lambda url, timeout=30, **kw: {"state": "FAIL", "note": "down"}
        _PRIOR.http_text = lambda url, timeout=30: {"state": "OK", "data": zh.encode("cp950").decode("latin-1"), "via": "SuperAccel"}
        r3 = http_text("http://example.invalid/fallback")
        chk("④ 拿不到位元組 → 退回前版 http_text,可逆亂碼反解(latin1->cp950)", r3.get("data") == zh and r3.get("decode_fix") == "latin1->cp950", r3)
        _PRIOR.http_text = lambda url, timeout=30: {"state": "OK", "data": "plain ascii", "via": "SuperAccel"}
        r4 = http_text("http://example.invalid/ascii")
        chk("⑤ 前版回純 ASCII → 不動(decode_fix ascii)", r4.get("data") == "plain ascii" and r4.get("decode_fix") == "ascii", r4)
        _PRIOR._deny_if_closed = keep["_deny_if_closed"]
        env_keep = {k: os.environ.pop(k, None) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
        try:
            calls.clear()
            r5 = http_text("http://example.invalid/gated")
        finally:
            for k, v in env_keep.items():
                if v is not None:
                    os.environ[k] = v
        chk("⑥ 雙閘沒開 → 照前版拒(state ≠ OK)· 零抓取(替身沒被叫)", r5.get("state") != "OK" and not calls, r5)
        chk("⑦ 名稱沿前版:http_json · http_bytes · probe · gate_state · _aegis 都在;smart_decode / demojibake 對外",
            all(callable(globals().get(n)) for n in ("http_json", "http_bytes", "probe", "gate_state")) and callable(smart_decode) and demojibake(zh.encode("utf-8").decode("latin-1"))[0] == zh)
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑧ 橋在 · 本檔不抓網(無 urllib / requests 匯入)· 不代設同意閘 · 不用 replace / ignore 解碼 · 不碰 TA-Lib",
            "[VIA:ACCEL-BRIDGE:v0100]" in body and all(x not in body for x in ("import " + "urllib", "import " + "requests", "import " + "talib", 'environ["VIA_NET_' + 'CONSENT"] = "'))
            and ', "rep' + 'lace")' not in body and 'errors="ign' + 'ore"' not in body)
    finally:
        for k, v in keep.items():
            setattr(_PRIOR, k, v)
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else _PRIOR.selftest()
    chk("⑨ 前版鏈 %s 自測 rc 0" % PRIOR.stem, prc == 0)
    print("[計] %s %s 自測 %d/%d · %s" % (STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
