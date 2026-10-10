#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0148 — 薄尾:extend 動詞(收尾定義 ②:VDF 以現在的資料庫多擷取一個月,測到最新資料)。
  extend [--days 35] [--tickers 2330,...] [--max 80]
     universe 來源(依序):--tickers → SSOT/VDF_Config 各族 items → VDF_TW_Focus_Universe_v*.json 裡的四碼 → VIA_Reports/vdf/RESULT_quote_latest.json 的 ticker;上限 --max
     每檔:引擎 yfinance <t>.TW(再 .TWO)抓最近 days 天 OHLCV → 併進 VDF 自己的日線庫 output_hub/export/vdf_store_daily_prices.csv(ticker,date,open,high,low,close,volume,source;去重 ticker+date,只增)
     驗收:最大日期 ≥ 最近交易日(週末/假日容忍 4 天)且成功率 ≥ 90% → GREEN;帳 registry/VDF_Extend_Ledger.jsonl;結果 VIA_Reports/vdf/RESULT_extend_latest.json
     抓完後 quote 會從 db 命中(同夾 *daily_prices*.csv)= 庫裡真的有資料
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
TAG = "v0148"


def _vnum_v0148(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0148(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0148(p) < _vnum_v0148(__file__)), key=_vnum_v0148)
PRIOR = _load_v0148(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _home():
    return Path(os.environ.get("VIA_VDF_HOME") or HERE)


def _out():
    return Path(os.environ.get("VIA_VDF_HEALTH_OUT") or (_home().parents[1] / "VIA_Reports" / "vdf"))


def _universe(explicit: list | None, cap: int) -> tuple:
    if explicit:
        return [re.sub(r"\D", "", t) for t in explicit if re.sub(r"\D", "", t)][:cap], "--tickers"
    tks = []
    cfg = _home() / "SSOT" / "VDF_Config_v0100.json"
    if cfg.exists():
        try:
            d = json.loads(cfg.read_text(encoding="utf-8-sig"))
            for g in (d.get("groups") or {}).values():
                for it in g.get("items") or []:
                    t = re.sub(r"\D", "", str(it.get("id", "")))
                    if t and t not in tks:
                        tks.append(t)
        except ValueError:
            pass
    if tks:
        return tks[:cap], "VDF_Config"
    for fp in sorted(_home().glob("VDF_TW_Focus_Universe_v*.json")):
        try:
            txt = fp.read_text(encoding="utf-8-sig")
            for t in re.findall(r"(?<!\d)([1-9]\d{3})(?!\d)", txt):
                if t not in tks:
                    tks.append(t)
        except OSError:
            pass
    if tks:
        return tks[:cap], "TW_Focus_Universe"
    q = _out() / "RESULT_quote_latest.json"
    if q.exists():
        try:
            for r in json.loads(q.read_text(encoding="utf-8-sig")).get("rows", []):
                t = str(r.get("ticker", ""))
                if re.fullmatch(r"(00\d{2}|[1-9]\d{3})", t) and t not in tks:
                    tks.append(t)
        except ValueError:
            pass
    return tks[:cap], "RESULT_quote"


def _store_path() -> Path:
    d = _home() / "output_hub" / "export"
    d.mkdir(parents=True, exist_ok=True)
    return d / "vdf_store_daily_prices.csv"


def _load_store() -> dict:
    fp = _store_path()
    rows = {}
    if fp.exists():
        with fp.open(encoding="utf-8-sig", errors="replace") as fh:
            for r in csv.DictReader(fh):
                rows[(r.get("ticker"), r.get("date"))] = r
    return rows


def _fetch_hist(ticker: str, days: int):
    try:
        import yfinance as yf  # noqa: WPS433
    except ImportError:
        return None, "yfinance 不在本環境"
    end = datetime.date.today() + datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=days)
    for suf in (".TW", ".TWO"):
        try:
            h = yf.Ticker(ticker + suf).history(start=start.isoformat(), end=end.isoformat(), auto_adjust=False)
        except Exception as exc:  # noqa: BLE001
            return None, "%s:%s" % (type(exc).__name__, str(exc)[:60])
        if h is not None and len(h):
            out = []
            for idx, row in h.iterrows():
                out.append({"ticker": ticker, "date": idx.strftime("%Y-%m-%d"), "open": round(float(row["Open"]), 4), "high": round(float(row["High"]), 4), "low": round(float(row["Low"]), 4), "close": round(float(row["Close"]), 4), "volume": int(row.get("Volume", 0) or 0), "source": "yfinance" + suf})
            return out, None
    return None, "無 .TW/.TWO 資料"


def extend(days: int = 35, tickers: list | None = None, cap: int = 80) -> dict:
    tks, src = _universe(tickers, cap)
    store = _load_store()
    before = len(store)
    per = []
    for t in tks:
        if os.environ.get("VIA_EXTEND_FAKE") == "1":      # 沙盒:不出網
            rows = [{"ticker": t, "date": (datetime.date.today() - datetime.timedelta(days=i)).isoformat(), "open": 1, "high": 1, "low": 1, "close": 1 + i, "volume": 1, "source": "fake"} for i in range(0, 5)]
            err = None
        else:
            rows, err = _fetch_hist(t, days)
        if err:
            per.append({"ticker": t, "ok": False, "why": err})
            continue
        n = 0
        for r in rows:
            k = (r["ticker"], r["date"])
            if k not in store:
                store[k] = r
                n += 1
        per.append({"ticker": t, "ok": True, "added": n, "max_date": max(r["date"] for r in rows)})
    fp = _store_path()
    if store:
        cols = ["ticker", "date", "open", "high", "low", "close", "volume", "source"]
        with fp.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for k in sorted(store):
                w.writerow(store[k])
    ok = [p for p in per if p["ok"]]
    max_date = max((p["max_date"] for p in ok), default="")
    today = datetime.date.today()
    fresh = bool(max_date) and (today - datetime.date.fromisoformat(max_date)).days <= 4
    rate = len(ok) / len(per) if per else 0
    lamp = "GREEN" if (per and fresh and rate >= 0.9) else ("RED" if not ok else "YELLOW")
    out = {"verb": "extend", "ts": datetime.datetime.now().isoformat(timespec="seconds"), "days": days, "universe_src": src, "n": len(per), "ok": len(ok), "rate": round(rate, 3), "added": len(store) - before, "store": str(fp), "store_rows": len(store), "max_date": max_date, "fresh": fresh, "per": per, "lamp": lamp}
    _out().mkdir(parents=True, exist_ok=True)
    (_out() / "RESULT_extend_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (_home() / "registry").mkdir(exist_ok=True)
    with (_home() / "registry" / "VDF_Extend_Ledger.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({k: out[k] for k in ("ts", "days", "universe_src", "n", "ok", "added", "store_rows", "max_date", "lamp")}, ensure_ascii=False) + "\n")
    return out


def _print_extend(o: dict) -> None:
    print("[計] VDF extend · 來源 %s · %d 檔 · 成 %d(%.0f%%)· 新增 %d 列 · 庫 %d 列 · 最大日期 %s%s · %s" % (o["universe_src"], o["n"], o["ok"], o["rate"] * 100, o["added"], o["store_rows"], o["max_date"] or "—", "(最新)" if o["fresh"] else "(不夠新)", o["lamp"]))
    for p in [x for x in o["per"] if not x["ok"]][:20]:
        print("  [YEL] %s · %s" % (p["ticker"], p["why"]))
    print("  [DB] %s" % o["store"])
    print("NEXT: %s" % ("VDF 多一個月到最新:過" if o["lamp"] == "GREEN" else "成功率或新鮮度不夠 → 看 [YEL] 代號;yfinance 不在就換 VDF_FetchSystem 的境跑"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["extend"]:
        def opt(flag, default=None):
            return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
        tks = [x for x in re.split(r"[,\s]+", opt("--tickers", "") or "") if x] or None
        o = extend(int(opt("--days", "35") or 35), tks, int(opt("--max", "80") or 80))
        _print_extend(o)
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

    td = Path(tempfile.mkdtemp(prefix="vdfext-"))
    home = td / "functional modules" / "VDF"
    (home / "SSOT").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VDF_HOME", "VIA_VDF_HEALTH_OUT", "VIA_EXTEND_FAKE", "VIA_QUOTE_NO_ENGINE")}
    os.environ.update({"VIA_VDF_HOME": str(home), "VIA_VDF_HEALTH_OUT": str(td / "VIA_Reports" / "vdf"), "VIA_EXTEND_FAKE": "1", "VIA_QUOTE_NO_ENGINE": "1"})
    (home / "VDF_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    return 0\n", encoding="utf-8")
    (home / "SSOT" / "VDF_Config_v0100.json").write_text(json.dumps({"groups": {"TW": {"items": [{"id": "2330"}, {"id": "2317"}]}}}), encoding="utf-8")
    o1 = extend(35)
    o2 = extend(35)
    chk("① universe 從 VDF_Config · 兩檔各 5 列進庫 · 最大日期 = 今天 → GREEN · 第二次去重新增 0", o1["universe_src"] == "VDF_Config" and o1["n"] == 2 and o1["added"] == 10 and o1["lamp"] == "GREEN" and o2["added"] == 0 and o2["store_rows"] == 10)
    q = PRIOR.quote(["2330"], asof=datetime.date.today().isoformat())
    chk("② 抓完 quote 從 db 命中(vdf_store_daily_prices.csv)", q["rows"][0].get("source") == "db" and q["rows"][0]["ok"])
    chk("③ 帳 + 結果檔", (home / "registry" / "VDF_Extend_Ledger.jsonl").exists() and (td / "VIA_Reports" / "vdf" / "RESULT_extend_latest.json").exists())
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("④ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 三橋", all(t in body for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]")))
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0148 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
