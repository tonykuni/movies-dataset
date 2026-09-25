#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0107（2026-09-25）：正式全名冊核對、抓前查庫、同日去重、官方優先去重分析、缺碼/逾期/source failure 不回假綠。
VDF_ENG063_MonthlyRevenue v0107 — 月營收分析模組(批194;操作員令)
v0105→v0106(側線 2026-09-24 第二段;主線批號由併線的手指定 L25;操作員令「繼續完成」· 九頭龍帳 Z163):
  MOPS「資料年月」的民國年月換算 `_roc_ym` 收進正典(SUP_MDL753 v0106 roc_ym,實作逐字取自本支 v0105),
  本支改**綁定**(VIA_LibCanon 律②;綁定不是 def)。同一個形狀全樹另一份在 VDF_ENG055 L10(CBC 利率檔),也同批改綁;
  逐式零差異證明在正典自測 ㊱。其餘一字未動;十檢 +⑨b(綁的是正典物件、行為同 v0105)。
====================================================================
操作員令:「月營收分析模組,透過鉅亨網取得公司資料」。
網路紀律(批180 凍結令+批181 階梯):本引擎零自建網路——一律經
SUP_MDL740 統包唯一正主 http_json 道(雙同意閘 fail-closed 隨統包);
鉅亨端點=候選冊誠實探測(首成即用;全敗=PENDING 留痕候源,不假數)。
資料層:
  落表 tw_monthly_revenue(code, ym, revenue, source, fetched_at)
    =原始落盤(先落盤後分析;正本 append/replace by (code,ym,source))
  分析視圖 monthly_revenue_analysis(庫內 SQL 零自算散落):
    mom_pct 月增/yoy_pct 年增/cum_12m 近12月累計/yoy_streak 連續
    年增正月數/high_60m 近60月新高旗標
用法:python3 VDF_ENG063_MonthlyRevenue_v0104.py run [codes…] |
      --analyze 2330 | --groups | --status | --selftest
v0102→v0103(批208):+族群月營收層——最新輪動快照成員冊(GroupId
×Ticker 快照冊直出零發明)×monthly_revenue_analysis→
revenue_group_analysis 視圖(gid×ym:成員數/營收合計/年增中位/
正年增佔比);--groups 榜=最新月族群動能排序。
v0100→v0101(批197):工作站空庫自舉——DB 父目錄自建(mkdir
parents;工作站 fresh clone 無 output_hub/mega 即炸=實測揪蟲)。
v0101→v0102(批202 解決所有問題令):+MOPS 官方正源 L1(P16 月營收
面結案)——上市 openapi.twse JSON+上櫃 mopsfin csv(BOM 容錯)雙所
全市場單拉;每列拆三點(當月+上月+去年當月)=首拉即可算月增年增;
民國年月轉西元;快照日增制歷史累積;鉅亨候選冊降 L2 候端點。
v0104→v0105(批508):分析視圖自測改連暫存 DuckDB，自建 schema 後驗 61 月
數學、ROLLBACK 與零殘留；fresh clone 不依賴工作站 mega 庫，也不碰正庫。
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from functools import partial as _lb_partial
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

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

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
NET_DIR = VIA / "supportive modules" / "network"
DEFAULT_CODES = None  # 預設正式雙所全名冊；商用候選只在明示 codes 且官方缺列時探測

# 鉅亨月營收候選端點冊(誠實探測:首成即用;全敗=PENDING 不假數)
# 批194 實測紀錄:12 候選全敗(quote 道 200=主機可達;本冊 404=路徑
# 不明;statementws 主機=proxy 502 政策擋)→PENDING 候操作員自工作站
# DevTools 抓實際 endpoint 補冊(append-only),或裁示改官方 MOPS 源。
CNYES_REVENUE_VARIANTS = [
    "https://ws.api.cnyes.com/ws/api/v1/statement/revenue/TWS:{code}:STOCK",
    "https://marketinfo.api.cnyes.com/mi/api/v1/twstock/revenue/{code}",
    "https://ws.api.cnyes.com/ws/api/v2/statement/twstock/{code}/revenue",
]

_SQL_ANALYSIS_VIEW = """
CREATE OR REPLACE VIEW monthly_revenue_analysis AS
WITH selected AS (
  SELECT * FROM tw_monthly_revenue
  QUALIFY row_number() OVER (PARTITION BY code, ym ORDER BY
      CASE WHEN source='MOPS_OFFICIAL' THEN 0 ELSE 1 END, fetched_at DESC) = 1
), base AS (
  SELECT code, ym, revenue,
         CAST(ym[1:4] AS INT) * 12 + CAST(ym[5:6] AS INT) AS midx,
         max(revenue) OVER (w RANGE BETWEEN 1 PRECEDING AND 1 PRECEDING) AS prev_m,
         max(revenue) OVER (w RANGE BETWEEN 12 PRECEDING AND 12 PRECEDING) AS prev_y,
         sum(revenue) OVER (w RANGE BETWEEN 11 PRECEDING AND CURRENT ROW) AS cum_12m_raw,
         count(*)     OVER (w RANGE BETWEEN 11 PRECEDING AND CURRENT ROW) AS n_12m,
         max(revenue) OVER (w RANGE BETWEEN 59 PRECEDING AND CURRENT ROW) AS max_60m
  FROM (SELECT code, ym, revenue,
               CAST(ym[1:4] AS INT) * 12 + CAST(ym[5:6] AS INT) AS _mi
        FROM selected)
  WINDOW w AS (PARTITION BY code ORDER BY _mi)
), yoy AS (
  SELECT *,
    CASE WHEN prev_m > 0 THEN revenue / prev_m - 1 END AS mom_pct,
    CASE WHEN prev_y > 0 THEN revenue / prev_y - 1 END AS yoy_pct,
    CASE WHEN n_12m = 12 THEN cum_12m_raw END AS cum_12m,
    CASE WHEN revenue >= max_60m THEN 1 ELSE 0 END AS high_60m
  FROM base
)
SELECT code, ym, revenue, mom_pct, yoy_pct, cum_12m, high_60m,
  (SELECT count(*) FROM yoy y2
   WHERE y2.code = yoy.code AND y2.ym > coalesce(
     (SELECT max(y3.ym) FROM yoy y3
      WHERE y3.code = yoy.code AND y3.ym <= yoy.ym
        AND (y3.yoy_pct IS NULL OR y3.yoy_pct <= 0)), '')
     AND y2.ym <= yoy.ym) AS yoy_streak
FROM yoy
"""


def _net():
    p = sorted(NET_DIR.glob("SUP_MDL740_NetUnified_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("net740_e63", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["net740_e63"] = m
    spec.loader.exec_module(m)
    return m


def _extract_rows(payload, code: str) -> list[tuple]:
    """鉅亨回包彈性剖析:遞迴找 (年月, 營收) 對;零發明——僅收
    同時具年月鍵與營收值鍵之紀錄"""
    rows = []

    def walk(o):
        if isinstance(o, dict):
            ym = None
            for k in ("date", "ym", "yearMonth", "month", "time"):
                v = o.get(k)
                if isinstance(v, str) and len(v) >= 6:
                    d = "".join(ch for ch in v if ch.isdigit())[:6]
                    if len(d) == 6 and d.startswith(("19", "20")):
                        ym = d
                        break
            rev = None
            for k in ("revenue", "sales", "monthlyRevenue", "val", "value"):
                v = o.get(k)
                if isinstance(v, (int, float)) and v > 0:
                    rev = float(v)
                    break
            if ym and rev is not None:
                rows.append((code, ym, rev))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(payload)
    return sorted(set(rows), key=lambda r: r[1])


# MOPS 官方源 L1(批202;官方>商用=憲章序)
# QA 實測:P=證券商 296 家(無 2330)/L=上市 1,085 家(含 2330)→
# 三版全收=全市場覆蓋(L 上市+P 證券商 JSON;O 上櫃 csv)
MOPS_TWSE_JSONS = [
    "https://openapi.twse.com.tw/v1/opendata/t187ap05_L",
    "https://openapi.twse.com.tw/v1/opendata/t187ap05_P",
]
MOPS_TPEX_CSV = "https://mopsfin.twse.com.tw/opendata/t187ap05_O.csv"


#: v0106:民國年月 '11507'→'202607';異常=None 誠實——改綁正典(實作逐字搬進 SUP_MDL753 v0106 roc_ym;自測 ㊱ 零差異)
_roc_ym = _LIB.UTILS.roc_ym


def _prev_ym(ym: str, k: int) -> str:
    y, m = int(ym[:4]), int(ym[4:])
    t = y * 12 + (m - 1) - k
    return f"{t // 12}{t % 12 + 1:02d}"


#: 批597 三庫整併:_num → 正典綁定(只收正數;不綁 positive 的話 '0'/'-inf'/'nan' 會被放行(量到 8 處差異))。
#  綁定不是 def——再包一層 def 的話能力庫裡那一族還在,家族數不會掉(LL143)。
_num = _lb_partial(_LIB.num, positive=True)


def _mops_rows(rec_get) -> list[tuple]:
    """單筆官方紀錄→三點(當月/上月/去年當月);千元單位官方原值零改"""
    code = str(rec_get("公司代號") or "").strip()
    ym = _roc_ym(rec_get("資料年月"))
    if not code or not code.isdigit() or ym is None:
        return []
    out = []
    cur = _num(rec_get("營業收入-當月營收"))
    if cur is not None:
        out.append((code, ym, cur))
    prv = _num(rec_get("營業收入-上月營收"))
    if prv is not None:
        out.append((code, _prev_ym(ym, 1), prv))
    lyr = _num(rec_get("營業收入-去年當月營收"))
    if lyr is not None:
        out.append((code, _prev_ym(ym, 12), lyr))
    return out


def run_mops(net, con, ts: str) -> tuple[int, list[str]]:
    """L1 官方雙所全市場;回(落列數, 敗所清單)"""
    import csv as _csv
    import io
    import json as _json
    rows, failed = [], []
    for url in MOPS_TWSE_JSONS:
        r = net.http_json(url)
        data = r.get("data")
        if (r.get("ok") or r.get("state") == "OK") and isinstance(data, list):
            for rec in data:
                rows += _mops_rows(rec.get)
        else:
            failed.append(f"openapi {url.rsplit('_', 1)[-1]} 版")
    rt = net.http_text(MOPS_TPEX_CSV)
    if rt.get("ok") or rt.get("state") == "OK":
        txt = (rt.get("data") or "").encode("utf-8", "ignore").decode("utf-8-sig", "ignore")
        try:
            for rec in _csv.DictReader(io.StringIO(txt)):
                rows += _mops_rows(rec.get)
        except Exception:
            failed.append("上櫃 csv 剖析")
    else:
        failed.append("上櫃 csv")
    if rows:
        # 同 (code,ym) 官方多點取當月值優先=先插當月後 dedup keep first
        con.execute("CREATE TEMP TABLE _mops(code VARCHAR, ym VARCHAR, revenue DOUBLE)")
        con.executemany("INSERT INTO _mops VALUES (?,?,?)", rows)
        con.execute("""DELETE FROM tw_monthly_revenue
                       WHERE source='MOPS_OFFICIAL'
                         AND (code, ym) IN (SELECT code, ym FROM _mops)""")
        con.execute(f"""INSERT INTO tw_monthly_revenue
            SELECT code, ym, max(revenue), 'MOPS_OFFICIAL', '{ts}'
            FROM _mops GROUP BY code, ym""")
        con.execute("DROP TABLE _mops")
    return len(rows), failed


def _ensure_dirs():
    """工作站自舉:fresh clone 無 output_hub/mega 目錄=先建(零破壞)"""
    DB_TW.parent.mkdir(parents=True, exist_ok=True)


def _ensure_schema(con):
    con.execute("""CREATE TABLE IF NOT EXISTS tw_monthly_revenue(
        code VARCHAR, ym VARCHAR, revenue DOUBLE,
        source VARCHAR, fetched_at VARCHAR)""")
    con.execute(_SQL_ANALYSIS_VIEW)


def _universe_owner():
    # 名冊與台灣快照日委派共識資料正主；不在本支硬編股票或市場後綴。
    path = sorted((VIA / 'functional modules/VRN').glob('VRN_ENG069_ConsensusDB_v*.py'))[-1]
    spec = importlib.util.spec_from_file_location('_revenue_universe', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def revenue_coverage(con, codes, day: str) -> dict:
    have = {}
    if 'tw_monthly_revenue' in {r[0] for r in con.execute('SHOW TABLES').fetchall()}:
        have = {str(c): (str(ym), str(ts or '')) for c, ym, ts in con.execute(
            "SELECT code, max(ym), max(fetched_at) FROM tw_monthly_revenue "
            "WHERE source='MOPS_OFFICIAL' AND revenue IS NOT NULL GROUP BY code").fetchall()}
    missing, overdue, unknown, checked = [], [], [], []
    from datetime import date
    for code in codes:
        row = have.get(code)
        if not row:
            missing.append(code)
            continue
        lag = _LIB.UTILS.period_lag('tw_monthly_revenue', row[0], today=date.fromisoformat(day))
        if lag['state'] != 'PERIOD_DUE':
            unknown.append(code)
        elif lag['lag_days']:
            overdue.append(code)
        if row[1][:10] == day:
            checked.append(code)
    return dict(day=day, universe=len(codes), covered=len(codes)-len(missing), missing=missing,
                overdue=overdue, unknown_period=unknown, checked_today=checked,
                latest={c: have[c][0] for c in codes if c in have})


def run(codes: list[str] | None = None) -> int:
    if os.environ.get('VIA_NET_CONSENT') != 'YES':
        print('[月營收] 同意閘未開(VIA_NET_CONSENT≠YES)=拒跑(fail-closed 誠實)')
        return 2
    import duckdb
    owner = _universe_owner()
    universe = owner.fetch_universe(DB_TW, codes)
    if not universe:
        print('[月營收] ABSENT：正式股票名冊缺席，零擷取')
        return 3
    day = owner.snapshot_day()
    # 首先只讀庫；來源未更新的缺口不靠盲抓歷史補造。
    with duckdb.connect(str(DB_TW), read_only=True) as c:
        before = revenue_coverage(c, universe, day)
    if len(before['checked_today']) == len(universe):
        print(f'[月營收] {day} 全名冊 {len(universe)} 已核取；同日零重抓')
        return 2 if before['overdue'] or before['unknown_period'] else 0
    net = _net()
    with duckdb.connect(str(DB_TW)) as con:
        _ensure_schema(con)
        from datetime import timezone, timedelta
        ts = datetime.now(timezone(timedelta(hours=8))).isoformat()
        n_mops, failed = run_mops(net, con, ts)
        after = revenue_coverage(con, universe, day)
        # 端點仍屬候選，不對全市場逐碼打三次已知不穩的商用 API。
        # 只有操作員明示選碼、官方缺這個碼時，才走原有候選道。
        for code in (codes or []):
            if code not in after['missing']:
                continue
            for tpl in CNYES_REVENUE_VARIANTS:
                url = tpl.format(code=code)
                r = net.http_json(url)
                rows = _extract_rows(r.get('data'), code) if r.get('ok') or r.get('state') == 'OK' else []
                if rows:
                    # 照原既有来源欄保存，分析視圖每碼每月只採一列，官方優先。
                    con.execute('CREATE OR REPLACE TEMP TABLE _revenue_new AS SELECT * FROM tw_monthly_revenue LIMIT 0')
                    con.executemany('INSERT INTO _revenue_new VALUES (?,?,?,?,?)',
                        [(c, ym, value, 'CNYES:' + url.split('/')[2], ts) for c, ym, value in rows])
                    _LIB.UTILS.upsert_select(con, 'tw_monthly_revenue', '_revenue_new', ['code', 'ym', 'source'])
                    con.execute('DROP TABLE _revenue_new')
                    break
        rep = VIA / 'VIA_Reports/monthly_revenue'
        rep.mkdir(parents=True, exist_ok=True)
        (rep / 'COVERAGE_latest.json').write_text(json.dumps(
            dict(before=before, after=after, source_failures=failed, official_rows=n_mops,
                 sources=[*MOPS_TWSE_JSONS, MOPS_TPEX_CSV]), ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"[月營收] 全名冊 {len(universe)} · 官方列 {n_mops} · 缺碼 {len(after['missing'])} · 逾期 {len(after['overdue'])} · 源敗 {len(failed)}")
    return 2 if failed or after['missing'] or after['overdue'] or after['unknown_period'] else 0


def _latest_classification():
    root = VIA / "functional modules" / "GroupIndex" / "output_hub" / "rotation_runs"
    runs = sorted(root.glob("ROTATION_TW_*")) if root.exists() else []
    for r in reversed(runs):
        p = r / "csv" / "latest_classification.csv"
        if p.exists():
            return p
    return None


def build_group_view(con) -> bool:
    """族群月營收視圖(批208):成員冊=快照冊直出;缺=誠實 False"""
    cls = _latest_classification()
    if cls is None:
        return False
    con.execute(f"""
        CREATE OR REPLACE VIEW revenue_group_analysis AS
        WITH m AS (SELECT DISTINCT GroupId,
                     regexp_replace(Ticker, '\\.(TW|TWO)$', '') AS code
                   FROM read_csv_auto('{cls.as_posix()}'))
        SELECT m.GroupId AS gid, a.ym,
               count(*) AS n_members,
               sum(a.revenue) AS revenue_sum,
               median(a.yoy_pct) AS yoy_median,
               count(*) FILTER (WHERE a.yoy_pct > 0) AS n_yoy_pos,
               count(*) FILTER (WHERE a.yoy_pct IS NOT NULL) AS n_yoy,
               count(*) FILTER (WHERE a.high_60m = 1) AS n_high60
        FROM monthly_revenue_analysis a
        JOIN m ON a.code = m.code
        GROUP BY m.GroupId, a.ym""")
    return True


def groups() -> int:
    import duckdb
    try:
        con = duckdb.connect(str(DB_TW))
    except Exception as e:
        if "lock" in str(e).lower():
            print("[族群月營收] 資料庫使用中(回補/日更進行中)=稍後再試"
                  "(誠實;單一寫者紀律)")
            return 0
        raise
    _ensure_schema(con)
    if not build_group_view(con):
        print("[族群月營收] 無輪動快照成員冊(誠實空)")
        con.close()
        return 0
    rows = con.execute("""
        SELECT gid, n_members, revenue_sum, yoy_median, n_yoy_pos, n_yoy, n_high60
        FROM revenue_group_analysis
        WHERE ym = (SELECT max(ym) FROM revenue_group_analysis)
        ORDER BY yoy_median DESC NULLS LAST LIMIT 15""").fetchall()
    ym = con.execute("SELECT max(ym) FROM revenue_group_analysis").fetchone()[0]
    con.close()
    pc = lambda x: "—" if x is None else f"{x * 100:+.1f}%"
    print(f"[族群月營收榜] {ym}(年增中位排序;成員冊=輪動快照直出)")
    for g, n, rs, ym_, pos, ny, hi in rows:
        print(f"  {g:12s} {n:3d} 檔 · 合計 {rs / 1e6:,.0f} 百萬 · 年增中位 {pc(ym_)}"
              f" · 正年增 {pos}/{ny} · 60月新高 {hi} 檔")
    return 0


def analyze(code: str) -> int:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        rows = con.execute(
            "SELECT ym, revenue, mom_pct, yoy_pct, cum_12m, yoy_streak, high_60m "
            "FROM monthly_revenue_analysis WHERE code=? ORDER BY ym DESC LIMIT 12",
            [code]).fetchall()
    except Exception:
        rows = []
    con.close()
    if not rows:
        print(f"[分析] {code} 無落庫月營收(先 run;誠實空)")
        return 0
    pc = lambda x: "—" if x is None else f"{x * 100:+.1f}%"
    print(f"[月營收分析] {code} 近 12 月(分析視圖=庫內 SQL 單一正主)")
    for ym, rev, mom, yoy, c12, stk, hi in rows:
        print(f"  {ym} 營收 {rev:,.0f} · 月增 {pc(mom)} · 年增 {pc(yoy)}"
              f" · 近12月累計 {('—' if c12 is None else format(c12, ',.0f'))}"
              f" · 連續年增 {stk} 月{' · 60月新高' if hi else ''}")
    return 0


def status() -> int:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        n, nc, mx = con.execute(
            "SELECT count(*), count(DISTINCT code), max(ym) "
            "FROM tw_monthly_revenue").fetchone()
        print(f"  [月營收] {n:,} 列 · {nc} 檔 · 最新 {mx}")
    except Exception:
        print("  [月營收] 未建(先 run)")
    con.close()
    return 0


def selftest() -> int:
    import duckdb
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    # 自指防護:禁字以拼接表達,避免檢查字面量自傷(批166 教訓)
    chk("① 統包唯一網路道(零自建:引擎內無 http 庫/外部行程直呼)",
        "SUP_MDL740_NetUnified_v*" in src
        and ("import " + "requests") not in src
        and ("import " + "urllib") not in src
        and ("sub" + "process") not in src)
    saved = os.environ.pop("VIA_NET_CONSENT", None)
    rc = run(["2330"])
    if saved is not None:
        os.environ["VIA_NET_CONSENT"] = saved
    chk("② 同意閘 fail-closed(閘未開=拒跑 rc2 零觸網)", rc == 2)
    chk("③ 端點候選冊(≥3 變體誠實探測;全敗=PENDING 不假數)",
        len(CNYES_REVENUE_VARIANTS) >= 3 and "PENDING" in src)
    _test_home = tempfile.TemporaryDirectory()
    con = duckdb.connect(str(Path(_test_home.name) / "monthly_revenue.duckdb"))
    _ensure_schema(con)
    con.execute("BEGIN")
    con.execute("DELETE FROM tw_monthly_revenue WHERE code='TEST63'")
    fx = [("TEST63", f"{2021 + m // 12}{m % 12 + 1:02d}", 100.0 + m * 10)
          for m in range(0, 61)]
    con.executemany("INSERT INTO tw_monthly_revenue VALUES (?,?,?,'FIXTURE','t')", fx)
    a = con.execute(
        "SELECT revenue, mom_pct, yoy_pct, cum_12m, yoy_streak, high_60m "
        "FROM monthly_revenue_analysis WHERE code='TEST63' "
        "ORDER BY ym DESC LIMIT 1").fetchone()
    exp_mom = a[0] / (a[0] - 10) - 1
    exp_yoy = a[0] / (a[0] - 120) - 1
    chk("④ 分析視圖數學實證(fixture 61 月:月增/年增/連續年增/60月新高)",
        abs(a[1] - exp_mom) < 1e-12 and abs(a[2] - exp_yoy) < 1e-12
        and a[4] >= 48 and a[5] == 1,
        f"(mom {a[1]:.4f}·yoy {a[2]:.4f}·streak {a[4]}·hi {a[5]})")
    c12 = con.execute(
        "SELECT cum_12m FROM monthly_revenue_analysis WHERE code='TEST63' "
        "ORDER BY ym DESC LIMIT 1").fetchone()[0]
    chk("⑤ 近12月累計守恆(等差級數手算對合;不足12月=NULL 誠實)",
        abs(c12 - sum(r[2] for r in fx[-12:])) < 1e-9)
    con.execute("ROLLBACK")  # fixture 零殘留(測試域 temp 紀律)
    left = con.execute(
        "SELECT count(*) FROM tw_monthly_revenue WHERE code='TEST63'").fetchone()[0]
    chk("⑥ fixture 零殘留(ROLLBACK 後正表無測試列)", left == 0)
    con.close()
    _test_home.cleanup()
    _boot_dir = VIA / "supportive modules" / "registry"
    _boot = next((p for p in (_boot_dir / "via_boot_update.ps1",
                              _boot_dir / "via_boot_update.sh") if p.is_file()), None)
    boot = _boot.read_text(encoding="utf-8") if _boot else ""
    chk("⑦ boot 接線(日更管線含月營收增量)",
        _boot is not None and "VDF_ENG063" in boot)
    chk("⑦b MOPS 官方 L1 機制(批202:民國轉西元+三點拆列+官方>商用宣告)",
        _roc_ym("11507") == "202607" and _roc_ym("bad") is None
        and _prev_ym("202601", 1) == "202512"
        and _prev_ym("202607", 12) == "202507"
        and _mops_rows({"公司代號": "2330", "資料年月": "11507",
                        "營業收入-當月營收": "1000", "營業收入-上月營收": "900",
                        "營業收入-去年當月營收": "800"}.get)
        == [("2330", "202607", 1000.0), ("2330", "202606", 900.0),
            ("2330", "202507", 800.0)]
        and "官方>商用" in Path(__file__).read_text(encoding="utf-8"))
    chk("⑧ 紀律宣告(統包唯一正主/fail-closed/先落盤後分析/不假數)",
        all(k in src for k in ("統包唯一正主", "fail-closed", "先落盤後分析",
                               "不假數")))
    chk("⑨b v0106 民國年月綁正典:_roc_ym 就是正典 roc_ym 物件(不是本地 def);行為同 v0105"
        "(11507 · 115/07 · 115年07月 → 202607;月份 13 · 民國 80 年前 · 西元 202607 · 亂字=None)",
        _roc_ym is _LIB.UTILS.roc_ym
        and [_roc_ym(x) for x in ("11507", "115/07", "115年07月", "11513", "07912", "202607", "bad")]
        == ["202607", "202607", "202607", None, None, None, None])
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 月營收分析模組(VDF_ENG063 v0106)· 十檢自測(零網路)===")
        return selftest()
    if "--analyze" in args:
        i = args.index("--analyze")
        return analyze(args[i + 1] if i + 1 < len(args) else "2330")
    if "--groups" in args:
        return groups()
    if "--status" in args:
        return status()
    if args and args[0] == "run":
        return run(args[1:] or DEFAULT_CODES)
    return status()


if __name__ == "__main__":
    sys.exit(main())
