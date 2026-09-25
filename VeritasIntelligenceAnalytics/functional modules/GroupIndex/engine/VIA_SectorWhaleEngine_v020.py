# -*- coding: utf-8 -*-
"""
VIA_SectorWhaleEngine_v020.py — 準確率改良 + 完整回測(準確率/波動性)
=========================================================
三項改良 (每項皆有結構理由, 非調參):
  [I1] MAD 穩健 z: median/MAD 取代 mean/std
       理由: 大戶流厚尾, 極端日污染 std => z 被壓縮 (與 Spearman
       取代 Pearson 同一哲學: 排序穩健性優先)
  [I2] 遲滯偵測 (Hysteresis): 進場 z>1.5 連3日, 出場 z<0.5
       理由: 事件中段 z 回落至 1.2 不代表事件結束; 單一門檻
       造成事件內訊號斷裂 => 召回被自己的門檻切碎
  [I3] 週錨貝氏融合: TDCC 週錨方向一致 => 有效門檻 x0.8;
       方向相反 => x1.3
       理由: 兩獨立證據源同向, 後驗信度上升, 證據門檻應降
回測: 10 種子 x (v0.1基線 vs v0.2改良) 成對比較
  準確率: Recall / FPR / Precision / F1 (日級, 模糊窗±3)
  波動性: 跨種子IQR / 訊號翻轉率 / 事件內平均連續長度 / 非事件期z雜訊
EXIT: 改良版須在召回中位數上勝基線且FPR不惡化, 否則禁交付
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

SEEDS=[7,11,23,37,53,71,97,113,151,20260725]
N_DAYS=300
SSOT={"schema_version":"0.2.0",
 "sector_registry":{
   "被動元件":["2327國巨","2492華新科","3026禾伸堂","2478大毅","6173信昌電"],
   "CPO":["3363上詮","3450聯鈞","4977眾達KY","4979華星光","6442光聖","3163波若威"],
   "PCB":["3037欣興","2313華通","4958臻鼎KY","6213聯茂","2383台光電","6274台燿"],
   "ABF":["3037欣興","8046南電","3189景碩"]},
 "v01":{"z_kind":"std","enter":1.5,"exit":1.5,"persist":3,"fusion":False},
 "v02":{"z_kind":"mad","enter":1.5,"exit":0.5,"persist":3,"fusion":True},
 "fusion_mult":{"agree":0.8,"oppose":1.3},"fuzzy":3,"lag":10}

# ---------------- 世界 (同 v0.1 構造) ----------------
def gen_world(seed,n=N_DAYS):
    rng=np.random.default_rng(seed)
    dates=pd.bdate_range(end="2026-07-24",periods=n)
    stocks=sorted({s for m in SSOT["sector_registry"].values() for s in m})
    mcap={s:rng.uniform(5e10,8e11) for s in stocks}
    CPO_EV=(150,175); PCB_EV=(220,245)
    rows=[]
    for i,d in enumerate(dates):
        for s in stocks:
            big=rng.normal(0,1.2e8); inst=rng.normal(0,0.9e8)
            gov=rng.normal(0,0.15e8); dayt=abs(rng.normal(0.3e8,0.1e8))
            if s in SSOT["sector_registry"]["CPO"] and CPO_EV[0]<=i<CPO_EV[1]:
                big+=rng.normal(2.2e8,0.5e8)
            if s in SSOT["sector_registry"]["PCB"] and PCB_EV[0]<=i<PCB_EV[1]:
                big-=rng.normal(2.0e8,0.5e8); inst+=rng.normal(0.8e8,0.3e8)
            rows.append((d.date(),s,big,inst,gov,dayt,mcap[s]))
    df=pd.DataFrame(rows,columns=["date","stock","big","inst","gov",
                                  "daytrade","mcap"])
    wk=[]
    for i,d in enumerate(dates):
        if d.dayofweek==4:
            for sec,mem in SSOT["sector_registry"].items():
                dv=rng.normal(0,0.05)
                if sec=="CPO" and CPO_EV[0]<=i<CPO_EV[1]: dv+=0.20
                if sec=="PCB" and PCB_EV[0]<=i<PCB_EV[1]: dv-=0.18
                wk.append((d.date(),sec,dv))
    wkdf=pd.DataFrame(wk,columns=["date","sector","anchor"])
    return df,wkdf,{"CPO":("ACCUM",CPO_EV),"PCB":("DIST",PCB_EV)}

# ---------------- 因子/合成 ----------------
def zscore(s,kind,w=60,mp=20,lag=10):
    b=s.shift(lag)
    if kind=="std":
        r=b.rolling(w,min_periods=mp); return (s-r.mean())/r.std()
    med=b.rolling(w,min_periods=mp).median()
    mad=(b-med).abs().rolling(w,min_periods=mp).median()
    return (s-med)/(1.4826*mad)

def sector_flows(df):
    d=df.copy()
    d["big_adj"]=d["big"]-np.sign(d["big"])*np.minimum(abs(d["big"]),d["daytrade"])
    d["whale"]=d["big_adj"]-d["inst"]-d["gov"]
    out={}
    for sec,mem in SSOT["sector_registry"].items():
        sub=d[d["stock"].isin(mem)].copy()
        sub["w"]=sub.groupby("date")["mcap"].transform(lambda x:x/x.sum())
        s=(sub["whale"]*sub["w"]).groupby(sub["date"]).sum()
        out[sec]=pd.DataFrame({"date":s.index,"flow":s.values})
    return out

def anchor_asof(wkdf,sec,dates):
    a=wkdf[wkdf["sector"]==sec].copy()
    a["eff"]=pd.to_datetime(a["date"])+pd.tseries.offsets.BDay(1)
    cal=pd.DataFrame({"date":pd.to_datetime(dates)})
    m=pd.merge_asof(cal,a[["eff","anchor"]].rename(columns={"eff":"date"})
                    .sort_values("date"),on="date",direction="backward")
    return m["anchor"].fillna(0).values

def detect(flow_z,anchor,cfg):
    n=len(flow_z); sig=np.zeros(n,int)   # +1吸籌 / -1出貨 / 0
    ec,xc,p=cfg["enter"],cfg["exit"],cfg["persist"]
    mult=np.ones(n)
    if cfg["fusion"]:
        for i in range(n):
            pass
    state=0; run=0
    for i in range(n):
        zv=flow_z[i]
        if np.isnan(zv): continue
        e=ec
        if cfg["fusion"] and anchor is not None and anchor[i]!=0:
            pass
        # 融合: 依方向調整有效進場門檻
        def eff(direction):
            if not cfg["fusion"] or anchor is None: return ec
            if anchor[i]*direction>0.02: return ec*SSOT["fusion_mult"]["agree"]
            if anchor[i]*direction<-0.02: return ec*SSOT["fusion_mult"]["oppose"]
            return ec
        if state==0:
            if zv>eff(+1): run=run+1 if run>0 else 1
            elif zv<-eff(-1): run=run-1 if run<0 else -1
            else: run=0
            if run>=p: state=1
            elif run<=-p: state=-1
        elif state==1:
            if zv<xc: state=0; run=0
        elif state==-1:
            if zv>-xc: state=0; run=0
        sig[i]=state
    return sig

# ---------------- 指標 ----------------
def fuzzy(t,k=3):
    return pd.Series(t).rolling(2*k+1,min_periods=1,center=True)\
             .max().astype(bool).values

def metrics(sig,truth_dir):
    """truth_dir: +1/-1/0 陣列"""
    t=truth_dir!=0; fz=fuzzy(t,SSOT["fuzzy"])
    hit=(sig==truth_dir)&t
    rec=float(hit[t].mean()) if t.sum() else np.nan
    fp=(sig!=0)&(~fz)
    fpr=float(fp.mean()) if (~fz).sum() else np.nan
    tp=int(hit.sum()); fpn=int(fp.sum())
    prec=tp/(tp+fpn) if tp+fpn else np.nan
    f1=2*prec*rec/(prec+rec) if prec and rec and (prec+rec)>0 else np.nan
    flips=int(np.abs(np.diff(sig)).clip(0,1).sum())
    runs=[]; cur=0
    for i in range(len(sig)):
        if t[i] and sig[i]==truth_dir[i]: cur+=1
        else:
            if cur: runs.append(cur); cur=0
    if cur: runs.append(cur)
    return dict(recall=rec,fpr=fpr,precision=prec,f1=f1,
                flip_rate=flips/len(sig),
                mean_run=float(np.mean(runs)) if runs else 0.0)

# ---------------- 回測 ----------------
def backtest(cfg):
    per_seed=[]
    for sd in SEEDS:
        df,wkdf,truth=gen_world(sd)
        flows=sector_flows(df)
        agg={"recall":[],"fpr":[],"precision":[],"f1":[],
             "flip_rate":[],"mean_run":[],"noise_z":[]}
        for sec,fl in flows.items():
            dates=fl["date"].values
            zc=zscore(fl["flow"],cfg["z_kind"]).values
            anc=anchor_asof(wkdf,sec,dates) if cfg["fusion"] else None
            sig=detect(zc,anc,cfg)
            td=np.zeros(len(dates),int)
            if sec in truth:
                kind,(a,b)=truth[sec]
                td[a:b]=1 if kind=="ACCUM" else -1
            m=metrics(sig,td)
            for k in ["fpr","flip_rate"]: agg[k].append(m[k])
            if sec in truth:
                for k in ["recall","precision","f1","mean_run"]:
                    agg[k].append(m[k])
            mask=~fuzzy(td!=0)
            agg["noise_z"].append(float(np.nanstd(zc[mask])))
        per_seed.append({k:np.nanmean(v) for k,v in agg.items()})
    dfm=pd.DataFrame(per_seed)
    summ={c:{"median":round(float(dfm[c].median()),3),
             "IQR":round(float(dfm[c].quantile(.75)-dfm[c].quantile(.25)),3)}
          for c in dfm.columns}
    return dfm,summ

def main():
    b_df,b=backtest(SSOT["v01"])
    i_df,imp=backtest(SSOT["v02"])
    R=[];T=lambda n,c,d="":R.append((n,"PASS" if c else "FAIL",d))
    T("A1 召回改善: v0.2中位>v0.1中位",
      imp["recall"]["median"]>b["recall"]["median"],
      f"{b['recall']['median']} -> {imp['recall']['median']}")
    T("A2 FPR不惡化 (v0.2<=v0.1+0.01)",
      imp["fpr"]["median"]<=b["fpr"]["median"]+0.01,
      f"{b['fpr']['median']} -> {imp['fpr']['median']}")
    T("A3 F1改善",imp["f1"]["median"]>b["f1"]["median"],
      f"{b['f1']['median']} -> {imp['f1']['median']}")
    T("A4 波動性: 召回跨種子IQR<=0.20",imp["recall"]["IQR"]<=0.20,
      f"IQR={imp['recall']['IQR']}")
    T("A5 訊號穩定: 翻轉率下降",
      imp["flip_rate"]["median"]<=b["flip_rate"]["median"],
      f"{b['flip_rate']['median']} -> {imp['flip_rate']['median']}")
    T("A6 事件內連續性提升 (mean_run)",
      imp["mean_run"]["median"]>=b["mean_run"]["median"],
      f"{b['mean_run']['median']} -> {imp['mean_run']['median']}")
    fails=sum(s=="FAIL" for _,s,_ in R)
    print("="*74)
    print(f"VIA SectorWhale v{SSOT['schema_version']} | 準確率改良回測 "
          f"| 10種子 成對比較 | SYNTHETIC(T4)")
    print("="*74)
    print("\n[改良項] I1 MAD穩健z  I2 遲滯偵測(進1.5/出0.5)  I3 週錨貝氏融合(x0.8/x1.3)")
    print("\n[準確率矩陣 (10種子中位數 / IQR)]")
    rows=[]
    for k in ["recall","fpr","precision","f1"]:
        rows.append([k,b[k]["median"],b[k]["IQR"],imp[k]["median"],imp[k]["IQR"]])
    print(pd.DataFrame(rows,columns=["指標","v0.1中位","v0.1 IQR",
          "v0.2中位","v0.2 IQR"]).to_string(index=False))
    print("\n[波動性矩陣]")
    rows=[]
    for k in ["flip_rate","mean_run","noise_z"]:
        rows.append([k,b[k]["median"],b[k]["IQR"],imp[k]["median"],imp[k]["IQR"]])
    print(pd.DataFrame(rows,columns=["指標","v0.1中位","v0.1 IQR",
          "v0.2中位","v0.2 IQR"]).to_string(index=False))
    print("\n[測試矩陣]")
    for n,s,d in R: print(f"  {s:4s} | {n}"+(f"  [{d}]" if d else ""))
    print("\n"+("✅ 全數通過 EXIT=0" if fails==0 else f"❌ {fails}項失敗 EXIT=1"))
    sys.exit(0 if fails==0 else 1)

if __name__=="__main__": main()
