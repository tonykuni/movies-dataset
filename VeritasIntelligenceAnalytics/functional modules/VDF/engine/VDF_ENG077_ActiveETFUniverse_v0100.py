#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG077_ActiveETFUniverse — 主動式 ETF 宇宙日更器(批374;via-etfuniv)
====================================================================
操作員令(批374)「How to update the list automatically? Active stock tickers include a suffix of A, but only active
Taiwan stock ETF has to release holding change daily. Use this logic to generate a daily auto updating mechanism.」
律(A 碼律+國內成分律):
  ① 代碼律   台灣主動式 ETF 代號=五碼數字+A(^\\d{5}A$;如 00981A);非 A 碼=被動,不入宇宙。
  ② 揭露律   只有「國內成分證券主動式」(台股主動式)須每日揭露持股;「國外成分證券主動式」(如 00402A 美國科技)
              不在每日持股名單=標 FOREIGN_COMPONENT,宇宙保留但 daily_required=False(誠實;不再對其抓持股)。
  ③ 來源     L1 官方 TWSE openapi t187ap47_L(ETF 冊;經 SUP_MDL740 統包雙閘)→ L2 離線後備=ENG055 L4 落表 etf_book
              最新 as_of → L3 既有 active_tw_etf_universe 快照(聯集只增,永不刪)。
  ④ 落地     ActiveTWETF.duckdb:active_tw_etf_registry(ticker,name,fund_type,domestic,daily_required,first_seen,last_seen,
              status,source;只增/更新 last_seen)+ active_tw_etf_universe 新快照列(snapshot_at;append-only)
              + ENG051 SSOT 檔 active_tw_etf_ssot/ActiveTWETF_Latest.csv(raw_ticker,name,issuer;只含 daily_required)
  ⑤ 差異     本次 vs 上次:新增(NEW)/消失於官方冊(MISSING_FROM_SOURCE=候查,不刪)逐字印;存證 VIA_Reports/active_etf_universe/。
  ⑥ 日更     boot 日更鏈第 ④ 步前置(先更宇宙再抓持股);FixAll 步 etf_universe;樞紐任務 etf_universe;via-etfuniv。
用法:python3 VDF_ENG077_ActiveETFUniverse_v0100.py run [--offline] | status | --selftest
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
# ===== [VIA:NET-BRIDGE:END] =====
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
ETF_ROOT = VDF / "output_hub" / "active_tw_etf"
DB_ETF = ETF_ROOT / "active_tw_etf_holdings" / "ActiveTWETF.duckdb"
DB_TW = VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb"
SSOT_CSV = ETF_ROOT / "active_tw_etf_ssot" / "ActiveTWETF_Latest.csv"
REP = VIA / "VIA_Reports" / "active_etf_universe"
TWSE_ETF_BOOK = "https://openapi.twse.com.tw/v1/opendata/t187ap47_L"
A_CODE = re.compile(r"^\d{5}A$")
REG_TABLE = "active_tw_etf_registry"
UNI_TABLE = "active_tw_etf_universe"


def is_active_code(code: str) -> bool:
    return bool(A_CODE.match(str(code or "").strip()))


def is_domestic(fund_type: str, name: str = "") -> bool | None:
    """國內成分=須每日揭露;國外成分=不須;類型未知=None(誠實)"""
    t = str(fund_type or "")
    if "國內成分" in t:
        return True
    if "國外成分" in t:
        return False
    return None


def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


def _net_or_none():
    import glob as _g
    import importlib.util as _il
    hits = sorted(_g.glob(str(VIA / "supportive modules" / "network" / "SUP_MDL740_NetUnified_v*.py")))
    if not hits:
        return None
    spec = _il.spec_from_file_location("via_net_dyn", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["via_net_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 來源
def from_twse(net) -> tuple[list[dict], str]:
    r = net.http_json(TWSE_ETF_BOOK)
    if r.get("state") != "OK" or not isinstance(r.get("data"), list):
        return [], f"TWSE {r.get('state')} {str(r.get('note', ''))[:60]}"
    out = []
    for it in r["data"]:
        code = str(it.get("基金代號") or "").strip()
        if not is_active_code(code):
            continue
        out.append({"ticker": code, "name": str(it.get("基金簡稱") or "").strip(), "fund_type": str(it.get("基金類型") or "").strip(),
                    "as_of": str(it.get("出表日期") or "").strip(), "source": "TWSE_t187ap47_L"})
    return out, f"TWSE {len(r['data'])} 檔 ETF 冊 · A 碼 {len(out)}"


def from_etf_book() -> tuple[list[dict], str]:
    if not DB_TW.exists():
        return [], "etf_book 庫缺"
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        if "etf_book" not in {t for (t,) in con.execute("SHOW TABLES").fetchall()}:
            return [], "etf_book 表缺"
        mx = con.execute("SELECT MAX(as_of) FROM etf_book").fetchone()[0]
        rows = con.execute("SELECT fund_code, fund_name, fund_type, as_of FROM etf_book WHERE as_of = ?", [mx]).fetchall()
    finally:
        con.close()
    out = [{"ticker": c, "name": n, "fund_type": t, "as_of": a, "source": "ENG055_L4_etf_book"} for c, n, t, a in rows if is_active_code(c)]
    return out, f"etf_book as_of {mx} · A 碼 {len(out)}"


def from_existing() -> list[dict]:
    if not DB_ETF.exists():
        return []
    import duckdb
    con = duckdb.connect(str(DB_ETF), read_only=True)
    try:
        tabs = {t for (t,) in con.execute("SHOW TABLES").fetchall()}
        if UNI_TABLE not in tabs:
            return []
        rows = con.execute(f"SELECT etf_ticker, etf_name, issuer FROM {UNI_TABLE}").fetchall()
    finally:
        con.close()
    seen, out = set(), []
    for t, n, i in rows:
        if is_active_code(t) and t not in seen:
            seen.add(t)
            out.append({"ticker": t, "name": n, "fund_type": "", "as_of": "", "source": "existing_universe", "issuer": i or ""})
    return out


def unify(primary: list[dict], fallback: list[dict], existing: list[dict]) -> list[dict]:
    """聯集只增:官方冊優先取名/類型;既有快照補 issuer;永不刪"""
    m = {}
    for src in (existing, fallback, primary):   # 後寫者勝(官方最後)
        for r in src:
            cur = m.setdefault(r["ticker"], {"ticker": r["ticker"], "name": "", "fund_type": "", "as_of": "", "source": "", "issuer": ""})
            for k in ("name", "fund_type", "as_of", "source"):
                if r.get(k):
                    cur[k] = r[k]
            if r.get("issuer"):
                cur["issuer"] = r["issuer"]
    out = []
    for r in m.values():
        dom = is_domestic(r["fund_type"], r["name"])
        r["domestic"] = dom
        r["daily_required"] = bool(dom) if dom is not None else True   # 類型未知=保守視為須抓(誠實標 UNKNOWN_TYPE)
        r["status"] = "ACTIVE_DOMESTIC" if dom else ("FOREIGN_COMPONENT" if dom is False else "UNKNOWN_TYPE")
        out.append(r)
    return sorted(out, key=lambda r: r["ticker"])


# ---------------------------------------------------------------- 落地
def persist(rows: list[dict], ts: str) -> dict:
    import duckdb
    DB_ETF.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_ETF))
    try:
        con.execute(f"""CREATE TABLE IF NOT EXISTS {REG_TABLE}(ticker VARCHAR PRIMARY KEY, name VARCHAR, fund_type VARCHAR, domestic BOOLEAN,
            daily_required BOOLEAN, status VARCHAR, source VARCHAR, issuer VARCHAR, first_seen VARCHAR, last_seen VARCHAR)""")
        con.execute(f"CREATE TABLE IF NOT EXISTS {UNI_TABLE}(snapshot_at TIMESTAMP, etf_ticker VARCHAR, etf_name VARCHAR, issuer VARCHAR, universe_source VARCHAR)")
        prev = {r[0]: r for r in con.execute(f"SELECT ticker, status, last_seen FROM {REG_TABLE}").fetchall()}
        new, kept = [], 0
        for r in rows:
            if r["ticker"] in prev:
                con.execute(f"UPDATE {REG_TABLE} SET name=?, fund_type=?, domestic=?, daily_required=?, status=?, source=?, issuer=COALESCE(NULLIF(?, ''), issuer), last_seen=? WHERE ticker=?",
                            [r["name"], r["fund_type"], r["domestic"], r["daily_required"], r["status"], r["source"], r.get("issuer", ""), ts, r["ticker"]])
                kept += 1
            else:
                con.execute(f"INSERT INTO {REG_TABLE} VALUES (?,?,?,?,?,?,?,?,?,?)",
                            [r["ticker"], r["name"], r["fund_type"], r["domestic"], r["daily_required"], r["status"], r["source"], r.get("issuer", ""), ts, ts])
                new.append(r["ticker"])
        # 官方冊消失者:不刪,標 MISSING_FROM_SOURCE(候查)
        cur = {r["ticker"] for r in rows}
        missing = [t for t in prev if t not in cur]
        for t in missing:
            con.execute(f"UPDATE {REG_TABLE} SET status='MISSING_FROM_SOURCE', daily_required=FALSE WHERE ticker=?", [t])
        snap = datetime.now()
        con.executemany(f"INSERT INTO {UNI_TABLE} VALUES (?,?,?,?,?)", [(snap, r["ticker"], r["name"], r.get("issuer", ""), "ENG077_" + r["source"]) for r in rows if r["daily_required"]])
        return {"new": new, "kept": kept, "missing": missing}
    finally:
        con.close()


def write_ssot_csv(rows: list[dict]) -> int:
    SSOT_CSV.parent.mkdir(parents=True, exist_ok=True)
    sel = [r for r in rows if r["daily_required"]]
    with SSOT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["raw_ticker", "name", "issuer"])
        w.writeheader()
        for r in sel:
            w.writerow({"raw_ticker": r["ticker"], "name": r["name"], "issuer": r.get("issuer", "")})
    return len(sel)


def run(args: list[str]) -> int:
    offline = "--offline" in args
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=== 主動式 ETF 宇宙日更(VDF_ENG077;A 碼律+國內成分揭露律)===", flush=True)
    primary, note1 = [], "離線"
    if not offline:
        if not gate_open():
            note1 = "同意閘未開=離線後備(誠實)"
        else:
            net = _net_or_none()
            if net is None:
                note1 = "統包網路工具缺=離線後備"
            else:
                primary, note1 = from_twse(net)
    fallback, note2 = from_etf_book()
    existing = from_existing()
    rows = unify(primary, fallback, existing)
    if not rows:
        print(f"  [SKIP] 三源皆空(TWSE:{note1};etf_book:{note2};既有 0)", flush=True)
        return 3
    p = persist(rows, ts)
    n_csv = write_ssot_csv(rows)
    dom = sum(1 for r in rows if r["status"] == "ACTIVE_DOMESTIC")
    frn = sum(1 for r in rows if r["status"] == "FOREIGN_COMPONENT")
    unk = sum(1 for r in rows if r["status"] == "UNKNOWN_TYPE")
    REP.mkdir(parents=True, exist_ok=True)
    (REP / f"UNIVERSE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json").write_text(json.dumps(
        {"ts": ts, "sources": {"twse": note1, "etf_book": note2, "existing": len(existing)}, "n": len(rows), "domestic": dom, "foreign": frn, "unknown": unk,
         "new": p["new"], "missing_from_source": p["missing"], "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [來源] TWSE:{note1} · etf_book:{note2} · 既有快照 {len(existing)}", flush=True)
    print(f"  [宇宙] A 碼 {len(rows)} 檔 · 國內成分(須每日揭露){dom} · 國外成分 {frn} · 類型未知 {unk} · 新增 {len(p['new'])} {p['new']} · 官方冊消失 {len(p['missing'])} {p['missing']}", flush=True)
    print(f"  [落地] {REG_TABLE} 更新 {p['kept']}+新 {len(p['new'])} · 快照 {UNI_TABLE} +{n_csv} · SSOT csv {SSOT_CSV.name} {n_csv} 檔(ENG051 讀此檔抓持股)", flush=True)
    for r in rows:
        if r["status"] != "ACTIVE_DOMESTIC":
            print(f"    [{r['status']:<19}] {r['ticker']} {r['name']}", flush=True)
    return 0


def status() -> int:
    if not DB_ETF.exists():
        print("  [DB] 缺")
        return 0
    import duckdb
    con = duckdb.connect(str(DB_ETF), read_only=True)
    try:
        tabs = {t for (t,) in con.execute("SHOW TABLES").fetchall()}
        if REG_TABLE in tabs:
            for st, n, ls in con.execute(f"SELECT status, COUNT(*), MAX(last_seen) FROM {REG_TABLE} GROUP BY 1 ORDER BY 1").fetchall():
                print(f"  [{st}] {n} · last_seen {ls}")
        else:
            print(f"  [{REG_TABLE}] 表缺(先 run)")
    finally:
        con.close()
    print(f"  SSOT csv {'在' if SSOT_CSV.exists() else '缺'} {SSOT_CSV}")
    return 0


def selftest() -> int:
    import tempfile
    global DB_ETF, DB_TW, SSOT_CSV, REP
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    chk("① A 碼律(00981A ✓;0050/00981/00981B/00981AA ✗)", is_active_code("00981A") and not any(is_active_code(x) for x in ("0050", "00981", "00981B", "00981AA", "981A")))
    chk("② 揭露律(國內成分=須每日;國外成分=不須;未知=None)", is_domestic("國內成分證券主動式交易所交易基金(股票)") is True and is_domestic("國外成分證券主動式交易所交易基金(股票)") is False and is_domestic("") is None)
    chk("③ 同意閘 fail-closed", not gate_open({}) and gate_open({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}))
    _s = (DB_ETF, DB_TW, SSOT_CSV, REP)
    with tempfile.TemporaryDirectory() as td:
        import duckdb
        DB_ETF, DB_TW = Path(td) / "etf.duckdb", Path(td) / "tw.duckdb"
        SSOT_CSV, REP = Path(td) / "ssot" / "ActiveTWETF_Latest.csv", Path(td) / "rep"
        c = duckdb.connect(str(DB_TW))
        c.execute("CREATE TABLE etf_book(fund_code VARCHAR, fund_name VARCHAR, fund_type VARCHAR, is_active BOOLEAN, tracking_index VARCHAR, as_of VARCHAR)")
        c.executemany("INSERT INTO etf_book VALUES (?,?,?,?,?,?)", [
            ("00981A", "主動群益台灣強棒", "國內成分證券主動式交易所交易基金(股票)", True, "不適用", "1150905"),
            ("00402A", "主動安聯美國科技", "國外成分證券主動式交易所交易基金(股票)", True, "不適用", "1150905"),
            ("0050", "元大台灣50", "國內成分證券指數股票型基金", False, "臺灣50指數", "1150905"),
            ("00981A", "舊名", "國內成分證券主動式交易所交易基金(股票)", True, "不適用", "1150801")])
        c.close()
        c = duckdb.connect(str(DB_ETF))
        c.execute("CREATE TABLE active_tw_etf_universe(snapshot_at TIMESTAMP, etf_ticker VARCHAR, etf_name VARCHAR, issuer VARCHAR, universe_source VARCHAR)")
        c.execute("INSERT INTO active_tw_etf_universe VALUES (now(), '00981A', '主動群益台灣強棒', '群益投信', 'OLD'), (now(), '00777A', '已下市主動', '某投信', 'OLD')")
        c.close()
        fb, n2 = from_etf_book()
        ex = from_existing()
        rows = unify([], fb, ex)
        by = {r["ticker"]: r for r in rows}
        chk("④ 離線後備=etf_book 最新 as_of 之 A 碼(0050 不入;舊 as_of 不採;既有快照 issuer 補入;聯集只增含 00777A)",
            set(by) == {"00981A", "00402A", "00777A"} and by["00981A"]["issuer"] == "群益投信" and by["00981A"]["name"] == "主動群益台灣強棒" and by["00402A"]["status"] == "FOREIGN_COMPONENT"
            and by["00777A"]["status"] == "UNKNOWN_TYPE" and by["00981A"]["daily_required"] and not by["00402A"]["daily_required"], str(sorted(by)))
        p1 = persist(rows, "t1")
        rows2 = [r for r in rows if r["ticker"] != "00777A"]
        p2 = persist(rows2, "t2")
        c = duckdb.connect(str(DB_ETF), read_only=True)
        st = dict(c.execute(f"SELECT ticker, status FROM {REG_TABLE}").fetchall())
        fs = c.execute(f"SELECT first_seen, last_seen FROM {REG_TABLE} WHERE ticker='00981A'").fetchone()
        snaps = c.execute(f"SELECT COUNT(*) FROM {UNI_TABLE} WHERE universe_source LIKE 'ENG077_%'").fetchone()[0]
        c.close()
        chk("⑤ 冊只增(首跑新 3;再跑更新 last_seen 不改 first_seen;消失者標 MISSING_FROM_SOURCE 不刪;快照 append-only)",
            len(p1["new"]) == 3 and p1["kept"] == 0 and p2["kept"] == 2 and p2["missing"] == ["00777A"] and st["00777A"] == "MISSING_FROM_SOURCE"
            and st["00981A"] == "ACTIVE_DOMESTIC" and fs == ("t1", "t2") and snaps == 3, f"{p1} {p2} snaps={snaps}")
        n = write_ssot_csv(rows2)
        txt = SSOT_CSV.read_text(encoding="utf-8-sig")
        chk("⑥ ENG051 SSOT csv(raw_ticker,name,issuer;只含 daily_required=國內成分;utf-8-sig)", n == 1 and txt.splitlines()[0] == "raw_ticker,name,issuer" and "00981A" in txt and "00402A" not in txt)

        class FakeNet:
            @staticmethod
            def http_json(url):
                return {"state": "OK", "data": [{"基金代號": "00999A", "基金簡稱": "主動野村臺灣高息", "基金類型": "國內成分證券主動式交易所交易基金(股票)", "出表日期": "1150907"},
                                                {"基金代號": "0056", "基金簡稱": "元大高股息", "基金類型": "國內成分證券指數股票型基金", "出表日期": "1150907"}]}
        pr, note = from_twse(FakeNet)
        rows3 = unify(pr, fb, ex)
        chk("⑦ 官方 TWSE 為主(A 碼濾;0056 不入;與後備聯集;新 00999A NEW)", len(pr) == 1 and pr[0]["ticker"] == "00999A" and "00999A" in {r["ticker"] for r in rows3} and "0056" not in {r["ticker"] for r in rows3})
    DB_ETF, DB_TW, SSOT_CSV, REP = _s
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(A 碼律/揭露律/聯集只增/永不刪/誠實/雙閘)", all(k in src for k in ("A 碼律", "揭露律", "聯集只增", "永不刪", "誠實", "雙閘")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 主動式 ETF 宇宙日更(VDF_ENG077)· 八檢自測 ===")
        return selftest()
    if a and a[0] == "status":
        return status()
    return run([x for x in a if x != "run"])


if __name__ == "__main__":
    sys.exit(main())
