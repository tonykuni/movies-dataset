#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_MarketFetch v0101 — VRN-2 的市場資料擷取引擎(包住 VDF_TW_DataFetchEngine v036 · 不改它一字 · 用引擎擷取 · 不靠既有資料庫)。

動詞:
  --fetch  [--basic <VRN2_BasicInfo_latest.json>] [--tickers 2330,6488] [--out <market 夾>] [--days 400]
           代號來源:基本資料冊 TICKER(4 碼)· 或 --tickers · 或 --scope <scope_in 夾>(檔名前四碼原則)
           以 VDF 引擎 --datasets daily --start(最早報告日 - 10 天 · 至少 --days)--end 今天 --output <market>/vdf 擷取(官方 TWSE / TPEX + Yahoo 還原)
           Python 優先用 %USERPROFILE%\\envs\\via_tw_fetch\\Scripts\\python.exe(VDF 包自己的環境)· 沒有就用本行程 Python(缺 yfinance / lxml → 回報交 VCGC)
  --fill   --basic <VRN2_BasicInfo_latest.json> --out <market 夾>
           讀 <market>/vdf/parquet/tw_universe + tw_equity_daily → 每檔:NAME · YFINANCE_TICKER · BLOOMBERG_TICKER · ADJ_CLOSE(最新)· ADJ_CLOSE_BEFORE_REPORT(報告日前最後一個交易日)·
           還原因子(報告日)→ TARGET_PRICE(ADJ)= TARGET_PRICE × 因子 · UPSIDE_PCT(ADJ)= TARGET_PRICE(ADJ)/ADJ_CLOSE - 1 → <market>/VRN2_Market_latest.json
           沒有的值寫 MISSING 與理由(不猜 · 不拿 Close 冒充 Adj Close)
  --selftest  三碼規則與 VRN2 Regex 對照 · 合成 parquet 填值 · 引擎在則跑其 28 項離線回歸(--with-vdf-tests)
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0101"
HERE = Path(__file__).resolve().parent
ENGINE_NAME = "VDF_TW_DataFetchEngine_v036.py"
_BASE = re.compile(r"^([1-9]\d{3})$")
_TYPES = [("STOCK", r"^([1-9]\d{3})"), ("ETF_EQUITY_ACTIVE", r"^(00\d{2,3}A)"), ("ETF_BOND_PASSIVE", r"^(00\d{2,3}B)"), ("ETF_BOND_ACTIVE", r"^(00\d{2,3}D)"), ("ETF_LEVERAGED", r"^(00\d{2,3}L)"),
          ("ETF_INVERSE", r"^(00\d{2,3}R)"), ("ETF_FUTURES", r"^(00\d{2,3}[UV])"), ("ETF_BALANCED", r"^(00\d{2,3}T)"), ("ETF_EQUITY_PASSIVE", r"^(00\d{2,3})")]   # v0101 VRN2 Regex v0103 九類


def ticker_type(code: str) -> tuple:
    """v0101 三種形式任一 → (類型 · 本地代碼)· 不合回 ('', '')。VRN-2 範圍只擷取 STOCK;ETF 只分類。"""
    s = (code or "").strip().upper()
    s = re.sub(r"(\.TWO?|\s+TT)$", "", s)
    for t, rx in _TYPES:
        m = re.match(rx + "$", s)
        if m:
            return t, m.group(1)
    return "", ""


def engine_path() -> Path | None:
    for p in (HERE / "_vdf_fetch" / ENGINE_NAME, HERE / ENGINE_NAME, HERE.parent / "VDF" / ENGINE_NAME):
        if p.exists():
            return p
    return None


def fetch_python() -> str:
    cand = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "envs" / "via_tw_fetch" / "Scripts" / "python.exe"
    return str(cand) if cand.exists() else sys.executable


def forms(code: str, market: str) -> dict:
    code = str(code).strip()
    if not _BASE.match(code) or market not in ("TWSE", "TPEX"):
        return {}
    return {"ticker": code, "yfinance_ticker": code + (".TW" if market == "TWSE" else ".TWO"), "bloomberg_ticker": "%s TT" % code, "market": market}


def _tickers_from_basic(basic_path: Path) -> list:
    try:
        rows = json.loads(basic_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for r in rows:
        t = str(r.get("TICKER") or "").strip()
        m = _BASE.match(t) or re.match(r"^([1-9]\d{3})(?:\.TWO?|\s+TT)$", t)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def _tickers_from_scope(scope: Path) -> list:
    out = []
    for p in sorted(scope.glob("*.pdf")):
        for m in re.finditer(r"(?<!\d)([1-9]\d{3})(?!\d)", p.name):
            c = m.group(1)
            if not (c[:2] in ("19", "20") and re.search(c + r"\d{4}", p.name)) and c not in out:
                out.append(c)
                break
    return out


def _dates_from_basic(basic_path: Path) -> list:
    try:
        rows = json.loads(basic_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    ds = []
    for r in rows:
        d = str(r.get("REPORT_DATE") or "")
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            ds.append(d)
    return ds


def fetch(args: dict) -> dict:
    eng = engine_path()
    out = Path(args["out"]); vdf = out / "vdf"; vdf.mkdir(parents=True, exist_ok=True)
    if not eng:
        return {"lamp": "GRAY", "msg": "VDF 擷取引擎 %s 不在(_vdf_fetch)· 不擷取" % ENGINE_NAME}
    tickers = [t for t in (args.get("tickers") or "").split(",") if _BASE.match(t.strip())]
    if not tickers and args.get("basic"):
        tickers = _tickers_from_basic(Path(args["basic"]))
    if not tickers and args.get("scope"):
        tickers = _tickers_from_scope(Path(args["scope"]))
    if not tickers:
        return {"lamp": "GRAY", "msg": "沒有代號(基本資料冊 / scope 都沒有 4 碼)· 不擷取"}
    dates = _dates_from_basic(Path(args["basic"])) if args.get("basic") else []
    today = _dt.date.today()
    start = min([_dt.date.fromisoformat(d) for d in dates] + [today]) - _dt.timedelta(days=10) if dates else today - _dt.timedelta(days=int(args.get("days") or 400))
    start = min(start, today - _dt.timedelta(days=int(args.get("days") or 400)))
    py = fetch_python()
    probe = subprocess.run([py, "-c", "import yfinance, lxml, pandas, pyarrow, duckdb; print('ok')"], capture_output=True, text=True, timeout=120)
    if "ok" not in probe.stdout:
        return {"lamp": "YELLOW", "msg": "擷取環境缺套件(%s)· yfinance / lxml / pandas / pyarrow / duckdb → 交 VCGC 安裝或用 VDF 包的 via_tw_fetch 環境" % py, "tickers": tickers}
    cmd = [py, "-W", "ignore", str(eng), "--tickers", ",".join(tickers), "--datasets", "daily", "--start", start.isoformat(), "--end", today.isoformat(), "--output", str(vdf)]
    if args.get("offline"):
        cmd.append("--offline")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=int(args.get("timeout") or 1800), cwd=str(eng.parent))
        rc, tail = r.returncode, (r.stdout + r.stderr).strip().splitlines()[-3:]
    except subprocess.TimeoutExpired:
        rc, tail = 124, ["逾時"]
    st = {}
    try:
        st = json.loads((vdf / "status.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    daily = (st.get("datasets") or {}).get("daily") or {}
    lamp = "GREEN" if rc == 0 else ("YELLOW" if rc == 2 else "RED")
    return {"lamp": lamp, "msg": "VDF 引擎 rc %d(%s)· 代號 %d · %s~%s · 日資料 %s · 問題 %d · %s" % (rc, {0: "完整", 2: "PARTIAL(可用資料已保存)"}.get(rc, "失敗"), len(tickers), start, today, json.dumps(daily, ensure_ascii=False)[:160], len(st.get("issues") or []), " / ".join(tail)[:160]), "tickers": tickers, "rc": rc}


def _read_parquet(glob_root: Path, table: str):
    import pandas as pd
    files = sorted((glob_root / "parquet" / table).glob("ticker=*/year=*/data.parquet"))
    if not files:
        return None
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def fill(args: dict) -> dict:
    import pandas as pd
    out = Path(args["out"]); vdf = out / "vdf"
    basic = json.loads(Path(args["basic"]).read_text(encoding="utf-8"))
    uni = _read_parquet(vdf, "tw_universe")
    daily = _read_parquet(vdf, "tw_equity_daily")
    if uni is None and daily is None:
        return {"lamp": "GRAY", "msg": "VDF 落盤沒有 tw_universe / tw_equity_daily(先 --fetch)"}
    uni_map = {}
    if uni is not None:
        for _, u in uni.iterrows():
            uni_map[str(u.get("ticker"))] = {"name": u.get("name"), "market": u.get("market")}
    if daily is not None:
        daily["date"] = pd.to_datetime(daily["date"]).dt.date
    per_ticker, per_file, n_ok, n_miss = {}, {}, 0, 0
    for row in basic:
        t = str(row.get("TICKER") or "").strip()
        m = _BASE.match(t) or re.match(r"^([1-9]\d{3})(?:\.TWO?|\s+TT)$", t)
        if not m:
            per_file[row.get("FILENAME")] = {"status": "MISSING", "reason": "基本資料冊代號不是 4 碼"}; n_miss += 1
            continue
        code = m.group(1)
        d = daily[daily["ticker"].astype(str) == code].sort_values("date") if daily is not None else None
        info = dict(forms(code, (uni_map.get(code) or {}).get("market") or ((d["market"].iloc[-1]) if d is not None and len(d) and "market" in d else "")))
        info["name"] = (uni_map.get(code) or {}).get("name") or ((d["name"].iloc[-1]) if d is not None and len(d) and "name" in d else "")
        rec = {"ticker": code, "name": info.get("name") or "", "yfinance_ticker": info.get("yfinance_ticker", ""), "bloomberg_ticker": info.get("bloomberg_ticker", "")}
        if d is None or not len(d):
            rec.update(status="MISSING", reason="VDF 沒有此代號的日資料")
            per_file[row.get("FILENAME")] = rec; n_miss += 1
            continue
        adj = d[d["adj_close"].notna()] if "adj_close" in d else d.iloc[0:0]
        if len(adj):
            last = adj.iloc[-1]
            rec.update(adj_close=float(last["adj_close"]), adj_close_date=str(last["date"]), close_latest=float(last["close"]) if pd.notna(last.get("close")) else None)
        else:
            rec.update(adj_close=None, adj_close_date="", adj_status="MISSING(Yahoo 還原價缺或核對 MISMATCH · 不拿 Close 冒充)")
        rd = str(row.get("REPORT_DATE") or "")
        rec["report_date"] = rd
        try:
            rdd = _dt.date.fromisoformat(rd)
            before = adj[adj["date"] < rdd]
            if len(before):
                b = before.iloc[-1]
                fac = float(b["adj_close"]) / float(b["close"]) if pd.notna(b.get("close")) and float(b["close"]) else None
                rec.update(adj_close_before_report=float(b["adj_close"]), adj_close_before_report_date=str(b["date"]), adjustment_factor_report=fac)
            else:
                rec.update(adj_close_before_report=None, adj_close_before_report_date="", adjustment_factor_report=None, before_status="MISSING(報告日前沒有日資料 · 需 --start 回補)")
        except ValueError:
            rec.update(adj_close_before_report=None, adjustment_factor_report=None, before_status="MISSING(報告日格式不是 YYYY-MM-DD)")
        tp = row.get("TARGET_PRICE")
        try:
            tpv = float(str(tp).replace(",", "")) if tp not in (None, "") else None
        except ValueError:
            tpv = None
        fac = rec.get("adjustment_factor_report")
        if tpv is not None and fac:
            rec["target_price_adj"] = round(tpv * fac, 2)
            if rec.get("adj_close"):
                rec["upside_pct_adj"] = round((rec["target_price_adj"] / rec["adj_close"] - 1) * 100, 1)
        rec["status"] = "OK" if rec.get("adj_close") is not None else "PARTIAL"
        per_file[row.get("FILENAME")] = rec
        per_ticker[code] = {k: rec[k] for k in ("name", "yfinance_ticker", "bloomberg_ticker", "adj_close", "adj_close_date") if k in rec}
        n_ok += int(rec["status"] == "OK")
    res = {"version": VERSION, "ts": _dt.datetime.now().isoformat(timespec="seconds"), "engine": ENGINE_NAME, "rule": "TARGET_PRICE(ADJ) = TARGET_PRICE × 報告日前最後交易日的 adj_close/close · UPSIDE_PCT(ADJ) = TARGET_PRICE(ADJ)/最新 ADJ_CLOSE - 1 · 缺就 MISSING 不猜",
           "per_file": per_file, "per_ticker": per_ticker}
    out.mkdir(parents=True, exist_ok=True)
    (out / "VRN2_Market_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "GREEN" if n_ok and not n_miss else ("YELLOW" if n_ok else "RED"), "msg": "市場資料填值 · 代號 %d · 完整 %d · 部分 %d · 缺 %d → %s" % (len(per_ticker), n_ok, len(per_file) - n_ok - n_miss, n_miss, out / "VRN2_Market_latest.json")}


def selftest(argv: list) -> int:
    ok = 0
    tt = [ticker_type(x)[0] for x in ("2330", "0050", "00878", "00981A", "00679B", "00631L", "00632R", "00635U", "00701T", "0050.TW", "00631L TT", "123")]
    e = tt == ["STOCK", "ETF_EQUITY_PASSIVE", "ETF_EQUITY_PASSIVE", "ETF_EQUITY_ACTIVE", "ETF_BOND_PASSIVE", "ETF_LEVERAGED", "ETF_INVERSE", "ETF_FUTURES", "ETF_BALANCED", "ETF_EQUITY_PASSIVE", "ETF_LEVERAGED", ""]
    print("  [%s] 代碼分類九類(Regex v0103)%s" % ("OK" if e else "FAIL", tt)); ok += int(e)
    f = forms("2330", "TWSE"); g = forms("6488", "TPEX")
    a = f["yfinance_ticker"] == "2330.TW" and f["bloomberg_ticker"] == "2330 TT" and g["yfinance_ticker"] == "6488.TWO" and forms("0050", "TWSE") == {}
    print("  [%s] 三碼規則 = VDF def_identity = VRN2 Regex v0101(TWSE .TW · TPEX .TWO · TT · ETF 不在範圍)" % ("OK" if a else "FAIL")); ok += int(a)
    import tempfile
    import pandas as pd
    td = Path(tempfile.mkdtemp()); vdf = td / "vdf"
    (vdf / "parquet" / "tw_universe" / "ticker=2330" / "year=2026").mkdir(parents=True)
    pd.DataFrame([{"ticker": "2330", "name": "台積電", "market": "TWSE"}]).to_parquet(vdf / "parquet" / "tw_universe" / "ticker=2330" / "year=2026" / "data.parquet")
    (vdf / "parquet" / "tw_equity_daily" / "ticker=2330" / "year=2026").mkdir(parents=True)
    pd.DataFrame([{"date": pd.Timestamp("2026-05-18"), "ticker": "2330", "name": "台積電", "market": "TWSE", "close": 1000.0, "adj_close": 980.0},
                  {"date": pd.Timestamp("2026-05-20"), "ticker": "2330", "name": "台積電", "market": "TWSE", "close": 1010.0, "adj_close": 1010.0}]).to_parquet(vdf / "parquet" / "tw_equity_daily" / "ticker=2330" / "year=2026" / "data.parquet")
    bp = td / "basic.json"
    bp.write_text(json.dumps([{"FILENAME": "x.pdf", "TICKER": "2330", "REPORT_DATE": "2026-05-19", "TARGET_PRICE": "1,200"}, {"FILENAME": "y.pdf", "TICKER": "9999", "REPORT_DATE": "2026-05-19", "TARGET_PRICE": "10"}]), encoding="utf-8")
    r = fill({"basic": str(bp), "out": str(td)})
    m = json.loads((td / "VRN2_Market_latest.json").read_text(encoding="utf-8"))["per_file"]
    x = m["x.pdf"]
    b = x["name"] == "台積電" and x["yfinance_ticker"] == "2330.TW" and x["adj_close"] == 1010.0 and x["adj_close_before_report"] == 980.0 and abs(x["target_price_adj"] - 1176.0) < 0.01 and abs(x["upside_pct_adj"] - 16.4) < 0.1 and m["y.pdf"]["status"] == "MISSING"
    print("  [%s] 填值:NAME / .TW / 最新 ADJ 1010 / 報告前 ADJ 980(因子 0.98)/ TP(ADJ) %s / 上漲 %s%% / 無資料代號 MISSING" % ("OK" if b else "FAIL", x.get("target_price_adj"), x.get("upside_pct_adj"))); ok += int(b)
    c = _tickers_from_scope(Path(tempfile.mkdtemp())) == []
    sc = Path(tempfile.mkdtemp()); (sc / "20250819兆豐個股報告-泓德能源(6873).pdf").write_bytes(b"x"); (sc / "GS-2317 20251205.pdf").write_bytes(b"x")
    c = _tickers_from_scope(sc) == ["6873", "2317"]
    print("  [%s] 檔名前四碼原則取代號 %s" % ("OK" if c else "FAIL", _tickers_from_scope(sc))); ok += int(c)
    eng = engine_path()
    print("  [%s] VDF 引擎在 %s" % ("OK" if eng else "FAIL", eng)); ok += int(bool(eng))
    n = 5
    if eng and "--with-vdf-tests" in argv:
        t = eng.parent / "test_VDF_TW_DataFetchEngine_v036.py"
        r2 = subprocess.run([sys.executable, "-W", "ignore", str(t)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600, cwd=str(eng.parent))
        d = r2.returncode == 0 and "OK" in r2.stderr + r2.stdout
        print("  [%s] VDF 引擎離線回歸 28 項 rc %d" % ("OK" if d else "FAIL", r2.returncode)); ok += int(d); n += 1
    print("[計] VRN2_MarketFetch %s 自測 %d/%d · %s" % (VERSION, ok, n, "PASS" if ok == n else "FAIL"))
    return 0 if ok == n else 1


def main(argv: list) -> int:
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest(argv)
    a = {"basic": opt("--basic"), "tickers": opt("--tickers", ""), "out": opt("--out", str(HERE.parent.parent / "VIA_Reports" / "vrn2" / "market")), "scope": opt("--scope"), "days": opt("--days", "400"), "timeout": opt("--timeout", "1800"), "offline": "--offline" in argv}
    if "--fetch" in argv:
        r = fetch(a); print("[計] 市場擷取 · %s · %s" % (r["lamp"], r["msg"]), flush=True); return 0 if r["lamp"] != "RED" else 1
    if "--fill" in argv:
        if not a["basic"]:
            print("[RED] --fill 需要 --basic"); return 2
        r = fill(a); print("[計] 市場填值 · %s · %s" % (r["lamp"], r["msg"]), flush=True); return 0 if r["lamp"] != "RED" else 1
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
