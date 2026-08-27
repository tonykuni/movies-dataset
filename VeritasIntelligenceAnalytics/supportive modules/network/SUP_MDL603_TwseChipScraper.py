#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
twse_chip_scraper.py  —  VIA 籌碼分析平台 真實資料抓取後端
================================================================
從 TWSE 公開 JSON 端點抓「個股三大法人買賣超(T86)」與「融資融券(MI_MARGN)」,
跨 N 個交易日組成時間序列,輸出 chip_data.json 給 VIA_ChipAnalysis_Platform 前端載入。

為何要後端:瀏覽器無法執行 requests/BeautifulSoup/Playwright;且前端直接 fetch TWSE
會被 CORS 擋。所以由此 Python 後端抓→落地 JSON→前端讀同目錄 JSON。

環境:Windows 11 / PowerShell 7 / Python 3.10+
相依:  pip install requests
執行:  python twse_chip_scraper.py            # 預設抓台積電 2330,近 40 個交易日
       python twse_chip_scraper.py 2454 60     # 抓聯發科 2454,近 60 日

⚠ 重要:TWSE 端點與欄位名稱偶有變動。第一次跑請確認 console 印出的「命中欄位」
   是否正確;若 TWSE 改版,只需調整 _COLS 關鍵字即可,不必動主流程。
   上櫃(TPEX)股票見檔尾 fetch_tpex_t86() 骨架(端點不同)。
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
import sys, json, time, datetime as dt
from pathlib import Path
import requests

# ── 設定 ─────────────────────────────────────────────────────────────────────
STOCK   = sys.argv[1] if len(sys.argv) > 1 else "2330"
DAYS    = int(sys.argv[2]) if len(sys.argv) > 2 else 40
OUT     = Path(__file__).with_name("chip_data.json")   # 與前端 HTML 同目錄
TIMEOUT = 15
RETRY   = 3
PAUSE   = 0.6                                           # 禮貌延遲,避免被擋

HEADERS = {"User-Agent": "Mozilla/5.0 (VIA-chip-scraper; research)"}

# 以「關鍵字」比對欄位,避免 TWSE 改欄位順序就壞掉
_COLS = {
    "code":    ["證券代號", "股票代號", "代號"],
    "foreign": ["外陸資買賣超股數(不含外資自營商)", "外資買賣超股數", "外陸資買賣超股數"],
    "foreign_dealer": ["外資自營商買賣超股數"],
    "trust":   ["投信買賣超股數"],
    "dealer":  ["自營商買賣超股數", "自營商買賣超股數(自行買賣)"],
    "margin_bal": ["融資今日餘額", "融資餘額"],
    "short_bal":  ["融券今日餘額", "融券餘額"],
}

TWSE_T86 = "https://www.twse.com.tw/rwd/zh/fund/T86"
TWSE_MGN = "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"


# ── 工具 ─────────────────────────────────────────────────────────────────────
def _get(url, params):
    """帶重試的 GET JSON;非交易日 TWSE 會回 stat != 'OK'。"""
    for k in range(RETRY):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if k == RETRY - 1:
                print(f"   [warn] {url} {params.get('date')} 失敗:{e}")
            time.sleep(PAUSE * (k + 1))
    return None


def _tables(js):
    """同時相容新版 {'tables':[{fields,data}]} 與舊版 {'fields','data'}。"""
    if not js:
        return []
    if js.get("stat") and js["stat"] != "OK":
        return []
    if "tables" in js and js["tables"]:
        return [(t.get("fields", []), t.get("data", [])) for t in js["tables"]]
    if "fields" in js and "data" in js:
        return [(js["fields"], js["data"])]
    return []


def _col_idx(fields, keys):
    for i, f in enumerate(fields):
        fx = str(f).replace(" ", "")
        for k in keys:
            if k.replace(" ", "") in fx:
                return i
    return None


def _num(x):
    try:
        return int(str(x).replace(",", "").replace("--", "0").strip() or 0)
    except Exception:
        return 0


def _trading_dates(n):
    """往回取 n 個「可能的交易日」(跳過週末);非交易日由 TWSE 回應自然濾掉。"""
    out, d = [], dt.date.today()
    while len(out) < n * 2 and len(out) < 90:      # 多抓緩衝,後面用實際回應過濾
        if d.weekday() < 5:
            out.append(d)
        d -= dt.timedelta(days=1)
    return list(reversed(out))


# ── 抓取:三大法人 T86(個股) ─────────────────────────────────────────────────
def fetch_t86(stock, dates):
    series = {"dates": [], "foreign": [], "trust": [], "dealer": []}
    hit_logged = False
    for d in dates:
        ymd = d.strftime("%Y%m%d")
        js = _get(TWSE_T86, {"date": ymd, "selectType": "ALLBUT0999", "response": "json"})
        for fields, rows in _tables(js):
            ci = _col_idx(fields, _COLS["code"])
            fi = _col_idx(fields, _COLS["foreign"])
            fdi = _col_idx(fields, _COLS["foreign_dealer"])
            ti = _col_idx(fields, _COLS["trust"])
            di = _col_idx(fields, _COLS["dealer"])
            if ci is None or fi is None or ti is None:
                continue
            if not hit_logged:
                print(f"   [T86] 命中欄位 foreign={fields[fi]!r} trust={fields[ti]!r} "
                      f"dealer={fields[di] if di is not None else 'NA'!r}")
                hit_logged = True
            for row in rows:
                if str(row[ci]).strip() == stock:
                    foreign = _num(row[fi]) + (_num(row[fdi]) if fdi is not None else 0)
                    trust = _num(row[ti])
                    dealer = _num(row[di]) if di is not None else 0
                    # 股 → 張(/1000),圖面較好讀;要原始股數就移除 //1000
                    series["dates"].append(d.strftime("%m/%d"))
                    series["foreign"].append(foreign // 1000)
                    series["trust"].append(trust // 1000)
                    series["dealer"].append(dealer // 1000)
                    break
        time.sleep(PAUSE)
    return series


# ── 抓取:融資融券 MI_MARGN(個股) ───────────────────────────────────────────
def fetch_margin(stock, dates):
    series = {"dates": [], "margin_balance": [], "short_balance": []}
    for d in dates:
        ymd = d.strftime("%Y%m%d")
        js = _get(TWSE_MGN, {"date": ymd, "selectType": "ALL", "response": "json"})
        for fields, rows in _tables(js):
            ci = _col_idx(fields, _COLS["code"])
            mi = _col_idx(fields, _COLS["margin_bal"])
            si = _col_idx(fields, _COLS["short_bal"])
            if ci is None or mi is None:
                continue
            for row in rows:
                if str(row[ci]).strip() == stock:
                    series["dates"].append(d.strftime("%m/%d"))
                    series["margin_balance"].append(_num(row[mi]))
                    series["short_balance"].append(_num(row[si]) if si is not None else 0)
                    break
        time.sleep(PAUSE)
    return series


# ── 主流程 ───────────────────────────────────────────────────────────────────
def main():
    dates = _trading_dates(DAYS)
    print(f"[VIA] 抓取 {STOCK} 近 ~{DAYS} 交易日(掃 {len(dates)} 個日期,非交易日自動略過)…")

    inst = fetch_t86(STOCK, dates)
    inst = {k: v[-DAYS:] for k, v in inst.items()}        # 取最後 DAYS 個有效日
    print(f"   三大法人:取得 {len(inst['dates'])} 日")

    mgn = fetch_margin(STOCK, dates)
    mgn = {k: v[-DAYS:] for k, v in mgn.items()}
    print(f"   融資融券:取得 {len(mgn['dates'])} 日")

    out = {
        "meta": {
            "stock": STOCK,
            "name": "",                                   # 可由前端對照表補名稱
            "updated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": "TWSE T86 / MI_MARGN",
            "unit": "三大法人=張(千股);融資融券=餘額",
            "is_real": True,
        },
        "institutional": inst,
        "margin": mgn,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 已寫出 {OUT}  →  將 HTML 與此 JSON 放同目錄,用本機伺服器開啟:")
    print(f"      python -m http.server 8000   然後瀏覽 http://localhost:8000/VIA_ChipAnalysis_Platform_v2.html")
    if not inst["dates"]:
        print("[!] 三大法人 0 日:多半是 TWSE 端點/欄位改版或近日皆非交易日。")
        print("    替代:openapi.twse.com.tw/v1/exchangeReport/T86(僅最新日)可先驗證連線。")


# ── TPEX(上櫃)骨架:端點不同,需另接 ────────────────────────────────────────
def fetch_tpex_t86(stock, dates):
    """上櫃股票(如 6488 環球晶)三大法人:TPEX 端點與 TWSE 不同。
    參考:https://www.tpex.org.tw/openapi/  之三大法人買賣超日報。
    結構不同,故另列;接法同上:抓→比對代號→組序列。"""
    raise NotImplementedError("TPEX 端點請依 tpex.org.tw OpenAPI 補；結構與 TWSE 不同。")


if __name__ == "__main__":
    main()
