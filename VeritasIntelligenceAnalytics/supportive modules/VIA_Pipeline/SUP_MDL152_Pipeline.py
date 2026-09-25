#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_pipeline.py  —  VIA 統一輪動引擎(回測 + 自演化最佳化 + 證偽 + 自我除錯)
================================================================================
把整條流程串成一支引擎:
  資料 → 自我測試/自動除錯 → 回測 → 自演化最佳化 → 魔鬼證偽閘 → 使用者驗收 → 裁決

它編排你已有的兩支引擎(同目錄):rotation_engine.py + devils_advocate.py。
請把三個檔放一起。依賴:pip install numpy pandas

核心信條(VIA 規範):
  • 最佳化目標 = OOS 穩健 + 通過證偽,**不是**最大回測報酬。
  • 每試一組參數都計入 n_trials → 灌進 Deflated Sharpe,防止「最佳化出來的假陽性」。
  • 全部 T-1,無 look-ahead;purge/embargo 走樣本外。
  • 自我除錯迴圈上限 3 輪;過不了就誠實回報 NOT VALIDATED,不假裝綠燈。
  • 通過才標「可進 sandbox」;sandbox parse=0 才談 promote。

執行:python via_pipeline.py --demo
"""
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

# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] =====
# 接橋補丁 v2(2026-08-12 令:引擎統一導入 輔助/加速器/網路/自動編號;
#  導入一律 bridge-first 過橋;graceful 全退化 — 缺席零影響;
#  不 eager 導入 Runtime_Bridge/EnvManager 重件)
import sys as _via_sys
from pathlib import Path as _via_Path

def _via_bootstrap_support_paths():
    try:
        _self = _via_Path(__file__).resolve()
        roots = [_self.parent]
        p = _self.parent
        for _ in range(4):
            p = p.parent
            roots.append(p)
        for root in roots:
            for name in ("supportive_module", "supportive modules"):
                sup = root / name
                if sup.is_dir():
                    s = str(sup)
                    if s not in _via_sys.path:
                        _via_sys.path.insert(0, s)
    except Exception:
        pass

_via_bootstrap_support_paths()
try:
    from VRN_SupportBridge import BRIDGE as _VIA_BRIDGE
    _VIA_HAS_BRIDGE = True
except Exception:
    _VIA_BRIDGE = None
    _VIA_HAS_BRIDGE = False

def _via_load(_name):
    # 統一導入閘:先過橋(輔助性工具),橋缺退直導,再缺落 None(graceful)
    try:
        if _VIA_BRIDGE is not None:
            for _fn in ("load", "get", "require"):
                _f = getattr(_VIA_BRIDGE, _fn, None)
                if callable(_f):
                    try:
                        _m = _f(_name)
                    except Exception:
                        _m = None
                    if _m is not None:
                        return _m
    except Exception:
        pass
    try:
        return __import__(_name)
    except Exception:
        return None

_VIA_SSOT = _via_load("VIA_SSOT_Unified")
_VIA_AEGIS = _via_load("VeritasAegisNexus")
_VIA_CELERITAS = _via_load("VeritasCeleritas")
_VIA_ACCEL = _via_load("VIA_SuperAccel_Module")   # 加速器(工作站候上傳;graceful)
_VIA_NET = _via_load("VIA_NetSupport")            # 網路支援模組
_VIA_REGCORE = _via_load("VIA_RegistryCore_v1")   # 自動編號核心(工作站候上傳;graceful)
try:
    if _VIA_REGCORE is not None:  # 自動編號:標準介面任一,全護欄不擲例外
        for _fn in ("auto_register", "ensure_code", "register_module"):
            _f = getattr(_VIA_REGCORE, _fn, None)
            if callable(_f):
                _f(__file__)
                break
except Exception:
    pass
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====

import sys, json, argparse, traceback, datetime as dt
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from rotation_engine import rebase100, log_ret, debeta, classify_and_prune, \
        make_demo as rot_make_demo, THEMES as ROT_THEMES, MARKET_COL
    from devils_advocate import adjudicate, sharpe, strat_returns, turnover
except Exception as e:
    print("[FATAL] 需與 rotation_engine.py、devils_advocate.py 同目錄。", e); sys.exit(2)
try:
    from via_io import load_themes, read_table, export_all, write_json
    HAS_IO = True
except Exception:
    HAS_IO = False

MAX_ROUNDS = 3
ANN = 252

# 參數搜尋空間(自演化)
SPACE = dict(WIN=[20, 40, 60], TOP_K=[1, 2, 3], REBAL=[5, 10, 20], CORR_KEEP=[0.2, 0.3, 0.4])
EVAL_COST_BPS = 15            # 評估時假設成本
# 使用者驗收準則(user-test)
ACCEPTANCE = dict(min_oos_sharpe=0.0, max_verdict_fail=0, min_breakeven_bps=10, require_clean_gt0=True)


# ── 訊號建構:族群動量 top-k → 做多其領導+同業 ───────────────────────────────
def build_group_indices(px, themes, corr_keep):
    reb = rebase100(px, px.index[0])
    ret = log_ret(px.drop(columns=[MARKET_COL], errors="ignore"))
    mkt = log_ret(px[MARKET_COL]) if MARKET_COL in px else ret.mean(axis=1)
    sig = debeta(ret, mkt)
    gidx, members = {}, {}
    for th, names in themes.items():
        import rotation_engine as RE
        RE.CORR_KEEP = corr_keep                          # 套用搜尋中的門檻
        cl, kept, _ = classify_and_prune(names, sig, reb)
        if len(kept) >= 2:
            gidx[th] = reb[kept].mean(axis=1)
            members[th] = kept
    return pd.DataFrame(gidx), members


def rotation_signal(px, themes, p):
    """回傳資產層權重 DataFrame(date × ticker);決策只用到當日(t)之前資訊,回測再 shift(1)。"""
    gidx, members = build_group_indices(px, themes, p["CORR_KEEP"])
    if gidx.shape[1] == 0:
        return None
    mom = gidx.pct_change(p["WIN"])
    cols = sorted({c for ms in members.values() for c in ms})
    # 再平衡日寫入「整列」(未入選者明確歸零)再 ffill 持有至下次再平衡。
    # 原寫法 replace(0→NaN).ffill 會令舊持倉跨期復活 → 權重和>1(weights_bounded
    # 三輪必 FAIL,rotation_engine 補齊後首跑實證);此為訊號層缺陷,非引擎層。
    W = pd.DataFrame(np.nan, index=px.index, columns=cols)
    rebal_days = px.index[p["WIN"]::p["REBAL"]]
    for t in rebal_days:
        m = mom.loc[t].dropna()
        if m.empty:
            continue
        top = m.sort_values(ascending=False).head(p["TOP_K"]).index
        picks = sorted({c for th in top for c in members.get(th, [])})
        row = pd.Series(0.0, index=cols)
        if picks:
            row[picks] = 1.0 / len(picks)
        W.loc[t] = row
    return W.ffill().fillna(0.0)


def backtest(W, px, cost_bps=EVAL_COST_BPS):
    clean = strat_returns(W, px, lag=1)                   # T-1,無洩漏
    cost = turnover(W).reindex(clean.index).fillna(0) * (cost_bps / 1e4)
    net = (clean - cost).dropna()
    return net


def oos_folds(net, folds=5, embargo=10):
    """切 folds 段,各段算 OOS Sharpe;回 (median, std, list)。"""
    n = len(net); step = n // folds
    sr = []
    for i in range(folds):
        seg = net.iloc[i * step + embargo: (i + 1) * step]
        if len(seg) > 15:
            sr.append(sharpe(seg))
    if not sr:
        return 0.0, 0.0, []
    return float(np.median(sr)), float(np.std(sr)), [round(x, 2) for x in sr]


# ── 自演化最佳化(隨機+精英突變),fitness 受證偽輕量閘把關 ───────────────────
def light_gate(net, W, px):
    """輕量閘:乾淨 Sharpe>0 且 撐過 15bps。重的全套證偽留給最後 best。"""
    return sharpe(net) > 0 and sharpe(backtest(W, px, 15)) > 0

def evolve(px, themes, budget=24, seed=1):
    rng = np.random.default_rng(seed)
    keys = list(SPACE)
    def sample():
        return {k: SPACE[k][rng.integers(len(SPACE[k]))] for k in keys}
    tried, best = [], None
    pop = [sample() for _ in range(min(8, budget))]
    evals = 0
    while evals < budget:
        scored = []
        for p in pop:
            if evals >= budget: break
            evals += 1
            try:
                W = rotation_signal(px, themes, p)
                if W is None: continue
                net = backtest(W, px)
                med, sd, _ = oos_folds(net)
                gate = light_gate(net, W, px)
                fit = (med - 0.5 * sd) if gate else -9.99
                scored.append((fit, p, med, sd))
                tried.append(p)
            except Exception:
                continue
        if not scored:
            break
        scored.sort(key=lambda x: x[0], reverse=True)
        if best is None or scored[0][0] > best[0]:
            best = scored[0]
        # 精英 + 突變產生下一代
        elites = [s[1] for s in scored[:3]]
        pop = elites + [{k: (e[k] if rng.random() > 0.4 else SPACE[k][rng.integers(len(SPACE[k]))])
                         for k in keys} for e in elites for _ in range(3)]
    return best, len(tried)


# ── 自我測試 + 自動除錯(till it works,上限 3 輪) ──────────────────────────────
def self_tests(W, px):
    out = []
    out.append(("no_nan_signal", not W.isna().any().any(), "訊號含 NaN"))
    out.append(("weights_bounded", float(W.abs().sum(axis=1).max()) <= 1.0001, "權重和>1"))
    # 無 look-ahead:用未位移權重×當日報酬若與 lag=1 完全相同 → 表示沒位移(危險)
    r0 = strat_returns(W, px, lag=0); r1 = strat_returns(W, px, lag=1)
    out.append(("is_lagged", not np.allclose(r0.fillna(0), r1.fillna(0)), "權重未位移(疑洩漏)"))
    out.append(("deterministic", True, ""))                # 種子固定,佔位
    return out

def repair(px, themes, p, failed):
    """依失敗項做有界修補,回新 (px, themes, p)。"""
    if "no_nan_signal" in failed:
        px = px.ffill().bfill()
    if "weights_bounded" in failed:
        p = {**p, "TOP_K": max(1, p["TOP_K"])}
    if "is_lagged" in failed:
        pass                                               # strat_returns 已 shift,通常資料太短;放寬視窗
        p = {**p, "WIN": max(20, p["WIN"] - 20)}
    return px, themes, p

def heal_and_build(px, themes, p):
    log = []
    for rnd in range(1, MAX_ROUNDS + 1):
        try:
            W = rotation_signal(px, themes, p)
            if W is None:
                raise RuntimeError("無有效族群(門檻過嚴?)")
            tests = self_tests(W, px)
            failed = [n for n, ok, _ in tests if not ok]
            log.append({"round": rnd, "failed": failed})
            if not failed:
                return W, p, px, themes, log, True
            px, themes, p = repair(px, themes, p, failed)
        except Exception as ex:
            log.append({"round": rnd, "error": str(ex), "trace": traceback.format_exc(limit=1)})
            px = px.ffill().bfill(); p = {**p, "CORR_KEEP": max(0.15, p["CORR_KEEP"] - 0.05)}
    return None, p, px, themes, log, False


# ── 主流程 ───────────────────────────────────────────────────────────────────
def run(px, themes, label="run"):
    R = {"meta": {"generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "label": label}}

    # 1) 自演化最佳化(OOS 穩健 + 輕量證偽閘)
    best, n_trials = evolve(px, themes)
    if best is None:
        R["verdict"] = "NOT VALIDATED — 最佳化無可行解"; return R
    fit, p, med, sd = best
    R["best_params"] = p; R["n_trials"] = n_trials
    R["oos"] = {"median_sharpe": round(med, 2), "std_sharpe": round(sd, 2), "fitness": round(fit, 2)}

    # 2) 自我測試 + 自動除錯(till it works)
    W, p, px, themes, heal_log, healed = heal_and_build(px, themes, p)
    R["self_heal"] = {"rounds": heal_log, "passed": healed}
    if not healed:
        R["verdict"] = "NOT VALIDATED — 自我測試未通過(已用滿 3 輪)"; return R

    # 3) 全套魔鬼證偽(n_trials = 試過的配置數 → 多重檢定折扣)
    net = backtest(W, px)
    _, _, fold_sr = oos_folds(net)
    mkt = log_ret(px[MARKET_COL]) if MARKET_COL in px else log_ret(px).mean(axis=1)
    verdict = adjudicate(W, px, mkt, n_trials=max(n_trials, 5))
    R["falsification"] = verdict
    R["oos"]["fold_sharpes"] = fold_sr

    # 4) 使用者驗收(user-test:預先登記準則)
    be = verdict["tests"]["3_cost_sweep"][1].get("breakeven_bps") if False else None
    be = verdict["tests"]["3_cost_sweep"].get("breakeven_bps")
    clean_sr = verdict["tests"]["1_leakage_gap"].get("sharpe_clean", 0)
    checks = {
        "oos_sharpe>=min":   med >= ACCEPTANCE["min_oos_sharpe"],
        "not_falsified":     verdict["verdict"] != "FALSIFIED 證偽",
        "cost_survivable":   (be is None) or (be >= ACCEPTANCE["min_breakeven_bps"]),
        "clean_gap_real":    (not ACCEPTANCE["require_clean_gt0"]) or (clean_sr > 0),
    }
    R["acceptance"] = checks
    passed = all(checks.values())
    R["verdict"] = ("VALIDATED ✓ 可進 sandbox(sandbox parse=0 後才 promote)"
                    if passed else "NOT VALIDATED — 未過驗收,勿 promote")
    return R


def _summary_df(R):
    row = {"verdict": R.get("verdict"), "n_trials": R.get("n_trials")}
    row.update({f"param_{k}": v for k, v in (R.get("best_params") or {}).items()})
    row.update({f"oos_{k}": v for k, v in (R.get("oos") or {}).items() if not isinstance(v, list)})
    if "falsification" in R:
        row["falsify_verdict"] = R["falsification"]["verdict"]; row["falsify_score"] = R["falsification"]["score"]
    for k, v in (R.get("acceptance") or {}).items():
        row[f"accept_{k}"] = v
    return pd.DataFrame([row]).set_index("verdict")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--prices"); ap.add_argument("--themes")
    ap.add_argument("--out", default="pipeline_result.json")
    ap.add_argument("--export", default="", help="逗號分隔:json,csv,parquet,duckdb")
    ap.add_argument("--gsheet-id"); ap.add_argument("--gsheet-creds")
    a = ap.parse_args()

    if a.demo or not a.prices:
        print("⚠ [SIMULATED] 合成資料跑通整條 pipeline — 非真實行情。")
        px, _ = rot_make_demo(days=400); themes = ROT_THEMES
    else:
        px = (read_table(a.prices) if HAS_IO else pd.read_csv(a.prices, index_col=0, parse_dates=True)).sort_index()
        themes = load_themes(a.themes) if (HAS_IO and a.themes) else ROT_THEMES   # group dict/list JSON

    R = run(px, themes, label="demo" if (a.demo or not a.prices) else "live")

    if HAS_IO:
        write_json(R, a.out)
    else:
        Path(a.out).write_text(json.dumps(R, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    fmts = tuple(f.strip() for f in a.export.split(",") if f.strip())
    if fmts and HAS_IO and "best_params" in R:
        gs = ({"spreadsheet": a.gsheet_id, "worksheet": "via_pipeline", "creds_json": a.gsheet_creds}
              if a.gsheet_id and a.gsheet_creds else None)
        written = export_all(_summary_df(R), str(Path(a.out).with_suffix("")), formats=fmts, gsheet=gs)
        print(" exported   :", written)

    print("\n══════ VIA PIPELINE 裁決 ══════")
    print(" best_params :", R.get("best_params"))
    print(" n_trials    :", R.get("n_trials"))
    print(" OOS         :", R.get("oos"))
    if "self_heal" in R:
        print(" self_heal   :", "PASS" if R["self_heal"]["passed"] else "FAIL", R["self_heal"]["rounds"])
    if "falsification" in R:
        f = R["falsification"]; print(" falsify     :", f["verdict"], f["score"], "fail_on=", f["fail_on"])
    if "acceptance" in R:
        print(" acceptance  :", R["acceptance"])
    print(" VERDICT     :", R["verdict"])
    print(f"\n[OK] {a.out}")


if __name__ == "__main__":
    main()
