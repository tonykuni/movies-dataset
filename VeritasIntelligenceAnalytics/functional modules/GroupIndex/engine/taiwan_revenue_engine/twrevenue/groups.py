"""groups.py -- 熱門族群分類層 (VIA 族群分類 v1.1 疊加).

資料來源: 使用者提供的 VIA 族群分類 (策展層 T2/T3), 抽取為 groups.csv:
    stock_id, name, group(族群), role(L/P/G 龍頭/第二梯隊/落後), market
角色 L/P/G 為人工策展的「領先性」判斷; 本引擎不採用檔案內的 hot/lead/chg
合成佔位數, 而是用 MOPS 真實月營收動能回填每個族群的實證強弱。

分工:
    VIA 檔案  -> 提供「族群骨架 + 龍頭角色」(誰在哪一群、誰是龍頭)
    本引擎    -> 提供「真實營收動能」(累計YoY / 多月趨勢 / 季節性 / 分數)
    合起來    -> 回答: 哪些熱門族群營收動能在加速? 龍頭的營收有沒有確認領先?

週期族群分流 (延續原則: 原物料/週期不看月營收):
    貨櫃航運 / 散裝航運 / 鋼鐵 / 條鋼  -> 標記週期, 不以月營收排名,
    改看 價格YoY / 庫存YoY / 產能利用率 / 毛利率YoY。
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

import os

import numpy as np
import pandas as pd

# 週期/原物料族群 (改看價格/庫存/毛利, 不看月營收)
# 含 VIA 族群名 (鋼鐵/條鋼/貨櫃航運/散裝航運) 與全市場六大週期類名
CYCLICAL_GROUPS = {"貨櫃航運", "散裝航運", "鋼鐵", "條鋼",
                   "水泥", "石化", "化工", "航運其他", "其他週期"}
# 非典型月營收族群 (月營收意義不同, 僅提示, 不強制排除)
ATYPICAL_GROUPS = {"金融"}

ROLE_LABEL = {"L": "龍頭", "P": "第二梯隊", "G": "落後"}


def load_groups(path: str | None = None) -> pd.DataFrame:
    """載入族群 SSOT (groups.csv)."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "groups.csv")
    if not os.path.exists(path):
        return pd.DataFrame(columns=["stock_id", "name", "group", "role", "market"])
    df = pd.read_csv(path, dtype={"stock_id": str})
    df["stock_id"] = df["stock_id"].str.strip()
    return df


def attach_groups(analysis: pd.DataFrame, groups: pd.DataFrame) -> pd.DataFrame:
    """把族群/角色疊到個股分析上 (多重歸屬 -> 一檔可展開成多列)."""
    if groups.empty:
        analysis = analysis.copy()
        analysis["group"] = np.nan
        analysis["role"] = np.nan
        return analysis
    g = groups[["stock_id", "group", "role"]]
    merged = analysis.merge(g, on="stock_id", how="left")
    return merged


def group_momentum(analysis: pd.DataFrame, groups: pd.DataFrame,
                   cfg: dict) -> pd.DataFrame:
    """計算每個族群的實證營收動能總表.

    以 VIA 族群為單位, 用引擎算出的個股動能 (score/cum_yoy/yoy/tier) 聚合。
    """
    if groups.empty:
        return pd.DataFrame()
    ac = cfg["analyze"]
    a = analysis.set_index("stock_id")
    rows = []
    for grp, gdf in groups.groupby("group", sort=False):
        ids = gdf["stock_id"].tolist()
        roles = dict(zip(gdf["stock_id"], gdf["role"]))
        sub = a.reindex(ids)                      # 對齊分析結果 (缺資料 -> NaN)
        covered = sub.dropna(subset=["cum_yoy"])
        n_members = len(ids)
        n_cov = len(covered)
        is_cyc = grp in CYCLICAL_GROUPS

        # 龍頭清單 (role == L)
        leaders = [i for i in ids if roles.get(i) == "L"]
        leader_cov = covered.reindex([i for i in leaders if i in covered.index])

        def _med(col, frame=covered):
            v = frame[col].dropna()
            return float(v.median()) if len(v) else np.nan

        med_cum = _med("cum_yoy")
        med_yoy = _med("yoy")
        med_score = _med("score")

        # ---- 族群加總表現 (營收加權, 反映族群真實體量) ----
        def _sum(col):
            return covered[col].dropna().sum() if col in covered else np.nan

        rev_now = _sum("revenue")
        rev_ly = _sum("revenue_prev_year")
        cum_now = _sum("cum_revenue")
        cum_ly = _sum("cum_revenue_prev_year")
        agg_yoy = ((rev_now / rev_ly - 1) * 100
                   if rev_ly and rev_ly > 0 else np.nan)
        agg_cum_yoy = ((cum_now / cum_ly - 1) * 100
                       if cum_ly and cum_ly > 0 else np.nan)
        breadth_pos = (float((covered["yoy"] > 0).mean()) * 100
                       if n_cov else np.nan)
        n_pref = int((covered["tier"] == "優選").sum()) if n_cov else 0
        n_warn = int((covered["tier"] == "警戒").sum()) if n_cov else 0
        n_accel = int(covered["yoy_accelerating"].sum()) if n_cov else 0

        # 龍頭確認: 龍頭中位動能分數 >= 族群中位 => 龍頭以營收確認領先
        leader_score = (float(leader_cov["score"].median())
                        if len(leader_cov) and leader_cov["score"].notna().any()
                        else np.nan)
        if is_cyc or pd.isna(leader_score) or pd.isna(med_score):
            leader_confirm = None
        else:
            leader_confirm = bool(leader_score >= med_score)

        # 族群動能型態
        # 判定以「族群加總累計YoY」為主 (反映體量), 廣度為輔
        anchor = agg_cum_yoy if pd.notna(agg_cum_yoy) else med_cum
        if is_cyc:
            verdict = "週期(改看價格/庫存)"
        elif pd.isna(anchor):
            verdict = "資料不足"
        elif anchor >= ac["cum_yoy_strong"] and (breadth_pos or 0) >= 60:
            verdict = "族群加速"
        elif anchor < 0 or (breadth_pos or 0) < 40:
            verdict = "族群轉弱"
        else:
            verdict = "分歧/中性"

        rows.append({
            "group": grp,
            "is_cyclical": is_cyc,
            "atypical": grp in ATYPICAL_GROUPS,
            "members": n_members,
            "covered": n_cov,
            "group_score": round(med_score, 1) if pd.notna(med_score) else np.nan,
            "agg_cum_yoy": round(agg_cum_yoy, 1) if pd.notna(agg_cum_yoy) else np.nan,
            "agg_yoy": round(agg_yoy, 1) if pd.notna(agg_yoy) else np.nan,
            "group_revenue": rev_now if pd.notna(rev_now) else np.nan,
            "median_cum_yoy": round(med_cum, 1) if pd.notna(med_cum) else np.nan,
            "median_yoy": round(med_yoy, 1) if pd.notna(med_yoy) else np.nan,
            "breadth_pos": round(breadth_pos, 0) if pd.notna(breadth_pos) else np.nan,
            "n_pref": n_pref,
            "n_warn": n_warn,
            "n_accel": n_accel,
            "n_leaders": len(leaders),
            "leader_names": "、".join(gdf[gdf.role == "L"]["name"].tolist()),
            "leader_score": round(leader_score, 1) if pd.notna(leader_score) else np.nan,
            "leader_confirm": leader_confirm,
            "verdict": verdict,
        })

    out = pd.DataFrame(rows)
    # 排序: 非週期依族群分數; 週期族群放最後
    out["_k"] = out["group_score"].fillna(-1)
    out.loc[out["is_cyclical"], "_k"] = -2
    out = out.sort_values("_k", ascending=False).drop(columns="_k")
    out = out.reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out


def cyclical_sector_groups(analysis: pd.DataFrame) -> pd.DataFrame:
    """由個股分析結果建「全市場週期六大類」的 groups 形式表.

    與 VIA 族群不同: 這是全市場覆蓋 (凡 cyclical_sector 非空的公司都入列),
    來源是 MOPS 產業別自動歸類, 免手工維護。role 一律留空 (週期類不設龍頭)。
    """
    if "cyclical_sector" not in analysis.columns:
        return pd.DataFrame(columns=["stock_id", "name", "group", "role", "market"])
    cyc = analysis[analysis["cyclical_sector"].notna()].copy()
    if cyc.empty:
        return pd.DataFrame(columns=["stock_id", "name", "group", "role", "market"])
    out = pd.DataFrame({
        "stock_id": cyc["stock_id"].astype(str),
        "name": cyc.get("name", ""),
        "group": cyc["cyclical_sector"],
        "role": np.nan,
        "market": "",
    })
    return out.drop_duplicates(subset=["stock_id", "group"]).reset_index(drop=True)


def order_sector_table(gt: pd.DataFrame) -> pd.DataFrame:
    """週期類表依固定順序排列 (水泥/鋼鐵/石化/化工/貨櫃/散裝/航運其他/其他週期)."""
    from .classify import SECTOR_ORDER
    if gt.empty:
        return gt
    key = {s: i for i, s in enumerate(SECTOR_ORDER)}
    gt = gt.copy()
    gt["_o"] = gt["group"].map(key).fillna(99)
    gt = gt.sort_values("_o").drop(columns="_o").reset_index(drop=True)
    gt["rank"] = range(1, len(gt) + 1)
    return gt


def group_members_detail(analysis: pd.DataFrame, groups: pd.DataFrame,
                         grp: str) -> pd.DataFrame:
    """回傳單一族群的成員明細 (含角色與實證動能), 供儀表板展開用."""
    ids = groups[groups["group"] == grp]["stock_id"].tolist()
    roles = dict(zip(groups[groups["group"] == grp]["stock_id"],
                     groups[groups["group"] == grp]["role"]))
    a = analysis.set_index("stock_id").reindex(ids).reset_index()
    a["role"] = a["stock_id"].map(roles)
    a["role_label"] = a["role"].map(ROLE_LABEL)
    rank = {"L": 0, "P": 1, "G": 2}
    a["_r"] = a["role"].map(rank).fillna(3)
    a = a.sort_values(["_r", "score"], ascending=[True, False]).drop(columns="_r")
    return a
