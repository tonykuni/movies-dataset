#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG056_ChipBackfill — 台股籌碼欄歷史回補(批140;via-chip)
v0102→v0103(側線 2026-09-24 第四段;主線批號由併線的手指定 L25;操作員令「擷取前先查庫缺啥 · 定範圍 · BATCH FETCHING 固定時間先暫存
  避免重複擷取 · 整合庫去重補不足 · 加速器跟網路工具覆蓋所有指令細節動作」):
  ① 本支 v0102 的批次迴圈(checkpoint 自庫重建之後那一段:小塊 accel_map 平行 · 自癒減工 · 每 80 件落檔 · Ctrl+C 安全)收成正典
     SUP_MDL753 v0108 `batch_fetch`(唯一實作;成交值 ENG057 與之後的全市場逐日道都用同一支),本支改呼叫它;`Progress` / `_fmt_eta`
     綁正典 `BatchProgress` / `fmt_eta`(逐字就是本支 v0102 的那兩段)。**順手修掉原型一個洞**:v0102 自癒減工後 range 步長還是舊塊長、
     切片卻用新塊長 → 每塊中間幾件被跳過(沒記 done,下次會補;但這一跑總結對不上)——正典用 while 逐塊推進,自測 ㊵ 驗。
  ② curl_json 拿掉「統包缺席=本地 curl 後備」:那條後備不經同意閘、也不經網路工具的法遵層。v0103:工具缺或缺 curl_json 車道
     → run() 開跑前誠實停(rc1,講明),不自己打 curl。自測 +⑩;⑧⑨ 一字未改照過(行為等價的證據)。十檢。
v0100→v0101(批142):curl 走統包 SUP_MDL740 curl_json 車道(紅線收口;缺席後備)。
v0101→v0102(批395 操作員令「剛才有卡斷 修正;20 個 PS 加速器;動態進度條及數字」;工作站實錄:via-chip run 印
  「待抓 1800 日×車道」後 96 秒零輸出=操作員 Ctrl+C → KeyboardInterrupt 裸 traceback,緩衝列與 checkpoint 全失):
  ① checkpoint 自庫重建:啟動時自 tw_chip_inst/tw_chip_margin 既有 (date, market) 標記該日該車道已完成(ENG079 整併/他機回補
     來的日子不再重抓;實錄 1800 → 只剩真缺的日×車道)並回寫 checkpoint
  ② 平行:SuperAccel accel_map(ACCEL-BRIDGE;加速器 #12 平行/#19 多引擎,同 ENG054 律)--workers N(預設 4)每工保留節流
     PAUSE_S;小塊(工×2)提交=Ctrl+C 最多等一塊;一塊傳輸敗過半=自癒減半工數(TWSE 限流誠實)
  ③ 動態進度條+數字(加速器 #16 Write-VIAProgress 同款):單列 \r 重繪 [####----] 百分比 完成/總數 OK 空 敗 至日 速率 ETA;
     非 TTY(log)=每 40 件換行;PROGRESS.json(VIA_Reports/vdf/chips)供主控台/接棒台讀
  ④ 中斷安全:Ctrl+C → 先落緩衝列(parquet+upsert)再存 checkpoint,印「[中斷] 已存;重跑續補」rc 130 零裸 traceback
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
用法:via-chip run [--days N] [--workers N] | --derive | --status | --selftest
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
CKPT = OUT / "chip_checkpoint.json"
PAUSE_S = 1.2
REPORTS = VDF.parent.parent / "VIA_Reports" / "vdf" / "chips"
PROGRESS = REPORTS / "PROGRESS.json"
WORKERS_DEFAULT = 4      # 批395:SuperAccel accel_map 平行工(每工保留 PAUSE_S 節流)
FLUSH_N = 80             # 每 80 件落 parquet+upsert+checkpoint(v0101 同律)
LANE_TABLE_MARKET = {"twse_t86": ("tw_chip_inst", "TWSE"), "tpex_inst": ("tw_chip_inst", "TPEX"),
                     "twse_margin": ("tw_chip_margin", "TWSE"), "tpex_margin": ("tw_chip_margin", "TPEX")}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _connect(db: Path, read_only: bool, retries: int = 6, wait: float = 3.0, sleep_fn=None):
    """讓庫律(批399 自審;ENG081/ENG064/ENG079 同律):DuckDB 單寫者鎖=短等重試;逾額誠實 RuntimeError(主程式 [FAIL] 庫忙 rc3,零裸 traceback)"""
    import duckdb
    last = ""
    for i in range(retries):
        try:
            return duckdb.connect(str(db), read_only=read_only)
        except duckdb.IOException as exc:
            last = str(exc)
            low = last.lower()
            if not any(k in low for k in ("lock", "already open", "being used", "另一個程序", "cannot open file")):
                raise
            print(f"  [庫忙] {i + 1}/{retries}:{last.splitlines()[0][:90]} → 等 {wait}s", flush=True)
            (sleep_fn or time.sleep)(wait)
    raise RuntimeError(f"庫忙逾 {retries}×{wait}s(日更鏈/回補/via-price 持單寫者鎖;等其跑完再 via-chip;via-bg 看背景引擎進程):{last.splitlines()[0][:120]}")


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
    spec = _il.spec_from_file_location("via_net_dyn", hits[-1])
    mod = _il.module_from_spec(spec)
    sys.modules["via_net_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod
# ===== [VIA:NET-BRIDGE:END] =====

_NET = None


def curl_json(url: str) -> dict | None:
    """v0101(批142):統包 curl_json 車道(凡外呼走網路工具紅線收口)。
    v0103:統包缺席=None,**不再自己打 curl**(那條後備不經同意閘也不經工具的法遵層);run() 開跑前先驗工具在位,缺=誠實停。"""
    global _NET
    if _NET is None:
        _NET = _net_or_none() or False
    if _NET and hasattr(_NET, "curl_json"):
        r = _NET.curl_json(url)
        return r.get("data") if r.get("state") == "OK" else None
    return None


def _net_ready() -> bool:
    """v0103:統包網路工具在位且有 curl_json 車道(真擷取的前提;缺=誠實停,不後備)。"""
    n = _net_or_none()
    return bool(n) and hasattr(n, "curl_json")


#: 批597 三庫整併:_num → 正典綁定(哨兵清單含 'nan';不綁 drop 的話 float('nan') 會回 nan 不是 None(量到 2 處差異))。
#  綁定不是 def——再包一層 def 的話能力庫裡那一族還在,家族數不會掉(LL143)。
_num = _lb_partial(_LIB.num, drop=("", "--", "-", "None", "nan"))


def trading_days() -> list[str]:
    """交易日曆=已庫價格實際日期(YYYY-MM-DD)"""
    con = _connect(DB_TW, read_only=True)
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
    con = _connect(DB_TW, read_only=False)
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


def db_done_lanes(db: Path | None = None) -> set:
    """checkpoint 自庫重建(批395):庫內已有 (date, market) 的籌碼表 → 該日該車道視為完成(零重抓;ENG079 整併來的日子亦算)"""
    import duckdb
    db = db or DB_TW
    out: set = set()
    if not db.exists():
        return out
    con = _connect(db, read_only=True)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        for lane, (table, market) in LANE_TABLE_MARKET.items():
            if table not in have:
                continue
            cols = {r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()}
            if "market" in cols:
                rows = con.execute(f"SELECT DISTINCT CAST(date AS VARCHAR) FROM {table} WHERE market = ?", [market]).fetchall()
            else:
                rows = con.execute(f"SELECT DISTINCT CAST(date AS VARCHAR) FROM {table}").fetchall()
            for (d,) in rows:
                out.add(f"{str(d)[:10]}|{lane}")
    finally:
        con.close()
    return out


#: v0103:進度條與 ETA 綁正典(逐字就是本支 v0102 的 Progress / _fmt_eta;綁定不是 def——LL143)
_fmt_eta = _LIB.UTILS.fmt_eta
Progress = _lb_partial(_LIB.UTILS.BatchProgress, label="籌碼", schema="VIA.ChipProgress.v1")


def fetch_lane(day: str, lane: str):
    """一日一車道:curl_json → 解析;傳輸敗=None(不記 done,保留重試權);每工保留節流"""
    ds = day.replace("-", "")
    url_fn, parser, table = LANES[lane]
    d = curl_json(url_fn(ds))
    time.sleep(PAUSE_S)
    if d is None:
        return None
    return parser(d, day)


def persist(table: str, rows: list) -> None:
    write_parquet(rows, table)
    upsert(table, rows, ["date", "code", "market"])


def run(max_days: int | None = None, workers: int | None = None, *, lane_fn=None, persist_fn=None, days_fn=None,
        ckpt: Path | None = None, db: Path | None = None, gate: bool | None = None, stream=None, tty: bool | None = None,
        progress_path: Path | None = None, accel=None) -> int:
    """批395:checkpoint 自庫重建 → 小塊 accel_map 平行(每工節流)→ 進度條 → 每 80 件落檔+checkpoint → Ctrl+C 安全"""
    out = stream or sys.stdout

    def say(msg: str) -> None:
        out.write(msg + "\n")
        out.flush()
    if not (gate if gate is not None else gate_open()):
        say("[FAIL-CLOSED] 同意閘未開")
        return 2
    if lane_fn is None and not _net_ready():           # v0103:真擷取才驗;缺工具=誠實停,不自己打 curl
        say("[FAIL] 統包網路工具缺席或缺 curl_json 車道(SUP_MDL740;不退回自己打 curl——那條路不經同意閘與法遵層)")
        return 1
    lane_fn = lane_fn or fetch_lane
    persist_fn = persist_fn or persist
    ckpt = ckpt or CKPT
    db = db or DB_TW
    workers = max(1, int(workers or WORKERS_DEFAULT))
    accel = VIA_ACCEL if accel is None else accel
    days = (days_fn or trading_days)()
    if not days:
        say("[FAIL] 交易日曆空(先跑價格回補)")
        return 1
    ck = json.loads(ckpt.read_text(encoding="utf-8")) if ckpt.exists() else {"done": []}
    done = set(ck["done"])
    from_db = db_done_lanes(db) - done
    done |= from_db
    todo = [(d, ln) for d in days for ln in LANES if f"{d}|{ln}" not in done]
    if max_days:
        limit_days = sorted({d for d, _ in todo})[:max_days]
        todo = [(d, ln) for d, ln in todo if d in limit_days]
    say(f"[籌碼] 交易日 {len(days)} · checkpoint 自庫重建 +{len(from_db)} 日×車道(庫內已有=不重抓)· 待抓 {len(todo)} 日×車道"
        f" · 工 {workers}(每工節流 {PAUSE_S}s;SuperAccel {'在' if accel is not None and hasattr(accel, 'accel_map') else '缺=循序'})")
    prog = Progress(len(todo), stream=stream, tty=tty, progress_path=PROGRESS if progress_path is None else progress_path)

    def _say_prog(msg: str) -> None:
        prog.stream.write(("\n" if prog.tty and not msg.startswith("\n") else "") + msg + "\n")
        prog.stream.flush()

    # v0103:批次迴圈交正典 batch_fetch(唯一實作;本支 v0102 的迴圈是它的原型)——小塊平行 · 自癒減工 · 每 FLUSH_N 件落檔 · Ctrl+C 安全
    r = _LIB.UTILS.batch_fetch(todo, lambda it: lane_fn(it[0], it[1]), persist_fn, done=done, ckpt=ckpt, workers=workers,
                               accel=accel, flush_n=FLUSH_N, prog=prog, target_of=lambda it: LANES[it[1]][2], say=_say_prog)
    if r["rc"] == 130:
        say(f"[中斷] Ctrl+C:已落緩衝列 {r['flushed']} 列 + checkpoint {len(done)} 日×車道(進度 {prog.done}/{prog.total});重跑 via-chip run 續補(零重抓)")
        return 130
    say(f"[畢] OK {prog.ok} · 空 {prog.empty} · 敗 {prog.fail}(空=非交易面/端點無資料;敗=傳輸敗保留重試權;誠實計數)· 落庫 {r['flushed']} 列 · checkpoint {len(done)} 日×車道")
    return 0


def derive() -> int:
    """衍生欄:券資比(短/融資餘額)…依批128 公式;NULL 誠實"""
    con = _connect(DB_TW, read_only=False)
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
    dbd = db_done_lanes()
    print(f"checkpoint 日×車道 {len(ck['done'])} · 覆蓋日 {len(days)} · 庫內已有 {len(dbd)} 日×車道(自庫重建;批395)")
    if PROGRESS.exists():
        try:
            pj = json.loads(PROGRESS.read_text(encoding="utf-8"))
            print(f"  [上次進度] {pj.get('state')} · {pj.get('line')}")
        except (OSError, ValueError):
            pass
    import duckdb
    if DB_TW.exists():
        con = _connect(DB_TW, read_only=True)
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
    # ⑦⑧⑨ 批395(零網路;臨時庫/臨時 checkpoint;假車道)
    import io
    import tempfile
    import duckdb
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db = root / "t.duckdb"
        c = duckdb.connect(str(db))
        c.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR, foreign_net DOUBLE)")
        c.execute("INSERT INTO tw_chip_inst VALUES ('2026-09-01','2330','TWSE',1),('2026-09-01','6488','TPEX',1)")
        c.execute("CREATE TABLE tw_chip_margin(date DATE, code VARCHAR, market VARCHAR, margin_bal DOUBLE)")
        c.execute("INSERT INTO tw_chip_margin VALUES ('2026-09-01','2330','TWSE',1)")
        c.close()
        dbd = db_done_lanes(db)
        real_connect = duckdb.connect

        def locked_forever(path, read_only=False):
            raise duckdb.IOException("IO Error: Could not set lock on file")
        duckdb.connect = locked_forever
        try:
            try:
                _connect(db, read_only=True, retries=2, wait=0.0, sleep_fn=lambda s: None)
                lock_ok = False
            except RuntimeError as exc:
                lock_ok = "庫忙逾" in str(exc) and "via-bg" in str(exc)
        finally:
            duckdb.connect = real_connect
        chk("⑦ checkpoint 自庫重建(庫內 (date,market) → 該日該車道已完成;margin TPEX 缺=待抓;庫缺=空集合)+ 讓庫律(永鎖=誠實 RuntimeError 指路 via-bg;批399)",
            dbd == {"2026-09-01|twse_t86", "2026-09-01|tpex_inst", "2026-09-01|twse_margin"} and db_done_lanes(root / "no.duckdb") == set() and lock_ok, f"({sorted(dbd)};lock {lock_ok})")
        out = io.StringIO()
        p = Progress(4, stream=out, tty=False, progress_path=root / "PROGRESS.json")
        p.tick("ok", "2026-09-01"); p.tick("empty", "2026-09-01"); p.tick("fail", "2026-09-02"); p.tick("ok", "2026-09-02")
        p.finish("OK")
        pj = json.loads((root / "PROGRESS.json").read_text(encoding="utf-8"))
        t = io.StringIO()
        p2 = Progress(2, stream=t, tty=True, every=0.0)
        p2.tick("ok", "2026-09-01")
        chk("⑧ 動態進度條+數字(百分比/完成/總數/OK/空/敗/至日/速率/ETA;非 TTY 尾件換行;TTY \\r 重繪;PROGRESS.json 落檔;ETA 格式)",
            "100.0% 4/4" in out.getvalue() and "OK 2" in out.getvalue() and "空 1" in out.getvalue() and "敗 1" in out.getvalue() and "至 2026-09-02" in out.getvalue()
            and "[####################]" in out.getvalue() and pj["state"] == "OK" and pj["done"] == 4 and pj["pct"] == 100.0
            and t.getvalue().startswith("\r[籌碼] [##########----------]  50.0% 1/2") and _fmt_eta(3725) == "1h02m" and _fmt_eta(62) == "1m02s", f"({out.getvalue().strip()[:90]})")
        calls = {"n": 0}
        saved: dict = {}

        def lane_ok(day, lane):
            calls["n"] += 1
            if calls["n"] == 6:
                raise KeyboardInterrupt
            table = LANES[lane][2]
            return [{"date": day, "code": "2330", "market": "TWSE", "x": 1.0}] if table == "tw_chip_inst" else []

        def lane_ok2(day, lane):
            return [{"date": day, "code": "2330", "market": "TWSE", "x": 1.0}]

        def keep(table, rows):
            saved.setdefault(table, []).extend(rows)
        ckp = root / "ck.json"
        so = io.StringIO()
        rc1 = run(None, 1, lane_fn=lane_ok, persist_fn=keep, days_fn=lambda: ["2026-09-01", "2026-09-02", "2026-09-03"], ckpt=ckp, db=db, gate=True, stream=so, tty=False, progress_path=root / "P.json")
        ck1 = json.loads(ckp.read_text(encoding="utf-8"))["done"]
        pj1 = json.loads((root / "P.json").read_text(encoding="utf-8"))
        rc2 = run(None, 2, lane_fn=lane_ok2, persist_fn=keep, days_fn=lambda: ["2026-09-01", "2026-09-02", "2026-09-03"], ckpt=ckp, db=db, gate=True, stream=so, tty=False, progress_path=root / "P.json")
        ck2 = json.loads(ckp.read_text(encoding="utf-8"))["done"]
        rc3 = run(None, 1, lane_fn=lane_ok2, persist_fn=keep, days_fn=lambda: ["2026-09-01", "2026-09-02", "2026-09-03"], ckpt=ckp, db=db, gate=True, stream=so, tty=False, progress_path=root / "P.json")
        chk("⑨ 中斷安全+續補(3 日×4 車道=12,庫內已有 3 → 待抓 9;第 6 次 Ctrl+C → 已落緩衝列+checkpoint(在飛塊不記 done)rc130 零 traceback;重跑 2 工 accel_map 只補剩餘 → rc0 12/12;再跑 0 待抓冪等;同意閘關=rc2)",
            rc1 == 130 and pj1["state"] == "INTERRUPTED" and len(ck1) == 3 + 4 and len(saved.get("tw_chip_inst", [])) >= 1
            and rc2 == 0 and len(ck2) == 12 and rc3 == 0 and "待抓 0 " in so.getvalue() and run(None, 1, gate=False, days_fn=lambda: ["x"], ckpt=ckp, db=db, stream=so, tty=False) == 2,
            f"(rc {rc1}/{rc2}/{rc3};ck {len(ck1)}/{len(ck2)};saved {sum(len(v) for v in saved.values())})")
    # ── v0103 ⑩:統包網路工具缺席=誠實停,不自己打 curl(真擷取路);curl_json 原始碼零 subprocess;批次迴圈在正典 ──
    import inspect as _insp10
    import io as _io10
    import tempfile as _tf10
    global _NET
    _g10 = globals()
    _saved10 = (_g10["_net_or_none"], _NET)
    try:
        _g10["_net_or_none"] = lambda: None
        _NET = None
        _cj = curl_json("https://www.twse.com.tw/rwd/zh/fund/T86?date=20260901&selectType=ALL&response=json")
        with _tf10.TemporaryDirectory() as _td10:
            _o10 = _io10.StringIO()
            _rc10 = run(None, 1, gate=True, days_fn=lambda: ["2026-09-01"], ckpt=Path(_td10) / "ck.json", db=Path(_td10) / "no.duckdb",
                        stream=_o10, tty=False, progress_path=Path(_td10) / "P.json")
            _rc10g = run(None, 1, gate=False, days_fn=lambda: ["2026-09-01"], ckpt=Path(_td10) / "ck.json", db=Path(_td10) / "no.duckdb",
                         stream=_io10.StringIO(), tty=False)
    finally:
        _g10["_net_or_none"], _NET = _saved10
    _src10 = _insp10.getsource(curl_json) + _insp10.getsource(run)
    chk("⑩ v0103 統包網路工具缺席=真擷取誠實停(rc1 講明,不自己打 curl);curl_json 缺工具回 None;同意閘關仍先回 rc2;"
        "curl_json/run 原始碼零 subprocess;批次迴圈交正典 batch_fetch、進度條綁正典 BatchProgress",
        _cj is None and _rc10 == 1 and "統包網路工具缺席" in _o10.getvalue() and _rc10g == 2
        and "subprocess" not in _src10 and "_LIB.UTILS.batch_fetch(" in _src10
        and getattr(Progress, "func", None) is _LIB.UTILS.BatchProgress and _fmt_eta is _LIB.UTILS.fmt_eta,
        f"(curl_json {_cj} · rc {_rc10}/{_rc10g})")
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 籌碼回補引擎(VDF_ENG056 v0103)· 十檢自測(零網路;批次迴圈在正典)===")
        return selftest()
    md = None
    if "--days" in args:
        md = int(args[args.index("--days") + 1])
    w = None
    if "--workers" in args:
        w = int(args[args.index("--workers") + 1])
    try:
        if "--status" in args:
            return status()
        if "--derive" in args:
            return derive()
        return run(md, w)
    except RuntimeError as exc:   # 批399 自審:讓庫律 → 誠實 [FAIL] rc3 零裸 traceback
        print(f"[FAIL] {exc}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
