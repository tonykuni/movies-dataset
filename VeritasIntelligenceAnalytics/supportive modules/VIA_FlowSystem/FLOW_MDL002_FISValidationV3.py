# -*- coding: utf-8 -*-
"""VIA FIS 驗證 harness v3 — PROVE THE LOGIC WORKS + MATRIX RESULTS.
新增三組實驗(接續 v2 已驗證的方向/強度/證偽閘):
  E1 多方法標準化集成:robust-z-tanh / plain-z / cross-sectional rank → ensemble+同號過濾
  E2 金額推估 vs 實際金額:implied = ETF淨流/覆蓋率;靜態 vs 動態覆蓋率;依覆蓋率分桶誤差(驗 coverage floor)
  E3 多源 fusion:ETF流 + positioning(COT型) → 實測IC加權融合 > 任一單源(OOS)
受控 DGP(沙盒無行情真值);同介面換真值即真回測。輸出 Visual Lock matrix HTML 報告。
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
import numpy as np, io, os, json, datetime
from scipy.stats import rankdata, norm, ttest_1samp
from numpy.lib.stride_tricks import sliding_window_view

RNG = np.random.default_rng(20260706)
N, T, W, KAPPA, SIMS = 40, 600, 100, 1.5, 40
PHI, G, SE = 0.90, 0.35, 0.90

def daily_ic(sig, fwd):
    out=[]
    for t in range(sig.shape[0]):
        a,b=sig[t],fwd[t]; m=np.isfinite(a)&np.isfinite(b)
        if m.sum()<5: out.append(np.nan); continue
        ra=rankdata(a[m]); rb=rankdata(b[m]); ra-=ra.mean(); rb-=rb.mean()
        d=np.sqrt((ra*ra).sum()*(rb*rb).sum()); out.append((ra*rb).sum()/d if d>0 else np.nan)
    return np.array(out)

def ic_stats(ics):
    ics=ics[np.isfinite(ics)]
    if len(ics)==0: return dict(ic=np.nan,t=np.nan,p=np.nan)
    mu,sd=ics.mean(),ics.std(ddof=1); ir=mu/sd if sd>0 else np.nan
    t=ir*np.sqrt(len(ics)) if sd>0 else np.nan
    return dict(ic=mu,t=t,p=2*(1-norm.cdf(abs(t))) if np.isfinite(t) else np.nan)

def robust_z(panel):
    z=np.full_like(panel,np.nan)
    win=sliding_window_view(panel,W,axis=0)
    med=np.median(win,axis=2); mad=np.median(np.abs(win-med[:,:,None]),axis=2)
    sd=1.4826*mad; z[W-1:,:]=np.where(sd>0,(panel[W-1:,:]-med)/sd,0.0)
    return z

def plain_z(panel):
    z=np.full_like(panel,np.nan)
    win=sliding_window_view(panel,W,axis=0)
    mu=win.mean(axis=2); sd=win.std(axis=2,ddof=1)
    z[W-1:,:]=np.where(sd>0,(panel[W-1:,:]-mu)/sd,0.0)
    return np.clip(z,-6,6)

def xs_rank(panel):
    z=np.full_like(panel,np.nan)
    for t in range(panel.shape[0]):
        r=rankdata(panel[t]); z[t]=(r-r.mean())/(r.std(ddof=1)+1e-9)
    z[:W-1,:]=np.nan
    return z

def one_sim():
    # latent 真流訊號
    s=np.zeros((T,N)); s[0]=RNG.standard_normal(N)
    for t in range(1,T): s[t]=PHI*s[t-1]+np.sqrt(1-PHI**2)*RNG.standard_normal(N)
    s=(s-s.mean(1,keepdims=True))/(s.std(1,keepdims=True)+1e-9)
    r_next=G*s+SE*RNG.standard_normal((T,N))

    # 市值 + 真實「全市場總流」(此為金額真值,實務不可觀測、僅回測用)
    mcap=np.exp(RNG.normal(0,1.0,N))*1e11
    actual_flow=(0.7*s+0.3*RNG.standard_normal((T,N)))*mcap[None,:]*0.001  # 實際指數總流$

    # 覆蓋率:各名 3%–11%,帶趨勢漂移(成長基金,600天可+40–80%);觀測 AUM = cov*mcap*(1+噪)
    cov0=RNG.uniform(0.03,0.11,N)
    drift=np.cumsum(RNG.normal(0.0008,0.004,(T,N)),axis=0)   # 趨勢+隨機漫步
    cov_true=np.clip(cov0[None,:]*np.exp(drift),0.015,0.30)
    # ETF 淨流 = 覆蓋率×實際總流 + 固定美元級特有噪(單一機構調倉);implied 誤差=eps/cov → 1/cov 放大
    flow_scale=mcap[None,:]*0.001
    eps=0.20*flow_scale*RNG.standard_normal((T,N))
    etf_flow=cov_true*actual_flow+eps
    # basket:每名 3 檔 ETF(獨立特有噪),Σflow/Σcov → 噪聲 √3 抵消
    cov3=cov_true[None,:,:]*RNG.uniform(0.6,1.4,(3,1,N))
    eps3=0.20*flow_scale[None,:,:]*RNG.standard_normal((3,T,N))
    etf3=cov3*actual_flow[None,:,:]+eps3
    implied_basket=etf3.sum(0)/np.clip(cov3.sum(0),1e-4,None)
    aum_obs=cov_true*mcap[None,:]*(1+0.03*RNG.standard_normal((T,N)))  # 可觀測 AUM

    # ---- E2 金額推估:implied = etf_flow / coverage_est ----
    cov_static=cov0[None,:]*np.ones((T,N))                    # 靜態(上線日估,會過期)
    cd=aum_obs/mcap[None,:]                                   # 動態(每日 AUM/市值,5日平滑)
    k=np.ones(5)/5.0
    cov_dynamic=np.vstack([np.convolve(cd[:,j],k,mode="same") for j in range(N)]).T
    implied_static=etf_flow/np.clip(cov_static,1e-4,None)
    implied_dynamic=etf_flow/np.clip(cov_dynamic,1e-4,None)
    def amt_metrics(implied, actual):
        m=np.isfinite(implied)&np.isfinite(actual)
        c=np.corrcoef(implied[m].ravel(),actual[m].ravel())[0,1]
        denom=np.abs(actual[m]); denom=np.where(denom<1e6,1e6,denom)
        mape=np.median(np.abs(implied[m]-actual[m])/denom)
        return c,mape
    cS,mS=amt_metrics(implied_static,actual_flow); cD,mD=amt_metrics(implied_dynamic,actual_flow)
    cB,mB=amt_metrics(implied_basket,actual_flow)
    # 覆蓋率分桶誤差(coverage floor 驗證)
    lo=cov0<0.05; hi=cov0>=0.05
    _,m_lo=amt_metrics(implied_dynamic[:,lo],actual_flow[:,lo]); _,m_hi=amt_metrics(implied_dynamic[:,hi],actual_flow[:,hi])

    # ---- E1 多方法標準化 ----
    organic=etf_flow/np.roll(aum_obs,1,axis=0); organic[0]=np.nan
    f_tanh=100*np.tanh(robust_z(organic)/KAPPA)
    f_z   =100*np.tanh(plain_z(organic)/KAPPA)
    f_rank=100*np.tanh(xs_rank(organic)/KAPPA)
    ens=(f_tanh+f_z+f_rank)/3.0
    same=(np.sign(f_tanh)==np.sign(f_z))&(np.sign(f_z)==np.sign(f_rank))
    agree=np.where(same,ens,0.0)   # 同號過濾:三法不同向 → 無效訊號(Ensemble 規則)
    ics={k:ic_stats(daily_ic(v,r_next)) for k,v in
         dict(tanh=f_tanh,z=f_z,rank=f_rank,ens=ens).items()}
    # agreement:只在有效訊號日/名上算命中率
    mask=np.isfinite(agree)&(np.abs(agree)>20)
    hit_ag=(np.sign(agree[mask])==np.sign(r_next[mask])).mean() if mask.sum()>0 else np.nan
    mask_all=np.isfinite(f_tanh)&(np.abs(f_tanh)>20)
    hit_single=(np.sign(f_tanh[mask_all])==np.sign(r_next[mask_all])).mean()

    # ---- E3 多源 fusion(實測IC加權)----
    srcA=organic                                              # ETF 流(較準)
    posB=0.6*s+1.8*RNG.standard_normal((T,N))                 # positioning/COT 型(較噪)
    fA=100*np.tanh(robust_z(srcA)/KAPPA); fB=100*np.tanh(robust_z(posB)/KAPPA)
    cut=int(T*0.6)
    icA_tr=ic_stats(daily_ic(fA[:cut],r_next[:cut]))["ic"]
    icB_tr=ic_stats(daily_ic(fB[:cut],r_next[:cut]))["ic"]
    wA=max(icA_tr,0)/max(icA_tr+icB_tr,1e-9); wB=1-wA
    fuse=wA*fA+wB*fB
    icA_oos=ic_stats(daily_ic(fA[cut:],r_next[cut:]))["ic"]
    icB_oos=ic_stats(daily_ic(fB[cut:],r_next[cut:]))["ic"]
    icF_oos=ic_stats(daily_ic(fuse[cut:],r_next[cut:]))["ic"]

    # 強度 long-short(沿 v2)
    ls=[]
    for t in range(W,T):
        f=f_tanh[t]
        if (not np.all(np.isfinite(f))) or np.std(f)<1e-9: continue
        q=rankdata(f)/len(f)
        top=r_next[t][q>=0.8]; bot=r_next[t][q<=0.2]
        if top.size==0 or bot.size==0: continue
        ls.append(top.mean()-bot.mean())
    ls=np.array(ls); tt=ttest_1samp(ls,0)

    return dict(ics=ics,hit_single=hit_single,hit_agree=hit_ag,
                amt=dict(cS=cS,mS=mS,cD=cD,mD=mD,cB=cB,mB=mB,m_lo=m_lo,m_hi=m_hi),
                fuse=dict(A=icA_oos,B=icB_oos,F=icF_oos,wA=wA),
                ls=dict(spread=ls.mean(),p=tt.pvalue))

# ---------- Monte-Carlo ----------
acc={k:[] for k in ["tanh","z","rank","ens"]}
hits_s,hits_a=[],[]; amt=[]; fu=[]; lss=[]
gates={"方向IC>0顯著(tanh)":0,"多方法皆有效(z/rank IC>0)":0,"Ensemble≥最弱單法":0,
       "同號過濾命中率≥單法":0,"basket金額優於單ETF(MAPE)":0,"動態MAPE≤靜態":0,
       "低覆蓋率誤差>高覆蓋率(floor成立)":0,"fusion OOS≥最佳單源-1%":0,"強度long-short顯著":0}
for _ in range(SIMS):
    r=one_sim()
    for k in acc: acc[k].append(r["ics"][k]["ic"])
    hits_s.append(r["hit_single"]); hits_a.append(r["hit_agree"])
    amt.append(r["amt"]); fu.append(r["fuse"]); lss.append(r["ls"])
    gates["方向IC>0顯著(tanh)"]        +=(r["ics"]["tanh"]["ic"]>0 and r["ics"]["tanh"]["p"]<0.05)
    gates["多方法皆有效(z/rank IC>0)"]  +=(r["ics"]["z"]["ic"]>0 and r["ics"]["rank"]["ic"]>0)
    gates["Ensemble≥最弱單法"]         +=(r["ics"]["ens"]["ic"]>=min(r["ics"]["tanh"]["ic"],r["ics"]["z"]["ic"],r["ics"]["rank"]["ic"]))
    gates["同號過濾命中率≥單法"]        +=(np.isfinite(r["hit_agree"]) and r["hit_agree"]>=r["hit_single"]-0.005)
    gates["basket金額優於單ETF(MAPE)"]+=(r["amt"]["mB"]<r["amt"]["mD"])
    gates["動態MAPE≤靜態"]             +=(r["amt"]["mD"]<=r["amt"]["mS"]+1e-12)
    gates["低覆蓋率誤差>高覆蓋率(floor成立)"]+=(r["amt"]["m_lo"]>r["amt"]["m_hi"])
    gates["fusion OOS≥最佳單源-1%"]     +=(r["fuse"]["F"]>=max(r["fuse"]["A"],r["fuse"]["B"])-0.01)
    gates["強度long-short顯著"]         +=(r["ls"]["spread"]>0 and r["ls"]["p"]<0.05)

def ms(a):
    a=np.array([x for x in a if np.isfinite(x)]); return a.mean(),a.std(ddof=1)

res={}
for k in acc: res[k]=ms(acc[k])
hs=ms(hits_s); ha=ms(hits_a)
cS=ms([a["cS"] for a in amt]); cD=ms([a["cD"] for a in amt])
mS=ms([a["mS"] for a in amt]); mD=ms([a["mD"] for a in amt])
mlo=ms([a["m_lo"] for a in amt]); mhi=ms([a["m_hi"] for a in amt])
fA=ms([f["A"] for f in fu]); fB=ms([f["B"] for f in fu]); fF=ms([f["F"] for f in fu])
wA=ms([f["wA"] for f in fu]); lsm=ms([l["spread"] for l in lss])

print("="*76)
print("VIA FIS 驗證 v3 · 多方法/金額收斂/多源fusion · sims=%d N=%d T=%d"%(SIMS,N,T))
print("="*76)
print("\n[E1 多方法標準化 IC]")
for k,lab in [("tanh","robust-z tanh"),("z","plain-z"),("rank","xs-rank"),("ens","Ensemble(3法)")]:
    print("  %-16s IC=%+.4f ± %.4f"%(lab,*res[k]))
print("  命中率 單法=%.2f%%  同號過濾=%.2f%%"%(hs[0]*100,ha[0]*100))
print("\n[E2 金額推估 vs 實際金額]")
cB=ms([a["cB"] for a in amt]); mB=ms([a["mB"] for a in amt])
print("  corr(implied,actual)  靜態=%.3f  動態=%.3f  basket=%.3f"%(cS[0],cD[0],cB[0]))
print("  Median APE            靜態=%.3f  動態=%.3f  basket(3ETF)=%.3f"%(mS[0],mD[0],mB[0]))
print("  動態MAPE 依覆蓋率分桶  <5%%: %.3f   ≥5%%: %.3f  (floor 依據)"%(mlo[0],mhi[0]))
print("\n[E3 多源 fusion OOS IC]")
print("  ETF流=%.4f  positioning=%.4f  fusion=%.4f (wA≈%.2f)"%(fA[0],fB[0],fF[0],wA[0]))
print("\n[強度] long-short=%.4f"%lsm[0])
print("\n[GATES]")
allp=True
for g,c in gates.items():
    tag="PASS" if c==SIMS else "%d/%d"%(c,SIMS)
    if c<0.9*SIMS: allp=False
    print("  %-32s %s"%(g,tag))
print("\nVERDICT:", "LOGIC PROVEN ✓ (all gates ≥90%)" if allp else "CHECK")

# ---------- save results for HTML report ----------
out={"res":{k:[float(x) for x in v] for k,v in res.items()},
     "hit":{"single":[float(x) for x in hs],"agree":[float(x) for x in ha]},
     "amt":{"cS":float(cS[0]),"cD":float(cD[0]),"cB":float(cB[0]),"mS":float(mS[0]),
            "mD":float(mD[0]),"mB":float(mB[0]),"mlo":float(mlo[0]),"mhi":float(mhi[0])},
     "fuse":{"A":float(fA[0]),"B":float(fB[0]),"F":float(fF[0]),"wA":float(wA[0])},
     "ls":float(lsm[0]),
     "gates":{k:int(v) for k,v in gates.items()},"sims":SIMS,
     "verdict":"LOGIC PROVEN" if allp else "CHECK"}
json.dump(out,io.open("/home/claude/v3_results.json","w"),ensure_ascii=False,indent=1)
print("\nresults -> /home/claude/v3_results.json")
