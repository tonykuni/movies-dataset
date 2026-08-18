# -*- coding: utf-8 -*-
"""VIA FIS 方法驗證 / 受控回測 harness (v2, 修正流量顯著性與時變AUM正規化).

驗證「有機流→穩健z→tanh」FIS 估計子能否顯著抓【方向】與【流量強度】,
並讓證偽閘(null不顯著 / leaky>>clean / OOS / 當沖去噪 / data-quality / 正規化)正確作動。
沙盒無行情真值 → 用已知 DGP(真流訊號 AR1 同驅動觀測流與次日報酬 + 微結構雜訊 + 當沖churn + 洩漏 + 時變AUM)。
同一 harness 之後餵真值(TWSE T86 / ETF 創贖 / CFTC COT)即為真回測。
"""
import numpy as np
from scipy.stats import rankdata, norm, ttest_rel, ttest_1samp

RNG = np.random.default_rng(20260705)
N, T, W, KAPPA, SIMS = 50, 750, 120, 1.5, 80
PHI, G, SE, SF = 0.90, 0.35, 0.90, 4.5
CHURN_BASE, CHURN_K, PEEK = 4.5, 9.0, 0.60

def daily_ic(sig, fwd):
    out = []
    for t in range(sig.shape[0]):
        a, b = sig[t], fwd[t]
        m = np.isfinite(a) & np.isfinite(b)
        if m.sum() < 5: out.append(np.nan); continue
        ra = rankdata(a[m]); rb = rankdata(b[m]); ra -= ra.mean(); rb -= rb.mean()
        d = np.sqrt((ra*ra).sum()*(rb*rb).sum())
        out.append((ra*rb).sum()/d if d > 0 else np.nan)
    return np.array(out)

def ic_stats(ics):
    ics = ics[np.isfinite(ics)]
    if len(ics) == 0: return dict(ic=np.nan, t=np.nan, p=np.nan)
    mu, sd = ics.mean(), ics.std(ddof=1); ir = mu/sd if sd > 0 else np.nan
    t = ir*np.sqrt(len(ics)) if sd > 0 else np.nan
    p = 2*(1-norm.cdf(abs(t))) if np.isfinite(t) else np.nan
    return dict(ic=mu, t=t, p=p)

def robust_z(panel):
    from numpy.lib.stride_tricks import sliding_window_view
    z = np.full_like(panel, np.nan)
    win = sliding_window_view(panel, W, axis=0)
    med = np.median(win, axis=2)
    mad = np.median(np.abs(win - med[:, :, None]), axis=2)
    sd = 1.4826*mad
    z[W-1:, :] = np.where(sd > 0, (panel[W-1:, :] - med)/sd, 0.0)
    return z

def one_sim():
    s = np.zeros((T, N)); s[0] = RNG.standard_normal(N)
    for t in range(1, T): s[t] = PHI*s[t-1] + np.sqrt(1-PHI**2)*RNG.standard_normal(N)
    s = (s - s.mean(1, keepdims=True))/(s.std(1, keepdims=True)+1e-9)

    r_next = G*s + SE*RNG.standard_normal((T, N))
    churn = RNG.uniform(0.10, 0.60, N)

    # 時變 AUM(成長基金:log 隨機漫步)→ 讓 organic 正規化有意義
    logA0 = RNG.normal(0, 1.0, N)
    steps = RNG.normal(0.0005, 0.02, (T, N))
    AUM = np.exp(logA0[None, :] + np.cumsum(steps, axis=0)) * 1e9
    AUM_lag = np.vstack([AUM[0][None, :], AUM[:-1]])   # AUM_{t-1}

    organic_clean = s + SF*RNG.standard_normal((T, N))               # position-diff(當沖免疫)
    turb = CHURN_BASE + CHURN_K*churn
    organic_turn  = s + turb[None, :]*RNG.standard_normal((T, N))     # turnover(含churn)
    organic_leaky = s + PEEK*r_next + 0.5*RNG.standard_normal((T, N)) # 洩漏

    def fis(org):  # 有機流→NetFlow(*AUM_lag)→還原/AUM_lag→穩健z→tanh
        net = org*AUM_lag
        return 100*np.tanh(robust_z(net/AUM_lag)/KAPPA)
    def fis_raw(org):  # 對『美元 NetFlow』直接做z(未除AUM)
        return 100*np.tanh(robust_z(org*AUM_lag)/KAPPA)

    FIS, FIS_turn, FIS_leaky = fis(organic_clean), fis(organic_turn), fis(organic_leaky)
    RAW = fis_raw(organic_clean)

    ic = daily_ic(FIS, r_next)
    res = {"clean": ic_stats(ic), "raw": ic_stats(daily_ic(RAW, r_next)),
           "turn": ic_stats(daily_ic(FIS_turn, r_next)),
           "leaky": ic_stats(daily_ic(FIS_leaky, r_next))}
    rn = r_next.copy()
    for t in range(T): rn[t] = RNG.permutation(rn[t])
    res["null"] = ic_stats(daily_ic(FIS, rn))
    cut = int(T*0.6)
    res["is"], res["oos"] = ic_stats(ic[:cut]), ic_stats(ic[cut:])
    lo = churn < np.median(churn)
    res["dq_lo"] = ic_stats(daily_ic(FIS_turn[:, lo], r_next[:, lo]))
    res["dq_hi"] = ic_stats(daily_ic(FIS_turn[:, ~lo], r_next[:, ~lo]))

    mask = np.isfinite(FIS) & (np.abs(FIS) > 20)
    hit = (np.sign(FIS[mask]) == np.sign(r_next[mask])); hr, nh = hit.mean(), hit.size
    hz = (hr-0.5)/np.sqrt(0.25/nh)
    res["hit"] = dict(rate=hr, z=hz, p=2*(1-norm.cdf(abs(hz))))

    # 流量顯著:FIS 分位 → 次日『帶號』報酬 long-short(top-bottom decile)單調性
    ls = []
    for t in range(W-1, T):
        f, rr = FIS[t], r_next[t]
        if not np.all(np.isfinite(f)): continue
        q = rankdata(f)/len(f)
        ls.append(rr[q >= 0.8].mean() - rr[q <= 0.2].mean())
    ls = np.array(ls); tt = ttest_1samp(ls, 0)
    res["ls"] = dict(spread=ls.mean(), t=tt.statistic, p=tt.pvalue)
    return res

keys = ["clean", "raw", "turn", "leaky", "null", "is", "oos", "dq_lo", "dq_hi"]
agg = {k: [] for k in keys}; aggt = {k: [] for k in keys}
hit_r, hit_p, ls_s, ls_p = [], [], [], []
gates = ["IC>0 顯著(方向)", "命中率>50% 顯著", "流量 long-short 顯著",
         "leaky>>clean(洩漏偵測)", "OOS 維持", "去噪 diff>turnover"]
gp = {g: 0 for g in gates}
null_fp = 0        # null 假陽性(p<.05)次數 → 應 ~5%
dq_lo_all, dq_hi_all, org_all, raw_all = [], [], [], []

for _ in range(SIMS):
    r = one_sim()
    for k in keys: agg[k].append(r[k]["ic"]); aggt[k].append(r[k]["t"])
    hit_r.append(r["hit"]["rate"]); hit_p.append(r["hit"]["p"])
    ls_s.append(r["ls"]["spread"]); ls_p.append(r["ls"]["p"])
    gp["IC>0 顯著(方向)"]        += (r["clean"]["ic"] > 0 and r["clean"]["p"] < 0.05)
    gp["命中率>50% 顯著"]        += (r["hit"]["rate"] > 0.5 and r["hit"]["p"] < 0.05)
    gp["流量 long-short 顯著"]    += (r["ls"]["spread"] > 0 and r["ls"]["p"] < 0.05)
    gp["leaky>>clean(洩漏偵測)"]  += (r["leaky"]["ic"] > r["clean"]["ic"] + 0.05)
    gp["OOS 維持"]              += (r["oos"]["ic"] > 0 and r["oos"]["p"] < 0.05)
    gp["去噪 diff>turnover"]     += (r["clean"]["ic"] > r["turn"]["ic"])
    null_fp += (r["null"]["p"] < 0.05)
    dq_lo_all.append(r["dq_lo"]["ic"]); dq_hi_all.append(r["dq_hi"]["ic"])
    org_all.append(r["clean"]["ic"]); raw_all.append(r["raw"]["ic"])

def ms(a):
    a = np.array([x for x in a if np.isfinite(x)]); return a.mean(), a.std(ddof=1)

print("="*74)
print("VIA FIS 方法驗證 · 受控回測 v2 (Monte-Carlo)")
print(f"  N={N} · T={T}日 · 窗={W} · κ={KAPPA} · sims={SIMS} · seed 固定 · 時變AUM")
print("="*74)
lab = {"clean":"乾淨FIS(diff)","raw":"原始$NetFlow(未除AUM)","turn":"turnover(含churn)",
       "leaky":"洩漏(偷看未來)","null":"NULL(打亂r)","is":"樣本內","oos":"樣本外OOS",
       "dq_lo":"低churn子集","dq_hi":"高churn子集"}
print("\n【IC 電池】跨截面 Spearman Rank-IC(mean±sd over sims)")
for k in keys:
    m, sdv = ms(agg[k]); tm, _ = ms(aggt[k])
    print(f"  {lab[k]:<22} IC={m:+.4f} ± {sdv:.4f}   t≈{tm:+.1f}")
hr_m, hr_s = ms(hit_r); ls_m, ls_s2 = ms(ls_s)
print(f"\n【方向】命中率(|FIS|>20)= {hr_m*100:.2f}% ± {hr_s*100:.2f}%")
print(f"【流量】FIS decile long-short 次日帶號報酬 = {ls_m:+.4f} ± {ls_s2:.4f}  (p<.05 於 {sum(p<0.05 for p in ls_p)}/{SIMS} sims)")
print("\n【證偽/穩健閘】通過率(over sims)")
for g in gates:
    c = gp[g]; bar = "█"*int(round(c/SIMS*20))
    tag = "PASS" if c == SIMS else (str(round(c/SIMS*100))+"%")
    print(f"  {tag:>5}  {g:<22} {bar} {c}/{SIMS}")
# 校準 + 發現(誠實,不列 pass/fail 硬閘)
fp_rate = null_fp/SIMS*100
dq_lo_m = np.nanmean(dq_lo_all); dq_hi_m = np.nanmean(dq_hi_all)
org_m = np.nanmean(org_all); raw_m = np.nanmean(raw_all)
print("\n【校準】null 假陽性率 = %.1f%% (理想≈5%%;過高=閘漏、過低=保守)" % fp_rate)
print("【DQ】低churn IC=%.4f > 高churn IC=%.4f → churn 稀釋訊號,可用 1-churn 折權" % (dq_lo_m, dq_hi_m))
print("【發現】organic(÷AUM) IC=%.4f ≈ 原始$NetFlow IC=%.4f" % (org_m, raw_m))
print("        → 每名滾動穩健z已提供尺度不變;÷AUM 之價值在可解釋性/pooled-z,非此處截面IC驅動。")
allp = all(v == SIMS for v in gp.values())
calib = (fp_rate <= 10.0); dqok = (dq_lo_m > dq_hi_m)
print("\n" + "="*74)
print("  核心 6 閘 = %s | null 校準 = %s | DQ 折權有效 = %s" %
      ("ALL PASS" if allp else "CHECK", "OK(%.1f%%)"%fp_rate if calib else "CHECK", "OK" if dqok else "CHECK"))
verdict = allp and calib and dqok
print("  總判定:%s — FIS 估計子顯著抓方向+流量強度,證偽閘正確作動(null崩解/洩漏偵測/OOS/去噪)。" %
      ("VALIDATED ✓" if verdict else "CHECK"))
print("  邊界:沙盒為受控 DGP 驗『估計子+閘』;接 TWSE T86/ETF創贖/CFTC COT 真值即為真回測。")
print("="*74)
