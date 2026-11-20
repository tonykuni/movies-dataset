#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL740_NetUnified v0120 — 薄尾:http_json 也先取位元組、自己解碼(不再吃 requests 猜的字集)

2026-11-20 容器實錄(VRN 開閘整輪 → ENG049 矩陣名稱亂碼「жҢҜжӣң」):VDF_MDL009 台股名單 1986 檔裡 892 檔上櫃名稱是亂碼,
另有上市主動式 ETF(00400A 等)名稱亂碼被當不合格剔除。根因:v0115 http_json → AegisNexus.fetch_json → fetch_text → resp.text;
回應沒帶 charset 時 requests 用字集偵測猜成 ptcp154 / cp1256(西里爾 / 阿拉伯),UTF-8 中文就被解成亂碼,json.loads 照樣成功,上游看不出來。
v0119 只修了 http_text;本版把同一招套到 http_json:
  雙閘先行(照舊,永不代設)→ 先拿位元組(Aegis fetch_bytes → 標準庫 http_bytes 重試道)
  → json.loads(位元組)(標準庫自己認 UTF-8 / 16 / 32 與 BOM,嚴格)→ 不行再 SUP_MDL756 smart_decode 後 json.loads
  → 回 {state · data · via · encoding}。
拿不到位元組才退回前版 http_json,並把結果裡每個字串做「單位元組字集 → UTF-8」可逆反解(只在反解後出現中日韓字、且原字串沒有時才換)。
其餘名稱全部沿前版。This file does not fetch on import.
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
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "SUP_MDL740_NetUnified"
TAG = "v0120"
# 字集偵測常見誤判(實錄:ptcp154 · cp1256);反解只在結果出現中日韓字時採用
MOJIBAKE_CODECS = ("ptcp154", "cp1251", "cp1256", "cp1252", "latin-1", "koi8_r", "cp866", "cp1253", "cp1254", "cp1255", "cp1257", "mac_roman")
_CJK = re.compile(r"[㐀-鿿豈-﫿]")


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


def unmojibake_str(s):
    """單一字串:原本沒有中日韓字、照某個單位元組字集編回位元組後是合法 UTF-8 且出現中日韓字 → 回 (正字, 字集);否則 (原字, None)。"""
    if not isinstance(s, str) or not s or _CJK.search(s) or s.isascii():
        return s, None
    for enc in MOJIBAKE_CODECS:
        try:
            fixed = s.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if _CJK.search(fixed):
            return fixed, enc
    return s, None


def unmojibake_deep(obj, hits=None):
    """JSON 結構逐字串反解;hits 記 {字集: 次數}。"""
    hits = {} if hits is None else hits
    if isinstance(obj, str):
        fixed, enc = unmojibake_str(obj)
        if enc:
            hits[enc] = hits.get(enc, 0) + 1
        return fixed
    if isinstance(obj, list):
        return [unmojibake_deep(x, hits) for x in obj]
    if isinstance(obj, dict):
        return {unmojibake_deep(k, hits): unmojibake_deep(v, hits) for k, v in obj.items()}
    return obj


def _json_from_bytes(raw: bytes):
    """回 (data, encoding);解不出回 (None, 原因)。"""
    try:
        return json.loads(raw), "json-bytes(utf-8/16/32)"
    except (ValueError, UnicodeDecodeError):
        pass
    sd = getattr(_PRIOR, "smart_decode", None)
    if callable(sd):
        try:
            dec = sd(bytes(raw))
            if not dec.get("lossy"):
                return json.loads(dec["text"]), dec.get("encoding")
        except Exception:  # noqa: BLE001
            pass
    return None, "not-json"


def http_json(url: str, timeout: int = 30) -> dict:
    """車道①:JSON 端點 — 先位元組再自己解碼;雙閘先行(永不代設)。"""
    d = _PRIOR._deny_if_closed()
    if d:
        return d
    raw, via, status, attempts = None, None, None, None
    try:
        ax = _PRIOR._aegis()
        if ax is not None and callable(getattr(ax, "fetch_bytes", None)):
            raw = ax.fetch_bytes(url, timeout=timeout)
            via = "AegisNexus"
    except Exception:  # noqa: BLE001
        raw = None
    if not raw:
        r = _PRIOR.http_bytes(url, timeout=timeout)
        if r.get("state") == "OK" and r.get("data"):
            raw, via, status, attempts = r["data"], r.get("via", "stdlib"), r.get("status"), r.get("attempts")
    if raw:
        data, enc = _json_from_bytes(bytes(raw))
        if data is not None:
            out = {"state": "OK", "data": data, "via": f"{via}+bytes", "encoding": enc}
            if status is not None:
                out["status"] = status
            if attempts is not None:
                out["attempts"] = attempts
            return out
    p = _PRIOR.http_json(url, timeout=timeout)
    if p.get("state") == "OK" and p.get("data") is not None:
        hits = {}
        p["data"] = unmojibake_deep(p["data"], hits)
        p["decode_fix"] = hits or "clean"
    return p


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

    print("=== %s %s · 薄尾自測(http_json 先位元組再自己解碼;零網路,全替身)===" % (STEM, TAG))
    rows = [{"SecuritiesCompanyCode": "6143", "CompanyName": "振曜"}, {"公司代號": "1240", "公司簡稱": "茂生農經"}, {"Code": "00400A", "Name": "主動國泰動能高息"}]
    body_utf8 = json.dumps(rows, ensure_ascii=False).encode("utf-8")
    keep = {k: getattr(_PRIOR, k) for k in ("_deny_if_closed", "_aegis", "http_bytes", "http_json")}
    calls = []
    try:
        _PRIOR._deny_if_closed = lambda: None
        _PRIOR._aegis = lambda: types.SimpleNamespace(fetch_bytes=lambda url, timeout=30, headers=None: (calls.append("aegis") or body_utf8))
        _PRIOR.http_bytes = lambda url, timeout=30, **kw: (calls.append("stdlib") or {"state": "FAIL", "note": "not used"})
        r1 = http_json("http://example.invalid/tpex.json")
        chk("① 沒帶字集的 UTF-8 JSON(實錄 6143 振曜 · 1240 茂生農經 · 00400A)→ 正字 · via AegisNexus+bytes · 不走標準庫",
            r1.get("state") == "OK" and r1.get("data") == rows and r1.get("via") == "AegisNexus+bytes" and calls == ["aegis"], r1)
        big5 = json.dumps(rows, ensure_ascii=False).encode("cp950")
        _PRIOR._aegis = lambda: None
        _PRIOR.http_bytes = lambda url, timeout=30, **kw: {"state": "OK", "data": big5, "via": "stdlib", "status": 200, "attempts": 1}
        r2 = http_json("http://example.invalid/big5.json")
        chk("② 核心缺席 → 標準庫位元組 · Big5 JSON 經 smart_decode → 正字 · status / attempts 帶回",
            r2.get("data") == rows and r2.get("status") == 200 and r2.get("attempts") == 1 and "cp950" in str(r2.get("encoding")), r2)
        garbled = [{k: v.encode("utf-8").decode(enc) for k, v in r.items()} for r, enc in zip(rows, ("ptcp154", "ptcp154", "cp1256"))]
        _PRIOR.http_bytes = lambda url, timeout=30, **kw: {"state": "FAIL", "note": "down"}
        _PRIOR.http_json = lambda url, timeout=30: {"state": "OK", "data": garbled, "via": "AegisNexus"}
        r3 = http_json("http://example.invalid/fallback")
        chk("③ 拿不到位元組 → 退回前版 http_json · 逐字串反解(ptcp154 · cp1256 → 正字)· 代號與英數不動",
            r3.get("data") == rows and set(r3.get("decode_fix") or {}) == {"ptcp154", "cp1256"}, r3)
        chk("④ 反解不亂改:正常中文 · 純英數 · 西文重音字(é)原樣", unmojibake_str("台積電")[1] is None and unmojibake_str("ABC 123")[1] is None and unmojibake_str("Société")[1] is None)
        _PRIOR._deny_if_closed = keep["_deny_if_closed"]
        env_keep = {k: os.environ.pop(k, None) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
        try:
            calls.clear()
            _PRIOR._aegis = lambda: types.SimpleNamespace(fetch_bytes=lambda url, timeout=30, headers=None: (calls.append("aegis") or body_utf8))
            r5 = http_json("http://example.invalid/gated")
        finally:
            for k, v in env_keep.items():
                if v is not None:
                    os.environ[k] = v
        chk("⑤ 雙閘沒開 → 照前版拒(state ≠ OK)· 零抓取(替身沒被叫)", r5.get("state") != "OK" and not calls, r5)
        chk("⑥ 名稱沿前版:http_text · http_bytes · probe · gate_state · smart_decode · demojibake 都在",
            all(callable(globals().get(n)) for n in ("http_text", "http_bytes", "probe", "gate_state", "smart_decode", "demojibake")))
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑦ 橋在 · 本檔不抓網(無 urllib / requests 匯入)· 不代設同意閘 · 不用 replace / ignore 解碼 · 不碰 TA-Lib",
            "[VIA:ACCEL-BRIDGE:v0100]" in body and all(x not in body for x in ("import " + "urllib", "import " + "requests", "import " + "talib", 'environ["VIA_NET_' + 'CONSENT"] = "'))
            and ', "rep' + 'lace")' not in body and 'errors="ign' + 'ore"' not in body)
    finally:
        for k, v in keep.items():
            setattr(_PRIOR, k, v)
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else _PRIOR.selftest()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR.stem, prc == 0)
    print("[計] %s %s 自測 %d/%d · %s" % (STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
