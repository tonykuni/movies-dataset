#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG073_DataArchitecture — VDF 資料架構對映/盤點/最佳化計畫(批360;via-vdfarch)
====================================================================
操作員令「優化vdf資料架構 加入上船的加速器跟網路工具」「只增不減 最優最快的資料結構
搭配加速器及網路工具」。
律:
  對映   上船 SSOT(VIA_VDF_SSOT_b360 尾版;fetch_matrix 12 類+unified_headers 5 群+
         macro 219 序列+consensus E 段)→ 現役表/引擎/網路車道/加速器 逐類對映;不合併
         不取代現役(Zero-Hydra);每類誠實狀態:
         POPULATED(現役表有列)/PARTIAL(表在但缺 SSOT 欄群)/SCHEMA-ONLY(表在零列)/
         PLANNED(無表;有候源)/PENDING_KEY(候鑰)/PENDING_AUTH(候白名單)。
  盤點   DuckDB 全表 rows/日期欄/型別/min→max/最新距今;parquet 檔數;資料家接點。
  最佳化 --optimize 列計畫(只增不減):date VARCHAR→DATE(新表 *_typed 並存;不 DROP)、
         ORDER BY 叢集重寫、序列 parquet 鏡;預設 dry-run 只印;--go 才寫;寫入=
         CREATE TABLE <t>_typed AS … (原表零觸碰;ENG 尾版讀新表由各引擎自行 version-forward)。
  加速器 20 擷取真用面燈(ENG074 F01–F20)+ ACCEL/NET 橋覆蓋(git ls-files VDF py 掃)。
  輸出   ui_support/VIA_UI_VDFArchitecture_v0100.html(小字四分區矩陣;自適應)+
         registry/VIA_VDFArchitecture_v0100.json(冊)。
用法:python3 VDF_ENG073_DataArchitecture_v0100.py [build [--open] | plan | --optimize [--go] | --selftest]
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
import html
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"
UI = VIA / "supportive modules" / "ui_support"
REG = VIA / "supportive modules" / "registry"
PAGE = UI / "VIA_UI_VDFArchitecture_v0100.html"
BOOK = REG / "VIA_VDFArchitecture_v0100.json"
DBS = {"tw": OUT / "vdf_tw_market.duckdb", "gl": OUT / "vdf_global_market.duckdb",
       "etf": VDF / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings" / "ActiveTWETF.duckdb"}
DATE_COLS = ("date", "as_of", "published", "trade_date", "data_date")

# SSOT 12 類 → 現役(表@庫 / 引擎 glob / 網路車道 / 缺口)— 只增不減對映冊
MAP = {
    "tw_stock": {"tables": ["tw_daily_prices@tw", "tw_prices_adj@tw", "prices_canonical@tw", "features_daily@tw",
                            "tw_chip_inst@tw", "tw_chip_margin@tw", "tw_chip_derived@tw", "tw_daytrade_stock@tw", "tw_trading_daily@tw", "tw_valuation_daily@tw"],
                 "engines": ["VDF_ENG064_HistoryBackfill_v*.py", "VDF_ENG054_TWDailyBackfill_v*.py", "VDF_ENG060_AdjPriceLayer_v*.py",
                             "VDF_ENG056_ChipBackfill_v*.py", "VDF_ENG061_FeatureStore_v*.py", "VDF_ENG055_OmniFetch_v*.py"],
                 "lanes": ["yf_history", "yahoo_chart", "http_json(TWSE/TPEX rwd)"], "headers": ["prices_core", "tw_chip_extension"],
                 "gap": "chip 籌碼 2025-11-26 後待 ENG056 續跑;Turnover/Market_Cap 欄候 L2/L3 併表"},
    "tw_index": {"tables": ["global_daily@gl"], "engines": ["VDF_ENG066_GlobalUniverse_v*.py", "VDF_ENG055_OmniFetch_v*.py"],
                 "lanes": ["yahoo_chart(^TWII)", "http_json(TWSE 指數)"], "headers": ["prices_core"],
                 "gap": "^TWII/^TWOII 在 L6 global_daily;指數籌碼欄群=候源(TWSE 三大法人買賣金額 t86 已於 chip)"},
    "tw_etf_passive": {"tables": ["etf_book@tw", "etf_stats_daily@gl", "tw_daily_prices@tw"],
                       "engines": ["VDF_ENG055_OmniFetch_v*.py"], "lanes": ["http_json(t187ap47_L)", "yahoo_quote_summary"],
                       "headers": ["prices_core"], "gap": "被動 ETF 日價=tw_daily_prices 含(代碼在 listings);AUM/流量估算 L5"},
    "tw_etf_active": {"tables": ["active_tw_etf_universe@etf", "holdings_daily@etf", "holdings_changes@etf", "etf_book@tw"],
                      "engines": ["VDF_ENG051_ActiveTWETF_Holdings*.py", "VDF_ENG068_ETFConsensusAnalysis_v*.py"],
                      "lanes": ["http_text(投信 PCF)", "gsheet_csv"], "headers": ["prices_core", "D.canonical_schema"],
                      "gap": "ETF 庫 60 列/GroupIndex 0 檔候 etf_fetch(工作站)"},
    "intl_stock": {"tables": ["global_daily@gl", "gl_prices_adj@gl", "prices_canonical@gl"], "engines": ["VDF_ENG066_GlobalUniverse_v*.py"],
                   "lanes": ["yahoo_chart", "yf_history"], "headers": ["prices_core"], "gap": "SSOT 20 檔國際個股候併 ENG066 宇宙冊"},
    "intl_index": {"tables": ["global_daily@gl", "index_valuation_proxy@gl"], "engines": ["VDF_ENG066_GlobalUniverse_v*.py", "VDF_ENG055_OmniFetch_v*.py"],
                   "lanes": ["yahoo_chart", "yahoo_quote_summary"], "headers": ["prices_core"], "gap": ""},
    "tw_financials": {"tables": ["tw_monthly_revenue@tw", "monthly_revenue_analysis@tw"], "engines": ["VDF_ENG063_MonthlyRevenue_v*.py"],
                      "lanes": ["http_json(MOPS)"], "headers": ["tw_financial"],
                      "gap": "季報 23 欄(tw_financial 群)=PLANNED:MOPS t164sb04 候源;上船 vdf_fetchers_financials 設計參考"},
    "commodity": {"tables": ["global_daily@gl"], "engines": ["VDF_ENG066_GlobalUniverse_v*.py"], "lanes": ["yahoo_chart", "akshare_call"],
                  "headers": ["prices_core"], "gap": "SSOT 15 檔(期貨+現貨)候併 ENG066 宇宙冊;akshare 現貨=候白名單"},
    "fx": {"tables": ["global_daily@gl"], "engines": ["VDF_ENG066_GlobalUniverse_v*.py", "VDF_ENG055_OmniFetch_v*.py"],
           "lanes": ["yahoo_chart(=X)"], "headers": ["prices_core"], "gap": "L6 FX 15 對已含;P18 USD FX 模板 PENDING_OPERATOR"},
    "macro": {"tables": ["us_macro@gl", "macro_series_registry@gl", "cross_macro@gl", "tw_rates_cbc@tw"],
              "engines": ["VDF_ENG074_FredMacroSSOT_v*.py", "VDF_ENG055_OmniFetch_v*.py"],
              "lanes": ["http_json(FRED api;鑰)", "http_json(Eurostat)", "curl_json(CBC)"], "headers": ["macro"],
              "gap": "FRED 190 series=ENG074 從新往舊(候鑰);Treasury_FD 14/Fed scrape 2/ISM 12=PLANNED 候源"},
    "sentiment": {"tables": ["sentiment_daily@gl", "factset_earnings@gl"], "engines": ["VDF_ENG055_OmniFetch_v*.py"],
                  "lanes": ["http_json(CNN F&G)", "http_text(FactSet)"], "headers": ["sentiment"],
                  "gap": "AAII 4 序列=訂閱牆 PENDING_AUTH;CNN 5 序列 L11 已抓 score"},
    "shipping": {"tables": [], "engines": [], "lanes": ["http_json(候源)"], "headers": ["macro"],
                 "gap": "BDI/SCFI/CCFI 3 序列=PLANNED(候源:Baltic 付費/上海航交所 WAF)"},
}
KEY_STATES = {"macro": "PENDING_KEY", "sentiment": "PENDING_AUTH"}


# ---------------------------------------------------------------- SSOT
def ssot_dir() -> Path | None:
    hits = sorted((VDF / "references" / "intake").glob("VIA_VDF_SSOT_b*"))
    return hits[-1] if hits else None


def load_ssot() -> dict:
    d = ssot_dir()
    out = {"dir": d.name if d else "", "categories": [], "headers": {}, "macro_n": 0, "macro_fred": 0, "consensus_cols": 0}
    if not d:
        return out
    try:
        fm = json.loads((d / "vdf_fetch_matrix.json").read_text(encoding="utf-8"))
        out["headers"] = fm.get("unified_headers", {})
        for c in fm.get("categories", []):
            tk = c.get("tickers")
            out["categories"].append({"id": c["id"], "zh": c.get("name_zh", ""), "name": c.get("name", ""),
                                      "schema_group": c.get("schema_group", ""), "pk": c.get("primary_key", []),
                                      "freq": c.get("update_frequency", ""), "sources": c.get("data_sources", []),
                                      "n_targets": len(tk) if isinstance(tk, list) else c.get("indicators", 0),
                                      "output_file": c.get("output_file", "")})
    except Exception as exc:
        out["err_matrix"] = f"{type(exc).__name__}: {exc}"
    try:
        ms = json.loads((d / "macro_ssot.json").read_text(encoding="utf-8"))
        sr = [v for v in ms.get("series_registry", {}).values() if isinstance(v, dict)]
        out["macro_n"] = len(sr)
        out["macro_fred"] = sum(1 for v in sr if v.get("fred_id"))
    except Exception as exc:
        out["err_macro"] = f"{type(exc).__name__}: {exc}"
    try:
        cs = json.loads((d / "tw_consensus_ssot.json").read_text(encoding="utf-8"))
        e = cs.get("section_E", {})
        out["consensus_cols"] = sum(len(v) for k, v in e.items() if k.startswith("E") and isinstance(v, (list, dict)))
    except Exception:
        pass
    return out


# ---------------------------------------------------------------- 盤點
def inventory() -> dict:
    import duckdb
    inv = {}
    today = date.today()
    for tag, db in DBS.items():
        if not db.exists():
            inv[tag] = {"db": db.name, "exists": False, "tables": {}}
            continue
        tabs = {}
        try:
            con = duckdb.connect(str(db), read_only=True)
            for (t,) in con.execute("SHOW TABLES").fetchall():
                cols = con.execute(f"PRAGMA table_info('{t}')").fetchall()
                dc = next((c for c in cols if c[1] in DATE_COLS), None)
                n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                rec = {"rows": n, "cols": len(cols), "date_col": dc[1] if dc else "", "date_type": dc[2] if dc else "",
                       "min": "", "max": "", "lag_days": None}
                if dc and n:
                    try:
                        mn, mx = con.execute(f'SELECT CAST(MIN("{dc[1]}") AS VARCHAR), CAST(MAX("{dc[1]}") AS VARCHAR) FROM "{t}"').fetchone()
                        rec["min"], rec["max"] = mn or "", mx or ""
                        try:
                            rec["lag_days"] = (today - date.fromisoformat(mx[:10])).days
                        except Exception:
                            rec["lag_days"] = None
                    except Exception:
                        pass
                tabs[t] = rec
            con.close()
        except Exception as exc:
            inv[tag] = {"db": db.name, "exists": True, "tables": {}, "err": f"{type(exc).__name__}: {str(exc)[:80]}"}
            continue
        inv[tag] = {"db": db.name, "exists": True, "tables": tabs}
    return inv


def _newest(pat: str) -> str:
    hits = sorted(HERE.glob(pat))
    return hits[-1].name if hits else ""


def _lanes() -> set:
    hits = sorted((VIA / "supportive modules" / "network").glob("SUP_MDL740_NetUnified_v*.py"))
    if not hits:
        return set()
    import re
    return set(re.findall(r"^def ([a-z_]+)\(", hits[-1].read_text(encoding="utf-8", errors="ignore"), re.M))


def classify(cat: str, inv: dict, ssot_cat: dict | None) -> tuple[str, list]:
    m = MAP.get(cat, {"tables": [], "engines": [], "lanes": [], "headers": [], "gap": ""})
    rows = []
    for ref in m["tables"]:
        t, _, tag = ref.partition("@")
        rec = inv.get(tag, {}).get("tables", {}).get(t)
        rows.append({"table": t, "db": tag, "exists": rec is not None, "rows": rec["rows"] if rec else 0,
                     "max": rec["max"] if rec else "", "lag": rec["lag_days"] if rec else None,
                     "date_type": rec["date_type"] if rec else ""})
    if not m["tables"]:
        return ("PLANNED", rows)
    if not any(r["exists"] for r in rows):
        return (KEY_STATES.get(cat, "PLANNED"), rows)
    if cat == "macro" and not any(r["table"] == "us_macro" and r["rows"] for r in rows):
        return ("PENDING_KEY", rows)   # FRED 主表零列=候鑰(先於 SCHEMA-ONLY 判)
    if not any(r["rows"] for r in rows):
        return ("SCHEMA-ONLY", rows)
    # 主表(首列)有列且 SSOT 欄群完整才 POPULATED;缺口非空=PARTIAL
    populated = rows[0]["rows"] > 0
    return ("POPULATED" if populated and not m["gap"] else "PARTIAL", rows)


def _date_expr(col: str) -> str:
    """VARCHAR 日期→DATE(ISO 直轉;ROC 7 碼 1150903→2026-09-03;緊湊 8 碼;其餘 TRY_CAST=NULL 誠實)"""
    c = f'"{col}"'
    return (f"CASE WHEN regexp_matches({c}, '^\\d{{7}}$') THEN make_date(1911 + CAST(substr({c}, 1, 3) AS INTEGER), "
            f"CAST(substr({c}, 4, 2) AS INTEGER), CAST(substr({c}, 6, 2) AS INTEGER)) "
            f"WHEN regexp_matches({c}, '^\\d{{8}}$') THEN CAST(strptime({c}, '%Y%m%d') AS DATE) "
            f"ELSE TRY_CAST({c} AS DATE) END")


def optimize_plan(inv: dict) -> list[dict]:
    """只增不減:VARCHAR 日期表→ *_typed 並存;大表叢集;序列 parquet 鏡"""
    plan = []
    for tag, d in inv.items():
        for t, rec in d.get("tables", {}).items():
            if rec["date_col"] and rec["date_type"].upper() == "VARCHAR" and rec["rows"] > 0:
                plan.append({"db": tag, "table": t, "action": "TYPED_MIRROR", "rows": rec["rows"],
                             "sql": f'CREATE TABLE IF NOT EXISTS "{t}_typed" AS SELECT * REPLACE ({_date_expr(rec["date_col"])} AS "{rec["date_col"]}") '
                                    f'FROM "{t}" ORDER BY "{rec["date_col"]}"',
                             "why": f'{rec["date_col"]} VARCHAR→DATE(ISO/ROC 7 碼/緊湊 8 碼皆轉;zone-map 掃描/區間查詢加速);原表零觸碰'})
            if rec["rows"] >= 100_000:
                plan.append({"db": tag, "table": t, "action": "CLUSTER_PARQUET", "rows": rec["rows"],
                             "sql": f'COPY (SELECT * FROM "{t}" ORDER BY {"ticker, " if True else ""}"{rec["date_col"] or "1"}") TO \'<mega>/arch/{t}.parquet\' (FORMAT PARQUET, COMPRESSION ZSTD)',
                             "why": "大表 zstd 叢集 parquet 鏡(polars/duckdb 零複製掃;跨機共享)"})
    return plan


def apply_plan(plan: list[dict], do_print: bool = True) -> dict:
    import duckdb
    done, fail = 0, 0
    (OUT / "arch").mkdir(parents=True, exist_ok=True)
    for p in plan:
        db = DBS[p["db"]]
        sql = p["sql"].replace("<mega>", str(OUT).replace("\\", "/"))
        if p["action"] == "CLUSTER_PARQUET":
            # ORDER BY ticker 欄缺=退 date
            try:
                con = duckdb.connect(str(db), read_only=True)
                cols = {c[1] for c in con.execute(f"PRAGMA table_info('{p['table']}')").fetchall()}
                con.close()
            except Exception:
                cols = set()
            if "ticker" not in cols and "code" not in cols:
                sql = sql.replace("ORDER BY ticker, ", "ORDER BY ")
            elif "ticker" not in cols:
                sql = sql.replace("ORDER BY ticker, ", "ORDER BY code, ")
        try:
            con = duckdb.connect(str(db))
            con.execute(sql)
            con.close()
            done += 1
            if do_print:
                print(f"  [OK  ] {p['action']} {p['table']}", flush=True)
        except Exception as exc:
            fail += 1
            if do_print:
                print(f"  [FAIL] {p['action']} {p['table']} {type(exc).__name__}: {str(exc)[:80]}", flush=True)
    return {"done": done, "fail": fail}


def bridge_coverage() -> dict:
    """ACCEL/NET 橋覆蓋(git ls-files VDF py;在冊律)"""
    try:
        r = subprocess.run(["git", "ls-files", "--", str(VDF.relative_to(VIA.parent)) + "/*.py"], cwd=str(VIA.parent),
                           capture_output=True, text=True, timeout=60)
        files = [VIA.parent / f for f in r.stdout.splitlines() if f.endswith(".py") and "references/intake" not in f and "RetiredEngines" not in f]
    except Exception:
        files = []
    a = n = 0
    for f in files:
        try:
            s = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        a += "[VIA:ACCEL-BRIDGE" in s
        n += "[VIA:NET-BRIDGE" in s
    return {"files": len(files), "accel": a, "net": n}


def fetch_lamps() -> list[dict]:
    try:
        import importlib.util as _il
        hits = sorted(HERE.glob("VDF_ENG074_FredMacroSSOT_v*.py"))
        if not hits:
            return []
        spec = _il.spec_from_file_location("eng074_dyn", hits[-1])
        m = _il.module_from_spec(spec)
        spec.loader.exec_module(m)
        try:
            import polars  # noqa: F401
            pol = "ACTIVE"
        except ImportError:
            pol = "FALLBACK"
        st = {"F02": "ACTIVE" if m.VIA_ACCEL is not None else "FALLBACK", "F09": pol,
              "F10": "ACTIVE" if m.VIA_NET_TOOL_PATH else "MISSING", "F01": "ACTIVE" if m.ssot_path() else "FALLBACK"}
        return [{"id": f[0], "name": f[1], "mech": f[2], "a": f[3], "state": st.get(f[0], "ACTIVE")} for f in m.FETCH_ACCEL]
    except Exception:
        return []


def data_home() -> dict:
    try:
        import importlib.util as _il
        hits = sorted(REG.glob("CGC_MDL123_DataHome_v0*.py"))
        if not hits:
            return {"home": "", "src": "MDL123 缺", "linked": False}
        spec = _il.spec_from_file_location("m123_dyn2", hits[-1])
        m = _il.module_from_spec(spec)
        spec.loader.exec_module(m)
        home, src = m.resolve_home(VIA)
        hub = OUT.parent
        linked = hub.is_symlink() or (os.name == "nt" and hub.exists() and str(hub.resolve()).lower() != str(hub).lower())
        return {"home": str(home), "src": src, "linked": bool(linked)}
    except Exception as exc:
        return {"home": "", "src": f"解析敗 {type(exc).__name__}", "linked": False}


# ---------------------------------------------------------------- 建冊
def build(do_print: bool = True) -> dict:
    t0 = time.time()
    ssot = load_ssot()
    inv = inventory()
    lanes = _lanes()
    cats = []
    ids = [c["id"] for c in ssot["categories"]] or list(MAP)
    for cid in ids:
        sc = next((c for c in ssot["categories"] if c["id"] == cid), None)
        state, rows = classify(cid, inv, sc)
        m = MAP.get(cid, {"tables": [], "engines": [], "lanes": [], "headers": [], "gap": ""})
        eng = [{"pat": e, "file": _newest(e), "ok": bool(_newest(e))} for e in m["engines"]]
        ln = [{"lane": x, "ok": x.split("(")[0] in lanes} for x in m["lanes"]]
        cats.append({"id": cid, "zh": (sc or {}).get("zh", cid), "state": state, "n_targets": (sc or {}).get("n_targets", 0),
                     "schema_group": (sc or {}).get("schema_group", ""), "pk": (sc or {}).get("pk", []),
                     "freq": (sc or {}).get("freq", ""), "sources": (sc or {}).get("sources", []),
                     "tables": rows, "engines": eng, "lanes": ln, "headers": m["headers"], "gap": m["gap"]})
    plan = optimize_plan(inv)
    n_tables = sum(len(d.get("tables", {})) for d in inv.values())
    n_rows = sum(r["rows"] for d in inv.values() for r in d.get("tables", {}).values())
    varchar_dates = sum(1 for d in inv.values() for r in d.get("tables", {}).values() if r["date_type"].upper() == "VARCHAR")
    tally = {k: sum(1 for c in cats if c["state"] == k) for k in ("POPULATED", "PARTIAL", "SCHEMA-ONLY", "PLANNED", "PENDING_KEY", "PENDING_AUTH")}
    rep = {"engine": "VDF_ENG073_DataArchitecture_v0100", "stamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
           "ssot": ssot, "data_home": data_home(), "inventory": inv, "categories": cats, "tally": tally,
           "kpi": {"tables": n_tables, "rows": n_rows, "varchar_date_tables": varchar_dates, "ssot_categories": len(ids),
                   "macro_series": ssot["macro_n"], "macro_fred": ssot["macro_fred"], "parquet_files": len(list(OUT.glob("*.parquet"))) if OUT.exists() else 0},
           "optimize_plan": plan, "fetch_accel": fetch_lamps(), "bridge": bridge_coverage(),
           "lanes_available": sorted(x for x in lanes if not x.startswith("_")), "elapsed_s": round(time.time() - t0, 2),
           "rules": ["只增不減:對映冊不合併不取代現役;最佳化=並存 *_typed/parquet 鏡;原表零 DROP",
                     "誠實三態:POPULATED/PARTIAL/SCHEMA-ONLY/PLANNED/PENDING_KEY/PENDING_AUTH 依實表列數與缺口判",
                     "鑰匙紅線:FRED 鑰僅 env 或 output_hub/mega/.fred_api_key(gitignored);SSOT 收容件明文鑰已遮罩",
                     "Zero-Hydra:上船 vdf_api(8765=DeckServer 樞紐 port 撞)不啟用;vdf_supportive_bridge 不重掛(在庫橋已承接)"]}
    BOOK.parent.mkdir(parents=True, exist_ok=True)
    BOOK.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(render(rep), encoding="utf-8")
    if do_print:
        print(f"=== VDF 資料架構(ENG073)· {rep['stamp']} ===")
        print(f"  資料家 {rep['data_home']['home']}({rep['data_home']['src']};接點 {'LINKED' if rep['data_home']['linked'] else 'UNLINKED'})")
        print(f"  SSOT {ssot['dir'] or '缺'} · 類 {len(ids)} · macro {ssot['macro_n']}(FRED {ssot['macro_fred']}) · 表 {n_tables} · 列 {n_rows:,} · VARCHAR 日期表 {varchar_dates}")
        for c in cats:
            main = c["tables"][0] if c["tables"] else None
            mrows = (f"{main['rows']:>8} 列" if main and main["exists"] else "     缺 ")
            print(f"  [{c['state']:<11}] {c['id']:<15} {c['zh'][:12]:<12} 主表 {main['table'] if main else '-':<22} {mrows} "
                  f"→{main['max'] if main else ''} 引擎 {sum(1 for e in c['engines'] if e['ok'])}/{len(c['engines'])} 車道 {sum(1 for l in c['lanes'] if l['ok'])}/{len(c['lanes'])}")
        print(f"  [計] {' · '.join(f'{k} {v}' for k, v in tally.items())} · 最佳化計畫 {len(plan)} 項(dry-run) · 橋 ACCEL {rep['bridge']['accel']}/{rep['bridge']['files']} NET {rep['bridge']['net']}/{rep['bridge']['files']}")
        print(f"  頁 {PAGE.name} · 冊 {BOOK.name} · {rep['elapsed_s']}s")
    return rep


# ---------------------------------------------------------------- 頁(小字四分區矩陣)
def render(r: dict) -> str:
    e = html.escape

    def b(s):
        c = {"POPULATED": "gr", "PARTIAL": "ye", "SCHEMA-ONLY": "ye", "PLANNED": "gy", "PENDING_KEY": "rd", "PENDING_AUTH": "rd",
             "ACTIVE": "gr", "FALLBACK": "ye", "MISSING": "rd"}.get(s, "gy")
        return f'<span class="b {c}">{e(s)}</span>'
    def tcell(t):
        if not t["exists"]:
            return '<span class=dim>' + e(t["table"]) + "@" + t["db"] + " 缺</span>"
        return e(t["table"]) + "@" + t["db"] + " " + f'{t["rows"]:,}' + "→" + e(t["max"])

    def mark(ok):
        return "✓" if ok else "✗"

    def crow_one(c):
        tabs = "<br>".join(tcell(t) for t in c["tables"]) or "<span class=dim>—</span>"
        engs = "<br>".join(mark(x["ok"]) + " " + e(x["file"] or x["pat"]) for x in c["engines"]) or "<span class=dim>—</span>"
        lns = "<br>".join(mark(x["ok"]) + " " + e(x["lane"]) for x in c["lanes"])
        return ('<tr><td class="m">' + e(c["id"]) + "</td><td>" + e(c["zh"]) + '</td><td class="c">' + b(c["state"])
                + '</td><td class="c m">' + str(c["n_targets"]) + '</td><td class="m">' + tabs + '</td><td class="m">' + engs
                + '</td><td class="m">' + lns + '</td><td class="dim">' + e(c["gap"]) + "</td></tr>")
    crow = "".join(crow_one(c) for c in r["categories"])

    def trow_one(tag, t, v):
        dt = v["date_type"].upper()
        badge = b("PARTIAL") if dt == "VARCHAR" else (b("POPULATED") if dt else "<span class=dim>—</span>")
        lag = "" if v["lag_days"] is None else str(v["lag_days"])
        return ('<tr><td class="m">' + tag + '</td><td class="m">' + e(t) + '</td><td class="c m">' + f'{v["rows"]:,}'
                + '</td><td class="c m">' + str(v["cols"]) + '</td><td class="m">' + e(v["date_col"]) + '</td><td class="c">' + badge
                + ' <span class="dim">' + e(v["date_type"]) + '</span></td><td class="m">' + e(v["min"]) + "→" + e(v["max"])
                + '</td><td class="c m">' + lag + "</td></tr>")
    trow = "".join(trow_one(tag, t, v) for tag, d in r["inventory"].items() for t, v in sorted(d.get("tables", {}).items()))
    prow = "".join('<tr><td class="m">' + e(p["db"]) + '</td><td class="m">' + e(p["table"]) + '</td><td class="c">' + e(p["action"])
                   + '</td><td class="c m">' + f'{p["rows"]:,}' + '</td><td class="dim">' + e(p["why"]) + "</td></tr>"
                   for p in r["optimize_plan"])
    arow = "".join(f'<tr><td class="m">{a["id"]}</td><td>{e(a["name"])}</td><td class="c">{b(a["state"])}</td><td class="m">{e(a["a"])}</td><td class="dim">{e(a["mech"])}</td></tr>'
                   for a in r["fetch_accel"])
    k = r["kpi"]
    dh = r["data_home"]
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · VDF 資料架構</title>
<style>:root{{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}}*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}}
.wrap{{max-width:1500px;margin:0 auto;padding:18px 14px 48px}}h1{{font-size:14px;margin:0}}.sub{{color:var(--mu);margin:3px 0 14px}}
h2{{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}}
.nav a{{color:#7dd3fc;margin-right:12px;text-decoration:none}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:14px}}.kpi{{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}}.kpi .n{{font-size:17px;font-weight:600}}.kpi .l{{font-size:10px;color:var(--mu)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}@media(max-width:1100px){{.grid{{grid-template-columns:1fr}}}}
table{{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}}th{{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}}td{{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}}td.c{{text-align:center}}.m{{font-family:ui-monospace,Consolas,monospace;font-size:10px}}.dim{{color:var(--mu)}}
.b{{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}}.gr{{background:#064e3b;color:#34d399;border-color:#059669}}.ye{{background:#78350f;color:#fde047;border-color:#d97706}}.rd{{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}}.gy{{background:#1f2937;color:#9ca3af;border-color:#374151}}
.note{{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}}</style></head><body><div class="wrap">
<h1>VDF DATA ARCHITECTURE · SSOT × TABLES × ENGINES × LANES × 20 FETCH ACCELERATORS</h1>
<p class="sub">{e(r["engine"])} · {e(r["stamp"])} · SSOT {e(r["ssot"]["dir"] or "缺")} · 資料家 {e(dh["home"])}({e(dh["src"])};接點 {"LINKED" if dh["linked"] else "UNLINKED"}) · {r["elapsed_s"]} s</p>
<p class="nav"><a href="VIA_UI_Consolidated_v0100.html">整</a><a href="VIA_UI_SystemCharter_v0100.html">冊</a><a href="VIA_UI_LifecycleRACI_v0100.html">環</a><a href="VIA_UI_IntakeRoster_v0100.html">收容</a><a href="VIA_UI_MasterControl_v0100.html">總控</a></p>
<div class="kpis"><div class="kpi"><div class="n">{k["ssot_categories"]}</div><div class="l">SSOT categories</div></div><div class="kpi"><div class="n">{k["tables"]}</div><div class="l">duckdb tables</div></div>
<div class="kpi"><div class="n">{k["rows"]:,}</div><div class="l">rows</div></div><div class="kpi"><div class="n">{k["macro_fred"]}/{k["macro_series"]}</div><div class="l">FRED / macro series</div></div>
<div class="kpi"><div class="n">{r["tally"]["POPULATED"]}+{r["tally"]["PARTIAL"]}</div><div class="l">populated + partial</div></div><div class="kpi"><div class="n">{r["tally"]["PENDING_KEY"] + r["tally"]["PENDING_AUTH"]}</div><div class="l">pending key/auth</div></div>
<div class="kpi"><div class="n">{k["varchar_date_tables"]}</div><div class="l">VARCHAR date tables (plan)</div></div><div class="kpi"><div class="n">{r["bridge"]["accel"]}/{r["bridge"]["files"]}</div><div class="l">ACCEL bridge · NET {r["bridge"]["net"]}</div></div></div>
<h2>MODULE — SSOT 12 categories → active tables / engines / lanes (honest state)</h2>
<table><colgroup><col style="width:7%"><col style="width:8%"><col style="width:7%"><col style="width:4%"><col style="width:24%"><col style="width:18%"><col style="width:13%"><col style="width:19%"></colgroup>
<thead><tr><th>SSOT</th><th>類</th><th>state</th><th>n</th><th>tables@db rows→max</th><th>engines (tail)</th><th>net lanes</th><th>gap (honest)</th></tr></thead><tbody>{crow}</tbody></table>
<div class="grid"><div>
<h2>DATA — duckdb inventory (rows / date column / type / range / lag days)</h2>
<table><colgroup><col style="width:5%"><col style="width:27%"><col style="width:11%"><col style="width:6%"><col style="width:10%"><col style="width:15%"><col style="width:20%"><col style="width:6%"></colgroup>
<thead><tr><th>db</th><th>table</th><th>rows</th><th>cols</th><th>date col</th><th>type</th><th>min→max</th><th>lag</th></tr></thead><tbody>{trow}</tbody></table>
</div><div>
<h2>FUNCTION-LIB — 20 fetch accelerators (ENG074; real-use lamps)</h2>
<table><colgroup><col style="width:7%"><col style="width:18%"><col style="width:12%"><col style="width:8%"><col style="width:55%"></colgroup>
<thead><tr><th>ID</th><th>name</th><th>state</th><th>↔A</th><th>mechanism</th></tr></thead><tbody>{arow or '<tr><td colspan="5" class="dim">ENG074 缺</td></tr>'}</tbody></table>
<h2>PLAN — optimize (add-only; dry-run; <span class="m">--optimize --go</span> to apply)</h2>
<table><colgroup><col style="width:6%"><col style="width:26%"><col style="width:16%"><col style="width:12%"><col style="width:40%"></colgroup>
<thead><tr><th>db</th><th>table</th><th>action</th><th>rows</th><th>why</th></tr></thead><tbody>{prow or '<tr><td colspan="5" class="dim">無計畫項</td></tr>'}</tbody></table>
</div></div>
<div class="note"><b>RULES</b><br>{"<br>".join(e(x) for x in r["rules"])}<br>lanes: <span class="m">{e(", ".join(r["lanes_available"]))}</span></div>
</div></body></html>"""


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    global OUT, DBS, PAGE, BOOK
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 對映冊 12 類齊(=SSOT fetch_matrix 12 類;每類 headers/gap 在)", len(MAP) == 12 and all("gap" in v and v["headers"] for v in MAP.values()))
    s = load_ssot()
    chk("② SSOT 尾版動態載入(12 類/5 欄群/macro 219·FRED 190)或誠實缺",
        (not s["dir"]) or (len(s["categories"]) == 12 and len(s["headers"]) == 5 and s["macro_fred"] >= 150), f"{s['dir']} {len(s['categories'])} {s['macro_fred']}")
    _s = (OUT, dict(DBS), PAGE, BOOK)
    with tempfile.TemporaryDirectory() as td:
        import duckdb
        OUT = Path(td)
        DBS = {"tw": OUT / "tw.duckdb", "gl": OUT / "gl.duckdb", "etf": OUT / "etf.duckdb"}
        PAGE, BOOK = OUT / "p.html", OUT / "b.json"
        con = duckdb.connect(str(DBS["tw"]))
        con.execute("CREATE TABLE tw_daily_prices (date VARCHAR, ticker VARCHAR, close DOUBLE)")
        con.execute("INSERT INTO tw_daily_prices VALUES ('2026-09-01','2330',1.0),('2026-09-03','2330',2.0)")
        con.execute("CREATE TABLE tw_monthly_revenue (code VARCHAR, v DOUBLE)")
        con.close()
        con = duckdb.connect(str(DBS["gl"]))
        con.execute("CREATE TABLE us_macro (date DATE, series VARCHAR, value DOUBLE)")
        con.close()
        inv = inventory()
        chk("③ 盤點(rows/date 欄/型別/min→max/lag;缺庫誠實 exists=False)",
            inv["tw"]["tables"]["tw_daily_prices"]["rows"] == 2 and inv["tw"]["tables"]["tw_daily_prices"]["date_type"].upper() == "VARCHAR"
            and inv["tw"]["tables"]["tw_daily_prices"]["max"] == "2026-09-03" and inv["etf"]["exists"] is False)
        st_stock, _ = classify("tw_stock", inv, None)
        st_macro, _ = classify("macro", inv, None)
        st_ship, _ = classify("shipping", inv, None)
        st_etf, _ = classify("tw_etf_active", inv, None)
        chk("④ 誠實狀態(有列+缺口=PARTIAL;us_macro 零列=PENDING_KEY;無表=PLANNED;候鑰/白名單分流)",
            st_stock == "PARTIAL" and st_macro == "PENDING_KEY" and st_ship == "PLANNED" and st_etf == "PLANNED", f"{st_stock}/{st_macro}/{st_ship}/{st_etf}")
        plan = optimize_plan(inv)
        chk("⑤ 最佳化計畫只增不減(VARCHAR 日期→*_typed 並存;零 DROP;預設 dry-run)",
            any(p["action"] == "TYPED_MIRROR" and p["table"] == "tw_daily_prices" for p in plan) and not any("DROP" in p["sql"].upper() for p in plan))
        r = apply_plan(plan, do_print=False)
        con = duckdb.connect(str(DBS["tw"]), read_only=True)
        typed = {c[1]: c[2] for c in con.execute("PRAGMA table_info('tw_daily_prices_typed')").fetchall()}
        n0 = con.execute("SELECT COUNT(*) FROM tw_daily_prices").fetchone()[0]
        con.close()
        chk("⑥ --go 落地(typed 鏡 DATE;原表列數不變)", r["done"] >= 1 and r["fail"] == 0 and typed.get("date", "").upper() == "DATE" and n0 == 2)
        rep = build(do_print=False)
        chk("⑦ 頁+冊(四分區 MODULE/DATA/FUNCTION-LIB/PLAN;小字;導航 整/冊/環)",
            PAGE.exists() and BOOK.exists() and all(x in PAGE.read_text(encoding="utf-8") for x in ("MODULE", "DATA", "FUNCTION-LIB", "PLAN", "font:11px", "VIA_UI_LifecycleRACI_v0100.html"))
            and len(rep["categories"]) == 12)
        chk("⑧ 20 擷取加速器燈(ENG074 F01–F20 動態載入)", len(rep["fetch_accel"]) == 20 or not sorted(HERE.glob("VDF_ENG074_*.py")), f"{len(rep['fetch_accel'])}")
    OUT, DBS, PAGE, BOOK = _s[0], _s[1], _s[2], _s[3]
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 鑰匙紅線+Zero-Hydra 宣告(源碼零明文鑰;vdf_api 不啟用;不合併現役)",
        not any(len(t) == 32 and all(c in "0123456789abcdef" for c in t) for t in src.replace("(", " ").replace(")", " ").split())
        and "不啟用" in src and "不取代現役" in src)
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VDF 資料架構(VDF_ENG073)· 九檢自測 ===")
        return selftest()
    if "--optimize" in a:
        inv = inventory()
        plan = optimize_plan(inv)
        print(f"=== 最佳化計畫(只增不減;{'GO' if '--go' in a else 'dry-run'})· {len(plan)} 項 ===")
        for p in plan:
            print(f"  [{p['action']:<15}] {p['db']}.{p['table']:<28} {p['rows']:>9,} 列 · {p['why']}")
        if "--go" in a:
            r = apply_plan(plan)
            print(f"  [計] 落地 {r['done']} · FAIL {r['fail']}")
            build(do_print=False)
            return 1 if r["fail"] else 0
        print("  (dry-run;--go 才寫;寫入=並存 *_typed/parquet 鏡,原表零觸碰)")
        return 0
    if not a or a[0] in ("build", "plan"):
        build()
        if "--open" in a:
            try:
                import webbrowser
                webbrowser.open(PAGE.as_uri())
            except Exception:
                pass
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
