#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG232_TWIndexOfficial v0100 — 加權指數(TAIEX)· 櫃買指數(TPEX)官方日資料 → tw_index_daily

操作員(R49 2026-10-02):「加權 櫃買資訊跟上面全抓當輸入 VDF SYSTEM MANAGER管理」「隔離資料夾有 去檢查去TA-LIB」
「可尋找舊資料可取用模塊化去TA-LIB編號加版本註冊加加速器 VDF加網路工具完成流程此用」。
VDF 輸入範圍冊(VDF_InputUniverse_SSOT)的 E-10 原本是缺口:tw_index_daily 沒有現役寫入引擎。本支補上:

  ① 解析沿用收容件(只讀、不改):references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_market.py 的 fetch_tw_index_official
     (TWSE FMTQIK · BFI82U · MI_MARGN · TWTB4U;TPEX dmsRpt · 3itrade · margin_bal · intraday_trading_stat)。
     收容件 TA-Lib 0 筆(R49 掃整個 b360 夾)。
  ② 網路:收容件自帶的 _Http 換成本支的 _NetHttp —— 一律走統包網路工具 SUP_MDL740 尾版 curl_bytes
     (雙閘 VIA_NET_CONSENT + VIA_SCRAPE_CONSENT 在工具裡;閘沒開 = DENY、零外呼、零寫入;AI 永不代設同意閘)。
  ③ 欄位照 VDF 輸入範圍冊 OUT-05(= VDF_TWEquity_DailyRow_Schema_v0100.indices.columns);代號 ^TWII → TAIEX、^TWO → TPEX。
     加權的 FMTQIK 只有收盤:open / high / low 照收容件填收盤值,note 欄照實標「OHL=收盤(FMTQIK 只給收盤)」。
  ④ 入庫走正典 VIA_LibCanon.UTILS.upsert_rows(鍵 date + index_code;已在 = 不動),庫 VDF_TWIndex_Daily.duckdb。

用法(經 VCGC;VIA_FROM_VCGC=YES):
  status                                   唯讀:各指數列數 · 最早 · 最新
  run --start YYYY-MM-DD [--end YYYY-MM-DD] [--dry]
  --selftest                               沙盒:假網路工具 + 暫存庫,零外呼
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
import json
import os
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "tw_index"
DB_IDX = OUT / "VDF_TWIndex_Daily.duckdb"
TABLE = "tw_index_daily"
KEYS = ["date", "index_code"]
INTAKE = VDF / "references" / "intake" / "VIA_VDF_SSOT_b360" / "vdf_fetchers_market.py"
CODE = {"^TWII": ("TAIEX", "發行量加權股價指數"), "^TWO": ("TPEX", "櫃買指數")}
ENGINE_TAG = "VDF_ENG232_TWIndexOfficial_v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def net_tool():
    """統包網路工具尾版(SUP_MDL740_NetUnified_v*.py;curl_bytes 車道,雙閘在工具裡)。缺 = None。"""
    hits = sorted((VIA / "supportive modules" / "network").glob("SUP_MDL740_NetUnified_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("via_net_for_eng232", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["via_net_for_eng232"] = mod
    spec.loader.exec_module(mod)
    return mod


class GateDenied(RuntimeError):
    """同意閘沒開:整輪停、零寫入。"""


class _NetHttp:
    """收容件 _Http 的替身:get_json(url, params, timeout) → 統包網路工具 curl_bytes。"""
    net = None

    def __init__(self):
        if self.net is None or not hasattr(self.net, "curl_bytes"):
            raise RuntimeError("網路工具缺(要 SUP_MDL740 的 curl_bytes;不自己打網路)")
        self.calls = 0

    def get_json(self, url: str, params=None, timeout: int = 30):
        if params:
            url = f"{url}{'&' if '?' in url else '?'}{urlencode(params)}"
        rb = self.net.curl_bytes(url, timeout=timeout, follow=True,
                                 headers={"User-Agent": "Mozilla/5.0 (VIA VDF)", "Accept": "application/json,*/*"})
        self.calls += 1
        if rb.get("state") == "DENY":
            raise GateDenied("同意閘沒開(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是操作員的手)")
        if rb.get("state") != "OK":
            return {}
        try:
            return json.loads((rb.get("data") or b"").decode("utf-8", "replace") or "{}")
        except ValueError:
            return {}


def load_intake(net):
    """只讀載入收容件,把它的 _Http 換成走網路工具的 _NetHttp(不改收容件檔)。"""
    if not INTAKE.is_file():
        raise FileNotFoundError(f"收容件不在:{INTAKE}")
    spec = importlib.util.spec_from_file_location("_vdf_intake_b360_market_for_eng232", INTAKE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _NetHttp.net = net
    mod._Http = _NetHttp
    if os.environ.get("VIA_ENG232_NOSLEEP") == "1":          # 自測不等;只換收容件自己的 time 名字,不動全域 time 模組
        import types
        mod.time = types.SimpleNamespace(sleep=lambda *_a, **_k: None, time=mod.time.time)
    return mod


def _num(v):
    try:
        return None if v is None or v != v else float(v)
    except (TypeError, ValueError):
        return None


def to_rows(df) -> list:
    """收容件輸出 → OUT-05 欄位(date · index_code · index_name · OHLC · volume · turnover · 三大法人)。"""
    rows = []
    if df is None or len(df) == 0:
        return rows
    for r in df.to_dict("records"):
        code, name = CODE.get(str(r.get("Ticker")), (None, None))
        if not code or _num(r.get("Close")) is None:
            continue
        rows.append({
            "date": str(r.get("Date")), "index_code": code, "index_name": name,
            "open": _num(r.get("Open")), "low": _num(r.get("Low")), "high": _num(r.get("High")), "close": _num(r.get("Close")),
            "volume": _num(r.get("Volume")), "turnover": _num(r.get("Turnover")),
            "inst_foreign_net": _num(r.get("FI_Net")), "inst_trust_net": _num(r.get("IT_Net")), "inst_dealer_net": _num(r.get("Dealer_Net")),
            "source": "TWSE 官方" if code == "TAIEX" else "TPEX 官方",
            "note": "OHL=收盤(FMTQIK 只給收盤)" if code == "TAIEX" else "",
        })
    return rows


def count(db: Path = DB_IDX) -> dict:
    """唯讀:各指數 (列數, 最早, 最新)。庫或表不在 = {}。"""
    if not db.is_file():
        return {}
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        try:
            if TABLE not in {t for (t,) in con.execute("SHOW TABLES").fetchall()}:
                return {}
            return {c: (n, str(lo), str(hi)) for c, n, lo, hi in con.execute(
                f"SELECT index_code, COUNT(*), MIN(date), MAX(date) FROM {TABLE} GROUP BY 1 ORDER BY 1").fetchall()}
        finally:
            con.close()
    except Exception:
        return {}


def run(start: str, end: str | None = None, net=None, db: Path = DB_IDX, dry: bool = False) -> dict:
    end = end or date.today().isoformat()
    net = net if net is not None else net_tool()
    res = {"state": "FAIL", "start": start, "end": end, "fetched": 0, "added": 0, "calls": 0, "note": ""}
    if net is None or not hasattr(net, "curl_bytes"):
        res["note"] = "網路工具缺(要 SUP_MDL740 的 curl_bytes)"
        return res
    mod = load_intake(net)
    try:
        df = mod.fetch_tw_index_official(type("Spec", (), {"output_file": TABLE})(), {"start": start, "end": end, "store": None})
    except GateDenied as exc:
        res.update(state="DENY", note=str(exc))
        return res
    rows = to_rows(df)
    res["fetched"] = len(rows)
    if not rows:
        res.update(state="EMPTY", note="期間內沒有可用的官方指數列(非交易日或來源回空)")
        return res
    if dry:
        res.update(state="OK", note="--dry:不寫庫")
        return res
    db.parent.mkdir(parents=True, exist_ok=True)
    new, _total = _LIB.UTILS.upsert_rows(db, TABLE, rows, KEYS, counts=True)
    res.update(state="OK", added=int(new))
    return res


def _allowed() -> bool:
    return os.environ.get("VIA_FROM_VCGC") == "YES"


def _arg(a: list, k: str):
    return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not _allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb == "status":
        c = count()
        print(f"  [TW 指數] {DB_IDX.name} · {TABLE} · " + (" · ".join(f"{k} {n} 列 {lo} → {hi}" for k, (n, lo, hi) in c.items()) or "空"))
        return 0 if c else 2
    if verb == "run":
        start = _arg(a, "--start")
        if not start:
            print("  [TW 指數] run 要 --start YYYY-MM-DD(逐交易日打官方端點,區間別給太長)")
            return 2
        r = run(start, _arg(a, "--end"), dry="--dry" in a)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return {"OK": 0, "DENY": 4, "EMPTY": 2}.get(r["state"], 1)
    print(__doc__)
    return 2


class _FakeNet:
    def __init__(self, deny: bool = False):
        self.deny, self.urls = deny, []

    def curl_bytes(self, url, headers=None, timeout=30, follow=True):
        self.urls.append(url)
        if self.deny:
            return {"state": "DENY"}
        if "FMTQIK" in url:
            body = {"data": [["115/10/01", "5,000,000,000", "300,000,000,000", "100", "23,456.78", "12.3"]]}
        elif "dmsRpt" in url:
            body = {"aaData": [], "tables": []}
        else:
            body = {}
        return {"state": "OK", "data": json.dumps(body).encode("utf-8")}


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 自測(假網路工具 + 暫存庫,零外呼)===")
    os.environ["VIA_ENG232_NOSLEEP"] = "1"
    src = Path(__file__).read_text(encoding="utf-8")
    intake_src = INTAKE.read_text(encoding="utf-8") if INTAKE.is_file() else ""
    import re
    chk("① 收容件在且 TA-Lib 0 筆;本支也不碰 TA-Lib", bool(intake_src) and not re.search(r"talib|ta-lib|ta_lib", intake_src, re.I)
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    mod = load_intake(_FakeNet())
    chk("② 收容件的 _Http 換成走網路工具的替身(收容件檔不改)", mod._Http is _NetHttp and "class _Http" in intake_src)
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "idx.duckdb"
        net = _FakeNet()
        r = run("2026-10-01", "2026-10-01", net=net, db=db)
        c = count(db)
        chk("③ 一個交易日:TAIEX 一列入庫(收盤 23456.78;OHL=收盤照實標)", r["state"] == "OK" and r["added"] == 1
            and c.get("TAIEX", (0,))[0] == 1, (r, c))
        chk("④ 外呼全經網路工具(端點是官方 TWSE / TPEX)", net.urls and all(("twse.com.tw" in u) or ("tpex.org.tw" in u) for u in net.urls), len(net.urls))
        r2 = run("2026-10-01", "2026-10-01", net=_FakeNet(), db=db)
        chk("⑤ 重跑只增不覆寫(同鍵不動)", r2["added"] == 0 and count(db)["TAIEX"][0] == 1)
        rd = run("2026-10-01", "2026-10-01", net=_FakeNet(deny=True), db=Path(td) / "deny.duckdb")
        chk("⑥ 同意閘沒開 = DENY、零寫入", rd["state"] == "DENY" and not (Path(td) / "deny.duckdb").exists())
        rows = to_rows(None)
        chk("⑦ 空輸入 = 空列(不假填)", rows == [])
    cols = ["date", "index_code", "index_name", "open", "low", "high", "close", "volume", "turnover",
            "inst_foreign_net", "inst_trust_net", "inst_dealer_net"]
    book = sorted(VDF.glob("VDF_InputUniverse_SSOT_v*.json"))
    want = []
    if book:
        bk = json.loads(book[-1].read_text(encoding="utf-8"))
        o = [x for x in bk["outputs"] if x["id"] == "OUT-05"][0]
        sch = json.loads((VIA / o["columns_ref"]["path"]).read_text(encoding="utf-8"))
        want = sch["indices"]["columns"]
    chk("⑧ 輸出欄位 = VDF 輸入範圍冊 OUT-05(DailyRow 冊 indices.columns)", want == cols, want)
    chk("⑨ 加速器橋 · 網路橋 · 正典橋在;不代設同意閘", all(m in src for m in ("VIA:ACCEL-BRIDGE", "VIA:NET-BRIDGE", "VIA:LIB-BRIDGE"))
        and "VIA_NET_CONSENT\"] =" not in src)
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
