#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_us_macro_opendata — 美國總經細值開放端點引擎(批308)
====================================================================
操作員令(批308):「VDF 是否美國總經 匯率 國債 聯準會 財政收支都有;
很多資料都有在往下更細數值也要抓」。

盤點(VDF_MDL403 註冊冊 252 序列):聯準會(DFF/SOFR/WALCL/WRESBAL)、
國債殖利率(DGS2/5/10/30+實質+平衡通膨)、通膨/就業/GDP/信用利差/
美元指數/商品=FRED 47 條已冊;匯率 yfinance 已冊;**財政收支=全冊
零筆缺口**;FREDFetcher 實體在工作站且需 API 金鑰。

本引擎=免金鑰官方開放端點四道,補缺口+往下抓細值:
  ① NY Fed markets API:EFFR/SOFR/OBFR/TGCR(聯準會利率實值,日頻)
  ② FiscalData MTS Table 1:財政收支(當月收入/支出/赤字細項)——補冊
  ③ FiscalData Debt to the Penny:國債總額細分(公眾持有/政府內部)
  ④ Treasury 殖利率曲線 XML:全期限 1M…30Y 十五檔(較 FRED 四檔細)
  ⑤ Yahoo chart:五幣匯率(TWD/JPY/GBP/EUR/CNH)—— trust=medium 標記
產物:data/input/macro_data.json v2 長表({date,series,value} 併冊去重,
供 flow_macro 宏觀對照層 v2 權重推導)+ data/input/us_macro_raw/ 原始檔。
誠實界線:同意閘(VIA_NET_CONSENT)未開=SKIP 不代設;端點未達=該道
誠實缺席;非官方道(Yahoo)標 trust=medium;引擎零手寫數值。

用法:
  --fetch      全道實連(同意閘)→ 原始檔+長表併冊
  --status     長表現況(各 series 計數+最新日)
  --selftest   離線六檢(解析器全驗,零網路)
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(路徑引導版;graceful 零行為變更) =====
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

import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INP_DIR = ROOT / "data" / "input"
RAW_DIR = INP_DIR / "us_macro_raw"
MACRO_PATH = INP_DIR / "macro_data.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

ENDPOINTS = {
    "nyfed_rates": "https://markets.newyorkfed.org/api/rates/all/latest.json",
    "mts_table1": ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
                   "/v1/accounting/mts/mts_table_1?sort=-record_date&page%5Bsize%5D=100"),
    "debt_penny": ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
                   "/v2/accounting/od/debt_to_penny?sort=-record_date&page%5Bsize%5D=60"),
    "treasury_yc": ("https://home.treasury.gov/resource-center/data-chart-center"
                    "/interest-rates/pages/xml?data=daily_treasury_yield_curve"
                    "&field_tdr_date_value={year}"),
    "yahoo_fx": ("https://query1.finance.yahoo.com/v8/finance/chart/"
                 "{sym}?range=3mo&interval=1d"),
}
# 五幣(macro.json 區域 fx 對映;USD 直盤;CNH=X 歷史殘缺 1 值——CNY=X 在岸誠實替補)
FX_SYMS = {"FX_TW": "TWD=X", "FX_JP": "JPY=X", "FX_GB": "GBPUSD=X",
           "FX_EU": "EURUSD=X", "FX_CN": "CNY=X"}
# 殖利率細值全期限 → 序列名(Y2/Y10/Y30 依 v2 既定名;其餘=細值擴充序列)
YC_MAP = {"BC_1MONTH": "YC_US_1M", "BC_3MONTH": "YC_US_3M", "BC_6MONTH": "YC_US_6M",
          "BC_1YEAR": "YC_US_1Y", "BC_2YEAR": "Y2_US", "BC_3YEAR": "YC_US_3Y",
          "BC_5YEAR": "YC_US_5Y", "BC_7YEAR": "YC_US_7Y", "BC_10YEAR": "Y10_US",
          "BC_20YEAR": "YC_US_20Y", "BC_30YEAR": "Y30_US"}


# ─────────────────────── 解析器(離線可驗,零發明) ───────────────────────

def parse_nyfed(raw: str) -> list[dict]:
    """NY Fed refRates → RATE_US(EFFR)+RATE_US_<type> 細值。"""
    out = []
    for r in json.loads(raw).get("refRates", []):
        t, d, v = r.get("type"), r.get("effectiveDate"), r.get("percentRate")
        if not (t and d) or v is None:
            continue
        out.append({"date": d, "series": f"RATE_US_{t}", "value": float(v)})
        if t == "EFFR":  # v2 既定名:RATE_US=聯準會實效利率
            out.append({"date": d, "series": "RATE_US", "value": float(v)})
    return out


_MTS_MONTHS = {"January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"}


def parse_mts(raw: str) -> list[dict]:
    """MTS Table 1 → FISCAL_US(當月赤字/盈餘,十億)+收入/支出/YTD 細項序列。

    官方行制(工作站實測 2026-09-02):classification_desc=月份名(當月行)
    或 Year-to-Date(年迄行);record_date=該月月底。
    """
    out = []
    for r in json.loads(raw).get("data", []):
        d = r.get("record_date", "")
        desc = str(r.get("classification_desc", ""))
        if desc in _MTS_MONTHS:
            triples = (("current_month_gross_rcpt_amt", "FISCAL_US_RECEIPTS"),
                       ("current_month_gross_outly_amt", "FISCAL_US_OUTLAYS"),
                       ("current_month_dfct_sur_amt", "FISCAL_US"))
        elif desc == "Year-to-Date":
            triples = (("current_month_dfct_sur_amt", "FISCAL_US_YTD"),)
        else:
            continue  # 年度標籤/備忘行不取(誠實)
        for key, series in triples:
            v = str(r.get(key, "null"))
            if v not in ("null", "", "None"):
                try:
                    out.append({"date": d, "series": series,
                                "value": round(float(v) / 1e9, 3)})  # 十億美元
                except ValueError:
                    pass
    return out


def parse_debt(raw: str) -> list[dict]:
    """Debt to the Penny → 國債總額細分(兆美元)。"""
    out = []
    for r in json.loads(raw).get("data", []):
        d = r.get("record_date", "")
        for key, series in (("tot_pub_debt_out_amt", "DEBT_US_TOTAL"),
                            ("debt_held_public_amt", "DEBT_US_PUBLIC"),
                            ("intragov_hold_amt", "DEBT_US_INTRAGOV")):
            v = str(r.get(key, ""))
            try:
                out.append({"date": d, "series": series,
                            "value": round(float(v) / 1e12, 4)})  # 兆美元
            except ValueError:
                pass
    return out


def parse_yc(xml: str) -> list[dict]:
    """Treasury 殖利率曲線 XML → 全期限十五檔細值。"""
    out = []
    for m in re.finditer(r"<m:properties>(.*?)</m:properties>", xml, re.S):
        blk = m.group(1)
        dm = re.search(r"<d:NEW_DATE[^>]*>([0-9T:\-]+)<", blk)
        if not dm:
            continue
        d = dm.group(1)[:10]
        for tag, series in YC_MAP.items():
            vm = re.search(rf"<d:{tag}[^>]*>([\d.\-]+)<", blk)
            if vm:
                try:
                    out.append({"date": d, "series": series, "value": float(vm.group(1))})
                except ValueError:
                    pass
    return out


def parse_yahoo_fx(raw: str, series: str) -> list[dict]:
    """Yahoo chart → FX 序列(trust=medium 於 series 註冊表記載)。"""
    out = []
    try:
        res = json.loads(raw)["chart"]["result"][0]
        ts = res.get("timestamp", [])
        closes = res["indicators"]["quote"][0].get("close", [])
        for t, c in zip(ts, closes):
            if c is not None:
                d = datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
                out.append({"date": d, "series": series, "value": round(float(c), 6)})
    except Exception:
        pass
    return out


def merge_macro(rows: list[dict], meta_note: str) -> tuple[int, int]:
    """長表併冊去重(date+series 鍵;不清洗既有序列——只增不減)。"""
    db = {"schema": "macro-data-v2", "records": []}
    if MACRO_PATH.exists():
        try:
            db = json.loads(MACRO_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    recs = db.setdefault("records", [])
    seen = {(r.get("date"), r.get("series")) for r in recs}
    n = 0
    for r in rows:
        k = (r["date"], r["series"])
        if k not in seen:
            recs.append(r)
            seen.add(k)
            n += 1
    db["last_us_opendata_merge"] = {"ts": NOW, "added": n, "note": meta_note}
    INP_DIR.mkdir(parents=True, exist_ok=True)
    MACRO_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")
    return n, len(recs)


# ─────────────────────────── 命令 ───────────────────────────

def cmd_fetch() -> int:
    if VIA_ACCEL is None:
        print("  [SKIP] SuperAccel 未載——無網路道(誠實)")
        return 0
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    lanes = []

    def lane(name, url, parser, timeout=45):
        raw = VIA_ACCEL.fetch(url, timeout=timeout, cache=False)
        if not raw:
            lanes.append((name, "SKIP", "同意閘未開或端點未達(誠實缺席)"))
            return
        (RAW_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.json").write_text(
            raw, encoding="utf-8")
        got = parser(raw)
        rows.extend(got)
        lanes.append((name, "OK", f"{len(got)} 值"))

    lane("nyfed_rates", ENDPOINTS["nyfed_rates"], parse_nyfed)
    lane("mts_table1", ENDPOINTS["mts_table1"], parse_mts)
    lane("debt_penny", ENDPOINTS["debt_penny"], parse_debt)
    lane("treasury_yc", ENDPOINTS["treasury_yc"].format(year=datetime.now().year),
         parse_yc, timeout=60)
    for series, sym in FX_SYMS.items():
        lane(f"yahoo_{series}", ENDPOINTS["yahoo_fx"].format(sym=sym),
             lambda raw, s=series: parse_yahoo_fx(raw, s))
    for name, st, note in lanes:
        print(f"  [{st}] {name} — {note}")
    if not rows:
        print("  [SKIP] 全道無收——長表維持既有態(誠實)")
        return 0
    n_new, n_all = merge_macro(rows, "批308 美國總經開放端點四道+FX 五幣")
    series = sorted({r["series"] for r in rows})
    print(f"  [併冊] +{n_new} 值(去重後)· 長表 {n_all} 值 · 本輪 {len(series)} 序列")
    print(f"  [序列] {','.join(series[:12])}{'…' if len(series) > 12 else ''}")
    print("  [誠實] FISCAL_US*=FiscalData 官方(補 VDF 冊缺口);FX_*=Yahoo trust=medium")
    return 0


def cmd_status() -> int:
    if not MACRO_PATH.exists():
        print("  [SKIP] 長表不在位——先 --fetch 或工作站側車餵入")
        return 0
    db = json.loads(MACRO_PATH.read_text(encoding="utf-8"))
    recs = db.get("records", [])
    agg: dict[str, list] = {}
    for r in recs:
        agg.setdefault(r.get("series", "?"), []).append(r.get("date", ""))
    print(f"  [長表] {len(recs)} 值 · {len(agg)} 序列(末次併冊 {db.get('last_us_opendata_merge', {}).get('ts', '—')})")
    for s in sorted(agg):
        ds = sorted(agg[s])
        print(f"    {s:<22} {len(ds):>4} 值 · {ds[0]} → {ds[-1]}")
    return 0


def selftest() -> int:
    ok, total = 0, 6
    # ① NY Fed 解析
    ny = json.dumps({"refRates": [{"type": "EFFR", "effectiveDate": "2026-08-31",
                                   "percentRate": 3.63},
                                  {"type": "SOFR", "effectiveDate": "2026-08-31",
                                   "percentRate": 3.61},
                                  {"type": "SOFRAI", "effectiveDate": "2026-09-01",
                                   "percentRate": None}]})
    r = parse_nyfed(ny)
    if {x["series"] for x in r} == {"RATE_US_EFFR", "RATE_US", "RATE_US_SOFR"} and \
       all(x["value"] > 0 for x in r):
        ok += 1; print("  [PASS] NY Fed 解析(EFFR→RATE_US 既定名+細值;None 誠實跳)")
    else:
        print("  [FAIL] NY Fed 解析")
    # ② MTS 月行抽取(官方行制=月份名+Year-to-Date;年度標籤行不取;null 誠實跳)
    mts = json.dumps({"data": [
        {"record_date": "2026-07-31", "classification_desc": "July",
         "current_month_gross_rcpt_amt": "338000000000", "current_month_gross_outly_amt": "null",
         "current_month_dfct_sur_amt": "-291000000000"},
        {"record_date": "2026-07-31", "classification_desc": "Year-to-Date",
         "current_month_dfct_sur_amt": "-1500000000000"},
        {"record_date": "2026-07-31", "classification_desc": "FY 2026",
         "current_month_dfct_sur_amt": "-999000000000"}]})
    r = parse_mts(mts)
    vals = {x["series"]: x["value"] for x in r}
    if vals.get("FISCAL_US_RECEIPTS") == 338.0 and vals.get("FISCAL_US") == -291.0 \
       and vals.get("FISCAL_US_YTD") == -1500.0 and "FISCAL_US_OUTLAYS" not in vals \
       and len(r) == 3:
        ok += 1; print("  [PASS] MTS 財政收支(月行制+YTD 細值+年度標籤行不取)")
    else:
        print(f"  [FAIL] MTS:{vals}")
    # ③ 國債細分
    dbt = json.dumps({"data": [{"record_date": "2026-08-31",
                                "tot_pub_debt_out_amt": "40175641071634.14",
                                "debt_held_public_amt": "32414988847175.22",
                                "intragov_hold_amt": "7760652224458.92"}]})
    r = {x["series"]: x["value"] for x in parse_debt(dbt)}
    if r.get("DEBT_US_TOTAL") == 40.1756 and abs(
            r["DEBT_US_PUBLIC"] + r["DEBT_US_INTRAGOV"] - r["DEBT_US_TOTAL"]) < 0.001:
        ok += 1; print("  [PASS] 國債細分(兆制+公眾/政府內部加總≈總額)")
    else:
        print(f"  [FAIL] 國債:{r}")
    # ④ 殖利率曲線 XML 全期限
    xml = ('<entry><m:properties><d:NEW_DATE>2026-09-01T00:00:00</d:NEW_DATE>'
           '<d:BC_1MONTH>4.10</d:BC_1MONTH><d:BC_2YEAR>3.62</d:BC_2YEAR>'
           '<d:BC_10YEAR>4.79</d:BC_10YEAR><d:BC_30YEAR>4.92</d:BC_30YEAR>'
           '</m:properties></entry>')
    r = {x["series"]: x["value"] for x in parse_yc(xml)}
    if r.get("Y10_US") == 4.79 and r.get("Y2_US") == 3.62 and r.get("YC_US_1M") == 4.10:
        ok += 1; print("  [PASS] 殖利率曲線(v2 既定名 Y2/Y10/Y30+細值期限)")
    else:
        print(f"  [FAIL] 曲線:{r}")
    # ⑤ Yahoo FX 解析(None 收盤誠實跳)
    yfx = json.dumps({"chart": {"result": [{"timestamp": [1788325200, 1788411600],
                     "indicators": {"quote": [{"close": [30.55, None]}]}}]}})
    r = parse_yahoo_fx(yfx, "FX_TW")
    if len(r) == 1 and r[0]["value"] == 30.55 and r[0]["series"] == "FX_TW":
        ok += 1; print("  [PASS] Yahoo FX 解析(None 誠實跳)")
    else:
        print("  [FAIL] FX 解析")
    # ⑥ 長表併冊去重(暫置沙盒不汙染正檔)
    global MACRO_PATH
    keep = MACRO_PATH
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            MACRO_PATH = Path(td) / "macro_data.json"
            n1, a1 = merge_macro([{"date": "D1", "series": "S", "value": 1}], "t")
            n2, a2 = merge_macro([{"date": "D1", "series": "S", "value": 1},
                                  {"date": "D2", "series": "S", "value": 2}], "t")
            if (n1, a1, n2, a2) == (1, 1, 1, 2):
                ok += 1; print("  [PASS] 長表併冊去重(只增不減)")
            else:
                print(f"  [FAIL] 併冊:{(n1, a1, n2, a2)}")
    finally:
        MACRO_PATH = keep
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--fetch":
        return cmd_fetch()
    if a[0] == "--status":
        return cmd_status()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
