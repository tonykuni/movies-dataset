"""cli.py -- 命令列進入點.

用法:
    python -m twrevenue.cli fetch      # 抓資料 + 增量寫入 parquet/duckdb
    python -m twrevenue.cli analyze    # 讀資料庫 -> 三層分析 + 族群 + 真突破
    python -m twrevenue.cli report     # 產生 HTML 儀表板
    python -m twrevenue.cli run        # fetch + analyze + report 一條龍
    python -m twrevenue.cli demo       # 用合成資料跑通全流程 (免網路)
    python -m twrevenue.cli breakout   # 只看真突破名單 (終端輸出)
    python -m twrevenue.cli groups     # 顯示 + 驗證族群分類
    python -m twrevenue.cli selftest   # 跑全套內建測試

    可加 --config other.yaml 指定設定檔。
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd
import yaml

from . import fetch as fetch_mod
from . import classify as classify_mod
from . import analyze as analyze_mod
from . import report as report_mod
from . import groups as groups_mod
from . import store as store_mod
from . import breakout as breakout_mod
from . import csvio


def load_cfg(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _base_dir(cfg) -> str:
    return os.path.dirname(cfg["fetch"]["raw_out"]) or "data"


def _load_full(cfg) -> pd.DataFrame:
    """完整歷史 (供真突破偵測用 — 歷史越長, ATH 判定越可靠)."""
    df = store_mod.load(cfg, months_back=None)
    if df is not None:
        return df
    fp = cfg["fetch"]["raw_out"]
    if not os.path.exists(fp):
        sys.exit("找不到資料庫/資料檔 — 請先執行 `fetch` 或 `demo`。")
    return csvio.read(fp, dtype={"stock_id": str}, parse_dates=["date"])


def _load_window(cfg) -> pd.DataFrame:
    """分析視窗 (最近 months_back 個月)."""
    df = store_mod.load(cfg, months_back=cfg["fetch"]["months_back"])
    if df is not None:
        return df
    return _load_full(cfg)


def cmd_fetch(cfg):
    data = fetch_mod.fetch_all(cfg)
    store_mod.upsert(data, cfg)
    return data


def cmd_analyze(cfg, data=None):
    full = _load_full(cfg) if data is None else data
    window = _load_window(cfg) if data is None else data
    base = _base_dir(cfg)
    cyc_kw = cfg.get("cyclical_industries", [])
    full = classify_mod.tag_cyclical(full, cyc_kw)
    window = classify_mod.tag_cyclical(window, cyc_kw)

    result = analyze_mod.analyze(window, cfg)
    csvio.write(result, os.path.join(base, "analysis.csv"), cfg)
    print(f"分析完成 -> {base}/analysis.csv  ({len(result)} 家公司)")

    # 真突破偵測 (使用完整歷史)
    bo = breakout_mod.detect(full, cfg)
    if not bo.empty:
        csvio.write(bo, os.path.join(base, "breakout.csv"), cfg)
        s = breakout_mod.summary(bo)
        print(f"真突破偵測 -> {base}/breakout.csv  "
              f"(候選 {s['candidates']} / 真突破 {s['real']} / "
              f"低基期假象 {s['lowbase']} / 兩年無成長 {s['no_cagr']} / "
              f"未創高 {s['no_ath']} / 單月暴衝 {s['oneoff']})")

    groups = groups_mod.load_groups()
    if not groups.empty:
        gt = groups_mod.group_momentum(result, groups, cfg)
        csvio.write(gt, os.path.join(base, "group_analysis.csv"), cfg)
        pt = groups_mod.group_momentum(result, groups, cfg, level="parent")
        csvio.write(pt, os.path.join(base, "group_parent_analysis.csv"), cfg)
        print(f"族群動能 -> {base}/group_analysis.csv  "
              f"({len(pt)} 大類 / {len(gt)} 子族群, 兩階層)")

    sg = groups_mod.cyclical_sector_groups(result)
    if not sg.empty:
        st = groups_mod.order_sector_table(groups_mod.group_momentum(result, sg, cfg))
        csvio.write(st, os.path.join(base, "cyclical_sectors.csv"), cfg)
        print(f"週期六大類 -> {base}/cyclical_sectors.csv  "
              f"({len(st)} 類, {int(st['members'].sum())} 家)")
    return result, window, bo


def cmd_report(cfg, result=None, data=None, bo=None):
    base = _base_dir(cfg)
    if result is None:
        fp = os.path.join(base, "analysis.csv")
        if not os.path.exists(fp):
            sys.exit("找不到 analysis.csv — 請先執行 analyze。")
        result = csvio.read(fp, dtype={"stock_id": str}, parse_dates=["date"])
    if bo is None:
        fp = os.path.join(base, "breakout.csv")
        bo = (csvio.read(fp, dtype={"stock_id": str}, parse_dates=["date"])
              if os.path.exists(fp) else None)
    dm = None
    src = data if data is not None else result
    if "date" in src.columns:
        dm = pd.to_datetime(src["date"]).max().strftime("%Y-%m")

    groups = groups_mod.load_groups()
    group_table = groups_mod.group_momentum(result, groups, cfg) if not groups.empty else None
    parent_table = (groups_mod.group_momentum(result, groups, cfg, level="parent")
                    if not groups.empty else None)
    sector_groups = groups_mod.cyclical_sector_groups(result)
    sector_table = (groups_mod.order_sector_table(
        groups_mod.group_momentum(result, sector_groups, cfg))
        if not sector_groups.empty else None)

    html = report_mod.build_dashboard(
        result, cfg, data_month=dm, group_table=group_table, groups=groups,
        sector_table=sector_table, sector_groups=sector_groups, breakout_table=bo,
        parent_table=parent_table)
    out = cfg["report"]["out_html"]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"儀表板已產生 -> {out}")
    return out


def cmd_run(cfg):
    data = cmd_fetch(cfg)
    result, window, bo = cmd_analyze(cfg, data)
    cmd_report(cfg, result, window, bo)


def cmd_demo(cfg):
    """免網路: 合成資料 -> 增量資料庫 -> 分析 -> 儀表板."""
    from .synth import make_synthetic
    data = make_synthetic(cfg)
    os.makedirs(_base_dir(cfg), exist_ok=True)
    csvio.write(data, cfg["fetch"]["raw_out"], cfg)
    print(f"合成資料 -> {cfg['fetch']['raw_out']}  "
          f"({len(data)} 列, {data.stock_id.nunique()} 家, "
          f"{data.date.nunique()} 個月)")
    store_mod.upsert(data, cfg)
    result, window, bo = cmd_analyze(cfg)
    cmd_report(cfg, result, window, bo)


def cmd_breakout(cfg):
    """終端輸出真突破名單 + 被濾掉的低基期假象 (對照組)."""
    base = _base_dir(cfg)
    fp = os.path.join(base, "breakout.csv")
    if not os.path.exists(fp):
        sys.exit("找不到 breakout.csv — 請先執行 analyze 或 demo。")
    bo = csvio.read(fp, dtype={"stock_id": str})
    B = breakout_mod
    pd.set_option("display.width", 200)
    pd.set_option("display.unicode.east_asian_width", True)
    s = B.summary(bo)
    print(f"\n候選 {s['candidates']} 檔 → 真突破 {s['real']} · 低基期假象 {s['lowbase']} "
          f"· 兩年無成長 {s['no_cagr']} · 未創高 {s['no_ath']} · 單月暴衝 {s['oneoff']}\n")
    cols = ["stock_id", "name", "industry", "score", "yoy", "ttm_yoy",
            "ath_margin", "ath_streak", "base_pct", "base_ratio", "cagr_2y"]
    real = bo[bo.verdict == B.V_REAL].head(cfg["breakout"]["top_n"])
    print("=== 真突破 (五關全過) ===")
    print(real[cols].to_string(index=False) if len(real) else "  (無)")
    fake = bo[bo.verdict == B.V_LOWBASE].sort_values("yoy", ascending=False).head(15)
    print("\n=== 被濾掉的低基期假象 (YoY 漂亮但基期塌陷) ===")
    print(fake[["stock_id", "name", "yoy", "is_ath", "base_pct", "base_ratio",
                "cagr_2y"]].to_string(index=False) if len(fake) else "  (無)")


def cmd_groups(cfg):
    """顯示 + 驗證族群分類, 並用實際 MOPS 資料核對名稱/市場別/存在性."""
    from .tests import t_groups_ssot
    pd.set_option("display.width", 200)
    pd.set_option("display.unicode.east_asian_width", True)
    g = groups_mod.load_groups()
    allg = groups_mod.load_groups(include_flagged=True)
    if g.empty:
        sys.exit("找不到 twrevenue/groups.csv")
    print(f"族群分類 SSOT (兩階層): {g['parent'].nunique()} 大類 / "
          f"{g['group'].nunique()} 子族群 / {g['stock_id'].nunique()} 檔 "
          f"(多重歸屬 {int(g['stock_id'].duplicated().sum())} 筆)\n")
    for par, pd_ in g.groupby("parent", sort=False):
        print(f"  ■ {par}  ({pd_['group'].nunique()} 子族群 / "
              f"{pd_['stock_id'].nunique()} 檔)")
        for grp, d in pd_.groupby("group", sort=False):
            L = d[d.role == "L"]["name"].tolist()
            print(f"      └ {grp:16s} {len(d):2d} 檔 · 龍頭 {'、'.join(L) or '—'}")

    _LAB = {"flagged": "歸屬有疑慮", "excluded": "規模稀釋, 排除加權",
            "superseded": "已被細分取代"}
    held = allg[allg["status"] != ""]
    if not held.empty:
        print(f"\n── 保留於 CSV 但不納入分析 {len(held)} 筆 (只增不減) ──")
        for st, d in held.groupby("status"):
            print(f"  [{_LAB.get(st, st)}] {len(d)} 筆")
            for _, r in d.iterrows():
                print(f"      {r['stock_id']} {r['name']} @ {r['group']} — {r['flag']}")

    # 用實際抓取資料核對 (MOPS 為官方來源)
    data = store_mod.load(cfg, months_back=1)
    if data is not None and not data.empty:
        v = groups_mod.verify_against_data(allg, data)
        print(f"\n── 與 MOPS 實際資料核對 (基準月 "
              f"{pd.to_datetime(data['date']).max():%Y-%m}) ──")
        for key, label in [("missing", "查無此代號 (可能為興櫃/已下市/代號錯誤)"),
                           ("name_mismatch", "名稱不符"),
                           ("market_mismatch", "市場別不符")]:
            t = v[key]
            print(f"  {label}: {len(t)} 筆")
            if not t.empty:
                print(t.to_string(index=False))
    else:
        print("\n(尚無抓取資料 — 執行 fetch 或 demo 後可自動核對名稱/市場別)")

    # 產業一致性啟發式
    base = _base_dir(cfg)
    fp = os.path.join(base, "analysis.csv")
    if os.path.exists(fp):
        a = csvio.read(fp, dtype={"stock_id": str})
        out = groups_mod.industry_coherence(allg, a)
        print(f"\n── 族群內產業離群檢查: {len(out)} 筆待複核 ──")
        if not out.empty:
            print(out.to_string(index=False))

    try:
        print(f"\n[PASS] 結構驗證通過 · {t_groups_ssot()}")
    except AssertionError as e:
        sys.exit(f"[FAIL] 結構驗證失敗: {e}")


def cmd_selftest(cfg):
    from .tests import run_all
    if not run_all():
        sys.exit(1)


def main(argv=None):
    p = argparse.ArgumentParser(description="台股月營收動能引擎")
    p.add_argument("command", choices=["fetch", "analyze", "report", "run",
                                       "demo", "breakout", "groups", "selftest"])
    p.add_argument("--config", default="config.yaml")
    args = p.parse_args(argv)
    cfg = load_cfg(args.config)
    {
        "fetch": cmd_fetch, "analyze": lambda c: cmd_analyze(c),
        "report": lambda c: cmd_report(c), "run": cmd_run, "demo": cmd_demo,
        "breakout": cmd_breakout, "groups": cmd_groups, "selftest": cmd_selftest,
    }[args.command](cfg)


if __name__ == "__main__":
    main()
