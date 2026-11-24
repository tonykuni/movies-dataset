#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG231_GlobalListings v0101 — 薄尾:日股 .xls 先認內容再讀 · 每市場一行白話結論(原因不再被截掉)

R17-b 工作站實跑(2026-09-28 17:10):⑦a `run` rc=1(PARTIAL:美股 OK、日股沒成)→ jp_listings 沒建 → DB 面板 HIGH;
⑦b `lists` rc=2(日股 NODATA)。v0100 的 run 只印一大段 JSON,一鍵總表只留最後三行(JSON 的收尾括號),日股為什麼沒成被截掉。

本尾版兩件事(其餘全照 v0100;L04 舊版一字不動):
  ① frame_from_xls 先認位元組再讀:
       OLE2(D0 CF 11 E0)= 真 .xls → xlrd;xlrd 不在改試 calamine(pandas 內建引擎名,要 python-calamine);兩個都不在 = ImportError → ABSENT(具名套件,不裝)
       PK(zip)          = 其實是 .xlsx → openpyxl
       < 開頭            = 回來的是網頁(擋頁 / 改址)→ FAIL 並說明,不入庫
       其他              = FAIL(檔頭前 8 位元組照印)
  ② run 印完 JSON 後,每個市場一行白話結論 + 下一步,最後一行總結(一鍵只留最後幾行也看得到原因)。

用法同 v0100(經 VCGC;VIA_FROM_VCGC=YES):status · run [--only us,jp] [--dry] · lists · --selftest
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import io
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG231_GlobalListings"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("vdf_eng231_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

ENGINE_TAG = _STEM + "_v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PRIOR.ENGINE_TAG = ENGINE_TAG
MARKET_ZH = {"us": "美股", "jp": "日股"}


def sniff(data: bytes) -> str:
    """位元組 → xls / xlsx / html / empty / unknown。"""
    if not data:
        return "empty"
    if data[:4] == b"\xd0\xcf\x11\xe0":
        return "xls"
    if data[:4] == b"PK\x03\x04":
        return "xlsx"
    if data.lstrip()[:1] == b"<":
        return "html"
    return "unknown"


def frame_from_xls(data: bytes):
    """先認內容再讀。缺讀檔套件 = ImportError(v0100 fetch_jp 照實 ABSENT);內容不是 Excel = ValueError(照實 FAIL)。"""
    import pandas as pd
    kind = sniff(data)
    if kind == "html":
        head = data.lstrip()[:120].decode("utf-8", "replace").replace("\n", " ")
        raise ValueError(f"回來的是網頁不是 Excel(擋頁或 JPX 改址):{head}")
    if kind == "empty":
        raise ValueError("回來 0 位元組")
    if kind == "unknown":
        raise ValueError(f"認不得的檔頭 {data[:8]!r}")
    if kind == "xlsx":
        return pd.read_excel(io.BytesIO(data), dtype=str, engine="openpyxl")
    miss = []
    for engine in ("xlrd", "calamine"):
        try:
            return pd.read_excel(io.BytesIO(data), dtype=str, engine=engine)
        except ImportError as e:
            miss.append(f"{engine}: {str(e).splitlines()[0][:80]}")
    raise ImportError("讀 .xls 的套件都不在(xlrd / python-calamine 擇一):" + " | ".join(miss))


PRIOR.frame_from_xls = frame_from_xls          # v0100 fetch_jp 呼叫的讀檔函式換成本尾版


def summarize(r: dict) -> list:
    """每市場一行白話 + 下一步;最後一行總結。"""
    hint = {"DENY": "同意閘沒開(你的手:-Consent 或提示時打 YES)",
            "ABSENT": "缺讀檔套件:工作站 python 環境裝 xlrd(操作員的手;AI 不裝)",
            "FAIL": "看上面原因:網址搬家 / 擋頁 / 網路;照原因處理後重跑 via-lists run --only jp",
            "EMPTY": "來源回來 0 列:看來源是否改版"}
    out = []
    for key, m in (r.get("markets") or {}).items():
        st = m.get("state", "?")
        line = f"  [{MARKET_ZH.get(key, key)}] {st} · {m.get('rows', 0):,} 列(個股 {m.get('stocks', 0):,})"
        if st == "OK":
            line += f" · 清單日 {m.get('as_of') or '—'} · 表內 {m.get('table_rows', 0):,}"
        else:
            line += f" · 原因:{(m.get('note') or '—')[:140]} → {hint.get(st, '看原因')}"
        out.append(line)
    out.append(f"  [清單] {r.get('state')} · " + " · ".join(f"{MARKET_ZH.get(k, k)} {v.get('state')}" for k, v in (r.get("markets") or {}).items())
               + (" · 乾跑不入庫" if r.get("dry") else ""))
    return out


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb != "run" or os.environ.get("VIA_FROM_VCGC") != "YES":
        return PRIOR.main(a)
    only = tuple(a[a.index("--only") + 1].split(",")) if "--only" in a and a.index("--only") + 1 < len(a) else ("us", "jp")
    r = PRIOR.run(only=only, dry="--dry" in a)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    for line in summarize(r):
        print(line)
    return {"OK": 0, "DENY": 4, "PARTIAL": 1}.get(r["state"], 2)


def selftest() -> int:
    rc = PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    print(f"=== {ENGINE_TAG} 薄尾加檢(先認內容再讀 · 白話結論)===")
    chk("⑪ 認檔頭:xls / xlsx / html / empty / unknown",
        [sniff(b"\xd0\xcf\x11\xe0xx"), sniff(b"PK\x03\x04xx"), sniff(b"  <!DOCTYPE html>"), sniff(b""), sniff(b"abc")] == ["xls", "xlsx", "html", "empty", "unknown"])
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        page = b"<!DOCTYPE html><html><body>Access Denied</body></html>"
        jh = PRIOR.run(only=("jp",), net=PRIOR._FakeNet({"data_j.xls": page}), db=td / "h.duckdb")
        m = jh["markets"]["jp"]
        chk("⑫ JPX 回網頁(擋頁 / 改址)→ FAIL 並寫明「回來的是網頁」,不入庫", m["state"] == "FAIL" and "網頁" in m["note"] and not (td / "h.duckdb").exists(), m["note"][:70])
        jo = PRIOR.run(only=("jp",), net=PRIOR._FakeNet({"data_j.xls": b"\xd0\xcf\x11\xe0 not really xls"}), db=td / "o.duckdb")
        mo = jo["markets"]["jp"]
        try:
            import xlrd  # noqa: F401
            has_xls = True
        except ImportError:
            try:
                import python_calamine  # noqa: F401
                has_xls = True
            except ImportError:
                has_xls = False
        want = "FAIL" if has_xls else "ABSENT"
        chk("⑬ 真 .xls 檔頭:讀檔套件在 → 壞檔 FAIL;都不在 → ABSENT 具名 xlrd / python-calamine", mo["state"] == want and (has_xls or "xlrd" in mo["note"]),
            f"{mo['state']} · {mo['note'][:70]}")
        import pandas as pd
        buf = io.BytesIO()
        pd.DataFrame({"日付": ["20260831", "20260831"], "コード": ["7203", "1306"], "銘柄名": ["トヨタ自動車", "TOPIX連動型ETF"],
                      "市場・商品区分": ["プライム（内国株式）", "ETF・ETN"], "33業種区分": ["輸送用機器", "-"]}).to_excel(buf, index=False, engine="openpyxl")
        jx = PRIOR.run(only=("jp",), net=PRIOR._FakeNet({"data_j.xls": buf.getvalue()}), db=td / "x.duckdb")
        mx = jx["markets"]["jp"]
        chk("⑭ 網址還是 .xls 但內容其實是 .xlsx → openpyxl 讀、只收内国株式入庫", mx["state"] == "OK" and mx["rows"] == 1 and mx["table_rows"] == 1 and mx["as_of"] == "2026-08-31",
            json.dumps(mx, ensure_ascii=False)[:90])
        lines = summarize({"state": "PARTIAL", "markets": {"us": {"state": "OK", "rows": 4, "stocks": 2, "as_of": "2026-09-28", "table_rows": 4}, "jp": m}})
        chk("⑮ 白話結論:每市場一行 + 總結;沒成的那行帶原因與下一步", len(lines) == 3 and "原因" in lines[1] and "網頁" in lines[1] and lines[-1].startswith("  [清單] PARTIAL"),
            lines[1][:80])
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["run"]) == 2
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("⑯ 不經 VCGC 就拒跑(run 也一樣)", denied)
    ok = rc == 0 and all(results)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(results)}/{len(results)} · v0100 本體 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
