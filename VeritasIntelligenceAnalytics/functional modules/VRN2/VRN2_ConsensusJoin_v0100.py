#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_ConsensusJoin v0100 — 借用操作員上傳的 VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine(v0120 · 不改它一字)抓 FactSet / YFinance 共識,組 Combined 冊(操作員 2026-10-29)。

操作員令:「Report Target Price(Adj) / FactSet Target Price Median / YFinance Target Price Median / 2026 Diluted EPS (FactSet) / 2027 / 2028 / 2026 PER (FactSet) / 2027 / 2028
          在 Combined 目標價後面加上上述;n 是今年 2026、n+1 2027,把他們還原真實年分」+ 欄名雙語(Report Date / 報告日期 …)。

動詞:
  run  [--v2 <VIA_Reports/vrn2>] [--engine <引擎檔>] [--fixture <json>…] [--timeout 900]
       代號 = 基本資料冊 TICKER(4 碼 · 去重 · 最多 50)→ 子行程跑引擎:--codes --output-dir <v2>/consensus --skip-unit-tests --allow-missing-duckdb(有 duckdb 它自己會用)
       Python 優先 $env:VIA_FETCH_PY → %USERPROFILE%\\envs\\via_tw_fetch\\Scripts\\python.exe(VDF 包的環境 · 有 yfinance)→ 本行程;線上模式缺 yfinance → 黃燈交 VCGC,不抓
       → 讀 factset_yfinance_consensus_matrix.csv → <v2>/consensus/VRN2_Consensus_latest.json(每代號:FactSet 目標價中位數 · YFinance 目標價中位數 · 各真實年度 EPS 中位數 / forward PER · 現價 · 擷取時間 · 來源)
       --fixture = 引擎的離線 fixture(測試 / 無網路);$env:VIA_VRN2_NO_CONSENSUS=1 → 灰燈不跑。
  join [--v2 …]
       Combined 冊 = 每份報告一列(基本資料冊順序)· 欄序照操作員雙語清單:REPORT_DATE · FILENAME · TICKER · YFINANCE_TICKER · BLOOMBERG_TICKER · NAME · BROKER · ANALYST · RATING · TARGET_PRICE ·
       TARGET_PRICE(ADJ)(報告目標價 × 報告日還原因子 · 來自 ⑥e 市場資料)· FACTSET_TARGET_PRICE_MEDIAN · YFINANCE_TARGET_PRICE_MEDIAN · <n>_DILUTED_EPS_FACTSET ×3 · <n>_PER_FACTSET ×3(n = 今年 · 真實年份)·
       CURRENT_PRICE_REPORT · UPSIDE_PCT(ADJ) · ADJ_CLOSE · ADJ_CLOSE_BEFORE_REPORT · TOPIC & SUMMARY(標題 + 四點)· STATUS(各欄來源 / 缺的原因)
       → output/VRN2_Combined_latest.json / .csv(/ .parquet 有 pyarrow 才寫)。基本資料冊 / 摘要冊 / 市場 json 一字不改。
  --selftest(用內建 fixture 離線跑引擎 · 需要引擎檔在同夾或 --engine)
[VIA:AST-CLASS] 類別 = 共識資料包裝 + 合併冊(VRN-2)· 入口 = ActivateVRN-2 ⑥f / 本檔 CLI
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

VERSION = "v0100"
DISPLAY_NAME = "VRN2_ConsensusJoin"
TAG = "共識合併 v0100"
HERE = Path(__file__).resolve().parent
ENGINE_GLOB = "VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v[0-9][0-9][0-9][0-9].py"
MATRIX_CSV = "factset_yfinance_consensus_matrix.csv"
CONSENSUS_JSON = "VRN2_Consensus_latest.json"
MAX_CODES = 50
_CODE = re.compile(r"^([1-9]\d{3})(?:\.TWO?|\s+TT)?$", re.I)
HEAD = ["REPORT_DATE", "FILENAME", "TICKER", "YFINANCE_TICKER", "BLOOMBERG_TICKER", "NAME", "BROKER", "ANALYST", "RATING", "TARGET_PRICE", "TARGET_PRICE(ADJ)", "FACTSET_TARGET_PRICE_MEDIAN", "YFINANCE_TARGET_PRICE_MEDIAN"]
TAIL = ["CURRENT_PRICE_REPORT", "UPSIDE_PCT(ADJ)", "ADJ_CLOSE", "ADJ_CLOSE_BEFORE_REPORT", "TOPIC & SUMMARY", "STATUS"]


def say(line: str) -> None:
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("utf-8", "replace").decode("ascii", "replace"), flush=True)


def now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def this_year() -> int:
    try:
        return int(os.environ.get("VRN2_CONSENSUS_YEAR") or _dt.date.today().year)
    except ValueError:
        return _dt.date.today().year


def year_columns(n: int | None = None) -> list:
    n = n or this_year()
    return ["%d_DILUTED_EPS_FACTSET" % y for y in (n, n + 1, n + 2)] + ["%d_PER_FACTSET" % y for y in (n, n + 1, n + 2)]


def columns(n: int | None = None) -> list:
    return HEAD + year_columns(n) + TAIL


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.py$", p.name)
    return int(m.group(1)) if m else -1


def engine_path(root: Path | None = None, explicit: str | None = None) -> Path | None:
    if explicit and Path(explicit).is_file():
        return Path(explicit)
    folders = [HERE]
    if root:
        folders += [Path(root) / "functional modules" / "VRN2", Path(root) / "functional modules" / "VRN", Path(root) / "functional modules" / "VDF", Path(root) / "supportive modules"]
    hits = []
    for f in folders:
        if f.is_dir():
            hits += list(f.glob(ENGINE_GLOB))
    hits = sorted(set(hits), key=_vnum)
    return hits[-1] if hits else None


def fetch_python() -> str:
    if os.environ.get("VIA_FETCH_PY") and Path(os.environ["VIA_FETCH_PY"]).is_file():
        return os.environ["VIA_FETCH_PY"]
    up = os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""
    for cand in (Path(up) / "envs" / "via_tw_fetch" / "Scripts" / "python.exe", Path(up) / "envs" / "via_tw_fetch" / "bin" / "python"):
        if up and cand.is_file():
            return str(cand)
    return sys.executable


def codes_from_basic(v2: Path) -> list:
    try:
        rows = json.loads((Path(v2) / "output" / "VRN2_BasicInfo_latest.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for r in rows:
        m = _CODE.match(str((r or {}).get("TICKER") or "").strip())
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out[:MAX_CODES]


def _stream(command: list, cwd: Path, wait: int, prefix: str = "    [⑥f] ") -> tuple:
    """跑子行程、逐行回印(有前綴)、超過 wait 秒就停;回 (rc, 全部行)。"""
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen(command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=env)
    q: queue.Queue = queue.Queue()

    def pump():
        for line in proc.stdout:
            q.put(line)
        q.put(None)
    threading.Thread(target=pump, daemon=True).start()
    lines, started = [], time.time()
    while True:
        try:
            line = q.get(timeout=5)
        except queue.Empty:
            if time.time() - started > wait:
                proc.kill()
                lines.append("[RED] 逾時 %d 秒 · 已停止" % wait)
                say(prefix + lines[-1])
                break
            continue
        if line is None:
            break
        lines.append(line.rstrip("\n"))
        say(prefix + lines[-1][:300])
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
    return (proc.returncode if proc.returncode is not None else -9), lines


def _f(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def parse_matrix(path: Path) -> dict:
    per = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            code = str(row.get("code") or "").strip()
            if not code:
                continue
            eps, per_ = {}, {}
            for k, v in row.items():
                m = re.match(r"^eps_(\d{4})_median$", k or "")
                if m and v not in (None, ""):
                    eps[m.group(1)] = _f(v)
                m = re.match(r"^eps_(\d{4})_forward_pe$", k or "")
                if m and v not in (None, ""):
                    per_[m.group(1)] = _f(v)
            per[code] = {"code": code, "symbol": row.get("symbol"), "company_name": row.get("company_name"), "fetched_at_utc": row.get("fetched_at_utc"), "current_price": _f(row.get("current_price")),
                         "factset_target_median": _f(row.get("target_median")), "factset_target_mean": _f(row.get("target_mean")), "factset_analyst_count": row.get("target_analyst_count"), "factset_rate_date": row.get("target_rate_date"),
                         "yf_target_median": _f(row.get("yf_target_median")), "yf_target_mean": _f(row.get("yf_target_mean")), "yf_analyst_count": row.get("yf_target_analyst_count"), "yf_current_price": _f(row.get("yf_current_price")),
                         "eps_median": eps, "forward_pe": per_, "source_agreement_gate": row.get("source_agreement_gate"), "source_page": row.get("source_page"), "source_yfinance": row.get("source_yfinance")}
    return per


def run(v2: Path, root: Path | None = None, fixtures: list | None = None, timeout: int = 900, engine: str | None = None) -> dict:
    v2 = Path(v2)
    out = v2 / "consensus"
    rec = {"engine_wrapper": "%s %s" % (DISPLAY_NAME, TAG), "verb": "run", "at": now(), "year_n": this_year(), "columns": year_columns()}
    eng = engine_path(root, engine)
    codes = codes_from_basic(v2)
    if os.environ.get("VIA_VRN2_NO_CONSENSUS") == "1":
        rec.update(lamp="GRAY", why="VIA_VRN2_NO_CONSENSUS=1 · 本輪不抓共識")
        return _finish(out, rec)
    if not eng:
        rec.update(lamp="GRAY", why="沒有共識引擎 %s(runtime / functional modules)· 不抓" % ENGINE_GLOB)
        return _finish(out, rec)
    if not codes:
        rec.update(lamp="GRAY", why="基本資料冊沒有 4 碼代號 · 不抓", engine=str(eng))
        return _finish(out, rec)
    py = fetch_python()
    rec.update(engine=str(eng), python=py, codes=codes)
    if not fixtures:
        probe = subprocess.run([py, "-c", "import yfinance; print('ok', yfinance.__version__)"], capture_output=True, text=True, timeout=120)
        if "ok" not in probe.stdout:
            rec.update(lamp="YELLOW", why="擷取環境缺 yfinance(%s)→ 交 VCGC 安裝或用 VDF 包的 via_tw_fetch 環境 · 本輪共識欄留空" % py)
            return _finish(out, rec)
    out.mkdir(parents=True, exist_ok=True)
    cmd = [py, "-X", "utf8", str(eng), "--codes", ",".join(codes), "--output-dir", str(out), "--skip-unit-tests", "--allow-missing-duckdb"]
    if fixtures:
        cmd += ["--no-resume"]
        for f in fixtures:
            cmd += ["--fixture", str(f)]
    rc, lines = _stream(cmd, eng.parent, timeout)
    gate = next((l.split(":", 1)[1].strip() for l in lines if l.startswith("def Gate")), "")
    rec.update(rc=rc, gate=gate, lines=len(lines), tail=[l[:200] for l in lines[-6:]])
    matrix = out / MATRIX_CSV
    if not matrix.is_file():
        rec.update(lamp="YELLOW" if rc else "YELLOW", why="引擎沒出矩陣 %s(rc %s · gate %s)· %s" % (MATRIX_CSV, rc, gate or "—", (lines[-1] if lines else "沒有輸出")[:160]))
        return _finish(out, rec)
    per = parse_matrix(matrix)
    got = [c for c in codes if c in per]
    rec.update(per_code=per, codes_got=got, codes_missing=[c for c in codes if c not in per])
    if got and not rec["codes_missing"]:
        rec.update(lamp="GREEN" if rc == 0 else "YELLOW", why="共識 %d / %d 代號 · FactSet 中位數 %d · YFinance 中位數 %d · gate %s · rc %s" % (len(got), len(codes), sum(1 for c in got if per[c]["factset_target_median"] is not None), sum(1 for c in got if per[c]["yf_target_median"] is not None), gate or "—", rc))
    elif got:
        rec.update(lamp="YELLOW", why="共識 %d / %d 代號(缺 %s)· gate %s · rc %s" % (len(got), len(codes), ",".join(rec["codes_missing"][:8]), gate or "—", rc))
    else:
        rec.update(lamp="YELLOW", why="矩陣裡沒有任何要的代號 · gate %s · rc %s" % (gate or "—", rc))
    return _finish(out, rec)


def _finish(out: Path, rec: dict) -> dict:
    try:
        out.mkdir(parents=True, exist_ok=True)
        p = out / CONSENSUS_JSON
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(p)
        rec["receipt"] = str(p)
    except OSError as error:
        rec["receipt_error"] = "%s: %s" % (type(error).__name__, error)
    return rec


def _jread(p: Path, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def _fmt(v, digits=2):
    if v is None:
        return ""
    try:
        return ("%." + str(digits) + "f") % float(v)
    except (TypeError, ValueError):
        return str(v)


def join(v2: Path) -> dict:
    v2 = Path(v2)
    out_dir = v2 / "output"
    basic = _jread(out_dir / "VRN2_BasicInfo_latest.json", [])
    summary = {r.get("FILENAME"): r for r in _jread(out_dir / "VRN2_Summary_latest.json", []) if isinstance(r, dict)}
    market = _jread(v2 / "market" / "VRN2_Market_latest.json", {}) or {}
    per_file = market.get("per_file") or {}
    cons = _jread(v2 / "consensus" / CONSENSUS_JSON, {}) or {}
    per_code = cons.get("per_code") or {}
    n = int(cons.get("year_n") or this_year())
    cols = columns(n)
    rec = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "join", "at": now(), "year_n": n, "columns": cols}
    if not isinstance(basic, list) or not basic:
        rec.update(lamp="GRAY", why="沒有基本資料冊 · 不組 Combined", rows=0)
        return rec
    rows = []
    n_adj = n_fs = n_yf = n_eps = 0
    for b in basic:
        if not isinstance(b, dict):
            continue
        fn = b.get("FILENAME")
        m = per_file.get(fn) or {}
        code_m = _CODE.match(str(b.get("TICKER") or "").strip())
        c = per_code.get(code_m.group(1)) if code_m else None
        s = summary.get(fn) or {}
        status = {}
        row = {k: b.get(k, "") for k in ("REPORT_DATE", "FILENAME", "TICKER", "YFINANCE_TICKER", "BLOOMBERG_TICKER", "NAME", "BROKER", "ANALYST", "RATING", "TARGET_PRICE", "CURRENT_PRICE_REPORT")}
        if not row["NAME"] and m.get("name"):
            row["NAME"] = m["name"]
            status["NAME"] = "VDF 清單"
        if not row["YFINANCE_TICKER"] and m.get("yfinance_ticker"):
            row["YFINANCE_TICKER"] = m["yfinance_ticker"]
        if not row["BLOOMBERG_TICKER"] and m.get("bloomberg_ticker"):
            row["BLOOMBERG_TICKER"] = m["bloomberg_ticker"]
        row["TARGET_PRICE(ADJ)"] = _fmt(m.get("target_price_adj"))
        status["TARGET_PRICE(ADJ)"] = "報告目標價 × 報告日還原因子 %s" % _fmt(m.get("adjustment_factor_report"), 6) if m.get("target_price_adj") is not None else ("缺:%s" % (m.get("before_status") or m.get("reason") or m.get("adj_status") or ("沒有市場資料(⑥e)" if not m else "沒有目標價或還原因子")))
        n_adj += int(m.get("target_price_adj") is not None)
        row["FACTSET_TARGET_PRICE_MEDIAN"] = _fmt((c or {}).get("factset_target_median"))
        row["YFINANCE_TARGET_PRICE_MEDIAN"] = _fmt((c or {}).get("yf_target_median"))
        if c:
            status["CONSENSUS"] = "FactSet(鉅亨)%s 位 · YFinance %s 位 · %s · gate %s" % (c.get("factset_analyst_count") or "—", c.get("yf_analyst_count") or "—", (c.get("fetched_at_utc") or "")[:19], c.get("source_agreement_gate") or "—")
            n_fs += int(c.get("factset_target_median") is not None)
            n_yf += int(c.get("yf_target_median") is not None)
        else:
            status["CONSENSUS"] = "缺:%s" % (cons.get("why") or "沒有共識資料(⑥f)")
        for y in (n, n + 1, n + 2):
            e = ((c or {}).get("eps_median") or {}).get(str(y))
            p = ((c or {}).get("forward_pe") or {}).get(str(y))
            row["%d_DILUTED_EPS_FACTSET" % y] = _fmt(e)
            row["%d_PER_FACTSET" % y] = _fmt(p)
            n_eps += int(e is not None)
        row["UPSIDE_PCT(ADJ)"] = _fmt(m.get("upside_pct_adj"), 1)
        row["ADJ_CLOSE"] = _fmt(m.get("adj_close")) or b.get("ADJ_CLOSE", "")
        row["ADJ_CLOSE_BEFORE_REPORT"] = _fmt(m.get("adj_close_before_report")) or b.get("ADJ_CLOSE_BEFORE_REPORT", "")
        if m.get("adj_close") is not None:
            status["ADJ_CLOSE"] = "Yahoo 還原收盤 %s" % (m.get("adj_close_date") or "")
        points = [str(s.get(k) or "").strip() for k in ("POINT_1", "POINT_2", "POINT_3", "POINT_4")]
        row["TOPIC & SUMMARY"] = (" · ".join([str(s.get("TITLE") or b.get("TITLE") or "").strip()] + [p for p in points if p])).strip(" ·")
        bs = b.get("_STATUS") if isinstance(b.get("_STATUS"), dict) else {}
        status["BASIC"] = "; ".join("%s %s" % (k, v) for k, v in list(bs.items())[:6])
        row["STATUS"] = " | ".join("%s: %s" % (k, v) for k, v in status.items() if v)
        rows.append({k: row.get(k, "") for k in cols})
    files = _write(out_dir, rows, cols)
    rec.update(rows=len(rows), target_adj=n_adj, factset_median=n_fs, yf_median=n_yf, eps_cells=n_eps, files=files)
    if n_fs or n_yf:
        rec.update(lamp="GREEN" if (n_adj and n_fs and n_yf) else "YELLOW", why="Combined %d 列 · 調整後目標價 %d · FactSet 中位數 %d · YFinance 中位數 %d · EPS 格 %d · 年 %d ~ %d" % (len(rows), n_adj, n_fs, n_yf, n_eps, n, n + 2))
    else:
        rec.update(lamp="YELLOW" if n_adj else "GRAY", why="Combined %d 列(共識欄全空:%s · 調整後目標價 %d)" % (len(rows), cons.get("why") or "⑥f 沒跑", n_adj))
    return rec


def _write(out_dir: Path, rows: list, cols: list) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    jp = out_dir / "VRN2_Combined_latest.json"
    tmp = jp.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(jp)
    files["json"] = str(jp)
    cp = out_dir / "VRN2_Combined_latest.csv"
    with cp.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    files["csv"] = str(cp)
    try:
        import pyarrow as pa  # noqa: WPS433
        import pyarrow.parquet as pq  # noqa: WPS433
        table = pa.Table.from_pylist([{k: ("" if r.get(k) is None else str(r.get(k))) for k in cols} for r in rows]) if rows else pa.table({c: pa.array([], pa.string()) for c in cols})
        pp = out_dir / "VRN2_Combined_latest.parquet"
        pq.write_table(table, str(pp), compression="zstd")
        files["parquet"] = str(pp)
    except Exception as error:  # noqa: BLE001
        files["parquet"] = "(沒寫:%s)" % type(error).__name__
    return files


# ===== selftest =====
def _fixture(path: Path, code: str, name: str, last: float, median: float, yf_median: float, eps: dict) -> Path:
    rate = [1761000000, 1758000000]
    fx = {"code": code, "captured_at_utc": "2026-10-29T02:00:00+00:00", "page": {"symbol": "TWS:%s:STOCK" % code, "url": "https://www.cnyes.com/twstock/%s/summary/overview" % code},
          "target": {"url": "https://marketinfo.api.cnyes.com/mi/api/v1/financialIndicator/targetPrice/TWS:%s:STOCK" % code, "payload": {"statusCode": 200, "message": "OK", "data": {"chName": name, "last": last, "feLow": median * 0.8, "feMean": median * 1.02, "feMedian": median, "feHigh": median * 1.2, "feStdDev": 5.0, "feUp": 3, "feDown": 1, "numEst": 20, "rateDate": "2026-10-20", "currency": "TWD"}}},
          "rating": {"url": "x", "payload": {"statusCode": 200, "message": "OK", "data": {"chName": name, "rateDate": rate, "feMark": [1.4, 1.5], "feBuy": [12, 11], "feOver": [5, 5], "feHold": [3, 4], "feUnder": [0, 0], "feSell": [0, 0], "feMedian": [median, median * 0.95], "currency": "TWD"}}},
          "eps": {"url": "x", "payload": {"statusCode": 200, "message": "OK", "data": [{"financialYear": y, "feMedian": v, "feLow": v * 0.9, "feMean": v * 1.01, "feHigh": v * 1.1, "feStdDev": 0.5, "feUp": 2, "feDown": 1, "numEst": 18, "rateDate": "2026-10-20", "currency": "TWD"} for y, v in eps.items()]}},
          "sales": {"url": "x", "payload": {"statusCode": 200, "message": "OK", "data": [{"financialYear": y, "feMedian": v * 1e5, "feLow": v * 0.9e5, "feMean": v * 1.01e5, "feHigh": v * 1.1e5, "feStdDev": 1.0, "feUp": 2, "feDown": 1, "numEst": 18, "rateDate": "2026-10-20", "currency": "TWD"} for y, v in eps.items()]}},
          "yfinance_info": {"ticker": "%s.TW" % code, "url": "https://finance.yahoo.com/quote/%s.TW/" % code, "captured_at_utc": "2026-10-29T02:00:00+00:00", "yfinance_version": "0.2.66",
                            "info": {"symbol": "%s.TW" % code, "shortName": name, "longName": name, "currency": "TWD", "currentPrice": last, "regularMarketPrice": last, "adjClose": last, "beta": 1.1, "targetLowPrice": yf_median * 0.85, "targetMeanPrice": yf_median * 1.01, "targetMedianPrice": yf_median, "targetHighPrice": yf_median * 1.15, "numberOfAnalystOpinions": 30, "recommendationMean": 1.6, "recommendationKey": "buy"},
                            "analysis": {}, "method_status": {}}}
    path.write_text(json.dumps(fx, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def selftest(engine: str | None = None) -> int:
    bad = []

    def chk(label, cond):
        say(("[PASS] " if cond else "[FAIL] ") + label)
        if not cond:
            bad.append(label)

    os.environ["VRN2_CONSENSUS_YEAR"] = "2026"
    chk("① 欄序照操作員清單:目標價 → 調整後目標價 → FactSet / YFinance 中位數 → 2026 / 2027 / 2028 EPS → 2026 / 2027 / 2028 PER → 現價 → 調整後上漲 → 還原收盤 → 主題與摘要 → 狀態",
        columns() == ["REPORT_DATE", "FILENAME", "TICKER", "YFINANCE_TICKER", "BLOOMBERG_TICKER", "NAME", "BROKER", "ANALYST", "RATING", "TARGET_PRICE", "TARGET_PRICE(ADJ)", "FACTSET_TARGET_PRICE_MEDIAN", "YFINANCE_TARGET_PRICE_MEDIAN",
                      "2026_DILUTED_EPS_FACTSET", "2027_DILUTED_EPS_FACTSET", "2028_DILUTED_EPS_FACTSET", "2026_PER_FACTSET", "2027_PER_FACTSET", "2028_PER_FACTSET", "CURRENT_PRICE_REPORT", "UPSIDE_PCT(ADJ)", "ADJ_CLOSE", "ADJ_CLOSE_BEFORE_REPORT", "TOPIC & SUMMARY", "STATUS"])
    eng = engine_path(None, engine)
    with tempfile.TemporaryDirectory(prefix="vrn2-cons-") as td:
        root = Path(td)
        v2 = root / "VIA_Reports" / "vrn2"
        (v2 / "output").mkdir(parents=True)
        (v2 / "market").mkdir()
        A, B, C = "CLSA-2330 20251001.pdf", "KGI-2454 20251002.pdf", "X-9999 20251003.pdf"
        json.dump([{"REPORT_DATE": "2025-10-01", "FILENAME": A, "TICKER": "2330", "YFINANCE_TICKER": "2330.TW", "BLOOMBERG_TICKER": "2330 TT", "NAME": "", "BROKER": "CLSA", "ANALYST": "A", "RATING": "BUY", "TARGET_PRICE": "1500", "CURRENT_PRICE_REPORT": "1000", "TITLE": "t1", "_STATUS": {"RATING": "首頁"}},
                   {"REPORT_DATE": "2025-10-02", "FILENAME": B, "TICKER": "2454", "YFINANCE_TICKER": "2454.TW", "BLOOMBERG_TICKER": "2454 TT", "NAME": "聯發科", "BROKER": "KGI", "ANALYST": "B", "RATING": "HOLD", "TARGET_PRICE": "1300", "CURRENT_PRICE_REPORT": "1200", "TITLE": "t2", "_STATUS": {}},
                   {"REPORT_DATE": "2025-10-03", "FILENAME": C, "TICKER": "9999", "BROKER": "X", "TARGET_PRICE": "", "TITLE": "t3", "_STATUS": {}}], open(v2 / "output" / "VRN2_BasicInfo_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
        json.dump([{"FILENAME": A, "TITLE": "台積電 重點", "POINT_1": "p1", "POINT_2": "p2", "POINT_3": "", "POINT_4": "p4"}], open(v2 / "output" / "VRN2_Summary_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
        json.dump({"per_file": {A: {"name": "台積電", "yfinance_ticker": "2330.TW", "adj_close": 1010.5, "adj_close_date": "2026-10-28", "adj_close_before_report": 990.0, "adjustment_factor_report": 0.98, "target_price_adj": 1470.0, "upside_pct_adj": 45.5},
                                B: {"name": "聯發科", "adj_close": 1250.0, "before_status": "MISSING(報告日前沒有日資料 · 需 --start 回補)"}}}, open(v2 / "market" / "VRN2_Market_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
        chk("② 代號來自基本資料冊:2330 · 2454 · 9999(去重 · 4 碼)", codes_from_basic(v2) == ["2330", "2454", "9999"])
        if not eng:
            say("[SKIP] 沒有共識引擎檔(同夾放 %s 或 --engine)· 跳過離線引擎實跑,只驗 join" % ENGINE_GLOB)
            r = {"lamp": "GRAY"}
        else:
            fx = [_fixture(root / "fx2330.json", "2330", "台積電", 1000.0, 1450.0, 1500.0, {2026: 60.0, 2027: 75.0, 2028: 90.0, 2025: 50.0}), _fixture(root / "fx2454.json", "2454", "聯發科", 1200.0, 1600.0, 1550.0, {2026: 70.0, 2027: 80.0}), _fixture(root / "fx9999.json", "9999", "測試", 10.0, 12.0, 11.0, {2026: 1.0})]
            r = run(v2, root, fixtures=fx, timeout=600)
            pc = r.get("per_code") or {}
            chk("③ 引擎離線 fixture 實跑:3 代號 · FactSet 中位數 1450 / 1600 · YFinance 中位數 1500 / 1550 · EPS 2026 60 · 2027 75 · 2028 90 · PER 2026 = 1000 / 60 · 收據在 consensus/",
                r.get("lamp") in ("GREEN", "YELLOW") and len(r.get("codes_got") or []) == 3 and pc.get("2330", {}).get("factset_target_median") == 1450.0 and pc.get("2454", {}).get("factset_target_median") == 1600.0 and pc.get("2330", {}).get("yf_target_median") == 1500.0 and pc.get("2454", {}).get("yf_target_median") == 1550.0
                and pc.get("2330", {}).get("eps_median", {}).get("2026") == 60.0 and pc.get("2330", {}).get("eps_median", {}).get("2028") == 90.0 and abs((pc.get("2330", {}).get("forward_pe", {}).get("2026") or 0) - 1000.0 / 60.0) < 1e-3 and (v2 / "consensus" / CONSENSUS_JSON).is_file())
            say("    引擎 rc %s · gate %s · %s" % (r.get("rc"), r.get("gate"), r.get("why")))
        j = join(v2)
        rows = json.loads((v2 / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))
        a, b, c = rows
        chk("④ join:3 列 · 欄序 = 清單 · 2330 調整後目標價 1470.00 · 上漲 45.5 · 還原收盤 1010.50 · NAME 由 VDF 補 · 主題與摘要 = 標題 + 三點(空點略)", len(rows) == 3 and list(a.keys()) == columns() and a["TARGET_PRICE(ADJ)"] == "1470.00" and a["UPSIDE_PCT(ADJ)"] == "45.5" and a["ADJ_CLOSE"] == "1010.50" and a["ADJ_CLOSE_BEFORE_REPORT"] == "990.00" and a["NAME"] == "台積電" and a["TOPIC & SUMMARY"] == "台積電 重點 · p1 · p2 · p4" and "NAME: VDF 清單" in a["STATUS"])
        if eng:
            chk("⑤ join 共識欄:2330 FactSet 1450.00 · YFinance 1500.00 · 2026 EPS 60.00 · 2028 EPS 90.00 · 2026 PER 16.67 · 2454 2028 空 · 9999 有共識但沒市場 → 調整後目標價空且說缺 · 綠 / 黃",
                a["FACTSET_TARGET_PRICE_MEDIAN"] == "1450.00" and a["YFINANCE_TARGET_PRICE_MEDIAN"] == "1500.00" and a["2026_DILUTED_EPS_FACTSET"] == "60.00" and a["2028_DILUTED_EPS_FACTSET"] == "90.00" and a["2026_PER_FACTSET"] == "16.67" and b["2028_DILUTED_EPS_FACTSET"] == "" and b["TARGET_PRICE(ADJ)"] == "" and "缺:MISSING(報告日前沒有日資料" in b["STATUS"] and c["FACTSET_TARGET_PRICE_MEDIAN"] == "12.00" and "沒有市場資料" in c["STATUS"] and j["lamp"] in ("GREEN", "YELLOW") and "FactSet(鉅亨)20 位" in a["STATUS"])
        else:
            chk("⑤ join 沒有共識資料:欄位存在但空 · STATUS 說缺 · 黃", a["FACTSET_TARGET_PRICE_MEDIAN"] == "" and "缺:" in a["STATUS"] and j["lamp"] == "YELLOW")
        chk("⑥ 輸出:json / csv(+ parquet 有 pyarrow)· 基本資料冊沒動(3 列 · _STATUS 還在)", (v2 / "output" / "VRN2_Combined_latest.csv").is_file() and len(json.loads((v2 / "output" / "VRN2_BasicInfo_latest.json").read_text(encoding="utf-8"))) == 3 and "_STATUS" in json.loads((v2 / "output" / "VRN2_BasicInfo_latest.json").read_text(encoding="utf-8"))[0])
        os.environ["VIA_VRN2_NO_CONSENSUS"] = "1"
        r2 = run(v2, root)
        os.environ.pop("VIA_VRN2_NO_CONSENSUS", None)
        chk("⑦ VIA_VRN2_NO_CONSENSUS=1 → 灰不跑 · 收據照寫", r2["lamp"] == "GRAY" and "不抓共識" in r2["why"] and (v2 / "consensus" / CONSENSUS_JSON).is_file())
    os.environ.pop("VRN2_CONSENSUS_YEAR", None)
    say("[%s] %s %s --selftest · 7 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest(opt("--engine"))
    verb = argv[0] if argv else ""
    if verb not in ("run", "join"):
        say(__doc__)
        return 2
    v2 = Path(opt("--v2") or (Path(os.environ["VIA_ROOT"]) / "VIA_Reports" / "vrn2" if os.environ.get("VIA_ROOT") else HERE.parent.parent / "VIA_Reports" / "vrn2"))
    root = Path(opt("--root")) if opt("--root") else (v2.parent.parent if v2.name == "vrn2" else None)
    if verb == "run":
        fixtures = [argv[i + 1] for i, a in enumerate(argv) if a == "--fixture" and i + 1 < len(argv)]
        r = run(v2, root, fixtures or None, int(opt("--timeout", "900")), opt("--engine"))
    else:
        r = join(v2)
    say("[%s] %s · %s · %s" % (r.get("lamp"), TAG, verb, r.get("why")))
    return 0 if r.get("lamp") in ("GREEN", "YELLOW", "GRAY") else 1


if __name__ == "__main__":
    sys.exit(main())
