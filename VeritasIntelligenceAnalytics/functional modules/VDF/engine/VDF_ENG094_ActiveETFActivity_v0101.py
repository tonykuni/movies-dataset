#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG094 v0101 — active Taiwan ETF daily metrics (規模 AUM · 淨值 NAV · 單位數 · 資金流) + breakdown (持股/產業配置).

v0100 stays (L04); this thin tail adds verbs and forwards the v0100 surface (plan/build/analyze…) via __getattr__.
Runs only through VCGC (VIA_FROM_VCGC=YES); `--selftest` is offline, deterministic, fixtures only.

  fetch [--apply] [--db PATH]      GATED lane. Uses only the unified network tool (_via_net → SUP_MDL740);
                                   refuses unless the operator has set VIA_NET_CONSENT=YES himself (this file reads it,
                                   never sets it). Produces etf_daily_metrics; --apply upserts into the EXISTING
                                   ActiveTWETF.duckdb (never creates a replacement DB, same rule as v0100.build).
  metrics [--db PATH] [--json]     read-only: latest etf_daily_metrics row per ETF.
  breakdown [--apply] [--all] [--db PATH] [--tw-db PATH] [--json]
                                   holdings_daily (ENG051/ENG078) × industry (VDF_ENG087 load_stock_list →
                                   tw_listings_industry.industry_name) → etf_breakdown. Zero network.
  sources [--json]                 which field has a real source (with file:line evidence) and which is ABSENT.

Sources adopted from existing code (no invented URLs):
  units_outstanding  TWSE OpenAPI t187ap47_L 「發行單位數/轉換數」|「發行單位數」   GroupIndex/engine/VIA_ActiveStockETF.py:709
                     URL as used by VDF_ENG077 v0100:68 / VIA_ActiveStockETF.py:492;  出表日期 ROC → ISO (VIA_ActiveStockETF.py:369)
  nav                TWSE /rwd/zh/ETF/etfNav?response=json (+&date=YYYYMMDD)       VIA_ActiveStockETF.py:551-552 (CANDIDATE:
                     that file itself notes TWSE moved this dataset; verify on the workstation) · row parse = parse_nav_rows :606
  aum                units × NAV (VIA_ActiveStockETF.py:1183); fallback: ENG055 lane L5 etf_stats_daily (Yahoo, ESTIMATE only)
  net flow           Δunits × NAV_t (VDF_ENG094 v0100:184-185 ADJUSTED_NET_UNITS_X_END_NAV; VIA_ActiveStockETF.py:887);
                     when units are missing: VDF_ENG096.aum_flow(prev_aum, aum, nav_return) (VDF_ENG096 v0100:62)
                     inflow/outflow = ENG096 split of the NET flow (not gross).
  units_subscribed / units_redeemed (gross creations/redemptions): ABSENT — no endpoint anywhere in live code or quarantine.
                     Candidate only: capitalfund POST /CFWeb/api/etf/buyback returns data.pcf, but no pcf NAV/units field names
                     are evidenced in code (only fundName/date1, VDF_ENG078 v0107:1543). Columns stay NULL.
kind: OFFICIAL = levels only, all from official lanes on one date; ESTIMATE = any flow value, any fallback or date mismatch.
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import datetime as _dt
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG094_ActiveETFActivity"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.py$", p.name)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))),
                  key=_vnum, default=HERE / "VDF_ENG094_ActiveETFActivity_v0100.py")
_SPEC = importlib.util.spec_from_file_location("eng094_prior_of_v0101", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = PRIOR
_SPEC.loader.exec_module(PRIOR)

ENGINE = Path(__file__).name
VDF = HERE.parent
DB = PRIOR.DB                                            # ActiveTWETF.duckdb(VIA_DB_ACTIVETWETF 可覆寫)
DB_GL = VDF / "output_hub" / "mega" / "vdf_global_market.duckdb"   # ENG055 v0118:167-169(L5 etf_stats_daily)
METRICS_TABLE, BREAKDOWN_TABLE = "etf_daily_metrics", "etf_breakdown"
METRICS_COLS = ("date", "etf_ticker", "aum", "nav", "units_outstanding", "units_subscribed", "units_redeemed", "net_units",
                "inflow_value", "outflow_value", "net_flow_value", "source", "source_url", "fetched_at", "kind")
METRICS_DDL = ("CREATE TABLE IF NOT EXISTS etf_daily_metrics(date DATE, etf_ticker VARCHAR, aum DOUBLE, nav DOUBLE, "
               "units_outstanding DOUBLE, units_subscribed DOUBLE, units_redeemed DOUBLE, net_units DOUBLE, "
               "inflow_value DOUBLE, outflow_value DOUBLE, net_flow_value DOUBLE, source VARCHAR, source_url VARCHAR, "
               "fetched_at TIMESTAMP, kind VARCHAR)")
BREAKDOWN_COLS = ("portfolio_date", "etf_ticker", "group_kind", "group", "weight_pct", "n_holdings")
BREAKDOWN_DDL = ('CREATE TABLE IF NOT EXISTS etf_breakdown(portfolio_date DATE, etf_ticker VARCHAR, group_kind VARCHAR, '
                 '"group" VARCHAR, weight_pct DOUBLE, n_holdings BIGINT)')

URL_UNITS = "https://openapi.twse.com.tw/v1/opendata/t187ap47_L"          # VDF_ENG077 v0100:68
URL_NAV = ("https://www.twse.com.tw/rwd/zh/ETF/etfNav?response=json",      # VIA_ActiveStockETF.py:551
           "https://www.twse.com.tw/rwd/zh/ETF/etfNav?response=json&date={ymd}")  # :552
ACTIVE_ETF_CODE = re.compile(r"^00\d{3}A$")                                 # = VDF_ENG087 v0105 ACTIVE_ETF_CODE
STOCK_CODE = re.compile(r"^[1-9]\d{3}$")                                    # = VDF_ENG087 v0105 STOCK_CODE

SOURCES = {
    "units_outstanding": {"state": "REAL", "kind": "OFFICIAL", "url": URL_UNITS,
                          "field": "發行單位數/轉換數 | 發行單位數 · date=出表日期",
                          "evidence": "functional modules/GroupIndex/engine/VIA_ActiveStockETF.py:709 · VDF_ENG077_ActiveETFUniverse_v0100.py:68",
                          "note": "t187ap47_L 更新頻率未在容器實測;工作站 fetch 兩天比對單位數是否逐日變動"},
    "nav": {"state": "CANDIDATE", "kind": "OFFICIAL", "url": URL_NAV[0],
            "field": "欄名含「淨值」(不含 前一/折溢) | nav | navPerShare · 代號/代碼 · 日期",
            "evidence": "functional modules/GroupIndex/engine/VIA_ActiveStockETF.py:551-552 (parse :606-627)",
            "note": "原檔自承 TWSE 搬過此資料集路徑;工作站實測前不算 VERIFIED"},
    "aum": {"state": "DERIVED", "kind": "OFFICIAL×OFFICIAL", "url": "",
            "field": "units_outstanding × nav",
            "evidence": "functional modules/GroupIndex/engine/VIA_ActiveStockETF.py:1183",
            "fallback": "VDF_ENG055 lane L5 etf_stats_daily(date,symbol,aum,nav) Yahoo → kind ESTIMATE (VDF_ENG055_OmniFetch_v0118.py:462-466)"},
    "net_flow": {"state": "DERIVED", "kind": "ESTIMATE", "url": "",
                 "field": "net_units = Δunits_outstanding · net_flow_value = net_units × nav_t · 缺單位數 → ENG096 aum_flow",
                 "evidence": "VDF_ENG094_ActiveETFActivity_v0100.py:184-185 · VDF_ENG096_ActiveETFMeasures_v0100.py:62 · VIA_ActiveStockETF.py:887"},
    "gross_subscriptions_redemptions": {"state": "ABSENT", "kind": None, "url": "",
                                        "field": "units_subscribed / units_redeemed",
                                        "evidence": "none in live engines or references/intake/* (grep 申購/買回/creation/redemption)",
                                        "note": "候選:capitalfund POST /CFWeb/api/etf/buyback 的 data.pcf(僅群益);程式內只見 fundName/date1"
                                                "(VDF_ENG078_ActiveETFHoldingsHistory_v0107.py:1543),不猜欄名 → 欄位留 NULL"},
    "breakdown": {"state": "REAL", "kind": "DERIVED", "url": "",
                  "field": "holdings_daily × tw_listings_industry.industry_name",
                  "evidence": "VDF_ENG051_ActiveTWETF_Holdings_v0103.py:2259 (holdings_daily DDL) · VDF_ENG055_OmniFetch_v0118.py:336-341 (industry_name)"},
}


def __getattr__(name: str):
    """PEP 562:v0100 公開面(plan/build/analyze/fund_interval…)照舊可叫。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- 小工具
def _num(v):
    if v is None:
        return None
    try:
        x = float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return x if x == x else None


def _norm(s) -> str:
    return re.sub(r"\s+", "", str(s or ""))


def roc_to_iso(s) -> str | None:
    """'1150731' / '115/07/31' / '20260731' → '2026-07-31'(沿用 VIA_ActiveStockETF.py:369)。"""
    digits = re.sub(r"\D", "", str(s or ""))
    if len(digits) == 7:
        y, m, d = int(digits[:3]) + 1911, digits[3:5], digits[5:7]
    elif len(digits) == 6:
        y, m, d = int(digits[:2]) + 1911, digits[2:4], digits[4:6]
    elif len(digits) == 8 and digits[0] in "12":
        y, m, d = int(digits[:4]), digits[4:6], digits[6:8]
    else:
        return None
    try:
        return _dt.date(y, int(m), int(d)).isoformat()
    except ValueError:
        return None


def _bare(t) -> str:
    return str(t or "").strip().upper().split(".")[0]


def _eng(stem: str):
    hits = sorted(HERE.glob(stem + "_v*.py"), key=_vnum)
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location(f"eng094v0101_{stem}", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 解析(純函式)
def parse_units(payload) -> dict:
    """t187ap47_L → {ticker: {units, as_of}};只收主動 A 碼。"""
    out = {}
    for r in payload if isinstance(payload, list) else []:
        if not isinstance(r, dict):
            continue
        code = _bare(r.get("基金代號"))
        if not ACTIVE_ETF_CODE.fullmatch(code):
            continue
        units = _num(r.get("發行單位數/轉換數") or r.get("發行單位數"))
        out[code] = {"units": units if units and units > 0 else None, "as_of": roc_to_iso(r.get("出表日期"))}
    return out


def parse_nav_rows(rows) -> dict:
    """NAV 回包(dict 列或位置列)→ {ticker: {nav, date}}(沿用 VIA_ActiveStockETF.py:606-627 的判欄規則)。"""
    if isinstance(rows, dict):
        rows = rows.get("data") or rows.get("aaData") or []
    out = {}
    for r in rows or []:
        code = nav = day = None
        if isinstance(r, dict):
            for k, v in r.items():
                kn = _norm(k)
                if code is None and ("代號" in kn or "代碼" in kn or kn.lower() in ("code", "stockcode", "fundcode")):
                    code = _norm(v)
                elif nav is None and ("淨值" in kn and "前一" not in kn and "折溢" not in kn):
                    nav = _num(v)
                elif nav is None and kn.lower() in ("nav", "navpershare"):
                    nav = _num(v)
                elif day is None and ("日期" in kn or kn.lower() == "date"):
                    day = roc_to_iso(v) or _norm(v)
        elif isinstance(r, (list, tuple)) and len(r) >= 3:
            code, nav = _norm(r[0]), _num(r[2])
        if code and nav is not None and nav > 0:
            out[_bare(code)] = {"nav": nav, "date": day or ""}
    return out


# ---------------------------------------------------------------- 快照 → 指標列(純函式;可單測)
def snapshot_rows(tickers, units: dict, navs: dict, yahoo: dict, fetched_at: str, today: str) -> list:
    """一天一檔一列(還沒算流量)。levels 來自官方 → OFFICIAL;用了 Yahoo 後備或日期對不上 → ESTIMATE。"""
    rows = []
    for t in sorted(set(tickers)):
        u, n, y = units.get(t) or {}, navs.get(t) or {}, yahoo.get(t) or {}
        src, urls, est = [], [], False
        uo, nav = u.get("units"), n.get("nav")
        day = n.get("date") or u.get("as_of") or today
        if uo is not None:
            src.append("units=TWSE_t187ap47_L")
            urls.append(URL_UNITS)
        if nav is not None:
            src.append("nav=TWSE_etfNav")
            urls.append(URL_NAV[0])
        if uo is not None and nav is not None and u.get("as_of") and n.get("date") and u["as_of"] != n["date"]:
            est = True
            src.append(f"DATE_MISMATCH(units {u['as_of']} · nav {n['date']})")
        aum = uo * nav if (uo is not None and nav is not None) else None
        if aum is not None:
            src.append("aum=units×nav")
        if nav is None and y.get("nav") is not None:
            nav, est = y["nav"], True
            src.append("nav=YAHOO_L5(ESTIMATE)")
        if aum is None and y.get("aum") is not None:
            aum, est = y["aum"], True
            src.append("aum=YAHOO_L5(ESTIMATE)")
        if uo is None and nav is None and aum is None:
            continue
        rows.append({"date": day, "etf_ticker": t, "aum": aum, "nav": nav, "units_outstanding": uo,
                     "units_subscribed": None, "units_redeemed": None, "net_units": None,
                     "inflow_value": None, "outflow_value": None, "net_flow_value": None,
                     "source": " · ".join(src), "source_url": " ".join(urls), "fetched_at": fetched_at,
                     "kind": "ESTIMATE" if est else "OFFICIAL"})
    return rows


def compute_flows(rows: list, aum_flow=None) -> list:
    """按 (etf, date) 排序,前後兩天:Δunits × NAV_t;缺單位數用 ENG096.aum_flow。流量一律 ESTIMATE(淨額,非毛申贖)。"""
    if aum_flow is None:
        eng096 = _eng("VDF_ENG096_ActiveETFMeasures")
        aum_flow = eng096.aum_flow
    out, last = [], {}
    for r in sorted(rows, key=lambda x: (x["etf_ticker"], str(x["date"]))):
        r = dict(r)
        p = last.get(r["etf_ticker"])
        if p is not None and str(p["date"]) != str(r["date"]):
            net = units = None
            if r["units_outstanding"] is not None and p["units_outstanding"] is not None and r["nav"] is not None:
                units = r["units_outstanding"] - p["units_outstanding"]
                net = units * r["nav"]
                method = "flow=Δunits×nav"
            elif None not in (r["aum"], p["aum"], r["nav"], p["nav"]) and p["nav"]:
                net = aum_flow(p["aum"], r["aum"], r["nav"] / p["nav"] - 1.0)["net"]
                method = "flow=ENG096.aum_flow"
            if net is not None:
                r.update(net_units=units, net_flow_value=net, inflow_value=net if net > 0 else 0.0,
                         outflow_value=-net if net < 0 else 0.0, kind="ESTIMATE",
                         source=(r["source"] + " · " + method + f"(prev {p['date']})").strip(" ·"))
        last[r["etf_ticker"]] = r
        out.append(r)
    return out


# ---------------------------------------------------------------- 庫
def _connect(db: Path, write: bool):
    import duckdb
    return duckdb.connect(str(db), read_only=not write)


def _tables(con) -> set:
    return {r[0] for r in con.execute("SHOW TABLES").fetchall()}


def read_metrics(db: Path) -> list:
    db = Path(db)
    if not db.is_file():
        return []
    con = _connect(db, False)
    try:
        if METRICS_TABLE not in _tables(con):
            return []
        cur = con.execute(f"SELECT {', '.join(METRICS_COLS)} FROM {METRICS_TABLE} ORDER BY etf_ticker, date")
        return [dict(zip(METRICS_COLS, (v.isoformat() if isinstance(v, (_dt.date, _dt.datetime)) and i in (0, 13) else v
                                        for i, v in enumerate(row)))) for row in cur.fetchall()]
    finally:
        con.close()


def upsert_metrics(db: Path, rows: list) -> int:
    """同鍵 (date, etf_ticker):OFFICIAL 不被 ESTIMATE 蓋掉;其餘以新列取代。庫不在 = 拒(不代建正庫)。"""
    db = Path(db)
    if not db.is_file():
        raise ValueError(f"正庫不在:{db};不代建替身庫(同 v0100.build)")
    con = _connect(db, True)
    n = 0
    try:
        con.execute("BEGIN TRANSACTION")
        con.execute(METRICS_DDL)
        for r in rows:
            old = con.execute(f"SELECT kind, net_flow_value FROM {METRICS_TABLE} WHERE date=CAST(? AS DATE) AND etf_ticker=?",
                              [r["date"], r["etf_ticker"]]).fetchone()
            if old and old[0] == "OFFICIAL" and r["kind"] == "ESTIMATE" and r["net_flow_value"] is None:
                continue
            con.execute(f"DELETE FROM {METRICS_TABLE} WHERE date=CAST(? AS DATE) AND etf_ticker=?", [r["date"], r["etf_ticker"]])
            con.execute(f"INSERT INTO {METRICS_TABLE} VALUES (CAST(? AS DATE),?,?,?,?,?,?,?,?,?,?,?,?,CAST(? AS TIMESTAMP),?)",
                        [r[c] for c in METRICS_COLS])
            n += 1
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()
    return n


def yahoo_levels(db_gl: Path, tickers) -> dict:
    """ENG055 L5 etf_stats_daily 最新一列(唯讀;Yahoo = ESTIMATE 後備)。"""
    db_gl = Path(db_gl)
    if not db_gl.is_file():
        return {}
    con = _connect(db_gl, False)
    try:
        if "etf_stats_daily" not in _tables(con):
            return {}
        rows = con.execute("SELECT symbol, aum, nav FROM etf_stats_daily QUALIFY row_number() OVER "
                           "(PARTITION BY symbol ORDER BY date DESC) = 1").fetchall()
    finally:
        con.close()
    want = set(tickers)
    return {_bare(s): {"aum": _num(a), "nav": _num(n)} for s, a, n in rows if _bare(s) in want}


# ---------------------------------------------------------------- fetch(閘門車道)
def consent_open(env=None) -> bool:
    env = os.environ if env is None else env
    return str(env.get("VIA_NET_CONSENT", "")).strip().upper() == "YES"


def active_universe(db_etf: Path | None = None) -> list:
    eng087 = _eng("VDF_ENG087_MarketListGovernance")
    try:
        return eng087.active_etf_codes(db_etf) if eng087 else []
    except Exception:
        return []


def fetch(db: Path = DB, apply: bool = False, net=None, env=None, today: str | None = None) -> dict:
    today = today or _dt.date.today().isoformat()
    if not consent_open(env):
        return {"state": "NO_CONSENT", "rows": [], "why": "VIA_NET_CONSENT 未由操作員設為 YES;本支只讀不代設(L07/L08)"}
    net = net if net is not None else _via_net()
    if net is None or not hasattr(net, "http_json"):
        return {"state": "ABSENT", "rows": [], "why": "統包網路工具缺(via_net_unified / SUP_MDL740)"}
    lanes = {}
    r = net.http_json(URL_UNITS)
    units = parse_units(r.get("data")) if r.get("state") == "OK" else {}
    lanes["units_outstanding"] = f"{r.get('state')} · {len(units)} 檔 A 碼"
    navs = {}
    for url in URL_NAV:
        rr = net.http_json(url.format(ymd=today.replace("-", "")))
        if rr.get("state") == "OK":
            navs = parse_nav_rows(rr.get("data"))
            if navs:
                lanes["nav"] = f"OK · {len(navs)} 檔 · {url}"
                break
        lanes["nav"] = f"{rr.get('state')} · {str(rr.get('note', ''))[:60]}"
    tickers = active_universe(db) or sorted(units)
    yahoo = yahoo_levels(DB_GL, tickers)
    lanes["yahoo_fallback"] = f"{len(yahoo)} 檔(ESTIMATE)"
    lanes["gross_subscriptions_redemptions"] = "ABSENT(無端點;見 sources)"
    fetched_at = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()
    snap = snapshot_rows(tickers, units, navs, yahoo, fetched_at, today)
    history = read_metrics(db) if Path(db).is_file() else []
    keys = {(r["etf_ticker"], str(r["date"])) for r in snap}
    merged = compute_flows([h for h in history if (h["etf_ticker"], str(h["date"])) not in keys] + snap)
    new_rows = [r for r in merged if (r["etf_ticker"], str(r["date"])) in keys]
    res = {"state": "OK" if new_rows else "NODATA", "rows": new_rows, "lanes": lanes, "universe": len(tickers),
           "written": None}
    if apply and new_rows:
        res["written"] = upsert_metrics(db, new_rows)
    return res


# ---------------------------------------------------------------- breakdown(零網路)
def asset_class(code: str, name: str) -> str:
    n = str(name or "")
    if re.search(r"現金|保證金|CASH", n, re.I):
        return "CASH"
    if re.search(r"期貨|FUTURE", n, re.I):
        return "FUTURES"
    if STOCK_CODE.fullmatch(code):
        return "STOCK_TW"
    if re.fullmatch(r"00\d{2,4}[A-Z]?", code):
        return "ETF"
    return "OTHER"


def breakdown_rows(holdings: list, industry: dict) -> list:
    """holdings: [{portfolio_date, etf_ticker, holding_ticker, holding_name, weight_pct}] → etf_breakdown 列。"""
    agg = {}
    for h in holdings:
        day, etf = str(h["portfolio_date"])[:10], _bare(h["etf_ticker"])
        code = _bare(h.get("holding_ticker"))
        w = _num(h.get("weight_pct")) or 0.0
        ac = asset_class(code, h.get("holding_name"))
        ind = (industry.get(code) or "未分類") if ac == "STOCK_TW" else ac
        for kind, grp in (("industry", ind), ("asset", ac)):
            k = (day, etf, kind, grp)
            s = agg.setdefault(k, [0.0, 0])
            s[0] += w
            s[1] += 1
    return [{"portfolio_date": k[0], "etf_ticker": k[1], "group_kind": k[2], "group": k[3],
             "weight_pct": round(v[0], 6), "n_holdings": v[1]} for k, v in sorted(agg.items())]


def read_holdings(db: Path, all_dates: bool = False) -> list:
    db = Path(db)
    if not db.is_file():
        return []
    con = _connect(db, False)
    try:
        if "holdings_daily" not in _tables(con):
            return []
        cols = [r[0] for r in con.execute("DESCRIBE holdings_daily").fetchall()]
        w = next((c for c in ("weight_pct", "weight") if c in cols), None)
        nm = "holding_name" if "holding_name" in cols else "NULL"
        sql = (f"SELECT CAST(portfolio_date AS VARCHAR), etf_ticker, holding_ticker, {nm}, {w or 'NULL'} FROM holdings_daily")
        if not all_dates:
            sql += (" WHERE (split_part(etf_ticker,'.',1), CAST(portfolio_date AS VARCHAR)) IN (SELECT split_part(etf_ticker,'.',1), "
                    "MAX(CAST(portfolio_date AS VARCHAR)) FROM holdings_daily GROUP BY 1)")
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    return [{"portfolio_date": d, "etf_ticker": e, "holding_ticker": h, "holding_name": n, "weight_pct": x}
            for d, e, h, n, x in rows]


def industry_map(db_tw: Path | None = None) -> dict:
    eng087 = _eng("VDF_ENG087_MarketListGovernance")
    if eng087 is None:
        return {}
    res = eng087.load_stock_list(db_tw)
    return {r["code"]: r.get("industry") or "" for r in res.get("rows", [])}


def write_breakdown(db: Path, rows: list) -> int:
    db = Path(db)
    if not db.is_file():
        raise ValueError(f"正庫不在:{db};不代建替身庫")
    con = _connect(db, True)
    try:
        con.execute("BEGIN TRANSACTION")
        con.execute(BREAKDOWN_DDL)
        for key in sorted({(r["portfolio_date"], r["etf_ticker"]) for r in rows}):
            con.execute(f"DELETE FROM {BREAKDOWN_TABLE} WHERE portfolio_date=CAST(? AS DATE) AND etf_ticker=?", list(key))
        con.executemany(f"INSERT INTO {BREAKDOWN_TABLE} VALUES (CAST(? AS DATE),?,?,?,?,?)",
                        [[r[c] for c in BREAKDOWN_COLS] for r in rows])
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()
    return len(rows)


def breakdown(db: Path = DB, db_tw: Path | None = None, apply: bool = False, all_dates: bool = False) -> dict:
    hold = read_holdings(db, all_dates)
    if not hold:
        return {"state": "NODATA", "rows": [], "why": f"holdings_daily 缺或空({db});先跑 VDF-WKF006 etf_holdings_daily"}
    ind = industry_map(db_tw)
    rows = breakdown_rows(hold, ind)
    unmapped = sorted({_bare(h["holding_ticker"]) for h in hold
                       if asset_class(_bare(h["holding_ticker"]), h.get("holding_name")) == "STOCK_TW"
                       and not ind.get(_bare(h["holding_ticker"]))})
    res = {"state": "OK" if ind else "AMBER", "rows": rows, "n": len(rows), "unmapped_industry": unmapped[:50],
           "why": "" if ind else "產業對照缺(tw_listings_industry 空/缺)→ 產業一律「未分類」", "written": None}
    if apply:
        res["written"] = write_breakdown(db, rows)
    return res


# ---------------------------------------------------------------- 自測(離線;假網路 + 暫存庫)
class _FakeNet:
    def __init__(self, units_payload, nav_payload):
        self.u, self.n, self.calls = units_payload, nav_payload, []

    def http_json(self, url, **_k):
        self.calls.append(url)
        if "t187ap47_L" in url:
            return {"state": "OK", "data": self.u}
        if "etfNav" in url:
            return {"state": "OK", "data": self.n}
        return {"state": "FAIL", "data": None, "note": "unexpected url"}


def selftest() -> int:
    checks = []

    def chk(name, ok, note=""):
        checks.append((name, bool(ok), note))

    chk("v0100 公開面轉接(fund_interval / build)", callable(getattr(sys.modules[__name__], "fund_interval", None))
        and callable(getattr(sys.modules[__name__], "build", None)))
    chk("ROC 日期", roc_to_iso("1150929") == "2026-09-29" and roc_to_iso("115/09/29") == "2026-09-29" and roc_to_iso("x") is None)
    units_d1 = [{"基金代號": "00981A", "發行單位數/轉換數": "1,000,000", "出表日期": "1150929"},
                {"基金代號": "00982A", "發行單位數": "500000", "出表日期": "1150929"},
                {"基金代號": "0050", "發行單位數": "9", "出表日期": "1150929"}]
    pu = parse_units(units_d1)
    chk("單位數:只收主動 A 碼、千分位", pu == {"00981A": {"units": 1000000.0, "as_of": "2026-09-29"},
                                     "00982A": {"units": 500000.0, "as_of": "2026-09-29"}}, str(pu))
    nav_d1 = {"data": [{"基金代號": "00981A", "單位淨值": "15.00", "前一營業日單位淨值": "14.9", "資料日期": "115/09/29"},
                       {"基金代號": "00982A", "單位淨值": "20.00", "資料日期": "115/09/26"},
                       ["00984A", "主動位置列", "12.00"]]}
    pn = parse_nav_rows(nav_d1)
    chk("淨值:dict 列 + 位置列、略過前一日淨值", pn["00981A"]["nav"] == 15.0 and pn["00981A"]["date"] == "2026-09-29"
        and pn["00982A"]["date"] == "2026-09-26" and pn["00984A"]["nav"] == 12.0, str(pn))
    s1 = snapshot_rows(["00981A", "00982A", "00983A"], pu, pn, {"00983A": {"aum": 3e8, "nav": 10.0}}, "2026-09-29T08:00:00+00:00", "2026-09-29")
    by = {r["etf_ticker"]: r for r in s1}
    chk("規模 = 單位數 × 淨值、官方 = OFFICIAL", by["00981A"]["aum"] == 15e6 and by["00981A"]["kind"] == "OFFICIAL")
    chk("Yahoo 後備 = ESTIMATE", by["00983A"]["kind"] == "ESTIMATE" and "YAHOO" in by["00983A"]["source"])
    chk("日期對不上 = ESTIMATE", by["00982A"]["kind"] == "ESTIMATE" and "DATE_MISMATCH" in by["00982A"]["source"])
    d2 = [dict(r, date="2026-09-30") for r in s1]
    d2[0].update(units_outstanding=1200000.0, nav=15.5, aum=1200000.0 * 15.5)          # 00981A +200k 單位
    d2[1].update(units_outstanding=450000.0, nav=20.0, aum=450000.0 * 20.0)            # 00982A −50k 單位
    d2[2].update(aum=3.3e8, nav=10.0)                                                   # 00983A 只有 AUM
    fl = {(r["etf_ticker"], r["date"]): r for r in compute_flows(s1 + d2, aum_flow=_eng("VDF_ENG096_ActiveETFMeasures").aum_flow)}
    a = fl[("00981A", "2026-09-30")]
    chk("流入:Δunits × NAV_t", a["net_units"] == 200000.0 and a["net_flow_value"] == 200000.0 * 15.5
        and a["inflow_value"] == 3.1e6 and a["outflow_value"] == 0.0 and a["kind"] == "ESTIMATE")
    b = fl[("00982A", "2026-09-30")]
    chk("流出:負淨額 → outflow", b["net_units"] == -50000.0 and b["outflow_value"] == 1e6 and b["inflow_value"] == 0.0)
    c = fl[("00983A", "2026-09-30")]
    chk("缺單位數 → ENG096 aum_flow(淨值不變,AUM +3000 萬)", c["net_units"] is None and abs(c["net_flow_value"] - 3e7) < 1e-6
        and "aum_flow" in c["source"])
    chk("首日無流量、毛申贖永遠 NULL(ABSENT)", fl[("00981A", "2026-09-29")]["net_flow_value"] is None
        and all(r["units_subscribed"] is None and r["units_redeemed"] is None for r in fl.values()))
    chk("欄位齊(etf_daily_metrics 表頭)", all(tuple(r) == METRICS_COLS for r in fl.values()))
    chk("來源冊:毛申贖 ABSENT、NAV 仍是 CANDIDATE", SOURCES["gross_subscriptions_redemptions"]["state"] == "ABSENT"
        and SOURCES["nav"]["state"] == "CANDIDATE")
    net = _FakeNet(units_d1, nav_d1)
    chk("沒有同意閘 = NO_CONSENT、零發包", fetch(Path("/nonexistent.duckdb"), net=net, env={})["state"] == "NO_CONSENT" and net.calls == [])
    hold = [{"portfolio_date": "2026-09-29", "etf_ticker": "00981A.TW", "holding_ticker": "2330", "holding_name": "台積電", "weight_pct": 9.0},
            {"portfolio_date": "2026-09-29", "etf_ticker": "00981A", "holding_ticker": "2454", "holding_name": "聯發科", "weight_pct": 5.0},
            {"portfolio_date": "2026-09-29", "etf_ticker": "00981A", "holding_ticker": "2317", "holding_name": "鴻海", "weight_pct": 4.0},
            {"portfolio_date": "2026-09-29", "etf_ticker": "00981A", "holding_ticker": "C_NTD", "holding_name": "現金", "weight_pct": 2.0},
            {"portfolio_date": "2026-09-29", "etf_ticker": "00981A", "holding_ticker": "9999", "holding_name": "未知", "weight_pct": 1.0}]
    bd = breakdown_rows(hold, {"2330": "半導體業", "2454": "半導體業", "2317": "其他電子業"})
    g = {(r["group_kind"], r["group"]): (r["weight_pct"], r["n_holdings"]) for r in bd}
    chk("產業配置:同產業加總、檔數", g[("industry", "半導體業")] == (14.0, 2) and g[("industry", "其他電子業")] == (4.0, 1)
        and g[("industry", "未分類")] == (1.0, 1) and g[("industry", "CASH")] == (2.0, 1), str(g))
    chk("資產配置:股票 / 現金", g[("asset", "STOCK_TW")] == (19.0, 4) and g[("asset", "CASH")] == (2.0, 1))
    chk("breakdown 欄位齊、ETF 去後綴", all(tuple(r) == BREAKDOWN_COLS and r["etf_ticker"] == "00981A" for r in bd))
    try:
        import duckdb
    except ImportError:
        duckdb = None
        chk("duckdb 缺:庫測略過(ABSENT,不算綠)", False)
    if duckdb is not None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "ActiveTWETF.duckdb"
            con = duckdb.connect(str(db))
            con.execute("CREATE TABLE holdings_daily(portfolio_date DATE, etf_ticker VARCHAR, holding_ticker VARCHAR, "
                        "holding_name VARCHAR, weight_pct DOUBLE)")
            con.executemany("INSERT INTO holdings_daily VALUES (CAST(? AS DATE),?,?,?,?)",
                            [(h["portfolio_date"], h["etf_ticker"], h["holding_ticker"], h["holding_name"], h["weight_pct"]) for h in hold]
                            + [("2026-09-26", "00981A", "2330", "台積電", 8.0)])
            con.close()
            tw = root / "tw.duckdb"
            con = duckdb.connect(str(tw))
            con.execute("CREATE TABLE tw_listings_industry(code VARCHAR, name VARCHAR, market VARCHAR, industry_name VARCHAR)")
            con.executemany("INSERT INTO tw_listings_industry VALUES (?,?,?,?)",
                            [("2330", "台積電", "TWSE", "半導體業"), ("2454", "聯發科", "TWSE", "半導體業"),
                             ("2317", "鴻海", "TWSE", "其他電子業"), ("6488", "環球晶", "TPEX", "半導體業")])
            con.close()
            res = breakdown(db, tw, apply=True)
            con = duckdb.connect(str(db), read_only=True)
            got = con.execute('SELECT "group", weight_pct FROM etf_breakdown WHERE group_kind=\'industry\' ORDER BY 1').fetchall()
            dates = con.execute("SELECT DISTINCT CAST(portfolio_date AS VARCHAR) FROM etf_breakdown").fetchall()
            con.close()
            chk("breakdown 落表(最新日;庫 × 產業)", res["written"] == len(res["rows"]) and ("半導體業", 14.0) in got
                and dates == [("2026-09-29",)] and res["unmapped_industry"] == ["9999"], str(got))
            net = _FakeNet(units_d1, nav_d1)
            r1 = fetch(db, apply=True, net=net, env={"VIA_NET_CONSENT": "YES"}, today="2026-09-29")
            units_d2 = [dict(units_d1[0], **{"發行單位數/轉換數": "1,200,000", "出表日期": "1150930"})]
            nav_d2 = {"data": [{"基金代號": "00981A", "單位淨值": "15.50", "資料日期": "115/09/30"}]}
            r2 = fetch(db, apply=True, net=_FakeNet(units_d2, nav_d2), env={"VIA_NET_CONSENT": "YES"}, today="2026-09-30")
            rows = read_metrics(db)
            last = [r for r in rows if r["etf_ticker"] == "00981A" and r["date"] == "2026-09-30"]
            chk("fetch(假網路)→ 落表 → 第二天從庫接前值算流量", r1["written"] and r2["written"] == 1 and last
                and last[0]["net_units"] == 200000.0 and last[0]["net_flow_value"] == 3.1e6, str(last))
            chk("fetch 只打兩條官方 URL(t187ap47_L · etfNav)", all("t187ap47_L" in u or "etfNav" in u for u in net.calls) and net.calls)
            chk("正庫不在 = 拒寫(不代建)", _raises(lambda: upsert_metrics(root / "nope.duckdb", r2["rows"])))
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        denied = main(["sources"]) == 2
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    chk("不經 VCGC 就拒跑", denied)
    bad = [(n, note) for n, ok, note in checks if not ok]
    for n, ok, note in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {n}" + (f" · {note}" if (note and not ok) else ""))
    print(f"[VDF_ENG094 v0101] {len(checks) - len(bad)}/{len(checks)}" + (" FAIL" if bad else " OK"))
    return 1 if bad else 0


def _raises(fn) -> bool:
    try:
        fn()
    except Exception:
        return True
    return False


def _opt(a: list, flag: str):
    return Path(a[a.index(flag) + 1]) if flag in a and a.index(flag) + 1 < len(a) else None


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or "selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = a[0] if a else "sources"
    db = _opt(a, "--db") or DB
    if verb == "sources":
        print(json.dumps(SOURCES, ensure_ascii=False, indent=1))
        return 0
    if verb == "fetch":
        res = fetch(db, apply="--apply" in a)
        print(json.dumps({k: v for k, v in res.items() if k != "rows"} | {"n": len(res.get("rows", [])),
                         "sample": res.get("rows", [])[:3]}, ensure_ascii=False, default=str))
        return 0 if res["state"] == "OK" else 2
    if verb == "metrics":
        rows = read_metrics(db)
        latest = {}
        for r in rows:
            latest[r["etf_ticker"]] = r
        print(json.dumps({"state": "OK" if latest else "NODATA", "db": str(db), "n_rows": len(rows),
                          "latest": list(latest.values())}, ensure_ascii=False, default=str))
        return 0 if latest else 2
    if verb == "breakdown":
        res = breakdown(db, _opt(a, "--tw-db"), apply="--apply" in a, all_dates="--all" in a)
        out = {k: v for k, v in res.items() if k != "rows"}
        out["sample"] = res["rows"][:12] if "--json" not in a else res["rows"]
        print(json.dumps(out, ensure_ascii=False, default=str))
        return 0 if res["state"] in ("OK", "AMBER") else 2
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
