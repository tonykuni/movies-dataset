#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_MarketFetch v0103 — VRN-2 的市場資料擷取引擎(包住 VDF_TW_DataFetchEngine v036 · 不改它一字 · 用引擎擷取 · 不靠既有資料庫)。

動詞:
  --fetch  [--basic <VRN2_BasicInfo_latest.json>] [--tickers 2330,6488] [--out <market 夾>]
           v0102 只抓必要日期:① 最新(今天 - 7 天 ~ 今天)② 每份報告日前一個交易日(報告日 - 7 天 ~ 報告日 - 1 天)→ 依視窗分組各跑一次 VDF 引擎 daily
           ③ 年度財報 n-3 ~ n(n = 報告年)→ --datasets financial --quarters {y}Q4(已完成的年度)+ latest(最新一季)· 依年組分組各跑一次
           代號來源:基本資料冊 TICKER(4 碼)· 或 --tickers · 或 --scope <scope_in 夾>(檔名前四碼原則)
           以 VDF 引擎 --datasets daily --start(最早報告日 - 10 天 · 至少 --days)--end 今天 --output <market>/vdf 擷取(官方 TWSE / TPEX + Yahoo 還原)
           Python 優先用 %USERPROFILE%\\envs\\via_tw_fetch\\Scripts\\python.exe(VDF 包自己的環境)· 沒有就用本行程 Python(缺 yfinance / lxml → 回報交 VCGC)
  --fill   --basic <VRN2_BasicInfo_latest.json> --out <market 夾>
           讀 <market>/vdf/parquet/tw_universe + tw_equity_daily → 每檔:NAME · YFINANCE_TICKER · BLOOMBERG_TICKER · ADJ_CLOSE(最新)· ADJ_CLOSE_BEFORE_REPORT(報告日前最後一個交易日)·
           還原因子(報告日)→ TARGET_PRICE(ADJ)= TARGET_PRICE × 因子 · UPSIDE_PCT(ADJ)= TARGET_PRICE(ADJ)/ADJ_CLOSE - 1 → <market>/VRN2_Market_latest.json
           沒有的值寫 MISSING 與理由(不猜 · 不拿 Close 冒充 Adj Close)
  --selftest  三碼規則與 VRN2 Regex 對照 · 合成 parquet 填值 · 引擎在則跑其 28 項離線回歸(--with-vdf-tests)
  --doctor [--out <market 夾>]  v0103 診斷:Python 版本 · 引擎可否編譯 / 匯入 · VIA 網路橋偵測(def_via_bridges)· 必要套件 · 最近一次失敗尾端(last_error.txt)
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0103"
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


def _run_engine(eng: Path, py: str, tickers: list, extra: list, vdf: Path, timeout: int) -> tuple:
    cmd = [py, "-W", "ignore", str(eng), "--tickers", ",".join(tickers), "--output", str(vdf)] + extra
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, cwd=str(eng.parent))
        lines = (r.stdout + r.stderr).strip().splitlines()
        if r.returncode not in (0, 2):                                         # v0103 失敗:完整尾端落盤
            try:
                (vdf / "last_error.txt").write_text("CMD: %s\n\n%s" % (" ".join(cmd), "\n".join(lines[-40:])), encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass
        return r.returncode, lines[-6:]
    except subprocess.TimeoutExpired:
        return 124, ["逾時"]


def plan_windows(basic_rows: list, today: _dt.date, tickers_only: list = None) -> tuple:
    """v0102 必要日期:每份 (代號, 報告日) → 視窗 [報告日-7, 報告日-1];全部代號 → 最新視窗 [今天-7, 今天];財報 → 年組 {n-3..n 已完成年度 Q4} 依代號分組。"""
    daily, fin = {}, {}
    last_done_q4 = today.year - 1 if today.month >= 4 else today.year - 2            # Q4 財報約 3 月底公告 → 4 月後才算已完成
    for r in basic_rows:
        t = str(r.get("TICKER") or "").strip()
        m = _BASE.match(t) or re.match(r"^([1-9]\d{3})(?:\.TWO?|\s+TT)$", t)
        if not m:
            continue
        code = m.group(1)
        try:
            rd = _dt.date.fromisoformat(str(r.get("REPORT_DATE") or ""))
        except ValueError:
            continue
        key = ((rd - _dt.timedelta(days=7)).isoformat(), (rd - _dt.timedelta(days=1)).isoformat())
        daily.setdefault(key, set()).add(code)
        yrs = tuple("%dQ4" % y for y in range(rd.year - 3, rd.year + 1) if y <= last_done_q4)
        if yrs:
            fin.setdefault(yrs, set()).add(code)
    allt = sorted(set(c for v in daily.values() for c in v) | set(tickers_only or []))
    if allt:
        daily[((today - _dt.timedelta(days=7)).isoformat(), today.isoformat())] = set(allt)
    # 相近視窗合併(起日差 ≤ 14 天 → 合成一個視窗 · 減少跑次)
    merged = []
    for (s0, e0), ts in sorted(daily.items()):
        if merged and (_dt.date.fromisoformat(s0) - _dt.date.fromisoformat(merged[-1][0][0])).days <= 14:
            ps, pe = merged[-1][0]
            merged[-1] = ((ps, max(pe, e0)), merged[-1][1] | ts)
        else:
            merged.append(((s0, e0), set(ts)))
    return merged, fin, allt


def fetch(args: dict) -> dict:
    eng = engine_path()
    out = Path(args["out"]); vdf = out / "vdf"; vdf.mkdir(parents=True, exist_ok=True)
    if not eng:
        return {"lamp": "GRAY", "msg": "VDF 擷取引擎 %s 不在(_vdf_fetch)· 不擷取" % ENGINE_NAME}
    rows = []
    if args.get("basic") and Path(args["basic"]).exists():
        try:
            rows = json.loads(Path(args["basic"]).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            rows = []
    tickers = [t for t in (args.get("tickers") or "").split(",") if _BASE.match(t.strip())]
    if not tickers and not rows and args.get("scope"):
        tickers = _tickers_from_scope(Path(args["scope"]))
    today = _dt.date.today()
    windows, fin, allt = plan_windows(rows, today, tickers)
    if not allt:
        return {"lamp": "GRAY", "msg": "沒有代號(基本資料冊 / scope 都沒有 4 碼)· 不擷取"}
    py = fetch_python()
    probe = subprocess.run([py, "-c", "import yfinance, lxml, pandas, pyarrow, duckdb; print('ok')"], capture_output=True, text=True, timeout=120)
    if "ok" not in probe.stdout:
        return {"lamp": "YELLOW", "msg": "擷取環境缺套件(%s)· yfinance / lxml / pandas / pyarrow / duckdb → 交 VCGC 安裝或用 VDF 包的 via_tw_fetch 環境" % py, "tickers": allt}
    to = int(args.get("timeout") or 1800)
    runs, rcs, tails = 0, [], []
    for (s0, e0), ts in windows:                                               # ① ② 日線視窗
        rc, tail = _run_engine(eng, py, sorted(ts), ["--datasets", "daily", "--start", s0, "--end", e0] + (["--offline"] if args.get("offline") else []), vdf, to)
        runs += 1; rcs.append(rc); tails.append("%s~%s(%d檔) rc%d" % (s0[5:], e0[5:], len(ts), rc))
        if rc not in (0, 2):                                                   # v0103 致命錯(rc 1)第一次就停 · 不重複跑同樣的錯
            tails.append("致命錯 → 停止後續視窗"); break
    if not args.get("no_financial"):
        for yrs, ts in sorted(fin.items()):                                    # ③ 年度財報 n-3 ~ n
            rc, tail = _run_engine(eng, py, sorted(ts), ["--datasets", "financial", "--quarters", ",".join(yrs)] + (["--offline"] if args.get("offline") else []), vdf, to)
            runs += 1; rcs.append(rc); tails.append("財報 %s~%s(%d檔) rc%d" % (yrs[0][:4], yrs[-1][:4], len(ts), rc))
        if allt:
            rc, tail = _run_engine(eng, py, allt, ["--datasets", "financial", "--quarters", "latest"] + (["--offline"] if args.get("offline") else []), vdf, to)
            runs += 1; rcs.append(rc); tails.append("財報 latest(%d檔) rc%d" % (len(allt), rc))
    worst = max(rcs) if rcs else 1
    lamp = "GREEN" if all(r == 0 for r in rcs) else ("YELLOW" if all(r in (0, 2) for r in rcs) else "RED")
    err = ""
    if lamp == "RED" and (vdf / "last_error.txt").exists():
        err = " · 失敗原因(last_error.txt 末 3 行):" + " ⏎ ".join((vdf / "last_error.txt").read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:])[:300]
    return {"lamp": lamp, "msg": "VDF 引擎只抓必要日期 · 跑 %d 次(日線視窗 %d · 財報年組 %d + latest)· 代號 %d · 失敗 %d · %s%s" % (runs, len(windows), len(fin), len(allt), sum(1 for r in rcs if r not in (0, 2)), " / ".join(tails)[:160], err), "tickers": allt, "rc": worst}


def _read_parquet(glob_root: Path, table: str):
    import pandas as pd
    files = sorted((glob_root / "parquet" / table).glob("ticker=*/year=*/data.parquet"))
    if not files:
        return None
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


_STD = {"revenue": ("營業收入", "營業收入合計", "Revenue", "Net sales", "Total revenue", "營收"), "operating_income": ("營業利益", "營業利益(損失)", "營業利益（損失）", "Operating income", "Operating profit"),
        "net_income": ("本期淨利", "本期淨利(淨損)", "本期淨利（淨損）", "Net income", "Net profit", "本期淨利（損）歸屬於母公司業主", "淨利（損）歸屬於母公司業主"),
        "eps_diluted": ("稀釋每股盈餘", "稀釋每股盈餘合計", "Diluted EPS"), "eps_basic": ("基本每股盈餘", "基本每股盈餘合計", "Basic EPS"),
        "equity": ("權益總額", "權益總計", "股東權益總額", "歸屬於母公司業主之權益合計", "歸屬於母公司業主之權益", "Total equity"),
        "dps_cash": ("現金股利", "每股現金股利", "Cash dividend")}                           # V2:PER 用稀釋 EPS · ROE 用前後期平均權益 · DPS 遞延規則(VDF v036 無股利資料集 → STATUS 註記)


def _ratios(fa: list, adj_close) -> dict:
    """V2 規範:ROE = 本期淨利 / 平均權益(前期 + 當期)/2 · PER = 還原收盤 / 稀釋 EPS(嚴格)· 全部純小數 · 算不出來寫原因。"""
    by = {}
    for x in fa:
        by.setdefault(x["year"], {})[x["std"]] = x.get("value")
    out = {"roe_avg_equity": {}, "per_diluted": None, "notes": []}
    for y in sorted(by):
        ni, eq, eq0 = by[y].get("net_income"), by[y].get("equity"), (by.get(y - 1) or {}).get("equity")
        if ni is not None and eq is not None and eq0 is not None and (eq + eq0):
            out["roe_avg_equity"][str(y)] = round(ni / ((eq + eq0) / 2.0), 9)
        elif ni is not None and eq is not None:
            out["notes"].append("ROE %d 未算:缺前期權益(需 n-1 年資產負債表)" % y)
    ys = [y for y in sorted(by) if by[y].get("eps_diluted") is not None and (by[y].get("basis") in (None, "ANNUAL") or True)]
    if ys and adj_close:
        y = ys[-1]; eps = by[y]["eps_diluted"]
        if eps:
            out["per_diluted"] = round(float(adj_close) / float(eps), 9); out["per_year"] = y
    elif adj_close:
        out["notes"].append("PER 未算:無稀釋 EPS(嚴格不用基本 EPS)")
    out["notes"].append("DPS 遞延規則未套用:VDF v036 無股利資料集(已宣告未發放應遞延往後一年)")
    return out


def _std_of(account: str) -> str:
    a = str(account or "").replace(" ", "")
    for k, names in _STD.items():
        if any(n.replace(" ", "") in a for n in names):
            return k
    return ""


def _annual(finrows, code: str, rd: str) -> list:
    """年度財報 n-3 ~ n(n = 報告年):ANNUAL(Q4 YTD)優先 · n 年沒有年度就用最新 YTD · 只收四個標準科目(其餘留在 VDF 落盤)."""
    try:
        n = int(str(rd)[:4])
    except ValueError:
        return []
    f = finrows[finrows["ticker"].astype(str) == code]
    if not len(f):
        return []
    out = []
    for y in range(n - 3, n + 1):
        fy = f[f["fiscal_year"].astype(str) == str(y)]
        if not len(fy):
            continue
        ann = fy[fy["basis"].astype(str) == "ANNUAL"]
        pick = ann if len(ann) else fy[fy["basis"].astype(str) == "YTD"]
        if not len(pick):
            continue
        q = pick["quarter"].astype(str).max() if "quarter" in pick else ""
        pick = pick[pick["quarter"].astype(str) == q] if q else pick
        for _, r in pick.iterrows():
            std = _std_of(r.get("account"))
            if std and not any(o["year"] == y and o["std"] == std for o in out):
                out.append({"year": y, "std": std, "account": r.get("account"), "value": float(r["value"]) if r.get("value") not in (None, "") else None, "unit": r.get("unit"), "basis": r.get("basis"), "quarter": r.get("quarter"), "scope": r.get("report_scope"), "statement": r.get("financial_statement")})
    return out


def fill(args: dict) -> dict:
    import pandas as pd
    out = Path(args["out"]); vdf = out / "vdf"
    basic = json.loads(Path(args["basic"]).read_text(encoding="utf-8"))
    uni = _read_parquet(vdf, "tw_universe")
    daily = _read_parquet(vdf, "tw_equity_daily")
    finrows = _read_parquet(vdf, "tw_financial")
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
                rec["upside_adj"] = round(rec["target_price_adj"] / rec["adj_close"] - 1, 9)          # V2 純小數
                rec["upside_pct_adj"] = round(rec["upside_adj"] * 100, 1)
        rec["financial_annual"] = _annual(finrows, code, rd) if finrows is not None else []
        rec["ratios"] = _ratios(rec["financial_annual"], rec.get("adj_close"))
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
    rows = [{"TICKER": "2330", "REPORT_DATE": "2025-08-19"}, {"TICKER": "2317", "REPORT_DATE": "2025-08-22"}, {"TICKER": "6488", "REPORT_DATE": "2023-10-11"}]
    w, fq, allt = plan_windows(rows, _dt.date(2026, 10, 27))
    g = len(w) == 3 and w[0][0] == ("2023-10-04", "2023-10-10") and w[1][0] == ("2025-08-12", "2025-08-21") and w[1][1] == {"2330", "2317"} and w[2][0] == ("2026-10-20", "2026-10-27") and fq == {("2022Q4", "2023Q4", "2024Q4", "2025Q4"): {"2330", "2317"}, ("2020Q4", "2021Q4", "2022Q4", "2023Q4"): {"6488"}}
    print("  [%s] 必要日期規劃:日線視窗 %d(相近報告日合併)· 財報年組 %s" % ("OK" if g else "FAIL", len(w), {k[0] + ".." + k[-1]: sorted(v) for k, v in fq.items()})); ok += int(g)
    (vdf / "parquet" / "tw_financial" / "ticker=2330" / "year=2025").mkdir(parents=True)
    pd.DataFrame([{"ticker": "2330", "fiscal_year": 2025, "quarter": "Q4", "basis": "ANNUAL", "financial_statement": "INCOME_STATEMENT", "account": "營業收入合計", "value": 3000000.0, "unit": "TWD_THOUSAND", "report_scope": "CONSOLIDATED"},
                  {"ticker": "2330", "fiscal_year": 2025, "quarter": "Q4", "basis": "ANNUAL", "financial_statement": "INCOME_STATEMENT", "account": "基本每股盈餘", "value": 45.25, "unit": "TWD_PER_SHARE", "report_scope": "CONSOLIDATED"},
                  {"ticker": "2330", "fiscal_year": 2026, "quarter": "Q2", "basis": "YTD", "financial_statement": "INCOME_STATEMENT", "account": "營業收入合計", "value": 1700000.0, "unit": "TWD_THOUSAND", "report_scope": "CONSOLIDATED"}]).to_parquet(vdf / "parquet" / "tw_financial" / "ticker=2330" / "year=2025" / "data.parquet")
    r = fill({"basic": str(bp), "out": str(td)})
    fa = json.loads((td / "VRN2_Market_latest.json").read_text(encoding="utf-8"))["per_file"]["x.pdf"].get("financial_annual") or []
    rt = _ratios([{"year": 2024, "std": "equity", "value": 4000.0}, {"year": 2025, "std": "equity", "value": 5000.0}, {"year": 2025, "std": "net_income", "value": 900.0}, {"year": 2025, "std": "eps_diluted", "value": 45.0}], 1010.0)
    i2 = abs(rt["roe_avg_equity"]["2025"] - 0.2) < 1e-9 and abs(rt["per_diluted"] - 1010.0 / 45.0) < 1e-9
    print("  [%s] V2 比率:ROE 平均權益 900/((4000+5000)/2)=%s · PER 稀釋 1010/45=%s(純小數)" % ("OK" if i2 else "FAIL", rt["roe_avg_equity"].get("2025"), rt["per_diluted"])); ok += int(i2)
    h = [(x["year"], x["std"], x["basis"]) for x in fa] == [(2025, "revenue", "ANNUAL"), (2025, "eps_basic", "ANNUAL"), (2026, "revenue", "YTD")]
    print("  [%s] 年度財報 n-3~n:2025 ANNUAL 營收 / EPS · 2026 用最新 YTD %s" % ("OK" if h else "FAIL", [(x["year"], x["std"], x["basis"]) for x in fa])); ok += int(h)
    eng = engine_path()
    print("  [%s] VDF 引擎在 %s" % ("OK" if eng else "FAIL", eng)); ok += int(bool(eng))
    n = 8
    if eng and "--with-vdf-tests" in argv:
        t = eng.parent / "test_VDF_TW_DataFetchEngine_v036.py"
        r2 = subprocess.run([sys.executable, "-W", "ignore", str(t)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600, cwd=str(eng.parent))
        d = r2.returncode == 0 and "OK" in r2.stderr + r2.stdout
        print("  [%s] VDF 引擎離線回歸 28 項 rc %d" % ("OK" if d else "FAIL", r2.returncode)); ok += int(d); n += 1
    print("[計] VRN2_MarketFetch %s 自測 %d/%d · %s" % (VERSION, ok, n, "PASS" if ok == n else "FAIL"))
    return 0 if ok == n else 1


def doctor(args: dict) -> int:
    eng = engine_path(); py = fetch_python()
    out = Path(args["out"]); vdf = out / "vdf"
    print("[計] 診斷 · Python %s · 引擎 %s · 擷取 Python %s" % (sys.version.split()[0], eng or "不在", py))
    if not eng:
        return 1
    r = subprocess.run([py, "-c", "import sys,py_compile;py_compile.compile(sys.argv[1],doraise=True);print('編譯 OK',sys.version.split()[0])", str(eng)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    print("[計]   編譯 → %s" % ((r.stdout + r.stderr).strip().splitlines() or ["?"])[-1][:200])
    probe = "import importlib.util,sys,json;sp=importlib.util.spec_from_file_location('e',sys.argv[1]);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);b=m.def_via_bridges(m.DEFAULT_VIA_ROOT);print('匯入 OK · via_root',m.DEFAULT_VIA_ROOT,'· accel',b['accel'],'· network',b['network'])"
    r = subprocess.run([py, "-W", "ignore", "-c", probe, str(eng)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, cwd=str(eng.parent))
    for l in (r.stdout + r.stderr).strip().splitlines()[-4:]:
        print("[計]   橋偵測 → %s" % l[:220])
    r = subprocess.run([py, "-c", "import yfinance, lxml, pandas, pyarrow, duckdb; print('套件 ok', yfinance.__version__, pandas.__version__)"], capture_output=True, text=True, timeout=120)
    print("[計]   套件 → %s" % ((r.stdout + r.stderr).strip().splitlines() or ["?"])[-1][:200])
    le = vdf / "last_error.txt"
    if le.exists():
        print("[計]   最近失敗(last_error.txt):")
        for l in le.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-8:]:
            print("[計]     " + l[:220])
    return 0


def main(argv: list) -> int:
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest(argv)
    a = {"basic": opt("--basic"), "tickers": opt("--tickers", ""), "out": opt("--out", str(HERE.parent.parent / "VIA_Reports" / "vrn2" / "market")), "scope": opt("--scope"), "timeout": opt("--timeout", "1800"), "offline": "--offline" in argv, "no_financial": "--no-financial" in argv}
    if "--doctor" in argv:
        return doctor(a)
    if "--fetch" in argv:
        r = fetch(a); print("[計] 市場擷取 · %s · %s" % (r["lamp"], r["msg"]), flush=True); return 0 if r["lamp"] != "RED" else 1
    if "--fill" in argv:
        if not a["basic"]:
            print("[RED] --fill 需要 --basic"); return 2
        r = fill(a); print("[計] 市場填值 · %s · %s" % (r["lamp"], r["msg"]), flush=True); return 0 if r["lamp"] != "RED" else 1
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
