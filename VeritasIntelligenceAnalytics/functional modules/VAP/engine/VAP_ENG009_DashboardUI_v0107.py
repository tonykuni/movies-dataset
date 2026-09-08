#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG009_DashboardUI — VIA 儀表板原始版(批167;操作員 Layout element 定案)
====================================================================
操作員令:Layout element(CSS+JS 全文)=版面規劃定案。本引擎收容整合:
  版面值單源=VIA_UI_TemplateSSOT.json「dashboard」節(批167 append 收錄
    定案值:260px Gate Panel/38px 表頭/圖卡 320-420px/斷點 768/字 11→10/
    tick 檔位冊);CSS 由冊生成,引擎零寫死
  結構=操作員規格原樣:PC 左右兩欄(左 Gate Panel 篩選+收合、右圖表區)
    /Mobile 上下佈局;Alerts+Audit Logs;Auto-Fixer(欄位檢/日期解析/
    補齊日期/補值/IQR 極端值平滑)+Auto-Optimizer(尺寸/字級/欄列自調)
  實料嵌入(AI 只整理不發明):vdf_tw_market.duckdb 三檔(2330/2317/2454)
    收盤+量+三法人買賣超,近 240 交易日;零網路零 CDN 單檔可離線開
  QA 修正(誠實留痕,結構零改):①autoFixData 欄位檢誤用 !df.date(陣列
    恆真)→ 檢首列鍵 ②fillMissingDates 回傳 fixed.df 未接線→接回
    ③「線性插值」實為前值遞補→註記正名 ④IQR 分位未濾 null→濾
    ⑤optimizePlotly 未防 Plotly 缺席→typeof 閘(零 CDN:預設內建 SVG
    車道,環境有 Plotly 時自動升級)
用法:python3 VAP_ENG009_DashboardUI_v0107.py run | --selftest
v0106→v0107(批400;工作站實錄 批397 via-famui「YELLOW vap VAP 儀表板 DATA … rc1;舊頁在位」=
  vdf_tw_market.duckdb 缺 tw_listings 等表 → 裸 duckdb.CatalogException traceback rc1 不誠實):
  +缺料前檢 preflight(唯讀零網路:版面冊/duckdb·pandas 件/正典庫檔/七表 tw_listings·prices_canonical·
  tw_chip_inst·tw_chip_margin·tw_trading_daily·tw_valuation_daily·features_daily/輪動快照 csv)→
  [缺料]/[缺件] 逐項指路可填之令(via-price=ENG054·via-chip=ENG056·via-py vdf ENG057 run/ENG055 run/
  ENG060 build/ENG061 build;via-tval/via-omni 未登錄=不指死路)誠實停 rc2,末二行=摘要+補料
  (MDL138 只存尾二行各 160 字);庫忙=讓庫律(批399 ENG056 同律 6×3s)[FAIL] rc3 指路 via-bg;
  渲染中例外=一行定位(缺表 rc2/庫忙 rc3/缺件 rc2/非預期 rc1)零裸 traceback;舊頁在位不以空殼覆蓋
  (庫檔缺亦停,不再 rc0 出空頁);正常渲染路徑 build/harvest_*/CSS/JS/HTML 位元組零改;
  自測十二檢保留(缺料時 ②–⑫ 誠實 SKIP 指路,不記 FAIL)+⑬缺料前檢 ⑭run 路誠實停 ⑮庫忙/缺件/
  非預期/渲染中缺表四路 ⑯子行程實跑零 Traceback=十六檢(無料沙盒亦 rc0);MDL138 判定:rc2+舊頁在位
  =DATA/YELLOW(頁缺時 rc≠0=FAIL/RED,需 MDL138 冊該項加 data_gate;本批不動 MDL138)。
v0105→v0106(批330 操作員嚴令):量=CGC_MDL118 三階扣當沖(無料=null 非原始量)+volume_raw 對照欄+dt_source;
價=prices_canonical(調整後;既合律一);頁註印律 stamp;v0105 零觸碰。[VIA:PLOTDATA-LAW:v0100]
v0104→v0105(批191):因子庫消費端接軌——個股層+因子快照列
  (features_daily=VDF_ENG061 單一因子正主庫取:日/20 日/60 日報酬
  ×年化波動×MA20/60 乖離×52 週高點距離×量能 Z;頁內零自算=
  同功能整併去重;NULL=視窗不足誠實顯示 —)。
v0103→v0104(批178):價格源切換正典調整層 prices_canonical(操作員
  令:調整後 OHLC=下游一切輸入;VDF_ENG060;close=adj_close,
  data_class=DERIVED_ADJ_FACTOR 於 note 誠實標示)。
v0102→v0103(批173):全球層——層級三分(個股/族群/全球):
  全球=ROTATION_GLOBAL 最新快照(glob 尾版)9 類別(US/歐洲三分/
  亞洲三分/大中華/商品)×類別指數 FULL_EW/成交值 PROXY/金流佔比
  PROXY/正廣度+宏觀因子四線(EURUSD/USDJPY/VIX/US10Y_D1=全球共通
  不隨類別);延續榜通用化(族群/全球同表)。誠實標記:TURNOVER_
  PROXY(價×量估算非所值)+profile=REVIEW 非 PASS(V13 裁定)全頁宣告。
v0101→v0102(批172):族群視角層——Gate Panel +「層級」下拉(個股/
  族群);族群層=GRP_ENG040 輪動 tw 最新快照(glob 尾版 ROTATION_TW_*)
  實料:六模組(族群指數 FULL_EW/成交值/金流佔比/正廣度/外資/投信
  金額)+輪動態燈(RotationState×Confidence)+金流佔比延續榜(最新
  日×5 日均×佔比變化;榜=快照冊直出零發明);副圖=金流佔比長條。
v0100→v0101(批169):深化系統連動——模組車道 5→8(+成交值/融資餘額/
  融券餘額,tw_trading_daily+tw_chip_margin 實料 639-640 日);主副雙圖
  (chart-grid 第二卡=成交量副圖,操作員規格原生支援);估值快照
  (tw_valuation_daily)誠實現值列(僅 2 快照日,不足作圖不假圖)。
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

import importlib
import json
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
SSOT = VIA / "supportive modules" / "registry" / "VIA_UI_TemplateSSOT_v0100.json"
DB = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"

def _plot_law():
    """CGC_MDL118 PlotDataLaw 尾版(批330;缺=None 誠實)"""
    import importlib.util
    hits = sorted((VIA / "supportive modules" / "registry").glob("CGC_MDL118_PlotDataLaw_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("via_plot_law", hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules["via_plot_law"] = m
    spec.loader.exec_module(m)
    return m

UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_Dashboard_v0100.html"

STOCKS = ["2330", "2317", "2454"]   # 原始版示範檔(儀表板下拉;實料嵌入)
N_SESS = 240


def load_dash_tokens() -> dict:
    return json.loads(SSOT.read_text(encoding="utf-8"))["dashboard"]


def harvest_data() -> dict:
    """duckdb 實料(唯讀):收盤/量/三法人買賣超;缺庫=誠實空+alert"""
    if not DB.exists():
        return {"stocks": {}, "note": "資料庫缺席(誠實)"}
    import duckdb
    con = duckdb.connect(str(DB), read_only=True)
    names = dict(con.execute(
        "SELECT code, name FROM tw_listings WHERE code IN ('2330','2317','2454')"
    ).fetchall())
    out = {}
    for c in STOCKS:
        px = con.execute(
            "SELECT date, close, volume FROM prices_canonical "
            "WHERE ticker=? ORDER BY date DESC LIMIT ?", [f"{c}.TW", N_SESS]
        ).fetchall()[::-1]
        ch = dict((r[0], r[1:]) for r in con.execute(
            "SELECT date, foreign_net, trust_net, dealer_net FROM tw_chip_inst "
            "WHERE code=? ORDER BY date DESC LIMIT ?", [c, N_SESS]).fetchall())
        mg = dict((r[0], r[1:]) for r in con.execute(
            "SELECT date, margin_bal, short_bal FROM tw_chip_margin "
            "WHERE code=? ORDER BY date DESC LIMIT ?", [c, N_SESS]).fetchall())
        tv = dict((r[0], r[1]) for r in con.execute(
            "SELECT date, trade_value FROM tw_trading_daily "
            "WHERE code=? ORDER BY date DESC LIMIT ?", [c, N_SESS]).fetchall())
        val = con.execute(
            "SELECT date, pe, pb, dividend_yield FROM tw_valuation_daily "
            "WHERE code=? ORDER BY date DESC LIMIT 1", [c]).fetchall()
        # 批191:因子快照=features_daily 庫取(VDF_ENG061;頁內零自算=
        # 消費端接軌,單一因子正主)
        ft = con.execute(
            "SELECT date, ret_1d, ret_20d, ret_60d, vol_20d_ann, ma20_ratio, "
            "ma60_ratio, hi252_dist, volu_z20 FROM features_daily "
            "WHERE ticker=? ORDER BY date DESC LIMIT 1", [f"{c}.TW"]).fetchall()
        # 批330 律二:量→扣當沖三階(無料=None;原始量保留 volume_raw;dt_source 逐列)
        law = _plot_law()
        vmap, smap, cov = {}, {}, {}
        if law is not None and px:
            import pandas as _pd
            d_, cov = law.ex_daytrade(_pd.DataFrame({"Date": [str(r[0]) for r in px], "Volume": [r[2] or 0 for r in px]}), c)
            vmap = {str(dd): (None if _pd.isna(v) else float(v)) for dd, v in zip(d_["Date"], d_["Volume"])}
            smap = {str(dd): s_ for dd, s_ in zip(d_["Date"], d_["DTSource"])}
        out[c] = {
            "name": names.get(c, c),
            "law": (law.stamp(cov) if law and cov else "量律缺"),
            "factors": ({"date": str(ft[0][0]),
                         "ret_1d": ft[0][1], "ret_20d": ft[0][2],
                         "ret_60d": ft[0][3], "vol_20d_ann": ft[0][4],
                         "ma20_ratio": ft[0][5], "ma60_ratio": ft[0][6],
                         "hi252_dist": ft[0][7], "volu_z20": ft[0][8]}
                        if ft else None),
            "valuation": ({"date": str(val[0][0]), "pe": val[0][1], "pb": val[0][2],
                           "yield": val[0][3]} if val else None),
            "rows": [{"date": str(d), "close": v, "volume": vmap.get(str(d)[:10]) if vmap else None,
                      "volume_raw": vol, "dt_source": smap.get(str(d)[:10], "NONE"),
                      "foreign": (ch.get(str(d)) or [None])[0],
                      "trust": (ch.get(str(d)) or [None, None])[1],
                      "dealer": (ch.get(str(d)) or [None, None, None])[2],
                      "margin": (mg.get(str(d)) or [None])[0],
                      "short": (mg.get(str(d)) or [None, None])[1],
                      "tvalue": tv.get(str(d))}
                     for d, v, vol in px]}
    con.close()
    return {"stocks": out, "note": f"vdf_tw_market prices_canonical(調整後價)· 近 {N_SESS} 交易日"}


def harvest_rotation(top_n: int = 12, days: int = 240) -> dict:
    """GRP_ENG040 輪動 tw 最新快照(glob 尾版;唯讀零重測):
    族群日列+輪動態+金流佔比延續榜。缺快照=誠實空。"""
    root = VIA / "functional modules" / "GroupIndex" / "output_hub" / "rotation_runs"
    runs = sorted(root.glob("ROTATION_TW_*")) if root.exists() else []
    if not runs:
        return {"groups": {}, "rank": [], "note": "無輪動快照(誠實)"}
    src = runs[-1]
    try:
        import pandas as pd
        df = pd.read_csv(src / "csv" / "group_rotation_daily.csv")
    except Exception as e:
        return {"groups": {}, "rank": [], "note": f"快照讀取敗(誠實):{e}"[:120]}
    df["Date"] = df["Date"].str.replace("/", "-")
    last = df["Date"].max()
    latest = df[df["Date"] == last].copy()
    top = (latest.sort_values("GroupTurnoverValue", ascending=False)
           .head(top_n)["GroupId"].tolist())
    dates = sorted(df["Date"].unique())[-days:]
    sub = df[df["GroupId"].isin(top) & df["Date"].isin(dates)]

    def _f(v):
        return None if pd.isna(v) else round(float(v), 6)

    groups = {}
    for gid, g in sub.groupby("GroupId"):
        g = g.sort_values("Date")
        tail = g.iloc[-1]
        groups[gid] = {
            "state": str(tail.get("RotationState", "")),
            "conf": _f(tail.get("RotationConfidence")),
            "rows": [{"date": r["Date"], "gindex": _f(r["GroupIndex_FULL_EW"]),
                      "tvalue": _f(r["GroupTurnoverValue"]),
                      "share": _f(r["GroupTurnoverShare"]),
                      "breadth": _f(r["PositiveBreadth"]),
                      "foreign": _f(r["ForeignNetAmount"]),
                      "trust": _f(r["InvestmentTrustNetAmount"])}
                     for _, r in g.iterrows()]}
    # 延續榜:最新日佔比×5 日均佔比×佔比變化(快照冊欄位直出;零發明)
    d5 = sorted(df["Date"].unique())[-5:]
    m5 = (df[df["Date"].isin(d5)].groupby("GroupId")["GroupTurnoverShare"]
          .mean().to_dict())
    rank = [{"gid": r["GroupId"], "share": _f(r["GroupTurnoverShare"]),
             "share5": _f(m5.get(r["GroupId"])),
             "chg": _f(r.get("TurnoverShareChange")),
             "state": str(r.get("RotationState", "")),
             "conf": _f(r.get("RotationConfidence"))}
            for _, r in latest.sort_values("GroupTurnoverShare", ascending=False)
            .head(10).iterrows()]
    return {"groups": groups, "rank": rank,
            "note": f"{src.name} · 最新日 {last} · 39 群取成交值前 {top_n}"}


def harvest_global(days: int = 400) -> dict:
    """ROTATION_GLOBAL 最新快照(glob 尾版;唯讀):9 類別+宏觀因子。
    誠實:TURNOVER_PROXY+REVIEW 註記隨資料出。"""
    root = VIA / "functional modules" / "GroupIndex" / "output_hub" / "rotation_runs"
    runs = sorted(root.glob("ROTATION_GLOBAL_*")) if root.exists() else []
    if not runs:
        return {"groups": {}, "rank": [], "factors": {}, "note": "無全球快照(誠實)"}
    src = runs[-1]
    import pandas as pd
    df = pd.read_csv(src / "csv" / "group_rotation_daily.csv")
    df["Date"] = df["Date"].str.replace("/", "-")
    last = df["Date"].max()
    dates = sorted(df["Date"].unique())[-days:]
    sub = df[df["Date"].isin(dates)]

    def _f(v):
        return None if pd.isna(v) else round(float(v), 6)

    groups = {}
    for gid, g in sub.groupby("GroupId"):
        g = g.sort_values("Date")
        tail = g.iloc[-1]
        groups[gid] = {
            "state": str(tail.get("RotationState", "")),
            "conf": _f(tail.get("RotationConfidence")),
            "rows": [{"date": r["Date"], "gindex": _f(r["GroupIndex_FULL_EW"]),
                      "tvalue": _f(r["GroupTurnoverValue"]),
                      "share": _f(r["GroupTurnoverShare"]),
                      "breadth": _f(r["PositiveBreadth"])}
                     for _, r in g.iterrows()]}
    fx = pd.read_csv(src / "csv" / "market_factors.csv")
    fx["Date"] = fx["Date"].str.replace("/", "-")
    fx = fx[fx["Date"].isin(sorted(fx["Date"].unique())[-days:])].sort_values("Date")
    factors = {k: [{"date": r["Date"], "value": _f(r[k])} for _, r in fx.iterrows()]
               for k in ("EURUSD_RET", "USDJPY_RET", "VIX_RET", "US10Y_D1")}
    latest = df[df["Date"] == last]
    d5 = sorted(df["Date"].unique())[-5:]
    m5 = (df[df["Date"].isin(d5)].groupby("GroupId")["GroupTurnoverShare"]
          .mean().to_dict())
    rank = [{"gid": r["GroupId"], "share": _f(r["GroupTurnoverShare"]),
             "share5": _f(m5.get(r["GroupId"])),
             "chg": _f(r.get("TurnoverShareChange")),
             "state": str(r.get("RotationState", "")),
             "conf": _f(r.get("RotationConfidence"))}
            for _, r in latest.sort_values("GroupTurnoverShare", ascending=False)
            .iterrows()]
    return {"groups": groups, "rank": rank, "factors": factors,
            "note": (f"{src.name} · 最新日 {last} · 成交值=PROXY(價×量估算)"
                     f" · profile=REVIEW 非 PASS(V13 裁定)")}

# ===== [批400] 缺料前檢(唯讀零網路;正常渲染路徑零觸碰)=====
# 工作站實錄(批397 via-famui):「YELLOW vap VAP 儀表板 DATA … rc1;舊頁在位」=
# vdf_tw_market.duckdb 缺 tw_listings 等表 → 裸 CatalogException traceback rc1(不誠實)。
# 本段:先檢版面冊/件/庫檔/七表/輪動快照 → [缺料]/[缺件] 逐項指路可填之令,誠實停 rc2;
# 庫忙=讓庫律(批399 ENG056 同律)[FAIL] rc3 指路 via-bg;零裸 traceback;舊頁在位不以空殼覆蓋。
VDF_ENG = VIA / "functional modules" / "VDF" / "engine"
GRP_ENG = VIA / "functional modules" / "GroupIndex" / "engine"
ROT_ROOT = VIA / "functional modules" / "GroupIndex" / "output_hub" / "rotation_runs"
# (表, 產者引擎 glob(尾版), 指路全文({eng}=尾版引擎相對路徑), 補料短語)
# 指路只指冊內已登錄短令(Register v0163):via-price/via-chip 在冊;ENG055 之 via-omni、
# ENG057 之 via-tval 皆未登錄=死路 → 改指通用家族啟動器 via-py vdf <引擎> <動詞>。
REQ_TABLES = (
    ("tw_listings", "VDF_ENG054_TWDailyBackfill_v*.py",
     "via-price(=VDF_ENG054 run;建庫+上市櫃清單+日價)", "via-price"),
    ("prices_canonical", "VDF_ENG060_AdjPriceLayer_v*.py",
     "via-py vdf \"{eng}\" build(調整後價 VIEW;先 via-price)", "ENG060 build"),
    ("tw_chip_inst", "VDF_ENG056_ChipBackfill_v*.py",
     "via-chip(=VDF_ENG056 run;三法人買賣超)", "via-chip"),
    ("tw_chip_margin", "VDF_ENG056_ChipBackfill_v*.py",
     "via-chip(=VDF_ENG056 run;融資融券餘額)", "via-chip"),
    ("tw_trading_daily", "VDF_ENG057_TradingValueBackfill_v*.py",
     "via-py vdf \"{eng}\" run(成交值;其 docstring 之 via-tval 未登錄=死路)", "ENG057 run"),
    ("tw_valuation_daily", "VDF_ENG055_OmniFetch_v*.py",
     "via-py vdf \"{eng}\" run(估值車道;via-omni 未登錄=死路)", "ENG055 run"),
    ("features_daily", "VDF_ENG061_FeatureStore_v*.py",
     "via-py vdf \"{eng}\" build(因子庫;先 prices_canonical)", "ENG061 build"),
)
DB_FILL = ("via-price(VDF_ENG054 run 建 vdf_tw_market.duckdb)· via-vdfdb run --apply(ENG079 本機三庫整併;"
           "抓過不再抓)· via-py vdf \"{eng}\" import <parquet 夾>(ENG065)")
DEP_FILL = "via-rungate --family vap --approve-install(家族境補庫;base 退路不裝功能件)"
SSOT_FILL = "via-reload(拉齊母倉;冊為 git 正本)"
LOCK_KEYS = ("lock", "already open", "being used", "另一個程序", "cannot open file")
ENGINE_TAG = "VAP_ENG009 v0107"


def _newest_name(root: Path, pat: str) -> str:
    """尾版律:glob 尾版檔名;缺=回 glob 原樣(誠實,不發明檔名)"""
    hits = sorted(root.glob(pat)) if root.exists() else []
    return hits[-1].name if hits else pat


def _rel(p: Path) -> str:
    try:
        return p.relative_to(VIA).as_posix()
    except ValueError:
        return str(p)


def _eng_path(root: Path, pat: str) -> str:
    return _rel(root / _newest_name(root, pat))


def _cut(s: str, n: int = 160) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _rot_fill(prof: str) -> str:
    return (f"via-py vdf \"{_eng_path(GRP_ENG, 'GRP_ENG040_GroupingRotationRunner_v*.py')}\" run {prof.lower()}"
            "(Register 之 via-rotation 現指 ENG072 故事橋,非此快照)")


def preflight(db: Path | None = None, ssot: Path | None = None, rot_root: Path | None = None,
              import_fn=None, connect_fn=None, sleep_fn=None, retries: int = 6, wait: float = 3.0) -> dict:
    """批400 缺料前檢(唯讀;零網路;零副作用)。
    回 {"missing": [項], "soft": [項], "busy": 訊息|None, "tables": {有表}};
    項={"kind": 冊|件|庫|表|快照, "key": 名, "what": 全文, "fill": 指路, "short": 補料短語}。
    missing 非空=誠實停 rc2;busy=庫忙 rc3;soft=頁內誠實空(渲染照走,只加印一行指路)。"""
    db = DB if db is None else db
    ssot = SSOT if ssot is None else ssot
    rot_root = ROT_ROOT if rot_root is None else rot_root
    import_fn = import_fn or importlib.import_module
    missing, soft, busy, tables = [], [], None, set()

    def item(kind, key, what, fill, short):
        return {"kind": kind, "key": key, "what": what, "fill": fill, "short": short}

    # ① 版面冊(單源;git 正本)
    if not ssot.exists():
        missing.append(item("冊", ssot.name, f"版面冊缺 {ssot.name}(registry)", SSOT_FILL, "via-reload"))
    else:
        try:
            if "dashboard" not in json.loads(ssot.read_text(encoding="utf-8")):
                missing.append(item("冊", ssot.name, f"版面冊 {ssot.name} 無「dashboard」節", SSOT_FILL, "via-reload"))
        except Exception as exc:
            missing.append(item("冊", ssot.name, f"版面冊 {ssot.name} 不可讀:{type(exc).__name__}", SSOT_FILL, "via-reload"))
    # ② python 件(家族境;訊息含 No module named=MDL138 退家族境判準同字)
    mods = {}
    for name in ("duckdb", "pandas"):
        try:
            mods[name] = import_fn(name)
        except Exception as exc:
            mods[name] = None
            missing.append(item("件", name, f"python 件 {name} 缺({type(exc).__name__}: No module named '{name}')",
                                DEP_FILL, "via-rungate --family vap --approve-install"))
    # ③ 正典庫檔 + 七表(唯讀開庫;讓庫律短等重試)
    db_fill = DB_FILL.format(eng=_eng_path(VDF_ENG, "VDF_ENG065_DbImport_v*.py"))
    if not db.exists():
        missing.append(item("庫", db.name, f"正典庫缺 {_rel(db)}", db_fill, "via-price(建庫)或 via-vdfdb run --apply"))
    elif mods.get("duckdb") is not None:
        connect = connect_fn or mods["duckdb"].connect
        con, last = None, ""
        for i in range(retries):
            try:
                con = connect(str(db), read_only=True)
                break
            except Exception as exc:
                last = str(exc) or type(exc).__name__
                head = last.splitlines()[0]
                if type(exc).__name__ != "IOException" or not any(k in last.lower() for k in LOCK_KEYS):
                    missing.append(item("庫", db.name, f"正典庫 {db.name} 不可開:{type(exc).__name__}: {head[:120]}",
                                        db_fill, "via-price(建庫)或 via-vdfdb run --apply"))
                    break
                print(f"  [庫忙] {i + 1}/{retries}:{head[:90]} → 等 {wait}s", flush=True)
                (sleep_fn or time.sleep)(wait)
        else:
            busy = (f"庫忙逾 {retries}×{wait}s(日更鏈/回補/via-price 持單寫者鎖;等其跑完再 via-famui vap;"
                    f"via-bg 看背景引擎進程):{last.splitlines()[0][:120]}")
        if con is not None:
            try:
                tables = {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}
            finally:
                con.close()
            for t, pat, fill, short in REQ_TABLES:
                if t not in tables:
                    missing.append(item("表", t, f"{db.name} 缺表 {t}", fill.format(eng=_eng_path(VDF_ENG, pat)), short))
    # ④ 輪動快照(族群/全球層):無=頁內誠實空(非致命);GLOBAL 半殘=致命(harvest_global 直讀 csv 會裸炸)
    for prof, need, layer in (("TW", ("group_rotation_daily.csv",), "族群層"),
                              ("GLOBAL", ("group_rotation_daily.csv", "market_factors.csv"), "全球層")):
        runs = sorted(rot_root.glob(f"ROTATION_{prof}_*")) if rot_root.exists() else []
        short = f"GRP_ENG040 run {prof.lower()}(via-py vdf)"
        if not runs:
            soft.append(item("快照", prof, f"輪動快照 ROTATION_{prof}_* 無({layer}=頁內誠實空)", _rot_fill(prof), short))
            continue
        lack = [n for n in need if not (runs[-1] / "csv" / n).exists()]
        if lack:
            (missing if prof == "GLOBAL" else soft).append(
                item("快照", prof, f"輪動快照 {runs[-1].name} 半殘缺 csv/{'、'.join(lack)}({layer})", _rot_fill(prof), short))
    return {"missing": missing, "soft": soft, "busy": busy, "tables": tables}


def _fill_line(entries: list, page: Path, rc: int) -> str:
    """[補料] 末行:依冊序去重之補料短語 → via-famui vap;含 rc 與舊頁在位(MDL138 尾行 160 字內優先要旨)"""
    order = ["via-reload", "via-rungate --family vap --approve-install", "via-price(建庫)或 via-vdfdb run --apply"]
    order += [s for *_, s in REQ_TABLES] + ["GRP_ENG040 run tw(via-py vdf)", "GRP_ENG040 run global(via-py vdf)"]
    order = list(dict.fromkeys(order))   # 冊序去重(via-chip 供兩表只列一次)
    have = {e["short"] for e in entries}
    steps = [s for s in order if s in have] + sorted(s for s in have if s not in order)
    keep = f"舊頁在位 {page.name}" if page.exists() else f"頁缺 {page.name}(MDL138 記 FAIL;補料後即 DATA)"
    return _cut(f"[補料] 誠實停 rc{rc} · {keep} · 次序:{' → '.join(steps)} → via-famui vap")


def report_preflight(pf: dict, page: Path | None = None) -> int:
    """印缺料/缺件/庫忙(誠實三態;stdout);回 0=可渲染 / 2=缺料誠實停 / 3=庫忙誠實停。
    正常路徑零加印(stdout 與 v0106 同);末二行=摘要+補料(MDL138 只存尾二行各 160 字)。"""
    page = UI_OUT if page is None else page
    if pf["busy"]:
        print(f"=== VIA 儀表板({ENGINE_TAG})· 缺料前檢(批400;唯讀零網路)===")
        print(_cut(f"[FAIL] 庫忙 {pf['busy']}", 300))
        print(_cut(f"[FAIL] 誠實停 rc3(讓庫律;零裸 traceback)· {'舊頁在位' if page.exists() else '頁缺'} {page.name}"
                   " · via-bg 看持鎖者,等其跑完再 via-famui vap"))
        return 3
    if pf["missing"]:
        print(f"=== VIA 儀表板({ENGINE_TAG})· 缺料前檢(批400;唯讀零網路)===")
        for e in pf["missing"]:
            print(f"  {'[缺件]' if e['kind'] == '件' else '[缺料]'} {e['what']} → {e['fill']}")
        for e in pf["soft"]:
            print(f"  [缺料·非致命] {e['what']} → {e['fill']}")
        groups, order = {}, []
        for e in pf["missing"]:
            groups.setdefault(e["kind"], []).append(e["key"])
            if e["kind"] not in order:
                order.append(e["kind"])
        tag = "[缺件]" if all(e["kind"] == "件" for e in pf["missing"]) else "[缺料]"
        names = ";".join(f"{k} {'·'.join(groups[k])}" for k in order)
        print(_cut(f"{tag} 缺 {len(pf['missing'])} 項:{names}({DB.name})"))
        print(_fill_line(pf["missing"], page, 2))
        return 2
    for e in pf["soft"]:
        print(f"[缺料·非致命] {e['what']} → {e['fill']}")
    return 0


def _honest_stop(exc: BaseException, page: Path | None = None) -> int:
    """渲染中例外 → 誠實一行定位(零裸 traceback):缺表 rc2 / 庫忙 rc3 / 缺件 rc2 / 非預期 rc1"""
    page = UI_OUT if page is None else page
    name = type(exc).__name__
    msg = (str(exc).splitlines() or [""])[0]
    frames = traceback.extract_tb(exc.__traceback__)[-2:]
    where = " ← ".join(f"{f.name}@{Path(f.filename).name}:{f.lineno}" for f in reversed(frames)) or "?"
    keep = f"舊頁在位 {page.name}" if page.exists() else f"頁缺 {page.name}(MDL138 記 FAIL;補料後即 DATA)"
    if name == "ModuleNotFoundError":
        print(f"[缺件] {msg} @ {where} → {DEP_FILL}")
        print(_cut(f"[補料] via-rungate --family vap --approve-install → via-famui vap · 誠實停 rc2 · {keep}"))
        return 2
    if name == "CatalogException":
        m = re.search(r"Table with name (\w+)", msg)
        t = m.group(1) if m else "?"
        hit = next(((f.format(eng=_eng_path(VDF_ENG, p)), s) for tt, p, f, s in REQ_TABLES if tt == t),
                   ("via-price/via-chip(VDF 日更鏈;表不在本引擎七表冊,候查產者)", "via-price/via-chip"))
        print(f"[缺料] 庫 {DB.name} 缺表 {t}({msg[:100]})@ {where} → {hit[0]}")
        print(_cut(f"[補料] {hit[1]} → via-famui vap · 誠實停 rc2 · {keep}"))
        return 2
    if name == "IOException" and any(k in msg.lower() for k in LOCK_KEYS):
        print(f"[FAIL] 庫忙 {msg[:120]} @ {where}(日更鏈/回補/via-price 持單寫者鎖)")
        print(_cut(f"[FAIL] 誠實停 rc3(讓庫律)· {keep} · via-bg 看持鎖者,等其跑完再 via-famui vap"))
        return 3
    print(f"[FAIL] 非預期 {name}: {msg[:140]} @ {where}")
    print(_cut(f"[FAIL] 誠實停 rc1(零裸 traceback;定位如上)· {keep} · 候修後 via-famui vap"))
    return 1
# ===== [批400] 缺料前檢 END =====


def build_css(t: dict) -> str:
    """操作員 Layout element CSS 原樣結構;值全由 dashboard token 節供給"""
    return f"""
:root {{
    --font-family: {t['font_family']};
    --font-size-base: {t['font_pc_px']}px;
    --color-bg: {t['color_bg']};
    --color-panel-bg: {t['color_panel_bg']};
    --color-border: {t['color_border']};
    --color-grid: {t['color_grid']};
}}
body {{ margin: 0; font-family: var(--font-family);
    font-size: var(--font-size-base); background: var(--color-bg); }}
.dashboard {{ display: grid; grid-template-columns: {t['panel_w_px']}px 1fr;
    grid-template-rows: 100vh; overflow: hidden; }}
.left-panel {{ background: var(--color-panel-bg);
    border-right: 1px solid var(--color-border); padding: 8px;
    display: flex; flex-direction: column; overflow-y: auto; box-sizing: border-box; }}
.right-panel {{ background: var(--color-bg); padding: 10px;
    overflow-y: auto; box-sizing: border-box; }}
.left-header, .right-header {{ height: {t['header_h_px']}px; font-weight: 600;
    display: flex; align-items: center; box-sizing: border-box; }}
.filter-panel {{ display: flex; flex-direction: column; gap: 6px; }}
.ui-select, .ui-date {{ width: 100%; padding: 4px; font-size: var(--font-size-base);
    border: 1px solid {t['input_border']}; border-radius: 3px; box-sizing: border-box; }}
.check-group {{ display: flex; gap: 10px; font-size: var(--font-size-base); }}
.chart-grid {{ display: grid; grid-template-columns: 1fr; gap: 10px; }}
.chart-card {{ background: var(--color-bg); border: 1px solid var(--color-border);
    border-radius: 4px; min-height: {t['chart_min_h_px']}px; width: 100%;
    padding: 6px; box-sizing: border-box; }}
.left-panel.collapsed {{ width: 0 !important; min-width: 0 !important;
    padding: 0 !important; overflow: hidden !important; }}
.alerts {{ margin-top: 8px; font-size: {t['font_mobile_px']}px; }}
.alert-item {{ border: 1px solid var(--color-border); border-radius: 3px;
    padding: 4px 6px; margin-bottom: 4px; background: {t['alert_bg']}; }}
#logs {{ width: 100%; border-collapse: collapse; font-size: {t['font_mobile_px']}px; }}
#logs th, #logs td {{ border: 1px solid var(--color-border); padding: 4px 6px; }}
@media (max-width: {t['breakpoint_px']}px) {{
    .dashboard {{ grid-template-columns: 1fr; grid-template-rows: auto 1fr; }}
    .left-panel {{ width: 100% !important; min-width: 100% !important;
        border-right: none; border-bottom: 1px solid var(--color-border); }}
    .chart-card {{ min-height: {t['chart_min_h_px']}px; }}
    html {{ font-size: {t['font_mobile_px']}px; }}
}}"""


_JS = r"""
/* VIA Dashboard — 操作員 Layout element JS(批167 收容;QA 修正五處留痕) */
const VIA = {
    screen: { width: window.innerWidth, height: window.innerHeight,
              isMobile: window.innerWidth < %%BP%% },
    chart: { baseHeightPC: %%HPC%%, baseHeightMobile: %%HMB%%,
             tickIntervals: %%TICKS%% },
    state: { stock: null, module: null, chartType: null,
             dateStart: null, dateEnd: null, checks: {}, alerts: [], logs: [] }
};

function bindUI() {
    document.querySelectorAll(".ui-select").forEach(el => { el.onchange = () => updateDashboard(); });
    document.querySelectorAll(".ui-date").forEach(el => { el.onchange = () => updateDashboard(); });
    document.querySelectorAll(".ui-check").forEach(el => { el.onchange = () => updateDashboard(); });
    document.getElementById("collapse-btn").onclick = () => toggleLeftPanel();
    document.getElementById("dropdown-layer").onchange = () => {
        applyLayer(); updateDashboard(); };
}

function toggleLeftPanel() {
    const panel = document.querySelector(".left-panel");
    panel.classList.toggle("collapsed");
    setTimeout(autoOptimize, 150);
}

function collectParams() {
    VIA.state.stock = document.getElementById("dropdown-stock")?.value;
    VIA.state.module = document.getElementById("dropdown-module")?.value;
    VIA.state.chartType = document.getElementById("dropdown-chart-type")?.value;
    VIA.state.dateStart = document.getElementById("date-start")?.value;
    VIA.state.dateEnd = document.getElementById("date-end")?.value;
    VIA.state.checks = {};
    document.querySelectorAll(".ui-check").forEach(el => { VIA.state.checks[el.value] = el.checked; });
    return { ...VIA.state };
}

/* 5. Auto-Fixer(QA①:欄位檢由 !df.date[陣列恆真誤報]改檢首列鍵) */
function autoFixData(df) {
    let alerts = [];
    let logs = [];
    if (!df.length || !("date" in (df[0] || {}))) {
        alerts.push("缺少日期欄位");
        logs.push({ issue: "Missing Column", notes: "date" });
        return { df: [], alerts, logs };
    }
    df.forEach(row => {
        if (!row.date || isNaN(new Date(row.date))) {
            alerts.push("日期格式錯誤");
            logs.push({ issue: "Invalid Date", notes: String(row.date) });
        }
    });
    df.sort((a, b) => new Date(a.date) - new Date(b.date));
    let fixed = fillMissingDates(df);
    if (fixed.added > 0) {
        alerts.push("時間軸不連續,已補齊日期(含非交易日;誠實列示)");
        logs.push({ issue: "Date Gap", notes: `${fixed.added} days added` });
    }
    df = fixed.df;   /* QA②:原稿未接回 fixed.df=補齊結果被丟棄 → 接線 */
    df = interpolateValues(df);
    df = smoothOutliers(df);
    return { df, alerts, logs };
}

function fillMissingDates(df) {
    let added = 0;
    let map = {};
    df.forEach(row => map[row.date] = row);
    let start = new Date(df[0].date);
    let end = new Date(df[df.length - 1].date);
    let full = [];
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        let key = d.toISOString().slice(0, 10);
        if (map[key]) full.push(map[key]);
        else { full.push({ date: key, value: null }); added++; }
    }
    return { df: full, added };
}

/* 7. 補值(QA③:原稿註記「線性插值」實為前值遞補=ffill;正名不改行為) */
function interpolateValues(df) {
    let last = null;
    for (let i = 0; i < df.length; i++) {
        if (df[i].value == null) { df[i].value = last; }
        else { last = df[i].value; }
    }
    return df;
}

/* 8. 極端值平滑(QA④:分位計算先濾 null,避免 NaN 汙染 IQR) */
function smoothOutliers(df) {
    let values = df.map(r => r.value).filter(v => v != null && !isNaN(v));
    if (!values.length) return df;
    let sorted = [...values].sort((a, b) => a - b);
    let q1 = sorted[Math.floor(sorted.length * 0.25)];
    let q3 = sorted[Math.floor(sorted.length * 0.75)];
    let iqr = q3 - q1;
    let lower = q1 - 3 * iqr;
    let upper = q3 + 3 * iqr;
    df.forEach(r => {
        if (r.value != null) {
            if (r.value < lower) r.value = lower;
            if (r.value > upper) r.value = upper;
        }
    });
    return df;
}

/* 9. Plotly 自動最佳化(QA⑤:typeof 閘=零 CDN;Plotly 在場才升級) */
function optimizePlotly(gd) {
    if (typeof Plotly === "undefined" || !gd || !gd.data) return;
    let maxVal = Math.max(...gd.data.flatMap(t => t.y || []));
    let interval = VIA.chart.tickIntervals.find(i => maxVal / i <= 12) || 5;
    Plotly.relayout(gd, { "yaxis.dtick": interval, "yaxis.tickformat": ".2f",
                          "xaxis.ticklabelmode": "period" });
    Plotly.update(gd, { textposition: "auto", insidetextanchor: "middle",
                        constraintext: "none" });
}

function autoOptimize() {
    VIA.screen.width = window.innerWidth;
    VIA.screen.height = window.innerHeight;
    VIA.screen.isMobile = VIA.screen.width < %%BP%%;
    const height = VIA.screen.isMobile ? VIA.chart.baseHeightMobile : VIA.chart.baseHeightPC;
    document.querySelectorAll(".chart-card").forEach(card => {
        card.style.minHeight = height + "px";
    });
    document.documentElement.style.fontSize =
        VIA.screen.isMobile ? "%%FMB%%px" : "%%FPC%%px";
    const dashboard = document.querySelector(".dashboard");
    if (VIA.screen.isMobile) {
        dashboard.style.gridTemplateColumns = "1fr";
        dashboard.style.gridTemplateRows = "auto 1fr";
    } else {
        dashboard.style.gridTemplateColumns = "%%PW%%px 1fr";
        dashboard.style.gridTemplateRows = "100vh";
    }
}

/* 嵌入實料(vdf_tw_market.duckdb;零網路)——fetchData 讀本地 JSON */
const VIA_DATA = %%DATA%%;
const VIA_GRP = %%GRPDATA%%;
const VIA_GLB = %%GLBDATA%%;
const GLB_FIELD = { "類別指數(FULL_EW)": "gindex", "成交值(PROXY)": "tvalue",
    "金流佔比(PROXY)": "share", "正廣度": "breadth" };
const GLB_FACTORS = ["EURUSD_RET", "USDJPY_RET", "VIX_RET", "US10Y_D1"];
const MODULE_FIELD = { "價格(收盤)": "close", "成交量(扣當沖;律)": "volume", "成交量(原始對照)": "volume_raw",
    "成交值": "tvalue", "外資買賣超": "foreign", "投信買賣超": "trust",
    "自營買賣超": "dealer", "融資餘額": "margin", "融券餘額": "short" };
const GRP_FIELD = { "族群指數(FULL_EW)": "gindex", "族群成交值": "tvalue",
    "金流佔比": "share", "正廣度": "breadth", "外資金額": "foreign",
    "投信金額": "trust" };

function currentLayer() {
    return document.getElementById("dropdown-layer")?.value || "個股";
}

/* 層級切換:同一 Gate Panel 骨架,選單內容換裝(操作員版面零改) */
function applyLayer() {
    const layer = currentLayer();
    const sel = document.getElementById("dropdown-stock");
    const mod = document.getElementById("dropdown-module");
    document.getElementById("lbl-target").innerText =
        layer === "全球" ? "類別" : (layer === "族群" ? "族群" : "個股");
    sel.innerHTML = "";
    mod.innerHTML = "";
    if (layer === "全球") {
        Object.keys(VIA_GLB.groups).forEach(g => {
            const o = document.createElement("option"); o.value = g; o.text = g;
            sel.appendChild(o); });
        Object.keys(GLB_FIELD).concat(GLB_FACTORS).forEach(m => {
            const o = document.createElement("option"); o.text = m; mod.appendChild(o); });
    } else if (layer === "族群") {
        Object.keys(VIA_GRP.groups).forEach(g => {
            const o = document.createElement("option"); o.value = g; o.text = g;
            sel.appendChild(o); });
        Object.keys(GRP_FIELD).forEach(m => {
            const o = document.createElement("option"); o.text = m; mod.appendChild(o); });
    } else {
        Object.entries(VIA_DATA.stocks).forEach(([c, v]) => {
            const o = document.createElement("option"); o.value = c;
            o.text = `${c} ${v.name}`; sel.appendChild(o); });
        Object.keys(MODULE_FIELD).forEach(m => {
            const o = document.createElement("option"); o.text = m; mod.appendChild(o); });
    }
    document.getElementById("rank-wrap").style.display =
        (layer === "族群" || layer === "全球") ? "block" : "none";
}

async function fetchData(params) {
    if (currentLayer() === "全球") {
        if (GLB_FACTORS.includes(params.module)) {
            return (VIA_GLB.factors[params.module] || [])
                .filter(r => (!params.dateStart || r.date >= params.dateStart)
                          && (!params.dateEnd || r.date <= params.dateEnd));
        }
        const g = VIA_GLB.groups[params.stock];
        if (!g) return [];
        const f = GLB_FIELD[params.module] || "gindex";
        return g.rows
            .filter(r => (!params.dateStart || r.date >= params.dateStart)
                      && (!params.dateEnd || r.date <= params.dateEnd))
            .map(r => ({ date: r.date, value: r[f] }));
    }
    if (currentLayer() === "族群") {
        const g = VIA_GRP.groups[params.stock];
        if (!g) return [];
        const f = GRP_FIELD[params.module] || "gindex";
        return g.rows
            .filter(r => (!params.dateStart || r.date >= params.dateStart)
                      && (!params.dateEnd || r.date <= params.dateEnd))
            .map(r => ({ date: r.date, value: r[f] }));
    }
    const s = VIA_DATA.stocks[params.stock];
    if (!s) return [];
    const f = MODULE_FIELD[params.module] || "close";
    return s.rows
        .filter(r => (!params.dateStart || r.date >= params.dateStart)
                  && (!params.dateEnd || r.date <= params.dateEnd))
        .map(r => ({ date: r.date, value: r[f] }));
}

/* 內建 SVG 圖車道(零 CDN;Plotly 在場時 optimizePlotly 自動升級)
   v0101:抽出 drawChart 通用器=主副雙圖共用(操作員 chart-grid 原生多卡) */
function drawChart(cardId, title, pts, kind) {
    const card = document.getElementById(cardId);
    const w = card.clientWidth - 12, h = card.clientHeight - 30 || 300;
    if (!pts.length) { card.innerHTML = `<div>${title}</div><div>無資料(誠實)</div>`; return; }
    const xs = pts.map((_, i) => i), ys = pts.map(r => r.value);
    const ymin = Math.min(...ys), ymax = Math.max(...ys), yr = (ymax - ymin) || 1;
    const X = i => 40 + (w - 50) * i / Math.max(1, xs.length - 1);
    const Y = v => (h - 20) - (h - 40) * (v - ymin) / yr;
    let grid = "";
    for (let g = 0; g <= 4; g++) {
        const gy = 20 + (h - 40) * g / 4;
        const gv = (ymax - yr * g / 4);
        grid += `<line x1="40" y1="${gy}" x2="${w - 10}" y2="${gy}" stroke="%%CGRID%%"/>` +
                `<text x="2" y="${gy + 3}" font-size="9">${gv >= 1e8 ? (gv/1e8).toFixed(1)+"億" : gv.toFixed(1)}</text>`;
    }
    let body = "";
    if (kind === "長條圖") {
        const bw = Math.max(1, (w - 50) / pts.length - 1);
        body = pts.map((r, i) =>
            `<rect x="${X(i) - bw / 2}" y="${Math.min(Y(r.value), Y(Math.max(ymin, 0)))}" width="${bw}" height="${Math.abs(Y(r.value) - Y(Math.max(ymin, 0))) || 1}" fill="#4a78b0"/>`).join("");
    } else {
        body = `<polyline fill="none" stroke="#1f4e79" stroke-width="1.4" points="` +
            pts.map((r, i) => `${X(i)},${Y(r.value)}`).join(" ") + `"/>`;
    }
    const lab = [0, Math.floor(pts.length / 2), pts.length - 1].map(i =>
        `<text x="${X(i)}" y="${h - 4}" font-size="9" text-anchor="middle">${pts[i].date}</text>`).join("");
    card.innerHTML = `<div style="font-weight:600">${title}</div>` +
        `<svg width="${w}" height="${h}" role="img">${grid}${body}${lab}</svg>`;
    optimizePlotly(card);
}

function renderRank() {
    const tb = document.querySelector("#rank tbody");
    tb.innerHTML = "";
    const src = currentLayer() === "全球" ? VIA_GLB : VIA_GRP;
    (src.rank || []).forEach(r => {
        const tr = document.createElement("tr");
        const pc = v => v == null ? "—" : (v * 100).toFixed(2) + "%";
        tr.innerHTML = `<td>${r.gid}</td><td style="text-align:center">${pc(r.share)}</td>` +
            `<td style="text-align:center">${pc(r.share5)}</td>` +
            `<td style="text-align:center">${pc(r.chg)}</td>` +
            `<td style="text-align:center">${r.state || "—"}</td>` +
            `<td style="text-align:center">${r.conf == null ? "—" : r.conf}</td>`;
        tb.appendChild(tr);
    });
}

function renderCharts(df) {
    if (currentLayer() === "全球") {
        const g = VIA_GLB.groups[VIA.state.stock] || {};
        const isFx = GLB_FACTORS.includes(VIA.state.module);
        const title = isFx
            ? `${VIA.state.module}(宏觀因子=全球共通,不隨類別)`
            : `${VIA.state.stock} · ${VIA.state.module}`;
        drawChart("chart-main", title, df.filter(r => r.value != null), VIA.state.chartType);
        const sub = (g.rows || [])
            .filter(r => (!VIA.state.dateStart || r.date >= VIA.state.dateStart)
                      && (!VIA.state.dateEnd || r.date <= VIA.state.dateEnd)
                      && r.share != null)
            .map(r => ({ date: r.date, value: r.share }));
        drawChart("chart-sub", `${VIA.state.stock} · 金流佔比 PROXY(副圖)`, sub, "長條圖");
        document.getElementById("val-row").innerText =
            `輪動態:${g.state || "—"} · 信心 ${g.conf == null ? "—" : g.conf} · ${VIA_GLB.note}`;
        renderRank();
        return;
    }
    if (currentLayer() === "族群") {
        const g = VIA_GRP.groups[VIA.state.stock] || {};
        const title = `${VIA.state.stock} · ${VIA.state.module}`;
        drawChart("chart-main", title, df.filter(r => r.value != null), VIA.state.chartType);
        const sub = (g.rows || [])
            .filter(r => (!VIA.state.dateStart || r.date >= VIA.state.dateStart)
                      && (!VIA.state.dateEnd || r.date <= VIA.state.dateEnd)
                      && r.share != null)
            .map(r => ({ date: r.date, value: r.share }));
        drawChart("chart-sub", `${VIA.state.stock} · 金流佔比(副圖)`, sub, "長條圖");
        document.getElementById("val-row").innerText =
            `輪動態:${g.state || "—"} · 信心 ${g.conf == null ? "—" : g.conf} · ` +
            `${VIA_GRP.note}(GRP_ENG040 快照冊直出;零發明)`;
        renderRank();
        return;
    }
    const stock = VIA_DATA.stocks[VIA.state.stock];
    const name = stock?.name || "";
    const title = `${VIA.state.stock} ${name} · ${VIA.state.module}`;
    drawChart("chart-main", title, df.filter(r => r.value != null), VIA.state.chartType);
    /* 副圖=成交量(操作員 chart-grid 第二卡;固定長條) */
    const sub = (stock?.rows || [])
        .filter(r => (!VIA.state.dateStart || r.date >= VIA.state.dateStart)
                  && (!VIA.state.dateEnd || r.date <= VIA.state.dateEnd)
                  && r.volume != null)
        .map(r => ({ date: r.date, value: r.volume }));
    drawChart("chart-sub", `${VIA.state.stock} ${name} · 成交量(副圖)`, sub, "長條圖");
    /* 估值誠實現值列(快照僅數日=不足作圖,不假圖) */
    const v = stock?.valuation;
    document.getElementById("val-row").innerText = v
        ? `估值快照 ${v.date}:PE ${v.pe} · PB ${v.pb} · 殖利率 ${v.yield}%(tw_valuation_daily;快照日不足作圖=誠實列現值)`
        : "估值快照:無(誠實)";
    /* 批191:因子快照列=features_daily 庫取(VDF_ENG061 單一正主;
       頁內零自算);NULL=視窗不足誠實顯示 — */
    const f = stock?.factors;
    const pc = (x, d = 2) => (x == null ? "—" : (x * 100).toFixed(d) + "%");
    const nm = (x, d = 2) => (x == null ? "—" : x.toFixed(d));
    document.getElementById("factor-row").innerText = f
        ? `因子快照 ${f.date}:日 ${pc(f.ret_1d)} · 20日 ${pc(f.ret_20d)} · `
          + `60日 ${pc(f.ret_60d)} · 年化波動 ${pc(f.vol_20d_ann, 1)} · `
          + `MA20乖離 ${pc(f.ma20_ratio)} · MA60乖離 ${pc(f.ma60_ratio)} · `
          + `52週高點 ${pc(f.hi252_dist)} · 量能Z ${nm(f.volu_z20)}`
          + `(features_daily=因子庫單一正主;—=視窗不足誠實)`
        : "因子快照:無(誠實)";
}

async function updateDashboard() {
    const params = collectParams();
    const rawData = await fetchData(params);
    const fixed = autoFixData(rawData);
    VIA.state.alerts = fixed.alerts;
    VIA.state.logs = fixed.logs;
    renderAlerts(VIA.state.alerts);
    renderLogs(VIA.state.logs);
    renderCharts(fixed.df);
    autoOptimize();
}

function renderAlerts(alerts) {
    const box = document.getElementById("alerts");
    box.innerHTML = "";
    alerts.forEach(a => {
        const div = document.createElement("div");
        div.className = "alert-item";
        div.innerText = a;
        box.appendChild(div);
    });
}

function renderLogs(logs) {
    const tbody = document.querySelector("#logs tbody");
    tbody.innerHTML = "";
    logs.forEach(log => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${new Date().toLocaleString()}</td>` +
            `<td>${log.issue}</td><td>${log.notes}</td>`;
        tbody.appendChild(tr);
    });
}

window.onload = () => { bindUI(); applyLayer(); autoOptimize(); updateDashboard(); };
window.onresize = autoOptimize;
"""

_HTML = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 儀表板 v0100</title><style>%%CSS%%</style></head><body>
<div class="dashboard">
  <div class="left-panel">
    <div class="left-header">VIA Gate Panel
      <button id="collapse-btn" style="margin-left:auto">☰</button></div>
    <div class="filter-panel">
      <label>層級</label>
      <select id="dropdown-layer" class="ui-select">
        <option>個股</option><option>族群</option><option>全球</option></select>
      <label id="lbl-target">個股</label>
      <select id="dropdown-stock" class="ui-select">%%OPT_STOCK%%</select>
      <label>模組</label>
      <select id="dropdown-module" class="ui-select">%%OPT_MODULE%%</select>
      <label>圖型</label>
      <select id="dropdown-chart-type" class="ui-select">
        <option>折線圖</option><option>長條圖</option></select>
      <label>起日</label><input type="date" id="date-start" class="ui-date" value="%%D0%%">
      <label>迄日</label><input type="date" id="date-end" class="ui-date" value="%%D1%%">
      <div class="check-group">
        <label><input type="checkbox" class="ui-check" value="autofix" checked>Auto-Fixer</label>
        <label><input type="checkbox" class="ui-check" value="smooth" checked>平滑</label>
      </div>
    </div>
    <div class="alerts" id="alerts"></div>
    <table id="logs"><thead><tr><th>時間</th><th>Issue</th><th>Notes</th></tr></thead>
    <tbody></tbody></table>
  </div>
  <div class="right-panel">
    <div class="right-header">主顯示區 · %%NOTE%% · %%TS%%</div>
    <div id="val-row" style="font-size:10px;color:#555;margin:0 0 6px 0"></div>
    <div id="factor-row" style="font-size:10px;color:#555;margin:0 0 6px 0"></div>
    <div class="chart-grid">
      <div class="chart-card" id="chart-main"></div>
      <div class="chart-card" id="chart-sub"></div>
    </div>
    <div id="rank-wrap" style="display:none;margin-top:8px">
      <div style="font-weight:600;font-size:11px">金流佔比延續榜(最新日;快照冊直出)</div>
      <table id="rank" style="width:100%;border-collapse:collapse;font-size:10px">
        <thead><tr><th style="text-align:left">族群</th><th>佔比</th><th>5日均</th>
        <th>佔比變化</th><th>輪動態</th><th>信心</th></tr></thead><tbody></tbody></table>
    </div>
    <div style="font-size:10px;color:#888;margin-top:6px">版面值單源=VIA_UI_TemplateSSOT
「dashboard」節(操作員 Layout element 定案;改冊即換裝)· 實料=vdf_tw_market.duckdb
零重測零發明 · 零 CDN(內建 SVG 車道;Plotly 在場自動升級)</div>
  </div>
</div>
<script>%%JS%%</script></body></html>"""


def build() -> Path:
    t = load_dash_tokens()
    data = harvest_data()
    rows0 = next(iter(data["stocks"].values()))["rows"] if data["stocks"] else []
    d0 = rows0[0]["date"] if rows0 else ""
    d1 = rows0[-1]["date"] if rows0 else ""
    opt_stock = "".join(f'<option value="{c}">{c} {v["name"]}</option>'
                        for c, v in data["stocks"].items())
    opt_module = "".join(f"<option>{m}</option>" for m in
                         ("價格(收盤)", "成交量", "成交值", "外資買賣超",
                          "投信買賣超", "自營買賣超", "融資餘額", "融券餘額"))
    js = (_JS.replace("%%BP%%", str(t["breakpoint_px"]))
          .replace("%%HPC%%", str(t["chart_max_h_px"]))
          .replace("%%HMB%%", str(t["chart_min_h_px"]))
          .replace("%%TICKS%%", json.dumps(t["tick_intervals"]))
          .replace("%%FPC%%", str(t["font_pc_px"]))
          .replace("%%FMB%%", str(t["font_mobile_px"]))
          .replace("%%PW%%", str(t["panel_w_px"]))
          .replace("%%CGRID%%", t["color_grid"])
          .replace("%%DATA%%", json.dumps(data, ensure_ascii=False))
          .replace("%%GRPDATA%%", json.dumps(harvest_rotation(), ensure_ascii=False))
          .replace("%%GLBDATA%%", json.dumps(harvest_global(), ensure_ascii=False)))
    html = (_HTML.replace("%%CSS%%", build_css(t))
            .replace("%%JS%%", js)
            .replace("%%OPT_STOCK%%", opt_stock)
            .replace("%%OPT_MODULE%%", opt_module)
            .replace("%%D0%%", d0).replace("%%D1%%", d1)
            .replace("%%NOTE%%", data["note"])
            .replace("%%TS%%", datetime.now().strftime("%Y-%m-%d %H:%M")))
    UI_OUT.parent.mkdir(parents=True, exist_ok=True)
    UI_OUT.write_text(html, encoding="utf-8")
    return UI_OUT


def _selftest_batch400(chk) -> None:
    """批400 新增四檢(零實料可跑:臨時 DuckDB 殘庫/注入件/子行程;正本頁與正典庫零觸碰)"""
    import contextlib
    import io
    import subprocess
    import tempfile
    try:
        import duckdb as _dk
    except Exception:
        _dk = None
    want = [x[0] for x in REQ_TABLES]

    def stub_import(n):   # 隔離表檢:件一律視為在位(pandas 缺之沙盒亦可測表偵測)
        return importlib.import_module("duckdb") if n == "duckdb" else object()

    if _dk is None:
        for nm in ("⑬ 缺料前檢", "⑭ run 路缺料誠實停", "⑮ 四路誠實停", "⑯ 子行程實跑"):
            chk(nm, False, "duckdb 缺=本檢不可測(於 via_vap 家族境跑;via-rungate --family vap --approve-install)", skip=True)
        return
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        norot = root / "norot"
        empty = root / "empty.duckdb"
        _dk.connect(str(empty)).close()
        part = root / "part.duckdb"
        c = _dk.connect(str(part))
        c.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR)")
        c.execute("CREATE VIEW prices_canonical AS SELECT '2026-01-01' AS date, '2330.TW' AS ticker, 1.0 AS close, 1 AS volume")
        c.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, foreign_net DOUBLE, trust_net DOUBLE, dealer_net DOUBLE)")
        c.close()
        full = root / "full.duckdb"
        c = _dk.connect(str(full))
        for tname in want:
            c.execute(f"CREATE TABLE {tname}(x INTEGER)")
        c.close()
        pf0 = preflight(db=empty, rot_root=norot, import_fn=stub_import)
        pf1 = preflight(db=part, rot_root=norot, import_fn=stub_import)
        pf2 = preflight(db=root / "nope.duckdb", rot_root=norot, import_fn=stub_import)
        pf3 = preflight(db=full, rot_root=norot, import_fn=stub_import)
        chk("⑬ 缺料前檢(空庫=七表依冊序全缺·半庫=餘四表·庫檔缺=指路建庫·全表=零缺;每項有 via- 指路;快照無=非致命)",
            [e["key"] for e in pf0["missing"]] == want and [e["key"] for e in pf1["missing"]] == want[3:]
            and len(pf2["missing"]) == 1 and pf2["missing"][0]["kind"] == "庫" and "via-price" in pf2["missing"][0]["fill"]
            and all("via-" in e["fill"] for e in pf0["missing"]) and not pf3["missing"]
            and len(pf0["soft"]) == 2 and pf0["busy"] is None and pf3["tables"] == set(want),
            f"(缺 {len(pf0['missing'])}/{len(pf1['missing'])}/{len(pf2['missing'])}/{len(pf3['missing'])})")
        page = root / "ui" / "VIA_UI_Dashboard_v0100.html"
        page.parent.mkdir()
        page.write_text("<html>old</html>", encoding="utf-8")
        g = globals()
        keep = (g["DB"], g["UI_OUT"], g["build"])

        def run_main(db, **pf_kw):
            g["DB"], g["UI_OUT"] = db, page
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["run"], pf_kw={**{"rot_root": norot, "import_fn": stub_import}, **pf_kw})
            return rc, buf.getvalue()

        def _raise(e):
            raise e

        def busy_connect(*a, **k):
            raise _dk.IOException('IO Error: Could not set lock on file "x.duckdb": Conflicting lock is held in python (PID 1)')

        def no_pandas(n):
            if n == "pandas":
                raise ModuleNotFoundError("No module named 'pandas'")
            return importlib.import_module(n)
        try:
            rc14, o14 = run_main(empty)
            l14 = [l for l in o14.splitlines() if l.strip()]
            chk("⑭ run 路缺料誠實停(rc2·[缺料] 七表逐項指路·末二行=[缺料]摘要+[補料]各 ≤160 字·舊頁位元組零改·零 Traceback)",
                rc14 == 2 and all(x in o14 for x in want) and o14.count("[缺料]") >= 8 and "via-price" in o14
                and l14[-2].startswith("[缺料] 缺 7 項") and l14[-1].startswith("[補料]") and "rc2" in l14[-1]
                and all(len(l) <= 160 for l in l14[-2:]) and "舊頁在位" in l14[-1]
                and page.read_text(encoding="utf-8") == "<html>old</html>" and "Traceback" not in o14)
            rc_b, o_b = run_main(part, connect_fn=busy_connect, sleep_fn=lambda s: None, retries=2, wait=0.0)
            rc_d, o_d = run_main(part, import_fn=no_pandas)
            g["build"] = lambda: _raise(RuntimeError("boom"))
            rc_u, o_u = run_main(full)
            g["build"] = lambda: _raise(_dk.CatalogException("Catalog Error: Table with name tw_daytrade_stock does not exist!"))
            rc_c, o_c = run_main(full)
            g["build"] = lambda: _raise(_dk.IOException('IO Error: Could not set lock on file "y.duckdb"'))
            rc_l, o_l = run_main(full)
            chk("⑮ 四路誠實停(庫忙=讓庫律 [FAIL] rc3 指路 via-bg·缺件=[缺件] rc2 指路 --approve-install·非預期=rc1 一行定位·渲染中缺表/鎖=rc2/rc3;皆零 Traceback)",
                rc_b == 3 and "[FAIL] 庫忙" in o_b and "via-bg" in o_b and o_b.count("[庫忙]") == 2
                and rc_d == 2 and "[缺件]" in o_d and "No module named 'pandas'" in o_d and "--approve-install" in o_d
                and rc_u == 1 and "[FAIL] 非預期 RuntimeError: boom" in o_u and "<lambda>@" in o_u
                and rc_c == 2 and "[缺料]" in o_c and "tw_daytrade_stock" in o_c
                and rc_l == 3 and "[FAIL] 庫忙" in o_l
                and all("Traceback" not in o for o in (o_b, o_d, o_u, o_c, o_l))
                and page.read_text(encoding="utf-8") == "<html>old</html>",
                f"(rc {rc_b}/{rc_d}/{rc_u}/{rc_c}/{rc_l})")
        finally:
            g["DB"], g["UI_OUT"], g["build"] = keep
        ui2 = root / "ui2.html"
        code = ("import sys, importlib.util\nfrom pathlib import Path\n"
                f"spec = importlib.util.spec_from_file_location('vap9_sub', {str(Path(__file__).resolve())!r})\n"
                "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
                f"m.DB = Path({str(empty)!r}); m.UI_OUT = Path({str(ui2)!r}); m.ROT_ROOT = Path({str(norot)!r})\n"
                "sys.exit(m.main(['run']))")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120,
                           stdin=subprocess.DEVNULL, cwd=str(HERE), encoding="utf-8", errors="replace")
        allout = (r.stdout or "") + (r.stderr or "")
        tail = [l for l in allout.strip().splitlines() if l.strip()][-2:]
        chk("⑯ 子行程實跑(rc2·stdout/stderr 零 Traceback·MDL138 尾二行=[缺料]+[補料]·頁未生成=舊頁在位律)",
            r.returncode == 2 and "Traceback" not in allout and len(tail) == 2
            and tail[0].startswith("[缺料]") and tail[1].startswith("[補料]") and not ui2.exists(),
            f"(rc {r.returncode};尾:{tail[-1][:60] if tail else ''})")


def selftest() -> int:
    fails, skips = [], []

    def chk(name, cond, note="", skip=False, weight=1):
        # 批400:誠實三態 OK/FAIL/SKIP(SKIP=環境缺料/缺件誠實註明,不記 FAIL;同 SelftestGrid 律;weight=合併列示之檢數)
        st = "SKIP" if skip else ("OK" if cond else "FAIL")
        print(f"  [{st}] {name} {note}")
        if skip:
            skips.extend([name] * weight)
        elif not cond:
            fails.append(name)

    t = load_dash_tokens()
    chk("① token 冊 dashboard 節在位(定案值齊:260/38/320-420/768/11-10/tick 8 檔)",
        t["panel_w_px"] == 260 and t["header_h_px"] == 38
        and t["chart_min_h_px"] == 320 and t["chart_max_h_px"] == 420
        and t["breakpoint_px"] == 768 and len(t["tick_intervals"]) == 8)
    # 批400:實料十一檢(②–⑫)需正典庫七表(+pandas)+輪動快照;缺=誠實 SKIP 指路(零裸 traceback),檢本文零改
    pf = preflight()
    real = not pf["missing"] and not pf["busy"]
    absent = {e["key"] for e in pf["soft"] + pf["missing"] if e["kind"] == "快照"}
    why = (";".join(e["what"] for e in pf["missing"])[:160] if pf["missing"]
           else (f"庫忙 {pf['busy'][:80]}" if pf["busy"] else ""))
    fill = " → ".join(dict.fromkeys(e["short"] for e in pf["missing"]))
    if not real:
        chk("②–⑨ 實料八檢(版面結構/實料嵌入/Auto-Fixer/Auto-Optimizer/零 CDN/Gate Panel/紀律宣告/車道深化)", False,
            f"缺料 SKIP:{why} → {fill}", skip=True, weight=8)
    else:
        p = build()
        h = p.read_text(encoding="utf-8")
        chk("② 版面結構=操作員規格(兩欄 grid+38px 表頭+收合+@media+Alerts+Logs)",
            f"grid-template-columns: {t['panel_w_px']}px 1fr" in h
            and f"height: {t['header_h_px']}px" in h
            and ".left-panel.collapsed" in h
            and f"@media (max-width: {t['breakpoint_px']}px)" in h
            and 'id="alerts"' in h and 'id="logs"' in h)
        n_rows = h.count('"date": "') or h.count('"date":"')
        chk("③ 實料嵌入(三檔×近 240 交易日;duckdb 唯讀零發明)",
            all(f'value="{c}"' in h for c in STOCKS) and n_rows >= 600,
            f"(列 {n_rows})")
        chk("④ Auto-Fixer 五修留痕(欄位檢首列鍵/fixed.df 接線/ffill 正名/null 安全 IQR/typeof 閘)",
            'in (df[0] || {})' in h and "df = fixed.df" in h
            and "前值遞補" in h and 'filter(v => v != null' in h
            and 'typeof Plotly === "undefined"' in h)
        chk("⑤ Auto-Optimizer(isMobile 斷點+圖卡高 320-420+字級 11→10 全冊值)",
            f"window.innerWidth < {t['breakpoint_px']}" in h
            and f"baseHeightPC: {t['chart_max_h_px']}" in h
            and f'"%s"' % f"{t['font_mobile_px']}px" in h.replace("'", '"'))
        chk("⑥ 零 CDN 零外鏈(內建 SVG 車道;無 http 資源)",
            "http://" not in h and "https://" not in h and "<svg" in h.lower()
            or ("http://" not in h and "https://" not in h and "renderCharts" in h))
        chk("⑦ Gate Panel 六件(三下拉+雙日期+勾選群+收合鈕)",
            all(k in h for k in ("dropdown-stock", "dropdown-module",
                                 "dropdown-chart-type", "date-start", "date-end",
                                 "collapse-btn")) and "check-group" in h)
        chk("⑧ 紀律宣告(版面值單源冊/實料零發明/QA 修正留痕)",
            "版面值單源" in h and "零重測零發明" in h
            and "QA" in Path(__file__).read_text(encoding="utf-8"))
        chk("⑨ 車道深化(八模組+融資融券/成交值實料+主副雙圖+估值誠實現值)",
            all(m in h for m in ("成交值", "融資餘額", "融券餘額"))
            and '"margin":' in h and '"short":' in h and '"tvalue":' in h
            and 'id="chart-sub"' in h and 'id="val-row"' in h
            and "誠實列現值" in h)
    if "TW" in absent or not real:
        chk("⑩ 族群視角層(輪動快照≥10 群+層級切換+延續榜+輪動態燈+誠實出處)", False,
            f"缺料 SKIP:{'ROTATION_TW_* 無/半殘' if 'TW' in absent else why} → {_rot_fill('TW') if 'TW' in absent else fill}", skip=True)
    else:
        rot = harvest_rotation()
        chk("⑩ 族群視角層(輪動快照≥10 群+層級切換+延續榜+輪動態燈+誠實出處)",
            len(rot["groups"]) >= 10 and len(rot["rank"]) == 10
            and 'id="dropdown-layer"' in h and 'id="rank"' in h
            and '"gindex":' in h and "RotationState" not in h
            and "快照冊直出" in h and "ROTATION_TW_" in h,
            f"({len(rot['groups'])} 群·{rot['note'][:40]})")
    if "GLOBAL" in absent or not real:
        chk("⑪ 全球層(9 類別+宏觀因子四線+PROXY/REVIEW 誠實標記+榜通用)", False,
            f"缺料 SKIP:{'ROTATION_GLOBAL_* 無/半殘' if 'GLOBAL' in absent else why} → {_rot_fill('GLOBAL') if 'GLOBAL' in absent else fill}", skip=True)
    else:
        glb = harvest_global()
        chk("⑪ 全球層(9 類別+宏觀因子四線+PROXY/REVIEW 誠實標記+榜通用)",
            len(glb["groups"]) == 9 and len(glb["factors"]) == 4
            and all(len(v) > 100 for v in glb["factors"].values())
            and "PROXY" in glb["note"] and "REVIEW" in glb["note"]
            and 'VIA_GLB' in h and "全球共通" in h and ">全球<" in h)
    if not real:
        chk("⑫ 因子快照列(批191:features_daily 庫取零自算+八因子嵌入+NULL 誠實—+單一正主宣告)", False, f"缺料 SKIP:{why} → {fill}", skip=True)
    else:
        d = harvest_data()
        f2330 = (d["stocks"].get("2330") or {}).get("factors")
        chk("⑫ 因子快照列(批191:features_daily 庫取零自算+八因子嵌入+"
            "NULL 誠實—+單一正主宣告)",
            f2330 is not None and f2330["ret_1d"] is not None
            and 'id="factor-row"' in h and '"ret_20d":' in h
            and "因子庫單一正主" in h and "視窗不足誠實" in h,
            f"(2330@{f2330['date'] if f2330 else '缺'})")
    _selftest_batch400(chk)
    print(f"  [計] 十六檢 OK {16 - len(fails) - len(skips)} · FAIL {len(fails)} · SKIP {len(skips)}(誠實三態)")
    return 1 if fails else 0


def main(argv=None, pf_kw: dict | None = None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    if "--selftest" in args:
        print(f"=== VIA 儀表板({ENGINE_TAG})· 十六檢自測(零網路)===")
        return selftest()
    # 批400:缺料前檢 → [缺料]/[缺件] rc2 · 庫忙 rc3(誠實停;舊頁在位);全在位=零加印,渲染路徑同 v0106
    rc = report_preflight(preflight(**(pf_kw or {})))
    if rc:
        return rc
    try:
        p = build()
    except Exception as exc:   # 批400:渲染中例外一律誠實一行定位(零裸 traceback;舊頁在位)
        return _honest_stop(exc)
    print(f"[UI] {p.name} · 版面單源 {SSOT.name}[dashboard]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
