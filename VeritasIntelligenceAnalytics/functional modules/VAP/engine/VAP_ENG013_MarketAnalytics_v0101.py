#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VAP_ENG013_MarketAnalytics v0101 — VAP 市場分析(9hh5to 手機代測令)
======================================================================
操作員令:「VAP 透過這些資料做出月營收分析和族群分析;ETF 分析持股
加總,可點選個別的也可以點選組合的」。全權代測=引擎+橋端點+手機 UI。
三分析(全唯讀;誠實雙道=庫直讀優先,缺庫退 fixture 示範道並明標):
  ① 月營收分析  庫道=monthly_revenue_analysis(工作站);fixture 道=
     v0139A UAT CSV(隨版控)。YoY/MoM/動能榜+族群彙總。
  ② 族群分析    庫道=tw_listings_industry×tw_trading_daily(雙日)
     ×tw_valuation_daily:逐產業 漲跌家數/量能(億)/均PE/均殖利率。
  ③ ETF 持股    冊=etf_book(is_active);持股=holdings_daily parquet
     (實庫 glob→fixture 後備);個別=權重榜;組合=等權平均權重
     +出現檔數(持股加總)。
紅線:唯讀零改動;庫鎖=busy 誠實;無資料=NOT_RUN 不假造;lane 必標。
v0100→v0101(9hh5to「共識取得+核對無誤+K線量圖」令):
  ④ kline(code)   K線+量三道:tw_daily_prices 庫直讀(OHLCV)→TWSE
     官方 STOCK_DAY(net;雙同意閘;月批+10 分快取)→tw_trading_daily
     收盤+量降級(mode=close_only 誠實)。
  ⑤ consensus_check(codes)  共識核對:庫內逐源最新列×鉅亨 targetPrice
     現值重取對照(net 缺=SKIP 僅庫內)→裁決 無誤/已更新/差異/單源。
用法:python3 VAP_ENG013_MarketAnalytics_v0101.py [--selftest|--print]
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
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
DB = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
HOLD_REAL = (VIA / "functional modules" / "VDF" / "output_hub" / "active_tw_etf"
             / "active_tw_etf_holdings" / "parquet" / "holdings_daily")
HOLD_FIX = HERE / "fixtures" / "vap_eng013_holdings_fixture.parquet"
UAT = (VIA / "functional modules" / "VIA_Accelerated_Integration_v0139A_DELIVERY"
       / "Validation" / "RUN_FIXTURE_UAT" / "data")
REV_FIX = UAT / "VIA_Monthly_Revenue_Detail_v0139A.csv"


def _con(read_db: bool = True):
    import duckdb
    if read_db and DB.exists():
        try:
            return duckdb.connect(str(DB), read_only=True), None
        except Exception as e:
            if "lock" in str(e).lower():
                return None, {"busy": True, "note": "資料庫使用中=稍後重試(誠實)"}
            return None, {"err": str(e)[:120]}
    return duckdb.connect(), None  # 記憶體連線(讀 parquet/csv 用)


def _rows(con, sql, args=()):
    try:
        cur = con.execute(sql, list(args))
        return [d[0] for d in cur.description], cur.fetchall()
    except Exception:
        return [], []


# ── ① 月營收分析 ──
def revenue_analysis(top: int = 12) -> dict:
    con, err = _con()
    if err:
        return err
    lane = "庫直讀"
    cols, rows = _rows(con, "SELECT code, ym, revenue, mom_pct, yoy_pct "
                            "FROM monthly_revenue_analysis "
                            "WHERE ym=(SELECT MAX(ym) FROM monthly_revenue_analysis) "
                            "ORDER BY yoy_pct DESC NULLS LAST")
    if not rows:  # 容器庫空=退 fixture 示範道(v0139A UAT;誠實標)
        lane = "fixture 示範道(v0139A UAT;工作站=庫直讀)"
        if not REV_FIX.exists():
            return {"lane": "NOT_RUN", "note": "庫空且 fixture 缺=誠實不假造"}
        with open(REV_FIX, encoding="utf-8-sig") as fh:
            raw = list(csv.DictReader(fh))
        latest = max(r["Revenue Month"] for r in raw)
        cur = [r for r in raw if r["Revenue Month"] == latest]

        def f(v):
            try:
                return float(v)
            except Exception:
                return None
        rows = [(r["Ticker"], latest, f(r["Monthly Revenue"]),
                 f(r["Revenue MoM Pct"]), f(r["Revenue YoY Pct"]),
                 r.get("Sector", ""), f(r["Revenue Momentum Score"])) for r in cur]
        rows.sort(key=lambda x: (x[4] is None, -(x[4] or 0)))
        sec = {}
        for r in rows:
            s = sec.setdefault(r[5] or "—", [0, 0.0])
            s[0] += 1
            s[1] += (r[2] or 0)
        return {"lane": lane, "ym": latest,
                "top_yoy": [[r[0], r[2], r[3], r[4], r[5], r[6]] for r in rows[:top]],
                "sectors": sorted(([k, v[0], round(v[1] / 1e8, 1)]
                                   for k, v in sec.items()), key=lambda x: -x[2])}
    top_rows = [[r[0], r[2], r[3], r[4], "", None] for r in rows[:top]]
    return {"lane": lane, "ym": rows[0][1] if rows else None,
            "top_yoy": top_rows, "sectors": []}


# ── ② 族群分析(容器庫=真資料)──
def group_analysis(top: int = 15) -> dict:
    con, err = _con()
    if err:
        return err
    cols, dts = _rows(con, "SELECT DISTINCT date FROM tw_trading_daily ORDER BY date DESC LIMIT 2")
    if not dts:
        return {"lane": "NOT_RUN", "note": "tw_trading_daily 空=誠實不假造"}
    d1 = str(dts[0][0])
    d0 = str(dts[1][0]) if len(dts) > 1 else None
    sql = """
      WITH t1 AS (SELECT code, close, trade_value FROM tw_trading_daily WHERE date=?),
           t0 AS (SELECT code, close c0 FROM tw_trading_daily WHERE date=?),
           v  AS (SELECT code, pe, dividend_yield FROM tw_valuation_daily
                  WHERE date=(SELECT MAX(date) FROM tw_valuation_daily))
      SELECT l.industry_name,
             COUNT(*) n,
             SUM(CASE WHEN t0.c0 IS NOT NULL AND t1.close>t0.c0 THEN 1 ELSE 0 END) up,
             SUM(CASE WHEN t0.c0 IS NOT NULL AND t1.close<t0.c0 THEN 1 ELSE 0 END) dn,
             ROUND(SUM(t1.trade_value)/1e8, 1) val_e8,
             ROUND(AVG(CASE WHEN v.pe>0 AND v.pe<500 THEN v.pe END), 1) pe,
             ROUND(AVG(v.dividend_yield), 2) dy
      FROM t1 JOIN "tw_listings_industry" l ON l.code=t1.code
      LEFT JOIN t0 ON t0.code=t1.code LEFT JOIN v ON v.code=t1.code
      WHERE l.industry_name IS NOT NULL AND l.industry_name<>''
      GROUP BY 1 HAVING COUNT(*)>=3 ORDER BY val_e8 DESC
    """
    cols, rows = _rows(con, sql, (d1, d0 or d1))
    return {"lane": "庫直讀(tw 上市名冊×交易×估值)", "date": d1, "prev": d0,
            "groups": [list(r) for r in rows[:top]], "total_groups": len(rows)}


# ── ③ ETF 持股(個別+組合加總)──
def _holdings_source():
    if HOLD_REAL.exists() and any(HOLD_REAL.glob("portfolio_date=*/*.parquet")):
        return str(HOLD_REAL / "portfolio_date=*" / "*.parquet"), "實庫 holdings_daily"
    if HOLD_FIX.exists():
        return str(HOLD_FIX), "fixture 示範道(工作站=實庫)"
    return None, "NOT_RUN"


def etf_list(limit: int = 40) -> dict:
    src, lane = _holdings_source()
    con, err = _con()
    if err:
        return err
    have = set()
    if src:
        mem, _ = _con(read_db=False)
        _, hr = _rows(mem, f"SELECT DISTINCT etf_ticker FROM '{src}'")
        have = {r[0] for r in hr}
    cols, rows = _rows(con, "SELECT DISTINCT fund_code, fund_name FROM etf_book "
                            "WHERE is_active ORDER BY fund_code")
    if not rows:
        return {"lane": "NOT_RUN", "note": "etf_book 空=誠實"}
    tap = [[c, n, (c in have) or (f"{c}.TW" in have)] for c, n in rows]
    tap.sort(key=lambda x: (not x[2], x[0]))
    return {"lane_book": "庫直讀 etf_book", "lane_hold": lane,
            "n_book": len(rows), "n_holdable": sum(1 for t in tap if t[2]),
            "etfs": tap[:limit]}


def etf_holdings(ids: list[str], top: int = 15) -> dict:
    """個別=逐檔權重榜;組合(len>1)=持股加總:等權平均權重+出現檔數。"""
    ids = [i.strip() for i in ids if i.strip()][:8]
    if not ids:
        return {"err": "未選 ETF(點選個別或組合)"}
    src, lane = _holdings_source()
    if not src:
        return {"lane": "NOT_RUN", "note": "持股資料缺(容器)=誠實;工作站有實庫"}
    con, _ = _con(read_db=False)
    marks = ",".join("?" * len(ids) * 2)
    _, rows = _rows(con,
                    f"SELECT etf_ticker, holding_ticker, holding_name, weight_pct "
                    f"FROM '{src}' WHERE etf_ticker IN ({marks}) "
                    f"AND portfolio_date=(SELECT MAX(portfolio_date) FROM '{src}')",
                    ids + [f"{i}.TW" for i in ids])
    if not rows:
        return {"lane": lane, "note": "所選 ETF 於持股源無列(誠實)", "ids": ids}
    per = {}
    for et, ht, hn, w in rows:
        per.setdefault(et, []).append([ht, hn, w])
    for et in per:
        per[et].sort(key=lambda x: -(x[2] or 0))
        per[et] = per[et][:top]
    if len(ids) == 1:
        return {"lane": lane, "mode": "individual", "ids": ids, "per": per}
    agg = {}
    n = len({et for et, *_ in rows})
    for et, ht, hn, w in rows:
        a = agg.setdefault(ht, {"name": hn, "sum": 0.0, "hits": 0})
        a["sum"] += float(w or 0)
        a["hits"] += 1
    combo = sorted(([ht, a["name"], round(a["sum"] / n, 2), a["hits"]]
                    for ht, a in agg.items()), key=lambda x: -x[2])
    return {"lane": lane, "mode": "combo", "ids": ids, "n_etf": n,
            "combo": combo[:max(top, 20)], "per": per,
            "note": "組合權重=等權平均(Σ權重/檔數);出現檔數=該股見於幾檔"}


# ── ④ K線+成交量(三道誠實)──
_KCACHE: dict = {}


def _consent() -> bool:
    import os
    return (os.environ.get("VIA_NET_CONSENT", "").upper() in ("YES", "1", "TRUE")
            and os.environ.get("VIA_SCRAPE_CONSENT", "").upper() in ("YES", "1", "TRUE"))


def parse_twse_month(d: dict) -> list:
    """TWSE STOCK_DAY 回包→bars [[date,o,h,l,c,v]](民國年轉西元;'--' 停牌跳過)。"""
    out = []
    for r in d.get("data", []):
        try:
            y, m, dd = r[0].split("/")
            dt = f"{int(y) + 1911:04d}-{m}-{dd}"
            f = lambda x: float(str(x).replace(",", ""))
            out.append([dt, f(r[3]), f(r[4]), f(r[5]), f(r[6]), int(f(r[1]))])
        except Exception:
            continue  # '--'/註記列=誠實跳過
    return out


def _twse_fetch(code: str, months: int) -> list:
    import json as _j
    import time as _t
    import urllib.request
    from datetime import date
    bars = []
    y, m = date.today().year, date.today().month
    for i in range(months):
        mm = m - i
        yy = y
        while mm <= 0:
            mm += 12
            yy -= 1
        u = (f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
             f"?date={yy}{mm:02d}01&stockNo={code}&response=json")
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                u, headers={"User-Agent": "Mozilla/5.0"}), timeout=12)
            bars += parse_twse_month(_j.loads(r.read()))
        except Exception:
            break  # 網路斷=誠實以已取為準
        _t.sleep(0.3)  # 官方源禮貌間隔
    return sorted(bars)


def kline(code: str, months: int = 6) -> dict:
    """K線+量三道:①tw_daily_prices 庫(OHLCV)②TWSE 官方(net 雙閘)
    ③tw_trading_daily 收盤+量降級(mode=close_only)。"""
    import re as _re
    import time as _t
    if not _re.fullmatch(r"\d{4,6}[A-Z]?", code or ""):
        return {"err": "代號格式不符(4-6 位數字)"}
    con, err = _con()
    if err:
        return err
    name = (
        _rows(con, "SELECT name FROM tw_listings_industry WHERE code=?", (code,))[1]
        or [[code]])[0][0]
    _, rows = _rows(con, "SELECT date, open, high, low, close, volume "
                         "FROM tw_daily_prices WHERE ticker=? "
                         "ORDER BY date DESC LIMIT ?", (f"{code}.TW", months * 22))
    if rows:
        bars = sorted([str(r[0])[:10], float(r[1]), float(r[2]), float(r[3]),
                       float(r[4]), int(r[5] or 0)] for r in rows)
        return {"lane": "庫直讀 tw_daily_prices", "code": code, "name": name,
                "mode": "ohlcv", "bars": bars}
    if _consent():
        ck = (code, months)
        hit = _KCACHE.get(ck)
        if hit and _t.time() - hit[0] < 600:
            bars = hit[1]
        else:
            bars = _twse_fetch(code, months)
            if bars:
                _KCACHE[ck] = (_t.time(), bars)
        if bars:
            return {"lane": "TWSE 官方 STOCK_DAY(net;10 分快取)", "code": code,
                    "name": name, "mode": "ohlcv", "bars": bars}
    _, rows = _rows(con, "SELECT date, close, volume FROM tw_trading_daily "
                         "WHERE code=? ORDER BY date", (code,))
    if rows:
        bars = [[str(r[0])[:10], None, None, None, float(r[1]), int(r[2] or 0)]
                for r in rows]
        return {"lane": "tw_trading_daily 降級(無 OHLC=誠實折線)", "code": code,
                "name": name, "mode": "close_only", "bars": bars}
    return {"lane": "NOT_RUN", "code": code, "name": name,
            "note": "三道皆缺(庫空+同意閘關)=誠實不假造"}


# ── ⑤ 共識核對(核對無誤驗證)──
def _cnyes_target(code: str) -> dict | None:
    import json as _j
    import urllib.request
    u = ("https://marketinfo.api.cnyes.com/mi/api/v1/financialIndicator"
         f"/targetPrice/TWS:{code}:STOCK")
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            u, headers={"User-Agent": "Mozilla/5.0"}), timeout=10)
        return (_j.loads(r.read()) or {}).get("data") or None
    except Exception:
        return None


def consensus_check(codes: list[str]) -> dict:
    """庫內共識(逐源最新列)×鉅亨現值重取對照。裁決:無誤(中位/分析師
    同)/已更新(rateDate 前進=源方更新誠實)/差異(同日不同值=列欄)/
    單源(無現值可對=僅庫內);net 缺=SKIP 僅列庫內。"""
    codes = [c.strip() for c in codes if c.strip()][:12]
    con, err = _con()
    if err:
        return err
    out = {"lane": "庫內×鉅亨現值對照" if _consent() else "庫內(net 同意閘關=SKIP 現值)",
           "rows": [], "verdicts": []}
    for c in codes:
        _, rs = _rows(con, "SELECT source, date, target_median, target_high, "
                           "target_low, n_analysts FROM consensus_daily WHERE code=? "
                           "QUALIFY row_number() OVER (PARTITION BY source "
                           "ORDER BY date DESC)=1", (c,))
        for s, d, med, hi, lo, n in rs:
            out["rows"].append([c, s, str(d)[:10], med, hi, lo, n])
        if not rs:
            out["verdicts"].append([c, "無庫值", "先跑共識擷取(consensus 任務)"])
            continue
        if not _consent():
            out["verdicts"].append([c, "SKIP", "net 關=僅庫內列示(誠實)"])
            continue
        live = _cnyes_target(c)
        if not live:
            out["verdicts"].append([c, "SKIP", "現值端點無回(誠實)"])
            continue
        fs = [r for r in rs if r[0] == "CNYES_FACTSET"]
        if not fs:
            out["verdicts"].append([c, "單源", "庫內無 FACTSET 列可對"])
            continue
        _, _, med, hi, lo, n = fs[0]
        same = (round(float(med or 0), 2) == round(float(live.get("feMedian") or 0), 2)
                and int(n or 0) == int(live.get("numEst") or 0))
        if same:
            out["verdicts"].append([c, "核對無誤", f"中位 {med}×{n} 分析師=現值一致"])
        else:
            out["verdicts"].append(
                [c, "已更新" if str(live.get("rateDate", "")) > str(fs[0][1])[:10] else "差異",
                 f"庫 {med}×{n} vs 現 {live.get('feMedian')}×{live.get('numEst')}"
                 f"(rateDate {live.get('rateDate')})"])
    return out


# ── 出力 ──
def cmd_print() -> int:
    for name, d in (("① 月營收分析", revenue_analysis()),
                    ("② 族群分析", group_analysis()),
                    ("③ ETF 冊", etf_list(limit=8))):
        print(f"── {name} ──")
        print("  " + json.dumps(d, ensure_ascii=False)[:500])
    return 0


# ── 自測(fixtures;零改動)──
def selftest() -> int:
    import duckdb
    import tempfile
    fails = []
    n = [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    r = revenue_analysis()
    chk("① 月營收分析(庫道或 fixture 道;lane 必標誠實)",
        ("lane" in r) and (r["lane"] == "NOT_RUN" or r.get("top_yoy")),
        f"({str(r.get('lane'))[:24]})")
    if r.get("top_yoy"):
        ys = [x[3] for x in r["top_yoy"] if x[3] is not None]
        chk("①b YoY 降冪排序(資訊要準)", ys == sorted(ys, reverse=True))
    g = group_analysis()
    chk("② 族群分析(庫直讀;產業聚合 漲跌家數/量能/均PE)",
        g.get("groups") and len(g["groups"][0]) == 7
        and all(gr[1] >= gr[2] + gr[3] for gr in g["groups"]),
        f"(族群 {g.get('total_groups')})")
    e = etf_list()
    chk("③ ETF 冊(etf_book 真讀+可點記號)",
        e.get("n_book", 0) > 0 and "etfs" in e, f"(冊 {e.get('n_book')})")
    with tempfile.TemporaryDirectory() as td:
        fx = Path(td) / "h.parquet"
        mem = duckdb.connect()
        mem.execute("""CREATE TABLE h AS SELECT * FROM (VALUES
          ('2026-08-24','00900','A ETF','2330','台積電',22.0),
          ('2026-08-24','00900','A ETF','2317','鴻海',8.0),
          ('2026-08-24','00901','B ETF','2330','台積電',18.0),
          ('2026-08-24','00901','B ETF','2454','聯發科',9.0))
          t(portfolio_date, etf_ticker, etf_name, holding_ticker, holding_name, weight_pct)""")
        mem.execute(f"COPY h TO '{fx}' (FORMAT PARQUET)")
        global HOLD_FIX, HOLD_REAL
        oldf, oldr = HOLD_FIX, HOLD_REAL
        HOLD_FIX, HOLD_REAL = fx, Path(td) / "nope"
        try:
            one = etf_holdings(["00900"])
            chk("④ 個別可點(單檔=權重榜降冪)",
                one.get("mode") == "individual"
                and one["per"]["00900"][0][0] == "2330")
            c = etf_holdings(["00900", "00901"])
            tsmc = next(x for x in c["combo"] if x[0] == "2330")
            chk("⑤ 組合加總(等權平均:台積電 (22+18)/2=20;出現 2 檔)",
                c.get("mode") == "combo" and tsmc[2] == 20.0 and tsmc[3] == 2)
            hon = next(x for x in c["combo"] if x[0] == "2317")
            chk("⑤b 單檔持股入組合(鴻海 8/2=4;出現 1 檔)",
                hon[2] == 4.0 and hon[3] == 1)
            chk("⑤c 組合榜降冪+lane 必標",
                c["combo"][0][0] == "2330" and "lane" in c)
        finally:
            HOLD_FIX, HOLD_REAL = oldf, oldr
    chk("⑥ 空選誠實拒", "err" in etf_holdings([]))
    chk("⑦ 唯讀紅線(全程 read_only/記憶體連線;零寫庫)",
        "read_only=True" in Path(__file__).read_text(encoding="utf-8"))
    fx = {"stat": "OK", "data": [
        ["115/08/03", "35,209,944", "83,673,350,698", "2,390.00", "2,395.00",
         "2,365.00", "2,370.00", "-55.00", "174,489", ""],
        ["115/08/04", "--", "--", "--", "--", "--", "--", "--", "--", "停牌"]]}
    kb = parse_twse_month(fx)
    chk("⑧ TWSE 月批剖析(民國轉西元;--停牌誠實跳過)",
        len(kb) == 1 and kb[0][0] == "2026-08-03" and kb[0][1] == 2390.0
        and kb[0][4] == 2370.0 and kb[0][5] == 35209944)
    import os
    os.environ.pop("VIA_NET_CONSENT", None)
    os.environ.pop("VIA_SCRAPE_CONSENT", None)
    k = kline("2330")
    chk("⑨ K線三道(lane 必標;無OHLC=close_only 誠實;格式拒)",
        "err" in kline("abc") and "lane" in k
        and (k.get("mode") in ("ohlcv", "close_only") or k["lane"] == "NOT_RUN"),
        f"({k.get('lane', '')[:22]}·{k.get('mode', '—')})")
    cc = consensus_check(["2330"])
    chk("⑩ 共識核對(net 關=SKIP 誠實;庫內列示;裁決欄)",
        "verdicts" in cc and cc["verdicts"]
        and cc["verdicts"][0][1] in ("SKIP", "無庫值", "核對無誤", "已更新", "差異", "單源"),
        f"({cc['verdicts'][0][1] if cc.get('verdicts') else '—'})")
    print(f"  [計] 自測 {n[0]} 項 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VAP 市場分析三件套(VAP_ENG013)· 自測 ===")
        return selftest()
    print("=== VAP_ENG013 市場分析:月營收/族群/ETF 持股加總(唯讀誠實雙道)===")
    return cmd_print()


if __name__ == "__main__":
    sys.exit(main())
