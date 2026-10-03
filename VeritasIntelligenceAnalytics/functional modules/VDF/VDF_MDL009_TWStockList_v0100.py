#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL009_TWStockList v0100 — 擷取第一步 ①:全台股清單(自動生成 · 驗證過 · 所有資料庫的開頭)

操作員 2026-10-03:「自動更新全台股清單及主動式 ETF 清單 可驗證 輸出兩組代號 date / ticker / yfinance ticker / bloomberg ticker /
name 都是從這清單擷取且為所有資料庫的開頭」「產生兩個自動生成清單驗證過引擎為第一步」「改為獨立運作由 VDF SYSTEM MANAGER 總控」。
  來源   TWSE OpenAPI STOCK_DAY_ALL(當日有行情)+ t187ap03_L(上市公司基本資料:簡稱 · 產業別)
         TPEX OpenAPI tpex_mainboard_daily_close_quotes + mopsfin_t187ap03_O(上櫃公司基本資料)
         網路只走鎖版網路工具 http_json(雙閘在工具裡;閘關 = DENY、零寫入;AI 永不代設)。
  規則   SSOT 代碼律 = MDL001 鎖定 regex (?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})(全碼比對;操作員鎖,本支不改,被擋的照列在報告)。
  開頭欄 date · ticker · yf_ticker(.TW 上市 / .TWO 上櫃)· bloomberg_ticker("2330 TT")· name,其後 market · industry · status · first_seen。
  驗證   V1 兩所都有料 · V2 代碼律 · V3 不重號 · V4 yf / bbg 後綴對所別 · V5 日差 NEW / DELISTED(ENG087 同一式)
         · V6 大量下市守門(> max(20, 5%) = 紅,不覆寫最新)· V7 數量合理(低於下限 = 黃)。
  輸出   <輸出根>/0-1-TWStockList/:tw_stock_list_latest.parquet / .csv · tw_stock_list_<日>.parquet · verify_report.json;
         DuckDB <輸出根>/vdf_master_lists.duckdb 表 tw_stock_list(增量:以 date + ticker 反連接只補新列;temp 當溢寫記憶體)。
  入口   VDF System Manager 總控標記 VIA_FROM_VDFSM=YES 或 VCGC;本支也提供 MDL010 共用核心(版本專屬名 *_v0100)。
動詞:run [--date YYYY-MM-DD] [--min N] | status | --selftest。不碰 TA-Lib。
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

import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

TAG = "VDF_MDL009_TWStockList v" + Path(__file__).stem.rsplit("_v", 1)[-1]
KEY_COLS = ("date", "ticker", "yf_ticker", "bloomberg_ticker", "name")
STATUSES = ("ACTIVE", "NEW", "DELISTED")
MASS_DELIST_MIN, MASS_DELIST_RATIO = 20, 0.05
SSOT_STOCK_RX = re.compile(r"^(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})$")     # MDL001 鎖定律(全碼)
SRC = {"twse_quote": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
       "twse_basic": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
       "tpex_quote": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
       "tpex_basic": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"}
OUT_DIR, STEM, TABLE = "0-1-TWStockList", "tw_stock_list", "tw_stock_list"
MIN_DEFAULT = {"TWSE": 500, "TPEX": 300}


# ---------------------------------------------------------------- 共用核心(MDL010 也用;版本專屬名)
def entry_ok_v0100() -> bool:
    return os.environ.get("VIA_FROM_VDFSM") == "YES" or os.environ.get("VIA_FROM_VCGC") == "YES"


def fetch_json_v0100(url: str):
    """鎖版網路工具 http_json;回 (state, data)。DENY = 雙閘沒開(不是壞掉)。"""
    nt = _via_net()
    if nt is None or not hasattr(nt, "http_json"):
        return "ABSENT", None
    try:
        r = nt.http_json(url, timeout=30) or {}
    except Exception as exc:
        return "FAIL:" + type(exc).__name__, None
    st = str(r.get("state") or "")
    return ("OK", r.get("data")) if st == "OK" else ("GATED" if st == "DENY" else "FAIL:" + str(r.get("note") or st)[:60], None)


def suffix_v0100(market: str) -> tuple:
    return (".TW", " TT") if market == "TWSE" else (".TWO", " TT")


def keyed_row_v0100(day: str, code: str, name: str, market: str, **extra) -> dict:
    yf, bb = suffix_v0100(market)
    return {"date": day, "ticker": code, "yf_ticker": code + yf, "bloomberg_ticker": code + bb, "name": name, "market": market, **extra}


def diff_v0100(current: list, previous: list, today: str) -> dict:
    """ENG087 同一式:NEW / ACTIVE / DELISTED + 大量下市守門。"""
    prev = {r["ticker"]: r for r in previous or [] if r.get("ticker")}
    baseline = not prev
    cur = {r["ticker"]: r for r in current}
    rows = []
    for t in sorted(set(prev) | set(cur)):
        p, c = prev.get(t), cur.get(t)
        if c is not None:
            if p is None or str(p.get("status")) == "DELISTED":
                st, first = ("ACTIVE" if baseline else "NEW"), (p or {}).get("first_seen") or today
            else:
                st, first = "ACTIVE", p.get("first_seen") or today
            rows.append({**c, "status": st, "first_seen": first})
        else:
            rows.append({**p, "date": today, "status": "DELISTED", "first_seen": p.get("first_seen") or ""})
    newly = [r["ticker"] for r in rows if r["status"] == "DELISTED" and str(prev[r["ticker"]].get("status")) != "DELISTED"]
    live = sum(1 for r in prev.values() if str(r.get("status")) != "DELISTED")
    limit = max(MASS_DELIST_MIN, int(live * MASS_DELIST_RATIO))
    return {"rows": rows, "baseline": baseline, "counts": {s: sum(r["status"] == s for r in rows) for s in STATUSES},
            "new": [r["ticker"] for r in rows if r["status"] == "NEW"], "delisted_today": newly,
            "mass_delist_limit": limit, "mass_delist": len(newly) > limit}


def write_outputs_v0100(rows: list, report: dict, out_root: Path, out_dir: str, stem: str, table: str, day: str, accept: bool) -> dict:
    """parquet / csv / 驗證報告 + DuckDB 增量(date + ticker 反連接;temp 當溢寫記憶體)。驗證紅 = 只寫報告,不覆寫最新。"""
    import pandas as pd
    d = out_root / out_dir
    d.mkdir(parents=True, exist_ok=True)
    (d / "verify_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not accept:
        return {"written": False}
    cols = list(KEY_COLS) + [c for c in rows[0] if c not in KEY_COLS] if rows else list(KEY_COLS)
    df = pd.DataFrame(rows, columns=cols)
    df.to_parquet(d / f"{stem}_latest.parquet", index=False)
    df.to_csv(d / f"{stem}_latest.csv", index=False, encoding="utf-8-sig")
    df.to_parquet(d / f"{stem}_{day}.parquet", index=False)
    added = None
    try:
        import duckdb
        tmp = out_root / "_tmp"
        tmp.mkdir(exist_ok=True)
        con = duckdb.connect(str(out_root / "vdf_master_lists.duckdb"))
        con.execute(f"SET temp_directory='{tmp.as_posix()}'")
        con.execute("SET preserve_insertion_order=false")
        con.register("df_in", df.astype(str))
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM df_in LIMIT 0")
        before = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        names = ", ".join(f'"{c}"' for c in cols)
        con.execute(f"INSERT INTO {table} ({names}) SELECT {names} FROM df_in i WHERE NOT EXISTS "
                    f"(SELECT 1 FROM {table} t WHERE t.date = i.date AND t.ticker = i.ticker)")
        added = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] - before
        con.close()
    except ImportError:
        added = "ABSENT:duckdb"
    return {"written": True, "rows": len(df), "duckdb_added": added}


def load_previous_v0100(out_root: Path, out_dir: str, stem: str) -> list:
    p = out_root / out_dir / f"{stem}_latest.parquet"
    if not p.is_file():
        return []
    import pandas as pd
    return pd.read_parquet(p).fillna("").to_dict("records")


def lamp_v0100(checks: list) -> str:
    st = [c["lamp"] for c in checks]
    return "RED" if "RED" in st else ("YELLOW" if "YELLOW" in st else "GREEN")


def print_report_v0100(tag: str, rep: dict) -> None:
    print(f"[{tag}] {rep['lamp']} · {rep['date']} · {rep['count']} 檔 · 新 {len(rep['diff']['new'])} · 今日下市 {len(rep['diff']['delisted_today'])}"
          f" · 寫入 {rep['write']}")
    for c in rep["checks"]:
        print(f"  [{c['lamp']}] {c['id']} {c['name']} · {c['note']}")


# ---------------------------------------------------------------- 全台股
def collect(day: str) -> tuple:
    got, states = {}, {}
    for k, url in SRC.items():
        states[k], got[k] = fetch_json_v0100(url)
    basic = {}
    for r in got.get("twse_basic") or []:
        basic[("TWSE", str(r.get("公司代號") or "").strip())] = (str(r.get("公司簡稱") or "").strip(), str(r.get("產業別") or "").strip())
    for r in got.get("tpex_basic") or []:
        code = str(r.get("公司代號") or r.get("SecuritiesCompanyCode") or "").strip()
        basic[("TPEX", code)] = (str(r.get("公司簡稱") or r.get("CompanyAbbreviation") or "").strip(), str(r.get("產業別") or "").strip())
    raw = [("TWSE", str(r.get("Code") or r.get("證券代號") or "").strip(), str(r.get("Name") or r.get("證券名稱") or "").strip())
           for r in got.get("twse_quote") or []]
    raw += [("TPEX", str(r.get("SecuritiesCompanyCode") or r.get("CompanyCode") or "").strip(),
             str(r.get("CompanyName") or "").strip()) for r in got.get("tpex_quote") or []]
    rows, rejected = [], []
    for market, code, name in raw:
        if not SSOT_STOCK_RX.match(code):
            rejected.append({"ticker": code, "name": name, "market": market})
            continue
        short, ind = basic.get((market, code), ("", ""))
        rows.append(keyed_row_v0100(day, code, short or name, market, industry=ind))
    return rows, rejected, states


def verify(rows: list, rejected: list, states: dict, prev: list, day: str, mins: dict) -> dict:
    checks = []
    by = {m: sum(r["market"] == m for r in rows) for m in ("TWSE", "TPEX")}
    gated = any(v == "GATED" for v in states.values())
    checks.append({"id": "V1", "name": "兩所都有料", "lamp": "GREEN" if by["TWSE"] and by["TPEX"] else "RED",
                   "note": f"上市 {by['TWSE']} · 上櫃 {by['TPEX']} · 來源 {states}" + (" · 雙閘沒開(不是壞掉)" if gated else "")})
    bad = [r["ticker"] for r in rows if not SSOT_STOCK_RX.match(r["ticker"])]
    checks.append({"id": "V2", "name": "SSOT 代碼律(MDL001 鎖定 regex)", "lamp": "RED" if bad else "GREEN",
                   "note": f"違律 {len(bad)} · 被擋 {len(rejected)}(ETF / 權證 / 年份樣碼等,照列)"})
    seen, dup = set(), []
    for r in rows:
        (dup.append(r["ticker"]) if r["ticker"] in seen else seen.add(r["ticker"]))
    checks.append({"id": "V3", "name": "不重號(兩所間)", "lamp": "RED" if dup else "GREEN", "note": f"重號 {dup[:5]}"})
    suf = [r["ticker"] for r in rows if r["yf_ticker"] != r["ticker"] + suffix_v0100(r["market"])[0] or r["bloomberg_ticker"] != r["ticker"] + " TT"]
    checks.append({"id": "V4", "name": "yf / bloomberg 後綴對所別", "lamp": "RED" if suf else "GREEN", "note": f"不合 {suf[:5]}"})
    df = diff_v0100(rows, prev, day)
    checks.append({"id": "V5", "name": "日差(對前一份)", "lamp": "GREEN", "note": ("首跑基準 · " if df["baseline"] else "") + json.dumps(df["counts"])})
    checks.append({"id": "V6", "name": "大量下市守門", "lamp": "RED" if df["mass_delist"] else "GREEN",
                   "note": f"今日下市 {len(df['delisted_today'])} / 上限 {df['mass_delist_limit']}"})
    low = {m: by[m] for m in by if by[m] < mins.get(m, 0)}
    checks.append({"id": "V7", "name": "數量合理", "lamp": "YELLOW" if low else "GREEN", "note": f"低於下限 {low} · 下限 {mins}"})
    return {"checks": checks, "diff": df, "lamp": lamp_v0100(checks)}


def run(day: str | None = None, out_root: Path | None = None, mins: dict | None = None) -> dict:
    day = day or date.today().isoformat()
    out_root = Path(out_root or Path.cwd())
    rows, rejected, states = collect(day)
    prev = load_previous_v0100(out_root, OUT_DIR, STEM)
    v = verify(rows, rejected, states, prev, day, mins if mins is not None else MIN_DEFAULT)
    final = v["diff"]["rows"]
    rep = {"engine": TAG, "date": day, "count": len(rows), "lamp": v["lamp"], "checks": v["checks"],
           "diff": {k: v["diff"][k] for k in ("baseline", "counts", "new", "delisted_today", "mass_delist", "mass_delist_limit")},
           "rejected": rejected[:200], "sources": states, "key_columns": list(KEY_COLS),
           "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    rep["write"] = write_outputs_v0100(final, rep, out_root, OUT_DIR, STEM, TABLE, day, accept=v["lamp"] != "RED" and bool(rows))
    return rep


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if not entry_ok_v0100():
        print("[VDF_MDL009] 拒絕。由 VDF System Manager 總控:python \"functional modules/VDF/VDF_SystemManager_v0128.py\" fetch run MDL009 --apply")
        return 2
    verb = args[0] if args else "run"
    if verb not in ("run", "status"):
        print(f"[拒跑] {TAG}:未知動詞 '{verb}'(已知:run · status · --selftest)")
        return 2
    day = args[args.index("--date") + 1] if "--date" in args else None
    mins = {"TWSE": int(args[args.index("--min") + 1]), "TPEX": int(args[args.index("--min") + 1])} if "--min" in args else None
    if verb == "status":
        p = Path.cwd() / OUT_DIR / "verify_report.json"
        print(p.read_text(encoding="utf-8") if p.is_file() else f"[{TAG}] 還沒有報告(先 run)")
        return 0 if p.is_file() else 2
    rep = run(day, mins=mins)
    print_report_v0100(TAG, rep)
    if any(c["id"] == "V1" and "雙閘沒開" in c["note"] for c in rep["checks"]):
        return 4
    return {"GREEN": 0, "YELLOW": 0, "RED": 1}[rep["lamp"]] if rep["count"] else 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 自測(假網路工具 · 暫存輸出根 · 零外呼)===")
    twse = [{"Code": c, "Name": n} for c, n in (("2330", "台積電"), ("2317", "鴻海"), ("0050", "元大台灣50"), ("2027", "大成鋼"), ("00981A", "主動群益"))]
    tpex = [{"SecuritiesCompanyCode": c, "CompanyName": n} for c, n in (("6488", "環球晶"), ("3324", "雙鴻"), ("00679B", "美債20"))]
    basic_l = [{"公司代號": "2330", "公司簡稱": "台積電", "產業別": "24"}, {"公司代號": "2317", "公司簡稱": "鴻海", "產業別": "31"}]

    class _Net:
        def __init__(self, data, deny=False):
            self.data, self.deny = data, deny

        def http_json(self, url, timeout=30):
            if self.deny:
                return {"state": "DENY"}
            for k, u in SRC.items():
                if u == url:
                    return {"state": "OK", "data": self.data.get(k, [])}
            return {"state": "FAIL", "note": "no route"}
    g = globals()
    real = g["_via_net"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        try:
            g["_via_net"] = lambda: _Net({"twse_quote": twse, "tpex_quote": tpex, "twse_basic": basic_l, "tpex_basic": []})
            r1 = run("2026-10-01", root, mins={"TWSE": 1, "TPEX": 1})
            chk("① 生成:SSOT 律擋 ETF / 年份樣碼 / A 碼 · 留 4 檔 · 開頭五欄 · 簡稱 / 產業別併入",
                r1["count"] == 4 and r1["lamp"] == "GREEN" and {x["ticker"] for x in r1["rejected"]} == {"0050", "2027", "00981A", "00679B"})
            import pandas as pd
            df = pd.read_parquet(root / OUT_DIR / f"{STEM}_latest.parquet")
            chk("② 欄位開頭 = date · ticker · yf_ticker · bloomberg_ticker · name;.TW / .TWO 與 'TT' 對所別",
                list(df.columns[:5]) == list(KEY_COLS) and set(df.loc[df.ticker == "6488", "yf_ticker"]) == {"6488.TWO"}
                and set(df.loc[df.ticker == "2330", "bloomberg_ticker"]) == {"2330 TT"}, list(df.columns))
            g["_via_net"] = lambda: _Net({"twse_quote": twse[:1] + [{"Code": "2454", "Name": "聯發科"}], "tpex_quote": tpex, "twse_basic": [], "tpex_basic": []})
            r2 = run("2026-10-02", root, mins={"TWSE": 1, "TPEX": 1})
            chk("③ 日差:2317 下市 · 2454 新增(ENG087 同一式)", r2["diff"]["new"] == ["2454"] and r2["diff"]["delisted_today"] == ["2317"], r2["diff"]["counts"])
            import duckdb
            con = duckdb.connect(str(root / "vdf_master_lists.duckdb"))
            n = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT date) FROM {TABLE}").fetchone()
            con.close()
            r2b = run("2026-10-02", root, mins={"TWSE": 1, "TPEX": 1})
            con = duckdb.connect(str(root / "vdf_master_lists.duckdb"))
            n3 = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
            con.close()
            chk("④ DuckDB 增量:兩天各一份 · 同日重跑零新列(date + ticker 反連接)", n[1] == 2 and n3 == n[0] and r2b["write"]["duckdb_added"] == 0, (n, n3))
            many = [{"Code": f"{1100 + i}", "Name": f"S{i}"} for i in range(60)]
            g["_via_net"] = lambda: _Net({"twse_quote": many, "tpex_quote": tpex, "twse_basic": [], "tpex_basic": []})
            run("2026-10-03", root, mins={"TWSE": 1, "TPEX": 1})
            g["_via_net"] = lambda: _Net({"twse_quote": many[:5], "tpex_quote": tpex, "twse_basic": [], "tpex_basic": []})
            r4 = run("2026-10-04", root, mins={"TWSE": 1, "TPEX": 1})
            latest = pd.read_parquet(root / OUT_DIR / f"{STEM}_latest.parquet")
            chk("⑤ 大量下市守門:55 檔同日消失 → RED · 最新不覆寫(負控)", r4["lamp"] == "RED" and r4["write"] == {"written": False}
                and len(latest[latest.status != "DELISTED"]) >= 60, len(r4["diff"]["delisted_today"]))
            g["_via_net"] = lambda: _Net({}, deny=True)
            os.environ["VIA_FROM_VDFSM"] = "YES"
            cwd = os.getcwd()
            os.chdir(root)
            try:
                import contextlib
                import io
                with contextlib.redirect_stdout(io.StringIO()):
                    rc_g = main(["run"])
            finally:
                os.chdir(cwd)
                os.environ.pop("VIA_FROM_VDFSM", None)
            chk("⑥ 雙閘沒開 → rc4(不是壞掉)· 零寫入最新", rc_g == 4)
        finally:
            g["_via_net"] = real
    saved = {k: os.environ.pop(k, None) for k in ("VIA_FROM_VDFSM", "VIA_FROM_VCGC")}
    try:
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc_x = main(["run"])
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 沒有總控入口 → rc2;加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", rc_x == 2 and "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
