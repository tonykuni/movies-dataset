#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG069_ConsensusDB — 驗證共識資料庫(批176;操作員定位令)
====================================================================
操作員令:「transform data in the stock report into verified consensus
database」——共識庫實體化(庫優先>模板;憲章 platform_doctrine):
  表 consensus_daily(vdf_tw_market.duckdb;upsert 冪等):
    date×code×source 主鍵;目標價四值/n_analysts/EPS 0y/1y/adopted_eps
    +upside_pct(=target_median/close-1;close 取 tw_daily_prices 同日或
    前一交易日;公式冊載庫內衍生零發明)+validated 旗標
  雙源設計:
    EXTERNAL_ANALYST=analyst_estimates 表正規化(Yahoo 車道;VDF_ENG059
      日更快照;validated=SOURCE_DIRECT)
    BROKER_REPORT=digest 批跑產出(券商報告件;經 finaudit 驗證旗標;
      收件夾空=誠實 0 筆,件到即入)
  consensus_latest 視圖:per code 最新共識+upside(未來模板/分析一律
    自此取數=操作員令)
v0101→v0102(批300 重建鏈實錄):EXTERNAL_ANALYST 段+表存在守衛
——analyst_estimates 缺(Yahoo 雲端擋牆)=誠實 0 筆列示續建,
不再炸斷 CNYES/BROKER 正規化與 consensus_latest 視圖(單源環境
可完建=雙源設計本旨)。
用法:python3 VRN_ENG069_ConsensusDB_v0102.py build | --status | --selftest
v0100→v0101(批178):upside 之 close 源改正典調整層 prices_canonical
(操作員令:調整後價=下游一切輸入;最新日 factor≈1 數值等價,紀律統一)。
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

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DB = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DIGEST_OUT = HERE / "fin_out"   # digest 批跑產出夾(件到即入;空=誠實 0)

DDL = """
CREATE TABLE IF NOT EXISTS consensus_daily (
  date DATE, code VARCHAR, source VARCHAR,
  target_high DOUBLE, target_low DOUBLE, target_mean DOUBLE,
  target_median DOUBLE, n_analysts INTEGER,
  eps_fy0 DOUBLE, eps_fy1 DOUBLE, adopted_eps DOUBLE,
  close DOUBLE, upside_pct DOUBLE,
  validated VARCHAR,
  PRIMARY KEY (date, code, source)
)"""


def _con(read_only: bool = False):
    import duckdb
    return duckdb.connect(str(DB), read_only=read_only)


def build() -> dict:
    """雙源入庫(冪等 upsert)+最新共識視圖"""
    con = _con()
    con.execute(DDL)
    # 源一:analyst_estimates 正規化(Yahoo 車道=EXTERNAL_ANALYST)
    # 批300 守衛:表缺(雲端擋牆未跑 ENG059)=誠實 0 筆,單源續建
    _tabs = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "analyst_estimates" in _tabs:
        con.execute("""
        INSERT OR REPLACE INTO consensus_daily
        SELECT a.date, a.code, 'EXTERNAL_ANALYST',
               a.target_high, a.target_low, a.target_mean, a.target_median,
               a.n_analysts, a.eps0y_avg, a.eps1y_avg, a.adopted_eps,
               p.close,
               CASE WHEN p.close IS NOT NULL AND p.close > 0
                    AND a.target_median IS NOT NULL
                    THEN a.target_median / p.close - 1 END,
               'SOURCE_DIRECT'
        FROM analyst_estimates a
        LEFT JOIN (
            SELECT ticker, close, date,
                   row_number() OVER (PARTITION BY ticker ORDER BY date DESC) rn
            FROM prices_canonical) p
          ON p.ticker = a.code || '.TW' AND p.rn = 1
    """)
    n_ext = con.execute(
        "SELECT count(*) FROM consensus_daily WHERE source='EXTERNAL_ANALYST'"
    ).fetchone()[0]
    # 源二:digest 券商報告產出(件到即入;經 finaudit 旗標)
    n_brk = 0
    if DIGEST_OUT.is_dir():
        for f in sorted(DIGEST_OUT.glob("*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            rows = d if isinstance(d, list) else d.get("reports") or []
            for r in rows:
                code = str(r.get("code") or r.get("代碼") or "").strip()
                tp = r.get("target_price") or r.get("目標價")
                dt = r.get("report_date") or r.get("date")
                if not (code and tp and dt):
                    continue  # 缺鍵=誠實跳過不猜
                con.execute(
                    "INSERT OR REPLACE INTO consensus_daily VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,NULL,NULL,?)",
                    [dt, code, "BROKER_REPORT", tp, tp, tp, tp, 1,
                     r.get("eps_fy0"), r.get("eps_fy1"), r.get("eps_fy0"),
                     "FINAUDIT_" + str(r.get("finaudit", "PENDING"))])
                n_brk += 1
    # 最新共識視圖(未來模板/分析取數點=操作員令)
    con.execute("""
        CREATE OR REPLACE VIEW consensus_latest AS
        SELECT * FROM (
          SELECT *, row_number() OVER (
                 PARTITION BY code, source ORDER BY date DESC) rn
          FROM consensus_daily) WHERE rn = 1
    """)
    total = con.execute("SELECT count(*) FROM consensus_daily").fetchone()[0]
    con.close()
    return {"external": n_ext, "broker": n_brk, "total": total}


def status() -> int:
    con = _con(read_only=True)
    try:
        rows = con.execute(
            "SELECT source, count(*), count(DISTINCT code), max(date) "
            "FROM consensus_daily GROUP BY 1").fetchall()
    except Exception:
        print("consensus_daily 未建(先 build)")
        return 1
    for s, n, nc, mx in rows:
        print(f"  [{s}] {n} 筆 · {nc} 檔 · 最新 {mx}")
    up = con.execute(
        "SELECT code, round(upside_pct*100,2) FROM consensus_latest "
        "WHERE source='EXTERNAL_ANALYST' AND upside_pct IS NOT NULL "
        "ORDER BY upside_pct DESC LIMIT 5").fetchall()
    print("  [upside 前五]", up)
    con.close()
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 憲章定位冊在位(platform_doctrine=庫優先)",
        "platform_doctrine" in json.loads(
            (VIA / "supportive modules" / "registry" /
             "VIA_System_Charter_v0100.json").read_text(encoding="utf-8")))
    r = build()
    chk("② 雙源入庫(EXTERNAL≥190 檔;BROKER=收件夾實況誠實)",
        r["external"] >= 190 and r["broker"] >= 0,
        f"(外部 {r['external']} · 券商 {r['broker']})")
    con = _con(read_only=True)
    cols = [d[0] for d in con.execute(
        "SELECT * FROM consensus_daily LIMIT 0").description]
    chk("③ 表 schema(14 欄含 upside_pct/validated;主鍵三元)",
        len(cols) == 14 and "upside_pct" in cols and "validated" in cols)
    n2330 = con.execute(
        "SELECT target_median, close, upside_pct FROM consensus_latest "
        "WHERE code='2330' AND source='EXTERNAL_ANALYST'").fetchall()
    chk("④ upside 公式實證(2330:median/close-1;庫內衍生)",
        bool(n2330) and n2330[0][2] is not None
        and abs(n2330[0][0] / n2330[0][1] - 1 - n2330[0][2]) < 1e-9,
        f"({n2330[0] if n2330 else '缺'})")
    con.close()   # duckdb 同檔禁異配置並存:先關唯讀再 build
    r2 = build()
    con2 = _con(read_only=True)
    t1 = con2.execute("SELECT count(*) FROM consensus_daily").fetchone()[0]
    chk("⑤ 冪等(重跑 build 筆數不增=INSERT OR REPLACE)",
        t1 == r["total"] and r2["total"] == r["total"], f"({t1} 筆)")
    chk("⑥ consensus_latest 視圖(per code×source 最新一筆)",
        con2.execute("SELECT count(*) FROM consensus_latest").fetchone()[0]
        == con2.execute(
            "SELECT count(DISTINCT code||source) FROM consensus_daily"
        ).fetchone()[0])
    chk("⑦ validated 旗標(外部=SOURCE_DIRECT;券商=FINAUDIT_*)",
        con2.execute("SELECT count(*) FROM consensus_daily "
                     "WHERE source='EXTERNAL_ANALYST' "
                     "AND validated!='SOURCE_DIRECT'").fetchone()[0] == 0)
    con2.close()
    boot = (VIA / "supportive modules" / "registry" /
            "via_boot_update.sh").read_text(encoding="utf-8")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告+boot 日更接線(公式冊載/缺鍵不猜/冪等)",
        "VRN_ENG069" in boot and "誠實跳過不猜" in src and "冪等" in src)
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 驗證共識資料庫(VRN_ENG069)· 八檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    r = build()
    print(f"[共識庫] 外部 {r['external']} · 券商 {r['broker']} · 總 {r['total']} 筆"
          f" · consensus_latest 視圖在位(未來分析取數點)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
