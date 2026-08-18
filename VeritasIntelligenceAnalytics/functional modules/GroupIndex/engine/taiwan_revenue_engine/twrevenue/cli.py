"""cli.py -- 命令列進入點.

用法:
    python -m twrevenue.cli fetch      # 抓資料 + 增量寫入 parquet/duckdb
    python -m twrevenue.cli analyze    # 讀資料庫 -> 分析 -> data/analysis.csv
    python -m twrevenue.cli report     # 讀分析 -> 產生 HTML 儀表板
    python -m twrevenue.cli run        # fetch + analyze + report 一條龍
    python -m twrevenue.cli demo       # 用合成資料跑通全流程 (免網路, 驗證用)
    python -m twrevenue.cli groups     # 顯示 + 驗證族群分類 (編輯 groups.csv 後執行)
    python -m twrevenue.cli selftest   # 跑全套內建測試

    可加 --config other.yaml 指定設定檔。
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


def load_cfg(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_raw(cfg) -> pd.DataFrame:
    """優先讀累計 parquet (取 months_back 視窗); 無則退回 CSV."""
    df = store_mod.load(cfg, months_back=cfg["fetch"]["months_back"])
    if df is not None:
        return df
    fp = cfg["fetch"]["raw_out"]
    if not os.path.exists(fp):
        sys.exit(f"找不到資料庫/資料檔 — 請先執行 `fetch` 或 `demo`。")
    return pd.read_csv(fp, dtype={"stock_id": str}, parse_dates=["date"])


def cmd_fetch(cfg):
    data = fetch_mod.fetch_all(cfg)
    store_mod.upsert(data, cfg)     # 累計增量寫入 parquet + duckdb
    return data


def cmd_analyze(cfg, data=None):
    if data is None:
        data = _load_raw(cfg)
    data = classify_mod.tag_cyclical(data, cfg.get("cyclical_industries", []))
    result = analyze_mod.analyze(data, cfg)
    base = os.path.dirname(cfg["fetch"]["raw_out"])
    out_fp = os.path.join(base, "analysis.csv")
    result.to_csv(out_fp, index=False)
    print(f"分析完成 -> {out_fp}  ({len(result)} 家公司)")
    # 族群動能層 (VIA 族群 × 實證營收)
    groups = groups_mod.load_groups()
    if not groups.empty:
        gt = groups_mod.group_momentum(result, groups, cfg)
        gt.to_csv(os.path.join(base, "group_analysis.csv"), index=False)
        print(f"族群動能 -> {os.path.join(base,'group_analysis.csv')}  "
              f"({len(gt)} 族群)")
    # 週期六大類 (全市場, 依 MOPS 產業別自動歸類)
    sg = groups_mod.cyclical_sector_groups(result)
    if not sg.empty:
        st = groups_mod.order_sector_table(
            groups_mod.group_momentum(result, sg, cfg))
        st.to_csv(os.path.join(base, "cyclical_sectors.csv"), index=False)
        print(f"週期六大類 -> {os.path.join(base,'cyclical_sectors.csv')}  "
              f"({len(st)} 類, {int(st['members'].sum())} 家)")
    return result, data


def cmd_report(cfg, result=None, data=None):
    if result is None:
        fp = os.path.join(os.path.dirname(cfg["fetch"]["raw_out"]), "analysis.csv")
        if not os.path.exists(fp):
            sys.exit("找不到 analysis.csv — 請先執行 analyze。")
        result = pd.read_csv(fp, dtype={"stock_id": str}, parse_dates=["date"])
    dm = None
    if data is not None and "date" in data.columns:
        dm = pd.to_datetime(data["date"]).max().strftime("%Y-%m")
    elif "date" in result.columns:
        dm = pd.to_datetime(result["date"]).max().strftime("%Y-%m")
    groups = groups_mod.load_groups()
    group_table = None
    if not groups.empty:
        group_table = groups_mod.group_momentum(result, groups, cfg)
    sector_groups = groups_mod.cyclical_sector_groups(result)
    sector_table = None
    if not sector_groups.empty:
        sector_table = groups_mod.order_sector_table(
            groups_mod.group_momentum(result, sector_groups, cfg))
    html = report_mod.build_dashboard(result, cfg, data_month=dm,
                                      group_table=group_table, groups=groups,
                                      sector_table=sector_table,
                                      sector_groups=sector_groups)
    out = cfg["report"]["out_html"]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"儀表板已產生 -> {out}")
    return out


def cmd_run(cfg):
    data = cmd_fetch(cfg)
    result, data = cmd_analyze(cfg, data)
    cmd_report(cfg, result, data)


def cmd_demo(cfg):
    """免網路: 合成資料 -> 增量資料庫 -> 分析 -> 儀表板 (驗證全管線)."""
    from .synth import make_synthetic
    data = make_synthetic(cfg)
    os.makedirs(os.path.dirname(cfg["fetch"]["raw_out"]), exist_ok=True)
    data.to_csv(cfg["fetch"]["raw_out"], index=False)
    print(f"合成資料 -> {cfg['fetch']['raw_out']}  "
          f"({len(data)} 列, {data.stock_id.nunique()} 家)")
    store_mod.upsert(data, cfg)     # demo 也走增量資料庫路徑
    result, data = cmd_analyze(cfg, data)
    cmd_report(cfg, result, data)


def cmd_groups(cfg):
    """顯示 + 驗證族群分類 (編輯 twrevenue/groups.csv 後執行此指令)."""
    from .tests import t_groups_ssot
    g = groups_mod.load_groups()
    if g.empty:
        sys.exit("找不到 twrevenue/groups.csv")
    print(f"族群分類 SSOT: {g['group'].nunique()} 群 / "
          f"{g['stock_id'].nunique()} 檔 (多重歸屬 "
          f"{int(g['stock_id'].duplicated().sum())} 檔)\n")
    for grp, d in g.groupby("group", sort=False):
        roles = d.set_index("stock_id")["role"]
        L = d[d.role == "L"]["name"].tolist()
        print(f"  {grp:12s} {len(d):2d} 檔 · 龍頭 {'、'.join(L) or '—'}")
    print()
    try:
        msg = t_groups_ssot()
        print(f"[PASS] 驗證通過 · {msg}")
    except AssertionError as e:
        sys.exit(f"[FAIL] 驗證失敗: {e}")


def cmd_selftest(cfg):
    from .tests import run_all
    if not run_all():
        sys.exit(1)


def main(argv=None):
    p = argparse.ArgumentParser(description="台股月營收動能引擎")
    p.add_argument("command",
                   choices=["fetch", "analyze", "report", "run", "demo",
                            "groups", "selftest"])
    p.add_argument("--config", default="config.yaml")
    args = p.parse_args(argv)
    cfg = load_cfg(args.config)
    {
        "fetch": cmd_fetch, "analyze": lambda c: cmd_analyze(c),
        "report": lambda c: cmd_report(c), "run": cmd_run, "demo": cmd_demo,
        "groups": cmd_groups, "selftest": cmd_selftest,
    }[args.command](cfg)


if __name__ == "__main__":
    main()
