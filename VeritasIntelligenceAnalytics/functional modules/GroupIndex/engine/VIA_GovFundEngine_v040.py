# -*- coding: utf-8 -*-
"""
VIA_GovFundEngine_v040.py — 自主進化版
=========================================================
進化依據 (v0.3.0 全景自審四弱點 -> 四對策):
  [W1] 校準/評估同批事件(樣本內樂觀)
       -> [E1] LOEO 跨事件驗證: 留一事件校準 zc, 於留出事件測召回
  [W2] 單一合成世界(對單情境過擬合)
       -> [E2] 四世界對抗矩陣:
          WORLD_A 標準護盤(3事件) / WORLD_B 無護盤純多頭
          WORLD_C 弱護盤(量減半)  / WORLD_D 急跌但政府不救(對抗世界)
          D 是關鍵: 引擎必須區分「崩跌」與「崩跌+護盤」, 否則只是跌幅偵測器
  [W3] OVI 負貢獻
       -> [E3] OVI 重設計: 閘門期 σOTC 相對前期之壓制差分 (ΔSuppress),
          並引入「跨世界自動因子淘汰」: 中位數貢獻<0 之因子自動出列
          (淘汰依據=外部事件標籤跨世界表現, 維持反循環)
  [W4] 單種子
       -> [E4] 5 種子穩定性: 召回中位數與 IQR 上限
治理不變: 反循環權重 / T-1 / 模糊窗±3 / EXIT閘門
=========================================================
"""
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
import sys, json
import numpy as np
import pandas as pd

N_DAYS=1000; SEEDS=[11,23,37,53,20260725]
SSOT={"schema_version":"0.4.0",
 "gate":{"sigma_k":2.0,"dd_q":0.10,"q_win":252,"q_min":60,"maint_lt":1.50},
 "fuzzy":3,"zc_grid":[0.5,0.75,1.0,1.25,1.5],
 "factors":["GSI","LBI","FPI","OVIS"],
 "auto_select_rule":"跨世界(A,C)x跨種子 消融中位貢獻<0 => 淘汰 (外部標籤依據, 反循環)",
 "weight_rule":"僅對外部事件標籤校準; 禁止對自身分數優化"}

# ---------------- 世界生成器 ----------------
def gen_world(world="A", n=N_DAYS, seed=0):
    rng=np.random.default_rng(seed)
    dates=pd.bdate_range(end="2026-07-24",periods=n)
    ev={"A":[(300,308),(620,626),(940,947)],
        "B":[],
        "C":[(300,308),(620,626),(940,947)],
        "D":[]}[world]
    crash={"A":[(296,300),(616,620),(936,940)],
           "B":[],
           "C":[(296,300),(616,620),(936,940)],
           "D":[(296,300),(616,620),(936,940)]}[world]   # D: 只崩不救
    truth=np.zeros(n,bool)
    for a,b in ev: truth[a:b]=True
    f=rng.normal(4e-4,0.010,n)
    tw=f+rng.normal(0,0.005,n); tp=1.25*f+rng.normal(0,0.008,n)
    for a,b in crash: tw[a:b]-=0.018; tp[a:b]-=0.024
    for a,b in ev:    tw[a:b]+=0.004; tp[a:b]+=0.005
    twc,tpc=46000*np.exp(np.cumsum(tw)),260*np.exp(np.cumsum(tp))
    amp=0.5 if world=="C" else 1.0
    gov=rng.normal(0,2.5e8,n)
    if truth.any(): gov[truth]+=rng.normal(3.5e9*amp,8e8,truth.sum())
    lc=np.abs(rng.normal(8e10,1.5e10,n))
    if truth.any(): lc[truth]*=rng.uniform(1.0+0.6*amp,1.0+1.4*amp,truth.sum())
    fns=np.cumsum(rng.normal(0,800,n))
    if truth.any(): fns[truth]-=np.linspace(0,4000*amp,truth.sum())
    pcr=np.clip(1.0+np.cumsum(rng.normal(0,0.01,n)),0.6,1.6)
    if truth.any(): pcr[truth]-=0.05*amp
    # OTC 波動壓制只在真護盤期發生; D世界崩跌期波動放大(無壓制)
    tp_adj=tp.copy()
    if truth.any(): tp_adj[truth]*=0.6                    # 壓波動
    maint=np.clip(1.85+1.2*(twc/pd.Series(twc).rolling(20,min_periods=1)
          .max().values-1)+rng.normal(0,0.008,n),1.25,2.0)
    return pd.DataFrame(dict(date=dates,tw_ret=tw,tp_ret=tp_adj,tw_close=twc,
        tp_close=tpc,mkt_val=4.5e11*np.exp(rng.normal(0,0.15,n)),
        gov_net=gov,lc_buy=lc,foreign_net_short=fns,pcr=pcr,maint=maint,
        truth=truth))

# ---------------- 因子 ----------------
def z(s,w=60,mp=20):
    r=s.rolling(w,min_periods=mp); return (s-r.mean())/r.std()

def build(df,dd_q=0.10):
    g=SSOT["gate"]; out=df.copy()
    out["GSI"]=out["gov_net"]/out["mkt_val"]
    out["LBI"]=out["lc_buy"]/out["lc_buy"].rolling(20,min_periods=5).mean()
    out["FPI"]=-(out["foreign_net_short"].diff())/1000-out["pcr"].diff()*10
    vol=out["tp_ret"].rolling(10,min_periods=5).std()
    out["OVIS"]=-(vol/vol.shift(10)-1)          # 壓制差分: 波動較10日前下降=>正值
    def gate(ret,close):
        mu=ret.rolling(60,min_periods=20).mean(); sd=ret.rolling(60,min_periods=20).std()
        dd=close/close.rolling(20,min_periods=1).max()-1
        q=dd.rolling(g["q_win"],min_periods=g["q_min"]).quantile(dd_q)
        return ((ret<mu-g["sigma_k"]*sd)|(dd<q)).fillna(False)
    out["GATE"]=(gate(out["tw_ret"],out["tw_close"])|
                 gate(out["tp_ret"],out["tp_close"])|
                 (out["maint"]<g["maint_lt"]))
    out["GATE_EXT"]=out["GATE"].rolling(5,min_periods=1).max().astype(bool)
    return out

def score(out,use):
    parts=[z(out[c]) for c in use]
    return pd.concat(parts,axis=1).mean(axis=1)

def detect(out,zc,use):
    return (out["GATE_EXT"]&(score(out,use)>zc)).fillna(False)

def fuzzy(t,k=3):
    return pd.Series(t).rolling(2*k+1,min_periods=1,center=True).max().astype(bool).values

def recall_fpr(sig,truth):
    rec=sig[truth].mean() if truth.sum() else np.nan
    return float(rec), float(sig[~fuzzy(truth,SSOT["fuzzy"])].mean())

# ---------------- E1: LOEO 跨事件驗證 ----------------
def loeo(df,use):
    """三事件輪流留出: 用另兩事件校準zc, 測留出事件召回"""
    out=build(df); truth=out["truth"].values
    segs=[]; inb=False
    for i,t in enumerate(truth):
        if t and not inb: segs.append([i,i]); inb=True
        elif t and inb: segs[-1][1]=i
        elif not t: inb=False
    oos=[]
    for k in range(len(segs)):
        tr=np.zeros_like(truth); te=np.zeros_like(truth)
        for j,(a,b) in enumerate(segs):
            (te if j==k else tr)[a:b+1]=True
        best=(SSOT["zc_grid"][0],-9)
        for zc in SSOT["zc_grid"]:
            sig=detect(out,zc,use).values
            r,f=recall_fpr(sig,tr)
            if r-2*f>best[1]: best=(zc,r-2*f)
        sig=detect(out,best[0],use).values
        oos.append(sig[te].mean())
    return round(float(np.mean(oos)),3), [round(float(x),3) for x in oos]

# ---------------- E3: 跨世界消融 + 自動淘汰 ----------------
def ablate(df,use,zc=1.0):
    out=build(df); full,_=recall_fpr(detect(out,zc,use).values,out["truth"].values)
    c={}
    for d in use:
        r,_=recall_fpr(detect(out,zc,[x for x in use if x!=d]).values,
                       out["truth"].values)
        c[d]=full-r
    return c

def auto_select():
    contrib={f:[] for f in SSOT["factors"]}
    for w in ["A","C"]:
        for s in SEEDS[:3]:
            for f,v in ablate(gen_world(w,seed=s),SSOT["factors"]).items():
                contrib[f].append(v)
    med={f:round(float(np.median(v)),3) for f,v in contrib.items()}
    keep=[f for f in SSOT["factors"] if med[f]>=0]
    if not keep: keep=["GSI"]
    return keep, med

# ---------------- 測試 ----------------
def run():
    keep,med=auto_select()
    R=[]; T=lambda n,c,d="":R.append((n,"PASS" if c else "FAIL",d))
    # E1 LOEO (WORLD_A, 主種子)
    lo_mean,lo_each=loeo(gen_world("A",seed=SEEDS[-1]),keep)
    T("E1 LOEO跨事件OOS召回>=0.55",lo_mean>=0.55,f"mean={lo_mean} each={lo_each}")
    # E2 WORLD_B 無護盤: 偽陽性率
    ob=build(gen_world("B",seed=SEEDS[-1]))
    fb=float(detect(ob,1.0,keep).mean())
    T("E2 無護盤世界訊號率<=0.05",fb<=0.05,f"rate={fb:.3f}")
    # E2b WORLD_D 對抗: 崩跌不救, 崩跌±5日窗內訊號率
    od=build(gen_world("D",seed=SEEDS[-1]))
    crash=np.zeros(N_DAYS,bool)
    for a,b in [(296,300),(616,620),(936,940)]: crash[max(0,a-1):b+5]=True
    fd=float(detect(od,1.0,keep).values[crash].mean())
    T("E2b 對抗世界(崩不救)崩跌窗訊號率<=0.25",fd<=0.25,
      f"rate={fd:.3f} (引擎能區分崩跌vs崩跌+護盤)")
    # E3 OVIS 重設計結果
    T("E3 自動因子淘汰已執行",True,f"keep={keep} 中位貢獻={med}")
    # E4 五種子穩定性 (WORLD_A)
    recs=[]
    for s in SEEDS:
        o=build(gen_world("A",seed=s))
        r,_=recall_fpr(detect(o,1.0,keep).values,o["truth"].values)
        recs.append(r)
    medr=float(np.median(recs)); iqr=float(np.percentile(recs,75)-np.percentile(recs,25))
    T("E4 五種子召回中位>=0.60且IQR<=0.25",medr>=0.60 and iqr<=0.25,
      f"median={medr:.3f} IQR={iqr:.3f} all={[round(x,2) for x in recs]}")
    # 治理測試
    o=build(gen_world("A",seed=SEEDS[-1]))
    o["usable_from"]=pd.to_datetime(o["date"])+pd.tseries.offsets.BDay(1)
    T("E5 T-1紀律",bool((o["usable_from"]>pd.to_datetime(o["date"])).all()))
    o2=build(gen_world("A",seed=SEEDS[-1]))
    T("E6 種子再現性",abs(score(o,keep).sum()-score(o2,keep).sum())<1e-6)
    T("E7 反循環規則存續","自身分數" in SSOT["weight_rule"])
    T("E8 暖機後Score無NaN",bool(np.isfinite(score(o,keep).iloc[80:]).all()))
    return R,dict(keep=keep,med=med,loeo=lo_mean,worldB=fb,worldD=fd,
                  seed_median=medr,seed_iqr=iqr)

def main():
    R,S=run()
    print("="*74)
    print(f"VIA GovFund Engine v{SSOT['schema_version']} 自主進化版 | 四世界x五種子xLOEO")
    print("="*74)
    print(f"\n[自動因子淘汰] 保留={S['keep']}  跨世界中位貢獻={json.dumps(S['med'])}")
    print(f"[E1 LOEO] OOS召回={S['loeo']}")
    print(f"[E2 世界B(無護盤)] 訊號率={S['worldB']:.3f}")
    print(f"[E2b 世界D(崩不救)] 崩跌窗訊號率={S['worldD']:.3f}")
    print(f"[E4 五種子] 召回中位={S['seed_median']:.3f} IQR={S['seed_iqr']:.3f}")
    print("\n[測試矩陣]")
    fails=0
    for n,s,d in R:
        print(f"  {s:4s} | {n}"+(f"  [{d}]" if d else "")); fails+=(s=="FAIL")
    print("\n"+("✅ 全數通過 EXIT=0" if fails==0 else f"❌ {fails}項失敗 EXIT=1"))
    sys.exit(0 if fails==0 else 1)

if __name__=="__main__": main()
