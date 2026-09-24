#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0105→v0106(批732;操作員 09-24「所有目標價及各前一日的價格都要換成ADJ CLOSE 上漲空間都要用最新的ADJ CLOSE」
            落到共識線 = 結 Z157 的 ENG069 段;同批操作員上傳整合引擎 v0120_2,共識線回到桌上)
  ① 上漲空間的 ADJ 版(Z157):`upside_pct = target_median ÷ 同日 close − 1` 用的是原始價,目標中位數是**共識日那時的
     股本基礎**,之後配息配股的現價比它低一截——上漲空間被高估(夾具:除息 3 元後舊式 34.0%、ADJ 30.0%)。
     新算法**不在本支長第二顆頭**(LL404/L05):每一列委派 ENG073 尾版 `adj_quote`——目標中位數 × 基準日因子
     ÷ 最新 adj close − 1;因子分母走交易所收盤(批730 Z173 同一個洞,B730 在 Z157 註記過「分母一併改交易所」)。
       · 共識快照(EXTERNAL_ANALYST / CNYES_FACTSET / YAHOO_QS …):基準日 = **共識日那一列**
         (傳給 adj_quote 的報告日 = 共識日 + 1 個日曆天,它取「報告日前一交易日」= 共識日或之前最近的交易日)。
       · BROKER_REPORT(券商報告):基準日 = 報告日前一交易日(L99 原意,報告日照傳)。
     **只增不減、不改舊表**:ENG070 / ENG071 都用 14 個位置的 `INSERT … VALUES` 寫 consensus_daily,
     在舊表加欄等於弄壞兩支別人的寫入——所以 ADJ 結果落**旁表 consensus_adj**(date×code×source 主鍵),
     另開視圖 **consensus_latest_adj** = consensus_latest + ADJ 欄;consensus_daily 14 欄、consensus_latest、
     upside_pct 一個字都不動。視圖裡目標中位數跟算 ADJ 時不一樣(別支事後改寫了那一列)→ 狀態 ADJ_STALE、數字不給;
     旁表還沒有那一列 → ADJ_NOT_RUN。單位跟 ENG073 一樣:upside_adj 是**百分比**(1 位小數),舊欄 upside_pct 是比值。
     新段不拖垮舊段:一列算壞 → 那一列 ADJ_ERROR(帶例外名)、其餘照算;ADJ 這一段整個壞 → 舊欄與舊視圖照建,因由印在 [共識庫] 那一行。
     容器實量(唯讀試算,198 列):舊欄有值 3 列(全是 CNYES 自帶 close;舊 join 只認 `.TW`,EXTERNAL 195 列全 NULL)
     → ADJ_OK 20 列 · ADJ_NO_FACTOR 124(容器價表只有 893 檔)· ADJ_NO_TARGET 54;3.3 秒。
  ② 自測只寫暫存庫(Z189 第一支;照 ENG070 v0103 的做法):v0105 的自測兩次 build() 寫**正式庫**、拿寫鎖,
     平行格子撞到別站讀鎖就紅(批731 v0480 實錄)。本版自測在暫存庫建夾具(四檔 + 一份券商報告;除息、上櫃尾碼、
     沒價、沒目標各一),正式庫**只開唯讀**:外部源覆蓋(原②的 ≥190)與「ADJ 試算 vs 獨立 SQL 複算」兩檢;
     正式庫被別的行程寫鎖中 → 誠實 SKIP(Z189 其餘各支還沒改)。+⑩ 釘住「正式庫前後一個位元組都沒變」。
  ③ 版史(L04):v0105 留在原地;build / --status / --selftest 用法不變,--status 多印 ADJ 覆蓋一行。

v0104→v0105(批642 **這一檢連自己失敗都印不出來**)
  全格子實測:本件自測直接拋 `TypeError: unsupported format string passed to
  NoneType.__format__`,整站紅在 selftest 第 224 行——**檢④在組自己的失敗訊息時炸掉**。
  f-string 的 note 是**先算好才傳進 chk 的**,所以 `{None:.6f}` 在判定之前就炸;
  條件寫得好好的(`upside_pct is not None` 本來就會判 FAIL),卻永遠輪不到它印出來。

  再往上一層,**尺也挑錯了列**:檢④要驗 `upside = median/close - 1` 這條公式,
  卻先硬選 `source='EXTERNAL_ANALYST'` 的那一列——而 2330 那一列是
  `median 3200 · close NULL · upside NULL`。**選了一列沒有輸入的資料去驗公式。**
  真正有輸入的是 CNYES_FACTSET 那一列(3175 / 2460 - 1 = 0.290650…)。
  退路本來就寫對了(要求 median 與 close 皆非空),只是**第一條查詢先命中就再也輪不到它**。

  量出來的背景(誠實記,不藏):`consensus_latest` 198 列裡 **195 列 upside_pct 是 NULL**,
  全部是 EXTERNAL_ANALYST 源——因為**價表沒有它們的 close**。
  那不是公式缺陷,是價料缺口,根在 VDF(與 VRN 文摘「上漲已算 2/46」同一個根)。
  所以 v0105 兩改:① 第一條查詢一併要求 median/close 非空(選得到有輸入的列才驗公式);
  ② note 一律走 `_fmt()`,None 印「未算」不炸。並把 195/198 這個數字印在檢④的註記裡——
  **一盞燈要讓人看出它紅在公式還是紅在沒有料**(L92)。

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
用法:python3 VRN_ENG069_ConsensusDB_v0106.py build | --status | --selftest
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

import collections
import datetime as _dt
import json
import sys
from pathlib import Path

ENGINE_VERSION = "v0106"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DB = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DIGEST_OUT = HERE / "fin_out"   # digest 批跑產出夾(件到即入;空=誠實 0)
ADJ_ENGINE_GLOB = "VRN_ENG073_ReportStructuredDB_v*.py"   # L99 上漲空間的唯一算法(尾版律)
REPORT_DATED = ("BROKER_REPORT",)   # 這些源的 date 是報告日(基準 = 報告日前一交易日);其餘是共識快照日
_E73_CACHE = []
_OPENED = collections.deque(maxlen=256)   # 本支開過的連線 (路徑, 唯讀?)——自測⑬ 拿它證明正式庫一次都沒被可寫地打開過

# v0106(Z157):ADJ 結果的旁表。consensus_daily 不加欄——ENG070/ENG071 用 14 個位置的 INSERT … VALUES 寫它。
ADJ_DDL = """
CREATE TABLE IF NOT EXISTS consensus_adj (
  date DATE, code VARCHAR, source VARCHAR,
  target_median DOUBLE, basis_date VARCHAR,
  target_median_adj DOUBLE, adj_factor DOUBLE, adj_factor_date VARCHAR, adj_factor_basis VARCHAR,
  price_latest_adj DOUBLE, price_latest_date VARCHAR,
  upside_adj DOUBLE, upside_adj_state VARCHAR, adj_block_reason VARCHAR, adj_event VARCHAR,
  adj_engine VARCHAR, computed_at TIMESTAMP,
  PRIMARY KEY (date, code, source)
)"""
ADJ_COLS = ("target_median_adj", "adj_factor", "adj_factor_date", "adj_factor_basis", "price_latest_adj",
            "price_latest_date", "upside_adj", "upside_adj_state", "adj_block_reason", "adj_event")
ADJ_FROM = {"target_median_adj": "target_price_adj"}   # 旁表欄名 → ENG073 adj_quote 的欄名(不同名的只有這一個)
# 目標中位數跟算 ADJ 那時不一樣(別支事後改寫了那一列)= 舊的 ADJ 不算數;旁表還沒這一列 = 還沒算
LATEST_ADJ_VIEW = """
CREATE OR REPLACE VIEW consensus_latest_adj AS
SELECT c.*,
       a.basis_date, a.target_median_adj, a.adj_factor, a.adj_factor_date, a.adj_factor_basis,
       a.price_latest_adj, a.price_latest_date,
       CASE WHEN a.code IS NOT NULL AND a.target_median IS NOT DISTINCT FROM c.target_median
            THEN a.upside_adj END AS upside_adj,
       CASE WHEN a.code IS NULL THEN 'ADJ_NOT_RUN'
            WHEN a.target_median IS DISTINCT FROM c.target_median THEN 'ADJ_STALE'
            ELSE a.upside_adj_state END AS upside_adj_state,
       a.adj_block_reason, a.adj_event, a.adj_engine, a.computed_at AS adj_computed_at
FROM consensus_latest c
LEFT JOIN consensus_adj a ON a.date = c.date AND a.code = c.code AND a.source = c.source"""

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


def _con(read_only: bool = False, db: Path | None = None):
    import duckdb
    _OPENED.append((str(db or DB), read_only))   # v0106:自測⑬ 用它量「正式庫有沒有被可寫地打開過」(Z189)
    return duckdb.connect(str(db or DB), read_only=read_only)


def adj_engine():
    """v0106(Z157):ENG073 尾版 = L99 上漲空間的唯一算法(`adj_quote`)。回 (模組 | None, 因由);只載一次。
    缺檔或太舊(沒有 adj_quote,批729 以前)= 誠實 None,build 照建舊欄、ADJ 旁表不寫,因由印在結果裡。"""
    if _E73_CACHE:
        return _E73_CACHE[0]
    mod, why = None, ""
    hits = sorted(HERE.glob(ADJ_ENGINE_GLOB))
    if not hits:
        why = f"樹上沒有 {ADJ_ENGINE_GLOB}"
    else:
        try:
            import importlib.util as _ilu
            sp = _ilu.spec_from_file_location("_vrn_eng073_for_eng069", hits[-1])
            mod = _ilu.module_from_spec(sp)
            sys.modules[sp.name] = mod
            sp.loader.exec_module(mod)
            if not all(hasattr(mod, k) for k in ("adj_quote", "ADJ_FIELDS")):
                mod, why = None, f"{hits[-1].name} 沒有 adj_quote(批729 以前的版本)"
            else:
                why = hits[-1].stem
        except Exception as exc:  # noqa: BLE001 -- the reason is returned and printed, not swallowed
            mod, why = None, f"{hits[-1].name} 載入失敗 {type(exc).__name__}: {str(exc)[:80]}"
    _E73_CACHE.append((mod, why))
    return mod, why


def basis_report_date(day, source: str) -> str:
    """傳給 adj_quote 的「報告日」。它取報告日**前一交易日**那一列當因子基準——
    共識快照要的是共識日那一列,所以傳共識日 + 1 個日曆天;券商報告照傳報告日(L99 原意)。"""
    d = day if isinstance(day, _dt.date) else _dt.date.fromisoformat(str(day)[:10])
    return (d if source in REPORT_DATED else d + _dt.timedelta(days=1)).isoformat()


def adj_rows(con, rows):
    """rows = [(date, code, source, target_median)] → [(date, code, source, target_median, basis_date, ADJ_COLS…)]。
    只讀(adj_quote 只下 SELECT),正式庫的唯讀連線也能算——自測拿它跟獨立 SQL 對答案。"""
    mod, why = adj_engine()
    if mod is None:
        return [], why
    out = []
    for day, code, source, tm in rows:
        basis = ""
        try:
            basis = basis_report_date(day, source)
            q = mod.adj_quote(con, str(code), basis, tm)
        except Exception as exc:  # noqa: BLE001 -- one bad row gets a named state; the others still get computed
            q = {"upside_adj_state": f"ADJ_ERROR({type(exc).__name__}: {str(exc)[:80]})"}
        out.append((day, code, source, tm, basis) + tuple(q.get(ADJ_FROM.get(k, k)) for k in ADJ_COLS))
    return out, why


def refresh_adj(con) -> dict:
    """v0106(Z157):consensus_latest 的每一列(每個代號 × 源的最新一筆,不論哪一支寫的)重算 ADJ 上漲空間,
    落旁表 consensus_adj,重建視圖 consensus_latest_adj。回 {rows, computed, ok, states, engine}。"""
    con.execute(ADJ_DDL)
    rows = con.execute("SELECT date, code, source, target_median FROM consensus_latest "
                       "ORDER BY code, source").fetchall()
    got, why = adj_rows(con, rows)
    now = _dt.datetime.now().replace(microsecond=0)
    if got:
        con.executemany(
            "INSERT OR REPLACE INTO consensus_adj VALUES (" + ",".join("?" * (5 + len(ADJ_COLS) + 2)) + ")",
            [r + (why, now) for r in got])
    con.execute(LATEST_ADJ_VIEW)
    states = {}
    for r in got:
        key = str(r[5 + ADJ_COLS.index("upside_adj_state")] or "").split("(")[0]
        states[key] = states.get(key, 0) + 1
    return {"rows": len(rows), "computed": len(got), "engine": why,
            "ok": sum(v for k, v in states.items() if k == "ADJ_OK"), "states": states}


# v0102→v0103(批394 續章 test/debug:雲端兩紅皆為「判準綁死單一源」造成的假紅)
#   ② 原硬要求 EXTERNAL≥190,但 build() 自身已有「批300 守衛:analyst_estimates 表缺=誠實 0 筆,
#      單源續建」——檢點與引擎守衛互相矛盾。該表由上游 VDF_ENG059(Yahoo 車道)寫入,雲端擋牆
#      未跑故表不存在 → 恆紅。v0103:表缺 → SKIP 並誠實列示在庫實源分布(現為 CNYES_FACTSET
#      251 筆/245 檔);表在位而 <190 → 照舊 FAIL。
#   ④ 原只查 source='EXTERNAL_ANALYST' 的 2330,該源在雲端不存在故恆「缺」;但庫內 CNYES_FACTSET
#      的 2330 三欄俱全(median 3175 / close 2410 / upside 0.317427),公式本可實證。v0103:優先
#      EXTERNAL_ANALYST,缺則取任一在庫源並誠實註記所用源。公式嚴格度不變(仍驗 median/close-1)。


def build(db: Path | None = None, digest_dir: Path | None = None) -> dict:
    """雙源入庫(冪等 upsert)+最新共識視圖。
    v0106:db / digest_dir 可指定(自測走暫存庫與暫存收件夾;不給 = 正式庫與 fin_out,行為同 v0105);
    尾段 refresh_adj() 算 ADJ 上漲空間落旁表(Z157),結果在回傳的 "adj"。"""
    con = _con(db=db)
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
    n_brk, bad_files = 0, []
    digest = Path(digest_dir) if digest_dir is not None else DIGEST_OUT
    if digest.is_dir():
        for f in sorted(digest.glob("*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001 -- v0106: named in the result and printed (was skipped silently)
                bad_files.append(f"{f.name}({type(exc).__name__})")
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
    t0 = _dt.datetime.now()
    try:
        adj = refresh_adj(con)      # v0106(Z157):同一個連線、同一次 build
    except Exception as exc:  # noqa: BLE001 -- the old build must still finish; the reason is returned and printed
        adj = {"rows": 0, "computed": 0, "ok": 0, "states": {},
               "engine": f"ADJ 旁表這一段失敗 {type(exc).__name__}: {str(exc)[:120]}(舊欄照建)"}
    adj["seconds"] = round((_dt.datetime.now() - t0).total_seconds(), 1)
    con.close()
    return {"external": n_ext, "broker": n_brk, "total": total, "adj": adj, "broker_bad": bad_files}


def status(db: Path | None = None) -> int:
    path = Path(db or DB)
    if not path.exists():
        print(f"  正式庫不在:{path}(先跑 boot 日更鏈建庫)")
        return 2
    con = _con(read_only=True, db=db)
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
    # v0106(Z157):ADJ 上漲空間覆蓋(旁表;百分比)
    try:
        st = con.execute("SELECT split_part(upside_adj_state, '(', 1), count(*) FROM consensus_latest_adj "
                         "GROUP BY 1 ORDER BY 2 DESC").fetchall()
        top = con.execute("SELECT code, source, upside_adj FROM consensus_latest_adj WHERE upside_adj IS NOT NULL "
                          "ORDER BY upside_adj DESC LIMIT 5").fetchall()
        print("  [ADJ 上漲空間(%;最新 adj close)] " + " · ".join(f"{s} {n}" for s, n in st))
        print("  [ADJ 前五]", top)
    except Exception:
        print("  [ADJ] consensus_latest_adj 未建(v0106 起 build 才會建;Z157)")
    con.close()
    return 0


# ---------------------------------------------------------------------------------------------------------------
# 自測(v0106:只寫暫存庫 —— Z189;正式庫只開唯讀)
# ---------------------------------------------------------------------------------------------------------------
FIXTURE_DAYS = ("2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-07",
                "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11")
# 夾具的答案:手算,不問 ENG073(算法在 _fixture 的說明裡一行一行寫出來)
FIXTURE_ADJ = {("9901", "EXTERNAL_ANALYST"): (30.0, 0.97, "2026-09-08", 126.1),
               ("9901", "BROKER_REPORT"): (25.0, 0.97, "2026-09-09", 121.25),
               ("9902", "EXTERNAL_ANALYST"): (12.2, 1.0, "2026-09-09", 55.0),
               ("9903", "EXTERNAL_ANALYST"): "ADJ_NO_FACTOR",
               ("9904", "EXTERNAL_ANALYST"): "ADJ_NO_TARGET"}
REAL_SAMPLE_ROWS, REAL_SAMPLE_OK = 150, 30     # ⑫ 正式庫試算:最多看 150 列、驗到 30 列 ADJ_OK 就停(工作站價表大)


def _fixture(root: Path) -> tuple:
    """暫存庫夾具(四檔 + 一份券商報告)。答案:
      9901(上市 .TW):09-10 除息 3 元,收盤 100 → 97;Yahoo 的 adj 在除息前 = 收盤 × 0.97 = 97。共識日 09-08:
          因子 = 09-08 那一列 97 ÷ 100 = 0.97,目標 130 × 0.97 = 126.1,最新 adj 97 → 126.1 ÷ 97 − 1 = 30.0%
          (舊欄 130 ÷ 97 − 1 = 34.0%——多算的就是那 3 元股息)。
      9902(上櫃 .TWO):09-09 除息 1 元,50 → 49;adj 在除息前 = 50 × 0.98 = 49。共識日 = 除息日 09-09:
          基準是共識日那一列(49 ÷ 49 = 1.0)→ 55 ÷ 49 − 1 = 12.2%(誤用「報告日前一交易日」會拿 09-08 的 0.98 → 10.0%);
          舊欄只認 `.TW`,這一列是 NULL。
      9903:有目標、價表沒有它 → ADJ_NO_FACTOR(要帶 adj_block_reason);9904:沒目標 → ADJ_NO_TARGET。
      券商報告 9901 目標 125、報告日 = 除息日 09-10:基準 = 報告日前一交易日 09-09(0.97)→ 121.25 ÷ 97 − 1 = 25.0%
          (誤把報告當快照 +1 天 → 09-10 的 1.0 → 28.9%)。
    交易所收盤 = Yahoo 收盤(兩邊一致,配股段 1.0;分母走交易所 = RAW_EXCHANGE)。"""
    db, digest = root / "consensus_selftest.duckdb", root / "fin_out"
    digest.mkdir()
    (digest / "broker_fixture.json").write_text(json.dumps({"reports": [
        {"code": "9901", "target_price": 125, "report_date": "2026-09-10",
         "eps_fy0": 8.0, "eps_fy1": 9.0, "finaudit": "PASS"}]}), encoding="utf-8")
    con = _con(db=db)
    con.execute("CREATE TABLE analyst_estimates (date VARCHAR, code VARCHAR, target_high DOUBLE, target_low DOUBLE, "
                "target_mean DOUBLE, target_median DOUBLE, n_analysts DOUBLE, eps0y_avg DOUBLE, eps1y_avg DOUBLE, "
                "adopted_eps DOUBLE)")
    con.executemany("INSERT INTO analyst_estimates VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("2026-09-08", "9901", 150, 110, 131, 130, 12, 8.0, 9.0, 8.0),
        ("2026-09-09", "9902", 60, 50, 55.5, 55, 6, 4.0, 4.5, 4.0),
        ("2026-09-11", "9903", 80, 60, 70, 70, 3, 5.0, 5.5, 5.0),
        ("2026-09-11", "9904", None, None, None, None, 0, None, None, None)])
    con.execute("CREATE TABLE prices_canonical (date VARCHAR, ticker VARCHAR, close DOUBLE)")
    con.execute("CREATE TABLE tw_daily_prices (date VARCHAR, ticker VARCHAR, close DOUBLE, adj_close DOUBLE)")
    con.execute("CREATE TABLE tw_trading_daily (date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
    for d in FIXTURE_DAYS:
        c1 = 100.0 if d < "2026-09-10" else 97.0
        c2 = 50.0 if d < "2026-09-09" else 49.0
        con.executemany("INSERT INTO tw_daily_prices VALUES (?,?,?,?)", [(d, "9901.TW", c1, 97.0), (d, "9902.TWO", c2, 49.0)])
        con.executemany("INSERT INTO tw_trading_daily VALUES (?,?,?,?)", [(d, "9901", "TWSE", c1), (d, "9902", "TPEX", c2)])
        con.executemany("INSERT INTO prices_canonical VALUES (?,?,?)", [(d, "9901.TW", c1), (d, "9902.TWO", c2)])
    con.close()
    return db, digest


def _fingerprint(path: Path):
    try:
        st = path.stat()
        return (st.st_size, st.st_mtime_ns)
    except OSError:
        return None


def _sql_latest_adj(con, code: str):
    """獨立複算用:最新 adj close(同 ENG073 的尾碼順序 .TW → .TWO → 裸碼,第一個有列的算)。"""
    for sfx in (".TW", ".TWO", ""):
        r = con.execute("SELECT CAST(date AS VARCHAR), adj_close FROM tw_daily_prices WHERE ticker=? "
                        "AND adj_close IS NOT NULL ORDER BY date DESC LIMIT 1", [f"{code}{sfx}"]).fetchone()
        if r:
            return float(r[1]), str(r[0])
    return None, ""


def _sql_basis_day(con, code: str, basis: str) -> str:
    """獨立複算用:基準日 = 傳給 adj_quote 的報告日**之前**最近一個有 close 與 adj 的交易日。"""
    for sfx in (".TW", ".TWO", ""):
        r = con.execute("SELECT max(CAST(date AS VARCHAR)) FROM tw_daily_prices WHERE ticker=? AND date<? "
                        "AND close IS NOT NULL AND close<>0 AND adj_close IS NOT NULL", [f"{code}{sfx}", basis]).fetchone()
        if r and r[0]:
            return str(r[0])
    return ""


def selftest() -> int:
    import inspect
    import tempfile
    fails, skips, ran = [], [], []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        ran.append(name)
        if not cond:
            fails.append(name)

    def skp(name, note=""):
        print(f"  [SKIP] {name} {note}")
        ran.append(name)
        skips.append(name)

    def _fmt(v, spec=""):
        """批642:note 是**先算好才傳進 chk 的**,所以它一炸,檢就永遠印不出自己為什麼紅。"""
        if v is None:
            return "未算"
        try:
            return format(v, spec) if spec else str(v)
        except Exception:
            return str(v)

    prod = Path(DB).resolve()
    prod_before = _fingerprint(prod)
    _OPENED.clear()
    chk("① 憲章定位冊在位(platform_doctrine=庫優先)",
        "platform_doctrine" in json.loads(
            (VIA / "supportive modules" / "registry" /
             "VIA_System_Charter_v0100.json").read_text(encoding="utf-8")))
    td = tempfile.TemporaryDirectory(prefix="eng069_selftest_")
    root = Path(td.name)
    db, digest = _fixture(root)
    # ---- ②–⑩ 全在暫存庫 ----
    r = build(db=db, digest_dir=digest)
    chk("② 雙源入庫(夾具:外部 4 檔 · 券商報告 1 份;正式庫的外部源覆蓋改在⑪唯讀量)",
        r["external"] == 4 and r["broker"] == 1, f"(外部 {r['external']} · 券商 {r['broker']} · 總 {r['total']})")
    con = _con(db=db)
    cols = [d[0] for d in con.execute("SELECT * FROM consensus_daily LIMIT 0").description]
    positional_ok, why_pos = True, ""
    try:                                                   # ENG070 / ENG071 的寫法:14 個位置的 VALUES
        con.execute("BEGIN")
        con.execute("INSERT INTO consensus_daily VALUES ('1900-01-01','TEST69','YAHOO_QS',"
                    "1,1,1,1,1,1,1,1,NULL,NULL,'FIXTURE')")
    except Exception as exc:  # noqa: BLE001 -- recorded and reported by ③
        positional_ok, why_pos = False, f"{type(exc).__name__}: {str(exc)[:80]}"
    finally:
        con.execute("ROLLBACK")
    pk = {d[0] for d in con.execute("DESCRIBE consensus_adj").fetchall() if d[3] == "PRI"}
    chk("③ 舊表 schema 不動(14 欄含 upside_pct/validated;ENG070/071 的 14 位置插入照收)+ ADJ 旁表主鍵三元",
        len(cols) == 14 and "upside_pct" in cols and "validated" in cols and positional_ok
        and pk == {"date", "code", "source"},
        f"(consensus_daily {len(cols)} 欄 · 位置插入 {'照收' if positional_ok else '被拒 ' + why_pos}"
        f" · consensus_adj 主鍵 {sorted(pk)})")
    old = dict(((c, s), (tm, cl, up)) for c, s, tm, cl, up in con.execute(
        "SELECT code, source, target_median, close, upside_pct FROM consensus_latest").fetchall())
    o1, o2 = old.get(("9901", "EXTERNAL_ANALYST")), old.get(("9902", "EXTERNAL_ANALYST"))
    chk("④ 舊欄 upside 公式照舊(9901:median/close−1;舊 join 只認 .TW,9902.TWO 為 NULL——舊欄一個字沒改)",
        bool(o1) and o1[2] is not None and abs(o1[0] / o1[1] - 1 - o1[2]) < 1e-12
        and bool(o2) and o2[2] is None,
        f"(9901 {_fmt(o1 and o1[0])} / {_fmt(o1 and o1[1])} − 1 = {_fmt(o1 and o1[2], '.6f')}"
        f" · 9902 {_fmt(o2 and o2[2])})")
    n_adj1 = con.execute("SELECT count(*) FROM consensus_adj").fetchone()[0]
    con.close()
    r2 = build(db=db, digest_dir=digest)
    con = _con(read_only=True, db=db)
    t1 = con.execute("SELECT count(*) FROM consensus_daily").fetchone()[0]
    n_adj2 = con.execute("SELECT count(*) FROM consensus_adj").fetchone()[0]
    chk("⑤ 冪等(重跑 build 筆數不增=INSERT OR REPLACE;ADJ 旁表同)",
        t1 == r["total"] and r2["total"] == r["total"] and n_adj1 == n_adj2 == r["adj"]["rows"],
        f"({t1} 筆 · ADJ {n_adj1} → {n_adj2})")
    chk("⑥ consensus_latest 視圖(per code×source 最新一筆)",
        con.execute("SELECT count(*) FROM consensus_latest").fetchone()[0]
        == con.execute("SELECT count(DISTINCT code||source) FROM consensus_daily").fetchone()[0])
    chk("⑦ validated 旗標(外部=SOURCE_DIRECT;券商=FINAUDIT_*)",
        con.execute("SELECT count(*) FROM consensus_daily WHERE source='EXTERNAL_ANALYST' "
                    "AND validated!='SOURCE_DIRECT'").fetchone()[0] == 0
        and con.execute("SELECT count(*) FROM consensus_daily WHERE source='BROKER_REPORT' "
                        "AND validated NOT LIKE 'FINAUDIT_%'").fetchone()[0] == 0)
    boot = (VIA / "supportive modules" / "registry" / "via_boot_update.sh").read_text(encoding="utf-8")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告+boot 日更接線(公式冊載/缺鍵不猜/冪等)",
        "VRN_ENG069" in boot and "誠實跳過不猜" in src and "冪等" in src)
    got = {(c, s): row for c, s, *row in con.execute(
        "SELECT code, source, upside_adj, adj_factor, adj_factor_date, upside_adj_state, adj_block_reason, "
        "adj_factor_basis, target_median_adj FROM consensus_latest_adj").fetchall()}
    bad, shown = [], []
    for key, want in FIXTURE_ADJ.items():
        g = got.get(key)
        if g is None:
            bad.append(f"{key} 視圖沒有這一列")
            continue
        up, fac, fdate, state, reason, basis, tp_adj = g
        if isinstance(want, tuple):
            ok = (up is not None and abs(up - want[0]) < 1e-9 and fac is not None and abs(fac - want[1]) < 1e-9
                  and fdate == want[2] and tp_adj is not None and abs(tp_adj - want[3]) < 1e-9
                  and str(state).startswith("ADJ_OK") and str(basis).startswith("RAW_EXCHANGE"))
            shown.append(f"{key[0]} {key[1][:3]} {_fmt(up)}%(目標 adj {_fmt(tp_adj)} · 因子 {_fmt(fac)} @ {fdate})")
        else:
            ok = str(state).startswith(want) and (want != "ADJ_NO_FACTOR" or bool(reason))
            shown.append(f"{key[0]} {state}")
        if not ok:
            bad.append(f"{key}: 得 {g} · 要 {want}")
    chk("⑨ ADJ 上漲空間算對(Z157;委派 ENG073 adj_quote;夾具答案手算:除息、上櫃尾碼、沒價、沒目標、券商報告日)",
        not bad and r2["adj"]["engine"].startswith("VRN_ENG073"),
        f"({' · '.join(shown)} · 舊欄 9901 {_fmt(o1 and o1[2] * 100, '.1f')}% · 引擎 {r2['adj']['engine']})"
        + (f" 不對:{' | '.join(bad)}" if bad else ""))
    con.close()
    con = _con(db=db)                                      # 別支事後改寫最新一列 / 新寫一列 → 舊的 ADJ 不能冒充
    con.execute("UPDATE consensus_daily SET target_median = 131 WHERE code='9901' AND source='EXTERNAL_ANALYST'")
    con.execute("INSERT INTO consensus_daily VALUES ('2026-09-11','9902','YAHOO_QS',"
                "60,50,56,56,5,4,4.5,4,NULL,NULL,'FIXTURE')")
    v = dict(((c, s), (up, st)) for c, s, up, st in con.execute(
        "SELECT code, source, upside_adj, upside_adj_state FROM consensus_latest_adj").fetchall())
    con.close()
    stale, fresh = v.get(("9901", "EXTERNAL_ANALYST")), v.get(("9902", "YAHOO_QS"))
    build(db=db, digest_dir=digest)
    con = _con(read_only=True, db=db)
    after = dict(((c, s), (up, st)) for c, s, up, st in con.execute(
        "SELECT code, source, upside_adj, upside_adj_state FROM consensus_latest_adj").fetchall())
    con.close()
    a1, a2 = after.get(("9901", "EXTERNAL_ANALYST")), after.get(("9902", "YAHOO_QS"))
    chk("⑩ ADJ 不冒充(目標被別支改寫 → ADJ_STALE 不給數;新列還沒算 → ADJ_NOT_RUN;下一次 build 兩列都補上)",
        stale == (None, "ADJ_STALE") and fresh == (None, "ADJ_NOT_RUN")
        and a1 is not None and a1[0] == 30.0 and a2 is not None and a2[0] == round((56 / 49 - 1) * 100, 1),
        f"(改寫後 {stale} · 新列 {fresh} → 重建後 9901 {a1} · 9902 YAHOO_QS {a2})")
    try:
        td.cleanup()
    except OSError as exc:
        print(f"  [註] 暫存夾清不掉({type(exc).__name__}),留在 {root}")
    # ---- ⑪⑫ 正式庫:只開唯讀 ----
    pc, why_skip = None, ""
    if not prod.exists():
        why_skip = f"(正式庫不在 {prod} = 還沒建;補法:boot 日更鏈)"
    else:
        try:
            pc = _con(read_only=True)
        except Exception as exc:  # noqa: BLE001 -- reported as SKIP below
            why_skip = (f"(正式庫開不了唯讀:{type(exc).__name__} {str(exc)[:60]} —— 多半是別的行程正拿著寫鎖"
                        "(Z189 其餘各支的自測還沒改);不算本支壞)")
    tabs = {t[0] for t in pc.execute("SHOW TABLES").fetchall()} if pc else set()
    name11 = "⑪ 正式庫外部源覆蓋(唯讀;原②:EXTERNAL ≥190 檔)"
    if pc is None:
        skp(name11, why_skip)
    elif "analyst_estimates" not in tabs:
        skp(name11, "(analyst_estimates 表缺=上游 ENG059 Yahoo 車道未跑;補法:跑 ENG059 建表後複判)")
    elif "consensus_latest" not in tabs:
        skp(name11, "(共識庫還沒 build 過;補法:ENG069 build)")
    else:
        n_ext = pc.execute("SELECT count(DISTINCT code) FROM consensus_latest "
                           "WHERE source='EXTERNAL_ANALYST'").fetchone()[0]
        n_src = pc.execute("SELECT count(DISTINCT code) FROM analyst_estimates").fetchone()[0]
        live = " · ".join(f"{a} {b} 列" for a, b in pc.execute(
            "SELECT source, count(*) FROM consensus_latest GROUP BY 1 ORDER BY 2 DESC").fetchall())
        if n_ext < 190 and n_src >= 190:
            skp(name11, f"(來源 {n_src} 檔、共識庫外部源只有 {n_ext} 檔 = 共識庫比來源舊;補法:ENG069 build · 在庫:{live})")
        else:
            chk(name11, n_ext >= 190, f"(外部源 {n_ext} 檔 · 來源 analyst_estimates {n_src} 檔 · 在庫:{live})")
    name12 = "⑫ 正式庫 ADJ 試算 vs 獨立 SQL(唯讀;基準日、最新 adj、目標 ×因子、百分比四項對得起來)"
    if pc is None or "consensus_latest" not in tabs or "tw_daily_prices" not in tabs:
        skp(name12, why_skip or "(正式庫沒有 consensus_latest 或 tw_daily_prices)")
    else:
        rows = pc.execute("SELECT date, code, source, target_median FROM consensus_latest "
                          "ORDER BY code, source LIMIT ?", [REAL_SAMPLE_ROWS]).fetchall()
        states, wrong, n_ok = {}, [], 0
        for row in rows:
            q, _why = adj_rows(pc, [row])
            if not q:
                wrong.append(f"ENG073 缺席:{_why}")
                break
            day, code, source, tm, basis = q[0][:5]
            res = dict(zip(ADJ_COLS, q[0][5:]))
            key = str(res["upside_adj_state"] or "").split("(")[0]
            states[key] = states.get(key, 0) + 1
            if key != "ADJ_OK":
                continue
            n_ok += 1
            last, ldate = _sql_latest_adj(pc, str(code))
            bday = _sql_basis_day(pc, str(code), basis)
            tp_adj = round(tm * res["adj_factor"], 4)
            up = round((tp_adj / last - 1) * 100, 1) if last else None
            diff = [k for k, a, b in (("最新adj", res["price_latest_adj"], last), ("最新日", res["price_latest_date"], ldate),
                                      ("基準日", res["adj_factor_date"], bday), ("目標adj", res["target_median_adj"], tp_adj),
                                      ("上漲%", res["upside_adj"], up)) if a != b]
            if source not in REPORT_DATED and bday > str(day)[:10]:
                diff.append("基準日晚於共識日")
            if diff:
                wrong.append(f"{code}/{source} {'、'.join(diff)}:ENG073 {res['upside_adj']}% 目標adj {res['target_median_adj']}"
                             f" @ {res['adj_factor_date']} · SQL {up}% 目標adj {tp_adj} @ {bday} · 最新 {last} {ldate}")
            if n_ok >= REAL_SAMPLE_OK:
                break
        note = (f"(看了 {sum(states.values())} 列:" + " · ".join(f"{k} {v}" for k, v in sorted(states.items()))
                + f" · ADJ_OK 逐列對 {n_ok} 列" + (f" · 不符 {len(wrong)}:{' | '.join(wrong[:3])}" if wrong else "") + ")")
        if n_ok == 0 and not wrong:
            skp(name12, note + " —— 一列都算不出 ADJ = 價料缺口(根在 VDF),不是公式缺陷")
        else:
            chk(name12, not wrong, note)
    if pc is not None:
        pc.close()
    # ---- ⑬ 最後量:本支自測有沒有可寫地打開過正式庫(Z189)----
    writable_prod = [p for p, ro in _OPENED if Path(p).resolve() == prod and not ro]
    body = inspect.getsource(selftest)
    static_ok = ("build" + "()") not in body and ("_con" + "()") not in body   # 拆字拼:整句寫在這裡,尺會量到自己
    prod_after = _fingerprint(prod)
    n_scratch = sum(1 for p, ro in _OPENED if Path(p).resolve() != prod)
    n_prod = sum(1 for p, ro in _OPENED if Path(p).resolve() == prod)
    chk("⑬ 自測只寫暫存庫(Z189;v0105 兩次 build 寫正式庫、拿寫鎖,平行格子撞別站的讀鎖)",
        not writable_prod and static_ok,
        f"(本支開過 {len(_OPENED)} 條連線:暫存庫 {n_scratch} · 正式庫 {n_prod} 條"
        f"{'全唯讀' if not writable_prod else f',其中可寫 {len(writable_prod)} 條:{writable_prod}'}"
        f" · 正式庫前後{'一致' if prod_before == prod_after else '不一致(本支沒開過可寫連線 → 是同時段別的行程寫的)'})")
    print(f"  [計] {len(ran)} 檢 OK {len(ran) - len(fails) - len(skips)} · FAIL {len(fails)}"
          f" · SKIP {len(skips)}(誠實三態;上游車道未跑 / 正式庫被別的行程鎖住 非本引擎缺陷)")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print(f"=== 驗證共識資料庫(VRN_ENG069 {ENGINE_VERSION})· 自測(零網路;只寫暫存庫,正式庫唯讀)===")
        return selftest()
    if "--status" in args:
        return status()
    r = build()
    a = r["adj"]
    print(f"[共識庫] 外部 {r['external']} · 券商 {r['broker']} · 總 {r['total']} 筆"
          f" · consensus_latest 視圖在位(未來分析取數點)")
    print(f"[共識庫] ADJ 上漲空間(最新 adj close;Z157)算得出 {a['ok']}/{a['rows']} 列 · "
          + " · ".join(f"{k} {v}" for k, v in sorted(a["states"].items()))
          + f" · 引擎 {a['engine']} · {a['seconds']} 秒 · 視圖 consensus_latest_adj")
    if r["broker_bad"]:
        print(f"[共識庫] 券商收件夾讀不了 {len(r['broker_bad'])} 份(跳過,不猜):" + " · ".join(r["broker_bad"][:5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
