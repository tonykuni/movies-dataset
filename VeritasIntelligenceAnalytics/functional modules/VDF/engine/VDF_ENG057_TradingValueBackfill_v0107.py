#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG057_TradingValueBackfill v0107 — 逐股成交值歷史回補(批154;via-tval;側線 2026-09-24 第四段:擷取五條紀律;第五段:市值以交易所為主;第七段:跟其他看盤網站核對;第八段:每日股數史;第九段:核對的閘與候選;第十段:核對表寫入收正典)
v0106→v0107(側線 2026-09-24 第十段;主線批號由併線的手指定 L25;掉球 Z191「去重寫入私有份收回正典」):
  xcheck 寫 tw_market_cap_xcheck 那一段是本支第七段自己長出來的一份私有去重寫入(CREATE … LIMIT 0 + INSERT … WHERE NOT EXISTS),
  Z191 當初只普查「名字叫 upsert 的函式」沒數到它;改用 SQL 字樣普查才現形。v0107 交正典 SUP_MDL753 v0110 `upsert_rows`
  (鍵 check_date+code,語意照舊:一天一份、當天已核的不重寫)。順帶:核對表之後若多一欄,照型別加(私有份是直接 Binder 錯)。十六檢照舊。
v0105→v0106(側線 2026-09-24 第九段;主線批號由併線的手指定 L25;PR #110 Codex 審兩條,逐條實量屬實 · 掉球 Z192):
  ① **xcheck 沒過本支的同意閘**:run / shares 都先判 gate_open()(兩閘都要 YES),xcheck 卻直接交網路工具——而網路工具 SUP_MDL740
     v0114 的閘二只看「有沒有設值」(gate_state:bool(VIA_SCRAPE_CONSENT)),短令冊 Register v0242 在閘未設時補的預設值正是 "OFF"
     → VIA_NET_CONSENT=YES + VIA_SCRAPE_CONSENT=OFF 時,本支別的動詞都擋,xcheck 照樣去問 Yahoo。v0106 在**載入網路工具之前**先判
     gate_open()(閘關=DENY,零外呼、什麼都不記);今天已核過、不必出網的照舊回報。網路工具閘二的口徑全樹三套(工具:有值即開 ·
     短令冊 via-gates:http 道只要閘一、爬蟲道要 I_ACCEPT_RESPONSIBLE_SCRAPING · 本支:兩閘都 YES),要不要統一=操作員裁 → Z192,本版不動工具。
  ② **候選是空的也回 OK**:`--codes` 指定的代號在全域最新日沒有嚴格市值(或它那個市場晚一天進庫),候選就空了,v0105 回「今天已核過 0 檔」的 OK=假綠。
     v0106:每個市場用**自己**最新一個有嚴格市值的交易日(`--codes` 則每個代號用自己的最新日)——某市場落後一天照核,不再整個市場被跳過;
     候選空=NODATA 講明是哪幾檔;要核的代號有的沒有嚴格市值=PARTIAL(rc 2),列在 missing;每列的 exchange_date 用那一列自己的交易日。
  自測 +⑯(閘關零出網 · 啟動器預設 OFF 也算關 · 落後的市場照核自己的最新日 · 候選空=NODATA · 部分沒有=PARTIAL · 前 N 大兩市場都在)。十六檢。
v0104→v0105(側線 2026-09-24 第八段;主線批號由併線的手指定 L25;操作員令「市值都以交易所為主」「整合資料庫去重補不足 確保完整性」· 掉球 Z184):
  ① **每日發行股數史**(`shares`):市值要用「那一天」的股數,第一份出表日之前以前只能用之後的股數近似(另欄)。交易所其實每天都給:
     TWSE「外資及陸資投資持股統計」MI_QFIIS 每天帶「發行股數」(容器實量 2026-09-23 1,363 檔:2330 25,932,370,067 · 2317 14,028,648,626——
     比 08-04 快照多,股數真的在變)· TPEX 每日收盤行情 otc(type=EW)帶「發行股數」。兩條車道一日一請求,寫進同一張 tw_shares_issued
     (src TWSE_RWD_MI_QFIIS / TPEX_RWD_OTC_SHARES)。**先查庫**:那天那個市場已有每日股數(任何每日來源,含 ENG055 L2 的 Capitals)=完成;
     只抓缺的;正典 batch_fetch(加速器 · 定量落盤 · Ctrl+C 安全);`--every N` 每 N 個交易日取一天(預設 5=週;股數只在事件時變,
     逐日抓大多是重抓;`--every 1` 逐日),最後一天一定取;跑完刷新市值檢視表。
  ② `upsert` 交正典 SUP_MDL753 v0109 `upsert_rows`(去重寫入的唯一實作;語意照 v0103:鍵已在只補空欄、src 不補)。本支這一份
     v0102 新欄一律 DOUBLE、v0103 才改——私有份會各自走樣。這裡留一個轉接(表、鍵、補欄政策固定;DB_TW 要晚綁,自測會換它)。
  自測 +⑮(解析真欄名 · 抽樣 · 先查庫 · 傳輸敗不記 done · 重跑只剩敗的 · 閘關 rc2 · 嚴格市值覆蓋變多)。十五檢。
v0103→v0104(側線 2026-09-24 第七段;主線批號由併線的手指定 L25;操作員令「… 市值都以交易所為主 可以跟其他看盤網站核對正確性」· 掉球 Z185):
  `xcheck`:交易所股數與市值 × Yahoo quoteSummary(sharesOutstanding / marketCap / regularMarketPrice)逐檔核對,只報不改。
  容器直接量(不經引擎、不落庫):2330 Yahoo 股數 25,932,370,067 = 交易所已發行股數,一股不差;5483 Yahoo 614,171,651、
  交易所 641,221,651——**Yahoo 少 4.2%**(Yahoo 是「流通在外」、交易所是「已發行」,差的看起來是庫藏股)。
  這正是要核對的東西:主數據照舊以交易所為準,口徑差逐檔列出來給人看。
  ① 最新一個有嚴格市值的交易日,取前 N 大(預設 30;`--codes` 指定)→ 走統包 `yahoo_quote_summary`(閘關=DENY 照實,不代設)。
  ② 先查庫:`tw_market_cap_xcheck` 今天已核過的碼不重抓(一天一份,只增不改)。
  ③ 每檔記 股數比(Yahoo ÷ 交易所)、價比(Yahoo 價 ÷ 交易所收盤;≠1 表示兩邊不是同一天)、Yahoo 市值 ÷(交易所收盤 × 交易所股數);
     股數差 >1% 標 DIFF;但若交易所**之後的出表**已跟 Yahoo 一樣,標 SNAPSHOT_STALE(價格那天用的股數快照舊了,不是口徑差)。
     容器真資料(上櫃前 30 大、交易所日 2026-09-23、股數 08-05 出表;Yahoo 回應在獨立行程錄下再重播):SAME 21 · 快照舊了 2(5274 配股後
     09-24 出表 41,582,953 = Yahoo)· 口徑差或 Yahoo 怪 6(5483 Yahoo 少 27,050,000 股;3105 Yahoo 只有 8,083 萬股、交易所 4.24 億股)· Yahoo 沒股數 1。
     鉅亨(cnyes)報價容器實量也拿得到,但**沒有市值與股數欄**(只有價量),本版不接。
  自測 +⑭(假工具零網路:同股數=SAME · 少 4.2%=DIFF · Yahoo 沒回=列 failed · 當天重跑不出網 · 閘關=DENY · 沒有嚴格市值=NODATA)。十四檢。
v0102→v0103(側線 2026-09-24 第五段;主線批號由併線的手指定 L25;操作員令「成交量 成交值 市值都以交易所為主 可以跟其他看盤網站核對正確性」· 掉球 Z179 · Z180):
  ① **市值**:交易所不直接給市值,但給發行股數(VDF_ENG055 v0115 L1 收進 `tw_shares_issued`,一份出表日一份)。
     新檢視表 `tw_market_cap_daily` = 交易所收盤 × 交易所發行股數,**全樹唯一一處**(主線 ENG092 冊宣告了市值這一欄,冊的規則改指向這裡)。
     股數取「當天或之前最近一份」(DuckDB ASOF 聯結)→ `market_cap`,basis=EXCHANGE_CLOSE×EXCHANGE_SHARES;
     那天之前還沒有任何一份股數的,**不填進 market_cap**——另一欄 `market_cap_later_shares` 用「之後第一份」近似,
     basis=EXCHANGE_CLOSE×LATER_EXCHANGE_SHARES。兩欄分開,是因為股數真的會跳:容器實量兩份出表(08-05 → 09-24)之間 8277 從 9,163 萬減到 3,950 萬
     (×0.43)、4747 與 1799 剛好翻倍——拿之後的股數回推舊日市值會差一倍以上——混在同一欄就看不出來。`mcap` 另列相鄰兩份出表股數差 ≥20% 的碼。
     動詞 `mcap`(建/刷新檢視表 + 覆蓋報告;不觸網);`run` 抓完順手刷新一次;`verify` 只讀不建。
  ② **口徑(Z180)**:每列記 `src`(TWSE_RWD_MI_INDEX / TPEX_RWD_DAILYQUOTES / …)。同一張表還有 ENG055 L2(openapi)在寫;
     容器實量上櫃 rwd dailyQuotes 與 openapi 每日收盤同口徑(2026-09-24 四碼 890 檔成交股數 890/890 一樣)。TPEX 另兩個後備變體
     (otc 不帶 type=EW · tradingStock)容器實量 0 列/無代號欄——實際上接不上,留著但具名。
     **舊列的 src 不補**:COALESCE 補值時 src 不在補的欄裡——那一列的量不是這一次抓的,補上這次的來源等於冒名(舊列 src=NULL,verify 記「未記」)。
     `verify` 多報各市場的 src 分布。
  自測 +⑫(src 逐列 · 舊列不冒名 · 分布)+⑬(市值嚴格/近似/無股數三態 · 跳動 · 缺股數表=NODATA · 只讀不建檢視)。十三檢。
v0101→v0102(主線批號由併線的手指定 L25;操作員令「擷取資料前要先檢查資料庫缺啥,確定擷取範圍去擷取,BATCH FETCHING 固定時間先暫存
  避免重複擷取 整合資料庫去重補不足 確保完整性 VDF加速器跟網路工具都要導入並覆蓋深入所有指令細節動作」):
  ① 先查庫缺啥:已抓清單 = checkpoint ∪ **庫裡已有的 (日, 市場)**(v0101 只看 checkpoint 檔——換機器或檔不見就整批重抓;
     ENG056 批395 早就自庫重建,本支沒有)。② 定範圍:只抓缺的日×車道。
  ③ 批次:迴圈交正典 SUP_MDL753 v0108 `batch_fetch`(唯一實作)——加速器 accel_map 平行(預設 2 工,每工照舊節流 1.2s;
     一塊傳輸敗過半自癒減工)· 每 40 件(≈v0101 的 20 日×2 車道)落庫 + 寫 checkpoint · Ctrl+C 安全 · 傳輸敗不記 done。
  ④ 去重:照舊 anti-join upsert(日, 代號, 市場);**跑完報完整性**:逐市場「有料日 / 日曆日」與缺哪幾天(抓過但空 vs 還沒抓到)。
  ⑤ 網路工具:拿掉「統包缺席=本地 curl 後備」(那條後備不經同意閘也不經法遵層);工具缺=開跑前誠實停。進度條綁正典 BatchProgress。
  ⑥ 操作員令(同日第二道)「所有數據都以交易所為主 但只有 YFINANCE 抓得到 ADJ CLOSE 所以可用他抓 CLOSE ADJ CLOSE 重複 CLOSE 是為了核對
     成交量 成交值 市值都以交易所為主 可以跟其他看盤網站核對正確性」:
     · 同一個請求(MI_INDEX ALLBUT0999 / TPEX 日行情)的回包本來就有開高低收,v0101 只收了收盤——v0102 收下 **open/high/low**(表頭名對位),
       tw_trading_daily 成為交易所 OHLCV + 成交值 + 筆數的主表(只增欄)。
     · 「查庫缺啥」跟著改:(日, 市場) 的列要**有開高低**才算完成;庫裡已有但缺開高低的列補一次(upsert 以 COALESCE **補不足、不覆蓋**)。
       checkpoint 換檔名 trading_value_ohlc_checkpoint.json(v0101 的檔記的是「只有收盤」的完成,不能沿用)。
     · `verify`(唯讀):交易所收盤 × Yahoo 收盤逐列核對——一致 / 配股換階(Yahoo 事後回乘,比值持續) / 單日陳價(比值單日跳、前後一致;Z175) /
       只有一邊有料(Z174)。Yahoo 在本支只當「核對」與 ADJ CLOSE 的來源,主數據以交易所為準。
     · 市值:交易所收盤 × 發行股數——庫裡**沒有發行股數**(名冊只有代碼/名稱/產業),本版誠實不算,記在文件待抓發行股數那一道。
  自測 +⑦⑧⑨⑩⑪(自庫重建 · 中斷/續補/冪等/閘 · 完整性 · 零 subprocess · 交易所×Yahoo 核對分類)。十一檢。
VDF_ENG057_TradingValueBackfill v0101 — 逐股成交值歷史回補(批154;via-tval)
====================================================================
批154 令「資金的進出增減可比較性」數據基座:tw_trading_daily 原僅
L2 當日快照(2 日),本器逐日回補雙所逐股 成交股數/成交金額/成交筆數
2024-01-02→最新——供真金流佔比指標(市場成交值−台積電−當沖為分母)
以真值取代 TURNOVER_PROXY。
  交易日曆=已庫 tw_daily_prices 實際日期(零猜測)
  車道×日:twse_mi(MI_INDEX ALLBUT0999 逐股)/tpex_quotes(櫃買日收)
  欄位對位=按表頭名動態(嚴禁寫死欄序;QA-20260825A 精神)
  TPEX 端點=啟動時變體探測,全敗誠實 TPEX_PENDING
  傳輸=統包 curl_json 車道(rwd/www TLS 指紋實證);節流 1.2s
  checkpoint 日×車道;20 日批 parquet;duckdb anti-join 冪等
用法:via-tval run [--days N] [--workers N] | verify | mcap | xcheck [--top N | --codes 2330,5483] | shares [--every N] [--days N] [--workers N] | --status | --selftest
v0100→v0101(批508):交易日曆自測改用暫存 DuckDB 三日夾具；工作站資料涵蓋率
另由 census/RunGate 驗，不再要求 fresh clone 先有 600 日正庫才准單元測試通過。
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


import json
import os
import sys
import time
from datetime import datetime
from datetime import date as _date
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
OUT = VDF / "output_hub" / "mega"
DB_TW = OUT / "vdf_tw_market.duckdb"
CKPT = OUT / "trading_value_ohlc_checkpoint.json"      # v0102:完成的定義改成「有開高低」;v0101 的 trading_value_checkpoint.json 不沿用
PAUSE_S = 1.2
WORKERS_DEFAULT = 2      # v0102:加速器 accel_map 平行工(每工保留 PAUSE_S 節流;MI_INDEX 回包大,比 ENG056 的 4 保守)
FLUSH_N = 40             # v0102:每 40 件(≈20 日×2 車道,同 v0101 的批長)落庫 + checkpoint
PROGRESS = OUT / "trading_value_progress.json"
LANE_MARKET = {"twse_mi": "TWSE", "tpex_quotes": "TPEX"}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#: v0103:逐列記來源表(Z180)。tw_trading_daily 有兩個寫入者(本支 rwd · ENG055 L2 openapi),TPEX 還有後備變體——口徑要看得出是誰寫的
SRC_TWSE = "TWSE_RWD_MI_INDEX"
TPEX_SRC = (("dailyQuotes", "TPEX_RWD_DAILYQUOTES"), ("/otc?", "TPEX_RWD_OTC"), ("tradingStock", "TPEX_RWD_TRADINGSTOCK"))
#: v0103:市值 = 交易所收盤 × 交易所發行股數(股數表由 ENG055 v0115 L1 收;本檢視表是全樹唯一一處)
SHARES_TABLE = "tw_shares_issued"
MCAP_VIEW = "tw_market_cap_daily"
MCAP_JUMP = 0.2                       # 相鄰兩份出表股數差 ≥20% → 列出(配股/面額變更/減資;拿之後的股數回推舊日會錯)
_MCAP_SQL = """
WITH t AS (SELECT TRY_CAST(date AS DATE) AS d, code, market, close FROM tw_trading_daily
           WHERE close > 0 AND TRY_CAST(date AS DATE) IS NOT NULL),
     sx AS (SELECT TRY_CAST(asof_date AS DATE) AS a, code, market, max(shares_issued) AS sh, min(src) AS src
            FROM tw_shares_issued WHERE shares_issued > 0 AND TRY_CAST(asof_date AS DATE) IS NOT NULL GROUP BY 1, 2, 3),
     st AS (SELECT t.d, t.code, t.market, t.close, sx.sh, sx.a, sx.src
            FROM t ASOF LEFT JOIN sx ON t.code = sx.code AND t.market = sx.market AND t.d >= sx.a),
     f AS (SELECT code, market, arg_min(sh, a) AS sh0, min(a) AS a0 FROM sx GROUP BY 1, 2)
SELECT st.d AS date, st.code, st.market, st.close,
       st.sh AS shares_issued, st.a AS shares_asof, st.src AS shares_src,
       st.close * st.sh AS market_cap,
       CASE WHEN st.sh IS NULL THEN f.a0 END AS later_shares_asof,
       CASE WHEN st.sh IS NULL THEN st.close * f.sh0 END AS market_cap_later_shares,
       CASE WHEN st.sh IS NOT NULL THEN 'EXCHANGE_CLOSE×EXCHANGE_SHARES'
            WHEN f.sh0 IS NOT NULL THEN 'EXCHANGE_CLOSE×LATER_EXCHANGE_SHARES'
            ELSE 'NO_SHARES' END AS basis
FROM st LEFT JOIN f ON st.code = f.code AND st.market = f.market
"""

TPEX_VARIANTS = [
    "https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes?date={slash}&type=EW&response=json",
    "https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date={slash}&response=json",
    "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock?date={slash}&type=EW&response=json",
]


def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(glob 最新;嚴禁寫死版號) =====
def _net_or_none():
    import glob as _g
    import importlib.util as _il
    VIA = VDF.parent.parent
    hits = sorted(_g.glob(str(VIA / "supportive modules" / "network"
                               / "SUP_MDL740_NetUnified_v*.py")))
    if not hits:
        return None
    spec = _il.spec_from_file_location("via_net_dyn57", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["via_net_dyn57"] = mod
    spec.loader.exec_module(mod)
    return mod
# ===== [VIA:NET-BRIDGE:END] =====

_NET = None


def curl_json(url: str) -> dict | None:
    """統包 curl_json 車道。v0102:統包缺席=None,**不再自己打 curl**(那條後備不經同意閘也不經工具的法遵層);
    run() 開跑前先驗工具在位,缺=誠實停。"""
    global _NET
    if _NET is None:
        _NET = _net_or_none() or False
    if _NET and hasattr(_NET, "curl_json"):
        r = _NET.curl_json(url)
        return r.get("data") if r.get("state") == "OK" else None
    return None


def _net_ready() -> bool:
    """v0102:統包網路工具在位且有 curl_json 車道(真擷取的前提;缺=誠實停,不後備)。"""
    n = _net_or_none()
    return bool(n) and hasattr(n, "curl_json")


#: 批597 三庫整併:_num → 正典綁定(純轉換(原本多一個 .strip(),float() 本來就吃得下前後空白);28 組語料零差異)。
#  綁定不是 def——再包一層 def 的話能力庫裡那一族還在,家族數不會掉(LL143)。
_num = _LIB.num


def _find_table(js: dict, need: tuple[str, ...]) -> tuple[list, list] | None:
    """rwd/www JSON 多表結構:按表頭名找含全部關鍵欄之表(零欄序寫死)"""
    tables = js.get("tables") or ([js] if js.get("fields") else [])
    for t in tables:
        fields = [str(f) for f in (t.get("fields") or [])]
        if all(any(k in f for f in fields) for k in need):
            return fields, t.get("data") or []
    return None


def _idx(fields: list[str], key: str) -> int | None:
    for i, f in enumerate(fields):
        if key in f:
            return i
    return None


def parse_twse_mi(js: dict, iso: str) -> list[dict]:
    ft = _find_table(js, ("證券代號", "成交金額", "成交股數"))
    if not ft:
        return []
    fields, data = ft
    ic, iv, ia, it_, ip = (_idx(fields, k) for k in
                           ("證券代號", "成交股數", "成交金額", "成交筆數", "收盤價"))
    io_, ih, il = (_idx(fields, k) for k in ("開盤價", "最高價", "最低價"))      # v0102:交易所為主——同一回包的開高低一併收
    rows = []
    for r in data:
        code = str(r[ic]).strip()
        if len(code) != 4 or not code.isdigit():
            continue  # 四碼普通股;權證/ETF 衍生另冊
        rows.append({"date": iso, "code": code, "market": "TWSE",
                     "volume": _num(r[iv]), "trade_value": _num(r[ia]),
                     "transactions": _num(r[it_]) if it_ is not None else None,
                     "close": _num(r[ip]) if ip is not None else None,
                     "open": _num(r[io_]) if io_ is not None else None,
                     "high": _num(r[ih]) if ih is not None else None,
                     "low": _num(r[il]) if il is not None else None})
    return rows


def parse_tpex(js: dict, iso: str) -> list[dict]:
    ft = _find_table(js, ("代號", "成交金額")) or _find_table(js, ("代號", "成交值"))
    if not ft:
        return []
    fields, data = ft
    ic = _idx(fields, "代號")
    iv = _idx(fields, "成交股數") or _idx(fields, "成交量")
    ia = _idx(fields, "成交金額") or _idx(fields, "成交值")
    it_ = _idx(fields, "成交筆數")
    ip = _idx(fields, "收盤")
    io_, ih, il = _idx(fields, "開盤"), _idx(fields, "最高"), _idx(fields, "最低")   # v0102:交易所為主
    rows = []
    for r in data:
        code = str(r[ic]).strip()
        if len(code) != 4 or not code.isdigit():
            continue
        rows.append({"date": iso, "code": code, "market": "TPEX",
                     "volume": _num(r[iv]) if iv is not None else None,
                     "trade_value": _num(r[ia]),
                     "transactions": _num(r[it_]) if it_ is not None else None,
                     "close": _num(r[ip]) if ip is not None else None,
                     "open": _num(r[io_]) if io_ is not None else None,
                     "high": _num(r[ih]) if ih is not None else None,
                     "low": _num(r[il]) if il is not None else None})
    return rows


_TPEX_URL: str | None = None


def _tpex_probe(sample_slash: str) -> str | None:
    """啟動時變體探測(同 ENG056 當沖手法);每變體重試 3 次退避
    (單發瞬斷不得棄整車道=批156 韌性精神);全敗=誠實 TPEX_PENDING"""
    global _TPEX_URL
    if _TPEX_URL is not None:
        return _TPEX_URL or None
    for tpl in TPEX_VARIANTS:
        for attempt in range(3):
            js = curl_json(tpl.format(slash=sample_slash))
            if js and parse_tpex(js, "probe"):
                _TPEX_URL = tpl
                return tpl
            time.sleep(1.5 * (attempt + 1))  # 退避重試
    _TPEX_URL = ""
    return None


def trading_days() -> list[str]:
    import duckdb
    if not DB_TW.exists():
        return []
    con = duckdb.connect(str(DB_TW), read_only=True)
    days = [r[0] for r in con.execute(
        "SELECT DISTINCT date FROM tw_daily_prices ORDER BY date").fetchall()]
    con.close()
    return days


def upsert(rows: list[dict]) -> int:
    """v0105:交正典 SUP_MDL753 upsert_rows(去重寫入的唯一實作)。語意照 v0103:鍵已在只補空欄(不覆蓋)、src 不補(不冒名)。"""
    return _LIB.UTILS.upsert_rows(DB_TW, "tw_trading_daily", rows, ["date", "code", "market"], fill=True, no_fill=("src",))


def db_done_lanes(db: Path | None = None) -> set:
    """v0102:checkpoint 自庫重建——tw_trading_daily 已有 (日, 市場) → 該日該車道已完成(換機器/ENG079 整併來的日子不重抓)。"""
    import duckdb
    db = db or DB_TW
    out: set = set()
    if not Path(db).exists():
        return out
    con = duckdb.connect(str(db), read_only=True)
    try:
        if "tw_trading_daily" not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            return out
        cols = {r[0] for r in con.execute("DESCRIBE tw_trading_daily").fetchall()}
        if not {"open", "high", "low"} <= cols:
            return out                            # 還沒有開高低欄=每一天都缺(交易所為主:要補一次)
        for d, mk in con.execute("SELECT DISTINCT CAST(date AS VARCHAR), market FROM tw_trading_daily "
                                 "WHERE open IS NOT NULL AND high IS NOT NULL AND low IS NOT NULL").fetchall():
            for ln, m in LANE_MARKET.items():
                if m == mk:
                    out.add(f"{d}|{ln}")
    finally:
        con.close()
    return out


def coverage(days: list, lanes: list, db: Path | None = None, done: set | None = None) -> dict:
    """v0102 完整性:逐市場「有料日 / 日曆日」+ 缺的日(抓過但空 vs 還沒抓到)。只讀。"""
    import duckdb
    db = db or DB_TW
    have: dict = {m: set() for m in LANE_MARKET.values()}
    if Path(db).exists():
        con = duckdb.connect(str(db), read_only=True)
        try:
            if "tw_trading_daily" in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
                for d, mk in con.execute("SELECT DISTINCT CAST(date AS VARCHAR), market FROM tw_trading_daily").fetchall():
                    have.setdefault(mk, set()).add(d)
        finally:
            con.close()
    out = {}
    for ln in lanes:
        mk = LANE_MARKET[ln]
        miss = [d for d in days if d not in have.get(mk, set())]
        out[mk] = {"have": len(days) - len(miss), "days": len(days), "missing": miss,
                   "fetched_empty": [d for d in miss if done and f"{d}|{ln}" in done]}
    return out


def fetch_lane(day: str, lane: str):
    """一日一車道:統包 curl_json → 表頭動態解析;傳輸敗=None(不記 done,保留重試權);每工保留節流。"""
    ds = day.replace("-", "")
    slash = f"{day[:4]}/{day[5:7]}/{day[8:]}"
    url = (f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={ds}"
           f"&type=ALLBUT0999&response=json") if lane == "twse_mi" else _TPEX_URL.format(slash=slash)
    js = curl_json(url)
    time.sleep(PAUSE_S)
    if js is None:
        return None
    rows = (parse_twse_mi if lane == "twse_mi" else parse_tpex)(js, day)
    src = SRC_TWSE if lane == "twse_mi" else _tpex_src(_TPEX_URL or "")
    for r in rows:
        r["src"] = src                                  # v0103:逐列記來源表(Z180)
    return rows


def _tpex_src(tpl: str) -> str:
    """v0103:TPEX 變體 → 來源名(認不出=TPEX_RWD_UNKNOWN,照實記)。"""
    return next((name for key, name in TPEX_SRC if key in tpl), "TPEX_RWD_UNKNOWN")


#: v0105:每日發行股數史(Z184)——交易所每天都給
SHARES_LANES = {"twse_shares": ("TWSE", "TWSE_RWD_MI_QFIIS"), "tpex_shares": ("TPEX", "TPEX_RWD_OTC_SHARES")}
SHARES_DAILY_SRC = {"TWSE": ("TWSE_RWD_MI_QFIIS",), "TPEX": ("TPEX_RWD_OTC_SHARES", "TPEX_OPENAPI_DAILY_CAPITALS")}
SHARES_CKPT = OUT / "shares_daily_checkpoint.json"
SHARES_PROGRESS = OUT / "shares_daily_progress.json"
SHARES_EVERY = 5                      # 每 5 個交易日取一天(股數只在事件時變;--every 1 逐日)


def _parse_shares(js: dict, iso: str, code_key: str, market: str, src: str) -> list[dict]:
    ft = _find_table(js, (code_key, "發行股數"))
    if not ft:
        return []
    fields, data = ft
    ic, ish = _idx(fields, code_key), _idx(fields, "發行股數")
    out = []
    for r in data:
        code = str(r[ic]).strip()
        if len(code) != 4 or not code.isdigit():
            continue
        sh = _num(r[ish])
        if sh and sh > 0:
            out.append({"asof_date": iso, "code": code, "market": market, "shares_issued": sh, "src": src})
    return out


def parse_twse_qfiis(js: dict, iso: str) -> list[dict]:
    """TWSE 外資及陸資投資持股統計(MI_QFIIS)→ 當天發行股數(四碼)。"""
    return _parse_shares(js, iso, "證券代號", "TWSE", "TWSE_RWD_MI_QFIIS")


def parse_tpex_shares(js: dict, iso: str) -> list[dict]:
    """TPEX 每日收盤行情(otc,type=EW;欄名帶尾空白)→ 當天發行股數(四碼)。"""
    return _parse_shares(js, iso, "代號", "TPEX", "TPEX_RWD_OTC_SHARES")


def fetch_shares(day: str, lane: str):
    """一日一車道;傳輸敗=None(不記 done,保留重試權);每工保留節流。"""
    ds, slash = day.replace("-", ""), f"{day[:4]}/{day[5:7]}/{day[8:]}"
    url = (f"https://www.twse.com.tw/rwd/zh/fund/MI_QFIIS?date={ds}&selectType=ALLBUT0999&response=json" if lane == "twse_shares"
           else f"https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date={slash}&type=EW&response=json")
    js = curl_json(url)
    time.sleep(PAUSE_S)
    if js is None:
        return None
    return (parse_twse_qfiis if lane == "twse_shares" else parse_tpex_shares)(js, day)


def shares_done(db: Path | None = None) -> set:
    """先查庫:那天那個市場已有**每日**股數(任何每日來源,含 ENG055 L2 的 Capitals)=完成。快照(出表)不算每日。"""
    import duckdb
    db = db or DB_TW
    if not Path(db).exists():
        return set()
    con = duckdb.connect(str(db), read_only=True)
    try:
        if SHARES_TABLE not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            return set()
        out = set()
        for lane, (mkt, _src) in SHARES_LANES.items():
            srcs = SHARES_DAILY_SRC[mkt]
            q = (f"SELECT DISTINCT CAST(asof_date AS VARCHAR) FROM {SHARES_TABLE} WHERE market = ? AND src IN ("
                 + ",".join("?" * len(srcs)) + ")")
            out |= {f"{r[0]}|{lane}" for r in con.execute(q, [mkt, *srcs]).fetchall()}
        return out
    finally:
        con.close()


def shares(max_days: int | None = None, workers: int | None = None, every: int | None = None, *, lane_fn=None, persist_fn=None,
           days_fn=None, lanes=None, ckpt: Path | None = None, db: Path | None = None, gate: bool | None = None, stream=None,
           tty: bool | None = None, progress_path: Path | None = None, accel=None) -> int:
    """v0105:每日發行股數史。先查庫(checkpoint ∪ 庫內已有每日股數)→ 抽樣日 × 兩車道只抓缺的 → 正典 batch_fetch → 報完整性 → 刷新市值檢視表。"""
    out = stream or sys.stdout

    def say(msg: str) -> None:
        out.write(msg + "\n")
        out.flush()
    if not (gate if gate is not None else gate_open()):
        say("[FAIL-CLOSED] 同意閘未開")
        return 2
    if lane_fn is None and not _net_ready():
        say("[FAIL] 統包網路工具缺席或缺 curl_json 車道(SUP_MDL740;不自己連)")
        return 1
    lane_fn = lane_fn or fetch_shares
    db = db or DB_TW
    persist_fn = persist_fn or (lambda rows: _LIB.UTILS.upsert_rows(db, SHARES_TABLE, rows, ["asof_date", "code", "market"]))
    ckpt = ckpt or SHARES_CKPT
    workers = max(1, int(workers or WORKERS_DEFAULT))
    every = max(1, int(every or SHARES_EVERY))
    accel = VIA_ACCEL if accel is None else accel
    days = (days_fn or trading_days)()
    if not days:
        say("[FAIL] 交易日曆空(先跑價格回補)")
        return 1
    picked = sorted(set(days[::every]) | {days[-1]})       # 抽樣,最後一天一定取
    lanes = lanes or list(SHARES_LANES)
    ck = json.loads(Path(ckpt).read_text(encoding="utf-8")) if Path(ckpt).exists() else {"done": []}
    done = set(ck["done"])
    from_db = shares_done(db) - done
    done |= from_db
    todo = [(d_, ln) for d_ in picked for ln in lanes if f"{d_}|{ln}" not in done]
    if max_days:
        lim = sorted({d_ for d_, _ in todo})[:max_days]
        todo = [(d_, ln) for d_, ln in todo if d_ in lim]
    say(f"[股數史] 交易日 {len(days)} · 每 {every} 日取一天 → {len(picked)} 天 · 庫內已有 +{len(from_db)} 日×車道(不重抓)· 待抓 {len(todo)} 日×車道 · 工 {workers}")
    prog = _LIB.UTILS.BatchProgress(len(todo), stream=stream, tty=tty,
                                    progress_path=SHARES_PROGRESS if progress_path is None else progress_path,
                                    label="股數史", schema="VIA.SharesHistoryProgress.v1")
    r = _LIB.UTILS.batch_fetch(todo, lambda it: lane_fn(it[0], it[1]), lambda _tb, rows: persist_fn(rows), done=done, ckpt=ckpt,
                               workers=workers, accel=accel, flush_n=FLUSH_N, prog=prog, say=say)
    if r["rc"] == 130:
        say(f"[中斷] Ctrl+C:已落 {r['flushed']} 列 + checkpoint;重跑續補(零重抓)")
        return 130
    for ln in lanes:
        have = sum(1 for d_ in picked if f"{d_}|{ln}" in done)
        say(f"[完整性] {ln} {have}/{len(picked)} 天" + ("" if have == len(picked) else f" · 缺 {len(picked) - have}(傳輸敗保留重試權)"))
    if persist_fn is not None and lane_fn is fetch_shares:          # 真抓才刷新市值檢視表(注入的測試不碰)
        try:
            mc = mcap(db)
            say(f"[市值] {mc['state']} · " + " · ".join(f"{m} 嚴格 {v['strict']} / 近似 {v['later']}" for m, v in mc["per_market"].items()))
        except Exception as exc:
            say(f"[市值] 刷新失敗:{type(exc).__name__}: {str(exc)[:120]}")
    return 0


XCHECK_TABLE = "tw_market_cap_xcheck"
XCHECK_TOL = 0.01                     # 股數差 >1% 標 DIFF


def xcheck(db: Path | None = None, codes: list | None = None, top: int = 30, net=None, today: str | None = None,
           gate: bool | None = None) -> dict:
    """v0104:跟其他看盤網站核對(操作員令)。交易所股數/市值 × Yahoo quoteSummary,逐檔記比值,只報不改。
    先查庫:今天已核過的碼不重抓;走統包 yahoo_quote_summary(閘關=DENY 照實)。
    v0106:本支的同意閘 gate_open() 在載入網路工具之前先判;每個市場(--codes 則每個代號)用自己最新一個有嚴格市值的交易日;
    候選空=NODATA;要核的代號有的沒有嚴格市值=PARTIAL(列在 missing)。"""
    import duckdb
    db = db or DB_TW
    today = today or _date.today().isoformat()
    out = {"state": "NODATA", "date": None, "dates": {}, "checked": 0, "skipped_today": 0, "rows": [], "diffs": [], "failed": [],
           "missing": []}
    if not Path(db).exists():
        out["why"] = "庫不在"
        return out
    con = duckdb.connect(str(db), read_only=True)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if not {"tw_trading_daily", SHARES_TABLE} <= have:
            out["why"] = f"缺表 {sorted({'tw_trading_daily', SHARES_TABLE} - have)}(發行股數由 VDF_ENG055 v0115+ L1 收)"
            return out
        # v0106:每個市場各用自己最新一個有嚴格市值的交易日(某市場晚一天進庫,不會因此整個市場被跳過)
        lat = {m_: str(d_) for m_, d_ in con.execute(
            f"SELECT market, CAST(max(date) AS VARCHAR) FROM ({_MCAP_SQL}) m WHERE market_cap IS NOT NULL GROUP BY 1").fetchall() if d_}
        if not lat:
            out["why"] = "沒有嚴格市值(股數出表日之後還沒有交易所收盤)"
            return out
        out["dates"], out["date"] = lat, max(lat.values())
        # --codes:每個代號用它自己的最新日;沒給:每個市場的最新日,兩市場合起來取前 N 大
        key, flt, args = (("code", " AND code IN (" + ",".join("?" * len(codes)) + ")", list(codes)) if codes
                          else ("market", "", []))
        cand = con.execute(
            f"WITH m AS (SELECT * FROM ({_MCAP_SQL}) x WHERE market_cap IS NOT NULL{flt}), "
            f"l AS (SELECT {key} AS k, max(date) AS d FROM m GROUP BY 1) "
            f"SELECT m.code, m.market, m.close, m.shares_issued, CAST(m.shares_asof AS VARCHAR), m.market_cap, CAST(m.date AS VARCHAR) "
            f"FROM m JOIN l ON m.{key} = l.k AND m.date = l.d ORDER BY m.market_cap DESC LIMIT ?",
            args + [int(top) if not codes else len(codes)]).fetchall()
        done = ({r[0] for r in con.execute(f"SELECT code FROM {XCHECK_TABLE} WHERE check_date = ?", [today]).fetchall()}
                if XCHECK_TABLE in have else set())
        # 交易所**最新一份**股數(可能晚於價格那天):用來分「快照舊了」與「口徑真的不同」
        newest = {(c_, m_): (a_, v_) for c_, m_, a_, v_ in con.execute(
            f"SELECT code, market, max(asof_date), arg_max(shares_issued, asof_date) FROM {SHARES_TABLE} "
            f"WHERE shares_issued > 0 GROUP BY 1, 2").fetchall()}
    finally:
        con.close()
    if codes:
        seen = {c[0] for c in cand}
        out["missing"] = [c for c in codes if c not in seen]
    if not cand:                                     # v0106:候選空≠「今天已核過」;講明是哪幾檔沒有嚴格市值
        out["why"] = (f"要核的代號都沒有嚴格市值:{','.join(out['missing'][:10])}" if codes else "沒有嚴格市值的候選")
        return out
    ok_state = "PARTIAL" if out["missing"] else "OK"
    miss = f"沒有嚴格市值 {len(out['missing'])} 檔:{','.join(out['missing'][:10])}" if out["missing"] else ""
    todo = [c for c in cand if c[0] not in done]
    out["skipped_today"] = len(cand) - len(todo)
    if not todo:
        out["state"] = ok_state
        out["why"] = f"今天已核過 {out['skipped_today']} 檔(不重抓)" + (f" · {miss}" if miss else "")
        return out
    # v0106:本支的同意閘先判,再載入/呼叫網路工具(工具的閘二只看有沒有設值,啟動器預設的 OFF 在那裡算開)
    if not (gate if gate is not None else gate_open()):
        out["state"], out["why"] = "DENY", "同意閘未開(VIA_NET_CONSENT 與 VIA_SCRAPE_CONSENT 都要 YES;不代設)"
        return out
    net = net if net is not None else _net_or_none()
    if net is None or not hasattr(net, "yahoo_quote_summary"):
        out["state"], out["why"] = "FAIL", "網路工具缺 yahoo_quote_summary 車道(SUP_MDL740;不自己連)"
        return out
    sym = {c[0]: f"{c[0]}.{'TW' if c[1] == 'TWSE' else 'TWO'}" for c in todo}
    r = net.yahoo_quote_summary(list(sym.values()), modules="price,defaultKeyStatistics")
    got = {x.get("symbol"): x for x in (r.get("rows") or [])}
    if not got:
        out["state"], out["why"] = (r.get("state") or "FAIL"), str(r.get("note", ""))[:120]   # 閘關 DENY / 握手敗 FAIL 照實
        return out
    rows = []
    for code, mkt, close, sh, asof, mc, dt in todo:
        y = got.get(sym[code])
        if not y:                                    # 整批有回、這一檔沒資料=明確結果(記下來,當天不重問);整批連不上才留重試權
            out["failed"].append(code)
            y = {}
        ysh, ymc, ypx = y.get("shares_outstanding"), y.get("market_cap"), y.get("price")
        rs = round(ysh / sh, 6) if ysh and sh else None
        n_asof, n_sh = newest.get((code, mkt), (asof, sh))
        rn = round(ysh / n_sh, 6) if ysh and n_sh else None
        rows.append({"check_date": today, "code": code, "market": mkt, "exchange_date": dt, "exchange_close": close,
                     "exchange_shares": sh, "exchange_asof": asof, "exchange_mcap": mc, "yahoo_shares": ysh, "yahoo_mcap": ymc,
                     "yahoo_price": ypx, "ratio_shares": rs, "exchange_shares_latest": n_sh,
                     "exchange_asof_latest": str(n_asof), "ratio_shares_latest": rn,
                     "ratio_price": round(ypx / close, 6) if ypx and close else None,
                     "ratio_mcap": round(ymc / mc, 6) if ymc and mc else None,
                     "flag": ("NO_YAHOO_ROW" if not y else ("NO_YAHOO_SHARES" if rs is None
                              else ("SAME" if abs(rs - 1) <= XCHECK_TOL
                                    # 交易所之後的出表已跟上 Yahoo=價格那天用的快照舊了(不是口徑差)
                                    else ("SNAPSHOT_STALE" if rn is not None and abs(rn - 1) <= XCHECK_TOL else "DIFF")))),
                     "src": "YAHOO_QUOTESUMMARY"})
    if rows:                                         # v0107:交正典(鍵 check_date+code;一天一份,當天已核的不重寫)
        _LIB.UTILS.upsert_rows(db, XCHECK_TABLE, rows, ["check_date", "code"])
    out.update({"state": ok_state, "checked": sum(1 for x in rows if x["flag"] != "NO_YAHOO_ROW"), "rows": rows,
                "diffs": [x for x in rows if x["flag"] == "DIFF"]})
    if miss:
        out["why"] = miss
    return out


def mcap(db: Path | None = None, write: bool = True, top: int = 5) -> dict:
    """v0103:市值 = 交易所收盤 × 交易所發行股數(操作員令「市值以交易所為主」)。
    write=True 建/刷新檢視表 tw_market_cap_daily(全樹唯一一處);write=False 唯讀、不建(verify 用)。
    回:逐市場 列數 / 嚴格(當天或之前有股數)/ 近似(只有之後的股數)/ 無股數、最新日前幾大、股數跳動。"""
    import duckdb
    db = db or DB_TW
    out = {"state": "NODATA", "view": MCAP_VIEW, "per_market": {}, "latest": None, "top": [], "jumps": []}
    if not Path(db).exists():
        out["why"] = "庫不在"
        return out
    con = duckdb.connect(str(db), read_only=not write)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        miss = sorted({"tw_trading_daily", SHARES_TABLE} - have)
        if miss:
            out["why"] = f"缺表 {miss}(發行股數由 VDF_ENG055 v0115+ L1 收;那一道要同意閘)"
            return out
        if write:
            con.execute(f"CREATE OR REPLACE VIEW {MCAP_VIEW} AS {_MCAP_SQL}")
            src = MCAP_VIEW
        else:
            src = f"({_MCAP_SQL})"
        for m, n, n_s, n_l, md in con.execute(
                f"SELECT market, count(*), count(market_cap), count(market_cap_later_shares), max(date) "
                f"FROM {src} m GROUP BY 1 ORDER BY 1").fetchall():
            out["per_market"][m] = {"rows": n, "strict": n_s, "later": n_l, "none": n - n_s - n_l, "max_date": str(md)}
        latest = con.execute(f"SELECT max(date) FROM {src} m WHERE market_cap IS NOT NULL").fetchone()[0]
        if latest:
            out["latest"] = str(latest)
            out["top"] = [dict(zip(("code", "market", "close", "shares_issued", "shares_asof", "market_cap"), r)) for r in con.execute(
                f"SELECT code, market, close, shares_issued, CAST(shares_asof AS VARCHAR), market_cap FROM {src} m "
                f"WHERE date = ? AND market_cap IS NOT NULL ORDER BY market_cap DESC LIMIT {int(top)}", [latest]).fetchall()]
        out["jumps"] = [dict(zip(("code", "market", "asof_prev", "shares_prev", "asof", "shares", "ratio"), r)) for r in con.execute(f"""
            WITH s AS (SELECT code, market, TRY_CAST(asof_date AS DATE) AS a, max(shares_issued) AS sh FROM {SHARES_TABLE}
                       WHERE shares_issued > 0 AND TRY_CAST(asof_date AS DATE) IS NOT NULL GROUP BY 1, 2, 3),
                 l AS (SELECT *, LAG(a) OVER w AS ap, LAG(sh) OVER w AS shp FROM s WINDOW w AS (PARTITION BY code, market ORDER BY a))
            SELECT code, market, CAST(ap AS VARCHAR), shp, CAST(a AS VARCHAR), sh, round(sh / shp, 4) FROM l
            WHERE shp > 0 AND abs(sh / shp - 1) >= {MCAP_JUMP} ORDER BY abs(sh / shp - 1) DESC, code LIMIT 20""").fetchall()]
        out["state"] = "OK"
    finally:
        con.close()
    return out


def run(max_days: int | None = None, workers: int | None = None, *, lane_fn=None, persist_fn=None, days_fn=None, lanes=None,
        ckpt: Path | None = None, db: Path | None = None, gate: bool | None = None, stream=None, tty: bool | None = None,
        progress_path: Path | None = None, accel=None) -> int:
    """v0102:先查庫缺啥(checkpoint ∪ 庫內已有)→ 只抓缺的 → 正典 batch_fetch(加速器平行 · 每 40 件落庫 · Ctrl+C 安全)→ 報完整性"""
    out = stream or sys.stdout

    def say(msg: str) -> None:
        out.write(msg + "\n")
        out.flush()
    if not (gate if gate is not None else gate_open()):
        say("[FAIL-CLOSED] 同意閘未開")
        return 2
    if lane_fn is None and not _net_ready():
        say("[FAIL] 統包網路工具缺席或缺 curl_json 車道(SUP_MDL740;不退回自己打 curl——那條路不經同意閘與法遵層)")
        return 1
    lane_fn = lane_fn or fetch_lane
    persist_fn = persist_fn or upsert
    ckpt = ckpt or CKPT
    db = db or DB_TW
    workers = max(1, int(workers or WORKERS_DEFAULT))
    accel = VIA_ACCEL if accel is None else accel
    days = (days_fn or trading_days)()
    if not days:
        say("[FAIL] 交易日曆空(先跑價格回補)")
        return 1
    if lanes is None:
        slash_last = f"{days[-1][:4]}/{days[-1][5:7]}/{days[-1][8:]}"
        tpex_ok = _tpex_probe(slash_last) is not None
        lanes = ["twse_mi"] + (["tpex_quotes"] if tpex_ok else [])
        if not tpex_ok:
            say("[誠實] TPEX 端點探測全敗=TPEX_PENDING(僅回補 TWSE)")
    ck = json.loads(Path(ckpt).read_text(encoding="utf-8")) if Path(ckpt).exists() else {"done": []}
    done = set(ck["done"])
    from_db = db_done_lanes(db) - done
    done |= from_db
    todo = [(d, ln) for d in days for ln in lanes if f"{d}|{ln}" not in done]
    if max_days:
        lim = sorted({d for d, _ in todo})[:max_days]
        todo = [(d, ln) for d, ln in todo if d in lim]
    say(f"[成交值] 交易日 {len(days)} · checkpoint 自庫重建 +{len(from_db)} 日×車道(庫內已有=不重抓)· 待抓 {len(todo)} 日×車道"
        f" · 工 {workers}(每工節流 {PAUSE_S}s;SuperAccel {'在' if accel is not None and hasattr(accel, 'accel_map') else '缺=循序'})")
    prog = _LIB.UTILS.BatchProgress(len(todo), stream=stream, tty=tty, progress_path=PROGRESS if progress_path is None else progress_path,
                                    label="成交值", schema="VIA.TradingValueProgress.v1")

    def _say_prog(msg: str) -> None:
        prog.stream.write(("\n" if prog.tty and not msg.startswith("\n") else "") + msg + "\n")
        prog.stream.flush()

    r = _LIB.UTILS.batch_fetch(todo, lambda it: lane_fn(it[0], it[1]), lambda _tb, rows: persist_fn(rows), done=done, ckpt=ckpt,
                               workers=workers, accel=accel, flush_n=FLUSH_N, prog=prog, say=_say_prog)
    if r["rc"] == 130:
        say(f"[中斷] Ctrl+C:已落緩衝列 {r['flushed']} 列 + checkpoint {len(done)} 日×車道(進度 {prog.done}/{prog.total});重跑 via-tval run 續補(零重抓)")
        return 130
    say(f"[畢] OK {prog.ok} · 空 {prog.empty} · 敗 {prog.fail}(空=非交易面/端點無資料;敗=傳輸敗保留重試權;誠實計數)· 落庫 {r['flushed']} 列 · checkpoint {len(done)} 日×車道")
    cov = coverage(days, lanes, db, done)
    for mk, c in cov.items():
        say(f"[完整性] {mk} 有料 {c['have']}/{c['days']} 日" + (f" · 缺 {len(c['missing'])}(抓過但空 {len(c['fetched_empty'])};例 {', '.join(c['missing'][:5])})" if c["missing"] else " · 齊"))
    if persist_fn is upsert:                           # v0103:真庫才刷新市值檢視表(注入的測試落庫不碰)
        try:
            mc = mcap(db)
            say(f"[市值] {mc['state']} · " + (" · ".join(f"{m} 嚴格 {v['strict']} / 近似 {v['later']} / 無股數 {v['none']}"
                                                        for m, v in mc["per_market"].items()) or mc.get("why", "")))
        except Exception as exc:                        # 市值刷新失敗不改本次擷取的結論(照實印)
            say(f"[市值] 刷新失敗:{type(exc).__name__}: {str(exc)[:120]}")
    return 0


def verify(db: Path | None = None, tol: float = 0.005, sample: int = 5) -> dict:
    """v0102(唯讀):交易所收盤 × Yahoo 收盤逐列核對。交易所為主;Yahoo 的 close 只拿來核對,它的主用途是 adj_close(操作員令)。
    每碼按日期看 r = Yahoo close ÷ 交易所 close:
      STALE_1D  單日陳價——前後兩天的 r 彼此一致、當天卻不一樣(先判:當天剛好 r=1 但前後都乘了配股段,也是 Yahoo 那天漏回調;Z175)
      SAME      |r−1| ≤ tol
      STOCK_SEG 其餘——Yahoo 事後回乘配股/拆股的持續換階(預期中的,不是錯)
    另數只有一邊有料的碼×日,與整天只有一邊有的日子(Z174)。"""
    import duckdb
    db = db or DB_TW
    out = {"state": "NODATA", "counts": {}, "stale_samples": [], "only_exchange": 0, "only_yahoo": 0,
           "days_only_yahoo": [], "days_only_exchange": [], "tol": tol,
           "market_absent_yahoo": [], "market_absent_exchange": [], "thin_yahoo": {}, "thin_exchange": {}, "src_mix": {}}
    if not Path(db).exists():
        out["why"] = "庫不在"
        return out
    con = duckdb.connect(str(db), read_only=True)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if not {"tw_trading_daily", "tw_daily_prices"} <= have:
            out["why"] = f"缺表:{sorted({'tw_trading_daily', 'tw_daily_prices'} - have)}"
            return out
        con.execute(f"""CREATE TEMP TABLE _j AS
            WITH j AS (
              SELECT CAST(t.date AS VARCHAR) AS d, t.code, t.market, t.close AS xc, p.close AS yc
              FROM tw_trading_daily t JOIN tw_daily_prices p
                ON CAST(p.date AS VARCHAR) = CAST(t.date AS VARCHAR) AND split_part(p.ticker, '.', 1) = t.code
              WHERE t.close > 0 AND p.close > 0)
            SELECT *, yc / xc AS r, LAG(yc / xc) OVER w AS rp, LEAD(yc / xc) OVER w AS rn
            FROM j WINDOW w AS (PARTITION BY code ORDER BY d)""")
        kind = (f"CASE WHEN rp IS NOT NULL AND rn IS NOT NULL AND abs(rp - rn) <= {tol} * rp AND abs(r - rp) > {tol} * rp THEN 'STALE_1D' "
                f"WHEN abs(r - 1) <= {tol} THEN 'SAME' ELSE 'STOCK_SEG' END")
        out["counts"] = dict(con.execute(f"SELECT {kind} AS k, count(*) FROM _j GROUP BY 1 ORDER BY 1").fetchall())
        out["stale_samples"] = [dict(zip(("date", "code", "exchange_close", "yahoo_close", "ratio", "ratio_prev"), x)) for x in con.execute(
            f"SELECT d, code, xc, yc, round(r, 4), round(rp, 4) FROM _j WHERE {kind} = 'STALE_1D' "
            f"ORDER BY abs(r - rp) DESC LIMIT {int(sample)}").fetchall()]
        out["only_exchange"] = con.execute(
            "SELECT count(*) FROM tw_trading_daily t WHERE t.close > 0 AND NOT EXISTS (SELECT 1 FROM tw_daily_prices p "
            "WHERE CAST(p.date AS VARCHAR) = CAST(t.date AS VARCHAR) AND split_part(p.ticker, '.', 1) = t.code)").fetchone()[0]
        out["only_yahoo"] = con.execute(
            "SELECT count(*) FROM tw_daily_prices p WHERE p.close > 0 AND p.ticker <> '_NOOP_' AND NOT EXISTS (SELECT 1 FROM tw_trading_daily t "
            "WHERE CAST(t.date AS VARCHAR) = CAST(p.date AS VARCHAR) AND t.code = split_part(p.ticker, '.', 1))").fetchone()[0]
        xd = {r[0] for r in con.execute("SELECT DISTINCT CAST(date AS VARCHAR) FROM tw_trading_daily WHERE close > 0").fetchall()}
        yd = {r[0] for r in con.execute("SELECT DISTINCT CAST(date AS VARCHAR) FROM tw_daily_prices WHERE close > 0 AND ticker <> '_NOOP_'").fetchall()}
        out["days_only_yahoo"] = sorted(yd - xd)
        out["days_only_exchange"] = sorted(xd - yd)
        # 薄日(逐市場):一邊的檔數不到另一邊一半=那天那一邊大半沒抓到(批730:2025-08-01 交易所 829 檔、Yahoo 3 列)
        per = con.execute("""
            WITH x AS (SELECT CAST(date AS VARCHAR) d, market m, count(*) n FROM tw_trading_daily WHERE close > 0 GROUP BY 1, 2),
                 y AS (SELECT CAST(date AS VARCHAR) d, CASE WHEN ticker LIKE '%.TWO' THEN 'TPEX' WHEN ticker LIKE '%.TW' THEN 'TWSE' END m,
                              count(*) n FROM tw_daily_prices WHERE close > 0 AND ticker <> '_NOOP_' GROUP BY 1, 2)
            SELECT coalesce(x.d, y.d), coalesce(x.m, y.m), coalesce(x.n, 0), coalesce(y.n, 0)
            FROM x FULL JOIN y ON x.d = y.d AND x.m = y.m WHERE coalesce(x.m, y.m) IS NOT NULL""").fetchall()
        for m in sorted({r[1] for r in per}):
            rows_m = [r for r in per if r[1] == m]
            xn, yn = sum(r[2] for r in rows_m), sum(r[3] for r in rows_m)
            if xn and not yn:
                out["market_absent_yahoo"].append(m)        # 整個市場只有交易所有(例:上市不在 Yahoo 價表=Z62)
                continue
            if yn and not xn:
                out["market_absent_exchange"].append(m)
                continue
            ty = sorted(r[0] for r in rows_m if r[3] < 0.5 * r[2])
            tx = sorted(r[0] for r in rows_m if r[2] < 0.5 * r[3])
            if ty:
                out["thin_yahoo"][m] = ty
            if tx:
                out["thin_exchange"][m] = tx
        # v0103:各市場的來源表分布(Z180;NULL=v0102 以前抓的,口徑未記)
        cols = {r[0] for r in con.execute("DESCRIBE tw_trading_daily").fetchall()}
        if "src" in cols:
            for m, sname, n in con.execute("SELECT market, coalesce(src, '未記'), count(*) FROM tw_trading_daily "
                                          "GROUP BY 1, 2 ORDER BY 1, 2").fetchall():
                out["src_mix"].setdefault(m, {})[sname] = n
        else:
            out["src_mix"] = {"*": {"未記": con.execute("SELECT count(*) FROM tw_trading_daily").fetchone()[0]}}
        out["state"] = "OK"
    finally:
        con.close()
    return out


def status() -> int:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    n, mn, mx = con.execute(
        "SELECT COUNT(*),MIN(date),MAX(date) FROM tw_trading_daily").fetchone()
    per = con.execute("SELECT market, COUNT(DISTINCT date) FROM tw_trading_daily "
                      "WHERE trade_value IS NOT NULL GROUP BY market").fetchall()
    con.close()
    done = len(json.loads(CKPT.read_text())["done"]) if CKPT.exists() else 0
    print(f"tw_trading_daily {n:,} 列 · {mn}→{mx} · 覆蓋日/市場 {per} · checkpoint {done}")
    return 0


def selftest() -> int:
    global curl_json, _TPEX_URL, PAUSE_S          # v0103 ⑫ 換假 curl_json / 變體 / 節流(跑完原樣還回)
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 同意閘 fail-closed", not gate_open({}) and gate_open(
        {"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}))

    fx = {"tables": [{"fields": ["日期", "指數"], "data": []},
                     {"fields": ["證券代號", "證券名稱", "成交股數", "成交筆數", "成交金額",
                                 "開盤價", "最高價", "最低價", "收盤價"],
                      "data": [["2330", "台積電", "25,000,000", "50,000", "30,000,000,000",
                                "1200", "1210", "1190", "1200"],
                               ["00500", "ETF樣", "1", "1", "1", "1", "1", "1", "1"]]}]}
    r = parse_twse_mi(fx, "2026-08-25")
    chk("② MI_INDEX 表頭動態對位(四碼濾+值真;v0102 開高低一併收)",
        len(r) == 1 and r[0]["trade_value"] == 3e10 and r[0]["close"] == 1200.0
        and (r[0]["open"], r[0]["high"], r[0]["low"]) == (1200.0, 1210.0, 1190.0))

    fx2 = {"tables": [{"fields": ["代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低",
                                  "成交股數", "成交金額(元)", "成交筆數"],
                       "data": [["5347", "世界", "100", "+1", "99", "101", "98",
                                 "3,000,000", "300,000,000", "8,000"]]}]}
    r2 = parse_tpex(fx2, "2026-08-25")
    chk("③ TPEX 表頭動態對位(v0102 開高低一併收)", len(r2) == 1 and r2[0]["trade_value"] == 3e8
        and r2[0]["market"] == "TPEX" and (r2[0]["open"], r2[0]["high"], r2[0]["low"], r2[0]["close"]) == (99.0, 101.0, 98.0, 100.0))

    import tempfile
    import duckdb
    global DB_TW
    _db = DB_TW
    with tempfile.TemporaryDirectory() as td:
        DB_TW = Path(td) / "t.duckdb"
        con = duckdb.connect(str(DB_TW))
        con.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR)")
        con.executemany("INSERT INTO tw_daily_prices VALUES (?,?)",
                        [("2026-08-22", "2330.TW"),
                         ("2026-08-25", "2330.TW"),
                         ("2026-08-26", "2317.TW")])
        con.close()
        days = trading_days()
        chk("④ 交易日曆=已庫價格日期(暫存夾具；覆蓋率另由 census 驗)",
            days == ["2026-08-22", "2026-08-25", "2026-08-26"],
            f"({len(days)} 日)")
        n1 = upsert(r)
        n2 = upsert(r)  # 冪等
        # v0102 補不足、不覆蓋:舊列缺開高低 → 補;已有值 → 不動
        upsert([{"date": "2026-08-26", "code": "5347", "market": "TPEX", "volume": 1.0, "trade_value": 1.0, "transactions": 1.0,
                 "close": 100.0, "open": None, "high": None, "low": None}])
        upsert([{"date": "2026-08-26", "code": "5347", "market": "TPEX", "volume": 1.0, "trade_value": 1.0, "transactions": 1.0,
                 "close": 100.0, "open": 99.0, "high": 101.0, "low": 98.0}])
        upsert([{"date": "2026-08-26", "code": "5347", "market": "TPEX", "volume": 9.0, "trade_value": 9.0, "transactions": 9.0,
                 "close": 999.0, "open": 999.0, "high": 999.0, "low": 999.0}])
        _c5 = duckdb.connect(str(DB_TW), read_only=True)
        f5 = _c5.execute("SELECT open, high, low, close, volume, count(*) OVER () FROM tw_trading_daily WHERE code='5347'").fetchone()
        _c5.close()
        chk("⑤ 按欄名 upsert+anti-join 冪等;v0102 補不足、不覆蓋(缺開高低的舊列補上,已有值 999 不蓋)",
            n1 == 1 and n2 == 1 and f5 == (99.0, 101.0, 98.0, 100.0, 1.0, 1), f"({f5})")
    DB_TW = _db

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 紀律宣告(表頭動態對位/傳輸敗不記 done/TPEX 誠實 PENDING)",
        "零欄序寫死" in src and "保重試權" in src and "TPEX_PENDING" in src)
    # ── v0102 ⑦–⑩:擷取五條紀律(自庫重建 · 中斷/續補/冪等/閘/工具缺席 · 完整性 · 零 subprocess)──
    import io as _io
    import inspect as _insp
    global _NET
    with tempfile.TemporaryDirectory() as td7:
        root = Path(td7)
        db7 = root / "m.duckdb"
        con = duckdb.connect(str(db7))
        con.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, volume DOUBLE, trade_value DOUBLE, "
                    "transactions DOUBLE, close DOUBLE, open DOUBLE, high DOUBLE, low DOUBLE)")
        con.execute("INSERT INTO tw_trading_daily VALUES ('2026-09-01','2330','TWSE',1,1,1,1,1,1,1),('2026-09-02','5347','TPEX',1,1,1,1,1,1,1),"
                    "('2026-09-03','2330','TWSE',1,1,1,1,NULL,NULL,NULL)")      # 09-03 TWSE 只有收盤(v0101 抓的)=還缺開高低
        con.close()
        dd = db_done_lanes(db7)
        _db_old = root / "old.duckdb"                  # v0101 的舊庫:還沒有開高低欄 → 每一天都算缺
        _co = duckdb.connect(str(_db_old))
        _co.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
        _co.execute("INSERT INTO tw_trading_daily VALUES ('2026-09-01','2330','TWSE',1)")
        _co.close()
        dd_old = db_done_lanes(_db_old)
        days3, lanes2 = ["2026-09-01", "2026-09-02", "2026-09-03"], ["twse_mi", "tpex_quotes"]
        calls = {"n": 0}

        def _row(day, lane):
            return [{"date": day, "code": "9999", "market": LANE_MARKET[lane], "volume": 1.0, "trade_value": 1.0,
                     "transactions": 1.0, "close": 1.0, "open": 1.0, "high": 1.0, "low": 1.0}]

        def lane_int(day, lane):                 # 第 3 次呼叫=操作員 Ctrl+C
            calls["n"] += 1
            if calls["n"] == 3:
                raise KeyboardInterrupt
            return _row(day, lane)
        _db_saved = DB_TW
        DB_TW = db7
        try:
            so, ck = _io.StringIO(), root / "ck.json"
            kw = dict(days_fn=lambda: days3, lanes=lanes2, ckpt=ck, db=db7, gate=True, stream=so, tty=False, progress_path=root / "P.json")
            rc1 = run(None, 1, lane_fn=lane_int, **kw)
            ck1 = json.loads(ck.read_text(encoding="utf-8"))["done"]
            pj1 = json.loads((root / "P.json").read_text(encoding="utf-8"))
            rc2 = run(None, 2, lane_fn=_row, **kw)
            ck2 = json.loads(ck.read_text(encoding="utf-8"))["done"]
            rc3 = run(None, 1, lane_fn=_row, **kw)
            rcg = run(None, 1, lane_fn=_row, **dict(kw, gate=False, stream=_io.StringIO()))
            _g = globals()
            _sv = (_g["_net_or_none"], _NET)
            try:
                _g["_net_or_none"] = lambda: None
                _NET = None
                ot = _io.StringIO()
                rct = run(None, 1, **dict(kw, stream=ot))
            finally:
                _g["_net_or_none"], _NET = _sv
            days4 = days3 + ["2026-09-04"]
            cov_a = coverage(days4, lanes2, db7, set(ck2))
            cov_b = coverage(days4, lanes2, db7, set(ck2) | {"2026-09-04|twse_mi"})
            n_rows = duckdb.connect(str(db7), read_only=True).execute(
                "SELECT count(*) FROM tw_trading_daily WHERE code = '9999' OR open IS NOT NULL").fetchone()[0]
        finally:
            DB_TW = _db_saved
    chk("⑦ v0102 先查庫缺啥:checkpoint 自庫重建(tw_trading_daily 已有 (日, 市場) **且有開高低** → 該日該車道已完成;只有收盤的 09-03 算缺;"
        "v0101 舊庫(還沒有開高低欄)=每一天都缺——交易所為主要補一次)",
        dd == {"2026-09-01|twse_mi", "2026-09-02|tpex_quotes"} and dd_old == set(), f"({sorted(dd)} · 舊庫 {sorted(dd_old)})")
    chk("⑧ v0102 批次交正典 batch_fetch:3 日×2 車道=6,庫內已有 2(有開高低)→ 待抓 4;第 3 次 Ctrl+C → 已落 2 件+checkpoint 4(在飛塊不記 done)rc130、"
        "進度檔 INTERRUPTED;2 工走加速器續補 → rc0 6/6;再跑待抓 0;庫內每 (日,代號,市場) 一列(去重);同意閘關 rc2;網路工具缺席=rc1 不自己打 curl",
        rc1 == 130 and len(ck1) == 4 and pj1["state"] == "INTERRUPTED" and rc2 == 0 and len(ck2) == 6 and rc3 == 0
        and "待抓 0 " in so.getvalue() and n_rows == 6 and rcg == 2 and rct == 1 and "統包網路工具缺席" in ot.getvalue(),
        f"(rc {rc1}/{rc2}/{rc3}/{rcg}/{rct} · ck {len(ck1)}/{len(ck2)} · 列 {n_rows})")
    chk("⑨ v0102 完整性:逐市場有料日/日曆日;多一天 09-04 → TWSE/TPEX 各 3/4、缺 09-04;那天記過 done=「抓過但空」,沒記=「還沒抓到」",
        cov_a["TWSE"]["have"] == 3 and cov_a["TWSE"]["missing"] == ["2026-09-04"] and cov_a["TWSE"]["fetched_empty"] == []
        and cov_b["TWSE"]["fetched_empty"] == ["2026-09-04"] and cov_a["TPEX"]["have"] == 3,
        f"(TWSE {cov_a['TWSE']['have']}/{cov_a['TWSE']['days']} · 抓過但空 {cov_b['TWSE']['fetched_empty']})")
    _src = _insp.getsource(curl_json) + _insp.getsource(run) + _insp.getsource(fetch_lane)
    chk("⑩ v0102 網路工具與加速器覆蓋:curl_json/run/fetch_lane 原始碼零 subprocess(工具缺席不後備)· 批次迴圈=正典 batch_fetch · 進度條=正典 BatchProgress",
        "subprocess" not in _src and "_LIB.UTILS.batch_fetch(" in _src and "_LIB.UTILS.BatchProgress(" in _src)
    # ── v0102 ⑪:交易所 × Yahoo 收盤核對(唯讀;交易所為主)──
    with tempfile.TemporaryDirectory() as td11:
        db11 = Path(td11) / "v.duckdb"
        c11 = duckdb.connect(str(db11))
        c11.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
        c11.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE, adj_close DOUBLE)")
        xs, ys = [], []
        for k, d in enumerate(["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"]):
            xs.append((d, "1111", "TPEX", 50.0))                                   # 1111:第 3 天 Yahoo 陳價(51),其餘一致
            ys.append((d, "1111.TWO", 51.0 if k == 2 else 50.0, 50.0))
            xs.append((d, "3333", "TPEX", 14.6))                                   # 3333:Yahoo 都回乘 1.4484,只有第 2 天漏回調(=14.6)
            ys.append((d, "3333.TWO", 14.6 if k == 1 else 21.14664, 21.0))
        for d, x, y in (("2026-09-01", 110.0, 100.0), ("2026-09-02", 110.0, 100.0), ("2026-09-03", 100.0, 100.0), ("2026-09-04", 100.0, 100.0)):
            xs.append((d, "2222", "TPEX", x))                                      # 2222:9/3 配股除權,Yahoo 把之前的回乘 1/1.1
            ys.append((d, "2222.TWO", y, y))
        xs.append(("2026-09-06", "1111", "TPEX", 50.0))                            # 交易所有、Yahoo 整天沒有
        ys.append(("2026-08-31", "2222.TWO", 100.0, 100.0))                        # Yahoo 有、交易所整天沒有
        c11.executemany("INSERT INTO tw_trading_daily VALUES (?,?,?,?)", xs)
        c11.executemany("INSERT INTO tw_daily_prices VALUES (?,?,?,?)", ys)
        c11.close()
        v11 = verify(db11)
        v11n = verify(Path(td11) / "no.duckdb")
        c11 = duckdb.connect(str(db11))                                             # 上市整個市場只有交易所有(Z62 形狀)
        c11.execute("INSERT INTO tw_trading_daily VALUES ('2026-09-01','2330','TWSE',1000.0)")
        c11.close()
        v11b = verify(db11)
    chk("⑪ v0102 交易所 × Yahoo 收盤核對(唯讀):1111 第 3 天 Yahoo 陳價、3333 第 2 天 Yahoo 漏回調(當天比值=1 但前後都乘 1.4484)→ 單日陳價 2;"
        "2222 配股前兩天比值 0.909 → 配股換階(預期,不是錯);只有交易所 1(09-06)· 只有 Yahoo 1(08-31)· 整天缺各 1;"
        "薄日逐市場列出(TPEX:Yahoo 薄 09-06、交易所薄 08-31);上市只有交易所有=整個市場標一次(不逐日洗版);庫不在=NODATA",
        v11["state"] == "OK" and v11["counts"].get("STALE_1D") == 2 and v11["counts"].get("STOCK_SEG", 0) >= 2
        and {(x["code"], x["date"]) for x in v11["stale_samples"]} == {("1111", "2026-09-03"), ("3333", "2026-09-02")}
        and v11["only_exchange"] == 1 and v11["only_yahoo"] == 1 and v11["days_only_exchange"] == ["2026-09-06"]
        and v11["days_only_yahoo"] == ["2026-08-31"] and v11n["state"] == "NODATA"
        and v11["thin_yahoo"].get("TPEX") == ["2026-09-06"] and v11["thin_exchange"].get("TPEX") == ["2026-08-31"]
        and v11["market_absent_yahoo"] == [] and v11b["market_absent_yahoo"] == ["TWSE"],
        f"({v11['counts']} · 陳價 {[(x['code'], x['date']) for x in v11['stale_samples']]} · 只交易所 {v11['only_exchange']} · 只 Yahoo {v11['only_yahoo']})")
    # ── v0103 ⑫:逐列記來源表 · 舊列不冒名 · verify 報分布(假 curl_json 零網路;暫存庫;global 宣告在本函式開頭)──
    _s12 = (curl_json, _TPEX_URL, PAUSE_S, DB_TW)
    _tw12 = {"stat": "OK", "tables": [{"fields": ["證券代號", "證券名稱", "成交股數", "成交筆數", "成交金額", "開盤價", "最高價", "最低價", "收盤價"],
                                        "data": [["2330", "台積電", "22,817,873", "65,303", "56,893,530,280", "2,475.00", "2,505.00", "2,475.00", "2,500.00"]]}]}
    _tp12 = {"tables": [{"fields": ["代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低", "均價", "成交股數", "成交金額(元)", "成交筆數"],
                         "data": [["5483", "中美晶", "184.50", "-10.50", "195.00", "195.00", "183.00", "186", "41,907,426", "7,858,925,376", "42,433"]]}]}
    _e12, _a12, _b12, _rows12, _v12 = "", [], [], None, {}
    try:
        curl_json = lambda url: _tw12 if "MI_INDEX" in url else _tp12            # noqa: E731
        _TPEX_URL, PAUSE_S = TPEX_VARIANTS[0], 0
        _a12, _b12 = fetch_lane("2026-09-23", "twse_mi"), fetch_lane("2026-09-23", "tpex_quotes")
        with tempfile.TemporaryDirectory() as td12:
            DB_TW = Path(td12) / "t.duckdb"
            _c = duckdb.connect(str(DB_TW))
            _c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, volume DOUBLE, trade_value DOUBLE, "
                       "transactions DOUBLE, close DOUBLE)")           # v0101 形狀的舊列:只有收盤、沒有 src
            _c.execute("INSERT INTO tw_trading_daily VALUES ('2026-09-23','2330','TWSE',1,2,3,2500)")
            _c.close()
            upsert(_a12 + _b12)
            _c = duckdb.connect(str(DB_TW), read_only=True)
            _rows12 = _c.execute("SELECT code, src, open, volume FROM tw_trading_daily ORDER BY code").fetchall()
            _c.close()
            _c = duckdb.connect(str(DB_TW))
            _c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE, adj_close DOUBLE)")
            _c.execute("INSERT INTO tw_daily_prices VALUES ('2026-09-23','5483.TWO',184.5,184.5)")
            _c.close()
            _v12 = verify(DB_TW)
    except Exception as exc:                          # 例外只紅本檢(不讓整支自測當掉,紅燈才指得到是哪一檢)
        _e12 = f"{type(exc).__name__}: {str(exc)[:100]}"
    finally:
        curl_json, _TPEX_URL, PAUSE_S, DB_TW = _s12
    chk("⑫ v0103 逐列記來源表(Z180):MI_INDEX 列=TWSE_RWD_MI_INDEX、dailyQuotes 列=TPEX_RWD_DAILYQUOTES;"
        "舊列(v0101 只有收盤)補開高低但**src 不補**(那列的量不是這次抓的,補上就是冒名)、量不覆蓋;verify 報各市場來源分布(舊列記「未記」)",
        not _e12 and [r.get("src") for r in _a12] == ["TWSE_RWD_MI_INDEX"] and [r.get("src") for r in _b12] == ["TPEX_RWD_DAILYQUOTES"]
        and _rows12 == [("2330", None, 2475.0, 1.0), ("5483", "TPEX_RWD_DAILYQUOTES", 195.0, 41907426.0)]
        and _v12.get("src_mix") == {"TPEX": {"TPEX_RWD_DAILYQUOTES": 1}, "TWSE": {"未記": 1}}
        and _tpex_src(TPEX_VARIANTS[1]) == "TPEX_RWD_OTC" and _tpex_src("x") == "TPEX_RWD_UNKNOWN",
        f"({_e12 or 'ok'} · 列 {_rows12} · 分布 {_v12.get('src_mix')})")
    # ── v0103 ⑬:市值 = 交易所收盤 × 交易所股數(嚴格 / 之後股數近似 / 無股數 三態分欄)· 股數跳動 · 缺表 NODATA · 只讀不建 ──
    _e13, m13n, m13r, m13, _v13, _view_before = "", {}, {}, {"per_market": {}, "jumps": [], "top": []}, None, None
    try:
        with tempfile.TemporaryDirectory() as td13:
            db13 = Path(td13) / "m.duckdb"
            _c = duckdb.connect(str(db13))
            _c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
            _c.executemany("INSERT INTO tw_trading_daily VALUES (?,?,?,?)", [
                ("2026-08-01", "1111", "TPEX", 10.0),     # 第一份股數(08-05)之前 → 嚴格空、近似=之後第一份
                ("2026-08-10", "1111", "TPEX", 10.0),     # 用 08-05 的一億股
                ("2026-09-10", "1111", "TPEX", 5.0),      # 用 09-01 的兩億股(股數翻倍,價也減半 → 市值不變)
                ("2026-09-10", "2222", "TWSE", 100.0),    # 沒有任何股數 → NO_SHARES
                ("bad-date", "1111", "TPEX", 7.0)])       # 日期認不出 → 不進檢視表(TRY_CAST;不炸整張)
            _c.close()
            m13n = mcap(db13)                              # 股數表還不在 → NODATA 講明
            _c = duckdb.connect(str(db13))
            _c.execute("CREATE TABLE tw_shares_issued(asof_date VARCHAR, code VARCHAR, market VARCHAR, shares_issued DOUBLE, src VARCHAR)")
            _c.executemany("INSERT INTO tw_shares_issued VALUES (?,?,?,?,?)", [
                ("2026-08-05", "1111", "TPEX", 1e8, "TPEX_OPENAPI_T187AP03_O"),
                ("2026-09-01", "1111", "TPEX", 2e8, "TPEX_OPENAPI_T187AP03_O")])
            _c.close()
            m13r = mcap(db13, write=False)                 # 只讀:算得出,但不建檢視表
            _c = duckdb.connect(str(db13), read_only=True)
            _view_before = _c.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [MCAP_VIEW]).fetchone()[0]
            _c.close()
            m13 = mcap(db13)
            _c = duckdb.connect(str(db13), read_only=True)
            _v13 = _c.execute(f"SELECT CAST(date AS VARCHAR), code, market_cap, market_cap_later_shares, basis FROM {MCAP_VIEW} "
                              "ORDER BY date, code").fetchall()
            _c.close()
    except Exception as exc:                          # 例外只紅本檢
        _e13 = f"{type(exc).__name__}: {str(exc)[:100]}"
    chk("⑬ v0103 市值=交易所收盤×交易所發行股數(全樹唯一一處):當天或之前最近一份股數 → market_cap(EXCHANGE_CLOSE×EXCHANGE_SHARES);"
        "第一份股數之前**不填 market_cap**,另欄 market_cap_later_shares 用之後第一份近似(LATER_EXCHANGE_SHARES)——股數翻倍時拿之後的股數回推會差一倍,"
        "兩欄分開才看得出;沒有股數=NO_SHARES;日期認不出不炸整張;股數跳動 ≥20% 列出;股數表不在=NODATA 講明要 ENG055 L1;write=False 只讀不建檢視表",
        not _e13 and m13n.get("state") == "NODATA" and "ENG055" in m13n.get("why", "")
        and m13r.get("state") == "OK" and _view_before == 0
        and m13.get("state") == "OK" and m13["per_market"].get("TPEX") == {"rows": 3, "strict": 2, "later": 1, "none": 0, "max_date": "2026-09-10"}
        and m13["per_market"].get("TWSE", {}).get("none") == 1
        and _v13 == [("2026-08-01", "1111", None, 1e9, "EXCHANGE_CLOSE×LATER_EXCHANGE_SHARES"),
                     ("2026-08-10", "1111", 1e9, None, "EXCHANGE_CLOSE×EXCHANGE_SHARES"),
                     ("2026-09-10", "1111", 1e9, None, "EXCHANGE_CLOSE×EXCHANGE_SHARES"),
                     ("2026-09-10", "2222", None, None, "NO_SHARES")]
        and [(j["code"], j["asof_prev"], j["asof"], j["ratio"]) for j in m13["jumps"]] == [("1111", "2026-08-05", "2026-09-01", 2.0)]
        and m13["top"] and m13["top"][0]["code"] == "1111",
        f"({_e13 or 'ok'} · {m13['per_market']} · 跳動 {[(j['code'], j['ratio']) for j in m13['jumps']]} · 只讀建表 {_view_before})")
    # ── v0104 ⑭:跟其他看盤網站核對(假工具零網路;暫存庫)──
    _e14, x14, x14b, x14d, x14n, x14c = "", {}, {}, {}, {}, None
    _calls14 = []

    class FakeYahoo14:
        @staticmethod
        def yahoo_quote_summary(symbols, modules="", pause_s=0.4):
            _calls14.append(list(symbols))
            data = {"2330.TW": (25932370067.0, 64182615539712.0, 2475.0), "5483.TWO": (614171651.0, 115771359232.0, 188.5),
                    "5274.TWO": (41582954.0, 824797822976.0, 19835.0)}
            return {"state": "OK", "rows": [{"symbol": s_, "shares_outstanding": data[s_][0], "market_cap": data[s_][1],
                                            "price": data[s_][2]} for s_ in symbols if s_ in data], "failed": []}

    class DenyYahoo14:
        @staticmethod
        def yahoo_quote_summary(symbols, modules="", pause_s=0.4):
            return {"state": "DENY", "note": "同意閘未開"}

    try:
        with tempfile.TemporaryDirectory() as td14:
            db14 = Path(td14) / "x.duckdb"
            _c = duckdb.connect(str(db14))
            _c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
            _c.executemany("INSERT INTO tw_trading_daily VALUES (?,?,?,?)", [
                ("2026-09-24", "2330", "TWSE", 2475.0), ("2026-09-24", "5483", "TPEX", 188.5), ("2026-09-24", "9999", "TPEX", 10.0),
                ("2026-09-24", "5274", "TPEX", 19835.0)])
            _c.execute("CREATE TABLE tw_shares_issued(asof_date VARCHAR, code VARCHAR, market VARCHAR, shares_issued DOUBLE, src VARCHAR)")
            _c.executemany("INSERT INTO tw_shares_issued VALUES (?,?,?,?,?)", [
                ("2026-08-04", "2330", "TWSE", 25932370067.0, "TREE_SNAPSHOT_T187AP03_L"),
                ("2026-09-24", "5483", "TPEX", 641221651.0, "TPEX_OPENAPI_T187AP03_O"),
                ("2026-09-24", "9999", "TPEX", 1e6, "TPEX_OPENAPI_T187AP03_O"),
                ("2026-08-05", "5274", "TPEX", 37802685.0, "TREE_SNAPSHOT_T187AP03_O"),       # 價格那天用這份(舊)
                ("2026-09-25", "5274", "TPEX", 41582953.0, "TPEX_OPENAPI_T187AP03_O")])       # 交易所之後的出表(配股後)
            _c.close()
            x14 = xcheck(db14, net=FakeYahoo14, today="2026-09-24", gate=True)
            x14b = xcheck(db14, net=FakeYahoo14, today="2026-09-24", gate=True)          # 當天重跑:先查庫,不出網
            x14d = xcheck(db14, net=DenyYahoo14, today="2026-09-25", gate=True)          # 隔天、工具那一層閘關:DENY 照實
            _c = duckdb.connect(str(db14), read_only=True)
            x14c = _c.execute(f"SELECT count(*) FROM {XCHECK_TABLE}").fetchone()[0]
            _c.close()
            db14n = Path(td14) / "n.duckdb"
            _c = duckdb.connect(str(db14n))
            _c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
            _c.execute("INSERT INTO tw_trading_daily VALUES ('2026-08-01','2330','TWSE',2400.0)")   # 股數出表日之前 → 沒有嚴格市值
            _c.execute("CREATE TABLE tw_shares_issued(asof_date VARCHAR, code VARCHAR, market VARCHAR, shares_issued DOUBLE, src VARCHAR)")
            _c.execute("INSERT INTO tw_shares_issued VALUES ('2026-08-04','2330','TWSE',25932370067.0,'X')")
            _c.close()
            x14n = xcheck(db14n, net=FakeYahoo14, today="2026-09-24", gate=True)
    except Exception as exc:
        _e14 = f"{type(exc).__name__}: {str(exc)[:100]}"
    _f14 = {x["code"]: x["flag"] for x in x14.get("rows", [])}
    chk("⑭ v0104 跟其他看盤網站核對(Yahoo quoteSummary,走統包;只報不改):2330 股數一股不差=SAME、5483 Yahoo 少 4.2%(流通在外 vs 已發行)=DIFF、"
        "5274 價格那天用的 08-05 快照舊了、交易所 09-25 出表已跟 Yahoo 一樣=SNAPSHOT_STALE(不算口徑差)、"
        "整批有回但這檔沒資料=NO_YAHOO_ROW 記下來(當天不重問);當天重跑先查庫、一次都不出網;閘關=DENY 照實、什麼都不記(留重試權);沒有嚴格市值=NODATA 講明",
        not _e14 and x14.get("state") == "OK"
        and _f14 == {"2330": "SAME", "5483": "DIFF", "9999": "NO_YAHOO_ROW", "5274": "SNAPSHOT_STALE"}
        and x14.get("failed") == ["9999"] and x14.get("checked") == 3
        and [(x["code"], x["ratio_shares"]) for x in x14.get("diffs", [])] == [("5483", 0.957815)] and len(_calls14) == 1
        and x14b.get("state") == "OK" and x14b.get("skipped_today") == 4 and x14b.get("checked") == 0
        and x14d.get("state") == "DENY" and x14c == 4
        and x14n.get("state") == "NODATA" and "嚴格市值" in x14n.get("why", ""),
        f"({_e14 or 'ok'} · {_f14} · failed {x14.get('failed')} · 重跑略過 {x14b.get('skipped_today')} · 閘關 {x14d.get('state')} · 無嚴格 {x14n.get('state')})")
    # ── v0105 ⑮:每日發行股數史(解析真欄名 · 抽樣 · 先查庫 · 傳輸敗不記 done · 閘關;暫存庫,零網路)──
    _e15, _p15, _r15, _r15b, _rows15, _mc15 = "", None, None, None, None, {}
    try:
        _q15 = {"stat": "OK", "tables": [{"fields": ["證券代號", "證券名稱", "國際證券編碼", "發行股數", "外資及陸資尚可投資股數"],
                                          "data": [["2330", "台積電", "TW0002330008", "25,932,370,067", "1"],
                                                   ["00400A", "ETF", "x", "9", "1"]]}]}
        _o15 = {"tables": [{"fields": ["代號", "名稱", "收盤 ", "漲跌", "發行股數 ", "次日漲停價 "],
                            "data": [["5483", "中美晶", "184.50", "-10.50", "641,221,651", "202.50"]]}]}
        _p15 = (parse_twse_qfiis(_q15, "2026-09-23"), parse_tpex_shares(_o15, "2026-09-23"))
        with tempfile.TemporaryDirectory() as td15:
            db15 = Path(td15) / "s.duckdb"
            _c = duckdb.connect(str(db15))
            _c.execute("CREATE TABLE tw_shares_issued(asof_date VARCHAR, code VARCHAR, market VARCHAR, shares_issued DOUBLE, src VARCHAR)")
            _c.execute("INSERT INTO tw_shares_issued VALUES ('2026-09-01','2330','TWSE',25932370067,'TWSE_RWD_MI_QFIIS')")   # 庫裡已有=不重抓
            _c.execute("INSERT INTO tw_shares_issued VALUES ('2026-09-05','5483','TPEX',641221651,'TPEX_OPENAPI_T187AP03_O')")  # 出表不算每日(抽樣日上)
            _c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
            _c.executemany("INSERT INTO tw_trading_daily VALUES (?,?,?,?)",
                           [("2026-09-02", "2330", "TWSE", 2400.0), ("2026-09-04", "2330", "TWSE", 2450.0)])
            _c.close()
            _days = ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"]
            _asked = []

            def _lane15(d_, ln):
                _asked.append((d_, ln))
                if (d_, ln) == ("2026-09-04", "tpex_shares"):
                    return None                                   # 傳輸敗:不記 done
                mkt = SHARES_LANES[ln][0]
                return [{"asof_date": d_, "code": "2330" if mkt == "TWSE" else "5483", "market": mkt,
                         "shares_issued": 25932370067.0 if mkt == "TWSE" else 641221651.0, "src": SHARES_LANES[ln][1]}]
            import io as _io15
            _buf = _io15.StringIO()
            _r15 = shares(None, 1, 3, lane_fn=_lane15, days_fn=lambda: _days, ckpt=Path(td15) / "ck.json", db=db15,
                          gate=True, stream=_buf, tty=False, progress_path=Path(td15) / "p.json", accel=None)
            _first = list(_asked)
            _asked.clear()
            _r15b = shares(None, 1, 3, lane_fn=_lane15, days_fn=lambda: _days, ckpt=Path(td15) / "ck.json", db=db15,
                           gate=True, stream=_buf, tty=False, progress_path=Path(td15) / "p.json", accel=None)
            _second = list(_asked)
            _gate15 = shares(None, 1, 3, lane_fn=_lane15, days_fn=lambda: _days, db=db15, gate=False, stream=_io15.StringIO())
            _c = duckdb.connect(str(db15), read_only=True)
            _rows15 = _c.execute("SELECT asof_date, code, src FROM tw_shares_issued WHERE src LIKE '%RWD%' ORDER BY asof_date, code").fetchall()
            _c.close()
            _mc15 = mcap(db15, write=False)
    except Exception as exc:
        _e15 = f"{type(exc).__name__}: {str(exc)[:100]}"
        _first = _second = []
        _gate15 = None
    chk("⑮ v0105 每日發行股數史:MI_QFIIS/otc 真欄名解析(四碼、千分位、TPEX 欄名帶尾空白);每 3 日抽樣(09-01 · 04)+ 最後一天一定取(09-05);"
        "先查庫(09-01 TWSE 已有每日股數=不重抓;09-05 的出表快照不算每日,照抓);傳輸敗(09-04 TPEX)不記 done、重跑只問那一個;閘關 rc2;"
        "股數史補上後 09-02/09-04 的上市收盤有嚴格市值",
        not _e15 and _p15 == ([{"asof_date": "2026-09-23", "code": "2330", "market": "TWSE", "shares_issued": 25932370067.0, "src": "TWSE_RWD_MI_QFIIS"}],
                              [{"asof_date": "2026-09-23", "code": "5483", "market": "TPEX", "shares_issued": 641221651.0, "src": "TPEX_RWD_OTC_SHARES"}])
        and _r15 == 0 and sorted(_first) == [("2026-09-01", "tpex_shares"), ("2026-09-04", "tpex_shares"), ("2026-09-04", "twse_shares"),
                                             ("2026-09-05", "tpex_shares"), ("2026-09-05", "twse_shares")]
        and _r15b == 0 and _second == [("2026-09-04", "tpex_shares")] and _gate15 == 2
        and _mc15.get("per_market", {}).get("TWSE", {}).get("strict") == 2,
        f"({_e15 or 'ok'} · 第一輪 {len(_first)} 件 · 重跑 {_second} · 閘關 rc {_gate15} · 市值 {_mc15.get('per_market')})")
    # ── v0106 ⑯:核對的閘與候選(PR #110 Codex 審兩條;假工具記每一次呼叫,零網路;暫存庫;不設任何同意閘環境變數)──
    _e16, _r16, _calls16 = "", {}, []

    class SpyYahoo16:
        @staticmethod
        def yahoo_quote_summary(symbols, modules="", pause_s=0.4):
            _calls16.append(list(symbols))
            data = {"2330.TW": 25932370067.0, "5483.TWO": 641221651.0, "1101.TW": 7536145058.0}
            return {"state": "OK", "rows": [{"symbol": s_, "shares_outstanding": data[s_], "market_cap": None, "price": None}
                                            for s_ in symbols if s_ in data], "failed": []}

    _g16 = globals()
    _orig_gate16 = _g16["gate_open"]
    try:
        with tempfile.TemporaryDirectory() as td16:
            db16 = Path(td16) / "g.duckdb"
            _c = duckdb.connect(str(db16))
            _c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, close DOUBLE)")
            _c.executemany("INSERT INTO tw_trading_daily VALUES (?,?,?,?)", [
                ("2026-09-22", "2330", "TWSE", 2400.0), ("2026-09-23", "2330", "TWSE", 2475.0),   # 上市晚一天進庫:最新 09-23
                ("2026-09-22", "1101", "TWSE", 24.0),                                             # 1101 自己最新只到 09-22(當天沒成交)
                ("2026-09-24", "5483", "TPEX", 188.5), ("2026-09-24", "9999", "TPEX", 10.0)])     # 9999 沒有任何股數=沒有嚴格市值
            _c.execute("CREATE TABLE tw_shares_issued(asof_date VARCHAR, code VARCHAR, market VARCHAR, shares_issued DOUBLE, src VARCHAR)")
            _c.executemany("INSERT INTO tw_shares_issued VALUES (?,?,?,?,?)", [
                ("2026-08-04", "2330", "TWSE", 25932370067.0, "TREE_SNAPSHOT_T187AP03_L"),
                ("2026-08-04", "1101", "TWSE", 7536145058.0, "TREE_SNAPSHOT_T187AP03_L"),
                ("2026-09-24", "5483", "TPEX", 641221651.0, "TPEX_OPENAPI_T187AP03_O")])
            _c.close()
            _r16["deny"] = xcheck(db16, net=SpyYahoo16, today="2026-09-24", gate=False)
            _n_deny = len(_calls16)
            # 閘預設讀 gate_open():換成「啟動器補的預設 VIA_SCRAPE_CONSENT=OFF」那一種環境(只換函式,不動 os.environ)
            _g16["gate_open"] = lambda env=None: _orig_gate16({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "OFF"})
            _r16["off"] = xcheck(db16, net=SpyYahoo16, today="2026-09-24")
            _g16["gate_open"] = _orig_gate16
            _n_off = len(_calls16)
            _c = duckdb.connect(str(db16), read_only=True)
            _t16 = XCHECK_TABLE in {r[0] for r in _c.execute("SHOW TABLES").fetchall()}
            _c.close()
            _r16["lag"] = xcheck(db16, codes=["2330", "1101"], net=SpyYahoo16, today="2026-09-24", gate=True)   # 每檔照核自己的最新日
            _r16["none"] = xcheck(db16, codes=["9999"], net=SpyYahoo16, today="2026-09-24", gate=True)   # 候選空
            _n_none = len(_calls16)
            _r16["part"] = xcheck(db16, codes=["5483", "9999"], net=SpyYahoo16, today="2026-09-24", gate=True)
            _r16["top"] = xcheck(db16, net=SpyYahoo16, today="2026-09-25", gate=True)                     # 前 N 大:兩市場都在
            _c = duckdb.connect(str(db16), read_only=True)
            _tab16 = _c.execute(f"SELECT check_date, string_agg(code, ',' ORDER BY code) FROM {XCHECK_TABLE} "
                                "GROUP BY 1 ORDER BY 1").fetchall()                # v0107:寫表交正典,鍵 check_date+code
            _c.close()
    except Exception as exc:                          # 例外只紅本檢
        _e16 = f"{type(exc).__name__}: {str(exc)[:100]}"
        _n_deny = _n_off = _n_none = -1
        _t16, _tab16 = None, None
    finally:
        _g16["gate_open"] = _orig_gate16
    _lag16 = {x.get("code"): x for x in ((_r16.get("lag") or {}).get("rows") or [])}
    chk("⑯ v0106 核對的閘與候選:本支的同意閘在載入網路工具之前先判——gate=False 零呼叫、DENY、不建核對表;"
        "預設讀 gate_open(),啟動器補的 VIA_SCRAPE_CONSENT=OFF 也算關(網路工具自己的閘二把 OFF 當開);"
        "上市晚一天進庫,--codes 2330,1101 各照核自己的最新日(09-23 · 09-22;v0105 拿全域最新日 09-24 套,候選空卻回 OK);"
        "候選空=NODATA 講明哪幾檔;要核的有一檔沒有嚴格市值=PARTIAL、列在 missing;不給代號時兩個市場各用自己的最新日一起排",
        not _e16 and not gate_open({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "OFF"})
        and _r16["deny"].get("state") == "DENY" and _n_deny == 0 and _r16["off"].get("state") == "DENY" and _n_off == 0
        and _t16 is False
        and _r16["lag"].get("state") == "OK" and _r16["lag"].get("missing") == []
        and {k: (v.get("exchange_date"), v.get("flag")) for k, v in _lag16.items()} == {"2330": ("2026-09-23", "SAME"), "1101": ("2026-09-22", "SAME")}
        and _r16["lag"].get("dates") == {"TWSE": "2026-09-23", "TPEX": "2026-09-24"}
        and _r16["none"].get("state") == "NODATA" and _r16["none"].get("missing") == ["9999"] and "9999" in _r16["none"].get("why", "")
        and _n_none == _n_off + 1
        and _r16["part"].get("state") == "PARTIAL" and _r16["part"].get("missing") == ["9999"] and _r16["part"].get("checked") == 1
        and _r16["top"].get("state") == "OK" and sorted(x["code"] for x in _r16["top"].get("rows", [])) == ["2330", "5483"]
        and _tab16 == [("2026-09-24", "1101,2330,5483"), ("2026-09-25", "2330,5483")],
        f"({_e16 or 'ok'} · " + " · ".join(f"{k} {v.get('state')}" for k, v in _r16.items()) + f" · 呼叫 {len(_calls16)})")
    print(f"  [計] 十六檢 OK {16 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 成交值回補(VDF_ENG057 v0107)· 十六檢自測(零網路;批次迴圈與去重寫入在正典;交易所為主;市值=交易所收盤×交易所股數;跟 Yahoo 核對;每日股數史;核對先過本支同意閘)===")
        return selftest()
    if "--status" in args:
        return status()
    if "verify" in args:                  # v0102:交易所 × Yahoo 收盤核對(唯讀)
        r = verify()
        print(f"[核對] {r['state']} · 容差 {r['tol']:.1%} · {r['counts']} · 只有交易所 {r['only_exchange']} · 只有 Yahoo {r['only_yahoo']}"
              f" · 交易所整天缺 {len(r['days_only_yahoo'])} 天 · Yahoo 整天缺 {len(r['days_only_exchange'])} 天" + (f" · {r.get('why')}" if r.get("why") else ""))
        for x in r["stale_samples"]:
            print(f"  [單日陳價] {x['date']} {x['code']} 交易所 {x['exchange_close']} · Yahoo {x['yahoo_close']} · 比值 {x['ratio']}(前一天 {x['ratio_prev']})")
        if r["days_only_yahoo"]:
            print(f"  [交易所缺整天] {', '.join(r['days_only_yahoo'][:10])}" + (" …" if len(r["days_only_yahoo"]) > 10 else ""))
        if r["days_only_exchange"]:
            print(f"  [Yahoo 缺整天] {', '.join(r['days_only_exchange'][:10])}" + (" …" if len(r["days_only_exchange"]) > 10 else ""))
        for m in r["market_absent_yahoo"]:
            print(f"  [整個市場只有交易所] {m}:Yahoo 價表這個市場一檔都沒有(交易所為主,Yahoo 只補 ADJ CLOSE——要補抓)")
        for m in r["market_absent_exchange"]:
            print(f"  [整個市場只有 Yahoo] {m}:交易所表這個市場一天都沒有(主數據缺——要補抓)")
        for m, ds in r["thin_yahoo"].items():
            print(f"  [Yahoo 薄日] {m} {len(ds)} 天:{', '.join(ds[:8])}" + (" …" if len(ds) > 8 else ""))
        for m, ds in r["thin_exchange"].items():
            print(f"  [交易所薄日] {m} {len(ds)} 天:{', '.join(ds[:8])}" + (" …" if len(ds) > 8 else ""))
        for m, mix in r.get("src_mix", {}).items():
            print(f"  [來源表] {m}:" + " · ".join(f"{k} {v:,}" for k, v in mix.items()))
        return 0 if r["state"] == "OK" else 2
    if "shares" in args:                  # v0105:每日發行股數史(交易所 MI_QFIIS / otc;先查庫、只抓缺的;要同意閘)
        n_ = int(args[args.index("--days") + 1]) if "--days" in args else None
        w_ = int(args[args.index("--workers") + 1]) if "--workers" in args else None
        e_ = int(args[args.index("--every") + 1]) if "--every" in args else None
        return shares(n_, w_, e_)
    if "xcheck" in args:                  # v0104:跟其他看盤網站核對(Yahoo quoteSummary;走統包、閘關=DENY)
        cs = [x for x in args[args.index("--codes") + 1].split(",") if x] if "--codes" in args else None
        tp = int(args[args.index("--top") + 1]) if "--top" in args else 30
        r = xcheck(codes=cs, top=tp)
        dd = " · ".join(f"{m} {d}" for m, d in sorted(r.get("dates", {}).items())) or r["date"]
        print(f"[核對 Yahoo] {r['state']} · 交易所日 {dd} · 核 {r['checked']} 檔 · 今天已核略過 {r['skipped_today']}"
              + (f" · {r.get('why')}" if r.get("why") else "") + (f" · Yahoo 沒回 {r['failed']}" if r["failed"] else ""))
        for x in r["rows"]:
            print(f"  [{x['flag']}] {x['code']} {x['market']} 股數 交易所 {x['exchange_shares']:,.0f}(出表 {x['exchange_asof']})"
                  f" · Yahoo {x['yahoo_shares'] or 0:,.0f} · 比 {x['ratio_shares']} · 價比 {x['ratio_price']} · 市值比 {x['ratio_mcap']}")
        return 0 if r["state"] == "OK" else 2
    if "mcap" in args:                    # v0103:市值 = 交易所收盤 × 交易所發行股數(建/刷新檢視表;不觸網)
        r = mcap()
        print(f"[市值] {r['state']} · 檢視表 {r['view']}" + (f" · {r.get('why')}" if r.get("why") else ""))
        for m, v in r["per_market"].items():
            print(f"  [{m}] {v['rows']:,} 列 · 嚴格 {v['strict']:,}(當天或之前有股數)· 近似 {v['later']:,}(只有之後的股數,另欄)"
                  f" · 無股數 {v['none']:,} · 最新 {v['max_date']}")
        for x in r["top"]:
            print(f"  [最新 {r['latest']}] {x['code']} {x['market']} 收 {x['close']} × 股數 {x['shares_issued']:,.0f}(出表 {x['shares_asof']})"
                  f" = {x['market_cap'] / 1e8:,.1f} 億")
        for j in r["jumps"][:10]:
            print(f"  [股數跳動] {j['code']} {j['market']} {j['asof_prev']} {j['shares_prev']:,.0f} → {j['asof']} {j['shares']:,.0f}(×{j['ratio']})")
        return 0 if r["state"] == "OK" else 2
    if "run" in args:
        n = int(args[args.index("--days") + 1]) if "--days" in args else None
        w = int(args[args.index("--workers") + 1]) if "--workers" in args else None
        return run(n, w)
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
