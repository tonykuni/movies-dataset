#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG082_FinStatements v0100 — 三大報表擷取引擎(批505;填主控台冊 vdf/fin_statements「缺席」空位)
====================================================================
操作員上傳 vdf_fetchers_financials.py(收容 VDF/references/intake/vdf_fetchers_financials_b504;正本零觸碰)。
它直呼 requests/yfinance,批494 律:網路只認 VeritasAegisNexus。本引擎**只掛不搬**:
  · 同意閘:SUP_MDL740 NetUnified gate_state()(法遵雙閘 VIA_NET_CONSENT + VIA_SCRAPE_CONSENT;fail-closed;永不代設)
  · MOPS 車道:走 NetUnified http_text(AegisNexus 車道)只**探路**(可達/長度入台帳);解析=候(收容件自己也寫「TODO/brittle」)
  · yfinance 車道:收容件 _fin_from_yfinance(canonical schema tw_financial 23 欄),Ticker 以 AegisNexus ResilientHTTPClient session
    注入(yfinance 若拒絕該 session 型別=退原生,tag 講明);yfinance 缺席=[缺件] 誠實停 rc2(裝=你的手)
  · 落地:DuckDB 表 tw_financial(派生層:同 Ticker DELETE+INSERT,冪等)+ parquet(duckdb COPY,零 pyarrow 相依)於 output_hub/mega/fin/
  · 庫找法:--db > env VIA_DB_VDF_TW_MARKET > VIA_DATA_HOME 內最新 vdf_tw_market.duckdb > output_hub/mega
用法:python3 VDF_ENG082_FinStatements_v0100.py run [--only 2330,2317] [--limit 5] [--years 5] [--db PATH] [--dry]
      | status [--db PATH] | --selftest
律:只增不減;誠實三態(GATED/ABSENT/NODATA/GREEN);零 CDN;閘不代設;自測零網路零污染(暫存庫)。
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
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"
INTAKE = VDF / "references" / "intake"
TABLE = "tw_financial"
VERSION = "0100"
MOPS_PROBE = "https://mops.twse.com.tw/mops/web/t164sb04"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def fetcher():
    """收容件尾版(vdf_fetchers_financials_b*/vdf_fetchers_financials.py);缺=None(誠實)。"""
    hits = sorted(INTAKE.glob("vdf_fetchers_financials_b*/vdf_fetchers_financials.py"))
    if not hits:
        return None
    try:
        return _load("vdf_fetchers_financials_intake", hits[-1])
    except Exception:
        return None


def net():
    """NetUnified(via_net_unified_v*.py → SUP_MDL740 正典);缺=None。"""
    hits = sorted((VIA / "supportive modules" / "network").glob("via_net_unified_v*.py"))
    if not hits:
        return None
    try:
        return _load("via_net_for_eng082", hits[-1])
    except Exception:
        return None


def gate_open() -> tuple:
    n = net()
    if n is None or not hasattr(n, "gate_state"):
        env = os.environ
        return (env.get("VIA_NET_CONSENT") == "YES" and bool(env.get("VIA_SCRAPE_CONSENT"))), "NetUnified 缺;退 env 直讀"
    g = n.gate_state()
    return bool(g.get("open")), f"gate1 {g.get('gate1_raw')} · gate2 {'set' if g.get('gate2_scrape_token_set') else '(未設)'}"


def aegis_session():
    """AegisNexus ResilientHTTPClient 的 requests session(給 yfinance 注入);缺=None + why。"""
    p = VIA / "supportive modules" / "network" / "VeritasAegisNexus.py"
    if not p.is_file():
        return None, "VeritasAegisNexus.py 缺"
    try:
        m = _load("via_aegis_for_eng082", p)
        cli = m.ResilientHTTPClient()
        s = cli._get_session()
        return s, f"AegisNexus session {type(s).__name__}"
    except Exception as exc:
        return None, f"AegisNexus session 取不到 {type(exc).__name__}:{str(exc)[:50]}"


def columns() -> list:
    f = fetcher()
    if f is None:
        return ["Date", "Ticker", "Period", "Period_Type", "Revenue", "Gross_Profit", "Operating_Income", "Net_Income", "EPS", "Total_Assets",
                "Total_Liabilities", "Equity", "Operating_CF", "Investing_CF", "Financing_CF", "Free_CF", "ROE", "ROA", "Gross_Margin",
                "Operating_Margin", "Net_Margin", "Debt_To_Equity", "Source"]
    return list(f._new_row("", "", "", "").keys())


def norm_ticker(t: str) -> str:
    """2330 → 2330.TW;2330.TWO/AAPL 照原;四碼台股預設上市(.TW),回空=.TWO 再試由 run 決定。"""
    t = str(t or "").strip().upper()
    if not t:
        return ""
    if t.isdigit() and len(t) == 4:
        return t + ".TW"
    return t


def _resolve_db(explicit: str | None):
    if explicit:
        return Path(explicit)
    e = os.environ.get("VIA_DB_VDF_TW_MARKET")
    if e and Path(e).is_file():
        return Path(e)
    home = os.environ.get("VIA_DATA_HOME")
    if home and Path(home).is_dir():
        c = sorted((q for q in Path(home).rglob("vdf_tw_market.duckdb") if "/_self_test" not in str(q).replace("\\", "/")), key=lambda q: q.stat().st_mtime)
        if c:
            return c[-1]
    p = OUT / "vdf_tw_market.duckdb"
    return p if p.is_file() else None


def listings(con, limit: int) -> list:
    try:
        rows = con.execute("SELECT code FROM tw_listings WHERE code IS NOT NULL ORDER BY code LIMIT ?", [int(limit)]).fetchall()
        return [str(r[0]) for r in rows]
    except Exception:
        return []


def _pull(ticker: str, years: int) -> tuple:
    """yfinance 車道(收容件 _fin_from_yfinance;AegisNexus session 注入);回 (rows, tag)。零快取、零假抽。"""
    f = fetcher()
    if f is None:
        return [], "ABSENT(收容件 vdf_fetchers_financials 缺)"
    try:
        import yfinance as yf
    except Exception as exc:
        return [], f"缺件 No module named 'yfinance'({type(exc).__name__};via-envtools 排裝,裝=你的手)"
    sess, why = aegis_session()
    orig = yf.Ticker
    tag = why
    if sess is not None:
        try:
            import functools
            yf.Ticker = functools.partial(orig, session=sess)      # 網路走 AegisNexus session
        except Exception:
            tag = "AegisNexus session 注入失敗→原生"
    try:
        rows = list(f._fin_from_yfinance(ticker))
    except TypeError as exc:                                     # 新版 yfinance 拒收 requests.Session(要 curl_cffi)
        yf.Ticker = orig
        tag = f"yfinance 拒收 AegisNexus session({str(exc)[:40]})→原生"
        try:
            rows = list(f._fin_from_yfinance(ticker))
        except Exception as exc2:
            return [], f"RUN_FAIL {type(exc2).__name__}:{str(exc2)[:60]}"
    except Exception as exc:
        return [], f"RUN_FAIL {type(exc).__name__}:{str(exc)[:60]}"
    finally:
        yf.Ticker = orig
    cutoff = f"{datetime.now().year - int(years)}-01-01"
    rows = [r for r in rows if str(r.get("Period", "")) >= cutoff]
    return rows, tag


def write_rows(con, rows: list, cols: list) -> int:
    con.execute("CREATE TABLE IF NOT EXISTS " + TABLE + " (" + ", ".join(f'"{c}" ' + ("VARCHAR" if c in ("Date", "Ticker", "Period", "Period_Type", "Source") else "DOUBLE") for c in cols)
                + ", fetched_at VARCHAR)")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tickers = sorted({r.get("Ticker") for r in rows if r.get("Ticker")})
    for t in tickers:
        con.execute(f"DELETE FROM {TABLE} WHERE Ticker = ?", [t])          # 派生層重算:同 Ticker 重寫
    ph = ",".join("?" for _ in cols) + ",?"
    for r in rows:
        con.execute(f"INSERT INTO {TABLE} VALUES ({ph})", [r.get(c) for c in cols] + [now])
    return len(rows)


def mops_probe(code: str) -> dict:
    """MOPS 探路(AegisNexus 車道;只記可達/長度;解析=候)。閘未開=DENIED 誠實。"""
    n = net()
    if n is None or not hasattr(n, "http_text"):
        return {"state": "ABSENT", "why": "NetUnified 缺"}
    try:
        r = n.http_text(MOPS_PROBE, timeout=20)
        return {"state": r.get("state", "?"), "len": len(str(r.get("data") or "")), "via": r.get("via", ""), "why": str(r.get("why") or r.get("reason") or "")[:80]}
    except Exception as exc:
        return {"state": "FAIL", "why": f"{type(exc).__name__}:{str(exc)[:60]}"}


def run(only: list | None, limit: int, years: int, db: str | None, dry: bool) -> int:
    ok, gwhy = gate_open()
    print(f"[三大報表] VDF_ENG082 v{VERSION} · 收容件 {'在' if fetcher() else '缺'} · 閘 {gwhy}")
    dbp = _resolve_db(db)
    if dbp is None:
        print("[庫缺] vdf_tw_market.duckdb 不在(env VIA_DB_VDF_TW_MARKET / VIA_DATA_HOME / output_hub/mega 皆無)=誠實停 rc2")
        return 2
    import duckdb
    con = duckdb.connect(str(dbp))
    try:
        codes = [c for c in (only or []) if c] or listings(con, limit)
        tickers = [norm_ticker(c) for c in codes if norm_ticker(c)]
        print(f"  庫 {dbp} · 目標 {len(tickers)} 檔:{','.join(tickers[:8])}{'…' if len(tickers) > 8 else ''} · 年數 {years}")
        if not tickers:
            print("  [缺料] 無目標(tw_listings 無列且未給 --only)=誠實停 rc2")
            return 2
        if dry:
            print("  [DRY] 只列不抓(不碰網路、不寫庫)")
            return 0
        if not ok:
            print("[FAIL-CLOSED] 同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT)=拒跑;閘由你自己設,我不代設")
            return 2
        cols = columns()
        tot, tags, empty = 0, {}, []
        for i, t in enumerate(tickers, 1):
            rows, tag = _pull(t, years)
            if not rows and t.endswith(".TW"):
                rows2, tag2 = _pull(t[:-3] + ".TWO", years)      # 上櫃再試
                if rows2:
                    rows, tag = rows2, tag2 + "(上櫃 .TWO)"
            if tag.startswith("缺件") or tag.startswith("ABSENT"):
                print(f"  [{tag}]")
                return 2
            tags[tag] = tags.get(tag, 0) + 1
            if rows:
                tot += write_rows(con, rows, cols)
                print(f"  [{i}/{len(tickers)}] {t} +{len(rows)} 列")
            else:
                empty.append(t)
                print(f"  [{i}/{len(tickers)}] {t} 零列({tag[:60]})")
            time.sleep(0.3)
        n = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
        pq = OUT / "fin"
        pq.mkdir(parents=True, exist_ok=True)
        pqf = pq / f"{TABLE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        try:
            con.execute(f"COPY (SELECT * FROM {TABLE}) TO '{pqf.as_posix()}' (FORMAT PARQUET)")
        except Exception as exc:
            pqf = f"parquet 未寫 {type(exc).__name__}"
        mp = mops_probe(tickers[0].split(".")[0])
        print(f"  [MOPS 探路] {mp.get('state')} · {mp.get('why') or ('len ' + str(mp.get('len')))} · 解析=候(VERIFY_PENDING)")
        print(f"[三大報表計] {len(tickers)} 檔 · +{tot} 列 · 零列 {len(empty)} · 表 {TABLE} 共 {n:,} 列 · parquet {pqf} · 車道 {tags}")
        return 0 if tot else 2
    finally:
        con.close()


def status(db: str | None) -> int:
    dbp = _resolve_db(db)
    print(f"[三大報表] VDF_ENG082 v{VERSION} · 收容件 {'在' if fetcher() else '缺'} · 閘 {gate_open()[1]} · 庫 {dbp or '缺'}")
    if dbp is None:
        return 2
    import duckdb
    try:
        con = duckdb.connect(str(dbp), read_only=True)
    except Exception as exc:
        print(f"  庫忙/壞:{str(exc)[:80]}")
        return 2
    try:
        n = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
        by = con.execute(f"SELECT Ticker, COUNT(*), MAX(Period) FROM {TABLE} GROUP BY 1 ORDER BY 1 LIMIT 12").fetchall()
        print(f"  {TABLE} {n:,} 列 · " + " · ".join(f"{t} {c}({p})" for t, c, p in by))
    except Exception:
        print(f"  {TABLE} 未建(先 run;閘要你開)")
    finally:
        con.close()
    return 0


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    f = fetcher()
    cols = columns()
    chk("① 收容件掛載(vdf_fetchers_financials_b*;canonical 23 欄 Date…Source)", f is not None and len(cols) == 23 and cols[0] == "Date" and cols[-1] == "Source", f"({len(cols)} 欄)")
    chk("② 代號正規:2330→2330.TW · 2330.TWO 照原 · AAPL 照原 · 空=空", norm_ticker("2330") == "2330.TW" and norm_ticker("2330.two") == "2330.TWO" and norm_ticker("aapl") == "AAPL" and norm_ticker("") == "")
    sv = {k: os.environ.get(k) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT", "VIA_DB_VDF_TW_MARKET", "VIA_DATA_HOME")}
    with tempfile.TemporaryDirectory() as td:
        try:
            import duckdb
            dbp = Path(td) / "t.duckdb"
            con = duckdb.connect(str(dbp)); con.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR)"); con.execute("INSERT INTO tw_listings VALUES ('2330','台積電'),('2317','鴻海')"); con.close()
            os.environ.pop("VIA_NET_CONSENT", None); os.environ.pop("VIA_SCRAPE_CONSENT", None)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = run(None, 5, 5, str(dbp), False)
            chk("③ 同意閘 fail-closed:閘未開 → 印 [FAIL-CLOSED] 同意閘未開 · rc2(匯流排判 GATED,不是壞)", rc == 2 and "[FAIL-CLOSED] 同意閘未開" in buf.getvalue())
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc_d = run(["2330"], 5, 5, str(dbp), True)
            chk("④ --dry 只列不抓不寫(閘未開也能列目標)", rc_d == 0 and "[DRY]" in buf.getvalue() and "2330.TW" in buf.getvalue())
            # ⑤ 端到端(假車道):monkeypatch _pull → 合成列;寫表 + 冪等 + parquet(duckdb COPY)
            g = globals()
            real_pull, real_probe = g["_pull"], g["mops_probe"]
            g["_pull"] = lambda t, y: ([dict(f._new_row(t, "2024-12-31", "annual", "selftest"), Revenue=100.0, Gross_Profit=40.0, Net_Income=10.0, Equity=50.0),
                                        dict(f._new_row(t, "2023-12-31", "annual", "selftest"), Revenue=90.0)], "fake-lane")
            g["mops_probe"] = lambda c: {"state": "SKIP", "why": "selftest 零網路"}
            os.environ["VIA_NET_CONSENT"] = "YES"; os.environ["VIA_SCRAPE_CONSENT"] = "x"
            _out = g["OUT"]; g["OUT"] = Path(td) / "mega"
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc1 = run(["2330", "2317"], 5, 5, str(dbp), False)
                    rc2 = run(["2330", "2317"], 5, 5, str(dbp), False)
                con = duckdb.connect(str(dbp), read_only=True)
                n = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
                tk = con.execute(f"SELECT COUNT(DISTINCT Ticker) FROM {TABLE}").fetchone()[0]
                ncol = len(con.execute(f"SELECT * FROM {TABLE} LIMIT 0").description)
                con.close()
                pqs = list((Path(td) / "mega" / "fin").glob("tw_financial_*.parquet"))
                chk("⑤ 端到端(假車道):2 檔 × 2 期 → 4 列、23+1 欄、重跑冪等(同 Ticker DELETE+INSERT 不倍增)、parquet 由 duckdb COPY 落 mega/fin(零 pyarrow)",
                    rc1 == 0 and rc2 == 0 and n == 4 and tk == 2 and ncol == 24 and len(pqs) >= 1, f"(列 {n} · 檔 {tk} · 欄 {ncol} · parquet {len(pqs)})")
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc_s = status(str(dbp))
                chk("⑥ status 讀得出表(列數/逐檔最新期)", rc_s == 0 and "tw_financial 4 列" in buf.getvalue() and "2330.TW 2(2024-12-31)" in buf.getvalue(), f"({buf.getvalue().splitlines()[-1][:80]})")
            finally:
                g["_pull"], g["mops_probe"], g["OUT"] = real_pull, real_probe, _out
        except ImportError:
            chk("③④⑤⑥ 端到端(本環境無 duckdb=SKIP 誠實)", True)
        finally:
            for k, v in sv.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 零直呼網路(無 import requests/httpx/yfinance 於模組頂層;yfinance 只在車道內惰性 import;MOPS 走 NetUnified http_text)",
        all(("\nimport " + k) not in src for k in ("requests", "httpx", "yfinance")) and "http_text(" in src and "gate_state()" in src)
    ok, why = gate_open()
    chk("⑧ 閘態讀自 NetUnified gate_state(永不代設;本容器應為關)", isinstance(ok, bool) and bool(why), f"({ok} · {why[:50]})")
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _argval(args, flag, default=None):
    if flag in args:
        i = args.index(flag) + 1
        if i < len(args) and not args[i].startswith("--"):
            return args[i]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print(f"=== 三大報表擷取引擎(VDF_ENG082 v{VERSION})· 八檢自測(零網路;暫存庫)===")
        return selftest()
    db = _argval(a, "--db")
    if a and a[0] == "run":
        only = [x.strip() for x in str(_argval(a, "--only", "")).split(",") if x.strip()]
        return run(only or None, int(_argval(a, "--limit", 5)), int(_argval(a, "--years", 5)), db, "--dry" in a)
    if a and a[0] == "status":
        return status(db)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
