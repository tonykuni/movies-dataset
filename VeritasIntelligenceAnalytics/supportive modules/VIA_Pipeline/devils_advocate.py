#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
devils_advocate.py  —  VIA 魔鬼辯論 / 策略證偽工具
================================================================================
對任何「輪動/擇時」訊號跑一套標準證偽攻擊,輸出裁決計分卡。
核心信條:通過條件 ≠「回測賺錢」,而是「撐過全部攻擊 + 有可證明的 leaky-vs-clean 落差」。

輸入:
  prices : DataFrame[date × ticker]  收盤價
  signal : DataFrame[date × ticker]  部位/權重(策略「想持有」的權重,未位移)
  market : Series                    大盤報酬(去β基準)
  n_trials : int                     你「試過幾組」(多重檢定膨脹)→ Deflated Sharpe 用

攻擊清單(每項回 pass / wounded / fail + 指標):
  1 leakage_gap   T-1(乾淨) vs T0(洩漏) 的 Sharpe 缺口
  2 factor_alpha  去β/因子中性後 alpha 是否還在
  3 cost_sweep    成本掃描,找損益兩平 bps
  4 regime_split  高/低波動 regime 各自 Sharpe
  5 deflated_SR   多重檢定折扣後的 Deflated Sharpe Ratio
  6 bootstrap_p   block-bootstrap 顯著性(保留自相關)
  7 stability     參數/子樣本穩定度(IS vs OOS 衰減)

依賴:pip install numpy pandas    執行:python devils_advocate.py --demo
"""

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

import sys, json, argparse, datetime as dt
from pathlib import Path
import numpy as np, pandas as pd
from math import erf, sqrt

ANN = 252

# ── 基礎 ─────────────────────────────────────────────────────────────────────
def _phi(x): return 0.5 * (1 + erf(x / sqrt(2)))                 # 標準常態 CDF

def sharpe(r, ann=ANN):
    r = pd.Series(r).dropna()
    return float(r.mean() / (r.std() + 1e-12) * np.sqrt(ann)) if len(r) > 2 else 0.0

def strat_returns(signal, prices, lag=1):
    """部位 lag 天後 × 次日報酬 → 策略日報酬。lag=1 為乾淨(T-1);lag=0 為洩漏(同日)。"""
    ret = np.log(prices).diff()
    w = signal.shift(lag).reindex(ret.index)
    w = w.div(w.abs().sum(axis=1) + 1e-12, axis=0)               # 標準化權重
    return (w * ret).sum(axis=1)

def turnover(signal, lag=1):
    w = signal.shift(lag)
    w = w.div(w.abs().sum(axis=1) + 1e-12, axis=0)
    return w.diff().abs().sum(axis=1)


# ── 攻擊 ─────────────────────────────────────────────────────────────────────
def t1_leakage_gap(signal, prices):
    clean = strat_returns(signal, prices, lag=1)
    leak  = strat_returns(signal, prices, lag=0)
    sc, sl = sharpe(clean), sharpe(leak)
    gap = sl - sc
    # 解讀:乾淨應 < 洩漏(有時序資訊),但乾淨仍須 > 0;若乾淨≈0而洩漏巨大→edge來自洩漏
    if sc <= 0.1 and gap > 1.0:  v = "fail"      # 邊際全來自洩漏
    elif sc > 0.3 and gap > 0.3: v = "pass"      # 乾淨有效且存在合理時序缺口
    else:                        v = "wounded"
    return v, dict(sharpe_clean=round(sc,2), sharpe_leaked=round(sl,2), gap=round(gap,2)), clean

def factor_alpha(clean, market, factors=None):
    df = pd.concat([clean.rename("y"), market.rename("mkt")], axis=1)
    if factors is not None: df = pd.concat([df, factors], axis=1)
    df = df.dropna()
    if len(df) < 20: return "wounded", dict(note="樣本不足")
    Y = df["y"].values
    X = np.column_stack([np.ones(len(df))] + [df[c].values for c in df.columns if c != "y"])
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ beta
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (resid.var(ddof=X.shape[1])))
    t_alpha = beta[0] / (se[0] + 1e-12)
    v = "pass" if abs(t_alpha) >= 2.0 else ("wounded" if abs(t_alpha) >= 1.0 else "fail")
    return v, dict(alpha_daily=round(float(beta[0]),5), t_alpha=round(float(t_alpha),2),
                   note="去β/因子中性後 alpha t<2 → 多半只是因子曝險")

def cost_sweep(signal, prices, clean, bps=(0,5,10,20,50)):
    tn = turnover(signal).reindex(clean.index).fillna(0)
    res = {}
    breakeven = None
    for b in bps:
        net = clean - tn * (b/1e4)
        s = sharpe(net); res[f"{b}bps"] = round(s,2)
        if breakeven is None and s <= 0: breakeven = b
    v = "pass" if res.get("20bps",0) > 0.3 else ("wounded" if res.get("10bps",0) > 0 else "fail")
    return v, dict(sharpe_by_cost=res, breakeven_bps=breakeven,
                   avg_turnover=round(float(tn.mean()),3))

def regime_split(clean, market):
    # vol 與 clean 起訖不同(rolling 20 吃頭、回測 lag 吃頭)→ 布林索引必先對齊
    vol = market.rolling(20).std().reindex(clean.index)
    med = vol.median()
    hi = clean[(vol >= med).fillna(False)]; lo = clean[(vol < med).fillna(False)]
    s_hi, s_lo = sharpe(hi), sharpe(lo)
    v = "pass" if (s_hi>0 and s_lo>0) else ("wounded" if (s_hi>0 or s_lo>0) else "fail")
    return v, dict(sharpe_highvol=round(s_hi,2), sharpe_lowvol=round(s_lo,2),
                   note="僅單一 regime 為正 → regime 依賴")

def deflated_sharpe(clean, n_trials=20):
    r = clean.dropna(); T = len(r)
    if T < 30: return "wounded", dict(note="樣本不足")
    sr = sharpe(r, ann=1)                                         # 非年化
    sk = float(((r-r.mean())**3).mean()/(r.std()**3+1e-12))
    ku = float(((r-r.mean())**4).mean()/(r.std()**4+1e-12))
    # 多重檢定門檻 SR*(Bailey & López de Prado 近似)
    emc = 0.5772
    z = (1-emc)*_phi_inv(1-1/n_trials) + emc*_phi_inv(1-1/(n_trials*np.e))
    sr_star = np.sqrt(1/(T-1)) * z * (np.std([sr])+ 0)           # 保守:trial SR 變異未知→用 1/sqrt(T) 尺度
    sr_star = np.sqrt(1.0/(T-1)) * z                              # 尺度化門檻
    psr = _phi(((sr - sr_star) * np.sqrt(T-1)) / np.sqrt(1 - sk*sr + (ku-1)/4*sr**2 + 1e-9))
    v = "pass" if psr >= 0.95 else ("wounded" if psr >= 0.75 else "fail")
    return v, dict(SR_daily=round(sr,3), SR_star=round(float(sr_star),3),
                   deflated_PSR=round(float(psr),3), n_trials=n_trials)

def _phi_inv(p):                                                 # 反常態(Acklam 近似)
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    pl,ph=0.02425,1-0.02425
    if p<pl:
        q=np.sqrt(-2*np.log(p)); return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p>ph:
        q=np.sqrt(-2*np.log(1-p)); return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q=p-0.5; r=q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

def bootstrap_p(clean, block=10, n=1000, seed=1):
    r = clean.dropna().values; T=len(r)
    if T < 30: return "wounded", dict(note="樣本不足")
    obs = r.mean()/(r.std()+1e-12)
    rng = np.random.default_rng(seed); cnt=0
    nb = T//block
    for _ in range(n):
        idx = rng.integers(0, T-block, nb)
        samp = np.concatenate([r[i:i+block] for i in idx])
        samp = samp - samp.mean()                                # 設為 H0:均值0
        if samp.mean()/(samp.std()+1e-12) >= obs: cnt+=1
    p = (cnt+1)/(n+1)
    v = "pass" if p<=0.05 else ("wounded" if p<=0.15 else "fail")
    return v, dict(block_bootstrap_p=round(p,3))

def stability(signal, prices, k=2):
    """子樣本(前/後半)Sharpe 衰減;不重估參數的快速穩定度檢查。"""
    clean = strat_returns(signal, prices, 1).dropna()
    h = len(clean)//2
    s_is, s_oos = sharpe(clean.iloc[:h]), sharpe(clean.iloc[h:])
    decay = s_is - s_oos
    v = "pass" if (s_oos>0 and decay<s_is*0.6) else ("wounded" if s_oos>0 else "fail")
    return v, dict(sharpe_first_half=round(s_is,2), sharpe_second_half=round(s_oos,2), decay=round(decay,2))


# ── 裁決 ─────────────────────────────────────────────────────────────────────
def adjudicate(signal, prices, market, n_trials=20):
    v1, d1, clean = t1_leakage_gap(signal, prices)
    tests = {
        "1_leakage_gap":  (v1, d1),
        "2_factor_alpha": factor_alpha(clean, market),
        "3_cost_sweep":   cost_sweep(signal, prices, clean),
        "4_regime_split": regime_split(clean, market),
        "5_deflated_SR":  deflated_sharpe(clean, n_trials),
        "6_bootstrap_p":  bootstrap_p(clean),
        "7_stability":    stability(signal, prices),
    }
    score = {"pass":2, "wounded":1, "fail":0}
    pts = sum(score[v] for v,_ in tests.values()); mx = 2*len(tests)
    fails = [k for k,(v,_) in tests.items() if v=="fail"]
    verdict = ("SURVIVES 存活" if pts>=mx*0.8 and not fails else
               "FALSIFIED 證偽" if fails else "WOUNDED 受傷")
    return {"verdict": verdict, "score": f"{pts}/{mx}", "fail_on": fails,
            "tests": {k:{"result":v, **d} for k,(v,d) in tests.items()}}


# ── demo:已知乾淨 vs 已知洩漏,看機制能否分辨 ───────────────────────────────
def make_demo(days=400, n=8, seed=3):
    rng=np.random.default_rng(seed)
    idx=pd.bdate_range(end=dt.date.today(), periods=days)
    px=pd.DataFrame(100*np.exp(np.cumsum(rng.normal(0.0003,0.012,(days,n)),0)),
                    index=idx, columns=[f"S{i}" for i in range(n)])
    ret=np.log(px).diff()
    mkt=ret.mean(axis=1)
    mom=ret.rolling(20).mean()                                   # 乾淨:過去20日動量(會被 shift)
    sig_clean=(mom.rank(axis=1,pct=True)-0.5).fillna(0)          # 橫斷面動量權重
    sig_leak =(ret.rank(axis=1,pct=True)-0.5).fillna(0)          # 洩漏:用「當日」報酬排序
    return px, mkt, sig_clean, sig_leak


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--demo",action="store_true")
    ap.add_argument("--out",default="devils_verdict.json"); ap.add_argument("--trials",type=int,default=20)
    a=ap.parse_args()
    if a.demo or True:                                           # 目前僅 demo 入口;接真實改這裡讀檔
        if not a.demo: print("⚠ 無輸入,跑 --demo 合成資料(SIMULATED)")
        px, mkt, sig_clean, sig_leak = make_demo()
        out={"meta":{"generated":dt.datetime.now().strftime("%Y-%m-%d %H:%M"),"data":"SIMULATED demo"},
             "clean_logic": adjudicate(sig_clean, px, mkt, a.trials),
             "leaky_logic": adjudicate(sig_leak,  px, mkt, a.trials)}
        Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
        for name in ("clean_logic","leaky_logic"):
            r=out[name]; print(f"\n■ {name}: {r['verdict']}  score={r['score']}  fail_on={r['fail_on']}")
            for k,t in r["tests"].items(): print(f"   {k:16s} {t['result']}")
        print(f"\n[OK] {a.out}")

if __name__=="__main__":
    main()
