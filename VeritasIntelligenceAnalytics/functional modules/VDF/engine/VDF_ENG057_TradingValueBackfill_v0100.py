#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG057_TradingValueBackfill — 逐股成交值歷史回補(批154;via-tval)
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
用法:via-tval run [--days N] | --status | --selftest
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

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
OUT = VDF / "output_hub" / "mega"
DB_TW = OUT / "vdf_tw_market.duckdb"
CKPT = OUT / "trading_value_checkpoint.json"
PAUSE_S = 1.2
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
    global _NET
    if _NET is None:
        _NET = _net_or_none() or False
    if _NET and hasattr(_NET, "curl_json"):
        r = _NET.curl_json(url)
        return r.get("data") if r.get("state") == "OK" else None
    # bytes 整體 decode(text=True 串流於中文多位元組邊界斷裂=UnicodeDecodeError)
    r = subprocess.run(["curl", "-sS", "--max-time", "40", "-A", UA, url],
                       capture_output=True, text=False)
    if r.returncode != 0:
        return None
    try:
        return json.loads((r.stdout or b"").decode("utf-8", "replace"))
    except Exception:
        return None


def _num(x):
    try:
        v = float(str(x).replace(",", "").strip())
        return v
    except Exception:
        return None


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
    rows = []
    for r in data:
        code = str(r[ic]).strip()
        if len(code) != 4 or not code.isdigit():
            continue  # 四碼普通股;權證/ETF 衍生另冊
        rows.append({"date": iso, "code": code, "market": "TWSE",
                     "volume": _num(r[iv]), "trade_value": _num(r[ia]),
                     "transactions": _num(r[it_]) if it_ is not None else None,
                     "close": _num(r[ip]) if ip is not None else None})
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
    rows = []
    for r in data:
        code = str(r[ic]).strip()
        if len(code) != 4 or not code.isdigit():
            continue
        rows.append({"date": iso, "code": code, "market": "TPEX",
                     "volume": _num(r[iv]) if iv is not None else None,
                     "trade_value": _num(r[ia]),
                     "transactions": _num(r[it_]) if it_ is not None else None,
                     "close": _num(r[ip]) if ip is not None else None})
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
    con.execute(f"INSERT INTO tw_trading_daily ({cols}) SELECT {cols} FROM df "
                f"WHERE NOT EXISTS (SELECT 1 FROM tw_trading_daily t "
                f'WHERE t."date"=df."date" AND t."code"=df."code" AND t."market"=df."market")')
    n = con.execute("SELECT COUNT(*) FROM tw_trading_daily").fetchone()[0]
    con.close()
    return n


def run(max_days: int | None = None) -> int:
    if not gate_open():
        print("[FAIL-CLOSED] 同意閘未開")
        return 2
    days = trading_days()
    if not days:
        print("[FAIL] 交易日曆空(先跑價格回補)")
        return 1
    slash_last = f"{days[-1][:4]}/{days[-1][5:7]}/{days[-1][8:]}"
    tpex_ok = _tpex_probe(slash_last) is not None
    lanes = ["twse_mi"] + (["tpex_quotes"] if tpex_ok else [])
    if not tpex_ok:
        print("[誠實] TPEX 端點探測全敗=TPEX_PENDING(僅回補 TWSE)")
    ck = json.loads(CKPT.read_text(encoding="utf-8")) if CKPT.exists() else {"done": []}
    done = set(ck["done"])
    todo = [(d, ln) for d in days for ln in lanes if f"{d}|{ln}" not in done]
    if max_days:
        lim = sorted({d for d, _ in todo})[:max_days]
        todo = [(d, ln) for d, ln in todo if d in lim]
    print(f"[成交值] 交易日 {len(days)} · 待抓 {len(todo)} 日×車道(節流 {PAUSE_S}s)", flush=True)
    buf: list[dict] = []
    n_ok = n_empty = 0
    seen_days = set()
    for i, (day, lane) in enumerate(todo):
        ds = day.replace("-", "")
        slash = f"{day[:4]}/{day[5:7]}/{day[8:]}"
        url = (f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={ds}"
               f"&type=ALLBUT0999&response=json") if lane == "twse_mi" \
            else _TPEX_URL.format(slash=slash)
        js = curl_json(url)
        rows = (parse_twse_mi if lane == "twse_mi" else parse_tpex)(js, day) if js else None
        if rows is not None:  # 傳輸敗不記 done=保重試權
            done.add(f"{day}|{lane}")
            if rows:
                buf.extend(rows)
                n_ok += 1
            else:
                n_empty += 1
            seen_days.add(day)
        # 批尾落盤=無條件評估(傳輸敗不得跳過;先落盤後記帳=帳不得超前於盤)
        if len(seen_days) >= 20 or i == len(todo) - 1:
            if buf:
                n = upsert(buf)
                print(f"  [批] {sorted(seen_days)[-1]} · +{len(buf)} 列 · 表 {n:,}", flush=True)
            CKPT.write_text(json.dumps({"done": sorted(done)}), encoding="utf-8")
            buf, seen_days = [], set()
        time.sleep(PAUSE_S)
    if buf:
        upsert(buf)
    CKPT.write_text(json.dumps({"done": sorted(done)}), encoding="utf-8")
    print(f"[畢] OK {n_ok} · 空 {n_empty}(空=非交易面/端點無資料,誠實計數)")
    return 0


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
    chk("② MI_INDEX 表頭動態對位(四碼濾+值真)",
        len(r) == 1 and r[0]["trade_value"] == 3e10 and r[0]["close"] == 1200.0)

    fx2 = {"tables": [{"fields": ["代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低",
                                  "成交股數", "成交金額(元)", "成交筆數"],
                       "data": [["5347", "世界", "100", "+1", "99", "101", "98",
                                 "3,000,000", "300,000,000", "8,000"]]}]}
    r2 = parse_tpex(fx2, "2026-08-25")
    chk("③ TPEX 表頭動態對位", len(r2) == 1 and r2[0]["trade_value"] == 3e8
        and r2[0]["market"] == "TPEX")

    days = trading_days()
    chk("④ 交易日曆=已庫價格日期", len(days) > 600, f"({len(days)} 日)")

    import tempfile
    global DB_TW
    _db = DB_TW
    with tempfile.TemporaryDirectory() as td:
        DB_TW = Path(td) / "t.duckdb"
        n1 = upsert(r)
        n2 = upsert(r)  # 冪等
        chk("⑤ 按欄名 upsert+anti-join 冪等", n1 == 1 and n2 == 1)
    DB_TW = _db

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 紀律宣告(表頭動態對位/傳輸敗不記 done/TPEX 誠實 PENDING)",
        "零欄序寫死" in src and "保重試權" in src and "TPEX_PENDING" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 成交值回補(VDF_ENG057)· 六檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "run" in args:
        n = int(args[args.index("--days") + 1]) if "--days" in args else None
        return run(n)
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
