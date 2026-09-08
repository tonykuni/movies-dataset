#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG081_UniverseAlign v0100 — 台股每日交易資訊×籌碼 數量對齊與股票清單更新引擎(批390)
====================================================================
操作員令(批390):「台股每日交易資訊及籌碼最後要對齊數量,作為更新股票清單,及核對分別數量一致;
輸出資料都採 parquet 增量擷取、DuckDB 管理」。
機制(Zero-Hydra:只讀正主表,不另抓;鍵律=價表 ticker(1101.TW/.TWO 批307)vs 籌碼 (code,market)→ tw_listings.yf_ticker
      對映,無冊=code+市場後綴推定):
  ① check  逐日核對(最近 N 個交易日;交易日曆=價表實際日期):價表票數 px_n vs 籌碼票數 chip_n(tw_chip_inst ∪ tw_chip_margin)
           → both/px_only/chip_only → 每日判定 ALIGNED(兩側票集合相等)/PARTIAL(交集≥90%)/MISALIGNED;最新日列不一致清單;
           籌碼最新日落後價表=誠實 MISALIGNED 並指路 via-chip run(ENG056)→ VIA_Reports/vdf/universe/ALIGN_latest.json
  ② update 股票清單=基準日(價表∪籌碼)∩ tw_listings(缺冊=價表∪籌碼全員)→ tw_universe(asof_date,ticker,code,market,name,
           in_prices,in_chips,aligned,updated_at);--apply 才寫:DuckDB anti-join 只增(鍵 asof_date,ticker)+ parquet 增量
           (output_hub/mega/tw_universe_<ts>.parquet 只含本次新增列;0 新增=不落檔);預設 dry-run 只印
           基準日律(批393 工作站實錄:最新價日 2026-09-07 只 399 票、籌碼 0,曾以此建清單 399 列=殘缺):預設=最新「雙側齊日」
           (價表票數 ≥ 窗內最大 60% 且籌碼有票且判定 ALIGNED/PARTIAL 的最新日);最新價日 價未齊/籌碼缺=誠實 YELLOW 改以雙側齊日為基準並印修法;
           --asof YYYY-MM-DD 指定基準日;--allow-latest 強制最新價日;status 標殘缺快照(列數 < 最大快照 60%)並報現役基準日 current_asof
  ③ status 上次 ALIGN_latest 摘要 + tw_universe 表現況
紀律:只增不減;正本零觸碰(不改價表/籌碼表);誠實三態(GREEN/YELLOW/RED;庫缺/表缺不假綠);零網路;尾版律;
      讓庫律(批391 工作站實錄:日更鏈/回補持單寫者鎖 → update --apply 曾 IOException traceback):開庫短等重試 6×3s,逾額誠實
      [FAIL] 庫忙 rc3 印修法(等日更鏈/回補跑完再 update --apply;check 唯讀)不再 traceback;持鎖者解析(批393:IOException 內 PID n →
      命令列 → 引擎名+動詞,印一次 [庫忙] 持鎖者;指路 via-bg 背景引擎進程唯讀一覽,絕不 Stop-Process;實錄:via-status 開的是同步頁不是進程表)。
      批400(code review 發現):逐日計數 SQL 端化——_daily_sets() 曾把窗內每一價列/籌碼列 fetchall 進 Python 逐日集合(update --asof 舊日
      窗擴至 3650 交易日≈54.5 萬價列+120 萬籌碼列全數實體化);改 _daily_counts():價/籌碼各去重 (日,票) 後 FULL OUTER JOIN 算交集/差集再
      GROUP BY 日;籌碼對映律仍是 chip_ticker()(只對窗內 DISTINCT (code,market) 在 Python 算一次 → TEMP _chipmap JOIN;零 SQL 重寫=零等價風險);
      單日票集合只由 _date_sets() 取需要的日(check 最新日差集清單/update 基準日清單列);check 表/ALIGN_latest 欄位/判定律/update 列/十一檢
      零變更;_daily_sets 保留為 ⑫ 逐列集合參照實作(只增不減);十二檢 ⑫ 以獨立逐列 Python 集合參照證等價(現有夾具 days=5/寬窗 --asof;
      25 日合成庫 窗 26>20 與 days=3 截窗;對映分支全覆蓋;TEMP 物件僅存本連線不落正本)。
用法:python3 VDF_ENG081_UniverseAlign_v0100.py check [--days N] [--db PATH] [--json]
      | update [--apply] [--asof YYYY-MM-DD] [--allow-latest] [--db PATH] [--json] | status [--db PATH] | --selftest
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

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
REPORTS = VIA / "VIA_Reports" / "vdf" / "universe"
LOG = VIA / "logs" / "vdf_universe_align.log"
PX = "tw_daily_prices"
CHIPS = ("tw_chip_inst", "tw_chip_margin")
UNIVERSE = "tw_universe"
VERBS = ("check", "update", "status")
DAYS_DEFAULT = 20
PARTIAL_FLOOR = 0.90
PX_FULL_FLOOR = 0.60   # 批393:價表票數 ≥ 窗內最大 60% 才算「價齊日」(日更未齊/來源缺=殘缺日,不作清單基準)
_PID_RX = re.compile(r"PID\s*(\d+)")
_ENGINE_RX = re.compile(r"((?:VDF|VRN|VAP|CGC|SUP)_(?:ENG|MDL)\d{3}_[A-Za-z0-9]+(?:_v\d{4})?\.py|via_boot_update\.(?:ps1|sh)|VIA\.ps1|VIA_SYSTEM_MANAGER_v\d{4}\.py)")


# ---------------------------------------------------------------- 基礎
def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def log_event(kind: str, msg: str, **kw) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now(), "kind": kind, "msg": msg, **kw}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, p)


def _duckdb():
    try:
        import duckdb
        return duckdb
    except Exception:
        return None


def _proc_cmdline(pid: int) -> str:
    """持鎖進程命令列(唯讀;Windows=Get-CimInstance Win32_Process;POSIX=ps;失敗=空字串;零第三方依賴;絕不動進程)"""
    import subprocess
    try:
        if os.name == "nt":
            cmd = ["powershell", "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine"]
        else:
            cmd = ["ps", "-o", "args=", "-p", str(int(pid))]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
        return " ".join(out.split())[:240]
    except Exception:
        return ""


def _holder_label(cmdline: str) -> str:
    """命令列 → 引擎名(+動詞):…VDF_ENG064_HistoryBackfill_v0102.py run --resume → 'VDF_ENG064_HistoryBackfill_v0102.py run'"""
    if not cmdline:
        return ""
    m = _ENGINE_RX.search(cmdline)
    if not m:
        return cmdline[:80]
    tail = cmdline[m.end():].strip().strip('"').split()
    verb = tail[0] if tail and not tail[0].startswith("-") else ""
    return (m.group(1) + (" " + verb if verb else "")).strip()


def _holder_of(msg: str) -> tuple:
    """IOException 文字 → (pid, 引擎標籤);無 PID=(None, '')(批393 工作站實錄:File is already open in python.exe (PID 7396))"""
    m = _PID_RX.search(msg or "")
    if not m:
        return (None, "")
    pid = int(m.group(1))
    return (pid, _holder_label(_proc_cmdline(pid)))


def _connect(db: Path, read_only: bool, retries: int = 6, wait: float = 3.0, sleep_fn=None, resolver=None):
    """讓庫律(批391;ENG064/ENG079 同律):DuckDB 單寫者鎖=短等重試;逾額誠實 RuntimeError(主程式印 [FAIL] rc3,零 traceback)
    批393:持鎖者解析(IOException 內 PID n → 命令列 → 引擎名)印一次 [庫忙] 持鎖者;[FAIL] 句指路 via-bg(唯讀一覽;絕不 Stop-Process)"""
    import time
    duckdb = _duckdb()
    last = ""
    holder = None
    for i in range(retries):
        try:
            return duckdb.connect(str(db), read_only=read_only)
        except duckdb.IOException as exc:
            last = str(exc)
            low = last.lower()
            if not any(k in low for k in ("lock", "already open", "being used", "另一個程序", "cannot open file")):
                raise
            if holder is None:
                holder = (resolver or _holder_of)(last)
                if holder[0]:
                    print(f"  [庫忙] 持鎖者 PID {holder[0]}:{holder[1] or '(命令列不可讀)'}(等其跑完;絕不 Stop-Process;via-bg 看全部背景引擎)", flush=True)
            print(f"  [庫忙] {i + 1}/{retries}:{last.splitlines()[0][:90]} → 等 {wait}s", flush=True)
            (sleep_fn or time.sleep)(wait)
    who = f"持鎖者 PID {holder[0]}:{holder[1] or '?'};" if holder and holder[0] else ""
    raise RuntimeError(f"庫忙逾 {retries}×{wait}s({who}日更鏈/歷史回補持單寫者鎖;等其跑完再 via-align {'update --apply' if not read_only else 'check'};via-bg 看背景引擎進程):{last.splitlines()[0][:120]}")


def _q(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def _qi(c) -> str:
    """欄名引號;缺欄=NULL(f-string 內不放反斜線=3.11 相容)"""
    return ('"' + str(c).replace('"', '""') + '"') if c else "NULL"


def _lit(v) -> str:
    """值字面量:None=NULL,其餘 _q 單引號(批400:_chipmap 單句多列 INSERT 用;CAST VARCHAR 後的值只會是 str 或 None)"""
    return "NULL" if v is None else _q(v)


def _tables(con) -> set:
    return {r[0] for r in con.execute("SHOW TABLES").fetchall()}


def _cols(con, t: str) -> dict:
    return {r[0].lower(): r[0] for r in con.execute(f'DESCRIBE "{t}"').fetchall()}


# ---------------------------------------------------------------- 對映(籌碼 code,market → 價表 ticker)
def listings_map(con) -> dict:
    """code → (yf_ticker, name, market);tw_listings 冊優先(批307 鍵律);缺冊=空"""
    m = {}
    if "tw_listings" not in _tables(con):
        return m
    cols = _cols(con, "tw_listings")
    if "code" not in cols:
        return m
    yf = cols.get("yf_ticker")
    sel = f'SELECT {_qi(cols["code"])}, {_qi(yf)}, {_qi(cols.get("name"))}, {_qi(cols.get("market"))} FROM tw_listings'
    for code, y, name, mk in con.execute(sel).fetchall():
        code = str(code).strip()
        mk = str(mk or "").upper()
        y = str(y) if y else (code + (".TW" if mk == "TWSE" else ".TWO" if mk == "TPEX" else ""))
        m[code] = (y, str(name or ""), mk)
    return m


def chip_ticker(code: str, market: str, lst: dict) -> str:
    code = str(code).strip()
    if code in lst and lst[code][0]:
        return lst[code][0]
    mk = str(market or "").upper()
    return code + (".TW" if mk == "TWSE" else ".TWO" if mk in ("TPEX", "OTC") else ".TW")


def _daily_sets(con, have: set, lst: dict, days: int) -> tuple:
    """最近 N 個交易日(交易日曆=價表)→ (px_dates 新→舊, 日→價表票集合, 日→籌碼票集合(inst∪margin 經冊對映), 籌碼最新日)
    批400:逐列 fetchall 全數實體化=寬窗(--asof 舊日 3650 交易日)記憶體/時間熱點;主路徑改 _daily_counts()+_date_sets(),
    本函式保留為逐列 Python 集合參照實作(⑫ 等價證;只增不減),不再於 check/update 主路徑呼叫"""
    chips = [t for t in CHIPS if t in have]
    px_dates = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(date AS VARCHAR) d FROM {PX} WHERE ticker <> '_NOOP_' ORDER BY d DESC LIMIT {int(days)}").fetchall()]
    chip_max = None
    chip_sets: dict = {}
    for t in chips:
        cols = _cols(con, t)
        dc, cc, mc = cols.get("date"), cols.get("code"), cols.get("market")
        if not (dc and cc):
            continue
        mx = con.execute(f'SELECT max(CAST("{dc}" AS VARCHAR)) FROM "{t}"').fetchone()[0]
        if mx and (chip_max is None or str(mx) > chip_max):
            chip_max = str(mx)[:10]
        if px_dates:
            rows = con.execute(f'SELECT CAST({_qi(dc)} AS VARCHAR), {_qi(cc)}, {_qi(mc)} FROM {_qi(t)} WHERE CAST({_qi(dc)} AS VARCHAR) >= {_q(min(px_dates))}').fetchall()
            for d, code, mk in rows:
                chip_sets.setdefault(str(d)[:10], set()).add(chip_ticker(code, mk, lst))
    px_sets: dict = {}
    if px_dates:
        for d, tk in con.execute(f"SELECT CAST(date AS VARCHAR), ticker FROM {PX} WHERE ticker <> '_NOOP_' AND CAST(date AS VARCHAR) >= {_q(min(px_dates))}").fetchall():
            px_sets.setdefault(str(d)[:10], set()).add(str(tk))
    return px_dates, px_sets, chip_sets, chip_max


def _verdict(p: set, c: set) -> str:
    if not c:
        return "MISALIGNED"
    if p == c:
        return "ALIGNED"
    if len(p & c) >= PARTIAL_FLOOR * max(len(p), len(c)):
        return "PARTIAL"
    return "MISALIGNED"


def _verdict_n(px_n: int, chip_n: int, both: int) -> str:
    """批400 計數版判定(與集合版 _verdict 等價:籌碼 0 票=MISALIGNED;兩集合相等 ⟺ 交集數=價票數=籌碼票數;交集 ≥ 90% 大方=PARTIAL)"""
    if not chip_n:
        return "MISALIGNED"
    if both == px_n == chip_n:
        return "ALIGNED"
    if both >= PARTIAL_FLOOR * max(px_n, chip_n):
        return "PARTIAL"
    return "MISALIGNED"


_ZERO = (0, 0, 0, 0, 0)   # 批400:日計數元組 (px_n, chip_n, both, px_only, chip_only);窗內缺日預設


def _daily_counts(con, have: set, lst: dict, days: int) -> tuple:
    """批400(code review):最近 N 個交易日(交易日曆=價表)→ (px_dates 新→舊, 日→(px_n, chip_n, both, px_only, chip_only), 籌碼最新日)
    逐日計數全在 DuckDB 端:價/籌碼各去重 (日,票) 後 FULL OUTER JOIN 算交集/差集再 GROUP BY 日,不再把窗內每一列 fetchall 進 Python
    (update --asof 舊日窗擴至 3650 交易日≈54.5 萬價列+120 萬籌碼列曾全數實體化為逐日集合);
    籌碼對映律仍是 chip_ticker()(只對窗內 DISTINCT (code,market) 對子在 Python 算一次 → TEMP TABLE _chipmap → SQL JOIN,NULL 對子以
    IS NOT DISTINCT FROM 配對=與逐列 str(None) 同律;零 SQL 重寫=零等價風險;載入用單句多列 INSERT 非 executemany);留 TEMP VIEW _align_px/_align_chip(日,票)供 _date_sets()
    只取需要的單日集合;TEMP 物件僅存於本連線(唯讀連線可建;正本零觸碰;Zero-Hydra);鍵律與 _daily_sets 同:日鍵=CAST VARCHAR 前 10 字、
    票=str、查鍵=原日字串;輸出與 _daily_sets 逐列集合算法逐日全等(⑫ 證)"""
    chips = [t for t in CHIPS if t in have]
    px_dates = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(date AS VARCHAR) d FROM {PX} WHERE ticker <> '_NOOP_' ORDER BY d DESC LIMIT {int(days)}").fetchall()]
    lo = min(px_dates) if px_dates else None
    chip_max = None
    parts = []
    for t in chips:
        cols = _cols(con, t)
        dc, cc, mc = cols.get("date"), cols.get("code"), cols.get("market")
        if not (dc and cc):
            continue
        mx = con.execute(f'SELECT max(CAST("{dc}" AS VARCHAR)) FROM "{t}"').fetchone()[0]
        if mx and (chip_max is None or str(mx) > chip_max):
            chip_max = str(mx)[:10]
        if lo:
            parts.append(f'SELECT substr(CAST({_qi(dc)} AS VARCHAR), 1, 10) AS d, CAST({_qi(cc)} AS VARCHAR) AS code, CAST({_qi(mc)} AS VARCHAR) AS market FROM {_qi(t)} WHERE CAST({_qi(dc)} AS VARCHAR) >= {_q(lo)}')
    raw = " UNION ALL ".join(parts) if parts else "SELECT NULL::VARCHAR AS d, NULL::VARCHAR AS code, NULL::VARCHAR AS market WHERE 1=0"
    con.execute("CREATE OR REPLACE TEMP TABLE _chipmap(code VARCHAR, market VARCHAR, ticker VARCHAR)")
    if parts:   # 對映只算窗內 DISTINCT (code,market)(數千對子;NULL 亦為一對子);單句多列 INSERT 分批(實測 executemany 逐列≈1ms/列:1800 列 1.9s → 單句 0.03s)
        pairs = con.execute(f"SELECT DISTINCT code, market FROM ({raw})").fetchall()
        vals = [f"({_lit(code)}, {_lit(mk)}, {_lit(chip_ticker(code, mk, lst))})" for code, mk in pairs]
        for i in range(0, len(vals), 1000):
            con.execute("INSERT INTO _chipmap VALUES " + ", ".join(vals[i:i + 1000]))
    con.execute(f"CREATE OR REPLACE TEMP VIEW _align_chip AS SELECT DISTINCT r.d, m.ticker AS tk FROM ({raw}) r JOIN _chipmap m ON r.code IS NOT DISTINCT FROM m.code AND r.market IS NOT DISTINCT FROM m.market")
    px_where = f"ticker <> '_NOOP_' AND CAST(date AS VARCHAR) >= {_q(lo)}" if lo else "1=0"
    con.execute(f"CREATE OR REPLACE TEMP VIEW _align_px AS SELECT DISTINCT substr(CAST(date AS VARCHAR), 1, 10) AS d, CAST(ticker AS VARCHAR) AS tk FROM {PX} WHERE {px_where}")
    counts: dict = {}
    if px_dates:
        sql = ("SELECT COALESCE(p.d, c.d) AS d, count(p.tk), count(c.tk), "
               "count(CASE WHEN p.tk IS NOT NULL AND c.tk IS NOT NULL THEN 1 END), "
               "count(CASE WHEN p.tk IS NOT NULL AND c.tk IS NULL THEN 1 END), "
               "count(CASE WHEN p.tk IS NULL AND c.tk IS NOT NULL THEN 1 END) "
               "FROM _align_px p FULL OUTER JOIN _align_chip c ON p.d = c.d AND p.tk = c.tk GROUP BY 1")
        for d, n, m, b, po, co in con.execute(sql).fetchall():
            counts[str(d)[:10]] = (int(n), int(m), int(b), int(po), int(co))
    return px_dates, counts, chip_max


def _date_sets(con, d) -> tuple:
    """批400:單日 (價表票集合, 籌碼票集合)——只實體化需要的那一日(check 最新日差集清單/update 基準日清單列);
    須先於同一連線跑過 _daily_counts()(用其 TEMP VIEW);查鍵=原日字串(與 _daily_sets 字典查鍵同律);無列=空集合"""
    p = {str(r[0]) for r in con.execute("SELECT tk FROM _align_px WHERE d = ?", [d]).fetchall()}
    c = {str(r[0]) for r in con.execute("SELECT tk FROM _align_chip WHERE d = ?", [d]).fetchall()}
    return p, c


def _pick_asof(px_dates: list, px_sets: dict, chip_sets: dict, px_top: int, asof: str | None = None, allow_latest: bool = False, counts: dict | None = None) -> dict:
    """基準日律(批393):--asof 指定 > --allow-latest 最新價日 > 最新雙側齊日(價 ≥ 窗內最大 60%、籌碼有票、ALIGNED/PARTIAL)
    > 最新雙側有票日 > 最新價日(籌碼全缺);非雙側齊日一律 YELLOW 並印修法(誠實三態;殘缺日不假綠)
    批400:給 counts(日→計數元組)即走計數版 _verdict_n 不實體化集合(px_sets/chip_sets 可為 None);無 counts=集合版原律"""
    def row(d):
        if counts is not None:
            n, m, b = counts.get(d, _ZERO)[:3]
            return n, m, _verdict_n(n, m, b), n >= PX_FULL_FLOOR * px_top
        p, c = px_sets.get(d, set()), chip_sets.get(d, set())
        return len(p), len(c), _verdict(p, c), len(p) >= PX_FULL_FLOOR * px_top
    d_latest = px_dates[0]
    n0, m0, v0, full0 = row(d_latest)
    if asof:
        if asof not in px_dates:
            return {"asof": None, "lamp": "RED", "rule": "--asof", "why": "", "error": f"基準日 {asof} 不在價表交易日(窗內 {px_dates[-1]}…{d_latest} 共 {len(px_dates)} 日)"}
        n, m, v, full = row(asof)
        good = bool(m) and v != "MISALIGNED" and full
        return {"asof": asof, "lamp": "GREEN" if good else "YELLOW", "rule": "--asof 指定",
                "why": "" if good else f"指定基準日 {asof} 價 {n} 籌碼 {m} {v}{'' if full else '(價未齊)'}=非雙側齊日(操作員指定,照辦)"}
    good0 = bool(m0) and v0 != "MISALIGNED" and full0
    if allow_latest or good0:
        return {"asof": d_latest, "lamp": "GREEN" if good0 else "YELLOW", "rule": "最新價日" if good0 else "--allow-latest 強制最新價日",
                "why": "" if good0 else f"最新價日 {d_latest} 價 {n0} 籌碼 {m0} {v0}{'' if full0 else '(價未齊)'}=非雙側齊日(--allow-latest 強制)"}
    flaw = ("(價未齊<窗內最大 " + str(px_top) + " 之 60%)" if not full0 else "") + ("(籌碼缺/落後)" if not m0 else "")
    for d in px_dates:
        n, m, v, full = row(d)
        if m and v != "MISALIGNED" and full:
            return {"asof": d, "lamp": "YELLOW", "rule": "最新雙側齊日",
                    "why": f"最新價日 {d_latest} 價 {n0} 籌碼 {m0}{flaw}=殘缺日不作基準 → 基準日改最新雙側齊日 {d}(價 {n} 籌碼 {m} {v});--asof 指定;--allow-latest 強制最新價日"}
    for d in px_dates:
        n, m, v, full = row(d)
        if m and n:
            return {"asof": d, "lamp": "YELLOW", "rule": "最新雙側有票日(窗內無齊日)",
                    "why": f"窗內無雙側齊日 → 基準日改最新雙側有票日 {d}(價 {n} 籌碼 {m} {v});先 via-chip run(ENG056)補籌碼再 update"}
    return {"asof": d_latest, "lamp": "YELLOW", "rule": "最新價日(窗內籌碼全缺)",
            "why": f"窗內籌碼全缺 → 清單只含價表側(asof {d_latest} 價 {n0});先 via-chip run(ENG056)補籌碼再 update"}


# ---------------------------------------------------------------- ① check
def check(db: Path = DB_TW, days: int = DAYS_DEFAULT, reports: Path = REPORTS, do_print: bool = True) -> dict:
    rep = {"schema": "VIA.UniverseAlign.v1", "ts": _now(), "db": str(db), "days": days, "verdict": "GREEN", "note": "", "dates": [], "mismatch": {"px_only": [], "chip_only": []},
           "latest": {}, "summary": {}}

    def say(s):
        if do_print:
            print(s, flush=True)

    duckdb = _duckdb()
    if duckdb is None:
        rep["verdict"], rep["note"] = "RED", "duckdb 缺(於 via_vdf_312 境跑:via-align;或 via-py vdf)"
        say(f"RED     {rep['note']}")
        _finish(rep, reports, "ALIGN")
        return rep
    if not db.exists():
        rep["verdict"], rep["note"] = "RED", f"庫缺 {db}(先 via-vdfdb run --apply / ENG054)"
        say(f"RED     {rep['note']}")
        _finish(rep, reports, "ALIGN")
        return rep
    con = _connect(db, read_only=True)
    try:
        have = _tables(con)
        if PX not in have:
            rep["verdict"], rep["note"] = "RED", f"價表缺 {PX}"
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "ALIGN")
            return rep
        chips = [t for t in CHIPS if t in have]
        if not chips:
            rep["verdict"], rep["note"] = "RED", f"籌碼表缺 {CHIPS}(先 via-chip run=ENG056)"
            say(f"RED     {rep['note']}")
        lst = listings_map(con)
        rep["summary"]["listings"] = len(lst)
        px_dates, counts, chip_max = _daily_counts(con, have, lst, days)   # 批400:逐日計數 SQL 端化(不再逐列 fetchall 進 Python)
        rep["summary"]["px_max"] = px_dates[0] if px_dates else None
        rep["summary"]["chip_max"] = chip_max
        px_top = max((counts.get(d, _ZERO)[0] for d in px_dates), default=0)
        rep["summary"]["px_top"] = px_top
        n_al = n_part = n_mis = 0
        for d in px_dates:
            n, m, b, po, co = counts.get(d, _ZERO)
            v = _verdict_n(n, m, b)
            n_al += v == "ALIGNED"
            n_part += v == "PARTIAL"
            n_mis += v == "MISALIGNED"
            rep["dates"].append({"date": d, "px_n": n, "chip_n": m, "both": b, "px_only": po, "chip_only": co, "verdict": v,
                                 "px_full": n >= PX_FULL_FLOOR * px_top})
        if px_dates:
            d0 = px_dates[0]
            p, c = _date_sets(con, d0)   # 批400:只實體化最新日(差集清單需集合)
            rep["latest"] = {"date": d0, "px_n": len(p), "chip_n": len(c), "both": len(p & c), "verdict": rep["dates"][0]["verdict"]}
            rep["mismatch"] = {"px_only": sorted(p - c)[:200], "chip_only": sorted(c - p)[:200], "px_only_n": len(p - c), "chip_only_n": len(c - p)}
        rep["summary"].update({"dates": len(px_dates), "aligned": n_al, "partial": n_part, "misaligned": n_mis})
        if rep["verdict"] != "RED":
            if not px_dates:
                rep["verdict"], rep["note"] = "RED", "價表無交易日"
            elif chip_max and rep["summary"]["px_max"] and chip_max < rep["summary"]["px_max"]:
                lag = (_dt.date.fromisoformat(rep["summary"]["px_max"]) - _dt.date.fromisoformat(chip_max)).days
                rep["verdict"] = "MISALIGNED"
                rep["note"] = f"籌碼最新日 {chip_max} 落後價表 {rep['summary']['px_max']}({lag} 日)→ via-chip run(ENG056 籌碼增量;交易日曆=價表,回補新增日後需重跑)後重核"
            elif n_mis:
                rep["verdict"] = "MISALIGNED"
                rep["note"] = f"{n_mis}/{len(px_dates)} 日票集合不一致(最新日 只有價 {rep['mismatch'].get('px_only_n', 0)} · 只有籌碼 {rep['mismatch'].get('chip_only_n', 0)})→ 差集見 mismatch;更新清單 via-align update --apply"
            elif n_part:
                rep["verdict"] = "PARTIAL"
                rep["note"] = f"{n_part}/{len(px_dates)} 日交集 ≥ {int(PARTIAL_FLOOR * 100)}% 但未全等(最新日 只有價 {rep['mismatch'].get('px_only_n', 0)} · 只有籌碼 {rep['mismatch'].get('chip_only_n', 0)})"
            else:
                rep["verdict"] = "ALIGNED"
                rep["note"] = f"{len(px_dates)} 日票集合全等(最新日 {rep['latest'].get('px_n', 0)} 票)"
            if rep["dates"] and not rep["dates"][0]["px_full"]:
                if rep["verdict"] == "ALIGNED":
                    rep["verdict"] = "PARTIAL"
                rep["note"] = f"最新價日 {rep['dates'][0]['date']} 價 {rep['dates'][0]['px_n']} < 窗內最大 {px_top} 之 60%=日更未齊(via-price run=ENG054 增量補齊;清單基準日自動改雙側齊日)· " + rep["note"]
    finally:
        con.close()
    _finish(rep, reports, "ALIGN")
    if do_print:
        lamp = {"ALIGNED": "GREEN", "PARTIAL": "YELLOW", "MISALIGNED": "YELLOW"}.get(rep["verdict"], rep["verdict"])
        say(f"[via-align check] {rep['verdict']}({lamp})· {rep['note']}")
        for d in rep["dates"][:10]:
            say(f"  {d['date']}  價 {d['px_n']:>5}  籌碼 {d['chip_n']:>5}  皆有 {d['both']:>5}  只價 {d['px_only']:>4}  只籌 {d['chip_only']:>4}  {d['verdict']}{'' if d.get('px_full', True) else '  價未齊'}")
        if len(rep["dates"]) > 10:
            say(f"  … 其餘 {len(rep['dates']) - 10} 日見 ALIGN_latest.json")
        say(f"  存證 {reports / 'ALIGN_latest.json'}")
    return rep


# ---------------------------------------------------------------- ② update
def update(db: Path = DB_TW, apply: bool = False, reports: Path = REPORTS, mega: Path | None = None, do_print: bool = True, asof: str | None = None, allow_latest: bool = False) -> dict:
    rep = {"schema": "VIA.UniverseUpdate.v1", "ts": _now(), "db": str(db), "mode": "apply" if apply else "dry-run", "verdict": "GREEN", "note": "", "asof": None, "latest_px_date": None, "asof_rule": "", "rows": 0, "new": 0, "parquet": "", "summary": {}}

    def say(s):
        if do_print:
            print(s, flush=True)

    duckdb = _duckdb()
    if duckdb is None or not db.exists():
        rep["verdict"], rep["note"] = "RED", ("duckdb 缺(via_vdf_312 境)" if duckdb is None else f"庫缺 {db}")
        say(f"RED     {rep['note']}")
        _finish(rep, reports, "UNIVERSE")
        return rep
    con = _connect(db, read_only=not apply)
    try:
        have = _tables(con)
        if PX not in have:
            rep["verdict"], rep["note"] = "RED", f"價表缺 {PX}"
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "UNIVERSE")
            return rep
        lst = listings_map(con)
        days = DAYS_DEFAULT
        if asof:   # 指定基準日=窗擴到含該日(上限 3650 交易日)
            k = con.execute(f"SELECT count(DISTINCT CAST(date AS VARCHAR)) FROM {PX} WHERE ticker <> '_NOOP_' AND CAST(date AS VARCHAR) >= {_q(str(asof)[:10])}").fetchone()[0]
            days = max(DAYS_DEFAULT, min(3650, int(k or 0) + 1))
        px_dates, counts, chip_max = _daily_counts(con, have, lst, days)   # 批400:寬窗(--asof 舊日)只算逐日計數,不實體化每日集合
        if not px_dates:
            rep["verdict"], rep["note"] = "RED", "價表空"
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "UNIVERSE")
            return rep
        px_top = max(counts.get(d, _ZERO)[0] for d in px_dates)
        pick = _pick_asof(px_dates, None, None, px_top, asof=str(asof)[:10] if asof else None, allow_latest=allow_latest, counts=counts)
        rep.update({"latest_px_date": px_dates[0], "asof_rule": pick["rule"], "px_top": px_top, "chip_max": chip_max})
        if pick.get("error"):
            rep["verdict"], rep["note"] = "RED", pick["error"]
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "UNIVERSE")
            return rep
        d0 = pick["asof"]
        px, chips = _date_sets(con, d0)   # 批400:只實體化基準日(清單列需集合)
        by_yf = {v[0]: (k, v[1], v[2]) for k, v in lst.items()}
        union = px | chips
        rows = []
        for tk in sorted(union):
            code, name, mk = by_yf.get(tk, (tk.split(".")[0], "", "TWSE" if tk.endswith(".TW") else "TPEX" if tk.endswith(".TWO") else ""))
            if lst and tk not in by_yf:
                continue   # 有冊=∩ tw_listings(下市/非股票碼不入清單)
            rows.append((d0, tk, code, mk, name, tk in px, tk in chips, tk in px and tk in chips, rep["ts"]))
        rep.update({"asof": d0, "rows": len(rows), "summary": {"px": len(px), "chips": len(chips), "union": len(union), "listed": len(rows), "aligned": sum(1 for r in rows if r[7]), "listings": len(lst)}})
        if not rows:
            rep["verdict"], rep["note"] = "RED", "最新日無票(價表/籌碼皆空)"
            say(f"RED     {rep['note']}")
            _finish(rep, reports, "UNIVERSE")
            return rep
        con.execute("CREATE OR REPLACE TEMP TABLE _uni(asof_date VARCHAR, ticker VARCHAR, code VARCHAR, market VARCHAR, name VARCHAR, in_prices BOOLEAN, in_chips BOOLEAN, aligned BOOLEAN, updated_at VARCHAR)")
        con.executemany("INSERT INTO _uni VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
        if UNIVERSE in have:
            n_new = con.execute(f"SELECT count(*) FROM _uni s WHERE NOT EXISTS (SELECT 1 FROM {UNIVERSE} t WHERE t.asof_date = s.asof_date AND t.ticker = s.ticker)").fetchone()[0]
        else:
            n_new = len(rows)
        rep["new"] = n_new
        if apply:
            if UNIVERSE not in have:
                con.execute(f"CREATE TABLE {UNIVERSE} AS SELECT * FROM _uni WHERE 1=0")
            con.execute(f"CREATE OR REPLACE TEMP TABLE _uni_new AS SELECT s.* FROM _uni s WHERE NOT EXISTS (SELECT 1 FROM {UNIVERSE} t WHERE t.asof_date = s.asof_date AND t.ticker = s.ticker)")
            if n_new:
                con.execute(f"INSERT INTO {UNIVERSE} SELECT * FROM _uni_new")
                mega = mega or MEGA
                mega.mkdir(parents=True, exist_ok=True)
                pq = mega / f"tw_universe_{_ts()}.parquet"
                try:
                    con.execute(f"COPY _uni_new TO {_q(str(pq).replace(chr(92), '/'))} (FORMAT PARQUET)")
                    rep["parquet"] = str(pq)
                except Exception as exc:
                    rep["note"] += f";parquet 落檔失敗 {str(exc)[:60]}"
            rep["verdict"] = "GREEN"
            rep["note"] = (f"tw_universe +{n_new} 列(asof {d0};anti-join 只增;parquet 增量 {Path(rep['parquet']).name if rep['parquet'] else '0 新增=不落檔'})" + rep["note"]) if True else ""
        else:
            rep["verdict"] = "GREEN"
            rep["note"] = f"dry-run:清單 {len(rows)} 票(asof {d0};價 {len(px)} ∪ 籌碼 {len(chips)} ∩ 冊 {len(lst) or '無冊'})· 計畫新增 {n_new}(--apply 才寫)"
        if rep["summary"]["aligned"] < rep["summary"]["listed"]:
            rep["note"] += f" · 未對齊 {rep['summary']['listed'] - rep['summary']['aligned']} 票(in_prices/in_chips 單側)"
        if pick["lamp"] == "YELLOW":   # 批393 基準日律:非雙側齊日=誠實 YELLOW 印修法(仍可寫;只增不減)
            rep["verdict"] = "YELLOW"
            rep["note"] += " · " + pick["why"]
    finally:
        con.close()
    _finish(rep, reports, "UNIVERSE")
    say(f"[via-align update] {rep['verdict']} · {rep['note']} · 存證 {reports / 'UNIVERSE_latest.json'}")
    return rep


def status(db: Path = DB_TW, reports: Path = REPORTS, do_print: bool = True) -> dict:
    out = {"align": None, "universe": None}
    p = reports / "ALIGN_latest.json"
    if p.exists():
        try:
            a = json.loads(p.read_text(encoding="utf-8"))
            out["align"] = {"ts": a.get("ts"), "verdict": a.get("verdict"), "note": a.get("note"), "latest": a.get("latest")}
        except Exception:
            pass
    duckdb = _duckdb()
    if duckdb and db.exists():
        try:
            con = _connect(db, read_only=True, retries=2, wait=1.0)
            try:
                if UNIVERSE in _tables(con):
                    n, mx, k = con.execute(f"SELECT count(*), max(asof_date), count(DISTINCT asof_date) FROM {UNIVERSE}").fetchone()
                    snaps = con.execute(f"SELECT asof_date, count(*), sum(CASE WHEN aligned THEN 1 ELSE 0 END) FROM {UNIVERSE} GROUP BY asof_date ORDER BY asof_date DESC").fetchall()
                    top = max((int(x[1]) for x in snaps), default=0)
                    det = [{"asof": str(x[0]), "rows": int(x[1]), "aligned": int(x[2] or 0), "state": "OK" if int(x[1]) >= PX_FULL_FLOOR * top else "PARTIAL(殘缺日快照;列數<最大快照 60%;批393)"} for x in snaps]
                    out["universe"] = {"rows": n, "asof_max": mx, "snapshots": k, "detail": det[:12], "current_asof": next((d["asof"] for d in det if d["state"] == "OK"), None)}
            finally:
                con.close()
        except Exception:
            pass
    if do_print:
        a = out["align"]
        print(f"[via-align status] 對齊 {a['verdict'] + ' ' + str(a['note'])[:100] if a else '未跑(via-align check)'} · 清單 {out['universe'] or '未建(via-align update --apply)'}")
    return out


def _finish(rep: dict, reports: Path, stem: str) -> None:
    try:
        _write_json(reports / f"{stem}_{_ts()}.json", rep)
        _write_json(reports / f"{stem}_latest.json", rep)
    except Exception as exc:
        rep["note"] += f";存證失敗 {str(exc)[:60]}"
    log_event(stem, rep.get("verdict", "?"), note=rep.get("note", "")[:200])


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    duckdb = _duckdb()
    if duckdb is None:
        print("  [FAIL] duckdb 缺=本引擎不可測(於 via_vdf_312 境跑)")
        return 1
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db, reports, mega = root / "vdf_tw_market.duckdb", root / "reports", root / "mega"
        c = duckdb.connect(str(db))
        c.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR, yf_ticker VARCHAR)")
        c.executemany("INSERT INTO tw_listings VALUES (?, ?, ?, ?)", [("2330", "台積電", "TWSE", "2330.TW"), ("2454", "聯發科", "TWSE", "2454.TW"), ("6488", "環球晶", "TPEX", "6488.TWO"), ("2317", "鴻海", "TWSE", "2317.TW")])
        c.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c.executemany("INSERT INTO tw_daily_prices VALUES (?, ?, ?)", [
            ("2026-09-01", "2330.TW", 1.0), ("2026-09-01", "2454.TW", 1.0), ("2026-09-01", "6488.TWO", 1.0),
            ("2026-09-02", "2330.TW", 1.0), ("2026-09-02", "2454.TW", 1.0), ("2026-09-02", "6488.TWO", 1.0), ("2026-09-02", "2317.TW", 1.0),
            ("2026-09-03", "2330.TW", 1.0), ("2026-09-03", "2454.TW", 1.0), ("2026-09-03", "6488.TWO", 1.0), ("2026-09-03", "9999.TW", 1.0)])
        c.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR, foreign_net DOUBLE)")
        c.executemany("INSERT INTO tw_chip_inst VALUES (?, ?, ?, ?)", [
            ("2026-09-01", "2330", "TWSE", 1.0), ("2026-09-01", "2454", "TWSE", 1.0), ("2026-09-01", "6488", "TPEX", 1.0),
            ("2026-09-02", "2330", "TWSE", 1.0), ("2026-09-02", "2454", "TWSE", 1.0), ("2026-09-02", "6488", "TPEX", 1.0), ("2026-09-02", "2317", "TWSE", 1.0),
            ("2026-09-03", "2330", "TWSE", 1.0), ("2026-09-03", "2454", "TWSE", 1.0)])
        c.execute("CREATE TABLE tw_chip_margin(date DATE, code VARCHAR, market VARCHAR, margin_bal DOUBLE)")
        c.executemany("INSERT INTO tw_chip_margin VALUES (?, ?, ?, ?)", [("2026-09-03", "6488", "TPEX", 1.0), ("2026-09-03", "2317", "TWSE", 1.0)])
        c.close()
        r = check(db, days=5, reports=reports, do_print=False)
        by = {d["date"]: d for d in r["dates"]}
        chk("① check 逐日核對(交易日曆=價表;籌碼 inst∪margin 經 tw_listings 對映 yahoo 票;01/02 全等 ALIGNED;03 價 9999 無籌碼、籌碼 2317 無價=MISALIGNED;差集清單;ALIGN_latest.json)",
            r["summary"]["dates"] == 3 and by["2026-09-01"]["verdict"] == "ALIGNED" and by["2026-09-02"]["verdict"] == "ALIGNED" and by["2026-09-02"]["px_n"] == 4
            and by["2026-09-03"]["verdict"] == "MISALIGNED" and by["2026-09-03"]["px_only"] == 1 and by["2026-09-03"]["chip_only"] == 1
            and r["mismatch"]["px_only"] == ["9999.TW"] and r["mismatch"]["chip_only"] == ["2317.TW"] and r["verdict"] == "MISALIGNED" and (reports / "ALIGN_latest.json").exists(),
            f"({r['verdict']};{[(d['date'], d['verdict'], d['px_n'], d['chip_n']) for d in r['dates']]})")
        u0 = update(db, apply=False, reports=reports, mega=mega, do_print=False, allow_latest=True)
        u1 = update(db, apply=True, reports=reports, mega=mega, do_print=False, allow_latest=True)
        c2 = duckdb.connect(str(db), read_only=True)
        rows = c2.execute(f"SELECT ticker, code, market, in_prices, in_chips, aligned FROM {UNIVERSE} ORDER BY ticker").fetchall()
        c2.close()
        pq = sorted(mega.glob("tw_universe_*.parquet"))
        chk("② update 股票清單(--allow-latest 最新日 價∪籌碼 ∩ 冊:9999 非冊不入;2317 只籌碼 in_prices=False;dry-run 零寫;--apply 建表 4 列 + parquet 增量 1 檔)",
            u0["mode"] == "dry-run" and u0["rows"] == 4 and u0["new"] == 4 and u1["new"] == 4 and len(rows) == 4
            and rows == [("2317.TW", "2317", "TWSE", False, True, False), ("2330.TW", "2330", "TWSE", True, True, True), ("2454.TW", "2454", "TWSE", True, True, True), ("6488.TWO", "6488", "TPEX", True, True, True)]
            and len(pq) == 1, f"(dry {u0['rows']}/{u0['new']};apply +{u1['new']};rows {rows};pq {len(pq)})")
        u2 = update(db, apply=True, reports=reports, mega=mega, do_print=False, allow_latest=True)
        chk("③ 重跑冪等(anti-join 0 新增;不落新 parquet)", u2["new"] == 0 and len(sorted(mega.glob("tw_universe_*.parquet"))) == 1 and (reports / "UNIVERSE_latest.json").exists(), f"(+{u2['new']})")
        st = status(db, reports=reports, do_print=False)
        chk("④ status(對齊摘要+清單現況+快照明細/現役基準日)", st["align"]["verdict"] == "MISALIGNED" and st["universe"]["rows"] == 4 and st["universe"]["snapshots"] == 1
            and st["universe"]["current_asof"] == "2026-09-03" and st["universe"]["detail"][0]["state"] == "OK")
        c3 = duckdb.connect(str(db))
        c3.execute("DELETE FROM tw_chip_inst WHERE CAST(date AS VARCHAR) = '2026-09-03'")
        c3.execute("DELETE FROM tw_chip_margin WHERE CAST(date AS VARCHAR) = '2026-09-03'")
        c3.close()
        r2 = check(db, days=5, reports=reports, do_print=False)
        chk("⑤ 籌碼落後價表=誠實 MISALIGNED 指路 via-chip run(ENG056)", r2["verdict"] == "MISALIGNED" and "落後" in r2["note"] and "via-chip" in r2["note"] and r2["summary"]["chip_max"] == "2026-09-02", f"({r2['note'][:80]})")
        u4 = update(db, apply=False, reports=reports, mega=mega, do_print=False)
        u5 = update(db, apply=False, reports=reports, mega=mega, do_print=False, allow_latest=True)
        u6 = update(db, apply=False, reports=reports, mega=mega, do_print=False, asof="2026-09-01")
        u7 = update(db, apply=False, reports=reports, mega=mega, do_print=False, asof="2026-12-31")
        c5 = duckdb.connect(str(db))
        c5.execute("INSERT INTO tw_daily_prices VALUES ('2026-09-04', '2330.TW', 1.0)")   # 殘缺日:只 1 票(<60% 窗內最大 4)
        c5.close()
        r4 = check(db, days=5, reports=reports, do_print=False)
        u8 = update(db, apply=False, reports=reports, mega=mega, do_print=False)
        chk("⑩ 基準日律(批393 實錄:最新價日只價無籌碼/價未齊=殘缺日不作清單基準 → 最新雙側齊日 09-02 YELLOW 印修法;check 標「價未齊」;--allow-latest 強制最新價日;--asof 指定;壞基準日 RED)",
            u4["asof"] == "2026-09-02" and u4["verdict"] == "YELLOW" and "基準日改" in u4["note"] and u4["latest_px_date"] == "2026-09-03" and u4["rows"] == 4
            and u5["asof"] == "2026-09-03" and u5["verdict"] == "YELLOW" and u6["asof"] == "2026-09-01" and u6["rows"] == 3 and u6["verdict"] == "GREEN" and u7["verdict"] == "RED"
            and r4["dates"][0]["date"] == "2026-09-04" and r4["dates"][0]["px_full"] is False and "日更未齊" in r4["note"] and u8["asof"] == "2026-09-02" and "價未齊" in u8["note"],
            f"(u4 {u4['asof']} {u4['verdict']};u5 {u5['asof']};u6 {u6['asof']}/{u6['rows']};u7 {u7['verdict']};r4 {r4['dates'][0]['px_n']}/{r4['summary'].get('px_top')} {r4['verdict']};u8 {u8['asof']})")
        # ⑫ 批400(code review):逐日計數 SQL 端化(_daily_counts=價/籌碼去重後 FULL OUTER JOIN 算交集/差集再 GROUP BY 日;籌碼對映只對 DISTINCT (code,market)
        #    經 chip_ticker → TEMP _chipmap JOIN)與「逐列 fetchall+chip_ticker 逐列對映+Python 集合」獨立參照算法逐日 (px_n,chip_n,both,px_only,chip_only) 全等;
        #    保留的 _daily_sets 同證;SQL 對映視圖 _align_chip(日,票)=Python 逐列對映;_date_sets 單日集合=參照;check 表列/最新日差集/判定與 update 摘要/列數=參照;
        #    現有夾具 days=5 + 寬窗 update --asof 2026-09-01;25 日合成庫(冊 yf 空/NULL 走冊後綴推定;無冊碼 OTC/小寫 otc/NULL 市場/未知市場走 chip_ticker
        #    後綴推定;_NOOP_ 與重複列去重;inst∪margin 去重)days=3 截窗/25 全窗/--asof 最舊日 窗 26>DAYS_DEFAULT;計數版 _verdict_n=集合版 _verdict;TEMP 物件不落正本
        def ref_counts(dbp, days):
            """參照:逐列 fetchall + chip_ticker 逐列對映 + Python 集合(獨立於 _daily_sets/_daily_counts)→ (px_dates, 日→五計數, 日→價集合, 日→籌碼集合, 全等, 各旗標)"""
            cx = duckdb.connect(str(dbp), read_only=True)
            try:
                hv, ls = _tables(cx), listings_map(cx)
                pd_ = [r[0] for r in cx.execute(f"SELECT DISTINCT CAST(date AS VARCHAR) d FROM {PX} WHERE ticker <> '_NOOP_' ORDER BY d DESC LIMIT {int(days)}").fetchall()]
                ps, cs = {}, {}
                for d, tk in cx.execute(f"SELECT CAST(date AS VARCHAR), ticker FROM {PX} WHERE ticker <> '_NOOP_' AND CAST(date AS VARCHAR) >= {_q(min(pd_))}").fetchall():
                    ps.setdefault(str(d)[:10], set()).add(str(tk))
                for t in [t for t in CHIPS if t in hv]:
                    for d, code, mk in cx.execute(f'SELECT CAST(date AS VARCHAR), code, market FROM "{t}" WHERE CAST(date AS VARCHAR) >= {_q(min(pd_))}').fetchall():
                        cs.setdefault(str(d)[:10], set()).add(chip_ticker(code, mk, ls))
                old = _daily_sets(cx, hv, ls, days)
                new = _daily_counts(cx, hv, ls, days)
                view = {(str(r[0]), str(r[1])) for r in cx.execute("SELECT d, tk FROM _align_chip").fetchall()}
                one = _date_sets(cx, pd_[0])
            finally:
                cx.close()
            ref = {d: (len(ps.get(d, set())), len(cs.get(d, set())), len(ps.get(d, set()) & cs.get(d, set())), len(ps.get(d, set()) - cs.get(d, set())), len(cs.get(d, set()) - ps.get(d, set()))) for d in pd_}
            flags = (old == (pd_, ps, cs, new[2]), new[0] == pd_ and {d: new[1].get(d, _ZERO) for d in pd_} == ref,
                     view == {(d, tk) for d, s in cs.items() for tk in s}, one == (ps.get(pd_[0], set()), cs.get(pd_[0], set())))
            return pd_, ref, ps, cs, all(flags), flags

        def five(x):
            return (x["px_n"], x["chip_n"], x["both"], x["px_only"], x["chip_only"])

        pd5, ref5, ps5, cs5, ok5, fl5 = ref_counts(db, 5)
        r12 = check(db, days=5, reports=reports, do_print=False)
        got5 = {x["date"]: five(x) for x in r12["dates"]}
        p0, c0 = ps5.get(pd5[0], set()), cs5.get(pd5[0], set())
        ok_chk = (list(got5) == pd5 and got5 == ref5 and r12["mismatch"]["px_only"] == sorted(p0 - c0)[:200] and r12["mismatch"]["chip_only"] == sorted(c0 - p0)[:200]
                  and r12["latest"] == {"date": pd5[0], "px_n": len(p0), "chip_n": len(c0), "both": len(p0 & c0), "verdict": _verdict(p0, c0)}
                  and all(x["verdict"] == _verdict(ps5.get(x["date"], set()), cs5.get(x["date"], set())) for x in r12["dates"]) and r12["summary"]["px_top"] == max(v[0] for v in ref5.values()))
        u12 = update(db, apply=False, reports=reports, mega=mega, do_print=False, asof="2026-09-01")   # 寬窗:含該日 k=4 → days=max(20,5)=20
        pdw, refw, psw, csw, okw, flw = ref_counts(db, 20)
        pw, cw = psw.get("2026-09-01", set()), csw.get("2026-09-01", set())
        ok_upd = (okw and u12["asof"] == "2026-09-01" and u12["verdict"] == "GREEN" and u12["rows"] == 3 and u12["px_top"] == max(v[0] for v in refw.values())
                  and u12["summary"]["px"] == len(pw) and u12["summary"]["chips"] == len(cw) and u12["summary"]["union"] == len(pw | cw) and u12["summary"]["aligned"] == len(pw & cw))
        db12 = root / "wide.duckdb"
        c12 = duckdb.connect(str(db12))
        c12.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR, yf_ticker VARCHAR)")
        c12.executemany("INSERT INTO tw_listings VALUES (?, ?, ?, ?)", [("2330", "台積電", "TWSE", "2330.TW"), ("2454", "聯發科", "TWSE", "2454.TW"), ("6488", "環球晶", "TPEX", "6488.TWO"),
                                                                        ("2317", "鴻海", "TWSE", "2317.TW"), ("3008", "大立光", "TWSE", ""), ("5483", "中美晶", "TPEX", None)])
        c12.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c12.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR, foreign_net DOUBLE)")
        c12.execute("CREATE TABLE tw_chip_margin(date DATE, code VARCHAR, market VARCHAR, margin_bal DOUBLE)")
        wd, day = [], _dt.date(2026, 7, 27)
        while len(wd) < 25:
            if day.weekday() < 5:
                wd.append(day.isoformat())
            day += _dt.timedelta(days=1)
        pxr, inr, mgr = [], [], []
        for i, ds in enumerate(wd):
            pxr += [(ds, "2330.TW", 1.0), (ds, "2454.TW", 1.0), (ds, "6488.TWO", 1.0), (ds, "3008.TW", 1.0), (ds, "_NOOP_", 0.0), (ds, "2330.TW", 1.0)]
            pxr += [(ds, "2317.TW", 1.0)] if i % 3 == 0 else []
            pxr += [(ds, "9999.TW", 1.0)] if i % 4 == 1 else []
            pxr += [(ds, "5483.TWO", 1.0), (ds, "8888.TWO", 1.0), (ds, "7777.TW", 1.0)] if i % 7 == 6 else []
            inr += [(ds, "2330", "TWSE", 1.0), (ds, "2454", "TWSE", 1.0), (ds, "6488", "TPEX", 1.0), (ds, "3008", "TWSE", 1.0)]
            inr += [(ds, "2317", "TWSE", 1.0)] if i % 5 == 2 else []
            inr += [(ds, "5483", "OTC", 1.0), (ds, "8888", "otc", 1.0), (ds, "7777", None, 1.0), (ds, "6666", "XX", 1.0)] if i % 7 == 6 else []
            mgr += [(ds, "2330", "TWSE", 1.0), (ds, "6488", "TPEX", 1.0)] + ([(ds, "2454", "TWSE", 1.0)] if i % 6 == 5 else []) + ([(ds, "1234", "TPEX", 1.0)] if i == 24 else [])
        c12.executemany("INSERT INTO tw_daily_prices VALUES (?, ?, ?)", pxr)
        c12.executemany("INSERT INTO tw_chip_inst VALUES (?, ?, ?, ?)", inr)
        c12.executemany("INSERT INTO tw_chip_margin VALUES (?, ?, ?, ?)", mgr)
        c12.close()
        pd3, ref3, ps3, cs3, ok3, fl3 = ref_counts(db12, 3)
        pd25, ref25, ps25, cs25, ok25, fl25 = ref_counts(db12, 25)
        rw3 = check(db12, days=3, reports=reports, do_print=False)
        rw25 = check(db12, days=25, reports=reports, do_print=False)
        uw = update(db12, apply=False, reports=reports, mega=mega, do_print=False, asof=wd[0])   # 寬窗:含最舊日 k=25 → days=26 > DAYS_DEFAULT
        uwa = update(db12, apply=True, reports=reports, mega=mega, do_print=False, asof=wd[0])   # 讀寫連線 --apply 同路徑:TEMP 物件仍不落正本
        cx12 = duckdb.connect(str(db12), read_only=True)
        yfs = {v[0] for v in listings_map(cx12).values()}
        left = _tables(cx12)
        cx12.close()
        po, co = ps25.get(wd[0], set()), cs25.get(wd[0], set())
        listed = [t for t in (po | co) if t in yfs]
        ok_wide = (ok3 and ok25 and len(pd3) == 3 and len(pd25) == 25 and pd3 == pd25[:3] and {x["date"]: five(x) for x in rw3["dates"]} == ref3 and {x["date"]: five(x) for x in rw25["dates"]} == ref25
                   and uw["asof"] == wd[0] and uw["latest_px_date"] == wd[-1] and uw["rows"] == len(listed) == 5 and uw["summary"]["aligned"] == sum(1 for t in listed if t in po and t in co)
                   and uw["summary"]["px"] == len(po) and uw["summary"]["chips"] == len(co) and uw["summary"]["union"] == len(po | co) and uw["px_top"] == max(v[0] for v in ref25.values())
                   and uwa["new"] == uwa["rows"] == 5 and UNIVERSE in left and not ({"_align_px", "_align_chip", "_chipmap"} & left))
        pool = [set(), {"a"}, {"a", "b"}, set("abcdefghij"), set("abcdefghik"), set("abcdefghijk"), set("bcdefghijkl"), set("abcdefghijklmnopqrst")]
        ok_v = all(_verdict(p, c) == _verdict_n(len(p), len(c), len(p & c)) for p in pool for c in pool)
        chk("⑫ 批400 逐日計數 SQL 端化(GROUP BY 日+FULL OUTER JOIN;籌碼對映只算 DISTINCT (code,market) 仍經 chip_ticker → TEMP _chipmap JOIN)= 逐列 Python 集合參照:現有夾具 days=5 check 表列/最新日差集/判定 + 寬窗 update --asof;25 日合成庫(冊 yf 空/NULL、無冊 OTC/otc/NULL/未知市場、_NOOP_/重複列/inst∪margin 去重)days=3 截窗/25 全窗/--asof 最舊日 窗 26>20;_daily_sets 參照同證;_verdict_n=_verdict;TEMP 物件唯讀/--apply 讀寫連線皆不落正本",
            ok5 and ok_chk and ok_upd and ok_wide and ok_v,
            f"(fixture {fl5}/{ok_chk}/{ok_upd};wide {fl3}/{fl25}/{ok_wide};verdict {ok_v};uw {uw['asof']} {uw['verdict']} rows {uw['rows']} px_top {uw.get('px_top')};rw25 {rw25['verdict']} {rw25['summary'].get('aligned')}/{rw25['summary'].get('partial')}/{rw25['summary'].get('misaligned')})")
        miss = check(root / "no.duckdb", reports=reports, do_print=False)
        chk("⑥ 庫缺誠實 RED(不假綠)", miss["verdict"] == "RED")
        c4 = duckdb.connect(str(root / "nolist.duckdb"))
        c4.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE)")
        c4.execute("INSERT INTO tw_daily_prices VALUES ('2026-09-03', '2330.TW', 1.0), ('2026-09-03', '6488.TWO', 1.0)")
        c4.execute("CREATE TABLE tw_chip_inst(date DATE, code VARCHAR, market VARCHAR, foreign_net DOUBLE)")
        c4.execute("INSERT INTO tw_chip_inst VALUES ('2026-09-03', '2330', 'TWSE', 1.0), ('2026-09-03', '6488', 'TPEX', 1.0)")
        c4.close()
        r3 = check(root / "nolist.duckdb", days=3, reports=reports, do_print=False)
        u3 = update(root / "nolist.duckdb", apply=False, reports=reports, mega=mega, do_print=False)
        chk("⑦ 無 tw_listings 冊=市場後綴推定(TWSE→.TW/TPEX→.TWO)仍 ALIGNED;清單=價∪籌碼全員", r3["verdict"] == "ALIGNED" and u3["rows"] == 2 and u3["summary"]["listings"] == 0, f"({r3['verdict']};{u3['rows']})")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/正本零觸碰/誠實三態/零網路/尾版律/Zero-Hydra/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "正本零觸碰", "誠實三態", "零網路", "尾版律", "Zero-Hydra", "ACCEL-BRIDGE")))
    # ⑨ 讓庫律(批391 工作站實錄:單寫者鎖 IOException):鎖兩次後放行=重試成功;永鎖=誠實 RuntimeError(主程式 rc3);非鎖 IOException 原樣拋
    calls = {"n": 0}
    real_connect = duckdb.connect

    def locked_twice(path, read_only=False):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise duckdb.IOException('IO Error: Cannot open file "x.duckdb": 程序無法存取檔案，因為檔案正由另一個程序使用。 File is already open in python.exe (PID 1)')
        return real_connect(path, read_only=read_only)

    def locked_forever(path, read_only=False):
        raise duckdb.IOException("IO Error: Could not set lock on file")

    def other_io(path, read_only=False):
        raise duckdb.IOException("IO Error: disk full")

    with tempfile.TemporaryDirectory() as td2:
        dbp = Path(td2) / "t.duckdb"
        real_connect(str(dbp)).close()
        duckdb.connect = locked_twice
        try:
            c_ok = _connect(dbp, read_only=True, retries=4, wait=0.0, sleep_fn=lambda s: None, resolver=lambda m: (None, ""))
            c_ok.close()
            ok_retry = calls["n"] == 3
            duckdb.connect = locked_forever
            try:
                _connect(dbp, read_only=False, retries=2, wait=0.0, sleep_fn=lambda s: None, resolver=lambda m: (None, ""))
                ok_forever = False
            except RuntimeError as exc:
                ok_forever = "庫忙逾" in str(exc) and "update --apply" in str(exc)
            duckdb.connect = other_io
            try:
                _connect(dbp, read_only=True, retries=2, wait=0.0, sleep_fn=lambda s: None, resolver=lambda m: (None, ""))
                ok_other = False
            except duckdb.IOException:
                ok_other = True
        finally:
            duckdb.connect = real_connect
    chk("⑨ 讓庫律(單寫者鎖 IOException 短等重試;鎖兩次後放行;永鎖=誠實 RuntimeError 指路等日更鏈/回補跑完;非鎖 IOException 原樣拋)", ok_retry and ok_forever and ok_other,
        f"(retry {calls['n']};forever {ok_forever};other {ok_other})")
    # ⑪ 持鎖者解析(批393 工作站實錄:File is already open in C:\Python313\python.exe (PID 7396);via-status 開的是同步頁不是進程表)
    lab = _holder_label(r'C:\Python313\python.exe "C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VDF\engine\VDF_ENG064_HistoryBackfill_v0102.py" run --resume')
    lab2 = _holder_label("powershell -NoProfile -ExecutionPolicy Bypass -File C:\\x\\supportive modules\\registry\\via_boot_update.ps1")
    lab3 = _holder_label("")
    pid_none = _holder_of("IO Error: Could not set lock on file")
    pid_hit = _PID_RX.search('IO Error: Cannot open file "x.duckdb": 程序無法存取檔案 File is already open in C:\\Python313\\python.exe (PID 7396)')

    def locked_pid(path, read_only=False):
        raise duckdb.IOException('IO Error: Cannot open file "x.duckdb": File is already open in C:\\Python313\\python.exe (PID 7396)')

    msg = ""
    with tempfile.TemporaryDirectory() as td3:
        dbp3 = Path(td3) / "t.duckdb"
        real_connect(str(dbp3)).close()
        duckdb.connect = locked_pid
        try:
            _connect(dbp3, read_only=True, retries=1, wait=0.0, sleep_fn=lambda s: None, resolver=lambda m: (7396, "VDF_ENG064_HistoryBackfill_v0102.py run"))
        except RuntimeError as exc:
            msg = str(exc)
        finally:
            duckdb.connect = real_connect
    chk("⑪ 持鎖者解析(IOException PID n → 命令列 → 引擎名+動詞;boot 鏈 ps1;空=空;無 PID=(None,''))+ [FAIL] 句含持鎖者 PID/引擎與 via-bg 指路(取代 via-status)",
        lab == "VDF_ENG064_HistoryBackfill_v0102.py run" and lab2 == "via_boot_update.ps1" and lab3 == "" and pid_none == (None, "") and pid_hit and pid_hit.group(1) == "7396"
        and "持鎖者 PID 7396" in msg and "VDF_ENG064" in msg and "via-bg" in msg and "via-status" not in msg, f"({lab};{lab2};{msg[:70]})")
    print(f"  [計] 十二檢 OK {12 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


# ---------------------------------------------------------------- CLI
def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 台股日交易×籌碼對齊與清單更新引擎(VDF_ENG081_UniverseAlign)· 十二檢自測(零網路;臨時庫)===")
        return selftest()
    verb = next((x for x in a if x in VERBS), "check")   # 動詞白名單
    db = Path(_arg(a, "--db", str(DB_TW)))
    as_json = "--json" in a
    try:
        if verb == "check":
            d = _arg(a, "--days", str(DAYS_DEFAULT))
            rep = check(db, days=max(1, min(3650, int(d))) if str(d).isdigit() else DAYS_DEFAULT, do_print=not as_json)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
            return 0 if rep["verdict"] != "RED" else 2
        if verb == "update":
            asof = _arg(a, "--asof")
            if asof and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(asof)):
                print(f"[FAIL] --asof 需 YYYY-MM-DD:{asof}")
                return 2
            rep = update(db, apply="--apply" in a, do_print=not as_json, asof=asof, allow_latest="--allow-latest" in a)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
            return 0 if rep["verdict"] != "RED" else 2
        st = status(db, do_print=not as_json)
        if as_json:
            print(json.dumps(st, ensure_ascii=False, indent=1, default=str))
        return 0
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        log_event("FAIL", str(exc)[:200])
        return 3
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
