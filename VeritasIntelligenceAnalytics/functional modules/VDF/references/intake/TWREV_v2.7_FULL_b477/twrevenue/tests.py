"""tests.py -- 內建自我測試 (python -m twrevenue.cli selftest).

涵蓋: 代號 regex / MOPS 解析 / 六大週期類 / 族群 SSOT / parquet 增量 /
      duckdb / URL 與月份推算 / 公式 / 真突破偵測 (含 ground truth)。
"""
from __future__ import annotations

import datetime as dt
import os
import re
import tempfile

import numpy as np
import pandas as pd

_MOCK_HTML = """<html><body><table border=1>
<tr><td colspan=11>產業別：水泥工業</td></tr>
<tr><th>公司代號</th><th>公司名稱</th><th>當月營收</th><th>上月營收</th>
<th>去年當月營收</th><th>上月比較增減(%)</th><th>去年同月增減(%)</th>
<th>當月累計營收</th><th>去年累計營收</th><th>前期比較增減(%)</th><th>備註</th></tr>
<tr><td>1101</td><td>台泥</td><td>8,000,000</td><td>7,500,000</td><td>9,000,000</td>
<td>6.67</td><td>-11.11</td><td>40,000,000</td><td>45,000,000</td><td>-11.11</td><td></td></tr>
<tr><td>合計</td><td></td><td>8,000,000</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td colspan=11>產業別：半導體業</td></tr>
<tr><th>公司代號</th><th>公司名稱</th><th>當月營收</th><th>上月營收</th>
<th>去年當月營收</th><th>上月比較增減(%)</th><th>去年同月增減(%)</th>
<th>當月累計營收</th><th>去年累計營收</th><th>前期比較增減(%)</th><th>備註</th></tr>
<tr><td>2330</td><td>台積電</td><td>256,000,000</td><td>240,000,000</td><td>200,000,000</td>
<td>6.67</td><td>28.00</td><td>1,200,000,000</td><td>980,000,000</td><td>22.45</td><td></td></tr>
</table></body></html>"""


def t_regex():
    from .fetch import STOCK_ID_REGEX
    cases = {"2330": True, "1101": True, "0050": False, "00878": False,
             "911616": False, "999": False, "12345": False}
    for k, e in cases.items():
        assert bool(re.match(STOCK_ID_REGEX, k)) == e, f"regex {k}"
    return f"{len(cases)} 案例 (四碼·首碼非零·排除ETF/TDR)"


def t_parser():
    from .fetch import _parse_html
    df = _parse_html(_MOCK_HTML)
    assert list(df["stock_id"]) == ["1101", "2330"], "合計列應剔除"
    assert df.loc[df.stock_id == "2330", "revenue"].iloc[0] == 256000000, \
        "當月營收不可被『去年當月營收』覆蓋 (最長匹配)"
    assert df.loc[df.stock_id == "2330", "revenue_prev_year"].iloc[0] == 200000000
    assert df.loc[df.stock_id == "1101", "industry"].iloc[0] == "水泥工業"
    assert df.loc[df.stock_id == "2330", "industry"].iloc[0] == "半導體業"
    assert abs(df.loc[df.stock_id == "2330", "cum_yoy"].iloc[0] - 22.45) < 1e-9
    return "欄位對映·最長匹配·合計列剔除·產業別附掛"


def t_sectors():
    from .classify import tag_cyclical
    t = pd.DataFrame({
        "stock_id": ["1101", "2002", "1301", "6505", "1710",
                     "2603", "2605", "2641", "2610", "2607", "2105", "2330"],
        "industry": ["水泥工業", "鋼鐵工業", "塑膠工業", "油電燃氣業", "化學工業",
                     "航運業", "航運業", "航運業", "航運業", "航運業",
                     "橡膠工業", "半導體業"]})
    r = tag_cyclical(t, ["航運業"]).set_index("stock_id")["cyclical_sector"]
    exp = {"1101": "水泥", "2002": "鋼鐵", "1301": "石化", "6505": "石化",
           "1710": "化工", "2603": "貨櫃航運", "2605": "散裝航運",
           "2641": "散裝航運", "2610": None, "2607": "航運其他",
           "2105": "其他週期", "2330": None}
    for sid, e in exp.items():
        got = r[sid]
        got = None if pd.isna(got) else got
        assert got == e, f"{sid}: {got} != {e}"
    return "六大類對映·航運細分·航空豁免"


def t_groups_ssot():
    from .fetch import STOCK_ID_REGEX
    from .groups import load_groups
    g = load_groups()
    assert not g.empty, "groups.csv 不可為空"
    bad = g[~g["stock_id"].str.match(STOCK_ID_REGEX)]
    assert bad.empty, f"代號不符規則: {bad['stock_id'].tolist()}"
    assert g["role"].isin(["L", "P", "G"]).all(), "role 僅允許 L/P/G"
    dup = g[g.duplicated(subset=["stock_id", "group"], keep=False)]
    assert dup.empty, f"同族群內重複代號: {dup['stock_id'].tolist()}"
    no_leader = [grp for grp, d in g.groupby("group") if (d.role == "L").sum() == 0]
    assert not no_leader, f"無龍頭的族群: {no_leader}"
    return f"{g['group'].nunique()} 群 / {g['stock_id'].nunique()} 檔 · 代號·角色·去重·龍頭齊備"


def t_groups_two_level():
    """兩階層 SSOT: parent 全覆蓋 / 樹狀 / 細分零遺漏 / status 值域."""
    from .groups import load_groups, CYCLICAL_PARENTS
    g, allg = load_groups(), load_groups(include_flagged=True)
    assert "parent" in allg.columns, "groups.csv 缺 parent 欄 (兩階層)"
    assert allg["parent"].notna().all() and (allg["parent"] != "").all(), \
        "有子族群未指派 L1 大類"
    ok = {"", "flagged", "excluded", "superseded"}
    assert allg["status"].isin(list(ok)).all(), \
        f"status 值域外: {set(allg['status']) - ok}"
    # 一個子族群只能屬於一個大類 (階層必須是樹, 不可是圖)
    multi = (allg.groupby("group")["parent"].nunique() > 1)
    assert not multi.any(), f"子族群跨多個大類: {multi[multi].index.tolist()}"
    # superseded (已被細分取代) 的成員必須全數出現在某個生效子族群 -> 零遺漏
    sup = allg[allg["status"] == "superseded"]
    lost = sorted(set(sup["stock_id"]) - set(g["stock_id"]))
    assert not lost, f"細分後遺漏個股: {lost}"
    # 每個生效子族群都必須有龍頭 (VIA 規則), 且大類本身不可當子族群名用
    assert CYCLICAL_PARENTS <= set(allg["parent"]), "週期大類名稱與 CSV 不一致"
    return (f"{g['parent'].nunique()} 大類 / {g['group'].nunique()} 子族群 · "
            f"樹狀·零遺漏·status 值域")


def t_groups_parent_dedupe():
    """L1 加總必須依個股去重: 同一檔跨兩個子族群不得被重複計入."""
    from .groups import group_momentum, dedupe_members
    g = pd.DataFrame([
        {"stock_id": "2330", "name": "A", "parent": "半導體", "group": "晶圓代工",
         "role": "L", "market": "上市"},
        {"stock_id": "2330", "name": "A", "parent": "半導體", "group": "CoWoS",
         "role": "P", "market": "上市"},
        {"stock_id": "3711", "name": "B", "parent": "半導體", "group": "CoWoS",
         "role": "L", "market": "上市"},
    ])
    dd = dedupe_members(g)
    assert len(dd) == 2, "去重後應剩 2 檔"
    assert dd.set_index("stock_id").loc["2330", "role"] == "L", \
        "去重須保留角色最高者 (龍頭不可被降級)"
    a = pd.DataFrame({
        "stock_id": ["2330", "3711"], "name": ["A", "B"],
        "revenue": [100.0, 50.0], "revenue_prev_year": [80.0, 50.0],
        "cum_revenue": [1000.0, 500.0], "cum_revenue_prev_year": [800.0, 500.0],
        "cum_yoy": [25.0, 0.0], "yoy": [25.0, 0.0], "score": [70.0, 50.0],
        "tier": ["優選", "一般"], "yoy_accelerating": [True, False]})
    cfg = {"analyze": {"cum_yoy_strong": 10.0}}
    p = group_momentum(a, g, cfg, level="parent")
    assert len(p) == 1 and p.iloc[0]["members"] == 2, "L1 成員數應為去重後 2"
    exp = round((150 / 130 - 1) * 100, 1)          # 去重: (100+50)/(80+50)-1
    dupv = round((250 / 210 - 1) * 100, 1)         # 未去重: 2330 被算兩次
    got = p.iloc[0]["agg_yoy"]
    assert got != dupv, f"L1 加總重複計入個股 (得 {got}%)"
    assert got == exp, f"L1 加總 YoY 應為 {exp}%, 實得 {got}%"
    assert p.iloc[0]["n_subgroups"] == 2, "n_subgroups 應在去重前計算"
    return f"去重加總 {exp}% (未去重為 {dupv}%) · 角色保留 · 子群數 2"


def t_store():
    from . import store
    with tempfile.TemporaryDirectory() as td:
        cfg = {"storage": {"parquet_path": os.path.join(td, "r.parquet"),
                           "duckdb_path": None}}
        d1 = pd.DataFrame({"stock_id": ["2330", "2454"], "year": [2026, 2026],
                           "month": [4, 4], "revenue": [100, 50]})
        d2 = pd.DataFrame({"stock_id": ["2330", "2330"], "year": [2026, 2026],
                           "month": [4, 5], "revenue": [110, 120]})
        a1 = store.upsert(d1, cfg)
        a2 = store.upsert(d2, cfg)
        assert len(a1) == 2 and len(a2) == 3, "增量筆數錯誤"
        v = a2[(a2.stock_id == "2330") & (a2.month == 4)]["revenue"].iloc[0]
        assert v == 110, "更正月份應以最新公告覆蓋"
        assert set(store.load(cfg, months_back=1)["month"]) == {5}, "視窗篩選錯誤"
    return "parquet 增量·主鍵去重·更正覆蓋·視窗載入"


def t_duckdb():
    try:
        import duckdb  # noqa: F401
    except ImportError:
        return "duckdb 未安裝, 略過"
    from . import store
    with tempfile.TemporaryDirectory() as td:
        cfg = {"storage": {"parquet_path": os.path.join(td, "r.parquet"),
                           "duckdb_path": os.path.join(td, "r.duckdb")}}
        store.upsert(pd.DataFrame({"stock_id": ["2330"], "year": [2026],
                                   "month": [5], "revenue": [120]}), cfg)
        import duckdb
        con = duckdb.connect(cfg["storage"]["duckdb_path"])
        n = con.execute("SELECT COUNT(*) FROM monthly_revenue").fetchone()[0]
        con.close()
        assert n == 1
    return "duckdb 查詢層同步"


def t_url():
    from .fetch import _build_url, month_iter
    assert _build_url("https://mops.twse.com.tw", "sii", 2024, 5, 0).endswith(
        "/nas/t21/sii/t21sc03_113_5_0.html")
    assert _build_url("https://mops.twse.com.tw", "otc", 2009, 3, 0).endswith(
        "/nas/t21/otc/t21sc03_98_3.html")
    assert list(month_iter(3, dt.date(2026, 7, 25))) == [(2026, 6), (2026, 5), (2026, 4)]
    return "URL 格式·民國年·舊格式·最新月推算"


def t_formula():
    rev = pd.Series([100.0 + i for i in range(24)])
    assert abs((rev.iloc[23] / rev.iloc[11] - 1) * 100 - (123 / 111 - 1) * 100) < 1e-9
    return "YoY = (本月/去年同月 − 1)×100"


# ── 真突破偵測: 已知答案驗證 ─────────────────────────────────
def _gt_cfg():
    import yaml
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "config.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["demo"] = dict(cfg.get("demo") or {})
    cfg["demo"]["universe_size"] = 200      # 測試用小宇宙
    return cfg


def t_breakout_gt():
    """三種已知型態必須被正確分類 — 這是反低基期濾網的核心驗收."""
    from .synth import make_synthetic
    from . import classify, breakout as B
    cfg = _gt_cfg()
    d = classify.tag_cyclical(make_synthetic(cfg), cfg["cyclical_industries"])
    bo = B.detect(d, cfg)
    expect = {"9001": B.V_REAL, "9002": B.V_REAL, "9003": B.V_REAL,
              "9101": B.V_LOWBASE, "9102": B.V_LOWBASE, "9201": B.V_ONEOFF}
    for sid, exp in expect.items():
        row = bo[bo.stock_id == sid]
        assert len(row), f"{sid} 未進候選池"
        got = row["verdict"].iloc[0]
        assert got == exp, f"{sid}: 期望 {exp}, 實得 {got}"
    return f"{len(expect)} 個 ground truth 全中 (真突破/低基期/單月暴衝)"


def t_breakout_logic():
    """低基期假象的 YoY 必須高於真突破, 卻仍被擋下 — 證明濾網不是靠 YoY 高低."""
    from .synth import make_synthetic
    from . import classify, breakout as B
    cfg = _gt_cfg()
    d = classify.tag_cyclical(make_synthetic(cfg), cfg["cyclical_industries"])
    bo = B.detect(d, cfg).set_index("stock_id")
    fake_yoy = bo.loc["9101", "yoy"]
    real_yoy = bo.loc["9001", "yoy"]
    assert fake_yoy > real_yoy, "測試案例設計失效: 假突破 YoY 應高於真突破"
    assert bo.loc["9101", "verdict"] == B.V_LOWBASE, "高 YoY 的低基期股未被擋下"
    # 關卡本身必須各自成立
    assert not bo.loc["9101", "g1_ath"], "低基期股不應是歷史新高"
    assert not bo.loc["9101", "g4_base"], "低基期股應在基期關卡被擋"
    assert not bo.loc["9101", "g5_cagr"], "低基期股兩年 CAGR 應不及格"
    assert bo.loc["9001", "g4_base"] and bo.loc["9001", "g5_cagr"], "真突破應通過基期與兩年關卡"
    # 週期股一律排除
    assert (bo[bo["is_cyclical"]]["verdict"] == B.V_CYCLICAL).all(), "週期股應全數排除"
    return (f"假突破 YoY {fake_yoy:.0f}% > 真突破 {real_yoy:.0f}% 仍被擋下; "
            f"關卡獨立性與週期排除正確")


def t_breakout_math():
    """突破指標的數學正確性 (ATH / TTM / 基期百分位 / 兩年CAGR)."""
    from . import breakout as B
    cfg = _gt_cfg()
    # 構造 30 個月: 前 24 月 = 100, 第 25-29 月 = 120, 最後一月 = 200
    n = 30
    rev = [100.0] * 24 + [120.0] * 5 + [200.0]
    dates = pd.date_range("2024-01-01", periods=n, freq="MS")
    g = pd.DataFrame({"stock_id": ["T001"] * n, "name": ["測試"] * n,
                      "industry": ["半導體業"] * n, "date": dates,
                      "revenue": rev, "yoy": [np.nan] * n, "is_cyclical": [False] * n})
    m = B.compute_breakout_metrics(g, cfg)
    assert m["is_ath"] is True, "200 應為歷史新高"
    assert abs(m["ath_margin"] - (200 / 120 - 1) * 100) < 1e-9, "超越前高幅度錯誤"
    assert m["ath_streak"] == 1, "只有最後一月創高 -> streak=1"
    # 去年同月 = index -13 = 第 17 個 (值 100)
    assert m["base_revenue"] == 100.0, "去年同月取值錯誤"
    assert abs(m["yoy"] - 100.0) < 1e-9, "YoY 應為 +100%"
    # 兩年前 = index -25 = 值 100 -> CAGR = sqrt(2)-1
    assert abs(m["cagr_2y"] - ((200 / 100) ** 0.5 - 1) * 100) < 1e-9, "兩年CAGR 錯誤"
    # 基期比: 基期月之前 12 個月中位數 = 100 -> ratio = 1.0
    assert abs(m["base_ratio"] - 1.0) < 1e-9, "基期比錯誤"
    return "ATH·超越幅度·streak·去年同月·YoY·2年CAGR·基期比 全部對得上"


def t_taxonomy_ssot():
    """SSOT 自我稽核: 別名指向合法、階層完整、無正式名/別名衝突."""
    from . import taxonomy as T
    a = T.audit()
    assert not a["bad_alias"], f"別名指向不存在的正式名: {a['bad_alias']}"
    assert not a["bad_l1"], f"L1 大類不合法: {a['bad_l1']}"
    assert not a["conflict"], f"字串同時是正式名與別名: {a['conflict']}"
    # 每個正式名都要有 L1/L2
    for canon, (l1, l2) in T.HIERARCHY.items():
        assert l1 in T.L1_ORDER and l2, f"{canon} 階層不完整"
    # 電子八大次產業必須齊備 (TWSE 電子類指數成分)
    eight = {"半導體業", "電腦及週邊設備業", "光電業", "通信網路業",
             "電子零組件業", "電子通路業", "資訊服務業", "其他電子業"}
    for e in eight:
        assert T.HIERARCHY[e][0] == T.L1_ELEC, f"{e} 應屬電子"
    assert T.HIERARCHY["金融保險"][0] == T.L1_FIN
    return (f"{a['n_canon']} 正式產業別 / {a['n_alias']} 組同義字 · "
            f"電子八大齊備 · 無衝突")


def t_taxonomy_normalize():
    """TWSE / TPEX 命名差異必須正規化到同一個正式名 (整合的核心)."""
    from . import taxonomy as T
    cases = {
        # TPEX 後綴 -> TWSE 正式名
        "建材營造業": "建材營造", "金融保險業": "金融保險",
        "貿易百貨業": "貿易百貨", "其他業": "其他",
        # 歷史更名
        "觀光事業": "觀光餐旅", "觀光餐飲": "觀光餐旅",
        # VIA 族群簡稱 -> 官方產業別
        "半導體": "半導體業", "電腦週邊": "電腦及週邊設備業",
        "鋼鐵": "鋼鐵工業", "金融": "金融保險", "航運": "航運業",
        # 正式名原樣通過
        "半導體業": "半導體業", "光電業": "光電業",
        # 上櫃專有
        "文化創意業": "文化創意業", "農業科技業": "農業科技業", "電子商務": "電子商務",
        # 空白/全形容忍
        " 半導體業 ": "半導體業",
    }
    for src, exp in cases.items():
        got = T.normalize(src)
        assert got == exp, f"normalize({src!r}) = {got!r}, 期望 {exp!r}"
    # 三分法歸屬
    assert T.levels("半導體")[1] == T.L1_ELEC
    assert T.levels("金融保險業")[1] == T.L1_FIN
    assert T.levels("鋼鐵工業")[1:] == (T.L1_NONELEC, "原物料")
    assert T.levels("電子商務")[1] == T.L1_NONELEC, "電子商務屬零售, 不應歸電子"
    # 歷史混類不得被拆成化學工業 (會把生技誤判成原物料週期)
    assert T.normalize("化學生技醫療") == "化學生技醫療"
    assert T.levels("化學生技醫療")[2].startswith("混類")
    # 未知產業回 None (由 attach 歸入「其他」並標 unknown)
    assert T.normalize("不存在的產業XYZ") is None
    return f"{len(cases)} 組命名變體正規化正確 · 三分法歸屬正確 · 混類不誤拆"


def t_taxonomy_cyclical_consistency():
    """正規化後, 命名變體不可造成週期歸類分裂."""
    from .classify import tag_cyclical
    t = pd.DataFrame({
        "stock_id": ["1101", "2002", "9001", "9002", "9003", "9004"],
        "industry": ["水泥工業", "鋼鐵工業", "觀光事業", "觀光餐旅",
                     "化學生技醫療", "金融保險業"]})
    r = tag_cyclical(t, []).set_index("stock_id")
    assert r.loc["1101", "cyclical_sector"] == "水泥"
    assert r.loc["2002", "cyclical_sector"] == "鋼鐵"
    # 觀光的兩種寫法必須歸到同一個正式名, 且都不是週期
    assert r.loc["9001", "industry_canon"] == r.loc["9002", "industry_canon"] == "觀光餐旅"
    assert not r.loc["9001", "is_cyclical"] and not r.loc["9002", "is_cyclical"]
    # 歷史混類不可被當成原物料週期
    assert not r.loc["9003", "is_cyclical"], "化學生技醫療不應自動歸週期 (會誤殺生技)"
    assert r.loc["9003", "industry_ambiguous"]
    assert r.loc["9004", "sector_l1"] == "金融"
    return "命名變體歸類一致 · 混類不誤判週期 · 階層欄位正確附掛"


def t_intl_ssot():
    """國際對照自我稽核: 每個台股產業別都有 GICS、三套標準對映完整."""
    from . import intl as I
    a = I.audit()
    assert not a["missing_industry"], f"未對映 GICS 的產業別: {a['missing_industry']}"
    assert not a["bad_gics"], f"GICS sector 名稱不合法: {a['bad_gics']}"
    assert not a["yf_missing"], f"GICS->yfinance 缺漏: {a['yf_missing']}"
    assert not a["icb_missing"], f"GICS->ICB 缺漏: {a['icb_missing']}"
    assert not a["super_missing"], f"yfinance sector 缺 super sector: {a['super_missing']}"
    assert not a["bad_override"], f"ticker 覆寫指向不合法 sector: {a['bad_override']}"
    assert len(I.GICS_SECTORS) == 11, "GICS 應為 11 個 sector"
    assert len(I.GICS_TO_YF) == 11 and len(set(I.GICS_TO_YF.values())) == 11, \
        "GICS <-> yfinance 應為一對一"
    assert set(I.YF_SUPER.values()) == {"Cyclical", "Defensive", "Sensitive"}, \
        "Morningstar 應為 3 個 super sector"
    return (f"{a['n_industry']} 台股產業別 -> 11 GICS sectors · "
            f"GICS↔yfinance 一對一 · ICB 完整 · {a['n_override']} 檔覆寫")


def t_intl_mapping():
    """關鍵對映正確性 (含跨 sector 的 ticker 覆寫)."""
    from . import intl as I
    # 台股產業別 -> GICS
    cases = {
        "半導體業": "Information Technology", "金融保險": "Financials",
        "鋼鐵工業": "Materials", "生技醫療業": "Health Care",
        "航運業": "Industrials", "食品工業": "Consumer Staples",
        "汽車工業": "Consumer Discretionary", "文化創意業": "Communication Services",
        "油電燃氣業": "Utilities", "建材營造": "Real Estate",
    }
    for ind, exp in cases.items():
        got = I.gics_of(ind)[0]
        assert got == exp, f"{ind} -> {got}, 期望 {exp}"
    # ticker 覆寫: 中華電屬通信網路業, 但 GICS 應為 Communication Services
    assert I.gics_of("通信網路業", "2412")[0] == "Communication Services"
    assert I.gics_of("通信網路業", "2345")[0] == "Information Technology", "設備商應留在 IT"
    assert I.gics_of("油電燃氣業", "6505")[0] == "Energy", "台塑化(煉油)應為 Energy"
    assert I.gics_of("貿易百貨", "2912")[0] == "Consumer Staples", "統一超應為必需消費"
    # GICS -> yfinance 名稱不同, 不可直接字串比對
    assert I.GICS_TO_YF["Information Technology"] == "Technology"
    assert I.GICS_TO_YF["Consumer Discretionary"] == "Consumer Cyclical"
    assert I.GICS_TO_YF["Financials"] == "Financial Services"
    # Morningstar super sector
    assert I.YF_SUPER["Technology"] == "Sensitive"
    assert I.YF_SUPER["Financial Services"] == "Cyclical"
    assert I.YF_SUPER["Healthcare"] == "Defensive"
    # yfinance ticker
    assert I.yf_ticker("2330", "上市") == "2330.TW"
    assert I.yf_ticker("6488", "上櫃") == "6488.TWO"
    assert I.yf_ticker("3081", "otc") == "3081.TWO"
    return f"{len(cases)} 組產業對映 · 4 檔 ticker 覆寫 · super sector · yf ticker 全正確"


def t_csv_encoding():
    """CSV 必須是 UTF-8 + BOM, 否則繁中 Windows 的 Excel 會用 CP950 解讀成亂碼."""
    from . import csvio
    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, "t.csv")
        df = pd.DataFrame({"stock_id": ["2330"], "name": ["台積電"],
                           "group": ["半導體"], "market": ["上市"]})
        csvio.write(df, fp)
        assert csvio.has_bom(fp), "輸出 CSV 缺少 BOM -> Excel 會亂碼"
        # 讀回必須完全還原, 且欄名不可殘留 BOM 字元
        back = csvio.read(fp, dtype={"stock_id": str})
        assert list(back.columns) == list(df.columns), \
            f"欄名被 BOM 汙染: {list(back.columns)}"
        assert back["name"].iloc[0] == "台積電", "中文未正確還原"
        # 非 pandas 的下游若用純 utf-8 開檔, BOM 會殘留在第一個欄名;
        # 這就是 csvio.read 一律用 utf-8-sig 的理由。
        # (pandas 3.x 的 read_csv 會自動吃掉 BOM, 但 open() 不會)
        with open(fp, encoding="utf-8") as f:
            assert f.readline().startswith("﻿"), "BOM 應存在於檔案開頭"
        with open(fp, encoding="utf-8-sig") as f:
            assert f.readline().startswith("stock_id"), "utf-8-sig 應吃掉 BOM"
        # 無 BOM 的舊檔也要能讀 (向下相容)
        fp2 = os.path.join(td, "t2.csv")
        df.to_csv(fp2, index=False, encoding="utf-8")
        assert not csvio.has_bom(fp2)
        assert csvio.read(fp2, dtype={"stock_id": str})["name"].iloc[0] == "台積電"
    return "輸出帶 BOM · 讀回無汙染 · 相容無 BOM 舊檔"


def t_csv_all_outputs_bom():
    """所有已產出的 CSV 都必須帶 BOM (含 groups.csv 與 data/ 下的輸出)."""
    from . import csvio
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    targets = [os.path.join(here, "twrevenue", "groups.csv")]
    dd = os.path.join(here, "data")
    if os.path.isdir(dd):
        targets += [os.path.join(dd, f) for f in sorted(os.listdir(dd))
                    if f.endswith(".csv")]
    checked = [t for t in targets if os.path.exists(t)]
    bad = [os.path.basename(t) for t in checked if not csvio.has_bom(t)]
    assert not bad, f"這些 CSV 缺 BOM (Excel 會亂碼): {bad}"
    return f"{len(checked)} 個 CSV 全部帶 BOM"


ALL = [("代號 regex", t_regex), ("MOPS 解析", t_parser),
       ("CSV 編碼", t_csv_encoding), ("CSV 全輸出", t_csv_all_outputs_bom),
       ("階層 SSOT", t_taxonomy_ssot), ("階層 正規化", t_taxonomy_normalize),
       ("階層 週期一致", t_taxonomy_cyclical_consistency),
       ("國際 SSOT", t_intl_ssot), ("國際 對映", t_intl_mapping),
       ("週期六大類", t_sectors), ("族群 SSOT", t_groups_ssot),
       ("族群 兩階層", t_groups_two_level),
       ("族群 L1去重加總", t_groups_parent_dedupe),
       ("增量資料庫", t_store), ("duckdb", t_duckdb),
       ("URL/月份", t_url), ("公式", t_formula),
       ("突破·數學", t_breakout_math),
       ("突破·已知答案", t_breakout_gt),
       ("突破·反低基期", t_breakout_logic)]


def run_all() -> bool:
    ok = True
    print("=" * 72)
    for name, fn in ALL:
        try:
            print(f"  [PASS] {name:14s} {fn()}")
        except Exception as e:
            ok = False
            print(f"  [FAIL] {name:14s} {type(e).__name__}: {e}")
    print("=" * 72)
    print("全部通過 ✔" if ok else "有測試失敗 ✘ — 請修正後再跑一次")
    return ok
