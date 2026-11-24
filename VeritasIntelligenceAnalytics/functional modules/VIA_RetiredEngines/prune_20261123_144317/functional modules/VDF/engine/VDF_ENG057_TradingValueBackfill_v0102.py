#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG057_TradingValueBackfill v0102 — 逐股成交值歷史回補(批154;via-tval;側線 2026-09-24 第四段:擷取五條紀律)
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
用法:via-tval run [--days N] [--workers N] | verify | --status | --selftest
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
    import duckdb
    import pandas as pd
    df = pd.DataFrame(rows)
    con = duckdb.connect(str(DB_TW))
    con.execute("CREATE TABLE IF NOT EXISTS tw_trading_daily AS SELECT * FROM df LIMIT 0")
    have = {c[0] for c in con.execute("DESCRIBE tw_trading_daily").fetchall()}
    for c in df.columns:
        if c not in have:
            con.execute(f'ALTER TABLE tw_trading_daily ADD COLUMN "{c}" DOUBLE')
    cols = ", ".join(f'"{c}"' for c in df.columns)  # 按欄名插入(QA-20260825A)
    # v0102 補不足、不覆蓋:鍵已在的列,只把庫裡是空的欄補上(交易所某日的數字不會變;已有值一律不動)
    fill = [c for c in df.columns if c not in ("date", "code", "market")]
    if fill:
        sets = ", ".join(f'"{c}" = COALESCE(t."{c}", d."{c}")' for c in fill)
        con.execute(f'UPDATE tw_trading_daily AS t SET {sets} FROM df AS d '
                    f'WHERE t."date"=d."date" AND t."code"=d."code" AND t."market"=d."market"')
    con.execute(f"INSERT INTO tw_trading_daily ({cols}) SELECT {cols} FROM df "
                f"WHERE NOT EXISTS (SELECT 1 FROM tw_trading_daily t "
                f'WHERE t."date"=df."date" AND t."code"=df."code" AND t."market"=df."market")')
    n = con.execute("SELECT COUNT(*) FROM tw_trading_daily").fetchone()[0]
    con.close()
    return n


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
    return (parse_twse_mi if lane == "twse_mi" else parse_tpex)(js, day)


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
           "market_absent_yahoo": [], "market_absent_exchange": [], "thin_yahoo": {}, "thin_exchange": {}}
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
    print(f"  [計] 十一檢 OK {11 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 成交值回補(VDF_ENG057 v0102)· 十一檢自測(零網路;批次迴圈在正典;交易所為主)===")
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
        return 0 if r["state"] == "OK" else 2
    if "run" in args:
        n = int(args[args.index("--days") + 1]) if "--days" in args else None
        w = int(args[args.index("--workers") + 1]) if "--workers" in args else None
        return run(n, w)
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
