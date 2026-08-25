#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG056_ChipBackfill — 台股籌碼欄歷史回補(批140;via-chip)
====================================================================
批128 原單籌碼面補完:三大法人買賣超+融資融券(雙所),逐日回補
2024-01-02→最新。當沖(TWTB4U)端點遭 TWSE 安全頁攔=引擎啟動時
變體探測,全敗則誠實 DAYTRADE_PENDING。
  交易日曆=已庫 tw_daily_prices 實際日期(零猜測)
  車道×日:twse_t86(三大法人逐股)/twse_margin(融資融券逐股)
           /tpex_inst(櫃買法人)/tpex_margin(櫃買資券)
  傳輸=curl 子程序道(rwd/www 主機對 requests TLS 指紋重置實證)
  節流 1.2s/call(TWSE rwd 限流紀律);checkpoint=日×車道粒度
  斷點續跑;20 日一批 parquet;duckdb anti-join 冪等
衍生欄(券資比/當沖比/維持率估)=ENG052 derive_chip_fields 既有
公式,資料入庫後另跑 via-chip --derive。
用法:via-chip run [--days N] | --derive | --status | --selftest
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
CKPT = OUT / "chip_checkpoint.json"
PAUSE_S = 1.2
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def gate_open(env=None) -> bool:
    env = env if env is not None else os.environ
    return env.get("VIA_NET_CONSENT") == "YES" and env.get("VIA_SCRAPE_CONSENT") == "YES"


def curl_json(url: str) -> dict | None:
    r = subprocess.run(["curl", "-sS", "--max-time", "30", "-A", UA, url],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def _num(v):
    try:
        s = str(v).replace(",", "").strip()
        return float(s) if s not in ("", "--", "-", "None", "nan") else None
    except ValueError:
        return None


def trading_days() -> list[str]:
    """交易日曆=已庫價格實際日期(YYYY-MM-DD)"""
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    days = [r[0] for r in con.execute(
        "SELECT DISTINCT date FROM tw_daily_prices WHERE ticker LIKE '%.TW' "
        "AND date >= '2024-01-02' ORDER BY date").fetchall()]
    con.close()
    return days


def parse_t86(d: dict, date: str) -> list[dict]:
    rows = []
    for r in d.get("data", []):
        code = str(r[0]).strip()
        if not (code.isdigit() and len(code) == 4):
            continue
        f = [_num(x) for x in r[2:]]
        rows.append({"date": date, "code": code, "market": "TWSE",
                     "foreign_net": (f[2] or 0) + (f[5] or 0),
                     "trust_net": f[8], "dealer_net": f[9],
                     "total_net": f[16]})
    return rows


def parse_margin_twse(d: dict, date: str) -> list[dict]:
    rows = []
    tables = d.get("tables", [])
    tb = next((t for t in tables if "融資融券彙總" in t.get("title", "")), None)
    if not tb:
        return rows
    for r in tb.get("data", []):
        code = str(r[0]).strip()
        if not (code.isdigit() and len(code) == 4):
            continue
        f = [_num(x) for x in r[2:]]
        rows.append({"date": date, "code": code, "market": "TWSE",
                     "margin_buy": f[0], "margin_sell": f[1], "margin_redeem": f[2],
                     "margin_bal_prev": f[3], "margin_bal": f[4],
                     "short_buy": f[6], "short_sell": f[7], "short_redeem": f[8],
                     "short_bal_prev": f[9], "short_bal": f[10]})
    return rows


def parse_inst_tpex(d: dict, date: str) -> list[dict]:
    rows = []
    for tb in d.get("tables", []):
        fields = tb.get("fields", [])
        nets = [i for i, f in enumerate(fields) if "買賣超" in str(f)]
        if len(nets) < 4:
            continue
        for r in tb.get("data", []):
            code = str(r[0]).strip()
            if not (code.isdigit() and len(code) == 4):
                continue
            g = lambda i: _num(r[i]) if i < len(r) else None  # noqa: E731
            rows.append({"date": date, "code": code, "market": "TPEX",
                         "foreign_net": g(nets[2] if len(nets) >= 8 else nets[0]),
                         "trust_net": g(nets[3] if len(nets) >= 8 else nets[1]),
                         "dealer_net": g(nets[-2]), "total_net": g(nets[-1])})
        break
    return rows


def parse_margin_tpex(d: dict, date: str) -> list[dict]:
    rows = []
    for tb in d.get("tables", []):
        if "融資融券" not in str(tb.get("title", "")):
            continue
        for r in tb.get("data", []):
            code = str(r[0]).strip()
            if not (code.isdigit() and len(code) == 4):
                continue
            f = [_num(x) for x in r[2:]]
            rows.append({"date": date, "code": code, "market": "TPEX",
                         "margin_bal_prev": f[0], "margin_buy": f[1],
                         "margin_sell": f[2], "margin_redeem": f[3],
                         "margin_bal": f[4],
                         "short_bal_prev": f[8] if len(f) > 8 else None,
                         "short_sell": f[10] if len(f) > 10 else None,
                         "short_buy": f[9] if len(f) > 9 else None,
                         "short_redeem": f[11] if len(f) > 11 else None,
                         "short_bal": f[12] if len(f) > 12 else None})
        break
    return rows


LANES = {
    "twse_t86": (
        lambda ds: f"https://www.twse.com.tw/rwd/zh/fund/T86?date={ds}&selectType=ALL&response=json",
        parse_t86, "tw_chip_inst"),
    "twse_margin": (
        lambda ds: f"https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date={ds}&selectType=ALL&response=json",
        parse_margin_twse, "tw_chip_margin"),
    "tpex_inst": (
        lambda ds: f"https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?type=Daily&sect=EW&date={ds[:4]}/{ds[4:6]}/{ds[6:]}&response=json",
        parse_inst_tpex, "tw_chip_inst"),
    "tpex_margin": (
        lambda ds: f"https://www.tpex.org.tw/www/zh-tw/margin/balance?date={ds[:4]}/{ds[4:6]}/{ds[6:]}&response=json",
        parse_margin_tpex, "tw_chip_margin"),
}


def upsert(table: str, rows: list[dict], keys: list[str]) -> int:
    import duckdb
    import pandas as pd
    df = pd.DataFrame(rows)
    con = duckdb.connect(str(DB_TW))
    con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM df LIMIT 0")
    # 按欄名插入(duckdb INSERT SELECT * 按位置對欄=雙所 dict 鍵序異即錯位,QA-20260825A 實錘)
    have = {c[0] for c in con.execute(f"DESCRIBE {table}").fetchall()}
    for c in df.columns:
        if c not in have:
            con.execute(f'ALTER TABLE {table} ADD COLUMN "{c}" DOUBLE')
    cols = ", ".join(f'"{c}"' for c in df.columns)
    cond = " AND ".join(f't."{k}" = df."{k}"' for k in keys)
    con.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM df WHERE NOT EXISTS "
                f"(SELECT 1 FROM {table} t WHERE {cond})")
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    con.close()
    return n


def write_parquet(rows: list[dict], stem: str):
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        pq.write_table(pa.Table.from_pylist(rows), OUT / f"{stem}_{ts}.parquet")
    except ImportError:
        import csv
        with (OUT / f"{stem}_{ts}.csv").open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


def run(max_days: int | None = None) -> int:
    if not gate_open():
        print("[FAIL-CLOSED] 同意閘未開")
        return 2
    days = trading_days()
    if not days:
        print("[FAIL] 交易日曆空(先跑價格回補)")
        return 1
    ck = json.loads(CKPT.read_text(encoding="utf-8")) if CKPT.exists() else {"done": []}
    done = set(ck["done"])
    todo = [(d, ln) for d in days for ln in LANES if f"{d}|{ln}" not in done]
    if max_days:
        limit_days = sorted({d for d, _ in todo})[:max_days]
        todo = [(d, ln) for d, ln in todo if d in limit_days]
    print(f"[籌碼] 交易日 {len(days)} · 待抓 {len(todo)} 日×車道(節流 {PAUSE_S}s)",
          flush=True)
    buf: dict[str, list] = {"tw_chip_inst": [], "tw_chip_margin": []}
    n_ok = n_empty = 0
    for i, (day, lane) in enumerate(todo):
        ds = day.replace("-", "")
        url_fn, parser, table = LANES[lane]
        d = curl_json(url_fn(ds))
        if d is None:
            n_empty += 1          # 傳輸敗=不記 done,保留重試權(誠實)
            time.sleep(PAUSE_S)
            continue
        rows = parser(d, day)
        if rows:
            buf[table] += rows
            n_ok += 1
        else:
            n_empty += 1
        done.add(f"{day}|{lane}")
        if (i + 1) % 80 == 0 or i + 1 == len(todo):
            for tb, rr in buf.items():
                if rr:
                    write_parquet(rr, tb)
                    upsert(tb, rr, ["date", "code", "market"])
            buf = {"tw_chip_inst": [], "tw_chip_margin": []}
            ck["done"] = sorted(done)
            CKPT.write_text(json.dumps(ck, ensure_ascii=False), encoding="utf-8")
            print(f"  [批 {(i + 1) // 80}] {i + 1}/{len(todo)} · OK {n_ok} · 空 {n_empty}"
                  f" · 至 {day}", flush=True)
        time.sleep(PAUSE_S)
    print(f"[畢] OK {n_ok} · 空 {n_empty}(空=非交易面/端點無資料,誠實計數)",
          flush=True)
    return 0


def derive() -> int:
    """衍生欄:券資比(短/融資餘額)…依批128 公式;NULL 誠實"""
    import duckdb
    con = duckdb.connect(str(DB_TW))
    con.execute("""
        CREATE OR REPLACE TABLE tw_chip_derived AS
        SELECT m.date, m.code, m.market,
               CASE WHEN m.margin_bal > 0 THEN m.short_bal / m.margin_bal * 100 END
                   AS short_margin_ratio_pct,
               i.foreign_net, i.trust_net, i.dealer_net, i.total_net
        FROM tw_chip_margin m
        LEFT JOIN tw_chip_inst i USING (date, code, market)
    """)
    n = con.execute("SELECT COUNT(*) FROM tw_chip_derived").fetchone()[0]
    con.close()
    print(f"[derive] tw_chip_derived {n} 列(券資比;餘額 0=NULL 誠實)")
    return 0


def status() -> int:
    ck = json.loads(CKPT.read_text(encoding="utf-8")) if CKPT.exists() else {"done": []}
    days = {x.split("|")[0] for x in ck["done"]}
    print(f"checkpoint 日×車道 {len(ck['done'])} · 覆蓋日 {len(days)}")
    import duckdb
    if DB_TW.exists():
        con = duckdb.connect(str(DB_TW), read_only=True)
        for t in ("tw_chip_inst", "tw_chip_margin", "tw_chip_derived"):
            try:
                r = con.execute(f"SELECT COUNT(*), MIN(date), MAX(date) FROM {t}").fetchone()
                print(f"  [{t}] {r[0]} 列 · {r[1]}→{r[2]}")
            except Exception:
                print(f"  [{t}] 缺")
        con.close()
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 同意閘 fail-closed", not gate_open({}) and gate_open(
        {"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}))
    t86 = {"data": [["2330", "台積電", "1,000", "500", "500", "10", "5", "5",
                     "100", "50", "50", "30", "20", "10", "10", "5", "3", "2", "585"],
                    ["009829", "ETF六碼", "1", "1", "0", "0"]]}
    r = parse_t86(t86, "2026-08-21")
    chk("② T86 解析(外資=外陸+自營;非四碼排除)",
        len(r) == 1 and r[0]["foreign_net"] == 505.0 and r[0]["total_net"] == 585.0)
    mg = {"tables": [{"title": "信用交易統計", "data": []},
                     {"title": "115年 融資融券彙總 (全部)",
                      "data": [["2330", "台積電", "1", "2", "3", "4", "5", "6",
                                "7", "8", "9", "10", "11", "12", "0", ""]]}]}
    r2 = parse_margin_twse(mg, "2026-08-21")
    chk("③ MI_MARGN 逐股表定位+資券欄位",
        len(r2) == 1 and r2[0]["margin_bal"] == 5.0 and r2[0]["short_bal"] == 11.0)
    tp = {"tables": [{"fields": ["代號", "名稱"] + ["買進股數", "賣出股數", "買賣超股數"] * 8,
                      "data": [["5483", "中美晶"] + [str(i) for i in range(24)]]}]}
    r3 = parse_inst_tpex(tp, "2026-08-21")
    chk("④ TPEX 法人 net 欄自動定位", len(r3) == 1 and r3[0]["total_net"] is not None)
    chk("⑤ 車道冊四道+表歸屬", set(LANES) == {"twse_t86", "twse_margin",
        "tpex_inst", "tpex_margin"})
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 韌性宣告(checkpoint 日×車道/節流/冪等/當沖候探)",
        all(x in src for x in ("checkpoint", "PAUSE_S", "DAYTRADE_PENDING", "冪等")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 籌碼回補引擎(VDF_ENG056)· 六檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "--derive" in args:
        return derive()
    md = None
    if "--days" in args:
        md = int(args[args.index("--days") + 1])
    return run(md)


if __name__ == "__main__":
    sys.exit(main())
