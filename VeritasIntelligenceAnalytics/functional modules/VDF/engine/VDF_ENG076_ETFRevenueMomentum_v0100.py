#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG076_ETFRevenueMomentum — 主動 ETF 持股 × 月營收動能(批373;via-etfrev)
====================================================================
操作員令(批373)「For active Taiwan stock ETF analysis and Taiwan monthly revenue analysis, please complete this project」。
兩專案合流層(零網路;全讀在庫真值):
  來源  ActiveTWETF.duckdb holdings_daily(每檔 ETF 最新 portfolio_date 持股權重)
        vdf_tw_market.duckdb monthly_revenue_analysis(ENG063 視圖:最新有 yoy 覆蓋之月 yoy_pct/mom_pct/yoy_streak/high_60m)
  ETF 層  持股數 · 營收覆蓋權重% · 權重加權 yoy · yoy 中位 · 正年增權重佔比 · 加權月增 · 60 月新高權重佔比 · 排名;
          加權律=僅覆蓋權重入分母(w_cov>0 才有值;NULL 誠實)
  個股層  營收動能 × 被持 ETF 數 × 合計權重(重疊榜)
  落庫  DB_TW 表 etf_revenue_momentum(anti-join 鍵 etf_ticker,asof_ym,portfolio_date;只增)+ etf_revenue_holdings
  存證  VIA_Reports/etf_revenue_momentum/ETF_REVENUE_<ym>.json;頁 ui_support/VIA_UI_ETFRevenueMomentum_v0100.html(手機單欄;零 CDN)
  誠實  持股庫缺/營收視圖缺=SKIP;覆蓋 <50% 標 LOW_COVERAGE;史深不足(yoy_streak 需 ≥13 月)標註
用法:python3 VDF_ENG076_ETFRevenueMomentum_v0100.py run | status | --selftest
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
import html
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
DB_TW = VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DB_ETF = VDF / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings" / "ActiveTWETF.duckdb"
REP = VIA / "VIA_Reports" / "etf_revenue_momentum"
OUT_UI = VIA / "supportive modules" / "ui_support" / "VIA_UI_ETFRevenueMomentum_v0100.html"
T_ETF = "etf_revenue_momentum"
T_HOLD = "etf_revenue_holdings"


def _con(db: Path, ro: bool = True):
    import duckdb
    return duckdb.connect(str(db), read_only=ro)


def latest_revenue_month(con) -> str | None:
    """最新「yoy 覆蓋 ≥50%」之月(誠實:快照未齊之月不採)"""
    rows = con.execute("""SELECT ym, COUNT(*) n, SUM(CASE WHEN yoy_pct IS NOT NULL THEN 1 ELSE 0 END) ny
                          FROM monthly_revenue_analysis GROUP BY ym ORDER BY ym DESC""").fetchall()
    for ym, n, ny in rows:
        if n and ny / n >= 0.5:
            return ym
    return rows[0][0] if rows else None


def compute() -> dict:
    if not DB_ETF.exists():
        return {"state": "SKIP", "note": "ActiveTWETF.duckdb 缺(先 etf_fetch)"}
    if not DB_TW.exists():
        return {"state": "SKIP", "note": "vdf_tw_market.duckdb 缺"}
    ce = _con(DB_ETF)
    try:
        hold = ce.execute("""SELECT h.etf_ticker, h.etf_name, h.portfolio_date, h.holding_ticker, h.holding_name, h.weight_pct
                             FROM holdings_daily h JOIN (SELECT etf_ticker, MAX(portfolio_date) d FROM holdings_daily GROUP BY 1) m
                             ON h.etf_ticker = m.etf_ticker AND h.portfolio_date = m.d
                             WHERE h.weight_pct IS NOT NULL AND h.holding_ticker IS NOT NULL""").fetchall()
    finally:
        ce.close()
    if not hold:
        return {"state": "SKIP", "note": "持股庫零列"}
    ct = _con(DB_TW)
    try:
        tabs = {t for (t,) in ct.execute("SHOW TABLES").fetchall()}
        if "monthly_revenue_analysis" not in tabs:
            return {"state": "SKIP", "note": "monthly_revenue_analysis 視圖缺(先 revenue)"}
        ym = latest_revenue_month(ct)
        if not ym:
            return {"state": "SKIP", "note": "營收視圖零列"}
        rev = {r[0]: {"yoy": r[1], "mom": r[2], "streak": r[3], "high60": r[4], "revenue": r[5]} for r in ct.execute(
            "SELECT code, yoy_pct, mom_pct, yoy_streak, high_60m, revenue FROM monthly_revenue_analysis WHERE ym = ?", [ym]).fetchall()}
        n_months = ct.execute("SELECT COUNT(DISTINCT ym) FROM monthly_revenue_analysis").fetchone()[0]
    finally:
        ct.close()
    by = {}
    for et, en, pd_, ht, hn, w in hold:
        code = str(ht).split(".")[0].strip()
        d = by.setdefault(et, {"etf_ticker": et, "etf_name": en, "portfolio_date": str(pd_), "rows": []})
        d["rows"].append({"code": code, "name": hn, "w": float(w), "rev": rev.get(code)})
    etfs, hold_rows = [], []
    for et, d in by.items():
        rows = d["rows"]
        w_all = sum(r["w"] for r in rows)
        cov = [r for r in rows if r["rev"] and r["rev"]["yoy"] is not None]
        w_cov = sum(r["w"] for r in cov)
        rec = {"etf_ticker": et, "etf_name": d["etf_name"], "portfolio_date": d["portfolio_date"], "asof_ym": ym,
               "n_holdings": len(rows), "w_total": round(w_all, 2), "cov_w": round(100.0 * w_cov / w_all, 1) if w_all else None,
               "w_yoy": None, "med_yoy": None, "pos_share_w": None, "w_mom": None, "high60_share_w": None, "avg_streak": None,
               "top": [], "flag": ""}
        if w_cov > 0:
            rec["w_yoy"] = round(100.0 * sum(r["w"] * r["rev"]["yoy"] for r in cov) / w_cov, 2)
            ys = sorted(r["rev"]["yoy"] for r in cov)
            rec["med_yoy"] = round(100.0 * ys[len(ys) // 2], 2)
            rec["pos_share_w"] = round(100.0 * sum(r["w"] for r in cov if r["rev"]["yoy"] > 0) / w_cov, 1)
            mom = [r for r in cov if r["rev"]["mom"] is not None]
            wm = sum(r["w"] for r in mom)
            rec["w_mom"] = round(100.0 * sum(r["w"] * r["rev"]["mom"] for r in mom) / wm, 2) if wm else None
            rec["high60_share_w"] = round(100.0 * sum(r["w"] for r in cov if r["rev"]["high60"]) / w_cov, 1)
            rec["avg_streak"] = round(sum((r["rev"]["streak"] or 0) for r in cov) / len(cov), 1)
            rec["top"] = [{"code": r["code"], "name": r["name"], "w": round(r["w"], 2), "yoy": round(100.0 * r["rev"]["yoy"], 1)}
                          for r in sorted(cov, key=lambda r: r["w"] * r["rev"]["yoy"], reverse=True)[:3]]
        if rec["cov_w"] is not None and rec["cov_w"] < 50:
            rec["flag"] = "LOW_COVERAGE"
        etfs.append(rec)
        for r in rows:
            hold_rows.append({"etf_ticker": et, "asof_ym": ym, "portfolio_date": d["portfolio_date"], "code": r["code"], "name": r["name"],
                              "w": round(r["w"], 3), "yoy": (round(100.0 * r["rev"]["yoy"], 2) if r["rev"] and r["rev"]["yoy"] is not None else None),
                              "mom": (round(100.0 * r["rev"]["mom"], 2) if r["rev"] and r["rev"]["mom"] is not None else None),
                              "streak": (r["rev"]["streak"] if r["rev"] else None), "high60": (r["rev"]["high60"] if r["rev"] else None)})
    ranked = sorted([e for e in etfs if e["w_yoy"] is not None], key=lambda e: e["w_yoy"], reverse=True)
    for i, e in enumerate(ranked, 1):
        e["rank"] = i
    # 個股重疊榜:被持 ETF 數 × 合計權重 × 營收動能
    agg = {}
    for h in hold_rows:
        a = agg.setdefault(h["code"], {"code": h["code"], "name": h["name"], "n_etf": 0, "w_sum": 0.0, "yoy": h["yoy"], "streak": h["streak"], "high60": h["high60"]})
        a["n_etf"] += 1
        a["w_sum"] = round(a["w_sum"] + h["w"], 2)
    overlap = sorted([a for a in agg.values() if a["yoy"] is not None], key=lambda a: (a["n_etf"], a["w_sum"]), reverse=True)[:30]
    return {"state": "OK", "asof_ym": ym, "n_months": n_months, "etfs": sorted(etfs, key=lambda e: e.get("rank", 999)), "holdings": hold_rows,
            "overlap": overlap, "note": ("史深 %d 月:yoy_streak/high_60m 需 ≥13/60 月真值(候 via-revfill)" % n_months) if n_months < 13 else ""}


def persist(res: dict) -> dict:
    import duckdb
    con = duckdb.connect(str(DB_TW))
    try:
        con.execute(f"""CREATE TABLE IF NOT EXISTS {T_ETF}(etf_ticker VARCHAR, asof_ym VARCHAR, portfolio_date VARCHAR, etf_name VARCHAR,
            n_holdings INTEGER, cov_w DOUBLE, w_yoy DOUBLE, med_yoy DOUBLE, pos_share_w DOUBLE, w_mom DOUBLE, high60_share_w DOUBLE,
            avg_streak DOUBLE, rank INTEGER, flag VARCHAR, computed_at VARCHAR)""")
        con.execute(f"""CREATE TABLE IF NOT EXISTS {T_HOLD}(etf_ticker VARCHAR, asof_ym VARCHAR, portfolio_date VARCHAR, code VARCHAR, name VARCHAR,
            w DOUBLE, yoy DOUBLE, mom DOUBLE, streak INTEGER, high60 INTEGER, computed_at VARCHAR)""")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        con.execute("CREATE TEMP TABLE _e AS SELECT * FROM " + T_ETF + " LIMIT 0")
        con.executemany("INSERT INTO _e VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        [(e["etf_ticker"], e["asof_ym"], e["portfolio_date"], e["etf_name"], e["n_holdings"], e["cov_w"], e["w_yoy"], e["med_yoy"],
                          e["pos_share_w"], e["w_mom"], e["high60_share_w"], e["avg_streak"], e.get("rank"), e["flag"], ts) for e in res["etfs"]])
        b0 = con.execute(f"SELECT COUNT(*) FROM {T_ETF}").fetchone()[0]
        con.execute(f"""INSERT INTO {T_ETF} SELECT * FROM _e x WHERE NOT EXISTS (SELECT 1 FROM {T_ETF} t
                        WHERE t.etf_ticker = x.etf_ticker AND t.asof_ym = x.asof_ym AND t.portfolio_date = x.portfolio_date)""")
        b1 = con.execute(f"SELECT COUNT(*) FROM {T_ETF}").fetchone()[0]
        con.execute("CREATE TEMP TABLE _h AS SELECT * FROM " + T_HOLD + " LIMIT 0")
        con.executemany("INSERT INTO _h VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        [(h["etf_ticker"], h["asof_ym"], h["portfolio_date"], h["code"], h["name"], h["w"], h["yoy"], h["mom"], h["streak"], h["high60"], ts) for h in res["holdings"]])
        con.execute(f"""INSERT INTO {T_HOLD} SELECT * FROM _h x WHERE NOT EXISTS (SELECT 1 FROM {T_HOLD} t
                        WHERE t.etf_ticker = x.etf_ticker AND t.asof_ym = x.asof_ym AND t.portfolio_date = x.portfolio_date AND t.code = x.code)""")
        con.execute("DROP TABLE _e")
        con.execute("DROP TABLE _h")
        return {"etf_new": b1 - b0, "etf_total": b1}
    finally:
        con.close()


def render(res: dict) -> str:
    e = html.escape

    def pct(v):
        return "—" if v is None else ("%+.1f%%" % v)
    def nz(v, suffix=""):
        return "—" if v is None else str(v) + suffix

    def erow(x):
        top = ", ".join(t["code"] + " " + ("%+.0f%%" % t["yoy"]) for t in x["top"])
        flag = (" · " + x["flag"]) if x["flag"] else ""
        return ('<tr><td class="m">' + str(x.get("rank", "—")) + '</td><td><b>' + e(x["etf_ticker"]) + '</b><br><span class="dim">' + e(x["etf_name"] or "") + "</span></td>"
                + '<td class="c m">' + str(x["n_holdings"]) + '<br><span class="dim">' + nz(x["cov_w"], "%") + "</span></td>"
                + '<td class="c m">' + pct(x["w_yoy"]) + '</td><td class="c m">' + pct(x["med_yoy"]) + '</td><td class="c m">' + nz(x["pos_share_w"], "%") + "</td>"
                + '<td class="c m">' + pct(x["w_mom"]) + '</td><td class="c m">' + nz(x["high60_share_w"], "%") + "</td>"
                + '<td class="m dim">' + e(top) + e(flag) + "</td></tr>")
    erows = "".join(erow(x) for x in res["etfs"])

    def orow(a):
        return ('<tr><td class="m">' + e(a["code"]) + "</td><td>" + e(a["name"] or "") + '</td><td class="c m">' + str(a["n_etf"]) + '</td><td class="c m">' + str(a["w_sum"])
                + '</td><td class="c m">' + ("%+.1f%%" % a["yoy"]) + '</td><td class="c m">' + nz(a["streak"]) + '</td><td class="c m">' + ("★" if a["high60"] else "") + "</td></tr>")
    orows = "".join(orow(a) for a in res["overlap"])
    n_ok = sum(1 for x in res["etfs"] if x["w_yoy"] is not None)
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · 主動 ETF × 月營收動能</title>
<style>:root{{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}}*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}}.wrap{{max-width:1300px;margin:0 auto;padding:18px 14px 48px}}
h1{{font-size:14px;margin:0}}.sub{{color:var(--mu);margin:3px 0 14px}}h2{{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}}.nav a{{color:#7dd3fc;margin-right:12px;text-decoration:none}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:14px}}.kpi{{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}}.kpi .n{{font-size:17px;font-weight:600}}.kpi .l{{font-size:10px;color:var(--mu)}}
table{{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}}th{{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}}td{{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word}}td.c{{text-align:center}}.m{{font-family:ui-monospace,Consolas,monospace;font-size:10px}}.dim{{color:var(--mu)}}
.note{{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}}
@media(max-width:700px){{table,thead,tbody,tr,td,th{{display:block}}thead{{display:none}}td{{border:0;padding:2px 6px}}tr{{border-bottom:1px solid var(--line);padding:6px 0}}}}</style></head><body><div class="wrap">
<h1>ACTIVE TW ETF × MONTHLY REVENUE MOMENTUM</h1><p class="sub">VDF_ENG076 · 營收月 {e(res["asof_ym"])} · 史深 {res["n_months"]} 月 · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
<p class="nav"><a href="VIA_UI_ProjectCompletion_v0100.html">竣</a><a href="VIA_UI_ETFConsensusAnalysis_v0100.html">ETF×共識</a><a href="VIA_UI_RevenueConsensusAnalysis_v0100.html">營收×共識</a><a href="VIA_UI_VDFArchitecture_v0100.html">架</a></p>
<div class="kpis"><div class="kpi"><div class="n">{len(res["etfs"])}</div><div class="l">ETFs with holdings</div></div><div class="kpi"><div class="n">{n_ok}</div><div class="l">ETFs with revenue momentum</div></div>
<div class="kpi"><div class="n">{len(res["holdings"])}</div><div class="l">holding rows</div></div><div class="kpi"><div class="n">{len(res["overlap"])}</div><div class="l">overlap leaders</div></div></div>
<h2>ETF — holdings-weighted revenue momentum (weights: only covered holdings in denominator)</h2>
<table><colgroup><col style="width:4%"><col style="width:16%"><col style="width:8%"><col style="width:9%"><col style="width:9%"><col style="width:8%"><col style="width:9%"><col style="width:8%"><col style="width:29%"></colgroup>
<thead><tr><th>#</th><th>ETF</th><th>n · cov%</th><th>w·yoy</th><th>med yoy</th><th>pos w%</th><th>w·mom</th><th>60m-high w%</th><th>top contributors</th></tr></thead><tbody>{erows}</tbody></table>
<h2>OVERLAP — holdings ranked by ETF count × total weight, with revenue momentum</h2>
<table><colgroup><col style="width:10%"><col style="width:26%"><col style="width:10%"><col style="width:14%"><col style="width:14%"><col style="width:13%"><col style="width:13%"></colgroup>
<thead><tr><th>code</th><th>name</th><th>#ETF</th><th>Σw</th><th>yoy</th><th>streak</th><th>60m high</th></tr></thead><tbody>{orows}</tbody></table>
<div class="note">加權律:僅營收覆蓋之持股權重入分母;覆蓋 &lt;50% 標 LOW_COVERAGE。{e(res.get("note", ""))} 來源=ActiveTWETF holdings_daily × ENG063 monthly_revenue_analysis;零網路;只增不減落庫 {T_ETF}/{T_HOLD}。</div>
</div></body></html>"""


def run() -> int:
    res = compute()
    if res["state"] != "OK":
        print(f"[ETF×營收] SKIP {res['note']}")
        return 0
    p = persist(res)
    REP.mkdir(parents=True, exist_ok=True)
    (REP / f"ETF_REVENUE_{res['asof_ym']}.json").write_text(json.dumps({k: v for k, v in res.items() if k != "holdings"}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    OUT_UI.parent.mkdir(parents=True, exist_ok=True)
    OUT_UI.write_text(render(res), encoding="utf-8")
    n_ok = sum(1 for x in res["etfs"] if x["w_yoy"] is not None)
    print(f"[ETF×營收] {len(res['etfs'])} 檔 ETF · 動能可算 {n_ok} · 營收月 {res['asof_ym']} · 史深 {res['n_months']} 月 · 落庫新 {p['etf_new']}/{p['etf_total']} · {OUT_UI.name}")
    for x in res["etfs"][:5]:
        if x["w_yoy"] is not None:
            print(f"  [榜] #{x['rank']} {x['etf_ticker']} {x['etf_name']} 加權 yoy {x['w_yoy']:+.1f}%(覆蓋 {x['cov_w']}%;正年增權重 {x['pos_share_w']}%)")
    if res.get("note"):
        print(f"  [註] {res['note']}")
    return 0


def status() -> int:
    if not DB_TW.exists():
        print("  [DB] 缺")
        return 0
    con = _con(DB_TW)
    try:
        tabs = {t for (t,) in con.execute("SHOW TABLES").fetchall()}
        if T_ETF in tabs:
            print(con.execute(f"SELECT asof_ym, COUNT(*), ROUND(AVG(w_yoy),2), MAX(computed_at) FROM {T_ETF} GROUP BY 1 ORDER BY 1 DESC").fetchall())
        else:
            print(f"  [{T_ETF}] 表缺(先 run)")
    finally:
        con.close()
    return 0


def selftest() -> int:
    import tempfile
    global DB_TW, DB_ETF, REP, OUT_UI
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    _s = (DB_TW, DB_ETF, REP, OUT_UI)
    with tempfile.TemporaryDirectory() as td:
        import duckdb
        DB_TW, DB_ETF = Path(td) / "tw.duckdb", Path(td) / "etf.duckdb"
        REP, OUT_UI = Path(td) / "rep", Path(td) / "p.html"
        c = duckdb.connect(str(DB_ETF))
        c.execute("CREATE TABLE holdings_daily(portfolio_date DATE, etf_ticker VARCHAR, etf_name VARCHAR, holding_ticker VARCHAR, holding_name VARCHAR, weight_pct DOUBLE)")
        c.executemany("INSERT INTO holdings_daily VALUES (?,?,?,?,?,?)", [
            ("2026-09-01", "00981A", "強棒", "2330", "台積電", 20.0), ("2026-09-01", "00981A", "強棒", "2454", "聯發科", 10.0), ("2026-09-01", "00981A", "強棒", "9999", "無營收", 10.0),
            ("2026-08-31", "00981A", "強棒", "2330", "台積電", 50.0), ("2026-09-01", "00982A", "另一", "2454", "聯發科", 30.0), ("2026-09-01", "00983A", "低覆", "9999", "無營收", 30.0)])
        c.close()
        c = duckdb.connect(str(DB_TW))
        c.execute("CREATE TABLE monthly_revenue_analysis(code VARCHAR, ym VARCHAR, revenue DOUBLE, mom_pct DOUBLE, yoy_pct DOUBLE, cum_12m DOUBLE, high_60m INTEGER, yoy_streak INTEGER)")
        c.executemany("INSERT INTO monthly_revenue_analysis VALUES (?,?,?,?,?,?,?,?)", [
            ("2330", "202607", 100, 0.05, 0.40, None, 1, 1), ("2454", "202607", 50, -0.02, -0.10, None, 0, 0), ("2330", "202608", 100, None, None, None, 0, 0)])
        c.close()
        r = compute()
        e = {x["etf_ticker"]: x for x in r["etfs"]}
        chk("① 最新月=yoy 覆蓋 ≥50% 之月(202608 快照未齊不採→202607)", r["state"] == "OK" and r["asof_ym"] == "202607")
        chk("② ETF 最新 portfolio_date 持股(00981A 用 09-01 三檔非 08-31)", e["00981A"]["n_holdings"] == 3 and e["00981A"]["portfolio_date"] == "2026-09-01")
        w = e["00981A"]
        chk("③ 加權律=僅覆蓋權重入分母(00981A:(20×40−10×10)/30=+23.33%;覆蓋 75%;正年增權重 66.7%)",
            abs(w["w_yoy"] - 23.33) < 0.01 and w["cov_w"] == 75.0 and w["pos_share_w"] == 66.7 and w["med_yoy"] == 40.0, f"{w['w_yoy']} {w['cov_w']} {w['pos_share_w']}")
        chk("④ 無覆蓋 ETF=NULL 誠實+LOW_COVERAGE 旗標;排名只計可算者(00981A #1, 00982A #2)",
            e["00983A"]["w_yoy"] is None and e["00983A"]["flag"] == "LOW_COVERAGE" and e["00981A"]["rank"] == 1 and e["00982A"]["rank"] == 2 and "rank" not in e["00983A"])
        chk("⑤ 重疊榜(2454 被持 2 檔 Σw 40 居首;無營收者不列)", r["overlap"][0]["code"] == "2454" and r["overlap"][0]["n_etf"] == 2 and all(a["code"] != "9999" for a in r["overlap"]))
        p1 = persist(r)
        p2 = persist(r)
        chk("⑥ 只增落庫 anti-join 冪等(首插 3;重跑 0;不覆寫)", p1["etf_new"] == 3 and p2["etf_new"] == 0 and p2["etf_total"] == 3)
        REP.mkdir(parents=True, exist_ok=True)
        OUT_UI.write_text(render(r), encoding="utf-8")
        h = OUT_UI.read_text(encoding="utf-8")
        chk("⑦ 頁(手機單欄 @media;零 CDN;導航竣/ETF×共識/營收×共識;史深註)", "@media" in h and "src=\"http" not in h and "VIA_UI_ProjectCompletion_v0100.html" in h and "史深" in h)
    DB_TW, DB_ETF, REP, OUT_UI = _s
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(零網路/只增不減/加權律/NULL 誠實/LOW_COVERAGE)", all(k in src for k in ("零網路", "只增不減", "加權律", "NULL 誠實", "LOW_COVERAGE")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 主動 ETF × 月營收動能(VDF_ENG076)· 八檢自測 ===")
        return selftest()
    if a and a[0] == "status":
        return status()
    return run()


if __name__ == "__main__":
    sys.exit(main())
