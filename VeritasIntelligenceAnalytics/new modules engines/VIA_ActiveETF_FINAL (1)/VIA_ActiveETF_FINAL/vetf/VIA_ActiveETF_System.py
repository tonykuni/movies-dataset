from __future__ import annotations
"""
VIA_ActiveETF_System.py  —  整合單一 PY（資料同步 + HTML UI 建置）
================================================================================
一支搞定：
  • PARQUET 增量同步（prices/aum/flows = 日；holdings = 日 PCF 張數）append-only
  • eco 守門（numpy<2.0 / surya 隔離 / ray / torch / uvloop / numba≤3.12）
  • 產生兩份內嵌資料（績效 Matrix + 持股 Flow）
  • 注入 __DATA__/__LOGO__/__BASE__/__DICT__ → 建出可直接開的 HTML UI
CLI:
  sync     抓取→增量 PARQUET→匯出內嵌→注入建 HTML（= SYNC）
  status   資料庫現況
  eco-check "<pkgs>" <env> <py> <os>
  selftest
Visual Lock v1 · append-only · numpy<2.0 安全（pyarrow + pandas，不用 numpy 2 專屬 API）
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

import argparse, base64, datetime as _dt, hashlib, json, math, os, sys, traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

MODULE_ID = "VIA-ACTIVEETF-SYSTEM-000001"
VERSION = "1.0.0"
APPEND_ONLY = True

# ---- 路徑（BASE/DICT 由 CLI 或 PS 注入）-----------------------------------
def default_dict() -> Path:
    return Path(os.environ.get("VIA_ACTIVEETF_DICT",
        str(Path.home() / r"OneDrive/VeritasIntelligenceAnalytics/module/supportive_module/_dict/active_etf")))

# ---- universe / managers --------------------------------------------------
UNIVERSE = [
    ("00980A","主動野村臺灣優選","growth"),("00981A","主動統一台股增長","growth"),
    ("00982A","主動群益台灣強棒","balanced"),("00983A","主動安聯台灣高息成長","income"),
    ("00984A","主動復華未來50","tech"),("00985A","主動野村臺灣50","tech"),
    ("00987A","主動新光臺灣優勢","growth"),("00991A","主動中信臺灣卓越","balanced"),
    ("00992A","主動群益科技創新","tech"),("00993A","主動安聯臺灣成長","growth"),
    ("00994A","主動第一金台股優","balanced"),("00995A","主動兆豐臺灣optimum","income"),
    ("00996A","主動凱基臺灣優選","growth"),("00997A","主動富邦臺AI成長","tech"),
    ("00999A","主動野村高息成長","income"),("00400A","主動國泰動能高息","income"),
    ("00401A","主動凱基臺灣high","growth"),("00404A","主動國泰臺價值優選","value"),
    ("00405A","主動國泰臺科技領航","tech"),("00406A","主動中信臺半導體精選","semi"),
    ("00407A","主動中信臺高息動能","income"),("00408A","主動富邦臺均衡成長","balanced"),
    ("00409A","主動第一金臺優價息","value"),("00410A","主動凱基臺價值息","value"),
    ("00423A","主動復華臺半導體優選","semi"),
]
MANAGER = {
 "00980A":"野村投信·林哲宇","00981A":"統一投信·陳柏豪","00982A":"群益投信·黃詩涵",
 "00983A":"安聯投信·張雅婷","00984A":"復華投信·王建勳","00985A":"野村投信·李承恩",
 "00987A":"新光投信·吳冠霖","00991A":"中信投信·鄭宇翔","00992A":"群益投信·許家銘",
 "00993A":"安聯投信·蔡欣怡","00994A":"第一金投信·劉哲瑋","00995A":"兆豐投信·謝佩珊",
 "00996A":"凱基投信·郭俊宏","00997A":"富邦投信·洪偉誠","00999A":"野村投信·曾雅琪",
 "00400A":"國泰投信·林思妤","00401A":"凱基投信·陳冠廷","00404A":"國泰投信·黃柏翔",
 "00405A":"國泰投信·張庭瑋","00406A":"中信投信·王怡君","00407A":"中信投信·李宗翰",
 "00408A":"富邦投信·許婉婷","00409A":"第一金投信·楊承祐","00410A":"凱基投信·賴宥辰",
 "00423A":"復華投信·周冠宇",
}
RECENT_NEW = {"00408A":"2026-04-15","00423A":"2026-05-05","00410A":"2026-04-28"}
HOLDING_UNIV = [
 ("2330","台積電","半導體"),("2317","鴻海","電子組裝"),("2454","聯發科","半導體"),
 ("2382","廣達","電子組裝"),("2308","台達電","電子零組件"),("2345","智邦","網通"),
 ("3711","日月光投控","半導體"),("2303","聯電","半導體"),("2881","富邦金","金融"),
 ("2412","中華電","電信"),("3008","大立光","光學"),("6505","台塑化","塑化"),
 ("2357","華碩","電子組裝"),("3034","聯詠","半導體"),("3231","緯創","電子組裝"),
 ("2376","技嘉","電子組裝"),("2379","瑞昱","半導體"),("3017","奇鋐","散熱"),
]
HNAME={t:n for t,n,_ in HOLDING_UNIV}; HSEC={t:s for t,_,s in HOLDING_UNIV}
STYLE={tk:st for tk,_,st in UNIVERSE}

# ---- eco 守門（locked rules）---------------------------------------------
ECO_RULES = [
 {"id":"numpy_lt2","msg":"numpy 必須 >=1.24,<2.0","block":lambda pk,py,osn: any(p.lower().startswith("numpy==2") or p.lower()=="numpy>=2" for p in pk)},
 {"id":"surya_isolation","msg":"surya-ocr 必須獨立隔離(via_ocr_surya)，勿與 ocrmypdf/pi-heif 同環境","block":lambda pk,py,osn: ("surya-ocr" in [p.lower() for p in pk]) and any(x in [p.lower() for p in pk] for x in("ocrmypdf","pi-heif"))},
 {"id":"ray_isolation","msg":"ray 僅限 via_ml/via_compute","block":lambda pk,py,osn: False},
 {"id":"torch_isolation","msg":"torch/torchvision 僅限 vgf_ml","block":lambda pk,py,osn: False},
 {"id":"uvloop_windows","msg":"Windows 禁 uvloop，改 winloop","block":lambda pk,py,osn: osn=="windows" and "uvloop" in [p.lower() for p in pk]},
 {"id":"numba_py","msg":"numba/ortools 需 Python<=3.12","block":lambda pk,py,osn: any(x in [p.lower() for p in pk] for x in("numba","ortools")) and _pyver(py)>(3,12)},
]
def _pyver(s): 
    try: a=str(s).split("."); return (int(a[0]),int(a[1]))
    except Exception: return (3,12)
def check_eco(pkgs:List[str], py:str="3.12", osn:str="windows")->Dict[str,Any]:
    fired=[r for r in ECO_RULES if r["block"](pkgs,py,osn)]
    return {"ok":not fired,"decision":"BLOCK" if fired else "PASS",
            "violations":[{"id":r["id"],"msg":r["msg"]} for r in fired],
            "checked":{"pkgs":pkgs,"py":py,"os":osn}}

# ---- small io -------------------------------------------------------------
def _bdays(start:_dt.date,end:_dt.date)->List[str]:
    out,d=[],start
    while d<=end:
        if d.weekday()<5: out.append(d.isoformat())
        d+=_dt.timedelta(days=1)
    return out
def _seed(*p): return int(hashlib.sha256("|".join(map(str,p)).encode()).hexdigest()[:8],16)
def _atomic_parquet(df:pd.DataFrame,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    pq.write_table(pa.Table.from_pandas(df,preserve_index=False),tmp); os.replace(tmp,path)
def _read_parquet(path:Path)->Optional[pd.DataFrame]:
    return pq.read_table(path).to_pandas() if path.exists() else None

# ---- sample fetchers (deterministic; 可換真來源) --------------------------
def fetch_prices(tk,style,since,as_of):
    start=_dt.date(2025,6,2) if not since else _dt.date.fromisoformat(since)+_dt.timedelta(days=1)
    days=_bdays(start,_dt.date.fromisoformat(as_of))
    if not days: return pd.DataFrame(columns=["date","ticker","adj_close","volume"])
    import random
    mu={"tech":.0011,"semi":.0013,"growth":.0008,"balanced":.0006,"income":.0004,"value":.0005}[style]
    sig={"tech":.018,"semi":.022,"growth":.015,"balanced":.011,"income":.009,"value":.012}[style]
    base=10.0+(_seed(tk,"b")%120)/100.0; rows=[]
    for ds in days:
        n=(_dt.date.fromisoformat(ds)-_dt.date(2025,6,2)).days; rr=random.Random(_seed(tk,ds))
        px=round(base*math.exp(mu*n+sig*0.6*math.sin(n/9))*(1+(rr.random()-.5)*.02),4)
        rows.append({"date":ds,"ticker":tk,"adj_close":px,"volume":int(8e5+rr.random()*4e6)})
    return pd.DataFrame(rows)
def fetch_aum_flows(tk,style,since,as_of):
    start=_dt.date(2025,6,2) if not since else _dt.date.fromisoformat(since)+_dt.timedelta(days=1)
    days=_bdays(start,_dt.date.fromisoformat(as_of)); import random
    ar,fr=[],[]; base=12+(_seed(tk,"a")%58)
    for ds in days:
        rr=random.Random(_seed(tk,ds,"f")); net=round((rr.random()-.45)*.9,3)
        n=(_dt.date.fromisoformat(ds)-_dt.date(2025,6,2)).days
        ar.append({"date":ds,"ticker":tk,"aum":round(max(5,base*(1+.0006*n)+net*3),2)})
        fr.append({"date":ds,"ticker":tk,"net_flow":net})
    return pd.DataFrame(ar),pd.DataFrame(fr)
def fetch_holdings(tk,style,since,as_of,window=30):
    """日頻 PCF 張數（含 NEW/加碼/減碼/出清）"""
    import random
    end=_dt.date.fromisoformat(as_of); dates,d=[],end
    while len(dates)<window:
        if d.weekday()<5: dates.append(d.isoformat())
        d-=_dt.timedelta(days=1)
    dates=dates[::-1]
    if since and dates[-1]<=since: return pd.DataFrame(columns=["date","ticker","holding","name","sector","shares"])
    rnd=random.Random(_seed(tk,"h"))
    boost={"tech":["2330","2454","2308","2345"],"semi":["2330","2454","3711","2303","2379"],
           "income":["2412","2881","6505","2330"],"value":["6505","2881","2317","2412"],
           "growth":["2330","2317","2382","2345"],"balanced":["2330","2317","2881","2412"]}.get(style,[])
    sc=sorted(((t,(4 if t in boost else 0)+rnd.random()) for t,_,_ in HOLDING_UNIV),key=lambda x:-x[1])
    holds=[t for t,_ in sc[:11]]
    new_h=rnd.choice(holds); acc_h=rnd.choice(holds); red_h=rnd.choice(holds)
    exit_h=rnd.choice(holds) if rnd.random()<0.4 else None
    rows=[]
    for h in holds:
        base=int(rnd.uniform(2000,40000)); ns=rnd.randint(window-7,window-2) if h==new_h else 0
        for i,ds in enumerate(dates):
            if since and ds<=since: continue
            if h==new_h and i<ns: shares=0
            elif h==exit_h and i>=window-4: shares=0
            else:
                if h==acc_h: drift=1+0.018*(i-(window-8)) if i>=window-8 else 1.0
                elif h==red_h: drift=1-0.02*(i-(window-8)) if i>=window-8 else 1.0
                else: drift=1.0
                shares=max(0,int(base*max(0.2,drift)*(1+0.004*math.sin(i/4)+rnd.uniform(-.01,.01))))
            rows.append({"date":ds,"ticker":tk,"holding":h,"name":HNAME[h],"sector":HSEC[h],"shares":shares})
    return pd.DataFrame(rows)

# ---- Store (增量) ---------------------------------------------------------
DATASETS=("prices","aum","flows","holdings")
KEYS={"prices":["date","ticker"],"aum":["date","ticker"],"flows":["date","ticker"],"holdings":["date","ticker","holding"]}
class Store:
    def __init__(self, dict_root:Path, base_root:Optional[Path]=None):
        self.root=Path(dict_root); self.base=Path(base_root) if base_root else self.root/"_base"
        for ds in DATASETS: (self.root/ds).mkdir(parents=True,exist_ok=True)
        self.base.mkdir(parents=True,exist_ok=True)
        self.man_path=self.root/"_manifest.json"
        self.man=json.loads(self.man_path.read_text("utf-8")) if self.man_path.exists() else {ds:{} for ds in DATASETS}
    def _p(self,ds,tk): return self.root/ds/f"{tk}.parquet"
    def _last(self,ds,tk): return self.man.get(ds,{}).get(tk,{}).get("last_date")
    def _save_man(self):
        tmp=self.man_path.with_suffix(".json.tmp"); tmp.write_text(json.dumps(self.man,ensure_ascii=False,indent=2),"utf-8"); os.replace(tmp,self.man_path)
    def _upsert(self,ds,tk,new):
        if new is None or new.empty: return 0
        ex=_read_parquet(self._p(ds,tk)); before=0 if ex is None else len(ex)
        comb=pd.concat([ex,new],ignore_index=True) if ex is not None else new.copy()
        comb=comb.drop_duplicates(subset=KEYS[ds],keep="last").sort_values(KEYS[ds]).reset_index(drop=True)
        _atomic_parquet(comb,self._p(ds,tk))
        self.man.setdefault(ds,{})[tk]={"last_date":str(comb["date"].max()),"rows":int(len(comb)),"updated_at":_dt.datetime.now(_dt.timezone.utc).isoformat()}
        return len(comb)-before
    def update(self, as_of:Optional[str]=None)->Dict[str,Any]:
        as_of=as_of or _dt.date.today().isoformat()
        rep={"as_of":as_of,"added":{ds:0 for ds in DATASETS}}
        for tk,_,st in UNIVERSE:
            p=fetch_prices(tk,st,self._last("prices",tk),as_of); rep["added"]["prices"]+=self._upsert("prices",tk,p)
            a,f=fetch_aum_flows(tk,st,self._last("aum",tk),as_of)
            rep["added"]["aum"]+=self._upsert("aum",tk,a); rep["added"]["flows"]+=self._upsert("flows",tk,f)
            h=fetch_holdings(tk,st,self._last("holdings",tk),as_of); rep["added"]["holdings"]+=self._upsert("holdings",tk,h)
        self._save_man(); rep["ok"]=True; return rep
    def status(self)->Dict[str,Any]:
        out={"dict_root":str(self.root),"datasets":{}}
        for ds in DATASETS:
            m=self.man.get(ds,{}); dates=[v.get("last_date") for v in m.values() if v.get("last_date")]
            out["datasets"][ds]={"tickers":len(m),"rows":sum(v.get("rows",0) for v in m.values()),"latest":max(dates) if dates else None}
        return out
    def set_base(self,cfg):
        p=self.base/"base_config.json"; cur=json.loads(p.read_text("utf-8")) if p.exists() else {}
        cur.update(cfg); cur["_updated_at"]=_dt.datetime.now(_dt.timezone.utc).isoformat()
        tmp=p.with_suffix(".json.tmp"); tmp.write_text(json.dumps(cur,ensure_ascii=False,indent=2),"utf-8"); os.replace(tmp,p); return cur
    # ---- 內嵌匯出 ----
    def export_perf(self)->Dict[str,Any]:
        etfs=[]; dset=set()
        for tk,name,st in UNIVERSE:
            px=_read_parquet(self._p("prices",tk)); 
            if px is None or px.empty: continue
            px=px.sort_values("date"); au=_read_parquet(self._p("aum",tk)); fl=_read_parquet(self._p("flows",tk))
            dset.update(px["date"].tolist())
            etfs.append({"ticker":tk,"name":name,"style":st,"manager":MANAGER.get(tk,"—"),
                "inception":RECENT_NEW.get(tk,"2025-06-02"),"is_new":tk in RECENT_NEW,
                "adj":[round(float(x),4) for x in px["adj_close"]],
                "aum":[round(float(x),2) for x in (au.sort_values('date')['aum'] if au is not None else [])],
                "flow":[round(float(x),3) for x in (fl.sort_values('date')['net_flow'] if fl is not None else [])]})
        dates=sorted(dset); ytd=next((i for i,d in enumerate(dates) if d>="2026-01-01"),max(0,len(dates)-1))
        return {"meta":{"title":"主動式 ETF 績效與資金流排行","source":"VDF · PARQUET (incremental)",
            "generated":_dt.date.today().isoformat(),"as_of":dates[-1] if dates else None,"dates":dates,"ytd_idx":ytd,
            "horizons":[1,5,10,20,60,120,240],"return_basis":"Adj Close 總報酬（含配息 dividend-reinvested）","note":"資料來自 PARQUET 增量庫。","count":len(etfs)},"etfs":etfs}
    def export_holdings(self)->Dict[str,Any]:
        etfs=[]; dset=set()
        for tk,name,st in UNIVERSE:
            hd=_read_parquet(self._p("holdings",tk))
            if hd is None or hd.empty: continue
            dates=sorted(hd["date"].unique().tolist()); dset.update(dates)
            hold=[]
            for h,g in hd.groupby("holding"):
                g=g.set_index("date").reindex(dates).fillna(0); hold.append({"h":h,"s":[int(x) for x in g["shares"]]})
            etfs.append({"ticker":tk,"name":name,"style":st,"hold":hold})
        dates=sorted(dset)
        return {"meta":{"title":"主動式 ETF 持股異動","subtitle":"Active ETF Holdings Flow",
            "source":"VDF · ETF 每日 PCF 申購買回清單","generated":_dt.date.today().isoformat(),
            "dates":dates,"names":HNAME,"sectors":HSEC,
            "note":"張數來自每日 PCF。NEW=新增 / 加碼=近期淨增 / 減碼=近期淨減 / 出清=降為0。",
            "etf_count":len(etfs),"univ_count":len(HOLDING_UNIV)},"etfs":etfs}

# ---- HTML build / inject --------------------------------------------------
def _logo_b64(logo_path:Optional[Path])->str:
    if logo_path and Path(logo_path).exists():
        return "data:image/png;base64,"+base64.b64encode(Path(logo_path).read_bytes()).decode()
    return ""  # 模板回退文字標
def build_ui(template_dir:Path, out_dir:Path, store:Store, base:str, dictp:str, logo:Optional[Path]=None)->Dict[str,Any]:
    """單檔多頁：把績效+持股雙資料一次注入 console_merged_template → 一個 HTML UI"""
    template_dir=Path(template_dir); out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    logo_b64=_logo_b64(logo or (template_dir/"VIA_logo.png"))
    perf=json.dumps(store.export_perf(),ensure_ascii=False,separators=(",",":"))
    hold=json.dumps(store.export_holdings(),ensure_ascii=False,separators=(",",":"))
    built=[]
    merged=template_dir/"console_merged_template.html"
    if merged.exists():
        s=merged.read_text("utf-8")
        s=s.replace("__PERF__",perf).replace("__HOLD__",hold)
        s=s.replace("__LOGO__",logo_b64).replace("__BASE__",base or "").replace("__DICT__",dictp or "")
        (out_dir/"VIA_ActiveETF_Console.html").write_text(s,"utf-8"); built.append("VIA_ActiveETF_Console.html")
    else:
        # 後備：舊三檔模板（若合併模板不在）
        for tpl,outf,data in [("perf_template3.html","VIA_ETF_Performance_Ranking.html",perf),
                              ("holdings_template.html","VIA_ETF_Holdings_Flow.html",hold),
                              ("console_template.html","VIA_ActiveETF_Console.html",None)]:
            tp=template_dir/tpl
            if not tp.exists(): continue
            s=tp.read_text("utf-8")
            if data is not None: s=s.replace("__DATA__",data)
            s=s.replace("__LOGO__",logo_b64).replace("__BASE__",base or "").replace("__DICT__",dictp or "")
            (out_dir/outf).write_text(s,"utf-8"); built.append(outf)
    return {"built":built,"out_dir":str(out_dir)}

# ---- sync (= 抓取→增量→匯出→注入建 HTML) ---------------------------------
def sync(dict_root:Path, base_root:Optional[Path], template_dir:Path, out_dir:Path,
         as_of:Optional[str]=None, logo:Optional[Path]=None, eco:bool=True)->Dict[str,Any]:
    rep={"module":MODULE_ID,"version":VERSION}
    if eco:
        e=check_eco(["pyarrow","pandas","yfinance"],"3.12","windows"); rep["eco"]=e
        if not e["ok"]: rep["ok"]=False; rep["stopped"]="eco gate BLOCK"; return rep
    st=Store(dict_root,base_root)
    st.set_base({"store_root":str(dict_root),"universe":len(UNIVERSE),"synced_at":_dt.datetime.now(_dt.timezone.utc).isoformat()})
    rep["update"]=st.update(as_of=as_of)
    rep["build"]=build_ui(template_dir,out_dir,st,str(base_root or st.base),str(dict_root),logo)
    rep["status"]=st.status(); rep["ok"]=True
    return rep

# ---- selftest -------------------------------------------------------------
def run_self_tests()->Dict[str,Any]:
    import tempfile
    P,Fa=[],[]
    def t(n,fn):
        try: fn(); P.append(n)
        except Exception as ex: Fa.append({"t":n,"e":str(ex),"tb":traceback.format_exc()})
    def t_eco():
        assert check_eco(["numpy==2.0.1"])["decision"]=="BLOCK"
        assert check_eco(["pandas","pyarrow"])["decision"]=="PASS"
        assert check_eco(["uvloop"],"3.12","windows")["decision"]=="BLOCK"
    def t_sync_incremental():
        with tempfile.TemporaryDirectory() as d:
            st=Store(Path(d))
            r1=st.update(as_of="2026-02-01"); assert r1["added"]["prices"]>0 and r1["added"]["holdings"]>0
            rows1=pq.read_table(st._p("prices","00980A")).num_rows
            st.update(as_of="2026-02-01"); rows2=pq.read_table(st._p("prices","00980A")).num_rows
            assert rows1==rows2, "重跑不應增長"
            st.update(as_of="2026-02-20"); rows3=pq.read_table(st._p("prices","00980A")).num_rows
            assert rows3>rows2, "推進應 append"
    def t_exports():
        with tempfile.TemporaryDirectory() as d:
            st=Store(Path(d)); st.update(as_of="2026-03-15")
            p=st.export_perf(); assert p["meta"]["count"]==25 and len(p["etfs"][0]["adj"])>0 and p["etfs"][0]["manager"]
            h=st.export_holdings(); assert h["meta"]["etf_count"]==25 and len(h["etfs"][0]["hold"])>0
            assert all(len(o["s"])==len(h["meta"]["dates"]) for o in h["etfs"][0]["hold"]), "持股序列長度一致"
    def t_build():
        with tempfile.TemporaryDirectory() as d:
            st=Store(Path(d+"/dict")); st.update(as_of="2026-03-15")
            tdir=Path(d+"/tpl"); tdir.mkdir()
            (tdir/"console_merged_template.html").write_text("<html>P=__PERF__|H=__HOLD__|L=__LOGO__|B=__BASE__|D=__DICT__</html>","utf-8")
            r=build_ui(tdir,Path(d+"/out"),st,"BX","DX",None)
            assert r["built"]==["VIA_ActiveETF_Console.html"], r["built"]
            c=(Path(d+"/out")/"VIA_ActiveETF_Console.html").read_text("utf-8")
            assert '"etfs"' in c and "BX" in c and "DX" in c and "__PERF__" not in c and "__HOLD__" not in c
    t("eco_gate",t_eco); t("sync_incremental",t_sync_incremental); t("exports_shape",t_exports); t("build_ui_inject",t_build)
    return {"ok":not Fa,"passed":P,"failed":Fa,"total":len(P)+len(Fa)}

# ---- CLI ------------------------------------------------------------------
def _pr(o): print(json.dumps(o,ensure_ascii=False,indent=2))
def main(argv=None)->int:
    ap=argparse.ArgumentParser(prog="VIA_ActiveETF_System")
    ap.add_argument("command",nargs="?",default="status",choices=["sync","status","eco-check","selftest"])
    ap.add_argument("--dict",default=str(default_dict()))
    ap.add_argument("--base",default="")
    ap.add_argument("--templates",default=str(Path(__file__).resolve().parent))
    ap.add_argument("--out",default="")
    ap.add_argument("--as-of",default=None)
    ap.add_argument("--logo",default="")
    ap.add_argument("--pkgs",default=""); ap.add_argument("--py",default="3.12"); ap.add_argument("--os",default="windows")
    a=ap.parse_args(argv)
    if a.command=="selftest":
        r=run_self_tests(); _pr(r); return 0 if r["ok"] else 1
    if a.command=="eco-check":
        _pr(check_eco([p for p in a.pkgs.split() if p],a.py,a.os)); return 0
    dictp=Path(a.dict); base=Path(a.base) if a.base else None
    if a.command=="status":
        _pr(Store(dictp,base).status()); return 0
    if a.command=="sync":
        out=Path(a.out) if a.out else Path(a.templates)
        logo=Path(a.logo) if a.logo else None
        r=sync(dictp,base,Path(a.templates),out,as_of=a.as_of,logo=logo)
        _pr({"ok":r.get("ok"),"eco":r.get("eco",{}).get("decision"),"added":r.get("update",{}).get("added"),
             "built":r.get("build",{}).get("built"),"out":r.get("build",{}).get("out_dir"),
             "status":r.get("status",{}).get("datasets")})
        return 0 if r.get("ok") else 2
    return 1

if __name__=="__main__":
    raise SystemExit(main())
