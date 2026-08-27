#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_GlobalETF_RiskModel · run_monitor.py
=============================================================================
VERITAS INTELLIGENCE ANALYTICS · 全球 ETF 風險同步觀測引擎（MDL009 ETFRISK）
姊妹引擎：MDL008 VIA_GlobalETFFlow（T1 真流）。本引擎為 T3 風險判讀層：
  五大風險分數（美元/利率/信用/商品 + 財政脆弱度）→ FIS 同式合成
  Regime 規則判讀（9 態）＋ RRG 區域輪動 ＋ 同步矩陣/領先滯後/PC1
  Forward P/E 倒算 EPS 結轉（Calculated_NotOriginal）＋ 惡魔驗證面板

用法
  python run_monitor.py                          # T4 demo 世界，完整輸出
  python run_monitor.py --days 780 --seed 7      # 換 demo 參數
  python run_monitor.py --source csv --prices p.csv --macro m.csv
  python run_monitor.py --selftest               # 離線驗收閘（EXIT 0/1）

治理：純標準庫；只讀來源；輸出 append-only（output/RUN_*/ + run_ledger.jsonl）；
UTF-8 no BOM；demo=T4 SYNTHETIC 全程掛標。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(MODULE_ROOT))

from engine import __engine__, __version__                        # noqa: E402
from engine import data_layer as dl                               # noqa: E402
from engine import mathkit as mk                                  # noqa: E402
from engine import report as rp                                   # noqa: E402
from engine.earnings import build_earnings_ledger                 # noqa: E402
from engine.factors import FactorPanel                            # noqa: E402
from engine.regime import classify_regime                         # noqa: E402
from engine.rotation import compute_rotation                      # noqa: E402
from engine.scores import (band_for, compute_fragility,           # noqa: E402
                           compute_pulse, compute_regional_potential,
                           compute_scores)
from engine.sync import compute_sync                              # noqa: E402

GROUP_ZH = {
    "global_equity": "全球股市", "us_equity": "美國股市",
    "developed_ex_us": "成熟非美", "emerging_markets": "新興市場",
    "us_rates": "美債利率", "credit": "信用債", "commodities": "商品",
    "currency": "匯率", "real_assets": "不動產", "digital_assets": "數位資產",
}
DUAL_VERIFY = [("HYG", "JNK"), ("MCHI", "FXI"), ("EEM", "VWO")]


# --------------------------------------------------------------------------- #
# 管線
# --------------------------------------------------------------------------- #

def build_dataset(config, config_path, market):
    panel = FactorPanel(market, benchmark=config["def_benchmark"])
    uni = dl.universe_tickers(config)

    scores = compute_scores(panel, config)
    scores_risk = {sid: s["risk"] for sid, s in scores.items()}
    pulse = compute_pulse(panel, config)
    fundamentals = {k: v for k, v in
                    dl.load_json(MODULE_ROOT / config["def_fragility"]["fundamentals_file"]).items()
                    if not k.startswith("_")}
    regional = compute_regional_potential(panel, config, fundamentals)
    fragility = compute_fragility(panel, config, fundamentals)
    rotation = compute_rotation(panel, config, uni)
    sync = compute_sync(panel, config, uni)
    regime = classify_regime(panel, config, scores_risk)
    snapshots = dl.load_json(MODULE_ROOT / config["def_earnings"]["sources_file"])
    earnings = build_earnings_ledger(market, config, fundamentals, snapshots,
                                     scores_risk.get("usd_stress"))

    # 全球熱力圖
    tf = config["def_timeframes_days"]
    heat = {}
    for group, members in config["def_etf_universe"].items():
        rows = []
        for m in members:
            rets = {}
            for label, k in tf.items():
                if label == "252d":
                    continue
                rets[label] = panel.ret(m["ticker"], int(k))
            rows.append({"ticker": m["ticker"], "name": m["name"], "ret": rets})
        heat[GROUP_ZH.get(group, group)] = rows

    # 利率/美元面板
    def yield_row(sid, name):
        s = panel.macro_series(sid)
        return {"id": sid, "name": name, "kind": "yield", "level": s[-1],
                "chg20": mk.series_change(s, 20)}

    y10, y2 = panel.macro_series("DGS10"), panel.macro_series("DGS2")
    curve = [a - b for a, b in zip(y10, y2)]
    rates_panel = [
        yield_row("DGS2", "美債2Y"), yield_row("DGS10", "美債10Y"),
        yield_row("DFII10", "10Y實質利率"), yield_row("T10YIE", "10Y通膨預期"),
        {"id": "10Y-2Y", "name": "殖利率曲線", "kind": "yield",
         "level": curve[-1], "chg20": mk.series_change(curve, 20)},
    ]
    for tkr, nm in (("UUP", "美元"), ("TLT", "美債20Y+"), ("TIP", "抗通膨債"),
                    ("GLD", "黃金"), ("HYG", "高收益債"), ("EMB", "新興美元債")):
        rates_panel.append({"id": tkr, "name": nm, "kind": "etf",
                            "level": panel.prices(tkr)[-1],
                            "chg20": panel.ret(tkr, 20)})

    devil = build_devil_panel(panel, market, regime, earnings, fundamentals)

    run_id = rp.make_run_id(config["def_output"]["run_prefix"],
                            config["def_output"]["run_suffix"])
    synthetic = market.provenance.get("data_source") == "synthetic_demo"
    summary = {
        "run_id": run_id, "engine": __engine__, "engine_version": __version__,
        "config_version": config["def_version"], "asof": market.asof,
        "data_source": market.provenance.get("data_source"),
        "truth_tier": market.provenance.get("truth_tier"),
        "gate": ("T4_SYNTHETIC_PIPELINE_DEMO" if synthetic else "T3_ESTIMATE_READY"),
        "regime_top": regime["top"]["id"], "regime_confidence": regime["confidence"],
        "scores": {sid: s["risk"] for sid, s in scores.items()},
        "pulse_z": pulse["z"], "pc1_share": sync["pc1_share"],
        "drawdown_sync": sync["drawdown_sync"]["count"],
        "devil_flags": len(devil),
    }
    return {
        "run_id": run_id, "engine_id": __engine__, "engine_version": __version__,
        "config_version": config["def_version"],
        "config_hash": rp.config_hash(config_path),
        "asof": market.asof, "provenance": market.provenance,
        "scores": scores, "pulse": pulse, "regional_potential": regional,
        "fragility": fragility, "rotation": rotation, "sync": sync,
        "regime": regime, "earnings": earnings, "heatmap": heat,
        "rates_panel": rates_panel, "devil_panel": devil, "summary": summary,
    }


def build_devil_panel(panel, market, regime, earnings, fundamentals):
    """惡魔驗證彙整：資料出處、雙重驗證、鈍化來源、判讀模糊，全部上桌。"""
    sev_zh = {"critical": "嚴重", "serious": "高", "warning": "注意", "good": "通過"}
    rows = []

    def add(severity, flag, detail):
        rows.append({"severity": severity, "severity_zh": sev_zh[severity],
                     "flag": flag, "detail": detail})

    if market.provenance.get("data_source") == "synthetic_demo":
        add("critical", "synthetic_data",
            "全部價格為 T4 合成示範資料（seed=%s），任何判讀僅驗證管線本身"
            % market.provenance.get("seed"))
    add("warning", "fundamentals_needs_verify",
        "財政/外部收支欄位為 demo 量級估值（Demo_Estimate_NeedsVerify），"
        "正式使用須以 IMF/World Bank/BIS 官方值覆寫")
    for a, b in DUAL_VERIFY:
        try:
            rel = panel.rel(a, b, 20)
        except ValueError:
            continue
        if rel is not None and abs(rel) > 0.015:
            add("serious", "dual_verify_divergence",
                "%s vs %s 20日報酬差 %+.2f%%（同曝險雙證分歧，查資料或折溢價）"
                % (a, b, rel * 100))
    for r in earnings["active"]:
        st = r["staleness"]["state"]
        if st in ("NEEDS_REFRESH", "REJECT_FOR_CURRENT_VALUATION"):
            add("serious", "stale_forward_pe",
                "%s forward P/E 已 %d 天未更新（%s）" %
                (r["index_name"], r["stale_days"], st))
        for d in r["devil_warnings"]:
            if d["flag"] in ("forward_pe_rounding", "source_divergence",
                             "valuation_expansion_warning"):
                add("warning", d["flag"], "%s：%s" % (r["index_name"], d["detail"]))
    if regime["confidence"] < 0.20:
        add("warning", "regime_ambiguous",
            "Regime 信心 %.0f%% 偏低，多態並存，降低方向性押注"
            % (regime["confidence"] * 100))
    rank = {"critical": 0, "serious": 1, "warning": 2, "good": 3}
    rows.sort(key=lambda r: rank[r["severity"]])
    return rows


def run_pipeline(args):
    config_path = Path(args.config) if args.config else \
        MODULE_ROOT / "config" / "global_etf_risk_config.json"
    config = dl.load_config(config_path)
    if args.source == "csv":
        if not args.prices:
            print("[FAIL] --source csv 需要 --prices", file=sys.stderr)
            return 2
        market = dl.load_csv_wide(args.prices, args.macro,
                                  macro_series=config["def_macro_series"])
        # fail-closed 前置驗證：缺檔缺欄要一次講清楚，不留深層 traceback
        missing_t = [u["ticker"] for u in dl.universe_tickers(config)
                     if u["ticker"] not in market.prices]
        missing_m = [s for s in config["def_macro_series"]
                     if s not in market.macro]
        if missing_t or missing_m:
            if missing_t:
                print("[FAIL] prices CSV 缺 universe ticker（%d）：%s"
                      % (len(missing_t), ", ".join(missing_t)), file=sys.stderr)
            if missing_m:
                print("[FAIL] macro CSV 缺序列：%s" % ", ".join(missing_m),
                      file=sys.stderr)
            return 2
    else:
        market = dl.generate_demo(config, asof=args.asof, days=args.days,
                                  seed=args.seed)

    ds = build_dataset(config, config_path, market)
    out_root = Path(args.outdir) if args.outdir else MODULE_ROOT / "output"
    run_dir, html_path = rp.write_outputs(ds, out_root)

    if not args.quiet:
        s = ds["summary"]
        print("=" * 74)
        print("VIA %s %s | %s | asof %s" % (__engine__, __version__,
                                            config["def_version"], s["asof"]))
        print("=" * 74)
        print("Gate        : %s" % s["gate"])
        print("Regime      : %s（信心 %.0f%%）" %
              (ds["regime"]["top"]["name_zh"], s["regime_confidence"] * 100))
        for sid, sc in ds["scores"].items():
            print("Score       : %-20s %5s /100  [%s]" %
                  (sid, "—" if sc["risk"] is None else "%.1f" % sc["risk"],
                   sc["band"]["label_zh"]))
        print("Pulse z     : %s   PC1 %s   回撤同步 %d 檔   惡魔旗標 %d" %
              (s["pulse_z"], s["pc1_share"], s["drawdown_sync"], s["devil_flags"]))
        print("RunDir      : %s" % run_dir)
        print("Dashboard   : %s" % html_path)
    return 0


# --------------------------------------------------------------------------- #
# SELFTEST（離線驗收閘，房規：PASS/FAIL 矩陣 + EXIT）
# --------------------------------------------------------------------------- #

def selftest():
    R = []

    def T(name, cond, detail=""):
        R.append((name, bool(cond), detail))

    config_path = MODULE_ROOT / "config" / "global_etf_risk_config.json"
    config = dl.load_config(config_path)
    uni = dl.universe_tickers(config)
    T("S01 SSOT 載入且宇宙>=50檔", len(uni) >= 50, "n=%d" % len(uni))

    z = mk.robust_z(10.0, [0.1 * i for i in range(-30, 30)])
    T("S02 robust_z 極端值被夾在 +3", z == 3.0, "z=%s" % z)
    T("S03 fis/risk 值域", abs(mk.fis_scale(3.0)) < 100.0001
      and mk.fis_scale(0.0) == 0.0, "fis(3)=%.2f" % mk.fis_scale(3.0))

    m1 = dl.generate_demo(config, asof="2026-08-14", days=400, seed=7)
    m2 = dl.generate_demo(config, asof="2026-08-14", days=400, seed=7)
    same = all(m1.prices[t][-1] == m2.prices[t][-1] for t in m1.prices)
    T("S04 種子再現性（同seed全等）", same and m1.macro == m2.macro)

    ds = build_dataset(config, config_path, m1)
    T("S05 腳本Regime被辨識為Top1",
      ds["regime"]["top"]["id"] == m1.provenance["scripted_regime_at_asof"],
      "top=%s script=%s" % (ds["regime"]["top"]["id"],
                            m1.provenance["scripted_regime_at_asof"]))
    risks = [s["risk"] for s in ds["scores"].values()]
    T("S06 四分數皆在 0..100", all(r is not None and 0 <= r <= 100 for r in risks),
      str(risks))
    quads = {r["quadrant"] for r in ds["rotation"]["rows"] if r["quadrant"]}
    T("S07 RRG 產出且象限有效", quads and quads <= {"Q1", "Q2", "Q3", "Q4"},
      str(sorted(quads)))
    T("S08 PC1 共振占比在 0..1",
      ds["sync"]["pc1_share"] is not None and 0 <= ds["sync"]["pc1_share"] <= 1,
      str(ds["sync"]["pc1_share"]))

    # 隱含 EPS：倒算、凍結、staleness
    act = {r["index_name"]: r for r in ds["earnings"]["active"]}
    spx = act.get("S&P 500")
    eps_ok = spx and abs(spx["implied_forward_eps"] - 6890.59 / 23.1) < 0.01
    T("S09 隱含EPS=Level/PE 且標 Calculated",
      eps_ok and spx["eps_status"] == "Calculated_NotOriginal",
      "eps=%s" % (spx and spx["implied_forward_eps"]))
    tw = act.get("MSCI Taiwan")
    T("S10 staleness 分級運作（TW 6/30 應非 FRESH）",
      tw and tw["staleness"]["state"] in
      ("STALE_WARNING", "NEEDS_REFRESH", "REJECT_FOR_CURRENT_VALUATION"),
      tw and "%sd→%s" % (tw["stale_days"], tw["staleness"]["state"]))
    T("S11 每日重算的是P/E不是EPS",
      spx and spx["daily_repriced_pe"] is not None
      and abs(spx["published_forward_pe"] * spx["proxy_ratio_since_publish"]
              - spx["daily_repriced_pe"]) < 0.01)

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rp.write_outputs(ds, td)
        ds2 = dict(ds)
        ds2["run_id"] = ds["run_id"] + "_B"
        ds2["summary"] = dict(ds["summary"], run_id=ds2["run_id"])
        rp.write_outputs(ds2, td)
        ledger = (Path(td) / "run_ledger.jsonl").read_text(encoding="utf-8")
        T("S12 run_ledger append-only（兩次=兩行）",
          ledger.count("\n") == 2)
        html = (Path(td) / ds["run_id"] / "dashboard.html").read_text(encoding="utf-8")
        T("S13 儀表板完整（DOCTYPE/理/SYNTHETIC標記）",
          html.startswith("<!DOCTYPE html>") and "理" in html
          and "SYNTHETIC" in html and len(html) > 20000,
          "%d bytes" % len(html))
        T("S14 儀表板無未替換占位符", "%(" not in html and "${" not in html)

    T("S15 惡魔面板揭露T4合成資料（critical）",
      any(d["flag"] == "synthetic_data" and d["severity"] == "critical"
          for d in ds["devil_panel"]),
      "devil_flags=%d" % len(ds["devil_panel"]))

    # 多種子穩健性（房規）：腳本 regime 在 5 種子中至少 4 次為 Top1
    seed_hits, seed_tops = 0, []
    for sd in (1, 2, 3, 5, 7):
        msd = dl.generate_demo(config, asof="2026-08-14", days=400, seed=sd)
        dsd = build_dataset(config, config_path, msd)
        top = dsd["regime"]["top"]["id"]
        seed_tops.append("%d:%s" % (sd, "✓" if top ==
                                    msd.provenance["scripted_regime_at_asof"] else top))
        seed_hits += (top == msd.provenance["scripted_regime_at_asof"])
    T("S16 多種子Regime穩健(>=4/5)", seed_hits >= 4,
      "hits=%d/5 [%s]" % (seed_hits, " ".join(seed_tops)))

    fails = sum(1 for _, ok, _ in R if not ok)
    print("=" * 74)
    print("VIA %s %s | SELFTEST | 純標準庫 · T4 SYNTHETIC 驗收世界" %
          (__engine__, __version__))
    print("=" * 74)
    for name, ok, detail in R:
        print("  %-4s | %s%s" % ("PASS" if ok else "FAIL", name,
                                 ("  [%s]" % detail) if detail else ""))
    print()
    print("✅ 全數通過 EXIT=0" if fails == 0 else "❌ %d 項失敗 EXIT=1" % fails)
    return 0 if fails == 0 else 1


def _utf8_console_guard():
    """Windows 舊主控台（cp950 等）防炸：無法編碼的字元以替代字輸出，EXIT 碼不變。"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except Exception:
                pass


def main(argv=None):
    _utf8_console_guard()
    ap = argparse.ArgumentParser(description="VIA MDL009 全球 ETF 風險同步觀測引擎")
    ap.add_argument("--source", choices=["demo", "csv"], default="demo")
    ap.add_argument("--prices", help="寬表價格 CSV（date + ticker 欄）")
    ap.add_argument("--macro", help="寬表宏觀 CSV（DGS2/DGS10/DFII10/T10YIE）")
    ap.add_argument("--asof", help="demo 截止日 YYYY-MM-DD（預設今日）")
    ap.add_argument("--days", type=int, default=780)
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--outdir", help="輸出根目錄（預設 module/output）")
    ap.add_argument("--config", help="SSOT config 路徑")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    try:
        return run_pipeline(args)
    except Exception as exc:                                   # noqa: BLE001
        if os.environ.get("VIA_DEBUG"):
            raise
        print("[FAIL] %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        print("[HINT] 設 VIA_DEBUG=1 可看完整 traceback", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
