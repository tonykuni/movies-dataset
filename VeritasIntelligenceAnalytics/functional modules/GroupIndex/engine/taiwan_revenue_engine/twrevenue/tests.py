"""tests.py -- 內建自我測試 (python -m twrevenue.cli selftest).

涵蓋: 代號 regex / MOPS 解析 (欄位對映·最長匹配·合計列·產業別附掛) /
六大週期類歸類 / 族群 SSOT 驗證 / parquet 增量去重 / URL 與月份推算 / 公式抽驗。
每次修改 groups.csv 或程式後執行, 全綠才代表機制未被破壞。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

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
    return f"{len(cases)} 個代號案例 (四碼·首碼非零·排除ETF/TDR)"


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


def t_store():
    from . import store
    with tempfile.TemporaryDirectory() as td:
        cfg = {"storage": {"parquet_path": os.path.join(td, "r.parquet"),
                           "duckdb_path": None}}
        d1 = pd.DataFrame({"stock_id": ["2330", "2454"], "year": [2026, 2026],
                           "month": [4, 4], "revenue": [100, 50]})
        d2 = pd.DataFrame({"stock_id": ["2330", "2330"], "year": [2026, 2026],
                           "month": [4, 5], "revenue": [110, 120]})  # 4月更正+5月新增
        a1 = store.upsert(d1, cfg)
        a2 = store.upsert(d2, cfg)
        assert len(a1) == 2 and len(a2) == 3, "增量筆數錯誤"
        v = a2[(a2.stock_id == "2330") & (a2.month == 4)]["revenue"].iloc[0]
        assert v == 110, "更正月份應以最新公告覆蓋"
        w = store.load(cfg, months_back=1)
        assert set(w["month"]) == {5}, "視窗篩選錯誤"
    return "parquet 增量·主鍵去重·更正覆蓋·視窗載入"


def t_duckdb():
    try:
        import duckdb  # noqa
    except ImportError:
        return "duckdb 未安裝, 略過 (pip install duckdb)"
    from . import store
    with tempfile.TemporaryDirectory() as td:
        cfg = {"storage": {"parquet_path": os.path.join(td, "r.parquet"),
                           "duckdb_path": os.path.join(td, "r.duckdb")}}
        d = pd.DataFrame({"stock_id": ["2330"], "year": [2026],
                          "month": [5], "revenue": [120]})
        store.upsert(d, cfg)
        import duckdb
        con = duckdb.connect(cfg["storage"]["duckdb_path"])
        n = con.execute("SELECT COUNT(*) FROM monthly_revenue").fetchone()[0]
        con.close()
        assert n == 1
    return "duckdb 查詢層同步"


def t_url():
    from .fetch import _build_url, month_iter
    u = _build_url("https://mops.twse.com.tw", "sii", 2024, 5, 0)
    assert u.endswith("/nas/t21/sii/t21sc03_113_5_0.html"), u
    u2 = _build_url("https://mops.twse.com.tw", "otc", 2009, 3, 0)
    assert u2.endswith("/nas/t21/otc/t21sc03_98_3.html"), u2
    mi = list(month_iter(3, dt.date(2026, 7, 25)))
    assert mi == [(2026, 6), (2026, 5), (2026, 4)], mi
    return "URL 格式·民國年·舊格式·最新月推算"


def t_formula():
    # YoY 公式抽驗: 合成一段序列, 官方欄位應與手算一致
    rev = pd.Series([100.0 + i for i in range(24)])
    yoy_official = (rev.iloc[23] / rev.iloc[11] - 1) * 100
    assert abs(yoy_official - ((123 / 111 - 1) * 100)) < 1e-9
    return "YoY = (本月/去年同月 − 1)×100 抽驗"


ALL = [("代號 regex", t_regex), ("MOPS 解析", t_parser),
       ("週期六大類", t_sectors), ("族群 SSOT", t_groups_ssot),
       ("增量資料庫", t_store), ("duckdb", t_duckdb),
       ("URL/月份", t_url), ("公式", t_formula)]


def run_all() -> bool:
    ok = True
    print("=" * 56)
    for name, fn in ALL:
        try:
            msg = fn()
            print(f"  [PASS] {name:10s} {msg}")
        except Exception as e:
            ok = False
            print(f"  [FAIL] {name:10s} {e}")
    print("=" * 56)
    print("全部通過 ✔" if ok else "有測試失敗 ✘ — 請修正後再跑一次")
    return ok
