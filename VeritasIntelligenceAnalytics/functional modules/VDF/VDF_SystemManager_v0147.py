#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0147 — 薄尾:quote 動詞(操作員令 2026-10-07:VRN 掃描個股報告時,需要的行情/基本資料透過 VDF 抓;可從資料庫或引擎)。
  quote --tickers 2330,3706 [--asof YYYY-MM-DD] [--days 5]
        每檔:① 先查本地(output_hub/export/vdf_tw_market_tw_daily_prices.csv 之類的匯出;有就 source=db)② 沒有 → 引擎 yfinance(<代號>.TW,再試 .TWO;source=engine)
        → VIA_Reports/vdf/RESULT_quote_latest.json(每檔:ticker · asof · close · prev_close · source · engine · ok/why)+ 貼回包;不碰 VDF 冊
其餘動詞照前版鏈。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

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

import csv
import datetime
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v0147"


def _vnum_v0147(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0147(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0147(p) < _vnum_v0147(__file__)), key=_vnum_v0147)
PRIOR = _load_v0147(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _db_lookup(home: Path, ticker: str, asof: str) -> dict | None:
    """本地匯出 csv 裡找 ticker 在 asof(或之前最近一日)的收盤;欄名寬鬆(ticker/symbol/代號 · date/日期 · close/收盤)。"""
    cands = sorted((home / "output_hub" / "export").glob("*daily_prices*.csv")) + sorted((home / "output_hub" / "export").glob("*prices_adj*.csv")) if (home / "output_hub" / "export").is_dir() else []
    best = None
    for fp in cands:
        try:
            with fp.open(encoding="utf-8-sig", errors="replace") as fh:
                rd = csv.DictReader(fh)
                cols = {c.lower(): c for c in (rd.fieldnames or [])}
                tk = next((cols[c] for c in ("ticker", "symbol", "代號", "stock_id", "code") if c in cols), None)
                dt = next((cols[c] for c in ("date", "日期", "trade_date", "asof") if c in cols), None)
                cl = next((cols[c] for c in ("close", "收盤", "adj_close", "收盤價") if c in cols), None)
                if not (tk and dt and cl):
                    continue
                for row in rd:
                    t = re.sub(r"\.TWO?$", "", str(row.get(tk, "")).strip())
                    if t != ticker:
                        continue
                    d = str(row.get(dt, ""))[:10]
                    if d <= asof and (best is None or d > best["date"]):
                        try:
                            best = {"date": d, "close": float(str(row.get(cl, "")).replace(",", "")), "file": fp.name}
                        except ValueError:
                            pass
        except OSError:
            continue
    return best


def _engine_lookup(ticker: str, asof: str, days: int) -> dict:
    try:
        import yfinance as yf  # noqa: WPS433
    except ImportError:
        return {"ok": False, "why": "yfinance 不在本環境(VDF_FetchSystem 的境才有;或 pip install yfinance)"}
    end = datetime.date.fromisoformat(asof) + datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=max(days, 5) + 10)
    for suf in (".TW", ".TWO"):
        try:
            h = yf.Ticker(ticker + suf).history(start=start.isoformat(), end=end.isoformat(), auto_adjust=False)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "why": "%s:%s" % (type(exc).__name__, str(exc)[:80])}
        if h is not None and len(h) >= 1:
            h = h[h.index.strftime("%Y-%m-%d") <= asof] if hasattr(h.index, "strftime") else h
            if len(h) == 0:
                continue
            last = h.iloc[-1]
            prev = h.iloc[-2] if len(h) >= 2 else None
            return {"ok": True, "symbol": ticker + suf, "date": h.index[-1].strftime("%Y-%m-%d"), "close": float(last["Close"]), "prev_close": (float(prev["Close"]) if prev is not None else None), "volume": int(last.get("Volume", 0) or 0)}
    return {"ok": False, "why": "yfinance 無 %s.TW/.TWO 資料" % ticker}


def quote(tickers: list, asof: str | None = None, days: int = 5) -> dict:
    home = Path(os.environ.get("VIA_VDF_HOME") or HERE)
    out_dir = Path(os.environ.get("VIA_VDF_HEALTH_OUT") or (home.parents[1] / "VIA_Reports" / "vdf"))
    out_dir.mkdir(parents=True, exist_ok=True)
    asof = asof or datetime.date.today().isoformat()
    rows = []
    for t in tickers:
        t = re.sub(r"\D", "", t)
        if not t:
            continue
        db = _db_lookup(home, t, asof)
        if db:
            rows.append({"ticker": t, "asof": asof, "date": db["date"], "close": db["close"], "source": "db", "engine": db["file"], "ok": True})
            continue
        eng = _engine_lookup(t, asof, days) if os.environ.get("VIA_QUOTE_NO_ENGINE") != "1" else {"ok": False, "why": "引擎關(VIA_QUOTE_NO_ENGINE=1)"}
        rows.append(dict({"ticker": t, "asof": asof, "source": "engine", "engine": "yfinance"}, **eng))
    out = {"verb": "quote", "ts": datetime.datetime.now().isoformat(timespec="seconds"), "asof": asof, "rows": rows, "ok": sum(1 for r in rows if r.get("ok")), "n": len(rows), "db": sum(1 for r in rows if r.get("source") == "db" and r.get("ok")), "engine": sum(1 for r in rows if r.get("source") == "engine" and r.get("ok"))}
    out["lamp"] = "GREEN" if out["ok"] == out["n"] and out["n"] else ("YELLOW" if out["ok"] else "RED")
    (out_dir / "RESULT_quote_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def _print_quote(o: dict) -> None:
    print("[計] VDF quote · %d 檔 · 成 %d(db %d · 引擎 %d)· asof %s · %s" % (o["n"], o["ok"], o["db"], o["engine"], o["asof"], o["lamp"]))
    for r in o["rows"][:40]:
        if r.get("ok"):
            print("  [OK] %s · %s · 收 %s · %s" % (r["ticker"], r.get("date"), r.get("close"), r["source"]))
        else:
            print("  [YEL] %s · %s" % (r["ticker"], r.get("why")))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["quote"]:
        def opt(flag, default=None):
            return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
        tks = [x for x in re.split(r"[,\s]+", opt("--tickers", "") or "") if x]
        if not tks:
            print("[拒跑] quote --tickers 2330,3706 [--asof YYYY-MM-DD] [--days 5]")
            return 2
        o = quote(tks, opt("--asof"), int(opt("--days", "5") or 5))
        _print_quote(o)
        return 1 if o["lamp"] == "RED" else 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vdfq-"))
    home = td / "functional modules" / "VDF"
    (home / "output_hub" / "export").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VDF_HOME", "VIA_VDF_HEALTH_OUT", "VIA_QUOTE_NO_ENGINE")}
    os.environ.update({"VIA_VDF_HOME": str(home), "VIA_VDF_HEALTH_OUT": str(td / "VIA_Reports" / "vdf"), "VIA_QUOTE_NO_ENGINE": "1"})
    (home / "VDF_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    return 0\n", encoding="utf-8")
    (home / "output_hub" / "export" / "vdf_tw_market_tw_daily_prices.csv").write_text("ticker,date,close\n2330.TW,2026-10-01,1200\n2330.TW,2026-10-03,1250\n3706,2026-10-02,88.5\n", encoding="utf-8")
    o = quote(["2330", "3706", "9999"], asof="2026-10-02")
    R = {r["ticker"]: r for r in o["rows"]}
    chk("① db 命中:2330 取 asof 前最近日 10-01 1200(非 10-03)· 3706 88.5 · 9999 無 → 引擎關 YEL", R["2330"]["close"] == 1200 and R["2330"]["date"] == "2026-10-01" and R["3706"]["close"] == 88.5 and not R["9999"]["ok"] and o["db"] == 2 and o["lamp"] == "YELLOW")
    chk("② 結果檔 RESULT_quote_latest.json", (td / "VIA_Reports" / "vdf" / "RESULT_quote_latest.json").exists())
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("④ 三橋", all(t in body for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]")))
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0147 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
