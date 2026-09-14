"""groups.py -- 熱門族群分類層 (VIA 族群分類 v1.1 疊加, 兩階層).

資料來源: VIA 族群分類 (策展層 T2/T3) -> groups.csv:
    stock_id, name, parent(L1大類), group(L2子族群),
    role(L/P/G 龍頭/第二梯隊/落後), market, source, status, flag

兩階層 (two-level taxonomy):
    L1 parent  = 12 大類 (半導體 / AI 伺服器 / 電子零組件 / ...)
    L2 group   = 48 子族群 (晶圓代工 / 封測 OSAT / AI 導軌·滑軌 / ...)
    同一檔可跨子族群 (如 3711 同在 封測 與 CoWoS); L1 加總時**依個股去重**,
    否則營收加權會重複計入同一家公司。

status 欄 (SSOT 生命週期, 只增不減不刪列):
    ""           = 生效, 納入分析
    "flagged"    = 歸屬有疑慮 (誤植 / 關聯薄弱)
    "excluded"   = 歸屬正確但規模稀釋 (該題材佔自身營收過低, 加權後失真)
    "superseded" = 已被更細的子族群完全取代 (避免與細分結果重複計數)

分工:
    VIA 檔案  -> 族群骨架 + 龍頭角色 (誰在哪一群、誰是龍頭)
    本引擎    -> 真實營收動能 (不採用檔案內 hot/lead/chg 合成佔位值)
    合起來    -> 哪些熱門族群營收動能在加速? 龍頭的營收有沒有確認領先?
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

# 週期族群 (含 VIA 族群名與全市場六大週期類名)
CYCLICAL_GROUPS = {"貨櫃航運", "散裝航運", "鋼鐵", "條鋼",
                   "水泥", "石化", "化工", "航運其他", "其他週期"}
ATYPICAL_GROUPS = {"金融"}          # 非典型月營收, 僅提示
# L1 大類層級的週期判定 (營收=價×量, 價格波動主導 -> 不看月營收動能)
CYCLICAL_PARENTS = {"原物料週期", "航運運輸"}
ROLE_LABEL = {"L": "龍頭", "P": "第二梯隊", "G": "落後"}


def load_groups(path: str | None = None,
                include_flagged: bool = False) -> pd.DataFrame:
    """載入族群 SSOT (兩階層).

    status 非空的列預設**不納入分析**, 但資料列一律保留在 groups.csv
    (只增不減); include_flagged=True 可取回全部列檢視。
    """
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "groups.csv")
    cols = ["stock_id", "name", "parent", "group", "role", "market",
            "source", "status", "flag"]
    if not os.path.exists(path):
        return pd.DataFrame(columns=cols)
    from . import csvio
    df = csvio.read(path, dtype={"stock_id": str})
    df["stock_id"] = df["stock_id"].str.strip()
    for c in ("flag", "source", "status", "parent"):
        if c not in df.columns:
            df[c] = ""
    df["flag"] = df["flag"].fillna("")
    df["status"] = df["status"].fillna("")
    # 舊版檔 (無 status 欄) 相容: flag 非空即視為 flagged
    df.loc[(df["status"] == "") & (df["flag"] != ""), "status"] = "flagged"
    df["parent"] = df["parent"].fillna("").replace("", np.nan).fillna(df["group"])
    if not include_flagged:
        df = df[df["status"] == ""].reset_index(drop=True)
    return df


def verify_against_data(groups: pd.DataFrame, data: pd.DataFrame) -> dict:
    """用實際抓取的 MOPS 資料核對 groups.csv (名稱 / 市場別 / 是否存在).

    MOPS 是官方來源, 所以它說了算 — 這能一次驗證全部成員, 不必逐檔人工查。
    回傳 {missing, name_mismatch, market_mismatch} 三張表。
    """
    if groups.empty or data is None or data.empty:
        return {"missing": pd.DataFrame(), "name_mismatch": pd.DataFrame(),
                "market_mismatch": pd.DataFrame()}
    MKT = {"sii": "上市", "otc": "上櫃"}
    d = data.sort_values("date").drop_duplicates("stock_id", keep="last")
    d = d.set_index(d["stock_id"].astype(str))
    ref_name = d["name"].astype(str) if "name" in d else pd.Series(dtype=str)
    ref_mkt = (d["market"].astype(str).map(lambda m: MKT.get(m, m))
               if "market" in d else pd.Series(dtype=str))

    g = groups.copy()
    g["stock_id"] = g["stock_id"].astype(str)
    g["_ref_name"] = g["stock_id"].map(ref_name)
    g["_ref_mkt"] = g["stock_id"].map(ref_mkt)

    missing = g[g["_ref_name"].isna()][["stock_id", "name", "group", "market", "source"]]
    known = g[g["_ref_name"].notna()]
    nm = known[known["name"].astype(str).str.strip()
               != known["_ref_name"].str.strip()]
    mk = known[known["market"].astype(str).str.strip()
               != known["_ref_mkt"].str.strip()]
    cols = ["stock_id", "name", "_ref_name", "group", "market", "_ref_mkt", "source"]
    return {"missing": missing,
            "name_mismatch": nm[cols].rename(
                columns={"_ref_name": "MOPS名稱", "_ref_mkt": "MOPS市場"}),
            "market_mismatch": mk[cols].rename(
                columns={"_ref_name": "MOPS名稱", "_ref_mkt": "MOPS市場"})}


def industry_coherence(groups: pd.DataFrame, analysis: pd.DataFrame,
                       min_share: float = 0.5) -> pd.DataFrame:
    """族群內產業一致性啟發式檢查.

    同一族群的成員多半落在少數幾個官方產業別; 若某檔的產業別與族群主流
    差異過大, 很可能是歸類錯誤 (例如 IC 設計公司被放進矽晶圓族群)。
    回傳離群成員清單供人工複核 — 是提示, 不是自動刪除。
    """
    if groups.empty or analysis is None or analysis.empty:
        return pd.DataFrame()
    if "industry_canon" not in analysis.columns:
        return pd.DataFrame()
    ind = analysis.set_index("stock_id")["industry_canon"]
    rows = []
    for grp, d in groups.groupby("group"):
        sub = d.copy()
        sub["industry"] = sub["stock_id"].map(ind)
        s = sub["industry"].dropna()
        if len(s) < 4:
            continue
        top = s.value_counts(normalize=True)
        main = top.index[0]
        if top.iloc[0] < min_share:      # 族群本身就分散 -> 不判離群
            continue
        for _, r in sub[sub["industry"].notna() & (sub["industry"] != main)].iterrows():
            share = float(top.get(r["industry"], 0.0))
            if share <= 0.12:            # 該產業在群內佔比極低 -> 離群
                rows.append({"stock_id": r["stock_id"], "name": r["name"],
                             "group": grp, "該檔產業": r["industry"],
                             "族群主流產業": main,
                             "主流佔比": f"{top.iloc[0]*100:.0f}%",
                             "source": r.get("source", "")})
    return pd.DataFrame(rows)


_ROLE_RANK = {"L": 0, "P": 1, "G": 2}


def dedupe_members(gdf: pd.DataFrame) -> pd.DataFrame:
    """同一檔跨多個子族群時只留一列 (保留角色最高者).

    L1 大類加總是營收加權 (Σ當月 / Σ去年同月); 若 3711 同時出現在
    「封測 OSAT」與「CoWoS」, 不去重就會被計入兩次, 加總值失真。
    """
    g = gdf.copy()
    g["_r"] = g["role"].map(_ROLE_RANK).fillna(3)
    return (g.sort_values("_r", kind="stable")
             .drop_duplicates(subset=["stock_id"], keep="first")
             .drop(columns="_r"))


def group_momentum(analysis: pd.DataFrame, groups: pd.DataFrame,
                   cfg: dict, level: str = "group") -> pd.DataFrame:
    """族群實證營收動能總表 (加總 = 營收加權).

    level="group"  -> L2 子族群 (48 群)
    level="parent" -> L1 大類   (12 類, 成員自動去重)
    """
    if groups.empty or level not in groups.columns:
        return pd.DataFrame()
    ac = cfg["analyze"]
    a = analysis.set_index("stock_id")
    is_parent = (level == "parent")
    rows = []
    for grp, gdf in groups.groupby(level, sort=False):
        n_sub = int(gdf["group"].nunique())
        if is_parent:
            gdf = dedupe_members(gdf)
        ids = gdf["stock_id"].tolist()
        roles = dict(zip(gdf["stock_id"], gdf["role"]))
        sub = a.reindex(ids)
        covered = sub.dropna(subset=["cum_yoy"])
        n_members, n_cov = len(ids), len(covered)
        is_cyc = grp in (CYCLICAL_PARENTS if is_parent else CYCLICAL_GROUPS)
        leaders = [i for i in ids if roles.get(i) == "L"]
        leader_cov = covered.reindex([i for i in leaders if i in covered.index])

        def _med(col):
            v = covered[col].dropna() if col in covered else pd.Series(dtype=float)
            return float(v.median()) if len(v) else np.nan

        def _sum(col):
            return covered[col].dropna().sum() if col in covered else np.nan

        med_cum, med_yoy, med_score = _med("cum_yoy"), _med("yoy"), _med("score")
        rev_now, rev_ly = _sum("revenue"), _sum("revenue_prev_year")
        cum_now, cum_ly = _sum("cum_revenue"), _sum("cum_revenue_prev_year")
        agg_yoy = ((rev_now / rev_ly - 1) * 100) if rev_ly and rev_ly > 0 else np.nan
        agg_cum_yoy = ((cum_now / cum_ly - 1) * 100) if cum_ly and cum_ly > 0 else np.nan
        breadth_pos = (float((covered["yoy"] > 0).mean()) * 100) if n_cov else np.nan
        n_pref = int((covered["tier"] == "優選").sum()) if n_cov else 0
        n_warn = int((covered["tier"] == "警戒").sum()) if n_cov else 0
        n_accel = int(covered["yoy_accelerating"].sum()) if n_cov else 0

        leader_score = (float(leader_cov["score"].median())
                        if len(leader_cov) and leader_cov["score"].notna().any() else np.nan)
        leader_confirm = (None if (is_cyc or pd.isna(leader_score) or pd.isna(med_score))
                          else bool(leader_score >= med_score))

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
            "group": grp, "level": level,
            "n_subgroups": n_sub if is_parent else 1,
            "is_cyclical": is_cyc,
            "atypical": grp in ATYPICAL_GROUPS,
            "members": n_members, "covered": n_cov,
            "group_score": round(med_score, 1) if pd.notna(med_score) else np.nan,
            "agg_cum_yoy": round(agg_cum_yoy, 1) if pd.notna(agg_cum_yoy) else np.nan,
            "agg_yoy": round(agg_yoy, 1) if pd.notna(agg_yoy) else np.nan,
            "median_cum_yoy": round(med_cum, 1) if pd.notna(med_cum) else np.nan,
            "median_yoy": round(med_yoy, 1) if pd.notna(med_yoy) else np.nan,
            "breadth_pos": round(breadth_pos, 0) if pd.notna(breadth_pos) else np.nan,
            "n_pref": n_pref, "n_warn": n_warn, "n_accel": n_accel,
            "n_leaders": len(leaders),
            "leader_names": "、".join(gdf[gdf.role == "L"]["name"].tolist()),
            "leader_score": round(leader_score, 1) if pd.notna(leader_score) else np.nan,
            "leader_confirm": leader_confirm, "verdict": verdict,
        })

    out = pd.DataFrame(rows)
    out["_k"] = out["group_score"].fillna(-1)
    out.loc[out["is_cyclical"], "_k"] = -2
    out = out.sort_values("_k", ascending=False).drop(columns="_k").reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out


def cyclical_sector_groups(analysis: pd.DataFrame) -> pd.DataFrame:
    """由個股分析結果建「全市場週期六大類」的 groups 形式表 (全市場覆蓋)."""
    if "cyclical_sector" not in analysis.columns:
        return pd.DataFrame(columns=["stock_id", "name", "group", "role", "market"])
    cyc = analysis[analysis["cyclical_sector"].notna()].copy()
    if cyc.empty:
        return pd.DataFrame(columns=["stock_id", "name", "group", "role", "market"])
    out = pd.DataFrame({
        "stock_id": cyc["stock_id"].astype(str), "name": cyc.get("name", ""),
        "group": cyc["cyclical_sector"], "role": np.nan, "market": "",
    })
    return out.drop_duplicates(subset=["stock_id", "group"]).reset_index(drop=True)


def order_sector_table(gt: pd.DataFrame) -> pd.DataFrame:
    from .classify import SECTOR_ORDER
    if gt.empty:
        return gt
    key = {s: i for i, s in enumerate(SECTOR_ORDER)}
    gt = gt.copy()
    gt["_o"] = gt["group"].map(key).fillna(99)
    gt = gt.sort_values("_o").drop(columns="_o").reset_index(drop=True)
    gt["rank"] = range(1, len(gt) + 1)
    return gt


def subgroups_of(group_table: pd.DataFrame, groups: pd.DataFrame,
                 parent: str) -> pd.DataFrame:
    """某 L1 大類底下的 L2 子族群動能列 (已依 group_score 排序)."""
    if group_table is None or group_table.empty or groups.empty:
        return pd.DataFrame()
    subs = groups[groups["parent"] == parent]["group"].unique().tolist()
    return group_table[group_table["group"].isin(subs)]


def group_members_detail(analysis: pd.DataFrame, groups: pd.DataFrame,
                         grp: str, level: str = "group") -> pd.DataFrame:
    sel = groups[groups[level] == grp] if level in groups.columns \
        else groups[groups["group"] == grp]
    if level == "parent":
        sel = dedupe_members(sel)
    ids = sel["stock_id"].tolist()
    roles = dict(zip(sel["stock_id"], sel["role"]))
    a = analysis.set_index("stock_id").reindex(ids).reset_index()
    a["role"] = a["stock_id"].map(roles)
    a["role_label"] = a["role"].map(ROLE_LABEL)
    rank = {"L": 0, "P": 1, "G": 2}
    a["_r"] = a["role"].map(rank).fillna(3)
    return a.sort_values(["_r", "score"], ascending=[True, False]).drop(columns="_r")
