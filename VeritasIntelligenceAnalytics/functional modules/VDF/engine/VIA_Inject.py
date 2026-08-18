#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_Inject — 第5步：把 VIA_VDF_Bridge 標準輸出 → 兩模板各自的資料結構並注入 HTML
   輸入：via_data_real.json（VIA_VDF_Bridge 產出，datasets: prices/institutional/nav_units/...）
   產出：
     equity_real.json  → window.VIA_REAL = { "<yf代碼>": {date,open,high,low,close,volume,
                          foreign_net,trust_net,dealer_net} }  （Equity Insight build() 用）
     etf_real.json     → { PERF:{meta:{dates,ytd_idx}, etfs:[{ticker,name,issuer,style,adj,aum,flow}]},
                          HOLD:{meta:{dates,names,sectors}, etfs:[{ticker,hold:[{h,s}]}]} }
   自算（免付費）：AUM=NAV*Units；NetFlow=ΔUnits*NAV。
   注入：--inject-equity <html> / --inject-etf <html> 會把對應 payload 以 <script> 注入，
         並掛 adapter（buildData 優先用 VIA_REAL；PERF/HOLD 用真值）。
   用法：
     py -3.11 VIA_Inject.py --real via_data_real.json --out-dir .            # 只產 JSON
     py -3.11 VIA_Inject.py --real via_data_real.json --inject-equity Equity.html --inject-etf ETF.html
     py -3.11 VIA_Inject.py --offline-demo --out-dir .                        # 合成 bridge 輸出測試
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
import sys, json, argparse, datetime
TODAY=datetime.date.today().isoformat()

def _axis(records, datef="date"):
    ds=sorted({r[datef] for r in records if r.get(datef)})
    return ds

def build_equity(real):
    """prices + institutional → per-symbol OHLCV + 法人淨買賣"""
    ds=real.get("datasets",{})
    prices=ds.get("prices",{}).get("records",[])
    inst=ds.get("institutional",{}).get("records",[])
    out={}
    # group prices by ticker
    byt={}
    for r in prices:
        tk=r.get("ticker") or r.get("yf") or r.get("code")
        if not tk: continue
        byt.setdefault(tk,[]).append(r)
    for tk,rows in byt.items():
        rows=sorted(rows,key=lambda x:x.get("date",""))
        def col(*ks):
            for k in ks:
                if any(k in r for r in rows): return [r.get(k) for r in rows]
            return None
        close=col("adj_close","close","adjclose")
        out[tk]={"date":[r.get("date") for r in rows],
                 "open":col("open","adj_open") or close,"high":col("high","adj_high") or close,
                 "low":col("low","adj_low") or close,"close":close,
                 "volume":col("volume","vol") or [None]*len(rows),
                 "foreign_net":[],"trust_net":[],"dealer_net":[]}
    # institutional → align by code+date (簡化：以代碼聚合到對應 ticker)
    instByCode={}
    for r in inst:
        cd=str(r.get("code") or r.get("ticker") or "")
        instByCode.setdefault(cd,{})[r.get("date")]= (r.get("foreign"),r.get("trust"),r.get("dealer"))
    for tk,o in out.items():
        code=tk.split(".")[0]
        m=instByCode.get(code,{})
        o["foreign_net"]=[(m.get(d,(None,None,None))[0]) for d in o["date"]]
        o["trust_net"]=[(m.get(d,(None,None,None))[1]) for d in o["date"]]
        o["dealer_net"]=[(m.get(d,(None,None,None))[2]) for d in o["date"]]
    return out

def build_etf(real):
    """prices(ETF) + nav_units → PERF(adj/aum/flow) ; holdings → HOLD"""
    ds=real.get("datasets",{})
    prices=ds.get("prices",{}).get("records",[])
    nav=ds.get("nav_units",{}).get("records",[])
    holds=ds.get("holdings",{}).get("records",[]) if "holdings" in ds else []
    # 共同日期軸（以 prices 為準）
    dates=_axis(prices)
    # adj per etf
    byt={}
    for r in prices:
        tk=r.get("ticker") or r.get("code")
        if tk: byt.setdefault(tk,{})[r.get("date")]=r.get("adj_close") or r.get("close")
    # nav/units → aum/flow per code
    navByCode={}
    for r in nav:
        navByCode.setdefault(str(r.get("code")),[]).append(r)
    def aum_flow(code):
        rows=sorted(navByCode.get(code,[]),key=lambda x:x.get("date",""))
        aum=[];flow=[];prevU=None
        amap={};fmap={}
        for r in rows:
            n=r.get("nav");u=r.get("units")
            a=(n*u/1e8) if (n and u) else None         # 億
            f=((u-prevU)*n/1e8) if (n and u and prevU is not None) else None
            amap[r.get("date")]=a;fmap[r.get("date")]=f;prevU=u
        return amap,fmap
    etfs=[]
    for tk,dmap in byt.items():
        code=tk.split(".")[0]
        amap,fmap=aum_flow(code)
        etfs.append({"ticker":tk,"name":code,"issuer":"","style":"",
            "adj":[dmap.get(d) for d in dates],
            "aum":[amap.get(d) for d in dates],
            "flow":[fmap.get(d) for d in dates]})
    # ytd_idx：當年第一個交易日
    ytd_idx=0
    if dates:
        y=dates[-1][:4]
        for i,d in enumerate(dates):
            if d[:4]==y: ytd_idx=i;break
    PERF={"meta":{"dates":dates,"ytd_idx":ytd_idx,"horizons":[1,5,10,20,60,120,240]},"etfs":etfs}
    # HOLD
    names={};sectors={};hbyt={}
    for r in holds:
        tk=r.get("etf") or r.get("ticker");h=str(r.get("stock") or r.get("h"))
        names[h]=r.get("name",h);sectors[h]=r.get("sector","")
        hbyt.setdefault(tk,{}).setdefault(h,{})[r.get("date")]=r.get("shares") or r.get("s")
    holds_etfs=[]
    for tk,hmap in hbyt.items():
        hl=[{"h":h,"s":[sm.get(d,0) for d in dates]} for h,sm in hmap.items()]
        holds_etfs.append({"ticker":tk,"hold":hl})
    HOLD={"meta":{"dates":dates,"names":names,"sectors":sectors},"etfs":holds_etfs}
    return {"PERF":PERF,"HOLD":HOLD}

def inject_html(path, var_js, marker_id):
    s=open(path,encoding="utf-8").read()
    block=f'<script id="{marker_id}">{var_js}</script>'
    # 移除舊注入
    import re
    s=re.sub(rf'<script id="{marker_id}">.*?</script>', '', s, flags=re.S)
    s=s.replace("</head>", block+"\n</head>") if "</head>" in s else s.replace("<body", block+"\n<body",1)
    open(path,"w",encoding="utf-8").write(s); return True

def offline_demo_real():
    # 合成一份 bridge 輸出：prices(2檔) + institutional + nav_units
    pr=[];inst=[];nav=[]
    for d in ["2026-06-02","2026-06-03","2026-06-04"]:
        pr+=[{"date":d,"ticker":"2330.TW","adj_close":1000,"open":995,"high":1010,"low":990,"volume":30000},
             {"date":d,"ticker":"00980A.TW","adj_close":15.2,"close":15.2}]
        inst+=[{"date":d,"code":"2330","foreign":12000,"trust":3000,"dealer":-500}]
        nav+=[{"date":d,"code":"00980A","nav":15.2,"units":1_000_000_000}]
    return {"datasets":{"prices":{"records":pr},"institutional":{"records":inst},"nav_units":{"records":nav}}}

def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--real");ap.add_argument("--offline-demo",action="store_true")
    ap.add_argument("--out-dir",default=".");ap.add_argument("--inject-equity");ap.add_argument("--inject-etf")
    a=ap.parse_args()
    real = offline_demo_real() if a.offline_demo else json.load(open(a.real,encoding="utf-8"))
    eq=build_equity(real); etf=build_etf(real)
    import os
    eqp=os.path.join(a.out_dir,"equity_real.json"); etfp=os.path.join(a.out_dir,"etf_real.json")
    open(eqp,"w",encoding="utf-8").write(json.dumps(eq,ensure_ascii=False))
    open(etfp,"w",encoding="utf-8").write(json.dumps(etf,ensure_ascii=False))
    res={"equity_symbols":list(eq.keys()),"etf_count":len(etf["PERF"]["etfs"]),
         "dates":len(etf["PERF"]["meta"]["dates"]),"outputs":[eqp,etfp]}
    if a.inject_equity:
        js="window.VIA_REAL="+json.dumps(eq,ensure_ascii=False)+";"
        inject_html(a.inject_equity, js, "via-real-equity"); res["injected_equity"]=a.inject_equity
    if a.inject_etf:
        js="window.VIA_ETF_REAL="+json.dumps(etf,ensure_ascii=False)+";"
        inject_html(a.inject_etf, js, "via-real-etf"); res["injected_etf"]=a.inject_etf
    sys.stdout.write(json.dumps(res,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
