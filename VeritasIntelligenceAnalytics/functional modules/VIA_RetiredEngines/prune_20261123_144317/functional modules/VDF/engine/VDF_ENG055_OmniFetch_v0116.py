#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG055_OmniFetch — 單 004 總擷取執行器(批137;via-omni)
====================================================================
操作員批137 大擷取令。八車道(READY 面實抓;NEEDS_KEY/WHITELIST 面
誠實登錄於單 004,候鑰/候白名單):
  L1 listings   雙所總清單附產業(代碼+中文名;TWSE 產業別冊內建)
  L2 trading    每日交易:逐股成交值/量/筆數(雙所)+市場總計 FMTQIK
  L3 valuation  每日估值:PE/PB/殖利率(雙所 BWIBBU/peratio)
  L4 etf_book   ETF 冊可更新(t187ap47_L;主動式=名稱含「主動」旗標)
  L5 etf_stats  ETF AUM/nav/PE/PB 快照(quoteSummary 握手道;台+全球)
                流量估算=ΔAUM−報酬效果 [ESTIMATE;≥2 快照自動出值]
  L6 global     指數擴編:美五大+亞洲+歐洲+南亞前十+區域匯率+區域 ETF
                (chart 直連;日線 2024-01-02→最新)
  L7 idx_val    指數估值代理(區域 ETF forwardPE/trailingPE/P/B [PROXY])
  L8 us_macro   FRED 細項(候 FRED_API_KEY;無鑰=誠實 SKIP)
韌性:批次即落盤 parquet+checkpoint 續跑+duckdb anti-join 冪等=中斷
零浪費;編碼 utf-8-sig。輸出:--export parquet|csv|sqlite|gsheet。
v0115→v0116(側線 2026-09-24 第六段;主線批號由併線的手指定 L25;操作員令「VDF加速器跟網路工具都要導入並覆蓋深入所有指令細節動作」):
  **更正 v0114 表頭**:那裡寫 L10/L11 是「全支唯二繞過工具的外呼」——**錯**。L13 FactSet(操作員點名的焦點引擎之一)也是:
  它只問統包「有沒有 curl 車道」,問完就自己 `subprocess.run(["curl", …])`,連線完全不經工具。v0114 我只驗了 L10/L11 兩條車道的原始碼,
  沒有全檔驗;第六段把 VDF_ENG089 的 audit 改成看語法樹(v0103)之後,「直連」那一欄當場把它列出來。
  ① L13 外呼改走統包 `curl_bytes`(HTML 位元組 → utf-8);工具缺這條車道=誠實 FAIL 講明要哪一版,不退回自己打 curl。
  ② 清單頁拿不到(閘關 DENY / 傳輸 FAIL)照實回那個態——以前回 EMPTY「掃 0 文零萃取(版式變?)」,把「沒連上」講成「版式變了」。
  ③ 先查庫缺啥:factset_earnings 已有的文章(source)不重抓;全在庫=OK 0 列並講明(不是 EMPTY)。
  自測 +⑯(假工具零網路:兩篇一篇已在庫 → 只抓一篇、萃取 P/E 與 EPS、倒推照舊;舊工具=FAIL;閘關=DENY;全檔語法樹零 ["curl", …])。
v0114→v0115(側線 2026-09-24 第五段;主線批號由併線的手指定 L25;操作員令「成交量 成交值 市值都以交易所為主」· 掉球 Z179 · Z180):
  **交易所不直接給市值,但給發行股數**——而且本支 L1 本來就在抓那一份:t187ap03_L「已發行普通股數或TDR原股發行股數」、
  t187ap03_O `IssueShares`(容器實量 TPEX openapi 出表 1150924,5483 = 641,221,651),**抓了卻把這一欄丟掉**。v0115 同一回包收下:
  ① L1 → 新表 `tw_shares_issued`(鍵 asof_date · code · market;asof_date=出表日期;src 具名 TWSE_OPENAPI_T187AP03_L / TPEX_OPENAPI_T187AP03_O)。
     **一份出表日一份**(只增不改):股數會變(容器實量兩份出表之間:8277 從 9,163 萬減到 3,950 萬、4747 與 1799 剛好翻倍),留史才算得出每一天的市值。
     欄名不用 `asof`——那是 DuckDB 的保留字(ASOF 聯結),實跑撞過。
  ② L2 上櫃每日收盤回包的 `Capitals`(每天的發行股數,與 IssueShares 同值)也進 `tw_shares_issued`(src TPEX_OPENAPI_DAILY_CAPITALS)。
  ③ L2 每列記 `src`(TWSE_OPENAPI_STOCK_DAY_ALL / TPEX_OPENAPI_DAILY_CLOSE)——`tw_trading_daily` 有兩個寫入者(本支 L2 · ENG057),
     口徑要看得出是誰寫的(Z180;上櫃 openapi 與 ENG057 的 rwd dailyQuotes 同口徑,容器實量 890/890)。
  ④ `--shares-snapshot`:樹上的交易所官方快照(t187ap03_L/_O 2026-08-05,批363 存證、可重放;openapi.twse 容器被擋時也拿得到)
     重放進同一張表(src=TREE_SNAPSHOT_…)——股數史從出表日 2026-08-04/05 起就有,嚴格市值才有起點。不觸網、不必同意閘、冪等。
     L1 與快照重放共用同一個解析 `_shares_rows`(不長第二份)。
  市值本身**不在本支算**:交易所收盤 × 交易所股數的檢視表在 VDF_ENG057 v0103(`tw_market_cap_daily`,一個出處)。自測 +⑭⑮。
v0113→v0114(側線 2026-09-24 第四段;主線批號由併線的手指定 L25;操作員令「VDF 加速器跟網路工具都要導入並覆蓋深入所有指令細節動作」):
  L10 央行利率檔(a13rate.xls)與 L11 CNN 恐懼貪婪原本在車道裡**直接** `subprocess.run(["curl", …])`——派工器 run() 有先驗同意閘,
  但連線本身不經統包網路工具(AegisNexus 法遵/限速層都跳過),是全支唯二繞過工具的外呼。v0114 兩處都改走工具的
  `curl_bytes` 車道(SUP_MDL740 v0114 新立;二進位檔與要原樣保留的 JSON 都用位元組道)。工具缺這條車道=誠實 FAIL 講明
  要哪一版,**不退回自己打 curl**。L11 原始 JSON 照舊逐位元保留(操作員令)。自測 +⑫。
  同段第二件(跨引擎實測抓到的回歸,推之前修):`upsert` 原本 `INSERT INTO t SELECT * FROM df`——**照欄位次序**插。
  `tw_trading_daily` 是兩支共用的表(本支 L2 寫最新一天、VDF_ENG057 寫歷史),ENG057 v0102 替它加了開高低三欄之後,
  本支 L2 每一次都炸:`BinderException: table tw_trading_daily has 10 columns but 7 values were supplied`(暫存庫實跑重現,兩種先後都炸)。
  改成**照欄名插入**:表上多的欄補 NULL;這批多出來的欄先照 DuckDB 對 df 推得的型別 ALTER 加上(字串欄不會被加成 DOUBLE)。
  冪等語意不變(鍵已在=不動,anti-join)。L2 同一回包順手收開高低(操作員令「所有數據以交易所為主」;TWSE OpeningPrice/
  HighestPrice/LowestPrice 是樹上 MDL004/MDL007 在用的欄名,TPEX Open/High/Low 容器實量)——ENG057 看到開高低齊的日子就不再重抓那一天。自測 +⑬。
v0112→v0113(側線 2026-09-24 第二段;主線批號由併線的手指定 L25;操作員令「繼續完成」· 九頭龍帳 Z163):
  本支一支就有**六份**民國/緊湊日期換算(`_iso_date` · `_roc_to_iso` 兩個 def,外加 L12 當沖市場級、L15 當沖逐股
  openapi 與 rwd 三處內嵌,和 L10 年月)——期別正典冊說「兩份」,是沒逐行數。前五份改綁正典 SUP_MDL753 v0106(經三庫橋 _LIB):
  `_iso_date = roc_to_iso_keep`(認不出=原值直通,同 v0112)· `_roc_to_iso = roc_to_iso`;三處內嵌改呼叫這兩個綁定。
  跟 v0112 不同的只有兩類,逐式證明在正典自測 ㉟:①不存在的日期不再造(1151301 原樣回;v0112 造出 2026-13-01);
  ②別的形狀正規化成同一個日期(115/9/3 → 2026-09-03;v0112 L12 內嵌轉法遇到七字元斜線會切成 2026-/9-/3)。
  現役形狀(民國七碼 1150923 · 八碼 20260923 · ISO)逐式同答。
  第六處 L10 CBC 民國年月五碼(11508)v0105 正典沒有這個形狀——v0106 正典新增 roc_ym(實作取自 VDF_ENG063 `_roc_ym`,
  有月份/年份範圍檢查;自測 ㊱),本支改呼叫它:月份 13 之類不再造出 2026-13-01 的列(跳過)。十一檢 +⑪。
v0111→v0112(側線 2026-09-24;主線批號由併線的手指定 L25;全景三回第二回實測):L4 etf_book 的 as_of
  改走 _iso_date(TWSE openapi t187ap47_L「出表日期」是民國七碼 1150913)。v0107 的說明宣告 L2/L3/L4 都已
  正規化,實際只改了 L2/L3——L4 從 v0106 到 v0111 六版都原樣落表,工作站 2026-09-24 etf_book 最新值就是
  1150913,目錄與燈號都算不出它的日子。自測 ⑥ 從前餵的正是 1150825,卻只檢 state 與主動旗標,沒檢 as_of
  (LL439:以為有檢,其實沒有)→ ⑥ 補檢落表值=ISO。舊的民國列只增不減照留(不 UPDATE);ISO 字串序大於
  民國七碼,ENG077 取 MAX(as_of) 自然取到新列。其餘一字未動;v0111 留作版史 L04。
v0106→v0107(批151):_iso_date 正規化(QA-20260825C:L2/L3/L4 之 TWSE Date
=ROC 7 碼/緊湊 8 碼混存→統一 ISO;既存列 SQL 遷移)。
v0105→v0106(批147):+L14 Eurostat(歐元區 PPI 年增%=FRED 停更缺口補位;
ISM/S&P PMI=JS 殼或訂閱牆候源;日本 CPI=e-stat 候 appId 註冊)。
v0104→v0105(批146):+L13 FactSet Earnings Insight 掃掘(fwd 12M P/E+
各期 bottom-up EPS+倒推隱含 fwd EPS;PRESS_RELEASE 佐證旗標)。
v0103→v0104(批144):+L12 當沖面(TPEX 市場級統計+TWSE 標的冊;
TWSE 逐股當沖 rwd WAF 死鎖=誠實候源)。
v0102→v0103(批141):+L11 市場情緒(CNN Fear&Greed 官方 API 補 Referer 破
418;原始 JSON 先保留+score 序列入庫;AAII 訂閱牆/akshare 已移除介面=誠實候源)。
v0101→v0102(批139):+L10 臺灣利率(CBC a13rate 臺銀利率史;curl 子程序
道破 TLS 指紋重置;非政策利率誠實旗標);NBS WAF/nstatdb TLS/DGBAS 檔徑=誠實列缺。
v0100→v0101(批138):+L9 跨區宏觀(FRED 活序列 9 條:美歐中 CPI/美 PPI/
美歐日中利率/US10Y;台灣缺口候源誠實列冊)+鑰匙檔後備(.fred_api_key)。
用法:via-omni run [--lane L1,L2,...] | --export fmt | --status | --selftest
v0111(批522 工作站實錄 via-bus one tw_daytrade_stock RED:TWSE-openapi TWTB4U 回的是**標的冊**(鍵 Date/Code/Name/Suspension,無量值);rwd/TPEX 皆 WAF 安全導向):
  L15 三態誠實——openapi=標的冊(只計數不當量值)· rwd/TPEX=WAF 候源 · **檔案收容道**(只收不掛線;律 L45):瀏覽器自 TWSE/TPEX 當沖頁存 CSV/JSON
  → 放 functional modules/VDF/references/intake/daytrade_files/ 或 run --lane L15 --from-file A,B [--date YYYY-MM-DD] [--market TWSE|TPEX];
  表頭關鍵字對映(代號/沖銷成交股數/買進金額/賣出金額)、民國日轉西元、已收檔冊 _ingested.json 不重收;十檢 +⑩。
v0110(批521 L41 當沖量值之源;工作站實錄 via-bus one tw_daytrade_stock RED:TWSE rwd TWTB4U 回安全頁(非 JSON)、TPEX rwd dayTrade 讀逾時):L15 改 openapi 優先
  (https://openapi.twse.com.tw/v1/exchangeReport/TWTB4U:同一支已在 L12 抓標的冊,逐股列以「Volume/股數・Buy/買進・Sell/賣出」鍵防禦對映;鍵名印回 note 供對表),rwd 退路;TPEX 逾時 20s 誠實候源。
v0109(批360/361):L8 us_macro 委派 VDF_ENG074_FredMacroSSOT 尾版(macro SSOT 190 FRED series;從新往舊視窗;checkpoint;accel_map+節流;parquet+DuckDB 同表 us_macro+polars 鏡);ENG074 缺=退內建 16 series 迴圈(誠實 FALLBACK);v0108 零觸碰。
v0108(批330 資料律):+L15 daytrade_stock 個股當沖量(TWSE rwd TWTB4U+TPEX rwd dayTrade;雲端 302=候工作站驗)→tw_daytrade_stock;v0107 零觸碰。
"""
from __future__ import annotations
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from functools import partial as _lb_partial
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import calendar
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"
DB_TW = OUT / "vdf_tw_market.duckdb"
DB_GL = OUT / "vdf_global_market.duckdb"
CKPT = OUT / "omni_checkpoint.json"
START_DATE = "2024-01-02"

# TWSE 產業別代碼冊(官方定義;TPEX 同碼系)
INDUSTRY_MAP = {
    "01": "水泥工業", "02": "食品工業", "03": "塑膠工業", "04": "紡織纖維",
    "05": "電機機械", "06": "電器電纜", "08": "玻璃陶瓷", "09": "造紙工業",
    "10": "鋼鐵工業", "11": "橡膠工業", "12": "汽車工業", "14": "建材營造業",
    "15": "航運業", "16": "觀光餐旅", "17": "金融保險業", "18": "貿易百貨業",
    "19": "綜合", "20": "其他業", "21": "化學工業", "22": "生技醫療業",
    "23": "油電燃氣業", "24": "半導體業", "25": "電腦及週邊設備業",
    "26": "光電業", "27": "通信網路業", "28": "電子零組件業", "29": "電子通路業",
    "30": "資訊服務業", "31": "其他電子業", "32": "文化創意業", "33": "農業科技業",
    "34": "電子商務", "35": "綠能環保", "36": "數位雲端", "37": "運動休閒",
    "38": "居家生活",
}
EP = {
    "twse_listings": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
    "tpex_listings": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",
    "twse_daily": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
    "tpex_daily": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
    "twse_val": "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL",
    "tpex_val": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis",
    "twse_mkt": "https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK",
    "etf_book": "https://openapi.twse.com.tw/v1/opendata/t187ap47_L",
}
# 指數/匯率/區域 ETF 擴編冊(Yahoo 代碼;誠實:Yahoo 缺載即列敗)
IDX_US = ["^GSPC", "^DJI", "^IXIC", "^NDX", "^RUT"]
IDX_ASIA = ["^N225", "^KS11", "^TWII", "^HSI", "000001.SS", "399001.SZ",
            "^STI", "^KLSE", "^JKSE", "PSEI.PS", "^SET.BK"]
IDX_EU = ["^FTSE", "^GDAXI", "^FCHI", "^STOXX50E", "^IBEX", "FTSEMIB.MI",
          "^AEX", "^SSMI"]
IDX_SOUTH_ASIA = ["^NSEI", "^BSESN", "^NSEBANK", "^CNXIT", "^CNX100",
                  "^CNX500", "NIFTY_MIDCAP_100.NS", "^KSE", "^CSE", "^DSEX"]
FX = ["TWD=X", "JPY=X", "KRW=X", "CNY=X", "HKD=X", "SGD=X", "INR=X", "PKR=X",
      "THB=X", "MYR=X", "IDR=X", "PHP=X", "EURUSD=X", "GBPUSD=X", "CHF=X"]
ETF_REGION = ["SPY", "DIA", "QQQ", "IWM", "ONEQ", "EWJ", "EWY", "EWT", "FXI",
              "MCHI", "EWH", "EWS", "EWM", "EIDO", "THD", "INDA", "EPI",
              "EWU", "EWG", "EWQ", "FEZ", "EZU", "EWL", "EWI", "EWP", "VGK"]
ETF_TW_ACTIVE_SUFFIX = ".TW"
# L9 跨區宏觀(FRED 活序列實測 2026-08-25;日本 CPI/歐日中 PPI 已停更、
# 台灣 CPI/PPI/利率 FRED 無=候源 dgbas.gov.tw/cbc.gov.tw 白名單,誠實列缺)
CROSS_SERIES = {
    ("US", "CPI"): "CPIAUCSL", ("EA", "CPI"): "CP0000EZ19M086NEST",
    ("CN", "CPI"): "CHNCPIALLMINMEI",
    ("US", "PPI"): "PPIFIS",
    ("US", "RATE"): "FEDFUNDS", ("EA", "RATE"): "ECBDFR",
    ("JP", "RATE"): "IRSTCI01JPM156N", ("CN", "RATE"): "INTDSRCNM193N",
    ("US", "GOV10Y"): "DGS10",
}
FRED_SERIES = ["CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE", "PPIFIS", "UNRATE",
               "PAYEMS", "ICSA", "CES0500000003", "PI", "DSPIC96", "PCE",
               "RSAFS", "UMCSENT", "HOUST", "DGS20"]


def _net_or_none():
    import glob as _g
    import importlib.util as _il
    hits = sorted(_g.glob(str(VIA / "supportive modules" / "network"
                               / "SUP_MDL740_NetUnified_v*.py")))
    if not hits:
        return None
    spec = _il.spec_from_file_location("via_net_dyn", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["via_net_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod


def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


def write_parquet(rows: list[dict], stem: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        p = OUT / f"{stem}_{ts}.parquet"
        pq.write_table(pa.Table.from_pylist(rows), p)
        return p
    except ImportError:
        import csv
        p = OUT / f"{stem}_{ts}.csv"
        with p.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return p


def upsert(db: Path, table: str, rows: list[dict], keys: list[str]) -> int:
    import duckdb
    import pandas as pd
    df = pd.DataFrame(rows)
    con = duckdb.connect(str(db))
    con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM df LIMIT 0")
    # v0114:照欄名插入(共用表可能比這批多欄,例 tw_trading_daily 經 ENG057 v0102 多開高低);
    #   這批多出來的欄先照 DuckDB 對 df 推得的型別加上——按欄位次序插,表一多欄就 BinderException
    have = {r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()}
    for c, typ in [(r[0], r[1]) for r in con.execute("DESCRIBE SELECT * FROM df").fetchall()]:
        if c not in have:
            con.execute(f'ALTER TABLE {table} ADD COLUMN "{c}" {typ}')
    cols = ", ".join(f'"{c}"' for c in df.columns)
    cond = " AND ".join(f't."{k}" = df."{k}"' for k in keys)
    con.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM df WHERE NOT EXISTS "
                f"(SELECT 1 FROM {table} t WHERE {cond})")
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()
    return n


#: 批597 三庫整併:_num → 正典綁定(純轉換;28 組語料與原實作零差異)。
#  綁定不是 def——再包一層 def 的話能力庫裡那一族還在,家族數不會掉(LL143)。
_num = _LIB.num


#: v0113:ROC/緊湊日期正規化 ISO(QA-20260825C:1150824→2026-08-24;20260824→2026-08-24;認不出=原值直通)
#  改綁正典(VIA_LibCanon 律②:綁定不是 def;逐式四類證明=SUP_MDL753 v0106 自測 ㉟)
_iso_date = _LIB.UTILS.roc_to_iso_keep


#: v0115:發行股數史(交易所給的;市值=交易所收盤×這一欄,算在 ENG057 tw_market_cap_daily)
SHARES_TABLE = "tw_shares_issued"
SHARES_KEYS = ["asof_date", "code", "market"]
SHARES_SRC = {"TWSE": "TWSE_OPENAPI_T187AP03_L", "TPEX": "TPEX_OPENAPI_T187AP03_O"}
TRADING_SRC = {"TWSE": "TWSE_OPENAPI_STOCK_DAY_ALL", "TPEX": "TPEX_OPENAPI_DAILY_CLOSE"}


SNAP_DIR = VIA / "supportive modules" / "VIA_Central_Governance" / "tw_source_snapshots"


def _shares_rows(items, mkt: str, src: str) -> list[dict]:
    """v0115:公司基本資料回包 → 發行股數列(L1 與樹上快照重放共用這一份)。出表日認不出=不收(不猜一個日子)。"""
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        code = str(it.get("公司代號") or it.get("SecuritiesCompanyCode") or "").strip()
        if not (code.isdigit() and len(code) == 4):
            continue
        sh = _num(it.get("已發行普通股數或TDR原股發行股數") or it.get("IssueShares"))
        asof = _iso_date(str(it.get("出表日期") or it.get("Date") or "").strip())
        if sh and sh > 0 and len(asof) == 10 and asof[4] == "-":
            out.append({"asof_date": asof, "code": code, "market": mkt, "shares_issued": sh, "src": src})
    return out


def shares_from_snapshots(snap_dir: Path | None = None) -> dict:
    """v0115:樹上的交易所官方快照(t187ap03_L/_O;批363 存證、可重放)→ tw_shares_issued(src=TREE_SNAPSHOT_…)。
    不觸網、不必同意閘;一份出表日一份,重放冪等。"""
    snap_dir = Path(snap_dir or SNAP_DIR)
    rows, files = [], []
    for mkt, pat, src in (("TWSE", "t187ap03_L_*.json", "TREE_SNAPSHOT_T187AP03_L"),
                          ("TPEX", "t187ap03_O_*.json", "TREE_SNAPSHOT_T187AP03_O")):
        for fp in sorted(snap_dir.glob(pat)):
            try:
                data = json.loads(fp.read_text(encoding="utf-8-sig"))
            except Exception as exc:
                return {"state": "FAIL", "note": f"{fp.name} 讀不開:{type(exc).__name__}"}
            got = _shares_rows(data if isinstance(data, list) else [], mkt, src)
            rows += got
            files.append(f"{fp.name}:{len(got)}")
    if not rows:
        return {"state": "NODATA", "note": f"快照夾沒有可用的 t187ap03 檔:{snap_dir}"}
    n = upsert(DB_TW, SHARES_TABLE, rows, SHARES_KEYS)
    return {"state": "OK", "rows": len(rows), "db": n, "note": " · ".join(files)}


def lane_listings(net) -> dict:
    rows = []
    shares = []                                     # v0115:同一回包的發行股數(以前抓了就丟)
    for mkt, key in (("TWSE", "twse_listings"), ("TPEX", "tpex_listings")):
        r = net.http_json(EP[key])
        if r["state"] != "OK":
            return {"state": r["state"], "note": f"{mkt}:{str(r.get('note',''))[:60]}"}
        for it in r["data"]:
            code = str(it.get("公司代號") or it.get("SecuritiesCompanyCode") or "").strip()
            if not (code.isdigit() and len(code) == 4):
                continue
            ic = str(it.get("產業別") or it.get("SecuritiesIndustryCode") or "").strip().zfill(2)
            rows.append({"code": code,
                         "name": str(it.get("公司簡稱") or it.get("CompanyName") or "").strip(),
                         "market": mkt, "industry_code": ic,
                         "industry_name": INDUSTRY_MAP.get(ic, "未冊碼(誠實)"),
                         "yf_ticker": code + (".TW" if mkt == "TWSE" else ".TWO")})
        shares += _shares_rows(r["data"], mkt, SHARES_SRC[mkt])
    write_parquet(rows, "tw_listings_industry")
    n = upsert(DB_TW, "tw_listings_industry", rows, ["code", "market"])
    if shares:
        upsert(DB_TW, SHARES_TABLE, shares, SHARES_KEYS)
    unk = sum(1 for x in rows if x["industry_name"].startswith("未冊碼"))
    asofs = sorted({x["asof_date"] for x in shares})
    return {"state": "OK", "rows": len(rows), "db": n, "shares": len(shares),
            "note": f"產業附掛;未冊碼 {unk};發行股數 {len(shares)} 檔(出表 {', '.join(asofs) or '—'})"}


def lane_trading(net) -> dict:
    rows = []
    r = net.http_json(EP["twse_daily"])
    if r["state"] == "OK":
        for it in r["data"]:
            rows.append({"date": _iso_date(it.get("Date")), "code": str(it.get("Code")),
                         "market": "TWSE", "volume": _num(it.get("TradeVolume")),
                         "trade_value": _num(it.get("TradeValue")),
                         "transactions": _num(it.get("Transaction")),
                         "close": _num(it.get("ClosingPrice")),
                         "open": _num(it.get("OpeningPrice")),          # v0114:交易所為主,同一回包的開高低一併收
                         "high": _num(it.get("HighestPrice")),
                         "low": _num(it.get("LowestPrice")),
                         "src": TRADING_SRC["TWSE"]})                   # v0115:兩個寫入者,口徑看得出是誰寫的
    r2 = net.http_json(EP["tpex_daily"])
    caps = []                                       # v0115:上櫃每日收盤帶 Capitals(當天發行股數)
    if r2["state"] == "OK":
        for it in r2["data"]:
            code = str(it.get("SecuritiesCompanyCode") or "")
            if not (code.isdigit() and len(code) == 4):
                continue
            rows.append({"date": _iso_date(it.get("Date")), "code": code, "market": "TPEX",
                         "volume": _num(it.get("TradingShares")),
                         "trade_value": _num(it.get("TransactionAmount")),
                         "transactions": _num(it.get("TransactionNumber")),
                         "close": _num(it.get("Close")),
                         "open": _num(it.get("Open")), "high": _num(it.get("High")),   # v0114:交易所為主
                         "low": _num(it.get("Low")), "src": TRADING_SRC["TPEX"]})
            cap, d_ = _num(it.get("Capitals")), rows[-1]["date"]
            if cap and cap > 0 and len(str(d_)) == 10:
                caps.append({"asof_date": d_, "code": code, "market": "TPEX", "shares_issued": cap,
                             "src": "TPEX_OPENAPI_DAILY_CAPITALS"})
    if not rows:
        return {"state": "EMPTY", "note": "雙所零列"}
    write_parquet(rows, "tw_trading_daily")
    n = upsert(DB_TW, "tw_trading_daily", rows, ["date", "code", "market"])
    if caps:
        upsert(DB_TW, SHARES_TABLE, caps, SHARES_KEYS)
    rm = net.http_json(EP["twse_mkt"])
    if rm["state"] == "OK":
        mrows = [{"date": _iso_date(x.get("Date")), "trade_value": _num(x.get("TradeValue")),
                  "volume": _num(x.get("TradeVolume")), "taiex": _num(x.get("TAIEX"))}
                 for x in rm["data"]]
        upsert(DB_TW, "tw_market_agg", mrows, ["date"])
    return {"state": "OK", "rows": len(rows), "db": n, "note": "成交值逐股+市場總計"}


def lane_valuation(net) -> dict:
    rows = []
    r = net.http_json(EP["twse_val"])
    if r["state"] == "OK":
        for it in r["data"]:
            rows.append({"date": _iso_date(it.get("Date")), "code": str(it.get("Code")),
                         "market": "TWSE", "pe": _num(it.get("PEratio")),
                         "pb": _num(it.get("PBratio")),
                         "dividend_yield": _num(it.get("DividendYield")), "dps": None})
    r2 = net.http_json(EP["tpex_val"])
    if r2["state"] == "OK":
        for it in r2["data"]:
            code = str(it.get("SecuritiesCompanyCode") or "")
            if not (code.isdigit() and len(code) == 4):
                continue
            rows.append({"date": _iso_date(it.get("Date")), "code": code, "market": "TPEX",
                         "pe": _num(it.get("PriceEarningRatio")),
                         "pb": _num(it.get("PriceBookRatio")),
                         "dividend_yield": _num(it.get("YieldRatio")),
                         "dps": _num(it.get("DividendPerShare"))})
    if not rows:
        return {"state": "EMPTY", "note": "雙所零列"}
    write_parquet(rows, "tw_valuation_daily")
    n = upsert(DB_TW, "tw_valuation_daily", rows, ["date", "code", "market"])
    return {"state": "OK", "rows": len(rows), "db": n, "note": "PE/PB/殖利率"}


def lane_etf_book(net) -> dict:
    r = net.http_json(EP["etf_book"])
    if r["state"] != "OK":
        return {"state": r["state"], "note": str(r.get("note", ""))[:80]}
    rows = []
    for it in r["data"]:
        name = str(it.get("基金中文名稱") or "")
        rows.append({"fund_code": str(it.get("基金代號") or "").strip(),
                     "fund_name": str(it.get("基金簡稱") or "").strip(),
                     "fund_type": str(it.get("基金類型") or "").strip(),
                     "is_active": ("主動" in name or "主動" in str(it.get("基金簡稱") or "")),
                     "tracking_index": str(it.get("標的指數/追蹤指數名稱") or "").strip(),
                     "as_of": _iso_date(str(it.get("出表日期") or "").strip())})   # v0112:民國七碼→ISO(L4 從前漏了)
    write_parquet(rows, "etf_book")
    n = upsert(DB_TW, "etf_book", rows, ["fund_code", "as_of"])
    act = sum(1 for x in rows if x["is_active"])
    return {"state": "OK", "rows": len(rows), "db": n, "note": f"主動式 {act} 檔旗標"}


def _etf_universe(net) -> list[str]:
    syms = list(ETF_REGION)
    r = net.http_json(EP["etf_book"])
    if r["state"] == "OK":
        for it in r["data"]:
            name = str(it.get("基金中文名稱") or "") + str(it.get("基金簡稱") or "")
            if "主動" in name:
                syms.append(str(it.get("基金代號")).strip() + ETF_TW_ACTIVE_SUFFIX)
    return syms


def lane_etf_stats(net) -> dict:
    if not hasattr(net, "yahoo_quote_summary"):
        return {"state": "SKIP", "note": "統包無 quoteSummary 車道"}
    syms = _etf_universe(net)
    r = net.yahoo_quote_summary(syms)
    if r["state"] != "OK":
        return {"state": r["state"], "note": str(r.get("note", ""))[:80]}
    today = datetime.now().strftime("%Y-%m-%d")
    rows = [{"date": today, **x} for x in r["rows"]]
    write_parquet(rows, "etf_stats_daily")
    n = upsert(DB_GL, "etf_stats_daily", rows, ["date", "symbol"])
    # 流量估算(≥2 快照;ESTIMATE 旗標)
    import duckdb
    con = duckdb.connect(str(DB_GL))
    fl = con.execute("""
        SELECT date, symbol,
               aum - LAG(aum) OVER w * (nav / NULLIF(LAG(nav) OVER w, 0)) AS flow_est
        FROM etf_stats_daily WHERE aum IS NOT NULL AND nav IS NOT NULL
        WINDOW w AS (PARTITION BY symbol ORDER BY date)
    """).fetchall()
    con.close()
    got = sum(1 for x in fl if x[2] is not None)
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": f"AUM 快照 {len(rows)};flow_est 可算 {got}(ESTIMATE;累計快照日增)"}


def lane_global(net) -> dict:
    if not hasattr(net, "yahoo_chart"):
        return {"state": "SKIP", "note": "統包無 chart 車道"}
    syms = sorted(set(IDX_US + IDX_ASIA + IDX_EU + IDX_SOUTH_ASIA + FX + ETF_REGION))
    ck = json.loads(CKPT.read_text(encoding="utf-8")) if CKPT.exists() else {"done": []}
    todo = [s for s in syms if s not in set(ck["done"])]
    se = calendar.timegm(time.strptime(START_DATE, "%Y-%m-%d"))
    total = 0
    failed_all = []
    for i in range(0, len(todo), 40):
        batch = todo[i:i + 40]
        rc = net.yahoo_chart(batch, se, int(time.time()))
        rows = rc.get("rows") or []
        failed_all += [f["ticker"] for f in rc.get("failed") or []]
        if rows:
            write_parquet(rows, "global_expand")
            upsert(DB_GL, "global_daily", rows, ["date", "ticker"])
            total += len(rows)
        ck["done"] = sorted(set(ck["done"]) | {x["ticker"] for x in rows})
        CKPT.write_text(json.dumps(ck, ensure_ascii=False), encoding="utf-8")
    return {"state": "OK" if total else "EMPTY", "rows": total,
            "note": f"擴編 {len(todo)} 標的·敗 {len(set(failed_all))}(Yahoo 缺載誠實列敗)"}


def lane_idx_val(net) -> dict:
    if not hasattr(net, "yahoo_quote_summary"):
        return {"state": "SKIP", "note": "統包無 quoteSummary 車道"}
    r = net.yahoo_quote_summary(ETF_REGION)
    if r["state"] != "OK":
        return {"state": r["state"], "note": str(r.get("note", ""))[:80]}
    today = datetime.now().strftime("%Y-%m-%d")
    rows = [{"date": today, "proxy_flag": "PROXY_ETF", **x} for x in r["rows"]]
    write_parquet(rows, "index_valuation_proxy")
    n = upsert(DB_GL, "index_valuation_proxy", rows, ["date", "symbol"])
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": "區域 ETF 代理估值 [PROXY];FactSet 倒推面候白名單"}


def _fred_key() -> str:
    key = os.environ.get("FRED_API_KEY", "")
    if key:
        return key
    kf = OUT / ".fred_api_key"
    return kf.read_text(encoding="utf-8").strip() if kf.exists() else ""


def _eng074() -> Path | None:
    hits = sorted(HERE.glob("VDF_ENG074_FredMacroSSOT_v*.py"))
    return hits[-1] if hits else None


def lane_us_macro(net) -> dict:
    key = _fred_key()
    if not key:
        return {"state": "SKIP", "note": "FRED_API_KEY 缺=誠實候鑰(單 004 已冊 16 series)"}
    e74 = _eng074()
    if e74 is not None and os.environ.get("VIA_L8_BUILTIN", "") != "1":
        # v0109:委派 ENG074(SSOT 190 series 從新往舊;同表 us_macro;非互動=鑰已在)
        import subprocess
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1"
        r = subprocess.run([sys.executable, str(e74), "run"], env=env, cwd=str(VIA), stdin=subprocess.DEVNULL)
        st = {0: "OK", 3: "SKIP"}.get(r.returncode, "FAIL")
        return {"state": st, "note": f"委派 {e74.name} rc={r.returncode}(SSOT 190 series;從新往舊)"}
    rows = []
    for sid in FRED_SERIES:
        url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
               f"&api_key={key}&file_type=json&observation_start={START_DATE}")
        r = net.http_json(url)
        if r["state"] != "OK":
            continue
        for ob in r["data"].get("observations", []):
            rows.append({"date": ob["date"], "series": sid, "value": _num(ob["value"])})
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    write_parquet(rows, "us_macro")
    n = upsert(DB_GL, "us_macro", rows, ["date", "series"])
    return {"state": "OK", "rows": len(rows), "db": n}


def lane_cross_macro(net) -> dict:
    key = _fred_key()
    if not key:
        return {"state": "SKIP", "note": "FRED_API_KEY 缺=誠實候鑰"}
    rows = []
    for (region, metric), sid in CROSS_SERIES.items():
        url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
               f"&api_key={key}&file_type=json&observation_start=2018-01-01")
        r = net.http_json(url)
        if r["state"] != "OK":
            continue
        for ob in r["data"].get("observations", []):
            v = _num(ob["value"])
            if v is not None:
                rows.append({"date": ob["date"], "region": region, "metric": metric,
                             "series": sid, "value": v})
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    write_parquet(rows, "cross_macro")
    n = upsert(DB_GL, "cross_macro", rows, ["date", "region", "metric"])
    gaps = "TW 三項+JP CPI+EA/JP/CN PPI=FRED 缺/停更,候 dgbas/cbc/stats.gov.cn 白名單"
    return {"state": "OK", "rows": len(rows), "db": n, "note": gaps}


CBC_A13 = "https://www.cbc.gov.tw/public/data/a13rate.xls"


def lane_tw_rates(net) -> dict:
    """L10(v0102;批139):臺灣利率——CBC 臺銀存放款利率史(a13rate.xls)。
    誠實標記:臺銀掛牌利率非央行政策利率;重貼現率檔=CBC 開放資料正確
    檔徑候查(JS 殼頁無法定位)+data.gov.tw/index.dgbas 候白名單。
    CBC 對 urllib/requests TLS 指紋重置=curl 子程序道——v0114 起走統包工具的 curl_bytes 車道(雙閘+法遵在工具裡)。"""
    import tempfile
    if not hasattr(net, "curl_bytes"):
        return {"state": "FAIL", "note": "網路工具缺 curl_bytes 車道(要 SUP_MDL740 v0114+;不自己打 curl)"}
    rb = net.curl_bytes(CBC_A13, timeout=30)
    if rb.get("state") != "OK":
        return {"state": "FAIL" if rb.get("state") != "DENY" else "DENY", "note": f"curl_bytes:{str(rb.get('note', ''))[:80]}"}
    with tempfile.NamedTemporaryFile(suffix=".xls", delete=False) as tf:
        tf.write(rb.get("data") or b"")
        tmp = tf.name
    import pandas as pd
    try:
        df = pd.read_excel(tmp, header=None)
    except Exception as exc:
        return {"state": "FAIL", "note": f"xls 解析:{str(exc)[:80]}"}
    rows = []
    for _, rr in df.iterrows():
        ym = str(rr.iloc[0]).strip()
        if not (ym.isdigit() and len(ym) == 5):
            continue
        yyyymm = _LIB.UTILS.roc_ym(ym)      # v0113:民國年月走正典(月份 13 · 民國 80 年前=None 跳過,不造日期)
        if not yyyymm:
            continue
        rows.append({"date": f"{yyyymm[:4]}-{yyyymm[4:]}-01", "source": "CBC_TAIBANK",
                     "demand_deposit_float": _num(rr.iloc[2]),
                     "savings_float": _num(rr.iloc[4]),
                     "fixed_1m": _num(rr.iloc[5]),
                     "honesty_flag": "臺銀掛牌利率(非央行政策利率;政策利率檔候源)"})
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    write_parquet(rows, "tw_rates_cbc")
    n = upsert(DB_TW, "tw_rates_cbc", rows, ["date", "source"])
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": f"臺銀利率史 {rows[0]['date']}→{rows[-1]['date']}[非政策利率誠實旗標]"}


CNN_FG = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"


def lane_sentiment(net) -> dict:
    """L11(v0103;批141):市場情緒——CNN Fear&Greed 官方 dataviz API
    (418 茶壺擋=補 Referer 瀏覽器頭破;curl 子程序道)。原始 JSON
    先保留(操作員令)+score 序列入庫。AAII=站方訂閱牆 403 誠實候源;
    akshare 現版已移除 aaii/fear_greed 介面(changelog 佐證)。v0114 起走統包工具 curl_bytes(位元組原樣,原始 JSON 照舊逐位元保留)。"""
    if not hasattr(net, "curl_bytes"):
        return {"state": "FAIL", "note": "網路工具缺 curl_bytes 車道(要 SUP_MDL740 v0114+;不自己打 curl)"}
    rb = net.curl_bytes(CNN_FG, timeout=25, follow=False, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://edition.cnn.com/markets/fear-and-greed",
        "Accept": "application/json"})
    body = (rb.get("data") or b"").decode("utf-8", "replace") if rb.get("state") == "OK" else ""
    if rb.get("state") != "OK" or not body.strip().startswith("{"):
        return {"state": "DENY" if rb.get("state") == "DENY" else "FAIL",
                "note": f"CNN F&G 不可達:{(str(rb.get('note', '')) or body)[:60]}"}
    d = json.loads(body)
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / f"cnn_fear_greed_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    raw.write_text(body, encoding="utf-8")   # 先保留原始(操作員令)
    rows = []
    hist = (d.get("fear_and_greed_historical") or {}).get("data") or []
    for x in hist:
        ts = x.get("x")
        if ts is None:
            continue
        rows.append({"date": datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d"),
                     "index": "CNN_FEAR_GREED", "score": x.get("y"),
                     "rating": x.get("rating")})
    now = d.get("fear_and_greed") or {}
    if now.get("score") is not None:
        rows.append({"date": str(now.get("timestamp", ""))[:10],
                     "index": "CNN_FEAR_GREED", "score": now["score"],
                     "rating": now.get("rating")})
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    write_parquet(rows, "sentiment_daily")
    n = upsert(DB_GL, "sentiment_daily", rows, ["date", "index"])
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": f"CNN F&G 今值 {round(float(now.get('score', 0)), 1)}"
                    f"({now.get('rating')});AAII 訂閱牆候源"}


def lane_daytrade(net) -> dict:
    """L12(v0104;批144):當沖面可得極大化——TPEX 市場級當沖統計
    (openapi 月窗)+TWSE 當沖標的冊快照。TWSE 逐股/市場級當沖=
    rwd TWTB4U 遭 WAF 安全頁死鎖(Referer/XHR 頭全試)=誠實候源。"""
    rows = []
    r = net.http_json("https://www.tpex.org.tw/openapi/v1/tpex_intraday_trading_statistics")
    if r["state"] == "OK":
        for it in r["data"]:
            ds = _iso_date(it.get("Date", ""))   # v0113:民國七碼走正典(舊內嵌轉法遇七字元斜線 115/9/3 會切成 2026-/9-/3)
            rows.append({"date": ds, "market": "TPEX",
                         "dt_volume": _num(it.get("DayTradingVolume")),
                         "dt_volume_pct": _num(str(it.get("DayTradingVolumeOfTheMarket", "")).rstrip("%")),
                         "dt_buy_value": _num(it.get("DayTradingValueOfBuys")),
                         "dt_sell_value": _num(it.get("DayTradingValueOfSells"))})
    if not rows:
        return {"state": r["state"] if r["state"] != "OK" else "EMPTY",
                "note": str(r.get("note", "零列"))[:80]}
    write_parquet(rows, "tw_daytrade_market")
    n = upsert(DB_TW, "tw_daytrade_market", rows, ["date", "market"])
    r2 = net.http_json("https://openapi.twse.com.tw/v1/exchangeReport/TWTB4U")
    n2 = 0
    if r2["state"] == "OK":
        el = [{"date": datetime.now().strftime("%Y-%m-%d"),
               "code": str(x.get("Code", "")).strip(),
               "suspension": str(x.get("Suspension", "")).strip()}
              for x in r2["data"] if x.get("Code")]
        if el:
            write_parquet(el, "tw_daytrade_eligible")
            n2 = upsert(DB_TW, "tw_daytrade_eligible", el, ["date", "code"])
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": f"TPEX 市場級 {len(rows)} 日+標的冊 {n2};TWSE 逐股=WAF 候源"}


def _grid_rows(payload) -> list[tuple[list, list]]:
    """rwd JSON 防禦解析:回 [(fields, data)];單表 data/fields 或多表 tables[]"""
    out = []
    if not isinstance(payload, dict):
        return out
    if payload.get("fields") and payload.get("data"):
        out.append((list(payload["fields"]), list(payload["data"])))
    for t in payload.get("tables", []) or []:
        if isinstance(t, dict) and t.get("fields") and t.get("data"):
            out.append((list(t["fields"]), list(t["data"])))
    return out


DAYTRADE_INTAKE = VIA / "functional modules" / "VDF" / "references" / "intake" / "daytrade_files"      # 批522:當沖檔案收容夾(只收不掛線;L45)
DAYTRADE_URLS = ("https://www.twse.com.tw/zh/trading/day-trading/twtb4u.html",
                 "https://www.tpex.org.tw/zh-tw/mainboard/trading/info/day-trading.html")
_FROM_FILES: list = []          # --from-file 明給(main 設)
_FILE_DATE: str | None = None   # --date
_FILE_MARKET: str | None = None  # --market


#: v0113:民國/西元日期字串 → YYYY-MM-DD(114年09月12日 · 114/09/12 · 1140912 · 20250912 · 2025-09-12;認不出=None)
#  改綁正典(舊實作是正典 roc_to_iso 的語料之一;SUP_MDL753 v0106 自測 ㉗)
_roc_to_iso = _LIB.UTILS.roc_to_iso


def _read_text_any(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def parse_daytrade_file(path: Path, date: str | None = None, market: str | None = None) -> tuple[list, str]:
    """批522 檔案收容道:TWSE「當日沖銷交易標的及成交量值」/ TPEX「當日沖銷交易統計」CSV 或 rwd/openapi JSON → rows;表頭以關鍵字對映(不寫死欄序)。
    回 (rows, note)。date 優先序:明給 > 檔名 > 檔內民國日 > 今天(標 note)。market:明給 > 檔名/內容含 tpex/上櫃/櫃買 → TPEX,否則 TWSE。"""
    import csv as _csv
    import io as _io
    import json as _json
    txt = _read_text_any(path)
    name = path.name
    mkt = (market or "").upper() or ("TPEX" if any(k in (name + txt[:400]).lower() for k in ("tpex", "上櫃", "櫃買", "daytrade")) else "TWSE")
    ds = date or _roc_to_iso(name) or _roc_to_iso(txt[:600])
    dnote = "" if ds else "(檔內無日期→今天)"
    ds = ds or datetime.now().strftime("%Y-%m-%d")
    rows: list = []

    def _push(code, vol, buy, sell):
        code = str(code or "").strip().strip('="')
        if len(code) == 4 and code.isdigit():
            rows.append({"date": ds, "code": code, "market": mkt, "dt_volume": _num(vol), "dt_buy_value": _num(buy), "dt_sell_value": _num(sell)})

    st = txt.lstrip()
    if st.startswith("{") or st.startswith("["):
        try:
            payload = _json.loads(st)
        except Exception:
            return [], f"{name}:JSON 解析失敗"
        if isinstance(payload, list):
            keys = list(payload[0].keys()) if payload and isinstance(payload[0], dict) else []

            def _k(*subs):
                for k in keys:
                    if any(x.lower() in k.lower() for x in subs):
                        return k
                return None
            kc, kv, kb, ks = _k("Code", "代號"), _k("Volume", "成交股數", "Shares"), _k("Buy", "買進"), _k("Sell", "賣出")
            if kc and kv:
                for it in payload:
                    _push(it.get(kc), it.get(kv), it.get(kb) if kb else None, it.get(ks) if ks else None)
            return rows, f"{name}:{mkt} {len(rows)} 檔 {ds}{dnote}" + ("" if rows else f"(鍵={keys[:5]} 無代號/量值)")
        for fields, data in _grid_rows(payload):
            fl = [str(f) for f in fields]

            def _ix(*ks_):
                for i, f in enumerate(fl):
                    if all(k in f for k in ks_):
                        return i
                return None
            ic, iv, ib, is_ = _ix("代號"), _ix("沖銷", "成交股數"), _ix("沖銷", "買進"), _ix("沖銷", "賣出")
            if ic is None or iv is None:
                continue
            for row in data:
                _push(row[ic], row[iv], row[ib] if ib is not None else None, row[is_] if is_ is not None else None)
        return rows, f"{name}:{mkt} {len(rows)} 檔 {ds}{dnote}"
    # CSV:找含「代號」與「沖銷」的表頭列
    header, hidx = None, -1
    lines = txt.splitlines()
    for i, ln in enumerate(lines):
        if "代號" in ln and "沖銷" in ln:
            header, hidx = ln, i
            break
    if header is None:
        return [], f"{name}:找不到表頭(需含 代號 與 沖銷)"
    rd = list(_csv.reader(_io.StringIO("\n".join(lines[hidx:]))))
    fl = [c.strip() for c in rd[0]]

    def _cx(*ks_):
        for i, f in enumerate(fl):
            if all(k in f for k in ks_):
                return i
        return None
    ic, iv = _cx("代號"), _cx("沖銷", "成交股數")
    ib, is_ = _cx("沖銷", "買進"), _cx("沖銷", "賣出")
    if ic is None or iv is None:
        return [], f"{name}:表頭無 代號/沖銷成交股數(表頭={fl[:6]})"
    for row in rd[1:]:
        if len(row) <= max(ic, iv):
            continue
        _push(row[ic], row[iv], row[ib] if ib is not None and ib < len(row) else None, row[is_] if is_ is not None and is_ < len(row) else None)
    return rows, f"{name}:{mkt} {len(rows)} 檔 {ds}{dnote}"


def _daytrade_from_files(notes: list) -> list:
    """--from-file 明給的檔,或收容夾內尚未收過的 CSV/JSON(冊 _ingested.json;同檔不重收;--from-file 明給則照收)。"""
    import json as _json
    files = [Path(x) for x in _FROM_FILES if str(x).strip()]
    ledger_p = DAYTRADE_INTAKE / "_ingested.json"
    ledger = {}
    if ledger_p.exists():
        try:
            ledger = _json.loads(ledger_p.read_text(encoding="utf-8"))
        except Exception:
            ledger = {}
    if not files and DAYTRADE_INTAKE.exists():
        for f in sorted(DAYTRADE_INTAKE.iterdir()):
            if f.suffix.lower() in (".csv", ".json") and not f.name.startswith("_"):
                key = f"{f.name}:{f.stat().st_size}"
                if key not in ledger:
                    files.append(f)
    rows: list = []
    for f in files:
        if not f.is_file():
            notes.append(f"檔缺:{f}")
            continue
        try:
            got, note = parse_daytrade_file(f, _FILE_DATE, _FILE_MARKET)
        except Exception as exc:
            got, note = [], f"{f.name}:解析例外 {type(exc).__name__}"
        rows += got
        notes.append("檔案:" + note)
        if got and DAYTRADE_INTAKE.exists() and f.parent == DAYTRADE_INTAKE:
            ledger[f"{f.name}:{f.stat().st_size}"] = {"rows": len(got), "ts": datetime.now().isoformat(timespec="seconds")}
    if ledger and DAYTRADE_INTAKE.exists():
        try:
            ledger_p.write_text(_json.dumps(ledger, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        except Exception:
            pass
    return rows


def lane_daytrade_stock(net) -> dict:
    """L15(v0108;批330 資料律):個股當沖成交量——TWSE rwd TWTB4U(selectType=All)+TPEX rwd dayTrade
    逐股日表→tw_daytrade_stock(date, code, market, dt_volume, dt_buy_value, dt_sell_value)。
    雲端實錄兩源皆 302(WAF/導向)=誠實 FAIL 候工作站驗;欄位以標頭關鍵字對映(防禦式)。"""
    today = datetime.now()
    rows, notes = [], []
    # 批521:openapi 優先(工作站可達;rwd 回 WAF 安全頁)。逐股列鍵名不寫死:含 Volume/股數 → dt_volume;Buy/買進 → 買進金額;Sell/賣出 → 賣出金額;Date(民國 yyymmdd)→ 西元。
    r0 = net.http_json("https://openapi.twse.com.tw/v1/exchangeReport/TWTB4U")
    if r0["state"] == "OK" and isinstance(r0["data"], list) and r0["data"]:
        keys = list(r0["data"][0].keys()) if isinstance(r0["data"][0], dict) else []
        def _k(*subs):
            for k in keys:
                lk = k.lower()
                if any(s.lower() in lk for s in subs):
                    return k
            return None
        kc, kv = _k("Code", "代號"), _k("Volume", "成交股數", "Shares")
        kb, ks, kd = _k("Buy", "買進"), _k("Sell", "賣出"), _k("Date", "日期")
        got = 0
        if kc and kv:
            for it in r0["data"]:
                code = str(it.get(kc, "")).strip()
                if not (len(code) == 4 and code.isdigit()):
                    continue
                ds = (_roc_to_iso(it.get(kd, "")) if kd else None) or today.strftime("%Y-%m-%d")   # v0113:七/八碼走正典;認不出照舊用今天
                rows.append({"date": ds, "code": code, "market": "TWSE", "dt_volume": _num(it.get(kv)),
                             "dt_buy_value": _num(it.get(kb)) if kb else None, "dt_sell_value": _num(it.get(ks)) if ks else None})
                got += 1
        notes.append(f"TWSE-openapi:{got} 檔" if got else f"TWSE-openapi=標的冊 {len(r0['data'])} 檔無量值(鍵={keys[:4]};量值走檔案收容道)")
    else:
        notes.append(f"TWSE-openapi:{r0['state']} {str(r0.get('note', ''))[:40]}")
    srcs = [("TWSE", f"https://www.twse.com.tw/rwd/zh/afterTrading/TWTB4U?date={today:%Y%m%d}&selectType=All&response=json"),
            ("TPEX", f"https://www.tpex.org.tw/www/zh-tw/intraday/dayTrade?date={today:%Y/%m/%d}&type=Daily&id=&response=json")]
    if any(r["market"] == "TWSE" for r in rows):
        srcs = [s for s in srcs if s[0] != "TPEX"] and [s for s in srcs if s[0] == "TPEX"]   # TWSE 已由 openapi 取得 → 只剩 TPEX
    for mkt, url in srcs:
        r = net.http_json(url)
        if r["state"] != "OK":
            notes.append(f"{mkt}:{r['state']} {str(r.get('note', ''))[:40]}")
            continue
        got = 0
        for fields, data in _grid_rows(r["data"]):
            fl = [str(f) for f in fields]
            def _ix(*keys):
                for i, f in enumerate(fl):
                    if all(k in f for k in keys):
                        return i
                return None
            ic, iv = _ix("代號"), _ix("沖銷", "成交股數")
            ib, is_ = _ix("沖銷", "買進", "金額"), _ix("沖銷", "賣出", "金額")
            if ic is None or iv is None:
                continue
            ds = _iso_date(r["data"].get("date", f"{today:%Y%m%d}"))   # v0113:八碼走正典(認不出=原值,同舊)
            for row in data:
                code = str(row[ic]).strip()
                if not (len(code) == 4 and code.isdigit()):
                    continue
                rows.append({"date": ds, "code": code, "market": mkt, "dt_volume": _num(row[iv]),
                             "dt_buy_value": _num(row[ib]) if ib is not None else None,
                             "dt_sell_value": _num(row[is_]) if is_ is not None else None})
                got += 1
        notes.append(f"{mkt}:{got} 檔" if got else f"{mkt}:表頭無「代號/沖銷成交股數」(格式候驗)")
    rows += _daytrade_from_files(notes)          # 批522:檔案收容道(只收不掛線;L45)
    if not rows:
        return {"state": "FAIL", "note": ("個股當沖零列=" + " · ".join(notes))[:400],
                "hint": f"量值在交易所網頁(python 客戶端被 WAF 擋):瀏覽器開 {DAYTRADE_URLS[0]} / {DAYTRADE_URLS[1]} 存 CSV → 放 {DAYTRADE_INTAKE} 或 run --lane L15 --from-file A,B --date YYYY-MM-DD"}
    write_parquet(rows, "tw_daytrade_stock")
    n = upsert(DB_TW, "tw_daytrade_stock", rows, ["date", "code"])
    return {"state": "OK", "rows": len(rows), "db": n, "note": " · ".join(notes)[:100]}


FS_TOPIC = "https://insight.factset.com/topic/earnings"
# 距離類不可用 [^.](小數點誤截,QA-20260825B):改惰性任意窗
FS_PE_RX = re.compile(r"forward 12-month P/E ratio.{0,80}?(\d{1,2}\.\d)", re.I)
FS_EPS_RX = re.compile(r"(Q[1-4]|CY\s?20\d{2})\s+bottom-up EPS estimate.{0,220}?"
                       r"\$(\d{2,3}\.\d{2})", re.I)
FS_DATE_RX = re.compile(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})')


def _factset_sources() -> set:
    """v0116:factset_earnings 已有的文章網址(先查庫缺啥);庫/表不在=空集合。"""
    try:
        import duckdb
    except ImportError:
        return set()
    if not Path(DB_GL).exists():
        return set()
    con = duckdb.connect(str(DB_GL), read_only=True)
    try:
        if "factset_earnings" not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            return set()
        return {r[0] for r in con.execute("SELECT DISTINCT source FROM factset_earnings WHERE source IS NOT NULL").fetchall()}
    finally:
        con.close()


def lane_factset(net) -> dict:
    """L13(v0105;批146):FactSet Earnings Insight 新聞稿掃掘(批137
    操作員令:每月新聞稿可倒推本益比)。萃取 forward 12M P/E 與各期
    bottom-up EPS;倒推=fwd_eps_implied=GSPC 收盤/fwd_pe(有 P/E 時)
    或 pe_implied=GSPC/EPS×係數面候算 [PRESS_RELEASE 佐證誠實旗標]。"""
    # v0116:外呼走統包 curl_bytes(v0115 以前問完「有沒有 curl 車道」就自己開 curl 子行程——連線不經工具)
    if not hasattr(net, "curl_bytes"):
        return {"state": "FAIL", "note": "網路工具缺 curl_bytes 車道(要 SUP_MDL740 v0114+;不自己打 curl)"}
    last: dict = {}

    def fetch(url):
        r = net.curl_bytes(url, timeout=25)
        last["state"], last["note"] = r.get("state"), str(r.get("note", ""))[:80]
        return (r.get("data") or b"").decode("utf-8", "replace") if r.get("state") == "OK" else ""

    listing = fetch(FS_TOPIC)
    if last.get("state") != "OK":                    # 沒連上就照實講(閘關 DENY / 傳輸 FAIL),不說成「版式變了」
        return {"state": last.get("state") or "FAIL", "note": f"清單頁:{last.get('note', '')}"}
    arts = sorted(set(re.findall(
        r'href="(https://insight\.factset\.com/[a-z0-9-]{15,})"', listing)))
    arts = [a for a in arts if "/author/" not in a and "/topic/" not in a][:6]
    have = _factset_sources()                        # v0116:先查庫缺啥——已在庫的文章不重抓
    todo = [a for a in arts if a not in have]
    rows = []
    for url in todo:
        h = fetch(url)
        if not h:
            continue
        text = re.sub(r"<[^>]+>", " ", h)
        text = re.sub(r"\s+", " ", text)
        dm = FS_DATE_RX.search(h)
        pub = dm.group(1) if dm else None
        for m in FS_PE_RX.finditer(text):
            rows.append({"published": pub, "metric": "SPX_FWD_PE_12M",
                         "period": "NTM", "value": float(m.group(1)),
                         "source": url, "flag": "PRESS_RELEASE"})
        for m in FS_EPS_RX.finditer(text):
            rows.append({"published": pub, "metric": "SPX_BOTTOMUP_EPS",
                         "period": m.group(1).replace(" ", ""),
                         "value": float(m.group(2)),
                         "source": url, "flag": "PRESS_RELEASE"})
    if not rows:
        if arts and not todo:
            return {"state": "OK", "rows": 0, "db": len(have), "note": f"清單 {len(arts)} 篇全已在庫(不重抓)"}
        return {"state": "EMPTY", "note": f"掃 {len(todo)} 文零萃取(已在庫略過 {len(arts) - len(todo)};版式變?誠實)"}
    # 去重(published×metric×period×value)
    seen, uniq = set(), []
    for r_ in rows:
        k = (r_["published"], r_["metric"], r_["period"], r_["value"])
        if k not in seen:
            seen.add(k)
            uniq.append(r_)
    write_parquet(uniq, "factset_earnings")
    n = upsert(DB_GL, "factset_earnings", uniq, ["published", "metric", "period", "value"])
    # 倒推:最近 fwd_pe × GSPC 收盤 → 隱含 fwd EPS
    derived = ""
    pes = [r_ for r_ in uniq if r_["metric"] == "SPX_FWD_PE_12M" and r_["published"]]
    if pes:
        latest = max(pes, key=lambda x: x["published"])
        import duckdb
        con = duckdb.connect(str(DB_GL), read_only=True)
        px = con.execute("SELECT adj_close FROM global_daily WHERE ticker='^GSPC' "
                         "AND date<=? ORDER BY date DESC LIMIT 1",
                         [latest["published"]]).fetchone()
        con.close()
        if px:
            fwd_eps = round(px[0] / latest["value"], 2)
            upsert(DB_GL, "factset_earnings",
                   [{"published": latest["published"], "metric": "SPX_FWD_EPS_IMPLIED",
                     "period": "NTM", "value": fwd_eps,
                     "source": latest["source"], "flag": "DERIVED=price/fwd_pe"}],
                   ["published", "metric", "period", "value"])
            derived = f"·倒推 fwd EPS {fwd_eps}(@{latest['published']})"
    if not pes:
        cys = [r_ for r_ in uniq if r_["metric"] == "SPX_BOTTOMUP_EPS"
               and str(r_["period"]).startswith("CY") and r_["published"]]
        if cys:
            latest = max(cys, key=lambda x: (x["published"], x["period"]))
            import duckdb
            con = duckdb.connect(str(DB_GL), read_only=True)
            px = con.execute("SELECT adj_close, date FROM global_daily WHERE ticker='^GSPC' "
                             "ORDER BY date DESC LIMIT 1").fetchone()
            con.close()
            if px:
                pe = round(px[0] / latest["value"], 2)
                upsert(DB_GL, "factset_earnings",
                       [{"published": px[1], "metric": "SPX_PE_IMPLIED",
                         "period": latest["period"], "value": pe,
                         "source": latest["source"],
                         "flag": f"DERIVED=price/{latest['period']}_EPS(倒推本益比)"}],
                       ["published", "metric", "period", "value"])
                derived = f"·倒推 P/E {pe}(GSPC@{px[1]}/{latest['period']} EPS)"
    eps_n = sum(1 for r_ in uniq if r_["metric"] == "SPX_BOTTOMUP_EPS")
    pe_n = len(pes)
    return {"state": "OK", "rows": len(uniq), "db": n,
            "note": f"掃 {len(arts)} 文·fwd P/E {pe_n}·EPS {eps_n}{derived}"}


EUROSTAT_PPI = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/"
                "data/sts_inppd_m?format=JSON&lang=EN&geo=EA20&sinceTimePeriod=2018-01"
                "&nace_r2=B-E36&unit=PCH_SM&indic_bt=PRC_PRR_DOM&s_adj=NSA")


def lane_eurostat(net) -> dict:
    """L14(v0106;批147):Eurostat 官方 API——歐元區 PPI 年增%(工業
    B-E36 國內市場;FRED 停更缺口補位)→ cross_macro(region=EA,
    metric=PPI)。JSON-stat 單變動維=time 直映。"""
    r = net.http_json(EUROSTAT_PPI)
    if r["state"] != "OK":
        return {"state": r["state"], "note": str(r.get("note", ""))[:80]}
    d = r["data"]
    tidx = d["dimension"]["time"]["category"]["index"]
    vals = d.get("value", {})
    rows = []
    for period, i in tidx.items():
        v = vals.get(str(i))
        if v is None:
            continue
        rows.append({"date": f"{period}-01", "region": "EA", "metric": "PPI",
                     "series": "eurostat:sts_inppd_m:PCH_SM", "value": float(v)})
    if not rows:
        return {"state": "EMPTY", "note": "零列(維度組合驗證失效?誠實)"}
    write_parquet(rows, "cross_macro_ea_ppi")
    n = upsert(DB_GL, "cross_macro", rows, ["date", "region", "metric"])
    return {"state": "OK", "rows": len(rows), "db": n,
            "note": f"EA PPI 年增% {rows[0]['date'][:7]}→{rows[-1]['date'][:7]}"}


LANES = {"L1": ("listings", lane_listings), "L2": ("trading", lane_trading),
         "L3": ("valuation", lane_valuation), "L4": ("etf_book", lane_etf_book),
         "L5": ("etf_stats", lane_etf_stats), "L6": ("global", lane_global),
         "L7": ("idx_val", lane_idx_val), "L8": ("us_macro", lane_us_macro), "L9": ("cross_macro", lane_cross_macro), "L10": ("tw_rates", lane_tw_rates), "L11": ("sentiment", lane_sentiment), "L12": ("daytrade", lane_daytrade), "L13": ("factset", lane_factset), "L14": ("eurostat", lane_eurostat),
         "L15": ("daytrade_stock", lane_daytrade_stock)}


def run(sel: list[str] | None) -> int:
    if not gate_open():
        print("[FAIL-CLOSED] 同意閘未開(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT)")
        return 2
    net = _net_or_none()
    if net is None:
        print("[FAIL] 統包網路工具缺席")
        return 1
    sel = sel or list(LANES)
    print(f"=== 單 004 總擷取(批137)· 車道 {','.join(sel)} ===")
    bad = 0
    for k in sel:
        name, fn = LANES[k]
        try:
            r = fn(net)
        except Exception as exc:
            r = {"state": "FAIL", "note": str(exc)[:100]}
        if r["state"] == "FAIL":
            bad += 1
        print(f"  [{r['state']:<5}] {k} {name:<10} {r.get('rows', '')} "
              f"{str(r.get('note', ''))[:84]}", flush=True)
    return 1 if bad else 0


def export(fmt: str) -> int:
    import duckdb
    dest = OUT / "export"
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for db in (DB_TW, DB_GL):
        if not db.exists():
            continue
        con = duckdb.connect(str(db), read_only=True)
        for (t,) in con.execute("SHOW TABLES").fetchall():
            df = con.execute(f"SELECT * FROM {t}").df()
            if fmt == "parquet":
                df.to_parquet(dest / f"{db.stem}_{t}.parquet")
            elif fmt in ("csv", "gsheet"):
                df.to_csv(dest / f"{db.stem}_{t}.csv", index=False,
                          encoding="utf-8-sig")  # gsheet 相容=utf-8-sig csv
            elif fmt == "sqlite":
                import sqlite3
                sq = sqlite3.connect(dest / f"{db.stem}.sqlite")
                df.to_sql(t, sq, if_exists="replace", index=False)
                sq.close()
            n += 1
        con.close()
    print(f"[export] {fmt} × {n} 表 → {dest.relative_to(VDF)}")
    return 0


def status() -> int:
    import duckdb
    for db in (DB_TW, DB_GL):
        if not db.exists():
            print(f"[{db.name}] 缺")
            continue
        con = duckdb.connect(str(db), read_only=True)
        print(f"[{db.name}]")
        for (t,) in con.execute("SHOW TABLES").fetchall():
            c = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t}: {c}")
        con.close()
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 同意閘 fail-closed", not gate_open({}) and gate_open(
        {"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}))
    net = _net_or_none()
    chk("② 統包三車道在位(http_json/yahoo_chart/quoteSummary)",
        net is not None and all(hasattr(net, x) for x in
                                ("http_json", "yahoo_chart", "yahoo_quote_summary")))
    chk("③ 產業冊+半導體=24", INDUSTRY_MAP["24"] == "半導體業"
        and INDUSTRY_MAP["17"] == "金融保險業")
    chk("④ 擴編冊(美5·亞11·歐8·南亞10·匯15·ETF26)",
        len(IDX_US) == 5 and len(IDX_ASIA) == 11 and len(IDX_EU) == 8
        and len(IDX_SOUTH_ASIA) == 10 and len(FX) == 15 and len(ETF_REGION) == 26)
    global OUT, DB_TW, DB_GL, CKPT
    _s = (OUT, DB_TW, DB_GL, CKPT)
    with tempfile.TemporaryDirectory() as td:
        OUT, DB_TW, DB_GL, CKPT = (Path(td), Path(td) / "tw.duckdb",
                                   Path(td) / "gl.duckdb", Path(td) / "ck.json")

        class FakeNet:
            @staticmethod
            def http_json(url):
                if "t187ap03_L" in url:
                    return {"state": "OK", "data": [{"公司代號": "2330", "公司簡稱": "台積電", "產業別": "24"}]}
                if "mopsfin" in url:
                    return {"state": "OK", "data": [{"SecuritiesCompanyCode": "5483",
                                                    "CompanyName": "中美晶", "SecuritiesIndustryCode": "24"}]}
                if "t187ap47_L" in url:
                    return {"state": "OK", "data": [{"基金代號": "00981A", "基金簡稱": "主動統一台股增長",
                                                    "基金類型": "ETF", "基金中文名稱": "統一台股增長主動式ETF",
                                                    "標的指數/追蹤指數名稱": "-", "出表日期": "1150825"}]}
                return {"state": "FAIL", "note": "no-net"}

        r1 = lane_listings(FakeNet)
        chk("⑤ L1 清單附產業(雙所+產業名對映)", r1["state"] == "OK" and r1["rows"] == 2)
        r4 = lane_etf_book(FakeNet)
        import duckdb as _ddb
        _c = _ddb.connect(str(DB_TW))
        _asof = [a for (a,) in _c.execute("SELECT as_of FROM etf_book").fetchall()]
        _c.close()
        chk("⑥ L4 ETF 冊+主動旗標+出表日期民國七碼→ISO(v0112;從前只檢 state,1150825 原樣落表也綠)",
            r4["state"] == "OK" and "主動式 1 檔" in r4["note"] and _asof == ["2026-08-25"], f"(as_of {_asof})")
        rows = [{"date": "2026-08-25", "symbol": "SPY", "aum": 1.0, "nav": 1.0}]
        n1 = upsert(DB_GL, "t", rows, ["date", "symbol"])
        n2 = upsert(DB_GL, "t", rows, ["date", "symbol"])
        chk("⑦ upsert 冪等(累計維護)", n1 == 1 and n2 == 1)
    OUT, DB_TW, DB_GL, CKPT = _s
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 韌性+誠實宣告(checkpoint/批次落盤/ESTIMATE/PROXY/候鑰)",
        all(x in src for x in ("checkpoint", "ESTIMATE", "PROXY", "候鑰", "utf-8-sig")))
    chk("⑨ L8 委派律(ENG074 尾版 glob;缺=內建 16 FALLBACK;VIA_L8_BUILTIN=1 強制內建)",
        "VDF_ENG074_FredMacroSSOT_v*.py" in src and "VIA_L8_BUILTIN" in src and len(FRED_SERIES) == 16)
    with tempfile.TemporaryDirectory() as td10:
        T10 = Path(td10)
        (T10 / "TWTB4U_20250912.csv").write_text("\ufeff\"114年09月12日 當日沖銷交易標的及成交量值\"\n\"證券代號\",\"證券名稱\",\"暫停現股賣出後現款買進當沖註記\",\"當日沖銷交易成交股數\",\"當日沖銷交易買進成交金額\",\"當日沖銷交易賣出成交金額\"\n\"2330\",\"台積電\",\"\",\"12,345,000\",\"1,234,500,000\",\"1,230,000,000\"\n\"0050\",\"元大台灣50\",\"\",\"100\",\"20,000\",\"20,100\"\n\"說明\",\"x\"\n", encoding="utf-8")
        (T10 / "tpex_daytrade.csv").write_text("代號,名稱,當日沖銷交易成交股數,當日沖銷交易買進成交金額,當日沖銷交易賣出成交金額\n6488,環球晶,\"55,000\",\"30,000,000\",\"29,500,000\"\n", encoding="utf-8")
        (T10 / "openapi_like.json").write_text('[{"Date":"1140912","Code":"2317","Name":"鴻海","DayTradingVolume":"9,000","DayTradingValueOfBuys":"1,800,000","DayTradingValueOfSells":"1,790,000"}]', encoding="utf-8")
        r1, n1 = parse_daytrade_file(T10 / "TWTB4U_20250912.csv")
        r2, n2 = parse_daytrade_file(T10 / "tpex_daytrade.csv", date="2025-09-12")
        r3, n3 = parse_daytrade_file(T10 / "openapi_like.json", date="2025-09-12", market="TWSE")
        _FROM_FILES[:] = [str(T10 / "TWTB4U_20250912.csv"), str(T10 / "nope.csv")]
        notes10: list = []
        rf = _daytrade_from_files(notes10)
        _FROM_FILES[:] = []
    chk("⑩ 批522 當沖檔案收容道(只收不掛線;L45):TWSE CSV 表頭關鍵字對映+民國日→西元+千分位+非四碼列丟;TPEX CSV 市場自檔名;openapi 型 JSON 鍵對映;--from-file 缺檔=note 不炸",
        len(r1) == 2 and r1[0]["date"] == "2025-09-12" and r1[0]["dt_volume"] == 12345000 and r1[0]["dt_buy_value"] == 1234500000 and r1[0]["market"] == "TWSE"
        and len(r2) == 1 and r2[0]["market"] == "TPEX" and r2[0]["code"] == "6488" and r2[0]["dt_volume"] == 55000
        and len(r3) == 1 and r3[0]["code"] == "2317" and r3[0]["dt_volume"] == 9000
        and len(rf) == 2 and any("檔缺" in n for n in notes10) and _roc_to_iso("1140912") == "2025-09-12" and _roc_to_iso("2026-09-12") == "2026-09-12",
        f"({n1} | {n2} | {n3})")
    # ── v0113 ⑪:六處民國/緊湊日期改綁正典(Z163;FakeNet 零網路;收容夾換空夾)──
    import inspect as _insp
    global DAYTRADE_INTAKE
    _s11 = (OUT, DB_TW, DB_GL, CKPT, DAYTRADE_INTAKE)
    with tempfile.TemporaryDirectory() as td11:
        OUT, DB_TW, DB_GL, CKPT = Path(td11), Path(td11) / "tw.duckdb", Path(td11) / "gl.duckdb", Path(td11) / "ck.json"
        DAYTRADE_INTAKE = Path(td11) / "intake_empty"   # 自測不得把工作站收容夾的真檔記成「已收」(ledger 會寫)

        class FakeNet11:
            @staticmethod
            def http_json(url):
                if "tpex_intraday_trading_statistics" in url:
                    return {"state": "OK", "data": [{"Date": "1150923", "DayTradingVolume": "1,000"},
                                                    {"Date": "115/9/3", "DayTradingVolume": "900"}]}   # 形狀防禦(非實錄)
                if "exchangeReport/TWTB4U" in url:
                    return {"state": "OK", "data": [{"Date": "1150923", "Code": "2330", "Name": "台積電", "DayTradingVolume": "2,000",
                                                    "DayTradingValueOfBuys": "3,000", "DayTradingValueOfSells": "2,900"}]}
                if "tpex.org.tw/www" in url:
                    return {"state": "OK", "data": {"date": "20260923", "fields": ["代號", "名稱", "當日沖銷交易成交股數",
                            "當日沖銷交易買進成交金額", "當日沖銷交易賣出成交金額"], "data": [["6488", "環球晶", "55,000", "30,000,000", "29,500,000"]]}}
                return {"state": "FAIL", "note": "no-net"}

        r12, r15 = lane_daytrade(FakeNet11), lane_daytrade_stock(FakeNet11)
        import duckdb as _ddb11
        _c = _ddb11.connect(str(DB_TW), read_only=True)
        d12 = sorted(x for (x,) in _c.execute("SELECT date FROM tw_daytrade_market").fetchall())
        d15 = sorted(tuple(r) for r in _c.execute("SELECT date, code, market FROM tw_daytrade_stock").fetchall())
        _c.close()
        _intake_untouched = not DAYTRADE_INTAKE.exists()
    OUT, DB_TW, DB_GL, CKPT, DAYTRADE_INTAKE = _s11
    _lanes_src = (_insp.getsource(lane_daytrade) + _insp.getsource(lane_daytrade_stock) + _insp.getsource(lane_trading)
                  + _insp.getsource(lane_valuation) + _insp.getsource(lane_tw_rates))
    chk("⑪ v0113 六處民國/緊湊日期改綁正典:_iso_date/_roc_to_iso 就是正典物件(綁定不是 def);L12 民國七碼與七字元斜線皆成 ISO、"
        "L15 openapi 七碼與 rwd 八碼皆成 ISO;現役形狀同 v0112(1150824 · 20260824 · ISO);不存在的日期不造(1151301 原樣回);"
        "五條車道(L2 · L3 · L10 · L12 · L15)原始碼零民國加法;自測收容夾換空夾(真收容夾零觸碰)",
        _iso_date is _LIB.UTILS.roc_to_iso_keep and _roc_to_iso is _LIB.UTILS.roc_to_iso
        and r12.get("state") == "OK" and d12 == ["2026-09-03", "2026-09-23"]
        and r15.get("state") == "OK" and d15 == [("2026-09-23", "2330", "TWSE"), ("2026-09-23", "6488", "TPEX")]
        and [_iso_date(x) for x in ("1150824", "20260824", "2026-08-24", "")] == ["2026-08-24", "2026-08-24", "2026-08-24", ""]
        and _iso_date("1151301") == "1151301" and "1911" not in _lanes_src and _intake_untouched,
        f"(L12 {d12} · L15 {d15} · {r12.get('state')}/{r15.get('state')})")
    # ── v0114 ⑫:L10/L11 外呼走統包工具 curl_bytes(FakeNet 零網路;庫與輸出夾換暫存)──
    _s12 = (OUT, DB_TW, DB_GL, CKPT)
    try:
        import openpyxl as _ox12
        import io as _io12
        _wb = _ox12.Workbook()
        _ws = _wb.active
        for _row in (["年月", "x", "活期存款", "x", "活儲", "一月期"], ["11507", "", 0.715, "", 0.845, 1.495],
                     ["11508", "", 0.715, "", 0.845, 1.495], ["11513", "", 9, "", 9, 9]):
            _ws.append(_row)
        _bio = _io12.BytesIO()
        _wb.save(_bio)
        _xls = _bio.getvalue()
    except Exception:
        _xls = None
    # 回包排版刻意不是 json.dumps 的樣子(無空白、鍵序不同)——「原始逐位元保留」重新序列化就會對不上
    _cnn = (b'{"fear_and_greed_historical":{"data":[{"y":50.1,"x":1789257600000,"rating":"neutral"}]},'
            b'"fear_and_greed":{"rating":"greed","score":55.4,"timestamp":"2026-09-24T00:00:00"}}')
    _calls12 = []

    class FakeNet12:
        @staticmethod
        def curl_bytes(url, headers=None, timeout=30, follow=True):
            _calls12.append((url, bool(headers), follow))
            if "cbc.gov.tw" in url:
                return {"state": "OK", "data": _xls, "via": "curl"} if _xls else {"state": "FAIL", "note": "no-xlsx-lib"}
            if "cnn.io" in url:
                return {"state": "OK", "data": _cnn, "via": "curl"}
            return {"state": "FAIL", "note": "no-net"}

    class OldNet12:                       # 舊版工具(沒有 curl_bytes)
        pass

    with tempfile.TemporaryDirectory() as td12:
        OUT, DB_TW, DB_GL, CKPT = Path(td12), Path(td12) / "tw.duckdb", Path(td12) / "gl.duckdb", Path(td12) / "ck.json"
        try:
            r10, r11 = lane_tw_rates(FakeNet12), lane_sentiment(FakeNet12)
            o10, o11 = lane_tw_rates(OldNet12), lane_sentiment(OldNet12)
            raw11 = sorted(Path(td12).glob("cnn_fear_greed_raw_*.json"))
            raw_ok = bool(raw11) and raw11[-1].read_bytes() == _cnn
        finally:
            OUT, DB_TW, DB_GL, CKPT = _s12
    _src12 = _insp.getsource(lane_tw_rates) + _insp.getsource(lane_sentiment)
    chk("⑫ v0114 L10/L11 外呼走統包工具 curl_bytes(不再自己 subprocess curl):L10 xls 位元組 → 兩個月入庫(民國 11513 月份 13 跳過)、"
        "L11 JSON 入庫且原始檔逐位元同;工具缺 curl_bytes=誠實 FAIL 講明要哪一版(不退回自己打 curl);兩條車道原始碼零 subprocess",
        (_xls is None or (r10.get("state") == "OK" and r10.get("rows") == 2)) and r11.get("state") == "OK" and raw_ok
        and o10.get("state") == "FAIL" and "curl_bytes" in o10.get("note", "") and o11.get("state") == "FAIL"
        and "subprocess" not in _src12 and len(_calls12) == 2 and _calls12[1][1] is True and _calls12[1][2] is False,
        f"(L10 {r10.get('state')} {r10.get('rows')} · L11 {r11.get('state')} {r11.get('rows')} · 原始同 {raw_ok} · 舊工具 {o10.get('state')}/{o11.get('state')})")
    # ── v0114 ⑬:共用表多欄不炸(照欄名插入)· 新欄照型別加 · L2 收開高低(暫存庫;FakeNet 零網路)──
    _s13 = (OUT, DB_TW, DB_GL, CKPT)
    _e13 = ""
    try:
        import duckdb as _ddb13
        with tempfile.TemporaryDirectory() as td13:
            OUT, DB_TW, DB_GL, CKPT = Path(td13), Path(td13) / "tw.duckdb", Path(td13) / "gl.duckdb", Path(td13) / "ck.json"
            _c13 = _ddb13.connect(str(DB_TW))            # 照 ENG057 v0102 的樣子先建:十欄(多開高低)
            _c13.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, volume DOUBLE, "
                         "trade_value DOUBLE, transactions DOUBLE, close DOUBLE, open DOUBLE, high DOUBLE, low DOUBLE)")
            _c13.execute("INSERT INTO tw_trading_daily VALUES ('2026-09-23','2330','TWSE',1,2,3,2500,2475,2505,2475)")
            _c13.close()
            _n13a = upsert(DB_TW, "tw_trading_daily", [{"date": "2026-09-22", "code": "2330", "market": "TWSE",
                                                        "volume": 1.0, "trade_value": 2.0, "transactions": 3.0,
                                                        "close": 2490.0}], ["date", "code", "market"])
            _n13b = upsert(DB_TW, "tw_trading_daily", [{"date": "2026-09-22", "code": "2330", "market": "TWSE",
                                                        "volume": 9.0, "trade_value": 9.0, "transactions": 9.0,
                                                        "close": 9.0, "src": "X"}], ["date", "code", "market"])
            _n13c = upsert(DB_TW, "tw_trading_daily", [{"date": "2026-09-21", "code": "2330", "market": "TWSE",
                                                        "volume": 1.0, "trade_value": 2.0, "transactions": 3.0,
                                                        "close": 2480.0, "src": "TWSE_OPENAPI"}], ["date", "code", "market"])

            class FakeNet13:
                @staticmethod
                def http_json(url):
                    if "STOCK_DAY_ALL" in url:
                        return {"state": "OK", "data": [{"Date": "1150924", "Code": "2317", "TradeVolume": "35,754,545",
                                                        "TradeValue": "9,154,003,139", "OpeningPrice": "255.00",
                                                        "HighestPrice": "257.00", "LowestPrice": "255.00",
                                                        "ClosingPrice": "256.00", "Transaction": "31,260"}]}
                    if "tpex_mainboard_daily_close_quotes" in url:
                        return {"state": "OK", "data": [{"Date": "1150924", "SecuritiesCompanyCode": "5483", "Close": "188.50",
                                                        "Open": "184.00", "High": "188.50", "Low": "181.50",
                                                        "TradingShares": "18651980", "TransactionAmount": "3472335519",
                                                        "TransactionNumber": "14810"}]}
                    return {"state": "FAIL", "note": "no-net"}
            _r13 = lane_trading(FakeNet13)
            _c13 = _ddb13.connect(str(DB_TW), read_only=True)
            _old13 = _c13.execute("SELECT close, open FROM tw_trading_daily WHERE date='2026-09-23'").fetchone()
            _keep13 = _c13.execute("SELECT close, src FROM tw_trading_daily WHERE date='2026-09-22'").fetchone()
            _t13 = dict(_c13.execute("SELECT column_name, data_type FROM information_schema.columns "
                                     "WHERE table_name='tw_trading_daily'").fetchall())
            _l2 = _c13.execute("SELECT code, market, open, high, low, close FROM tw_trading_daily "
                               "WHERE date='2026-09-24' ORDER BY code").fetchall()
            _c13.close()
    except Exception as exc:                       # 舊寫法會在這裡炸:十欄表插七欄 → BinderException
        _e13 = f"{type(exc).__name__}: {str(exc)[:90]}"
        _n13a = _n13b = _n13c = _r13 = _old13 = _keep13 = _l2 = None
        _t13 = {}
    finally:
        OUT, DB_TW, DB_GL, CKPT = _s13
    chk("⑬ v0114 共用表照欄名插入:tw_trading_daily 已由 ENG057 v0102 建成十欄(多開高低),本支七欄的列照插不炸(舊寫法 BinderException);"
        "鍵已在=不動(冪等,不覆蓋);這批新欄照型別加(src 是 VARCHAR 不是 DOUBLE);L2 同一回包收開高低(TWSE OpeningPrice… · TPEX Open…)",
        not _e13 and _n13a == 2 and _n13b == 2 and _n13c == 3 and _old13 == (2500.0, 2475.0)
        and _keep13 == (2490.0, None) and _t13.get("src") == "VARCHAR"
        and (_r13 or {}).get("state") == "OK"
        and _l2 == [("2317", "TWSE", 255.0, 257.0, 255.0, 256.0), ("5483", "TPEX", 184.0, 188.5, 181.5, 188.5)],
        f"({_e13 or 'ok'} · 列 {_n13a}/{_n13b}/{_n13c} · src 型 {_t13.get('src')} · L2 {_l2})")
    # ── v0115 ⑭:發行股數(交易所給的)收進 tw_shares_issued · L2 每列記 src(暫存庫;FakeNet 零網路)──
    _s14 = (OUT, DB_TW, DB_GL, CKPT)
    _e14 = ""
    try:
        import duckdb as _ddb14
        with tempfile.TemporaryDirectory() as td14:
            OUT, DB_TW, DB_GL, CKPT = Path(td14), Path(td14) / "tw.duckdb", Path(td14) / "gl.duckdb", Path(td14) / "ck.json"

            class FakeNet14:
                @staticmethod
                def http_json(url):
                    if "t187ap03_L" in url:          # 欄名照樹上快照 t187ap03_L_20260805(出表 1150804)
                        return {"state": "OK", "data": [
                            {"出表日期": "1150804", "公司代號": "2330", "公司簡稱": "台積電", "產業別": "24",
                             "已發行普通股數或TDR原股發行股數": "25932370067"},
                            {"出表日期": "?", "公司代號": "2317", "公司簡稱": "鴻海", "產業別": "31",
                             "已發行普通股數或TDR原股發行股數": "13862916983"}]}      # 出表日認不出=不收股數
                    if "mopsfin" in url:              # 欄名照容器實量 TPEX openapi(出表 1150924)
                        return {"state": "OK", "data": [{"Date": "1150924", "SecuritiesCompanyCode": "5483",
                                                        "CompanyName": "中美矽晶製品股份有限公司", "SecuritiesIndustryCode": "24",
                                                        "IssueShares": "641221651"}]}
                    if "STOCK_DAY_ALL" in url:
                        return {"state": "OK", "data": [{"Date": "1150925", "Code": "2330", "TradeVolume": "1",
                                                        "TradeValue": "1", "Transaction": "1", "ClosingPrice": "2500",
                                                        "OpeningPrice": "2475", "HighestPrice": "2505", "LowestPrice": "2475"}]}
                    if "tpex_mainboard_daily_close_quotes" in url:
                        return {"state": "OK", "data": [{"Date": "1150925", "SecuritiesCompanyCode": "5483", "Close": "188.50",
                                                        "Open": "184.00", "High": "188.50", "Low": "181.50",
                                                        "TradingShares": "18651980", "TransactionAmount": "3472335519",
                                                        "TransactionNumber": "14810", "Capitals": "641300000"}]}
                    return {"state": "FAIL", "note": "no-net"}
            _r14a = lane_listings(FakeNet14)
            _r14b = lane_trading(FakeNet14)
            _r14c = lane_listings(FakeNet14)          # 同一份出表日再跑一次=不重複(只增不改)
            _c14 = _ddb14.connect(str(DB_TW), read_only=True)
            _sh14 = _c14.execute(f"SELECT asof_date, code, market, shares_issued, src FROM {SHARES_TABLE} "
                                 "ORDER BY code, src").fetchall()
            _src14 = _c14.execute("SELECT code, src FROM tw_trading_daily ORDER BY code").fetchall()
            _c14.close()
    except Exception as exc:
        _e14 = f"{type(exc).__name__}: {str(exc)[:90]}"
        _r14a = _r14b = _r14c = {}
        _sh14 = _src14 = None
    finally:
        OUT, DB_TW, DB_GL, CKPT = _s14
    chk("⑭ v0115 發行股數是交易所給的(t187ap03_L 已發行普通股數 · t187ap03_O IssueShares · 上櫃每日收盤 Capitals),"
        "抓了就要收:進 tw_shares_issued(一份出表日一份、src 具名;出表日認不出=不收,不猜日子);同一份出表日重跑不重複;"
        "L2 每列記 src(tw_trading_daily 兩個寫入者,口徑要看得出是誰寫的)",
        not _e14 and (_r14a or {}).get("shares") == 2 and (_r14c or {}).get("shares") == 2
        and _sh14 == [("2026-08-04", "2330", "TWSE", 25932370067.0, "TWSE_OPENAPI_T187AP03_L"),
                      ("2026-09-25", "5483", "TPEX", 641300000.0, "TPEX_OPENAPI_DAILY_CAPITALS"),
                      ("2026-09-24", "5483", "TPEX", 641221651.0, "TPEX_OPENAPI_T187AP03_O")]
        and _src14 == [("2330", "TWSE_OPENAPI_STOCK_DAY_ALL"), ("5483", "TPEX_OPENAPI_DAILY_CLOSE")]
        and (_r14b or {}).get("state") == "OK",
        f"({_e14 or 'ok'} · 股數 {_sh14} · src {_src14})")
    # ── v0115 ⑮:樹上交易所快照重放進股數史(暫存快照夾 + 暫存庫;不觸網)──
    _s15 = (OUT, DB_TW, DB_GL, CKPT)
    _e15, _r15a, _r15b, _r15c, _rows15 = "", {}, {}, {}, None
    try:
        import duckdb as _ddb15
        with tempfile.TemporaryDirectory() as td15:
            OUT, DB_TW, DB_GL, CKPT = Path(td15), Path(td15) / "tw.duckdb", Path(td15) / "gl.duckdb", Path(td15) / "ck.json"
            _sd = Path(td15) / "snap"
            _sd.mkdir()
            (_sd / "t187ap03_L_20260805.json").write_text(json.dumps([
                {"出表日期": "1150804", "公司代號": "2330", "已發行普通股數或TDR原股發行股數": "25932370067"},
                {"出表日期": "1150804", "公司代號": "0050", "已發行普通股數或TDR原股發行股數": "abc"}]),     # 股數認不出=不收
                encoding="utf-8-sig")
            (_sd / "t187ap03_O_20260805.json").write_text(json.dumps([
                {"Date": "1150805", "SecuritiesCompanyCode": "8277", "IssueShares": "91628833"}]), encoding="utf-8")
            _r15a = shares_from_snapshots(_sd)
            _r15b = shares_from_snapshots(_sd)             # 重放冪等
            _r15c = shares_from_snapshots(Path(td15) / "空夾")
            _c15 = _ddb15.connect(str(DB_TW), read_only=True)
            _rows15 = _c15.execute(f"SELECT asof_date, code, market, shares_issued, src FROM {SHARES_TABLE} ORDER BY code").fetchall()
            _c15.close()
    except Exception as exc:
        _e15 = f"{type(exc).__name__}: {str(exc)[:90]}"
    finally:
        OUT, DB_TW, DB_GL, CKPT = _s15
    chk("⑮ v0115 樹上交易所快照(t187ap03_L/_O,批363 存證)重放進股數史:src=TREE_SNAPSHOT_…、出表日當 asof;股數認不出不收;"
        "重放冪等(第二次表內列數不變);空夾=NODATA 講明;與 L1 共用同一個解析 _shares_rows(不長第二份)",
        not _e15 and _r15a.get("state") == "OK" and _r15a.get("rows") == 2 and _r15b.get("db") == 2
        and _r15c.get("state") == "NODATA"
        and _rows15 == [("2026-08-04", "2330", "TWSE", 25932370067.0, "TREE_SNAPSHOT_T187AP03_L"),
                        ("2026-08-05", "8277", "TPEX", 91628833.0, "TREE_SNAPSHOT_T187AP03_O")]
        and _insp.getsource(lane_listings).count("_shares_rows(") == 1
        and "已發行普通股數" not in _insp.getsource(lane_listings),
        f"({_e15 or 'ok'} · {_rows15} · 重放 {_r15b.get('db')} · 空夾 {_r15c.get('state')})")
    # ── v0116 ⑯:L13 FactSet 外呼走統包 curl_bytes · 已在庫不重抓 · 沒連上照實講 · 全檔語法樹零 ["curl", …](暫存庫;假工具零網路)──
    _s16 = (OUT, DB_TW, DB_GL, CKPT)
    _e16, _r16, _o16, _d16, _calls16, _n16 = "", {}, {}, {}, [], None
    _a1, _a2 = "https://insight.factset.com/earnings-season-update-sept-19-2026", "https://insight.factset.com/earnings-season-update-sept-26-2026"
    _listing16 = f'<a href="{_a1}">1</a> <a href="{_a2}">2</a> <a href="https://insight.factset.com/author/someone-name-here">x</a>'.encode()
    _art16 = ('<script>{"datePublished":"2026-09-26"}</script><p>The forward 12-month P/E ratio for the S&P 500 is 22.4.</p>'
              '<p>The Q3 bottom-up EPS estimate (which is an aggregation of the median EPS estimates for Q3 for all the companies '
              'in the index) increased by 0.4% to $66.10.</p>').encode()          # FactSet 新聞稿的句型(FS_EPS_RX 認的就是這個)

    class FakeNet16:
        @staticmethod
        def curl_bytes(url, headers=None, timeout=30, follow=True):
            _calls16.append(url)
            return {"state": "OK", "data": _listing16 if url == FS_TOPIC else _art16, "via": "curl"}

    class DenyNet16:
        @staticmethod
        def curl_bytes(url, headers=None, timeout=30, follow=True):
            return {"state": "DENY", "note": "同意閘未開"}

    try:
        import duckdb as _ddb16
        with tempfile.TemporaryDirectory() as td16:
            OUT, DB_TW, DB_GL, CKPT = Path(td16), Path(td16) / "tw.duckdb", Path(td16) / "gl.duckdb", Path(td16) / "ck.json"
            _c16 = _ddb16.connect(str(DB_GL))
            _c16.execute("CREATE TABLE factset_earnings(published VARCHAR, metric VARCHAR, period VARCHAR, value DOUBLE, source VARCHAR, flag VARCHAR)")
            _c16.execute("INSERT INTO factset_earnings VALUES ('2026-09-19','SPX_FWD_PE_12M','NTM',22.0,?,'PRESS_RELEASE')", [_a1])
            _c16.execute("CREATE TABLE global_daily(date VARCHAR, ticker VARCHAR, adj_close DOUBLE)")
            _c16.execute("INSERT INTO global_daily VALUES ('2026-09-25','^GSPC',6720.0)")
            _c16.close()
            _r16 = lane_factset(FakeNet16)
            _o16 = lane_factset(OldNet12)
            _d16 = lane_factset(DenyNet16)
            _c16 = _ddb16.connect(str(DB_GL), read_only=True)
            _n16 = _c16.execute("SELECT metric, period, value FROM factset_earnings WHERE published='2026-09-26' ORDER BY metric").fetchall()
            _c16.close()
    except Exception as exc:
        _e16 = f"{type(exc).__name__}: {str(exc)[:90]}"
    finally:
        OUT, DB_TW, DB_GL, CKPT = _s16
    import ast as _ast16
    _curl_lists = [n for n in _ast16.walk(_ast16.parse(Path(__file__).read_text(encoding="utf-8")))
                   if isinstance(n, _ast16.List) and n.elts and isinstance(n.elts[0], _ast16.Constant) and n.elts[0].value == "curl"]
    chk("⑯ v0116 L13 FactSet 外呼走統包 curl_bytes(v0115 以前問完車道就自己 subprocess curl):兩篇一篇已在庫 → 只抓清單+一篇、萃取 P/E 與 EPS、倒推 fwd EPS 照舊;"
        "舊工具=FAIL 講明要哪一版;閘關=DENY(不再說成「版式變了」);全檔語法樹零 [\"curl\", …]",
        not _e16 and _r16.get("state") == "OK" and _calls16 == [FS_TOPIC, _a2]
        and _n16 == [("SPX_BOTTOMUP_EPS", "Q3", 66.1), ("SPX_FWD_EPS_IMPLIED", "NTM", 300.0), ("SPX_FWD_PE_12M", "NTM", 22.4)]
        and _o16.get("state") == "FAIL" and "curl_bytes" in _o16.get("note", "") and _d16.get("state") == "DENY"
        and "subprocess" not in _insp.getsource(lane_factset) and not _curl_lists,
        f"({_e16 or 'ok'} · 呼叫 {len(_calls16)} · 列 {_n16} · 舊 {_o16.get('state')} · 閘關 {_d16.get('state')} · curl 清單 {len(_curl_lists)})")
    print(f"  [計] 十六檢 OK {16 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 總擷取執行器(VDF_ENG055 v0116)· 十六檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "--shares-snapshot" in args:                 # v0115:樹上交易所快照重放進股數史(不觸網、不必同意閘)
        i = args.index("--shares-snapshot")
        r = shares_from_snapshots(Path(args[i + 1]) if i + 1 < len(args) and not args[i + 1].startswith("-") else None)
        print(f"[股數快照] {r['state']} · {r.get('rows', 0)} 列 · 表內 {r.get('db', '—')} · {r.get('note', '')}")
        return 0 if r["state"] == "OK" else 2
    if "--export" in args:
        return export(args[args.index("--export") + 1])
    sel = None
    if "--lane" in args:
        sel = [x for x in args[args.index("--lane") + 1].split(",") if x in LANES]
    if "--from-file" in args and args.index("--from-file") + 1 < len(args):      # 批522 當沖檔案收容道
        _FROM_FILES.extend(x for x in args[args.index("--from-file") + 1].split(",") if x.strip())
    if "--date" in args and args.index("--date") + 1 < len(args):
        globals()["_FILE_DATE"] = args[args.index("--date") + 1]
    if "--market" in args and args.index("--market") + 1 < len(args):
        globals()["_FILE_MARKET"] = args[args.index("--market") + 1]
    return run(sel)


if __name__ == "__main__":
    sys.exit(main())
