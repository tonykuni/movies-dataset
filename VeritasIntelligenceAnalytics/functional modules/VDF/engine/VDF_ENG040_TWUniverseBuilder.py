#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_TW_Universe_Builder — 第一階段：建出「全台股」基礎宇宙(TWSE+TPEx)
   目的：用免費官方來源建出全台股清單(代碼/名稱/市場/產業)，成為 ETF Console 與
        Equity Insight 兩模板共用的 master universe；之後 VDF 各引擎把日線/法人/財報
        寫進 DICT，由 VIA_VDF_Bridge 對應注入兩模板。
   來源(免費·官方·可驗證；每筆附 source_url)：
     上市 TWSE 公司基本資料: https://openapi.twse.com.tw/v1/opendata/t187ap03_L
     上市 TWSE 全部日收盤  : https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
     上櫃 TPEx 主板日收盤  : https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes
     上櫃 TPEx 公司基本資料: https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O
   規則(沿用鎖定)：TW_TICKER_REGEX = r"(?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})"
   輸出：master universe → json / parquet / duckdb(表 universe)，欄位
     code, name, market(TWSE|TPEx), industry, yf(代碼.TW/.TWO), source_url, verifiable
   用法：
     py -3.11 VIA_TW_Universe_Builder.py --probe-urls
     py -3.11 VIA_TW_Universe_Builder.py --out C:\\...\\_dict\\tw_universe.json --duckdb C:\\...\\active_etf.duckdb
     py -3.11 VIA_TW_Universe_Builder.py --offline-demo --out demo.json
   LL：requests 選用(有網路才實抓)；pandas/duckdb 選用(寫對應格式)。零付費。
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
import sys, re, json, argparse, datetime
TODAY=datetime.date.today().isoformat()
TW_TICKER_REGEX = re.compile(r"^(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})$")
SRC={
 "twse_basic":"https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
 "twse_all_day":"https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
 "tpex_basic":"https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",
 "tpex_day":"https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
}
def _req():
    try: import requests; return requests
    except Exception: return None
def probe():
    print(json.dumps({"verifiable_free_sources":SRC,
      "ticker_rule":"first digit 1-9, 4 digits, exclude years 2021-2030",
      "feeds_two_templates":["Taiwan Active Stock ETF Console","Equity Insight (Resonance Stock Stack)"],
      "pipeline":"VDF engines → write DBs into DICT → VIA_VDF_Bridge classifies → inject into both templates"}, ensure_ascii=False, indent=2))

def fetch_twse(requests):
    out=[]
    try:
        r=requests.get(SRC["twse_basic"],timeout=12,headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            for row in r.json():
                code=(row.get("公司代號") or row.get("Code") or "").strip()
                name=(row.get("公司簡稱") or row.get("公司名稱") or row.get("Name") or "").strip()
                ind=(row.get("產業別") or row.get("Industry") or "").strip()
                if TW_TICKER_REGEX.match(code):
                    out.append({"code":code,"name":name,"market":"TWSE","industry":ind,
                                "yf":code+".TW","source_url":SRC["twse_basic"],"verifiable":True})
    except Exception as e: sys.stderr.write(f"[twse] {e}\n")
    return out
def fetch_tpex(requests):
    out=[]
    try:
        r=requests.get(SRC["tpex_basic"],timeout=12,headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            for row in r.json():
                code=(row.get("SecuritiesCompanyCode") or row.get("公司代號") or "").strip()
                name=(row.get("CompanyAbbreviation") or row.get("公司簡稱") or "").strip()
                ind=(row.get("SecuritiesIndustryCode") or row.get("產業別") or "").strip()
                if TW_TICKER_REGEX.match(code):
                    out.append({"code":code,"name":name,"market":"TPEx","industry":ind,
                                "yf":code+".TWO","source_url":SRC["tpex_basic"],"verifiable":True})
    except Exception as e: sys.stderr.write(f"[tpex] {e}\n")
    return out

def offline_demo():
    base=[("2330","台積電","TWSE","半導體"),("2454","聯發科","TWSE","半導體"),("2317","鴻海","TWSE","電子"),
          ("2308","台達電","TWSE","電子零組件"),("6770","力積電","TWSE","半導體"),("5347","世界先進","TPEx","半導體"),
          ("3105","穩懋","TPEx","半導體"),("8069","元太","TPEx","光電")]
    mk=lambda c,n,m,i:{"code":c,"name":n,"market":m,"industry":i,"yf":c+(".TW" if m=="TWSE" else ".TWO"),
                       "source_url":SRC["twse_basic" if m=="TWSE" else "tpex_basic"],"verifiable":True}
    return [mk(*b) for b in base if TW_TICKER_REGEX.match(b[0])]

def write_outputs(rows, out_json, duckdb_path):
    res={}
    if out_json:
        open(out_json,"w",encoding="utf-8").write(json.dumps(
          {"as_of":TODAY,"count":len(rows),"sources":SRC,"universe":rows},ensure_ascii=False,indent=2))
        res["json"]=out_json
    if duckdb_path:
        try:
            import duckdb,pandas as pd
            con=duckdb.connect(duckdb_path);con.register("u",pd.DataFrame(rows))
            con.execute("CREATE OR REPLACE TABLE universe AS SELECT * FROM u")
            n=con.execute("SELECT count(*) FROM universe").fetchone()[0];con.close()
            res["duckdb_rows"]=n
        except Exception as e: res["duckdb_error"]=str(e)
    return res

def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe-urls",action="store_true");ap.add_argument("--offline-demo",action="store_true")
    ap.add_argument("--out",default="tw_universe.json");ap.add_argument("--duckdb",default="")
    a=ap.parse_args()
    if a.probe_urls: return probe()
    requests=_req()
    rows = offline_demo() if a.offline_demo else (fetch_twse(requests)+fetch_tpex(requests))
    # 去重(同代碼以先到為準)
    seen=set();uniq=[]
    for r in rows:
        if r["code"] in seen: continue
        seen.add(r["code"]);uniq.append(r)
    res=write_outputs(uniq,a.out,a.duckdb)
    by_mkt={};
    for r in uniq: by_mkt[r["market"]]=by_mkt.get(r["market"],0)+1
    sys.stdout.write(json.dumps({"ok":True,"total":len(uniq),"by_market":by_mkt,"outputs":res},ensure_ascii=False,indent=2))

if __name__=="__main__": main()
